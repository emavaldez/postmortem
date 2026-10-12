"""004 — entrega 3: pool (historia lag1 + ratios) restringido a los top150 (`variables_final_top150.txt`),
train 202103–202106 -> score 202108, params fijos del baseline, 5 semillas promediadas, 8 archivos top-k.
Uso (raíz del repo): venv/bin/python competencia/experimentos/004_seleccion_variables/final.py"""
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(AQUI.parents[1] / "src"))
from config import ID_COL, MES_SCORING, SEMILLAS  # noqa: E402
from pool import cargar  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402
from validacion import KS, NUM_ROUNDS, PARAMS_BASE, xy  # noqa: E402

VARS = (AQUI / "variables_final_top150.txt").read_text().split()

if __name__ == "__main__":
    train = cargar([202103, 202104, 202105, 202106])
    score = cargar([MES_SCORING], solo_con_target=False)     # 202108: sin target; lag1 viene de 202107
    Xt, yt = xy(train)
    Xt, Xs = Xt[VARS], score[VARS]
    print(f"train {Xt.shape} ({yt.sum()} BAJA+2) | score {Xs.shape} | % con lag1 en 202108: {score[VARS[0] if '_lag1' in VARS[0] else 'ctrx_quarter_lag1'].notna().mean():.3f}")
    p = np.mean([lgb.train({**PARAMS_BASE, "seed": s}, lgb.Dataset(Xt, label=yt), num_boost_round=NUM_ROUNDS).predict(Xs)
                 for s in SEMILLAS], axis=0)
    ids = score[ID_COL].values
    pd.DataFrame({ID_COL: ids, "proba": p}).to_csv(AQUI / "tmp" / "proba_202108.csv", index=False)   # tmp/ no se versiona
    for k in KS:
        print(guardar_submit(top_k_ids(ids, p, k), f"exp004_top150_k{k}").name)
    print("proba media", p.mean().round(4), "| clientes con p>=0.025:", int((p >= 0.025).sum()))
