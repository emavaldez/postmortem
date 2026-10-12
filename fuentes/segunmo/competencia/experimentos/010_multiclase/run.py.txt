"""B1 — modelo multiclase (CONTINUA / BAJA+1 / BAJA+2) vs binario, mismas filas y mismos hiperparámetros: cambia SOLO el objetivo.

Filas de entrenamiento (iguales para el binario y el multiclase): todos los BAJA+2, todos los BAJA+1 y una fracción r de CONTINUA (r de
M1 top1 de Optuna, ~0.1). Así el multiclase ve la clase rara BAJA+1 completa; el binario la ve como negativo (en 005 se submuestreaban
junto con CONTINUA, por eso se incluye BIN_005 como referencia histórica).
Variantes (columnas M1 = top150 con historia por fold, hiperparámetros y rondas de M1 top1 de 005, ccajas corregida):
  BIN_005   binario, negativos (BAJA+1 y CONTINUA) submuestreados con r           (como en 005)
  BIN_misma binario sobre las filas del multiclase
  MC_p2     multiclase, score = P(BAJA+2)
  MC_h2     multiclase, score = P(BAJA+2) / (1 - P(BAJA+1))   (riesgo condicional: "se va en 2 meses dado que sigue en 1")
  BIN+MC    media de ranks de BIN_misma y MC_p2 (¿diversidad?)
5 semillas nuevas (SEMILLAS_20[2:7]), folds A, B, Bh. Ganancia = media sobre k=8000..15000 (M ARS) y k=11500.
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/010_multiclase/run.py   |   tail -f competencia/experimentos/010_multiclase/log.txt"""
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from config import ID_COL, MES_COL, TARGET_COL  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from pool import cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402
from validacion import KS  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
SEMILLAS_B1 = SEMILLAS_20[2:7]
CLASES = {"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def rank(p):
    return rankdata(p) / len(p)


if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]
    filas, t0 = [], time.time()
    escribir(f"\n===== B1 multiclase {time.strftime('%Y-%m-%d %H:%M')} | r={r:.3f} rondas={rondas} | semillas {SEMILLAS_B1} =====")
    for fold, (mt, mv) in FOLDS.items():
        dt, dv = cargar(mt, negocio=True), cargar([mv], negocio=True)
        cols = (A005 / "sel" / f"top150_{fold}.txt").read_text().split()
        y3 = dt[TARGET_COL].map(CLASES).values; yb = (y3 == 2).astype(int); yv = (dv[TARGET_COL] == "BAJA+2").astype(int).values
        Xt, Xv = dt[cols], dv[cols]
        escribir(f"[{fold}] train {Xt.shape}: CONTINUA {(y3==0).sum()}, BAJA+1 {(y3==1).sum()}, BAJA+2 {(y3==2).sum()} -> valid {mv}")
        for s in SEMILLAS_B1:
            u = np.random.RandomState(s).rand(len(y3))
            keep_005, keep_mc = (y3 == 2) | (u < r), (y3 >= 1) | (u < r)
            P = {}
            m = lgb.train({**params, "seed": s}, lgb.Dataset(Xt[keep_005], label=yb[keep_005]), num_boost_round=rondas)
            P["BIN_005"] = m.predict(Xv)
            m = lgb.train({**params, "seed": s}, lgb.Dataset(Xt[keep_mc], label=yb[keep_mc]), num_boost_round=rondas)
            P["BIN_misma"] = m.predict(Xv)
            m = lgb.train({**params, "objective": "multiclass", "num_class": 3, "seed": s}, lgb.Dataset(Xt[keep_mc], label=y3[keep_mc]), num_boost_round=rondas)
            pm = m.predict(Xv)
            P["MC_p2"] = pm[:, 2]; P["MC_h2"] = pm[:, 2] / np.clip(1 - pm[:, 1], 1e-6, None)
            P["BIN+MC"] = (rank(P["BIN_misma"]) + rank(P["MC_p2"])) / 2
            for nombre, p in P.items():
                acum = ganancia_acumulada(yv, p)
                filas.append({"fold": fold, "semilla": s, "modelo": nombre, "auc": roc_auc_score(yv, p),
                              "gan_media_k": np.mean([acum[k - 1] for k in KS]), "gan_k11500": acum[11500 - 1]})
            g = {f["modelo"]: f["gan_media_k"] / 1e6 for f in filas[-len(P):]}
            escribir(f"[{fold} s={s}] " + " | ".join(f"{k} {v:.1f}" for k, v in g.items()) + f" ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(filas).to_csv(CSV, index=False)
    res = pd.DataFrame(filas); res.to_csv(CSV, index=False); res["M"] = res.gan_media_k / 1e6
    p = res.pivot_table(index=["fold", "semilla"], columns="modelo", values="M"); comp = []
    for a, b in [("BIN_misma", "BIN_005"), ("MC_p2", "BIN_misma"), ("MC_h2", "BIN_misma"), ("BIN+MC", "BIN_misma"), ("MC_p2", "BIN_005")]:
        d = (p[a] - p[b]).groupby("fold"); fila = {"comparacion": f"{a} - {b}"}
        for f in FOLDS:
            fila[f"{f}_delta"], fila[f"{f}_ee"] = d.mean()[f], d.std()[f] / np.sqrt(len(SEMILLAS_B1))
        comp.append(fila)
    comp = pd.DataFrame(comp).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + res.groupby(["modelo", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nAUC:\n" + res.groupby(["modelo", "fold"]).auc.mean().unstack().round(4).to_string())
    escribir("\nDiferencias pareadas:\n" + comp.to_string(index=False)); escribir("[B1] terminado")
