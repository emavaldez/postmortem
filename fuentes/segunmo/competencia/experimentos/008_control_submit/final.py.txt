"""008 — submit de control: mismo MIX6 de 005 (3 mejores trials de M0 y de M1, mismo k=11500, train 202103–06 -> score 202108) con DOS cambios
de pipeline: `ccajas_depositos` corregida (NA en 202105) en M0 y M1, y el bloque lag2/delta2/ratio2 (+150 cols) sumado a M1.
Sirve para verificar sobre 202108 que el pipeline de lag2 funciona (lag2 de 202108 sale de 202106) y comparar contra exp005_final_s30
(Public 96.83M, mismo k, misma muestra del Public). Menos semillas que ese (6 vs 30 por config): se compara por diferencia, no por nivel.
Uso (raíz del repo): venv/bin/python competencia/experimentos/008_control_submit/final.py"""
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(A005))
sys.path.insert(0, str(AQUI.parents[1] / "src"))
import config  # noqa: E402
config.CORREGIR_CCAJAS = True
from optuna_run import es_hist  # noqa: E402
from reevaluar import configs  # noqa: E402
from config import ID_COL, MES_SCORING, SEMILLAS  # noqa: E402
from historia import agregar_historia_n  # noqa: E402
from pool import VARS, cargar  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402
from validacion import xy  # noqa: E402

K, N_SEM = 11500, 6
COLS_LAG2 = [f"{v}_{s}2" for v in VARS for s in ("lag", "d", "r")]

if __name__ == "__main__":
    semillas = SEMILLAS + [int(s) for s in np.random.RandomState(SEMILLAS[0]).randint(100_003, 999_983, size=1)]
    semillas = semillas[:N_SEM]
    cfg = {k: v for k, v in configs().items() if k[1].startswith("top")}
    train = cargar([202103, 202104, 202105, 202106], negocio=True).copy()
    score = cargar([MES_SCORING], solo_con_target=False, negocio=True).copy()
    Xt0, yt = xy(train); yt = yt.values
    M0 = [c for c in Xt0.columns if not es_hist(c)]                     # se define ANTES de sumar lag2 (es_hist lo marcaría)
    M1 = (A005 / "sel" / "top150_final.txt").read_text().split() + COLS_LAG2
    Xt, score = agregar_historia_n(train, VARS, 2), agregar_historia_n(score, VARS, 2)
    cols = {"M0": M0, "M1": M1}
    print(f"train {Xt.shape} | score {score.shape} | M0 {len(M0)} cols, M1 {len(M1)} cols | semillas {semillas}", flush=True)
    # los ratios r2 son NaN cuando el lag vale 0, por eso se chequea solo el lag2 crudo contra la variable original
    assert score[[f"{v}_lag2" for v in VARS]].notna().mean().mean() > 0.9 * score[VARS].notna().mean().mean(), "lag2 de 202108 vacío: revisar join"
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
    pd.DataFrame({ID_COL: ids, "p": p, **{f"{c}_{n}": v for (c, n), v in P.items()}}).to_csv(AQUI / "tmp" / "proba_202108.csv", index=False)
    print(guardar_submit(top_k_ids(ids, p, K), f"exp008_lag2_ccajas_k{K}").name)
    prev = AQUI.parents[1] / "submissions" / "exp005_final_s30_k11500.csv"
    if prev.exists():
        a, b = set(top_k_ids(ids, p, K)), set(np.loadtxt(prev, dtype=np.int64))
        print(f"solapamiento top-{K} con exp005_final_s30: {len(a & b) / K:.1%}")
