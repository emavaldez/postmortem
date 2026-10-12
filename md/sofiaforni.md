# Sofía Forni — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: SofiaForni
- Repositorio: https://github.com/SofiaForni/primera_entrega_EYF
- Link posteado: https://github.com/SofiaForni/primera_entrega_EYF
- Commit: 9f53f8122290736616a602a3531fd4cba438a4d6
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/sofiaforni/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/sofiaforni.json

## Resumen

La entrega contiene un notebook de R (forni_primera_entrega.ipynb, 40 celdas, sin salidas guardadas) y un README. El notebook lee competencia_01_crudo.csv, genera clase_ternaria si el archivo no la trae y arma una clase binaria con BAJA+1 y BAJA+2 como positivos. Pasa ccajas_depositos a NA en 202105, calcula lag 1, lag 2, delta 1 y delta 2 de todas las variables por mes calendario y reemplaza cada variable, lag y delta por su ranking con cero fijo dentro de cada foto_mes. Guarda ese dataset en CSV y calcula un diagnóstico de drift con Kolmogorov-Smirnov que no excluye variables. Corre una optimización bayesiana con mlr3mbo (10 evaluaciones, métrica AUC, una semilla) que entrena con 202103 y 202104 y valida en 202106, sin las variables de préstamos personales. Con los hiperparámetros resultantes entrena 20 LightGBM (una semilla cada uno) con 202103 y 202104 para armar una curva de ganancia suavizada de 202106, y otros 20 con 202103 a 202106 para predecir 202108. Promedia las probabilidades de las 20 semillas y escribe un archivo con los primeros k clientes para cada uno de 7 cortes. Según el README, el corte enviado es el de 11.000.

**Qué entrega.** Archivos CSV de una columna, sin encabezado, con los primeros k numero_de_cliente del ranking por probabilidad promedio de 20 modelos, para k = 10.000, 11.000, 11.500, 12.000, 12.040, 12.700 y 12.350 (entregas/entrega_[k]_envios.csv). Según el README, el corte enviado es el de 11.000. El repositorio no incluye los archivos generados.

**Cómo se ejecuta.** Según la sección 8 del README: instalar los paquetes data.table, bbotk, mlr3, mlr3mbo, mlr3learners, DiceKriging y lightgbm; ubicar el dataset en ~/buckets/b1/datasets/competencia_01_crudo.csv (o ajustar PARAM$carpeta_base y PARAM$archivo_dataset); ejecutar las celdas del notebook en orden. El README menciona como opciones PARAM$correr_BO en FALSE para usar PARAM$hiperparametros_manuales, PARAM$columnas_excluidas_modelo, PARAM$envios_manual y PARAM$cortes_envios, y la posibilidad de cargar competencia_01_crudo_FE_rank.csv para no repetir el feature engineering. La sección 6 del README indica que se hicieron 3 corridas finales, una por cada semilla primigenia (501367, 898543 y 500153).

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase01): positivo = BAJA+1 o BAJA+2, negativo = CONTINUA, NA en los meses sin clase. La clase_ternaria se genera en el notebook si el CSV no la trae.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica: la BO, la curva de junio y el modelo final usan todas las filas de sus meses de entrenamiento (bagging_fraction, pos_bagging_fraction y neg_bagging_fraction en 1.0).
- **Calidad de datos:** ccajas_depositos se pasa a NA en 202105 antes de calcular lags y deltas (línea 275), de modo que los lags y deltas que dependen de ese mes también quedan en NA. Los NA no se imputan.
- **Drifting:** Cada variable original, cada lag y cada delta se reemplaza por su ranking con cero fijo dentro de cada foto_mes: los positivos quedan en (0, 1], los negativos en [-1, 0), el 0 queda en 0 y los NA se mantienen. Aparte se calcula el estadístico de Kolmogorov-Smirnov de cada variable rankeada entre 202104 y 202106 y entre 202106 y 202108, sobre muestras de hasta 20.000 filas por mes; la tabla se imprime y no excluye variables.
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** Lag 1 y lag 2 por mes calendario (el mismo cliente uno y dos meses antes; NA si no hay registro) y delta 1 y delta 2 (valor menos lag) de todas las columnas salvo numero_de_cliente, foto_mes, clase_ternaria y clase01. Según el README son 152 variables y 760 columnas nuevas, con los sufijos _rank, _lag1_rank, _lag2_rank, _delta1_rank y _delta2_rank.
- **Selección de variables:** No hay selección por importancia. Las 10 columnas derivadas de cprestamos_personales y mprestamos_personales se excluyen sólo de la optimización bayesiana; la curva de junio y el modelo final las incluyen. PARAM$columnas_excluidas_modelo está vacío. Las columnas sin rankear se eliminan, salvo numero_de_cliente y foto_mes, que entran al modelo sin transformar. Según el README, la BO usa 752 variables y el modelo final 762.
- **Optimización de hiperparámetros:** Optimización bayesiana con bbotk y mlr3mbo (bayesopt_ego, surrogate regr.km de DiceKriging, expected improvement, optimizador de la adquisición por búsqueda al azar de 1.000 evaluaciones). Terminador de 10 evaluaciones; el comentario de la línea 104 indica que el diseño inicial son 12 evaluaciones. Espacio: num_iterations 64 a 4096, num_leaves 16 a 2048, min_sum_hessian_in_leaf 1e-06 a 0.1. Entrena con 202103 y 202104, valida en 202106, métrica AUC, semilla 501367, sin las variables de préstamos personales.
- **Hiperparámetros finales:** Fijos en el código: boosting gbdt, objective binary, learning_rate 0.005, feature_fraction 0.50, feature_fraction_bynode 0.20, min_data_in_leaf 0, max_bin 31, max_depth -1, lambda_l1 0, lambda_l2 0, fracciones de bagging 1.0, early_stopping 0. num_iterations, num_leaves y min_sum_hessian_in_leaf se toman de la fila de mayor AUC del log de la BO; el notebook no tiene salidas guardadas. Según el README: num_iterations 4028, num_leaves 1226, min_sum_hessian_in_leaf 0.00477222. Esos mismos valores figuran en PARAM$hiperparametros_manuales, que el código usa sólo si PARAM$correr_BO es FALSE.
- **Semillas:** 20 semillas generadas en el código: para cada primigenia se llama a set.seed y a sample(100000:999999, n), con 501367 (5 semillas), 898543 (10) y 500153 (5). Las mismas 20 se usan en la curva de junio y en el modelo final. La BO y el muestreo del diagnóstico de drift usan PARAM$semilla_primigenia, 501367.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio aritmético de las probabilidades de 20 modelos LightGBM con los mismos hiperparámetros y distinta semilla, leídas de los archivos prob_semilla_[semilla].csv.
- **Corte:** Cantidades fijas escritas en el código (línea 795): 10.000, 11.000, 11.500, 12.000, 12.040, 12.700 y 12.350 clientes, un archivo por cada una. Según el README, el corte enviado es 11.000, y la curva de ganancia de junio se usa para elegir el corte. Esa curva calcula el corte de mayor ganancia suavizada (k_junio) y una meseta (cortes con ganancia mayor o igual al 99% del máximo), que se imprimen y grafican; esos valores no entran en el código que escribe los archivos.
- **Validación:** Un mes posterior al entrenamiento: 202106. La BO entrena con 202103 y 202104 (el comentario de la línea 82 dice 'sin mayo a proposito') y mide AUC en 202106 con una semilla. La curva de ganancia entrena 20 modelos con 202103 y 202104, promedia sus probabilidades de 202106 y calcula la ganancia acumulada con 1.072.500 por BAJA+2 y -27.500 por cualquier otra clase, para cortes de 3.500 a 20.500 cada 50, con media móvil centrada de 21 puntos.
- **Salidas:** En ~/buckets/b1/datasets: competencia_01_crudo_FE_rank.csv. En ~/buckets/b1/experimentos/primer_entrega_piloto_FE_rank_20semillas: BO_log.txt, prob_semillas_parcial.rds, probs_semillas/prob_semilla_[semilla].csv (uno por semilla), ranking_prob_promedio.csv y entregas/entrega_[k]_envios.csv para 7 cortes.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: sí
- Entorno declarado: El notebook rotula sus rutas como 'adaptadas para VM de cloud', con base en ~/buckets/b1. El README lista los paquetes a instalar sin versiones. Los metadatos del notebook registran kernel R (ir), versión 4.6.1. El entrenamiento de la curva de junio fija num_threads en 4. No se declara sistema operativo ni tamaño de máquina.

## Pasos del camino de la entrega

1. **Parámetros de la corrida.** Se define la lista PARAM: semilla primigenia 501367, 20 semillas derivadas de tres primigenias (5 de 501367, 10 de 898543 y 5 de 500153), rutas con base en ~/buckets/b1, meses de cada etapa, variables de préstamos que quedan fuera de la BO, 10 evaluaciones de la BO y ganancia de 1.072.500 por BAJA+2 y -27.500 por el resto. Se listan los parámetros fijos de LightGBM y el espacio de búsqueda de tres hiperparámetros. (`forni_primera_entrega.ipynb` líneas 52–113; `forni_primera_entrega.ipynb` líneas 115–164)
2. **Lectura del dataset y armado de las clases.** Se lee competencia_01_crudo.csv. Si no trae clase_ternaria, se genera a partir de los períodos siguientes de cada cliente. Se verifica que existan los meses necesarios, que los meses de entrenamiento final tengan clase y que 202108 tenga un registro por cliente. Se crea clase01 con BAJA+1 y BAJA+2 en 1 y CONTINUA en 0. (`forni_primera_entrega.ipynb` líneas 203–254)
3. **Corrección de ccajas_depositos y claves para los lags.** Se conservan los meses 202103 a 202108, se pasa ccajas_depositos a NA en 202105 y se arma una clave por cliente y período para ubicar la fila del mismo cliente uno y dos meses antes. Las variables a transformar son todas las columnas salvo numero_de_cliente, foto_mes, clase_ternaria y clase01. (`forni_primera_entrega.ipynb` líneas 269–290)
4. **Lags, deltas y ranking con cero fijo por mes.** Para cada variable se arman 5 versiones (valor, lag 1, lag 2, delta 1 y delta 2) y cada una se reemplaza por su ranking con cero fijo dentro de cada foto_mes: positivos en (0, 1], negativos en [-1, 0), cero en 0 y NA sin imputar. Se eliminan las columnas sin rankear, salvo numero_de_cliente, foto_mes y las clases. (`forni_primera_entrega.ipynb` líneas 292–345)
5. **Chequeos y guardado del dataset con feature engineering.** Se verifica el rango de las columnas nuevas, los NA esperados en los lags de 202103 y 202104 y en ccajas_depositos, y la presencia de las columnas de préstamos. El dataset completo se escribe en competencia_01_crudo_FE_rank.csv; según el README tiene 983.061 filas y 764 columnas. (`forni_primera_entrega.ipynb` líneas 347–387; `README.md` líneas 44–46)
6. **Diagnóstico de drift.** Sobre muestras de hasta 20.000 filas por mes se calcula el estadístico de Kolmogorov-Smirnov de cada variable rankeada entre 202104 y 202106 (referencia) y entre 202106 y 202108 (futuro). Se imprimen las 25 variables de mayor ks_futuro. La tabla no cambia el conjunto de variables. (`forni_primera_entrega.ipynb` líneas 396–428)
7. **Conjuntos de variables y datasets de LightGBM.** Se arman dos listas: campos_modelo (numero_de_cliente, foto_mes y todas las columnas rankeadas) y campos_bo (las mismas sin las 10 columnas de préstamos personales). Con 202103 y 202104 como entrenamiento y 202106 como validación, sin submuestreo, se construyen los lgb.Dataset de la BO y el de entrenamiento de la curva de junio. Según el README son 326.184 filas de entrenamiento y 164.114 de validación. (`forni_primera_entrega.ipynb` líneas 441–488; `README.md` líneas 50–62)
8. **Optimización bayesiana.** Con bbotk y mlr3mbo se evalúan 10 combinaciones de num_iterations, num_leaves y min_sum_hessian_in_leaf. Cada evaluación entrena un LightGBM con 202103 y 202104, mide AUC en 202106 y registra el resultado en BO_log.txt. Se toman los hiperparámetros de la fila de mayor AUC; si PARAM$correr_BO es FALSE se usan los manuales. (`forni_primera_entrega.ipynb` líneas 495–588)
9. **Curva de ganancia de 202106.** Se entrenan 20 modelos (una semilla cada uno) con 202103 y 202104 y campos_modelo, y se promedian sus probabilidades de 202106. Se calcula la ganancia acumulada para cortes de 3.500 a 20.500 cada 50, se suaviza con media móvil centrada de 21 puntos, se ubica el corte de mayor ganancia suavizada y la meseta de valores mayores o iguales al 99% del máximo, y se grafica. (`forni_primera_entrega.ipynb` líneas 600–669)
10. **Modelo final y predicción de 202108.** Se entrena un LightGBM por cada una de las 20 semillas con 202103, 202104, 202105 y 202106, las variables de campos_modelo y los mismos hiperparámetros. Cada modelo predice 202108 y sus probabilidades se guardan en un archivo por semilla. Según el README el entrenamiento tiene 654.066 filas y 202108 tiene 164.647 clientes. (`forni_primera_entrega.ipynb` líneas 676–711; `README.md` líneas 85–85)
11. **Promedio de las semillas y ranking.** Se leen todos los archivos de probabilidades por semilla, se unen por numero_de_cliente, se promedian y se ordenan de mayor a menor probabilidad en ranking_prob_promedio.csv. La operación aparece en dos celdas consecutivas de código, con distinto nombre de columnas y distinto chequeo de clientes. (`forni_primera_entrega.ipynb` líneas 713–746; `forni_primera_entrega.ipynb` líneas 756–785)
12. **Archivos de envío.** Para cada corte de la lista 10.000, 11.000, 11.500, 12.000, 12.040, 12.700 y 12.350 se escribe entregas/entrega_[k]_envios.csv con los primeros k numero_de_cliente del ranking, sin encabezado. El README declara que el corte enviado es 11.000 y lista además cortes de 12.500 y 13.000. (`forni_primera_entrega.ipynb` líneas 787–806; `README.md` líneas 4–4; `README.md` líneas 89–89)

## Archivos

- `forni_primera_entrega.ipynb` · principal · Jupyter (R) · 806 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/sofiaforni/forni_primera_entrega.ipynb.txt) — Notebook de R con 40 celdas (14 de texto y 26 de código, sin salidas guardadas) que contiene todo el camino: parámetros, lectura, feature engineering con lags, deltas y ranking con cero fijo, diagnóstico de drift, optimización bayesiana, curva de ganancia de 202106, modelo final de 20 semillas y archivos de envío.
- `README.md` · explicacion · Markdown · 107 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/sofiaforni/README.md.txt) — Texto de presentación en 8 secciones: resumen del enfoque, flujo del notebook, feature engineering, modelo, elección del corte de envíos, modelo final y archivos generados, reproducibilidad y cómo correrlo. Declara que el corte enviado es 11.000, los hiperparámetros resultantes de la BO, las cantidades de filas y de bajas de cada conjunto y las semillas primigenias de las 3 corridas finales.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### forni_primera_entrega.ipynb

Notebook de R con 40 celdas (14 de texto y 26 de código, sin salidas guardadas) que contiene todo el camino: parámetros, lectura, feature engineering con lags, deltas y ranking con cero fijo, diagnóstico de drift, optimización bayesiana, curva de ganancia de 202106, modelo final de 20 semillas y archivos de envío.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–21] Celda de texto inicial. Enumera el flujo en 7 pasos (carga, feature engineering,
#   diagnóstico de drift, optimización bayesiana, curva de ganancia de junio, modelo final y CSV de envío) y los
#   cambios respecto del notebook base. Indica que la BO usa PARAM$semilla_primigenia con valor 898543; la línea
#   54 del código le asigna 501367.
#%% celda 1 [texto]
# Primera entrega piloto: feature engineering con ranking + LightGBM (BO, 20 semillas)

**Flujo**
1. Carga de datos y chequeos
2. Feature engineering: `ccajas_depositos` roto en 202105, lags y deltas 1 y 2, y ranking con cero fijo dentro de cada mes
3. Diagnóstico de data drift (sobre las variables rankeadas)
4. Optimización bayesiana: entrena con **marzo + abril**, valida en **junio** (métrica AUC, una sola semilla)
5. Curva de ganancia de junio con `n_semillas` semillas, para elegir el corte
6. Modelo final con **marzo + abril + mayo + junio** y `n_semillas` semillas; la probabilidad de agosto es el promedio
7. CSV de envío: uno por defecto (corte de la curva suavizada) y uno por cada valor de `PARAM$cortes_envios`

**Cambios respecto del notebook base**
* Feature engineering antes de cualquier entrenamiento; el modelo usa las variables rankeadas más `numero_de_cliente` y `foto_mes` sin transformar (sin ranking ni lags).
* `cprestamos_personales` y `mprestamos_personales` pasan por el feature engineering, pero **no se usan en la BO**; sí en la curva de junio y en el modelo final.
* El dataset completo con el feature engineering se guarda en CSV (`PARAM$archivo_dataset_fe`) para poder volver a cargarlo sin repetir el FE.
* Sin undersampling en ningún paso (BO, curva y modelo final).
* `feature_fraction_bynode = 0.20` fijo; la BO optimiza `num_iterations`, `num_leaves` y `min_sum_hessian_in_leaf`.
* Métrica de la BO: AUC. La BO corre con una sola semilla.
* `PARAM$semillas_por_primigenia` define las semillas de la curva de junio y del modelo final (las mismas en ambos): 5 generadas con la primigenia 501367, 10 con 898543 y 5 con 500153, 20 en total (`PARAM$n_semillas`). La BO usa una sola semilla (`PARAM$semilla_primigenia`, 898543).
* La BO hace 10 evaluaciones.

# [Anotación · líneas 23–45] Imprime la fecha y hora, borra los objetos de la sesión y carga 8 paquetes:
#   data.table, bbotk, mlr3, mlr3mbo, mlr3learners, paradox, DiceKriging y lightgbm. La instalación de paquetes
#   figura en una línea comentada.
#%% celda 2 [código]
format(Sys.time(), "%a %b %d %X %Y")

#%% celda 3 [texto]
## 1. Inicio y librerías

#%% celda 4 [código]
# limpio la memoria
rm(list=ls(all.names=TRUE))
gc(full=TRUE, verbose=FALSE)

#%% celda 5 [código]
# Si falta algun paquete, descomentar:
#install.packages(c("data.table", "bbotk", "mlr3", "mlr3mbo", "mlr3learners", "DiceKriging", "lightgbm"))

library(data.table)
library(bbotk)
library(mlr3)
library(mlr3mbo)
library(mlr3learners)
library(paradox)
library(DiceKriging)
library(lightgbm)

# [Anotación · líneas 47–71] Crea la lista PARAM. Fija la semilla primigenia en 501367 y define cuántas
#   semillas se generan a partir de cada primigenia: 5 con 501367, 10 con 898543 y 5 con 500153 (20 en total).
#   Para cada primigenia llama a set.seed y sortea esa cantidad de enteros entre 100000 y 999999; verifica que
#   sean 20 y que no haya repetidas. El nombre del experimento queda en
#   primer_entrega_piloto_FE_rank_20semillas.
#%% celda 6 [texto]
## 2. Parámetros

Todo lo que se puede querer cambiar está en esta celda.

#%% celda 7 [código]
PARAM <- list()
PARAM$semilla_primigenia <- 501367


# semillas para la curva de junio y para el modelo final (la BO usa una sola semilla: semilla_primigenia)
# nombre = semilla primigenia, valor = cantidad de semillas que se generan a partir de ella
PARAM$semillas_por_primigenia <- c("501367"= 5, "898543"= 10, "500153"= 5)
PARAM$n_semillas <- sum(PARAM$semillas_por_primigenia)   # 20 en total
PARAM$experimento <- paste0("primer_entrega_piloto_FE_rank_", PARAM$n_semillas, "semillas")

# las semillas se generan de forma reproducible: para cada primigenia, set.seed() + sample()
PARAM$semillas <- unlist(lapply(names(PARAM$semillas_por_primigenia), function(prim) {
  set.seed(as.integer(prim))
  sample(100000:999999, PARAM$semillas_por_primigenia[[prim]])
}), use.names= FALSE)

# la curva de junio y el modelo final usan las mismas semillas
stopifnot(PARAM$n_semillas >= 1, length(PARAM$semillas) == PARAM$n_semillas,
          !anyDuplicated(PARAM$semillas))

# [Anotación · líneas 73–100] Define las rutas con base en ~/buckets/b1 (dataset en
#   datasets/competencia_01_crudo.csv y dataset con feature engineering en competencia_01_crudo_FE_rank.csv) y
#   los meses de cada etapa: feature engineering 202103 a 202108, entrenamiento de la BO 202103 y 202104,
#   validación 202106, entrenamiento final 202103 a 202106 y predicción 202108. Declara las dos variables de
#   préstamos personales que quedan fuera de la BO, una lista vacía de columnas a excluir del modelo, los
#   límites de envíos 8.000 y 15.000 y una secuencia de cortes de 8.000 a 15.000 cada 1.000. PARAM$envios_min,
#   envios_max, envios_manual y cortes_envios no se referencian en las celdas de código posteriores.
# --- RUTAS ADAPTADAS PARA VM DE CLOUD ---
PARAM$carpeta_base <- path.expand("~/buckets/b1")
PARAM$archivo_dataset <- file.path(PARAM$carpeta_base, "datasets/competencia_01_crudo.csv")

# dataset completo con el feature engineering (mismo lugar que el original, con FE en el nombre)
PARAM$archivo_dataset_fe <- file.path(dirname(PARAM$archivo_dataset), "competencia_01_crudo_FE_rank.csv")

# meses
PARAM$meses_fe    <- 202103:202108                       # meses con los que se hace el feature engineering
PARAM$train_bo    <- c(202103, 202104)                   # entrena la BO (sin mayo a proposito)
PARAM$validate_bo <- c(202106)                           # valida la BO y arma la curva de ganancia
PARAM$train_final <- c(202103, 202104, 202105, 202106)   # modelo final
PARAM$future      <- c(202108)                           # mes a predecir (sin clase)

# variables que pasan por el feature engineering pero NO se usan en la Bayesian Optimization
# (si en la curva de junio y el modelo final); numero_de_cliente y foto_mes no tienen FE y se usan en todo el proceso
PARAM$variables_fuera_bo <- c("cprestamos_personales", "mprestamos_personales")

# columnas ya rankeadas que se quieren sacar del modelo (nombres exactos, por ejemplo "mcuentas_saldo_lag1_rank")
PARAM$columnas_excluidas_modelo <- character(0)

# cantidad de envios permitida por la campania
PARAM$envios_min <- 8000
PARAM$envios_max <- 15000
PARAM$envios_manual <- NA    # poner un numero (8000-15000) para reemplazar el corte por defecto (el de la curva suavizada)

# ademas del CSV por defecto, se escribe un CSV por cada uno de estos cortes
PARAM$cortes_envios <- seq(8000, 15000, by= 1000)

# [Anotación · líneas 102–113] Activa la optimización bayesiana (correr_BO en TRUE) con 10 evaluaciones; el
#   comentario indica que el diseño inicial son 12 evaluaciones (4 por cada uno de los 3 parámetros). Define
#   hiperparámetros manuales (num_iterations 4028, num_leaves 1226, min_sum_hessian_in_leaf 0.00477222056195233)
#   que se usan sólo si correr_BO es FALSE. Fija la ganancia por envío: 1.072.500 para BAJA+2 y -27.500 para
#   cualquier otra clase.
# Bayesian Optimization
PARAM$correr_BO <- TRUE
# el diseno inicial son 12 evaluaciones (4 x 3 parametros): con 10 iteraciones se evalua solo el diseno inicial, sin evaluaciones guiadas por el modelo
PARAM$hyperparametertuning$iteraciones <- 10
# se usan solo si correr_BO es FALSE (vienen de una corrida anterior con otras variables y otros meses: reemplazar)
PARAM$hiperparametros_manuales <- list(
  num_iterations= 4028L, num_leaves= 1226L, min_sum_hessian_in_leaf= 0.00477222056195233
)

# ganancia por envio
PARAM$ganancia_acierto <- 1072500   # BAJA+2
PARAM$ganancia_error   <- -27500    # cualquier otra clase

# [Anotación · líneas 115–164] Lista los parámetros fijos de LightGBM: boosting gbdt, objective binary, metric
#   auc, max_bin 31, learning_rate 0.005, feature_fraction 0.50, feature_fraction_bynode 0.20, min_data_in_leaf
#   0, max_depth -1, lambda_l1 y lambda_l2 en 0, fracciones de bagging en 1.0, early_stopping 0, deterministic
#   TRUE y seed igual a la semilla primigenia. Define el espacio de búsqueda de la BO: num_iterations entre 64 y
#   4096, num_leaves entre 16 y 2048 y min_sum_hessian_in_leaf entre 1e-06 y 0.1.
#%% celda 8 [código]
# Parametros fijos del LightGBM; la BO pisa los tres de abajo
PARAM$lgbm$param_fijos <- list(
  boosting= "gbdt",
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
  min_data_in_leaf= 0,          # fijo, muy importante
  feature_fraction= 0.50,       # fijo
  feature_fraction_bynode= 0.20,# fijo
  learning_rate= 0.005,         # fijo, muy importante

  num_iterations= 20000,     # se modificara
  num_leaves= 1024,          # se modificara
  min_sum_hessian_in_leaf= 1e-06  # se modificara
)

# Espacio de busqueda de la BO
PARAM$hyperparametertuning$hs <- ps(
  num_iterations= p_int(lower= 64L, upper= 4096L),
  num_leaves= p_int(lower= 16L, upper= 2048L),
  min_sum_hessian_in_leaf= p_dbl(lower= 1e-06, upper= 0.1)
)

# [Anotación · líneas 166–196] Define tres funciones. loguear agrega a un archivo de log una línea con fecha y
#   valores separados por tabulador, con encabezado la primera vez. curva_ganancia asigna a cada fila la
#   ganancia de acierto o de error según sea BAJA+2 o no, ordena por probabilidad descendente, acumula y
#   devuelve la ganancia acumulada en cada corte pedido. tabla_bajas cuenta por mes los clientes, los BAJA+1,
#   los BAJA+2 y la suma de ambos.
#%% celda 9 [texto]
## 3. Funciones auxiliares

#%% celda 10 [código]
# escribe una linea en el log de la BO (con encabezado la primera vez)
loguear <- function(reg, arch, verbose= TRUE) {
  linea <- paste0(format(Sys.time(), "%Y%m%d.%H%M%S"), "\t",
                  paste(unlist(reg), collapse= "\t"), "\n")
  if (!file.exists(arch)) {
    cat(paste0("fecha\t", paste(names(reg), collapse= "\t"), "\n"), file= arch)
  }
  cat(linea, file= arch, append= TRUE)
  if (verbose) cat(linea)
}

# ganancia acumulada para una cantidad de envios, ordenando por probabilidad descendente
curva_ganancia <- function(prob, clase_ternaria, cortes) {
  gan <- ifelse(clase_ternaria == "BAJA+2", PARAM$ganancia_acierto, PARAM$ganancia_error)
  acumulada <- cumsum(gan[order(prob, decreasing= TRUE)])
  data.table(envios= cortes, ganancia= acumulada[cortes])
}

# cantidad de clientes y de bajas (BAJA+1 y BAJA+2) por mes, para comparar con el corte elegido
tabla_bajas <- function(meses) {
  dataset[foto_mes %in% meses, list(
    clientes = .N,
    baja1    = sum(clase_ternaria == "BAJA+1", na.rm= TRUE),
    baja2    = sum(clase_ternaria == "BAJA+2", na.rm= TRUE),
    bajas    = sum(clase_ternaria %in% c("BAJA+1", "BAJA+2"))
  ), by= foto_mes][order(foto_mes)]
}

# [Anotación · líneas 198–238] Lee el dataset con fread e imprime filas y columnas. Si no trae clase_ternaria,
#   la genera: convierte foto_mes a un número de período, obtiene para cada cliente los dos períodos siguientes
#   y asigna CONTINUA, BAJA+1 (sin registro en el período siguiente) o BAJA+2 (con registro en el siguiente y
#   sin registro en el subsiguiente), dejando sin clase el último período (en el anteúltimo sólo se asigna
#   BAJA+1). Imprime la cantidad de filas por mes y clase desde 202103.
#%% celda 11 [texto]
## 4. Carga de datos y chequeos

Si el CSV ya trae `clase_ternaria` se usa tal cual; si no, se genera con la misma lógica (con todos los meses del archivo, antes de filtrar).

#%% celda 12 [código]
dataset <- fread(PARAM$archivo_dataset, stringsAsFactors= TRUE)
cat("filas:", nrow(dataset), "  columnas:", ncol(dataset), "\n")

#%% celda 13 [código]
if (!("clase_ternaria" %in% names(dataset))) {
  cat("El dataset no tiene clase_ternaria: la genero\n")

  dsimple <- dataset[, list(
    "pos" = .I,
    numero_de_cliente,
    periodo0 = as.integer(foto_mes/100)*12 + foto_mes%%100)]

  setorder(dsimple, numero_de_cliente, periodo0)

  periodo_ultimo <- dsimple[, max(periodo0)]
  periodo_anteultimo <- periodo_ultimo - 1

  dsimple[, c("periodo1", "periodo2") :=
            shift(periodo0, n= 1:2, fill= NA, type= "lead"), numero_de_cliente]

  dsimple[periodo0 < periodo_anteultimo, clase_ternaria := "CONTINUA"]

  dsimple[periodo0 < periodo_ultimo &
            (is.na(periodo1) | periodo0 + 1 < periodo1),
          clase_ternaria := "BAJA+1"]

  dsimple[periodo0 < periodo_anteultimo & (periodo0 + 1 == periodo1) &
            (is.na(periodo2) | periodo0 + 2 < periodo2),
          clase_ternaria := "BAJA+2"]

  setorder(dsimple, pos)
  dataset[, clase_ternaria := dsimple$clase_ternaria]
}

dataset[foto_mes >= 202103, .N, list(foto_mes, clase_ternaria)][order(foto_mes, clase_ternaria)]

# [Anotación · líneas 240–254] Verifica con stopifnot que existan todos los meses necesarios, que los meses de
#   entrenamiento final no tengan clase NA y que 202108 tenga un registro por cliente. Crea clase01: 1 para
#   BAJA+1 y BAJA+2, 0 para CONTINUA y NA donde no hay clase.
#%% celda 14 [código]
# chequeos: los meses existen, los de entrenamiento tienen clase, y agosto tiene un registro por cliente
meses_necesarios <- unique(c(PARAM$meses_fe, PARAM$train_bo, PARAM$validate_bo, PARAM$train_final, PARAM$future))
stopifnot(all(meses_necesarios %in% unique(dataset$foto_mes)))

stopifnot(!any(is.na(dataset[foto_mes %in% PARAM$train_final, clase_ternaria])))
stopifnot(!anyDuplicated(dataset[foto_mes %in% PARAM$future, numero_de_cliente]))

cat("clientes en el mes a predecir:", dataset[foto_mes %in% PARAM$future, .N], "\n")

#%% celda 15 [código]
# clase binaria: BAJA+1 y BAJA+2 = 1, CONTINUA = 0 (queda NA donde no hay clase, por ejemplo agosto)
dataset[, clase01 := NA_integer_]
dataset[!is.na(clase_ternaria),
        clase01 := ifelse(clase_ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)]

# [Anotación · líneas 256–290] Celda de texto con los 5 pasos del feature engineering y primera celda de
#   código de esa etapa: conserva los meses 202103 a 202108, pasa ccajas_depositos a NA en 202105 y arma una
#   clave numérica por cliente y período para ubicar con match la fila del mismo cliente un mes y dos meses
#   antes (NA si no existe). Define como variables a transformar todas las columnas salvo numero_de_cliente,
#   foto_mes, clase_ternaria y clase01, y verifica que sean numéricas.
#%% celda 16 [texto]
## 5. Feature engineering

Se hace **antes de cualquier entrenamiento**, en este orden:

1. **`ccajas_depositos` roto en 202105.** Todos sus valores son 0 ese mes, así que se pasa a `NA` solo en 202105. Se hace primero, para que los lags y deltas que dependen de ese valor también queden en `NA`.
2. **Lags y deltas 1 y 2** (marzo a agosto) para todas las variables, menos `foto_mes`, `numero_de_cliente` y la clase ternaria (y `clase01`). Esto incluye `cprestamos_personales` y `mprestamos_personales` (`PARAM$variables_fuera_bo`), que después se dejan afuera solo de la BO.
   * Los lags se calculan por **mes calendario** (el lag 1 de un registro es el mismo cliente un mes antes, el lag 2 dos meses antes). Si no hay registro de ese mes, queda `NA`: marzo no tiene lags y abril no tiene lag 2.
   * El delta es la **diferencia simple**: `delta1 = valor_t - valor_t-1` y `delta2 = valor_t - valor_t-2`.
3. **Ranking con cero fijo, dentro de cada `foto_mes`,** sobre las variables originales, los lags y los deltas: los valores negativos se ordenan entre sí y quedan en [-1, 0), los positivos en (0, 1], y el 0 queda en 0. Los `NA` se mantienen (no se imputa nada).
4. Se eliminan todas las variables sin rankear, **salvo `numero_de_cliente`, `foto_mes` y las clases**, que se conservan sin transformar: el modelo usa las nuevas (`_rank`, `_lag1_rank`, `_lag2_rank`, `_delta1_rank`, `_delta2_rank`) más `numero_de_cliente` y `foto_mes`.
5. Se guarda el dataset completo con el feature engineering (`PARAM$archivo_dataset_fe`).

#%% celda 17 [código]
# me quedo con los meses del feature engineering
dataset <- dataset[foto_mes %in% PARAM$meses_fe]

# paso 1: ccajas_depositos esta roto en 202105 (todos ceros) -> NA solo en ese mes
stopifnot("ccajas_depositos" %in% names(dataset))
dataset[foto_mes == 202105, ccajas_depositos := NA]

# paso 2: claves para encontrar el mismo cliente 1 y 2 meses antes (por mes calendario)
periodo <- (dataset$foto_mes %/% 100L) * 12L + dataset$foto_mes %% 100L
clave <- as.numeric(dataset$numero_de_cliente) * 1000 + (periodo - min(periodo))
stopifnot(!anyDuplicated(clave))

idx_lag1 <- match(clave - 1, clave)   # NA si no hay registro del mes anterior
idx_lag2 <- match(clave - 2, clave)   # NA si no hay registro de hace dos meses

# variables sobre las que se hace el feature engineering
cols_no_fe <- c("numero_de_cliente", "foto_mes", "clase_ternaria", "clase01")
vars_fe <- setdiff(names(dataset), cols_no_fe)
stopifnot(all(PARAM$variables_fuera_bo %in% vars_fe))   # los prestamos tambien pasan por el FE
stopifnot(all(sapply(vars_fe, function(v) is.numeric(dataset[[v]]))))
cat("variables para el feature engineering:", length(vars_fe), "\n")

# [Anotación · líneas 292–345] Define rank_cero_fijo: deja el 0 en 0, asigna a los positivos su rango (empates
#   promediados) dividido por la cantidad de positivos y a los negativos el rango de su valor absoluto, con
#   signo negativo, dividido por la cantidad de negativos; los NA quedan NA. rank_por_mes aplica esa función
#   dentro de cada foto_mes. Para cada variable arma 5 versiones (valor, lag 1, lag 2, valor menos lag 1 y valor
#   menos lag 2), rankea cada una por mes y la guarda con los sufijos _rank, _lag1_rank, _lag2_rank,
#   _delta1_rank y _delta2_rank. Luego borra las columnas sin rankear, salvo las 4 excluidas, y agrega las
#   nuevas.
#%% celda 18 [código]
# ranking 

rank_cero_fijo <- function(x) {
  out <- rep(NA_real_, length(x))
  ok <- !is.na(x)
  out[ok & x == 0] <- 0

  pos <- which(ok & x > 0)
  if (length(pos) > 0) out[pos] <- frank(x[pos], ties.method= "average") / length(pos)

  neg <- which(ok & x < 0)
  if (length(neg) > 0) out[neg] <- -frank(-x[neg], ties.method= "average") / length(neg)

  out
}

# aplica el ranking dentro de cada foto_mes
filas_por_mes <- split(seq_len(nrow(dataset)), dataset$foto_mes)

rank_por_mes <- function(x) {
  out <- rep(NA_real_, length(x))
  for (ii in filas_por_mes) out[ii] <- rank_cero_fijo(x[ii])
  out
}

sufijos <- c("_rank", "_lag1_rank", "_lag2_rank", "_delta1_rank", "_delta2_rank")
nuevas <- vector("list", length(vars_fe) * length(sufijos))
nombres_nuevas <- character(length(nuevas))
k <- 0L

for (v in vars_fe) {
  x  <- as.numeric(dataset[[v]])
  l1 <- x[idx_lag1]
  l2 <- x[idx_lag2]
  versiones <- list(x, l1, l2, x - l1, x - l2)

  for (j in seq_along(versiones)) {
    k <- k + 1L
    nuevas[[k]] <- rank_por_mes(versiones[[j]])
    nombres_nuevas[k] <- paste0(v, sufijos[j])
  }
}
names(nuevas) <- nombres_nuevas

# elimino todas las variables sin rankear y agrego las rankeadas
cols_borrar <- setdiff(names(dataset), cols_no_fe)
dataset[, (cols_borrar) := NULL]
dataset[, (nombres_nuevas) := nuevas]

rm(nuevas, versiones, x, l1, l2, idx_lag1, idx_lag2, clave, periodo)
gc(full= TRUE, verbose= FALSE)

cat("filas:", nrow(dataset), "  columnas:", ncol(dataset), "\n")

# [Anotación · líneas 347–387] Verifica con stopifnot que las columnas nuevas estén entre -1 y 1, que los lag
#   1 sean NA en 202103 y los lag 2 en 202103 y 202104, que ccajas_depositos sea NA en 202105, en su lag 1 de
#   202106 y en su lag 2 de 202107, que numero_de_cliente y foto_mes sigan sin transformar y que existan las 10
#   columnas de préstamos. Imprime la cantidad de variables nuevas y la proporción de NA por mes. Escribe el
#   dataset completo en PARAM$archivo_dataset_fe con fwrite.
#%% celda 19 [código]
# chequeos del feature engineering
rangos <- suppressWarnings(dataset[, lapply(.SD, function(z) c(min(z, na.rm= TRUE), max(z, na.rm= TRUE))),
                                   .SDcols= nombres_nuevas])
rangos <- unlist(rangos)
rangos <- rangos[is.finite(rangos)]
stopifnot(all(rangos >= -1 & rangos <= 1))

# marzo no tiene lags; abril no tiene lag 2
cols_lag1 <- grep("_lag1_rank$", nombres_nuevas, value= TRUE)
cols_lag2 <- grep("_lag2_rank$", nombres_nuevas, value= TRUE)
stopifnot(all(sapply(cols_lag1, function(v) dataset[foto_mes == 202103, all(is.na(get(v)))])))
stopifnot(all(sapply(cols_lag2, function(v) dataset[foto_mes %in% c(202103, 202104), all(is.na(get(v)))])))

# ccajas_depositos: NA en 202105, y por arrastre en el lag 1 de junio, el lag 2 de julio y los deltas que dependen de mayo
stopifnot(dataset[foto_mes == 202105, all(is.na(ccajas_depositos_rank))])
stopifnot(dataset[foto_mes == 202106, all(is.na(ccajas_depositos_lag1_rank))])
stopifnot(dataset[foto_mes == 202107, all(is.na(ccajas_depositos_lag2_rank))])

# numero_de_cliente y foto_mes: siguen en el dataset, sin ranking ni lags (valores originales)
stopifnot(all(c("numero_de_cliente", "foto_mes") %in% names(dataset)))
stopifnot(!any(grepl("^(numero_de_cliente|foto_mes)_", names(dataset))))
stopifnot(all(dataset$foto_mes %in% PARAM$meses_fe), !anyNA(dataset$numero_de_cliente))

# los prestamos pasaron por el FE (5 columnas cada uno)
cols_prestamos <- as.vector(outer(PARAM$variables_fuera_bo, sufijos, paste0))
stopifnot(all(cols_prestamos %in% names(dataset)))

cat("variables nuevas:", length(nombres_nuevas), "\n")
cat("proporcion de NA por mes (promedio de todas las variables nuevas):\n")
print(dataset[, list(prop_NA= mean(is.na(unlist(.SD)))), by= foto_mes, .SDcols= nombres_nuevas][order(foto_mes)])

#%% celda 20 [texto]
### Guardado del dataset con feature engineering

Se guarda el dataset **completo** (`numero_de_cliente`, `foto_mes`, `clase_ternaria`, `clase01` y todas las variables rankeadas, incluidos los préstamos) en la misma carpeta que el archivo original. Para el entrenamiento final se puede volver a cargar con `fread(PARAM$archivo_dataset_fe, stringsAsFactors= TRUE)` sin repetir el feature engineering.

#%% celda 21 [código]
fwrite(dataset, PARAM$archivo_dataset_fe)
cat("dataset con FE guardado en:", PARAM$archivo_dataset_fe, "\n")
cat("filas:", nrow(dataset), "  columnas:", ncol(dataset), "\n")

# [Anotación · líneas 389–428] Con la semilla 501367 toma una muestra de hasta 20.000 filas de 202104, de
#   202106 y de 202108. Para cada columna terminada en _rank calcula el estadístico de Kolmogorov-Smirnov entre
#   202104 y 202106 (ks_referencia) y entre 202106 y 202108 (ks_futuro), ordena por ks_futuro descendente e
#   imprime las 25 primeras. La tabla no modifica el conjunto de variables.
#%% celda 22 [texto]
## 6. Diagnóstico de Data Drift

Se compara la distribución de cada variable rankeada entre **junio y agosto** con el estadístico de Kolmogorov-Smirnov (0 = iguales, 1 = totalmente distintas). Como referencia se incluye también **abril vs junio**, que muestra cuánto cambia una variable "normalmente" en dos meses.

La tabla es informativa: **no excluye nada por sí sola**. Si alguna variable muestra un salto muy grande en `ks_futuro` respecto de `ks_referencia`, agregar su nombre exacto (por ejemplo `"mcuentas_saldo_lag1_rank"`) a `PARAM$columnas_excluidas_modelo` y volver a correr desde la celda de parámetros. Los `NA` se ignoran en cada comparación.

#%% celda 23 [código]
set.seed(PARAM$semilla_primigenia)

muestra_mes <- function(mes, n= 20000L) {
  x <- dataset[foto_mes == mes]
  x[sample(.N, min(.N, n))]
}

d_abr <- muestra_mes(202104)
d_jun <- muestra_mes(202106)
d_ago <- muestra_mes(PARAM$future[1])

vars_num <- grep("_rank$", names(dataset), value= TRUE)

ks_stat <- function(a, b) {
  tryCatch(
    suppressWarnings(as.numeric(ks.test(a, b, exact= FALSE)$statistic)),
    error= function(e) NA_real_
  )
}

drift <- rbindlist(lapply(vars_num, function(v) {
  data.table(
    variable = v,
    ks_referencia = ks_stat(d_abr[[v]], d_jun[[v]]),   # abril vs junio
    ks_futuro     = ks_stat(d_jun[[v]], d_ago[[v]])    # junio vs agosto
  )
}))

setorder(drift, -ks_futuro)
print(head(drift, 25))

rm(d_abr, d_jun, d_ago)

# [Anotación · líneas 430–455] Arma dos listas de variables. campos_modelo: numero_de_cliente, foto_mes y
#   todas las columnas terminadas en _rank menos las de PARAM$columnas_excluidas_modelo. campos_bo: las mismas
#   sin las 10 columnas derivadas de cprestamos_personales y mprestamos_personales. Verifica ambas listas e
#   imprime sus tamaños.
#%% celda 24 [texto]
## 7. Preprocesamiento

Se arman los datasets de la Bayesian Optimization, **sin undersampling**:
* **Entrenamiento:** marzo + abril completos.
* **Validación:** junio completo.

Hay dos conjuntos de variables:
* `campos_bo`: las que usa la BO (`numero_de_cliente`, `foto_mes` y las rankeadas, **sin** los préstamos).
* `campos_modelo`: las que usan la curva de junio y el modelo final (`campos_bo` **más** los préstamos).

#%% celda 25 [código]
# variables del modelo (curva de junio y modelo final): numero_de_cliente, foto_mes (sin FE) y todas las rankeadas, prestamos incluidos
campos_modelo <- c(
  "numero_de_cliente", "foto_mes",
  setdiff(grep("_rank$", colnames(dataset), value= TRUE), PARAM$columnas_excluidas_modelo)
)

# variables de la BO: las mismas, sin los prestamos
cols_prestamos <- as.vector(outer(PARAM$variables_fuera_bo, sufijos, paste0))
campos_bo <- setdiff(campos_modelo, cols_prestamos)

stopifnot(all(c("numero_de_cliente", "foto_mes") %in% campos_bo))
stopifnot(!any(cols_prestamos %in% campos_bo))
cat("variables de la BO:", length(campos_bo), "\n")
cat("variables de la curva de junio y del modelo final:", length(campos_modelo), "\n")

# [Anotación · líneas 457–488] Separa las filas de 202103 y 202104 (entrenamiento) y las de 202106
#   (validación), sin submuestreo. Construye tres lgb.Dataset con clase01 como etiqueta: entrenamiento y
#   validación de la BO con campos_bo, y entrenamiento de la curva de junio con campos_modelo. Imprime filas y
#   cantidad de positivos de cada conjunto y la tabla de bajas de 202103 a 202106.
#%% celda 26 [código]
# training de la BO: marzo + abril, todos los clientes
dtr  <- dataset[foto_mes %in% PARAM$train_bo]

# validacion de la BO: junio completo
dval <- dataset[foto_mes %in% PARAM$validate_bo]

# datasets de la BO: sin los prestamos
dtrain_bo <- lgb.Dataset(
  data= data.matrix(dtr[, campos_bo, with= FALSE]),
  label= dtr$clase01,
  free_raw_data= FALSE
)

dvalidate_bo <- lgb.Dataset(
  data= data.matrix(dval[, campos_bo, with= FALSE]),
  label= dval$clase01,
  free_raw_data= FALSE
)

# dataset de entrenamiento de la curva de junio: con los prestamos
dtrain <- lgb.Dataset(
  data= data.matrix(dtr[, campos_modelo, with= FALSE]),
  label= dtr$clase01,
  free_raw_data= FALSE
)

cat("train BO:", nrow(dtr), "filas,", sum(dtr$clase01), "bajas\n")
cat("validacion BO:", nrow(dval), "filas,", sum(dval$clase01), "bajas\n")

cat("\nbajas (BAJA+1 y BAJA+2) por mes:\n")
print(tabla_bajas(c(202103, 202104, 202105, 202106)))

# [Anotación · líneas 490–534] Crea la carpeta del experimento dentro de ~/buckets/b1/experimentos y la fija
#   como directorio de trabajo; si existe un BO_log.txt anterior lo renombra con fecha y extensión .bak. Define
#   Estimar_lightgbm, la función que evalúa cada punto de la BO: combina los parámetros fijos con los
#   propuestos, entrena con el dataset de la BO usando 202106 como conjunto de validación, toma
#   modelo$best_score (AUC) como métrica, la escribe en el log y la devuelve.
#%% celda 27 [texto]
## 8. Optimización Bayesiana

Una sola semilla (`PARAM$semilla_primigenia`) y métrica **AUC** sobre junio.

#%% celda 28 [código]
# carpeta del experimento
carpeta_exp <- file.path(PARAM$carpeta_base, "experimentos", PARAM$experimento)
dir.create(carpeta_exp, recursive= TRUE, showWarnings= FALSE)
setwd(carpeta_exp)

archivo_log <- "BO_log.txt"

# si hay un log de una corrida anterior lo renombro (no se borra) para no mezclar corridas
if (PARAM$correr_BO && file.exists(archivo_log)) {
  file.rename(archivo_log, paste0(archivo_log, ".", format(Sys.time(), "%Y%m%d%H%M%S"), ".bak"))
}

giter <- 0

#%% celda 29 [código]
# En xs llegan los hiperparametros que propone la BO
Estimar_lightgbm <- function(xs) {

  flush.console()
  giter <<- giter + 1

  # xs pisa a param_fijos
  param_completo <- modifyList(PARAM$lgbm$param_fijos, xs)

  modelo <- lgb.train(
    data= dtrain_bo,
    valids= list("val" = dvalidate_bo),
    param= param_completo
  )

  xx <- param_completo
  xx$iter <- giter
  xx$metrica <- modelo$best_score

  loguear(xx, archivo_log)
  set.seed(PARAM$semilla_primigenia, kind= "L'Ecuyer-CMRG")  # reordeno la semilla para mlr3mbo

  return(list(metrica = xx$metrica))
}

# [Anotación · líneas 536–566] Configura la optimización con bbotk y mlr3mbo: objetivo a maximizar sobre el
#   espacio definido, terminador de 10 evaluaciones, surrogate de kriging (regr.km), función de adquisición
#   expected improvement y optimizador de la adquisición por búsqueda al azar con 1.000 evaluaciones, dentro del
#   ciclo bayesopt_ego.
#%% celda 30 [código]
objective <- ObjectiveRFun$new(
  fun= Estimar_lightgbm,
  domain= PARAM$hyperparametertuning$hs,
  codomain= ps(metrica = p_dbl(tags= "maximize")),
  id= "BO_lightgbm"
)

instance <- OptimInstanceBatchSingleCrit$new(
  objective= objective,
  terminator= trm("evals", n_evals= PARAM$hyperparametertuning$iteraciones)
)

surrogate <- srlrn(lrn("regr.km",
  optim.method= "BFGS",
  nugget.estim= TRUE,
  control= list(trace= FALSE)))

acq_function <- acqf("ei")   # expected improvement

acq_optimizer <- acqo(
  optimizer= opt("random_search", batch_size= 1000),
  terminator= trm("evals", n_evals= 1000)
)

optimizer <- opt("mbo",
  loop_function= bayesopt_ego,
  surrogate= surrogate,
  acq_function= acq_function,
  acq_optimizer= acq_optimizer
)

# [Anotación · líneas 568–588] Si correr_BO es TRUE ejecuta la optimización, lee BO_log.txt, lo ordena por
#   métrica descendente, imprime las 10 primeras filas y toma num_iterations, num_leaves y
#   min_sum_hessian_in_leaf de la primera. Si es FALSE usa PARAM$hiperparametros_manuales.
#%% celda 31 [texto]
### Corrida

Con `PARAM$correr_BO <- TRUE` esta celda es la más lenta del notebook. Si se pone en `FALSE`, se saltea y se usan `PARAM$hiperparametros_manuales`.

#%% celda 32 [código]
if (PARAM$correr_BO) {
  bayesiana_salida <- optimizer$optimize(instance)

  tb_bayesiana <- fread(archivo_log)
  setorder(tb_bayesiana, -metrica)
  print(head(tb_bayesiana[, list(iter, num_iterations, num_leaves, min_sum_hessian_in_leaf, metrica)], 10))

  mejores_hiperparametros <- as.list(
    tb_bayesiana[1, list(num_iterations, num_leaves, min_sum_hessian_in_leaf)]
  )
} else {
  mejores_hiperparametros <- PARAM$hiperparametros_manuales
}

mejores_hiperparametros

# [Anotación · líneas 590–622] Combina los parámetros fijos con los tres hiperparámetros elegidos. Para cada
#   una de las 20 semillas entrena un LightGBM con 202103 y 202104 y campos_modelo (num_threads 4), predice
#   202106 y guarda la matriz parcial de probabilidades en prob_semillas_parcial.rds. Promedia las 20 columnas
#   para obtener la probabilidad del ensamble. La celda de texto previa menciona una media móvil de 5 puntos y
#   envíos entre 8.000 y 15.000; el código de las líneas 625 a 627 usa 21 puntos y cortes de 3.500 a 20.500.
#%% celda 33 [texto]
## 9. Curva de ganancia de junio

Agosto no tiene clase, así que no se puede medir su ganancia. Lo que sí se puede es repetir el ejercicio en junio:
1. Se entrenan `PARAM$n_semillas` modelos (una semilla cada uno) con los mejores hiperparámetros, usando **marzo + abril** y las variables de `campos_modelo` (con los préstamos).
2. Se promedian las probabilidades de junio y se calcula la ganancia para cada cantidad de envíos entre 8.000 y 15.000.
3. Se suaviza la curva con una media móvil de 5 puntos (±500 envíos) para no quedarse con un pico producto del azar, y se toma el máximo.

Esta curva es solo para elegir el corte, no para la optimización.

#%% celda 34 [código]
# ================== CURVA DE JUNIO: ENTRENAMIENTO + GRAFICO ==================
param_final <- modifyList(PARAM$lgbm$param_fijos, mejores_hiperparametros)

X_val <- data.matrix(dval[, campos_modelo, with= FALSE])

semillas_curva <- PARAM$semillas 
prob_semillas  <- matrix(0, nrow= nrow(dval), ncol= length(semillas_curva))

# ---- entrenamiento ----
for (i in seq_along(semillas_curva)) {
  t0 <- Sys.time()
  param_semilla <- modifyList(param_final,
                              list(seed= semillas_curva[i],
                                   num_threads= 4))
  modelo_val <- lgb.train(data= dtrain, param= param_semilla)
  prob_semillas[, i] <- predict(modelo_val, X_val)
  cat("curva de junio: semilla", i, "de", length(semillas_curva),
      "- tardó", format(Sys.time() - t0), "\n")
  flush.console()
  saveRDS(prob_semillas, "prob_semillas_parcial.rds")
}
prob_val <- rowMeans(prob_semillas)   # ensamble

# [Anotación · líneas 624–650] Fija los cortes de 3.500 a 20.500 cada 50, una media móvil centrada de 21
#   puntos y una tolerancia de 0,01. Calcula la curva de ganancia suavizada del ensamble y el promedio de las
#   curvas suavizadas de cada semilla. Toma como k_junio el corte de mayor ganancia suavizada del ensamble y
#   delimita la meseta contigua de cortes con ganancia mayor o igual al 99% del máximo, con su centro.
# ---- parametros de la curva ----
paso        <- 50
cortes_plot <- seq(3500, 20500, by= paso)
ventana     <- 21                    # +-500 envios
tolerancia  <- 0.01                  # meseta: >= (1 - tolerancia) * maximo

suavizar <- function(g) frollmean(g, n= ventana, align= "center")

# ---- curvas ----
g_ens <- suavizar(curva_ganancia(prob_val, dval$clase_ternaria, cortes_plot)$ganancia)

g_sueltos <- rowMeans(sapply(seq_len(ncol(prob_semillas)), function(i) {
  suavizar(curva_ganancia(prob_semillas[, i], dval$clase_ternaria, cortes_plot)$ganancia)
}))

# ---- maximo suavizado y meseta contigua ----
k_junio <- cortes_plot[which.max(g_ens)]

umbral <- (1 - tolerancia) * max(g_ens, na.rm= TRUE)
i_max  <- which.max(g_ens)
ini <- i_max
while (ini > 1 && !is.na(g_ens[ini - 1]) && g_ens[ini - 1] >= umbral) ini <- ini - 1
fin <- i_max
while (fin < length(g_ens) && !is.na(g_ens[fin + 1]) && g_ens[fin + 1] >= umbral) fin <- fin + 1
meseta_ini    <- cortes_plot[ini]
meseta_fin    <- cortes_plot[fin]
centro_meseta <- round((meseta_ini + meseta_fin) / 2)

# [Anotación · líneas 652–669] Grafica en millones la ganancia suavizada del ensamble y el promedio de las
#   semillas sueltas, con líneas verticales en los bordes de la meseta, en su centro y en el máximo suavizado.
#   Imprime los límites de la meseta, el centro y k_junio.
# ---- grafico ----
ylim <- range(c(g_ens, g_sueltos), na.rm= TRUE) / 1e6

plot(cortes_plot, g_ens / 1e6, type= "l", lwd= 3, xlim= c(4000, 20000), ylim= ylim,
     xlab= "envíos en junio", ylab= "ganancia suavizada (M)",
     main= "Curva de ganancia del ensamble en junio")
lines(cortes_plot, g_sueltos / 1e6, lty= 2, lwd= 1.5)
abline(v= c(meseta_ini, meseta_fin), col= "gray60", lty= 3)
abline(v= centro_meseta, col= "red", lty= 2, lwd= 2)
abline(v= k_junio, col= "blue", lty= 1, lwd= 1.5)

legend("bottomright", bty= "n",
       legend= c("ensamble", "promedio de sueltos", "centro de la meseta", "máximo suavizado"),
       lty= c(1, 2, 2, 1), lwd= c(3, 1.5, 2, 1.5), col= c("black", "black", "red", "blue"))

cat("meseta entre", meseta_ini, "y", meseta_fin, "envíos\n")
cat("centro de la meseta:", centro_meseta, "envíos\n")
cat("corte de junio (máximo suavizado):", k_junio, "envíos\n")

# [Anotación · líneas 671–711] Arma el dataset de entrenamiento final con 202103 a 202106 y campos_modelo, y
#   la matriz de 202108. Para cada una de las 20 semillas entrena un LightGBM con los mismos hiperparámetros,
#   predice 202108 y escribe las probabilidades de esa semilla en probs_semillas/prob_semilla_[semilla].csv.
#%% celda 35 [texto]
## 10. Modelo final y predicción de agosto

Se entrena con **marzo + abril + mayo + junio**, sin undersampling y con los mismos hiperparámetros, un modelo por semilla (`PARAM$n_semillas`). Cada uno predice agosto y la **probabilidad final es el promedio** de las probabilidades de todos los modelos.

#%% celda 36 [código]
dfinal <- dataset[foto_mes %in% PARAM$train_final]
cat("train final:", nrow(dfinal), "filas,", sum(dfinal$clase01), "bajas\n")

dtrain_final <- lgb.Dataset(
  data= data.matrix(dfinal[, campos_modelo, with= FALSE]),
  label= dfinal$clase01,
  free_raw_data= FALSE
)

dfuture <- dataset[foto_mes %in% PARAM$future]
X_fut <- data.matrix(dfuture[, campos_modelo, with= FALSE])

# Carpeta para las probabilidades de cada semilla
dir_probs <- file.path(PARAM$carpeta_base, "experimentos", PARAM$experimento, "probs_semillas")
dir.create(dir_probs, showWarnings= FALSE, recursive= TRUE)

prob_semillas <- matrix(
  NA_real_, nrow= nrow(dfuture), ncol= length(PARAM$semillas),
  dimnames= list(NULL, paste0("semilla_", PARAM$semillas))
)

for (i in seq_along(PARAM$semillas)) {
  param_semilla <- modifyList(param_final, list(seed= PARAM$semillas[i]))
  modelo_final <- lgb.train(data= dtrain_final, param= param_semilla)
  prob_semillas[, i] <- predict(modelo_final, X_fut)

  # Guardo las probabilidades de esta semilla
  fwrite(
    data.table(numero_de_cliente= dfuture$numero_de_cliente,
               prob= prob_semillas[, i]),
    file.path(dir_probs, paste0("prob_semilla_", PARAM$semillas[i], ".csv"))
  )

  cat("modelo final: semilla", i, "de", length(PARAM$semillas), "\n")
}

# [Anotación · líneas 713–746] Lee todos los archivos prob_semilla_*.csv de la carpeta probs_semillas,
#   verifica que tengan la misma cantidad de clientes, los une por numero_de_cliente y calcula el promedio de
#   las columnas de probabilidad. Ordena por probabilidad descendente y escribe ranking_prob_promedio.csv con
#   numero_de_cliente y prob.
#%% celda 37 [código]
dir_base  <- file.path(PARAM$carpeta_base, "experimentos", PARAM$experimento)
dir_probs <- file.path(dir_base, "probs_semillas")

# Leo TODOS los archivos de probabilidades por semilla
archivos <- list.files(dir_probs, pattern = "^prob_semilla_.*\\.csv$", full.names = TRUE)
cat("Archivos encontrados:", length(archivos), "\n")
stopifnot(length(archivos) > 0)

lista <- lapply(archivos, function(f) {
  x <- fread(f)
  setnames(x, "prob", paste0("prob_", tools::file_path_sans_ext(basename(f))))
  setkey(x, numero_de_cliente)
  x
})

# Chequeo que todos tengan los mismos clientes
n_clientes <- sapply(lista, nrow)
stopifnot(length(unique(n_clientes)) == 1)

# Uno por numero_de_cliente y promedio simple
tb_futuro <- Reduce(function(a, b) merge(a, b, by = "numero_de_cliente"), lista)
stopifnot(nrow(tb_futuro) == n_clientes[1])

cols_prob <- grep("^prob_prob_semilla_", names(tb_futuro), value = TRUE)
tb_futuro[, prob := rowMeans(.SD), .SDcols = cols_prob]
cat("Semillas promediadas:", length(cols_prob), "\n")

# Ordeno por probabilidad descendente y guardo el ranking
setorder(tb_futuro, -prob)
fwrite(tb_futuro[, .(numero_de_cliente, prob)],
       file.path(dir_base, "ranking_prob_promedio.csv"))

cat("Ranking guardado:", nrow(tb_futuro), "clientes\n")

# [Anotación · líneas 748–785] La celda de texto describe un CSV por defecto con el corte de junio escalado al
#   tamaño de agosto y un CSV por cada valor de PARAM$cortes_envios, con ids escritos con sprintf; ese cálculo
#   no se observa en las celdas de código siguientes. La celda de código repite la lectura de los archivos por
#   semilla (columnas p_[semilla]), verifica que todos tengan los mismos clientes en el mismo orden, promedia,
#   ordena y vuelve a escribir ranking_prob_promedio.csv.
#%% celda 38 [texto]
## 11. Archivos de envío

* **CSV por defecto** (`<experimento>.csv`): el corte de junio (curva suavizada) se escala al tamaño de agosto y se limita a [8.000, 15.000] (o se usa `PARAM$envios_manual` si se definió).
* **Un CSV por cada corte** de `PARAM$cortes_envios` (`<experimento>_k<corte>.csv`) para poder probar distintos puntos de corte.

Todos son **solo la columna de ids, sin encabezado**, ordenados por la probabilidad promedio. Los ids se pasan a **entero** y se escriben con `sprintf("%d")`, que no usa notación científica.

#%% celda 39 [código]
dir_base  <- file.path(PARAM$carpeta_base, "experimentos", PARAM$experimento)
dir_probs <- file.path(dir_base, "probs_semillas")

archivos <- list.files(dir_probs, pattern = "prob_semilla_\\d+\\.csv$", full.names = TRUE)
cat("Archivos encontrados:", length(archivos), "\n")
stopifnot(length(archivos) > 0)

lista <- lapply(archivos, function(f) {
  semilla <- sub(".*prob_semilla_(\\d+)\\.csv$", "\\1", basename(f))
  x <- fread(f)
  setnames(x, "prob", paste0("p_", semilla))
  setkey(x, numero_de_cliente)
  x
})

# Mismos clientes en todos los archivos
ids_ref <- lista[[1]]$numero_de_cliente
stopifnot(all(sapply(lista, function(x) identical(x$numero_de_cliente, ids_ref))))

tb_futuro <- Reduce(function(a, b) merge(a, b, by = "numero_de_cliente"), lista)

cols_prob <- grep("^p_\\d+$", names(tb_futuro), value = TRUE)
tb_futuro[, prob := rowMeans(.SD), .SDcols = cols_prob]
cat("Semillas promediadas:", length(cols_prob), "\n")

setorder(tb_futuro, -prob)
fwrite(tb_futuro[, .(numero_de_cliente, prob)],
       file.path(dir_base, "ranking_prob_promedio.csv"))
cat("Ranking guardado:", nrow(tb_futuro), "clientes\n")

# [Anotación · líneas 787–806] Crea la carpeta entregas, lee ranking_prob_promedio.csv y, para cada corte de
#   la lista 10.000, 11.000, 11.500, 12.000, 12.040, 12.700 y 12.350, escribe entrega_[k]_envios.csv con los
#   primeros k numero_de_cliente, sin encabezado. Imprime el nombre del archivo, la cantidad de ids y la
#   probabilidad del último cliente incluido.
#%% celda 40 [código]
library(data.table)

dir_base <- file.path(PARAM$carpeta_base, "experimentos", PARAM$experimento)

dir_entregas <- file.path(dir_base, "entregas")
dir.create(dir_entregas, showWarnings = FALSE)

cortes <- c(10000, 11000, 11500, 12000, 12040, 12700, 12350)

tb_futuro <- fread(file.path(dir_base, "ranking_prob_promedio.csv"))
setorder(tb_futuro, -prob)
stopifnot(max(cortes) <= nrow(tb_futuro))

for (k in cortes) {
  archivo <- file.path(dir_entregas, paste0("entrega_", k, "_envios.csv"))
  fwrite(tb_futuro[1:k, .(numero_de_cliente)], archivo, col.names = FALSE)
  cat("Guardado:", basename(archivo), "| ids enviados:", k,
      "| prob del último enviado:", round(tb_futuro$prob[k], 5), "\n")
}
```


## Explicaciones del alumno (texto original)

### README.md

> # Primera entrega – Feature engineering con ranking + LightGBM (BO + ensamble de semillas)
>
>
> Predicción de bajas de clientes para el mes **202108** a partir de un LightGBM entrenado sobre variables rankeadas, con optimización bayesiana de hiperparámetros y un ensamble de 20 modelos finales (5 semillas con 501367, 10 con 898543 y 5 con 500153). Corte de 11000 enviado para la entrega.
>
> ---
>
> ## 1. Resumen del enfoque
>
> | Etapa | Qué se hace |
> |---|---|
> | Datos | `competencia_01_crudo.csv` (983.061 filas × 154 columnas). Se genera `clase_ternaria`. |
> | Feature engineering | Corrección de `ccajas_depositos`, lags y deltas 1 y 2, ranking con cero fijo por mes. |
> | Data drift | KS entre variables rankeadas (abril vs junio como referencia, junio vs agosto). Informativo. |
> | Optimización bayesiana | Train: marzo + abril. Validación: junio. Métrica: AUC, 1 semilla, 10 evaluaciones. |
> | Curva de ganancia | Junio con 20 semillas promediadas, suavizada, para elegir el corte de envíos. |
> | Modelo final | Train: marzo + abril + mayo + junio. 20 modelos (3 corridas: 5 + 10 + 5 semillas), probabilidad = promedio. |
> | Envío | CSV con los `numero_de_cliente` a contactar, ordenados por probabilidad. |
>
> ## 2. Flujo del notebook
>
> 1. **Inicio y librerías:** `data.table`, `bbotk`, `mlr3`, `mlr3mbo`, `mlr3learners`, `paradox`, `DiceKriging`, `lightgbm`.
> 2. **Parámetros:** todo lo configurable está en un único objeto `PARAM`.
> 3. **Funciones auxiliares:** log de la BO, curva de ganancia y tabla de bajas por mes.
> 4. **Carga y chequeos:** existencia de los meses, clase presente en los meses de entrenamiento y un registro por cliente en agosto.
> 5. **Feature engineering** (ver sección 3).
> 6. **Diagnóstico de data drift.**
> 7. **Preprocesamiento:** armado de los `lgb.Dataset` sin undersampling.
> 8. **Optimización bayesiana.**
> 9. **Curva de ganancia de junio.**
> 10. **Modelo final y predicción de agosto.**
> 11. **Archivos de envío.**
>
> ## 3. Feature engineering
>
> Se aplica **antes de cualquier entrenamiento**, en este orden:
>
> 1. **`ccajas_depositos` roto en 202105:** todos sus valores son 0 ese mes, por lo que se pasa a `NA` solo en 202105. Se hace primero para que los lags y deltas que dependen de ese valor también queden en `NA`.
> 2. **Lags y deltas 1 y 2** (marzo a agosto) para las 152 variables, excepto `foto_mes`, `numero_de_cliente`, `clase_ternaria` y `clase01`.
>    * Los lags se calculan por **mes calendario**: si no hay registro de ese mes queda `NA` (marzo no tiene lags y abril no tiene lag 2).
>    * `delta1 = valor_t − valor_t-1` y `delta2 = valor_t − valor_t-2`.
> 3. **Ranking con cero fijo dentro de cada `foto_mes`**, sobre las variables originales, los lags y los deltas: los negativos quedan en [-1, 0), los positivos en (0, 1] y el 0 se mantiene en 0. Los `NA` no se imputan.
> 4. Se eliminan las variables sin rankear, **salvo** `numero_de_cliente`, `foto_mes` y las clases.
> 5. Se guarda el dataset completo con FE en `competencia_01_crudo_FE_rank.csv` (983.061 filas × 764 columnas) para no repetir el proceso.
>
> Resultado: **760 variables nuevas** con sufijos `_rank`, `_lag1_rank`, `_lag2_rank`, `_delta1_rank` y `_delta2_rank`.
>
> ## 4. Modelo
>
> * **Variables de la BO (752):** `numero_de_cliente`, `foto_mes` y las rankeadas, **sin** `cprestamos_personales` ni `mprestamos_personales`.
> * **Variables de la curva de junio y del modelo final (762):** las anteriores **más** los préstamos.
> * **Sin undersampling** en ningún paso.
> * **Parámetros fijos de LightGBM** (principales): `boosting= gbdt`, `objective= binary`, `learning_rate= 0.005`, `feature_fraction= 0.50`, `feature_fraction_bynode= 0.20`, `min_data_in_leaf= 0`, `max_bin= 31`.
> * **Espacio de búsqueda de la BO:**
>
> | Hiperparámetro | Rango |
> |---|---|
> | `num_iterations` | 64 – 4096 |
> | `num_leaves` | 16 – 2048 |
> | `min_sum_hessian_in_leaf` | 1e-06 – 0.1 |
>
> * **Datos de entrenamiento / validación de la BO:** 326.184 filas (4.082 bajas) para entrenar y 164.114 filas (1.972 bajas) para validar.
> * **Mejores hiperparámetros encontrados:**
>
> | Hiperparámetro | Valor |
> |---|---|
> | `num_iterations` | 4028 |
> | `num_leaves` | 1226 |
> | `min_sum_hessian_in_leaf` | 0.00477222 |
>
>
> ## 5. Elección del corte de envíos
>
> Agosto no tiene clase, por lo que el corte se estima con junio:
>
> 1. Se entrenan 20 modelos (uno por semilla) con marzo + abril y se promedian las probabilidades de junio.
> 2. Se calcula la ganancia acumulada para cada cantidad de envíos (cortes de 3.500 a 20.500 cada 50).
> 3. Se suaviza con una media móvil de 21 puntos (±500 envíos) y se toma el máximo.
> 4. Se identifica la **meseta** (valores ≥ 99% del máximo) y su centro.
>
> La cantidad de envíos permitida es de 8.000 a 15.000.
>
> ## 6. Modelo final y archivos generados
>
> El modelo final se entrena con **202103 + 202104 + 202105 + 202106** (654.066 filas, 8.067 bajas) con los mismos hiperparámetros, una semilla por modelo. Se hicieron **3 corridas finales**, cada una con una semilla primigenia distinta: **501367** (5 semillas), **898543** (10 semillas) y **500153** (5 semillas), es decir 20 modelos en total. La probabilidad de agosto (164.647 clientes) es el promedio de las semillas.
>
> Archivos de salida en `~/buckets/b1/experimentos/primer_entrega_piloto_FE_rank_20semillas/`:
>
> Cortes generados: 10.000, 11.000, 11.500, 12.000, 12.040, 12.350, 12.500, 12.700 y 13.000 envíos.
>
> ## 7. Reproducibilidad
>
> * Semillas primigenias de las corridas finales: `501367` (5 semillas del modelo final), `898543` (10 semillas) y `500153` (5 semillas). La BO y la curva de junio se hicieron con `PARAM$semilla_primigenia = 501367`.
>
> ## 8. Cómo correrlo
>
> 1. Instalar los paquetes (hay una línea comentada en la celda de librerías):
>    ```r
>    install.packages(c("data.table", "bbotk", "mlr3", "mlr3mbo", "mlr3learners", "DiceKriging", "lightgbm"))
>    ```
> 2. Ubicar el dataset en `~/buckets/b1/datasets/competencia_01_crudo.csv` (o ajustar `PARAM$carpeta_base` y `PARAM$archivo_dataset`).
> 3. Ejecutar las celdas en orden. La BO y los 20 entrenamientos (curva de junio y modelo final) son las partes más lentas.
> 4. Opciones útiles en `PARAM`:
>    * `PARAM$correr_BO <- FALSE` para saltear la BO y usar `PARAM$hiperparametros_manuales`.
>    * `PARAM$columnas_excluidas_modelo` para sacar columnas ya rankeadas (por ejemplo, según el diagnóstico de drift).
>    * `PARAM$envios_manual` y `PARAM$cortes_envios` para fijar o probar cortes distintos.
> 5. Para no repetir el feature engineering, se puede cargar `competencia_01_crudo_FE_rank.csv` con `fread(..., stringsAsFactors= TRUE)`.

