"""Selección de variables con "canaritos": columnas de ruido puro agregadas al entrenamiento.

Idea: una variable real que el modelo usa menos que una columna de ruido aleatorio no está aportando señal (los
árboles la usan igual para ajustar ruido del train). Se entrena con N canaritos U(0,1), se promedia la importancia
(gain relativo) entre semillas y se descartan las variables cuya importancia no supera el umbral de los canaritos.
Solo se mira el train: nunca el mes de validación.
"""
import lightgbm as lgb
import numpy as np
import pandas as pd

from config import SEMILLAS
from validacion import NUM_ROUNDS, PARAMS_BASE


def importancias_con_canaritos(X: pd.DataFrame, y, semillas=SEMILLAS, n_canaritos: int = 20,
                               params: dict | None = None, rounds: int = NUM_ROUNDS) -> pd.DataFrame:
    """Gain relativo (suma 1 por modelo) de cada columna, media y desvío entre semillas. Los canaritos se llaman
    `canario_i` y se redibujan en cada semilla."""
    params = {**PARAMS_BASE, **(params or {})}
    filas = []
    for s in semillas:
        rng = np.random.RandomState(s)
        canarios = pd.DataFrame(rng.rand(len(X), n_canaritos), columns=[f"canario_{i}" for i in range(n_canaritos)],
                                index=X.index)
        Xc = pd.concat([X, canarios], axis=1)
        m = lgb.train({**params, "seed": s}, lgb.Dataset(Xc, label=y), num_boost_round=rounds)
        g = pd.Series(m.feature_importance("gain"), index=Xc.columns)
        filas.append(g / g.sum())
    imp = pd.concat(filas, axis=1)
    return pd.DataFrame({"gain_media": imp.mean(axis=1), "gain_sd": imp.std(axis=1)}).sort_values("gain_media", ascending=False)


def elegir(imp: pd.DataFrame, regla: str = "max") -> list[str]:
    """Variables (sin canaritos) cuya importancia media supera el umbral de los canaritos:
    'max' = el mejor canarito (estricto), 'p90' = percentil 90 de los canaritos (más permisivo)."""
    es_can = imp.index.str.startswith("canario_")
    umbral = imp.loc[es_can, "gain_media"].max() if regla == "max" else imp.loc[es_can, "gain_media"].quantile(0.9)
    return [c for c in imp.index[~es_can] if imp.loc[c, "gain_media"] > umbral]
