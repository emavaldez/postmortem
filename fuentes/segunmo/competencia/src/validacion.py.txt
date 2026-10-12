"""Validación out-of-time de 2 folds, común a todos los experimentos (ver competencia/PLAN.md).

  Fold A: train 202103            -> valid 202105
  Fold B: train 202103 + 202104   -> valid 202106   (el del baseline 001)
(Entre train y valid queda un mes de separación: el target de un mes mira 2 meses adelante.)

Uso típico:
    res = evaluar()                                  # baseline
    res = evaluar(transformar=mi_funcion)            # transformar(df) -> df con features modificadas
    res = evaluar(params={...}, rounds=500)          # otros hiperparámetros
    print(resumen(res))
`transformar` se aplica a train y a valid por separado: debe ser fila a fila o usar solo información del
propio mes (si necesita historia de otros meses, pasar `cargar=` propio que devuelva el DataFrame ya armado).
"""
import time
from typing import Callable

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from config import ID_COL, MES_COL, SEMILLAS, TARGET_COL, UMBRAL
from data import cargar_meses
from ganancia import ganancia_acumulada, ganancia_por_umbral

FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106)}
NUM_ROUNDS = 300
PARAMS_BASE = {
    "objective": "binary", "boosting_type": "gbdt", "max_bin": 31,
    "num_leaves": 31, "learning_rate": 0.05, "min_data_in_leaf": 200,
    "feature_fraction": 0.5, "bagging_fraction": 0.8, "bagging_freq": 1,
    "feature_pre_filter": False, "verbose": -1, "num_threads": 0,
    # Reproducibilidad: mismo resultado con cualquier cantidad de hilos/máquina (verificado: no cambia el modelo respecto de no ponerlo)
    "deterministic": True, "force_row_wise": True,
}
KS = list(range(8000, 15001, 1000))   # cantidades de envíos candidatas (rango permitido por el bot)
K_REF = 11000                         # k de referencia para comparar experimentos


def xy(df: pd.DataFrame, quitar: tuple = ()):
    X = df.drop(columns=[c for c in (ID_COL, MES_COL, TARGET_COL, *quitar) if c in df.columns])
    return X, (df[TARGET_COL] == "BAJA+2").astype(int)


def evaluar(transformar: Callable | None = None, params: dict | None = None, rounds: int = NUM_ROUNDS,
            folds: dict = FOLDS, semillas=SEMILLAS, cargar: Callable = cargar_meses, quitar: tuple = (),
            verbose: bool = True) -> pd.DataFrame:
    """Una fila por (fold, semilla) con AUC y ganancias (mes completo, sin escalar)."""
    params = {**PARAMS_BASE, **(params or {})}
    filas = []
    for nombre, (meses_train, mes_valid) in folds.items():
        train, valid = cargar(meses_train), cargar([mes_valid])
        if transformar is not None:
            train, valid = transformar(train), transformar(valid)
        (Xt, yt), (Xv, yv) = xy(train, quitar), xy(valid, quitar)
        if verbose:
            print(f"fold {nombre}: train {Xt.shape} ({yt.sum()} BAJA+2) -> valid {mes_valid} {Xv.shape} ({yv.sum()} BAJA+2)")
        for s in semillas:
            t0 = time.time()
            # Dataset nuevo por semilla: el binning depende de `seed` (como en el baseline 001)
            p = lgb.train({**params, "seed": s}, lgb.Dataset(Xt, label=yt), num_boost_round=rounds).predict(Xv)
            acum = ganancia_acumulada(yv.values, p)
            filas.append({"fold": nombre, "semilla": s, "auc": roc_auc_score(yv, p),
                          "gan_umbral": ganancia_por_umbral(yv.values, p), "n_umbral": int((p >= UMBRAL).sum()),
                          "gan_max_expost": acum.max(), "k_max_expost": int(acum.argmax()) + 1,
                          **{f"gan_k{k}": acum[k - 1] for k in KS}})
            if verbose:
                print(f"  semilla {s}: AUC {filas[-1]['auc']:.4f} | k={K_REF}: {filas[-1][f'gan_k{K_REF}']/1e6:.1f}M "
                      f"| {time.time()-t0:.0f}s", flush=True)
    return pd.DataFrame(filas)


def resumen(res: pd.DataFrame) -> pd.DataFrame:
    """Media y desvío entre semillas por fold (ganancias en millones) + fila 'A+B' con la media de los folds."""
    cols = ["auc", "gan_umbral", "gan_max_expost"] + [f"gan_k{k}" for k in KS]
    m = res.groupby("fold")[cols].mean()
    s = res.groupby("fold")[cols].std()
    out = pd.concat({"media": m, "desvio": s}, axis=1)
    out.loc["A+B"] = pd.concat([m.mean(), s.mean()]).values
    ganancias = [c for c in out.columns if c[1] != "auc"]
    out[ganancias] = out[ganancias] / 1e6
    return out.round(3)
