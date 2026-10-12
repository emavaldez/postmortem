# germandasr — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: germandasr
- Repositorio: https://github.com/germandasr/DMEyF---1ra-Competencia
- Link posteado: https://github.com/germandasr/DMEyF---1ra-Competencia
- Commit: f0ff0ad2eb2ea1e4428ec78a2bd0c11ead149a87
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/germandasr/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/germandasr.json

## Resumen

La entrega tiene dos notebooks de R, un README y dos archivos de resultados. Exp_51_entrega_final.ipynb parte del dataset crudo, calcula clase_ternaria, pasa ccajas_depositos a NA en 202105, agrega lag 1, lag 2, delta 1 y delta 2 de las variables originales y excluye cprestamos_personales y mprestamos_personales. Con las filas de 202103 y 202104, partidas al azar en 70% entrenamiento y 30% validación, corre una optimización bayesiana (mlr3mbo) de 10 evaluaciones sobre num_iterations, num_leaves y min_sum_hessian_in_leaf de LightGBM, con clase binaria (BAJA+1 o BAJA+2 = 1) y AUC como métrica. Con la fila de mayor métrica entrena 20 modelos, uno por semilla, sobre 202103 a 202106 sin submuestreo, predice 202108 y graba probabilidades_20_semillas.txt. Exp_51_ensamble_submit.ipynb promedia las 20 probabilidades, ordena de mayor a menor y escribe entrega_final.csv con los primeros 11.100 clientes. Según el README, ese archivo reproduce el CSV enviado como última entrega al bot.

**Qué entrega.** Un CSV de una columna sin encabezado con los 11.100 numero_de_cliente de mayor probabilidad promedio en 202108 (entrega_final.csv en el código). El repositorio incluye corte_11100_ENSAMBLE.csv (11.100 líneas, una columna de números de cliente; ni el README ni el código lo nombran) y probabilidades_20_semillas.txt (164.647 filas de 202108, 22 columnas).

**Cómo se ejecuta.** Según el README hay dos opciones. Opción rápida: con el probabilidades_20_semillas.txt provisto, correr Exp_51_ensamble_submit.ipynb, que genera entrega_final.csv. Opción completa: 1) correr Exp_51_entrega_final.ipynb de punta a punta, con competencia_01_crudo.csv en la ruta de la celda de setup (ajustando PARAM$data_dir), lo que genera BO_log.txt y probabilidades_20_semillas.txt; 2) correr Exp_51_ensamble_submit.ipynb en la misma carpeta. El README indica que el primer notebook tarda varias horas.

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase01): 1 si clase_ternaria es BAJA+1 o BAJA+2, 0 en otro caso. La clase_ternaria se calcula en el mismo notebook a partir del dataset crudo.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202103, 202104
- **Mes que predice:** 202108
- **Submuestreo:** No hay: en la optimización entra el 100% de las filas del fold de entrenamiento y en el modelo final todas las filas de los cuatro meses.
- **Calidad de datos:** Pasa ccajas_depositos a NA en 202105; el comentario indica que en ese mes la variable toma un único valor (0).
- **Drifting:** No aplica transformaciones a las variables. Excluye cprestamos_personales y mprestamos_personales; las celdas de texto del notebook dicen que cambian de distribución entre los meses de entrenamiento y el mes futuro. El README indica 'sin Ranking Cero Fijo'.
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** Lag 1 y lag 2 por cliente, y delta 1 y delta 2 (valor actual menos cada lag), de todas las columnas salvo numero_de_cliente, foto_mes, clase_ternaria, cprestamos_personales y mprestamos_personales.
- **Selección de variables:** Se quitan por nombre cprestamos_personales y mprestamos_personales (tampoco se generan sus lags ni deltas). No se observa otro mecanismo de selección; numero_de_cliente y foto_mes quedan en la lista de columnas del modelo.
- **Optimización de hiperparámetros:** Optimización bayesiana con bbotk y mlr3mbo (bayesopt_ego, sustituto kriging regr.km, adquisición expected improvement, búsqueda al azar de 1.000 evaluaciones sobre la adquisición), 10 evaluaciones, maximizando el AUC del 30% de validación. Espacio: num_iterations 64 a 4096, num_leaves 16 a 2048, min_sum_hessian_in_leaf 1e-06 a 0,1.
- **Hiperparámetros finales:** num_iterations, num_leaves y min_sum_hessian_in_leaf salen de la fila de mayor métrica de BO_log.txt; ese archivo no está en el repositorio y los valores no figuran en el código. Fijos: learning_rate 0,005, feature_fraction 0,50, min_data_in_leaf 0, max_bin 31, max_depth -1, lambda_l1 0, lambda_l2 0, bagging_fraction 1,0, boosting gbdt, objective binary.
- **Semillas:** Semilla primigenia 420029 para la partición y la optimización. Para el modelo final, 20 semillas escritas en el código: 420029, 425207, 420521, 420307, 420929, 500009, 523021, 546031, 569047, 592049, 615053, 638059, 661061, 684091, 707099, 730111, 753127, 776137, 799147 y 822161.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio aritmético sin ponderar (rowMeans) de las probabilidades de 20 modelos LightGBM con los mismos hiperparámetros y distinta semilla.
- **Corte:** Cantidad fija: los 11.100 clientes de mayor probabilidad promedio (CORTE_FINAL <- 11100). No se observa en el código cómo se eligió ese valor.
- **Validación:** Partición aleatoria, estratificada por clase_ternaria, de las filas de 202103 y 202104 en 70% entrenamiento y 30% validación (semilla 420029); la métrica es el AUC sobre el 30%. El modelo final se entrena sin conjunto de validación. No se calcula la ganancia de la competencia en ningún archivo.
- **Salidas:** competencia_01.csv.gz (dataset con clase_ternaria), BO_log.txt (registro de la optimización), prob_individuales/prediccion_semilla_<semilla>.txt (20 archivos), probabilidades_20_semillas.txt (22 columnas) y entrega_final.csv (una columna, sin encabezado, 11.100 clientes).

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: no
- Entorno declarado: No se declaran máquina ni sistema. Los metadatos de ambos notebooks registran el kernel 'R 4.5.3'. Los paquetes se instalan con install.packages() sin versión. El notebook principal usa rutas locales de Windows (C:/Users/germa/...) y un comentario indica que ya no hace falta Colab ni Drive; varias celdas de texto mencionan el runtime R de Google Colab.

## Pasos del camino de la entrega

1. **Rutas y generación de clase_ternaria.** Define la carpeta local de datos, lee competencia_01_crudo.csv, calcula para cada cliente los períodos de sus dos filas siguientes y asigna CONTINUA, BAJA+1 o BAJA+2; graba el resultado en competencia_01.csv.gz y muestra el conteo por mes y clase. (`Exp_51_entrega_final.ipynb` líneas 10–79)
2. **Parámetros de la corrida.** Después de limpiar el ambiente y cargar las librerías, define experimento Exp_51_entrega_final, semilla primigenia 420029, 70% de entrenamiento, meses de optimización 202103 y 202104, meses del modelo final 202103 a 202106, mes futuro 202108 y 10 iteraciones bayesianas. (`Exp_51_entrega_final.ipynb` líneas 139–157)
3. **Parámetros fijos y espacio de búsqueda de LightGBM.** Fija learning_rate 0,005, feature_fraction 0,50, min_data_in_leaf 0, max_bin 31, objective binary y metric auc, y define el espacio de búsqueda: num_iterations 64 a 4096, num_leaves 16 a 2048 y min_sum_hessian_in_leaf 1e-06 a 0,1. (`Exp_51_entrega_final.ipynb` líneas 160–215)
4. **Lectura del dataset y corrección de ccajas_depositos.** Crea la carpeta del experimento, lee competencia_01.csv.gz y pasa ccajas_depositos a NA en 202105. (`Exp_51_entrega_final.ipynb` líneas 266–285)
5. **Lags y deltas.** Sobre todos los meses, calcula por cliente lag 1 y lag 2 de cada columna (salvo identificadores, clase y las dos de préstamos personales) y las diferencias delta 1 y delta 2 contra esos lags. (`Exp_51_entrega_final.ipynb` líneas 287–304)
6. **Partición 70/30 de 202103 y 202104 y clase binaria.** Toma las filas de 202103 y 202104, las parte al azar en 70% y 30% de forma estratificada por clase_ternaria con la semilla 420029, crea clase01 (BAJA+1 o BAJA+2 = 1) y marca el fold 1 como entrenamiento, sin submuestreo. (`Exp_51_entrega_final.ipynb` líneas 306–333)
7. **Columnas del modelo.** Arma campos_buenos con todas las columnas menos clase_ternaria, clase01, fold y training, y quita cprestamos_personales y mprestamos_personales. (`Exp_51_entrega_final.ipynb` líneas 335–362)
8. **Función objetivo y conjuntos de entrenamiento y validación.** Define Estimar_lightgbm(), que entrena un LightGBM con los hiperparámetros recibidos, toma la métrica del conjunto de validación y la registra en BO_log.txt; construye los lgb.Dataset del 70% y del 30%. (`Exp_51_entrega_final.ipynb` líneas 375–426)
9. **Optimización bayesiana.** Configura mlr3mbo con sustituto kriging, adquisición expected improvement y terminación a las 10 evaluaciones, y ejecuta la optimización. (`Exp_51_entrega_final.ipynb` líneas 428–473)
10. **Elección de hiperparámetros y dataset final.** Lee BO_log.txt, toma la fila de mayor metrica, la superpone a los parámetros fijos y arma el dataset de entrenamiento final con 202103, 202104, 202105 y 202106. (`Exp_51_entrega_final.ipynb` líneas 490–517)
11. **Semillerío de 20 modelos y predicción de 202108.** Con 20 semillas escritas en el código, entrena un LightGBM por semilla sobre los cuatro meses, sin conjunto de validación, y predice la probabilidad de cada cliente de 202108. (`Exp_51_entrega_final.ipynb` líneas 519–556)
12. **Exportación de probabilidades.** Graba un archivo por semilla en prob_individuales/ y la tabla unificada probabilidades_20_semillas.txt con numero_de_cliente, foto_mes y las 20 columnas de probabilidad. (`Exp_51_entrega_final.ipynb` líneas 561–591)
13. **Ensamble por promedio.** El segundo notebook lee probabilidades_20_semillas.txt y calcula prob_ensamble como el promedio por fila de las columnas de probabilidad. (`Exp_51_ensamble_submit.ipynb` líneas 27–35)
14. **Corte en 11.100 clientes y archivo final.** Ordena por prob_ensamble de mayor a menor, toma los primeros 11.100 numero_de_cliente (CORTE_FINAL) y los graba en entrega_final.csv, una columna sin encabezado. (`Exp_51_ensamble_submit.ipynb` líneas 15–22; `Exp_51_ensamble_submit.ipynb` líneas 40–58)

## Archivos

- `Exp_51_entrega_final.ipynb` · principal · Jupyter (R) · 594 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/germandasr/Exp_51_entrega_final.ipynb.txt) — Notebook de R que va del dataset crudo a probabilidades_20_semillas.txt: genera clase_ternaria, crea lags y deltas, corre la optimización bayesiana de LightGBM sobre 202103 y 202104 y entrena 20 semillas sobre 202103 a 202106 para predecir 202108.
- `Exp_51_ensamble_submit.ipynb` · principal · Jupyter (R) · 61 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/germandasr/Exp_51_ensamble_submit.ipynb.txt) — Notebook de R que lee probabilidades_20_semillas.txt, promedia las 20 probabilidades por cliente, ordena de mayor a menor y graba entrega_final.csv con los primeros 11.100 numero_de_cliente.
- `README.md` · explicacion · Markdown · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/germandasr/README.md.txt) — Texto de presentación: resume la metodología (LightGBM con optimización bayesiana, lags y deltas, sin undersampling, semillerío de 20 semillas promediado), lista los tres archivos que describe, da dos formas de reproducir la entrega e indica que el corte está en la variable CORTE_FINAL.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### Exp_51_entrega_final.ipynb

Notebook de R que va del dataset crudo a probabilidades_20_semillas.txt: genera clase_ternaria, crea lags y deltas, corre la optimización bayesiana de LightGBM sobre 202103 y 202104 y entrena 20 semillas sobre 202103 a 202106 para predecir 202108.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Títulos del notebook y celda de rutas: fija PARAM$data_dir en una carpeta local de
#   Windows (C:/Users/germa/...), arma las rutas de competencia_01_crudo.csv (entrada) y competencia_01.csv.gz
#   (salida con la clase) y detiene la ejecución con stop() si el archivo crudo no existe.
#%% celda 1 [texto]
# **ENTREGA FINAL -- Exp_51 (BO) + Produccion Agosto, en un unico notebook self-contained**

#%% celda 2 [texto]
## 1. SETEOS INICIALES

#%% celda 3 [texto]
### 1.1  Seteo Ambiente Local

#%% celda 4 [código]
# Rutas locales (ya no hace falta Colab, Drive ni wget)
if (!exists("PARAM")) PARAM <- list()
PARAM$data_dir <- "C:/Users/germa/Desktop/Personal/Maestría/Data Mining/Primer Año/Data Mining en Economía y Finanzas/Clase1"

archivo_crudo    <- file.path(PARAM$data_dir, "competencia_01_crudo.csv")
archivo_ternaria <- file.path(PARAM$data_dir, "competencia_01.csv.gz")

if (!file.exists(archivo_crudo)) {
  stop("No encuentro el archivo crudo en: ", archivo_crudo)
}

# [Anotación · líneas 22–51] Carga data.table y lee el dataset crudo. Para cada fila calcula periodo0 (año ×
#   12 + mes), ordena por cliente y período, obtiene el último y el anteúltimo período del dataset y, dentro de
#   cada cliente, los períodos de sus dos filas siguientes (periodo1 y periodo2).
#%% celda 5 [texto]
### 1.2 Generacion de la clase_ternaria

#%% celda 6 [texto]
Esta parte se debe correr con el runtime en lenguaje **R** Ir al menu, Runtime -> Change Runtime Tipe -> Runtime type -> R

#%% celda 7 [código]
require( "data.table" )

# leo el dataset
dataset <- fread(archivo_crudo)

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


# calculo los leads de orden 1 y 2
dsimple[, c("periodo1", "periodo2") :=
    shift(periodo0, n=1:2, fill=NA, type="lead"),  numero_de_cliente ]

# [Anotación · líneas 53–75] Asigna clase_ternaria: CONTINUA a las filas anteriores al anteúltimo período;
#   BAJA+1 a las anteriores al último período cuyo cliente no tiene fila en el mes siguiente; BAJA+2 a las
#   anteriores al anteúltimo cuyo cliente tiene fila en el mes siguiente y no en el posterior. Las demás filas
#   quedan sin clase. Copia la columna al dataset en el orden original y lo graba como competencia_01.csv.gz.
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

# grabo local, en vez de /content/datasets/
fwrite( dataset,
    file = archivo_ternaria,
    sep = ","
)

# [Anotación · líneas 77–79] Ordena el dataset por foto_mes, clase_ternaria y numero_de_cliente y muestra la
#   cantidad de filas por mes y clase.
#%% celda 8 [código]
setorder( dataset, foto_mes, clase_ternaria, numero_de_cliente)
dataset[, .N, list(foto_mes, clase_ternaria)]

# [Anotación · líneas 81–99] Títulos de la sección de optimización bayesiana. Imprime fecha y hora, borra
#   todos los objetos del ambiente de R con rm(list=ls(all.names=TRUE)) y ejecuta el recolector de memoria.
#%% celda 9 [texto]
## 2 OPTIMIZACIÓN BAYESIANA

#%% celda 10 [texto]
Esta parte se debe correr con el runtime en lenguaje R Ir al menu, Runtime -> Change Runtime Type -> Runtime type -> R

#%% celda 11 [texto]
### 2.1 Inicio

#%% celda 12 [texto]
limpio el ambiente de R

#%% celda 13 [código]
format(Sys.time(), "%a %b %d %X %Y")

#%% celda 14 [código]
# limpio la memoria
rm(list=ls(all.names=TRUE)) # remove all objects
gc(full=TRUE, verbose=FALSE) # garbage collection

# [Anotación · líneas 101–130] Instala con install.packages() R.utils, rlist, bbotk, mlr3, mlr3mbo,
#   mlr3learners, DiceKriging y lightgbm, sin indicar versiones, y carga esas librerías junto con data.table.
#%% celda 15 [texto]
### 2.2 Carga de Librerias

#%% celda 16 [texto]
Esta parte lleva  demasiados   minutos la primera vez en Google Colab
<br> por suerte a partir del 15-septiembre empezaremos a trabajar con Google Cloud, en donde todas las librerias, de Python R y Julia ya estarán instaladas

#%% celda 17 [código]
# instalo paquetes
install.packages( c("R.utils", "rlist" ) )

#%% celda 18 [código]
# Librerias  modernas  para la Bayesian Optimization
install.packages( c("bbotk", "mlr3", "mlr3mbo", "mlr3learners", "DiceKriging") )

#%% celda 19 [código]
# el LightGBM
install.packages(c("lightgbm"))

#%% celda 20 [código]
library(data.table)
library(R.utils)
library(rlist)
library(bbotk)
library(mlr3)
library(mlr3mbo)
library(mlr3learners)
# library(paradox)
library(DiceKriging)
library(lightgbm)

# [Anotación · líneas 132–157] Crea la lista PARAM: experimento "Exp_51_entrega_final", semilla_primigenia
#   420029, training_pct 70, meses de la optimización 202103 y 202104 (train), meses del modelo final 202103 a
#   202106 (train_final), mes a predecir 202108 (future) y 10 iteraciones de optimización bayesiana. Los
#   comentarios indican que no se usa submuestreo y que no se definen cortes porque 202108 no tiene clase.
#%% celda 21 [texto]
### 2.2.3 Definicion de Parametros

#%% celda 22 [texto]
aqui debe cargar SU semilla primigenia
<br>recuerde cambiar el numero de experimento en cada corrida nueva

#%% celda 23 [código]
PARAM <- list()
PARAM$experimento <- "Exp_51_entrega_final"
PARAM$semilla_primigenia <-  420029

#%% celda 24 [código]
# training y future
PARAM$training_pct <- 70
PARAM$train <- c(202103, 202104)  # marzo + abril, como Exp_01
PARAM$train_final <- c(202103, 202104, 202105, 202106)  # marzo+abril+mayo+junio: todo lo conocido antes de agosto
PARAM$future <- c(202108)  # AGOSTO -- el mes real de la entrega
# PARAM$cortes: no aplica -- agosto no tiene clase_ternaria real, no hay curva de ganancia posible

#%% celda 25 [código]
# Sin undersampling (tip del profe: pocos meses, no hace falta reducir los CONTINUA)
# entra el 100% del fold de training, tanto en la BO como en la produccion final

#%% celda 26 [código]
PARAM$hyperparametertuning$iteraciones <- 10 # iteraciones bayesianas

# [Anotación · líneas 159–202] Define los parámetros fijos de LightGBM: boosting gbdt, objective binary,
#   metric auc, max_bin 31, max_depth -1, lambda_l1 y lambda_l2 en 0, bagging_fraction 1,0, min_data_in_leaf 0,
#   feature_fraction 0,50, learning_rate 0,005, early_stopping 0, seed igual a la semilla primigenia,
#   deterministic TRUE y force_row_wise TRUE. num_iterations (20000), num_leaves (1024) y
#   min_sum_hessian_in_leaf (1e-06) figuran con valores que luego se reemplazan por los de la optimización.
#%% celda 27 [código]
# Parametros LightGBM

# parametros fijos del LightGBM que se pisaran con la parte variable de la BO
PARAM$lgbm$param_fijos <-  list(
  boosting= "gbdt", # puede ir  dart  , ni pruebe random_forest
  objective= "binary",
  metric= "auc",
  feature_pre_filter= FALSE,
  first_metric_only= FALSE,
  boost_from_average= TRUE,
  force_row_wise= TRUE,
  deterministic= TRUE,
  verbosity= -100,

  seed= PARAM$semilla_primigenia,

  max_depth= -1L,
  min_gain_to_split= 0,
  lambda_l1= 0.0,
  lambda_l2= 0.0,
  max_bin= 31L,

  bagging_fraction= 1.0,
  pos_bagging_fraction= 1.0,
  neg_bagging_fraction= 1.0,
  is_unbalance= FALSE,
  scale_pos_weight= 1.0,

  drop_rate= 0.1,
  max_drop= 50,
  skip_drop= 0.5,

  extra_trees= FALSE,

  early_stopping= 0,
  min_data_in_leaf= 0,     # fijo, esto es FUNDAMENTAL
  feature_fraction= 0.50,  # fijo
  learning_rate= 0.005,    # fijo

  num_iterations= 20000,     # se modificara
  num_leaves= 1024,          # se modificara
  min_sum_hessian_in_leaf= 1e-06  # se modificara
)

# [Anotación · líneas 204–215] Define el espacio de búsqueda con ps(): num_iterations entero entre 64 y 4096,
#   num_leaves entero entre 16 y 2048 y min_sum_hessian_in_leaf real entre 1e-06 y 0,1.
#%% celda 28 [texto]
Aqui se definen los hiperparámetros de LightGBM que participan de la Bayesian Optimization

#%% celda 29 [código]
# Aqui se cargan los bordes de los hiperparametros de la BO
#  es vital entender que se optimiza min_sum_hessian_in_leaf y que  min_data_in_leaf se deja fijo en CERO

PARAM$hypeparametertuning$hs <- ps(
  num_iterations= p_int(lower= 64L,  upper= 4096L),
  num_leaves= p_int(lower= 16L,  upper= 2048L),
  min_sum_hessian_in_leaf= p_dbl( lower=1e-06, upper=0.1)
)

# [Anotación · líneas 217–230] Define particionar(): agrega al dataset una columna (por defecto fold) que
#   reparte las filas al azar en bloques con las proporciones de division, dentro de cada grupo de la columna
#   agrupa, fijando la semilla con el generador L'Ecuyer-CMRG.
#%% celda 30 [código]
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

# [Anotación · líneas 232–261] Define loguear(): agrega a un archivo de texto separado por tabuladores una
#   línea con fecha y hora y los valores del registro recibido; si el archivo no existe escribe antes la línea
#   de títulos. Con verbose imprime la línea por pantalla.
#%% celda 31 [código]
# logueo al archivo BO_log.txt
loguear  <- function( preg, arch=NA, verbose=TRUE )
{
  t0 <- Sys.time()
  reg <- copy( preg )
  if( "feature_contri" %in%  names(reg) ) {
    reg$feature_contri <- reg$feature_contri[1]
  }
  archivo <- arch
  if( is.na(arch) ) archivo <- paste0( folder, substitute( reg), ext )


  if( !file.exists( archivo ) )
  {
    # Escribo los titulos
    linea  <- paste0( "fecha\t",
                      paste( list.names(reg), collapse="\t" ), "\n" )

    cat( linea, file=archivo )
  }

  # escribo el registro
  linea  <- paste0( format(t0, "%Y%m%d.%H%M%S"),  "\t",     # la fecha y hora
                    gsub( ", ", "\t", toString( reg ) ),  "\n" )

  cat( linea, file=archivo, append=TRUE )  # grabo al archivo

  if( verbose )  cat( linea )   # imprimo por pantalla
}

# [Anotación · líneas 263–277] Fija PARAM$exp_dir en otra carpeta local de Windows, crea dentro la carpeta del
#   experimento y la pone como directorio de trabajo. Lee competencia_01.csv.gz desde una ruta completa escrita
#   en la celda, con las columnas de texto como factores.
#%% celda 32 [texto]
### 2.2.4  Preprocesamiento

#%% celda 33 [código]
# carpeta de trabajo
PARAM$exp_dir <- "C:/Users/germa/Desktop/Personal/Maestría/Data Mining/Primer Año/Data Mining en Economía y Finanzas/Competencia_1_Final"

setwd(PARAM$exp_dir)
dir.create(PARAM$experimento, showWarnings=FALSE)
setwd( file.path(PARAM$exp_dir, PARAM$experimento))

#%% celda 34 [código]
# lectura del dataset
archivo_ternaria <- "C:/Users/germa/Desktop/Personal/Maestría/Data Mining/Primer Año/Data Mining en Economía y Finanzas/Clase1/competencia_01.csv.gz"
dataset <- fread(archivo_ternaria, stringsAsFactors= TRUE)

# [Anotación · líneas 279–285] Reemplaza por NA los valores de ccajas_depositos en 202105; el comentario
#   indica que en ese mes la variable toma un único valor (0).
#%% celda 35 [texto]
#### Correccion de datos + Lag1/Lag2/Delta1/Delta2 (variables originales, SIN Ranking Cero Fijo)

#%% celda 36 [código]
# ===== Correccion de datos: ccajas_depositos colapsa a un unico valor (0) en 202105 =====
# (bug de carga, no efecto economico - visto en Exp_25 / Analisis_Estabilidad_Mensual)
dataset[foto_mes == 202105, ccajas_depositos := NA]

# [Anotación · líneas 287–304] Ordena por cliente y mes. Para todas las columnas salvo numero_de_cliente,
#   foto_mes, clase_ternaria, cprestamos_personales y mprestamos_personales calcula, dentro de cada cliente, el
#   valor de la fila anterior (_lag1) y el de dos filas atrás (_lag2) con shift(), y las diferencias entre el
#   valor actual y cada uno (_delta1 y _delta2). El cálculo abarca todos los meses del dataset.
# ===== LAG 1, LAG 2 y sus DELTA -- sobre TODO el dataset =====
setorder(dataset, numero_de_cliente, foto_mes)

campos_lagueables <- setdiff(colnames(dataset),
                              c("numero_de_cliente", "foto_mes", "clase_ternaria",
                                "cprestamos_personales", "mprestamos_personales"))

dataset[, paste0(campos_lagueables, "_lag1") := shift(.SD, 1, NA, "lag"),
        by = numero_de_cliente, .SDcols = campos_lagueables]
dataset[, paste0(campos_lagueables, "_lag2") := shift(.SD, 2, NA, "lag"),
        by = numero_de_cliente, .SDcols = campos_lagueables]

for (campo in campos_lagueables) {
  dataset[, paste0(campo, "_delta1") := get(campo) - get(paste0(campo, "_lag1"))]
  dataset[, paste0(campo, "_delta2") := get(campo) - get(paste0(campo, "_lag2"))]
}

gc(full = TRUE, verbose = FALSE)

# [Anotación · líneas 306–333] Toma las filas de 202103 y 202104, las divide con particionar() en 70% (fold 1)
#   y 30% (fold 2) de forma estratificada por clase_ternaria con la semilla 420029, crea clase01 (1 si la clase
#   es BAJA+1 o BAJA+2, 0 en otro caso) y marca training = 1 en las filas del fold 1, sin submuestrear.
#%% celda 37 [código]
dataset_train <- dataset[foto_mes %in% PARAM$train]

#%% celda 38 [código]
  particionar(dataset_train,
    division= c(PARAM$training_pct, 100L -PARAM$training_pct),
    agrupa= "clase_ternaria",
    seed= PARAM$semilla_primigenia # aqui se usa SU semilla
  )

#%% celda 39 [código]
# paso la clase a binaria que tome valores {0,1}  enteros
#  BAJA+1 y BAJA+2  son  1,   CONTINUA es 0
#  a partir de ahora ya NO puedo cortar  por prob(BAJA+2) > 1/40

dataset_train[,
  clase01 := ifelse(clase_ternaria %in% c("BAJA+2","BAJA+1"), 1L, 0L)
]

#%% celda 40 [código]
# defino los datos que forman parte del training
# SIN undersampling: entra el 100% del fold de training

dataset_train[, training := 0L]
dataset_train[
  foto_mes %in%  PARAM$train &  fold==1,
  training := 1L
]

# [Anotación · líneas 335–362] Arma campos_buenos, la lista de columnas del modelo: todas las de dataset_train
#   menos clase_ternaria, clase01, fold y training (numero_de_cliente y foto_mes quedan en la lista), y luego
#   quita cprestamos_personales y mprestamos_personales. Las celdas de texto intermedias dicen que esas dos
#   variables cambian de distribución entre los meses de entrenamiento y el mes futuro.
#%% celda 41 [código]
# los campos que se van a utilizar

campos_buenos <- setdiff(
  colnames(dataset_train),
  c("clase_ternaria", "clase01", "fold", "training")
)

#%% celda 42 [texto]
#### 2.2.4.1  Salsa Magica (dedicada a Laura Pasquini)

Los EDAs que estan haciendo los alumnos de los lunes son pura falopa, y de la mala. El uso de Agentes de la IA solo les empera el daño cerebral, generan pedf larguisimos, que no te dan ganas de leerlos, carentes de insights y alma.
<br>El unico EDA que tiene realmente sentido, en este caso, es comparar la distribución de cada variable de los meses donde se entrena (202103 a 202106) y el mes donde se va a aplicar el modelo (202108), buscando Data Drifting.
<br>Aun con los reales datos del futuro, donde no se tiene la clase, SIEMPRE se puede analizar el Data Drifting.
<br>Para las variables con distribuciones distintas se puede hacer:
* Transformar la variable para hacerla homogenea entre los dos periodos
* Eliminarla (es lo simple, que se eligió hacer en este caso)

#%% celda 43 [texto]
En esa exploracion gráfica del Data Drifting, se vio que estas variables cambian de distribucion entre los meses de entrenamiento y el mes futuro, y se decidió brutalmente eliminarlas
* cprestamos_personales
* mprestamos_personales


más adelantes, se utilizarán técnicas más inclusivas, y se preservaran dichas variables, transformadas.

#%% celda 44 [código]
campos_buenos <- setdiff( campos_buenos, c("cprestamos_personales", "mprestamos_personales") )

# [Anotación · líneas 364–373] Inicializa el contador de iteraciones giter en 0; si ya existe BO_log.txt en la
#   carpeta de trabajo, lo lee y continúa desde el mayor valor de iter.
#%% celda 45 [texto]
2.2.5 Configuracion Bayesian Optimization

#%% celda 46 [código]
giter <- 0

if( file.exists("BO_log.txt") ){
  tb_BO <- fread("BO_log.txt")
  giter <- tb_BO[, max(iter)]
}

# [Anotación · líneas 375–403] Define Estimar_lightgbm(), la función que evalúa cada punto de la optimización:
#   superpone los hiperparámetros recibidos a los fijos, entrena con lgb.train() sobre dtrain usando dvalidate
#   como conjunto de validación, toma modelo$best_score como métrica, registra parámetros, iteración y métrica
#   en BO_log.txt, vuelve a fijar la semilla y devuelve la métrica.
#%% celda 47 [código]
# En el argumento x llegan los parametros de la bayesiana

Estimar_lightgbm <- function(xs) {

  flush.console()
  giter <<- giter + 1

  # x pisa (o agrega) a param_fijos
  param_completo <- modifyList(PARAM$lgbm$param_fijos, xs)
  xx <- copy(param_completo)

  # entreno LightGBM
  modelo <- lgb.train(
    data= dtrain,
    valids= list( "val"=dvalidate),
    param= param_completo
  )


  # obtengo la ganancia
  xx$iter <- giter
  xx$metrica <- modelo$best_score

  loguear( xx, "BO_log.txt")
  set.seed(PARAM$semilla_primigenia, kind = "L'Ecuyer-CMRG")  # le reordeno a mlr3MBO

  return( list( metrica = xx$metrica) )
}

# [Anotación · líneas 405–426] Construye los lgb.Dataset de entrenamiento (filas con training = 1) y de
#   validación (training = 0) con las columnas de campos_buenos y clase01 como etiqueta, y muestra la cantidad
#   de filas y columnas de cada uno.
#%% celda 48 [código]
# dejo los datos de training en el formato que necesita LightGBM

dtrain <- lgb.Dataset(
  data= data.matrix(dataset_train[training == 1L, campos_buenos, with= FALSE]),
  label= dataset_train[training == 1L, clase01],
  free_raw_data= FALSE
)

nrow(dtrain)
ncol(dtrain)

#%% celda 49 [código]
# datos de validation en el formato que necesita LightGBM
dvalidate <- lgb.Dataset(
  data= data.matrix(dataset_train[training == 0L, campos_buenos, with= FALSE]),
  label= dataset_train[training == 0L, clase01],
  free_raw_data= FALSE
)

nrow(dvalidate)
ncol(dvalidate)

# [Anotación · líneas 428–467] Configura la optimización con bbotk y mlr3mbo: objetivo ObjectiveRFun que
#   maximiza metrica sobre el espacio definido, instancia de un solo criterio que termina a las 10 evaluaciones,
#   modelo sustituto de kriging (regr.km con BFGS y nugget estimado), función de adquisición expected
#   improvement, optimizador de la adquisición por búsqueda al azar (1.000 evaluaciones) y bucle bayesopt_ego.
#   Define kbayesiana ("bayesiana.RDATA"), nombre que no se vuelve a usar en el notebook.
#%% celda 50 [código]
# Aqui comienza la configuracion de la Bayesian Optimization

# en este archivo quedan la evolucion binaria de la BO
kbayesiana <- "bayesiana.RDATA"

funcion_optimizar <- Estimar_lightgbm # la funcion que voy a maximizar

objective <- ObjectiveRFun$new(
  fun= funcion_optimizar,
  domain= PARAM$hypeparametertuning$hs,
  codomain= ps(metrica = p_dbl(tags="maximize")),
  id= "BO_lightgbm"
)


instance <- OptimInstanceBatchSingleCrit$new(
  objective= objective,
  terminator=  trm("evals", n_evals = PARAM$hyperparametertuning$iteraciones)
)


surrogate <- srlrn(lrn("regr.km",
  optim.method = "BFGS",
  nugget.estim = TRUE,
  control= list(trace = FALSE)))

acq_function  <- acqf("ei")                 # expected improvement

acq_optimizer  <- acqo(
  optimizer  = opt("random_search", batch_size= 1000),
  terminator = trm("evals", n_evals= 1000)
)

optimizer <- opt("mbo",
  loop_function = bayesopt_ego,
  surrogate= surrogate,
  acq_function= acq_function,
  acq_optimizer= acq_optimizer
)

# [Anotación · líneas 469–476] Ejecuta la optimización con optimizer$optimize(instance). El texto indica que
#   las iteraciones quedan registradas en BO_log.txt.
#%% celda 51 [texto]
2.2.6 Corrida Bayesian Optimization

#%% celda 52 [código]
bayesiana_salida <- optimizer$optimize(instance)

#%% celda 53 [texto]
Luego de este punto, en la carpeta del experimento quedó el archivo BO_log.txt que posee todas las iteraciones de la Bayesian Optimization

# [Anotación · líneas 478–494] Inicio de la sección de producción: vuelve a ubicarse en la carpeta del
#   experimento, lee BO_log.txt, lo ordena por metrica de mayor a menor y guarda la primera fila completa como
#   lista en PARAM$out$lgbm$mejores_hiperparametros.
#%% celda 54 [texto]
## 2.3  Produccion

#%% celda 55 [texto]
### Final Training
Construyo el modelo final, que es uno solo, no hace ningun tipo de particion < training, validation, testing>]

#%% celda 56 [código]
setwd(PARAM$exp_dir)
dir.create(PARAM$experimento, showWarnings= FALSE)
setwd( file.path(PARAM$exp_dir, PARAM$experimento ))

#%% celda 57 [código]
 # cergo los mejores hiperparametros, que son los de mayor metrica
 tb_bayesiana <- fread("BO_log.txt")
 setorder( tb_bayesiana, -metrica )
 PARAM$out$lgbm$mejores_hiperparametros <- as.list(tb_bayesiana[1])

# [Anotación · líneas 496–517] Crea clase01 en todo el dataset, redefine dataset_train con las filas de
#   202103, 202104, 202105 y 202106 y muestra el conteo por mes y clase. Arma param_final superponiendo a los
#   parámetros fijos la fila elegida de BO_log.txt y lo muestra.
#%% celda 58 [texto]
#### Final Training Dataset

Aqui esta la gran decision de en qué meses hago el Final Training
<br> debo utilizar los mejores hiperparámetros que encontré en la  optimización bayesiana

#%% celda 59 [código]
# clase01
dataset[, clase01 := ifelse(clase_ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)]

#%% celda 60 [código]
dataset_train <- dataset[foto_mes %in% PARAM$train_final]
dataset_train[,.N, list(foto_mes, clase_ternaria)]

#%% celda 61 [texto]
#### Final Training Hyperparameters

#%% celda 62 [código]
param_final <- modifyList(PARAM$lgbm$param_fijos,
  PARAM$out$lgbm$mejores_hiperparametros)

param_final

# [Anotación · líneas 519–527] Define las 20 semillas del semillerío (420029, 425207, 420521, 420307, 420929 y
#   15 más entre 500009 y 822161), separa las filas de 202108 en dfuture y crea una matriz vacía de predicciones
#   con una columna por semilla.
#%% celda 63 [código]
# ===== SEMILLERIO: 20 semillas (5 habituales + 15 primos nuevos) =====
PARAM$semillerio <- c(420029, 425207, 420521, 420307, 420929,
                       500009, 523021, 546031, 569047, 592049,
                       615053, 638059, 661061, 684091, 707099,
                       730111, 753127, 776137, 799147, 822161)

dfuture <- dataset[foto_mes %in% PARAM$future]
predicciones <- matrix(nrow = nrow(dfuture), ncol = length(PARAM$semillerio))

# [Anotación · líneas 529–556] Para cada semilla: la pone en param_final$seed, arma el lgb.Dataset con todas
#   las filas de dataset_train (202103 a 202106) y las columnas de campos_buenos, entrena con lgb.train() sin
#   conjunto de validación, predice sobre dfuture y guarda las probabilidades en la columna correspondiente.
#   Imprime la duración de cada semilla y el tiempo transcurrido.
#%% celda 64 [código]
# Entreno los 20 modelos (mismos hiperparametros, solo cambia la semilla)

hora_inicio_semillerio <- Sys.time()

for (i in seq_along(PARAM$semillerio)) {

  t0_semilla <- Sys.time()
  param_final$seed <- PARAM$semillerio[i]

  dtrain_final <- lgb.Dataset(
    data= data.matrix(dataset_train[, campos_buenos, with= FALSE]),
    label= dataset_train[, clase01]
  )

  modelo_final <- lgb.train(
    data= dtrain_final,
    param= param_final
  )

  predicciones[, i] <- predict(modelo_final, data.matrix(dfuture[, campos_buenos, with= FALSE]))

  duracion_semilla <- round(difftime(Sys.time(), t0_semilla, units = "secs"), 1)
  transcurrido <- round(difftime(Sys.time(), hora_inicio_semillerio, units = "mins"), 1)
  cat(sprintf("[%s] semilla %d/%d (%d) lista - tardo %ss - transcurrido %smin\n",
              format(Sys.time(), "%H:%M:%S"), i, length(PARAM$semillerio),
              PARAM$semillerio[i], duracion_semilla, transcurrido))
}

# [Anotación · líneas 558–575] Crea la carpeta prob_individuales y graba un archivo por semilla,
#   prediccion_semilla_<semilla>.txt, con numero_de_cliente, foto_mes y prob, separado por tabuladores.
#%% celda 65 [texto]
### 3.1 Exportacion de probabilidades: una por semilla + tabla unificada (22 columnas)

#%% celda 66 [código]
dir.create("prob_individuales", showWarnings = FALSE)

# 1) un archivo por semilla (id, mes, prob)
for (i in seq_along(PARAM$semillerio)) {
  tb_i <- data.table(
    numero_de_cliente = dfuture$numero_de_cliente,
    foto_mes = dfuture$foto_mes,
    prob = predicciones[, i]
  )
  fwrite(tb_i,
    file = file.path("prob_individuales", sprintf("prediccion_semilla_%d.txt", PARAM$semillerio[i])),
    sep = "\t"
  )
}

# [Anotación · líneas 577–594] Arma una tabla con numero_de_cliente, foto_mes y una columna
#   prob_semilla_<semilla> por cada modelo (22 columnas), imprime la cantidad de columnas y la graba en
#   probabilidades_20_semillas.txt. Calcula prob_ensamble como promedio por fila de las 20 probabilidades, que
#   queda en memoria sin grabarse, e imprime fecha y hora.
# 2) unificacion: ID + MES + las 20 probabilidades = 22 columnas
tb_probabilidades <- data.table(
  numero_de_cliente = dfuture$numero_de_cliente,
  foto_mes = dfuture$foto_mes
)
for (i in seq_along(PARAM$semillerio)) {
  tb_probabilidades[, paste0("prob_semilla_", PARAM$semillerio[i]) := predicciones[, i]]
}

cat("Columnas de la tabla unificada:", ncol(tb_probabilidades), "\n")  # 2 + 20 = 22

fwrite(tb_probabilidades, file = "probabilidades_20_semillas.txt", sep = "\t")

# el ensamble (promedio simple) se calcula aparte, no se agrega como columna 23
prob_ensamble <- rowMeans(predicciones)

#%% celda 67 [código]
format(Sys.time(), "%a %b %d %X %Y")
```

### Exp_51_ensamble_submit.ipynb

Notebook de R que lee probabilidades_20_semillas.txt, promedia las 20 probabilidades por cliente, ordena de mayor a menor y graba entrega_final.csv con los primeros 11.100 numero_de_cliente.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–10] Celda de texto que indica que el notebook toma probabilidades_20_semillas.txt y
#   produce el archivo de una columna subido al bot, sin reentrenar. Carga data.table y desactiva la notación
#   científica con options(scipen = 999).
#%% celda 1 [texto]
# **Exp_51 -- Ensamble y seleccion de corte (genera el CSV final submiteado)**

Este notebook toma `probabilidades_20_semillas.txt` (generado por `Exp_51_entrega_final.ipynb`, o el que se provee junto a esta carpeta como atajo) y produce el archivo final de 1 columna que fue subido al bot de la competencia.

**No hace falta reentrenar nada para correr este notebook** -- alcanza con tener el archivo de probabilidades en la misma carpeta.

#%% celda 2 [código]
library(data.table)
options(scipen = 999)

# [Anotación · líneas 12–22] Parámetros: archivo de entrada probabilidades_20_semillas.txt, CORTE_FINAL 11100
#   (cantidad de clientes a enviar, ordenados por probabilidad descendente) y archivo de salida
#   entrega_final.csv.
#%% celda 3 [texto]
## Parametros

#%% celda 4 [código]
# archivo de probabilidades agrupadas (20 semillas), generado por Exp_51_entrega_final.ipynb
ARCHIVO_PROBABILIDADES <- "probabilidades_20_semillas.txt"

# CORTE elegido como entrega final -- cuantos clientes se envian, ordenados por probabilidad desc.
CORTE_FINAL <- 11100   # <-- EDITAR ACA con el corte definitivo que se decida

ARCHIVO_SALIDA <- "entrega_final.csv"

# [Anotación · líneas 24–35] Lee el archivo de probabilidades, toma como columnas de probabilidad todas menos
#   numero_de_cliente y foto_mes, imprime cuántas son y calcula prob_ensamble como el promedio por fila de esas
#   columnas, sin ponderar.
#%% celda 5 [texto]
## Lectura de probabilidades y armado del ensamble

#%% celda 6 [código]
tb <- fread(ARCHIVO_PROBABILIDADES)

# las columnas de probabilidad son todas menos numero_de_cliente y foto_mes
cols_prob <- setdiff(colnames(tb), c("numero_de_cliente", "foto_mes"))
cat("Cantidad de semillas/modelos en el ensamble:", length(cols_prob), "\n")

# ensamble = promedio simple de probabilidades (sin ponderar)
tb[, prob_ensamble := rowMeans(.SD), .SDcols = cols_prob]

# [Anotación · líneas 37–46] Ordena la tabla por prob_ensamble de mayor a menor, verifica que CORTE_FINAL no
#   supere la cantidad de filas y toma los numero_de_cliente de las primeras 11.100 filas.
#%% celda 7 [texto]
## Ranking por probabilidad y seleccion del corte

#%% celda 8 [código]
setorder(tb, -prob_ensamble)

stopifnot(CORTE_FINAL <= nrow(tb))

clientes_entrega <- as.integer(tb[1:CORTE_FINAL, numero_de_cliente])
cat("Clientes seleccionados:", length(clientes_entrega), "de", nrow(tb), "totales\n")

# [Anotación · líneas 48–58] Graba entrega_final.csv con esos números de cliente en una columna sin encabezado
#   e imprime el nombre del archivo y la cantidad de clientes.
#%% celda 9 [texto]
## Exportacion del CSV final (1 columna, sin header -- formato exigido por el bot)

#%% celda 10 [código]
fwrite(
  data.table(numero_de_cliente = clientes_entrega),
  file = ARCHIVO_SALIDA,
  col.names = FALSE
)

cat("Archivo final generado:", ARCHIVO_SALIDA, "con", length(clientes_entrega), "clientes\n")

# [Anotación · líneas 60–61] Celda marcada como código cuyo contenido es la frase "El ensemble mejor obtenido
#   es de 11100 clientes."; en el notebook original la celda conserva como salida un error de sintaxis de R.
#%% celda 11 [código]
El ensemble mejor obtenido es de 11100 clientes.
```


## Explicaciones del alumno (texto original)

### README.md

> # Entrega final -- DMEyF 2026, Primera Competencia
>
> Reproduce exactamente el archivo CSV enviado como última entrega al bot `competencia-uno`.
>
> ## Metodología
>
> LightGBM con Bayesian Optimization (mlr3/mlr3mbo), entrenado sobre variables originales +
> lag1/lag2/delta1/delta2 (sin Ranking Cero Fijo), sin undersampling. La BO se corre con
> marzo+abril (202103-202104, meses con `clase_ternaria` 100% real) como train/validation. El
> modelo final se entrena con marzo a junio (202103-202106, todo lo conocido antes de agosto) y
> predice sobre agosto (202108). Semillerío de 20 semillas, ensamble por promedio simple de
> probabilidades.
>
> ## Archivos
>
> | Archivo | Qué hace |
> |---|---|
> | `Exp_51_entrega_final.ipynb` | Notebook único y self-contained: desde el dataset crudo de la competencia hasta `probabilidades_20_semillas.txt` (corre la Bayesian Optimization y despues entrena las 20 semillas finales). Tarda varias horas en correr completo. |
> | `Exp_51_ensamble_submit.ipynb` | Toma `probabilidades_20_semillas.txt`, arma el ensamble (promedio simple de las 20 probabilidades) y genera `entrega_final.csv` -- el archivo exacto que se subió al bot. No necesita reentrenar nada. |
> | `probabilidades_20_semillas.txt` | Probabilidades ya calculadas (20 columnas, una por semilla) para agosto. Se provee como atajo, para poder correr `Exp_51_ensamble_submit.ipynb` directamente sin tener que correr `Exp_51_entrega_final.ipynb` (que tarda horas). |
>
> ## Cómo reproducir
>
> **Opción rápida (recomendada):** usar el `probabilidades_20_semillas.txt` ya provisto y correr
> directamente `Exp_51_ensamble_submit.ipynb`. Genera `entrega_final.csv` en segundos.
>
> **Opción completa (desde cero):**
> 1. Correr `Exp_51_entrega_final.ipynb` de punta a punta. Requiere el dataset crudo de la
>    competencia (`competencia_01_crudo.csv`) en la ruta indicada en la celda de setup inicial
>    (ajustar `PARAM$data_dir` según corresponda). Genera `BO_log.txt` y
>    `probabilidades_20_semillas.txt`.
> 2. Correr `Exp_51_ensamble_submit.ipynb` en la misma carpeta. Genera `entrega_final.csv`.
>
> ## Corte final
>
> El corte (cantidad de clientes a los que se les envía la oferta) está fijado en la variable
> `CORTE_FINAL` dentro de `Exp_51_ensamble_submit.ipynb`.

