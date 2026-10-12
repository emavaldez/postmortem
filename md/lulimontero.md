# Lucía Montero — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: lulimontero
- Repositorio: https://github.com/lulimontero/maestria-data-mining-2026
- Link posteado: https://github.com/lulimontero/maestria-data-mining-2026/tree/main/DMEyF/Primera-Competencia
- Commit: 86545d771713fa4601d16665cb2cb3b8e5406a90
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/lulimontero/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/lulimontero.json

## Resumen

La entrega está en DMEyF/Primera-Competencia: un README, cuatro notebooks de R y dos logs de optimización bayesiana. Según el README, el archivo entregado es Intentoj_blend_12000.csv, un blend de dos experimentos de LightGBM. Los notebooks j4955 y j4957 comparten el mismo flujo: calculan clase_ternaria, pasan a NA las variables que valen cero en todo un mes, crean flags de valor cero, totales y cocientes de tarjetas, reemplazan las variables monetarias por su rank con cero fijo dentro de cada mes y agregan lags y deltas de orden 1 y 2, tendencia y promedio en ventana de 3 meses y variables de transición. Entrenan con clase binaria (BAJA+1 y BAJA+2 positivos, peso 0,25 para BAJA+1) sobre 202103–202106, después de eliminar los CONTINUA a los que un modelo auxiliar asigna probabilidad de 0,5 o más, y predicen 202108 promediando semillas (3 en j4955, 12 en j4957). j4955 usa hiperparámetros escritos en el código y feature_fraction_bynode 1,0; j4957 corre una optimización bayesiana de 40 evaluaciones con feature_fraction_bynode 0,2. El notebook del blend convierte las dos predicciones promedio en puestos, los promedia y escribe archivos con cortes de 10.500 a 14.500 clientes.

**Qué entrega.** Según el README, el archivo entregado es Intentoj_blend_12000.csv: una columna sin encabezado con los 12.000 numero_de_cliente de 202108 de mayor puntaje en el blend de los experimentos j4955 y j4957. El archivo no está en el repositorio; lo genera blend_j4955_j4957.ipynb en ~/buckets/b1/exp/BLEND-4955-4957/.

**Cómo se ejecuta.** El README (sección 7) indica que todos los notebooks usan kernel R y da el orden: 1) opcional, notebooks/j4953_competencia.ipynb (la bayesiana de la que salen los hiperparámetros de j4955); 2) notebooks/j4955_competencia.ipynb, que genera ~/buckets/b1/exp/HT4955-01/prediccion_promedio.txt; 3) notebooks/j4957_competencia.ipynb, que incluye su bayesiana (unas 5,5 horas según el README) y genera ~/buckets/b1/exp/HT4957-01/prediccion_promedio.txt; 4) notebooks/blend_j4955_j4957.ipynb, que lee esos dos archivos y escribe los CSV de envío en ~/buckets/b1/exp/BLEND-4955-4957/.

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase01): positivo = BAJA+1 o BAJA+2, negativo = CONTINUA. Al entrenar, las filas BAJA+1 llevan peso 0,25 y el resto peso 1,0.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** El parámetro de undersampling vale 1 (se toman todos los CONTINUA), de modo que no hay submuestreo al azar. Sí se eliminan del entrenamiento los CONTINUA a los que un modelo auxiliar (2.180 iteraciones, 30 hojas) asigna probabilidad de 0,5 o más: en la bayesiana ese modelo se entrena con el 30%, se aplica a todo el conjunto de entrenamiento y se usa para descartar CONTINUA del 70%; en el modelo final se hace por cross-fitting en dos mitades de 202103–202106. Según el README, se eliminan 161 y 304 CONTINUA respectivamente.
- **Calidad de datos:** Las columnas numéricas con todos sus valores en cero en un mes se pasan a NA en ese mes (según el README, es el caso de ccajas_depositos en 202105); ccajas_depositos de 202105 se vuelve a pasar a NA sobre el dataset releído. Los cocientes con resultado infinito o NaN se pasan a NA.
- **Drifting:** Rank con cero fijo dentro de cada foto_mes para las columnas que empiezan con m, Master_m o Visa_m (82 variables según el README): ceros en 1e-7, positivos en (0,1], negativos en [-1,0). El rank reemplaza los valores originales y se aplica antes de calcular lags, deltas y tendencias.
- **Variables dentro del mes:** Flags <variable>_zero (1/0/NA) para las variables que valen cero alguna vez (140 según el README); totales Master + Visa (mv_mlimitecompra, mv_msaldototal, mv_mconsumototal, mv_mpagado, mv_mpagominimo) y cocientes sobre el límite total (mvr_utilizacion, mvr_consumo_limite, mvr_pago_limite, mvr_pagominimo_lim); ctrx_quarter_normalizado (ctrx_quarter por 5, 2 o 1,2 según antigüedad 1, 2 o 3); mpayroll_sobre_edad; cpayroll_tot y cconsumos_tot.
- **Variables históricas:** lag1, lag2, delta1 y delta2 de todas las variables (salvo las _zero); pendiente de cuadrados mínimos (_tend3) y promedio (_avg3) en ventana de 3 meses; transiciones mes anterior → actual de Master_status, Visa_status y delinquency (_trans, _empeora, _entra_mora); flags _prende y _apaga de siete variables de conteo, de active_quarter, del payroll total y de los consumos totales; n_canales_apagados (suma de cuatro flags _apaga).
- **Selección de variables:** No se observa en el código una selección de variables: el modelo usa todas las columnas del dataset menos clase_ternaria y las auxiliares (clase01, fold, azar, training, training30, prob30, aporta, fold30); numero_de_cliente y foto_mes quedan entre las variables. La importancia de variables se calcula y se graba en impo.txt sin usarse para filtrar. La exclusión de cprestamos_personales y mprestamos_personales está comentada.
- **Optimización de hiperparámetros:** j4957: optimización bayesiana con bbotk y mlr3mbo (bayesopt_ego, surrogate kriging regr.km, expected improvement, 40 evaluaciones) sobre num_iterations [64, 4096], num_leaves [16, 2048], min_sum_hessian_in_leaf [1e-06, 0,1] y feature_fraction [0,1, 0,9]; entrena en el fold 1 de 202103–202104 sin registros dudosos y mide AUC en 202106. j4955 no corre la bayesiana: sus cuatro valores están escritos en el código y, según el README, son la fila de mayor métrica de la bayesiana de j4953 (100 evaluaciones en el log incluido).
- **Hiperparámetros finales:** Comunes: learning_rate 0,005, min_data_in_leaf 0, max_bin 31, max_depth -1, lambda_l1 y lambda_l2 0, sin bagging, objective binary. j4955: num_iterations 3606, num_leaves 1443, min_sum_hessian_in_leaf 0,0875, feature_fraction 0,1202, feature_fraction_bynode 1,0. j4957: la fila de mayor métrica de su BO_log.txt (en el log incluido: num_iterations 2652, num_leaves 1642, min_sum_hessian_in_leaf 0,0896, feature_fraction 0,1100), feature_fraction_bynode 0,2.
- **Semillas:** Semilla primigenia 600013 para particiones, bayesiana y modelo auxiliar. Modelo final de j4955: 600013, 620003 y 640007. Modelo final de j4957: 600013, 157331, 209897, 318677, 431201, 547361, 712889, 823981, 934511, 660007, 680003 y 620003. Backtest: 600013, 620003, 640007, 660007 y 680003.
- **Cantidad de semillas:** 15
- **Ensamble:** Dentro de cada experimento se promedian las probabilidades de sus semillas (3 en j4955, 12 en j4957; 15 modelos en total). El blend combina los dos experimentos con peso 50/50: convierte cada probabilidad promedio en un puesto (frank), promedia los dos puestos de cada cliente y ordena por ese promedio.
- **Corte:** Cantidad fija de clientes según el orden del blend. El notebook del blend escribe nueve archivos con cortes de 10.500 a 14.500 cada 500; según el README se entregó el de 12.000, elegido a partir de los resultados del leaderboard público y del backtest de 202106.
- **Validación:** La bayesiana entrena en 202103–202104 y mide AUC en 202106. Backtest en j4955 y j4957: entrenamiento en 202103 y 202104, prueba en 202106 con 5 semillas, ganancia de la competencia (1.072.500 por BAJA+2, -27.500 por el resto) para cortes de 4.000 a 19.000 cada 200, en total y sobre una partición simulada 30/70. Según el README, en el backtest la mayor ganancia del ensamble es 408,1 millones con 12.200 envíos en j4955 y 426,8 millones con 14.200 en j4957, y en el leaderboard público el blend con 12.000 envíos obtuvo 107,77.
- **Salidas:** En ~/buckets/b1/datasets: competencia_01_lag1y2_delta1y2_rank.csv.gz. En ~/buckets/b1/exp/<experimento>/: BO_log.txt (cuando se corre la bayesiana), modelo.txt, modelo_<semilla>.txt, prediccion.txt, prediccion_promedio.txt, resultados_semillas.txt, impo.txt, PARAM.yml, PARAM_semillas.yml, hs_paramset.rds, backtest_202106.txt e Intentoj4955_01..07.csv o Intentoj4957_01..11.csv. En ~/buckets/b1/exp/BLEND-4955-4957/: Intentoj_blend_<corte>.csv para nueve cortes. El repositorio incluye sólo los BO_log de HT4953-01 y HT4957-01.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: El README indica que todos los notebooks usan kernel R y que datos y salidas están bajo ~/buckets/b1 (datasets y exp); señala que la bayesiana de j4957 tardó unas 5,5 horas. No se declaran máquina, sistema operativo ni versiones de R o de los paquetes; los notebooks instalan los paquetes sin fijar versión.

## Pasos del camino de la entrega

1. **Lectura del dataset y cálculo de clase_ternaria.** Los dos notebooks de experimento leen competencia_01_crudo.csv desde ~/buckets/b1/datasets y calculan clase_ternaria (CONTINUA, BAJA+1, BAJA+2) a partir de la presencia de cada cliente en los dos meses siguientes; el último mes queda sin clase. (`DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 98–108; `DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 143–181; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 143–181)
2. **Variables en cero durante todo un mes pasadas a NA.** Para cada mes se detectan las columnas numéricas con todos sus valores en cero y esos ceros se reemplazan por NA en ese mes. Más adelante, sobre el dataset releído, ccajas_depositos de 202105 se vuelve a pasar a NA. (`DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 201–244; `DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 1437–1440; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 201–244)
3. **Variables dentro del mes: flags de cero, totales y cocientes de tarjeta.** Se crea un flag <variable>_zero (1, 0 o NA) para cada variable que vale cero alguna vez, se suman Master y Visa en cinco totales mv_ y se calculan cuatro cocientes mvr_ sobre el límite de compra total, con los montos sin rankear. (`DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 249–276; `DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 281–314; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 249–314)
4. **Rank con cero fijo por mes de las variables monetarias.** Las columnas cuyo nombre empieza con m, Master_m o Visa_m (sin las _zero) se reemplazan, dentro de cada foto_mes, por su rank: ceros en 1e-7, positivos en (0,1] y negativos en [-1,0). (`DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 331–358; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 331–358)
5. **Lags, deltas, tendencia y promedio en ventana de 3 meses.** Para todas las columnas salvo identificadores, clase y flags _zero se agregan lag1, lag2, delta1 y delta2 por cliente, y con una función en C++ (Rcpp) la pendiente de cuadrados mínimos (_tend3) y el promedio (_avg3) de una ventana de 3 meses. (`DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 360–386; `DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 446–636; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 360–386; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 446–636)
6. **Variables manuales y de transición, y guardado del dataset.** Se agregan ctrx_quarter_normalizado y mpayroll_sobre_edad, códigos de transición de estado y mora de las tarjetas, flags de prende y apaga para variables de actividad, totales de payroll y consumos y el conteo n_canales_apagados. El dataset resultante se graba en competencia_01_lag1y2_delta1y2_rank.csv.gz y se relee en la segunda parte del notebook. (`DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 638–766; `DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 781–787; `DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 1199–1205; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 638–766)
7. **Parámetros de la corrida e hiperparámetros fijos.** PARAM fija el experimento, la semilla primigenia 600013, los meses (bayesiana 202103–202104, validación 202106, modelo final 202103–202106, predicción 202108), los cortes a evaluar y los parámetros fijos de LightGBM. Los dos experimentos difieren en feature_fraction_bynode: 1,0 en j4955 y 0,2 en j4957. (`DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 873–946; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 873–946)
8. **Clase binaria, partición 70/30 y columnas del modelo.** Sobre 202103 y 202104 se arma una partición 70/30 estratificada por clase, se crea clase01 (BAJA+1 y BAJA+2 valen 1) y se define campos_buenos, que deja afuera la clase y las columnas auxiliares. (`DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 1210–1263; `DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 1268–1282; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 1210–1282)
9. **Exclusión de registros dudosos en el entrenamiento de la bayesiana.** Un modelo auxiliar (modelo30: 2.180 iteraciones, 30 hojas) se entrena con el fold 2 (30%) y puntúa todo el conjunto; del fold 1 se sacan los CONTINUA con prob30 de 0,5 o más. Con las filas restantes se arma dtrain, con peso 0,25 para BAJA+1 y 1,0 para el resto; dvalidate es todo 202106 con los mismos pesos. (`DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 1294–1416; `DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 1639–1694; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 1294–1416; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 1639–1694)
10. **Hiperparámetros: bayesiana en j4957, valores cargados a mano en j4955.** j4957 optimiza num_iterations, num_leaves, min_sum_hessian_in_leaf y feature_fraction con mlr3mbo (kriging y expected improvement, 40 evaluaciones), entrenando en 202103–202104 y midiendo AUC en 202106; registra cada evaluación en BO_log.txt y toma la fila de mayor métrica. En j4955 esas celdas están comentadas y los cuatro valores se escriben en el código. (`DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 972–980; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 1574–1601; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 1752–1791; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 1814–1824; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 2055–2069; `DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 1929–1937)
11. **Limpieza del entrenamiento final por cross-fitting.** Los meses 202103 a 202106 se parten en dos mitades estratificadas; cada mitad recibe prob30 de un modelo auxiliar entrenado en la otra, y se eliminan los CONTINUA con prob30 de 0,5 o más. (`DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 2100–2155; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 2100–2155)
12. **Entrenamiento final con pesos y varias semillas.** Con los hiperparámetros elegidos y los pesos por clase se entrena un modelo por semilla sobre 202103–202106 ya limpio: 3 semillas en j4955 y 12 en j4957. Cada modelo se graba y predice 202108. (`DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 2170–2218; `DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 2471–2521; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 2170–2218; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 2471–2522)
13. **Promedio de semillas y archivos por experimento.** Las probabilidades de las semillas se promedian y se graban en prediccion_promedio.txt dentro de la carpeta de cada experimento. Cada notebook escribe además archivos de envío propios con distintos cortes (7 en j4955 y 11 en j4957). (`DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 2584–2599; `DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 2735–2817; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 2585–2600; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 2736–2866)
14. **Backtest en 202106.** Con los mismos hiperparámetros y pesos se entrena en 202103 y 202104 con 5 semillas y se predice 202106, calculando la ganancia de la competencia para cortes de 4.000 a 19.000 cada 200, por semilla y para el promedio de probabilidades. j4955 agrega una simulación de 5.000 muestras del 70% con el corte en 12.000. (`DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 2819–2918; `DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` líneas 2920–2932; `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` líneas 2868–2967)
15. **Blend por puestos y archivos de envío.** El notebook del blend lee las dos predicciones promedio, convierte cada probabilidad en un puesto, promedia los dos puestos de cada cliente y escribe un archivo con los primeros N clientes para cada corte de 10.500 a 14.500 cada 500. Según el README, se entregó Intentoj_blend_12000.csv. (`DMEyF/Primera-Competencia/notebooks/blend_j4955_j4957.ipynb` líneas 5–33; `DMEyF/Primera-Competencia/README.md` líneas 157–191)

## Archivos

- `DMEyF/Primera-Competencia/README.md` · explicacion · Markdown · 202 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lulimontero/DMEyF/Primera-Competencia/README.md.txt) — Presenta la entrega: estructura de la carpeta, problema y ganancia, pipeline de variables, clase y pesos, limpieza de registros dudosos, optimización bayesiana, tabla comparativa de los experimentos j4955 y j4957, origen de los hiperparámetros de j4955, resultados declarados del backtest en 202106 y del leaderboard público, funcionamiento del blend, elección del corte de 12.000 y pasos para reproducir. La línea 107 es un comentario HTML 'COMPLETAR' sobre las diferencias entre j4953 y j4955, y el texto remite a un .gitignore que no figura entre los archivos del clon.
- `DMEyF/Primera-Competencia/bayesianas/HT4953-01_BO_log.txt` · secundario · Texto · 101 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lulimontero/DMEyF/Primera-Competencia/bayesianas/HT4953-01_BO_log.txt.txt) — Log de la bayesiana del experimento HT4953-01: 100 evaluaciones, una por línea, con fecha, todos los parámetros de LightGBM, número de iteración y métrica (AUC). La fila de mayor métrica (iteración 23, 0,913479658101473) tiene num_iterations 3606, num_leaves 1443, min_sum_hessian_in_leaf 0,0874518118416699 y feature_fraction 0,120189655432349, los valores escritos en j4955.
- `DMEyF/Primera-Competencia/bayesianas/HT4957-01_BO_log.txt` · secundario · Texto · 41 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lulimontero/DMEyF/Primera-Competencia/bayesianas/HT4957-01_BO_log.txt.txt) — Log de la bayesiana del experimento HT4957-01: 40 evaluaciones con feature_fraction_bynode 0,2. La fila de mayor métrica (iteración 36, AUC 0,913532050835411) tiene num_iterations 2652, num_leaves 1642, min_sum_hessian_in_leaf 0,0895907073782362 y feature_fraction 0,110020719581356.
- `DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb` · principal · Jupyter (R) · 2932 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lulimontero/DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb.txt) — Experimento HT4955-01: construye las variables, entrena LightGBM en 202103–202106 con hiperparámetros escritos en el código (feature_fraction_bynode 1,0) y 3 semillas, predice 202108 y graba prediccion_promedio.txt, que es una de las dos entradas del blend. Incluye un backtest en 202106. Las celdas de la optimización bayesiana están comentadas.
- `DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb` · principal · Jupyter (R) · 2967 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lulimontero/DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb.txt) — Experimento HT4957-01: mismo flujo que j4955 con feature_fraction_bynode 0,2, optimización bayesiana propia de 40 evaluaciones y 12 semillas en el modelo final; graba prediccion_promedio.txt, la otra entrada del blend. Difiere de j4955 en esas celdas, en la cantidad de archivos de envío propios (11) y en que no tiene la simulación final del corte de 12.000.
- `DMEyF/Primera-Competencia/notebooks/j4953_competencia.ipynb` · secundario · Jupyter (R) · 2136 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lulimontero/DMEyF/Primera-Competencia/notebooks/j4953_competencia.ipynb.txt) — Experimento HT4953-01, del que según el README salen los hiperparámetros de j4955 y cuya ejecución el README marca como opcional. Corre una bayesiana de 100 evaluaciones con el mismo espacio de búsqueda, métrica AUC y feature_fraction_bynode 1,0, entrenando con todas las filas de 202103–202104 y validando en 202106. En este notebook las variables son el rank con cero fijo más lag1, lag2, delta1 y delta2; no están las celdas de flags _zero, totales de tarjeta, tendencias, variables manuales ni transiciones, ni la exclusión de registros dudosos, ni el backtest. Entrena el modelo final en 202103–202106 con 20 semillas y escribe cinco archivos Intentoj4953_0N.csv con cortes de 11.400 a 12.200.
- `DMEyF/Primera-Competencia/notebooks/blend_j4955_j4957.ipynb` · principal · Jupyter (R) · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lulimontero/DMEyF/Primera-Competencia/notebooks/blend_j4955_j4957.ipynb.txt) — Lee las predicciones promedio de HT4955-01 y HT4957-01, las combina promediando los puestos de cada cliente y escribe los archivos de envío Intentoj_blend_<corte>.csv para cortes de 10.500 a 14.500 cada 500.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### DMEyF/Primera-Competencia/notebooks/j4955_competencia.ipynb

Experimento HT4955-01: construye las variables, entrena LightGBM en 202103–202106 con hiperparámetros escritos en el código (feature_fraction_bynode 1,0) y 3 semillas, predice 202108 y graba prediccion_promedio.txt, que es una de las dos entradas del blend. Incluye un backtest en 202106. Las celdas de la optimización bayesiana están comentadas.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–18] Celdas de texto iniciales: enlace de Colab al notebook z494_TareaHogar_04.ipynb
#   del repositorio dmecoyfin/dmeyf2026, título 'Tarea para el Hogar 04' y una lista de siete cambios, marcados
#   en el código como '>>> CAMBIO … <<< FIN CAMBIO', referidos a la exclusión de registros dudosos del
#   entrenamiento.
#%% celda 1 [texto]
<a href="https://colab.research.google.com/github/dmecoyfin/dmeyf2026/blob/ensembles_2026/ensembles/z494_TareaHogar_04.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

#%% celda 2 [texto]
# Tarea para el Hogar 04

#%% celda 3 [texto]
# ⚠️ CAMBIOS: Excluyendo registros dudosos de training
Todos los cambios están marcados con `>>> CAMBIO` ... `<<< FIN CAMBIO` y las celdas nuevas tienen un título **⚠️ CAMBIO**.

1. `campos_buenos` excluye `training30`, `prob30`, `aporta`, `fold30`
2. Celda nueva: `modelo30` entrenado con el fold 2
3. Celda nueva: `prob30` sobre el training de la BO
4. Celda nueva: `aporta` + `training` (ahora con `fold == 1`)
5. `dtrain` (sin cambio de lógica, solo controles)
6. Arreglo de sintaxis en el hardcodeo de hiperparámetros
7. Celda nueva: limpieza del training final por cross-fitting (**la que cambia el modelo sin BO**)

# [Anotación · líneas 19–97] Celdas de texto con el enunciado de la tarea (objetivos, hiperparámetros de
#   LightGBM, fuentes de consulta, preparación de Google Colab) y dos celdas de código enteramente comentadas
#   (montaje de Google Drive y carga de rpy2).
#%% celda 4 [texto]
#  1. Big Picture

#%% celda 5 [texto]
LightGBM es el algoritmo estado del arte para datasets estructurados.
<br> La Bayesian Optimization es el estado del arte para optimización de hiperparámetros
<br> Las soluciones a las tres competencias de la asignatura contendrán LightGBMs y Bayesian Optimizations
<br> LightGBM ha aumentado en forma no darwiniana sus hiperparámetros en los últimos ocho años; no todos los existentes son útiles.
<br> Es necesario lograr entender cuales son los hiperparámetros relevantes de LightGBM

#%% celda 6 [texto]
# 2. Hiperparámetros del LightGBM

#%% celda 7 [texto]
Los objetivos de esta tarea son:


*   Aumentar la rentabilidad de la campaña de marketing de retención proactiva de clientes.
*   Generar un mejor modelo optimizando sus hiperparámetros
*   Conceptual : investigar los mas relevantes hiperparámetros de LightGBM
*   Familiarizarse con la Bayesian Optimization, sus largos tiempos de corrida y opciones para reducirlos
*   Familiarizarse con el uso de máquinas virtuales de Google Colab
*   Ver un pipeline completo de optimización de hiperparámetros y puesta en producción

#%% celda 8 [texto]
LightGBM cuenta con mas de 60 hiperparámetros, siendo posible utilizar 40 al mismo tiempo, aunque no razonable.
<br> La documentación oficial de los hiperparámetros de LightGBM es  https://lightgbm.readthedocs.io/en/latest/Parameters.html#core-parameters

#%% celda 9 [texto]
Se lo alerta sobre que una Optimizacion Bayesiana lleva varias horas de corrida, y usted deberá correr VARIAS optimizaciones para descubrir cuales parámetros conviene optimizar.
<br> A pesar que la próxima clase es recien en viernes 01 de agosto, inicie la tarea con tiempo, aprenda a planificar estratégicamente sus corridas como un@ científ@  de datos.

#%% celda 10 [texto]
Es necesario investigar cuales son los hiperparámetros de LightGBM que vale la pena optimizar en una Bayesian Optimization, ya que los realmente utiles son apenas un reducido subconjunto.
<br>Usted deberá investigar cuales son los hiperparámetros mas relevantes de LightGBM, su primer alternativa es preguntándole a su amigo con capacidades especiales ChatGPT o sus endogámicos familiares Claude, DeepSeek, Gemini, Grok, etc
<br> La segunda alternativa es la propia documentación de LightGBM  https://lightgbm.readthedocs.io/en/latest/Parameters-Tuning.html

#%% celda 11 [texto]
Adicionalmente podra buscar información como la que proveen esta diminuta muestra aleatoria de artículos ligeros:
*  https://medium.com/@sarahzouinina/a-deep-dive-into-lightgbm-how-to-choose-and-tune-parameters-7c584945842e
*  https://www.kaggle.com/code/somang1418/tuning-hyperparameters-under-10-minutes-lgbm
*  https://towardsdatascience.com/beginners-guide-to-the-must-know-lightgbm-hyperparameters-a0005a812702/


<br>  La muestra anterior se brinda a modo de ejemplo, usted deberá buscar muuuuchas  fuentes adicionales de información
<br> Tenga presente que LightGBM es el estado del arte en modelado predictivo para datasets estructurado, que son el 90% del trabajo del 95% de los Data Scientists en Argentina.

#%% celda 12 [texto]
El desafío de esta tarea es:
* Qué hiperparparámetros conviene optimizar?  Las recomendaciones de los artículos ligeros es siempre sensata?  Sus autores realmente hicieron experimentos o son siemplemente escritores de entretenimiento carente de base científica?
* Elegidos los hiperparámetros, cual es el  <desde, hasta> que se debe utilizar en la Bayesian Optimization ?
* Realmente vale la pena optimizar 10 o 16 hiperparámetros al mismo tiempo ?  No resulta contraproducente una búsqueda en un espacio de tal alta dimensionalidad ?

#%% celda 13 [texto]
## 2.1  Seteo del ambiente en Google Colab

#%% celda 14 [texto]
Esta parte se debe correr con el runtime en Python3
<br>Ir al menu, Runtime -> Change Runtime Type -> Runtime type ->  **Python 3**

#%% celda 15 [texto]
Conectar la virtual machine donde esta corriendo Google Colab con el  Google Drive, para poder tener persistencia de archivos

#%% celda 16 [código]
# primero establecer el Runtime de Python 3
# from google.colab import drive
# drive.mount('/content/.drive')

#%% celda 17 [texto]
Para correr la siguiente celda es fundamental en Arranque en Frio haber copiado el archivo kaggle.json al Google Drive, en la carpeta indicada en el instructivo

<br>los siguientes comando estan en shell script de Linux
*   Crear las carpetas en el Google Drive
*   "instalar" el archivo kaggle.json desde el Google Drive a la virtual machine para que pueda ser utilizado por la libreria  kaggle de Python
*   Bajar el  **dataset_pequeno**  al  Google Drive  y tambien al disco local de la virtual machine que esta corriendo Google Colab

#%% celda 18 [código]
#%load_ext rpy2.ipython

# [Anotación · líneas 98–135] Carga data.table, define DIR como ~/buckets/b1/datasets y lee
#   competencia_01_crudo.csv. La celda 22 contiene, comentados, los comandos de shell para crear carpetas en
#   Colab y descargar ese archivo.
#%% celda 19 [código]
require( "data.table" )

#%% celda 20 [código]
#%%R
#DIR <- "/Users/luciamontero/Desktop/Repositorios/Maestría Ciencia de Datos - UBA/2026/Segundo Cuatri/DMEyF/TP1-v1"
DIR     <- path.expand("~/buckets/b1/datasets")

#%% celda 21 [código]
#dataset <- fread(file.path(DIR, "competencia_01_crudo.csv"))
dataset <- fread(file.path(DIR, "competencia_01_crudo.csv"))

#%% celda 22 [código]
#%%shell

#mkdir -p "/content/.drive/My Drive/dmeyf"
#mkdir -p "/content/buckets"
#ln -s "/content/.drive/My Drive/dmeyf" /content/buckets/b1


#mkdir -p /content/buckets/b1/exp
#mkdir -p /content/buckets/b1/datasets
#mkdir -p /content/datasets



#archivo_origen="https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
#archivo_destino="/content/datasets/competencia_01_crudo.csv"
#archivo_destino_bucket="/content/buckets/b1/datasets/competencia_01_crudo.csv"

#if ! test -f $archivo_destino_bucket; then
#  wget  $archivo_origen  -O $archivo_destino_bucket
#fi


#if ! test -f $archivo_destino; then
#  cp  $archivo_destino_bucket  $archivo_destino
#fi

# [Anotación · líneas 137–181] Calcula clase_ternaria: numera los meses en forma consecutiva (periodo0),
#   obtiene para cada cliente sus dos períodos siguientes y asigna CONTINUA a los períodos anteriores al
#   anteúltimo, BAJA+1 cuando el cliente no aparece en el mes siguiente y BAJA+2 cuando aparece en el siguiente
#   pero no en el subsiguiente. Las filas del último período quedan sin clase.
#%% celda 23 [texto]
## Generacion de la clase_ternaria

#%% celda 24 [texto]
Esta parte se debe correr con el runtime en lenguaje **R** Ir al menu, Runtime -> Change Runtime Tipe -> Runtime type -> R

#%% celda 25 [código]
#%%R

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

# [Anotación · líneas 183–196] Deja comentada la escritura de competencia_01.csv.gz, ordena el dataset por
#   foto_mes, clase_ternaria y numero_de_cliente, cuenta filas por mes y clase y muestra la cantidad de
#   columnas.
#%% celda 26 [código]
#%%R
#fwrite(dataset,
#    file = file.path(DIR, "competencia_01.csv.gz"),
#    sep = ","
#)

#%% celda 27 [código]
#%%R
setorder( dataset, foto_mes, clase_ternaria, numero_de_cliente)
dataset[, .N, list(foto_mes, clase_ternaria)]

#%% celda 28 [código]
ncol(dataset)

# [Anotación · líneas 198–244] Recorre cada foto_mes y arma vars_full_zero, la tabla de columnas numéricas
#   (sin foto_mes ni numero_de_cliente) cuyos valores son todos cero en ese mes. Luego, para cada mes de esa
#   tabla, reemplaza por NA los ceros de esas columnas en ese mes.
#%% celda 29 [texto]
## vars_full_zero muestra qué columnas estuvieron completamente en cero en qué meses.

#%% celda 30 [código]
# Busco los features que tienen full_zero menos foto_mes y numero_de_cliente (preventivo)
numeric_cols <- names(dataset)[sapply(dataset, is.numeric)]
numeric_cols <- setdiff(numeric_cols, c("foto_mes", "numero_de_cliente"))

result_list <- list()

for(month in unique(dataset$foto_mes)) {
  month_data <- dataset[foto_mes == month, ..numeric_cols]
  
  # TODO CERO
  zero_cols <- numeric_cols[sapply(month_data, function(x) all(x == 0, na.rm = TRUE))]
  
  if(length(zero_cols) > 0) {
    result_list[[as.character(month)]] <- data.table(
      foto_mes = month,
      column_name = zero_cols
    )
  }
}

vars_full_zero <- rbindlist(result_list)
print(vars_full_zero)

# Aplico NULL 
#for(month in unique(vars_full_zero$foto_mes)){
#  vars_this_month <- vars_full_zero[foto_mes == month, column_name]
  
#  dataset[foto_mes == month,
#          (vars_this_month) := lapply(.SD, function(x) ifelse(x == 0, NA, x)),
#          .SDcols = vars_this_month]
#}

#%% celda 31 [texto]
### Les aplico NA

#%% celda 32 [código]
# Aplico NULL 
for(month in unique(vars_full_zero$foto_mes)){
  vars_this_month <- vars_full_zero[foto_mes == month, column_name]
  
  dataset[foto_mes == month,
          (vars_this_month) := lapply(.SD, function(x) ifelse(x == 0, NA, x)),
          .SDcols = vars_this_month]}

# [Anotación · líneas 246–276] Para cada columna numérica (sin numero_de_cliente, foto_mes ni clase_ternaria)
#   que vale cero al menos una vez en algún mes crea una columna <variable>_zero con 1 si el valor es 0, 0 si es
#   distinto de 0 y NA si es NA. Imprime la cantidad creada y, como control, la distribución de
#   cpayroll_trx_zero por mes.
#%% celda 33 [texto]
## NUEVO: variables _zero (flag 1/0/NA, no se rankean ni laguean)

#%% celda 34 [código]
# =====================================================================
# CAMBIO 2: variables _zero (FLAG de "la variable vale cero")
#   1  si la variable original vale 0
#   NA si la variable original es NA
#   0  en el resto de los casos
# Solo para las variables que ALGUNA VEZ valen cero (en cualquier mes).
# Se calculan sobre los valores CRUDOS (antes del rank, que pisa los montos).
# Estas columnas NO se rankean ni se laguean (ver celda de rank/lags).
# =====================================================================
cols_base_zero <- setdiff(colnames(dataset),
                          c("numero_de_cliente", "foto_mes", "clase_ternaria"))
cols_base_zero <- cols_base_zero[sapply(cols_base_zero, function(v) is.numeric(dataset[[v]]))]

tiene_cero <- dataset[, sapply(.SD, function(x) any(x == 0, na.rm = TRUE)),
                      .SDcols = cols_base_zero]
cols_zero  <- cols_base_zero[tiene_cero]

# as.integer(x == 0) da exactamente 1 / 0 / NA  (NA == 0 es NA)
dataset[, paste0(cols_zero, "_zero") := lapply(.SD, function(x) as.integer(x == 0)),
        .SDcols = cols_zero]

cat("Variables _zero creadas:", length(cols_zero), " ncol(dataset) =", ncol(dataset), "\n")

# control sobre un ejemplo
dataset[, list(uno  = sum(cpayroll_trx_zero == 1L, na.rm = TRUE),
               cero = sum(cpayroll_trx_zero == 0L, na.rm = TRUE),
               na   = sum(is.na(cpayroll_trx_zero))), by = foto_mes][order(foto_mes)]

# [Anotación · líneas 278–314] Si existen los límites de compra de Master y Visa, suma ambas tarjetas en
#   mv_mlimitecompra, mv_msaldototal, mv_mconsumototal, mv_mpagado y mv_mpagominimo (rowSums con na.rm) y
#   calcula cuatro cocientes sobre el límite total: mvr_utilizacion, mvr_consumo_limite, mvr_pago_limite y
#   mvr_pagominimo_lim. Los resultados infinitos o NaN se pasan a NA. Todo se calcula sobre los montos sin
#   rankear.
#%% celda 35 [texto]
## NUEVO: totales de tarjeta + ratios de utilizacion (ANTES del rank)

#%% celda 36 [código]
# =====================================================================
# NUEVO (va ANTES del rank): totales de tarjeta + RATIOS de utilizacion.
# Se calculan sobre monto CRUDO a proposito: un ratio de rankings no
# significa nada. Al empezar con "m", el grep ^m de la celda siguiente
# los rankea por mes (bien) y el loop de lags les da lag/delta
# (util: tendencia de la utilizacion mes a mes).
# =====================================================================
req_lim <- c("Master_mlimitecompra","Visa_mlimitecompra")
if (all(req_lim %in% colnames(dataset))) {
  dataset[, mv_mlimitecompra := rowSums(cbind(Master_mlimitecompra, Visa_mlimitecompra), na.rm = TRUE) ]

  if (all(c("Master_msaldototal","Visa_msaldototal") %in% colnames(dataset)))
    dataset[, mv_msaldototal   := rowSums(cbind(Master_msaldototal,   Visa_msaldototal),   na.rm = TRUE) ]
  if (all(c("Master_mconsumototal","Visa_mconsumototal") %in% colnames(dataset)))
    dataset[, mv_mconsumototal := rowSums(cbind(Master_mconsumototal, Visa_mconsumototal), na.rm = TRUE) ]
  if (all(c("Master_mpagado","Visa_mpagado") %in% colnames(dataset)))
    dataset[, mv_mpagado       := rowSums(cbind(Master_mpagado,       Visa_mpagado),       na.rm = TRUE) ]
  if (all(c("Master_mpagominimo","Visa_mpagominimo") %in% colnames(dataset)))
    dataset[, mv_mpagominimo   := rowSums(cbind(Master_mpagominimo,   Visa_mpagominimo),   na.rm = TRUE) ]

  # ratios de utilizacion (denominador = limite de compra total)
  if ("mv_msaldototal"   %in% colnames(dataset)) dataset[, mvr_utilizacion    := mv_msaldototal   / mv_mlimitecompra ]  # saldo/limite (el mas predictivo)
  if ("mv_mconsumototal" %in% colnames(dataset)) dataset[, mvr_consumo_limite := mv_mconsumototal / mv_mlimitecompra ]
  if ("mv_mpagado"       %in% colnames(dataset)) dataset[, mvr_pago_limite    := mv_mpagado       / mv_mlimitecompra ]
  if ("mv_mpagominimo"   %in% colnames(dataset)) dataset[, mvr_pagominimo_lim := mv_mpagominimo   / mv_mlimitecompra ]

  # division por limite 0 -> Inf/NaN -> NA
  for (cc in intersect(c("mvr_utilizacion","mvr_consumo_limite","mvr_pago_limite","mvr_pagominimo_lim"), colnames(dataset))) {
    malos <- which( is.infinite(dataset[[cc]]) | is.nan(dataset[[cc]]) )
    if (length(malos)) set(dataset, malos, cc, NA_real_)
  }
  cat("Ratios de utilizacion agregados (antes del rank). ncol =", ncol(dataset), "\n")
}

# [Anotación · líneas 316–358] Define rank_cero_fijo: los ceros quedan en 1e-7, los positivos se reemplazan
#   por su rango (frank, empates promediados) dividido por la cantidad de positivos, los negativos por el rango
#   negado dividido por la cantidad de negativos, y los NA siguen NA. La aplica dentro de cada foto_mes a las
#   columnas cuyo nombre empieza con m, Master_m o Visa_m (sin las _zero), reemplazando los valores originales.
#%% celda 37 [texto]
## Generación de lag1, delta1, lag2, delta2
Para cada campo del dataset original (*) se crean los siguientes campos de a partir de la historia:
- lag1 lags de orden 1
- delta1 valor actual - lag1
- lag2 lags de orden 2
- delta2 valor actual - lag2

Se pasa de 155 campos a 763

(*) Excepto para los campos [numero_de_cliente, foto_mes, clase_ternaria]

#%% celda 38 [texto]
**Primero calculo ranking y despues lags y deltas sobre ranking**

#%% celda 39 [código]
# ---- NUEVO: ranking de variables monetarias por foto_mes (antes de lags y deltas) ----
# rank con cero fijo: 0 queda en 1e-7, positivos en (0,1], negativos en [-1,0), NA queda NA
rank_cero_fijo <- function(x) {
  y   <- rep(NA_real_, length(x))
  pos <- !is.na(x) & x > 0
  neg <- !is.na(x) & x < 0
  y[!is.na(x) & x == 0] <- 1e-7   # cero fijo en 1e-7 (y no 0) para que la celda de 0 -> NA no lo pise
  if (any(pos)) y[pos] <-  frank( x[pos], ties.method = "average") / sum(pos)
  if (any(neg)) y[neg] <- -frank(-x[neg], ties.method = "average") / sum(neg)
  y
}

# variables monetarias (ajustar el patron si hace falta)
cols_monetarias <- grep("^(m|Master_m|Visa_m)", colnames(dataset), value = TRUE)
# CAMBIO 2: las _zero NO participan del rank (mcaja_ahorro_zero, Master_m..._zero empiezan con m)
cols_monetarias <- grep("_zero$", cols_monetarias, value = TRUE, invert = TRUE)
cat("Variables monetarias a rankear:", length(cols_monetarias), "\n")

# reemplazo las originales por su ranking dentro de cada mes
dataset[, (cols_monetarias) := lapply(.SD, rank_cero_fijo),
        by = foto_mes, .SDcols = cols_monetarias]

# opción B: conservar las originales y sumar las rankeadas
# dataset[, paste0(cols_monetarias, "_rank") := lapply(.SD, rank_cero_fijo),
#         by = foto_mes, .SDcols = cols_monetarias]

# ---- FIN NUEVO ----

# [Anotación · líneas 360–386] Toma como columnas a laguear todas menos numero_de_cliente, foto_mes,
#   clase_ternaria y las _zero. Para cada una crea, por cliente, el valor de uno y dos meses atrás (_lag1,
#   _lag2) y las diferencias del valor actual con cada uno (_delta1, _delta2).
# Feature Engineering Historico
cols_lagueables <- copy( setdiff(
    colnames(dataset),
    c("numero_de_cliente", "foto_mes", "clase_ternaria")
) )
# CAMBIO 2: las _zero tampoco se laguean / deltean / tendencian
cols_lagueables <- grep("_zero$", cols_lagueables, value = TRUE, invert = TRUE)


dataset[, 
    paste0(cols_lagueables, "_lag1") := shift(.SD, 1, NA, "lag"),
    by = numero_de_cliente,
    .SDcols = cols_lagueables
]

dataset[, 
    paste0(cols_lagueables, "_lag2") := shift(.SD, 2, NA, "lag"),
    by = numero_de_cliente,
    .SDcols = cols_lagueables
]

# agrego los delta lags de orden 1
for (vcol in cols_lagueables)
{
    dataset[, paste0(vcol, "_delta1") := get(vcol) - get(paste0(vcol, "_lag1"))]
    dataset[, paste0(vcol, "_delta2") := get(vcol) - get(paste0(vcol, "_lag2"))]
}

# [Anotación · líneas 388–441] Celda enteramente comentada con la variante de orden inverso: lags y deltas
#   sobre valores crudos y después el rank de todas las columnas numéricas por mes.
#%% celda 40 [texto]
Este codigo sería para primero calculo los lags y delta lags y después el ranking ; con la versión de arriba era al revés

#%% celda 41 [código]
# # ---- NUEVO: lags y deltas sobre valores crudos, y DESPUES ranking por foto_mes ----
# # rank con cero fijo: 0 queda en 1e-7, positivos en (0,1], negativos en [-1,0), NA queda NA
# rank_cero_fijo <- function(x) {
#   y   <- rep(NA_real_, length(x))
#   pos <- !is.na(x) & x > 0
#   neg <- !is.na(x) & x < 0
#   y[!is.na(x) & x == 0] <- 1e-7   # cero fijo en 1e-7 (y no 0) para que la celda de 0 -> NA no lo pise
#   if (any(pos)) y[pos] <-  frank( x[pos], ties.method = "average") / sum(pos)
#   if (any(neg)) y[neg] <- -frank(-x[neg], ties.method = "average") / sum(neg)
#   y
# }

# # Feature Engineering Historico (ahora sobre los valores crudos)
# cols_lagueables <- copy( setdiff(
#     colnames(dataset),
#     c("numero_de_cliente", "foto_mes", "clase_ternaria")
# ) )


# dataset[, 
#     paste0(cols_lagueables, "_lag1") := shift(.SD, 1, NA, "lag"),
#     by = numero_de_cliente,
#     .SDcols = cols_lagueables
# ]

# dataset[, 
#     paste0(cols_lagueables, "_lag2") := shift(.SD, 2, NA, "lag"),
#     by = numero_de_cliente,
#     .SDcols = cols_lagueables
# ]

# # agrego los delta lags de orden 1 y 2
# for (vcol in cols_lagueables)
# {
#     dataset[, paste0(vcol, "_delta1") := get(vcol) - get(paste0(vcol, "_lag1"))]
#     dataset[, paste0(vcol, "_delta2") := get(vcol) - get(paste0(vcol, "_lag2"))]
# }

# # ranking de TODAS las variables numericas (incluye lags y deltas), menos identificadores y la clase
# cols_a_rankear <- setdiff(
#   colnames(dataset)[sapply(dataset, is.numeric)],
#   c("numero_de_cliente", "foto_mes", "clase_ternaria")
# )
# cat("Variables a rankear:", length(cols_a_rankear), "\n")

# # reemplazo las originales por su ranking dentro de cada mes
# dataset[, (cols_a_rankear) := lapply(.SD, rank_cero_fijo),
#         by = foto_mes, .SDcols = cols_a_rankear]

# # ---- FIN NUEVO ----

# [Anotación · líneas 443–534] Carga Rcpp y define en C++ la función fhistC: para cada fila, con los valores
#   no NA de la ventana que empieza en la posición indicada por pdesde, calcula la pendiente de la recta de
#   cuadrados mínimos, el mínimo, el máximo y el promedio; devuelve NA si hay menos de dos valores. Devuelve
#   además el valor de la fila anterior cuando pertenece a la misma ventana.
#%% celda 42 [texto]
## variables de tendencia (cuadrados minimos) y promedio de la ventana

#%% celda 43 [código]
# =====================================================================
# CAMBIO 3: variables de TENDENCIA (pendiente por cuadrados minimos del
# valor actual y los ventana-1 anteriores) + promedio de la ventana.
# Corre DESPUES de rank + lags/deltas: usa cols_lagueables (sin _zero)
# y tendencia sobre los montos ya rankeados, igual que los lags.
# =====================================================================
if (!require("Rcpp")) install.packages("Rcpp")
library(Rcpp)

#------------------------------------------------------------------------------
# se calculan para los meses previos el minimo, maximo y
#  tendencia calculada con cuadrados minimos
# la formula de calculo de la tendencia puede verse en
#  https://stats.libretexts.org/Bookshelves/Introductory_Statistics/Book%3A_Introductory_Statistics_(Shafer_and_Zhang)/10%3A_Correlation_and_Regression/10.04%3A_The_Least_Squares_Regression_Line
# para la maxíma velocidad esta funcion esta escrita en lenguaje C,
# y no en la porqueria de R o Python

cppFunction("NumericVector fhistC(NumericVector pcolumna, IntegerVector pdesde )
{
  /* Aqui se cargan los valores para la regresion */
  double  x[100] ;
  double  y[100] ;

  int n = pcolumna.size();
  NumericVector out( 5*n );

  for(int i = 0; i < n; i++)
  {
    //lag
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

    /* Si hay al menos dos valores */
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
#------------------------------------------------------------------------------

# [Anotación · líneas 536–605] Define TendenciaYmuchomas: arma vector_desde, que indica para cada fila dónde
#   empieza su ventana sin cruzar de un cliente a otro, llama a fhistC por cada columna y agrega al dataset,
#   según los argumentos, las columnas _tend, _min, _max, _avg, _ratioavg y _ratiomax con el tamaño de ventana
#   como sufijo.
# calcula la tendencia de las variables cols de los ultimos 6 meses
# la tendencia es la pendiente de la recta que ajusta por cuadrados minimos
# La funcionalidad de ratioavg es autoria de  Daiana Sparta,  UAustral  2021

TendenciaYmuchomas <- function(
    dataset, cols, ventana = 6, tendencia = TRUE,
    minimo = TRUE, maximo = TRUE, promedio = TRUE,
    ratioavg = FALSE, ratiomax = FALSE) {
  gc(verbose= FALSE)
  # Esta es la cantidad de meses que utilizo para la historia
  ventana_regresion <- ventana

  last <- nrow(dataset)

  # creo el vector_desde que indica cada ventana
  # de esta forma se acelera el procesamiento ya que lo hago una sola vez
  vector_ids <- dataset[ , numero_de_cliente ]

  vector_desde <- seq(
    -ventana_regresion + 2,
    nrow(dataset) - ventana_regresion + 1
  )

  vector_desde[1:ventana_regresion] <- 1

  for (i in 2:last) {
    if (vector_ids[i - 1] != vector_ids[i]) {
      vector_desde[i] <- i
    }
  }
  for (i in 2:last) {
    if (vector_desde[i] < vector_desde[i - 1]) {
      vector_desde[i] <- vector_desde[i - 1]
    }
  }

  for (campo in cols) {
    nueva_col <- fhistC(dataset[, get(campo)], vector_desde)

    if (tendencia) {
      dataset[, paste0(campo, "_tend", ventana) :=
        nueva_col[(0 * last + 1):(1 * last)]]
    }

    if (minimo) {
      dataset[, paste0(campo, "_min", ventana) :=
        nueva_col[(1 * last + 1):(2 * last)]]
    }

    if (maximo) {
      dataset[, paste0(campo, "_max", ventana) :=
        nueva_col[(2 * last + 1):(3 * last)]]
    }

    if (promedio) {
      dataset[, paste0(campo, "_avg", ventana) :=
        nueva_col[(3 * last + 1):(4 * last)]]
    }

    if (ratioavg) {
      dataset[, paste0(campo, "_ratioavg", ventana) :=
        get(campo) / nueva_col[(3 * last + 1):(4 * last)]]
    }

    if (ratiomax) {
      dataset[, paste0(campo, "_ratiomax", ventana) :=
        get(campo) / nueva_col[(2 * last + 1):(3 * last)]]
    }
  }
}
# [Anotación · líneas 606–636] Ordena el dataset por numero_de_cliente y foto_mes, reserva lugar para columnas
#   nuevas con setalloccol y llama a TendenciaYmuchomas sobre las columnas lagueables con ventana 3, pidiendo
#   sólo tendencia y promedio (_tend3 y _avg3). Vuelve a ordenar por foto_mes y cliente, verifica que existan
#   las _tend3 e imprime la máxima diferencia entre ctrx_quarter_tend3 y ctrx_quarter_delta2/2.
#------------------------------------------------------------------------------

# fhistC exige las filas de cada cliente contiguas y ordenadas por mes
setorderv(dataset, c("numero_de_cliente", "foto_mes"))

# la funcion agrega columnas por referencia DENTRO de una funcion: si se agotan
# los slots pre-reservados de data.table, las columnas nuevas no llegan al
# dataset global. Reservo lugar antes por las dudas.
setalloccol(dataset, ncol(dataset) + 2 * length(cols_lagueables) + 100)

TendenciaYmuchomas(dataset,
  cols= cols_lagueables,
  ventana= 3,
  tendencia= TRUE,
  minimo= FALSE,
  maximo= FALSE,
  promedio= TRUE,
  ratioavg= FALSE,
  ratiomax= FALSE
)

setorder( dataset, foto_mes, numero_de_cliente )

# controles
stopifnot(all(paste0(cols_lagueables, "_tend3") %in% colnames(dataset)))
cat("Tendencias agregadas. ncol(dataset) =", ncol(dataset), "\n")

# OJO: con ventana=3 la pendiente es (x_t - x_{t-2})/2 = delta2/2 -> redundante.
# Esta diferencia deberia dar ~0. Para sumar informacion nueva, probar ventana= 6.
dataset[!is.na(ctrx_quarter_tend3) & !is.na(ctrx_quarter_delta2),
        max(abs(ctrx_quarter_tend3 - ctrx_quarter_delta2 / 2))]

# [Anotación · líneas 638–664] Crea dos variables que no pasan por rank, lags ni tendencia:
#   ctrx_quarter_normalizado, que multiplica ctrx_quarter por 5, 2 y 1,2 para clientes con cliente_antiguedad 1,
#   2 y 3, y mpayroll_sobre_edad, el cociente entre mpayroll (ya rankeado) y cliente_edad, con infinitos y NaN
#   pasados a NA. Las últimas líneas son controles.
#%% celda 44 [código]
# =====================================================================
# Variables manuales: NO se rankean, NO se laguean, NO tienen tendencia.
# Van DESPUES de la celda de tendencias: cols_monetarias y cols_lagueables
# ya se usaron, asi que estas columnas quedan afuera automaticamente.
# Igual entran a la bayesiana y al modelo final (via campos_buenos).
# =====================================================================

# ctrx_quarter corregido para clientes con menos de 3 meses de antiguedad
# (ctrx_quarter es un conteo: no fue rankeado, esta crudo)
# factores heuristicos (no proporcionales): inflan a los clientes nuevos
dataset[, ctrx_quarter_normalizado := as.numeric(ctrx_quarter)]
dataset[cliente_antiguedad == 1, ctrx_quarter_normalizado := ctrx_quarter * 5.0]
dataset[cliente_antiguedad == 2, ctrx_quarter_normalizado := ctrx_quarter * 2.0]
dataset[cliente_antiguedad == 3, ctrx_quarter_normalizado := ctrx_quarter * 1.2]

# mpayroll aca YA esta rankeado por mes -> el ratio no arrastra inflacion
dataset[, mpayroll_sobre_edad := mpayroll / cliente_edad]
dataset[is.infinite(mpayroll_sobre_edad) | is.nan(mpayroll_sobre_edad),
        mpayroll_sobre_edad := NA]

# controles
c("ctrx_quarter_normalizado", "mpayroll_sobre_edad") %in% colnames(dataset)        # TRUE TRUE
any(grepl("^(ctrx_quarter_normalizado|mpayroll_sobre_edad)_", colnames(dataset)))   # FALSE (sin lags/tend)
dataset[, .(min = min(ctrx_quarter_normalizado, na.rm = TRUE),
            max = max(ctrx_quarter_normalizado, na.rm = TRUE)), by = cliente_antiguedad <= 3]
summary(dataset$mpayroll_sobre_edad)

# [Anotación · líneas 666–704] Para Master_status y Visa_status crea _trans (código que combina el estado del
#   mes anterior y el actual, con NA codificado como 99) y _empeora (1 si el estado actual es mayor que el
#   anterior). Para Master_delinquency y Visa_delinquency crea _trans (NA codificado como 9) y _entra_mora (1 si
#   pasa de 0 a 1).
#%% celda 45 [texto]
## NUEVO: variables de transicion (anterior -> actual) + flags prende/apaga

#%% celda 46 [código]
# =====================================================================
# NUEVO: variables de TRANSICION (estado anterior -> estado actual)
# Corre al FINAL de la celda de FE (ya existen los _lag1).
# Idea (guia): lo que aporta es el CRUCE anterior->actual y los flags
# de prender/apagar, NO la dummy del estado anterior aislada.
# Estas columnas quedan CRUDAS: no se rankean ni se vuelven a laguear.
# =====================================================================

# ---------- 1) STATUS de tarjeta: combinacion + direccion ----------
# Master_status / Visa_status in {0,6,7,9} + NA.  NA se codifica como 99.
for (v in c("Master_status", "Visa_status")) {
  vlag <- paste0(v, "_lag1")
  if (vlag %in% colnames(dataset)) {
    # combinacion anterior -> actual (codigo unico)
    dataset[, paste0(v, "_trans") :=
              fifelse(is.na(get(vlag)), 99L, as.integer(get(vlag))) * 100L +
              fifelse(is.na(get(v)),    99L, as.integer(get(v))) ]
    # EMPEORA: el estado sube (0<6<7<9 es monotono en "gravedad") -> deterioro
    dataset[, paste0(v, "_empeora") :=
              as.integer( !is.na(get(vlag)) & !is.na(get(v)) & get(v) > get(vlag) ) ]
  }
}

# ---------- 2) DELINQUENCY (mora): combinacion anterior -> actual ----------
# Master_delinquency / Visa_delinquency in {0,1} + NA.  NA se codifica como 9.
for (v in c("Master_delinquency", "Visa_delinquency")) {
  vlag <- paste0(v, "_lag1")
  if (vlag %in% colnames(dataset)) {
    dataset[, paste0(v, "_trans") :=
              fifelse(is.na(get(vlag)), 9L, as.integer(get(vlag))) * 10L +
              fifelse(is.na(get(v)),    9L, as.integer(get(v))) ]
    dataset[, paste0(v, "_entra_mora") :=
              as.integer( !is.na(get(vlag)) & get(vlag) == 0 & get(v) == 1 ) ]
  }
}

# [Anotación · líneas 706–733] Para siete variables de conteo (ctrx_quarter, cpayroll_trx, cpayroll2_trx,
#   transacciones y consumos de Visa y Master) crea _prende (el mes anterior valía 0 y el actual es mayor que 0)
#   y _apaga (el anterior era mayor que 0 y el actual es 0 o NA). Para active_quarter crea active_quarter_apaga
#   (pasa de 1 a 0) y active_quarter_prende (de 0 a 1).
# ---------- 3) ACTIVIDAD: flags de encendido/apagado (0 -> >0  y  >0 -> 0) ----
# Solo variables de CONTEO (quedaron crudas, no rankeadas).
cols_actividad <- c(
  "ctrx_quarter",
  "cpayroll_trx", "cpayroll2_trx",
  "ctarjeta_visa_transacciones", "ctarjeta_master_transacciones",
  "Master_cconsumos", "Visa_cconsumos"
)
for (v in cols_actividad) {
  vlag <- paste0(v, "_lag1")
  if (v %in% colnames(dataset) & vlag %in% colnames(dataset)) {
    dataset[, paste0(v, "_prende") :=
              as.integer( !is.na(get(vlag)) & get(vlag) == 0 &
                          !is.na(get(v))    & get(v)    > 0 ) ]
    dataset[, paste0(v, "_apaga") :=
              as.integer( !is.na(get(vlag)) & get(vlag) > 0 &
                          ( is.na(get(v)) | get(v) == 0 ) ) ]
  }
}

# ---------- 4) ACTIVE_QUARTER: dejar de estar activo (1 -> 0) ----------
# 1->0 es casi literal "dejo de operar": muy on-target para BAJA+2.
if (all(c("active_quarter","active_quarter_lag1") %in% colnames(dataset))) {
  dataset[, active_quarter_apaga :=
            as.integer( !is.na(active_quarter_lag1) & active_quarter_lag1 == 1 & active_quarter == 0 ) ]
  dataset[, active_quarter_prende :=
            as.integer( !is.na(active_quarter_lag1) & active_quarter_lag1 == 0 & active_quarter == 1 ) ]
}

# [Anotación · líneas 735–766] Suma cpayroll_trx y cpayroll2_trx en cpayroll_tot y los consumos de Master y
#   Visa en cconsumos_tot, calcula el lag 1 de cada total por cliente y sus flags _apaga y _prende. Crea
#   n_canales_apagados como la suma de cuatro flags: ctrx_quarter_apaga, active_quarter_apaga,
#   cpayroll_tot_apaga y cconsumos_tot_apaga.
# ---------- 5) PAYROLL total (haberes): perder el sueldo = fuga fuerte ----------
if (all(c("cpayroll_trx","cpayroll2_trx") %in% colnames(dataset))) {
  dataset[, cpayroll_tot := rowSums(cbind(cpayroll_trx, cpayroll2_trx), na.rm = TRUE) ]
  dataset[, cpayroll_tot_lag1 := shift(cpayroll_tot, 1, NA, "lag"), by = numero_de_cliente ]
  dataset[, cpayroll_tot_apaga  :=
            as.integer( !is.na(cpayroll_tot_lag1) & cpayroll_tot_lag1 > 0 & cpayroll_tot == 0 ) ]
  dataset[, cpayroll_tot_prende :=
            as.integer( !is.na(cpayroll_tot_lag1) & cpayroll_tot_lag1 == 0 & cpayroll_tot > 0 ) ]
}

# ---------- 6) CONSUMO total de tarjetas: on/off combinado ----------
if (all(c("Master_cconsumos", "Visa_cconsumos") %in% colnames(dataset))) {
  dataset[, cconsumos_tot := rowSums(cbind(Master_cconsumos, Visa_cconsumos), na.rm = TRUE) ]
  dataset[, cconsumos_tot_lag1 := shift(cconsumos_tot, 1, NA, "lag"), by = numero_de_cliente ]
  dataset[, cconsumos_tot_prende :=
            as.integer( !is.na(cconsumos_tot_lag1) & cconsumos_tot_lag1 == 0 & cconsumos_tot >  0 ) ]
  dataset[, cconsumos_tot_apaga :=
            as.integer( !is.na(cconsumos_tot_lag1) & cconsumos_tot_lag1 >  0 & cconsumos_tot == 0 ) ]
}

# ---------- 7) SCORE de intensidad de fuga: cuantos canales apago este mes ----
# Lista CURADA (canales primarios) para no doble-contar Master/Visa sueltos.
apaga_primarios <- intersect(
  c("ctrx_quarter_apaga", "active_quarter_apaga",
    "cpayroll_tot_apaga", "cconsumos_tot_apaga"),
  colnames(dataset)
)
if (length(apaga_primarios) >= 2) {
  dataset[, n_canales_apagados := rowSums(.SD, na.rm = TRUE), .SDcols = apaga_primarios ]
}

cat("Variables de transicion + flags agregadas. ncol(dataset) =", ncol(dataset), "\n")

# [Anotación · líneas 768–787] Muestra la cantidad y los nombres de las columnas y graba el dataset con todas
#   las variables en ~/buckets/b1/datasets/competencia_01_lag1y2_delta1y2_rank.csv.gz.
#%% celda 47 [texto]
Verificación de los campos recién creados

#%% celda 48 [código]
ncol(dataset)
colnames(dataset)

#%% celda 49 [código]
#fwrite(dataset,
#    file = file.path(DIR, "competencia_01_lag1y2_delta1y2_rank.csv.gz"),
#    sep = ","
#)

#%% celda 50 [código]
DIR <- path.expand("~/buckets/b1/datasets")

fwrite(dataset,
    file = file.path(DIR, "competencia_01_lag1y2_delta1y2_rank.csv.gz"),
    sep = ","
)

# [Anotación · líneas 789–862] Imprime la hora, borra todos los objetos de memoria y carga las librerías de la
#   segunda parte: parallel, R.utils, primes, rlist, yaml, lightgbm, DiceKriging y mlrMBO (instalándolas si
#   faltan); instala bbotk, mlr3, mlr3mbo y mlr3learners y carga bbotk, paradox, mlr3mbo, mlr3learners, ggplot2,
#   dplyr y scales.
#%% celda 51 [texto]
## 2.2 Optimizacion Hiperparámetros

#%% celda 52 [texto]
Esta parte se debe correr con el runtime en lenguaje R Ir al menu, Runtime -> Change Runtime Type -> Runtime type -> R

#%% celda 53 [texto]
## 2.2.1 Inicio

#%% celda 54 [texto]
limpio el ambiente de R

#%% celda 55 [código]
#%%R
format(Sys.time(), "%a %b %d %X %Y")

#%% celda 56 [código]
#%%R
# limpio la memoria
rm(list=ls(all.names=TRUE)) # remove all objects
gc(full=TRUE, verbose=FALSE) # garbage collection

#%% celda 57 [texto]
## 2.2.2 Carga de Librerias

#%% celda 58 [texto]
Esta parte lleva varios minutos la primera vez en Google Colab

#%% celda 59 [código]
#%%R
# cargo las librerias que necesito
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

#%% celda 60 [código]
# Librerias  modernas  para la Bayesian Optimization
install.packages( c("bbotk", "mlr3", "mlr3mbo", "mlr3learners", "DiceKriging") )

#%% celda 61 [código]
library(bbotk)        # For ObjectiveRFun, OptimInstanceBatchSingleCrit, trm(), opt()
library(paradox)      # For ps(), p_dbl() 
library(mlr3mbo)      # For bayesopt_ego, srlrn(), acqf(), acqo(), opt("mbo")
library(mlr3learners) # For lrn("regr.km")

#%% celda 62 [código]
require("ggplot2")

#%% celda 63 [código]
library(dplyr)
library(ggplot2)
library(scales) # Para el formato de números en el eje logarítmico

# [Anotación · líneas 864–895] Define PARAM: experimento HT4955-01, semilla primigenia 600013, meses de la
#   bayesiana 202103 y 202104, meses del modelo final 202103 a 202106, validación 202106, predicción 202108,
#   cortes de 4.000 a 19.000 cada 200, porcentaje de training 70 y undersampling 1 (toma todos los CONTINUA).
#%% celda 64 [texto]
## 2.2.3 Definicion de Parámetros

#%% celda 65 [texto]
Aquí debe **cargar SU semilla primigenia**


Recuerde **cambiar el numero de experimento en cada corrida nueva**

#%% celda 66 [código]
#%%R
PARAM <- list()
PARAM$experimento <- "HT4955-01"
PARAM$semilla_primigenia <- 600013

#%% celda 67 [código]
#%%R
# training y future
PARAM$train <- c(202103,202104) #entrenamiento bayesiana
PARAM$train_final <- c(202103,202104,202105,202106) #entrenamiento modelo
PARAM$validate <- c(202106)   # validacion de la bayesiana
PARAM$future <- c(202108) #prediccion modelo
PARAM$semilla_kaggle <- 600013 #gustavo pasquini no usa, acá lo uso para la funcion inicializar
PARAM$cortes <- seq(4000, 19000, by= 200) #la secuencia va de 4.000 a 19.000 saltando de a 500; en gustavo pasquini va de 9000 a 15000
PARAM$training_pct <- 70 #la introduce gustavo pasquini

#%% celda 68 [código]
#%%R
# un undersampling de 0.1  toma solo el 10% de los CONTINUA
# undersampling de 1.0  implica tomar TODOS los datos

PARAM$trainingstrategy$undersampling <- 1

# [Anotación · líneas 897–946] Define los parámetros fijos de LightGBM: boosting gbdt, objective binary,
#   metric auc, deterministic TRUE, seed 600013, max_depth -1, lambda_l1 y lambda_l2 en 0, max_bin 31,
#   fracciones de bagging en 1, min_data_in_leaf 0, learning_rate 0,005, feature_fraction 0,5 y
#   feature_fraction_bynode 1,0. num_iterations 20000, num_leaves 1024 y min_sum_hessian_in_leaf 1e-06 son
#   valores iniciales que luego se reemplazan.
#%% celda 69 [código]
#%%R
# Parametros LightGBM

PARAM$hyperparametertuning$xval_folds <- 5 

# parametros fijos del LightGBM que se pisaran con la parte variable de la BO
PARAM$lgbm$param_fijos <-  list( # nolint
  boosting = "gbdt", # puede ir dart, ni pruebe random_forest
  objective = "binary",
  metric = "auc",
  #metric = "average_precision", #average_precision pone gustavo pasquini
  feature_pre_filter = FALSE,
  first_metric_only = FALSE,
  boost_from_average = TRUE,
  force_row_wise = TRUE, # para reducir warnings
  #force_col_wise = TRUE,
  deterministic = TRUE, #pone gustavo pasquini
  verbosity = -100,

  seed = PARAM$semilla_primigenia,

  max_depth = -1L, # -1 significa no limitar,  por ahora lo dejo fijo
  min_gain_to_split = 0, #min_gain_to_split >= 0
  lambda_l1 = 0.0, # lambda_l1 >= 0.0
  lambda_l2 = 0.0, # lambda_l2 >= 0.0
  max_bin = 31L, # lo debo dejar fijo, no participa de la BO

  bagging_fraction = 1.0, # 0.0 < bagging_fraction <= 1.0
  pos_bagging_fraction = 1.0, # 0.0 < pos_bagging_fraction <= 1.0
  neg_bagging_fraction = 1.0, # 0.0 < neg_bagging_fraction <= 1.0
  is_unbalance = FALSE, #
  scale_pos_weight = 1.0, # scale_pos_weight > 0.0

  drop_rate = 0.1, # 0.0 < neg_bagging_fraction <= 1.0
  max_drop = 50, # <=0 means no limit
  skip_drop = 0.5, # 0.0 <= skip_drop <= 1.0

  extra_trees = FALSE,

  early_stopping = 0, #pone gustavo pasquini
  min_data_in_leaf = 0, #en tareahogar4 era 5000; en gustavo pasquini pone 0 y dice "fijo, esto es FUNDAMENTAL"
  feature_fraction = 0.50, #fijo
  feature_fraction_bynode = 1.0, #lo agrego gustavo en zulip para la competencia final
  learning_rate = 0.005, #en tareahogar4 era 0.02; en gustavo pasquini pone 0.005 y dice "fijo"

  num_iterations = 20000, #en tareahogar4 era 1200; en gustavo pasquini pone 20000 y dice "se modificara"
  num_leaves = 1024, #en tareahogar4 era 750; en gustavo pasquini pone 1024 y dice "se modificara"
  min_sum_hessian_in_leaf = 1e-06 #min_sum_hessian_in_leaf >= 0.0; en tareahogar4 era 0.001; en gustavo pasquini pone 1e-06 y dice "se modificara"
)

# [Anotación · líneas 948–999] Celdas del espacio de búsqueda de la bayesiana: quedan comentadas tanto la
#   versión con makeParamSet como la versión con ps() (num_iterations 64–4096, num_leaves 16–2048,
#   min_sum_hessian_in_leaf 1e-06–0,1, feature_fraction 0,1–0,9). Fija PARAM$hyperparametertuning$iteraciones en
#   50.
#%% celda 70 [texto]
Aqui **se definen los hiperparámetros de LightGBM que participan de la Bayesian Optimization**
- si es un `numero entero` debe ir  makeIntegerParam
- si es un `numero real (con decimales)` debe ir  makeNumericParam
- es muy importante leer cuales son un `lower y upper  permitidos y ademas razonables`

#%% celda 71 [código]
#%%R
# Aqui se cargan los bordes de los hiperparametros de la BO
# Original TareaHohar_04:

# Original TareaHohar_04: Utiliza funciones como makeParamSet y makeIntegerParam, que son características del ecosistema tradicional mlr (o el paquete ParamHelpers).
#PARAM$hypeparametertuning$hs <- makeParamSet(
#  makeIntegerParam("num_iterations", lower= 8L, upper= 5000L),
#  makeNumericParam("learning_rate", lower= 0.01, upper= 0.8),
#  makeNumericParam("feature_fraction", lower= 0.1, upper= 1.0),
#  makeIntegerParam("num_leaves", lower= 8L, upper= 5000L),
#  makeIntegerParam("min_data_in_leaf", lower= 1L, upper= 10000L)
#)

#%% celda 72 [texto]
## flag1: correr para bayesiana --aca empieza

#%% celda 73 [código]
# Aqui se cargan los bordes de los hiperparametros de la BO
# Gustavo Pasquini:

# Gustavo Pasquini: Usa ps(), p_int() y p_dbl(), que corresponden a la sintaxis más moderna del paquete paradox (el estándar actual en el ecosistema mlr3).
#PARAM$hypeparametertuning$hs <- ps(
#  num_iterations = p_int(lower = 64L,  upper = 4096L), #En TareaHohar_04 iba de 8L a 5000L
#  num_leaves = p_int(lower = 16L,  upper = 2048L), #En TareaHohar_04 iba de 8L a 5000L
#  min_sum_hessian_in_leaf = p_dbl( lower = 1e-06, upper = 0.1), #se introdujo en gustavo pasquini
#  feature_fraction = p_dbl(lower = 0.1, upper = 0.9))

  #learning_rate estaba en tareahogar_04
  #feature_fraction estaba en tareahogar_04
  #min_data_in_leaf estaba en tareahogar_04
# Es VITAL entender que se optimiza min_sum_hessian_in_leaf y que  min_data_in_leaf se deja fijo en CERO

#%% celda 74 [texto]
## flag1: correr para bayesiana --aca termina

#%% celda 75 [texto]
`iteraciones`: Define cuántas veces se evalúa la función objetivo en la Bayesian Optimization, es decir, **cuántas combinaciones de hiperparámetros se prueban en total**

**A mayor cantidad de hiperparámetros, se debe aumentar las iteraciones de la Bayesian Optimization**
- 30 es un valor muy tacaño, pero corre rápido
- Debería partir de 50, alcanzando los 100 si se dispone de tiempo

#%% celda 76 [código]
#%%R
PARAM$hyperparametertuning$iteraciones <- 50 # iteraciones bayesianas; En TareaHohar_04 eran 50, gustavo pasquini pone 10

# [Anotación · líneas 1001–1040] Define particionar: agrega al dataset una columna (por defecto fold) que
#   reparte las filas al azar en grupos según las proporciones de division, por separado dentro de cada valor de
#   la columna agrupa, con la semilla indicada (generador L'Ecuyer-CMRG).
#%% celda 77 [texto]
## Funciones

#%% celda 78 [texto]
`Función "particionar"`:

Agrega una columna fold al dataset que asigna a cada fila un grupo (1, 2, ...) según las proporciones que le pasás, estratificado: la proporción se respeta dentro de cada valor de agrupa (acá, cada clase de clase_ternaria).

Paso a paso, con division = c(70, 30):
- bloque: arma un vector con 70 unos y 30 dos (rep(1, 70) y rep(2, 30)), o sea, la "receta" del reparto.
- rep(bloque, ceiling(.N / length(bloque))): repite esa receta las veces necesarias para cubrir al menos .N filas del grupo.
- sample(...): mezcla al azar.
- [1:.N]: recorta al tamaño exacto del grupo.
- by = agrupa: repite todo por separado para BAJA+1, BAJA+2 y CONTINUA. Así cada clase queda dividida ~70/30 y no pasa que BAJA+2, que es rara, caiga toda en un fold.

El set.seed(seed, "L'Ecuyer-CMRG") hace el reparto reproducible.

Dónde se usa en tu notebook
- dataset_train con c(70, 30): **fold 1 es el 70 % de train (del que sale el undersampling) y fold 2 es el 30 % de validación**.
- drealidad con c(3, 7): **fold 1 es el 30 % "Public" y fold 2 el 70 % "Private"**, para simular el leaderboard de Kaggle.

Detalles a tener presentes
- Modifica el data.table por referencia (:=), por eso la llamás sin asignar el resultado (particionar(dataset_train, ...)) y la columna aparece igual.
- La proporción es aproximada, no exacta. Como recorta con [1:.N] después de mezclar, en grupos chicos (BAJA+2) puede desviarse un poco de 70/30. No es un problema práctico.

#%% celda 79 [código]
#%%R
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

# [Anotación · líneas 1042–1100] Define loguear: agrega una línea con fecha y hora y los valores del registro
#   recibido a un archivo de texto separado por tabulaciones (BO_log.txt), escribiendo antes el encabezado si el
#   archivo no existe.
#%% celda 80 [texto]
`Función logeuar`:

Es una bitácora que agrega una línea por evaluación de la BO a un archivo de texto separado por tabulaciones. Se llama desde Estimar_lightgbm, y xx (parámetros completos + iter + metrica) es lo que llega como preg.
- copy(preg): hace una copia para no modificar el objeto original.
- feature_contri: es un parámetro de LightGBM que puede ser un vector largo. Si existe, se queda con el primer elemento para no ensuciar el log. En tu caso no aparece, así que esa línea no hace nada.
- Si el archivo no existe, escribe primero los encabezados: fecha más los nombres de los campos (list.names viene del paquete rlist).
- Escribe la fila: la fecha y hora (20260927.232503) seguida de los valores. toString(reg) los une con ", " y el gsub cambia esas comas por tabulaciones.
- append = TRUE agrega al final sin pisar lo anterior, y verbose la imprime también en consola.

Por eso el script puede retomarse: el bloque de giter lee este archivo y toma max(iter) para continuar la numeración.

Detalles a tener presentes
- folder y ext no están definidos, pero solo se usan si arch es NA. Como siempre la llamás con "BO_log.txt", no hay problema.
- Depende de que las columnas no cambien entre corridas. Escribe el encabezado solo cuando el archivo no existe, y después agrega filas sin chequear que coincidan. Si cambiás algo de param_fijos o de los hiperparámetros optimizados y reusás el mismo BO_log.txt, las columnas se desalinean y el fread posterior te da datos corridos. Por eso te sugería cambiar el experimento o borrar el archivo antes de la corrida nueva.
- Usa ", " como separador de toString. Si algún valor contuviera esa secuencia (por ejemplo un parámetro de texto con coma y espacio), se partiría en dos columnas. Con tus parámetros, todos numéricos, lógicos o palabras simples, no pasa.
- Los valores no son NA-seguros. Si metrica llegara como NA (por ejemplo, si best_score fallara), se escribiría igual como NA y el setorder(-metrica) posterior lo mandaría al final sin avisar. En tu log no ocurre, pero es lo primero que miraría si un día hay resultados raros.

#%% celda 81 [código]
# ESTO LO INTRODUCE GUSTAVO PASQUINI
# Esta función actúa como una bitácora. Toma los resultados o parámetros de un proceso y los guarda en un archivo de texto para no perder el historial de lo que hizo el script.
# Entrada: Recibe un registro (preg), un nombre de archivo (arch) y un interruptor para imprimir en pantalla (verbose).
# Qué hace:
# - Captura la fecha y hora exacta (Sys.time()).
# - Limpia variables pesadas (se queda solo con el primer elemento de feature_contri para no ensuciar el log).
# - Si el archivo de texto no existe, lo crea y escribe los encabezados separados por tabulaciones (\t).
# - Escribe el nuevo registro al final del archivo (append=TRUE).
# Salida: No devuelve ningún objeto a R; su efecto ocurre en el disco duro (escribe un archivo de texto) y en la consola.


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

# [Anotación · líneas 1102–1132] Define realidad_inicializar: toma numero_de_cliente, foto_mes y
#   clase_ternaria del conjunto recibido y le agrega una partición 30/70 estratificada por clase (fold 1 y fold
#   2) con la semilla 600013, que representa las partes pública y privada.
#%% celda 82 [texto]
`Función realidad_inicializar`:

Prepara la "tabla de la realidad" para calcular la ganancia real de cada corte, simulando el leaderboard de Kaggle.
- Se queda con tres columnas de dfuture: numero_de_cliente, foto_mes y clase_ternaria. Esta última es la verdad, lo que realmente pasó con cada cliente.
- Le agrega una columna fold con particionar(..., division = c(3, 7), agrupa = "clase_ternaria"). Es el mismo reparto estratificado que vimos antes: 30 % de los clientes al fold 1 (el "Public") y 70 % al fold 2 (el "Private"), manteniendo esa proporción dentro de cada clase.
- Devuelve el resultado, que después usa realidad_evaluar para calcular ganancia total, Public y Private.

Como pfuture[, list(...)] genera una tabla nueva, particionar modifica esa copia y no toca dfuture.

Detalles a tener presentes
- pparam no se usa. La función recibe pparam pero adentro usa PARAM$semilla_kaggle directamente, la variable global. Funciona porque PARAM existe, pero lo prolijo sería seed = pparam$semilla_kaggle, o sacar el argumento.
- La semilla es la misma que la de train. semilla_kaggle y semilla_primigenia valen ambas 600013. No causa problemas porque se aplican a datasets distintos, pero si querés que el Public/Private sea independiente de tu semilla de trabajo, podés ponerles valores diferentes.
- El reparto es una simulación. Es una partición aleatoria estratificada que replica la lógica de Kaggle (30/70), pero no es la partición real de la competencia. Por eso tus números de Public y Private sirven para ver estabilidad y no para predecir el puntaje exacto que te dará Kaggle.

#%% celda 83 [código]
#%%R
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

# [Anotación · líneas 1134–1176] Define realidad_evaluar: une la columna Predicted a la tabla de realidad y
#   calcula la ganancia de los clientes con Predicted igual a 1 (1.072.500 por cada BAJA+2 y -27.500 por
#   cualquier otro) para el total, para el fold 1 dividido por 0,3 y para el fold 2 dividido por 0,7.
#%% celda 84 [texto]
`Función realidad_evaluar`:

Calcula la ganancia real de un corte, dada una columna Predicted (1 = enviar el estímulo, 0 = no).
- Pega la predicción a la realidad. El prealidad[pprediccion, on = ..., predicted := i.Predicted] es un join por numero_de_cliente y foto_mes que agrega la columna predicted a drealidad sin copiarla.
- Cuenta clientes por combinación de fold, predicted y clase_ternaria, en tbl.
- Calcula la ganancia solo sobre los clientes con predicted == 1: cada BAJA+2 suma +1.072.500 y cualquier otro cliente (CONTINUA o BAJA+1) resta 27.500, que es el costo del estímulo.
- Devuelve tres números:
1. total: la ganancia de todos los clientes, sin escalar.
2. public: la ganancia del fold 1 (30 %) dividida por 0,3, o sea extrapolada a la población completa.
3. private: la ganancia del fold 2 (70 %) dividida por 0,7, extrapolada igual.
- Borra predicted para dejar drealidad limpia para la próxima llamada del loop.

El escalado es lo que permite comparar Public y Private con total en la misma escala. Sin ese /0.3 y /0.7, Public valdría casi la mitad que Private solo por tener menos clientes.

Detalles a tener presentes
- Los BAJA+1 cuentan como costo, no como ganancia. Está bien y es la regla de la competencia: solo acertarle a un BAJA+2 paga.
- Modifica prealidad por referencia. Agrega y quita la columna predicted sobre el objeto original. Si la función fallara a mitad de camino, esa columna quedaría colgada. En la próxima llamada simplemente se pisa, así que no rompe nada, pero es bueno saberlo.
- Divide por 0,3 y 0,7 exactos, pero las particiones son aproximadas. Como vimos en particionar, la proporción real de cada fold puede desviarse apenas del 30/70, así que Public y Private tienen un pequeño error de escala. Es despreciable, y total no tiene ese problema.
- Los clientes sin predicción se ignoran. Si algún cliente de drealidad no está en pprediccion, queda con predicted = NA y el filtro predicted == 1L lo descarta. En tu caso no pasa, porque las dos tablas salen del mismo dfuture.
- Necesita clase completa. Si clase_ternaria fuera NA en algún cliente enviado, el ifelse daría NA y la suma también. Tus resultados numéricos muestran que ese no es el caso.

#%% celda 85 [código]
#%%R
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

# [Anotación · líneas 1178–1205] Crea la carpeta ~/buckets/b1/exp/HT4955-01, la fija como directorio de
#   trabajo y vuelve a leer el dataset con variables desde competencia_01_lag1y2_delta1y2_rank.csv.gz.
#%% celda 86 [texto]
## 2.2.4  Preprocesamiento

#%% celda 87 [código]
PARAM$experimento

#%% celda 88 [código]
#%%R
# carpeta de trabajo
# por favor cambiar numero de experimento si se cambia el loop principal
#setwd("/content/buckets/b1/exp")
#experimento <- "HT2900"
#dir.create(experimento, showWarnings=FALSE)
#setwd( paste0("/content/buckets/b1/exp/", experimento ))
#DIR_EXP <- "/Users/luciamontero/Desktop/Repositorios/Maestría Ciencia de Datos - UBA/2026/Segundo Cuatri/DMEyF/TP1-v1"
DIR_EXP <- path.expand("~/buckets/b1/exp")
experimento <- PARAM$experimento

dir.create(file.path(DIR_EXP, experimento), showWarnings = FALSE, recursive = TRUE)
setwd(file.path(DIR_EXP, experimento))

#%% celda 89 [código]
#%%R
# lectura del dataset
#DIR <- "/Users/luciamontero/Desktop/Repositorios/Maestría Ciencia de Datos - UBA/2026/Segundo Cuatri/DMEyF/TP1-v1"
DIR <- path.expand("~/buckets/b1/datasets")
#dataset <- fread(file.path(DIR, "competencia_01.csv.gz"))
dataset <- fread(file.path(DIR, "competencia_01_lag1y2_delta1y2_rank.csv.gz"))

# [Anotación · líneas 1207–1263] Arma dataset_train con 202103 y 202104, lo particiona 70/30 estratificado por
#   clase_ternaria (fold 1 y fold 2) con la semilla 600013, crea clase01 (1 para BAJA+1 y BAJA+2, 0 para
#   CONTINUA), una columna azar uniforme y marca training = 1 para las filas que pasan el undersampling (con
#   valor 1, todas).
#%% celda 90 [texto]
Defino **dataset_train** como **202104**

#%% celda 91 [código]
#%%R
dataset_train <- dataset[foto_mes %in% PARAM$train] #202104

#%% celda 92 [texto]
A continuación dividimos **dataset_train** en un grupo con el **70% de los registros** y otro con el 30%. La L en 100L solo le indica a R que trate al 100 como un número entero (integer). Agrupa = "clase_ternaria": Esto es fundamental; realiza un muestreo estratificado. Le indica a la función que **la división del 70/30 no se haga de forma 100% ciega, sino que se asegure de que ambas particiones mantengan exactamente la misma proporción de tu variable objetivo (clase_ternaria)**. Así evitas, por ejemplo, que por mala suerte todos los casos de "BAJA+2" queden en un solo grupo.

#%% celda 93 [código]
PARAM$training_pct

#%% celda 94 [código]
# ESTO LO AGREGA GUSTAVO PASQUINI
  particionar(dataset_train,
    division= c(PARAM$training_pct, 100L -PARAM$training_pct), #definimos mas arriba training_pct como 70
    agrupa= "clase_ternaria",
    seed= PARAM$semilla_primigenia # aqui se usa SU semilla
  )

#%% celda 95 [texto]
A continuación **se crea una nueva variable** objetivo **binaria clase01** (de ceros y unos). Básicamente, **transforma tu problema original de 3 clases (ternario) en un problema de 2 clases**. "¿El valor de esta fila es 'BAJA+2' o 'BAJA+1'?" 1L, 0L: Si la respuesta es Sí (es una BAJA), le asigna un 1 en la nueva columna.

#%% celda 96 [código]
# paso la clase a binaria que tome valores {0,1}  enteros
#  BAJA+1 y BAJA+2  son  1,   CONTINUA es 0
#  a partir de ahora ya NO puedo cortar  por prob(BAJA+2) > 1/40

dataset_train[,
  clase01 := ifelse(clase_ternaria %in% c("BAJA+2","BAJA+1"), 1L, 0L)
]

#%% celda 97 [texto]
Al dataset_train le agrega las columnas **azar** (nº aleatorio entre 0 y 1) y **training**, que inicialmente es 0 para todas las filas. Luego, **marca con training = 1 únicamente a las filas que van a entrenar el modelo de la BO**, dejando el resto (que ya estaban en 0 desde la línea anterior) sin tocar. Una fila se marca con training = 1 solo si cumple las tres cosas a la vez:
- foto_mes %in% PARAM$train → **está en el mes de entrenamiento (202104)**.
- fold == 1 → **pertenece al 70 %** (el fold de entrenamiento, no el de validación).
- (azar <= PARAM$trainingstrategy$undersampling | clase_ternaria %in% c("BAJA+1", "BAJA+2")) → si está en el 10% de los CONTINUA, o es BAJA+1 o BAJA+2. Se está implementando **undersampling (submuestreo) de la clase mayoritaria** (continua)

#%% celda 98 [código]
PARAM$trainingstrategy$undersampling

#%% celda 99 [código]
# defino los datos que forma parte del training
# aqui se hace el undersampling de los CONTINUA
# notar que para esto utilizo la SEGUNDA semilla

set.seed(PARAM$semilla_primigenia, kind = "L'Ecuyer-CMRG")
dataset_train[, azar := runif(nrow(dataset_train))]
dataset_train[, training := 0L]

dataset_train[
  #foto_mes %in%  PARAM$train &  fold==1 &
  foto_mes %in%  PARAM$train &
    (azar <= PARAM$trainingstrategy$undersampling | clase_ternaria %in% c("BAJA+1", "BAJA+2")),
  training := 1L
]

# [Anotación · líneas 1265–1286] Define campos_buenos: todas las columnas de dataset_train menos
#   clase_ternaria, clase01, fold, azar, training, training30, prob30, aporta y fold30. foto_mes y
#   numero_de_cliente quedan incluidas.
#%% celda 100 [texto]
Luego se seleccionan **con qué campos (columnas) va a aprender tu modelo**, filtrando y descartando aquellas que no deben usarse.

#%% celda 101 [código]
# ####################################################################
# >>> CAMBIO REGISTROS DUDOSOS (1/7) : campos_buenos excluye las columnas nuevas
# ####################################################################
# Antes solo se excluian clase_ternaria, clase01, fold, azar, training.
# Ahora tambien training30, prob30, aporta y fold30: si entraran como
# features habria leakage (prob30 es la salida de otro modelo) y el
# predict sobre dfuture fallaria porque ahi esas columnas no existen.
# foto_mes y numero_de_cliente SIGUEN entrando (a proposito).

campos_buenos <- setdiff(
  colnames(dataset_train),
  c("clase_ternaria", "clase01", "fold", "azar", "training",
    "training30", "prob30", "aporta", "fold30")   # <<< CAMBIO: agregadas las 4 ultimas
)

# ####################################################################
# <<< FIN CAMBIO
# ####################################################################

# [Anotación · líneas 1288–1365] Marca training30 = 1 en las filas del fold 2 (30%), arma con ellas un
#   lgb.Dataset con etiqueta clase01 y entrena modelo30 con parámetros fijos: metric average_precision,
#   learning_rate 0,005, feature_fraction 0,5, num_iterations 2180, num_leaves 30, min_sum_hessian_in_leaf
#   0,1141634103, min_data_in_leaf 0 y seed 600013.
#%% celda 102 [texto]
## ⚠️ CAMBIO — Excluyendo registros dudosos de training (parte BO)
Se entrena un `modelo30` con el **fold 2** (30%), se calcula `prob30` para todo el training y se eliminan del **fold 1** los `CONTINUA` con `prob30 > 0.5`.

**Solo afecta a la bayesiana.** Si no corrés la BO, lo que cambia tu modelo es la parte del *Final Training* (CAMBIO 7/7).

#%% celda 103 [código]
# ####################################################################
# >>> CAMBIO REGISTROS DUDOSOS (2/7) : modelo30 entrenado con el fold 2
# ####################################################################
# Paso 1: dataset de training del modelo30 (fold 2 = el 30%)
dataset_train[, training30 := 0L]

dataset_train[
  foto_mes %in%  PARAM$train &  fold==2 &
    (azar <= PARAM$trainingstrategy$undersampling | clase_ternaria %in% c("BAJA+1", "BAJA+2")),
  training30 := 1L
]

# uso campos_buenos (ya excluye training30/prob30/aporta) en vez de un
# campos_buenos30 aparte: asi dtrain30 y el predict usan las mismas columnas
dtrain30 <- lgb.Dataset(
  data= data.matrix(dataset_train[training30 == 1L, campos_buenos, with= FALSE]),
  label= dataset_train[training30 == 1L, clase01],
  free_raw_data= FALSE
)

# Paso 2: parametros fijos del modelo30
PARAM$lgbm$param_iniciales30 <-  list(
  boosting= "gbdt",
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

  num_iterations= 2180,
  num_leaves= 30,
  min_sum_hessian_in_leaf= 0.1141634103
)

# Paso 3: entreno el modelo30
modelo30 <- lgb.train(
  data= dtrain30,
  param= PARAM$lgbm$param_iniciales30
)

# ####################################################################
# <<< FIN CAMBIO
# ####################################################################

# [Anotación · líneas 1367–1416] Aplica modelo30 a todo dataset_train y guarda la probabilidad en prob30.
#   Marca aporta = 1 en las filas del fold 1 que son clase01 = 1 o CONTINUA con prob30 menor a 0,5, y redefine
#   training = 1 sólo para las filas del fold 1 con aporta = 1. Muestra los conteos y libera modelo30.
#%% celda 104 [código]
# ####################################################################
# >>> CAMBIO REGISTROS DUDOSOS (3/7) : prob30 sobre TODO el training de la BO
# ####################################################################
# Paso 4: aplico el modelo30 a TODO el dataset de training (202103 y 202104)
prediccion30 <- predict(
  modelo30,
  data.matrix(dataset_train[, campos_buenos, with= FALSE])
)

dataset_train[, prob30 := prediccion30 ]

# control: cuantos CONTINUA del fold 1 se van a eliminar (dudoso == TRUE)
dataset_train[fold == 1L, .N, list(clase_ternaria, dudoso = prob30 > 0.5)][order(clase_ternaria)]

# ####################################################################
# <<< FIN CAMBIO
# ####################################################################

#%% celda 105 [código]
# ####################################################################
# >>> CAMBIO REGISTROS DUDOSOS (4/7) : aporta + training (reemplaza la definicion de la celda 97)
# ####################################################################
# Elimino del training los CONTINUA con prob30 > 0.5.
# OJO: ahora SI se filtra fold == 1. En el fold 2 prob30 es in-sample
# (el modelo30 se entreno ahi), asi que no sirve para limpiarlo.

dataset_train[, aporta := 0L ]
dataset_train[ fold==1L &
  ( clase01==1L | (clase01==0L & prob30 <0.5)),
    aporta := 1L
  ]

# defino los datos que forman parte del training (pisa lo de la celda 97)
# azar ya existe (celda 97, misma semilla) -> no hace falta regenerarlo
dataset_train[, training := 0L]

dataset_train[
  foto_mes %in%  PARAM$train &  fold==1 & aporta==1L &
    (azar <= PARAM$trainingstrategy$undersampling | clase_ternaria %in% c("BAJA+1", "BAJA+2")),
  training := 1L
]

dataset_train[, .N, list(training, clase_ternaria)][order(training, clase_ternaria)]

rm(dtrain30, modelo30, prediccion30); gc(verbose= FALSE)

# ####################################################################
# <<< FIN CAMBIO
# ####################################################################

# [Anotación · líneas 1418–1486] Celdas de texto sobre data drifting. Pasa a NA ccajas_depositos en 202105
#   sobre el dataset completo. Quedan comentadas la exclusión de cprestamos_personales y mprestamos_personales y
#   el reemplazo de ceros por NA en las predictoras. Arma dataset_validate con 202106 y le crea clase01.
#%% celda 106 [texto]
## 2.2.4.1  Salsa Magica (dedicada a Laura Pasquini)

**El unico EDA que tiene realmente sentido, en este caso, es comparar la distribución de cada variable del mes donde se entrena 202104 y el mes donde se va a aplicar el modelo 202106, buscando Data Drifting.**

Aun con los reales datos del futuro, donde no se tiene la clase, SIEMPRE se puede analizar el Data Drifting.

Para las variables con distribuciones distintas se puede hacer:
* Transformar la variable para hacerla homogenea entre los dos periodos
* Eliminarla (es lo simple, que se eligió hacer en este caso)

#%% celda 107 [texto]
En esa exploracion gráfica del Data Drifting, **se vio que estas variables cambian de distribucion entre 202104 y 202106, y se decidió brutalmente eliminarlas**
- `cprestamos_personales`
- `mprestamos_personales`


Más adelantes, se utilizarán técnicas más inclusivas, y se preservaran dichas variables, transformadas.

#%% celda 108 [código]
# Borro los datos envenenados de junio
dataset[foto_mes == 202105, 
        `:=`(ccajas_depositos = NA)]

#%% celda 109 [texto]
### sigue acá el código

#%% celda 110 [código]
campos_buenos

#%% celda 111 [código]
#campos_buenos <- setdiff( campos_buenos, c("cprestamos_personales", "mprestamos_personales") )

# update: cambio esta linea para q no entren sus lags ni deltas tampoco
# update competencia supuestamente no hay q correr esto
#campos_buenos <- campos_buenos[!grepl("^[cm]prestamos_personales", campos_buenos)]

#%% celda 112 [código]
# Reemplazar 0 por NA solamente en las variables predictoras
# ... PERO excluyendo las binarias / de transicion, donde el 0 es un valor
# informativo (flag "no paso", o estado "0->0" que siguio sano), no ausencia.
# Mandarlas a NA fusiona el valor sano/mayoritario con el faltante y degrada
# justo las features nuevas.

# CAMBIO: lo aplico tambien a dataset_train, asi la BO optimiza con la MISMA
# condicion (0 -> NA) con la que despues se entrena y predice el modelo final.
# Debe correr ANTES de crear dtrain/dvalidate.

# CAMBIO: columnas que NO deben recibir 0->NA
#cols_flags <- grep("(_trans$|_apaga$|_prende$|_empeora$|_entra_mora$|^n_canales_apagados$)",
#                   campos_buenos, value = TRUE)
#cols_cero_na <- setdiff(campos_buenos, cols_flags)
#cat("0->NA aplicado a", length(cols_cero_na), "cols; excluidas (flags/trans):", length(cols_flags), "\n")

#dataset[, (cols_cero_na) := lapply(.SD, function(x) {
#  x[x == 0] <- NA
#  x
#}), .SDcols = cols_cero_na]

#dataset_train[, (cols_cero_na) := lapply(.SD, function(x) {
#  x[x == 0] <- NA
#  x
#}), .SDcols = cols_cero_na]

#%% celda 113 [código]
# Esos son los clientes con los que se evalúa cada modelo de la bayesiana, 202106
dataset_validate <- dataset[foto_mes %in% PARAM$validate]

dataset_validate[, clase01 := ifelse(clase_ternaria %in% c("BAJA+1","BAJA+2"), 1L, 0L)]

# [Anotación · líneas 1488–1538] Celdas de texto que describen la optimización bayesiana. Inicializa el
#   contador giter en 0 o, si ya existe BO_log.txt en la carpeta del experimento, en la mayor iteración
#   registrada.
#%% celda 114 [texto]
## 2.2.5 Configuracion Bayesian Optimization

#%% celda 115 [texto]
**RESUMEN**

Usa **average_precision (AP)** calculada sobre el set de validación. No usa ganancia en pesos ni AUC (el AUC era la versión original).
- Qué mide el AP: El modelo ordena a los clientes de mayor a menor probabilidad de baja. El AP resume qué tan concentradas quedan las bajas reales arriba de ese ranking. Va de 0 a 1, y más alto es mejor. Tus valores (~0,10 a 0,12) son bajos en términos absolutos porque las bajas son muy raras, y por eso conviene compararlos entre sí y no contra 1.
- El modelo le pone una probabilidad de baja a cada cliente y los ordena de mayor a menor. Un buen modelo deja a los que realmente se dan de baja arriba de todo en esa lista. El AP mide qué tan arriba quedaron.

Cómo funciona la BO: Pensala como buscar la mejor receta cuando cada prueba es cara: hornear tarda 3 minutos y tenés que ajustar 3 perillas (num_iterations, num_leaves, min_sum_hessian_in_leaf). PARAM$hypeparametertuning$hs

La BO ve solo esto:
- **Entrada**: 3 números (los valores de esas perillas). PARAM$hypeparametertuning$hs
- **Salida**: 1 número (metrica, el AP).

Todo lo demás (los otros parámetros fijos, los datos, el undersampling) queda dentro de la caja negra.

El ciclo:

Diseño inicial. Prueba combinaciones repartidas por el espacio, sin criterio. El surrogate aprende. Con esos pares (perillas → AP) ajusta un modelo barato, el Kriging (regr.km), que dibuja una superficie estimada del AP para todas las combinaciones, incluso las no probadas, y además dice cuánta incertidumbre tiene en cada zona.
La acquisition function elige el próximo punto. Con Expected Improvement busca dónde es más probable mejorar el mejor AP hasta ahora. Equilibra dos ganas: probar cerca de lo que ya funcionó (explotar) y probar zonas inexploradas donde podría haber algo mejor (explorar).
Evalúa de verdad ese punto: entrena un LightGBM con esas perillas y mide el AP.
Agrega el resultado y repite desde el paso 2, con un surrogate más informado.

**Cuando llega a n_evals, se queda con la combinación de mayor AP**. La ventaja frente a probar al azar es que cada evaluación cara se usa para decidir mejor la siguiente, y con pocas pruebas eso importa.

Qué no hace la BO
- **No conoce la ganancia ni el corte de envíos**. Eso lo evaluás vos después, con el modelo final y realidad_evaluar.
- No entrena el modelo final. **Solo entrega los mejores hiperparámetros. Después reentrenás con todos los datos de 202104, sin undersampling**.
- **No optimiza learning_rate, feature_fraction, etc. Esos están fijos en param_fijos.**

#%% celda 116 [texto]
------------------

#%% celda 117 [texto]
Inicializa el contador `giter`, que numera las evaluaciones de la BO y se escribe en la columna iter del log.

giter <- 0: arranca en cero.
if (file.exists("BO_log.txt")): si ya existe un log de una corrida anterior en la carpeta de trabajo, lo lee.
giter <- tb_BO[, max(iter)]: pone el contador en el último número de iteración registrado. Si el log llegó hasta 12, giter vale 12 y la próxima evaluación se numera 13.

Estimar_lightgbm hace giter <<- giter + 1 en cada evaluación, y ese valor es el que va al log. Así la numeración es continua aunque el script se corte y se vuelva a correr.

#%% celda 118 [código]
giter <- 0

if( file.exists("BO_log.txt") ){
  tb_BO <- fread("BO_log.txt")
  giter <- tb_BO[, max(iter)]
}

# [Anotación · líneas 1540–1601] Queda comentada la función que medía AUC con lgb.cv de 5 folds. Define
#   Estimar_lightgbm, la función objetivo de la bayesiana: combina los parámetros fijos con los recibidos,
#   entrena un LightGBM con dtrain validando en dvalidate, toma modelo$best_score como métrica, registra la
#   evaluación con loguear en BO_log.txt y devuelve la métrica.
#%% celda 119 [código]
# ESTE ERA EL ORIGINAL DE TAREA HOGAR 04, QUE SE CAMBIÓ EN GUSTAVO PASQUINI XQ YA NO SE OPTIMIZA AUC
#%%R
# En el argumento x llegan los parámetros de la bayesiana
#  devuelve la AUC en cross validation del modelo entrenado

#EstimarGanancia_AUC_lightgbm <- function(x) {

  # x pisa (o agrega) a param_fijos
  #param_completo <- modifyList(PARAM$lgbm$param_fijos, x)

  # entreno LightGBM
  #modelocv <- lgb.cv(
    #data= dtrain,
    #nfold= PARAM$hyperparametertuning$xval_folds,
    #stratified= TRUE,
    #param= param_completo
  #)

  # obtengo la ganancia
  #AUC <- modelocv$best_score

  # hago espacio en la memoria
  #rm(modelocv)
  #gc(full= TRUE, verbose= FALSE)

  #message(format(Sys.time(), "%a %b %d %X %Y"), " AUC ", AUC)

  #return(AUC)
#}

#%% celda 120 [texto]
Es la función que la BO llama en cada evaluación: recibe una combinación de hiperparámetros, entrena un modelo y devuelve qué tan bueno fue. 

#%% celda 121 [código]
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

# [Anotación · líneas 1603–1694] Arma dtrain con las filas training = 1 (fold 1 de 202103 y 202104 sin los
#   CONTINUA dudosos), etiqueta clase01 y peso 0,25 para BAJA+1 y 1,0 para el resto. Arma dvalidate con todo
#   202106, con la misma etiqueta y los mismos pesos. Las versiones anteriores de ambos objetos quedan
#   comentadas.
#%% celda 122 [texto]
**la bayesiana se entrena con dtrain y se testea con dvalidate** optimizando la función Estimar_lightgbm

#%% celda 123 [texto]
**dtrain usa las filas con training == 1L**:
- 202104
- clase01 (problema binario)
- está en el fold1, o sea en el 70% destinado a entrenar Y QUE ADEMAS sobrevive al undersampling (o es BAJA+1 o BAJA+2 (se conservan todos), o es CONTINUA y le tocó un azar <= 0.1 (se conserva el 10 %)) --> es mucho menor al 70%


**dvalidate usa las filas con training == 0L**:
- 202104
- clase01
- 30% destinado a evaluar MÁS todos los continua que no sobreviven al undersampling --> es mucho mayor al 30% 

------
1. Se entrena con undersampling para que la construccion del LightGBM sea rapida
2. Entrenar es muchisimo mas costoso que validar ! porque en cada split debo buscar en todas las <columnas, valores> cual es el mejor split
3. Para entrenar es critico tener pocos registros, para validar no importa tanto la cantidad de registros

Formas de lograr que la optmiizacion de hiperparametros sea rapida:
- No usar 5-fold cross validation y solo utilizar <train, validate>
- Reducir el tamano de training haciendo undersampling de clase mayoritaria
- Hacer algo magico que NO haga falta la Bayesian Optimization en lo absoluto, o que solo hagan falta unas pocas iteraciones

#%% celda 124 [código]
# dejo los datos de training en el formato que necesita LightGBM
#dtrain <- lgb.Dataset(
#  data= data.matrix(dataset_train[training == 1L, campos_buenos, with= FALSE]),
#  label= dataset_train[training == 1L, clase01],
#  free_raw_data= FALSE
#)

#nrow(dtrain)
#ncol(dtrain)

#%% celda 125 [código]
# ####################################################################
# >>> CAMBIO REGISTROS DUDOSOS (5/7) : dtrain ahora usa el training ya limpio
# ####################################################################
# El codigo es el mismo de antes: 'training == 1L' ya incluye fold == 1
# y aporta == 1 (se definio en la celda del CAMBIO 4/7).
# Solo importa si corres la bayesiana: sin BO, dtrain no se usa.

# LE AGREGO PESOS PARA DISTINGUIR LOS BAJA+2
dtrain <- lgb.Dataset(
  data= data.matrix(dataset_train[training == 1L, campos_buenos, with= FALSE]),
  label= dataset_train[training == 1L, clase01],
  weight= dataset_train[training == 1L, ifelse(clase_ternaria == "BAJA+1", 0.25, 1.0)],
  free_raw_data= FALSE
)

nrow(dtrain)   # <<< CAMBIO: control, deberia ser ~70% del training menos los dudosos
ncol(dtrain)

# ####################################################################
# <<< FIN CAMBIO
# ####################################################################

#%% celda 126 [código]
# datos de validation en el formato que necesita LightGBM
#dvalidate <- lgb.Dataset(
#  data= data.matrix(dataset_train[training == 0L, campos_buenos, with= FALSE]),
#  label= dataset_train[training == 0L, clase01],
#  free_raw_data= FALSE
#)

#nrow(dvalidate)
#ncol(dvalidate)

#%% celda 127 [código]
  # LE AGREGO PESOS PARA DISTINGUIR LOS BAJA+2

  # datos de validation en el formato que necesita LightGBM
  #dvalidate <- lgb.Dataset(
  #  data= data.matrix(dataset_train[training == 0L, campos_buenos, with= FALSE]),
  #  label= dataset_train[training == 0L, clase01],
  #  weight= dataset_train[training == 0L, ifelse(clase_ternaria == "BAJA+1", 0.25, 1.0)],
  #  free_raw_data= FALSE
  #)

#%% celda 128 [código]
  # LE AGREGO PESOS PARA DISTINGUIR LOS BAJA+2
  # version nueva: usa dataset_validate que es el de la bayesiana, 202106

  # datos de validation en el formato que necesita LightGBM
  dvalidate <- lgb.Dataset(
    data= data.matrix(dataset_validate[, campos_buenos, with= FALSE]),
    label= dataset_validate[, clase01],
    weight= dataset_validate[, ifelse(clase_ternaria == "BAJA+1", 0.25, 1.0)],
    free_raw_data= FALSE
  )

# [Anotación · líneas 1696–1795] Configuración de la optimización bayesiana, enteramente comentada en este
#   notebook: tanto la versión con mlrMBO como la versión con mlr3mbo (objetivo, instancia con terminador por
#   cantidad de evaluaciones, surrogate regr.km, expected improvement y optimizador mbo).
#%% celda 129 [texto]
### original onfiguracion de la Bayesian Optimization en tarea hogar 04

#%% celda 130 [código]
# ESTA ERA LA ORIGINAL DE TAREA HOGAR 04
#%%R
# Aqui comienza la configuracion de la Bayesian Optimization

# en este archivo quedan la evolucion binaria de la BO
#kbayesiana <- "bayesiana.RDATA"

#funcion_optimizar <- EstimarGanancia_AUC_lightgbm # la funcion que voy a maximizar

#configureMlr(show.learner.output= FALSE)

# configuro la busqueda bayesiana,  los hiperparametros que se van a optimizar
# por favor, no desesperarse por lo complejo

#obj.fun <- makeSingleObjectiveFunction(
#  fn= funcion_optimizar, # la funcion que voy a maximizar
#  minimize= FALSE, # estoy Maximizando la ganancia
#  noisy= TRUE,
#  par.set= PARAM$hypeparametertuning$hs, # definido al comienzo del programa
#  has.simple.signature= FALSE # paso los parametros en una lista
#)

# cada 600 segundos guardo el resultado intermedio
#ctrl <- makeMBOControl(
#  save.on.disk.at.time= 600, # se graba cada 600 segundos
#  save.file.path= kbayesiana
#) # se graba cada 600 segundos

# indico la cantidad de iteraciones que va a tener la Bayesian Optimization
#ctrl <- setMBOControlTermination(
#  ctrl,
#  iters= PARAM$hyperparametertuning$iteraciones
#) # cantidad de iteraciones

# defino el método estandar para la creacion de los puntos iniciales,
# los "No Inteligentes"
#ctrl <- setMBOControlInfill(ctrl, crit= makeMBOInfillCritEI())

# establezco la funcion que busca el maximo
#surr.km <- makeLearner(
#  "regr.km",
#  predict.type= "se",
#  covtype= "matern3_2",
#  control= list(trace= TRUE)
#)

#%% celda 131 [texto]
### cambio en gustavo pasquini configuracion de la Bayesian Optimization en tarea hogar 04

#%% celda 132 [texto]
## flag2: correr para bayesiana --aca empieza

#%% celda 133 [código]
# Aqui comienza la configuracion de la Bayesian Optimization

# en este archivo quedan la evolucion binaria de la BO
#kbayesiana <- "bayesiana.RDATA"

#funcion_optimizar <- Estimar_lightgbm # la funcion que voy a maximizar

#objective <- ObjectiveRFun$new(
#  fun= funcion_optimizar,
#  domain= PARAM$hypeparametertuning$hs,
#  codomain= ps(metrica = p_dbl(tags="maximize")),
#  id= "BO_lightgbm"
#)


#instance <- OptimInstanceBatchSingleCrit$new(
#  objective= objective,
#  terminator=  trm("evals", n_evals = PARAM$hyperparametertuning$iteraciones)
#)


#surrogate <- srlrn(lrn("regr.km",
#  optim.method = "BFGS",
#  nugget.estim = TRUE,
#  control= list(trace = FALSE)))

#acq_function  <- acqf("ei")                 # expected improvement

#acq_optimizer  <- acqo(
#  optimizer  = opt("random_search", batch_size= 1000),
#  terminator = trm("evals", n_evals= 1000)
#)

#optimizer <- opt("mbo",
#  loop_function = bayesopt_ego,
#  surrogate= surrogate,
#  acq_function= acq_function,
#  acq_optimizer= acq_optimizer
#)

#%% celda 134 [texto]
## flag2: correr para bayesiana --aca termina

# [Anotación · líneas 1796–1925] Corrida de la bayesiana, lectura del historial de evaluaciones y gráficos con
#   plotly y ggplot: todo comentado en este notebook.
#%% celda 135 [texto]
## 2.2.6 Corrida Bayesian Optimization

#%% celda 136 [código]
# ESTE ERA EL ORIGINAL DE TAREA HOGAR 04
#%%R
# inicio la optimizacion bayesiana, retomando si ya existe
# es la celda mas lenta de todo el notebook

#if (!file.exists(kbayesiana)) {
#  bayesiana_salida <- mbo(obj.fun, learner= surr.km, control= ctrl)
#} else {
#  bayesiana_salida <- mboContinue(kbayesiana) # retomo en caso que ya exista
#}

#%% celda 137 [texto]
## flag3: correr para bayesiana --aca empieza

#%% celda 138 [código]
#inicio <- Sys.time()

#%% celda 139 [código]
# VERSION GUSTAVO PASQUINI
#bayesiana_salida <- optimizer$optimize(instance)

#%% celda 140 [código]
#fin <- Sys.time()
#tiempo_total <- fin - inicio
#print(tiempo_total)

#%% celda 141 [texto]
Luego de este punto, **en la carpeta del experimento quedó el archivo BO_log.txt que posee todas las iteraciones de la Bayesian Optimization**

#%% celda 142 [texto]
1. Verás una columna por cada hiperparámetro que estabas optimizando.
2. La columna de tu métrica objetivo (El "Output"): Verás una columna con el nombre exacto de la métrica que le pediste al optimizador que maximizara o minimizara.
3. Las columnas técnicas y de metadatos (Internas de mlr3/bbotk): Estas columnas las genera automáticamente el ecosistema para llevar el control interno. Las más comunes que te devolverá son x_domain (lista interna con los hiperparámetros transformados), timestamp, batch_nr, uhash, warnings, resample_result (Una columna muy poderosa que guarda el objeto completo del remuestreo (ej. el Cross-Validation). Si quisieras, desde aquí podrías extraer las predicciones exactas que hizo el modelo en esa iteración), etc

#%% celda 143 [código]
## ESTE ERA EL ORIGINAL DE TAREA HOGAR 04 (DEJAR COMENTADO)
#%%R
#tb_bayesiana <- as.data.table(bayesiana_salida$opt.path)
#colnames( tb_bayesiana)

# RENOVADO PARA GUSTAVO PASQUINI (SI CORRER ESTO)
# Extraer el historial de todas las pruebas realizadas
#tb_bayesiana <- instance$archive$data
#colnames(tb_bayesiana)

#%% celda 144 [texto]
### Gráficos Bayesiana

#%% celda 145 [código]
#if (!require("plotly")) install.packages("plotly")
#library(plotly)

#%% celda 146 [código]
#  plot_ly(
#    tb_bayesiana,
#    x = ~num_iterations,
#    y = ~num_leaves,
#    z = ~min_sum_hessian_in_leaf,
#    color = ~metrica,
#    colors = c("blue", "red"),
#    type = "scatter3d",
#    mode = "markers",
#    marker = list(size = 6)
#  ) %>%
#    layout(title = "Bayesian Optimization - LightGBM",
#           scene = list(
#             xaxis = list(title = "num_iterations"),
#             yaxis = list(title = "num_leaves"),
#             zaxis = list(title = "min_sum_hessian_in_leaf")
#           ))

#%% celda 147 [código]
#  plot_ly(
#    tb_bayesiana,
#    type = "parcoords",
#    line = list(color = ~metrica,
#                colorscale = list(c(0, "blue"), c(1, "red")),
#                showscale = TRUE),
#    dimensions = list(
#      list(label = "num_iterations", values = ~num_iterations),
#      list(label = "num_leaves", values = ~num_leaves),
#      list(label = "min_sum_hessian_in_leaf", values = ~min_sum_hessian_in_leaf),
#      list(label = "metrica", values = ~metrica)
#    )
#  )

#%% celda 148 [código]
#if (!require("patchwork")) install.packages("patchwork")
#library(patchwork)

#%% celda 149 [código]
# p1 <- ggplot(tb_bayesiana, aes(num_iterations, num_leaves, color = metrica)) +
#   geom_point(size = 3) + scale_color_gradient(low = "blue", high = "red") +
#   theme_minimal()

# p2 <- ggplot(tb_bayesiana, aes(num_iterations, min_sum_hessian_in_leaf, color = metrica)) +
#   geom_point(size = 3) + scale_color_gradient(low = "blue", high = "red") +
#   theme_minimal()

# p3 <- ggplot(tb_bayesiana, aes(num_leaves, min_sum_hessian_in_leaf, color = metrica)) +
#   geom_point(size = 3) + scale_color_gradient(low = "blue", high = "red") +
#   theme_minimal()

# p1 / p2 / p3   # con patchwork, apilados

#%% celda 150 [código]
#  library(data.table)
#  tb_long <- melt(tb_bayesiana, id.vars = "metrica",
#                  measure.vars = c("num_iterations", "num_leaves", "min_sum_hessian_in_leaf"))

#  ggplot(tb_long, aes(value, metrica)) +
#    geom_point(alpha = 0.6) +
#    geom_smooth(method = "loess", se = FALSE, color = "red") +
#    facet_wrap(~variable, scales = "free_x") +
#    theme_minimal()

#%% celda 151 [texto]
### Sigue el código

#%% celda 152 [código]
#Si en lugar de ver todo el historial de iteraciones quisieras ver únicamente cuál fue la combinación ganadora (la mejor):
#instance$result

#%% celda 153 [texto]
## flag2: correr para bayesiana --aca termina

# [Anotación · líneas 1926–1953] Carga a mano los hiperparámetros: num_iterations 3606, num_leaves 1443,
#   min_sum_hessian_in_leaf 0,0874518118416699 y feature_fraction 0,120189655432349, con métrica
#   0,913479658101473. Queda comentada la toma del resultado desde instance. Según el README, esos valores son
#   la fila de mayor métrica de la bayesiana del experimento j4953.
#%% celda 154 [texto]
# IMPORTANTE, HARDCODEO ESTO PARA NO CORRER TODA LA BAYESIANA

#%% celda 155 [código]
PARAM$out$lgbm$mejores_hiperparametros <- list(
  num_iterations          = 3606,
  num_leaves              = 1443,
  min_sum_hessian_in_leaf = 0.0874518118416699,
  feature_fraction        = 0.120189655432349
)

PARAM$out$lgbm$y <- 0.913479658101473

#%% celda 156 [texto]
## flag4: correr para bayesiana --aca empieza

#%% celda 157 [código]
#PARAM$out$lgbm$mejores_hiperparametros <- instance$result_x_domain
#PARAM$out$lgbm$y <- instance$result_y

#%% celda 158 [texto]
## flag4: correr para bayesiana --aca termina

#%% celda 159 [código]
PARAM$out$lgbm$mejores_hiperparametros

#%% celda 160 [código]
PARAM$out$lgbm$y

# [Anotación · líneas 1955–2075] Celdas comentadas de versiones anteriores (guardado de la bayesiana con
#   mlrMBO, PARAM.yml). Fija como directorio de trabajo ~/buckets/b1/exp/HT4955-01. Quedan comentadas las
#   lecturas de BO_log.txt para tomar la fila de mayor métrica. Muestra los hiperparámetros cargados.
#%% celda 161 [código]
## ESTE ERA EL ORIGINAL DE TAREA HOGAR 04
# %%R
# almaceno los resultados de la Bayesian Optimization
# y capturo los mejores hiperparametros encontrados

#tb_bayesiana <- as.data.table(bayesiana_salida$opt.path)

#tb_bayesiana[, iter := .I]

# ordeno en forma descendente por AUC = y
#setorder(tb_bayesiana, -y)

# grabo para eventualmente poder utilizarlos en OTRA corrida
#fwrite( tb_bayesiana,
#  file= "BO_log.txt",
#  sep= "\t"
#)

# los mejores hiperparámetros son los que quedaron en el registro 1 de la tabla
#PARAM$out$lgbm$mejores_hiperparametros <- tb_bayesiana[
#  1, # el primero es el de mejor AUC
#  setdiff(colnames(tb_bayesiana),
#    c("y","dob","eol","error.message","exec.time","ei","error.model",
#      "train.time","prop.type","propose.time","se","mean","iter")),
#  with= FALSE
#]


#PARAM$out$lgbm$y <- tb_bayesiana[1, y]

#%% celda 162 [código]
#%%R
#write_yaml( PARAM, file="PARAM.yml")

#%% celda 163 [código]
#%%R
#print(PARAM$out$lgbm$mejores_hiperparametros)
#print(PARAM$out$lgbm$y)

#%% celda 164 [texto]
## 2.3  Producción

#%% celda 165 [texto]
## Final Training
Construyo el modelo final, que es uno solo, no hace ningun tipo de particion < training, validation, testing>]

#%% celda 166 [código]
# original tarea 04
#setwd("/content/buckets/b1/exp")
#experimento <- paste0("exp", PARAM$experimento)
#dir.create(experimento, showWarnings= FALSE)
#setwd( paste0("/content/buckets/b1/exp/", experimento ))

#%% celda 167 [código]
# gustavo pasquini
#setwd("/content/buckets/b1/exp")
#dir.create(PARAM$experimento, showWarnings= FALSE)
#setwd( paste0("/content/buckets/b1/exp/", PARAM$experimento ))

#%% celda 168 [código]
#%%R
# Carpeta de trabajo base
#DIR_EXP <- "/Users/luciamontero/Desktop/Repositorios/Maestría Ciencia de Datos - UBA/2026/Segundo Cuatri/DMEyF/TP1-v1"
DIR_EXP <- path.expand("~/buckets/b1/exp")
# Identificador del experimento
#experimento <- paste0("exp", PARAM$experimento)
experimento <- PARAM$experimento

# Creación de la carpeta del experimento
#dir.create(file.path(DIR_EXP, experimento), showWarnings = FALSE, recursive = TRUE)

# Definición del directorio de trabajo activo
setwd(file.path(DIR_EXP, experimento))

#%% celda 169 [texto]
Cargo los **mejores hiperparametros**, que son los de mayor metrica.

#%% celda 170 [código]
 # cargo los mejores hiperparametros, que son los de mayor metrica
 
##DIR <- "/Users/luciamontero/Desktop/Repositorios/Maestría Ciencia de Datos - UBA/2026/Segundo Cuatri/DMEyF/TP1-v1/HT4940-01"
#DIR_EXP <- "/Users/luciamontero/Desktop/Repositorios/Maestría Ciencia de Datos - UBA/2026/Segundo Cuatri/DMEyF/TP1-v1"
#experimento <- PARAM$experimento
#setwd(file.path(DIR_EXP, experimento))

# Unimos la ruta y el nombre del archivo con file.path()
#tb_bayesiana <- fread(file.path(DIR_EXP, "BO_log.txt"))

#setorder(tb_bayesiana, -metrica)

# Seleccionamos únicamente las columnas que son hiperparámetros
#cols_hiper <- c("num_iterations", "num_leaves", "min_sum_hessian_in_leaf")

# Extraemos la mejor fila y la convertimos en lista para el modelo
#PARAM$out$lgbm$mejores_hiperparametros <- as.list(tb_bayesiana[1, cols_hiper, with = FALSE])

#%% celda 171 [texto]
## flag5: correr para bayesiana --aca empieza

#%% celda 172 [código]
#DIR_EXP <- "/Users/luciamontero/Desktop/Repositorios/Maestría Ciencia de Datos - UBA/2026/Segundo Cuatri/DMEyF/TP1-v1"
#DIR_EXP <- path.expand("~/buckets/b1/exp")
#experimento <- PARAM$experimento
#setwd(file.path(DIR_EXP, experimento))

#tb_bayesiana <- fread("BO_log.txt")

#setorder(tb_bayesiana, -metrica)

# Seleccionamos únicamente las columnas que son hiperparámetros
#cols_hiper <- c("num_iterations", "num_leaves", "min_sum_hessian_in_leaf","feature_fraction")

# Extraemos la mejor fila y la convertimos en lista para el modelo
#PARAM$out$lgbm$mejores_hiperparametros <- as.list(tb_bayesiana[1, cols_hiper, with = FALSE])

#%% celda 173 [texto]
## flag5: correr para bayesiana --aca termina

#%% celda 174 [código]
PARAM$out$lgbm$mejores_hiperparametros

# [Anotación · líneas 2077–2103] Crea clase01 en el dataset completo y arma dataset_train con los meses 202103
#   a 202106, mostrando la cantidad de filas por mes y clase.
#%% celda 175 [texto]
## Final Training Dataset

Aqui esta la gran decision de **en qué meses hago el Final Training**


Debo utilizar los mejores hiperparámetros que encontré en la  optimización bayesiana

#%% celda 176 [código]
# clase01
# Crea la variable a predecir, clase01, en el dataset completo. Es la misma transformación que hicimos antes para el entrenamiento de la BO, pero ahora sobre dataset.
dataset[, clase01 := ifelse(clase_ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)]

# Para cada fila mira clase_ternaria y asigna:
# 1 si es BAJA+1 o BAJA+2
# 0 en cualquier otro caso (CONTINUA)

#%% celda 177 [código]
PARAM$train_final

#%% celda 178 [texto]
Para entrenar el modelo final se usan **todos los datos del 202104**

#%% celda 179 [código]
# Este dataset_train pisa el que usaste en la BO. Es un objeto nuevo con todas las filas de ese mes, sin fold, training ni azar, porque esas columnas solo existían en el subconjunto anterior. Por eso más adelante el entrenamiento final usa todos los datos, sin undersampling ni partición.
dataset_train <- dataset[foto_mes %in% PARAM$train_final]
dataset_train[,.N, list(foto_mes, clase_ternaria)]

# [Anotación · líneas 2105–2155] Limpieza del entrenamiento final por cross-fitting: particiona dataset_train
#   en dos mitades estratificadas por clase (fold30, semilla 600013), entrena para cada mitad un modelo con los
#   parámetros de modelo30 sobre la otra mitad y le asigna prob30. Conserva las filas con clase01 = 1 o prob30
#   menor a 0,5 (elimina los CONTINUA restantes) y muestra los conteos por mes y clase.
#%% celda 180 [texto]
## ⚠️ CAMBIO — Excluyendo registros dudosos en el Final Training
Esta es la parte que **sí cambia tu modelo** aunque no corras la bayesiana.

Como acá no hay un fold "limpio" sobrante, se hace *cross-fitting*: se parte 202103–202106 en dos mitades estratificadas, cada mitad se puntúa con un `modelo30` entrenado en la otra, y se eliminan los `CONTINUA` con `prob30 > 0.5`. Así ningún registro se evalúa con un modelo que lo vio, y no se pierde el 30%.

#%% celda 181 [código]
# ####################################################################
# >>> CAMBIO REGISTROS DUDOSOS (7/7) : limpieza del training final por cross-fitting
# ####################################################################
# Va DESPUES de crear dataset_train (202103..202106) y ANTES de dtrain_final.
# clase01 ya viene del dataset (celda de clase01).
# Ojo memoria: arma 2 matrices de ~la mitad del training final cada vez.

particionar(dataset_train,
  division= c(50, 50),
  agrupa= "clase_ternaria",
  campo= "fold30",
  seed= PARAM$semilla_primigenia
)

dataset_train[, prob30 := NA_real_]

for (f in 1:2) {
  dtr30 <- lgb.Dataset(
    data= data.matrix(dataset_train[fold30 != f, campos_buenos, with= FALSE]),
    label= dataset_train[fold30 != f, clase01],
    free_raw_data= TRUE
  )
  m30 <- lgb.train(data= dtr30, param= PARAM$lgbm$param_iniciales30)

  dataset_train[fold30 == f, prob30 := predict(
    m30, data.matrix(dataset_train[fold30 == f, campos_buenos, with= FALSE])
  )]

  rm(dtr30, m30); gc(verbose= FALSE)
}

# control: dudosos por mes y clase
dataset_train[, .N, list(foto_mes, clase_ternaria, dudoso = prob30 > 0.5)][order(foto_mes, clase_ternaria)]

# elimino los CONTINUA dudosos
dataset_train <- dataset_train[clase01 == 1L | prob30 < 0.5]
dataset_train[, .N, list(foto_mes, clase_ternaria)][order(foto_mes, clase_ternaria)]

# despues sigue igual: dtrain_final, modelo_final y el loop de semillas
# usan este dataset_train ya limpio

# ####################################################################
# <<< FIN CAMBIO
# ####################################################################

# [Anotación · líneas 2157–2203] Arma param_final superponiendo los hiperparámetros elegidos a los parámetros
#   fijos y construye dtrain_final con las filas que quedan de 202103 a 202106, las columnas de campos_buenos,
#   etiqueta clase01 y peso 0,25 para BAJA+1 y 1,0 para el resto.
#%% celda 182 [código]
#ORIGINAL TAREA 04
#%%R
# dejo los datos en el formato que necesita LightGBM

#dtrain_final <- lgb.Dataset(
#  data= data.matrix(dataset_train[, campos_buenos, with= FALSE]),
#  label= dataset_train[, clase01]
#)

#%% celda 183 [texto]
## Final Training Hyperparameters

#%% celda 184 [código]
# Toma la primera lista y pisa solo los elementos que aparecen en la segunda. El resultado es una lista con todos los parámetros fijos, donde esos tres tienen los valores ganadores de la BO.
param_final <- modifyList(PARAM$lgbm$param_fijos,PARAM$out$lgbm$mejores_hiperparametros)

param_final

#%% celda 185 [texto]
## Final Training

#%% celda 186 [texto]
Separa los clientes de junio de 2021, que son los que el modelo va a "ver por primera vez" para simular el uso real.

#%% celda 187 [texto]
Para entrenar el modelo final se usan **todos los datos del 202104** para los campos buenos. Acá se transforma al formato que necesita lgbm.

#%% celda 188 [código]
campos_buenos

#%% celda 189 [código]
# Arma el dataset de entrenamiento final en el formato de LightGBM. El modelo tiene que predecir: 1 para BAJA+1 y BAJA+2; 0 para CONTINUA
#dtrain_final <- lgb.Dataset(
#  data= data.matrix(dataset_train[, campos_buenos, with= FALSE]),
#  label= dataset_train[, clase01]
#)

#%% celda 190 [código]
  # # LE AGREGO PESOS PARA DISTINGUIR LOS BAJA+2

  # Arma el dataset de entrenamiento final en el formato de LightGBM. El modelo tiene que predecir: 1 para BAJA+1 y BAJA+2; 0 para CONTINUA
  dtrain_final <- lgb.Dataset(
    data= data.matrix(dataset_train[, campos_buenos, with= FALSE]),
    label= dataset_train[, clase01],
    weight= dataset_train[, ifelse(clase_ternaria == "BAJA+1", 0.25, 1.0)]
  )

# [Anotación · líneas 2205–2228] Entrena modelo_final con param_final (seed 600013) y lo graba en modelo.txt.
#   El guardado de la importancia de variables queda comentado en esta parte.
#%% celda 191 [texto]
Entreno el modelo con los datos en el formato q necesita lgbm (dtrain_final), con los parametros ganadores (param_final)

#%% celda 192 [código]
# Entreno el modelo sobre todo el periodo
modelo_final <- lgb.train(
  data= dtrain_final,
  param= param_final
)

#%% celda 193 [código]
#%%R
# grabo a disco el modelo en un formato para seres humanos ... ponele ...
lgb.save(modelo_final, "modelo.txt" )

#%% celda 194 [código]
# acá ya podría ver la importancia de las variables
# tb_importancia <- as.data.table(lgb.importance(modelo_final))
#archivo_importancia <- "impo.txt"

#fwrite(tb_importancia,
#  file= archivo_importancia,
#  sep= "\t"
#)

# [Anotación · líneas 2230–2269] Arma dfuture con 202108, le aplica modelo_final y guarda en prediccion.txt
#   numero_de_cliente, foto_mes, la probabilidad y gan (1.072.500 si clase_ternaria es BAJA+2, -27.500 en otro
#   caso).
#%% celda 195 [texto]
## Predict / Scoring

#%% celda 196 [texto]
Aplico el **modelo final a los datos del futuro**

#%% celda 197 [código]
PARAM$future

#%% celda 198 [código]
# datos del futuro
dfuture <- dataset[foto_mes %in% PARAM$future] #PARAM$future=202106

#%% celda 199 [código]
# hago el predict en los datos del futuro, y calculo la ganancia

# aplico el modelo a los datos nuevos
prediccion <- predict(
  modelo_final,
  data.matrix(dfuture[, campos_buenos, with= FALSE])
)

#%% celda 200 [código]
#Este código simula el rendimiento económico del modelo sobre datos del futuro (dfuture), evaluando la ganancia total que obtendrías
#al enviar estímulos/ofertas a distintas cantidades de clientes (puntos de corte).

# tabla de prediccion
# calculo la ganancia en los datos del futuro para todos los cortes
tb_prediccion <- dfuture[, list(numero_de_cliente, foto_mes,clase_ternaria)]
tb_prediccion[, prob := prediccion ]
tb_prediccion[, gan := ifelse(clase_ternaria == "BAJA+2", 1072500, -27500)] # gan es lo que ganarías si le enviaras el estímulo a ese cliente: +1.072.500 si es BAJA+2, -27.500 si no. Todavía no hay un total, porque este depende de cuántos clientes enviás (el corte) y de en qué orden están.

setwd(file.path(DIR_EXP, experimento))

# tabla de prediccion
# grabo las probabilidad del modelo
fwrite(tb_prediccion[,list(numero_de_cliente,foto_mes,prob,gan)], #la ganancia de cada cliente, no la total
  file = "prediccion.txt",
  sep = "\t"
)

# [Anotación · líneas 2271–2347] Ordena por probabilidad descendente, calcula la ganancia acumulada, imprime
#   la ganancia de cada corte de PARAM$cortes y grafica la curva para las primeras 30.000 posiciones. Las celdas
#   de control de la distribución de prob quedan comentadas.
#%% celda 201 [texto]
El **corte (o "envíos")** es la **cantidad de clientes a los que decidís mandarles el estímulo** de retención. El modelo no te dice "este cliente se va a dar de baja sí o no", sino "este tiene 8 % de probabilidad, este 2 %, este 0,1 %...". **Alguien tiene que decidir hasta dónde de esa lista se manda el estímulo, y esa decisión es el corte**.

Cómo funciona
- El modelo le asigna una probabilidad a cada cliente de junio (prob).
- Ordenás la lista de mayor a menor probabilidad (setorder(tb_prediccion, -prob)).
- Elegís un número, por ejemplo 10000, y mandás el estímulo a los primeros 10000 de la lista.

Predicted = 1 significa "le mando el estímulo" y 0 "no le mando".
- tb_prediccion[, Predicted := 0L]        # a nadie
- tb_prediccion[1:envios, Predicted := 1L] # a los primeros 'envios'

**Por qué importa el número: Cada envío tiene un costo y un posible beneficio:**
- Si el cliente era BAJA+2, ganás 1.072.500.
- Si no lo era, perdés 27.500 (lo que costó el estímulo).

**Al principio de la lista están los clientes con más chance de ser BAJA+2, así que casi cada envío suma ganancia**. A medida que bajás, las probabilidades caen, aparecen cada vez más clientes que no se iban a ir, y cada envío nuevo resta más de lo que suma. Por eso la curva tiene forma de montaña.

#%% celda 202 [código]
# Dibujo la curva de ganancia acumulada
setorder(tb_prediccion, -prob)

tb_prediccion[, ganancia_acumulada := cumsum(gan)]
tb_prediccion[, pos := sequence(.N)]

for (envios in PARAM$cortes) {
  ganancia <- tb_prediccion[1:envios, sum(gan)]
  cat( envios, "\t", ganancia, "\n")
}

#%% celda 203 [código]
#%%R
# observamos la curva de ganancia

# defino hasta donde muestra el grafico
amostrar <- 30000

gra <- ggplot(
           data= tb_prediccion[pos <= amostrar],
           aes( x= pos, y= ganancia_acumulada)
             ) + geom_line()

gra <- gra + theme(text = element_text(size = 16))

options(repr.plot.width=16, repr.plot.height=9)
print( gra )

#%% celda 204 [código]
tb_prediccion |> head()

# Muestra los 6 clientes con mayor probabilidad de baja según el modelo, es decir el principio de la lista ordenada sobre la que se define el corte. El head() solo imprime las primeras 6 filas.

#%% celda 205 [texto]
Qué se ve en esas 6 filas:
- Las probabilidades van de 0,999 a 0,988, o sea que **el modelo está casi seguro de que esos clientes se van. Sin embargo, ninguno es BAJA+2: hay 2 BAJA+1 y 4 CONTINUA.** Como solo BAJA+2 paga, los 6 valen -27.500 y la ganancia acumulada baja de a 27.500 por fila hasta -165.000 en la posición 6 (6 × 27.500).
- Un arranque negativo no significa que el modelo esté mal. **La ganancia total de un corte recién se ve después de miles de clientes: en tu tabla de cortes la curva termina en +411 M en 11.000 envíos. Seis filas son una muestra chica para juzgar nada.**

Lo que sí llama la atención
- Que las probabilidades sean tan cercanas a 1 es raro para un problema donde las bajas son muy pocas. El modelo final entrena sin undersampling, así que esperaría probabilidades más bajas, aunque las de los mejores sigan siendo relativamente altas. Junto con que los primeros 6 no acierten ninguna BAJA+2, es señal de un modelo muy confiado.
- Puede deberse a que tiene mucha capacidad (364 hojas, 3253 árboles, min_data_in_leaf = 0) y se ajusta demasiado al entrenamiento. No es un problema del código, es algo que se ve al mirar el resultado.

Para chequearlo, mirá la distribución de prob en junio:

#%% celda 206 [código]
#summary(tb_prediccion$prob)
#tb_prediccion[, .(n = .N, bajas2 = sum(clase_ternaria == "BAJA+2")),
#              by = .(tramo = cut(prob, c(0, .1, .5, .9, 1)))]

#%% celda 207 [código]
#tb_prediccion[, .(n = .N,
#                  bajas = sum(clase_ternaria %in% c("BAJA+1", "BAJA+2")),
#                  prob_media = mean(prob)),
#              by = .(tramo = cut(prob, c(0, .1, .5, .9, 1)))][
#  , tasa_real := bajas / n][]

#%% celda 208 [código]
format(Sys.time(), "%a %b %d %X %Y")

# [Anotación · líneas 2349–2415] Inicializa drealidad con dfuture y, para cada corte, marca Predicted = 1 en
#   los primeros envíos e imprime la ganancia total, pública y privada que devuelve realidad_evaluar. Guarda
#   PARAM en PARAM.yml y el objeto del espacio de búsqueda en hs_paramset.rds.
#%% celda 209 [texto]
## Revisamos ganancia bajo distintos cortes

#%% celda 210 [código]
PARAM

#%% celda 211 [código]
#%%R
# inicilizo el dataset  drealidad
drealidad <- realidad_inicializar( dfuture, PARAM)

#`Función realidad_inicializar`:
#Prepara la "tabla de la realidad" para calcular la ganancia real de cada corte, simulando el leaderboard de Kaggle.
#- Se queda con tres columnas de dfuture: numero_de_cliente, foto_mes y clase_ternaria. Esta última es la verdad, lo que realmente pasó con cada cliente.
#- Le agrega una columna fold con particionar(..., division = c(3, 7), agrupa = "clase_ternaria"). Es el mismo reparto estratificado que vimos antes: 30 % de los clientes al fold 1 (el "Public") y 70 % al fold 2 (el "Private"), manteniendo esa proporción dentro de cada clase.
#- Devuelve el resultado, que después usa realidad_evaluar para calcular ganancia total, Public y Private.

#%% celda 212 [código]
head(drealidad)

#%% celda 213 [código]
head(tb_prediccion)

#%% celda 214 [código]
PARAM$cortes

#%% celda 215 [código]
#%%R
# genero archivos con los  "envios" mejores
# suba TODOS los archivos a Kaggle

# ordeno por probabilidad descendente
setorder(tb_prediccion, -prob)

for (envios in PARAM$cortes) {
  tb_prediccion[, Predicted := 0L] # seteo inicial a 0
  tb_prediccion[1:envios, Predicted := 1L] # marco los primeros

  res <- realidad_evaluar( drealidad, tb_prediccion)

  options(scipen = 999)
  cat( "Envios=", envios, "\t",
    " TOTAL=", res$total,
    "  Public=", res$public,
    " Private=", res$private,
    "\n",
    sep= ""
  )

}

#%% celda 216 [código]
# el original era 
# write_yaml( PARAM, file="PARAM.yml")

# 1. Guardar el ParamSet en un archivo RDS
saveRDS(PARAM$hypeparametertuning$hs, file = "hs_paramset.rds")

# 2. Reemplazar el objeto por la ruta en tu lista PARAM
PARAM_yaml <- PARAM
PARAM_yaml$hypeparametertuning$hs <- "hs_paramset.rds"

# 3. Escribir el YAML sin errores
yaml::write_yaml(PARAM_yaml, file = "PARAM.yml")

#%% celda 217 [código]
format(Sys.time(), "%a %b %d %X %Y")

# [Anotación · líneas 2417–2462] Calcula la importancia de variables de modelo_final, la graba en impo.txt y
#   grafica las 20 variables de mayor Gain.
#%% celda 218 [texto]
## Importancia de las variables

#%% celda 219 [código]
# ahora imprimo la importancia de variables

tb_importancia <- as.data.table(lgb.importance(modelo_final))
archivo_importancia <- "impo.txt"

setwd(file.path(DIR_EXP, experimento))

# Al haber usado setwd(), al poner solo "impo.txt" se guarda adentro de exp...
fwrite(tb_importancia,
  file = "impo.txt",
  sep = "\t"
)

#%% celda 220 [código]
tb_importancia
# Gain (Ganancia): Es la métrica principal de importancia. Indica cuánto mejora la precisión del modelo cada vez que se utiliza esta variable para dividir los datos en un árbol. A mayor valor, más relevante es la variable para predecir.
# Cover (Cobertura): Representa la proporción relativa de observaciones (o datos) que pasan por los nodos donde se utiliza esta variable.
# Frequency (Frecuencia): Mide el porcentaje o proporción de veces que la variable fue elegida para hacer una división a lo largo de todos los árboles del modelo.

#%% celda 221 [código]
# Tomamos las 20 variables más importantes por Gain
tb_importancia %>%
  head(20) %>%
  ggplot(aes(x = reorder(Feature, Gain), y = Gain)) +
  geom_col(fill = "#3182bd", width = 0.7) +
  coord_flip() +
  labs(
    title = "Top 20 Variables más Importantes",
    subtitle = "Medido por Ganancia (Gain)",
    x = NULL,
    y = "Gain"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    panel.grid.major.y = element_blank(),
    plot.title = element_text(face = "bold", size = 14),
    axis.text.y = element_text(color = "black")
  )

#%% celda 222 [texto]
Finalmente usted deberá cargar el resultado de su corrida en la Google Sheet Colaborativa,  hoja **TareaHogar04**
<br> Siéntase libre de agregar las columnas que hagan falta a la planilla

# [Anotación · líneas 2464–2521] Define las semillas 600013, 620003 y 640007. Para cada una entrena un modelo
#   con param_final cambiando sólo seed, lo graba como modelo_<semilla>.txt, predice 202108 y evalúa todos los
#   cortes; al final evalúa también el promedio de las probabilidades de las semillas. Los resultados se graban
#   en resultados_semillas.txt.
#%% celda 223 [texto]
## Variabilidad por semilla
Realizo el **entrenamiento del modelo final** con **varias semillas (mismos hiperparámetros)** y evalúo la ganancia en cada corte, más el promedio de las semillas.

#%% celda 224 [texto]
La BO sigue usando una sola semilla (semilla_primigenia = 600013), como antes. Las 5 semillas solo se aplican al entrenamiento final, que es lo que queríamos.

#%% celda 225 [código]
# ---- Variabilidad por semilla: mismos hiperparametros, cambia solo la semilla ----
#PARAM$semillas <- c(600013, 620003, 640007, 660007, 680003)  
PARAM$semillas <- c(
  600013, 620003, 640007  # las 5 tuyas, sin cambios
)

X_future <- data.matrix(dfuture[, campos_buenos, with= FALSE]) #selecciona un conjunto de columnas específicas de una tabla y las convierte en una matriz numérica
predicciones <- matrix(NA_real_, nrow= nrow(dfuture), ncol= length(PARAM$semillas)) #crea una matriz vacía llamada predicciones, que se utiliza para almacenar los resultados que generarán múltiples modelos (entrenados con distintas semillas aleatorias) para cada registro de dfuture.

tb_resultados <- data.table(semilla= character(), envios= numeric(),total= numeric(), public= numeric(), private= numeric())

# evalua todos los cortes para un vector de probabilidades y devuelve una tabla
evaluar_cortes <- function(prob, etiqueta) {
  tb_pred <- dfuture[, list(numero_de_cliente, foto_mes)]
  tb_pred[, prob := prob]
  setorder(tb_pred, -prob)

  filas <- list()
  for (envios in PARAM$cortes) {
    tb_pred[, Predicted := 0L]
    tb_pred[1:envios, Predicted := 1L]
    res <- realidad_evaluar(drealidad, tb_pred)
    filas[[length(filas) + 1]] <- list(etiqueta, envios, res$total, res$public, res$private)
  }
  rbindlist(filas)
}

for (i in seq_along(PARAM$semillas)) {
  semilla <- PARAM$semillas[i]
  gc()

  param_semilla <- copy(param_final)
  param_semilla$seed <- semilla          # lo unico que cambia entre corridas

  modelo <- lgb.train(data= dtrain_final, param= param_semilla)
  lgb.save(modelo, paste0("modelo_", semilla, ".txt"))
  predicciones[, i] <- predict(modelo, X_future)

  tb_resultados <- rbind(tb_resultados,
                         evaluar_cortes(predicciones[, i], as.character(semilla)),
                         use.names= FALSE)

  fwrite(tb_resultados, "resultados_semillas.txt", sep= "\t")   # grabo en cada vuelta
}

# el promedio de las semillas, evaluado igual
tb_resultados <- rbind(tb_resultados,
                       evaluar_cortes(rowMeans(predicciones), "promedio"),
                       use.names= FALSE)
fwrite(tb_resultados, "resultados_semillas.txt", sep= "\t")

# [Anotación · líneas 2523–2582] Resume por corte la media, el desvío, el mínimo y el máximo de la ganancia
#   entre semillas junto con la del promedio; repite la impresión de ganancia por corte de tb_prediccion y
#   guarda PARAM en PARAM_semillas.yml.
#%% celda 226 [código]
# resumen: cuanto varia la ganancia segun la semilla en cada corte
resumen <- tb_resultados[semilla != "promedio",
  list(media= mean(total), desvio= sd(total), minimo= min(total), maximo= max(total)),
  by= envios]

prom <- tb_resultados[semilla == "promedio", list(envios, total_promedio= total)]
resumen <- merge(resumen, prom, by= "envios")
resumen

#%% celda 227 [código]
head(drealidad)

#%% celda 228 [código]
head(tb_prediccion)

#%% celda 229 [código]
PARAM$cortes

#%% celda 230 [código]
#%%R
# genero archivos con los  "envios" mejores
# suba TODOS los archivos a Kaggle

# ordeno por probabilidad descendente
setorder(tb_prediccion, -prob)

for (envios in PARAM$cortes) {
  tb_prediccion[, Predicted := 0L] # seteo inicial a 0
  tb_prediccion[1:envios, Predicted := 1L] # marco los primeros

  res <- realidad_evaluar( drealidad, tb_prediccion)

  options(scipen = 999)
  cat( "Envios=", envios, "\t",
    " TOTAL=", res$total,
    "  Public=", res$public,
    " Private=", res$private,
    "\n",
    sep= ""
  )

}

#%% celda 231 [código]
# el original era 
# write_yaml( PARAM, file="PARAM.yml")

# 1. Guardar el ParamSet en un archivo RDS
saveRDS(PARAM$hypeparametertuning$hs, file = "hs_paramset.rds")

# 2. Reemplazar el objeto por la ruta en tu lista PARAM
PARAM_yaml <- PARAM
PARAM_yaml$hypeparametertuning$hs <- "hs_paramset.rds"

# 3. Escribir el YAML sin errores
yaml::write_yaml(PARAM_yaml, file = "PARAM_semillas.yml")

#%% celda 232 [código]
format(Sys.time(), "%a %b %d %X %Y")

# [Anotación · líneas 2584–2642] Toma como predicción el promedio de las probabilidades de las semillas y
#   graba prediccion_promedio.txt con numero_de_cliente, foto_mes, prob y gan. Repite sobre ese promedio la
#   curva de ganancia acumulada, el gráfico y la ganancia por corte.
#%% celda 233 [código]
# ---- Uso el promedio de las semillas como predicción ----
prediccion <- rowMeans(predicciones)

# ---- (celda 174) tabla de predicción ----
tb_prediccion <- dfuture[, list(numero_de_cliente, foto_mes, clase_ternaria)]
tb_prediccion[, prob := prediccion]
tb_prediccion[, gan := ifelse(clase_ternaria == "BAJA+2", 1072500, -27500)]

setwd(file.path(DIR_EXP, experimento))

# grabo las probabilidades del modelo promedio
fwrite(tb_prediccion[, list(numero_de_cliente, foto_mes, prob, gan)],
  file = "prediccion_promedio.txt",
  sep = "\t"
)

# ---- (celda 176) curva de ganancia acumulada ----
setorder(tb_prediccion, -prob)

tb_prediccion[, ganancia_acumulada := cumsum(gan)]
tb_prediccion[, pos := sequence(.N)]

for (envios in PARAM$cortes) {
  ganancia <- tb_prediccion[1:envios, sum(gan)]
  cat(envios, "\t", ganancia, "\n")
}

# ---- (celda 177) gráfico de la curva de ganancia ----
amostrar <- 30000

gra <- ggplot(
  data= tb_prediccion[pos <= amostrar],
  aes(x= pos, y= ganancia_acumulada)
) + geom_line()

gra <- gra + theme(text = element_text(size = 16))

options(repr.plot.width=16, repr.plot.height=9)
print(gra)

# ---- (celda 189) ganancia en cada corte: total, Public y Private ----
setorder(tb_prediccion, -prob)

for (envios in PARAM$cortes) {
  tb_prediccion[, Predicted := 0L]
  tb_prediccion[1:envios, Predicted := 1L]

  res <- realidad_evaluar(drealidad, tb_prediccion)

  options(scipen = 999)
  cat("Envios=", envios, "\t",
    " TOTAL=", res$total,
    "  Public=", res$public,
    " Private=", res$private,
    "\n",
    sep= ""
  )
}

# [Anotación · líneas 2644–2690] Arma resumen_completo con la media y el desvío de la ganancia total y las
#   medias pública y privada por corte, junto con la ganancia del promedio de probabilidades; grafica cada
#   semilla, la media y el ensamble, y muestra el corte de mayor ganancia media y el de mayor ganancia del
#   ensamble.
#%% celda 234 [código]
# media (y dispersión) de la ganancia entre semillas, para cada corte
resumen_completo <- tb_resultados[semilla != "promedio",
  list(
    total_media   = mean(total),
    total_desvio  = sd(total),
    public_media  = mean(public),
    private_media = mean(private)
  ),
  by= envios]

# ganancia del ensamble (promedio de probabilidades), para comparar
ensamble <- tb_resultados[semilla == "promedio",
  list(envios, total_ensamble= total)]

resumen_completo <- merge(resumen_completo, ensamble, by= "envios")
setorder(resumen_completo, envios)

options(scipen = 999)
resumen_completo

#%% celda 235 [texto]
Las dos formas de "promediar" no son lo mismo
- total_media (azul): promedia las ganancias de 5 modelos evaluados por separado. Responde a "¿cuánto gano en promedio si uso una sola semilla?".
- total_ensamble (rojo): promedia primero las probabilidades de los 5 modelos y evalúa el ranking resultante. Responde a "¿cuánto gano si uso los 5 modelos juntos?".

#%% celda 236 [código]
ggplot() +
  geom_line(data= tb_resultados[semilla != "promedio"],
            aes(x= envios, y= total, group= semilla),
            color= "grey70") +
  geom_line(data= resumen_completo,
            aes(x= envios, y= total_media),
            color= "blue", linewidth= 1.2) +
  geom_line(data= resumen_completo,
            aes(x= envios, y= total_ensamble),
            color= "red", linewidth= 1.2, linetype= "dashed") +
  theme_minimal() +
  labs(title= "Ganancia por corte según semilla",
       subtitle= "Gris: cada semilla | Azul: media de ganancias | Rojo: ganancia del promedio de probabilidades",
       x= "Envíos", y= "Ganancia total")

#%% celda 237 [código]
resumen_completo[which.max(total_media), list(envios, total_media)]

#%% celda 238 [código]
resumen_completo[which.max(total_ensamble), list(envios, total_ensamble)]

# [Anotación · líneas 2692–2733] Celdas de texto y una celda comentada que generaba el archivo de envío con el
#   corte de mayor ganancia del ensamble.
#%% celda 239 [texto]
Finalmente, entre tanta lista de instrucciones, algo conceptual:

En la materia Data Mining sufrieron descarnadamente el overfitting, un modelo que funcionaba bien en el Public Leaderboard era muy malo en el Private. Eran presa de La maldicion del ganador

Para evitar eso, ahora en sus notebooks, en la parte final de generaicion del modelo final con LightGBM, generan varios modelos, cada uno solamente cambiando el hipeparametro seed de LightGBM y con el resto de los hiperparametros identicos.

Cada uno de estos modelos genera una prediccion sobre los datos del futuro, el mes 202108

Esos multiples archivos (hasta 20) son los que entregan en un submit, y el generoso bot, a diferencia del traicionero Zulip, les devuelve la media y la varianza de esas ganancias, con lo cual reducen enormemente el overfitting.
(tecnicamente NO lo eliminan por completo)

#%% celda 240 [texto]
## Archivo final de envíos
Genera un CSV **sin encabezado** con únicamente los `numero_de_cliente` a los que se envía el estímulo, usando el ensamble de las 5 semillas y el corte (cantidad de envíos) que maximiza la ganancia del ensamble. Los ids se escriben como enteros, sin notación científica.

#%% celda 241 [código]
# ---- Archivo final: solo numero_de_cliente a estimular, sin encabezado ----

# corte elegido: el que maximiza la ganancia del ensamble (promedio de semillas)
#envios_final <- resumen_completo[which.max(total_ensamble), envios]
# (para fijar el corte a mano, por ejemplo: envios_final <- 11000)

# ordeno por probabilidad del ensamble (descendente) y me quedo con los primeros 'envios_final'
#tb_envio <- dfuture[, list(numero_de_cliente)]
#tb_envio[, prob := rowMeans(predicciones)]
#setorder(tb_envio, -prob)
#ids_estimulo <- tb_envio[1:envios_final, numero_de_cliente]

# ids como enteros: nada de notacion cientifica
# (format(..., scientific=FALSE) garantiza digitos completos, tambien si superan el rango de integer de 32 bits)
#ids_txt <- format(as.numeric(ids_estimulo), scientific= FALSE, trim= TRUE)
#stopifnot(!any(grepl("[eE.]", ids_txt)))   # control: ni notacion cientifica ni decimales

#archivo_envio <- file.path(DIR_EXP, experimento, paste0("envio_", envios_final, ".csv"))
#archivo_envio <- file.path(DIR_EXP, experimento, "Intento01z4945.csv")
#writeLines(ids_txt, archivo_envio)         # una columna, sin encabezado, sin comillas

#cat("Archivo:", archivo_envio, "\n")
#cat("Clientes a estimular:", length(ids_txt), "\n")
#cat("Primeras lineas del archivo:\n")
#print(readLines(archivo_envio, n= 5))

# [Anotación · líneas 2735–2817] Con tb_prediccion ordenada por la probabilidad promedio, graba siete archivos
#   de una columna sin encabezado, Intentoj4955_01.csv a Intentoj4955_07.csv, con los primeros 11.400, 11.600,
#   11.800, 12.000, 11.200, 11.000 y 10.800 clientes. Después de cada uno lo relee y muestra cantidad de filas,
#   de columnas, duplicados y las dos primeras líneas.
#%% celda 242 [código]
setorder(tb_prediccion, -prob)
fwrite(tb_prediccion[1:11400, list(numero_de_cliente)],
       file = "Intentoj4955_01.csv", col.names = FALSE)

#%% celda 243 [código]
chk <- fread("Intentoj4955_01.csv", header = FALSE)
nrow(chk)                    # tiene que ser 12000
ncol(chk)                    # tiene que ser 1
anyDuplicated(chk$V1)        # tiene que ser 0
readLines("Intentoj4955_01.csv", n = 2)   # solo números, sin nombres

#%% celda 244 [código]
setorder(tb_prediccion, -prob)
fwrite(tb_prediccion[1:11600, list(numero_de_cliente)],
       file = "Intentoj4955_02.csv", col.names = FALSE)

#%% celda 245 [código]
chk <- fread("Intentoj4955_02.csv", header = FALSE)
nrow(chk)                    # tiene que ser 12000
ncol(chk)                    # tiene que ser 1
anyDuplicated(chk$V1)        # tiene que ser 0
readLines("Intentoj4955_02.csv", n = 2)   # solo números, sin nombres

#%% celda 246 [código]
setorder(tb_prediccion, -prob)
fwrite(tb_prediccion[1:11800, list(numero_de_cliente)],
       file = "Intentoj4955_03.csv", col.names = FALSE)

#%% celda 247 [código]
chk <- fread("Intentoj4955_03.csv", header = FALSE)
nrow(chk)                    # tiene que ser 12000
ncol(chk)                    # tiene que ser 1
anyDuplicated(chk$V1)        # tiene que ser 0
readLines("Intentoj4955_03.csv", n = 2)   # solo números, sin nombres

#%% celda 248 [código]
setorder(tb_prediccion, -prob)
fwrite(tb_prediccion[1:12000, list(numero_de_cliente)],
       file = "Intentoj4955_04.csv", col.names = FALSE)

#%% celda 249 [código]
chk <- fread("Intentoj4955_04.csv", header = FALSE)
nrow(chk)                    # tiene que ser 12000
ncol(chk)                    # tiene que ser 1
anyDuplicated(chk$V1)        # tiene que ser 0
readLines("Intentoj4955_04.csv", n = 2)   # solo números, sin nombres

#%% celda 250 [código]
setorder(tb_prediccion, -prob)
fwrite(tb_prediccion[1:11200, list(numero_de_cliente)],
       file = "Intentoj4955_05.csv", col.names = FALSE)

#%% celda 251 [código]
chk <- fread("Intentoj4955_05.csv", header = FALSE)
nrow(chk)                    # tiene que ser 12000
ncol(chk)                    # tiene que ser 1
anyDuplicated(chk$V1)        # tiene que ser 0
readLines("Intentoj4955_05.csv", n = 2)   # solo números, sin nombres

#%% celda 252 [código]
setorder(tb_prediccion, -prob)
fwrite(tb_prediccion[1:11000, list(numero_de_cliente)],
       file = "Intentoj4955_06.csv", col.names = FALSE)

#%% celda 253 [código]
chk <- fread("Intentoj4955_06.csv", header = FALSE)
nrow(chk)                    # tiene que ser 12000
ncol(chk)                    # tiene que ser 1
anyDuplicated(chk$V1)        # tiene que ser 0
readLines("Intentoj4955_06.csv", n = 2)   # solo números, sin nombres

#%% celda 254 [código]
setorder(tb_prediccion, -prob)
fwrite(tb_prediccion[1:10800, list(numero_de_cliente)],
       file = "Intentoj4955_07.csv", col.names = FALSE)

#%% celda 255 [código]
chk <- fread("Intentoj4955_07.csv", header = FALSE)
nrow(chk)                    # tiene que ser 12000
ncol(chk)                    # tiene que ser 1
anyDuplicated(chk$V1)        # tiene que ser 0
readLines("Intentoj4955_07.csv", n = 2)   # solo números, sin nombres

# [Anotación · líneas 2819–2874] Backtest: toma 202103 y 202104 como entrenamiento y 202106 como prueba, con
#   las semillas 600013, 620003, 640007, 660007 y 680003 y la limpieza de dudosos desactivada
#   (limpiar_dudosos_bt = FALSE). Arma dtrain_bt con los mismos pesos por clase, inicializa la tabla de realidad
#   de 202106 y define evaluar_cortes_bt, que calcula la ganancia de cada corte.
#%% celda 256 [código]
# =====================================================================
# BACKTEST: entreno con 202103 + 202104, predigo 202106, mido ganancia
# =====================================================================
PARAM$train_bt   <- c(202103, 202104)
PARAM$test_bt    <- 202106
PARAM$semillas_bt <- c(600013, 620003, 640007, 660007, 680003)
PARAM$limpiar_dudosos_bt <- FALSE          # TRUE = aplica el cross-fitting de dudosos

dataset_bt <- dataset[foto_mes %in% PARAM$train_bt]
dtest_bt   <- dataset[foto_mes %in% PARAM$test_bt]

# --- (opcional) misma limpieza de registros dudosos que usás en el final ---
if (PARAM$limpiar_dudosos_bt) {
  particionar(dataset_bt, division= c(50, 50), agrupa= "clase_ternaria",
              campo= "fold30", seed= PARAM$semilla_primigenia)
  dataset_bt[, prob30 := NA_real_]
  for (f in 1:2) {
    dtr30 <- lgb.Dataset(
      data= data.matrix(dataset_bt[fold30 != f, campos_buenos, with= FALSE]),
      label= dataset_bt[fold30 != f, clase01], free_raw_data= TRUE)
    m30 <- lgb.train(data= dtr30, param= PARAM$lgbm$param_iniciales30)
    dataset_bt[fold30 == f, prob30 := predict(
      m30, data.matrix(dataset_bt[fold30 == f, campos_buenos, with= FALSE]))]
    rm(dtr30, m30); gc(verbose= FALSE)
  }
  dataset_bt <- dataset_bt[clase01 == 1L | prob30 < 0.5]
}
dataset_bt[, .N, list(foto_mes, clase_ternaria)][order(foto_mes, clase_ternaria)]

#%% celda 257 [código]
# --- dataset de LightGBM (mismos pesos que el modelo final) ---
dtrain_bt <- lgb.Dataset(
  data= data.matrix(dataset_bt[, campos_buenos, with= FALSE]),
  label= dataset_bt[, clase01],
  weight= dataset_bt[, ifelse(clase_ternaria == "BAJA+1", 0.25, 1.0)]
)

#%% celda 258 [código]
# --- realidad de junio (junio SI tiene clase_ternaria, por eso se puede medir) ---
drealidad_bt <- realidad_inicializar(dtest_bt, PARAM)
X_test_bt    <- data.matrix(dtest_bt[, campos_buenos, with= FALSE])

evaluar_cortes_bt <- function(prob, etiqueta) {
  tb_pred <- dtest_bt[, list(numero_de_cliente, foto_mes)]
  tb_pred[, prob := prob]
  setorder(tb_pred, -prob)
  filas <- list()
  for (envios in PARAM$cortes) {
    tb_pred[, Predicted := 0L]
    tb_pred[1:envios, Predicted := 1L]
    res <- realidad_evaluar(drealidad_bt, tb_pred)
    filas[[length(filas) + 1]] <- list(etiqueta, envios, res$total, res$public, res$private)
  }
  rbindlist(filas)
}

# [Anotación · líneas 2876–2918] Entrena un modelo por semilla con param_final sobre dtrain_bt, predice 202106
#   y evalúa todos los cortes; agrega la evaluación del promedio de probabilidades y graba backtest_202106.txt.
#   Resume por corte media, desvío, pública y privada, muestra el corte de mayor ganancia del ensamble y el de
#   mayor ganancia media, y grafica las curvas.
#%% celda 259 [código]
# --- entreno por semilla (mismos hiperparametros que el final) ---
pred_bt <- matrix(NA_real_, nrow= nrow(dtest_bt), ncol= length(PARAM$semillas_bt))
tb_bt   <- data.table(semilla= character(), envios= numeric(),
                      total= numeric(), public= numeric(), private= numeric())

for (i in seq_along(PARAM$semillas_bt)) {
  p <- copy(param_final)
  p$seed <- PARAM$semillas_bt[i]
  m <- lgb.train(data= dtrain_bt, param= p)
  pred_bt[, i] <- predict(m, X_test_bt)
  tb_bt <- rbind(tb_bt, evaluar_cortes_bt(pred_bt[, i], as.character(PARAM$semillas_bt[i])),
                 use.names= FALSE)
  rm(m); gc(verbose= FALSE)
}

#%% celda 260 [código]
# --- ensamble (promedio de probabilidades) ---
tb_bt <- rbind(tb_bt, evaluar_cortes_bt(rowMeans(pred_bt), "promedio"), use.names= FALSE)
fwrite(tb_bt, "backtest_202106.txt", sep= "\t")

#%% celda 261 [código]
# --- resumen por corte ---
options(scipen= 999)
res_bt <- merge(
  tb_bt[semilla != "promedio",
        list(media= mean(total), desvio= sd(total),
             public= mean(public), private= mean(private)), by= envios],
  tb_bt[semilla == "promedio", list(envios, ensamble= total)], by= "envios")
setorder(res_bt, envios)
res_bt

res_bt[which.max(ensamble), list(envios, ensamble)]   # mejor corte del ensamble
res_bt[which.max(media),    list(envios, media)]      # mejor corte por media de semillas

#%% celda 262 [código]
# curva de ganancia del backtest
ggplot() +
  geom_line(data= tb_bt[semilla != "promedio"], aes(envios, total, group= semilla), color= "grey70") +
  geom_line(data= res_bt, aes(envios, media),    color= "blue", linewidth= 1.2) +
  geom_line(data= res_bt, aes(envios, ensamble), color= "red",  linewidth= 1.2, linetype= "dashed") +
  theme_minimal() +
  labs(title= "Backtest 202106 (train 202103+202104)", x= "Envíos", y= "Ganancia total")

# [Anotación · líneas 2920–2932] Con el corte fijado en 12.000 sobre el promedio del backtest, asigna a cada
#   cliente su ganancia si queda dentro del corte y 0 si no; repite 5.000 veces (set.seed(1)) un muestreo sin
#   reposición del 70% de las filas, suma la ganancia y la divide por 0,7. Muestra los cuantiles 1%, 5%, 50% y
#   95% y la proporción de simulaciones por debajo de 300 millones.
#%% celda 263 [código]
corte <- 12000
tb <- dtest_bt[, list(clase_ternaria)]
tb[, prob := rowMeans(pred_bt)]
setorder(tb, -prob)
tb[, gan := ifelse(seq_len(.N) <= corte,
                   ifelse(clase_ternaria == "BAJA+2", 1072500, -27500), 0)]

set.seed(1)
n <- nrow(tb)
sim <- replicate(5000, sum(tb$gan[sample.int(n, round(n * 0.7))]) / 0.7)
quantile(sim, c(0.01, 0.05, 0.50, 0.95))
mean(sim < 300e6)
```

### DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb

Experimento HT4957-01: mismo flujo que j4955 con feature_fraction_bynode 0,2, optimización bayesiana propia de 40 evaluaciones y 12 semillas en el modelo final; graba prediccion_promedio.txt, la otra entrada del blend. Difiere de j4955 en esas celdas, en la cantidad de archivos de envío propios (11) y en que no tiene la simulación final del corte de 12.000.

El código completo está en https://emavaldez.github.io/postmortem/fuentes/lulimontero/DMEyF/Primera-Competencia/notebooks/j4957_competencia.ipynb.txt

### DMEyF/Primera-Competencia/notebooks/blend_j4955_j4957.ipynb

Lee las predicciones promedio de HT4955-01 y HT4957-01, las combina promediando los puestos de cada cliente y escribe los archivos de envío Intentoj_blend_<corte>.csv para cortes de 10.500 a 14.500 cada 500.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–9] Carga data.table y lee las dos predicciones promedio:
#   ~/buckets/b1/exp/HT4955-01/prediccion_promedio.txt y ~/buckets/b1/exp/HT4957-01/prediccion_promedio.txt.
#%% celda 1 [código]
require( "data.table" )

#%% celda 2 [código]
library(data.table)
DIR_EXP <- path.expand("~/buckets/b1/exp")

a <- fread(file.path(DIR_EXP, "HT4955-01", "prediccion_promedio.txt"))
b <- fread(file.path(DIR_EXP, "HT4957-01", "prediccion_promedio.txt"))

# [Anotación · líneas 11–18] Une ambas tablas por numero_de_cliente (pa y pb son las probabilidades de cada
#   experimento) y verifica que no se pierdan filas. Calcula score como el promedio de los puestos de pa y pb
#   (frank, creciente con la probabilidad) y ordena de mayor a menor score.
tb <- merge(a[, .(numero_de_cliente, pa = prob)],
            b[, .(numero_de_cliente, pb = prob)],
            by = "numero_de_cliente")
stopifnot(nrow(tb) == nrow(a), nrow(tb) == nrow(b))

# blend 50/50 por puestos
tb[, score := (frank(pa) + frank(pb)) / 2]
setorder(tb, -score)

# [Anotación · líneas 20–33] Crea la carpeta BLEND-4955-4957 y, para cada corte de 10.500 a 14.500 cada 500,
#   escribe Intentoj_blend_<corte>.csv con los primeros numero_de_cliente, sin encabezado. Relee cada archivo y
#   verifica que tenga la cantidad de filas del corte y ningún cliente duplicado.
# carpeta para los archivos del blend
dir_blend <- file.path(DIR_EXP, "BLEND-4955-4957")
dir.create(dir_blend, showWarnings = FALSE)

cortes_blend <- seq(10500, 14500, by = 500)

for (corte in cortes_blend) {
  archivo <- file.path(dir_blend, paste0("Intentoj_blend_", corte, ".csv"))
  fwrite(tb[1:corte, .(numero_de_cliente)], archivo, col.names = FALSE)

  chk <- fread(archivo, header = FALSE)
  stopifnot(nrow(chk) == corte, anyDuplicated(chk$V1) == 0)
  cat(corte, "OK\n")
}
```


## Explicaciones del alumno (texto original)

### DMEyF/Primera-Competencia/README.md

> # Competencia 01 — Predicción de BAJA+2 (DMEyF 2026)
>
> Modelo de LightGBM para elegir a qué clientes enviarles un estímulo de retención en **202108**.
> La entrega final es un **blend de dos experimentos** (j4955 y j4957) con un corte de **12.000 envíos**.
>
> **Archivo entregado:** `Intentoj_blend_12000.csv`
>
> ---
>
> ## 1. Estructura del repositorio
>
> ```
> .
> ├── README.md
> ├── notebooks/
> │   ├── j4953_competencia.ipynb      # experimento HT4953-01: bayesiana que dio los hiperparámetros del j4955
> │   ├── j4955_competencia.ipynb      # experimento HT4955-01 (hiperparámetros del j4953, bynode = 1.0, 3 semillas)
> │   ├── j4957_competencia.ipynb      # experimento HT4957-01 (bayesiana propia, bynode = 0.2, 12 semillas)
> │   └── blend_j4955_j4957.ipynb      # blend de los dos y archivos de envío
> ├── bayesianas/
>     ├── HT4953-01_BO_log.txt         # log completo de la bayesiana del j4953
>     └── HT4957-01_BO_log.txt         # log completo de la bayesiana del j4957
>
> ```
>
> Los datasets, los modelos `.txt` de LightGBM y las predicciones intermedias no se suben (ver `.gitignore`).
>
> ## 2. Problema y ganancia
>
> - Datos: `competencia_01_crudo.csv`, meses 202103 a 202108.
> - `clase_ternaria`: `CONTINUA`, `BAJA+1`, `BAJA+2`. En 202107 y 202108 la clase no se conoce.
> - Ganancia por cliente estimulado: **+1.072.500** si es `BAJA+2`, **−27.500** en cualquier otro caso.
> - El modelo ordena a los clientes por probabilidad de baja, y la entrega son los primeros N (el **corte**).
>
> ## 3. Pipeline (igual en los dos experimentos)
>
> ### 3.1 Feature engineering (de 155 a 1.305 columnas)
>
> | Paso | Detalle |
> |---|---|
> | Datos rotos | `ccajas_depositos` vale 0 en todo 202105, así que se pasa a `NA` en ese mes |
> | Flags `_zero` | 140 variables: 1 si la original vale 0, 0 si no, NA si es NA (no se rankean ni se laguean) |
> | Totales y ratios de tarjeta | `mv_*` (Master + Visa) y ratios de utilización `mvr_*` (saldo, consumo, pago y pago mínimo sobre el límite), calculados sobre montos crudos |
> | Ranking de montos | 82 variables monetarias reemplazadas por su ranking dentro de cada mes (0 queda fijo, positivos en (0,1], negativos en [−1,0)), para eliminar el efecto de la inflación |
> | Historia | `lag1`, `lag2`, `delta1`, `delta2` de todas las variables |
> | Tendencia | pendiente por cuadrados mínimos (`_tend3`) y promedio (`_avg3`) en una ventana de 3 meses |
> | Manuales | `ctrx_quarter_normalizado` (corrige a los clientes con menos de 3 meses de antigüedad) y `mpayroll_sobre_edad` |
> | Transiciones | cambios de estado de tarjeta y de mora mes a mes, flags de "prende/apaga" de actividad, payroll y consumos, y `n_canales_apagados` |
>
> ### 3.2 Target y pesos
>
> - Clase binaria `clase01` = 1 para `BAJA+1` y `BAJA+2`.
> - Peso 0,25 a los `BAJA+1` y 1,0 al resto, para que el modelo priorice los `BAJA+2`.
>
> ### 3.3 Limpieza de registros dudosos
>
> Un modelo auxiliar chico (`modelo30`: 2.180 árboles, 30 hojas) puntúa cada registro. Se eliminan los `CONTINUA` con `prob30 > 0.5`, que son clientes que se ven como bajas y confunden al entrenamiento.
>
> - **En la bayesiana:** `modelo30` se entrena con el 30% (fold 2) y limpia el 70% (fold 1). Se eliminan 161 `CONTINUA`.
> - **En el modelo final:** *cross-fitting* 50/50 sobre 202103–202106. Cada mitad se puntúa con un modelo entrenado en la otra, así ningún registro se evalúa con un modelo que lo vio. Se eliminan 304 `CONTINUA`.
>
> ### 3.4 Optimización bayesiana
>
> - Entrenamiento 202103 + 202104 (fold 1 limpio) y validación 202106. Métrica: AUC.
> - `mlr3mbo`, surrogate kriging y expected improvement.
> - Espacio de búsqueda: `num_iterations` [64, 4096], `num_leaves` [16, 2048], `min_sum_hessian_in_leaf` [1e-6, 0.1], `feature_fraction` [0.1, 0.9].
> - Fijos: `learning_rate` 0,005, `min_data_in_leaf` 0, `max_bin` 31, sin bagging.
>
> ### 3.5 Modelo final
>
> - Entrenamiento en **202103 a 202106** (limpio), predicción sobre **202108**.
> - Se entrena el mismo modelo con varias semillas y se **promedian las probabilidades**.
>
> ## 4. Los dos experimentos
>
> | | **j4955** (HT4955-01) | **j4957** (HT4957-01) |
> |---|---|---|
> | `feature_fraction_bynode` | 1.0 | 0.2 |
> | Hiperparámetros | bayesiana del **j4953** (copiados a mano en el notebook) | bayesiana propia, 40 iteraciones (5,5 h) |
> | `num_iterations` | 3606 | 2652 |
> | `num_leaves` | 1443 | 1642 |
> | `min_sum_hessian_in_leaf` | 0,0875 | 0,0896 |
> | `feature_fraction` | 0,120 | 0,110 |
> | AUC en la bayesiana | 0,91348 | 0,91353 |
> | Semillas en el modelo final | 3 | 12 |
>
> Las dos bayesianas llegaron prácticamente a la misma zona y al mismo AUC. Lo que distingue a los modelos es el `bynode` y la cantidad de semillas.
>
> ### 4.1 Origen de los hiperparámetros del j4955
>
> El j4955 **no corre su propia optimización bayesiana**, para no repetir una corrida de varias horas. Usa los mejores hiperparámetros encontrados por la bayesiana del experimento **j4953** (`notebooks/j4953_competencia.ipynb`, log completo en `bayesianas/HT4953-01_BO_log.txt`).
>
> En `j4955_competencia.ipynb`, las celdas de la bayesiana están comentadas y los hiperparámetros se cargan a mano, en la celda bajo el título *"IMPORTANTE, HARDCODEO ESTO PARA NO CORRER TODA LA BAYESIANA"*:
>
> ```r
> PARAM$out$lgbm$mejores_hiperparametros <- list(
>   num_iterations          = 3606,
>   num_leaves              = 1443,
>   min_sum_hessian_in_leaf = 0.0874518118416699,
>   feature_fraction        = 0.120189655432349
> )
> PARAM$out$lgbm$y <- 0.913479658101473   # AUC de esa configuración en la bayesiana del j4953
> ```
>
> Esos valores son la **fila de mayor `metrica`** del `BO_log.txt` del j4953.
>
> <!-- COMPLETAR: diferencias de configuración entre j4953 y j4955, si las hay (por ejemplo feature_fraction_bynode o cambios de features). Si no hay ninguna, dejar: "La configuración del j4953 es idéntica a la del j4955; solo cambia que el j4955 no ejecuta la bayesiana." -->
>
> **Cómo proceder para reproducirlo:**
>
> 1. Correr `j4953_competencia.ipynb` completo, incluida la bayesiana. Deja `~/buckets/b1/exp/HT4953-01/BO_log.txt`.
> 2. Tomar la mejor fila de ese log:
>    ```r
>    tb <- fread("~/buckets/b1/exp/HT4953-01/BO_log.txt")
>    setorder(tb, -metrica)
>    tb[1, .(num_iterations, num_leaves, min_sum_hessian_in_leaf, feature_fraction, metrica)]
>    ```
> 3. Verificar que coincidan con los valores hardcodeados en el j4955 (o reemplazarlos por los obtenidos) y correr `j4955_competencia.ipynb`.
>
> También se puede omitir el paso 1 y usar directamente los valores del log que está en `bayesianas/HT4953-01_BO_log.txt`.
>
> ## 5. Evaluación
>
> ### 5.1 Backtest en 202106
>
> Entrenamiento 202103 + 202104 y test en 202106 (que sí tiene clase), con 5 semillas. Ganancia total, en millones:
>
> | Envíos | j4955 (media) | j4957 (media) | j4955 (ensamble) | j4957 (ensamble) |
> |---|---|---|---|---|
> | 13.200 | 405,5 | 417,3 | 408,1 | 420,2 |
> | 14.200 | 400,0 | 416,9 | 403,7 | 426,8 |
> | 15.000 | 400,2 | 417,3 | 399,3 | 423,5 |
> | Mejor corte | 13.200 → 405,5 | 11.600 → 419,8 | 12.200 → 408,1 | 14.200 → 426,8 |
>
> El j4957 gana en el backtest, pero **ese resultado está sesgado a su favor**: su bayesiana eligió los hiperparámetros validando justamente en 202106. Además, la variación entre semillas del j4957 (~20 M entre la mejor y la peor) es casi del mismo tamaño que la diferencia entre los modelos.
>
> ### 5.2 Public leaderboard (202108, 30% de los clientes)
>
> | Envíos | j4955 | j4957 | **Blend** |
> |---|---|---|---|
> | 10.500 | | | 106,34 |
> | 11.000 | 109,84 | 102,25 | 107,17 |
> | 11.400 | 109,45 | 103,04 | |
> | 11.500 | | | 109,15 |
> | 11.600 | 108,16 | 102,60 | |
> | 11.800 | 107,00 | 102,19 | |
> | 12.000 | 106,70 | 104,20 | **107,77** |
> | 12.500 | | | 105,79 |
> | 13.000 | | | 104,45 |
> | 13.500 | | | 102,19 |
> | 14.000 | | | 99,69 |
> | 14.200 | | 99,63 | |
> | 14.500 | | | 101,92 |
>
> En el public, el j4957 queda por debajo del j4955 en todos los cortes comparables (3 a 8 M), aunque la diferencia se achica hacia 12.000. El blend queda entre los dos modelos con 11.000 envíos, empata con el j4955 alrededor de 11.500 y **con 12.000 supera a ambos** (107,77 contra 106,70 y 104,20). Todas estas diferencias son de 1 a 8 M, o sea 1–7 `BAJA+2`. El public tiene un ruido de alrededor de ±10 M (son ~49 mil clientes y unos 220 `BAJA+2` entre los enviados), así que diferencias de ese tamaño no son concluyentes.
>
> ## 6. Blend
>
> ### 6.1 Qué hace
>
> Combina los rankings de los dos modelos en uno solo:
>
> 1. Cada modelo le asigna una probabilidad a **todos** los clientes de 202108 (`prediccion_promedio.txt`, que ya es el promedio de sus semillas).
> 2. Cada probabilidad se convierte en un **puesto** dentro de su modelo.
> 3. Se **promedian los dos puestos** de cada cliente.
> 4. Se ordena por ese promedio y se envía a los primeros N.
>
> Ejemplo:
>
> | Cliente | Puesto j4955 | Puesto j4957 | Promedio | Puesto final |
> |---|---|---|---|---|
> | A | 2 | 1 | 1,5 | 1 |
> | B | 1 | 3 | 2,0 | 2 |
> | C | 3 | 2 | 2,5 | 3 |
>
> Los clientes que **los dos modelos** ponen arriba quedan arriba. Los que solo uno pone arriba bajan a una posición intermedia.
>
> Se promedian **puestos y no probabilidades** para que los dos modelos pesen exactamente la mitad, aunque sus probabilidades estén en escalas distintas. Para elegir los primeros N solo importa el orden.
>
> ### 6.2 Por qué un blend
>
> - En el public gana el j4955 y en el backtest gana el j4957 (este último con el sesgo explicado arriba). Las dos señales apuntan para lados opuestos y son del tamaño del ruido. No hay un ganador claro.
> - Cada modelo se equivoca en clientes distintos (tienen distinto `bynode` y distintos hiperparámetros). Al promediar, los errores que comete uno solo pierden peso.
> - Para el private (el 70% restante) es la opción con menos riesgo: no depende de haber acertado cuál de los dos modelos es mejor.
>
> ### 6.3 Elección del corte: 12.000
>
> - En el public, el blend rinde mejor entre 11.000 y 12.000 envíos y baja de forma sostenida a partir de 12.500.
> - Con 12.000 envíos, el blend es la mejor de las tres opciones en el public: blend 107,77, j4955 106,70 y j4957 104,20.
> - El backtest de 202106 ubicaba el óptimo más arriba (12.200–14.200).
> - 12.000 queda en el borde alto de la zona buena del public y más cerca del óptimo del backtest. No se eligió el máximo exacto del public (11.500), porque entre cortes vecinos la diferencia es de 1–2 `BAJA+2`, es decir, ruido.
>
> ## 7. Cómo reproducir
>
> Todos los notebooks usan kernel R.
>
> 1. *(Opcional)* Correr `notebooks/j4953_competencia.ipynb`, que contiene la bayesiana que dio origen a los hiperparámetros del j4955. Ver la sección 4.1. Si se omite, se usan los valores ya cargados en el j4955, que coinciden con `bayesianas/HT4953-01_BO_log.txt`.
> 2. Correr `notebooks/j4955_competencia.ipynb`. Genera `~/buckets/b1/exp/HT4955-01/prediccion_promedio.txt`.
> 3. Correr `notebooks/j4957_competencia.ipynb` (incluye su bayesiana, de ~5,5 h). Genera `~/buckets/b1/exp/HT4957-01/prediccion_promedio.txt`.
> 4. Correr `notebooks/blend_j4955_j4957.ipynb`. Solo lee esos dos archivos y escribe los CSV de envío en `~/buckets/b1/exp/BLEND-4955-4957/`.
>
> Semilla primigenia: 600013.

