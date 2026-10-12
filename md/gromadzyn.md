# gromadzyn — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: gromadzyn
- Repositorio: https://github.com/gromadzyn/dmeyfCompetencia1
- Link posteado: https://github.com/gromadzyn/dmeyfCompetencia1/
- Commit: ac82cca1ff91ca240fac1037984705dcb1906645
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/gromadzyn/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/gromadzyn.json

## Resumen

La entrega es un repositorio con un notebook de Google Colab en R (entrega1Gromadzyn.ipynb) y un README de dos frases que indica cuál es el archivo entregado. El notebook descarga el dataset crudo, calcula clase_ternaria, pasa ccajas_depositos a NA en 202105, agrega lag 1, lag 2 y sus deltas para cada variable numérica y reemplaza todas las variables numéricas por un ranking calculado dentro de cada mes, con cero fijo, en el rango [-1, 1]. Con clase binaria (positivo = BAJA+1 o BAJA+2) corre una optimización bayesiana de 30 iteraciones con mlrMBO sobre num_iterations, num_leaves y min_sum_hessian_in_leaf, entrenando LightGBM en 202103 y 202104 y maximizando el AUC en 202106. Después entrena 10 modelos LightGBM sobre 202103 a 202106, sin submuestreo, cada uno con una semilla distinta y con una de las 10 configuraciones de mayor AUC de la optimización, promedia sus probabilidades para 202108 y escribe archivos con los primeros 10000, 10500, 11000, 11500 y 12000 clientes. Según el README, el archivo entregado es submit_ensamble10_11000.csv.

**Qué entrega.** Según el README, el archivo submit_ensamble10_11000.csv: un CSV sin encabezado con los 11.000 numero_de_cliente de mayor probabilidad promedio entre 10 modelos. El archivo no está en el repositorio; el notebook lo escribe en Google Drive, en dmeyf/exp/expEntrega1Prueba1/.

**Cómo se ejecuta.** El README no enumera pasos; dice que 'el colab' genera el CSV en Google Drive. Las celdas de texto del notebook indican correrlo en Google Colab: la primera parte (montar Google Drive y descargar el dataset) con runtime Python 3 y, desde la generación de clase_ternaria en adelante, con runtime R. La celda de la optimización bayesiana retoma desde bayesiana.RDATA si ese archivo ya existe en la carpeta del experimento.

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase01): positivo = BAJA+1 o BAJA+2, negativo = CONTINUA. La clase_ternaria se calcula en el mismo notebook a partir del dataset crudo.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No hay submuestreo: se entrena con todos los registros de los meses elegidos, tanto en la optimización como en el entrenamiento final. PARAM$trainingstrategy$undersampling se fija en 1.0 y no se lee en otra celda.
- **Calidad de datos:** ccajas_depositos se pasa a NA en 202105, antes de calcular los lags (una vez al generar la clase y otra vez al leer el dataset en el preprocesamiento).
- **Drifting:** Todas las variables numéricas (originales, lags y deltas) se reemplazan por un ranking calculado por separado dentro de cada foto_mes con cero fijo: los ceros quedan en 0, los negativos pasan al intervalo [-1, 0) y los positivos al intervalo (0, 1]; los NA se conservan.
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** Lag 1, lag 2, delta contra lag 1 y delta contra lag 2 de cada variable numérica original (4 columnas nuevas por variable). El lag queda en NA si la fila anterior no es del mismo cliente o no está a exactamente 1 o 2 meses. Según la salida guardada en el notebook, son 152 variables numéricas y 760 features en total.
- **Selección de variables:** No se observa en el código: el modelo recibe todas las columnas salvo numero_de_cliente, foto_mes, clase_ternaria, clase01, training, azar y fold.
- **Optimización de hiperparámetros:** Optimización bayesiana con mlrMBO (modelo sustituto de kriging con covarianza matern3_2, criterio Expected Improvement), 30 iteraciones, sobre num_iterations [64, 4096], num_leaves [16, 2048] y min_sum_hessian_in_leaf [1e-06, 0.1]. Cada evaluación entrena con 202103 y 202104 y mide el AUC en 202106; se maximiza el AUC.
- **Hiperparámetros finales:** Fijos en el código: boosting gbdt, objective binary, learning_rate 0.005, feature_fraction 0.50, feature_fraction_bynode 0.20, max_bin 31, min_data_in_leaf 0, max_depth -1, lambda_l1 0, lambda_l2 0, min_gain_to_split 0, bagging_fraction 1.0. num_iterations, num_leaves y min_sum_hessian_in_leaf salen de las 10 configuraciones distintas de mayor AUC de la optimización, una por modelo; sus valores no están escritos en el código. Según la salida guardada en el notebook, la de mayor AUC es num_iterations 2733, num_leaves 1273, min_sum_hessian_in_leaf 0.01675586 (AUC 0.9181958 en 202106).
- **Semillas:** Semilla primigenia 170383, usada en todas las evaluaciones de la optimización. Para los modelos finales se sortean 10 semillas con set.seed(170383) y sample.int(100000000, 10), una por modelo.
- **Cantidad de semillas:** 10
- **Ensamble:** Promedio aritmético (rowMeans) de las probabilidades de 10 modelos LightGBM; cada modelo tiene una semilla distinta y una de las 10 configuraciones de hiperparámetros tomadas de la optimización bayesiana.
- **Corte:** Cantidad fija de clientes: se ordena por probabilidad promedio descendente y se generan cinco archivos con los primeros 10000, 10500, 11000, 11500 y 12000. Según el README, el entregado es el de 11000.
- **Validación:** Un mes posterior al entrenamiento: en la optimización se entrena con 202103 y 202104 y se mide el AUC en 202106. El notebook define funciones para calcular la ganancia (realidad_inicializar y realidad_evaluar) que no se llaman en ninguna celda. No se observa en el código una medición del ensamble final ni de los cortes sobre meses con clase.
- **Salidas:** En Google Drive, carpeta dmeyf/exp/HTEntrega1Prueba1: BO_evaluaciones.tsv, bayesiana.RDATA, BO_resultados.tsv, configuraciones_ensamble.tsv y PARAM.yml. En dmeyf/exp/expEntrega1Prueba1: modelo_01.txt a modelo_10.txt, modelos_semillas_configuraciones.tsv, probabilidades_ensamble_10.csv.gz, probabilidades_individuales_10.csv.gz, submit_ensamble10_10000.csv, submit_ensamble10_10500.csv, submit_ensamble10_11000.csv, submit_ensamble10_11500.csv, submit_ensamble10_12000.csv y PARAM.yml. En el disco de Colab: /content/datasets/competencia_01.csv.gz. Ninguno de estos archivos está en el repositorio.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: Google Colab con Google Drive montado en /content/.drive. Las celdas de texto indican runtime Python 3 para la preparación del ambiente y runtime R para el resto. La metadata del notebook declara kernel R ('ir') y machine_shape 'hm' de Colab. No se declaran versiones de R ni de los paquetes; los que faltan se instalan con install.packages sin indicar versión.

## Pasos del camino de la entrega

1. **Preparación del ambiente en Google Colab.** Con runtime Python 3 se monta Google Drive en /content/.drive. Una celda de shell crea la carpeta dmeyf en Drive, la enlaza como /content/buckets/b1 y descarga competencia_01_crudo.csv desde storage.googleapis.com si todavía no está, copiándolo a /content/datasets. (`entrega1Gromadzyn.ipynb` líneas 17–55)
2. **Generación de clase_ternaria.** Con runtime R se lee el dataset crudo, se pasa ccajas_depositos a NA en 202105 y se calcula clase_ternaria mirando si cada cliente tiene registro en el mes siguiente y en el subsiguiente (CONTINUA, BAJA+1, BAJA+2). El resultado se graba como competencia_01.csv.gz. (`entrega1Gromadzyn.ipynb` líneas 63–117)
3. **Librerías y parámetros de la corrida.** Se cargan data.table, lightgbm, mlrMBO, DiceKriging y otras librerías. Se definen la semilla primigenia 170383, los meses (optimización: 202103 y 202104 con validación en 202106; entrenamiento final: 202103 a 202106; predicción: 202108), 10 modelos, 10 configuraciones, los hiperparámetros fijos de LightGBM y el espacio de búsqueda de tres hiperparámetros con 30 iteraciones. (`entrega1Gromadzyn.ipynb` líneas 145–262)
4. **Lectura del dataset y corrección de mayo.** Se lee competencia_01.csv.gz, se vuelve a pasar ccajas_depositos a NA en 202105, se arma la lista de variables numéricas originales y se ordena el dataset por cliente y mes. (`entrega1Gromadzyn.ipynb` líneas 327–363)
5. **Lags y deltas de orden 1 y 2.** Para cada variable numérica se crean el valor de 1 y de 2 meses atrás (_lag1, _lag2) y la diferencia entre el valor actual y cada uno (_delta_lag1, _delta_lag2). Una máscara deja en NA el lag cuando la fila anterior no es del mismo cliente o no está a exactamente 1 o 2 meses. (`entrega1Gromadzyn.ipynb` líneas 365–419)
6. **Ranking mensual con cero fijo.** Cada columna numérica (originales, lags y deltas) se reemplaza por su ranking dentro de cada foto_mes: cero queda en 0, los negativos van a [-1, 0) y los positivos a (0, 1]. Después se controla con stopifnot que todas las columnas estén en [-1, 1] o sean NA y que ccajas_depositos siga en NA en 202105. (`entrega1Gromadzyn.ipynb` líneas 421–511)
7. **Conjuntos de entrenamiento y validación para la optimización.** Se separan 202103 y 202104 para entrenar y 202106 para validar, se crea clase01 (1 para BAJA+1 y BAJA+2) y se arman los lgb.Dataset con todas las columnas que no son identificadores ni etiquetas, sin submuestreo. (`entrega1Gromadzyn.ipynb` líneas 513–544)
8. **Función objetivo: AUC en 202106.** Cada evaluación entrena LightGBM con los hiperparámetros fijos más los propuestos, con la semilla 170383, predice sobre 202106 y calcula el AUC con la fórmula de rangos. Cada evaluación se agrega a BO_evaluaciones.tsv. (`entrega1Gromadzyn.ipynb` líneas 549–584)
9. **Optimización bayesiana.** Se configura mlrMBO con un modelo sustituto de kriging (matern3_2), criterio Expected Improvement, 30 iteraciones y guardado del estado en bayesiana.RDATA cada 600 segundos. Se ejecuta con mbo, o se retoma con mboContinue si el archivo de estado ya existe. (`entrega1Gromadzyn.ipynb` líneas 586–643)
10. **Selección de las configuraciones para el ensamble.** El historial de la optimización se ordena por AUC descendente y se toman las primeras 10 combinaciones distintas de num_iterations, num_leaves y min_sum_hessian_in_leaf. Se graban BO_resultados.tsv, configuraciones_ensamble.tsv y PARAM.yml. (`entrega1Gromadzyn.ipynb` líneas 650–669)
11. **Dataset de entrenamiento final.** En la carpeta expEntrega1Prueba1 se calcula clase01 sobre todo el dataset y se arma el lgb.Dataset con los meses 202103, 202104, 202105 y 202106 completos. (`entrega1Gromadzyn.ipynb` líneas 678–703)
12. **Entrenamiento de 10 modelos.** Se sortean 10 semillas a partir de 170383. El modelo i combina los hiperparámetros fijos con la configuración i de la lista (en forma cíclica si hubiera menos de 10), usa la semilla i, se entrena sobre 202103 a 202106 y se guarda como modelo_NN.txt. Se graba una tabla con la semilla y la configuración de cada modelo. (`entrega1Gromadzyn.ipynb` líneas 723–750)
13. **Predicción de 202108 y promedio.** Se cargan desde disco los 10 modelos guardados, se predice 202108 con cada uno y se promedian las 10 probabilidades por cliente. Se graban las probabilidades promedio y las individuales. (`entrega1Gromadzyn.ipynb` líneas 752–850)
14. **Archivos de envío con cinco cortes.** Se ordenan los clientes por probabilidad promedio descendente y se graba un CSV sin encabezado con los primeros 10000, 10500, 11000, 11500 y 12000 numero_de_cliente. Según el README, el archivo entregado es submit_ensamble10_11000.csv. (`entrega1Gromadzyn.ipynb` líneas 852–895; `README.md` líneas 1–3)

## Archivos

- `entrega1Gromadzyn.ipynb` · principal · Jupyter (R) · 901 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/gromadzyn/entrega1Gromadzyn.ipynb.txt) — Notebook de Google Colab que recorre todo el camino de la entrega: descarga del dataset, cálculo de clase_ternaria, lags, deltas y ranking mensual con cero fijo, optimización bayesiana de LightGBM con AUC en 202106, entrenamiento de 10 modelos sobre 202103 a 202106, promedio de probabilidades para 202108 y escritura de los archivos de envío con cinco cortes.
- `README.md` · explicacion · Markdown · 3 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/gromadzyn/README.md.txt) — Dos frases: indica que el Colab genera, entre otros, el archivo submit_ensamble10_11000.csv en Google Drive (Mi unidad / dmeyf / exp / expEntrega1Prueba1) y que ese es el CSV de la entrega.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### entrega1Gromadzyn.ipynb

Notebook de Google Colab que recorre todo el camino de la entrega: descarga del dataset, cálculo de clase_ternaria, lags, deltas y ranking mensual con cero fijo, optimización bayesiana de LightGBM con AUC en 202106, entrenamiento de 10 modelos sobre 202103 a 202106, promedio de probabilidades para 202108 y escritura de los archivos de envío con cinco cortes.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–15] Celdas de texto iniciales: un enlace 'Open in Colab' que apunta a
#   ensembles/z494_TareaHogar_04.ipynb del repositorio dmecoyfin/dmeyf2026, el título 'COMPETENCIA 1' y la
#   indicación de correr esta primera parte con el runtime Python 3 y de conectar Google Drive.
#%% celda 1 [texto]
<a href="https://colab.research.google.com/github/dmecoyfin/dmeyf2026/blob/main/ensembles/z494_TareaHogar_04.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

#%% celda 2 [texto]
# COMPETENCIA 1

#%% celda 3 [texto]
#### 2.1  Seteo del ambiente en Google Colab

#%% celda 4 [texto]
Esta parte se debe correr con el runtime en Python3
<br>Ir al menu, Runtime -> Change Runtime Type -> Runtime type ->  **Python 3**

#%% celda 5 [texto]
Conectar la virtual machine donde esta corriendo Google Colab con el  Google Drive, para poder tener persistencia de archivos

# [Anotación · líneas 17–20] Celda en Python: monta Google Drive en /content/.drive.
#%% celda 6 [código]
# primero establecer el Runtime de Python 3
from google.colab import drive
drive.mount('/content/.drive')

# [Anotación · líneas 22–55] La celda de texto menciona el archivo kaggle.json y el 'dataset_pequeno'. La
#   celda de shell que sigue no usa kaggle.json: crea la carpeta dmeyf en Google Drive, la enlaza como
#   /content/buckets/b1, crea las subcarpetas exp y datasets y, si el archivo no existe, descarga
#   competencia_01_crudo.csv con wget desde storage.googleapis.com al Drive y lo copia a /content/datasets.
#%% celda 7 [texto]
Para correr la siguiente celda es fundamental en Arranque en Frio haber copiado el archivo kaggle.json al Google Drive, en la carpeta indicada en el instructivo

<br>los siguientes comando estan en shell script de Linux
*   Crear las carpetas en el Google Drive
*   "instalar" el archivo kaggle.json desde el Google Drive a la virtual machine para que pueda ser utilizado por la libreria  kaggle de Python
*   Bajar el  **dataset_pequeno**  al  Google Drive  y tambien al disco local de la virtual machine que esta corriendo Google Colab

#%% celda 8 [código]
%%shell

mkdir -p "/content/.drive/My Drive/dmeyf"
mkdir -p "/content/buckets"
ln -s "/content/.drive/My Drive/dmeyf" /content/buckets/b1


mkdir -p /content/buckets/b1/exp
mkdir -p /content/buckets/b1/datasets
mkdir -p /content/datasets



archivo_origen="https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
archivo_destino="/content/datasets/competencia_01_crudo.csv"
archivo_destino_bucket="/content/buckets/b1/datasets/competencia_01_crudo.csv"

if ! test -f $archivo_destino_bucket; then
  wget  $archivo_origen  -O $archivo_destino_bucket
fi


if ! test -f $archivo_destino; then
  cp  $archivo_destino_bucket  $archivo_destino
fi

# [Anotación · líneas 57–86] A partir de aquí el runtime es R. Lee competencia_01_crudo.csv, pasa
#   ccajas_depositos a NA en 202105 y arma una tabla auxiliar con la posición de cada fila, el cliente y un
#   número de período consecutivo (año × 12 + mes), ordenada por cliente y período. Guarda el último período del
#   dataset y el anterior.
#%% celda 9 [texto]
## Generacion de la clase_ternaria

#%% celda 10 [texto]
Esta parte se debe correr con el runtime en lenguaje **R** Ir al menu, Runtime -> Change Runtime Tipe -> Runtime type -> R

#%% celda 11 [código]
require( "data.table" )

# leo el dataset
dataset <- fread("/content/datasets/competencia_01_crudo.csv" )

# La variable rota se anula UNICAMENTE en mayo de 2021.
# Se corrige antes de crear variables temporales.
dataset[foto_mes == 202105, ccajas_depositos := NA_real_]

# calculo el periodo0 consecutivo
dsimple <- dataset[, list(
    "pos" = .I,
    numero_de_cliente,
    periodo0 = as.integer(foto_mes/100)*12 +  foto_mes%%100 ) ]


# ordeno
setorder( dsimple, numero_de_cliente, periodo0 )

# calculo topes
periodo_ultimo <- dsimple[, max(periodo0) ]
periodo_anteultimo <- periodo_ultimo - 1


# [Anotación · líneas 88–113] Calcula por cliente los períodos de sus dos registros siguientes (lead 1 y lead
#   2) y asigna la clase: CONTINUA a los períodos anteriores al anteúltimo; BAJA+1 si el cliente no tiene
#   registro en el período siguiente; BAJA+2 si tiene el siguiente pero no el de dos meses después. Las filas
#   que no entran en ninguna condición quedan en NA. Pega la clase en el dataset y lo graba como
#   /content/datasets/competencia_01.csv.gz.
# calculo los leads de orden 1 y 2
dsimple[, c("periodo1", "periodo2") :=
    shift(periodo0, n=1:2, fill=NA, type="lead"),  numero_de_cliente ]

# assign most common class values = "CONTINUA"
dsimple[ periodo0 < periodo_anteultimo, clase_ternaria := "CONTINUA" ]

# calculo BAJA+1
dsimple[ periodo0 < periodo_ultimo &
    ( is.na(periodo1) | periodo0 + 1 < periodo1 ),
    clase_ternaria := "BAJA+1" ]

# calculo BAJA+2
dsimple[ periodo0 < periodo_anteultimo & (periodo0+1 == periodo1 )
    & ( is.na(periodo2) | periodo0 + 2 < periodo2 ),
    clase_ternaria := "BAJA+2" ]


# pego el resultado en el dataset original y grabo
setorder( dsimple, pos )
dataset[, clase_ternaria := dsimple$clase_ternaria ]

fwrite( dataset,
    file =  "/content/datasets/competencia_01.csv.gz",
    sep = ","
)

# [Anotación · líneas 115–117] Ordena el dataset y cuenta registros por foto_mes y clase_ternaria.
#%% celda 12 [código]
setorder( dataset, foto_mes, clase_ternaria, numero_de_cliente)
dataset[, .N, list(foto_mes, clase_ternaria)]

# [Anotación · líneas 119–137] Encabezados de la sección de optimización de hiperparámetros. Imprime fecha y
#   hora, borra todos los objetos del ambiente de R (incluido el dataset en memoria) y libera memoria.
#%% celda 13 [texto]
### 2.2 Optimizacion Hiperparámetros

#%% celda 14 [texto]
Esta parte se debe correr con el runtime en lenguaje R Ir al menu, Runtime -> Change Runtime Type -> Runtime type -> R

#%% celda 15 [texto]
### 2.2.1 Inicio

#%% celda 16 [texto]
limpio el ambiente de R

#%% celda 17 [código]
format(Sys.time(), "%a %b %d %X %Y")

#%% celda 18 [código]
# limpio la memoria
rm(list=ls(all.names=TRUE)) # remove all objects
gc(full=TRUE, verbose=FALSE) # garbage collection

# [Anotación · líneas 139–172] Carga data.table, parallel, R.utils, primes, utils, rlist, yaml, lightgbm,
#   DiceKriging y mlrMBO. Los paquetes que no están instalados se instalan con install.packages, sin indicar
#   versión.
#%% celda 19 [texto]
### 2.2.2 Carga de Librerias

#%% celda 20 [texto]
Esta parte lleva varios minutos la primera vez en Google Colab

#%% celda 21 [código]
# cargo las librerias que necesito
require("data.table")
require("parallel")

if(!require("R.utils")) install.packages("R.utils")
require("R.utils")

if( !require("primes") ) install.packages("primes")
require("primes")

if( !require("utils") ) install.packages("utils")
require("utils")

if( !require("rlist") ) install.packages("rlist")
require("rlist")

if( !require("yaml")) install.packages("yaml")
require("yaml")

if( !require("lightgbm") ) install.packages("lightgbm")
require("lightgbm")

if( !require("DiceKriging") ) install.packages("DiceKriging")
require("DiceKriging")

if( !require("mlrMBO") ) install.packages("mlrMBO")
require("mlrMBO")

# [Anotación · líneas 174–199] Define los parámetros de la corrida: experimento 'Entrega1Prueba1', semilla
#   primigenia 170383, meses de entrenamiento para la optimización 202103 y 202104, validación 202106,
#   entrenamiento final 202103 a 202106, mes a predecir 202108, semilla_kaggle 314159, cortes de 10000 a 12000
#   cada 500, 10 modelos y 10 configuraciones. Fija undersampling en 1.0; ese parámetro no se lee en ninguna
#   otra celda.
#%% celda 22 [texto]
### 2.2.3 Definicion de Parametros

#%% celda 23 [texto]
aqui debe cargar SU semilla primigenia
<br>recuerde cambiar el numero de experimento en cada corrida nueva

#%% celda 24 [código]
PARAM <- list()
PARAM$experimento <- "Entrega1Prueba1"
PARAM$semilla_primigenia <- 170383

#%% celda 25 [código]
# Optimización: validación temporal con junio; el entrenamiento final incluye los cuatro meses.
PARAM$train <- c(202103, 202104)
PARAM$validacion <- 202106
PARAM$train_final <- c(202103, 202104, 202105, 202106)
PARAM$future <- 202108
PARAM$semilla_kaggle <- 314159
PARAM$cortes <- c(10000L, 10500L, 11000L, 11500L, 12000L)
PARAM$n_modelos <- 10L
PARAM$top_configuraciones <- 10L

#%% celda 26 [código]
# Sin undersampling en la primera competencia, incluida la BO.
PARAM$trainingstrategy$undersampling <- 1.0

# [Anotación · líneas 201–240] Lista de hiperparámetros fijos de LightGBM: boosting gbdt, objective binary,
#   metric auc, max_depth -1, min_gain_to_split 0, lambda_l1 y lambda_l2 0, max_bin 31, bagging_fraction 1.0,
#   is_unbalance FALSE, scale_pos_weight 1.0, extra_trees FALSE, learning_rate 0.005, feature_fraction 0.50,
#   feature_fraction_bynode 0.20, min_data_in_leaf 0 y semilla 170383. También figuran drop_rate 0.1, max_drop
#   50 y skip_drop 0.5. num_iterations (1200) y num_leaves (750) están en la lista y son reemplazados por los
#   valores que propone la optimización.
#%% celda 27 [código]
# Parametros LightGBM
# parametros fijos del LightGBM que se pisaran con la parte variable de la BO
PARAM$lgbm$param_fijos <-  list(
  boosting= "gbdt", # puede ir  dart  , ni pruebe random_forest
  objective= "binary",
  metric= "auc",
  first_metric_only= TRUE,
  boost_from_average= TRUE,
  feature_pre_filter= FALSE,
  force_row_wise= TRUE, # para reducir warnings
  verbosity= -100,

  seed= PARAM$semilla_primigenia,

  max_depth= -1L, # -1 significa no limitar,  por ahora lo dejo fijo
  min_gain_to_split= 0, # min_gain_to_split >= 0
  lambda_l1= 0.0, # lambda_l1 >= 0.0
  lambda_l2= 0.0, # lambda_l2 >= 0.0
  max_bin= 31L, # lo debo dejar fijo, no participa de la BO

  bagging_fraction= 1.0, # 0.0 < bagging_fraction <= 1.0
  pos_bagging_fraction= 1.0, # 0.0 < pos_bagging_fraction <= 1.0
  neg_bagging_fraction= 1.0, # 0.0 < neg_bagging_fraction <= 1.0
  is_unbalance= FALSE, #
  scale_pos_weight= 1.0, # scale_pos_weight > 0.0

  drop_rate= 0.1, # 0.0 < neg_bagging_fraction <= 1.0
  max_drop= 50, # <=0 means no limit
  skip_drop= 0.5, # 0.0 <= skip_drop <= 1.0

  extra_trees= FALSE,

  num_iterations= 1200,
  learning_rate= 0.005,
  feature_fraction= 0.50,
  feature_fraction_bynode= 0.20,
  num_leaves= 750,
  min_data_in_leaf= 0
)

# [Anotación · líneas 242–262] Define el espacio de búsqueda de la optimización bayesiana: num_iterations
#   entero entre 64 y 4096, num_leaves entero entre 16 y 2048 y min_sum_hessian_in_leaf real entre 1e-06 y 0.1.
#   Fija 30 iteraciones.
#%% celda 28 [texto]
Aqui se definen los hiperparámetros de LightGBM que participan de la Bayesian Optimization
<br> si es un numero entero debe ir  makeIntegerParam
<br> si es un numero real (con decimales) debe ir  makeNumericParam
<br> es muy importante leer cuales son un lower y upper  permitidos y ademas razonables

#%% celda 29 [código]
# Los únicos hiperparámetros optimizados (los demás permanecen fijos).
PARAM$hyperparametertuning$hs <- makeParamSet(
  makeIntegerParam("num_iterations", lower= 64L, upper= 4096L),
  makeIntegerParam("num_leaves", lower= 16L, upper= 2048L),
  makeNumericParam("min_sum_hessian_in_leaf", lower= 1e-06, upper= 0.1)
)

#%% celda 30 [texto]
A mayor cantidad de hiperparámetros, se debe aumentar las iteraciones de la Bayesian Optimization
<br> 30 es un valor muy tacaño, pero corre rápido
<br> deberia partir de 50, alcanzando los 100 si se dispone de tiempo

#%% celda 31 [código]
PARAM$hyperparametertuning$iteraciones <- 30L # ajustar según presupuesto computacional

# [Anotación · líneas 264–314] Define tres funciones auxiliares. particionar agrega una columna fold con una
#   partición al azar estratificada según las proporciones pedidas. realidad_inicializar arma una tabla con
#   cliente, mes y clase y la parte en proporción 3 y 7 con la semilla 314159. realidad_evaluar calcula la
#   ganancia de una predicción en cada parte y en total, con 1072500 por cada BAJA+2 marcado y -27500 por cada
#   otro registro marcado. realidad_inicializar y realidad_evaluar no se llaman en ninguna otra celda del
#   notebook.
#%% celda 32 [código]
# particionar agrega una columna llamada fold a un dataset
#   que consiste en una particion estratificada segun agrupa
# particionar( data=dataset, division=c(70,30),
#  agrupa=clase_ternaria, seed=semilla)   crea una particion 70, 30

particionar <- function(data, division, agrupa= "", campo= "fold", start= 1, seed= NA) {
  if (!is.na(seed)) set.seed(seed, "L'Ecuyer-CMRG")

  bloque <- unlist(mapply(
    function(x, y) {rep(y, x)},division, seq(from= start, length.out= length(division))))

  data[, (campo) := sample(rep(bloque,ceiling(.N / length(bloque))))[1:.N],by= agrupa]
}

#%% celda 33 [código]
# iniciliazo el dataset de realidad, para medir ganancia
realidad_inicializar <- function( pfuture, pparam) {

  # datos para verificar la ganancia
  drealidad <- pfuture[, list(numero_de_cliente, foto_mes, clase_ternaria)]

  particionar(drealidad,
    division= c(3, 7),
    agrupa= "clase_ternaria",
    seed= PARAM$semilla_kaggle
  )

  return( drealidad )
}

#%% celda 34 [código]
# evaluo ganancia en los datos de la realidad

realidad_evaluar <- function( prealidad, pprediccion) {

  prealidad[ pprediccion,
    on= c("numero_de_cliente", "foto_mes"),
    predicted:= i.Predicted
  ]

  tbl <- prealidad[, list("qty"=.N), list(fold, predicted, clase_ternaria)]

  res <- list()
  res$public  <- tbl[fold==1 & predicted==1L, sum(qty*ifelse(clase_ternaria=="BAJA+2", 1072500, -27500))]/0.3
  res$private <- tbl[fold==2 & predicted==1L, sum(qty*ifelse(clase_ternaria=="BAJA+2", 1072500, -27500))]/0.7
  res$total <- tbl[predicted==1L, sum(qty*ifelse(clase_ternaria=="BAJA+2", 1072500, -27500))]

  prealidad[, predicted:=NULL]
  return( res )
}

# [Anotación · líneas 316–325] Crea la carpeta de trabajo de la optimización,
#   /content/buckets/b1/exp/HTEntrega1Prueba1, y se ubica en ella.
#%% celda 35 [texto]
### 2.2.4  Preprocesamiento

#%% celda 36 [código]
# carpeta de trabajo

setwd("/content/buckets/b1/exp")
experimento_folder <- paste0("HT", PARAM$experimento)
dir.create(experimento_folder, showWarnings=FALSE)
setwd( paste0("/content/buckets/b1/exp/", experimento_folder ))

# [Anotación · líneas 327–363] Lee competencia_01.csv.gz, vuelve a pasar ccajas_depositos a NA en 202105 y
#   arma la lista de variables numéricas originales, dejando afuera numero_de_cliente, foto_mes, clase_ternaria,
#   clase01, azar, training y fold. Si hay variables no numéricas, avisa que quedan sin lags. Ordena el dataset
#   por cliente y mes e imprime la cantidad de variables numéricas y de filas.
#%% celda 37 [código]

library(data.table)

t_total <- proc.time()[["elapsed"]]

# ============================================================
# 1. LECTURA Y CORRECCION DE MAYO
# ============================================================
dataset <- fread(
  "/content/datasets/competencia_01.csv.gz",
  stringsAsFactors = FALSE,
  showProgress = TRUE
)

dataset[foto_mes == 202105L, ccajas_depositos := NA_real_]

excluir <- c(
  "numero_de_cliente", "foto_mes", "clase_ternaria",
  "clase01", "azar", "training", "fold"
)

variables_originales <- setdiff(names(dataset), excluir)
variables_numericas <- variables_originales[
  vapply(dataset[, ..variables_originales], is.numeric, logical(1))
]

otras <- setdiff(variables_originales, variables_numericas)
if (length(otras)) {
  message("Variables no numericas sin lags: ",
          paste(otras, collapse = ", "))
}

setorder(dataset, numero_de_cliente, foto_mes)

cat("Variables numericas:", length(variables_numericas), "\n")
cat("Filas:", nrow(dataset), "\n")

# [Anotación · líneas 365–419] Para los órdenes 1 y 2 arma una máscara que marca una fila como válida sólo si
#   la fila ubicada 'orden' posiciones antes es del mismo cliente y está exactamente a 'orden' meses. Para cada
#   variable numérica crea <variable>_lag<orden> con el valor de esa fila anterior (NA donde la máscara no es
#   válida) y <variable>_delta_lag<orden> con la diferencia entre el valor actual y ese lag. El desplazamiento
#   se hace sobre la columna entera, sin agrupar por cliente.
# ============================================================
# 2. LAGS Y DELTA LAGS (ORDENES 1 Y 2)
# ============================================================
t0 <- proc.time()[["elapsed"]]

mes <- (dataset$foto_mes %/% 100L) * 12L +
       (dataset$foto_mes %% 100L)

cliente <- dataset$numero_de_cliente
n <- nrow(dataset)

for (orden in 1:2) {

  # Una sola mascara para TODAS las variables
  valido <- rep(FALSE, n)

  if (n > orden) {
    actual <- seq.int(orden + 1L, n)
    anterior <- actual - orden

    valido[actual] <-
      !is.na(cliente[actual]) &
      !is.na(cliente[anterior]) &
      cliente[actual] == cliente[anterior] &
      (mes[actual] - mes[anterior] == orden)
  }

  # Sin by=cliente ni agrupamientos repetidos
  for (v in variables_numericas) {

    previo <- shift(dataset[[v]], n = orden)
    previo[!valido] <- NA_real_

    set(
      dataset,
      j = paste0(v, "_lag", orden),
      value = previo
    )

    set(
      dataset,
      j = paste0(v, "_delta_lag", orden),
      value = dataset[[v]] - previo
    )
  }

  cat(
    "Orden", orden, "completado en",
    round(proc.time()[["elapsed"]] - t0, 1),
    "segundos acumulados\n"
  )
}

rm(mes, cliente, valido)
gc(verbose = FALSE)

# [Anotación · líneas 421–449] Define ranking_cero_fijo: los ceros quedan en 0; los valores negativos se
#   ordenan entre sí y se llevan al intervalo [-1, 0) como -1 + (posición - 1) / cantidad de negativos; los
#   positivos se llevan a (0, 1] como posición / cantidad de positivos. Los empates reciben la posición promedio
#   y los NA se conservan.
# ============================================================
# 3. RANKINGS MENSUALES [-1, 1], CERO FIJO
# ============================================================
t_rank <- proc.time()[["elapsed"]]

ranking_cero_fijo <- function(x) {

  z <- rep(NA_real_, length(x))

  ceros <- !is.na(x) & x == 0
  z[ceros] <- 0

  neg <- which(!is.na(x) & x < 0)
  pos <- which(!is.na(x) & x > 0)

  if (length(neg)) {
    z[neg] <- -1 +
      (frank(x[neg], ties.method = "average") - 1) /
      length(neg)
  }

  if (length(pos)) {
    z[pos] <-
      frank(x[pos], ties.method = "average") /
      length(pos)
  }

  z
}

# [Anotación · líneas 451–487] Toma todas las columnas numéricas que no son identificadores ni etiquetas
#   (originales, lags y deltas) y reemplaza los valores de cada una por el resultado de ranking_cero_fijo
#   calculado por separado dentro de cada foto_mes. Informa el avance cada 100 columnas.
campos_ranking <- setdiff(names(dataset), excluir)
campos_ranking <- campos_ranking[
  vapply(dataset[, ..campos_ranking], is.numeric, logical(1))
]

# Calculamos los indices de cada mes UNA SOLA VEZ
indices_meses <- split(
  seq_len(nrow(dataset)),
  dataset$foto_mes
)

total <- length(campos_ranking)

for (i in seq_along(campos_ranking)) {

  v <- campos_ranking[i]
  x <- dataset[[v]]

  for (idx in indices_meses) {
    x[idx] <- ranking_cero_fijo(x[idx])
  }

  set(dataset, j = v, value = x)

  if (i %% 100L == 0L || i == total) {
    cat(
      "Rankings:", i, "/", total,
      "| Tiempo:",
      round(proc.time()[["elapsed"]] - t_rank, 1),
      "segundos\n"
    )
    flush.console()
  }
}

rm(indices_meses)
gc(verbose = FALSE)

# [Anotación · líneas 489–511] Controles con stopifnot: ccajas_depositos tiene que ser NA en todo 202105 y
#   todas las columnas rankeadas tienen que estar entre -1 y 1 o ser NA. Imprime la cantidad de features y el
#   tiempo total del preprocesamiento.
# ============================================================
# 4. AUDITORIA
# ============================================================
stopifnot(
  all(is.na(dataset[
    foto_mes == 202105L,
    ccajas_depositos
  ]))
)

stopifnot(
  all(vapply(
    dataset[, ..campos_ranking],
    function(x) all(is.na(x) | (x >= -1 & x <= 1)),
    logical(1)
  ))
)

cat("\nPREPROCESAMIENTO TERMINADO\n")
cat("Features:", length(campos_ranking), "\n")
cat("Tiempo total:",
    round(proc.time()[["elapsed"]] - t_total, 1),
    "segundos\n")

# [Anotación · líneas 513–544] Separa los meses 202103 y 202104 para entrenar y 202106 para validar. Crea
#   clase01, que vale 1 para BAJA+1 y BAJA+2 y 0 para el resto. Marca todos los registros de entrenamiento con
#   training = 1 (sin submuestreo). Define campos_buenos como todas las columnas menos identificadores y
#   etiquetas, verifica que sean numéricas y arma los lgb.Dataset de entrenamiento y de validación.
#%% celda 38 [código]
dataset_train <- dataset[foto_mes %in% PARAM$train]
dataset_validate <- dataset[foto_mes == PARAM$validacion]

#%% celda 39 [código]
# Mantener el target original: BAJA+1 Y BAJA+2 son clase positiva.
dataset_train[, clase01 := as.integer(clase_ternaria %in% c("BAJA+2", "BAJA+1"))]
dataset_validate[, clase01 := as.integer(clase_ternaria %in% c("BAJA+2", "BAJA+1"))]
stopifnot(!anyNA(dataset_train$clase01), !anyNA(dataset_validate$clase01))

#%% celda 40 [código]
# Sin undersampling: se entrenan TODOS los registros de los meses seleccionados.
dataset_train[, training := 1L]

#%% celda 41 [código]
# Identificadores/etiquetas fuera de las features (evita leakage).
campos_buenos <- setdiff(names(dataset_train),
  c("numero_de_cliente", "foto_mes", "clase_ternaria", "clase01", "training", "azar", "fold"))
# LightGBM recibe matriz numérica.
stopifnot(all(vapply(dataset_train[, ..campos_buenos], is.numeric, logical(1))))

#%% celda 42 [código]
dtrain <- lgb.Dataset(
  data= data.matrix(dataset_train[, ..campos_buenos]),
  label= dataset_train$clase01, free_raw_data= FALSE
)
dvalidate <- lgb.Dataset(
  data= data.matrix(dataset_validate[, ..campos_buenos]),
  label= dataset_validate$clase01, reference=dtrain, free_raw_data=FALSE
)
cat("Train:", nrow(dataset_train), "Validation:", nrow(dataset_validate),
    "Features:", length(campos_buenos), "\n")

# [Anotación · líneas 546–560] Prepara el registro de la optimización: si existe BO_evaluaciones.tsv, retoma
#   el contador de iteraciones desde el máximo guardado. Define loguear, que agrega una fila a un archivo
#   separado por tabuladores.
#%% celda 43 [texto]
2.2.5 Configuracion Bayesian Optimization

#%% celda 44 [código]
# BO tiene su propio historial persistente; no se sobreescribe con el resultado final.
giter <- 0L
if (file.exists("BO_evaluaciones.tsv")) {
  tb_BO <- fread("BO_evaluaciones.tsv")
  if (nrow(tb_BO)) giter <- max(tb_BO$iter, na.rm=TRUE)
}
loguear <- function(registro, archivo) {
  fila <- as.data.table(registro)
  fwrite(fila, file=archivo, sep="\t", append=file.exists(archivo),
         col.names=!file.exists(archivo))
}

# [Anotación · líneas 562–584] Función objetivo de la optimización: combina los hiperparámetros fijos con los
#   propuestos, fija la semilla 170383, entrena LightGBM con 202103 y 202104 durante num_iterations rondas,
#   predice sobre 202106 y calcula el AUC con la fórmula de rangos (suma de los rangos de los positivos menos
#   positivos × (positivos + 1) / 2, dividido por positivos × negativos). Guarda la evaluación en
#   BO_evaluaciones.tsv y devuelve el AUC.
#%% celda 45 [código]
# Optimización AUC, validación temporal 202106.
Estimar_lightgbm <- function(xs) {
  giter <<- giter + 1L
  parametros <- modifyList(PARAM$lgbm$param_fijos, xs)
  parametros$seed <- PARAM$semilla_primigenia
  niter <- as.integer(parametros$num_iterations)
  parametros$num_iterations <- NULL
  modelo <- lgb.train(params=parametros, data=dtrain,
                       valids=list(validacion=dvalidate),
                       nrounds=niter,
                       verbose=-1)
  # AUC calculada explícitamente sobre validación temporal (evita diferencias de API).
  p <- predict(modelo, data.matrix(dataset_validate[, ..campos_buenos]))
  y <- dataset_validate$clase01
  positivos <- sum(y == 1L); negativos <- sum(y == 0L)
  stopifnot(positivos > 0, negativos > 0)
  puntaje <- (sum(rank(p, ties.method="average")[y == 1L]) -
              positivos*(positivos+1)/2) / (positivos*negativos)
  loguear(c(list(iter=giter, auc=puntaje), xs), "BO_evaluaciones.tsv")
  cat("BO", giter, "AUC", signif(puntaje, 6), "\n")
  return(puntaje)
}

# [Anotación · líneas 586–629] Configura mlrMBO: función objetivo a maximizar, declarada como ruidosa (noisy =
#   TRUE); guardado del estado en bayesiana.RDATA cada 600 segundos; 30 iteraciones como criterio de fin;
#   Expected Improvement como criterio para proponer puntos; y un modelo sustituto de kriging (regr.km) con
#   covarianza matern3_2.
#%% celda 46 [código]
# Aqui comienza la configuracion de la Bayesian Optimization

# en este archivo quedan la evolucion binaria de la BO
kbayesiana <- "bayesiana.RDATA"

funcion_optimizar <- Estimar_lightgbm # la funcion que voy a maximizar

configureMlr(show.learner.output= FALSE)

# configuro la busqueda bayesiana,  los hiperparametros que se van a optimizar
# por favor, no desesperarse por lo complejo

obj.fun <- makeSingleObjectiveFunction(
  fn= funcion_optimizar, # la funcion que voy a maximizar
  minimize= FALSE, # estoy Maximizando la ganancia
  noisy= TRUE,
  par.set= PARAM$hyperparametertuning$hs, # definido al comienzo del programa
  has.simple.signature= FALSE # paso los parametros en una lista
)

# cada 600 segundos guardo el resultado intermedio
ctrl <- makeMBOControl(
  save.on.disk.at.time= 600, # se graba cada 600 segundos
  save.file.path= kbayesiana
) # se graba cada 600 segundos

# indico la cantidad de iteraciones que va a tener la Bayesian Optimization
ctrl <- setMBOControlTermination(
  ctrl,
  iters= PARAM$hyperparametertuning$iteraciones
) # cantidad de iteraciones

# defino el método estandar para la creacion de los puntos iniciales,
# los "No Inteligentes"
ctrl <- setMBOControlInfill(ctrl, crit= makeMBOInfillCritEI())

# establezco la funcion que busca el maximo
surr.km <- makeLearner(
  "regr.km",
  predict.type= "se",
  covtype= "matern3_2",
  control= list(trace= TRUE)
)

# [Anotación · líneas 631–643] Ejecuta la optimización bayesiana con mbo; si bayesiana.RDATA ya existe, la
#   retoma con mboContinue. La llamada a mbo no recibe un diseño inicial.
#%% celda 47 [texto]
2.2.6 Corrida Bayesian Optimization

#%% celda 48 [código]

# inicio la optimizacion bayesiana, retomando si ya existe
# es la celda mas lenta de todo el notebook

if (!file.exists(kbayesiana)) {
  bayesiana_salida <- mbo(obj.fun, learner= surr.km, control= ctrl)
} else {
  bayesiana_salida <- mboContinue(kbayesiana) # retomo en caso que ya exista
}

# [Anotación · líneas 645–669] Pasa el historial de la optimización a una tabla, la ordena por AUC descendente
#   y la graba en BO_resultados.tsv. Guarda en PARAM la configuración de la primera fila y su AUC. Arma
#   configuraciones_ensamble con las primeras 10 combinaciones distintas de num_iterations, num_leaves y
#   min_sum_hessian_in_leaf en ese orden y las graba en configuraciones_ensamble.tsv. Escribe PARAM.yml e
#   imprime la configuración de mayor AUC.
#%% celda 49 [código]

tb_bayesiana <- as.data.table(bayesiana_salida$opt.path)
colnames( tb_bayesiana)

#%% celda 50 [código]
# BO: ordenar por AUC y recuperar las mejores configuraciones distintas.
tb_bayesiana <- as.data.table(bayesiana_salida$opt.path)
tb_bayesiana[, iter := .I]
setorder(tb_bayesiana, -y)
fwrite(tb_bayesiana, file="BO_resultados.tsv", sep="\t")
hiperparametros <- c("num_iterations", "num_leaves", "min_sum_hessian_in_leaf")
stopifnot(all(hiperparametros %in% names(tb_bayesiana)))
PARAM$out$lgbm$mejores_hiperparametros <- as.list(tb_bayesiana[1, ..hiperparametros])
PARAM$out$lgbm$y <- tb_bayesiana[1, y]
configuraciones_ensamble <- unique(tb_bayesiana[, ..hiperparametros])
configuraciones_ensamble <- head(configuraciones_ensamble, PARAM$top_configuraciones)
fwrite(configuraciones_ensamble, "configuraciones_ensamble.tsv", sep="\t")

#%% celda 51 [código]
write_yaml( PARAM, file="PARAM.yml")

#%% celda 52 [código]
print(PARAM$out$lgbm$mejores_hiperparametros)
print(PARAM$out$lgbm$y)

# [Anotación · líneas 671–703] Sección de producción; la celda de texto dice que el modelo final 'es uno
#   solo'. Se ubica en /content/buckets/b1/exp/expEntrega1Prueba1. Calcula clase01 en todo el dataset (1 para
#   BAJA+1 y BAJA+2, 0 para CONTINUA, NA donde no hay clase), filtra los meses 202103 a 202106, cuenta registros
#   por clase y arma el lgb.Dataset de entrenamiento final con campos_buenos.
#%% celda 53 [texto]
## 2.3  Produccion

#%% celda 54 [texto]
### Final Training
Construyo el modelo final, que es uno solo, no hace ningun tipo de particion < training, validation, testing>]

#%% celda 55 [código]
setwd("/content/buckets/b1/exp")
experimento <- paste0("exp", PARAM$experimento)
dir.create(experimento, showWarnings= FALSE)
setwd(file.path("/content/buckets/b1/exp", experimento))

#%% celda 56 [texto]
#### Final Training Dataset

Aqui esta la gran decision de en qué meses hago el Final Training
<br> debo utilizar los mejores hiperparámetros que encontré en la  optimización bayesiana

#%% celda 57 [código]
# Mantener BAJA+1 y BAJA+2 como positivos; no inventar etiqueta futura.
dataset[, clase01 := fifelse(is.na(clase_ternaria), NA_integer_,
  as.integer(clase_ternaria %in% c("BAJA+1", "BAJA+2")))]

#%% celda 58 [código]
dataset_train <- dataset[foto_mes %in% PARAM$train_final]
dataset_train[,.N,clase_ternaria]

#%% celda 59 [código]
dtrain_final <- lgb.Dataset(
  data=data.matrix(dataset_train[, ..campos_buenos]),
  label=dataset_train$clase01, free_raw_data=FALSE
)

# [Anotación · líneas 705–721] Arma param_final (hiperparámetros fijos más la configuración de mayor AUC) y
#   param_normalizado (una copia con min_data_in_leaf en 0) y muestra el primero. Ninguno de los dos se usa en
#   la celda de entrenamiento que sigue, que arma los parámetros de cada modelo por su cuenta.
#%% celda 60 [texto]
#### Final Training Hyperparameters

#%% celda 61 [código]
# Las configuraciones seleccionadas por AUC varían entre modelos.
param_final <- modifyList(PARAM$lgbm$param_fijos,
  PARAM$out$lgbm$mejores_hiperparametros)
param_final

#%% celda 62 [texto]
#### Training
Genero el modelo final, siempre sobre TODOS los datos de  final_train, sin hacer ningun tipo de undersampling de la clase mayoritaria y mucho menos cross validation.

#%% celda 63 [código]
# Sin corrección por undersampling, ya que NO hubo undersampling.
param_normalizado <- copy(param_final)
param_normalizado$min_data_in_leaf <- 0L

# [Anotación · líneas 723–750] Fija set.seed(170383) y sortea 10 semillas con sample.int(100000000, 10). Toma
#   los registros de 202108 como datos a predecir. En un ciclo de 10 pasos, el modelo i usa la configuración
#   número ((i - 1) módulo cantidad de configuraciones) + 1, la combina con los hiperparámetros fijos, le pone
#   la semilla i y min_data_in_leaf 0, entrena con 202103 a 202106 durante num_iterations rondas, predice 202108
#   y guarda el modelo como modelo_NN.txt. Al final graba modelos_semillas_configuraciones.tsv con la semilla y
#   la configuración de cada modelo.
#%% celda 64 [código]
# Entrenar 10 modelos con distintas semillas Y configuraciones de BO.
# El target y todas las features son idénticos en entrenamiento y scoring.
set.seed(PARAM$semilla_primigenia)
semillas_ensamble <- sample.int(100000000L, PARAM$n_modelos)
stopifnot(nrow(configuraciones_ensamble) >= 1L)
modelos_finales <- vector("list", PARAM$n_modelos)
dfuture <- dataset[foto_mes %in% PARAM$future]
stopifnot(nrow(dfuture) > 0L, !anyDuplicated(dfuture$numero_de_cliente))
matriz_futura <- data.matrix(dfuture[, ..campos_buenos])
predicciones <- matrix(NA_real_, nrow=nrow(dfuture), ncol=PARAM$n_modelos)
registro_modelos <- vector("list", PARAM$n_modelos)
for (i in seq_len(PARAM$n_modelos)) {
  cfg <- as.list(configuraciones_ensamble[((i - 1L) %% nrow(configuraciones_ensamble)) + 1L])
  p <- modifyList(PARAM$lgbm$param_fijos, cfg)
  p$seed <- as.integer(semillas_ensamble[i])
  p$min_data_in_leaf <- 0L
  niter <- as.integer(p$num_iterations)
  p$num_iterations <- NULL
  m <- lgb.train(params=p, data=dtrain_final,
                 nrounds=niter, verbose=-1)
  modelos_finales[[i]] <- m
  predicciones[, i] <- predict(m, matriz_futura)
  lgb.save(m, sprintf("modelo_%02d.txt", i))
  registro_modelos[[i]] <- as.data.table(c(list(modelo=i, seed=p$seed), cfg))
  cat(sprintf("Modelo %02d/%02d entrenado\n", i, PARAM$n_modelos))
}
fwrite(rbindlist(registro_modelos, fill=TRUE), "modelos_semillas_configuraciones.tsv", sep="\t")

# [Anotación · líneas 752–813] Vuelve a cargar desde disco los archivos modelo_01.txt a modelo_10.txt,
#   verifica que existan y no estén vacíos, y predice 202108 con cada uno sobre las mismas columnas
#   (campos_buenos), llenando una matriz de 10 columnas. No reutiliza la matriz de predicciones de la celda
#   anterior. Controla que todas las probabilidades sean finitas.
#%% celda 65 [código]

library(data.table)
library(lightgbm)

# =====================================================
# ENSAMBLE DE LOS 10 MODELOS GUARDADOS
# SIN REENTRENAMIENTO
# =====================================================

# Directorio donde se guardaron modelo_01.txt, etc.
directorio_modelos <- getwd()

archivos <- file.path(
  directorio_modelos,
  sprintf("modelo_%02d.txt", 1:10)
)

# Comprobar que existan los 10 modelos
stopifnot(
  all(file.exists(archivos)),
  all(file.info(archivos)$size > 0)
)

cat("Los 10 modelos fueron encontrados.\n")

# Recuperar clientes de agosto
dfuture <- dataset[foto_mes == 202108L]

stopifnot(
  nrow(dfuture) > 0L,
  !anyDuplicated(dfuture$numero_de_cliente)
)

# Exactamente las mismas features del entrenamiento
matriz_futura <- data.matrix(
  dfuture[, ..campos_buenos]
)

# Matriz de probabilidades
pred10 <- matrix(
  NA_real_,
  nrow = nrow(dfuture),
  ncol = 10L
)

for (i in 1:10) {

  cat("Prediciendo con modelo", i, "/10\n")

  modelo <- lgb.load(archivos[i])

  pred10[, i] <- predict(
    modelo,
    matriz_futura
  )

  rm(modelo)
  gc(verbose = FALSE)
}

stopifnot(all(is.finite(pred10)))

# [Anotación · líneas 815–850] Promedia por fila las 10 probabilidades (rowMeans) y graba
#   probabilidades_ensamble_10.csv.gz con cliente y probabilidad promedio. Graba también
#   probabilidades_individuales_10.csv.gz con la probabilidad de cada modelo.
# =====================================================
# ENSAMBLE: PROMEDIO DE LAS 10 PROBABILIDADES
# =====================================================

tb_prediccion10 <- data.table(
  numero_de_cliente = dfuture$numero_de_cliente,
  prob = rowMeans(pred10)
)

# Guardar probabilidades completas
fwrite(
  tb_prediccion10,
  "probabilidades_ensamble_10.csv.gz"
)

# Guardar tambien las predicciones individuales
pred_individuales <- as.data.table(pred10)

setnames(
  pred_individuales,
  paste0("modelo_", 1:10)
)

pred_individuales[
  , numero_de_cliente := dfuture$numero_de_cliente
]

setcolorder(
  pred_individuales,
  "numero_de_cliente"
)

fwrite(
  pred_individuales,
  "probabilidades_individuales_10.csv.gz"
)

# [Anotación · líneas 852–895] Ordena por probabilidad promedio descendente (y por numero_de_cliente ante
#   igualdad) y, para cada corte de 10000, 10500, 11000, 11500 y 12000, graba submit_ensamble10_<corte>.csv con
#   los primeros numero_de_cliente, sin encabezado. Los cortes están escritos en un vector local; no se lee
#   PARAM$cortes.
# =====================================================
# SUBMISSIONS CON DIFERENTES CORTES
# =====================================================

setorder(
  tb_prediccion10,
  -prob,
  numero_de_cliente
)

cortes <- c(
  10000L,
  10500L,
  11000L,
  11500L,
  12000L
)

for (corte in cortes) {

  stopifnot(nrow(tb_prediccion10) >= corte)

  archivo <- sprintf(
    "submit_ensamble10_%d.csv",
    corte
  )

  fwrite(
    tb_prediccion10[
      1:corte,
      .(numero_de_cliente)
    ],
    archivo,
    col.names = FALSE,
    quote = FALSE
  )

  cat(
    "Generado:", archivo,
    "| Clientes:", corte, "\n"
  )
}

cat("\nENSAMBLE DE 10 MODELOS FINALIZADO\n")

# [Anotación · líneas 897–901] Vuelve a escribir PARAM.yml, ahora en la carpeta de producción, e imprime fecha
#   y hora.
#%% celda 66 [código]
write_yaml( PARAM, file="PARAM.yml")

#%% celda 67 [código]
format(Sys.time(), "%a %b %d %X %Y")
```


## Explicaciones del alumno (texto original)

### README.md

> El colab genera, entre otros, un csv en drive en la carpeta Mi unidad / dmeyf / exp / expEntrega1Prueba1 / submit_ensamble10_11000.csv
>
> Ese es el csv de la entrega

