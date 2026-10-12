"""Funciones comunes de los experimentos con el modelo MULTICLASE (CONTINUA/BAJA+1/BAJA+2), ver 010/013/020-022.
Score condicional P(BAJA+2)/(1-P(BAJA+1)); filas de train = BAJA+1 y BAJA+2 completos + fracción r de CONTINUA."""
import lightgbm as lgb
import numpy as np

from config import TARGET_COL
from ganancia import ganancia_acumulada
from validacion import KS

CLASES = {"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}


def etiquetas(df) -> np.ndarray:
    return df[TARGET_COL].map(CLASES).values


def filas(y3: np.ndarray, r: float, seed: int) -> np.ndarray:
    """Máscara de entrenamiento: BAJA+1 y BAJA+2 siempre, CONTINUA con probabilidad r (r=1.0 = sin undersampling)."""
    return (y3 >= 1) | (np.random.RandomState(seed).rand(len(y3)) < r)


def entrenar(params: dict, X, y3, keep, seed: int, rondas: int, peso=None):
    return lgb.train({**params, "objective": "multiclass", "num_class": 3, "seed": seed},
                     lgb.Dataset(X[keep], label=y3[keep], weight=None if peso is None else peso[keep]), num_boost_round=rondas)


def score_cond(pm: np.ndarray) -> np.ndarray:
    return pm[:, 2] / np.clip(1 - pm[:, 1], 1e-6, None)


def gan_media(yv, p) -> float:
    """Ganancia media sobre k=8000..15000, en millones de ARS."""
    acum = ganancia_acumulada(yv, p)
    return float(np.mean([acum[k - 1] for k in KS])) / 1e6
