# Clari — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: ClariRZ
- Repositorio: https://github.com/ClariRZ/Primera-compentencia
- Link posteado: https://github.com/ClariRZ/Primera-compentencia/tree/main
- Commit: 03ba3f3ed29edc31ff42a5947c584404f631f3b8
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/clarirz/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/clarirz.json

## Resumen

Repositorio en Python con cinco carpetas numeradas que se ejecutan en orden y un README por carpeta. El paso 1 arma `clase_ternaria` con DuckDB y guarda un Parquet. El paso 2 genera un banco de variables derivadas por bloques y define el conjunto C3: las 152 variables originales más 1.910 derivadas (historia con lag 1 y ventana 2, y sumas y cocientes de tarjetas). El paso 3 agrupa a los 4.067 clientes BAJA+2 de 202103–202106 en cinco grupos con un Random Forest y KMeans. El paso 4 encadena cuatro corridas: Q0 y B1 (variables con un mes anómalo pasadas a NA, evaluadas en 202106), SUPERFINAL (compara conjuntos de variables y pesos por mes, busca hiperparámetros con 20 trials de Optuna entrenando 202103 y midiendo ganancia en 202105, y fija el corte con 20 semillas en 202106) y CLAW2, que entrena 20 LightGBM binarios (BAJA+2 contra el resto) sobre 202103–202106 con los hiperparámetros de SUPERFINAL y un peso por fila para los BAJA+2 según su grupo, promedia las probabilidades de 202108 y escribe los 13.500 clientes de mayor probabilidad. El paso 5 contiene un verificador del CSV y la transcripción del manifiesto de la corrida. Cada corrida verifica hashes y resultados de la anterior antes de seguir. El repositorio no incluye datos, modelos ni el CSV entregado.

**Qué entrega.** Un CSV de una columna, sin encabezado, con 13.500 `numero_de_cliente` de 202108 ordenados de menor a mayor. Según el README, el archivo enviado es `C1CLAW2C065771C9ENS13500.csv` y su ganancia pública fue 101,0900 M ARS. El archivo no está en el repositorio: lo escribe `run_cluster_aware.py` en `$HOME/c1clusteraware01/stage4_august/delivery/`.

**Cómo se ejecuta.** El README indica clonar, crear un entorno con Python 3.12 e instalar `requirements.lock` y `requirements-z501.txt`, y correr en orden: (1) `1_dataset/preparar_competencia.py --workdir $HOME/c1m1femasiva03/datos`; (2) copiar `2_variables` a `$HOME/c1m1femasiva03_s3/paquete_c1` y ejecutar `run_screening.py --solo-generar-fe` y `run_s3_confirm_c3.py`; (3) `3_grupos_baja2/validar_clusters_estabilidad.py --data … --out $HOME/z501`; (4) `run_q0.py` con `--preflight`, `--prepare`, `--canary` y `--execute`, luego `run_superfinal100_v2_safe.py --home $HOME --all` y `auditar_superfinal100_v2.py --home $HOME`, y con `export CLAW2_REPLICA=1`, `run_cluster_aware.py --home $HOME --labels-cluster $HOME/z501/reference_labels.csv --phase all` y `audit_cluster_aware.py`; (5) `5_prediccion_final/verificar_csv_final.py` con `--sha256` y `--n 13500`. Cada carpeta tiene un README con sus comandos.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM, Random Forest, KMeans
- **Clase que entrena:** Binaria: positivo = BAJA+2; negativo = BAJA+1 y CONTINUA juntos (`clase_ternaria.eq("BAJA+2")`). La `clase_ternaria` se arma en el paso 1 según la presencia del cliente uno y dos meses después; un cliente que falta el mes siguiente y vuelve al subsiguiente queda como CONTINUA. Según el README, antes se probaron "ambas bajas contra CONTINUA" y "BAJA+2 contra CONTINUA sin los BAJA+1"; ese código no está en el repositorio.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202105, 202106
- **Mes que predice:** 202108
- **Submuestreo:** El LightGBM final entrena con todas las filas de 202103–202106, sin submuestreo. Sólo el Random Forest del paso 3 usa una muestra: todos los clientes con algún BAJA+2 y una cantidad igual de clientes presentes en los seis meses sin ninguna baja, elegidos por orden de `hash(numero_de_cliente + 214363)`.
- **Calidad de datos:** Q0 pasa `ccajas_depositos` de 202105 a NA y B1 prueba cuatro combinaciones más con `Visa_fultimo_cierre` y `Master_fultimo_cierre` de 202106, puntuando 202106 con los 20 modelos ya entrenados. La etapa 0 de SUPERFINAL toma el brazo que B1 promueve o, si ninguno pasa la regla, el dataset original; el banco final de variables se genera desde ese dataset. El repositorio no indica qué brazo quedó en la corrida original. El generador de variables reemplaza infinitos por NaN y deja NaN donde una derivada no se puede calcular.
- **Drifting:** No se observa en el código del camino de la entrega. El banco de variables incluye un bloque `ranks` (percentil de cada variable dentro del mes) que se compara como brazo en el paso 2 y en la etapa 1 de SUPERFINAL; el conjunto C3 no lo incluye.
- **Variables dentro del mes:** En C3, los bloques `ratios` y `tarjetas`: monto por operación (monto/cantidad) para 27 conceptos; para 16 campos de tarjeta, suma Visa + Master, diferencia Visa − Master y cantidad de marcas con dato, y fracción de Visa en 5 de ellos; por marca, consumo/límite de compra, saldo/límite de financiación y pagado/pago mínimo; indicadores de tenencia con y sin uso para Visa, Master y débito; y cantidad de marcas con cuenta y con uso.
- **Variables históricas:** Con `config_screening.json` (lags [1], ventanas [2]): para cada variable numérica, lag 1, delta 1, delta simétrico 1 y, en flujos no negativos y conteos, cambio relativo 1; seis indicadores de transición de t−1 a t; meses desde el último valor no cero y rachas de ceros y de no ceros; para las categóricas, código del mes anterior, cambio, racha y resúmenes de ventana 2; y lag 1, delta 1, transiciones y media, mínimo y máximo de ventana 2 de resúmenes como la cantidad de funciones activas o el saldo total de préstamos. Los bloques `ventanas` y `tendencias` están definidos en `fe_univariadas.py` y no se guardan en el banco.
- **Selección de variables:** Por familias de bloques: C3 = bloques de historia con al menos un mes de historia más los bloques `tarjetas` y `ratios` sin historia (`plan_s2_familias.json`, `run_s3_confirm_c3.py`). La etapa 1 de SUPERFINAL compara C3 contra 9 variantes (sin las tres cantidades de préstamos, con disponibilidad, con percentiles, con estados) y, según el README, quedó C3 con 2.062 variables. `run_screening.py` calcula además una lista de 20 derivadas por brazo según su rango de importancia, que ningún otro script del repositorio lee.
- **Optimización de hiperparámetros:** Optuna con `TPESampler(seed=17)`, 20 trials guardados en SQLite. Cada trial entrena un LightGBM con semilla 17 sobre 202103 y mide en 202105 la ganancia promedio de la terna de cortes consecutivos de mayor promedio (grilla 8.000–15.000 de a 500). Espacio: learning_rate 0,015–0,06 (log), num_leaves 24–128, min_data_in_leaf 100–1.200 (log), feature_fraction 0,55–1, bagging_fraction 0,65–1, lambda_l1 1e-8–5 (log), lambda_l2 1e-8–10 (log), max_bin en {63, 127, 255} y rondas 200–550. Los 3 trials de mayor valor se reentrenan con 202103–202104 y 5 semillas (1304, 1405, 1506, 1607 y 1708) y se comparan en 202106 contra los parámetros base de `config.yaml`. CLAW2 no repite la búsqueda.
- **Hiperparámetros finales:** Leídos en ejecución desde el resultado de la etapa 3 de SUPERFINAL. Según el manifiesto transcripto: objective binary, metric binary_logloss, boosting_type gbdt, learning_rate 0,015386775172063426, num_leaves 79, min_data_in_leaf 551, feature_fraction 0,6866382166758678, bagging_fraction 0,6525364259464963, bagging_freq 1, max_bin 63, lambda_l1 5,72231579234109e-06, lambda_l2 0,013648797015113241, force_col_wise true, deterministic true, num_threads 6 y 361 rondas (trial 11 de `trials.csv`).
- **Semillas:** 20 semillas escritas en el código: 17, 101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203, 1304, 1405, 1506, 1607, 1708, 1809 y 1910. Cada modelo construye su propio `lgb.Dataset` con la semilla también en los parámetros del dataset. El Random Forest y el KMeans del paso 3 usan la semilla 214363.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio aritmético de las probabilidades de 202108 de los 20 modelos, que comparten variables e hiperparámetros y difieren en la semilla. Según el README, también se probaron promedios de modelos con hiperparámetros distintos y mezclas con modelos anteriores; ese código no está en el repositorio.
- **Corte:** Cantidad fija de 13.500 clientes (`N_FIXED` en `cluster_aware_common.py`). El valor proviene de la etapa 4 de SUPERFINAL: centro de la terna de cortes consecutivos de mayor ganancia promedio en la curva del promedio de 20 semillas sobre 202106, con grilla 8.000–15.000 de a 500. CLAW2 exige que ese resultado sea 13.500 y no evalúa otros cortes.
- **Validación:** En meses posteriores y con la ganancia de la competencia (1.072.500 por BAJA+2 incluido y −27.500 por el resto): entrenamiento 202103–202104 con evaluación en 202106, y entrenamiento 202103 con evaluación en 202105 (Optuna y primera prueba de pesos por grupo). Las comparaciones son pareadas por semilla contra un control, con reglas escritas en el código (diferencia media y mediana positivas y un mínimo de semillas a favor: 2 de 3, 3 de 5 o 14 de 20). Antes de comparar, un modelo de control tiene que reproducir los puntajes guardados de la corrida anterior (tolerancia 1e-12 en Q0, igualdad exacta en SUPERFINAL y CLAW2).
- **Salidas:** Todo se escribe en carpetas fijas de `$HOME`: `competencia_01.parquet`; el banco de variables en partes Parquet con `catalogo_features.csv` y `manifest.json`; `reference_labels.csv`; por cada etapa un `RESULT.json`, puntajes por semilla en `.npz`, modelos `modelo_<semilla>.txt` y tablas CSV de comparación; `trials.csv` y `optuna.db`; y en `c1clusteraware01/stage4_august/delivery/` el CSV final, `MANIFEST.json` y `mensaje_zulip.txt` con el texto `submit <nombre>`. Ningún script envía el archivo.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Random Forest (`modelo.random_forest`)
- Otro modelo (`modelo.otro_modelo`)
- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Mínimos y máximos de ventana (`variables.min_max_ventana`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Técnicas sólo exploradas

- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: Python 3.12 en una máquina Linux con 56 GB de RAM y 6 hilos, según el README y `4_modelo/README.md`. `requirements.lock` fija 20 paquetes con versión exacta (entre ellos lightgbm 4.7.0, optuna 4.9.0, pandas 2.2.3, numpy 2.3.5 y pyarrow 25.0.1); `requirements-z501.txt` agrega duckdb y scikit-learn sin versión. El código lee `/proc/meminfo`, exige 56 GiB de memoria total para SUPERFINAL y usa carpetas con nombre fijo dentro de `$HOME` (configurable con `--home`); los destinos de Cloud Storage están reemplazados por un texto fijo y esas copias se omiten.

## Pasos del camino de la entrega

1. **Clase ternaria y Parquet.** `preparar_competencia.py` lee el CSV crudo con DuckDB (lo descarga si no está), marca la presencia de cada cliente en cada mes y asigna `clase_ternaria` según esté uno y dos meses después. Guarda `competencia_01.parquet` y una tabla de filas por mes y clase. (`1_dataset/preparar_competencia.py` líneas 24–77)
2. **Banco de variables derivadas.** `run_screening.py --solo-generar-fe` verifica el SHA-256 del dataset y llama a `generate`, que arma un panel por cliente y mes y calcula variables por bloques con lag 1 y ventana 2: historia de cada variable (valor anterior, delta, cambio relativo, transiciones y rachas), monto por operación y combinaciones de los campos de Visa y Master. Guarda las variables de 202103–202106 en partes Parquet con un catálogo y un manifiesto; la historia se calcula con todos los meses del archivo. (`2_variables/experimentos_20261006_m1_fe_masiva/run_screening.py` líneas 28–42; `2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/generar_fe.py` líneas 52–149; `2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_core.py` líneas 39–60; `2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_univariadas.py` líneas 81–116; `2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_relaciones.py` líneas 169–258)
3. **Conjunto C3 y su confirmación.** `run_s3_confirm_c3.py` define C3 como las 152 variables originales más las derivadas de los bloques de historia (con al menos un mes de historia) y de los bloques `tarjetas` y `ratios` (sin historia). Entrena con 202103–202104 y evalúa en 202106, con 20 semillas y 300 rondas, un modelo con las variables originales y otro con C3, y guarda la lista ordenada de variables (`features.json`), los puntajes por semilla y `confirmacion_c3.json` con la regla de promoción. Los scripts de `4_modelo/` exigen 2.062 variables, 1.910 de ellas derivadas. (`2_variables/experimentos_20261006_m1_fe_masiva/run_s3_confirm_c3.py` líneas 28–46; `2_variables/experimentos_20261006_m1_fe_masiva/run_s3_confirm_c3.py` líneas 84–135; `2_variables/experimentos_20261006_m1_fe_masiva/run_s3_confirm_c3.py` líneas 137–172)
4. **Grupos de clientes BAJA+2.** `validar_clusters_estabilidad.py` arma una muestra con los clientes que tienen algún BAJA+2 y una cantidad igual de clientes presentes en todos los meses sin bajas, entrena un Random Forest de 300 árboles para separarlos, resume a cada cliente BAJA+2 por las variables de los últimos cortes de las hojas en que caen sus filas y agrupa esos perfiles con KMeans (k = 5). Escribe `reference_labels.csv` con cliente y grupo, numerados de mayor a menor tamaño. Lo que sigue en el script son controles de estabilidad. (`3_grupos_baja2/validar_clusters_estabilidad.py` líneas 27–65; `3_grupos_baja2/validar_clusters_estabilidad.py` líneas 121–131; `3_grupos_baja2/eda_clusters_profundo.py` líneas 73–94)
5. **Q0: reproducción de C3 y `ccajas_depositos` en NA.** `run_q0.py` crea una copia del dataset con `ccajas_depositos` de 202105 en NA y un banco de variables sobre ella. Para cada una de las 20 semillas entrena el modelo de C3 (202103–202104, 300 rondas), exige que reproduzca los puntajes de 202106 guardados por `run_s3_confirm_c3.py` con diferencia máxima de 1e-12, guarda el modelo y puntúa 202106 corregido. Compara ganancias por semilla y deja `LISTO.json`. (`4_modelo/experimentos_20261007_post_c3/02_q0_ccajas_na/run_q0.py` líneas 193–240; `4_modelo/experimentos_20261007_post_c3/02_q0_ccajas_na/run_q0.py` líneas 396–452; `4_modelo/experimentos_20261007_post_c3/02_q0_ccajas_na/run_q0.py` líneas 504–601)
6. **B1: otras variables con un mes anómalo.** `run_b1.py`, lanzado por la etapa 0 de SUPERFINAL, arma cuatro copias del dataset con `Visa_fultimo_cierre` y/o `Master_fultimo_cierre` de 202106 en NA (una también con `ccajas_depositos` de 202105), genera las variables de 202106 de cada una y las puntúa con los 20 modelos de Q0 sin reentrenar. Para cada brazo elige la terna de cortes consecutivos de mayor ganancia promedio y lo compara con C3 original; `RESUMEN.json` indica el brazo promovido o C3_ORIG. (`4_modelo/experimentos_20261007_post_c3/04_b1_variables_rotas/run_b1.py` líneas 46–55; `4_modelo/experimentos_20261007_post_c3/04_b1_variables_rotas/run_b1.py` líneas 252–268; `4_modelo/experimentos_20261007_post_c3/04_b1_variables_rotas/run_b1.py` líneas 400–446; `4_modelo/experimentos_20261007_post_c3/04_b1_variables_rotas/run_b1.py` líneas 488–606)
7. **SUPERFINAL: canary y etapa 0.** `run_superfinal100_v2_safe.py --all` configura la versión 2 (un `lgb.Dataset` por semilla) y primero exige que C3 con la semilla 17 reproduzca de forma idéntica los puntajes guardados por `run_s3_confirm_c3.py`. La etapa 0 lee el brazo promovido por B1 y fija con qué dataset y con qué banco de evaluación siguen las etapas. (`4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100_v2_safe.py` líneas 1–10; `4_modelo/experimentos_20261007_post_c3/05_superfinal100/superfinal100_v2.py` líneas 55–81; `4_modelo/experimentos_20261007_post_c3/05_superfinal100/superfinal100_v2.py` líneas 181–217; `4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100.py` líneas 113–149)
8. **SUPERFINAL etapa 1: conjunto de variables.** Compara 10 conjuntos (C3, C3 sin las cantidades de préstamos y variantes con disponibilidad, percentiles o estados del mes) entrenando 202103–202104 y evaluando en 202106 con parámetros base y 300 rondas: 3 semillas para todos y 5 semillas distintas para C3 y tres más. Un conjunto reemplaza a C3 sólo si su ganancia de meseta es mayor, la diferencia pareada media y mediana son positivas y gana en al menos 3 de 5 semillas. Según el README, quedó C3. (`4_modelo/experimentos_20261007_post_c3/05_superfinal100/super_common.py` líneas 265–312; `4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100.py` líneas 152–306)
9. **SUPERFINAL etapa 2: peso por mes.** Con las variables elegidas compara cuatro políticas de peso por mes de entrenamiento (202103 con peso 1, 0,5, 0,25 o 0 frente a 202104 con peso 1) con 5 semillas en 202106. Sin una política promovida queda EXPANDING, que en el entrenamiento final da peso 1 a los cuatro meses. El manifiesto transcripto registra EXPANDING. (`4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100.py` líneas 41–52; `4_modelo/experimentos_20261007_post_c3/05_superfinal100/superfinal100_v2.py` líneas 220–292)
10. **SUPERFINAL etapa 3: Optuna.** Un estudio de Optuna con `TPESampler(seed=17)` corre 20 trials; cada uno entrena con 202103 y semilla 17 y devuelve la ganancia promedio de la meseta elegida en 202105. Los tres trials de mayor valor y los parámetros base se entrenan con 202103–202104 y 5 semillas y se comparan en 202106; queda el candidato promovido de mayor ganancia de meseta o, si ninguno pasa, los parámetros base. Según el README de la carpeta, quedó el trial 11 (361 rondas). (`4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100.py` líneas 398–431; `4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100.py` líneas 434–545)
11. **SUPERFINAL etapa 4: 20 semillas y corte.** Entrena el candidato con las 20 semillas sobre 202103–202104 y lo compara en 202106 con los 20 puntajes de C3 guardados por `run_s3_confirm_c3.py`. El corte `n_final` es el centro de la terna de cortes consecutivos de mayor ganancia promedio en la curva del promedio de semillas (grilla 8.000–15.000 de a 500). La versión 2 exige al menos 14 de 20 semillas a favor para continuar. Según el README, el corte resultó 13.500. (`4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100.py` líneas 548–612; `4_modelo/experimentos_20261007_post_c3/05_superfinal100/super_common.py` líneas 128–145; `4_modelo/experimentos_20261007_post_c3/05_superfinal100/superfinal100_v2.py` líneas 295–310)
12. **SUPERFINAL etapa 5 y auditoría.** Genera el banco final de variables para 202103–202106 y 202108 desde el dataset de la etapa 0, entrena 20 modelos con los cuatro meses y exporta su propio CSV (`C1SF2…`). `auditar_superfinal100_v2.py` reconstruye el promedio desde los 20 puntajes, lo compara con el CSV y escribe `AUDITORIA_FINAL.json`. El modelo final reutiliza de esta corrida la lista de variables, los parámetros, las rondas, la política de pesos por mes, el banco final y los puntajes de 202106 como control. (`4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100.py` líneas 623–649; `4_modelo/experimentos_20261007_post_c3/05_superfinal100/stage5_v2_safe.py` líneas 84–127; `4_modelo/experimentos_20261007_post_c3/05_superfinal100/stage5_v2_safe.py` líneas 150–235; `4_modelo/experimentos_20261007_post_c3/05_superfinal100/auditar_superfinal100_v2.py` líneas 144–158)
13. **CLAW2: controles de entrada y pesos por grupo.** `run_cluster_aware.py` exige la auditoría de SUPERFINAL, el corte 13.500 y que `reference_labels.csv` contenga exactamente los 4.067 clientes BAJA+2 de 202103–202106. `make_weights` multiplica el peso de cada fila BAJA+2 por un valor de su grupo y reescala para que la suma de pesos de los BAJA+2 no cambie. En el brazo BALANCED_CAPPED el multiplicador es la mediana de las masas de los grupos dividida por la masa del grupo, limitada entre 0,5 y 4. (`4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/run_cluster_aware.py` líneas 79–99; `4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/run_cluster_aware.py` líneas 233–272; `4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/cluster_aware_common.py` líneas 96–141)
14. **CLAW2: prueba en mayo y confirmaciones en junio.** Tres recetas de pesos y un control se entrenan con 202103 y 3 semillas y se miden en 202105 en el corte 13.500; sigue la que pasa la regla con mayor ganancia. Esa receta se entrena con 202103–202104 y se compara en 202106 con los puntajes de SUPERFINAL, primero con 5 semillas (tras verificar que el control con la semilla 808 da puntajes idénticos) y después con 20, donde se exige al menos 2 BAJA+2 más incluidos, al menos 1 más de los grupos 2 y 5 y 14 semillas a favor. Si una etapa no pasa, las siguientes no entrenan. Según el README, pasó BALANCED_CAPPED. (`4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/run_cluster_aware.py` líneas 275–332; `4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/run_cluster_aware.py` líneas 335–394; `4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/run_cluster_aware.py` líneas 411–462)
15. **CLAW2: entrenamiento final y puntajes de 202108.** Con el banco final de SUPERFINAL entrena 20 LightGBM binarios (BAJA+2 contra el resto) sobre todas las filas de 202103–202106, con las variables, parámetros y rondas de SUPERFINAL, peso por mes de la política elegida y pesos por grupo para los BAJA+2. Cada semilla construye su propio dataset; cada modelo puntúa las 164.647 filas de 202108 y se guarda con su hash. (`4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/run_cluster_aware.py` líneas 465–541; `4_modelo/experimentos_20261007_post_c3/05_superfinal100/superfinal100_v2.py` líneas 64–81)
16. **Archivo de entrega y verificación.** Promedia los 20 vectores de probabilidad, ordena de mayor a menor (empates por `numero_de_cliente`), toma los primeros 13.500 y los escribe de menor a mayor, uno por línea y sin encabezado, en `C1CLAW<identidad>ENS13500.csv`, junto con `MANIFEST.json` y `mensaje_zulip.txt`. Ningún script envía el archivo. `audit_cluster_aware.py` reconstruye el corte desde los 20 puntajes y `verificar_csv_final.py` controla formato, cantidad y SHA-256. (`4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/run_cluster_aware.py` líneas 543–568; `4_modelo/experimentos_20261007_post_c3/05_superfinal100/super_common.py` líneas 187–201; `4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/audit_cluster_aware.py` líneas 102–136; `5_prediccion_final/verificar_csv_final.py` líneas 67–115)

## Archivos

- `README.md` · explicacion · Markdown · 137 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/README.md.txt) — Presentación de la entrega: archivo final y ganancia pública declarada, tabla de los cinco pasos, detalle del modelo (clase, meses, variables, hiperparámetros, semillas y pesos por grupo), motivo de los pesos, instrucciones de réplica y cuatro tablas con lo que se probó y su resultado.
- `requirements-z501.txt` · configuracion · Texto · 4 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/requirements-z501.txt.txt) — Dependencias adicionales para el paso 3: duckdb y scikit-learn, sin versión. El README indica instalarlas junto con `requirements.lock`, que fija las versiones del resto.
- `3_grupos_baja2/eda_clusters_profundo.py` · principal · Python · 293 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/3_grupos_baja2/eda_clusters_profundo.py.txt) — Paso 3. Define las constantes y las funciones del perfil de hojas del Random Forest que importa `validar_clusters_estabilidad.py`. Su propio `main` es un análisis descriptivo de los grupos (perfiles, transiciones, comparación con CONTINUA) que el README no indica ejecutar.
- `3_grupos_baja2/README.md` · explicacion · Markdown · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/3_grupos_baja2/README.md.txt) — Explica el paso 3: Random Forest para distinguir BAJA+2 de clientes que permanecen, perfil de hojas y KMeans con k = 5; comando de ejecución y tamaños esperados de los cinco grupos (1.280, 1.136, 857, 579 y 215 clientes).
- `3_grupos_baja2/validar_clusters_estabilidad.py` · principal · Python · 190 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/3_grupos_baja2/validar_clusters_estabilidad.py.txt) — Paso 3. Entrena el Random Forest de referencia, agrupa los perfiles de los clientes BAJA+2 con KMeans (k = 5) y escribe `reference_labels.csv`, que el modelo final usa para pesar las filas BAJA+2. Después corre cuatro controles de estabilidad de esa partición.
- `2_variables/PAQUETE.json` · configuracion · JSON · 91 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/PAQUETE.json.txt) — Commit, repositorio de origen (`ClariRZ/Experimentos-cloud`) y SHA-256 de 85 archivos del paquete de variables. `run_q0.py` compara contra estos hashes los scripts, planes y `config.yaml` del paso 2. De los 85 archivos listados, 69 no están en este repositorio.
- `2_variables/README.md` · explicacion · Markdown · 28 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/README.md.txt) — Explica el paso 2: qué variables se agregan a las 152 originales para llegar a 2.062 (conjunto C3), qué hace cada archivo, por qué la carpeta conserva su estructura (el paso 4 la espera copiada en `$HOME/c1m1femasiva03_s3/paquete_c1/`) y los dos comandos que generan el banco de variables y la lista de C3.
- `2_variables/experimentos_20261006_m1_fe_masiva/plan_s2_familias.json` · configuracion · JSON · 91 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/plan_s2_familias.json.txt) — Plan de la comparación por familias de variables: folds, 5 semillas, 300 rondas, cortes y los bloques de cada familia. `run_s3_confirm_c3.py` lee de acá los bloques de S2_HIST_CORE y S2_TARJETAS_RATIOS. El script que corre este plan (`run_s2_familias.py`, nombrado en `PAQUETE.json`) no está en el repositorio.
- `2_variables/experimentos_20261006_m1_fe_masiva/config_screening.json` · configuracion · JSON · 10 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/config_screening.json.txt) — Configuración del generador de variables usada en todo el camino de la entrega: lags [1], ventanas [2], límite de 365.000 días para fechas relativas, 64 variables por archivo de partes, almacenamiento en float32 y relaciones activadas.
- `2_variables/experimentos_20261006_m1_fe_masiva/run_screening.py` · principal · Python · 189 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/run_screening.py.txt) — Paso 2. Construye el banco de variables derivadas (`fe_bank_dev`) llamando a `generate`. Sin `--solo-generar-fe` entrena además cuatro brazos de comparación masiva con 5 semillas; el README indica correrlo con ese flag.
- `2_variables/experimentos_20261006_m1_fe_masiva/plan_s3_confirm_c3.json` · configuracion · JSON · 47 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/plan_s3_confirm_c3.json.txt) — Plan de la confirmación de C3: entrenamiento 202103–202104, evaluación 202106, 20 semillas, 300 rondas, cortes 10.500, 11.000 y 11.500 y las cuatro condiciones de promoción.
- `2_variables/experimentos_20261006_m1_fe_masiva/run_s3_confirm_c3.py` · principal · Python · 199 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/run_s3_confirm_c3.py.txt) — Paso 2. Define el conjunto C3 a partir del catálogo del banco, entrena con 20 semillas un modelo con las variables originales y otro con C3 (202103–202104 contra 202106) y deja la lista de variables, los puntajes por semilla y `confirmacion_c3.json`, que los scripts del paso 4 exigen.
- `2_variables/experimentos_20261006_m1_fe_masiva/plan_screening.json` · configuracion · JSON · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/plan_screening.json.txt) — Plan de la comparación masiva: SHA-256 del dataset, 17 bloques a generar (deja fuera `ventanas` y `tendencias`), cuatro brazos, dos folds (202103→202105 y 202103–202104→202106), 5 semillas, 300 rondas y cortes.
- `2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/requirements.txt` · configuracion · Texto · 3 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/requirements.txt.txt) — Rangos de versión de numpy, pandas y pyarrow para el generador de variables.
- `2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_semantica.py` · principal · Python · 81 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_semantica.py.txt) — Lee y valida `catalogo_fuentes.csv`, que clasifica las 152 variables originales por tipo (numérica, categórica, fecha relativa o reloj) y modo de historia; esa clasificación decide qué transformaciones recibe cada variable.
- `2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/config_amplia.json` · configuracion · JSON · 10 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/config_amplia.json.txt) — Configuración por defecto de la línea de comandos de `generar_fe.py`: lags 1 a 5, ventanas 2 a 6 y float64. Los scripts del camino de la entrega no la usan: pasan `config_screening.json`.
- `2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/cargar_bloques.py` · principal · Python · 38 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/cargar_bloques.py.txt) — Lectura selectiva del banco: devuelve las variables originales más las derivadas pedidas para los meses indicados. La usan todos los scripts que entrenan o puntúan.
- `2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_core.py` · principal · Python · 97 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_core.py.txt) — Clase `Panel` (orden por cliente y mes, lags por mes calendario exacto y percentil dentro del mes), utilidades de indicadores y cocientes, y el bloque `cobertura_panel`.
- `2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_relaciones.py` · principal · Python · 477 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_relaciones.py.txt) — Variables que combinan varias columnas del mismo mes (monto por operación, sumas y cocientes de tarjetas, funciones activas, productos, deuda, interacciones) y la historia de algunos de esos resúmenes. C3 usa los bloques `ratios`, `tarjetas` e `historia_relaciones`.
- `2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_univariadas.py` · principal · Python · 151 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_univariadas.py.txt) — Transformaciones de una variable por vez, según su tipo en el catálogo: disponibilidad, historia (lag, delta, cambio relativo, transiciones, rachas), estados, percentiles del mes, ventanas y tendencias. C3 usa los bloques `historia_numerica`, `transiciones_numericas`, `recencia` y `categoricas`.
- `2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/generar_fe.py` · principal · Python · 164 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/generar_fe.py.txt) — Generador del banco de variables: lee el Parquet, arma el panel, recorre las variables producidas por los módulos `fe_*.py` y las guarda en partes Parquet con un catálogo y un manifiesto. Lo llaman `run_screening.py`, `run_q0.py`, `run_b1.py` y SUPERFINAL.
- `2_variables/vendor/comun/config.yaml` · configuracion · YAML · 185 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/2_variables/vendor/comun/config.yaml.txt) — Configuración traída de un repositorio anterior de experimentos. Los scripts de esta entrega leen sólo `lightgbm.base` (learning_rate 0,03, num_leaves 64, min_data_in_leaf 100, feature_fraction 0,8, bagging_fraction 0,8, bagging_freq 1, max_bin 255), que son los parámetros de todas las comparaciones previas a Optuna. El resto (meses, ganancia, un espacio de Optuna de 40 trials, una lista de 10 variables con historia, cortes candidatos y una ruta local al Parquet) no lo lee ningún script del repositorio.
- `1_dataset/README.md` · explicacion · Markdown · 15 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/1_dataset/README.md.txt) — Explica el paso 1: cómo se arma `clase_ternaria`, el comando para correr `preparar_competencia.py` y el SHA-256, las 983.061 filas y las 155 columnas que los scripts del paso 4 esperan del Parquet.
- `1_dataset/preparar_competencia.py` · principal · Python · 96 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/1_dataset/preparar_competencia.py.txt) — Paso 1. Con DuckDB lee el CSV crudo, arma `clase_ternaria` según la presencia del cliente uno y dos meses después y guarda `competencia_01.parquet` y una tabla de filas por mes y clase.
- `5_prediccion_final/README.md` · explicacion · Markdown · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/5_prediccion_final/README.md.txt) — Ficha del envío: nombre del archivo, mensaje al bot, fecha, identificador del envío, ganancia pública declarada, cantidad de filas y SHA-256; respuesta del bot y comando para verificar un CSV regenerado.
- `5_prediccion_final/MANIFIESTO_CLAW2_TRANSCRIPTO.json` · configuracion · JSON · 62 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/5_prediccion_final/MANIFIESTO_CLAW2_TRANSCRIPTO.json.txt) — Transcripción del `MANIFEST.json` de la corrida final: identidad, brazo BALANCED_CAPPED, 20 modelos, N 13.500, nombre y SHA-256 del CSV, los 16 parámetros de LightGBM, 361 rondas, política EXPANDING y el detalle de pesos por grupo. Dos campos iniciales aclaran que es una transcripción de campos y no una ejecución nueva.
- `5_prediccion_final/verificar_csv_final.py` · secundario · Python · 123 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/5_prediccion_final/verificar_csv_final.py.txt) — Verificador del CSV final, sin entrenar: formato de una columna sin encabezado, cantidad de filas, clientes sin repetir y, de forma opcional, pertenencia a 202108, igualdad contra un CSV de referencia y SHA-256 esperado.
- `4_modelo/README.md` · explicacion · Markdown · 65 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/README.md.txt) — Explica el paso 4: las cuatro carpetas de experimentos y su orden, el mapa de carpetas fijas dentro de `$HOME`, la máquina usada, el reemplazo del bucket de Cloud Storage por un texto fijo, los comandos de cada corrida y la variable de entorno `CLAW2_REPLICA=1`.
- `4_modelo/experimentos_20261007_post_c3/05_superfinal100/super_common.py` · principal · Python · 493 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/05_superfinal100/super_common.py.txt) — Utilidades compartidas por SUPERFINAL y CLAW2: constantes de meses y semillas, rutas fijas, parámetros base, curva de ganancia y elección de meseta, carga de folds, definición de los 10 conjuntos de variables y exportación del CSV.
- `4_modelo/experimentos_20261007_post_c3/05_superfinal100/auditar_superfinal100_v2.py` · principal · Python · 169 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/05_superfinal100/auditar_superfinal100_v2.py.txt) — Auditoría de SUPERFINAL sin entrenar: reconstruye el promedio desde los 20 puntajes guardados, lo compara con el CSV y escribe `AUDITORIA_FINAL.json`, que `run_cluster_aware.py` exige antes de empezar.
- `4_modelo/experimentos_20261007_post_c3/05_superfinal100/test_superfinal100_v2.py` · secundario · Python · 100 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/05_superfinal100/test_superfinal100_v2.py.txt) — Seis tests con `unittest` que no usan los datos de la competencia: coherencia entre el plan y el código, particiones de semillas sin superposición, igualdad de predicciones entre el dataset por semilla y el camino de referencia sobre datos sintéticos, presencia de ciertos textos en el código fuente y la fórmula de estimación de memoria.
- `4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100_v2_safe.py` · principal · Python · 10 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100_v2_safe.py.txt) — Punto de entrada de SUPERFINAL: carga la versión 2, reemplaza su etapa 5 por la variante que libera memoria y llama a `main` (`--home $HOME --all`).
- `4_modelo/experimentos_20261007_post_c3/05_superfinal100/README.md` · explicacion · Markdown · 42 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/05_superfinal100/README.md.txt) — Explica SUPERFINAL: tabla de las seis etapas con qué decide cada una y su resultado, espacio de búsqueda de Optuna, tabla de los hiperparámetros elegidos (trial 11), qué hace cada archivo y qué salidas lee el modelo final.
- `4_modelo/experimentos_20261007_post_c3/05_superfinal100/stage5_v2_safe.py` · principal · Python · 291 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/05_superfinal100/stage5_v2_safe.py.txt) — Etapa 5 de SUPERFINAL: genera el banco final de variables (202103–202106 y 202108), entrena 20 modelos con los cuatro meses y exporta el CSV de SUPERFINAL. El modelo final de la entrega reutiliza ese banco.
- `4_modelo/experimentos_20261007_post_c3/05_superfinal100/plan_superfinal100.json` · configuracion · JSON · 223 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/05_superfinal100/plan_superfinal100.json.txt) — Plan de la versión 1 de SUPERFINAL (corrida `c1superfinal100`). En el camino de la entrega `plan_doc` queda reemplazado por el plan de la versión 2, de modo que este archivo no se lee.
- `4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100.py` · principal · Python · 825 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100.py.txt) — Etapas de SUPERFINAL versión 1. La versión 2 usa de acá la etapa 0 (calidad de datos), la etapa 1 (conjunto de variables), la etapa 3 (Optuna y revalidación), la etapa 4 (20 semillas y corte) y la preparación del banco final; sus `stage2`, `stage5`, `run_all` y `main` no se llaman en el camino de la entrega.
- `4_modelo/experimentos_20261007_post_c3/05_superfinal100/plan_superfinal100_v2.json` · configuracion · JSON · 89 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/05_superfinal100/plan_superfinal100_v2.json.txt) — Plan de SUPERFINAL versión 2: fold, grilla de cortes, dataset por semilla con canary exacto, memoria mínima, particiones de semillas, brazos de representación, políticas de peso por mes, búsqueda (20 trials, semilla 17, 202103→202105, 3 a revalidar) y confirmación con 14 semillas a favor. El código lo incluye en las huellas de cada etapa y verifica los campos `run` y `stop_after_this_experiment`; los umbrales están escritos también en el código.
- `4_modelo/experimentos_20261007_post_c3/05_superfinal100/superfinal100_v2.py` · principal · Python · 484 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/05_superfinal100/superfinal100_v2.py.txt) — Orquestador de SUPERFINAL versión 2: configura los módulos comunes, entrena con un `lgb.Dataset` por semilla, corre el canary contra C3 y define la etapa 2, la regla de 14 semillas de la etapa 4 y el orden de las etapas.
- `4_modelo/experimentos_20261007_post_c3/04_b1_variables_rotas/plan_b1.json` · configuracion · JSON · 106 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/04_b1_variables_rotas/plan_b1.json.txt) — Descripción declarativa de B1: modelos congelados, fold, semillas, grilla, seis brazos y regla de selección. `run_b1.py` no lee este archivo: arma su plan con `make_plan`.
- `4_modelo/experimentos_20261007_post_c3/04_b1_variables_rotas/README.md` · explicacion · Markdown · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/04_b1_variables_rotas/README.md.txt) — Explica B1: con los modelos de Q0 prueba marcar como faltantes otras variables con un mes anómalo; indica que SUPERFINAL lo ejecuta en su etapa 0.
- `4_modelo/experimentos_20261007_post_c3/04_b1_variables_rotas/run_b1.py` · principal · Python · 661 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/04_b1_variables_rotas/run_b1.py.txt) — Paso 4, B1. Sin reentrenar, puntúa 202106 con los 20 modelos de Q0 sobre cuatro copias del dataset con variables de un mes pasadas a NA, y decide con una regla fija qué brazo de calidad de datos usa SUPERFINAL (o el dataset original).
- `4_modelo/experimentos_20261007_post_c3/02_q0_ccajas_na/README.md` · explicacion · Markdown · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/02_q0_ccajas_na/README.md.txt) — Explica Q0: reproduce los 20 modelos de C3 y vuelve a puntuar 202106 con `ccajas_depositos` de 202105 marcada como faltante; lista los cuatro modos de ejecución y la salida.
- `4_modelo/experimentos_20261007_post_c3/02_q0_ccajas_na/run_q0.py` · principal · Python · 660 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/02_q0_ccajas_na/run_q0.py.txt) — Paso 4, Q0. Reproduce los 20 modelos de C3 (202103–202104, 300 rondas) con tolerancia 1e-12, los guarda y vuelve a puntuar 202106 con `ccajas_depositos` de 202105 en NA. B1 y SUPERFINAL exigen su salida.
- `4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/audit_cluster_aware.py` · secundario · Python · 163 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/audit_cluster_aware.py.txt) — Auditoría de CLAW2 sin entrenar, posterior a la escritura del CSV: verifica estados de las etapas, manifiesto, conservación de la suma de pesos, hashes de los 20 modelos y que el CSV contenga los 13.500 clientes de mayor promedio; escribe `AUDIT.json`.
- `4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/plan.json` · configuracion · JSON · 244 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/plan.json.txt) — Plan de CLAW2: hipótesis, corte fijo 13.500, identidad de la corrida de SUPERFINAL de origen, uso de los grupos sólo para pesar filas BAJA+2 de entrenamiento, regla de normalización de pesos, los cuatro brazos y, por etapa, meses, semillas y condiciones para pasar. `run_cluster_aware.py` toma de acá la identidad de origen e incluye el plan en sus huellas.
- `4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/run_cluster_aware.py` · principal · Python · 617 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/run_cluster_aware.py.txt) — Modelo final (CLAW2). Toma variables, hiperparámetros, rondas, política de pesos por mes y banco final de SUPERFINAL, prueba tres recetas de peso por grupo para las filas BAJA+2 (202105 y 202106) y, si pasan las tres etapas, entrena 20 LightGBM con 202103–202106 y escribe el CSV de 13.500 clientes de 202108.
- `4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/README.md` · explicacion · Markdown · 34 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/README.md.txt) — Explica CLAW2: el único cambio respecto de SUPERFINAL es el peso de cada BAJA+2 según su grupo; tabla de las tres recetas con su resultado en mayo, pesos efectivos del modelo de agosto, qué hace cada archivo y nombre del CSV de salida.
- `4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/cluster_aware_common.py` · principal · Python · 166 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/cluster_aware_common.py.txt) — Cálculo de los pesos por grupo de las filas BAJA+2 con conservación de la suma de pesos, métricas en el corte fijo 13.500 por grupo y resumen pareado por semilla.
- `4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/test_cluster_aware.py` · secundario · Python · 75 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/test_cluster_aware.py.txt) — Nueve tests con `unittest` sobre datos sintéticos: campos del plan, recetas con los cinco grupos, conservación de la suma de pesos de los BAJA+2 con y sin pesos por mes, límites 0,5–4 de BALANCED_CAPPED, diferencia de ganancia por un BAJA+2 más (1.100.000), elección del ganador, resumen pareado y presencia o ausencia de ciertos textos en el código de `run_cluster_aware.py`.
- `.github/workflows/validacion_codigo.yml` · configuracion · YAML · 17 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/clarirz/.github/workflows/validacion_codigo.yml.txt) — Flujo de GitHub Actions (ubuntu-24.04, Python 3.12): instala las dependencias, compila los `.py` de las cinco carpetas y corre los dos archivos de tests, que no necesitan datos.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### 3_grupos_baja2/eda_clusters_profundo.py

Paso 3. Define las constantes y las funciones del perfil de hojas del Random Forest que importa `validar_clusters_estabilidad.py`. Su propio `main` es un análisis descriptivo de los grupos (perfiles, transiciones, comparación con CONTINUA) que el README no indica ejecutar.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–19] Docstring e importaciones (duckdb, `KMeans`, `RandomForestClassifier`).
#   Constantes: nombres de columnas, semilla 214363, 300 árboles, mínimo de 50 filas por hoja y k = 5.
#   `validar_clusters_estabilidad.py` importa estas constantes.
"""
EDA profundo de clusters BAJA+2.

Esto es EDA/characterización, no selección de k ni prueba causal.
Reproduce z501 y después estudia variables originales, comparación con
CONTINUA y tiempo relativo a BAJA+2 / último mes activo.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import duckdb
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier

ID="numero_de_cliente"; MES="foto_mes"; TARGET="clase_ternaria"
GRUPO="grupo"; CLUSTER="cluster"; RAIZ="_sin_split"
SEED=214363; N_TREES=300; MIN_LEAF=50; K=5

# [Anotación · líneas 21–43] Listas de variables para los perfiles descriptivos: 33 variables originales
#   (`VARS`), las dos nominales (`Master_status`, `Visa_status`) y 18 variables para mirar transiciones.
VARS=[
 "active_quarter","internet","cproductos","ctrx_quarter",
 "chomebanking_transacciones","mcaja_ahorro","mcuentas_saldo","mpasivos_margen",
 "ctarjeta_debito_transacciones","ctarjeta_visa","ctarjeta_visa_transacciones",
 "mtarjeta_visa_consumo","ctarjeta_visa_debitos_automaticos",
 "mtarjeta_visa_debitos_automaticos","mttarjeta_visa_debitos_automaticos",
 "ctarjeta_master","ctarjeta_master_transacciones","mtarjeta_master_consumo",
 "cpayroll_trx","mpayroll","cpagomiscuentas","matm",
 "ctransferencias_recibidas","mtransferencias_recibidas",
 "ctransferencias_emitidas","mtransferencias_emitidas","ccajas_transacciones",
 "cdescubierto_preacordado","cprestamos_personales","mprestamos_personales",
 "Visa_mfinanciacion_limite","Master_status","Visa_status",
]
NOMINAL={"Master_status","Visa_status"}
TRANSITION_VARS=[
 "ctrx_quarter","chomebanking_transacciones","mcaja_ahorro",
 "ctarjeta_debito_transacciones","ctarjeta_visa_transacciones",
 "mtarjeta_visa_consumo","ctarjeta_visa_debitos_automaticos",
 "mtarjeta_visa_debitos_automaticos","mttarjeta_visa_debitos_automaticos",
 "mpayroll","cpayroll_trx","cpagomiscuentas","matm",
 "ctransferencias_recibidas","ctransferencias_emitidas",
 "cprestamos_personales","mprestamos_personales","ccajas_transacciones",
]

# [Anotación · líneas 45–54] `month_ord` convierte AAAAMM en un número de mes correlativo; `load_full` lee el
#   dataset completo con DuckDB desde Parquet o CSV.
def month_ord(x):
    x=pd.to_numeric(x, errors="coerce")
    return (x//100).astype("Int64")*12 + (x%100).astype("Int64")

def load_full(data):
    return duckdb.connect().execute(
        f"SELECT * FROM read_parquet('{data.as_posix()}')"
        if data.suffix.lower()==".parquet"
        else f"SELECT * FROM read_csv('{data.as_posix()}', sample_size=-1)"
    ).df()

# [Anotación · líneas 56–71] `build_z501_sample` arma la muestra para el Random Forest: todas las filas de los
#   clientes con algún BAJA+2 (grupo 1) y las de una cantidad igual de clientes presentes en todos los meses y
#   sin ninguna baja (grupo 0), elegidos por orden de `hash(numero_de_cliente + 214363)`.
def build_z501_sample(full):
    churn_ids=full.loc[full[TARGET].eq("BAJA+2"),ID].drop_duplicates()
    n_months=full[MES].nunique()
    faithful=full.groupby(ID,sort=False).agg(
        n_rows=(MES,"size"),
        any_baja=(TARGET,lambda s:s.isin(["BAJA+1","BAJA+2"]).any())
    )
    fid=faithful.index[(faithful.n_rows.eq(n_months)) & (~faithful.any_baja)]
    ids_df=pd.DataFrame({ID:fid.to_numpy(dtype=np.int64)})
    con=duckdb.connect(); con.register("ids_df",ids_df)
    fs=con.execute(
        f"SELECT {ID} FROM ids_df ORDER BY hash({ID}+{SEED}) LIMIT {len(churn_ids)}"
    ).df()[ID]
    a=full[full[ID].isin(churn_ids)].copy(); a[GRUPO]=1
    b=full[full[ID].isin(fs)].copy(); b[GRUPO]=0
    return pd.concat([a,b],ignore_index=True).sort_values([ID,MES])

# [Anotación · líneas 73–82] `numeric_features` lista las columnas numéricas salvo claves, clase y grupo.
#   `last_split_feature` asigna a cada nodo de un árbol la variable del corte que lleva a él (−1 para la raíz).
def numeric_features(df):
    excl={ID,MES,TARGET,GRUPO}
    return [c for c in df.columns if c not in excl and pd.api.types.is_numeric_dtype(df[c])]

def last_split_feature(est):
    t=est.tree_; out=np.full(t.node_count,-1,dtype=np.int64)
    internal=np.flatnonzero(t.children_left!=-1)
    out[t.children_left[internal]]=t.feature[internal]
    out[t.children_right[internal]]=t.feature[internal]
    return out

# [Anotación · líneas 84–94] `leaf_profile` ubica cada fila en una hoja de cada árbol, reemplaza la hoja por
#   la variable de su último corte, cuenta por cliente cuántas veces aparece cada variable y normaliza a
#   proporciones. El resultado es un perfil por cliente.
def leaf_profile(rf,X,ids,features):
    leaves=rf.apply(X); nfeat=len(features); codes=np.empty_like(leaves)
    for j,est in enumerate(rf.estimators_):
        codes[:,j]=last_split_feature(est)[leaves[:,j]]
    codes[codes<0]=nfeat
    idx,uid=pd.factorize(ids)
    C=np.zeros((len(uid),nfeat+1),dtype=np.int64)
    np.add.at(C,(np.repeat(idx,leaves.shape[1]),codes.ravel()),1)
    C=pd.DataFrame(C,index=pd.Index(uid,name=ID),columns=features+[RAIZ])
    P=C.drop(columns=[RAIZ]); P=P.loc[:,P.sum(axis=0)>0]
    return P.div(P.sum(axis=1),axis=0)

# [Anotación · líneas 96–119] `reproduce_clusters` entrena el Random Forest (300 árboles, 50 filas mínimas por
#   hoja, `max_features="sqrt"`, clases balanceadas) para separar grupo 1 de grupo 0, calcula el perfil de los
#   clientes BAJA+2 y corre KMeans con k = 5 y 20 inicializaciones. Renumera los grupos de mayor a menor tamaño
#   y arma, por grupo, las 10 variables con mayor cociente entre su peso en el grupo y su peso global.
def reproduce_clusters(sample):
    feats=numeric_features(sample)
    X=sample[feats].to_numpy(dtype=np.float32)
    y=sample[GRUPO].to_numpy(); ids=sample[ID].to_numpy()
    rf=RandomForestClassifier(
      n_estimators=N_TREES,min_samples_leaf=MIN_LEAF,max_features="sqrt",
      class_weight="balanced",oob_score=True,n_jobs=-1,random_state=SEED
    ).fit(X,y)
    P=leaf_profile(rf,X,ids,feats)
    churn_ids=pd.Index(sample.loc[sample[GRUPO].eq(1),ID].unique())
    Pc=P.loc[churn_ids]
    km=KMeans(n_clusters=K,n_init=20,random_state=SEED).fit(Pc.values)
    order=pd.Series(km.labels_).value_counts().index.tolist()
    remap={old:new+1 for new,old in enumerate(order)}
    labels=pd.Series([remap[z] for z in km.labels_],index=Pc.index,name=CLUSTER)
    global_share=Pc.mean(); rows=[]
    for c,sub in Pc.groupby(labels):
        sh=sub.mean()
        tab=pd.DataFrame({"share_cluster":sh,"share_global":global_share})
        tab["lift"]=tab.share_cluster/tab.share_global.replace(0,np.nan)
        tab=tab[tab.share_cluster>=0.5/Pc.shape[1]].sort_values("lift",ascending=False).head(10)
        for rank,(v,r) in enumerate(tab.iterrows(),1):
            rows.append({CLUSTER:c,"rank":rank,"variable":v,**r.to_dict()})
    return rf,labels,pd.DataFrame(rows)

# [Anotación · líneas 121–128] `prepare_history` toma todas las filas de los clientes agrupados y agrega el
#   mes de su BAJA+2, su último mes presente y la distancia en meses de cada fila a esos dos momentos.
def prepare_history(full,labels):
    d=full[full[ID].isin(labels.index)].copy().merge(labels,left_on=ID,right_index=True)
    b2=d.loc[d[TARGET].eq("BAJA+2")].groupby(ID)[MES].min().rename("mes_baja2")
    last=d.groupby(ID)[MES].max().rename("mes_ultimo_activo")
    d=d.merge(b2,on=ID).merge(last,on=ID)
    d["rel_baja2"]=(month_ord(d[MES])-month_ord(d.mes_baja2)).astype("Int64")
    d["rel_ultimo_activo"]=(month_ord(d[MES])-month_ord(d.mes_ultimo_activo)).astype("Int64")
    return d

# [Anotación · líneas 130–166] Funciones descriptivas: resumen de una variable numérica (faltantes, ceros,
#   positivos, media, mediana y cuartiles), tabla de perfiles por grupo y distribución de las variables
#   nominales.
def describe_numeric(x):
    x=pd.to_numeric(x,errors="coerce"); obs=x.dropna(); pos=obs[obs>0]
    return dict(
      n=len(x),n_obs=len(obs),pct_missing=100*x.isna().mean(),
      pct_zero_obs=100*(obs.eq(0).mean() if len(obs) else np.nan),
      pct_positive_obs=100*(obs.gt(0).mean() if len(obs) else np.nan),
      mean=obs.mean() if len(obs) else np.nan,
      median=obs.median() if len(obs) else np.nan,
      q25=obs.quantile(.25) if len(obs) else np.nan,
      q75=obs.quantile(.75) if len(obs) else np.nan,
      median_positive=pos.median() if len(pos) else np.nan,
    )

def profile_table(d,by,vars_):
    rows=[]
    for keys,g in d.groupby(by,dropna=False):
        if not isinstance(keys,tuple): keys=(keys,)
        base=dict(zip(by,keys))
        for v in vars_:
            if v not in g.columns: continue
            if v in NOMINAL:
                row={**base,"variable":v,"n":len(g),"n_obs":g[v].notna().sum(),
                     "pct_missing":100*g[v].isna().mean(),"pct_zero_obs":np.nan,
                     "pct_positive_obs":np.nan,"mean":np.nan,"median":np.nan,
                     "q25":np.nan,"q75":np.nan,"median_positive":np.nan}
            else:
                row={**base,"variable":v,**describe_numeric(g[v])}
            rows.append(row)
    return pd.DataFrame(rows)

def nominal_distribution(d,by,vars_):
    rows=[]
    for v in vars_:
        if v not in d.columns: continue
        z=d.groupby(by,dropna=False)[v].value_counts(dropna=False,normalize=True).rename("share").reset_index()
        z["variable"]=v; rows.append(z)
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()

# [Anotación · líneas 168–187] `transitions` cuenta, por grupo y variable, cuántos clientes pasan de positivo
#   a cero, de cero a cero y de cero a positivo entre dos meses relativos a la BAJA+2.
def transitions(d,from_rel,to_rel):
    vars_=[v for v in TRANSITION_VARS if v in d.columns]
    a=d[d.rel_baja2.eq(from_rel)][[ID,CLUSTER]+vars_].set_index(ID)
    b=d[d.rel_baja2.eq(to_rel)][[ID,CLUSTER]+vars_].set_index(ID)
    ids=a.index.intersection(b.index); a=a.loc[ids]; b=b.loc[ids]; rows=[]
    for c in sorted(d[CLUSTER].unique()):
        idx=a.index[a[CLUSTER].eq(c)]
        for v in vars_:
            x=a.loc[idx,v]; y=b.loc[idx,v]; valid=x.notna()&y.notna()
            x=x[valid]; y=y[valid]; prev=x>0; nprev=int(prev.sum())
            p0=int(((x>0)&y.eq(0)).sum()); zz=int((x.eq(0)&y.eq(0)).sum())
            zp=int((x.eq(0)&y.gt(0)).sum()); pp=(x>0)&(y>0)
            rows.append({
              CLUSTER:c,"variable":v,"from_rel":from_rel,"to_rel":to_rel,
              "n_pairs":len(x),"n_prev_positive":nprev,"n_positive_to_zero":p0,
              "pct_positive_to_zero":100*p0/nprev if nprev else np.nan,
              "n_zero_to_zero":zz,"n_zero_to_positive":zp,
              "median_delta_among_stay_positive":(y[pp]-x[pp]).median() if pp.any() else np.nan
            })
    return pd.DataFrame(rows)

# [Anotación · líneas 189–208] `continua_benchmark` compara, por grupo, mes relativo y mes calendario,
#   medianas y porcentaje de ceros contra los clientes CONTINUA del mismo mes.
def continua_benchmark(full,hist):
    cont=full[full[TARGET].eq("CONTINUA")]; rows=[]
    dh=hist[hist.rel_baja2.between(-3,0)]
    for (c,rel,mes),g in dh.groupby([CLUSTER,"rel_baja2",MES]):
        ref=cont[cont[MES].eq(mes)]
        if ref.empty: continue
        for v in VARS:
            if v not in g.columns or v not in ref.columns or v in NOMINAL: continue
            a=pd.to_numeric(g[v],errors="coerce").dropna()
            b=pd.to_numeric(ref[v],errors="coerce").dropna()
            if not len(a) or not len(b): continue
            rows.append({
              CLUSTER:c,"rel_baja2":int(rel),MES:mes,"variable":v,
              "cluster_n":len(a),"continua_n":len(b),
              "cluster_median":a.median(),"continua_median":b.median(),
              "cluster_pct_zero":100*a.eq(0).mean(),"continua_pct_zero":100*b.eq(0).mean(),
              "cluster_median_positive":a[a>0].median() if (a>0).any() else np.nan,
              "continua_median_positive":b[b>0].median() if (b>0).any() else np.nan,
            })
    return pd.DataFrame(rows)

# [Anotación · líneas 210–243] `c1_matched_visa` compara el grupo 1 contra clientes CONTINUA del mismo mes
#   emparejados por decil de transacciones y de consumo Visa.
def c1_matched_visa(full,hist):
    cont=full[full[TARGET].eq("CONTINUA")]; out=[]
    for rel in [-1,0]:
      c1=hist[(hist[CLUSTER].eq(1))&hist.rel_baja2.eq(rel)].copy()
      for mes,a in c1.groupby(MES):
        b=cont[cont[MES].eq(mes)].copy()
        if a.empty or b.empty: continue
        for v in ["ctarjeta_visa_transacciones","mtarjeta_visa_consumo"]:
            vals=pd.to_numeric(b[v],errors="coerce")
            b[f"_pct_{v}"]=vals.rank(pct=True,method="average")
            sorted_b=np.sort(vals.dropna().to_numpy())
            av=pd.to_numeric(a[v],errors="coerce")
            a[f"_pct_{v}"]=av.apply(lambda x: np.searchsorted(sorted_b,x,side="right")/len(sorted_b) if pd.notna(x) and len(sorted_b) else np.nan)
        for df in (a,b):
            df["_bin_trx"]=np.minimum((df["_pct_ctarjeta_visa_transacciones"]*10).fillna(-1).astype(int),9)
            df["_bin_amt"]=np.minimum((df["_pct_mtarjeta_visa_consumo"]*10).fillna(-1).astype(int),9)
        parts=[]
        for (bt,ba),ga in a.groupby(["_bin_trx","_bin_amt"]):
            gb=b[b._bin_trx.eq(bt)&b._bin_amt.eq(ba)]
            if not gb.empty: parts.append(gb.sample(n=len(ga),replace=len(gb)<len(ga),random_state=SEED))
        if not parts: continue
        bm=pd.concat(parts,ignore_index=True)
        for v in [x for x in VARS if x not in NOMINAL and x not in {"ctarjeta_visa_transacciones","mtarjeta_visa_consumo"}]:
            if v not in a.columns or v not in bm.columns: continue
            xa=pd.to_numeric(a[v],errors="coerce").dropna(); xb=pd.to_numeric(bm[v],errors="coerce").dropna()
            if not len(xa) or not len(xb): continue
            out.append({
              "rel_baja2":rel,MES:mes,"variable":v,"c1_n":len(xa),"matched_continua_n":len(xb),
              "c1_median":xa.median(),"matched_continua_median":xb.median(),
              "c1_pct_zero":100*xa.eq(0).mean(),"matched_continua_pct_zero":100*xb.eq(0).mean(),
              "c1_median_positive":xa[xa>0].median() if (xa>0).any() else np.nan,
              "matched_continua_median_positive":xb[xb>0].median() if (xb>0).any() else np.nan,
            })
    return pd.DataFrame(out)

# [Anotación · líneas 245–262] `pairwise_at_event` calcula, para cada par de grupos, la diferencia de medianas
#   de cada variable dividida por el rango intercuartílico, en el mes de la BAJA+2 y en el anterior.
def pairwise_at_event(hist):
    rows=[]
    for rel in [-1,0]:
      d=hist[hist.rel_baja2.eq(rel)]
      for v in [x for x in VARS if x not in NOMINAL and x in d.columns]:
        vals=pd.to_numeric(d[v],errors="coerce"); iqr=vals.quantile(.75)-vals.quantile(.25)
        for a in range(1,K+1):
          xa=pd.to_numeric(d.loc[d[CLUSTER].eq(a),v],errors="coerce").dropna()
          for b in range(a+1,K+1):
            xb=pd.to_numeric(d.loc[d[CLUSTER].eq(b),v],errors="coerce").dropna()
            if not len(xa) or not len(xb): continue
            rows.append({
              "rel_baja2":rel,"cluster_a":a,"cluster_b":b,"variable":v,
              "median_a":xa.median(),"median_b":xb.median(),
              "std_median_diff_iqr":(xa.median()-xb.median())/iqr if pd.notna(iqr) and iqr!=0 else np.nan,
              "pct_zero_a":100*xa.eq(0).mean(),"pct_zero_b":100*xb.eq(0).mean()
            })
    return pd.DataFrame(rows)

# [Anotación · líneas 264–293] `main` ejecuta ocho pasos (lectura, agrupamiento, historia, perfiles,
#   transiciones, comparación con CONTINUA, emparejamiento del grupo 1 y contrastes) y escribe doce CSV
#   numerados en la carpeta de salida. El camino de la entrega usa de este archivo las constantes y las
#   funciones `load_full`, `numeric_features` y `leaf_profile`, no este `main`.
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--out",type=Path,default=Path("resultados_eda_clusters")); args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    print("1/8 leyendo datos"); full=load_full(args.data)
    print("2/8 reproduciendo z501"); sample=build_z501_sample(full); rf,labels,defs=reproduce_clusters(sample)
    pd.DataFrame({CLUSTER:labels.value_counts().sort_index().index,"n_clientes":labels.value_counts().sort_index().values}).to_csv(args.out/"01_cluster_sizes.csv",index=False)
    defs.to_csv(args.out/"02_defining_features.csv",index=False)
    print("Clusters reproducidos:")
    print(labels.value_counts().sort_index().to_string())
    print("Top 3 atributos por cluster:")
    print(defs[defs["rank"]<=3][[CLUSTER,"rank","variable","lift"]].to_string(index=False))
    print("3/8 historia"); hist=prepare_history(full,labels)
    present=list(dict.fromkeys([v for v in VARS if v in hist.columns]))
    print("4/8 perfiles")
    profile_table(hist[hist.rel_baja2.eq(0)],[CLUSTER],present).to_csv(args.out/"03_raw_profile_at_baja2.csv",index=False)
    profile_table(hist[hist.rel_baja2.between(-3,1)],[CLUSTER,"rel_baja2"],present).to_csv(args.out/"04_profile_relative_to_baja2.csv",index=False)
    profile_table(hist[hist.rel_ultimo_activo.between(-3,0)],[CLUSTER,"rel_ultimo_activo"],present).to_csv(args.out/"05_profile_relative_to_last_active.csv",index=False)
    nominal_distribution(hist[hist.rel_baja2.between(-3,1)],[CLUSTER,"rel_baja2"],[v for v in NOMINAL if v in hist.columns]).to_csv(args.out/"05b_status_distribution.csv",index=False)
    print("5/8 transiciones")
    pd.concat([transitions(hist,a,b) for a,b in [(-3,-2),(-2,-1),(-1,0),(0,1)]],ignore_index=True).to_csv(args.out/"06_transitions_relative_to_baja2.csv",index=False)
    print("6/8 CONTINUA"); continua_benchmark(full,hist).to_csv(args.out/"07_cluster_vs_continua_same_month.csv",index=False)
    print("7/8 C1 matched"); c1_matched_visa(full,hist).to_csv(args.out/"08_c1_vs_continua_matched_visa.csv",index=False)
    print("8/8 contrastes"); pairwise_at_event(hist).to_csv(args.out/"09_pairwise_cluster_contrasts.csv",index=False)
    pd.DataFrame({"variable":present}).to_csv(args.out/"10_selected_variables.csv",index=False)
    pd.DataFrame({"metric":["rf_oob","n_churn","n_sample_rows"],"value":[rf.oob_score_,len(labels),len(sample)]}).to_csv(args.out/"00_run_metadata.csv",index=False)
    print(f"RF OOB={rf.oob_score_:.4f} (NO es validación de clusters)")
    print("Listo",args.out)

if __name__=="__main__": main()
```

### 3_grupos_baja2/validar_clusters_estabilidad.py

Paso 3. Entrena el Random Forest de referencia, agrupa los perfiles de los clientes BAJA+2 con KMeans (k = 5) y escribe `reference_labels.csv`, que el modelo final usa para pesar las filas BAJA+2. Después corre cuatro controles de estabilidad de esa partición.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–25] Docstring con los cuatro controles de estabilidad. Importa `KMeans`,
#   `RandomForestClassifier`, `adjusted_rand_score` y `linear_sum_assignment`, y de `eda_clusters_profundo.py`
#   las constantes y las funciones `load_full`, `numeric_features` y `leaf_profile`.
"""
Validación de estabilidad de la segmentación z501.

NO selecciona k por silhouette.
Evalúa:
1) sensibilidad de KMeans a semillas sobre la misma representación;
2) estabilidad por bootstrap de clientes;
3) estabilidad al reconstruir Random Forest + muestra de fieles con otras semillas;
4) cómo se fusiona/subdivide k=5 al usar otras resoluciones.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import adjusted_rand_score
from scipy.optimize import linear_sum_assignment

from eda_clusters_profundo import (
    ID,MES,TARGET,GRUPO,CLUSTER,RAIZ,SEED,N_TREES,MIN_LEAF,
    load_full,numeric_features,leaf_profile
)
import duckdb

# [Anotación · líneas 27–42] `build_sample` arma la muestra con una semilla dada: filas de los clientes con
#   algún BAJA+2 (grupo 1) y de igual cantidad de clientes presentes en todos los meses sin ninguna baja (grupo
#   0), elegidos por orden de `hash(numero_de_cliente + semilla)`.
def build_sample(full, seed):
    churn_ids=full.loc[full[TARGET].eq("BAJA+2"),ID].drop_duplicates()
    n_months=full[MES].nunique()
    faithful=full.groupby(ID,sort=False).agg(
        n_rows=(MES,"size"),
        any_baja=(TARGET,lambda s:s.isin(["BAJA+1","BAJA+2"]).any())
    )
    fid=faithful.index[(faithful.n_rows.eq(n_months)) & (~faithful.any_baja)]
    ids_df=pd.DataFrame({ID:fid.to_numpy(dtype=np.int64)})
    con=duckdb.connect(); con.register("ids_df",ids_df)
    fs=con.execute(
        f"SELECT {ID} FROM ids_df ORDER BY hash({ID}+{seed}) LIMIT {len(churn_ids)}"
    ).df()[ID]
    a=full[full[ID].isin(churn_ids)].copy(); a[GRUPO]=1
    b=full[full[ID].isin(fs)].copy(); b[GRUPO]=0
    return pd.concat([a,b],ignore_index=True).sort_values([ID,MES])

# [Anotación · líneas 44–55] `fit_profile` entrena el Random Forest (300 árboles por defecto, 50 filas mínimas
#   por hoja, clases balanceadas, semilla dada) sobre todas las columnas numéricas de la muestra y devuelve el
#   perfil de hojas de los clientes BAJA+2.
def fit_profile(full, seed=SEED, n_trees=N_TREES):
    sample=build_sample(full,seed)
    feats=numeric_features(sample)
    X=sample[feats].to_numpy(dtype=np.float32)
    y=sample[GRUPO].to_numpy(); ids=sample[ID].to_numpy()
    rf=RandomForestClassifier(
        n_estimators=n_trees,min_samples_leaf=MIN_LEAF,max_features="sqrt",
        class_weight="balanced",oob_score=True,n_jobs=-1,random_state=seed
    ).fit(X,y)
    P=leaf_profile(rf,X,ids,feats)
    churn_ids=pd.Index(sample.loc[sample[GRUPO].eq(1),ID].unique())
    return rf,P.loc[churn_ids]

# [Anotación · líneas 57–65] `fit_k` ajusta KMeans con k grupos y 20 inicializaciones (opcionalmente sobre un
#   remuestreo de filas) y asigna grupo a todos los clientes; `size_remap` renumera los grupos de mayor a menor
#   tamaño empezando en 1.
def fit_k(P,k,seed=SEED,n_init=20,weights_idx=None):
    X=P.values if weights_idx is None else P.values[weights_idx]
    km=KMeans(n_clusters=k,n_init=n_init,random_state=seed).fit(X)
    return km,km.predict(P.values)

def size_remap(labels):
    order=pd.Series(labels).value_counts().index.tolist()
    remap={old:new+1 for new,old in enumerate(order)}
    return np.array([remap[x] for x in labels])

# [Anotación · líneas 67–83] `best_map` empareja las etiquetas de dos particiones con el algoritmo húngaro
#   sobre la tabla cruzada; `top_features` devuelve, por grupo, las 10 variables con mayor cociente entre su
#   peso en el grupo y su peso global.
def best_map(ref,pred):
    tab=pd.crosstab(pd.Series(ref,name="ref"),pd.Series(pred,name="pred"))
    M=tab.to_numpy()
    rr,cc=linear_sum_assignment(-M)
    mapping={tab.columns[c]:tab.index[r] for r,c in zip(rr,cc)}
    mapped=np.array([mapping.get(x,-1) for x in pred])
    return mapped,mapping,tab

def top_features(P,labels,n=10):
    global_mean=P.mean(axis=0)
    out={}
    for c in sorted(np.unique(labels)):
        ids=np.flatnonzero(labels==c)
        sh=P.iloc[ids].mean(axis=0)
        lift=(sh/global_mean.replace(0,np.nan)).sort_values(ascending=False)
        out[c]=set(lift.head(n).index)
    return out

# [Anotación · líneas 85–119] `report` lee los CSV de estabilidad y escribe `ESTABILIDAD_CLUSTERS.md` con el
#   índice de Rand ajustado (mediana, mínimo y máximo) de cada control y la estabilidad de pertenencia por
#   grupo.
def report(outdir):
    km=pd.read_csv(outdir/"stability_kmeans_seeds.csv")
    boot=pd.read_csv(outdir/"stability_bootstrap.csv")
    rf=pd.read_csv(outdir/"stability_rf_seeds.csv")
    pc=pd.read_csv(outdir/"bootstrap_client_stability.csv")

    lines=["# Estabilidad de clusters z501","",
      "Esta validación **no elige k mediante silhouette**. Pregunta si la partición k=5 reaparece cuando perturbamos el algoritmo, los clientes y la representación del Random Forest.","",
      "## 1. Semilla de KMeans sobre la misma representación","",
      f"- ARI mediano: **{km.ari.median():.4f}**",
      f"- ARI mínimo: **{km.ari.min():.4f}**",
      f"- ARI máximo: **{km.ari.max():.4f}**","",
      "## 2. Bootstrap de clientes","",
      f"- ARI mediano: **{boot.ari.median():.4f}**",
      f"- ARI mínimo: **{boot.ari.min():.4f}**",
      f"- ARI máximo: **{boot.ari.max():.4f}**","",
      "Estabilidad de pertenencia individual tras hacer matching de etiquetas:","",
      "| cluster referencia | estabilidad media | P10 | P90 |",
      "|---:|---:|---:|---:|"]
    for c,g in pc.groupby("cluster_ref"):
        lines.append(f"| C{c} | {g.stability.mean():.3f} | {g.stability.quantile(.10):.3f} | {g.stability.quantile(.90):.3f} |")
    lines += ["","## 3. Reconstrucción RF + muestra de fieles con otras semillas","",
      "| seed | OOB | ARI vs referencia | overlap medio top-10 atributos |",
      "|---:|---:|---:|---:|"]
    for r in rf.itertuples():
        lines.append(f"| {r.seed} | {r.oob:.4f} | {r.ari:.4f} | {r.top10_overlap_mean:.3f} |")
    lines += ["","## 4. Otras resoluciones de k","",
      "El archivo k_resolution_crosswalk.csv muestra cómo cada C1–C5 se reparte cuando usamos k=3,4,6,7. Se interpreta como **fusión/subdivisión**, no como concurso para encontrar un k verdadero.","",
      "## Regla de interpretación","",
      "- ARI alto bajo semillas: KMeans no depende demasiado de una inicialización particular.",
      "- ARI alto bajo bootstrap: la geometría de la partición es reproducible al perturbar clientes.",
      "- ARI alto al reconstruir RF: los perfiles no dependen sólo de una muestra de fieles o un bosque particular.",
      "- Un cluster que se divide al aumentar k pero conserva su familia de atributos puede representar una familia estable con subtipos.",
      "- Un cluster que cambia de identidad o membresía en todas las perturbaciones debe narrarse con más cautela.",""]
    (outdir/"ESTABILIDAD_CLUSTERS.md").write_text("\n".join(lines),encoding="utf-8")

# [Anotación · líneas 121–131] `main` lee el dataset, calcula el perfil de referencia con semilla 214363 y 300
#   árboles, corre KMeans con k = 5, renumera por tamaño y escribe `reference_labels.csv` con
#   `numero_de_cliente` y `cluster_ref`. Ese archivo es la entrada de grupos del modelo final.
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args(); args.out.mkdir(parents=True,exist_ok=True)
    full=load_full(args.data)

    print("Referencia RF/P")
    rf0,P0=fit_profile(full,SEED,N_TREES)
    km0,raw0=fit_k(P0,5,SEED); ref=size_remap(raw0)
    pd.DataFrame({ID:P0.index,"cluster_ref":ref}).to_csv(args.out/"reference_labels.csv",index=False)

# [Anotación · líneas 133–138] Repite KMeans con 20 semillas sobre el mismo perfil y guarda el índice de Rand
#   ajustado contra la referencia en `stability_kmeans_seeds.csv`.
    print("KMeans seeds")
    rows=[]
    for s in [17,101,202,303,404,505,606,707,808,909,1010,1111,1212,1313,1414,1515,1616,1717,1818,1919]:
        km,p=fit_k(P0,5,s)
        rows.append({"seed":s,"ari":adjusted_rand_score(ref,p),"inertia":km.inertia_})
    pd.DataFrame(rows).to_csv(args.out/"stability_kmeans_seeds.csv",index=False)

# [Anotación · líneas 140–152] Hace 30 remuestreos con reposición de clientes, ajusta KMeans en cada uno,
#   empareja etiquetas con la referencia y guarda el índice de Rand ajustado y, por cliente, la fracción de
#   remuestreos en que conserva su grupo.
    print("Bootstrap customers")
    rng=np.random.default_rng(SEED); brow=[]; same=np.zeros((len(ref),30),dtype=np.int8)
    n=len(P0)
    for b in range(30):
        idx=rng.integers(0,n,size=n)
        km,p=fit_k(P0,5,SEED+b+1,weights_idx=idx)
        mapped,mapping,tab=best_map(ref,p)
        ari=adjusted_rand_score(ref,p)
        same[:,b]=(mapped==ref)
        brow.append({"bootstrap":b+1,"ari":ari,"inertia":km.inertia_})
    pd.DataFrame(brow).to_csv(args.out/"stability_bootstrap.csv",index=False)
    stab=same.mean(axis=1)
    pd.DataFrame({ID:P0.index,"cluster_ref":ref,"stability":stab}).to_csv(args.out/"bootstrap_client_stability.csv",index=False)

# [Anotación · líneas 154–172] Reconstruye la muestra y el Random Forest con 5 semillas (17, 101, 202, 303 y
#   404), vuelve a agrupar y guarda el OOB, el índice de Rand ajustado, la superposición de las 10 variables
#   principales por grupo y los tamaños.
    print("RF/sample seeds")
    ref_top=top_features(P0,ref,10); rrows=[]
    for s in [17,101,202,303,404]:
        rf,P=fit_profile(full,s,N_TREES)
        P=P.reindex(P0.index)
        km,p=fit_k(P,5,SEED)
        mapped,mapping,tab=best_map(ref,p)
        ari=adjusted_rand_score(ref,p)
        tops=top_features(P,mapped,10)
        overlaps=[]
        for c in range(1,6):
            a=ref_top.get(c,set()); bb=tops.get(c,set())
            overlaps.append(len(a&bb)/len(a|bb) if a|bb else np.nan)
        rrows.append({
            "seed":s,"oob":rf.oob_score_,"ari":ari,
            "top10_overlap_mean":np.nanmean(overlaps),
            "cluster_sizes":json.dumps(pd.Series(mapped).value_counts().sort_index().to_dict())
        })
    pd.DataFrame(rrows).to_csv(args.out/"stability_rf_seeds.csv",index=False)

# [Anotación · líneas 174–190] Ajusta KMeans con k = 3, 4, 6 y 7 y guarda cómo se reparte cada grupo de
#   referencia en los grupos alternativos (`k_resolution_crosswalk.csv`). Por último escribe el informe.
    print("k resolution crosswalk")
    rows=[]
    for k in [3,4,6,7]:
        km,p=fit_k(P0,k,SEED)
        p=size_remap(p)
        tab=pd.crosstab(pd.Series(ref,name="cluster_ref"),pd.Series(p,name="cluster_alt"))
        for c in tab.index:
            den=tab.loc[c].sum()
            for alt,nc in tab.loc[c].items():
                rows.append({"k_alt":k,"cluster_ref":c,"cluster_alt":alt,"n":nc,"share_of_ref":nc/den})
    pd.DataFrame(rows).to_csv(args.out/"k_resolution_crosswalk.csv",index=False)

    report(args.out)
    print("Listo",args.out)

if __name__=="__main__":
    main()
```

### 2_variables/experimentos_20261006_m1_fe_masiva/run_screening.py

Paso 2. Construye el banco de variables derivadas (`fe_bank_dev`) llamando a `generate`. Sin `--solo-generar-fe` entrena además cuatro brazos de comparación masiva con 5 semillas; el README indica correrlo con ese flag.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–19] Importa numpy, pandas y yaml, agrega la carpeta `fe_amplia` al camino de
#   importación y trae `generate`, `sha256_file` y `cargar_bloques`. Lee `plan_screening.json` (brazos, meses,
#   semillas, cortes) y `config_screening.json` (lags y ventanas del generador).
#!/usr/bin/env python3
from __future__ import annotations
import argparse, gc, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
FE=HERE/"fe_amplia"
sys.path.insert(0,str(FE))
from generar_fe import generate, sha256_file
from cargar_bloques import cargar_bloques

KEYS=["numero_de_cliente","foto_mes"]
TARGET="clase_ternaria"
PLAN=json.loads((HERE/"plan_screening.json").read_text())
CONFIG=json.loads((HERE/"config_screening.json").read_text())

# [Anotación · líneas 21–26] Dos utilidades: escribir un JSON creando la carpeta si falta y calcular el
#   SHA-256 de una lista serializada.
def write_json(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2))

def hash_list(xs):
    return hashlib.sha256(json.dumps(xs,ensure_ascii=False).encode()).hexdigest()

# [Anotación · líneas 28–42] `ensure_bank` compara el SHA-256 del dataset con el del plan. Si el banco ya
#   existe con `manifest.json`, exige estado `completed`, la misma entrada y la misma configuración y lo
#   reutiliza; si la carpeta tiene contenido sin manifiesto, se detiene. Si no existe, llama a `generate` con
#   los 17 bloques de `generated_blocks` y los meses de salida 202103 a 202106.
def ensure_bank(data,bank):
    got=sha256_file(data)
    if got!=PLAN["dataset_sha256"]:
        raise ValueError("SHA del dataset no coincide con el padre M1")
    manifest=bank/"manifest.json"
    if manifest.exists():
        m=json.loads(manifest.read_text())
        if m.get("status")!="completed" or m.get("input_sha256")!=got or m.get("config")!=CONFIG:
            raise ValueError("Banco FE existente incompatible")
        print("REUSAR banco FE",bank,flush=True)
        return m
    if bank.exists() and any(bank.iterdir()):
        raise ValueError("Carpeta de banco no vacía sin manifest válido")
    print("GENERAR banco FE de desarrollo",flush=True)
    return generate(data,bank,CONFIG,blocks=PLAN["generated_blocks"],months=[202103,202104,202105,202106])

# [Anotación · líneas 44–53] `derived_for_arm` elige del catálogo las variables derivadas de cada brazo:
#   ninguna (F0_M1_RAW), las que piden al menos un mes de historia (F1_TEMPORAL_MASIVA), las que no piden
#   historia (F2_REPRESENTACION_MASIVA) o todas (F3_TOTAL_MASIVA).
def derived_for_arm(bank,arm):
    if arm=="F0_M1_RAW":return []
    cat=pd.read_csv(bank/"catalogo_features.csv")
    cat=cat[cat.status.eq("generated")].copy()
    mh=pd.to_numeric(cat.min_history,errors="coerce").fillna(0)
    if arm=="F1_TEMPORAL_MASIVA":s=cat.loc[mh.ge(1),"feature"]
    elif arm=="F2_REPRESENTACION_MASIVA":s=cat.loc[mh.eq(0),"feature"]
    elif arm=="F3_TOTAL_MASIVA":s=cat["feature"]
    else:raise ValueError(arm)
    return s.drop_duplicates().tolist()

# [Anotación · líneas 55–69] `load_arm` carga las variables originales (y las derivadas del brazo) y las
#   etiquetas de los meses pedidos, verifica que las claves coincidan fila a fila, que haya exactamente 152
#   variables originales y que no haya nombres repetidos.
def load_arm(bank,arm,months):
    derived=derived_for_arm(bank,arm)
    if arm=="F0_M1_RAW":
        df=pd.read_parquet(bank/"raw.parquet")
        df=df[df.foto_mes.isin(months)].reset_index(drop=True)
    else:
        df,_=cargar_bloques(bank,meses=months,incluir_raw=True,features=derived)
    lab=pd.read_parquet(bank/"etiquetas.parquet")
    lab=lab[lab.foto_mes.isin(months)].reset_index(drop=True)
    if not df[KEYS].equals(lab[KEYS]):raise ValueError("X/y desalineados")
    raw=[c for c in df.columns if c not in KEYS and not c.startswith("fe__")]
    if len(raw)!=152:raise ValueError(f"Se esperaban 152 RAW y hay {len(raw)}")
    feats=raw+derived
    if len(feats)!=len(set(feats)):raise ValueError("Features duplicadas")
    return df,lab,feats,derived

# [Anotación · líneas 71–78] `gains` ordena por puntaje descendente (desempata por `numero_de_cliente`) y,
#   para cada corte del plan (10.500, 11.000 y 11.500), calcula la ganancia: 1.072.500 por cada BAJA+2 incluido
#   menos 27.500 por cada uno de los demás.
def gains(ids,y,scores):
    order=np.lexsort((np.asarray(ids,np.int64),-np.asarray(scores,float)))
    out={}
    for n in PLAN["cuts"]:
        z=np.asarray(y,np.int8)[order[:n]]
        hits=int(z.sum())
        out[n]=int(hits*1072500-(n-hits)*27500)
    return out

# [Anotación · líneas 80–85] `fit_model` entrena un LightGBM con los parámetros recibidos más la semilla, la
#   cantidad de hilos y `deterministic=True`, con las rondas del plan (300).
def fit_model(x,y,params,seed,threads):
    import lightgbm as lgb
    p=dict(params)
    p.update(seed=int(seed),num_threads=int(threads),deterministic=True)
    ds=lgb.Dataset(x,label=y,free_raw_data=False)
    return lgb.train(p,ds,num_boost_round=int(PLAN["rounds"]))

# [Anotación · líneas 87–135] `run_one` evalúa un brazo en un fold (mayo: entrena 202103 y evalúa 202105;
#   junio: entrena 202103–202104 y evalúa 202106) con clase binaria BAJA+2. Para cada una de las 5 semillas
#   entrena o reutiliza el `.npz` guardado, guarda puntajes e importancia por ganancia, y escribe
#   `por_seed.csv`, `importancias.csv` (ganancia media, semillas con ganancia positiva y rango mediano) y
#   `resumen.json` con la media y el desvío de la ganancia promedio de los tres cortes y la ganancia del
#   promedio de semillas.
def run_one(bank,out,arm,fold_name,params,threads):
    fold=PLAN["folds"][fold_name]
    months=sorted(set(fold["train"]+[fold["eval"]]))
    df,lab,feats,derived=load_arm(bank,arm,months)
    tr=df.foto_mes.isin(fold["train"]).to_numpy()
    ev=df.foto_mes.eq(fold["eval"]).to_numpy()
    ytr=lab.loc[tr,TARGET].eq("BAJA+2").to_numpy(np.int8)
    yev=lab.loc[ev,TARGET].eq("BAJA+2").to_numpy(np.int8)
    ids=df.loc[ev,"numero_de_cliente"].to_numpy(np.int64)
    root=out/"evaluacion"/fold_name/arm
    root.mkdir(parents=True,exist_ok=True)
    write_json(root/"features.json",{"features":feats,"derived":derived,"hash":hash_list(feats)})
    xtr=df.loc[tr,feats]
    xev=df.loc[ev,feats]
    rows=[];scores_all=[];imps=[]
    for seed in PLAN["seeds"]:
        cp=root/f"seed_{seed}.npz"
        if cp.exists():
            z=np.load(cp,allow_pickle=False)
            scores=z["scores"];imp=z["gain"]
            print("REUSAR",arm,fold_name,seed,flush=True)
        else:
            print("ENTRENAR",arm,fold_name,seed,"features",len(feats),flush=True)
            model=fit_model(xtr,ytr,params,seed,threads)
            scores=model.predict(xev,num_threads=threads)
            imp=model.feature_importance(importance_type="gain").astype(float)
            np.savez_compressed(cp,scores=scores,gain=imp,ids=ids,y=yev)
            del model
        g=gains(ids,yev,scores)
        rows.append({"seed":seed,
          "ganancia_10500":g[10500],"ganancia_11000":g[11000],"ganancia_11500":g[11500],
          "ganancia_banda":float(np.mean([g[10500],g[11000],g[11500]]))})
        scores_all.append(scores);imps.append(imp)
    pd.DataFrame(rows).to_csv(root/"por_seed.csv",index=False)
    imp=np.vstack(imps)
    rank=np.vstack([pd.Series(-v).rank(method="min").to_numpy() for v in imp])
    fi=pd.DataFrame({"feature":feats,"gain_medio":imp.mean(0),
      "seeds_gain_positivo":(imp>0).sum(0),"rank_mediana":np.median(rank,axis=0),
      "es_derivada":[x in set(derived) for x in feats]})
    fi.sort_values(["rank_mediana","gain_medio"],ascending=[True,False]).to_csv(root/"importancias.csv",index=False)
    ens=np.mean(np.vstack(scores_all),axis=0);ge=gains(ids,yev,ens)
    rr=pd.DataFrame(rows)
    summary={"arm":arm,"fold":fold_name,"n_features":len(feats),"n_derived":len(derived),
      "n_train":int(tr.sum()),"n_eval":int(ev.sum()),"media_banda":float(rr.ganancia_banda.mean()),
      "sd_banda":float(rr.ganancia_banda.std(ddof=1)),"media_11000":float(rr.ganancia_11000.mean()),
      "sd_11000":float(rr.ganancia_11000.std(ddof=1)),"ensemble":{str(k):v for k,v in ge.items()}}
    write_json(root/"resumen.json",summary)
    del df,lab,xtr,xev,imp,rank,fi,scores_all,imps
    gc.collect()

# [Anotación · líneas 137–166] `summarize` resta, semilla por semilla, la ganancia de cada brazo y la de
#   F0_M1_RAW y escribe `comparacion_screening.csv` (diferencia media, desvío y fracción de semillas a favor).
#   Después arma `shortlist_preliminar.csv` con las 20 derivadas de menor rango mediano por brazo entre las que
#   tienen ganancia positiva en al menos 3 semillas.
def summarize(out):
    rows=[]
    for fold in PLAN["folds"]:
        bp=out/"evaluacion"/fold/"F0_M1_RAW"/"por_seed.csv"
        if not bp.exists():continue
        b=pd.read_csv(bp).set_index("seed")
        for arm,spec in PLAN["arms"].items():
            if arm=="F0_M1_RAW" or fold not in spec["folds"]:continue
            p=out/"evaluacion"/fold/arm/"por_seed.csv"
            if not p.exists():continue
            a=pd.read_csv(p).set_index("seed")
            common=sorted(set(a.index)&set(b.index))
            d=a.loc[common,"ganancia_banda"]-b.loc[common,"ganancia_banda"]
            d11=a.loc[common,"ganancia_11000"]-b.loc[common,"ganancia_11000"]
            rows.append({"fold":fold,"arm":arm,"delta_banda_medio":float(d.mean()),
              "delta_banda_sd":float(d.std(ddof=1)),"fraccion_mejora":float((d>0).mean()),
              "delta_11000_medio":float(d11.mean()),"n_seeds":len(common)})
    comp=pd.DataFrame(rows);comp.to_csv(out/"comparacion_screening.csv",index=False)
    short=[]
    for fold in PLAN["folds"]:
        for arm,spec in PLAN["arms"].items():
            if arm=="F0_M1_RAW" or fold not in spec["folds"]:continue
            p=out/"evaluacion"/fold/arm/"importancias.csv"
            if not p.exists():continue
            d=pd.read_csv(p)
            d=d[d.es_derivada.astype(bool)&d.seeds_gain_positivo.ge(PLAN["shortlist"]["requires_nonzero_gain_seeds"])]
            d=d.sort_values(["rank_mediana","gain_medio"],ascending=[True,False]).head(PLAN["shortlist"]["top_per_arm"]).copy()
            d.insert(0,"arm",arm);d.insert(0,"fold",fold);short.append(d)
    if short:pd.concat(short,ignore_index=True).to_csv(out/"shortlist_preliminar.csv",index=False)
    return comp

# [Anotación · líneas 168–189] `main` recibe `--data`, `--out`, `--threads` (6), `--solo-generar-fe` y
#   `--arms`. Asegura el banco en `<out>/fe_bank_dev` y guarda su manifiesto. Con `--solo-generar-fe` termina
#   ahí; si no, lee los parámetros `lightgbm.base` de `vendor/comun/config.yaml`, corre cada brazo en sus folds
#   e imprime la comparación.
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--threads",type=int,default=6)
    ap.add_argument("--solo-generar-fe",action="store_true")
    ap.add_argument("--arms",nargs="*",choices=list(PLAN["arms"]))
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    bank=a.out/"fe_bank_dev"
    m=ensure_bank(a.data,bank);write_json(a.out/"00_manifest_fe.json",m)
    if a.solo_generar_fe:
        print("OK: FE generadas; no se entrenaron modelos");return
    params=yaml.safe_load((ROOT/"vendor/comun/config.yaml").read_text())["lightgbm"]["base"]
    arms=a.arms or list(PLAN["arms"])
    for arm in arms:
        for fold in PLAN["arms"][arm]["folds"]:
            run_one(bank,a.out,arm,fold,params,a.threads)
    comp=summarize(a.out)
    print(comp.to_string(index=False) if len(comp) else "Sin comparaciones")
    print("No genera submits ni usa agosto.")

if __name__=="__main__":main()
```

### 2_variables/experimentos_20261006_m1_fe_masiva/run_s3_confirm_c3.py

Paso 2. Define el conjunto C3 a partir del catálogo del banco, entrena con 20 semillas un modelo con las variables originales y otro con C3 (202103–202104 contra 202106) y deja la lista de variables, los puntajes por semilla y `confirmacion_c3.json`, que los scripts del paso 4 exigen.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–19] Importa las mismas piezas que `run_screening.py` y lee dos planes:
#   `plan_s3_confirm_c3.json` (fold, 20 semillas, cortes y regla de decisión) y `plan_s2_familias.json` (qué
#   bloques forman cada familia).
#!/usr/bin/env python3
from __future__ import annotations
import argparse, gc, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
FE=HERE/"fe_amplia"
sys.path.insert(0,str(FE))
from cargar_bloques import cargar_bloques
from generar_fe import sha256_file

PLAN=json.loads((HERE/"plan_s3_confirm_c3.json").read_text())
S2PLAN=json.loads((HERE/"plan_s2_familias.json").read_text())
KEYS=["numero_de_cliente","foto_mes"]
TARGET="clase_ternaria"

# [Anotación · líneas 21–26] Dos utilidades: escribir un JSON y calcular el SHA-256 de una lista serializada.
def write_json(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2))

def hash_list(xs):
    return hashlib.sha256(json.dumps(xs,ensure_ascii=False).encode()).hexdigest()

# [Anotación · líneas 28–46] `select_features` arma C3 desde el catálogo del banco: de la familia S2_HIST_CORE
#   (bloques `historia_numerica`, `transiciones_numericas`, `recencia`, `categoricas` e `historia_relaciones`)
#   toma las variables que piden al menos un mes de historia; de S2_TARJETAS_RATIOS (bloques `tarjetas` y
#   `ratios`), las que no piden historia. C3 es la unión sin repetidos; se detiene si alguna parte queda vacía.
def select_features(bank):
    cat=pd.read_csv(bank/"catalogo_features.csv")
    cat=cat[cat.status.eq("generated")].copy()
    mh=pd.to_numeric(cat.min_history,errors="coerce").fillna(0)

    hist=S2PLAN["arms"]["S2_HIST_CORE"]
    d=cat[cat.block.isin(hist["blocks"])].copy()
    mh_d=pd.to_numeric(d.min_history,errors="coerce").fillna(0)
    hist_features=d.loc[mh_d.ge(1),"feature"].drop_duplicates().tolist()

    tr=S2PLAN["arms"]["S2_TARJETAS_RATIOS"]
    d2=cat[cat.block.isin(tr["blocks"])].copy()
    mh2=pd.to_numeric(d2.min_history,errors="coerce").fillna(0)
    card_features=d2.loc[mh2.eq(0),"feature"].drop_duplicates().tolist()

    c3=list(dict.fromkeys(hist_features+card_features))
    if not hist_features or not card_features or not c3:
        raise ValueError("C3 quedó sin features")
    return hist_features,card_features,c3

# [Anotación · líneas 48–63] `load_arm` carga los meses del fold (202103 y 202104 para entrenar, 202106 para
#   evaluar) con las variables originales y las derivadas pedidas, junto con las etiquetas, y repite los
#   controles de alineación y de 152 variables originales.
def load_arm(bank,derived):
    fold=PLAN["fold"]
    months=sorted(set(fold["train"]+[fold["eval"]]))
    if derived:
        df,_=cargar_bloques(bank,meses=months,incluir_raw=True,features=derived)
    else:
        df=pd.read_parquet(bank/"raw.parquet")
        df=df[df.foto_mes.isin(months)].reset_index(drop=True)
    lab=pd.read_parquet(bank/"etiquetas.parquet")
    lab=lab[lab.foto_mes.isin(months)].reset_index(drop=True)
    if not df[KEYS].equals(lab[KEYS]):raise ValueError("X/y desalineados")
    raw=[c for c in df.columns if c not in KEYS and not c.startswith("fe__")]
    if len(raw)!=152:raise ValueError(f"RAW != 152: {len(raw)}")
    feats=raw+derived
    if len(feats)!=len(set(feats)):raise ValueError("Features duplicadas")
    return df,lab,feats

# [Anotación · líneas 65–82] `gains` calcula ganancia y cantidad de BAJA+2 incluidos en los cortes 10.500,
#   11.000 y 11.500; `fit_model` entrena un LightGBM de 300 rondas con la semilla indicada y
#   `deterministic=True`.
def gains(ids,y,scores):
    order=np.lexsort((np.asarray(ids,np.int64),-np.asarray(scores,float)))
    out={}
    for n in PLAN["cuts"]:
        z=np.asarray(y,np.int8)[order[:n]]
        hits=int(z.sum())
        out[n]={
            "ganancia":int(hits*1072500-(n-hits)*27500),
            "hits_baja2":hits
        }
    return out

def fit_model(x,y,params,seed,threads):
    import lightgbm as lgb
    p=dict(params)
    p.update(seed=int(seed),num_threads=int(threads),deterministic=True)
    ds=lgb.Dataset(x,label=y,free_raw_data=False)
    return lgb.train(p,ds,num_boost_round=int(PLAN["rounds"]))

# [Anotación · líneas 84–135] `run_arm` entrena un brazo con clase binaria BAJA+2. Escribe `features.json` con
#   la lista ordenada de variables (las 152 originales seguidas de las derivadas) y su hash. Para cada una de
#   las 20 semillas entrena o reutiliza el `.npz`, que guarda puntajes de 202106, importancia, clientes y clase.
#   Deja `por_seed.csv`, `importancias.csv` y `ensemble.json` con la ganancia del promedio de semillas.
def run_arm(bank,out,name,derived,params,threads):
    fold=PLAN["fold"]
    df,lab,feats=load_arm(bank,derived)
    tr=df.foto_mes.isin(fold["train"]).to_numpy()
    ev=df.foto_mes.eq(fold["eval"]).to_numpy()
    ytr=lab.loc[tr,TARGET].eq("BAJA+2").to_numpy(np.int8)
    yev=lab.loc[ev,TARGET].eq("BAJA+2").to_numpy(np.int8)
    ids=df.loc[ev,"numero_de_cliente"].to_numpy(np.int64)
    root=out/name
    root.mkdir(parents=True,exist_ok=True)
    write_json(root/"features.json",{
        "arm":name,"features":feats,"derived":derived,
        "n_raw":152,"n_derived":len(derived),"hash":hash_list(feats)
    })
    xtr=df.loc[tr,feats];xev=df.loc[ev,feats]
    rows=[];imps=[];scores_all=[]
    for seed in PLAN["seeds"]:
        cp=root/f"seed_{seed}.npz"
        if cp.exists():
            z=np.load(cp,allow_pickle=False)
            scores=z["scores"];imp=z["gain"]
            print("REUSAR",name,seed,flush=True)
        else:
            print("ENTRENAR",name,seed,"features",len(feats),flush=True)
            model=fit_model(xtr,ytr,params,seed,threads)
            scores=model.predict(xev,num_threads=threads)
            imp=model.feature_importance(importance_type="gain").astype(float)
            np.savez_compressed(cp,scores=scores,gain=imp,ids=ids,y=yev)
            del model
        g=gains(ids,yev,scores)
        rows.append({
            "seed":seed,
            "ganancia_10500":g[10500]["ganancia"],
            "ganancia_11000":g[11000]["ganancia"],
            "ganancia_11500":g[11500]["ganancia"],
            "ganancia_banda":float(np.mean([g[10500]["ganancia"],g[11000]["ganancia"],g[11500]["ganancia"]]))
        })
        imps.append(imp);scores_all.append(scores)
    pd.DataFrame(rows).to_csv(root/"por_seed.csv",index=False)
    imp=np.vstack(imps)
    pd.DataFrame({
        "feature":feats,
        "gain_medio":imp.mean(0),
        "seeds_gain_positivo":(imp>0).sum(0),
        "es_derivada":[f in set(derived) for f in feats]
    }).sort_values("gain_medio",ascending=False).to_csv(root/"importancias.csv",index=False)
    ens=np.mean(np.vstack(scores_all),axis=0)
    write_json(root/"ensemble.json",{
        "cuts":{str(n):gains(ids,yev,ens)[n] for n in PLAN["cuts"]}
    })
    del df,lab,xtr,xev,imp,imps,scores_all
    gc.collect()

# [Anotación · líneas 137–172] `compare` calcula por semilla la diferencia C3 − M1_RAW en la ganancia promedio
#   de los tres cortes y en el corte 11.000, guarda `deltas_pareados.csv` y escribe `confirmacion_c3.json` con
#   medias, mediana, semillas a favor y `promote_to_tuning`, que es verdadero si la media y la mediana de la
#   diferencia de banda y la media en 11.000 son positivas y al menos 60 % de las semillas da diferencia
#   positiva.
def compare(out):
    a=pd.read_csv(out/"M1_RAW"/"por_seed.csv").set_index("seed")
    b=pd.read_csv(out/"C3_HIST_MAS_TARJETAS"/"por_seed.csv").set_index("seed")
    seeds=PLAN["seeds"]
    if set(seeds)!=set(a.index) or set(seeds)!=set(b.index):
        raise ValueError("Seeds incompletas o incompatibles")
    d=(b.loc[seeds,"ganancia_banda"]-a.loc[seeds,"ganancia_banda"]).astype(float)
    d11=(b.loc[seeds,"ganancia_11000"]-a.loc[seeds,"ganancia_11000"]).astype(float)
    per=pd.DataFrame({
        "seed":seeds,
        "delta_banda":d.to_numpy(),
        "delta_11000":d11.to_numpy()
    })
    per.to_csv(out/"deltas_pareados.csv",index=False)
    summary={
        "n_seeds":len(seeds),
        "delta_banda_medio":float(d.mean()),
        "delta_banda_sd":float(d.std(ddof=1)),
        "delta_banda_mediana":float(d.median()),
        "positive_seed_fraction":float((d>0).mean()),
        "wins":int((d>0).sum()),
        "ties":int((d==0).sum()),
        "losses":int((d<0).sum()),
        "delta_11000_medio":float(d11.mean()),
        "delta_11000_mediana":float(d11.median())
    }
    promote=(
        summary["delta_banda_medio"]>0 and
        summary["delta_11000_medio"]>0 and
        summary["delta_banda_mediana"]>0 and
        summary["positive_seed_fraction"]>=0.60
    )
    summary["promote_to_tuning"]=bool(promote)
    summary["rule"]=PLAN["decision"]["promote_if_all"]
    write_json(out/"confirmacion_c3.json",summary)
    return summary

# [Anotación · líneas 174–199] `main` verifica el SHA-256 del dataset y que el banco del paso anterior esté
#   completo, selecciona las variables, guarda `00_c3_features.json`, lee los parámetros `lightgbm.base` de
#   `config.yaml`, entrena el brazo M1_RAW (sólo variables originales) y el brazo C3_HIST_MAS_TARJETAS, compara
#   e imprime el resumen.
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",required=True,type=Path)
    ap.add_argument("--s1-root",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--threads",type=int,default=6)
    a=ap.parse_args()
    if sha256_file(a.data)!=PLAN["dataset_sha256"]:raise ValueError("Dataset distinto")
    bank=a.s1_root/"fe_bank_dev"
    m=json.loads((bank/"manifest.json").read_text())
    if m.get("status")!="completed":raise ValueError("Banco FE S1 incompleto")
    hist,cards,c3=select_features(bank)
    a.out.mkdir(parents=True,exist_ok=True)
    write_json(a.out/"00_c3_features.json",{
        "historia_n":len(hist),"tarjetas_ratios_n":len(cards),
        "c3_n":len(c3),"historia":hist,"tarjetas_ratios":cards,"c3":c3
    })
    params=yaml.safe_load((ROOT/"vendor/comun/config.yaml").read_text())["lightgbm"]["base"]
    run_arm(bank,a.out,"M1_RAW",[],params,a.threads)
    run_arm(bank,a.out,"C3_HIST_MAS_TARJETAS",c3,params,a.threads)
    summary=compare(a.out)
    print("\n=== S3 CONFIRMACION C3 ===")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("\nNo usa agosto, no tunea y no genera submits.")

if __name__=="__main__":main()
```

### 2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_semantica.py

Lee y valida `catalogo_fuentes.csv`, que clasifica las 152 variables originales por tipo (numérica, categórica, fecha relativa o reloj) y modo de historia; esa clasificación decide qué transformaciones recibe cada variable.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–21] Declara las columnas del catálogo de fuentes, los tipos admitidos (`numeric`,
#   `category`, `relative_date`, `clock`), los modos de historia admitidos y el conjunto de los 152 nombres de
#   variables esperados.
"""Catálogo semántico de los 152 predictores fuente, sin selección por target.

El catálogo distingue representaciones y habilita operaciones compatibles;
no calcula transformaciones, no imputa y no redefine valores de la fuente.
"""
from __future__ import annotations

import csv
from pathlib import Path

FIELDS = (
    'variable', 'kind', 'subtype', 'family', 'unit', 'history_mode',
    'zero_interpretable', 'signed', 'caution',
)
KINDS = frozenset({'numeric', 'category', 'relative_date', 'clock'})
HISTORY_MODES = frozenset({
    'nonnegative_flow', 'signed_flow', 'stock', 'count_stock',
    'rolling_flow', 'nominal', 'relative_date', 'clock', 'unknown',
})
STRUCTURAL_COLUMNS = frozenset({'numero_de_cliente', 'foto_mes', 'clase_ternaria'})
EXPECTED_VARIABLES = frozenset(('Master_Finiciomora', 'Master_Fvencimiento', 'Master_cadelantosefectivo', 'Master_cconsumos', 'Master_delinquency', 'Master_fechaalta', 'Master_fultimo_cierre', 'Master_madelantodolares', 'Master_madelantopesos', 'Master_mconsumosdolares', 'Master_mconsumospesos', 'Master_mconsumototal', 'Master_mfinanciacion_limite', 'Master_mlimitecompra', 'Master_mpagado', 'Master_mpagominimo', 'Master_mpagosdolares', 'Master_mpagospesos', 'Master_msaldodolares', 'Master_msaldopesos', 'Master_msaldototal', 'Master_status', 'Visa_Finiciomora', 'Visa_Fvencimiento', 'Visa_cadelantosefectivo', 'Visa_cconsumos', 'Visa_delinquency', 'Visa_fechaalta', 'Visa_fultimo_cierre', 'Visa_madelantodolares', 'Visa_madelantopesos', 'Visa_mconsumosdolares', 'Visa_mconsumospesos', 'Visa_mconsumototal', 'Visa_mfinanciacion_limite', 'Visa_mlimitecompra', 'Visa_mpagado', 'Visa_mpagominimo', 'Visa_mpagosdolares', 'Visa_mpagospesos', 'Visa_msaldodolares', 'Visa_msaldopesos', 'Visa_msaldototal', 'Visa_status', 'active_quarter', 'catm_trx', 'catm_trx_other', 'ccaja_ahorro', 'ccaja_seguridad', 'ccajas_consultas', 'ccajas_depositos', 'ccajas_extracciones', 'ccajas_otras', 'ccajas_transacciones', 'ccajeros_propios_descuentos', 'ccallcenter_transacciones', 'ccheques_depositados', 'ccheques_depositados_rechazados', 'ccheques_emitidos', 'ccheques_emitidos_rechazados', 'ccomisiones_mantenimiento', 'ccomisiones_otras', 'ccuenta_corriente', 'ccuenta_debitos_automaticos', 'cdescubierto_preacordado', 'cextraccion_autoservicio', 'cforex', 'cforex_buy', 'cforex_sell', 'chomebanking_transacciones', 'cinversion1', 'cinversion2', 'cliente_antiguedad', 'cliente_edad', 'cliente_vip', 'cmobile_app_trx', 'cpagodeservicios', 'cpagomiscuentas', 'cpayroll2_trx', 'cpayroll_trx', 'cplazo_fijo', 'cprestamos_hipotecarios', 'cprestamos_personales', 'cprestamos_prendarios', 'cproductos', 'cseguro_accidentes_personales', 'cseguro_auto', 'cseguro_vida', 'cseguro_vivienda', 'ctarjeta_debito', 'ctarjeta_debito_transacciones', 'ctarjeta_master', 'ctarjeta_master_debitos_automaticos', 'ctarjeta_master_descuentos', 'ctarjeta_master_transacciones', 'ctarjeta_visa', 'ctarjeta_visa_debitos_automaticos', 'ctarjeta_visa_descuentos', 'ctarjeta_visa_transacciones', 'ctransferencias_emitidas', 'ctransferencias_recibidas', 'ctrx_quarter', 'internet', 'mactivos_margen', 'matm', 'matm_other', 'mautoservicio', 'mcaja_ahorro', 'mcaja_ahorro_adicional', 'mcaja_ahorro_dolares', 'mcajeros_propios_descuentos', 'mcheques_depositados', 'mcheques_depositados_rechazados', 'mcheques_emitidos', 'mcheques_emitidos_rechazados', 'mcomisiones', 'mcomisiones_mantenimiento', 'mcomisiones_otras', 'mcuenta_corriente', 'mcuenta_corriente_adicional', 'mcuenta_debitos_automaticos', 'mcuentas_saldo', 'mextraccion_autoservicio', 'mforex_buy', 'mforex_sell', 'minversion1_dolares', 'minversion1_pesos', 'minversion2', 'mpagodeservicios', 'mpagomiscuentas', 'mpasivos_margen', 'mpayroll', 'mpayroll2', 'mplazo_fijo_dolares', 'mplazo_fijo_pesos', 'mprestamos_hipotecarios', 'mprestamos_personales', 'mprestamos_prendarios', 'mrentabilidad', 'mrentabilidad_annual', 'mtarjeta_master_consumo', 'mtarjeta_master_descuentos', 'mtarjeta_visa_consumo', 'mtarjeta_visa_descuentos', 'mtransferencias_emitidas', 'mtransferencias_recibidas', 'mttarjeta_master_debitos_automaticos', 'mttarjeta_visa_debitos_automaticos', 'tcallcenter', 'tcuentas', 'thomebanking', 'tmobile_app'))


# [Anotación · líneas 24–30] `_boolean` convierte textos `true/false` o `1/0` en booleanos y se detiene con
#   otro valor.
def _boolean(value: str, field: str, variable: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {'true', '1'}:
        return True
    if normalized in {'false', '0'}:
        return False
    raise ValueError(f'{variable}: {field} debe ser true/false o 1/0; recibido {value!r}')


# [Anotación · líneas 33–73] `load_catalog` lee `catalogo_fuentes.csv` y valida: columnas en el orden
#   esperado, 152 filas sin nombres vacíos ni repetidos, los mismos nombres que el conjunto esperado, tipo y
#   modo de historia admitidos, campos de subtipo, familia y unidad completos, y combinaciones compatibles entre
#   tipo y modo de historia.
def load_catalog(path=None) -> list[dict]:
    """Lee y valida el catálogo completo; devuelve booleanos reales.

    La ruta por defecto es ``catalogo_fuentes.csv`` junto a este módulo.
    Una copia externa debe conservar exactamente los 152 predictores y el
    esquema. La comprobación contra metadatos fuente se documenta en notas;
    el lector no necesita acceder a la base ni al target para funcionar.
    """
    source = Path(path) if path is not None else Path(__file__).with_name('catalogo_fuentes.csv')
    with source.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f'Esquema de catálogo inesperado. Se requieren, en orden: {FIELDS}')
        specs = [dict(row) for row in reader]
    if len(specs) != 152:
        raise ValueError(f'El catálogo completo requiere 152 predictores; recibidos {len(specs)}')
    names = [r['variable'] for r in specs]
    if len(set(names)) != 152 or any(not name for name in names):
        raise ValueError('Variables vacías o duplicadas en el catálogo')
    if set(names) != EXPECTED_VARIABLES:
        missing = sorted(EXPECTED_VARIABLES.difference(names))
        extra = sorted(set(names).difference(EXPECTED_VARIABLES))
        raise ValueError(f'Cobertura de fuentes diferente: faltan={missing}, extras={extra}')
    if STRUCTURAL_COLUMNS.intersection(names):
        raise ValueError('ID, foto_mes y target no pertenecen al catálogo de predictores')
    for spec in specs:
        variable = spec['variable']
        if spec['kind'] not in KINDS or spec['history_mode'] not in HISTORY_MODES:
            raise ValueError(f'{variable}: kind/history_mode no admitido')
        for field in ('zero_interpretable', 'signed'):
            spec[field] = _boolean(spec[field], field, variable)
        if not spec['subtype'] or not spec['family'] or not spec['unit']:
            raise ValueError(f'{variable}: subtype/family/unit incompleto')
        expected = {'category':'nominal', 'relative_date':'relative_date', 'clock':'clock'}
        if spec['kind'] in expected and spec['history_mode'] != expected[spec['kind']]:
            raise ValueError(f'{variable}: combinación kind/history_mode incompatible')
        if spec['kind'] == 'numeric' and spec['history_mode'] in {'nominal','relative_date','clock'}:
            raise ValueError(f'{variable}: history_mode incompatible con numeric')
        if spec['history_mode'] == 'nonnegative_flow' and spec['signed']:
            raise ValueError(f'{variable}: flujo nonnegative marcado signed')
    return specs


# [Anotación · líneas 76–81] `make_specs` es un alias de `load_catalog`; `__all__` lista los nombres públicos.
def make_specs() -> list[dict]:
    """Alias sin efectos laterales para obtener el catálogo predeterminado."""
    return load_catalog()


__all__ = ['load_catalog', 'make_specs', 'FIELDS', 'KINDS', 'HISTORY_MODES']
```

### 2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/cargar_bloques.py

Lectura selectiva del banco: devuelve las variables originales más las derivadas pedidas para los meses indicados. La usan todos los scripts que entrenan o puntúan.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–6] Docstring e importaciones (pandas y el catálogo de fuentes).
"""Carga selectiva para ablaciones; NO construye un dataframe gigante por defecto."""
from pathlib import Path
import json
import pandas as pd
from fe_semantica import load_catalog

# [Anotación · líneas 7–19] `cargar_bloques` lee el manifiesto del banco (exige estado `completed`) y el
#   catálogo, y arma la selección por bloques o por lista explícita de variables; se detiene si se piden bloques
#   o variables que no existen.
def cargar_bloques(carpeta,bloques=None,meses=None,incluir_raw=True,features=None):
    root=Path(carpeta);manifest=json.loads((root/'manifest.json').read_text())
    if manifest['status']!='completed':raise ValueError('Ejecución incompleta')
    cat=pd.read_csv(root/'catalogo_features.csv')
    wanted=set(bloques or [])
    if not wanted and not features:raise ValueError('Elegir bloques o features explícitamente')
    unknown=wanted-set(cat.block)
    if unknown:raise ValueError(f'Bloques inexistentes:{sorted(unknown)}')
    sel=cat[cat.block.isin(wanted)] if wanted else cat
    if features is not None:
        unknown_features=set(features)-set(cat.feature)
        if unknown_features:raise ValueError(f'Features inexistentes:{sorted(unknown_features)}')
        sel=sel[sel.feature.isin(features)]
# [Anotación · líneas 20–34] Lee `raw.parquet` (o sólo las claves), filtra los meses pedidos y, para cada
#   archivo de partes, lee únicamente las columnas seleccionadas, verifica que las claves coincidan y las
#   agrega. Las variables registradas como totalmente faltantes se agregan como columnas de NaN. El orden final
#   es: columnas originales y luego las derivadas en el orden del catálogo.
    rawpath=root/('raw.parquet' if incluir_raw else 'claves.parquet')
    df=pd.read_parquet(rawpath)
    mask=df.foto_mes.isin(meses) if meses else pd.Series(True,index=df.index)
    base=df.loc[mask].reset_index(drop=True)
    pieces=[base]
    for rel,features in sel[sel.status.eq('generated')].groupby('file',sort=False):
        part=pd.read_parquet(root/rel,columns=['numero_de_cliente','foto_mes']+features.feature.tolist())
        if not part[['numero_de_cliente','foto_mes']].equals(df[['numero_de_cliente','foto_mes']]):
            raise ValueError(f'Claves desalineadas en {rel}')
        pieces.append(part.loc[mask,features.feature.tolist()].reset_index(drop=True))
    absent=sel.loc[sel.status.eq('all_missing_in_output'),'feature'].tolist()
    if absent:pieces.append(pd.DataFrame(float('nan'),index=base.index,columns=absent))
    result=pd.concat(pieces,axis=1)
    # Orden de schema estable aunque cambie qué columnas son totalmente NA.
    result=result[base.columns.tolist()+sel.feature.tolist()]
# [Anotación · líneas 35–38] Devuelve la tabla y la lista de columnas categóricas, según el catálogo de
#   fuentes y el tipo declarado de cada derivada.
    cats=([s['variable'] for s in load_catalog() if s['kind']=='category' and s['variable'] in base] +
          sel.loc[sel.feature_kind.eq('category'),'feature'].tolist())
    # Devuelve claves y tipos; el usuario separa X de claves e y antes de entrenar.
    return result, cats
```

### 2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_core.py

Clase `Panel` (orden por cliente y mes, lags por mes calendario exacto y percentil dentro del mes), utilidades de indicadores y cocientes, y el bloque `cobertura_panel`.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–7] Define las claves (`numero_de_cliente`, `foto_mes`) y el conjunto de columnas que
#   no pueden ser fuente de una variable: las claves, `clase_ternaria` y `clase_binaria`.
"""Primitivas del panel: sólo calendario actual/pasado, sin consultar el target."""
from __future__ import annotations
import numpy as np
import pandas as pd

KEYS = ['numero_de_cliente', 'foto_mes']
FORBIDDEN = {'numero_de_cliente', 'foto_mes', 'clase_ternaria', 'clase_binaria'}

# [Anotación · líneas 9–31] El constructor de `Panel` verifica que las claves existan, no sean nulas ni estén
#   repetidas y que `foto_mes` sea un AAAAMM entero con mes entre 1 y 12. Ordena por cliente y mes y guarda el
#   índice de mes (año × 12 + mes − 1), la fecha de fin de mes en días, un índice por cliente y mes y la lista
#   de filas de cada mes.
class Panel:
    def __init__(self, df, config=None):
        self.config = config or {}
        if not set(KEYS).issubset(df):
            raise ValueError('Faltan claves numero_de_cliente/foto_mes')
        if df[KEYS].isna().any().any() or df.duplicated(KEYS).any():
            raise ValueError('Claves nulas o cliente-mes duplicado')
        fm = pd.to_numeric(df.foto_mes, errors='raise').to_numpy(float)
        if not np.isfinite(fm).all() or not np.equal(fm, np.floor(fm)).all():
            raise ValueError('foto_mes debe ser un entero YYYYMM')
        if not (((fm % 100) >= 1) & ((fm % 100) <= 12)).all():
            raise ValueError('Mes inválido')
        self.df = df.sort_values(KEYS, kind='stable').reset_index(drop=True)
        self.n = len(self.df)
        self.columns = set(self.df.columns)
        self.month = self.df.foto_mes.to_numpy(dtype=np.int64)
        self.month_index = (self.month // 100) * 12 + self.month % 100 - 1
        # Convención del EDA: fecha de foto = fin del mes.
        dates = pd.to_datetime(self.df.foto_mes.astype(str), format='%Y%m') + pd.offsets.MonthEnd(0)
        self.days = dates.to_numpy(dtype='datetime64[D]').astype(np.int64)
        self.index = pd.MultiIndex.from_arrays([self.df.numero_de_cliente, self.month_index])
        self._indices = {}
        self._month_groups = [np.flatnonzero(self.month == m) for m in np.unique(self.month)]

# [Anotación · líneas 33–37] `get` devuelve una columna como vector de float64 y reemplaza los infinitos por
#   NaN.
    def get(self, name):
        x = pd.to_numeric(self.df[name], errors='raise').to_numpy(dtype=np.float64, na_value=np.nan)
        if np.isinf(x).any():
            x = x.copy(); x[np.isinf(x)] = np.nan
        return x

# [Anotación · líneas 39–60] `lag_index` busca, para cada fila, la fila del mismo cliente exactamente k meses
#   calendario antes; `lag` devuelve el valor de esa fila o NaN si no existe; `row_present` indica si existe.
    def lag_index(self, k):
        if not isinstance(k, (int, np.integer)) or k < 0:
            raise ValueError('lag debe ser entero no negativo')
        if k == 0:
            return np.arange(self.n)
        if k not in self._indices:
            previous = pd.MultiIndex.from_arrays([self.df.numero_de_cliente, self.month_index - k])
            self._indices[k] = self.index.get_indexer(previous)
        return self._indices[k]

    def lag(self, values, k):
        values = np.asarray(values, dtype=float)
        if values.shape != (self.n,):
            raise ValueError('Vector no alineado con panel')
        idx = self.lag_index(k)
        result = np.full(self.n, np.nan)
        valid = idx >= 0
        result[valid] = values[idx[valid]]
        return result

    def row_present(self, k):
        return self.lag_index(k) >= 0

# [Anotación · líneas 62–72] `rank` calcula, dentro de cada mes, el percentil entre 0 y 1 de los valores
#   finitos, con empates promediados.
    def rank(self, values):
        """Percentil [0,1] por foto completa, empates medios; no mira otros meses."""
        values = np.asarray(values, dtype=float)
        out = np.full(self.n, np.nan)
        for idx in self._month_groups:
            ok = np.isfinite(values[idx]); n = int(ok.sum())
            if not n:
                continue
            ranks = pd.Series(values[idx][ok]).rank(method='average').to_numpy()
            out[idx[ok]] = (ranks - 1) / (n - 1) if n > 1 else 0.0
        return out

# [Anotación · líneas 74–86] `flag` convierte una condición en 1/0 y deja NaN donde no es válida;
#   `safe_divide` divide sólo cuando numerador y denominador son finitos y el denominador es distinto de cero, y
#   devuelve NaN en el resto.
def flag(condition, valid):
    return np.where(valid, np.asarray(condition, bool).astype(float), np.nan)

def safe_divide(num, den, valid=None):
    num, den = np.asarray(num, float), np.asarray(den, float)
    ok = np.isfinite(num) & np.isfinite(den) & (den != 0)
    if valid is not None:
        ok &= valid
    out = np.full(np.broadcast_shapes(num.shape, den.shape), np.nan)
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        np.divide(num, den, out=out, where=ok)
    out[~np.isfinite(out)] = np.nan
    return out

# [Anotación · líneas 88–97] `generate_coverage` produce el bloque `cobertura_panel`: si existe la fila del
#   cliente k meses atrás, cuántas filas hay en cada ventana y si la ventana está completa.
def generate_coverage(panel, config):
    lags = config['lags']; windows = config['windows']
    def item(op, value, formula, history=0):
        return 'fe__panel__' + op, np.asarray(value, float), dict(block='cobertura_panel', sources=[], formula=formula, interpretation='Disponibilidad de filas; nunca se usa ausencia futura.', min_history=history, unit='meses/indicador', caution='No mide actividad; las fronteras del archivo censuran la historia.', feature_kind='numeric')
    for k in lags:
        yield item(f'fila_lag{k}', panel.row_present(k), f'existe fila del mismo cliente en t-{k}', k)
    for w in windows:
        nrows = sum(panel.row_present(k).astype(float) for k in range(w))
        yield item(f'filas_w{w}', nrows, f'filas presentes en [t-{w-1},t]', w-1)
        yield item(f'completo_w{w}', nrows == w, f'filas_w{w} == {w}', w-1)
```

### 2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_relaciones.py

Variables que combinan varias columnas del mismo mes (monto por operación, sumas y cocientes de tarjetas, funciones activas, productos, deuda, interacciones) y la historia de algunos de esos resúmenes. C3 usa los bloques `ratios`, `tarjetas` e `historia_relaciones`.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–11] Docstring del módulo e importación de numpy; el único nombre público es
#   `generate_relations`.
"""Candidate, target-free relations for the DMEyF panel.

Only raw columns and past/current snapshots are accessed.  Every yielded array
has one value per panel row; undefined quantities stay NaN.  This module proposes
features, it does not assert that they improve a predictive model.
"""
from __future__ import annotations

import numpy as np

__all__ = ["generate_relations"]

# [Anotación · líneas 13–42] `TICKETS`: 27 ternas (concepto, columna de monto, columna de cantidad) para
#   calcular el monto por operación: haberes, consumos de Visa y Master, extracciones, cajeros, transferencias,
#   pagos, débitos automáticos, descuentos, comisiones, cheques y compra y venta de moneda extranjera.
# Amount and count refer to the same named concept and monthly period.
TICKETS = (
    ("payroll", "mpayroll", "cpayroll_trx"),
    ("payroll2", "mpayroll2", "cpayroll2_trx"),
    ("visa", "mtarjeta_visa_consumo", "ctarjeta_visa_transacciones"),
    ("master", "mtarjeta_master_consumo", "ctarjeta_master_transacciones"),
    ("extraccion_autoservicio", "mextraccion_autoservicio", "cextraccion_autoservicio"),
    ("atm", "matm", "catm_trx"),
    ("atm_other", "matm_other", "catm_trx_other"),
    ("transferencias_recibidas", "mtransferencias_recibidas", "ctransferencias_recibidas"),
    ("transferencias_emitidas", "mtransferencias_emitidas", "ctransferencias_emitidas"),
    ("pagodeservicios", "mpagodeservicios", "cpagodeservicios"),
    ("pagomiscuentas", "mpagomiscuentas", "cpagomiscuentas"),
    ("debitos_cuenta", "mcuenta_debitos_automaticos", "ccuenta_debitos_automaticos"),
    ("debitos_visa", "mttarjeta_visa_debitos_automaticos", "ctarjeta_visa_debitos_automaticos"),
    ("debitos_master", "mttarjeta_master_debitos_automaticos", "ctarjeta_master_debitos_automaticos"),
    ("descuentos_debito", "mcajeros_propios_descuentos", "ccajeros_propios_descuentos"),
    ("descuentos_visa", "mtarjeta_visa_descuentos", "ctarjeta_visa_descuentos"),
    ("descuentos_master", "mtarjeta_master_descuentos", "ctarjeta_master_descuentos"),
    ("comisiones_mantenimiento", "mcomisiones_mantenimiento", "ccomisiones_mantenimiento"),
    ("comisiones_otras", "mcomisiones_otras", "ccomisiones_otras"),
    ("cheques_depositados", "mcheques_depositados", "ccheques_depositados"),
    ("cheques_emitidos", "mcheques_emitidos", "ccheques_emitidos"),
    ("cheques_depositados_rechazados", "mcheques_depositados_rechazados", "ccheques_depositados_rechazados"),
    ("cheques_emitidos_rechazados", "mcheques_emitidos_rechazados", "ccheques_emitidos_rechazados"),
    ("forex_buy", "mforex_buy", "cforex_buy"),
    ("forex_sell", "mforex_sell", "cforex_sell"),
    ("visa_detalle", "Visa_mconsumototal", "Visa_cconsumos"),
    ("master_detalle", "Master_mconsumototal", "Master_cconsumos"),
)

# [Anotación · líneas 44–73] `FUNCTIONS` agrupa columnas de cantidad en siete dominios de uso (haberes,
#   tarjetas, pagos, transferencias, cajeros y extracciones, digitales y atención); `CARD_FIELDS` lista 16
#   campos que existen con prefijo `Visa_` y `Master_`; `PRODUCTS` agrupa columnas de tenencia en nueve grupos
#   de productos.
# These seven domains are channels/functions, NOT mutually exclusive operations.
# Counts provide evidence of use.  Amounts, fees, profits, product stocks,
# nominal status codes and 'ever installed' flags are intentionally excluded.
FUNCTIONS = {
    "haberes": ("cpayroll_trx", "cpayroll2_trx"),
    "tarjetas": ("ctarjeta_debito_transacciones", "ctarjeta_visa_transacciones", "ctarjeta_master_transacciones"),
    "pagos": ("cpagomiscuentas", "cpagodeservicios", "ccuenta_debitos_automaticos", "ctarjeta_visa_debitos_automaticos", "ctarjeta_master_debitos_automaticos"),
    "transferencias": ("ctransferencias_recibidas", "ctransferencias_emitidas"),
    "cajeros_y_extracciones": ("cextraccion_autoservicio", "catm_trx", "catm_trx_other", "ccajas_extracciones"),
    "digitales": ("chomebanking_transacciones", "cmobile_app_trx"),
    "atencion": ("ccallcenter_transacciones", "ccajas_transacciones", "ccajas_consultas", "ccajas_depositos", "ccajas_otras"),
}

CARD_FIELDS = (
    "mfinanciacion_limite", "mlimitecompra", "msaldototal", "msaldopesos",
    "msaldodolares", "mconsumospesos", "mconsumosdolares", "mconsumototal",
    "madelantopesos", "madelantodolares", "mpagado", "mpagospesos",
    "mpagosdolares", "mpagominimo", "cconsumos", "cadelantosefectivo",
)
PRODUCTS = {
    "cuentas": ("ccuenta_corriente", "ccaja_ahorro"),
    "debito": ("ctarjeta_debito",),
    "credito": ("ctarjeta_visa", "ctarjeta_master"),
    "prestamos_personales": ("cprestamos_personales",),
    "prestamos_prendarios": ("cprestamos_prendarios",),
    "prestamos_hipotecarios": ("cprestamos_hipotecarios",),
    "plazo_fijo": ("cplazo_fijo",),
    "inversiones": ("cinversion1", "cinversion2"),
    "seguros": ("cseguro_vida", "cseguro_auto", "cseguro_vivienda", "cseguro_accidentes_personales"),
}


# [Anotación · líneas 76–132] Funciones auxiliares: cociente con denominador estrictamente positivo (NaN en
#   otro caso), indicador de actividad (1 si algún conteo es positivo, 0 sólo si todos son cero, NaN en el
#   resto), Y lógico de tres valores, suma que exige todos los sumandos finitos, conteo de valores finitos y
#   armado de los metadatos de cada variable.
def _safe_ratio(num, den, nonnegative_num=False):
    """Undefined denominator (including zero) is NaN; never add epsilon."""
    out = np.full(len(num), np.nan, dtype=np.float64)
    good = np.isfinite(num) & np.isfinite(den) & (den > 0)
    if nonnegative_num:
        good &= num >= 0
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        np.divide(num, den, out=out, where=good)
    out[~np.isfinite(out)] = np.nan
    return out


def _activity(arrays):
    """Positive evidence wins; inactivity requires every count observed as zero."""
    any_positive = np.zeros(len(arrays[0]), dtype=bool)
    all_zero = np.ones(len(arrays[0]), dtype=bool)
    for x in arrays:
        finite = np.isfinite(x)
        any_positive |= finite & (x > 0)
        all_zero &= finite & (x == 0)
    out = np.full(len(arrays[0]), np.nan, dtype=np.float64)
    out[all_zero] = 0.0
    out[any_positive] = 1.0
    return out


def _and(a, b):
    """Three-valued Boolean AND: false dominates unknown."""
    out = np.full(len(a), np.nan, dtype=np.float64)
    out[(a == 0) | (b == 0)] = 0.0
    out[(a == 1) & (b == 1)] = 1.0
    return out


def _strict_sum(arrays):
    """Arithmetic sum only when every required component is finite."""
    out = np.zeros(len(arrays[0]), dtype=np.float64)
    good = np.ones(len(out), dtype=bool)
    with np.errstate(over="ignore", invalid="ignore"):
        for x in arrays:
            good &= np.isfinite(x)
            out += x
    out[~good | ~np.isfinite(out)] = np.nan
    return out


def _n_finite(arrays, nonnegative=False):
    out = np.zeros(len(arrays[0]), dtype=np.float64)
    for x in arrays:
        out += np.isfinite(x) & ((x >= 0) if nonnegative else True)
    return out


def _meta(block, sources, formula, interpretation, unit, caution="", min_history=0):
    return dict(block=block, sources=list(dict.fromkeys(sources)), formula=formula,
                interpretation=interpretation, min_history=int(min_history),
                unit=unit, caution=caution)


# [Anotación · líneas 135–167] `generate_relations` termina sin producir nada si `relations` es falso. Define
#   `get` (lee una columna y verifica su forma) y `emit` (nombra la variable `fe__rel__<sufijo>`, pasa infinitos
#   a NaN y, si se pide, la guarda en `history` para calcular después su historia).
def generate_relations(panel, config):
    """Yield ``(name, values, metadata)``; ``relations=False`` disables the module.

    panel supplies df/get/lag/rank/columns/n.  panel.lag MUST enforce same-customer
    exact calendar lags; no row shift across an absent month is valid.  Filtering
    on metadata['block'] belongs to the caller.  Source absence skips a whole
    feature definition rather than silently redefining its denominator/domain.
    """
    if not config.get("relations", True):
        return
    available = set(panel.columns)
    n = int(panel.n)
    history = []
    has = lambda cols: all(c in available for c in cols)

    def get(v):
        # Borrow panel arrays read-only; never modify raw vectors in-place.
        out = np.asarray(panel.get(v), dtype=np.float64)
        if out.ndim != 1 or len(out) != n:
            raise ValueError(f"Invalid raw vector shape for {v}: {out.shape}")
        return out

    def emit(suffix, values, meta, remember=False, binary=False):
        values = np.asarray(values, dtype=np.float64)
        if values.ndim != 1 or len(values) != n:
            raise ValueError(f"Invalid feature shape for {suffix}: {values.shape}")
        if np.isinf(values).any():
            values = values.copy()
            values[np.isinf(values)] = np.nan
        name = "fe__rel__" + suffix
        if remember:
            history.append((name, values, meta, binary))
        return name, values, meta

# [Anotación · líneas 169–180] Bloque `ratios`: monto por operación de cada terna de `TICKETS` cuando la
#   cantidad es mayor que cero.
    # Monthly amount per recorded operation. Negative numerators are retained:
    # they may represent adjustments; they never become activity indicators.
    for concept, amount, count in TICKETS:
        if not has((amount, count)):
            continue
        caution = ("Denominador estrictamente positivo y ambos campos finitos; 0/0 es NA. "
                   "Montos negativos se conservan como ajustes posibles. No mide número de productos.")
        if concept.startswith("comisiones"):
            caution += " Comisión cobrada no equivale a una operación voluntaria del cliente."
        yield emit("ticket__" + concept, _safe_ratio(get(amount), get(count)),
                   _meta("ratios", (amount, count), f"{amount}/{count} si {count}>0",
                         f"Monto medio por registro mensual: {concept}", "pesos_por_registro", caution))

# [Anotación · líneas 182–227] Bloque `tarjetas`, primera parte: para cada campo de `CARD_FIELDS`, suma Visa +
#   Master, diferencia Visa − Master y cantidad de marcas con dato; para cinco campos, fracción de Visa sobre el
#   total. Para cada marca, tres cocientes: consumo sobre límite de compra, saldo sobre límite de financiación y
#   pagado sobre pago mínimo.
    # Card fields are combined only with the identical field in the other brand.
    for field in CARD_FIELDS:
        cols = ("Visa_" + field, "Master_" + field)
        if not has(cols):
            continue
        a, b = (get(v) for v in cols)
        unit = "conteo" if field.startswith("c") else "unidad_original_del_campo"
        caution = ("Mismo campo en Visa y Master; suma/diferencia requieren ambos observados. "
                   "No convierte monedas, no suma pesos con dólares ni completa una marca faltante con cero. "
                   "Cantidad de marcas observadas mide cobertura, no tenencia.")
        if field == "msaldototal":
            caution += " EDA detectó escala aproximada 0.8525 en Visa_msaldototal respecto de sus componentes; comparabilidad de escala pendiente."
        summed = _strict_sum([a, b])
        yield emit("tarjetas__" + field + "_sum", summed,
                   _meta("tarjetas", cols, "Visa_campo + Master_campo; soporte completo",
                         "Total del mismo concepto entre ambas marcas", unit, caution))
        yield emit("tarjetas__" + field + "_diff_visa_master", _strict_sum([a, -b]),
                   _meta("tarjetas", cols, "Visa_campo - Master_campo; soporte completo",
                         "Diferencia entre marcas en el mismo concepto", unit, caution))
        yield emit("tarjetas__" + field + "_n_marcas_observadas", _n_finite([a, b]),
                   _meta("tarjetas", cols, "I(Visa observado)+I(Master observado)",
                         "Cobertura del campo, de cero a dos marcas", "conteo", caution))
        if field in ("mlimitecompra", "mfinanciacion_limite", "mconsumototal", "cconsumos", "cadelantosefectivo"):
            share = _safe_ratio(a, summed, nonnegative_num=True)
            share[~np.isfinite(b) | (b < 0)] = np.nan
            yield emit("tarjetas__" + field + "_fraccion_visa", share,
                       _meta("tarjetas", cols, "Visa/(Visa+Master), ambos>=0, suma>0",
                             "Participación de Visa en un concepto observado en las dos marcas",
                             "fraccion", caution + " No se define con total cero o componentes negativos."))

    for brand in ("Visa", "Master"):
        # These are accounting ratios, not assertions of arrears or limit breach.
        ratios = (
            ("consumo_sobre_limite_compra", "mconsumototal", "mlimitecompra", "Consumo mensual respecto del límite de compra"),
            ("saldo_no_negativo_sobre_limite_financiacion", "msaldototal", "mfinanciacion_limite", "Saldo no negativo respecto del límite de financiación"),
            ("pagado_sobre_pago_minimo", "mpagado", "mpagominimo", "Pagos registrados respecto del pago mínimo informado"),
        )
        for suffix, numerator, denominator, meaning in ratios:
            cols = (brand + "_" + numerator, brand + "_" + denominator)
            if not has(cols):
                continue
            yield emit("tarjetas__" + brand.lower() + "_" + suffix,
                       _safe_ratio(get(cols[0]), get(cols[1]), nonnegative_num=True),
                       _meta("tarjetas", cols, "numerador>=0 / denominador>0; ambos finitos",
                             meaning, "razon",
                             "Relación contable exploratoria: los cortes pueden diferir. No acredita mora, pago suficiente ni utilización contractual exacta. No se trunca en 1. Visa_msaldototal mostró escala aproximada 0.8525 frente a sus componentes; relación saldo/límite conserva esa incertidumbre."))

# [Anotación · líneas 229–258] Bloque `tarjetas`, segunda parte: para Visa, Master y débito, indicadores de
#   tenencia sin uso, tenencia con uso y uso sin tenencia; y la cantidad de marcas de crédito con cuenta y con
#   transacciones, que se guardan para calcular historia.
    # Separately identify ownership and observed use, without treating missing
    # card details as absence of a card.
    own, use = {}, {}
    for brand, owncol, usecol in (
        ("visa", "ctarjeta_visa", "ctarjeta_visa_transacciones"),
        ("master", "ctarjeta_master", "ctarjeta_master_transacciones"),
        ("debito", "ctarjeta_debito", "ctarjeta_debito_transacciones"),
    ):
        if not has((owncol, usecol)):
            continue
        own[brand], use[brand] = _activity([get(owncol)]), _activity([get(usecol)])
        for suffix, values, formula, meaning in (
            ("tenencia_sin_uso", _and(own[brand], 1 - use[brand]), "tenencia>0 AND transacciones=0", "Tenencia observada sin uso mensual observado"),
            ("tenencia_con_uso", _and(own[brand], use[brand]), "tenencia>0 AND transacciones>0", "Tenencia y uso observados"),
            ("uso_sin_tenencia", _and(1 - own[brand], use[brand]), "tenencia=0 AND transacciones>0", "Incoherencia o diferencia de corte entre tenencia y uso"),
        ):
            yield emit("tarjetas__" + brand + "_" + suffix, values,
                       _meta("tarjetas", (owncol, usecol), formula, meaning, "indicador_0_1",
                             "Lógica de tres valores; una ausencia de información no equivale a cero. Tenencia no significa actividad."))
    if all(b in own for b in ("visa", "master")):
        sources = ("ctarjeta_visa", "ctarjeta_master")
        yield emit("tarjetas__n_marcas_con_cuenta", _strict_sum([own['visa'], own['master']]),
                   _meta("tarjetas", sources, "I(cuentas Visa>0)+I(cuentas Master>0), ambos resueltos",
                         "Cantidad de marcas de crédito con cuenta observada", "conteo",
                         "No cuenta plásticos ni monedas y no mide uso."), remember=True)
        sources = ("ctarjeta_visa_transacciones", "ctarjeta_master_transacciones")
        yield emit("tarjetas__n_marcas_con_uso", _strict_sum([use['visa'], use['master']]),
                   _meta("tarjetas", sources, "I(trx Visa>0)+I(trx Master>0), ambos resueltos",
                         "Cantidad de marcas de crédito con transacciones", "conteo",
                         "No equivale al total de transacciones."), remember=True)

# [Anotación · líneas 260–302] Bloque `funciones`: por dominio, indicador de actividad y cantidad de conteos
#   válidos; con los siete dominios, cantidad de funciones activas (con cobertura completa y como cota
#   inferior), cantidad de indicadores resueltos y fracción activa.
    function_flags = {}
    for domain, cols in FUNCTIONS.items():
        if not has(cols):
            continue
        arrays = [get(c) for c in cols]
        flag = _activity(arrays)
        function_flags[domain] = flag
        caution = ("Un positivo observado implica función activa; cero exige todos los conteos observados en cero. "
                   "Los negativos inesperados no prueban inactividad. Dominios pueden solaparse; no suman operaciones únicas.")
        if domain == "digitales":
            caution += " cmobile_app_trx tiene semántica empírica binaria; se usa sólo su positividad, no su magnitud."
        if domain == "atencion":
            caution += " ccajas_depositos fue constante en mayo; interpretar con la auditoría de fuente."
        yield emit("funcion__" + domain + "_activa", flag,
                   _meta("funciones", cols, "OR de conteos>0; 0 sólo con todos=0; resto NA",
                         "Evidencia de uso mensual del dominio " + domain,
                         "indicador_0_1", caution), remember=True, binary=True)
        yield emit("funcion__" + domain + "_n_campos_validos", _n_finite(arrays, nonnegative=True),
                   _meta("funciones", cols, "sum I(conteo finito y>=0)",
                         "Cobertura de los conteos requeridos para interpretar el dominio", "conteo", caution))
    all_function_sources = tuple(dict.fromkeys(c for cols in FUNCTIONS.values() for c in cols))
    function_total = None
    if len(function_flags) == len(FUNCTIONS):
        flags = list(function_flags.values())
        function_total = _strict_sum(flags)
        resolved = _n_finite(flags)
        lower = np.zeros(n, dtype=np.float64)
        for x in flags:
            lower += x == 1
        caution = ("Siete dominios fijos: haberes, tarjetas, pagos, transferencias, cajeros/extracciones, digitales y atención. "
                   "Miden amplitud de uso; no son operaciones independientes ni productos. No incluyen comisiones, rentabilidad o saldos.")
        for suffix, values, formula, meaning in (
            ("n_activas", function_total, "suma de siete indicadores; todos resueltos", "Amplitud mensual de funciones activas con cobertura completa"),
            ("n_activas_min", lower, "número de dominios con evidencia positiva", "Cota inferior de funciones activas, aunque falte información"),
            ("n_resueltas", resolved, "número de indicadores 0/1 resueltos", "Cobertura para interpretar amplitud de uso"),
        ):
            yield emit("funciones__" + suffix, values,
                       _meta("funciones", all_function_sources, formula, meaning, "conteo", caution),
                       remember=(suffix == "n_activas"))
        yield emit("funciones__fraccion_activas_observadas", _safe_ratio(lower, resolved),
                   _meta("funciones", all_function_sources, "n_activas_min/n_resueltas si n_resueltas>0",
                         "Fracción activa entre funciones resueltas", "fraccion",
                         caution + " Denominador variable: comparar junto con n_resueltas; no sustituye al total completo."))

# [Anotación · líneas 304–358] Bloque `stocks_productos_deuda`: presencia de cada grupo de productos y
#   cantidad de grupos presentes; indicador de productos presentes sin funciones activas; saldo total, cantidad
#   total y saldo medio por tipo de préstamo; y parte positiva y parte negativa del saldo de cuentas.
    product_flags = {}
    for domain, cols in PRODUCTS.items():
        if not has(cols):
            continue
        flag = _activity([get(c) for c in cols]); product_flags[domain] = flag
        yield emit("producto__" + domain + "_presente", flag,
                   _meta("stocks_productos_deuda", cols, "OR de cantidades>0; 0 sólo con todos=0",
                         "Tenencia del grupo de productos " + domain, "indicador_0_1",
                         "Tenencia no equivale a uso, pago de cuotas ni compromiso activo. No utiliza montos como un segundo producto."))
    if len(product_flags) == len(PRODUCTS):
        psources = tuple(dict.fromkeys(c for cols in PRODUCTS.values() for c in cols))
        product_total = _strict_sum(list(product_flags.values()))
        yield emit("productos__n_familias_presentes", product_total,
                   _meta("stocks_productos_deuda", psources, "suma de nueve grupos de tenencia con cobertura completa",
                         "Diversidad de grupos de productos presentes", "conteo",
                         "Nueve grupos definidos en PRODUCTS; no coincide con cproductos ni cuenta monedas o cuentas individuales."), remember=True)
        if function_total is not None:
            yield emit("productos__familias_sin_funciones_observadas",
                       _and(_activity([product_total]), 1 - _activity([function_total])),
                       _meta("stocks_productos_deuda", psources + all_function_sources,
                             "n_familias_presentes>0 AND n_funciones_activas=0",
                             "Productos presentes con las siete funciones observadas inactivas", "indicador_0_1",
                             "No significa cliente sin relación, cuenta cerrada ni deuda como único vínculo."))

    loan_types = ("personales", "prendarios", "hipotecarios")
    loan_counts = tuple("cprestamos_" + t for t in loan_types)
    loan_amounts = tuple("mprestamos_" + t for t in loan_types)
    loan_stock = None
    if has(loan_amounts):
        loan_stock = _strict_sum([get(c) for c in loan_amounts])
        yield emit("deuda__prestamos_saldo_total", loan_stock,
                   _meta("stocks_productos_deuda", loan_amounts, "suma de tres saldos restantes; soporte completo",
                         "Saldo de deuda restante de los préstamos registrados", "pesos",
                         "Es un stock, no una cuota pagada ni mora. No se añade saldo de cuenta negativo o tarjeta para evitar mezclar conceptos."), remember=True)
    if has(loan_counts):
        yield emit("deuda__prestamos_cantidad_total", _strict_sum([get(c) for c in loan_counts]),
                   _meta("stocks_productos_deuda", loan_counts, "suma de cantidades de préstamos vigentes; soporte completo",
                         "Cantidad de préstamos vigentes", "conteo",
                         "No informa cuántas cuotas se pagaron ni si hay atraso."))
    for kind in loan_types:
        cols = ("mprestamos_" + kind, "cprestamos_" + kind)
        if has(cols):
            yield emit("deuda__saldo_medio_" + kind, _safe_ratio(get(cols[0]), get(cols[1])),
                       _meta("stocks_productos_deuda", cols, "saldo restante/cantidad vigente si cantidad>0",
                             "Saldo medio por préstamo de la misma clase", "pesos_por_prestamo",
                             "Promedio de stocks, no ticket de una transacción ni pago mensual."))
    if has(("mcuentas_saldo",)):
        balance = get("mcuentas_saldo"); good = np.isfinite(balance)
        for suffix, vals, meaning in (
            ("saldo_cuentas_positivo", np.where(good, np.maximum(balance, 0), np.nan), "Parte positiva del saldo total de cuentas"),
            ("saldo_cuentas_negativo_magnitud", np.where(good, np.maximum(-balance, 0), np.nan), "Magnitud de la parte negativa del saldo total de cuentas"),
        ):
            yield emit("stock__" + suffix, vals,
                       _meta("stocks_productos_deuda", ("mcuentas_saldo",), "max(saldo,0) o max(-saldo,0); NA preservado",
                             meaning, "pesos", "Saldo es posición, no flujo ni actividad. Saldo negativo no prueba inactividad ni mora."))

# [Anotación · líneas 360–422] Bloque `interacciones`: combinaciones de dos condiciones (haberes con consumo
#   Visa, saldo negativo con extracciones, extracciones con transferencias recibidas, caja de ahorro positiva
#   sin transacciones del trimestre), el producto del saldo por el indicador de extracción y la diferencia entre
#   el percentil mensual de `ctrx_quarter` y el de `mcaja_ahorro`.
    # Directed hypotheses from semantic relations, not an all-pairs explosion.
    # Binary conditions are explicit; no arbitrary ordinal encoding of internet,
    # card status, clusters or the target is involved.
    if has(("cpayroll_trx", "mtarjeta_visa_consumo")):
        cols = ("cpayroll_trx", "mtarjeta_visa_consumo")
        p, v = _activity([get(cols[0])]), _activity([get(cols[1])])
        for suffix, a, b, meaning in (
            ("haberes_visa_ambos_positivos", p, v, "Haberes acreditados y consumo Visa positivo"),
            ("haberes_visa_ambos_cero", 1-p, 1-v, "Ausencia observada de haberes y consumo Visa en la foto"),
            ("haberes_sin_consumo_visa", p, 1-v, "Haberes acreditados con consumo Visa observado en cero"),
            ("consumo_visa_sin_haberes", 1-p, v, "Consumo Visa positivo con haberes observados en cero"),
        ):
            yield emit("interaccion__" + suffix, _and(a, b),
                       _meta("interacciones", cols, "AND de condiciones binarias con tres valores",
                             meaning, "indicador_0_1",
                             "Complementariedad descriptiva del EDA; no interacción predictiva aprobada. Una foto no demuestra apagado histórico ni ausencia de otras funciones."),
                       remember=(suffix == "haberes_visa_ambos_cero"), binary=True)

    if has(("mcuentas_saldo", "cextraccion_autoservicio")):
        cols = ("mcuentas_saldo", "cextraccion_autoservicio")
        balance = get(cols[0]); extr = _activity([get(cols[1])])
        negative = np.where(np.isfinite(balance), (balance < 0).astype(float), np.nan)
        for suffix, b, meaning in (
            ("saldo_negativo_sin_extracciones", 1-extr, "Saldo negativo con extracciones observadas en cero"),
            ("saldo_negativo_con_extracciones", extr, "Saldo negativo con extracciones registradas"),
        ):
            yield emit("interaccion__" + suffix, _and(negative, b),
                       _meta("interacciones", cols, "saldo<0 AND condición de extracciones; tres valores",
                             meaning, "indicador_0_1",
                             "No identifica mora ni causa de baja; el signo del saldo y el uso describen dimensiones distintas."))
        yield emit("interaccion__saldo_por_estado_extraccion", balance * extr,
                   _meta("interacciones", cols, "mcuentas_saldo * I(extracciones>0); requiere ambos observados",
                         "Saldo signed condicionado a extracción observada", "pesos",
                         "Producto dirigido, no cociente por un saldo cercano a cero; su utilidad debe contrastarse frente a efectos principales."))

    if has(("cextraccion_autoservicio", "ctransferencias_recibidas")):
        cols = ("cextraccion_autoservicio", "ctransferencias_recibidas")
        extraction = _activity([get(cols[0])]); received = _activity([get(cols[1])])
        for suffix, a, b, meaning in (
            ("extraccion_transferencia_ambas_positivas", extraction, received, "Extracciones y transferencias recibidas registradas"),
            ("extraccion_transferencia_ambas_cero", 1-extraction, 1-received, "Extracciones y transferencias recibidas observadas en cero"),
            ("extraccion_sin_transferencia_recibida", extraction, 1-received, "Extracciones con transferencias recibidas observadas en cero"),
            ("transferencia_recibida_sin_extraccion", 1-extraction, received, "Transferencias recibidas con extracciones observadas en cero"),
        ):
            yield emit("interaccion__" + suffix, _and(a, b),
                       _meta("interacciones", cols, "AND de condiciones de conteos positivos/cero; tres valores",
                             meaning, "indicador_0_1",
                             "Familia motivada por relación exploratoria entre montos, reformulada con conteos para estados interpretables. No supone que una transferencia financió una extracción ni añade un ratio monetario."))

    if has(("ctrx_quarter", "mcaja_ahorro")):
        cols = ("ctrx_quarter", "mcaja_ahorro")
        quarter = _activity([get(cols[0])]); saving = get(cols[1])
        positive = np.where(np.isfinite(saving), (saving > 0).astype(float), np.nan)
        yield emit("interaccion__caja_positiva_sin_trx_trimestre", _and(positive, 1-quarter),
                   _meta("interacciones", cols, "mcaja_ahorro>0 AND ctrx_quarter=0; tres valores",
                         "Saldo positivo en caja de ahorro con cero transacciones trimestrales registradas", "indicador_0_1",
                         "Combina stock y ventana de 90 días. No interpreta ausencia de transacciones como cuenta vacía ni cierre."))
        rq = np.asarray(panel.rank(get(cols[0])), dtype=np.float64)
        rs = np.asarray(panel.rank(saving), dtype=np.float64)
        yield emit("interaccion__brecha_rank_trx_caja", rq-rs,
                   _meta("interacciones", cols, "rango_percentil_mensual(ctrx_quarter)-rango_percentil_mensual(mcaja_ahorro)",
                         "Desacople relativo entre nivel transaccional trimestral y saldo", "diferencia_de_percentiles",
                         "Rangos sin target, calculados en la foto actual. Empates y población afectan su valor; no es una relación causal ni un ratio monetario."))

# [Anotación · líneas 424–451] Bloque `historia_relaciones`, para los resúmenes guardados en `history`: por
#   cada lag, valor anterior y delta; para los indicadores binarios, cuatro transiciones (pasa a cero, pasa a
#   uno, persiste en uno, persiste en cero).
    # History of deliberately selected summaries: no future snapshots and no
    # zero-fill at panel boundaries. Other raw-column history belongs elsewhere.
    if not config.get("relations_history", True):
        return
    lags = sorted({int(k) for k in config.get("lags", [1, 2, 3, 4, 5]) if int(k) > 0})
    windows = sorted({int(w) for w in config.get("windows", [2, 3, 4, 5, 6]) if int(w) >= 2})
    for name, current, meta, binary in history:
        base = name.removeprefix("fe__rel__")
        hist_caution = (meta['caution'] + " Historia por meses calendario del mismo cliente; una foto ausente no es cero. "
                        "Los lags del resumen se recalculan sobre sus valores pasados; no incorporan información futura.")
        for k in lags:
            past = np.asarray(panel.lag(current, k), dtype=np.float64)
            for operation, values, formula in (
                (f"lag{k}", past, f"{name}(t-{k})"),
                (f"delta{k}", current-past, f"{name}(t)-{name}(t-{k})"),
            ):
                yield emit(base + "__" + operation, values,
                           _meta("historia_relaciones", meta['sources'], formula,
                                 "Historia del resumen: " + meta['interpretation'],
                                 "cambio_indicador_-1_0_1" if binary and operation.startswith("delta") else meta['unit'], hist_caution, k))
            if binary:
                known = np.isfinite(current) & np.isfinite(past)
                for suffix, before, now in (("pasa_a_cero",1,0), ("pasa_a_uno",0,1), ("persiste_uno",1,1), ("persiste_cero",0,0)):
                    vals = np.where(known, ((past == before) & (current == now)).astype(float), np.nan)
                    yield emit(base + f"__{suffix}_lag{k}", vals,
                               _meta("historia_relaciones", meta['sources'], f"I({name}(t-{k})={before} AND {name}(t)={now}), extremos observados",
                                     "Transición entre extremos observados del resumen", "indicador_0_1",
                                     hist_caution + " Para lag>1 no prueba permanencia ni monotonicidad en meses intermedios.", k))
# [Anotación · líneas 452–477] Bloque `historia_relaciones`, ventanas: cantidad de meses observados y, sólo
#   con la ventana completa, media, mínimo y máximo del resumen en los w meses que terminan en t.
        for w in windows:
            # Exact w-month history including t; neither expanding windows nor
            # variable denominators are substituted when history is incomplete.
            observed = np.isfinite(current).astype(np.float64)
            total = np.where(np.isfinite(current), current, 0.0)
            mn = np.where(np.isfinite(current), current, np.inf)
            mx = np.where(np.isfinite(current), current, -np.inf)
            for k in range(1, w):
                prev = np.asarray(panel.lag(current, k), dtype=np.float64)
                ok = np.isfinite(prev); observed += ok
                total += np.where(ok, prev, 0.0)
                mn = np.minimum(mn, np.where(ok, prev, np.inf))
                mx = np.maximum(mx, np.where(ok, prev, -np.inf))
            complete = observed == w
            definitions = (
                ("n_observados", observed, "conteo", "Cantidad de meses con resumen interpretable"),
                ("media", np.where(complete, total/w, np.nan), "fraccion" if binary else meta['unit'], "Media con todos los meses observados"),
                ("min", np.where(complete, mn, np.nan), meta['unit'], "Mínimo con todos los meses observados"),
                ("max", np.where(complete, mx, np.nan), meta['unit'], "Máximo con todos los meses observados"),
            )
            for op, vals, unit, meaning in definitions:
                yield emit(base + f"__{op}_ventana{w}", vals,
                           _meta("historia_relaciones", meta['sources'], f"{op} de {name} en [t-{w-1},t]; ventana fija",
                                 meaning + ": " + meta['interpretation'], unit,
                                 hist_caution + " Media/min/max son NA sin ventana completa; n_observados conserva la cobertura.",
                                 0 if op == "n_observados" else w-1))
```

### 2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/fe_univariadas.py

Transformaciones de una variable por vez, según su tipo en el catálogo: disponibilidad, historia (lag, delta, cambio relativo, transiciones, rachas), estados, percentiles del mes, ventanas y tendencias. C3 usa los bloques `historia_numerica`, `transiciones_numericas`, `recencia` y `categoricas`.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–17] `generate_univariate` recibe el panel, la ficha de una variable del catálogo y la
#   configuración. Lee el vector de la variable, los lags y las ventanas, y define `emit`, que nombra cada
#   resultado `fe__<variable>__<operación>` y le adjunta bloque, fuente, fórmula y meses de historia que
#   requiere.
"""Transformaciones univariadas explícitas según semántica, no según target."""
from __future__ import annotations
import numpy as np
from fe_core import flag, safe_divide, FORBIDDEN

def generate_univariate(panel, spec, config):
    v = spec['variable']
    if v in FORBIDDEN:
        raise ValueError('Una clave o target no puede transformarse como predictor')
    kind = spec['kind']; x = panel.get(v); obs = np.isfinite(x)
    lags = config['lags']; windows = config['windows']; maxk = max(max(lags), max(windows)-1)
    def emit(op, values, block, formula, history=0, fkind='numeric', caution='', unit=None):
        return f'fe__{v}__{op}', np.asarray(values, dtype=float), {
            'block': block, 'sources': [v], 'formula': formula,
            'interpretation': f"{spec.get('history_mode','unknown')}: {op}",
            'min_history': history, 'unit': unit or spec.get('unit','--'),
            'caution': (spec.get('caution','') + ' ' + caution).strip(), 'feature_kind': fkind}

# [Anotación · líneas 19–24] Bloque `disponibilidad`: indicador de valor faltante y, por cada lag, si el dato
#   aparece (antes NA, ahora observado) o desaparece respecto de la fila de k meses atrás.
    yield emit('missing', ~obs, 'disponibilidad', '1 si el valor no es finito, 0 si observado', unit='indicador')
    # Diferenciar transición de disponibilidad de falta de fila.
    for k in lags:
        prev = panel.lag(x, k); po = np.isfinite(prev); row = panel.row_present(k)
        yield emit(f'aparece_dato_l{k}', flag(obs & ~po, row), 'disponibilidad', f'fila t-{k} presente con NA, valor t observado', k, unit='indicador')
        yield emit(f'desaparece_dato_l{k}', flag(~obs & po, row), 'disponibilidad', f'fila t-{k} presente y observada, valor t NA', k, unit='indicador')

# [Anotación · líneas 26–40] Variables de tipo fecha relativa (bloque `fechas`): marca los valores con valor
#   absoluto mayor a 365.000 días, los excluye y calcula por lag el valor anterior, la diferencia descontando
#   los días transcurridos entre fotos y un indicador de cambio de evento.
    if kind == 'relative_date':
        # Sólo vista derivada: RAW no se cambia. Valores >1000 años son extremos,
        # no fechas válidas para pendientes. Incluye vencimientos año 9999.
        bound = config.get('relative_date_abs_limit', 365000)
        extreme = obs & (np.abs(x) > bound)
        yield emit('fecha_extrema', flag(extreme, obs), 'fechas', f'abs(x) > {bound} días', unit='indicador', caution='Alerta de calidad, no causa de baja.')
        clean = np.where(extreme, np.nan, x)
        for k in lags:
            prev = panel.lag(clean, k)
            elapsed = panel.days - panel.lag(panel.days, k)
            adj = clean - prev - elapsed
            yield emit(f'lag{k}_limpio', prev, 'fechas', f'x(t-{k}) excluyendo extremos', k)
            yield emit(f'delta_evento_l{k}', adj, 'fechas', f'x(t)-x(t-{k})-[días foto(t)-días foto(t-{k})]', k, caution='Convención foto−evento; cero equivale a evento fijo, no a ausencia de actividad.')
            yield emit(f'cambio_evento_l{k}', flag(np.abs(adj) > 0.5, np.isfinite(adj)), 'fechas', f'abs(delta_evento_l{k}) > 0.5 días', k, unit='indicador')
        return

# [Anotación · líneas 42–49] Variables de tipo reloj (edad y antigüedad, bloque `relojes`): lag, delta y, para
#   `cliente_antiguedad`, delta menos los k meses transcurridos.
    if kind == 'clock':
        for k in lags:
            prev = panel.lag(x, k)
            yield emit(f'lag{k}', prev, 'relojes', f'x(t-{k})', k)
            yield emit(f'delta{k}', x-prev, 'relojes', f'x(t)-x(t-{k})', k, caution='Cambio de edad/antigüedad; no se interpreta como uso o apagado.')
            if v == 'cliente_antiguedad':
                yield emit(f'delta_ajustado{k}', x-prev-k, 'relojes', f'x(t)-x(t-{k})-{k} meses', k)
        return

# [Anotación · líneas 51–70] Variables categóricas (bloque `categoricas`): código del mes anterior, indicador
#   de cambio, longitud de la racha del código actual y, por ventana, cantidad de códigos observados, proporción
#   igual al código actual, cantidad de cambios y pares de meses observados.
    if kind == 'category':
        for k in lags:
            prev = panel.lag(x, k); ok = obs & np.isfinite(prev)
            yield emit(f'estado_lag{k}', prev, 'categoricas', f'código nominal observado en t-{k}', k, 'category', unit='código nominal')
            yield emit(f'cambio_l{k}', flag(x != prev, ok), 'categoricas', f'x(t) != x(t-{k}) con ambos observados', k, unit='indicador')
        streak = np.ones(panel.n); continuing = obs.copy()
        for k in range(1, maxk+1):
            prev = panel.lag(x, k); continuing &= np.isfinite(prev) & (prev == x)
            streak += continuing
        yield emit('racha_estado_observada', np.where(obs, streak, np.nan), 'categoricas', f'longitud consecutiva hacia atrás del código actual, máximo {maxk+1}', maxk, unit='meses', caution='Racha observada, censurada al inicio del archivo, hueco o NA; no duración total conocida.')
        for w in windows:
            a = np.vstack([panel.lag(x,k) for k in range(w)]); seen = np.isfinite(a); n = seen.sum(axis=0)
            same = ((a == x) & seen).sum(axis=0)
            pairs = seen[:-1] & seen[1:]
            changes = ((a[:-1] != a[1:]) & pairs).sum(axis=0)
            yield emit(f'nobs_w{w}', n, 'categoricas', f'número de códigos observados en {w} meses calendario', w-1, unit='meses')
            yield emit(f'prop_estado_actual_w{w}', safe_divide(same, n, obs), 'categoricas', f'fracción observada igual al código actual en {w} meses', w-1, unit='proporción')
            yield emit(f'cambios_w{w}', np.where(pairs.sum(axis=0)>0, changes, np.nan), 'categoricas', f'cambios entre pares adyacentes observados de {w} meses', w-1, unit='cambios')
            yield emit(f'pares_observados_w{w}', pairs.sum(axis=0), 'categoricas', f'pares mensuales con ambos códigos observados en ventana {w}', w-1, unit='pares')
        return

# [Anotación · líneas 72–79] Variables numéricas: indicadores de cero, negativo y positivo (bloque
#   `estado_numerico`), `sign(x)·log(1+|x|)` (bloque `transformaciones`) y percentil dentro del mes, sobre todos
#   los valores y sobre los distintos de cero (bloque `ranks`).
    if kind != 'numeric':
        raise ValueError(f'Tipo no soportado {kind}: {v}')
    for op, cond in [('cero',x == 0),('negativo',x < 0),('positivo',x > 0)]:
        yield emit(op, flag(cond,obs), 'estado_numerico', op+' con valor observado', unit='indicador', caution='Estado matemático; no equivale automáticamente a actividad voluntaria.')
    yield emit('signed_log1p', np.sign(x)*np.log1p(np.abs(x)), 'transformaciones', 'sign(x)*log(1+abs(x))', unit='escala transformada', caution='Transformación monótona; puede ser redundante para árboles.')
    rank = panel.rank(x)
    yield emit('rank_mes', rank, 'ranks', 'percentil con empates medios de observados en la foto completa', unit='percentil', caution='Requiere disponer del lote mensual de scoring completo; no utiliza target.')
    yield emit('rank_no_cero_mes', panel.rank(np.where(x!=0,x,np.nan)), 'ranks', 'percentil entre valores observados distintos de cero del mismo mes', unit='percentil')

# [Anotación · líneas 81–91] Por cada lag k: valor de k meses atrás, delta y delta simétrico (delta dividido
#   por la suma de valores absolutos, 0 si ambos son cero) en el bloque `historia_numerica`; delta del percentil
#   en `ranks`; y cambio relativo (delta sobre el valor anterior) para flujos no negativos, flujos móviles y
#   conteos.
    for k in lags:
        prev = panel.lag(x,k); delta = x-prev
        yield emit(f'lag{k}', prev, 'historia_numerica', f'x(t-{k}) exacto por calendario', k)
        yield emit(f'delta{k}', delta, 'historia_numerica', f'x(t)-x(t-{k})', k)
        den = np.abs(x)+np.abs(prev)
        sym = safe_divide(delta,den)
        sym = np.where(obs & np.isfinite(prev) & (den==0),0,sym)
        yield emit(f'delta_simetrico{k}', sym, 'historia_numerica', f'(x(t)-x(t-{k}))/(abs(x(t))+abs(x(t-{k}))); 0 si ambos cero', k, unit='cambio simétrico [-1,1]', caution='No es variación porcentual convencional.')
        yield emit(f'delta_rank{k}', rank-panel.lag(rank,k), 'ranks', f'rank_mes(t)-rank_mes(t-{k})', k, unit='diferencia percentiles', caution='Puede cambiar porque cambia la población de referencia.')
        if spec.get('history_mode') in {'nonnegative_flow','rolling_flow','count_stock'}:
            yield emit(f'cambio_relativo{k}', safe_divide(delta,prev,(prev>0)&(x>=0)), 'historia_numerica', f'(x(t)-x(t-{k}))/x(t-{k}), previo>0 y actual>=0', k, unit='proporción')

# [Anotación · líneas 93–105] Bloque `transiciones_numericas`: seis indicadores de t−1 a t (cero a cero, no
#   cero a cero, cero a no cero, pasó a negativo, negativo persistente, salió de negativo). Si la historia
#   configurada llega a 2 meses, agrega la segunda diferencia `aceleracion2`.
    prev = panel.lag(x,1); ok = obs & np.isfinite(prev)
    transitions = {
        'cero_a_cero': (prev==0)&(x==0),
        'no_cero_a_cero': (prev!=0)&(x==0),
        'cero_a_no_cero': (prev==0)&(x!=0),
        'paso_a_negativo': (prev>=0)&(x<0),
        'negativo_persistente': (prev<0)&(x<0),
        'salio_de_negativo': (prev<0)&(x>=0),
    }
    for op, val in transitions.items():
        yield emit(op, flag(val,ok), 'transiciones_numericas', f'{op}: t-1→t, ambos observados', 1, unit='indicador', caution='No-cero incluye negativos; no se etiqueta automáticamente como uso.')
    if maxk >= 2:
        yield emit('aceleracion2', x-2*prev+panel.lag(x,2), 'historia_numerica', 'x(t)-2*x(t-1)+x(t-2)', 2)

# [Anotación · líneas 107–116] Bloque `recencia`: meses desde el último valor observado distinto de cero y
#   longitud de las rachas de ceros y de no ceros hacia atrás, hasta el máximo de historia configurado.
    recent = np.full(panel.n,np.nan); zero_run = np.zeros(panel.n); nonzero_run = np.zeros(panel.n)
    zcont = obs.copy(); nzcont = obs.copy()
    for k in range(maxk+1):
        a = panel.lag(x,k); ao = np.isfinite(a)
        recent = np.where(np.isnan(recent)&ao&(a!=0),k,recent)
        zcont &= ao & (a==0); nzcont &= ao & (a!=0)
        zero_run += zcont; nonzero_run += nzcont
    yield emit('meses_desde_no_cero_observado', recent, 'recencia', f'mínimo k con x(t-k) observado y distinto de cero, 0≤k≤{maxk}', maxk, unit='meses', caution='Recencia del último registro observado; un hueco no demuestra ausencia de eventos.')
    yield emit('racha_cero_observada', np.where(obs,zero_run,np.nan), 'recencia', f'ceros consecutivos desde t hacia atrás, máximo {maxk+1}; corta en NA/hueco', maxk, unit='meses')
    yield emit('racha_no_cero_observada', np.where(obs,nonzero_run,np.nan), 'recencia', f'no-ceros consecutivos desde t hacia atrás, máximo {maxk+1}; corta en NA/hueco', maxk, unit='meses')

# [Anotación · líneas 118–151] Por cada ventana w: bloque `ventanas` (observados, media, desvío, mínimo,
#   máximo, amplitud, proporción de ceros y de negativos, subidas y bajadas, y suma con ventana completa para
#   flujos) y bloque `tendencias` (pendiente de mínimos cuadrados contra el mes e indicadores de serie
#   creciente, decreciente o alternante con ventana completa). Estos dos bloques no figuran en
#   `generated_blocks` del plan, por lo que no se guardan en el banco.
    for w in windows:
        # Orden: pasado → presente. Cada posición es un mes exacto.
        a = np.vstack([panel.lag(x,k) for k in range(w-1,-1,-1)])
        seen = np.isfinite(a); n = seen.sum(axis=0); complete = n==w
        total = np.where(seen,a,0).sum(axis=0); mean = safe_divide(total,n)
        variance = safe_divide(np.where(seen,(a-mean)**2,0).sum(axis=0),n)
        mn = np.where(seen,a,np.inf).min(axis=0); mx = np.where(seen,a,-np.inf).max(axis=0)
        mn[n==0]=np.nan; mx[n==0]=np.nan
        pairs = seen[1:]&seen[:-1]; d=np.diff(a,axis=0); npairs=pairs.sum(axis=0)
        up=((d>0)&pairs).sum(axis=0); down=((d<0)&pairs).sum(axis=0)
        # No usar nansum como suma económica: con faltantes la suma queda NA.
        vals = {
            'nobs':(n,'número de valores observados','meses'),
            'media_obs':(mean,'media de observados; leer junto a nobs',spec.get('unit','--')),
            'std_obs':(np.where(n>=2,np.sqrt(variance),np.nan),'desvío poblacional entre observados, n>=2',spec.get('unit','--')),
            'min_obs':(mn,'mínimo observado',spec.get('unit','--')),
            'max_obs':(mx,'máximo observado',spec.get('unit','--')),
            'amplitud_obs':(np.where(n>=2,mx-mn,np.nan),'máximo-mínimo, n>=2',spec.get('unit','--')),
            'prop_cero_obs':(safe_divide(((a==0)&seen).sum(axis=0),n),'ceros/valores observados','proporción'),
            'prop_negativo_obs':(safe_divide(((a<0)&seen).sum(axis=0),n),'negativos/valores observados','proporción'),
            'pares_obs':(npairs,'pares de meses adyacentes con ambos valores observados','pares'),
            'subidas_obs':(np.where(npairs>0,up,np.nan),'pares observados con delta>0','pares'),
            'bajadas_obs':(np.where(npairs>0,down,np.nan),'pares observados con delta<0','pares'),
        }
        for op,(val,formula,unit) in vals.items():
            yield emit(f'{op}_w{w}',val,'ventanas',formula+f' en {w} meses calendario',w-1,unit=unit,caution='Ventana incluye t; los resúmenes parciales llevan nobs y pares_obs.')
        if spec.get('history_mode') in {'nonnegative_flow','signed_flow'}:
            yield emit(f'suma_completa_w{w}',np.where(complete,total,np.nan),'ventanas',f'suma de flujos mensuales sólo con {w} valores observados',w-1)
        tt=np.arange(w,dtype=float); tt-=tt.mean()
        slope=(np.where(seen,a,0)*tt[:,None]).sum(axis=0)/(tt@tt)
        yield emit(f'pendiente_completa_w{w}',np.where(complete,slope,np.nan),'tendencias',f'pendiente OLS vs mes; requiere los {w} meses observados',w-1,unit=spec.get('unit','--')+'/mes',caution='Ventanas móviles de RAW se superponen; pendiente no prueba causa ni salida abrupta.')
        yield emit(f'decreciente_completo_w{w}',flag((down>0)&(up==0),complete),'tendencias',f'ningún aumento y alguna disminución en {w} meses completos',w-1,unit='indicador')
        yield emit(f'creciente_completo_w{w}',flag((up>0)&(down==0),complete),'tendencias',f'ninguna disminución y algún aumento en {w} meses completos',w-1,unit='indicador')
        yield emit(f'alternancia_completa_w{w}',flag((up>0)&(down>0),complete),'tendencias',f'al menos una subida y una bajada en {w} meses completos',w-1,unit='indicador')
```

### 2_variables/experimentos_20261006_m1_fe_masiva/fe_amplia/generar_fe.py

Generador del banco de variables: lee el Parquet, arma el panel, recorre las variables producidas por los módulos `fe_*.py` y las guarda en partes Parquet con un catálogo y un manifiesto. Lo llaman `run_screening.py`, `run_q0.py`, `run_b1.py` y SUPERFINAL.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–22] Importa pandas, numpy y pyarrow y los generadores de los otros módulos de la
#   carpeta. `sha256_file` calcula el SHA-256 de un archivo leyéndolo de a 8 MB.
#!/usr/bin/env python3
"""FE amplia para DMEyF: salidas columnares por partes, memoria acotada."""
from __future__ import annotations
import argparse, csv, hashlib, json, platform, time
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from fe_core import Panel, KEYS, FORBIDDEN, generate_coverage
from fe_semantica import load_catalog
from fe_univariadas import generate_univariate
from fe_relaciones import generate_relations

ROOT = Path(__file__).resolve().parent

def sha256_file(path):
    h = hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

# [Anotación · líneas 24–36] `validate_config` exige que `lags` sea una lista de enteros ≥ 1 y `windows` de
#   enteros ≥ 2, sin repetidos; que `storage_dtype` sea float32 o float64; que `features_per_part` esté entre 1
#   y 128; y que `rank_reference` sea `complete_contemporary_month`.
def validate_config(config):
    for key, minimum in [('lags',1),('windows',2)]:
        values=config.get(key)
        if not isinstance(values,list) or not values or any(type(x)!=int or x<minimum for x in values):
            raise ValueError(f'{key} debe ser una lista no vacía de enteros >= {minimum}')
        if len(set(values))!=len(values):
            raise ValueError(f'{key}: valores repetidos')
    if config.get('storage_dtype','float64') not in {'float32','float64'}:
        raise ValueError('storage_dtype inválido')
    if not 1 <= config.get('features_per_part',32) <= 128:
        raise ValueError('features_per_part debe estar entre 1 y128')
    if config.get('rank_reference','complete_contemporary_month')!='complete_contemporary_month':
        raise ValueError('Este generador implementa ranks del lote contemporáneo completo')

# [Anotación · líneas 38–50] `iter_features` encadena tres fuentes de variables: cobertura del panel,
#   transformaciones univariadas de cada variable del catálogo y relaciones entre variables. Deja pasar sólo las
#   de los bloques pedidos y se detiene si una variable declara como fuente una clave o la clase.
def iter_features(panel, specs, config, blocks=None):
    blocks = set(blocks or [])
    streams=[generate_coverage(panel,config)]
    streams.extend(generate_univariate(panel,spec,config) for spec in specs)
    if config.get('relations',True):
        streams.append(generate_relations(panel,config))
    for stream in streams:
        for name, values, meta in stream:
            if not blocks or meta['block'] in blocks:
                meta.setdefault('feature_kind','numeric')
                if FORBIDDEN.intersection(meta.get('sources',[])):
                    raise ValueError(f'Feature usa fuente prohibida: {name}')
                yield name,values,meta

# [Anotación · líneas 52–67] `generate` valida la configuración, exige que la carpeta de salida esté vacía y
#   crea `manifest.json` en estado `running` con la configuración, el SHA-256 de la entrada, las versiones de
#   las bibliotecas, la hora de inicio y el hash de cada `.py` de la carpeta.
def generate(input_path, output_path, config, blocks=None, months=None, max_clients=None, variables=None):
    validate_config(config)
    output=Path(output_path)
    # Nunca mezclar una ejecución anterior ni sobrescribir resultados.
    if output.exists() and any(output.iterdir()):
        raise ValueError('La carpeta de salida debe ser nueva o estar vacía')
    output.mkdir(parents=True,exist_ok=True); (output/'features').mkdir(exist_ok=True)
    start=time.time(); manifest={'status':'running','config':config,'input_sha256':sha256_file(input_path),
        'blocks_requested':blocks or 'all','output_months_requested':months or 'all',
        'versions':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'pyarrow':pa.__version__},
        'target_used_for_features':False,'rank_population':'complete_contemporary_month' if not max_clients else 'diagnostic_client_subset',
        'diagnostic_max_clients':max_clients,'started_at_utc':pd.Timestamp.now(tz='UTC').isoformat()}
    manifest['code_sha256']={p.name:sha256_file(p) for p in ROOT.glob('*.py')}
    def save_manifest():
        tmp=output/'manifest.tmp'; tmp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2));tmp.replace(output/'manifest.json')
    save_manifest()
# [Anotación · líneas 68–96] Lee el Parquet completo, arma el `Panel` y verifica que las columnas sean
#   exactamente las 152 del catálogo. Calcula la máscara de filas de los meses de salida (la historia se calcula
#   con todos los meses del archivo) y guarda `claves.parquet`, `raw.parquet` (variables originales sin la
#   clase) y `etiquetas.parquet` (claves y `clase_ternaria`).
    try:
        df=pd.read_parquet(input_path)
        input_rows=len(df)
        if max_clients:
            # Determinista y mantiene toda la historia de cada ID escogido.
            ids=np.sort(df.numero_de_cliente.unique())[:max_clients]
            df=df[df.numero_de_cliente.isin(ids)].copy()
        panel=Panel(df,config);del df
        specs=load_catalog()
        actual=set(panel.columns)-FORBIDDEN
        expected={s['variable'] for s in specs}
        if actual != expected:
            raise ValueError(f'Esquema difiere de152predictores: faltan={sorted(expected-actual)}, extras={sorted(actual-expected)}')
        if variables:
            unknown=set(variables)-expected
            if unknown:raise ValueError(f'Variables desconocidas:{sorted(unknown)}')
            specs=[s for s in specs if s['variable'] in variables]
            # Selección univariada explícita no genera relaciones de otras fuentes.
            config={**config,'relations':False};manifest['config']=config
        row_mask=np.isin(panel.month,months) if months else np.ones(panel.n,bool)
        if not row_mask.any():raise ValueError('No hay filas para los meses de salida')
        if months and not set(months).issubset(set(panel.month)):
            raise ValueError('Algún mes de salida no está en la base')
        keys=panel.df.loc[row_mask,KEYS].reset_index(drop=True)
        keys.to_parquet(output/'claves.parquet',index=False)
        raw=[c for c in panel.df if c not in {'clase_ternaria','clase_binaria'}]
        panel.df.loc[row_mask,raw].to_parquet(output/'raw.parquet',index=False)
        if 'clase_ternaria' in panel.df:
            panel.df.loc[row_mask,KEYS+['clase_ternaria']].to_parquet(output/'etiquetas.parquet',index=False)
# [Anotación · líneas 97–110] `flush` escribe las variables acumuladas en el buffer como
#   `features/parte_NNNN.parquet` (compresión zstd, con las claves) y anota en el catálogo en qué archivo quedó
#   cada una.
        catalog=[];buffer={};buffer_rows=[];seen_names=set();parts=[];part_no=0
        dtype=np.dtype(config.get('storage_dtype','float64'))
        def flush():
            nonlocal part_no
            if not buffer:return
            part_no+=1; rel=f'features/parte_{part_no:04d}.parquet'
            arrays={k:pa.array(keys[k].to_numpy()) for k in KEYS}
            arrays.update({k:pa.array(v,from_pandas=True) for k,v in buffer.items()})
            table=pa.table(arrays)
            tmp=output/(rel+'.tmp');pq.write_table(table,tmp,compression='zstd',compression_level=3,row_group_size=65536)
            tmp.replace(output/rel)
            for idx in buffer_rows:catalog[idx]['file']=rel
            parts.append({'file':rel,'n_features':len(buffer),'rows':len(keys),'bytes':(output/rel).stat().st_size})
            buffer.clear();buffer_rows.clear()
# [Anotación · líneas 111–131] Recorre las variables generadas: rechaza nombres repetidos, longitudes
#   distintas a la del panel e infinitos; registra en el catálogo filas, valores observados, fracción faltante,
#   mínimo y máximo, y el estado `generated` o `all_missing_in_output`; convierte al tipo de almacenamiento y
#   descarga el buffer cada `features_per_part` variables.
        for name,values,meta in iter_features(panel,specs,config,blocks):
            if name in seen_names:raise ValueError(f'Feature duplicada:{name}')
            seen_names.add(name);values=np.asarray(values,dtype=float)
            if values.shape!=(panel.n,):raise ValueError(f'Longitud incorrecta:{name}')
            arr=values[row_mask]
            if np.isinf(arr).any():raise ValueError(f'Inf en {name}')
            finite=np.isfinite(arr);nobs=int(finite.sum())
            entry={'feature':name,**meta,'sources':json.dumps(meta.get('sources',[]),ensure_ascii=False),
                'n_rows':len(arr),'n_observed':nobs,'missing_fraction':1-nobs/len(arr),
                'minimum':float(arr[finite].min()) if nobs else None,'maximum':float(arr[finite].max()) if nobs else None,
                'status':'generated' if nobs else 'all_missing_in_output','file':''}
            # Se registra toda definición; omitir materializar un vector todo NA ahorra espacio.
            catalog.append(entry)
            if nobs:
                arr=arr.astype(dtype,copy=False)
                if np.isinf(arr).any():raise ValueError(f'Overflow al guardar {name}; usar float64')
                buffer[name]=arr;buffer_rows.append(len(catalog)-1)
            if len(buffer)>=config.get('features_per_part',32):flush()
            if len(catalog)%500==0:
                print(f'{len(catalog)} definiciones; {part_no} partes; {time.time()-start:.1f}s',flush=True)
        flush()
# [Anotación · líneas 132–149] Escribe `catalogo_features.csv`, `resumen_bloques.csv` y
#   `variables_transformadas.csv` y cierra el manifiesto con estado `completed`, filas, meses, cantidades de
#   variables, partes y segundos transcurridos. Si ocurre una excepción, deja el manifiesto en estado `failed`
#   con el mensaje.
        if not catalog:raise ValueError('La selección no produjo features; revisar nombres de bloque')
        cat=pd.DataFrame(catalog);cat.to_csv(output/'catalogo_features.csv',index=False)
        summary=cat.groupby('block').agg(definidas=('feature','size'),materializadas=('status',lambda x:int(x.eq('generated').sum()))).reset_index()
        summary.to_csv(output/'resumen_bloques.csv',index=False)
        pd.DataFrame(specs).to_csv(output/'variables_transformadas.csv',index=False)
        manifest.update(status='completed',input_rows=input_rows,panel_rows=panel.n,output_rows=len(keys),
            input_months=sorted(map(int,np.unique(panel.month))),output_months=sorted(map(int,keys.foto_mes.unique())),
            source_predictors=len(expected),source_predictors_transformed=len(specs),
            features_defined=len(catalog),features_materialized=int(cat.status.eq('generated').sum()),
            all_missing_features=int(cat.status.eq('all_missing_in_output').sum()),parts=parts,
            output_bytes=sum(p['bytes'] for p in parts),elapsed_seconds=round(time.time()-start,3),
            coverage_note='min_history expresa amplitud retrospectiva solicitada; ventanas parciales se acompañan de nobs. No implica disponibilidad en todos los meses de train.',
            warnings=['No es una selección predictiva ni una prueba de ganancia.','No incorporar etiquetas ni claves como predictores.','Las features de tipo category requieren tratamiento nominal al entrenar.','Ranks calculados con población contemporánea, nunca con futuros BAJA+2.'])
        save_manifest();print(json.dumps({k:manifest[k] for k in ['status','panel_rows','output_rows','features_defined','features_materialized','elapsed_seconds']},ensure_ascii=False),flush=True)
        return manifest
    except Exception as exc:
        manifest.update(status='failed',error=f'{type(exc).__name__}: {exc}',elapsed_seconds=time.time()-start)
        save_manifest();raise

# [Anotación · líneas 151–164] Interfaz de línea de comandos: `--input`, `--output`, `--config` (por defecto
#   `config_amplia.json`), `--blocks`, `--months`, `--max-clients` y `--variables`. Los scripts del camino de la
#   entrega no usan esta interfaz: llaman a `generate` con `config_screening.json`.
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--config',type=Path,default=ROOT/'config_amplia.json')
    p.add_argument('--blocks',nargs='+',help='Bloques exactos; omitir para todos')
    p.add_argument('--months',nargs='+',type=int,help='Sólo filtra salida; historia y ranks usan todas las fotos disponibles')
    p.add_argument('--max-clients',type=int,help='Diagnóstico por subconjunto, no ejecución de producción')
    p.add_argument('--variables',nargs='+',help='Prueba univariada selectiva; desactiva relaciones')
    args=p.parse_args()
    if args.max_clients is not None and args.max_clients<1:p.error('--max-clients debe ser positivo')
    cfg=json.loads(args.config.read_text())
    generate(args.input,args.output,cfg,args.blocks,args.months,args.max_clients,args.variables)

if __name__=='__main__':main()
```

### 1_dataset/preparar_competencia.py

Paso 1. Con DuckDB lee el CSV crudo, arma `clase_ternaria` según la presencia del cliente uno y dos meses después y guarda `competencia_01.parquet` y una tabla de filas por mes y clase.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–6] Importa `pathlib`, `argparse`, `urllib.request` y `duckdb`, y define la URL del CSV
#   crudo de la competencia.
from pathlib import Path
import argparse
import urllib.request
import duckdb

URL = "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"

# [Anotación · líneas 8–20] Lee el argumento `--workdir` (por defecto `_cluster_work`), crea la carpeta y
#   define tres rutas dentro de ella: el CSV crudo, el Parquet de salida y `target_counts.csv`. Si el CSV crudo
#   no está, lo descarga de la URL.
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workdir", type=Path, default=Path("_cluster_work"))
    args = p.parse_args()
    args.workdir.mkdir(parents=True, exist_ok=True)

    raw = args.workdir / "competencia_01_crudo.csv"
    out = args.workdir / "competencia_01.parquet"
    counts = args.workdir / "target_counts.csv"

    if not raw.exists():
        print("Descargando dataset crudo...")
        urllib.request.urlretrieve(URL, raw)

# [Anotación · líneas 22–47] Abre DuckDB y empieza la consulta: lee el CSV entero con `numero_de_cliente` como
#   entero de 64 bits, arma la lista de meses y la de clientes, hace el producto de ambas y marca en `mes_0`,
#   con 1 o 0, si el cliente tiene fila en ese mes.
    con = duckdb.connect()
    print("Construyendo target...")
    q = f"""
    COPY (
      WITH raw AS (
        SELECT * REPLACE (CAST(numero_de_cliente AS BIGINT) AS numero_de_cliente)
        FROM read_csv('{raw.as_posix()}', sample_size=-1)
      ),
      periodos AS (
        SELECT DISTINCT foto_mes FROM raw
      ),
      clientes AS (
        SELECT DISTINCT numero_de_cliente FROM raw
      ),
      todo AS (
        SELECT numero_de_cliente, foto_mes
        FROM clientes CROSS JOIN periodos
      ),
      presencia AS (
        SELECT
          t.numero_de_cliente,
          t.foto_mes,
          CASE WHEN r.numero_de_cliente IS NULL THEN 0 ELSE 1 END AS mes_0
        FROM todo t
        LEFT JOIN raw r USING (numero_de_cliente, foto_mes)
      ),
# [Anotación · líneas 48–70] Con `lead` por cliente calcula si está presente uno y dos meses después (`mes_1`,
#   `mes_2`) y asigna `clase_ternaria` a las filas existentes: CONTINUA si falta el mes siguiente pero vuelve al
#   subsiguiente, BAJA+1 si falta el mes siguiente, BAJA+2 si está el mes siguiente y falta el subsiguiente,
#   CONTINUA si está en los dos, y NULL cuando no hay meses posteriores para decidir.
      ventana AS (
        SELECT
          *,
          lead(mes_0, 1) OVER (PARTITION BY numero_de_cliente ORDER BY foto_mes) AS mes_1,
          lead(mes_0, 2) OVER (PARTITION BY numero_de_cliente ORDER BY foto_mes) AS mes_2
        FROM presencia
      ),
      etiquetas AS (
        SELECT
          numero_de_cliente,
          foto_mes,
          CASE
            -- Intermitente: falta el mes siguiente pero vuelve al subsiguiente.
            -- Se conserva como CONTINUA para reproducir la base canónica usada en el EDA.
            WHEN mes_1 = 0 AND mes_2 = 1 THEN 'CONTINUA'
            WHEN mes_1 = 0 THEN 'BAJA+1'
            WHEN mes_1 = 1 AND mes_2 = 0 THEN 'BAJA+2'
            WHEN mes_1 = 1 AND mes_2 = 1 THEN 'CONTINUA'
            ELSE NULL
          END AS clase_ternaria
        FROM ventana
        WHERE mes_0 = 1
      )
# [Anotación · líneas 71–77] Une las etiquetas con las filas originales por cliente y mes, ordena por cliente
#   y mes y escribe el resultado en `competencia_01.parquet` con compresión ZSTD.
      SELECT r.*, e.clase_ternaria
      FROM raw r
      JOIN etiquetas e USING (numero_de_cliente, foto_mes)
      ORDER BY numero_de_cliente, foto_mes
    ) TO '{out.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """
    con.execute(q)

# [Anotación · líneas 79–96] Escribe en `target_counts.csv` la cantidad de filas por mes y clase, imprime esa
#   misma tabla y la ruta del Parquet. Las dos últimas líneas llaman a `main()` cuando el archivo se ejecuta
#   como script.
    con.execute(f"""
      COPY (
        SELECT foto_mes, clase_ternaria, count(*) AS n
        FROM read_parquet('{out.as_posix()}')
        GROUP BY foto_mes, clase_ternaria
        ORDER BY foto_mes, clase_ternaria
      ) TO '{counts.as_posix()}' (HEADER, DELIMITER ',')
    """)

    print(con.execute(f"""
      SELECT foto_mes, clase_ternaria, count(*) n
      FROM read_parquet('{out.as_posix()}')
      GROUP BY 1,2 ORDER BY 1,2
    """).df().to_string(index=False))
    print("Listo:", out)

if __name__ == "__main__":
    main()
```

### 4_modelo/experimentos_20261007_post_c3/05_superfinal100/super_common.py

Utilidades compartidas por SUPERFINAL y CLAW2: constantes de meses y semillas, rutas fijas, parámetros base, curva de ganancia y elección de meseta, carga de folds, definición de los 10 conjuntos de variables y exportación del CSV.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] Importaciones y `_gcs` (copia a Cloud Storage que se omite con el texto de
#   reemplazo del bucket).
from __future__ import annotations

import contextlib
import gc
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterable

import numpy as np
import pandas as pd
import yaml

def _gcs(cmd, check=True, **kw):
    """Respaldo opcional a Cloud Storage. Se omite cuando el bucket es el placeholder de publicacion."""
    if any("REEMPLAZAR_CON_BUCKET_PROPIO" in str(a) or "BUCKET_PRIVADO_NO_PUBLICADO" in str(a) for a in cmd):
        return None
    return subprocess.run(cmd, check=check, **kw)


# [Anotación · líneas 26–46] Constantes compartidas: SHA-256 del dataset, las 20 semillas y sus subconjuntos
#   de 5 y 3, meses (entrenar 202103–202104 y evaluar 202106; búsqueda con 202103 y 202105; final 202103–202106;
#   predicción 202108), filas esperadas por mes, grilla de cortes 8.000–15.000 de a 500, ganancia y costo, 6
#   hilos, las tres cantidades de préstamos que algunos brazos quitan, los 7 bloques de C3 y 6 bloques
#   adicionales.
RUN = "c1superfinal100"
DATA_SHA = "59231e670a1342ad6f689ad7edc7ece047fc9f7115c6d7845e6c72fa3bbd95bb"
SEEDS20 = [17,101,202,303,404,505,606,707,808,909,1001,1102,1203,1304,1405,1506,1607,1708,1809,1910]
SEEDS5 = SEEDS20[:5]
SEEDS3 = SEEDS20[:3]
TRAIN_EVAL = [202103, 202104]
EVAL_MONTH = 202106
TUNE_TRAIN = [202103]
TUNE_EVAL = 202105
FINAL_TRAIN = [202103,202104,202105,202106]
SCORE_MONTH = 202108
EXPECTED_ROWS = {202103:162900,202104:163284,202105:163768,202106:164114,202107:164348,202108:164647}
N_GRID = list(range(8000,15001,500))
GAIN_HIT = 1_072_500
COST = 27_500
THREADS = 6
DROP_LOANS = ["cprestamos_personales","cprestamos_prendarios","cprestamos_hipotecarios"]
C3_BLOCKS = ["historia_numerica","transiciones_numericas","recencia","categoricas","historia_relaciones","tarjetas","ratios"]
EXTRA_BLOCKS = ["disponibilidad","cobertura_panel","ranks","estado_numerico","stocks_productos_deuda","funciones"]
SUPER_BLOCKS = C3_BLOCKS + EXTRA_BLOCKS
REMOTE = "gs://REEMPLAZAR_CON_BUCKET_PROPIO/corridas/" + RUN


# [Anotación · líneas 49–109] Utilidades (`require`, hash, huella, JSON), `paths` con las carpetas fijas
#   dentro de `home`, `add_fe_path` para importar el generador del paso 2 y `base_params`, que lee
#   `lightgbm.base` de `config.yaml` y agrega 6 hilos y `deterministic=True`.
def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def load_json(path: Path):
    require(path.is_file(), f"Falta {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def paths(home: Path) -> dict[str, Path]:
    stage = home / "c1m1femasiva03_s3/paquete_c1/experimentos_20261006_m1_fe_masiva"
    return {
        "stage": stage,
        "pkg": stage.parent,
        "fe": stage / "fe_amplia",
        "s3": home / "c1m1femasiva03_s3/resultados_s3",
        "bank_orig": home / "c1m1femasiva03_s3/resultados_s1/fe_bank_dev",
        "data": home / "c1m1femasiva03/datos/competencia_01.parquet",
        "q0": home / "c1q0ccajas06",
        "b1": home / "c1b1rotas01",
        "out": home / RUN,
    }


def add_fe_path(p: dict[str, Path]) -> None:
    s = str(p["fe"])
    if s not in sys.path:
        sys.path.insert(0, s)


def base_params(p: dict[str, Path]) -> dict:
    params = dict(
        yaml.safe_load((p["pkg"] / "vendor/comun/config.yaml").read_text())["lightgbm"]["base"]
    )
    params.update(num_threads=THREADS, deterministic=True)
    return params


# [Anotación · líneas 112–145] `gain_curve` valida puntajes en [0, 1] y calcula la ganancia en cada corte de
#   la grilla (orden por puntaje descendente, empates por cliente). `robust_choice` elige la terna de cortes
#   consecutivos de mayor ganancia promedio (desempata por mayor mínimo y menor N) y devuelve su corte central
#   (`n_robusto`), el promedio (`ganancia_robusta`) y el corte de ganancia máxima.
def gain_curve(ids: np.ndarray, y: np.ndarray, scores: np.ndarray) -> dict[int, int]:
    ids = np.asarray(ids, dtype=np.int64)
    y = np.asarray(y, dtype=np.int8)
    scores = np.asarray(scores, dtype=np.float64)
    require(ids.shape == y.shape == scores.shape, "IDs/y/scores desalineados")
    require(np.isfinite(scores).all(), "Scores no finitos")
    require(((scores >= 0) & (scores <= 1)).all(), "Scores fuera de [0,1]")
    order = np.lexsort((ids, -scores))
    out = {}
    for n in N_GRID:
        z = y[order[:n]]
        hits = int(z.sum())
        out[n] = int(hits * GAIN_HIT - (n - hits) * COST)
    return out


def robust_choice(curve: dict[int, int]) -> dict:
    candidates = []
    for n in N_GRID[1:-1]:
        ns = [n-500,n,n+500]
        vals = [int(curve[k]) for k in ns]
        candidates.append((float(np.mean(vals)), int(min(vals)), -n, n, vals))
    require(candidates, "Sin candidatos robustos")
    avg, mn, _, n, vals = max(candidates)
    peak_n = max(N_GRID, key=lambda k:(curve[k],-k))
    return {
        "n_robusto": int(n),
        "ganancia_robusta": float(avg),
        "ganancia_min_meseta": int(mn),
        "meseta_n": [int(n-500),int(n),int(n+500)],
        "meseta_gain": [int(v) for v in vals],
        "n_peak": int(peak_n),
        "gain_peak": int(curve[peak_n]),
    }


# [Anotación · líneas 148–184] `summarize_scores` calcula la curva de cada semilla y la del promedio de
#   semillas con su meseta elegida. `paired_at_plateau` calcula, por semilla, la diferencia de ganancia promedio
#   entre un brazo y el control en los cortes de una meseta, y resume media, mediana, desvío y semillas a favor,
#   empatadas y en contra.
def summarize_scores(
    ids: np.ndarray,
    y: np.ndarray,
    score_by_seed: dict[int,np.ndarray],
    seeds: list[int],
) -> tuple[dict, dict[int,dict[int,int]], np.ndarray]:
    require(set(score_by_seed) == set(seeds), "Seeds de scores incompletas")
    seed_curves = {s: gain_curve(ids,y,score_by_seed[s]) for s in seeds}
    mat = np.vstack([score_by_seed[s] for s in seeds])
    ens = mat.mean(axis=0,dtype=np.float64)
    curve = gain_curve(ids,y,ens)
    return robust_choice(curve), seed_curves, ens


def paired_at_plateau(
    arm_curves: dict[int,dict[int,int]],
    control_curves: dict[int,dict[int,int]],
    seeds: list[int],
    ns: list[int],
) -> dict:
    d = np.asarray(
        [
            np.mean([arm_curves[s][n] - control_curves[s][n] for n in ns])
            for s in seeds
        ],
        dtype=float,
    )
    return {
        "mean": float(d.mean()),
        "median": float(np.median(d)),
        "sd": float(d.std(ddof=1)) if len(d) > 1 else 0.0,
        "positive_fraction": float((d>0).mean()),
        "wins": int((d>0).sum()),
        "ties": int((d==0).sum()),
        "losses": int((d<0).sum()),
        "deltas": d.tolist(),
    }


# [Anotación · líneas 187–201] `export_csv` ordena por puntaje descendente (empates por cliente), toma los
#   primeros n clientes, los ordena de menor a mayor y los escribe uno por línea sin encabezado; verifica
#   cantidad de líneas, ausencia de repetidos y formato numérico, y devuelve nombre, filas y SHA-256.
def export_csv(path: Path, ids: np.ndarray, scores: np.ndarray, n: int) -> dict:
    ids = np.asarray(ids,dtype=np.int64)
    scores = np.asarray(scores,dtype=np.float64)
    require(len(ids)==len(scores) and len(np.unique(ids))==len(ids), "IDs inválidos")
    require(np.isfinite(scores).all(), "Scores no finitos")
    order = np.lexsort((ids,-scores))
    chosen = np.sort(ids[order[:n]])
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp = path.with_name(path.name+".tmp")
    np.savetxt(tmp,chosen,fmt="%d")
    lines = tmp.read_text().splitlines()
    require(len(lines)==n and len(set(lines))==n, "CSV con cantidad/duplicados inválidos")
    require(all(re.fullmatch(r"[1-9][0-9]*",x) for x in lines), "CSV formato inválido")
    tmp.replace(path)
    return {"file":path.name,"rows":n,"sha256":digest(path),"header":False}


# [Anotación · líneas 204–219] `preflight_base` verifica rutas, SHA-256 del dataset, que la confirmación de C3
#   esté promovida con 20 semillas, que el esquema tenga 2.062 variables con las derivadas a partir de la
#   posición 152 y que el banco original esté completo.
def preflight_base(home: Path) -> dict:
    p = paths(home)
    for key in ["stage","pkg","fe","s3","bank_orig","data","q0"]:
        require(p[key].exists(), f"Falta {key}: {p[key]}")
    require(digest(p["data"]) == DATA_SHA, "Dataset distinto")
    s3_summary = load_json(p["s3"] / "confirmacion_c3.json")
    require(s3_summary.get("n_seeds")==20 and s3_summary.get("promote_to_tuning") is True,
            "C3/S3 no está cerrado")
    schema_doc = load_json(p["s3"] / "C3_HIST_MAS_TARJETAS/features.json")
    schema = schema_doc["features"]
    derived = schema_doc["derived"]
    require(len(schema)==2062 and schema[152:]==derived, "Schema C3 inesperado")
    bm = load_json(p["bank_orig"] / "manifest.json")
    require(bm.get("status")=="completed" and bm.get("input_sha256")==DATA_SHA,
            "Banco original incompatible")
    return {"paths":p,"schema":schema,"derived":derived,"s3_summary":s3_summary}


# [Anotación · líneas 222–257] `quality_dataset_and_bank` devuelve el dataset y el banco según el brazo de
#   calidad: el original, la copia de Q0 o la copia de un brazo de B1. `ensure_quality_bank` genera, cuando el
#   brazo no es el original, un banco de 202105 y 202106 con los 13 bloques sobre la copia corregida.
def quality_dataset_and_bank(ctx: dict, quality_arm: str) -> tuple[Path,Path|None]:
    p = ctx["paths"]
    if quality_arm == "C3_ORIG":
        return p["data"], p["bank_orig"]
    if quality_arm == "Q0_CCAJAS":
        return p["q0"] / "datos/competencia_01_q0_ccajas_202105_na.parquet", None
    require(quality_arm.startswith("B1_"), f"Quality arm desconocido: {quality_arm}")
    return p["b1"] / "arms" / quality_arm / "dataset.parquet", None


def ensure_quality_bank(ctx: dict, quality_arm: str) -> tuple[Path,Path]:
    p = ctx["paths"]
    data, existing = quality_dataset_and_bank(ctx,quality_arm)
    require(data.is_file(), f"Falta dataset quality {quality_arm}: {data}")
    if existing is not None:
        return data, existing
    bank = p["out"] / "stage0_quality_bank"
    config = load_json(p["stage"] / "config_screening.json")
    if (bank/"manifest.json").is_file():
        m = load_json(bank/"manifest.json")
        require(m.get("status")=="completed", "Quality bank incompleto")
        require(m.get("input_sha256")==digest(data), "Quality bank usa otra entrada")
        require(m.get("output_months")==[202105,202106], "Quality bank meses inesperados")
        require(m.get("blocks_requested")==SUPER_BLOCKS, "Quality bank bloques inesperados")
        return data,bank
    if bank.exists() and any(bank.iterdir()):
        q = p["out"] / ("stage0_quality_bank_incomplete_"+str(int(pd.Timestamp.utcnow().timestamp())))
        bank.rename(q)
    add_fe_path(p)
    from generar_fe import generate
    print("STAGE0: generar banco quality mayo-junio",flush=True)
    generate(data,bank,config,blocks=SUPER_BLOCKS,months=[202105,202106])
    m = load_json(bank/"manifest.json")
    require(m.get("status")=="completed" and m.get("input_sha256")==digest(data),
            "Quality bank no cerró")
    return data,bank


# [Anotación · líneas 260–312] `feature_arms` define los 10 conjuntos de variables de la etapa 1: C3; C3 sin
#   las tres cantidades de préstamos ni sus derivadas (NOPREST); y cada uno con el agregado de indicadores de
#   disponibilidad y cobertura (OBS), percentiles del mes (RANK) o indicadores de estado, productos y funciones
#   del mes (STATE), más dos combinaciones.
def catalog(p: dict[str,Path]) -> pd.DataFrame:
    c = pd.read_csv(p["bank_orig"]/"catalogo_features.csv").set_index("feature",verify_integrity=True)
    return c


def feature_arms(ctx: dict) -> dict[str,list[str]]:
    p = ctx["paths"]
    cat = catalog(p)
    c3 = list(ctx["schema"])
    raw = c3[:152]

    def generated(blocks: Iterable[str], current_only: bool=False) -> list[str]:
        z = cat[cat.block.isin(list(blocks)) & cat.status.eq("generated")].copy()
        if current_only:
            mh = pd.to_numeric(z.min_history,errors="coerce").fillna(0)
            z = z[mh.eq(0)]
        return z.index.tolist()

    obs = generated(["disponibilidad","cobertura_panel"],current_only=False)
    ranks = generated(["ranks"],current_only=True)
    state = generated(["estado_numerico","stocks_productos_deuda","funciones"],current_only=True)

    def unique(xs: Iterable[str]) -> list[str]:
        return list(dict.fromkeys(xs))

    def no_loans(xs: list[str]) -> list[str]:
        out=[]
        for f in xs:
            if f in DROP_LOANS:
                continue
            if f in cat.index:
                src = str(cat.loc[f,"sources"])
                if any(v in src for v in DROP_LOANS):
                    continue
            out.append(f)
        return out

    arms = {
        "C3": unique(c3),
        "NOPREST": no_loans(unique(c3)),
        "C3_OBS": unique(c3+obs),
        "NOPREST_OBS": no_loans(unique(c3+obs)),
        "C3_RANK": unique(c3+ranks),
        "NOPREST_RANK": no_loans(unique(c3+ranks)),
        "C3_STATE": unique(c3+state),
        "NOPREST_STATE": no_loans(unique(c3+state)),
        "NOPREST_OBS_STATE": no_loans(unique(c3+obs+state)),
        "NOPREST_RANK_OBS": no_loans(unique(c3+ranks+obs)),
    }
    for name,feats in arms.items():
        require(len(feats)==len(set(feats)), f"Features duplicadas {name}")
        require(all(f in raw or f in cat.index for f in feats), f"Feature desconocida {name}")
    return arms


# [Anotación · líneas 315–356] `load_fold` carga las variables pedidas para los meses de entrenamiento desde
#   el banco original y para el mes de evaluación desde el banco indicado, con la clase binaria BAJA+2, y
#   verifica alineación de claves, orden de columnas y filas esperadas.
def split_derived(features: list[str], ctx: dict) -> list[str]:
    raw=set(ctx["schema"][:152])
    return [f for f in features if f not in raw]


def load_fold(
    ctx: dict,
    features: list[str],
    train_months: list[int],
    eval_month: int,
    eval_bank: Path,
) -> dict:
    p=ctx["paths"]
    add_fe_path(p)
    from cargar_bloques import cargar_bloques
    derived=split_derived(features,ctx)

    trdf,_=cargar_bloques(
        p["bank_orig"],meses=train_months,incluir_raw=True,features=derived
    )
    evdf,_=cargar_bloques(
        eval_bank,meses=[eval_month],incluir_raw=True,features=derived
    )
    labels=pd.read_parquet(p["bank_orig"]/"etiquetas.parquet")
    trlab=labels[labels.foto_mes.isin(train_months)].reset_index(drop=True)
    evlab=labels[labels.foto_mes.eq(eval_month)].reset_index(drop=True)
    require(trdf[["numero_de_cliente","foto_mes"]].equals(trlab[["numero_de_cliente","foto_mes"]]),
            "Train keys desalineadas")
    require(evdf[["numero_de_cliente","foto_mes"]].equals(evlab[["numero_de_cliente","foto_mes"]]),
            "Eval keys desalineadas")
    require(list(trdf[features].columns)==features and list(evdf[features].columns)==features,
            "Orden features distinto")
    xtr=trdf[features]
    xev=evdf[features]
    ytr=trlab.clase_ternaria.eq("BAJA+2").to_numpy(np.int8)
    yev=evlab.clase_ternaria.eq("BAJA+2").to_numpy(np.int8)
    ids=evdf.numero_de_cliente.to_numpy(np.int64)
    months=trdf.foto_mes.to_numpy(np.int64)
    require(len(ids)==EXPECTED_ROWS[eval_month], f"Filas eval inesperadas {eval_month}")
    del trdf,evdf,labels,trlab,evlab
    gc.collect()
    return {"x_train":xtr,"x_eval":xev,"y_train":ytr,"y_eval":yev,"ids":ids,"train_months":months}


# [Anotación · líneas 359–376] `policy_weights` convierte un peso por mes en un peso por fila y descarta las
#   filas con peso 0. `score_checkpoint` lee un `.npz` de puntajes si existe y valida identidad, etiqueta,
#   semilla y claves.
def policy_weights(months: np.ndarray, weights_by_month: dict[int,float]) -> tuple[np.ndarray,np.ndarray]:
    w=np.asarray([float(weights_by_month.get(int(m),0.0)) for m in months],dtype=np.float64)
    keep=w>0
    require(keep.any(), "Política dejó train vacío")
    return keep,w[keep]


def score_checkpoint(path: Path, identity: str, label: str, seed: int, ids: np.ndarray, y: np.ndarray) -> np.ndarray|None:
    if not path.is_file():
        return None
    with np.load(path,allow_pickle=False) as z:
        require(str(z["identity"].item())==identity, f"Checkpoint otra identity {path}")
        require(str(z["label"].item())==label, f"Checkpoint otro label {path}")
        require(int(z["seed"].item())==seed, f"Checkpoint otra seed {path}")
        require(np.array_equal(z["ids"],ids) and np.array_equal(z["y"],y), f"Checkpoint keys {path}")
        sc=np.asarray(z["scores"],dtype=np.float64).copy()
    require(sc.shape==ids.shape and np.isfinite(sc).all(), f"Scores inválidos {path}")
    return sc


# [Anotación · líneas 379–464] `train_seeds` entrena una semilla tras otra sobre un único `lgb.Dataset`
#   compartido, con reutilización de puntajes guardados. En el camino de la entrega esta función queda
#   reemplazada por `train_seeds_per_seed` de `superfinal100_v2.py`.
def train_seeds(
    data: dict,
    features: list[str],
    params: dict,
    rounds: int,
    seeds: list[int],
    weights_by_month: dict[int,float],
    out_dir: Path,
    identity: str,
    label: str,
    save_models: bool=False,
    backup_prefix: str|None=None,
    reuse_scores: dict[int,np.ndarray]|None=None,
) -> dict[int,np.ndarray]:
    import lightgbm as lgb
    out_dir.mkdir(parents=True,exist_ok=True)
    reuse_scores=reuse_scores or {}

    keep,w=policy_weights(data["train_months"],weights_by_month)
    if bool(np.all(keep)):
        xtr=data["x_train"]
    else:
        xtr=data["x_train"].loc[keep].reset_index(drop=True)
    ytr=data["y_train"][keep]
    xev=data["x_eval"]
    ids=data["ids"];yev=data["y_eval"]

    ds=lgb.Dataset(
        xtr,label=ytr,weight=w,feature_name=features,free_raw_data=True,
        params={"max_bin": int(params.get("max_bin",255))}
    )
    ds.construct()
    del xtr,ytr,w
    gc.collect()

    scores_by_seed={}
    for i,seed in enumerate(seeds,1):
        cp=out_dir/f"seed_{seed}.npz"
        mp=out_dir/f"modelo_{seed}.txt"
        existing=score_checkpoint(cp,identity,label,seed,ids,yev)
        if existing is not None:
            scores_by_seed[seed]=existing
            print(f"REUSAR {label} {i}/{len(seeds)} seed={seed}",flush=True)
            continue

        if seed in reuse_scores:
            scores=np.asarray(reuse_scores[seed],dtype=np.float64)
            require(scores.shape==ids.shape and np.isfinite(scores).all(),"Reuse scores inválidos")
            with cp.with_suffix(".tmp").open("wb") as fh:
                np.savez_compressed(
                    fh,identity=np.array(identity),label=np.array(label),seed=np.array(seed),
                    ids=ids,y=yev,scores=scores,reused=np.array(True)
                )
            cp.with_suffix(".tmp").replace(cp)
            scores_by_seed[seed]=scores
            print(f"COPIAR SCORE {label} {i}/{len(seeds)} seed={seed}",flush=True)
            continue

        print(f"ENTRENAR {label} {i}/{len(seeds)} seed={seed}; features={len(features)}; rounds={rounds}",flush=True)
        model=lgb.train(dict(params,seed=int(seed)),ds,num_boost_round=int(rounds))
        scores=np.asarray(model.predict(xev,num_threads=THREADS),dtype=np.float64)
        require(scores.shape==ids.shape and np.isfinite(scores).all(),"Scores nuevos inválidos")
        require(((scores>=0)&(scores<=1)).all(),"Scores fuera de rango")
        model_sha=""
        if save_models:
            tmpm=mp.with_suffix(".tmp")
            model.save_model(str(tmpm))
            tmpm.replace(mp)
            model_sha=digest(mp)
        with cp.with_suffix(".tmp").open("wb") as fh:
            np.savez_compressed(
                fh,identity=np.array(identity),label=np.array(label),seed=np.array(seed),
                ids=ids,y=yev,scores=scores,reused=np.array(False),
                model_sha256=np.array(model_sha)
            )
        cp.with_suffix(".tmp").replace(cp)
        if backup_prefix:
            files=[str(cp)]+([str(mp)] if save_models else [])
            _gcs(["gcloud","storage","cp",*files,backup_prefix+"/"],check=True)
        scores_by_seed[seed]=scores
        del model
        gc.collect()

    del ds,xev
    gc.collect()
    return scores_by_seed


# [Anotación · líneas 467–493] `load_s3_control` lee los puntajes de C3 del paso 2 para las semillas pedidas.
#   `validate_catalog_compat` verifica que un banco nuevo defina las variables igual que el original (bloque,
#   fuentes, fórmula, tipo e historia mínima).
def load_s3_control(ctx: dict, seeds: list[int]) -> tuple[np.ndarray,np.ndarray,dict[int,np.ndarray]]:
    p=ctx["paths"]
    ids0=None;y0=None;out={}
    for seed in seeds:
        cp=p["s3"]/"C3_HIST_MAS_TARJETAS"/f"seed_{seed}.npz"
        require(cp.is_file(),f"Falta S3 seed={seed}")
        with np.load(cp,allow_pickle=False) as z:
            ids=np.asarray(z["ids"],dtype=np.int64)
            y=np.asarray(z["y"],dtype=np.int8)
            sc=np.asarray(z["scores"],dtype=np.float64)
        if ids0 is None:
            ids0=ids.copy();y0=y.copy()
        else:
            require(np.array_equal(ids0,ids) and np.array_equal(y0,y),"S3 desalineado")
        out[seed]=sc.copy()
    return ids0,y0,out


def validate_catalog_compat(original_bank: Path, new_bank: Path, features: list[str]) -> None:
    a=pd.read_csv(original_bank/"catalogo_features.csv").set_index("feature",verify_integrity=True)
    b=pd.read_csv(new_bank/"catalogo_features.csv").set_index("feature",verify_integrity=True)
    derived=[f for f in features if f in a.index]
    require(set(derived)<=set(b.index),"Banco nuevo no contiene features")
    for col in ["block","sources","formula","feature_kind","min_history"]:
        x=a.loc[derived,col].fillna("").astype(str).tolist()
        y=b.loc[derived,col].fillna("").astype(str).tolist()
        require(x==y,f"Definición de features cambió: {col}")
```

### 4_modelo/experimentos_20261007_post_c3/05_superfinal100/auditar_superfinal100_v2.py

Auditoría de SUPERFINAL sin entrenar: reconstruye el promedio desde los 20 puntajes guardados, lo compara con el CSV y escribe `AUDITORIA_FINAL.json`, que `run_cluster_aware.py` exige antes de empezar.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–37] Importaciones, corrida y semillas. `expected_ids` devuelve los n clientes de mayor
#   puntaje ordenados de menor a mayor; `read_csv_ids` lee un CSV de una columna y valida formato y ausencia de
#   repetidos.
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re

import numpy as np

HERE = Path(__file__).resolve().parent
import sys
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import super_common as C

RUN = "c1superfinal100v2"
SEEDS = [17,101,202,303,404,505,606,707,808,909,1001,1102,1203,1304,1405,1506,1607,1708,1809,1910]


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def expected_ids(ids: np.ndarray, scores: np.ndarray, n: int) -> np.ndarray:
    order = np.lexsort((ids, -scores))
    return np.sort(ids[order[:n]])


def read_csv_ids(path: Path) -> np.ndarray:
    lines = path.read_text(encoding="utf-8").splitlines()
    require(lines and all(re.fullmatch(r"[1-9][0-9]*", x) for x in lines),
            f"CSV formato inválido: {path}")
    arr = np.asarray([int(x) for x in lines], dtype=np.int64)
    require(len(np.unique(arr)) == len(arr), f"CSV duplicados: {path}")
    return arr


# [Anotación · líneas 40–66] `main` lee los resultados de las etapas 4 y 5. Si la etapa 5 se detuvo sin
#   promoción, verifica que no exista ningún CSV y escribe `AUDITORIA_FINAL.json` con estado `AUDIT_STOP_OK`.
def main() -> None:
    parser = argparse.ArgumentParser(description="Auditor 0-fits SUPERFINAL100 v2")
    parser.add_argument("--home", type=Path, default=Path.home())
    args = parser.parse_args()
    home = args.home.resolve()
    root = home / RUN
    stage4 = C.load_json(root / "stage4_confirm20/RESULT.json")
    stage5 = C.load_json(root / "stage5_final/RESULT.json")

    if stage5.get("status") == "stopped_no_promotion":
        require(stage4.get("promote_to_august") is False,
                "Stage5 dice stop pero Stage4 promovió")
        delivery = root / "stage5_final/delivery"
        csvs = list(delivery.glob("*.csv")) if delivery.exists() else []
        require(not csvs, "Hay CSV aunque no hubo promoción")
        audit = {
            "status": "AUDIT_STOP_OK",
            "run": RUN,
            "stage4_identity": stage4["identity"],
            "promote_to_august": False,
            "submit_generated": False,
            "promotion_rule_v2": stage4.get("promotion_rule_v2"),
        }
        C.write_json(root / "AUDITORIA_FINAL.json", audit)
        print("AUDIT_STOP_OK")
        print("No hubo promoción; no existe submit final.")
        return

# [Anotación · líneas 68–74] Exige estado `ready_not_submitted`, promoción con al menos 14 semillas a favor,
#   el mismo N que la etapa 4 y que N esté en la grilla 8.000–15.000 de a 500.
    require(stage5.get("status") == "ready_not_submitted", "Stage5 no está listo")
    require(stage4.get("promote_to_august") is True, "Stage5 listo sin promoción")
    require(stage4.get("paired", {}).get("wins", 0) >= 14, "Promoción con menos de 14 wins")
    identity = stage5["identity"]
    n = int(stage5["n"])
    require(n == int(stage4["n_final"]), "N final distinto de Stage4")
    require(8000 <= n <= 15000 and n % 500 == 0, "N fuera de grilla")

# [Anotación · líneas 76–113] Para cada semilla verifica el par modelo y `.npz` (identidad, semilla, hash del
#   modelo), que los puntajes sean finitos y estén en [0, 1] y que los 164.647 clientes coincidan; arma la
#   matriz de 20 × 164.647 y la promedia.
    model_dir = root / "stage5_final/models"
    ids0 = None
    score_rows = []
    model_rows = []
    for seed in SEEDS:
        cp = model_dir / f"seed_{seed}.npz"
        model_path = model_dir / f"modelo_{seed}.txt"
        require(cp.is_file() and model_path.is_file(), f"Falta par seed={seed}")
        with np.load(cp, allow_pickle=False) as z:
            require(str(z["identity"].item()) == identity, f"Identity seed={seed}")
            require(int(z["seed"].item()) == seed, f"Seed incorrecta {seed}")
            ids = np.asarray(z["ids"], dtype=np.int64)
            scores = np.asarray(z["scores"], dtype=np.float64)
            require(str(z["model_sha256"].item()) == C.digest(model_path),
                    f"Hash modelo/checkpoint seed={seed}")
        require(scores.shape == ids.shape and np.isfinite(scores).all(),
                f"Scores inválidos seed={seed}")
        require(((scores >= 0) & (scores <= 1)).all(),
                f"Scores fuera de rango seed={seed}")
        if ids0 is None:
            ids0 = ids.copy()
            require(len(ids0) == 164647, "Cantidad agosto inesperada")
            require(len(np.unique(ids0)) == len(ids0), "IDs duplicados")
        else:
            require(np.array_equal(ids0, ids), f"IDs distintos seed={seed}")
        score_rows.append(scores.copy())
        model_rows.append({
            "seed": seed,
            "checkpoint_sha256": C.digest(cp),
            "model_sha256": C.digest(model_path),
            "n_scores": len(scores),
            "score_min": float(scores.min()),
            "score_max": float(scores.max()),
        })

    matrix = np.vstack(score_rows)
    require(matrix.shape == (20, 164647), "Matriz de scores incompleta")
    ensemble = matrix.mean(axis=0, dtype=np.float64)

# [Anotación · líneas 115–142] Verifica manifiesto y `LISTO.json`, que haya un solo CSV con el nombre y el
#   SHA-256 registrados, que sus clientes sean exactamente los N de mayor promedio, el mensaje de envío y el
#   resultado del canary.
    delivery = root / "stage5_final/delivery"
    manifest = C.load_json(delivery / "MANIFEST.json")
    listo = C.load_json(root / "stage5_final/LISTO.json")
    require(manifest["identity"] == identity and listo["identity"] == identity,
            "Manifest/LISTO de otra identity")
    require(int(manifest["n"]) == n and int(listo["n"]) == n,
            "N de manifiesto distinto")
    require(manifest.get("status") == "ready_not_submitted", "Manifest no listo")
    require(manifest.get("execution") == "dataframe_64GiB_dataset_per_seed_gc",
            "Modo de ejecución inesperado")

    csvs = sorted(delivery.glob("*.csv"))
    require(len(csvs) == 1, f"Debe existir un solo CSV; hay {len(csvs)}")
    csv_path = csvs[0]
    require(csv_path.name == manifest["file"]["file"], "Nombre CSV distinto")
    require(C.digest(csv_path) == manifest["file"]["sha256"], "SHA CSV distinto")
    got = read_csv_ids(csv_path)
    require(len(got) == n, f"CSV tiene {len(got)} filas; esperaba {n}")
    exp = expected_ids(ids0, ensemble, n)
    require(np.array_equal(got, exp), "CSV no corresponde al ensemble top-N")

    message = (delivery / "mensaje_zulip.txt").read_text(encoding="utf-8").strip()
    require(message == manifest["submit_message"], "Mensaje Zulip distinto")
    require(message.startswith("submit C1SF2"), "Prefijo submit inesperado")

    canary = C.load_json(root / "canary_s3_exact/RESULT.json")
    require(canary.get("status") == "passed" and canary.get("max_abs") == 0.0,
            "Canary S3 no exacto")

# [Anotación · líneas 144–169] Escribe `AUDITORIA_FINAL.json` con estado `AUDIT_OK`, la identidad, el CSV, su
#   hash y los hashes por semilla, e imprime el resumen.
    audit = {
        "status": "AUDIT_OK",
        "run": RUN,
        "identity": identity,
        "n_models": 20,
        "n_august": 164647,
        "n_final": n,
        "csv": csv_path.name,
        "csv_sha256": C.digest(csv_path),
        "submit_message": message,
        "canary_s3_max_abs": canary["max_abs"],
        "stage4_wins": stage4["paired"]["wins"],
        "models": model_rows,
    }
    C.write_json(root / "AUDITORIA_FINAL.json", audit)
    print("AUDIT_OK")
    print(f"identity={identity}")
    print("modelos=20")
    print("agosto=164647")
    print(f"N={n}")
    print(f"CSV={csv_path}")
    print(message)


if __name__ == "__main__":
    main()
```

### 4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100_v2_safe.py

Punto de entrada de SUPERFINAL: carga la versión 2, reemplaza su etapa 5 por la variante que libera memoria y llama a `main` (`--home $HOME --all`).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–10] Importa `superfinal100_v2`, reemplaza su `stage5_per_seed` por
#   `stage5_per_seed_safe` y llama a `main`.
#!/usr/bin/env python3
from __future__ import annotations

import superfinal100_v2 as V2
from stage5_v2_safe import stage5_per_seed_safe

V2.stage5_per_seed = stage5_per_seed_safe

if __name__ == "__main__":
    V2.main()
```

### 4_modelo/experimentos_20261007_post_c3/05_superfinal100/stage5_v2_safe.py

Etapa 5 de SUPERFINAL: genera el banco final de variables (202103–202106 y 202108), entrena 20 modelos con los cuatro meses y exporta el CSV de SUPERFINAL. El modelo final de la entrega reutiliza ese banco.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–21] Importaciones, módulos C, V1 y V2 y `_gcs`.
#!/usr/bin/env python3
from __future__ import annotations

import gc
from pathlib import Path
import subprocess
import time

import numpy as np
import pandas as pd

import super_common as C
import run_superfinal100 as V1
import superfinal100_v2 as V2

def _gcs(cmd, check=True, **kw):
    """Respaldo opcional a Cloud Storage. Se omite cuando el bucket es el placeholder de publicacion."""
    if any("REEMPLAZAR_CON_BUCKET_PROPIO" in str(a) or "BUCKET_PRIVADO_NO_PUBLICADO" in str(a) for a in cmd):
        return None
    return subprocess.run(cmd, check=check, **kw)



# [Anotación · líneas 24–50] `stage5_per_seed_safe` devuelve el resultado guardado si existe. Si la etapa 4 no
#   promovió, escribe un resultado `stopped_no_promotion` y termina sin entrenar.
def stage5_per_seed_safe(
    ctx: dict,
    s0: dict,
    s1: dict,
    s2: dict,
    s3: dict,
    s4: dict,
) -> dict:
    import lightgbm as lgb

    out = V1.stage_path(ctx, 5, "final")
    result_path = out / "RESULT.json"
    if result_path.is_file():
        return C.load_json(result_path)
    if not s4["promote_to_august"]:
        result = {
            "status": "stopped_no_promotion",
            "stage4_identity": s4["identity"],
            "no_submit": True,
        }
        C.write_json(result_path, result)
        _gcs(
            ["gcloud", "storage", "cp", str(result_path), V2.REMOTE + "/stage5_RESULT.json"],
            check=True,
        )
        print("STAGE5 NO EJECUTADO: no promovió bajo regla v2.", flush=True)
        return result

# [Anotación · líneas 52–82] Verifica la memoria total (56 GiB) y que la disponible alcance la estimación
#   `(2·filas de entrenamiento + filas de 202108)·variables·8 bytes + 8 GiB`; lee la lista de variables
#   ganadora, prepara el banco final y vuelve a verificar la memoria.
    total_gib, available_gib = V2.meminfo_gib()
    V2.require(
        total_gib >= V2.MIN_TOTAL_GIB,
        f"VM insuficiente: MemTotal={total_gib:.1f}GiB < {V2.MIN_TOTAL_GIB}",
    )
    features = C.load_json(Path(s1["winner_features_file"]))["features"]
    n_train = sum(C.EXPECTED_ROWS[m] for m in C.FINAL_TRAIN)
    n_score = C.EXPECTED_ROWS[C.SCORE_MONTH]
    estimated_gib = (
        ((2 * n_train + n_score) * len(features) * 8) / V2.GIB
        + V2.RESERVE_GIB
    )
    V2.require(
        available_gib >= estimated_gib,
        f"RAM disponible insuficiente: {available_gib:.1f}GiB < "
        f"estimado {estimated_gib:.1f}GiB",
    )
    print(
        f"RAM_GUARD_OK total={total_gib:.1f} available={available_gib:.1f} "
        f"estimated={estimated_gib:.1f}",
        flush=True,
    )

    bank = V1.prepare_final_bank(ctx, s0, features)
    gc.collect()
    _, available_after_bank = V2.meminfo_gib()
    V2.require(
        available_after_bank >= estimated_gib,
        f"RAM insuficiente después del banco: {available_after_bank:.1f}GiB < "
        f"estimado {estimated_gib:.1f}GiB",
    )

# [Anotación · líneas 84–127] Carga del banco final las filas de 202103–202106 y sus etiquetas, arma la clase
#   binaria BAJA+2, aplica los pesos por mes de la política ganadora y libera las tablas intermedias. Después
#   carga las filas de 202108 y verifica que haya 164.647 clientes sin repetir.
    C.add_fe_path(ctx["paths"])
    from cargar_bloques import cargar_bloques

    derived = C.split_derived(features, ctx)
    train_df, _ = cargar_bloques(
        bank, meses=C.FINAL_TRAIN, incluir_raw=True, features=derived
    )
    labels = pd.read_parquet(bank / "etiquetas.parquet")
    train_labels = labels[
        labels.foto_mes.isin(C.FINAL_TRAIN)
    ].reset_index(drop=True)
    V2.require(
        train_df[["numero_de_cliente", "foto_mes"]].equals(
            train_labels[["numero_de_cliente", "foto_mes"]]
        ),
        "Final train desalineado",
    )
    x_train = train_df[features]
    y_train = train_labels.clase_ternaria.eq("BAJA+2").to_numpy(np.int8)
    months = train_df.foto_mes.to_numpy(np.int64)
    keep, weights = C.policy_weights(
        months, V1.FINAL_RECENCY[s2["winner_policy"]]
    )
    x_fit = (
        x_train
        if bool(np.all(keep))
        else x_train.loc[keep].reset_index(drop=True)
    )
    y_fit = y_train[keep]
    del train_df, x_train, train_labels, labels, y_train, months, keep
    gc.collect()

    score_df, _ = cargar_bloques(
        bank, meses=[C.SCORE_MONTH], incluir_raw=True, features=derived
    )
    ids = score_df.numero_de_cliente.to_numpy(np.int64)
    V2.require(
        len(ids) == C.EXPECTED_ROWS[C.SCORE_MONTH]
        and len(np.unique(ids)) == len(ids),
        "IDs agosto",
    )
    x_score = score_df[features]
    del score_df
    gc.collect()

# [Anotación · líneas 129–148] Calcula la identidad de la etapa: huella del plan, la etapa 4, el hash del
#   dataset, el hash del manifiesto del banco final, las variables, los parámetros, las rondas, la política y el
#   corte.
    identity = C.fingerprint(
        {
            "run": V2.RUN,
            "stage": 5,
            "plan": V2.PLAN,
            "stage4": s4["identity"],
            "data_sha": C.digest(Path(s0["dataset"])),
            "bank_manifest_sha": C.digest(bank / "manifest.json"),
            "features": C.fingerprint(features),
            "params": s3["params"],
            "rounds": s3["rounds"],
            "policy": s2["winner_policy"],
            "n": s4["n_final"],
            "dataset_per_seed": True,
            "memory_cleanup": True,
        }
    )
    model_dir = out / "models"
    model_dir.mkdir(exist_ok=True)
    all_scores: list[np.ndarray] = []

# [Anotación · líneas 150–235] Para cada una de las 20 semillas: reutiliza el par modelo y `.npz` si es
#   válido; si no, verifica la reserva de memoria, construye el dataset de esa semilla, entrena las rondas
#   elegidas imprimiendo el avance cada 25 iteraciones, puntúa 202108, guarda el modelo en texto y el `.npz` con
#   su hash, y libera memoria.
    for index, seed in enumerate(C.SEEDS20, 1):
        cp = model_dir / f"seed_{seed}.npz"
        model_path = model_dir / f"modelo_{seed}.txt"
        if cp.is_file() and model_path.is_file():
            with np.load(cp, allow_pickle=False) as z:
                V2.require(
                    str(z["identity"].item()) == identity
                    and int(z["seed"].item()) == seed,
                    f"Checkpoint final incompatible seed={seed}",
                )
                V2.require(
                    np.array_equal(z["ids"], ids),
                    f"IDs final seed={seed}",
                )
                V2.require(
                    str(z["model_sha256"].item()) == C.digest(model_path),
                    f"Hash final seed={seed}",
                )
                scores = np.asarray(z["scores"], dtype=np.float64).copy()
            print(f"REUSAR FINAL V2 {index}/20 seed={seed}", flush=True)
        else:
            V2.require(
                not cp.exists() and not model_path.exists(),
                f"Par final parcial seed={seed}",
            )
            _, available_now = V2.meminfo_gib()
            V2.require(
                available_now >= V2.RESERVE_GIB,
                f"RAM < reserva antes seed={seed}",
            )
            print(f"ENTRENAR FINAL V2 {index}/20 seed={seed}", flush=True)
            ds, seed_params = V2.dataset_for_seed(
                x_fit, y_fit, weights, features, s3["params"], seed
            )
            started = time.monotonic()

            def progress(env):
                iteration = env.iteration + 1
                if (
                    iteration == 1
                    or iteration % 25 == 0
                    or iteration == s3["rounds"]
                ):
                    print(
                        f"seed={seed} BOOST {iteration}/{s3['rounds']}; "
                        f"t={time.monotonic()-started:.1f}s",
                        flush=True,
                    )

            model = lgb.train(
                seed_params,
                ds,
                num_boost_round=int(s3["rounds"]),
                callbacks=[progress],
            )
            scores = np.asarray(
                model.predict(x_score, num_threads=C.THREADS),
                dtype=np.float64,
            )
            V2.require(
                scores.shape == ids.shape and np.isfinite(scores).all(),
                "Scores final inválidos",
            )
            tmp_model = model_path.with_suffix(".tmp")
            model.save_model(str(tmp_model))
            tmp_model.replace(model_path)
            with cp.with_suffix(".tmp").open("wb") as fh:
                np.savez_compressed(
                    fh,
                    identity=np.array(identity),
                    seed=np.array(seed),
                    ids=ids,
                    scores=scores,
                    model_sha256=np.array(C.digest(model_path)),
                )
            cp.with_suffix(".tmp").replace(cp)
            _gcs(
                [
                    "gcloud", "storage", "cp", str(cp), str(model_path),
                    V2.REMOTE + "/stage5_models/",
                ],
                check=True,
            )
            del model, ds
            gc.collect()
        all_scores.append(scores)

# [Anotación · líneas 237–291] Promedia los 20 vectores de puntajes, exporta los `n_final` clientes de mayor
#   promedio a `C1SF2<12 caracteres de la identidad>ENS<n>.csv` y escribe `MANIFEST.json`, `mensaje_zulip.txt`
#   con el texto `submit …`, `LISTO.json` y `RESULT.json` con estado `ready_not_submitted`.
    ensemble = np.vstack(all_scores).mean(axis=0, dtype=np.float64)
    n_final = int(s4["n_final"])
    delivery = out / "delivery"
    delivery.mkdir(exist_ok=True)
    prefix = "C1SF2" + identity[:12].upper()
    csv_path = delivery / f"{prefix}ENS{n_final}.csv"
    info = C.export_csv(csv_path, ids, ensemble, n_final)
    manifest = {
        "status": "ready_not_submitted",
        "run": V2.RUN,
        "identity": identity,
        "n": n_final,
        "file": info,
        "submit_message": f"submit {prefix}ENS{n_final}",
        "representation": s1["winner"],
        "quality_arm": s0["quality_arm"],
        "recency": s2["winner_policy"],
        "params": s3["params"],
        "rounds": s3["rounds"],
        "stage4_identity": s4["identity"],
        "execution": "dataframe_64GiB_dataset_per_seed_gc",
    }
    C.write_json(delivery / "MANIFEST.json", manifest)
    (delivery / "mensaje_zulip.txt").write_text(
        manifest["submit_message"] + "\n", encoding="utf-8"
    )
    C.write_json(out / "LISTO.json", manifest)
    _gcs(
        [
            "gcloud", "storage", "cp", str(csv_path),
            str(delivery / "MANIFEST.json"),
            str(delivery / "mensaje_zulip.txt"), str(out / "LISTO.json"),
            V2.REMOTE + "/final/",
        ],
        check=True,
    )
    result = {
        "status": "ready_not_submitted",
        "identity": identity,
        "n": n_final,
        "csv": str(csv_path),
        "sha256": info["sha256"],
        "submit_message": manifest["submit_message"],
    }
    C.write_json(result_path, result)
    _gcs(
        [
            "gcloud", "storage", "cp", str(result_path),
            V2.REMOTE + "/stage5_RESULT.json",
        ],
        check=True,
    )
    print("SUPERFINAL100_V2_LISTO. NO ENVIADO.", flush=True)
    print(manifest["submit_message"], flush=True)
    return result
```

### 4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100.py

Etapas de SUPERFINAL versión 1. La versión 2 usa de acá la etapa 0 (calidad de datos), la etapa 1 (conjunto de variables), la etapa 3 (Optuna y revalidación), la etapa 4 (20 semillas y corte) y la preparación del banco final; sus `stage2`, `stage5`, `run_all` y `main` no se llaman en el camino de la entrega.

El código completo está en https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/05_superfinal100/run_superfinal100.py.txt

### 4_modelo/experimentos_20261007_post_c3/05_superfinal100/superfinal100_v2.py

Orquestador de SUPERFINAL versión 2: configura los módulos comunes, entrena con un `lgb.Dataset` por semilla, corre el canary contra C3 y define la etapa 2, la regla de 14 semillas de la etapa 4 y el orden de las etapas.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–39] Importaciones, `_gcs`, carga de `super_common` (C) y `run_superfinal100` (V1).
#   Constantes: corrida `c1superfinal100v2`, plan `plan_superfinal100_v2.json`, memoria mínima 56 GiB y reserva
#   8 GiB, y cuatro particiones de semillas sin superposición: cribado (17, 101, 202), confirmación de
#   representación (303–707), pesos por mes (808–1203) y revalidación de hiperparámetros (1304–1708).
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pandas as pd

def _gcs(cmd, check=True, **kw):
    """Respaldo opcional a Cloud Storage. Se omite cuando el bucket es el placeholder de publicacion."""
    if any("REEMPLAZAR_CON_BUCKET_PROPIO" in str(a) or "BUCKET_PRIVADO_NO_PUBLICADO" in str(a) for a in cmd):
        return None
    return subprocess.run(cmd, check=check, **kw)


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import super_common as C
import run_superfinal100 as V1

RUN = "c1superfinal100v2"
REMOTE = "gs://REEMPLAZAR_CON_BUCKET_PROPIO/corridas/" + RUN
PLAN = json.loads((HERE / "plan_superfinal100_v2.json").read_text(encoding="utf-8"))
GIB = 1024**3
MIN_TOTAL_GIB = 56.0
RESERVE_GIB = 8.0
SCREEN_SEEDS = [17, 101, 202]
REP_CONFIRM_SEEDS = [303, 404, 505, 606, 707]
RECENCY_SEEDS = [808, 909, 1001, 1102, 1203]
TUNE_CONFIRM_SEEDS = [1304, 1405, 1506, 1607, 1708]


# [Anotación · líneas 42–61] `meminfo_gib` lee memoria total y disponible de `/proc/meminfo`.
#   `configure_runtime` cambia en los módulos C y V1 el nombre de la corrida y el destino remoto, hace que
#   `plan_doc` devuelva el plan de la versión 2 y reemplaza `train_seeds` por `train_seeds_per_seed`.
def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def meminfo_gib() -> tuple[float, float]:
    values = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, rest = line.split(":", 1)
        values[key] = float(rest.strip().split()[0]) / 1024 / 1024
    return values["MemTotal"], values["MemAvailable"]


def configure_runtime() -> None:
    C.RUN = RUN
    C.REMOTE = REMOTE
    V1.RUN = RUN
    V1.REMOTE = REMOTE
    V1.plan_doc = lambda: PLAN
    V1.train_seeds = train_seeds_per_seed


# [Anotación · líneas 64–81] `dataset_for_seed` construye un `lgb.Dataset` nuevo para una semilla, con
#   `max_bin` y la semilla en los parámetros del dataset; no pasa pesos cuando todos valen 1.
def dataset_for_seed(x, y, weights, features, params: dict, seed: int):
    import lightgbm as lgb

    seed_params = dict(params)
    seed_params["seed"] = int(seed)
    weight_arg = None if weights is None or bool(np.all(weights == 1.0)) else weights
    ds = lgb.Dataset(
        x,
        label=y,
        weight=weight_arg,
        feature_name=features,
        free_raw_data=False,
        params={
            "max_bin": int(seed_params.get("max_bin", 255)),
            "seed": int(seed),
        },
    )
    return ds, seed_params


# [Anotación · líneas 84–178] `train_seeds_per_seed` aplica los pesos por mes y, para cada semilla, reutiliza
#   el `.npz` válido, copia un puntaje heredado o entrena con un dataset propio de esa semilla; valida puntajes
#   en [0, 1], guarda el modelo si se pide y escribe el `.npz` con identidad, etiqueta, semilla, claves y
#   puntajes.
def train_seeds_per_seed(
    data: dict,
    features: list[str],
    params: dict,
    rounds: int,
    seeds: list[int],
    weights_by_month: dict[int, float],
    out_dir: Path,
    identity: str,
    label: str,
    save_models: bool = False,
    backup_prefix: str | None = None,
    reuse_scores: dict[int, np.ndarray] | None = None,
) -> dict[int, np.ndarray]:
    import lightgbm as lgb

    out_dir.mkdir(parents=True, exist_ok=True)
    reuse_scores = reuse_scores or {}
    keep, weights = C.policy_weights(data["train_months"], weights_by_month)
    x_train = (
        data["x_train"]
        if bool(np.all(keep))
        else data["x_train"].loc[keep].reset_index(drop=True)
    )
    y_train = data["y_train"][keep]
    x_eval = data["x_eval"]
    ids = data["ids"]
    y_eval = data["y_eval"]

    result: dict[int, np.ndarray] = {}
    for index, seed in enumerate(seeds, 1):
        cp = out_dir / f"seed_{seed}.npz"
        model_path = out_dir / f"modelo_{seed}.txt"
        existing = C.score_checkpoint(cp, identity, label, seed, ids, y_eval)
        if existing is not None:
            if save_models:
                require(model_path.is_file(), f"Checkpoint sin modelo seed={seed}")
                with np.load(cp, allow_pickle=False) as z:
                    require(
                        str(z["model_sha256"].item()) == C.digest(model_path),
                        f"Hash modelo/checkpoint seed={seed}",
                    )
            result[seed] = existing
            print(f"REUSAR {label} {index}/{len(seeds)} seed={seed}", flush=True)
            continue

        if seed in reuse_scores:
            scores = np.asarray(reuse_scores[seed], dtype=np.float64)
            require(scores.shape == ids.shape and np.isfinite(scores).all(), "Reuse inválido")
            with cp.with_suffix(".tmp").open("wb") as fh:
                np.savez_compressed(
                    fh,
                    identity=np.array(identity), label=np.array(label),
                    seed=np.array(seed), ids=ids, y=y_eval, scores=scores,
                    reused=np.array(True), model_sha256=np.array(""),
                )
            cp.with_suffix(".tmp").replace(cp)
            result[seed] = scores
            print(f"COPIAR SCORE {label} {index}/{len(seeds)} seed={seed}", flush=True)
            continue

        print(
            f"ENTRENAR {label} {index}/{len(seeds)} seed={seed}; "
            f"features={len(features)}; rounds={rounds}; dataset_per_seed=SI",
            flush=True,
        )
        ds, seed_params = dataset_for_seed(
            x_train, y_train, weights, features, params, seed
        )
        model = lgb.train(seed_params, ds, num_boost_round=int(rounds))
        scores = np.asarray(model.predict(x_eval, num_threads=C.THREADS), dtype=np.float64)
        require(scores.shape == ids.shape and np.isfinite(scores).all(), "Scores inválidos")
        require(((scores >= 0) & (scores <= 1)).all(), "Scores fuera de rango")

        model_sha = ""
        if save_models:
            tmp_model = model_path.with_suffix(".tmp")
            model.save_model(str(tmp_model))
            tmp_model.replace(model_path)
            model_sha = C.digest(model_path)
        with cp.with_suffix(".tmp").open("wb") as fh:
            np.savez_compressed(
                fh,
                identity=np.array(identity), label=np.array(label),
                seed=np.array(seed), ids=ids, y=y_eval, scores=scores,
                reused=np.array(False), model_sha256=np.array(model_sha),
            )
        cp.with_suffix(".tmp").replace(cp)
        if backup_prefix:
            files = [str(cp)] + ([str(model_path)] if save_models else [])
            _gcs(["gcloud", "storage", "cp", *files, backup_prefix + "/"], check=True)
        result[seed] = scores
        del model, ds
        gc.collect()
    return result


# [Anotación · líneas 181–217] `exact_s3_canary` entrena C3 con la semilla 17, parámetros base y 300 rondas
#   sobre 202103–202104 y exige que los puntajes de 202106 sean idénticos (diferencia máxima 0) a los guardados
#   en el paso 2.
def exact_s3_canary(ctx: dict) -> dict:
    root = ctx["paths"]["out"] / "canary_s3_exact"
    result_path = root / "RESULT.json"
    if result_path.is_file():
        result = C.load_json(result_path)
        require(result.get("status") == "passed" and result.get("max_abs") == 0.0,
                "Canary previo inválido")
        return result

    root.mkdir(parents=True, exist_ok=True)
    features = list(ctx["schema"])
    data = C.load_fold(ctx, features, C.TRAIN_EVAL, C.EVAL_MONTH, ctx["paths"]["bank_orig"])
    identity = C.fingerprint({"run": RUN, "stage": "canary", "plan": PLAN, "seed": 17})
    scores = train_seeds_per_seed(
        data, features, C.base_params(ctx["paths"]), 300, [17],
        {202103: 1.0, 202104: 1.0}, root / "scores", identity, "C3_S3_CANARY",
    )[17]
    with np.load(ctx["paths"]["s3"] / "C3_HIST_MAS_TARJETAS/seed_17.npz",
                 allow_pickle=False) as z:
        expected_ids = np.asarray(z["ids"], dtype=np.int64)
        expected_y = np.asarray(z["y"], dtype=np.int8)
        expected = np.asarray(z["scores"], dtype=np.float64)
    require(np.array_equal(data["ids"], expected_ids), "Canary IDs")
    require(np.array_equal(data["y_eval"], expected_y), "Canary y")
    max_abs = float(np.max(np.abs(scores - expected)))
    exact = bool(np.array_equal(scores, expected))
    require(exact and max_abs == 0.0, f"CANARY S3 FALLÓ: max_abs={max_abs}")
    result = {
        "status": "passed", "identity": identity, "seed": 17,
        "max_abs": max_abs, "exact_array_equal": exact,
        "candidate_sha256": hashlib.sha256(scores.tobytes()).hexdigest(),
        "s3_sha256": hashlib.sha256(expected.tobytes()).hexdigest(),
    }
    C.write_json(result_path, result)
    _gcs(["gcloud", "storage", "cp", str(result_path), REMOTE + "/CANARY_S3.json"], check=True)
    print("CANARY_S3_EXACT_OK", flush=True)
    return result


# [Anotación · líneas 220–292] `stage2_v2` (etapa 2): entrena las cuatro políticas de peso por mes con las
#   variables ganadoras, parámetros base, 300 rondas y las semillas 808–1203, y evalúa en 202106. Una política
#   pasa si su ganancia de meseta supera la de EXPANDING en los mismos cortes, la diferencia pareada media y
#   mediana son positivas y gana en al menos 3 de 5 semillas. Queda la promovida de mayor ganancia de meseta, o
#   EXPANDING.
def stage2_v2(ctx: dict, s0: dict, s1: dict) -> dict:
    out = V1.stage_path(ctx, 2, "recency")
    result_path = out / "RESULT.json"
    if result_path.is_file():
        return C.load_json(result_path)
    features = C.load_json(Path(s1["winner_features_file"]))["features"]
    data = C.load_fold(ctx, features, C.TRAIN_EVAL, C.EVAL_MONTH, Path(s0["eval_bank"]))
    params = C.base_params(ctx["paths"])
    identity = C.fingerprint({
        "run": RUN, "stage": 2, "plan": PLAN, "stage1": s1["identity"],
        "features": C.fingerprint(features), "seeds": RECENCY_SEEDS,
    })
    scores_by = {}
    meta = {}
    control_curves = None
    for policy, weights in V1.RECENCY.items():
        pid = C.fingerprint({"parent": identity, "policy": policy, "weights": weights})
        scores = train_seeds_per_seed(
            data, features, params, 300, RECENCY_SEEDS, weights,
            out / policy, pid, policy,
        )
        choice, curves, ensemble = C.summarize_scores(data["ids"], data["y_eval"], scores, RECENCY_SEEDS)
        scores_by[policy] = {k: v.copy() for k, v in scores.items()}
        meta[policy] = {"identity": pid, "choice": choice}
        if policy == "EXPANDING":
            control_curves = curves
        del scores, curves, ensemble
        gc.collect()
    require(control_curves is not None, "Falta EXPANDING")
    rows = []
    promoted = []
    control_scores = scores_by["EXPANDING"]
    for policy in V1.RECENCY:
        choice = meta[policy]["choice"]
        if policy == "EXPANDING":
            paired = {"mean": 0.0, "median": 0.0, "sd": 0.0,
                      "positive_fraction": 0.0, "wins": 0, "ties": 5, "losses": 0}
            control_same = choice["ganancia_robusta"]
            passed = True
        else:
            _, curves, _ = C.summarize_scores(data["ids"], data["y_eval"], scores_by[policy], RECENCY_SEEDS)
            paired = C.paired_at_plateau(curves, control_curves, RECENCY_SEEDS, choice["meseta_n"])
            control_same = V1.control_gain_at_ns(
                data["ids"], data["y_eval"], control_scores, RECENCY_SEEDS, choice["meseta_n"]
            )
            passed = bool(choice["ganancia_robusta"] > control_same and paired["mean"] > 0
                          and paired["median"] > 0 and paired["wins"] >= 3)
            if passed:
                promoted.append(policy)
        rows.append({
            "policy": policy, "passed": passed,
            "control_gain_same_plateau": float(control_same),
            "delta_ensemble_same_plateau": float(choice["ganancia_robusta"] - control_same),
            **{k: v for k, v in choice.items() if k != "meseta_gain"},
            **{f"paired_{k}": v for k, v in paired.items() if k != "deltas"},
        })
    frame = pd.DataFrame(rows)
    frame.to_csv(out / "comparison.csv", index=False)
    winner = (
        frame[frame.policy.isin(promoted)]
        .sort_values(["ganancia_robusta", "delta_ensemble_same_plateau"], ascending=[False, False])
        .iloc[0].policy if promoted else "EXPANDING"
    )
    result = {
        "status": "completed", "identity": identity, "winner_policy": winner,
        "representation": s1["winner"], "quality_arm": s0["quality_arm"],
        "winner_features_file": s1["winner_features_file"], "promoted": promoted,
        "seeds": RECENCY_SEEDS, "fresh_vs_stage1": True,
    }
    C.write_json(result_path, result)
    _gcs(["gcloud", "storage", "cp", str(result_path), str(out / "comparison.csv"), REMOTE + "/"], check=True)
    print("STAGE2_V2_COMPLETO. Policy:", winner, flush=True)
    return result


# [Anotación · líneas 295–310] `stage4_strict` llama a la etapa 4 de V1 y recalcula `promote_to_august`
#   exigiendo al menos 14 de 20 semillas a favor, además de ganancia de meseta mayor que el control y diferencia
#   pareada media y mediana positivas; reescribe el `RESULT.json`.
def stage4_strict(ctx: dict, s0: dict, s1: dict, s2: dict, s3: dict) -> dict:
    result = V1.stage4(ctx, s0, s1, s2, s3)
    paired = result["paired"]
    strict = bool(
        result["candidate_choice"]["ganancia_robusta"] > result["control_gain_at_candidate_plateau"]
        and paired["mean"] > 0 and paired["median"] > 0 and paired["wins"] >= 14
    )
    result["legacy_promote_12_of_20"] = bool(result.get("promote_to_august"))
    result["promotion_rule_v2"] = {
        "paired_mean_gt": 0, "paired_median_gt": 0, "wins_min": 14,
        "ensemble_robust_gain_gt_c3": True,
    }
    result["promote_to_august"] = strict
    C.write_json(ctx["paths"]["out"] / "stage4_confirm20/RESULT.json", result)
    print(f"STAGE4_V2_PROMOTE={strict}; wins={paired['wins']}/20", flush=True)
    return result


# [Anotación · líneas 313–435] `stage5_per_seed`: entrenamiento final de SUPERFINAL con un dataset por
#   semilla. `run_superfinal100_v2_safe.py` la reemplaza por `stage5_per_seed_safe`, que hace lo mismo liberando
#   memoria entre pasos.
def stage5_per_seed(ctx: dict, s0: dict, s1: dict, s2: dict, s3: dict, s4: dict) -> dict:
    import lightgbm as lgb

    out = V1.stage_path(ctx, 5, "final")
    result_path = out / "RESULT.json"
    if result_path.is_file():
        return C.load_json(result_path)
    if not s4["promote_to_august"]:
        result = {"status": "stopped_no_promotion", "stage4_identity": s4["identity"], "no_submit": True}
        C.write_json(result_path, result)
        _gcs(["gcloud", "storage", "cp", str(result_path), REMOTE + "/stage5_RESULT.json"], check=True)
        print("STAGE5 NO EJECUTADO: no promovió bajo regla v2.", flush=True)
        return result

    total_gib, available_gib = meminfo_gib()
    require(total_gib >= MIN_TOTAL_GIB, f"VM insuficiente: MemTotal={total_gib:.1f}GiB < {MIN_TOTAL_GIB}")
    features = C.load_json(Path(s1["winner_features_file"]))["features"]
    n_train = sum(C.EXPECTED_ROWS[m] for m in C.FINAL_TRAIN)
    n_score = C.EXPECTED_ROWS[C.SCORE_MONTH]
    estimated_gib = ((2 * n_train + n_score) * len(features) * 8) / GIB + RESERVE_GIB
    require(available_gib >= estimated_gib,
            f"RAM disponible insuficiente: {available_gib:.1f}GiB < estimado {estimated_gib:.1f}GiB")
    print(f"RAM_GUARD_OK total={total_gib:.1f} available={available_gib:.1f} estimated={estimated_gib:.1f}", flush=True)

    bank = V1.prepare_final_bank(ctx, s0, features)
    C.add_fe_path(ctx["paths"])
    from cargar_bloques import cargar_bloques
    derived = C.split_derived(features, ctx)
    train_df, _ = cargar_bloques(bank, meses=C.FINAL_TRAIN, incluir_raw=True, features=derived)
    labels = pd.read_parquet(ctx["paths"]["bank_orig"] / "etiquetas.parquet")
    train_labels = labels[labels.foto_mes.isin(C.FINAL_TRAIN)].reset_index(drop=True)
    require(train_df[["numero_de_cliente", "foto_mes"]].equals(
        train_labels[["numero_de_cliente", "foto_mes"]]), "Final train desalineado")
    x_train = train_df[features]
    y_train = train_labels.clase_ternaria.eq("BAJA+2").to_numpy(np.int8)
    months = train_df.foto_mes.to_numpy(np.int64)
    keep, weights = C.policy_weights(months, V1.FINAL_RECENCY[s2["winner_policy"]])
    x_fit = x_train if bool(np.all(keep)) else x_train.loc[keep].reset_index(drop=True)
    y_fit = y_train[keep]

    score_df, _ = cargar_bloques(bank, meses=[C.SCORE_MONTH], incluir_raw=True, features=derived)
    ids = score_df.numero_de_cliente.to_numpy(np.int64)
    require(len(ids) == C.EXPECTED_ROWS[C.SCORE_MONTH] and len(np.unique(ids)) == len(ids), "IDs agosto")
    x_score = score_df[features]
    identity = C.fingerprint({
        "run": RUN, "stage": 5, "plan": PLAN, "stage4": s4["identity"],
        "data_sha": C.digest(Path(s0["dataset"])),
        "bank_manifest_sha": C.digest(bank / "manifest.json"),
        "features": C.fingerprint(features), "params": s3["params"],
        "rounds": s3["rounds"], "policy": s2["winner_policy"],
        "n": s4["n_final"], "dataset_per_seed": True,
    })
    model_dir = out / "models"
    model_dir.mkdir(exist_ok=True)
    all_scores = []
    for index, seed in enumerate(C.SEEDS20, 1):
        cp = model_dir / f"seed_{seed}.npz"
        model_path = model_dir / f"modelo_{seed}.txt"
        if cp.is_file() and model_path.is_file():
            with np.load(cp, allow_pickle=False) as z:
                require(str(z["identity"].item()) == identity and int(z["seed"].item()) == seed,
                        f"Checkpoint final incompatible seed={seed}")
                require(np.array_equal(z["ids"], ids), f"IDs final seed={seed}")
                require(str(z["model_sha256"].item()) == C.digest(model_path), f"Hash final seed={seed}")
                scores = np.asarray(z["scores"], dtype=np.float64).copy()
            print(f"REUSAR FINAL V2 {index}/20 seed={seed}", flush=True)
        else:
            require(not cp.exists() and not model_path.exists(), f"Par final parcial seed={seed}")
            _, available_now = meminfo_gib()
            require(available_now >= RESERVE_GIB, f"RAM < reserva antes seed={seed}")
            print(f"ENTRENAR FINAL V2 {index}/20 seed={seed}", flush=True)
            ds, seed_params = dataset_for_seed(x_fit, y_fit, weights, features, s3["params"], seed)
            started = time.monotonic()
            def progress(env):
                it = env.iteration + 1
                if it == 1 or it % 25 == 0 or it == s3["rounds"]:
                    print(f"seed={seed} BOOST {it}/{s3['rounds']}; t={time.monotonic()-started:.1f}s", flush=True)
            model = lgb.train(seed_params, ds, num_boost_round=int(s3["rounds"]), callbacks=[progress])
            scores = np.asarray(model.predict(x_score, num_threads=C.THREADS), dtype=np.float64)
            require(scores.shape == ids.shape and np.isfinite(scores).all(), "Scores final inválidos")
            tmp_model = model_path.with_suffix(".tmp")
            model.save_model(str(tmp_model))
            tmp_model.replace(model_path)
            with cp.with_suffix(".tmp").open("wb") as fh:
                np.savez_compressed(fh, identity=np.array(identity), seed=np.array(seed),
                                    ids=ids, scores=scores,
                                    model_sha256=np.array(C.digest(model_path)))
            cp.with_suffix(".tmp").replace(cp)
            _gcs(["gcloud", "storage", "cp", str(cp), str(model_path),
                            REMOTE + "/stage5_models/"], check=True)
            del model, ds
            gc.collect()
        all_scores.append(scores)

    ensemble = np.vstack(all_scores).mean(axis=0, dtype=np.float64)
    n_final = int(s4["n_final"])
    delivery = out / "delivery"
    delivery.mkdir(exist_ok=True)
    prefix = "C1SF2" + identity[:12].upper()
    csv_path = delivery / f"{prefix}ENS{n_final}.csv"
    info = C.export_csv(csv_path, ids, ensemble, n_final)
    manifest = {
        "status": "ready_not_submitted", "run": RUN, "identity": identity,
        "n": n_final, "file": info, "submit_message": f"submit {prefix}ENS{n_final}",
        "representation": s1["winner"], "quality_arm": s0["quality_arm"],
        "recency": s2["winner_policy"], "params": s3["params"],
        "rounds": s3["rounds"], "stage4_identity": s4["identity"],
        "execution": "dataframe_64GiB_dataset_per_seed",
    }
    C.write_json(delivery / "MANIFEST.json", manifest)
    (delivery / "mensaje_zulip.txt").write_text(manifest["submit_message"] + "\n", encoding="utf-8")
    C.write_json(out / "LISTO.json", manifest)
    _gcs(["gcloud", "storage", "cp", str(csv_path), str(delivery / "MANIFEST.json"),
                    str(delivery / "mensaje_zulip.txt"), str(out / "LISTO.json"),
                    REMOTE + "/final/"], check=True)
    result = {"status": "ready_not_submitted", "identity": identity, "n": n_final,
              "csv": str(csv_path), "sha256": info["sha256"],
              "submit_message": manifest["submit_message"]}
    C.write_json(result_path, result)
    _gcs(["gcloud", "storage", "cp", str(result_path), REMOTE + "/stage5_RESULT.json"], check=True)
    print("SUPERFINAL100_V2_LISTO. NO ENVIADO.", flush=True)
    print(manifest["submit_message"], flush=True)
    return result


# [Anotación · líneas 438–451] `run_all` encadena: canary, etapa 0, etapa 1 (con sus dos particiones de
#   semillas), etapa 2, etapa 3 (con la partición de revalidación), etapa 4 con las 20 semillas y etapa 5.
def run_all(ctx: dict) -> dict:
    exact_s3_canary(ctx)
    s0 = V1.stage0(ctx)
    V1.SEEDS3 = SCREEN_SEEDS
    V1.SEEDS5 = REP_CONFIRM_SEEDS
    s1 = V1.stage1(ctx, s0)
    s2 = stage2_v2(ctx, s0, s1)
    V1.SEEDS5 = TUNE_CONFIRM_SEEDS
    s3 = V1.stage3(ctx, s0, s1, s2)
    V1.SEEDS20 = list(C.SEEDS20)
    s4 = stage4_strict(ctx, s0, s1, s2, s3)
    s5 = stage5_per_seed(ctx, s0, s1, s2, s3, s4)
    return {"stage0": s0, "stage1": s1, "stage2": s2,
            "stage3": s3, "stage4": s4, "stage5": s5}


# [Anotación · líneas 454–484] `main` exige `--all`, configura los módulos, verifica 56 GiB de memoria total,
#   corre el preflight base, valida el plan, toma un candado de archivo y ejecuta todo; al final imprime si la
#   etapa 4 promovió, las semillas a favor y el estado de la etapa 5.
def main() -> None:
    parser = argparse.ArgumentParser(description="SUPERFINAL100 v2 corregido")
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    require(args.all, "Usar --all")
    configure_runtime()
    total_gib, _ = meminfo_gib()
    require(total_gib >= MIN_TOTAL_GIB,
            f"VM de al menos {MIN_TOTAL_GIB:.0f} GiB requerida; MemTotal={total_gib:.1f} GiB")
    ctx = C.preflight_base(args.home.resolve())
    require(PLAN["run"] == RUN and PLAN["stop_after_this_experiment"] is True,
            "Plan v2 inesperado")
    ctx["paths"]["out"].mkdir(parents=True, exist_ok=True)
    import fcntl
    lock = (ctx["paths"]["out"] / ".lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise SystemExit("SUPERFINAL100 v2 ya tiene otro proceso activo")
    result = run_all(ctx)
    print(json.dumps({
        "stage4_promote": result["stage4"].get("promote_to_august"),
        "stage4_wins": result["stage4"].get("paired", {}).get("wins"),
        "stage5_status": result["stage5"].get("status"),
        "stage5_submit": result["stage5"].get("submit_message"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

### 4_modelo/experimentos_20261007_post_c3/04_b1_variables_rotas/run_b1.py

Paso 4, B1. Sin reentrenar, puntúa 202106 con los 20 modelos de Q0 sobre cuatro copias del dataset con variables de un mes pasadas a NA, y decide con una regla fija qué brazo de calidad de datos usa SUPERFINAL (o el dataset original).

El código completo está en https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/04_b1_variables_rotas/run_b1.py.txt

### 4_modelo/experimentos_20261007_post_c3/02_q0_ccajas_na/run_q0.py

Paso 4, Q0. Reproduce los 20 modelos de C3 (202103–202104, 300 rondas) con tolerancia 1e-12, los guarda y vuelve a puntuar 202106 con `ccajas_depositos` de 202105 en NA. B1 y SUPERFINAL exigen su salida.

El código completo está en https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/02_q0_ccajas_na/run_q0.py.txt

### 4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/run_cluster_aware.py

Modelo final (CLAW2). Toma variables, hiperparámetros, rondas, política de pesos por mes y banco final de SUPERFINAL, prueba tres recetas de peso por grupo para las filas BAJA+2 (202105 y 202106) y, si pasan las tres etapas, entrena 20 LightGBM con 202103–202106 y escribe el CSV de 13.500 clientes de 202108.

El código completo está en https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/run_cluster_aware.py.txt

### 4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/cluster_aware_common.py

Cálculo de los pesos por grupo de las filas BAJA+2 con conservación de la suma de pesos, métricas en el corte fijo 13.500 por grupo y resumen pareado por semilla.

El código completo está en https://emavaldez.github.io/postmortem/fuentes/clarirz/4_modelo/experimentos_20261007_post_c3/13_cluster_aware_reweighting/cluster_aware_common.py.txt


## Explicaciones del alumno (texto original)

### README.md

> # Primera Competencia DMEyF 2026 — Clara M. Rodríguez
>
> <p align="justify"><b>Entrega final:</b> <code>C1CLAW2C065771C9ENS13500.csv</code> (13.500 <code>numero_de_cliente</code> de 202108, una columna, sin encabezado). Ganancia pública del bot: <b>101,0900 M ARS</b> (Submission ID <code>1586-1791569183206183</code>).</p>
>
> ## Cómo armé mi predicción final
>
> <p align="justify">Es un <b>ensamble por promedio de 20 modelos LightGBM</b>. Todos tienen las mismas variables y los mismos hiperparámetros; solo cambia la semilla. Lo distinto del modelo es <b>cómo pesa a los clientes que se van</b> mientras entrena.</p>
>
> | Paso | Carpeta | Qué hace |
> |---|---|---|
> | 1 | [`1_dataset/`](1_dataset/) | Del CSV de la cátedra arma la clase (`clase_ternaria`) y guarda un Parquet |
> | 2 | [`2_variables/`](2_variables/) | Construye las variables: a las 152 originales les agrega historia y ratios de tarjetas → **2.062 variables** |
> | 3 | [`3_grupos_baja2/`](3_grupos_baja2/) | Separa a los clientes BAJA+2 en **cinco grupos** según cómo se van del banco |
> | 4 | [`4_modelo/`](4_modelo/) | Elige hiperparámetros con **Optuna** (SUPERFINAL) y entrena el modelo final (**CLAW2**), que reparte el peso de los BAJA+2 entre esos cinco grupos → archivo final |
> | 5 | [`5_prediccion_final/`](5_prediccion_final/) | Qué archivo se envió, con qué parámetros, y cómo verificarlo |
>
> <p align="justify">La probabilidad final de cada cliente es el promedio simple de las probabilidades de los 20 modelos. Se ordenan de mayor a menor (empates por <code>numero_de_cliente</code>) y se envían los primeros 13.500.</p>
>
> ### Detalle del modelo
>
> - **Clase:** BAJA+2 contra el resto (BAJA+1 y CONTINUA juntos).
> - **Meses:** entrenamiento final 202103–202106, predicción 202108. 202107 no tiene clase; solo aporta historia para los lags de agosto.
> - **Variables (2.062):** las 152 originales + 1.910 derivadas: historia de cada variable (lags, deltas, transiciones) y ratios de tarjetas. Es el bloque que llamo **C3**.
> - **Ventana:** los cuatro meses de entrenamiento con el mismo peso.
> - **Hiperparámetros:** los que eligió Optuna en SUPERFINAL (20 trials, `TPESampler(seed=17)`, entrenando marzo y midiendo ganancia en mayo). El modelo final no volvió a optimizar.
>
> | num_iterations | learning_rate | num_leaves | min_data_in_leaf | feature_fraction | bagging_fraction | max_bin | lambda_l1 | lambda_l2 |
> |---|---|---|---|---|---|---|---|---|
> | 361 | 0,015387 | 79 | 551 | 0,686638 | 0,652536 | 63 | 5,72e-06 | 0,013649 |
>
> <p align="justify">Con todos los decimales: <a href="5_prediccion_final/MANIFIESTO_CLAW2_TRANSCRIPTO.json"><code>5_prediccion_final/MANIFIESTO_CLAW2_TRANSCRIPTO.json</code></a>. Los 20 trials de Optuna están en <a href="4_modelo/experimentos_20261007_post_c3/05_superfinal100/trials.csv"><code>4_modelo/.../05_superfinal100/trials.csv</code></a>.</p>
>
> - **Semillas (20):** 17, 101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203, 1304, 1405, 1506, 1607, 1708, 1809, 1910.
> - **Pesos de los BAJA+2:** cada BAJA+2 de marzo a junio pertenece a uno de cinco grupos. Los grupos chicos pesan más y los grandes menos (tope entre 0,5 y 4), y después se reescala para que **el peso total de los BAJA+2 no cambie** (4.067). No cambia el balance entre los que se van y los que se quedan; solo cambia a cuáles BAJA+2 mira más el modelo.
>
> | Grupo | BAJA+2 marzo–junio | Peso de cada uno |
> |---|---:|---:|
> | C1 | 1.280 | 0,635 |
> | C2 | 1.136 | 0,716 |
> | C3 | 857 | 0,949 |
> | C4 | 579 | 1,405 |
> | C5 | 215 | 3,783 |
>
> <p align="justify">Los grupos <b>no son una variable del modelo</b> y no se usan para predecir agosto: solo definen el peso de los BAJA+2 de entrenamiento.</p>
>
> ### Por qué esos pesos
>
> <p align="justify">Cuando miré a quién se le escapaba a SUPERFINAL en junio, vi que no fallaba parejo. De los 1.098 BAJA+2 de junio agarraba 697 y perdía 401, y <b>309 de esos 401 eran de dos grupos (C2 y C5)</b>:</p>
>
> | Grupo | BAJA+2 en junio | Detectados | % detectado |
> |---|---:|---:|---:|
> | C1 | 324 | 238 | 73,5% |
> | C2 | 334 | 115 | 34,4% |
> | C3 | 185 | 181 | 97,8% |
> | C4 | 105 | 103 | 98,1% |
> | C5 | 150 | 60 | 40,0% |
>
> <p align="justify">El modelo aprendía bien las formas "fáciles" de irse y casi ignoraba las otras. Repartiendo el peso, en junio pasó de <b>697 a 718 BAJA+2 detectados</b> con los mismos 13.500 envíos (+23,10 M ARS), y mejoró en las 20 semillas.</p>
>
> ## Cómo replicar (en orden)
>
> <p align="justify">Todo es <b>Python 3.12</b>; la corrida original fue en una máquina Linux con 56 GB de RAM. En el repo está el código y nada más: el dataset (<code>competencia_01_crudo.csv</code> de la cátedra), las variables, los grupos, los 20 modelos y el archivo final se generan corriendo los pasos en orden. Cada carpeta tiene su README con el comando exacto; acá va el resumen.</p>
>
> ```bash
> git clone https://github.com/ClariRZ/Primera-compentencia.git
> cd Primera-compentencia
> python3.12 -m venv .venv && source .venv/bin/activate
> python -m pip install -r requirements.lock -r requirements-z501.txt
> ```
>
> <p align="justify">Los scripts leen y escriben en carpetas fijas dentro de <code>$HOME</code>; el mapa de cuál es cada una está en <a href="4_modelo/README.md"><code>4_modelo/README.md</code></a>.</p>
>
> 1. **Dataset** → `1_dataset/preparar_competencia.py` deja `competencia_01.parquet`.
> 2. **Variables** → `2_variables/.../run_screening.py` construye el banco de variables y `run_s3_confirm_c3.py` deja el bloque C3.
> 3. **Grupos** → `3_grupos_baja2/validar_clusters_estabilidad.py` escribe `reference_labels.csv` (4.067 clientes y su grupo).
> 4. **Modelo** → dentro de `4_modelo/`: controles de calidad (`run_q0.py`), SUPERFINAL con Optuna (`run_superfinal100_v2_safe.py --all`) y el modelo final (`run_cluster_aware.py --phase all`), que escribe:
>
> ```
> $HOME/c1clusteraware01/stage4_august/delivery/C1CLAW2C065771C9ENS13500.csv   <- la entrega final
> ```
>
> 5. **Verificación** → `5_prediccion_final/verificar_csv_final.py` compara filas, formato y SHA-256 contra el archivo enviado.
>
> <p align="justify">Al reentrenar 20 modelos LightGBM en otra máquina puede haber diferencias ínfimas en las probabilidades y, como mucho, un puñado de clientes distintos cerca del corte 13.500. El nombre del archivo lo arma el script: <code>C1CLAW</code> + los primeros 10 caracteres de la identidad de la corrida + <code>ENS13500</code>. El código es el que corrió; el único cambio es que los respaldos a Cloud Storage se saltean si no se configura un bucket.</p>
>
> ## Lo que probé en el camino
>
> <p align="justify">Fueron cuatro etapas. "Bot" es la ganancia <b>pública</b> en millones de ARS; "interno" es la diferencia de ganancia en junio contra el modelo que venía usando, entrenando con marzo y abril.</p>
>
> ### 1. ¿Qué clase y qué variables originales? (corte 11.000)
>
> | Qué probé | Bot | ¿Me lo quedé? | Por qué |
> |---|---:|---|---|
> | Ambas bajas contra CONTINUA, sin las seis variables de préstamos | 87,16 | Punto de partida | Mi primer modelo. Promediar sus 20 semillas dio 87,37. |
> | Lo mismo + resúmenes de fechas de Visa y Master | 86,96 | No | No agregó nada. |
> | BAJA+2 contra CONTINUA, sacando los BAJA+1 del entrenamiento | 87,56 | No | Casi igual que el primero. |
> | Ambas bajas, con las variables de préstamos | 89,32 | — | Los préstamos ayudaban. |
> | Montos de préstamos sí, cantidades no | 89,56 | No | Parecido al anterior. |
> | Historia de 10 variables, sin préstamos | 89,86 | — | La historia ayudaba. |
> | Historia de 10 variables, con préstamos | 90,03 | — | Mejor que por separado. |
> | **BAJA+2 contra el resto**, con préstamos | 91,47 | **Sí** | Entrenar con la clase que paga fue lo que más mejoró. |
> | Mezclas mitad y mitad del primer modelo con los tres mejores | 90,62 / 90,19 / 88,36 | No | Mezclar con un modelo peor bajó al mejor. |
> | Promedio de las 20 semillas de BAJA+2 contra el resto | **91,80** | **Sí** | Base de todo lo que siguió. |
>
> ### 2. ¿Más variables?
>
> | Qué probé | Interno | Bot | ¿Me lo quedé? | Por qué |
> |---|---:|---:|---|---|
> | Historia masiva de todas las variables | −6,97 | — | No | Peor que sin agregar nada. |
> | Representaciones masivas (rankings, estados, transformaciones) | −7,41 | — | No | Peor en mayo y en junio. |
> | Las dos cosas juntas | +3,67 | — | No | Mejoraba en promedio, pero el desvío entre semillas (23,34) era mucho mayor que la mejora. |
> | **Solo dos familias: historia + tarjetas/ratios (C3)** | +8,95 | **96,06** | **Sí** | Confirmado con 20 semillas: +6,01 y 15 de 20 a favor. |
>
> <p align="justify">Agregar miles de variables empeoró; agregar dos familias elegidas mejoró.</p>
>
> ### 3. Ventana, hiperparámetros y corte
>
> | Qué probé | Bot | ¿Me lo quedé? | Por qué |
> |---|---:|---|---|
> | **SUPERFINAL:** sobre C3, comparar representaciones, pesos por mes, 20 trials de Optuna y el corte, con reglas fijadas de antemano | **98,51** | **Sí** | Quedó C3, los cuatro meses con igual peso, los hiperparámetros de la tabla de arriba y corte 13.500. |
> | Promediar modelos con hiperparámetros distintos | — | No | En junio dio −12,1 M contra SUPERFINAL. |
> | Mezclar los modelos de C3 con los de SUPERFINAL | — | No | No pasó mi regla para reemplazar a SUPERFINAL. |
>
> ### 4. ¿A cuáles BAJA+2 mirar más?
>
> <p align="justify">Las tres primeras filas se compararon en mayo, entrenando con marzo y con 3 semillas.</p>
>
> | Qué probé | Interno | Bot | ¿Me lo quedé? | Por qué |
> |---|---:|---:|---|---|
> | Triplicar el peso de C2 y multiplicar por 2,5 el de C5 | −9,9 | — | No | Recuperaba más C2 y C5, pero perdía más en los otros grupos. |
> | Peso inverso a lo que se detectaba cada grupo en junio | −12,1 | — | No | Lo mismo. |
> | **Peso inverso al tamaño del grupo, con tope** | +4,4 | **101,09** | **Sí, es la entrega final** | Único que pasó mayo; en junio dio +23,10 M y 20 de 20 semillas. |
> | Armar los grupos solo con marzo, sin mirar meses posteriores | — | — | No | No pasó la prueba de mayo. |
>
> <p align="justify"><b>Sobre el corte:</b> hasta C3 usé 11.000. SUPERFINAL comparó de 8.000 a 15.000 de a 500 y eligió 13.500 con 20 semillas en junio; el modelo final lo mantuvo fijo. Entre C3 y SUPERFINAL cambiaron a la vez el modelo y el corte, así que los +2,45 M del bot no son solo del modelo.</p>
>
> <p align="justify"><b>Lo que me llevo:</b> lo que más movió la ganancia fue <b>qué le pido al modelo que aprenda</b>: primero la clase (BAJA+2 sola) y al final a qué BAJA+2 prestarle atención. Agregar variables en masa y mezclar modelos distintos me dio peor casi siempre.</p>

### 3_grupos_baja2/README.md

> # 3 — Cinco grupos de clientes que se van
>
> **Qué hice:** quería saber si los BAJA+2 se van todos de la misma manera o hay varias formas de irse. Entrené un Random Forest para distinguir BAJA+2 de clientes fieles, armé un perfil de cada BAJA+2 con las hojas en que cae, y sobre esos perfiles hice KMeans con k=5. Salen cinco grupos (C1 a C5) de los 4.067 BAJA+2 de marzo a junio.
>
> El modelo final (paso 4) usa estos grupos **solo para decidir cuánto pesa cada BAJA+2 al entrenar**. No son una variable y no se usan para predecir agosto.
>
> | Archivo | Qué hace |
> |---|---|
> | `eda_clusters_profundo.py` | Random Forest (300 árboles, semilla 214363) + perfil de hojas + KMeans k=5 |
> | `validar_clusters_estabilidad.py` | Escribe `reference_labels.csv` (cliente, grupo) y después comprueba que los cinco grupos reaparecen cambiando semillas, bootstrap de clientes y árboles |
>
> ```bash
> python 3_grupos_baja2/validar_clusters_estabilidad.py \
>   --data $HOME/c1m1femasiva03/datos/competencia_01.parquet --out $HOME/z501
> ```
>
> El script escribe `reference_labels.csv` al principio y después sigue con las pruebas de estabilidad (20 semillas de KMeans, bootstrap, otros bosques), que tardan y no hacen falta para la entrega: se puede cortar una vez que apareció el archivo.
>
> `$HOME/z501/reference_labels.csv` debe tener 4.067 filas con estos tamaños: C1 1.280, C2 1.136, C3 857, C4 579, C5 215. El archivo no está en el repo porque tiene IDs de clientes.
>
> Lo que encontré con estos grupos está en el README principal: SUPERFINAL detectaba casi todos los BAJA+2 de C3 y C4 (98%) y menos de la mitad de los de C2 y C5.

### 2_variables/README.md

> # 2 — Variables
>
> **Qué hice:** a las 152 variables originales les agregué historia (lag, delta y transiciones mes a mes de cada variable) y ratios entre las variables de tarjetas. Son 1.910 variables nuevas; con las originales, **2.062**. A ese conjunto lo llamo **C3**.
>
> Antes probé agregar muchísimas más variables (miles, de varias familias: rankings, estados, transformaciones) y fue peor que no agregar nada. C3 fue la única combinación que mejoró de forma estable en junio: +8,95 M ARS con 5 semillas, y confirmado con 20 semillas (+6,01 M, 15 de 20 a favor).
>
> | Archivo | Qué hace |
> |---|---|
> | `experimentos_20261006_m1_fe_masiva/fe_amplia/generar_fe.py` y `fe_*.py` | Generan las variables por bloques; `catalogo_fuentes.csv` dice de qué variable original sale cada una |
> | `experimentos_20261006_m1_fe_masiva/run_screening.py` | Construye el banco completo de variables (`fe_bank_dev`) y hace la primera comparación |
> | `experimentos_20261006_m1_fe_masiva/run_s3_confirm_c3.py` | Confirma C3 con 20 semillas y deja la lista de las 2.062 variables (`C3_HIST_MAS_TARJETAS/features.json`) |
> | `vendor/comun/config.yaml` | Parámetros base de LightGBM y meses del protocolo |
> | `PAQUETE.json` | Hash de cada archivo; el paso 4 lo usa para comprobar que el código de este paso es el que corrió |
>
> Esta carpeta es el "paquete" que el paso 4 espera en `$HOME/c1m1femasiva03_s3/paquete_c1/`, por eso tiene esa estructura y no se le pueden cambiar los nombres.
>
> ```bash
> mkdir -p $HOME/c1m1femasiva03_s3
> cp -r 2_variables $HOME/c1m1femasiva03_s3/paquete_c1
> D=$HOME/c1m1femasiva03/datos/competencia_01.parquet
> cd $HOME/c1m1femasiva03_s3/paquete_c1/experimentos_20261006_m1_fe_masiva
> python run_screening.py      --data $D --out $HOME/c1m1femasiva03_s3/resultados_s1 --solo-generar-fe
> python run_s3_confirm_c3.py  --data $D --s1-root $HOME/c1m1femasiva03_s3/resultados_s1 --out $HOME/c1m1femasiva03_s3/resultados_s3
> ```
>
> `--solo-generar-fe` construye el banco de variables y termina; sin ese flag además entrena los 15 modelos de la comparación masiva, que no hacen falta para la entrega.
>
> Salidas que usa el paso 4: `resultados_s1/fe_bank_dev/` (banco de variables y `etiquetas.parquet`) y `resultados_s3/confirmacion_c3.json` + `resultados_s3/C3_HIST_MAS_TARJETAS/features.json`.

### 1_dataset/README.md

> # 1 — Dataset con clase
>
> **Qué hice:** del CSV crudo de la cátedra armé la clase `clase_ternaria` (CONTINUA, BAJA+1, BAJA+2) mirando si el cliente aparece uno y dos meses después, y guardé todo en un Parquet para que los pasos siguientes lo lean rápido.
>
> Script: [`preparar_competencia.py`](preparar_competencia.py) (DuckDB). Si no encuentra el CSV, lo descarga de la URL de la competencia.
>
> ```bash
> mkdir -p $HOME/c1m1femasiva03/datos
> cp /RUTA/competencia_01_crudo.csv $HOME/c1m1femasiva03/datos/
> python 1_dataset/preparar_competencia.py --workdir $HOME/c1m1femasiva03/datos
> sha256sum $HOME/c1m1femasiva03/datos/competencia_01.parquet
> ```
>
> Los scripts del paso 4 comprueban que ese Parquet tenga SHA-256
> `59231e670a1342ad6f689ad7edc7ece047fc9f7115c6d7845e6c72fa3bbd95bb` (983.061 filas, 155 columnas) y se detienen si no coincide.

### 5_prediccion_final/README.md

> # 5 — Predicción final
>
> | | |
> |---|---|
> | Archivo enviado | `C1CLAW2C065771C9ENS13500.csv` |
> | Mensaje al bot | `submit C1CLAW2C065771C9ENS13500` |
> | Fecha | 09/10/2026 |
> | Submission ID | `1586-1791569183206183` |
> | Ganancia pública | **101,0900 M ARS** |
> | Filas | 13.500 `numero_de_cliente` de agosto, una columna, sin encabezado, ordenados de menor a mayor |
> | SHA-256 | `a1ced864e5e6de15fbd3c65a12c29506387d1bece5f6a87435b45ff907f549ff` |
>
> Respuesta del bot:
>
> ```
> Submission received: 1 candidate model
> Public gain -> mean: 101.0900, std dev: 0.0000
> Submission ID: 1586-1791569183206183
> This is now your final submission -- your LAST pre-deadline submit always is, with no separate step needed.
> ```
>
> `MANIFIESTO_CLAW2_TRANSCRIPTO.json` es el `MANIFEST.json` que escribió el modelo final al generar ese CSV: identidad de la corrida, los 16 parámetros de LightGBM, rondas, pesos por grupo y el hash. Lo copié del bucket; por eso dice "transcripto".
>
> Para comprobar un CSV regenerado con el paso 4:
>
> ```bash
> python 5_prediccion_final/verificar_csv_final.py /RUTA/C1CLAW2C065771C9ENS13500.csv \
>   --sha256 a1ced864e5e6de15fbd3c65a12c29506387d1bece5f6a87435b45ff907f549ff --n 13500
> ```
>
> Con `--dataset /RUTA/competencia_01_crudo.csv` también verifica que todos los IDs existan en agosto.
>
> El CSV no está en el repo: la cátedra tiene el que se adjuntó al bot, y el pipeline lo regenera.

### 4_modelo/README.md

> # 4 — Hiperparámetros y modelo final
>
> Acá está el entrenamiento, en dos partes que van en orden:
>
> | Carpeta | Qué hice |
> |---|---|
> | [`02_q0_ccajas_na/`](experimentos_20261007_post_c3/02_q0_ccajas_na/) y [`04_b1_variables_rotas/`](experimentos_20261007_post_c3/04_b1_variables_rotas/) | Controles de calidad de datos: reproduzco exacto el modelo C3 y pruebo si marcar como faltante una variable rota en un mes mejora algo. SUPERFINAL los necesita para elegir con qué versión del dataset arranca. |
> | [`05_superfinal100/`](experimentos_20261007_post_c3/05_superfinal100/) | **SUPERFINAL:** una sola corrida con reglas fijadas de antemano que elige representación, pesos por mes, hiperparámetros (**Optuna**) y corte. De acá salen los parámetros del modelo final. |
> | [`13_cluster_aware_reweighting/`](experimentos_20261007_post_c3/13_cluster_aware_reweighting/) | **Modelo final (CLAW2):** mismo modelo que SUPERFINAL, pero repartiendo el peso de los BAJA+2 entre los cinco grupos del paso 3. Escribe el CSV de la entrega. |
>
> Las carpetas conservan sus nombres originales porque los scripts se llaman entre sí por esos nombres (`13_…` importa de `05_…`, y `05_…` ejecuta `04_…`).
>
> ## Dónde espera cada cosa
>
> Los scripts leen y escriben en carpetas fijas de `$HOME`:
>
> ```
> $HOME/
> ├── c1m1femasiva03/datos/competencia_01.parquet          <- paso 1
> ├── c1m1femasiva03_s3/
> │   ├── paquete_c1/                                      <- paso 2 (copia de 2_variables/)
> │   ├── resultados_s1/fe_bank_dev/                       <- paso 2
> │   └── resultados_s3/                                   <- paso 2
> ├── z501/reference_labels.csv                            <- paso 3
> ├── c1q0ccajas06/           c1b1rotas01/                 <- salidas de Q0 y B1
> ├── c1superfinal100v2/                                   <- salida de SUPERFINAL
> └── c1clusteraware01/stage4_august/delivery/             <- CSV final
> ```
>
> Máquina: Linux con 56 GB de RAM y 6 hilos.
>
> En la corrida original cada etapa se respaldaba a un bucket de Cloud Storage con `gcloud`. Para publicar, el nombre del bucket se reemplazó por un placeholder y esas copias se saltean (función `_gcs` al inicio de cada script); es el único cambio respecto del código que corrió y no toca ningún cálculo. Si se quiere respaldar, basta poner un bucket propio en la constante `REMOTE` de cada script.
>
> ## Comandos
>
> ```bash
> R=4_modelo/experimentos_20261007_post_c3
>
> # Controles de calidad (Q0 reproduce C3 con 20 semillas; B1 lo lanza SUPERFINAL solo)
> python $R/02_q0_ccajas_na/run_q0.py --preflight
> python $R/02_q0_ccajas_na/run_q0.py --prepare
> python $R/02_q0_ccajas_na/run_q0.py --canary
> python $R/02_q0_ccajas_na/run_q0.py --execute
>
> # SUPERFINAL: calidad -> representación -> pesos por mes -> Optuna -> 20 semillas -> producción
> python $R/05_superfinal100/run_superfinal100_v2_safe.py --home $HOME --all
> python $R/05_superfinal100/auditar_superfinal100_v2.py --home $HOME     # obligatorio: escribe AUDITORIA_FINAL.json, que el modelo final exige
>
> # Modelo final (CLAW2_REPLICA=1: acepta la corrida de SUPERFINAL recién hecha; ver nota)
> export CLAW2_REPLICA=1
> python $R/13_cluster_aware_reweighting/run_cluster_aware.py \
>   --home $HOME --labels-cluster $HOME/z501/reference_labels.csv --phase all
> python $R/13_cluster_aware_reweighting/audit_cluster_aware.py --home $HOME   # debe decir AUDIT_OK
> ```
>
> Cada script primero verifica hashes, identidades y conteos de la etapa anterior y se detiene si algo no coincide. Nada hace submit automático.
>
> **Nota sobre `CLAW2_REPLICA=1`.** Cada corrida de SUPERFINAL lleva una huella (un hash que incluye, entre otras cosas, el tiempo que tardó en generar las variables), y el modelo final tiene grabada en `plan.json` la huella de la corrida original. Una corrida nueva de SUPERFINAL tiene otra huella, así que sin esa variable de entorno el modelo final se detiene en su preflight. Con `CLAW2_REPLICA=1` toma la huella de la corrida presente en `$HOME`, que igual debe haber pasado su auditoría. El resto de los controles no cambia. El archivo generado tendrá otro prefijo (sale de esa huella), pero el contenido se compara con el verificador del paso 5.
>
> Tests sin datos (corren en GitHub Actions):
>
> ```bash
> (cd $R/13_cluster_aware_reweighting && python test_cluster_aware.py)
> (cd $R/05_superfinal100 && python test_superfinal100_v2.py)
> ```

