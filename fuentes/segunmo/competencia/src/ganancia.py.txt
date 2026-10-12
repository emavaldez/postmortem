"""Funciones de ganancia de la campaña de retención.

y_true: array de etiquetas ('BAJA+2' / otras) o binario (1 = BAJA+2).
proba:  probabilidad predicha de BAJA+2.
"""
import numpy as np

from config import COSTO_ESTIMULO, GANANCIA_ACIERTO, POSITIVO, UMBRAL


def _es_positivo(y_true) -> np.ndarray:
    y = np.asarray(y_true)
    return (y == POSITIVO) if y.dtype.kind in "OUS" else (y == 1)


def ganancia_por_umbral(y_true, proba, umbral: float = UMBRAL, prop: float = 1.0) -> float:
    """Ganancia total si se estimula a todos los clientes con proba >= umbral.
    `prop` es la fracción de los datos evaluada (se reescala dividiendo por prop)."""
    pos = _es_positivo(y_true)
    estimula = np.asarray(proba) >= umbral
    return float((np.where(pos, GANANCIA_ACIERTO, -COSTO_ESTIMULO)[estimula]).sum() / prop)


def ganancia_acumulada(y_true, proba) -> np.ndarray:
    """Ganancia acumulada ordenando por proba descendente: el elemento k-1 es la ganancia de enviar a los k primeros."""
    pos = _es_positivo(y_true)
    orden = np.argsort(-np.asarray(proba), kind="stable")
    return np.cumsum(np.where(pos[orden], GANANCIA_ACIERTO, -COSTO_ESTIMULO))


def mejor_corte(y_true, proba) -> tuple[int, float]:
    """(cantidad óptima de envíos, ganancia máxima). OJO: óptimo ex post sobre estos datos."""
    acum = ganancia_acumulada(y_true, proba)
    k = int(np.argmax(acum))
    return k + 1, float(acum[k])
