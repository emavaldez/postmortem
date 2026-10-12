# Competencia 01 — entrega final: ensamble ens04_e032_e033_e034 con 10500 envíos

Esta carpeta contiene todo lo necesario para replicar **exactamente** el archivo que se subió
como entrega final de la competencia. La entrega es un **ensamble**: el promedio de los rankings
de 3 modelos (cada uno, a su vez, un ensamble de LightGBM con varios conjuntos de
hiperparámetros y semillas). Cada componente está en su propia subcarpeta con su configuración,
sus hiperparámetros y sus modelos entrenados.

| | |
|---|---|
| Archivo entregado | `20261011-091551_ens04_e032_e033_e034_e10500.csv` (solo `numero_de_cliente`, sin encabezado, 10500 filas) |
| sha256 | `385da7093ab1e93b894016de3cb537460dc48ee0cc2befdce943ddbae850d5df` |
| Puntaje público | 110.1650 M |
| Período objetivo | 202108 |

El dataset de la competencia **no está en el repositorio**: el script lo descarga solo desde la
URL pública de la cátedra (`competencia_01_crudo.csv`).

## Componentes del ensamble

| # | Experimento | Modelos | Peso | Run de origen |
|---|---|---|---|---|
| 0 | `e032_expansiva_auc_topk` | 24 | 1 | `20261009-232755_e032_expansiva_auc_topk` |
| 1 | `e033_montos_rank_cero_fijo` | 24 | 1 | `20261011-023622_e033_montos_rank_cero_fijo` |
| 2 | `e034_comportamiento` | 24 | 1 | `20261011-041115_e034_comportamiento` |

Combinación: cada componente predice la probabilidad de BAJA+2 en 202108; se convierte en su
rank normalizado dentro del mes (`competencia_1/pipeline/ensamble.py`, método `rank`), se
promedian los rankings y se envían los 10500 clientes de mayor valor.

## Cómo replicarla

Hace falta Python 3.11 y unos 16 GB de RAM. Hay tres niveles; en todos se reproduce cada
componente (y se verifica el sha256 de su propio CSV), se arma el ensamble y se compara el sha256
del CSV final con el de arriba (`[ensamble] RESULTADO: OK, coincide`):

| Modo | Qué rehace | Tiempo aprox. |
|---|---|---|
| `predecir` (default) | Datos y features desde el crudo, y **predice** con los 72 modelos ya entrenados | ~1 h |
| `entrenar` | Lo anterior, pero **reentrena** los 72 modelos con los hiperparámetros de cada componente | ~4 h |
| `completo` | **Todo, incluida la optimización de hiperparámetros** de cada componente (Optuna, 180 trials en total) | ~5 h |

**Linux o VM de GCP:**

```bash
git clone https://github.com/pfranzd/dmeyf2026-entregas.git && cd dmeyf2026-entregas/competencia_01
bash reproducir.sh              # o: bash reproducir.sh entrenar | bash reproducir.sh completo
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/pfranzd/dmeyf2026-entregas.git; cd dmeyf2026-entregas\competencia_01
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements-lock.txt
$env:ENTREGA_MODO = "predecir"      # o "entrenar" / "completo"
.venv\Scripts\python entrega.py
```

También se puede abrir `entrega.ipynb` (es el mismo código que `entrega.py`) y ejecutarlo
completo; el modo se elige en la segunda celda.

El CSV del ensamble queda en `work/entrega/runs/<fecha>_ensamble/submits/` y los de cada
componente en `work/entrega/runs/<fecha>_entrega/submits/`.

## Entorno

- `requirements-lock.txt`: **versiones exactas** de todas las librerías (incluidas las
  transitivas) con las que se generó la entrega. `requirements.txt` lista solo las directas.
- Python 3.11 (`.python-version`). El script avisa si alguna versión instalada difiere.
- La igualdad byte a byte depende de las versiones de LightGBM y DuckDB y de
  `lgbm.fijos.num_threads` (8) en `competencia_1/configs/base.yaml`; no los cambies.

## Qué hace cada modelo

### 0_e032_expansiva_auc_topk

- LightGBM, objetivo `binary` sobre `BAJA+1 + BAJA+2`; la ganancia se mide sobre BAJA+2 (+780.000 / −20.000).
- Features: datos originales + familias temporales (lags, deltas, ventanas, tendencia) según `competencia_1/configs/exp/e032_expansiva_auc_topk.yaml`.
- Optimización: validación temporal con gap de 2 meses; objetivo `auc` promedio de los folds:
  - train [202103] → validación 202105
  - train [202103, 202104] → validación 202106
- Undersampling de CONTINUA en la optimización: 0.25 (el modelo final entrena sin undersampling).
- Modelo final entrenado con los meses [202103, 202104, 202105, 202106]; predice 202108.
- Ensamble final: 12 conjuntos de hiperparámetros × 2 semillas; se promedian las probabilidades.

### 1_e033_montos_rank_cero_fijo

- LightGBM, objetivo `binary` sobre `BAJA+1 + BAJA+2`; la ganancia se mide sobre BAJA+2 (+780.000 / −20.000).
- Features: datos originales + familias temporales (lags, deltas, ventanas, tendencia) según `competencia_1/configs/exp/e033_montos_rank_cero_fijo.yaml`.
- Optimización: validación temporal con gap de 2 meses; objetivo `auc` promedio de los folds:
  - train [202103] → validación 202105
  - train [202103, 202104] → validación 202106
- Undersampling de CONTINUA en la optimización: 0.25 (el modelo final entrena sin undersampling).
- Modelo final entrenado con los meses [202103, 202104, 202105, 202106]; predice 202108.
- Ensamble final: 12 conjuntos de hiperparámetros × 2 semillas; se promedian las probabilidades.

### 2_e034_comportamiento

- LightGBM, objetivo `binary` sobre `BAJA+1 + BAJA+2`; la ganancia se mide sobre BAJA+2 (+780.000 / −20.000).
- Features: datos originales + familias temporales (lags, deltas, ventanas, tendencia) según `competencia_1/configs/exp/e034_comportamiento.yaml`.
- Optimización: validación temporal con gap de 2 meses; objetivo `auc` promedio de los folds:
  - train [202103] → validación 202105
  - train [202103, 202104] → validación 202106
- Undersampling de CONTINUA en la optimización: 0.25 (el modelo final entrena sin undersampling).
- Modelo final entrenado con los meses [202103, 202104, 202105, 202106]; predice 202108.
- Ensamble final: 12 conjuntos de hiperparámetros × 2 semillas; se promedian las probabilidades.

## De dónde salen los hiperparámetros (optimización)

### 0_e032_expansiva_auc_topk

Los hiperparámetros **no están fijados a mano**: salen de una optimización bayesiana con Optuna, incluida en esta carpeta.

- Estudio: `optimizacion/0_e032_expansiva_auc_topk/estudio.db` (SQLite de Optuna, 60 trials, 37 completos y 23 podados) y `optimizacion/0_e032_expansiva_auc_topk/resumen.json`.
- La entrega usa los 12 mejores trials: #43, #41, #32, #22, #27, #44, #57, #31, #51, #42, #52, #21.
- Para rehacerla de punta a punta: el modo `completo` (corre `competencia_1/configs/exp/e032_expansiva_auc_topk.yaml`: Optuna → mejores trials → modelos → CSV) y comprueba el sha256.


### 1_e033_montos_rank_cero_fijo

Los hiperparámetros **no están fijados a mano**: salen de una optimización bayesiana con Optuna, incluida en esta carpeta.

- Estudio: `optimizacion/1_e033_montos_rank_cero_fijo/estudio.db` (SQLite de Optuna, 60 trials, 38 completos y 22 podados) y `optimizacion/1_e033_montos_rank_cero_fijo/resumen.json`.
- La entrega usa los 12 mejores trials: #57, #55, #59, #58, #15, #54, #14, #21, #27, #42, #56, #34.
- Para rehacerla de punta a punta: el modo `completo` (corre `competencia_1/configs/exp/e033_montos_rank_cero_fijo.yaml`: Optuna → mejores trials → modelos → CSV) y comprueba el sha256.


### 2_e034_comportamiento

Los hiperparámetros **no están fijados a mano**: salen de una optimización bayesiana con Optuna, incluida en esta carpeta.

- Estudio: `optimizacion/2_e034_comportamiento/estudio.db` (SQLite de Optuna, 60 trials, 34 completos y 26 podados) y `optimizacion/2_e034_comportamiento/resumen.json`.
- La entrega usa los 12 mejores trials: #53, #52, #15, #31, #14, #24, #32, #21, #51, #16, #57, #44.
- Para rehacerla de punta a punta: el modo `completo` (corre `competencia_1/configs/exp/e034_comportamiento.yaml`: Optuna → mejores trials → modelos → CSV) y comprueba el sha256.


## Contenido de la carpeta

```
entrega.py / entrega.ipynb     punto de entrada (mismo código)
reproducir.sh                  atajo para Linux / GCP
requirements*.txt, .python-version
competencia_1/                 pipeline (datos → features → Optuna → modelos → CSV)
  configs/base.yaml            defaults
  configs/exp/*.yaml           configuración de cada experimento (optimización + final)
  definitiva/entrega.json      el ensamble: componentes, método, pesos y sha256 esperado
  definitiva/componentes/<i>_<experimento>/   config.yaml, params.json, entrega.json y modelos/
dmeyf/, config/                métricas y semillas
optimizacion/<i>_<experimento>/  evidencia de la optimización de cada componente (Optuna)
```

## Trazabilidad

Generada el 2026-10-11 12:13 desde el repositorio de trabajo, commit `27084eb76e`, ensamble
`20261011-091551_ens04_e032_e033_e034`. El CSV de ese ensamble coincide byte a byte con el que reproduce esta carpeta.
