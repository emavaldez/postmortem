# IsabelEspinozaDM — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: iespinozahDM
- Repositorio: https://github.com/iespinozahDM/primeracompetencia-dmeyf
- Link posteado: https://github.com/iespinozahDM/primeracompetencia-dmeyf
- Commit: 9f73fa533d9b30ae478dc3ac2c5a477ad36dab3a
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/iespinozahdm/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/iespinozahdm.json

## Resumen

La entrega contiene un notebook de R (Espinoza-Comp1.ipynb, cinco celdas) y un README. El notebook lee el archivo crudo de la competencia, calcula la clase ternaria con adelantos de uno y dos períodos por cliente, pasa ccajas_depositos a NA en 202105, elimina cprestamos_personales y mprestamos_personales y arma una clase binaria con positivo = BAJA+2. Agrega el lag 1 y el delta 1 de todas las variables. Con mlrMBO (20 puntos iniciales y 30 iteraciones) busca num_iterations, num_leaves y min_sum_hessian_in_leaf de un LightGBM entrenado en 202103 y 202104, maximizando la ganancia de las 10.000 filas de mayor probabilidad en 202106. Con los valores que devuelve esa búsqueda entrena 5 modelos con distinta semilla sobre 202103 a 202106, promedia sus probabilidades para 202108 y escribe ieh_final_1110.csv con los 10.000 clientes de mayor probabilidad. El README incluye una tabla de cuatro experimentos con ganancias del leaderboard público y un texto sobre problemas de memoria al agregar lags y deltas de orden 2; el código de esos otros experimentos no está en el repositorio.

**Qué entrega.** Un archivo ieh_final_1110.csv, sin encabezado, con el numero_de_cliente de las 10.000 filas de 202108 con mayor probabilidad promedio. El archivo no está en el repositorio.

**Cómo se ejecuta.** No se indica. El repositorio trae un único notebook de R con cinco celdas que imprimen los pasos [PASO 1] a [PASO 7]; lee /home/ds/datasets/competencia_01_crudo.csv y escribe optimizacion_marzo_abril_pure.rds e ieh_final_1110.csv en el directorio de trabajo.

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase01): 1 si clase_ternaria es BAJA+2 y 0 en los demás casos. La clase_ternaria se calcula en el notebook a partir del archivo crudo, con adelantos de 1 y 2 períodos por cliente.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código: entrena con todas las filas de los meses elegidos. El README menciona pruebas con submuestreo (30% en EXP-03) cuyo código no está en el repositorio.
- **Calidad de datos:** Pasa ccajas_depositos a NA en las filas de 202105 y elimina las columnas cprestamos_personales y mprestamos_personales.
- **Drifting:** No se observa en el código
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** Lag de orden 1 (valor de la fila anterior del mismo cliente) y delta de orden 1 (valor actual menos lag 1) de todas las columnas, salvo numero_de_cliente, foto_mes, las clases y los períodos auxiliares. Según la salida guardada en el notebook original, el dataset queda con 457 columnas.
- **Selección de variables:** No se observa en el código: el modelo usa todas las variables originales que quedan más sus lag1 y delta1. El README menciona una selección con lgb.importance() en otros experimentos, sin código en el repositorio.
- **Optimización de hiperparámetros:** Optimización bayesiana con mlrMBO: diseño inicial de 20 puntos y 30 iteraciones con criterio Expected Improvement y modelo sustituto de kriging (regr.km, covarianza matern3_2). Busca num_iterations entre 500 y 3000, num_leaves entre 16 y 63 y min_sum_hessian_in_leaf entre 0,01 y 5,0. Cada evaluación entrena en 202103 y 202104 y mide la ganancia de las 10.000 filas de mayor probabilidad en 202106.
- **Hiperparámetros finales:** num_leaves, min_sum_hessian_in_leaf y la cantidad de rondas se toman del resultado de la optimización bayesiana; sus valores no están escritos en el código ni en las salidas guardadas del notebook. Fijos en el código: boosting gbdt, objective binary, metric auc, max_bin 31, min_data_in_leaf 0, feature_fraction 0,50, feature_fraction_bynode 0,20, learning_rate 0,005, boost_from_average TRUE, nthreads 1. Según el README, la entrega usa 30 hojas y 2.180 rondas.
- **Semillas:** set.seed(314159) seguido de sample(1:1000000, 5) genera las 5 semillas del modelo final. El mismo set.seed(314159) precede al diseño inicial de la optimización; los parámetros de LightGBM dentro de la función objetivo no incluyen seed.
- **Cantidad de semillas:** 5
- **Ensamble:** Promedio de las probabilidades de 5 modelos LightGBM con los mismos hiperparámetros y distinta semilla.
- **Corte:** Cantidad fija: las 10.000 filas de mayor probabilidad promedio. El mismo corte de 10.000 se usa para calcular la ganancia dentro de la optimización.
- **Validación:** Un mes posterior al entrenamiento: entrena en 202103 y 202104 y mide en 202106 la ganancia (117.500 por cada BAJA+2 y -27.500 por cada fila restante) de las 10.000 filas de mayor probabilidad. Se usa sólo dentro de la optimización bayesiana.
- **Salidas:** optimizacion_marzo_abril_pure.rds (resultado de la optimización bayesiana) e ieh_final_1110.csv (10.000 numero_de_cliente, sin encabezado, separados por tabulador). Ninguno de los dos archivos está en el repositorio.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Técnicas sólo exploradas

- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: no
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: sí
- Entorno declarado: El README menciona una máquina virtual de 60 GB de RAM. Los metadatos del notebook indican kernel de R, versión 4.6.1. El dataset se lee de /home/ds/datasets/. No se declaran versiones de paquetes.

## Pasos del camino de la entrega

1. **Carga de librerías y lectura del dataset.** Carga data.table, lightgbm, ParamHelpers, mlrMBO y DiceKriging y lee el archivo crudo /home/ds/datasets/competencia_01_crudo.csv. (`Espinoza-Comp1.ipynb` líneas 1–12)
2. **Cálculo de la clase ternaria.** Numera los períodos de forma consecutiva, obtiene para cada cliente el período de sus dos filas siguientes y asigna CONTINUA, BAJA+1 o BAJA+2 según el cliente tenga o no fila en el período siguiente y en el que le sigue. (`Espinoza-Comp1.ipynb` líneas 14–31)
3. **Correcciones de datos y clase binaria.** Pasa ccajas_depositos a NA en 202105, elimina cprestamos_personales y mprestamos_personales y crea clase01 con valor 1 para BAJA+2 y 0 para el resto. (`Espinoza-Comp1.ipynb` líneas 33–41)
4. **Lags y deltas de orden 1.** Para cada variable agrega el valor de la fila anterior del mismo cliente (_lag1) y la diferencia entre el valor actual y ese lag (_delta1). (`Espinoza-Comp1.ipynb` líneas 43–57)
5. **Partición para la optimización.** Separa 202103 y 202104 como entrenamiento y 202106 como validación, define la lista de columnas de entrada y construye el lgb.Dataset y la matriz de validación. (`Espinoza-Comp1.ipynb` líneas 59–74)
6. **Espacio de búsqueda y diseño inicial.** Define los rangos de num_iterations (500 a 3000), num_leaves (16 a 63) y min_sum_hessian_in_leaf (0,01 a 5,0) y genera 20 puntos iniciales con set.seed(314159). (`Espinoza-Comp1.ipynb` líneas 76–86)
7. **Función objetivo: ganancia en 202106.** Entrena un LightGBM con los parámetros fijos y los tres valores del punto evaluado, predice 202106 y devuelve la ganancia de las 10.000 filas de mayor probabilidad (117.500 por BAJA+2, -27.500 por el resto). (`Espinoza-Comp1.ipynb` líneas 88–114)
8. **Optimización bayesiana con mlrMBO.** Configura 30 iteraciones con criterio Expected Improvement y sustituto de kriging, ejecuta mbo() sobre el diseño inicial, guarda el resultado en optimizacion_marzo_abril_pure.rds y extrae el punto de mayor ganancia. (`Espinoza-Comp1.ipynb` líneas 116–133)
9. **Datos del entrenamiento final.** Toma 202103, 202104, 202105 y 202106 como entrenamiento y 202108 como mes a predecir, y construye el lgb.Dataset y la matriz de predicción con las mismas columnas. (`Espinoza-Comp1.ipynb` líneas 135–149)
10. **Parámetros finales y semillas.** Arma los parámetros con los valores fijos más num_leaves y min_sum_hessian_in_leaf de la optimización, y sortea 5 semillas entre 1 y 1.000.000 tras set.seed(314159). (`Espinoza-Comp1.ipynb` líneas 151–166)
11. **Entrenamiento con 5 semillas y promedio.** Entrena un modelo por semilla con la cantidad de rondas que devolvió la optimización, acumula las probabilidades predichas para 202108 y las divide por 5. (`Espinoza-Comp1.ipynb` líneas 168–190)
12. **Escritura del archivo de entrega.** Escribe en ieh_final_1110.csv el numero_de_cliente de las 10.000 filas de mayor probabilidad promedio, sin encabezado y con tabulador como separador. (`Espinoza-Comp1.ipynb` líneas 192–199)

## Archivos

- `Espinoza-Comp1.ipynb` · principal · Jupyter (R) · 199 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/iespinozahdm/Espinoza-Comp1.ipynb.txt) — Notebook de R con cinco celdas de código que va desde la lectura del archivo crudo hasta la escritura del archivo de entrega: clase ternaria, correcciones de datos, lags y deltas de orden 1, optimización bayesiana con mlrMBO y entrenamiento final con 5 semillas. En el notebook original las celdas 1 a 3 tienen número de ejecución y salida guardada; la celda 4 sólo conserva su primera línea impresa y la celda 5 no tiene salida guardada.
- `README.md` · explicacion · Markdown · 34 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/iespinozahdm/README.md.txt) — Texto de presentación con el nombre de la alumna, una tabla titulada 'Resumen Metodológico y Bitácora de Experimentos' y una sección de tres apartados sobre los lags y deltas de orden 1, los problemas de memoria al agregar el orden 2 y el criterio de cierre. Según el README: EXP-01 (variables originales, 30 hojas / 500 rondas, 100% de datos) $81.200.000 de ganancia pública promedio; EXP-02 (lag1 + delta1, 30 hojas / 2.180 rondas, 100% de datos) $95.782.500, marcado como 'Candidato Elegido'; EXP-03 (selección con Gain > 0, 16 hojas / 500 rondas, submuestreo 30%) $84.865.000; VARIOS (lag2 + delta2, 753 columnas) sin resultado por falta de memoria en una máquina virtual de 60 GB de RAM. Menciona además una selección de 30 variables con lgb.importance() para calcular el orden 2 sólo sobre ellas (501 columnas). No indica cómo ejecutar el notebook.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### Espinoza-Comp1.ipynb

Notebook de R con cinco celdas de código que va desde la lectura del archivo crudo hasta la escritura del archivo de entrega: clase ternaria, correcciones de datos, lags y deltas de orden 1, optimización bayesiana con mlrMBO y entrenamiento final con 5 semillas. En el notebook original las celdas 1 a 3 tienen número de ejecución y salida guardada; la celda 4 sólo conserva su primera línea impresa y la celda 5 no tiene salida guardada.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Carga data.table, lightgbm, ParamHelpers, mlrMBO y DiceKriging, desactiva la
#   notación científica (scipen = 999) y lee con fread el archivo /home/ds/datasets/competencia_01_crudo.csv en
#   el objeto dataset.
#%% celda 1 [código]
library(data.table)
library(lightgbm)
library(ParamHelpers)
library(mlrMBO)
library(DiceKriging)

options(scipen = 999)

print("[PASO 1] Leyendo el archivo crudo original desde el disco...")
flush.console()
dataset <- fread("/home/ds/datasets/competencia_01_crudo.csv")

# [Anotación · líneas 14–27] Calcula periodo0, un número de período consecutivo (año × 12 + mes) a partir de
#   foto_mes, ordena por cliente y período y guarda el último período y el anterior a ese. Para cada cliente
#   agrega periodo1 y periodo2: el período de su fila siguiente y el de dos filas más adelante (NA si no
#   existen).
#%% celda 2 [código]
print("[PASO 2] Ejecutando algoritmo de Clase Ternaria")
flush.console()

# Calculamos el periodo consecutivo lineal
dataset[, periodo0 := as.integer(foto_mes/100)*12 + foto_mes%%100]
setorder(dataset, numero_de_cliente, periodo0)

periodo_ultimo <- dataset[, max(periodo0)]
periodo_anteultimo <- periodo_ultimo - 1

# Generamos las ventanas móviles hacia adelante agrupando por cliente
dataset[, c("periodo1", "periodo2") := shift(periodo0, n=1:2, fill=NA, type="lead"), by = numero_de_cliente]

# [Anotación · líneas 28–32] Asigna clase_ternaria en tres pasos sucesivos. CONTINUA: todas las filas
#   anteriores al anteúltimo período. BAJA+1: filas anteriores al último período cuyo cliente no tiene fila en
#   el período siguiente. BAJA+2: filas anteriores al anteúltimo período cuyo cliente está en el período
#   siguiente y no en el que le sigue. Las filas del último período y las del anteúltimo que no son BAJA+1
#   quedan sin clase.
# Asignación de estados secuenciales de la cátedra
dataset[periodo0 < periodo_anteultimo, clase_ternaria := "CONTINUA"]
dataset[periodo0 < periodo_ultimo & (is.na(periodo1) | periodo0 + 1 < periodo1), clase_ternaria := "BAJA+1"]
dataset[periodo0 < periodo_anteultimo & (periodo0+1 == periodo1) & (is.na(periodo2) | periodo0 + 2 < periodo2), clase_ternaria := "BAJA+2"]

# [Anotación · líneas 33–42] Pasa ccajas_depositos a NA en las filas de 202105 y, si existe
#   cprestamos_personales, elimina esa columna y mprestamos_personales. Crea clase01, que vale 1 cuando
#   clase_ternaria es BAJA+2 y 0 en los demás casos, e imprime la cantidad de filas por clase. La salida
#   guardada en el notebook original muestra 645.999 CONTINUA, 5.103 BAJA+1, 4.067 BAJA+2 y 327.892 filas sin
#   clase.
# Parches obligatorios de Data Quality y eliminación de columnas 
dataset[foto_mes == 202105, ccajas_depositos := NA]
if ("cprestamos_personales" %in% colnames(dataset)) {
  dataset[, c("cprestamos_personales", "mprestamos_personales") := NULL]
}
dataset[, clase01 := ifelse(clase_ternaria == "BAJA+2", 1L, 0L)]

print("Control de etiquetas recuperadas en la RAM:")
print(dataset[, .N, by = clase_ternaria])

# [Anotación · líneas 43–58] Toma como columnas a procesar todas menos numero_de_cliente, foto_mes,
#   clase_ternaria, clase01 y los tres períodos auxiliares. Para cada una crea <variable>_lag1 con el valor de
#   la fila anterior del mismo cliente (shift de 1 agrupado por numero_de_cliente, con el dataset ordenado por
#   cliente y período) y <variable>_delta1 como el valor actual menos ese lag. Imprime la cantidad de columnas
#   resultante (457 según la salida guardada en el notebook original).
#%% celda 3 [código]
print("[PASO 3] Generando historia clínica de ORDEN 1 EXCLUSIVA...")
flush.console()

columnas_conductuales <- setdiff(colnames(dataset), c("numero_de_cliente", "foto_mes", "clase_ternaria", "clase01", "periodo0", "periodo1", "periodo2"))

cols_lag1 <- paste0(columnas_conductuales, "_lag1")
dataset[, (cols_lag1) := shift(.SD, n = 1, type = "lag"), by = numero_de_cliente, .SDcols = columnas_conductuales]

for (v in columnas_conductuales) {
  dataset[, paste0(v, "_delta1") := get(v) - get(paste0(v, "_lag1"))]
}

print(paste("[OK] Columnas en RAM:", ncol(dataset)))
flush.console()

# [Anotación · líneas 59–75] Separa las filas de 202103 y 202104 para entrenar y las de 202106 para validar
#   dentro de la optimización. Define campos_buenos_O1: todas las columnas menos las dos clases,
#   numero_de_cliente, foto_mes y los períodos auxiliares (variables originales, lags y deltas). Construye el
#   lgb.Dataset de entrenamiento con etiqueta clase01 y la matriz de validación.
#%% celda 4 [código]
print("[PASO 4] Inicializando la Optimización Bayesiana")
flush.console()

# Partición temporal de control: Marzo y Abril unificados entrenan, Junio valida de forma pura
df_train_bo <- dataset[foto_mes %in% c(202103, 202104)]
df_val_bo   <- dataset[foto_mes == 202106]

campos_buenos_O1 <- setdiff(colnames(dataset), c("clase_ternaria", "clase01", "numero_de_cliente", "foto_mes", "periodo0", "periodo1", "periodo2"))

dtrain_bo_puro <- lgb.Dataset(
  data = data.matrix(df_train_bo[, campos_buenos_O1, with = FALSE]),
  label = df_train_bo$clase01,
  free_raw_data = FALSE
)
matriz_val_bo_puro <- data.matrix(df_val_bo[, campos_buenos_O1, with = FALSE])

# [Anotación · líneas 76–87] Define el espacio de búsqueda con tres hiperparámetros: num_iterations entero
#   entre 500 y 3000, num_leaves entero entre 16 y 63 y min_sum_hessian_in_leaf numérico entre 0,01 y 5,0. Fija
#   set.seed(314159), genera un diseño inicial de 20 puntos con generateDesign y pone en 0 el contador global de
#   evaluaciones.
# Espacio de búsqueda 
obj_space_oficial <- makeParamSet(
  makeIntegerParam("num_iterations",          lower = 500L,  upper = 3000L), 
  makeIntegerParam("num_leaves",              lower = 16L,   upper = 63L),   
  makeNumericParam("min_sum_hessian_in_leaf",  lower = 0.01,  upper = 5.0)    
)

set.seed(314159)
diseno_inicial_oficial <- generateDesign(n = 20L, par.set = obj_space_oficial) # 20 basales

GLOBAL_ITER <- 0

# [Anotación · líneas 88–115] Función objetivo de la optimización. Arma los parámetros de LightGBM con valores
#   fijos (gbdt, objective binary, metric auc, max_bin 31, min_data_in_leaf 0, feature_fraction 0,50,
#   feature_fraction_bynode 0,20, learning_rate 0,005, nthreads 1) y los tres valores del punto evaluado;
#   entrena con nrounds = num_iterations y predice 202106. Ordena por probabilidad descendente, asigna 117.500 a
#   cada BAJA+2 y -27.500 a cada fila restante, suma las primeras 10.000 filas, imprime el resultado y lo
#   devuelve.
funcion_objetivo_oficial <- function(x) {
  GLOBAL_ITER <<- GLOBAL_ITER + 1
  
  params <- list(
    boosting = "gbdt", objective = "binary", metric = "auc", max_bin = 31,
    min_data_in_leaf = 0, feature_fraction = 0.50, feature_fraction_bynode = 0.20,
    learning_rate = 0.005, boost_from_average = TRUE, verbosity = -100, nthreads = 1
  )
  params$num_iterations          <- as.integer(x["num_iterations"])
  params$num_leaves              <- as.integer(x["num_leaves"])
  params$min_sum_hessian_in_leaf <- as.numeric(x["min_sum_hessian_in_leaf"])
  
  modelo <- lgb.train(data = dtrain_bo_puro, params = params, nrounds = params$num_iterations)
  prediccion <- predict(modelo, matriz_val_bo_puro)
  
  tbl_eval <- data.table(clase_ternaria = df_val_bo$clase_ternaria, prob = prediccion)
  setorder(tbl_eval, -prob)
  
  tbl_eval[, ganancia_individual := ifelse(clase_ternaria == "BAJA+2", 117500, -27500)]
  max_ganancia <- tbl_eval[1:10000, sum(ganancia_individual)]
  
  cat(sprintf("[BO] Iteración %02d | Rondas: %d | Hojas: %d | Hessian: %.6f | Ganancia Junio: $%s\n", 
              GLOBAL_ITER, params$num_iterations, params$num_leaves, params$min_sum_hessian_in_leaf, format(max_ganancia, big.mark=".")))
  flush.console()
  
  return(max_ganancia)
}

# [Anotación · líneas 116–125] Envuelve la función como objetivo de un solo criterio a maximizar (minimize =
#   FALSE). Configura mlrMBO con 30 iteraciones, criterio de adquisición Expected Improvement y, como modelo
#   sustituto, kriging (regr.km) con covarianza matern3_2 y predicción con error estándar.
obj_fun_oficial <- makeSingleObjectiveFunction(
  name = "Optimizacion", fn = funcion_objetivo_oficial, par.set = obj_space_oficial, has.simple.signature = FALSE, minimize = FALSE
)

mbo_ctrl <- makeMBOControl()
mbo_ctrl <- setMBOControlTermination(mbo_ctrl, iters = 30L) # 30 MBO inteligentes. Total = 50.
mbo_ctrl <- setMBOControlInfill(mbo_ctrl, crit = makeMBOInfillCritEI())

surr_km <- makeLearner("regr.km", predict.type = "se", covtype = "matern3_2", control = list(trace = FALSE))

# [Anotación · líneas 126–134] Ejecuta mbo() con el diseño inicial de 20 puntos y las 30 iteraciones (50
#   evaluaciones en total), guarda el resultado en optimizacion_marzo_abril_pure.rds y extrae en
#   vector_parametros_campeones el punto que devuelve la búsqueda (run_bayes_oficial$x).
# GATILLADO TEÓRICO DETERMINISTA: Al ejecutarse, este bloque guarda las variables óptimas en 'run_bayes_oficial'
run_bayes_oficial <- mbo(obj_fun_oficial, design = diseno_inicial_oficial, learner = surr_km, control = mbo_ctrl, show.info = FALSE)

# Grabamos el .rds
saveRDS(run_bayes_oficial, file = "optimizacion_marzo_abril_pure.rds")

# EXTRAEMOS EL VECTOR DE PARÁMETROS GANADORES 
vector_parametros_campeones <- run_bayes_oficial$x

# [Anotación · líneas 135–150] Define los meses del entrenamiento final (202103, 202104, 202105 y 202106) y el
#   mes a predecir (202108). Construye el lgb.Dataset final con las columnas de campos_buenos_O1 y etiqueta
#   clase01, y la matriz de 202108.
#%% celda 5 [código]
print("[PASO 5] Configurando matrices finales de producción al 100% de datos usando ORDEN 1 LAGS/DELTAS")
flush.console()

meses_entrenamiento_final <- c(202103, 202104, 202105, 202106)

dataset_train_final  <- dataset[foto_mes %in% meses_entrenamiento_final]
dataset_future_final <- dataset[foto_mes == 202108] # Agosto futuro de producción

dtrain_produccion <- lgb.Dataset(
  data = data.matrix(dataset_train_final[, campos_buenos_O1, with = FALSE]), 
  label = dataset_train_final$clase01, 
  free_raw_data = FALSE
)
matriz_future_produccion <- data.matrix(dataset_future_final[, campos_buenos_O1, with = FALSE])

# [Anotación · líneas 151–163] Arma los parámetros del modelo final: los mismos valores fijos de la función
#   objetivo, más num_leaves y min_sum_hessian_in_leaf tomados del resultado de la optimización.
print("[PASO 6] Lanzando Bagging dinámico de semillas extraídas del vector de la BO...")
flush.console()

params_produccion_dinamicos <- list(
  boosting = "gbdt", objective = "binary", metric = "auc", max_bin = 31, min_data_in_leaf = 0,
  feature_fraction = 0.50, feature_fraction_bynode = 0.20, learning_rate = 0.005,
  boost_from_average = TRUE, verbosity = -100, nthreads = 1,
  # ----------------------------------------------------------------------------
  num_leaves              = as.integer(vector_parametros_campeones["num_leaves"]),
  min_sum_hessian_in_leaf = as.numeric(vector_parametros_campeones["min_sum_hessian_in_leaf"])
  # ----------------------------------------------------------------------------
)

# [Anotación · líneas 164–185] Fija set.seed(314159) y sortea 5 semillas entre 1 y 1.000.000. Para cada una
#   asigna el parámetro seed, entrena un LightGBM sobre los cuatro meses con la cantidad de rondas que devolvió
#   la optimización (num_iterations) y suma su predicción para 202108 a un acumulador que empieza en cero.
set.seed(314159)
# Replicamos tus tandas de 5 en 5 semillas fijas de ese día
total_semillas_finales <- sample(1:1000000, 5)

probabilidades_acumuladas <- rep(0, nrow(dataset_future_final))

for (s in 1:length(total_semillas_finales)) {
  cat(paste0("   -> Entrenando Semilla de Production ", s, " de 5... \n"))
  flush.console()
  
  params_produccion_dinamicos$seed <- total_semillas_finales[s]
  
  # Forzamos las rondas dinámicas extraídas del vector de la BO
  modelo_instancia <- lgb.train(
    data = dtrain_produccion, 
    params = params_produccion_dinamicos, 
    nrounds = as.integer(vector_parametros_campeones["num_iterations"])
  )
  
  probabilidades_acumuladas <- probabilidades_acumuladas + predict(modelo_instancia, matriz_future_produccion)
}

# [Anotación · líneas 186–199] Divide el acumulado por 5 para obtener la probabilidad promedio de cada cliente
#   y ordena de mayor a menor. Escribe en ieh_final_1110.csv el numero_de_cliente de las primeras 10.000 filas,
#   sin encabezado y con tabulador como separador, e imprime un mensaje de fin.
tb_prediccion_definitiva <- data.table(
  numero_de_cliente = as.integer(dataset_future_final$numero_de_cliente), 
  prob = probabilidades_acumuladas / 5
)
setorder(tb_prediccion_definitiva, -prob)

print("[PASO 7] Exportando entregable (Corte 10.000)...")
flush.console()

fwrite(tb_prediccion_definitiva[1:10000, list(numero_de_cliente)], file = "ieh_final_1110.csv", col.names = FALSE, sep = "\t")

print("====================================================================")
print("=== ¡PROCESO GUARDADO CON ÉXITO! ===")
print("====================================================================")
```


## Explicaciones del alumno (texto original)

### README.md

> # primeracompetencia-dmeyf
> Entrega de archivos para reproducir resultados de primera competencia del curso Data Mining para Economía y Finanzas 2026
>
> # 📊 Primera Competencia: Data Mining para Economía y Finanzas 2026
> * **Nombre:** [Isabel Espinoza Herrera]
> ---
>
> ## 🏛️ Resumen Metodológico y Bitácora de Experimentos
> Este repositorio contiene la arquitectura reproducible utilizada para la Primera Competencia de Churn Bancario. El enfoque principal consistió en explotar la atrición conductual de los clientes mediante ventanas móviles de historia clínica transaccional, optimizando los hiperparámetros mediante mlrMBO y controlando la varianza con ensambles masivos de semillas.
>
> A lo largo del proceso experimental, se exploraron  los límites de la infraestructura y el balance de datos, documentando algunas de las siguientes métricas en el Public Leaderboard:
>
> | ID Experimento | Estrategia de Feature Engineering | Hiperparámetros (Hojas / Rondas) | Muestreo / RAM | Ganancia Pública Promedio (\$) | Veredicto / Estado |
> | :--- | :--- | :--- | :--- | :--- | :--- |
> | **EXP-01** | Variables Originales Base | 30 Leaves / 500 Rondas | 100% Datos | \$ 81.200.000 | 
> | **EXP-02 (Récord)** | **Historia Clínica de Orden 1** (Lag1 + Delta1) | **30 Leaves / 2.180 Rondas** | **100% Datos** | **\$ 95.782.500** | **Candidato Elegido** |
> | **EXP-03** | Selección Purificada (Gain > 0) | 16 Leaves / 500 Rondas | 30% Undersampling | \$ 84.865.000 | El más estable |
> | **VARIOS** | Historia Completa Orden 2 (Lag2 + Delta2) |  Leaves / Rondas varias | 100% Datos | *Fallo por OOM / Colapso* | Error Crítico de Infraestructura |
>
> ---
>
> ## 🛠️ Lecciones Aprendidas e Ingeniería de Infraestructura 
>
> ### 1. El Impacto Exponencial del Orden 1
> La incorporación de desfasajes de **Orden 1 (Lags y Deltas a 30 días)** demostró ser el verdadero motor predictivo del modelo, permitiendo que LightGBM identifique patrones nítidos de vaciamiento de cuentas. Esta estrategia empujó la ganancia local y pública de forma neta hacia el récord del laboratorio de **\$95.782.500**.
>
> ### 2. El Desafío de la Alta Dimensionalidad y la Memoria Virtual (Out Of Memory)
> Al intentar profundizar la sensibilidad del modelo incorporando la historia clínica completa de **Orden 2 (Lags 2 y Deltas 2 a 60 días)**, la matriz de datos se expandió originalmente a **753 columnas complejas**. 
> Al entrenar con el 100% de la población (sin undersampling) a lo largo del cuatrimestre acumulado, el volumen matemático colosal saturó de forma iterativa los hilos de cálculo en la Máquina Virtual de 60GB de RAM, provocando:
> * **Bloqueos de hilos (*Deadlocks*)** y congelamiento de semillas individuales (superando los 900 segundos por iteración).
> * **Caídas completas del Kernel de R** por sobrecarga de memoria (*Out of Memory*).
>
> ### 3. Mitigación Híbrida y Criterio de Cierre
> Se probó con diferentes undersamplings, todos dando resultados sub-óptimos. Para solucionar la restricción física de hardware, se diseñó e implementó un algoritmo automatizado de **Selección Híbrida de Características** en R (`lgb.importance()`). Este script extrajo las 30 variables reinas del negocio bancario, calculando el Orden 2 estrictamente sobre este grupo selecto para desinflar la base a 501 dimensiones limpias. Evaluando los costos de cómputo remanentes y priorizando la estabilidad estadística ante el corte rígido de envíos, se optó por consolidar la entrega definitiva bajo la arquitectura consagrada de **30 hojas y 2.180 rondas**, la cual demostró el máximo equilibrio de regularización matemática en la población del banco sin llegar al OOM. Se continuarán explorando estrategias para poder utilizar y explotar la información que los lags y deltas de segundo orden puedan aportar y los métodos que se puedan implementar.

