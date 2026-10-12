"""
preproc_comun.py — cálculo compartido de variables para el preprocesamiento de cada experimento (DMEyF).

Lo importan los scripts 01_preprocesamiento_Lxx.py. Cada experimento guarda una copia de este módulo en
exp/Lxx/codigo/, así todos calculan EXACTAMENTE lo mismo y cada uno sigue siendo reproducible por sí solo.

Contenido (recomendaciones del profesor, secciones 1.3 y 1.4):
  - rank_cero_fijo      ranking por mes con cero fijo y signo (clase 9).
  - posicion_de_lag     lags por UNIÓN con (cliente, mes - k): los meses faltantes quedan NA (no se usa shift por fila).
  - tendencia_promedio  pendiente de la recta de cuadrados mínimos y promedio sobre una ventana de 3 meses
                        (mes actual y los 2 anteriores). Réplica de fhistC del ejemplo en R con ventana=3,
                        pero por MES CALENDARIO y no por fila: cada mes disponible aporta un punto con su
                        posición real (1, 2, 3); se necesitan al menos 2 puntos, si no, NA.
  - flag_zero           variable _zero: 1 si el original vale cero, NA si era NA, 0 en el resto.
"""
import numpy as np
import pandas as pd

# Columnas SIN historia: su valor cambia de forma determinística con el calendario
# (su delta sería constante) -> solo se rankean, no llevan lags, deltas, tendencia ni promedio.
SIN_HISTORIA = [
    "cliente_edad", "cliente_antiguedad",
    "Master_fechaalta", "Visa_fechaalta", "Master_Fvencimiento", "Visa_Fvencimiento",
    "Master_fultimo_cierre", "Visa_fultimo_cierre", "Master_Finiciomora", "Visa_Finiciomora",
]
NO_RANKEAR = ["numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria"]


def rank_cero_fijo(v, idx_mes):
    """Ranking con cero fijo y signo, dentro de cada mes. v: float64. Devuelve float32."""
    out = np.full(v.shape, np.nan, dtype=np.float32)
    for idx in idx_mes:
        x = v[idx]
        r = np.full(len(x), np.nan)
        r[x == 0] = 0.0                                   # el cero se queda en cero
        pos, neg = x > 0, x < 0                           # (los NaN no entran en ninguna máscara)
        if pos.any():
            r[pos] = pd.Series(x[pos]).rank(method="average", pct=True).to_numpy()
        if neg.any():
            r[neg] = -pd.Series(-x[neg]).rank(method="average", pct=True).to_numpy()
        out[idx] = r
    return out


def posicion_de_lag(key, k):
    """Para cada fila, la posición de la fila del MISMO cliente en el mes (mes - k); -1 si no existe."""
    orden = np.argsort(key, kind="stable")
    ks = key[orden]
    objetivo = key - k
    i = np.searchsorted(ks, objetivo)
    i = np.clip(i, 0, len(ks) - 1)
    existe = ks[i] == objetivo
    pos = orden[i]
    pos[~existe] = -1
    return pos


def aplicar_lag(x, pos):
    out = np.full(x.shape, np.nan)
    ok = pos >= 0
    out[ok] = x[pos[ok]]
    return out


def tendencia_promedio(x, l1, l2):
    """Ventana de 3 meses (x = mes actual, l1 = mes-1, l2 = mes-2; NaN si falta).
    Devuelve (pendiente de la recta de cuadrados mínimos, promedio), ambos float64.
    Los puntos tienen x = 1 (l2), 2 (l1) y 3 (actual); los NaN no aportan. Con menos de 2 puntos: NaN, NaN."""
    ys = (l2, l1, x)
    xs = (1.0, 2.0, 3.0)
    n = sx = sy = sxy = sxx = 0.0
    for xv, y in zip(xs, ys):
        m = ~np.isnan(y)
        n = n + m
        sx = sx + xv * m
        sy = sy + np.where(m, y, 0.0)
        sxy = sxy + xv * np.where(m, y, 0.0)
        sxx = sxx + (xv * xv) * m
    ok = n >= 2
    with np.errstate(divide="ignore", invalid="ignore"):
        pend = (n * sxy - sx * sy) / (n * sxx - sx * sx)
        prom = sy / n
    return np.where(ok, pend, np.nan), np.where(ok, prom, np.nan)


def flag_zero(x):
    """1.0 si x == 0, 0.0 si x != 0, NaN si x es NaN (float32). Estas variables NO se rankean."""
    return np.where(np.isnan(x), np.nan, (x == 0).astype("float32")).astype("float32")
