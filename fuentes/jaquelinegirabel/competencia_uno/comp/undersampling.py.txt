"""Undersampling del train: se quedan todos los BAJA+2 (clase 1) y una fraccion r, al azar,
de los demas (clase 0: CONTINUA y BAJA+1 juntos).

- Solo se reduce lo que el modelo usa para aprender. Lo que se usa para medir (el 30% de cada
  particion de Optuna y el mes de test) tiene siempre a todos los clientes.
- Cada semilla saca su propia muestra, asi el ensamble por semillas tambien promedia muestras.
- Como el modelo vio mas BAJA+2 que en la realidad, sus probabilidades salen infladas. Se
  corrigen con  p_real = p * r / (p * r + 1 - p)  antes de aplicar el corte de 0.025 y
  cualquier metrica.

r = None significa sin undersampling (todo queda igual que antes).
"""
import numpy as np

from . import config


def indices_muestra(y, r, seed):
    """Posiciones (0..n-1) de todos los positivos y de una fraccion r de los negativos."""
    y = np.asarray(y)
    positivos = np.flatnonzero(y == 1)
    negativos = np.flatnonzero(y == 0)
    rng = np.random.default_rng(seed)
    elegidos = rng.choice(negativos, size=int(round(len(negativos) * r)), replace=False)
    return np.sort(np.concatenate([positivos, elegidos]))


def corregir_probabilidad(p, r):
    """Deshace el efecto del undersampling sobre las probabilidades."""
    if r is None:
        return p
    p = np.asarray(p, dtype='float64')
    return p * r / (p * r + 1 - p)


def construir_si_hace_falta(train_lgb, seed):
    """Construye el Dataset completo con los mismos parametros de binning que usaria lgb.train.

    Un subconjunto (subset) necesita que el Dataset completo ya este construido; si no, LightGBM
    lo construye con sus valores por defecto y despues no deja cambiar max_bin. Si ya esta
    construido (por ejemplo por lgb.cv en Optuna) no se toca.
    """
    construido = getattr(train_lgb, '_handle', getattr(train_lgb, 'handle', None)) is not None
    if not construido:
        train_lgb.params = {
            **(train_lgb.params or {}),
            'max_bin': config.PARAMS_FIJOS['max_bin'],
            'feature_pre_filter': config.PARAMS_FIJOS['feature_pre_filter'],
            'seed': seed,
            'verbose': -1,
        }
        train_lgb.construct()
    return train_lgb


def dataset_muestra(train_lgb, y, r, seed):
    """El lgb.Dataset de train completo (r None) o un subconjunto con la muestra de esa semilla."""
    if r is None:
        return train_lgb
    construir_si_hace_falta(train_lgb, seed)
    return train_lgb.subset(indices_muestra(y, r, seed).tolist())
