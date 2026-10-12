"""Carga del dataset y armado de X / y por meses."""
import numpy as np
import pandas as pd

from . import config

COLUMNAS_CLASE = ['clase_ternaria', 'clase_binaria']


def liberar_memoria():
    """Libera buffers de pyarrow y fuerza al sistema operativo a recuperar memoria."""
    try:
        import pyarrow as pa
        pa.default_memory_pool().release_unused()
    except Exception:
        pass
    import gc
    gc.collect()
    try:
        import ctypes
        ctypes.CDLL('libc.so.6').malloc_trim(0)
    except Exception:
        pass


def cargar_datos(dataset='final', usar_cache=True):
    """Lee uno de los datasets de config.DATASETS.

    Los .parquet se leen directo. Para un .csv, la primera vez se guarda una copia en
    cache/<nombre>.parquet y las siguientes se lee esa copia (mismo contenido, mucho mas
    rapido); si el CSV es mas nuevo que la copia, se regenera.
    """
    if dataset not in config.DATASETS:
        raise ValueError(f"Dataset '{dataset}' no existe. Opciones: {list(config.DATASETS)}")
    archivo = config.DATASETS[dataset]
    if not archivo.exists():
        raise FileNotFoundError(f'No existe {archivo}. Para el dataset extendido: '
                                f'.venv/bin/python generate_features_extendido.py')
    if archivo.suffix == '.parquet':
        data = pd.read_parquet(archivo)
    else:
        csv = archivo
        parquet = config.CACHE_DIR / (csv.stem + '.parquet')
        if usar_cache and parquet.exists() and parquet.stat().st_mtime >= csv.stat().st_mtime:
            data = pd.read_parquet(parquet)
        else:
            data = pd.read_csv(csv)
            if usar_cache:
                data.to_parquet(parquet, index=False)

    # Reducir consumo de memoria: convertir float64 a float32 y liberar buffers
    for c in data.select_dtypes(include=['float64']).columns:
        data[c] = data[c].astype('float32')
    liberar_memoria()
    return data


def agregar_clase_binaria(data):
    """BAJA+2 -> 1, BAJA+1 y CONTINUA -> 0 (modelo A)."""
    data['clase_binaria'] = np.where(data['clase_ternaria'] == 'BAJA+2', 1, 0)
    return data


def separar(data, meses, columnas_excluidas=()):
    """X, y (binaria) y clase ternaria de los meses indicados.

    columnas_excluidas: variables que no se usan como feature (ej. numero_de_cliente).
    """
    datos_meses = data[data['foto_mes'].isin(meses)]
    X = datos_meses.drop(COLUMNAS_CLASE + list(columnas_excluidas), axis=1)
    y = datos_meses['clase_binaria']
    clase = datos_meses['clase_ternaria']
    return X, y, clase
