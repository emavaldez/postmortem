# tomasfarias-hub — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: tomasfarias-hub
- Repositorio: https://github.com/tomasfarias-hub/DMEYF
- Link posteado: https://github.com/tomasfarias-hub/DMEYF/tree/main
- Commit: c1ef1a961209e7d70feafcfb551c36770fe00e07
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/tomasfarias-hub/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/tomasfarias-hub.json

## Resumen

La entrega es un repositorio con una notebook de Python para Google Colab (archivo notebook), un README y cuatro archivos de texto (reproducibilidad, resultados, dataset y Requirements). La notebook lee competencia_01.csv desde Google Drive, agrega la suma de los consumos de Visa y Master (tc_consumo_total) y, para 17 variables, la diferencia con la fila anterior del mismo cliente (delta_1), y arma una clase binaria con positivo = BAJA+2. Define una búsqueda de hiperparámetros con Optuna sobre 202103 y 202104, que queda desactivada por el interruptor USAR_PARAMS_FIJOS = True: se entrena con cinco hiperparámetros y 418 rondas escritos en el código. Con un LightGBM entrenado en 202103-202104 mide la ganancia en 202106, analiza las hojas de los árboles y calcula la curva de ganancia acumulada. Para la entrega promedia 5 modelos con semillas distintas: entrenados en 202103-202104 predicen 202106, donde se toma el máximo de la curva de ganancia suavizada (media móvil de 500) como proporción de la cartera; entrenados en 202103-202106 con max_bin = 255 predicen 202108, y se escribe un CSV con esa misma proporción de clientes de mayor probabilidad. Según el README, la entrega tiene 11.972 clientes.

**Qué entrega.** Un CSV sin encabezado con un numero_de_cliente por línea: los clientes de 202108 de mayor probabilidad promedio. El nombre se arma como entrega_<mes>_<método>_<cantidad>.csv. Según el README, el archivo de la entrega es entrega_202108_optimo_11972.csv, con 11.972 clientes (7,27 % de los 164.647 de agosto). El archivo no está en el repositorio.

**Cómo se ejecuta.** Según el README y el archivo reproducibilidad: subir la carpeta a Google Drive, colocar el dataset en data/competencia_01.csv, abrir la notebook en Google Colab, cambiar base_path en la segunda celda por la ruta de esa carpeta en el Drive propio (terminada en /) y ejecutar todas las celdas en orden. Con USAR_PARAMS_FIJOS = True no se ejecuta la optimización con Optuna.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: clase_binaria = 1 si clase_ternaria es BAJA+2 y 0 en los demás casos (BAJA+1 y CONTINUA).
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código.
- **Calidad de datos:** No se observa en el código un tratamiento de variables por mes. Al sumar Visa_mconsumototal y Master_mconsumototal los valores vacíos se reemplazan por 0.
- **Drifting:** No se observa en el código.
- **Variables dentro del mes:** Una variable: tc_consumo_total = Visa_mconsumototal + Master_mconsumototal, con los vacíos en 0.
- **Variables históricas:** Delta de orden 1 para 17 variables (lista CAMPOS_DELTA): valor de la fila menos el valor de la fila anterior del mismo cliente, con el dataset ordenado por numero_de_cliente y foto_mes (shift(1) dentro del grupo por cliente). Las columnas se llaman delta_1_<variable> y se guardan como float32.
- **Selección de variables:** No se observa en el código. Se usan todas las columnas salvo clase_ternaria, clase_binaria, numero_de_cliente y foto_mes. La importancia de variables se calcula y se muestra, sin usarse para filtrar.
- **Optimización de hiperparámetros:** La notebook define un estudio de Optuna (exp_301_lgbm_sss, guardado en SQLite) que busca num_leaves (8 a 100), learning_rate (0,005 a 0,3), min_data_in_leaf (1 a 1000), feature_fraction (0,1 a 1,0) y bagging_fraction (0,1 a 1,0) con lgb.cv sobre 202103 y 202104: 5 particiones StratifiedShuffleSplit con 30 % de validación, hasta 1000 rondas, parada temprana de 50 + 5/learning_rate rondas y, como métrica, la ganancia de las filas con probabilidad ≥ 0,025 dividida por 0,3. Con USAR_PARAMS_FIJOS = True la llamada study.optimize(objective, n_trials=15) no se ejecuta y se usan los valores escritos en PARAMS_OPTIMOS y BEST_ITER. Según el README, esos valores son los del trial de mayor ganancia de la corrida de la entrega.
- **Hiperparámetros finales:** objective = binary, boosting_type = gbdt, num_leaves = 19, learning_rate = 0.021127696716538504, min_data_in_leaf = 858, feature_fraction = 0.8257277981830174, bagging_fraction = 0.2302571235653956, boost_from_average = True, feature_pre_filter = False, first_metric_only = True, 418 rondas. max_bin = 255 en el modelo final y 31 en los modelos de validación. El diccionario de parámetros no incluye bagging_freq.
- **Semillas:** semilla = 2323 se pasa a np.random.seed y con np.random.choice(1000000, size=50, replace=False) se genera una lista de 50 semillas. El semillerío usa las primeras 5 (N_SEMILLAS = 5); semillas[0] se usa en el modelo individual, en StratifiedShuffleSplit y en lgb.cv. optuna.create_study se llama sin sampler ni semilla.
- **Cantidad de semillas:** 5
- **Ensamble:** Promedio de las probabilidades de 5 modelos LightGBM con los mismos hiperparámetros y distinta semilla (función entrenar_promedio).
- **Corte:** Con metodo = "optimo": el semillerío entrenado con 202103-202104 predice 202106; se ordena por probabilidad, se calcula la ganancia acumulada, se suaviza con una media móvil centrada de 500 posiciones y se toma la posición del máximo. Esa cantidad dividida por las filas de 202106 da una proporción (prop_opt), que se multiplica por las filas de 202108 para obtener la cantidad de envíos. Según el README: 11.933 envíos en 202106 (7,27 %) y 11.972 en 202108. El código tiene además las opciones "umbral" (probabilidad ≥ 0,025) y "cantidad" (primeros 8000), que no se ejecutan con el valor de metodo escrito.
- **Validación:** Un modelo entrenado con 202103 y 202104 se evalúa en 202106: ganancia de los clientes con probabilidad ≥ 0,025 y curva de ganancia acumulada según la cantidad de envíos. El semillerío de 5 modelos entrenado con los mismos meses se evalúa también en 202106. Dentro de la función objetivo de Optuna, lgb.cv usa 5 particiones aleatorias estratificadas con 30 % de validación sobre 202103-202104. Según el README, en 202106: 341,82 M con un modelo y umbral 0,025; 350,40 M en el máximo de la curva con un modelo; 356,04 M con el semillerío y la curva suavizada.
- **Salidas:** Un CSV sin encabezado ni índice con la columna numero_de_cliente, de nombre entrega_<mes_futuro>_<metodo>_<cantidad>.csv, escrito en la carpeta modelos/ de Google Drive y en /content/, y descargado con google.colab.files.download. La base SQLite de Optuna se ubica en db/optimization_lgbm.db. La notebook muestra además una tabla de importancia de variables y salidas sobre las hojas de los árboles y la ganancia acumulada.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optuna (`hiperparametros.optuna`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)
- Validación cruzada (`validacion.validacion_cruzada`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Técnicas sólo exploradas

- Corta por umbral de probabilidad (`corte.umbral_probabilidad`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: sí
- Entorno declarado: Google Colab: la notebook monta Google Drive y usa google.colab.files; la primera celda instala Optuna con pip. El archivo Requirements lista 9 paquetes sin versión (numpy, pandas, scipy, scikit-learn, matplotlib, plotly, lightgbm, optuna, jupyter). El archivo reproducibilidad tiene una sección Versiones con los campos de lightgbm, optuna, pandas, numpy y scikit-learn sin completar. No se declara máquina ni versión de Python.

## Pasos del camino de la entrega

1. **Instalación e importación de librerías.** Instala Optuna con pip e importa pandas, numpy, matplotlib, plotly, gaussian_kde y ks_2samp de scipy, StratifiedShuffleSplit de scikit-learn, lightgbm y optuna con sus funciones de visualización. (`notebook` líneas 1–23)
2. **Configuración, semillas y lectura del dataset.** Monta Google Drive, define las rutas data/, modelos/ y db/ bajo base_path, las constantes ganancia_acierto = 1.072.500 y costo_estimulo = 27.500, los meses (mes_train = 202103 y 202104, mes_test = 202106, mes_final_train = 202103 a 202106, mes_futuro = 202108) y genera 50 semillas a partir de semilla = 2323. Lee competencia_01.csv con pandas. (`notebook` líneas 25–54)
3. **Variables nuevas: consumo total de tarjetas y deltas.** Ordena por cliente y mes, crea tc_consumo_total como suma de Visa_mconsumototal y Master_mconsumototal (vacíos en 0) y calcula delta_1 para las 17 variables de CAMPOS_DELTA como el valor de la fila menos el de la fila anterior del mismo cliente. Imprime, por mes, la fracción de filas con delta_1_mpayroll calculado. (`notebook` líneas 59–86)
4. **Clase binaria.** Crea clase_binaria con valor 1 cuando clase_ternaria es BAJA+2 y 0 en los demás casos. (`notebook` líneas 91–94)
5. **Conjuntos de entrenamiento y prueba.** Separa las filas de 202103 y 202104 (entrenamiento) y las de 202106 (prueba), quita clase_ternaria, clase_binaria, numero_de_cliente y foto_mes de las variables predictoras y arma los lgb.Dataset. (`notebook` líneas 96–110)
6. **Definición de la optimización con Optuna.** Define las 5 particiones StratifiedShuffleSplit (30 % de validación), la métrica de ganancia con umbral 0,025 dividida por 0,3, la función objetivo que corre lgb.cv con cinco hiperparámetros propuestos por Optuna, y crea o reabre el estudio exp_301_lgbm_sss en una base SQLite. (`notebook` líneas 112–180)
7. **Interruptor de hiperparámetros fijos.** Con USAR_PARAMS_FIJOS = True se usan los valores de PARAMS_OPTIMOS (num_leaves 19, learning_rate 0,0211, min_data_in_leaf 858, feature_fraction 0,8257, bagging_fraction 0,2303) y BEST_ITER = 418; study.optimize con 15 trials sólo se ejecuta si el interruptor está en False. (`notebook` líneas 182–199)
8. **Entrenamiento de un modelo con 202103 y 202104.** Toma los hiperparámetros según el interruptor, arma el diccionario params (objective binary, max_bin 31, seed = semillas[0]) y entrena un LightGBM con 418 rondas sobre 202103 y 202104. (`notebook` líneas 201–243)
9. **Importancia de variables, predicción y ganancia en 202106.** Muestra las variables con importancia mayor que cero, predice 202106 y calcula la ganancia de los clientes con probabilidad ≥ 0,025. (`notebook` líneas 245–269)
10. **Análisis de las hojas de los árboles.** Para cada árbol y cada hoja cuenta las filas de entrenamiento por clase, calcula la ganancia de la hoja, el valor de la hoja convertido a probabilidad, la proporción de BAJA+2 y la probabilidad final media del modelo, y grafica la comparación. (`notebook` líneas 271–402)
11. **Curva de ganancia acumulada en 202106 con un modelo.** Ordena 202106 por probabilidad, calcula la ganancia acumulada, ubica la cantidad de envíos del máximo y la del umbral 0,025, arma una tabla para 12 cortes entre 500 y 30.000 envíos, grafica la curva e imprime el corte del máximo trasladado a 202108 como cantidad de envíos (en proporción al tamaño de la cartera). (`notebook` líneas 404–459)
12. **Parámetros de la entrega y función de semillerío.** Fija metodo = "optimo", umbral = 0,025, n_envios_manual = 8000, N_SEMILLAS = 5 y VENTANA = 500, y define entrenar_promedio, que entrena un modelo por semilla y promedia las probabilidades. (`notebook` líneas 464–496)
13. **Semillerío de validación y cálculo del corte.** Entrena 5 modelos con 202103 y 202104 (max_bin 31), promedia sus probabilidades sobre 202106, calcula la ganancia acumulada, la suaviza con una media móvil centrada de 500 y guarda la posición del máximo como proporción de las filas de 202106 (prop_opt). (`notebook` líneas 498–523)
14. **Modelo final y predicción de 202108.** Entrena 5 modelos con 202103 a 202106 y max_bin 255, promedia sus probabilidades sobre 202108 y ordena los clientes de mayor a menor. (`notebook` líneas 525–530)
15. **Selección de clientes y controles.** Con metodo = "optimo" toma los primeros round(prop_opt × filas de 202108) clientes. Verifica con assert que no haya clientes repetidos y que todos pertenezcan a 202108. (`notebook` líneas 532–545)
16. **Escritura y descarga del archivo.** Escribe el CSV sin encabezado ni índice en modelos/ de Drive y en /content/, imprime la cantidad de clientes y la probabilidad del último incluido, y descarga el archivo con files.download. (`notebook` líneas 547–563)

## Archivos

- `resultados` · explicacion · Markdown · 24 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tomasfarias-hub/resultados.txt) — Tablas con los valores que el texto atribuye a las salidas guardadas de la notebook: en 202106 (164.114 clientes, 1.098 BAJA+2), cuatro filas de envíos y ganancia (341,82 M, 350,40 M, 356,04 M y 359,34 M); para 202108, método de corte, 164.647 clientes en cartera, 11.972 enviados (7,27 %), probabilidad del último incluido 0,01685 y nombre del archivo.
- `dataset` · explicacion · Markdown · 9 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tomasfarias-hub/dataset.txt) — Nota que indica colocar el dataset de la competencia en data/competencia_01.csv y que ese archivo no se sube al repositorio.
- `reproducibilidad` · explicacion · Markdown · 53 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tomasfarias-hub/reproducibilidad.txt) — Texto sobre cómo reproducir la entrega: entorno Google Colab, tres pasos de ejecución, efecto del interruptor USAR_PARAMS_FIJOS (con False cada ejecución suma 15 trials al estudio y, según el texto, el sampler de Optuna no tiene semilla), origen de las 50 semillas y una sección Versiones con los campos sin completar.
- `Requirements` · configuracion · Markdown · 9 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tomasfarias-hub/Requirements.txt) — Lista de 9 paquetes de Python sin versión: numpy, pandas, scipy, scikit-learn, matplotlib, plotly, lightgbm, optuna y jupyter.
- `README.md` · explicacion · Markdown · 254 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tomasfarias-hub/README.md.txt) — Presentación de la entrega: el problema y el punto de equilibrio 0,025, una estructura de repositorio, los pasos para correr la notebook en Colab, la descripción de la notebook sección por sección (4.1 a 4.15) y tablas de resultados en 202106 y de la entrega de 202108. La estructura de la sección 2 nombra requirements.txt, notebooks/competencia_01_lgbm.ipynb, docs/reproducibilidad.md, resultados/hiperparametros.json y resultados/metricas.md; en el repositorio los archivos están en la raíz con los nombres Requirements, notebook, reproducibilidad, resultados y dataset, y no hay un archivo hiperparametros.json.
- `notebook` · principal · Jupyter (python) · 563 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tomasfarias-hub/notebook.txt) — Notebook de Python para Google Colab con 22 celdas (18 de código y 4 de texto). Contiene todo el camino: lectura, variables nuevas, clase binaria, definición de Optuna, entrenamiento, evaluación en 202106, análisis de hojas, semillerío y escritura del CSV de 202108.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### notebook

Notebook de Python para Google Colab con 22 celdas (18 de código y 4 de texto). Contiene todo el camino: lectura, variables nuevas, clase binaria, definición de Optuna, entrenamiento, evaluación en 202106, análisis de hojas, semillerío y escritura del CSV de 202108.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] Instala Optuna con pip e importa pandas, numpy, matplotlib, plotly, gaussian_kde y
#   ks_2samp de scipy, StratifiedShuffleSplit, lightgbm y optuna con cuatro funciones de visualización. En el
#   resto del archivo no aparecen llamadas a plotly, gaussian_kde, ks_2samp ni a las funciones plot_ de Optuna.
#%% celda 1 [código]
#cargo las librerías a utilizar

!pip install -q optuna

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px

from scipy.stats import gaussian_kde
from scipy.stats import ks_2samp

from sklearn.model_selection import StratifiedShuffleSplit

import lightgbm as lgb

import optuna
from optuna.visualization import plot_optimization_history, plot_param_importances, plot_slice, plot_contour

# [Anotación · líneas 25–54] Monta Google Drive y define base_path y las subcarpetas data/, modelos/ y db/.
#   Fija ganancia_acierto = 1.072.500 y costo_estimulo = 27.500, los meses de cada etapa (mes_train = 202103 y
#   202104; mes_test = 202106; mes_final_train = 202103, 202104, 202105 y 202106; mes_futuro = 202108) y, con
#   semilla = 2323, genera una lista de 50 enteros distintos menores que 1.000.000. Lee competencia_01.csv en un
#   DataFrame.
#%% celda 2 [código]
#cargo el dataset con la target

from google.colab import drive
drive.mount('/content/drive')

base_path = '/content/drive/MyDrive/DMEyF/2026/notebooks/'

dataset_path = base_path + 'data/'
modelos_path = base_path + 'modelos/'
db_path = base_path + 'db/'

dataset_file = 'competencia_01.csv'

ganancia_acierto = 1_072_500
costo_estimulo = 27_500

#meses de train y test

mes_train = [202103, 202104]                 # validación
mes_test  = 202106                           # con clase conocida
mes_final_train = [202103, 202104, 202105, 202106]
mes_futuro = 202108                          # solo para predecir

# agregue sus semillas
semilla = 2323
np.random.seed(semilla)
semillas = np.random.choice(1000000, size=50, replace=False).tolist()

data = pd.read_csv(dataset_path + dataset_file)

# [Anotación · líneas 56–86] Define la lista CAMPOS_DELTA con 17 variables, ordena el dataset por
#   numero_de_cliente y foto_mes, y crea tc_consumo_total como suma de Visa_mconsumototal y Master_mconsumototal
#   con los vacíos en 0. Para cada variable de la lista calcula delta_1_<variable> = valor menos valor de la
#   fila anterior del mismo cliente (shift(1) dentro del grupo), convierte las columnas nuevas a float32 y las
#   agrega. Imprime las columnas de la lista ausentes en el dataset y, por mes, la fracción de filas con
#   delta_1_mpayroll no nulo.
#%% celda 3 [texto]
#Feature Engineering

#%% celda 4 [código]
#deltas

CAMPOS_DELTA = [
    "mpayroll", "cpayroll_trx",
    "mtarjeta_visa_consumo", "ctarjeta_visa_transacciones", "mttarjeta_visa_debitos_automaticos",
    "tc_consumo_total",
    "cproductos", "ctrx_quarter", "active_quarter", "internet", "cdescubierto_preacordado",
    "chomebanking_transacciones", "cmobile_app_trx",
    "mcuentas_saldo", "mcaja_ahorro", "mprestamos_personales", "mplazo_fijo_pesos",
]

data = data.sort_values(["numero_de_cliente", "foto_mes"]).reset_index(drop=True)

data["tc_consumo_total"] = data["Visa_mconsumototal"].fillna(0) + data["Master_mconsumototal"].fillna(0)

faltan = [c for c in CAMPOS_DELTA if c not in data.columns]
print("Columnas que faltan:", faltan)

g = data.groupby("numero_de_cliente", sort=False)
nuevas = {f"delta_1_{c}": data[c] - g[c].shift(1) for c in CAMPOS_DELTA if c not in faltan}

nuevas = pd.DataFrame(nuevas).astype("float32")
data = pd.concat([data, nuevas], axis=1)
print("Variables nuevas:", nuevas.shape[1], "| shape final:", data.shape)

# control: % de filas con delta calculado, por mes
print(data.groupby("foto_mes")["delta_1_mpayroll"].apply(lambda s: s.notna().mean()).round(3))

# [Anotación · líneas 88–94] Crea la columna clase_binaria: 1 si clase_ternaria es BAJA+2 y 0 en cualquier
#   otro caso.
#%% celda 5 [texto]
#LGBM

#%% celda 6 [código]
#consolido las clases

data['clase_binaria'] = np.where(data['clase_ternaria'] == 'BAJA+2', 1, 0)

# [Anotación · líneas 96–110] Define las cuatro columnas que no entran como variables predictoras
#   (clase_ternaria, clase_binaria, numero_de_cliente, foto_mes). Separa las filas de 202103 y 202104 como
#   entrenamiento y las de 202106 como prueba, arma las matrices X y los vectores de clase, y construye un
#   lgb.Dataset para cada conjunto.
#%% celda 7 [código]
NO_FEATURES = ['clase_ternaria', 'clase_binaria', 'numero_de_cliente', 'foto_mes']

train_data = data[data['foto_mes'].isin(mes_train)]
test_data  = data[data['foto_mes'] == mes_test]

X_train = train_data.drop(columns=NO_FEATURES)
y_train_binaria = train_data['clase_binaria']

X_test = test_data.drop(columns=NO_FEATURES)
y_test_binaria = test_data['clase_binaria']
y_test_class = test_data['clase_ternaria']

train_data_lgb = lgb.Dataset(X_train, label=y_train_binaria)
test_data_lgb = lgb.Dataset(X_test, label=y_test_binaria)

# [Anotación · líneas 112–124] Crea un StratifiedShuffleSplit de 5 particiones con 30 % de validación y
#   random_state = semillas[0]. Define la métrica ganancia_prob_lgm: asigna 1.072.500 a las filas con etiqueta 1
#   y −27.500 a las de etiqueta 0, suma las de probabilidad ≥ 0,025 y divide por prop = 0,3; la devuelve con el
#   nombre gan_prob y como métrica a maximizar.
#%% celda 8 [código]
#optimización con Optuna

import os

sss_opt = StratifiedShuffleSplit(n_splits=5, test_size=0.3, random_state=semillas[0])

def ganancia_prob_lgm(y_pred, data, prop=0.3):
  y_true = data.get_label()
  ganancia = np.where(y_true == 1, ganancia_acierto, 0) - np.where(y_true == 0, costo_estimulo, 0)
  return 'gan_prob', ganancia[y_pred >= 0.025].sum() / prop, True



# [Anotación · líneas 126–167] Función objetivo de Optuna. Cada trial propone num_leaves (8 a 100),
#   learning_rate (0,005 a 0,3), min_data_in_leaf (1 a 1000), feature_fraction (0,1 a 1,0) y bagging_fraction
#   (0,1 a 1,0); el resto queda fijo (objective binary, gbdt, max_bin 31, seed = semillas[0]). Corre lgb.cv con
#   hasta 1000 rondas, parada temprana de int(50 + 5/learning_rate) rondas, la métrica de ganancia y las 5
#   particiones definidas antes. Devuelve el máximo de la ganancia media de validación y guarda en el trial la
#   ronda en que se alcanza (best_iter).
def objective(trial):

    num_leaves = trial.suggest_int('num_leaves', 8, 100)
    learning_rate = trial.suggest_float('learning_rate', 0.005, 0.3) # mas bajo, más iteraciones necesita
    min_data_in_leaf = trial.suggest_int('min_data_in_leaf', 1, 1000)
    feature_fraction = trial.suggest_float('feature_fraction', 0.1, 1.0)
    bagging_fraction = trial.suggest_float('bagging_fraction', 0.1, 1.0)

    params = {
        'objective': 'binary',
        'metric': 'custom',
        'boosting_type': 'gbdt',
        'first_metric_only': True,
        'boost_from_average': True,
        'feature_pre_filter': False,
        'max_bin': 31,
        'num_leaves': num_leaves,
        'learning_rate': learning_rate,
        'min_data_in_leaf': min_data_in_leaf,
        'feature_fraction': feature_fraction,
        'bagging_fraction': bagging_fraction,
        'seed': semillas[0],
        'verbose': -1
    }

    cv_results = lgb.cv(
        params,
        train_data_lgb,
        num_boost_round=1000, # modificar, subir y subir...
        callbacks=[lgb.early_stopping(stopping_rounds=int(50 + 5 / learning_rate), verbose=False)],
        feval=ganancia_prob_lgm,
        folds=sss_opt.split(X_train, y_train_binaria), # usamos StratifiedShuffleSplit en vez del k-fold interno
        seed=semillas[0]
    )

    max_gan = max(cv_results['valid gan_prob-mean'])
    best_iter = cv_results['valid gan_prob-mean'].index(max_gan) + 1

    # Guardamos cual es la mejor iteración del modelo
    trial.set_user_attr("best_iter", best_iter)

    return max_gan

# [Anotación · líneas 169–180] Crea la carpeta db/ si no existe y abre o crea el estudio de Optuna
#   exp_301_lgbm_sss con dirección maximize, guardado en la base SQLite optimization_lgbm.db y con
#   load_if_exists = True.
# Asegurar que el directorio de la base de datos exista
os.makedirs(db_path, exist_ok=True)

storage_name = "sqlite:///" + db_path + "optimization_lgbm.db"
study_name = "exp_301_lgbm_sss"

study = optuna.create_study(
    direction="maximize",
    study_name=study_name,
    storage=storage_name,
    load_if_exists=True,
)

# [Anotación · líneas 182–199] Define el interruptor USAR_PARAMS_FIJOS = True, el diccionario PARAMS_OPTIMOS
#   con cinco valores (num_leaves 19, learning_rate 0.021127696716538504, min_data_in_leaf 858, feature_fraction
#   0.8257277981830174, bagging_fraction 0.2302571235653956) y BEST_ITER = 418. La llamada
#   study.optimize(objective, n_trials=15) sólo se ejecuta si el interruptor está en False. El comentario de la
#   línea 184 nombra el trial 15.
#%% celda 9 [código]
#Para evitar tener que correr optuna en la evaluación, seteo los parametros óptimos que utilicé
# True  -> usa los hiperparámetros de la entrega (trial 15)
# False -> corre la optimización con Optuna
USAR_PARAMS_FIJOS = True

PARAMS_OPTIMOS = {
    'num_leaves': 19,
    'learning_rate': 0.021127696716538504,
    'min_data_in_leaf': 858,
    'feature_fraction': 0.8257277981830174,
    'bagging_fraction': 0.2302571235653956,
}
BEST_ITER = 418

#%% celda 10 [código]
if not USAR_PARAMS_FIJOS:
    study.optimize(objective, n_trials=15)

# [Anotación · líneas 201–243] Según el interruptor, toma los hiperparámetros y la cantidad de rondas de los
#   valores fijos o del trial de mayor valor del estudio (study.best_trial). El comentario de la línea 207
#   nombra el trial 30. Arma el diccionario params (objective binary, gbdt, max_bin 31, boost_from_average True,
#   feature_pre_filter False, seed = semillas[0], sin la clave metric) y entrena un modelo con lgb.train sobre
#   202103 y 202104 con best_iter rondas.
#%% celda 11 [código]
#entreno el modelo

#entreno el modelo

if USAR_PARAMS_FIJOS:
    # hiperparámetros de la entrega (trial 30), definidos en la celda anterior
    best_iter = BEST_ITER
    num_leaves = PARAMS_OPTIMOS['num_leaves']
    learning_rate = PARAMS_OPTIMOS['learning_rate']
    min_data_in_leaf = PARAMS_OPTIMOS['min_data_in_leaf']
    feature_fraction = PARAMS_OPTIMOS['feature_fraction']
    bagging_fraction = PARAMS_OPTIMOS['bagging_fraction']
else:
    # mejor trial del estudio de Optuna
    best_iter = study.best_trial.user_attrs["best_iter"]
    num_leaves = study.best_trial.params['num_leaves']
    learning_rate = study.best_trial.params['learning_rate']
    min_data_in_leaf = study.best_trial.params['min_data_in_leaf']
    feature_fraction = study.best_trial.params['feature_fraction']
    bagging_fraction = study.best_trial.params['bagging_fraction']

print(f"Árboles: {best_iter} | num_leaves: {num_leaves} | learning_rate: {learning_rate:.4f}")

params = {
    'objective': 'binary',
    'boosting_type': 'gbdt',
    'first_metric_only': True,
    'boost_from_average': True,
    'feature_pre_filter': False,
    'max_bin': 31,
    'num_leaves': num_leaves,
    'learning_rate': learning_rate,
    'min_data_in_leaf': min_data_in_leaf,
    'feature_fraction': feature_fraction,
    'bagging_fraction': bagging_fraction,
    'seed': semillas[0],
    'verbose': 0
}

model = lgb.train(params,
                  train_data_lgb,
                  num_boost_round=best_iter)

# [Anotación · líneas 245–257] Arma una tabla con la importancia de cada variable (el valor por defecto de
#   feature_importance, cantidad de usos en divisiones), la ordena de mayor a menor y muestra las de importancia
#   mayor que cero. Calcula las probabilidades del modelo sobre las filas de 202106.
#%% celda 12 [código]
#importancia de las variables

importances = model.feature_importance()
feature_names = X_train.columns.tolist()
importance_df = pd.DataFrame({'feature': feature_names, 'importance': importances})
importance_df = importance_df.sort_values('importance', ascending=False)
importance_df[importance_df['importance'] > 0]

#%% celda 13 [código]
#predicción

y_pred_lgm = model.predict(X_test)

# [Anotación · líneas 259–269] Define gan_prob, que suma 1.072.500 por cada fila de clase 1 y −27.500 por cada
#   fila de clase 0 entre las de probabilidad ≥ 0,025 y divide por prop (1 por defecto). Imprime la ganancia del
#   modelo en 202106.
#%% celda 14 [texto]
#Evaluación del modelo

#%% celda 15 [código]
#medición de ganancia en junio

def gan_prob(y_pred, y_true, prop = 1):
  ganancia = np.where(y_true == 1, ganancia_acierto, 0) - np.where(y_true == 0, costo_estimulo, 0)
  return ganancia[y_pred >= 0.025].sum() / prop

print("Ganancia LGBM en junio:", gan_prob(y_pred_lgm, y_test_binaria))

# [Anotación · líneas 271–283] Comienzo de get_leaf_info_lgbm: obtiene con pred_leaf=True la hoja en la que
#   cae cada fila en cada árbol, lleva el resultado a una matriz de dos dimensiones y toma la serie de clases
#   reales.
#%% celda 16 [código]
def get_leaf_info_lgbm(model, X, y_clase):
    # Hoja asignada a cada observación para cada árbol
    hojas = model.predict(X, pred_leaf=True)

    # Si hay un solo árbol, garantizar que sea una matriz 2D
    hojas = np.asarray(hojas)
    if hojas.ndim == 1:
        hojas = hojas.reshape(-1, 1)

    # Clases reales
    clases = pd.Series(y_clase).reset_index(drop=True)

# [Anotación · líneas 284–328] Para cada árbol cruza hoja contra clase y cuenta las filas BAJA+1, BAJA+2 y
#   CONTINUA de cada hoja, completa con 0 las clases ausentes, agrega el total (Samples), la clase con más filas
#   (Predicted Class) y el índice del árbol, y concatena todo en una tabla con una fila por árbol y hoja. Aplica
#   la función al conjunto de entrenamiento con clase_ternaria.
    leaf_info = []

    # Analizar cada árbol por separado
    for tree_idx in range(hojas.shape[1]):
        df = pd.DataFrame({
            'Node': hojas[:, tree_idx],
            'Clase': clases
        })

        # Contar observaciones por hoja y clase
        tabla = pd.crosstab(df['Node'], df['Clase'])

        # Asegurar que existan las tres columnas
        for clase in ['BAJA+1', 'BAJA+2', 'CONTINUA']:
            if clase not in tabla.columns:
                tabla[clase] = 0

        tabla = tabla[['BAJA+1', 'BAJA+2', 'CONTINUA']]
        tabla['Samples'] = tabla.sum(axis=1)

        # Clase mayoritaria de cada hoja
        tabla['Predicted Class'] = tabla[
            ['BAJA+1', 'BAJA+2', 'CONTINUA']
        ].idxmax(axis=1)

        tabla = tabla.reset_index()

        # Ordenar columnas como en la tabla original
        tabla = tabla[
            ['Node', 'Samples', 'Predicted Class',
             'BAJA+1', 'BAJA+2', 'CONTINUA']
        ]

        tabla.insert(0, 'Tree', tree_idx)
        leaf_info.append(tabla)

    return pd.concat(leaf_info, ignore_index=True)

leaf_df = get_leaf_info_lgbm(
    model,
    X_train,
    train_data['clase_ternaria']
)

leaf_df

# [Anotación · líneas 330–341] Agrega a la tabla de hojas la columna ganancia = 1.072.500 × BAJA+2 − 27.500 ×
#   BAJA+1 − 27.500 × CONTINUA y ordena las hojas de mayor a menor ganancia.
#%% celda 17 [código]
#ganancia por nodo

leaf_df["ganancia"] = (
    ganancia_acierto * leaf_df["BAJA+2"]
    - costo_estimulo * leaf_df["BAJA+1"]
    - costo_estimulo * leaf_df["CONTINUA"]
)

leaf_df.sort_values("ganancia", ascending=False, inplace=True)

leaf_df

# [Anotación · líneas 343–358] Extrae con trees_to_dataframe el valor de cada hoja del modelo, obtiene el
#   número de hoja del texto de node_index y lo une a la tabla por árbol y hoja. Calcula prob_empirica = BAJA+2
#   / Samples y prob_modelo_hoja = 1 / (1 + exp(−valor_hoja)), y ordena por esta última de mayor a menor.
#%% celda 18 [código]
# valor de cada hoja según el modelo (log-odds)
td = model.trees_to_dataframe()
hojas = td[td['split_feature'].isna()].copy()          # solo hojas
hojas['Node'] = hojas['node_index'].str.split('-L').str[1].astype(int)
hojas = hojas.rename(columns={'tree_index': 'Tree', 'value': 'valor_hoja'})
hojas = hojas[['Tree', 'Node', 'valor_hoja']]

# lo pego a leaf_df (mismas claves Tree / Node que devuelve pred_leaf)
leaf_df = leaf_df.merge(hojas, on=['Tree', 'Node'], how='left')

leaf_df["prob_empirica"] = leaf_df["BAJA+2"] / leaf_df["Samples"]
leaf_df["prob_modelo_hoja"] = 1 / (1 + np.exp(-leaf_df["valor_hoja"]))

leaf_df.sort_values("prob_modelo_hoja", ascending=False, inplace=True)
leaf_df

# [Anotación · líneas 360–381] Vuelve a generar la tabla de hojas, predice las probabilidades del modelo sobre
#   el entrenamiento y, para cada árbol, calcula la media de esa probabilidad final entre las filas de cada hoja
#   (prob_final_media). Une ese valor a la tabla y recalcula prob_empirica.
#%% celda 19 [código]
import matplotlib.pyplot as plt

# Regeneramos leaf_df para asegurar que esté limpio y evitar problemas de merges repetidos
leaf_df = get_leaf_info_lgbm(
    model,
    X_train,
    train_data['clase_ternaria']
)

y_pred_train = pd.Series(model.predict(X_train)).reset_index(drop=True)
hojas_mat = model.predict(X_train, pred_leaf=True)

prob_media = []
for t in range(hojas_mat.shape[1]):
    g = y_pred_train.groupby(hojas_mat[:, t]).mean().reset_index()
    g.columns = ["Node", "prob_final_media"]
    g.insert(0, "Tree", t)
    prob_media.append(g)

leaf_df = leaf_df.merge(pd.concat(prob_media), on=["Tree", "Node"], how="left")
leaf_df["prob_empirica"] = leaf_df["BAJA+2"] / leaf_df["Samples"]

# [Anotación · líneas 383–402] Dibuja dos gráficos: la dispersión de prob_empirica contra prob_final_media por
#   hoja, con líneas en 0,025, y un histograma de 100 intervalos en escala logarítmica de las probabilidades
#   predichas en entrenamiento, con una línea en 0,025. Muestra la tabla de hojas ordenada por prob_final_media.
# Gráfico: probabilidad empírica de la hoja vs probabilidad que le da el modelo completo
fig, ax = plt.subplots(1, 2, figsize=(14, 5))

ax[0].scatter(leaf_df["prob_empirica"], leaf_df["prob_final_media"], s=5, alpha=0.3)
ax[0].axhline(0.025, color="red", ls="--", label="umbral 0.025")
ax[0].axvline(0.025, color="red", ls="--")
ax[0].set_xlabel("Prob. empírica de la hoja (BAJA+2 / Samples)")
ax[0].set_ylabel("Prob. final media del modelo")
ax[0].set_title("Hojas: empírica vs modelo")
ax[0].legend()

ax[1].hist(y_pred_train, bins=100, log=True)
ax[1].axvline(0.025, color="red", ls="--")
ax[1].set_xlabel("Probabilidad predicha (train)")
ax[1].set_title("Distribución de probabilidades (escala log)")

plt.tight_layout()
plt.show()

leaf_df.sort_values("prob_final_media", ascending=False)

# [Anotación · líneas 404–428] Con el modelo individual predice las filas de 202106 y las ordena de mayor a
#   menor probabilidad. Asigna 1.072.500 a cada BAJA+2 y −27.500 al resto y calcula la suma acumulada. Obtiene
#   n_opt, la cantidad de envíos donde la ganancia acumulada es máxima, y n_umbral, la cantidad de clientes con
#   probabilidad ≥ 0,025, e imprime ambas con su ganancia.
#%% celda 20 [código]
#ganancia acumulada por posibles puntos de corte

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

mes_eval = 202106   # mes con clase conocida, distinto del mes con que entrenaste el modelo

# 1) Predicciones en el mes de evaluación, ordenadas de mayor a menor probabilidad
d_eval = data[data["foto_mes"] == mes_eval].copy()
d_eval["prob"] = model.predict(d_eval[X_train.columns])
d_eval = d_eval.sort_values("prob", ascending=False).reset_index(drop=True)

# 2) Ganancia por cliente estimulado y ganancia acumulada
g = np.where(d_eval["clase_ternaria"] == "BAJA+2", ganancia_acierto, -costo_estimulo)
gan_acum = np.cumsum(g)
n = np.arange(1, len(g) + 1)

n_opt = int(gan_acum.argmax() + 1)
n_umbral = int((d_eval["prob"] >= 0.025).sum())

print(f"Clientes en {mes_eval}: {len(d_eval):,} | BAJA+2: {(d_eval['clase_ternaria']=='BAJA+2').sum():,}")
print(f"Corte óptimo: {n_opt:,} envíos ({100*n_opt/len(d_eval):.2f}%) -> ganancia {gan_acum[n_opt-1]/1e6:,.2f} M")
print(f"Corte por umbral 0.025: {n_umbral:,} envíos ({100*n_umbral/len(d_eval):.2f}%) -> ganancia {gan_acum[n_umbral-1]/1e6:,.2f} M")

# [Anotación · líneas 430–459] Arma una tabla con envíos, porcentaje de la cartera, probabilidad de corte y
#   ganancia en millones para 12 cortes (500, 1000, 2000, 3000, 4000, 5000, 6000, 8000, 10000, 15000, 20000 y
#   30000). Grafica la curva de ganancia acumulada completa y recortada a 4 × n_opt, con líneas en n_opt y
#   n_umbral. Imprime n_opt llevado a 202108 como cantidad de envíos, junto con un texto fijo que menciona 5.589
#   envíos.
# 3) Tabla para distintos puntos de corte
cortes = [500, 1000, 2000, 3000, 4000, 5000, 6000, 8000, 10000, 15000, 20000, 30000]
cortes = [c for c in cortes if c <= len(d_eval)]
tabla = pd.DataFrame({
    "envios": cortes,
    "% cartera": [100 * c / len(d_eval) for c in cortes],
    "prob_corte": [d_eval["prob"].iloc[c - 1] for c in cortes],
    "ganancia_M": [gan_acum[c - 1] / 1e6 for c in cortes],
})
display(tabla.round(4))

# 4) Gráfico: curva completa y zoom alrededor del óptimo
fig, ax = plt.subplots(1, 2, figsize=(15, 5))
for a, lim in zip(ax, [len(n), min(len(n), n_opt * 4)]):
    a.plot(n[:lim], gan_acum[:lim] / 1e6, color="#2a6fdb")
    a.axvline(n_opt, color="green", ls="--", label=f"óptimo: {n_opt:,}")
    a.axvline(n_umbral, color="red", ls="--", label=f"umbral 0.025: {n_umbral:,}")
    a.axhline(0, color="gray", lw=0.8)
    a.set_xlabel("Cantidad de clientes estimulados")
    a.set_ylabel("Ganancia acumulada (millones)")
    a.legend()
ax[0].set_title(f"Ganancia acumulada ({mes_eval}) - curva completa")
ax[1].set_title("Zoom alrededor del óptimo")
plt.tight_layout()
plt.show()

# 5) Equivalente en agosto, trasladando el corte como proporción de la cartera
n_agosto = int((data["foto_mes"] == 202108).sum())
print(f"Corte óptimo trasladado a agosto: {round(n_opt / len(d_eval) * n_agosto):,} envíos "
      f"(el que subiste fueron 5,589)")

# [Anotación · líneas 461–483] Parámetros de la celda de entrega: mes_eval = 202106, mes_futuro = 202108,
#   metodo = "optimo", umbral = 0,025, n_envios_manual = 8000, N_SEMILLAS = 5 y VENTANA = 500. Un assert
#   verifica que mes_eval no esté entre los meses de mes_train.
#%% celda 21 [texto]
#Creación del archivo para la entrega

#%% celda 22 [código]
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from google.colab import files

mes_eval = 202106       # mes con clase conocida, distinto de los meses de train
mes_futuro = 202108     # mes a predecir

# Cómo cortar: "optimo" (N que maximiza la ganancia suavizada en mes_eval, trasladado a agosto),
#              "umbral" (prob >= umbral) o "cantidad" (top N fijo)
metodo = "optimo"
umbral = 0.025
n_envios_manual = 8000   # solo se usa si metodo == "cantidad"

N_SEMILLAS = 5           # semillerío (probá con 3 la primera vez para medir el tiempo)
VENTANA = 500            # ventana de la media móvil para suavizar la curva de ganancia

assert mes_eval not in mes_train, "mes_eval no puede estar entre los meses con los que entrenaste el modelo"

# [Anotación · líneas 485–496] Define entrenar_promedio: para cada una de las primeras n_semillas semillas de
#   la lista entrena un LightGBM con el diccionario params, cambiando seed y max_bin, con best_iter rondas sobre
#   df_train; suma las probabilidades sobre df_pred y devuelve el promedio.
def entrenar_promedio(df_train, df_pred, n_semillas, max_bin):
    """Entrena n_semillas modelos y devuelve el promedio de sus probabilidades sobre df_pred."""
    X_tr = df_train[X_train.columns]
    y_tr = df_train["clase_binaria"]
    X_pr = df_pred[X_train.columns]
    prob = np.zeros(len(df_pred))
    for i, s in enumerate(semillas[:n_semillas], 1):
        p = {**params, "seed": s, "max_bin": max_bin}
        m = lgb.train(p, lgb.Dataset(X_tr, label=y_tr), num_boost_round=best_iter)
        prob += m.predict(X_pr)
        print(f"  semilla {i}/{n_semillas} lista")
    return prob / n_semillas

# [Anotación · líneas 498–523] Entrena el semillerío de 5 modelos con 202103 y 202104 (max_bin 31) y promedia
#   las probabilidades sobre 202106. Ordena por probabilidad, calcula la ganancia acumulada y la suaviza con una
#   media móvil centrada de 500 posiciones (min_periods = 1). n_opt es la posición del máximo de la curva
#   suavizada y prop_opt, esa cantidad dividida por las filas de 202106. Imprime ese corte y el máximo de la
#   curva sin suavizar, y grafica ambas curvas.
# 1) Validación: semillerío entrenado con mes_train y evaluado en mes_eval
print("Validación:")
d_val_train = data[data["foto_mes"].isin(mes_train)]
d_eval = data[data["foto_mes"] == mes_eval].copy()
d_eval["prob"] = entrenar_promedio(d_val_train, d_eval, N_SEMILLAS, max_bin=31)
d_eval = d_eval.sort_values("prob", ascending=False).reset_index(drop=True)

g = np.where(d_eval["clase_ternaria"] == "BAJA+2", ganancia_acierto, -costo_estimulo)
gan_acum = np.cumsum(g)
gan_suave = pd.Series(gan_acum).rolling(VENTANA, center=True, min_periods=1).mean().values

n_opt = int(gan_suave.argmax() + 1)
prop_opt = n_opt / len(d_eval)
print(f"[{mes_eval}] corte óptimo (curva suavizada): {n_opt:,} envíos ({100*prop_opt:.2f}% de la cartera) "
      f"-> ganancia {gan_acum[n_opt-1]/1e6:,.2f} M")
print(f"[{mes_eval}] máximo crudo: {int(gan_acum.argmax()+1):,} envíos -> {gan_acum.max()/1e6:,.2f} M")

x = np.arange(1, len(gan_acum) + 1)
plt.figure(figsize=(9, 4))
plt.plot(x, gan_acum / 1e6, alpha=0.4, label="cruda")
plt.plot(x, gan_suave / 1e6, label="suavizada")
plt.axvline(n_opt, color="green", ls="--", label=f"óptimo: {n_opt:,}")
plt.axhline(0, color="gray", lw=0.8)
plt.xlabel("Clientes estimulados"); plt.ylabel("Ganancia acumulada (M)")
plt.title(f"Ganancia acumulada en {mes_eval} (promedio de {N_SEMILLAS} semillas)")
plt.legend(); plt.show()

# [Anotación · líneas 525–530] Entrena el semillerío de 5 modelos con las filas de 202103, 202104, 202105 y
#   202106 y max_bin 255, promedia las probabilidades sobre las filas de 202108 y las ordena de mayor a menor.
# 2) Modelo final: semillerío entrenado con marzo-junio (max_bin 255), predice el mes futuro
print("Modelo final:")
d_final = data[data["foto_mes"].isin(mes_final_train)]
d_futuro = data[data["foto_mes"] == mes_futuro].copy()
d_futuro["prob"] = entrenar_promedio(d_final, d_futuro, N_SEMILLAS, max_bin=255)
d_futuro = d_futuro.sort_values("prob", ascending=False)

# [Anotación · líneas 532–545] Elige los clientes según metodo: con "optimo", los primeros round(prop_opt ×
#   filas de 202108); con "umbral", los de probabilidad ≥ umbral; en otro caso, los primeros n_envios_manual. Se
#   queda con la columna numero_de_cliente y verifica con assert que no haya repetidos y que todos estén en
#   202108.
# 3) Selección de clientes según el método
if metodo == "optimo":
    n_envios = int(round(prop_opt * len(d_futuro)))      # mismo % de cartera que el óptimo de mes_eval
    elegidos = d_futuro.head(n_envios)
elif metodo == "umbral":
    elegidos = d_futuro[d_futuro["prob"] >= umbral]
else:
    elegidos = d_futuro.head(n_envios_manual)

entrega = elegidos[["numero_de_cliente"]]

# 4) Controles
assert entrega["numero_de_cliente"].is_unique
assert entrega["numero_de_cliente"].isin(data.loc[data["foto_mes"] == mes_futuro, "numero_de_cliente"]).all()

# [Anotación · líneas 547–563] Arma el nombre entrega_<mes_futuro>_<metodo>_<cantidad>.csv, crea modelos/ si
#   no existe y escribe el archivo sin índice ni encabezado en Drive y en /content/. Imprime la cantidad de
#   clientes sobre el total de 202108, las dos rutas y la probabilidad mínima entre los elegidos, y descarga el
#   archivo con files.download.
# 5) Guardado (sin encabezado): en Drive y en el entorno de Colab
nombre_archivo = f"entrega_{mes_futuro}_{metodo}_{len(entrega)}.csv"

os.makedirs(modelos_path, exist_ok=True)
archivo_drive = modelos_path + nombre_archivo
archivo_colab = "/content/" + nombre_archivo

entrega.to_csv(archivo_drive, index=False, header=False)
entrega.to_csv(archivo_colab, index=False, header=False)

print(f"{len(entrega):,} clientes de {len(d_futuro):,} ({100*len(entrega)/len(d_futuro):.2f}%)")
print("Guardado en Drive:", archivo_drive)
print("Guardado en Colab:", archivo_colab)
print("Prob. del último cliente incluido:", elegidos["prob"].min())

# 6) Descarga a tu computadora
files.download(archivo_colab)
```


## Explicaciones del alumno (texto original)

### resultados

> # Resultados de la corrida de la entrega
>
> Valores tomados de las salidas guardadas en `notebooks/competencia_01_lgbm.ipynb`.
>
> ## Evaluación en junio (202106)
>
> El mes tiene 164.114 clientes y 1.098 BAJA+2.
>
> | Modelo | Criterio de corte | Envíos | % cartera | Ganancia |
> |---|---|---|---|---|
> | 1 semilla | probabilidad ≥ 0,025 | 8.770 | 5,34 % | 341,82 M |
> | 1 semilla | óptimo (máximo de la curva) | 11.618 | 7,08 % | 350,40 M |
> | Semillerío de 5 | óptimo (curva suavizada) | 11.933 | 7,27 % | 356,04 M |
> | Semillerío de 5 | máximo crudo | 12.053 | 7,34 % | 359,34 M |
>
> ## Entrega (202108)
>
> | Dato | Valor |
> |---|---|
> | Método de corte | `optimo`: misma proporción de cartera que el óptimo suavizado de junio |
> | Clientes en la cartera de agosto | 164.647 |
> | Clientes enviados | **11.972 (7,27 %)** |
> | Probabilidad del último cliente incluido | 0,01685 |
> | Archivo | `modelos/entrega_202108_optimo_11972.csv` (sin encabezado) |

### dataset

> # Datos
>
> Colocar acá el dataset original de la competencia:
>
> ```
> data/competencia_01.csv
> ```
>
> El archivo no se sube al repositorio (ver `.gitignore`).

### reproducibilidad

> # Cómo reproducir la entrega
>
> ## Entorno
>
> La notebook está escrita para **Google Colab**: monta Google Drive con `google.colab.drive` y descarga el archivo final
> con `google.colab.files`. Esas dos librerías no existen fuera de Colab.
>
> La primera celda instala Optuna. Lightgbm, pandas, scikit-learn, matplotlib y plotly ya vienen en Colab.
>
> ## Pasos
>
> 1. Subir esta carpeta a Google Drive y colocar el dataset en `data/competencia_01.csv`.
> 2. En la segunda celda de la notebook, cambiar `base_path` por la ruta de esa carpeta en el Drive propio
>    (la notebook trae la ruta del autor):
>
>    ```python
>    base_path = '/content/drive/MyDrive/DMEyF/2026/notebooks/'
>    ```
>
>    Debe terminar en `/`, y adentro tienen que estar `data/` y `modelos/`. La carpeta `db/` se crea sola.
> 3. Ejecutar las celdas en orden.
>
> ## Optimización: ya resuelta
>
> La notebook trae el interruptor `USAR_PARAMS_FIJOS = True`. Con ese valor:
>
> - No se ejecuta Optuna: la celda `study.optimize` queda desactivada.
> - El modelo se entrena con los hiperparámetros de la entrega (`PARAMS_OPTIMOS` y `BEST_ITER = 418`).
>
> Así se obtiene el mismo modelo sin necesidad del archivo `.db` de Optuna.
>
> Si se pone `USAR_PARAMS_FIJOS = False`, se corre la optimización de cero. En ese caso:
>
> - El sampler de Optuna no tiene semilla, así que los trials no coinciden con los de la entrega.
> - Cada ejecución de `study.optimize(objective, n_trials=15)` suma 15 trials al estudio guardado en `db/`, y el mejor trial puede cambiar.
>
> ## Semillas
>
> `semilla = 2323`. De ella salen las 50 semillas (`semillas`) usadas en la validación y en el semillerío.
> Con los mismos datos, hiperparámetros y versiones de librerías el resultado debería coincidir.
> Pueden aparecer diferencias mínimas según la versión de LightGBM o la cantidad de hilos.
>
> ## Versiones
>
> Completar con las versiones usadas en Colab (`pip list | grep -iE "lightgbm|optuna|pandas|numpy|scikit-learn"`):
>
> ```
> lightgbm=
> optuna=
> pandas=
> numpy=
> scikit-learn=
> ```

### README.md

> # Predicción de bajas — Competencia 01 (agosto 2021)
>
> Modelo LightGBM que arma el listado de clientes a los que se les envía la campaña de retención en **agosto 2021 (202108)**.
>
> **Resultado:** 11.972 clientes (7,27 % de la cartera de 164.647). Aplicado a junio, el mismo procedimiento da una ganancia de unos 356 M.
>
> ## Contenido
>
> 1. [El problema](#1-el-problema)
> 2. [Estructura del repositorio](#2-estructura-del-repositorio)
> 3. [Cómo correrlo](#3-cómo-correrlo)
> 4. [Qué hace la notebook, sección por sección](#4-qué-hace-la-notebook-sección-por-sección)
> 5. [Resultados](#5-resultados)
>
> ---
>
> ## 1. El problema
>
> Cada cliente puede tener tres clases (`clase_ternaria`): `CONTINUA`, `BAJA+1` y `BAJA+2`. Se contacta a un cliente con una campaña de retención, y la economía es:
>
> | Situación | Resultado |
> |---|---|
> | Contactar a un BAJA+2 | **+ $1.072.500** |
> | Contactar a cualquier otro cliente | **− $27.500** |
> | No contactar | $0 |
>
> El objetivo es entregar la lista de `numero_de_cliente` a contactar en 202108, un mes para el que todavía no se conoce la clase. La lista tiene que maximizar la ganancia esperada.
>
> **Punto de equilibrio.** Contactar a un cliente con probabilidad *p* de ser BAJA+2 conviene si
> `p · 1.072.500 − (1 − p) · 27.500 > 0`, es decir, si `p > 27.500 / 1.100.000 = 0,025`.
> Por eso el umbral de probabilidad 0,025 aparece en varias partes del código.
>
> ---
>
> ## 2. Estructura del repositorio
>
> ```
> .
> ├── README.md
> ├── requirements.txt
> ├── notebooks/
> │   └── competencia_01_lgbm.ipynb     # todo el código, con las salidas de la corrida de la entrega
> ├── docs/
> │   └── reproducibilidad.md           # entorno, semillas y el tema de Optuna, en detalle
> ├── resultados/
> │   ├── hiperparametros.json          # hiperparámetros del modelo final
> │   └── metricas.md                   # ganancias en junio y datos de la entrega
> ├── data/                             # acá va competencia_01.csv (no se sube al repo)
> └── modelos/                          # acá se guarda el CSV de la entrega
> ```
>
> ---
>
> ## 3. Cómo correrlo
>
> La notebook está escrita para **Google Colab**: monta Google Drive y descarga el archivo final con `google.colab.files`.
>
> 1. Subir esta carpeta a Google Drive y colocar el dataset en `data/competencia_01.csv`.
> 2. Abrir `notebooks/competencia_01_lgbm.ipynb` en Colab.
> 3. En la segunda celda, cambiar `base_path` por la ruta de esa carpeta en el Drive propio. Debe terminar en `/`:
>    ```python
>    base_path = '/content/drive/MyDrive/DMEyF/2026/notebooks/'
>    ```
> 4. Ejecutar todas las celdas en orden.
>
> La notebook trae `USAR_PARAMS_FIJOS = True`, así que **no re-optimiza**: entrena directamente con los hiperparámetros de la entrega.
> Los detalles (semillas, versiones, qué pasa si se activa Optuna) están en [`docs/reproducibilidad.md`](docs/reproducibilidad.md).
>
> ---
>
> ## 4. Qué hace la notebook, sección por sección
>
> ### 4.1 Librerías
>
> Instala Optuna (`!pip install -q optuna`) e importa:
>
> - **pandas y numpy** para los datos; **matplotlib** para los gráficos.
> - **scikit-learn**: `StratifiedShuffleSplit`, que se usa para armar las particiones de validación.
> - **LightGBM**: el modelo.
> - **Optuna**: la optimización de hiperparámetros.
>
> También se importan plotly, `gaussian_kde`, `ks_2samp` y las funciones `plot_*` de Optuna, que esta versión de la notebook no llega a usar.
>
> ### 4.2 Configuración y carga de datos
>
> - Monta Google Drive y define las rutas: `data/` (dataset), `modelos/` (entrega) y `db/` (base de Optuna).
> - Define la economía del problema: `ganancia_acierto = 1.072.500` y `costo_estimulo = 27.500`.
> - Define las **particiones temporales**:
>
>   | Variable | Meses | Uso |
>   |---|---|---|
>   | `mes_train` | 202103, 202104 | entrenamiento y optimización de hiperparámetros |
>   | `mes_test` | 202106 | evaluación, con clase conocida |
>   | `mes_final_train` | 202103 a 202106 | entrenamiento del modelo final |
>   | `mes_futuro` | 202108 | mes a predecir |
>
>   Mayo solo se usa en el entrenamiento final y julio no se usa. Entre el último mes de entrenamiento (abril) y el de evaluación (junio) hay dos meses,
>   la misma distancia que entre junio y agosto.
> - Fija la **semilla** `semilla = 2323` y genera con ella una lista de 50 semillas distintas (`semillas`), que se usan en toda la notebook para que los resultados se puedan repetir.
> - Lee `competencia_01.csv`.
>
> ### 4.3 Feature engineering
>
> Se agregan variables nuevas que describen cómo cambió cada cliente respecto del mes anterior:
>
> 1. Ordena el dataset por `numero_de_cliente` y `foto_mes`.
> 2. Crea `tc_consumo_total`: consumo de la tarjeta Visa más el de la Master (`Visa_mconsumototal + Master_mconsumototal`, con los vacíos en 0).
> 3. Para 17 variables (`CAMPOS_DELTA`) calcula `delta_1_<variable>` = valor del mes menos valor del mes anterior **del mismo cliente**. Las variables son:
>    - Sueldos: `mpayroll`, `cpayroll_trx`.
>    - Tarjetas: consumo y transacciones Visa, débitos automáticos, `tc_consumo_total`.
>    - Actividad: `cproductos`, `ctrx_quarter`, `active_quarter`, `internet`, `cdescubierto_preacordado`.
>    - Canales digitales: `chomebanking_transacciones`, `cmobile_app_trx`.
>    - Saldos y productos: `mcuentas_saldo`, `mcaja_ahorro`, `mprestamos_personales`, `mplazo_fijo_pesos`.
> 4. Verifica que ninguna columna falte e imprime el porcentaje de filas con delta calculado por mes. En 202103 es 0 % porque no existe febrero; en el resto, alrededor de 99 %.
>
> El dataset pasa de 155 columnas originales a **173** (155 + `tc_consumo_total` + 17 deltas), con 983.061 filas.
> Las nuevas columnas se guardan como `float32`.
>
> ### 4.4 Target binario
>
> Se crea `clase_binaria`: **1** si `clase_ternaria == 'BAJA+2'`, **0** en cualquier otro caso (`BAJA+1` y `CONTINUA`). Es el único tipo de cliente que da ganancia al contactarlo.
>
> ### 4.5 Armado de los conjuntos de entrenamiento y prueba
>
> - Excluye de las variables predictoras `clase_ternaria`, `clase_binaria`, `numero_de_cliente` y `foto_mes`. Quedan **170 variables**.
> - `train_data`: filas de marzo y abril. `test_data`: filas de junio.
> - Arma `X_train`, `y_train_binaria`, `X_test`, `y_test_binaria` y el `lgb.Dataset` de entrenamiento.
>
> ### 4.6 Optimización de hiperparámetros con Optuna
>
> Busca la mejor combinación de hiperparámetros de LightGBM para el objetivo del negocio, que es la ganancia y no una métrica estadística.
>
> **Validación cruzada.** `StratifiedShuffleSplit` con 5 particiones y 30 % de validación en cada una, estratificadas por clase. Se usa dentro de `lgb.cv`.
>
> **Métrica personalizada (`ganancia_prob_lgm`).** Para cada partición de validación suma la ganancia de los clientes cuya probabilidad predicha es ≥ 0,025
> y la divide por 0,3. Esa división escala la ganancia de una validación del 30 % de los datos a la del conjunto completo.
>
> **Función objetivo.** En cada trial, Optuna propone valores para cinco hiperparámetros:
>
> | Hiperparámetro | Rango |
> |---|---|
> | `num_leaves` | 8 a 100 |
> | `learning_rate` | 0,005 a 0,3 |
> | `min_data_in_leaf` | 1 a 1000 |
> | `feature_fraction` | 0,1 a 1,0 |
> | `bagging_fraction` | 0,1 a 1,0 |
>
> Con ellos corre `lgb.cv` hasta 1000 árboles, con `max_bin = 31` (más rápido) y *early stopping*: corta si la ganancia deja de mejorar durante `50 + 5 / learning_rate` iteraciones.
> Cuanto menor la tasa de aprendizaje, más paciencia. El trial devuelve la **máxima ganancia promedio** de la validación cruzada y guarda en `best_iter` en qué iteración se alcanzó.
>
> **Persistencia.** El estudio (`exp_301_lgbm_sss`) se guarda en una base SQLite en `db/`, de modo que puede retomarse y acumular trials.
>
> ### 4.7 Hiperparámetros fijos (interruptor)
>
> Para que la notebook se pueda reproducir sin repetir la optimización, hay un interruptor:
>
> - `USAR_PARAMS_FIJOS = True`: usa `PARAMS_OPTIMOS` y `BEST_ITER` (los valores del mejor trial de la corrida de la entrega).
> - `USAR_PARAMS_FIJOS = False`: se ejecuta `study.optimize(objective, n_trials=15)` y se usa el mejor trial del estudio.
>
> Valores fijos: `num_leaves = 19`, `learning_rate = 0,0211277`, `min_data_in_leaf = 858`, `feature_fraction = 0,8257278`, `bagging_fraction = 0,2302572` y 418 árboles.
>
> ### 4.8 Entrenamiento del modelo
>
> Elige los hiperparámetros según el interruptor, arma el diccionario `params` y entrena un LightGBM con `lgb.train` sobre marzo y abril, con 418 árboles y `max_bin = 31`.
>
> ### 4.9 Importancia de variables
>
> Calcula cuántas veces usó el modelo cada variable para dividir (importancia por *split*) y la ordena de mayor a menor. De las 170 variables, **138** tienen importancia mayor que cero.
> Las más usadas son `mrentabilidad_annual`, `mcuentas_saldo`, `mprestamos_personales`, `ctrx_quarter` y `mactivos_margen`.
>
> ### 4.10 Predicción en junio
>
> Aplica el modelo a las filas de junio (`X_test`), un mes que no se usó para entrenar ni para optimizar.
>
> ### 4.11 Ganancia en junio
>
> Con la función `gan_prob`, suma la ganancia real de junio de los clientes con probabilidad ≥ 0,025.
> Un solo modelo da **341.825.000** (sin escalar, porque se evalúa el mes completo).
>
> ### 4.12 Análisis de las hojas de los árboles
>
> Un modelo LightGBM es un conjunto de árboles, y cada observación cae en una hoja de cada árbol. Esta parte examina qué tipo de clientes cae en cada hoja:
>
> 1. `get_leaf_info_lgbm` obtiene, con `pred_leaf=True`, la hoja de cada observación de entrenamiento en cada árbol.
> 2. Cuenta cuántos `BAJA+1`, `BAJA+2` y `CONTINUA` hay en cada hoja y marca la clase mayoritaria. Devuelve una tabla con una fila por árbol y hoja.
> 3. **Ganancia por nodo**: `1.072.500 × BAJA+2 − 27.500 × (BAJA+1 + CONTINUA)`, ordenando las hojas de mayor a menor ganancia.
> 4. **Valor de la hoja según el modelo**: extrae con `trees_to_dataframe` el valor de cada hoja (en escala *log-odds*) y lo convierte en probabilidad con la función sigmoide, `1 / (1 + e^-valor)`.
>    También calcula la **probabilidad empírica** de cada hoja, `BAJA+2 / Samples`.
>
> ### 4.13 Probabilidad empírica contra probabilidad del modelo
>
> Regenera la tabla de hojas y, para cada una, calcula la probabilidad final media que el modelo completo asigna a las observaciones que caen ahí. Luego grafica:
>
> - Un diagrama de dispersión de la probabilidad empírica de cada hoja contra la probabilidad final media (con el umbral 0,025 marcado).
> - Un histograma, en escala logarítmica, de las probabilidades predichas sobre entrenamiento.
>
> Sirve para ver si las hojas con muchos BAJA+2 reales son las que el modelo califica con probabilidad alta.
>
> ### 4.14 Ganancia acumulada y puntos de corte
>
> Pregunta a cuántos clientes conviene enviar. Sobre junio:
>
> 1. Ordena a los clientes de mayor a menor probabilidad predicha.
> 2. Recorre la lista sumando +1.072.500 por cada BAJA+2 y −27.500 por cada otro cliente, para obtener la **ganancia acumulada** según la cantidad de envíos.
> 3. Identifica el corte óptimo (el máximo de la curva) y el corte por umbral 0,025.
> 4. Muestra una tabla de ganancia para cortes de 500 a 30.000 envíos y dos gráficos: la curva completa y un zoom alrededor del óptimo.
> 5. Traslada el corte óptimo a agosto **como proporción de la cartera**, porque agosto no tiene la misma cantidad de clientes que junio.
>
> ### 4.15 Creación del archivo de entrega
>
> Es la sección que produce el resultado final. Parámetros configurables: `metodo`, `umbral`, `n_envios_manual`, `N_SEMILLAS = 5` y `VENTANA = 500`.
>
> 1. **Semillerío.** La función `entrenar_promedio` entrena 5 modelos idénticos, cada uno con una semilla distinta, y promedia sus probabilidades. Promediar reduce la dependencia de una semilla en particular.
> 2. **Validación.** Entrena el semillerío con marzo y abril (`max_bin = 31`), predice junio, y calcula la curva de ganancia acumulada.
> 3. **Suavizado.** Aplica a la curva una media móvil centrada de 500 clientes para evitar que el máximo dependa de un pico aislado, y toma el máximo de la curva suavizada.
>    Eso da el corte óptimo como proporción de la cartera (`prop_opt`).
> 4. **Modelo final.** Entrena el semillerío de 5 modelos con marzo a junio y `max_bin = 255` (más resolución en las variables numéricas), y predice agosto.
> 5. **Selección de clientes**, según `metodo`:
>    - `"optimo"`: toma el mismo porcentaje de la cartera que el óptimo de junio.
>    - `"umbral"`: todos los clientes con probabilidad ≥ `umbral`.
>    - `"cantidad"`: los primeros `n_envios_manual`.
>
>    La entrega se hizo con `"optimo"`.
> 6. **Controles.** Verifica que no haya clientes repetidos y que todos pertenezcan a agosto.
> 7. **Guardado.** Escribe el archivo sin encabezado, un `numero_de_cliente` por línea, con el nombre `entrega_202108_optimo_11972.csv`, en `modelos/` (Drive) y en el entorno de Colab, y lo descarga.
>
> ---
>
> ## 5. Resultados
>
> Evaluación en junio (202106): 164.114 clientes, 1.098 BAJA+2.
>
> | Modelo | Criterio de corte | Envíos | % cartera | Ganancia |
> |---|---|---|---|---|
> | 1 semilla | probabilidad ≥ 0,025 | 8.770 | 5,34 % | 341,82 M |
> | 1 semilla | óptimo (máximo de la curva) | 11.618 | 7,08 % | 350,40 M |
> | Semillerío de 5 | óptimo (curva suavizada) | 11.933 | 7,27 % | 356,04 M |
>
> Ganancia de junio según la cantidad de envíos (un modelo):
>
> | Envíos | % cartera | Prob. de corte | Ganancia |
> |---|---|---|---|
> | 2.000 | 1,22 % | 0,0873 | 152,9 M |
> | 5.000 | 3,05 % | 0,0434 | 282,7 M |
> | 8.000 | 4,87 % | 0,0276 | 341,0 M |
> | 10.000 | 6,09 % | 0,0216 | 344,3 M |
> | 15.000 | 9,14 % | 0,0133 | 341,0 M |
> | 20.000 | 12,19 % | 0,0092 | 317,9 M |
> | 30.000 | 18,28 % | 0,0052 | 176,0 M |
>
> La ganancia crece rápido hasta unos 8.000 envíos, se mantiene casi plana entre 8.000 y 15.000, y cae después.
>
> **Entrega 202108:** 11.972 clientes, 7,27 % de los 164.647 de agosto. El último cliente incluido tiene probabilidad 0,01685.
> El detalle y los hiperparámetros están en [`resultados/`](resultados/).

