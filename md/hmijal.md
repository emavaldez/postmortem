# hmijal — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: hmijal
- Repositorio: https://github.com/hmijal/dmeyf2026
- Link posteado: https://github.com/hmijal/dmeyf2026/tree/main/primera_competencia
- Commit: b322ec62a1afb98756065294154f293ca37aeed7
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/hmijal/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/hmijal.json

## Resumen

La entrega es la carpeta primera_competencia, con un notebook en R (primera_compe_2.ipynb) y un READ_ME.txt de dos líneas. El notebook lee competencia_01_crudo.csv.gz, calcula clase_ternaria, agrega a cada variable sus lags de orden 1 y 2 y los deltas contra cada lag, pasa a NA ccajas_depositos en 202105, crea tres sumas de tarjetas Visa y Master y reemplaza todas las variables por un ranking por mes que deja el cero fijo. Con clase binaria (positivo = BAJA+1 o BAJA+2) corre una optimización bayesiana de LightGBM con mlr3mbo sobre num_iterations, num_leaves y min_sum_hessian_in_leaf, entrenando en 202103 y 202104 y midiendo average_precision en 202106, sin las variables de préstamos personales. Con la configuración de mayor métrica entrena 20 modelos, uno por semilla, en 202103 a 202106 (con las variables de préstamos personales incluidas), predice 202108, promedia las 20 probabilidades y escribe 13 listas de clientes con cortes de 9.000 a 15.000 cada 500. El READ_ME.txt indica que la predicción final es HT4950-04_promedio_11000.csv.

**Qué entrega.** Un CSV sin encabezado con los 11.000 numero_de_cliente de mayor probabilidad promedio en 202108 (HT4950-04_promedio_11000.csv, según el READ_ME.txt). El notebook genera además los otros 12 cortes, las probabilidades por semilla y los 20 modelos guardados; ninguno de esos archivos está en el repositorio.

**Cómo se ejecuta.** El READ_ME.txt no indica qué ejecutar; sólo dice que, de los .csv generados al terminar el proceso, se use HT4950-04_promedio_11000.csv. Dentro del notebook, dos celdas de texto indican correr con el runtime en lenguaje R (Runtime -> Change Runtime Type -> R). Las celdas de montaje de Google Drive, creación de carpetas, descarga del dataset y la mayoría de las instalaciones de paquetes están comentadas (queda activa la instalación condicional de paradox).

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase01): 1 si clase_ternaria es BAJA+1 o BAJA+2, 0 en otro caso. clase_ternaria se calcula en el mismo notebook según la presencia del cliente en los dos meses siguientes.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica: la única línea sobre undersampling (PARAM$trainingstrategy$undersampling <- 1) está comentada y se entrena con todas las filas de los meses elegidos.
- **Calidad de datos:** Asigna NA a ccajas_depositos en 202105. La asignación se hace después de calcular lags y deltas y sólo sobre la columna original; las columnas ccajas_depositos_lag1, _lag2, _delta1 y _delta2 no se modifican en esa celda.
- **Drifting:** Reemplaza cada variable (originales, lags, deltas y las tres sumas z_) por un ranking calculado dentro de cada foto_mes: los ceros quedan en 0, los positivos pasan a rango denso dividido por su máximo (entre 0 y 1) y los negativos a un valor entre -1 y 0; los NA se mantienen. foto_mes no se transforma. Aparte, en la optimización bayesiana se quitan cprestamos_personales y mprestamos_personales con sus lags y deltas; para el modelo final se vuelven a incluir.
- **Variables dentro del mes:** Tres sumas Visa + Master: z_ctarjetas (cantidad de tarjetas), z_ctarjetas_transacciones (cantidad de transacciones) y z_mtarjetas_consumo (monto de consumo). Si los dos sumandos son NA el resultado es NA; si uno solo es NA se toma como 0.
- **Variables históricas:** Lag 1 y lag 2 de todas las columnas salvo numero_de_cliente, foto_mes y clase_ternaria, obtenidos uniendo la tabla consigo misma por cliente y un índice de mes consecutivo; delta 1 y delta 2 como diferencia entre el valor del mes y cada lag. Las tres sumas z_ se crean después y no tienen lags ni deltas. Según la salida guardada en el notebook original, el dataset abarca 202103 a 202108.
- **Selección de variables:** En la optimización bayesiana se excluyen a mano 10 columnas (cprestamos_personales, mprestamos_personales y sus _lag1, _lag2, _delta1, _delta2); según la salida guardada en el notebook original quedan 754 columnas. Para el entrenamiento final esas 10 columnas se vuelven a agregar a campos_buenos. foto_mes no figura entre las columnas quitadas de campos_buenos. No se observa selección por importancia.
- **Optimización de hiperparámetros:** Optimización bayesiana con mlr3mbo y bbotk (modelo sustituto regr.km de DiceKriging, función de adquisición expected improvement, búsqueda al azar de 1.000 evaluaciones para la adquisición) sobre num_iterations (64 a 4096), num_leaves (16 a 2048) y min_sum_hessian_in_leaf (1e-06 a 0,1). Terminador de 10 evaluaciones. Cada evaluación entrena en 202103 y 202104 y se maximiza average_precision en 202106. Según la salida guardada en el notebook original, se evaluaron 12 configuraciones.
- **Hiperparámetros finales:** Parámetros fijos del código (boosting gbdt, objective binary, learning_rate 0,005, feature_fraction 0,50, feature_fraction_bynode 0,20, max_bin 31, min_data_in_leaf 0, max_depth -1, lambda_l1 0, lambda_l2 0, bagging_fraction 1,0, early_stopping 0) pisados con la fila de mayor métrica de BO_log.txt. Según la salida guardada de la optimización en el notebook original: num_iterations 1744, num_leaves 97, min_sum_hessian_in_leaf 0,001204961, con average_precision 0,1882966 en 202106.
- **Semillas:** 20 semillas escritas en el código: 765461, 765487, 765497, 765503, 765521, 384157, 414857, 503857, 697757, 735157, 775777, 333331, 555557, 111119, 799999, 600013, 620003, 640007, 660007 y 680003. En cada modelo la semilla se asigna a seed, bagging_seed, feature_fraction_seed, drop_seed y data_random_seed. La optimización bayesiana usa la semilla 775777 (PARAM$semilla_primigenia).
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio por cliente de las probabilidades de los 20 modelos (rowMeans sobre las columnas prob_<semilla>); los 20 modelos comparten hiperparámetros y difieren en la semilla.
- **Corte:** Ordena por probabilidad promedio descendente y escribe una lista por cada corte de 9.000 a 15.000 cada 500 (13 cortes). El READ_ME.txt indica que la predicción final es el corte de 11.000. No se observa en el código activo cómo se elige ese corte; las celdas que calculan la ganancia por corte en 202106 están comentadas.
- **Validación:** Un mes posterior al entrenamiento: en la optimización bayesiana se entrena en 202103 y 202104 y se mide average_precision en 202106 (202105 no participa). Las celdas 70 a 78, que entrenan un modelo con la configuración de mayor métrica y calculan la ganancia acumulada en 202106 (1.072.500 por cada BAJA+2 y -27.500 por el resto) para los cortes de 9.000 a 15.000, están comentadas; sus salidas guardadas en el notebook original muestran 476.300.000 para 11.000 envíos y un máximo de 477.867.500 en 10.783 envíos.
- **Salidas:** En /content/buckets/b1/exp/HT4950-04/: BO_log.txt (una fila por evaluación de la optimización), modelo_semilla_<semilla>.txt (20 modelos), predicciones_agosto_20_semillas.csv (probabilidad de cada semilla por cliente), HT4950-04_promedio_<corte>.csv (13 listas de numero_de_cliente sin encabezado), HT4950-04_predicciones_promedio.csv y una copia del notebook como HT4950-04.ipynb. Además escribe /content/datasets/competencia_01.csv.gz con clase_ternaria.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Técnicas sólo exploradas

- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: no
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: sí
- Entorno declarado: No hay un texto que declare el entorno. Los títulos y las rutas del notebook refieren a Google Colab (/content/buckets/b1, montaje de Google Drive en celdas comentadas) y la última celda usa /home/ds/buckets/b1/dmeyf2026/primera_competencia. Los metadatos del notebook original indican kernel R (ir), versión 4.6.1. Carga data.table, R.utils, rlist, bbotk, mlr3, mlr3mbo, mlr3learners, DiceKriging, paradox y lightgbm, sin versiones.

## Pasos del camino de la entrega

1. **Lectura del dataset y cálculo de clase_ternaria.** Lee /content/buckets/b1/datasets/competencia_01_crudo.csv.gz, convierte foto_mes en un índice de mes consecutivo y calcula por cliente los dos meses siguientes. Asigna CONTINUA a los meses anteriores al anteúltimo, BAJA+1 cuando el cliente no aparece en el mes siguiente y BAJA+2 cuando aparece en el siguiente y no en el subsiguiente. Graba el resultado en /content/datasets/competencia_01.csv.gz. (`primera_competencia/primera_compe_2.ipynb` líneas 53–99)
2. **Lags de orden 1 y 2.** Para todas las columnas salvo numero_de_cliente, foto_mes y clase_ternaria arma dos copias de la tabla con el índice de mes corrido en +1 y +2 y las une a la tabla original por cliente e índice de mes, lo que agrega las columnas _lag1 y _lag2. (`primera_competencia/primera_compe_2.ipynb` líneas 123–195)
3. **Deltas contra cada lag.** Para cada variable original calcula _delta1 (valor del mes menos _lag1) y _delta2 (valor del mes menos _lag2) y reordena las columnas en grupos de cinco por variable. (`primera_competencia/primera_compe_2.ipynb` líneas 206–245)
4. **Corrección de ccajas_depositos y sumas de tarjetas.** Asigna NA a ccajas_depositos en 202105 y crea z_ctarjetas, z_ctarjetas_transacciones y z_mtarjetas_consumo como suma de las columnas de Visa y Master correspondientes, con NA cuando ambas son NA. (`primera_competencia/primera_compe_2.ipynb` líneas 250–287)
5. **Ranking por mes con cero fijo.** Recorre todas las columnas salvo numero_de_cliente, foto_mes y clase_ternaria y, dentro de cada foto_mes, reemplaza los valores: 0 queda en 0, los positivos pasan a rango denso dividido por el rango máximo y los negativos a (rango - rango máximo - 1) dividido por el rango máximo; los NA quedan como NA. (`primera_competencia/primera_compe_2.ipynb` líneas 292–327)
6. **Parámetros de la corrida.** Define el experimento HT4950-04, la semilla 775777, los meses (train 202103 y 202104, validate 202106, train_final 202103 a 202106, future 202108), 10 iteraciones para la optimización, los parámetros fijos de LightGBM y los rangos de los tres hiperparámetros que se optimizan. (`primera_competencia/primera_compe_2.ipynb` líneas 398–419; `primera_competencia/primera_compe_2.ipynb` líneas 422–467; `primera_competencia/primera_compe_2.ipynb` líneas 473–487)
7. **Dataset de la optimización.** Filtra 202103, 202104 y 202106, crea clase01 (1 para BAJA+1 y BAJA+2) y la marca training (1 para 202103 y 202104). Arma campos_buenos con todas las columnas salvo numero_de_cliente, clase_ternaria, clase01, fold, azar y training, y le quita las 10 columnas de préstamos personales. Construye dtrain (202103 y 202104) y dvalidate (202106) como lgb.Dataset. (`primera_competencia/primera_compe_2.ipynb` líneas 531–587; `primera_competencia/primera_compe_2.ipynb` líneas 631–647)
8. **Optimización bayesiana.** La función objetivo entrena un LightGBM con los parámetros fijos pisados por los propuestos, toma modelo$best_score sobre dvalidate (average_precision) y registra la evaluación en BO_log.txt. La optimización se configura con mlr3mbo (regr.km, expected improvement, terminador de 10 evaluaciones) y se ejecuta con optimizer$optimize(instance). (`primera_competencia/primera_compe_2.ipynb` líneas 600–628; `primera_competencia/primera_compe_2.ipynb` líneas 671–715)
9. **Hiperparámetros elegidos y dataset final.** Lee BO_log.txt, lo ordena por métrica descendente y guarda la primera fila como PARAM$out$lgbm$mejores_hiperparametros. Crea clase01 en todo el dataset, separa dataset_train (202103 a 202106) y dfuture (202108) y vuelve a agregar a campos_buenos las 10 columnas de préstamos personales. (`primera_competencia/primera_compe_2.ipynb` líneas 847–889)
10. **Entrenamiento con 20 semillas y predicción de 202108.** Para cada una de las 20 semillas arma los parámetros (fijos más los elegidos), asigna la semilla a los cinco parámetros de semilla de LightGBM, entrena sobre dataset_train, guarda el modelo en modelo_semilla_<semilla>.txt y agrega la probabilidad predicha para 202108 como columna prob_<semilla>. Al terminar graba predicciones_agosto_20_semillas.csv. (`primera_competencia/primera_compe_2.ipynb` líneas 914–991)
11. **Promedio de semillas y listas por corte.** Promedia por cliente las columnas prob_<semilla>, ordena de mayor a menor y, para cada corte de 9.000 a 15.000 cada 500, escribe HT4950-04_promedio_<corte>.csv con los numero_de_cliente de las primeras filas, sin encabezado. Graba también HT4950-04_predicciones_promedio.csv. El READ_ME.txt señala el archivo de 11.000 como la predicción final. (`primera_competencia/primera_compe_2.ipynb` líneas 1111–1177; `primera_competencia/READ_ME.txt` líneas 1–2)
12. **Copia del notebook a la carpeta del experimento.** Busca el único .ipynb de /home/ds/buckets/b1/dmeyf2026/primera_competencia y lo copia a /content/buckets/b1/exp/HT4950-04/HT4950-04.ipynb; si encuentra una cantidad distinta de uno, se detiene. (`primera_competencia/primera_compe_2.ipynb` líneas 1218–1271)

## Archivos

- `primera_competencia/primera_compe_2.ipynb` · principal · Jupyter (R) · 1271 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/hmijal/primera_competencia/primera_compe_2.ipynb.txt) — Notebook en R que va desde la lectura del dataset crudo hasta las listas de clientes: clase_ternaria, lags, deltas, ranking por mes, optimización bayesiana de LightGBM, 20 modelos por semilla, promedio y cortes.
- `primera_competencia/READ_ME.txt` · explicacion · Texto · 2 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/hmijal/primera_competencia/READ_ME.txt.txt) — Dos líneas: indica que, de los .csv que se generan al terminar el proceso, se use HT4950-04_promedio_11000.csv, y que ese archivo es el último que se subió a Zulip como predicción final.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### primera_competencia/primera_compe_2.ipynb

Notebook en R que va desde la lectura del dataset crudo hasta las listas de clientes: clase_ternaria, lags, deltas, ranking por mes, optimización bayesiana de LightGBM, 20 modelos por semilla, promedio y cortes.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–46] Título y celdas de preparación del ambiente en Google Colab: montaje de Google
#   Drive, creación de /content/buckets/b1 con las carpetas exp y datasets, y una función descargar() que baja
#   competencia_01_crudo.csv. Todo el código de las celdas 4 y 5 está comentado.
#%% celda 1 [texto]
# LightGBM  Optimizacion Bayesiana

#%% celda 2 [texto]
#### 2.1  Seteo del ambiente en Google Colab

#%% celda 3 [texto]
Conectar la virtual machine donde esta corriendo Google Colab con el  Google Drive, para poder tener persistencia de archivos

#%% celda 4 [código]
# # primero establecer el Runtime de Python 3
# from google.colab import drive
# drive.mount('/content/.drive')

#%% celda 5 [código]
# %%shell

# mkdir -p "/content/.drive/My Drive/dmeyf"
# mkdir -p "/content/buckets"
# ln -sfn  "/content/.drive/My Drive/dmeyf" /content/buckets/b1


# mkdir -p /content/buckets/b1/exp
# mkdir -p /content/buckets/b1/datasets
# mkdir -p /content/datasets


# # defino funcion descargar()
# descargar() {
#   carpeta_destino="/content/buckets/b1/datasets/"
#   url_origen="https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/"
#   archivo="$1"

#   if ! test -f "$carpeta_destino""$archivo"; then
#     wget  "$url_origen""$archivo"  -O "$carpeta_destino""$archivo"
#   fi

#   if ! test -f  "/content/datasets/""$archivo"; then
#     cp  "$carpeta_destino""$archivo"  "/content/datasets/""$archivo"
#   fi;
# }


# # hago la descarga efectiva, llamando a descargar()
# descargar  "competencia_01_crudo.csv"

# [Anotación · líneas 47–99] Lee competencia_01_crudo.csv.gz, calcula periodo0 (año por 12 más mes) y, por
#   cliente, los dos periodos siguientes con shift tipo lead. Asigna CONTINUA a los periodos anteriores al
#   anteúltimo, BAJA+1 si falta el periodo siguiente y BAJA+2 si está el siguiente y falta el subsiguiente. Pega
#   clase_ternaria al dataset en su orden original y lo graba en /content/datasets/competencia_01.csv.gz.
#%% celda 6 [texto]
## Generacion de la clase_ternaria

#%% celda 7 [texto]
Esta parte se debe correr con el runtime en lenguaje **R** Ir al menu, Runtime -> Change Runtime Tipe -> Runtime type -> R

#%% celda 8 [código]
require( "data.table" )

# leo el dataset
dataset <- fread("/content/buckets/b1/datasets/competencia_01_crudo.csv.gz" )

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

# [Anotación · líneas 101–118] Celdas de inspección: cantidad de filas por foto_mes y clase_ternaria, primeras
#   filas, nombres de columnas, filas por foto_mes y estructura del dataset.
#%% celda 9 [código]
setorder( dataset, foto_mes, clase_ternaria, numero_de_cliente)
dataset[, .N, list(foto_mes, clase_ternaria)]

#%% celda 10 [texto]
### 2.2.2 Generación de nuevas columnas

#%% celda 11 [código]
head(dataset)

#%% celda 12 [código]
colnames(dataset)

#%% celda 13 [código]
dataset[, .N, by = foto_mes]

#%% celda 14 [código]
str(dataset)

# [Anotación · líneas 120–201] Sobre una copia del dataset crea periodo_idx (índice de mes consecutivo) y dos
#   tablas con todas las columnas salvo numero_de_cliente, foto_mes y clase_ternaria renombradas a _lag1 y
#   _lag2, con periodo_idx corrido en +1 y +2. Las une a la tabla base por numero_de_cliente y periodo_idx
#   (unión por izquierda), restaura el orden original, quita las columnas auxiliares e intercala cada variable
#   con sus dos lags. Las celdas 17 y 18 muestran la dimensión y 20 filas ordenadas por cliente y mes.
#%% celda 15 [texto]
Creo los LAG DE ORDEN 1 Y 2

#%% celda 16 [código]

#library(data.table)

# 1. Trabajamos con una copia y guardamos el orden original
base <- copy(dataset)
base[, fila_original := .I]

# 2. Convertimos foto_mes a un índice mensual consecutivo
base[, periodo_idx := (foto_mes %/% 100) * 12 + foto_mes %% 100]

# 3. Identificamos las columnas que queremos desplazar
columnas <- setdiff(
  names(dataset),
  c("numero_de_cliente", "foto_mes","clase_ternaria")
)

# 4. Creamos las variables lag1
lag1 <- base[, c("numero_de_cliente", "periodo_idx", columnas),
             with = FALSE]

setnames(lag1, columnas, paste0(columnas, "_lag1"))
lag1[, periodo_idx := periodo_idx + 1L]

# 5. Creamos las variables lag2
lag2 <- base[, c("numero_de_cliente", "periodo_idx", columnas),
             with = FALSE]

setnames(lag2, columnas, paste0(columnas, "_lag2"))
lag2[, periodo_idx := periodo_idx + 2L]

# 6. Unimos los valores históricos con el dataset original
resultado <- merge(
  base, lag1,
  by = c("numero_de_cliente", "periodo_idx"),
  all.x = TRUE, sort = FALSE
)

resultado <- merge(
  resultado, lag2,
  by = c("numero_de_cliente", "periodo_idx"),
  all.x = TRUE, sort = FALSE
)

# 7. Recuperamos el orden original
setorder(resultado, fila_original)

# 8. Quitamos las columnas auxiliares
resultado[, c("fila_original", "periodo_idx") := NULL]

# 9. Ordeno las columnas

# Excluir columnas que no queremos desplazar
columnas <- setdiff(
  names(dataset),
  c("numero_de_cliente", "foto_mes", "clase_ternaria")
)

# Orden intercalado: original, lag1, lag2
orden_columnas <- c(
  "numero_de_cliente",
  "foto_mes",
  unlist(lapply(columnas, function(col) {
    c(col, paste0(col, "_lag1"), paste0(col, "_lag2"))
  })),
  "clase_ternaria"
)

# Aplicar el orden
resultado <- resultado[, ..orden_columnas]

# 9. Actualizamos el dataset
dataset <- resultado

#%% celda 17 [código]
dim(dataset)

#%% celda 18 [código]
dataset[order(numero_de_cliente, foto_mes)][1:20]

# [Anotación · líneas 203–248] Para cada variable original (las que no terminan en _lag1, _lag2, _delta1 o
#   _delta2) crea _delta1 = valor - _lag1 y _delta2 = valor - _lag2. Reordena las columnas en el orden variable,
#   _lag1, _lag2, _delta1, _delta2 y muestra las primeras filas.
#%% celda 19 [texto]
Creo los DELTA LAG de orden 1 y 2

#%% celda 20 [código]

# 1. Identificar las variables originales (excluyendo IDs, clase y lags)
columnas <- setdiff(
  names(dataset),
  c("numero_de_cliente", "foto_mes", "clase_ternaria")
)

columnas <- columnas[!grepl("_(lag1|lag2|delta1|delta2)$", columnas)]

# 2. Crear delta1 y delta2
for (col in columnas) {
  dataset[, paste0(col, "_delta1") :=
            get(col) - get(paste0(col, "_lag1"))]

  dataset[, paste0(col, "_delta2") :=
            get(col) - get(paste0(col, "_lag2"))]
}

# 3. Ordenar las columnas
orden_columnas <- c(
  "numero_de_cliente",
  "foto_mes",
  unlist(lapply(columnas, function(col) {
    c(
      col,
      paste0(col, "_lag1"),
      paste0(col, "_lag2"),
      paste0(col, "_delta1"),
      paste0(col, "_delta2")
    )
  })),
  "clase_ternaria"
)

# 4. Aplicar el orden
dataset <- dataset[, ..orden_columnas]

# 5. Verificar el resultado
head(dataset[, 1:12, with = FALSE])

#%% celda 21 [código]
dataset[order(numero_de_cliente, foto_mes)][1:20]

# [Anotación · líneas 250–253] Asigna NA a ccajas_depositos en las filas de foto_mes 202105. Las columnas
#   derivadas de esa variable, ya creadas en las celdas anteriores, no se tocan aquí.
#%% celda 22 [código]
# Reemplazo los 0 que están mal por NA en 202105 del campo ccajas_depositos

dataset[foto_mes == 202105, ccajas_depositos := NA_real_]

# [Anotación · líneas 255–287] Crea tres variables como suma de Visa y Master: z_ctarjetas (ctarjeta_visa +
#   ctarjeta_master), z_ctarjetas_transacciones (cantidades de transacciones) y z_mtarjetas_consumo (montos de
#   consumo). Si las dos columnas son NA el resultado es NA; si una sola es NA se reemplaza por 0 antes de
#   sumar.
#%% celda 23 [código]
# z_ctarjetas suma la cantidad de tarjetas de crédito visa y master

dataset[, z_ctarjetas :=
  fifelse(
    is.na(ctarjeta_visa) & is.na(ctarjeta_master),
    NA_real_,
    fifelse(is.na(ctarjeta_visa), 0, ctarjeta_visa) +
    fifelse(is.na(ctarjeta_master), 0, ctarjeta_master)
  )
]


# z_ctarjetas_transacciones suma la cantidad de transcacciones de las tarjetas de crédito visa y master
dataset[, z_ctarjetas_transacciones :=
  fifelse(
    is.na(ctarjeta_visa_transacciones) & is.na(ctarjeta_master_transacciones),
    NA_real_,
    fifelse(is.na(ctarjeta_visa_transacciones), 0, ctarjeta_visa_transacciones) +
    fifelse(is.na(ctarjeta_master_transacciones), 0, ctarjeta_master_transacciones)
  )
]


# z_mtarjetas_consumo suma llos montos de consumo de las tarjetas visa y master
dataset[, z_mtarjetas_consumo :=
  fifelse(
    is.na(mtarjeta_visa_consumo) & is.na(mtarjeta_master_consumo),
    NA_real_,
    fifelse(is.na(mtarjeta_visa_consumo), 0, mtarjeta_visa_consumo) +
    fifelse(is.na(mtarjeta_master_consumo), 0, mtarjeta_master_consumo)
  )
]

# [Anotación · líneas 289–343] Para cada columna salvo numero_de_cliente, foto_mes y clase_ternaria, la
#   convierte a numérica y la reemplaza, dentro de cada foto_mes, por un ranking: 0 queda en 0; los positivos
#   reciben rango denso (frank) dividido por el rango máximo, entre 0 y 1; los negativos reciben (rango - rango
#   máximo - 1) / rango máximo, entre -1 y 0; los NA se conservan. Luego muestra Master_Finiciomora con sus lags
#   y deltas, 20 filas al azar y la historia del cliente 63791172.
#%% celda 24 [texto]
Calculo los RANKINGS de todas las variables

#%% celda 25 [código]

# 1. Identificar todas las variables a transformar
excluir <- c("numero_de_cliente", "foto_mes", "clase_ternaria")
columnas <- setdiff(names(dataset), excluir)

# 2. Ranking por mes, manteniendo el cero
for (col in columnas) {

  # Convertir la columna a double ANTES de modificarla
  set(dataset, j = col, value = as.numeric(dataset[[col]]))

  dataset[, (col) := {
    x <- get(col)
    resultado <- rep(NA_real_, .N)

    # Ceros
    resultado[!is.na(x) & x == 0] <- 0

    # Positivos: de 0 a 1
    pos <- which(!is.na(x) & x > 0)
    if (length(pos) > 0) {
      r <- frank(x[pos], ties.method = "dense")
      resultado[pos] <- r / max(r)
    }

    # Negativos: de -1 a 0
    neg <- which(!is.na(x) & x < 0)
    if (length(neg) > 0) {
      r <- frank(x[neg], ties.method = "dense")
      resultado[neg] <- (r - max(r) - 1) / max(r)
    }

    resultado
  }, by = foto_mes]
}

# 3. Comprobar el resultado
head(dataset[, .(
  foto_mes,
  Master_Finiciomora,
  Master_Finiciomora_lag1,
  Master_Finiciomora_lag2,
  Master_Finiciomora_delta1,
  Master_Finiciomora_delta2
)])

#%% celda 26 [código]
dataset[sample(.N, 20)]

#%% celda 27 [código]
dataset[numero_de_cliente == 63791172][order(foto_mes)]

# [Anotación · líneas 345–389] Encabezados de la sección de optimización, impresión de fecha y hora, celdas
#   comentadas con install.packages (R.utils, rlist, bbotk, mlr3, mlr3mbo, mlr3learners, DiceKriging, lightgbm)
#   y carga de las librerías data.table, R.utils, rlist, bbotk, mlr3, mlr3mbo, mlr3learners, DiceKriging y
#   lightgbm.
#%% celda 28 [texto]
## 2.2 Optimizacion Hiperparámetros

#%% celda 29 [texto]
Esta parte se debe correr con el runtime en lenguaje R Ir al menu, Runtime -> Change Runtime Type -> Runtime type -> R

#%% celda 30 [texto]
### 2.2.1 Inicio

#%% celda 31 [texto]
limpio el ambiente de R

#%% celda 32 [código]
format(Sys.time(), "%a %b %d %X %Y")

#%% celda 33 [texto]
### 2.2.2 Carga de Librerias

#%% celda 34 [texto]
Esta parte lleva  demasiados   minutos la primera vez en Google Colab
<br> por suerte a partir del 15-septiembre empezaremos a trabajar con Google Cloud, en donde todas las librerias, de Python R y Julia ya estarán instaladas

#%% celda 35 [código]
# # instalo paquetes
# install.packages( c("R.utils", "rlist" ) )

#%% celda 36 [código]
# # Librerias  modernas  para la Bayesian Optimization
# install.packages( c("bbotk", "mlr3", "mlr3mbo", "mlr3learners", "DiceKriging") )

#%% celda 37 [código]
# # el LightGBM
# install.packages(c("lightgbm"))

#%% celda 38 [código]
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

# [Anotación · líneas 391–419] Parámetros de la corrida en la lista PARAM: experimento HT4950-04,
#   semilla_primigenia 775777, training_pct 70 (no se usa en el resto del notebook), train 202103 y 202104,
#   validate 202106, train_final 202103 a 202106, future 202108, cortes de 9.000 a 15.000 cada 500 e iteraciones
#   bayesianas 10. La línea de undersampling está comentada.
#%% celda 39 [texto]
### 2.2.3 Definicion de Parametros

#%% celda 40 [texto]
aqui debe cargar SU semilla primigenia
<br>recuerde cambiar el numero de experimento en cada corrida nueva

#%% celda 41 [código]
PARAM <- list()
PARAM$experimento <- "HT4950-04"
PARAM$semilla_primigenia <-  775777

#%% celda 42 [código]
# training y future
PARAM$training_pct <- 70
PARAM$train <- c(202103,202104)
PARAM$validate <- c(202106)
PARAM$train_final <- c(202103,202104,202105,202106)
PARAM$future <- c(202108)
PARAM$cortes <- seq(9000, 15000, by= 500)

#%% celda 43 [código]
# # un undersampling de 0.1  toma solo el 10% de los CONTINUA
# # undersampling de 1.0  implica tomar TODOS los datos

# PARAM$trainingstrategy$undersampling <- 1

#%% celda 44 [código]
PARAM$hyperparametertuning$iteraciones <- 10 # iteraciones bayesianas

# [Anotación · líneas 421–467] Parámetros fijos de LightGBM: boosting gbdt, objective binary, metric
#   average_precision, deterministic TRUE, seed 775777, max_depth -1, lambda_l1 y lambda_l2 en 0, max_bin 31,
#   fracciones de bagging en 1,0, is_unbalance FALSE, scale_pos_weight 1,0, early_stopping 0, min_data_in_leaf
#   0, feature_fraction 0,50, learning_rate 0,005 y feature_fraction_bynode 0,20. num_iterations 20000,
#   num_leaves 1024 y min_sum_hessian_in_leaf 1e-06 son los valores que la optimización reemplaza.
#%% celda 45 [código]
# Parametros LightGBM

# parametros fijos del LightGBM que se pisaran con la parte variable de la BO
PARAM$lgbm$param_fijos <-  list(
  boosting= "gbdt", # puede ir  dart  , ni pruebe random_forest
  objective= "binary",
  metric= "average_precision",
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

  feature_fraction_bynode = 0.20, # lo agregué yo
  

  num_iterations= 20000,     # se modificara
  num_leaves= 1024,          # se modificara
  min_sum_hessian_in_leaf= 1e-06  # se modificara
)

# [Anotación · líneas 469–487] Instala paradox si no está y lo carga. Define el espacio de búsqueda en
#   PARAM$hypeparametertuning$hs: num_iterations entero entre 64 y 4096, num_leaves entero entre 16 y 2048 y
#   min_sum_hessian_in_leaf real entre 1e-06 y 0,1.
#%% celda 46 [texto]
Aqui se definen los hiperparámetros de LightGBM que participan de la Bayesian Optimization

#%% celda 47 [código]
# Aqui se cargan los bordes de los hiperparametros de la BO
#  es vital entender que se optimiza min_sum_hessian_in_leaf y que  min_data_in_leaf se deja fijo en CERO
# Instalar si todavía no está instalado
if (!requireNamespace("paradox", quietly = TRUE)) {
  install.packages("paradox")
}

# Cargar el paquete
library(paradox)

PARAM$hypeparametertuning$hs <- ps(
  num_iterations= p_int(lower= 64L,  upper= 4096L),
  num_leaves= p_int(lower= 16L,  upper= 2048L),
  min_sum_hessian_in_leaf= p_dbl( lower=1e-06, upper=0.1)
)

# [Anotación · líneas 489–518] Función loguear(): agrega al archivo indicado una línea separada por
#   tabuladores con fecha y hora y los valores de la lista recibida; si el archivo no existe escribe antes la
#   línea de títulos. En el notebook se la llama con el archivo BO_log.txt.
#%% celda 48 [código]
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

# [Anotación · líneas 520–552] Crea la carpeta /content/buckets/b1/exp/HT4950-04 y la fija como directorio de
#   trabajo. Arma dataset_bo con los meses 202103, 202104 y 202106, la clase binaria clase01 (1 si
#   clase_ternaria es BAJA+1 o BAJA+2) y la marca training (1 para 202103 y 202104). campos_buenos son todas las
#   columnas salvo numero_de_cliente, clase_ternaria, clase01, fold, azar y training; foto_mes queda incluida.
#%% celda 49 [texto]
### 2.2.4  Preprocesamiento

#%% celda 50 [código]
# carpeta de trabajo

setwd("/content/buckets/b1/exp")
dir.create(PARAM$experimento, showWarnings=FALSE)
setwd( paste0("/content/buckets/b1/exp/", PARAM$experimento))

#%% celda 51 [código]
dataset_bo <- dataset[
  foto_mes %in% c(PARAM$train, PARAM$validate)
]

# Variable objetivo binaria
dataset_bo[, clase01 :=
  as.integer(clase_ternaria %in% c("BAJA+1", "BAJA+2"))
]

# Selección de registros:
# training = 1 para marzo y abril
# training = 0 para junio
dataset_bo[, training :=
  as.integer(foto_mes %in% PARAM$train)
]

#%% celda 52 [código]
# Variables predictoras
campos_buenos <- setdiff(
  names(dataset_bo),
  c("numero_de_cliente","clase_ternaria","clase01","fold","azar","training"  )
)

# [Anotación · líneas 554–587] Dos celdas de texto sobre data drifting indican que cprestamos_personales y
#   mprestamos_personales cambian de distribución entre 202104 y 202106 y que se eliminan. La celda de código
#   quita de campos_buenos esas dos variables y sus _lag1, _lag2, _delta1 y _delta2 (10 columnas).
#%% celda 53 [texto]
#### 2.2.4.1  Salsa Magica (dedicada a Laura Pasquini)

Los EDAs que estan haciendo los alumnos de los lunes son pura falopa, y de la mala. El uso de Agentes de la IA solo les empera el daño cerebral, generan pedf larguisimos, que no te dan ganas de leerlos, carentes de insights y alma.
<br>El unico EDA que tiene realmente sentido, en este caso, es comparar la distribución de cada variable del mes donde se entrena 202104 y el mes donde se va a aplicar el modelo 202106, buscando Data Drifting.
<br>Aun con los reales datos del futuro, donde no se tiene la clase, SIEMPRE se puede analizar el Data Drifting.
<br>Para las variables con distribuciones distintas se puede hacer:
* Transformar la variable para hacerla homogenea entre los dos periodos
* Eliminarla (es lo simple, que se eligió hacer en este caso)

#%% celda 54 [texto]
En esa exploracion gráfica del Data Drifting, se vio que estas variables cambian de distribucion entre 202104 y 202106, y se decidió brutalmente eliminarlas
* cprestamos_personales
* mprestamos_personales


más adelantes, se utilizarán técnicas más inclusivas, y se preservaran dichas variables, transformadas.

#%% celda 55 [código]
campos_buenos <- setdiff(
  campos_buenos,
  c(
    "cprestamos_personales",
    "cprestamos_personales_lag1",
    "cprestamos_personales_lag2",
    "cprestamos_personales_delta1",
    "cprestamos_personales_delta2",
    "mprestamos_personales",
    "mprestamos_personales_lag1",
    "mprestamos_personales_lag2",
    "mprestamos_personales_delta1",
    "mprestamos_personales_delta2"
  )
)

# [Anotación · líneas 589–628] Inicializa el contador giter (si existe BO_log.txt continúa desde su iteración
#   máxima) y define Estimar_lightgbm(): combina los parámetros fijos con los que propone la optimización,
#   entrena con lgb.train sobre dtrain usando dvalidate como conjunto de validación, toma modelo$best_score como
#   métrica, registra parámetros, iteración y métrica en BO_log.txt, vuelve a fijar la semilla 775777 y devuelve
#   la métrica.
#%% celda 56 [texto]
2.2.5 Configuracion Bayesian Optimization

#%% celda 57 [código]
giter <- 0

if( file.exists("BO_log.txt") ){
  tb_BO <- fread("BO_log.txt")
  giter <- tb_BO[, max(iter)]
}

#%% celda 58 [código]
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

# [Anotación · líneas 630–668] Construye dtrain con las filas de training == 1 (202103 y 202104) y dvalidate
#   con las de 202106, ambos con las columnas de campos_buenos y la etiqueta clase01. Las celdas 60 a 63
#   muestran cantidad de filas y columnas de cada uno, filas por mes y positivos por mes.
#%% celda 59 [código]
# Dataset de entrenamiento: marzo y abril en el formato que necesita LightGBM
dtrain <- lgb.Dataset(
  data = data.matrix(
    dataset_bo[training == 1L, campos_buenos, with = FALSE]
  ),
  label = dataset_bo[training == 1L, clase01],
  free_raw_data = FALSE
)

# Dataset de validación: junio en el formato que necesita LightGBM
dvalidate <- lgb.Dataset(
  data = data.matrix(
    dataset_bo[foto_mes == PARAM$validate, campos_buenos, with = FALSE]
  ),
  label = dataset_bo[foto_mes == PARAM$validate, clase01],
  free_raw_data = FALSE
)

#%% celda 60 [código]
# Comprobar dimensiones
nrow(dtrain)
ncol(dtrain)

nrow(dvalidate)
ncol(dvalidate)

#%% celda 61 [código]
dataset_bo[, .N, by = foto_mes][order(foto_mes)]

#%% celda 62 [código]
dataset_bo[, .(
  filas = .N,
  positivos = sum(clase01 == 1L, na.rm = TRUE)
), by = foto_mes][order(foto_mes)]

#%% celda 63 [código]
nrow(dtrain)
nrow(dvalidate)

# [Anotación · líneas 670–721] Configura la optimización bayesiana: objetivo ObjectiveRFun sobre
#   Estimar_lightgbm con la métrica a maximizar, instancia con terminador de 10 evaluaciones, modelo sustituto
#   regr.km (método BFGS, nugget estimado), función de adquisición expected improvement, optimizador de la
#   adquisición por búsqueda al azar con lote de 1.000 y 1.000 evaluaciones, y optimizador mbo con bayesopt_ego.
#   La celda 66 ejecuta optimizer$optimize(instance) y la 67 imprime fecha y hora.
#%% celda 64 [código]
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

#%% celda 65 [texto]
2.2.6 Corrida Bayesian Optimization

#%% celda 66 [código]
bayesiana_salida <- optimizer$optimize(instance)

#%% celda 67 [código]
format(Sys.time(), "%a %b %d %X %Y")

#%% celda 68 [texto]
Luego de este punto, en la carpeta del experimento quedó el archivo BO_log.txt que posee todas las iteraciones de la Bayesian Optimization

# [Anotación · líneas 723–833] Bloque comentado en su totalidad (celdas 70 a 78): toma de BO_log.txt la fila
#   de mayor métrica, entrena un modelo con dtrain y dvalidate, predice 202106, asigna 1.072.500 a cada BAJA+2 y
#   -27.500 al resto, calcula la ganancia acumulada por orden de probabilidad, la imprime para los cortes de
#   PARAM$cortes, la grafica hasta 20.000 envíos y busca la posición de ganancia máxima.
#%% celda 69 [texto]
### Valido con el calculo de ganancia

#%% celda 70 [código]
# setwd("/content/buckets/b1/exp")
# dir.create(PARAM$experimento, showWarnings= FALSE)
# setwd( paste0("/content/buckets/b1/exp/", PARAM$experimento ))

#%% celda 71 [código]
 # # cergo los mejores hiperparametros, que son los de mayor metrica
 # tb_bayesiana <- fread("BO_log.txt")
 # setorder( tb_bayesiana, -metrica )
 # PARAM$out$lgbm$mejores_hiperparametros <- as.list(tb_bayesiana[1])

#%% celda 72 [código]
# param_final <- modifyList(
#     PARAM$lgbm$param_fijos,
#     PARAM$out$lgbm$mejores_hiperparametros
#   )

#%% celda 73 [código]
  # # entreno LightGBM
  # modelo <- lgb.train(
  #   data= dtrain,
  #   valids= list( "val"=dvalidate),
  #   param= param_final
  # )

#%% celda 74 [código]
# # Dataset de junio
# tb_prediccion <- copy(
#   dataset_bo[
#     foto_mes == PARAM$validate,
#     c(
#       "numero_de_cliente",
#       "foto_mes",
#       "clase_ternaria",
#       campos_buenos
#     ),
#     with = FALSE
#   ]
# )

# # Predecir probabilidades
# prediccion_junio <- predict(
#   modelo,
#   data.matrix(
#     tb_prediccion[, campos_buenos, with = FALSE]
#   )
# )

# # Agregar probabilidades
# tb_prediccion[, prob := as.numeric(prediccion_junio)]

# # Verificar
# head(tb_prediccion[, .(
#   numero_de_cliente,
#   foto_mes,
#   clase_ternaria,
#   prob
# )])

#%% celda 75 [código]
# # Asignar la ganancia real según la clase
# tb_prediccion[, gan := fifelse(
#   clase_ternaria == "BAJA+2",
#   1072500,
#   -27500
# )]

# # Ordenar de mayor a menor probabilidad
# setorder(tb_prediccion, -prob)

# # Calcular la ganancia acumulada
# tb_prediccion[, ganancia_acumulada := cumsum(gan)]
# tb_prediccion[, pos := seq_len(.N)]

# # Evaluar los cortes
# for (envios in PARAM$cortes) {
#   if (envios <= nrow(tb_prediccion)) {
#     ganancia <- tb_prediccion[envios, ganancia_acumulada]
#     cat(envios, "\t", ganancia, "\n")
#   }
# }

#%% celda 76 [código]
# plot(
#   tb_prediccion$pos,
#   tb_prediccion$ganancia_acumulada,
#   type = "l",
#   xlim = c(0, 20000),
#   ylim = c(0, max(tb_prediccion$ganancia_acumulada, na.rm = TRUE)),
#   xlab = "Cantidad de clientes enviados",
#   ylab = "Ganancia acumulada",
#   main = "Ganancia acumulada - Validación junio"
# )

# abline(h = 0, lty = 2)

#%% celda 77 [código]
# # Buscar la máxima ganancia acumulada
# fila_max <- which.max(tb_prediccion$ganancia_acumulada)

# cat("Máxima ganancia:", tb_prediccion$ganancia_acumulada[fila_max], "\n")
# cat("Cantidad de envíos:", tb_prediccion$pos[fila_max], "\n")

#%% celda 78 [código]
# tb_prediccion[fila_max, .(
#   envios = pos,
#   ganancia_maxima = ganancia_acumulada
# )]

# [Anotación · líneas 835–865] Sección de producción: vuelve a fijar el directorio del experimento, lee
#   BO_log.txt, lo ordena por métrica descendente y guarda la primera fila completa como lista en
#   PARAM$out$lgbm$mejores_hiperparametros. Crea clase01 en todo el dataset y arma dataset_train con los meses
#   202103 a 202106, mostrando filas por mes y clase.
#%% celda 79 [texto]
## 2.3  Produccion

#%% celda 80 [texto]
### Final Training
Construyo el modelo final, que es uno solo, no hace ningun tipo de particion < training, validation, testing>]

#%% celda 81 [código]
setwd("/content/buckets/b1/exp")
dir.create(PARAM$experimento, showWarnings= FALSE)
setwd( paste0("/content/buckets/b1/exp/", PARAM$experimento ))

#%% celda 82 [código]
 # cergo los mejores hiperparametros, que son los de mayor metrica
 tb_bayesiana <- fread("BO_log.txt")
 setorder( tb_bayesiana, -metrica )
 PARAM$out$lgbm$mejores_hiperparametros <- as.list(tb_bayesiana[1])

#%% celda 83 [texto]
#### Final Training Dataset

Aqui esta la gran decision de en qué meses hago el Final Training
<br> debo utilizar los mejores hiperparámetros que encontré en la  optimización bayesiana

#%% celda 84 [código]
# clase01
dataset[, clase01 := ifelse(clase_ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)]

#%% celda 85 [código]
dataset_train <- dataset[foto_mes %in% PARAM$train_final]
dataset_train[,.N, list(foto_mes, clase_ternaria)]

# [Anotación · líneas 867–911] Arma dfuture con las filas de 202108. Vuelve a agregar a campos_buenos las 10
#   columnas de préstamos personales quitadas antes y saca numero_de_cliente, clase_ternaria y clase01. Las
#   celdas 89 y 90, que entrenan un único modelo final y predicen con él, están comentadas.
#%% celda 86 [texto]
#### Final Training Hyperparameters

#%% celda 87 [código]
# aplico el modelo a los datos sin clase
dfuture <- dataset[foto_mes %in% PARAM$future]

#%% celda 88 [código]
campos_buenos <- unique(c(
  campos_buenos,
  "cprestamos_personales",
  "cprestamos_personales_lag1",
  "cprestamos_personales_lag2",
  "cprestamos_personales_delta1",
  "cprestamos_personales_delta2",
  "mprestamos_personales",
  "mprestamos_personales_lag1",
  "mprestamos_personales_lag2",
  "mprestamos_personales_delta1",
  "mprestamos_personales_delta2"
))

campos_buenos <- setdiff(campos_buenos, c("numero_de_cliente", "clase_ternaria", "clase01"))

#%% celda 89 [código]
# # Entreno el modelo sobre todo el periodo

# dtrain_final <- lgb.Dataset(
#   data= data.matrix(dataset_train[, campos_buenos, with= FALSE]),
#   label= dataset_train[, clase01]
# )

# modelo_final <- lgb.train(
#   data= dtrain_final,
#   param= param_final
# )

#%% celda 90 [código]
# # hago el predict en los datos del futuro, y calculo la ganancia

# # aplico el modelo a los datos nuevos
# prediccion <- predict(
#   modelo_final,
#   data.matrix(dfuture[, campos_buenos, with= FALSE])
# )

# [Anotación · líneas 913–933] Lista de 20 semillas. Construye dtrain_final con dataset_train (columnas
#   campos_buenos, etiqueta clase01) e inicia tb_predicciones con numero_de_cliente y foto_mes de dfuture.
#%% celda 91 [código]
# Las semillas
semillas <- c(
  765461, 765487, 765497, 765503, 765521,
  384157, 414857, 503857, 697757, 735157,
  775777, 333331, 555557, 111119, 799999,
  600013, 620003, 640007, 660007, 680003
)

#%% celda 92 [código]
# Preparar los datos una sola vez
dtrain_final <- lgb.Dataset(
  data = data.matrix(
    dataset_train[, campos_buenos, with = FALSE]
  ),
  label = dataset_train[, clase01],
  free_raw_data = FALSE
)

# Tabla para guardar las predicciones de los 20 modelos
tb_predicciones <- dfuture[, .(numero_de_cliente, foto_mes)]

# [Anotación · líneas 935–997] Bucle sobre las 20 semillas: arma param_final con los parámetros fijos pisados
#   por los elegidos, asigna la semilla a seed, bagging_seed, feature_fraction_seed, drop_seed y
#   data_random_seed, entrena con lgb.train sobre dtrain_final sin conjunto de validación, guarda el modelo en
#   modelo_semilla_<semilla>.txt, predice dfuture y agrega la columna prob_<semilla>; imprime hora de inicio y
#   fin y libera memoria. Al terminar graba predicciones_agosto_20_semillas.csv.
#%% celda 93 [código]
for (semilla in semillas) {

  cat(
    "\nEntrenando modelo con semilla:", semilla,
    "|", format(Sys.time(), "%H:%M:%S"), "\n"
  )
  flush.console()
  flush(stdout())

  # Hiperparámetros optimizados + semilla de esta corrida
  param_final <- modifyList(
    PARAM$lgbm$param_fijos,
    PARAM$out$lgbm$mejores_hiperparametros
  )

  param_final$seed <- semilla
  param_final$bagging_seed <- semilla
  param_final$feature_fraction_seed <- semilla
  param_final$drop_seed <- semilla
  param_final$data_random_seed <- semilla

  # Entrenar modelo
  modelo_final <- lgb.train(
    data = dtrain_final,
    param = param_final
  )

  # Guardar el modelo
  lgb.save(
    modelo_final,
    paste0("modelo_semilla_", semilla, ".txt")
  )

  # Predecir agosto
  prediccion <- predict(
    modelo_final,
    data.matrix(dfuture[, campos_buenos, with = FALSE])
  )

  # Guardar probabilidades de esta semilla
  nombre_columna <- paste0("prob_", semilla)
  tb_predicciones[, (nombre_columna) := as.numeric(prediccion)]

  cat(
    "FINALIZADO | Semilla:", semilla,
    "| Hora:", format(Sys.time(), "%H:%M:%S"), "\n"
  )
  flush.console()
  flush(stdout())

  rm(modelo_final, prediccion)
  gc()
}

# Guardar las predicciones en un solo archivo
fwrite(tb_predicciones, "predicciones_agosto_20_semillas.csv")

# Ver las primeras filas
head(tb_predicciones)

#%% celda 94 [código]
format(Sys.time(), "%a %b %d %X %Y")

# [Anotación · líneas 999–1105] Bloque comentado (celdas 96 y 98): genera una lista de clientes por cada
#   semilla y cada corte de 9.000 a 15.000 cada 500, con nombre HT4950-04_<semilla>_<corte>.csv, y las comprime
#   en HT4950-04_listas_clientes.zip. La celda 99, activa, imprime fecha y hora.
#%% celda 95 [texto]
#### Leo archivos y veo las mejores particiones

#%% celda 96 [código]
# # Nombre del experimento
# nombre_experimento <- PARAM$experimento

# # Leer las predicciones
# archivo_entrada <- "predicciones_agosto_20_semillas.csv"
# tb_predicciones <- fread(archivo_entrada)

# # Detectar las semillas disponibles
# columnas_prob <- grep("^prob_", names(tb_predicciones), value = TRUE)

# # Cortes: 9000, 9500, ..., 15000
# cortes <- seq(9000, 15000, by = 500)

# # Verificar que haya suficientes clientes
# stopifnot(nrow(tb_predicciones) >= max(cortes))

# # Convertir los números de cliente a texto sin notación científica
# clientes <- format(
#   tb_predicciones$numero_de_cliente,
#   scientific = FALSE,
#   trim = TRUE
# )

# # Generar los archivos para cada semilla y cada corte
# for (columna in columnas_prob) {

#   orden <- order(-tb_predicciones[[columna]], na.last = TRUE)
#   clientes_ordenados <- clientes[orden]

#   # Obtener el número de semilla
#   numero_semilla <- sub("^prob_", "", columna)

#   for (corte in cortes) {

#     seleccion <- clientes_ordenados[seq_len(corte)]

#     # Nombre variable según el experimento
#     nombre_archivo <- paste0(
#       nombre_experimento, "_",
#       numero_semilla, "_",
#       corte, ".csv"
#     )

#     fwrite(
#       data.table(seleccion),
#       file = nombre_archivo,
#       col.names = FALSE,
#       quote = FALSE,
#       sep = ","
#     )

#     cat("Generado:", nombre_archivo, "\n")
#   }
# }

# cat(
#   "\nProceso terminado. Total de archivos generados:",
#   length(columnas_prob) * length(cortes),
#   "\n"
# )

#%% celda 97 [texto]
zipeo los archivos y los guardo

#%% celda 98 [código]
# # Nombre del experimento
# nombre_experimento <- PARAM$experimento

# # Buscar los CSV correspondientes a este experimento
# archivos <- list.files(
#   path = ".",
#   pattern = paste0(
#     "^",
#     nombre_experimento,
#     "_[0-9]+_[0-9]+\\.csv$"
#   ),
#   full.names = TRUE
# )

# if (length(archivos) == 0) {
#   stop("No se encontraron archivos CSV para el experimento ", nombre_experimento)
# }

# # Nombre variable del ZIP
# archivo_zip <- paste0(
#   nombre_experimento,
#   "_listas_clientes.zip"
# )

# utils::zip(
#   zipfile = archivo_zip,
#   files = archivos,
#   flags = "-j"
# )

# cat(
#   "ZIP generado:", normalizePath(archivo_zip),
#   "\nCantidad de CSV incluidos:", length(archivos),
#   "\n"
# )

#%% celda 99 [código]
format(Sys.time(), "%a %b %d %X %Y")

# [Anotación · líneas 1107–1177] Lee predicciones_agosto_20_semillas.csv, calcula prob_promedio como promedio
#   de las columnas prob_ por fila y ordena de mayor a menor. Para cada corte de 9.000 a 15.000 cada 500 escribe
#   HT4950-04_promedio_<corte>.csv con los numero_de_cliente de las primeras filas, sin encabezado ni notación
#   científica. Graba la tabla completa en HT4950-04_predicciones_promedio.csv e imprime la cantidad de semillas
#   promediadas y de archivos generados.
#%% celda 100 [texto]
Genero ensambles con el promedio

#%% celda 101 [código]
# Nombre del experimento
nombre_experimento <- PARAM$experimento

# Leer las predicciones de las semillas
tb_predicciones <- fread("predicciones_agosto_20_semillas.csv")

# Detectar las columnas de probabilidades
columnas_prob <- grep("^prob_", names(tb_predicciones), value = TRUE)

# Verificar que existan probabilidades
stopifnot(length(columnas_prob) > 0)
stopifnot("numero_de_cliente" %in% names(tb_predicciones))

# Calcular el promedio de probabilidades por cliente
tb_predicciones[, prob_promedio := rowMeans(
  as.matrix(.SD),
  na.rm = TRUE
), .SDcols = columnas_prob]

# Ordenar de mayor a menor probabilidad promedio
setorder(tb_predicciones, -prob_promedio)

# Cortes: 9000, 9500, ..., 15000
cortes <- seq(9000, 15000, by = 500)

# Verificar que haya suficientes clientes
stopifnot(nrow(tb_predicciones) >= max(cortes))

# Convertir los números de cliente a texto sin notación científica
clientes_ordenados <- format(
  tb_predicciones$numero_de_cliente,
  scientific = FALSE,
  trim = TRUE
)

# Generar un CSV por cada corte
for (corte in cortes) {

  seleccion <- clientes_ordenados[seq_len(corte)]

  nombre_archivo <- paste0(
    nombre_experimento,
    "_promedio_",
    corte,
    ".csv"
  )

  fwrite(
    data.table(seleccion),
    file = nombre_archivo,
    col.names = FALSE,
    quote = FALSE,
    sep = ","
  )

  cat("Generado:", nombre_archivo, "\n")
}

# Guardar también todas las probabilidades promedio
fwrite(
  tb_predicciones,
  paste0(nombre_experimento, "_predicciones_promedio.csv")
)

cat("\nProceso terminado.\n")
cat("Semillas promediadas:", length(columnas_prob), "\n")
cat("Archivos de cortes generados:", length(cortes), "\n")

# [Anotación · líneas 1179–1212] Bloque comentado: verifica que existan 13 archivos
#   HT4950-04_promedio_<corte>.csv y los comprime en HT4950-04_promedio_listas_clientes.zip.
#%% celda 102 [código]
# zipeo los ensambles

#%% celda 103 [código]

# nombre_experimento <- PARAM$experimento

# archivos <- list.files(
#   path = ".",
#   pattern = paste0(
#     "^",
#     nombre_experimento,
#     "_promedio_[0-9]+\\.csv$"
#   ),
#   full.names = TRUE
# )

# if (length(archivos) != 13) {
#   stop("Se esperaban 13 archivos de cortes, pero se encontraron ", length(archivos))
# }

# archivo_zip <- paste0(
#   nombre_experimento,
#   "_promedio_listas_clientes.zip"
# )

# utils::zip(
#   zipfile = archivo_zip,
#   files = archivos,
#   flags = "-j"
# )

# cat("ZIP generado:", normalizePath(archivo_zip), "\n")
# cat("CSV incluidos:", length(archivos), "\n")

# [Anotación · líneas 1214–1271] Busca los .ipynb de /home/ds/buckets/b1/dmeyf2026/primera_competencia, se
#   detiene si no hay exactamente uno y copia ese notebook a /content/buckets/b1/exp/HT4950-04/HT4950-04.ipynb,
#   creando la carpeta de destino si no existe.
#%% celda 104 [código]
#Guardo una copia de la notebook que generó los archivos

#%% celda 105 [código]
# 1. Nombre del experimento
nombre_experimento <- PARAM$experimento

# 2. Carpeta donde está la notebook original
carpeta_origen <- "/home/ds/buckets/b1/dmeyf2026/primera_competencia"

# 3. Buscar la notebook original
archivos_ipynb <- list.files(
  path = carpeta_origen,
  pattern = "\\.ipynb$",
  full.names = TRUE
)

if (length(archivos_ipynb) != 1) {
  stop(
    "Se esperaba una sola notebook en ",
    carpeta_origen,
    ", pero se encontraron ",
    length(archivos_ipynb),
    "."
  )
}

archivo_origen <- archivos_ipynb[1]

# 4. Carpeta de destino del experimento
carpeta_destino <- file.path(
  "/content/buckets/b1/exp",
  nombre_experimento
)

dir.create(
  carpeta_destino,
  recursive = TRUE,
  showWarnings = FALSE
)

# 5. Copiar la notebook con el nombre del experimento
archivo_destino <- file.path(
  carpeta_destino,
  paste0(nombre_experimento, ".ipynb")
)

if (file.copy(
  from = archivo_origen,
  to = archivo_destino,
  overwrite = TRUE
)) {
  cat("Notebook copiada correctamente.\n")
  cat("Original:", archivo_origen, "\n")
  cat("Destino:", archivo_destino, "\n")
} else {
  stop("No se pudo copiar la notebook.")
}
```


## Explicaciones del alumno (texto original)

### primera_competencia/READ_ME.txt

> De los .csv generados al terminar el proceso, utilizar el que se llama HT4950-04_promedio_11000.csv
> Ese .csv es el último que se subio a zulip como predicción final.

