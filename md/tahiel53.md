# Tahiel Maccario — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: tahiel53
- Repositorio: https://github.com/tahiel53/DMEyF-competencia_1
- Link posteado: https://github.com/tahiel53/DMEyF-competencia_1.git
- Commit: f7cd493146767a88a594f82e23e4de0cb44e53d2
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/tahiel53/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/tahiel53.json

## Resumen

La entrega contiene un README, cuatro notebooks de R numerados (0, 1, 2 y 3b) y la carpeta exp/ con resultados intermedios: el registro de la optimización, los dos sets de hiperparámetros, las predicciones por cliente de 50 modelos y un resumen de la entrega. El notebook 0 calcula la clase ternaria, pone en NA ccajas_depositos en 202105, elimina cprestamos_personales y mprestamos_personales, agrega lags y deltas de orden 1 y 2 y reemplaza cada variable por su ranking con cero fijo dentro de cada mes. El notebook 1 evalúa con mlr3mbo 10 combinaciones de num_iterations, num_leaves y min_sum_hessian_in_leaf, entrenando LightGBM en 202103 y 202104 y midiendo AUC en 202106, y guarda las 2 de mayor AUC. El notebook 2 se corre una vez por set: entrena 5 semillas en 202103 y 202104 para predecir 202106 (backtest) y 20 semillas en 202103 a 202106 para predecir 202108, con clase binaria (positivo = BAJA+1 o BAJA+2) y sin submuestreo. El notebook 3b promedia las probabilidades de los 40 modelos finales, calcula la curva de ganancia del backtest y escribe los 11.750 clientes de mayor probabilidad.

**Qué entrega.** Un archivo exp/entregas/v3_sets12_40mod_c11750_<mmddHHMM>.csv con los 11.750 numero_de_cliente de mayor probabilidad promedio de 202108, uno por línea y sin encabezado. El CSV no está en el repositorio (el .gitignore excluye exp/entregas/*.csv); sí están las predicciones de los 40 modelos finales y el resumen de la entrega, que nombra el archivo v3_sets12_40mod_c11750_10102129.csv.

**Cómo se ejecuta.** Según el README: cada notebook se abre en JupyterLab con kernel de R desde la carpeta del repositorio y se corre con Run All Cells, con el dataset en ../competencia_01_crudo.csv. Da tres opciones. A: notebook 0 y después 3b, usando las predicciones guardadas en exp/modelos/. B (unas 17 horas): borrar exp/modelos/, correr el 0, el 2 con PARAM$set_hiperparametros <- 1, el 2 otra vez con el valor 2 y el 3b. C (unas 18 horas): borrar además exp/BO/ y exp/mejores_hiperparametros.txt, correr el 0, el 1 y seguir como en B desde el notebook 2.

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Calcula clase_ternaria (CONTINUA, BAJA+1, BAJA+2) según la presencia del cliente en los dos meses siguientes. Entrena con clase binaria: positivo = BAJA+1 o BAJA+2, negativo = CONTINUA.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica: los modelos se entrenan con todos los registros de los meses de entrenamiento (654.066 filas en los modelos finales según la salida guardada del notebook 2).
- **Calidad de datos:** ccajas_depositos pasa a NA en las filas de 202105; el comentario del código indica que en ese mes todos sus valores son cero.
- **Drifting:** Elimina cprestamos_personales y mprestamos_personales. Reemplaza cada variable (originales, lags y deltas; 750 columnas según la salida guardada) por su ranking con cero fijo calculado dentro de cada mes: positivos en (0, 1], negativos en [-1, 0), el cero en 0 y los NA en NA. numero_de_cliente, foto_mes y clase_ternaria no se transforman.
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** Lag 1 y lag 2 de todas las variables originales (valor de la fila anterior y de dos filas atrás del mismo cliente, con el dataset ordenado por cliente y mes) y delta 1 y delta 2 (valor actual menos lag 1 y menos lag 2). Los lags se calculan antes de descartar 202107.
- **Selección de variables:** No se observa en el código. El modelo usa todas las columnas del dataset preprocesado menos foto_mes y clase_ternaria (751 variables según la salida guardada, con numero_de_cliente incluido).
- **Optimización de hiperparámetros:** mlr3mbo con bbotk (bayesopt_ego, modelo sustituto regr.km, adquisición expected improvement) sobre num_iterations [64, 4096], num_leaves [16, 2048] y min_sum_hessian_in_leaf [1e-06, 0.1]. Hace 10 evaluaciones con un diseño inicial de tamaño 10, por lo que según el propio notebook las 10 son al azar. Cada evaluación entrena en 202103 y 202104 con seed 370003 y mide AUC en 202106; la ganancia en cortes de 9.000 a 14.000 se registra como dato informativo. Se guardan los 2 sets de mayor AUC. El README y una tabla del notebook indican 1.0 como límite superior de min_sum_hessian_in_leaf; el código usa 0.1.
- **Hiperparámetros finales:** Fijos: boosting gbdt, objective binary, max_bin 31, min_data_in_leaf 0, feature_fraction 0.50, feature_fraction_bynode 0.20, learning_rate 0.005, bagging_fraction 1.0, lambda_l1 0, lambda_l2 0, max_depth -1, min_gain_to_split 0, use_missing TRUE, deterministic TRUE, force_row_wise TRUE. Set 1: num_iterations 3172, num_leaves 943, min_sum_hessian_in_leaf 0.02584. Set 2: num_iterations 2033, num_leaves 1874, min_sum_hessian_in_leaf 0.08125 (valores de exp/mejores_hiperparametros.txt).
- **Semillas:** Semilla primigenia 370003. Las 20 semillas salen de set.seed(370003) y sample(100000:999999, 20) y se usan como seed de LightGBM, una por modelo, con cada uno de los 2 sets. El backtest usa las primeras 5. La optimización usa seed 370003 en todas sus evaluaciones.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio sin ponderar (rowMeans) de las probabilidades de los 40 modelos finales: 20 semillas con el set 1 y 20 con el set 2.
- **Corte:** Cantidad fija escrita en el código: CORTES <- c(11750); se toman los 11.750 clientes de mayor prob_ensemble. Según el README, el valor se eligió con la curva de ganancia del backtest en 202106 y con la ganancia pública de varios cortes. El resumen guardado informa, para el backtest de todos los modelos juntos, 456,8 millones con 11.750 envíos y un máximo de 461,7 millones con 10.530 envíos.
- **Validación:** En un mes posterior al entrenamiento: la optimización entrena en 202103 y 202104 y mide AUC en 202106; el backtest entrena 5 semillas por set en esos mismos meses, predice 202106 y calcula la curva de ganancia acumulada (1.072.500 por cada BAJA+2 y -27.500 por cada uno de los demás) para cada set y para los 10 modelos juntos.
- **Salidas:** datos/dataset_preprocesado.fst; exp/BO/BO_log.txt y exp/mejores_hiperparametros.txt; exp/modelos/{final,backtest}_set{1,2}_s<semilla>.txt con numero_de_cliente y prob; exp/probabilidades_*.csv; exp/ganancia_vs_envios_sets12.png; exp/entregas/v3_sets12_40mod_c11750_<marca>.csv con un numero_de_cliente por línea y exp/entregas/resumen_<marca>.txt.

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
- Búsqueda en grilla o al azar (`hiperparametros.grilla_o_azar`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Técnicas sólo exploradas

- Genera archivos con varios cortes (`corte.varios_cortes`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: no
- Entorno declarado: Según el README: JupyterLab con kernel de R (IRkernel), corrido en una VM de Google Cloud con 12 vCPU; paquetes data.table, R.utils, fst, lightgbm, bbotk, mlr3, mlr3mbo, mlr3learners, DiceKriging y ggplot2, listados sin versión, que cada notebook instala si faltan. Los metadatos de los notebooks registran R 4.6.1.

## Pasos del camino de la entrega

1. **Lectura del dataset y clase ternaria.** Lee ../competencia_01_crudo.csv y calcula clase_ternaria mirando los registros de cada cliente en los dos meses siguientes: BAJA+1 si no está en el mes siguiente, BAJA+2 si está en el siguiente y no en el subsiguiente, CONTINUA en el resto de los meses con información suficiente. (`0_preprocesamiento.ipynb` líneas 65–99)
2. **Calidad de datos y variables eliminadas.** Pone NA en ccajas_depositos para 202105 y elimina cprestamos_personales y mprestamos_personales. (`0_preprocesamiento.ipynb` líneas 105–109)
3. **Lags y deltas de orden 1 y 2.** Crea _lag1 y _lag2 de todas las variables originales por cliente, filtra los meses 202103, 202104, 202105, 202106 y 202108 y crea _delta1 y _delta2 como diferencia entre el valor actual y cada lag. (`0_preprocesamiento.ipynb` líneas 116–137)
4. **Ranking con cero fijo por variable y por mes.** Reemplaza cada una de las 750 columnas por su ranking dentro del mes: positivos en (0, 1], negativos en [-1, 0), el cero en 0 y los NA en NA. (`0_preprocesamiento.ipynb` líneas 153–184)
5. **Control y guardado del dataset preprocesado.** Verifica que todas las columnas transformadas queden entre -1 y 1 y escribe datos/dataset_preprocesado.fst ordenado por mes y cliente. (`0_preprocesamiento.ipynb` líneas 193–217)
6. **Hiperparámetros fijos y espacio de búsqueda.** Define los hiperparámetros fijos de LightGBM (max_bin 31, min_data_in_leaf 0, feature_fraction 0.50, feature_fraction_bynode 0.20, learning_rate 0.005, sin bagging) y el espacio de búsqueda de num_iterations, num_leaves y min_sum_hessian_in_leaf. (`1_optimizacion_bayesiana.ipynb` líneas 67–99; `1_optimizacion_bayesiana.ipynb` líneas 112–116)
7. **Datos de la optimización.** Arma la clase binaria (BAJA+1 o BAJA+2 = 1), el conjunto de entrenamiento con todas las filas de 202103 y 202104 y el de prueba con 202106, con la ganancia por fila (1.072.500 para BAJA+2, -27.500 para el resto). (`1_optimizacion_bayesiana.ipynb` líneas 167–192)
8. **Optimización de hiperparámetros.** Evalúa 10 combinaciones con mlr3mbo; cada una entrena un LightGBM con seed 370003, mide AUC y ganancia en 202106 y se registra en exp/BO/BO_log.txt. Las 2 de mayor AUC quedan en exp/mejores_hiperparametros.txt como set 1 y set 2. (`1_optimizacion_bayesiana.ipynb` líneas 201–254; `1_optimizacion_bayesiana.ipynb` líneas 257–306; `1_optimizacion_bayesiana.ipynb` líneas 315–321; `1_optimizacion_bayesiana.ipynb` líneas 330–337)
9. **Semillas y set de hiperparámetros.** Genera 20 semillas a partir de 370003 y lee de exp/mejores_hiperparametros.txt el set indicado en PARAM$set_hiperparametros. El notebook se corre una vez con el set 1 y otra con el set 2. (`2_modelos_semillas.ipynb` líneas 47–69; `2_modelos_semillas.ipynb` líneas 114–132)
10. **Backtest en 202106.** Con las primeras 5 semillas entrena en 202103 y 202104, predice 202106 y guarda la probabilidad por cliente de cada modelo en exp/modelos/backtest_set<s>_s<semilla>.txt. (`2_modelos_semillas.ipynb` líneas 181–235; `2_modelos_semillas.ipynb` líneas 264–276)
11. **Modelos finales para 202108.** Con cada una de las 20 semillas entrena en 202103, 202104, 202105 y 202106 con todos los registros, predice 202108 y guarda la probabilidad por cliente en exp/modelos/final_set<s>_s<semilla>.txt. (`2_modelos_semillas.ipynb` líneas 284–295)
12. **Ensemble de los 40 modelos.** Lee las predicciones de los modelos de los sets 1 y 2 y calcula prob_ensemble como el promedio de las 40 columnas de modelos finales; hace lo mismo con los 10 modelos del backtest y les agrega la clase de 202106. (`3b_corte_y_entrega_sets_combinados.ipynb` líneas 106–132; `3b_corte_y_entrega_sets_combinados.ipynb` líneas 138–160)
13. **Curva de ganancia del backtest.** Calcula la ganancia acumulada en 202106 según la cantidad de envíos para el ensemble de cada set y para todos juntos, ubica el máximo de cada curva, la grafica y la tabula en cortes de 8.000 a 15.000. (`3b_corte_y_entrega_sets_combinados.ipynb` líneas 168–205)
14. **Corte y archivo de entrega.** Con el corte escrito en CORTES (11750), ordena los clientes de 202108 por prob_ensemble descendente y escribe los primeros 11.750 numero_de_cliente en un CSV dentro de exp/entregas/. (`3b_corte_y_entrega_sets_combinados.ipynb` líneas 213–226; `3b_corte_y_entrega_sets_combinados.ipynb` líneas 234–250)
15. **Resumen de la entrega.** Escribe exp/entregas/resumen_<marca>.txt con los modelos del ensemble, sus hiperparámetros y semillas, la ganancia del backtest en el corte elegido y el nombre del envío. (`3b_corte_y_entrega_sets_combinados.ipynb` líneas 252–288; `exp/entregas/resumen_10102129.txt` líneas 1–18)

## Archivos

- `0_preprocesamiento.ipynb` · principal · Jupyter (R) · 220 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tahiel53/0_preprocesamiento.ipynb.txt) — Notebook de R que lee el dataset crudo, calcula la clase ternaria, corrige ccajas_depositos, elimina dos variables, agrega lags y deltas de orden 1 y 2, aplica el ranking con cero fijo por mes y guarda datos/dataset_preprocesado.fst.
- `1_optimizacion_bayesiana.ipynb` · principal · Jupyter (R) · 340 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tahiel53/1_optimizacion_bayesiana.ipynb.txt) — Notebook de R que busca num_iterations, num_leaves y min_sum_hessian_in_leaf con mlr3mbo: 10 evaluaciones de LightGBM entrenado en 202103 y 202104 y medido por AUC en 202106. Escribe exp/BO/BO_log.txt y los 2 sets de mayor AUC en exp/mejores_hiperparametros.txt.
- `README.md` · explicacion · Markdown · 115 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tahiel53/README.md.txt) — Presenta la entrega: una tabla con cada etapa del modelo, los 2 sets de hiperparámetros con su AUC en 202106, las 20 semillas, el contenido del repositorio, los requisitos y tres formas de reproducir la entrega (opciones A, B y C) con sus tiempos.
- `3b_corte_y_entrega_sets_combinados.ipynb` · principal · Jupyter (R) · 288 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tahiel53/3b_corte_y_entrega_sets_combinados.ipynb.txt) — Notebook de R que lee las predicciones guardadas en exp/modelos/, promedia los 40 modelos finales de los sets 1 y 2, calcula la curva de ganancia del backtest en 202106, aplica el corte de 11.750 envíos y escribe el archivo de entrega y su resumen en exp/entregas/. No entrena modelos.
- `2_modelos_semillas.ipynb` · principal · Jupyter (R) · 317 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tahiel53/2_modelos_semillas.ipynb.txt) — Notebook de R que, para un set de hiperparámetros, entrena 5 modelos de backtest (202103 y 202104, predice 202106) y 20 modelos finales (202103 a 202106, predice 202108), uno por semilla, y guarda la probabilidad por cliente de cada modelo en exp/modelos/. Según el README se corre dos veces, con el set 1 y con el set 2.
- `exp/entregas/resumen_10102129.txt` · explicacion · Texto · 18 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tahiel53/exp/entregas/resumen_10102129.txt.txt) — Resumen que escribe el notebook 3b (líneas 254 a 288), fechado 2026-10-10 21:29: ensemble de 40 LightGBM, hiperparámetros y semillas de los sets 1 y 2, ganancia del backtest en 202106 con 10 modelos (456,8 millones con 11.750 envíos; máximo de 461,7 millones con 10.530 envíos para todos juntos) y el nombre del envío v3sets12c11750t10102129.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### 0_preprocesamiento.ipynb

Notebook de R que lee el dataset crudo, calcula la clase ternaria, corrige ccajas_depositos, elimina dos variables, agrega lags y deltas de orden 1 y 2, aplica el ranking con cero fijo por mes y guarda datos/dataset_preprocesado.fst.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Celda de texto de presentación: indica que el notebook se corre una sola vez, lee
#   ../competencia_01_crudo.csv y guarda datos/dataset_preprocesado.fst, y enumera sus seis pasos (clase
#   ternaria, calidad de datos, drifting, lags y deltas, ranking con cero fijo, filtrado de meses y guardado).
#   Señala que numero_de_cliente, foto_mes y clase_ternaria no se transforman.
#%% celda 1 [texto]
# 0 · Preprocesamiento del dataset

Se corre **una sola vez**. Lee `../competencia_01_crudo.csv`, lo transforma y guarda
`datos/dataset_preprocesado.fst`, que es lo que usan los notebooks 1, 2 y 3.

**Qué hace, en orden:**
1. **Clase ternaria** (BAJA+1, BAJA+2, CONTINUA).
2. **Data Quality:** `ccajas_depositos` en 202105 tiene todos ceros → `NA` en ese mes
3. **Data Drifting:** saca `cprestamos_personales` y `mprestamos_personales`
4. **Lags y delta lags de orden 1 y 2** de todas las variables
   (`_lag1`, `_lag2`, `_delta1` = actual − lag1, `_delta2` = actual − lag2)
5. **Ranking con cero fijo, por variable y por mes**, a todas las columnas (también lags y deltas):
   * los valores positivos pasan a (0, 1], equiespaciados según su ranking dentro del mes
   * los negativos pasan a [−1, 0), equiespaciados según su ranking dentro del mes
   * el cero queda en 0 y los NA quedan NA
   * **reemplaza** a las columnas originales (no quedan los valores originales)
6. Se queda con los meses que se usan después (202103, 202104, 202105, 202106 y 202108) y guarda

No se transforman `numero_de_cliente`, `foto_mes` ni `clase_ternaria`.

# [Anotación · líneas 22–43] Imprime la fecha y hora, limpia la memoria, fija el repositorio de CRAN y carga
#   data.table, R.utils, fst y lightgbm; cada paquete se instala si no está disponible. Imprime la cantidad de
#   núcleos de la máquina.
#%% celda 2 [texto]
### Librerías

#%% celda 3 [código]
format(Sys.time(), "%a %b %d %X %Y")

# limpio la memoria
rm(list=ls(all.names=TRUE))
gc(full=TRUE, verbose=FALSE)

# cargo las librerias (la primera vez se instalan y tarda varios minutos)
options(repos= c(CRAN= "https://cloud.r-project.org"))
options(width= 200)

for (paquete in c("data.table", "R.utils", "fst", "lightgbm")) {
  if (!require(paquete, character.only= TRUE)) {
    install.packages(paquete)
    library(paquete, character.only= TRUE)
  }
}

cat("Nucleos disponibles:", parallel::detectCores(), "\n")

# [Anotación · líneas 45–59] Define la lista PARAM: los meses que se guardan (202103, 202104, 202105, 202106 y
#   202108), el archivo de entrada ../competencia_01_crudo.csv y el de salida datos/dataset_preprocesado.fst.
#   Detiene la ejecución si el archivo de entrada no existe.
#%% celda 4 [texto]
### Parámetros

#%% celda 5 [código]
PARAM <- list()

# meses que se guardan (los que usan la BO, los modelos y el scoring)
PARAM$meses_a_guardar <- c(202103, 202104, 202105, 202106, 202108)

PARAM$archivo_entrada <- "../competencia_01_crudo.csv"
PARAM$archivo_dataset <- "datos/dataset_preprocesado.fst"

if (!file.exists(PARAM$archivo_entrada))
  stop("No encuentro ", PARAM$archivo_entrada,
    ". Esta carpeta tiene que estar adentro de la carpeta del dataset")

# [Anotación · líneas 61–80] Lee el CSV con fread. Arma una tabla auxiliar con la posición de cada fila, el
#   cliente y el mes convertido a número lineal (año × 12 + mes), la ordena por cliente y período y le agrega,
#   por cliente, el período de las dos filas siguientes (lead 1 y lead 2). Guarda el último período del dataset
#   y el anterior a ese.
#%% celda 6 [texto]
## 1 · Clase ternaria

#%% celda 7 [código]
dataset <- fread(PARAM$archivo_entrada)

# Los períodos se convierten a número lineal (año*12 + mes) para poder comparar 
# correctamente si los meses son consecutivos.
dsimple <- dataset[, list(
    "pos" = .I,
    numero_de_cliente,
    periodo0 = as.integer(foto_mes/100)*12 +  foto_mes%%100 ) ]

setorder( dsimple, numero_de_cliente, periodo0 )

periodo_ultimo     <- dsimple[, max(periodo0) ]
periodo_anteultimo <- periodo_ultimo - 1

dsimple[, c("periodo1", "periodo2") :=
    shift(periodo0, n=1:2, fill=NA, type="lead"),  numero_de_cliente ]

# [Anotación · líneas 82–99] Asigna la clase en tres pasos: CONTINUA a todas las filas de períodos anteriores
#   al anteúltimo; BAJA+1 a las filas anteriores al último período cuyo cliente no tiene registro en el mes
#   siguiente; BAJA+2 a las filas anteriores al anteúltimo cuyo cliente está en el mes siguiente y no en el
#   subsiguiente. Vuelve al orden original, copia clase_ternaria al dataset y muestra la cantidad de filas por
#   mes y clase. Según la salida guardada en el notebook, los meses presentes van de 202103 a 202108; la clase
#   queda en NA en todo 202108 y en las filas de 202107 que no son BAJA+1.
# El cliente sigue en el banco en los dos meses siguientes
dsimple[ periodo0 < periodo_anteultimo, clase_ternaria := "CONTINUA" ]

# El cliente se da de baja en el mes siguiente
dsimple[ periodo0 < periodo_ultimo &
    ( is.na(periodo1) | periodo0 + 1 < periodo1 ),
    clase_ternaria := "BAJA+1" ]

# El cliente sigue se da de baja en dos meses
dsimple[ periodo0 < periodo_anteultimo & (periodo0+1 == periodo1 )
    & ( is.na(periodo2) | periodo0 + 2 < periodo2 ),
    clase_ternaria := "BAJA+2" ]

setorder( dsimple, pos )
dataset[, clase_ternaria := dsimple$clase_ternaria ]
rm(dsimple)

dataset[, .N, list(foto_mes, clase_ternaria)][order(foto_mes, clase_ternaria)]

# [Anotación · líneas 101–109] Asigna NA a ccajas_depositos en las filas de 202105 (el comentario indica que
#   en ese mes todos sus valores son cero) y elimina las columnas cprestamos_personales y mprestamos_personales.
#%% celda 8 [texto]
## 2 · Data Quality y 3 · Data Drifting

#%% celda 9 [código]
# ccajas_depositos esta rota en 202105: todos sus valores son cero
dataset[foto_mes == 202105, ccajas_depositos := NA]

# variables con data drifting que saco
dataset[, c("cprestamos_personales", "mprestamos_personales") := NULL]

# [Anotación · líneas 111–125] Ordena el dataset por cliente y mes y toma como variables originales todas las
#   columnas menos numero_de_cliente, foto_mes y clase_ternaria. Para cada una crea las columnas _lag1 y _lag2
#   con el valor de la fila anterior y de dos filas atrás del mismo cliente (shift por numero_de_cliente; NA
#   cuando no hay fila previa).
#%% celda 10 [texto]
## 4 · Lags y delta lags de orden 1 y 2

#%% celda 11 [código]
# ordeno por cliente y mes, asi el "mes anterior" queda en la fila de arriba
setorder(dataset, numero_de_cliente, foto_mes)

cols_originales <- setdiff(colnames(dataset),
  c("numero_de_cliente", "foto_mes", "clase_ternaria"))

# lag1 = valor del mes anterior,  lag2 = valor de hace dos meses (por cliente)
dataset[, paste0(cols_originales, "_lag1") := shift(.SD, 1L, NA, "lag"),
  by= numero_de_cliente, .SDcols= cols_originales]
dataset[, paste0(cols_originales, "_lag2") := shift(.SD, 2L, NA, "lag"),
  by= numero_de_cliente, .SDcols= cols_originales]

# [Anotación · líneas 127–137] Conserva sólo las filas de los cinco meses de PARAM$meses_a_guardar; 202107
#   queda afuera después de haber aportado a los lags de 202108. Para cada variable original crea _delta1 y
#   _delta2 como el valor actual menos lag1 y menos lag2. Imprime la cantidad de columnas y filas: 753 y 818.713
#   según la salida guardada.
# me quedo solo con los meses que se usan despues (para ahorrar ram)
dataset <- dataset[foto_mes %in% PARAM$meses_a_guardar]
gc(full=TRUE, verbose=FALSE)

# delta1 = valor actual - lag1,   delta2 = valor actual - lag2
for (col in cols_originales) {
  dataset[, paste0(col, "_delta1") := get(col) - get(paste0(col, "_lag1"))]
  dataset[, paste0(col, "_delta2") := get(col) - get(paste0(col, "_lag2"))]
}

cat("Columnas:", ncol(dataset), "  Filas:", nrow(dataset), "\n")

# [Anotación · líneas 139–161] La celda de texto describe la transformación y la función rank_cero_fijo la
#   aplica a un vector: a los valores positivos les asigna su ranking (frank) dividido por la cantidad de
#   positivos, lo que da valores en (0, 1]; a los negativos, el ranking de su valor absoluto dividido por la
#   cantidad de negativos y con signo menos, en [-1, 0); el cero queda en 0 y los NA quedan NA.
#%% celda 12 [texto]
## 5 · Ranking con cero fijo, por variable y por mes

Para cada variable y cada mes por separado:
* positivos → `ranking / cantidad de positivos` (valores equiespaciados entre 0 y 1; el más grande vale 1)
* negativos → `−ranking / cantidad de negativos`, ordenados por valor absoluto (el más negativo vale −1)
* cero → 0
* NA → NA

Así el modelo aprende comportamiento relativo del cliente dentro de su cohorte, no valores absolutos que varían por inflación u otros factores externos.

#%% celda 13 [código]
# La función convierte cada valor numérico en su posición relativa dentro del mes, 
# separando positivos y negativos y respetando el cero
rank_cero_fijo <- function(x) {
  r <- rep(NA_real_, length(x))
  positivos <- which(x > 0)
  negativos <- which(x < 0)
  if (length(positivos) > 0) r[positivos] <-  frank(x[positivos]) / length(positivos)
  if (length(negativos) > 0) r[negativos] <- -frank(-x[negativos]) / length(negativos)
  r[which(x == 0)] <- 0
  r
}

# [Anotación · líneas 163–184] Arma la lista de columnas a transformar (todas menos numero_de_cliente,
#   foto_mes y clase_ternaria; 750 según la salida guardada) y los índices de fila de cada foto_mes. Define
#   avisar, que imprime mensajes con la hora. Recorre las columnas y, para cada una, aplica rank_cero_fijo por
#   separado a las filas de cada mes y reemplaza la columna original con el resultado; informa el avance cada
#   100 columnas.
cols_a_transformar <- setdiff(colnames(dataset),
  c("numero_de_cliente", "foto_mes", "clase_ternaria"))

# las filas de cada mes
filas_por_mes <- split(seq_len(nrow(dataset)), dataset$foto_mes)

avisar <- function(...) {
  cat(format(Sys.time(), "%H:%M:%S"), " ", ..., "\n", sep= "")
  flush.console()
}

avisar("Transformando ", length(cols_a_transformar), " columnas")
for (k in seq_along(cols_a_transformar)) {
  col <- cols_a_transformar[k]
  x <- dataset[[col]]
  nuevo <- rep(NA_real_, length(x))
  for (filas in filas_por_mes) nuevo[filas] <- rank_cero_fijo(x[filas])
  set(dataset, j= col, value= nuevo)   # reemplaza la columna original

  if (k %% 100 == 0) avisar("   ", k, " de ", length(cols_a_transformar), " columnas")
}
avisar("Listo")

# [Anotación · líneas 186–202] Control: calcula el mínimo y el máximo de todas las columnas transformadas y
#   detiene la ejecución si alguno queda fuera de [-1, 1]. Muestra, por mes, el mínimo, la mediana, el máximo,
#   la cantidad de ceros y la cantidad de NA de mcuentas_saldo.
#%% celda 14 [texto]
### Control

Para cada mes, el mínimo y el máximo de todas las columnas transformadas tienen que estar entre −1 y 1.
Abajo, como ejemplo, cómo queda `mcuentas_saldo` en cada mes.

#%% celda 15 [código]
minimo <- min(sapply(cols_a_transformar, function(c) min(dataset[[c]], na.rm= TRUE)))
maximo <- max(sapply(cols_a_transformar, function(c) max(dataset[[c]], na.rm= TRUE)))
cat("Minimo de todas las columnas:", minimo, "  Maximo:", maximo, "\n\n")
stopifnot(minimo >= -1, maximo <= 1)

dataset[, list(minimo= min(mcuentas_saldo, na.rm= TRUE),
               mediana= median(mcuentas_saldo, na.rm= TRUE),
               maximo= max(mcuentas_saldo, na.rm= TRUE),
               ceros= sum(mcuentas_saldo == 0, na.rm= TRUE),
               nulos= sum(is.na(mcuentas_saldo))), foto_mes][order(foto_mes)]

# [Anotación · líneas 204–220] Ordena el dataset por foto_mes y numero_de_cliente, crea la carpeta datos y lo
#   escribe en formato fst con compresión 50. Informa el tamaño del archivo, las filas y las columnas (1.35 GB,
#   818.713 filas y 753 columnas según la salida guardada) y vuelve a mostrar el conteo por mes y clase. La
#   última celda imprime la fecha y hora.
#%% celda 16 [texto]
## 6 · Guardo el dataset preprocesado

#%% celda 17 [código]
# ordenado por mes (asi los notebooks siguientes pueden leer solo los meses que necesitan)
setorder(dataset, foto_mes, numero_de_cliente)

dir.create("datos", showWarnings= FALSE)
avisar("Grabando ", PARAM$archivo_dataset)
write_fst(dataset, PARAM$archivo_dataset, compress= 50)
avisar("Listo: ", round(file.size(PARAM$archivo_dataset) / 1e9, 2), " GB, ",
  nrow(dataset), " filas, ", ncol(dataset), " columnas")

dataset[, .N, list(foto_mes, clase_ternaria)][order(foto_mes, clase_ternaria)]

#%% celda 18 [código]
format(Sys.time(), "%a %b %d %X %Y")
```

### 1_optimizacion_bayesiana.ipynb

Notebook de R que busca num_iterations, num_leaves y min_sum_hessian_in_leaf con mlr3mbo: 10 evaluaciones de LightGBM entrenado en 202103 y 202104 y medido por AUC en 202106. Escribe exp/BO/BO_log.txt y los 2 sets de mayor AUC en exp/mejores_hiperparametros.txt.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Celda de texto de presentación: el notebook requiere el notebook 0 corrido;
#   entrena en 202103 y 202104 con todos los registros y mide en 202106; hace 10 iteraciones con la semilla
#   370003 y guarda los 2 sets de mayor métrica en exp/mejores_hiperparametros.txt después de cada iteración.
#   Indica que, si la corrida se corta, al volver a correr sigue desde exp/BO/BO_log.txt.
#%% celda 1 [texto]
# 1 · Bayesian Optimization

**Antes:** tiene que estar corrido el notebook 0.

**Qué hace:**
* Entrena en **202103 + 202104** (todos los registros, **sin undersampling**) y mide en **202106**
* Hiperparámetros fijos y de la BO: num_iterations (64 a 4096), num_leaves (16 a 2048), min_sum_hessian_in_leaf (1e-06 a 0.1).
* **10 iteraciones** con la semilla **370003** (con 3 hiperparámetros, las 10 son al azar)
* Guarda los **2 mejores sets** de hiperparámetros en `exp/mejores_hiperparametros.txt`
  (se actualiza después de cada iteración, así el notebook 2 puede arrancar aunque esto se corte)

**Si se corta:** volver a correr todo. Sigue desde la última iteración guardada en `exp/BO/BO_log.txt`.

# [Anotación · líneas 15–36] Imprime la fecha y hora, limpia la memoria y carga data.table, R.utils, fst,
#   lightgbm, bbotk, mlr3, mlr3mbo, mlr3learners y DiceKriging, instalando los que falten. Imprime la cantidad
#   de núcleos.
#%% celda 2 [texto]
### Librerías

#%% celda 3 [código]
format(Sys.time(), "%a %b %d %X %Y")

# limpio la memoria
rm(list=ls(all.names=TRUE))
gc(full=TRUE, verbose=FALSE)

# cargo las librerias (la primera vez se instalan y tarda varios minutos)
options(repos= c(CRAN= "https://cloud.r-project.org"))
options(width= 200)

for (paquete in c("data.table", "R.utils", "fst", "lightgbm", "bbotk", "mlr3", "mlr3mbo", "mlr3learners", "DiceKriging")) {
  if (!require(paquete, character.only= TRUE)) {
    install.packages(paquete)
    library(paquete, character.only= TRUE)
  }
}

cat("Nucleos disponibles:", parallel::detectCores(), "\n")

# [Anotación · líneas 38–61] Define PARAM: archivo del dataset preprocesado, semilla 370003, meses de
#   entrenamiento de la optimización (202103 y 202104), mes de prueba (202106), 10 iteraciones y los cortes
#   donde se informa la ganancia (de 9.000 a 14.000 de a 500). Detiene la ejecución si el dataset preprocesado
#   no existe.
#%% celda 4 [texto]
### Parámetros

#%% celda 5 [código]
PARAM <- list()

PARAM$archivo_dataset <- "datos/dataset_preprocesado.fst"

# Mi semilla
PARAM$semilla <- 370003

# training y testing de la BO
PARAM$bo_train <- c(202103, 202104)
PARAM$bo_test  <- c(202106)

# cantidad de combinaciones que prueba la BO
# (las primeras 4 x 3 = 12 serian al azar, asi que con 10 son todas al azar)
PARAM$bo_iteraciones <- 10

# cortes donde mido la ganancia en 202106 (solo informativo)
PARAM$cortes <- seq(9000, 14000, by= 500)

if (!file.exists(PARAM$archivo_dataset))
  stop("No existe ", PARAM$archivo_dataset, ". Primero hay que correr el notebook 0")

# [Anotación · líneas 63–99] Lista de hiperparámetros fijos de LightGBM: boosting gbdt, objective binary,
#   metric auc, force_row_wise y deterministic en TRUE, max_depth -1, min_gain_to_split 0, lambda_l1 0,
#   lambda_l2 0, bagging_fraction 1.0, is_unbalance FALSE, scale_pos_weight 1.0, extra_trees FALSE, use_missing
#   TRUE, max_bin 31, min_data_in_leaf 0, feature_fraction 0.50, feature_fraction_bynode 0.20 y learning_rate
#   0.005. num_iterations 1000, num_leaves 64 y min_sum_hessian_in_leaf 0.001 figuran como valores por defecto
#   que la optimización reemplaza. El bloque es idéntico al de las líneas 75 a 107 del notebook 2.
#%% celda 6 [código]
# Hiperparametros FIJOS de LightGBM: los que pide el profesor (punto 1.7)
# ⚠️ Este bloque tiene que ser IGUAL en los notebooks 1 y 2

PARAM$lgbm$param_fijos <- list(
  boosting=           "gbdt",
  objective=          "binary",
  metric=             "auc",
  first_metric_only=  FALSE,
  boost_from_average= TRUE,
  feature_pre_filter= FALSE,
  force_row_wise=     TRUE,
  deterministic=      TRUE,
  verbosity=          -100,

  max_depth=          -1L,
  min_gain_to_split=  0,
  lambda_l1=          0,
  lambda_l2=          0,
  bagging_fraction=   1.0,       # sin bagging
  is_unbalance=       FALSE,
  scale_pos_weight=   1.0,
  extra_trees=        FALSE,
  use_missing=        TRUE,      # para que LightGBM entienda los NA

  # ---- fijos ----
  max_bin=                 31L,
  min_data_in_leaf=        0L,
  feature_fraction=        0.50,
  feature_fraction_bynode= 0.20,
  learning_rate=           0.005,

  # ---- estos tres los elige la BO (aca solo hay un valor por defecto) ----
  num_iterations=          1000L,
  num_leaves=              64L,
  min_sum_hessian_in_leaf= 0.001
)

# [Anotación · líneas 101–116] Espacio de búsqueda definido con ps(): num_iterations entero entre 64 y 4096,
#   num_leaves entero entre 16 y 2048 y min_sum_hessian_in_leaf real entre 1e-06 y 0.1. La tabla de la celda de
#   texto previa indica 1.0 como límite superior de min_sum_hessian_in_leaf; el código usa 0.1.
#%% celda 7 [texto]
Hiperparámetros de la BO (los que pide el profesor). Los rangos son los que veníamos usando,
porque el profesor no los especifica:

| Hiperparámetro | desde | hasta |
|---|---|---|
| `num_iterations` | 64 | 4096 |
| `num_leaves` | 16 | 2048 |
| `min_sum_hessian_in_leaf` | 0.000001 | 1.0 |

#%% celda 8 [código]
PARAM$bo_espacio <- ps(
  num_iterations=          p_int(lower= 64L,   upper= 4096L),
  num_leaves=              p_int(lower= 16L,   upper= 2048L),
  min_sum_hessian_in_leaf= p_dbl(lower= 1e-06, upper= 0.1)
)

# [Anotación · líneas 118–137] Define avisar, que imprime un mensaje con la hora, y mostrar_avance, un
#   callback de LightGBM que imprime el número de árbol cada 250 iteraciones y en la última.
#%% celda 9 [texto]
### Funciones

#%% celda 10 [código]
# escribe un mensaje con la hora
avisar <- function(...) {
  cat(format(Sys.time(), "%H:%M:%S"), " ", ..., "\n", sep= "")
  flush.console()
}

# muestra el avance de LightGBM mientras entrena (cada 250 arboles)
mostrar_avance <- function(env) {
  if (env$iteration %% 250 == 0 || env$iteration == env$end_iteration) {
    cat("      ", format(Sys.time(), "%H:%M:%S"),
      "  arbol ", env$iteration, " de ", env$end_iteration, "\n", sep= "")
    flush.console()
  }
}
attr(mostrar_avance, "call") <- quote(mostrar_avance())
attr(mostrar_avance, "name") <- "mostrar_avance"

# [Anotación · líneas 139–161] Define leer_meses, que lee del archivo fst el rango de filas que abarca los
#   meses pedidos y filtra esos meses; calcular_auc, que obtiene el AUC a partir de la suma de rankings de los
#   positivos; y calcular_ganancias, que ordena por probabilidad descendente, acumula la ganancia y devuelve el
#   acumulado en cada corte pedido.
# lee del dataset preprocesado solo los meses pedidos
# (el archivo esta ordenado por foto_mes, asi no se carga todo en memoria)
leer_meses <- function(meses) {
  foto_mes <- read_fst(PARAM$archivo_dataset, columns= "foto_mes")$foto_mes
  filas <- which(foto_mes %in% meses)
  dt <- read_fst(PARAM$archivo_dataset, from= min(filas), to= max(filas),
    as.data.table= TRUE)
  dt[foto_mes %in% meses]
}

# AUC (area bajo la curva ROC), calculado a partir de los rankings
calcular_auc <- function(clase, prob) {
  rango <- frank(prob)
  n1 <- sum(clase == 1)
  n0 <- sum(clase == 0)
  (sum(rango[clase == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0)
}

# ganancia si le envio estimulo a los primeros N clientes (para cada N de cortes)
calcular_ganancias <- function(prob, gan, cortes) {
  acumulada <- cumsum(gan[order(-prob)])
  acumulada[cortes]
}

# [Anotación · líneas 163–192] Crea exp/BO, lee 202103, 202104 y 202106 y arma clase01: 1 si clase_ternaria es
#   BAJA+1 o BAJA+2, 0 en otro caso. Las variables del modelo son todas las columnas menos foto_mes,
#   clase_ternaria y clase01 (751 según la salida guardada, con numero_de_cliente incluido). Construye el
#   lgb.Dataset de entrenamiento con todas las filas de 202103 y 202104 (326.184 según la salida guardada), la
#   matriz de 202106 (164.114 filas) y una tabla de prueba con clase01 y la ganancia por fila: 1.072.500 si es
#   BAJA+2 y -27.500 en otro caso.
#%% celda 11 [texto]
## Datos de training (202103 + 202104) y testing (202106)

#%% celda 12 [código]
dir.create("exp/BO", showWarnings= FALSE, recursive= TRUE)

dataset <- leer_meses(c(PARAM$bo_train, PARAM$bo_test))
dataset[, clase01 := ifelse(clase_ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)]

# las variables del modelo (todas menos estas)
campos_buenos <- setdiff(colnames(dataset), c("foto_mes", "clase_ternaria", "clase01"))
cat("Variables del modelo:", length(campos_buenos), "\n")

# training: TODOS los registros de 202103 y 202104, sin undersampling
dtrain <- lgb.Dataset(
  data=  data.matrix(dataset[foto_mes %in% PARAM$bo_train, campos_buenos, with= FALSE]),
  label= dataset[foto_mes %in% PARAM$bo_train, clase01],
  free_raw_data= TRUE
)

# testing: 202106, aca se miden el AUC y la ganancia
mtest <- data.matrix(dataset[foto_mes %in% PARAM$bo_test, campos_buenos, with= FALSE])
dtest <- dataset[foto_mes %in% PARAM$bo_test,
  list(numero_de_cliente, clase01,
       gan= ifelse(clase_ternaria == "BAJA+2", 1072500, -27500))]

cat("Filas training:", nrow(dtrain), "  Filas testing:", nrow(mtest), "\n")

rm(dataset)
gc(full=TRUE, verbose=FALSE)

# [Anotación · líneas 194–213] Fija exp/BO/BO_log.txt como archivo de registro y el contador de iteraciones
#   giter en 0. Define guardar_mejores, que lee el registro, lo ordena por AUC descendente, toma las 2 primeras
#   filas, les agrega la columna set (1 y 2) y las escribe en exp/mejores_hiperparametros.txt.
#%% celda 13 [texto]
## Configuración de la BO

`Estimar_lightgbm` entrena un LightGBM con la combinación propuesta, lo mide en 202106,
agrega una línea a `exp/BO/BO_log.txt` y actualiza `exp/mejores_hiperparametros.txt`.

#%% celda 14 [código]
archivo_log <- "exp/BO/BO_log.txt"
giter <- 0

# guarda los 2 mejores sets de hiperparametros (por AUC)
guardar_mejores <- function() {
  log_bo <- fread(archivo_log)
  setorder(log_bo, -auc)
  mejores <- log_bo[1:min(2, .N)]
  mejores[, set := .I]
  setcolorder(mejores, "set")
  fwrite(mejores, "exp/mejores_hiperparametros.txt", sep= "\t")
  invisible(mejores)
}

# [Anotación · líneas 215–254] Función objetivo Estimar_lightgbm: combina los hiperparámetros fijos con los
#   tres propuestos, fija seed 370003 y entrena un LightGBM sobre 202103 y 202104 con la cantidad de iteraciones
#   propuesta; lgb.train se llama sin conjunto de validación. Predice 202106, calcula el AUC y la ganancia en
#   cada corte y agrega una línea a BO_log.txt con la iteración, la semilla, los hiperparámetros, el AUC, la
#   ganancia máxima entre los cortes, el corte donde ocurre y los minutos. Actualiza
#   exp/mejores_hiperparametros.txt y devuelve el AUC.
Estimar_lightgbm <- function(xs) {

  giter <<- giter + 1
  t0 <- Sys.time()

  avisar("Iteracion ", giter, " de ", PARAM$bo_iteraciones)
  avisar("   entrenando con: ",
    paste(names(xs), "=", signif(unlist(xs), 4), collapse= ", "))

  param_completo <- modifyList(PARAM$lgbm$param_fijos, xs)
  param_completo$seed <- PARAM$semilla

  modelo <- lgb.train(data= dtrain, param= param_completo,
    callbacks= list(mostrar_avance))

  avisar("   prediciendo 202106 y calculando AUC y ganancia")
  prob <- predict(modelo, mtest)
  ganancias <- calcular_ganancias(prob, dtest$gan, PARAM$cortes)

  registro <- data.table(
    iter=    giter,
    semilla= PARAM$semilla,
    as.data.table(xs),
    auc=     calcular_auc(dtest$clase01, prob),
    ganancia_max= max(ganancias),
    envios_max=   PARAM$cortes[which.max(ganancias)],
    minutos= round(as.numeric(
      difftime(Sys.time(), t0, units= "mins")), 1)
  )
  fwrite(registro, archivo_log, sep= "\t", append= file.exists(archivo_log))
  guardar_mejores()

  avisar("   listo en ", registro$minutos, " min.",
    "  AUC = ", round(registro$auc, 5),
    "  ganancia = ", round(registro$ganancia_max / 1e6, 1), " millones",
    ", corte = ", registro$envios_max)

  set.seed(PARAM$semilla, kind= "L'Ecuyer-CMRG")
  return(list(auc= registro$auc))
}

# [Anotación · líneas 256–288] Fija la semilla 370003 con el generador L'Ecuyer-CMRG. Declara el objetivo de
#   bbotk (maximizar auc sobre el espacio de búsqueda) y la instancia de optimización con un terminador de 10
#   evaluaciones. Si existe BO_log.txt, verifica que tenga las columnas del espacio de búsqueda, carga sus
#   evaluaciones al archivo de la instancia, continúa la numeración de iteraciones y marca la optimización como
#   terminada si ya hay 10 filas.
#%% celda 15 [código]
set.seed(PARAM$semilla, kind= "L'Ecuyer-CMRG")

objective <- ObjectiveRFun$new(
  fun=      Estimar_lightgbm,
  domain=   PARAM$bo_espacio,
  codomain= ps(auc= p_dbl(tags= "maximize")),
  id=       "BO_lightgbm"
)

instance <- OptimInstanceBatchSingleCrit$new(
  objective=  objective,
  terminator= trm("evals", n_evals= PARAM$bo_iteraciones)
)

# si la BO ya habia empezado, retomo desde lo que quedo en BO_log.txt
bo_terminada <- FALSE
if (file.exists(archivo_log)) {
  log_anterior <- fread(archivo_log)

  if (!all(PARAM$bo_espacio$ids() %in% names(log_anterior)))
    stop("El BO_log.txt es de un espacio de busqueda distinto.",
      " Borra la carpeta exp/BO y volve a correr")

  giter <- max(log_anterior$iter)
  bo_terminada <- nrow(log_anterior) >= PARAM$bo_iteraciones

  instance$archive$add_evals(
    xdt= log_anterior[, PARAM$bo_espacio$ids(), with= FALSE],
    ydt= log_anterior[, list(auc)]
  )
  avisar("Retomo la BO: ya hay ", nrow(log_anterior), " iteraciones hechas")
}

# [Anotación · líneas 290–306] Configura el optimizador mbo de mlr3mbo: lazo bayesopt_ego, modelo sustituto de
#   kriging (regr.km con optim.method BFGS y nugget.estim TRUE), función de adquisición expected improvement
#   optimizada con búsqueda al azar de 1.000 puntos, y diseño inicial de tamaño min(4 × 3, 10) = 10. Con 10
#   evaluaciones en total, todas pertenecen al diseño inicial; los comentarios del código las describen como al
#   azar.
surrogate <- srlrn(lrn("regr.km",
  optim.method= "BFGS",
  nugget.estim= TRUE,
  control=      list(trace= FALSE)))

# las primeras 4 x (cantidad de hiperparametros) son al azar, sin pasarse de las iteraciones
cantidad_al_azar <- min(4 * length(PARAM$bo_espacio$ids()), PARAM$bo_iteraciones)

optimizer <- opt("mbo",
  loop_function= bayesopt_ego,
  surrogate=     surrogate,
  acq_function=  acqf("ei"),
  acq_optimizer= acqo(
    optimizer=  opt("random_search", batch_size= 1000),
    terminator= trm("evals", n_evals= 1000)),
  args= list(init_design_size= cantidad_al_azar)
)

# [Anotación · líneas 308–321] Corre la optimización, salvo que el registro ya tenga las 10 iteraciones. Según
#   la salida guardada, la corrida va de las 04:58 a las 06:15 y evalúa 10 combinaciones.
#%% celda 16 [texto]
## Corrida de la BO  ⏳

Cada combinación muestra con qué hiperparámetros entrena, el avance cada 250 árboles,
y al terminar su AUC y su ganancia en 202106.

#%% celda 17 [código]
if (bo_terminada) {
  avisar("La BO ya estaba terminada")
} else {
  avisar("Arranca la BO. Las primeras ", cantidad_al_azar, " iteraciones son al azar")
  optimizer$optimize(instance)
  avisar("Termino la BO")
}

# [Anotación · líneas 323–340] Lee BO_log.txt, lo ordena por AUC descendente, agrega la ganancia máxima en
#   millones e imprime todas las iteraciones; vuelve a escribir exp/mejores_hiperparametros.txt. Según la salida
#   guardada, el AUC de las 10 iteraciones va de 0.91728 a 0.92043. La última celda imprime la fecha y hora.
#%% celda 18 [texto]
## Resultado

Todas las iteraciones ordenadas por AUC, y los **2 mejores sets** que va a usar el notebook 2
(guardados en `exp/mejores_hiperparametros.txt`).

#%% celda 19 [código]
tb_BO <- fread(archivo_log)
setorder(tb_BO, -auc)
tb_BO[, ganancia_millones := round(ganancia_max / 1e6, 1)]
print(tb_BO[, list(iter, num_iterations, num_leaves, min_sum_hessian_in_leaf,
  auc, ganancia_millones, envios_max, minutos)])

cat("\nLos 2 mejores sets (exp/mejores_hiperparametros.txt):\n")
guardar_mejores()

#%% celda 20 [código]
format(Sys.time(), "%a %b %d %X %Y")
```

### 3b_corte_y_entrega_sets_combinados.ipynb

Notebook de R que lee las predicciones guardadas en exp/modelos/, promedia los 40 modelos finales de los sets 1 y 2, calcula la curva de ganancia del backtest en 202106, aplica el corte de 11.750 envíos y escribe el archivo de entrega y su resumen en exp/entregas/. No entrena modelos.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Celda de texto de presentación: el notebook junta los modelos de los dos sets de
#   hiperparámetros (20 semillas con cada uno, 40 modelos) en un solo ensemble, leyendo la predicción de cada
#   modelo desde exp/modelos/ y promediando los 40; además calcula el ensemble de cada set por separado para el
#   gráfico. Requiere el notebook 2 corrido con el set 1 y con el set 2. Se presenta como igual al 'notebook 3',
#   que no está en el repositorio.
#%% celda 1 [texto]
# 3b · Ensemble combinando los sets 1 y 2 + corte y entrega

Igual que el notebook 3, pero junta los modelos de los **dos sets de hiperparámetros**
(20 semillas con el set 1 + 20 con el set 2 = **40 modelos**) en un solo ensemble.

**Cómo arma el ensemble:** lee la predicción de **cada modelo** desde `exp/modelos/`
(no las tablas `probabilidades_*.csv`, que ya traen su propio `prob_ensemble` adentro)
y hace el **promedio simple de los 40 modelos**. Así ningún ensemble parcial entra en el promedio.

Además calcula el ensemble de cada set por separado, solo para compararlos en el gráfico.

**Antes:** tiene que estar corrido el notebook 2 con `PARAM$set_hiperparametros <- 1` y con `<- 2`.

# [Anotación · líneas 15–36] Imprime la fecha y hora, limpia la memoria y carga data.table, R.utils, fst,
#   lightgbm y ggplot2, instalando los que falten. Imprime la cantidad de núcleos.
#%% celda 2 [texto]
### Librerías

#%% celda 3 [código]
format(Sys.time(), "%a %b %d %X %Y")

# limpio la memoria
rm(list=ls(all.names=TRUE))
gc(full=TRUE, verbose=FALSE)

# cargo las librerias (la primera vez se instalan y tarda varios minutos)
options(repos= c(CRAN= "https://cloud.r-project.org"))
options(width= 200)

for (paquete in c("data.table", "R.utils", "fst", "lightgbm", "ggplot2")) {
  if (!require(paquete, character.only= TRUE)) {
    install.packages(paquete)
    library(paquete, character.only= TRUE)
  }
}

cat("Nucleos disponibles:", parallel::detectCores(), "\n")

# [Anotación · líneas 38–54] Define PARAM: los sets que se combinan (1 y 2), el dataset preprocesado, el mes
#   del backtest (202106), el límite del gráfico (20.000 envíos) y los cortes de la tabla de ganancias (de 8.000
#   a 15.000 de a 500). Arma el sufijo sets12 que identifica los archivos de salida.
#%% celda 4 [texto]
### Parámetros

#%% celda 5 [código]
PARAM <- list()

# ✏️ los sets que se juntan en el ensemble
PARAM$sets <- c(1, 2)

PARAM$archivo_dataset <- "datos/dataset_preprocesado.fst"
PARAM$backtest_test   <- c(202106)

# rango del grafico y de la tabla de ganancias
PARAM$grafico_hasta <- 20000
PARAM$tabla_cortes  <- seq(8000, 15000, by= 500)

nombre_sets <- paste0("sets", paste(PARAM$sets, collapse= ""))   # ej: "sets12"

# [Anotación · líneas 56–99] Define las mismas funciones auxiliares que los notebooks 1 y 2 (avisar,
#   mostrar_avance, leer_meses, calcular_auc y calcular_ganancias). En el resto de este notebook sólo se llama
#   leer_meses.
#%% celda 6 [texto]
### Funciones

#%% celda 7 [código]
# escribe un mensaje con la hora
avisar <- function(...) {
  cat(format(Sys.time(), "%H:%M:%S"), " ", ..., "\n", sep= "")
  flush.console()
}

# muestra el avance de LightGBM mientras entrena (cada 250 arboles)
mostrar_avance <- function(env) {
  if (env$iteration %% 250 == 0 || env$iteration == env$end_iteration) {
    cat("      ", format(Sys.time(), "%H:%M:%S"),
      "  arbol ", env$iteration, " de ", env$end_iteration, "\n", sep= "")
    flush.console()
  }
}
attr(mostrar_avance, "call") <- quote(mostrar_avance())
attr(mostrar_avance, "name") <- "mostrar_avance"

# lee del dataset preprocesado solo los meses pedidos
# (el archivo esta ordenado por foto_mes, asi no se carga todo en memoria)
leer_meses <- function(meses) {
  foto_mes <- read_fst(PARAM$archivo_dataset, columns= "foto_mes")$foto_mes
  filas <- which(foto_mes %in% meses)
  dt <- read_fst(PARAM$archivo_dataset, from= min(filas), to= max(filas),
    as.data.table= TRUE)
  dt[foto_mes %in% meses]
}

# AUC (area bajo la curva ROC), calculado a partir de los rankings
calcular_auc <- function(clase, prob) {
  rango <- frank(prob)
  n1 <- sum(clase == 1)
  n0 <- sum(clase == 0)
  (sum(rango[clase == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0)
}

# ganancia si le envio estimulo a los primeros N clientes (para cada N de cortes)
calcular_ganancias <- function(prob, gan, cortes) {
  acumulada <- cumsum(gan[order(-prob)])
  acumulada[cortes]
}

# [Anotación · líneas 101–132] armar_tabla_sets recibe el tipo de modelo (final o backtest) y la lista de
#   sets. Para cada set lee los archivos exp/modelos/<tipo>_set<s>_s<semilla>.txt, verifica que todos tengan los
#   mismos clientes y agrega una columna prob_set<s>_s<semilla> por modelo. Después calcula ensemble_set<s> como
#   el promedio de las columnas de cada set y prob_ensemble como el promedio de todas las columnas de modelos
#   (rowMeans), sin incluir los promedios por set.
#%% celda 8 [código]
# junta las predicciones de todos los modelos de los sets pedidos.
# Arma una columna por modelo (prob_set1_s450862, prob_set2_s450862, ...),
# el ensemble de cada set por separado (ensemble_set1, ensemble_set2, solo para comparar)
# y prob_ensemble = promedio simple de TODOS los modelos
armar_tabla_sets <- function(tipo, sets) {      # tipo: "final" o "backtest"
  tabla <- NULL
  for (s in sets) {
    archivos <- sort(list.files("exp/modelos",
      pattern= paste0("^", tipo, "_set", s, "_s"), full.names= TRUE))
    for (archivo in archivos) {
      pred <- fread(archivo)
      setorder(pred, numero_de_cliente)
      semilla <- sub(".*_s([0-9]+)\\.txt$", "\\1", archivo)
      if (is.null(tabla)) tabla <- pred[, list(numero_de_cliente)]
      stopifnot(identical(tabla$numero_de_cliente, pred$numero_de_cliente))
      tabla[, paste0("prob_set", s, "_s", semilla) := pred$prob]
    }
  }
  if (is.null(tabla)) return(NULL)

  # columnas de los modelos (no incluye ningun ensemble)
  modelos <- grep("^prob_set[0-9]+_s", names(tabla), value= TRUE)

  for (s in sets) {
    cols_set <- grep(paste0("^prob_set", s, "_s"), modelos, value= TRUE)
    if (length(cols_set) > 0)
      tabla[, paste0("ensemble_set", s) := rowMeans(.SD), .SDcols= cols_set]
  }
  tabla[, prob_ensemble := rowMeans(.SD), .SDcols= modelos]
  tabla
}

# [Anotación · líneas 134–160] Arma la tabla de modelos finales (202108) y la del backtest (202106) y detiene
#   la ejecución si alguna queda vacía. A la del backtest le agrega la clase_ternaria de 202106 leída del
#   dataset preprocesado. Cuenta los modelos por set (20 finales y 5 de backtest por set, 40 en el ensemble
#   final, según la salida guardada) y escribe exp/probabilidades_202108_sets12.csv y
#   exp/probabilidades_202106_backtest_sets12.csv.
#%% celda 9 [texto]
## Tablas de probabilidades con todos los modelos

#%% celda 10 [código]
tabla_final <- armar_tabla_sets("final", PARAM$sets)
tabla_bt    <- armar_tabla_sets("backtest", PARAM$sets)

if (is.null(tabla_final)) stop("No hay modelos finales. Falta correr el notebook 2")
if (is.null(tabla_bt))    stop("No hay modelos del backtest. Falta correr el notebook 2")

clases <- leer_meses(PARAM$backtest_test)[, list(numero_de_cliente, clase_ternaria)]
tabla_bt[clases, on= "numero_de_cliente", clase_ternaria := i.clase_ternaria]

# cuantos modelos hay de cada set
contar <- function(tabla) {
  sapply(PARAM$sets, function(s) sum(grepl(paste0("^prob_set", s, "_s"), names(tabla))))
}
cantidad_final <- sum(grepl("^prob_set[0-9]+_s", names(tabla_final)))
cantidad_bt    <- sum(grepl("^prob_set[0-9]+_s", names(tabla_bt)))

print(data.table(set= PARAM$sets,
  modelos_finales_202108= contar(tabla_final),
  modelos_backtest_202106= contar(tabla_bt)))
cat("\nModelos en el ensemble final:", cantidad_final, "\n")

fwrite(tabla_final, paste0("exp/probabilidades_202108_", nombre_sets, ".csv"))
fwrite(tabla_bt, paste0("exp/probabilidades_202106_backtest_", nombre_sets, ".csv"))

# [Anotación · líneas 162–183] Con la tabla del backtest calcula tres curvas de ganancia acumulada (set 1, set
#   2 y todos juntos): asigna 1.072.500 a cada BAJA+2 y -27.500 al resto, ordena por probabilidad descendente y
#   acumula. Para cada curva toma la cantidad de envíos donde la ganancia acumulada es máxima y la imprime;
#   guarda aparte el máximo de 'todos juntos'. Según la salida guardada: 11.852 envíos (set 1), 10.746 (set 2) y
#   10.530 (todos juntos).
#%% celda 11 [texto]
## Ganancia vs. cantidad de envíos (backtest en 202106)

Tres curvas: el ensemble de cada set por separado y el de **todos juntos** (el que se usa para el bot).

#%% celda 12 [código]
columnas_curva <- c(paste0("ensemble_set", PARAM$sets), "prob_ensemble")
columnas_curva <- intersect(columnas_curva, names(tabla_bt))
gan <- ifelse(tabla_bt$clase_ternaria == "BAJA+2", 1072500, -27500)

curvas <- rbindlist(lapply(columnas_curva, function(col) {
  orden <- order(-tabla_bt[[col]])
  data.table(
    ensemble= ifelse(col == "prob_ensemble", "todos juntos",
                     sub("ensemble_set", "solo set ", col)),
    envios= seq_along(orden),
    ganancia= cumsum(gan[orden]))
}))

mejores <- curvas[, .SD[which.max(ganancia)], by= ensemble]
print(mejores[, list(ensemble, envios, ganancia_millones= round(ganancia / 1e6, 1))])
mejor <- mejores[ensemble == "todos juntos"]

# [Anotación · líneas 185–205] Grafica las tres curvas hasta 20.000 envíos, con una línea vertical punteada en
#   el máximo de 'todos juntos', y guarda el gráfico en exp/ganancia_vs_envios_sets12.png. Muestra una tabla con
#   la ganancia en millones de cada curva en los cortes de 8.000 a 15.000 de a 500.
grafico <- ggplot(curvas[envios <= PARAM$grafico_hasta],
                  aes(x= envios, y= ganancia / 1e6, color= ensemble)) +
  geom_line(aes(linewidth= ensemble == "todos juntos")) +
  scale_linewidth_manual(values= c(`FALSE`= 0.5, `TRUE`= 1.1), guide= "none") +
  geom_vline(xintercept= mejor$envios, linetype= "dashed") +
  annotate("text", x= mejor$envios, y= mejor$ganancia / 1e6,
    label= paste0("  maximo (todos juntos): ", mejor$envios, " envios"),
    hjust= 0, vjust= -0.5) +
  scale_x_continuous(breaks= seq(0, PARAM$grafico_hasta, by= 2000)) +
  scale_y_continuous(expand= expansion(mult= c(0.02, 0.12))) +
  labs(x= "Cantidad de envios", y= "Ganancia (millones)", color= "Ensemble",
    title= paste0("Ganancia en 202106 (backtest, ", cantidad_bt, " modelos en total)")) +
  theme_minimal(base_size= 16) + theme(legend.position= "top")

options(repr.plot.width= 16, repr.plot.height= 8)
print(grafico)
ggsave(paste0("exp/ganancia_vs_envios_", nombre_sets, ".png"), grafico, width= 12, height= 6)

# tabla de ganancias en cortes redondos, una columna por ensemble
dcast(curvas[envios %in% PARAM$tabla_cortes],
  envios ~ ensemble, value.var= "ganancia", fun.aggregate= function(x) round(x / 1e6, 1))

# [Anotación · líneas 207–226] El corte se escribe a mano en CORTES; el archivo quedó guardado con c(11750).
#   Si el vector es NA y la sesión es interactiva, lo pide por teclado. Detiene la ejecución si no hay corte o
#   si alguno está fuera del rango entre 1 y la cantidad de clientes de 202108.
#%% celda 13 [texto]
## Elegí el corte  ✏️

Escribie el corte en la primera línea de la celda (`CORTES <- c(11000, 11500, 12000)`).

#%% celda 14 [código]
CORTES <- c(11750)   # Escribir aca el corte. Ejemplo: CORTES <- c(11000)

if (all(is.na(CORTES)) && interactive()) {
  respuesta <- readline("Cuantos envios? (si son varios, separalos con espacios): ")
  CORTES <- suppressWarnings(as.integer(strsplit(trimws(respuesta), "[ ,;]+")[[1]]))
}

if (length(CORTES) == 0 || any(is.na(CORTES)))
  stop("No hay corte. Escribilo en la primera linea de esta celda, por ejemplo",
    " CORTES <- c(11000), y volve a correrla")
if (any(CORTES < 1 | CORTES > nrow(tabla_final)))
  stop("Los cortes tienen que estar entre 1 y ", nrow(tabla_final))

cat("Cortes elegidos:", CORTES, "\n")

# [Anotación · líneas 228–252] Crea exp/entregas, arma una marca con mes, día, hora y minuto y ordena la tabla
#   final por prob_ensemble descendente. Para cada corte toma los primeros numero_de_cliente, los formatea como
#   enteros, verifica que no haya duplicados ni notación científica y los escribe, uno por línea y sin
#   encabezado, en exp/entregas/v3_sets12_<cantidad de modelos>mod_c<corte>_<marca>.csv. Arma el nombre del
#   envío (v3sets12c11750t<marca>).
#%% celda 15 [texto]
## Archivos para el bot

Con el ensemble de **todos los modelos juntos** (`prob_ensemble`). Quedan en `exp/entregas/`, junto con un resumen.

#%% celda 16 [código]
dir.create("exp/entregas", showWarnings= FALSE, recursive= TRUE)

marca <- format(Sys.time(), "%m%d%H%M")   # mes, dia, hora y minuto: el nombre nunca se repite
setorder(tabla_final, -prob_ensemble)

archivos_bot <- c()
for (corte in CORTES) {
  # sprintf("%.0f") escribe los numeros como enteros, nunca como 4.8e+07
  ids <- sprintf("%.0f", tabla_final[1:corte, numero_de_cliente])
  stopifnot(!anyDuplicated(ids), !any(grepl("e", ids)))

  archivo <- paste0("exp/entregas/v3_", nombre_sets, "_", cantidad_final, "mod_c",
    corte, "_", marca, ".csv")
  writeLines(ids, archivo)
  archivos_bot <- c(archivos_bot, archivo)
  cat("Generado:", archivo, " (", length(ids), "clientes )\n")
}

nombre_submit <- paste0("v3", nombre_sets, "c", paste(CORTES, collapse= "c"), "t", marca)

# [Anotación · líneas 254–288] Escribe exp/entregas/resumen_<marca>.txt: fecha, cantidad de modelos del
#   ensemble, hiperparámetros y semillas de cada set (leídos de exp/mejores_hiperparametros.txt y de los nombres
#   de columnas), los hiperparámetros fijos, la ganancia del backtest en cada corte elegido, el máximo de cada
#   curva, el mensaje de envío y los nombres de los archivos generados seguidos del texto 'ganancia del bot:'
#   sin valor. Imprime el resumen en pantalla.
# ---- resumen ----
archivo_resumen <- paste0("exp/entregas/resumen_", marca, ".txt")
escribir <- function(...) cat(..., "\n", file= archivo_resumen, append= TRUE, sep= "")

escribir("RESUMEN DE LA ENTREGA   ", format(Sys.time(), "%Y-%m-%d %H:%M"))
escribir("")
escribir("Ensemble: promedio simple de ", cantidad_final, " LightGBM")
hiper <- fread("exp/mejores_hiperparametros.txt")
for (s in PARAM$sets) {
  h <- hiper[set == s]
  semillas <- sub(paste0("prob_set", s, "_s"), "",
    grep(paste0("^prob_set", s, "_s"), names(tabla_final), value= TRUE))
  escribir("Set ", s, ": ", length(semillas), " modelos.  num_iterations = ", h$num_iterations,
    ", num_leaves = ", h$num_leaves,
    ", min_sum_hessian_in_leaf = ", signif(h$min_sum_hessian_in_leaf, 4))
  escribir("   semillas: ", paste(semillas, collapse= ", "))
}
escribir("Fijos: max_bin 31, min_data_in_leaf 0, feature_fraction 0.5,",
  " feature_fraction_bynode 0.2, learning_rate 0.005")
escribir("")
escribir("Ganancia en el backtest 202106 (todos juntos, ", cantidad_bt, " modelos):")
curva_todos <- curvas[ensemble == "todos juntos"]
for (corte in CORTES)
  escribir("   ", corte, " envios: ",
    round(curva_todos[envios == corte, ganancia] / 1e6, 1), " millones")
for (k in seq_len(nrow(mejores)))
  escribir("   maximo ", mejores$ensemble[k], ": ", round(mejores$ganancia[k] / 1e6, 1),
    " millones con ", mejores$envios[k], " envios")
escribir("")
escribir("Mensaje para el bot:  submit    ", nombre_submit)
escribir("Archivos:")
escribir(paste0("   ", basename(archivos_bot), "   ->  ganancia del bot: ", collapse= "\n"))

cat("\n")
cat(readLines(archivo_resumen), sep= "\n")
```

### 2_modelos_semillas.ipynb

Notebook de R que, para un set de hiperparámetros, entrena 5 modelos de backtest (202103 y 202104, predice 202106) y 20 modelos finales (202103 a 202106, predice 202108), uno por semilla, y guarda la probabilidad por cliente de cada modelo en exp/modelos/. Según el README se corre dos veces, con el set 1 y con el set 2.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–18] Celda de texto de presentación: requiere los notebooks 0 y 1; genera 20 semillas a
#   partir de 370003, toma un set de hiperparámetros de la optimización, entrena un backtest (202103 y 202104,
#   predice 202106) y los modelos finales (202103 a 202106, predice 202108) y arma tablas con una columna por
#   semilla y el promedio. Indica que cada modelo guarda su predicción en exp/modelos/ y que los ya hechos se
#   saltean al volver a correr. Menciona un 'notebook 3' de gráfico y corte; en el repositorio no hay un archivo
#   con ese nombre, sí 3b_corte_y_entrega_sets_combinados.ipynb.
#%% celda 1 [texto]
# 2 · Modelos con muchas semillas + ensemble

**Antes:** tienen que estar corridos el notebook 0 y el notebook 1
(alcanza con que la BO tenga al menos 1 iteración hecha).

**Qué hace:**
1. A partir de la semilla primigenia **370003** genera **20 semillas** al azar (se cambia fácil en `PARAM$cantidad_semillas`)
2. Toma el **mejor set** de hiperparámetros de la BO (o el segundo, con `PARAM$set_hiperparametros <- 2`)
3. **Backtest** (para el gráfico de ganancia): entrena con las primeras semillas en 202103 + 202104 y predice **202106**,
   que tiene clase
4. **Modelos finales:** entrena un LightGBM por semilla en **202103–202106** (sin undersampling) y predice **202108**
5. Arma las tablas de probabilidades: **una columna por semilla + `prob_ensemble`** (promedio simple)

Cada modelo guarda su predicción en `exp/modelos/`. **Si se corta, volvé a correr todo:** los modelos ya hechos se saltean.
Si después subís la cantidad de semillas, las primeras siguen siendo las mismas y no se vuelven a entrenar.

El notebook 3 (gráfico y corte) se puede abrir **mientras este sigue corriendo**: usa los modelos que ya estén.

# [Anotación · líneas 20–41] Imprime la fecha y hora, limpia la memoria y carga data.table, R.utils, fst y
#   lightgbm, instalando los que falten. Imprime la cantidad de núcleos.
#%% celda 2 [texto]
### Librerías

#%% celda 3 [código]
format(Sys.time(), "%a %b %d %X %Y")

# limpio la memoria
rm(list=ls(all.names=TRUE))
gc(full=TRUE, verbose=FALSE)

# cargo las librerias (la primera vez se instalan y tarda varios minutos)
options(repos= c(CRAN= "https://cloud.r-project.org"))
options(width= 200)

for (paquete in c("data.table", "R.utils", "fst", "lightgbm")) {
  if (!require(paquete, character.only= TRUE)) {
    install.packages(paquete)
    library(paquete, character.only= TRUE)
  }
}

cat("Nucleos disponibles:", parallel::detectCores(), "\n")

# [Anotación · líneas 43–69] Define PARAM: semilla primigenia 370003, 20 semillas, set de hiperparámetros a
#   usar (el archivo quedó guardado con el valor 2; el comentario indica que se corre primero con 1 y después
#   con 2), meses de entrenamiento de los modelos finales (202103, 202104, 202105 y 202106), mes a predecir
#   (202108), meses del backtest (entrena en 202103 y 202104, predice 202106) y 5 semillas para el backtest.
#   Detiene la ejecución si falta el dataset preprocesado o exp/mejores_hiperparametros.txt.
#%% celda 4 [texto]
### Parámetros  ✏️

#%% celda 5 [código]
PARAM <- list()

PARAM$archivo_dataset <- "datos/dataset_preprocesado.fst"

# ✏️ semillas: se generan al azar a partir de la primigenia
PARAM$semilla_primigenia <- 370003
PARAM$cantidad_semillas  <- 20

# ✏️ que set de hiperparametros de la BO uso: 1 = el mejor, 2 = el segundo
PARAM$set_hiperparametros <- 2 # HAGO CON 1 Y DESPUES VUELVO A CORRER NOTEBOOK CON 2

# Modelos finales: training y mes a predecir
PARAM$final_train <- c(202103, 202104, 202105, 202106)
PARAM$future      <- c(202108)

# ✏️ Backtest para el grafico de ganancia: training, mes con clase, y con cuantas semillas
#    (con 5 semillas el promedio ya es estable y tarda bastante menos; para usar todas, poner 20)
PARAM$backtest_train    <- c(202103, 202104)
PARAM$backtest_test     <- c(202106)
PARAM$semillas_backtest <- 5

for (archivo in c(PARAM$archivo_dataset, "exp/mejores_hiperparametros.txt"))
  if (!file.exists(archivo)) stop("No existe ", archivo, ". Faltan correr los notebooks anteriores")

# [Anotación · líneas 71–107] Lista de hiperparámetros fijos de LightGBM, idéntica a la del notebook 1 (líneas
#   67 a 99): objective binary, max_bin 31, min_data_in_leaf 0, feature_fraction 0.50, feature_fraction_bynode
#   0.20, learning_rate 0.005, bagging_fraction 1.0, lambda_l1 y lambda_l2 en 0, max_depth -1, y use_missing,
#   force_row_wise y deterministic en TRUE.
#%% celda 6 [código]
# Hiperparametros FIJOS de LightGBM:
# Este bloque tiene que ser IGUAL en los notebooks 1 y 2

PARAM$lgbm$param_fijos <- list(
  boosting=           "gbdt",
  objective=          "binary",
  metric=             "auc",
  first_metric_only=  FALSE,
  boost_from_average= TRUE,
  feature_pre_filter= FALSE,
  force_row_wise=     TRUE,
  deterministic=      TRUE,
  verbosity=          -100,

  max_depth=          -1L,
  min_gain_to_split=  0,
  lambda_l1=          0,
  lambda_l2=          0,
  bagging_fraction=   1.0,       # sin bagging
  is_unbalance=       FALSE,
  scale_pos_weight=   1.0,
  extra_trees=        FALSE,
  use_missing=        TRUE,      # para que LightGBM entienda los NA

  # ---- fijos ----
  max_bin=                 31L,
  min_data_in_leaf=        0L,
  feature_fraction=        0.50,
  feature_fraction_bynode= 0.20,
  learning_rate=           0.005,

  # ---- estos tres los elige la BO (aca solo hay un valor por defecto) ----
  num_iterations=          1000L,
  num_leaves=              64L,
  min_sum_hessian_in_leaf= 0.001
)

# [Anotación · líneas 109–132] Genera las semillas con set.seed(370003) y sample(100000:999999, 20). Lee
#   exp/mejores_hiperparametros.txt, toma la fila del set elegido y guarda sus num_iterations, num_leaves y
#   min_sum_hessian_in_leaf. Arma el nombre del set (set1 o set2), que se usa como parte del nombre de los
#   archivos, y crea exp/modelos.
#%% celda 7 [texto]
### Semillas e hiperparámetros

#%% celda 8 [código]
# genero las semillas a partir de la primigenia
set.seed(PARAM$semilla_primigenia)
PARAM$semillas <- sample(100000:999999, PARAM$cantidad_semillas)
cat("Semillas:", PARAM$semillas, "\n\n")

# el set de hiperparametros elegido de la BO
mejores <- fread("exp/mejores_hiperparametros.txt")
hiper <- mejores[set == PARAM$set_hiperparametros]
if (nrow(hiper) == 0) stop("No existe el set ", PARAM$set_hiperparametros)

PARAM$hiperparametros_BO <- list(
  num_iterations=          hiper$num_iterations,
  num_leaves=              hiper$num_leaves,
  min_sum_hessian_in_leaf= hiper$min_sum_hessian_in_leaf
)
print(hiper)

# nombre que identifica al set en los archivos (por si despues se usa el otro set)
nombre_set <- paste0("set", PARAM$set_hiperparametros)
dir.create("exp/modelos", showWarnings= FALSE, recursive= TRUE)

# [Anotación · líneas 134–177] Define las mismas funciones auxiliares que el notebook 1: avisar,
#   mostrar_avance (avance cada 250 árboles), leer_meses, calcular_auc y calcular_ganancias. Las dos últimas no
#   se llaman en el resto de este notebook.
#%% celda 9 [texto]
### Funciones

#%% celda 10 [código]
# escribe un mensaje con la hora
avisar <- function(...) {
  cat(format(Sys.time(), "%H:%M:%S"), " ", ..., "\n", sep= "")
  flush.console()
}

# muestra el avance de LightGBM mientras entrena (cada 250 arboles)
mostrar_avance <- function(env) {
  if (env$iteration %% 250 == 0 || env$iteration == env$end_iteration) {
    cat("      ", format(Sys.time(), "%H:%M:%S"),
      "  arbol ", env$iteration, " de ", env$end_iteration, "\n", sep= "")
    flush.console()
  }
}
attr(mostrar_avance, "call") <- quote(mostrar_avance())
attr(mostrar_avance, "name") <- "mostrar_avance"

# lee del dataset preprocesado solo los meses pedidos
# (el archivo esta ordenado por foto_mes, asi no se carga todo en memoria)
leer_meses <- function(meses) {
  foto_mes <- read_fst(PARAM$archivo_dataset, columns= "foto_mes")$foto_mes
  filas <- which(foto_mes %in% meses)
  dt <- read_fst(PARAM$archivo_dataset, from= min(filas), to= max(filas),
    as.data.table= TRUE)
  dt[foto_mes %in% meses]
}

# AUC (area bajo la curva ROC), calculado a partir de los rankings
calcular_auc <- function(clase, prob) {
  rango <- frank(prob)
  n1 <- sum(clase == 1)
  n0 <- sum(clase == 0)
  (sum(rango[clase == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0)
}

# ganancia si le envio estimulo a los primeros N clientes (para cada N de cortes)
calcular_ganancias <- function(prob, gan, cortes) {
  acumulada <- cumsum(gan[order(-prob)])
  acumulada[cortes]
}

# [Anotación · líneas 179–205] preparar_training lee los meses pedidos, arma la etiqueta binaria (1 si
#   clase_ternaria es BAJA+1 o BAJA+2), deja como variables todas las columnas menos foto_mes y clase_ternaria y
#   construye el lgb.Dataset con todas las filas, pasándole los hiperparámetros fijos. preparar_scoring
#   devuelve, para el mes a predecir, los numero_de_cliente y la matriz con las mismas columnas.
#%% celda 11 [código]
# arma el lgb.Dataset de training con los meses pedidos (todos los registros)
preparar_training <- function(meses) {
  dt <- leer_meses(meses)
  clase <- ifelse(dt$clase_ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)
  campos <- setdiff(colnames(dt), c("foto_mes", "clase_ternaria"))
  dt[, setdiff(colnames(dt), campos) := NULL]     # dejo solo las variables
  matriz <- data.matrix(dt)
  rm(dt)
  gc(full=TRUE, verbose=FALSE)

  dtrain <- lgb.Dataset(data= matriz, label= clase,
    params= PARAM$lgbm$param_fijos, free_raw_data= TRUE)
  lgb.Dataset.construct(dtrain)
  rm(matriz)
  gc(full=TRUE, verbose=FALSE)
  avisar("Training con ", paste(meses, collapse= ", "), ": ", nrow(dtrain), " registros")
  dtrain
}

# arma la matriz del mes a predecir
preparar_scoring <- function(meses) {
  dt <- leer_meses(meses)
  campos <- setdiff(colnames(dt), c("foto_mes", "clase_ternaria"))
  list(numero_de_cliente= dt$numero_de_cliente,
       matriz= data.matrix(dt[, campos, with= FALSE]))
}

# [Anotación · líneas 207–235] entrenar_semillas recorre las semillas: si ya existe
#   exp/modelos/<prefijo>_s<semilla>.txt la saltea; si no, combina los hiperparámetros fijos con los del set,
#   fija seed en la semilla, entrena con lgb.train, predice el mes de scoring y escribe un archivo separado por
#   tabulaciones con numero_de_cliente y prob. Informa los minutos de cada modelo y libera memoria.
# entrena un LightGBM por semilla y guarda la prediccion de cada uno
entrenar_semillas <- function(semillas, dtrain, scoring, prefijo) {
  for (k in seq_along(semillas)) {
    semilla <- semillas[k]
    archivo <- paste0("exp/modelos/", prefijo, "_s", semilla, ".txt")

    if (file.exists(archivo)) {
      avisar("Semilla ", semilla, " (", k, " de ", length(semillas), ") ya estaba hecha")
      next
    }

    t0 <- Sys.time()
    avisar("Semilla ", semilla, " (", k, " de ", length(semillas), ")  entrenando")

    param <- modifyList(PARAM$lgbm$param_fijos, PARAM$hiperparametros_BO)
    param$seed <- semilla

    modelo <- lgb.train(data= dtrain, param= param, callbacks= list(mostrar_avance))

    pred <- data.table(numero_de_cliente= scoring$numero_de_cliente,
      prob= predict(modelo, scoring$matriz))
    fwrite(pred, archivo, sep= "\t")

    avisar("   listo en ",
      round(as.numeric(difftime(Sys.time(), t0, units= "mins")), 1), " min")
    rm(modelo)
    gc(full=TRUE, verbose=FALSE)
  }
}

# [Anotación · líneas 237–256] armar_tabla lee los archivos de exp/modelos que coinciden con un patrón, los
#   ordena por numero_de_cliente, verifica que todos tengan los mismos clientes y arma una tabla con una columna
#   prob_s<semilla> por modelo y la columna prob_ensemble con el promedio de esas columnas (rowMeans).
# junta las predicciones de cada semilla en una tabla: una columna por semilla
# y una columna prob_ensemble con el promedio simple
armar_tabla <- function(patron) {
  archivos <- sort(list.files("exp/modelos", pattern= patron, full.names= TRUE))
  if (length(archivos) == 0) return(NULL)

  tabla <- NULL
  for (archivo in archivos) {
    pred <- fread(archivo)
    setorder(pred, numero_de_cliente)
    semilla <- sub(".*_s([0-9]+)\\.txt$", "\\1", archivo)
    if (is.null(tabla)) tabla <- pred[, list(numero_de_cliente)]
    stopifnot(identical(tabla$numero_de_cliente, pred$numero_de_cliente))
    tabla[, paste0("prob_s", semilla) := pred$prob]
  }

  columnas <- grep("^prob_s", names(tabla), value= TRUE)
  tabla[, prob_ensemble := rowMeans(.SD), .SDcols= columnas]
  tabla
}

# [Anotación · líneas 258–276] Backtest: toma las primeras 5 semillas y, si falta alguno de sus archivos
#   backtest_<set>_s<semilla>.txt, entrena en 202103 y 202104 y predice 202106. Según la salida guardada
#   (corrida con el set 2), el entrenamiento tiene 326.184 registros y cada modelo tarda cerca de 11 minutos.
#%% celda 12 [texto]
## Backtest: entreno en 202103 + 202104 y predigo 202106  ⏳

Sirve para el gráfico de ganancia vs. envíos del notebook 3 (202106 tiene clase; 202108 no).

#%% celda 13 [código]
semillas_bt <- PARAM$semillas[1:min(PARAM$semillas_backtest, length(PARAM$semillas))]
prefijo_bt  <- paste0("backtest_", nombre_set)

faltan <- !file.exists(paste0("exp/modelos/", prefijo_bt, "_s", semillas_bt, ".txt"))
if (any(faltan)) {
  dtrain_bt  <- preparar_training(PARAM$backtest_train)
  scoring_bt <- preparar_scoring(PARAM$backtest_test)
  entrenar_semillas(semillas_bt, dtrain_bt, scoring_bt, prefijo_bt)
  rm(dtrain_bt, scoring_bt)
  gc(full=TRUE, verbose=FALSE)
} else {
  avisar("El backtest ya estaba hecho")
}

# [Anotación · líneas 278–295] Modelos finales: si falta alguno de los 20 archivos final_<set>_s<semilla>.txt,
#   entrena en 202103, 202104, 202105 y 202106 y predice 202108, un modelo por semilla. Según la salida guardada
#   (set 2), el entrenamiento tiene 654.066 registros y cada modelo tarda cerca de 22 minutos.
#%% celda 14 [texto]
## Modelos finales: entreno en 202103–202106 y predigo 202108  ⏳

Esta es la parte más larga.

#%% celda 15 [código]
prefijo_final <- paste0("final_", nombre_set)

faltan <- !file.exists(paste0("exp/modelos/", prefijo_final, "_s", PARAM$semillas, ".txt"))
if (any(faltan)) {
  dtrain_final  <- preparar_training(PARAM$final_train)
  scoring_final <- preparar_scoring(PARAM$future)
  entrenar_semillas(PARAM$semillas, dtrain_final, scoring_final, prefijo_final)
  rm(dtrain_final, scoring_final)
  gc(full=TRUE, verbose=FALSE)
} else {
  avisar("Los modelos finales ya estaban hechos")
}

# [Anotación · líneas 297–317] Arma la tabla de los modelos finales del set y la escribe en
#   exp/probabilidades_202108_<set>.csv; arma la del backtest, le agrega la clase_ternaria de 202106 y la
#   escribe en exp/probabilidades_202106_backtest_<set>.csv. Imprime cuántos modelos hay en cada tabla (20 y 5
#   según la salida guardada) y las primeras filas. La última celda imprime la fecha y hora.
#%% celda 16 [texto]
## Tablas de probabilidades

* `exp/probabilidades_202108_set1.csv`: una columna por semilla y `prob_ensemble` (promedio simple)
* `exp/probabilidades_202106_backtest_set1.csv`: lo mismo para el backtest, con la `clase_ternaria`

#%% celda 17 [código]
tabla_final <- armar_tabla(paste0("^", prefijo_final, "_s"))
fwrite(tabla_final, paste0("exp/probabilidades_202108_", nombre_set, ".csv"))

tabla_bt <- armar_tabla(paste0("^", prefijo_bt, "_s"))
clases <- leer_meses(PARAM$backtest_test)[, list(numero_de_cliente, clase_ternaria)]
tabla_bt[clases, on= "numero_de_cliente", clase_ternaria := i.clase_ternaria]
fwrite(tabla_bt, paste0("exp/probabilidades_202106_backtest_", nombre_set, ".csv"))

cat("Modelos finales en el ensemble:", sum(grepl("^prob_s", names(tabla_final))), "\n")
cat("Modelos del backtest:", sum(grepl("^prob_s", names(tabla_bt))), "\n\n")
head(tabla_final)

#%% celda 18 [código]
format(Sys.time(), "%a %b %d %X %Y")
```


## Explicaciones del alumno (texto original)

### README.md

> # Competencia 01 · DMEyF 2026
>
> Predicción de los clientes que se van a dar de baja (BAJA+2) en **202108**, para una campaña de retención.
>
> **Entrega final:** Los **11.750** clientes con mayor probabilidad según un **ensemble de 40 LightGBM**.
>
> ![Pipeline](pipeline.png)
>
> ---
>
> ## Resumen del modelo
>
> | Etapa | Qué se hace |
> |---|---|
> | **Clase** | Clase ternaria (BAJA+1, BAJA+2, CONTINUA) calculada con los meses siguientes. El modelo es binario: positivos = BAJA+1 y BAJA+2 |
> | **Data quality** | `ccajas_depositos` está rota en 202105 (todos ceros), así que se pone `NA` en ese mes |
> | **Data drifting** | Se eliminan `cprestamos_personales` y `mprestamos_personales` |
> | **Feature engineering** | Lags y delta lags de orden 1 y 2 de todas las variables (`_lag1`, `_lag2`, `_delta1`, `_delta2`) |
> | **Ranking por mes** | Para cada variable y cada mes por separado, ranking con cero fijo: positivos equiespaciados en (0, 1], negativos en [−1, 0), el 0 queda en 0 y los NA quedan NA. Reemplaza a los valores originales, incluidos lags y deltas. No se transforman `numero_de_cliente`, `foto_mes` ni `clase_ternaria` |
> | **Variables del modelo** | Todas las transformadas y `numero_de_cliente` (no se usa `foto_mes`) |
> | **Hiperparámetros fijos** | `max_bin` 31, `min_data_in_leaf` 0, `feature_fraction` 0.5, `feature_fraction_bynode` 0.2, `learning_rate` 0.005, sin bagging, `use_missing` TRUE |
> | **Bayesian Optimization** | Optimiza `num_iterations` (64–4096), `num_leaves` (16–2048) y `min_sum_hessian_in_leaf` (1e-6–1). Métrica AUC. Training 202103 + 202104 completo (sin undersampling), testing 202106. 10 iteraciones, semilla 370003. Se guardan los **2 mejores sets** |
> | **Modelos finales** | 20 semillas generadas a partir de 370003. Con cada set y cada semilla se entrena un LightGBM en **202103–202106** completo (sin undersampling) y se predice **202108**: 2 sets × 20 semillas = **40 modelos** |
> | **Ensemble** | Promedio simple de las probabilidades de los 40 modelos, por `numero_de_cliente` |
> | **Corte** | Se envía estímulo a los **11.750** clientes con mayor probabilidad. Se eligió con la curva de ganancia de un backtest (mismos sets y semillas, entrenados en 202103 + 202104 y aplicados a 202106) y con la ganancia pública de varios cortes |
>
> **Los 2 sets de hiperparámetros** (de `exp/mejores_hiperparametros.txt`):
>
> | Set | num_iterations | num_leaves | min_sum_hessian_in_leaf | AUC en 202106 |
> |---|---|---|---|---|
> | 1 | 3172 | 943 | 0.02584 | 0.92043 |
> | 2 | 2033 | 1874 | 0.08125 | 0.91990 |
>
> **Las 20 semillas** (generadas con `set.seed(370003); sample(100000:999999, 20)`):
> 195361, 236655, 403489, 450862, 490646, 520928, 547247, 593810, 598549, 623217,
> 674659, 697241, 805062, 907503, 943042, 944552, 962589, 967354, 976901, 991514
>
> ---
>
> ## Contenido del repositorio
>
> ```
> .
> ├── README.md
> ├── pipeline.png                                  diagrama del proceso
> ├── 0_preprocesamiento.ipynb                      clase, data quality, drifting, lags y ranking por mes
> ├── 1_optimizacion_bayesiana.ipynb                BO (10 iteraciones, semilla 370003)
> ├── 2_modelos_semillas.ipynb                      backtest + modelos finales de un set (se corre 2 veces)
> ├── 3b_corte_y_entrega_sets_combinados.ipynb      ensemble de los 40 modelos, curva de ganancia y archivo final
> ├── datos/                                        acá el notebook 0 deja el dataset preprocesado (no se sube)
> └── exp/                                          resultados intermedios ("checkpoints")
>     ├── BO/BO_log.txt                             las 10 iteraciones de la BO
>     ├── mejores_hiperparametros.txt               los 2 mejores sets
>     ├── modelos/                                  probabilidad de cada cliente, una por modelo:
>     │     final_set{1,2}_s{semilla}.txt             40 modelos finales (202108)
>     │     backtest_set{1,2}_s{semilla}.txt          10 modelos del backtest (202106)
>     ├── ganancia_vs_envios_sets12.png             curva de ganancia del backtest
>     └── entregas/resumen_10102129.txt             resumen de la entrega final
> ```
>
> Los notebooks se suben **con las salidas de la corrida original**, para que se vea lo que se ejecutó.
>
> ---
>
> ## Requisitos
>
> - **Jupyter (JupyterLab) con kernel de R** (IRkernel). Se corrió en una VM de Google Cloud con **12 vCPU**.
> - **Paquetes de R:** se instalan solos la primera vez que se corre cada notebook:
>   `data.table`, `R.utils`, `fst`, `lightgbm`, `bbotk`, `mlr3`, `mlr3mbo`, `mlr3learners`, `DiceKriging` y `ggplot2`.
> - **⚠️ El dataset va en la carpeta de arriba del repositorio**, porque los notebooks lo leen de
>   `../competencia_01_crudo.csv`:
>
> Cada notebook se abre en JupyterLab desde la carpeta del repositorio y se corre con **Run → Run All Cells**.
>
> ---
>
> ## Cómo reproducir la entrega
>
> Hay tres formas, según desde dónde se quiera partir. Todas terminan en el mismo archivo.
>
> ### Opción A · Desde los modelos ya entrenados (el más rapido)
>
> Usa las predicciones de los 40 modelos que están en `exp/modelos/`.
>
> 1. `0_preprocesamiento.ipynb` (~3 min). Genera `datos/dataset_preprocesado.fst`. El notebook 3b lo usa
>    para la clase de 202106 del backtest.
> 2. `3b_corte_y_entrega_sets_combinados.ipynb`. Ya tiene fijado el corte (`CORTES <- c(11750)`).
>
> El archivo de submit queda en `exp/entregas/v3_sets12_40mod_c11750_<fecha-hora>.csv`. El nombre cambia por la
> fecha y la hora, pero el contenido es idéntico al entregado: los mismos 11.750 clientes, en el mismo orden.
>
> ### Opción B · Reentrenando los modelos con los hiperparámetros de la BO (~17 horas)
>
> Usa los 2 sets de `exp/mejores_hiperparametros.txt`.
>
> 1. Borrar la carpeta `exp/modelos/` (si no, el notebook 2 encuentra los modelos y no los vuelve a entrenar).
> 2. `0_preprocesamiento.ipynb` (~3 min).
> 3. `2_modelos_semillas.ipynb` con `PARAM$set_hiperparametros <- 1` (~8 h: 5 modelos de backtest de ~11 min
>    y 20 finales de ~22 min).
> 4. `2_modelos_semillas.ipynb` otra vez, con `PARAM$set_hiperparametros <- 2` (~8 h).
> 5. `3b_corte_y_entrega_sets_combinados.ipynb`.
>
> ### Opción C · Desde cero (~18 horas)
>
> 1. Borrar `exp/BO/`, `exp/mejores_hiperparametros.txt` y `exp/modelos/`.
> 2. `0_preprocesamiento.ipynb` (~3 min).
> 3. `1_optimizacion_bayesiana.ipynb` (~75 min).
> 4. Seguir desde el paso 3 de la opción B.
>
> **Notas sobre la reproducibilidad:**
> - Todo usa semillas fijas, y LightGBM corre con `deterministic = TRUE` y `force_row_wise = TRUE`.
> - El notebook 2 quedó guardado con `PARAM$set_hiperparametros <- 2` porque fue la última corrida
>   (primero se corrió con 1 y después con 2, como en la opción B).
> - Si una corrida se corta, se vuelve a correr el mismo notebook y sigue desde donde quedó.
>   La BO retoma desde `exp/BO/BO_log.txt`, y el notebook 2 saltea los modelos que ya están en `exp/modelos/`.

### exp/entregas/resumen_10102129.txt

> RESUMEN DE LA ENTREGA   2026-10-10 21:29
>
> Ensemble: promedio simple de 40 LightGBM
> Set 1: 20 modelos.  num_iterations = 3172, num_leaves = 943, min_sum_hessian_in_leaf = 0.02584
>    semillas: 195361, 236655, 403489, 450862, 490646, 520928, 547247, 593810, 598549, 623217, 674659, 697241, 805062, 907503, 943042, 944552, 962589, 967354, 976901, 991514
> Set 2: 20 modelos.  num_iterations = 2033, num_leaves = 1874, min_sum_hessian_in_leaf = 0.08125
>    semillas: 195361, 236655, 403489, 450862, 490646, 520928, 547247, 593810, 598549, 623217, 674659, 697241, 805062, 907503, 943042, 944552, 962589, 967354, 976901, 991514
> Fijos: max_bin 31, min_data_in_leaf 0, feature_fraction 0.5, feature_fraction_bynode 0.2, learning_rate 0.005
>
> Ganancia en el backtest 202106 (todos juntos, 10 modelos):
>    11750 envios: 456.8 millones
>    maximo solo set 1: 462.8 millones con 11852 envios
>    maximo solo set 2: 464.6 millones con 10746 envios
>    maximo todos juntos: 461.7 millones con 10530 envios
>
> Mensaje para el bot:  submit    v3sets12c11750t10102129
> Archivos:
>    v3_sets12_40mod_c11750_10102129.csv   ->  ganancia del bot: 

