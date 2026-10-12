# marco — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: ssmito
- Repositorio: https://github.com/ssmito/dmeyf2026
- Link posteado: https://github.com/ssmito/dmeyf2026/tree/entrega-1/entregas
- Commit: 252df345b3a38a2a79d35d22cf8855793c1a718f
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/ssmito/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/ssmito.json

## Resumen

La entrega es la carpeta entregas/ de un fork del repositorio de la materia. El camino que produce la predicción tiene tres etapas, descriptas en readme.md. (1) Dos notebooks de Python generan los datasets desde competencia_01_crudo.csv: calculan la clase ternaria, ponen en NaN ccajas_depositos en 202105 y agregan 'lags fraccionarios' (promedio ponderado de los meses anteriores con pesos decrecientes, y la diferencia del valor actual contra ese promedio); un tercer dataset reemplaza cada variable por su ranking dentro del mes, con el cero fijo. (2) En bo/, los hiperparámetros de LightGBM se buscan con Optuna (GPSampler) maximizando average_precision sobre una partición 70/30 con submuestreo; los 3 juegos de mayor métrica se reentrenan con 5 semillas en 202103-202104 para medir la ganancia en 202106 y el de mayor ganancia promedio se guarda en un .rds. (3) p005_3models_runner.ipynb entrena tres modelos LightGBM (tres datasets, dos juegos de hiperparámetros) con 50 semillas sobre 202103-202106, con clase positiva BAJA+1 o BAJA+2, promedia las 150 probabilidades por cliente de 202108 y escribe los primeros `envios` clientes. La carpeta incluye además versiones anteriores (p001 a p004, r001 y r002), dos bitácoras en CSV y archivos de entorno.

**Qué entrega.** Un CSV sin encabezado con una columna numero_de_cliente: los primeros `envios` clientes de 202108 ordenados por el promedio de 150 probabilidades (3 modelos x 50 semillas), escrito como entregas/entregas/p005_3models_<id_prueba>.csv. El archivo no está en el repositorio. La copia de la notebook tiene envios = 12500 y logging_python.csv registra archivos de 12.000, 12.500 y 13.000 clientes para esa corrida.

**Cómo se ejecuta.** Según readme.md: (1) colocar competencia_01_crudo.csv en entregas/dataset/ y ejecutar completas, desde esa carpeta, versiones_dataset_1.ipynb y versiones_dataset_2.ipynb; (2) ejecutar entregas/p005_3models_runner.ipynb desde entregas/, en orden, hasta el punto anterior a la sección Documentación; necesita los datasets generados y los .rds de entregas/parametros/; (3) para replicar los hiperparámetros, desde entregas/bo: las BO con kernel Python (lag009_replica, lag028_replica) y luego, con kernel R, las validaciones multisemilla y las validaciones manuales, que generan 40-REPLICA.rds y 62-REPLICA.rds.

## Ficha

- **Lenguajes:** Python, R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: clase01 = 1 cuando ternaria es BAJA+1 o BAJA+2, 0 en el resto. La columna ternaria se calcula en funciones/ternaria.py según la presencia del cliente en los dos meses siguientes.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** El entrenamiento final (p005) usa todas las filas de los cuatro meses. En las optimizaciones bayesianas de bo/ el conjunto de entrenamiento conserva todas las BAJA+1 y BAJA+2 del fold 1 y las demás filas del fold 1 cuyo número al azar es menor o igual a 0,1 (undersampling 0,1 en PARAM.yml). Al pasar los hiperparámetros a un entrenamiento sin submuestreo, min_data_in_leaf se divide por 0,1.
- **Calidad de datos:** En dataset/versiones_dataset_2.ipynb la variable ccajas_depositos se reemplaza por NaN en las filas de foto_mes 202105, antes de generar las variables derivadas. No se observa otro tratamiento.
- **Drifting:** Sólo en el dataset del modelo 3 (RANKS_LF_O2_K6_P4.csv): cada variable se reemplaza por su ranking dentro de cada foto_mes, con positivos y negativos rankeados por separado y divididos por el máximo común de ambos, de modo que el valor queda entre -1 y 1, los ceros en 0 y los NaN sin cambio (rankear_por_mes con escala 'comun' y empates 'average'). Los modelos 1 y 2 usan los valores sin transformar.
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** 'Lags fraccionarios' para cada variable numérica: promedio ponderado de los K meses anteriores con pesos (1 - factor_perdida)^k normalizados, asignados por distancia real en meses y renormalizados cuando faltan valores (sufijo _lag_pond), y diferencia entre el valor actual y ese promedio (_delta_lag_pond). Modelos 1 y 3: K = 6, factor 0,4. Modelo 2: K = 3, factor 0,6, más una segunda ventana que empieza dos meses atrás (_lag_pond2 y _delta_lag_pond2). El dataset de la BO LAG-009 (versiones_dataset_1) usa en cambio lag 1 y delta 1 de todas las variables.
- **Selección de variables:** No se observa selección por importancia. Se excluyen a mano cprestamos_personales y mprestamos_personales con sus derivadas _lag1, _delta1, _lag_pond y _delta_lag_pond. La lista de exclusión de p005 no contiene numero_de_cliente, foto_mes ni las columnas _lag_pond2 y _delta_lag_pond2 de préstamos personales.
- **Optimización de hiperparámetros:** Optuna con GPSampler (semilla 230047), maximizando average_precision en validación. LAG-009: 200 trials (50 de inicio), mes 202104, dataset con lag 1 y delta 1. LAG-028: 60 trials (30 de inicio y 15 puntos encolados a mano según BO_log.txt), meses 202103 y 202104, dataset de rankings. Rangos (LAG-028/PARAM.yml): num_iterations 400-2000, num_leaves 256-2048, feature_fraction 0,1-0,35, min_sum_hessian_in_leaf 0,0001-0,1, learning_rate 0,005-0,025, min_data_in_leaf 100-1000, scale_pos_weight 0,5-1. Después, los 3 trials de mayor métrica de cada BO se reentrenan con 5 semillas en 202103-202104 y se toma el de mayor ganancia promedio en 202106.
- **Hiperparámetros finales:** Leídos de los .rds del repositorio. parametros/40.rds (modelos 1 y 2): num_iterations 454, num_leaves 256, learning_rate 0,01857, feature_fraction 0,2642, min_data_in_leaf 1810, min_sum_hessian_in_leaf 0,1, scale_pos_weight 0,5. parametros/62.rds (modelo 3): num_iterations 2000, num_leaves 2048, learning_rate 0,005, feature_fraction 0,35, min_data_in_leaf 1000, min_sum_hessian_in_leaf 0,1, scale_pos_weight 0,8647. En ambos: objective binary, boosting gbdt, max_bin 31, max_depth -1, lambda_l1 0, lambda_l2 0, bagging_fraction 1, early_stopping 0.
- **Semillas:** 50 números primos escritos en el código, de 230047 a 230567. Con cada semilla se entrenan los tres modelos. En bo/: semilla 230047 para la partición y el sampler, 5 primos sorteados entre 100.000 y 1.000.000 para el benchmark y 230047-230081 para la validación manual.
- **Cantidad de semillas:** 50
- **Ensamble:** Promedio aritmético de 150 probabilidades por cliente: 3 modelos LightGBM x 50 semillas. Los modelos difieren en el dataset (lags fraccionarios K=6, lags fraccionarios de dos ventanas K=3, y rankings por mes); los modelos 1 y 2 comparten hiperparámetros (40.rds) y el modelo 3 usa 62.rds.
- **Corte:** Cantidad fija: los primeros `envios` clientes ordenados por probabilidad promedio. En la copia del repositorio la celda de corte tiene envios = 12500 y la nota de la celda de documentación dice 'subimos envios a 13k'. logging_python.csv registra tres archivos de la corrida de 50 semillas, con 12.000, 12.500 y 13.000 clientes. El repositorio no indica cuál fue el envío final.
- **Validación:** Toda la validación está en bo/. (1) Dentro de cada BO: partición aleatoria estratificada 70/30 de los meses de la BO, midiendo average_precision. (2) Benchmark multisemilla: los 3 juegos de mayor métrica se entrenan en 202103-202104 con 5 semillas y se calcula la ganancia en 202106 (1.072.500 por BAJA+2 enviado, -27.500 por cualquier otro) para los cortes guardados en PARAM.rds (4.000 a 19.000 cada 500), con una división Public/Private 30/70. (3) Validación manual: el juego elegido se reentrena con 5 semillas y se registra el promedio de la ganancia máxima en 202106. El entrenamiento final no separa validación.
- **Salidas:** predicciones/p005_3models_overnight/: configuracion.json y, por semilla, tres CSV (numero_de_cliente, prob) más la marca completa.json. entregas/p005_3models_<id_prueba>.csv: una columna numero_de_cliente sin encabezado. Una fila por archivo generado en logging_python.csv.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Optuna (`hiperparametros.optuna`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)

## Técnicas sólo exploradas

- Clase artificial o pseudo-etiquetas para meses sin clase (`clase.clase_artificial`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: no
- Entorno declarado: readme.md: ejecución local con 64 GB de RAM, con los tres datasets en memoria. entorno.yml: entorno conda cmeyf-cuda13 con Python 3.11.15, lightgbm 4.7.0, pandas 3.0.3, numpy 2.4.6, optuna 4.9.0, scikit-learn 1.9.0, rdata 1.1.0 y cudf-cu13 26.8.1. sessionInfo.txt: R 4.3.1 (x86_64-conda-linux-gnu) y lista de paquetes instalados, entre ellos lightgbm 4.6.0. Los sessionInfo.txt de los dos benchmarks indican Ubuntu 22.04.2 LTS.

## Pasos del camino de la entrega

1. **Lectura del crudo y corrección de una variable.** versiones_dataset_2.ipynb lee competencia_01_crudo.csv y reemplaza por NaN ccajas_depositos en foto_mes 202105. (`entregas/dataset/versiones_dataset_2.ipynb` líneas 41–54)
2. **Cálculo de la clase ternaria.** ternaria() marca cada fila como BAJA+1, BAJA+2 o 'continua' según si el cliente aparece en el mes siguiente y en el subsiguiente; el penúltimo mes sólo recibe BAJA+1 y el último queda sin clase. El resultado se guarda en c_01_tern_2.csv. (`entregas/funciones/ternaria.py` líneas 7–53; `entregas/dataset/versiones_dataset_2.ipynb` líneas 62–72)
3. **Lags fraccionarios K=6 (dataset del modelo 1).** Para cada variable numérica se calcula el promedio ponderado de los 6 meses anteriores con pesos 0,6^k normalizados (_lag_pond) y la diferencia del valor actual contra ese promedio (_delta_lag_pond). Se guarda c_01_tern_2_lf_k6_p4.csv. (`entregas/dataset/versiones_dataset_2.ipynb` líneas 176–342; `entregas/dataset/versiones_dataset_2.ipynb` líneas 348–376)
4. **Lags fraccionarios de dos ventanas K=3 (dataset del modelo 2).** Con K = 3 y factor_perdida 0,6 se calculan dos promedios ponderados: uno sobre los meses a distancia 1 a 3 y otro sobre los meses a distancia 2 a 4 (sufijo 2), cada uno con su delta. Se guarda c_01_tern_2_lf_O2_k3_p6.csv. (`entregas/dataset/versiones_dataset_2.ipynb` líneas 493–652; `entregas/dataset/versiones_dataset_2.ipynb` líneas 655–671)
5. **Ranking por mes con cero fijo (dataset del modelo 3).** rankear_por_mes reemplaza cada variable del dataset K=6 por su ranking dentro del mes, con signo y normalizado entre -1 y 1. Se guarda RANKS_LF_O2_K6_P4.csv. (`entregas/funciones/ternaria.py` líneas 55–121; `entregas/dataset/versiones_dataset_2.ipynb` líneas 686–704)
6. **Dataset con lag 1 y delta 1 para la BO LAG-009.** versiones_dataset_1.ipynb agrega a cada variable el valor del mes anterior y la diferencia con él, y guarda competencia_01_ternaria_lags.csv. En esta notebook no se anula ccajas_depositos. (`entregas/dataset/versiones_dataset_1.ipynb` líneas 71–157)
7. **Optimización de hiperparámetros con Optuna.** Cada BO parte los meses de entrenamiento 70/30, submuestrea al 10% las filas que no son baja en el fold de entrenamiento y maximiza average_precision con GPSampler. LAG-009 usa 202104 y 200 trials; LAG-028 usa 202103-202104 y 60 trials. Las notebooks de réplica toman rangos y puntos iniciales del estudio original y escriben en carpetas -REPLICA. (`entregas/bo/lag009_replica.ipynb` líneas 111–248; `entregas/bo/lag028_replica.ipynb` líneas 127–265; `entregas/bo/LAG-009/PARAM.yml` líneas 1–58; `entregas/bo/LAG-028/PARAM.yml` líneas 1–101)
8. **Benchmark multisemilla sobre 202106.** Los 3 trials de mayor métrica de cada BO se entrenan con 5 semillas en 202103-202104, sin submuestreo y con min_data_in_leaf dividido por 0,1. Para cada corte se calcula la ganancia en 202106 y se conserva, por modelo, el corte de mayor ganancia total promedio. (`entregas/bo/validacion_multisemilla_lag009_replica.ipynb` líneas 214–263; `entregas/bo/validacion_multisemilla_lag009_replica.ipynb` líneas 380–408; `entregas/bo/validacion_multisemilla_lag009_replica.ipynb` líneas 495–584; `entregas/bo/validacion_multisemilla_lag009_replica.ipynb` líneas 628–632; `entregas/bo/validacion_multisemilla_lag028_replica.ipynb` líneas 502–591)
9. **Validación manual y archivo de parámetros.** Se toma del benchmark el modelo de mayor ganancia promedio, se combinan sus hiperparámetros con los fijos, se entrena con las semillas 230047 a 230081 en 202103-202104, se mide la ganancia en 202106 y se guarda la lista de parámetros por semilla en un .rds (40-REPLICA.rds y 62-REPLICA.rds). Según readme.md, p005 usa los originales parametros/40.rds y 62.rds. (`entregas/bo/validacion_manual_lag009_replica.ipynb` líneas 149–174; `entregas/bo/validacion_manual_lag009_replica.ipynb` líneas 194–241; `entregas/bo/validacion_manual_lag009_replica.ipynb` líneas 299–303; `entregas/bo/validacion_manual_lag028_replica.ipynb` líneas 158–183; `entregas/bo/validacion_manual_lag028_replica.ipynb` líneas 319–323)
10. **Configuración de la corrida final.** p005 declara los tres datasets, los .rds 40, 40 y 62, los meses de entrenamiento 202103-202106, el mes 202108, las 50 semillas y las 16 columnas excluidas, y registra en configuracion.json las huellas de los archivos de entrada y las versiones de las librerías. (`entregas/p005_3models_runner.ipynb` líneas 44–91; `entregas/p005_3models_runner.ipynb` líneas 178–191)
11. **Preparación de las matrices de cada modelo.** Para cada dataset se lee el CSV, se crea clase01 (BAJA+1 o BAJA+2), se leen los hiperparámetros del .rds y se arman en memoria las matrices de entrenamiento y de predicción. (`entregas/p005_3models_runner.ipynb` líneas 208–257)
12. **Entrenamiento por semilla.** Para cada una de las 50 semillas se entrenan los tres LightGBM con todas las filas de entrenamiento y se guardan las probabilidades de 202108 en tres CSV y una marca completa.json; las semillas ya completas se saltean al retomar. (`entregas/p005_3models_runner.ipynb` líneas 260–290; `entregas/p005_3models_runner.ipynb` líneas 329–371)
13. **Combinación de modelos y semillas.** Se leen las probabilidades guardadas de todas las semillas completas, se verifican clientes y cantidades, y se promedian por cliente las columnas de los tres modelos. (`entregas/p005_3models_runner.ipynb` líneas 381–433)
14. **Corte y archivo de entrega.** Se escriben en un CSV sin encabezado los primeros `envios` clientes por probabilidad promedio (12500 en la copia del repositorio); el nombre lleva el id_prueba siguiente al último de la bitácora. (`entregas/p005_3models_runner.ipynb` líneas 441–464)
15. **Registro en la bitácora.** Se agrega o actualiza en logging_python.csv una fila con datasets, semillas, meses, columnas excluidas, .rds, envíos, archivo, nota y resultado. Según logging_python.csv, las filas 53, 54 y 55 (50 semillas; 12.000, 12.500 y 13.000 envíos) registran resultado_competencia_mean 106.7000, 107.6350 y 106.7000. (`entregas/p005_3models_runner.ipynb` líneas 474–525)

## Archivos

- `entregas/p003_2models.ipynb` · secundario · Jupyter (python) · 298 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/p003_2models.ipynb.txt) — Ensamble de 2 modelos (c_01_tern_2_lf_k6_p4.csv y c_01_tern_2_lf_O2_k3_p6.csv, ambos con .rds 40) y 20 semillas, en una sola pasada en memoria: promedia las 40 probabilidades por cliente y escribe un CSV con el corte (12500 en la copia).
- `entregas/sessionInfo.txt` · configuracion · Texto · 232 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/sessionInfo.txt.txt) — Versión de R (4.3.1, x86_64-conda-linux-gnu) y lista de paquetes de R instalados con su versión, entre ellos lightgbm 4.6.0.
- `entregas/p005_3models_runner.ipynb` · principal · Jupyter (python) · 531 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/p005_3models_runner.ipynb.txt) — Notebook que el readme indica ejecutar para la entrega: entrena tres modelos LightGBM por cada una de 50 semillas, guarda las probabilidades por semilla, las promedia por cliente y escribe el CSV con el corte y la fila de bitácora.
- `entregas/p002.ipynb` · secundario · Jupyter (python) · 350 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/p002.ipynb.txt) — Versión con pseudoetiquetas: un primer modelo entrenado en 202103-202106 predice 202107; se conservan las BAJA+1 reales de julio y se marca BAJA+2 a los clientes con probabilidad mayor o igual a prob_corte (0,00354); el modelo final entrena en 202103-202107 con 5 semillas (.rds 52 y 53) y escribe un CSV por semilla.
- `entregas/p001.ipynb` · secundario · Jupyter (python) · 290 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/p001.ipynb.txt) — Versión anterior en Python con un dataset y un .rds: entrena un LightGBM por semilla (20 semillas, .rds 40, c_01_tern_2_lf_k6_p4.csv, meses 202103 a 202106) y escribe un CSV por semilla con los primeros `envios` clientes (11000 en la copia), sin promediar entre semillas; registra la prueba en logging_python.csv.
- `entregas/readme.md` · explicacion · Markdown · 38 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/readme.md.txt) — Instrucciones en tres secciones: cómo ejecutar la entrega (p005 desde entregas/, 50 semillas, 64 GB de RAM), cómo generar los datasets (dos notebooks en entregas/dataset/) y cómo replicar las BO, los benchmarks multisemilla y los .rds. Declara que los hiperparámetros de LAG-009 se buscaron con un dataset y se usan con otros dos.
- `entregas/r002.ipynb` · secundario · Jupyter (R) · 332 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/r002.ipynb.txt) — Versión en R de p002 (pseudoetiquetas para 202107 con .rds 52 y modelo final con .rds 53, 5 semillas), con una celda para generar cortes adicionales sin reentrenar; registra en logging.csv.
- `entregas/entorno.yml` · configuracion · YAML · 414 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/entorno.yml.txt) — Exportación del entorno conda cmeyf-cuda13 con versiones exactas: Python 3.11.15 y, por pip, lightgbm 4.7.0, pandas 3.0.3, optuna 4.9.0, rdata 1.1.0 y cudf-cu13 26.8.1, entre otros paquetes.
- `entregas/p004_3models.ipynb` · secundario · Jupyter (python) · 297 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/p004_3models.ipynb.txt) — Igual a p003 con un tercer modelo (RANKS_LF_O2_K6_P4.csv con .rds 62): 3 modelos por 20 semillas, promedio de 60 probabilidades y corte de 12000 en la copia. Es la notebook que p005 adapta.
- `entregas/r001.ipynb` · secundario · Jupyter (R) · 228 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/r001.ipynb.txt) — Versión en R de p001: lee el dataset con data.table y el .rds con readRDS, entrena un LightGBM por semilla (5 semillas, .rds 40) en 202103-202106, escribe un CSV por semilla con los primeros 11000 clientes y registra en logging.csv.
- `entregas/dataset/versiones_dataset_1.ipynb` · principal · Jupyter (python) · 368 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/dataset/versiones_dataset_1.ipynb.txt) — Genera competencia_01_ternaria_lags.csv (clase ternaria más lag 1 y delta 1 de cada variable), el dataset que lee la BO LAG-009. La sección de lags fraccionarios está comentada.
- `entregas/dataset/versiones_dataset_2.ipynb` · principal · Jupyter (python) · 721 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/dataset/versiones_dataset_2.ipynb.txt) — Genera, a partir de competencia_01_crudo.csv, los tres datasets que lee p005: lags fraccionarios K=6, lags fraccionarios de dos ventanas K=3 y rankings por mes. Contiene además bloques comentados de lags de orden 1 y 2.
- `entregas/funciones/ternaria.py` · principal · Python · 121 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/funciones/ternaria.py.txt) — Módulo con las dos funciones que usan las notebooks de dataset: ternaria() calcula la clase por presencia del cliente en los meses siguientes y rankear_por_mes() reemplaza variables por su ranking mensual con signo.
- `entregas/bo/validacion_multisemilla_lag009_replica.ipynb` · principal · Jupyter (R) · 686 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/validacion_multisemilla_lag009_replica.ipynb.txt) — Réplica en R del benchmark multisemilla de LAG-009: reentrena los juegos de hiperparámetros de mayor métrica de la BO con varias semillas y mide la ganancia en el mes futuro para una lista de cortes.
- `entregas/bo/validacion_manual_lag028_replica.ipynb` · principal · Jupyter (R) · 330 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/validacion_manual_lag028_replica.ipynb.txt) — Validación manual en R del modelo elegido en el benchmark de LAG-028, sobre el dataset de rankings; guarda los parámetros por semilla en 62-REPLICA.rds.
- `entregas/bo/lag028_replica.ipynb` · principal · Jupyter (python) · 285 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/lag028_replica.ipynb.txt) — Réplica de la optimización bayesiana LAG-028 con Optuna sobre el dataset de rankings, de la que salen los hiperparámetros de parametros/62.rds (modelo 3). Lee bo/LAG-028/ y escribe en bo/LAG-028-REPLICA/.
- `entregas/bo/validacion_manual_lag009_replica.ipynb` · principal · Jupyter (R) · 310 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/validacion_manual_lag009_replica.ipynb.txt) — Validación manual en R del modelo elegido en el benchmark de LAG-009: lo reentrena con 5 semillas, mide la ganancia en 202106 y guarda los parámetros por semilla en 40-REPLICA.rds.
- `entregas/bo/validacion_multisemilla_lag028_replica.ipynb` · principal · Jupyter (R) · 693 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/validacion_multisemilla_lag028_replica.ipynb.txt) — Réplica en R del benchmark multisemilla de LAG-028; mismo código que la de LAG-009, con otro benchmark de origen y una lista de 25 columnas excluidas.
- `entregas/bo/lag009_replica.ipynb` · principal · Jupyter (python) · 268 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/lag009_replica.ipynb.txt) — Réplica de la optimización bayesiana LAG-009 con Optuna, de la que salen los hiperparámetros de parametros/40.rds (modelos 1 y 2). Lee la configuración y el estudio de bo/LAG-009/ y escribe en bo/LAG-009-REPLICA/.
- `entregas/bo/LAG-028/BO_log.txt` · secundario · Texto · 61 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/LAG-028/BO_log.txt.txt) — Tabla exportada de Optuna con los 60 trials de la BO original LAG-028, ordenada de mayor a menor value; 15 filas corresponden a puntos encolados a mano. La primera fila es el trial 42, value 0,1272.
- `entregas/bo/LAG-028/PARAM.yml` · configuracion · YAML · 113 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/LAG-028/PARAM.yml.txt) — Parámetros y resultado de la BO original LAG-028: meses 202103 y 202104, undersampling 0,1, 60 iteraciones con 30 de inicio, 15 ids de modelos previos, rangos de búsqueda de 7 hiperparámetros, una ruta absoluta en archivo_validaciones, dataset RANKS_LF_O2_K6_P4.csv y el trial de mayor métrica (average_precision 0,1272).
- `entregas/bo/LAG-028/impo.txt` · secundario · Texto · 435 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/LAG-028/impo.txt.txt) — Importancia de variables (Gain, Cover, Frequency) de un modelo de LAG-028: 434 variables, la primera es ctrx_quarter. Ninguna notebook de la entrega lo genera ni lo lee.
- `entregas/bo/LAG-009/BO_log.txt` · secundario · Texto · 201 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/LAG-009/BO_log.txt.txt) — Tabla exportada de Optuna con los 200 trials de la BO original LAG-009, ordenada de mayor a menor value: número, valor, tiempos, los 7 hiperparámetros, puntos encolados a mano (3 filas) y estado. La primera fila es el trial 83, value 0,1325.
- `entregas/bo/LAG-009/PARAM.yml` · configuracion · YAML · 69 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/LAG-009/PARAM.yml.txt) — Parámetros y resultado de la BO original LAG-009: semilla 230047, training_pct 70, mes 202104, undersampling 0,1, 200 iteraciones con 50 de inicio, parámetros fijos de LightGBM (objective binary, metric average_precision, max_bin 31) y, en out, los hiperparámetros del trial de mayor métrica (average_precision 0,1325).
- `entregas/bo/LAG-009/impo.txt` · secundario · Texto · 320 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/LAG-009/impo.txt.txt) — Importancia de variables (Gain, Cover, Frequency) de un modelo de LAG-009: 319 variables, la primera es ctrx_quarter. Ninguna notebook de la entrega lo genera ni lo lee.
- `entregas/bo/benchmark_multisemilla_lags20260924_114539/sessionInfo.txt` · configuracion · Texto · 36 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/benchmark_multisemilla_lags20260924_114539/sessionInfo.txt.txt) — sessionInfo de R del benchmark multisemilla original de LAG-009: R 4.3.1 sobre Ubuntu 22.04.2 LTS, generador L'Ecuyer-CMRG, lightgbm 4.6.0, primes 1.6.1, here 1.0.2 y data.table 1.14.8.
- `entregas/bo/benchmark_multisemilla_lags20261009_200322/sessionInfo.txt` · configuracion · Texto · 36 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/benchmark_multisemilla_lags20261009_200322/sessionInfo.txt.txt) — sessionInfo de R del benchmark multisemilla original de LAG-028, con el mismo contenido que el de LAG-009.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### entregas/p005_3models_runner.ipynb

Notebook que el readme indica ejecutar para la entrega: entrena tres modelos LightGBM por cada una de 50 semillas, guarda las probabilidades por semilla, las promedia por cliente y escribe el CSV con el corte y la fila de bitácora.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–22] Presentación de la notebook (adaptación de p004_3models.ipynb: tres modelos por
#   semilla, datos en memoria y posibilidad de retomar) y carga de librerías: pandas, numpy, lightgbm, rdata
#   para leer los .rds de R, hashlib, json y gc.
#%% celda 1 [texto]
# p005 — Predicciones de 3 modelos por semilla, con datos en memoria

Adaptación de `p004_3models.ipynb`. Cada modelo conserva su dataset y RDS, leídos desde `dataset/` y `parametros/`. Los meses y columnas excluidas son compartidos.

Para cada semilla se entrenan los modelos 1, 2 y 3, en ese orden. Después se guardan sus tres predicciones en `predicciones/`. Se puede interrumpir la generación y pasar a la celda de combinación: solamente se usan semillas con los tres archivos completos. Volver a ejecutar la generación retoma las semillas pendientes, hasta completar las 50.

Guardar y ejecutar esta notebook desde `entregas/`, como p004. Las primeras 20 semillas son las de p004; se agregan los siguientes 30 primos de la misma secuencia.

Los tres datasets se leen y preparan una sola vez. Se mantienen en RAM sus matrices de entrenamiento, etiquetas, matrices de predicción e identificadores de clientes durante todas las semillas. Los DataFrames usados para prepararlas se liberan para evitar copias duplicadas.

#%% celda 2 [código]
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb
import rdata
from IPython.display import display
import os
import gc
import hashlib
import json

# [Anotación · líneas 24–36] Define las rutas a partir del directorio de trabajo (se ejecuta desde entregas/):
#   dataset/, parametros/, entregas/ para la salida, predicciones/ para las probabilidades por semilla y
#   logging_python.csv como bitácora. Lista el contenido de dataset/.
#%% celda 3 [texto]
## Directorios

#%% celda 4 [código]
carpeta_entregas = Path.cwd()
data_folder = carpeta_entregas / "dataset"
carpeta_parametros = carpeta_entregas / "parametros"
carpeta_salida = carpeta_entregas / "entregas"
archivo_logging = carpeta_entregas / "logging_python.csv"
carpeta_predicciones = carpeta_entregas / "predicciones"

#%% celda 5 [código]
os.listdir(data_folder)

# [Anotación · líneas 38–71] Parámetros de la corrida: un dataset por modelo (c_01_tern_2_lf_k6_p4.csv,
#   c_01_tern_2_lf_O2_k3_p6.csv y RANKS_LF_O2_K6_P4.csv), los .rds de hiperparámetros 40, 40 y 62, meses de
#   entrenamiento 202103 a 202106, mes a predecir 202108 y 50 semillas (números primos de 230047 a 230567). La
#   corrida se llama p005_3models_overnight y sus archivos van a predicciones/p005_3models_overnight/.
#%% celda 6 [texto]
## Parámetros

Completar los tres datasets y RDS en el mismo orden: modelo 1, modelo 2, modelo 3. Se conservan los valores de p004. `nombre_corrida` identifica las predicciones guardadas; usar otro nombre cuando cambien datasets, RDS, meses o columnas. La celda de generación se puede volver a ejecutar para retomar esta misma corrida.

#%% celda 7 [código]
dataset_files = [
    "c_01_tern_2_lf_k6_p4.csv",  # dataset del modelo 1, con .csv
    "c_01_tern_2_lf_O2_k3_p6.csv",  # dataset del modelo 2, con .csv
    "RANKS_LF_O2_K6_P4.csv",  # dataset del modelo 3, con .csv
]
ids_rds = [
    40,  # id del RDS del modelo 1
    40,  # id del RDS del modelo 2
    62,  # id del RDS del modelo 3
]

train_final = [202103, 202104, 202105, 202106]
future = [202108]
SEEDS = [
    230047, 230059, 230063, 230077, 230081,
    230089, 230101, 230107, 230117, 230123,
    230137, 230143, 230149, 230189, 230203,
    230213, 230221, 230227, 230233, 230239,
    230257, 230273, 230281, 230291, 230303,
    230309, 230311, 230327, 230339, 230341,
    230353, 230357, 230369, 230383, 230387,
    230389, 230393, 230431, 230449, 230453,
    230467, 230471, 230479, 230501, 230507,
    230539, 230551, 230561, 230563, 230567,
]

nombre_corrida = "p005_3models_overnight"
carpeta_corrida = carpeta_predicciones / nombre_corrida

# [Anotación · líneas 73–91] Lista de 16 columnas que no entran al modelo: ternaria, ternaria_lag1, clase01,
#   fold, azar, training, y cprestamos_personales y mprestamos_personales con sus derivadas _lag1, _delta1,
#   _lag_pond y _delta_lag_pond. La lista no incluye numero_de_cliente, foto_mes ni las columnas con sufijo
#   _lag_pond2 o _delta_lag_pond2.
#%% celda 8 [código]
columnas_excluir = [
    "ternaria",
    "ternaria_lag1",
    "clase01",
    "fold",
    "azar",
    "training",
    "cprestamos_personales",
    "mprestamos_personales",
    "cprestamos_personales_lag1",
    "mprestamos_personales_lag1",
    "cprestamos_personales_delta1",
    "mprestamos_personales_delta1",
    "cprestamos_personales_lag_pond",
    "mprestamos_personales_lag_pond",
    "cprestamos_personales_delta_lag_pond",
    "mprestamos_personales_delta_lag_pond"
]

# [Anotación · líneas 93–125] convertir_r pasa la estructura leída del .rds a diccionarios, listas y escalares
#   de Python, y convierte a entero los números de punto flotante sin parte decimal. data_matrix arma la matriz
#   numérica float64: las columnas categóricas o de texto se reemplazan por el código de su nivel (desde 1, con
#   los niveles ordenados) y los faltantes quedan como NaN.
#%% celda 9 [texto]
## Lectura de parámetros y preparación de datos

#%% celda 10 [código]
def convertir_r(valor):
    if isinstance(valor, dict):
        return {k: convertir_r(v) for k, v in valor.items()}
    if isinstance(valor, np.ndarray):
        if valor.size == 1:
            return convertir_r(valor.item())
        return [convertir_r(v) for v in valor.tolist()]
    if isinstance(valor, (list, tuple)):
        return [convertir_r(v) for v in valor]
    if isinstance(valor, np.generic):
        return convertir_r(valor.item())
    # R serializa muchos parámetros enteros como double (31.0).
    # LightGBM Python exige int para esos valores; se conserva su valor.
    if isinstance(valor, float) and np.isfinite(valor) and valor.is_integer():
        return int(valor)
    return valor

def data_matrix(df):
    matriz = df.copy()
    for nombre in matriz.columns:
        serie = matriz[nombre]
        if isinstance(serie.dtype, pd.CategoricalDtype):
            codigos = serie.cat.codes
            matriz[nombre] = (codigos + 1).where(codigos >= 0, np.nan)
        elif pd.api.types.is_object_dtype(serie.dtype) or pd.api.types.is_string_dtype(serie.dtype):
            niveles = sorted(serie.dropna().unique())
            codigos = pd.Categorical(serie, categories=niveles).codes
            matriz[nombre] = np.where(codigos >= 0, codigos + 1, np.nan)
    return matriz.to_numpy(dtype=np.float64)

# [Anotación · líneas 127–155] Texto sobre los archivos de la corrida y dos funciones:
#   configuracion_solicitada verifica que haya tres datasets, tres ids de .rds, un único mes a predecir,
#   semillas sin repetir y un nombre de corrida sin directorios, y devuelve esos parámetros como diccionario;
#   guardar_json escribe un JSON en un archivo temporal y lo renombra sobre el destino.
#%% celda 11 [texto]
## Archivos de la corrida

`configuracion.json` registra los parámetros y fuentes de esta corrida. En cada `semilla_XXXXXX/` se guardan tres CSV con `numero_de_cliente` y `prob`. `completa.json` se escribe al terminar los tres archivos y registra las cantidades de filas. Una carpeta sin esa marca queda fuera del promedio y se vuelve a generar al retomar.

#%% celda 12 [código]
def configuracion_solicitada():
    if (len(dataset_files) != 3 or len(ids_rds) != 3
            or any(not archivo for archivo in dataset_files)
            or any(id_rds is None for id_rds in ids_rds)):
        raise ValueError("Completar los tres datasets y sus tres ids_rds, en el mismo orden.")
    if len(future) != 1 or not SEEDS or len(SEEDS) != len(set(SEEDS)):
        raise ValueError("Se requiere un mes a predecir y una lista de semillas sin repetidos.")
    if not nombre_corrida or Path(nombre_corrida).name != nombre_corrida or nombre_corrida in (".", ".."):
        raise ValueError("nombre_corrida debe ser un nombre de carpeta, sin directorios.")
    return {
        "dataset_files": list(dataset_files),
        "ids_rds": [str(id_rds) for id_rds in ids_rds],
        "train_final": list(train_final),
        "future": list(future),
        "seeds": list(SEEDS),
        "columnas_excluir": list(columnas_excluir),
    }


def guardar_json(archivo, datos):
    temporal = archivo.with_name(archivo.name + ".tmp")
    temporal.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temporal, archivo)


# [Anotación · líneas 158–191] fuente_modelo toma, para un modelo, el tamaño y la fecha de modificación del
#   CSV y el SHA-256 del .rds. leer_configuracion lee configuracion.json y corta la ejecución si difiere de los
#   parámetros actuales. preparar_corrida crea configuracion.json la primera vez (parámetros, fuentes y
#   versiones de lightgbm, pandas y numpy) y, si ya existe, corta la ejecución cuando cambiaron las fuentes o
#   las versiones.
def fuente_modelo(numero_modelo, configuracion):
    dataset_file = configuracion["dataset_files"][numero_modelo - 1]
    id_rds = configuracion["ids_rds"][numero_modelo - 1]
    datos = (data_folder / dataset_file).stat()
    return {
        "dataset_bytes": datos.st_size,
        "dataset_mtime_ns": datos.st_mtime_ns,
        "rds_sha256": hashlib.sha256((carpeta_parametros / f"{id_rds}.rds").read_bytes()).hexdigest(),
    }


def leer_configuracion():
    archivo = carpeta_corrida / "configuracion.json"
    configuracion = json.loads(archivo.read_text(encoding="utf-8"))
    solicitada = configuracion_solicitada()
    if any(configuracion.get(k) != v for k, v in solicitada.items()):
        raise ValueError("Esta corrida tiene otros parámetros. Revisar los parámetros o usar otro nombre_corrida.")
    return configuracion


def preparar_corrida():
    solicitada = configuracion_solicitada()
    fuentes = [fuente_modelo(n, solicitada) for n in (1, 2, 3)]
    versiones = {"lightgbm": lgb.__version__, "pandas": pd.__version__, "numpy": np.__version__}
    archivo = carpeta_corrida / "configuracion.json"
    if archivo.exists():
        configuracion = leer_configuracion()
        if configuracion["fuentes"] != fuentes or configuracion["versiones"] != versiones:
            raise ValueError("Cambiaron las fuentes o versiones de esta corrida. Revisarlas o usar otro nombre_corrida.")
    else:
        configuracion = dict(solicitada, fuentes=fuentes, versiones=versiones)
        carpeta_corrida.mkdir(parents=True, exist_ok=True)
        guardar_json(archivo, configuracion)
    return configuracion


# [Anotación · líneas 194–205] archivos_semilla devuelve las tres rutas modelo_<n>_<semilla>.csv dentro de
#   semilla_<semilla>/. semillas_guardadas devuelve las semillas que tienen los tres CSV y la marca
#   completa.json.
def archivos_semilla(seed):
    carpeta = carpeta_corrida / f"semilla_{seed}"
    return [carpeta / f"modelo_{n}_{seed}.csv" for n in (1, 2, 3)]


def semillas_guardadas(configuracion):
    completas = []
    for seed in configuracion["seeds"]:
        marca = carpeta_corrida / f"semilla_{seed}" / "completa.json"
        if marca.exists() and all(archivo.exists() for archivo in archivos_semilla(seed)):
            completas.append(seed)
    return completas

# [Anotación · líneas 207–231] preparar_modelo, primera parte: comprueba que el dataset y el .rds no hayan
#   cambiado, lee el CSV, reemplaza por cadena vacía los faltantes de ternaria y ordena por foto_mes, ternaria y
#   numero_de_cliente. Lee el .rds; si es una lista por semilla toma su primer elemento como parámetros base.
#   Crea clase01 = 1 cuando ternaria es BAJA+1 o BAJA+2, arma la lista de columnas de entrada (todas menos las
#   excluidas) y separa las filas de entrenamiento (202103 a 202106) y las del mes a predecir (202108).
#%% celda 13 [código]
def preparar_modelo(numero_modelo, configuracion):
    if fuente_modelo(numero_modelo, configuracion) != configuracion["fuentes"][numero_modelo - 1]:
        raise ValueError(f"Modelo {numero_modelo}: cambiaron el dataset o RDS de esta corrida.")

    dataset_file = configuracion["dataset_files"][numero_modelo - 1]
    id_rds = configuracion["ids_rds"][numero_modelo - 1]
    dataset = pd.read_csv(data_folder / dataset_file, low_memory=False)
    dataset["ternaria"] = dataset["ternaria"].fillna("")
    dataset = dataset.sort_values(
        ["foto_mes", "ternaria", "numero_de_cliente"],
        kind="stable", na_position="first",
    ).reset_index(drop=True)

    parametros = convertir_r(rdata.read_rds(carpeta_parametros / f"{id_rds}.rds"))
    params_base = (
        parametros
        if "num_iterations" in parametros
        else next(iter(parametros.values()))
    )

    dataset["clase01"] = dataset["ternaria"].isin(["BAJA+1", "BAJA+2"]).astype(np.int32)
    campos_buenos = [c for c in dataset.columns if c not in configuracion["columnas_excluir"]]
    dataset_train = dataset.loc[dataset["foto_mes"].isin(configuracion["train_final"])].copy()
    dfuture = dataset.loc[dataset["foto_mes"].isin(configuracion["future"])].copy()

# [Anotación · líneas 233–257] preparar_modelo, segunda parte: corta si no hay filas o si los identificadores
#   de cliente del mes a predecir están repetidos o vacíos. Construye las matrices X_train y X_future y devuelve
#   un diccionario con parámetros base, nombres de columnas, matrices, etiquetas, clientes y cantidades de
#   filas; borra los DataFrames intermedios.
    if dataset_train.empty or dfuture.empty:
        raise ValueError(f"Modelo {numero_modelo}: no hay filas para los meses elegidos.")

    tb_predicciones = dfuture[["numero_de_cliente"]].set_index("numero_de_cliente")
    if not tb_predicciones.index.is_unique or tb_predicciones.index.hasnans:
        raise ValueError(f"Modelo {numero_modelo}: revisar los identificadores de clientes en future.")

    cantidad_total = len(dataset)
    cantidad_train = len(dataset_train)

    X_train = data_matrix(dataset_train[campos_buenos])
    X_future = data_matrix(dfuture[campos_buenos])
    datos_modelo = {
        "params_base": params_base,
        "campos_buenos": campos_buenos,
        "X_train": X_train,
        "X_future": X_future,
        "clase01": dataset_train["clase01"].to_numpy(copy=True),
        "clientes": tb_predicciones.index.copy(),
        "cantidad_total": cantidad_total,
        "cantidad_train": cantidad_train,
    }
    del dataset, dataset_train, dfuture
    print(f"Modelo={numero_modelo}: datos preparados en memoria")
    return datos_modelo


# [Anotación · líneas 260–290] entrenar_modelo: copia los parámetros base, fija seed con la semilla recibida y
#   separa num_iterations como cantidad de rondas. Arma el lgb.Dataset con las matrices en memoria y sin
#   variables categóricas, entrena con lgb.train, predice la probabilidad para los clientes de 202108 y corta si
#   alguna no es finita. Devuelve la tabla de probabilidades indexada por cliente y las cantidades de filas.
def entrenar_modelo(numero_modelo, seed, configuracion):
    if fuente_modelo(numero_modelo, configuracion) != configuracion["fuentes"][numero_modelo - 1]:
        raise ValueError(f"Modelo {numero_modelo}: cambiaron el dataset o RDS de esta corrida.")

    datos_modelo = datos_modelos[numero_modelo - 1]
    params_base = datos_modelo["params_base"]
    campos_buenos = datos_modelo["campos_buenos"]
    X_train = datos_modelo["X_train"]
    X_future = datos_modelo["X_future"]
    tb_predicciones = pd.DataFrame(index=datos_modelo["clientes"].copy())
    params_semilla = params_base.copy()
    params_semilla["seed"] = seed
    num_boost_round = int(params_semilla.pop("num_iterations"))

    dtrain_final = lgb.Dataset(
        data=X_train,
        label=datos_modelo["clase01"],
        feature_name=campos_buenos,
        categorical_feature=[],
    )
    modelo_final = lgb.train(
        params=params_semilla,
        train_set=dtrain_final,
        num_boost_round=num_boost_round,
    )
    tb_predicciones["prob"] = modelo_final.predict(X_future)
    if not np.isfinite(tb_predicciones["prob"].to_numpy()).all():
        raise ValueError(f"Modelo {numero_modelo}, semilla {seed}: predicciones no finitas.")
    print(f"Modelo={numero_modelo} Semilla={seed}: predicciones listas")
    del dtrain_final, modelo_final
    return tb_predicciones, datos_modelo["cantidad_total"], datos_modelo["cantidad_train"]

# [Anotación · líneas 292–327] Texto con las instrucciones de la celda de generación y su primera parte:
#   prepara la corrida, obtiene las semillas ya completas y, si quedan semillas pendientes y los datos no están
#   en memoria para esta configuración, prepara los tres modelos uno por uno; corta si los datasets no tienen
#   los mismos clientes en el mes a predecir.
#%% celda 14 [texto]
## Entrenamiento y predicciones

Ejecutar esta celda y dejarla correr. Primero carga y prepara los tres datasets una sola vez; después recorre las semillas y entrena los modelos 1, 2 y 3 para cada una. Las matrices preparadas permanecen en memoria durante toda la generación. No se imprime la tabla de cantidades por mes y clase.

Para detenerla, usar **Interrupt / Interrumpir kernel**; después ejecutar la celda de combinación. Las ternas anteriores quedan guardadas aunque la interrupción ocurra durante un entrenamiento o una escritura.

Al retomar esta celda se saltean las semillas completas y se reutilizan los datos que siguen en memoria. Tras reiniciar el kernel, los datos se cargan nuevamente una sola vez. Si todas las semillas están completas, no se cargan los datasets.

Usar el mismo `nombre_corrida` permite continuar las ternas guardadas con la versión anterior de esta notebook.

#%% celda 15 [código]
configuracion = preparar_corrida()
completas = set(semillas_guardadas(configuracion))

try:
    pendientes = [seed for seed in configuracion["seeds"] if seed not in completas]
    if pendientes and (
        "datos_modelos" not in globals()
        or len(datos_modelos) != 3
        or globals().get("configuracion_en_memoria") != configuracion
    ):
        # Se libera cualquier preparación anterior antes de cargar esta configuración.
        configuracion_en_memoria = None
        datos_modelos = []
        gc.collect()
        for numero_modelo in (1, 2, 3):
            datos_modelo = preparar_modelo(numero_modelo, configuracion)
            if datos_modelos and not datos_modelo["clientes"].sort_values().equals(
                datos_modelos[0]["clientes"].sort_values()
            ):
                raise ValueError("Los datasets tienen distintos clientes para el mes a predecir.")
            datos_modelos.append(datos_modelo)
            del datos_modelo
            gc.collect()
        configuracion_en_memoria = configuracion

# [Anotación · líneas 329–371] Recorre las 50 semillas salteando las completas. Para cada semilla entrena los
#   modelos 1, 2 y 3, verifica que las tres predicciones tengan los mismos clientes, escribe los tres CSV
#   (numero_de_cliente, prob) mediante archivo temporal y renombrado, y luego la marca completa.json con la
#   semilla, las cantidades de filas y los nombres de archivo. Una interrupción de teclado se captura con un
#   mensaje; al final imprime cuántas ternas completas hay en disco.
    for seed in configuracion["seeds"]:
        if seed in completas:
            print(f"Semilla={seed}: terna ya guardada")
            continue

        predicciones_semilla = []
        totales_semilla = []
        entrenamiento_semilla = []
        for numero_modelo in (1, 2, 3):
            predicciones, cantidad_total, cantidad_train = entrenar_modelo(numero_modelo, seed, configuracion)
            if predicciones_semilla and not predicciones.index.sort_values().equals(
                predicciones_semilla[0].index.sort_values()
            ):
                raise ValueError("Los datasets tienen distintos clientes para el mes a predecir.")
            predicciones_semilla.append(predicciones)
            totales_semilla.append(cantidad_total)
            entrenamiento_semilla.append(cantidad_train)
            gc.collect()

        archivos = archivos_semilla(seed)
        archivos[0].parent.mkdir(parents=True, exist_ok=True)
        # La marca se elimina antes de reescribir una terna incompleta.
        marca = archivos[0].parent / "completa.json"
        marca.unlink(missing_ok=True)
        for predicciones, archivo in zip(predicciones_semilla, archivos):
            temporal = archivo.with_name(archivo.name + ".tmp")
            predicciones.reset_index().to_csv(temporal, index=False)
            os.replace(temporal, archivo)
        guardar_json(marca, {
            "seed": seed,
            "cantidad_registros_totales": totales_semilla,
            "cantidad_registros_entrenamiento": entrenamiento_semilla,
            "cantidad_clientes": len(predicciones_semilla[0]),
            "archivos": [archivo.name for archivo in archivos],
        })
        completas.add(seed)
        del predicciones_semilla, predicciones
        gc.collect()
        print(f"Semilla={seed}: terna guardada ({len(completas)} completas)")
except KeyboardInterrupt:
    print("Generación interrumpida. La combinación usará solamente las ternas completas.")
finally:
    print(f"Ternas completas en disco: {len(semillas_guardadas(configuracion))}/{len(configuracion['seeds'])}")

# [Anotación · líneas 373–399] Texto y primera parte de la combinación: relee configuracion.json, corta si no
#   hay ninguna terna completa, lee la marca completa.json de cada semilla y comprueba que corresponda a sus
#   archivos y que todas las semillas registren las mismas cantidades de filas de origen.
#%% celda 16 [texto]
## Combinación por cliente

Esta celda lee las predicciones guardadas. Se puede ejecutar después de interrumpir la generación o cuando terminan las 50 semillas. También funciona tras reiniciar el kernel: ejecutar imports, directorios, parámetros y funciones anteriores, y saltar la celda de entrenamiento.

Cada semilla completa aporta exactamente tres probabilidades por cliente. Se conservan la combinación y el orden de columnas de p004 (modelo y luego semilla). La lectura de los CSV recupera los valores `float64` sin pérdida por redondeo. Si no hay ninguna terna completa, primero hay que generar una.

#%% celda 17 [código]
configuracion = leer_configuracion()
semillas_completas = semillas_guardadas(configuracion)
if not semillas_completas:
    raise ValueError("No hay ternas completas para combinar. Generar al menos una semilla.")

informacion_semillas = []
for seed in semillas_completas:
    marca = carpeta_corrida / f"semilla_{seed}" / "completa.json"
    informacion = json.loads(marca.read_text(encoding="utf-8"))
    if informacion["seed"] != seed or informacion["archivos"] != [a.name for a in archivos_semilla(seed)]:
        raise ValueError(f"Semilla {seed}: la documentación de la terna no corresponde a sus archivos.")
    informacion_semillas.append(informacion)

cantidad_registros_totales = informacion_semillas[0]["cantidad_registros_totales"]
cantidad_registros_entrenamiento = informacion_semillas[0]["cantidad_registros_entrenamiento"]
if any(info["cantidad_registros_totales"] != cantidad_registros_totales
       or info["cantidad_registros_entrenamiento"] != cantidad_registros_entrenamiento
       for info in informacion_semillas):
    raise ValueError("Las ternas tienen distintas cantidades de registros de origen.")

# [Anotación · líneas 401–433] Para cada modelo y cada semilla completa lee el CSV de probabilidades con
#   precisión round_trip, valida columnas, clientes únicos, cantidad de clientes y valores finitos, y exige el
#   mismo conjunto de clientes en todos los archivos. Une las columnas de los tres modelos (3 por cada semilla),
#   calcula el promedio por cliente y ordena de mayor a menor probabilidad.
predicciones_por_modelo = []
clientes_referencia = None
for numero_modelo in (1, 2, 3):
    probabilidades = []
    for seed, informacion in zip(semillas_completas, informacion_semillas):
        archivo = archivos_semilla(seed)[numero_modelo - 1]
        predicciones = pd.read_csv(archivo, float_precision="round_trip")
        if list(predicciones.columns) != ["numero_de_cliente", "prob"]:
            raise ValueError(f"Revisar columnas de {archivo.name}.")
        predicciones = predicciones.set_index("numero_de_cliente")
        if (not predicciones.index.is_unique or predicciones.index.hasnans
                or len(predicciones) != informacion["cantidad_clientes"]
                or not np.isfinite(predicciones["prob"].to_numpy()).all()):
            raise ValueError(f"Revisar clientes o probabilidades de {archivo.name}.")
        clientes = predicciones.index.sort_values()
        if clientes_referencia is None:
            clientes_referencia = clientes
        elif not clientes.equals(clientes_referencia):
            raise ValueError("Los archivos tienen distintos clientes: no se puede promediar con igual cantidad de predicciones.")
        probabilidades.append(predicciones["prob"].rename(f"prob_{seed}"))
    predicciones_por_modelo.append(pd.concat(probabilidades, axis=1))

tb_prediccion = (
    pd.concat(predicciones_por_modelo, axis=1)
    .mean(axis=1)
    .rename("prob")
    .reset_index()
    .sort_values("prob", ascending=False, kind="stable")
    .reset_index(drop=True)
)

print(f"Semillas completas={len(semillas_completas)} Predicciones por cliente={3 * len(semillas_completas)}")
print(f"Clientes={len(tb_prediccion)} Corrida={carpeta_corrida}")

# [Anotación · líneas 435–464] Corte: envios = 12500 en la copia del repositorio. Calcula id_prueba como el
#   máximo de logging_python.csv más 1 (o 1 si el archivo no existe), avanza el número mientras exista un
#   archivo con ese nombre y escribe los primeros `envios` numero_de_cliente, sin encabezado, en la subcarpeta
#   entregas/ como p005_3models_<id_prueba>.csv.
#%% celda 18 [texto]
## Generación del corte

Cambiar `envios` y ejecutar esta celda para generar otro corte sin entrenar de nuevo. Registrar cada generación en la celda de documentación antes de generar la siguiente, para que avance `id_prueba`.

#%% celda 19 [código]
envios = 12500  # cambiar para cada corte

if envios != int(envios) or not 1 <= envios <= len(tb_prediccion):
    raise ValueError("Revisar envios: debe ser un entero entre 1 y la cantidad de clientes.")
envios = int(envios)

if archivo_logging.exists():
    historico = pd.read_csv(archivo_logging)
    id_prueba = int(historico["id_prueba"].max()) + 1
else:
    id_prueba = 1

carpeta_salida.mkdir(parents=True, exist_ok=True)
archivo = f"p005_3models_{id_prueba}.csv"
while (carpeta_salida / archivo).exists():
    id_prueba += 1
    archivo = f"p005_3models_{id_prueba}.csv"
tb_prediccion.head(envios)[["numero_de_cliente"]].to_csv(
    carpeta_salida / archivo,
    header=False,
    index=False,
)
archivos_salida = [archivo]
print(f"Archivo={archivo} Envios={envios}")

# [Anotación · líneas 466–477] Texto de la sección de documentación y datos que se cargan a mano para la
#   bitácora: la nota (termina en 'subimos envios a 13k'), resultado_competencia_mean '106.7000' con el
#   comentario 'completar con el score de Kaggle', desvío 'NA' y referencia de entrega e55_p.
#%% celda 20 [texto]
## Documentación

Se mantiene el formato de `logging_python.csv` de p004. Se registran las semillas efectivamente combinadas, los datasets, RDS, meses y cantidades de filas de la corrida guardada. La nota identifica la carpeta de predicciones y cuántas probabilidades aportó cada cliente.

Completar `ref_submit` y los resultados cuando estén disponibles. Se puede volver a ejecutar la celda de registro para actualizar esa entrega.

#%% celda 21 [código]
nota = "3 modelos igual q antes, pero ahora en el runner con 50 semillas, entrega hecha con 50, subimos envios a 13k"
resultado_competencia_mean = "106.7000"  # completar con el score de Kaggle
resultado_competencia_std = "NA"
ref_submit = "e55_p"  # completar con la referencia de la entrega

# [Anotación · líneas 479–531] Arma una fila con id_prueba, referencia, nombre de notebook, datasets, semillas
#   combinadas, cantidades de filas, meses, columnas excluidas, ids de .rds, envíos, archivo generado, nota y
#   resultados. Si logging_python.csv ya tiene ese id_prueba reemplaza la fila; si no, la agrega al final; si el
#   archivo no existe lo crea. Muestra las últimas 30 filas de la bitácora.
#%% celda 22 [código]
registro_prueba = pd.DataFrame([{
    "id_prueba": id_prueba,
    "ref_submit": ref_submit,
    "notebook": "p005_3models_por_semilla_memoria.ipynb",
    "dataset": ",".join(Path(archivo).stem for archivo in configuracion["dataset_files"]),
    "seeds": ",".join(map(str, semillas_completas)),
    "cantidad_registros_totales": ",".join(map(str, cantidad_registros_totales)),
    "cantidad_registros_entrenamiento": ",".join(map(str, cantidad_registros_entrenamiento)),
    "cantidad_registros_prediccion": len(tb_prediccion),
    "meses_entrenamiento": ",".join(map(str, configuracion["train_final"])),
    "meses_prediccion": ",".join(map(str, configuracion["future"])),
    "columnas_excluidas": ",".join(configuracion["columnas_excluir"]),
    "bajas":"1+2",                                       #baja+1 y baja+2 o solo baja+2
    "id_rds": ",".join(map(str, configuracion["ids_rds"])),
    "envios": envios,
    "archivos": ",".join(archivos_salida),
    "nota": nota,
    "resultado_competencia_mean": resultado_competencia_mean,
    "resultado_competencia_std": resultado_competencia_std
}])

if archivo_logging.exists():
    historico = pd.read_csv(
        archivo_logging,
        dtype={
            "ref_submit": str,
            "id_rds": str,
            "cantidad_registros_totales": str,
            "cantidad_registros_entrenamiento": str,
            "seeds": str,
            "meses_entrenamiento": str,
            "meses_prediccion": str,
            "nota": str,
            "resultado_competencia_mean": str,
            "resultado_competencia_std": str,
        },
    )
    fila = historico["id_prueba"].eq(id_prueba)

    if fila.any():
        historico.loc[fila, registro_prueba.columns] = registro_prueba.to_numpy()
        historico.to_csv(archivo_logging, index=False)
    else:
        registro_prueba.to_csv(archivo_logging, mode="a", header=False, index=False)
else:
    registro_prueba.to_csv(archivo_logging, index=False)

# display(registro_prueba)

#%% celda 23 [código]
# display(pd.read_csv(archivo_logging).tail(15))
display(pd.read_csv(archivo_logging)[['id_prueba','envios','resultado_competencia_mean','resultado_competencia_std', 'ref_submit','dataset','meses_entrenamiento','id_rds','nota']].tail(30))
```

### entregas/dataset/versiones_dataset_1.ipynb

Genera competencia_01_ternaria_lags.csv (clase ternaria más lag 1 y delta 1 de cada variable), el dataset que lee la BO LAG-009. La sección de lags fraccionarios está comentada.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–35] Carga pandas y numpy, importa ternaria desde funciones/ternaria.py y define rutas
#   en el directorio de trabajo: competencia_01_crudo.csv de entrada y competencia_01_ternaria_lags.csv de
#   salida.
#%% celda 1 [texto]
# Libraries

#%% celda 2 [código]
import os
import pandas as pd
import numpy as np

#%% celda 3 [código]
# dispongo la carpeta con funciones e importo ternara. 
from pathlib import Path
import sys
import importlib

# Obtiene la ruta del directorio actual y sube un nivel (.parent)
raiz_proyecto = Path().resolve().parent
# Agrega la ruta al sistema si no está ya incluida
if str(raiz_proyecto) not in sys.path:
  sys.path.append(str(raiz_proyecto))

# Importa tu librería o módulo
from funciones.ternaria import ternaria

#%% celda 4 [texto]
# URLs y Constantes

#%% celda 5 [código]
DATA_FOLDER = os.getcwd()
DATA_CRUDO_URL = os.path.join(DATA_FOLDER, 'competencia_01_crudo.csv')
DATA_TERNARIA_URL = os.path.join(DATA_FOLDER, 'competencia_01_ternaria.csv')
DATA_LAGS_URL = os.path.join(DATA_FOLDER, 'competencia_01_ternaria_lags.csv')
DATA_DICT_URL= os.path.join(DATA_FOLDER, 'data_dict.csv')

SEED = 230047
SEEDS =[230047, 230059, 230063, 230077, 230081]

# [Anotación · líneas 37–65] Lee el archivo crudo, agrega la columna ternaria y muestra las primeras filas. El
#   guardado de competencia_01_ternaria.csv está comentado.
#%% celda 6 [texto]
# LEEMOS DATOS CRUDOS

#%% celda 7 [código]
df_crudo = pd.read_csv(
    DATA_CRUDO_URL,
    dtype={'numero_de_cliente': 'int32', 'foto_mes': 'int32'}
)

#%% celda 8 [código]
df_crudo.head()

#%% celda 9 [texto]
# VERSIONES

#%% celda 10 [texto]
## Agregamos TERNARIA

#%% celda 11 [código]
df_ternaria = ternaria(df_crudo)

#%% celda 12 [código]
df_ternaria.head()

#%% celda 13 [texto]
### GUARDAMOS

#%% celda 14 [código]
# df_ternaria.to_csv(DATA_TERNARIA_URL, index=False)

# [Anotación · líneas 67–112] Copia el dataset, corta si hay más de una fila por cliente y mes, ordena por
#   cliente y mes, crea un índice mensual continuo y define las columnas base: todas menos numero_de_cliente,
#   foto_mes, clase_ternaria y el índice auxiliar (la columna ternaria queda incluida).
#%% celda 15 [texto]
## LAGs

#%% celda 16 [código]
df_trabajo = df_ternaria.copy()

#%% celda 17 [código]
# Debe existir una sola fila por cliente y mes
claves = ["numero_de_cliente", "foto_mes"]

if df_trabajo.duplicated(claves).any():
    raise ValueError("Hay más de una fila para algún cliente y foto_mes")

df_trabajo = (
    df_trabajo
    .sort_values(claves)
    .reset_index(drop=True)
    .copy()
)

#%% celda 18 [código]

# Índice mensual: permite controlar correctamente pasos como 202112 -> 202201
foto_mes_num = pd.to_numeric(df_trabajo["foto_mes"])

anio = foto_mes_num // 100
mes = foto_mes_num % 100

if not mes.between(1, 12).all():
    raise ValueError("foto_mes contiene meses inválidos")

df_trabajo["_mes_idx"] = anio * 12 + mes

# Columnas sobre las que se generan los lags
columnas_excluidas = {
    "numero_de_cliente",
    "foto_mes",
    "clase_ternaria",
    "_mes_idx"
}

columnas_base = [
    columna
    for columna in df_trabajo.columns
    if columna not in columnas_excluidas
]

# [Anotación · líneas 114–141] Para cada columna base toma el valor de la fila anterior del mismo cliente y lo
#   anula cuando esa fila no es exactamente el mes anterior (sufijo _lag1). Para las columnas numéricas calcula
#   la diferencia entre el valor actual y el lag (sufijo _delta1). Une todo y quita el índice auxiliar.
#%% celda 19 [código]

agrupado = df_trabajo.groupby("numero_de_cliente", sort=False)

# Valor de la fila anterior para el mismo cliente
lags = agrupado[columnas_base].shift(1)
mes_anterior = agrupado["_mes_idx"].shift(1)

# Sólo es válido si corresponde exactamente al mes anterior
mes_consecutivo = (df_trabajo["_mes_idx"] - mes_anterior).eq(1)
lags.loc[~mes_consecutivo, :] = np.nan

# Delta únicamente para variables numéricas
columnas_numericas = (
    df_trabajo[columnas_base]
    .select_dtypes(include="number")
    .columns
)

deltas = df_trabajo[columnas_numericas] - lags[columnas_numericas]

lags.columns = [f"{columna}_lag1" for columna in lags.columns]
deltas.columns = [f"{columna}_delta1" for columna in deltas.columns]

df_lags = pd.concat(
    [df_trabajo, lags, deltas],
    axis=1
).drop(columns="_mes_idx")

# [Anotación · líneas 143–157] Muestra filas de control (un cliente y la variable mrentabilidad) y guarda el
#   dataset en competencia_01_ternaria_lags.csv, que es el archivo que lee bo/lag009_replica.ipynb.
#%% celda 20 [código]
df_lags.head(20)

#%% celda 21 [código]
# pd.Series(df_lags.columns)[pd.Series(df_lags.columns).str.contains('mrentabilidad') ]
df_lags.loc[df_lags['numero_de_cliente']==12159858][['foto_mes','mrentabilidad','mrentabilidad_lag1', 'mrentabilidad_delta1']]
# df_lags.loc[df_lags['numero_de_cliente']==12159858][['foto_mes','mcomisiones','mcomisiones_lag1', 'mcomisiones_delta1']]
# df_lags.loc[df_lags['numero_de_cliente']==12159858]

#%% celda 22 [texto]
### GUARDAMOS

#%% celda 23 [código]
# guardamos como csv
df_lags.to_csv(DATA_LAGS_URL, index=False)

# [Anotación · líneas 159–368] Sección de lags fraccionarios completamente comentada: las funciones
#   generar_pesos y agregar_lags_ponderados y el guardado de competencia_01_ternaria_lf_k6_perdida4.csv no se
#   ejecutan.
#%% celda 24 [texto]
## LAGs fracionarios

#%% celda 25 [código]
# df_trabajo = df_ternaria.copy()

#%% celda 26 [código]


# def generar_pesos(K, factor_perdida):
#     """
#     factor_perdida indica qué proporción de importancia se pierde
#     por cada mes adicional hacia atrás.
#     """
#     if K < 1:
#         raise ValueError("K debe ser mayor o igual a 1")

#     if not 0 <= factor_perdida < 1:
#         raise ValueError("factor_perdida debe estar entre 0 y 1")

#     retencion = 1 - factor_perdida
#     pesos = retencion ** np.arange(K, dtype=float)

#     return pesos / pesos.sum()


# def agregar_lags_ponderados(
#     df,
#     K=6,
#     factor_perdida=0.4,
#     columnas=None,
#     tam_bloque=20
# ):
#     df = df.copy()

#     claves = ["numero_de_cliente", "foto_mes"]

#     if df.duplicated(claves).any():
#         raise ValueError("Hay más de una fila para algún cliente y mes")

#     # Convierto YYYYMM a un índice mensual continuo.
#     foto_mes = pd.to_numeric(df["foto_mes"], errors="raise").astype("int64")
#     mes = foto_mes % 100

#     if not mes.between(1, 12).all():
#         raise ValueError("foto_mes contiene meses inválidos")

#     df["_mes_idx"] = (foto_mes // 100) * 12 + mes

#     # El cálculo necesita los registros ordenados cronológicamente.
#     df = (
#         df.sort_values(
#             ["numero_de_cliente", "_mes_idx"],
#             kind="stable"
#         )
#         .reset_index(drop=True)
#     )

#     if columnas is None:
#         excluidas = {
#             "numero_de_cliente",
#             "foto_mes",
#             "clase_ternaria",
#             "_mes_idx"
#         }

#         columnas = [
#             columna
#             for columna in df.select_dtypes(include=np.number).columns
#             if columna not in excluidas
#             and not columna.endswith("_lag_pond")
#             and not columna.endswith("_delta_lag_pond")
#         ]

#     no_numericas = [
#         columna
#         for columna in columnas
#         if not pd.api.types.is_numeric_dtype(df[columna])
#     ]

#     if no_numericas:
#         raise TypeError(
#             f"Las siguientes columnas no son numéricas: {no_numericas}"
#         )

#     pesos = generar_pesos(K, factor_perdida)
#     n_filas = len(df)

#     # Peso correspondiente a cada observación histórica.
#     # Se usa la distancia real entre meses, no simplemente la fila anterior.
#     pesos_por_fila = np.zeros((n_filas, K), dtype=np.float64)

#     grupo_mes = df.groupby(
#         "numero_de_cliente",
#         sort=False
#     )["_mes_idx"]

#     for desplazamiento in range(1, K + 1):
#         mes_anterior = grupo_mes.shift(desplazamiento)
#         distancia = df["_mes_idx"] - mes_anterior

#         valido = distancia.between(1, K)
#         posiciones = distancia.loc[valido].astype(int).to_numpy() - 1

#         pesos_por_fila[
#             valido.to_numpy(),
#             desplazamiento - 1
#         ] = pesos[posiciones]

#     nuevas_columnas = []

#     # Se procesa por bloques para limitar el uso de memoria.
#     for inicio in range(0, len(columnas), tam_bloque):
#         bloque = columnas[inicio:inicio + tam_bloque]

#         numerador = np.zeros((n_filas, len(bloque)), dtype=np.float64)
#         denominador = np.zeros_like(numerador)

#         grupo = df[bloque].groupby(
#             df["numero_de_cliente"],
#             sort=False
#         )

#         for desplazamiento in range(1, K + 1):
#             valores_pasados = grupo.shift(desplazamiento).to_numpy(
#                 dtype=np.float64,
#                 na_value=np.nan
#             )

#             peso = pesos_por_fila[
#                 :, desplazamiento - 1
#             ][:, None]

#             disponible = valores_pasados.notna() if False else ~np.isnan(
#                 valores_pasados
#             )

#             numerador += np.where(
#                 disponible,
#                 valores_pasados * peso,
#                 0.0
#             )

#             denominador += disponible * peso

#         lag_ponderado = np.divide(
#             numerador,
#             denominador,
#             out=np.full_like(numerador, np.nan),
#             where=denominador > 0
#         )

#         valores_actuales = df[bloque].to_numpy(
#             dtype=np.float64,
#             na_value=np.nan
#         )

#         delta_ponderado = valores_actuales - lag_ponderado

#         nuevas_columnas.append(
#             pd.DataFrame(
#                 lag_ponderado,
#                 columns=[f"{c}_lag_pond" for c in bloque]
#             )
#         )

#         nuevas_columnas.append(
#             pd.DataFrame(
#                 delta_ponderado,
#                 columns=[f"{c}_delta_lag_pond" for c in bloque]
#             )
#         )

#     df = pd.concat([df, *nuevas_columnas], axis=1)

#     return df.drop(columns="_mes_idx")

#%% celda 27 [código]
# df_trabajo.shape

#%% celda 28 [código]
# k = 6
# factor_perdida = .4
# print(generar_pesos(3, 0.4))
# df_lags_fraccionarios = agregar_lags_ponderados(
#     df_trabajo,
#     K=k,
#     factor_perdida=factor_perdida
# )

#%% celda 29 [código]
# df_lags_fraccionarios

#%% celda 30 [código]
# df_lags_fraccionarios.columns

#%% celda 31 [código]

# df_lags_fraccionarios.loc[df_lags_fraccionarios['numero_de_cliente']==12159858][['foto_mes','mrentabilidad','mrentabilidad_lag_pond', 'mrentabilidad_delta_lag_pond']]
# # df_lags_fraccionarios.loc[df_lags_fraccionarios['numero_de_cliente']==12159858]

#%% celda 32 [texto]
### GUARDAMOS

#%% celda 33 [código]
# filename = f'competencia_01_ternaria_lf_k{k}_perdida{factor_perdida*10:.0f}.csv'
# df_lags_fraccionarios.to_csv(os.path.join(DATA_FOLDER, filename), index=False)

#%% celda 34 [código]
# df_lags_fraccionarios
```

### entregas/dataset/versiones_dataset_2.ipynb

Genera, a partir de competencia_01_crudo.csv, los tres datasets que lee p005: lags fraccionarios K=6, lags fraccionarios de dos ventanas K=3 y rankings por mes. Contiene además bloques comentados de lags de orden 1 y 2.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–36] Carga pandas y numpy, agrega la carpeta padre al sys.path e importa ternaria y
#   rankear_por_mes desde funciones/ternaria.py. Define las rutas de entrada y salida en el directorio de
#   trabajo (competencia_01_crudo.csv, c_01_tern_2.csv y otros nombres) y dos constantes de semillas que no se
#   usan en el resto de la notebook.
#%% celda 1 [texto]
# Libraries

#%% celda 2 [código]
import os
import pandas as pd
import numpy as np

#%% celda 3 [código]
# dispongo la carpeta con funciones e importo ternara. 
from pathlib import Path
import sys
import importlib

# Obtiene la ruta del directorio actual y sube un nivel (.parent)
raiz_proyecto = Path().resolve().parent
# Agrega la ruta al sistema si no está ya incluida
if str(raiz_proyecto) not in sys.path:
  sys.path.append(str(raiz_proyecto))

# Importa tu librería o módulo
from funciones.ternaria import ternaria, rankear_por_mes

#%% celda 4 [texto]
# URLs y Constantes

#%% celda 5 [código]
DATA_FOLDER = os.getcwd()
DATA_CRUDO_URL = os.path.join(DATA_FOLDER, 'competencia_01_crudo.csv')
DATA_TERNARIA_URL = os.path.join(DATA_FOLDER, 'c_01_tern_2.csv')
DATA_LAGS_URL = os.path.join(DATA_FOLDER, 'c_01_tern_2_lags.csv')
DATA_LAGS_O2_URL = os.path.join(DATA_FOLDER, 'c_01_tern_2_lags_O2.csv')
DATA_DICT_URL= os.path.join(DATA_FOLDER, 'data_dict.csv')

SEED = 230047
SEEDS =[230047, 230059, 230063, 230077, 230081]

# [Anotación · líneas 38–54] Lee competencia_01_crudo.csv con numero_de_cliente y foto_mes como int32 y
#   reemplaza por NaN la variable ccajas_depositos en las filas de foto_mes 202105.
#%% celda 6 [texto]
# LEEMOS DATOS CRUDOS

#%% celda 7 [código]
df_crudo = pd.read_csv(
    DATA_CRUDO_URL,
    dtype={'numero_de_cliente': 'int32', 'foto_mes': 'int32'}
)

#%% celda 8 [código]
df_crudo.head()

#%% celda 9 [texto]
## "IMPUTAMOS" CCAJAS_DEPOSITOS con NA para 202105

#%% celda 10 [código]
df_crudo.loc[df_crudo['foto_mes']==202105, 'ccajas_depositos'] = np.nan

# [Anotación · líneas 56–72] Agrega la columna ternaria con la función ternaria() y guarda el resultado en
#   c_01_tern_2.csv.
#%% celda 11 [texto]
# VERSIONES

#%% celda 12 [texto]
## Agregamos TERNARIA

#%% celda 13 [código]
df_ternaria = ternaria(df_crudo)

#%% celda 14 [código]
df_ternaria.head()

#%% celda 15 [texto]
### GUARDAMOS

#%% celda 16 [código]
df_ternaria.to_csv(DATA_TERNARIA_URL, index=False)

# [Anotación · líneas 74–165] Bloque de lag 1 y delta 1 (el mismo cálculo de versiones_dataset_1.ipynb)
#   completamente comentado: no se ejecuta ni se guarda c_01_tern_2_lags.csv.
#%% celda 17 [texto]
## LAGs

#%% celda 18 [código]
# df_trabajo = df_ternaria.copy()

#%% celda 19 [código]
# # Debe existir una sola fila por cliente y mes
# claves = ["numero_de_cliente", "foto_mes"]

# if df_trabajo.duplicated(claves).any():
#     raise ValueError("Hay más de una fila para algún cliente y foto_mes")

# df_trabajo = (
#     df_trabajo
#     .sort_values(claves)
#     .reset_index(drop=True)
#     .copy()
# )

#%% celda 20 [código]

# # Índice mensual: permite controlar correctamente pasos como 202112 -> 202201
# foto_mes_num = pd.to_numeric(df_trabajo["foto_mes"])

# anio = foto_mes_num // 100
# mes = foto_mes_num % 100

# if not mes.between(1, 12).all():
#     raise ValueError("foto_mes contiene meses inválidos")

# df_trabajo["_mes_idx"] = anio * 12 + mes

# # Columnas sobre las que se generan los lags
# columnas_excluidas = {
#     "numero_de_cliente",
#     "foto_mes",
#     "clase_ternaria",
#     "ternaria",
#     "_mes_idx"
# }

# columnas_base = [
#     columna
#     for columna in df_trabajo.columns
#     if columna not in columnas_excluidas
# ]

#%% celda 21 [código]

# agrupado = df_trabajo.groupby("numero_de_cliente", sort=False)

# # Valor de la fila anterior para el mismo cliente
# lags = agrupado[columnas_base].shift(1)
# mes_anterior = agrupado["_mes_idx"].shift(1)

# # Sólo es válido si corresponde exactamente al mes anterior
# mes_consecutivo = (df_trabajo["_mes_idx"] - mes_anterior).eq(1)
# lags.loc[~mes_consecutivo, :] = np.nan

# # Delta únicamente para variables numéricas
# columnas_numericas = (
#     df_trabajo[columnas_base]
#     .select_dtypes(include="number")
#     .columns
# )

# deltas = df_trabajo[columnas_numericas] - lags[columnas_numericas]

# lags.columns = [f"{columna}_lag1" for columna in lags.columns]
# deltas.columns = [f"{columna}_delta1" for columna in deltas.columns]

# df_lags = pd.concat(
#     [df_trabajo, lags, deltas],
#     axis=1
# ).drop(columns="_mes_idx")

#%% celda 22 [código]
# df_lags.head(20)

#%% celda 23 [código]
# pd.Series(df_lags.columns)[pd.Series(df_lags.columns).str.contains('mrentabilidad') ]
# df_lags.loc[df_lags['numero_de_cliente']==12159858][['foto_mes','mrentabilidad','mrentabilidad_lag1', 'mrentabilidad_delta1']]
# df_lags.loc[df_lags['numero_de_cliente']==12159858][['foto_mes','mcomisiones','mcomisiones_lag1', 'mcomisiones_delta1']]
# df_lags.loc[df_lags['numero_de_cliente']==12159858]

#%% celda 24 [texto]
### GUARDAMOS

#%% celda 25 [código]
# guardamos como csv
# df_lags.to_csv(DATA_LAGS_URL, index=False)

# [Anotación · líneas 167–190] Copia el dataset con ternaria y define generar_pesos: devuelve K pesos (1 -
#   factor_perdida)^k, con k de 0 a K-1, divididos por su suma; el primero corresponde al mes inmediatamente
#   anterior.
#%% celda 26 [texto]
## LAGs fracionarios

#%% celda 27 [código]
df_trabajo = df_ternaria.copy()

#%% celda 28 [código]


def generar_pesos(K, factor_perdida):
    """
    factor_perdida indica qué proporción de importancia se pierde
    por cada mes adicional hacia atrás.
    """
    if K < 1:
        raise ValueError("K debe ser mayor o igual a 1")

    if not 0 <= factor_perdida < 1:
        raise ValueError("factor_perdida debe estar entre 0 y 1")

    retencion = 1 - factor_perdida
    pesos = retencion ** np.arange(K, dtype=float)

    return pesos / pesos.sum()


# [Anotación · líneas 193–250] agregar_lags_ponderados, primera parte: corta si hay más de una fila por
#   cliente y mes, convierte foto_mes en un índice mensual continuo, ordena por cliente y mes y elige las
#   columnas a procesar: todas las numéricas salvo numero_de_cliente, foto_mes, clase_ternaria y las que ya
#   terminan en _lag_pond o _delta_lag_pond.
def agregar_lags_ponderados(
    df,
    K=6,
    factor_perdida=0.4,
    columnas=None,
    tam_bloque=20
):
    df = df.copy()

    claves = ["numero_de_cliente", "foto_mes"]

    if df.duplicated(claves).any():
        raise ValueError("Hay más de una fila para algún cliente y mes")

    # Convierto YYYYMM a un índice mensual continuo.
    foto_mes = pd.to_numeric(df["foto_mes"], errors="raise").astype("int64")
    mes = foto_mes % 100

    if not mes.between(1, 12).all():
        raise ValueError("foto_mes contiene meses inválidos")

    df["_mes_idx"] = (foto_mes // 100) * 12 + mes

    # El cálculo necesita los registros ordenados cronológicamente.
    df = (
        df.sort_values(
            ["numero_de_cliente", "_mes_idx"],
            kind="stable"
        )
        .reset_index(drop=True)
    )

    if columnas is None:
        excluidas = {
            "numero_de_cliente",
            "foto_mes",
            "clase_ternaria",
            "_mes_idx"
        }

        columnas = [
            columna
            for columna in df.select_dtypes(include=np.number).columns
            if columna not in excluidas
            and not columna.endswith("_lag_pond")
            and not columna.endswith("_delta_lag_pond")
        ]

    no_numericas = [
        columna
        for columna in columnas
        if not pd.api.types.is_numeric_dtype(df[columna])
    ]

    if no_numericas:
        raise TypeError(
            f"Las siguientes columnas no son numéricas: {no_numericas}"
        )

# [Anotación · líneas 252–274] Calcula, para cada fila y cada desplazamiento de 1 a K filas hacia atrás dentro
#   del cliente, la distancia real en meses con esa fila; si la distancia está entre 1 y K le asigna el peso
#   correspondiente a esa distancia y, si no, peso 0.
    pesos = generar_pesos(K, factor_perdida)
    n_filas = len(df)

    # Peso correspondiente a cada observación histórica.
    # Se usa la distancia real entre meses, no simplemente la fila anterior.
    pesos_por_fila = np.zeros((n_filas, K), dtype=np.float64)

    grupo_mes = df.groupby(
        "numero_de_cliente",
        sort=False
    )["_mes_idx"]

    for desplazamiento in range(1, K + 1):
        mes_anterior = grupo_mes.shift(desplazamiento)
        distancia = df["_mes_idx"] - mes_anterior

        valido = distancia.between(1, K)
        posiciones = distancia.loc[valido].astype(int).to_numpy() - 1

        pesos_por_fila[
            valido.to_numpy(),
            desplazamiento - 1
        ] = pesos[posiciones]

# [Anotación · líneas 276–342] En bloques de 20 columnas acumula el numerador (valor pasado por peso) y el
#   denominador (suma de pesos de los valores presentes) y obtiene el promedio ponderado de los meses anteriores
#   (sufijo _lag_pond), que queda en NaN cuando no hay ningún valor pasado. Calcula además la diferencia entre
#   el valor actual y ese promedio (sufijo _delta_lag_pond) y agrega todas las columnas nuevas al dataset.
    nuevas_columnas = []

    # Se procesa por bloques para limitar el uso de memoria.
    for inicio in range(0, len(columnas), tam_bloque):
        bloque = columnas[inicio:inicio + tam_bloque]

        numerador = np.zeros((n_filas, len(bloque)), dtype=np.float64)
        denominador = np.zeros_like(numerador)

        grupo = df[bloque].groupby(
            df["numero_de_cliente"],
            sort=False
        )

        for desplazamiento in range(1, K + 1):
            valores_pasados = grupo.shift(desplazamiento).to_numpy(
                dtype=np.float64,
                na_value=np.nan
            )

            peso = pesos_por_fila[
                :, desplazamiento - 1
            ][:, None]

            disponible = valores_pasados.notna() if False else ~np.isnan(
                valores_pasados
            )

            numerador += np.where(
                disponible,
                valores_pasados * peso,
                0.0
            )

            denominador += disponible * peso

        lag_ponderado = np.divide(
            numerador,
            denominador,
            out=np.full_like(numerador, np.nan),
            where=denominador > 0
        )

        valores_actuales = df[bloque].to_numpy(
            dtype=np.float64,
            na_value=np.nan
        )

        delta_ponderado = valores_actuales - lag_ponderado

        nuevas_columnas.append(
            pd.DataFrame(
                lag_ponderado,
                columns=[f"{c}_lag_pond" for c in bloque]
            )
        )

        nuevas_columnas.append(
            pd.DataFrame(
                delta_ponderado,
                columns=[f"{c}_delta_lag_pond" for c in bloque]
            )
        )

    df = pd.concat([df, *nuevas_columnas], axis=1)

    return df.drop(columns="_mes_idx")

# [Anotación · líneas 344–379] Ejecuta la función con K = 6 y factor_perdida = 0,4, imprime ejemplos de pesos
#   y dimensiones, y guarda el resultado en c_01_tern_2_lf_k6_p4.csv (dataset del modelo 1 en p005).
#%% celda 29 [código]
df_trabajo.shape

#%% celda 30 [código]
k = 6
factor_perdida = .4
print(generar_pesos(3, 0.4))
df_lags_fraccionarios = agregar_lags_ponderados(
    df_trabajo,
    K=k,
    factor_perdida=factor_perdida
)

#%% celda 31 [código]
print(generar_pesos(3, 0.7))
print(generar_pesos(3, 0.7))
print(generar_pesos(6, 0.7))

#%% celda 32 [código]
df_lags_fraccionarios.columns

#%% celda 33 [código]
df_lags_fraccionarios.shape

#%% celda 34 [texto]
### GUARDAMOS

#%% celda 35 [código]
pd.Series(df_lags_fraccionarios.columns).loc[pd.Series(df_lags_fraccionarios.columns).str.contains('tern')]

#%% celda 36 [código]
filename = f'c_01_tern_2_lf_k{k}_p{factor_perdida*10:.0f}.csv'
df_lags_fraccionarios.to_csv(os.path.join(DATA_FOLDER, filename), index=False)

#%% celda 37 [código]
df_lags_fraccionarios

# [Anotación · líneas 381–487] Define agregar_lags_2: lag y delta de orden 1 y 2 de cada variable, válidos
#   sólo cuando la fila tomada está exactamente 1 o 2 meses atrás, con recuperación del valor de dos meses atrás
#   cuando falta el mes intermedio. Las celdas que la llaman y guardan c_01_tern_2_lags_O2.csv están comentadas.
#%% celda 38 [texto]
## LAGS ORDEN 2

#%% celda 39 [código]
def agregar_lags_2(df_ternaria):
    df_trabajo = df_ternaria.copy()

    # Debe existir una sola fila por cliente y mes
    claves = ["numero_de_cliente", "foto_mes"]

    if df_trabajo.duplicated(claves).any():
        raise ValueError("Hay más de una fila para algún cliente y foto_mes")

    df_trabajo = (
        df_trabajo
        .sort_values(claves)
        .reset_index(drop=True)
        .copy()
    )

    # Índice mensual: controla pasos como 202112 -> 202201
    foto_mes_num = pd.to_numeric(df_trabajo["foto_mes"])
    anio = foto_mes_num // 100
    mes = foto_mes_num % 100

    if not mes.between(1, 12).all():
        raise ValueError("foto_mes contiene meses inválidos")

    df_trabajo["_mes_idx"] = anio * 12 + mes

    columnas_excluidas = {
        "numero_de_cliente",
        "foto_mes",
        "clase_ternaria",
        "ternaria",
        "_mes_idx"
    }

    columnas_base = [
        columna
        for columna in df_trabajo.columns
        if columna not in columnas_excluidas
    ]

    agrupado = df_trabajo.groupby("numero_de_cliente", sort=False)

    # Delta únicamente para variables numéricas
    columnas_numericas = (
        df_trabajo[columnas_base]
        .select_dtypes(include="number")
        .columns
    )

    nuevas_columnas = []

    for periodo in (1, 2):
        lags = agrupado[columnas_base].shift(periodo)
        mes_anterior = agrupado["_mes_idx"].shift(periodo)

        mes_consecutivo = (
            df_trabajo["_mes_idx"] - mes_anterior
        ).eq(periodo)
        lags.loc[~mes_consecutivo, :] = np.nan

        # Para lag2, recupero t-2 también cuando falta t-1
        if periodo == 2:
            mes_anterior = agrupado["_mes_idx"].shift(1)
            falta_mes_intermedio = (
                df_trabajo["_mes_idx"] - mes_anterior
            ).eq(2)

            lags.loc[falta_mes_intermedio, :] = (
                agrupado[columnas_base].shift(1)
                .loc[falta_mes_intermedio, :]
            )

        deltas = df_trabajo[columnas_numericas] - lags[columnas_numericas]

        lags.columns = [
            f"{columna}_lag{periodo}" for columna in lags.columns
        ]
        deltas.columns = [
            f"{columna}_delta{periodo}" for columna in deltas.columns
        ]

        nuevas_columnas.extend([lags, deltas])

    return pd.concat(
        [df_trabajo, *nuevas_columnas],
        axis=1
    ).drop(columns="_mes_idx")

#%% celda 40 [código]
# df_lags_o2 = agregar_lags_2(df_ternaria)

#%% celda 41 [código]
# df_lags_o2.shape

#%% celda 42 [código]
# pd.Series(df_lags_o2.columns).loc[pd.Series(df_lags_o2.columns).str.contains('tern')]

#%% celda 43 [código]
# df_lags_o2.loc[df_lags_o2['numero_de_cliente']==12159858][['foto_mes','mrentabilidad','mrentabilidad_lag1','mrentabilidad_lag2', 'mrentabilidad_delta1','mrentabilidad_delta2']]
# # df_lags.loc[df_lags['numero_de_cliente']==12159858][['foto_mes','mcomisiones','mcomisiones_lag1', 'mcomisiones_delta1']]

#%% celda 44 [código]
# df_lags_o2.to_csv(DATA_LAGS_O2_URL, index=False)

# [Anotación · líneas 489–557] agregar_lags_ponderados_2, primera parte: mismas validaciones, índice mensual y
#   orden que la función anterior; la selección de columnas excluye también ternaria y los sufijos _lag_pond2 y
#   _delta_lag_pond2. Obtiene los K pesos.
#%% celda 45 [texto]
## LAGs Fraccionarios orden 2

#%% celda 46 [código]
def agregar_lags_ponderados_2(
    df,
    K=6,
    factor_perdida=0.4,
    columnas=None,
    tam_bloque=20
):
    df = df.copy()

    claves = ["numero_de_cliente", "foto_mes"]

    if df.duplicated(claves).any():
        raise ValueError("Hay más de una fila para algún cliente y mes")

    # Convierto YYYYMM a un índice mensual continuo.
    foto_mes = pd.to_numeric(df["foto_mes"], errors="raise").astype("int64")
    mes = foto_mes % 100

    if not mes.between(1, 12).all():
        raise ValueError("foto_mes contiene meses inválidos")

    df["_mes_idx"] = (foto_mes // 100) * 12 + mes

    # El cálculo necesita los registros ordenados cronológicamente.
    df = (
        df.sort_values(
            ["numero_de_cliente", "_mes_idx"],
            kind="stable"
        )
        .reset_index(drop=True)
    )

    if columnas is None:
        excluidas = {
            "numero_de_cliente",
            "foto_mes",
            "clase_ternaria",
            "ternaria",
            "_mes_idx"
        }

        columnas = [
            columna
            for columna in df.select_dtypes(include=np.number).columns
            if columna not in excluidas
            and not columna.endswith("_lag_pond")
            and not columna.endswith("_delta_lag_pond")
            and not columna.endswith("_lag_pond2")
            and not columna.endswith("_delta_lag_pond2")
        ]

    no_numericas = [
        columna
        for columna in columnas
        if not pd.api.types.is_numeric_dtype(df[columna])
    ]

    if no_numericas:
        raise TypeError(
            f"Las siguientes columnas no son numéricas: {no_numericas}"
        )

    pesos = generar_pesos(K, factor_perdida)
    n_filas = len(df)
    nuevas_columnas = []

# [Anotación · líneas 559–652] Repite el cálculo para dos ventanas: la primera toma los meses a distancia 1 a
#   K (columnas _lag_pond y _delta_lag_pond) y la segunda los meses a distancia 2 a K+1 (columnas _lag_pond2 y
#   _delta_lag_pond2), con los mismos K pesos aplicados desde el inicio de cada ventana. El cálculo por bloques
#   de 20 columnas es el de la función anterior.
    for inicio_lag in (1, 2):
        # Conservo los nombres actuales para la primera ventana.
        sufijo = "" if inicio_lag == 1 else "2"

        # Se usa la distancia real entre meses.
        pesos_por_fila = np.zeros(
            (n_filas, K + inicio_lag - 1),
            dtype=np.float64
        )

        grupo_mes = df.groupby(
            "numero_de_cliente",
            sort=False
        )["_mes_idx"]

        for desplazamiento in range(1, K + inicio_lag):
            mes_anterior = grupo_mes.shift(desplazamiento)
            distancia = df["_mes_idx"] - mes_anterior

            valido = distancia.between(inicio_lag, K + inicio_lag - 1)
            posiciones = (
                distancia.loc[valido].astype(int).to_numpy() - inicio_lag
            )

            pesos_por_fila[
                valido.to_numpy(),
                desplazamiento - 1
            ] = pesos[posiciones]

        # Se procesa por bloques para limitar el uso de memoria.
        for inicio in range(0, len(columnas), tam_bloque):
            bloque = columnas[inicio:inicio + tam_bloque]

            numerador = np.zeros((n_filas, len(bloque)), dtype=np.float64)
            denominador = np.zeros_like(numerador)

            grupo = df[bloque].groupby(
                df["numero_de_cliente"],
                sort=False
            )

            for desplazamiento in range(1, K + inicio_lag):
                valores_pasados = grupo.shift(desplazamiento).to_numpy(
                    dtype=np.float64,
                    na_value=np.nan
                )

                peso = pesos_por_fila[
                    :, desplazamiento - 1
                ][:, None]

                disponible = valores_pasados.notna() if False else ~np.isnan(
                    valores_pasados
                )

                numerador += np.where(
                    disponible,
                    valores_pasados * peso,
                    0.0
                )

                denominador += disponible * peso

            lag_ponderado = np.divide(
                numerador,
                denominador,
                out=np.full_like(numerador, np.nan),
                where=denominador > 0
            )

            valores_actuales = df[bloque].to_numpy(
                dtype=np.float64,
                na_value=np.nan
            )

            delta_ponderado = valores_actuales - lag_ponderado

            nuevas_columnas.append(
                pd.DataFrame(
                    lag_ponderado,
                    columns=[f"{c}_lag_pond{sufijo}" for c in bloque]
                )
            )

            nuevas_columnas.append(
                pd.DataFrame(
                    delta_ponderado,
                    columns=[f"{c}_delta_lag_pond{sufijo}" for c in bloque]
                )
            )

    df = pd.concat([df, *nuevas_columnas], axis=1)

    return df.drop(columns="_mes_idx")

# [Anotación · líneas 654–674] Ejecuta la función sobre el dataset con ternaria con K = 3 y factor_perdida =
#   0,6 y guarda c_01_tern_2_lf_O2_k3_p6.csv (dataset del modelo 2 en p005).
#%% celda 47 [código]
k2 = 3
factor_perdida_2 = 0.6

#%% celda 48 [código]

df_lags_fraccionarios_2 = agregar_lags_ponderados_2(
    df_ternaria,
    K=k2,
    factor_perdida=factor_perdida_2
)

#%% celda 49 [código]
# pd.Series(df_lags_fraccionarios_2.columns).loc[pd.Series(df_lags_fraccionarios_2.columns).str.contains('tern')]

#%% celda 50 [código]
filename = f'c_01_tern_2_lf_O2_k{k2}_p{factor_perdida_2*10:.0f}.csv'
df_lags_fraccionarios_2.to_csv(os.path.join(DATA_FOLDER, filename), index=False)

#%% celda 51 [código]
df_lags_fraccionarios_2.shape

# [Anotación · líneas 676–704] Aplica rankear_por_mes al dataset de la primera función (K = 6, factor 0,4),
#   dejando sin transformar numero_de_cliente, foto_mes y ternaria, con escala 'comun' y empates 'average'.
#   Muestra controles de dimensiones y de máximos y guarda RANKS_LF_O2_K6_P4.csv (dataset del modelo 3 en p005).
#%% celda 52 [texto]
## RANKING a LAG FRACCIONARIOS ORDEN 1

#%% celda 53 [código]
df_lags_fraccionarios.columns

#%% celda 54 [código]
pd.Series(df_lags_fraccionarios.columns).loc[pd.Series(df_lags_fraccionarios.columns).str.contains('tern')]

#%% celda 55 [código]
columnas_no_rankear =['numero_de_cliente','foto_mes','ternaria']
df_lags_fracc_ranking_comun_average = rankear_por_mes(df_lags_fraccionarios,columnas_excluidas=columnas_no_rankear, escala="comun", empates="average" )

#%% celda 56 [código]
df_lags_fraccionarios.shape, df_lags_fracc_ranking_comun_average.shape

#%% celda 57 [código]
df_lags_fracc_ranking_comun_average[[column for column in df_lags_fracc_ranking_comun_average.columns if column not in columnas_no_rankear]].max().sum()
pd.Series(df_lags_fracc_ranking_comun_average[[column for column in df_lags_fracc_ranking_comun_average.columns if column not in columnas_no_rankear]].max())[df_lags_fracc_ranking_comun_average[[column for column in df_lags_fracc_ranking_comun_average.columns if column not in columnas_no_rankear]].max()<1]

#%% celda 58 [código]
df_lags_fracc_ranking_comun_average.Visa_mpagosdolares_delta_lag_pond.max(),df_lags_fracc_ranking_comun_average.Visa_mpagosdolares_delta_lag_pond.min()

#%% celda 59 [texto]
### GUARDAMOS

#%% celda 60 [código]
filename = f'RANKS_LF_O2_K{k}_P{factor_perdida*10:.0f}.csv'
df_lags_fracc_ranking_comun_average.to_csv(os.path.join(DATA_FOLDER, filename), index=False)

# [Anotación · líneas 706–721] Bloque comentado: ranking del dataset de lags de orden 2 y guardado de
#   RANKS_LAGS_O2.csv.
#%% celda 61 [texto]
## RANKING a LAGS NORMALES ORDEN 2

#%% celda 62 [código]
# columnas_no_rankear =['numero_de_cliente','foto_mes','ternaria']
# df_lags_o2_ranking_comun_average = rankear_por_mes(df_lags_o2,columnas_excluidas=columnas_no_rankear, escala="comun", empates="average" )

#%% celda 63 [código]
# df_lags_o2.shape, df_lags_o2_ranking_comun_average.shape

#%% celda 64 [texto]
### GUARDAMOS

#%% celda 65 [código]
# filename = f'RANKS_LAGS_O2.csv'
# df_lags_o2_ranking_comun_average.to_csv(os.path.join(DATA_FOLDER, filename), index=False)
```

### entregas/funciones/ternaria.py

Módulo con las dos funciones que usan las notebooks de dataset: ternaria() calcula la clase por presencia del cliente en los meses siguientes y rankear_por_mes() reemplaza variables por su ranking mensual con signo.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–4] Importa cudf, cupy, numpy y pandas; de cupy se usa cp.int8 en la tabla de
#   presencia.
import cudf
import cupy as cp
import numpy as np
import pandas as pd


# [Anotación · líneas 7–34] ternaria(): crea un índice mensual continuo, arma la tabla de presencia (una fila
#   por cliente y mes) y, desplazando ese índice 1 y 2 meses, la une dos veces al dataset para saber si cada
#   cliente está presente en el mes siguiente (tiene_t1) y en el subsiguiente (tiene_t2).
def ternaria(df):
    # Índice de mes continuo para cada fila.
    year = df['foto_mes'] // 100
    month = df['foto_mes'] % 100
    df['mes_idx'] = year * 12 + month

    # Tabla de existencia: una fila por cliente y mes.
    presencia = (
        df[['numero_de_cliente', 'mes_idx']]
        .drop_duplicates()
        .assign(presente=cp.int8(1))
    )

    # Presencia en t+1: desplazamos la clave para que coincida con el mes actual t.
    presencia_t1 = presencia.rename(columns={'mes_idx': 'mes_idx_t1', 'presente': 'presente_t1'})
    presencia_t1['mes_idx'] = presencia_t1['mes_idx_t1'] - 1
    presencia_t1 = presencia_t1[['numero_de_cliente', 'mes_idx', 'presente_t1']]

    # Presencia en t+2.
    presencia_t2 = presencia.rename(columns={'mes_idx': 'mes_idx_t2', 'presente': 'presente_t2'})
    presencia_t2['mes_idx'] = presencia_t2['mes_idx_t2'] - 2
    presencia_t2 = presencia_t2[['numero_de_cliente', 'mes_idx', 'presente_t2']]

    df = df.merge(presencia_t1, on=['numero_de_cliente', 'mes_idx'], how='left')
    df = df.merge(presencia_t2, on=['numero_de_cliente', 'mes_idx'], how='left')

    tiene_t1 = df['presente_t1'].fillna(0).astype('bool')
    tiene_t2 = df['presente_t2'].fillna(0).astype('bool')

# [Anotación · líneas 36–53] Asigna la clase: en los meses anteriores al penúltimo, BAJA+1 si el cliente no
#   está en el mes siguiente, BAJA+2 si está en el siguiente pero no en el subsiguiente y 'continua' (en
#   minúsculas) si está en ambos. En el penúltimo mes sólo marca BAJA+1 a quien no está en el último; el resto
#   de ese mes y todo el último mes quedan sin clase. Quita las columnas auxiliares.
    # Último mes observado del dataset: no tiene horizonte futuro verificable.
    ultimo_mes_idx = int(df['mes_idx'].max())

    # df['ternaria'] = cudf.Series(None, index=df.index, dtype='str')
    df['ternaria'] = pd.Series(None, index=df.index, dtype='str')
    df.loc[df['mes_idx'] < ultimo_mes_idx - 1, 'ternaria'] = 'BAJA+1'
    df.loc[(df['mes_idx'] < ultimo_mes_idx - 1) & tiene_t1, 'ternaria'] = 'BAJA+2'
    df.loc[(df['mes_idx'] < ultimo_mes_idx - 1) & tiene_t1 & tiene_t2, 'ternaria'] = 'continua'

    # Penúltimo mes: sólo puede determinarse baja+1; si continúa queda sin clase.
    df.loc[(df['mes_idx'] == ultimo_mes_idx - 1) & ~tiene_t1, 'ternaria'] = 'BAJA+1'

    # Quitamos columnas auxiliares.
    df = df.drop(columns=['mes_idx', 'presente_t1', 'presente_t2'])
    # Nulos en vez de NAN en CUDF
    df.loc[df["ternaria"] == "", "ternaria"] = None

    return df

# [Anotación · líneas 55–84] rankear_por_mes(): documentación de los argumentos (columnas excluidas, escala
#   'comun' o 'separada', empates 'dense' o 'average') y selección de las columnas a transformar, sobre una
#   copia del dataset.
def rankear_por_mes(
    df,
    columnas_excluidas,
    escala="comun",
    empates="dense"
):
    """
    Reemplaza las variables por rankings calculados por columna y foto_mes.

    df: dataframe de entrada, con registros cliente/mes.
    columnas_excluidas: columnas que permanecen sin modificaciones.
    escala:
        "comun": mismo paso para positivos y negativos; máximo absoluto = 1.
        "separada": cada signo se normaliza por separado hasta +1 o -1.
    empates:
        "dense": valores iguales comparten rango; el siguiente es consecutivo.
        "average": valores iguales reciben el promedio de sus posiciones.

    Conserva los ceros como 0, los NaN como NaN y el signo de los demás valores.
    Un grupo constante no nulo queda en +1 o -1 según su signo.
    Devuelve una copia, conservando columnas, índice y orden de las filas.
    """
    df = df.copy()
    meses = df["foto_mes"].copy()

    columnas = [
        columna
        for columna in df.columns
        if columna not in columnas_excluidas
    ]

# [Anotación · líneas 86–121] Para cada columna y dentro de cada foto_mes rankea por separado los valores
#   positivos y el valor absoluto de los negativos. Con escala 'comun' divide ambos rankings por el mayor de los
#   dos máximos del mes; con 'separada', cada uno por su propio máximo. El resultado queda entre -1 y 1 con el
#   signo original, los ceros en 0 y los NaN sin cambio.
    for columna in columnas:
        valores = df[columna]

        ranking_positivo = (
            valores.where(valores > 0)
            .groupby(meses, sort=False)
            .rank(method=empates)
        )
        ranking_negativo = (
            (-valores.where(valores < 0))
            .groupby(meses, sort=False)
            .rank(method=empates)
        )

        maximo_positivo = (
            ranking_positivo.groupby(meses, sort=False).transform("max")
        )
        maximo_negativo = (
            ranking_negativo.groupby(meses, sort=False).transform("max")
        )

        if escala == "comun":
            maximo = pd.concat(
                [maximo_positivo, maximo_negativo], axis=1
            ).max(axis=1)
            maximo_positivo = maximo
            maximo_negativo = maximo
        elif escala != "separada":
            raise ValueError('escala debe ser "comun" o "separada"')

        ranking = (ranking_positivo / maximo_positivo).fillna(
            -ranking_negativo / maximo_negativo
        )
        df[columna] = ranking.mask(valores.eq(0).fillna(False), 0.0)

    return df
```

### entregas/bo/validacion_multisemilla_lag009_replica.ipynb

Réplica en R del benchmark multisemilla de LAG-009: reentrena los juegos de hiperparámetros de mayor métrica de la BO con varias semillas y mide la ganancia en el mes futuro para una lista de cortes.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–32] Presentación de la notebook (réplica del benchmark multisemilla de LAG-009; genera
#   sólo PARAM.rds y mejor_corte_por_modelo.tsv) y carga de data.table, here, primes y lightgbm.
#%% celda 1 [texto]
# Réplica de la validación multisemilla de LAG-009

Esta notebook conserva la evaluación multisemilla y la selección de los mejores cortes:

1. carga el dataset y genera `ternaria`;
2. lee el `BO_log.txt` de cada experimento configurado;
3. selecciona los mejores `n` conjuntos de hiperparámetros;
4. entrena cada conjunto con las `m` semillas del benchmark original;
5. calcula las ganancias de cada corte y elige el mejor corte de cada modelo.

Genera únicamente los dos archivos utilizados por la validación manual para construir el `.rds`:

- `PARAM.rds`: configuración del benchmark, parámetros fijos y undersampling;
- `mejor_corte_por_modelo.tsv`: hiperparámetros y métricas del mejor corte de cada modelo.

La evaluación detallada y los promedios por corte se conservan en memoria para realizar la selección. No ejecuta una nueva optimización bayesiana.

Para LAG-009, la BO utiliza `competencia_01_ternaria_lags.csv`, mientras que este benchmark utiliza el dataset documentado en su `PARAM.rds`. Se conservan las 16 exclusiones históricas de su validación.

#%% celda 2 [texto]
## Librerías

Si falta algún paquete, instalarlo previamente en el entorno de R correspondiente.

#%% celda 3 [código]
library(data.table)
library(here)
library(primes)
library(lightgbm)

options(scipen = 999)

# [Anotación · líneas 34–74] Texto de configuración y lectura de la configuración original: carpetas relativas
#   a entregas/bo, benchmark de origen benchmark_multisemilla_lags20260924_114539 y carpeta de salida con sufijo
#   -REPLICA (corta si ya existe). Lee PARAM.rds del benchmark original, exige 12 campos (dataset, archivo de
#   resultados, semilla primigenia, n_mejores, m_semillas, train_final, future, semilla_kaggle, cortes,
#   trainingstrategy, lgbm y semillas) y toma de ahí el nombre del dataset.
#%% celda 4 [texto]
## Configuración

Ejecutar desde `entregas/bo`, con kernel R. El dataset se toma de `../dataset`.

`benchmark_original` identifica la carpeta cuya documentación define la configuración a reproducir. Del `PARAM.rds` se recuperan los parámetros de entrada y las semillas de entrenamiento documentadas.

El nombre de la BO se configura en `PARAM$experimentos_origen`, como en la notebook original. Debe coincidir con la carpeta del experimento que se quiere evaluar, dentro de `entregas/bo`.

El dataset, los meses, los cortes, las cantidades y los parámetros fijos pertenecen al benchmark multisemilla. Los modelos y sus hiperparámetros se seleccionan desde el `BO_log.txt` de la BO indicada.

La notebook conserva la generación original de semillas y comprueba que coincidan exactamente con las documentadas antes de continuar. Después vuelve a entrenar y calcular toda la validación con el código original.

#%% celda 5 [código]
# Ejecutar desde entregas/bo.
root <- getwd()
exp_folder <- root
data_folder <- file.path(dirname(root), "dataset")

benchmark_original <- "benchmark_multisemilla_lags20260924_114539"
benchmark_replica <- "benchmark_multisemilla_lags20260924_114539-REPLICA"
carpeta_salida <- file.path(exp_folder, benchmark_replica)

if (dir.exists(carpeta_salida)) {
  stop("La carpeta de salida ya existe: ", carpeta_salida)
}

# Recupera la configuración y las semillas documentadas del benchmark.
configuracion_original <- readRDS(
  file.path(exp_folder, benchmark_original, "PARAM.rds")
)
campos_configuracion <- c(
  "dataset", "archivo_resultados", "semilla_primigenia",
  "n_mejores", "m_semillas", "train_final", "future",
  "semilla_kaggle", "cortes", "trainingstrategy", "lgbm", "semillas"
)
stopifnot(all(campos_configuracion %in% names(configuracion_original)))
configuracion_original <- configuracion_original[campos_configuracion]

dataset_file <- configuracion_original$dataset
dataset_url <- file.path(data_folder, dataset_file)

# [Anotación · líneas 76–98] Arma PARAM para esta corrida: experimento de origen LAG-009-REPLICA y el resto
#   copiado del benchmark original (archivo de resultados, semilla primigenia, cantidad de modelos y de
#   semillas, meses, semilla de la partición, cortes, undersampling y parámetros fijos de LightGBM).
#%% celda 6 [código]


PARAM <- list()
# Ejemplo: c("HT4950-01", "HT4950-02")
# PARAM$experimentos_origen <- c("PY495-01","PY495-02","PY4941", "PY495-01", "PY4942", "HT4941", "HT4942", "HT4940")
PARAM$dataset <- dataset_file
PARAM$experimentos_origen <- c('LAG-009-REPLICA')
PARAM$archivo_resultados <- configuracion_original$archivo_resultados

PARAM$semilla_primigenia <- configuracion_original$semilla_primigenia
PARAM$n_mejores <- configuracion_original$n_mejores #cantidad de modelos a evaluar de cada experimento
PARAM$m_semillas <- configuracion_original$m_semillas

PARAM$train_final <- configuracion_original$train_final
PARAM$future <- configuracion_original$future
PARAM$semilla_kaggle <- configuracion_original$semilla_kaggle
PARAM$cortes <- configuracion_original$cortes
PARAM$trainingstrategy$undersampling <- configuracion_original$trainingstrategy$undersampling

#%% celda 7 [código]
# Parámetros fijos documentados. Los presentes en BO_log.txt los pisan.
PARAM$lgbm$param_fijos <- configuracion_original$lgbm$param_fijos

# [Anotación · líneas 100–149] Lee el dataset y recalcula la clase ternaria con data.table: por cliente
#   obtiene los dos períodos siguientes y asigna CONTINUA, BAJA+1 (no está en el mes siguiente) o BAJA+2 (está
#   en el siguiente y no en el subsiguiente); el último mes queda sin clase y el penúltimo sólo recibe BAJA+1.
#   Ordena el dataset y cuenta filas por mes y clase.
#%% celda 8 [texto]
## Dataset y clase ternaria

Se conserva la lógica de generación utilizada en z495.

#%% celda 9 [código]

if (!file.exists(dataset_url)) {
  stop("No existe el dataset: ", dataset_url)
}
dataset <- fread(dataset_url)

#%% celda 10 [código]


dsimple <- dataset[, .(
  pos = .I,
  numero_de_cliente,
  periodo0 = as.integer(foto_mes / 100) * 12 + foto_mes %% 100
)]

setorder(dsimple, numero_de_cliente, periodo0)

periodo_ultimo <- dsimple[, max(periodo0)]
periodo_anteultimo <- periodo_ultimo - 1L

dsimple[, c("periodo1", "periodo2") :=
  shift(periodo0, n = 1:2, fill = NA, type = "lead"),
  by = numero_de_cliente
]

dsimple[periodo0 < periodo_anteultimo, ternaria := "CONTINUA"]

dsimple[
  periodo0 < periodo_ultimo &
    (is.na(periodo1) | periodo0 + 1L < periodo1),
  ternaria := "BAJA+1"
]

dsimple[
  periodo0 < periodo_anteultimo & periodo0 + 1L == periodo1 &
    (is.na(periodo2) | periodo0 + 2L < periodo2),
  ternaria := "BAJA+2"
]

setorder(dsimple, pos)
dataset[, ternaria := dsimple$ternaria]

setorder(dataset, foto_mes, ternaria, numero_de_cliente)
conteo_clases <- dataset[, .N, by = .(foto_mes, ternaria)]

# [Anotación · líneas 151–188] Crea clase01 (BAJA+1 o BAJA+2 = 1), separa entrenamiento (train_final) y futuro
#   (future), define las columnas de entrada quitando 16 nombres y arma el lgb.Dataset de entrenamiento con
#   todas las filas de esos meses.
#%% celda 11 [código]
dataset[, clase01 := fifelse(
  ternaria %in% c("BAJA+2", "BAJA+1"),
  1L,
  0L
)]

dataset_train <- copy(dataset[foto_mes %in% PARAM$train_final])
dfuture <- copy(dataset[foto_mes %in% PARAM$future])

campos_buenos <- setdiff(
  names(dataset_train),
c(
    "ternaria",
    "ternaria_lag1",
    "clase01",
    "fold",
    "azar",
    "training",
    "cprestamos_personales",
    "mprestamos_personales",
    "cprestamos_personales_lag1",
    "mprestamos_personales_lag1",
    "cprestamos_personales_delta1",
    "mprestamos_personales_delta1",
    "cprestamos_personales_lag_pond",
    "mprestamos_personales_lag_pond",
    "cprestamos_personales_delta_lag_pond",
    "mprestamos_personales_delta_lag_pond"
  )
)

dtrain_final <- lgb.Dataset(
  data = data.matrix(dataset_train[, ..campos_buenos]),
  label = dataset_train[, clase01]
)

conteo_train_final <- dataset_train[, .N, by = ternaria]

# [Anotación · líneas 190–263] resolver_carpeta_experimento ubica la carpeta de la BO. leer_mejores_resultados
#   lee su BO_log.txt, conserva los trials COMPLETE, renombra las columnas params_* de Optuna al nombre del
#   parámetro de LightGBM, detecta la columna de métrica (metrica, value o y), ordena de mayor a menor y
#   devuelve los primeros n_mejores con su ranking e identificador de origen.
#%% celda 12 [texto]
## Lectura de resultados de R o Python

La función reconoce:

- `metrica` en el log de z495/R;
- `value` y columnas `params_*` en el log de Optuna/Python;
- `y` en otros logs de R compatibles.

#%% celda 13 [código]
resolver_carpeta_experimento <- function(experimento) {
  if (dir.exists(experimento)) {
    return(normalizePath(experimento, mustWork = TRUE))
  }

  candidato <- file.path(exp_folder, experimento)
  if (!dir.exists(candidato)) {
    stop("No existe la carpeta del experimento: ", candidato)
  }

  normalizePath(candidato, mustWork = TRUE)
}


leer_mejores_resultados <- function(carpeta, archivo, n_mejores) {
  ruta <- file.path(carpeta, archivo)
  if (!file.exists(ruta)) {
    stop("No existe el archivo de resultados: ", ruta)
  }

  tb <- fread(ruta)
  tb[, fila_origen := .I]

  if ("state" %in% names(tb)) {
    tb <- tb[state == "COMPLETE"]
  }

  # Optuna escribe los hiperparámetros como params_nombre.
  columnas_python <- grep("^params_", names(tb), value = TRUE)
  for (columna in columnas_python) {
    nombre_lgbm <- sub("^params_", "", columna)
    if (!nombre_lgbm %in% names(tb)) {
      setnames(tb, columna, nombre_lgbm)
    }
  }

  candidatas_metrica <- c("metrica", "value", "y")
  campo_metrica <- candidatas_metrica[candidatas_metrica %in% names(tb)][1]

  if (is.na(campo_metrica)) {
    stop("No se encontró una columna de métrica: metrica, value o y")
  }

  tb[, metrica_origen := as.numeric(get(campo_metrica))]
  tb <- tb[is.finite(metrica_origen)]

  if (nrow(tb) == 0L) {
    stop("El archivo no contiene evaluaciones completas con una métrica válida")
  }

  setorder(tb, -metrica_origen)
  tb <- head(tb, min(as.integer(n_mejores), nrow(tb)))
  tb[, ranking_origen := .I]

  if ("iter" %in% names(tb)) {
    tb[, id_origen := as.character(iter)]
  } else if ("number" %in% names(tb)) {
    tb[, id_origen := as.character(number)]
  } else {
    tb[, id_origen := as.character(fila_origen)]
  }

  tb[]
}

# [Anotación · líneas 265–301] Aplica esa lectura a cada experimento de origen, une los resultados, numera los
#   modelos (modelo_id) y determina qué columnas del log son parámetros de LightGBM.
#%% celda 14 [código]
modelos_por_experimento <- lapply(
  PARAM$experimentos_origen,
  function(experimento) {
    carpeta <- resolver_carpeta_experimento(experimento)

    modelos <- leer_mejores_resultados(
      carpeta = carpeta,
      archivo = PARAM$archivo_resultados,
      n_mejores = PARAM$n_mejores
    )

    modelos[, experimento_origen := experimento]
    modelos
  }
)

mejores_modelos <- rbindlist(
  modelos_por_experimento,
  use.names = TRUE,
  fill = TRUE
)

mejores_modelos[, modelo_id := .I]

columnas_parametros <- intersect(
  names(PARAM$lgbm$param_fijos),
  names(mejores_modelos)
)

columnas_mostrar <- unique(c(
  "experimento_origen", "ranking_origen", "id_origen", "metrica_origen",
  columnas_parametros
))

# Descomentar si se quieren inspeccionar los modelos seleccionados.
# mejores_modelos[, ..columnas_mostrar]

# [Anotación · líneas 303–330] Genera las semillas de entrenamiento: sortea m_semillas números primos entre
#   100.000 y 1.000.000 con set.seed(semilla_primigenia) y generador L'Ecuyer-CMRG, y corta si no coinciden con
#   las semillas guardadas en el benchmark original.
#%% celda 15 [texto]
## Semillas

Se generan semillas primas reproducibles con el código original y se comprueba que coincidan, en el mismo orden, con las semillas de entrenamiento documentadas en el benchmark original. Si difieren, la ejecución se detiene antes de entrenar.

#%% celda 16 [código]
primos <- generate_primes(100000, 1000000)

if (PARAM$m_semillas > length(primos)) {
  stop("m_semillas supera la cantidad de números primos disponibles")
}

set.seed(PARAM$semilla_primigenia, kind = "L'Ecuyer-CMRG")
PARAM$semillas <- sample(
  primos,
  size = PARAM$m_semillas,
  replace = FALSE
)

# Verifica las semillas contra las documentadas en el benchmark original.
if (!identical(
  as.integer(PARAM$semillas),
  as.integer(configuracion_original$semillas)
)) {
  stop("Las semillas generadas no coinciden con las documentadas en el benchmark original")
}

invisible(PARAM$semillas)

# [Anotación · líneas 332–411] Funciones de ganancia: particionar asigna folds al azar dentro de cada grupo;
#   realidad_inicializar divide los clientes del mes futuro en Public (30%) y Private (70%) estratificando por
#   ternaria con semilla_kaggle; realidad_evaluar suma 1.072.500 por cada BAJA+2 enviado y -27.500 por cada otro
#   cliente enviado, y devuelve la ganancia total y las de Public y Private divididas por 0,3 y 0,7.
#%% celda 17 [texto]
## Ganancia de Producción de z494

Se conserva la división fija `Public`/`Private` de z494. La semilla Kaggle es independiente de las semillas usadas para entrenar los modelos.

#%% celda 18 [código]
particionar <- function(
  data,
  division,
  agrupa = "",
  campo = "fold",
  start = 1L,
  seed = NA
) {
  if (!is.na(seed)) {
    set.seed(seed, kind = "L'Ecuyer-CMRG")
  }

  bloque <- unlist(mapply(
    function(x, y) rep(y, x),
    division,
    seq(from = start, length.out = length(division))
  ))

  data[, (campo) := sample(
    rep(bloque, ceiling(.N / length(bloque)))
  )[1:.N], by = agrupa]
}


realidad_inicializar <- function(pfuture, pparam) {
  drealidad <- pfuture[, .(
    numero_de_cliente,
    foto_mes,
    ternaria
  )]

  particionar(
    data = drealidad,
    division = c(3L, 7L),
    agrupa = "ternaria",
    seed = pparam$semilla_kaggle
  )

  drealidad
}


realidad_evaluar <- function(prealidad, pprediccion) {
  prealidad[
    pprediccion,
    on = c("numero_de_cliente", "foto_mes"),
    predicted := i.Predicted
  ]

  tbl <- prealidad[, .(
    qty = .N
  ), by = .(fold, predicted, ternaria)]

  res <- list(
    public = tbl[
      fold == 1L & predicted == 1L,
      sum(qty * fifelse(ternaria == "BAJA+2", 1072500, -27500))
    ] / 0.3,
    private = tbl[
      fold == 2L & predicted == 1L,
      sum(qty * fifelse(ternaria == "BAJA+2", 1072500, -27500))
    ] / 0.7,
    total = tbl[
      predicted == 1L,
      sum(qty * fifelse(ternaria == "BAJA+2", 1072500, -27500))
    ]
  )

  prealidad[, predicted := NULL]
  res
}


drealidad <- realidad_inicializar(dfuture, PARAM)

# [Anotación · líneas 413–478] extraer_parametros_modelo pisa los parámetros fijos con los de la fila del log,
#   fija la semilla, convierte a entero los parámetros enteros y divide min_data_in_leaf por el undersampling.
#   entrenar_y_predecir entrena con esos parámetros sobre el dataset de entrenamiento y devuelve la probabilidad
#   para el mes futuro.
#%% celda 19 [texto]
## Entrenamiento y evaluación de los mejores modelos

Cada fila del log pisa los parámetros fijos correspondientes. Cada semilla cambia el entrenamiento de LightGBM, pero no los hiperparámetros del experimento.

#%% celda 20 [código]
extraer_parametros_modelo <- function(fila_modelo, semilla) {
  disponibles <- intersect(
    names(PARAM$lgbm$param_fijos),
    names(fila_modelo)
  )

  parametros_log <- as.list(fila_modelo[, ..disponibles])
  parametros_log <- parametros_log[vapply(
    parametros_log,
    function(valor) length(valor) == 1L && !is.na(valor),
    logical(1)
  )]

  parametros <- modifyList(
    PARAM$lgbm$param_fijos,
    parametros_log
  )

  parametros$seed <- as.integer(semilla)

  parametros_enteros <- intersect(
    c(
      "num_iterations", "num_leaves", "max_depth", "max_bin",
      "max_drop", "early_stopping", "min_data_in_leaf"
    ),
    names(parametros)
  )

  parametros[parametros_enteros] <- lapply(
    parametros[parametros_enteros],
    as.integer
  )

  # Normalización de Producción de z494. En z495 permanece en cero.
  parametros$min_data_in_leaf <- round(
    parametros$min_data_in_leaf /
      PARAM$trainingstrategy$undersampling
  )

  parametros
}


entrenar_y_predecir <- function(fila_modelo, semilla) {
  parametros <- extraer_parametros_modelo(fila_modelo, semilla)

  modelo <- lgb.train(
    data = dtrain_final,
    param = parametros
  )

  prediccion <- predict(
    modelo,
    data.matrix(dfuture[, ..campos_buenos])
  )

  rm(modelo)

  prediccion
}

# [Anotación · líneas 480–589] Ciclo principal: para cada modelo seleccionado y cada semilla entrena, ordena
#   los clientes del mes futuro por probabilidad y, para cada corte de PARAM$cortes, marca los primeros `envios`
#   y calcula la ganancia total, Public y Private. Guarda una fila por modelo, semilla y corte e imprime el
#   avance y el tiempo restante estimado.
#%% celda 21 [código]
total_entrenamientos <- nrow(mejores_modelos) * length(PARAM$semillas)

resultados <- vector(
  mode = "list",
  length = total_entrenamientos * length(PARAM$cortes)
)

k <- 0L
entrenamientos_completos <- 0L
inicio_proceso <- Sys.time()

cat("Entrenamientos totales:", total_entrenamientos, "\n")
flush.console()

for (modelo_id in seq_len(nrow(mejores_modelos))) {
  cat("****MODELO:", modelo_id, "****** \n")
  flush.console()
  fila_modelo <- mejores_modelos[modelo_id]
  experimento <- fila_modelo$experimento_origen
  modelos_en_experimento <- mejores_modelos[
    experimento_origen == experimento,
    .N
  ]

  for (indice_semilla in seq_along(PARAM$semillas)) {
    semilla <- PARAM$semillas[indice_semilla]
    cat("****SEMILLA:", semilla, "****** \n")
    flush.console()
    inicio_entrenamiento <- Sys.time()

    prediccion <- entrenar_y_predecir(
      fila_modelo = fila_modelo,
      semilla = semilla
    )

    tb_prediccion <- dfuture[, .(
      numero_de_cliente,
      foto_mes,
      ternaria
    )]

    tb_prediccion[, prob := prediccion]
    setorder(tb_prediccion, -prob)

    for (envios in PARAM$cortes) {
      k <- k + 1L

      tb_prediccion[, Predicted := 0L]
      tb_prediccion[seq_len(envios), Predicted := 1L]

      ganancia <- realidad_evaluar(
        prealidad = drealidad,
        pprediccion = tb_prediccion
      )

      resultados[[k]] <- data.table(
        modelo_id = modelo_id,
        experimento_origen = experimento,
        dataset_bench=dataset_file,
        ranking_origen = fila_modelo$ranking_origen,
        id_origen = fila_modelo$id_origen,
        metrica_origen = fila_modelo$metrica_origen,
        semilla = as.integer(semilla),
        envios = as.integer(envios),
        ganancia_total = ganancia$total,
        ganancia_public_estimada = ganancia$public,
        ganancia_private_estimada = ganancia$private
      )
    }

    entrenamientos_completos <- entrenamientos_completos + 1L
    porcentaje <- 100 * entrenamientos_completos / total_entrenamientos
    minutos_transcurridos <- as.numeric(difftime(
      Sys.time(), inicio_proceso, units = "mins"
    ))
    minutos_ultimo <- as.numeric(difftime(
      Sys.time(), inicio_entrenamiento, units = "mins"
    ))
    minutos_restantes <-
      minutos_transcurridos / entrenamientos_completos *
      (total_entrenamientos - entrenamientos_completos)

    cat(sprintf(
      paste0(
        "[%d/%d - %.1f%%] Experimento=%s | modelo=%d/%d | ",
        "semilla=%d/%d | último=%.1f min | faltan~%.1f min\n"
      ),
      entrenamientos_completos,
      total_entrenamientos,
      porcentaje,
      experimento,
      fila_modelo$ranking_origen,
      modelos_en_experimento,
      indice_semilla,
      length(PARAM$semillas),
      minutos_ultimo,
      minutos_restantes
    ))
    flush.console()

    rm(prediccion, tb_prediccion)
    gc(full = TRUE, verbose = FALSE)
  }
}

resultados_detalle <- rbindlist(resultados)

# Descomentar para imprimir el resultado individual de cada semilla y corte.
# resultados_detalle[]

# [Anotación · líneas 591–625] Promedia por modelo y corte sobre las semillas: ganancia total media, desvío,
#   mínimo y máximo, y medias de Public y Private; une esos valores con los hiperparámetros de cada modelo.
#%% celda 22 [texto]
## Promedio de ganancias

`resumen_ganancias` muestra cada corte promediado sobre las `m` semillas. `mejor_corte_por_modelo` conserva el corte con mayor ganancia total promedio para cada conjunto de hiperparámetros.

#%% celda 23 [código]
resumen_metricas <- resultados_detalle[, .(
  ganancia_total_promedio = mean(ganancia_total),
  ganancia_total_sd = if (.N > 1L) sd(ganancia_total) else 0,
  ganancia_total_min = min(ganancia_total),
  ganancia_total_max = max(ganancia_total),
  ganancia_public_promedio = mean(ganancia_public_estimada),
  ganancia_private_promedio = mean(ganancia_private_estimada)
), by = .(dataset_bench, modelo_id, envios)]

info_modelos <- mejores_modelos[, c(
  "experimento_origen",
  "ranking_origen",
  "id_origen",
  "metrica_origen",
  columnas_parametros
), with = FALSE]

info_modelos[, modelo_id := .I]

resumen_ganancias <- merge(
  info_modelos,
  resumen_metricas,
  by = "modelo_id"
)

setorder(resumen_ganancias, experimento_origen, ranking_origen, envios)

# Descomentar para imprimir el resumen de todos los cortes.
# resumen_ganancias[]

# [Anotación · líneas 627–665] Para cada modelo se queda con el corte de mayor ganancia total promedio, ordena
#   los modelos por esa ganancia e imprime la tabla por experimento.
#%% celda 24 [código]
mejor_corte_por_modelo <- resumen_ganancias[
  order(modelo_id, -ganancia_total_promedio),
  .SD[1L],
  by = modelo_id
]

setorder(
  mejor_corte_por_modelo,
  experimento_origen,
  -ganancia_total_promedio
)

columnas_resumen <- intersect(c(
  "ranking_origen",
  "id_origen",
  "metrica_origen",
  "num_iterations",
  "num_leaves",
  "min_sum_hessian_in_leaf",
  "envios",
  "ganancia_total_promedio",
  "ganancia_total_sd",
  "ganancia_total_min",
  "ganancia_total_max",
  "ganancia_public_promedio",
  "ganancia_private_promedio"
), names(mejor_corte_por_modelo))

for (experimento in PARAM$experimentos_origen) {
  cat("\nExperimento:", experimento, "\n")
  print(
    mejor_corte_por_modelo[
      experimento_origen == experimento,
      ..columnas_resumen
    ]
  )
  flush.console()
}

# [Anotación · líneas 667–686] Crea la carpeta de salida y guarda PARAM.rds y mejor_corte_por_modelo.tsv.
#%% celda 25 [texto]
## Archivos para la validación manual

Se guardan únicamente `PARAM.rds` y `mejor_corte_por_modelo.tsv` en `carpeta_salida`.

#%% celda 26 [código]
dir.create(carpeta_salida, recursive = TRUE, showWarnings = FALSE)

saveRDS(
  PARAM,
  file.path(carpeta_salida, "PARAM.rds")
)

fwrite(
  mejor_corte_por_modelo,
  file.path(carpeta_salida, "mejor_corte_por_modelo.tsv"),
  sep = "\t"
)

cat("Archivos guardados en:", carpeta_salida, "\n")
```

### entregas/bo/validacion_manual_lag028_replica.ipynb

Validación manual en R del modelo elegido en el benchmark de LAG-028, sobre el dataset de rankings; guarda los parámetros por semilla en 62-REPLICA.rds.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–42] Presentación y carga de librerías, instalando las que falten: data.table, R.utils,
#   primes, rlist, yaml, lightgbm, DiceKriging, mlrMBO, here y ggplot2.
#%% celda 1 [texto]
# Réplica de la validación manual — LAG-028 / RDS 62

Ejecutar desde `entregas/bo`, con kernel R.

La entrada es `benchmark_multisemilla_lags20261009_200322-REPLICA`. El dataset, los meses, las semillas y las columnas excluidas son los de la validación manual original que produjo el RDS 62; se configuran en esta notebook.

Se conserva el código original que elige el mejor modelo del benchmark, construye sus parámetros, entrena y evalúa cada semilla. Se guardan `62-REPLICA.rds` y `validaciones_manuales_replica.csv` en `entregas/bo`.

# Librerias

#%% celda 2 [código]
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

library(here)
require("ggplot2")

# [Anotación · líneas 44–64] Rutas relativas a entregas/bo, dataset RANKS_LF_O2_K6_P4.csv, archivo de registro
#   validaciones_manuales_replica.csv, semillas 230047, 230059, 230063, 230077 y 230081, e identificador
#   62-REPLICA.
#%% celda 3 [texto]
# URLS

#%% celda 4 [código]
# Ejecutar desde entregas/bo.
root <- getwd()
exp_folder <- root
data_folder <- file.path(dirname(root), "dataset")

dataset_file = 'RANKS_LF_O2_K6_P4.csv'
dataset_url <- file.path(data_folder, dataset_file)
list.files(data_folder)

carpeta_man_val <- root
archivo_validaciones <- file.path(
  carpeta_man_val,
  "validaciones_manuales_replica.csv"
)

SEEDS <- c(230047, 230059, 230063, 230077, 230081)
id_validacion <- '62-REPLICA'

# [Anotación · líneas 66–127] Lee el dataset, lo ordena y cuenta filas por mes y clase; crea clase01 (BAJA+1 o
#   BAJA+2 = 1) y define las columnas de entrada quitando 25 nombres (los de bo/lag028_replica.ipynb).
#%% celda 5 [texto]
# LEEMOS DATASET

#%% celda 6 [código]
# leo el dataset
dataset <- fread(dataset_url)

#%% celda 7 [código]
setorder( dataset, foto_mes, ternaria, numero_de_cliente)
dataset[, .N, list(foto_mes, ternaria)]

#%% celda 8 [código]
# colnames(dataset)

#%% celda 9 [texto]
# CLASE01

#%% celda 10 [código]
dataset[, clase01 := ifelse(ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)]

#%% celda 11 [texto]
# Columnas a usar

#%% celda 12 [código]
grep("prestamos_personales", colnames(dataset), value = TRUE, ignore.case = TRUE)
grep("ternaria", colnames(dataset), value = TRUE, ignore.case = TRUE)

#%% celda 13 [código]
columnas_excluir <-
c(
    "ternaria",
    "ternaria_lag1",
    "ternaria_lag2",
    "clase01",
    "fold",
    "azar",
    "training",
    "cprestamos_personales",
    "cprestamos_personales_lag1",
    "cprestamos_personales_delta1",
    "cprestamos_personales_lag2",
    "cprestamos_personales_delta2",
    "cprestamos_personales_lag_pond",
    "cprestamos_personales_delta_lag_pond",
    "cprestamos_personales_lag_pond2",
    "cprestamos_personales_delta_lag_pond2",
    "mprestamos_personales",
    "mprestamos_personales_lag1",
    "mprestamos_personales_delta1",
    "mprestamos_personales_lag2",
    "mprestamos_personales_delta2",
    "mprestamos_personales_lag_pond",
    "mprestamos_personales_delta_lag_pond",
    "mprestamos_personales_lag_pond2",
    "mprestamos_personales_delta_lag_pond2"
  )

#%% celda 14 [código]
campos_buenos <- setdiff(
  colnames(dataset),
  columnas_excluir  
)

# [Anotación · líneas 129–153] Indica la carpeta del benchmark replicado
#   (benchmark_multisemilla_lags20261009_200322-REPLICA) y los meses: entrenamiento 202103 y 202104, futuro
#   202106.
#%% celda 15 [texto]
# Experimento

#%% celda 16 [código]
# Carpeta generada por la validación multisemilla replicada.
carpeta_benchmarks <- exp_folder
writeLines(list.files(carpeta_benchmarks, pattern = "benchmark"))

#%% celda 17 [código]
benchmark_base <- "benchmark_multisemilla_lags20261009_200322-REPLICA"

#%% celda 18 [texto]
## Parametros

#%% celda 19 [código]

carpeta_benchmark <-file.path(
  carpeta_benchmarks,
  benchmark_base
)

#%% celda 20 [código]
train <- c(202103, 202104)
train_final <- c(202103, 202104)
future <- c(202106)

# [Anotación · líneas 155–186] Lee PARAM.rds del benchmark y, de mejor_corte_por_modelo.tsv, la fila de mayor
#   ganancia_total_promedio. Combina los parámetros fijos con los de esa fila, divide min_data_in_leaf por el
#   undersampling y toma la lista de cortes.
#%% celda 21 [código]

# Configuración utilizada durante la validación
PARAM_BENCH <- readRDS(
  file.path(carpeta_benchmark, "PARAM.rds")
)

# Lee los mejores resultados y selecciona el de mayor ganancia promedio
mejor_modelo <- data.table::fread(
  file.path(carpeta_benchmark, "mejor_corte_por_modelo.tsv")
)[which.max(ganancia_total_promedio)]

# Identifica qué columnas de la fila corresponden a parámetros de LightGBM
columnas_parametros <- intersect(
  names(PARAM_BENCH$lgbm$param_fijos),
  names(mejor_modelo)
)

# Combina los parámetros fijos con los del mejor modelo
params_completos <- modifyList(
  PARAM_BENCH$lgbm$param_fijos,
  as.list(mejor_modelo[, ..columnas_parametros])
)

# Ajusta min_data_in_leaf según el undersampling usado
params_completos$min_data_in_leaf <- round(
  params_completos$min_data_in_leaf /
    PARAM_BENCH$trainingstrategy$undersampling
)

#%% celda 22 [código]
cortes <-PARAM_BENCH$cortes

# [Anotación · líneas 188–208] Celdas de control (directorio de trabajo, existencia y permiso de lectura de
#   PARAM.rds, listado de carpetas) y separación de las filas de entrenamiento y del mes futuro.
#%% celda 23 [código]
getwd()
ruta <- file.path(carpeta_benchmark, "PARAM.rds")
ruta
file.exists(ruta)
file.access(ruta, 4)

#%% celda 24 [código]
list.files(exp_folder, pattern = "^benchmark_multisemilla")
list.files(carpeta_benchmark)

#%% celda 25 [texto]
## Dataset train y test

#%% celda 26 [código]
dataset_train <- dataset[foto_mes %in% train_final]
dataset_train[,.N, list(foto_mes, ternaria)]

#%% celda 27 [código]
# aplico el modelo a los datos sin clase
dfuture <- dataset[foto_mes %in% future]

# [Anotación · líneas 210–261] Para cada semilla entrena un LightGBM con todos los datos de entrenamiento,
#   predice el mes futuro, asigna 1.072.500 a cada BAJA+2 y -27.500 al resto, ordena por probabilidad y calcula
#   la ganancia acumulada; guarda el máximo de la curva y los parámetros usados. Al final promedia los máximos
#   de las 5 semillas.
#%% celda 28 [texto]
# Entreno

#%% celda 29 [código]
ganancias_semillas <- numeric(length(SEEDS))
curvas_semillas <- vector("list", length(SEEDS))
params_por_semilla <- setNames(vector("list", length(SEEDS)), as.character(SEEDS))

for (i in seq_along(SEEDS)) {
  params_semilla <- params_completos
  params_semilla$seed <- SEEDS[i]
  params_por_semilla[[i]] <- params_semilla

  dtrain_final <- lgb.Dataset(
    data= data.matrix(dataset_train[, campos_buenos, with= FALSE]),
    label= dataset_train[, clase01]
  )

  modelo_final <- lgb.train(
    data= dtrain_final,
    param= params_semilla
  )

  # hago el predict en los datos del futuro, y calculo la ganancia

  # aplico el modelo a los datos nuevos
  prediccion <- predict(
    modelo_final,
    data.matrix(dfuture[, campos_buenos, with= FALSE])
  )

  # calculo la ganancia en los datos ddel futuro para todos los cortes
  tb_prediccion <- dfuture[, list(numero_de_cliente, foto_mes,ternaria)]
  tb_prediccion[, prob := prediccion ]
  tb_prediccion[, gan := ifelse(ternaria == "BAJA+2", 1072500, -27500)]

  # lgb.save(modelo_final, "modelo.txt" )
  # Dibujo la curva de ganancia acumulada
  setorder(tb_prediccion, -prob)
  tb_prediccion[, ganancia_acumulada := cumsum(gan)]
  tb_prediccion[, pos := sequence(.N)]

  print(tb_prediccion|> head())

  ganancias_semillas[i] <- max(tb_prediccion$ganancia_acumulada)
  curvas_semillas[[i]] <- tb_prediccion[, list(
    pos, ganancia_acumulada, seed = SEEDS[i]
  )]
}

ganancia_promedio <- mean(ganancias_semillas)
tb_curvas <- rbindlist(curvas_semillas)

# [Anotación · líneas 263–281] Grafica la ganancia acumulada de cada semilla hasta la posición 30.000 e
#   imprime, para cada corte, la ganancia de los primeros clientes de la tabla de la última semilla del ciclo.
#%% celda 30 [código]
# defino hasta donde muestra el grafico
amostrar <- 30000
# observamos la curva de ganancia
gra <- ggplot(
           data= tb_curvas[pos <= amostrar],
           aes( x= pos, y= ganancia_acumulada, color= factor(seed))
             ) + geom_line() + labs(color = "Seed")

gra <- gra + theme(text = element_text(size = 16))

options(repr.plot.width=16, repr.plot.height=9)
print( gra )

#%% celda 31 [código]
for (envios in cortes) {
  ganancia <- tb_prediccion[1:envios, sum(gan)]
  cat( envios, "\t", ganancia, "\n")
}

# [Anotación · líneas 283–323] Agrega una fila a validaciones_manuales_replica.csv y guarda la lista de
#   parámetros por semilla en 62-REPLICA.rds.
#%% celda 32 [texto]
# Guardamos resultados

#%% celda 33 [código]
if (file.exists(archivo_validaciones)) {
  validaciones_previas <- fread(archivo_validaciones)
}

registro_validacion <- data.table(
  id_validacion = id_validacion,
  ganancia = ganancia_promedio,
  seeds = paste(SEEDS, collapse = ","),
  dataset = dataset_file,
  cantidad_registros_totales = nrow(dataset),
  cantidad_registros_entrenamiento = nrow(dataset_train),
  cantidad_registros_validacion = nrow(dfuture),
  meses_entrenamiento = paste(train_final, collapse = ","),
  meses_validacion = paste(future, collapse = ","),
  columnas_excluidas = paste(columnas_excluir, collapse = ","),
  benchmark_original = benchmark_base
)

# Incorpora seeds al histórico anterior si todavía no tiene esa columna.
if (file.exists(archivo_validaciones) && !("seeds" %in% names(validaciones_previas))) {
  validaciones_previas[, seeds := NA_character_]
  setcolorder(validaciones_previas, names(registro_validacion))
  fwrite(validaciones_previas, archivo_validaciones)
}

fwrite(
  registro_validacion,
  archivo_validaciones,
  append = file.exists(archivo_validaciones),
  col.names = !file.exists(archivo_validaciones)
)

# Guarda exactamente los parámetros enviados a lgb.train()
saveRDS(
  params_por_semilla,
  file.path(carpeta_man_val, paste0(id_validacion, ".rds"))
)

# [Anotación · líneas 325–330] Lee y muestra el histórico de validaciones.
#%% celda 34 [texto]
# Historico

#%% celda 35 [código]
historico <- fread(archivo_validaciones)
historico
```

### entregas/bo/lag028_replica.ipynb

Réplica de la optimización bayesiana LAG-028 con Optuna sobre el dataset de rankings, de la que salen los hiperparámetros de parametros/62.rds (modelo 3). Lee bo/LAG-028/ y escribe en bo/LAG-028-REPLICA/.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–19] Presentación (réplica de la BO a partir de la configuración y los puntos iniciales
#   del experimento original) y carga de librerías: cudf, numpy, pandas, yaml, lightgbm, optuna con GPSampler y
#   train_test_split de scikit-learn.
#%% celda 1 [texto]
# Réplica de BO

Configuración y puntos iniciales recuperados del experimento original.
Ejecutar desde `entregas/bo`. Los resultados se guardan en una carpeta nueva.

#%% celda 2 [código]
import os
import numpy as np
import pandas as pd
import yaml
import lightgbm as lgb
import optuna
import cudf

from sklearn.model_selection import train_test_split
from optuna.samplers import GPSampler
from optuna.distributions import IntDistribution
from optuna.trial import TrialState

# [Anotación · líneas 21–63] Define carpetas relativas a entregas/bo, el experimento de origen LAG-028, la
#   carpeta de salida LAG-028-REPLICA, el dataset RANKS_LF_O2_K6_P4.csv y 25 columnas excluidas (ternaria con
#   sus lags 1 y 2, clase01, fold, azar, training y las dos de préstamos personales con sufijos _lag1, _delta1,
#   _lag2, _delta2, _lag_pond, _delta_lag_pond, _lag_pond2 y _delta_lag_pond2). Corta si origen y destino
#   coinciden.
#%% celda 3 [código]
# Ejecutar con el directorio de trabajo en entregas/bo.
BO_URL = os.getcwd()
DATA_FOLDER = os.path.join(os.path.dirname(BO_URL), "dataset")

experimento_original = "LAG-028"
experiment_name = "LAG-028-REPLICA"
dataset_file = "RANKS_LF_O2_K6_P4.csv"

columnas_excluidas = {
    "ternaria",
    "ternaria_lag1",
    "ternaria_lag2",
    "clase01",
    "fold",
    "azar",
    "training",
    "cprestamos_personales",
    "cprestamos_personales_lag1",
    "cprestamos_personales_delta1",
    "cprestamos_personales_lag2",
    "cprestamos_personales_delta2",
    "cprestamos_personales_lag_pond",
    "cprestamos_personales_delta_lag_pond",
    "cprestamos_personales_lag_pond2",
    "cprestamos_personales_delta_lag_pond2",
    "mprestamos_personales",
    "mprestamos_personales_lag1",
    "mprestamos_personales_delta1",
    "mprestamos_personales_lag2",
    "mprestamos_personales_delta2",
    "mprestamos_personales_lag_pond",
    "mprestamos_personales_delta_lag_pond",
    "mprestamos_personales_lag_pond2",
    "mprestamos_personales_delta_lag_pond2",
}

ORIGEN_URL = os.path.join(BO_URL, experimento_original)
EXPERIMENT_URL = os.path.join(BO_URL, experiment_name)
DATA_LAGS_URL = os.path.join(DATA_FOLDER, dataset_file)

if os.path.abspath(ORIGEN_URL) == os.path.abspath(EXPERIMENT_URL):
    raise ValueError("El destino debe ser distinto del experimento original.")

# [Anotación · líneas 65–114] Lee PARAM.yml del experimento original y abre su estudio de Optuna
#   (optuna_study.db). De los trials recupera la distribución de cada hiperparámetro (límites, tipo, paso y
#   escala logarítmica) y los puntos que se habían encolado a mano (fixed_params). Actualiza PARAM con el nombre
#   nuevo, el dataset, las exclusiones y los rangos, e imprime meses, métrica y cantidades de trials.
#%% celda 4 [texto]
## Configuración original

#%% celda 5 [código]
with open(os.path.join(ORIGEN_URL, "PARAM.yml"), encoding="utf-8") as archivo:
    PARAM = yaml.safe_load(archivo)

study_db_original = os.path.join(ORIGEN_URL, "optuna_study.db")
study_original = optuna.load_study(
    study_name=PARAM["experimento"],
    storage=f"sqlite:///{study_db_original}",
)

# Recuperar límites, tipos, pasos y escala logarítmica.
distribuciones = {}
for trial in study_original.trials:
    distribuciones.update(trial.distributions)

rangos_bo = {
    nombre: (distribucion.low, distribucion.high)
    for nombre, distribucion in distribuciones.items()
}

# Puntos agregados a mano, en el mismo orden del estudio original.
puntos_iniciales_bo = [
    trial.system_attrs["fixed_params"].copy()
    for trial in study_original.trials
    if "fixed_params" in trial.system_attrs
]

PARAM["experimento"] = experiment_name
PARAM["dataset"] = dataset_file
PARAM["columnas_excluidas"] = sorted(columnas_excluidas)
PARAM["rangos_bo"] = {nombre: list(rango) for nombre, rango in rangos_bo.items()}
PARAM["out"]["lgbm"] = {}

# Parámetros editables antes de ejecutar las celdas siguientes:
# PARAM["train"], PARAM["training_pct"], PARAM["semilla_primigenia"]
# PARAM["trainingstrategy"]["undersampling"]
# PARAM["lgbm"]["param_fijos"]
# PARAM["hyperparametertuning"]["n_startup_trials"]
# PARAM["hyperparametertuning"]["iteraciones"]
# rangos_bo, puntos_iniciales_bo

n_startup_trials = PARAM["hyperparametertuning"]["n_startup_trials"]
n_trials_total = PARAM["hyperparametertuning"]["iteraciones"]
print("Meses:", PARAM["train"])
print("Métrica:", PARAM["lgbm"]["param_fijos"]["metric"])
print("Puntos manuales:", len(puntos_iniciales_bo))
print("Inicialización:", n_startup_trials, "| Total:", n_trials_total)

# [Anotación · líneas 116–161] Lee el CSV con cudf, se queda con los meses de PARAM['train'] (202103 y 202104
#   en LAG-028/PARAM.yml; la lectura con pandas está comentada) y pasa a pandas. Parte las filas en fold 1 (70%)
#   y fold 2 con train_test_split estratificado por ternaria y semilla 230047. Crea clase01 (BAJA+1 o BAJA+2 =
#   1), un número al azar por fila y la marca training: filas del fold 1 que son baja o cuyo número al azar es
#   menor o igual a 0,1 (undersampling).
#%% celda 6 [texto]
## Dataset y partición

#%% celda 7 [código]
# df = pd.read_csv(
#     DATA_LAGS_URL,
#     dtype={"numero_de_cliente": "int32", "foto_mes": "int32"},
# )
# dataset_train_cpu = df.loc[df["foto_mes"].isin(PARAM["train"])].reset_index(drop=True)
# del df

df = cudf.read_csv(
    DATA_LAGS_URL,
    dtype={"numero_de_cliente": "int32", "foto_mes": "int32"},
)

dataset_train_cpu = (
    df.loc[df["foto_mes"].isin(PARAM["train"])]
    .to_pandas()
    .reset_index(drop=True)
)
del df

indices_fold_1, indices_fold_2 = train_test_split(
    np.arange(len(dataset_train_cpu)),
    train_size=PARAM["training_pct"] / 100,
    stratify=dataset_train_cpu["ternaria"],
    random_state=PARAM["semilla_primigenia"],
)

dataset_train_cpu["fold"] = np.int8(2)
dataset_train_cpu.loc[indices_fold_1, "fold"] = np.int8(1)
dataset_train_cpu["clase01"] = (
    dataset_train_cpu["ternaria"].isin(["BAJA+1", "BAJA+2"])
    .astype(np.int8)
)

rng = np.random.default_rng(PARAM["semilla_primigenia"])
dataset_train_cpu["azar"] = rng.random(len(dataset_train_cpu))
dataset_train_cpu["training"] = (
    dataset_train_cpu["fold"].eq(1)
    & (
        (dataset_train_cpu["azar"] <= PARAM["trainingstrategy"]["undersampling"])
        | dataset_train_cpu["ternaria"].isin(["BAJA+1", "BAJA+2"])
    )
).astype(np.int8)

# [Anotación · líneas 163–187] Arma la lista de columnas de entrada y dos lgb.Dataset: entrenamiento con las
#   filas training == 1 y validación con todas las filas training == 0 (el fold 2 y las filas del fold 1 que el
#   submuestreo dejó afuera). Imprime las cantidades.
campos_buenos = [
    columna for columna in dataset_train_cpu.columns
    if columna not in columnas_excluidas
]

mask_training = dataset_train_cpu["training"].eq(1)
# Igual que en z495: validation incluye todas las filas con training == 0.
mask_validation = dataset_train_cpu["training"].eq(0)

dtrain = lgb.Dataset(
    data=dataset_train_cpu.loc[mask_training, campos_buenos],
    label=dataset_train_cpu.loc[mask_training, "clase01"],
    feature_name=campos_buenos,
    free_raw_data=False,
)
dvalidate = lgb.Dataset(
    data=dataset_train_cpu.loc[mask_validation, campos_buenos],
    label=dataset_train_cpu.loc[mask_validation, "clase01"],
    feature_name=campos_buenos,
    free_raw_data=False,
)

print("Filas para training:", int(mask_training.sum()))
print("Filas para validation:", int(mask_validation.sum()))
print("Columnas:", len(campos_buenos))

# [Anotación · líneas 189–222] Función objetivo: sugiere cada hiperparámetro con la distribución recuperada
#   del estudio original, los combina con los parámetros fijos de PARAM.yml, entrena con num_iterations rondas
#   evaluando sobre validación y devuelve el valor de average_precision que queda en best_score.
#%% celda 8 [texto]
## Función objetivo

#%% celda 9 [código]
def objective(trial):
    parametros_variables = {}
    for nombre, distribucion in distribuciones.items():
        if isinstance(distribucion, IntDistribution):
            parametros_variables[nombre] = trial.suggest_int(
                nombre, *rangos_bo[nombre],
                step=distribucion.step, log=distribucion.log,
            )
        else:
            parametros_variables[nombre] = trial.suggest_float(
                nombre, *rangos_bo[nombre],
                step=distribucion.step, log=distribucion.log,
            )

    parametros_completos = {
        **PARAM["lgbm"]["param_fijos"],
        **parametros_variables,
    }
    num_boost_round = int(parametros_completos.pop("num_iterations"))

    modelo = lgb.train(
        params=parametros_completos,
        train_set=dtrain,
        num_boost_round=num_boost_round,
        valid_sets=[dvalidate],
        valid_names=["val"],
    )

    metrica = PARAM["lgbm"]["param_fijos"]["metric"]
    return float(modelo.best_score["val"][metrica])

# [Anotación · líneas 224–249] Crea la carpeta de salida y un estudio nuevo con GPSampler (semilla 230047,
#   n_startup_trials de PARAM.yml, objetivo no determinístico), guardado en SQLite y con la misma dirección que
#   el original. Si el estudio está vacío encola los puntos manuales. Escribe PARAM.yml en la carpeta nueva.
#%% celda 10 [texto]
## Nueva BO

#%% celda 11 [código]
os.makedirs(EXPERIMENT_URL, exist_ok=True)

sampler = GPSampler(
    seed=PARAM["semilla_primigenia"],
    n_startup_trials=n_startup_trials,
    deterministic_objective=False,
)
study_db_url = os.path.join(EXPERIMENT_URL, "optuna_study.db")
study = optuna.create_study(
    study_name=experiment_name,
    direction=study_original.direction,
    sampler=sampler,
    storage=f"sqlite:///{study_db_url}",
    load_if_exists=True,
)

if not study.trials:
    for punto in puntos_iniciales_bo:
        study.enqueue_trial(punto)

with open(os.path.join(EXPERIMENT_URL, "PARAM.yml"), "w", encoding="utf-8") as archivo:
    yaml.safe_dump(PARAM, archivo, sort_keys=False, allow_unicode=True)

# [Anotación · líneas 251–265] Cuenta los trials completos y ejecuta los que faltan hasta el total configurado
#   (60 iteraciones, 30 de inicio, en LAG-028/PARAM.yml).
#%% celda 12 [código]
trials_completos = sum(
    trial.state == TrialState.COMPLETE for trial in study.trials
)
trials_restantes = max(0, n_trials_total - trials_completos)

print("Trials completos:", trials_completos)
print("Trials restantes:", trials_restantes)

if trials_restantes > 0:
    study.optimize(
        objective,
        n_trials=trials_restantes,
        show_progress_bar=True,
    )

# [Anotación · líneas 267–285] Exporta los trials a BO_log.txt, ordenados de mayor a menor métrica y separados
#   por tabulador, y agrega a PARAM.yml los hiperparámetros del trial de mayor métrica y su valor.
#%% celda 13 [texto]
## Resultados

#%% celda 14 [código]
tb_bayesiana = study.trials_dataframe()
tb_bayesiana["iter"] = np.arange(1, len(tb_bayesiana) + 1)
tb_bayesiana = (
    tb_bayesiana.sort_values("value", ascending=False, na_position="last")
    .reset_index(drop=True)
)
tb_bayesiana.to_csv(
    os.path.join(EXPERIMENT_URL, "BO_log.txt"), sep="\t", index=False,
)

PARAM["out"]["lgbm"]["mejores_hiperparametros"] = dict(study.best_trial.params)
PARAM["out"]["lgbm"]["y"] = float(study.best_value)

with open(os.path.join(EXPERIMENT_URL, "PARAM.yml"), "w", encoding="utf-8") as archivo:
    yaml.safe_dump(PARAM, archivo, sort_keys=False, allow_unicode=True)
```

### entregas/bo/validacion_manual_lag009_replica.ipynb

Validación manual en R del modelo elegido en el benchmark de LAG-009: lo reentrena con 5 semillas, mide la ganancia en 202106 y guarda los parámetros por semilla en 40-REPLICA.rds.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–42] Presentación y carga de librerías, instalando las que falten: data.table, R.utils,
#   primes, rlist, yaml, lightgbm, DiceKriging, mlrMBO, here y ggplot2.
#%% celda 1 [texto]
# Réplica de la validación manual — LAG-009 / RDS 40

Ejecutar desde `entregas/bo`, con kernel R.

La entrada es `benchmark_multisemilla_lags20260924_114539-r`. El dataset, los meses, las semillas y las columnas excluidas son los de la validación manual original que produjo el RDS 40; se configuran en esta notebook.

Se conserva el código original que elige el mejor modelo del benchmark, construye sus parámetros, entrena y evalúa cada semilla. Se guardan `40.rds` y `validaciones_manuales_replica.csv` en `entregas/bo`.

# Librerias

#%% celda 2 [código]
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

library(here)
require("ggplot2")

# [Anotación · líneas 44–64] Rutas relativas a entregas/bo, dataset
#   competencia_01_ternaria_lf_k6_perdida4.csv, archivo de registro validaciones_manuales_replica.csv, semillas
#   230047, 230059, 230063, 230077 y 230081, e identificador 40-REPLICA.
#%% celda 3 [texto]
# URLS

#%% celda 4 [código]
# Ejecutar desde entregas/bo.
root <- getwd()
exp_folder <- root
data_folder <- file.path(dirname(root), "dataset")

dataset_file = 'competencia_01_ternaria_lf_k6_perdida4.csv'
dataset_url <- file.path(data_folder, dataset_file)
list.files(data_folder)

carpeta_man_val <- root
archivo_validaciones <- file.path(
  carpeta_man_val,
  "validaciones_manuales_replica.csv"
)

SEEDS <- c(230047, 230059, 230063, 230077, 230081)
id_validacion <- '40-REPLICA'

# [Anotación · líneas 66–118] Lee el dataset, lo ordena y cuenta filas por mes y clase; crea clase01 (BAJA+1 o
#   BAJA+2 = 1) y define las columnas de entrada quitando 16 nombres (los mismos de p005).
#%% celda 5 [texto]
# LEEMOS DATASET

#%% celda 6 [código]
# leo el dataset
dataset <- fread(dataset_url)

#%% celda 7 [código]
setorder( dataset, foto_mes, ternaria, numero_de_cliente)
dataset[, .N, list(foto_mes, ternaria)]

#%% celda 8 [código]
# colnames(dataset)

#%% celda 9 [texto]
# CLASE01

#%% celda 10 [código]
dataset[, clase01 := ifelse(ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)]

#%% celda 11 [texto]
# Columnas a usar

#%% celda 12 [código]
grep("prestamos_personales", colnames(dataset), value = TRUE, ignore.case = TRUE)
grep("ternaria", colnames(dataset), value = TRUE, ignore.case = TRUE)

#%% celda 13 [código]
columnas_excluir <-
c(
    "ternaria",
    "ternaria_lag1",
    "clase01",
    "fold",
    "azar",
    "training",
    "cprestamos_personales",
    "mprestamos_personales",
    "cprestamos_personales_lag1",
    "mprestamos_personales_lag1",
    "cprestamos_personales_delta1",
    "mprestamos_personales_delta1",
    "cprestamos_personales_lag_pond",
    "mprestamos_personales_lag_pond",
    "cprestamos_personales_delta_lag_pond",
    "mprestamos_personales_delta_lag_pond"
  )

#%% celda 14 [código]
campos_buenos <- setdiff(
  colnames(dataset),
  columnas_excluir  
)

# [Anotación · líneas 120–144] Indica la carpeta del benchmark replicado
#   (benchmark_multisemilla_lags20260924_114539-REPLICA) y los meses: entrenamiento 202103 y 202104, futuro
#   202106.
#%% celda 15 [texto]
# Experimento

#%% celda 16 [código]
# Carpeta generada por la validación multisemilla replicada.
carpeta_benchmarks <- exp_folder
writeLines(list.files(carpeta_benchmarks, pattern = "benchmark"))

#%% celda 17 [código]
benchmark_base <- "benchmark_multisemilla_lags20260924_114539-REPLICA"

#%% celda 18 [texto]
## Parametros

#%% celda 19 [código]

carpeta_benchmark <-file.path(
  carpeta_benchmarks,
  benchmark_base
)

#%% celda 20 [código]
train <- c(202103, 202104)
train_final <- c(202103, 202104)
future <- c(202106)

# [Anotación · líneas 146–177] Lee PARAM.rds del benchmark y, de mejor_corte_por_modelo.tsv, la fila de mayor
#   ganancia_total_promedio. Combina los parámetros fijos con los de esa fila, divide min_data_in_leaf por el
#   undersampling y toma la lista de cortes.
#%% celda 21 [código]

# Configuración utilizada durante la validación
PARAM_BENCH <- readRDS(
  file.path(carpeta_benchmark, "PARAM.rds")
)

# Lee los mejores resultados y selecciona el de mayor ganancia promedio
mejor_modelo <- data.table::fread(
  file.path(carpeta_benchmark, "mejor_corte_por_modelo.tsv")
)[which.max(ganancia_total_promedio)]

# Identifica qué columnas de la fila corresponden a parámetros de LightGBM
columnas_parametros <- intersect(
  names(PARAM_BENCH$lgbm$param_fijos),
  names(mejor_modelo)
)

# Combina los parámetros fijos con los del mejor modelo
params_completos <- modifyList(
  PARAM_BENCH$lgbm$param_fijos,
  as.list(mejor_modelo[, ..columnas_parametros])
)

# Ajusta min_data_in_leaf según el undersampling usado
params_completos$min_data_in_leaf <- round(
  params_completos$min_data_in_leaf /
    PARAM_BENCH$trainingstrategy$undersampling
)

#%% celda 22 [código]
cortes <-PARAM_BENCH$cortes

# [Anotación · líneas 179–188] Separa las filas de entrenamiento y las del mes futuro.
#%% celda 23 [texto]
## Dataset train y test

#%% celda 24 [código]
dataset_train <- dataset[foto_mes %in% train_final]
dataset_train[,.N, list(foto_mes, ternaria)]

#%% celda 25 [código]
# aplico el modelo a los datos sin clase
dfuture <- dataset[foto_mes %in% future]

# [Anotación · líneas 190–241] Para cada semilla entrena un LightGBM con todos los datos de entrenamiento,
#   predice el mes futuro, asigna 1.072.500 a cada BAJA+2 y -27.500 al resto, ordena por probabilidad y calcula
#   la ganancia acumulada; guarda el máximo de la curva y los parámetros usados. Al final promedia los máximos
#   de las 5 semillas.
#%% celda 26 [texto]
# Entreno

#%% celda 27 [código]
ganancias_semillas <- numeric(length(SEEDS))
curvas_semillas <- vector("list", length(SEEDS))
params_por_semilla <- setNames(vector("list", length(SEEDS)), as.character(SEEDS))

for (i in seq_along(SEEDS)) {
  params_semilla <- params_completos
  params_semilla$seed <- SEEDS[i]
  params_por_semilla[[i]] <- params_semilla

  dtrain_final <- lgb.Dataset(
    data= data.matrix(dataset_train[, campos_buenos, with= FALSE]),
    label= dataset_train[, clase01]
  )

  modelo_final <- lgb.train(
    data= dtrain_final,
    param= params_semilla
  )

  # hago el predict en los datos del futuro, y calculo la ganancia

  # aplico el modelo a los datos nuevos
  prediccion <- predict(
    modelo_final,
    data.matrix(dfuture[, campos_buenos, with= FALSE])
  )

  # calculo la ganancia en los datos ddel futuro para todos los cortes
  tb_prediccion <- dfuture[, list(numero_de_cliente, foto_mes,ternaria)]
  tb_prediccion[, prob := prediccion ]
  tb_prediccion[, gan := ifelse(ternaria == "BAJA+2", 1072500, -27500)]

  # lgb.save(modelo_final, "modelo.txt" )
  # Dibujo la curva de ganancia acumulada
  setorder(tb_prediccion, -prob)
  tb_prediccion[, ganancia_acumulada := cumsum(gan)]
  tb_prediccion[, pos := sequence(.N)]

  print(tb_prediccion|> head())

  ganancias_semillas[i] <- max(tb_prediccion$ganancia_acumulada)
  curvas_semillas[[i]] <- tb_prediccion[, list(
    pos, ganancia_acumulada, seed = SEEDS[i]
  )]
}

ganancia_promedio <- mean(ganancias_semillas)
tb_curvas <- rbindlist(curvas_semillas)

# [Anotación · líneas 243–261] Grafica la ganancia acumulada de cada semilla hasta la posición 30.000 e
#   imprime, para cada corte, la ganancia de los primeros clientes de la tabla de la última semilla del ciclo.
#%% celda 28 [código]
# defino hasta donde muestra el grafico
amostrar <- 30000
# observamos la curva de ganancia
gra <- ggplot(
           data= tb_curvas[pos <= amostrar],
           aes( x= pos, y= ganancia_acumulada, color= factor(seed))
             ) + geom_line() + labs(color = "Seed")

gra <- gra + theme(text = element_text(size = 16))

options(repr.plot.width=16, repr.plot.height=9)
print( gra )

#%% celda 29 [código]
for (envios in cortes) {
  ganancia <- tb_prediccion[1:envios, sum(gan)]
  cat( envios, "\t", ganancia, "\n")
}

# [Anotación · líneas 263–303] Agrega una fila a validaciones_manuales_replica.csv (identificador, ganancia
#   promedio, semillas, dataset, cantidades de filas, meses, columnas excluidas y benchmark) y guarda la lista
#   de parámetros por semilla en 40-REPLICA.rds.
#%% celda 30 [texto]
# Guardamos resultados

#%% celda 31 [código]
if (file.exists(archivo_validaciones)) {
  validaciones_previas <- fread(archivo_validaciones)
}

registro_validacion <- data.table(
  id_validacion = id_validacion,
  ganancia = ganancia_promedio,
  seeds = paste(SEEDS, collapse = ","),
  dataset = dataset_file,
  cantidad_registros_totales = nrow(dataset),
  cantidad_registros_entrenamiento = nrow(dataset_train),
  cantidad_registros_validacion = nrow(dfuture),
  meses_entrenamiento = paste(train_final, collapse = ","),
  meses_validacion = paste(future, collapse = ","),
  columnas_excluidas = paste(columnas_excluir, collapse = ","),
  benchmark_original = benchmark_base
)

# Incorpora seeds al histórico anterior si todavía no tiene esa columna.
if (file.exists(archivo_validaciones) && !("seeds" %in% names(validaciones_previas))) {
  validaciones_previas[, seeds := NA_character_]
  setcolorder(validaciones_previas, names(registro_validacion))
  fwrite(validaciones_previas, archivo_validaciones)
}

fwrite(
  registro_validacion,
  archivo_validaciones,
  append = file.exists(archivo_validaciones),
  col.names = !file.exists(archivo_validaciones)
)

# Guarda exactamente los parámetros enviados a lgb.train()
saveRDS(
  params_por_semilla,
  file.path(carpeta_man_val, paste0(id_validacion, ".rds"))
)

# [Anotación · líneas 305–310] Lee y muestra el histórico de validaciones.
#%% celda 32 [texto]
# Historico

#%% celda 33 [código]
historico <- fread(archivo_validaciones)
historico
```

### entregas/bo/validacion_multisemilla_lag028_replica.ipynb

Réplica en R del benchmark multisemilla de LAG-028; mismo código que la de LAG-009, con otro benchmark de origen y una lista de 25 columnas excluidas.

El código completo está en https://emavaldez.github.io/postmortem/fuentes/ssmito/entregas/bo/validacion_multisemilla_lag028_replica.ipynb.txt

### entregas/bo/lag009_replica.ipynb

Réplica de la optimización bayesiana LAG-009 con Optuna, de la que salen los hiperparámetros de parametros/40.rds (modelos 1 y 2). Lee la configuración y el estudio de bo/LAG-009/ y escribe en bo/LAG-009-REPLICA/.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] Presentación (réplica de la BO a partir de la configuración y los puntos iniciales
#   del experimento original) y carga de librerías: cudf, numpy, pandas, yaml, lightgbm, optuna con GPSampler y
#   train_test_split de scikit-learn.
#%% celda 1 [texto]
# Réplica de BO

Configuración y puntos iniciales recuperados del experimento original.
Ejecutar desde `entregas/bo`. Los resultados se guardan en una carpeta nueva.

Usa la lectura original con `cudf.read_csv()`: primero filtra los meses y luego convierte a pandas. Ejecutar con el kernel Python que tiene cuDF, como la BO original.

Para comparar una nueva ejecución desde el comienzo, configurar una carpeta de salida nueva. Los trials guardados en una carpeta existente se retoman; no se recalculan al cambiar el lector.

#%% celda 2 [código]
import os
import cudf
import numpy as np
import pandas as pd
import yaml
import lightgbm as lgb
import optuna

from sklearn.model_selection import train_test_split
from optuna.samplers import GPSampler
from optuna.distributions import IntDistribution
from optuna.trial import TrialState

# [Anotación · líneas 25–54] Define carpetas relativas a entregas/bo, el experimento de origen LAG-009, la
#   carpeta de salida LAG-009-REPLICA, el dataset competencia_01_ternaria_lags.csv y 12 columnas excluidas
#   (ternaria, ternaria_lag1, clase01, fold, azar, training y las dos de préstamos personales con sus _lag1 y
#   _delta1). Corta si origen y destino coinciden.
#%% celda 3 [código]
# Ejecutar con el directorio de trabajo en entregas/bo.
BO_URL = os.getcwd()
DATA_FOLDER = os.path.join(os.path.dirname(BO_URL), "dataset")

experimento_original = "LAG-009"
experiment_name = "LAG-009-REPLICA"
dataset_file = "competencia_01_ternaria_lags.csv"

columnas_excluidas = {
    "ternaria",
    "ternaria_lag1",
    "clase01",
    "fold",
    "azar",
    "training",
    "cprestamos_personales",
    "cprestamos_personales_lag1",
    "cprestamos_personales_delta1",
    "mprestamos_personales",
    "mprestamos_personales_lag1",
    "mprestamos_personales_delta1",
}

ORIGEN_URL = os.path.join(BO_URL, experimento_original)
EXPERIMENT_URL = os.path.join(BO_URL, experiment_name)
DATA_LAGS_URL = os.path.join(DATA_FOLDER, dataset_file)

if os.path.abspath(ORIGEN_URL) == os.path.abspath(EXPERIMENT_URL):
    raise ValueError("El destino debe ser distinto del experimento original.")

# [Anotación · líneas 56–105] Lee PARAM.yml del experimento original y abre su estudio de Optuna
#   (optuna_study.db). De los trials recupera la distribución de cada hiperparámetro (límites, tipo, paso y
#   escala logarítmica) y los puntos que se habían encolado a mano (fixed_params). Actualiza PARAM con el nombre
#   nuevo, el dataset, las exclusiones y los rangos, e imprime meses, métrica y cantidades de trials.
#%% celda 4 [texto]
## Configuración original

#%% celda 5 [código]
with open(os.path.join(ORIGEN_URL, "PARAM.yml"), encoding="utf-8") as archivo:
    PARAM = yaml.safe_load(archivo)

study_db_original = os.path.join(ORIGEN_URL, "optuna_study.db")
study_original = optuna.load_study(
    study_name=PARAM["experimento"],
    storage=f"sqlite:///{study_db_original}",
)

# Recuperar límites, tipos, pasos y escala logarítmica.
distribuciones = {}
for trial in study_original.trials:
    distribuciones.update(trial.distributions)

rangos_bo = {
    nombre: (distribucion.low, distribucion.high)
    for nombre, distribucion in distribuciones.items()
}

# Puntos agregados a mano, en el mismo orden del estudio original.
puntos_iniciales_bo = [
    trial.system_attrs["fixed_params"].copy()
    for trial in study_original.trials
    if "fixed_params" in trial.system_attrs
]

PARAM["experimento"] = experiment_name
PARAM["dataset"] = dataset_file
PARAM["columnas_excluidas"] = sorted(columnas_excluidas)
PARAM["rangos_bo"] = {nombre: list(rango) for nombre, rango in rangos_bo.items()}
PARAM["out"]["lgbm"] = {}

# Parámetros editables antes de ejecutar las celdas siguientes:
# PARAM["train"], PARAM["training_pct"], PARAM["semilla_primigenia"]
# PARAM["trainingstrategy"]["undersampling"]
# PARAM["lgbm"]["param_fijos"]
# PARAM["hyperparametertuning"]["n_startup_trials"]
# PARAM["hyperparametertuning"]["iteraciones"]
# rangos_bo, puntos_iniciales_bo

n_startup_trials = PARAM["hyperparametertuning"]["n_startup_trials"]
n_trials_total = PARAM["hyperparametertuning"]["iteraciones"]
print("Meses:", PARAM["train"])
print("Métrica:", PARAM["lgbm"]["param_fijos"]["metric"])
print("Puntos manuales:", len(puntos_iniciales_bo))
print("Inicialización:", n_startup_trials, "| Total:", n_trials_total)

# [Anotación · líneas 107–144] Lee el CSV con cudf, se queda con los meses de PARAM['train'] (202104 en
#   LAG-009/PARAM.yml) y pasa a pandas. Parte las filas en fold 1 (70%) y fold 2 con train_test_split
#   estratificado por ternaria y semilla 230047. Crea clase01 (BAJA+1 o BAJA+2 = 1), un número al azar por fila
#   y la marca training: filas del fold 1 que son baja o cuyo número al azar es menor o igual a 0,1
#   (undersampling).
#%% celda 6 [texto]
## Dataset y partición

#%% celda 7 [código]
df = cudf.read_csv(
    DATA_LAGS_URL,
    dtype={"numero_de_cliente": "int32", "foto_mes": "int32"},
)
dataset_train_cpu = (
    df.loc[df["foto_mes"].isin(PARAM["train"])]
    .to_pandas()
    .reset_index(drop=True)
)
del df

indices_fold_1, indices_fold_2 = train_test_split(
    np.arange(len(dataset_train_cpu)),
    train_size=PARAM["training_pct"] / 100,
    stratify=dataset_train_cpu["ternaria"],
    random_state=PARAM["semilla_primigenia"],
)

dataset_train_cpu["fold"] = np.int8(2)
dataset_train_cpu.loc[indices_fold_1, "fold"] = np.int8(1)
dataset_train_cpu["clase01"] = (
    dataset_train_cpu["ternaria"].isin(["BAJA+1", "BAJA+2"])
    .astype(np.int8)
)

rng = np.random.default_rng(PARAM["semilla_primigenia"])
dataset_train_cpu["azar"] = rng.random(len(dataset_train_cpu))
dataset_train_cpu["training"] = (
    dataset_train_cpu["fold"].eq(1)
    & (
        (dataset_train_cpu["azar"] <= PARAM["trainingstrategy"]["undersampling"])
        | dataset_train_cpu["ternaria"].isin(["BAJA+1", "BAJA+2"])
    )
).astype(np.int8)

# [Anotación · líneas 146–170] Arma la lista de columnas de entrada y dos lgb.Dataset: entrenamiento con las
#   filas training == 1 y validación con todas las filas training == 0 (el fold 2 y las filas del fold 1 que el
#   submuestreo dejó afuera). Imprime las cantidades.
campos_buenos = [
    columna for columna in dataset_train_cpu.columns
    if columna not in columnas_excluidas
]

mask_training = dataset_train_cpu["training"].eq(1)
# Igual que en z495: validation incluye todas las filas con training == 0.
mask_validation = dataset_train_cpu["training"].eq(0)

dtrain = lgb.Dataset(
    data=dataset_train_cpu.loc[mask_training, campos_buenos],
    label=dataset_train_cpu.loc[mask_training, "clase01"],
    feature_name=campos_buenos,
    free_raw_data=False,
)
dvalidate = lgb.Dataset(
    data=dataset_train_cpu.loc[mask_validation, campos_buenos],
    label=dataset_train_cpu.loc[mask_validation, "clase01"],
    feature_name=campos_buenos,
    free_raw_data=False,
)

print("Filas para training:", int(mask_training.sum()))
print("Filas para validation:", int(mask_validation.sum()))
print("Columnas:", len(campos_buenos))

# [Anotación · líneas 172–205] Función objetivo: sugiere cada hiperparámetro con la distribución recuperada
#   del estudio original, los combina con los parámetros fijos de PARAM.yml, entrena con num_iterations rondas
#   evaluando sobre validación y devuelve el valor de average_precision que queda en best_score.
#%% celda 8 [texto]
## Función objetivo

#%% celda 9 [código]
def objective(trial):
    parametros_variables = {}
    for nombre, distribucion in distribuciones.items():
        if isinstance(distribucion, IntDistribution):
            parametros_variables[nombre] = trial.suggest_int(
                nombre, *rangos_bo[nombre],
                step=distribucion.step, log=distribucion.log,
            )
        else:
            parametros_variables[nombre] = trial.suggest_float(
                nombre, *rangos_bo[nombre],
                step=distribucion.step, log=distribucion.log,
            )

    parametros_completos = {
        **PARAM["lgbm"]["param_fijos"],
        **parametros_variables,
    }
    num_boost_round = int(parametros_completos.pop("num_iterations"))

    modelo = lgb.train(
        params=parametros_completos,
        train_set=dtrain,
        num_boost_round=num_boost_round,
        valid_sets=[dvalidate],
        valid_names=["val"],
    )

    metrica = PARAM["lgbm"]["param_fijos"]["metric"]
    return float(modelo.best_score["val"][metrica])

# [Anotación · líneas 207–232] Crea la carpeta de salida y un estudio nuevo con GPSampler (semilla 230047,
#   n_startup_trials de PARAM.yml, objetivo no determinístico), guardado en SQLite y con la misma dirección que
#   el original. Si el estudio está vacío encola los puntos manuales. Escribe PARAM.yml en la carpeta nueva.
#%% celda 10 [texto]
## Nueva BO

#%% celda 11 [código]
os.makedirs(EXPERIMENT_URL, exist_ok=True)

sampler = GPSampler(
    seed=PARAM["semilla_primigenia"],
    n_startup_trials=n_startup_trials,
    deterministic_objective=False,
)
study_db_url = os.path.join(EXPERIMENT_URL, "optuna_study.db")
study = optuna.create_study(
    study_name=experiment_name,
    direction=study_original.direction,
    sampler=sampler,
    storage=f"sqlite:///{study_db_url}",
    load_if_exists=True,
)

if not study.trials:
    for punto in puntos_iniciales_bo:
        study.enqueue_trial(punto)

with open(os.path.join(EXPERIMENT_URL, "PARAM.yml"), "w", encoding="utf-8") as archivo:
    yaml.safe_dump(PARAM, archivo, sort_keys=False, allow_unicode=True)

# [Anotación · líneas 234–248] Cuenta los trials completos y ejecuta los que faltan hasta el total configurado
#   (200 iteraciones, 50 de inicio, en LAG-009/PARAM.yml).
#%% celda 12 [código]
trials_completos = sum(
    trial.state == TrialState.COMPLETE for trial in study.trials
)
trials_restantes = max(0, n_trials_total - trials_completos)

print("Trials completos:", trials_completos)
print("Trials restantes:", trials_restantes)

if trials_restantes > 0:
    study.optimize(
        objective,
        n_trials=trials_restantes,
        show_progress_bar=True,
    )

# [Anotación · líneas 250–268] Exporta los trials a BO_log.txt, ordenados de mayor a menor métrica y separados
#   por tabulador, y agrega a PARAM.yml los hiperparámetros del trial de mayor métrica y su valor.
#%% celda 13 [texto]
## Resultados

#%% celda 14 [código]
tb_bayesiana = study.trials_dataframe()
tb_bayesiana["iter"] = np.arange(1, len(tb_bayesiana) + 1)
tb_bayesiana = (
    tb_bayesiana.sort_values("value", ascending=False, na_position="last")
    .reset_index(drop=True)
)
tb_bayesiana.to_csv(
    os.path.join(EXPERIMENT_URL, "BO_log.txt"), sep="\t", index=False,
)

PARAM["out"]["lgbm"]["mejores_hiperparametros"] = dict(study.best_trial.params)
PARAM["out"]["lgbm"]["y"] = float(study.best_value)

with open(os.path.join(EXPERIMENT_URL, "PARAM.yml"), "w", encoding="utf-8") as archivo:
    yaml.safe_dump(PARAM, archivo, sort_keys=False, allow_unicode=True)
```


## Explicaciones del alumno (texto original)

### entregas/readme.md

> # Entrega 1
>
> ## 1. ENTREGA
>
> Ejecutar `entregas/p005_3models_runner.ipynb` desde `entregas/`. Necesita los datasets generados y los `.rds` originales con los hiperparámetros de los modelos, ya copiados a `entregas/parametros/`.
>
> Correr toda la notebook como está, en orden, hasta el punto anterior a **Documentación**. Entrena los 3 modelos con 50 semillas, combina las predicciones y guarda el CSV de entrega en `entregas/entregas/`.
>
> **carga 3 datasets en memoria, local con 64 gb de ram no tuve OOM**
>
>
> ## 2. DATASETS
>
> Punto de partida: colocar `competencia_01_crudo.csv` en `entregas/dataset/`, junto a las dos notebooks.
>
> Desde `entregas/dataset/`, ejecutar completas, como están:
>
> 1. `versiones_dataset_1.ipynb`: genera los datasets necesarios para la cadena de LAG-009.
> 2. `versiones_dataset_2.ipynb`: genera los demás datasets utilizados en la entrega.
>
> **Sí, soy consciente q en LAG-009 los HP son encontrados para un dataset y en las predicciones los uso con 2 datasets diferentes, pero con varias BO no pude mejorar los resultados de esos mismos HP incluso para los otros datasets, y los resultados mandan**
>
> ## 3. BO
>
> Ejecutar los tres pasos desde `entregas/bo`, con kernel Python para las BO y kernel R para las validaciones.
>
> 1. **Replicar las BO:** `lag009_replica.ipynb` y `lag028_replica.ipynb` toman los parámetros, rangos y puntos iniciales de las carpetas originales `LAG-009/` y `LAG-028/` y reproducen la optimización en `LAG-009-REPLICA/` y `LAG-028-REPLICA/`.
> 2. **Replicar el benchmark multisemilla:** `validacion_multisemilla_lag009_replica.ipynb` y `validacion_multisemilla_lag028_replica.ipynb` toman la configuración de los benchmarks originales, evalúan los modelos de las BO replicadas con varias semillas y seleccionan sus mejores cortes.
> 3. **Replicar los `.rds`:** `validacion_manual_lag009_replica.ipynb` y `validacion_manual_lag028_replica.ipynb` toman el modelo elegido de cada benchmark replicado y generan `40-REPLICA.rds` y `62-REPLICA.rds`. Sus referencias originales son `entregas/parametros/40.rds` y `entregas/parametros/62.rds`, utilizados para la entrega.
>
> Las carpetas de benchmark originales contienen los resultados de referencia; las réplicas generan sus salidas en las carpetas con sufijo `-REPLICA`:
>
> | BO | Benchmark original en `entregas/bo/` | Benchmark replicado en `entregas/bo/` |
> | --- | --- | --- |
> | LAG-009 | `benchmark_multisemilla_lags20260924_114539/` | `benchmark_multisemilla_lags20260924_114539-REPLICA/` |
> | LAG-028 | `benchmark_multisemilla_lags20261009_200322/` | `benchmark_multisemilla_lags20261009_200322-REPLICA/` |
>
> Cada benchmark replicado guarda `PARAM.rds` y `mejor_corte_por_modelo.tsv`, los dos archivos necesarios para crear el `.rds` de parámetros.

