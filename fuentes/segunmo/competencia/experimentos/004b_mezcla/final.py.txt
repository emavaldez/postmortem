"""004b — entrega 4: mezcla M0 (columnas originales) + M1 (top150 con historia), train 202103–202106 -> score 202108.
10 semillas por familia (las 5 propias + 5 derivadas, como en SEMILLAS_20), params fijos del baseline.
p = (media de M0 + media de M1)/2 ; 8 archivos top-k (k=8000..15000), igual que las entregas anteriores para comparar.
Uso (raíz del repo): venv/bin/python competencia/experimentos/004b_mezcla/final.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(AQUI))
from config import ID_COL, MES_SCORING  # noqa: E402
from pool import cargar  # noqa: E402
from run import SEMILLAS_20, ajustar, es_hist  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402
from validacion import KS, xy  # noqa: E402

if __name__ == "__main__":
    semillas = SEMILLAS_20[:10]
    Xt, yt = xy(cargar([202103, 202104, 202105, 202106]))
    score = cargar([MES_SCORING], solo_con_target=False)
    orig = [c for c in Xt.columns if not es_hist(c)]
    top = (AQUI.parent / "004_seleccion_variables" / "variables_final_top150.txt").read_text().split()
    print(f"train {Xt.shape} ({yt.sum()} BAJA+2) | score {score.shape} | M0 {len(orig)} cols, M1 {len(top)} cols | semillas {semillas}", flush=True)
    p0 = np.mean([ajustar(Xt[orig], yt, score[orig], s) for s in semillas], axis=0)
    p1 = np.mean([ajustar(Xt[top], yt, score[top], s) for s in semillas], axis=0)
    p = (p0 + p1) / 2
    ids = score[ID_COL].values
    pd.DataFrame({ID_COL: ids, "p0": p0, "p1": p1, "p": p}).to_csv(AQUI / "tmp" / "proba_202108.csv", index=False)   # tmp/ no se versiona
    for k in KS:
        print(guardar_submit(top_k_ids(ids, p, k), f"exp004b_mix_k{k}").name)
    print("corr(p0,p1) %.3f | clientes con p>=0.025: M0 %d, M1 %d, MIX %d" % (np.corrcoef(p0, p1)[0, 1], (p0 >= .025).sum(), (p1 >= .025).sum(), (p >= .025).sum()))
