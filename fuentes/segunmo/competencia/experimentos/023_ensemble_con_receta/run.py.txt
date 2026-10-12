"""023 — ¿suma la receta del profe (multiclase, SIN undersampling, 512 hojas, min_sum_hessian 0.05, 800 rondas) al ensemble MIX6 multiclase? (021 la mostró competitiva.)
Mismo diseño que 013/009b: las 6 configuraciones de 005 en multiclase (score condicional, rank medio) vs ese ensemble + el modelo de la receta, pareado por (fold, semilla).
Ensembles: MIX6 | MIX6+REC (7 modelos, REC pesa 1/7) | 50/50 (rank medio de MIX6 y rank de REC) | REC sola. Folds A, B, Bh; 3 semillas (SEMILLAS_20[2:5]); ccajas corregida.
REC usa las columnas M1 top150 del fold. Ganancia = media sobre k=8000..15000 (M ARS).
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/023_ensemble_con_receta/run.py   |   tail -f competencia/experimentos/023_ensemble_con_receta/log.txt"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from multiclase import entrenar, etiquetas, filas, gan_media, score_cond  # noqa: E402
from optuna_run import es_hist  # noqa: E402
from pool import cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402
from validacion import xy  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
SEMILLAS_023 = SEMILLAS_20[2:5]
RECETA = {"max_bin": 31, "min_data_in_leaf": 0, "feature_fraction": 0.5, "feature_fraction_bynode": 0.2, "learning_rate": 0.005,
          "min_sum_hessian_in_leaf": 0.05, "num_leaves": 512, "feature_pre_filter": False, "verbose": -1, "num_threads": 0}
RONDAS_REC = 800


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


rk = lambda ps: np.mean([rankdata(p) / len(p) for p in ps], axis=0)  # noqa: E731

if __name__ == "__main__":
    cfg = {k: v for k, v in configs().items() if k[1].startswith("top")}
    res, t0 = [], time.time()
    escribir(f"\n===== 023 {time.strftime('%Y-%m-%d %H:%M')} | semillas {SEMILLAS_023} =====")
    for fold, (mt, mv) in FOLDS.items():
        dt, dv = cargar(mt, negocio=True), cargar([mv], negocio=True)
        Xt0, _ = xy(dt)
        cols = {"M0": [c for c in Xt0.columns if not es_hist(c)], "M1": (A005 / "sel" / f"top150_{fold}.txt").read_text().split()}
        y3, yv = etiquetas(dt), (dv["clase_ternaria"] == "BAJA+2").astype(int).values
        for s in SEMILLAS_023:
            P = []
            for (c, nombre), (r, rondas, params) in cfg.items():
                m = entrenar(params, dt[cols[c]], y3, filas(y3, r, s), s, rondas)
                P.append(score_cond(m.predict(dv[cols[c]])))
            rec = score_cond(entrenar(RECETA, dt[cols["M1"]], y3, filas(y3, 1.0, s), s, RONDAS_REC).predict(dv[cols["M1"]]))
            E = {"MIX6": rk(P), "MIX6+REC": rk(P + [rec]), "50/50": (rankdata(rk(P)) + rankdata(rec)) / (2 * len(rec)), "REC": rec}
            g = {n: gan_media(yv, p) for n, p in E.items()}
            res += [{"fold": fold, "semilla": s, "modelo": n, "M": v} for n, v in g.items()]
            escribir(f"[{fold} s={s}] MIX6 {g['MIX6']:.1f} | +REC {g['MIX6+REC'] - g['MIX6']:+.1f} | 50/50 {g['50/50'] - g['MIX6']:+.1f} | REC sola {g['REC'] - g['MIX6']:+.1f} ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.DataFrame(res); p = r_.pivot_table(index=["fold", "semilla"], columns="modelo", values="M"); filas_ = []
    for v in ("MIX6+REC", "50/50", "REC"):
        d = (p[v] - p["MIX6"]).groupby("fold")
        filas_.append({"comparacion": f"{v} - MIX6", **{f"{f}_delta": d.mean()[f] for f in FOLDS}, **{f"{f}_ee": d.std()[f] / np.sqrt(len(SEMILLAS_023)) for f in FOLDS},
                       "pares_positivos": f"{int(((p[v] - p['MIX6']) > 0).sum())}/{len(p)}"})
    comp = pd.DataFrame(filas_).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + r_.groupby(["modelo", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas vs MIX6:\n" + comp.to_string(index=False)); escribir("[023] terminado")
