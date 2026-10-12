# Laura Pasquini — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: laupasq1967
- Repositorio: https://github.com/laupasq1967/Entrega-final-DMEyF
- Link posteado: https://github.com/laupasq1967/Entrega-final-DMEyF.git
- Commit: 395462d7043b7d42b1558dc2f243b04978dead59
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/laupasq1967/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/laupasq1967.json

## Resumen

La entrega está en la carpeta repo_entrega: una notebook final en R, la lista de 576 variables que esa notebook lee, un README y la carpeta procesamiento_previo, con 16 notebooks y archivos de apoyo que documentan de dónde salen los hiperparámetros y las listas de variables. La notebook final lee competencia_01.csv, pasa a NA los ceros de ccajas_depositos en 202105, calcula lag 1, lag 2, delta 1 y delta 2 de todas las variables numéricas y aplica un ranking por mes con el cero fijo (ceros en 0, resto en escala de 1 a 100). Arma dos conjuntos de variables: A'plus (576: seleccionadas con canaritos, con promedio, máximo, mínimo, cocientes y tendencia de 3 meses, variables compuestas y gen_1) y B (todas las originales con sus lags y deltas, sin foto_mes ni numero_de_cliente). Entrena LightGBM con clase binaria (BAJA+1 o BAJA+2 = 1) sobre 202103 a 202106, con hiperparámetros fijos y 100 semillas por modelo, y predice 202108. Convierte cada predicción en percentil, promedia las semillas de cada modelo, promedia A'plus y B y escribe los 10.600 clientes de mayor puntaje. Según el README, ese archivo obtuvo 119,3775 en el Public Leaderboard.

**Qué entrega.** Un CSV sin encabezado, Aprimaplus_B100_corte10600.csv, con el numero_de_cliente de los 10.600 clientes de mayor puntaje del ensamble para 202108. El README lo presenta como el archivo del último envío (10.600 clientes con Predicted = 1). La notebook escribe además scores_Aprimaplus_B100_202108.csv, con los puntajes de todos los clientes, y un archivo .rds por semilla y modelo en la carpeta rankings. Los archivos de salida no están en el repositorio.

**Cómo se ejecuta.** Según repo_entrega/README.md: 1) dejar competencia_01.csv en la carpeta de datasets y variables_A_Aprimaplus.txt junto a la notebook; 2) cambiar en la primera celda de código las dos rutas (carpeta de datasets y carpeta de salida); 3) ejecutar completa Notebook_final_reproducible_Aprimaplus_B100.ipynb con R y el kernel IRkernel, con N_SEMILLAS = 100. El README indica unas 11 horas en una PC con 20 GB de RAM, que la corrida es reanudable (saltea las semillas que ya tienen ranking guardado) y que con N_SEMILLAS = 1 sirve de verificación en 1 h 20 min. También indica que la carpeta procesamiento_previo no hace falta ejecutarla.

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase01): 1 si clase_ternaria es BAJA+1 o BAJA+2, 0 en otro caso, en los dos modelos (líneas 274 y 301 de la notebook final). El README resume el objetivo como 'clase_ternaria BAJA+2'.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** —
- **Mes que predice:** 202108
- **Submuestreo:** La notebook final no submuestrea: entrena con todas las filas de 202103 a 202106. El submuestreo de CONTINUA al 10 % (con peso 10 por fila) aparece sólo en la optimización bayesiana de procesamiento_previo.
- **Calidad de datos:** Los ceros de ccajas_depositos en 202105 se pasan a NA antes de calcular los lags. Del modelo A'plus se sacan las variables cuyo nombre contiene Master_fultimo_cierre, Visa_fultimo_cierre o Visa_mpagado, con sus derivadas. Un comentario de z_exportar_datasets_A_B_rankeados lista otras variables con un mes anómalo (Visa_Finiciomora, Visa_mpagado, Master_fultimo_cierre, Visa_fultimo_cierre) que no se corrigen.
- **Drifting:** Ranking con cero fijo por mes: dentro de cada foto_mes y para cada variable numérica, los ceros quedan en 0, los valores distintos de cero (negativos y positivos juntos) se ordenan con frank (empates al promedio) y se llevan a una escala de 1 a 100, y los NA quedan NA. Se aplica a originales, lags, deltas y variables históricas. No hay deflación. En el modelo B se excluye foto_mes como variable.
- **Variables dentro del mes:** Sólo en A'plus y calculadas sobre valores ya rankeados: sumas de variables de tarjetas Visa y Master (consumo, saldo, límite, pago mínimo, descuentos), de payroll, de préstamos prendarios e hipotecarios, de inversiones, de plazos fijos y de comisiones; utilizacion_tarjetas (consumo/límite); tarjetas_activas_count; transferencias_netas (recibidas − emitidas); y gen_1 = ctrx_quarter + cpayroll_trx_min3. El código contempla 15 compuestas; 10 de ellas figuran en variables_A_Aprimaplus.txt, además de gen_1.
- **Variables históricas:** Lag 1 y lag 2 (shift por cliente sobre el dataset ordenado por cliente y mes) y delta 1 y delta 2 (actual − lag) de todas las variables numéricas, calculados antes de rankear. Para A'plus, además, sobre la ventana actual + lag 1 + lag 2: promedio (_avg3), máximo (_max3), mínimo (_min3), cociente actual/promedio (_ratio_avg), cociente actual/máximo (_ratio_max) y tendencia ((actual − lag 2)/2, o actual − lag 1 si falta lag 2). B usa originales, lags y deltas (760 variables según el README).
- **Selección de variables:** A'plus usa una lista fija de 576 variables leída de variables_A_Aprimaplus.txt; la notebook detiene la ejecución si la lista que arma no coincide en cantidad y orden. Según el README y los notebooks de procesamiento_previo, la lista sale de canaritos: se agrega un 20 % de variables al azar, se entrena un LightGBM, se numera cada variable por su posición en la importancia (Gain) y se conservan las reales con posición menor a la media + 2 desvíos de las posiciones de los canaritos. Lista A: 358 variables con 202103+202104; lista A': intersección de dos semillas con 202105+202106 (526); unión = 575, más gen_1. En esas corridas cprestamos_personales y mprestamos_personales no entran como candidatas. B no tiene selección: usa todas las columnas menos las claves y la clase.
- **Optimización de hiperparámetros:** La notebook final no optimiza: los valores están escritos. En procesamiento_previo hay: optimización bayesiana con mlrMBO (experimento 4961: 11 hiperparámetros, 100 iteraciones, validación cruzada de 5 folds sobre 202104 con submuestreo 0,1 y la ganancia como métrica); comparación de los 3 y los 5 trials de mayor ganancia interna con 10 semillas sobre 202106; grillas de learning_rate × scale_pos_weight (25 y 56 combinaciones) y de min_data_in_leaf, medidas con ganancia en 202106. Según el README se toman del trial 2 de la BO feature_fraction, num_leaves, min_gain_to_split, lambda_l1, lambda_l2 y bagging_fraction, y de las grillas learning_rate 0,02, scale_pos_weight 0,5 y min_data_in_leaf 4000 (A'plus) y 1000 (B); las 600 iteraciones quedan fijadas sin grilla propia.
- **Hiperparámetros finales:** Comunes a los dos modelos: boosting gbdt, objective binary, num_iterations 600, learning_rate 0,02, feature_fraction 0,1541961, num_leaves 1684, lambda_l1 1,520327, lambda_l2 7,548036, min_gain_to_split 0,2158453, bagging_fraction 0,8425105, bagging_freq 6, scale_pos_weight 0,5, max_bin 31, max_depth −1, min_sum_hessian_in_leaf 0,001. min_data_in_leaf: 4000 en A'plus y 1000 en B.
- **Semillas:** 100 semillas por modelo, las mismas para A'plus y B: 10 escritas en el código (585581, 249449, 655649, 503039, 798191, 112909, 334667, 421303, 667021, 887923), 20 primos escritos entre 100003 y 100271 y los 70 primeros primos a partir de 100272, calculados en el código. Cada semilla se pasa como seed de LightGBM y a set.seed con L'Ecuyer-CMRG. En total, 200 entrenamientos.
- **Cantidad de semillas:** 100
- **Ensamble:** Dos niveles, sobre percentiles: cada predicción de una semilla se convierte en frank(prob)/n; se promedian las 100 semillas de cada modelo (rA y rB); el puntaje final es (rA + rB)/2. Los dos modelos difieren en el conjunto de variables (576 de A'plus contra todas las originales con lags y deltas de B) y en min_data_in_leaf.
- **Corte:** Cantidad fija: los 10.600 clientes de mayor puntaje final (CORTE_FINAL). Según la celda de presentación de la notebook, el valor se eligió mirando la curva ganancia–corte del Public; ese análisis no está en el código.
- **Validación:** La notebook final no calcula ganancia ni separa un mes de validación; sólo compara, si existen en rutas locales, el archivo generado con el entregado y el ranking de la primera semilla con el original. En procesamiento_previo las decisiones se miden entrenando con 202104 o con 202103+202104 y prediciendo 202106, con la ganancia de la competencia (1.072.500 por BAJA+2 y −27.500 por el resto) y 10 semillas (3 en las etapas de descarte); la mayoría usa un corte fijo de 12.000 envíos, y las comparaciones de trials y la grilla sobre el trial 2 toman el corte de mayor ganancia entre 4.000 y 19.000. La BO usa validación cruzada de 5 folds dentro de 202104.
- **Salidas:** En la carpeta de salida: rankings/rank_MODELO_sSEMILLA.rds (uno por semilla y modelo, 200 con N_SEMILLAS = 100), Aprimaplus_B100_corte10600.csv (10.600 ids, sin encabezado) y scores_Aprimaplus_B100_202108.csv (numero_de_cliente, rank_Aplus, rank_B, rank_final). Ninguno está incluido en el repositorio.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Mínimos y máximos de ventana (`variables.min_max_ventana`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Búsqueda en grilla o al azar (`hiperparametros.grilla_o_azar`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)
- El repositorio declara el uso de asistentes de IA (`proceso.uso_de_ia_declarado`)

## Técnicas sólo exploradas

- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Validación cruzada (`validacion.validacion_cruzada`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README: R 4.5.3, Windows, 20 GB de RAM, paquetes data.table y lightgbm 4.7.0, kernel IRkernel. La notebook final imprime las versiones de lightgbm, data.table y R y llama a sessionInfo(). Las rutas del código apuntan a C:/Users/Laura/Documents/DMEyF/.

## Pasos del camino de la entrega

1. **Insumos fijos: lista de variables e hiperparámetros.** La notebook final parte de dos insumos ya decididos: la lista ordenada de 576 variables de A'plus (variables_A_Aprimaplus.txt) y los hiperparámetros escritos en el código. El README explica su origen en procesamiento_previo: optimización bayesiana y grillas para los hiperparámetros, canaritos y algoritmo genético para las variables. (`repo_entrega/variables_A_Aprimaplus.txt` líneas 1–576; `repo_entrega/README.md` líneas 64–93)
2. **Configuración de la corrida.** Define rutas, meses de entrenamiento (202103 a 202106), mes a predecir (202108), la corrección de ccajas_depositos, el corte de 10.600, las 100 semillas y los hiperparámetros de los dos modelos (param_A con min_data_in_leaf 4000 y param_B con 1000). (`repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb` líneas 37–101)
3. **Lectura del dataset y chequeos.** Lee competencia_01.csv, que ya trae clase_ternaria, muestra las filas por mes y clase y detiene la ejecución si falta la clase, si no está 202108 o si hay filas de entrenamiento sin clase. Ordena por cliente y mes. (`repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb` líneas 106–117)
4. **Corrección de ceros en ccajas_depositos.** Los valores 0 de ccajas_depositos en 202105 pasan a NA. (`repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb` líneas 122–128)
5. **Lags y deltas de 1 y 2 meses.** Para cada variable numérica calcula por cliente el valor de una y de dos filas atrás (lag 1 y lag 2) y la diferencia del valor actual con cada uno (delta 1 y delta 2), sobre los valores originales. Después conserva sólo los meses 202103 a 202106 y 202108. (`repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb` líneas 134–153)
6. **Función de ranking con cero fijo.** Define la transformación por mes y por variable: los ceros quedan en 0, los valores distintos de cero se ordenan y se escalan de 1 a 100 y los NA se mantienen. (`repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb` líneas 159–184)
7. **Dataset de A'plus: variables históricas y ranking.** Lee la lista de variables, arma dataset_A con las columnas necesarias y calcula promedio, máximo, mínimo, cocientes y tendencia de 3 meses para las variables base que la lista pide, sin las que coinciden con el patrón Master_fultimo_cierre, Visa_fultimo_cierre o Visa_mpagado. Luego rankea dataset_A. (`repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb` líneas 190–241)
8. **Variables compuestas, gen_1 y clase binaria de A'plus.** Sobre los valores rankeados suma pares o ternas de variables, calcula utilizacion_tarjetas, tarjetas_activas_count, transferencias_netas y gen_1 = ctrx_quarter + cpayroll_trx_min3, y crea clase01 (BAJA+1 o BAJA+2 = 1). Comprueba que las variables armadas coincidan con el archivo y construye las matrices de entrenamiento y de 202108. (`repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb` líneas 243–291)
9. **Dataset de B.** Rankea el dataset completo (originales, lags y deltas), crea clase01 y usa como variables todas las columnas menos clase_ternaria, clase01, numero_de_cliente y foto_mes. Verifica que los clientes de 202108 y la etiqueta coincidan con los de A'plus. (`repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb` líneas 296–316)
10. **Entrenamiento por semilla y por modelo.** Para cada una de las 100 semillas y cada modelo entrena un LightGBM con lgb.train sobre 202103 a 202106, predice 202108 y guarda el percentil de cada cliente (frank(prob)/n) en un archivo .rds; si el archivo ya existe, saltea esa semilla. (`repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb` líneas 322–344)
11. **Ensamble, corte y archivo de salida.** Promedia los percentiles de las semillas de cada modelo, promedia A'plus y B, ordena de mayor a menor y escribe los primeros 10.600 numero_de_cliente en un CSV sin encabezado. Escribe también los puntajes de todos los clientes y verifica el formato del archivo. (`repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb` líneas 350–369)
12. **Comparaciones opcionales con la corrida original.** Si existen en rutas locales, compara el archivo generado con el entregado (cantidad de clientes en común y orden) y el ranking de la primera semilla con el guardado en la corrida original (correlación de Spearman). Llama a sessionInfo(). (`repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb` líneas 375–403)

## Archivos

- `README.md` · explicacion · Markdown · 3 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/README.md.txt) — Texto de la raíz del repositorio: indica que todo el contenido de la entrega (notebook final, README con las instrucciones de replicación y notebooks de procesamiento previo) está en la carpeta repo_entrega.
- `repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb` · principal · Jupyter (R) · 403 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb.txt) — Notebook en R que genera el archivo entregado: prepara los datos, arma los conjuntos de variables A'plus y B, entrena LightGBM con 100 semillas por modelo sobre 202103 a 202106, ensambla por promedio de percentiles y escribe los 10.600 clientes de mayor puntaje para 202108.
- `repo_entrega/variables_A_Aprimaplus.txt` · configuracion · Texto · 576 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/variables_A_Aprimaplus.txt.txt) — Lista ordenada de las 576 variables del modelo A'plus, una por línea, que la notebook final lee y contra la que verifica las variables que arma. Contiene 74 nombres sin sufijo histórico (originales, 10 compuestas y gen_1 en la última línea), 72 _ratio_avg, 68 _avg3, 61 _max3, 61 _ratio_max, 51 _min3, 42 _lag1, 41 _lag2, 37 _delta1, 35 _delta2 y 34 _tendencia. No se observa en el código qué notebook escribe el archivo con este nombre; z_exportar_datasets_A_B_rankeados escribe la misma construcción (unión de listas + gen_1) como variables_A.txt.
- `repo_entrega/README.md` · explicacion · Markdown · 108 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/README.md.txt) — Presentación de la entrega: archivo enviado y puntaje declarado, estructura de carpetas, tabla que relaciona cada notebook de procesamiento_previo con lo que documenta, pasos para replicar, tiempos medidos, descripción del modelo y del ensamble, origen de los hiperparámetros (BO, selección del trial, grillas) y de las listas de variables (canaritos, algoritmo genético), otras optimizaciones probadas que no se incluyen en el repositorio, verificación realizada, entorno y declaración de uso de Claude como asistente.
- `repo_entrega/procesamiento_previo/z_verificacion_gen1_sobre_ganadora.ipynb` · secundario · Jupyter (R) · 203 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z_verificacion_gen1_sobre_ganadora.ipynb.txt) — Compara la lista de 358 variables con y sin gen_1 (359), primero con 3 semillas y luego con 10, entrenando con 202103+202104 y midiendo la ganancia en 202106 con corte fijo de 12.000.
- `repo_entrega/procesamiento_previo/z_exportar_datasets_A_B_rankeados.ipynb` · secundario · Jupyter (R) · 293 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z_exportar_datasets_A_B_rankeados.ipynb.txt) — Repite la preparación de datos de la notebook final (corrección de ccajas_depositos, lags, deltas, variables históricas, ranking cero fijo, compuestas y gen_1), arma la lista de A'plus como unión de la lista A (358) y la intersección de las dos listas de 202105+202106, y exporta los datasets de A'plus y de B a parquet o csv.gz junto con variables_A.txt y variables_B.txt. No entrena modelos. El README lo describe como auxiliar.
- `repo_entrega/procesamiento_previo/z_grilla_rankeado_lags.ipynb` · secundario · Jupyter (R) · 119 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z_grilla_rankeado_lags.ipynb.txt) — Grilla de min_data_in_leaf (460, 1000, 2000, 3500, 5000) para la configuración B sobre un dataset con lags ya rankeado, con 10 semillas por valor, entrenamiento en 202104, ganancia en 202106 y corte fijo de 12.000.
- `repo_entrega/procesamiento_previo/z494_TareaHogar_04_TerceraCapa_SalsaMagica.ipynb` · secundario · Jupyter (R) · 741 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z494_TareaHogar_04_TerceraCapa_SalsaMagica.ipynb.txt) — Notebook sobre la plantilla de la Tarea Hogar 04 de la materia. Genera clase_ternaria a partir del archivo crudo y escribe competencia_01.csv. Corre una optimización bayesiana con mlrMBO (experimento 4961, semilla 585581): 11 hiperparámetros de LightGBM, 100 iteraciones, lgb.cv de 5 folds sobre 202104 con submuestreo de CONTINUA al 10 % y peso 10, sin cprestamos_personales ni mprestamos_personales, y como métrica la ganancia con umbral de probabilidad 0,025. Guarda BO_log.txt y PARAM.yml, entrena un modelo con los hiperparámetros de mayor ganancia sobre 202104 (min_data_in_leaf dividido por 0,1), predice 202106 e imprime la ganancia para cortes de 4.000 a 19.000 de a 500.
- `repo_entrega/procesamiento_previo/z_grilla_min_data_lags.ipynb` · secundario · Jupyter (R) · 221 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z_grilla_min_data_lags.ipynb.txt) — Grilla de min_data_in_leaf sobre un dataset con lags y deltas sin rankear, para dos configuraciones de hiperparámetros llamadas Modelo A (1.351 iteraciones, feature_fraction 0,5153582) y Modelo B (600 iteraciones, feature_fraction 0,1541961). Para cada valor mide el porcentaje de Gain que toman los canaritos y la ganancia media y el desvío con 10 semillas en 202106.
- `repo_entrega/procesamiento_previo/z_modeloA_gen1_v2.ipynb` · secundario · Jupyter (R) · 191 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z_modeloA_gen1_v2.ipynb.txt) — Compara dos variantes del modelo A de 358 variables + gen_1 con 10 semillas: gen_1 sin rankear y gen_1 con ranking cero fijo por mes, con entrenamiento en 202103+202104, ganancia en 202106 y corte fijo de 12.000.
- `repo_entrega/procesamiento_previo/z_grid_lr_scalePosWeight.ipynb` · secundario · Jupyter (R) · 287 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z_grid_lr_scalePosWeight.ipynb.txt) — Grilla de 56 combinaciones de learning_rate × scale_pos_weight sobre 359 variables (lista de 358 + gen_1), en etapas: 1 semilla para todas, 3 semillas para las 5 primeras y 10 semillas para la primera, con entrenamiento en 202103+202104, ganancia en 202106 y corte fijo de 12.000.
- `repo_entrega/procesamiento_previo/z_canaritos_202105_06.ipynb` · secundario · Jupyter (R) · 218 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z_canaritos_202105_06.ipynb.txt) — Repite la selección con canaritos entrenando con 202105+202106 y con dos semillas (585581 y 249449), escribe las listas de cada semilla y las compara entre sí y con la lista de 202103+202104. Según el README, la intersección de las dos listas de 2 desvíos es la lista A' de 526 variables.
- `repo_entrega/procesamiento_previo/z_overnight_canaritos_genetico.ipynb` · secundario · Jupyter (R) · 320 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z_overnight_canaritos_genetico.ipynb.txt) — Notebook en tres partes: una poda con 30 canaritos (umbral = Gain máximo de los canaritos), un algoritmo genético que busca combinaciones de dos variables con +, −, × o ÷ usando como aptitud el AUC univariado contra clase01, y una prueba de las 10 primeras combinaciones con 3 semillas en 202106. Según el README, de la parte 2 sale gen_1 = ctrx_quarter + cpayroll_trx_min3.
- `repo_entrega/procesamiento_previo/z601_BO_Diagnostico.ipynb` · secundario · Jupyter (R) · 120 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z601_BO_Diagnostico.ipynb.txt) — Lee el BO_log.txt del experimento 4961 y grafica el historial de la optimización, la importancia de cada hiperparámetro, la relación de cada hiperparámetro con la ganancia y un mapa de learning_rate × scale_pos_weight.
- `repo_entrega/procesamiento_previo/z601_Top3Trials_NSemillas.ipynb` · secundario · Jupyter (R) · 142 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z601_Top3Trials_NSemillas.ipynb.txt) — Toma del BO_log.txt los 3 trials de mayor ganancia interna y entrena cada uno con 10 semillas sobre 202104, prediciendo 202106, para comparar media, desvío, mínimo y máximo de ganancia.
- `repo_entrega/procesamiento_previo/z494_Grilla_LR_ScalePosWeight_Trial2.ipynb` · secundario · Jupyter (R) · 294 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z494_Grilla_LR_ScalePosWeight_Trial2.ipynb.txt) — Grilla de 25 combinaciones (learning_rate 0,01, 0,02, 0,03, 0,05, 0,08 × scale_pos_weight 0,3, 0,5, 0,62, 1, 2) sobre los hiperparámetros del trial 2 de la BO (930 iteraciones, min_data_in_leaf 46 dividido por 0,1). Entrena con 202104 y una semilla (585581), predice 202106 y, para cada combinación, registra el corte de mayor ganancia entre 4.000 y 19.000. Escribe grilla_lr_spw_trial2.txt.
- `repo_entrega/procesamiento_previo/z_canaritos_asesinos.ipynb` · secundario · Jupyter (R) · 235 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z_canaritos_asesinos.ipynb.txt) — Selección de variables con canaritos sobre 202103+202104: agrega un 20 % de variables al azar, entrena un LightGBM, numera las variables por su posición en la importancia y conserva las reales con posición menor a la media + 1 desvío y a la media + 2 desvíos de las posiciones de los canaritos. Escribe las dos listas; la de 2 desvíos es la lista A de 358 variables según el README.
- `repo_entrega/procesamiento_previo/z_grilla_min_data_in_leaf_canaritos.ipynb` · secundario · Jupyter (R) · 206 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z_grilla_min_data_in_leaf_canaritos.ipynb.txt) — Grilla de min_data_in_leaf sobre las variables originales de competencia_01.csv, para dos configuraciones de hiperparámetros (A: valores 1, 50, 150, 460, 1000, 2000; B: 460, 1000, 2000, 3500). Para cada valor mide el porcentaje de Gain de los canaritos y la ganancia con 10 semillas en 202106 con corte fijo de 12.000.
- `repo_entrega/procesamiento_previo/z_grilla_mdl_modeloA.ipynb` · secundario · Jupyter (R) · 166 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z_grilla_mdl_modeloA.ipynb.txt) — Grilla de min_data_in_leaf (300, 500, 1000, 2000, 3000, 4000, 5000) para el modelo A de 358 variables + gen_1, con 10 semillas por valor, entrenamiento en 202103+202104, ganancia en 202106 y corte fijo de 12.000.
- `repo_entrega/procesamiento_previo/z601_Top5Trials_NSemillas.ipynb` · secundario · Jupyter (R) · 141 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/z601_Top5Trials_NSemillas.ipynb.txt) — Igual que z601_Top3Trials_NSemillas pero con los 5 trials de mayor ganancia interna del BO_log.txt: 10 semillas por trial, entrenamiento en 202104 y ganancia en 202106.
- `repo_entrega/procesamiento_previo/archivos_de_apoyo/BO_log.txt` · secundario · Texto · 145 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/archivos_de_apoyo/BO_log.txt.txt) — Tabla separada por tabuladores con las 144 evaluaciones de la optimización bayesiana del experimento 4961, ordenadas de mayor a menor ganancia interna (columna y): los 11 hiperparámetros de cada evaluación y columnas propias de mlrMBO (dob, exec.time, ei, prop.type, entre otras). La primera fila tiene y = 256.245.000 y la segunda, y = 253.660.000.
- `repo_entrega/procesamiento_previo/archivos_de_apoyo/campos_canaritos_asesinos_2sd.txt` · secundario · Texto · 359 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/archivos_de_apoyo/campos_canaritos_asesinos_2sd.txt.txt) — Lista de 358 variables (más una línea de encabezado) que escribe z_canaritos_asesinos con el criterio media + 2 desvíos sobre 202103+202104; el README la llama lista A.
- `repo_entrega/procesamiento_previo/archivos_de_apoyo/campos_canaritos_202105_06_s585581_2sd.txt` · secundario · Texto · 577 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/archivos_de_apoyo/campos_canaritos_202105_06_s585581_2sd.txt.txt) — Lista de 576 variables (más encabezado) que escribe z_canaritos_202105_06 con la semilla 585581 y el criterio media + 2 desvíos sobre 202105+202106.
- `repo_entrega/procesamiento_previo/archivos_de_apoyo/PARAM.yml` · secundario · YAML · 260 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/archivos_de_apoyo/PARAM.yml.txt) — Volcado en YAML de la lista PARAM del experimento 4961: rutas, semilla 585581, meses (train 202104, future 202106), cortes, submuestreo 0,1, 5 folds, 100 iteraciones, parámetros fijos de LightGBM, espacio de búsqueda de los 11 hiperparámetros y los hiperparámetros de mayor ganancia interna (1.351 iteraciones, learning_rate 0,05475, min_data_in_leaf 1, y = 256.245.000).
- `repo_entrega/procesamiento_previo/archivos_de_apoyo/genetico_top_features.txt` · secundario · Texto · 2 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/archivos_de_apoyo/genetico_top_features.txt.txt) — Salida del algoritmo genético de z_overnight_canaritos_genetico: encabezado y una sola combinación, ctrx_quarter + cpayroll_trx_min3, con aptitud (AUC univariado) 0,8752.
- `repo_entrega/procesamiento_previo/archivos_de_apoyo/campos_canaritos_202105_06_s249449_2sd.txt` · secundario · Texto · 570 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/laupasq1967/repo_entrega/procesamiento_previo/archivos_de_apoyo/campos_canaritos_202105_06_s249449_2sd.txt.txt) — Lista de 569 variables (más encabezado) que escribe z_canaritos_202105_06 con la semilla 249449 y el criterio media + 2 desvíos sobre 202105+202106. La intersección con la lista de la semilla 585581 tiene 526 variables.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### repo_entrega/Notebook_final_reproducible_Aprimaplus_B100.ipynb

Notebook en R que genera el archivo entregado: prepara los datos, arma los conjuntos de variables A'plus y B, entrena LightGBM con 100 semillas por modelo sobre 202103 a 202106, ensambla por promedio de percentiles y escribe los 10.600 clientes de mayor puntaje para 202108.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–32] Celda de texto de presentación: declara el modelo (A'plus + B, 100 semillas cada
#   uno, promedio de rankings, corte 10.600), el resultado en el Public según la propia notebook (119,3775 M),
#   los seis pasos, los requisitos (R 4.5, data.table, lightgbm, unos 20 GB de RAM, competencia_01.csv y
#   variables_A_Aprimaplus.txt), los tiempos medidos y una tabla de decisiones (ranking cero fijo, selección con
#   canaritos, sin Salsa Mágica, foto_mes fuera de B, hiperparámetros fijos, corte).
#%% celda 1 [texto]
# Primera competencia DMEyF 2026 — Notebook final reproducible
**Modelo entregado: A'plus + B, 100 semillas de cada uno, ensamble por promedio de rankings, corte 10.600.**
Resultado en el Public del bot: **119,3775 M** (archivo `Aprimaplus_B100_corte10600.csv`).

## Qué hace (de punta a punta)
1. Lee `competencia_01.csv` (ya trae `clase_ternaria`) y corrige un cero roto (`ccajas_depositos` en 202105 → NA).
2. Calcula para cada cliente los **rezagos de 1 y 2 meses** (`_lag1`, `_lag2`) y las **diferencias con el valor actual** (`_delta1`, `_delta2`) de todas las variables numéricas.
3. **Modelo A'plus** (576 variables): variables seleccionadas con canaritos + variables históricas (promedio, máximo, mínimo, razones y tendencia de 3 meses) + variables compuestas + `gen_1`. Se transforman con el *ranking cero fijo* (ver más abajo).
4. **Modelo B** (todas las variables originales + lags + deltas, rankeadas igual; sin `foto_mes` ni `numero_de_cliente`).
5. Entrena **LightGBM con 100 semillas para A'plus y 100 para B** sobre 202103–202106 y predice 202108.
6. Promedia los rankings (percentiles) de las semillas de cada modelo, promedia A'plus y B, y se queda con los **10.600 clientes** de mayor puntaje.

## Requisitos
- R 4.5 con los paquetes `data.table` y `lightgbm`. RAM: unos 20 GB.
- `competencia_01.csv` (carpeta de datasets del curso).
- `variables_A_Aprimaplus.txt` en la misma carpeta que esta notebook: la lista **ordenada** de las 576 variables de A'plus (575 seleccionadas + `gen_1`). El orden importa: LightGBM elige las columnas de cada árbol según su posición.
- Tiempo medido en una máquina de 20 GB de RAM: ~70 min de preparación (carga, rezagos, ranking y matrices) + ~2 min por semilla de A'plus + ~4 min por semilla de B. Con 100 semillas, **unas 11 h en total**. Es **reanudable**: si se corta, volver a correrla; las semillas ya hechas se saltean (la preparación se repite).
- Para una prueba rápida, poner `N_SEMILLAS <- 10` en la celda de configuración (~2 h). Da un resultado parecido pero **no idéntico** al de 100 semillas.
- Para **verificar el pipeline completo en ~1 h 20 min**, poner `N_SEMILLAS <- 1` y correr hasta el final: la sección 11 compara el ranking de esa semilla con el que ya teníamos guardado. En la corrida de verificación (semilla 585581) los rankings de A'plus y de B resultaron **idénticos** a los originales (Spearman 1).

## Decisiones que conviene conocer (transparencia)
| Tema | Qué se hizo |
|---|---|
| Ranking cero fijo | Variante **propia** (no la fórmula de la cátedra, que no vimos con detalle): por mes y por variable, los valores distintos de cero (negativos y positivos juntos) se ordenan y se escalan de 1 a 100; el cero queda fijo en 0 y los NA siguen NA |
| Selección de variables | Se hizo con canaritos usando etiquetas hasta 202106. Por eso la validación en 202106 sale **optimista** para el modelo A; la decisión final se apoyó en el Public del bot y no solo en esa validación |
| Salsa Mágica | No se usa (no se excluyen `cprestamos_personales` ni `mprestamos_personales`) |
| `foto_mes` | Se excluye de B: con 202108 como mes a predecir sería un valor nunca visto en el entrenamiento |
| Hiperparámetros | Fijos y los mismos en las 100 semillas (los del ensamble que dio 472,23 M en validación); no se reoptimizan acá |
| Corte | 10.600 clientes, elegido mirando la curva ganancia–corte del Public (la ganancia cambia poco entre ~10.500 y ~10.750) |

**Reproducibilidad:** las semillas están fijas, pero LightGBM con varios hilos puede dar diferencias de redondeo según la versión y la máquina. Al final, la notebook compara contra el archivo entregado (si está disponible) e informa cuántos clientes coinciden.

# [Anotación · líneas 34–62] Borra el entorno, carga data.table y lightgbm y define: las dos rutas (carpeta de
#   datasets y carpeta de salida, en C:/Users/Laura/Documents/DMEyF/), el archivo de variables, los meses de
#   entrenamiento 202103 a 202106, el mes a predecir 202108, la corrección de ccajas_depositos en 202105, el
#   corte de 10.600 y N_SEMILLAS = 100. Detiene la ejecución si falta el archivo de variables.
#%% celda 2 [texto]
### 1. Configuración

#%% celda 3 [código]
rm(list = ls())
gc()

require("data.table")
require("lightgbm")
options(scipen = 999)

# ---- RUTAS: cambiar solo estas dos lineas ----
PARAM_carpeta_datasets <- "C:/Users/Laura/Documents/DMEyF/datasets/"      # contiene competencia_01.csv
PARAM_carpeta_salida   <- "C:/Users/Laura/Documents/DMEyF/exp/final_reproducible/"   # aca se escribe todo
archivo_variables_A    <- "variables_A_Aprimaplus.txt"                    # en la misma carpeta que esta notebook

dir.create(PARAM_carpeta_salida, showWarnings = FALSE, recursive = TRUE)
if (!file.exists(archivo_variables_A)) stop("Falta ", archivo_variables_A, " (debe estar junto a esta notebook; ver Requisitos)")

# ---- Periodos ----
MESES_TRAIN <- c(202103, 202104, 202105, 202106)
MES_FUTURE  <- 202108

# ---- Correccion de ceros rotos (cero -> NA en el/los mes(es) indicados) ----
CORRECCIONES <- list(ccajas_depositos = c(202105))

# ---- Salida ----
CORTE_FINAL <- 10600
N_SEMILLAS  <- 100        # 100 = entrega final; 10 = prueba rapida (no identica); 1 = verificacion del pipeline

# [Anotación · líneas 64–71] Arma la lista de 100 semillas: 10 escritas (la primera es 585581), 20 primos
#   escritos entre 100003 y 100271 y los primeros 70 primos a partir de 100272, obtenidos con la función
#   es_primo. Verifica que sean 100 distintas y toma las primeras N_SEMILLAS.
# ---- Semillas: 10 originales + 20 nuevas + 70 primos a partir de 100272 ----
SEMILLAS_10 <- c(585581, 249449, 655649, 503039, 798191, 112909, 334667, 421303, 667021, 887923)
SEMILLAS_NUEVAS <- c(100003, 100019, 100043, 100049, 100057, 100069, 100103, 100109, 100129, 100151, 100153, 100169, 100183, 100189, 100193, 100207, 100213, 100237, 100267, 100271)
es_primo <- function(n) n > 1 && all(n %% 2:floor(sqrt(n)) != 0)
cand <- 100272:101500; cand <- cand[sapply(cand, es_primo)]
SEM100 <- c(SEMILLAS_10, SEMILLAS_NUEVAS, cand[1:70])
stopifnot(length(unique(SEM100)) == 100)
SEMILLAS <- SEM100[1:N_SEMILLAS]

# [Anotación · líneas 73–101] Define los hiperparámetros de los dos modelos, iguales para todas las semillas.
#   Comparten gbdt, objetivo binario, 600 iteraciones, learning_rate 0,02, feature_fraction 0,1541961,
#   num_leaves 1684, lambda_l1 1,520327, lambda_l2 7,548036, min_gain_to_split 0,2158453, bagging_fraction
#   0,8425105 cada 6 iteraciones, scale_pos_weight 0,5 y max_bin 31. Difieren en min_data_in_leaf (4000 en
#   param_A, 1000 en param_B) y en first_metric_only. Imprime la configuración y las versiones de lightgbm,
#   data.table y R.
# ---- Hiperparametros (iguales para todas las semillas) ----
param_A <- list(
  boosting = "gbdt", objective = "binary", metric = "auc",
  first_metric_only = TRUE, boost_from_average = TRUE, feature_pre_filter = FALSE, verbosity = -100,
  learning_rate = 0.02, feature_fraction = 0.1541961, feature_fraction_bynode = 1,
  min_data_in_leaf = 4000, num_leaves = 1684, max_depth = -1,
  lambda_l1 = 1.520327, lambda_l2 = 7.548036, min_gain_to_split = 0.2158453, max_delta_step = 0,
  bagging_fraction = 0.8425105, bagging_freq = 6, min_sum_hessian_in_leaf = 0.001,
  pos_bagging_fraction = 1, neg_bagging_fraction = 1, extra_trees = FALSE, path_smooth = 0,
  cat_l2 = 10, cat_smooth = 10, max_cat_to_onehot = 4, top_rate = 0.2, other_rate = 0.1,
  use_missing = TRUE, is_unbalance = FALSE, num_iterations = 600, early_stopping_rounds = 0,
  max_bin = 31, scale_pos_weight = 0.5, force_row_wise = TRUE
)
param_B <- list(
  boosting = "gbdt", objective = "binary", metric = "auc",
  first_metric_only = FALSE, boost_from_average = TRUE, feature_pre_filter = FALSE,
  force_row_wise = TRUE, verbosity = -100,
  max_depth = -1, max_bin = 31,
  min_sum_hessian_in_leaf = 0.001,
  pos_bagging_fraction = 1, neg_bagging_fraction = 1, is_unbalance = FALSE,
  drop_rate = 0.1, max_drop = 50, skip_drop = 0.5, extra_trees = FALSE,
  num_iterations = 600, learning_rate = 0.02, feature_fraction = 0.1541961,
  num_leaves = 1684, min_data_in_leaf = 1000, scale_pos_weight = 0.5,
  min_gain_to_split = 0.2158453, lambda_l1 = 1.520327, lambda_l2 = 7.548036,
  bagging_fraction = 0.8425105, bagging_freq = 6
)

cat("Train:", paste(MESES_TRAIN, collapse = "+"), "| future:", MES_FUTURE, "| semillas:", N_SEMILLAS, "| corte:", CORTE_FINAL, "\n")
cat("lightgbm", as.character(packageVersion("lightgbm")), "| data.table", as.character(packageVersion("data.table")), "|", R.version.string, "\n")

# [Anotación · líneas 103–117] Lee competencia_01.csv con fread, muestra las filas por mes y clase_ternaria y
#   detiene la ejecución si falta la columna clase_ternaria, si no está 202108 o si hay filas de entrenamiento
#   sin clase. Ordena por numero_de_cliente y foto_mes.
#%% celda 4 [texto]
### 2. Carga de `competencia_01.csv` y chequeos

#%% celda 5 [código]
t0 <- Sys.time()
dataset <- fread(paste0(PARAM_carpeta_datasets, "competencia_01.csv"), stringsAsFactors = TRUE)
cat("Cargado:", nrow(dataset), "filas x", ncol(dataset), "columnas en", round(as.numeric(Sys.time() - t0, units = "secs"), 1), "seg\n")

if (!("clase_ternaria" %in% colnames(dataset))) stop("No se encontro clase_ternaria")
cat("\nFilas por mes y clase_ternaria:\n")
print(dcast(dataset[, .N, by = .(foto_mes, clase_ternaria)], foto_mes ~ clase_ternaria, value.var = "N"))

if (!(MES_FUTURE %in% dataset$foto_mes)) stop("No esta el mes future en el dataset: ", MES_FUTURE)
if (dataset[foto_mes %in% MESES_TRAIN & is.na(clase_ternaria), .N] > 0) stop("Hay filas de train sin clase_ternaria (NA)")
setorder(dataset, numero_de_cliente, foto_mes)

# [Anotación · líneas 119–128] Para cada variable de CORRECCIONES (ccajas_depositos en 202105) cuenta los
#   ceros de ese mes y los pasa a NA.
#%% celda 6 [texto]
### 3. Corrección del cero roto (`ccajas_depositos`, 202105: cero → NA)

#%% celda 7 [código]
for (v in names(CORRECCIONES)) {
  meses <- CORRECCIONES[[v]]
  n <- dataset[foto_mes %in% meses & get(v) == 0, .N]
  dataset[foto_mes %in% meses & get(v) == 0, (v) := NA_real_]
  cat(v, "-- meses", paste(meses, collapse = ","), "-- ceros pasados a NA:", n, "\n")
}

# [Anotación · líneas 130–153] Para cada variable numérica (todas menos numero_de_cliente, foto_mes y
#   clase_ternaria) calcula por cliente, con shift, el valor de una y de dos filas atrás (_lag1, _lag2) y la
#   diferencia del valor actual con cada uno (_delta1, _delta2). Después conserva sólo las filas de 202103 a
#   202106 y de 202108.
#%% celda 8 [texto]
### 4. Rezagos y diferencias de 1 y 2 meses
`_lag1` = valor de hace 1 mes; `_lag2` = valor de hace 2 meses; `_delta1` = actual − lag1; `_delta2` = actual − lag2. Se calculan sobre los valores originales, por cliente, **antes** de rankear.

#%% celda 9 [código]
campos_no_procesar <- c("numero_de_cliente", "foto_mes", "clase_ternaria")
campos_lag <- setdiff(colnames(dataset), campos_no_procesar)
campos_lag <- campos_lag[sapply(dataset[, ..campos_lag], is.numeric)]
cat("Lags/deltas para", length(campos_lag), "variables\n")

t0 <- Sys.time()
dataset[, (paste0(campos_lag, "_lag1")) := shift(.SD, n = 1, fill = NA, type = "lag"), by = numero_de_cliente, .SDcols = campos_lag]
dataset[, (paste0(campos_lag, "_lag2")) := shift(.SD, n = 2, fill = NA, type = "lag"), by = numero_de_cliente, .SDcols = campos_lag]
for (campo in campos_lag) {
  dataset[, paste0(campo, "_delta1") := get(campo) - get(paste0(campo, "_lag1"))]
  dataset[, paste0(campo, "_delta2") := get(campo) - get(paste0(campo, "_lag2"))]
}
cat("Listo en", round(as.numeric(Sys.time() - t0, units = "secs"), 1), "seg |", nrow(dataset), "filas x", ncol(dataset), "columnas\n")

# con los rezagos ya calculados, se conservan solo los meses que se usan (el ranking es por mes: no cambia)
MESES_USAR <- c(MESES_TRAIN, MES_FUTURE)
dataset <- dataset[foto_mes %in% MESES_USAR]
gc()
cat("Filas que quedan (", paste(MESES_USAR, collapse = ","), "):", nrow(dataset), "\n")

# [Anotación · líneas 155–184] Define rankear_cero_fijo: deja en 0 los ceros, ordena con frank los valores
#   distintos de cero y los lleva a la escala 1 a 100 (100 si hay uno solo), y mantiene los NA. Define
#   rankear_dataset, que aplica esa función a cada columna numérica dentro de cada foto_mes, pasando antes las
#   columnas enteras a numéricas.
#%% celda 10 [texto]
### 5. Ranking cero fijo
Por mes y por variable: los valores distintos de cero (negativos y positivos juntos) se ordenan y se llevan a una escala de 1 a 100; el cero queda en 0 y los NA siguen siendo NA.

#%% celda 11 [código]
rankear_cero_fijo <- function(x) {
  out <- rep(0, length(x))
  idx_nz <- which(x != 0 & !is.na(x))
  n <- length(idx_nz)
  if (n == 1) {
    out[idx_nz] <- 100
  } else if (n > 1) {
    r <- frank(x[idx_nz], ties.method = "average")
    out[idx_nz] <- 1 + 99 * (r - 1) / (n - 1)
  }
  out[is.na(x)] <- NA_real_
  out
}

rankear_dataset <- function(dt) {
  campos_no_rankear <- c("numero_de_cliente", "foto_mes", "clase_ternaria")
  campos_rankear <- setdiff(colnames(dt), campos_no_rankear)
  campos_rankear <- campos_rankear[sapply(dt[, ..campos_rankear], is.numeric)]
  for (campo in campos_rankear) {
    # las columnas enteras no pueden guardar percentiles con decimales: se pasan a numeric antes de rankear
    if (is.integer(dt[[campo]])) set(dt, j = campo, value = as.numeric(dt[[campo]]))
    dt[, (campo) := rankear_cero_fijo(get(campo)), by = foto_mes]
  }
  invisible(dt)
}

# [Anotación · líneas 186–210] Lee variables_A_Aprimaplus.txt, exige que la última variable sea gen_1 y que no
#   haya repetidas, y separa las 575 restantes. Lista 30 variables que sirven de insumo a las compuestas, define
#   el patrón de variables que se sacan del modelo A (Master_fultimo_cierre, Visa_fultimo_cierre, Visa_mpagado)
#   y arma dataset_A con las claves y las columnas necesarias que ya existen en el dataset.
#%% celda 12 [texto]
### 6. Modelo A'plus: variables históricas, ranking, compuestas y `gen_1`
Solo se calculan y rankean las columnas que el modelo usa (el ranking es independiente por columna, así que el resultado es idéntico al de rankear todo; solo ahorra tiempo y memoria).

#%% celda 13 [código]
t0 <- Sys.time()

variables_A_archivo <- trimws(readLines(archivo_variables_A)); variables_A_archivo <- variables_A_archivo[variables_A_archivo != ""]
stopifnot(tail(variables_A_archivo, 1) == "gen_1", !anyDuplicated(variables_A_archivo))
campos_A_archivo <- setdiff(variables_A_archivo, "gen_1")   # las 575 seleccionadas, en su orden

insumos_compuestas <- c("mtarjeta_visa_consumo", "mtarjeta_master_consumo", "Visa_mconsumototal", "Master_mconsumototal",
  "Visa_msaldototal", "Master_msaldototal", "Visa_mlimitecompra", "Master_mlimitecompra", "Visa_mpagado", "Master_mpagado",
  "Visa_mpagominimo", "Master_mpagominimo", "mcajeros_propios_descuentos", "mtarjeta_visa_descuentos",
  "mtarjeta_master_descuentos", "Visa_status", "Master_status", "mpayroll", "mpayroll2", "mprestamos_prendarios",
  "mprestamos_hipotecarios", "minversion1_pesos", "minversion1_dolares", "minversion2", "mplazo_fijo_dolares",
  "mplazo_fijo_pesos", "mtransferencias_recibidas", "mtransferencias_emitidas", "mcomisiones_mantenimiento",
  "mcomisiones_otras")
patron_ruidoso <- "Master_fultimo_cierre|Visa_fultimo_cierre|Visa_mpagado"   # estas variables se sacan del modelo A
necesarias <- unique(c(campos_A_archivo, insumos_compuestas, "ctrx_quarter", "cpayroll_trx_min3"))
necesarias <- necesarias[!grepl(patron_ruidoso, necesarias)]
sufijos_fe <- c("_avg3", "_max3", "_min3", "_ratio_avg", "_ratio_max", "_tendencia")

claves <- c("numero_de_cliente", "foto_mes", "clase_ternaria")
dataset_A <- dataset[, unique(c(claves, intersect(necesarias, colnames(dataset)))), with = FALSE]

# [Anotación · líneas 212–241] Para cada variable base que tiene lag 1 y lag 2 y de la que la lista pide
#   alguna derivada, calcula sobre el valor actual y los dos rezagos: promedio (_avg3), máximo (_max3), mínimo
#   (_min3), cociente actual/promedio (_ratio_avg), cociente actual/máximo (_ratio_max) y tendencia ((actual −
#   lag 2)/2, o actual − lag 1 si falta lag 2). Agrega a dataset_A sólo las derivadas que están en la lista y
#   luego aplica el ranking cero fijo a todo dataset_A.
# --- variables historicas (promedio, maximo, minimo, razones y tendencia de 3 meses) ---
todas <- colnames(dataset)
bases <- sub("_lag1$", "", grep("_lag1$", todas, value = TRUE))
bases <- bases[bases %in% todas & paste0(bases, "_lag2") %in% todas]
bases <- bases[!grepl(patron_ruidoso, bases)]
bases_fe <- bases[vapply(bases, function(b) any(paste0(b, sufijos_fe) %in% necesarias), logical(1))]
for (b in bases_fe) {
  a  <- dataset[[b]]
  l1 <- dataset[[paste0(b, "_lag1")]]
  l2 <- dataset[[paste0(b, "_lag2")]]
  avg3 <- rowMeans(cbind(a, l1, l2), na.rm = TRUE)
  avg3[is.nan(avg3)] <- NA_real_
  max3 <- pmax(a, l1, l2, na.rm = TRUE)
  min3 <- pmin(a, l1, l2, na.rm = TRUE)
  derivadas <- list(
    avg3 = avg3, max3 = max3, min3 = min3,
    ratio_avg = ifelse(!is.na(avg3) & avg3 != 0, a / avg3, NA_real_),
    ratio_max = ifelse(!is.na(max3) & max3 != 0, a / max3, NA_real_),
    tendencia = ifelse(!is.na(l2), (a - l2) / 2, ifelse(!is.na(l1), a - l1, NA_real_))
  )
  for (s in names(derivadas)) {
    nom <- paste0(b, "_", s)
    if (nom %in% necesarias) dataset_A[, (nom) := derivadas[[s]]]
  }
}
cat("Variables historicas:", length(bases_fe), "variables base de", length(bases), "\n")

# --- ranking cero fijo ---
rankear_dataset(dataset_A)
gc()

# [Anotación · líneas 243–279] Sobre los valores ya rankeados define las variables compuestas: sumas de pares
#   o ternas (consumos, saldos, límites, pagos, pagos mínimos y descuentos de tarjetas, payroll, préstamos
#   prendarios e hipotecarios, inversiones, plazos fijos, comisiones), que sólo se crean si hay al menos dos
#   insumos presentes; utilizacion_tarjetas (consumo/límite, 0 si el límite es 0); tarjetas_activas_count;
#   transferencias_netas; y gen_1 = ctrx_quarter + cpayroll_trx_min3. Crea clase01 (1 si BAJA+1 o BAJA+2). Arma
#   campos_A en el orden del archivo y detiene la ejecución si no es idéntica a la lista leída.
# --- variables compuestas y gen_1 (se calculan sobre valores ya rankeados) ---
agregar_si_existen <- function(dt, nombre_nueva, columnas, fun_combinacion) {
  presentes <- columnas[columnas %in% colnames(dt)]
  if (length(presentes) < 2) return(invisible(NULL))
  dt[, (nombre_nueva) := fun_combinacion(.SD), .SDcols = presentes]
}
suma_filas <- function(sd) Reduce(`+`, sd)

agregar_si_existen(dataset_A, "consumo_tarjetas_total", c("mtarjeta_visa_consumo", "mtarjeta_master_consumo"), suma_filas)
agregar_si_existen(dataset_A, "consumototal_tarjetas", c("Visa_mconsumototal", "Master_mconsumototal"), suma_filas)
agregar_si_existen(dataset_A, "saldo_tarjetas_total", c("Visa_msaldototal", "Master_msaldototal"), suma_filas)
agregar_si_existen(dataset_A, "limite_tarjetas_total", c("Visa_mlimitecompra", "Master_mlimitecompra"), suma_filas)
agregar_si_existen(dataset_A, "pagado_tarjetas_total", c("Visa_mpagado", "Master_mpagado"), suma_filas)
agregar_si_existen(dataset_A, "pagominimo_tarjetas_total", c("Visa_mpagominimo", "Master_mpagominimo"), suma_filas)
agregar_si_existen(dataset_A, "descuentos_tarjetas_total",
                   c("mcajeros_propios_descuentos", "mtarjeta_visa_descuentos", "mtarjeta_master_descuentos"), suma_filas)
if (all(c("consumototal_tarjetas", "limite_tarjetas_total") %in% colnames(dataset_A))) {
  dataset_A[, utilizacion_tarjetas := ifelse(limite_tarjetas_total == 0, 0, consumototal_tarjetas / limite_tarjetas_total)]
}
if (all(c("Visa_status", "Master_status") %in% colnames(dataset_A))) {
  dataset_A[, tarjetas_activas_count := as.integer(Visa_status == 0) + as.integer(Master_status == 0)]
}
agregar_si_existen(dataset_A, "ingresos_payroll_total", c("mpayroll", "mpayroll2"), suma_filas)
agregar_si_existen(dataset_A, "prestamos_sin_personales_total", c("mprestamos_prendarios", "mprestamos_hipotecarios"), suma_filas)
agregar_si_existen(dataset_A, "inversiones_totales", c("minversion1_pesos", "minversion1_dolares", "minversion2"), suma_filas)
agregar_si_existen(dataset_A, "plazo_fijo_total", c("mplazo_fijo_dolares", "mplazo_fijo_pesos"), suma_filas)
if (all(c("mtransferencias_recibidas", "mtransferencias_emitidas") %in% colnames(dataset_A))) {
  dataset_A[, transferencias_netas := mtransferencias_recibidas - mtransferencias_emitidas]
}
agregar_si_existen(dataset_A, "comisiones_totales_manual", c("mcomisiones_mantenimiento", "mcomisiones_otras"), suma_filas)
dataset_A[, gen_1 := ctrx_quarter + cpayroll_trx_min3]
dataset_A[, clase01 := ifelse(clase_ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)]

campos_A <- campos_A_archivo[campos_A_archivo %in% colnames(dataset_A)]
campos_A <- c(campos_A, "gen_1")
cat("Variables modelo A'plus:", length(campos_A), "\n")
if (!identical(campos_A, variables_A_archivo)) stop("Las variables de A'plus calculadas no coinciden (ni en cantidad ni en orden) con ", archivo_variables_A)

# [Anotación · líneas 281–291] Separa las filas de entrenamiento (202103 a 202106) y las de 202108 ordenadas
#   por cliente, convierte ambas a matriz con las columnas de campos_A, guarda la etiqueta y los ids de 202108,
#   imprime cantidades y libera memoria.
# --- matrices (future ordenado por cliente) ---
dataset_A_train <- dataset_A[foto_mes %in% MESES_TRAIN]
dfuture_A       <- dataset_A[foto_mes == MES_FUTURE]
setkey(dfuture_A, numero_de_cliente)
matriz_A_train  <- data.matrix(dataset_A_train[, campos_A, with = FALSE])
matriz_A_future <- data.matrix(dfuture_A[, campos_A, with = FALSE])
y_train    <- dataset_A_train$clase01
ids_future <- dfuture_A$numero_de_cliente
cat("train:", nrow(dataset_A_train), "filas |", sum(y_train), "positivos (BAJA+1 y BAJA+2) | future:", length(ids_future), "clientes\n")
rm(dataset_A, dataset_A_train, dfuture_A); gc(full = TRUE, verbose = FALSE)
cat("Modelo A'plus: matrices listas en", round(as.numeric(Sys.time() - t0, units = "secs"), 1), "seg\n")

# [Anotación · líneas 293–316] Modelo B: aplica el ranking cero fijo al dataset completo (originales, lags y
#   deltas), crea clase01 y toma como variables todas las columnas menos clase_ternaria, clase01,
#   numero_de_cliente y foto_mes. Verifica que los clientes de 202108 y la etiqueta de entrenamiento sean
#   idénticos a los de A'plus y arma las matrices.
#%% celda 14 [texto]
### 7. Modelo B: todas las variables, rankeadas (sin `foto_mes` ni `numero_de_cliente`)

#%% celda 15 [código]
t0 <- Sys.time()
dataset_B <- dataset
rm(dataset)
rankear_dataset(dataset_B)
dataset_B[, clase01 := ifelse(clase_ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)]
gc()

campos_B <- setdiff(colnames(dataset_B), c("clase_ternaria", "clase01", "numero_de_cliente", "foto_mes"))
cat("Variables modelo B:", length(campos_B), "\n")

idx_train  <- which(dataset_B$foto_mes %in% MESES_TRAIN)
idx_future <- which(dataset_B$foto_mes == MES_FUTURE)
idx_future <- idx_future[order(dataset_B$numero_de_cliente[idx_future])]   # mismo orden que en A'plus
stopifnot(identical(dataset_B$numero_de_cliente[idx_future], ids_future))
stopifnot(identical(dataset_B$clase01[idx_train], y_train))

matriz_B_train  <- data.matrix(dataset_B[idx_train,  campos_B, with = FALSE])
matriz_B_future <- data.matrix(dataset_B[idx_future, campos_B, with = FALSE])
rm(dataset_B, idx_train, idx_future); gc(full = TRUE, verbose = FALSE)
cat("Modelo B: matrices listas en", round(as.numeric(Sys.time() - t0, units = "secs"), 1), "seg\n")

# [Anotación · líneas 318–344] Define entrenar_modelo: para cada semilla, si ya existe su archivo .rds la
#   saltea; si no, pone la semilla en los parámetros y en set.seed, entrena un LightGBM con lgb.train sobre todo
#   el entrenamiento, predice 202108 y guarda frank(prob)/n. Lo ejecuta para Aplus (param_A) y para B (param_B)
#   e informa cuántas semillas tiene cada modelo.
#%% celda 16 [texto]
### 8. Entrenamiento: una corrida de LightGBM por semilla y por modelo (reanudable)
Cada semilla guarda el ranking de sus predicciones (`frank(prob) / n`) en un archivo `.rds`; si ya existe, se saltea.

#%% celda 17 [código]
carpeta_rank <- paste0(PARAM_carpeta_salida, "rankings/"); dir.create(carpeta_rank, showWarnings = FALSE, recursive = TRUE)
ruta_rank <- function(modelo, s) paste0(carpeta_rank, "rank_", modelo, "_s", s, ".rds")

entrenar_modelo <- function(modelo, param, m_train, m_future) {
  for (SEM in SEMILLAS) {
    archivo <- ruta_rank(modelo, SEM)
    if (file.exists(archivo)) { cat("[", modelo, "semilla", SEM, "] ya hecha, se saltea\n"); next }
    t0 <- Sys.time()
    p <- param; p$seed <- SEM
    set.seed(SEM, "L'Ecuyer-CMRG")
    m <- lgb.train(data = lgb.Dataset(data = m_train, label = y_train, free_raw_data = FALSE), param = p, verbose = -1)
    prob <- predict(m, m_future)
    rm(m); gc(full = TRUE, verbose = FALSE)
    saveRDS(frank(prob) / length(prob), archivo)
    cat("[", modelo, "semilla", SEM, "] lista en", round(as.numeric(Sys.time() - t0, units = "mins"), 1), "min |", format(Sys.time()), "\n")
  }
}

entrenar_modelo("Aplus", param_A, matriz_A_train, matriz_A_future)
entrenar_modelo("B",     param_B, matriz_B_train, matriz_B_future)
cat("\nA'plus:", sum(file.exists(sapply(SEMILLAS, function(s) ruta_rank("Aplus", s)))), "de", length(SEMILLAS), "semillas |",
    "B:", sum(file.exists(sapply(SEMILLAS, function(s) ruta_rank("B", s)))), "de", length(SEMILLAS), "semillas\n")

# [Anotación · líneas 346–369] Promedia por cliente los percentiles de las semillas de cada modelo (rA, rB),
#   imprime su correlación de Spearman, calcula rank_final = (rA + rB)/2 y toma los 10.600 clientes de mayor
#   valor. Escribe el CSV sin encabezado con esos ids y un CSV con los puntajes de todos los clientes; relee el
#   primero y verifica que tenga sólo enteros, 10.600 líneas y ningún repetido.
#%% celda 18 [texto]
### 9. Ensamble y archivo para el bot
Ranking promedio de las semillas de cada modelo; luego promedio de A'plus y B; se toman los `CORTE_FINAL` clientes con mayor ranking.

#%% celda 19 [código]
rA <- rowMeans(sapply(SEMILLAS, function(s) readRDS(ruta_rank("Aplus", s))))
rB <- rowMeans(sapply(SEMILLAS, function(s) readRDS(ruta_rank("B", s))))
stopifnot(length(rA) == length(ids_future), length(rB) == length(ids_future))
cat("Spearman A'plus vs B:", round(cor(rA, rB, method = "spearman"), 4), "\n")

rank_final <- (rA + rB) / 2
orden <- ids_future[order(-rank_final)]
top <- orden[1:CORTE_FINAL]

archivo_final <- paste0(PARAM_carpeta_salida, "Aprimaplus_B", N_SEMILLAS, "_corte", CORTE_FINAL, ".csv")
fwrite(data.table(id = as.integer(top)), archivo_final, col.names = FALSE)
fwrite(data.table(numero_de_cliente = as.integer(ids_future), rank_Aplus = rA, rank_B = rB, rank_final = rank_final),
       paste0(PARAM_carpeta_salida, "scores_Aprimaplus_B", N_SEMILLAS, "_202108.csv"))

# chequeo de formato (sin encabezado, solo enteros, sin repetidos, cantidad exacta)
lineas <- readLines(archivo_final)
stopifnot(all(grepl("^[0-9]+$", lineas)), length(lineas) == CORTE_FINAL, !anyDuplicated(lineas))
cat("Archivo para el bot:", archivo_final, "| filas:", length(lineas), "| formato ok\n")
cat("Primeras lineas:", paste(head(lineas, 5), collapse = ", "), "\n")

# [Anotación · líneas 371–385] Si N_SEMILLAS es 100 y existe el archivo entregado en una ruta local, informa
#   cuántos clientes coinciden y si el orden es idéntico. Imprime el resultado del Public que declara la
#   notebook y llama a sessionInfo().
#%% celda 20 [texto]
### 10. Comparación con el archivo entregado (opcional)
Si se dispone del archivo que obtuvo 119,3775 en el Public, se informa cuántos clientes coinciden. Con 100 semillas y la misma versión de LightGBM debería coincidir completo o casi.

#%% celda 21 [código]
archivo_entregado <- "C:/Users/Laura/Documents/DMEyF/exp/submit_Aprimaplus/cortes/Aprimaplus_B100_corte10600.csv"   # ajustar o ignorar
if (N_SEMILLAS == 100 && file.exists(archivo_entregado)) {
  ref <- fread(archivo_entregado, header = FALSE)$V1
  cat("Coinciden con el archivo entregado:", length(intersect(ref, top)), "de", CORTE_FINAL,
      "| mismo orden:", identical(as.integer(ref), as.integer(top)), "\n")
} else {
  cat("Sin comparacion (N_SEMILLAS != 100 o no se encontro el archivo entregado)\n")
}
cat("\nResultado en el Public del bot para el archivo entregado: 119,3775 M\n")
sessionInfo()

# [Anotación · líneas 387–403] Para la primera semilla, si existen en rutas locales los rankings de la corrida
#   original (uno de A'plus y uno de B), calcula la correlación de Spearman con el ranking nuevo e informa si
#   son idénticos.
#%% celda 22 [texto]
### 11. Verificación rápida de una semilla (opcional)
Compara el ranking de la primera semilla con el que se guardó cuando se armó la entrega original (si esos archivos están disponibles). Si el pipeline es el mismo, la correlación debe ser 1 (o casi).

#%% celda 23 [código]
exp_original <- "C:/Users/Laura/Documents/DMEyF/exp/"      # ajustar o ignorar
s1 <- SEMILLAS[1]
for (par in list(list("Aplus", paste0(exp_original, "submit_Aprimaplus/rankApp_s", s1, ".rds")),
                 list("B",     paste0(exp_original, "submit_control_soloB/rank_s", s1, ".rds")))) {
  if (file.exists(par[[2]]) && file.exists(ruta_rank(par[[1]], s1))) {
    nuevo <- readRDS(ruta_rank(par[[1]], s1)); viejo <- readRDS(par[[2]])
    cat(par[[1]], "semilla", s1, "| Spearman con el ranking original:", round(cor(nuevo, viejo, method = "spearman"), 6),
        "| identicos:", isTRUE(all.equal(nuevo, viejo)), "\n")
  } else {
    cat(par[[1]], ": sin comparacion (no se encontro el ranking original)\n")
  }
}
```


## Explicaciones del alumno (texto original)

### README.md

> # Entrega final DMEyF 2026 — Laura Pasquini
>
> Todo el contenido de la entrega (notebook final, README con las instrucciones de replicación y notebooks de procesamiento previo) está en la carpeta [`repo_entrega`](./repo_entrega).

### repo_entrega/README.md

> ---
>
> editor_options: 
>   markdown: 
>     wrap: sentence
> ---
>
> # Primera competencia DMEyF 2026 — Entrega final (Laura Pasquini)
>
> **Archivo entregado como último submit:** `Aprimaplus_B100_corte10600.csv` (10.600 clientes con `Predicted = 1`; Public Leaderboard: ganancia 119,3775).
>
> El archivo sale de un ensamble de dos modelos LightGBM, **A'plus** y **B**, con 100 semillas cada uno. Todo lo necesario para regenerarlo exactamente está en la raíz de esta carpeta: la notebook final y `variables_A_Aprimaplus.txt`. La carpeta `procesamiento_previo/` documenta **de dónde salen** los hiperparámetros y las listas de variables que la notebook final usa como datos fijos (no hace falta volver a ejecutarla).
>
> ## Estructura
>
> ```         
> Notebook_final_reproducible_Aprimaplus_B100.ipynb   <- genera el archivo entregado (hay que ejecutarla)
> variables_A_Aprimaplus.txt                           <- lista de las 576 variables de A'plus (entrada de la notebook)
> README.md
> procesamiento_previo/                                <- evidencia, no hace falta ejecutarla
>     (16 notebooks, ver tabla)
>     archivos_de_apoyo/                               <- log de la BO y listas de variables
> ```
>
> | Etapa | Notebook (`procesamiento_previo/`) | Qué documenta |
> |------------------------|------------------------|------------------------|
> | BO | `z494_TareaHogar_04_TerceraCapa_SalsaMagica` | Bayesian Optimization (experimento 4961) |
> | BO | `z601_BO_Diagnostico` | Diagnóstico de la BO |
> | BO | `z601_Top3Trials_NSemillas`, `z601_Top5Trials_NSemillas` | Validación de los mejores trials con 10 semillas |
> | Grilla | `z494_Grilla_LR_ScalePosWeight_Trial2` | learning_rate × scale_pos_weight sobre el trial 2 |
> | Grilla | `z_grid_lr_scalePosWeight` | Misma grilla, más fina, sobre 359 variables |
> | Grilla | `z_grilla_mdl_modeloA` | `min_data_in_leaf` de A (→ 4000) |
> | Grilla | `z_grilla_rankeado_lags`, `z_grilla_min_data_lags`, `z_grilla_min_data_in_leaf_canaritos` | `min_data_in_leaf` de B (→ 1000) |
> | Variables | `z_canaritos_asesinos` | Lista A (358 variables) |
> | Variables | `z_canaritos_202105_06` | Lista A' (526 variables) |
> | Variables | `z_overnight_canaritos_genetico`, `z_verificacion_gen1_sobre_ganadora`, `z_modeloA_gen1_v2` | Origen y verificación de `gen_1` |
> | Variables | `z_exportar_datasets_A_B_rankeados` | Exportación de los datasets procesados (auxiliar) |
>
> ## Cómo replicar el archivo entregado
>
> 1.  Dejar `competencia_01.csv` en la carpeta de datasets y poner `variables_A_Aprimaplus.txt` junto a la notebook.
> 2.  En la celda 1 de `Notebook_final_reproducible_Aprimaplus_B100.ipynb` cambiar **solo las dos rutas** (carpeta de datasets y carpeta de salida).
> 3.  Ejecutar la notebook completa (R, kernel IRkernel). `N_SEMILLAS <- 100` ya está configurado.
> 4.  Resultado: `Aprimaplus_B100_corte10600.csv` en la carpeta de salida. La sección 10 lo compara con el archivo entregado (cuando está disponible).
>
> **Tiempos medidos** (PC con 20 GB de RAM): preparación de datos ≈ 70 min; modelo A'plus ≈ 1,9 min por semilla; modelo B ≈ 4,2 min por semilla. Con 100 semillas por modelo el total es ≈ 11 h. La notebook es **reanudable**: guarda un ranking por semilla en `rankings/` y salta los ya hechos. Para una verificación rápida: `N_SEMILLAS <- 1` (≈ 1 h 20 min); la sección 11 compara el resultado de la semilla 585581 con el original (idéntico).
>
> **Precaución:** la primera celda de configuración contiene `rm(list = ls())`; no volver a ejecutarla en medio de una sesión.
>
> ## Qué hace el modelo
>
> - **Entrenamiento:** meses 202103 a 202106 (con `clase_ternaria` BAJA+2 como objetivo). **Predicción:** 202108.
> - **Variables históricas:** el promedio, máximo, mínimo, razones (valor actual / promedio y / máximo) y tendencia de 3 meses se calculan dentro de la notebook final (celda 12) a partir del valor actual y los rezagos de 1 y 2 meses; no hace falta ejecutar ningún otro notebook para generarlas.
> - **Transformación de variables:** "ranking cero fijo" por mes y variable (ceros fijos en 0, valores distintos de cero reescalados de 1 a 100, NA se mantiene). Se corrige `ccajas_depositos` de 202105 (ceros pasados a NA).
> - **Modelo A'plus:** 576 variables (575 seleccionadas con canaritos + `gen_1`), `min_data_in_leaf = 4000`.
> - **Modelo B:** 760 variables = 152 variables × (original, lag 1, lag 2, delta 1, delta 2), `min_data_in_leaf = 1000`. Sin `foto_mes` ni `numero_de_cliente`.
> - **Hiperparámetros comunes:** learning_rate 0,02; feature_fraction 0,1541961; num_leaves 1684; lambda_l1 1,520327; lambda_l2 7,548036; min_gain_to_split 0,2158453; bagging_fraction 0,8425105 (freq 6); scale_pos_weight 0,5; 600 iteraciones; max_bin 31; boosting gbdt.
> - **Ensamble en dos niveles (todo por percentiles):**
>   1.  Por semilla: la probabilidad predicha se convierte en percentil (`rank/n`).
>   2.  Por modelo: promedio de los 100 percentiles de cada modelo (rA, rB).
>   3.  Entre modelos: `(rA + rB) / 2`.
>   4.  Corte: los 10.600 clientes con mayor puntaje reciben `Predicted = 1`.
>
> ## Origen de los hiperparámetros (`procesamiento_previo/`)
>
> 1.  **Bayesian Optimization (mlrMBO)** — `z494_TareaHogar_04_TerceraCapa_SalsaMagica.ipynb`: experimento 4961, 11 hiperparámetros, 100 iteraciones, 5 folds, undersampling 0,1 de los CONTINUA, entrenamiento solo en 202104 (151 variables originales, sin lags), ganancia directa como métrica. Sigue la plantilla de la Tarea Hogar 04 del curso, con "Salsa Mágica" (se excluyen `cprestamos_personales` y `mprestamos_personales`). Resultados en `archivos_de_apoyo/` (`BO_log.txt`, `bayesiana.RDATA` y `PARAM.yml`, de la carpeta `HT4961`). El `competencia_01.csv` se genera en esa misma notebook (celda de `clase_ternaria`) a partir del archivo crudo.
> 2.  **Selección del trial:** el mejor trial por ganancia interna (trial 1) no fue el elegido. Con 10 semillas sobre 202106 el **trial 2** (iteración 70; ganancia interna 253,66 M; segundo mejor) validó mejor (media 439,9 M contra 411,0 M del trial 1; `z601_Top3Trials_NSemillas.ipynb` y `z601_Top5Trials_NSemillas.ipynb`). De ese trial se toman feature_fraction, num_leaves, min_gain_to_split, lambda_l1, lambda_l2 y bagging_fraction. `z601_BO_Diagnostico.ipynb` muestra el diagnóstico de la BO. *Limitaciones conocidas:* (a) la BO y estas comparaciones usan `numero_de_cliente` como variable (así viene la plantilla del curso); los modelos finales lo excluyen;
>     (b) `Top3/Top5` usan `min_data_in_leaf` sin multiplicar por 10 (el factor de la normalización por undersampling), por lo que la comparación entre trials no es exactamente la misma configuración que se usa después.
> 3.  **Grilla learning_rate × scale_pos_weight:** `z494_Grilla_LR_ScalePosWeight_Trial2.ipynb` (sobre el trial 2, 930 iteraciones, una semilla, 25 combinaciones): ganó learning_rate 0,02 y scale_pos_weight 0,5. `z_grid_lr_scalePosWeight.ipynb` repite una grilla más fina (56 combinaciones, 3 etapas, 600 iteraciones, 359 variables): el mejor candidato (0,015 / 0,6) quedó prácticamente empatado (+0,11 M sobre 463,98 M, dentro del ruido) y se mantuvo 0,02 / 0,5.
> 4.  **`min_data_in_leaf`:**
>     - **A'plus = 4000:** `z_grilla_mdl_modeloA.ipynb` (A con 358 variables + `gen_1`, dataset rankeado con lags y FE histórico, 10 semillas, entrenamiento 202103+202104, corte fijo 12.000, resto de hiperparámetros fijos). Valores probados 300, 500, 1000, 2000, 3000, 4000 y 5000: ganó 4000 (media 463,98 M); 3000 y 2000 quedaron muy cerca (463,65 M y 463,43 M). La grilla se hizo sobre el modelo A de 358 variables; el valor se mantuvo al pasar a A'plus (576 variables). Como respaldo, en `z_grilla_min_data_lags.ipynb` (dataset con lags sin rankear) un `min_data_in_leaf` alto reduce el porcentaje de Gain que se llevan los canaritos (de 50,7 % con 1000 a 40,8 % con 4000).
>     - **B = 1000:** `z_grilla_rankeado_lags.ipynb` (grilla de B sobre el dataset rankeado con lags; confirmó 1000 como mejor valor) y, antes, `z_grilla_min_data_lags.ipynb` (1000 y 2000 empatan en 464,09 M; se eligió 1000). `z_grilla_min_data_in_leaf_canaritos.ipynb` (variables originales, 151) también da 1000 como mejor valor para B (450,78 M).
> 5.  **600 iteraciones:** valor fijado en las primeras pruebas manuales con learning_rate 0,02, sin grilla propia. Los notebooks de la cadena de canaritos ya usaban 600 y se mantuvo para el modelo final (la grilla sobre el trial 2 usa 930, que es el valor de la BO con su learning_rate original de 0,0273).
>
> La BO **no se vuelve a ejecutar**: el log se incluye como evidencia y los valores quedan fijos en la notebook final.
>
> **Otras BOs exploradas y no adoptadas.** Además de la BO de la que salen los hiperparámetros finales (HT4961, trial 2), se probaron otras optimizaciones que **no** intervienen en el archivo entregado y por eso no se incluyen en este repositorio:
> - BO de 11 hiperparámetros sobre el dataset con lags rankeado (751 variables) y sobre la lista de 358 variables + `gen_1`, primero optimizando AUC (la ganancia real quedó en 452,65 M contra 463,98 M de referencia) y luego ganancia directa (411,77 M en screening de 3 semillas; descartada porque los hiperparámetros quedaron pegados a los bordes del espacio de búsqueda y el modelo se sobreajustó a los folds internos).
> - BO entrenando con los 4 meses (202103 a 202106), con y sin canaritos.
> - BO por separado para el modelo A y para el modelo B (con undersampling 0,1 y folds agrupados por cliente).
> - BO de B contra pseudo-etiquetas de 202108.
>
> Ninguna de ellas reemplazó a los hiperparámetros del trial 2, que son los que usa la notebook final para A'plus y B (solo `min_data_in_leaf` se define por modelo, ver más abajo).
>
> ## Origen de las listas de variables (`procesamiento_previo/`)
>
> - **Lista A (358 variables):** `z_canaritos_asesinos.ipynb`, receta de la cátedra ("canaritos asesinos": 20 % de canaritos, un LightGBM, id ordinal por importancia, se descartan las variables con id mayor a media + 2 desvíos de los ids de los canaritos), entrenando con 202103 y 202104.
> - **Lista A' (526 variables):** `z_canaritos_202105_06.ipynb`, misma receta entrenando con 202105 y 202106 y con dos semillas (585581 y 249449); A' es la **intersección** de las dos listas de 2 desvíos.
> - **A'plus (575 variables)** = unión de A y A'. Más `gen_1` = 576 (`variables_A_Aprimaplus.txt`, en orden). La notebook final verifica que la lista que calcula coincide con ese archivo.
> - **`gen_1` = `ctrx_quarter` + `cpayroll_trx_min3`:** surgió de un algoritmo genético (AUC univariado) en `z_overnight_canaritos_genetico.ipynb` (parte 2; la parte 1 es una poda de canaritos anterior, descartada; la corrida original duró unas 8,9 h (≈ 11.900 generaciones) y el mejor individuo fue siempre el mismo, con AUC univariado 0,8752: `genetico_top_features.txt` lo registra y `genetico_log.txt` guarda la evolución. Dos corridas posteriores (v2 y v3, no incluidas) encontraron otras combinaciones con AUC univariado similar (0,8775 y 0,8756) que no se adoptaron en el modelo final). Se verificó en `z_verificacion_gen1_sobre_ganadora.ipynb` sobre la lista A de 358 variables, con 10 semillas: 462,44 M sin `gen_1` contra 463,98 M con `gen_1` (+1,54 M, dentro del ruido entre semillas; sobre la poda vieja de 110 variables había sumado +4,29 M) y se conservó. `z_modeloA_gen1_v2.ipynb` compara además `gen_1` sin rankear contra rankeada (463,98 M contra 463,43 M). En el modelo final se calcula sobre las variables ya rankeadas.
> - Del modelo A se excluyen `Master_fultimo_cierre`, `Visa_fultimo_cierre` y `Visa_mpagado` (variables con un mes anómalo).
> - Los archivos de listas (`campos_canaritos_asesinos_2sd.txt`, `campos_canaritos_202105_06_s585581_2sd.txt`, `campos_canaritos_202105_06_s249449_2sd.txt`, `genetico_top_features.txt`) están en `procesamiento_previo/archivos_de_apoyo/`.
> - `z_exportar_datasets_A_B_rankeados.ipynb` exporta los datasets ya procesados (unión de A y A', lags, deltas y ranking); es un auxiliar y no interviene en el archivo final.
>
> ## Verificación realizada
>
> - Semilla 585581 reentrenada desde cero con la notebook final: ranking idéntico al original (A'plus y B).
> - El archivo final reconstruido a partir de los 200 rankings guardados coincide con el entregado: 10.600 de 10.600, mismo orden.
>
> ## Entorno
>
> R 4.5.3, Windows, 20 GB de RAM. Paquetes: data.table, lightgbm 4.7.0. El entrenamiento es determinista para una semilla dada.
>
> ## Uso de asistencia de IA
>
> Para el desarrollo de este trabajo usé Claude (Anthropic) como asistente: revisión y limpieza de código,
> armado de la notebook reproducible final y redacción de este README. Las decisiones de modelado,
> los experimentos y las corridas son propios.

