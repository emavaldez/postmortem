# micaelarr — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: micaelarr
- Repositorio: https://github.com/micaelarr/primeracompetencia
- Link posteado: https://github.com/micaelarr/primeracompetencia
- Commit: ebe30f0bc3698da0ddbae931b19d1d6b2c85137c
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/micaelarr/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/micaelarr.json

## Resumen

Repositorio con un README, un notebook de Python que genera la predicción (prediccion_final/churn_pipeline_final.ipynb), un CSV de 11.500 clientes y la carpeta optimizacion_bayesiana/ con notebooks de versiones anteriores (v3, v5, v7, v9 y v11), tres bases de Optuna y un JSON con las 6 configuraciones finales. El notebook final carga competencia_01.csv en DuckDB, pasa ccajas_depositos a NULL en 202105, imputa los nulos de tarjetas, deflacta los montos por IPC y calcula lags y deltas, sumas y cocientes, dummies de un KMeans (k = 5) y hasta 175 variables de historia de 3 meses (7 por cada una de 25 variables). Excluye variables por una lista fija y por PSI > 0,25 contra 202108 y verifica con un assert que queden 504 columnas. Entrena LightGBM con clase binaria (BAJA+1 o BAJA+2), sin submuestreo y con pesos por fila de 0,8 elevado a los meses de antigüedad: 6 configuraciones de hiperparámetros escritas en el código (según el README, los 6 trials de mayor valor de un estudio de Optuna) por 2 semillas. Mide el ensamble en 202106 entrenando con 202103–202105, reentrena con 202103–202106, promedia las probabilidades de los 12 modelos sobre 202108 y exporta los 11.500 clientes de mayor probabilidad.

**Qué entrega.** Un CSV de una columna, sin encabezado, con los 11.500 numero_de_cliente de mayor probabilidad promedio del ensamble. El repositorio incluye prediccion_final/prediccion_baja_202108_lgbm_binario_final_corte11500_20261010_140610.csv, de 11.500 filas, cuyo nombre sigue el formato que escribe el notebook final. El README nombra como archivo final prediccion_baja_202108_lgbm_binario_v11_corte11500_20261009_224353.csv (formato de nombre del notebook v11), que no está en el repositorio, y declara su SHA-256 (2d690cb3…d81b0a); el SHA-256 del CSV incluido es a50677f0…d0a858.

**Cómo se ejecuta.** Según el README (sección 3): (1) poner competencia_01.csv en la carpeta del notebook o hasta 3 niveles arriba, o definir la variable de entorno CHURN_BASE_PATH con la carpeta que lo contiene; (2) instalar los paquetes de la sección Entorno; (3) ejecutar churn_pipeline_final.ipynb de principio a fin (Run All); (4) el CSV sale en salida_final_<fecha>/ junto con meta.json y resumen_cortes.csv; (5) comparar el SHA-256 o el conjunto de IDs con el archivo entregado. Para repetir la optimización, el README indica correr churn_pipeline_v9_optuna.ipynb (copiando origen_warm_start/*.db a una carpeta modelos/ junto al dataset) y después churn_pipeline_v11_corrida_original.ipynb. El README nombra las carpetas como 01_prediccion_final/ y 02_optimizacion_bayesiana/; en el repositorio se llaman prediccion_final/ y optimizacion_bayesiana/.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: positivo = BAJA+1 o BAJA+2, negativo = CONTINUA (construir_y con target 'binario'). La ganancia se calcula contando sólo BAJA+2 como acierto.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica: los modelos se entrenan con todas las filas de los meses de entrenamiento. La función correr_experimento() contiene un assert de que la matriz tiene el 100 % de las filas de train; esa función no se llama en el notebook final.
- **Calidad de datos:** ccajas_depositos se pasa a NULL en 202105 al cargar el CSV (VARIABLES_ROTAS) y no se imputa. Los nulos de 32 columnas de montos y cantidades de Master y Visa se imputan con 0; status, delinquency y fechaalta con -1; Fvencimiento, Finiciomora y fultimo_cierre con el centinela 999999; el resto de las columnas con nulos, con la mediana de train. Se agregan los flags tiene_visa y tiene_master. Tres reportes (saltos por mes de promedio, ceros y nulos; porcentaje de nulos en train y en 202108; outliers por 3 × IQR) se imprimen y no modifican los datos.
- **Drifting:** Deflacta por IPC (índice acumulado base 100 con variaciones mensuales de 4,8; 4,1; 3,3; 3,2; 3,0 y 2,5 % para 202103–202108) las columnas de monto que no están en dólares, que pasan a tener sufijo _real. Calcula el PSI (10 cuantiles, con buckets aparte para nulos y centinela) de cada variable numérica entre train (202103–202105) y 202108 y excluye las de PSI > 0,25, los lags y deltas de las variables base excluidas y las derivadas de éstas con PSI propio > 0,10. La función de rank por mes con cero fijo está definida y no crea columnas porque VARS_RANK es una lista vacía.
- **Variables dentro del mes:** 10 sumas y cocientes (tc_consumo_total, tc_saldo_total, tc_limite_total, visa_utilizacion, master_utilizacion, tc_transacciones_total, prestamos_total, margen_neto, liquidez_total_pesos, digital_trx_total), más tc_utilizacion_total, ratio_deuda_ingreso, ratio_digital_total_trx, tiene_prestamos, tiene_payroll y prop_vida_en_banco; flags tiene_visa y tiene_master; y 5 dummies de cluster de un KMeans (k = 5, n_init = 20, semilla 214363) sobre 14 variables recortadas a los percentiles 1–99 y escaladas con RobustScaler, ajustado sólo con train.
- **Variables históricas:** lag1, lag2, delta1 y delta2 de 15 variables (VARS_LAG), exigiendo que el mes anterior esté exactamente a 1 o 2 meses; delta1 de todas las demás variables numéricas, salvo identificadores, columnas con centinela y flags; y, para 25 variables escritas en el código (VARS_HIST_FIJAS), 7 variables sobre el mes actual y los 2 anteriores: media (_m3), desvío (_s3), mínimo (_mn3), máximo (_mx3), desvío sobre media (_cv3), apartamiento del mes respecto de la media (_xvsm3) y cantidad de caídas consecutivas (_racha3). 202107 se usa sólo como historia de 202108.
- **Selección de variables:** Excluye siempre mpayroll_real, cpayroll_trx, mprestamos_personales_real y cprestamos_personales con sus lags, deltas y derivadas (los flags tiene_payroll y tiene_prestamos se conservan); excluye por PSI > 0,25; quita los 4 límites de tarjeta en nominal y mcomisiones_mantenimiento; descarta las variables de historia con PSI > 0,25. Un assert exige 504 columnas. Las 25 variables con historia están fijadas en el código; según el comentario del notebook, en la corrida original salieron de un ranking de importancia (gain) de un LightGBM entrenado en train, código que está en los notebooks v9 y v11. Según el README se probó un recorte de variables con canaritos; ese código no está en el repositorio.
- **Optimización de hiperparámetros:** El notebook final no ejecuta búsqueda: las 6 configuraciones están escritas en el código. Según el README y los notebooks de optimizacion_bayesiana/, salen de un estudio de Optuna (sampler TPE con semilla 17, almacenado en SQLite y retomado entre corridas; 60 trials completos según el README) que maximiza el máximo de la curva de ganancia suavizada (media móvil de 401 envíos) en 202106 entrenando con 202103–202105, con 3 semillas por trial, sobre learning_rate (0,01–0,1), num_leaves (8–1024), min_data_in_leaf (50–5000), feature_fraction (0,1–0,8), bagging_fraction (0,5–1), lambda_l2 (0,001–100) y num_boost_round (100–2000). Los primeros trials se encolan desde los 5 de mayor valor de estudios anteriores.
- **Hiperparámetros finales:** 6 configuraciones de LightGBM con objective = binary y bagging_freq = 1: learning_rate entre 0,0133 y 0,0192; num_leaves entre 26 y 78; min_data_in_leaf entre 766 y 3052; feature_fraction entre 0,102 y 0,157; bagging_fraction entre 0,790 y 0,995; lambda_l2 entre 0,379 y 1,494; num_boost_round entre 484 y 631. Corresponden a los trials 54, 32, 23, 26, 43 y 31; los valores completos están en configs_finales.json y en la lista CONFIGS del notebook.
- **Semillas:** numpy.random.seed(17) y sorteo de 50 semillas sin reposición entre 0 y 999.999; las 3 primeras quedan reservadas para Optuna y el ensamble usa las 2 siguientes en cada una de las 6 configuraciones (12 modelos). KMeans usa la semilla 214363 y el sampler de Optuna la 17. LightGBM corre con num_threads = cantidad de CPU de la máquina.
- **Cantidad de semillas:** 2
- **Ensamble:** Promedio de probabilidades en dos niveles, con igual peso: primero entre las 2 semillas de cada configuración y después entre las 6 configuraciones (12 modelos LightGBM).
- **Corte:** Cantidad fija escrita en el código: los 11.500 clientes de mayor probabilidad (N_ENVIOS_MANUAL = 11_500). El notebook calcula además, sobre 202106, el máximo de la curva de ganancia suavizada y una meseta a menos de 2 aciertos de ese máximo, que no intervienen en el corte exportado. Según el README, se enviaron varios cortes al leaderboard público y se eligió 11.500; el máximo en la validación de 202106 equivalía a 12.720 envíos.
- **Validación:** Un mes posterior: las 6 configuraciones se entrenan con 202103–202105 y se mide en 202106 la ganancia máxima de la curva suavizada (ventana de 401 envíos; +1.072.500 por BAJA+2 y −27.500 por cada otro envío), por configuración y para el ensamble acumulado. El backtest que entrena con 202103–202104 y evalúa en 202105 y 202106 está en el código con CORRER_BACKTEST = False.
- **Salidas:** Carpeta salida_final_<fecha>/ con prediccion_baja_202108_lgbm_binario_final_corte11500_<fecha>.csv (una columna, sin encabezado, enteros), resumen_cortes.csv (equivalente del corte en 202106 y su ganancia) y meta.json (versiones de librerías, sistema, cantidad de CPU, variante, decay, configuraciones y resumen del corte en 202106).

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Deflación por IPC, dólar o UVA (`drifting.deflacion`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Mínimos y máximos de ventana (`variables.min_max_ventana`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Técnicas sólo exploradas

- Random Forest (`modelo.random_forest`)
- Tres clases (CONTINUA, BAJA+1, BAJA+2) (`clase.multiclase`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- Genera archivos con varios cortes (`corte.varios_cortes`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README: Python 3.13 (Anaconda) en Windows 11, máquina con unos 34 GB de RAM; paquetes duckdb, pandas, numpy, scikit-learn, lightgbm, optuna, matplotlib y psutil, sin número de versión (la línea de versiones de la corrida original figura como texto a completar). El notebook final guarda versiones de librerías, sistema y cantidad de CPU en meta.json al ejecutarse; ese archivo no está en el repositorio. Los notebooks de optimizacion_bayesiana/ tienen una ruta absoluta de Windows al dataset; el notebook final la reemplaza por una búsqueda de la carpeta.

## Pasos del camino de la entrega

1. **Configuración y roles de los meses.** Ubica la carpeta de competencia_01.csv (variable de entorno CHURN_BASE_PATH o búsqueda hasta 3 niveles arriba) y asigna un rol a cada mes: 202103–202105 entrenamiento, 202106 validación, 202107 sólo historia, 202108 aplicación y 202103–202106 para el modelo final. Define la ganancia (+1.072.500 por acierto, −27.500 por envío), las variables rotas y los límites de tarjeta que se conservan en nominal. (`prediccion_final/churn_pipeline_final.ipynb` líneas 33–102)
2. **Carga del CSV en DuckDB y asignación de roles.** Crea una base DuckDB en disco con límite de memoria del 40 % de la RAM, carga el CSV con read_csv_auto, pone en NULL ccajas_depositos en 202105 y agrega la columna rol. Verifica con assert que no haya meses sin rol, que 202108 venga como 'SIN CLASE' y que train y validación no tengan clase nula. (`prediccion_final/churn_pipeline_final.ipynb` líneas 184–236; `prediccion_final/churn_pipeline_final.ipynb` líneas 239–304)
3. **Reportes de calidad e imputación.** Imprime tres reportes (variables con saltos por mes, nulos en train y aplicación, outliers por IQR) y crea la tabla etapa2 imputando los nulos de tarjetas con 0, −1 o 999.999 según la columna y el resto con la mediana de train; agrega tiene_visa y tiene_master. (`prediccion_final/churn_pipeline_final.ipynb` líneas 111–128; `prediccion_final/churn_pipeline_final.ipynb` líneas 314–361; `prediccion_final/churn_pipeline_final.ipynb` líneas 428–467)
4. **Deflactación por IPC.** Arma un índice acumulado con la variación mensual del IPC de 202103 a 202108 y divide por él los montos que no están en dólares, generando columnas _real. Se eliminan las versiones nominales salvo 4 límites de tarjeta. (`prediccion_final/churn_pipeline_final.ipynb` líneas 140–143; `prediccion_final/churn_pipeline_final.ipynb` líneas 477–515)
5. **Lags y deltas.** Con ventanas por cliente calcula lag1, lag2, delta1 y delta2 de 15 variables y delta1 del resto de las numéricas; el lag sólo se toma si el mes anterior está exactamente a 1 o 2 períodos, y si no queda NULL. (`prediccion_final/churn_pipeline_final.ipynb` líneas 145–152; `prediccion_final/churn_pipeline_final.ipynb` líneas 518–588)
6. **Variables combinadas dentro del mes.** Agrega sumas y cocientes de tarjetas, préstamos, márgenes, liquidez y canales digitales con las macros suma_sin_null y ratio_sin_null, y los flags tiene_prestamos y tiene_payroll. Después pasa las tablas a un DataFrame de pandas por rol en float32 y cierra DuckDB. (`prediccion_final/churn_pipeline_final.ipynb` líneas 591–627; `prediccion_final/churn_pipeline_final.ipynb` líneas 692–717)
7. **Cluster de clientes con KMeans.** Ajusta un KMeans de 5 grupos sobre 14 variables de train, recortadas a los percentiles 1–99, imputadas con la mediana y escaladas con RobustScaler; asigna el cluster al resto de los meses y lo agrega como 5 dummies. (`prediccion_final/churn_pipeline_final.ipynb` líneas 728–772)
8. **PSI contra 202108 y selección de columnas.** Calcula el PSI de cada variable numérica entre train y 202108 y arma columnas_modelo excluyendo las 4 variables de payroll y préstamos personales con sus lags, deltas y derivadas, las variables con PSI > 0,25 con sus lags y deltas, y las derivadas de éstas con PSI propio > 0,10. (`prediccion_final/churn_pipeline_final.ipynb` líneas 811–819; `prediccion_final/churn_pipeline_final.ipynb` líneas 880–962)
9. **Variables de historia sobre 3 meses.** Para 25 variables fijas calcula media, desvío, mínimo, máximo, desvío relativo, apartamiento del mes contra la media y racha de caídas sobre el mes actual y los 2 anteriores (NaN si falta alguno), y conserva las que tienen PSI ≤ 0,25 entre train y 202108. (`prediccion_final/churn_pipeline_final.ipynb` líneas 1300–1392)
10. **Columnas finales y pesos por mes.** Quita de columnas_modelo los 4 límites de tarjeta en nominal y mcomisiones_mantenimiento, suma las variables de historia y exige 504 columnas con un assert. Fija el decay en 0,8: cada fila pesa 0,8 elevado a los meses que la separan del último mes del conjunto de entrenamiento. (`prediccion_final/churn_pipeline_final.ipynb` líneas 1177–1186; `prediccion_final/churn_pipeline_final.ipynb` líneas 1401–1417)
11. **Procedencia de los hiperparámetros.** Las 6 configuraciones están escritas en la lista CONFIGS y en configs_finales.json. Según el README, son los 6 trials de mayor valor del estudio de Optuna lgbm_binario, cuyos trials 0–36 generó el notebook v9 y 37–61 el notebook v11, que retoma la misma base y arma la lista a partir del estudio. (`prediccion_final/churn_pipeline_final.ipynb` líneas 1438–1526; `optimizacion_bayesiana/configs_finales.json` líneas 1–89; `optimizacion_bayesiana/churn_pipeline_v9_optuna.ipynb` líneas 1445–1446; `optimizacion_bayesiana/churn_pipeline_v11_corrida_original.ipynb` líneas 1470–1472; `optimizacion_bayesiana/churn_pipeline_v11_corrida_original.ipynb` líneas 1513–1538; `README.md` líneas 55–83)
12. **Ensamble en validación (202106).** Entrena cada configuración con 2 semillas sobre 202103–202105 con pesos por mes, predice 202106 y promedia. Imprime la ganancia máxima suavizada de cada configuración, su diferencia con el valor de Optuna y la ganancia del ensamble al ir sumando configuraciones. (`prediccion_final/churn_pipeline_final.ipynb` líneas 1435–1436; `prediccion_final/churn_pipeline_final.ipynb` líneas 1529–1579)
13. **Curva de ganancia y corte en 202106.** Ordena 202106 por probabilidad, acumula la ganancia, la suaviza con una media móvil de 401 posiciones y toma su máximo y la meseta a menos de 2 aciertos; lo grafica. Este valor queda como referencia en resumen_cortes.csv y meta.json. (`prediccion_final/churn_pipeline_final.ipynb` líneas 1052–1065; `prediccion_final/churn_pipeline_final.ipynb` líneas 1598–1648)
14. **Reentrenamiento con 202103–202106 y predicción de 202108.** Une train y validación, vuelve a entrenar las 6 configuraciones × 2 semillas con pesos por mes y promedia las probabilidades sobre los clientes de 202108. La cantidad de envíos es N_ENVIOS_MANUAL = 11.500. (`prediccion_final/churn_pipeline_final.ipynb` líneas 1727–1751)
15. **Exportación del CSV y metadatos.** Crea salida_final_<fecha>/ y escribe el CSV con los primeros 11.500 numero_de_cliente por probabilidad descendente (una columna, sin encabezado), resumen_cortes.csv y meta.json con el entorno y las configuraciones. (`prediccion_final/churn_pipeline_final.ipynb` líneas 1754–1821)

## Archivos

- `README.md` · explicacion · Markdown · 120 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/micaelarr/README.md.txt) — Presenta la entrega en 7 secciones: estructura del repositorio, resumen de la solución, pasos para replicar el archivo final, procedencia de los hiperparámetros (estudio de Optuna, espacio de búsqueda y tabla de las 6 configuraciones), elección del corte de 11.500 con una tabla de ganancia suavizada en 202106 por corte, entorno, y una lista de lo que se probó y se descartó con diferencias expresadas en cantidad de BAJA+2. Los nombres de carpeta (01_prediccion_final/, 02_optimizacion_bayesiana/) y del CSV final que cita difieren de los que hay en el repositorio.
- `optimizacion_bayesiana/churn_pipeline_v11_corrida_original.ipynb` · secundario · Jupyter (python) · 1827 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/micaelarr/optimizacion_bayesiana/churn_pipeline_v11_corrida_original.ipynb.txt) — Versión v11 del mismo pipeline, con ruta absoluta de Windows al dataset. Según el README, es la corrida que generó los trials 37–61 del estudio de Optuna y el archivo enviado. Difiere del notebook final en que elige las 25 variables con historia por importancia, compara tres variantes en la etapa 6a, ejecuta los estudios de Optuna lgbm_binario y lgbm_catedra, arma CONFIGS desde los estudios, corre el backtest y exporta un CSV por cada corte de 10.000 a 14.500 más el corte automático.
- `optimizacion_bayesiana/configs_finales.json` · configuracion · JSON · 89 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/micaelarr/optimizacion_bayesiana/configs_finales.json.txt) — JSON con una descripción del estudio de Optuna y las 6 configuraciones del ensamble (trials 54, 32, 23, 26, 43 y 31): para cada una, el valor de Optuna (entre 476,5 y 486,5 millones) y los 7 hiperparámetros de LightGBM. Los valores coinciden con la lista CONFIGS del notebook final.
- `optimizacion_bayesiana/churn_pipeline_v9_optuna.ipynb` · secundario · Jupyter (python) · 1729 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/micaelarr/optimizacion_bayesiana/churn_pipeline_v9_optuna.ipynb.txt) — Versión v9 del pipeline. Según el README, generó los trials 0–36 del estudio de Optuna. Agrega a la v7 las variables de historia y los pesos por mes, compara 6 variantes (2 conjuntos de columnas × decay 1,0, 0,8 y 0,6), ejecuta el estudio lgbm_binario (150 trials o 4 h) y termina con un semillero de 30 modelos con los parámetros del trial de mayor valor, corte automático y un único CSV.
- `optimizacion_bayesiana/origen_warm_start/churn_pipeline_v3.ipynb` · secundario · Jupyter (python) · 1169 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/micaelarr/optimizacion_bayesiana/origen_warm_start/churn_pipeline_v3.ipynb.txt) — Versión v3 del pipeline, origen de una de las bases de warm start. Deflacta todos los montos, calcula lags y deltas sólo de 15 variables, cluster y PSI, y ejecuta tres estudios de Optuna (Random Forest con tres clases, Random Forest binario y LightGBM binario); el de mayor ganancia en 202106 sigue a un semillero de 10 modelos, corte automático y un único CSV. No tiene variables rotas a NULL, límites en nominal, variables de historia ni pesos por mes.
- `optimizacion_bayesiana/origen_warm_start/churn_pipeline_v7.ipynb` · secundario · Jupyter (python) · 1615 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/micaelarr/optimizacion_bayesiana/origen_warm_start/churn_pipeline_v7.ipynb.txt) — Versión v7: copia de la v5 en la que la etapa 6a compara variantes que quitan ccajas_depositos, Visa_mpagado y mcomisiones_mantenimiento, de a una y las tres juntas. Usa VERSION_ESTUDIO = 'v5', por lo que su estudio de Optuna se guarda en la misma base que el de la v5.
- `optimizacion_bayesiana/origen_warm_start/churn_pipeline_v5.ipynb` · secundario · Jupyter (python) · 1604 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/micaelarr/optimizacion_bayesiana/origen_warm_start/churn_pipeline_v5.ipynb.txt) — Versión v5 del pipeline. Respecto de la v3 agrega ccajas_depositos a NULL en 202105, los límites de tarjeta en nominal, delta1 para todas las numéricas, una etapa 6a que compara 4 conjuntos de columnas con 10 semillas, Random Forest desactivado, estudio de Optuna de LightGBM (150 trials o 4 h, con warm start desde v4 y v3), semillero de 30 modelos y backtest.
- `prediccion_final/churn_pipeline_final.ipynb` · principal · Jupyter (python) · 1821 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/micaelarr/prediccion_final/churn_pipeline_final.ipynb.txt) — Notebook de Python (54 celdas en la copia a texto) que va de competencia_01.csv al CSV de 11.500 clientes: ETL en DuckDB, variables, cluster, PSI, variables de historia, ensamble de 6 configuraciones de LightGBM × 2 semillas medido en 202106 y reentrenado con 202103–202106. Conserva de la versión v11 las funciones de Optuna, Random Forest y backtest, que aquí no se ejecutan.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### prediccion_final/churn_pipeline_final.ipynb

Notebook de Python (54 celdas en la copia a texto) que va de competencia_01.csv al CSV de 11.500 clientes: ETL en DuckDB, variables, cluster, PSI, variables de historia, ensamble de 6 configuraciones de LightGBM × 2 semillas medido en 202106 y reentrenado con 202103–202106. Conserva de la versión v11 las funciones de Optuna, Random Forest y backtest, que aquí no se ejecutan.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–9] Celda de texto de presentación: declara que el notebook parte de competencia_01.csv
#   y genera el CSV de 11.500 clientes, y enumera tres fijaciones respecto de la v11: columnas y decay de la
#   etapa 6a, 6 configuraciones de hiperparámetros escritas en el código y corte de 11.500.
#%% celda 1 [texto]
# Pipeline de predicción de churn bancario (Agosto 2021) — ENTREGA FINAL

Notebook único que, partiendo de `competencia_01.csv`, genera el CSV final (11.500 clientes). Es la v11 con tres fijaciones para que la corrida sea reproducible y no dependa de decisiones tomadas en corridas anteriores:
1. **Etapa 6a fijada:** columnas = ganadora de la v7 + features de historia, decay de pesos por mes 0,8 (resultado de la 6a de la corrida original).
2. **Hiperparámetros fijos:** las 6 configuraciones del ensamble están escritas en la celda de la Etapa 6 (salen del estudio de Optuna incluido en `02_optimizacion_bayesiana/`; ver README).
3. **Corte fijo:** 11.500 envíos; se exporta un solo CSV.

Las etapas siguen la numeración de la v11 (que se conserva abajo). Las secciones de Optuna/variantes se reemplazaron por celdas que aplican lo ya decidido.

# [Anotación · líneas 11–25] Importa os, json, time, datetime, duckdb, numpy, pandas y matplotlib, y define
#   LOKY_MAX_CPU_COUNT con la cantidad de CPU. La línea de instalación con pip está comentada.
#%% celda 2 [código]
# Si falta alguna librería, descomentá:
# %pip install duckdb optuna lightgbm --quiet

import os
import json
import time
import datetime

os.environ.setdefault("LOKY_MAX_CPU_COUNT", str(os.cpu_count()))  # silencia el warning de joblib en Windows

import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# [Anotación · líneas 27–52] Define _buscar_base(), que ubica la carpeta de competencia_01.csv: usa la
#   variable de entorno CHURN_BASE_PATH si existe y, si no, busca el archivo en la carpeta de trabajo y hasta 3
#   niveles arriba; si no lo encuentra lanza FileNotFoundError. Con esa carpeta arma las rutas del dataset, de
#   modelos/ (que crea) y de las salidas.
#%% celda 3 [texto]
## Configuración general

`MODO_PRUEBA = True` corre todo con una muestra de clientes y pocos trials (unos minutos), para
chequear que el notebook ande de punta a punta antes de lanzar la corrida larga.

#%% celda 4 [código]
# Carpeta que contiene competencia_01.csv (las salidas y duckdb_tmp/ se crean ahí).
# Orden de búsqueda: variable de entorno CHURN_BASE_PATH; si no, la carpeta del notebook y hasta 3 niveles arriba.
def _buscar_base():
    if os.environ.get("CHURN_BASE_PATH"):
        return os.environ["CHURN_BASE_PATH"]
    carpeta = os.getcwd()
    for _ in range(4):
        if os.path.exists(os.path.join(carpeta, "competencia_01.csv")):
            return carpeta
        carpeta = os.path.dirname(carpeta)
    raise FileNotFoundError("No se encontró competencia_01.csv: copialo a la carpeta del notebook "
                            "o definí la variable de entorno CHURN_BASE_PATH con la carpeta que lo contiene.")


BASE_PATH = _buscar_base()
DATASET_PATH = os.path.join(BASE_PATH, "competencia_01.csv")
MODELOS_PATH = os.path.join(BASE_PATH, "modelos")
SALIDAS_PATH = BASE_PATH
os.makedirs(MODELOS_PATH, exist_ok=True)

# [Anotación · líneas 54–68] MODO_PRUEBA = False (con True se carga el 5 % de los clientes). Asigna los meses:
#   202107 sólo para historia, 202103–202105 entrenamiento, 202106 validación, 202108 aplicación y 202103–202106
#   para el reentrenamiento final. Define los nombres de las columnas de cliente, mes, clase y rol.
MODO_PRUEBA = False   # True = 5% de los clientes, sólo para probar que corre
FRACCION_MUESTRA = 0.05 if MODO_PRUEBA else 1.0   # fracción de CLIENTES (no de filas) que se cargan

MESES_HIST = [202107]                    # sólo para lags/deltas, no entrenan
MESES_TRAIN = [202103, 202104, 202105]   # se concatenan para el entrenamiento
MES_VALID = 202106                       # Optuna, elección de modelo y cantidad de envíos
MES_APLICACION = 202108                  # mes del desafío (SIN CLASE)
MESES_FINAL = MESES_TRAIN + [MES_VALID]  # reentrenamiento final (Etapa 9)

ID_COL = "numero_de_cliente"
MES_COL = "foto_mes"
TARGET_COL = "clase_ternaria"
ROL_COL = "rol"

COLS_NO_FEATURE = {ID_COL, MES_COL, TARGET_COL, ROL_COL}

# [Anotación · líneas 70–89] NO_DEFLACTAR lista 4 límites de tarjeta (compra y financiación de Visa y Master)
#   que se conservan también en nominal. DELTAS_EXTRA = True activa el delta1 para todas las numéricas.
#   VARIABLES_ROTAS indica que ccajas_depositos se pasa a NULL en 202105; la entrada de cprestamos_hipotecarios
#   en 202103 está comentada.
# Montos que NO se deflactan (además de la versión _real se conserva la nominal con su
# nombre original): los límites de tarjeta se mantienen fijos en pesos nominales, así que
# al dividirlos por el IPC "caen" artificialmente mes a mes y el PSI los descarta.
NO_DEFLACTAR = [
    "Visa_mlimitecompra", "Master_mlimitecompra",
    "Visa_mfinanciacion_limite", "Master_mfinanciacion_limite",
]

# delta1_ (valor actual - mes anterior) para TODAS las variables numéricas, además de
# los lag1/lag2/delta1/delta2 completos de VARS_LAG.
DELTAS_EXTRA = True

# Variables con un error de carga en meses puntuales: se ponen en NULL (NA) SÓLO en
# esos meses, apenas se carga el csv (antes de imputar, deflactar, calcular lags o PSI).
# Así el modelo no aprende de un valor que no es real (LightGBM lo trata como faltante).
VARIABLES_ROTAS = {
    "ccajas_depositos": [202105],   # 100% ceros en 202105 (en el resto de los meses ~3–4% > 0)
    # Otros candidatos que marcó el scan de la Etapa 2 — descomentá si querés tratarlos igual:
    # "cprestamos_hipotecarios": [202103],   # promedio 0.014 vs ~0.05 en los demás meses
}

# [Anotación · líneas 91–102] Constantes de ganancia: 1.072.500 por acierto y 27.500 de costo por envío.
#   periodo() convierte AAAAMM en un número de mes correlativo (año × 12 + mes) para poder restar meses.
#   PRIMER_MES es el menor mes configurado (202103).
# Constantes del negocio (idénticas en z201/z301/z401/exp_401/z701)
ganancia_acierto = 1_072_500
costo_estimulo = 27_500


def periodo(mes: int) -> int:
    """foto_mes (AAAAMM) -> número de mes correlativo (año*12 + mes). Permite
    restar meses sin romperse al cruzar de año (202201 - 202112 = 1, no 89)."""
    return (mes // 100) * 12 + mes % 100


PRIMER_MES = min(MESES_HIST + MESES_TRAIN + [MES_VALID, MES_APLICACION])

# [Anotación · líneas 104–128] Reglas de imputación para columnas de tarjetas Master y Visa: COLS_CERO (16
#   sufijos de montos y cantidades por marca, 32 columnas) se imputan con 0; status, delinquency y fechaalta,
#   con −1; Fvencimiento, Finiciomora y fultimo_cierre, con el centinela 999.999.
#%% celda 5 [texto]
## Etapa 2 — reglas de imputación

El 99% de los nulos de este dataset están en las 22 columnas `Master_*` y 22 `Visa_*`, en bloques
parejos → no son azarosos, son clientes que no tienen esa tarjeta.

#%% celda 6 [código]
COLS_CERO = [
    f"{marca}_{sufijo}"
    for marca in ("Master", "Visa")
    for sufijo in (
        "mfinanciacion_limite", "msaldototal", "msaldopesos", "msaldodolares",
        "mconsumospesos", "mconsumosdolares", "mconsumototal",
        "mlimitecompra", "madelantopesos", "madelantodolares",
        "mpagado", "mpagospesos", "mpagosdolares", "mpagominimo",
        "cconsumos", "cadelantosefectivo",
    )
]
# Status/delinquency: rango real >= 0 -> centinela -1. fechaalta: rango real >= 1 -> -1 también sirve.
COLS_EXTREMO_NEG1 = [f"{marca}_{sufijo}" for marca in ("Master", "Visa")
                     for sufijo in ("status", "delinquency", "fechaalta")]
# Fvencimiento/Finiciomora/fultimo_cierre pueden ser negativos o ~0 legítimamente -> centinela alto.
CENTINELA_ALTO = 999_999
COLS_EXTREMO_ALTO = [f"{marca}_{sufijo}" for marca in ("Master", "Visa")
                     for sufijo in ("Fvencimiento", "Finiciomora", "fultimo_cierre")]

# [Anotación · líneas 130–152] IPC_MENSUAL guarda la variación mensual de 202103 a 202108 (4,8; 4,1; 3,3; 3,2;
#   3,0; 2,5). VARS_LAG lista las 15 variables que reciben lag1, lag2, delta1 y delta2.
#%% celda 7 [texto]
## Etapa 3 — deflactación por inflación y variables para lags

Variación mensual del IPC (INDEC, Argentina 2021), igual que `exp_402_feature_engineering_3`.

Con 202103 en train, ese mes queda con `lag1_*` y `lag2_*` vacíos (no hay 202102/202101), y
202104 con `lag2_*` vacío. No es un problema: LightGBM usa los NaN de forma nativa y el RF los
imputa marcando con un indicador que el valor fue imputado (ver Etapa 6).

#%% celda 8 [código]
IPC_MENSUAL = {
    202103: 4.8, 202104: 4.1, 202105: 3.3,
    202106: 3.2, 202107: 3.0, 202108: 2.5,
}

VARS_LAG = [
    "mcuentas_saldo_real", "mrentabilidad_real", "mactivos_margen_real",
    "mpasivos_margen_real", "mpayroll_real", "mprestamos_personales_real",
    "ctrx_quarter", "ctarjeta_visa_transacciones", "ctarjeta_master_transacciones",
    "chomebanking_transacciones", "cmobile_app_trx",
    "mtransferencias_emitidas_real", "mextraccion_autoservicio_real",
    "cprestamos_personales", "cproductos",
]

# [Anotación · líneas 154–179] Auxiliares de SQL: _col() pone un nombre entre comillas dobles, _columnas()
#   devuelve los nombres de columna de una tabla y _periodo_sql() es la versión SQL de periodo().
#   crear_macros_sql() crea dos macros de DuckDB: suma_sin_null (suma tratando NULL como 0) y ratio_sin_null
#   (cociente que devuelve 0 si el denominador es NULL o 0).
#%% celda 9 [texto]
## Funciones auxiliares SQL

#%% celda 10 [código]
def _col(nombre: str) -> str:
    """Identificador entre comillas dobles (preserva mayúsculas, evita palabras reservadas)."""
    return f'"{nombre}"'


def _columnas(con, tabla: str) -> list:
    """Nombres de columna de una tabla de la conexión (sin traer datos)."""
    return con.execute(f"SELECT * FROM {tabla} LIMIT 0").df().columns.tolist()


def _periodo_sql(expr: str) -> str:
    """Versión SQL de periodo(): año*12 + mes (división entera con //)."""
    return f"(({expr} // 100) * 12 + ({expr} % 100))"


def crear_macros_sql(con: duckdb.DuckDBPyConnection) -> None:
    """Mismas macros que exp_402/z402: suma y ratio tratando NULL/0 sin romperse."""
    con.execute("CREATE OR REPLACE MACRO suma_sin_null(a, b) AS COALESCE(a, 0) + COALESCE(b, 0)")
    con.execute(
        "CREATE OR REPLACE MACRO ratio_sin_null(a, b) AS "
        "CASE WHEN COALESCE(b, 0) = 0 THEN 0 ELSE a / b END"
    )

# [Anotación · líneas 181–218] construir_etapa1_sql(), primera parte: carga el CSV con read_csv_auto en la
#   tabla raw (si fraccion < 1 filtra clientes por hash del id), verifica que existan foto_mes, clase_ternaria y
#   numero_de_cliente y arma la cláusula REPLACE que pone NULL en las variables de VARIABLES_ROTAS sólo en sus
#   meses.
#%% celda 11 [texto]
## Etapa 1 — Estructura de Datasets (prevención de Data Leakage)

#%% celda 12 [código]
def construir_etapa1_sql(con: duckdb.DuckDBPyConnection, ruta: str = DATASET_PATH,
                          fraccion: float = FRACCION_MUESTRA) -> None:
    """
    Carga el csv con read_csv_auto (igual que z101_target_sql) y agrega 'rol'.
    Si fraccion < 1 (MODO_PRUEBA) se queda con una muestra de CLIENTES vía hash
    del id: así cada cliente seleccionado conserva todos sus meses y los lags
    siguen teniendo sentido.
    """
    t0 = time.time()
    filtro = ""
    if fraccion < 1:
        filtro = f"WHERE hash({_col(ID_COL)}) % 10000 < {int(fraccion * 10000)}"
    con.execute(f"CREATE OR REPLACE TABLE raw AS SELECT * FROM read_csv_auto('{ruta}') {filtro}")
    print(f"CSV cargado en DuckDB ({ruta}) en {time.time() - t0:.1f} s"
          + (f" — MUESTRA de {fraccion:.0%} de clientes" if fraccion < 1 else ""))

    faltantes = {MES_COL, TARGET_COL, ID_COL} - set(_columnas(con, "raw"))
    if faltantes:
        raise ValueError(f"Faltan columnas esperadas en el dataset: {faltantes}")

    meses_hist_sql = ",".join(map(str, MESES_HIST))
    meses_train_sql = ",".join(map(str, MESES_TRAIN))

    # Variables rotas -> NULL sólo en sus meses (SELECT * REPLACE de DuckDB)
    rotas = {c: m for c, m in VARIABLES_ROTAS.items() if c in _columnas(con, "raw")}
    for c in set(VARIABLES_ROTAS) - set(rotas):
        print(f"(Aviso: '{c}' está en VARIABLES_ROTAS pero no existe en el csv)")
    replace_clause = ""
    if rotas:
        reemplazos = ", ".join(
            f"CASE WHEN {_col(MES_COL)} IN ({','.join(map(str, meses))}) THEN NULL ELSE {_col(c)} END AS {_col(c)}"
            for c, meses in rotas.items()
        )
        replace_clause = f"REPLACE ({reemplazos})"

# [Anotación · líneas 220–236] Crea la tabla etapa1 con la columna rol ('historico', 'train', 'validacion' o
#   'aplicacion' según foto_mes) aplicando el REPLACE de variables rotas, e imprime cuántas filas quedaron en
#   NULL por cada una.
    con.execute(f"""
        CREATE OR REPLACE TABLE etapa1 AS
        SELECT * {replace_clause},
            CASE
                WHEN {_col(MES_COL)} IN ({meses_hist_sql}) THEN 'historico'
                WHEN {_col(MES_COL)} IN ({meses_train_sql}) THEN 'train'
                WHEN {_col(MES_COL)} = {MES_VALID} THEN 'validacion'
                WHEN {_col(MES_COL)} = {MES_APLICACION} THEN 'aplicacion'
            END AS {_col(ROL_COL)}
        FROM raw
    """)
    for c, meses in rotas.items():
        n_na = con.execute(f"""
            SELECT COUNT(*) FROM etapa1 WHERE {_col(c)} IS NULL
            AND {_col(MES_COL)} IN ({','.join(map(str, meses))})
        """).fetchone()[0]
        print(f"Variable rota: '{c}' -> NA en {meses} ({n_na:,} filas)")


# [Anotación · líneas 239–273] validar_estructura_sql(): imprime las filas por rol y verifica con assert que
#   no haya filas sin rol, que todo el mes de aplicación tenga clase 'SIN CLASE' y que train y validación no
#   tengan clase nula; imprime la distribución de clase_ternaria por mes.
def validar_estructura_sql(con: duckdb.DuckDBPyConnection) -> None:
    """Chequeos de sanidad: filas por rol, aplicación toda 'SIN CLASE', train/validación sin target nulo."""
    conteos = con.execute(f"""
        SELECT {_col(ROL_COL)}, COUNT(*) AS n, MIN({_col(MES_COL)}) AS mn, MAX({_col(MES_COL)}) AS mx
        FROM etapa1 GROUP BY {_col(ROL_COL)} ORDER BY mn
    """).fetchall()
    print("Filas por rol:")
    for rol, n, mn, mx in conteos:
        print(f"  {str(rol):12s}: {n:>8,} filas | meses {mn}-{mx}")

    sin_rol = con.execute(f"SELECT COUNT(*) FROM etapa1 WHERE {_col(ROL_COL)} IS NULL").fetchone()[0]
    assert sin_rol == 0, f"Hay {sin_rol} filas de meses que no están en la configuración."

    mal_aplic = con.execute(f"""
        SELECT COUNT(*) FROM etapa1
        WHERE {_col(ROL_COL)} = 'aplicacion' AND COALESCE({_col(TARGET_COL)}, '') != 'SIN CLASE'
    """).fetchone()[0]
    assert mal_aplic == 0, "El mes de aplicación debería venir íntegramente como 'SIN CLASE'."

    for rol in ("train", "validacion"):
        n_nan = con.execute(f"""
            SELECT COUNT(*) FROM etapa1
            WHERE {_col(ROL_COL)} = '{rol}' AND {_col(TARGET_COL)} IS NULL
        """).fetchone()[0]
        assert n_nan == 0, f"El rol '{rol}' tiene {n_nan} filas con target sin madurar."

    for rol in ("train", "validacion"):
        dist = con.execute(f"""
            SELECT {_col(MES_COL)}, {_col(TARGET_COL)}, COUNT(*) AS n FROM etapa1
            WHERE {_col(ROL_COL)} = '{rol}' GROUP BY ALL ORDER BY 1, 3 DESC
        """).df()
        print(f"\n{rol} - distribución de {TARGET_COL} por mes:")
        print(dist.pivot(index=MES_COL, columns=TARGET_COL, values="n").to_string())

    print("\nOK: estructura de datasets validada.")

# [Anotación · líneas 275–304] Borra y vuelve a crear una base DuckDB en disco (duckdb_tmp/churn_v5.duckdb),
#   fija el límite de memoria en el 40 % de la RAM (4 GB si psutil no está instalado) y el directorio temporal;
#   después crea las macros, construye etapa1 y la valida.
#%% celda 13 [código]
# Base DuckDB EN DISCO (no en RAM): las tablas intermedias ocupan varios GB y una base en
# memoria se queda sin lugar (OutOfMemoryException). En disco, DuckDB baja a disco lo que no entra.
DUCKDB_PATH = os.path.join(BASE_PATH, "duckdb_tmp", "churn_v5.duckdb")
os.makedirs(os.path.dirname(DUCKDB_PATH), exist_ok=True)
try:   # arrancar siempre de cero
    con.close()   # si la celda se re-ejecuta en el mismo kernel
except NameError:
    pass
for _f in (DUCKDB_PATH, DUCKDB_PATH + ".wal"):
    if os.path.exists(_f):
        try:
            os.remove(_f)
        except PermissionError:
            raise RuntimeError(f"{_f} está en uso por otro kernel: cerralo (Kernel -> Shut Down) y reintentá.")

try:   # límite de memoria de DuckDB: ~40% de la RAM (el resto queda para pandas/LightGBM)
    import psutil
    DUCKDB_MEMORIA_GB = max(2, int(psutil.virtual_memory().total / 1e9 * 0.4))
except ImportError:
    DUCKDB_MEMORIA_GB = 4

con = duckdb.connect(DUCKDB_PATH)
con.execute(f"SET memory_limit = '{DUCKDB_MEMORIA_GB}GB'")
con.execute(f"SET temp_directory = '{os.path.dirname(DUCKDB_PATH)}'")
con.execute("SET preserve_insertion_order = false")
print(f"DuckDB en disco ({DUCKDB_PATH}), límite de memoria {DUCKDB_MEMORIA_GB} GB")
crear_macros_sql(con)
construir_etapa1_sql(con)
validar_estructura_sql(con)

# [Anotación · líneas 306–361] scan_variables_rotas_sql(): para cada variable numérica y mes calcula el
#   promedio y las proporciones de ceros y de nulos y los compara con la mediana de los demás meses; marca los
#   casos en que el promedio se multiplica o divide por más de 3 o cae a 0, o en que la proporción de ceros o de
#   nulos sube 30 puntos o más. Devuelve un reporte y no modifica datos.
#%% celda 14 [texto]
## Etapa 2 — Data Quality

Primero un **scan de variables rotas por mes** sobre el csv original: así se detectaron
`ccajas_depositos` en 202105 (100% ceros) y otros candidatos. Después, la auditoría de nulos,
outliers e imputación de la v3. Las columnas de `VARIABLES_ROTAS` no se imputan: quedan NA.

#%% celda 15 [código]
def scan_variables_rotas_sql(con: duckdb.DuckDBPyConnection, tabla: str = "raw",
                             factor: float = 3.0, salto: float = 0.30) -> pd.DataFrame:
    """
    Diagnóstico de "catástrofes" de carga: para cada variable numérica y cada mes
    compara contra la mediana de los demás meses y marca:
      - promedio que se multiplica/divide por más de 'factor' (o cae a 0 exacto),
      - salto de 'salto' (30 pp) o más en el % de ceros o en el % de nulos.
    Corre sobre 'raw' (el csv original, antes de VARIABLES_ROTAS). Es un reporte:
    no modifica nada; lo que quieras tratar lo agregás a VARIABLES_ROTAS.
    """
    tipos = con.execute(f"DESCRIBE {tabla}").df()
    numericas = [c for c, t in zip(tipos["column_name"], tipos["column_type"])
                 if c not in COLS_NO_FEATURE and any(k in t.upper() for k in ("INT", "DOUBLE", "FLOAT", "DECIMAL"))]
    exprs = []
    for i, c in enumerate(numericas):
        exprs += [f"AVG({_col(c)}) AS m{i}",
                  f"AVG(CASE WHEN {_col(c)} = 0 THEN 1.0 ELSE 0.0 END) AS z{i}",
                  f"AVG(CASE WHEN {_col(c)} IS NULL THEN 1.0 ELSE 0.0 END) AS n{i}"]
    stats = con.execute(f"""
        SELECT {_col(MES_COL)}, {", ".join(exprs)} FROM {tabla} GROUP BY 1 ORDER BY 1
    """).df().set_index(MES_COL)

    filas = []
    for i, c in enumerate(numericas):
        m, z, n = stats[f"m{i}"], stats[f"z{i}"], stats[f"n{i}"]
        for mes in stats.index:
            otros = stats.index != mes
            med_m, med_z, med_n = m[otros].median(), z[otros].median(), n[otros].median()
            ratio = m[mes] / med_m if med_m not in (0,) and pd.notna(med_m) and pd.notna(m[mes]) else np.nan
            motivos = []
            if pd.notna(ratio) and ratio != 0 and (abs(ratio) > factor or abs(ratio) < 1 / factor):
                motivos.append(f"promedio x{ratio:.2f}")
            if m[mes] == 0 and med_m != 0:
                motivos.append("promedio = 0")
            if z[mes] - med_z >= salto:
                motivos.append(f"ceros {med_z:.0%} -> {z[mes]:.0%}")
            if n[mes] - med_n >= salto:
                motivos.append(f"nulos {med_n:.0%} -> {n[mes]:.0%}")
            if motivos:
                filas.append({"variable": c, "mes": mes, "promedio_mes": m[mes],
                              "mediana_otros_meses": med_m, "motivo": "; ".join(motivos),
                              "ya_en_VARIABLES_ROTAS": mes in VARIABLES_ROTAS.get(c, [])})
    reporte = pd.DataFrame(filas)
    print(f"Scan de variables rotas sobre '{tabla}' ({len(numericas)} variables numéricas):")
    print(reporte.round(4).to_string(index=False) if len(reporte) else "  sin anomalías")
    print("\nOJO: *_fultimo_cierre / *_Fvencimiento dependen del día de corte de cada mes "
          "(no son errores; el PSI ya las saca si driftean).")
    return reporte


# [Anotación · líneas 364–388] auditoria_calidad_sql(): calcula el porcentaje de nulos de cada columna en
#   train y en aplicación y su diferencia, imprime las 20 primeras y devuelve las columnas con nulos que no
#   están cubiertas por las reglas de imputación.
def auditoria_calidad_sql(con: duckdb.DuckDBPyConnection, columnas: list) -> tuple:
    """% de nulos en train vs. aplicación (diagnóstico de z701) y columnas con nulos sin regla (van a mediana)."""
    def pct_nulos(rol: str) -> pd.Series:
        expr = ", ".join(
            f"AVG(CASE WHEN {_col(c)} IS NULL THEN 1.0 ELSE 0.0 END) * 100 AS {_col(c)}"
            for c in columnas
        )
        return con.execute(f"SELECT {expr} FROM etapa1 WHERE {_col(ROL_COL)} = '{rol}'").df().iloc[0]

    resumen = pd.DataFrame({
        "null_%_train": pct_nulos("train"),
        "null_%_aplicacion": pct_nulos("aplicacion"),
    })
    resumen["gap_null_%"] = (resumen["null_%_train"] - resumen["null_%_aplicacion"]).abs()
    resumen = resumen.sort_values("null_%_train", ascending=False)

    con_nulos = resumen[(resumen["null_%_train"] > 0) | (resumen["null_%_aplicacion"] > 0)]
    print(f"Columnas con algún nulo (train o aplicación): {len(con_nulos)}")
    print(con_nulos.round(2).head(20))

    sin_clasificar = [c for c in con_nulos.index
                      if c not in COLS_CERO + COLS_EXTREMO_NEG1 + COLS_EXTREMO_ALTO]
    if sin_clasificar:
        print(f"\nColumnas con nulos NO cubiertas por las reglas -> mediana de train: {sin_clasificar}")
    return resumen, sin_clasificar


# [Anotación · líneas 391–414] detectar_outliers_sql(): por columna calcula Q1 y Q3 sobre train y cuenta los
#   valores fuera de Q1 − 3·IQR y Q3 + 3·IQR; imprime las 15 columnas con mayor porcentaje. Es un reporte: no
#   recorta valores.
def detectar_outliers_sql(con: duckdb.DuckDBPyConnection, columnas: list,
                           factor_iqr: float = 3.0) -> pd.DataFrame:
    """Diagnóstico de outliers por IQR, sólo sobre train. Es un reporte: no recorta nada."""
    filas = []
    for c in columnas:
        q1, q3 = con.execute(f"""
            SELECT quantile_cont({_col(c)}, 0.25), quantile_cont({_col(c)}, 0.75)
            FROM etapa1 WHERE {_col(ROL_COL)} = 'train'
        """).fetchone()
        if q1 is None or q3 is None or q3 == q1:
            continue
        iqr = q3 - q1
        lim_inf, lim_sup = q1 - factor_iqr * iqr, q3 + factor_iqr * iqr
        n_out, n = con.execute(f"""
            SELECT SUM(CASE WHEN {_col(c)} < {lim_inf} OR {_col(c)} > {lim_sup} THEN 1 ELSE 0 END), COUNT(*)
            FROM etapa1 WHERE {_col(ROL_COL)} = 'train'
        """).fetchone()
        if n_out:
            filas.append({"columna": c, "n_outliers_train": n_out, "%_outliers_train": 100 * n_out / n,
                          "lim_inf": lim_inf, "lim_sup": lim_sup})
    reporte = pd.DataFrame(filas).sort_values("%_outliers_train", ascending=False)
    print(f"\nVariables con outliers (IQR x{factor_iqr}) en train: {len(reporte)}")
    print(reporte.head(15).round(2).to_string(index=False))
    return reporte


# [Anotación · líneas 417–425] calcular_medianas_train_sql(): mediana de cada columna calculada sólo con las
#   filas de train (0 si no hay valor).
def calcular_medianas_train_sql(con: duckdb.DuckDBPyConnection, columnas: list) -> dict:
    """Mediana calculada ÚNICAMENTE sobre train (fit) para aplicarla igual a todos los roles."""
    if not columnas:
        return {}
    expr = ", ".join(f"median({_col(c)}) AS {_col(c)}" for c in columnas)
    fila = con.execute(f"SELECT {expr} FROM etapa1 WHERE {_col(ROL_COL)} = 'train'").fetchone()
    medianas = {c: (v if v is not None else 0) for c, v in zip(columnas, fila)}
    print(f"Medianas de train: {medianas}")
    return medianas


# [Anotación · líneas 428–453] construir_etapa2_sql(): crea la tabla etapa2 imputando con COALESCE los valores
#   0, −1, 999.999 o la mediana de train según la lista a la que pertenece cada columna, y agrega los flags
#   tiene_visa y tiene_master (ctarjeta_visa > 0, ctarjeta_master > 0).
def construir_etapa2_sql(con: duckdb.DuckDBPyConnection, medianas: dict) -> None:
    """Aplica ceros, centinelas y medianas; agrega flags de tenencia de tarjeta."""
    columnas_etapa1 = _columnas(con, "etapa1")
    cols_cero = [c for c in COLS_CERO if c in columnas_etapa1]
    cols_neg1 = [c for c in COLS_EXTREMO_NEG1 if c in columnas_etapa1]
    cols_alto = [c for c in COLS_EXTREMO_ALTO if c in columnas_etapa1]
    cols_mediana = list(medianas.keys())

    exclude_clause = ", ".join(_col(c) for c in cols_cero + cols_neg1 + cols_alto + cols_mediana)
    partes = []
    partes += [f"COALESCE({_col(c)}, 0) AS {_col(c)}" for c in cols_cero]
    partes += [f"COALESCE({_col(c)}, -1) AS {_col(c)}" for c in cols_neg1]
    partes += [f"COALESCE({_col(c)}, {CENTINELA_ALTO}) AS {_col(c)}" for c in cols_alto]
    partes += [f"COALESCE({_col(c)}, {medianas[c]}) AS {_col(c)}" for c in cols_mediana]
    partes += [
        "CASE WHEN ctarjeta_visa > 0 THEN 1 ELSE 0 END AS tiene_visa",
        "CASE WHEN ctarjeta_master > 0 THEN 1 ELSE 0 END AS tiene_master",
    ]
    con.execute(f"""
        CREATE OR REPLACE TABLE etapa2 AS
        SELECT * EXCLUDE ({exclude_clause}), {", ".join(partes)}
        FROM etapa1
    """)
    print(f"Etapa 2: imputadas {len(cols_cero)} (cero) + {len(cols_neg1)} (-1) + "
          f"{len(cols_alto)} ({CENTINELA_ALTO}) + {len(cols_mediana)} (mediana train). "
          f"Agregadas tiene_visa, tiene_master.")

# [Anotación · líneas 455–467] Ejecuta el scan de variables rotas sobre raw y borra esa tabla; corre la
#   auditoría de nulos y el reporte de outliers, calcula las medianas de train para las columnas sin regla (sin
#   incluir las de VARIABLES_ROTAS, que quedan en NULL), construye etapa2 y borra etapa1.
#%% celda 16 [código]
reporte_rotas = scan_variables_rotas_sql(con)
con.execute("DROP TABLE raw")   # ya no se usa: liberar espacio

#%% celda 17 [código]
columnas_candidatas = [c for c in _columnas(con, "etapa1") if c not in COLS_NO_FEATURE]
_, sin_clasificar = auditoria_calidad_sql(con, columnas_candidatas)
# Las variables rotas quedan en NA a propósito: NO se imputan por mediana.
sin_clasificar = [c for c in sin_clasificar if c not in VARIABLES_ROTAS]
reporte_outliers = detectar_outliers_sql(con, columnas_candidatas)
medianas = calcular_medianas_train_sql(con, sin_clasificar)
construir_etapa2_sql(con, medianas)
con.execute("DROP TABLE etapa1")   # ya no se usa: liberar espacio

# [Anotación · líneas 469–494] _columnas_monetarias(): selecciona las columnas de monto (prefijo m, Master_m o
#   Visa_m) cuyo nombre no contiene 'dolares'. _indice_ipc_filas(): arma el índice de precios acumulado mes a
#   mes con base 100.
#%% celda 18 [texto]
## Etapa 3 — Feature Engineering

Deflactación (salvo la versión nominal de los límites de tarjeta, `NO_DEFLACTAR`), lags
completos para `VARS_LAG` + `delta1_` para todas las demás numéricas (`DELTAS_EXTRA`),
y ratios. Los rank por mes de la v4 quedan desactivados.

#%% celda 19 [código]
def _columnas_monetarias(columnas: list) -> list:
    """Montos ('m*', 'Master_m*', 'Visa_m*') salvo los denominados en dólares (no se deflactan por IPC en pesos)."""
    return [
        c for c in columnas
        if c not in COLS_NO_FEATURE
        and "dolares" not in c.lower()
        and (c.startswith("Master_m") or c.startswith("Visa_m")
             or (c.startswith("m") and not c.startswith(("Master", "Visa"))))
    ]


def _indice_ipc_filas() -> list:
    """Índice acumulado mes a mes, base 100."""
    idx, filas = 100.0, []
    for mes in sorted(IPC_MENSUAL):
        idx *= (1 + IPC_MENSUAL[mes] / 100)
        filas.append((mes, idx))
    return filas


# [Anotación · líneas 497–515] construir_etapa3_deflactado_sql(): crea una tabla con el índice de IPC, la une
#   por foto_mes y divide cada monto por (índice / 100), generando columnas con sufijo _real; elimina las
#   columnas nominales salvo las 4 de NO_DEFLACTAR.
def construir_etapa3_deflactado_sql(con: duckdb.DuckDBPyConnection) -> None:
    """monto_real = monto / (ipc_indice / 100). Agrega '_real' y descarta el nominal."""
    valores = ", ".join(f"({mes}, {idx})" for mes, idx in _indice_ipc_filas())
    con.execute(f"CREATE OR REPLACE TABLE ipc AS SELECT * FROM (VALUES {valores}) AS t({MES_COL}, ipc_indice)")

    cols_monetarias = _columnas_monetarias(_columnas(con, "etapa2"))
    reales = [f"({_col(c)} / (ipc_indice / 100.0)) AS {_col(c + '_real')}" for c in cols_monetarias]
    # Las de NO_DEFLACTAR conservan además la versión nominal (nombre original).
    exclude_clause = ", ".join(_col(c) for c in ["ipc_indice"] + cols_monetarias if c not in NO_DEFLACTAR)

    con.execute(f"""
        CREATE OR REPLACE TABLE etapa3_deflactado AS
        SELECT * EXCLUDE ({exclude_clause}), {", ".join(reales)}
        FROM (SELECT e.*, i.ipc_indice FROM etapa2 e JOIN ipc i ON e.{MES_COL} = i.{MES_COL})
    """)
    con.execute("DROP TABLE ipc")
    nominales = [c for c in NO_DEFLACTAR if c in cols_monetarias]
    print(f"Deflactadas {len(cols_monetarias)} variables monetarias. "
          f"Se conservan también en nominal: {nominales}")


# [Anotación · líneas 518–528] _candidatas_delta_extra(): lista las columnas numéricas que reciben sólo
#   delta1: todas menos identificadores y clase, las que ya tienen lags completos, las de centinela (999.999 o
#   −1) y los flags tiene_visa y tiene_master. DELTAS_EXTRA_CREADAS guarda los nombres generados.
def _candidatas_delta_extra(con, tabla: str, ya_con_lags: list) -> list:
    """Numéricas a las que se les agrega delta1_: todas menos ids/target, las que ya tienen
    lags completos, centinelas (999999/-1: su diferencia no significa nada) y flags."""
    tipos = con.execute(f"DESCRIBE {tabla}").df()
    excluir = (COLS_NO_FEATURE | set(ya_con_lags) | set(COLS_EXTREMO_ALTO) | set(COLS_EXTREMO_NEG1)
               | {"tiene_visa", "tiene_master"})
    return [c for c, t in zip(tipos["column_name"], tipos["column_type"])
            if c not in excluir and any(k in t.upper() for k in ("INT", "DOUBLE", "FLOAT", "DECIMAL"))]


DELTAS_EXTRA_CREADAS = []   # se completa en construir_etapa3_lags_sql (lo usa la Etapa 6a)


# [Anotación · líneas 531–564] construir_etapa3_lags_sql(), primera parte: con una ventana por cliente
#   ordenada por mes calcula, en una tabla auxiliar, el período del mes actual y de las dos filas anteriores,
#   los valores de 1 y 2 filas atrás de las variables de VARS_LAG y el de 1 fila atrás de las candidatas extra.
def construir_etapa3_lags_sql(con: duckdb.DuckDBPyConnection, variables: list = VARS_LAG) -> None:
    """
    lag1/lag2/delta1/delta2 por cliente. Si al cliente le falta un mes en el
    medio, LAG() posicional traería el valor de un mes equivocado: se exige
    que la distancia en PERÍODOS (año*12+mes) sea exactamente 1 o 2 (si no,
    NULL). Usar períodos evita el bug de restar AAAAMM al cruzar de año.
    """
    columnas = _columnas(con, "etapa3_deflactado")
    faltantes = [v for v in variables if v not in columnas]
    variables = [v for v in variables if v in columnas]
    if faltantes:
        print(f"(Aviso: se omiten de los lags porque no existen: {faltantes})")

    extra = _candidatas_delta_extra(con, "etapa3_deflactado", variables) if DELTAS_EXTRA else []

    per = _periodo_sql(_col(MES_COL))
    aux_exprs = [f"{per} AS {_col('_per')}",
                 f"LAG({per}, 1) OVER w AS {_col('_per_lag1')}",
                 f"LAG({per}, 2) OVER w AS {_col('_per_lag2')}"]
    aux_cols = ["_per", "_per_lag1", "_per_lag2"]
    for v in variables:
        aux_exprs += [f"LAG({_col(v)}, 1) OVER w AS {_col('_val_lag1_' + v)}",
                      f"LAG({_col(v)}, 2) OVER w AS {_col('_val_lag2_' + v)}"]
        aux_cols += [f"_val_lag1_{v}", f"_val_lag2_{v}"]
    for v in extra:
        aux_exprs.append(f"LAG({_col(v)}, 1) OVER w AS {_col('_val_lag1_' + v)}")
        aux_cols.append(f"_val_lag1_{v}")

    con.execute(f"""
        CREATE OR REPLACE TABLE _etapa3_aux AS
        SELECT *, {", ".join(aux_exprs)}
        FROM etapa3_deflactado
        WINDOW w AS (PARTITION BY {_col(ID_COL)} ORDER BY {_col(MES_COL)})
    """)

# [Anotación · líneas 566–588] Segunda parte: lag1 y lag2 se toman sólo si la distancia en períodos es
#   exactamente 1 o 2 meses (si no, NULL); delta1 y delta2 son la diferencia entre el valor actual y esos lags.
#   Para las candidatas extra agrega sólo delta1. Crea etapa3_lags sin las columnas auxiliares.
    final_exprs = []
    for v in variables:
        lag1 = f"CASE WHEN {_col('_per')} - {_col('_per_lag1')} = 1 THEN {_col('_val_lag1_' + v)} END"
        lag2 = f"CASE WHEN {_col('_per')} - {_col('_per_lag2')} = 2 THEN {_col('_val_lag2_' + v)} END"
        final_exprs += [f"({lag1}) AS {_col('lag1_' + v)}",
                        f"({lag2}) AS {_col('lag2_' + v)}",
                        f"({_col(v)} - ({lag1})) AS {_col('delta1_' + v)}",
                        f"({_col(v)} - ({lag2})) AS {_col('delta2_' + v)}"]
    DELTAS_EXTRA_CREADAS.clear()
    for v in extra:
        lag1 = f"CASE WHEN {_col('_per')} - {_col('_per_lag1')} = 1 THEN {_col('_val_lag1_' + v)} END"
        final_exprs.append(f"({_col(v)} - ({lag1})) AS {_col('delta1_' + v)}")
        DELTAS_EXTRA_CREADAS.append(f"delta1_{v}")

    exclude_clause = ", ".join(_col(c) for c in aux_cols)
    con.execute(f"""
        CREATE OR REPLACE TABLE etapa3_lags AS
        SELECT * EXCLUDE ({exclude_clause}), {", ".join(final_exprs)}
        FROM _etapa3_aux
    """)
    con.execute("DROP TABLE _etapa3_aux")
    print(f"Generados lag1/lag2/delta1/delta2 para {len(variables)} variables ({len(variables) * 4} columnas)"
          f" + delta1 para {len(extra)} variables más.")


# [Anotación · líneas 591–627] construir_etapa3_ratios_sql(): agrega 10 variables (consumo, saldo y límite
#   total de tarjetas; utilización de Visa y de Master; transacciones de tarjeta; préstamos totales; margen
#   neto; liquidez en pesos; transacciones digitales) y después tc_utilizacion_total, ratio_deuda_ingreso,
#   ratio_digital_total_trx, los flags tiene_prestamos y tiene_payroll y prop_vida_en_banco (antigüedad / (edad
#   × 12)).
def construir_etapa3_ratios_sql(con: duckdb.DuckDBPyConnection) -> None:
    """Ratios y agrupaciones (macros suma_sin_null/ratio_sin_null)."""
    con.execute("""
        CREATE OR REPLACE TABLE etapa3_base AS
        SELECT *,
            suma_sin_null(Visa_mconsumototal_real, Master_mconsumototal_real) AS tc_consumo_total,
            suma_sin_null(Visa_msaldototal_real, Master_msaldototal_real) AS tc_saldo_total,
            suma_sin_null(Visa_mlimitecompra_real, Master_mlimitecompra_real) AS tc_limite_total,
            ratio_sin_null(Visa_msaldototal_real, Visa_mlimitecompra_real) AS visa_utilizacion,
            ratio_sin_null(Master_msaldototal_real, Master_mlimitecompra_real) AS master_utilizacion,
            suma_sin_null(ctarjeta_visa_transacciones, ctarjeta_master_transacciones) AS tc_transacciones_total,
            suma_sin_null(
                suma_sin_null(mprestamos_personales_real, mprestamos_prendarios_real),
                mprestamos_hipotecarios_real
            ) AS prestamos_total,
            (mactivos_margen_real - mpasivos_margen_real) AS margen_neto,
            suma_sin_null(
                suma_sin_null(mcaja_ahorro_real, mcuenta_corriente_real),
                mplazo_fijo_pesos_real
            ) AS liquidez_total_pesos,
            suma_sin_null(chomebanking_transacciones, cmobile_app_trx) AS digital_trx_total
        FROM etapa3_lags
    """)
    con.execute("""
        CREATE OR REPLACE TABLE etapa3_final AS
        SELECT *,
            ratio_sin_null(tc_saldo_total, tc_limite_total) AS tc_utilizacion_total,
            ratio_sin_null(prestamos_total, mpayroll_real) AS ratio_deuda_ingreso,
            ratio_sin_null(digital_trx_total, ctrx_quarter) AS ratio_digital_total_trx,
            CASE WHEN prestamos_total > 0 THEN 1 ELSE 0 END AS tiene_prestamos,
            CASE WHEN COALESCE(mpayroll_real, 0) > 0 OR COALESCE(cpayroll_trx, 0) > 0
                 THEN 1 ELSE 0 END AS tiene_payroll,
            ratio_sin_null(cliente_antiguedad, cliente_edad * 12) AS prop_vida_en_banco
        FROM etapa3_base
    """)
    con.execute("DROP TABLE etapa3_base")
    print("Agregadas 10 variables de ratios/agrupaciones + tiene_prestamos, tiene_payroll, prop_vida_en_banco.")


# [Anotación · líneas 630–652] DERIVADAS registra, para cada variable derivada, las variables base con las que
#   se calcula; se usa en la etapa 5 para propagar exclusiones. FLAGS_QUE_SOBREVIVEN indica que tiene_payroll y
#   tiene_prestamos no se excluyen aunque se excluya su base.
# Dependencias de las variables derivadas: se usan en la Etapa 5 para que, si
# se excluye una variable base, la exclusión llegue también a lo que se calculó con ella.
DERIVADAS = {
    "tc_consumo_total": ["Visa_mconsumototal_real", "Master_mconsumototal_real"],
    "tc_saldo_total": ["Visa_msaldototal_real", "Master_msaldototal_real"],
    "tc_limite_total": ["Visa_mlimitecompra_real", "Master_mlimitecompra_real"],
    "visa_utilizacion": ["Visa_msaldototal_real", "Visa_mlimitecompra_real"],
    "master_utilizacion": ["Master_msaldototal_real", "Master_mlimitecompra_real"],
    "tc_utilizacion_total": ["Visa_msaldototal_real", "Master_msaldototal_real",
                             "Visa_mlimitecompra_real", "Master_mlimitecompra_real"],
    "tc_transacciones_total": ["ctarjeta_visa_transacciones", "ctarjeta_master_transacciones"],
    "prestamos_total": ["mprestamos_personales_real", "mprestamos_prendarios_real", "mprestamos_hipotecarios_real"],
    "margen_neto": ["mactivos_margen_real", "mpasivos_margen_real"],
    "liquidez_total_pesos": ["mcaja_ahorro_real", "mcuenta_corriente_real", "mplazo_fijo_pesos_real"],
    "digital_trx_total": ["chomebanking_transacciones", "cmobile_app_trx"],
    "ratio_deuda_ingreso": ["mprestamos_personales_real", "mprestamos_prendarios_real",
                            "mprestamos_hipotecarios_real", "mpayroll_real"],
    "ratio_digital_total_trx": ["chomebanking_transacciones", "cmobile_app_trx", "ctrx_quarter"],
    "prop_vida_en_banco": ["cliente_antiguedad", "cliente_edad"],
}
# Banderas que sobreviven A PROPÓSITO aunque su base se excluya (son el reemplazo
# robusto del monto: "cobra sueldo acá", "tiene algún préstamo").
FLAGS_QUE_SOBREVIVEN = {"tiene_payroll", "tiene_prestamos"}

# [Anotación · líneas 654–679] VARS_RANK = [] deja sin efecto construir_etapa3_rank_sql(), que para cada
#   variable listada agrega un rank por mes con cero fijo (CUME_DIST por signo: positivos en (0, 1], negativos
#   en [−1, 0), cero en 0). Con la lista vacía la función retorna sin crear columnas.
# Rank por mes ("rank cero fijo"): variables cuyo NIVEL driftea entre meses (límites de
# tarjeta: el PSI las descarta) pero cuya posición RELATIVA dentro del mes sigue siendo
# informativa. 0 sigue siendo 0, positivos -> (0, 1], negativos -> [-1, 0), NULL sigue NULL.
# Por construcción, su distribución es casi idéntica todos los meses (PSI ~ 0).
# v5: DESACTIVADO. En los límites (~145 valores distintos) el rank queda escalonado y daba
# PSI 0.24–0.25 por artefacto; se reemplaza por usar los límites en nominal (NO_DEFLACTAR).
VARS_RANK = []


def construir_etapa3_rank_sql(con: duckdb.DuckDBPyConnection, variables: list = VARS_RANK) -> None:
    """Agrega <var>_rank (rank cero fijo dentro de cada foto_mes) a etapa3_final."""
    columnas = _columnas(con, "etapa3_final")
    variables = [v for v in variables if v in columnas]
    if not variables:
        return
    exprs = []
    for v in variables:
        x = _col(v)
        exprs.append(f"""CASE
            WHEN {x} > 0 THEN CUME_DIST() OVER (PARTITION BY {_col(MES_COL)}, SIGN({x}) ORDER BY {x})
            WHEN {x} < 0 THEN -CUME_DIST() OVER (PARTITION BY {_col(MES_COL)}, SIGN({x}) ORDER BY {x} DESC)
            WHEN {x} = 0 THEN 0 END AS {_col(v + '_rank')}""")
    con.execute("ALTER TABLE etapa3_final RENAME TO etapa3_pre_rank")
    con.execute(f"CREATE TABLE etapa3_final AS SELECT *, {', '.join(exprs)} FROM etapa3_pre_rank")
    con.execute("DROP TABLE etapa3_pre_rank")
    print(f"Agregados {len(variables)} ranks por mes: {[v + '_rank' for v in variables]}")

# [Anotación · líneas 681–686] Ejecuta en orden deflactación, lags, ratios y rank, borrando cada tabla
#   intermedia cuando deja de usarse.
#%% celda 20 [código]
# Cada tabla intermedia se borra apenas deja de hacer falta.
construir_etapa3_deflactado_sql(con); con.execute("DROP TABLE etapa2")
construir_etapa3_lags_sql(con);       con.execute("DROP TABLE etapa3_deflactado")
construir_etapa3_ratios_sql(con);     con.execute("DROP TABLE etapa3_lags")
construir_etapa3_rank_sql(con)

# [Anotación · líneas 688–717] extraer_roles_sql(): lee etapa3_final y devuelve un DataFrame de pandas por
#   rol, convirtiendo en la consulta las columnas DOUBLE y DECIMAL a FLOAT (float32). Después cierra DuckDB,
#   borra la base temporal e imprime la memoria usada y las dimensiones de cada rol.
#%% celda 21 [texto]
## Extraer los roles como DataFrames de pandas

#%% celda 22 [código]
def extraer_roles_sql(con: duckdb.DuckDBPyConnection, tabla: str = "etapa3_final") -> dict:
    """Tabla final de DuckDB -> un DataFrame por rol, con los float64 pasados a float32
    (la mitad de memoria; a los árboles les sobra precisión)."""
    # El CAST a FLOAT se hace en SQL: así pandas nunca materializa la versión float64.
    tipos = con.execute(f"DESCRIBE {tabla}").df()
    select = ", ".join(
        f"CAST({_col(c)} AS FLOAT) AS {_col(c)}" if t.upper() in ("DOUBLE", "FLOAT8") or t.upper().startswith("DECIMAL")
        else _col(c)
        for c, t in zip(tipos["column_name"], tipos["column_type"])
    )
    return {
        r: con.execute(f"SELECT {select} FROM {tabla} WHERE {_col(ROL_COL)} = '{r}'").df()
        for r in ("historico", "train", "validacion", "aplicacion")
    }


roles = extraer_roles_sql(con)
print(f"Columnas tras Feature Engineering: {len(_columnas(con, 'etapa3_final'))}")
# DuckDB ya no se usa: se cierra y se borra la base temporal para liberar disco y memoria.
con.close()
for _f in (DUCKDB_PATH, DUCKDB_PATH + ".wal"):
    if os.path.exists(_f):
        os.remove(_f)
print(f"Memoria total: {sum(d.memory_usage(deep=True).sum() for d in roles.values()) / 1e9:.2f} GB")
for nombre, d in roles.items():
    print(f"  {nombre:12s}: {d.shape[0]:>8,} filas x {d.shape[1]} columnas")

# [Anotación · líneas 719–739] Parámetros del clustering: semilla 214363, 5 clusters y VARS_CLUSTER con las 14
#   variables usadas para agrupar clientes (edad, antigüedad, productos, transacciones del trimestre y
#   digitales, saldo, rentabilidad, margen neto, utilización de tarjetas, liquidez y 4 flags).
#%% celda 23 [texto]
## Etapa 4 — Clustering de Clientes (No Supervisado)

KMeans sobre variables de comportamiento (sin mirar el target), fit sólo en train y predict en el
resto. El cluster entra al modelo como **dummies** `cluster_1..k` (antes entraba como número 1–5,
lo que le sugería al modelo un orden que no existe). La tasa de BAJA por cluster es sólo un
diagnóstico, nunca un insumo de la feature.

#%% celda 24 [código]
SEED_CLUSTER = 214_363  # misma semilla que z501_cluster_rf
K_CLUSTERS = 5

VARS_CLUSTER = [
    "cliente_edad", "cliente_antiguedad", "cproductos",
    "ctrx_quarter", "digital_trx_total",
    "mcuentas_saldo_real", "mrentabilidad_real", "margen_neto",
    "tc_utilizacion_total", "liquidez_total_pesos",
    "tiene_visa", "tiene_master", "tiene_prestamos", "tiene_payroll",
]
# Nota: se quitó 'ratio_deuda_ingreso' respecto de la versión anterior, porque usa
# mpayroll_real y mprestamos_personales_real (excluidas por la hoja de ruta).


# [Anotación · líneas 742–772] construir_cluster(): recorta cada variable a los percentiles 1 y 99 de train,
#   imputa con la mediana de train, escala con RobustScaler y ajusta KMeans (k = 5, n_init = 20) sólo con train;
#   predice el cluster de los demás roles, renumera los clusters por tamaño (1 = el más numeroso) y agrega las
#   dummies cluster_1 a cluster_5.
def construir_cluster(roles: dict, variables: list = VARS_CLUSTER,
                       k: int = K_CLUSTERS, seed: int = SEED_CLUSTER) -> dict:
    """RobustScaler + KMeans con recorte p1–p99 (calculado en train). fit sólo en train."""
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import RobustScaler

    train = roles["train"]
    variables = [v for v in variables if v in train.columns]
    limites = {v: tuple(train[v].quantile([0.01, 0.99])) for v in variables}

    def _matriz(df):
        rec = pd.DataFrame({v: df[v].clip(*limites[v]) for v in variables})
        return rec.fillna(pd.Series({v: train[v].median() for v in variables}))

    scaler = RobustScaler()
    X_train = scaler.fit_transform(_matriz(train))
    kmeans = KMeans(n_clusters=k, n_init=20, random_state=seed)
    labels_train = kmeans.fit_predict(X_train)

    orden = pd.Series(labels_train).value_counts().index.tolist()   # 1 = el más numeroso
    remap = {viejo: nuevo + 1 for nuevo, viejo in enumerate(orden)}

    for nombre, df in roles.items():
        labels = labels_train if nombre == "train" else kmeans.predict(scaler.transform(_matriz(df)))
        df["cluster"] = pd.Series(labels, index=df.index).map(remap)
        for j in range(1, k + 1):
            df[f"cluster_{j}"] = (df["cluster"] == j).astype("int8")

    print(f"Etapa 4: KMeans k={k} (fit sólo en train) sobre {len(variables)} variables.")
    print(train["cluster"].value_counts().sort_index().to_string())
    return roles


# [Anotación · líneas 775–792] diagnostico_churn_por_cluster(): imprime la tasa de BAJA+1 o BAJA+2 por cluster
#   en train y validación; no genera variables. La celda siguiente ejecuta el clustering y el diagnóstico.
def diagnostico_churn_por_cluster(roles: dict) -> pd.DataFrame:
    """Tasa de BAJA (BAJA+1 o BAJA+2) por cluster en train/validación. Diagnóstico, NO feature."""
    partes = []
    for rol in ("train", "validacion"):
        df = roles[rol]
        es_baja = df[TARGET_COL].isin(["BAJA+1", "BAJA+2"])
        r = es_baja.groupby(df["cluster"]).agg(n_clientes="count", tasa_baja="mean")
        r["tasa_baja_pct"] = r.pop("tasa_baja") * 100
        r["rol"] = rol
        partes.append(r.reset_index())
    reporte = pd.concat(partes, ignore_index=True).sort_values(["cluster", "rol"])
    print("\nTasa de BAJA por cluster — diagnóstico, NO es feature:")
    print(reporte.round(3).to_string(index=False))
    return reporte

#%% celda 25 [código]
roles = construir_cluster(roles)
_ = diagnostico_churn_por_cluster(roles)

# [Anotación · líneas 794–819] Parámetros del drift: PSI con 10 buckets y umbrales 0,10 (alerta) y 0,25 (drift
#   sustancial). VARS_EXCLUIR_SIEMPRE contiene mpayroll_real, cpayroll_trx, mprestamos_personales_real y
#   cprestamos_personales. La columna cluster (número) no entra al modelo.
#%% celda 26 [texto]
## Etapa 5 — Data Drift (PSI) y selección de columnas

Umbrales de `z701_drifting`: PSI < 0.10 sin drift · 0.10–0.25 alerta temprana · > 0.25 drift sustancial.
Se compara **Train vs Aplicación (202108)**.

Cambios respecto de la versión anterior:
- Las columnas de `VARIABLES_ROTAS` se comparan sin los meses en que se pusieron en NA a mano.
- Las `*_rank` (Etapa 3) deberían dar PSI ~0: reemplazan a los límites de tarjeta que salen por drift.
- Para `lag{k}_`/`delta{k}_` se usa sólo la parte de train donde el lag existe de verdad
  (meses con al menos k meses previos en el dataset), así no se confunde NaN estructural con drift.
- **La exclusión se propaga:** si se saca una variable base (por hoja de ruta o por PSI), también
  salen sus `lag/delta`. Las derivadas (`DERIVADAS`) de una variable de la hoja de ruta salen
  siempre; las de una variable con drift salen si su propio PSI está en alerta (> 0.10).
  Las banderas `tiene_payroll`/`tiene_prestamos` sobreviven a propósito.

#%% celda 27 [código]
PSI_BUCKETS = 10
PSI_UMBRAL_ALERTA = 0.10
PSI_UMBRAL_SUSTANCIAL = 0.25

# Variables base que la hoja de ruta pide sacar siempre (aguinaldo / cambio de estructura).
VARS_EXCLUIR_SIEMPRE = ["mpayroll_real", "cpayroll_trx", "mprestamos_personales_real", "cprestamos_personales"]

# Nunca son features (el cluster entra como dummies).
COLS_NO_MODELO = {"cluster"}

# [Anotación · líneas 821–853] _psi_bins(): arma los buckets del PSI con cuantiles sobre la unión de los
#   valores válidos de ambas muestras, más un bucket para nulos y otro opcional para el valor centinela, y
#   devuelve la proporción esperada y la actual de cada bucket.
#%% celda 28 [código]
def _psi_bins(expected: pd.Series, actual: pd.Series, buckets: int = PSI_BUCKETS,
              valor_centinela=None) -> pd.DataFrame:
    """Bins de PSI como z701: cuantiles sobre la unión de válidos + buckets aparte para nulos y centinela."""
    exp_null = expected.isna().mean() if len(expected) else 0.0
    act_null = actual.isna().mean() if len(actual) else 0.0
    exp_v, act_v = expected.dropna(), actual.dropna()

    exp_cent = act_cent = 0.0
    if valor_centinela is not None:
        exp_cent = float((exp_v == valor_centinela).mean()) * (1 - exp_null) if len(exp_v) else 0.0
        act_cent = float((act_v == valor_centinela).mean()) * (1 - act_null) if len(act_v) else 0.0
        exp_v, act_v = exp_v[exp_v != valor_centinela], act_v[act_v != valor_centinela]

    union = pd.concat([exp_v, act_v])
    cortes = None
    if union.nunique() > 1:
        _, cortes = pd.qcut(union, q=buckets, retbins=True, duplicates="drop")

    resto_exp, resto_act = 1.0 - exp_null - exp_cent, 1.0 - act_null - act_cent
    filas = []
    if cortes is None or len(cortes) < 2:
        filas.append({"Bucket": "unico", "Expected_Prop": resto_exp, "Actual_Prop": resto_act})
    else:
        exp_prop = pd.cut(exp_v, bins=cortes, include_lowest=True).value_counts(normalize=True, sort=False) * resto_exp
        act_prop = pd.cut(act_v, bins=cortes, include_lowest=True).value_counts(normalize=True, sort=False) * resto_act
        for b in exp_prop.index:
            filas.append({"Bucket": str(b), "Expected_Prop": exp_prop.get(b, 0.0), "Actual_Prop": act_prop.get(b, 0.0)})
    if exp_null > 0 or act_null > 0:
        filas.append({"Bucket": "Null_Values", "Expected_Prop": exp_null, "Actual_Prop": act_null})
    if exp_cent > 0 or act_cent > 0:
        filas.append({"Bucket": "Centinela", "Expected_Prop": exp_cent, "Actual_Prop": act_cent})
    return pd.DataFrame(filas).fillna(0.0)


# [Anotación · líneas 856–877] psi(): suma (actual − esperado) × ln(actual / esperado) sobre los buckets, con
#   piso de 1e-10 en las proporciones. _orden_lag() devuelve 1 o 2 si la columna es un lag o delta de ese orden
#   y _base_de() devuelve el nombre de la variable base de un lag o delta.
def psi(expected: pd.Series, actual: pd.Series, buckets: int = PSI_BUCKETS, valor_centinela=None) -> float:
    """PSI tal cual z701_drifting, con bucket opcional para un centinela."""
    if expected.empty and actual.empty:
        return 0.0
    df = _psi_bins(expected, actual, buckets=buckets, valor_centinela=valor_centinela)
    e = np.maximum(df["Expected_Prop"].to_numpy(dtype=float), 1e-10)
    a = np.maximum(df["Actual_Prop"].to_numpy(dtype=float), 1e-10)
    total = float(np.sum((a - e) * np.log(a / e)))
    return total if not np.isnan(total) else np.inf


def _orden_lag(col: str) -> int:
    """1 para lag1_/delta1_, 2 para lag2_/delta2_, 0 si no es un lag."""
    for k in (1, 2):
        if col.startswith((f"lag{k}_", f"delta{k}_")):
            return k
    return 0


def _base_de(col: str) -> str:
    """'delta2_mpayroll_real' -> 'mpayroll_real'."""
    return col.split("_", 1)[1] if _orden_lag(col) else col


# [Anotación · líneas 880–912] analizar_drift(): calcula el PSI de cada columna numérica entre train y
#   aplicación (202108). Para lag{k} y delta{k} usa sólo las filas de train con k meses previos en el dataset;
#   para las variables de VARIABLES_ROTAS deja afuera los meses puestos en NULL y los k siguientes; para las
#   columnas con centinela 999.999 usa un bucket aparte. Etiqueta cada columna según los umbrales e imprime las
#   20 de mayor PSI.
def analizar_drift(roles: dict, columnas: list = None) -> pd.DataFrame:
    """PSI Train vs Aplicación. Para lag{k}/delta{k} sólo filas de train con k meses previos en el dataset."""
    train, aplic = roles["train"], roles["aplicacion"]
    if columnas is None:
        columnas = [c for c in train.select_dtypes(include=[np.number]).columns
                    if c not in COLS_NO_FEATURE | COLS_NO_MODELO and not c.startswith("cluster_")]
    per_train = train[MES_COL].map(periodo)

    filas = []
    for c in columnas:
        if c not in aplic.columns:
            continue
        k = _orden_lag(c)
        base = train[per_train >= periodo(PRIMER_MES) + k] if k else train
        destino = aplic
        base_c = _base_de(c)
        if base_c in VARIABLES_ROTAS:
            # El NA puesto a mano no es drift: se comparan sólo meses sanos. Para un lag/delta
            # de orden k también quedan afectados los k meses siguientes al mes roto.
            malos = {periodo(m) for m in VARIABLES_ROTAS[base_c]}
            afectado = lambda df: df[MES_COL].map(periodo).map(lambda p: any(0 <= p - b <= k for b in malos))
            base = base[~afectado(base)]
            destino = aplic[~afectado(aplic)]
        valor = psi(base[c], destino[c], valor_centinela=CENTINELA_ALTO if c in COLS_EXTREMO_ALTO else None)
        filas.append({"columna": c, "psi": valor})

    reporte = pd.DataFrame(filas).sort_values("psi", ascending=False).reset_index(drop=True)
    reporte["alerta"] = np.select(
        [reporte["psi"] > PSI_UMBRAL_SUSTANCIAL, reporte["psi"] > PSI_UMBRAL_ALERTA],
        ["DRIFT SUSTANCIAL", "alerta temprana"], default="sin drift significativo")
    print("PSI Train vs Aplicación (202108) — primeras 20:")
    print(reporte.head(20).round(4).to_string(index=False))
    return reporte


# [Anotación · líneas 915–958] seleccionar_columnas_modelo(): arma la lista de variables del modelo excluyendo
#   (a) las de VARS_EXCLUIR_SIEMPRE con todos sus lags, deltas y derivadas, salvo los flags que sobreviven, y
#   (b) las de PSI > 0,25, los lags y deltas de variables base con drift y las derivadas de éstas cuyo PSI
#   propio supera 0,10. Imprime cada exclusión con su motivo y las columnas que quedan con PSI entre 0,10 y
#   0,25.
def seleccionar_columnas_modelo(roles: dict, reporte_psi: pd.DataFrame,
                                 vars_siempre: list = VARS_EXCLUIR_SIEMPRE,
                                 umbral_excluir: float = PSI_UMBRAL_SUSTANCIAL) -> list:
    """
    Lista final de features. Excluye:
      (a) variables de la hoja de ruta + TODOS sus lags/deltas + sus derivadas (salvo banderas),
      (b) variables con PSI > umbral_excluir + sus lags/deltas + derivadas cuyo propio PSI > alerta.
    """
    train = roles["train"]
    todas = [c for c in train.columns if c not in COLS_NO_FEATURE | COLS_NO_MODELO]
    psi_de = dict(zip(reporte_psi["columna"], reporte_psi["psi"]))

    por_psi = set(reporte_psi.loc[reporte_psi["psi"] > umbral_excluir, "columna"])
    bases_siempre = set(vars_siempre)
    # Sólo variables "base" con drift propagan a sus lags/deltas (que un delta2_ tenga
    # drift no implica que la variable base lo tenga).
    bases_psi = {c for c in por_psi if not _orden_lag(c)}

    motivo = {}
    for c in todas:
        base = _base_de(c)
        if base in bases_siempre:
            motivo[c] = "hoja de ruta" + (" (lag/delta)" if base != c else "")
        elif c in por_psi:
            motivo[c] = "PSI > umbral"
        elif base in bases_psi:
            motivo[c] = f"lag/delta de variable con drift ({base})"
        elif c in DERIVADAS and c not in FLAGS_QUE_SOBREVIVEN:
            deps = set(DERIVADAS[c])
            if deps & bases_siempre:
                motivo[c] = f"derivada de {sorted(deps & bases_siempre)} (hoja de ruta)"
            elif deps & bases_psi and psi_de.get(c, 0) > PSI_UMBRAL_ALERTA:
                motivo[c] = f"derivada de {sorted(deps & bases_psi)} con PSI {psi_de[c]:.3f} > {PSI_UMBRAL_ALERTA}"

    finales = [c for c in todas if c not in motivo]
    alerta = [c for c in finales if PSI_UMBRAL_ALERTA < psi_de.get(c, 0) <= umbral_excluir]

    print("Columnas excluidas y motivo:")
    for c, m in sorted(motivo.items(), key=lambda x: (x[1], x[0])):
        print(f"  {c:40s} {m}")
    print(f"\nOJO — siguen en el modelo pero en alerta temprana (PSI {PSI_UMBRAL_ALERTA}–{umbral_excluir}), "
          f"revisalas: {alerta}")
    print(f"\nColumnas finales para el modelo: {len(finales)} (de {len(todas)})")
    return finales

# [Anotación · líneas 960–962] Ejecuta el análisis de drift y la selección de columnas; el resultado queda en
#   columnas_modelo.
#%% celda 29 [código]
reporte_psi = analizar_drift(roles)
columnas_modelo = seleccionar_columnas_modelo(roles, reporte_psi)

# [Anotación · líneas 964–991] Celda de texto conservada de la versión con Optuna: describe los tres
#   experimentos (rf_ternario, rf_binario, lgbm_binario), el entrenamiento sin undersampling, el objetivo
#   (ganancia máxima de la curva suavizada en 202106) y el costo por trial. En este notebook la búsqueda no se
#   ejecuta (ver la celda de la línea 1419).
#%% celda 30 [texto]
## Etapa 6 — Comparación de modelos con Optuna (sin undersampling)

Tres experimentos, **mismo objetivo y misma validación (202106)**:

| Experimento | Algoritmo | Target de entrenamiento | Score usado para ordenar |
|---|---|---|---|
| `rf_ternario` | Random Forest | CONTINUA / BAJA+1 / BAJA+2 | P(BAJA+2) |
| `rf_binario` | Random Forest | BAJA+1 ∪ BAJA+2 = 1, CONTINUA = 0 | P(BAJA) |
| `lgbm_binario` | LightGBM | BAJA+1 ∪ BAJA+2 = 1, CONTINUA = 0 | P(BAJA) |

**Sin undersampling:** cada trial entrena con el 100% de las filas de train (todos los CONTINUA).
Hay un `assert` que lo verifica antes de lanzar Optuna.

**Objetivo:** ganancia máxima de la curva acumulada **suavizada** sobre 202106 (sólo BAJA+2 suma).

**Costo por trial:**
- RF: árboles fijos en `RF_ARBOLES_OPTUNA` (100) y 1 semilla por trial. En un RF más árboles nunca
  empeora, sólo reduce ruido; por eso no se optimiza y se sube recién en el semillero (`RF_ARBOLES_FINAL`).
  Aun así, sin undersampling cada trial puede tardar 10–20 min: con el `timeout` de 2 h vas a tener
  pocos trials. Si querés comparar en serio, subí el timeout o corré estas celdas de noche.
- LightGBM: 3 semillas por trial (3–5 min por trial en tu máquina). 150 trials / 4 h.
  **Warm start:** los 5 mejores trials (sin repetir) de los estudios v4 y v3 se encolan primero.
  Se optimiza sobre las columnas de la variante elegida en la Etapa 6a.
- **RF desactivado** (`"activo": False`): si querés volver a compararlo, activalo.

Estudios en `modelos/optuna_<experimento>_v5.db` (se retoman solos si interrumpís).
Para saltear un experimento, poné `"activo": False`.

# [Anotación · líneas 993–1019] Importa optuna, RandomForestClassifier, SimpleImputer y lightgbm. Con
#   numpy.random.seed(17) sortea 50 semillas sin reposición: las 3 primeras son SEMILLAS_OPTUNA y las 47
#   restantes SEMILLAS_SEMILLERO. Define N_SEMILLERO, la cantidad de árboles del Random Forest, la ventana de
#   suavizado (401 envíos) y WARM_START_TOP = 5.
#%% celda 31 [código]
import optuna
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer

try:
    import lightgbm as lgb
except ImportError:
    lgb = None
    print("OJO: LightGBM no está instalado (pip install lightgbm). Se saltea 'lgbm_binario'.")

optuna.logging.set_verbosity(optuna.logging.WARNING)

SEMILLA_BASE = 17
np.random.seed(SEMILLA_BASE)
SEMILLAS = np.random.choice(1_000_000, size=50, replace=False).tolist()
SEMILLAS_OPTUNA = SEMILLAS[:3]          # como mucho 3 por trial
SEMILLAS_SEMILLERO = SEMILLAS[3:]       # disjuntas de las de Optuna (47 disponibles)

# Modelos en el semillero según el algoritmo ganador (LightGBM es barato -> más modelos)
N_SEMILLERO = {"lgbm": 30, "rf": 10}
RF_ARBOLES_OPTUNA = 100   # fijo durante Optuna
RF_ARBOLES_FINAL = 300    # por modelo del semillero -> total = RF_ARBOLES_FINAL * N_SEMILLERO["rf"]

VENTANA_SUAVIZADO = 41 if MODO_PRUEBA else 401      # envíos de la media móvil (impar)
VERSION_ESTUDIO = "v11_prueba" if MODO_PRUEBA else "v11"
WARM_START_TOP = 5

# [Anotación · líneas 1021–1046] PARAMS_CATEDRA_FIJOS y el diccionario EXPERIMENTOS con la configuración de
#   los estudios de Optuna (rf_ternario, rf_binario y lgbm_catedra con activo = False; lgbm_binario con 60
#   trials, timeout de 9.000 s y bases de warm start). Estas definiciones no se usan en este notebook porque no
#   se llama a correr_experimento().
# Receta de la cátedra (última clase): hiperparámetros fijos; Optuna sólo toca num_iterations,
# num_leaves y min_sum_hessian_in_leaf. Sin undersampling.
PARAMS_CATEDRA_FIJOS = {"learning_rate": 0.005, "max_bin": 31, "min_data_in_leaf": 0,
                        "feature_fraction": 0.50, "feature_fraction_bynode": 0.20, "metric": "auc"}

EXPERIMENTOS = {
    # RF desactivado desde la v5: en la v4 hizo 2 trials en 2 h y quedó ~40 BAJA+2 abajo de LightGBM.
    "rf_ternario":  {"algoritmo": "rf", "target": "ternario", "semillas_optuna": 1,
                     "n_trials": 20, "timeout": 2 * 3600, "activo": False},
    "rf_binario":   {"algoritmo": "rf", "target": "binario", "semillas_optuna": 1,
                     "n_trials": 20, "timeout": 2 * 3600, "activo": False},
    # Retoma el estudio de la v9 (37 trials hechos): corre hasta completar n_trials. Si cambian las
    # columnas o el decay elegidos en la 6a, poné "db_version": "v11" para empezar un estudio nuevo.
    "lgbm_binario": {"algoritmo": "lgbm", "target": "binario", "semillas_optuna": 3,
                     "n_trials": 60, "timeout": 9000, "activo": True, "db_version": "v9",
                     "warm_start_db": ["optuna_lgbm_binario_v5.db", "optuna_lgbm_binario_v4.db", "optuna_lgbm_binario_v3.db"]},
    "lgbm_catedra": {"algoritmo": "lgbm", "target": "binario", "semillas_optuna": 3,
                     "n_trials": 40, "timeout": 3 * 3600, "activo": False, "receta": "catedra",
                     "params_fijos": PARAMS_CATEDRA_FIJOS, "db_version": "v11",
                     "enqueue": [{"num_leaves": 64, "min_sum_hessian_in_leaf": 5.0, "num_boost_round": 1200}]},
}
if MODO_PRUEBA:
    N_SEMILLERO = {"lgbm": 2, "rf": 2}
    for cfg in EXPERIMENTOS.values():
        cfg.update(n_trials=2, timeout=600)
        cfg.pop("db_version", None)

# [Anotación · líneas 1048–1073] curva_ganancia(): ordena por score descendente y acumula +1.072.500 por cada
#   BAJA+2 y −27.500 por cada otro cliente. suavizar(): media móvil centrada de 401 posiciones.
#   ganancia_max_suavizada(): máximo de la curva suavizada. construir_y(): con target 'binario' devuelve 1 para
#   BAJA+1 o BAJA+2 y 0 para el resto; con 'ternario' devuelve la clase original.
#%% celda 32 [texto]
### Funciones de ganancia, targets, preprocesamiento y entrenamiento

#%% celda 33 [código]
def curva_ganancia(score, y_true):
    """Ordena de mayor a menor score y acumula la ganancia (sólo BAJA+2 es acierto)."""
    orden = np.argsort(-np.asarray(score), kind="mergesort")
    gan = np.where(np.asarray(y_true)[orden] == "BAJA+2", ganancia_acierto, -costo_estimulo)
    return orden, np.cumsum(gan)


def suavizar(acum, ventana: int = VENTANA_SUAVIZADO):
    """Media móvil centrada: un acierto suelto no mueve el óptimo."""
    return pd.Series(acum).rolling(ventana, center=True, min_periods=1).mean().to_numpy()


def ganancia_max_suavizada(score, y_true, ventana: int = VENTANA_SUAVIZADO) -> float:
    return float(suavizar(curva_ganancia(score, y_true)[1], ventana).max())


def construir_y(serie: pd.Series, target: str) -> np.ndarray:
    if target == "ternario":
        return serie.to_numpy()
    if target == "binario":
        return serie.isin(["BAJA+1", "BAJA+2"]).astype(int).to_numpy()
    raise ValueError(target)


# [Anotación · líneas 1076–1105] preparar_preprocesador() y transformar(): para LightGBM no se imputa (la
#   matriz pasa a float32 con sus NaN); para Random Forest se ajusta un SimpleImputer por mediana con
#   indicadores de faltante, sin el indicador de las variables de VARIABLES_ROTAS. params_finales() agrega
#   n_estimators = 300 sólo para Random Forest y no se llama en este notebook.
def preparar_preprocesador(algoritmo: str, df_fit: pd.DataFrame, columnas: list):
    """
    LightGBM: nada (usa los NaN de forma nativa).
    RF: mediana (fit en df_fit) + indicadores de faltante, SALVO para VARIABLES_ROTAS:
    su indicador sería una "marca de mes" (sólo vale 1 en el mes roto) y el modelo
    podría aprender algo propio de ese mes. Para el RF esas filas quedan con la mediana.
    """
    if algoritmo == "lgbm":
        return None, list(columnas)
    imp = SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)
    imp.fit(df_fit[columnas].astype("float32"))
    nombres = list(imp.get_feature_names_out())
    sacar = {f"missingindicator_{c}" for c in VARIABLES_ROTAS}
    keep = np.array([i for i, n in enumerate(nombres) if n not in sacar])
    return {"imp": imp, "keep": keep}, [nombres[i] for i in keep]


def transformar(prep, df: pd.DataFrame, columnas: list) -> np.ndarray:
    X = df[columnas].astype("float32")
    if prep is None:
        return X.to_numpy()
    return prep["imp"].transform(X)[:, prep["keep"]].astype(np.float32)


def params_finales(algoritmo: str, params: dict) -> dict:
    """Agrega lo que no optimiza Optuna (cantidad de árboles del RF en el semillero)."""
    p = dict(params)
    if algoritmo == "rf":
        p["n_estimators"] = RF_ARBOLES_FINAL
    return p


# [Anotación · líneas 1108–1122] entrenar(): para LightGBM separa num_boost_round, fija objective = 'binary',
#   bagging_freq = 1, la semilla y num_threads = cantidad de CPU, y entrena con lgb.train usando los pesos por
#   fila si se pasan. score_modelo() devuelve la probabilidad predicha (en Random Forest, la de la clase BAJA+2
#   o la de la clase positiva).
def entrenar(algoritmo: str, params: dict, X, y, seed: int, w=None):
    if algoritmo == "rf":
        p = {"n_estimators": RF_ARBOLES_OPTUNA, **params}
        return RandomForestClassifier(**p, random_state=seed, n_jobs=-1).fit(X, y, sample_weight=w)
    p = dict(params)
    n_rounds = p.pop("num_boost_round")
    p.update(objective="binary", bagging_freq=1, verbosity=-1, seed=seed, num_threads=os.cpu_count())
    return lgb.train(p, lgb.Dataset(X, label=y, weight=w), num_boost_round=n_rounds)


def score_modelo(modelo, X, algoritmo: str, target: str) -> np.ndarray:
    if algoritmo == "lgbm":
        return modelo.predict(X)
    clases = list(modelo.classes_)
    return modelo.predict_proba(X)[:, clases.index("BAJA+2" if target == "ternario" else 1)]


# [Anotación · líneas 1125–1148] sugerir_params(): espacios de búsqueda de Optuna para Random Forest, para la
#   receta 'catedra' (3 hiperparámetros libres sobre parámetros fijos) y para LightGBM (learning_rate 0,01–0,1;
#   num_leaves 8–1024; min_data_in_leaf 50–5000; feature_fraction 0,1–0,8; bagging_fraction 0,5–1; lambda_l2
#   0,001–100; num_boost_round 100–2000). No se invoca en este notebook.
def sugerir_params(trial, algoritmo: str, receta: str = None) -> dict:
    if algoritmo == "rf":   # espacio de exp_401, sin n_estimators (fijo, ver arriba)
        return {
            "max_depth": trial.suggest_int("max_depth", 2, 40),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 2000),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 200),
            "max_features": trial.suggest_float("max_features", 0.05, 0.7),
            "max_leaf_nodes": trial.suggest_int("max_leaf_nodes", 10, 5000),
            "max_samples": trial.suggest_float("max_samples", 0.5, 0.9),
        }
    if receta == "catedra":   # fijos + 3 hiperparámetros bayesianos
        return {**PARAMS_CATEDRA_FIJOS,
                "num_leaves": trial.suggest_int("num_leaves", 8, 1024, log=True),
                "min_sum_hessian_in_leaf": trial.suggest_float("min_sum_hessian_in_leaf", 0.1, 50.0, log=True),
                "num_boost_round": trial.suggest_int("num_boost_round", 400, 4000, log=True)}
    return {   # mismo espacio que v3 (necesario para el warm start)
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 8, 1024, log=True),
        "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 50, 5000, log=True),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.1, 0.8),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.5, 1.0),
        "lambda_l2": trial.suggest_float("lambda_l2", 1e-3, 100, log=True),
        "num_boost_round": trial.suggest_int("num_boost_round", 100, 2000, log=True),
    }


# [Anotación · líneas 1151–1171] correr_semillero(): entrena un modelo por semilla con los mismos
#   hiperparámetros, predice sobre cada matriz recibida y descarta el modelo; devuelve los scores por semilla y
#   la importancia (gain, normalizada a suma 1) promediada entre semillas.
def correr_semillero(algoritmo: str, target: str, params: dict, X_fit, y_fit,
                     X_preds: list, nombres: list, semillas: list, w_fit=None):
    """
    Entrena un modelo por semilla, predice sobre cada matriz de X_preds y lo DESCARTA
    (no acumula modelos en RAM). Devuelve: lista con un array (n_semillas x n_filas) de
    scores por cada X_pred, y las importancias promedio.
    """
    scores = [[] for _ in X_preds]
    imps = []
    for i, s in enumerate(semillas, 1):
        t0 = time.time()
        m = entrenar(algoritmo, params, X_fit, y_fit, s, w_fit)
        for j, X in enumerate(X_preds):
            scores[j].append(score_modelo(m, X, algoritmo, target))
        imp = m.feature_importances_ if algoritmo == "rf" else m.feature_importance("gain").astype(float)
        imps.append(imp / max(imp.sum(), 1e-12))
        del m
        print(f"  modelo {i}/{len(semillas)} (semilla {s}) en {(time.time() - t0) / 60:.1f} min")
    importancias = (pd.DataFrame({"variable": nombres, "importancia_media": np.mean(imps, axis=0)})
                    .sort_values("importancia_media", ascending=False).reset_index(drop=True))
    return [np.array(sc) for sc in scores], importancias

# [Anotación · líneas 1173–1186] pesos_mes(): el peso de cada fila es decay elevado a los meses de antigüedad
#   respecto del último mes del conjunto de entrenamiento. pesos_df() devuelve None si el decay es 1,0.
#   DECAY_ELEGIDO se inicializa en 1,0 y se redefine en la línea 1401.
# ---- v9: pesos por mes -------------------------------------------------------------------
DECAY_ELEGIDO = 1.0   # lo fija la Etapa 6a (1.0 = todos los meses pesan igual)


def pesos_mes(meses: pd.Series, decay: float) -> np.ndarray:
    """peso = decay ** (meses de antigüedad respecto del último mes del conjunto de entrenamiento)."""
    per = meses.map(periodo).to_numpy()
    return (decay ** (per.max() - per)).astype("float64")


def pesos_df(df: pd.DataFrame, decay: float = None):
    """Pesos de un DataFrame de entrenamiento con el decay elegido (None si no hay pesos)."""
    d = DECAY_ELEGIDO if decay is None else decay
    return None if d == 1.0 else pesos_mes(df[MES_COL], d)

# [Anotación · líneas 1188–1221] _trials_previos() lee los trials completos de estudios de Optuna guardados en
#   modelos/ y los ordena por valor; encolar_warm_start() encola en un estudio vacío los 5 de mayor valor sin
#   repetir parámetros. No se invocan en este notebook.
#%% celda 34 [código]
def _trials_previos(nombre: str, dbs) -> list:
    """Trials completos de estudios anteriores (lista de .db en MODELOS_PATH), mejor primero."""
    if isinstance(dbs, str):
        dbs = [dbs]
    trials = []
    for db in dbs or []:
        ruta = os.path.join(MODELOS_PATH, db)
        if not os.path.exists(ruta):
            continue
        try:
            viejo = optuna.load_study(study_name=nombre, storage="sqlite:///" + ruta.replace("\\", "/"))
        except Exception as e:
            print(f"[{nombre}] no se pudo leer {db}: {e}")
            continue
        trials += [(t.value, t.params, db) for t in viejo.trials if t.state == optuna.trial.TrialState.COMPLETE]
    return sorted(trials, key=lambda x: x[0], reverse=True)


def encolar_warm_start(study, nombre: str, dbs, top: int = WARM_START_TOP) -> None:
    """Encola los 'top' mejores trials (sin repetir parámetros) de estudios anteriores."""
    if len(study.trials) > 0:
        return
    vistos, n = set(), 0
    for valor, params, db in _trials_previos(nombre, dbs):
        clave = tuple(sorted(params.items()))
        if clave in vistos:
            continue
        vistos.add(clave)
        study.enqueue_trial(params)
        n += 1
        print(f"[{nombre}] warm start: encolado trial de {db} (valor allá {valor:,.0f})")
        if n >= top:
            break


# [Anotación · líneas 1224–1287] correr_experimento(): función que ejecuta un estudio de Optuna (sampler TPE
#   con semilla 17, almacenamiento en SQLite, reanudable): entrena con todas las filas de train y pesos por mes,
#   promedia las probabilidades de las semillas del trial y devuelve la ganancia máxima suavizada en 202106.
#   Incluye el assert de que la matriz tiene el 100 % de las filas de train. En este notebook no se llama;
#   resultados queda como diccionario vacío.
def correr_experimento(nombre: str, roles: dict, columnas: list) -> dict:
    """Optuna para un experimento. Persiste en sqlite y retoma lo ya corrido."""
    cfg = EXPERIMENTOS[nombre]
    algoritmo, target = cfg["algoritmo"], cfg["target"]
    if not cfg.get("activo", True):
        print(f"[{nombre}] salteado (activo=False).")
        return None
    if algoritmo == "lgbm" and lgb is None:
        print(f"[{nombre}] salteado: LightGBM no está instalado.")
        return None

    prep, _ = preparar_preprocesador(algoritmo, roles["train"], columnas)
    X_tr = transformar(prep, roles["train"], columnas)
    X_va = transformar(prep, roles["validacion"], columnas)
    y_tr = construir_y(roles["train"][TARGET_COL], target)
    y_va = roles["validacion"][TARGET_COL].to_numpy()
    w_tr = pesos_df(roles["train"])
    print(f"[{nombre}] decay de pesos por mes: {DECAY_ELEGIDO}")

    # Sin undersampling: la matriz de Optuna tiene TODAS las filas de train.
    assert len(X_tr) == len(roles["train"]) == len(y_tr), "Optuna debe usar el 100% de train"
    dist = pd.Series(roles["train"][TARGET_COL]).value_counts().to_dict()
    print(f"[{nombre}] train para Optuna: {len(X_tr):,} filas (sin undersampling) {dist}")

    semillas = SEMILLAS_OPTUNA[:cfg["semillas_optuna"]]

    def objective(trial):
        params = sugerir_params(trial, algoritmo, cfg.get("receta"))
        scores = [score_modelo(entrenar(algoritmo, params, X_tr, y_tr, s, w_tr), X_va, algoritmo, target)
                  for s in semillas]
        return ganancia_max_suavizada(np.mean(scores, axis=0), y_va)

    storage = "sqlite:///" + os.path.join(MODELOS_PATH, f"optuna_{nombre}_{cfg.get('db_version', VERSION_ESTUDIO)}.db").replace("\\", "/")
    study = optuna.create_study(direction="maximize", study_name=nombre, storage=storage,
                                load_if_exists=True, sampler=optuna.samplers.TPESampler(seed=SEMILLA_BASE))
    encolar_warm_start(study, nombre, cfg.get("warm_start_db", []))
    if not study.trials:
        for p in cfg.get("enqueue", []):
            study.enqueue_trial(p)

    hechos = sum(t.state == optuna.trial.TrialState.COMPLETE for t in study.trials)
    faltan = max(0, cfg["n_trials"] - hechos)
    print(f"[{nombre}] trials completos previos: {hechos} | a correr: {faltan} "
          f"(timeout {cfg['timeout'] / 60:.0f} min, {len(semillas)} semilla/s por trial)")

    t0 = time.time()
    try:
        if faltan:
            study.optimize(objective, n_trials=faltan, timeout=cfg["timeout"], show_progress_bar=True)
    except KeyboardInterrupt:
        print("Interrumpido: se usa el mejor trial hasta ahora (el estudio queda guardado).")

    completos = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    if not completos:
        print(f"[{nombre}] sin trials completos.")
        return None
    print(f"[{nombre}] {(time.time() - t0) / 60:.1f} min | trials completos: {len(completos)} | "
          f"mejor ganancia suavizada en 202106: {study.best_value:,.0f}")
    print(f"[{nombre}] mejores parámetros: {study.best_params}")
    return {"nombre": nombre, **cfg, "study": study, "best_value": study.best_value,
            "best_params": study.best_params, "n_trials_ok": len(completos)}


resultados = {}

# [Anotación · líneas 1289–1308] N_VARS_HIST = 25 y VARS_HIST_FIJAS: las 25 variables base escritas en el
#   código para las que se calculan variables de historia. La celda de texto anterior describe los 7 sufijos que
#   se generan.
#%% celda 35 [texto]
## Etapa 6-pre — Features de historia (v9)

Para las `N_VARS_HIST` variables más importantes (ranking por ganancia de un LightGBM rápido entrenado **sólo en train**) se calculan, sobre los últimos 3 meses (t, t-1, t-2, que deben ser consecutivos):
`_m3` (media), `_s3` (desvío), `_mn3` / `_mx3` (mínimo y máximo), `_cv3` (desvío relativo), `_xvsm3` (cuánto se aparta el mes actual de la media) y `_racha3` (0, 1 o 2 caídas consecutivas).

**Límite de los datos:** hay 6 meses (03–08), así que estas columnas sólo existen desde 202105 (en train de validación: sólo 202105; en el final: 05 y 06). Las filas sin 3 meses de historia quedan en NaN, igual que los `lag2_`.
Cada feature nueva pasa por el filtro de PSI (train con valor vs. 202108).

#%% celda 36 [código]
import warnings
N_VARS_HIST = 25
VARS_HIST_FIJAS = ['mcaja_ahorro_real', 'mpasivos_margen_real', 'ctrx_quarter', 'ctarjeta_visa_transacciones',
                   'ccomisiones_mantenimiento', 'mcuentas_saldo_real', 'liquidez_total_pesos', 'mautoservicio_real',
                   'mrentabilidad_annual_real', 'tc_utilizacion_total', 'mtarjeta_visa_consumo_real',
                   'ctarjeta_debito_transacciones', 'Visa_mpagospesos_real', 'mactivos_margen_real', 'mrentabilidad_real',
                   'tc_saldo_total', 'cproductos', 'tc_consumo_total', 'tc_transacciones_total', 'mcuenta_corriente_real',
                   'mtransferencias_recibidas_real', 'ccajas_consultas', 'margen_neto', 'Visa_msaldopesos_real',
                   'mextraccion_autoservicio_real']
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)


# [Anotación · líneas 1311–1327] _importancia_por_base() entrena un LightGBM de 150 rondas sobre train y suma
#   la importancia (gain) por variable base; está definida y no se llama en este notebook. _desplazar() devuelve
#   el valor de k meses antes del mismo cliente sólo si esa fila está exactamente k períodos atrás; si no, NaN.
def _importancia_por_base(roles: dict, columnas: list) -> pd.Series:
    """Ganancia de un LightGBM rápido (train), sumada por variable base (lag/delta -> su base)."""
    X = roles["train"][columnas].astype("float32").to_numpy()
    y = construir_y(roles["train"][TARGET_COL], "binario")
    p = {"learning_rate": 0.05, "num_leaves": 35, "min_data_in_leaf": 373, "feature_fraction": 0.2,
         "bagging_fraction": 0.9, "lambda_l2": 8.0, "num_boost_round": 150}
    m = entrenar("lgbm", p, X, y, SEMILLA_BASE)
    imp = pd.Series(m.feature_importance("gain"), index=columnas)
    return imp.groupby([_base_de(c) for c in columnas]).sum().sort_values(ascending=False)


def _desplazar(a: np.ndarray, ids: np.ndarray, per: np.ndarray, k: int) -> np.ndarray:
    """a[t-k] del mismo cliente si ese mes es exactamente k meses antes; NaN si no."""
    out = np.full(a.shape, np.nan, dtype=np.float32)
    ok = (ids[k:] == ids[:-k]) & ((per[k:] - per[:-k]) == k)
    out[k:] = np.where(ok, a[:-k], np.nan)
    return out


# [Anotación · líneas 1330–1360] Toma la lista fija de 25 variables (assert de que existan), arma un panel con
#   todos los roles ordenado por cliente y mes y, para cada variable, apila el valor del mes y los de 1 y 2
#   meses antes para calcular: media (_m3), desvío (_s3), mínimo (_mn3), máximo (_mx3), desvío / |media| (_cv3),
#   (valor − media) / |media| (_xvsm3) y cantidad de caídas entre meses seguidos, de 0 a 2 (_racha3). Si falta
#   alguno de los tres meses el resultado es NaN.
NUEVAS_HIST = []
if lgb is None:
    print("LightGBM no está instalado: no se generan features de historia.")
else:
    # ENTREGA: lista fija. En la corrida original estas 25 variables salieron de un LightGBM rápido
    # (ranking por ganancia, sólo train); como ese ranking puede variar entre corridas/máquinas, se fija.
    vars_h = list(VARS_HIST_FIJAS)
    faltan = [v for v in vars_h if v not in roles["train"].columns]
    assert not faltan, f"Faltan columnas para las features de historia: {faltan}"
    print(f"Variables con historia ({len(vars_h)}): {vars_h}")

    panel = pd.concat([roles[r][[ID_COL, MES_COL] + vars_h] for r in ("historico", "train", "validacion", "aplicacion")],
                      ignore_index=True).sort_values([ID_COL, MES_COL]).reset_index(drop=True)
    ids = panel[ID_COL].to_numpy()
    per = panel[MES_COL].map(periodo).to_numpy()
    nuevo = {}
    with np.errstate(divide="ignore", invalid="ignore"):
        for v in vars_h:
            x = panel[v].to_numpy(np.float32)
            l1, l2 = _desplazar(x, ids, per, 1), _desplazar(x, ids, per, 2)
            st = np.stack([x, l1, l2])
            m3, s3 = st.mean(axis=0), st.std(axis=0)
            den = np.abs(m3)
            nuevo[f"{v}_m3"] = m3
            nuevo[f"{v}_s3"] = s3
            nuevo[f"{v}_mn3"] = st.min(axis=0)
            nuevo[f"{v}_mx3"] = st.max(axis=0)
            nuevo[f"{v}_cv3"] = np.where(den > 1e-9, s3 / den, np.nan).astype(np.float32)
            nuevo[f"{v}_xvsm3"] = np.where(den > 1e-9, (x - m3) / den, np.nan).astype(np.float32)
            nuevo[f"{v}_racha3"] = np.where(np.isnan(x) | np.isnan(l1) | np.isnan(l2), np.nan,
                                            (x < l1).astype(np.float32) + (l1 < l2)).astype(np.float32)
# [Anotación · líneas 1361–1373] Arma un DataFrame con las columnas nuevas, verifica que no haya pares
#   cliente-mes duplicados y las une a cada rol por cliente y mes, con un assert de que no cambie la cantidad de
#   filas.
    nuevo_df = pd.DataFrame(nuevo)
    nuevo_df[ID_COL], nuevo_df[MES_COL] = ids, panel[MES_COL].to_numpy()
    assert not nuevo_df.duplicated([ID_COL, MES_COL]).any()
    del panel, nuevo
    candidatas_hist = [c for c in nuevo_df.columns if c not in (ID_COL, MES_COL)]

    for r in ("historico", "train", "validacion", "aplicacion"):
        m = roles[r][[ID_COL, MES_COL]].merge(nuevo_df, on=[ID_COL, MES_COL], how="left")
        assert len(m) == len(roles[r])
        for c in candidatas_hist:
            roles[r][c] = m[c].to_numpy(np.float32)
        del m
    del nuevo_df

# [Anotación · líneas 1375–1392] Calcula el PSI de cada variable de historia entre las filas de train con
#   valor y 202108 (sólo si hay más de 1.000 filas con valor), conserva en NUEVAS_HIST las de PSI ≤ 0,25 y
#   elimina las demás de todos los roles; imprime cuántas quedan y el porcentaje de filas con alguna variable de
#   historia por rol.
    # PSI de cada feature nueva: filas de train que sí tienen valor vs. aplicación (202108)
    tr, ap = roles["train"], roles["aplicacion"]
    psi_h = {}
    for c in candidatas_hist:
        a = tr[c].dropna()
        psi_h[c] = psi(a, ap[c].dropna()) if len(a) > 1000 else np.nan
    psi_h = pd.Series(psi_h)
    NUEVAS_HIST = [c for c in candidatas_hist if psi_h[c] <= PSI_UMBRAL_SUSTANCIAL]
    descartadas = [c for c in candidatas_hist if c not in NUEVAS_HIST]
    for r in ("historico", "train", "validacion", "aplicacion"):
        roles[r].drop(columns=descartadas, inplace=True)
    print(f"Features de historia creadas: {len(candidatas_hist)} | descartadas por PSI > {PSI_UMBRAL_SUSTANCIAL} "
          f"o sin datos: {len(descartadas)} | quedan {len(NUEVAS_HIST)}")
    cobertura = {r: float(roles[r][NUEVAS_HIST].notna().any(axis=1).mean()) if NUEVAS_HIST else 0.0
                 for r in ("train", "validacion", "aplicacion")}
    print("Filas con al menos una feature de historia: " + ", ".join(f"{r} {100 * v:.0f}%" for r, v in cobertura.items()))
    if descartadas:
        print("Descartadas (primeras 15):", descartadas[:15])

# [Anotación · líneas 1394–1417] Fija DECAY_ELEGIDO = 0,8 y la variante 'hist_d0.8': a las columnas
#   seleccionadas en la etapa 5 les quita los 4 límites de tarjeta en nominal y mcomisiones_mantenimiento (con
#   sus lags, deltas y versión _real) y les suma las variables de historia. Con MODO_PRUEBA = False, un assert
#   exige que queden 504 columnas.
#%% celda 37 [texto]
## Etapa 6a — Columnas y decay (FIJADOS)

En la corrida original esta etapa comparó `v7_d0.8`, `hist_d0.8` y `hist_d0.8_catedra` (10 semillas c/u, sobre 202106) y eligió **`hist_d0.8`**: columnas de la ganadora de la v7 (sin límites nominales y sin `mcomisiones_mantenimiento`) + features de historia, con pesos por mes `0,8 ** meses_de_antigüedad`.
Acá se aplica esa decisión directamente (la evaluación está en la corrida original, `02_optimizacion_bayesiana/`).

#%% celda 38 [código]
DECAY_ELEGIDO = 0.8
VARIANTE_ELEGIDA = "hist_d0.8"


def _sin(cols, nombres):
    """Saca las columnas cuya variable base (sin lag/delta ni sufijo _real) está en `nombres`."""
    malos = set(nombres) | {n + "_real" for n in nombres}
    return [c for c in cols if _base_de(c) not in malos]


base_cols = list(columnas_modelo)
base_v7 = _sin([c for c in base_cols if _base_de(c) not in NO_DEFLACTAR], ["mcomisiones_mantenimiento"])
columnas_modelo = base_v7 + NUEVAS_HIST
print(f"Variante fijada: {VARIANTE_ELEGIDA} -> {len(columnas_modelo)} columnas, decay {DECAY_ELEGIDO}")
if not MODO_PRUEBA:
    assert len(columnas_modelo) == 504, (f"Se esperaban 504 columnas (corrida original) y hay {len(columnas_modelo)}: "
                                         "revisá que el dataset y las versiones de librerías sean las del README.")

# [Anotación · líneas 1419–1427] Celda con sólo comentarios que indica que no se corre Optuna, y celda que
#   fija el modelo: GANADOR = 'lgbm_binario', ALGORITMO = 'lgbm', TARGET = 'binario'.
#%% celda 39 [código]
# ENTREGA: no se corre Optuna. Los hiperparámetros salen del estudio guardado (ver README y la
# celda de configuraciones de más abajo). Se mantiene el nombre del experimento para la salida.

#%% celda 40 [código]
GANADOR = "lgbm_binario"
ALGORITMO = "lgbm"
TARGET = "binario"
print(f"Modelo: {GANADOR} ({ALGORITMO}, target {TARGET}, BAJA+1 y BAJA+2 = 1)")

# [Anotación · líneas 1429–1436] Dos semillas por configuración (una en MODO_PRUEBA): SEMILLAS_ENSAMBLE toma
#   las 2 primeras de SEMILLAS_SEMILLERO.
#%% celda 41 [texto]
### Ensamble de configuraciones (hiperparámetros fijos)

Se entrena cada una de las 6 configuraciones con 2 semillas y se promedian las probabilidades por cliente (cada configuración pesa igual).

#%% celda 42 [código]
N_SEMILLAS_POR_CONFIG = 1 if MODO_PRUEBA else 2
SEMILLAS_ENSAMBLE = SEMILLAS_SEMILLERO[:N_SEMILLAS_POR_CONFIG]

# [Anotación · líneas 1438–1526] CONFIGS: lista escrita en el código con las 6 configuraciones de LightGBM
#   (trials 54, 32, 23, 26, 43 y 31 del estudio lgbm_binario), cada una con su valor de Optuna y 7
#   hiperparámetros: learning_rate entre 0,0133 y 0,0192, num_leaves entre 26 y 78, min_data_in_leaf entre 766 y
#   3.052, feature_fraction entre 0,10 y 0,16, bagging_fraction entre 0,79 y 0,99, lambda_l2 entre 0,38 y 1,49 y
#   entre 484 y 631 rondas. Imprime 6 × 2 = 12 modelos.
# Las 6 mejores configuraciones del estudio de Optuna `optuna_lgbm_binario_v9.db` (60 trials completos,
# ordenados por ganancia suavizada en 202106). Son las mismas de `02_optimizacion_bayesiana/configs_finales.json`.
CONFIGS = [
    {
        "origen": "lgbm_binario",
        "trial": 54,
        "valor_optuna": 486488852.8678304,
        "params": {
            "learning_rate": 0.015612703381810599,
            "num_leaves": 27,
            "min_data_in_leaf": 766,
            "feature_fraction": 0.15444767384449581,
            "bagging_fraction": 0.9947572829047991,
            "lambda_l2": 0.37873831248437256,
            "num_boost_round": 484
        }
    },
    {
        "origen": "lgbm_binario",
        "trial": 32,
        "valor_optuna": 480285099.75062346,
        "params": {
            "learning_rate": 0.014531061647074092,
            "num_leaves": 43,
            "min_data_in_leaf": 1736,
            "feature_fraction": 0.15713432617476172,
            "bagging_fraction": 0.9692633473387323,
            "lambda_l2": 1.4943015630266268,
            "num_boost_round": 631
        }
    },
    {
        "origen": "lgbm_binario",
        "trial": 23,
        "valor_optuna": 478287406.4837905,
        "params": {
            "learning_rate": 0.017237078740101018,
            "num_leaves": 26,
            "min_data_in_leaf": 945,
            "feature_fraction": 0.10311474177385625,
            "bagging_fraction": 0.890631830104153,
            "lambda_l2": 0.492418620530642,
            "num_boost_round": 516
        }
    },
    {
        "origen": "lgbm_binario",
        "trial": 26,
        "valor_optuna": 478216153.3665835,
        "params": {
            "learning_rate": 0.015494668647079659,
            "num_leaves": 78,
            "min_data_in_leaf": 3052,
            "feature_fraction": 0.10833089379318772,
            "bagging_fraction": 0.7895872741175383,
            "lambda_l2": 0.8492377345278003,
            "num_boost_round": 571
        }
    },
    {
        "origen": "lgbm_binario",
        "trial": 43,
        "valor_optuna": 476870367.83042395,
        "params": {
            "learning_rate": 0.01922004952162682,
            "num_leaves": 44,
            "min_data_in_leaf": 1418,
            "feature_fraction": 0.10236806870585548,
            "bagging_fraction": 0.9652474036368197,
            "lambda_l2": 0.8281582583221055,
            "num_boost_round": 501
        }
    },
    {
        "origen": "lgbm_binario",
        "trial": 31,
        "valor_optuna": 476508135.91022444,
        "params": {
            "learning_rate": 0.013314097648216049,
            "num_leaves": 28,
            "min_data_in_leaf": 1399,
            "feature_fraction": 0.1343272633492515,
            "bagging_fraction": 0.8795820052170668,
            "lambda_l2": 0.7865118082223679,
            "num_boost_round": 624
        }
    }
]
print(f"{len(CONFIGS)} configuraciones x {len(SEMILLAS_ENSAMBLE)} semillas = {len(CONFIGS) * len(SEMILLAS_ENSAMBLE)} modelos")


# [Anotación · líneas 1529–1542] correr_ensamble(): para cada configuración llama a correr_semillero() con las
#   semillas del ensamble y guarda el promedio de scores entre semillas; devuelve una matriz (configuraciones ×
#   filas) por cada conjunto a predecir y la importancia promediada entre configuraciones.
def correr_ensamble(configs: list, X_fit, y_fit, X_preds: list, nombres: list, semillas: list, w_fit=None):
    """Una tanda de semillas por configuración. Devuelve, por cada X_pred, un array
    (n_configs x n_filas) con el score medio de cada configuración, y las importancias promedio."""
    por_config = [[] for _ in X_preds]
    imps = []
    for k, cfg in enumerate(configs, 1):
        print(f"Configuración {k}/{len(configs)} ({cfg['origen']}, trial {cfg['trial']})")
        sc, imp = correr_semillero("lgbm", "binario", cfg["params"], X_fit, y_fit, X_preds, nombres, semillas, w_fit=w_fit)
        for j in range(len(X_preds)):
            por_config[j].append(sc[j].mean(axis=0))
        imps.append(imp.set_index("variable")["importancia_media"])
    imp_medias = pd.concat(imps, axis=1).mean(axis=1).sort_values(ascending=False)
    importancias_ens = imp_medias.rename("importancia_media").rename_axis("variable").reset_index()
    return [np.array(pc) for pc in por_config], importancias_ens

# [Anotación · líneas 1544–1560] Etapa 7: arma las matrices de train (202103–202105) y de validación (202106),
#   entrena el ensamble con pesos por mes y obtiene score_valid como promedio entre las 6 configuraciones.
#%% celda 43 [texto]
## Etapa 7 — Ensamble en validación (entrenado en train, evaluado en 202106)

Cada configuración de `CONFIGS` se entrena con sus semillas, predice 202106 y se descarta. Se muestra la ganancia de cada configuración sola y la del ensamble.

#%% celda 44 [código]
prep_tr, nombres_features = preparar_preprocesador(ALGORITMO, roles["train"], columnas_modelo)
X_tr = transformar(prep_tr, roles["train"], columnas_modelo)
X_va = transformar(prep_tr, roles["validacion"], columnas_modelo)
y_tr = construir_y(roles["train"][TARGET_COL], TARGET)
y_va = roles["validacion"][TARGET_COL].to_numpy()

t0 = time.time()
(scores_val,), importancias = correr_ensamble(CONFIGS, X_tr, y_tr, [X_va], nombres_features, SEMILLAS_ENSAMBLE,
                                              w_fit=pesos_df(roles["train"]))
print(f"Ensamble de validación: {len(scores_val)} configuraciones en {(time.time() - t0) / 60:.1f} min")
score_valid = scores_val.mean(axis=0)

# [Anotación · líneas 1562–1579] Arma una tabla con la ganancia máxima suavizada en 202106 de cada
#   configuración y su diferencia con el valor de Optuna expresada en cantidad de BAJA+2; grafica la ganancia
#   del ensamble al ir sumando configuraciones e imprime la diferencia entre el ensamble completo y la
#   configuración de mayor ganancia.
tabla_cfg = pd.DataFrame([{"config": k + 1, "origen": c["origen"], "trial": c["trial"],
                           "valor_optuna": c["valor_optuna"],
                           "ganancia_202106": ganancia_max_suavizada(scores_val[k], y_va)}
                          for k, c in enumerate(CONFIGS)])
tabla_cfg["optimismo_optuna_en_BAJA+2"] = (tabla_cfg["valor_optuna"] - tabla_cfg["ganancia_202106"]) / ganancia_acierto
print(tabla_cfg.round({"valor_optuna": 0, "ganancia_202106": 0, "optimismo_optuna_en_BAJA+2": 1}).to_string(index=False))

curva_semillas = [ganancia_max_suavizada(scores_val[:k].mean(axis=0), y_va) for k in range(1, len(scores_val) + 1)]
plt.figure(figsize=(8, 4))
plt.plot(range(1, len(curva_semillas) + 1), curva_semillas, marker="o")
plt.xlabel("Configuraciones en el ensamble")
plt.ylabel("Ganancia suavizada 202106")
plt.title("¿Sigue mejorando al sumar configuraciones?")
plt.grid(alpha=0.3)
plt.show()
mejor_sola = tabla_cfg["ganancia_202106"].max()
print(f"Mejor configuración sola: {mejor_sola:,.0f} | ensamble de {len(scores_val)}: {curva_semillas[-1]:,.0f} "
      f"| diferencia: {(curva_semillas[-1] - mejor_sola) / ganancia_acierto:+.1f} BAJA+2")

# [Anotación · líneas 1581–1589] Imprime y grafica las 25 variables de mayor importancia media del ensamble.
#%% celda 45 [código]
print(importancias.head(25).to_string())
top = importancias.head(25).iloc[::-1]
plt.figure(figsize=(10, 8))
plt.barh(top["variable"], top["importancia_media"])
plt.xlabel("Importancia media")
plt.title(f"25 variables más importantes — {GANADOR}")
plt.tight_layout()
plt.show()

# [Anotación · líneas 1591–1624] elegir_corte(): sobre 202106 calcula la curva de ganancia y su versión
#   suavizada, toma como cantidad de envíos la posición del máximo de la suavizada y define la meseta como el
#   rango de posiciones cuya ganancia suavizada está a menos de 2 aciertos (2 × 1.072.500) de ese máximo;
#   devuelve también el máximo de la curva sin suavizar y la probabilidad en el corte. Se ejecuta sobre
#   score_valid.
#%% celda 46 [texto]
## Etapa 8 — Cantidad de envíos óptima (sobre 202106)

Corte = máximo de la curva **suavizada**. La **meseta** es el rango de envíos a menos de 2 aciertos
del máximo: cualquier cantidad dentro de ese rango es razonable.

#%% celda 47 [código]
def elegir_corte(score, y_true, ventana: int = VENTANA_SUAVIZADO, tolerancia: float = 2 * ganancia_acierto):
    orden, acum = curva_ganancia(score, y_true)
    suav = suavizar(acum, ventana)
    i = int(suav.argmax())
    meseta = np.where(suav >= suav[i] - tolerancia)[0]
    resumen = {
        "n_envios_optimo": i + 1,
        "ganancia_suavizada": float(suav[i]),
        "ganancia_real_en_ese_corte": float(acum[i]),
        "probabilidad_corte": float(np.asarray(score)[orden][i]),
        "meseta_desde": int(meseta.min()) + 1,
        "meseta_hasta": int(meseta.max()) + 1,
        "argmax_crudo": int(acum.argmax()) + 1,
        "ganancia_max_cruda": float(acum.max()),
    }
    tabla = pd.DataFrame({
        "posicion": np.arange(1, len(acum) + 1),
        "probabilidad": np.asarray(score)[orden],
        "ganancia_acumulada": acum,
        "ganancia_suavizada": suav,
    })
    return resumen, tabla


resumen_corte, tabla_ganancia = elegir_corte(score_valid, y_va)
for k, v in resumen_corte.items():
    print(f"  {k:28s}: {v:,.5f}" if isinstance(v, float) and v < 1 else f"  {k:28s}: {v:,.0f}")

# [Anotación · líneas 1626–1648] Grafica la curva de ganancia acumulada y la suavizada en 202106 (completa y
#   con zoom alrededor de la meseta) e imprime una tabla con 40 posiciones equiespaciadas más la fila del
#   máximo.
#%% celda 48 [código]
n_opt = resumen_corte["n_envios_optimo"]
fig, axes = plt.subplots(1, 2, figsize=(16, 5))
for ax, (desde, hasta) in zip(axes, [(1, len(tabla_ganancia)),
                                     (max(1, resumen_corte["meseta_desde"] - 3000), resumen_corte["meseta_hasta"] + 3000)]):
    t = tabla_ganancia[tabla_ganancia["posicion"].between(desde, hasta)]
    ax.plot(t["posicion"], t["ganancia_acumulada"], lw=0.8, alpha=0.6, label="Ganancia acumulada")
    ax.plot(t["posicion"], t["ganancia_suavizada"], lw=2, label=f"Suavizada ({VENTANA_SUAVIZADO})")
    ax.axvspan(resumen_corte["meseta_desde"], resumen_corte["meseta_hasta"], color="green", alpha=0.12, label="Meseta")
    ax.axvline(n_opt, color="red", ls="--", label=f"Óptimo suavizado: {n_opt:,}")
    ax.set_xlabel("Cantidad de clientes contactados")
    ax.set_ylabel("Ganancia")
    ax.grid(alpha=0.25)
    ax.legend()
axes[0].set_title("Curva completa (202106)")
axes[1].set_title("Zoom alrededor de la meseta")
plt.tight_layout()
plt.show()

#%% celda 49 [código]
pos = np.unique(np.append(np.linspace(0, len(tabla_ganancia) - 1, 40).astype(int), n_opt - 1))
print(tabla_ganancia.iloc[pos].assign(optimo=lambda d: d["posicion"] == n_opt)
      .round({"probabilidad": 5, "ganancia_suavizada": 0}).to_string(index=False))

# [Anotación · líneas 1650–1678] Celda de texto: enumera las condiciones del esquema de validación (entrenar
#   con 202103–202105 y validar en 202106) y describe el backtest de la celda siguiente, que entrena con
#   202103–202104 y evalúa en 202105 (1 mes de distancia) y en 202106 (2 meses).
#%% celda 50 [texto]
## Etapa 8b — ¿Está bien entrenar con 202103–05 y validar con 202106?

**Lo que está bien:**
- Todos los targets usados están maduros: BAJA+2 de 202106 necesita saber si el cliente está en
  202108, y 202108 está en el dataset. 202107 no tiene target (necesitaría 202109) y por eso no entrena.
- No hay fuga de información: lags sólo miran hacia atrás, y medianas, clusters y cortes de outliers
  se ajustan sólo con train. El PSI mira las features de 202108 pero nunca su target.

**Lo que no replica producción:**
- **Gap:** en producción el último mes con target es 202106 y se predice 202108 (**2 meses** de
  distancia). En la validación actual el último mes de train es 202105 y se valida en 202106
  (**1 mes**). La validación es, entonces, un poco optimista: el modelo "ve" un pasado más cercano
  que el que va a tener en agosto. El código de cátedra (`exp_401`: train 202103 → test 202105)
  respeta el gap de 2.
- **Superposición de ventanas:** el target de 202105 (BAJA+1/BAJA+2) se define mirando 202106–202107,
  el mismo período que valida. No es fuga directa (no se ve el target de 202106), pero comparten shocks.
- **202106 es un mes raro:** tiene aguinaldo (`mpayroll` +45%, por eso la hoja de ruta lo saca).
- **Un solo mes de validación** (~1.100 BAJA+2): el ruido es grande.

**El backtest de abajo lo mide en vez de suponerlo.** Con los mismos hiperparámetros entrena con
202103–04 y evalúa en 202105 (gap 1) y en 202106 (gap 2, como producción). Como los meses tienen
distinta cantidad de BAJA+2, se compara el **% de la ganancia ideal** (ganancia / (BAJA+2 × $1.07M)).
- Si gap 1 y gap 2 dan parecido → el esquema actual está bien.
- Si gap 2 cae mucho → la ganancia de 202106 que ves arriba sobreestima la de agosto; conviene ser
  conservadora con la cantidad de envíos (lado izquierdo de la meseta) y considerar tunear con gap 2
  (`MESES_TRAIN = [202103, 202104]`, validación 202106), a costa de un mes menos de datos en Optuna.
- También se compara la **cantidad de envíos óptima** de cada esquema: si el gap 2 pide bastantes
  menos, es otra señal para cortar más cerca del borde izquierdo de la meseta.

# [Anotación · líneas 1680–1718] CORRER_BACKTEST = False: el backtest no se ejecuta. El código bajo esa
#   condición entrena el ensamble con los meses de train que están a 2 o más meses de la validación
#   (202103–202104) y evalúa en 202105 y 202106, informando para cada esquema la ganancia suavizada, el
#   porcentaje de la ganancia ideal y la cantidad de envíos del máximo.
#%% celda 51 [código]
CORRER_BACKTEST = False   # diagnóstico de la corrida original; no hace falta para la predicción final
N_SEMILLAS_BACKTEST = 1   # semillas por configuración (el backtest entrena sobre menos meses)


def evaluar_esquema(nombre, score, y_true):
    r, _ = elegir_corte(score, y_true)
    n_b2 = int((np.asarray(y_true) == "BAJA+2").sum())
    return {"esquema": nombre, "BAJA+2": n_b2, "ganancia_suavizada": r["ganancia_suavizada"],
            "%_ganancia_ideal": 100 * r["ganancia_suavizada"] / (n_b2 * ganancia_acierto),
            "n_envios_optimo": r["n_envios_optimo"],
            "n_envios_%_del_mes": 100 * r["n_envios_optimo"] / len(y_true)}


meses_bt = [m for m in MESES_TRAIN if periodo(m) <= periodo(MES_VALID) - 2]
if CORRER_BACKTEST and not meses_bt:
    print("Backtest salteado: no hay meses de train con 2 meses de distancia a la validación.")
elif CORRER_BACKTEST:
    mes_gap1 = max(MESES_TRAIN)
    tr = roles["train"]
    df_bt, df_g1 = tr[tr[MES_COL].isin(meses_bt)], tr[tr[MES_COL] == mes_gap1]
    print(f"Backtest: train {meses_bt} -> valida {mes_gap1} (gap 1) y {MES_VALID} (gap 2)")

    prep_bt, nombres_bt = preparar_preprocesador(ALGORITMO, df_bt, columnas_modelo)
    (sc_g1, sc_g2), _ = correr_ensamble(
        CONFIGS, transformar(prep_bt, df_bt, columnas_modelo), construir_y(df_bt[TARGET_COL], TARGET),
        [transformar(prep_bt, df_g1, columnas_modelo), transformar(prep_bt, roles["validacion"], columnas_modelo)],
        nombres_bt, SEMILLAS_ENSAMBLE[:N_SEMILLAS_BACKTEST], w_fit=pesos_df(df_bt))

    backtest = pd.DataFrame([
        evaluar_esquema(f"actual: {min(MESES_TRAIN)}–{mes_gap1} -> {MES_VALID} (gap 1)", score_valid, y_va),
        evaluar_esquema(f"{min(meses_bt)}–{max(meses_bt)} -> {mes_gap1} (gap 1)",
                        sc_g1.mean(axis=0), df_g1[TARGET_COL].to_numpy()),
        evaluar_esquema(f"{min(meses_bt)}–{max(meses_bt)} -> {MES_VALID} (gap 2, como producción)",
                        sc_g2.mean(axis=0), y_va),
    ])
    print(backtest.round(1).to_string(index=False))
    print(f"\n(Ensamble de {len(CONFIGS)} configuraciones; la fila 'actual' usa {len(SEMILLAS_ENSAMBLE)} semilla/s por "
          f"configuración y las del backtest {N_SEMILLAS_BACKTEST}.)")

# [Anotación · líneas 1720–1742] Etapa 9: N_ENVIOS_MANUAL = 11.500. Concatena train y validación
#   (202103–202106), verifica los meses con assert, arma las matrices y entrena de nuevo las 6 configuraciones ×
#   2 semillas con pesos por mes; score_aplic es el promedio de probabilidades entre configuraciones para cada
#   cliente de 202108.
#%% celda 52 [texto]
## Etapa 9 — Reentrenamiento final (202103–202106) y predicción de agosto

Mismas configuraciones y semillas, entrenando con **todos los meses con target** (`MESES_FINAL`). Se promedian las probabilidades de las configuraciones por `numero_de_cliente`.
El corte automático se traslada **por cantidad** (los `n_envios_optimo` de 202106, reescalados por la cantidad de clientes de agosto); la Etapa 10 exporta además otros cortes.

#%% celda 53 [código]
N_ENVIOS_MANUAL = 11_500   # corte elegido (ver README, sección "Elección del corte")

df_final = pd.concat([roles["train"], roles["validacion"]], ignore_index=True)
assert sorted(df_final[MES_COL].unique().tolist()) == sorted(MESES_FINAL)

prep_final, nombres_final = preparar_preprocesador(ALGORITMO, df_final, columnas_modelo)
X_final = transformar(prep_final, df_final, columnas_modelo)
y_final = construir_y(df_final[TARGET_COL], TARGET)
aplicacion = roles["aplicacion"]
X_ap = transformar(prep_final, aplicacion, columnas_modelo)

t0 = time.time()
(scores_ap,), _ = correr_ensamble(CONFIGS, X_final, y_final, [X_ap], nombres_final, SEMILLAS_ENSAMBLE,
                                  w_fit=pesos_df(df_final))
print(f"Ensamble final ({MESES_FINAL}): {len(scores_ap)} configuraciones en {(time.time() - t0) / 60:.1f} min")
score_aplic = scores_ap.mean(axis=0)

# [Anotación · líneas 1744–1751] Define la cantidad de envíos: usa N_ENVIOS_MANUAL (11.500); con None usa el
#   máximo de 202106 reescalado por la cantidad de clientes de 202108. Imprime el corte y la probabilidad del
#   último cliente incluido.
n_opt = resumen_corte["n_envios_optimo"]
n_envios = N_ENVIOS_MANUAL or int(round(n_opt * len(aplicacion) / len(roles["validacion"])))
orden_ap = np.argsort(-score_aplic, kind="mergesort")
print(f"Corte automático en agosto: {n_envios:,} de {len(aplicacion):,} clientes "
      f"({'manual' if N_ENVIOS_MANUAL else 'automático'}; meseta en 202106: "
      f"{resumen_corte['meseta_desde']:,}–{resumen_corte['meseta_hasta']:,})")
print(f"Probabilidad del último cliente contactado en agosto: {score_aplic[orden_ap][n_envios - 1]:.5f} "
      f"(en 202106 era {resumen_corte['probabilidad_corte']:.5f}; no tienen por qué coincidir)")

# [Anotación · líneas 1753–1773] _entorno() junta la versión de Python, el sistema, la cantidad de CPU lógicas
#   y las versiones de lightgbm, duckdb, pandas, numpy, scikit-learn, optuna y psutil. CORTES = [11.500].
#%% celda 54 [código]
import platform, importlib.metadata as _im


def _entorno():
    paquetes = ["lightgbm", "duckdb", "pandas", "numpy", "scikit-learn", "optuna", "psutil"]
    v = {p: (_im.version(p) if _safe(p) else None) for p in paquetes}
    return {"python": platform.python_version(), "sistema": platform.platform(), "cpu_logicas": os.cpu_count(), **v}


def _safe(p):
    try:
        _im.version(p)
        return True
    except Exception:
        return False


# Cortes a exportar (cantidad de clientes en agosto). La campaña espera entre 8.000 y 15.000.
# Se agrega siempre el corte automático (n_envios). Todos salen del MISMO ranking: sólo cambia el tamaño.
CORTES = [11_500]


# [Anotación · líneas 1776–1813] exportar_cortes(): crea la carpeta salida_final_<fecha>, ordena los clientes
#   de 202108 por score descendente y, para cada corte entre 8.000 y 15.000, escribe un CSV de una columna sin
#   encabezado con los primeros n numero_de_cliente; guarda resumen_cortes.csv (equivalente del corte en 202106
#   y su ganancia suavizada y sin suavizar) y meta.json (entorno, variante, decay, meses, cantidad de variables,
#   configuraciones y resumen del corte).
def exportar_cortes(score_aplic, cortes, n_auto, prefijo: str = "prediccion_baja_202108") -> pd.DataFrame:
    """Un CSV por corte (una sola columna, sin encabezado, IDs enteros, nombre único) en una carpeta nueva,
    más resumen_cortes.csv (ganancia validada en 202106 de cada corte) y meta.json."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    carpeta = os.path.join(SALIDAS_PATH, f"salida_final_{ts}")
    os.makedirs(carpeta, exist_ok=True)
    orden = np.argsort(-score_aplic, kind="mergesort")
    ids_ord = aplicacion[ID_COL].to_numpy()[orden]
    probs_ord = score_aplic[orden]
    escala = len(roles["validacion"]) / len(aplicacion)

    filas = []
    for n in sorted(set(cortes)):
        if not (8_000 <= n <= 15_000):
            print(f"OJO: corte {n:,} fuera de 8.000–15.000: se saltea.")
            continue
        ruta = os.path.join(carpeta, f"{prefijo}_{GANADOR}_final_corte{n}_{ts}.csv")
        pd.DataFrame({ID_COL: ids_ord[:n]}).astype("int64").to_csv(ruta, index=False, header=False)
        n_val = min(max(int(round(n * escala)), 1), len(tabla_ganancia))
        filas.append({"archivo": os.path.basename(ruta), "n_envios": n, "equivale_en_202106": n_val,
                      "ganancia_suavizada_202106": float(tabla_ganancia["ganancia_suavizada"].iloc[n_val - 1]),
                      "ganancia_real_202106": float(tabla_ganancia["ganancia_acumulada"].iloc[n_val - 1]),
                      "prob_ultimo_cliente": float(probs_ord[n - 1]),
                      "dentro_meseta": resumen_corte["meseta_desde"] <= n_val <= resumen_corte["meseta_hasta"],
                      "corte_automatico": n == n_auto})
    resumen = pd.DataFrame(filas)
    resumen.to_csv(os.path.join(carpeta, "resumen_cortes.csv"), index=False)

    meta = {"version": "entrega_final", "entorno": _entorno(), "modelo": GANADOR, "variante": globals().get("VARIANTE_ELEGIDA"),
            "decay": DECAY_ELEGIDO, "meses_final": MESES_FINAL, "variables_rotas": VARIABLES_ROTAS,
            "n_features": len(columnas_modelo), "semillas_por_config": len(SEMILLAS_ENSAMBLE),
            "configs": [{"origen": c["origen"], "trial": c["trial"], "valor_optuna": c["valor_optuna"],
                         "params": c["params"]} for c in CONFIGS],
            "resumen_corte_202106": resumen_corte, "no_deflactar": NO_DEFLACTAR}
    with open(os.path.join(carpeta, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=float)
    print(f"Guardados {len(resumen)} archivos en: {carpeta}")
    return resumen


# [Anotación · líneas 1816–1821] Si MODO_PRUEBA es False, ejecuta exportar_cortes() con el corte de 11.500 e
#   imprime el resumen.
if MODO_PRUEBA:
    print("MODO_PRUEBA: no se exportan los submits (los datos son una muestra). Poné MODO_PRUEBA = False.")
else:
    resumen_cortes = exportar_cortes(score_aplic, CORTES, n_envios)
    print(resumen_cortes.drop(columns="archivo").round({"ganancia_suavizada_202106": 0, "ganancia_real_202106": 0,
                                                       "prob_ultimo_cliente": 5}).to_string(index=False))
```


## Explicaciones del alumno (texto original)

### README.md

> # Competencia 1 — Predicción de churn bancario (BAJA+2, agosto 2021) — DMEyF 2026
>
> Autora: Micaela R. Rodriguez
>
> Este repositorio permite replicar **exactamente** el archivo enviado como entrega final:
>
> | | |
> |---|---|
> | Archivo final | `prediccion_final/prediccion_baja_202108_lgbm_binario_v11_corte11500_20261009_224353.csv` |
> | Contenido | 11.500 `numero_de_cliente` (una sola columna, sin encabezado, enteros) |
> | SHA-256 | `2d690cb36f34445efa9a4b81726037c2bcba30c88c164e6d249137ec37d81b0a` |
>
> ## 1. Estructura del repositorio
>
> ```
> ├── README.md
> ├── prediccion_final/
> │   └── prediccion_baja_202108_lgbm_binario_v11_corte11500_20261009_224353.csv   <- el submit final
> ├── 01_prediccion_final/
> │   └── churn_pipeline_final.ipynb          <- UN notebook: competencia_01.csv -> CSV final
> └── 02_optimizacion_bayesiana/              <- de dónde salen los hiperparámetros (ver sección 4)
>     ├── configs_finales.json                <- las 6 configuraciones usadas en el ensamble
>     ├── optuna_lgbm_binario_v9.db           <- estudio de Optuna completo (60 trials)
>     ├── churn_pipeline_v9_optuna.ipynb      <- corrida que generó los trials 0–36
>     ├── churn_pipeline_v11_corrida_original.ipynb   <- corrida que generó los trials 37–61 y el submit (con salidas)
>     ├── resumen_cortes_corrida_original.csv
>     └── origen_warm_start/                  <- estudios previos que sembraron el punto de partida de Optuna
> ```
>
> ## 2. Resumen de la solución
>
> - **Datos:** `competencia_01.csv` (202103–202108). Se predice BAJA+2 en 202108.
> - **Meses:** entrenamiento 202103–05 y validación 202106 (para decidir); entrenamiento final 202103–06; aplicación 202108. 202107 no tiene target y se usa sólo para lags e historia.
> - **Target:** binario (BAJA+1 y BAJA+2 = 1). La ganancia se mide sólo sobre BAJA+2 (+1.072.500 por acierto, −27.500 por error).
> - **Sin undersampling** en ninguna etapa (hay un `assert`).
> - **Calidad de datos:** `ccajas_depositos` en NA para 202105 (todos ceros). Montos deflactados por IPC (los límites de tarjeta se conservan también en nominal). Se excluyen `mpayroll`, `cpayroll_trx`, `mprestamos_personales`, `cprestamos_personales`, sus lags/deltas y sus derivadas (hoja de ruta).
> - **Drift:** se excluyen las variables con PSI > 0,25 (train vs. 202108), con sus lags/deltas. En la entrega, además, se sacan los límites de tarjeta nominales y `mcomisiones_mantenimiento`.
> - **Features:** lags y deltas de 15 variables, `delta1` de todas las numéricas, ratios/agrupaciones, cluster KMeans (k=5, ajustado sólo en train) como dummies y **175 features de historia** (media, desvío, mínimo, máximo, desvío relativo, apartamiento contra la media y racha de caídas sobre los últimos 3 meses) de 25 variables. Total: **504 columnas**.
> - **Pesos por mes:** cada fila pesa `0,8 ** (meses desde el último mes de entrenamiento)`.
> - **Modelo:** LightGBM binario. **Ensamble de 6 configuraciones × 2 semillas = 12 modelos**, entrenados con 202103–202106, y se **promedian las probabilidades por cliente**.
> - **Corte:** los 11.500 clientes con mayor probabilidad (ver sección 5).
>
> ## 3. Cómo replicar el archivo final
>
> 1. Poner `competencia_01.csv` en la carpeta del notebook o en una carpeta superior (hasta 3 niveles), o definir `CHURN_BASE_PATH` con la carpeta que lo contiene. El notebook crea ahí `duckdb_tmp/` (se borra solo) y `salida_final_<fecha>/`.
> 2. Instalar el entorno (sección 6).
> 3. Ejecutar `01_prediccion_final/churn_pipeline_final.ipynb` de principio a fin (*Run All*). No requiere nada más: las 6 configuraciones de hiperparámetros, las 25 variables con historia, el decay (0,8), el conjunto de columnas y el corte (11.500) están fijados en el notebook.
> 4. El archivo sale en `salida_final_<fecha>/prediccion_baja_202108_lgbm_binario_final_corte11500_<fecha>.csv`, junto con `meta.json` (versiones de librerías, cantidad de CPU, configuraciones) y `resumen_cortes.csv`. El nombre lleva la fecha de la corrida; el **contenido** debe coincidir con el archivo de `prediccion_final/`.
> 5. Verificación: el notebook comprueba que quedan 504 columnas; comparar `sha256sum` del CSV generado con el de la tabla de arriba, o comparar el conjunto de IDs.
>
> Tiempo: unos 40 minutos de entrenamiento (≈18 min el ensamble en validación y ≈21 min el entrenamiento final, medidos en la corrida original) más el ETL y las features. La corrida original usó una máquina Windows con ~34 GB de RAM; se recomiendan al menos 16 GB (DuckDB trabaja en disco con límite de memoria del 40% de la RAM).
>
> **Sobre la reproducibilidad exacta:** todas las semillas están fijadas, pero LightGBM usa `num_threads = os.cpu_count()` y la suma en punto flotante con distinta cantidad de hilos o distinta versión de la librería puede alterar los últimos decimales de las probabilidades. Si el archivo generado no coincide bit a bit, esperar diferencias sólo en los clientes cercanos al corte. Por eso `meta.json` registra el entorno de cada corrida. Por la misma razón las 25 variables con historia **están escritas en el notebook** (en la corrida original salieron de un ranking de importancia que cambió entre dos corridas).
>
> ## 4. Procedencia de los hiperparámetros (optimización bayesiana)
>
> Los hiperparámetros del ensamble **no se optimizan dentro del notebook final**: salen de un estudio de Optuna que se guardó y se incluye completo.
>
> - **Estudio:** `02_optimizacion_bayesiana/optuna_lgbm_binario_v9.db` (nombre de estudio `lgbm_binario`; 60 trials completos y 2 fallidos por interrupción manual).
> - **Objetivo de Optuna:** máximo de la curva de ganancia suavizada (media móvil de 401 envíos) en 202106, entrenando con 202103–05, **sin undersampling**, pesos por mes 0,8 y 3 semillas por trial. Sampler TPE (semilla 17).
> - **Espacio de búsqueda:** `learning_rate` 0,01–0,1 (log), `num_leaves` 8–1024 (log), `min_data_in_leaf` 50–5000 (log), `feature_fraction` 0,1–0,8, `bagging_fraction` 0,5–1, `lambda_l2` 0,001–100 (log), `num_boost_round` 100–2000 (log).
> - **Cómo se corrió:** el estudio se fue continuando en el tiempo (límite de 3–4 h por corrida): los trials 0–36 los generó `churn_pipeline_v9_optuna.ipynb` (8/10/2026) y los trials 37–61, `churn_pipeline_v11_corrida_original.ipynb` (9/10/2026). Los trials 0–36 se evaluaron con 502 columnas y los siguientes con 504 (las dos corridas difirieron en una de las 25 variables con historia).
> - **Punto de partida:** los trials 0–4 son la reevaluación de los 5 mejores parámetros de estudios previos (`origen_warm_start/`: `optuna_lgbm_binario_v5.db`, con trials de las corridas v5 y v7, y `optuna_lgbm_binario_v3.db`). Ninguna de las 6 configuraciones finales es un trial de partida; sí influyeron en el muestreo de TPE. Se incluyen los notebooks y bases de esos estudios por completitud.
>
> **Las 6 configuraciones del ensamble** (las mejores 6 del estudio por valor de Optuna; también en `configs_finales.json` y en la celda de configuraciones del notebook final):
>
> | Trial | Corrida | Valor Optuna (202106) | lr | hojas | min_data_in_leaf | feature_fraction | bagging_fraction | lambda_l2 | rondas |
> |---|---|---|---|---|---|---|---|---|---|
> | 54 | v11 | 486,49 M | 0,01561 | 27 | 766 | 0,15445 | 0,99476 | 0,37874 | 484 |
> | 32 | v9 | 480,29 M | 0,01453 | 43 | 1736 | 0,15713 | 0,96926 | 1,49430 | 631 |
> | 23 | v9 | 478,29 M | 0,01724 | 26 | 945 | 0,10311 | 0,89063 | 0,49242 | 516 |
> | 26 | v9 | 478,22 M | 0,01549 | 78 | 3052 | 0,10833 | 0,78959 | 0,84924 | 571 |
> | 43 | v11 | 476,87 M | 0,01922 | 44 | 1418 | 0,10237 | 0,96525 | 0,82816 | 501 |
> | 31 | v9 | 476,51 M | 0,01331 | 28 | 1399 | 0,13433 | 0,87958 | 0,78651 | 624 |
>
> (Valores completos en `configs_finales.json`.)
>
> **Qué hacer según el caso:**
> - *Replicar la predicción final:* nada más que la sección 3; los hiperparámetros ya están en el notebook.
> - *Verificar que las configuraciones salen del estudio:* abrir `optuna_lgbm_binario_v9.db` (`optuna.load_study(study_name="lgbm_binario", storage="sqlite:///optuna_lgbm_binario_v9.db")`) y tomar los 6 mejores trials completos; deben coincidir con la tabla.
> - *Volver a correr la optimización:* correr `churn_pipeline_v9_optuna.ipynb` (copiando `origen_warm_start/*.db` a una carpeta `modelos/` junto al dataset) y luego `churn_pipeline_v11_corrida_original.ipynb`, que retoma el mismo estudio. No se espera obtener los mismos trials: la búsqueda estuvo limitada por tiempo y se interrumpió y retomó varias veces.
>
> Observación: el valor de Optuna de los mejores trials es optimista respecto del real (se elige el máximo sobre un solo mes de validación): al reentrenar las 6 configuraciones con 2 semillas, la ganancia en 202106 de cada una difiere entre −9 y +12 BAJA+2 del valor de Optuna. Por eso se usa el ensamble y no el mejor trial solo.
>
> ## 5. Elección del corte (11.500 envíos)
>
> Los cortes de 10.000 a 14.500 (en pasos de 500) salen del **mismo ranking** (sólo cambia cuántos clientes se contactan). Se enviaron varios al pseudo-Kaggle (leaderboard público) y **el mejor resultado fue el de 11.500**, que es el que se entrega.
>
> Como referencia, la ganancia suavizada del ensamble en 202106 (cortes de agosto reescalados por la cantidad de clientes del mes):
>
> | Envíos en agosto | Equivale en 202106 | Ganancia suavizada |
> |---|---|---|
> | 10.000 | 9.968 | 458,9 M |
> | 11.000 | 10.964 | 468,3 M |
> | **11.500 (elegido)** | 11.463 | **472,9 M** |
> | 12.000 | 11.961 | 475,0 M |
> | 12.500 | 12.460 | 480,6 M |
> | 12.720 (óptimo en validación) | 12.679 | 482,5 M |
> | 13.000 | 12.958 | 480,1 M |
> | 14.000 | 13.955 | 472,6 M |
>
> La validación en 202106 favorece un corte mayor (óptimo en 12.720; 11.500 queda unos 9,6 M, unos 9 BAJA+2, por debajo), mientras que el pseudo-Kaggle de agosto favoreció 11.500. El leaderboard público es una muestra ruidosa (una diferencia de ~4% equivale a unos 17 BAJA+2), así que la elección se apoya en la evidencia disponible sobre agosto, que es el mes que se evalúa.
>
> ## 6. Entorno
>
> - Python 3.13 (Anaconda), Windows 11. Paquetes: `duckdb`, `pandas`, `numpy`, `scikit-learn`, `lightgbm`, `optuna`, `matplotlib`, `psutil` (opcional; fija el límite de memoria de DuckDB).
> - Versiones usadas en la corrida original: `<completar con las del entorno de la entrega: pip list | findstr "lightgbm duckdb pandas numpy scikit-learn optuna">`.
> - El notebook final guarda las versiones y la cantidad de CPU en `meta.json`.
>
> ## 7. Qué se probó y se descartó (resumen)
>
> Todas las comparaciones se hicieron sobre 202106 con un semillero de 10 modelos; una diferencia de 1–3 BAJA+2 se considera ruido.
>
> - **Random Forest** (ternario y binario): unos 40 BAJA+2 por debajo de LightGBM y 30–100 veces más lento.
> - **Undersampling de CONTINUA:** descartado por decisión (pocos meses; recomendación de la cátedra).
> - **Recorte de variables con "canaritos"** (variables aleatorias de control): −24 a −36 BAJA+2.
> - **Sacar variables con errores de datos y variables de fecha** (`cliente_vip`, conteos de préstamos hipotecarios/prendarios, `*_descuentos`, `ccajas_depositos`, `*_Fvencimiento`, `*_Finiciomora`, `*_fultimo_cierre`, `*_fechaalta`): −2 a −8 BAJA+2; las fechas aportan señal, así que se conservan.
> - **Receta de hiperparámetros de la cátedra** (`lr 0,005`, `max_bin 31`, `min_data_in_leaf 0`, `feature_fraction 0,5`, `feature_fraction_bynode 0,2`) con una configuración inicial: −21 BAJA+2 y 4 veces más lenta; el estudio de Optuna correspondiente no llegó a completar trials, por lo que no es concluyente.
> - **Features de historia:** aportan poco por sí solas (+0,65 BAJA+2 sobre las mismas columnas sin historia, dentro del ruido); se mantienen en la entrega porque así se entrenó el submit.
> - **Lo que sí mejoró:** pesos por mes (decay 0,8: +3,4 BAJA+2), ensamble de configuraciones, límites de tarjeta sólo en nominal (evita un drift artificial) y sacar `mcomisiones_mantenimiento`.

