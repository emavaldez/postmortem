"""015 — curva de ganancia vs k para el ENSEMBLE MULTICLASE (6 configuraciones de 005, score condicional, rank medio, ccajas corregida).
Toda la validación usó la media sobre k=8000..15000; con el multiclase el k óptimo pudo haberse corrido. Acá se guarda la curva completa (k=6000..16000, paso 500) y el
óptimo por fold. Folds A, B, Bh; 3 semillas (SEMILLAS_20[2:5]). El bot solo acepta 8000..15000.
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/015_curva_k/run.py   |   tail -f competencia/experimentos/015_curva_k/log.txt"""
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from config import TARGET_COL  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from optuna_run import es_hist  # noqa: E402
from pool import cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402
from validacion import xy  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "curvas.csv"
FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
SEMILLAS_015, KS_GRID = SEMILLAS_20[2:5], list(range(6000, 16001, 500))
CLASES = {"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    cfg = {k: v for k, v in configs().items() if k[1].startswith("top")}
    filas, t0 = [], time.time()
    escribir(f"\n===== 015 {time.strftime('%Y-%m-%d %H:%M')} | semillas {SEMILLAS_015} =====")
    for fold, (mt, mv) in FOLDS.items():
        dt, dv = cargar(mt, negocio=True), cargar([mv], negocio=True)
        Xt0, _ = xy(dt)
        cols = {"M0": [c for c in Xt0.columns if not es_hist(c)], "M1": (A005 / "sel" / f"top150_{fold}.txt").read_text().split()}
        y3 = dt[TARGET_COL].map(CLASES).values; yv = (dv[TARGET_COL] == "BAJA+2").astype(int).values
        for s in SEMILLAS_015:
            P = []
            for (c, nombre), (r, rondas, params) in cfg.items():
                keep = (y3 >= 1) | (np.random.RandomState(s).rand(len(y3)) < r)
                m = lgb.train({**params, "objective": "multiclass", "num_class": 3, "seed": s}, lgb.Dataset(dt.loc[keep, cols[c]], label=y3[keep]), num_boost_round=rondas)
                pm = m.predict(dv[cols[c]]); P.append(pm[:, 2] / np.clip(1 - pm[:, 1], 1e-6, None))
            rk = np.mean([rankdata(p) / len(p) for p in P], axis=0)
            acum = ganancia_acumulada(yv, rk)
            filas.append({"fold": fold, "semilla": s, "positivos": int(yv.sum()), "k_max": int(acum.argmax()) + 1, "gan_max": acum.max(), **{f"k{k}": acum[k - 1] for k in KS_GRID}})
            escribir(f"[{fold} s={s}] óptimo ex post k={filas[-1]['k_max']} ({acum.max()/1e6:.1f}M) | k=11500: {acum[11499]/1e6:.1f}M ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(filas).to_csv(CSV, index=False)
    r = pd.DataFrame(filas); r.to_csv(CSV, index=False)
    curva = r.groupby("fold")[[f"k{k}" for k in KS_GRID]].mean().T / 1e6; curva.index = KS_GRID
    curva["media_folds"] = curva.mean(axis=1); curva["regret_vs_mejor_k"] = (curva[["A", "B", "Bh"]].max() - curva[["A", "B", "Bh"]]).mean().mean() * 0
    reg = curva[["A", "B", "Bh"]].sub(curva[["A", "B", "Bh"]].max(axis=0), axis=1)         # pérdida de cada k respecto del mejor k de ese fold
    curva["pierde_vs_pico_media"] = reg.mean(axis=1)
    curva.drop(columns="regret_vs_mejor_k").round(1).to_csv(AQUI / "curva_media.csv")
    escribir("\nGanancia media por k (M ARS) y pérdida vs el pico de cada fold:\n" + curva.drop(columns="regret_vs_mejor_k").round(1).loc[8000:15000:500].to_string())
    escribir("\nk del pico por fold: " + ", ".join(f"{f}: {int(curva[f].idxmax())}" for f in ["A", "B", "Bh"]) + f" | pico de la media de folds: {int(curva['media_folds'].idxmax())}")
    escribir("[015] terminado")
