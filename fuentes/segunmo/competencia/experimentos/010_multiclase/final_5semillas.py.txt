"""010 — medida honesta con el Public: el mismo modelo de `final.py` (MIX6 de 005 en multiclase, score condicional, rank medio, ccajas corregida, sin lag2,
train 202103–06 -> score 202108), pero 5 archivos, cada uno con UNA de las semillas propias (SEMILLAS de config.py) para las 6 configuraciones,
todos con k=11500. Se mandan juntos en un submit: el bot devuelve media y desvío entre archivos = ruido por semilla en el Public.
(En `final.py` cada configuración promedia 6 semillas; acá es 1, así que cada archivo es algo más ruidoso que ese.)
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/010_multiclase/final_5semillas.py   |   tail -f competencia/experimentos/010_multiclase/final5_log.txt"""
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
config.CORREGIR_CCAJAS = True
from config import ID_COL, MES_SCORING, SEMILLAS, TARGET_COL  # noqa: E402
from optuna_run import es_hist  # noqa: E402
from pool import cargar  # noqa: E402
from reevaluar import configs  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402
from validacion import xy  # noqa: E402

K, LOG = 11500, AQUI / "final5_log.txt"
CLASES = {"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    cfg = {k: v for k, v in configs().items() if k[1].startswith("top")}
    dt = cargar([202103, 202104, 202105, 202106], negocio=True)
    score = cargar([MES_SCORING], solo_con_target=False, negocio=True)
    y3 = dt[TARGET_COL].map(CLASES).values
    Xt0, _ = xy(dt)
    cols = {"M0": [c for c in Xt0.columns if not es_hist(c)], "M1": (A005 / "sel" / "top150_final.txt").read_text().split()}
    ids = score[ID_COL].values
    escribir(f"\n===== final 5 semillas {time.strftime('%Y-%m-%d %H:%M')} | semillas {SEMILLAS} | k={K} =====")
    t0, tops = time.time(), {}
    (AQUI / "tmp").mkdir(exist_ok=True)
    for s in SEMILLAS:
        P = {}
        for (c, nombre), (r, rondas, params) in cfg.items():
            keep = (y3 >= 1) | (np.random.RandomState(s).rand(len(y3)) < r)
            m = lgb.train({**params, "objective": "multiclass", "num_class": 3, "seed": s},
                          lgb.Dataset(dt.loc[keep, cols[c]], label=y3[keep]), num_boost_round=rondas)
            pm = m.predict(score[cols[c]])
            P[f"{c}_{nombre}"] = pm[:, 2] / np.clip(1 - pm[:, 1], 1e-6, None)
        rk = np.mean([rankdata(p) / len(p) for p in P.values()], axis=0)
        pd.DataFrame({ID_COL: ids, "rank": rk, **P}).to_csv(AQUI / "tmp" / f"proba_seed{s}.csv", index=False)
        tops[s] = top_k_ids(ids, rk, K)
        escribir(f"semilla {s}: {guardar_submit(tops[s], f'exp010_seed{s}_k{K}').name} ({(time.time()-t0)/60:.0f} min)")
    ss = list(tops)
    sol = [len(set(tops[a]) & set(tops[b])) / K for i, a in enumerate(ss) for b in ss[i + 1:]]
    escribir(f"solapamiento top-{K} entre semillas: min {min(sol):.1%}, media {np.mean(sol):.1%}, max {max(sol):.1%}")
    prev = AQUI.parents[1] / "submissions" / f"exp010_mc_h2_k{K}.csv"
    if prev.exists():
        p0 = set(np.loadtxt(prev, dtype=np.int64))
        escribir("solapamiento con exp010_mc_h2 (6 semillas): " + ", ".join(f"{s}: {len(set(t) & p0) / K:.1%}" for s, t in tops.items()))
    escribir("[final5] terminado")
