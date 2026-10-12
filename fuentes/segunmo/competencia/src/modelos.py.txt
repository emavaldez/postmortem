"""Guardado de modelos y huellas, para NO tener que reentrenar (cada modelo del final cuesta minutos) y para poder verificar la reproducción.

- El modelo (texto de LightGBM, decenas de MB) se guarda en `artifacts/modelos_final/` -> NO se versiona (tamaño; el repo es público).
- Lo que SÍ se versiona es `competencia/modelos_manifiesto.csv`: por cada modelo, la huella SHA-256 del archivo de modelo y de su predicción sobre el mes a puntuar.
  Quien regenere el pipeline puede comprobar que obtiene exactamente los mismos modelos comparando huellas (`competencia/verificar_modelos.py`).
"""
import csv
import hashlib
from pathlib import Path

import numpy as np

from config import RAIZ

CARPETA = RAIZ / "artifacts" / "modelos_final"
MANIFIESTO = RAIZ / "competencia" / "modelos_manifiesto.csv"
COLUMNAS = ["nombre", "sha256_modelo", "sha256_prediccion"]


def huella_arreglo(a) -> str:
    return hashlib.sha256(np.ascontiguousarray(a, dtype=np.float64).tobytes()).hexdigest()


def huella_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _leer() -> dict:
    if not MANIFIESTO.exists():
        return {}
    with open(MANIFIESTO, newline="") as f:
        return {fila["nombre"]: fila for fila in csv.DictReader(f)}


def guardar_modelo(booster, nombre: str, prediccion=None) -> Path:
    """Guarda el booster en artifacts/modelos_final/<nombre>.txt y registra sus huellas en el manifiesto (reemplaza la entrada si ya existía)."""
    CARPETA.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA / f"{nombre}.txt"
    booster.save_model(str(ruta))
    filas = _leer()
    filas[nombre] = {"nombre": nombre, "sha256_modelo": huella_archivo(ruta),
                     "sha256_prediccion": huella_arreglo(prediccion) if prediccion is not None else ""}
    with open(MANIFIESTO, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas[k] for k in sorted(filas))
    return ruta


def verificar_orden_cache(tmp: Path, ids) -> None:
    """Guarda contra un error silencioso: las predicciones cacheadas (`tmp/*.npy`) son vectores POSICIONALES (una entrada por fila de scoring).
    Si se generaron con otro orden de filas (p. ej. antes del ORDER BY explícito del 2026-10-10) y se cargan con el orden actual, los scores
    quedarían asignados a los clientes equivocados sin ningún error. Se deja una marca con la huella del orden de `ids` y se exige que coincida."""
    huella = hashlib.md5(np.ascontiguousarray(ids, dtype=np.int64).tobytes()).hexdigest()
    marca = Path(tmp) / "_orden_scoring.md5"
    if marca.exists():
        if marca.read_text().strip() != huella:
            raise RuntimeError(f"{tmp}: las predicciones cacheadas se generaron con otro orden de filas. Borrar o mover esa carpeta tmp/ y reentrenar.")
    else:
        if any(Path(tmp).glob("*.npy")):
            raise RuntimeError(f"{tmp}: hay predicciones cacheadas SIN marca de orden (corrida anterior al ORDER BY explícito). Borrar o mover esa carpeta tmp/ y reentrenar.")
        Path(tmp).mkdir(parents=True, exist_ok=True)
        marca.write_text(huella)
