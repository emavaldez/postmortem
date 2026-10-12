# nicozare — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: nicozare
- Repositorio: https://github.com/nicozare/primera-competencia-dmeyf
- Link posteado: https://github.com/nicozare/primera-competencia-dmeyf
- Commit: 0fc28e8d398d2f21eb97b27fbfe32cf751e79195
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/nicozare/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/nicozare.json

## Resumen

Repositorio en Python con tres scripts numerados (scripts/01, 02 y 03), dos módulos compartidos (config.py y comun.py), una carpeta con la búsqueda de hiperparámetros, 15 modelos LightGBM guardados y el CSV entregado. El paso 1 arma con DuckDB la clase_ternaria, descarta 4 columnas listadas a mano, marca con cobra_aguinaldo los saldos de junio y diciembre que superan 1,4 veces el promedio o el máximo previo del cliente (y los divide por 1,111) y agrega lag 1, lag 2, delta 1 y delta 2 de cada columna numérica (741 variables en total). El paso 2 entrena LightGBM con clase binaria (positivo = BAJA+1 o BAJA+2), submuestreo de CONTINUA al 50 % y 5 semillas × 3 submodelos: primero deja fuera el último mes con clase completa, mide ahí la ganancia y elige la cantidad de clientes entre 8.000 y 15.000; después reentrena con todos los meses con clase. El paso 3 promedia las probabilidades de los 15 modelos sobre el mes más reciente del dataset y escribe los 11.500 clientes de mayor probabilidad. Los hiperparámetros se leen de un JSON que, según el README, sale de una búsqueda con Optuna de 30 trials incluida en el repositorio. Los meses no están escritos en el código: se toman por posición dentro del dataset.

**Qué entrega.** prediccion_final/prediccion_final.csv: 11.500 numero_de_cliente, uno por línea, sin encabezado. Según prediccion_final/README.md, es el mismo contenido (mismo SHA-256) que submissions/submission_promedio.csv, el archivo que escribe scripts/03_generar_submission.py con los 11.500 clientes de mayor probabilidad promedio entre las 5 semillas en el mes más reciente del dataset. El SHA-256 del CSV incluido coincide con el que figura en ese README.

**Cómo se ejecuta.** Según el README: poner el dataset crudo en data/dataset_crudo.csv (no viene en el repositorio), correr `uv sync` y luego, en orden, `uv run python scripts/01_feature_engineering.py`, `uv run python scripts/02_entrenar_ensamble.py` (indicado como opcional, porque los modelos ya entrenados vienen en modelos/) y `uv run python scripts/03_generar_submission.py`. La búsqueda de hiperparámetros se corre aparte, desde optimizacion_hiperparametros/, con `uv run --with duckdb --with lightgbm --with numpy --with optuna --with pandas --with scikit-learn python buscar_hiperparametros.py`.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria. En el entrenamiento del ensamble (02_entrenar_ensamble.py) el positivo es BAJA+1 o BAJA+2. En la búsqueda de hiperparámetros (buscar_hiperparametros.py) el positivo es sólo BAJA+2. La ganancia medida en el holdout cuenta como acierto sólo a BAJA+2. La clase_ternaria se calcula en el paso 1 a partir de la presencia del cliente uno y dos meses después.
- **Meses de entrenamiento:** —
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** En cada submodelo se conservan todas las filas positivas (BAJA+1 y BAJA+2) y las filas CONTINUA cuyo número al azar es menor o igual a 0,5 (SUBMUESTREO_CONTINUA = 0.5), con un generador de numpy sembrado con la semilla interna del submodelo. min_data_in_leaf se divide por 0,5 (380 pasa a 760). La búsqueda de hiperparámetros no submuestrea.
- **Calidad de datos:** Se excluyen del dataset de variables 4 columnas escritas en config.COLUMNAS_CON_DRIFT: Master_fultimo_cierre, Visa_fultimo_cierre, Master_Finiciomora y Visa_Finiciomora. En junio y diciembre, mcuentas_saldo se divide por 1,111 en las filas donde es mayor o igual a 1,4 veces el promedio o el máximo del saldo del mismo cliente en sus meses anteriores; esas filas quedan marcadas con cobra_aguinaldo = 1. Las columnas cuyo tipo no es numérico tampoco pasan al dataset de variables.
- **Drifting:** No se aplican transformaciones por mes (rank, deflación o estandarización). Se excluyen las 4 columnas de config.COLUMNAS_CON_DRIFT; según el README se identificaron con PSI (Population Stability Index). El cálculo de PSI no figura en el código del repositorio.
- **Variables dentro del mes:** No se observa en el código. Según el README, se probaron cocientes entre variables del mismo mes y no se incorporaron.
- **Variables históricas:** Para cada una de las 148 columnas numéricas: lag 1, lag 2, delta 1 y delta 2 (592 columnas), tomando la fila anterior y la de dos filas atrás del mismo cliente ordenado por foto_mes. Además, cobra_aguinaldo (0/1), que compara el saldo de junio o diciembre con el promedio y el máximo de los meses anteriores del cliente; no recibe lag ni delta. No hay tendencias, promedios ni mínimos o máximos de ventana como variables.
- **Selección de variables:** No se observa en el código: el modelo usa todas las columnas de data/dataset_features.csv salvo numero_de_cliente, foto_mes, clase_ternaria y clase_binaria (741 según modelos/features.txt). Según el README, se probó una selección por importancia contra canaritos y no se incorporó.
- **Optimización de hiperparámetros:** Optuna, 30 trials, estudio lgbm_drift_aguinaldo guardado en SQLite; create_study no indica sampler y el docstring y el README lo nombran TPE. Espacio: num_leaves 8 a 100, learning_rate 0,005 a 0,3, min_data_in_leaf 1 a 1000, feature_fraction 0,1 a 1,0 y bagging_fraction 0,1 a 1,0. Cada trial corre lgb.cv con 5 particiones de StratifiedShuffleSplit (30 % de prueba, random_state 100081), hasta 1000 rondas, early stopping de int(50 + 5 / learning_rate) rondas y una métrica propia: ganancia de las filas con probabilidad mayor o igual a 0,025, dividida por 0,3. Usa positivo = BAJA+2, sin submuestreo, sobre los meses con clase menos el último. La base incluida tiene 30 trials completos; el de mayor valor es el número 26 (1.193.298.333) y sus valores son los de modelos/mejores_hiperparametros.json.
- **Hiperparámetros finales:** De modelos/mejores_hiperparametros.json: num_leaves 41, learning_rate 0,009613, min_data_in_leaf 380 (se entrena con 760 = 380 / 0,5), feature_fraction 0,2555, bagging_fraction 0,5477 y 690 rondas. Fijos en armar_params: objective binary, boosting_type gbdt, max_bin 31, boost_from_average True, feature_pre_filter False, first_metric_only False. El diccionario no incluye bagging_freq; los 15 modelos guardados registran bagging_freq: 0.
- **Semillas:** 5 semillas escritas en config.py (100081, 100103, 100129, 100151, 100169). Cada una genera 3 submodelos con semilla interna = semilla + k × 7919 (k = 0, 1, 2), lo que da 15 semillas distintas (por ejemplo 100081, 108000 y 115919), usadas como seed de LightGBM y para el submuestreo. La búsqueda de hiperparámetros usa la semilla 100081.
- **Cantidad de semillas:** 15
- **Ensamble:** Promedio de probabilidades de 15 modelos LightGBM con los mismos hiperparámetros y distinta semilla: primero el promedio de los 3 submodelos de cada semilla y después el promedio de las 5 semillas (submission_promedio.csv). También se escribe un archivo por semilla con el promedio de sus 3 submodelos.
- **Corte:** Cantidad fija de clientes ordenados por probabilidad descendente. Se elige en el holdout: para cada corte de 8.000 a 15.000 de a 250 (29 valores) se promedia la ganancia de las 5 semillas y se toma el corte de mayor ganancia promedio, que se guarda en modelos/corte_optimo.txt. El archivo incluido contiene 11500.
- **Validación:** Holdout en el último mes con clase completa: se entrenan 5 × 3 submodelos con los meses anteriores y se mide en ese mes la ganancia (1.072.500 por cada BAJA+2 seleccionado y −27.500 por cada otro cliente) en cada corte. Los meses no están escritos en el código: detectar_meses toma como predicción el último mes del dataset, como entrenamiento todos menos los dos últimos y como holdout el último de entrenamiento; con un dataset que termina en 202108 eso da holdout 202106 y predicción 202108. En la búsqueda de hiperparámetros se usa lgb.cv con 5 particiones aleatorias estratificadas sobre los meses anteriores al holdout. Según el README, la ganancia en el holdout con 11.500 clientes es $392M.
- **Salidas:** Paso 1: data/dataset_features.csv. Paso 2: output/ganancia_por_corte.csv, modelos/corte_optimo.txt, modelos/features.txt y 15 archivos modelos/lgb_seed_<semilla>_k<k>.txt. Paso 3: 5 archivos submissions/submission_seed_<semilla>.csv y submissions/submission_promedio.csv, con un numero_de_cliente por línea y sin encabezado. La búsqueda escribe optimizacion_lgbm.db y resultado_busqueda.json. El repositorio incluye prediccion_final/prediccion_final.csv (11.500 líneas).

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)
- Validación cruzada (`validacion.validacion_cruzada`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Técnicas sólo exploradas

- Random Forest (`modelo.random_forest`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: no
- Entorno declarado: pyproject.toml: requires-python >= 3.11 y dependencias duckdb>=1.5.5, lightgbm>=4.7.0, numpy>=2.4.6 y pandas>=3.0.5; .python-version: 3.11. El README usa uv (uv sync, uv run) y .gitignore excluye uv.lock. optuna y scikit-learn no están en pyproject.toml: el README de la búsqueda los agrega con uv run --with. No se declara máquina ni sistema operativo.

## Pasos del camino de la entrega

1. **Rutas y constantes.** config.py define las rutas relativas a la carpeta del repositorio, las 5 semillas, los valores de la función de ganancia (1.072.500 y 27.500), el rango del barrido del corte (8.000 a 15.000, paso 250), las 4 columnas a excluir, las constantes de aguinaldo (1,4; meses 6 y 12; 1,111), la proporción de submuestreo (0,5) y la cantidad de submodelos por semilla (3). (`scripts/config.py` líneas 1–46)
2. **Lectura del dataset crudo y selección de columnas.** Carga data/dataset_crudo.csv en DuckDB y arma la lista de columnas numéricas, dejando fuera numero_de_cliente, foto_mes, clase_ternaria y las 4 columnas de COLUMNAS_CON_DRIFT. (`scripts/01_feature_engineering.py` líneas 38–48; `scripts/config.py` líneas 32–35)
3. **Cálculo de clase_ternaria.** Cruza todos los clientes con todos los meses y, según si el cliente está presente uno y dos meses después, asigna BAJA+1, BAJA+2 o CONTINUA; deja nulo cuando el dataset no tiene los meses siguientes. (`scripts/01_feature_engineering.py` líneas 50–64)
4. **Marca de aguinaldo y ajuste de mcuentas_saldo.** En junio y diciembre compara mcuentas_saldo con el promedio y el máximo de los meses anteriores del mismo cliente; si es mayor o igual a 1,4 veces alguno de los dos, marca cobra_aguinaldo = 1 y divide el saldo por 1,111. (`scripts/01_feature_engineering.py` líneas 66–95; `scripts/config.py` líneas 37–41)
5. **Lags, deltas y escritura del dataset de variables.** Agrega lag 1, lag 2, delta 1 y delta 2 de cada columna numérica por cliente y escribe data/dataset_features.csv con numero_de_cliente, foto_mes, clase_ternaria, cobra_aguinaldo, las columnas numéricas y las derivadas. (`scripts/01_feature_engineering.py` líneas 97–121)
6. **Búsqueda de hiperparámetros con Optuna.** Script aparte, corrido antes del pipeline según el README. Sobre los meses con clase menos el último, con positivo = BAJA+2, corre 30 trials de Optuna; cada trial evalúa 5 hiperparámetros con lgb.cv en 5 particiones aleatorias estratificadas y una métrica de ganancia. Escribe resultado_busqueda.json; los valores del trial de mayor ganancia son los que figuran en modelos/mejores_hiperparametros.json. (`optimizacion_hiperparametros/buscar_hiperparametros.py` líneas 42–50; `optimizacion_hiperparametros/buscar_hiperparametros.py` líneas 53–56; `optimizacion_hiperparametros/buscar_hiperparametros.py` líneas 59–90; `optimizacion_hiperparametros/buscar_hiperparametros.py` líneas 92–110; `modelos/mejores_hiperparametros.json` líneas 1–11)
7. **Parámetros del modelo.** Lee los hiperparámetros y la cantidad de rondas (690) del JSON y arma los parámetros de LightGBM, con min_data_in_leaf dividido por la proporción de submuestreo y max_bin 31. (`scripts/02_entrenar_ensamble.py` líneas 47–61)
8. **Clase binaria, variables y meses.** Lee el dataset de variables, crea clase_binaria (1 = BAJA+1 o BAJA+2), toma como variables todas las columnas salvo 4 y determina por posición los meses de entrenamiento (todos menos los dos últimos), el holdout (el último de entrenamiento) y el mes de predicción (el último del dataset). (`scripts/02_entrenar_ensamble.py` líneas 98–104; `scripts/comun.py` líneas 7–25)
9. **Submuestreo y entrenamiento de cada submodelo.** Cada submodelo usa la semilla interna semilla + k × 7919, conserva todos los positivos y el 50 % al azar de los negativos, y entrena 690 rondas de LightGBM sin conjunto de validación. (`scripts/02_entrenar_ensamble.py` líneas 64–68; `scripts/comun.py` líneas 32–40; `scripts/config.py` líneas 43–46)
10. **Control en holdout y elección del corte.** Entrena 5 semillas × 3 submodelos sin el mes de holdout, predice ese mes y, para cada corte de 8.000 a 15.000 de a 250, promedia la ganancia de las 5 semillas. Guarda la tabla en output/ganancia_por_corte.csv y el corte de mayor ganancia promedio en modelos/corte_optimo.txt. (`scripts/02_entrenar_ensamble.py` líneas 106–116; `scripts/02_entrenar_ensamble.py` líneas 75–94)
11. **Reentrenamiento con todos los meses con clase.** Vuelve a entrenar los 15 submodelos con todos los meses de entrenamiento, incluido el holdout, y guarda cada uno en modelos/lgb_seed_<semilla>_k<k>.txt junto con la lista de variables en modelos/features.txt. (`scripts/02_entrenar_ensamble.py` líneas 118–127)
12. **Predicción sobre el mes más reciente.** Carga los 15 modelos guardados, predice sobre las filas del último mes del dataset con las variables de features.txt y promedia los 3 submodelos de cada semilla. (`scripts/03_generar_submission.py` líneas 27–41)
13. **Selección de clientes y archivos de salida.** Lee el corte de modelos/corte_optimo.txt y escribe, sin encabezado, los numero_de_cliente de mayor probabilidad: un archivo por semilla y submission_promedio.csv con el promedio de las 5 semillas. Según prediccion_final/README.md, este último coincide con el archivo entregado. (`scripts/03_generar_submission.py` líneas 43–59; `prediccion_final/README.md` líneas 1–22)

## Archivos

- `pyproject.toml` · configuracion · TOML · 11 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicozare/pyproject.toml.txt) — Metadatos del proyecto para uv: requires-python >= 3.11 y dependencias duckdb>=1.5.5, lightgbm>=4.7.0, numpy>=2.4.6 y pandas>=3.0.5.
- `README.md` · explicacion · Markdown · 184 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicozare/README.md.txt) — Presentación de la entrega: diagrama del pipeline, comandos para correrlo, tablas con lo que hace cada script, una tabla de ganancia en el holdout por cantidad de clientes (según el README, $392M con 11.500) y la sección "Qué se probó y no funcionó", con variantes y su resultado público según el README: Random Forest 81,6; cocientes entre variables del mismo mes 85,1 a 92,6; ventana de aguinaldo ampliada 85,1; selección con canaritos 66,4; submuestreo sin cambio de etiqueta 93,3; y 95,2 para una receta sola frente a 96,6 combinando tres.
- `modelos/mejores_hiperparametros.json` · configuracion · JSON · 11 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicozare/modelos/mejores_hiperparametros.json.txt) — Hiperparámetros que lee 02_entrenar_ensamble.py: num_leaves 41, learning_rate 0,009613, min_data_in_leaf 380, feature_fraction 0,2555, bagging_fraction 0,5477, num_boost_round 690; incluye además ganancia_cv 1.193.298.333.
- `modelos/features.txt` · configuracion · Texto · 741 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicozare/modelos/features.txt.txt) — Lista de 741 nombres de variables, uno por línea, que 02_entrenar_ensamble.py escribe y 03_generar_submission.py lee: cobra_aguinaldo, 148 columnas numéricas del dataset y sus lag_1_, lag_2_, delta_1_ y delta_2_.
- `prediccion_final/README.md` · explicacion · Markdown · 22 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicozare/prediccion_final/README.md.txt) — Describe prediccion_final.csv (11.500 numero_de_cliente, sin encabezado), da su SHA-256 e indica que submissions/submission_promedio.csv, generado por 03_generar_submission.py, debe dar el mismo hash.
- `optimizacion_hiperparametros/buscar_hiperparametros.py` · principal · Python · 115 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicozare/optimizacion_hiperparametros/buscar_hiperparametros.py.txt) — Búsqueda de 5 hiperparámetros de LightGBM con Optuna (30 trials) sobre los meses con clase menos el último, con positivo = BAJA+2 y lgb.cv en 5 particiones aleatorias estratificadas. Según su docstring y el README, de esta búsqueda salen los valores de modelos/mejores_hiperparametros.json.
- `optimizacion_hiperparametros/README.md` · explicacion · Markdown · 52 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicozare/optimizacion_hiperparametros/README.md.txt) — Explica el contenido de la carpeta de búsqueda, el método (Optuna, 30 iteraciones, lgb.cv en 5 particiones con 30 % de prueba, métrica de ganancia), cómo consultar la base SQLite sin volver a correr y cómo repetir la búsqueda. Según este README, el trial número 26 (ganancia CV $1.193.298.333) coincide con modelos/mejores_hiperparametros.json.
- `scripts/01_feature_engineering.py` · principal · Python · 125 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicozare/scripts/01_feature_engineering.py.txt) — Lee el dataset crudo con DuckDB, calcula clase_ternaria, excluye 4 columnas, marca y ajusta el saldo en meses de aguinaldo, agrega lags y deltas de orden 1 y 2 y escribe data/dataset_features.csv.
- `scripts/config.py` · configuracion · Python · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicozare/scripts/config.py.txt) — Rutas relativas al repositorio y constantes del pipeline: semillas, función de ganancia, rango del corte, columnas excluidas, constantes de aguinaldo y de submuestreo.
- `scripts/03_generar_submission.py` · principal · Python · 63 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicozare/scripts/03_generar_submission.py.txt) — Carga los 15 modelos guardados, predice sobre el último mes del dataset y escribe 6 archivos con los clientes de mayor probabilidad: uno por semilla y uno con el promedio de las 5 semillas.
- `scripts/02_entrenar_ensamble.py` · principal · Python · 131 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicozare/scripts/02_entrenar_ensamble.py.txt) — Entrena el ensamble de LightGBM en dos corridas: una sin el mes de holdout, con la que mide la ganancia y elige el corte, y otra con todos los meses con clase, cuyos 15 modelos guarda en modelos/.
- `scripts/comun.py` · principal · Python · 40 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicozare/scripts/comun.py.txt) — Funciones que usan los scripts 02 y 03: determinación de los meses por posición, lectura de la lista de variables y submuestreo de los negativos.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### optimizacion_hiperparametros/buscar_hiperparametros.py

Búsqueda de 5 hiperparámetros de LightGBM con Optuna (30 trials) sobre los meses con clase menos el último, con positivo = BAJA+2 y lgb.cv en 5 particiones aleatorias estratificadas. Según su docstring y el README, de esta búsqueda salen los valores de modelos/mejores_hiperparametros.json.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–11] Docstring del módulo: indica que los valores de
#   modelos/mejores_hiperparametros.json salen de esta búsqueda ya corrida, que no se ejecuta al generar la
#   submission y que usa los meses con clase conocida menos el más reciente, StratifiedShuffleSplit de 5
#   particiones y 30 iteraciones de Optuna (TPE).
"""Búsqueda de hiperparámetros de LightGBM con Optuna.

Los valores que terminan en `modelos/mejores_hiperparametros.json` (los que
usa el pipeline de entrega) salen de esta búsqueda, ya corrida. No se vuelve
a correr automáticamente al generar la submission: este script es para
quien quiera reproducir la búsqueda desde cero o revisarla.

Entrena con todos los meses de clase conocida excepto el más reciente
(se lo reserva como medición), evaluando la ganancia real con
StratifiedShuffleSplit de 5 particiones. 30 iteraciones de Optuna (TPE).
"""
# [Anotación · líneas 12–34] Importa json, lightgbm, numpy, optuna, pandas y StratifiedShuffleSplit. Define la
#   ruta de data/dataset_features.csv, la semilla 100081, los valores de ganancia (1.072.500 y 27.500), el
#   umbral de probabilidad 27.500 / (27.500 + 1.072.500) = 0,025, las columnas que no son variables, 30 trials y
#   el nombre del estudio, lgbm_drift_aguinaldo.
from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

REPO_DIR = Path(__file__).resolve().parent.parent
DATASET_FE_CSV_PATH = REPO_DIR / "data" / "dataset_features.csv"

SEMILLA = 100081
GANANCIA_ACIERTO = 1_072_500
COSTO_ESTIMULO = 27_500
UMBRAL_ESTIMULO = COSTO_ESTIMULO / (COSTO_ESTIMULO + GANANCIA_ACIERTO)
COLUMNAS_NO_FEATURE = ["numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria"]

N_TRIALS = 30
STUDY_NAME = "lgbm_drift_aguinaldo"

# [Anotación · líneas 35–40] Versión propia de detectar_meses: devuelve los meses de entrenamiento (todos
#   menos los dos últimos) y el holdout (el último de ellos).

def detectar_meses(foto_mes_unicos: list[int]) -> tuple[list[int], int]:
    meses = sorted(foto_mes_unicos)
    meses_entrenamiento = meses[:-2] if len(meses) > 2 else meses[:-1]
    return meses_entrenamiento, meses_entrenamiento[-1]

# [Anotación · líneas 41–51] cargar_train lee el dataset de variables, crea clase_binaria con positivo =
#   BAJA+2 únicamente, se queda con los meses de entrenamiento menos el holdout y devuelve la matriz de
#   variables, la etiqueta y la lista de variables. No aplica submuestreo.

def cargar_train() -> tuple[pd.DataFrame, pd.Series, list[str]]:
    data = pd.read_csv(DATASET_FE_CSV_PATH, low_memory=False)
    data["clase_binaria"] = np.where(data["clase_ternaria"] == "BAJA+2", 1, 0)
    meses_entrenamiento, mes_holdout = detectar_meses(sorted(data["foto_mes"].unique()))
    meses_fit = [m for m in meses_entrenamiento if m != mes_holdout]
    train = data[data["foto_mes"].isin(meses_fit)]
    feats = [c for c in data.columns if c not in COLUMNAS_NO_FEATURE]
    print(f"Entrenando búsqueda sobre {meses_fit} ({len(train):,} filas, {len(feats)} features)", flush=True)
    return train[feats], train["clase_binaria"], feats

# [Anotación · líneas 52–57] ganancia_prob_lgm es la métrica propia para LightGBM: asigna 1.072.500 a los
#   positivos y −27.500 a los negativos, suma la ganancia de las filas con probabilidad mayor o igual a 0,025 y
#   la divide por prop = 0,3. Se declara como métrica a maximizar.

def ganancia_prob_lgm(y_pred, dataset, prop=0.3):
    y_true = dataset.get_label()
    ganancia = np.where(y_true == 1, GANANCIA_ACIERTO, 0) - np.where(y_true == 0, COSTO_ESTIMULO, 0)
    return "gan_prob", ganancia[y_pred >= UMBRAL_ESTIMULO].sum() / prop, True

# [Anotación · líneas 58–63] main carga los datos, arma el lgb.Dataset y define un StratifiedShuffleSplit de 5
#   particiones con 30 % de prueba y random_state 100081.

def main() -> None:
    X_train, y_train, feats = cargar_train()
    train_lgb = lgb.Dataset(X_train, label=y_train)
    sss = StratifiedShuffleSplit(n_splits=5, test_size=0.3, random_state=SEMILLA)

# [Anotación · líneas 64–84] objective define un trial: muestrea num_leaves entre 8 y 100, learning_rate entre
#   0,005 y 0,3, min_data_in_leaf entre 1 y 1000, y feature_fraction y bagging_fraction entre 0,1 y 1,0, con
#   max_bin 31 fijo. Corre lgb.cv sobre las 5 particiones con hasta 1000 rondas, early stopping de int(50 + 5 /
#   learning_rate) rondas y la métrica de ganancia. Devuelve el máximo de la ganancia media entre particiones y
#   guarda la ronda en que ocurre como atributo best_iter.
    def objective(trial: optuna.Trial) -> float:
        params = {
            "objective": "binary", "metric": "custom", "boosting_type": "gbdt",
            "first_metric_only": True, "boost_from_average": True, "feature_pre_filter": False,
            "max_bin": 31,
            "num_leaves": trial.suggest_int("num_leaves", 8, 100),
            "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.3),
            "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 1, 1000),
            "feature_fraction": trial.suggest_float("feature_fraction", 0.1, 1.0),
            "bagging_fraction": trial.suggest_float("bagging_fraction", 0.1, 1.0),
            "seed": SEMILLA, "verbose": -1,
        }
        cv_results = lgb.cv(
            params, train_lgb, num_boost_round=1000,
            callbacks=[lgb.early_stopping(stopping_rounds=int(50 + 5 / params["learning_rate"]), verbose=False)],
            feval=ganancia_prob_lgm, folds=sss.split(X_train, y_train), seed=SEMILLA,
        )
        max_gan = max(cv_results["valid gan_prob-mean"])
        trial.set_user_attr("best_iter", cv_results["valid gan_prob-mean"].index(max_gan) + 1)
        return max_gan

# [Anotación · líneas 85–91] Crea o reabre (load_if_exists=True) el estudio de Optuna con dirección maximize
#   en la base SQLite optimizacion_lgbm.db de la misma carpeta, sin indicar sampler, y corre 30 trials.
    study = optuna.create_study(
        direction="maximize", study_name=STUDY_NAME,
        storage=f"sqlite:///{Path(__file__).resolve().parent / 'optimizacion_lgbm.db'}",
        load_if_exists=True,
    )
    study.optimize(objective, n_trials=N_TRIALS)

# [Anotación · líneas 92–104] Toma del trial de mayor valor los 5 hiperparámetros y el atributo best_iter como
#   num_boost_round, e imprime la ganancia, los hiperparámetros y la cantidad de rondas.
    mejores = {
        "num_leaves": study.best_trial.params["num_leaves"],
        "learning_rate": study.best_trial.params["learning_rate"],
        "min_data_in_leaf": study.best_trial.params["min_data_in_leaf"],
        "feature_fraction": study.best_trial.params["feature_fraction"],
        "bagging_fraction": study.best_trial.params["bagging_fraction"],
    }
    num_boost_round = study.best_trial.user_attrs["best_iter"]

    print(f"\nMejor ganancia CV: {study.best_value:,.0f}", flush=True)
    print(f"Mejores hiperparámetros: {mejores}", flush=True)
    print(f"num_boost_round sugerido: {num_boost_round}", flush=True)

# [Anotación · líneas 105–115] Escribe optimizacion_hiperparametros/resultado_busqueda.json con las claves
#   hiperparametros, num_boost_round y ganancia_cv. Las dos últimas líneas ejecutan main() cuando el archivo se
#   corre como script.
    destino = Path(__file__).resolve().parent / "resultado_busqueda.json"
    destino.write_text(
        json.dumps({"hiperparametros": mejores, "num_boost_round": num_boost_round, "ganancia_cv": study.best_value},
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Guardado en {destino}", flush=True)


if __name__ == "__main__":
    main()
```

### scripts/01_feature_engineering.py

Lee el dataset crudo con DuckDB, calcula clase_ternaria, excluye 4 columnas, marca y ajusta el saldo en meses de aguinaldo, agrega lags y deltas de orden 1 y 2 y escribe data/dataset_features.csv.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Docstring del módulo: enumera los cuatro pasos del script (cálculo de
#   clase_ternaria, exclusión de las columnas de config.COLUMNAS_CON_DRIFT, marca y ajuste de aguinaldo sobre
#   mcuentas_saldo, y lags y deltas de orden 1 y 2).
"""Calcula la clase objetivo y arma el dataset de features a partir del
dataset crudo.

Pasos:
  1. clase_ternaria: para cada cliente y mes, mira si sigue existiendo 1 y 2
     meses después. CONTINUA si sigue en ambos, BAJA+1 si deja de existir al
     mes siguiente, BAJA+2 si existe un mes más pero no dos.
  2. Se excluyen columnas con un desplazamiento fuerte de distribución entre
     meses (ver config.COLUMNAS_CON_DRIFT) — no reflejan un cambio real del
     cliente, sino un cambio en cómo se generó el dato en algún mes puntual.
  3. Aguinaldo: en los meses de aguinaldo (junio y diciembre), si el saldo de
     cuentas de un cliente sube muy por encima de su propio promedio o
     máximo habitual (calculados con sus meses anteriores), se marca con la
     columna `cobra_aguinaldo` y se corrige ese saldo dividiéndolo por un
     factor fijo — queda reemplazado en la misma columna `mcuentas_saldo`.
  4. Lags y deltas de orden 1 y 2 (valor de 1 y 2 meses atrás, y la
     diferencia contra cada uno) sobre todas las columnas numéricas,
     incluida la de saldo ya corregida. `cobra_aguinaldo` queda como columna
     plana, sin lag ni delta.
"""
# [Anotación · líneas 21–36] Importa duckdb y, desde config.py, las rutas de entrada y salida, la lista de
#   columnas a excluir y las tres constantes de aguinaldo. Define NO_NUMERICAS con las tres columnas que no
#   reciben lag ni delta: numero_de_cliente, foto_mes y clase_ternaria.
from __future__ import annotations

import duckdb

from config import (
    COLUMNAS_CON_DRIFT,
    DATASET_FE_CSV_PATH,
    INFLACION_AGUINALDO,
    MESES_AGUINALDO,
    RAW_CSV_PATH,
    UMBRAL_AGUINALDO,
)

NO_NUMERICAS = ("numero_de_cliente", "foto_mes", "clase_ternaria")


# [Anotación · líneas 37–49] Abre una conexión DuckDB en memoria y carga data/dataset_crudo.csv en la tabla
#   crudo con read_csv_auto. Arma la lista numericas con las columnas que no están en NO_NUMERICAS ni en
#   COLUMNAS_CON_DRIFT y cuyo tipo es BIGINT, DOUBLE, INTEGER, FLOAT, HUGEINT, SMALLINT, TINYINT o DECIMAL, e
#   imprime cuántas son.
def main() -> None:
    con = duckdb.connect()
    con.execute(f"create or replace table crudo as select * from read_csv_auto('{RAW_CSV_PATH.as_posix()}')")

    cols = [r[0] for r in con.execute("describe crudo").fetchall()]
    tipos = {r[0]: r[1] for r in con.execute("describe crudo").fetchall()}
    numericas = [
        c for c in cols
        if c not in NO_NUMERICAS and c not in COLUMNAS_CON_DRIFT
        and tipos[c] in ("BIGINT", "DOUBLE", "INTEGER", "FLOAT", "HUGEINT", "SMALLINT", "TINYINT", "DECIMAL")
    ]
    print(f"columnas numéricas utilizadas: {len(numericas)} (excluidas por drift: {COLUMNAS_CON_DRIFT})", flush=True)

# [Anotación · líneas 50–65] Calcula clase_ternaria en la tabla base. Cruza todos los clientes con todos los
#   meses, marca con mes_0 = 1 los pares que existen en el dataset y mira esa marca uno y dos meses adelante:
#   BAJA+1 si el cliente no está al mes siguiente, BAJA+2 si está al mes siguiente pero no a los dos meses,
#   CONTINUA si está en ambos, y nulo cuando el dataset no tiene el mes siguiente o el segundo. Conserva sólo
#   las filas existentes (mes_0 = 1).
    # clase_ternaria
    con.execute("""
        create or replace table base as
        with periodos as (select distinct foto_mes from crudo),
        clientes as (select distinct numero_de_cliente from crudo),
        todo as (select numero_de_cliente, foto_mes from clientes cross join periodos),
        ct as (
            select c.*, if(c.numero_de_cliente is null, 0, 1) as mes_0,
            lead(mes_0, 1) over (partition by t.numero_de_cliente order by foto_mes) as mes_1,
            lead(mes_0, 2) over (partition by t.numero_de_cliente order by foto_mes) as mes_2,
            case when mes_1 is null then null when mes_1 = 0 then 'BAJA+1'
                 when mes_2 is null then null when mes_2 = 0 then 'BAJA+2' else 'CONTINUA' end as clase_ternaria
            from todo t left join crudo c using (numero_de_cliente, foto_mes)
        ) select * exclude (mes_0, mes_1, mes_2) from ct where mes_0 = 1
    """)

# [Anotación · líneas 66–83] Para cada cliente y cada mes de junio o diciembre (MESES_AGUINALDO = 6 y 12)
#   calcula el promedio y el máximo de mcuentas_saldo sobre todas las filas del mismo cliente con foto_mes
#   anterior (tabla ref_aguinaldo) y los agrega a base como columnas promedio y maximo con un left join; en los
#   demás meses quedan nulas.
    # aguinaldo: referencia por cliente = promedio/máximo de su saldo en los
    # meses ANTERIORES a cada mes de aguinaldo (nunca meses futuros)
    meses_aguinaldo_sql = ", ".join(str(m) for m in MESES_AGUINALDO)
    con.execute(f"""
        create or replace table ref_aguinaldo as
        select b.numero_de_cliente, b.foto_mes as mes_aguinaldo,
               avg(h.mcuentas_saldo) as promedio, max(h.mcuentas_saldo) as maximo
        from base b
        join base h on h.numero_de_cliente = b.numero_de_cliente and h.foto_mes < b.foto_mes
        where cast(b.foto_mes % 100 as int) in ({meses_aguinaldo_sql})
        group by b.numero_de_cliente, b.foto_mes
    """)
    con.execute("""
        create or replace table base as
        select b.*, r.promedio, r.maximo
        from base b left join ref_aguinaldo r
        on r.numero_de_cliente = b.numero_de_cliente and r.mes_aguinaldo = b.foto_mes
    """)
# [Anotación · líneas 84–96] Define la condición cumple: el mes es junio o diciembre y mcuentas_saldo es mayor
#   o igual a 1,4 (UMBRAL_AGUINALDO) veces el promedio o el máximo previos. Crea base_aguinaldo con la columna
#   cobra_aguinaldo (1 si cumple, 0 si no) y con mcuentas_saldo dividido por 1,111 (INFLACION_AGUINALDO) en las
#   filas que cumplen; quita promedio y maximo. Imprime la cantidad de filas marcadas.
    cumple = f"""cast(foto_mes % 100 as int) in ({meses_aguinaldo_sql}) and (
                    mcuentas_saldo >= {UMBRAL_AGUINALDO} * promedio
                    or mcuentas_saldo >= {UMBRAL_AGUINALDO} * maximo)"""
    con.execute(f"""
        create or replace table base_aguinaldo as
        select * exclude (mcuentas_saldo, promedio, maximo),
               if({cumple}, 1, 0) as cobra_aguinaldo,
               if({cumple}, mcuentas_saldo / {INFLACION_AGUINALDO}, mcuentas_saldo) as mcuentas_saldo
        from base
    """)
    n_cobra = con.execute("select count(*) from base_aguinaldo where cobra_aguinaldo = 1").fetchone()[0]
    print(f"filas marcadas con cobra_aguinaldo=1: {n_cobra:,}", flush=True)

# [Anotación · líneas 97–116] Para cada columna de numericas genera cuatro expresiones SQL: el valor de la
#   fila anterior y el de dos filas atrás del mismo cliente ordenado por foto_mes (lag_1_ y lag_2_) y la
#   diferencia del valor actual con cada uno (delta_1_ y delta_2_). Crea la tabla fe con numero_de_cliente,
#   foto_mes, clase_ternaria, cobra_aguinaldo, las columnas numéricas y las derivadas, ordenada por cliente y
#   mes.
    # cobra_aguinaldo queda como columna plana (sin lag/delta); mcuentas_saldo
    # ya tiene el ajuste aplicado y recibe lag/delta como cualquier otra
    # columna de `numericas`.
    partes = []
    for c in numericas:
        partes += [
            f"lag({c}, 1) over ventana as lag_1_{c}",
            f"lag({c}, 2) over ventana as lag_2_{c}",
            f"{c} - lag({c}, 1) over ventana as delta_1_{c}",
            f"{c} - lag({c}, 2) over ventana as delta_2_{c}",
        ]
    salida = ["numero_de_cliente", "foto_mes", "clase_ternaria", "cobra_aguinaldo"] + numericas
    con.execute(f"""
        create or replace table fe as
        select {', '.join(salida)}, {', '.join(partes)}
        from base_aguinaldo
        window ventana as (partition by numero_de_cliente order by foto_mes)
        order by numero_de_cliente, foto_mes
    """)

# [Anotación · líneas 117–125] Imprime la cantidad de columnas de fe, crea la carpeta data/ si no existe y
#   exporta la tabla a data/dataset_features.csv con encabezado. Las dos últimas líneas ejecutan main() cuando
#   el archivo se corre como script.
    n_cols = con.execute("select count(*) from (describe fe)").fetchone()[0]
    print(f"columnas totales: {n_cols}", flush=True)
    DATASET_FE_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"copy fe to '{DATASET_FE_CSV_PATH.as_posix()}' (format csv, header)")
    print(f"guardado en {DATASET_FE_CSV_PATH}", flush=True)


if __name__ == "__main__":
    main()
```

### scripts/03_generar_submission.py

Carga los 15 modelos guardados, predice sobre el último mes del dataset y escribe 6 archivos con los clientes de mayor probabilidad: uno por semilla y uno con el promedio de las 5 semillas.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–15] Docstring del módulo: indica que se predice sobre el mes más reciente del dataset
#   con los modelos ya guardados, que se promedian los 3 submodelos de cada semilla y luego las 5 semillas, que
#   no se descarta ningún cliente antes de ordenar y que la salida son 5 archivos por semilla más uno con el
#   promedio.
"""Genera los archivos de submission.

Predice con los modelos ya entrenados sobre el mes más reciente del dataset
(el único sin clase conocida, que es justamente el que hay que predecir).
Para cada semilla, promedia sus 3 submodelos; para cada cliente, se toma el
promedio de las 5 semillas como probabilidad final. Se seleccionan los
`corte_optimo` clientes con mayor probabilidad.

No se descarta ningún cliente antes de rankear: al predecir sobre el mes más
reciente, cualquier candidato ya existe en ese mes por definición.

Salida: un archivo por semilla (5 "modelos candidatos", según pide el
enunciado de la entrega) más un sexto archivo con el promedio de las 5 —
las probabilidades promediadas entre semillas, antes de rankear.
"""
# [Anotación · líneas 16–25] Importa numpy, pandas y lightgbm, las funciones cargar_features y detectar_meses
#   de comun.py y las rutas y constantes de config.py.
from __future__ import annotations

import numpy as np
import pandas as pd
import lightgbm as lgb

from comun import cargar_features, detectar_meses
from config import DATASET_FE_CSV_PATH, MODELS_DIR, SEMILLAS, SUBMISSIONS_DIR, SUBMODELOS_POR_SEMILLA


# [Anotación · líneas 26–34] Lee data/dataset_features.csv, obtiene con detectar_meses el mes de predicción
#   (el último del dataset) y se queda con sus filas. Lee la lista de variables de modelos/features.txt y arma
#   la matriz X con esas columnas.
def main() -> None:
    data = pd.read_csv(DATASET_FE_CSV_PATH, low_memory=False)
    _, _, mes_prediccion = detectar_meses(sorted(data["foto_mes"].unique()))
    mes = data[data["foto_mes"] == mes_prediccion]
    print(f"Prediciendo sobre foto_mes={mes_prediccion}: {len(mes):,} clientes", flush=True)

    feats = cargar_features(MODELS_DIR / "features.txt")
    X = mes[feats]

# [Anotación · líneas 35–42] Para cada una de las 5 semillas carga sus 3 modelos desde
#   modelos/lgb_seed_<semilla>_k<k>.txt y guarda el promedio de las tres predicciones sobre X.
    probs_por_semilla = {}
    for seed in SEMILLAS:
        submodelos = [
            lgb.Booster(model_file=str(MODELS_DIR / f"lgb_seed_{seed}_k{k}.txt"))
            for k in range(SUBMODELOS_POR_SEMILLA)
        ]
        probs_por_semilla[seed] = np.mean([m.predict(X) for m in submodelos], axis=0)

# [Anotación · líneas 43–53] Lee el corte de modelos/corte_optimo.txt. Para cada semilla ordena los clientes
#   por probabilidad descendente, toma los primeros corte y escribe sus numero_de_cliente como enteros, sin
#   índice ni encabezado, en submissions/submission_seed_<semilla>.csv.
    corte = int((MODELS_DIR / "corte_optimo.txt").read_text(encoding="utf-8").strip())
    print(f"Corte: {corte:,} clientes", flush=True)

    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    for seed in SEMILLAS:
        orden = np.argsort(probs_por_semilla[seed])[::-1][:corte]
        seleccionados = mes.iloc[orden]["numero_de_cliente"].astype("int64")
        destino = SUBMISSIONS_DIR / f"submission_seed_{seed}.csv"
        seleccionados.to_csv(destino, index=False, header=False)
        print(f"  semilla {seed}: {len(seleccionados):,} clientes -> {destino}", flush=True)

# [Anotación · líneas 54–63] Promedia las probabilidades de las 5 semillas, toma los corte clientes de mayor
#   promedio y los escribe en submissions/submission_promedio.csv con el mismo formato. Las dos últimas líneas
#   ejecutan main() cuando el archivo se corre como script.
    promedio = np.mean([probs_por_semilla[s] for s in SEMILLAS], axis=0)
    orden = np.argsort(promedio)[::-1][:corte]
    seleccionados = mes.iloc[orden]["numero_de_cliente"].astype("int64")
    destino = SUBMISSIONS_DIR / "submission_promedio.csv"
    seleccionados.to_csv(destino, index=False, header=False)
    print(f"  promedio de las 5 semillas: {len(seleccionados):,} clientes -> {destino}", flush=True)


if __name__ == "__main__":
    main()
```

### scripts/02_entrenar_ensamble.py

Entrena el ensamble de LightGBM en dos corridas: una sin el mes de holdout, con la que mide la ganancia y elige el corte, y otra con todos los meses con clase, cuyos 15 modelos guarda en modelos/.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Docstring del módulo: describe el esquema de 3 submodelos por semilla, las dos
#   corridas (control en holdout con elección del corte y modelo de entrega con todos los meses con clase), la
#   clase positiva (BAJA+1 o BAJA+2), el submuestreo al 50 % y el ajuste de min_data_in_leaf.
"""Entrena el ensamble de modelos LightGBM.

Por cada semilla se entrenan 3 submodelos (variando la semilla interna, que
cambia el submuestreo de filas y de columnas de cada árbol) y se promedian
sus probabilidades — reduce la varianza de un único modelo.

Dos corridas:
  1. Control de calidad: entrena sin el mes más reciente con clase conocida
     (se lo reserva como holdout) y mide la ganancia real ahí. Con esa
     medición se elige, dentro de RANGO_CORTE, la cantidad de clientes a
     estimular que da la mayor ganancia.
  2. Modelo de entrega: entrena con TODOS los meses de clase conocida y
     guarda un modelo por semilla y submodelo en modelos/.

En las dos corridas, la clase a predecir es "se da de baja dentro de los
próximos dos meses" (BAJA+1 o BAJA+2), y se submuestrea la clase mayoritaria
(clientes que continúan) al 50% en cada submodelo — todos los positivos se
conservan. Al entrenar con menos filas de la clase mayoritaria,
`min_data_in_leaf` se divide por esa misma proporción.
"""
# [Anotación · líneas 21–46] Importa json, lightgbm, numpy y pandas, las funciones detectar_meses y
#   submuestrear_continuas de comun.py y las constantes de config.py. Define COLUMNAS_NO_FEATURE:
#   numero_de_cliente, foto_mes, clase_ternaria y clase_binaria.
from __future__ import annotations

import json

import lightgbm as lgb
import numpy as np
import pandas as pd

from comun import detectar_meses, submuestrear_continuas
from config import (
    COSTO_ESTIMULO,
    DATASET_FE_CSV_PATH,
    GANANCIA_ACIERTO,
    MODELS_DIR,
    OUTPUT_DIR,
    PASO_BARRIDO_CORTE,
    RANGO_CORTE,
    SEMILLA_INTERNA_PASO,
    SEMILLAS,
    SUBMODELOS_POR_SEMILLA,
    SUBMUESTREO_CONTINUA,
)

COLUMNAS_NO_FEATURE = ["numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria"]


# [Anotación · líneas 47–54] cargar_hiperparametros lee modelos/mejores_hiperparametros.json y devuelve el
#   diccionario "hiperparametros" y el entero "num_boost_round". Se ejecuta al importar el módulo y deja los
#   valores en HIPERPARAMETROS y NUM_BOOST_ROUND.
def cargar_hiperparametros() -> tuple[dict, int]:
    datos = json.loads((MODELS_DIR / "mejores_hiperparametros.json").read_text(encoding="utf-8"))
    return datos["hiperparametros"], datos["num_boost_round"]


HIPERPARAMETROS, NUM_BOOST_ROUND = cargar_hiperparametros()


# [Anotación · líneas 55–63] armar_params arma el diccionario de parámetros de LightGBM: objective binary,
#   boosting_type gbdt, max_bin 31, boost_from_average True, feature_pre_filter False, first_metric_only False,
#   verbose -1, la semilla recibida y los hiperparámetros del JSON, con min_data_in_leaf reemplazado por
#   round(min_data_in_leaf / 0,5). El diccionario no incluye bagging_freq.
def armar_params(seed: int) -> dict:
    hiper = {**HIPERPARAMETROS, "min_data_in_leaf": round(HIPERPARAMETROS["min_data_in_leaf"] / SUBMUESTREO_CONTINUA)}
    return {
        "objective": "binary", "boosting_type": "gbdt", "first_metric_only": False,
        "boost_from_average": True, "feature_pre_filter": False, "max_bin": 31,
        "seed": seed, "verbose": -1, **hiper,
    }


# [Anotación · líneas 64–70] entrenar_submodelo calcula la semilla interna como semilla + k × 7919,
#   submuestrea el conjunto con esa semilla (todos los positivos y 50 % de los negativos), arma el lgb.Dataset
#   con clase_binaria como etiqueta y entrena NUM_BOOST_ROUND rondas con lgb.train, sin conjunto de validación
#   ni early stopping.
def entrenar_submodelo(df: pd.DataFrame, feats: list[str], seed: int, k: int) -> lgb.Booster:
    seed_interna = seed + k * SEMILLA_INTERNA_PASO
    muestra = submuestrear_continuas(df, seed_interna, SUBMUESTREO_CONTINUA)
    dataset = lgb.Dataset(muestra[feats], label=muestra["clase_binaria"])
    return lgb.train(armar_params(seed_interna), dataset, num_boost_round=NUM_BOOST_ROUND)


# [Anotación · líneas 71–80] predecir_ensamble devuelve el promedio de las predicciones de una lista de
#   modelos. ganancia_en_corte asigna 1.072.500 a cada fila con clase BAJA+2 y −27.500 a las demás, ordena por
#   probabilidad descendente y suma la ganancia de las primeras corte filas.
def predecir_ensamble(modelos: list[lgb.Booster], X: pd.DataFrame) -> np.ndarray:
    return np.mean([m.predict(X) for m in modelos], axis=0)


def ganancia_en_corte(y_pred: np.ndarray, clase: np.ndarray, corte: int) -> float:
    g = np.where(clase == "BAJA+2", GANANCIA_ACIERTO, -COSTO_ESTIMULO)
    orden = np.argsort(y_pred)[::-1][:corte]
    return float(g[orden].sum())


# [Anotación · líneas 81–96] elegir_corte_optimo recorre los cortes de 8.000 a 15.000 de a 250 (29 valores).
#   Para cada uno promedia la ganancia de las 5 semillas, guarda la tabla en output/ganancia_por_corte.csv, toma
#   el corte de mayor ganancia promedio, lo imprime y lo escribe en modelos/corte_optimo.txt.
def elegir_corte_optimo(preds_por_semilla: dict[int, np.ndarray], clase: np.ndarray) -> int:
    cortes = list(range(RANGO_CORTE[0], RANGO_CORTE[1] + 1, PASO_BARRIDO_CORTE))
    filas = [
        {"corte": c, "ganancia_promedio": np.mean([ganancia_en_corte(preds_por_semilla[s], clase, c) for s in SEMILLAS])}
        for c in cortes
    ]
    df = pd.DataFrame(filas)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_DIR / "ganancia_por_corte.csv", index=False)
    mejor = df.loc[df["ganancia_promedio"].idxmax()]
    corte = int(mejor["corte"])
    print(f"Corte óptimo dentro de {RANGO_CORTE}: {corte:,} (ganancia promedio ${mejor['ganancia_promedio']:,.0f})", flush=True)
    (MODELS_DIR / "corte_optimo.txt").write_text(str(corte), encoding="utf-8")
    return corte


# [Anotación · líneas 97–105] main lee data/dataset_features.csv, crea clase_binaria (1 si clase_ternaria es
#   BAJA+1 o BAJA+2, 0 en otro caso) y toma como variables todas las columnas salvo las de COLUMNAS_NO_FEATURE.
#   Con detectar_meses obtiene los meses de entrenamiento y el holdout (el último de ellos), y arma
#   meses_fit_holdout con los meses de entrenamiento menos el holdout.
def main() -> None:
    data = pd.read_csv(DATASET_FE_CSV_PATH, low_memory=False)
    data["clase_binaria"] = np.where(data["clase_ternaria"].isin(["BAJA+1", "BAJA+2"]), 1, 0)
    feats = [c for c in data.columns if c not in COLUMNAS_NO_FEATURE]
    print(f"{len(feats)} features", flush=True)

    meses_entrenamiento, mes_holdout, _ = detectar_meses(sorted(data["foto_mes"].unique()))
    meses_fit_holdout = [m for m in meses_entrenamiento if m != mes_holdout]

# [Anotación · líneas 106–117] Control en holdout: entrena con meses_fit_holdout y predice el mes de holdout.
#   Para cada una de las 5 semillas entrena 3 submodelos y promedia sus probabilidades; con las predicciones de
#   las 5 semillas y la clase_ternaria del holdout llama a elegir_corte_optimo.
    print(f"\n--- Control de calidad: entrena con {meses_fit_holdout}, mide en {mes_holdout} ---", flush=True)
    train = data[data["foto_mes"].isin(meses_fit_holdout)]
    valid = data[data["foto_mes"] == mes_holdout]
    clase_valid = valid["clase_ternaria"].to_numpy()

    preds_por_semilla = {}
    for seed in SEMILLAS:
        modelos = [entrenar_submodelo(train, feats, seed, k) for k in range(SUBMODELOS_POR_SEMILLA)]
        preds_por_semilla[seed] = predecir_ensamble(modelos, valid[feats])
        print(f"  semilla {seed} entrenada", flush=True)
    elegir_corte_optimo(preds_por_semilla, clase_valid)

# [Anotación · líneas 118–131] Modelo de entrega: toma todos los meses de entrenamiento (incluido el holdout),
#   escribe la lista de variables en modelos/features.txt y, para cada semilla y cada k de 0 a 2, entrena un
#   submodelo y lo guarda en modelos/lgb_seed_<semilla>_k<k>.txt (15 archivos). Las dos últimas líneas ejecutan
#   main() cuando el archivo se corre como script.
    print(f"\n--- Modelo de entrega: entrena con {meses_entrenamiento} ---", flush=True)
    train_final = data[data["foto_mes"].isin(meses_entrenamiento)]
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    (MODELS_DIR / "features.txt").write_text("\n".join(feats), encoding="utf-8")
    for seed in SEMILLAS:
        for k in range(SUBMODELOS_POR_SEMILLA):
            modelo = entrenar_submodelo(train_final, feats, seed, k)
            destino = MODELS_DIR / f"lgb_seed_{seed}_k{k}.txt"
            modelo.save_model(str(destino))
        print(f"  semilla {seed}: {SUBMODELOS_POR_SEMILLA} submodelos guardados", flush=True)


if __name__ == "__main__":
    main()
```

### scripts/comun.py

Funciones que usan los scripts 02 y 03: determinación de los meses por posición, lectura de la lista de variables y submuestreo de los negativos.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–6] Docstring del módulo e importación de pandas.
"""Funciones compartidas por los tres scripts del pipeline."""
from __future__ import annotations

import pandas as pd


# [Anotación · líneas 7–26] detectar_meses ordena los meses presentes y devuelve tres valores por posición:
#   los meses de entrenamiento (todos menos los dos últimos, o todos menos el último si hay dos meses o menos),
#   el holdout (el último mes de entrenamiento) y el mes de predicción (el último del dataset).
def detectar_meses(foto_mes_unicos: list[int]) -> tuple[list[int], int, int]:
    """A partir de los meses presentes en el dataset, determina:
      - meses_entrenamiento: los que tienen clase_ternaria completa (todo
        cliente tiene al menos 2 meses de datos posteriores para saber si
        se da de baja).
      - mes_holdout: el último de esos meses, se usa como control de
        calidad (se excluye de un segundo entrenamiento para medir la
        ganancia real antes de confiar en el modelo).
      - mes_prediccion: el mes más reciente del dataset (no tiene
        clase_ternaria conocida — es el que hay que predecir).

    Un mes tiene clase_ternaria completa si hay al menos dos meses más
    después de él en el dataset.
    """
    meses = sorted(foto_mes_unicos)
    mes_prediccion = meses[-1]
    meses_entrenamiento = meses[:-2] if len(meses) > 2 else meses[:-1]
    mes_holdout = meses_entrenamiento[-1]
    return meses_entrenamiento, mes_holdout, mes_prediccion

# [Anotación · líneas 27–30] cargar_features lee un archivo de texto y devuelve la lista de sus líneas no
#   vacías, sin espacios en los extremos.

def cargar_features(ruta) -> list[str]:
    return [c.strip() for c in ruta.read_text(encoding="utf-8").splitlines() if c.strip()]

# [Anotación · líneas 31–40] submuestrear_continuas genera un número al azar entre 0 y 1 por fila con
#   numpy.random.default_rng(seed) y conserva las filas con clase_binaria = 1 y las filas cuyo número al azar es
#   menor o igual a proporcion.

def submuestrear_continuas(df: pd.DataFrame, seed: int, proporcion: float) -> pd.DataFrame:
    """Conserva todos los positivos (clase_binaria=1) y una fracción al azar
    de los negativos (clase_binaria=0)."""
    import numpy as np

    rng = np.random.default_rng(seed)
    azar = rng.random(len(df))
    mantener = (df["clase_binaria"] == 1) | (azar <= proporcion)
    return df[mantener]
```


## Explicaciones del alumno (texto original)

### README.md

> # Predicción de baja de clientes - Paquete Premium
>
> Pipeline que, a partir del dataset crudo de clientes, predice qué clientes
> van a dar de baja el "Paquete Premium" en los próximos dos meses, y genera
> los archivos de submission (listas de clientes a los que conviene ofrecerles
> una acción de retención).
>
> ## Qué hace cada paso
>
> ```
> ┌──────────────────────┐
> │ dataset_crudo.csv     │   un archivo mensual (foto_mes) por cliente,
> │ (uno pone el suyo en  │   con ~150 variables: saldos, consumos,
> │  data/)                │   tarjetas, préstamos, antigüedad, etc.
> └───────────┬───────────┘
>             │
>             ▼
> ┌──────────────────────────────┐
> │ 01_feature_engineering.py     │  calcula la clase a predecir y arma
> │                                │  todas las columnas de entrada
> └───────────┬───────────────────┘
>             ▼
> ┌──────────────────────────────┐
> │ data/dataset_features.csv     │  un cliente-mes por fila, ~740 columnas
> └───────────┬───────────────────┘
>             ▼
> ┌──────────────────────────────┐
> │ 02_entrenar_ensamble.py       │  entrena los modelos (opcional: ya vienen
> │                                │  entrenados en modelos/, ver más abajo)
> └───────────┬───────────────────┘
>             ▼
> ┌──────────────────────────────┐
> │ modelos/*.txt, corte_optimo   │
> └───────────┬───────────────────┘
>             ▼
> ┌──────────────────────────────┐
> │ 03_generar_submission.py      │  predice sobre el mes más reciente y
> │                                │  arma los archivos finales
> └───────────┬───────────────────┘
>             ▼
> ┌──────────────────────────────┐
> │ submissions/*.csv             │  6 archivos: uno por semilla + 1 promedio
> └──────────────────────────────┘
> ```
>
> ## Cómo correrlo
>
> ```bash
> # 1. Poner el dataset crudo en data/dataset_crudo.csv (no viene incluido en el repo)
> uv sync
>
> uv run python scripts/01_feature_engineering.py
> uv run python scripts/02_entrenar_ensamble.py   # opcional, ver abajo
> uv run python scripts/03_generar_submission.py
> ```
>
> ### Sobre `modelos/`
>
> El repo ya incluye los modelos entrenados (15 archivos `lgb_seed_*.txt`, los
> hiperparámetros y el corte óptimo) correspondientes al mejor resultado
> obtenido hasta ahora. Esto permite correr directamente el paso 3
> (`03_generar_submission.py`) sobre un `dataset_features.csv` recién generado
> con el paso 1, sin tener que entrenar de nuevo.
>
> Correr `02_entrenar_ensamble.py` es opcional: vuelve a entrenar los modelos
> desde cero con la misma configuración (mismos hiperparámetros, mismo
> criterio de corte) y **sobrescribe** los archivos de `modelos/`. Sirve para
> verificar que el pipeline es reproducible, o para reentrenar si se usa un
> dataset distinto (por ejemplo, con meses más recientes).
>
> ## El problema que se resuelve
>
> Un cliente es `BAJA+2` si dentro de dos meses deja de tener el Paquete
> Premium. La tarea es identificar, con los datos de HOY, a esos clientes para
> poder ofrecerles una acción de retención a tiempo. A los que se dan de baja
> el próximo mes (`BAJA+1`) ya se llega tarde.
>
> Cada acierto (ofrecerle la acción a alguien que efectivamente se iba a dar de
> baja) vale mucho más que el costo de ofrecérsela a alguien que de todos modos
> iba a continuar, así que el modelo se evalúa con una métrica de ganancia de
> negocio, no con accuracy ni AUC.
>
> ## `01_feature_engineering.py`: columnas que arma
>
> | Técnica | Qué hace |
> |---|---|
> | **Clase objetivo (`clase_ternaria`)** | Para cada cliente y mes, mira si sigue existiendo 1 y 2 meses después. `CONTINUA` si sigue en los dos, `BAJA+1` si deja de existir al mes siguiente, `BAJA+2` si existe uno más pero no dos. |
> | **Exclusión de columnas con drift** | 4 columnas (`Master_fultimo_cierre`, `Visa_fultimo_cierre`, `Master_Finiciomora`, `Visa_Finiciomora`) cambian de distribución de un mes a otro de forma brusca y no económica (ver detalle abajo). Se descartan por completo, ni crudas ni derivadas. |
> | **`cobra_aguinaldo`** (columna nueva) | 1 si, en un mes de aguinaldo (junio o diciembre), el saldo del cliente sube a 1,4x o más de su propio promedio o máximo habitual (calculado con sus meses anteriores). Es una marca de "este mes el saldo está inflado por el aguinaldo, no por ahorro genuino". |
> | **Corrección de `mcuentas_saldo`** | En las filas marcadas con `cobra_aguinaldo=1`, el saldo se divide por 1,111 (un ajuste fijo) antes de seguir usándolo. Evita que el modelo confunda "cobró el aguinaldo este mes" con "mejoró su situación económica". |
> | **Lags y deltas, orden 1 y 2** | Para cada columna numérica (incluida `mcuentas_saldo` ya corregida), se agregan 4 columnas: `lag_1_X` y `lag_2_X` (el valor de esa variable 1 y 2 meses atrás) y `delta_1_X` y `delta_2_X` (la diferencia contra esos valores). Le da al modelo la tendencia de cada cliente, no solo su foto del mes actual. |
>
> **Por qué se excluyen esas 4 columnas por drift**: se mide con PSI
> (*Population Stability Index*, un indicador estándar para detectar cuándo la
> distribución de una variable cambió demasiado entre dos períodos). Dos de
> ellas (`Master_fultimo_cierre`, `Visa_fultimo_cierre`) pasan a tener ~77% de
> ceros de golpe en un solo mes: un cambio en cómo se generó el dato, no un
> cambio real de comportamiento de los clientes. Las otras dos
> (`Master_Finiciomora`, `Visa_Finiciomora`) tienen más del 98% de valores
> faltantes en todo el dataset.
>
> ## `02_entrenar_ensamble.py`: cómo se entrena
>
> | Técnica | Qué hace |
> |---|---|
> | **LightGBM** | Modelo de árboles de gradient boosting, el estándar para este tipo de datos tabulares. |
> | **Clase a predecir** | `BAJA+1` **o** `BAJA+2` cuentan como positivo (no solo `BAJA+2`). Los clientes que se van el próximo mes se comportan de forma parecida a los que se van en dos meses, así que sumarlos da más ejemplos positivos para aprender el patrón. |
> | **Submuestreo de la clase mayoritaria** | Los clientes que continúan son muchísimo más numerosos que los que se dan de baja. Cada submodelo entrena con todos los positivos pero solo un 50% al azar de los que continúan: balancea el entrenamiento y lo acelera. `min_data_in_leaf` se ajusta (se divide por ese mismo 0,5) para compensar que hay menos filas. |
> | **Ensamble de 5 semillas × 3 submodelos** | Por cada una de las 5 semillas, se entrenan 3 submodelos (cambiando una semilla interna, que varía qué filas y qué columnas ve cada árbol) y se promedian sus probabilidades. Reduce la varianza de confiar en un solo entrenamiento. |
> | **Control de calidad (holdout)** | Antes de entrenar el modelo final, se entrena una versión que deja afuera el mes más reciente con clase conocida, y se mide la ganancia real ahí, para confirmar que el modelo generaliza antes de usarlo. |
> | **Elección del corte** | Con esa medición, se recorre la cantidad de clientes a estimular (entre 8.000 y 15.000, de a pasos de 250) y se elige la que da mayor ganancia promedio entre las 5 semillas. |
> | **Modelo de entrega** | Se reentrena con el mismo procedimiento pero usando todos los meses con clase conocida (incluido el que se usó de holdout), para aprovechar el máximo de información disponible. |
>
> Los hiperparámetros de LightGBM (`num_leaves`, `learning_rate`,
> `min_data_in_leaf`, `feature_fraction`, `bagging_fraction` y la cantidad de
> árboles) ya vienen elegidos en `modelos/mejores_hiperparametros.json`. No se
> buscan de nuevo en este script. La búsqueda que originó esos valores está
> en `optimizacion_hiperparametros/`, con su propio README.
>
> ## `03_generar_submission.py`: cómo se arma la entrega
>
> Predice sobre el mes más reciente del dataset, el único sin clase conocida.
> Para cada semilla se promedian sus 3 submodelos; se toman los
> `corte_optimo` clientes con mayor probabilidad y se guardan en un CSV (sin
> encabezado, un `numero_de_cliente` por línea). Además se genera un sexto
> archivo que promedia la probabilidad de las 5 semillas antes de rankear.
>
> ## Sensibilidad del corte
>
> El corte se elige recorriendo la cantidad de clientes a estimular entre
> 8.000 y 15.000 (de a pasos de 250) y midiendo la ganancia real en el
> holdout. La curva es bastante plana alrededor del óptimo: entre 10.750 y
> 12.000 la diferencia es menor al 1%.
>
> | Clientes | Ganancia (holdout) |
> |---|---|
> | 8.000 | $368M |
> | 9.500 | $379M |
> | 10.750 | $391M |
> | **11.500** | **$392M (máximo)** |
> | 12.750 | $389M |
> | 14.000 | $382M |
> | 15.000 | $381M |
>
> ## Qué se probó y no funcionó
>
> Antes de llegar a esta receta se probaron variantes de feature engineering
> y de algoritmo que no mejoraron (o empeoraron) el resultado público. Se
> deja documentado para no repetirlas:
>
> | Variante probada | Resultado público | Contra la receta actual |
> |---|---|---|
> | Random Forest en vez de LightGBM, mismas columnas | 81,6 | peor |
> | Agregar columnas de ratios entre variables del mismo mes (uso de límite de tarjeta, carga de préstamos sobre ingreso, etc.) | 85,1 a 92,6 según la base | peor en los dos casos probados |
> | Ampliar la ventana de referencia del aguinaldo a más meses | 85,1 (combinado con los ratios de arriba) | peor |
> | Selección de columnas por importancia contra variables aleatorias ("canaritos") | 66,4 | mucho peor |
> | Submuestreo de la clase mayoritaria SIN el cambio de etiqueta (BAJA+1 y BAJA+2 positivos) | 93,3 | parecido, sin mejora clara |
>
> Lo que sí mejoró, y es lo que incorpora la receta actual: tratar `BAJA+1` y
> `BAJA+2` como positivos juntos, submuestrear la clase mayoritaria, y
> descartar las columnas con drift detectado por PSI. Combinar probabilidades
> de varias recetas de feature engineering distintas también sumó (95,2 de
> una receta sola contra 96,6 combinando tres), aunque menos que el cambio de
> etiqueta y submuestreo.
>
> ## Estructura del repo
>
> ```
> competencia_01/
> ├── data/                        dataset_crudo.csv (lo pone el usuario) y
> │                                dataset_features.csv (lo genera el paso 1)
> ├── modelos/                     hiperparámetros, corte óptimo y los 15
> │                                modelos ya entrenados (5 semillas × 3)
> ├── optimizacion_hiperparametros/  búsqueda que originó esos hiperparámetros
> │                                (base de Optuna + script), con su README
> ├── prediccion_final/            el CSV que se entregó y su hash SHA-256
> ├── scripts/
> │   ├── config.py                rutas y constantes
> │   ├── comun.py                  funciones compartidas
> │   ├── 01_feature_engineering.py
> │   ├── 02_entrenar_ensamble.py
> │   └── 03_generar_submission.py
> └── submissions/                  salida de 03_generar_submission.py
> ```

### prediccion_final/README.md

> # Archivo final
>
> `prediccion_final.csv`: 11.500 `numero_de_cliente`, sin encabezado, uno por
> línea. Es la lista de clientes a los que conviene ofrecerles una acción de
> retención.
>
> SHA-256:
>
> ```
> 6c3229728b7fb353dd46338d39d277d88e9b95c67247a70b2450e4dd8d48225a
> ```
>
> Al correr `scripts/03_generar_submission.py` (ver el README de la raíz), el
> archivo `submissions/submission_promedio.csv` que genera debe dar este mismo
> hash:
>
> ```bash
> shasum -a 256 submissions/submission_promedio.csv
> ```
>
> Si da un hash distinto, algo cambió respecto a la corrida original (otra
> versión del dataset crudo, otra versión de LightGBM, etc.).

### optimizacion_hiperparametros/README.md

> # Optimización de hiperparámetros
>
> Los valores de `modelos/mejores_hiperparametros.json` (los que usa
> `scripts/02_entrenar_ensamble.py` del pipeline de entrega) no se buscan
> dentro del pipeline final: salen de esta búsqueda, ya corrida de antemano.
> Esta carpeta documenta esa búsqueda para que se pueda revisar o repetir.
>
> ## Contenido
>
> - `optimizacion_lgbm.db`: base de datos SQLite de Optuna con los 30 trials
>   ya completados (estudio `lgbm_drift_aguinaldo`).
> - `buscar_hiperparametros.py`: el script que generó esos 30 trials.
> - `resultado_busqueda.json`: se genera al correr el script (no viene
>   incluido; ver más abajo cómo verificarlo sin correrlo).
>
> ## Método
>
> Optuna (TPE), 30 iteraciones, sobre 5 hiperparámetros de LightGBM
> (`num_leaves`, `learning_rate`, `min_data_in_leaf`, `feature_fraction`,
> `bagging_fraction`). Cada trial se mide con `lgb.cv` en 5 particiones
> (`StratifiedShuffleSplit`, 30% de test), entrenando con todos los meses de
> clase conocida excepto el más reciente (ese se reserva para la medición
> real del pipeline principal, nunca se usa acá). La métrica de cada trial es
> la ganancia real del negocio sobre las probabilidades que superan el umbral
> de equilibrio económico, no AUC ni logloss.
>
> ## Cómo verificar el resultado sin volver a correr la búsqueda
>
> ```bash
> uv run --with optuna python -c "
> import optuna
> st = optuna.load_study(study_name='lgbm_drift_aguinaldo', storage='sqlite:///optimizacion_lgbm.db')
> print(st.best_trial.number, st.best_value, st.best_trial.params, st.best_trial.user_attrs)
> "
> ```
>
> El mejor trial (número 26, ganancia CV $1.193.298.333) coincide exactamente
> con los valores de `../modelos/mejores_hiperparametros.json`.
>
> ## Cómo reproducir la búsqueda desde cero
>
> Requiere haber corrido antes `scripts/01_feature_engineering.py` (necesita
> `data/dataset_features.csv`).
>
> ```bash
> uv run --with duckdb --with lightgbm --with numpy --with optuna --with pandas --with scikit-learn python buscar_hiperparametros.py
> ```
>
> Como usa `load_if_exists=True` sobre la misma base, si se corre de nuevo
> sigue agregando trials al mismo estudio en vez de empezar otro. Para una
> búsqueda completamente nueva, borrar o renombrar `optimizacion_lgbm.db`
> antes de correrlo.

