"""Constantes y rutas compartidas por todos los modulos y notebooks."""
import os
from pathlib import Path

import numpy as np

# Carpeta clusters/ (este archivo vive en clusters/comp/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Datasets disponibles (setting DATASET de los notebooks). Ver FEATURES.md.
DATASETS = {
    'final': BASE_DIR / 'competencia_01_final.csv',               # 195 columnas
    'extendido': BASE_DIR / 'competencia_01_extendido.parquet',   # final + inflacion + lags 1-2 + deltas 1-2
}
DATASET_CSV = DATASETS['final']
CACHE_DIR = BASE_DIR / 'cache'          # copia en parquet del CSV (carga mucho mas rapida)

# Salidas. La variable de entorno COMP_SALIDAS_DIR permite mandarlas a otra carpeta (ej. pruebas).
SALIDAS_DIR = Path(os.environ.get('COMP_SALIDAS_DIR', BASE_DIR))
DB_DIR = SALIDAS_DIR / 'db'                # estudios de Optuna
MODELOS_DIR = SALIDAS_DIR / 'modelos'      # modelos LightGBM en formato texto
RESULTADOS_DIR = SALIDAS_DIR / 'resultados'  # tablas ya calculadas (para no recalcular)
SUBMITS_DIR = SALIDAS_DIR / 'submits'        # archivos para subir a la plataforma

for _d in (CACHE_DIR, DB_DIR, MODELOS_DIR, RESULTADOS_DIR, SUBMITS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Matriz de ganancia
GANANCIA_ACIERTO = 1_072_500
COSTO_ESTIMULO = 27_500
UMBRAL = 0.025  # COSTO_ESTIMULO / (GANANCIA_ACIERTO + COSTO_ESTIMULO)

# Clase objetivo (setting CLASE_OBJETIVO): que clases son el 1 con el que se ENTRENA.
# La ganancia siempre se cuenta con los BAJA+2 reales (es lo unico que paga).
CLASES_OBJETIVO = {
    'baja2': ['BAJA+2'],              # modelo A (por defecto)
    'baja1y2': ['BAJA+1', 'BAJA+2'],  # modelo B
}

# Como puntua Optuna cada trial (setting METRICA_OPTUNA):
#   'umbral'          -> ganancia con p >= UMBRAL (0.025). Por defecto: reproduce todo lo ya corrido.
#   'umbral_ajustado' -> ganancia con p >= UMBRAL / s, donde s = proporcion de BAJA+2 entre los
#                        positivos de entrenamiento (para el modelo B; en el A, s = 1 y da 0.025)
#   'franja'          -> ganancia promedio enviando al top 5%, 6%, 7%, 8% y 9% de los clientes
#                        (el rango que acepta la plataforma: 8000 a 15000 de ~164000)
METRICAS_OPTUNA = ['umbral', 'umbral_ajustado', 'franja']
FRANJA = (0.05, 0.06, 0.07, 0.08, 0.09)

# Meses
MES_INICIO = 202103   # primer mes del dataset
MES_TRAIN = 202103    # por defecto (esquema del notebook de clase): entrena en marzo...
MES_TEST = 202105     # ...y mide la ganancia en mayo

SEMILLA = 6389
SEMILLA_CLASE = 17  # la del notebook de clase z601: solo para reproducirlo (experimento it00_z601 original)

# Estudio de Optuna original (notebook z601_clases_final_csv.ipynb)
STORAGE_OPTUNA_ORIGINAL = f"sqlite:///{BASE_DIR / 'db' / 'optimization_lgbm.db'}"
STUDY_NAME_ORIGINAL = 'exp_301_lgbm_sss'

# Los rangos de busqueda de Optuna (espacios it00_z601, it01_bordes, ...) estan en
# comp/optimizacion_optuna.py, ESPACIOS.

# Parametros fijos de LightGBM (los que Optuna no busca)
PARAMS_FIJOS = {
    'objective': 'binary',
    'boosting_type': 'gbdt',
    'first_metric_only': True,
    'boost_from_average': True,
    'feature_pre_filter': False,
    'max_bin': 31,
}

NUM_BOOST_ROUND = 250  # cantidad de arboles fija del esquema original

N_TRIALS = 60    # trials de Optuna por experimento (solo se corren los que faltan)
N_SEMILLAS = 20   # semillas para la prueba de estabilidad y para el ensamble


def generar_semillas(semilla=SEMILLA, n=50):
    """Mismas 50 semillas que el notebook original (np.random.seed + choice)."""
    np.random.seed(semilla)
    return np.random.choice(1000000, size=n, replace=False).tolist()
