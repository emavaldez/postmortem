# Ani-victoria — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: Ani-victoria
- Repositorio: https://github.com/Ani-victoria/dmeyf2026-competencia01
- Link posteado: https://github.com/Ani-victoria/dmeyf2026-competencia01/tree/main
- Commit: 21e0aaf0d52f973799d834a8e370d8ac7a0d09c5
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/ani-victoria/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/ani-victoria.json

## Resumen

La entrega contiene un README, tres notebooks de R numerados en el orden de ejecución y el registro de una búsqueda bayesiana de hiperparámetros (BO_log.txt). El notebook 6005 corre esa búsqueda con mlrMBO: 30 iteraciones, entrena LightGBM con 202103–202105 y 25% de los CONTINUA y mide la ganancia en 202106. Los notebooks 6018 y 6019 leen de ese registro la fila de mayor ganancia y arman las mismas variables: marca de aguinaldo, lag y delta de orden 1 de todas las columnas numéricas, lag y delta de orden 2 de una lista de 78 variables y 62 rankings por mes con cero fijo (rk_*). Cada uno entrena 20 LightGBM de clase binaria (BAJA+1 y BAJA+2 positivas) con 202103–202106, cada modelo con su semilla y su propio 25% de CONTINUA, y predice 202108. El 6019 usa 20 semillas distintas de las del 6018, promedia las probabilidades de los 40 modelos y escribe listas de clientes para 10.000 a 12.000 envíos. Según el README, la entrega final es la de 11.000 clientes (FINAL_e6019x40_N11000.csv), con una ganancia declarada de 110,47 en el bot. El README incluye además una tabla de 16 experimentos con la ganancia que declara para cada uno; los notebooks de los otros experimentos no están en el repositorio.

**Qué entrega.** Un archivo de texto sin encabezado con 11.000 numero_de_cliente de 202108: los de mayor probabilidad promedio de los 40 modelos. El notebook 6019 lo escribe en exp/HT6019/zulip/FINAL_e6019x40_N11000.csv. El README lo ubica también en entrega_final/FINAL_e6019x40_N11000.csv, carpeta que no figura entre los archivos del repositorio clonado.

**Cómo se ejecuta.** Según el README, tres pasos en orden sobre la estructura ~/buckets/b1 de Google Cloud. Paso 1: copiar 1_hiperparametros_6005/BO_log.txt a ~/buckets/b1/exp/HT6005/BO_log.txt, o bien correr el notebook 6005, que genera ese archivo (el README indica varias horas). Paso 2: abrir competencia01_gcp_6018_rank_cero_fijo.ipynb y hacer Run All (1,5 a 2,5 h), que genera exp/HT6018/predicciones_futuro.csv. Paso 3: abrir competencia01_gcp_6019_6018_semillas_nuevas.ipynb y hacer Run All (1,5 a 2,5 h), que entrena 20 modelos más, los promedia con los 20 del 6018 y escribe exp/HT6019/zulip/FINAL_e6019x40_N11000.csv. El README indica comparar ese archivo con entrega_final/FINAL_e6019x40_N11000.csv. El dataset se descarga desde la URL escrita en los notebooks.

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase01): 1 si clase_ternaria es BAJA+1 o BAJA+2, 0 en otro caso. La clase_ternaria se calcula en el mismo notebook a partir de la presencia del cliente en los dos meses siguientes.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** Cada modelo entrena con todas las filas de clase01 = 1 y, de las demás, las que sortean un número uniforme menor o igual a 0.25 (PARAM$trainingstrategy$undersampling_final = 0.25). En 6018 y 6019 el sorteo se hace por modelo dentro de dtrain_bolsa, con runif tras set.seed(semilla, kind = "Mersenne-Twister"), de modo que cada semilla tiene su propio subconjunto de CONTINUA. En la búsqueda bayesiana del 6005 el sorteo se hace una sola vez (columna azar) con set.seed(992720, kind = "L'Ecuyer-CMRG").
- **Calidad de datos:** No se observa en el código.
- **Drifting:** 62 variables de monto se pasan a ranking dentro de cada foto_mes (columnas rk_*) con la función rank_cero_fijo: el 0 queda en 0, cada positivo recibe su rango entre los positivos dividido por la cantidad de positivos (intervalo (0,1]), cada negativo el rango de su valor absoluto entre los negativos con signo menos (intervalo [-1,0)) y los NA quedan NA. Las variables originales se conservan. No se observa deflación ni estandarización.
- **Variables dentro del mes:** mes_aguinaldo (1 si foto_mes es junio o diciembre) y mpayroll_sin_sac (mpayroll dividido por 1.5 cuando cobra_aguinaldo es 1, mpayroll en otro caso). cobra_aguinaldo vale 1 si mes_aguinaldo es 1 y payroll_ratio está entre 1.3 y 2.0; payroll_ratio usa las dos filas anteriores del cliente (ver variables históricas). Los 62 rankings rk_* también se calculan dentro de cada foto_mes (ver drifting).
- **Variables históricas:** payroll_ratio (mpayroll sobre el promedio de mpayroll de las dos filas anteriores del cliente; NA si ese promedio no es positivo); lag 1 y delta 1 de todas las columnas numéricas salvo numero_de_cliente y foto_mes, incluidas las cuatro de aguinaldo (156 columnas de origen según la salida guardada en los notebooks); lag 2 y delta 2 de una lista de 78 variables escrita en el código (156 columnas nuevas). Los lags se calculan con shift por numero_de_cliente sobre la tabla ordenada por cliente y mes. El orden 2 general (PARAM$fe$lag2) y el bloque de máximo, mínimo y promedio contra el mes anterior (PARAM$fe$minmaxmean) están en FALSE. Según la salida guardada de 6018 y 6019, el dataset tiene 471 columnas tras el orden 1, 627 tras el orden 2 y 689 con los rankings.
- **Selección de variables:** No se observa en el código una selección por importancia. La lista de 78 variables de orden 2 y la de 62 variables de ranking están escritas en el código; el texto de la celda 32 del notebook 6019 dice que la primera sale de un notebook de diagnóstico (competencia01_gcp_diagnostico_orden2.ipynb) que no está en el repositorio. La importancia de variables del último modelo de la prueba en junio se guarda en impo_junio.txt y se imprime, sin usarse para filtrar. Entran al modelo todas las columnas salvo clase_ternaria, clase01, azar y training (688 según la salida guardada en los notebooks 6018 y 6019).
- **Optimización de hiperparámetros:** Búsqueda bayesiana con mlrMBO en el notebook 6005: 30 iteraciones, modelo sustituto regr.km (kriging con covarianza matern3_2) y criterio de expected improvement, sobre num_iterations (300 a 2000), learning_rate (0.01 a 0.1), feature_fraction (0.1 a 1.0), num_leaves (20 a 1024) y min_data_in_leaf (20 a 3000). Cada punto entrena 2 modelos (semillas 864203 y 451997) con 202103–202105 y 25% de CONTINUA y devuelve el máximo de la curva de ganancia promedio en 202106 entre 8.000 y 15.000 envíos de a 250. El BO_log.txt del repositorio tiene 50 filas: 20 del diseño inicial y 30 propuestas por la búsqueda. Los notebooks 6018 y 6019 no repiten la búsqueda: leen ese archivo.
- **Hiperparámetros finales:** Primera fila de BO_log.txt al ordenar por y descendente (y = 303.800.000): num_iterations 1168, learning_rate 0.0131541499918231, feature_fraction 0.344637721065804, num_leaves 61, min_data_in_leaf 966 (se multiplica por 0.25/0.25 = 1). Fijos en el código: boosting gbdt, objective binary, metric auc, max_bin 31, max_depth -1, lambda_l1 0, lambda_l2 0, min_gain_to_split 0, min_sum_hessian_in_leaf 0.001, bagging_fraction 1.0, feature_pre_filter FALSE, force_row_wise TRUE, extra_trees FALSE, is_unbalance FALSE, scale_pos_weight 1.0. El parámetro seed se reemplaza en cada modelo por su semilla.
- **Semillas:** Semilla primigenia 992720. Notebook 6018: las 10 de PARAM$semillas (864203, 451997, 909131, 582314, 737281, 128945, 675432, 390217, 842691, 519804) más 10 tomadas de sample(100000:999999, 30) tras set.seed(992720); según la salida guardada son 665522, 727778, 554901, 636033, 289813, 727556, 386266, 502608, 160882 y 303657. Notebook 6019: 20 tomadas de sample(100000:999999, 60) tras set.seed(992720 + 6019), descartando las 20 del 6018 (un stopifnot verifica que no se repitan); según la salida guardada son 478895, 768641, 898199, 203816, 505287, 779340, 835262, 379050, 418101, 576147, 379157, 582228, 173019, 936797, 989100, 522669, 378094, 906206, 368631 y 234948. Cada semilla se usa para el sorteo del 25% de CONTINUA y como seed de LightGBM.
- **Cantidad de semillas:** 40
- **Ensamble:** Promedio aritmético de las probabilidades de 40 LightGBM con las mismas variables e hiperparámetros y distinta semilla. El notebook 6019 lee exp/HT6018/predicciones_futuro.csv, promedia sus columnas pred_bolsa_* (p18, n18 modelos), promedia las propias (p19, n19) y calcula por numero_de_cliente p40 = (p18·n18 + p19·n19)/(n18 + n19).
- **Corte:** Cantidad fija de clientes, ordenados por probabilidad promedio descendente. El notebook 6019 escribe el ensamble de 40 modelos para 10.000, 10.500, 11.000, 11.500 y 12.000 envíos, y el de sus 20 modelos para 9.500 a 12.000 de a 250. El código no elige uno de esos archivos. Según el README, la entrega es la de 11.000, se probaron cortes de 9.500 a 14.000 y 11.000 dio el resultado más alto en todos los modelos. En el código de 6018 y 6019 la ganancia por corte sólo se tabula en la prueba de junio (9.000 a 13.000 de a 500) y ningún corte se toma de esa tabla.
- **Validación:** Mes posterior al entrenamiento: 202106. En la búsqueda bayesiana (6005) se entrena con 202103–202105 y se mide en 202106 completo la ganancia (+780.000 por cada BAJA+2 y −20.000 por cada fila que no lo es). En 6018 y 6019 la sección "Prueba en junio" entrena los 20 modelos con 202103–202105, promedia sus probabilidades en 202106 y tabula la ganancia para 9.000 a 13.000 envíos de a 500, junto a las columnas de otros experimentos si sus archivos existen; esa tabla se imprime y se graba, y no se usa en las celdas siguientes. El notebook 6005 además evalúa con 10 semillas en 202106 (media y desvío por corte) y con 3 semillas en 202105 entrenando con 202103–202104. Los modelos que predicen 202108 se entrenan después con 202103–202106.
- **Salidas:** En ~/buckets/b1/exp/HT6019/: zulip/FINAL_e6019x40_N10000 a N12000 (5 archivos, ensamble de 40), zulip/FINAL_e6019_N09500 a N12000 (11 archivos, 20 modelos), predicciones_futuro.csv (una columna pred_bolsa_<semilla> por modelo), bagging_pred_junio.csv, impo_junio.txt, comparacion_junio_vs_6006.txt y PARAM.yml. En exp/HT6018/: los mismos archivos con el nombre e6018, sin los x40. En exp/HT6005/: BO_log.txt, bayesiana.RDATA, PARAM.yml, curvas_evaluacion_local.txt, predicciones_futuro.csv, impo.txt, archivos zulip/ por semilla y por corte y zulip/FINAL_e6005_N<corte>.csv. En datasets/: competencia_01_crudo.csv y competencia_01.csv.gz.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Técnicas sólo exploradas

- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: Según el README: Google Cloud, máquina e2 custom de 8 vCPU y 64 GB de RAM (template del curso to-064ram-08vcpu), notebooks en R que esperan BASE <- ~/buckets/b1. Los metadatos de los tres notebooks registran kernel ir y R 4.6.1. No se declaran versiones de los paquetes; los notebooks los instalan con install.packages si faltan.

## Pasos del camino de la entrega

1. **Descarga del dataset y armado de la clase.** Cada notebook descarga competencia_01_crudo.csv a ~/buckets/b1/datasets si el archivo no existe, calcula clase_ternaria (CONTINUA, BAJA+1, BAJA+2) según la presencia del cliente en los dos meses siguientes y graba competencia_01.csv.gz. (`1_hiperparametros_6005/competencia01_gcp_6005.ipynb` líneas 10–73; `2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` líneas 8–71; `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` líneas 9–73)
2. **Parámetros de la corrida.** Semilla primigenia 992720, lista de 10 semillas, train 202103–202105, eval_mes 202106, train_final 202103–202106, future 202108, undersampling 0.25 y lista de parámetros fijos de LightGBM. Los tres notebooks repiten este bloque; cambia el número de experimento. (`1_hiperparametros_6005/competencia01_gcp_6005.ipynb` líneas 124–214; `2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` líneas 125–215; `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` líneas 132–222)
3. **Variables de aguinaldo.** Crea mes_aguinaldo (junio y diciembre), payroll_ratio (mpayroll sobre el promedio de las dos filas anteriores del cliente), cobra_aguinaldo (mes de aguinaldo y cociente entre 1.3 y 2.0) y mpayroll_sin_sac (mpayroll / 1.5 si cobra_aguinaldo es 1). Se calculan antes de los lags, por lo que también reciben lag y delta. (`1_hiperparametros_6005/competencia01_gcp_6005.ipynb` líneas 294–317; `2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` líneas 293–316; `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` líneas 307–330)
4. **Lags y deltas de orden 1.** Para cada columna numérica (salvo numero_de_cliente y foto_mes) calcula el valor de la fila anterior del cliente (_lag1) y la diferencia con ese valor (_delta1). (`1_hiperparametros_6005/competencia01_gcp_6005.ipynb` líneas 325–353; `2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` líneas 323–351; `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` líneas 342–370)
5. **Búsqueda bayesiana de hiperparámetros (notebook 6005).** El notebook 6005 crea clase01 y campos_buenos y, con las variables de aguinaldo y los lags y deltas de orden 1, entrena con 202103–202105 y 25% de CONTINUA y mide en 202106 el máximo de la curva de ganancia promedio de 2 semillas. mlrMBO propone 30 puntos sobre 5 hiperparámetros después de un diseño inicial; el resultado se ordena por ganancia y se graba en BO_log.txt, cuya primera fila es 1168 / 0.01315 / 0.3446 / 61 / 966. (`1_hiperparametros_6005/competencia01_gcp_6005.ipynb` líneas 223–235; `1_hiperparametros_6005/competencia01_gcp_6005.ipynb` líneas 375–385; `1_hiperparametros_6005/competencia01_gcp_6005.ipynb` líneas 391–437; `1_hiperparametros_6005/competencia01_gcp_6005.ipynb` líneas 440–486; `1_hiperparametros_6005/competencia01_gcp_6005.ipynb` líneas 489–514; `1_hiperparametros_6005/BO_log.txt` líneas 1–2)
6. **Lag 2 y delta 2 para 78 variables.** En 6018 y 6019 se agrega, sólo para una lista de 78 variables escrita en el notebook, el valor de dos filas atrás del cliente (_lag2) y la diferencia con ese valor (_delta2). (`2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` líneas 357–448; `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` líneas 380–471)
7. **Rankings con cero fijo por mes.** Para 62 variables de monto calcula rk_<variable> dentro de cada foto_mes: 0 queda en 0, los positivos van a (0,1] según su rango entre los positivos y los negativos a [-1,0) según su rango entre los negativos. (`2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` líneas 459–546; `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` líneas 482–569)
8. **Clase binaria y columnas del modelo.** Crea clase01 (1 para BAJA+1 y BAJA+2) y define campos_buenos como todas las columnas salvo clase_ternaria, clase01, azar y training. (`2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` líneas 570–580; `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` líneas 593–603)
9. **Lectura de los hiperparámetros del 6005.** Lee exp/HT6005/BO_log.txt, lo ordena por y descendente y reemplaza en los parámetros fijos los cinco hiperparámetros de la primera fila. La búsqueda no se repite en estos notebooks. (`2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` líneas 586–601; `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` líneas 609–624)
10. **Semillas y submuestreo por modelo.** El 6018 arma 20 semillas (10 escritas más 10 sorteadas con set.seed(992720)); el 6019 sortea otras 20 con set.seed(992720 + 6019) y descarta las del 6018. dtrain_bolsa arma los datos de cada modelo: todas las filas de clase01 = 1 más el 25% de las demás, sorteado con la semilla del modelo. (`2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` líneas 603–618; `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` líneas 626–646)
11. **Prueba en junio.** Entrena los 20 modelos con 202103–202105, predice 202106, promedia las probabilidades y tabula la ganancia para 9.000 a 13.000 envíos de a 500. Guarda la importancia de variables del último modelo y la tabla de comparación con otros experimentos. (`2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` líneas 626–672; `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` líneas 654–700)
12. **Modelos del 6018 para 202108.** Entrena 20 modelos con 202103–202106, cada uno con su 25% de CONTINUA, y guarda una columna de probabilidades por semilla en exp/HT6018/predicciones_futuro.csv. Escribe además los archivos FINAL_e6018 con el promedio de los 20. (`2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` líneas 680–700; `2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` líneas 703–722)
13. **Modelos del 6019 con 20 semillas nuevas.** Repite el entrenamiento con 202103–202106 para las 20 semillas nuevas, guarda exp/HT6019/predicciones_futuro.csv y escribe los archivos FINAL_e6019 con el promedio de esos 20 modelos. (`3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` líneas 708–728; `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` líneas 731–747)
14. **Promedio de los 40 modelos y archivos de salida.** Une por numero_de_cliente el promedio de los 20 modelos del 6018 con el de los 20 del 6019, calcula el promedio de los 40, ordena de mayor a menor y escribe zulip/FINAL_e6019x40_N<N>.csv para N de 10.000 a 12.000 de a 500. Según el README, el de N = 11.000 es la entrega. (`3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` líneas 749–767; `README.md` líneas 3–4)

## Archivos

- `README.md` · explicacion · Markdown · 90 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ani-victoria/README.md.txt) — Presentación de la entrega: cómo se arma la predicción final, cómo replicarla en tres pasos y una tabla de 16 experimentos con la ganancia que declara para cada uno en el bot.
- `2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` · principal · Jupyter (R) · 730 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ani-victoria/2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb.txt) — Notebook del experimento 6018. Arma las variables (aguinaldo, lag y delta de orden 1, orden 2 para 78 variables, 62 rankings con cero fijo), entrena 20 LightGBM con 202103–202106 y guarda sus probabilidades para 202108 en exp/HT6018/predicciones_futuro.csv.
- `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` · principal · Jupyter (R) · 779 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ani-victoria/3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb.txt) — Notebook del experimento 6019. Repite el armado de variables y el entrenamiento del 6018 con 20 semillas distintas y, en su última celda de código, promedia las probabilidades de los 40 modelos y escribe los archivos FINAL_e6019x40.
- `1_hiperparametros_6005/BO_log.txt` · configuracion · Texto · 51 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ani-victoria/1_hiperparametros_6005/BO_log.txt.txt) — Registro de la búsqueda bayesiana del experimento 6005: 50 filas con los hiperparámetros probados y la ganancia de cada punto, ordenadas por ganancia descendente. Los notebooks 6018 y 6019 leen su primera fila.
- `1_hiperparametros_6005/competencia01_gcp_6005.ipynb` · principal · Jupyter (R) · 728 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ani-victoria/1_hiperparametros_6005/competencia01_gcp_6005.ipynb.txt) — Notebook del experimento 6005. Corre la búsqueda bayesiana de hiperparámetros con mlrMBO y graba BO_log.txt, que es lo que usan los notebooks 6018 y 6019. El resto del notebook (evaluación local, modelos y archivos propios del 6005, prueba en 202105) no alimenta la entrega final.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### 2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb

Notebook del experimento 6018. Arma las variables (aguinaldo, lag y delta de orden 1, orden 2 para 78 variables, 62 rankings con cero fijo), entrena 20 LightGBM con 202103–202106 y guarda sus probabilidades para 202108 en exp/HT6018/predicciones_futuro.csv.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] Título del experimento 6018 (rankings con cero fijo). Fija BASE en ~/buckets/b1,
#   crea las carpetas datasets y exp y descarga competencia_01_crudo.csv desde la URL del curso sólo si el
#   archivo no existe o está vacío, con un timeout de 3.600 segundos.
#%% celda 1 [texto]
# Primera Competencia (notebook nombre: exp 6018 ahora hago rankings con cero fijo 

#%% celda 2 [texto]
## 1. Carpetas y dataset (bucket de Google Cloud)

#%% celda 3 [código]
BASE <- path.expand("~/buckets/b1")   # bucket de Google Cloud (persistente)

dir.create(file.path(BASE, "datasets"), recursive= TRUE, showWarnings= FALSE)
dir.create(file.path(BASE, "exp"),      recursive= TRUE, showWarnings= FALSE)

# URL del dataset 2026
archivo_origen  <- "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
archivo_destino <- file.path(BASE, "datasets", "competencia_01_crudo.csv")

options(timeout= 3600)   # el archivo es grande; por defecto R corta a los 60 segundos

if (!file.exists(archivo_destino) || file.size(archivo_destino) == 0)
  download.file(archivo_origen, archivo_destino, mode= "wb")

cat("Carpeta de trabajo:", BASE, "\n")
cat("Dataset:", round(file.size(archivo_destino) / 1e6), "MB\n")

# [Anotación · líneas 25–75] Arma clase_ternaria: convierte foto_mes en un número de período consecutivo,
#   calcula por cliente los dos períodos siguientes (leads 1 y 2) y asigna CONTINUA a los períodos anteriores al
#   anteúltimo, BAJA+1 cuando el cliente no aparece en el período siguiente y BAJA+2 cuando aparece en el
#   siguiente y no en el subsiguiente. Graba competencia_01.csv.gz y muestra la cantidad de filas por foto_mes y
#   clase.
#%% celda 4 [texto]
## 2. Generacion de la clase_ternaria]

#%% celda 5 [código]
require( "data.table" )

# leo el dataset
dataset <- fread(file.path(BASE, "datasets", "competencia_01_crudo.csv") )

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
    file =  file.path(BASE, "datasets", "competencia_01.csv.gz"),
    sep = ","
)

#%% celda 6 [código]
setorder( dataset, foto_mes, clase_ternaria, numero_de_cliente)
dataset[, .N, list(foto_mes, clase_ternaria)]

# [Anotación · líneas 77–117] Registra la hora, borra todos los objetos de memoria salvo BASE y carga
#   data.table, parallel, R.utils, primes, utils, rlist, yaml, lightgbm, DiceKriging y mlrMBO, instalando los
#   que falten.
#%% celda 7 [texto]
## 3. Inicio y parámetros

#%% celda 8 [código]
format(Sys.time(), "%a %b %d %X %Y")

# limpio la memoria
rm(list= setdiff(ls(all.names=TRUE), "BASE")) # remove all objects, salvo BASE
gc(full=TRUE, verbose=FALSE) # garbage collection

#%% celda 9 [texto]
Carga de librerias. Esta parte lleva varios minutos la primera vez en Google Colab

#%% celda 10 [código]
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

# [Anotación · líneas 119–173] Define PARAM: experimento 6018, semilla primigenia 992720 y una lista de 10
#   semillas. Meses: train 202103–202105, eval_mes 202106, train_final 202103–202106 y future 202108. Cortes de
#   evaluación de 8.000 a 15.000 de a 250, undersampling 0.25 para la búsqueda bayesiana y para los modelos
#   finales y PARAM$fe$lag2 en FALSE.
#%% celda 11 [texto]
### 3.1 Definicion de Parametros
aqui debe cargar SU semilla primigenia
<br>**recuerde cambiar el numero de experimento en cada corrida nueva**

#%% celda 12 [código]
PARAM <- list()
PARAM$experimento <- 6018   # el 6016 con ranking con cero fijo

PARAM$semillaprimigenia <- 992720

# semillas para los modelos finales: un archivo de Zulip por semilla (maximo 20 por submit)
PARAM$semillas <- c(
  864203, 451997, 909131, 582314, 737281,
  128945, 675432, 390217, 842691, 519804
)

#%% celda 13 [texto]
**Meses.** Ajustar según la tabla de la sección 2. Dataset 2026: meses 202103 a 202108, futuro 202108:
- `eval_mes` = último mes con BAJA+2 conocido (202106) → donde se mide la ganancia local y la BO.
- `train` = meses anteriores a `eval_mes` → entrenamiento para BO y evaluación local.
- `train_final` = `train` + `eval_mes` → entrenamiento de los modelos que predicen el futuro.
- `future` = mes a predecir y entregar.

202107 **no** se usa para entrenar: todavía no se sabe quién de ese mes es BAJA+2.

#%% celda 14 [código]
# -------------------------------------------
# Períodos de entrenamiento, evaluación y futuro
# -------------------------------------------
PARAM$train       <- c(202103, 202104, 202105)   # el dataset 2026 arranca en 202103
PARAM$eval_mes    <- c(202106)
PARAM$train_final <- c(PARAM$train, PARAM$eval_mes)
PARAM$future      <- c(202108)

# cortes (cantidad de envíos) que se evaluan localmente
PARAM$cortes_eval <- seq(8000, 15000, by= 250)

# cortes para los archivos de Zulip
# NULL = se eligen solos alrededor del mejor corte de la evaluación local
PARAM$envios_zulip <- NULL

#%% celda 15 [código]
# un undersampling de 0.1  toma solo el 10% de los CONTINUA
# undersampling de 1.0  implica tomar TODOS los datos
# undersampling: Bayesian Optimization
PARAM$trainingstrategy$undersampling <- 0.25

# undersampling: evaluacion local y modelos finales
#  1.0 = todos los datos (necesita 16 GB de RAM o mas)
#  0.25 = version liviana para una compu con 8 GB
PARAM$trainingstrategy$undersampling_final <- 0.25

# lags y deltas de orden 2: FALSE para ahorrar memoria (8 GB)
PARAM$fe$lag2 <- FALSE

# [Anotación · líneas 175–236] Lista de parámetros fijos de LightGBM (gbdt, objective binary, metric auc,
#   max_bin 31, max_depth -1, lambda_l1 y lambda_l2 en 0, bagging_fraction 1.0) con valores iniciales para los
#   cinco hiperparámetros que después se reemplazan. Define también los rangos de la búsqueda bayesiana, 30
#   iteraciones y 2 semillas por iteración; en este notebook no se llama a mbo y de este bloque sólo param_fijos
#   se usa más adelante (línea 593).
#%% celda 16 [código]
# Parametros LightGBM

# parametros fijos del LightGBM que se pisaran con la parte variable de la BO
PARAM$lgbm$param_fijos <-  list(
  boosting= "gbdt", # puede ir  dart  , ni pruebe random_forest
  objective= "binary",
  metric= "auc",
  first_metric_only= FALSE,
  boost_from_average= TRUE,
  feature_pre_filter= FALSE,
  force_row_wise= TRUE, # para reducir warnings
  verbosity= -100,

  seed= PARAM$semillaprimigenia,

  max_depth= -1L, # -1 significa no limitar,  por ahora lo dejo fijo
  min_gain_to_split= 0, # min_gain_to_split >= 0
  min_sum_hessian_in_leaf= 0.001, #  min_sum_hessian_in_leaf >= 0.0
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

  num_iterations= 1000,
  learning_rate= 0.02,
  feature_fraction= 0.5,
  num_leaves= 150,
  min_data_in_leaf= 500
)

#%% celda 17 [texto]
Hiperparámetros que participan de la Bayesian Optimization
<br> si es un numero entero debe ir  makeIntegerParam
<br> si es un numero real (con decimales) debe ir  makeNumericParam

#%% celda 18 [código]
# Aqui se cargan los bordes de los hiperparametros de la BO
PARAM$hypeparametertuning$hs <- makeParamSet(
  makeIntegerParam("num_iterations", lower= 300L, upper= 2000L),
  makeNumericParam("learning_rate", lower= 0.01, upper= 0.1),
  makeNumericParam("feature_fraction", lower= 0.1, upper= 1.0),
  makeIntegerParam("num_leaves", lower= 20L, upper= 1024L),
  makeIntegerParam("min_data_in_leaf", lower= 20L, upper= 3000L)
)

#%% celda 19 [código]
PARAM$hyperparametertuning$iteraciones <- 30 # iteraciones bayesianas

# cuantas semillas usa CADA iteracion de la BO (1 o 2; mas semillas = mucho mas lento)
PARAM$hyperparametertuning$cant_semillas <- 2

# [Anotación · líneas 238–256] ganancia_acumulada ordena por probabilidad descendente y acumula +780.000 por
#   cada BAJA+2 y −20.000 por cada fila que no lo es. escribir_zulip escribe los numero_de_cliente uno por
#   línea, sin encabezado y sin notación científica.
#%% celda 20 [texto]
### 3.2 Funciones auxiliares

#%% celda 21 [código]
# ganancia acumulada: ordeno de mayor a menor probabilidad
#  y voy sumando +780000 por cada BAJA+2 y -20000 por cada uno que no lo es
# el elemento N del resultado es la ganancia de enviar estimulo a los N primeros

ganancia_acumulada <- function( pprob, pes_baja2 ) {
  cumsum( ifelse( pes_baja2[ order(-pprob) ], 780000, -20000 ) )
}

#%% celda 22 [código]
# escribe un archivo para Zulip: solo numero_de_cliente, sin encabezado,
#  sin notacion cientifica (cuidado con 48000000 y 31100000)

escribir_zulip <- function( pids, parchivo ) {
  writeLines( format( pids, scientific= FALSE, trim= TRUE ), parchivo )
}

# [Anotación · líneas 258–287] Crea exp/HT6018 y la fija como carpeta de trabajo. Lee competencia_01.csv.gz,
#   imprime filas y cantidad de BAJA+2 por mes y detiene la ejecución si falta algún mes de train_final, si
#   falta el mes futuro o si eval_mes no tiene BAJA+2.
#%% celda 23 [texto]
## 4. Preprocesamiento

#%% celda 24 [código]
# carpeta de trabajo

setwd(file.path(BASE, "exp"))
experimento_folder <- paste0("HT", PARAM$experimento)
dir.create(experimento_folder, showWarnings=FALSE)
setwd(file.path(BASE, "exp", experimento_folder))

if( file.exists("bayesiana.RDATA") )
  cat("ATENCION: ya existe bayesiana.RDATA en esta carpeta, la BO se va a retomar.\n",
      "Si es una corrida nueva, cambie PARAM$experimento\n")

#%% celda 25 [código]
# lectura del dataset
dataset <- fread(file.path(BASE, "datasets", "competencia_01.csv.gz"), stringsAsFactors= TRUE)

#%% celda 26 [código]
# controlo que los meses de PARAM tengan sentido
meses <- dataset[, list( N= .N, baja2= sum(clase_ternaria == "BAJA+2", na.rm= TRUE)), foto_mes]
print( meses )

stopifnot( all( PARAM$train_final %in% meses$foto_mes ) )
stopifnot( PARAM$future %in% meses$foto_mes )
stopifnot( meses[ foto_mes == PARAM$eval_mes, baja2 ] > 0 )   # eval_mes debe tener BAJA+2

if( PARAM$future != max(meses$foto_mes) )
  cat( "ATENCION: PARAM$future no es el ultimo mes del dataset\n" )

# [Anotación · líneas 289–316] Variables de aguinaldo: mes_aguinaldo (1 en junio y diciembre), payroll_ratio
#   (mpayroll sobre el promedio de mpayroll de las dos filas anteriores del cliente), cobra_aguinaldo (mes de
#   aguinaldo y cociente entre 1.3 y 2.0) y mpayroll_sin_sac (mpayroll / 1.5 cuando cobra_aguinaldo es 1).
#   Imprime cuántos clientes quedan marcados por mes.
#%% celda 27 [texto]
### 4.1 Aguinaldo 

#%% celda 28 [código]
setorder(dataset, numero_de_cliente, foto_mes)

# 1. mes en que se paga aguinaldo (junio y diciembre)
dataset[, mes_aguinaldo := as.integer(foto_mes %% 100 %in% c(6, 12))]

# 2. payroll promedio de los 2 meses anteriores (solo pasado)
dataset[, payroll_prev := (shift(mpayroll, 1) + shift(mpayroll, 2)) / 2, by= numero_de_cliente]

# 3. cuanto salto el sueldo contra el pasado
dataset[, payroll_ratio := fifelse(payroll_prev > 0, mpayroll / payroll_prev, NA_real_)]

# 4. cobra aguinaldo: mes de aguinaldo y el sueldo sube entre 30% y 100%
#    (mismo criterio que el notebook de polars)
dataset[, cobra_aguinaldo := as.integer(
  mes_aguinaldo == 1 & !is.na(payroll_ratio) & payroll_ratio >= 1.3 & payroll_ratio <= 2.0
)]

# 5. payroll sin aguinaldo: el SAC es medio sueldo, entonces divido por 1.5
dataset[, mpayroll_sin_sac := fifelse(cobra_aguinaldo == 1, mpayroll / 1.5, mpayroll)]

dataset[, payroll_prev := NULL]

# control: cuantos clientes cobran aguinaldo por mes
dataset[, list(cobran= sum(cobra_aguinaldo), clientes= .N), foto_mes]

# [Anotación · líneas 318–351] Para todas las columnas numéricas salvo numero_de_cliente, foto_mes y
#   clase_ternaria calcula el valor de la fila anterior del cliente (_lag1) y la diferencia con ese valor
#   (_delta1). Las ramas de orden 2 de este bloque no se ejecutan porque PARAM$fe$lag2 es FALSE.
#%% celda 29 [texto]
### 4.2 Feature engineering

#%% celda 30 [código]
# 1. Ordenar por cliente y mes
setorder(dataset, numero_de_cliente, foto_mes)

# 2. Columnas a transformar: excluyo identificadores, mes y clase
cols_excluir <- c("numero_de_cliente", "foto_mes", "clase_ternaria")
cols_features <- setdiff(names(dataset), cols_excluir)

# 3. Solo las columnas numericas
cols_features <- cols_features[sapply(dataset[, ..cols_features], is.numeric)]
cat("Cantidad de columnas numericas para lag/delta:", length(cols_features), "\n")

# 4. Lags de orden 1 (y 2 si PARAM$fe$lag2 es TRUE)
cols_lag1 <- paste0(cols_features, "_lag1")
dataset[, (cols_lag1) := shift(.SD, n= 1, type= "lag"), by= numero_de_cliente, .SDcols= cols_features]

if (PARAM$fe$lag2) {
  cols_lag2 <- paste0(cols_features, "_lag2")
  dataset[, (cols_lag2) := shift(.SD, n= 2, type= "lag"), by= numero_de_cliente, .SDcols= cols_features]
}

# 5. Delta-lags
for (i in seq_along(cols_features)) {
  col <- cols_features[i]
  set(dataset, j= paste0(col, "_delta1"), value= dataset[[col]] - dataset[[cols_lag1[i]]])
  if (PARAM$fe$lag2)
    set(dataset, j= paste0(col, "_delta2"), value= dataset[[col]] - dataset[[cols_lag2[i]]])
}

cat("Lags y deltas generados. Columnas totales:", ncol(dataset), "\n")
gc(full= TRUE, verbose= FALSE)

# [Anotación · líneas 353–448] Lista de 78 variables escrita en el código (vars_orden2). Verifica que existan
#   y calcula para cada una el valor de dos filas atrás del cliente (_lag2) y la diferencia con ese valor
#   (_delta2): 156 columnas nuevas.
#%% celda 31 [texto]
### 4.3 Lag 2 y delta 2 **solo** para las 78 variables que no me generan un problema en agosto

#%% celda 32 [código]
vars_orden2 <- c(
  "minversion2",
  "ccallcenter_transacciones",
  "thomebanking",
  "ctrx_quarter",
  "tcallcenter",
  "Master_msaldototal",
  "cseguro_vida",
  "Visa_msaldototal",
  "cprestamos_personales",
  "Visa_msaldopesos",
  "chomebanking_transacciones",
  "cinversion1",
  "mcheques_emitidos",
  "mcheques_depositados",
  "cseguro_auto",
  "cseguro_vivienda",
  "ccheques_emitidos",
  "Master_mpagado",
  "Visa_mpagado",
  "ccuenta_debitos_automaticos",
  "ccheques_depositados",
  "matm",
  "Master_mpagospesos",
  "mcuenta_corriente",
  "ctransferencias_recibidas",
  "mtransferencias_recibidas",
  "mcaja_ahorro",
  "mcaja_ahorro_adicional",
  "mextraccion_autoservicio",
  "catm_trx",
  "Visa_mpagospesos",
  "internet",
  "mrentabilidad_annual",
  "mcomisiones",
  "mautoservicio",
  "cinversion2",
  "cseguro_accidentes_personales",
  "mcuenta_debitos_automaticos",
  "mcomisiones_otras",
  "mtransferencias_emitidas",
  "mprestamos_prendarios",
  "mcajeros_propios_descuentos",
  "ccomisiones_mantenimiento",
  "ctransferencias_emitidas",
  "cextraccion_autoservicio",
  "cmobile_app_trx",
  "Master_mpagominimo",
  "Visa_mpagosdolares",
  "mactivos_margen",
  "cdescubierto_preacordado",
  "ctarjeta_debito_transacciones",
  "ccajeros_propios_descuentos",
  "Master_mpagosdolares",
  "Visa_mpagominimo",
  "cprestamos_hipotecarios",
  "mttarjeta_visa_debitos_automaticos",
  "mcomisiones_mantenimiento",
  "ccomisiones_otras",
  "cforex",
  "cforex_sell",
  "mforex_sell",
  "ccajas_transacciones",
  "ccajas_extracciones",
  "matm_other",
  "mrentabilidad",
  "mpasivos_margen",
  "mprestamos_personales",
  "mprestamos_hipotecarios",
  "mpagomiscuentas",
  "ctarjeta_master_descuentos",
  "catm_trx_other",
  "tmobile_app",
  "mcaja_ahorro_dolares",
  "ctarjeta_debito",
  "cprestamos_prendarios",
  "cpagomiscuentas",
  "ccajas_consultas",
  "ccajas_otras"
)

faltan <- setdiff(vars_orden2, names(dataset))
if (length(faltan) > 0) stop("No existen en el dataset: ", paste(faltan, collapse= ", "))

setorder(dataset, numero_de_cliente, foto_mes)
cols_l2 <- paste0(vars_orden2, "_lag2")
dataset[, (cols_l2) := shift(.SD, n= 2, type= "lag"), by= numero_de_cliente, .SDcols= vars_orden2]
for (i in seq_along(vars_orden2))
  set(dataset, j= paste0(vars_orden2[i], "_delta2"), value= dataset[[vars_orden2[i]]] - dataset[[cols_l2[i]]])

cat("Orden 2 para", length(vars_orden2), "variables (", 2 * length(vars_orden2), "columnas nuevas). Columnas totales:", ncol(dataset), "\n")
gc(full= TRUE, verbose= FALSE)

# [Anotación · líneas 450–546] Lista de 62 variables de monto (vars_rank) y función rank_cero_fijo: deja el 0
#   en 0, asigna a cada positivo su rango entre los positivos dividido por la cantidad de positivos (intervalo
#   (0,1]), a cada negativo el rango de su valor absoluto entre los negativos con signo menos (intervalo [-1,0))
#   y mantiene los NA. Se aplica dentro de cada foto_mes y genera las columnas rk_*. Imprime por mes el mínimo y
#   el máximo de rk_mcuentas_saldo, el porcentaje de ceros de rk_mprestamos_personales y las medianas de
#   mpayroll y rk_mpayroll.
#%% celda 33 [texto]
### 4.5 Rankings con cero fijo dentro de cada mes (lo único que cambia contra el 6016)
Para cada variable de monto, `rk_<variable>`, calculado **dentro de cada mes**:
- 0 → **0**
- positivos → su lugar **entre los positivos**, de 0 a 1 (el más alto = 1)
- negativos → su lugar **entre los negativos**, de 0 a −1 (el más negativo = −1)
- vacío → vacío

#%% celda 34 [código]
vars_rank <- c(
  "Visa_mconsumosdolares",
  "mtarjeta_master_consumo",
  "Master_mconsumosdolares",
  "Visa_mconsumospesos",
  "Visa_mconsumototal",
  "Master_mconsumospesos",
  "Master_mconsumototal",
  "mpayroll",
  "Visa_msaldodolares",
  "minversion1_pesos",
  "Master_msaldodolares",
  "mtarjeta_visa_consumo",
  "mcuentas_saldo",
  "minversion2",
  "Visa_mlimitecompra",
  "Visa_mfinanciacion_limite",
  "Master_msaldototal",
  "Master_msaldopesos",
  "Visa_msaldototal",
  "mpagodeservicios",
  "mplazo_fijo_dolares",
  "mttarjeta_master_debitos_automaticos",
  "Visa_msaldopesos",
  "mtarjeta_visa_descuentos",
  "mtarjeta_master_descuentos",
  "mcheques_emitidos",
  "mcheques_depositados",
  "Master_mpagado",
  "Visa_mpagado",
  "matm",
  "Master_mpagospesos",
  "mcuenta_corriente",
  "mtransferencias_recibidas",
  "mcaja_ahorro",
  "mcaja_ahorro_adicional",
  "mextraccion_autoservicio",
  "Visa_mpagospesos",
  "mrentabilidad_annual",
  "mcomisiones",
  "mautoservicio",
  "mcuenta_debitos_automaticos",
  "mcomisiones_otras",
  "mtransferencias_emitidas",
  "mprestamos_prendarios",
  "mcajeros_propios_descuentos",
  "Master_mpagominimo",
  "Visa_mpagosdolares",
  "mactivos_margen",
  "Master_mpagosdolares",
  "Visa_mpagominimo",
  "mttarjeta_visa_debitos_automaticos",
  "mcomisiones_mantenimiento",
  "mforex_sell",
  "matm_other",
  "mrentabilidad",
  "mpasivos_margen",
  "mprestamos_personales",
  "mprestamos_hipotecarios",
  "mpagomiscuentas",
  "mcaja_ahorro_dolares",
  "Master_mfinanciacion_limite",
  "Master_mlimitecompra"
)
faltan <- setdiff(vars_rank, names(dataset))
if (length(faltan) > 0) stop("No existen: ", paste(faltan, collapse= ", "))

rank_cero_fijo <- function(x) {
  r <- rep(NA_real_, length(x))
  r[!is.na(x) & x == 0] <- 0
  pos <- which(!is.na(x) & x > 0)
  neg <- which(!is.na(x) & x < 0)
  if (length(pos) > 0) r[pos] <-  frank(x[pos],  ties.method= "max") / length(pos)   # (0, 1]
  if (length(neg) > 0) r[neg] <- -frank(-x[neg], ties.method= "max") / length(neg)   # [-1, 0)
  r
}
cols_rk <- paste0("rk_", vars_rank)
dataset[, (cols_rk) := lapply(.SD, rank_cero_fijo), by= foto_mes, .SDcols= vars_rank]

# control extra: el cero queda en cero, positivos en (0,1], negativos en [-1,0)
print(dataset[, list(min_rk_saldo= min(rk_mcuentas_saldo, na.rm= TRUE), max_rk_saldo= max(rk_mcuentas_saldo, na.rm= TRUE),
                     pct_rk_prestamo_cero= round(100 * mean(rk_mprestamos_personales == 0, na.rm= TRUE), 1)), by= foto_mes][order(foto_mes)])
cat("Rankings agregados:", length(cols_rk), "| columnas totales:", ncol(dataset), "\n")

# control: el sueldo en pesos sube de mes a mes (inflacion + aguinaldo); el ranking no
print(dataset[mpayroll > 0, list(mediana_mpayroll= round(median(mpayroll)),
                                 mediana_rk_mpayroll= round(median(rk_mpayroll), 3)), by= foto_mes][order(foto_mes)])
gc(full= TRUE, verbose= FALSE)

# [Anotación · líneas 548–580] Bloque de máximo, mínimo y promedio contra el mes anterior, que no se ejecuta
#   porque PARAM$fe$minmaxmean es FALSE. Después crea clase01 (1 para BAJA+1 y BAJA+2) y define campos_buenos
#   como todas las columnas salvo clase_ternaria, clase01, azar y training; numero_de_cliente y foto_mes quedan
#   dentro de esa lista.
#%% celda 35 [texto]
### 4.4 (Opcional) máximo, mínimo y promedio contra el mes anterior
Tomado de los notebooks 4955/7001. **Usa mucha RAM** (agrega 3 columnas por variable):
activarlo solo si Colab tiene memoria suficiente.

#%% celda 36 [código]
PARAM$fe$minmaxmean <- FALSE

if( PARAM$fe$minmaxmean ) {
  for (i in seq_along(cols_features)) {
    col <- cols_features[i]
    actual   <- dataset[[col]]
    anterior <- dataset[[cols_lag1[i]]]
    set(dataset, j= paste0(col, "_max"),  value= pmax(actual, anterior))
    set(dataset, j= paste0(col, "_min"),  value= pmin(actual, anterior))
    set(dataset, j= paste0(col, "_mean"), value= (actual + anterior) / 2)
  }
  cat("max/min/mean generados. Columnas totales:", ncol(dataset), "\n")
  gc(full= TRUE, verbose= FALSE)
}

#%% celda 37 [código]
# paso la clase a binaria que tome valores {0,1}  enteros
#  BAJA+1 y BAJA+2  son  1,   CONTINUA es 0
dataset[, clase01 := ifelse(clase_ternaria %in% c("BAJA+2","BAJA+1"), 1L, 0L)]

# los campos que se van a utilizar
campos_buenos <- setdiff(
  colnames(dataset),
  c("clase_ternaria", "clase01", "azar", "training")
)

length(campos_buenos)

# [Anotación · líneas 582–601] Lee exp/HT6005/BO_log.txt (detiene la ejecución si no existe), lo ordena por y
#   descendente y toma de la primera fila los cinco hiperparámetros, que reemplazan a los de param_fijos.
#   min_data_in_leaf se multiplica por undersampling_final/undersampling (0.25/0.25) y se redondea.
#%% celda 38 [texto]
## 5. Hiperparámetros: los del 6005 (no se repite la Bayesian Optimization)

#%% celda 39 [código]
archivo_bo <- file.path(BASE, "exp", "HT6005", "BO_log.txt")
if (!file.exists(archivo_bo)) stop("No encuentro ", archivo_bo, " : falta el resultado de la Bayesian Optimization del 6005.")

tb_bo <- fread(archivo_bo)
setorder(tb_bo, -y)
cols_hp <- c("num_iterations", "learning_rate", "feature_fraction", "num_leaves", "min_data_in_leaf")

param_bag <- modifyList(PARAM$lgbm$param_fijos, as.list(tb_bo[1, ..cols_hp]))
param_bag$num_iterations   <- as.integer(param_bag$num_iterations)
param_bag$num_leaves       <- as.integer(param_bag$num_leaves)
param_bag$min_data_in_leaf <- as.integer(round(param_bag$min_data_in_leaf *
  PARAM$trainingstrategy$undersampling_final / PARAM$trainingstrategy$undersampling))

options(scipen= 999)
cat("Hiperparametros del 6005 (ganancia en la BO:", format(tb_bo[1, y], big.mark= ","), ")\n")
print(tb_bo[1, ..cols_hp])

# [Anotación · líneas 603–618] Arma las 20 semillas: las 10 de PARAM$semillas más las primeras 10 de
#   sample(100000:999999, 30) tras set.seed(992720) que no estén en esa lista. dtrain_bolsa(meses, semilla) fija
#   la semilla (Mersenne-Twister), sortea un número uniforme por fila y arma el lgb.Dataset con las filas de los
#   meses pedidos que tienen clase01 = 1 o que sortearon 0.25 o menos.
# 20 semillas para el bagging: las 10 de siempre + 10 nuevas (siempre las mismas)
PARAM$bagging$cant_bolsas <- 20
set.seed(PARAM$semillaprimigenia)
PARAM$bagging$semillas <- c(PARAM$semillas,
                            setdiff(sample(100000:999999, 30), PARAM$semillas)[1:(PARAM$bagging$cant_bolsas - length(PARAM$semillas))])
cat("\nSemillas del bagging:", PARAM$bagging$semillas, "\n")

# datos de entrenamiento de UNA bolsa: todas las bajas + un 25% de los CONTINUA elegido con su propia semilla
dtrain_bolsa <- function(meses, semilla) {
  set.seed(semilla, kind= "Mersenne-Twister")   # mismo generador siempre, aunque se retome la corrida
  azar_b <- runif(nrow(dataset))
  filtro <- dataset$foto_mes %in% meses &
            (azar_b <= PARAM$trainingstrategy$undersampling_final | dataset$clase01 == 1L)
  lgb.Dataset(data= data.matrix(dataset[filtro, campos_buenos, with= FALSE]),
              label= dataset[filtro, clase01])
}

# [Anotación · líneas 620–672] Prueba en junio: para cada semilla entrena con 202103–202105 y predice 202106
#   completo, guardando cada columna en bagging_pred_junio.csv (saltea las que ya existen). Guarda la
#   importancia de variables del último modelo en impo_junio.txt e imprime las 25 primeras y los rk_* entre las
#   60 primeras. Calcula la ganancia del promedio de las 20 probabilidades para 9.000 a 13.000 envíos de a 500
#   y, si existen los archivos de exp/HT6006 y exp/HT6016, agrega sus columnas y las diferencias; escribe
#   comparacion_junio_vs_6006.txt.
#%% celda 40 [texto]
## 6. Prueba en junio: 6016 vs 6006
Entrena los 20 modelos con marzo–mayo y mide la ganancia en junio (promediando sus probabilidades). La tabla pone al lado la curva del **6006 (bagging 20)**.
<br>Se guarda en `bagging_pred_junio.csv` a medida que avanza.

#%% celda 41 [código]
X_jun     <- data.matrix(dataset[foto_mes %in% PARAM$eval_mes, campos_buenos, with= FALSE])
baja2_jun <- dataset[foto_mes %in% PARAM$eval_mes, clase_ternaria %in% "BAJA+2"]

archivo_jun <- "bagging_pred_junio.csv"
pred_jun <- if (file.exists(archivo_jun)) fread(archivo_jun) else data.table(fila= seq_len(nrow(X_jun)))

for (s in PARAM$bagging$semillas) {
  col <- paste0("bolsa_", s)
  if (col %in% names(pred_jun)) { cat("Saltando (ya existe):", col, "\n"); next }
  d <- dtrain_bolsa(PARAM$train, s)
  m <- lgb.train(data= d, param= modifyList(param_bag, list(seed= s)))
  pred_jun[, (col) := predict(m, X_jun)]
  fwrite(pred_jun, archivo_jun)
  cat(format(Sys.time(), "%X"), "junio, bolsa", s, "lista\n")
  rm(d); gc(full= TRUE, verbose= FALSE)
}

if (exists("m")) {
  impo <- as.data.table(lgb.importance(m)); impo[, puesto := .I]
  fwrite(impo, "impo_junio.txt", sep= "\t")
  cat("\nLas 25 variables mas importantes:\n"); print(head(impo[, list(puesto, Feature, Gain= round(Gain, 4))], 25))
  cat("\nRankings (rk_) entre las 60 mas importantes:\n")
  print(impo[puesto <= 60 & grepl("^rk_", Feature), list(puesto, Feature, Gain= round(Gain, 4))])
  cat("Rankings en el top 60:", impo[puesto <= 60 & grepl("^rk_", Feature), .N], "de 60 (en el 6016 fueron 14)\n")
}

# ---------- comparacion contra el 6006 ----------
cortes     <- seq(9000, 13000, by= 500)
cols_bolsa <- paste0("bolsa_", PARAM$bagging$semillas)
comparacion <- data.table(envios= cortes,
                          e6018_bagging_20= round(ganancia_acumulada(rowMeans(pred_jun[, ..cols_bolsa]), baja2_jun)[cortes] / 1e6, 1))
archivo_6006 <- file.path(BASE, "exp", "HT6006", "bagging_comparacion_junio.txt")
if (file.exists(archivo_6006)) {
  c6006 <- fread(archivo_6006)[, list(envios, e6006_bagging_20= bagging_20_modelos)]
  comparacion <- merge(c6006, comparacion, by= "envios")
  comparacion[, diferencia := e6018_bagging_20 - e6006_bagging_20]
}
archivo_6016 <- file.path(BASE, "exp", "HT6016", "comparacion_junio_vs_6006.txt")
if (file.exists(archivo_6016)) {
  comparacion <- merge(comparacion, fread(archivo_6016)[, list(envios, e6016_bagging_20)], by= "envios")
  comparacion[, dif_vs_6016 := e6018_bagging_20 - e6016_bagging_20]
}
fwrite(comparacion, "comparacion_junio_vs_6006.txt", sep= "\t")
cat("\nGanancia en JUNIO (millones):\n"); print(comparacion)
if ("diferencia" %in% names(comparacion))
  cat("\nMejor 6006:", max(comparacion$e6006_bagging_20), "M  |  Mejor 6018:", max(comparacion$e6018_bagging_20), "M",
      "\n(diferencias de 1-2 M pueden ser ruido; 4-5 M o mas, probablemente real)\n")

# [Anotación · líneas 674–700] Modelos para 202108: para cada una de las 20 semillas entrena con 202103–202106
#   (cada modelo con su 25% de CONTINUA) y agrega la predicción como columna pred_bolsa_<semilla> a
#   predicciones_futuro.csv, que se reescribe en cada vuelta y se retoma si ya existe. Este archivo es el que
#   después lee el notebook 6019.
#%% celda 42 [texto]
## 7. Modelos para agosto (20 bolsas) y archivos para el bot
Entrena con marzo–junio, cada modelo con su propio 25% de los CONTINUA. Tarda ~40–60 minutos.
<br>Las predicciones se guardan en `predicciones_futuro.csv` a medida que avanza (si se corta, saltea lo ya hecho).

#%% celda 43 [código]
dfuture  <- dataset[foto_mes %in% PARAM$future]
X_future <- data.matrix(dfuture[, campos_buenos, with= FALSE])

archivo_pred <- "predicciones_futuro.csv"
if (file.exists(archivo_pred)) {
  tb_pred <- fread(archivo_pred)
  stopifnot(identical(tb_pred$numero_de_cliente, dfuture$numero_de_cliente))
} else {
  tb_pred <- dfuture[, list(numero_de_cliente)]
}

for (s in PARAM$bagging$semillas) {
  col <- paste0("pred_bolsa_", s)
  if (col %in% names(tb_pred)) { cat("Saltando (ya existe):", col, "\n"); next }
  d <- dtrain_bolsa(PARAM$train_final, s)
  m <- lgb.train(data= d, param= modifyList(param_bag, list(seed= s)))
  tb_pred[, (col) := predict(m, X_future)]
  fwrite(tb_pred, archivo_pred)
  cat(format(Sys.time(), "%X"), "agosto, bagging, semilla", s, "guardada\n")
  rm(d); gc(full= TRUE, verbose= FALSE)
}

# [Anotación · líneas 702–722] Promedia las columnas pred_bolsa_*, ordena los clientes por probabilidad
#   descendente y escribe zulip/FINAL_e6018_N<N>.csv para N de 9.500 a 12.000 de a 250, comprobando cantidad de
#   líneas, sólo dígitos, sin repetidos y clientes de 202108. Guarda PARAM en PARAM.yml.
#%% celda 44 [código]
# ---------- archivos FINAL: promedio de las probabilidades de los 20 modelos ----------
options(scipen= 999)
dir.create("zulip", showWarnings= FALSE)

cols_pred <- grep("^pred_bolsa_", names(tb_pred), value= TRUE)
cat("Modelos promediados:", length(cols_pred), "\n")
prob <- rowMeans(tb_pred[, ..cols_pred])
ids  <- tb_pred$numero_de_cliente[order(-prob)]

for (N in seq(9500, 12000, by= 250)) {
  archivo <- sprintf("zulip/FINAL_e6018_N%05d.csv", N)
  escribir_zulip(ids[1:N], archivo)
  lineas <- readLines(archivo)
  ok <- length(lineas) == N && all(grepl("^[0-9]+$", lineas)) && !anyDuplicated(lineas) &&
        all(as.numeric(lineas) %in% dfuture$numero_de_cliente)
  cat(archivo, ":", length(lineas), "lineas,", ifelse(ok, "OK", "ERROR"), "\n")
}

write_yaml(PARAM, file= "PARAM.yml")
format(Sys.time(), "%a %b %d %X %Y")

# [Anotación · líneas 724–730] Celda de texto con la lista de qué subir al bot: la columna dif_vs_6016 de la
#   tabla de junio y FINAL_e6018_N11000.csv.
#%% celda 45 [texto]
## 8. Qué subir al bot (siempre `submit <nombre>` en la primera línea)
Los archivos están en `exp/HT6018/zulip/`.
1. Tabla de junio: columna `dif_vs_6016` (mismos hiperparámetros y semillas → comparación justa).
2. `FINAL_e6018_N11000.csv` → comparar con el **6016: 111,65** (ruido del público ±4).
3. **Último envío: el elegido, solo.**
4. Al terminar: apagar la máquina.
```

### 3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb

Notebook del experimento 6019. Repite el armado de variables y el entrenamiento del 6018 con 20 semillas distintas y, en su última celda de código, promedia las probabilidades de los 40 modelos y escribe los archivos FINAL_e6019x40.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–24] Título del experimento 6019 (el 6018 con 20 semillas nuevas, más el promedio de
#   las 40). Fija BASE en ~/buckets/b1, crea las carpetas datasets y exp y descarga competencia_01_crudo.csv
#   desde la URL del curso sólo si el archivo no existe o está vacío, con un timeout de 3.600 segundos.
#%% celda 1 [texto]
# Primera Competencia (nuevo exp 6019, voy a hacer lo mismoq que en el 6018 con **20 semillas nuevas** (+ las 40 juntas)

#%% celda 2 [texto]
## 1. Carpetas y dataset (bucket de Google Cloud)
El dataset ya está en el bucket: la descarga se saltea.

#%% celda 3 [código]
BASE <- path.expand("~/buckets/b1")   # bucket de Google Cloud (persistente)

dir.create(file.path(BASE, "datasets"), recursive= TRUE, showWarnings= FALSE)
dir.create(file.path(BASE, "exp"),      recursive= TRUE, showWarnings= FALSE)

# URL del dataset 2026
archivo_origen  <- "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
archivo_destino <- file.path(BASE, "datasets", "competencia_01_crudo.csv")

options(timeout= 3600)   # el archivo es grande; por defecto R corta a los 60 segundos

if (!file.exists(archivo_destino) || file.size(archivo_destino) == 0)
  download.file(archivo_origen, archivo_destino, mode= "wb")

cat("Carpeta de trabajo:", BASE, "\n")
cat("Dataset:", round(file.size(archivo_destino) / 1e6), "MB\n")

# [Anotación · líneas 26–82] Arma clase_ternaria: convierte foto_mes en un número de período consecutivo,
#   calcula por cliente los dos períodos siguientes (leads 1 y 2) y asigna CONTINUA a los períodos anteriores al
#   anteúltimo, BAJA+1 cuando el cliente no aparece en el período siguiente y BAJA+2 cuando aparece en el
#   siguiente y no en el subsiguiente. Graba el resultado en competencia_01.csv.gz y muestra la cantidad de
#   filas por foto_mes y clase.
#%% celda 4 [texto]
## 2. Generacion de la clase_ternaria
Todo corre con el kernel **R**.

#%% celda 5 [código]
require( "data.table" )

# leo el dataset
dataset <- fread(file.path(BASE, "datasets", "competencia_01_crudo.csv") )

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
    file =  file.path(BASE, "datasets", "competencia_01.csv.gz"),
    sep = ","
)

#%% celda 6 [texto]
**Mirar esta tabla con atención**: define los meses de la sección 3.
- El **mes futuro** es el último (según el profe, 202108).
- El **último mes con BAJA+2** es el mes de evaluación local (normalmente futuro − 2).

#%% celda 7 [código]
setorder( dataset, foto_mes, clase_ternaria, numero_de_cliente)
dataset[, .N, list(foto_mes, clase_ternaria)]

# [Anotación · líneas 84–124] Registra la hora, borra todos los objetos de memoria salvo BASE y carga
#   data.table, parallel, R.utils, primes, utils, rlist, yaml, lightgbm, DiceKriging y mlrMBO, instalando los
#   que falten.
#%% celda 8 [texto]
## 3. Inicio y parámetros

#%% celda 9 [código]
format(Sys.time(), "%a %b %d %X %Y")

# limpio la memoria
rm(list= setdiff(ls(all.names=TRUE), "BASE")) # remove all objects, salvo BASE
gc(full=TRUE, verbose=FALSE) # garbage collection

#%% celda 10 [texto]
Carga de librerias. Esta parte lleva varios minutos la primera vez en Google Colab

#%% celda 11 [código]
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

# [Anotación · líneas 126–180] Define PARAM: experimento 6019, semilla primigenia 992720 y una lista de 10
#   semillas. Meses: train 202103–202105, eval_mes 202106, train_final los cuatro (202103–202106) y future
#   202108. Cortes de evaluación de 8.000 a 15.000 de a 250, undersampling 0.25 tanto para la búsqueda bayesiana
#   como para los modelos finales y PARAM$fe$lag2 en FALSE (sin orden 2 para todas las variables).
#%% celda 12 [texto]
### 3.1 Definicion de Parametros
aqui debe cargar SU semilla primigenia
<br>**recuerde cambiar el numero de experimento en cada corrida nueva**

#%% celda 13 [código]
PARAM <- list()
PARAM$experimento <- 6019   # el 6018 con 20 semillas nuevas

PARAM$semillaprimigenia <- 992720

# semillas para los modelos finales: un archivo de Zulip por semilla (maximo 20 por submit)
PARAM$semillas <- c(
  864203, 451997, 909131, 582314, 737281,
  128945, 675432, 390217, 842691, 519804
)

#%% celda 14 [texto]
**Meses.** Ajustar según la tabla de la sección 2. Dataset 2026: meses 202103 a 202108, futuro 202108:
- `eval_mes` = último mes con BAJA+2 conocido (202106) → donde se mide la ganancia local y la BO.
- `train` = meses anteriores a `eval_mes` → entrenamiento para BO y evaluación local.
- `train_final` = `train` + `eval_mes` → entrenamiento de los modelos que predicen el futuro.
- `future` = mes a predecir y entregar.

202107 **no** se usa para entrenar: todavía no se sabe quién de ese mes es BAJA+2.

#%% celda 15 [código]
# -------------------------------------------
# Períodos de entrenamiento, evaluación y futuro
# -------------------------------------------
PARAM$train       <- c(202103, 202104, 202105)   # el dataset 2026 arranca en 202103
PARAM$eval_mes    <- c(202106)
PARAM$train_final <- c(PARAM$train, PARAM$eval_mes)
PARAM$future      <- c(202108)

# cortes (cantidad de envíos) que se evaluan localmente
PARAM$cortes_eval <- seq(8000, 15000, by= 250)

# cortes para los archivos de Zulip
# NULL = se eligen solos alrededor del mejor corte de la evaluación local
PARAM$envios_zulip <- NULL

#%% celda 16 [código]
# un undersampling de 0.1  toma solo el 10% de los CONTINUA
# undersampling de 1.0  implica tomar TODOS los datos
# undersampling: Bayesian Optimization
PARAM$trainingstrategy$undersampling <- 0.25

# undersampling: evaluacion local y modelos finales
#  1.0 = todos los datos (necesita 16 GB de RAM o mas)
#  0.25 = version liviana para una compu con 8 GB
PARAM$trainingstrategy$undersampling_final <- 0.25

# lags y deltas de orden 2: FALSE para ahorrar memoria (8 GB)
PARAM$fe$lag2 <- FALSE

# [Anotación · líneas 182–243] Lista de parámetros fijos de LightGBM (gbdt, objective binary, metric auc,
#   max_bin 31, max_depth -1, lambda_l1 y lambda_l2 en 0, bagging_fraction 1.0) con valores iniciales para los
#   cinco hiperparámetros que después se reemplazan (num_iterations 1000, learning_rate 0.02, feature_fraction
#   0.5, num_leaves 150, min_data_in_leaf 500). Define también los rangos de la búsqueda bayesiana, 30
#   iteraciones y 2 semillas por iteración; en este notebook no se llama a mbo y de este bloque sólo param_fijos
#   se usa más adelante (línea 616).
#%% celda 17 [código]
# Parametros LightGBM

# parametros fijos del LightGBM que se pisaran con la parte variable de la BO
PARAM$lgbm$param_fijos <-  list(
  boosting= "gbdt", # puede ir  dart  , ni pruebe random_forest
  objective= "binary",
  metric= "auc",
  first_metric_only= FALSE,
  boost_from_average= TRUE,
  feature_pre_filter= FALSE,
  force_row_wise= TRUE, # para reducir warnings
  verbosity= -100,

  seed= PARAM$semillaprimigenia,

  max_depth= -1L, # -1 significa no limitar,  por ahora lo dejo fijo
  min_gain_to_split= 0, # min_gain_to_split >= 0
  min_sum_hessian_in_leaf= 0.001, #  min_sum_hessian_in_leaf >= 0.0
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

  num_iterations= 1000,
  learning_rate= 0.02,
  feature_fraction= 0.5,
  num_leaves= 150,
  min_data_in_leaf= 500
)

#%% celda 18 [texto]
Hiperparámetros que participan de la Bayesian Optimization
<br> si es un numero entero debe ir  makeIntegerParam
<br> si es un numero real (con decimales) debe ir  makeNumericParam

#%% celda 19 [código]
# Aqui se cargan los bordes de los hiperparametros de la BO
PARAM$hypeparametertuning$hs <- makeParamSet(
  makeIntegerParam("num_iterations", lower= 300L, upper= 2000L),
  makeNumericParam("learning_rate", lower= 0.01, upper= 0.1),
  makeNumericParam("feature_fraction", lower= 0.1, upper= 1.0),
  makeIntegerParam("num_leaves", lower= 20L, upper= 1024L),
  makeIntegerParam("min_data_in_leaf", lower= 20L, upper= 3000L)
)

#%% celda 20 [código]
PARAM$hyperparametertuning$iteraciones <- 30 # iteraciones bayesianas

# cuantas semillas usa CADA iteracion de la BO (1 o 2; mas semillas = mucho mas lento)
PARAM$hyperparametertuning$cant_semillas <- 2

# [Anotación · líneas 245–263] ganancia_acumulada ordena por probabilidad descendente y acumula +780.000 por
#   cada BAJA+2 y −20.000 por cada fila que no lo es; el elemento N del resultado es la ganancia de enviar a los
#   N primeros. escribir_zulip escribe los numero_de_cliente uno por línea, sin encabezado y sin notación
#   científica.
#%% celda 21 [texto]
### 3.2 Funciones auxiliares

#%% celda 22 [código]
# ganancia acumulada: ordeno de mayor a menor probabilidad
#  y voy sumando +780000 por cada BAJA+2 y -20000 por cada uno que no lo es
# el elemento N del resultado es la ganancia de enviar estimulo a los N primeros

ganancia_acumulada <- function( pprob, pes_baja2 ) {
  cumsum( ifelse( pes_baja2[ order(-pprob) ], 780000, -20000 ) )
}

#%% celda 23 [código]
# escribe un archivo para Zulip: solo numero_de_cliente, sin encabezado,
#  sin notacion cientifica (cuidado con 48000000 y 31100000)

escribir_zulip <- function( pids, parchivo ) {
  writeLines( format( pids, scientific= FALSE, trim= TRUE ), parchivo )
}

# [Anotación · líneas 265–294] Crea exp/HT6019 y la fija como carpeta de trabajo (avisa si allí existe
#   bayesiana.RDATA). Lee competencia_01.csv.gz, imprime filas y cantidad de BAJA+2 por mes y detiene la
#   ejecución si falta algún mes de train_final, si falta el mes futuro o si eval_mes no tiene BAJA+2.
#%% celda 24 [texto]
## 4. Preprocesamiento

#%% celda 25 [código]
# carpeta de trabajo

setwd(file.path(BASE, "exp"))
experimento_folder <- paste0("HT", PARAM$experimento)
dir.create(experimento_folder, showWarnings=FALSE)
setwd(file.path(BASE, "exp", experimento_folder))

if( file.exists("bayesiana.RDATA") )
  cat("ATENCION: ya existe bayesiana.RDATA en esta carpeta, la BO se va a retomar.\n",
      "Si es una corrida nueva, cambie PARAM$experimento\n")

#%% celda 26 [código]
# lectura del dataset
dataset <- fread(file.path(BASE, "datasets", "competencia_01.csv.gz"), stringsAsFactors= TRUE)

#%% celda 27 [código]
# controlo que los meses de PARAM tengan sentido
meses <- dataset[, list( N= .N, baja2= sum(clase_ternaria == "BAJA+2", na.rm= TRUE)), foto_mes]
print( meses )

stopifnot( all( PARAM$train_final %in% meses$foto_mes ) )
stopifnot( PARAM$future %in% meses$foto_mes )
stopifnot( meses[ foto_mes == PARAM$eval_mes, baja2 ] > 0 )   # eval_mes debe tener BAJA+2

if( PARAM$future != max(meses$foto_mes) )
  cat( "ATENCION: PARAM$future no es el ultimo mes del dataset\n" )

# [Anotación · líneas 296–330] Variables de aguinaldo. mes_aguinaldo vale 1 en junio y diciembre;
#   payroll_ratio es mpayroll dividido por el promedio de mpayroll de las dos filas anteriores del cliente (NA
#   si ese promedio no es positivo); cobra_aguinaldo vale 1 si es mes de aguinaldo y el cociente está entre 1.3
#   y 2.0; mpayroll_sin_sac es mpayroll dividido por 1.5 cuando cobra_aguinaldo es 1 y mpayroll en otro caso.
#   Borra la columna auxiliar payroll_prev e imprime cuántos clientes quedan marcados por mes.
#%% celda 28 [texto]
### 4.1 Aguinaldo (SAC) sin usar datos del futuro
En junio (y diciembre) el sueldo depositado salta por el aguinaldo. Si el modelo no lo sabe,
puede leer ese salto como un cambio de comportamiento del cliente.
<br>Cada fila usa **solo su mes y los dos anteriores**: la marca vale lo mismo para entrenar que para predecir.
<br>Va **antes** de los lags, así también se generan lags y deltas de estas variables.

#%% celda 29 [código]
# ============================================================
# AGUINALDO (SAC) SIN USAR DATOS DEL FUTURO
# ============================================================
setorder(dataset, numero_de_cliente, foto_mes)

# 1. mes en que se paga aguinaldo (junio y diciembre)
dataset[, mes_aguinaldo := as.integer(foto_mes %% 100 %in% c(6, 12))]

# 2. payroll promedio de los 2 meses anteriores (solo pasado)
dataset[, payroll_prev := (shift(mpayroll, 1) + shift(mpayroll, 2)) / 2, by= numero_de_cliente]

# 3. cuanto salto el sueldo contra el pasado
dataset[, payroll_ratio := fifelse(payroll_prev > 0, mpayroll / payroll_prev, NA_real_)]

# 4. cobra aguinaldo: mes de aguinaldo y el sueldo sube entre 30% y 100%
#    (mismo criterio que el notebook de polars)
dataset[, cobra_aguinaldo := as.integer(
  mes_aguinaldo == 1 & !is.na(payroll_ratio) & payroll_ratio >= 1.3 & payroll_ratio <= 2.0
)]

# 5. payroll sin aguinaldo: el SAC es medio sueldo, entonces divido por 1.5
dataset[, mpayroll_sin_sac := fifelse(cobra_aguinaldo == 1, mpayroll / 1.5, mpayroll)]

dataset[, payroll_prev := NULL]

# control: cuantos clientes cobran aguinaldo por mes
dataset[, list(cobran= sum(cobra_aguinaldo), clientes= .N), foto_mes]

# [Anotación · líneas 332–370] Toma todas las columnas numéricas salvo numero_de_cliente, foto_mes y
#   clase_ternaria (incluidas las de aguinaldo) y, con el dataset ordenado por cliente y mes, calcula para cada
#   una el valor de la fila anterior del cliente (_lag1) y la diferencia con ese valor (_delta1). Las ramas de
#   orden 2 de este bloque no se ejecutan porque PARAM$fe$lag2 es FALSE.
#%% celda 30 [texto]
### 4.2 Feature engineering: lags y delta-lags (orden 1 y 2)
Mismo enfoque de tu notebook, pero vectorizado con `.SDcols` (mucho más rápido que el loop con `get()`).

#%% celda 31 [código]
# ============================================================
# FEATURE ENGINEERING: LAGS Y DELTA-LAGS (ORDEN 1 Y 2)
# ============================================================

# 1. Ordenar por cliente y mes
setorder(dataset, numero_de_cliente, foto_mes)

# 2. Columnas a transformar: excluyo identificadores, mes y clase
cols_excluir <- c("numero_de_cliente", "foto_mes", "clase_ternaria")
cols_features <- setdiff(names(dataset), cols_excluir)

# 3. Solo las columnas numericas
cols_features <- cols_features[sapply(dataset[, ..cols_features], is.numeric)]
cat("Cantidad de columnas numericas para lag/delta:", length(cols_features), "\n")

# 4. Lags de orden 1 (y 2 si PARAM$fe$lag2 es TRUE)
cols_lag1 <- paste0(cols_features, "_lag1")
dataset[, (cols_lag1) := shift(.SD, n= 1, type= "lag"), by= numero_de_cliente, .SDcols= cols_features]

if (PARAM$fe$lag2) {
  cols_lag2 <- paste0(cols_features, "_lag2")
  dataset[, (cols_lag2) := shift(.SD, n= 2, type= "lag"), by= numero_de_cliente, .SDcols= cols_features]
}

# 5. Delta-lags
for (i in seq_along(cols_features)) {
  col <- cols_features[i]
  set(dataset, j= paste0(col, "_delta1"), value= dataset[[col]] - dataset[[cols_lag1[i]]])
  if (PARAM$fe$lag2)
    set(dataset, j= paste0(col, "_delta2"), value= dataset[[col]] - dataset[[cols_lag2[i]]])
}

cat("Lags y deltas generados. Columnas totales:", ncol(dataset), "\n")
gc(full= TRUE, verbose= FALSE)

# [Anotación · líneas 372–471] Lista de 78 variables escrita en el código (vars_orden2). Verifica que existan
#   en el dataset y calcula para cada una el valor de dos filas atrás del cliente (_lag2) y la diferencia con
#   ese valor (_delta2): 156 columnas nuevas. El texto de la celda indica que la lista proviene de un notebook
#   de diagnóstico (competencia01_gcp_diagnostico_orden2.ipynb), que no está en el repositorio.
#%% celda 32 [texto]
### 4.3 Lag 2 y delta 2 **solo** para las 78 variables que no "mienten" en agosto (lo único que cambia contra el 6006)
Salen del diagnóstico (`competencia01_gcp_diagnostico_orden2.ipynb`). Quedaron **afuera**:
- las que **mienten en agosto** por el aguinaldo (sueldo, saldo total, consumos con tarjeta, saldos en dólares, inversiones...): su delta 2 de agosto compara contra junio;
- la **zona gris**: pasan la regla pero agosto es el peor de los tres meses por más de 3 puntos (casi todas de tarjeta). *Ante la duda, afuera*;
- las **quietas** (casi nunca cambian: su lag 2 es una copia), las de **calendario** y las que **casi nadie usa**.

#%% celda 33 [código]
vars_orden2 <- c(
  "minversion2",
  "ccallcenter_transacciones",
  "thomebanking",
  "ctrx_quarter",
  "tcallcenter",
  "Master_msaldototal",
  "cseguro_vida",
  "Visa_msaldototal",
  "cprestamos_personales",
  "Visa_msaldopesos",
  "chomebanking_transacciones",
  "cinversion1",
  "mcheques_emitidos",
  "mcheques_depositados",
  "cseguro_auto",
  "cseguro_vivienda",
  "ccheques_emitidos",
  "Master_mpagado",
  "Visa_mpagado",
  "ccuenta_debitos_automaticos",
  "ccheques_depositados",
  "matm",
  "Master_mpagospesos",
  "mcuenta_corriente",
  "ctransferencias_recibidas",
  "mtransferencias_recibidas",
  "mcaja_ahorro",
  "mcaja_ahorro_adicional",
  "mextraccion_autoservicio",
  "catm_trx",
  "Visa_mpagospesos",
  "internet",
  "mrentabilidad_annual",
  "mcomisiones",
  "mautoservicio",
  "cinversion2",
  "cseguro_accidentes_personales",
  "mcuenta_debitos_automaticos",
  "mcomisiones_otras",
  "mtransferencias_emitidas",
  "mprestamos_prendarios",
  "mcajeros_propios_descuentos",
  "ccomisiones_mantenimiento",
  "ctransferencias_emitidas",
  "cextraccion_autoservicio",
  "cmobile_app_trx",
  "Master_mpagominimo",
  "Visa_mpagosdolares",
  "mactivos_margen",
  "cdescubierto_preacordado",
  "ctarjeta_debito_transacciones",
  "ccajeros_propios_descuentos",
  "Master_mpagosdolares",
  "Visa_mpagominimo",
  "cprestamos_hipotecarios",
  "mttarjeta_visa_debitos_automaticos",
  "mcomisiones_mantenimiento",
  "ccomisiones_otras",
  "cforex",
  "cforex_sell",
  "mforex_sell",
  "ccajas_transacciones",
  "ccajas_extracciones",
  "matm_other",
  "mrentabilidad",
  "mpasivos_margen",
  "mprestamos_personales",
  "mprestamos_hipotecarios",
  "mpagomiscuentas",
  "ctarjeta_master_descuentos",
  "catm_trx_other",
  "tmobile_app",
  "mcaja_ahorro_dolares",
  "ctarjeta_debito",
  "cprestamos_prendarios",
  "cpagomiscuentas",
  "ccajas_consultas",
  "ccajas_otras"
)

faltan <- setdiff(vars_orden2, names(dataset))
if (length(faltan) > 0) stop("No existen en el dataset: ", paste(faltan, collapse= ", "))

setorder(dataset, numero_de_cliente, foto_mes)
cols_l2 <- paste0(vars_orden2, "_lag2")
dataset[, (cols_l2) := shift(.SD, n= 2, type= "lag"), by= numero_de_cliente, .SDcols= vars_orden2]
for (i in seq_along(vars_orden2))
  set(dataset, j= paste0(vars_orden2[i], "_delta2"), value= dataset[[vars_orden2[i]]] - dataset[[cols_l2[i]]])

cat("Orden 2 para", length(vars_orden2), "variables (", 2 * length(vars_orden2), "columnas nuevas). Columnas totales:", ncol(dataset), "\n")
gc(full= TRUE, verbose= FALSE)

# [Anotación · líneas 473–569] Lista de 62 variables de monto (vars_rank) y función rank_cero_fijo: deja el 0
#   en 0, asigna a cada positivo su rango entre los positivos dividido por la cantidad de positivos (empates al
#   máximo, intervalo (0,1]), a cada negativo el rango de su valor absoluto entre los negativos con signo menos
#   (intervalo [-1,0)) y mantiene los NA. Se aplica dentro de cada foto_mes y genera las columnas rk_*. Imprime
#   dos controles por mes: mínimo y máximo de rk_mcuentas_saldo con el porcentaje de ceros de
#   rk_mprestamos_personales, y la mediana de mpayroll junto a la de rk_mpayroll.
#%% celda 34 [texto]
### 4.5 Rankings con cero fijo dentro de cada mes (lo único que cambia contra el 6016)
Para cada variable de monto, `rk_<variable>`, calculado **dentro de cada mes**:
- 0 → **0**
- positivos → su lugar **entre los positivos**, de 0 a 1 (el más alto = 1)
- negativos → su lugar **entre los negativos**, de 0 a −1 (el más negativo = −1)
- vacío → vacío

#%% celda 35 [código]
vars_rank <- c(
  "Visa_mconsumosdolares",
  "mtarjeta_master_consumo",
  "Master_mconsumosdolares",
  "Visa_mconsumospesos",
  "Visa_mconsumototal",
  "Master_mconsumospesos",
  "Master_mconsumototal",
  "mpayroll",
  "Visa_msaldodolares",
  "minversion1_pesos",
  "Master_msaldodolares",
  "mtarjeta_visa_consumo",
  "mcuentas_saldo",
  "minversion2",
  "Visa_mlimitecompra",
  "Visa_mfinanciacion_limite",
  "Master_msaldototal",
  "Master_msaldopesos",
  "Visa_msaldototal",
  "mpagodeservicios",
  "mplazo_fijo_dolares",
  "mttarjeta_master_debitos_automaticos",
  "Visa_msaldopesos",
  "mtarjeta_visa_descuentos",
  "mtarjeta_master_descuentos",
  "mcheques_emitidos",
  "mcheques_depositados",
  "Master_mpagado",
  "Visa_mpagado",
  "matm",
  "Master_mpagospesos",
  "mcuenta_corriente",
  "mtransferencias_recibidas",
  "mcaja_ahorro",
  "mcaja_ahorro_adicional",
  "mextraccion_autoservicio",
  "Visa_mpagospesos",
  "mrentabilidad_annual",
  "mcomisiones",
  "mautoservicio",
  "mcuenta_debitos_automaticos",
  "mcomisiones_otras",
  "mtransferencias_emitidas",
  "mprestamos_prendarios",
  "mcajeros_propios_descuentos",
  "Master_mpagominimo",
  "Visa_mpagosdolares",
  "mactivos_margen",
  "Master_mpagosdolares",
  "Visa_mpagominimo",
  "mttarjeta_visa_debitos_automaticos",
  "mcomisiones_mantenimiento",
  "mforex_sell",
  "matm_other",
  "mrentabilidad",
  "mpasivos_margen",
  "mprestamos_personales",
  "mprestamos_hipotecarios",
  "mpagomiscuentas",
  "mcaja_ahorro_dolares",
  "Master_mfinanciacion_limite",
  "Master_mlimitecompra"
)
faltan <- setdiff(vars_rank, names(dataset))
if (length(faltan) > 0) stop("No existen: ", paste(faltan, collapse= ", "))

rank_cero_fijo <- function(x) {
  r <- rep(NA_real_, length(x))
  r[!is.na(x) & x == 0] <- 0
  pos <- which(!is.na(x) & x > 0)
  neg <- which(!is.na(x) & x < 0)
  if (length(pos) > 0) r[pos] <-  frank(x[pos],  ties.method= "max") / length(pos)   # (0, 1]
  if (length(neg) > 0) r[neg] <- -frank(-x[neg], ties.method= "max") / length(neg)   # [-1, 0)
  r
}
cols_rk <- paste0("rk_", vars_rank)
dataset[, (cols_rk) := lapply(.SD, rank_cero_fijo), by= foto_mes, .SDcols= vars_rank]

# control extra: el cero queda en cero, positivos en (0,1], negativos en [-1,0)
print(dataset[, list(min_rk_saldo= min(rk_mcuentas_saldo, na.rm= TRUE), max_rk_saldo= max(rk_mcuentas_saldo, na.rm= TRUE),
                     pct_rk_prestamo_cero= round(100 * mean(rk_mprestamos_personales == 0, na.rm= TRUE), 1)), by= foto_mes][order(foto_mes)])
cat("Rankings agregados:", length(cols_rk), "| columnas totales:", ncol(dataset), "\n")

# control: el sueldo en pesos sube de mes a mes (inflacion + aguinaldo); el ranking no
print(dataset[mpayroll > 0, list(mediana_mpayroll= round(median(mpayroll)),
                                 mediana_rk_mpayroll= round(median(rk_mpayroll), 3)), by= foto_mes][order(foto_mes)])
gc(full= TRUE, verbose= FALSE)

# [Anotación · líneas 571–603] Bloque de máximo, mínimo y promedio entre el mes actual y el anterior, que no
#   se ejecuta porque PARAM$fe$minmaxmean es FALSE. Después crea clase01 (1 para BAJA+1 y BAJA+2, 0 para el
#   resto) y define campos_buenos como todas las columnas salvo clase_ternaria, clase01, azar y training;
#   numero_de_cliente y foto_mes quedan dentro de esa lista.
#%% celda 36 [texto]
### 4.4 (Opcional) máximo, mínimo y promedio contra el mes anterior
Tomado de los notebooks 4955/7001. **Usa mucha RAM** (agrega 3 columnas por variable):
activarlo solo si Colab tiene memoria suficiente.

#%% celda 37 [código]
PARAM$fe$minmaxmean <- FALSE

if( PARAM$fe$minmaxmean ) {
  for (i in seq_along(cols_features)) {
    col <- cols_features[i]
    actual   <- dataset[[col]]
    anterior <- dataset[[cols_lag1[i]]]
    set(dataset, j= paste0(col, "_max"),  value= pmax(actual, anterior))
    set(dataset, j= paste0(col, "_min"),  value= pmin(actual, anterior))
    set(dataset, j= paste0(col, "_mean"), value= (actual + anterior) / 2)
  }
  cat("max/min/mean generados. Columnas totales:", ncol(dataset), "\n")
  gc(full= TRUE, verbose= FALSE)
}

#%% celda 38 [código]
# paso la clase a binaria que tome valores {0,1}  enteros
#  BAJA+1 y BAJA+2  son  1,   CONTINUA es 0
dataset[, clase01 := ifelse(clase_ternaria %in% c("BAJA+2","BAJA+1"), 1L, 0L)]

# los campos que se van a utilizar
campos_buenos <- setdiff(
  colnames(dataset),
  c("clase_ternaria", "clase01", "azar", "training")
)

length(campos_buenos)

# [Anotación · líneas 605–624] Lee exp/HT6005/BO_log.txt (detiene la ejecución si no existe), lo ordena por y
#   descendente y toma de la primera fila num_iterations, learning_rate, feature_fraction, num_leaves y
#   min_data_in_leaf, que reemplazan a los de param_fijos. min_data_in_leaf se multiplica por
#   undersampling_final/undersampling (0.25/0.25) y se redondea. Imprime los valores.
#%% celda 39 [texto]
## 5. Hiperparámetros: los del 6005 (no se repite la Bayesian Optimization)

#%% celda 40 [código]
archivo_bo <- file.path(BASE, "exp", "HT6005", "BO_log.txt")
if (!file.exists(archivo_bo)) stop("No encuentro ", archivo_bo, " : falta el resultado de la Bayesian Optimization del 6005.")

tb_bo <- fread(archivo_bo)
setorder(tb_bo, -y)
cols_hp <- c("num_iterations", "learning_rate", "feature_fraction", "num_leaves", "min_data_in_leaf")

param_bag <- modifyList(PARAM$lgbm$param_fijos, as.list(tb_bo[1, ..cols_hp]))
param_bag$num_iterations   <- as.integer(param_bag$num_iterations)
param_bag$num_leaves       <- as.integer(param_bag$num_leaves)
param_bag$min_data_in_leaf <- as.integer(round(param_bag$min_data_in_leaf *
  PARAM$trainingstrategy$undersampling_final / PARAM$trainingstrategy$undersampling))

options(scipen= 999)
cat("Hiperparametros del 6005 (ganancia en la BO:", format(tb_bo[1, y], big.mark= ","), ")\n")
print(tb_bo[1, ..cols_hp])

# [Anotación · líneas 626–646] Semillas: reconstruye las 20 del 6018 (las 10 de PARAM$semillas más 10 de
#   sample(100000:999999, 30) tras set.seed(992720)) y genera 20 nuevas con set.seed(992720 + 6019) y
#   sample(100000:999999, 60), quitando las anteriores; un stopifnot verifica que no haya repetidas.
#   dtrain_bolsa(meses, semilla) arma el lgb.Dataset de un modelo: fija la semilla (Mersenne-Twister), sortea un
#   número uniforme por fila y conserva, de los meses pedidos, las filas con clase01 = 1 y las que sortearon
#   0.25 o menos.
# 20 semillas para el bagging: las 10 de siempre + 10 nuevas (siempre las mismas)
PARAM$bagging$cant_bolsas <- 20
# las 20 semillas que usaron el 6006 ... 6018 (para NO repetirlas)
set.seed(PARAM$semillaprimigenia)
semillas_viejas <- c(PARAM$semillas,
                     setdiff(sample(100000:999999, 30), PARAM$semillas)[1:(PARAM$bagging$cant_bolsas - length(PARAM$semillas))])
# 20 semillas NUEVAS, siempre las mismas (para poder retomar)
set.seed(PARAM$semillaprimigenia + 6019)
PARAM$bagging$semillas <- setdiff(sample(100000:999999, 60), semillas_viejas)[1:PARAM$bagging$cant_bolsas]
stopifnot(length(intersect(PARAM$bagging$semillas, semillas_viejas)) == 0)
cat("\nSemillas NUEVAS del bagging:", PARAM$bagging$semillas, "\n")

# datos de entrenamiento de UNA bolsa: todas las bajas + un 25% de los CONTINUA elegido con su propia semilla
dtrain_bolsa <- function(meses, semilla) {
  set.seed(semilla, kind= "Mersenne-Twister")   # mismo generador siempre, aunque se retome la corrida
  azar_b <- runif(nrow(dataset))
  filtro <- dataset$foto_mes %in% meses &
            (azar_b <= PARAM$trainingstrategy$undersampling_final | dataset$clase01 == 1L)
  lgb.Dataset(data= data.matrix(dataset[filtro, campos_buenos, with= FALSE]),
              label= dataset[filtro, clase01])
}

# [Anotación · líneas 648–700] Prueba en junio: para cada una de las 20 semillas entrena con 202103–202105
#   (dtrain_bolsa) y predice 202106 completo, guardando cada columna en bagging_pred_junio.csv; las semillas ya
#   presentes en el archivo se saltean. Guarda la importancia de variables del último modelo en impo_junio.txt e
#   imprime las 25 primeras y los rk_* que están entre las 60 primeras. Calcula la ganancia del promedio de las
#   20 probabilidades para 9.000 a 13.000 envíos de a 500 (en millones) y, si existen los archivos de exp/HT6006
#   y exp/HT6018, agrega sus columnas y las diferencias; escribe comparacion_junio_vs_6006.txt.
#%% celda 41 [texto]
## 6. Prueba en junio: 6016 vs 6006
Entrena los 20 modelos con marzo–mayo y mide la ganancia en junio (promediando sus probabilidades). La tabla pone al lado la curva del **6006 (bagging 20)**.
<br>Se guarda en `bagging_pred_junio.csv` a medida que avanza.

#%% celda 42 [código]
X_jun     <- data.matrix(dataset[foto_mes %in% PARAM$eval_mes, campos_buenos, with= FALSE])
baja2_jun <- dataset[foto_mes %in% PARAM$eval_mes, clase_ternaria %in% "BAJA+2"]

archivo_jun <- "bagging_pred_junio.csv"
pred_jun <- if (file.exists(archivo_jun)) fread(archivo_jun) else data.table(fila= seq_len(nrow(X_jun)))

for (s in PARAM$bagging$semillas) {
  col <- paste0("bolsa_", s)
  if (col %in% names(pred_jun)) { cat("Saltando (ya existe):", col, "\n"); next }
  d <- dtrain_bolsa(PARAM$train, s)
  m <- lgb.train(data= d, param= modifyList(param_bag, list(seed= s)))
  pred_jun[, (col) := predict(m, X_jun)]
  fwrite(pred_jun, archivo_jun)
  cat(format(Sys.time(), "%X"), "junio, bolsa", s, "lista\n")
  rm(d); gc(full= TRUE, verbose= FALSE)
}

if (exists("m")) {
  impo <- as.data.table(lgb.importance(m)); impo[, puesto := .I]
  fwrite(impo, "impo_junio.txt", sep= "\t")
  cat("\nLas 25 variables mas importantes:\n"); print(head(impo[, list(puesto, Feature, Gain= round(Gain, 4))], 25))
  cat("\nRankings (rk_) entre las 60 mas importantes:\n")
  print(impo[puesto <= 60 & grepl("^rk_", Feature), list(puesto, Feature, Gain= round(Gain, 4))])
  cat("Rankings en el top 60:", impo[puesto <= 60 & grepl("^rk_", Feature), .N], "de 60 (en el 6018 fueron 15)\n")
}

# ---------- comparacion contra el 6006 ----------
cortes     <- seq(9000, 13000, by= 500)
cols_bolsa <- paste0("bolsa_", PARAM$bagging$semillas)
comparacion <- data.table(envios= cortes,
                          e6019_bagging_20= round(ganancia_acumulada(rowMeans(pred_jun[, ..cols_bolsa]), baja2_jun)[cortes] / 1e6, 1))
archivo_6006 <- file.path(BASE, "exp", "HT6006", "bagging_comparacion_junio.txt")
if (file.exists(archivo_6006)) {
  c6006 <- fread(archivo_6006)[, list(envios, e6006_bagging_20= bagging_20_modelos)]
  comparacion <- merge(c6006, comparacion, by= "envios")
  comparacion[, diferencia := e6019_bagging_20 - e6006_bagging_20]
}
archivo_6018 <- file.path(BASE, "exp", "HT6018", "comparacion_junio_vs_6006.txt")
if (file.exists(archivo_6018)) {
  comparacion <- merge(comparacion, fread(archivo_6018)[, list(envios, e6018_semillas_viejas= e6018_bagging_20)], by= "envios")
  comparacion[, dif_nuevas_vs_viejas := e6019_bagging_20 - e6018_semillas_viejas]
}
fwrite(comparacion, "comparacion_junio_vs_6006.txt", sep= "\t")
cat("\nGanancia en JUNIO (millones):\n"); print(comparacion)
if ("diferencia" %in% names(comparacion))
  cat("\nMejor 6006:", max(comparacion$e6006_bagging_20), "M  |  Mejor 6018:", max(comparacion$e6019_bagging_20), "M",
      "\n(diferencias de 1-2 M pueden ser ruido; 4-5 M o mas, probablemente real)\n")

# [Anotación · líneas 702–728] Modelos para 202108: para cada una de las 20 semillas entrena con 202103–202106
#   (cada modelo con su 25% de CONTINUA) y predice los clientes de 202108. Cada predicción se agrega como
#   columna pred_bolsa_<semilla> a predicciones_futuro.csv, que se reescribe en cada vuelta; si el archivo ya
#   existe se retoma y se saltean las semillas presentes.
#%% celda 43 [texto]
## 7. Modelos para agosto (20 bolsas) y archivos para el bot
Entrena con marzo–junio, cada modelo con su propio 25% de los CONTINUA. Tarda ~40–60 minutos.
<br>Las predicciones se guardan en `predicciones_futuro.csv` a medida que avanza (si se corta, saltea lo ya hecho).

#%% celda 44 [código]
dfuture  <- dataset[foto_mes %in% PARAM$future]
X_future <- data.matrix(dfuture[, campos_buenos, with= FALSE])

archivo_pred <- "predicciones_futuro.csv"
if (file.exists(archivo_pred)) {
  tb_pred <- fread(archivo_pred)
  stopifnot(identical(tb_pred$numero_de_cliente, dfuture$numero_de_cliente))
} else {
  tb_pred <- dfuture[, list(numero_de_cliente)]
}

for (s in PARAM$bagging$semillas) {
  col <- paste0("pred_bolsa_", s)
  if (col %in% names(tb_pred)) { cat("Saltando (ya existe):", col, "\n"); next }
  d <- dtrain_bolsa(PARAM$train_final, s)
  m <- lgb.train(data= d, param= modifyList(param_bag, list(seed= s)))
  tb_pred[, (col) := predict(m, X_future)]
  fwrite(tb_pred, archivo_pred)
  cat(format(Sys.time(), "%X"), "agosto, bagging, semilla", s, "guardada\n")
  rm(d); gc(full= TRUE, verbose= FALSE)
}

# [Anotación · líneas 730–747] Promedia las columnas pred_bolsa_* de este notebook, ordena los clientes por
#   probabilidad descendente y escribe zulip/FINAL_e6019_N<N>.csv para N de 9.500 a 12.000 de a 250. Para cada
#   archivo comprueba que tenga N líneas, sólo dígitos, sin repetidos y con clientes de 202108.
#%% celda 45 [código]
# ---------- archivos FINAL: promedio de las probabilidades de los 20 modelos ----------
options(scipen= 999)
dir.create("zulip", showWarnings= FALSE)

cols_pred <- grep("^pred_bolsa_", names(tb_pred), value= TRUE)
cat("Modelos promediados:", length(cols_pred), "\n")
prob <- rowMeans(tb_pred[, ..cols_pred])
ids  <- tb_pred$numero_de_cliente[order(-prob)]

for (N in seq(9500, 12000, by= 250)) {
  archivo <- sprintf("zulip/FINAL_e6019_N%05d.csv", N)
  escribir_zulip(ids[1:N], archivo)
  lineas <- readLines(archivo)
  ok <- length(lineas) == N && all(grepl("^[0-9]+$", lineas)) && !anyDuplicated(lineas) &&
        all(as.numeric(lineas) %in% dfuture$numero_de_cliente)
  cat(archivo, ":", length(lineas), "lineas,", ifelse(ok, "OK", "ERROR"), "\n")
}

# [Anotación · líneas 749–770] Ensamble de 40: lee exp/HT6018/predicciones_futuro.csv, promedia sus columnas
#   pred_bolsa_* (p18, n18 modelos), une por numero_de_cliente con el promedio de este notebook (p19, n19) y
#   calcula p40 = (p18·n18 + p19·n19)/(n18 + n19). Imprime cuántos clientes coinciden entre los 11.000 primeros
#   de p18 y los de p19 y escribe zulip/FINAL_e6019x40_N<N>.csv para N de 10.000 a 12.000 de a 500, comprobando
#   cantidad de líneas, sólo dígitos y sin repetidos. Guarda PARAM en PARAM.yml.
# ---------- las 40: 6018 (semillas viejas) + 6019 (semillas nuevas) ----------
f18 <- fread(file.path(BASE, "exp", "HT6018", "predicciones_futuro.csv"))
a18 <- data.table(numero_de_cliente= as.numeric(f18$numero_de_cliente),
                  p18= rowMeans(f18[, grep("^pred_bolsa_", names(f18)), with= FALSE]),
                  n18= length(grep("^pred_bolsa_", names(f18))))
a19 <- data.table(numero_de_cliente= as.numeric(tb_pred$numero_de_cliente), p19= prob, n19= length(cols_pred))
m40 <- merge(a18, a19, by= "numero_de_cliente")
cat("\nClientes cruzados 6018 / 6019:", nrow(m40), "de", nrow(a19), "\n")
m40[, p40 := (p18 * n18 + p19 * n19) / (n18 + n19)]     # promedio de los 40 modelos
ids40 <- m40[order(-p40), numero_de_cliente]
cat("Top 11.000 en comun 6019 (nuevas) vs 6018 (viejas):",
    length(intersect(m40[order(-p19), numero_de_cliente][1:11000], m40[order(-p18), numero_de_cliente][1:11000])), "de 11000\n")
for (N in seq(10000, 12000, by= 500)) {
  archivo <- sprintf("zulip/FINAL_e6019x40_N%05d.csv", N)
  escribir_zulip(ids40[1:N], archivo)
  lineas <- readLines(archivo)
  ok <- length(lineas) == N && all(grepl("^[0-9]+$", lineas)) && !anyDuplicated(lineas)
  cat(archivo, ":", length(lineas), "lineas,", ifelse(ok, "OK", "ERROR"), "\n")
}

write_yaml(PARAM, file= "PARAM.yml")
format(Sys.time(), "%a %b %d %X %Y")

# [Anotación · líneas 772–779] Celda de texto con la lista de qué subir al bot: mirar la tabla de junio,
#   FINAL_e6019_N11000.csv (sólo semillas nuevas) y FINAL_e6019x40_N11000.csv, al que nombra como candidato al
#   envío final.
#%% celda 46 [texto]
## 8. Qué subir al bot (siempre `submit <nombre>` en la primera línea)
Los archivos están en `exp/HT6019/zulip/`.
1. Tabla de junio: `dif_nuevas_vs_viejas` → si es chica (±3), el 6018 no depende de las semillas.
2. `FINAL_e6019_N11000.csv` (solo semillas nuevas) → comparar con el **6018: 112,39** (ruido ±4).
3. `FINAL_e6019x40_N11000.csv` (las 40) → **candidato al envío final**.
4. **Último envío: el elegido, solo.**
5. Al terminar: apagar la máquina.
```

### 1_hiperparametros_6005/competencia01_gcp_6005.ipynb

Notebook del experimento 6005. Corre la búsqueda bayesiana de hiperparámetros con mlrMBO y graba BO_log.txt, que es lo que usan los notebooks 6018 y 6019. El resto del notebook (evaluación local, modelos y archivos propios del 6005, prueba en 202105) no alimenta la entrega final.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–25] Nota inicial: según el texto, el experimento se corrió antes en VS Code y dio
#   107,97 en el bot. Fija BASE en ~/buckets/b1, crea las carpetas datasets y exp y descarga
#   competencia_01_crudo.csv si no existe o está vacío.
#%% celda 1 [texto]
# Nota para mi: Primera Competencia (titulo: exp 6005 (copiando mi notebook original de google collab))

**Originalmente lo corri en VS Code y dio 107,97 en el bot, no hice ningun cambio al modelo y tiene 
aguinaldo + lags y deltas **de orden 1**, Bayesian Optimization de 30 iteraciones, 25% de los CONTINUA, 10 semillas.

Nota para despues de probar en el bot: hacer ensambles

#%% celda 2 [código]
BASE <- path.expand("~/buckets/b1")   # bucket de Google Cloud (persistente)

dir.create(file.path(BASE, "datasets"), recursive= TRUE, showWarnings= FALSE)
dir.create(file.path(BASE, "exp"),      recursive= TRUE, showWarnings= FALSE)

# URL del dataset 2026
archivo_origen  <- "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
archivo_destino <- file.path(BASE, "datasets", "competencia_01_crudo.csv")

options(timeout= 3600)   # el archivo es grande; por defecto R corta a los 60 segundos

if (!file.exists(archivo_destino) || file.size(archivo_destino) == 0)
  download.file(archivo_origen, archivo_destino, mode= "wb")

cat("Carpeta de trabajo:", BASE, "\n")
cat("Dataset:", round(file.size(archivo_destino) / 1e6), "MB\n")

# [Anotación · líneas 27–77] Arma clase_ternaria con los leads 1 y 2 del período por cliente (CONTINUA,
#   BAJA+1, BAJA+2), graba competencia_01.csv.gz y muestra la cantidad de filas por foto_mes y clase.
#%% celda 3 [texto]
## Genero mi clase ternaria primero 

#%% celda 4 [código]
require( "data.table" )

# leo el dataset
dataset <- fread(file.path(BASE, "datasets", "competencia_01_crudo.csv") )

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
    file =  file.path(BASE, "datasets", "competencia_01.csv.gz"),
    sep = ","
)

#%% celda 5 [código]
setorder( dataset, foto_mes, clase_ternaria, numero_de_cliente)
dataset[, .N, list(foto_mes, clase_ternaria)]

# [Anotación · líneas 79–116] Registra la hora, borra los objetos de memoria salvo BASE y carga data.table,
#   parallel, R.utils, primes, utils, rlist, yaml, lightgbm, DiceKriging y mlrMBO, instalando los que falten.
#%% celda 6 [texto]
## Inicio y parámetros (notebook del repositorio de las clases de los jueves)

#%% celda 7 [código]
format(Sys.time(), "%a %b %d %X %Y")

# limpio la memoria
rm(list= setdiff(ls(all.names=TRUE), "BASE")) # remove all objects, salvo BASE
gc(full=TRUE, verbose=FALSE) # garbage collection

#%% celda 8 [código]
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

# [Anotación · líneas 118–172] Define PARAM: experimento 6005, semilla primigenia 992720 y 10 semillas. Meses:
#   train 202103–202105, eval_mes 202106, train_final 202103–202106, future 202108. Cortes de evaluación de
#   8.000 a 15.000 de a 250, envios_zulip en NULL, undersampling 0.25 para la búsqueda y para los modelos
#   finales, lag2 en FALSE.
#%% celda 9 [texto]
###  Definicion de Parametros
aqui debe cargar SU semilla primigenia
<br>**recuerde cambiar el numero de experimento en cada corrida nueva**

#%% celda 10 [código]
PARAM <- list()
PARAM$experimento <- 6005   # el 5002 corrido en Google Cloud

PARAM$semillaprimigenia <- 992720

# semillas para los modelos finales: un archivo de Zulip por semilla (maximo 20 por submit)
PARAM$semillas <- c(
  864203, 451997, 909131, 582314, 737281,
  128945, 675432, 390217, 842691, 519804
)

#%% celda 11 [texto]
**Meses.** Ajustar según la tabla de la sección 2. Dataset 2026: meses 202103 a 202108, futuro 202108:
- `eval_mes` = último mes con BAJA+2 conocido (202106) → donde se mide la ganancia local y la BO.
- `train` = meses anteriores a `eval_mes` → entrenamiento para BO y evaluación local.
- `train_final` = `train` + `eval_mes` → entrenamiento de los modelos que predicen el futuro.
- `future` = mes a predecir y entregar.

202107 **no** se usa para entrenar: todavía no se sabe quién de ese mes es BAJA+2.

#%% celda 12 [código]
# -------------------------------------------
# Períodos de entrenamiento, evaluación y futuro
# -------------------------------------------
PARAM$train       <- c(202103, 202104, 202105)   # el dataset 2026 arranca en 202103
PARAM$eval_mes    <- c(202106)
PARAM$train_final <- c(PARAM$train, PARAM$eval_mes)
PARAM$future      <- c(202108)

# cortes (cantidad de envíos) que se evaluan localmente
PARAM$cortes_eval <- seq(8000, 15000, by= 250)

# cortes para los archivos de Zulip
# NULL = se eligen solos alrededor del mejor corte de la evaluación local
PARAM$envios_zulip <- NULL

#%% celda 13 [código]
# un undersampling de 0.1  toma solo el 10% de los CONTINUA
# undersampling de 1.0  implica tomar TODOS los datos
# undersampling: Bayesian Optimization
PARAM$trainingstrategy$undersampling <- 0.25

# undersampling: evaluacion local y modelos finales
#  1.0 = todos los datos (necesita 16 GB de RAM o mas)
#  0.25 = version liviana para una compu con 8 GB
PARAM$trainingstrategy$undersampling_final <- 0.25

# lags y deltas de orden 2: FALSE para ahorrar memoria (8 GB)
PARAM$fe$lag2 <- FALSE

# [Anotación · líneas 174–235] Parámetros fijos de LightGBM (gbdt, objective binary, metric auc, max_bin 31,
#   max_depth -1, sin regularización L1 ni L2) y espacio de búsqueda: num_iterations 300 a 2000, learning_rate
#   0.01 a 0.1, feature_fraction 0.1 a 1.0, num_leaves 20 a 1024, min_data_in_leaf 20 a 3000. Fija 30
#   iteraciones bayesianas y 2 semillas por iteración.
#%% celda 14 [código]
# Parametros LightGBM

# parametros fijos del LightGBM que se pisaran con la parte variable de la BO
PARAM$lgbm$param_fijos <-  list(
  boosting= "gbdt", # puede ir  dart  , ni pruebe random_forest
  objective= "binary",
  metric= "auc",
  first_metric_only= FALSE,
  boost_from_average= TRUE,
  feature_pre_filter= FALSE,
  force_row_wise= TRUE, # para reducir warnings
  verbosity= -100,

  seed= PARAM$semillaprimigenia,

  max_depth= -1L, # -1 significa no limitar,  por ahora lo dejo fijo
  min_gain_to_split= 0, # min_gain_to_split >= 0
  min_sum_hessian_in_leaf= 0.001, #  min_sum_hessian_in_leaf >= 0.0
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

  num_iterations= 1000,
  learning_rate= 0.02,
  feature_fraction= 0.5,
  num_leaves= 150,
  min_data_in_leaf= 500
)

#%% celda 15 [texto]
Hiperparámetros que participan de la Bayesian Optimization
<br> si es un numero entero debe ir  makeIntegerParam
<br> si es un numero real (con decimales) debe ir  makeNumericParam

#%% celda 16 [código]
# Aqui se cargan los bordes de los hiperparametros de la BO
PARAM$hypeparametertuning$hs <- makeParamSet(
  makeIntegerParam("num_iterations", lower= 300L, upper= 2000L),
  makeNumericParam("learning_rate", lower= 0.01, upper= 0.1),
  makeNumericParam("feature_fraction", lower= 0.1, upper= 1.0),
  makeIntegerParam("num_leaves", lower= 20L, upper= 1024L),
  makeIntegerParam("min_data_in_leaf", lower= 20L, upper= 3000L)
)

#%% celda 17 [código]
PARAM$hyperparametertuning$iteraciones <- 30 # iteraciones bayesianas

# cuantas semillas usa CADA iteracion de la BO (1 o 2; mas semillas = mucho mas lento)
PARAM$hyperparametertuning$cant_semillas <- 2

# [Anotación · líneas 237–255] ganancia_acumulada (suma +780.000 por BAJA+2 y −20.000 por el resto en orden de
#   probabilidad descendente) y escribir_zulip (un numero_de_cliente por línea, sin encabezado ni notación
#   científica).
#%% celda 18 [texto]
### Funciones auxiliares

#%% celda 19 [código]
# ganancia acumulada: ordeno de mayor a menor probabilidad
#  y voy sumando +780000 por cada BAJA+2 y -20000 por cada uno que no lo es
# el elemento N del resultado es la ganancia de enviar estimulo a los N primeros

ganancia_acumulada <- function( pprob, pes_baja2 ) {
  cumsum( ifelse( pes_baja2[ order(-pprob) ], 780000, -20000 ) )
}

#%% celda 20 [código]
# escribe un archivo para Zulip: solo numero_de_cliente, sin encabezado,
#  sin notacion cientifica (cuidado con 48000000 y 31100000)

escribir_zulip <- function( pids, parchivo ) {
  writeLines( format( pids, scientific= FALSE, trim= TRUE ), parchivo )
}

# [Anotación · líneas 257–286] Crea exp/HT6005 como carpeta de trabajo y avisa si ya existe bayesiana.RDATA
#   (en ese caso la búsqueda se retoma). Lee competencia_01.csv.gz y verifica que los meses de PARAM existan y
#   que eval_mes tenga BAJA+2.
#%% celda 21 [texto]
# Super importante Ana, el preprocesamiento!!

#%% celda 22 [código]
# carpeta de trabajo

setwd(file.path(BASE, "exp"))
experimento_folder <- paste0("HT", PARAM$experimento)
dir.create(experimento_folder, showWarnings=FALSE)
setwd(file.path(BASE, "exp", experimento_folder))

if( file.exists("bayesiana.RDATA") )
  cat("ATENCION: ya existe bayesiana.RDATA en esta carpeta, la BO se va a retomar.\n",
      "Si es una corrida nueva, cambie PARAM$experimento\n")

#%% celda 23 [código]
# lectura del dataset
dataset <- fread(file.path(BASE, "datasets", "competencia_01.csv.gz"), stringsAsFactors= TRUE)

#%% celda 24 [código]
# controlo que los meses de PARAM tengan sentido
meses <- dataset[, list( N= .N, baja2= sum(clase_ternaria == "BAJA+2", na.rm= TRUE)), foto_mes]
print( meses )

stopifnot( all( PARAM$train_final %in% meses$foto_mes ) )
stopifnot( PARAM$future %in% meses$foto_mes )
stopifnot( meses[ foto_mes == PARAM$eval_mes, baja2 ] > 0 )   # eval_mes debe tener BAJA+2

if( PARAM$future != max(meses$foto_mes) )
  cat( "ATENCION: PARAM$future no es el ultimo mes del dataset\n" )

# [Anotación · líneas 288–317] Variables de aguinaldo: mes_aguinaldo, payroll_ratio (mpayroll sobre el
#   promedio de las dos filas anteriores del cliente), cobra_aguinaldo (mes de aguinaldo y cociente entre 1.3 y
#   2.0) y mpayroll_sin_sac (mpayroll / 1.5 cuando cobra_aguinaldo es 1).
#%% celda 25 [texto]
### Aguinaldo 
En junio (y diciembre) el sueldo depositado salta por el aguinaldo.

#%% celda 26 [código]

setorder(dataset, numero_de_cliente, foto_mes)

# 1. mes en que se paga aguinaldo (junio y diciembre)
dataset[, mes_aguinaldo := as.integer(foto_mes %% 100 %in% c(6, 12))]

# 2. payroll promedio de los 2 meses anteriores (solo pasado)
dataset[, payroll_prev := (shift(mpayroll, 1) + shift(mpayroll, 2)) / 2, by= numero_de_cliente]

# 3. cuanto salto el sueldo contra el pasado
dataset[, payroll_ratio := fifelse(payroll_prev > 0, mpayroll / payroll_prev, NA_real_)]

# 4. cobra aguinaldo: mes de aguinaldo y el sueldo sube entre 30% y 100%
#    (mismo criterio que el notebook de polars)
dataset[, cobra_aguinaldo := as.integer(
  mes_aguinaldo == 1 & !is.na(payroll_ratio) & payroll_ratio >= 1.3 & payroll_ratio <= 2.0
)]

# 5. payroll sin aguinaldo: el SAC es medio sueldo, entonces divido por 1.5
dataset[, mpayroll_sin_sac := fifelse(cobra_aguinaldo == 1, mpayroll / 1.5, mpayroll)]

dataset[, payroll_prev := NULL]

# control: cuantos clientes cobran aguinaldo por mes
dataset[, list(cobran= sum(cobra_aguinaldo), clientes= .N), foto_mes]

# [Anotación · líneas 319–353] Lag 1 y delta 1 de todas las columnas numéricas salvo numero_de_cliente,
#   foto_mes y clase_ternaria. El orden 2 no se calcula porque PARAM$fe$lag2 es FALSE.
#%% celda 27 [texto]
### lags y delta-lags

#%% celda 28 [código]
# 
# 1. Ordenar por cliente y mes
setorder(dataset, numero_de_cliente, foto_mes)

# 2. Columnas a transformar: excluyo identificadores, mes y clase
cols_excluir <- c("numero_de_cliente", "foto_mes", "clase_ternaria")
cols_features <- setdiff(names(dataset), cols_excluir)

# 3. Solo las columnas numericas
cols_features <- cols_features[sapply(dataset[, ..cols_features], is.numeric)]
cat("Cantidad de columnas numericas para lag/delta:", length(cols_features), "\n")

# 4. Lags de orden 1 (y 2 si PARAM$fe$lag2 es TRUE)
cols_lag1 <- paste0(cols_features, "_lag1")
dataset[, (cols_lag1) := shift(.SD, n= 1, type= "lag"), by= numero_de_cliente, .SDcols= cols_features]

if (PARAM$fe$lag2) {
  cols_lag2 <- paste0(cols_features, "_lag2")
  dataset[, (cols_lag2) := shift(.SD, n= 2, type= "lag"), by= numero_de_cliente, .SDcols= cols_features]
}

# 5. Delta-lags
for (i in seq_along(cols_features)) {
  col <- cols_features[i]
  set(dataset, j= paste0(col, "_delta1"), value= dataset[[col]] - dataset[[cols_lag1[i]]])
  if (PARAM$fe$lag2)
    set(dataset, j= paste0(col, "_delta2"), value= dataset[[col]] - dataset[[cols_lag2[i]]])
}

cat("Lags y deltas generados. Columnas totales:", ncol(dataset), "\n")
gc(full= TRUE, verbose= FALSE)

# [Anotación · líneas 355–385] Bloque de máximo, mínimo y promedio contra el mes anterior, desactivado
#   (PARAM$fe$minmaxmean en FALSE). Crea clase01 (1 para BAJA+1 y BAJA+2) y campos_buenos (todas las columnas
#   salvo clase_ternaria, clase01, azar y training).
#%% celda 29 [texto]
### (Opcional) máximo, mínimo y promedio contra el mes anterior

#%% celda 30 [código]
PARAM$fe$minmaxmean <- FALSE

if( PARAM$fe$minmaxmean ) {
  for (i in seq_along(cols_features)) {
    col <- cols_features[i]
    actual   <- dataset[[col]]
    anterior <- dataset[[cols_lag1[i]]]
    set(dataset, j= paste0(col, "_max"),  value= pmax(actual, anterior))
    set(dataset, j= paste0(col, "_min"),  value= pmin(actual, anterior))
    set(dataset, j= paste0(col, "_mean"), value= (actual + anterior) / 2)
  }
  cat("max/min/mean generados. Columnas totales:", ncol(dataset), "\n")
  gc(full= TRUE, verbose= FALSE)
}

#%% celda 31 [código]
# paso la clase a binaria que tome valores {0,1}  enteros
#  BAJA+1 y BAJA+2  son  1,   CONTINUA es 0
dataset[, clase01 := ifelse(clase_ternaria %in% c("BAJA+2","BAJA+1"), 1L, 0L)]

# los campos que se van a utilizar
campos_buenos <- setdiff(
  colnames(dataset),
  c("clase_ternaria", "clase01", "azar", "training")
)

length(campos_buenos)

# [Anotación · líneas 387–409] Datos de la búsqueda: sortea la columna azar con set.seed(992720, kind =
#   "L'Ecuyer-CMRG") y arma dtrain_bo con las filas de 202103–202105 que tienen clase01 = 1 o azar menor o igual
#   a 0.25. El conjunto de evaluación es 202106 completo, con la marca de BAJA+2. Toma las 2 primeras semillas
#   de la lista.
#%% celda 32 [texto]
## Bayesian Optimization

#%% celda 33 [código]
# datos de entrenamiento de la BO, con undersampling de los CONTINUA
set.seed(PARAM$semillaprimigenia, kind = "L'Ecuyer-CMRG")
dataset[, azar := runif(nrow(dataset))]

dtrain_bo <- lgb.Dataset(
  data= data.matrix(dataset[foto_mes %in% PARAM$train &
                            (azar <= PARAM$trainingstrategy$undersampling | clase01 == 1L),
                            campos_buenos, with= FALSE]),
  label= dataset[foto_mes %in% PARAM$train &
                 (azar <= PARAM$trainingstrategy$undersampling | clase01 == 1L), clase01],
  free_raw_data= FALSE
)

# datos de evaluacion: el mes con BAJA+2 conocido, completo
dtest_bo     <- data.matrix(dataset[foto_mes %in% PARAM$eval_mes, campos_buenos, with= FALSE])
es_baja2_bo  <- dataset[foto_mes %in% PARAM$eval_mes, clase_ternaria %in% "BAJA+2"]
semillas_bo  <- PARAM$semillas[ 1:PARAM$hyperparametertuning$cant_semillas ]

nrow(dtrain_bo)

# [Anotación · líneas 411–437] Función objetivo EstimarGanancia_lightgbm: combina los parámetros fijos con los
#   que propone la búsqueda, entrena un modelo por cada una de las 2 semillas, predice 202106 y calcula la curva
#   de ganancia en los cortes de 8.000 a 15.000. Devuelve el máximo de la curva promedio de las semillas.
#%% celda 34 [código]
EstimarGanancia_lightgbm <- function(x) {
  # 1. Combinar hiperparametros fijos + los que prueba la BO
  param_completo <- modifyList(PARAM$lgbm$param_fijos, x)

  # 2. Una curva de ganancia por semilla
  curvas <- c()
  for (semilla in semillas_bo) {
    modelo <- lgb.train(
      data= dtrain_bo,
      param= modifyList(param_completo, list(seed= semilla))
    )
    pred <- predict(modelo, dtest_bo)
    curvas <- rbind(curvas, ganancia_acumulada(pred, es_baja2_bo)[PARAM$cortes_eval])
  }

  # 3. Mejor punto de la curva promedio
  ganancia <- max(colMeans(curvas))

  message(format(Sys.time(), "%a %b %d %X %Y"),
          " Ganancia: ", format(ganancia, big.mark= ",", scientific= FALSE))

  rm(modelo)
  gc(full= TRUE, verbose= FALSE)

  return(ganancia)
}

# [Anotación · líneas 439–486] Configura mlrMBO: función de un objetivo a maximizar, marcada como ruidosa;
#   guardado del estado cada 600 segundos en bayesiana.RDATA; 30 iteraciones; criterio de expected improvement;
#   modelo sustituto regr.km con covarianza matern3_2. Ejecuta mbo, o mboContinue si ya existe bayesiana.RDATA.
#%% celda 35 [código]
# Aqui comienza la configuracion de la Bayesian Optimization

# en este archivo quedan la evolucion binaria de la BO
kbayesiana <- "bayesiana.RDATA"

funcion_optimizar <- EstimarGanancia_lightgbm # la funcion que voy a maximizar

configureMlr(show.learner.output= FALSE)

obj.fun <- makeSingleObjectiveFunction(
  fn= funcion_optimizar,
  minimize= FALSE, # estoy Maximizando la ganancia
  noisy= TRUE,
  par.set= PARAM$hypeparametertuning$hs,
  has.simple.signature= FALSE # paso los parametros en una lista
)

# cada 600 segundos guardo el resultado intermedio
ctrl <- makeMBOControl(
  save.on.disk.at.time= 600,
  save.file.path= kbayesiana
)

# indico la cantidad de iteraciones que va a tener la Bayesian Optimization
ctrl <- setMBOControlTermination(
  ctrl,
  iters= PARAM$hyperparametertuning$iteraciones
)

ctrl <- setMBOControlInfill(ctrl, crit= makeMBOInfillCritEI())

# establezco la funcion que busca el maximo
surr.km <- makeLearner(
  "regr.km",
  predict.type= "se",
  covtype= "matern3_2",
  control= list(trace= TRUE)
)

#%% celda 36 [código]
# inicio la optimizacion bayesiana, retomando si ya existe

if (!file.exists(kbayesiana)) {
  bayesiana_salida <- mbo(obj.fun, learner= surr.km, control= ctrl)
} else {
  bayesiana_salida <- mboContinue(kbayesiana) # retomo en caso que ya exista
}

# [Anotación · líneas 488–527] Pasa el historial de la búsqueda a una tabla, la ordena por y descendente y la
#   graba en BO_log.txt (separado por tabulaciones). Guarda los hiperparámetros de la primera fila y su ganancia
#   en PARAM y en PARAM.yml. Arma param_normalizado multiplicando min_data_in_leaf por
#   undersampling_final/undersampling.
#%% celda 37 [código]
# almaceno los resultados de la Bayesian Optimization
# y capturo los mejores hiperparametros encontrados

tb_bayesiana <- as.data.table(bayesiana_salida$opt.path)
tb_bayesiana[, iter := .I]

# ordeno en forma descendente por ganancia = y
setorder(tb_bayesiana, -y)

fwrite( tb_bayesiana, file= "BO_log.txt", sep= "\t" )

# los mejores hiperparametros son los que quedaron en el registro 1 de la tabla
PARAM$out$lgbm$mejores_hiperparametros <- as.list(tb_bayesiana[
  1,
  setdiff(colnames(tb_bayesiana),
    c("y","dob","eol","error.message","exec.time","ei","error.model",
      "train.time","prop.type","propose.time","se","mean","iter")),
  with= FALSE
])

PARAM$out$lgbm$y <- tb_bayesiana[1, y]

print(PARAM$out$lgbm$mejores_hiperparametros)
cat("Ganancia BO:", format(PARAM$out$lgbm$y, big.mark= ",", scientific= FALSE), "\n")

write_yaml( PARAM, file= "PARAM.yml")

#%% celda 38 [código]
param_final <- modifyList(PARAM$lgbm$param_fijos,
  PARAM$out$lgbm$mejores_hiperparametros)

# este punto es muy SUTIL: la BO entreno con un undersampling,
#  los modelos de aqui en adelante entrenan con undersampling_final
#  min_data_in_leaf se escala segun la proporcion de datos
param_normalizado <- copy(param_final)
param_normalizado$min_data_in_leaf <- round(param_final$min_data_in_leaf *
  PARAM$trainingstrategy$undersampling_final / PARAM$trainingstrategy$undersampling)

param_normalizado

# [Anotación · líneas 529–568] Evaluación local: entrena un modelo por cada una de las 10 semillas con
#   202103–202105 submuestreado, predice 202106 y guarda la curva de ganancia por corte; calcula media y desvío
#   entre semillas, los graba en curvas_evaluacion_local.txt, toma como mejor_envio el corte de mayor ganancia
#   media y grafica la curva.
#%% celda 39 [texto]
## Evaluación local 

#%% celda 40 [código]
dtrain_eval <- lgb.Dataset(
  data= data.matrix(dataset[foto_mes %in% PARAM$train & (azar <= PARAM$trainingstrategy$undersampling_final | clase01 == 1L), campos_buenos, with= FALSE]),
  label= dataset[foto_mes %in% PARAM$train & (azar <= PARAM$trainingstrategy$undersampling_final | clase01 == 1L), clase01]
)

curvas <- data.table(envios= PARAM$cortes_eval)

for (semilla in PARAM$semillas) {
  modelo <- lgb.train(
    data= dtrain_eval,
    param= modifyList(param_normalizado, list(seed= semilla))
  )
  pred <- predict(modelo, dtest_bo)
  curvas[, (paste0("s", semilla)) := ganancia_acumulada(pred, es_baja2_bo)[PARAM$cortes_eval]]
  cat(format(Sys.time(), "%X"), "semilla", semilla, "lista\n")
}

rm(modelo, dtrain_eval)
gc(full= TRUE, verbose= FALSE)

curvas[, media  := rowMeans(.SD),     .SDcols= patterns("^s")]
curvas[, desvio := apply(.SD, 1, sd), .SDcols= patterns("^s")]
fwrite(curvas, "curvas_evaluacion_local.txt", sep= "\t")

options(scipen= 999)
print(curvas[, list(envios, media, desvio)])

mejor_envio <- curvas[which.max(media), envios]
cat(">> Mejor corte promedio:", mejor_envio,
    " | ganancia media:", format(curvas[which.max(media), media], big.mark= ","), "\n")

#%% celda 41 [código]
plot(curvas$envios, curvas$media / 1e6, type= "l", lwd= 2,
     xlab= "envios", ylab= "ganancia media (millones)",
     main= paste("Evaluacion local en", PARAM$eval_mes))
abline(v= mejor_envio, lty= 2, col= "red")

# [Anotación · líneas 570–612] Modelos del experimento 6005 para 202108: entrena un modelo por cada una de las
#   10 semillas con 202103–202106 (el mismo 25% de CONTINUA para todos) y guarda una columna de probabilidades
#   por semilla en predicciones_futuro.csv, retomando si el archivo existe. Guarda la importancia de variables
#   del último modelo en impo.txt.
#%% celda 42 [texto]
## Modelos finales

#%% celda 43 [código]
dtrain_final <- lgb.Dataset(
  data= data.matrix(dataset[foto_mes %in% PARAM$train_final & (azar <= PARAM$trainingstrategy$undersampling_final | clase01 == 1L), campos_buenos, with= FALSE]),
  label= dataset[foto_mes %in% PARAM$train_final & (azar <= PARAM$trainingstrategy$undersampling_final | clase01 == 1L), clase01]
)

dfuture  <- dataset[foto_mes %in% PARAM$future]
X_future <- data.matrix(dfuture[, campos_buenos, with= FALSE])

archivo_pred <- "predicciones_futuro.csv"

if (file.exists(archivo_pred)) {
  tb_pred <- fread(archivo_pred)
  stopifnot( identical(tb_pred$numero_de_cliente, dfuture$numero_de_cliente) )
} else {
  tb_pred <- dfuture[, list(numero_de_cliente)]
}

for (semilla in PARAM$semillas) {
  col_pred <- paste0("pred_", semilla)

  if (col_pred %in% colnames(tb_pred)) {
    cat("Saltando semilla (ya existe):", semilla, "\n")
    next
  }

  modelo <- lgb.train(
    data= dtrain_final,
    param= modifyList(param_normalizado, list(seed= semilla))
  )
  tb_pred[, (col_pred) := predict(modelo, X_future)]

  fwrite(tb_pred, archivo_pred)
  cat(format(Sys.time(), "%X"), "semilla", semilla, "guardada\n")
}

# importancia de variables del ultimo modelo
fwrite(as.data.table(lgb.importance(modelo)), "impo.txt", sep= "\t")
rm(modelo)
gc(full= TRUE, verbose= FALSE)

# [Anotación · líneas 614–655] Archivos del experimento 6005: toma cortes de a 500 alrededor de mejor_envio
#   (hasta 1.500 a cada lado, dentro de 8.000 a 15.000) y escribe un archivo por semilla y por corte en zulip/.
#   Luego promedia las probabilidades de las semillas y escribe zulip/FINAL_e6005_N<corte>.csv con
#   PARAM$envio_final = mejor_envio.
#%% celda 44 [texto]
## Archivos para Zulip

#%% celda 45 [código]
options(scipen= 999)
dir.create("zulip", showWarnings= FALSE)

# cortes alrededor del mejor de la evaluacion local, dentro de [8000, 15000]
if (is.null(PARAM$envios_zulip)) {
  base <- round(mejor_envio / 500) * 500
  PARAM$envios_zulip <- unique(pmin(pmax(seq(base - 1500, base + 1500, by= 500), 8000), 15000))
}
cat("Cortes para Zulip:", PARAM$envios_zulip, "\n")

cols_pred <- grep("^pred_", colnames(tb_pred), value= TRUE)

for (col in cols_pred) {
  ids_ordenados <- tb_pred$numero_de_cliente[ order(-tb_pred[[col]]) ]
  for (envios in PARAM$envios_zulip) {
    archivo <- sprintf("zulip/e%d_N%05d_s%s.csv", PARAM$experimento, envios, sub("pred_", "", col))
    escribir_zulip(ids_ordenados[1:envios], archivo)
  }
}

cat(length(list.files("zulip")), "archivos generados en",
    paste0(getwd(), "/zulip"), "\n")

#%% celda 46 [texto]
**Archivo final:** promedio de las probabilidades de todas las semillas, un solo archivo.
<br>Por defecto usa el mejor corte local. **Cuando sepas qué corte dio mejor en el bot, cambiá `PARAM$envio_final` y volvé a correr esta celda.**

#%% celda 47 [código]
PARAM$envio_final <- mejor_envio   # <- cambiar por el mejor corte segun el bot

tb_pred[, prob_ensamble := rowMeans(.SD), .SDcols= cols_pred]
ids_ensamble <- tb_pred$numero_de_cliente[ order(-tb_pred$prob_ensamble) ]

archivo_final <- sprintf("zulip/FINAL_e%d_N%05d.csv", PARAM$experimento, PARAM$envio_final)
escribir_zulip(ids_ensamble[1:PARAM$envio_final], archivo_final)
tb_pred[, prob_ensamble := NULL]

cat("Archivo final:", archivo_final, "\n")

# [Anotación · líneas 657–682] Control de formato de todos los archivos de zulip/: cantidad de líneas entre
#   8.000 y 15.000, sólo dígitos, sin repetidos y clientes de 202108. Guarda PARAM en PARAM.yml y registra la
#   hora.
#%% celda 48 [código]
# control de formato de TODOS los archivos de Zulip
ids_futuro <- dfuture$numero_de_cliente

control <- rbindlist(lapply(list.files("zulip", full.names= TRUE), function(archivo) {
  lineas <- readLines(archivo)
  data.table(
    archivo     = basename(archivo),
    lineas      = length(lineas),
    en_rango    = length(lineas) >= 8000 & length(lineas) <= 15000,
    solo_numeros= all(grepl("^[0-9]+$", lineas)),   # sin encabezado ni notacion cientifica
    sin_repetir = !anyDuplicated(lineas),
    del_futuro  = all(as.numeric(lineas) %in% ids_futuro)
  )
}))

print(control)
if (control[, all(en_rango & solo_numeros & sin_repetir & del_futuro)]) {
  cat("OK: todos los archivos cumplen el formato\n")
} else {
  cat("ATENCION: hay archivos con problemas (ver tabla)\n")
}

#%% celda 49 [código]
write_yaml( PARAM, file= "PARAM.yml")
format(Sys.time(), "%a %b %d %X %Y")

# [Anotación · líneas 684–712] Prueba en 202105: entrena con 202103–202104 submuestreado y las 3 primeras
#   semillas, predice 202105 y calcula la ganancia media para 8.000 a 15.000 envíos de a 500; imprime la tabla
#   en millones y el corte de mayor media.
#%% celda 50 [texto]
##  Archivos FINAL para el bot 

#%% celda 51 [código]
stopifnot(exists("dataset"), exists("param_normalizado"))   # si falla, la sesion se reinicio

filtro_tr <- dataset$foto_mes %in% c(202103, 202104) &
             (dataset$azar <= PARAM$trainingstrategy$undersampling_final | dataset$clase01 == 1L)

dtrain_may <- lgb.Dataset(
  data  = data.matrix(dataset[filtro_tr, campos_buenos, with = FALSE]),
  label = dataset[filtro_tr, clase01]
)
X_may     <- data.matrix(dataset[foto_mes == 202105, campos_buenos, with = FALSE])
baja2_may <- dataset[foto_mes == 202105, clase_ternaria %in% "BAJA+2"]

cortes_may <- seq(8000, 15000, by = 500)
curvas_may <- data.table(envios = cortes_may)

for (s in PARAM$semillas[1:3]) {
  m <- lgb.train(data = dtrain_may, param = modifyList(param_normalizado, list(seed = s)))
  curvas_may[, (paste0("s", s)) := ganancia_acumulada(predict(m, X_may), baja2_may)[cortes_may]]
  cat(format(Sys.time(), "%X"), "semilla", s, "lista\n")
}

curvas_may[, media := rowMeans(.SD), .SDcols = patterns("^s")]
options(scipen = 999)
print(curvas_may[, list(envios, media_millones = round(media / 1e6, 1))])
cat(">> Mejor corte en MAYO:", curvas_may[which.max(media), envios], "\n")

# [Anotación · líneas 714–728] Relee predicciones_futuro.csv, promedia las columnas pred_* y escribe
#   zulip/FINAL_e6005_N<N>.csv para N de 9.500 a 12.000 de a 250.
#%% celda 52 [texto]
Prueba en zona del sweet spot

#%% celda 53 [código]
options(scipen = 999)
tb_pred   <- fread("predicciones_futuro.csv")
cols_pred <- grep("^pred_", names(tb_pred), value = TRUE)
tb_pred[, prob_ensamble := rowMeans(.SD), .SDcols = cols_pred]
ids_ensamble <- tb_pred$numero_de_cliente[order(-tb_pred$prob_ensamble)]

for (N in seq(9500, 12000, by = 250)) {
  archivo <- sprintf("zulip/FINAL_e6005_N%05d.csv", N)
  writeLines(format(ids_ensamble[1:N], scientific = FALSE, trim = TRUE), archivo)
  cat(archivo, ":", length(readLines(archivo)), "lineas\n")
}
```


## Explicaciones del alumno (texto original)

### README.md

> # Primera Competencia DMEyF 2026 — Ana Dominguez
>
> **Entrega final:** `entrega_final/FINAL_e6019x40_N11000.csv`
> (11.000 `numero_de_cliente` de 202108, sin encabezado).
>
> ## Cómo armé mi predicción final...
>
> Es un **ensamble por promedio de 40 modelos LightGBM**. Todos tienen las mismas variables y los mismos hiperparámetros; solo cambié la semilla:
>
> | Parte | Notebook | Qué aporta |
> |---|---|---|
> | 1 | `1_hiperparametros_6005/` | Bayesian Optimization que dio los hiperparámetros (`BO_log.txt`) |
> | 2 | `2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` | 20 modelos (bagging, 20 semillas) → `exp/HT6018/predicciones_futuro.csv` |
> | 3 | `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` | 20 modelos más (20 semillas nuevas) + **promedio de los 40** → archivo final |
>
> La probabilidad final de cada cliente es el promedio simple de las probabilidades de los 40 modelos (20 del 6018 + 20 del 6019). Se ordenan de mayor a menor y se envían los primeros 11.000.
>
> ### Detalle del modelo (6018 y 6019 son idénticos salvo las semillas)
> - **Clase:** `clase01` = BAJA+1 + BAJA+2.
> - **Meses:** entrenamiento final 202103–202106, predicción 202108 (202107 no se usa: no tiene clase).
> - **Variables:**
>   - aguinaldo  (`mpayroll_sin_sac`, `cobra_aguinaldo`);
>   - lags y deltas de orden 1 para todas las variables;
>   - lag y delta de orden 2 para una lista fija de 78 variables (escrita en la notebook);
>   - 62 rankings "con cero fijo" dentro de cada mes (`rk_*`): 0 → 0, positivos en (0,1], negativos en [−1,0).
> - **Entrenamiento:** cada modelo usa todas las bajas + un 25% de los CONTINUA, elegido con su propia semilla (`set.seed(semilla, kind="Mersenne-Twister")`).
> - **Hiperparámetros:** la mejor fila de `exp/HT6005/BO_log.txt` (num_iterations, learning_rate, feature_fraction, num_leaves, min_data_in_leaf).
> - **Semillas:**
>   - 6018: las 10 de `PARAM$semillas` + 10 de `set.seed(992720)`;
>   - 6019: 20 nuevas de `set.seed(992720 + 6019)`, sin repetir ninguna del 6018.
>
> ### De dónde sale cada parte
> Las variables del 6018 se fueron sumando en experimentos anteriores: 6006 (bagging), 6011 (orden 2 selectivo), 6016 (rankings), 6018 (rankings con cero fijo). Esas notebooks **no hacen falta para replicar**: la notebook del 6018 ya incluye todo ese feature engineering, y ninguna de ellas genera un archivo que use la entrega final. Lo único que se reutiliza de un experimento anterior son los hiperparámetros del 6005.
>
> ## Cómo replicar (en orden)
>
> Las notebooks están en **R** y esperan la estructura del curso en Google Cloud: `BASE <- ~/buckets/b1`. Cada notebook escribe en `~/buckets/b1/exp/HTxxxx/`. El dataset se descarga solo desde la URL de la competencia.
>
> Máquina usada: Google Cloud, e2 custom de 8 vCPU y 64 GB de RAM (template del curso `to-064ram-08vcpu`).
>
> **Paso 1 — Hiperparámetros (6005).** La notebook `1_hiperparametros_6005/competencia01_gcp_6005.ipynb` corre una Bayesian Optimization de 30 iteraciones (entrena 202103–202105 con 25% de CONTINUA, mide la ganancia en 202106) y escribe `exp/HT6005/BO_log.txt`. La mejor fila, que es la que usan el 6018 y el 6019, es:
>
> | num_iterations | learning_rate | feature_fraction | num_leaves | min_data_in_leaf |
> |---|---|---|---|---|
> | 1168 | 0.01315415 | 0.3446377 | 61 | 966 |
>
>  Hay dos opciones:
> - **A (rápida, la recomendada):** copiar `1_hiperparametros_6005/BO_log.txt` a `~/buckets/b1/exp/HT6005/BO_log.txt`. Las notebooks 6018 y 6019 solo leen la mejor fila de ese archivo.
> - **B (completa):** correr la notebook de `1_hiperparametros_6005/`, que genera ese mismo `BO_log.txt`. Tarda varias horas.
>
> **Paso 2 — 6018.** Abrir `competencia01_gcp_6018_rank_cero_fijo.ipynb` y hacer **Run All** (~1,5–2,5 h).
> Genera `exp/HT6018/predicciones_futuro.csv`, con las probabilidades de los 20 modelos para 202108.
>
> **Paso 3 — 6019 y archivo final.** Abrir `competencia01_gcp_6019_6018_semillas_nuevas.ipynb` y hacer **Run All** (~1,5–2,5 h).
> Entrena los 20 modelos nuevos y, en la última celda de código, promedia con los 20 del 6018 (lee `exp/HT6018/predicciones_futuro.csv`) y escribe:
>
> ```
> exp/HT6019/zulip/FINAL_e6019x40_N11000.csv   <- la entrega final
> ```
>
> **Verificación:** comparar ese archivo con `entrega_final/FINAL_e6019x40_N11000.csv`.
> ## Lo que probé en el camino
>
> En el camino hubo muchos (MUCHOS) experimentos que no me salieron, o que por lo menos me tiraban para atrás, tanto en el bot como en mis métricas internas (la ganancia en junio, que usé como mes de prueba). Así que acá dejo el listado para los docentes y los compañeros del curso, por si a alguien le sirve saber qué caminos no conviene repetir.
>
> | Exp | Qué probé | Ganancia (bot) | ¿Me lo quedé? | Por qué |
> |---|---|---|---|---|
> | 6005 | Modelo base: marca de aguinaldo, lags y deltas de orden 1, Bayesian Optimization propia, 10 semillas | 108,82 | Sí, como base | Es el punto de partida. Sus hiperparámetros fueron los que usé hasta el final. |
> | 6006 | Bagging: 20 modelos, cada uno entrenado con su propio 25% de los CONTINUA | 109,04 | **Sí** | Antes, todos los modelos veían el mismo 25% de los clientes que se quedan. Con un sorteo distinto para cada modelo, entre los 20 ven a casi todos, y al promediar se compensan sus errores. En junio ganó 4 M contra la versión sin bagging. |
> | 6007 | Más variables armadas a mano dentro de cada mes | 97,32 | No | Muchas columnas nuevas que repetían información que el modelo ya tenía. En vez de ayudar, le dieron más lugares donde encontrar patrones casuales del entrenamiento. |
> | 6008 | Lag 2 y delta 2 para **todas** las variables | 99,83 | No | Para agosto, el delta 2 compara contra junio, que es el mes del aguinaldo. Sueldos y saldos de junio están inflados, entonces en agosto muchísimos clientes "parecen" haber caído, y el modelo los confunde con clientes que se van. |
> | 8001 | Otra Bayesian Optimization, con otros hiperparámetros | 97,60 | No | Los hiperparámetros que mejor andan en el mes donde se eligen tienen parte de suerte. Ganaban en junio pero no se sostenían en agosto. |
> | 6010 | Ensamble mezclando modelos con configuraciones distintas | 105,74 / 101,20 | No | Promediar solo ayuda si todos los modelos son buenos y se equivocan en cosas distintas. Acá los más flojos arrastraron hacia abajo al mejor. |
> | 6011 | Lag 2 y delta 2 **solo** para 78 variables que no "mienten" en agosto | 109,56 | **Sí** | Hice un diagnóstico variable por variable: comparé cuánto se mueve agosto contra un mes normal. El orden 2 quedó solo donde agosto se ve como un mes común, y afuera las variables tocadas por el aguinaldo. |
> | 6012 | Elegir hiperparámetros midiendo en mayo en vez de junio | 103,73 | No | La idea era tener junio como examen limpio, pero la bayesiana tuvo un mes menos para aprender, y lo que eligió no se trasladó bien a agosto. |
> | 6013 | 6006 + 6011 juntos (40 modelos) | 109,29 | No | Dio lo mismo que el 6011 solo. Mezclar con un modelo un poco peor no suma. |
> | 6014 | Sacar el aguinaldo también de junio en el entrenamiento | 107,58 | No | Al "limpiar" junio, las filas de entrenamiento dejaron de parecerse a lo que el modelo ve en agosto, y perdí información real de ese mes. |
> | 6015 | El 6011 con semillas nuevas (40 modelos) | 109,48 | No lo usé, pero sirvió como control | Dio igual que el 6011. Confirmó que la mejora era real y no suerte de las semillas. |
> | 6016 | 62 rankings de montos dentro de cada mes | 111,65 | **Sí** | Por la inflación, todos los montos en pesos suben mes a mes, así que un mismo sueldo "significa" distinto en marzo que en agosto. El ranking compara a cada cliente con los demás del mismo mes, y eso borra la inflación y el aguinaldo. |
> | 6017 | Variables "dejó de…" (cobrar sueldo, débitos automáticos, tarjeta, canales) | 111,32 | No | La idea tenía sentido, pero esa información ya estaba en los lags, los deltas y `ctrx_quarter`. Para el modelo no era nada nuevo. |
> | 6018 | Rankings con "cero fijo" | **112,39** | **Sí** | En el ranking común, "no tener el producto" quedaba pegado a "tener muy poco". Con cero fijo, el 0 es siempre 0, los positivos van entre 0 y 1 y las deudas entre −1 y 0. Tres situaciones distintas, bien separadas. |
> | 6019x40 | El 6018 con 20 semillas nuevas, promediando los 40 modelos | 110,47 | **Sí, es la entrega final** | Es el mismo modelo que el 6018, promediado el doble de veces. Las semillas nuevas coinciden con las viejas en 10.812 de los 11.000 clientes enviados, así que la diferencia con el 6018 es ruido, y con 40 modelos la suerte de cada uno pesa la mitad. |
> | 6022 | La receta de entrenamiento de la cátedra: sin undersampling, learning rate 0,005, bayesiana de 3 hiperparámetros, 10 modelos distintos | 105,02 | No | Con un learning rate tan bajo, seguramente necesitaba más árboles de los que le dejé probar a la bayesiana. Además, mis variables y mi forma de entrenar venían ajustadas juntas desde el principio. No me dio el tiempo para afinarla. |
>
> **Sobre el corte:** probé desde 9.500 hasta 14.000 clientes. El 11.000 fue el mejor de forma consistente en todos los modelos.
>
> **Lo que me llevo:** lo que más mejoró fueron las **variables que corrigen efectos del calendario**: el aguinaldo, la inflación y los meses que "mienten". Cambiar hiperparámetros o la forma de entrenar siempre me dio peor. Y aprendí a no perseguir diferencias chiquitas entre envíos: por eso elegí la versión de 40 modelos, la más estable, aunque el 6018 solo haya tenido un número un poco más alto.
> ### Notas
> - Las celdas que comparan contra otros experimentos (6006, 6016) son solo informativas. Si esos archivos no existen, se saltean solas!
> - LightGBM corre multihilo, así que en otra máquina puede haber diferencias ínfimas en las probabilidades y, como mucho, un puñado de clientes distintos cerca del corte 11.000.

