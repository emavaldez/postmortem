"""001 — Baseline: LightGBM binario (BAJA+2 vs resto), validación out-of-time, 5 semillas.

Uso (desde la raíz del repo):  venv/bin/python competencia/experimentos/001_baseline_lgbm/run.py

Esquema (ver resumenes/04):
  - Validación: train 202103+202104  ->  valid 202106  (202105 queda de separación: el target de 202104
    mira hasta 202106). Se repite con las 5 semillas propias.
  - Final: train con TODOS los meses con target (202103..202106) -> scoring 202108, promediando las 5 semillas.
  - Hiperparámetros FIJOS (sin optimizar): es el baseline contra el que se compara después.
Salidas (en esta carpeta): validacion.csv, curva_validacion.csv, y los CSV de submit en competencia/submissions/.
"""
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from config import ID_COL, MES_COL, MES_SCORING, SEMILLAS, TARGET_COL, UMBRAL  # noqa: E402
from data import cargar_meses  # noqa: E402
from ganancia import ganancia_acumulada, ganancia_por_umbral  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402

MESES_TRAIN, MES_VALID = [202103, 202104], 202106
MESES_FINAL = [202103, 202104, 202105, 202106]
NUM_ROUNDS = 300
PARAMS = {
    "objective": "binary", "boosting_type": "gbdt", "max_bin": 31,
    "num_leaves": 31, "learning_rate": 0.05, "min_data_in_leaf": 200,
    "feature_fraction": 0.5, "bagging_fraction": 0.8, "bagging_freq": 1,
    "feature_pre_filter": False, "verbose": -1, "num_threads": 0,
}
KS = list(range(8000, 15001, 1000))   # cantidades de envíos candidatas (rango permitido por el bot)
RONDAS_CURVA = [50, 100, 150, 200, 250, 300]


def xy(df):
    X = df.drop(columns=[ID_COL, MES_COL, TARGET_COL])
    return X, (df[TARGET_COL] == "BAJA+2").astype(int)


def entrenar(X, y, semilla):
    return lgb.train({**PARAMS, "seed": semilla}, lgb.Dataset(X, label=y), num_boost_round=NUM_ROUNDS)


def validar():
    train, valid = cargar_meses(MESES_TRAIN), cargar_meses([MES_VALID])
    (Xt, yt), (Xv, yv) = xy(train), xy(valid)
    print(f"train {Xt.shape} ({yt.sum()} BAJA+2) | valid {Xv.shape} ({yv.sum()} BAJA+2)")
    filas, curva = [], []
    for s in SEMILLAS:
        t0 = time.time()
        m = entrenar(Xt, yt, s)
        p = m.predict(Xv)
        acum = ganancia_acumulada(yv.values, p)
        filas.append({"semilla": s, "auc": roc_auc_score(yv, p),
                      "gan_umbral": ganancia_por_umbral(yv.values, p), "n_umbral": int((p >= UMBRAL).sum()),
                      "gan_max_expost": acum.max(), "k_max_expost": int(acum.argmax()) + 1,
                      **{f"gan_k{k}": acum[k - 1] for k in KS}})
        for r in RONDAS_CURVA:
            pr = m.predict(Xv, num_iteration=r)
            curva.append({"semilla": s, "rondas": r, "auc": roc_auc_score(yv, pr),
                          "gan_umbral": ganancia_por_umbral(yv.values, pr),
                          "gan_max_expost": ganancia_acumulada(yv.values, pr).max()})
        print(f"semilla {s}: AUC {filas[-1]['auc']:.4f} | gan@0.025 {filas[-1]['gan_umbral']/1e6:.1f}M "
              f"({filas[-1]['n_umbral']} envíos) | máx ex-post {filas[-1]['gan_max_expost']/1e6:.1f}M "
              f"en k={filas[-1]['k_max_expost']} | {time.time()-t0:.0f}s", flush=True)
    res, cur = pd.DataFrame(filas), pd.DataFrame(curva)
    res.to_csv(AQUI / "validacion.csv", index=False)
    cur.groupby("rondas").mean(numeric_only=True).drop(columns="semilla").to_csv(AQUI / "curva_validacion.csv")
    cols = ["auc", "gan_umbral", "gan_max_expost"] + [f"gan_k{k}" for k in KS]
    print("\nValidación 202106 (media ± desvío entre semillas, en millones):")
    for c in cols:
        esc = 1 if c == "auc" else 1e6
        print(f"  {c:>15}: {res[c].mean()/esc:10.3f} ± {res[c].std()/esc:.3f}")
    return res


def final():
    train, score = cargar_meses(MESES_FINAL), cargar_meses([MES_SCORING], solo_con_target=False)
    X, y = xy(train)
    Xs = score.drop(columns=[ID_COL, MES_COL, TARGET_COL])
    print(f"\nfinal: train {X.shape} ({y.sum()} BAJA+2) -> scoring {MES_SCORING}: {Xs.shape}")
    p = np.mean([entrenar(X, y, s).predict(Xs) for s in SEMILLAS], axis=0)
    print(f"  clientes con p >= {UMBRAL}: {(p >= UMBRAL).sum()} | p máx {p.max():.3f}")
    for k in KS:
        ruta = guardar_submit(top_k_ids(score[ID_COL].values, p, k), f"exp001_baseline_k{k}")
        print("  escrito", ruta.name)


if __name__ == "__main__":
    validar()
    if "--sin-final" not in sys.argv:
        final()
