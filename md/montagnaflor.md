# montagnaflor — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: montagnaflor
- Repositorio: https://github.com/montagnaflor/DMEyF-Competencia-01
- Link posteado: https://github.com/montagnaflor/DMEyF-Competencia-01
- Commit: ff92d7d1004e64d115d00862083505e92dd0b1c7
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/montagnaflor/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/montagnaflor.json

## Resumen

La entrega tiene un README, una notebook de Python (prediccion_bajas_202108.ipynb) y orden_filas.csv.gz, un archivo con foto_mes y numero_de_cliente en el orden de filas de la corrida original. La notebook hace todo el recorrido. Con DuckDB agrega al CSV de la competencia deltas de 1 y 2 meses, cociente contra la media de 3 meses y pendiente de 3 meses para 17 campos, percent_rank dentro del mes para 13 montos y flags de productos que pasan a cero. Carga 202103-202106 y 202108, excluye las variables con PSI mayor a 0,25 entre 202106 y 202108, pasa a NaN las variables de préstamos personales en 202106 y descarta las variables cuya importancia no supera la de 20 canaritos. Entrena con BAJA+1 y BAJA+2 como positivos y el 25% de los CONTINUA. Optimiza un LightGBM con Optuna (100 trials, validación cruzada de 5 folds en 202103-202104, ganancia suavizada como métrica), evalúa los 5 trials de mayor ganancia con 10 semillas en 202106 y de ahí elige el trial y la cantidad de envíos. El modelo final se entrena en 202103-202106 con 20 semillas y max_bin 255; se promedian las probabilidades sobre 202108 y se escriben los clientes de mayor probabilidad. Un Random Forest se mide en 202106 como línea de base. Según el README, la entrega final tiene 11.036 clientes y una ganancia pública de 101,12.

**Qué entrega.** Un CSV sin encabezado con una columna, numero_de_cliente, con los n_envios clientes de 202108 de mayor probabilidad promedio de 20 modelos (exp/final_202108/entrega01_202108.csv). Según el README la entrega final tiene 11.036 clientes y una ganancia pública de 101,12. El archivo no está incluido en el repositorio.

**Cómo se ejecuta.** Según el README: (1) copiar el dataset de la competencia a data/competencia_01.csv, al lado de la notebook; (2) correr la notebook completa, por ejemplo con `jupyter nbconvert --to notebook --execute prediccion_bajas_202108.ipynb --output prediccion_bajas_202108_ejecutada.ipynb --ExecutePreprocessor.timeout=-1` (unas 5 horas en una PC de 8 núcleos y 8 GB de RAM); en Google Colab, subir competencia_01.csv a MyDrive/dmeyf/data/ y orden_filas.csv.gz a MyDrive/dmeyf/; (3) la entrega queda en exp/final_202108/entrega01_202108.csv.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: positivo = BAJA+1 o BAJA+2 (PARAM['positivos']), negativo = CONTINUA. La clase ternaria se codifica 0/1/2 en la columna clase y viaja en el peso de cada fila (1 + 0,00001 × clase) hasta la función de métrica, donde sólo BAJA+2 suma ganancia. Las filas de 202108 quedan con clase -1.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** Conserva todas las filas BAJA+1 y BAJA+2 y el 25% de las CONTINUA (PARAM['undersampling'] = 0.25): sortea un número uniforme por posición de fila con numpy default_rng(SEMILLAS[0]) y quedan las CONTINUA con valor menor a 0,25. Se aplica al conjunto de optimización (202103-202104) y al del modelo final (202103-202106); el holdout 202106 y 202108 se usan completos. En las métricas calculadas sobre datos submuestreados el costo de cada CONTINUA se multiplica por 4 (PESO_NEG = 1/0,25). El sorteo depende del orden de las filas; orden_filas.csv.gz fija ese orden.
- **Calidad de datos:** En las filas de 202106 se pasan a NaN todas las columnas cuyo nombre contiene 'prestamos_personales' (originales y derivadas), después del análisis de drift. Se excluyen las variables cuyo porcentaje de nulos cambia más de 20 puntos porcentuales entre 202106 y 202108. El mes 202107 no se carga para entrenar ni para medir.
- **Drifting:** Dos tratamientos. (1) En el feature engineering se agrega el percent_rank dentro de cada foto_mes de 13 variables de montos (columnas rank_mes_); las columnas originales se conservan. (2) Se calcula el PSI de cada variable entre 202106 y 202108 (10 intervalos por cuantiles de 202106 más uno para los nulos) y se excluyen las de PSI mayor a 0,25 o con diferencia de nulos mayor a 20 puntos porcentuales. Según el README quedan excluidas 9 variables.
- **Variables dentro del mes:** tc_consumo_total (Visa_mconsumototal + Master_mconsumototal), tc_uso_limite (ese consumo dividido por la suma de Visa_mlimitecompra y Master_mlimitecompra), ratio_transf_emitidas_recibidas (mtransferencias_emitidas / mtransferencias_recibidas) y rank_mes_ (percent_rank dentro del mes) de 13 montos.
- **Variables históricas:** Para 17 campos: delta contra 1 y 2 meses atrás (delta_1_, delta_2_), cociente contra el promedio de la ventana de 3 meses que termina en el mes actual (ratio_media3_) y pendiente de regresión en esa ventana (slope_3_). Para 7 contadores: flag_apago_ (mayor a 0 el mes anterior y 0 o nulo en el actual), la suma de esos flags (n_productos_apagados) y meses_sin_payroll_3 (meses de la ventana de 3 con cpayroll_trx en 0 o nulo). Se calculan por cliente sobre el CSV completo, antes de filtrar los meses que se cargan. No se guardan columnas de lag.
- **Selección de variables:** Exclusión por drift (PSI mayor a 0,25 o diferencia de nulos mayor a 20 puntos porcentuales entre 202106 y 202108) y después canaritos: se agregan 20 variables uniformes al azar a los datos de 202103-202104 submuestreados, se entrena un LightGBM de 200 árboles (learning_rate 0,05, num_leaves 16, min_data_in_leaf 1.000, feature_fraction 0,5, max_bin 31) y se descartan las variables con importancia por gain menor o igual a la del canarito de mayor importancia. excluir_manual está vacío. Según el README quedan 74 variables.
- **Optimización de hiperparámetros:** Optuna con TPESampler, 100 trials, sobre 202103-202104 submuestreados. Cada trial corre lgb.cv con 5 folds estratificados, hasta 3.000 árboles, early stopping de 100 rondas, max_bin 31 y la ganancia suavizada (media móvil de 401 posiciones sobre la curva acumulada) como única métrica. Rangos: learning_rate 0,01-0,3 (log), num_leaves 8-256 (log), min_data_in_leaf 50-5.000 (log), feature_fraction 0,1-1,0, bagging_fraction 0,5-1,0, lambda_l1 y lambda_l2 0,001-10 (log). El estudio se guarda en una base SQLite (optuna.db) y se retoma si ya existe. Los 5 trials de mayor ganancia de CV se reentrenan con 10 semillas y se miden en 202106; se elige el de mayor ganancia media.
- **Hiperparámetros finales:** Los del trial elegido (trial 58 según el README), con min_data_in_leaf multiplicado por el cociente de filas entre el conjunto final y el de optimización, max_bin = 255 y la cantidad de árboles que dejó el early stopping de la validación cruzada de ese trial. Fijos: objective binary, boosting_type gbdt, boost_from_average True, feature_pre_filter False, bagging_freq 1. Los valores numéricos del trial no figuran en el repositorio (la notebook no trae salidas y registro.json no está incluido).
- **Semillas:** Semilla primigenia 14072024: con numpy default_rng se sortean 50 enteros distintos entre 100.000 y 999.999 (lista SEMILLAS). Usos: SEMILLAS[0] submuestreo; [1] canaritos; [2], [3] y [4] folds, modelo y sampler del Random Forest; [5], [6] y [7] modelo, folds y sampler de la optimización de LightGBM; [10] a [19] las 10 semillas de evaluación en 202106; [30] a [49] las 20 semillas del modelo final.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio de las probabilidades de 20 modelos LightGBM con los mismos hiperparámetros y distinta semilla, entrenados en 202103-202106 submuestreado. En la evaluación de 202106 se calcula además la curva del promedio de 10 semillas por trial.
- **Corte:** Por cantidad de envíos. Sobre 202106 se calcula la ganancia de cada una de las 10 semillas del trial elegido en la grilla de 4.000 a 20.000 envíos de a 500; se toma el corte de mayor ganancia media y se traslada a 202108 como proporción de la cantidad de clientes del mes (corte / filas de 202106 × filas de 202108, redondeado). Según el README: 11.000 en junio y 11.036 en agosto.
- **Validación:** Validación cruzada estratificada de 5 folds sobre 202103-202104 dentro de la optimización, y holdout en 202106 (dos meses después de 202104), que no entra en la optimización: ahí se miden los 5 trials de mayor ganancia de CV con 10 semillas cada uno, con modelos entrenados en 202103-202104, y se eligen el trial y el corte. Un Random Forest optimizado con Optuna (25 trials, 3 folds, 100 árboles en la búsqueda y 500 en el ajuste) se mide también en 202106 como línea de base. La métrica es la ganancia de la competencia: 1.072.500 por cada BAJA+2 enviado y -27.500 por cada uno de los demás.
- **Salidas:** En exp/final_202108/: entregaNN_202108.csv (numero_de_cliente, sin encabezado, numeración correlativa), probabilidades_202108.csv, modelo_final_ultima_semilla.txt, registro.json, drift_jun_ago.csv, importancia_canaritos.csv, holdout_semillas.csv y optuna.db. En data/: competencia_01_fe.parquet. Las carpetas exp/ y data/ figuran en .gitignore y no están en el repositorio.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Validación cruzada (`validacion.validacion_cruzada`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)

## Técnicas sólo exploradas

- Random Forest (`modelo.random_forest`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Genera archivos con varios cortes (`corte.varios_cortes`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README: PC de 8 núcleos y 8 GB de RAM, unas 5 horas de corrida; Python 3.13, numpy 2.4.3, pandas 3.0.1, pyarrow 25.0.1, duckdb 1.5.5, lightgbm 4.7.0, optuna 4.9.0, scikit-learn 1.9.0. La notebook indica que corre en Google Colab, en una VM de Google Cloud o local. La ruta de Drive (/content/drive/MyDrive/dmeyf/) y /content/ sólo se usan cuando detecta Colab; en los demás casos la base es la carpeta actual o la variable de entorno DMEYF_BASE. El archivo de datos incluido es orden_filas.csv.gz (foto_mes y numero_de_cliente de cada fila); no se incluyen predicciones ni modelos.

## Pasos del camino de la entrega

1. **Entorno y rutas.** Detecta si corre en Google Colab; en ese caso monta Drive y usa /content/drive/MyDrive/dmeyf/ como base, y si no usa la variable de entorno DMEYF_BASE o la carpeta actual. Define las rutas del CSV, del parquet con feature engineering y de orden_filas.csv.gz. (`prediccion_bajas_202108.ipynb` líneas 41–63)
2. **Feature engineering con DuckDB.** Si el parquet no existe, una consulta SQL lee el CSV completo y agrega 3 variables del mes (tc_consumo_total, tc_uso_limite, ratio_transf_emitidas_recibidas), delta_1, delta_2, ratio_media3 y slope_3 para 17 campos, percent_rank dentro del mes para 13 montos, 7 flags de producto que pasa a cero, n_productos_apagados y meses_sin_payroll_3. Escribe competencia_01_fe.parquet ordenado por foto_mes y numero_de_cliente. (`prediccion_bajas_202108.ipynb` líneas 77–162)
3. **Parámetros y semillas.** El diccionario PARAM reúne meses, fracción de submuestreo (0,25), umbral de PSI (0,25), cantidad de canaritos (20), trials (25 de Random Forest y 100 de LightGBM), folds (5), semillas (10 de evaluación y 20 finales) y la grilla de cortes. De la semilla primigenia 14072024 se derivan 50 semillas. (`prediccion_bajas_202108.ipynb` líneas 190–247)
4. **Carga de meses, orden de filas y clase.** Lee del parquet 202103, 202104, 202105, 202106 y 202108 con las columnas float64 pasadas a float32. Si existe orden_filas.csv.gz, reordena las filas según ese archivo. Codifica la clase como 0, 1 y 2 y deja 202108 en -1. (`prediccion_bajas_202108.ipynb` líneas 258–286)
5. **Drift entre 202106 y 202108.** Calcula por variable el PSI entre 202106 y 202108 y la diferencia de porcentaje de nulos, guarda la tabla en drift_jun_ago.csv y excluye las variables con PSI mayor a 0,25 o diferencia de nulos mayor a 20 puntos porcentuales. (`prediccion_bajas_202108.ipynb` líneas 298–334)
6. **Préstamos personales de 202106 a NaN.** En las filas de 202106 pasa a NaN todas las columnas cuyo nombre contiene 'prestamos_personales'. Se hace después del cálculo de drift. (`prediccion_bajas_202108.ipynb` líneas 337–342)
7. **Funciones de ganancia, submuestreo y conjuntos.** Define la curva de ganancia acumulada, su versión suavizada con media móvil de 401 posiciones, el submuestreo de CONTINUA, la etiqueta binaria, el Dataset de LightGBM con la clase codificada en el peso y la métrica feval_ganancia. Arma d_optim (202103-202104 con 25% de CONTINUA) y d_hold (202106 completo). (`prediccion_bajas_202108.ipynb` líneas 356–405)
8. **Canaritos.** Agrega 20 variables al azar, entrena un LightGBM de 200 árboles sobre d_optim y descarta las variables con importancia por gain menor o igual a la del canarito de mayor importancia. (`prediccion_bajas_202108.ipynb` líneas 417–441)
9. **Random Forest como línea de base.** Optimiza con Optuna (25 trials, validación cruzada de 3 folds, 100 árboles) un Random Forest sobre d_optim, lo reentrena con 500 árboles y calcula su curva de ganancia en 202106. Su ganancia máxima se usa como referencia en los gráficos y en el registro; no interviene en la predicción de 202108. (`prediccion_bajas_202108.ipynb` líneas 452–494)
10. **Optimización bayesiana de LightGBM.** Estudio de Optuna con TPESampler y 100 trials: cada trial sortea 7 hiperparámetros y corre lgb.cv con 5 folds estratificados sobre d_optim, hasta 3.000 árboles, early stopping de 100 rondas y la ganancia suavizada como métrica. Guarda la cantidad de árboles de cada trial. (`prediccion_bajas_202108.ipynb` líneas 507–558)
11. **Evaluación de 5 trials con 10 semillas en 202106.** Entrena los 5 trials de mayor ganancia de CV con 10 semillas cada uno sobre 202103-202104, predice 202106 y registra la ganancia en cada corte de 4.000 a 20.000. Elige el trial de mayor ganancia media entre semillas. (`prediccion_bajas_202108.ipynb` líneas 580–613)
12. **Cantidad de envíos.** Para el trial elegido toma el corte de mayor ganancia media en 202106 y lo convierte en cantidad de envíos para 202108 manteniendo la proporción sobre la cantidad de clientes del mes. (`prediccion_bajas_202108.ipynb` líneas 643–667)
13. **Modelo final con 20 semillas.** Entrena en 202103-202106, con 25% de CONTINUA, 20 modelos LightGBM con los hiperparámetros del trial elegido, min_data_in_leaf escalado por la cantidad de filas y max_bin 255, y promedia sus probabilidades sobre 202108. (`prediccion_bajas_202108.ipynb` líneas 680–701)
14. **Archivo de entrega y registro.** Guarda las probabilidades de todos los clientes de 202108, escribe el CSV de entrega con los n_envios de mayor probabilidad (sin encabezado) y un registro.json con los parámetros y los valores elegidos en la corrida. (`prediccion_bajas_202108.ipynb` líneas 704–741)

## Archivos

- `README.md` · explicacion · Markdown · 105 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/montagnaflor/README.md.txt) — Presenta la entrega: resultado declarado, pasos para replicarla, versiones de los paquetes, el motivo del archivo orden_filas.csv.gz, la metodología en diez puntos, una tabla con todos los experimentos (v1 a v9 y variantes) y conclusiones.
- `prediccion_bajas_202108.ipynb` · principal · Jupyter (python) · 741 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/montagnaflor/prediccion_bajas_202108.ipynb.txt) — Notebook de Python con todo el recorrido: feature engineering con DuckDB, análisis de drift, canaritos, Random Forest de línea de base, optimización de LightGBM con Optuna, evaluación en 202106, elección del corte, modelo final de 20 semillas y escritura del archivo de entrega. No trae salidas guardadas.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### prediccion_bajas_202108.ipynb

Notebook de Python con todo el recorrido: feature engineering con DuckDB, análisis de drift, canaritos, Random Forest de línea de base, optimización de LightGBM con Optuna, evaluación en 202106, elección del corte, modelo final de 20 semillas y escritura del archivo de entrega. No trae salidas guardadas.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–28] Celda de texto de presentación: enuncia el objetivo (lista de numero_de_cliente
#   para la campaña, con 1.072.500 por cada BAJA+2 contactado y un costo de 27.500 por cada envío que no lo es),
#   una tabla con el uso de cada mes (202103-202106 con clase completa, 202107 sin usar, 202108 a predecir) y
#   los nueve puntos de la estrategia que desarrolla el resto de la notebook.
#%% celda 1 [texto]
# Predicción de bajas — Agosto 2021 (202108)

**Objetivo:** entregar el listado de `numero_de_cliente` a los que se les envía la campaña de retención.
Cada BAJA+2 contactado suma **$1.072.500** y cada envío que no es BAJA+2 cuesta **$27.500**.

**Situación de los datos** (`competencia_01`):

| foto_mes | clase | uso |
|---|---|---|
| 202103 – 202106 | completa | entrenamiento / validación |
| 202107 | incompleta (los BAJA+2 todavía no se conocen) | **no se usa** |
| 202108 | desconocida | mes a predecir |

Entre el último mes con clase (junio) y agosto hay **2 meses**. Toda la validación imita esa distancia:
optimizo con **marzo–abril** y mido en **junio**, que funciona como *holdout* y nunca entra en la optimización.

**Estrategia contra el overfitting**
1. Ganancia (no AUC) como métrica, suavizada para no premiar picos de suerte.
2. Optimización bayesiana (Optuna) con cross validation sobre marzo–abril.
3. Canaritos para descartar variables que no le ganan al ruido.
4. Drifting: se excluyen variables cuya distribución en agosto cambió mucho respecto de junio.
5. *Maldición del ganador*: no me quedo con el trial #1; evalúo el top-k con muchas semillas en junio y elijo por media y estabilidad.
6. Corte por **cantidad de envíos**, no por probabilidad.
7. Modelo final = promedio de varias semillas (semillerío).
8. **Datos anómalos**: en junio los BAJA+2 tienen préstamos personales igual que los CONTINUA (22%, contra 8-12% en marzo-mayo); esas variables se ponen en NaN solo en junio, después del análisis de drift.
9. `max_bin = 255` en el modelo final (31 en la optimización, por velocidad).

# [Anotación · líneas 29–64] Detecta si corre en Google Colab. En Colab monta Drive, fija la carpeta base en
#   /content/drive/MyDrive/dmeyf/ e instala optuna y duckdb; fuera de Colab la base es la variable de entorno
#   DMEYF_BASE o la carpeta actual. Define las rutas del CSV de la competencia, del parquet con feature
#   engineering (ambos en data/) y de orden_filas.csv.gz, y crea la carpeta data/ si no existe.
#%% celda 2 [texto]
## 0. Entorno

#%% celda 3 [texto]
La notebook corre igual en **Google Colab**, en una **VM de Google Cloud** o local. Hace falta:

* el dataset original `competencia_01.csv`: local, en `data/` al lado de esta notebook; en Colab, en `MyDrive/dmeyf/data/`.
* `orden_filas.csv.gz` (está en el repositorio): local, al lado de esta notebook; en Colab, en `MyDrive/dmeyf/`.

La primera vez se genera `competencia_01_fe.parquet` (sección 1) y queda guardado para las siguientes corridas.
Los resultados (incluida la base de Optuna, para poder retomar si se corta) quedan en `exp/` (en Colab, `MyDrive/dmeyf/exp/`).

#%% celda 4 [código]
import os
import sys
import shutil

EN_COLAB = "google.colab" in sys.modules

if EN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    BASE = "/content/drive/MyDrive/dmeyf/"
    !pip install -q optuna duckdb
else:
    # local o VM: la carpeta del repositorio (data/ y exp/ quedan al lado de esta notebook)
    BASE = os.environ.get("DMEYF_BASE", "./")

CARPETA_DATOS = BASE + "data/"
ARCHIVO_CSV = CARPETA_DATOS + "competencia_01.csv"
ARCHIVO_DATOS = CARPETA_DATOS + "competencia_01_fe.parquet"
# orden de filas de la corrida que generó la entrega final (ver README): el undersampling depende del orden
ARCHIVO_ORDEN = BASE + "orden_filas.csv.gz"
os.makedirs(CARPETA_DATOS, exist_ok=True)
print("Datos:", ARCHIVO_DATOS)

# [Anotación · líneas 65–100] Texto que describe el feature engineering y tres listas de campos:
#   CAMPOS_TENDENCIA (17 campos para deltas, cociente contra la media y pendiente), CAMPOS_RANK (13 montos en
#   pesos para el ranking dentro del mes) y CAMPOS_APAGO (7 contadores de productos para los flags de producto
#   que pasa a cero).
#%% celda 5 [texto]
## 1. Feature engineering: `competencia_01.csv` → `competencia_01_fe.parquet`

#%% celda 6 [texto]
Con funciones de ventana de DuckDB (técnicas del z402), sobre el dataset **completo** (el ranking dentro de cada mes compara al cliente contra toda la cartera de ese mes):

1. **Tendencia contra el propio pasado del cliente**: delta de 1 y 2 meses, ratio contra la media de los últimos 3 meses y pendiente de los últimos 3 meses.
2. **Ranking dentro del mes** de los montos en pesos (contra el drifting por inflación).
3. **"Apagó el producto"**: lo tenía el mes anterior y ahora no; cantidad de productos apagados y meses sin payroll.

Solo se ejecuta si el parquet no existe. El archivo se escribe ordenado por `foto_mes, numero_de_cliente`, porque el undersampling depende del orden de las filas.

#%% celda 7 [código]
import time
import duckdb

CAMPOS_TENDENCIA = [
    "mpayroll", "cpayroll_trx",
    "mtarjeta_visa_consumo", "ctarjeta_visa_transacciones", "mttarjeta_visa_debitos_automaticos",
    "tc_consumo_total",
    "cproductos", "ctrx_quarter", "active_quarter", "internet", "cdescubierto_preacordado",
    "chomebanking_transacciones", "cmobile_app_trx",
    "mcuentas_saldo", "mcaja_ahorro", "mprestamos_personales", "mplazo_fijo_pesos",
]
CAMPOS_RANK = [
    "mpayroll", "mtarjeta_visa_consumo", "mttarjeta_visa_debitos_automaticos", "tc_consumo_total",
    "mcuentas_saldo", "mcaja_ahorro", "mprestamos_personales", "mplazo_fijo_pesos",
    "mrentabilidad", "mcomisiones", "matm", "mtransferencias_emitidas", "mtransferencias_recibidas",
]
CAMPOS_APAGO = [
    "cpayroll_trx", "cdescubierto_preacordado", "ctarjeta_visa_debitos_automaticos",
    "ctarjeta_master_debitos_automaticos", "ccuenta_debitos_automaticos", "cprestamos_personales",
    "cplazo_fijo",
]


# [Anotación · líneas 101–137] query_feature_engineering arma la consulta SQL de DuckDB: una primera etapa lee
#   el CSV completo y agrega un índice de mes (año × 12 + mes), tc_consumo_total (consumo Visa más Master),
#   tc_uso_limite (ese consumo sobre la suma de los límites de compra) y ratio_transf_emitidas_recibidas.
#   Después, por cliente ordenado por foto_mes, calcula para cada campo de tendencia delta_1 y delta_2 (valor
#   menos el de 1 y 2 meses atrás), ratio_media3 (valor sobre el promedio de la ventana de 3 meses que termina
#   en el mes actual) y slope_3 (pendiente de regresión contra el índice de mes en esa ventana); el percent_rank
#   dentro de cada foto_mes de los campos de ranking; un flag_apago por contador (mayor a 0 el mes anterior y 0
#   o nulo en el actual), su suma n_productos_apagados y meses_sin_payroll_3 (meses de la ventana con
#   cpayroll_trx en 0 o nulo). El resultado se escribe en parquet ordenado por foto_mes y numero_de_cliente, sin
#   el índice de mes.
def query_feature_engineering(csv, out):
    sel = []
    for c in CAMPOS_TENDENCIA:
        sel += [
            f"{c} - lag({c}, 1) over w AS delta_1_{c}",
            f"{c} - lag({c}, 2) over w AS delta_2_{c}",
            f"{c} / nullif(avg({c}) over w3, 0) AS ratio_media3_{c}",
            f"regr_slope({c}, mes_idx) over w3 AS slope_3_{c}",
        ]
    for c in CAMPOS_RANK:
        sel.append(f"percent_rank() over (partition by foto_mes order by {c}) AS rank_mes_{c}")
    flags = [f"(coalesce(lag({c}, 1) over w, 0) > 0 AND coalesce({c}, 0) = 0)::INT" for c in CAMPOS_APAGO]
    sel += [f"{f} AS flag_apago_{c}" for c, f in zip(CAMPOS_APAGO, flags)]
    sel.append(" + ".join(flags) + " AS n_productos_apagados")
    sel.append("sum((coalesce(cpayroll_trx, 0) = 0)::INT) over w3 AS meses_sin_payroll_3")
    columnas = ",\n               ".join(sel)
    return f"""
    COPY (
        WITH base AS (
            SELECT *,
                   (foto_mes // 100) * 12 + (foto_mes % 100) AS mes_idx,
                   coalesce(Visa_mconsumototal, 0) + coalesce(Master_mconsumototal, 0) AS tc_consumo_total,
                   tc_consumo_total / nullif(coalesce(Visa_mlimitecompra, 0) + coalesce(Master_mlimitecompra, 0), 0)
                       AS tc_uso_limite,
                   mtransferencias_emitidas / nullif(mtransferencias_recibidas, 0) AS ratio_transf_emitidas_recibidas
            FROM read_csv('{csv}', sample_size = -1)
        )
        SELECT * EXCLUDE (mes_idx),
               {columnas}
        FROM base
        WINDOW w  AS (PARTITION BY numero_de_cliente ORDER BY foto_mes),
               w3 AS (PARTITION BY numero_de_cliente ORDER BY foto_mes ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
        ORDER BY foto_mes, numero_de_cliente
    ) TO '{out}' (FORMAT parquet)
    """


# [Anotación · líneas 138–163] Si el parquet ya existe no lo regenera. Si no, abre DuckDB con límite de
#   memoria de 2 GB, 2 hilos, directorio temporal en data/duckdb_tmp y preserve_insertion_order desactivado,
#   ejecuta la consulta sobre un archivo .tmp y lo renombra al terminar. En Colab copia antes el CSV al disco de
#   la máquina virtual y después el parquet, y lee desde esa copia.
if os.path.exists(ARCHIVO_DATOS):
    print("Ya existe", ARCHIVO_DATOS, "-> no se regenera")
else:
    csv = ARCHIVO_CSV
    if EN_COLAB:
        # leer del disco de la VM es mucho más rápido que leer de Drive
        shutil.copy(ARCHIVO_CSV, "/content/competencia_01.csv")
        csv = "/content/competencia_01.csv"
    t0 = time.time()
    temporal = ARCHIVO_DATOS + ".tmp"  # se renombra al terminar: un corte no deja un parquet incompleto
    con = duckdb.connect()
    # pocos hilos y disco como respaldo: alcanza con ~2 GB de RAM libres
    con.execute("SET memory_limit = '2GB'")
    con.execute("SET threads = 2")
    con.execute(f"SET temp_directory = '{CARPETA_DATOS}duckdb_tmp'")
    con.execute("SET preserve_insertion_order = false")
    con.execute(query_feature_engineering(csv, temporal))
    con.close()
    os.replace(temporal, ARCHIVO_DATOS)
    print(f"Generado {ARCHIVO_DATOS} en {time.time() - t0:.0f}s")

if EN_COLAB:
    # leer del disco de la VM es mucho más rápido que leer de Drive
    shutil.copy(ARCHIVO_DATOS, "/content/competencia_01_fe.parquet")
    ARCHIVO_DATOS = "/content/competencia_01_fe.parquet"

# [Anotación · líneas 164–184] Importa json, warnings, numpy, pandas, pyarrow, matplotlib, lightgbm, optuna y,
#   de scikit-learn, RandomForestClassifier y StratifiedKFold. Baja el nivel de mensajes de Optuna a WARNING,
#   silencia un aviso repetido de sklearn e imprime las versiones de lightgbm y optuna.
#%% celda 8 [código]
import json
import warnings
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import matplotlib.pyplot as plt

import lightgbm as lgb
import optuna
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold

optuna.logging.set_verbosity(optuna.logging.WARNING)
# aviso inofensivo de sklearn que el Random Forest repite miles de veces
warnings.filterwarnings("ignore", message=".*sklearn.utils.parallel.delayed.*")
print("lightgbm", lgb.__version__, "| optuna", optuna.__version__)

# [Anotación · líneas 185–238] Diccionario PARAM con los parámetros de la corrida: semilla primigenia
#   14072024; meses de optimización 202103 y 202104, holdout 202106, meses del modelo final 202103 a 202106 y
#   mes a predecir 202108; positivos BAJA+1 y BAJA+2; undersampling 0,25; PSI máximo 0,25; variables con
#   'prestamos_personales' a anular en 202106; 20 canaritos; Random Forest con 25 trials, 100 árboles en la
#   búsqueda y 500 en el ajuste final; LightGBM con 100 trials, 5 folds, hasta 3.000 árboles, early stopping de
#   100 y max_bin final 255; top_k 5, 10 semillas de evaluación, 20 semillas finales y cortes de 4.000 a 20.000
#   de a 500.
#%% celda 9 [texto]
### Parámetros del experimento
Todo lo que se puede tocar está acá. **Cambiar `semilla_primigenia` por la propia.**

#%% celda 10 [código]
PARAM = {
    "experimento": "final_202108",
    "semilla_primigenia": 14072024,        # <-- CAMBIAR por tu semilla

    # ventanas temporales (todas respetan los 2 meses de distancia)
    "meses_optim": [202103, 202104],       # donde se optimizan hiperparámetros
    "mes_holdout": 202106,                 # validación final, nunca entra en la BO
    "meses_final": [202103, 202104, 202105, 202106],
    "mes_futuro": 202108,

    # target: entrenar con BAJA+1 y BAJA+2 como positivos (z601), medir ganancia solo con BAJA+2
    "positivos": ["BAJA+1", "BAJA+2"],

    # fracción de CONTINUA que se conserva (acelera mucho; la ganancia se corrige por este factor)
    "undersampling": 0.25,

    # drifting
    "psi_max": 0.25,                       # PSI junio vs agosto por encima de esto -> se excluye
    "excluir_manual": [],                  # variables a sacar a mano
    # Variables que se ponen en NaN en un mes puntual con datos anómalos (se aplica después del drift).
    # En junio los BAJA+2 tienen préstamos personales como los CONTINUA (22%), cuando en mar-may tienen 8-12%.
    "anular_en_mes": {202106: ["prestamos_personales"]},

    # canaritos
    "usar_canaritos": True,
    "n_canaritos": 20,

    # Random Forest
    "rf_trials": 25,
    "rf_arboles_bo": 100,
    "rf_arboles_final": 500,

    # LightGBM
    "lgbm_trials": 100,
    "nfold": 5,
    "max_arboles": 3000,
    # max_bin del modelo final: la BO y la evaluación en junio usan 31 (rápido); el modelo final usa 255
    # (más detalle en los montos: +1,8M en junio y mejor en el público).
    "max_bin_final": 255,
    "early_stopping": 100,

    # maldición del ganador y semillerío
    "top_k": 5,
    "n_semillas_eval": 10,                 # semillas por trial en junio (20 si hay tiempo)
    "n_semillas_final": 20,
    "cortes": list(range(4000, 20001, 500)),
    "trial_elegido": None,                 # None = automático; o un número de trial para forzarlo
}

# [Anotación · líneas 239–248] Fija la ganancia por acierto (1.072.500) y el costo por envío (27.500), crea la
#   carpeta de salida exp/final_202108/ y genera la lista SEMILLAS: 50 enteros distintos entre 100.000 y 999.999
#   sorteados con numpy default_rng a partir de la semilla primigenia.
GANANCIA_ACIERTO = 1_072_500
COSTO_ESTIMULO = 27_500

CARPETA_EXP = BASE + "exp/" + PARAM["experimento"] + "/"
os.makedirs(CARPETA_EXP, exist_ok=True)

rng = np.random.default_rng(PARAM["semilla_primigenia"])
SEMILLAS = rng.choice(np.arange(100_000, 1_000_000), size=50, replace=False).tolist()
print("Carpeta del experimento:", CARPETA_EXP)

# [Anotación · líneas 249–267] Lee del parquet sólo los meses 202103, 202104, 202105, 202106 y 202108,
#   convierte las columnas float64 a float32 antes y después de pasar a pandas y libera la tabla de pyarrow.
#%% celda 11 [texto]
## 2. Datos

#%% celda 12 [texto]
Se cargan solo los meses necesarios y los `float64` pasan a `float32` (mitad de memoria).
La clase se codifica como 0 = CONTINUA, 1 = BAJA+1, 2 = BAJA+2. Agosto queda en -1 porque su clase es desconocida
(en el archivo figura como CONTINUA, pero eso es un artefacto de cómo se construyó el target).

#%% celda 13 [código]
meses_cargar = sorted(set(PARAM["meses_final"] + [PARAM["mes_futuro"]]))
tabla = pq.read_table(ARCHIVO_DATOS, filters=[("foto_mes", "in", meses_cargar)])
# float64 -> float32 antes de pasar a pandas: mismo resultado, mitad de memoria en el pico
tabla = tabla.cast(pa.schema([pa.field(f.name, pa.float32() if f.type == pa.float64() else f.type) for f in tabla.schema]))
data = tabla.to_pandas()
del tabla
# las enteras con nulos llegan a pandas como float64: también a float32
cols_f64 = data.select_dtypes("float64").columns
data = data.astype({c: "float32" for c in cols_f64})

# [Anotación · líneas 268–279] Si existe orden_filas.csv.gz, lo lee, se queda con los meses cargados y
#   reordena las filas del DataFrame para que queden en el orden de ese archivo, identificando cada fila por
#   foto_mes y numero_de_cliente. Un assert verifica que todas las filas del archivo estén en los datos y que la
#   cantidad coincida.
# Se aplica el orden de filas de la corrida original. El parquet de esa corrida se generó sin orden fijo
# (DuckDB en paralelo) y el undersampling sortea los CONTINUA según el orden de las filas: con este
# archivo (solo foto_mes y numero_de_cliente, sin información de la clase) se replica la misma muestra.
if os.path.exists(ARCHIVO_ORDEN):
    orden = pd.read_csv(ARCHIVO_ORDEN)
    orden = orden[orden["foto_mes"].isin(meses_cargar)]
    posiciones = pd.MultiIndex.from_frame(data[["foto_mes", "numero_de_cliente"]]).get_indexer(
        pd.MultiIndex.from_frame(orden))
    assert len(posiciones) == len(data) and (posiciones >= 0).all(), "el archivo de orden no coincide con los datos"
    data = data.iloc[posiciones].reset_index(drop=True)
    print("Orden de filas aplicado desde", ARCHIVO_ORDEN)

# [Anotación · líneas 280–287] Crea la columna clase con 0 para CONTINUA, 1 para BAJA+1 y 2 para BAJA+2, y le
#   asigna -1 a las filas de 202108. Define los códigos positivos (1 y 2), imprime el tamaño del DataFrame y
#   muestra la tabla de foto_mes por clase_ternaria.
data["clase"] = data["clase_ternaria"].map({"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}).astype("int8")
data.loc[data["foto_mes"] == PARAM["mes_futuro"], "clase"] = -1

CODIGOS_POSITIVOS = [{"BAJA+1": 1, "BAJA+2": 2}[c] for c in PARAM["positivos"]]

print(f"{data.shape[0]:,} filas x {data.shape[1]} columnas, {data.memory_usage().sum() / 1e9:.2f} GB")
pd.crosstab(data["foto_mes"], data["clase_ternaria"])

# [Anotación · líneas 288–310] Función psi: calcula el Population Stability Index entre una serie de
#   referencia y una actual, con 10 intervalos definidos por los cuantiles de los valores no nulos de la
#   referencia, extremos abiertos a infinito y un intervalo adicional para los nulos. Las proporciones tienen un
#   piso de 0,0001 y devuelve 0 si la referencia tiene un único valor.
#%% celda 14 [texto]
## 3. Drifting y calidad de datos: junio vs agosto

#%% celda 15 [texto]
Como en z701: PSI por variable y cambio en el porcentaje de nulos, comparando el último mes con clase (junio)
contra el mes a predecir (agosto). Si una variable cambió mucho, lo que el modelo aprendió de ella no aplica en agosto.

Referencia usual del PSI: < 0.1 estable, 0.1–0.25 moderado, > 0.25 drift fuerte.

#%% celda 16 [código]
def psi(referencia, actual, buckets=10, eps=1e-4):
    ref_nn, act_nn = referencia.dropna(), actual.dropna()
    if ref_nn.nunique() <= 1:
        return 0.0
    cortes = np.unique(np.quantile(ref_nn, np.linspace(0, 1, buckets + 1)))
    cortes = np.concatenate([[-np.inf], cortes[1:-1], [np.inf]])
    # el último bin son los nulos
    e = np.append(np.histogram(ref_nn, cortes)[0], referencia.isna().sum()) / len(referencia)
    a = np.append(np.histogram(act_nn, cortes)[0], actual.isna().sum()) / len(actual)
    e, a = np.maximum(e, eps), np.maximum(a, eps)
    return float(np.sum((a - e) * np.log(a / e)))


# [Anotación · líneas 311–328] Define las variables candidatas (todas las columnas menos numero_de_cliente,
#   foto_mes, clase_ternaria y clase) y arma una tabla por variable con el PSI entre 202106 y 202108, el
#   porcentaje de nulos en cada uno de los dos meses y su diferencia en puntos porcentuales. La ordena por PSI
#   descendente, la guarda en drift_jun_ago.csv y muestra las 25 primeras.
NO_FEATURES = ["numero_de_cliente", "foto_mes", "clase_ternaria", "clase"]
campos = [c for c in data.columns if c not in NO_FEATURES]

ref = data[data["foto_mes"] == PARAM["mes_holdout"]]
act = data[data["foto_mes"] == PARAM["mes_futuro"]]

tb_drift = pd.DataFrame({
    "psi": [psi(ref[c], act[c]) for c in campos],
    "nulos_jun_%": [100 * ref[c].isna().mean() for c in campos],
    "nulos_ago_%": [100 * act[c].isna().mean() for c in campos],
}, index=campos)
tb_drift["dif_nulos_pp"] = tb_drift["nulos_ago_%"] - tb_drift["nulos_jun_%"]
tb_drift = tb_drift.sort_values("psi", ascending=False)
del ref, act

tb_drift.to_csv(CARPETA_EXP + "drift_jun_ago.csv")
tb_drift.head(25).round(3)

# [Anotación · líneas 329–343] Marca para excluir las variables con PSI mayor a 0,25 o con diferencia de nulos
#   mayor a 20 puntos porcentuales en valor absoluto, y arma campos_buenos sin ellas ni las de excluir_manual
#   (lista vacía). Después pasa a NaN, sólo en las filas de 202106, todas las columnas cuyo nombre contiene
#   'prestamos_personales', convirtiéndolas antes a float32.
#%% celda 17 [código]
excluir_drift = tb_drift.index[(tb_drift["psi"] > PARAM["psi_max"]) | (tb_drift["dif_nulos_pp"].abs() > 20)].tolist()
print("Excluidas por drift:", excluir_drift)

campos_buenos = [c for c in campos if c not in excluir_drift + PARAM["excluir_manual"]]
print(f"Quedan {len(campos_buenos)} variables")

#%% celda 18 [código]
# anulación por mes: después del drift, para que estas variables no queden excluidas por tener 100% de nulos en ese mes
for mes, patrones in PARAM.get("anular_en_mes", {}).items():
    cols = [c for c in campos if any(p in c for p in patrones)]
    data[cols] = data[cols].astype("float32")  # las enteras no admiten NaN
    data.loc[data["foto_mes"] == int(mes), cols] = np.nan
    print(f"{mes}: {len(cols)} variables en NaN ->", cols)

# [Anotación · líneas 344–370] curva_ganancia ordena las filas por probabilidad descendente y acumula
#   1.072.500 por cada BAJA+2 y -27.500 por cada una de las demás, multiplicando el costo de los CONTINUA por
#   peso_neg. ganancia_suavizada aplica a esa curva acumulada una media móvil de 401 posiciones y devuelve su
#   máximo.
#%% celda 19 [texto]
## 4. Funciones de ganancia y de armado de datasets

#%% celda 20 [texto]
* **Ganancia suavizada**: ordeno por probabilidad, acumulo la ganancia y tomo el máximo de la *media móvil* de esa curva.
  El máximo crudo premia picos de suerte; la versión suavizada es la que conviene optimizar.
* **Undersampling**: si me quedo con el 25% de los CONTINUA, cada CONTINUA de validación "pesa" 4 envíos perdidos,
  así la ganancia sigue siendo comparable con la del mes completo.
* **Truco del peso**: LightGBM solo le pasa a la métrica `label` y `weight`. Como entreno con BAJA+1 y BAJA+2 como
  positivos, codifico la clase ternaria en el peso (`1 + 0.00001 * clase`), lo que prácticamente no altera el entrenamiento.

#%% celda 21 [código]
def curva_ganancia(y_pred, clase, peso_neg=1.0):
    # ganancia acumulada al enviar a los N clientes de mayor probabilidad, para N = 1..len
    orden = np.argsort(-y_pred, kind="stable")
    c = clase[orden]
    g = np.where(c == 2, GANANCIA_ACIERTO, -COSTO_ESTIMULO * np.where(c == 0, peso_neg, 1.0))
    return np.cumsum(g)


def ganancia_suavizada(y_pred, clase, peso_neg=1.0, ventana=401):
    acum = curva_ganancia(y_pred, clase, peso_neg)
    if len(acum) > ventana:
        acum = np.convolve(acum, np.ones(ventana) / ventana, mode="valid")
    return acum.max()


# [Anotación · líneas 371–388] submuestrear conserva todas las filas con clase 1 o 2 y las CONTINUA cuyo
#   número uniforme al azar, sorteado por posición de fila con la semilla recibida, es menor a la fracción
#   pedida. etiqueta devuelve 1 para las clases positivas y 0 para el resto. dataset_lgb arma el Dataset de
#   LightGBM con esa etiqueta y un peso de 1 + 0,00001 × clase, que lleva la clase ternaria hasta la función de
#   métrica.
def submuestrear(df, frac, semilla):
    # conserva todas las bajas y una fracción de los CONTINUA
    azar = np.random.default_rng(semilla).random(len(df))
    return df[(df["clase"] > 0) | (azar < frac)]


def etiqueta(df):
    return df["clase"].isin(CODIGOS_POSITIVOS).astype("int8").values


def dataset_lgb(df, campos):
    return lgb.Dataset(
        df[campos], label=etiqueta(df),
        weight=1 + 1e-5 * df["clase"].values,
        free_raw_data=False,
    )


# [Anotación · líneas 389–406] Fija PESO_NEG = 1/0,25 = 4 y la cantidad de meses de optimización (2).
#   feval_ganancia recupera la clase ternaria desde el peso, calcula la ganancia suavizada con el costo de los
#   CONTINUA multiplicado por 4 y la lleva a escala mensual multiplicando por 5 folds y dividiendo por 2 meses.
#   Arma d_optim (202103 y 202104 submuestreados al 25% con SEMILLAS[0]) y d_hold (202106 completo).
PESO_NEG = 1 / PARAM["undersampling"]
N_MESES_OPTIM = len(PARAM["meses_optim"])


def feval_ganancia(y_pred, dataset):
    clase = np.rint((dataset.get_weight() - 1) * 1e5).astype(int)
    # x nfold: cada fold de validación es 1/nfold de los datos; / meses: ganancia por mes
    gan = ganancia_suavizada(y_pred, clase, PESO_NEG) * PARAM["nfold"] / N_MESES_OPTIM
    return "ganancia", gan, True


d_optim = submuestrear(data[data["foto_mes"].isin(PARAM["meses_optim"])], PARAM["undersampling"], SEMILLAS[0])
d_hold = data[data["foto_mes"] == PARAM["mes_holdout"]]
clase_hold = d_hold["clase"].values

print(f"Optimización: {len(d_optim):,} filas (undersampling {PARAM['undersampling']})")
print(f"Holdout {PARAM['mes_holdout']}: {len(d_hold):,} filas, {int((clase_hold == 2).sum())} BAJA+2")

# [Anotación · líneas 407–442] Canaritos: agrega 20 columnas de números uniformes al azar (SEMILLAS[1]) a las
#   variables de d_optim y entrena un LightGBM binario de 200 árboles con learning_rate 0,05, num_leaves 16,
#   min_data_in_leaf 1.000, feature_fraction 0,5 y max_bin 31. Calcula la importancia por gain, toma como umbral
#   la del canarito de mayor importancia y quita de campos_buenos las variables con importancia menor o igual;
#   guarda las importancias en importancia_canaritos.csv.
#%% celda 22 [texto]
## 5. Canaritos: ¿qué variables le ganan al ruido?

#%% celda 23 [texto]
Agrego variables de ruido puro (como en z401) y entreno un LightGBM *regularizado* (si es muy permisivo,
sobreajusta y el ruido termina con mucha importancia).
Toda variable con menos importancia que el mejor canarito no aporta más que el azar y se descarta.
Si descarta demasiadas, revisar la lista o poner `usar_canaritos = False`.

#%% celda 24 [código]
if PARAM["usar_canaritos"]:
    rng_c = np.random.default_rng(SEMILLAS[1])
    canaritos = [f"canarito_{i}" for i in range(PARAM["n_canaritos"])]
    ruido = pd.DataFrame(rng_c.random((len(d_optim), len(canaritos)), dtype="float32"),
                         columns=canaritos, index=d_optim.index)
    X_c = pd.concat([d_optim[campos_buenos], ruido], axis=1)

    params_canaritos = {
        "objective": "binary", "verbosity": -1, "seed": SEMILLAS[1],
        "learning_rate": 0.05, "num_leaves": 16, "min_data_in_leaf": 1000,
        "feature_fraction": 0.5, "max_bin": 31,
    }
    m_c = lgb.train(params_canaritos, lgb.Dataset(X_c, label=etiqueta(d_optim)), num_boost_round=200)

    imp = pd.Series(m_c.feature_importance("gain"), index=X_c.columns).sort_values(ascending=False)
    umbral = imp[canaritos].max()
    descartadas = [c for c in campos_buenos if imp[c] <= umbral]
    print(f"Mejor canarito en el puesto {imp.index.get_loc(imp[canaritos].idxmax()) + 1} de {len(imp)}")
    print(f"Descartadas por canaritos ({len(descartadas)}):", descartadas)

    campos_buenos = [c for c in campos_buenos if c not in descartadas]
    imp.to_csv(CARPETA_EXP + "importancia_canaritos.csv")
    del X_c, m_c

print(f"Variables finales: {len(campos_buenos)}")

# [Anotación · líneas 443–485] Random Forest de scikit-learn sobre d_optim con los nulos reemplazados por
#   -999. Un estudio de Optuna (TPE con SEMILLAS[4], guardado en optuna.db) busca max_depth entre 4 y 30,
#   min_samples_leaf entre 1 y 1.000, max_features entre 0,05 y 0,7 y max_samples entre 0,3 y 1,0, con 100
#   árboles y validación cruzada estratificada de 3 folds; el objetivo es la ganancia suavizada media de los
#   folds llevada a escala mensual. Ejecuta los trials que falten hasta 25.
#%% celda 25 [texto]
## 6. Random Forest: línea base

#%% celda 26 [texto]
Optimización bayesiana con 3-fold CV estratificado sobre marzo–abril, con pocos árboles para que sea rápida (z401).
Luego entreno el mejor con más árboles y mido en junio. Es el piso que LightGBM tiene que superar.
Random Forest de sklearn no acepta nulos en todas las versiones: los imputo con -999.

#%% celda 27 [código]
X_rf = d_optim[campos_buenos].fillna(-999).values
y_rf = etiqueta(d_optim)
clase_rf = d_optim["clase"].values


def objetivo_rf(trial):
    params = {
        "max_depth": trial.suggest_int("max_depth", 4, 30),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 1000, log=True),
        "max_features": trial.suggest_float("max_features", 0.05, 0.7),
        "max_samples": trial.suggest_float("max_samples", 0.3, 1.0),
    }
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEMILLAS[2])
    ganancias = []
    for tr, te in skf.split(X_rf, clase_rf):
        rf = RandomForestClassifier(n_estimators=PARAM["rf_arboles_bo"], n_jobs=-1,
                                    random_state=SEMILLAS[3], **params)
        rf.fit(X_rf[tr], y_rf[tr])
        pred = rf.predict_proba(X_rf[te])[:, 1]
        ganancias.append(ganancia_suavizada(pred, clase_rf[te], PESO_NEG))
    return np.mean(ganancias) * 3 / N_MESES_OPTIM


estudio_rf = optuna.create_study(
    study_name="rf", direction="maximize",
    storage=f"sqlite:///{CARPETA_EXP}optuna.db", load_if_exists=True,
    sampler=optuna.samplers.TPESampler(seed=SEMILLAS[4]),
)
faltan = PARAM["rf_trials"] - len(estudio_rf.trials)
t0 = time.time()
if faltan > 0:
    estudio_rf.optimize(objetivo_rf, n_trials=faltan)
print(f"{time.time() - t0:.0f}s | mejor ganancia CV: {estudio_rf.best_value:,.0f}", estudio_rf.best_params)

# [Anotación · líneas 486–495] Entrena un Random Forest de 500 árboles con los parámetros de mayor ganancia
#   del estudio, predice 202106 e imprime la ganancia máxima de la curva y la cantidad de envíos donde se
#   alcanza. Ese valor se usa después como referencia en los gráficos y en el registro.
#%% celda 28 [código]
rf = RandomForestClassifier(n_estimators=PARAM["rf_arboles_final"], n_jobs=-1,
                            random_state=SEMILLAS[3], **estudio_rf.best_params)
rf.fit(X_rf, y_rf)
pred_rf_hold = rf.predict_proba(d_hold[campos_buenos].fillna(-999).values)[:, 1]
curva_rf = curva_ganancia(pred_rf_hold, clase_hold)

print(f"RF en {PARAM['mes_holdout']}: ganancia máxima {curva_rf.max():,.0f} enviando a {curva_rf.argmax() + 1:,}")
del rf, X_rf

# [Anotación · líneas 496–522] PARAMS_FIJOS define los parámetros de LightGBM que no se optimizan: objective
#   binary, sin métrica interna, boosting gbdt, boost_from_average, feature_pre_filter desactivado, max_bin 31 y
#   bagging_freq 1. armar_params une esos parámetros con los hiperparámetros de un trial y una semilla.
#%% celda 29 [texto]
## 7. LightGBM: optimización bayesiana

#%% celda 30 [texto]
Cross validation de 5 folds sobre marzo–abril, métrica = ganancia suavizada por mes, *early stopping* para
elegir la cantidad de árboles. Los rangos empujan hacia modelos que generalizan:
`min_data_in_leaf` alto, `feature_fraction` y `bagging_fraction` < 1, regularización L1/L2.

La base de Optuna se guarda en disco: **si Colab se desconecta, al volver a correr la celda retoma donde quedó.**

#%% celda 31 [código]
PARAMS_FIJOS = {
    "objective": "binary",
    "metric": "None",                # la única métrica es la ganancia
    "boosting_type": "gbdt",
    "boost_from_average": True,
    "feature_pre_filter": False,
    "max_bin": 31,
    "bagging_freq": 1,
    "verbosity": -1,
}


def armar_params(hp, semilla):
    return {**PARAMS_FIJOS, **hp, "seed": semilla}


# [Anotación · líneas 523–547] Arma el Dataset de optimización con d_optim y las variables seleccionadas.
#   objetivo_lgbm sortea learning_rate (0,01 a 0,3), num_leaves (8 a 256), min_data_in_leaf (50 a 5.000),
#   feature_fraction (0,1 a 1), bagging_fraction (0,5 a 1), lambda_l1 y lambda_l2 (0,001 a 10) y corre lgb.cv
#   con 5 folds estratificados, hasta 3.000 árboles, feval_ganancia como métrica y early stopping de 100 rondas.
#   Guarda en el trial el largo de la serie de ganancia media (best_iter) y devuelve su último valor.
dtrain_optim = dataset_lgb(d_optim, campos_buenos)


def objetivo_lgbm(trial):
    hp = {
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 8, 256, log=True),
        "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 50, 5000, log=True),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.1, 1.0),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.5, 1.0),
        "lambda_l1": trial.suggest_float("lambda_l1", 1e-3, 10, log=True),
        "lambda_l2": trial.suggest_float("lambda_l2", 1e-3, 10, log=True),
    }
    cv = lgb.cv(
        armar_params(hp, SEMILLAS[5]), dtrain_optim,
        num_boost_round=PARAM["max_arboles"],
        nfold=PARAM["nfold"], stratified=True, seed=SEMILLAS[6],
        feval=feval_ganancia,
        callbacks=[lgb.early_stopping(PARAM["early_stopping"], verbose=False)],
    )
    clave = [k for k in cv if k.endswith("ganancia-mean")][0]
    trial.set_user_attr("best_iter", len(cv[clave]))
    return cv[clave][-1]


# [Anotación · líneas 548–568] Crea o retoma el estudio 'lgbm' de Optuna (maximizar, TPESampler con
#   SEMILLAS[7], almacenado en optuna.db) y ejecuta los trials que falten hasta 100. Imprime la ganancia de CV
#   más alta, sus hiperparámetros y su cantidad de árboles, y muestra tres gráficos de Optuna: historia de la
#   optimización, importancia de los hiperparámetros y gráfico de slice por hiperparámetro.
estudio_lgbm = optuna.create_study(
    study_name="lgbm", direction="maximize",
    storage=f"sqlite:///{CARPETA_EXP}optuna.db", load_if_exists=True,
    sampler=optuna.samplers.TPESampler(seed=SEMILLAS[7]),
)
faltan = PARAM["lgbm_trials"] - len(estudio_lgbm.trials)
t0 = time.time()
if faltan > 0:
    estudio_lgbm.optimize(objetivo_lgbm, n_trials=faltan)
print(f"{time.time() - t0:.0f}s | mejor ganancia CV: {estudio_lgbm.best_value:,.0f}")
print(estudio_lgbm.best_params, "| árboles:", estudio_lgbm.best_trial.user_attrs["best_iter"])

#%% celda 32 [código]
optuna.visualization.plot_optimization_history(estudio_lgbm)

#%% celda 33 [código]
optuna.visualization.plot_param_importances(estudio_lgbm)

#%% celda 34 [código]
optuna.visualization.plot_slice(estudio_lgbm)

# [Anotación · líneas 569–602] Toma los 5 trials de mayor ganancia de CV y, para cada uno, entrena 10 modelos
#   (SEMILLAS[10] a SEMILLAS[19]) sobre el Dataset de 202103-202104 con los hiperparámetros y la cantidad de
#   árboles del trial. Con cada modelo predice 202106 completo y registra la ganancia en cada corte de la grilla
#   de 4.000 a 20.000; además calcula la curva de ganancia del promedio de las 10 predicciones. Guarda el
#   detalle por trial, semilla y corte en holdout_semillas.csv.
#%% celda 35 [texto]
## 8. Contra la maldición del ganador: top-k trials × semillas en junio

#%% celda 36 [texto]
El mejor trial de la BO es, en parte, el que tuvo más suerte (z0333). Tomo los `top_k` mejores, los entreno
en marzo–abril con `n_semillas_eval` semillas distintas y mido la ganancia en junio, que la BO nunca vio.
Me quedo con el de **mejor ganancia media**, mirando también que su dispersión no sea enorme.

Ojo: como junio se usa para elegir trial y corte, la ganancia de junio que se reporte acá queda un poco optimista.

#%% celda 37 [código]
trials_ok = [t for t in estudio_lgbm.trials if t.value is not None]
top_trials = sorted(trials_ok, key=lambda t: t.value, reverse=True)[:PARAM["top_k"]]
cortes = np.array(PARAM["cortes"])
semillas_eval = SEMILLAS[10:10 + PARAM["n_semillas_eval"]]

filas = []
curvas_ensamble = {}
t0 = time.time()
for t in top_trials:
    suma_pred = np.zeros(len(d_hold))
    for s in semillas_eval:
        modelo = lgb.train(armar_params(t.params, s), dtrain_optim, num_boost_round=t.user_attrs["best_iter"])
        pred = modelo.predict(d_hold[campos_buenos])
        suma_pred += pred
        curva = curva_ganancia(pred, clase_hold)
        for n in cortes:
            filas.append({"trial": t.number, "semilla": s, "corte": n, "ganancia": curva[n - 1]})
    curvas_ensamble[t.number] = curva_ganancia(suma_pred / len(semillas_eval), clase_hold)
    print(f"trial {t.number} listo ({time.time() - t0:.0f}s)")

df_semillas = pd.DataFrame(filas)
df_semillas.to_csv(CARPETA_EXP + "holdout_semillas.csv", index=False)

# [Anotación · líneas 603–614] Calcula la media y el desvío de la ganancia por trial y corte, y para cada
#   trial se queda con el corte de mayor media, junto con su ganancia de CV y la ganancia del promedio de
#   semillas en ese corte. El trial elegido es el de mayor ganancia media en 202106, salvo que
#   PARAM['trial_elegido'] indique un número.
#%% celda 38 [código]
media_por_corte = df_semillas.groupby(["trial", "corte"])["ganancia"].agg(["mean", "std"]).reset_index()
mejor_por_trial = media_por_corte.loc[media_por_corte.groupby("trial")["mean"].idxmax()].set_index("trial")
mejor_por_trial["ganancia_cv"] = [estudio_lgbm.trials[i].value for i in mejor_por_trial.index]
mejor_por_trial["ganancia_ensamble"] = [curvas_ensamble[i][int(n) - 1] for i, n in mejor_por_trial["corte"].items()]
mejor_por_trial = mejor_por_trial.sort_values("mean", ascending=False)

trial_elegido = PARAM["trial_elegido"] if PARAM["trial_elegido"] is not None else int(mejor_por_trial.index[0])
print("Trial elegido:", trial_elegido)
print(f"Random Forest (línea base) en junio: {curva_rf.max():,.0f}")
mejor_por_trial.round(0)

# [Anotación · líneas 615–633] Gráfico de cajas con la distribución de la ganancia en 202106 de las 10
#   semillas de cada trial, en el corte de mayor media de cada uno; la caja del trial elegido va en azul y una
#   línea punteada marca la ganancia del Random Forest.
#%% celda 39 [código]
# distribución de la ganancia en junio por trial, cada uno en su mejor corte
fig, ax = plt.subplots(figsize=(10, 5))
orden_trials = mejor_por_trial.index.tolist()
datos = [df_semillas[(df_semillas["trial"] == t) & (df_semillas["corte"] == mejor_por_trial.loc[t, "corte"])]["ganancia"] / 1e6
         for t in orden_trials]
cajas = ax.boxplot(datos, patch_artist=True, widths=0.5)
for i, caja in enumerate(cajas["boxes"]):
    caja.set_facecolor("#2a78d6" if orden_trials[i] == trial_elegido else "#c9cdd3")
    caja.set_edgecolor("#4a4f57")
ax.set_xticks(range(1, len(orden_trials) + 1), [f"trial {t}" for t in orden_trials])
ax.axhline(curva_rf.max() / 1e6, color="#4a4f57", linestyle="--", linewidth=1)
ax.text(len(orden_trials) + 0.4, curva_rf.max() / 1e6, "Random Forest", va="bottom", ha="right", color="#4a4f57")
ax.set_ylabel("Ganancia en junio (millones)")
ax.set_title(f"Ganancia en {PARAM['mes_holdout']} con {len(semillas_eval)} semillas por trial (azul: elegido)")
ax.grid(axis="y", color="#e6e8eb")
ax.spines[["top", "right"]].set_visible(False)
plt.show()

# [Anotación · líneas 634–663] Para el trial elegido toma el corte de la grilla con mayor ganancia media entre
#   semillas (corte_optimo) y avisa si quedó en un extremo de la grilla. Grafica la ganancia media en 202106
#   según la cantidad de envíos con una banda de ± 1 desvío, la curva del promedio de probabilidades y una línea
#   vertical en el corte.
#%% celda 40 [texto]
## 9. Punto de corte: ¿a cuántos clientes enviar?

#%% celda 41 [texto]
Como en z601, pienso en **cantidad de envíos** y no en probabilidad. Elijo el corte que maximiza la ganancia
*media entre semillas* del trial elegido (más estable que la curva de una sola corrida).
Como agosto tiene otra cantidad de clientes que junio, traslado el corte como **proporción de la cartera**.

#%% celda 42 [código]
curva_media = media_por_corte[media_por_corte["trial"] == trial_elegido].set_index("corte")
corte_optimo = int(curva_media["mean"].idxmax())
if corte_optimo in (cortes.min(), cortes.max()):
    print("ATENCIÓN: el corte óptimo quedó en el borde de la grilla, ampliar PARAM['cortes']")

fig, ax = plt.subplots(figsize=(10, 5))
ax.fill_between(curva_media.index, (curva_media["mean"] - curva_media["std"]) / 1e6,
                (curva_media["mean"] + curva_media["std"]) / 1e6, color="#2a78d6", alpha=0.15, linewidth=0)
ax.plot(curva_media.index, curva_media["mean"] / 1e6, color="#2a78d6", linewidth=2, label="Media entre semillas (± 1 desvío)")
ax.plot(cortes, curvas_ensamble[trial_elegido][cortes - 1] / 1e6, color="#4a4f57", linewidth=2, linestyle="--",
        label="Ensamble (promedio de probabilidades)")
ax.axvline(corte_optimo, color="#4a4f57", linewidth=1)
ax.text(corte_optimo, ax.get_ylim()[0], f"  corte = {corte_optimo:,}", va="bottom", color="#4a4f57")
ax.set_xlabel("Cantidad de envíos")
ax.set_ylabel("Ganancia en junio (millones)")
ax.set_title(f"Trial {trial_elegido}: ganancia en {PARAM['mes_holdout']} según cantidad de envíos")
ax.legend(frameon=False)
ax.grid(axis="y", color="#e6e8eb")
ax.spines[["top", "right"]].set_visible(False)
plt.show()

# [Anotación · líneas 664–668] Convierte el corte en proporción de los clientes de 202106 y la aplica a la
#   cantidad de clientes de 202108, redondeando, para obtener n_envios.
proporcion_envios = corte_optimo / len(d_hold)
n_futuro = int((data["foto_mes"] == PARAM["mes_futuro"]).sum())
n_envios = int(round(proporcion_envios * n_futuro))
print(f"Corte en junio: {corte_optimo:,} ({100 * proporcion_envios:.2f}% de la cartera) -> agosto: {n_envios:,} envíos")

# [Anotación · líneas 669–702] Toma los hiperparámetros y la cantidad de árboles del trial elegido. Arma el
#   conjunto final con 202103 a 202106 submuestreado al 25% con SEMILLAS[0] y multiplica min_data_in_leaf por el
#   cociente entre las filas de ese conjunto y las del de optimización. Entrena 20 modelos (SEMILLAS[30] a
#   SEMILLAS[49]) con max_bin 255, suma sus predicciones sobre 202108 y las divide por 20; guarda el modelo de
#   la última semilla en modelo_final_ultima_semilla.txt.
#%% celda 43 [texto]
## 10. Modelo final y entrega

#%% celda 44 [texto]
Reentreno con **marzo–junio** usando los hiperparámetros del trial elegido, el mismo undersampling,
y promedio las probabilidades de `n_semillas_final` semillas sobre agosto.

Como el dataset final tiene más filas que el de optimización, escalo `min_data_in_leaf` en la misma proporción
para que las hojas representen la misma fracción de los datos. La cantidad de árboles queda igual.

#%% celda 45 [código]
hp_final = dict(estudio_lgbm.trials[trial_elegido].params)
n_arboles = estudio_lgbm.trials[trial_elegido].user_attrs["best_iter"]

d_final = submuestrear(data[data["foto_mes"].isin(PARAM["meses_final"])], PARAM["undersampling"], SEMILLAS[0])
escala = len(d_final) / len(d_optim)
hp_final["min_data_in_leaf"] = int(round(hp_final["min_data_in_leaf"] * escala))
dtrain_final = dataset_lgb(d_final, campos_buenos)

d_futuro = data[data["foto_mes"] == PARAM["mes_futuro"]]
semillas_final = SEMILLAS[30:30 + PARAM["n_semillas_final"]]
suma_pred = np.zeros(len(d_futuro))

t0 = time.time()
for i, s in enumerate(semillas_final, 1):
    modelo = lgb.train({**armar_params(hp_final, s), "max_bin": PARAM["max_bin_final"]}, dtrain_final,
                       num_boost_round=n_arboles)
    suma_pred += modelo.predict(d_futuro[campos_buenos])
    print(f"semilla {i}/{len(semillas_final)} ({time.time() - t0:.0f}s)")

modelo.save_model(CARPETA_EXP + "modelo_final_ultima_semilla.txt")
prob_futuro = suma_pred / len(semillas_final)
print(hp_final, "| árboles:", n_arboles)

# [Anotación · líneas 703–723] Ordena los clientes de 202108 por probabilidad promedio descendente y guarda la
#   tabla completa en probabilidades_202108.csv. Toma los primeros n_envios, busca el número de entrega más alto
#   entre los archivos entrega*.csv de exp/ y escribe entregaNN_202108.csv con el número siguiente, sin
#   encabezado y con la columna numero_de_cliente. Verifica con assert que no haya clientes repetidos y que
#   todos pertenezcan a 202108, e imprime la probabilidad del último cliente incluido.
#%% celda 46 [código]
tb_pred = pd.DataFrame({"numero_de_cliente": d_futuro["numero_de_cliente"].values, "prob": prob_futuro})
tb_pred = tb_pred.sort_values("prob", ascending=False).reset_index(drop=True)
tb_pred.to_csv(CARPETA_EXP + "probabilidades_202108.csv", index=False)

entrega = tb_pred.head(n_envios)[["numero_de_cliente"]]
# numeración correlativa entre todas las corridas de exp/: entrega01_202108.csv, entrega02_202108.csv, ...
import glob, re
patron = re.compile(rf"entrega(\d+)_{PARAM['mes_futuro']}\.csv$")
previas = [int(m.group(1)) for f in glob.glob(BASE + "exp/**/entrega*.csv", recursive=True)
           if (m := patron.search(os.path.basename(f)))]
n_entrega = max(previas, default=0) + 1
archivo_entrega = CARPETA_EXP + f"entrega{n_entrega:02d}_{PARAM['mes_futuro']}.csv"
entrega.to_csv(archivo_entrega, index=False, header=False)  # el formato de entrega va sin encabezado

# controles
assert entrega["numero_de_cliente"].is_unique
assert entrega["numero_de_cliente"].isin(d_futuro["numero_de_cliente"]).all()
print(f"{len(entrega):,} clientes en {archivo_entrega}")
print(f"Probabilidad del último cliente incluido: {tb_pred.loc[n_envios - 1, 'prob']:.4f}")

# [Anotación · líneas 724–741] Escribe registro.json con PARAM, las variables excluidas por drift, la cantidad
#   de variables finales, el trial elegido, los hiperparámetros finales, la cantidad de árboles, el corte en
#   junio, los envíos de agosto, la ruta del archivo de entrega, la ganancia media en junio y la del Random
#   Forest.
#%% celda 47 [código]
# registro del experimento, para poder reproducirlo
registro = {
    "PARAM": PARAM,
    "variables_excluidas_drift": excluir_drift,
    "n_variables": len(campos_buenos),
    "trial_elegido": trial_elegido,
    "hiperparametros_final": hp_final,
    "n_arboles": n_arboles,
    "corte_junio": corte_optimo,
    "n_envios_agosto": n_envios,
    "archivo_entrega": archivo_entrega,
    "ganancia_junio_media": float(curva_media.loc[corte_optimo, "mean"]),
    "ganancia_junio_rf": float(curva_rf.max()),
}
with open(CARPETA_EXP + "registro.json", "w", encoding="utf-8") as f:
    json.dump(registro, f, indent=2, ensure_ascii=False, default=str)
registro
```


## Explicaciones del alumno (texto original)

### README.md

> # Competencia 01 — Predicción de bajas, agosto 2021
>
> DMEyF — Florencia Montagna
>
> Entrega final: 11.036 clientes (ganancia pública **101,12**).
>
> ## Cómo replicar la entrega final
>
> | archivo | qué es |
> |---|---|
> | `prediccion_bajas_202108.ipynb` | Todo el proceso, desde el CSV de la competencia hasta el archivo de entrega |
> | `orden_filas.csv.gz` | Orden de las filas de la corrida original (ver abajo) |
>
> 1. Copiar el dataset de la competencia a `data/competencia_01.csv` (al lado de la notebook).
> 2. Correr la notebook completa (~5 h en una PC de 8 núcleos y 8 GB de RAM). Por ejemplo:
>    ```
>    jupyter nbconvert --to notebook --execute prediccion_bajas_202108.ipynb --output prediccion_bajas_202108_ejecutada.ipynb --ExecutePreprocessor.timeout=-1
>    ```
>    En Google Colab: subir `competencia_01.csv` a `MyDrive/dmeyf/data/` y `orden_filas.csv.gz` a `MyDrive/dmeyf/`.
> 3. La entrega queda en `exp/final_202108/entrega01_202108.csv` y es idéntica al archivo entregado.
>
> Versiones usadas: Python 3.13, numpy 2.4.3, pandas 3.0.1, pyarrow 25.0.1, duckdb 1.5.5, lightgbm 4.7.0,
> optuna 4.9.0, scikit-learn 1.9.0. Semilla primigenia: 14072024.
>
> ### Por qué está `orden_filas.csv.gz`
>
> El undersampling sortea el 25% de los CONTINUA según el orden de las filas del dataset. La entrega final se
> generó con un parquet cuyo orden no era determinístico (DuckDB escribe en paralelo). La notebook genera ahora el
> parquet ordenado por `foto_mes, numero_de_cliente` y, si encuentra `orden_filas.csv.gz`, reordena las filas como
> en la corrida original; así se obtiene exactamente la misma muestra y la misma entrega. El archivo tiene solo
> `foto_mes` y `numero_de_cliente`: no contiene información de la clase. Sin él, la notebook corre igual y produce
> una entrega equivalente (mismo método, otra muestra de CONTINUA).
>
> Verificado: los valores del parquet regenerado desde el CSV son idénticos a los del original, los datos cargados
> con el archivo de orden son idénticos fila por fila a los de la corrida original, y esa corrida, ejecutada desde
> cero (incluida la optimización bayesiana), reproduce la entrega final exacta.
>
> ## Metodología
>
> **Validación con la misma distancia que el problema**: entre el último mes con clase completa (junio) y agosto
> hay 2 meses; 202107 no se usa (sus BAJA+2 no se conocen).
>
> | meses | uso |
> |---|---|
> | 202103–202104 | optimización bayesiana (5-fold) |
> | 202106 | holdout: elección del trial y del corte; nunca entra en la optimización |
> | 202103–202106 | modelo final |
> | 202108 | predicción |
>
> 1. **Feature engineering**: deltas de 1 y 2 meses, ratio contra la media de 3 meses y pendiente del propio cliente;
>    ranking de montos dentro del mes (contra la inflación); flags de "apagó un producto".
> 2. **Target**: BAJA+1 y BAJA+2 como positivos para entrenar; la ganancia se mide solo con BAJA+2.
> 3. **Undersampling** del 25% de los CONTINUA, con la ganancia corregida por ese factor.
> 4. **Drift**: se excluyen variables con PSI > 0,25 entre junio y agosto (9, casi todas tendencias de payroll
>    distorsionadas por el aguinaldo de junio).
> 5. **Datos anómalos**: en junio los BAJA+2 tienen préstamos personales igual que los CONTINUA (22% contra 8–12% en
>    marzo–mayo). Esas variables se ponen en NaN solo en junio. La ganancia en junio pasó de $395M a $449M.
> 6. **Canaritos**: se descartan las variables que no superan al mejor de 20 canaritos (quedan 74).
> 7. **LightGBM** con optimización bayesiana (Optuna, 100 trials), métrica = ganancia suavizada, early stopping.
> 8. **Maldición del ganador**: los 5 mejores trials se evalúan en junio con 10 semillas; se elige por ganancia media
>    (trial 58), no el mejor de la optimización.
> 9. **Corte por cantidad de envíos**, el que maximiza la ganancia media en junio (11.000), trasladado a agosto como
>    proporción de la cartera (11.036).
> 10. **Modelo final**: marzo–junio, `min_data_in_leaf` escalado por la cantidad de filas, promedio de 20 semillas,
>     `max_bin = 255` (31 en la optimización).
>
> ## Todos los experimentos
>
> Junio: ganancia media de 10 semillas en el mejor corte. Público: ganancia en el leaderboard público (25% de agosto),
> en millones. "20 semillas" = 20 modelos de una semilla subidos juntos (media ± desvío).
>
> | versión | cambio | junio | envíos | público |
> |---|---|---|---|---|
> | v1 | base | $395,3M | 12.541 | 94,85 |
> | v1 | 9 cortes de 9.000 a 16.000 | | varios | 93,12 ± 6,02 |
> | v1 | trial 62, 20 semillas | | 12.541 | 93,75 ± 1,69 |
> | v1 | trial 61, 20 semillas | | 12.541 | 91,67 ± 2,24 |
> | v1 | menos envíos | | 11.537 | 98,07 |
> | v2 | sin canaritos (236 variables) | $397,2M | 11.537 | 98,23 |
> | v2 | más envíos | | 12.541 | 95,98 |
> | **v3** | **v1 + préstamos de junio en NaN** | **$449,0M** | 11.036 | **98,86** |
> | v3 | más envíos | | 11.537 | 96,61 |
> | v3 | 20 semillas | | 11.036 | 96,25 ± 2,14 |
> | v4 | v3 + nulos (no 0/1) cuando no hay mes anterior | $435,9M | 11.036 | 94,13 |
> | v5 | v3 con un modelo por mes, ensamblados | $444,1M | 11.036 | 90,97 |
> | v6 | v3 + tendencias de payroll robustas al aguinaldo | $446,9M | 11.036 | 98,78 |
> | v6 | 20 semillas | | 11.036 | 96,68 ± 2,01 |
> | v7 | promedio de rankings v3 + v6 | | 11.036 | 99,14 |
> | **final** | **v3 + `max_bin = 255` en el modelo final** | **$450,8M** | 11.036 | **101,12** |
> | final | 20 semillas | | 11.036 | 96,76 ± 2,09 |
> | v9 | v3 + optimización con validación temporal (marzo → mayo) | $451,4M | 11.036 | 92,32 |
> | — | final + todos los CONTINUA en el modelo final | (+6,4M) | 11.036 | 95,56 |
> | — | ídem, 20 semillas | | 11.036 | 91,53 ± 2,45 |
> | — | misma notebook con otra muestra de CONTINUA (parquet ordenado) | $442,9M | 11.537 | 92,07 |
>
> **Conclusiones**
>
> * Lo que más movió la ganancia: neutralizar los préstamos de junio y el corte (con los mismos modelos, bajar de
>   ~12.500 a ~11.000 envíos sumó 2–3M en el público).
> * Junio predijo bien el efecto de los cambios en datos y variables (v3, v4, v5, `max_bin`), pero no el de los cambios
>   en cómo se entrena el modelo final (v9, todos los CONTINUA): junio evalúa un modelo de marzo–abril, no uno de
>   marzo–junio.
> * El ensamble de 20 semillas suma ~2,5M sobre la semilla promedio.
> * La variabilidad de una corrida completa (otra muestra de CONTINUA) es grande: el mismo método dio 101,12 y 92,07
>   en el público.

