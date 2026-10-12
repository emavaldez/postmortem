# AgustinLovrich — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: agustinlovrich
- Repositorio: https://github.com/agustinlovrich/dmeyf-primera-competencia
- Link posteado: https://github.com/agustinlovrich/dmeyf-primera-competencia
- Commit: 6ef281f4f90978ee8e033f3e6acf3c7eeb89c29c
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/agustinlovrich/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/agustinlovrich.json

## Resumen

La entrega contiene un único script en R (run_rank_prestamos_junbo_hist.R, 518 líneas), un README general, tres README de carpeta, los hiperparámetros y las evaluaciones de la optimización bayesiana con el log de la corrida, y el archivo de predicción con su hash SHA-256. El script lee el crudo de la competencia, calcula clase_ternaria si no viene, pasa ccajas_depositos a NA en 202105 y reemplaza cada una de las 152 variables por su rango con signo dentro del mes (cero fijo). Sobre esos rangos calcula lag 1, lag 2, delta 1, delta 2, y tendencia y promedio de una ventana de 3 meses con una función C++ (Rcpp): 7 columnas por variable, 1064 en total; los valores crudos se descartan. Una optimización bayesiana con mlrMBO (AUC, entrena en 202103+202104, valida en 202106, sin las columnas de préstamos personales) busca num_iterations, num_leaves y min_sum_hessian_in_leaf. Con esos valores (1439, 256 y 0.0299943) entrena 40 modelos LightGBM de clase binaria (BAJA+1 o BAJA+2) en 202103-202106, sin submuestreo y con las columnas de préstamos incluidas, promedia las probabilidades sobre 202108 y escribe un archivo por corte de 9000 a 13000. Según el README, se entregó el corte de 11000 y el puntaje público de ese archivo fue 107.44.

**Qué entrega.** prediccion_final/lovrich_ensamble_corte11000.csv: 11000 líneas, un numero_de_cliente por línea y sin encabezado. Según el README, son los 11000 clientes de mayor probabilidad promedio del ensamble de 40 semillas para 202108 y es el archivo subido al bot. El script lo genera como entrega/corte_11000/lovrich_ensamble.csv dentro de la carpeta de salida.

**Cómo se ejecuta.** El README indica dos opciones, cada una con un único comando. Opción A (completa, incluye la optimización bayesiana; unos 125 minutos de optimización según el README): DMEYF_CRUDO=data/competencia_01_crudo.csv DMEYF_EXP=salida_run GCS_BUCKET= NTHREAD=8 NSEEDS=40 Rscript run_rank_prestamos_junbo_hist.R. Opción B: antes de ese mismo comando, crear salida_run y copiar optimizacion_bayesiana/bo_mejor_config.csv a salida_run/bo_mejor_config.csv, con lo que el script no repite la optimización. GCS_BUCKET vacío desactiva la subida a Google Cloud Storage. El crudo no está en el repositorio y se coloca en data/competencia_01_crudo.csv. La entrega queda en salida_run/entrega/corte_11000/lovrich_ensamble.csv.

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase01): 1 si clase_ternaria es BAJA+1 o BAJA+2, 0 en el resto (línea 227). Si el crudo no trae clase_ternaria, el script la calcula por cliente y mes calendario (líneas 203-216). No se usan pesos por fila ni por clase.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica: el parámetro us vale 1.0 (línea 134), con lo que la condición azar <= us de la línea 311 deja pasar todas las filas CONTINUA de 202103-202106. La optimización bayesiana y el modelo de 202106 usan todas las filas de 202103 y 202104 (líneas 312 y 419).
- **Calidad de datos:** ccajas_depositos se pasa a NA en 202105 antes de cualquier transformación (líneas 222-226). El script se detiene si el crudo tiene columnas de texto distintas de clase_ternaria, si falta alguno de los meses 202103 a 202108, si hay más de una fila por cliente y mes o si algún mes de entrenamiento queda sin clase. Compara la cantidad de positivos de 202103-202105 con el valor 6083 y sólo avisa si difiere.
- **Drifting:** Normalización por rango con signo, por variable y dentro de cada mes, para las 152 variables base (líneas 241-256): NA queda NA; cero queda cero; los valores positivos se reemplazan por su rango (empates al promedio) dividido por la cantidad de positivos del mes, en (0,1]; los negativos, por menos el rango de su valor absoluto dividido por la cantidad de negativos, en [-1,0). Los valores crudos se eliminan del dataset (línea 296). No hay deflación.
- **Variables dentro del mes:** No se observa en el código: no se crean sumas, cocientes ni combinaciones entre variables del mismo mes. Cada variable base se reemplaza por su columna normalizada (_rank).
- **Variables históricas:** Todas se calculan sobre las columnas _rank de las 152 variables. Lag 1 y lag 2: valor del mismo cliente uno y dos meses calendario atrás, NA si ese mes no está (líneas 264-277). Delta 1 y delta 2: valor del mes menos cada lag. Tendencia (_rank_tend3): pendiente por mínimos cuadrados sobre las últimas 3 filas del cliente. Promedio (_rank_avg3): media de los valores no NA de esa ventana. Tendencia y promedio quedan en NA cuando la ventana tiene menos de dos valores no NA; se calculan con una función C++ compilada con Rcpp (líneas 49-118 y 286-289). Total: 7 columnas por variable, 1064.
- **Selección de variables:** No hay selección por importancia. Quedan fuera del modelo numero_de_cliente, foto_mes, clase_ternaria y clase01. Las 14 columnas derivadas de cprestamos_personales y mprestamos_personales se excluyen de la optimización bayesiana y del modelo de 202106 (1050 columnas, feats_bo) y se incluyen en el entrenamiento final (1064 columnas, feats_all).
- **Optimización de hiperparámetros:** Optimización bayesiana con mlrMBO dentro del mismo script (líneas 341-403): modelo sustituto Kriging (regr.km, covarianza matern3_2), criterio Expected Improvement, diseño inicial de 10 puntos por hipercubo latino maximin, hasta 30 iteraciones o 120 minutos. Espacio: num_iterations en [600, 3500], num_leaves en [16, 256], min_sum_hessian_in_leaf en [0.0001, 0.03]. Cada punto entrena en 202103+202104 con una semilla (la primera del lote) y se mide por AUC en 202106, sin validación cruzada y sin las columnas de préstamos. Se guarda el punto que mbo devuelve como resultado. Si bo_mejor_config.csv ya existe en la carpeta de salida, la optimización no se repite. Según bo_evaluaciones.csv y junbo_hist.log, la corrida incluida evaluó 24 puntos en 125.2 minutos y el punto guardado es el de mayor AUC (0.91907).
- **Hiperparámetros finales:** De la optimización (optimizacion_bayesiana/bo_mejor_config.csv): num_leaves = 256, min_sum_hessian_in_leaf = 0.0299943000368938, num_iterations = 1439. Fijos en el código (líneas 146-150): objective = binary, metric = auc, boosting = gbdt, boost_from_average = TRUE, feature_pre_filter = FALSE, force_row_wise = TRUE, deterministic = TRUE, max_bin = 31, min_data_in_leaf = 0, feature_fraction = 0.50, feature_fraction_bynode = 0.20, learning_rate = 0.005.
- **Semillas:** 40 (variable de entorno NSEEDS, 40 por defecto). Se obtienen con una criba de primos entre 100000 y 1000000, set.seed(100193) y un sorteo de 50; se usan las primeras 40. Las primeras 20 se comparan con una lista escrita en el código y el script se detiene si no coinciden (líneas 172-181). La optimización bayesiana usa la primera semilla; la curva de 202106, las primeras 10.
- **Cantidad de semillas:** 40
- **Ensamble:** Promedio aritmético de las probabilidades de los 40 modelos LightGBM, que comparten datos e hiperparámetros y difieren en la semilla (línea 479).
- **Corte:** Cantidad fija: los 11000 clientes de mayor probabilidad promedio. El script escribe archivos para 9 cortes, de 9000 a 13000 con paso 500, tanto del ensamble como de cada semilla (líneas 486-493). Según el README, el corte de 11000 se elige porque la ganancia media entre semillas en 202106 tiene su máximo en ese corte (454.96 millones) y porque coincide con lo observado en el leaderboard público.
- **Validación:** Un mes posterior: se entrena en 202103+202104 y se mide en 202106. La optimización bayesiana mide AUC (calculado con el estadístico de Mann-Whitney) y registra además la ganancia. El modelo de junio, con 10 semillas y 1050 columnas, produce una curva de ganancia por corte (1.072.500 por cada BAJA+2 enviado y -27.500 por cualquier otro envío): media y desvío entre semillas y ganancia del promedio de probabilidades. No hay validación cruzada ni conjunto de prueba aparte.
- **Salidas:** En la carpeta de salida (DMEYF_EXP): bo_mejor_config.csv y bo_evaluaciones.csv; curva_junio_junbo_hist.csv y .png; modelos/prob_s<semilla>.csv con la probabilidad por cliente de cada semilla; predicciones_202108_junbo_hist.csv con la probabilidad promedio ordenada; entrega/corte_<k>/lovrich_s<semilla>.csv y lovrich_ensamble.csv, con un numero_de_cliente por línea y sin encabezado (369 archivos según el log). El repositorio incluye prediccion_final/lovrich_ensamble_corte11000.csv (11000 líneas) y su SHA-256.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)

## Técnicas sólo exploradas

- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README: R 4.6.1, lightgbm 4.7.0, data.table y Rcpp, con un compilador de C++ (Rtools en Windows, build-essential en Linux); para la optimización bayesiana, DiceKriging, mlrMBO, smoof, lhs y ParamHelpers, que el script instala si faltan. El log incluido registra R 4.6.1 (2026-06-24), lightgbm 4.7.0, data.table 1.18.6.1 y 8 hilos. No se declara máquina ni sistema operativo. Las rutas del crudo y de la salida se pasan por variables de entorno y son relativas; el valor por defecto de GCS_BUCKET es un bucket de Google Cloud Storage escrito en el código (línea 127), que se usa sólo para la subida opcional de resultados.

## Pasos del camino de la entrega

1. **Parámetros de la corrida.** La lista PRM fija la semilla primigenia 100193, las rutas y recursos que se leen de variables de entorno (DMEYF_CRUDO, DMEYF_EXP, GCS_BUCKET, NTHREAD, NSEEDS), los meses (entrenamiento final 202103-202106, predicción 202108, optimización en 202103+202104 con validación en 202106), us = 1.0, las dos variables de préstamos personales, los cortes de 9000 a 13000 con paso 500, los hiperparámetros fijos de LightGBM y los rangos y el presupuesto de la optimización bayesiana. (`run_rank_prestamos_junbo_hist.R` líneas 123–157)
2. **Generación de las semillas.** Con una criba se obtienen los primos entre 100000 y 1000000; con set.seed(100193) se sortean 50 y se usan los primeros 40 (NSEEDS). Los primeros 20 se comparan con una lista escrita en el código y el script se detiene si no coinciden. (`run_rank_prestamos_junbo_hist.R` líneas 172–182)
3. **Lectura del crudo y controles.** Lee el CSV con fread. Se detiene si hay columnas de texto distintas de clase_ternaria o si falta alguno de los meses 202103 a 202108. Según junbo_hist.log, el crudo de la corrida incluida tiene 983061 filas y 155 columnas. (`run_rank_prestamos_junbo_hist.R` líneas 189–197)
4. **Clase ternaria.** Si el crudo no la trae, se calcula por cliente y mes calendario: BAJA+1 si el cliente no aparece al mes siguiente, BAJA+2 si aparece al mes siguiente y no a los dos meses, CONTINUA en el resto; sólo en los meses que tienen dos meses posteriores en el dataset. El script se detiene si un mes de entrenamiento queda sin clase. (`run_rank_prestamos_junbo_hist.R` líneas 203–217)
5. **Corrección de ccajas_depositos y clase binaria.** ccajas_depositos se pasa a NA en 202105. Se crea clase01 = 1 para BAJA+1 y BAJA+2 y 0 para el resto. La cantidad de positivos de 202103-202105 se compara con 6083 y, si difiere, se imprime un aviso. (`run_rank_prestamos_junbo_hist.R` líneas 222–231)
6. **Normalización por rango con signo dentro de cada mes.** Cada variable base se transforma dentro de cada foto_mes: NA queda NA, cero queda cero, los positivos pasan a su rango dividido por la cantidad de positivos (intervalo (0,1]) y los negativos a menos el rango de su valor absoluto dividido por la cantidad de negativos (intervalo [-1,0)). El resultado se guarda en columnas <variable>_rank. (`run_rank_prestamos_junbo_hist.R` líneas 241–257)
7. **Lags y deltas sobre los rangos.** Para cada variable, sobre su columna _rank, se toma el valor del mismo cliente un mes y dos meses calendario antes (_lag1, _lag2; NA si ese mes no está) y la diferencia del valor del mes con cada uno (_delta1, _delta2). (`run_rank_prestamos_junbo_hist.R` líneas 264–280)
8. **Tendencia y promedio de 3 meses.** Con el dataset ordenado por cliente y mes, agrega_historico calcula para cada columna _rank la pendiente por mínimos cuadrados (_rank_tend3) y el promedio (_rank_avg3) sobre las últimas 3 filas del cliente, usando la función C++ fhistC compilada con Rcpp. Con menos de dos valores no NA en la ventana, ambos quedan en NA. Según el README, el núcleo C++ es de la cátedra. (`run_rank_prestamos_junbo_hist.R` líneas 49–118; `run_rank_prestamos_junbo_hist.R` líneas 286–291)
9. **Descarte de los valores crudos y listas de columnas.** Se eliminan las variables base sin transformar. feats_all reúne las 7 columnas por variable (1064 según el log) y feats_bo es la misma lista sin las 14 columnas de cprestamos_personales y mprestamos_personales (1050). (`run_rank_prestamos_junbo_hist.R` líneas 296–304)
10. **Selección de filas y matrices.** Se definen las filas de entrenamiento final (202103-202106 con clase; con us = 1.0 no se descarta ninguna), de entrenamiento y validación de la optimización (202103+202104 y 202106) y de predicción (202108), con sus etiquetas. Según el log: 326184 filas con 4074 positivos para la optimización, 164114 filas con 1098 BAJA+2 en 202106 y 654066 filas en el entrenamiento final. (`run_rank_prestamos_junbo_hist.R` líneas 309–327)
11. **Optimización bayesiana de tres hiperparámetros.** Si no existe bo_mejor_config.csv en la carpeta de salida, mlrMBO busca num_iterations (600-3500), num_leaves (16-256) y min_sum_hessian_in_leaf (0.0001-0.03): 10 puntos iniciales por hipercubo latino maximin y hasta 30 iteraciones o 120 minutos con Kriging y Expected Improvement. Cada punto entrena un LightGBM en 202103+202104 con feats_bo y la primera semilla, y devuelve el AUC en 202106; la ganancia se registra en bo_evaluaciones.csv sin intervenir en la elección. Si la optimización está desactivada o termina con error se usa una configuración de respaldo (44, 0.0068328532, 1920). El archivo incluido en el repositorio tiene 256, 0.0299943000368938 y 1439. (`run_rank_prestamos_junbo_hist.R` líneas 332–411)
12. **Curva de ganancia en 202106.** Con los hiperparámetros leídos se entrenan 10 modelos (las primeras 10 semillas) en 202103+202104 con feats_bo y se predice 202106. Para cada corte de 9000 a 13000 se calcula la ganancia de cada semilla (1.072.500 por BAJA+2, -27.500 por el resto), su media y desvío, y la ganancia del promedio de probabilidades. Se guarda en curva_junio_junbo_hist.csv y en un gráfico PNG. (`run_rank_prestamos_junbo_hist.R` líneas 418–450)
13. **Entrenamiento final con 40 semillas.** Se entrena un LightGBM por semilla en 202103-202106 con las 1064 columnas de feats_all (incluidas las de préstamos), los hiperparámetros fijos y los tres de la optimización, y se predice 202108. La probabilidad de cada semilla se guarda en modelos/prob_s<semilla>.csv; si el archivo ya existe, se lee en lugar de reentrenar. (`run_rank_prestamos_junbo_hist.R` líneas 456–474)
14. **Promedio de probabilidades y archivos por corte.** Se promedian las probabilidades de las 40 semillas por cliente y se ordena de mayor a menor. Para cada uno de los 9 cortes se escribe un archivo con los k clientes de mayor probabilidad promedio (lovrich_ensamble.csv) y uno por cada semilla, con un numero_de_cliente por línea y sin encabezado. (`run_rank_prestamos_junbo_hist.R` líneas 479–494)
15. **Validación de formato y subida opcional.** Cada CSV de la carpeta entrega se verifica: entre 8000 y 13000 líneas, sólo dígitos, sin repetidos y con clientes de 202108; si alguno no cumple, el script se detiene. Si GCS_BUCKET no está vacío, la carpeta entrega y el archivo de predicciones se copian a un bucket con gcloud storage. (`run_rank_prestamos_junbo_hist.R` líneas 499–518)
16. **Elección del corte entregado.** Según el README, de los archivos generados se entrega el del ensamble con corte 11000 (entrega/corte_11000/lovrich_ensamble.csv, copiado como prediccion_final/lovrich_ensamble_corte11000.csv), porque la ganancia media entre semillas en 202106 tiene su máximo en ese corte (454.96 millones) y porque el leaderboard público también muestra el valor más alto en 11000 (107.44 para el ensamble). (`README.md` líneas 148–180; `prediccion_final/README.md` líneas 5–12)

## Archivos

- `README.md` · explicacion · Markdown · 205 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinlovrich/README.md.txt) — Presentación de la entrega: estructura del repositorio, requisitos (R 4.6.1, lightgbm 4.7.0, Rcpp y compilador de C++), dos formas de ejecución (con la optimización bayesiana o reutilizando bo_mejor_config.csv), los 13 pasos del flujo, una tabla de decisiones, la justificación del corte de 11000 con la curva de ganancia en 202106 y con puntajes públicos, y una lista de seis experimentos descartados. Según el README, el ensamble de 40 semillas con corte 11000 obtuvo 107.44 en el leaderboard público y la misma receta sin tendencia ni promedio de 3 meses, 104.50. La tabla de ganancia en 202106 tiene los mismos valores que junbo_hist.log imprime para el modelo de junio de 10 semillas.
- `run_rank_prestamos_junbo_hist.R` · principal · R · 518 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinlovrich/run_rank_prestamos_junbo_hist.R.txt) — Script único que va del crudo a los archivos de envío: clase, corrección de ccajas_depositos, normalización por rango con signo, lags, deltas, tendencia y promedio de 3 meses, optimización bayesiana, curva de ganancia en 202106, entrenamiento de 40 semillas, promedio y archivos por corte.
- `optimizacion_bayesiana/README.md` · explicacion · Markdown · 73 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinlovrich/optimizacion_bayesiana/README.md.txt) — Explica cómo se obtuvieron los hiperparámetros (mlrMBO con Kriging y Expected Improvement, 10 puntos iniciales, hasta 30 iteraciones o 120 minutos, entrenando en 202103+202104 y validando en 202106 por AUC), qué contiene cada archivo de la carpeta y cómo copiar bo_mejor_config.csv a la carpeta de salida para que el script no repita la optimización. Señala que el valor elegido de num_leaves (256) coincide con el tope del rango de búsqueda y que min_sum_hessian_in_leaf (0.0299943) queda cerca del tope 0.03.
- `prediccion_final/SHA256.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinlovrich/prediccion_final/SHA256.txt.txt) — Una línea con el hash SHA-256 de lovrich_ensamble_corte11000.csv, en el formato que lee sha256sum -c.
- `prediccion_final/README.md` · explicacion · Markdown · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinlovrich/prediccion_final/README.md.txt) — Indica que lovrich_ensamble_corte11000.csv es el archivo subido al bot, que corresponde a entrega/corte_11000/lovrich_ensamble.csv del script (un numero_de_cliente por línea, sin encabezado, 11000 clientes) y cómo comprobar su hash SHA-256 en Linux, macOS y Windows.
- `data/README.md` · explicacion · Markdown · 22 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinlovrich/data/README.md.txt) — Indica que el crudo competencia_01_crudo.csv no está en el repositorio, que se coloca en esta carpeta y se pasa al script con la variable de entorno DMEYF_CRUDO, y que tiene que contener los meses 202103 a 202108 con todas las columnas numéricas salvo clase_ternaria.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### run_rank_prestamos_junbo_hist.R

Script único que va del crudo a los archivos de envío: clase, corrección de ccajas_depositos, normalización por rango con signo, lags, deltas, tendencia y promedio de 3 meses, optimización bayesiana, curva de ganancia en 202106, entrenamiento de 40 semillas, promedio y archivos por corte.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–39] Encabezado en comentarios del autor: resume el flujo del script (lectura, clase,
#   corrección de ccajas_depositos, normalización por rango, lags y deltas, tendencia y promedio de 3 meses,
#   optimización bayesiana sin los préstamos, entrenamiento final con 40 semillas, curva de junio, promedio y
#   cortes), enumera los criterios y decisiones declarados e indica el modo de uso y los paquetes requeridos.
#!/usr/bin/env Rscript
# =====================================================================================
#  run_rank_prestamos_junbo_hist.R  —  = junbo + FE HISTORICO (tendencia y promedio de 3 meses
#                           sobre los rankings). Pipeline de normalizacion por rango + semillerio,
#                           BO de rangos AMPLIOS (num_leaves hasta 256, hessiano desde 0.0001).
#                           La foto de junio se arma SIN los prestamos (feats_bo); el final SI los usa.
#                           7 features por variable (rank, lag1, delta1, lag2, delta2, rank_tend3, rank_avg3).
# -------------------------------------------------------------------------------------
#  Normalizacion por rango con signo + exclusion de los prestamos de la BO (reincorporados al final).
# -------------------------------------------------------------------------------------
#  QUE HACE, de punta a punta y en UN solo script autocontenido y reproducible:
#    - Lee el crudo, arma clase_ternaria y clase01.
#    - dq1: ccajas_depositos = NA solo en 202105.
#    - Normaliza por rango con signo (por variable y por mes) + retrovisores/diferencias 1 y 2
#      + FE historico sobre los rankings (tendencia y promedio de 3 meses: rank_tend3, rank_avg3).
#      Descarta los valores crudos: al arbol solo le llegan columnas transformadas.
#    - BO (mlrMBO, AUC, train 202103+04 -> valida 202106, sin CV, us=1) SIN los 2 prestamos
#      -> busca num_iterations, num_leaves, min_sum_hessian_in_leaf.
#    - Reincorpora las columnas de los 2 prestamos y entrena el modelo FINAL (202103-06)
#      con los hiperparametros de la BO, 40 semillas (primigenia 100193), sin undersampling.
#    - FOTO EN JUNIO: modelo train 03+04 -> predice 202106 (con feats_bo, sin prestamos),
#      curva de ganancia por corte (media/desvio, 10 semillas) para elegir el corte.
#    - Promedia probabilidades, barre cortes y valida formato.
#
#  CRITERIOS DE METODOLOGIA:
#    - BO SIEMPRE sin undersampling (desacoplada del us final).   - BO con 1 semilla (la primera del lote).
#    - Prestamos fuera de la BO y reincorporados al final.        - Semillerio final de 40 semillas.
#    - El corte se decide mirando la curva + la foto de junio.
#    NO se hace: normalizar tambien los retrovisores, ni ensamble-de-ensambles dentro de este script.
#
#  DECISIONES PROPIAS:
#    - Semilla primigenia 100193 (metodo catedra: criba de primos 1e5..1e6, set.seed, sample).
#    - us = 1.0 (sin undersampling) en BO y en el train final.
#    - Las columnas de los 2 prestamos NO entran a la BO pero SI al train final.
#    - Retrovisores CALENDARIO-exactos: mismo cliente en periodo-1 / periodo-2 (NA si falta el mes).
#
#  Uso:   NTHREAD=8 DMEYF_CRUDO=~/crudo.csv Rscript run_rank_prestamos_junbo_hist.R > junbo_hist.log 2>&1
#  Requiere: data.table, lightgbm y (para la BO) DiceKriging + mlrMBO + smoof + lhs + ParamHelpers.
# =====================================================================================
# [Anotación · líneas 40–43] Carga data.table, lightgbm y Rcpp, desactiva la notación científica y define
#   set_env_int, que lee una variable de entorno como entero y usa un valor por defecto si está vacía.
suppressMessages({ library(data.table); library(lightgbm); library(Rcpp) })
options(scipen = 999)
set_env_int <- function(name, def){ v <- Sys.getenv(name); if (nzchar(v)) as.integer(v) else as.integer(def) }

# [Anotación · líneas 44–103] Define con Rcpp la función C++ fhistC. Recibe una columna y, para cada fila, la
#   posición donde empieza su ventana. Reúne los valores no NA de la ventana con su posición (1, 2, 3...) y, si
#   hay más de uno, calcula la pendiente por mínimos cuadrados, el mínimo, el máximo y el promedio; con uno o
#   ninguno deja NA en los cuatro. Guarda además el valor de la fila anterior cuando la ventana empieza antes de
#   la fila. Devuelve un vector de largo 5n con los cinco resultados uno a continuación del otro.
# -------------------------------------------------------------------------------------
#  FE HISTORICO (ventana): tendencia (pendiente por minimos cuadrados) y promedio sobre
#  los ultimos `ventana` registros de cada cliente. Nucleo en C++ por velocidad.
#  Requiere que el dataset este ordenado por (numero_de_cliente, foto_mes).
# -------------------------------------------------------------------------------------
cppFunction("NumericVector fhistC(NumericVector pcolumna, IntegerVector pdesde )
{
  double  x[100] ;
  double  y[100] ;
  int n = pcolumna.size();
  NumericVector out( 5*n );
  for(int i = 0; i < n; i++)
  {
    if( pdesde[i]-1 < i )  out[ i + 4*n ]  =  pcolumna[i-1] ;
    else                   out[ i + 4*n ]  =  NA_REAL ;
    int  libre    = 0 ;
    int  xvalor   = 1 ;
    for( int j= pdesde[i]-1;  j<=i; j++ )
    {
       double a = pcolumna[j] ;
       if( !R_IsNA( a ) )
       {
          y[ libre ]= a ;
          x[ libre ]= xvalor ;
          libre++ ;
       }
       xvalor++ ;
    }
    if( libre > 1 )
    {
      double  xsum  = x[0] ;
      double  ysum  = y[0] ;
      double  xysum = xsum * ysum ;
      double  xxsum = xsum * xsum ;
      double  vmin  = y[0] ;
      double  vmax  = y[0] ;
      for( int h=1; h<libre; h++)
      {
        xsum  += x[h] ;
        ysum  += y[h] ;
        xysum += x[h]*y[h] ;
        xxsum += x[h]*x[h] ;
        if( y[h] < vmin )  vmin = y[h] ;
        if( y[h] > vmax )  vmax = y[h] ;
      }
      out[ i ]  =  (libre*xysum - xsum*ysum)/(libre*xxsum -xsum*xsum) ;
      out[ i + n ]    =  vmin ;
      out[ i + 2*n ]  =  vmax ;
      out[ i + 3*n ]  =  ysum / libre ;
    }
    else
    {
      out[ i       ]  =  NA_REAL ;
      out[ i + n   ]  =  NA_REAL ;
      out[ i + 2*n ]  =  NA_REAL ;
      out[ i + 3*n ]  =  NA_REAL ;
    }
  }
  return  out;
}")
# [Anotación · líneas 104–118] agrega_historico arma, para cada fila, el inicio de su ventana: dos filas antes
#   con ventana = 3, la propia fila cuando cambia el numero_de_cliente, y nunca anterior al inicio de la fila
#   previa, de modo que la ventana no incluye filas de otro cliente. Para cada columna llama a fhistC y agrega
#   al dataset <columna>_tend3 (el tramo de pendientes) y <columna>_avg3 (el tramo de promedios); mínimo, máximo
#   y valor anterior no se usan.

# agrega <col>_tend<ventana> y/o <col>_avg<ventana> para cada col (dataset ordenado por cliente, mes)
agrega_historico <- function(dataset, cols, ventana = 3L, tendencia = TRUE, promedio = TRUE){
  last <- nrow(dataset)
  vector_ids   <- dataset[["numero_de_cliente"]]
  vector_desde <- seq(-ventana + 2L, last - ventana + 1L)
  vector_desde[seq_len(ventana)] <- 1L
  for (i in 2:last) if (vector_ids[i - 1L] != vector_ids[i]) vector_desde[i] <- i
  for (i in 2:last) if (vector_desde[i] < vector_desde[i - 1L]) vector_desde[i] <- vector_desde[i - 1L]
  for (campo in cols) {
    nc <- fhistC(dataset[[campo]], vector_desde)
    if (tendencia) set(dataset, j = paste0(campo, "_tend", ventana), value = nc[(0L*last + 1L):(1L*last)])
    if (promedio)  set(dataset, j = paste0(campo, "_avg",  ventana), value = nc[(3L*last + 1L):(4L*last)])
  }
}
# [Anotación · líneas 119–143] Lista PRM con los parámetros: semilla primigenia 100193; ruta del crudo
#   (DMEYF_CRUDO, por defecto crudo.csv), carpeta de salida (DMEYF_EXP) y bucket (GCS_BUCKET, por defecto un
#   bucket gs:// escrito en el código); hilos (NTHREAD) y cantidad de semillas (NSEEDS, 40). Meses:
#   entrenamiento final 202103 a 202106, predicción 202108, optimización entrenando en 202103+202104 y validando
#   en 202106. us = 1.0, las dos variables de préstamos personales, ccajas_depositos y 202105 para la
#   corrección, corte de referencia 11000, cortes de 9000 a 13000 con paso 500 y 10 semillas para el modelo de
#   junio.

# -------------------------------------------------------------------------------------
#  PARAMETROS (todo lo que define el experimento vive aca)
# -------------------------------------------------------------------------------------
PRM <- list()
PRM$primigenia   <- 100193L
PRM$crudo        <- Sys.getenv("DMEYF_CRUDO", unset = "crudo.csv")
PRM$salida       <- Sys.getenv("DMEYF_EXP",   unset = "exp_rank_prestamos_junbo_hist")
PRM$bucket       <- Sys.getenv("GCS_BUCKET",  unset = "gs://agustin_lovrich_buckito2026")
PRM$nthread      <- set_env_int("NTHREAD", parallel::detectCores())
PRM$nseeds       <- set_env_int("NSEEDS", 40L)         # 40 semillas para la prediccion final (pool de 50; se usan las primeras NSEEDS)
PRM$meses_train  <- c(202103L, 202104L, 202105L, 202106L)   # entrenamiento final
PRM$mes_futuro   <- 202108L                                  # mes a predecir
PRM$bo_train     <- c(202103L, 202104L)                      # BO: entrena
PRM$bo_valid     <- 202106L                                  # BO: valida (sin CV)
PRM$us           <- 1.0                                      # undersampling CONTINUA (1 = ninguno)
PRM$prestamos    <- c("cprestamos_personales", "mprestamos_personales")  # se sacan antes de la BO
PRM$dq_campo     <- "ccajas_depositos"
PRM$dq_mes       <- 202105L
PRM$k_modelo     <- 11000L
PRM$cortes       <- seq(9000L, 13000L, by = 500L)
# para elegir el corte, observar ademas los ENVIOS OPTIMOS EN JUNIO (mes 6, etiquetado)
PRM$junio_train  <- c(202103L, 202104L)   # modelo de testeo: entrena 03+04
PRM$junio_test   <- 202106L               # predice 202106 (tiene clase) -> curva de ganancia
PRM$junio_nseeds <- 10L                   # 10 semillas para la curva de junio (diagnostico)
# [Anotación · líneas 144–157] Hiperparámetros fijos de LightGBM: objective binary, metric auc, boosting gbdt,
#   max_bin 31, min_data_in_leaf 0, feature_fraction 0.50, feature_fraction_bynode 0.20, learning_rate 0.005,
#   deterministic y force_row_wise en TRUE. Configuración de la optimización bayesiana: 10 puntos de diseño, 30
#   iteraciones, tope de 120 minutos, num_iterations entre 600 y 3500, num_leaves entre 16 y 256,
#   min_sum_hessian_in_leaf entre 0.0001 y 0.03. Configuración de respaldo: num_leaves 44,
#   min_sum_hessian_in_leaf 0.0068328532, num_iterations 1920.

# hiperparametros FIJOS de LightGBM (quedan congelados; la BO solo mueve los otros 3)
PRM$fijos <- list(objective = "binary", metric = "auc", boosting = "gbdt",
  boost_from_average = TRUE, feature_pre_filter = FALSE, force_row_wise = TRUE,
  deterministic = TRUE, num_threads = PRM$nthread,          # reproducibilidad + usa NTHREAD
  verbosity = -100L, max_bin = 31L, min_data_in_leaf = 0L,
  feature_fraction = 0.50, feature_fraction_bynode = 0.20, learning_rate = 0.005)

# BO: rangos de los 3 bayesianos + presupuesto
PRM$bo <- list(activar = TRUE, diseno = 10L, iteraciones = 30L, tope_min = 120,
  iter_min = 600L, iter_max = 3500L, hojas_min = 16L, hojas_max = 256L,   # tope alto de hojas: habilita arboles profundos
  hess_min = 0.0001, hess_max = 0.03)                                     # piso bajo de hessiano: habilita hojas chicas
# config de respaldo si la BO falla (valores profundos razonables)
PRM$respaldo <- list(num_leaves = 44L, min_sum_hessian_in_leaf = 0.0068328532, num_iterations = 1920L)
# [Anotación · líneas 158–167] Valores de control esperados: 6083 positivos en 202103-202105, 150 variables y
#   1050 columnas en la optimización, 1064 columnas en el entrenamiento final. Imprime la cantidad de hilos, la
#   de semillas y el valor de us, y las versiones de R, lightgbm y data.table.

# anclas de control (aproximadas: avisan, no frenan salvo la clase)
PRM$ancla_npos_03_05 <- 6083L     # positivos 202103-05 VERIFICADO en competencia_01. Solo AVISA.
PRM$ancla_vars_bo    <- 150L      # 152 base - 2 prestamos
PRM$ancla_cols_bo    <- 1050L     # 150 x 7 (rank, lag1, delta1, lag2, delta2, rank_tend3, rank_avg3)
PRM$ancla_cols_final <- 1064L     # 152 x 7

cat(sprintf("== rank_prestamos == nthread=%d nseeds=%d us=%.2f ==\n", PRM$nthread, PRM$nseeds, PRM$us))
cat("R:", R.version.string, "| lightgbm", as.character(packageVersion("lightgbm")),
    "| data.table", as.character(packageVersion("data.table")), "\n")
# [Anotación · líneas 168–184] Genera los números primos entre 100000 y 1000000 con una criba, fija
#   set.seed(100193) y sortea 50. Compara los primeros 20 con una lista escrita en el código y se detiene si no
#   coinciden o si NSEEDS supera 50. SEMILLAS queda con los primeros NSEEDS valores. Crea la carpeta de salida.

# -------------------------------------------------------------------------------------
#  SEMILLAS (metodo catedra con la primigenia 100193) + verificacion
# -------------------------------------------------------------------------------------
primos_en_rango <- function(a, b){ x <- rep(TRUE, b); x[1] <- FALSE
  for (i in 2:floor(sqrt(b))) if (x[i]) x[seq(i*i, b, by = i)] <- FALSE
  p <- which(x); p[p >= a] }
set.seed(PRM$primigenia)
semillas_pool <- sample(primos_en_rango(100000L, 1000000L), 50L)   # 50 semillas via criba + muestreo con la primigenia
ctrl_semillas <- c(467473L,754373L,564671L,248189L,373721L,437243L,905161L,391619L,289841L,961159L,
                   670639L,635021L,850207L,975433L,740939L,723103L,889519L,161599L,535219L,373193L)
if (!all(semillas_pool[seq_len(20L)] == ctrl_semillas)) stop("el sorteo de semillas (primigenia 100193) NO es reproducible: reviso antes de seguir")
if (PRM$nseeds > 50L) stop("NSEEDS > 50: ampliar el pool de semillas")
SEMILLAS <- semillas_pool[seq_len(PRM$nseeds)]
cat("semillas:", paste(SEMILLAS, collapse = " "), "\n")

dir.create(PRM$salida, showWarnings = FALSE, recursive = TRUE)
# [Anotación · líneas 185–197] Lee el crudo con fread e imprime filas y columnas. Se detiene si no encuentra
#   el archivo, si hay columnas de texto distintas de clase_ternaria o si falta alguno de los meses 202103 a
#   202108.

# -------------------------------------------------------------------------------------
#  1) LECTURA DEL CRUDO + controles
# -------------------------------------------------------------------------------------
if (!file.exists(PRM$crudo)) stop("no encuentro el crudo en: ", PRM$crudo)
cat("leyendo", PRM$crudo, "...\n"); ds <- fread(PRM$crudo)
cat("filas:", nrow(ds), "| columnas:", ncol(ds), "\n")
chr <- names(ds)[vapply(ds, is.character, logical(1))]
chr <- setdiff(chr, "clase_ternaria")
if (length(chr) > 0) stop("hay columnas de texto en el crudo: ", paste(chr, collapse = ", "))
# control de meses: 202107 hace falta para los lags de 202108 y la clase de 202106
faltan <- setdiff(c(202103L,202104L,202105L,202106L,202107L,202108L), unique(ds$foto_mes))
if (length(faltan) > 0) stop("faltan meses en el crudo: ", paste(faltan, collapse = ", "))
# [Anotación · líneas 198–217] Si el crudo no trae clase_ternaria, la calcula: numera los meses como
#   año*12+mes, arma una clave cliente+mes y verifica si el cliente aparece al mes siguiente y a los dos meses.
#   En los meses con dos meses posteriores disponibles asigna CONTINUA (aparece en ambos), BAJA+2 (aparece en el
#   siguiente y no a los dos meses) o BAJA+1 (no aparece en el siguiente); el resto queda NA. Se detiene si
#   algún mes de entrenamiento tiene filas sin clase.

# -------------------------------------------------------------------------------------
#  2) CLASE_TERNARIA (por cliente y mes calendario)
#     BAJA+1: no esta el mes siguiente | BAJA+2: esta el siguiente pero no a +2 | CONTINUA: resto
# -------------------------------------------------------------------------------------
if (!"clase_ternaria" %in% names(ds)) {
  ds[, periodo := as.integer(foto_mes/100L)*12L + foto_mes %% 100L]
  cm_key <- as.numeric(ds$numero_de_cliente) * 1e5 + ds$periodo
  if (anyDuplicated(cm_key) > 0) stop("hay mas de una fila por cliente y mes")
  sigue1 <- (cm_key + 1) %in% cm_key       # el cliente reaparece al mes siguiente
  sigue2 <- (cm_key + 2) %in% cm_key       # el cliente reaparece dos meses despues
  pmax   <- max(ds$periodo)
  ds[, clase_ternaria := NA_character_]
  obs <- ds$periodo <= (pmax - 2L)        # solo donde el futuro es totalmente observable
  ds[obs &  sigue1 &  sigue2, clase_ternaria := "CONTINUA"]
  ds[obs &  sigue1 & !sigue2, clase_ternaria := "BAJA+2"]
  ds[obs & !sigue1,           clase_ternaria := "BAJA+1"]
  ds[, periodo := NULL]; rm(cm_key, sigue1, sigue2)
}
if (ds[foto_mes %in% PRM$meses_train & is.na(clase_ternaria), .N] > 0) stop("hay meses de train sin clase_ternaria")
# [Anotación · líneas 218–231] Pasa ccajas_depositos a NA en 202105 e imprime cuántos valores no NA quedan.
#   Crea clase01 = 1 cuando clase_ternaria es BAJA+1 o BAJA+2 y 0 en el resto. Cuenta los positivos de
#   202103-202105 y los compara con 6083; si difieren imprime un aviso y continúa.

# -------------------------------------------------------------------------------------
#  3) dq1 + clase01 + (se sacan los prestamos ANTES DE NADA)
# -------------------------------------------------------------------------------------
if (PRM$dq_campo %in% names(ds)) {
  ds[foto_mes == PRM$dq_mes, (PRM$dq_campo) := NA]
  cat("dq1:", PRM$dq_campo, "no-NA en", PRM$dq_mes, "=",
      ds[foto_mes == PRM$dq_mes, sum(!is.na(get(PRM$dq_campo)))], "(debe ser 0)\n")
}
ds[, clase01 := as.integer(clase_ternaria %in% c("BAJA+1", "BAJA+2"))]
npos <- ds[foto_mes %in% c(202103L,202104L,202105L) & clase01 == 1L, .N]
cat("npos 202103-05 =", npos, "| ancla =", PRM$ancla_npos_03_05,
    if (npos == PRM$ancla_npos_03_05) "-> OK\n" else "-> *** DIFIERE ***\n")
if (npos != PRM$ancla_npos_03_05) cat("*** AVISO: npos difiere del ancla", PRM$ancla_npos_03_05, "-> revisar el dato/clase antes de interpretar (no freno) ***\n")
# [Anotación · líneas 232–257] ranking_signado transforma un vector: NA queda NA, cero queda cero, los
#   positivos pasan a su rango (empates al promedio) dividido por la cantidad de positivos y los negativos a
#   menos el rango de su valor absoluto dividido por la cantidad de negativos. Las variables base son todas las
#   columnas salvo numero_de_cliente, foto_mes, clase_ternaria y clase01. Ordena por cliente y mes y aplica la
#   función a cada variable dentro de cada foto_mes, creando las columnas <variable>_rank.

# -------------------------------------------------------------------------------------
#  4) NORMALIZACION POR RANGO CON SIGNO (una variable, dentro de cada mes) -> columnas _rank
#     Mantiene el signo y deja el cero quieto: faltante -> faltante; cero -> cero;
#     los valores > 0 se mapean al intervalo (0,1] segun su posicion relativa, y los < 0
#     a [-1,0) segun la posicion de su modulo. Se aplica a las 152 variables base. Los 2
#     prestamos se normalizan igual, pero sus columnas no entran a la BO y recien se suman
#     al entrenamiento final (como la normalizacion es por variable, el numero no cambia).
# -------------------------------------------------------------------------------------
ranking_signado <- function(x){
  out  <- rep(NA_real_, length(x))
  hay  <- !is.na(x)
  out[hay & x == 0] <- 0
  pos <- hay & x > 0; if (any(pos)) out[pos] <-  frank(x[pos],  ties.method = "average") / sum(pos)
  neg <- hay & x < 0; if (any(neg)) out[neg] <- -frank(-x[neg], ties.method = "average") / sum(neg)
  out
}
no_feature <- c("numero_de_cliente", "foto_mes", "clase_ternaria", "clase01")
base_vars  <- setdiff(names(ds), no_feature)
cat("variables base:", length(base_vars), "(incluye los 2 prestamos)\n")

setorder(ds, numero_de_cliente, foto_mes)
cols_rk <- paste0(base_vars, "_rank")
cat("normalizando por rango, mes a mes...\n")
ds[, (cols_rk) := lapply(.SD, ranking_signado), by = foto_mes, .SDcols = base_vars]
gc()
# [Anotación · líneas 258–280] Calcula, para cada fila, la posición de la fila del mismo cliente un mes y dos
#   meses calendario antes (NA si no existe) mediante una clave cliente+mes. Para cada variable, sobre su
#   columna _rank, crea _lag1 y _lag2 (el valor en esas posiciones) y _delta1 y _delta2 (el valor del mes menos
#   cada lag). Cada 25 variables imprime el avance y libera memoria.

# -------------------------------------------------------------------------------------
#  5) RETROVISORES 1 y 2 y sus diferencias, sobre las columnas normalizadas
#     retro_k = el mismo cliente k meses atras en el calendario (faltante si ese mes no esta)
#     dif_k   = valor del mes - retro_k
# -------------------------------------------------------------------------------------
ds[, .periodo := as.integer(foto_mes/100L)*12L + foto_mes %% 100L]
cli_mes <- as.numeric(ds$numero_de_cliente) * 1e5 + ds$.periodo   # identificador cliente+mes, exacto bajo 2^53
if (anyDuplicated(cli_mes) > 0) stop("hay mas de una fila por cliente y mes (al calcular retrovisores)")
prev1 <- match(cli_mes - 1, cli_mes)     # posicion del mes inmediato anterior del mismo cliente
prev2 <- match(cli_mes - 2, cli_mes)     # posicion de dos meses atras
ds[, .periodo := NULL]; rm(cli_mes)

cat("retrovisores y diferencias...\n")
for (k in seq_along(base_vars)) {
  v  <- ds[[cols_rk[k]]]
  set(ds, j = paste0(base_vars[k], "_lag1"),   value = v[prev1])
  set(ds, j = paste0(base_vars[k], "_delta1"), value = v - v[prev1])
  set(ds, j = paste0(base_vars[k], "_lag2"),   value = v[prev2])
  set(ds, j = paste0(base_vars[k], "_delta2"), value = v - v[prev2])
  if (k %% 25L == 0L) { cat("  ", k, "/", length(base_vars), "\n"); invisible(gc(verbose = FALSE)) }
}
rm(prev1, prev2); gc()
# [Anotación · líneas 281–291] Reordena por cliente y mes, reserva espacio para las columnas nuevas y llama a
#   agrega_historico con ventana 3 sobre las columnas _rank: crea <variable>_rank_tend3 y <variable>_rank_avg3,
#   dos columnas por variable.

# -------------------------------------------------------------------------------------
#  5.5) FE HISTORICO: tendencia (pendiente 3 meses) y promedio (3 meses) sobre los rankings
#       -> columnas <var>_rank_tend3 y <var>_rank_avg3 (ventana posicional por cliente)
# -------------------------------------------------------------------------------------
setorder(ds, numero_de_cliente, foto_mes)   # fhistC usa ventana posicional: requiere orden cliente, mes
cat("FE historico (tend3 + avg3) sobre los rankings...\n")
invisible(data.table::setalloccol(ds, ncol(ds) + 2L * length(cols_rk) + 64L))   # pre-aloca slots: set() dentro de la funcion no puede crecer el DT
agrega_historico(ds, cols = cols_rk, ventana = 3L, tendencia = TRUE, promedio = TRUE)
cat("  columnas historicas creadas:", 2L * length(cols_rk), "\n")
invisible(gc(verbose = FALSE))
# [Anotación · líneas 292–304] Elimina las variables base sin transformar. Arma feats_all con las 7 columnas
#   por variable (_rank, _lag1, _delta1, _lag2, _delta2, _rank_tend3, _rank_avg3), feats_prest con las 14
#   columnas de cprestamos_personales y mprestamos_personales, y feats_bo como feats_all sin feats_prest.
#   Imprime las cantidades junto a los valores de control 1064 y 1050.

# -------------------------------------------------------------------------------------
#  6) Se descartan los valores crudos: al arbol solo le llegan las columnas transformadas.
# -------------------------------------------------------------------------------------
ds[, (base_vars) := NULL]
feats_all  <- c(paste0(base_vars,"_rank"), paste0(base_vars,"_lag1"), paste0(base_vars,"_delta1"),
                paste0(base_vars,"_lag2"), paste0(base_vars,"_delta2"),
                paste0(base_vars,"_rank_tend3"), paste0(base_vars,"_rank_avg3"))   # 7 por variable
feats_prest <- unlist(lapply(PRM$prestamos, function(v) paste0(v, c("_rank","_lag1","_delta1","_lag2","_delta2","_rank_tend3","_rank_avg3"))))
feats_bo   <- setdiff(feats_all, feats_prest)   # BO: SIN los 2 prestamos
stopifnot(all(feats_all %in% names(ds)))
cat(sprintf("features totales: %d (ancla ~%d) | features BO: %d (ancla %d)\n",
            length(feats_all), PRM$ancla_cols_final, length(feats_bo), PRM$ancla_cols_bo))
# [Anotación · líneas 305–327] Define los índices de filas: entrenamiento final (202103-202106 con clase; con
#   us = 1.0 entran todas), entrenamiento de la optimización (202103 y 202104), validación (202106) y predicción
#   (202108). Extrae las etiquetas clase01, la clase ternaria de 202106 y los numero_de_cliente de 202108, se
#   detiene si estos últimos se repiten y construye las matrices de la optimización con feats_bo.

# -------------------------------------------------------------------------------------
#  Seleccion de filas (undersampling us; con us=1 entran todos los CONTINUA)
# -------------------------------------------------------------------------------------
set.seed(PRM$primigenia); azar <- runif(nrow(ds))
es_pos <- ds$clase_ternaria %in% c("BAJA+1", "BAJA+2")
r_train <- which(ds$foto_mes %in% PRM$meses_train & !is.na(ds$clase_ternaria) & (azar <= PRM$us | es_pos))
r_boTr  <- which(ds$foto_mes %in% PRM$bo_train    & !is.na(ds$clase_ternaria))   # la BO SIEMPRE sin undersampling
r_boVa  <- which(ds$foto_mes == PRM$bo_valid)
r_fut   <- which(ds$foto_mes == PRM$mes_futuro)
rm(azar, es_pos)

y_train  <- ds$clase01[r_train]
y_boTr   <- ds$clase01[r_boTr]
y_boVa   <- ds$clase01[r_boVa]
cl_boVa  <- ds$clase_ternaria[r_boVa]
ids_fut  <- ds$numero_de_cliente[r_fut]
if (anyDuplicated(ids_fut) > 0) stop("hay numero_de_cliente repetidos en 202108")

mat_boTr <- as.matrix(ds[r_boTr, ..feats_bo])
mat_boVa <- as.matrix(ds[r_boVa, ..feats_bo])
cat(sprintf("BO: train %d filas (%d pos) -> valida %d (%d BAJA+2 reales)\n",
            length(r_boTr), sum(y_boTr), length(r_boVa), sum(cl_boVa == "BAJA+2")))
# [Anotación · líneas 328–339] Define las rutas de bo_mejor_config.csv y de bo_evaluaciones.csv, la función
#   auc_mw (AUC a partir de los rangos, estadístico de Mann-Whitney) y la función gan_corte, que suma 1.072.500
#   por cada BAJA+2 y -27.500 por cada otro cliente entre los k de mayor probabilidad.

# =====================================================================================
#  7) BAYESIAN OPTIMIZATION (mlrMBO, AUC, sin CV) -> num_iterations, num_leaves, hessiano
# =====================================================================================
f_cfg <- file.path(PRM$salida, "bo_mejor_config.csv")
auc_mw <- function(p, y){ rr <- frank(p, ties.method = "average")   # AUC via estadistico de Mann-Whitney
  n1 <- sum(y == 1L); n0 <- length(y) - n1
  (sum(rr[y == 1L]) - n1*(n1+1)/2) / (n1*n0) }
# ganancia: se LOGUEA junto al AUC en la BO (NO cambia la seleccion, que sigue por AUC). La usa tambien junio.
GANA_B2 <- 1072500; GANA_NO <- -27500
gan_corte <- function(prob, clase, k){ o <- order(-prob)[seq_len(k)]; sum(ifelse(clase[o] == "BAJA+2", GANA_B2, GANA_NO)) }
f_evals <- file.path(PRM$salida, "bo_evaluaciones.csv")
# [Anotación · líneas 340–375] Si bo_mejor_config.csv no existe en la carpeta de salida: con la optimización
#   desactivada escribe la configuración de respaldo; si no, instala los paquetes que falten, arma el
#   lgb.Dataset de 202103+202104 y define la función objetivo. Esta entrena un LightGBM con los hiperparámetros
#   fijos, los tres valores propuestos y la primera semilla, predice 202106, calcula el AUC, la ganancia al
#   corte 11000 y la mayor ganancia entre los cortes, agrega una fila a bo_evaluaciones.csv y devuelve el AUC.

if (!file.exists(f_cfg)) {
  if (!PRM$bo$activar) {
    fwrite(data.table(fuente = "respaldo_profundo", num_leaves = PRM$respaldo$num_leaves,
      min_sum_hessian_in_leaf = PRM$respaldo$min_sum_hessian_in_leaf,
      num_iterations = PRM$respaldo$num_iterations, auc = NA_real_), f_cfg)
  } else {
    ok <- tryCatch({
      for (pk in c("DiceKriging","mlrMBO","smoof","lhs","ParamHelpers")) {
        if (!requireNamespace(pk, quietly = TRUE)) install.packages(pk, repos = "https://cloud.r-project.org")
      }
      suppressMessages({ library(DiceKriging); library(mlrMBO); library(smoof) })
      dbo <- lgb.Dataset(mat_boTr, label = y_boTr, free_raw_data = FALSE,
        params = list(max_bin = PRM$fijos$max_bin, min_data_in_leaf = 0L, feature_pre_filter = FALSE, verbosity = -100L))
      t_bo <- Sys.time(); it <- 0L
      if (file.exists(f_evals)) invisible(file.remove(f_evals))   # log limpio para esta BO
      objetivo <- function(x){
        it <<- it + 1L; t0 <- Sys.time()
        pr <- PRM$fijos
        pr$num_leaves <- as.integer(x$num_leaves)
        pr$min_sum_hessian_in_leaf <- as.numeric(x$min_sum_hessian_in_leaf)
        pr$seed <- SEMILLAS[1]   # la BO corre con 1 semilla (la primera del lote)
        m  <- lgb.train(params = pr, data = dbo, nrounds = as.integer(x$num_iterations), verbose = -1L)
        pv <- predict(m, mat_boVa)
        a  <- auc_mw(pv, y_boVa)                                        # <- lo que OPTIMIZA la BO (sin cambios)
        g_ref  <- gan_corte(pv, cl_boVa, PRM$k_modelo) / 1e6           # ganancia INFORMATIVA al corte de referencia
        g_best <- max(sapply(PRM$cortes, function(k) gan_corte(pv, cl_boVa, k))) / 1e6   # mejor ganancia del barrido
        seg <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
        fwrite(data.table(iter = it, num_iterations = as.integer(x$num_iterations), num_leaves = pr$num_leaves,
                          min_sum_hessian_in_leaf = pr$min_sum_hessian_in_leaf, auc = a,
                          gan_ref = g_ref, gan_best = g_best, segundos = round(seg, 1)),
               f_evals, append = file.exists(f_evals), col.names = !file.exists(f_evals))
        cat(sprintf("[BO %d] hojas %d | hess %.5f | arb %d -> AUC %.5f | gan@%d %.1fM | gan_best %.1fM\n",
                    it, pr$num_leaves, pr$min_sum_hessian_in_leaf, as.integer(x$num_iterations), a, PRM$k_modelo, g_ref, g_best))
        rm(m); invisible(gc(verbose = FALSE)); a
      }
# [Anotación · líneas 376–403] Define el espacio de búsqueda (num_iterations, num_leaves,
#   min_sum_hessian_in_leaf), la función a maximizar, el control de mlrMBO (30 iteraciones o 120 minutos,
#   criterio Expected Improvement), el modelo sustituto regr.km con covarianza matern3_2 y un diseño inicial de
#   10 puntos por hipercubo latino maximin. Ejecuta mbo, escribe en bo_mejor_config.csv el punto que devuelve
#   como resultado con su AUC e imprime la correlación entre AUC y ganancia de las evaluaciones. Si la
#   optimización termina con error, escribe la configuración de respaldo. Si el archivo ya existía, no se
#   optimiza.
      espacio <- makeParamSet(
        makeIntegerParam("num_iterations",          lower = PRM$bo$iter_min, upper = PRM$bo$iter_max),
        makeIntegerParam("num_leaves",              lower = PRM$bo$hojas_min, upper = PRM$bo$hojas_max),
        makeNumericParam("min_sum_hessian_in_leaf", lower = PRM$bo$hess_min,  upper = PRM$bo$hess_max))
      fun <- makeSingleObjectiveFunction(fn = objetivo, par.set = espacio,
        minimize = FALSE, noisy = TRUE, has.simple.signature = FALSE)
      ctrl <- makeMBOControl()
      ctrl <- setMBOControlTermination(ctrl, iters = PRM$bo$iteraciones, time.budget = PRM$bo$tope_min * 60)
      ctrl <- setMBOControlInfill(ctrl, crit = makeMBOInfillCritEI())
      surr <- makeLearner("regr.km", predict.type = "se", covtype = "matern3_2", control = list(trace = FALSE))
      set.seed(SEMILLAS[1]); dis <- ParamHelpers::generateDesign(n = PRM$bo$diseno, par.set = espacio, fun = lhs::maximinLHS)
      cat("inicio BO:", format(Sys.time(), "%X"), "| tope", PRM$bo$tope_min, "min\n")
      set.seed(SEMILLAS[1]); res <- mbo(fun = fun, design = dis, learner = surr, control = ctrl)
      best <- res$x
      fwrite(data.table(fuente = "BO_AUC", num_leaves = as.integer(best$num_leaves),
        min_sum_hessian_in_leaf = as.numeric(best$min_sum_hessian_in_leaf),
        num_iterations = as.integer(best$num_iterations), auc = res$y), f_cfg)
      cat("BO lista en", round(as.numeric(difftime(Sys.time(), t_bo, units = "mins")),1), "min | mejor AUC", round(res$y,5), "\n")
      if (file.exists(f_evals)) { ev <- fread(f_evals)
        if (nrow(ev) >= 3L) cat(sprintf("** relacion AUC<->ganancia en la BO: cor(auc, gan_best) = %.3f (n=%d evals) | config elegida por AUC **\n",
                                        suppressWarnings(cor(ev$auc, ev$gan_best)), nrow(ev))) }
      rm(dbo); invisible(gc()); TRUE
    }, error = function(e){ cat("*** la BO fallo:", conditionMessage(e), "-> uso config de respaldo ***\n"); FALSE })
    if (!ok && !file.exists(f_cfg)) fwrite(data.table(fuente = "respaldo_BOfallo",
      num_leaves = PRM$respaldo$num_leaves, min_sum_hessian_in_leaf = PRM$respaldo$min_sum_hessian_in_leaf,
      num_iterations = PRM$respaldo$num_iterations, auc = NA_real_), f_cfg)
  }
} else cat("bo_mejor_config.csv ya existe: no repito la BO\n")
# [Anotación · líneas 404–411] Lee bo_mejor_config.csv, guarda en HIP los tres hiperparámetros (num_leaves,
#   min_sum_hessian_in_leaf, num_iterations), los imprime y libera las matrices de la optimización.

cfg <- fread(f_cfg)
HIP <- list(num_leaves = as.integer(cfg$num_leaves[1]),
            min_sum_hessian_in_leaf = as.numeric(cfg$min_sum_hessian_in_leaf[1]),
            num_iterations = as.integer(cfg$num_iterations[1]))
cat(sprintf("hiperparametros finales [%s]: hojas %d | hess %.8f | arboles %d\n",
            cfg$fuente[1], HIP$num_leaves, HIP$min_sum_hessian_in_leaf, HIP$num_iterations))
rm(mat_boTr, mat_boVa); gc()
# [Anotación · líneas 412–432] Modelo de junio: toma las primeras 10 semillas, entrena en 202103+202104 con
#   feats_bo (sin las columnas de préstamos) y los hiperparámetros de HIP, y guarda en la matriz Pjun la
#   probabilidad predicha para 202106 con cada semilla.

# =====================================================================================
#  7.5) ENVIOS OPTIMOS EN JUNIO: modelo de testeo, train 202103+04 -> predice 202106.
#       FOTO JUNIO con feats_bo (1050, SIN prestamos). El FINAL de 202108 sigue con feats_all (1064).
#       Da la curva de ganancia (media y desvio entre semillas) para ELEGIR el corte.
# =====================================================================================
sem_jun <- SEMILLAS[seq_len(min(PRM$junio_nseeds, PRM$nseeds))]   # GANA_B2/GANA_NO/gan_corte ya definidos arriba (BO)
r_junTr <- which(ds$foto_mes %in% PRM$junio_train & !is.na(ds$clase_ternaria))   # 03+04 sin US
r_junTe <- which(ds$foto_mes == PRM$junio_test)                                   # 202106
mat_junTr <- as.matrix(ds[r_junTr, ..feats_bo]); y_junTr <- ds$clase01[r_junTr]   # FOTO JUNIO: SIN prestamos (1050 feats)
mat_junTe <- as.matrix(ds[r_junTe, ..feats_bo]); cl_junTe <- ds$clase_ternaria[r_junTe]
djun <- lgb.Dataset(mat_junTr, label = y_junTr, free_raw_data = FALSE,
  params = list(max_bin = PRM$fijos$max_bin, min_data_in_leaf = 0L, feature_pre_filter = FALSE, verbosity = -100L))
Pjun <- matrix(0, nrow(mat_junTe), length(sem_jun))
cat("--- modelo de JUNIO (", length(sem_jun), "semillas) ---\n")
for (j in seq_along(sem_jun)) {
  pr <- c(PRM$fijos, list(num_leaves = HIP$num_leaves, min_sum_hessian_in_leaf = HIP$min_sum_hessian_in_leaf, seed = sem_jun[j]))
  m  <- lgb.train(params = pr, data = djun, nrounds = HIP$num_iterations, verbose = -1L)
  Pjun[, j] <- predict(m, mat_junTe)
  cat("  [junio] semilla", sem_jun[j], "ok (", j, "/", length(sem_jun), ")\n"); rm(m); invisible(gc(verbose = FALSE))
}
# [Anotación · líneas 433–450] Calcula la ganancia de cada semilla en cada corte y arma la tabla curva:
#   ganancia media, desvío entre semillas y ganancia del promedio de probabilidades, en millones. La escribe en
#   curva_junio_junbo_hist.csv, imprime el corte de mayor ganancia del promedio junto a la del corte 10500 y
#   guarda un gráfico PNG de la curva.
G <- sapply(PRM$cortes, function(k) sapply(seq_along(sem_jun), function(j) gan_corte(Pjun[, j], cl_junTe, k)))
curva <- data.table(corte = PRM$cortes,
  gan_media    = colMeans(G) / 1e6,
  gan_desvio   = (if (length(sem_jun) > 1) apply(G, 2, sd) else rep(0, length(PRM$cortes))) / 1e6,
  gan_ensamble = sapply(PRM$cortes, function(k) gan_corte(rowMeans(Pjun), cl_junTe, k)) / 1e6)
fwrite(curva, file.path(PRM$salida, "curva_junio_junbo_hist.csv"))
opt <- curva[which.max(gan_ensamble)]
cat("\n=== ENVIOS OPTIMOS EN JUNIO (202106) ===\n"); print(curva)
cat(sprintf("corte optimo (ensamble): %d -> %.1f M | referencia corte 10500: %.1f M\n",
            opt$corte, opt$gan_ensamble, curva[corte == 10500L, gan_ensamble]))
tryCatch({
  png(file.path(PRM$salida, "curva_junio_junbo_hist.png"), width = 1050, height = 650, res = 110)
  plot(curva$corte, curva$gan_ensamble, type = "o", pch = 19, lwd = 2, col = "#1f6feb",
       xlab = "corte (envios)", ylab = "ganancia junio (M $)", main = "Envios optimos en JUNIO (train 03+04 -> predice 06)")
  points(opt$corte, opt$gan_ensamble, col = "red", pch = 19, cex = 1.6)
  abline(v = 10500, lty = 3, col = "gray40"); grid(); dev.off()
}, error = function(e) cat("(no se pudo graficar junio:", conditionMessage(e), ")\n"))
rm(mat_junTr, mat_junTe, djun, Pjun); gc()
# [Anotación · líneas 451–474] Arma las matrices de entrenamiento final (202103-202106) y de 202108 con
#   feats_all, elimina el dataset de memoria y crea el lgb.Dataset. Para cada semilla: si ya existe
#   modelos/prob_s<semilla>.csv lo lee; si no, entrena un LightGBM con los hiperparámetros fijos, los de HIP y
#   esa semilla, predice 202108 y guarda las probabilidades en ese archivo.

# =====================================================================================
#  8-9) ENTRENAMIENTO FINAL (202103-06, 1064 features con prestamos reincorporados)
#       N semillas (NSEEDS, default 40), mismos hiperparametros, promedio de probabilidades.
# =====================================================================================
mat_train <- as.matrix(ds[r_train, ..feats_all])
mat_fut   <- as.matrix(ds[r_fut,   ..feats_all])
rm(ds); gc()
dtrain <- lgb.Dataset(mat_train, label = y_train, free_raw_data = FALSE,
  params = list(max_bin = PRM$fijos$max_bin, min_data_in_leaf = 0L, feature_pre_filter = FALSE, verbosity = -100L))
cat(sprintf("train final: %d filas, %d features (prestamos reincorporados)\n", nrow(mat_train), ncol(mat_train)))

dir_mod <- file.path(PRM$salida, "modelos"); dir.create(dir_mod, showWarnings = FALSE)
P <- matrix(0, length(ids_fut), length(SEMILLAS))
for (j in seq_along(SEMILLAS)) {
  s <- SEMILLAS[j]
  f_prob <- file.path(dir_mod, sprintf("prob_s%d.csv", s))
  if (file.exists(f_prob)) { P[, j] <- fread(f_prob)$prob; cat("  semilla", s, "ya estaba\n"); next }
  pr <- c(PRM$fijos, list(num_leaves = HIP$num_leaves, min_sum_hessian_in_leaf = HIP$min_sum_hessian_in_leaf, seed = s))
  m  <- lgb.train(params = pr, data = dtrain, nrounds = HIP$num_iterations, verbose = -1L)
  P[, j] <- predict(m, mat_fut)
  fwrite(data.table(numero_de_cliente = ids_fut, prob = P[, j]), f_prob)
  cat(sprintf("  semilla %d ok (%d/%d)\n", s, j, length(SEMILLAS))); rm(m); invisible(gc(verbose = FALSE))
}
# [Anotación · líneas 475–494] Promedia las probabilidades de todas las semillas por cliente, ordena de mayor
#   a menor y escribe predicciones_202108_junbo_hist.csv. Para cada corte de 9000 a 13000 crea
#   entrega/corte_<k>/ con un archivo por semilla (los k clientes de mayor probabilidad de esa semilla) y
#   lovrich_ensamble.csv (los k de mayor probabilidad promedio), sin encabezado.

# =====================================================================================
#  10-12) ENSAMBLE (promedio de probabilidades) + barrido de cortes + por-modelo
# =====================================================================================
prob_ens <- rowMeans(P)
pred <- data.table(numero_de_cliente = as.integer(ids_fut), prob = prob_ens)
setorder(pred, -prob)
fwrite(pred, file.path(PRM$salida, "predicciones_202108_junbo_hist.csv"))

dir_ent <- file.path(PRM$salida, "entrega"); dir.create(dir_ent, showWarnings = FALSE)
escribir <- function(ids, archivo) fwrite(data.table(as.integer(ids)), archivo, col.names = FALSE)
for (k in PRM$cortes) {
  dk <- file.path(dir_ent, sprintf("corte_%d", k)); dir.create(dk, showWarnings = FALSE)
  for (j in seq_along(SEMILLAS)) {
    env <- ids_fut[order(-P[, j])][seq_len(k)]
    escribir(env, file.path(dk, sprintf("lovrich_s%d.csv", SEMILLAS[j])))
  }
  escribir(pred$numero_de_cliente[seq_len(k)], file.path(dk, "lovrich_ensamble.csv"))
}
cat("submits escritos en", dir_ent, "\n")
# [Anotación · líneas 495–507] Recorre todos los CSV de la carpeta entrega y verifica que cada uno tenga entre
#   8000 y 13000 líneas, sólo dígitos, sin repetidos y con clientes presentes en 202108. Se detiene si alguno no
#   cumple; si no, imprime la cantidad de archivos verificados.

# =====================================================================================
#  13) VALIDACION DE FORMATO
# =====================================================================================
csvs <- list.files(dir_ent, pattern = "\\.csv$", recursive = TRUE, full.names = TRUE)
mal <- 0L
for (f in csvs) {
  x <- readLines(f)
  ok <- length(x) >= 8000 && length(x) <= 13000 && all(grepl("^[0-9]+$", x)) &&
        !anyDuplicated(x) && all(as.integer(x) %in% ids_fut)
  if (!ok) { cat("FORMATO MAL:", f, "\n"); mal <- mal + 1L }
}
if (mal > 0) stop(mal, " archivos no pasan la validacion de formato") else cat("formato OK en", length(csvs), "archivos\n")
# [Anotación · líneas 508–518] Si GCS_BUCKET no está vacío, copia con gcloud storage la carpeta entrega y el
#   archivo de predicciones al bucket. Imprime DONE_JUNBO_HIST al terminar.

# -------------------------------------------------------------------------------------
#  Subida opcional al bucket
# -------------------------------------------------------------------------------------
if (nzchar(PRM$bucket)) {
  cat("subiendo al bucket...\n")
  system(sprintf("gcloud storage cp --recursive %s %s/dmeyf_comp01/submits/rank_prestamos_junbo_hist/ >/dev/null 2>&1", dir_ent, PRM$bucket))
  system(sprintf("gcloud storage cp %s %s/dmeyf_comp01/ >/dev/null 2>&1",
                 file.path(PRM$salida, "predicciones_202108_junbo_hist.csv"), PRM$bucket))
}
cat("DONE_JUNBO_HIST\n")
```


## Explicaciones del alumno (texto original)

### README.md

> # DM EyF 2026: Competencia 01 (predicción de BAJA+2 en 202108)
>
> Entrega de **Agustín Lovrich**. Este repositorio contiene **todo lo necesario para replicar
> en forma exacta la predicción final** que subí al bot: el script end-to-end, los
> hiperparámetros con la optimización bayesiana que los produjo, y el archivo de entrega.
>
> - **Predicción final entregada:** `prediccion_final/lovrich_ensamble_corte11000.csv`
> - **Modelo:** LightGBM con normalización por rango con signo + retrovisores + **FE histórico**
>   (tendencia y promedio de 3 meses), semillerío de 40 semillas.
> - **Hiperparámetros (de la BO):** `num_leaves = 256`, `min_sum_hessian_in_leaf = 0.0299943`,
>   `num_iterations = 1439` (ver `optimizacion_bayesiana/`).
> - **Corte elegido:** 11000 envíos (justificación más abajo).
>
> > Agregar el **FE histórico** (tendencia + promedio de 3 meses sobre los rankings) subió el
> > leaderboard público de **104.50** (misma receta sin FE histórico, corte 11000) a **107.44**.
>
> ---
>
> ## Estructura del repositorio
>
> ```
> competencia_01/
> ├── README.md                                 # este archivo
> ├── run_rank_prestamos_junbo_hist.R           # script ÚNICO end-to-end (FE + FE histórico + BO + 40 semillas + submits)
> ├── optimizacion_bayesiana/
> │   ├── README.md                             # cómo saltar la BO y cómo se generaron los hiper
> │   ├── bo_mejor_config.csv                   # los hiperparámetros elegidos (para saltar la BO)
> │   ├── bo_evaluaciones.csv                   # la optimización bayesiana que los produjo
> │   └── junbo_hist.log                        # log completo de la corrida (procedencia)
> ├── prediccion_final/
> │   ├── README.md                             # qué es el archivo entregado + verificación por hash
> │   ├── lovrich_ensamble_corte11000.csv       # el archivo EXACTO entregado al bot
> │   └── SHA256.txt                            # hash del archivo de entrega
> └── data/
>     └── README.md                             # dónde poner el dataset crudo (no se versiona)
> ```
>
> ---
>
> ## Cómo replicar la predicción final
>
> ### Requisitos
> - R (probado en 4.6.1) con `data.table`, `lightgbm` (4.7.0) y `Rcpp` (para el FE histórico en C++).
>   El FE histórico compila una función C++ con `Rcpp::cppFunction`, así que hace falta un compilador
>   de C++ (Rtools en Windows, `build-essential` en Linux).
> - Para la optimización bayesiana: `DiceKriging`, `mlrMBO`, `smoof`, `lhs`, `ParamHelpers`
>   (el script los instala solo si faltan).
> - El dataset crudo de la competencia: `competencia_01_crudo.csv` (ver `data/README.md`).
>
> ### Opción A: reproducción completa (corre la BO desde cero)
> Genera la predicción de punta a punta, **incluyendo** la optimización bayesiana
> (~125 min de BO + feature engineering + 40 modelos). Es 100% autocontenido.
>
> ```bash
> DMEYF_CRUDO=data/competencia_01_crudo.csv \
> DMEYF_EXP=salida_run \
> GCS_BUCKET= \
> NTHREAD=8 NSEEDS=40 \
> Rscript run_rank_prestamos_junbo_hist.R
> ```
>
> - `GCS_BUCKET=` (vacío) desactiva la subida opcional a Google Cloud; **no hace falta ningún
>   bucket para replicar.**
> - La entrega queda en `salida_run/entrega/corte_11000/lovrich_ensamble.csv`.
>
> ### Opción B: saltar la BO usando los hiperparámetros ya optimizados
> Si no se quiere volver a correr la optimización bayesiana (~2 h), se le entrega al script
> la configuración ya encontrada. Ver instrucciones detalladas en
> [`optimizacion_bayesiana/README.md`](optimizacion_bayesiana/README.md). En resumen:
>
> ```bash
> mkdir -p salida_run
> cp optimizacion_bayesiana/bo_mejor_config.csv salida_run/bo_mejor_config.csv
> DMEYF_CRUDO=data/competencia_01_crudo.csv DMEYF_EXP=salida_run GCS_BUCKET= \
>   NTHREAD=8 NSEEDS=40 Rscript run_rank_prestamos_junbo_hist.R
> ```
>
> El script detecta `bo_mejor_config.csv` en la carpeta de salida y **no repite la BO**
> (`bo_mejor_config.csv ya existe: no repito la BO`). El resto del flujo es idéntico.
>
> > La configuración de la Opción B **es la misma** que elige la Opción A: la BO es
> > determinista (misma semilla primigenia 100193). La Opción B solo existe para ahorrar tiempo.
> > Siguiendo la indicación de la cátedra, se incluye además la optimización que dio origen a
> > esos hiperparámetros (`bo_evaluaciones.csv` + `junbo_hist.log`).
>
> ---
>
> ## El pipeline (de punta a punta)
>
> Todo ocurre en un único script R, reproducible y autocontenido:
>
> 1. **Lectura del crudo** y controles (meses presentes, sin columnas de texto).
> 2. **`clase_ternaria`** por cliente y mes calendario (BAJA+1 / BAJA+2 / CONTINUA). Si el crudo
>    ya la trae, se usa; si no, se genera.
> 3. **Data Quality (dq1):** `ccajas_depositos` se pone en NA solo en 202105 (mes roto), antes
>    de cualquier transformación.
> 4. **Normalización por rango con signo**, por variable y por mes (columnas `_rank`):
>    faltante → faltante, cero → cero, positivos → (0,1], negativos → [-1,0).
> 5. **Retrovisores 1 y 2 y sus diferencias** calculados **sobre las columnas normalizadas**
>    (lag1/delta1/lag2/delta2, calendario-exactos: el mismo cliente k meses atrás).
> 6. **FE histórico sobre los rankings:** por cada variable, la **tendencia** (pendiente por
>    mínimos cuadrados de los últimos 3 meses del cliente, `_rank_tend3`) y el **promedio** de los
>    últimos 3 meses (`_rank_avg3`). Se calcula con una función C++ (núcleo de la cátedra) sobre una
>    ventana posicional por cliente. Cada variable deja así **7 columnas**.
> 7. **Se descartan los valores crudos**: el árbol solo ve columnas transformadas
>    (7 por variable → **1064 columnas**).
> 8. **Optimización bayesiana** (mlrMBO, Kriging + Expected Improvement, métrica AUC, sin CV):
>    entrena 202103+04 → valida 202106, **sin undersampling**, **sin los 2 préstamos personales**
>    (1050 columnas). Busca `num_iterations`, `num_leaves`, `min_sum_hessian_in_leaf`.
> 9. **Foto de junio** (diagnóstico): modelo 202103+04 → predice 202106 (con las 1050 columnas),
>    curva de ganancia por corte para mirar la forma.
> 10. **Entrenamiento final** (202103-06, sin undersampling, **con los préstamos reincorporados**
>     ya transformados → 1064 columnas): **40 modelos** con los mismos hiperparámetros, cambiando
>     solo la semilla (primigenia 100193).
> 11. **Ensamble** = promedio simple de probabilidades por cliente.
> 12. **Barrido de cortes** (9000–13000, paso 500) → un archivo de envío por corte.
> 13. **Validación de formato** de todos los archivos (8000–13000 filas, enteros, sin
>     duplicados, solo clientes de 202108).
>
> **Hiperparámetros fijos** (no entran a la BO): `objective=binary`, `metric=auc`,
> `max_bin=31`, `min_data_in_leaf=0`, `feature_fraction=0.5`, `feature_fraction_bynode=0.2`,
> `learning_rate=0.005`, `deterministic=TRUE`.
>
> ---
>
> ## Resumen de decisiones
>
> | Decisión | Elección |
> |---|---|
> | **Datos** | `competencia_01_crudo.csv` → `clase_ternaria` (BAJA+1 / BAJA+2 / CONTINUA, por cliente y mes). Se genera en el script si el crudo no la trae. |
> | **Variables** | las 152 base normalizadas por rango con signo + `lag1`, `delta1`, `lag2`, `delta2`, `rank_tend3`, `rank_avg3` de todas (7 por variable → 1064 columnas). La BO usa 1050 (sin las 2 de préstamos). `ccajas_depositos` → NA en 202105 (dq1). |
> | **FE histórico** | sobre los rankings: tendencia (pendiente mínimos cuadrados, 3 meses) y promedio (3 meses), por cliente, con función C++ (núcleo de la cátedra). |
> | **Fuera del modelo** | `numero_de_cliente`, `foto_mes`, `clase_ternaria`. `cprestamos_personales` y `mprestamos_personales` quedan fuera de la BO y se reincorporan (ya transformados) en el entrenamiento final. |
> | **Clase** | `clase01` = 1 si `BAJA+1` ∪ `BAJA+2`, 0 si `CONTINUA`. Sin pesos ni clase artificial. |
> | **Hiperparámetros** | fijos: `max_bin` 31, `min_data_in_leaf` 0, `feature_fraction` 0.5, `feature_fraction_bynode` 0.2, `learning_rate` 0.005, `deterministic`. De la BO: **256 hojas**, `min_sum_hessian_in_leaf` **0.0299943**, **1439 árboles**. |
> | **Entrenamiento** | 202103-202106, 654.066 filas, sin undersampling. |
> | **Semillas** | 40, derivadas de la primigenia 100193 (criba de primos 1e5-1e6, `set.seed`, `sample`). |
> | **Ensamble** | promedio simple de **probabilidades** de las 40 semillas. |
> | **Corte** | **11000** (por la curva de ganancia en junio; público consistente: 107.44). |
>
> > **Nota sobre la BO:** eligió `num_leaves = 256`, que es el **tope del rango** de búsqueda
> > (`hojas_max = 256`), y un hessiano (`0.0299943`) muy cerca de su tope (`0.03`). O sea, la
> > búsqueda quedó pegada al borde del espacio: el óptimo podría estar más allá del rango. Se dejó
> > así para esta entrega; ampliar el rango de hojas sería el próximo paso.
>
> ---
>
> ## Por qué corte 11000
>
> El corte se eligió mirando la curva de ganancia en junio (mes 202106, etiquetado, validación
> propia del modelo), en la corrida final de 40 semillas. La ganancia es la del bot (BAJA+2 suma
> 1.072.500; cualquier otro envío resta 27.500), en millones:
>
> | Corte | Ganancia media ± sd entre semillas | Ganancia del ensamble |
> |---|---|---|
> | 9000  | 445.17 ± 3.95 | 462.00 |
> | 9500  | 449.68 ± 5.16 | 459.25 |
> | 10000 | 453.20 ± 5.31 | 456.50 |
> | 10500 | 453.64 ± 5.27 | 455.95 |
> | 11000 | **454.96 ± 3.89** | 454.30 |
> | 11500 | 454.30 ± 4.41 | 450.45 |
> | 12000 | 454.63 ± 5.19 | 452.10 |
> | 12500 | 453.97 ± 3.23 | 452.65 |
> | 13000 | 453.53 ± 4.73 | 456.50 |
>
> La media entre semillas (más estable que el ensamble de una sola realización) **tiene su máximo
> en 11000** (454.96).
>
> El leaderboard público coincide. El promedio de los envíos por-semilla (20 archivos) da la
> variabilidad entre semillas; el ensamble de las 40 semillas es un único archivo:
>
> | Corte | Público: por-semilla (media ± sd, 20 envíos) | Público: ensamble |
> |---|---|---|
> | 9500  | 99.83 ± 2.86 | n/d |
> | 10000 | 102.66 ± 1.94 | n/d |
> | 10500 | 103.64 ± 2.64 | 104.42 |
> | 11000 | **104.48 ± 2.84** | **107.44** |
>
> 11000 es el mejor tanto en la media por-semilla como en el ensamble. Las dos señales (junio y
> público) apuntan a 11000, así que ese es el corte de la entrega.
>
> ---
>
> ## Experimentos que se probaron y NO mejoraron la predicción
>
> Apartado de cosas que exploré y **descarté** porque no mejoraban (o empeoraban) el resultado:
>
> 1. **Manejo alternativo de NAs (`keepna`).** Leaderboard **101.27**. Peor.
> 2. **Rangos angostos de la BO** (`num_leaves ≤ 128`, `hessiano ≥ 0.0005`). Leaderboard
>    **103.12** vs **104.66** con rangos amplios (hasta 256 hojas, hessiano desde 0.0001). Los
>    rangos amplios dejan a la BO alcanzar árboles más profundos, que es donde está la ganancia.
> 3. **Flags binarios "es cero" por variable (`_zero`, 140 columnas intra-mes).** El modelo se
>    volvió más complejo (217 hojas, 900 columnas) pero la ganancia en junio quedó prácticamente
>    igual (~460M contra ~457M, una diferencia menor al desvío entre semillas de ~4-5 M) y no mostró
>    mejora clara. No se adoptó: más complejidad y más riesgo de sobreajuste sin beneficio.
> 4. **Hiperparámetros fijos salteando la Bayesiana**.
>    Se descartó en favor de dejar que la BO busque (es parte de la receta).
> 5. **Más semillas del mismo modelo (50, 80).** Rendimiento decreciente marcado: a 40 semillas el
>    ensamble ya es estable. Clonar el mismo modelo con más semillas **no agrega diversidad**, solo
>    reduce varianza marginalmente; no justifica el tiempo.
> 6. **Elegir el corte por el pico del leaderboard público.** El leaderboard público se mueve entre
>    cortes vecinos más de lo que distingue a un corte del otro: en una corrida el corte 10500 dio
>    105.71 con 10 semillas y 103.70 con 40 semillas, una diferencia comparable al desvío entre
>    semillas del semillerío. Por eso el corte final se decidió por la curva de ganancia en junio,
>    corroborada por el público, no por un único pico público.

### optimizacion_bayesiana/README.md

> # Optimización bayesiana: hiperparámetros del modelo final
>
> Esta carpeta documenta **cómo se obtuvieron los hiperparámetros** del modelo final y permite
> **saltar la optimización bayesiana** (BO) para no repetirla (~125 min), usando directamente la
> configuración encontrada.
>
> Se incluye por la indicación de la cátedra: si un modelo usa los mejores hiperparámetros de una
> corrida anterior para no volver a correr la BO, hay que subir **también la optimización que los
> originó** y explicar cómo proceder.
>
> ## Archivos
>
> | Archivo | Qué es |
> |---|---|
> | `bo_mejor_config.csv` | La configuración elegida por la BO (la que salta la optimización). |
> | `bo_evaluaciones.csv` | **La optimización completa**: cada punto evaluado por la BO con su AUC y ganancia. |
> | `junbo_hist.log` | Log completo de la corrida que generó todo (procedencia verificable). |
>
> ### `bo_mejor_config.csv`
> ```
> fuente,num_leaves,min_sum_hessian_in_leaf,num_iterations,auc
> BO_AUC,256,0.0299943000368938,1439,0.919070894119264
> ```
> - `num_leaves = 256`, `min_sum_hessian_in_leaf = 0.0299943000368938`, `num_iterations = 1439`.
> - Elegida por **AUC** sobre la validación de 202106 (la métrica que optimiza la BO).
>
> ## Cómo se generó (la optimización)
>
> En el mismo script `run_rank_prestamos_junbo_hist.R`, paso 8:
>
> - **Motor:** `mlrMBO` con surrogate Kriging (`regr.km`, matérn 3/2) y criterio de infill
>   **Expected Improvement**.
> - **Diseño inicial:** 10 puntos de un hipercubo latino maximin.
> - **Iteraciones:** hasta 30 guiadas por EI, con tope de 120 minutos.
> - **Espacio de búsqueda:** `num_iterations ∈ [600, 3500]`, `num_leaves ∈ [16, 256]`,
>   `min_sum_hessian_in_leaf ∈ [0.0001, 0.03]`.
> - **Datos de la BO:** entrena 202103+04, valida 202106 (sin cross-validation), **sin
>   undersampling** y **sin las columnas de los 2 préstamos personales** (1050 columnas, ya con el
>   FE histórico).
> - **Semilla:** la primigenia 100193 → la BO es **determinista y reproducible**.
> - **Selección:** la mejor por AUC. En `bo_evaluaciones.csv` queda registrada también la ganancia
>   por corte de cada punto (informativa; no cambia la selección).
>
> El trazado completo (con la correlación AUC↔ganancia de esa corrida) está en `junbo_hist.log`.
>
> > **Observación:** la BO eligió `num_leaves = 256`, que es el **tope del rango** (`hojas_max`), y
> > un hessiano (`0.0299943`) muy cerca de su tope (`0.03`). La búsqueda quedó pegada al borde del
> > espacio, así que el óptimo podría estar más allá del rango. Ampliar el rango de hojas sería el
> > próximo paso; para esta entrega se usó la mejor configuración dentro del rango.
>
> ## Cómo usar estos hiperparámetros para saltar la BO
>
> El script busca un archivo `bo_mejor_config.csv` **dentro de la carpeta de salida**
> (`DMEYF_EXP`). Si existe, no corre la optimización y usa esos hiperparámetros:
>
> ```bash
> mkdir -p salida_run
> cp optimizacion_bayesiana/bo_mejor_config.csv salida_run/bo_mejor_config.csv
>
> DMEYF_CRUDO=data/competencia_01_crudo.csv \
> DMEYF_EXP=salida_run \
> GCS_BUCKET= \
> NTHREAD=8 NSEEDS=40 \
> Rscript run_rank_prestamos_junbo_hist.R
> ```
>
> En el log verás `bo_mejor_config.csv ya existe: no repito la BO` y luego
> `hiperparametros finales [BO_AUC]: hojas 256 | hess 0.02999430 | arboles 1439`. El resto del
> pipeline (feature engineering, FE histórico, 40 semillas, ensamble, cortes) es idéntico a la
> reproducción completa.
>
> > **Importante:** saltar la BO da exactamente la misma configuración que correrla (es
> > determinista). Esta opción es solo para ahorrar las ~2 horas de optimización.

### prediccion_final/README.md

> # Predicción final
>
> ## El archivo entregado
>
> `lovrich_ensamble_corte11000.csv` es **el archivo exacto que subí al bot** como entrega final.
>
> - Es la salida de `run_rank_prestamos_junbo_hist.R` en
>   `entrega/corte_11000/lovrich_ensamble.csv`.
> - Contenido: un `numero_de_cliente` por línea, sin encabezado; los **11000** clientes con mayor
>   probabilidad estimada de ser BAJA+2 en 202108, según el ensamble de 40 semillas.
> - Modelo: LightGBM, normalización por rango con signo + retrovisores + FE histórico (tendencia y
>   promedio de 3 meses), hiperparámetros `256 / 0.0299943 / 1439` (ver `../optimizacion_bayesiana/`).
>
> ## Verificación de integridad
>
> `SHA256.txt` contiene el hash SHA-256 del archivo de entrega, para verificar que una réplica
> produjo el mismo archivo. Para comprobar:
>
> ```bash
> # Linux / macOS
> sha256sum -c SHA256.txt
>
> # Windows (PowerShell)
> Get-FileHash lovrich_ensamble_corte11000.csv -Algorithm SHA256
> ```
>
> El hash de una réplica debe coincidir con el de `SHA256.txt`. (La reproducibilidad está
> garantizada por `deterministic=TRUE` en LightGBM y las semillas fijas de la primigenia 100193.)
>
> ## Cómo se regenera
>
> Corriendo el pipeline (ver el README principal, Opción A o B). El archivo de entrega queda en
> `<DMEYF_EXP>/entrega/corte_11000/lovrich_ensamble.csv`.

### data/README.md

> # data/
>
> Acá va el **dataset crudo de la competencia**. No se versiona en GitHub (es el dato de la
> cátedra y es grande).
>
> ## Qué poner acá
>
> - `competencia_01_crudo.csv`: el crudo de la competencia 01 (foto_mes 202103 a 202108, con
>   `numero_de_cliente`, `foto_mes` y las ~152 variables del dataset).
>
> El script lo toma vía la variable de entorno `DMEYF_CRUDO`:
>
> ```bash
> DMEYF_CRUDO=data/competencia_01_crudo.csv ... Rscript ../run_rank_prestamos_junbo_hist.R
> ```
>
> ## Requisitos del crudo
>
> - Deben estar los meses `202103, 202104, 202105, 202106, 202107, 202108` (202107 hace falta para
>   los retrovisores de 202108 y para la clase de 202106).
> - Todas las columnas numéricas (salvo `clase_ternaria` si ya viene calculada). Si no trae
>   `clase_ternaria`, el script la calcula.

