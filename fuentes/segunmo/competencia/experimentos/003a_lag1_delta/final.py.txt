"""003a — entrega temprana: lag1+delta1 (50 vars), train 202103–202106 (NaN nativo en 202103) -> score 202108.
Params fijos del baseline, 5 semillas propias promediadas, 8 archivos top-k (k=8000..15000).
Uso (raíz del repo): venv/bin/python competencia/experimentos/003a_lag1_delta/final.py"""
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from config import ID_COL, MES_COL, MES_SCORING, SEMILLAS  # noqa: E402
from historia import agregar_deltas, cargar_con_lags  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402
from validacion import KS, NUM_ROUNDS, PARAMS_BASE, xy  # noqa: E402

VARS = (AQUI / "variables_historia.txt").read_text().split()
cargar = lambda meses, **kw: agregar_deltas(cargar_con_lags(meses, VARS, **kw), VARS)  # noqa: E731

if __name__ == "__main__":
    train = cargar([202103, 202104, 202105, 202106])
    score = cargar([MES_SCORING], solo_con_target=False)   # 202108 no tiene target; su lag1 viene de 202107
    Xt, yt = xy(train)
    Xs = score[Xt.columns]                                  # mismo orden de columnas que en train
    print(f"train {Xt.shape} ({yt.sum()} BAJA+2) | score {Xs.shape} | % con lag1 en 202108: {score[VARS[0]+'_lag1'].notna().mean():.3f}")
    p = np.mean([lgb.train({**PARAMS_BASE, "seed": s}, lgb.Dataset(Xt, label=yt), num_boost_round=NUM_ROUNDS).predict(Xs)
                 for s in SEMILLAS], axis=0)
    ids = score[ID_COL].values
    pd.DataFrame({ID_COL: ids, "proba": p}).to_csv(AQUI / "tmp" / "proba_202108.csv", index=False)
    for k in KS:
        print(guardar_submit(top_k_ids(ids, p, k), f"exp003a_lag1_k{k}"))
    print("proba: media", p.mean().round(4), "| clientes con p>=0.025:", int((p >= 0.025).sum()))
