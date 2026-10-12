# JAQUELINE LEONOR GIRABEL — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: JaquelineGirabel
- Repositorio: https://github.com/JaquelineGirabel/dmeyf2026
- Link posteado: https://github.com/JaquelineGirabel/dmeyf2026
- Commit: 2b071387e3ac2978705e5e0d3c8ac662ff30c67d
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/jaquelinegirabel/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/jaquelinegirabel.json

## Resumen

Repositorio en Python con un paquete propio (competencia_uno/comp/) y un flujo de tres pasos que el README indica para reproducir el último envío: el notebook z101_target_sql.ipynb arma clase_ternaria con DuckDB; generate_features_extendido.py agrega 40 variables derivadas, ranks por mes con cero fijo de las variables de montos y lags y deltas de 1 y 2 meses de las variables originales; main.py corre el experimento. El experimento entrena LightGBM con clase binaria (BAJA+1 o BAJA+2 = 1), conserva el 10% de los negativos al entrenar y corrige las probabilidades, busca hiperparámetros con Optuna (60 trials, 5 particiones aleatorias 70/30 de 202103-202105, ganancia con umbral 0.025 / s), mide los 3 trials de mayor valor en 202106 con 20 semillas y elige el de mayor primer cuartil de ganancia. El modelo final se entrena con 202103-202106, promedia 20 semillas y envía los 12058 clientes de mayor probabilidad de 202108. La notebook primerComp_010 contiene el mismo flujo con gráficos y, según el comentario de main.py, sus valores son los del envío original. El repositorio trae además otras 9 notebooks de experimentos con otros flags, un generador de notebooks, las bases de Optuna, los modelos y las predicciones guardadas.

**Qué entrega.** Un CSV sin encabezado con 12058 numero_de_cliente, uno por línea: los de mayor probabilidad promedio (20 semillas) en 202108. El archivo no está en el repositorio (el .gitignore excluye *.csv y submits/); registro.md lista dos archivos generados por main.py y el README nombra el envío de referencia ..._optumbral_ajustado_trial49_top12058_20261007_182001.csv.

**Cómo se ejecuta.** Según el README, desde la raíz: crear el entorno con python3 -m venv .venv e instalar con pip install -r requirements.txt; ejecutar z101_target_sql.ipynb para generar competencia_01.csv en competencia_uno/; ejecutar python competencia_uno/generate_features_extendido.py, que genera el .parquet; y por último .venv/bin/python competencia_uno/main.py. Opcional: main.py --comparar <csv> compara el resultado con el envío de referencia. El README agrega que main.py carga de db/, modelos/ y resultados/ lo que ya está calculado.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria, positivo = BAJA+1 o BAJA+2 y CONTINUA = 0 (CLASE_OBJETIVO = 'baja1y2'). La ganancia se calcula siempre con los BAJA+2 reales (clase_binaria).
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** UNDERSAMPLING = 0.1: en cada entrenamiento se conservan todos los positivos de la etiqueta de entrenamiento y el 10% de los negativos, elegidos al azar sin reposición con la semilla del modelo (cada semilla usa su propia muestra). Las probabilidades se corrigen con p·r / (p·r + 1 − p) antes de aplicar el umbral, medir o promediar. No se submuestrean la parte de validación de Optuna, el mes de test ni el mes a predecir.
- **Calidad de datos:** No se observa en el código un tratamiento de variables rotas por mes. En el cálculo de las 40 variables derivadas, los valores vacíos, NA, NaN o null se leen como 0 (parse_float); las variables contra el mes anterior quedan vacías o en 0 cuando el mes previo del cliente no es el consecutivo, y ese caso se marca con flag_gap_mes. armar_particion y armar_prediccion cortan con error si un mes de entrenamiento o de test tiene clase_ternaria incompleta.
- **Drifting:** Rank percentil dentro de cada mes con cero fijo (positivos en (0, 1], negativos en [−1, 0), cero en 0) para las variables cuyo nombre empieza con m, Visa_m o Master_m, agregado como columnas <var>_rank; las columnas en pesos se conservan. Además, percentil dentro del mes de mcuentas_saldo, mpayroll y Visa_mconsumototal (rank_saldo_mes, rank_mpayroll_mes, rank_visa_consumo_mes).
- **Variables dentro del mes:** tiene_payroll, saldo_vacio (mcuentas_saldo < 1000), activo_digital (thomebanking = 1 o cmobile_app_trx > 0), ratio_uso_limite_visa y ratio_uso_limite_master (saldo / límite), ratio_consumo_vs_limite_visa y _master (consumo / límite), ratio_pagado_vs_deuda_visa, flag_pago_minimo, flag_paga_solo_minimo (pagado ≤ 1,15 × pago mínimo), rango_productos_ord (cproductos en 4 tramos), total_deuda (saldo Visa + saldo Master), cseguros_total (suma de 4 contadores de seguros), flag_mora_visa, flag_mora_master y flag_mora. Los cocientes quedan vacíos cuando el denominador no es positivo.
- **Variables históricas:** Lag 1 y lag 2 y delta 1 y delta 2 de las variables originales (152 según el docstring), uniendo la tabla consigo misma por cliente y mes calendario. Sobre el mes anterior consecutivo: lag de ctrx_quarter, mcuentas_saldo, cpayroll_trx y Visa_mconsumototal; deltas de ctrx_quarter, saldo, mpayroll, cproductos y débitos automáticos; ratio_saldo = (actual − anterior) / max(|anterior|, 1000); flags de cambio (perdió sueldo, tarjeta sin consumo, canceló seguro, cerró plazo fijo, dejó el canal digital, nueva mora); rachas de meses seguidos con baja de ctrx_quarter y de saldo; delta_rank_saldo_mes y flag_gap_mes. ctrx_quarter_slope_3: pendiente de regresión de ctrx_quarter contra cliente_antiguedad en una ventana de hasta 4 meses (regr_slope de DuckDB). El docstring indica que no se calcula lag 3.
- **Selección de variables:** No se observa en el código una selección de variables: el modelo usa todas las columnas del dataset extendido salvo clase_ternaria y clase_binaria; numero_de_cliente y foto_mes quedan como variables (DROP_NUMERO_CLIENTE = False).
- **Optimización de hiperparámetros:** Optuna (create_study con direction='maximize' y almacenamiento SQLite por experimento), 60 trials (config.N_TRIALS). Espacio 'it01_bordes': num_leaves 4-64, learning_rate 0.003-0.1, min_data_in_leaf 200-8000, lambda_l1 0.01-10 y lambda_l2 0.01-100 en escala logarítmica; feature_fraction 0.2-0.9 y bagging_fraction 0.2-1.0; bagging_freq = 1. Cada trial entrena en 5 particiones estratificadas 70/30 de 202103-202105 (con submuestreo sólo en el 70%), hasta 3000 rondas con early stopping de paciencia min(50 + 5/learning_rate, 500). El valor del trial es el máximo de la curva promedio de ganancia con p ≥ 0.025 / s sobre los BAJA+2 reales, y la ronda de ese máximo se guarda como best_iter.
- **Hiperparámetros finales:** Trial 49 del estudio (según registro.md). Según la base de Optuna y el modelo guardado que trae el repositorio: num_leaves 35, learning_rate 0.02959, min_data_in_leaf 244, feature_fraction 0.6736, bagging_fraction 0.7136, lambda_l1 0.0440, lambda_l2 2.1226 y 522 árboles (best_iter). Fijos en el código: objective binary, boosting_type gbdt, bagging_freq 1, max_bin 31, first_metric_only True, boost_from_average True, feature_pre_filter False.
- **Semillas:** config.SEMILLA = 6389; generar_semillas fija np.random.seed(6389) y sortea 50 enteros distintos menores a 1.000.000. La primera se usa en Optuna (particiones, submuestreo y semilla del modelo) y en los modelos de una semilla; las primeras 20 (config.N_SEMILLAS), en la prueba de semillas y en el ensamble.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio de las probabilidades corregidas de 20 modelos LightGBM con los mismos hiperparámetros y la misma cantidad de árboles, cada uno entrenado con una semilla distinta y con la muestra de submuestreo de esa semilla.
- **Corte:** Cantidad fija: los 12058 clientes de mayor probabilidad promedio (CONFIG['CORTE'] = 12058, escrito a mano). El código admite también 'umbral' (p ≥ 0.025 / s). En la salida guardada de la notebook 010, 12058 es la cantidad de envíos de máxima ganancia del ensamble de 20 semillas en 202106. guardar_submit exige entre 8000 y 15000 clientes.
- **Validación:** Dos niveles. Dentro de Optuna: 5 particiones aleatorias estratificadas 70/30 de los meses 202103-202105. Fuera: el mes 202106 como test; ahí se miden el trial de mayor valor, los 3 trials de mayor valor (con una semilla y con 20) y el modelo elegido (una semilla y ensamble), con ganancia (1.072.500 por BAJA+2 enviado y −27.500 por el resto), KS y la comparación entre p ≥ umbral y el corte de máxima ganancia. El modelo se elige entre esos 3 por mayor primer cuartil de ganancia en 202106 entre semillas. El código imprime un AVISO cuando un mes de train es posterior al mes de test menos 2, que es el caso de 202105 con test 202106.
- **Salidas:** main.py escribe competencia_uno/<experimento>_trial49_top12058_<fecha_hora>.csv (ids sin encabezado) y agrega una fila a competencia_uno/registro.md. Guarda además el estudio de Optuna en db/<experimento>.db, los modelos en modelos/<experimento>/*.txt, las predicciones de los ensambles en resultados/<experimento>/*.npy y las tablas df_top3.csv y df_semillas_20semillas.csv. El repositorio trae las bases, los modelos y los .npy; el .gitignore excluye *.csv, *.parquet y submits/.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Técnicas sólo exploradas

- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Corta por umbral de probabilidad (`corte.umbral_probabilidad`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: no
- Entorno declarado: requirements.txt lista 11 paquetes con versión mínima (pandas>=2.0.0, pyarrow>=15.0.0, numpy>=1.24.0, lightgbm>=4.0.0, optuna>=3.5.0, scikit-learn>=1.3.0, scipy>=1.11.0, plotly>=5.18.0, tqdm>=4.66.0, nbformat>=5.9.0, ipykernel>=6.29.0). El README indica un entorno virtual creado con python3 -m venv. El docstring de generate_features_extendido.py pide Python 3.10 o más nuevo y duckdb, que no figura en requirements.txt; el notebook z101 instala jupysql y duckdb-engine con %pip y usa la ruta /home/jaqueline/Desktop/DMEyF/dmeyf2026/. No se declara máquina ni sistema operativo.

## Pasos del camino de la entrega

1. **Construcción de clase_ternaria.** El notebook carga competencia_01_crudo.csv en DuckDB, cruza todos los clientes con todos los periodos, marca la presencia del cliente en el mes y en los dos siguientes y asigna CONTINUA, BAJA+1 o BAJA+2; exporta competencia_uno/competencia_01.csv. (`z101_target_sql.ipynb` líneas 209–235; `z101_target_sql.ipynb` líneas 295–297)
2. **Variables derivadas dentro del mes.** generar_final_csv recorre el CSV cliente por cliente y calcula indicadores, cocientes y sumas con datos del mismo mes: uso de límites de tarjeta, deuda total, seguros, mora, pago mínimo, canal digital y tramo de cantidad de productos. (`competencia_uno/generate_features_extendido.py` líneas 238–276)
3. **Variables contra el mes anterior, percentiles mensuales y tendencia.** Sólo cuando el mes previo del cliente es el consecutivo calcula lags, deltas, ratio_saldo, flags de cambio y rachas; después reemplaza saldo, mpayroll y consumo Visa por su percentil dentro del mes, calcula el delta del percentil de saldo y obtiene ctrx_quarter_slope_3 con regr_slope de DuckDB sobre una ventana de 4 filas. (`competencia_uno/generate_features_extendido.py` líneas 278–330; `competencia_uno/generate_features_extendido.py` líneas 390–431; `competencia_uno/generate_features_extendido.py` líneas 440–455)
4. **Ranks con cero fijo, lags y deltas de 1 y 2 meses.** main agrega <var>_rank para las variables de montos y <var>_lag1, _lag2, _delta1 y _delta2 para las variables originales, descarta las que repiten columnas ya existentes y escribe competencia_01_extendido.parquet. (`competencia_uno/generate_features_extendido.py` líneas 508–514; `competencia_uno/generate_features_extendido.py` líneas 539–574)
5. **Configuración del experimento.** CONFIG fija dataset 'extendido', espacio 'it01_bordes', train 202103-202105, test 202106, undersampling 0.1, clase 'baja1y2', métrica 'umbral_ajustado', train final 202103-202106, predicción 202108 y corte 12058. Con esos flags se crea un Experimento, cuyo tag da nombre a la base de Optuna y a las carpetas de modelos y resultados, y se generan las semillas. (`competencia_uno/main.py` líneas 29–60; `competencia_uno/main.py` líneas 136–151; `competencia_uno/comp/experimento.py` líneas 77–94; `competencia_uno/comp/config.py` líneas 76–83)
6. **Carga de datos y partición train / test.** Lee el parquet, pasa las columnas float64 a float32 y agrega clase_binaria (BAJA+2 = 1). armar_particion junta los meses de train, arma la etiqueta de entrenamiento (BAJA+1 o BAJA+2 = 1), calcula el umbral 0.025 / s con s = BAJA+2 / positivos de entrenamiento y separa el mes de test. (`competencia_uno/comp/datos.py` líneas 26–61; `competencia_uno/comp/particiones.py` líneas 23–66; `competencia_uno/main.py` líneas 153–156)
7. **Submuestreo y corrección de probabilidades.** Para cada entrenamiento se toma un subset del lgb.Dataset con todos los positivos y el 10% de los negativos, sorteados con la semilla; las probabilidades que predice el modelo se corrigen con p·r / (p·r + 1 − p). (`competencia_uno/comp/undersampling.py` líneas 18–33; `competencia_uno/comp/undersampling.py` líneas 56–61)
8. **Búsqueda de hiperparámetros con Optuna.** Abre o crea el estudio del experimento y corre los trials que faltan hasta 60. Cada trial entrena en 5 particiones 70/30 de los meses de train con early stopping y se puntúa con el máximo de la curva promedio de ganancia; la ronda del máximo queda como best_iter. (`competencia_uno/comp/optimizacion_optuna.py` líneas 39–53; `competencia_uno/comp/optimizacion_optuna.py` líneas 117–172; `competencia_uno/comp/optimizacion_optuna.py` líneas 202–208; `competencia_uno/main.py` líneas 158–162)
9. **Top 3 trials y prueba con 20 semillas.** Los 3 trials de mayor valor se entrenan con todos los meses de train y se miden en 202106; cada uno se reentrena con 20 semillas y se calculan media, desvío, mínimo, máximo, mediana y cuartiles de la ganancia. (`competencia_uno/main.py` líneas 164–182; `competencia_uno/comp/modelos.py` líneas 86–132)
10. **Elección del modelo.** Con TRIAL_ELEGIDO = None y CRITERIO_ELEGIDO = 'semillas' se toma, entre los 3, el trial con mayor primer cuartil de ganancia entre semillas; de él salen los hiperparámetros y la cantidad de árboles. (`competencia_uno/main.py` líneas 201–221; `competencia_uno/comp/modelos.py` líneas 135–140)
11. **Medición en el mes de test con una semilla y con ensamble.** Para 202106 calcula la predicción del modelo de una semilla y el promedio de 20 semillas, e imprime KS, probabilidad media, envíos y ganancia con p ≥ umbral, envíos y ganancia del corte de máxima ganancia y la ganancia de franja. (`competencia_uno/main.py` líneas 223–242; `competencia_uno/comp/metricas.py` líneas 92–129)
12. **Ensayo de reentrenamiento.** Con MESES_TRAIN_EXTRA = 202103-202105 y MES_TEST_EXTRA = 202106, iguales a los del experimento, reutiliza la misma partición, entrena o carga el modelo elegido, calcula el ensamble e imprime la misma tabla de métricas. (`competencia_uno/main.py` líneas 244–281)
13. **Entrenamiento final y predicción de 202108.** Arma el train con 202103-202106 y la misma etiqueta, entrena 20 modelos con los hiperparámetros y árboles elegidos (uno por semilla, cada uno con su muestra), predice 202108, corrige y promedia; si el .npy del promedio existe, lo carga. (`competencia_uno/main.py` líneas 283–297; `competencia_uno/comp/entrega.py` líneas 25–62; `competencia_uno/comp/ensamble.py` líneas 12–34)
14. **Corte y archivo de salida.** Selecciona los 12058 numero_de_cliente de mayor probabilidad, valida formato y cantidad (entre 8000 y 15000), escribe el CSV con fecha y hora en el nombre dentro de competencia_uno/ y agrega una fila a registro.md. (`competencia_uno/main.py` líneas 299–309; `competencia_uno/comp/entrega.py` líneas 65–120; `competencia_uno/registro.md` líneas 1–6)
15. **Comparación opcional con otro archivo.** Con --comparar lee otro CSV de ids e informa cuántos clientes coinciden, cuántos hay sólo en cada archivo y si ambos conjuntos son idénticos. (`competencia_uno/main.py` líneas 311–318)

## Archivos

- `requirements.txt` · configuracion · Texto · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/requirements.txt.txt) — Lista de 11 dependencias con versión mínima: pandas, pyarrow, numpy, lightgbm, optuna, scikit-learn, scipy, plotly, tqdm, nbformat e ipykernel.
- `z101_target_sql.ipynb` · principal · Jupyter (python) · 315 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/z101_target_sql.ipynb.txt) — Notebook que carga competencia_01_crudo.csv en DuckDB, construye clase_ternaria (CONTINUA, BAJA+1, BAJA+2) y exporta competencia_01.csv a competencia_uno/. Incluye celdas de texto y consultas de ejemplo sobre WITH y funciones de ventana.
- `README.md` · explicacion · Markdown · 58 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/README.md.txt) — Indica la instalación (entorno virtual y requirements.txt), los tres pasos de ejecución (z101_target_sql.ipynb, generate_features_extendido.py y main.py), la opción --comparar contra el envío de referencia y dónde quedan las salidas. Afirma que main.py está configurado por defecto para reproducir el último submit de la competencia.
- `competencia_uno/registro.md` · explicacion · Markdown · 6 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/registro.md.txt) — Tabla de submits generados, escrita por entrega.anotar_en_registro. Tiene 2 filas, ambas del experimento it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optumbral_ajustado: trial 49, train 202103, 202104, 202105 y 202106, corte 12058, 12058 clientes y probabilidad mínima enviada 0.0321, con sello de fecha 20261010.
- `competencia_uno/generate_features_extendido.py` · principal · Python · 588 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/generate_features_extendido.py.txt) — Genera competencia_01_extendido.parquet a partir de competencia_01.csv: primero calcula 40 variables derivadas (indicadores, cocientes, lags y deltas del mes anterior, percentiles mensuales y una tendencia) y después agrega ranks por mes con cero fijo, lags y deltas de 1 y 2 meses.
- `competencia_uno/main.py` · principal · Python · 322 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/main.py.txt) — Script que corre el experimento completo desde la terminal con los valores de CONFIG (o de la línea de comandos): datos, Optuna, top 3 y prueba de semillas, modelo elegido, medición en el mes de test, ensayo, predicción de 202108 y archivo de salida.
- `competencia_uno/comp/datos.py` · principal · Python · 73 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/comp/datos.py.txt) — Carga del dataset (parquet directo, o CSV con copia en cache/), creación de clase_binaria y separación de X e y por meses.
- `competencia_uno/comp/config.py` · configuracion · Python · 83 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/comp/config.py.txt) — Constantes y rutas compartidas: datasets, carpetas de salida, matriz de ganancia, umbral, clases objetivo, métricas de Optuna, meses por defecto, semilla, parámetros fijos de LightGBM, cantidad de trials y de semillas.
- `competencia_uno/comp/undersampling.py` · principal · Python · 61 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/comp/undersampling.py.txt) — Submuestreo de los negativos del train por semilla y corrección de las probabilidades que produce un modelo entrenado con esa muestra.
- `competencia_uno/comp/particiones.py` · principal · Python · 85 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/comp/particiones.py.txt) — Arma el train y el test de un experimento, la etiqueta de entrenamiento según la clase objetivo y el umbral de decisión.
- `competencia_uno/comp/__init__.py` · principal · Python · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/comp/__init__.py.txt) — Archivo de inicio del paquete comp: sólo contiene un docstring con la lista de módulos y qué hace cada uno.
- `competencia_uno/comp/optimizacion_optuna.py` · principal · Python · 217 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/comp/optimizacion_optuna.py.txt) — Espacios de búsqueda, funciones objetivo y manejo del estudio de Optuna. La función objetivo usada con clase 'baja1y2' y métrica 'umbral_ajustado' es crear_objetivo_cv_metrica.
- `competencia_uno/comp/experimento.py` · principal · Python · 134 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/comp/experimento.py.txt) — Dataclass Experimento: guarda los flags de una corrida, los valida y deriva de ellos el nombre (tag), la base de Optuna, las carpetas de modelos y resultados, la semilla y los avisos.
- `competencia_uno/comp/modelos.py` · principal · Python · 140 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/comp/modelos.py.txt) — Entrenamiento o carga de modelos LightGBM, evaluación de los trials de mayor valor en el mes de test, prueba con varias semillas y elección por primer cuartil.
- `competencia_uno/comp/entrega.py` · principal · Python · 129 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/comp/entrega.py.txt) — Arma el train final y el mes a predecir, obtiene la predicción del ensamble, selecciona los clientes según el corte, escribe el CSV y lo anota en registro.md.
- `competencia_uno/comp/ensamble.py` · principal · Python · 34 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/comp/ensamble.py.txt) — Promedio de las predicciones de un mismo modelo entrenado con varias semillas, con guardado en .npy.
- `competencia_uno/comp/graficos.py` · secundario · Python · 186 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/comp/graficos.py.txt) — Figuras de plotly para las métricas (boxplot por semillas, distribución por clase, KS, ganancia acumulada, lift y captura). Lo usan las notebooks; main.py no lo importa.
- `competencia_uno/comp/metricas.py` · principal · Python · 153 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/comp/metricas.py.txt) — Funciones de ganancia (por umbral, por franja, acumulada), métrica custom para LightGBM, KS, lift y captura.
- `competencia_uno/notebooks/primerComp_008_it01_bordes_train202103-202104-202105_test202106_dsextendido_us10.ipynb` · secundario · Jupyter (python) · 384 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/notebooks/primerComp_008_it01_bordes_train202103-202104-202105_test202106_dsextendido_us10.ipynb.txt) — Experimento 008: como el 007, con UNDERSAMPLING = 0.1, clase 'baja2' y CORTE = 12283.
- `competencia_uno/notebooks/primerComp_007_it01_bordes_train202103-202104-202105_test202106_dsextendido.ipynb` · secundario · Jupyter (python) · 384 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/notebooks/primerComp_007_it01_bordes_train202103-202104-202105_test202106_dsextendido.ipynb.txt) — Experimento 007: dataset 'extendido', train 202103-202105, test 202106, sin undersampling, N_TRIALS = 23 y CORTE = 'umbral'.
- `competencia_uno/notebooks/primerComp_006_it01_bordes_cv_dsextendido.ipynb` · secundario · Jupyter (python) · 384 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/notebooks/primerComp_006_it01_bordes_cv_dsextendido.ipynb.txt) — Experimento 006: como el 002, con el dataset 'extendido'; TRIAL_ELEGIDO = 37 y CORTE = 11337.
- `competencia_uno/notebooks/nuevo_experimento.py` · secundario · Python · 154 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/notebooks/nuevo_experimento.py.txt) — Crea una notebook de experimento a partir de la plantilla primerComp_001.ipynb: copia la plantilla, fija los flags con expresiones regulares, borra las salidas, le pone el número siguiente y agrega una fila a EXPERIMENTOS.md.
- `competencia_uno/notebooks/primerComp_002_it01_bordes_cv.ipynb` · secundario · Jupyter (python) · 384 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/notebooks/primerComp_002_it01_bordes_cv.ipynb.txt) — Experimento 002: dataset 'final', espacio 'it01_bordes', train 202103, test 202105, ensayo extra con train 202103-202105 y test 202106, CORTE = 'umbral'. Usa una versión de la plantilla sin los flags CLASE_OBJETIVO ni METRICA_OPTUNA.
- `competencia_uno/notebooks/primerComp_011_it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optfranja.ipynb` · secundario · Jupyter (python) · 406 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/notebooks/primerComp_011_it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optfranja.ipynb.txt) — Experimento 011: como el 010, con METRICA_OPTUNA = 'franja' (ganancia promedio enviando del 5% al 9% de los clientes), N_TRIALS = 45 y CORTE = 11285.
- `competencia_uno/notebooks/primerComp_012_it01_bordes_train202103-202104-202105_test202106_dsextendido_us5_clasebaja1y2_optumbral_ajustado.ipynb` · secundario · Jupyter (python) · 406 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/notebooks/primerComp_012_it01_bordes_train202103-202104-202105_test202106_dsextendido_us5_clasebaja1y2_optumbral_ajustado.ipynb.txt) — Experimento 012: como el 010, con UNDERSAMPLING = 0.05, N_TRIALS = 40 y CORTE = 12728.
- `competencia_uno/notebooks/primerComp_004_it01_bordes_sinid.ipynb` · secundario · Jupyter (python) · 384 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/notebooks/primerComp_004_it01_bordes_sinid.ipynb.txt) — Experimento 004: como el 002, con DROP_NUMERO_CLIENTE = True (numero_de_cliente no se usa como variable) y N_TRIALS = 80.
- `competencia_uno/notebooks/primerComp_009_it01_bordes_train202103-202104-202105_test202106_dsextendido_us5.ipynb` · secundario · Jupyter (python) · 384 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/notebooks/primerComp_009_it01_bordes_train202103-202104-202105_test202106_dsextendido_us5.ipynb.txt) — Experimento 009: como el 007, con UNDERSAMPLING = 0.05, clase 'baja2' y CORTE = 11429.
- `competencia_uno/notebooks/primerComp_001.ipynb` · secundario · Jupyter (python) · 403 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/notebooks/primerComp_001.ipynb.txt) — Plantilla de las notebooks de experimento. Flags: dataset 'final', espacio 'it00_z601', train 202103, test 202105, clase 'baja2', métrica 'umbral', sin undersampling; con esa combinación el modelo elegido usa los parámetros fijos del notebook de clase y 250 árboles. CORTE = 'umbral'.
- `competencia_uno/notebooks/primerComp_010_it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optumbral_ajustado.ipynb` · principal · Jupyter (python) · 406 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jaquelinegirabel/competencia_uno/notebooks/primerComp_010_it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optumbral_ajustado.ipynb.txt) — Notebook del experimento 010, con los mismos flags que CONFIG de main.py y el mismo flujo, más las figuras de Optuna y de las métricas. Guarda el CSV en submits/. El comentario de main.py indica que sus valores reproducen el submit ..._trial49_top12058_20261007_182001.csv.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### z101_target_sql.ipynb

Notebook que carga competencia_01_crudo.csv en DuckDB, construye clase_ternaria (CONTINUA, BAJA+1, BAJA+2) y exporta competencia_01.csv a competencia_uno/. Incluye celdas de texto y consultas de ejemplo sobre WITH y funciones de ventana.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–18] Texto con la consigna (crear competencia_01.csv con clase_ternaria a partir de
#   competencia_01_crudo.csv) y celda que arma la ruta del dataset crudo en
#   /home/jaqueline/Desktop/DMEyF/dmeyf2026/; si el archivo no existe corta con FileNotFoundError.
#%% celda 1 [texto]
# Crear la clase  Target

Hay que crear el archivo competencia_01.csv, usando el competencia_01_crudo.csv con una variable adicional llamada clase_ternaria, que contenga las categorías **CONTINUA, BAJA+1 y BAJA+2**

Para esto primero es necesario descargar el dataset.

#%% celda 2 [código]
import os

dataset_filename = "competencia_01_crudo.csv"
dataset_path = "/home/jaqueline/Desktop/DMEyF/dmeyf2026/"
file_path = os.path.join(dataset_path, dataset_filename)

if not os.path.isfile(file_path):
    raise FileNotFoundError(f"No se encontró el dataset en: {file_path}")

print(f"Usando dataset local: {file_path}")

# [Anotación · líneas 20–50] Instala jupysql y duckdb-engine con %pip, carga la extensión sql, configura
#   SqlMagic (autopandas, sin feedback) y abre una conexión DuckDB en memoria; ejecuta una consulta de prueba.
#%% celda 3 [texto]
Luego, para generar la clase vamos a usar el lenguaje **SQL**, a través de una base de datos **OLAP** llamada **DuckDB**.

La documentación la puede encontrar [aquí](https://duckdb.org/docs/current/) Procedemos a instalar componentes adicionales para utilizar directamente el lenguaje en la notebook

#%% celda 4 [código]
%pip install --upgrade jupysql duckdb-engine "wcwidth>=0.8.0"

#%% celda 5 [texto]
Configuramos el entorno de ejecución. Si ya tiene todo instalado, solo necesita ejecutar esta celda para empezar a usar **duckdb**

#%% celda 6 [código]
import duckdb
import pandas as pd

%load_ext sql
%config SqlMagic.autopandas = True
%config SqlMagic.feedback = False
%config SqlMagic.displaycon = False

%sql duckdb:///

#%% celda 7 [texto]
Support for third party widgets will remain active for the duration of the session. To disable support:

#%% celda 8 [texto]
Y ya podemos usar **SQL** dentro de una notebook!

#%% celda 9 [código]
%%sql
select 'hola mundo'

# [Anotación · líneas 52–77] Carga el CSV crudo en la tabla competencia_01_crudo con read_csv_auto, muestra 5
#   filas y cuenta las filas de cada foto_mes.
#%% celda 10 [texto]
Cargamos el archivo `.csv` a una tabla pasando su ubicación

#%% celda 11 [código]
%%sql
SET enable_progress_bar = false;

create or replace table competencia_01_crudo as
select
    *
from read_csv_auto("{{dataset_path + dataset_filename}}")

#%% celda 12 [texto]
Hagamos unas queries básicas para comprobar que todo esta funcionando bien.

#%% celda 13 [código]
%sql select * from competencia_01_crudo limit 5

#%% celda 14 [código]
%%sql
select
    foto_mes
    , count(*) as cantidad -- cuenta cuantos casos hay en cada foto_mes
                           -- y lo guarda en un campo llamado cantidad
from competencia_01_crudo
group by foto_mes

# [Anotación · líneas 79–143] Texto y consultas de ejemplo: cláusula WITH (promedio de mrentabilidad por
#   cliente comparado con el valor de cada mes) y funciones de ventana lead y lag de 1 y 2 meses para el cliente
#   12159854.
#%% celda 15 [texto]
Antes de avanzar con la construcción del **target** veamos repasemos un poco de **SQL**

## WITH

Un escenario común es necesitar realizar una consulta a no a una tabla, sino a otra consulta. Una forma tradicional de hacerlo es usando es:
* Creando una tabla temporal con esa consulta
* Usando `selects from select`.

Esta necesidad es muy común, pero como todo en la vida hay peros.
- Crear una tabla en una base de datos que va a ser usada UNA SOLA VEZ ensucia los esquemas con un montón de tablas que no son útiles y además del desorden ocupan espacio innecesario
- El `select from select`, debe ser de las cosas peor vistas por los administradores de BBDD. Tienen sus razones técnicas, en general la recomendación es no usarlo a menos que uno conozca bien como funciona la base de datos por dentro, ya que hay casos donde terminan ocasionando muchos problemas

Y que hacer? bueno hay una clausula en **SQL** llamada `WITH`, que nos permite crear esas (plural) tablas para ser usadas en la **query** principal. Ejemplo si queremos comparar el valor de una variable con su promedio a través de todos los meses.

#%% celda 16 [código]
%%sql
with promedios as (
    select
        numero_de_cliente
        , avg(mrentabilidad) as avg_mrentabilidad
    from competencia_01_crudo
    group by numero_de_cliente
) select
    cp.numero_de_cliente
    , cp.foto_mes
    , if(cp.mrentabilidad > p.avg_mrentabilidad, 'mayor', 'menor') as comparacion
from competencia_01_crudo cp
join promedios p using (numero_de_cliente)

#%% celda 17 [texto]
- Usar esa clausula tiene muchos beneficios, entre ellos sumar legibilidad de código y le permite al motor de **SQL** optimizar mejor, ya que entiende todo lo que se buscar hacer y planifica como resolverlo en el menor tiempo posible.

**NOTA**: Hay un tipo de tabla que se llaman temporales, que se borran solas una vez que uno se desconecta de la base de datos. Es una mejor alternativa frente al `CREATE`, sin embargo si la tabla que se esta creando se usa una sola vez es conveniente usar el `WITH` porque permite optimizar la ejecución. Si esa tabla va a ser usada mas de una vez dentro del proceso, las tablas temporales son la mejor opción.

#%% celda 18 [texto]
# Funciones Analíticas

Las funciones analíticas en SQL son un conjunto de funciones que te permiten realizar cálculos avanzados sobre un conjunto de filas relacionadas dentro de una consulta conservando las filas individuales y calculando sobre ventanas de datos relacionadas.

Veamos un ejemplo para que quede más claro:

#%% celda 19 [código]
%%sql
select
    numero_de_cliente
    , foto_mes
    , mrentabilidad
from competencia_01_crudo
where numero_de_cliente = 12159854
order by foto_mes

#%% celda 20 [código]
%%sql
select
    numero_de_cliente
    , foto_mes
    , mrentabilidad
    , lead(mrentabilidad, 1) over (partition by numero_de_cliente order by foto_mes) as mrentabilidad_mas_1
    , lag(mrentabilidad, 1) over (partition by numero_de_cliente order by foto_mes) as mrentabilidad_menos_1
    , lead(mrentabilidad, 2) over (partition by numero_de_cliente order by foto_mes) as mrentabilidad_mas_2
    , lag(mrentabilidad, 2) over (partition by numero_de_cliente order by foto_mes) as mrentabilidad_menos_2
from competencia_01_crudo
where numero_de_cliente = 12159854
order by foto_mes

# [Anotación · líneas 145–207] Caso del cliente 60112254: lista sus meses, genera todas las combinaciones
#   cliente × periodo con cross join y marca con mes_0 = 1 o 0 si el cliente tiene fila en cada periodo.
#%% celda 21 [texto]
* Qué paso?
* ¿Cómo esta construyendo las nuevas variables?
* ¿ Nos puede ayudar a construir targets ?

¿Dondé puedo leer un poco más de esta magia negra? https://duckdb.org/docs/sql/window_functions.html

## Los casos raros

Que pasa con el cliente **60112254** y la foto **202104**?

#%% celda 22 [código]
%%sql
select
    numero_de_cliente
    , foto_mes
from competencia_01_crudo
where numero_de_cliente = 60112254
order by foto_mes

#%% celda 23 [texto]
* ¿Cuál debería ser la clase para cada periodo?

### Una pista

Podemos generar todas las posibles combinaciones de clientes y periodos de manera muy simple

#%% celda 24 [código]
%%sql
with periodos as (
  select distinct foto_mes from competencia_01_crudo
), clientes as (
  select distinct numero_de_cliente from competencia_01_crudo
)
select numero_de_cliente, foto_mes from clientes cross join periodos
where numero_de_cliente = 60112254
order by foto_mes

#%% celda 25 [texto]
Solo nos queda saber si estuvo o no el banco el cliente en ese periodo y armar el

#%% celda 26 [código]
%%sql
with periodos as (
    select distinct foto_mes from competencia_01_crudo -- Esto también se puede hacer con secuencias
), clientes as (
    select distinct numero_de_cliente from competencia_01_crudo
), todo as (
    select numero_de_cliente, foto_mes from clientes cross join periodos
)
select
    t.numero_de_cliente
    , t.foto_mes
    , if(c.numero_de_cliente is null, 0, 1) as mes_0
from todo t
left join competencia_01_crudo c using (numero_de_cliente, foto_mes)
where t.numero_de_cliente = 60112254
order by foto_mes

#%% celda 27 [texto]
Antes de continuar, tomémonos un momento para reflexionar. Con todas estas piezas, ¿cómo podemos ensamblar el target?

Una vez que lo tengamos claro sobre el papel, proceda a completar el código que sigue.

# [Anotación · líneas 209–235] Crea la tabla competencia_01: sobre el cruce cliente × periodo calcula mes_0
#   (presencia en el mes) y, con lead, mes_1 y mes_2 (presencia 1 y 2 meses después). Asigna CONTINUA si mes_2 =
#   1; BAJA+1 si mes_1 = 0 y mes_2 es 0 o nulo; BAJA+2 si mes_1 = 1 y mes_2 = 0; nulo en los demás casos.
#   Conserva sólo las filas con mes_0 = 1 y quita las tres columnas auxiliares.
#%% celda 28 [código]
%%sql
create or replace table competencia_01 as
with periodos as (
    select distinct foto_mes from competencia_01_crudo
), clientes as (
    select distinct numero_de_cliente from competencia_01_crudo
), todo as (
    select numero_de_cliente, foto_mes from clientes cross join periodos
), clase_ternaria as (
    select
        c.*
        , if(c.numero_de_cliente is null, 0, 1) as mes_0
        , lead(mes_0, 1) over (partition by t.numero_de_cliente order by foto_mes) as mes_1
        , lead(mes_0, 2) over (partition by t.numero_de_cliente order by foto_mes) as mes_2
        , case
            when mes_2 = 1 then 'CONTINUA'
            when mes_1 = 0 and (mes_2 = 0 or mes_2 is null) then 'BAJA+1'
            when mes_1 = 1 and mes_2 = 0 then 'BAJA+2'
            else null
        end as clase_ternaria
    from todo t
    left join competencia_01_crudo c using (numero_de_cliente, foto_mes)
) select
  * EXCLUDE (mes_0, mes_1, mes_2)
from clase_ternaria
where mes_0 = 1

# [Anotación · líneas 237–258] Celda comentada con la versión de plantilla de la misma consulta, donde
#   clase_ternaria vale null.
#%% celda 29 [código]
# %%sql
# create or replace table competencia_01 as
# with periodos as (
#     select distinct foto_mes from competencia_01_crudo
# ), clientes as (
#     select distinct numero_de_cliente from competencia_01_crudo
# ), todo as (
#     select numero_de_cliente, foto_mes from clientes cross join periodos
# ), clase_ternaria as (
#     select
#         c.*
#         , if(c.numero_de_cliente is null, 0, 1) as mes_0
#         , lead(mes_0, 1) over (partition by t.numero_de_cliente order by foto_mes) as mes_1
#         , lead(mes_0, 2) over (partition by t.numero_de_cliente order by foto_mes) as mes_2
#         , null as clase_ternaria -- Replazar null por la lógica que genera el target
#     from todo t
#     left join competencia_01_crudo c using (numero_de_cliente, foto_mes)
# ) select
#   * EXCLUDE (mes_0, mes_1, mes_2)
# from clase_ternaria
# where mes_0 = 1

# [Anotación · líneas 260–286] Cuenta las filas de competencia_01, pivotea la cantidad de clientes por clase y
#   foto_mes y cuenta el total de filas por clase.
#%% celda 30 [texto]
Revisamos que todo salga como esperamos

#%% celda 31 [código]
%sql select count(*) from competencia_01

#%% celda 32 [texto]
Y vemos la cardinalidad de las clases por periodo

#%% celda 33 [texto]
* ¿Cuál es la nominalidad de cada clase?

#%% celda 34 [código]
%%sql
PIVOT competencia_01
on clase_ternaria
USING count(numero_de_cliente)
GROUP BY foto_mes

#%% celda 35 [código]
%%sql

select 
    clase_ternaria, 
    count(*) as cant,
from competencia_01
group by clase_ternaria

# [Anotación · líneas 288–297] Exporta la tabla a competencia_uno/competencia_01.csv dentro de dataset_path
#   con COPY (FORMAT CSV, HEADER).
#%% celda 36 [texto]
* ¿Cuál es la proporción del target?

## Guardar tabla en .csv

Para guardar a un `.csv` simplemente debe ejecutar la siguiente sentencia

#%% celda 37 [código]
%%sql
COPY competencia_01 TO '{{dataset_path}}/competencia_uno/competencia_01.csv' (FORMAT CSV, HEADER)

# [Anotación · líneas 299–315] Texto final sobre la sintaxis de DuckDB: función IF, SELECT * EXCLUDE y uso de
#   alias.
#%% celda 38 [texto]

## El pato del amor

DuckDB no es una base de datos SQL estándar; su sintaxis moderna facilita significativamente la escritura de consultas. A continuación, te menciono algunas características destacadas:

+ Uso de variables: En DuckDB, no es necesario reescribir las variables; puedes utilizar tus variables una vez definidas, lo que simplifica el código.

+ Función IF: DuckDB soporta la función IF(condición, valor_si_verdadero, valor_si_falso), lo que hace que tu código sea más claro y legible en comparación con el uso de CASE WHEN.

+ Exclusión de campos: Puedes utilizar SELECT * EXCLUDE(field1, ...) para excluir campos específicos de la lista de selección, lo que ahorra tiempo y esfuerzo.

+ Alias en cláusulas: Es posible utilizar alias en las cláusulas WHERE, GROUP BY y HAVING, lo que añade flexibilidad a la escritura de consultas.

+ Uso de alias en cálculos: DuckDB permite el uso de alias dentro del cálculo de otros campos, facilitando la manipulación y transformación de datos en una consulta.

Estas son solo algunas de las capacidades que hacen de DuckDB una herramienta poderosa. Te recomiendo leer la documentación y el blog oficial para explorar más a fondo su potencial.
```

### competencia_uno/generate_features_extendido.py

Genera competencia_01_extendido.parquet a partir de competencia_01.csv: primero calcula 40 variables derivadas (indicadores, cocientes, lags y deltas del mes anterior, percentiles mensuales y una tendencia) y después agrega ranks por mes con cero fijo, lags y deltas de 1 y 2 meses.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–29] Docstring: describe los dos pasos (las 40 variables de competencia_01_final y
#   luego historia e inflación), los grupos nuevos (<var>_rank con cero fijo, <var>_lag1 y _lag2, <var>_delta1 y
#   _delta2 para las 152 variables originales), el motivo por el que no se agrega lag3 (el dataset empieza en
#   202103) y el uso por línea de comandos.
"""Genera competencia_01_extendido.parquet a partir de competencia_01.csv (el dataset crudo).

Es un solo archivo, sin otras dependencias del proyecto: alcanza con tener competencia_01.csv.
Pasos:
1. Calcula las 40 variables de competencia_01_final con el mismo codigo de
   generate_features_final.py (copiado tal cual en generar_final_csv, mas abajo).
2. Agrega las variables de historia e inflacion de abajo.
El resultado es identico al competencia_01_extendido.parquet que se armaba leyendo competencia_01_final.

Grupos nuevos (ver FEATURES.md):
- <var>_rank    (inflacion) rank dentro del mes de las variables de plata, con "cero fijo":
                positivos -> (0, 1], negativos -> [-1, 0), cero -> 0, vacio -> vacio.
                Un saldo en el percentil 80 de marzo y uno en el percentil 80 de agosto valen
                lo mismo aunque en pesos el de agosto sea mas grande por inflacion.
- <var>_lag1, <var>_lag2      valor del mismo cliente 1 y 2 meses calendario antes
                              (vacio si no estaba ese mes o si el mes no existe en el dataset).
- <var>_delta1, <var>_delta2  valor actual menos lag1 / lag2.
Lags y deltas se calculan para las 152 variables originales.

No se agrega lag3: el dataset empieza en 202103, asi que lag3 recien existe desde 202106 y
estaria vacio en todos los meses de train.

Uso (por defecto lee y escribe en la carpeta del script):
    python generate_features_extendido.py
    python generate_features_extendido.py --entrada otra/competencia_01.csv --salida otra/competencia_01_extendido.parquet
    python generate_features_extendido.py --guardar-final    # ademas deja competencia_01_final.csv

Necesita: pandas, numpy, pyarrow y duckdb (Python 3.10 o mas nuevo).
"""
# [Anotación · líneas 30–55] Importa csv, bisect, tempfile, duckdb (termina con un mensaje si falta), numpy y
#   pandas. Define las rutas por defecto en la carpeta del script (competencia_01.csv y
#   competencia_01_extendido.parquet), las claves numero_de_cliente y foto_mes, y sumar_meses, que suma n meses
#   a un AAAAMM.
import argparse
import bisect
import csv
import tempfile
import time
from collections import defaultdict
from pathlib import Path

try:
    import duckdb
except ImportError:
    raise SystemExit('Falta duckdb (lo usa ctrx_quarter_slope_3). Instalarlo con: pip install duckdb')
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
ENTRADA = AQUI / 'competencia_01.csv'
SALIDA = AQUI / 'competencia_01_extendido.parquet'
CLAVES = ['numero_de_cliente', 'foto_mes']


def sumar_meses(mes, n):
    """sumar_meses(202105, -2) -> 202103. Funciona cruzando anios."""
    anio, m = divmod(mes, 100)
    total = anio * 12 + (m - 1) + n
    return (total // 12) * 100 + total % 12 + 1


# [Anotación · líneas 58–102] Inicio de generar_final_csv: lee el encabezado del CSV y guarda la posición de
#   las 25 columnas que usa (claves, cpayroll_trx, mcuentas_saldo, ctrx_quarter, thomebanking, cmobile_app_trx,
#   límites, saldos, consumos y pagos de Visa y Master, cproductos, mpayroll, delinquency, cplazo_fijo, los
#   cuatro seguros y ccuenta_debitos_automaticos).
# ---------------------------------------------------------------------------------------------
# 1. Las 40 variables de competencia_01_final (codigo de generate_features_final.py, sin cambios)
# ---------------------------------------------------------------------------------------------
def generar_final_csv(input_file, output_file):
    """Codigo de generate_features_final.py sin cambios: lee input_file (competencia_01.csv)
    y escribe output_file con las 195 columnas de competencia_01_final."""
    input_file, output_file = str(input_file), str(output_file)
    input_file_sql = input_file.replace("'", "''")

    start_time = time.time()
    print("Iniciando procesamiento de competencia_01.csv (version final)...")


    # 1. Leer encabezados
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

    idx = {h: i for i, h in enumerate(headers)}

    num_cli_idx = idx["numero_de_cliente"]
    foto_mes_idx = idx["foto_mes"]
    payroll_trx_idx = idx["cpayroll_trx"]
    saldo_idx = idx["mcuentas_saldo"]
    ctrx_idx = idx["ctrx_quarter"]
    thb_idx = idx["thomebanking"]
    mob_idx = idx["cmobile_app_trx"]
    visa_lim_idx = idx["Visa_mlimitecompra"]
    visa_saldo_idx = idx["Visa_msaldototal"]
    visa_pmin_idx = idx["Visa_mpagominimo"]
    visa_cons_idx = idx["Visa_mconsumototal"]
    visa_pagado_idx = idx["Visa_mpagado"]
    cprod_idx = idx["cproductos"]
    master_cons_idx = idx["Master_mconsumototal"]
    master_lim_idx = idx["Master_mlimitecompra"]
    master_saldo_idx = idx["Master_msaldototal"]
    mpayroll_idx = idx["mpayroll"]
    visa_delinq_idx = idx["Visa_delinquency"]
    master_delinq_idx = idx["Master_delinquency"]
    cplazo_fijo_idx = idx["cplazo_fijo"]
    cseguro_vida_idx = idx["cseguro_vida"]
    cseguro_auto_idx = idx["cseguro_auto"]
    cseguro_vivienda_idx = idx["cseguro_vivienda"]
    cseguro_accidentes_idx = idx["cseguro_accidentes_personales"]
    ccuenta_deb_auto_idx = idx["ccuenta_debitos_automaticos"]

# [Anotación · líneas 104–157] Declara los nombres de las columnas nuevas en tres listas: 20 en
#   new_headers_v1, 19 en new_headers_v2 (mora, rachas, seguros, ranks, flag_gap_mes) y 1 en new_headers_v3
#   (ctrx_quarter_slope_3). Arma el encabezado de salida y un índice de posición para las de v1 y v2.
    # Columnas heredadas de generate_features.py (con 3 formulas corregidas, ver README/MD)
    new_headers_v1 = [
        "tiene_payroll",
        "saldo_vacio",
        "activo_digital",
        "ratio_uso_limite_visa",
        "flag_pago_minimo",
        "rango_productos_ord",
        "ctrx_quarter_lag1",
        "mcuentas_saldo_lag1",
        "cpayroll_trx_lag1",
        "Visa_mconsumototal_lag1",
        "delta_ctrx_quarter",
        "delta_mcuentas_saldo",
        "ratio_saldo",
        "flag_perdio_sueldo",
        "flag_apago_tarjeta",
        "rank_saldo_mes",
        "ratio_consumo_vs_limite_master",
        "delta_mpayroll",
        "total_deuda",
        "ratio_pagado_vs_deuda_visa",
    ]

    # Columnas nuevas de esta ronda
    new_headers_v2 = [
        "flag_mora_visa",
        "flag_mora_master",
        "flag_mora",
        "flag_nueva_mora",
        "flag_paga_solo_minimo",
        "racha_baja_ctrx_quarter",
        "racha_baja_saldo",
        "delta_cproductos",
        "delta_ccuenta_debitos_automaticos",
        "cseguros_total",
        "flag_cancelo_seguro",
        "flag_cerro_plazo_fijo",
        "flag_dejo_digital",
        "ratio_uso_limite_master",
        "ratio_consumo_vs_limite_visa",
        "rank_mpayroll_mes",
        "rank_visa_consumo_mes",
        "delta_rank_saldo_mes",
        "flag_gap_mes",
    ]

    # Tendencia (regr_slope de DuckDB), agregada a partir de z402_Feature_Engineering_en_SQL.ipynb
    new_headers_v3 = [
        "ctrx_quarter_slope_3",
    ]

    all_headers = headers + new_headers_v1 + new_headers_v2 + new_headers_v3
    new_idx = {h: len(headers) + i for i, h in enumerate(new_headers_v1 + new_headers_v2)}


# [Anotación · líneas 160–183] Funciones auxiliares: parse_float devuelve 0.0 para vacío, NA, NaN o null;
#   fm_to_int pasa AAAAMM a un número de mes corrido; fmt_num escribe los enteros sin decimales; safe_ratio
#   calcula (actual − anterior) / max(|anterior|, 1000).
    def parse_float(v):
        if not v or v in ("NA", "<NA>", "NaN", "null"):
            return 0.0
        try:
            return float(v)
        except ValueError:
            return 0.0


    def fm_to_int(fm):
        fm = int(fm)
        return (fm // 100) * 12 + (fm % 100)


    def fmt_num(v):
        return f"{v:.0f}" if float(v).is_integer() else f"{v}"


    def safe_ratio(curr, prev, floor=1000.0):
        """Cambio relativo acotado: (curr - prev) / max(|prev|, floor).
        Evita el problema de ratio_saldo original (curr/prev con epsilon fijo),
        que producia signos incorrectos cuando el saldo cruza cero."""
        denom = max(abs(prev), floor)
        return (curr - prev) / denom


# [Anotación · líneas 186–236] Carga todas las filas del CSV en un diccionario por cliente, ordena las de cada
#   cliente por foto_mes y, fila por fila, convierte a número las columnas que usa; cseguros_total suma los
#   cuatro contadores de seguros.
    # 2. Leer registros organizados por cliente
    print("Cargando y ordenando historia de clientes...")
    client_records = defaultdict(list)
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            client_records[row[num_cli_idx]].append(row)

    print(f"Total clientes unicos: {len(client_records)} cargados en {time.time() - start_time:.2f}s")

    # 3. Procesar variables estaticas y temporales
    month_saldos = defaultdict(list)
    month_payrolls = defaultdict(list)
    month_visacons = defaultdict(list)
    processed_rows = []

    for cli, rows in client_records.items():
        rows.sort(key=lambda r: int(r[foto_mes_idx]))
        prev = None
        racha_ctrx = 0
        racha_saldo = 0

        for r in rows:
            fm = r[foto_mes_idx]
            fm_num = fm_to_int(fm)
            payroll = parse_float(r[payroll_trx_idx])
            saldo = parse_float(r[saldo_idx])
            ctrx = parse_float(r[ctrx_idx])
            thb = parse_float(r[thb_idx])
            mob = parse_float(r[mob_idx])
            visa_lim = parse_float(r[visa_lim_idx])
            visa_saldo = parse_float(r[visa_saldo_idx])
            visa_pmin = parse_float(r[visa_pmin_idx])
            visa_cons = parse_float(r[visa_cons_idx])
            visa_pagado = parse_float(r[visa_pagado_idx])
            cprod = parse_float(r[cprod_idx])
            master_cons = parse_float(r[master_cons_idx])
            master_lim = parse_float(r[master_lim_idx])
            master_saldo = parse_float(r[master_saldo_idx])
            mpayroll_val = parse_float(r[mpayroll_idx])
            visa_delinq = parse_float(r[visa_delinq_idx])
            master_delinq = parse_float(r[master_delinq_idx])
            cplazo_fijo = parse_float(r[cplazo_fijo_idx])
            ccuenta_deb_auto = parse_float(r[ccuenta_deb_auto_idx])
            cseguros_total = (
                parse_float(r[cseguro_vida_idx])
                + parse_float(r[cseguro_auto_idx])
                + parse_float(r[cseguro_vivienda_idx])
                + parse_float(r[cseguro_accidentes_idx])
            )

# [Anotación · líneas 238–276] Variables del mismo mes: tiene_payroll (cpayroll_trx > 0), saldo_vacio
#   (mcuentas_saldo < 1000), activo_digital (thomebanking = 1 o cmobile_app_trx > 0), ratio_uso_limite_visa
#   (saldo / límite, vacío si no hay límite), flag_pago_minimo, rango_productos_ord (cproductos en 4 tramos:
#   hasta 5, 7, 9 y más de 9), ratio de consumo sobre límite de Master, total_deuda (saldo Visa + Master),
#   ratio_pagado_vs_deuda_visa, flags de mora y flag_paga_solo_minimo (pagado ≤ 1,15 × pago mínimo, con saldo y
#   mínimo positivos). Acumula saldo, mpayroll y consumo Visa por mes para los percentiles.
            # --- Variables estaticas (no requieren historia) ---
            tiene_payroll = 1 if payroll > 0 else 0
            saldo_vacio = 1 if saldo < 1000 else 0
            activo_digital = 1 if (thb == 1 or mob > 0) else 0
            # FIX bug #3: antes devolvia 0.0 si no tenia limite (confundia "sin tarjeta" con "0% de uso").
            # Ahora, igual que las demas ratios nuevas, queda en blanco (NaN) si no aplica.
            ratio_limite = round(visa_saldo / visa_lim, 4) if visa_lim > 0 else ""
            flag_pmin = 1 if visa_pmin > 0 else 0

            # FIX bug #2: bins recalculados sobre el histograma real de cproductos (rango 3-17,
            # con ~92% de los clientes entre 6 y 10). Los bins originales (<=2,<=5,<=10,>10)
            # dejaban el 92% de los casos en un unico valor.
            if cprod <= 5:
                rango_prod_ord = 0
            elif cprod <= 7:
                rango_prod_ord = 1
            elif cprod <= 9:
                rango_prod_ord = 2
            else:
                rango_prod_ord = 3

            ratio_master = round(master_cons / master_lim, 4) if master_lim > 0 else ""
            total_deuda = round(visa_saldo + master_saldo, 2)
            ratio_pagado_visa = round(visa_pagado / visa_saldo, 4) if visa_saldo > 0 else ""

            # --- Familia mora / estres crediticio (nueva, familia 4 del SKILL.md) ---
            flag_mora_visa = 1 if visa_delinq == 1 else 0
            flag_mora_master = 1 if master_delinq == 1 else 0
            flag_mora = 1 if (flag_mora_visa or flag_mora_master) else 0

            # Indicador real de "paga solo el minimo" (distinto de flag_pago_minimo,
            # que solo indica que existe un minimo calculado, es decir que hay deuda).
            flag_paga_solo_minimo = 1 if (
                visa_saldo > 0 and visa_pmin > 0 and visa_pagado <= visa_pmin * 1.15
            ) else 0

            month_saldos[fm].append(saldo)
            month_payrolls[fm].append(mpayroll_val)
            month_visacons[fm].append(visa_cons)

# [Anotación · líneas 278–330] Variables contra el mes anterior del mismo cliente, sólo si es el mes
#   calendario consecutivo; si hay un salto, flag_gap_mes = 1 y quedan vacías o en 0. Calcula el lag de
#   ctrx_quarter, saldo, cpayroll_trx y consumo Visa; deltas de ctrx_quarter, saldo, mpayroll, cproductos y
#   débitos automáticos; ratio_saldo; flags de pérdida de sueldo, tarjeta sin consumo, seguro cancelado, plazo
#   fijo cerrado, abandono del canal digital y nueva mora; y rachas de meses seguidos con baja de ctrx_quarter y
#   de saldo.
            # --- Variables temporales: requieren mes anterior CONSECUTIVO ---
            gap_flag = 0
            valid_prev = False
            if prev is not None:
                gap = fm_num - prev["fm_num"]
                if gap == 1:
                    valid_prev = True
                else:
                    # FIX bug #4: antes se calculaba el lag/delta igual, aunque hubiera
                    # meses faltantes entre observaciones del mismo cliente.
                    gap_flag = 1

            if not valid_prev:
                ctrx_lag = ""
                saldo_lag = ""
                payroll_lag = ""
                visa_cons_lag = ""
                delta_ctrx = ""
                delta_saldo = ""
                ratio_saldo = ""
                flag_perdio_sueldo = 0
                flag_apago_tarjeta = 0
                delta_mpayroll = ""
                delta_cproductos = ""
                delta_ccuenta_deb = ""
                flag_cancelo_seguro = 0
                flag_cerro_plazo_fijo = 0
                flag_dejo_digital = 0
                flag_nueva_mora = 0
                racha_ctrx = 0
                racha_saldo = 0
            else:
                p = prev
                ctrx_lag = fmt_num(p["ctrx"])
                saldo_lag = f"{p['saldo']:.2f}"
                payroll_lag = fmt_num(p["payroll"])
                visa_cons_lag = f"{p['visa_cons']:.2f}"
                delta_ctrx = f"{ctrx - p['ctrx']:.2f}"
                delta_saldo = f"{saldo - p['saldo']:.2f}"
                # FIX bug #1: formula anterior (saldo+1000)/(prev_saldo+1000) daba ratios
                # negativos sin sentido en ~10% de las filas cuando el saldo cruza cero.
                ratio_saldo = f"{safe_ratio(saldo, p['saldo']):.4f}"
                flag_perdio_sueldo = 1 if (p["payroll"] > 0 and payroll == 0) else 0
                flag_apago_tarjeta = 1 if (p["visa_cons"] > 0 and visa_cons == 0) else 0
                delta_mpayroll = f"{mpayroll_val - p['mpayroll']:.2f}"
                delta_cproductos = f"{cprod - p['cprod']:.2f}"
                delta_ccuenta_deb = f"{ccuenta_deb_auto - p['ccuenta_deb_auto']:.2f}"
                flag_cancelo_seguro = 1 if cseguros_total < p["cseguros_total"] else 0
                flag_cerro_plazo_fijo = 1 if (p["cplazo_fijo"] > 0 and cplazo_fijo == 0) else 0
                flag_dejo_digital = 1 if (p["activo_digital"] == 1 and activo_digital == 0) else 0
                flag_nueva_mora = 1 if (p["flag_mora"] == 0 and flag_mora == 1) else 0
                racha_ctrx = racha_ctrx + 1 if (ctrx - p["ctrx"]) < 0 else 0
                racha_saldo = racha_saldo + 1 if (saldo - p["saldo"]) < 0 else 0

# [Anotación · líneas 332–388] Guarda los valores del mes como referencia para la fila siguiente y agrega a la
#   fila original las 39 columnas nuevas en el orden del encabezado; ahí calcula también ratio_uso_limite_master
#   y ratio_consumo_vs_limite_visa. Saldo, mpayroll y consumo Visa quedan como valores provisorios en las
#   posiciones de los ranks.
            prev = {
                "fm_num": fm_num,
                "ctrx": ctrx,
                "saldo": saldo,
                "payroll": payroll,
                "visa_cons": visa_cons,
                "mpayroll": mpayroll_val,
                "cprod": cprod,
                "ccuenta_deb_auto": ccuenta_deb_auto,
                "cseguros_total": cseguros_total,
                "cplazo_fijo": cplazo_fijo,
                "activo_digital": activo_digital,
                "flag_mora": flag_mora,
            }

            new_row = r + [
                tiene_payroll,
                saldo_vacio,
                activo_digital,
                ratio_limite,
                flag_pmin,
                rango_prod_ord,
                ctrx_lag,
                saldo_lag,
                payroll_lag,
                visa_cons_lag,
                delta_ctrx,
                delta_saldo,
                ratio_saldo,
                flag_perdio_sueldo,
                flag_apago_tarjeta,
                saldo,  # placeholder -> rank_saldo_mes (pase 2)
                ratio_master,
                delta_mpayroll,
                total_deuda,
                ratio_pagado_visa,
                flag_mora_visa,
                flag_mora_master,
                flag_mora,
                flag_nueva_mora,
                flag_paga_solo_minimo,
                racha_ctrx,
                racha_saldo,
                delta_cproductos,
                delta_ccuenta_deb,
                cseguros_total,
                flag_cancelo_seguro,
                flag_cerro_plazo_fijo,
                flag_dejo_digital,
                round(master_saldo / master_lim, 4) if master_lim > 0 else "",
                round(visa_cons / visa_lim, 4) if visa_lim > 0 else "",
                mpayroll_val,  # placeholder -> rank_mpayroll_mes (pase 2)
                visa_cons,  # placeholder -> rank_visa_consumo_mes (pase 2)
                "",  # placeholder -> delta_rank_saldo_mes (pase 3)
                gap_flag,
            ]
            processed_rows.append(new_row)

# [Anotación · líneas 390–413] Ordena los valores de cada mes y reemplaza los provisorios por el percentil
#   dentro del mes (bisect_right sobre la lista ordenada, dividido por la cantidad de filas del mes):
#   rank_saldo_mes, rank_mpayroll_mes y rank_visa_consumo_mes.
    # 4. Calcular percentiles mensuales (anti-inflacion: saldo, payroll y consumo Visa)
    print("Calculando percentiles mensuales (saldo, payroll, consumo Visa)...")
    saldo_sorted = {fm: sorted(v) for fm, v in month_saldos.items()}
    payroll_sorted = {fm: sorted(v) for fm, v in month_payrolls.items()}
    visacons_sorted = {fm: sorted(v) for fm, v in month_visacons.items()}

    rank_saldo_pos = new_idx["rank_saldo_mes"]
    rank_payroll_pos = new_idx["rank_mpayroll_mes"]
    rank_visacons_pos = new_idx["rank_visa_consumo_mes"]

    for row in processed_rows:
        fm = row[foto_mes_idx]

        s_list = saldo_sorted[fm]
        s = row[rank_saldo_pos]
        row[rank_saldo_pos] = f"{bisect.bisect_right(s_list, s) / len(s_list):.4f}"

        p_list = payroll_sorted[fm]
        p = row[rank_payroll_pos]
        row[rank_payroll_pos] = f"{bisect.bisect_right(p_list, p) / len(p_list):.4f}"

        v_list = visacons_sorted[fm]
        v = row[rank_visacons_pos]
        row[rank_visacons_pos] = f"{bisect.bisect_right(v_list, v) / len(v_list):.4f}"

# [Anotación · líneas 415–431] delta_rank_saldo_mes: recorre las filas en orden y resta al rank de saldo del
#   mes el del mes anterior del mismo cliente cuando es consecutivo; en otro caso queda vacío.
    # 5. delta_rank_saldo_mes: requiere rank_saldo_mes ya calculado para el mes anterior.
    # processed_rows mantiene los bloques por cliente contiguos y ordenados por foto_mes,
    # asi que basta un recorrido secuencial detectando cambio de cliente o salto de mes.
    print("Calculando delta_rank_saldo_mes...")
    delta_rank_pos = new_idx["delta_rank_saldo_mes"]
    prev_cli = None
    prev_fm_num = None
    prev_rank = None
    for row in processed_rows:
        cli = row[num_cli_idx]
        fm_num = fm_to_int(row[foto_mes_idx])
        rank_val = float(row[rank_saldo_pos])
        if prev_cli == cli and (fm_num - prev_fm_num) == 1:
            row[delta_rank_pos] = f"{rank_val - prev_rank:.4f}"
        else:
            row[delta_rank_pos] = ""
        prev_cli, prev_fm_num, prev_rank = cli, fm_num, rank_val

# [Anotación · líneas 433–470] ctrx_quarter_slope_3: con DuckDB calcula regr_slope(ctrx_quarter,
#   cliente_antiguedad) por cliente, ordenado por foto_mes, en una ventana de la fila actual y las 3 anteriores,
#   y agrega el valor a cada fila (vacío si no es un número).
    # 6. ctrx_quarter_slope_3: pendiente de regresion (tendencia) de ctrx_quarter en una ventana
    # movil de hasta 4 meses (actual + 3 anteriores). Usa DuckDB (regr_slope), igual que en
    # z402_Feature_Engineering_en_SQL.ipynb, en vez de re-implementar la formula de OLS a mano.
    # x = cliente_antiguedad (no foto_mes ni un contador de filas): al ser la antiguedad real del
    # cliente, un salto de mes faltante se refleja como un salto de 2 en vez de 1, y regr_slope
    # normaliza por la distancia real en x, por lo que el resultado sigue siendo "cambio por mes"
    # incluso para los pocos clientes con historia discontinua (ver flag_gap_mes).
    print("Calculando ctrx_quarter_slope_3 con DuckDB (regr_slope)...")
    con = duckdb.connect()
    slope_rows = con.execute(
        f"""
        select
            numero_de_cliente,
            foto_mes,
            regr_slope(ctrx_quarter, cliente_antiguedad) over (
                partition by numero_de_cliente
                order by foto_mes
                rows between 3 preceding and current row
            ) as ctrx_quarter_slope_3
        from read_csv_auto('{input_file_sql}')
        """
    ).fetchall()
    con.close()


    def is_valid_number(x):
        return x is not None and not (isinstance(x, float) and x != x)


    slope_map = {
        (str(cli), str(fm)): slope
        for cli, fm, slope in slope_rows
        if is_valid_number(slope)
    }

    for row in processed_rows:
        slope = slope_map.get((row[num_cli_idx], row[foto_mes_idx]))
        row.append(f"{slope:.4f}" if slope is not None else "")

# [Anotación · líneas 472–479] Escribe el CSV de salida con el encabezado completo y todas las filas
#   procesadas.
    # 7. Escribir archivo final
    print(f"Escribiendo {len(processed_rows)} filas en {output_file}...")
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(all_headers)
        writer.writerows(processed_rows)

    print(f"Dataset generado exitosamente en {output_file} en {time.time() - start_time:.2f} segundos!")


# [Anotación · líneas 482–498] generar_final ejecuta generar_final_csv hacia un archivo temporal (o hacia
#   competencia_01_final.csv con --guardar-final) y lo lee con pandas. variables_originales devuelve las
#   columnas del CSV de entrada salvo las claves y clase_ternaria.
def generar_final(entrada, guardar_en=None):
    """DataFrame con las 195 columnas de competencia_01_final, leido igual que competencia_01_final.csv."""
    entrada = Path(entrada).resolve()
    if not entrada.exists():
        raise SystemExit(f'No existe {entrada}')
    if guardar_en is not None:
        generar_final_csv(entrada, guardar_en)
        return pd.read_csv(guardar_en)
    with tempfile.TemporaryDirectory() as carpeta:
        archivo = Path(carpeta) / 'competencia_01_final.csv'
        generar_final_csv(entrada, archivo)
        return pd.read_csv(archivo)


def variables_originales(columnas, entrada=ENTRADA):
    originales = pd.read_csv(entrada, nrows=1).columns
    return [c for c in originales if c not in CLAVES + ['clase_ternaria'] and c in columnas]


# [Anotación · líneas 501–519] es_plata identifica las variables de montos por prefijo (m, Visa_m, Master_m).
#   rank_cero_fijo calcula el percentil dentro de cada mes por separado para los positivos (de 0 a 1) y los
#   negativos (de −1 a 0) y deja el cero en 0. iguales compara dos columnas con tolerancia 1e-6.
# ---------------------------------------------------------------------------------------------
# 2. Variables de historia e inflacion
# ---------------------------------------------------------------------------------------------
def es_plata(nombre):
    return nombre.startswith(('m', 'Visa_m', 'Master_m'))


def rank_cero_fijo(x, mes):
    """Rank percentil dentro de cada mes, separando positivos y negativos y dejando el 0 fijo."""
    rank_pos = x.where(x > 0).groupby(mes).rank(pct=True)
    rank_neg = -(-x).where(x < 0).groupby(mes).rank(pct=True)
    r = rank_pos.fillna(rank_neg)
    r[x == 0] = 0.0
    return r.astype('float32')


def iguales(a, b):
    a, b = np.asarray(a, dtype='float64'), np.asarray(b, dtype='float64')
    return np.allclose(a, b, equal_nan=True, rtol=1e-6, atol=1e-6)


# [Anotación · líneas 522–537] main: lee --entrada, --salida y --guardar-final, genera el DataFrame con las
#   columnas de competencia_01_final y arma la lista de variables originales y la de variables de montos.
def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--entrada', type=Path, default=ENTRADA, help='dataset crudo (competencia_01.csv)')
    parser.add_argument('--salida', type=Path, default=SALIDA, help='parquet a generar')
    parser.add_argument('--guardar-final', action='store_true',
                        help='ademas guardar competencia_01_final.csv al lado de la entrada')
    args = parser.parse_args()

    inicio = time.time()
    print(f'Generando las variables de competencia_01_final desde {args.entrada.name}...')
    guardar_en = Path(args.entrada).resolve().parent / 'competencia_01_final.csv' if args.guardar_final else None
    data = generar_final(args.entrada, guardar_en)
    print(f'  listo en {time.time() - inicio:.0f} s')
    variables = variables_originales(data.columns, args.entrada)
    plata = [v for v in variables if es_plata(v)]
    print(f'{data.shape[1]} columnas de entrada | {len(variables)} variables originales | {len(plata)} de plata')

# [Anotación · líneas 539–552] Agrega <var>_rank para cada variable de montos. Para k = 1 y 2 copia claves y
#   variables, corre foto_mes k meses hacia adelante y une por cliente y mes (left join); de ahí salen
#   <var>_lagk y <var>_deltak (valor actual menos lag), que quedan vacíos si el cliente no tiene ese mes.
    nuevas = {}

    print('Ranks dentro del mes (inflacion)...')
    for v in plata:
        nuevas[f'{v}_rank'] = rank_cero_fijo(data[v], data['foto_mes'])

    for k in (1, 2):
        print(f'Lag {k} y delta {k}...')
        previo = data[CLAVES + variables].copy()
        previo['foto_mes'] = previo['foto_mes'].map(lambda m: sumar_meses(m, k))  # el valor de M aparece en M + k
        lag = data[CLAVES].merge(previo, on=CLAVES, how='left')  # how='left' respeta el orden de data
        for v in variables:
            nuevas[f'{v}_lag{k}'] = lag[v].to_numpy(dtype='float32')
            nuevas[f'{v}_delta{k}'] = (data[v].to_numpy(dtype='float64') - lag[v].to_numpy(dtype='float64')).astype('float32')

# [Anotación · líneas 554–570] Quita columnas nuevas que repiten una existente: si <var>_delta1 coincide con
#   delta_<var>, o <var>_lag1 con la columna del mismo nombre de la tabla base, descarta la nueva; si el nombre
#   coincide y los valores no, conserva la de la tabla base. Imprime ambas listas.
    # Lags/deltas que ya existian en competencia_01_final con otro nombre (o el mismo): no duplicar.
    # Si ya existe una columna con el mismo nombre se conserva la de final (para que final quede
    # identico dentro de extendido). Ej.: Visa_mconsumototal_lag1 de final pone 0 donde el mes
    # anterior estaba vacio; la calculada aca lo deja vacio.
    ya_existentes = {f'{v}_delta1': f'delta_{v}' for v in variables}
    ya_existentes.update({f'{v}_lag1': f'{v}_lag1' for v in variables})
    descartadas, conservadas_de_final = [], []
    for nueva, existente in ya_existentes.items():
        if existente in data.columns and nueva in nuevas:
            if iguales(nuevas[nueva], data[existente]):
                del nuevas[nueva]
                descartadas.append(nueva)
            elif nueva == existente:
                del nuevas[nueva]
                conservadas_de_final.append(nueva)
    print(f'Descartadas por repetir una columna existente: {descartadas}')
    print(f'Mismo nombre que una de final con otros valores (se conserva la de final): {conservadas_de_final}')

# [Anotación · líneas 572–588] Concatena las columnas nuevas a la tabla base, escribe el parquet e imprime la
#   cantidad de columnas nuevas por grupo (rank, lag1, lag2, delta1, delta2) y el tiempo total.
    extendido = pd.concat([data, pd.DataFrame(nuevas, index=data.index)], axis=1)
    print(f'Escribiendo {extendido.shape[0]} filas x {extendido.shape[1]} columnas en {args.salida}...')
    extendido.to_parquet(args.salida, index=False)

    grupos = {
        'rank (inflacion)': sum(c.endswith('_rank') for c in nuevas),
        'lag1': sum(c.endswith('_lag1') for c in nuevas),
        'lag2': sum(c.endswith('_lag2') for c in nuevas),
        'delta1': sum(c.endswith('_delta1') for c in nuevas),
        'delta2': sum(c.endswith('_delta2') for c in nuevas),
    }
    print(f'Nuevas: {len(nuevas)} {grupos} | total columnas: {extendido.shape[1]}')
    print(f'Listo en {time.time() - inicio:.0f} s')


if __name__ == '__main__':
    main()
```

### competencia_uno/main.py

Script que corre el experimento completo desde la terminal con los valores de CONFIG (o de la línea de comandos): datos, Optuna, top 3 y prueba de semillas, modelo elegido, medición en el mes de test, ensayo, predicción de 202108 y archivo de salida.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–24] Docstring con los 6 pasos del experimento y ejemplos de uso por línea de comandos;
#   importa argparse, os, sys y Path.
"""Corre un experimento completo desde la terminal: lo mismo que hacen las notebooks primerComp_*,
sin graficos. Los parametros se configuran en CONFIG (abajo) o por linea de comandos.

Pasos (los mismos de la notebook):
  1. datos y train/test
  2. Optuna (solo corre los trials que faltan)
  3. mejor trial, top 3 y prueba de semillas
  4. modelo elegido (automatico o a mano) y sus metricas en el mes de test, con ensamble
  5. ensayo: reentrenar con otros meses y medir en otro mes (opcional)
  6. prediccion de agosto y archivo de submit (en la carpeta de main.py)

Todo lo ya calculado se carga del disco (db/, modelos/, resultados/), igual que en las notebooks.

Uso (desde la carpeta competencia_uno/):
    .venv/bin/python main.py                      # usa CONFIG tal cual
    .venv/bin/python main.py --corte umbral       # cambia un parametro
    .venv/bin/python main.py --sin-submit         # no guarda el archivo de submit
    .venv/bin/python main.py --comparar submits/<archivo>.csv   # compara el submit con otro archivo
    .venv/bin/python main.py --help
"""
import argparse
import os
import sys
from pathlib import Path

# [Anotación · líneas 26–61] CONFIG con los valores de la corrida: dataset 'extendido', espacio 'it01_bordes',
#   train 202103-202105, test 202106, numero_de_cliente como variable, undersampling 0.1, clase 'baja1y2',
#   métrica de Optuna 'umbral_ajustado', trials y trial elegido en None, criterio 'semillas', ensayo extra con
#   los mismos meses, train final 202103-202106, predicción 202108, corte 12058 y GUARDAR_SUBMIT True.
# ============================ CONFIGURACIÓN ============================
# Valores de la notebook 010: reproducen el submit
# it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optumbral_ajustado_trial49_top12058_20261007_182001.csv
CONFIG = {
    # Dataset: 'final' (195 columnas) o 'extendido' (+ inflación, lags y deltas). Ver FEATURES.md
    'DATASET': 'extendido',
    # Espacio de búsqueda de Optuna (comp/optimizacion_optuna.py, ESPACIOS): 'it00_z601' o 'it01_bordes'
    'ESPACIO_BUSQUEDA': 'it01_bordes',
    # Meses de train (Optuna elige los parámetros solo con estos) y mes de test (solo para medir)
    'MESES_TRAIN': [202103, 202104, 202105],
    'MES_TEST': 202106,
    # True: numero_de_cliente no se usa como variable
    'DROP_NUMERO_CLIENTE': False,
    # Fracción de la clase 0 que se queda en el train (None: todos)
    'UNDERSAMPLING': 0.1,
    # 'baja2' (modelo A) o 'baja1y2' (modelo B: BAJA+1 y BAJA+2 = 1)
    'CLASE_OBJETIVO': 'baja1y2',
    # Cómo puntúa Optuna: 'umbral' (p >= 0.025), 'umbral_ajustado' (p >= 0.025 / s) o 'franja' (top 5% a 9%)
    'METRICA_OPTUNA': 'umbral_ajustado',
    # Trials de Optuna (None: config.N_TRIALS)
    'N_TRIALS': None,
    # Modelo elegido: un número de trial a mano, o None para elegir según CRITERIO_ELEGIDO
    'TRIAL_ELEGIDO': None,
    # 'semillas' (caja más alta y concentrada, mayor Q1) u 'optuna' (mejor trial de Optuna)
    'CRITERIO_ELEGIDO': 'semillas',
    # Ensayo: reentrenar el modelo elegido con estos meses y medir en este mes (None: no se hace)
    'MESES_TRAIN_EXTRA': [202103, 202104, 202105],
    'MES_TEST_EXTRA': 202106,
    # Predicción final
    'MESES_TRAIN_FINAL': [202103, 202104, 202105, 202106],
    'MES_PREDICCION': 202108,
    # 'umbral' (p >= umbral de decisión) o una cantidad de clientes, ej. 12058
    'CORTE': 12058,
    'GUARDAR_SUBMIT': True,
}
# =======================================================================


# [Anotación · líneas 64–113] lista_de_meses y parsear_argumentos: define un argumento de línea de comandos
#   por cada clave de CONFIG, más --sin-ensayo, --sin-submit, --comparar y --salidas, y reemplaza en una copia
#   de CONFIG los valores que se pasaron.
def lista_de_meses(texto):
    return [int(m) for m in texto.replace(',', ' ').split()]


def parsear_argumentos(config):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--dataset')
    p.add_argument('--espacio', dest='ESPACIO_BUSQUEDA')
    p.add_argument('--meses-train', type=int, nargs='+')
    p.add_argument('--mes-test', type=int)
    p.add_argument('--sin-id', action='store_true', default=None, help='no usar numero_de_cliente como variable')
    p.add_argument('--undersampling', type=float, help='fracción de la clase 0 en el train; 0 = sin undersampling')
    p.add_argument('--clase-objetivo', choices=['baja2', 'baja1y2'])
    p.add_argument('--metrica-optuna', choices=['umbral', 'umbral_ajustado', 'franja'])
    p.add_argument('--trials', type=int, dest='N_TRIALS')
    p.add_argument('--trial-elegido', type=int)
    p.add_argument('--criterio-elegido', choices=['semillas', 'optuna'])
    p.add_argument('--meses-train-extra', type=int, nargs='+')
    p.add_argument('--mes-test-extra', type=int)
    p.add_argument('--sin-ensayo', action='store_true', help='no hacer el ensayo con otros meses')
    p.add_argument('--meses-train-final', type=int, nargs='+')
    p.add_argument('--mes-prediccion', type=int)
    p.add_argument('--corte', help="'umbral' o una cantidad de clientes")
    p.add_argument('--sin-submit', action='store_true', help='no guardar el archivo de submit')
    p.add_argument('--comparar', type=Path, help='submit (.csv) con el que comparar el resultado')
    p.add_argument('--salidas', type=Path,
                   help='carpeta para db/, modelos/, resultados/ y submits/ (por defecto clusters/)')
    a = p.parse_args()

    cfg = dict(config)
    for clave, valor in [
        ('DATASET', a.dataset), ('ESPACIO_BUSQUEDA', a.ESPACIO_BUSQUEDA), ('MESES_TRAIN', a.meses_train),
        ('MES_TEST', a.mes_test), ('CLASE_OBJETIVO', a.clase_objetivo), ('METRICA_OPTUNA', a.metrica_optuna),
        ('N_TRIALS', a.N_TRIALS), ('TRIAL_ELEGIDO', a.trial_elegido), ('CRITERIO_ELEGIDO', a.criterio_elegido),
        ('MESES_TRAIN_EXTRA', a.meses_train_extra), ('MES_TEST_EXTRA', a.mes_test_extra),
        ('MESES_TRAIN_FINAL', a.meses_train_final), ('MES_PREDICCION', a.mes_prediccion),
    ]:
        if valor is not None:
            cfg[clave] = valor
    if a.sin_id:
        cfg['DROP_NUMERO_CLIENTE'] = True
    if a.undersampling is not None:
        cfg['UNDERSAMPLING'] = a.undersampling or None
    if a.sin_ensayo:
        cfg['MESES_TRAIN_EXTRA'] = None
    if a.corte is not None:
        cfg['CORTE'] = a.corte if a.corte == 'umbral' else int(a.corte)
    if a.sin_submit:
        cfg['GUARDAR_SUBMIT'] = False
    return cfg, a.comparar, a.salidas


# [Anotación · líneas 116–134] titulo imprime un separador. main lee la configuración, fija la variable de
#   entorno COMP_SALIDAS_DIR si se pasó --salidas, agrega la carpeta del script al sys.path e importa numpy,
#   pandas y los módulos de comp.
def titulo(texto):
    print(f"\n{'=' * 10} {texto} {'=' * max(0, 70 - len(texto))}", flush=True)


def main():
    cfg, comparar, salidas = parsear_argumentos(CONFIG)
    if salidas is not None:
        os.environ['COMP_SALIDAS_DIR'] = str(salidas.resolve())  # antes de importar comp

    # los modulos se importan aca para que COMP_SALIDAS_DIR ya este definido
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import numpy as np
    import pandas as pd
    from comp import config, datos, ensamble, entrega, metricas, modelos, optimizacion_optuna
    from comp.experimento import Experimento
    from comp.particiones import armar_particion, armar_particiones, describir, sumar_meses

    pd.set_option('display.width', 200)
    pd.set_option('display.max_columns', 30)

# [Anotación · líneas 136–156] Crea el Experimento con los flags y lo describe, genera las semillas a partir
#   de exp.semilla y resuelve la cantidad de trials (config.N_TRIALS = 60 cuando es None). Carga el dataset,
#   agrega clase_binaria y arma la partición train / test.
    # ---------------------------------------------------------------- 1. experimento y datos
    titulo('Experimento')
    exp = Experimento(
        espacio=cfg['ESPACIO_BUSQUEDA'],
        meses_train=tuple(cfg['MESES_TRAIN']),
        mes_test=cfg['MES_TEST'],
        drop_numero_cliente=cfg['DROP_NUMERO_CLIENTE'],
        dataset=cfg['DATASET'],
        undersampling=cfg['UNDERSAMPLING'],
        clase_objetivo=cfg['CLASE_OBJETIVO'],
        metrica_optuna=cfg['METRICA_OPTUNA'],
    )
    exp.describir()
    semillas = config.generar_semillas(exp.semilla)
    n_trials = cfg['N_TRIALS'] if cfg['N_TRIALS'] is not None else config.N_TRIALS
    print(f'  trials de Optuna: {n_trials} | semillas: {config.N_SEMILLAS}')

    titulo('Datos')
    data = datos.agregar_clase_binaria(datos.cargar_datos(exp.dataset))
    particiones = armar_particiones(data, exp)
    describir(particiones)

# [Anotación · líneas 158–162] Abre o crea el estudio de Optuna del experimento, arma la función objetivo con
#   la primera semilla y corre sólo los trials que faltan para llegar al total.
    # ---------------------------------------------------------------- 2. Optuna
    titulo('Optuna')
    study = optimizacion_optuna.cargar_estudio(exp)
    objective = optimizacion_optuna.crear_objetivo(exp, particiones, semillas[0])
    study = optimizacion_optuna.optimizar_hasta(study, objective, n_trials_total=n_trials)

# [Anotación · líneas 164–182] Toma el trial de mayor valor del estudio, lo entrena o carga con la primera
#   semilla y los árboles de su best_iter, e imprime su ganancia en el mes de test. Evalúa en ese mes los 3
#   trials de mayor valor, reentrena cada uno con las 20 semillas e imprime media, desvío, mínimo, máximo,
#   mediana y cuartiles de la ganancia en millones.
    # ---------------------------------------------------------------- 3. mejor trial, top 3, semillas
    titulo('Mejor trial de Optuna')
    best = study.best_trial
    arboles_best = modelos.cantidad_arboles(exp, best.user_attrs['best_iter'])
    params_best = optimizacion_optuna.armar_params(best.params, semillas[0], exp.espacio)
    print(f"Mejor trial: {best.number} | best_iter en Optuna: {best.user_attrs['best_iter']} | árboles usados: {arboles_best}")
    for mes, p in particiones.items():
        modelo_best = modelos.entrenar_o_cargar(
            exp.modelos_dir / f'lgb_mejor_trial_{mes}.txt', params_best, modelos.datos_train(p, exp, semillas[0]), arboles_best)
        print(f"Ganancia LGBM en {mes}:", modelos.ganancia_experimento(modelos.predecir(modelo_best, p['X_test'], exp), p, exp))

    titulo('Top 3 trials, medidos en el mes de test')
    df_top3 = modelos.evaluar_top_trials(optimizacion_optuna.top_trials(study, 3), particiones, exp, semillas[0])
    print(df_top3.to_string(index=False))

    titulo(f'Prueba de semillas ({config.N_SEMILLAS})')
    df_semillas = modelos.evaluar_semillas(df_top3, particiones, exp, semillas[:config.N_SEMILLAS])
    estadisticas = modelos.estadisticas_semillas(df_semillas)
    print((estadisticas / 1e6).round(2).to_string())

# [Anotación · líneas 184–221] Define el modelo elegido. Si el experimento es la combinación del notebook de
#   clase usa parámetros fijos (num_leaves 16, learning_rate 0.019868, min_data_in_leaf 816, feature_fraction
#   0.277155, bagging_fraction 0.634130 y 250 árboles). Si no, toma el trial indicado a mano, el de mayor Q1
#   entre semillas ('semillas') o el primero según Optuna ('optuna'), y arma sus parámetros y su cantidad de
#   árboles.
    # ---------------------------------------------------------------- 4. modelo elegido
    titulo('Modelo elegido')
    if exp.es_original:
        params_elegido = {
            **config.PARAMS_FIJOS,
            'num_leaves': 16,
            'learning_rate': 0.019868,
            'min_data_in_leaf': 816,
            'feature_fraction': 0.277155,
            'bagging_fraction': 0.634130,
            'seed': semillas[0],
            'verbose': -1,
        }
        arboles_elegido = config.NUM_BOOST_ROUND
        id_elegido = ''  # nombres de archivo del notebook original
        trial_txt = 'fijo'
        print('Modelo elegido: parámetros fijos del notebook original')
    else:
        if cfg['TRIAL_ELEGIDO'] is not None:
            t = study.trials[cfg['TRIAL_ELEGIDO']]
            if t.state.name != 'COMPLETE':
                raise ValueError(f"El trial {cfg['TRIAL_ELEGIDO']} no terminó (estado {t.state.name})")
            fila = {**t.params, 'trial': t.number,
                    'best_iter': modelos.cantidad_arboles(exp, t.user_attrs.get('best_iter'))}
            como = 'a mano'
        elif cfg['CRITERIO_ELEGIDO'] == 'semillas':
            fila = modelos.elegir_por_semillas(df_top3, estadisticas)
            como = 'semillas'
        elif cfg['CRITERIO_ELEGIDO'] == 'optuna':
            fila = df_top3[df_top3['orden'] == 1].iloc[0]
            como = 'optuna'
        else:
            raise ValueError(f"CRITERIO_ELEGIDO tiene que ser 'semillas' u 'optuna', no {cfg['CRITERIO_ELEGIDO']!r}")
        params_elegido = optimizacion_optuna.armar_params(fila, semillas[0], exp.espacio)
        arboles_elegido = int(fila['best_iter'])
        id_elegido = f"_trial{int(fila['trial'])}"
        trial_txt = str(int(fila['trial']))
        print(f"Modelo elegido ({como}): trial {trial_txt} ({arboles_elegido} árboles)")

# [Anotación · líneas 223–242] Para el mes de test entrena o carga el modelo elegido con una semilla, obtiene
#   el promedio de 20 semillas (lo calcula o lo carga del .npy) e imprime para ambos KS, probabilidad media,
#   envíos y ganancia con p ≥ umbral, envíos y ganancia del corte de máxima ganancia, la diferencia entre ambas
#   y la ganancia de franja, en millones.
    comparacion = []
    for mes, p in particiones.items():
        modelo = modelos.entrenar_o_cargar(
            exp.modelos_dir / f'lgb_elegido{id_elegido}_{mes}.txt', params_elegido,
            modelos.datos_train(p, exp, semillas[0]), arboles_elegido)
        y_una = modelos.predecir(modelo, p['X_test'], exp)
        y_ens = ensamble.predecir_promedio_semillas(
            params_elegido, arboles_elegido, p['train_lgb'], p['X_test'], semillas[:config.N_SEMILLAS],
            archivo=exp.resultados_dir / f'pred_ensamble{id_elegido}_{mes}_{config.N_SEMILLAS}semillas.npy',
            y_train=p['y_train'], undersampling=exp.undersampling,
        )
        for nombre, y in [('una semilla', y_una), (f'ensamble {config.N_SEMILLAS} semillas', y_ens)]:
            comparacion.append({'mes': mes, 'modelo': nombre, 'ks': metricas.ks(y, p['y_test'])['ks'],
                                'prob_media': float(np.mean(y)),
                                **metricas.umbral_vs_mejor_corte(y, p['y_test'], umbral=p['umbral'], con_franja=True)})
    titulo(f"Mes de test: p >= umbral de decisión contra el mejor corte (ganancias en millones)")
    tabla = pd.DataFrame(comparacion)
    for c in ['ganancia_umbral', 'ganancia_mejor_corte', 'perdida', 'ganancia_franja']:
        tabla[c] = (tabla[c] / 1e6).round(1)
    print(tabla.round({'ks': 4, 'prob_media': 4, 'p_mejor_corte': 4, 'perdida_pct': 1}).to_string(index=False))

# [Anotación · líneas 244–281] Ensayo opcional: avisa si algún mes de MESES_TRAIN_EXTRA es posterior a
#   MES_TEST_EXTRA − 2; reutiliza la partición si los meses coinciden con los del experimento (si no, arma
#   otra), entrena o carga el modelo elegido con esos meses, calcula el ensamble de 20 semillas e imprime la
#   misma tabla de métricas. Después libera memoria.
    # ---------------------------------------------------------------- 5. ensayo con otros meses
    if cfg['MESES_TRAIN_EXTRA']:
        titulo(f"Ensayo: train {cfg['MESES_TRAIN_EXTRA']} -> test {cfg['MES_TEST_EXTRA']}")
        for m in cfg['MESES_TRAIN_EXTRA']:
            if m > sumar_meses(cfg['MES_TEST_EXTRA'], -2):
                print(f"AVISO: train {m} rompe la regla M - 2 (su BAJA+2 se conoce recién en {sumar_meses(m, 2)}, "
                      f"después de {cfg['MES_TEST_EXTRA']}): la ganancia puede ser optimista.")
        if cfg['MESES_TRAIN_EXTRA'] == cfg['MESES_TRAIN'] and cfg['MES_TEST_EXTRA'] == cfg['MES_TEST']:
            p_extra = particiones[cfg['MES_TEST']]
        else:
            del particiones
            datos.liberar_memoria()
            p_extra = armar_particion(data, cfg['MESES_TRAIN_EXTRA'], cfg['MES_TEST_EXTRA'], exp.columnas_excluidas,
                                      exp.clase_objetivo)
        print(f"Train ({p_extra['y_train'].sum()} positivos de {len(p_extra['y_train'])}) -> "
              f"test ({p_extra['y_test'].sum()} BAJA+2 de {len(p_extra['y_test'])})")
        sufijo = 'train' + '-'.join(map(str, cfg['MESES_TRAIN_EXTRA'])) + f"_test{cfg['MES_TEST_EXTRA']}"
        modelo_extra = modelos.entrenar_o_cargar(
            exp.modelos_dir / f'lgb_elegido{id_elegido}_{sufijo}.txt', params_elegido,
            modelos.datos_train(p_extra, exp, semillas[0]), arboles_elegido)
        y_una = modelos.predecir(modelo_extra, p_extra['X_test'], exp)
        y_ens_extra = ensamble.predecir_promedio_semillas(
            params_elegido, arboles_elegido, p_extra['train_lgb'], p_extra['X_test'], semillas[:config.N_SEMILLAS],
            archivo=exp.resultados_dir / f'pred_ensamble{id_elegido}_{sufijo}_{config.N_SEMILLAS}semillas.npy',
            y_train=p_extra['y_train'], undersampling=exp.undersampling,
        )
        filas = []
        for nombre, y in [('una semilla', y_una), (f'ensamble {config.N_SEMILLAS} semillas', y_ens_extra)]:
            filas.append({'modelo': nombre, 'ks': metricas.ks(y, p_extra['y_test'])['ks'],
                          **metricas.umbral_vs_mejor_corte(y, p_extra['y_test'], umbral=p_extra['umbral'], con_franja=True)})
        tabla_extra = pd.DataFrame(filas)
        for c in ['ganancia_umbral', 'ganancia_mejor_corte', 'perdida', 'ganancia_franja']:
            tabla_extra[c] = (tabla_extra[c] / 1e6).round(1)
        print(tabla_extra.round({'ks': 4, 'p_mejor_corte': 4, 'perdida_pct': 1}).to_string(index=False))
        del p_extra
    if 'particiones' in locals():
        del particiones
    datos.liberar_memoria()

# [Anotación · líneas 283–297] Arma el train final con MESES_TRAIN_FINAL y las filas de MES_PREDICCION,
#   obtiene el promedio de las 20 semillas (entrena, o carga el .npy si existe) e imprime la probabilidad media,
#   el umbral de decisión y una tabla con la cantidad de clientes y la probabilidad mínima para p ≥ umbral y
#   para 8000 a 15000 clientes.
    # ---------------------------------------------------------------- 6. predicción y submit
    titulo(f"Predicción de {cfg['MES_PREDICCION']}")
    pred = entrega.armar_prediccion(data, cfg['MESES_TRAIN_FINAL'], cfg['MES_PREDICCION'], exp.columnas_excluidas,
                                    exp.clase_objetivo)
    del data
    datos.liberar_memoria()
    print(f"Train {cfg['MESES_TRAIN_FINAL']} ({pred['y_train'].sum()} positivos de {len(pred['y_train'])}) -> "
          f"predicción {cfg['MES_PREDICCION']} ({len(pred['ids'])} clientes)")
    sufijo_final = 'train' + '-'.join(map(str, cfg['MESES_TRAIN_FINAL'])) + f"_pred{cfg['MES_PREDICCION']}"
    y_pred_final = entrega.predecir(
        params_elegido, arboles_elegido, pred, semillas[:config.N_SEMILLAS], undersampling=exp.undersampling,
        archivo=exp.resultados_dir / f'pred_ensamble{id_elegido}_{sufijo_final}_{config.N_SEMILLAS}semillas.npy',
    )
    print(f"Probabilidad media predicha: {y_pred_final.mean():.4f} | umbral de decisión: p >= {pred['umbral']:.4f}")
    print(entrega.resumen_cortes(y_pred_final, umbral=pred['umbral']).round(4).to_string(index=False))

# [Anotación · líneas 299–309] Selecciona los clientes según CORTE (los 12058 de mayor probabilidad), guarda
#   el CSV en la carpeta de main.py con el nombre <tag>_trial<N>_top12058_<fecha_hora>.csv y agrega una fila a
#   registro.md.
    corte = cfg['CORTE']
    ids_submit = entrega.clientes_a_contactar(pred['ids'], y_pred_final, corte, umbral=pred['umbral'])
    print(f'Corte {corte!r}: {len(ids_submit)} clientes a estimular')

    if cfg['GUARDAR_SUBMIT']:
        nombre_corte = 'umbral' if corte == 'umbral' else f'top{corte}'
        dir_main = Path(__file__).resolve().parent
        archivo_submit = entrega.guardar_submit(ids_submit, f'{exp.tag}{id_elegido}_{nombre_corte}', carpeta=dir_main)
        entrega.anotar_en_registro(archivo_submit, exp.tag, trial_txt, corte, ids_submit, y_pred_final,
                                   cfg['MESES_TRAIN_FINAL'], carpeta=dir_main)
        print('Submit guardado en', archivo_submit)

# [Anotación · líneas 311–322] Con --comparar lee otro CSV de ids e imprime la cantidad de clientes de cada
#   archivo, los que hay en común, los que están sólo en uno y si los conjuntos son idénticos. Al final, el
#   punto de entrada del script.
    if comparar is not None:
        titulo(f'Comparación con {comparar.name}')
        otros = np.loadtxt(comparar, dtype='int64', ndmin=1)
        iguales = len(otros) == len(ids_submit) and np.array_equal(np.sort(otros), ids_submit)
        print(f'clientes: {len(ids_submit)} (nuevo) | {len(otros)} ({comparar.name})')
        print(f'en común: {len(np.intersect1d(otros, ids_submit))} | '
              f'solo en el nuevo: {len(np.setdiff1d(ids_submit, otros))} | solo en el otro: {len(np.setdiff1d(otros, ids_submit))}')
        print('RESULTADO:', 'IDÉNTICO' if iguales else 'DISTINTO')


if __name__ == '__main__':
    main()
```

### competencia_uno/comp/datos.py

Carga del dataset (parquet directo, o CSV con copia en cache/), creación de clase_binaria y separación de X e y por meses.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] Define COLUMNAS_CLASE (clase_ternaria y clase_binaria) y liberar_memoria, que
#   libera el pool de pyarrow, ejecuta gc.collect() y llama a malloc_trim de libc.so.6, ignorando cualquier
#   excepción.
"""Carga del dataset y armado de X / y por meses."""
import numpy as np
import pandas as pd

from . import config

COLUMNAS_CLASE = ['clase_ternaria', 'clase_binaria']


def liberar_memoria():
    """Libera buffers de pyarrow y fuerza al sistema operativo a recuperar memoria."""
    try:
        import pyarrow as pa
        pa.default_memory_pool().release_unused()
    except Exception:
        pass
    import gc
    gc.collect()
    try:
        import ctypes
        ctypes.CDLL('libc.so.6').malloc_trim(0)
    except Exception:
        pass


# [Anotación · líneas 26–55] cargar_datos lee el dataset pedido de config.DATASETS: los .parquet directo; los
#   .csv, desde una copia parquet en cache/ si existe y no es anterior al CSV (si no, lee el CSV y guarda la
#   copia). Convierte las columnas float64 a float32 y libera memoria.
def cargar_datos(dataset='final', usar_cache=True):
    """Lee uno de los datasets de config.DATASETS.

    Los .parquet se leen directo. Para un .csv, la primera vez se guarda una copia en
    cache/<nombre>.parquet y las siguientes se lee esa copia (mismo contenido, mucho mas
    rapido); si el CSV es mas nuevo que la copia, se regenera.
    """
    if dataset not in config.DATASETS:
        raise ValueError(f"Dataset '{dataset}' no existe. Opciones: {list(config.DATASETS)}")
    archivo = config.DATASETS[dataset]
    if not archivo.exists():
        raise FileNotFoundError(f'No existe {archivo}. Para el dataset extendido: '
                                f'.venv/bin/python generate_features_extendido.py')
    if archivo.suffix == '.parquet':
        data = pd.read_parquet(archivo)
    else:
        csv = archivo
        parquet = config.CACHE_DIR / (csv.stem + '.parquet')
        if usar_cache and parquet.exists() and parquet.stat().st_mtime >= csv.stat().st_mtime:
            data = pd.read_parquet(parquet)
        else:
            data = pd.read_csv(csv)
            if usar_cache:
                data.to_parquet(parquet, index=False)

    # Reducir consumo de memoria: convertir float64 a float32 y liberar buffers
    for c in data.select_dtypes(include=['float64']).columns:
        data[c] = data[c].astype('float32')
    liberar_memoria()
    return data


# [Anotación · líneas 58–73] agregar_clase_binaria crea clase_binaria = 1 para BAJA+2 y 0 para el resto.
#   separar filtra los meses pedidos y devuelve X (todas las columnas menos las de clase y las excluidas), y
#   (clase_binaria) y la clase ternaria.
def agregar_clase_binaria(data):
    """BAJA+2 -> 1, BAJA+1 y CONTINUA -> 0 (modelo A)."""
    data['clase_binaria'] = np.where(data['clase_ternaria'] == 'BAJA+2', 1, 0)
    return data


def separar(data, meses, columnas_excluidas=()):
    """X, y (binaria) y clase ternaria de los meses indicados.

    columnas_excluidas: variables que no se usan como feature (ej. numero_de_cliente).
    """
    datos_meses = data[data['foto_mes'].isin(meses)]
    X = datos_meses.drop(COLUMNAS_CLASE + list(columnas_excluidas), axis=1)
    y = datos_meses['clase_binaria']
    clase = datos_meses['clase_ternaria']
    return X, y, clase
```

### competencia_uno/comp/undersampling.py

Submuestreo de los negativos del train por semilla y corrección de las probabilidades que produce un modelo entrenado con esa muestra.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–15] Docstring: se conservan todos los positivos y una fracción r al azar de los demás,
#   sólo en lo que se usa para entrenar; cada semilla saca su propia muestra; las probabilidades se corrigen con
#   p·r / (p·r + 1 − p); r = None significa sin submuestreo.
"""Undersampling del train: se quedan todos los BAJA+2 (clase 1) y una fraccion r, al azar,
de los demas (clase 0: CONTINUA y BAJA+1 juntos).

- Solo se reduce lo que el modelo usa para aprender. Lo que se usa para medir (el 30% de cada
  particion de Optuna y el mes de test) tiene siempre a todos los clientes.
- Cada semilla saca su propia muestra, asi el ensamble por semillas tambien promedia muestras.
- Como el modelo vio mas BAJA+2 que en la realidad, sus probabilidades salen infladas. Se
  corrigen con  p_real = p * r / (p * r + 1 - p)  antes de aplicar el corte de 0.025 y
  cualquier metrica.

r = None significa sin undersampling (todo queda igual que antes).
"""
import numpy as np

from . import config


# [Anotación · líneas 18–33] indices_muestra devuelve, ordenadas, las posiciones de todos los positivos y de
#   round(r × cantidad de negativos) negativos elegidos sin reposición con np.random.default_rng(seed).
#   corregir_probabilidad aplica p·r / (p·r + 1 − p), o devuelve p sin cambios si r es None.
def indices_muestra(y, r, seed):
    """Posiciones (0..n-1) de todos los positivos y de una fraccion r de los negativos."""
    y = np.asarray(y)
    positivos = np.flatnonzero(y == 1)
    negativos = np.flatnonzero(y == 0)
    rng = np.random.default_rng(seed)
    elegidos = rng.choice(negativos, size=int(round(len(negativos) * r)), replace=False)
    return np.sort(np.concatenate([positivos, elegidos]))


def corregir_probabilidad(p, r):
    """Deshace el efecto del undersampling sobre las probabilidades."""
    if r is None:
        return p
    p = np.asarray(p, dtype='float64')
    return p * r / (p * r + 1 - p)


# [Anotación · líneas 36–61] construir_si_hace_falta construye el lgb.Dataset completo con max_bin 31 y
#   feature_pre_filter False si todavía no está construido. dataset_muestra devuelve el Dataset completo (r
#   None) o un subset con los índices de la muestra de esa semilla.
def construir_si_hace_falta(train_lgb, seed):
    """Construye el Dataset completo con los mismos parametros de binning que usaria lgb.train.

    Un subconjunto (subset) necesita que el Dataset completo ya este construido; si no, LightGBM
    lo construye con sus valores por defecto y despues no deja cambiar max_bin. Si ya esta
    construido (por ejemplo por lgb.cv en Optuna) no se toca.
    """
    construido = getattr(train_lgb, '_handle', getattr(train_lgb, 'handle', None)) is not None
    if not construido:
        train_lgb.params = {
            **(train_lgb.params or {}),
            'max_bin': config.PARAMS_FIJOS['max_bin'],
            'feature_pre_filter': config.PARAMS_FIJOS['feature_pre_filter'],
            'seed': seed,
            'verbose': -1,
        }
        train_lgb.construct()
    return train_lgb


def dataset_muestra(train_lgb, y, r, seed):
    """El lgb.Dataset de train completo (r None) o un subconjunto con la muestra de esa semilla."""
    if r is None:
        return train_lgb
    construir_si_hace_falta(train_lgb, seed)
    return train_lgb.subset(indices_muestra(y, r, seed).tolist())
```

### competencia_uno/comp/particiones.py

Arma el train y el test de un experimento, la etiqueta de entrenamiento según la clase objetivo y el umbral de decisión.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Docstring (train = todos los meses de train juntos; test = el mes de test; regla M
#   − 2) e imports. sumar_meses suma n meses a un AAAAMM.
"""Arma el train y el test de un experimento.

- Train: los meses de experimento.meses_train (todas sus filas juntas).
- Test: experimento.mes_test, que solo se usa para medir la ganancia.

Regla M - 2 (recomendada, no obligatoria): la BAJA+2 de un mes se conoce recien dos meses
despues. Para que el test copie la situacion real de agosto, los meses de train deberian ser
como mucho mes_test - 2. Si no, el experimento muestra un AVISO (ver Experimento.avisos).
"""
import lightgbm as lgb

from . import config
from .datos import separar


def sumar_meses(mes, n):
    """sumar_meses(202105, -2) -> 202103. Funciona cruzando anios."""
    anio, m = divmod(mes, 100)
    total = anio * 12 + (m - 1) + n
    return (total // 12) * 100 + total % 12 + 1


# [Anotación · líneas 23–37] etiqueta_entrenamiento devuelve la etiqueta BAJA+2 (clase 'baja2') o 1 para las
#   clases de CLASES_OBJETIVO (BAJA+1 y BAJA+2 en 'baja1y2'). umbral_de_decision calcula 0.025 / s, con s =
#   BAJA+2 / positivos de entrenamiento.
def etiqueta_entrenamiento(y_baja2, clase, clase_objetivo='baja2'):
    """El 1 con el que se entrena: BAJA+2 (modelo A) o BAJA+1 + BAJA+2 (modelo B)."""
    if clase_objetivo == 'baja2':
        return y_baja2
    return clase.isin(config.CLASES_OBJETIVO[clase_objetivo]).astype('int64')


def umbral_de_decision(y_baja2, y_entrenamiento):
    """p >= UMBRAL / s, con s = BAJA+2 / positivos de entrenamiento.

    Si el modelo predice "BAJA+1 o BAJA+2", solo una parte s de esos positivos paga; contactar
    conviene cuando la chance de BAJA+2 (~ s * p) es >= 0.025. En el modelo A, s = 1: da 0.025.
    """
    s = y_baja2.sum() / y_entrenamiento.sum()
    return config.UMBRAL / s


# [Anotación · líneas 40–66] armar_particion verifica que los meses de train y el de test tengan
#   clase_ternaria completa (si no, ValueError), separa X e y de train y de test y devuelve un diccionario con
#   X_train, la etiqueta de entrenamiento, los BAJA+2 reales del train, el umbral, el lgb.Dataset de train,
#   X_test, y_test (BAJA+2 reales), la etiqueta objetivo del test y su clase ternaria.
def armar_particion(data, meses_de_train, mes_test, columnas_excluidas=(), clase_objetivo='baja2'):
    """Train con meses_de_train, test con mes_test. Devuelve un dict con todo lo necesario.

    y_train es la etiqueta con la que se entrena (segun clase_objetivo); y_train_baja2 e y_test
    son siempre los BAJA+2 reales, con los que se cuenta la ganancia.
    """
    # Un mes sin BAJA+2 conocida (ej. 202107, 202108) quedaria con todo 0 sin avisar
    for mes in list(meses_de_train) + [mes_test]:
        if data.loc[data['foto_mes'] == mes, 'clase_ternaria'].isna().any():
            raise ValueError(f'El mes {mes} no tiene la clase completa (BAJA+2 desconocida): no sirve para train ni test')
    X_train, y_baja2_train, clase_train = separar(data, meses_de_train, columnas_excluidas)
    y_train = etiqueta_entrenamiento(y_baja2_train, clase_train, clase_objetivo)
    X_test, y_test, clase_test = separar(data, [mes_test], columnas_excluidas)
    return {
        'meses_train': list(meses_de_train),
        'mes_test': mes_test,
        'clase_objetivo': clase_objetivo,
        'X_train': X_train,
        'y_train': y_train,
        'y_train_baja2': y_baja2_train,
        'umbral': umbral_de_decision(y_baja2_train, y_train),
        'train_lgb': lgb.Dataset(X_train, label=y_train),
        'X_test': X_test,
        'y_test': y_test,
        'y_test_objetivo': etiqueta_entrenamiento(y_test, clase_test, clase_objetivo),
        'clase_test': clase_test,
    }


# [Anotación · líneas 69–85] armar_particiones devuelve {mes_test: partición} para el experimento. describir
#   imprime la cantidad de BAJA+2 y de filas de train y de test y, si la clase objetivo no es 'baja2', los
#   positivos de entrenamiento y el umbral.
def armar_particiones(data, experimento):
    """{mes_test: particion}. Hay un solo mes de test; se devuelve como dict para que el resto
    del codigo (modelos, ensamble, graficos) lo recorra igual."""
    return {
        experimento.mes_test: armar_particion(
            data, experimento.meses_train, experimento.mes_test, experimento.columnas_excluidas,
            experimento.clase_objetivo)
    }


def describir(particiones):
    for mes, p in particiones.items():
        print(f"Test {mes} ({p['y_test'].sum()} BAJA+2 de {len(p['y_test'])}) <- "
              f"train {p['meses_train']} ({p['y_train_baja2'].sum()} BAJA+2 de {len(p['y_train'])})")
        if p.get('clase_objetivo', 'baja2') != 'baja2':
            print(f"  se entrena con {config.CLASES_OBJETIVO[p['clase_objetivo']]} = 1: {p['y_train'].sum()} positivos "
                  f"| umbral de decision p >= {p['umbral']:.4f}")
```

### competencia_uno/comp/__init__.py

Archivo de inicio del paquete comp: sólo contiene un docstring con la lista de módulos y qué hace cada uno.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Docstring del paquete: enumera config, experimento, datos, particiones, metricas,
#   optimizacion_optuna, modelos, ensamble, graficos y entrega con una línea sobre cada uno.
"""Modulos para el modelo de BAJA+2 (competencia 01).

- config:               rutas, matriz de ganancia, meses, semillas, parametros fijos
- experimento:          flags de un experimento y carpetas donde se guardan sus resultados
- datos:                carga del dataset (con cache parquet) y X / y por meses
- particiones:          train (meses_train) y test (mes_test) de un experimento
- metricas:             ganancia, KS, ganancia acumulada, lift, captura
- optimizacion_optuna:  espacios de busqueda y estudio de Optuna (reanudable)
- modelos:              entrenar/cargar modelos, top trials, estabilidad por semillas
- ensamble:             promedio de predicciones de varias semillas
- graficos:             figuras plotly de las metricas
- entrega:              prediccion de agosto y archivo de submit (submits/)
"""
```

### competencia_uno/comp/optimizacion_optuna.py

Espacios de búsqueda, funciones objetivo y manejo del estudio de Optuna. La función objetivo usada con clase 'baja1y2' y métrica 'umbral_ajustado' es crear_objetivo_cv_metrica.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–16] Docstring e imports: los trials quedan en la base SQLite del experimento y cada
#   trial se puntúa con la ganancia promedio en 5 particiones 70/30 de los meses de train.
"""Busqueda de hiperparametros de LightGBM con Optuna.

Los trials quedan guardados en la base SQLite del experimento, asi que volver a correr no
repite trials: solo se calculan los que faltan.

Cada trial se puntua como en el notebook de clase: ganancia promedio en 5 particiones 70/30
de los meses de train (todas sus filas juntas). El mes de test no se usa para elegir nada.
"""
import lightgbm as lgb
import numpy as np
import optuna
from sklearn.model_selection import StratifiedShuffleSplit

from . import config
from .metricas import feval_ganancia, ganancia_segun_metrica
from .undersampling import construir_si_hace_falta, corregir_probabilidad, indices_muestra

# [Anotación · líneas 18–54] ESPACIOS. 'it00_z601': num_leaves 8-100, learning_rate 0.005-0.3,
#   min_data_in_leaf 1-1000, feature_fraction y bagging_fraction 0.1-1.0; hasta 1000 rondas, paciencia 50 + 5/lr
#   y 250 árboles fijos. 'it01_bordes': num_leaves 4-64, learning_rate 0.003-0.1 y min_data_in_leaf 200-8000 en
#   escala logarítmica, feature_fraction 0.2-0.9, bagging_fraction 0.2-1.0, lambda_l1 0.01-10 y lambda_l2
#   0.01-100 en escala logarítmica, bagging_freq 1; hasta 3000 rondas, paciencia min(50 + 5/lr, 500) y árboles =
#   best_iter del trial.
# Espacios de busqueda, uno por iteracion. Nombre: it<NN>_<palabra que lo recuerde>.
# Para probar uno nuevo: copiar el ultimo, darle el numero siguiente y cambiar lo que haga falta.
# Cada parametro buscado: (nombre, tipo, minimo, maximo, escala_log). El orden importa
# (es el orden de los suggest de Optuna).
ESPACIOS = {
    # it00 "z601": el del notebook de clase z601, sin cambios (para reproducir sus resultados)
    'it00_z601': {
        'parametros': [
            ('num_leaves', 'int', 8, 100, False),
            ('learning_rate', 'float', 0.005, 0.3, False),
            ('min_data_in_leaf', 'int', 1, 1000, False),
            ('feature_fraction', 'float', 0.1, 1.0, False),
            ('bagging_fraction', 'float', 0.1, 1.0, False),  # sin bagging_freq no tiene efecto
        ],
        'fijos': {},
        'num_boost_round_max': 1000,
        'paciencia': lambda lr: int(50 + 5 / lr),
        'arboles_fijos': 250,  # los modelos finales usan 250 arboles, no best_iter
    },
    # it01 "bordes": rangos ampliados donde los 250 trials de it00 se apilaban contra el borde,
    # bagging activado y regularizacion L1/L2
    'it01_bordes': {
        'parametros': [
            ('num_leaves', 'int', 4, 64, True),          # los mejores estaban en 8-20, pegados al minimo
            ('learning_rate', 'float', 0.003, 0.1, True),  # los mejores < 0.06; > 0.1 siempre malo
            ('min_data_in_leaf', 'int', 200, 8000, True),  # los mejores en 800-1000, pegados al maximo
            ('feature_fraction', 'float', 0.2, 0.9, False),
            ('bagging_fraction', 'float', 0.2, 1.0, False),  # ahora activo (bagging_freq = 1)
            ('lambda_l1', 'float', 0.01, 10.0, True),      # regularizacion, nuevo
            ('lambda_l2', 'float', 0.01, 100.0, True),     # regularizacion, nuevo
        ],
        'fijos': {'bagging_freq': 1},
        'num_boost_round_max': 3000,
        'paciencia': lambda lr: min(int(50 + 5 / lr), 500),
        'arboles_fijos': None,  # los modelos finales usan best_iter del trial
    },
}


# [Anotación · líneas 57–77] armar_params une los parámetros fijos de config, los fijos del espacio y los
#   valores buscados, y agrega seed y verbose. sugerir pide a Optuna un valor por cada parámetro del espacio con
#   suggest_int o suggest_float.
def armar_params(hiperparametros, seed, espacio, verbose=-1):
    """Parametros fijos + los buscados (de un dict de Optuna o una fila de DataFrame)."""
    esp = ESPACIOS[espacio]
    params = {**config.PARAMS_FIJOS, **esp['fijos']}
    for nombre, tipo, *_ in esp['parametros']:
        valor = hiperparametros[nombre]
        params[nombre] = int(valor) if tipo == 'int' else valor
    params['seed'] = seed
    params['verbose'] = verbose
    return params


def sugerir(trial, espacio):
    """Pide a Optuna un valor para cada parametro del espacio."""
    valores = {}
    for nombre, tipo, minimo, maximo, log in ESPACIOS[espacio]['parametros']:
        if tipo == 'int':
            valores[nombre] = trial.suggest_int(nombre, minimo, maximo, log=log)
        else:
            valores[nombre] = trial.suggest_float(nombre, minimo, maximo, log=log)
    return valores


# [Anotación · líneas 80–114] crear_objetivo_cv (clase 'baja2' con métrica 'umbral'): arma 5 particiones
#   estratificadas 70/30 con StratifiedShuffleSplit, aplica el submuestreo sólo a la parte de entrenamiento de
#   cada una y corre lgb.cv con early stopping y la métrica de ganancia; devuelve el máximo de la ganancia media
#   y guarda su ronda en best_iter.
def crear_objetivo_cv(particion, espacio, semilla, test_size=0.3, r=None):
    """Ganancia maxima promedio en 5 particiones 70/30 del train (esquema original).

    r (undersampling): se reduce solo el 70% con el que aprende el modelo; el 30% con el que
    se mide queda completo y sus probabilidades se corrigen. Las muestras son las mismas para
    todos los trials, asi los trials se comparan entre si.
    """
    esp = ESPACIOS[espacio]
    X_train, y_train, train_lgb = particion['X_train'], particion['y_train'], particion['train_lgb']
    sss = StratifiedShuffleSplit(n_splits=5, test_size=test_size, random_state=semilla)
    feval = feval_ganancia(prop=test_size, r=r)
    if r is not None:
        y = np.asarray(y_train)
        folds_muestra = [
            (tr[indices_muestra(y[tr], r, semilla + k)], va)
            for k, (tr, va) in enumerate(sss.split(X_train, y_train))
        ]

    def objective(trial):
        params = {**armar_params(sugerir(trial, espacio), semilla, espacio), 'metric': 'custom'}
        cv_results = lgb.cv(
            params,
            train_lgb,
            num_boost_round=esp['num_boost_round_max'],
            callbacks=[lgb.early_stopping(stopping_rounds=esp['paciencia'](params['learning_rate']), verbose=False)],
            feval=feval,
            folds=sss.split(X_train, y_train) if r is None else folds_muestra,
            seed=semilla,
        )

        max_gan = max(cv_results['valid gan_prob-mean'])
        trial.set_user_attr('best_iter', cv_results['valid gan_prob-mean'].index(max_gan) + 1)
        return max_gan

    return objective


# [Anotación · líneas 117–145] crear_objetivo_cv_metrica (las demás combinaciones): fija el umbral (el de la
#   partición si la métrica es 'umbral_ajustado'; si no, 0.025), arma las mismas 5 particiones 70/30,
#   submuestrea la parte de entrenamiento con semilla + k, ordena los índices y guarda por partición los subsets
#   de train y de validación y los BAJA+2 reales de la validación.
def crear_objetivo_cv_metrica(particion, espacio, semilla, metrica, test_size=0.3, r=None):
    """Como crear_objetivo_cv, pero con cualquier METRICA_OPTUNA y cualquier clase objetivo.

    Las mismas 5 particiones 70/30 (y las mismas muestras si hay undersampling). Cada particion
    sabe cuales de sus clientes son BAJA+2 reales, asi la ganancia se cuenta bien aunque el
    modelo se entrene con BAJA+1 + BAJA+2 (modelo B).
    Diferencia con lgb.cv: cada particion corta por early stopping por su cuenta; la curva
    promedio se toma hasta la particion mas corta y best_iter es su maximo.
    """
    esp = ESPACIOS[espacio]
    X_train, y_train, train_lgb = particion['X_train'], particion['y_train'], particion['train_lgb']
    y_baja2 = np.asarray(particion['y_train_baja2'])
    umbral = particion['umbral'] if metrica == 'umbral_ajustado' else config.UMBRAL
    sss = StratifiedShuffleSplit(n_splits=5, test_size=test_size, random_state=semilla)
    y = np.asarray(y_train)

    construir_si_hace_falta(train_lgb, semilla)
    folds = []
    for k, (tr, va) in enumerate(sss.split(X_train, y_train)):
        if r is not None:
            tr = tr[indices_muestra(y[tr], r, semilla + k)]
        # LightGBM ordena las filas de un subset por posicion: se ordenan aca para que
        # los BAJA+2 reales queden alineados con las predicciones
        tr, va = np.sort(tr), np.sort(va)
        folds.append({
            'train': train_lgb.subset(tr.tolist()),
            'valid': train_lgb.subset(va.tolist()),
            'baja2': y_baja2[va],
        })

# [Anotación · líneas 147–172] Función objetivo: para cada partición entrena con lgb.train hasta el máximo de
#   rondas del espacio con early stopping, midiendo en cada ronda la ganancia sobre los BAJA+2 reales con las
#   probabilidades corregidas (dividida por 0,3). Promedia las 5 curvas hasta el largo de la más corta, guarda
#   como best_iter la ronda de mayor promedio y devuelve ese valor.
    def objective(trial):
        params = {**armar_params(sugerir(trial, espacio), semilla, espacio), 'metric': 'custom'}
        curvas = []
        for f in folds:
            def feval(y_pred, data, baja2=f['baja2']):
                y_pred = corregir_probabilidad(y_pred, r)
                return 'gan', ganancia_segun_metrica(y_pred, baja2, metrica, umbral, prop=test_size), True
            evals = {}
            lgb.train(
                params, f['train'],
                num_boost_round=esp['num_boost_round_max'],
                valid_sets=[f['valid']], valid_names=['valid'], feval=feval,
                callbacks=[
                    lgb.early_stopping(stopping_rounds=esp['paciencia'](params['learning_rate']), verbose=False),
                    lgb.record_evaluation(evals),
                ],
            )
            curvas.append(evals['valid']['gan'])

        n = min(len(c) for c in curvas)
        promedio = np.mean([c[:n] for c in curvas], axis=0)
        best_iter = int(np.argmax(promedio)) + 1
        trial.set_user_attr('best_iter', best_iter)
        return float(promedio[best_iter - 1])

    return objective


# [Anotación · líneas 175–185] crear_objetivo elige entre las dos funciones anteriores según la clase objetivo
#   y la métrica del experimento.
def crear_objetivo(experimento, particiones, semilla):
    """Optuna se puntua solo con los meses de train (el mes de test no se mira).

    Con los valores por defecto (modelo A, METRICA_OPTUNA = 'umbral') se usa exactamente el
    mismo codigo que en todos los experimentos ya corridos.
    """
    (particion,) = particiones.values()
    if experimento.clase_objetivo == 'baja2' and experimento.metrica_optuna == 'umbral':
        return crear_objetivo_cv(particion, experimento.espacio, semilla, r=experimento.undersampling)
    return crear_objetivo_cv_metrica(particion, experimento.espacio, semilla, experimento.metrica_optuna,
                                     r=experimento.undersampling)


# [Anotación · líneas 188–217] cargar_estudio abre o crea el estudio (direction 'maximize', storage SQLite del
#   experimento, load_if_exists). trials_completos filtra los terminados. optimizar_hasta corre sólo los trials
#   que faltan para llegar al total. top_trials devuelve los n de mayor valor.
def cargar_estudio(experimento):
    """Abre el estudio del experimento si existe, o lo crea vacio."""
    return optuna.create_study(
        direction='maximize',
        study_name=experimento.study_name,
        storage=experimento.storage,
        load_if_exists=True,
    )


def trials_completos(study):
    return [t for t in study.trials if t.state.name == 'COMPLETE']


def optimizar_hasta(study, objective, n_trials_total):
    """Corre solo los trials que faltan para llegar a n_trials_total."""
    faltan = n_trials_total - len(trials_completos(study))
    print(f"Trials completos: {len(trials_completos(study))} | faltan: {max(faltan, 0)}")
    if faltan > 0:
        study.optimize(objective, n_trials=faltan)
    return study


def top_trials(study, n=3):
    """Los n trials con mayor valor."""
    return sorted(
        [t for t in study.trials if t.value is not None],
        key=lambda t: t.value,
        reverse=True,
    )[:n]
```

### competencia_uno/comp/experimento.py

Dataclass Experimento: guarda los flags de una corrida, los valida y deriva de ellos el nombre (tag), la base de Optuna, las carpetas de modelos y resultados, la semilla y los avisos.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–19] Docstring e imports: un experimento entrena con meses_train y mide en mes_test;
#   cada combinación de flags tiene su tag y sus carpetas db/<tag>.db, modelos/<tag>/ y resultados/<tag>/.
"""Configuracion de un experimento (los flags del notebook) y donde se guardan sus resultados.

Un experimento entrena con `meses_train` y mide la ganancia en `mes_test`:
- Optuna elige los parametros solo con los meses de train (5 particiones 70/30, como el
  notebook de clase z601). El mes de test no se usa para elegir nada: solo para informar.

Cada combinacion de flags tiene su propio nombre (tag) y sus propias carpetas, para que
nunca se mezclen resultados de experimentos distintos:
    db/<tag>.db, modelos/<tag>/, resultados/<tag>/
La combinacion que reproduce el notebook de clase (espacio 'it00_z601', train 202103,
test 202105, con numero_de_cliente, dataset final) usa el estudio de Optuna de
z601_clases_final_csv.ipynb.
"""
from dataclasses import dataclass

from . import config
from .particiones import sumar_meses
from .optimizacion_optuna import ESPACIOS


# [Anotación · líneas 21–45] Dataclass inmutable con 8 campos (espacio, meses_train, mes_test,
#   drop_numero_cliente, dataset, undersampling, clase_objetivo, metrica_optuna). __post_init__ valida que
#   espacio, dataset, clase y métrica existan, que undersampling esté entre 0 y 1 y que los meses de train sean
#   anteriores al de test.
@dataclass(frozen=True)
class Experimento:
    espacio: str = 'it01_bordes'               # nombre de un espacio de optimizacion_optuna.ESPACIOS
    meses_train: tuple = (config.MES_TRAIN,)   # meses con los que se entrena (y Optuna elige parametros)
    mes_test: int = config.MES_TEST            # mes donde se mide la ganancia
    drop_numero_cliente: bool = False          # True: numero_de_cliente no se usa como feature
    dataset: str = 'final'                     # nombre de un dataset de config.DATASETS
    undersampling: float = None                # fraccion de la clase 0 que se queda en el train (None: todos)
    clase_objetivo: str = 'baja2'              # 'baja2' (modelo A) o 'baja1y2' (modelo B), ver config.CLASES_OBJETIVO
    metrica_optuna: str = 'umbral'             # como puntua Optuna, ver config.METRICAS_OPTUNA

    def __post_init__(self):
        if self.espacio not in ESPACIOS:
            raise ValueError(f"Espacio '{self.espacio}' no existe. Opciones: {list(ESPACIOS)}")
        if self.dataset not in config.DATASETS:
            raise ValueError(f"Dataset '{self.dataset}' no existe. Opciones: {list(config.DATASETS)}")
        if self.clase_objetivo not in config.CLASES_OBJETIVO:
            raise ValueError(f"Clase objetivo '{self.clase_objetivo}' no existe. Opciones: {list(config.CLASES_OBJETIVO)}")
        if self.metrica_optuna not in config.METRICAS_OPTUNA:
            raise ValueError(f"Metrica '{self.metrica_optuna}' no existe. Opciones: {config.METRICAS_OPTUNA}")
        if self.undersampling is not None and not 0 < self.undersampling < 1:
            raise ValueError(f'undersampling tiene que estar entre 0 y 1 (o None), no {self.undersampling}')
        tardios = [m for m in self.meses_train if m >= self.mes_test]
        if tardios:
            raise ValueError(f'Meses de train {tardios} no son anteriores al mes de test {self.mes_test}')

# [Anotación · líneas 47–75] avisos lista los meses de train posteriores a mes_test − 2. columnas_excluidas
#   devuelve numero_de_cliente si drop_numero_cliente es True. es_esquema_clase y es_original identifican la
#   combinación del notebook de clase (it00_z601, train 202103, test 202105, dataset final, sin undersampling,
#   baja2, umbral). semilla devuelve 17 para esa combinación y 6389 para las demás.
    def avisos(self):
        """Meses de train que rompen la regla M - 2 (su BAJA+2 usa datos posteriores al mes de test)."""
        limite = sumar_meses(self.mes_test, -2)
        return [
            f'train {m} rompe la regla M - 2: su BAJA+2 se conoce recien en '
            f'{sumar_meses(m, 2)}, despues de {self.mes_test}. '
            f'La ganancia en {self.mes_test} puede ser optimista.'
            for m in self.meses_train if m > limite
        ]

    @property
    def columnas_excluidas(self):
        return ['numero_de_cliente'] if self.drop_numero_cliente else []

    @property
    def es_esquema_clase(self):
        """Train marzo, test mayo: el esquema del notebook de clase."""
        return tuple(self.meses_train) == (config.MES_TRAIN,) and self.mes_test == config.MES_TEST

    @property
    def es_original(self):
        return (self.espacio == 'it00_z601' and self.es_esquema_clase and not self.drop_numero_cliente
                and self.dataset == 'final' and self.undersampling is None
                and self.clase_objetivo == 'baja2' and self.metrica_optuna == 'umbral')

    @property
    def semilla(self):
        """config.SEMILLA, salvo al reproducir el notebook de clase (usa la suya)."""
        return config.SEMILLA_CLASE if self.es_original else config.SEMILLA

# [Anotación · líneas 77–94] tag arma el nombre del experimento: el espacio, 'cv' o 'train<meses>_test<mes>',
#   y los sufijos 'sinid', 'ds<dataset>', 'us<porcentaje>', 'clase<objetivo>' y 'opt<métrica>' cuando el flag
#   difiere del valor por defecto.
    @property
    def tag(self):
        partes = [self.espacio]
        if self.es_esquema_clase:
            partes.append('cv')  # nombre que ya usaban 001, 002 y 004
        else:
            partes.append('train' + '-'.join(str(m) for m in self.meses_train) + f'_test{self.mes_test}')
        if self.drop_numero_cliente:
            partes.append('sinid')
        if self.dataset != 'final':
            partes.append(f'ds{self.dataset}')
        if self.undersampling is not None:
            partes.append(f'us{round(self.undersampling * 100):g}')
        if self.clase_objetivo != 'baja2':
            partes.append(f'clase{self.clase_objetivo}')
        if self.metrica_optuna != 'umbral':
            partes.append(f'opt{self.metrica_optuna}')
        return '_'.join(partes)

# [Anotación · líneas 96–116] storage y study_name devuelven la base SQLite y el nombre del estudio de Optuna;
#   resultados_dir y modelos_dir devuelven las carpetas del experimento y las crean si no existen.
    @property
    def storage(self):
        if self.es_original:
            return config.STORAGE_OPTUNA_ORIGINAL
        return f"sqlite:///{config.DB_DIR / (self.tag + '.db')}"

    @property
    def study_name(self):
        return config.STUDY_NAME_ORIGINAL if self.es_original else self.tag

    @property
    def resultados_dir(self):
        d = config.RESULTADOS_DIR / self.tag
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def modelos_dir(self):
        d = config.MODELOS_DIR / self.tag
        d.mkdir(parents=True, exist_ok=True)
        return d

# [Anotación · líneas 118–134] describir imprime el tag, el dataset, el espacio, los meses, las columnas
#   excluidas, la clase objetivo, la métrica, el undersampling, la ubicación del estudio, la semilla y los
#   avisos.
    def describir(self):
        print(f"Experimento: {self.tag}")
        print(f"  dataset: {self.dataset} ({config.DATASETS[self.dataset].name})")
        print(f"  espacio de busqueda: {self.espacio}")
        print(f"  train: {list(self.meses_train)} -> test: {self.mes_test}")
        print(f"  columnas excluidas: {self.columnas_excluidas or 'ninguna'}")
        print(f"  clase objetivo: {self.clase_objetivo} ({' + '.join(config.CLASES_OBJETIVO[self.clase_objetivo])} = 1)")
        print(f"  metrica de Optuna: {self.metrica_optuna}")
        if self.undersampling is None:
            print('  undersampling: no')
        else:
            print(f'  undersampling: se queda el {self.undersampling:.0%} de los no-BAJA+2 en el train '
                  '(cada semilla su muestra; el mes de test se mide con todos)')
        print(f"  Optuna: {self.study_name} en {self.storage}")
        print(f"  semilla: {self.semilla}")
        for aviso in self.avisos():
            print('  AVISO:', aviso)
```

### competencia_uno/comp/modelos.py

Entrenamiento o carga de modelos LightGBM, evaluación de los trials de mayor valor en el mes de test, prueba con varias semillas y elección por primer cuartil.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–16] Docstring e imports: todo se evalúa en el mes de test y lo que tarda se guarda en
#   modelos/<tag>/ y resultados/<tag>/ para reutilizarlo.
"""Entrenamiento de LightGBM, evaluacion de los mejores trials y estabilidad por semillas.

Todo se evalua en el mes de test del experimento. Las columnas de ganancia se llaman
ganancia_<mes>; ganancia_promedio es el mismo valor (queda por compatibilidad con los
resultados ya guardados).

Todo lo que tarda se guarda en disco (modelos/<tag>/ y resultados/<tag>/) y se reutiliza si
ya existe. Para forzar el recalculo, borrar el archivo o pasar recalcular=True.
"""
import lightgbm as lgb
import pandas as pd

from . import config
from .metricas import ganancia_segun_metrica, ganancia_umbral
from .optimizacion_optuna import ESPACIOS, armar_params
from .undersampling import corregir_probabilidad, dataset_muestra


# [Anotación · líneas 19–39] entrenar_o_cargar carga el modelo del archivo si existe; si no, lo entrena con
#   lgb.train y lo guarda. csv_cacheado hace lo mismo con una tabla: la lee si existe o la calcula y la guarda.
def entrenar_o_cargar(archivo, params, train_lgb, num_boost_round, recalcular=False):
    """Carga el modelo de `archivo` si existe; si no, entrena y lo guarda."""
    if archivo.exists() and not recalcular:
        print('Modelo cargado desde', archivo)
        return lgb.Booster(model_file=str(archivo))

    model = lgb.train(params, train_lgb, num_boost_round=num_boost_round)
    model.save_model(str(archivo))
    print('Modelo entrenado y guardado en', archivo)
    return model


def csv_cacheado(archivo, calcular, recalcular=False):
    """Lee `archivo` si existe; si no, ejecuta calcular() y guarda el resultado."""
    if archivo.exists() and not recalcular:
        print('Cargado desde', archivo)
        return pd.read_csv(archivo)

    df = calcular()
    df.to_csv(archivo, index=False)
    return df


# [Anotación · líneas 42–66] cantidad_arboles (los fijos del espacio, o best_iter), datos_train (Dataset
#   completo o la muestra de la semilla), predecir (probabilidades corregidas por el submuestreo),
#   umbral_experimento (el ajustado sólo con métrica 'umbral_ajustado'; si no, 0.025) y ganancia_experimento
#   (ganancia en el mes de test con la métrica del experimento y los BAJA+2 reales).
def cantidad_arboles(experimento, best_iter):
    """Arboles fijos si el espacio los define (it00: 250); si no, best_iter del trial."""
    fijos = ESPACIOS[experimento.espacio]['arboles_fijos']
    return fijos if fijos is not None else int(best_iter)


def datos_train(particion, experimento, seed):
    """Dataset de train para una semilla: completo, o la muestra de esa semilla si hay undersampling."""
    return dataset_muestra(particion['train_lgb'], particion['y_train'], experimento.undersampling, seed)


def predecir(model, X, experimento):
    """Probabilidades del modelo, corregidas si se entreno con undersampling."""
    return corregir_probabilidad(model.predict(X), experimento.undersampling)


def umbral_experimento(particion, experimento):
    """Umbral de decision: 0.025 salvo con METRICA_OPTUNA = 'umbral_ajustado' (0.025 / s)."""
    return particion['umbral'] if experimento.metrica_optuna == 'umbral_ajustado' else config.UMBRAL


def ganancia_experimento(y_pred, particion, experimento):
    """Ganancia en el mes de test con la misma metrica con la que Optuna eligio (BAJA+2 reales)."""
    return ganancia_segun_metrica(y_pred, particion['y_test'], experimento.metrica_optuna,
                                  umbral_experimento(particion, experimento))


# [Anotación · líneas 69–83] ganancias_por_mes entrena con el train y mide la ganancia en el mes de test.
#   importancia devuelve las variables con cantidad de splits mayor a 0, ordenadas de mayor a menor.
def ganancias_por_mes(params, num_boost_round, particiones, experimento):
    """Entrena con el train y mide la ganancia en el mes de test."""
    ganancias = {}
    for mes, p in particiones.items():
        model = lgb.train(params, datos_train(p, experimento, params['seed']), num_boost_round=num_boost_round)
        ganancias[f'ganancia_{mes}'] = ganancia_experimento(predecir(model, p['X_test'], experimento), p, experimento)
    ganancias['ganancia_promedio'] = sum(ganancias.values()) / len(particiones)
    return ganancias


def importancia(model, feature_names):
    """Importancia (cantidad de splits) de las variables usadas por el modelo."""
    importance_df = pd.DataFrame({'feature': feature_names, 'importance': model.feature_importance()})
    importance_df = importance_df.sort_values('importance', ascending=False)
    return importance_df[importance_df['importance'] > 0]


# [Anotación · líneas 86–104] evaluar_top_trials entrena cada trial con todo el train y registra orden, número
#   de trial, valor de Optuna, árboles, ganancia en el mes de test e hiperparámetros; la tabla se guarda en
#   df_top<N>.csv.
def evaluar_top_trials(trials, particiones, experimento, seed, recalcular=False):
    """Entrena cada trial con todo su train y mide la ganancia en cada mes de test."""
    def calcular():
        resultados = []
        for i, trial in enumerate(trials, start=1):
            arboles = cantidad_arboles(experimento, trial.user_attrs.get('best_iter'))
            params = armar_params(trial.params, seed, experimento.espacio)
            resultados.append({
                'orden': i,
                'trial': trial.number,
                'valor_optuna': trial.value,
                'best_iter': arboles,
                **ganancias_por_mes(params, arboles, particiones, experimento),
                **trial.params,
            })
        return pd.DataFrame(resultados)

    archivo = experimento.resultados_dir / f'df_top{len(trials)}.csv'
    return csv_cacheado(archivo, calcular, recalcular)


# [Anotación · líneas 107–122] evaluar_semillas reentrena cada modelo de la tabla anterior con cada semilla y
#   registra la ganancia en el mes de test; la tabla se guarda en df_semillas_<N>semillas.csv.
def evaluar_semillas(df_top, particiones, experimento, semillas, recalcular=False):
    """Reentrena cada modelo de df_top con varias semillas y mide la ganancia en cada mes de test."""
    def calcular():
        rows = []
        for _, fila in df_top.iterrows():
            for seed in semillas:
                params = armar_params(fila, seed, experimento.espacio)
                rows.append({
                    'trial': fila['trial'],
                    'seed': seed,
                    **ganancias_por_mes(params, int(fila['best_iter']), particiones, experimento),
                })
        return pd.DataFrame(rows)

    archivo = experimento.resultados_dir / f'df_semillas_{len(semillas)}semillas.csv'
    return csv_cacheado(archivo, calcular, recalcular)


# [Anotación · líneas 125–140] estadisticas_semillas calcula por trial media, desvío, mínimo, máximo, mediana,
#   q1 y q3 de la ganancia, ordenado por q1 descendente. elegir_por_semillas devuelve la fila del trial con
#   mayor q1.
def estadisticas_semillas(df_semillas, columna='ganancia_promedio'):
    """Distribucion de la ganancia por modelo, ordenada por q1 (el borde de abajo de la caja)."""
    g = df_semillas.groupby('trial')[columna]
    return (
        g.agg(['mean', 'std', 'min', 'max', 'median'])
        .assign(q1=g.quantile(0.25), q3=g.quantile(0.75))
        .sort_values('q1', ascending=False)
    )


def elegir_por_semillas(df_top, estadisticas):
    """Fila de df_top del modelo con la caja mas alta y concentrada: el mayor q1 entre semillas.

    Una caja solo tiene el borde de abajo alto si es alta y no se estira hacia abajo.
    """
    return df_top[df_top['trial'] == estadisticas['q1'].idxmax()].iloc[0]
```

### competencia_uno/comp/entrega.py

Arma el train final y el mes a predecir, obtiene la predicción del ensamble, selecciona los clientes según el corte, escribe el CSV y lo anota en registro.md.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–22] Docstring con el formato del archivo (CSV sin encabezado, un numero_de_cliente
#   entero por línea, entre 8000 y 15000, nombre distinto en cada submit) e imports; MIN_REGISTROS = 8000 y
#   MAX_REGISTROS = 15000.
"""Prediccion de un mes sin respuestas (agosto) y archivo de submit.

Formato pedido por la plataforma:
- archivo .csv, con un nombre distinto en cada submit (nunca repetido);
- solo los numero_de_cliente a los que se envia estimulo, uno por linea, entre 8000 y 15000;
- sin encabezado;
- ids como enteros (nunca en notacion cientifica, ej. 48000000 y no 4.8e+07).

Los archivos quedan en submits/ y cada uno se anota en submits/registro.md.
"""
import datetime

import lightgbm as lgb
import numpy as np
import pandas as pd

from . import config
from .datos import separar
from .ensamble import predecir_promedio_semillas

MIN_REGISTROS = 8000
MAX_REGISTROS = 15000


# [Anotación · líneas 25–54] armar_prediccion verifica que los meses de train sean anteriores al de
#   predicción, que tengan clase completa y que haya filas del mes a predecir; arma X e y de train con la
#   etiqueta de la clase objetivo, calcula el umbral 0.025 / (BAJA+2 / positivos) y devuelve el lgb.Dataset de
#   train, X del mes a predecir y sus numero_de_cliente.
def armar_prediccion(data, meses_train, mes_prediccion, columnas_excluidas=(), clase_objetivo='baja2'):
    """Train con meses_train (con respuestas) y las filas de mes_prediccion (sin respuestas).

    clase_objetivo: 'baja2' (modelo A) o 'baja1y2' (modelo B). 'umbral' es el corte de decision
    (0.025 en el A; 0.025 / s en el B, con s = BAJA+2 / positivos del train).
    """
    if any(m >= mes_prediccion for m in meses_train):
        raise ValueError(f'Los meses de train {list(meses_train)} tienen que ser anteriores a {mes_prediccion}')
    for mes in meses_train:
        if data.loc[data['foto_mes'] == mes, 'clase_ternaria'].isna().any():
            raise ValueError(f'El mes {mes} no tiene la clase completa (BAJA+2 desconocida): no sirve para train')
    datos_mes = data[data['foto_mes'] == mes_prediccion]
    if datos_mes.empty:
        raise ValueError(f'No hay filas del mes {mes_prediccion}')
    X_train, y_baja2, clase_train = separar(data, meses_train, columnas_excluidas)
    if clase_objetivo == 'baja2':
        y_train = y_baja2
    else:
        y_train = clase_train.isin(config.CLASES_OBJETIVO[clase_objetivo]).astype('int64')
    X_pred, _, _ = separar(data, [mes_prediccion], columnas_excluidas)
    return {
        'meses_train': list(meses_train),
        'mes_prediccion': mes_prediccion,
        'X_train': X_train,
        'y_train': y_train,
        'umbral': config.UMBRAL / (y_baja2.sum() / y_train.sum()),
        'train_lgb': lgb.Dataset(X_train, label=y_train),
        'X_pred': X_pred,
        'ids': datos_mes['numero_de_cliente'].to_numpy(dtype='int64'),
    }


# [Anotación · líneas 57–62] predecir llama a predecir_promedio_semillas con el train final, el mes a
#   predecir, las semillas y la fracción de submuestreo.
def predecir(params, num_boost_round, prediccion, semillas, undersampling=None, archivo=None):
    """Ensamble de semillas entrenado con los meses de train; probabilidades del mes a predecir."""
    return predecir_promedio_semillas(
        params, num_boost_round, prediccion['train_lgb'], prediccion['X_pred'], semillas,
        archivo=archivo, y_train=prediccion['y_train'], undersampling=undersampling,
    )


# [Anotación · líneas 65–76] clientes_a_contactar devuelve los ids con p ≥ umbral (corte 'umbral') o los N de
#   mayor probabilidad (corte entero), ordenados de menor a mayor.
def clientes_a_contactar(ids, y_pred, corte='umbral', umbral=None):
    """ids a estimular. corte = 'umbral' (p >= umbral, por defecto config.UMBRAL) o un entero N
    (los N de mayor probabilidad)."""
    umbral = config.UMBRAL if umbral is None else umbral
    ids, y_pred = np.asarray(ids), np.asarray(y_pred)
    if corte == 'umbral':
        elegidos = ids[y_pred >= umbral]
    elif isinstance(corte, (int, np.integer)) and corte > 0:
        elegidos = ids[np.argsort(y_pred)[::-1][:corte]]
    else:
        raise ValueError(f"corte tiene que ser 'umbral' o una cantidad de clientes, no {corte!r}")
    return np.sort(elegidos.astype('int64'))


# [Anotación · líneas 79–105] guardar_submit valida que los ids sean enteros, sin repetidos y entre 8000 y
#   15000; escribe <nombre>_<AAAAMMDD_HHMMSS>.csv con un id por línea y relee el archivo para verificar que
#   todas las líneas sean dígitos.
def guardar_submit(ids, nombre, carpeta=None):
    """Valida el formato y guarda submits/<nombre>_<fecha-hora>.csv. Devuelve la ruta.

    Nunca pisa un archivo: la fecha y hora en el nombre lo hace unico.
    """
    carpeta = carpeta or config.SUBMITS_DIR
    carpeta.mkdir(parents=True, exist_ok=True)
    ids = np.asarray(ids)

    if not np.issubdtype(ids.dtype, np.integer):
        raise ValueError(f'Los ids tienen que ser enteros, no {ids.dtype}')
    if len(np.unique(ids)) != len(ids):
        raise ValueError('Hay numero_de_cliente repetidos')
    if not MIN_REGISTROS <= len(ids) <= MAX_REGISTROS:
        raise ValueError(f'El submit tiene {len(ids)} clientes; la plataforma pide entre '
                         f'{MIN_REGISTROS} y {MAX_REGISTROS}. Cambiar el corte.')

    sello = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    archivo = carpeta / f'{nombre}_{sello}.csv'
    if archivo.exists():
        raise FileExistsError(archivo)
    archivo.write_text(''.join(f'{int(i)}\n' for i in ids), encoding='utf-8')

    # control: se relee como texto y se verifica linea por linea
    lineas = archivo.read_text(encoding='utf-8').splitlines()
    assert len(lineas) == len(ids) and all(l.isdigit() for l in lineas), 'El archivo no quedo con ids enteros'
    return archivo


# [Anotación · líneas 108–129] anotar_en_registro crea registro.md si no existe y agrega una fila con archivo,
#   experimento, trial, meses de train, corte, cantidad de clientes y probabilidad mínima enviada.
#   resumen_cortes arma una tabla con la cantidad de clientes y la probabilidad mínima para p ≥ umbral y para
#   8000 a 15000 clientes.
def anotar_en_registro(archivo, experimento, trial, corte, ids, y_pred, meses_train, carpeta=None):
    """Agrega una fila a submits/registro.md para saber despues que se mando en cada archivo."""
    carpeta = carpeta or config.SUBMITS_DIR
    registro = carpeta / 'registro.md'
    if not registro.exists():
        registro.write_text(
            '# Submits generados\n\n'
            '| Archivo | Experimento | Trial | Train | Corte | Clientes | p minima enviada |\n'
            '|---|---|---|---|---|---|---|\n', encoding='utf-8')
    p_min = float(np.sort(np.asarray(y_pred))[::-1][len(ids) - 1])
    with registro.open('a', encoding='utf-8') as f:
        f.write(f"| `{archivo.name}` | {experimento} | {trial} | {', '.join(map(str, meses_train))} "
                f"| {corte} | {len(ids)} | {p_min:.4f} |\n")


def resumen_cortes(y_pred, cortes=(8000, 9000, 10000, 11000, 12000, 13000, 14000, 15000), umbral=None):
    """Cuantos clientes manda p >= umbral (por defecto 0.025) y que probabilidad minima tiene cada cantidad fija."""
    umbral = config.UMBRAL if umbral is None else umbral
    orden = np.sort(np.asarray(y_pred))[::-1]
    filas = [{'corte': f'p >= {umbral:.4g}', 'clientes': int((orden >= umbral).sum()), 'p_minima': umbral}]
    filas += [{'corte': f'top {n}', 'clientes': n, 'p_minima': float(orden[n - 1])} for n in cortes if n <= len(orden)]
    return pd.DataFrame(filas)
```

### competencia_uno/comp/ensamble.py

Promedio de las predicciones de un mismo modelo entrenado con varias semillas, con guardado en .npy.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–10] Docstring e imports: el mismo modelo se entrena con varias semillas y se promedian
#   las probabilidades, tanto para medir en el mes de test como para la predicción final.
"""Ensamble por semillas: entrena el mismo modelo con varias semillas y promedia las
probabilidades. Reduce la variacion que da una sola semilla "con suerte" (o sin ella).

Sirve tanto para evaluar (X_pred = mes de test) como para la prediccion final (X_pred = agosto).
"""
import lightgbm as lgb
import numpy as np

from .undersampling import corregir_probabilidad, dataset_muestra


# [Anotación · líneas 12–34] predecir_promedio_semillas: si el archivo .npy existe lo carga. Si no, para cada
#   semilla toma la muestra de submuestreo de esa semilla, entrena con lgb.train cambiando sólo 'seed', predice
#   y corrige las probabilidades; promedia todas las predicciones y guarda el resultado en el .npy.
def predecir_promedio_semillas(params, num_boost_round, train_lgb, X_pred, semillas, archivo=None, recalcular=False,
                               y_train=None, undersampling=None):
    """Promedio de las predicciones de un modelo entrenado con cada semilla.

    undersampling (con y_train): cada semilla entrena con su propia muestra y sus
    probabilidades se corrigen antes de promediar.

    archivo (.npy, opcional): si existe se carga; si no, se guarda ahi el resultado.
    """
    if archivo is not None and archivo.exists() and not recalcular:
        print('Predicciones cargadas desde', archivo)
        return np.load(archivo)

    predicciones = []
    for seed in semillas:
        datos = dataset_muestra(train_lgb, y_train, undersampling, seed)
        model = lgb.train({**params, 'seed': seed}, datos, num_boost_round=num_boost_round)
        predicciones.append(corregir_probabilidad(model.predict(X_pred), undersampling))
    y_pred = np.mean(predicciones, axis=0)

    if archivo is not None:
        np.save(archivo, y_pred)
    return y_pred
```

### competencia_uno/comp/metricas.py

Funciones de ganancia (por umbral, por franja, acumulada), métrica custom para LightGBM, KS, lift y captura.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–19] ganancia_por_cliente asigna +1.072.500 si es BAJA+2 y −27.500 si no.
#   ganancia_umbral suma esa ganancia sobre los clientes con p ≥ umbral y la divide por prop (la fracción de
#   datos evaluada).
"""Metricas de negocio y de discriminacion para el modelo binario (BAJA+2 vs resto)."""
import numpy as np
from scipy.stats import ks_2samp

from .config import COSTO_ESTIMULO, FRANJA, GANANCIA_ACIERTO, UMBRAL
from .undersampling import corregir_probabilidad


def ganancia_por_cliente(y_true):
    """+GANANCIA_ACIERTO si es BAJA+2, -COSTO_ESTIMULO si no."""
    return np.where(y_true == 1, GANANCIA_ACIERTO, 0) - np.where(y_true == 0, COSTO_ESTIMULO, 0)


def ganancia_umbral(y_pred, y_true, umbral=UMBRAL, prop=1):
    """Ganancia de estimular a todos los clientes con probabilidad >= umbral.

    prop escala la ganancia cuando se evalua sobre una fraccion de los datos (ej. 0.3 en CV).
    """
    return ganancia_por_cliente(y_true)[y_pred >= umbral].sum() / prop


# [Anotación · líneas 22–44] ganancia_franja ordena por probabilidad descendente y promedia la ganancia
#   acumulada al enviar el 5%, 6%, 7%, 8% y 9% de los clientes. ganancia_segun_metrica aplica una u otra según
#   la métrica ('umbral' y 'umbral_ajustado' usan el umbral recibido).
def ganancia_franja(y_pred, y_true, fracciones=FRANJA, prop=1):
    """Ganancia promedio enviando al top f de los clientes, para cada f de `fracciones`.

    No depende de la calibracion: solo del orden de los clientes.
    """
    y_true = np.asarray(y_true)
    ganancia_ordenada = ganancia_por_cliente(y_true)[np.argsort(y_pred)[::-1]]
    acumulada = np.cumsum(ganancia_ordenada)
    n = len(y_true)
    return np.mean([acumulada[max(int(round(f * n)), 1) - 1] for f in fracciones]) / prop


def ganancia_segun_metrica(y_pred, y_true, metrica='umbral', umbral=UMBRAL, prop=1):
    """La ganancia con la que se juzga un modelo, segun METRICA_OPTUNA.

    'umbral' y 'umbral_ajustado' cortan en p >= umbral (el umbral ajustado lo calcula quien llama);
    'franja' promedia el top 5% a 9%. y_true son los BAJA+2 reales.
    """
    if metrica in ('umbral', 'umbral_ajustado'):
        return ganancia_umbral(y_pred, y_true, umbral, prop)
    if metrica == 'franja':
        return ganancia_franja(y_pred, y_true, prop=prop)
    raise ValueError(f"Metrica '{metrica}' no existe. Opciones: umbral, umbral_ajustado, franja")


# [Anotación · líneas 47–56] feval_ganancia devuelve la métrica custom 'gan_prob' para LightGBM: corrige las
#   probabilidades por el submuestreo y calcula la ganancia con el umbral.
def feval_ganancia(prop=0.3, umbral=UMBRAL, r=None):
    """Metrica custom para lgb.cv / lgb.train ('gan_prob', mayor es mejor).

    r: fraccion de undersampling del train (None: sin undersampling). Si hay, las
    probabilidades se corrigen antes de aplicar el umbral.
    """
    def ganancia_prob_lgm(y_pred, data):
        y_pred = corregir_probabilidad(y_pred, r)
        return 'gan_prob', ganancia_umbral(y_pred, data.get_label(), umbral, prop), True
    return ganancia_prob_lgm


# [Anotación · líneas 59–89] ks calcula el estadístico de Kolmogorov-Smirnov entre las probabilidades de
#   positivos y negativos con ks_2samp y devuelve además las dos distribuciones acumuladas y el punto de máxima
#   distancia.
def ks(y_pred, y_true):
    """Estadistico KS entre las probabilidades de positivos y negativos.

    Devuelve un dict con el valor, el p-value y los datos para graficar las CDF.
    """
    y_true = np.asarray(y_true)
    pred_pos = y_pred[y_true == 1]
    pred_neg = y_pred[y_true == 0]

    ks_stat, ks_pvalue = ks_2samp(pred_pos, pred_neg)

    x_pos = np.sort(pred_pos)
    x_neg = np.sort(pred_neg)

    # punto donde se da la maxima distancia entre las dos CDF
    todos = np.sort(np.concatenate([x_pos, x_neg]))
    cdf_pos_interp = np.searchsorted(x_pos, todos, side='right') / len(x_pos)
    cdf_neg_interp = np.searchsorted(x_neg, todos, side='right') / len(x_neg)
    idx_max = np.argmax(np.abs(cdf_pos_interp - cdf_neg_interp))

    return {
        'ks': ks_stat,
        'p_value': ks_pvalue,
        'x_pos': x_pos,
        'cdf_pos': np.arange(1, len(x_pos) + 1) / len(x_pos),
        'x_neg': x_neg,
        'cdf_neg': np.arange(1, len(x_neg) + 1) / len(x_neg),
        'x_ks': todos[idx_max],
        'cdf_pos_ks': cdf_pos_interp[idx_max],
        'cdf_neg_ks': cdf_neg_interp[idx_max],
    }


# [Anotación · líneas 92–108] ganancia_acumulada ordena por probabilidad descendente, acumula la ganancia y
#   devuelve la curva, la cantidad de clientes donde es máxima, esa ganancia y la probabilidad en ese punto.
def ganancia_acumulada(y_pred, y_true):
    """Ordena por probabilidad descendente y acumula la ganancia.

    Devuelve un dict con la curva, el corte optimo (cantidad de clientes),
    la ganancia maxima y la probabilidad en ese corte.
    """
    orden = np.argsort(y_pred)[::-1]
    ganancia_ordenada = np.where(np.asarray(y_true) == 1, GANANCIA_ACIERTO, -COSTO_ESTIMULO)[orden]
    curva = np.cumsum(ganancia_ordenada)

    mejor_corte = np.argmax(curva) + 1
    return {
        'curva': curva,
        'mejor_corte': mejor_corte,
        'mejor_ganancia': curva[mejor_corte - 1],
        'p_corte': y_pred[orden][mejor_corte - 1],
    }


# [Anotación · líneas 111–129] umbral_vs_mejor_corte devuelve envíos y ganancia con p ≥ umbral; envíos,
#   ganancia y probabilidad del corte de máxima ganancia; la diferencia absoluta y porcentual entre ambas; y, si
#   se pide, la ganancia de franja.
def umbral_vs_mejor_corte(y_pred, y_true, umbral=UMBRAL, con_franja=False):
    """Compara la regla p >= umbral con el mejor corte posible (elegido mirando las respuestas).

    perdida = cuanto deja de ganar la regla del umbral frente al mejor corte de ese mes.
    con_franja: agrega la ganancia promedio enviando al top 5% a 9% (ver config.FRANJA).
    """
    res = ganancia_acumulada(y_pred, y_true)
    envios_umbral = int((np.asarray(y_pred) >= umbral).sum())
    gan_umbral = ganancia_umbral(y_pred, y_true, umbral)
    return {
        'envios_umbral': envios_umbral,
        'ganancia_umbral': gan_umbral,
        'envios_mejor_corte': int(res['mejor_corte']),
        'ganancia_mejor_corte': res['mejor_ganancia'],
        'p_mejor_corte': res['p_corte'],
        'perdida': res['mejor_ganancia'] - gan_umbral,
        'perdida_pct': (res['mejor_ganancia'] - gan_umbral) / res['mejor_ganancia'] * 100,
        **({'ganancia_franja': ganancia_franja(y_pred, y_true)} if con_franja else {}),
    }


# [Anotación · líneas 132–153] ganancia_en_cortes devuelve la ganancia acumulada en cantidades dadas; lift, la
#   tasa de BAJA+2 en los primeros N (de 1000 a 20000) sobre la tasa total; captura, la proporción acumulada de
#   BAJA+2 por percentil de clientes.
def ganancia_en_cortes(curva, cortes):
    """Ganancia acumulada en cada cantidad de clientes de `cortes`."""
    cortes = np.asarray(cortes)
    cortes = cortes[cortes <= len(curva)]
    return cortes, curva[cortes - 1]


def lift(y_pred, y_true, cortes=np.arange(1000, 20001, 1000)):
    """Tasa de BAJA+2 en el top-N dividida por la tasa en toda la poblacion."""
    y_true = np.asarray(y_true)
    y_true_ordenado = y_true[np.argsort(y_pred)[::-1]]
    tasa_base = y_true.mean()
    return cortes, np.array([y_true_ordenado[:corte].mean() / tasa_base for corte in cortes])


def captura(y_pred, y_true):
    """Proporcion acumulada de BAJA+2 capturados, por percentil de clientes contactados."""
    y_true_ordenado = np.asarray(y_true)[np.argsort(y_pred)[::-1]]
    curva = np.cumsum(y_true_ordenado) / y_true_ordenado.sum()
    n = len(y_true_ordenado)
    percentiles = np.arange(1, n + 1) / n * 100
    return percentiles, curva
```

### competencia_uno/notebooks/primerComp_010_it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optumbral_ajustado.ipynb

Notebook del experimento 010, con los mismos flags que CONFIG de main.py y el mismo flujo, más las figuras de Optuna y de las métricas. Guarda el CSV en submits/. El comentario de main.py indica que sus valores reproducen el submit ..._trial49_top12058_20261007_182001.csv.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] Encabezado del experimento 010 (creado desde primerComp_001.ipynb con
#   nuevo_experimento.py) y texto de la plantilla: qué definen los flags, las carpetas por experimento y el
#   esquema (Optuna con los meses de train en 5 particiones 70/30, entrenamiento con todos los meses de train y
#   ganancia medida en el mes de test).
#%% celda 1 [texto]
> **Experimento 010: `it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optumbral_ajustado`**, creado el 2026-10-07 desde `primerComp_001.ipynb` con `nuevo_experimento.py`. No cambiar los flags acá: para otra combinación, crear otro experimento.

#%% celda 2 [texto]
# primerComp_001 — Modelo A (BAJA+2 vs resto)

Modelo binario: `BAJA+2 -> 1`, `BAJA+1` y `CONTINUA -> 0`. Toda la lógica vive en `comp/`; acá solo se configura, se llama y se grafica.

**Esta es la plantilla.** Con los flags tal como están reproduce `z601_clases_final_csv.ipynb` (todo se carga del disco). Para un experimento nuevo no se edita esta: se crea una copia numerada con `.venv/bin/python nuevo_experimento.py --espacio ... [--meses-train ...] [--mes-test ...] [--sin-id] [--dataset ...]` (ver `EXPERIMENTOS.md`).

**Cómo funciona:** los flags de la celda de abajo definen el experimento. Cada combinación de flags es un *experimento* con su propio nombre y sus propias carpetas, así que nunca se pisan resultados:
- trials de Optuna: `db/<experimento>.db`
- modelos: `modelos/<experimento>/`
- tablas y predicciones: `resultados/<experimento>/`

Lo que ya está calculado se carga del disco y no se vuelve a correr. Para recalcular algo, borrar su archivo.

**Cómo entrena (igual que el notebook de clase, con los meses que elijas):**
1. Optuna elige los parámetros **solo con los meses de train** (5 particiones 70/30).
2. Con esos parámetros se entrena con todos los meses de train.
3. La ganancia se mide en el **mes de test**, que no se usa para elegir nada.

**Para reproducir `z601_clases_final_csv.ipynb`:** `DATASET = 'final'`, `ESPACIO_BUSQUEDA = 'it00_z601'`, `MESES_TRAIN = [202103]`, `MES_TEST = 202105`, `DROP_NUMERO_CLIENTE = False`.

# [Anotación · líneas 25–68] Flags: dataset 'extendido', espacio 'it01_bordes', train 202103-202105, test
#   202106, numero_de_cliente como variable, undersampling 0.1, clase 'baja1y2', métrica 'umbral_ajustado' y
#   N_TRIALS None.
#%% celda 3 [código]
# ============================ CONFIGURACIÓN ============================
# Dataset. Están definidos en comp/config.py (DATASETS), ver FEATURES.md:
#   'final'     -> competencia_01_final (195 columnas)
#   'extendido' -> final + ranks por inflación + lags y deltas de 1 y 2 meses
DATASET = 'extendido'

# Espacio de búsqueda de Optuna. Están definidos en comp/optimizacion_optuna.py (ESPACIOS):
#   'it00_z601'   -> el del notebook de clase z601 (para reproducirlo)
#   'it01_bordes' -> rangos ampliados donde z601 tocaba los bordes, bagging activo, regularización
ESPACIO_BUSQUEDA = 'it01_bordes'

# Meses con los que se entrena. Optuna elige los parámetros solo con estos meses.
MESES_TRAIN = [202103, 202104, 202105]

# Mes donde se mide la ganancia. No se usa para elegir nada.
# Recomendado: meses de train <= MES_TEST - 2 (si no, el notebook muestra un AVISO).
MES_TEST = 202106

# True: numero_de_cliente no se usa como variable
DROP_NUMERO_CLIENTE = False

# Undersampling: fracción de los no-BAJA+2 (CONTINUA + BAJA+1) que se queda en el TRAIN.
# None: todos. Ej. 0.1 = se queda el 10%. Todos los BAJA+2 se quedan siempre.
# Solo se reduce lo que el modelo usa para aprender: el 30% con el que Optuna mide y el mes de
# test tienen a todos los clientes. Las probabilidades se corrigen solas.
UNDERSAMPLING = 0.1

# Clase con la que se ENTRENA (la ganancia siempre se cuenta con los BAJA+2 reales):
#   'baja2'   -> modelo A: BAJA+2 = 1; BAJA+1 y CONTINUA = 0 (por defecto)
#   'baja1y2' -> modelo B: BAJA+1 y BAJA+2 = 1; CONTINUA = 0
CLASE_OBJETIVO = 'baja1y2'

# Cómo puntúa Optuna cada trial (y cómo se miden el top 3 y la prueba de semillas):
#   'umbral'          -> ganancia con p >= 0.025 (por defecto: así se corrió todo hasta ahora)
#   'umbral_ajustado' -> ganancia con p >= 0.025 / s (s = BAJA+2 / positivos del train; pensado para el modelo B)
#   'franja'          -> ganancia promedio enviando al top 5%, 6%, 7%, 8% y 9% de los clientes
METRICA_OPTUNA = 'umbral_ajustado'

# Trials de Optuna para este experimento (None: usa config.N_TRIALS)
N_TRIALS = None

# Semillas: en comp/config.py (N_SEMILLAS)
# =======================================================================

# [Anotación · líneas 70–111] Agrega la carpeta raíz al sys.path, importa lightgbm, las figuras de Optuna y
#   los módulos de comp; crea el Experimento, genera las semillas y resuelve la cantidad de trials. Carga el
#   dataset, agrega clase_binaria y arma la partición.
#%% celda 4 [código]
import sys
from pathlib import Path

# Permitir importar el paquete comp/ estando dentro de notebooks/
root_dir = Path.cwd().parent.resolve() if Path.cwd().name == 'notebooks' else Path.cwd().resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import lightgbm as lgb
from IPython.display import display
from optuna.visualization import plot_optimization_history, plot_param_importances, plot_slice, plot_contour

from comp import config, datos, ensamble, graficos, metricas, modelos, optimizacion_optuna
from comp.experimento import Experimento
from comp.particiones import armar_particiones, describir as describir_particiones

exp = Experimento(
    espacio=ESPACIO_BUSQUEDA,
    meses_train=tuple(MESES_TRAIN),
    mes_test=MES_TEST,
    drop_numero_cliente=DROP_NUMERO_CLIENTE,
    dataset=DATASET,
    undersampling=UNDERSAMPLING,
    clase_objetivo=CLASE_OBJETIVO,
    metrica_optuna=METRICA_OPTUNA,
)
exp.describir()

semillas = config.generar_semillas(exp.semilla)
n_trials = N_TRIALS if N_TRIALS is not None else config.N_TRIALS
print(f'  trials de Optuna: {n_trials}')

#%% celda 5 [texto]
## Datos: train y test

#%% celda 6 [código]
data = datos.cargar_datos(exp.dataset)
data = datos.agregar_clase_binaria(data)

particiones = armar_particiones(data, exp)  # dict {mes_test: datos}; hay un solo mes de test
describir_particiones(particiones)

# [Anotación · líneas 113–138] Abre el estudio de Optuna, corre los trials que faltan y muestra la historia de
#   la búsqueda, la importancia de los parámetros, los gráficos de slice y los de contorno.
#%% celda 7 [texto]
## Optimización de hiperparámetros (Optuna)

Cada trial se puntúa con 5 particiones 70/30 **dentro de los meses de train** (como el notebook de clase). El mes de test no se mira.

La ganancia de cada trial se mide según `METRICA_OPTUNA` (por defecto p ≥ 0.025), siempre contando los BAJA+2 reales. Con esa misma métrica se miden el top 3 y la prueba de semillas.

#%% celda 8 [código]
study = optimizacion_optuna.cargar_estudio(exp)
objective = optimizacion_optuna.crear_objetivo(exp, particiones, semillas[0])
study = optimizacion_optuna.optimizar_hasta(study, objective, n_trials_total=n_trials)

#%% celda 9 [código]
plot_optimization_history(study)

#%% celda 10 [código]
plot_param_importances(study)

#%% celda 11 [código]
plot_slice(study)

#%% celda 12 [código]
plot_contour(study)

#%% celda 13 [código]
plot_contour(study, params=['learning_rate', 'min_data_in_leaf'])

# [Anotación · líneas 140–158] Entrena o carga el trial de mayor valor con la primera semilla, imprime su
#   ganancia en el mes de test y muestra la importancia de variables de ese modelo.
#%% celda 14 [texto]
## Mejor trial: entrenado con todo su train, evaluado en el mes de test

#%% celda 15 [código]
best = study.best_trial
arboles_best = modelos.cantidad_arboles(exp, best.user_attrs['best_iter'])
params_best = optimizacion_optuna.armar_params(best.params, semillas[0], exp.espacio)
print(f"Mejor trial: {best.number} | best_iter en Optuna: {best.user_attrs['best_iter']} | árboles usados: {arboles_best}")

modelos_best = {}
for mes, p in particiones.items():
    modelos_best[mes] = modelos.entrenar_o_cargar(
        exp.modelos_dir / f'lgb_mejor_trial_{mes}.txt', params_best, modelos.datos_train(p, exp, semillas[0]), arboles_best)
    print(f"Ganancia LGBM en {mes}:", modelos.ganancia_experimento(modelos.predecir(modelos_best[mes], p['X_test'], exp), p, exp))

#%% celda 16 [código]
mes_ultimo = list(particiones)[-1]
print('Importancia de variables, modelo del mes', mes_ultimo)
modelos.importancia(modelos_best[mes_ultimo], particiones[mes_ultimo]['X_train'].columns.tolist())

# [Anotación · líneas 160–178] Evalúa los 3 trials de mayor valor en el mes de test, los reentrena con 20
#   semillas, calcula las estadísticas por trial y dibuja un boxplot de ganancia por trial.
#%% celda 17 [texto]
## Top 3 trials (según Optuna), medidos en el mes de test

#%% celda 18 [código]
df_top3 = modelos.evaluar_top_trials(optimizacion_optuna.top_trials(study, 3), particiones, exp, semillas[0])
df_top3

#%% celda 19 [texto]
## Estabilidad: cada uno de los 3 modelos con varias semillas

¿El mejor lo es por los parámetros o por suerte de la semilla?

#%% celda 20 [código]
df_semillas = modelos.evaluar_semillas(df_top3, particiones, exp, semillas[:config.N_SEMILLAS])
estadisticas = modelos.estadisticas_semillas(df_semillas)
estadisticas

#%% celda 21 [código]
graficos.box_semillas(df_semillas, estadisticas)

# [Anotación · líneas 180–240] Texto sobre cómo elegir el modelo y celda que lo define con TRIAL_ELEGIDO =
#   None y CRITERIO_ELEGIDO = 'semillas' (el de mayor Q1); entrena o carga ese modelo con una semilla y predice
#   el mes de test.
#%% celda 22 [texto]
## Modelo elegido y sus métricas

**Cómo elegir:**
1. Correr todo el notebook (lo ya calculado se carga del disco).
2. Mirar los boxplots de la prueba de semillas.
3. Si querés otro trial, poner su número en `TRIAL_ELEGIDO` en la celda de abajo y **correr desde esa celda hacia abajo**. Lo de arriba no hace falta volver a correrlo.

Con `TRIAL_ELEGIDO = None` se elige solo, según `CRITERIO_ELEGIDO`:
- `'semillas'`: de los 3 mejores, el de **caja más alta y concentrada** (mayor Q1, el borde de abajo de la caja). Se elige mirando el mes de test, pero solo entre 3; el ensayo en otro mes (más abajo) es el control limpio.
- `'optuna'`: el mejor trial de Optuna (elegido solo con los meses de train).

Reproduciendo el notebook de clase se usan sus parámetros fijos (`model_params`) y `TRIAL_ELEGIDO` no se usa.

#%% celda 23 [código]
# ---------- Elegir el modelo DESPUÉS de mirar los boxplots de arriba ----------
# None: automático según CRITERIO_ELEGIDO. Un número (ej. 30): ese trial de Optuna, elegido a mano.
TRIAL_ELEGIDO = None
# Automático: 'semillas' = la caja más alta y concentrada (mayor Q1) | 'optuna' = el mejor trial de Optuna
CRITERIO_ELEGIDO = 'semillas'
# -------------------------------------------------------------------------------

if exp.es_original:
    params_elegido = {
        **config.PARAMS_FIJOS,
        'num_leaves': 16,
        'learning_rate': 0.019868,
        'min_data_in_leaf': 816,
        'feature_fraction': 0.277155,
        'bagging_fraction': 0.634130,
        'seed': semillas[0],
        'verbose': -1,
    }
    arboles_elegido = config.NUM_BOOST_ROUND
    id_elegido = ''  # nombres de archivo del notebook original
    print('Modelo elegido: parámetros fijos del notebook original')
else:
    if TRIAL_ELEGIDO is not None:
        t = study.trials[TRIAL_ELEGIDO]
        if t.state.name != 'COMPLETE':
            raise ValueError(f'El trial {TRIAL_ELEGIDO} no terminó (estado {t.state.name})')
        fila = {**t.params, 'trial': t.number,
                'best_iter': modelos.cantidad_arboles(exp, t.user_attrs.get('best_iter'))}
        print(f'Trial elegido a mano: {TRIAL_ELEGIDO}')
    elif CRITERIO_ELEGIDO == 'semillas':
        fila = modelos.elegir_por_semillas(df_top3, estadisticas)  # mayor Q1 entre semillas
    elif CRITERIO_ELEGIDO == 'optuna':
        fila = df_top3[df_top3['orden'] == 1].iloc[0]  # el mejor de Optuna
    else:
        raise ValueError(f"CRITERIO_ELEGIDO tiene que ser 'semillas' u 'optuna', no {CRITERIO_ELEGIDO!r}")
    params_elegido = optimizacion_optuna.armar_params(fila, semillas[0], exp.espacio)
    arboles_elegido = int(fila['best_iter'])
    id_elegido = f"_trial{int(fila['trial'])}"  # el trial va en los nombres de archivo
    print(f"Modelo elegido ({'a mano' if TRIAL_ELEGIDO is not None else CRITERIO_ELEGIDO}): trial {int(fila['trial'])} ({arboles_elegido} árboles)")

predicciones = {}
resumenes = {}
for mes, p in particiones.items():
    modelo = modelos.entrenar_o_cargar(
        exp.modelos_dir / f'lgb_elegido{id_elegido}_{mes}.txt', params_elegido, modelos.datos_train(p, exp, semillas[0]), arboles_elegido)
    predicciones[mes] = modelos.predecir(modelo, p['X_test'], exp)

# [Anotación · líneas 242–255] Calcula las métricas y figuras del modelo de una semilla en el mes de test e
#   imprime KS, probabilidad media, tasa real de la clase objetivo y el corte de máxima ganancia.
#%% celda 24 [código]
for mes, p in particiones.items():
    resumen, figuras = graficos.todas_las_metricas(
        predicciones[mes], p['y_test'], p['clase_test'], umbral=p['umbral'],
        y_objetivo=p['y_test_objetivo'] if exp.clase_objetivo != 'baja2' else None)
    resumenes[mes] = resumen
    print(f"===== Test {mes} =====")
    print(f"KS = {resumen['ks']:.4f}")
    tasa = resumen.get('tasa_real_objetivo', resumen['tasa_real_baja2'])
    print(f"Probabilidad media predicha: {resumen['prob_media']:.4f} | tasa real de la clase objetivo: {tasa:.4f}")
    print(f"Máxima ganancia: {resumen['mejor_ganancia']:.2f} en el corte {resumen['mejor_corte']}, "
          f"con probabilidad de corte p = {resumen['p_corte']:.4f}")
    for figura in figuras.values():
        figura.show()

# [Anotación · líneas 257–279] Obtiene la predicción del ensamble de 20 semillas en el mes de test, calcula
#   sus métricas, muestra su curva de ganancia y arma una tabla que compara una semilla con el ensamble.
#%% celda 25 [texto]
## Ensamble: promedio de las predicciones del modelo elegido con varias semillas

Mismo modelo, entrenado `config.N_SEMILLAS` veces cambiando solo la semilla; se promedian las probabilidades.

#%% celda 26 [código]
comparacion = []
for mes, p in particiones.items():
    y_ens = ensamble.predecir_promedio_semillas(
        params_elegido, arboles_elegido, p['train_lgb'], p['X_test'], semillas[:config.N_SEMILLAS],
        archivo=exp.resultados_dir / f'pred_ensamble{id_elegido}_{mes}_{config.N_SEMILLAS}semillas.npy',
        y_train=p['y_train'], undersampling=exp.undersampling,
    )
    resumen_ens, figuras_ens = graficos.todas_las_metricas(
        y_ens, p['y_test'], p['clase_test'], umbral=p['umbral'],
        y_objetivo=p['y_test_objetivo'] if exp.clase_objetivo != 'baja2' else None)
    comparacion.append({'mes': mes, 'modelo': 'una semilla', **resumenes[mes]})
    comparacion.append({'mes': mes, 'modelo': f'ensamble {config.N_SEMILLAS} semillas', **resumen_ens})
    figuras_ens['ganancia'].update_layout(title=f'Ganancia acumulada - ensamble {config.N_SEMILLAS} semillas - {mes}')
    figuras_ens['ganancia'].show()

import pandas as pd
pd.DataFrame(comparacion)

# [Anotación · líneas 281–314] Compara p ≥ umbral con el corte de máxima ganancia para una semilla y para el
#   ensamble, con la curva de ganancia de cada uno, y muestra la tabla en millones.
#%% celda 27 [texto]
## Regla p ≥ 0.025 contra el mejor corte

Para el modelo elegido (una semilla) y el ensamble:
- **p ≥ umbral**: la regla que se puede aplicar en agosto (no necesita saber las respuestas). Es 0.025 en el modelo A; en el modelo B, 0.025 / s (ver `CLASE_OBJETIVO`).
- **ganancia_franja**: la ganancia promedio enviando al top 5% a 9% de los clientes.
- **mejor corte**: la cantidad de clientes que hubiera dado la máxima ganancia, elegida **mirando las respuestas reales** de este mes. No se puede aplicar en agosto; sirve como techo.
- **pérdida**: cuánto deja de ganar la regla p ≥ 0.025 frente a ese techo.

En los gráficos: rombo verde = p ≥ 0.025, punto rojo = mejor corte.

#%% celda 28 [código]
import pandas as pd

comparacion_umbral = []
for mes, p in particiones.items():
    y_ens = ensamble.predecir_promedio_semillas(
        params_elegido, arboles_elegido, p['train_lgb'], p['X_test'], semillas[:config.N_SEMILLAS],
        archivo=exp.resultados_dir / f'pred_ensamble{id_elegido}_{mes}_{config.N_SEMILLAS}semillas.npy',
        y_train=p['y_train'], undersampling=exp.undersampling,
    )
    for modelo, y in [('una semilla', predicciones[mes]), (f'ensamble {config.N_SEMILLAS} semillas', y_ens)]:
        r = metricas.umbral_vs_mejor_corte(y, p['y_test'], umbral=p['umbral'], con_franja=True)
        comparacion_umbral.append({'mes': mes, 'modelo': modelo, **r})
        graficos.curva_ganancia(
            metricas.ganancia_acumulada(y, p['y_test']),
            titulo=f"{modelo} - {mes}: p ≥ {p['umbral']:.4g} (verde) contra el mejor corte (rojo)",
            envios_umbral=r['envios_umbral'], umbral=round(p['umbral'], 4),
        ).show()

tabla_umbral = pd.DataFrame(comparacion_umbral)
for c in ['ganancia_umbral', 'ganancia_mejor_corte', 'perdida']:
    tabla_umbral[c] = (tabla_umbral[c] / 1e6).round(1)  # en millones
tabla_umbral.round({'p_mejor_corte': 4, 'perdida_pct': 1})

# [Anotación · líneas 316–365] Ensayo con MESES_TRAIN_EXTRA = 202103-202105 y MES_TEST_EXTRA = 202106: arma la
#   partición, entrena o carga el modelo elegido, calcula el ensamble y muestra la tabla de métricas y las
#   curvas.
#%% celda 29 [texto]
## Reentrenar con más meses y medir en otro mes (con ensamble)

Toma **el mismo modelo elegido** (los mismos parámetros y la misma cantidad de árboles, sin volver a correr Optuna), lo entrena con los meses de `MESES_TRAIN_EXTRA` y mide la ganancia en `MES_TEST_EXTRA`, con el ensamble de semillas.

Sirve para ver dos cosas:
1. **¿Reentrenar con más meses ayuda?** Es el mismo paso que se haría para agosto (reentrenar con los meses disponibles), ensayado en un mes con respuestas.
2. **Comparar experimentos en el mismo mes**, aunque sus parámetros se hayan elegido con otro train.

Regla recomendada: meses de train ≤ mes de test − 2 (para junio, hasta abril). Si se usa mayo, el AVISO lo recuerda.

#%% celda 30 [código]
MESES_TRAIN_EXTRA = [202103, 202104, 202105]
MES_TEST_EXTRA = 202106

from comp.particiones import armar_particion, sumar_meses

for m in MESES_TRAIN_EXTRA:
    if m > sumar_meses(MES_TEST_EXTRA, -2):
        print(f'AVISO: train {m} rompe la regla M - 2 (su BAJA+2 se conoce recién en {sumar_meses(m, 2)}, '
              f'después de {MES_TEST_EXTRA}): la ganancia puede ser optimista.')

p_extra = armar_particion(data, MESES_TRAIN_EXTRA, MES_TEST_EXTRA, exp.columnas_excluidas, exp.clase_objetivo)
print(f"Train {MESES_TRAIN_EXTRA} ({p_extra['y_train'].sum()} BAJA+2 de {len(p_extra['y_train'])}) -> "
      f"test {MES_TEST_EXTRA} ({p_extra['y_test'].sum()} BAJA+2 de {len(p_extra['y_test'])})")

sufijo = 'train' + '-'.join(map(str, MESES_TRAIN_EXTRA)) + f'_test{MES_TEST_EXTRA}'
modelo_extra = modelos.entrenar_o_cargar(
    exp.modelos_dir / f'lgb_elegido{id_elegido}_{sufijo}.txt', params_elegido, modelos.datos_train(p_extra, exp, semillas[0]), arboles_elegido)
y_una = modelos.predecir(modelo_extra, p_extra['X_test'], exp)
y_ens_extra = ensamble.predecir_promedio_semillas(
    params_elegido, arboles_elegido, p_extra['train_lgb'], p_extra['X_test'], semillas[:config.N_SEMILLAS],
    archivo=exp.resultados_dir / f'pred_ensamble{id_elegido}_{sufijo}_{config.N_SEMILLAS}semillas.npy',
    y_train=p_extra['y_train'], undersampling=exp.undersampling,
)

filas = []
for modelo_nombre, y in [('una semilla', y_una), (f'ensamble {config.N_SEMILLAS} semillas', y_ens_extra)]:
    r = metricas.umbral_vs_mejor_corte(y, p_extra['y_test'], umbral=p_extra['umbral'], con_franja=True)
    filas.append({'modelo': modelo_nombre, 'ks': metricas.ks(y, p_extra['y_test'])['ks'], **r})
    graficos.curva_ganancia(
        metricas.ganancia_acumulada(y, p_extra['y_test']),
        titulo=f"{modelo_nombre} - train {MESES_TRAIN_EXTRA} -> test {MES_TEST_EXTRA}: p ≥ {p_extra['umbral']:.4g} (verde) contra el mejor corte (rojo)",
        envios_umbral=r['envios_umbral'], umbral=round(p_extra['umbral'], 4),
    ).show()

tabla_extra = pd.DataFrame(filas)
for c in ['ganancia_umbral', 'ganancia_mejor_corte', 'perdida']:
    tabla_extra[c] = (tabla_extra[c] / 1e6).round(1)  # en millones
tabla_extra.round({'ks': 4, 'p_mejor_corte': 4, 'perdida_pct': 1})

# [Anotación · líneas 367–406] Entrena con 202103-202106, predice 202108 con el ensamble de 20 semillas,
#   muestra la tabla de cortes, selecciona los 12058 clientes de mayor probabilidad (CORTE = 12058), guarda el
#   CSV en submits/ y lo anota en submits/registro.md.
#%% celda 31 [texto]
## Predicción de agosto y archivo de submit

Entrena **el modelo elegido** (mismos parámetros y árboles) con `MESES_TRAIN_FINAL`, predice `MES_PREDICCION` con el ensamble de semillas y guarda el archivo para la plataforma en `submits/`:
- solo los `numero_de_cliente` a estimular, uno por línea, sin encabezado, como enteros;
- entre 8000 y 15000 clientes (si el corte da otra cantidad, el archivo no se guarda y avisa);
- el nombre lleva el experimento, el trial, el corte y la fecha-hora, así **nunca se repite**. Cada vez que se corre con `GUARDAR_SUBMIT = True` se crea un archivo nuevo, anotado en `submits/registro.md`.

`CORTE`: `'umbral'` (p ≥ 0.025 en el modelo A; el umbral ajustado en el modelo B) o una cantidad de clientes (ej. `12000`, los de mayor probabilidad). La tabla de abajo muestra cuántos clientes da cada opción, para decidir con el ensayo de junio.

#%% celda 32 [código]
MESES_TRAIN_FINAL = [202103, 202104, 202105, 202106]
MES_PREDICCION = 202108
CORTE = 12058        # 'umbral' (p >= 0.025) o una cantidad de clientes, ej. 12000
GUARDAR_SUBMIT = True   # False: solo muestra cuántos clientes daría cada corte

from comp import entrega

pred = entrega.armar_prediccion(data, MESES_TRAIN_FINAL, MES_PREDICCION, exp.columnas_excluidas, exp.clase_objetivo)
print(f"Train {MESES_TRAIN_FINAL} ({pred['y_train'].sum()} BAJA+2 de {len(pred['y_train'])}) -> "
      f"predicción {MES_PREDICCION} ({len(pred['ids'])} clientes)")

sufijo_final = 'train' + '-'.join(map(str, MESES_TRAIN_FINAL)) + f'_pred{MES_PREDICCION}'
y_pred_final = entrega.predecir(
    params_elegido, arboles_elegido, pred, semillas[:config.N_SEMILLAS], undersampling=exp.undersampling,
    archivo=exp.resultados_dir / f'pred_ensamble{id_elegido}_{sufijo_final}_{config.N_SEMILLAS}semillas.npy',
)
print(f'Probabilidad media predicha en {MES_PREDICCION}: {y_pred_final.mean():.4f}')
print(f"Umbral de decisión: p >= {pred['umbral']:.4f}")
display(entrega.resumen_cortes(y_pred_final, umbral=pred['umbral']).round(4))

ids_submit = entrega.clientes_a_contactar(pred['ids'], y_pred_final, CORTE, umbral=pred['umbral'])
print(f'Corte {CORTE!r}: {len(ids_submit)} clientes a estimular')

if GUARDAR_SUBMIT:
    nombre_corte = 'umbral' if CORTE == 'umbral' else f'top{CORTE}'
    archivo_submit = entrega.guardar_submit(ids_submit, f'{exp.tag}{id_elegido}_{nombre_corte}')
    entrega.anotar_en_registro(archivo_submit, exp.tag, id_elegido.replace('_trial', '') or 'fijo', CORTE,
                               ids_submit, y_pred_final, MESES_TRAIN_FINAL)
    print('Submit guardado en', archivo_submit)
```


## Explicaciones del alumno (texto original)

### README.md

> # DMEyF 2026 - Competencia 1
>
> Este repositorio contiene el código, notebooks y experimentos desarrollados para la **Competencia 1** de la materia Datos Minería y Finanzas (DMEyF 2026).
>
> ---
>
> ## 🚀 Requisitos e Instalación
>
> Desde la raíz del repositorio (`dmeyf2026/`):
>
> 1. **Crear y activar el entorno virtual:**
>    ```bash
>    python3 -m venv .venv
>    source .venv/bin/activate
>    ```
>
> 2. **Instalar dependencias:**
>    ```bash
>    pip install -r requirements.txt
>    ```
>
> ---
>
> ## 📌 Reproducción del Submit con `main.py`
>
> El script `main.py` está preparado y configurado por defecto para reproducir exactamente lo que fue el **último submit de la competencia**.
>
> El script corre el flujo completo (o carga del disco todo lo ya calculado en `db/`, `modelos/` y `resultados/` para una reproducción inmediata) y genera el archivo `.csv` final listo para la plataforma directamente en la carpeta `competencia_uno/`.
>
> ### Ejecución
>
> Ejecutar z101_target_sql.ipynb para generar competencia_01.csv en competencia_uno.
>
> Ejecutar python competencia_uno/generate_features_extendido.py. Genera un archivo .parquet.
>
>
> Por último, desde la raíz del repositorio:
> ```bash
> .venv/bin/python competencia_uno/main.py
> ```
>
> *(O si estás ubicado dentro de la carpeta `competencia_uno/`:)*
> ```bash
> ../.venv/bin/python main.py
> ```
>
> ### Comparación con el submit de referencia (opcional)
> Si deseas comprobar automáticamente que el submit generado coincida cliente por cliente con el archivo original enviado:
> ```bash
> .venv/bin/python competencia_uno/main.py --comparar competencia_uno/submits/it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optumbral_ajustado_trial49_top12058_20261007_182001.csv
> ```
>
> ---
>
> ## 📂 Salidas y Resultados
>
> * **Submits generados por `main.py`:** se guardan directamente en `competencia_uno/<nombre_experimento>_<fecha_hora>.csv` para no sobreescribir los archivos de la carpeta `submits/`.
> * **Caché y reproducibilidad:** El script carga automáticamente los estudios de Optuna desde `db/`, los modelos entrenados desde `modelos/` y las predicciones calculadas desde `resultados/`. No recalcula lo existente, asegurando idénticos resultados y tiempos de ejecución mínimos.

### competencia_uno/registro.md

> # Submits generados
>
> | Archivo | Experimento | Trial | Train | Corte | Clientes | p minima enviada |
> |---|---|---|---|---|---|---|
> | `it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optumbral_ajustado_trial49_top12058_20261010_233903.csv` | it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optumbral_ajustado | 49 | 202103, 202104, 202105, 202106 | 12058 | 12058 | 0.0321 |
> | `it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optumbral_ajustado_trial49_top12058_20261010_234354.csv` | it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optumbral_ajustado | 49 | 202103, 202104, 202105, 202106 | 12058 | 12058 | 0.0321 |

