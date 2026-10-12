"""Armado y validación de archivos de submit (formato Zulip de la cátedra).

Formato: CSV sin encabezado, un numero_de_cliente entero por línea (los clientes a estimular),
entre 8000 y 15000 registros. Cuidado con la notación científica (48000000 → 4.8e+07).
"""
import re
from pathlib import Path

import numpy as np

from config import RAIZ

SUBMISSIONS = RAIZ / "competencia" / "submissions"
MIN_ENVIOS, MAX_ENVIOS = 8000, 15000


def guardar_submit(ids, nombre: str, carpeta: Path = SUBMISSIONS) -> Path:
    """Escribe `<nombre>.csv` con los ids a estimular. Usar un nombre de archivo distinto en cada submit."""
    ids = np.asarray(ids)
    if not np.all(np.mod(ids, 1) == 0):
        raise ValueError("los numero_de_cliente deben ser enteros")
    ids = ids.astype(np.int64)
    if len(np.unique(ids)) != len(ids):
        raise ValueError("hay numero_de_cliente repetidos")
    if not MIN_ENVIOS <= len(ids) <= MAX_ENVIOS:
        raise ValueError(f"{len(ids)} registros: el bot espera entre {MIN_ENVIOS} y {MAX_ENVIOS}")
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", nombre):
        raise ValueError("nombre sin espacios ni caracteres raros")
    ruta = carpeta / f"{nombre}.csv"
    if ruta.exists():
        raise FileExistsError(f"{ruta.name} ya existe: usar un nombre distinto para cada submit")
    carpeta.mkdir(parents=True, exist_ok=True)
    np.savetxt(ruta, ids, fmt="%d")  # %d garantiza enteros, sin encabezado
    return ruta


def top_k_ids(ids, proba, k: int):
    """Los k clientes con mayor probabilidad (corte por cantidad de envíos)."""
    orden = np.argsort(-np.asarray(proba), kind="stable")[:k]
    return np.asarray(ids)[orden]


def cuerpo_mensaje(nombre_submit: str) -> str:
    """Cuerpo del mensaje de Zulip. Se adjuntan uno o más .csv (máx 20 por submit, 13 submits/día)."""
    return f"submit    {nombre_submit}"
