"""030 — ENSEMBLE con las columnas de 'todas las variables con lags' (028): ¿conserva la ventaja sobre el ensemble actual?
Ensemble de las 3 configuraciones M1 de 005 (top1-3), multiclase, score condicional, rank medio, en dos versiones: E1 = M1 top150 + lag2 de 50 variables (lo que usa el final),
E2 = todas las columnas (863: pool + lag1/d1 de las 92 variables extra + lag2/d2 de las 142). Más la mezcla 50/50 de los dos rankings (E12). Folds L y B2 (targets solapados en 202107),
3 semillas (SEMILLAS_20[2:5]), ccajas corregida. Ganancia = media sobre k=8000..15000 (M ARS).
Uso (raíz del repo): venv/bin/python competencia/experimentos/030_ensemble_todas_lags/run.py   |   tail -f competencia/experimentos/030_ensemble_todas_lags/log.txt"""
import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(AQUI.parents[0] / "005_optuna"))
spec = importlib.util.spec_from_file_location("t028", AQUI.parents[0] / "028_todas_lags" / "run.py"); t028 = importlib.util.module_from_spec(spec); spec.loader.exec_module(t028)
from multiclase import entrenar, etiquetas, filas, gan_media, score_cond  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402

LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
SEMILLAS_030 = SEMILLAS_20[2:5]


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


rk = lambda ps: np.mean([rankdata(p) / len(p) for p in ps], axis=0)  # noqa: E731

if __name__ == "__main__":
    cfg = {k: v for k, v in configs().items() if k[0] == "M1" and k[1].startswith("top")}
    base = (t028.A005 / "sel" / "top150_Bh.txt").read_text().split()
    res, t0 = [], time.time()
    escribir(f"\n===== 030 {time.strftime('%Y-%m-%d %H:%M')} | {len(SEMILLAS_030)} semillas | {len(cfg)} configs M1 =====")
    for fold, (mt, mv) in t028.FOLDS.items():
        dt, dv = t028.construir(mt), t028.construir([mv])
        todas = [c for c in dt.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria") and not c.startswith("canario")]
        sets = {"E1": base + t028.LAG2_50, "E2": todas}
        y3, yv = etiquetas(dt), (dv["clase_ternaria"] == "BAJA+2").astype(int).values
        for s in SEMILLAS_030:
            P = {n: [] for n in sets}
            for (c, nombre), (r, rondas, params) in cfg.items():
                keep = filas(y3, r, s)
                for n, cs in sets.items():
                    P[n].append(score_cond(entrenar(params, dt[cs], y3, keep, s, rondas).predict(dv[cs])))
            R = {n: rk(ps) for n, ps in P.items()}
            R["E12"] = (rankdata(R["E1"]) + rankdata(R["E2"])) / (2 * len(yv))
            g = {n: gan_media(yv, p) for n, p in R.items()}
            res += [{"fold": fold, "semilla": s, "modelo": n, "M": v} for n, v in g.items()]
            escribir(f"[{fold} s={s}] E1 {g['E1']:.1f} | E2 {g['E2'] - g['E1']:+.1f} | mezcla 50/50 {g['E12'] - g['E1']:+.1f} ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.DataFrame(res); p = r_.pivot_table(index=["fold", "semilla"], columns="modelo", values="M"); filas_ = []
    for v in ("E2", "E12"):
        d = (p[v] - p["E1"]).groupby("fold")
        filas_.append({"comparacion": f"{v} - E1", **{f"{f}_delta": d.mean()[f] for f in t028.FOLDS}, **{f"{f}_ee": d.std()[f] / np.sqrt(len(SEMILLAS_030)) for f in t028.FOLDS},
                       "pares_positivos": f"{int(((p[v] - p['E1']) > 0).sum())}/{len(p)}"})
    comp = pd.DataFrame(filas_).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + r_.groupby(["modelo", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas vs E1:\n" + comp.to_string(index=False)); escribir("[030] terminado")
