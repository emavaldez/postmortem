"""005 — candidato a entrega final: MIX6 (3 mejores trials de la ronda 1 de M0 y de M1), 30 semillas por configuración
(las 5 propias + 25 derivadas de la primera, como en SEMILLAS_20), train 202103–202106 -> score 202108, UN solo archivo con k fijo.
Uso (raíz del repo): venv/bin/python competencia/experimentos/005_optuna/final30.py [k]   (k por defecto 11500)"""
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from optuna_run import es_hist  # noqa: E402
from reevaluar import configs  # noqa: E402
from config import ID_COL, MES_SCORING, SEMILLAS  # noqa: E402
from pool import cargar  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402
from validacion import xy  # noqa: E402

K = int(sys.argv[1]) if len(sys.argv) > 1 else 11500
N_SEM = 30
if __name__ == "__main__":
    semillas = SEMILLAS + [int(s) for s in np.random.RandomState(SEMILLAS[0]).randint(100_003, 999_983, size=N_SEM - len(SEMILLAS))]
    cfg = {k: v for k, v in configs().items() if k[1].startswith("top")}
    Xt, yt = xy(cargar([202103, 202104, 202105, 202106], negocio=True)); yt = yt.values
    score = cargar([MES_SCORING], solo_con_target=False, negocio=True)
    cols = {"M0": [c for c in Xt.columns if not es_hist(c)], "M1": (AQUI / "sel" / "top150_final.txt").read_text().split()}
    print(f"train {Xt.shape} | score {score.shape} | {len(cfg)} configs x {N_SEM} semillas", flush=True)
    P = {}
    for (c, nombre), (r, rounds, params) in cfg.items():
        ps = []
        for s in semillas:
            keep = (yt == 1) | (np.random.RandomState(s).rand(len(yt)) < r)
            m = lgb.train({**params, "seed": s}, lgb.Dataset(Xt.loc[keep, cols[c]], label=yt[keep]), num_boost_round=rounds)
            ps.append(m.predict(score[cols[c]]))
        P[(c, nombre)] = np.mean(ps, axis=0); print(f"listo {c} {nombre}", flush=True)
    p = np.mean(list(P.values()), axis=0); ids = score[ID_COL].values
    (AQUI / "tmp").mkdir(exist_ok=True)
    pd.DataFrame({ID_COL: ids, "p": p, **{f"{c}_{n}": v for (c, n), v in P.items()}}).to_csv(AQUI / "tmp" / "proba_final30_202108.csv", index=False)
    print(guardar_submit(top_k_ids(ids, p, K), f"exp005_final_s{N_SEM}_k{K}").name)
