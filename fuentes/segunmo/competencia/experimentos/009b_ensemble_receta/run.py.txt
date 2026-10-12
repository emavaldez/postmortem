"""009b — ¿agregar la receta del profe (009) al MIX6 de 005 sube la ganancia del ensemble? Además compara promediar probabilidades vs ranks (D1).

Modelos: los 6 de MIX6 (3 mejores trials de Optuna de M0 y de M1, cada uno con su r) y 2 de la receta sobre las columnas M1:
  REC128 = 128 hojas, REC256 = 256 hojas; ambos r=0.1, min_sum_hessian 0.05, 1000 rondas, lr 0.005, min_data_in_leaf 0, ff 0.5, bynode 0.2.
Ensembles (media de probabilidades salvo que diga rank): MIX6 | MIX6_rank | REC2 | MIX6+REC2 (8 modelos, la receta pesa 25%) |
  MIX6+REC2_rank | 50/50 (media de MIX6 y media de REC2).
5 semillas NUEVAS (SEMILLAS_20[2:7]: ni las de la búsqueda de 005 ni las de 009), folds A, B, Bh, ccajas corregida, sin lag2 (un cambio por vez).
Métrica: media de la ganancia sobre k=8000..15000 (M ARS) y k=11500. Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/009b_ensemble_receta/run.py
Progreso: tail -f competencia/experimentos/009b_ensemble_receta/log.txt"""
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
from ganancia import ganancia_acumulada  # noqa: E402
from optuna_run import es_hist  # noqa: E402
from pool import cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402
from validacion import KS, xy  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
SEMILLAS_009B = SEMILLAS_20[2:7]
RECETA = {"objective": "binary", "max_bin": 31, "min_data_in_leaf": 0, "feature_fraction": 0.5, "feature_fraction_bynode": 0.2,
          "learning_rate": 0.005, "min_sum_hessian_in_leaf": 0.05, "feature_pre_filter": False, "verbose": -1, "num_threads": 0}
REC = {"REC128": 128, "REC256": 256}
R_REC, RONDAS_REC = 0.1, 1000


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def rank_medio(ps):
    return np.mean([rankdata(p) / len(p) for p in ps], axis=0)


if __name__ == "__main__":
    cfg = {k: v for k, v in configs().items() if k[1].startswith("top")}
    filas, t0 = [], time.time()
    escribir(f"\n===== 009b {time.strftime('%Y-%m-%d %H:%M')} | semillas {SEMILLAS_009B} =====")
    for fold, (mt, mv) in FOLDS.items():
        (Xt, yt), (Xv, yv) = xy(cargar(mt, negocio=True)), xy(cargar([mv], negocio=True))
        cols = {"M0": [c for c in Xt.columns if not es_hist(c)], "M1": (A005 / "sel" / f"top150_{fold}.txt").read_text().split()}
        yt, yv = yt.values, yv.values
        for s in SEMILLAS_009B:
            P = {}
            for (c, nombre), (r, rondas, params) in cfg.items():
                keep = (yt == 1) | (np.random.RandomState(s).rand(len(yt)) < r)
                m = lgb.train({**params, "seed": s}, lgb.Dataset(Xt.loc[keep, cols[c]], label=yt[keep]), num_boost_round=rondas)
                P[f"{c}_{nombre}"] = m.predict(Xv[cols[c]])
            mix6 = list(P.values())
            keep = (yt == 1) | (np.random.RandomState(s).rand(len(yt)) < R_REC)
            for nombre, hojas in REC.items():
                m = lgb.train({**RECETA, "num_leaves": hojas, "seed": s}, lgb.Dataset(Xt.loc[keep, cols["M1"]], label=yt[keep]), num_boost_round=RONDAS_REC)
                P[nombre] = m.predict(Xv[cols["M1"]])
            rec2 = [P[n] for n in REC]
            E = {**{n: p for n, p in P.items()},
                 "MIX6": np.mean(mix6, axis=0), "MIX6_rank": rank_medio(mix6), "REC2": np.mean(rec2, axis=0),
                 "MIX6+REC2": np.mean(mix6 + rec2, axis=0), "MIX6+REC2_rank": rank_medio(mix6 + rec2),
                 "MIX6_50_REC2_50": 0.5 * np.mean(mix6, axis=0) + 0.5 * np.mean(rec2, axis=0)}
            for nombre, p in E.items():
                acum = ganancia_acumulada(yv, p)
                filas.append({"fold": fold, "semilla": s, "modelo": nombre, "auc": roc_auc_score(yv, p),
                              "gan_media_k": np.mean([acum[k - 1] for k in KS]), "gan_k11500": acum[11500 - 1]})
            g = {f["modelo"]: f["gan_media_k"] / 1e6 for f in filas[-len(E):]}
            escribir(f"[{fold} s={s}] MIX6 {g['MIX6']:.1f} | MIX6+REC2 {g['MIX6+REC2']:.1f} | 50/50 {g['MIX6_50_REC2_50']:.1f} | REC2 {g['REC2']:.1f} "
                     f"| rank: {g['MIX6_rank']:.1f}/{g['MIX6+REC2_rank']:.1f} ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(filas).to_csv(CSV, index=False)
    r = pd.DataFrame(filas); r.to_csv(CSV, index=False)
    r["M"] = r.gan_media_k / 1e6
    p = r.pivot_table(index=["fold", "semilla"], columns="modelo", values="M")
    comp = []
    for a, b in [("MIX6+REC2", "MIX6"), ("MIX6_50_REC2_50", "MIX6"), ("REC2", "MIX6"), ("MIX6_rank", "MIX6"), ("MIX6+REC2_rank", "MIX6+REC2")]:
        d = (p[a] - p[b]).groupby("fold"); fila = {"comparacion": f"{a} - {b}"}
        for f in FOLDS:
            fila[f"{f}_delta"], fila[f"{f}_ee"] = d.mean()[f], d.std()[f] / np.sqrt(len(SEMILLAS_009B))
        comp.append(fila)
    comp = pd.DataFrame(comp).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + r.groupby(["modelo", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas:\n" + comp.to_string(index=False)); escribir("[009b] terminado")
