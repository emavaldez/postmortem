# AgustinBerna — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: AgustinBerna
- Repositorio: https://github.com/AgustinBerna/dmeyf2026
- Link posteado: https://github.com/AgustinBerna/dmeyf2026/tree/main/Competencia_1
- Commit: 860279c74160cb99538683d2ba1d4d5755d8515e
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/agustinberna/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/agustinberna.json

## Resumen

La entrega es la carpeta Competencia_1 de un fork del repositorio de la materia: un README y tres scripts de Python (correr.py, pipeline.py y basal_features.py). correr.py contiene la configuración y lanza cuatro etapas. La preparación lee el CSV crudo con DuckDB, calcula la clase ternaria y un target binario (BAJA+1 o BAJA+2 contra CONTINUA), pasa a NA valores de algunas variables en meses puntuales, ajusta 62 columnas de montos por IPC, agrega tres flags de aguinaldo, un signed rank para las variables con PSI mayo-junio mayor a 0,25 y lags y deltas de 1 y 2 meses. La búsqueda corre 60 trials de Optuna (TPE) con LightGBM sobre tres folds temporales (validación en 202105 y 202106), con submuestreo del 50% de CONTINUA y una ganancia ponderada 0,50/0,25/0,25 como objetivo. Se conservan las 10 configuraciones de mayor ganancia, se promedian sus predicciones de validación y se elige un único N en la grilla de 7.000 a 15.000. El entrenamiento final usa 202103-202106 con 20 semillas por configuración (200 modelos), promedia las probabilidades sobre 202108 y escribe los N clientes de mayor promedio.

**Qué entrega.** Un CSV sin encabezado, envio_agosto_top<N>.csv, con el numero_de_cliente de los N clientes de 202108 con mayor probabilidad promedio de los 200 modelos; N se lee de cut.json (10.500 según el README). El código escribe además scores_agosto_ensemble.csv.gz con la probabilidad promedio de todos los clientes de 202108. Ninguno de los dos archivos está incluido en el repositorio.

**Cómo se ejecuta.** Según el README: colocar competencia_01_crudo.csv junto a los .py y ejecutar `python -u correr.py`; los resultados quedan en runs/. El docstring de correr.py agrega un ejemplo con argumentos: `python correr.py --raw-path /ruta/competencia_01_crudo.csv --work-dir /ruta/salida --threads 8`. correr.py acepta además --duckdb-memory-gb y --stage (all, prepare, search, select o score).

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (columna target_baja12): 1 = BAJA+1 o BAJA+2, 0 = CONTINUA. La clase ternaria se calcula dentro del pipeline a partir del CSV crudo, según la presencia del cliente en los dos meses siguientes; los meses que no tienen dos meses posteriores en el archivo quedan sin clase. En la ganancia de validación sólo BAJA+2 suma.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202105, 202106
- **Mes que predice:** 202108
- **Submuestreo:** Conserva todas las filas con target 1 y el 50% de las filas CONTINUA (undersampling_continua = 0.5), elegidas por un hash determinístico de cliente y mes combinado con sampling_seed = 700087. Se aplica al entrenamiento de cada fold y al entrenamiento final; los meses de validación y 202108 se usan completos.
- **Calidad de datos:** ccajas_depositos de 202105 pasa completa a NA; los ceros de Visa_Finiciomora y Master_Finiciomora pasan a NA en 202105 y 202108; los ceros de Master_fultimo_cierre y Visa_fultimo_cierre pasan a NA en 202106; los valores de internet distintos de 0 y 1 pasan a NA; los infinitos pasan a NA. Cada corrección se registra con la cantidad de filas afectadas en dq_corrections.csv. Antes se verifica que no haya pares cliente/mes repetidos y que estén los meses requeridos.
- **Drifting:** Dos tratamientos. (1) Ajuste por IPC: 62 columnas de montos se multiplican por ipc[202108]/ipc[mes], con el índice de cada mes escrito en CONFIG (435,8657 en 202103 a 510,3942 en 202108). (2) Signed rank: después de las correcciones y del ajuste por IPC se calcula el PSI de cada variable original no categórica entre 202105 y 202106 (10 bins por cuantiles, sobre valores no nulos); a las de PSI mayor a 0,25, hasta 15, se les agrega en cada mes una columna srank_ con 0 para el cero, el percentil entre los positivos y el percentil con signo menos entre los negativos. La columna original se conserva. Según el README las variables con signed rank son Master_mlimitecompra y Master_Finiciomora.
- **Variables dentro del mes:** No se observa en el código la creación de sumas, cocientes o combinaciones dentro del mes. Dentro de cada mes sólo se agregan las columnas srank_ (ver drifting). Según el README se probaron combinaciones de variables intra-mes, que no forman parte de los archivos entregados.
- **Variables históricas:** Para cada columna del mes (originales, flags de aguinaldo y srank_) se generan lag1, lag2, delta1 y delta2 (valor actual menos el de 1 y de 2 meses atrás), uniendo cada mes con los dos anteriores por cliente dentro de los meses 202103-202108. Tres flags de aguinaldo comparan 202106 con 202105 sobre valores sin ajustar por IPC: mpayroll_dup_junio (mpayroll de junio mayor o igual a 1,5 veces el de mayo), cpayroll_dup_junio (contador de acreditaciones mayor o igual a 2 veces el de mayo) y cobra_aguinaldo (1 si alguno de los dos vale 1); en los demás meses valen 0. Según el README son 785 variables en total.
- **Selección de variables:** No se observa en el código una selección de variables para el modelo: entran todas las columnas generadas. El código sólo verifica que el total de columnas no supere max_columns = 1000. El PSI entre 202105 y 202106 se usa para elegir a qué variables se les agrega signed rank, no para quitar variables.
- **Optimización de hiperparámetros:** Optuna con sampler TPE (semilla 700087), 60 trials secuenciales, estudio guardado en SQLite. Espacio: num_iterations 300-2.000 (paso 100), num_leaves 20-256, min_sum_hessian_in_leaf 0,01-20 (log), learning_rate 0,01-0,10 (log), feature_fraction 0,10-1,00 y min_data_in_leaf 100-3.000 (log). Cada trial entrena los tres folds con early stopping de 100 rondas sobre la ganancia y devuelve el máximo de la curva de ganancia ponderada 0,50/0,25/0,25 con un N común en la grilla de 7.000 a 15.000 cada 500.
- **Hiperparámetros finales:** Las 10 combinaciones distintas de mayor ganancia ponderada entre los trials completos; sus valores se generan en la corrida (expanding_selected.json, frozen.json) y no están escritos en el repositorio. La cantidad de árboles de cada una es la mediana redondeada de las iteraciones elegidas por early stopping en sus tres folds. Fijos en el código: objective binary, max_bin 31, bagging_fraction 0,7, bagging_freq 1, feature_fraction_bynode 1,0, feature_pre_filter False, force_col_wise True y deterministic True. Master_status y Visa_status se declaran categóricas.
- **Semillas:** 20 semillas finales consecutivas, 700087 a 700106, escritas en CONFIG; cada una fija seed, bagging_seed y feature_fraction_seed. En la búsqueda cada fold usa 700087 más el índice del fold. La semilla 700087 se usa también para el sampler TPE, para data_random_seed y para el hash del submuestreo.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio uniforme de las probabilidades de 200 modelos LightGBM sobre 202108: 10 configuraciones de hiperparámetros por 20 semillas cada una. Para elegir el corte se promedian, dentro de cada fold, las predicciones de validación de las 10 configuraciones (un modelo por configuración y fold).
- **Corte:** Un único N: el de mayor ganancia en la curva ponderada 0,50/0,25/0,25 del promedio de las 10 configuraciones en los tres folds de validación, sobre la grilla de 7.000 a 15.000 cada 500. El N se guarda en cut.json y frozen.json antes del entrenamiento final, que verifica el SHA-256 de cut.json y features.json. Según el README el corte es 10.500. El envío toma los N clientes de mayor probabilidad promedio; los empates se ordenan por numero_de_cliente ascendente.
- **Validación:** Tres folds temporales definidos en CONFIG: entrena con 202103 y valida en 202105; entrena con 202103-202104 y valida en 202106; entrena con 202103-202105 y valida en 202106. Los dos primeros dejan un mes sin usar entre entrenamiento y validación. La métrica es la ganancia por TopN con los valores de CONFIG (gain = 1.072.500 por cada BAJA+2 y cost = 27.500 por cada otro cliente enviado); se usa para el early stopping y como objetivo de Optuna con pesos 0,50/0,25/0,25 por fold. Por fold también se registran AUC y average precision. El código exige que la validación sea al menos 1 mes posterior al último mes de entrenamiento (min_train_valid_gap = 1).
- **Salidas:** En la carpeta de trabajo (por defecto runs/tres_folds_us50_aguinaldo15_001): envio_agosto_top<N>.csv (ids sin encabezado), scores_agosto_ensemble.csv.gz (probabilidad promedio de todos los clientes de 202108), expanding_trials.csv, expanding_selected.json, ensemble_validation_curve.csv, cut.json, frozen.json, models/ (un modelo en texto por configuración y semilla), scores/ (predicciones individuales en .npz), base_AAAAMM.parquet y month_AAAAMM.parquet, features.json, dq_corrections.csv, drift_rank_selection.csv, aguinaldo_report.json, sampling_*.json, config.json, manifest.json, run.log y FINALIZADO.json. Ninguna de estas salidas está incluida en el repositorio.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Deflación por IPC, dólar o UVA (`drifting.deflacion`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: sí
- Entorno declarado: El README lista versiones de librerías: duckdb 1.5.5, lightgbm 4.7.0, optuna 3.6.1, numpy 2.4.4, pandas 3.0.1, pyarrow 24.0.0, psutil 7.2.2 y scikit-learn 1.9.1. No se declara máquina ni sistema operativo. El código guarda en manifest.json las versiones de Python, lightgbm, optuna, duckdb, pandas y numpy de la corrida y usa por defecto 8 hilos y 4 GB de memoria para DuckDB. En la raíz del repositorio, fuera del link posteado, hay un pyproject.toml con requires-python >= 3.11 y un .python-version con 3.11.

## Pasos del camino de la entrega

1. **Configuración y punto de entrada.** correr.py define el diccionario CONFIG (meses, IPC, columnas a ajustar, rangos de búsqueda, folds y semillas) y los argumentos de línea de comandos; escribe config.json en la carpeta de trabajo y llama a pipeline.run con la etapa pedida (por defecto las cuatro: prepare, search, select y score). (`Competencia_1/correr.py` líneas 11–11; `Competencia_1/correr.py` líneas 14–32)
2. **Validaciones y control de la corrida.** pipeline.run valida la configuración, toma un lock sobre la carpeta de trabajo, guarda en manifest.json la configuración, el SHA-256 del CSV y del código y las versiones de las librerías, y ejecuta las etapas en orden. Si la carpeta ya tiene un manifest distinto, corta. (`Competencia_1/pipeline.py` líneas 439–497)
3. **Lectura del CSV y cálculo de la clase.** DuckDB carga competencia_01_crudo.csv completo. La clase ternaria se calcula uniendo cada cliente con los dos meses siguientes, y el target binario vale 1 para BAJA+1 o BAJA+2 y 0 para CONTINUA; los meses sin dos meses posteriores en el archivo quedan sin clase. (`Competencia_1/basal_features.py` líneas 42–69)
4. **Correcciones de calidad por mes.** ccajas_depositos de 202105 pasa a NA; los ceros de Visa_Finiciomora y Master_Finiciomora pasan a NA en 202105 y 202108 y los de Master_fultimo_cierre y Visa_fultimo_cierre en 202106; los valores de internet fuera de 0 y 1 pasan a NA. Cada corrección queda registrada en dq_corrections.csv. (`Competencia_1/pipeline.py` líneas 93–116; `Competencia_1/basal_features.py` líneas 70–89)
5. **Ajuste de montos por IPC.** Las 62 columnas de inflation_columns se multiplican por el cociente entre el IPC de 202108 y el IPC del mes de cada fila, con los índices escritos en CONFIG. (`Competencia_1/pipeline.py` líneas 117–127; `Competencia_1/correr.py` líneas 11–11)
6. **Flags de aguinaldo.** En 202106 se comparan mpayroll y el contador de acreditaciones con los valores de 202105 sin ajustar por IPC: se marca cuando el monto es al menos 1,5 veces el de mayo o el contador al menos 2 veces. Se agregan tres columnas (mpayroll_dup_junio, cpayroll_dup_junio y cobra_aguinaldo) que valen 0 en los demás meses. (`Competencia_1/basal_features.py` líneas 20–35; `Competencia_1/basal_features.py` líneas 76–81)
7. **PSI mayo-junio y signed rank.** Se calcula el PSI de cada variable original no categórica entre 202105 y 202106. A las que superan 0,25, hasta 15, se les agrega en cada mes una columna srank_ con el percentil con signo y el cero fijo. (`Competencia_1/pipeline.py` líneas 71–90; `Competencia_1/basal_features.py` líneas 10–17; `Competencia_1/basal_features.py` líneas 90–102; `Competencia_1/basal_features.py` líneas 107–117)
8. **Lags y deltas de 1 y 2 meses.** Para cada columna del mes se generan lag1, lag2, delta1 y delta2 con dos LEFT JOIN por cliente contra los meses anteriores, y se exporta un Parquet por mes. El código corta si se superan 1.000 columnas; según el README quedan 785 variables. (`Competencia_1/basal_features.py` líneas 118–146; `Competencia_1/Readme.md` líneas 32–32)
9. **Submuestreo de CONTINUA.** En cada conjunto de entrenamiento se conservan todas las filas con target 1 y el 50% de las CONTINUA, elegidas por un hash determinístico de cliente y mes con la semilla 700087. (`Competencia_1/pipeline.py` líneas 168–179)
10. **Folds temporales.** CONFIG define tres folds: entrenar con 202103 y validar en 202105; entrenar con 202103-202104 y validar en 202106; entrenar con 202103-202105 y validar en 202106. Para cada fold se construyen y guardan los Dataset binarios de LightGBM, con el mes de validación completo. (`Competencia_1/correr.py` líneas 11–11; `Competencia_1/pipeline.py` líneas 202–228)
11. **Métrica de ganancia por TopN.** La curva de ganancia ordena por probabilidad, suma 1.072.500 por cada BAJA+2 y resta 27.500 por cada otro cliente, y se evalúa en N = 7.000 a 15.000 cada 500. Las curvas de los tres folds se combinan con pesos 0,50/0,25/0,25 y se toma el máximo con un N común. (`Competencia_1/pipeline.py` líneas 52–68; `Competencia_1/pipeline.py` líneas 182–186; `Competencia_1/pipeline.py` líneas 231–238)
12. **Búsqueda de hiperparámetros.** 60 trials secuenciales de Optuna con sampler TPE (semilla 700087) sobre seis hiperparámetros de LightGBM. Cada trial entrena los tres folds con early stopping de 100 rondas sobre la ganancia y devuelve la ganancia ponderada. (`Competencia_1/pipeline.py` líneas 241–293; `Competencia_1/Readme.md` líneas 39–52)
13. **Selección de 10 configuraciones.** Se ordenan los trials por ganancia ponderada y se conservan las 10 combinaciones distintas de mayor valor. La cantidad de árboles final de cada una es la mediana redondeada de las iteraciones elegidas por early stopping en sus tres folds. (`Competencia_1/pipeline.py` líneas 282–282; `Competencia_1/pipeline.py` líneas 294–306)
14. **Elección del corte N.** Se obtienen las predicciones de validación de las 10 configuraciones, se promedian dentro de cada fold, se calcula la curva ponderada del promedio y se toma el N de mayor ganancia. El N y las configuraciones se guardan en cut.json y frozen.json; según el README el corte es 10.500. (`Competencia_1/pipeline.py` líneas 314–357; `Competencia_1/Readme.md` líneas 15–15)
15. **Entrenamiento final de 200 modelos.** Con 202103-202106 submuestreado se entrena cada una de las 10 configuraciones con las 20 semillas 700087 a 700106 y se predice 202108 por lotes; se guarda un modelo y un archivo de scores por combinación. (`Competencia_1/pipeline.py` líneas 360–415)
16. **Promedio y archivo de envío.** Se promedian las probabilidades de los 200 modelos, se ordenan los clientes de 202108 por promedio descendente y se escriben los N primeros ids en envio_agosto_top<N>.csv, sin encabezado, junto con scores_agosto_ensemble.csv.gz y FINALIZADO.json. (`Competencia_1/pipeline.py` líneas 421–436)

## Archivos

- `Competencia_1/correr.py` · principal · Python · 35 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinberna/Competencia_1/correr.py.txt) — Punto de entrada de la entrega: contiene el diccionario CONFIG con todos los parámetros de la corrida, lee los argumentos de línea de comandos, escribe config.json en la carpeta de trabajo y llama a pipeline.run.
- `Competencia_1/Readme.md` · explicacion · Markdown · 110 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinberna/Competencia_1/Readme.md.txt) — Texto de presentación de la entrega: tabla resumen del método, decisiones (calidad, inflación y préstamos, aguinaldo, variables agregadas, folds, selección y corte, semillas y ensamble), lista de archivos compartidos, versiones de librerías, instrucciones para reproducir y tabla de salidas.
- `Competencia_1/pipeline.py` · principal · Python · 525 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinberna/Competencia_1/pipeline.py.txt) — Módulo con las etapas del proceso: correcciones de calidad y ajuste por IPC por mes, submuestreo, curva de ganancia, búsqueda de hiperparámetros con Optuna sobre tres folds, selección de 10 configuraciones y del corte N, entrenamiento final de 200 modelos LightGBM y escritura del envío. También controla la corrida (validaciones, lock, manifest y reanudación).
- `Competencia_1/basal_features.py` · principal · Python · 148 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinberna/Competencia_1/basal_features.py.txt) — Etapa de preparación de datos: carga el CSV en DuckDB, calcula la clase ternaria y el target binario, aplica las correcciones por mes, agrega los flags de aguinaldo y los signed ranks de las variables elegidas por PSI, genera lags y deltas de 1 y 2 meses y exporta un Parquet por mes.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### Competencia_1/correr.py

Punto de entrada de la entrega: contiene el diccionario CONFIG con todos los parámetros de la corrida, lee los argumentos de línea de comandos, escribe config.json en la carpeta de trabajo y llama a pipeline.run.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–9] Docstring con la descripción de la corrida («Tres folds US50, prestamos
#   conservados, umbrales monto 1.5 y contador 2»), un ejemplo de invocación y la lista de dependencias. Importa
#   argparse, json, os, Path y el módulo pipeline.
"""Tres folds US50, prestamos conservados, umbrales monto 1.5 y contador 2.
Ejemplo: python correr.py --raw-path /ruta/competencia_01_crudo.csv --work-dir /ruta/salida --threads 8
Dependencias: duckdb, lightgbm, optuna, numpy, pandas, pyarrow, psutil, scikit-learn.
"""
import argparse
import json
import os
from pathlib import Path
import pipeline

# [Anotación · líneas 11–11] Diccionario CONFIG escrito en una sola línea de 3.055 caracteres (la copia
#   mostrada la corta; los valores que siguen se leyeron del archivo original). Define: meses 202103-202108, mes
#   a predecir 202108, meses del entrenamiento final 202103-202106, índice IPC por mes, 62 columnas de montos a
#   ajustar, semilla 700087, Master_status y Visa_status como categóricas, gain 1.072.500 y cost 27.500, pesos
#   por fold 0,5/0,25/0,25, grilla de N de 7.000 a 15.000 cada 500, early stopping 100, rangos de búsqueda
#   (árboles 300-2.000, hojas 20-256, hessian 0,01-20, learning_rate 0,01-0,1, feature_fraction 0,1-1,0,
#   min_data_in_leaf 100-3.000), 60 trials, top_k 10, submuestreo de CONTINUA 0,5, 20 semillas finales
#   700087-700106, umbral de PSI 0,25 con hasta 15 variables y umbrales de aguinaldo 1,5 y 2,0. La estrategia
#   «expanding» tiene objetivo «common» y tres folds: 202103 valida en 202105, 202103-202104 valida en 202106 y
#   202103-202105 valida en 202106.
CONFIG = {'raw_path': 'competencia_01_crudo.csv', 'months': [202103, 202104, 202105, 202106, 202107, 202108], 'score_month': 202108, 'final_train_months': [202103, 202104, 202105, 202106], 'threads': 8, 'max_columns': 1000, 'ipc': {'202103': 435.8657, '202104': 453.6503, '202105': 468.725, '202106': 483.6049, '202107': 498.0987, '202108': 510.3942}, 'inflation_columns': ['mrentabilidad', 'mrentabilidad_annual', 'mcomisiones', 'mactivos_margen', 'mpasivos_margen', 'mcuenta_corriente_adicional', 'mcuenta_corriente', 'mcaja_ahorro', 'mcaja_ahorro_adicional', 'mcuentas_saldo', 'mautoservicio', 'mtarjeta_visa_consumo', 'mtarjeta_master_consumo', 'mprestamos_personales', 'mprestamos_prendarios', 'mprestamos_hipotecarios', 'mplazo_fijo_pesos', 'minversion1_pesos', 'minversion2', 'mpayroll', 'mpayroll2', 'mcuenta_debitos_automaticos', 'mttarjeta_visa_debitos_automaticos', 'mttarjeta_master_debitos_automaticos', 'mpagodeservicios', 'mpagomiscuentas', 'mcajeros_propios_descuentos', 'mtarjeta_visa_descuentos', 'mtarjeta_master_descuentos', 'mcomisiones_mantenimiento', 'mcomisiones_otras', 'mforex_buy', 'mforex_sell', 'mtransferencias_recibidas', 'mtransferencias_emitidas', 'mextraccion_autoservicio', 'mcheques_depositados', 'mcheques_emitidos', 'mcheques_depositados_rechazados', 'mcheques_emitidos_rechazados', 'matm', 'matm_other', 'Master_mfinanciacion_limite', 'Master_msaldototal', 'Master_msaldopesos', 'Master_mconsumospesos', 'Master_mlimitecompra', 'Master_madelantopesos', 'Master_mpagado', 'Master_mpagospesos', 'Master_mconsumototal', 'Master_mpagominimo', 'Visa_mfinanciacion_limite', 'Visa_msaldototal', 'Visa_msaldopesos', 'Visa_mconsumospesos', 'Visa_mlimitecompra', 'Visa_madelantopesos', 'Visa_mpagado', 'Visa_mpagospesos', 'Visa_mconsumototal', 'Visa_mpagominimo'], 'seed': 700087, 'learning_rate': 0.005, 'min_data_in_leaf': 300, 'feature_fraction': 0.3, 'bagging_fraction': 0.7, 'categorical_columns': ['Master_status', 'Visa_status'], 'score_batch_size': 32768, 'gain': 1072500, 'cost': 27500, 'month_weights': [0.5, 0.25, 0.25], 'n_min': 7000, 'n_max': 15000, 'n_step': 500, 'n_manual': None, 'save_models': True, 'early_stopping': 100, 'trees_min': 300, 'max_trees': 2000, 'leaves_range': [20, 256], 'hessian_range': [0.01, 20], 'work_dir': 'runs/tres_folds_us50_aguinaldo15_001', 'duckdb_memory_gb': 4, 'nominal_limits': [], 'undersampling_continua': 0.5, 'sampling_seed': 700087, 'final_seeds': [700087, 700088, 700089, 700090, 700091, 700092, 700093, 700094, 700095, 700096, 700097, 700098, 700099, 700100, 700101, 700102, 700103, 700104, 700105, 700106], 'trials': 60, 'top_k': 10, 'learning_rate_range': [0.01, 0.1], 'feature_fraction_range': [0.1, 1.0], 'min_data_range': [100, 3000], 'drift_threshold': 0.25, 'drift_rank_top_k': 15, 'aguinaldo_ratio': 1.5, 'aguinaldo_count_ratio': 2.0, 'strategies': {'expanding': {'objective': 'common', 'folds': [{'train': [202103], 'valid': 202105}, {'train': [202103, 202104], 'valid': 202106}, {'train': [202103, 202104, 202105], 'valid': 202106}]}}, 'min_train_valid_gap': 1}


# [Anotación · líneas 14–22] Define los argumentos de línea de comandos: --raw-path (por defecto
#   competencia_01_crudo.csv junto al script), --work-dir (por defecto runs/tres_folds_us50_aguinaldo15_001),
#   --threads (8), --duckdb-memory-gb (4) y --stage (all, prepare, search, select o score; por defecto all).
#   Corta con error si los hilos o la memoria son menores a 1.
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-path',default=str(Path(__file__).with_name('competencia_01_crudo.csv')))
    parser.add_argument('--work-dir',default='runs/tres_folds_us50_aguinaldo15_001')
    parser.add_argument('--threads',type=int,default=8)
    parser.add_argument('--duckdb-memory-gb',type=int,default=4)
    parser.add_argument('--stage',choices=['all','prepare','search','select','score'],default='all')
    args=parser.parse_args()
    if args.threads<1 or args.duckdb_memory_gb<1:parser.error('CPU y memoria deben ser positivos')
# [Anotación · líneas 23–32] Resuelve la ruta del CSV y corta si no existe; crea la carpeta de trabajo y arma
#   la configuración efectiva reemplazando en CONFIG la ruta del dataset, la carpeta, los hilos y la memoria.
#   Escribe config.json en la carpeta de trabajo (corta si ya existe uno distinto) y llama a pipeline.run con la
#   etapa pedida, en modo reanudación si ya hay un manifest.json.
    raw=Path(args.raw_path).expanduser().resolve()
    if not raw.is_file():parser.error('No existe el dataset: '+str(raw))
    root=Path(args.work_dir).expanduser().resolve()
    root.mkdir(parents=True,exist_ok=True)
    cfg=dict(CONFIG,raw_path=str(raw),work_dir=str(root),threads=args.threads,duckdb_memory_gb=args.duckdb_memory_gb)
    config=root/'config.json'
    if config.exists() and json.loads(config.read_text())!=cfg:
        parser.error('Salida existente con otra configuracion; elegir otro work-dir')
    config.write_text(json.dumps(cfg,indent=2)+'\n')
    pipeline.run(config,args.stage,resume=(root/'manifest.json').exists())


# [Anotación · líneas 35–35] Ejecuta main cuando el archivo se corre como script.
if __name__=='__main__':main()
```

### Competencia_1/pipeline.py

Módulo con las etapas del proceso: correcciones de calidad y ajuste por IPC por mes, submuestreo, curva de ganancia, búsqueda de hiperparámetros con Optuna sobre tres folds, selección de 10 configuraciones y del corte N, entrenamiento final de 200 modelos LightGBM y escritura del envío. También controla la corrida (validaciones, lock, manifest y reanudación).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–26] Docstring del módulo e importaciones (duckdb, lightgbm, numpy, optuna, pandas,
#   psutil y las métricas AUC y average precision de scikit-learn). Define los nombres de las columnas clave
#   (numero_de_cliente, foto_mes, clase_ternaria, target_baja12), el conjunto EXCLUDED de columnas que no son
#   predictores y el logger.
"""Churn: FE persistente, dos estudios temporales y un único ranking de agosto."""
from __future__ import annotations
import argparse
import gc
import hashlib
import json
import logging
import os
from pathlib import Path
import pickle
import platform
import signal
import time
import warnings
import duckdb
import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import psutil
from sklearn.metrics import roc_auc_score, average_precision_score


ID, MES, CLASE, TARGET = 'numero_de_cliente', 'foto_mes', 'clase_ternaria', 'target_baja12'
EXCLUDED = {ID, MES, CLASE, TARGET, '__month'}
LOG = logging.getLogger('dual')


# [Anotación · líneas 29–49] Funciones auxiliares: q pone un identificador entre comillas dobles para SQL;
#   digest calcula el SHA-256 de un archivo leyéndolo en bloques de 8 MB; write_json escribe un JSON en un
#   archivo temporal y lo renombra; month_index convierte AAAAMM en un número de mes consecutivo (año por 12 más
#   mes).
def q(name):
    return '"'+name.replace('"', '""')+'"'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8*1024**2), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    temp.replace(path)


def month_index(m):
    return int(m)//100*12+int(m)%100


# [Anotación · líneas 52–68] gain_curve calcula la ganancia acumulada en cada corte de una lista de TopN.
#   Ordena los clientes por score descendente, desempatando por numero_de_cliente ascendente (trabaja sólo con
#   los candidatos al corte más grande), asigna cfg['gain'] a cada BAJA+2 y -cfg['cost'] al resto, acumula y
#   devuelve el valor en cada N. Corta con error si el mes tiene menos filas que el N máximo.
def gain_curve(scores, ids, labels, cuts, cfg):
    cuts = np.asarray(cuts, dtype=int)
    if len(scores) < cuts.max():
        raise ValueError('El TopN excede la población mensual')
    scores=np.asarray(scores);ids=np.asarray(ids)
    top=int(cuts.max())
    if top<len(scores):
        boundary=np.partition(scores,len(scores)-top)[len(scores)-top]
        higher=np.flatnonzero(scores>boundary)
        tied=np.flatnonzero(scores==boundary)
        tied=tied[np.argsort(ids[tied],kind='stable')[:top-len(higher)]]
        candidate=np.r_[higher,tied]
        order=candidate[np.lexsort((ids[candidate],-scores[candidate]))]
    else:
        order=np.lexsort((ids,-scores))
    rewards = np.where(np.asarray(labels)[order] == 'BAJA+2', cfg['gain'], -cfg['cost'])
    return np.cumsum(rewards, dtype=np.int64)[cuts-1].astype(float)


# [Anotación · líneas 71–90] psi calcula el Population Stability Index entre una muestra de referencia y una
#   actual. Usa 10 bins por cuantiles de la referencia con extremos abiertos y un bin aparte para los valores no
#   finitos; si la referencia tiene un solo valor usa los bins menor, igual, mayor y faltante. Suma 0,5 a cada
#   conteo antes de calcular las proporciones.
def psi(reference, current, bins=10):
    a, b = np.asarray(reference, float), np.asarray(current, float)
    valid = a[np.isfinite(a)]
    # Missing es un bin explícito; referencia constante tiene bins propios.
    if len(np.unique(valid)) <= 1:
        if len(valid):
            v = valid[0]
            def count(x):
                return np.array([np.sum(x < v), np.sum(x == v), np.sum(x > v), np.sum(~np.isfinite(x))], float)
        else:
            def count(x):
                return np.array([np.isfinite(x).sum(), (~np.isfinite(x)).sum()], float)
    else:
        edges = np.unique(np.quantile(valid, np.linspace(0, 1, bins+1)))
        edges[0], edges[-1] = -np.inf, np.inf
        def count(x):
            return np.append(np.histogram(x[np.isfinite(x)], edges)[0], np.sum(~np.isfinite(x))).astype(float)
    ca, cb = count(a)+0.5, count(b)+0.5
    pa, pb = ca/ca.sum(), cb/cb.sum()
    return float(np.sum((pb-pa)*np.log(pb/pa)))


# [Anotación · líneas 93–116] quality_month aplica las correcciones de calidad a la tabla de un mes: convierte
#   los predictores numéricos a float32 y pasa infinitos a NA; pasa a NA la columna completa de cada regla
#   recibida para ese mes; pasa a NA los ceros de Visa_Finiciomora y Master_Finiciomora en 202105 y 202108 y los
#   de Master_fultimo_cierre y Visa_fultimo_cierre en 202106; y pasa a NA los valores de internet distintos de 0
#   y 1. Registra cada acción con la cantidad de filas afectadas.
def quality_month(df, cfg, rules):
    month = int(df[MES].iloc[0])
    records = []
    zeros = {202105: ['Visa_Finiciomora', 'Master_Finiciomora'],
             202106: ['Master_fultimo_cierre', 'Visa_fultimo_cierre'],
             202108: ['Visa_Finiciomora', 'Master_Finiciomora']}
    for c in df.select_dtypes(include=np.number):
        if c not in EXCLUDED:
            df[c] = df[c].astype('float32').replace([np.inf, -np.inf], np.nan)
    df = df.copy()
    for c, months in rules.items():
        if month in months and c in df:
            records.append(dict(month=month, column=c, action='todo_mes_NA', affected=int(df[c].notna().sum())))
            df[c] = np.nan
    for c in zeros.get(month, []):
        if c not in df:
            raise ValueError('Falta columna de calidad: '+c)
        n = int(df[c].eq(0).sum())
        df.loc[df[c].eq(0), c] = np.nan
        records.append(dict(month=month, column=c, action='ceros_NA', affected=n))
    if 'internet' in df:
        invalid = df.internet.notna() & ~df.internet.isin([0, 1])
        records.append(dict(month=month, column='internet', action='dominio_0_1', affected=int(invalid.sum())))
        df.loc[invalid, 'internet'] = np.nan
# [Anotación · líneas 117–127] Ajuste por IPC: calcula el factor como el IPC del mes a predecir dividido por
#   el IPC del mes de la tabla y multiplica por él cada columna de inflation_columns presente. Las columnas
#   listadas en nominal_limits (lista vacía en CONFIG) generarían una columna nueva con sufijo _real en lugar de
#   reemplazarse. Devuelve la tabla y el registro de correcciones.
    factor = cfg['ipc'][str(cfg['score_month'])]/cfg['ipc'][str(month)]
    real_limits = {}
    for c in cfg['inflation_columns']:
        if c in df:
            if c in cfg['nominal_limits']:
                real_limits[c+'_real'] = (df[c]*factor).astype('float32')
            else:
                df[c] = (df[c]*factor).astype('float32')
    if real_limits:
        df = pd.concat([df,pd.DataFrame(real_limits,index=df.index)],axis=1)
    return df, records


# [Anotación · líneas 130–140] prepare delega la etapa de preparación en basal_features.prepare_basal.
#   parquet_path devuelve la ruta month_AAAAMM.parquet de un mes y load_months concatena las columnas pedidas de
#   varios meses.
def prepare(cfg,root):
    from basal_features import prepare_basal
    prepare_basal(cfg,root)


def parquet_path(root,month):
    return root/f'month_{month}.parquet'


def load_months(root, months, columns):
    return pd.concat([pd.read_parquet(parquet_path(root,m), columns=columns) for m in months], ignore_index=True)


# [Anotación · líneas 143–165] matrix_month convierte el Parquet de un mes en una matriz float32 guardada en
#   disco (datasets/matrix_AAAAMM.npy), escribiéndola por lotes; si el archivo ya existe lo reutiliza. Devuelve
#   la matriz abierta como memmap de sólo lectura y verifica que su cantidad de columnas coincida con la lista
#   de features.
def matrix_month(root, month, features, batch_size):
    """Memmap en disco: decodifica Parquet una vez, no en cada trial/modelo."""
    import pyarrow.parquet as pq
    folder=root/'datasets'
    folder.mkdir(exist_ok=True)
    path=folder/f'matrix_{month}.npy'
    if not path.exists():
        parquet=pq.ParquetFile(parquet_path(root,month))
        temp=path.with_suffix('.npy.tmp')
        matrix=np.lib.format.open_memmap(temp,mode='w+',dtype='float32',
                                       shape=(parquet.metadata.num_rows,len(features)))
        offset=0
        for batch in parquet.iter_batches(batch_size=batch_size,columns=features):
            values=batch.to_pandas().to_numpy(dtype='float32')
            matrix[offset:offset+len(values)]=values
            offset+=len(values)
        matrix.flush()
        del matrix
        temp.replace(path)
    result=np.load(path,mmap_mode='r',allow_pickle=False)
    if result.shape[1]!=len(features):
        raise ValueError('Memmap incompatible con features')
    return result


# [Anotación · líneas 168–179] sample_training submuestrea el entrenamiento: calcula un hash por par cliente-
#   mes, lo combina con el SHA-256 de sampling_seed y lo lleva al intervalo [0,1); conserva las filas con target
#   1 y las de target 0 cuyo valor es menor a undersampling_continua (0,5). Corta si hay filas sin target y
#   guarda los conteos de antes y después en sampling_<clave>.json.
def sample_training(frame,cfg,root,key):
    if frame[TARGET].isna().any():raise ValueError('No muestrear target inmaduro')
    hashes=pd.util.hash_pandas_object(frame[[ID,MES]],index=False).to_numpy(dtype='uint64')
    # Máscara reproducible por cliente-mes; sólo CONTINUA se submuestrea.
    values=(hashes ^ np.uint64(int.from_bytes(hashlib.sha256(str(cfg['sampling_seed']).encode()).digest()[:8],'little'))).astype('float64')/float(2**64)
    keep=frame[TARGET].eq(1).to_numpy() | (values<cfg['undersampling_continua'])
    sampled=frame.loc[keep].copy()
    write_json(root/f'sampling_{key}.json',dict(before=len(frame),after=len(sampled),
        positives_before=int(frame[TARGET].sum()),positives_after=int(sampled[TARGET].sum()),
        continua_before=int(frame[TARGET].eq(0).sum()),continua_after=int(sampled[TARGET].eq(0).sum()),
        fraction=cfg['undersampling_continua'],method='stable client-month hash'))
    return sampled


# [Anotación · líneas 182–199] gain_evaluator arma la métrica personalizada de LightGBM «ganancia_topN»: el
#   máximo de la curva de ganancia sobre los cortes, a maximizar. fixed_params devuelve los parámetros fijos
#   (objective binary, metric None, max_bin 31, bagging_freq 1, feature_fraction_bynode 1.0, feature_pre_filter
#   False, force_col_wise, deterministic y data_random_seed) junto con learning_rate, min_data_in_leaf,
#   feature_fraction y bagging_fraction tomados de la configuración. model_params les superpone los
#   hiperparámetros del trial, excepto num_iterations, y las tres semillas seed, bagging_seed y
#   feature_fraction_seed.
def gain_evaluator(meta,cuts,cfg):
    ids=meta[ID].to_numpy(); labels=meta[CLASE].to_numpy()
    def evaluate(pred,dataset):
        return 'ganancia_topN',float(gain_curve(pred,ids,labels,cuts,cfg).max()),True
    return evaluate


def fixed_params(cfg):
    return dict(objective='binary', metric='None', learning_rate=cfg['learning_rate'], max_bin=31,
        min_data_in_leaf=cfg['min_data_in_leaf'], feature_fraction=cfg['feature_fraction'],
        feature_fraction_bynode=1.0, bagging_fraction=cfg['bagging_fraction'], bagging_freq=1,
        feature_pre_filter=False, force_col_wise=True, verbosity=-1, num_threads=cfg['threads'],
        deterministic=True, data_random_seed=cfg['seed'])


def model_params(cfg, hp, seed):
    return {**fixed_params(cfg), **{k:v for k,v in hp.items() if k != 'num_iterations'},
            'seed':seed, 'bagging_seed':seed, 'feature_fraction_seed':seed}


# [Anotación · líneas 202–228] fold_data prepara los datos de un fold. Si no existen los binarios en
#   datasets/, carga los meses de entrenamiento, aplica el submuestreo, carga el mes de validación completo,
#   construye los Dataset de LightGBM con Master_status y Visa_status como categóricas y los guarda en formato
#   binario. Luego abre esos binarios y devuelve el Dataset de entrenamiento, el de validación, la matriz memmap
#   del mes de validación y sus columnas de id, clase y target.
def fold_data(root, cfg, features, plan, key):
    cache = root/'datasets'
    cache.mkdir(exist_ok=True)
    trfile, vafile = cache/f'{key}_train.bin', cache/f'{key}_valid.bin'
    meta = load_months(root, [plan['valid']], [ID, CLASE, TARGET])
    dataset_params = {k:fixed_params(cfg)[k] for k in ['max_bin','feature_pre_filter','data_random_seed']}
    if not trfile.exists() or not vafile.exists():
        train = load_months(root, plan['train'], list(dict.fromkeys(features+[ID,MES,CLASE,TARGET])))
        train = sample_training(train,cfg,root,key)
        valid = load_months(root, [plan['valid']], features+[TARGET])
        if train[TARGET].isna().any() or valid[TARGET].isna().any():
            raise ValueError('Target inmaduro en fold')
        cats=[c for c in cfg['categorical_columns'] if c in features]
        dt = lgb.Dataset(train[features], label=train[TARGET], params=dataset_params,categorical_feature=cats).construct()
        dv = lgb.Dataset(valid[features], label=valid[TARGET], reference=dt).construct()
        for ds, dest in [(dt,trfile), (dv,vafile)]:
            temp = dest.with_suffix('.bin.tmp')
            if temp.exists():
                temp.unlink()
            ds.save_binary(str(temp))
            temp.replace(dest)
        del train, valid, dt, dv
        gc.collect()
    dt = lgb.Dataset(str(trfile), params=dataset_params)
    dv = lgb.Dataset(str(vafile), reference=dt)
    Xvalid = matrix_month(root,plan['valid'],features,cfg['score_batch_size'])
    return dt, dv, Xvalid, meta


# [Anotación · líneas 231–238] objective_value combina las curvas de ganancia de los folds. Con la estrategia
#   «independent» suma, con los pesos, el máximo de cada fold con su propio N; en otro caso (la «common» de
#   CONFIG) calcula la curva promedio ponderada y devuelve su máximo con un N común para todos los folds.
def objective_value(curves, cuts, strategy, weights):
    curves = np.asarray(curves)
    if strategy == 'independent':
        positions = curves.argmax(axis=1)
        return float(np.dot(weights, curves[np.arange(len(curves)), positions])), [int(cuts[i]) for i in positions]
    average = np.asarray(weights)@curves
    i = int(average.argmax())
    return float(average[i]), [int(cuts[i])]*len(curves)


# [Anotación · líneas 241–254] Inicio de la etapa de búsqueda para una estrategia: lee la lista de features,
#   arma la grilla de cortes (n_min a n_max cada n_step), crea o reabre un estudio de Optuna en SQLite
#   (<nombre>.db) que maximiza, con sampler TPE de semilla cfg['seed'] o el sampler guardado en un pickle
#   previo, y marca como fallidos los trials que quedaron en estado RUNNING.
def optimize(cfg, root, name):
    features = json.loads((root/'features.json').read_text(encoding='utf-8'))['features']
    strategy = cfg['strategies'][name]
    cuts = np.arange(cfg['n_min'], cfg['n_max']+1, cfg['n_step'])
    # Caché de bins: deja sólo un fold/modelo activo, y reutiliza cuantización por trial.
    storage = optuna.storages.RDBStorage('sqlite:///'+(root/f'{name}.db').as_posix(),
                                        engine_kwargs={'connect_args':{'timeout':60}})
    sampler_path = root/f'{name}_sampler.pkl'
    sampler = pickle.loads(sampler_path.read_bytes()) if sampler_path.exists() else optuna.samplers.TPESampler(seed=cfg['seed'])
    study = optuna.create_study(study_name=name, storage=storage, direction='maximize',
                                sampler=sampler, load_if_exists=True)
    # El lock global asegura que RUNNING pertenece a una ejecución muerta.
    for trial in study.get_trials(states=[optuna.trial.TrialState.RUNNING]):
        study.tell(trial.number, state=optuna.trial.TrialState.FAIL)
# [Anotación · líneas 255–284] Función objetivo de cada trial: sugiere num_iterations (paso 100), num_leaves,
#   min_sum_hessian_in_leaf (log), learning_rate (log), feature_fraction y min_data_in_leaf (este último en
#   escala log) en los rangos de CONFIG. Para cada fold entrena LightGBM con semilla cfg['seed'] más el índice
#   del fold y early stopping de cfg['early_stopping'] rondas sobre la ganancia en validación, predice el mes de
#   validación en la iteración elegida por early stopping y calcula su curva de ganancia, AUC y average
#   precision. Devuelve el valor de objective_value y guarda en el trial las curvas, los cortes, las iteraciones
#   por fold y su mediana redondeada (final_iterations).
    def objective(trial):
        hp = dict(num_iterations=trial.suggest_int('num_iterations', cfg['trees_min'], cfg['max_trees'], step=100),
                  num_leaves=trial.suggest_int('num_leaves', *cfg['leaves_range']),
                  min_sum_hessian_in_leaf=trial.suggest_float('min_sum_hessian_in_leaf', *cfg['hessian_range'], log=True),
                  learning_rate=trial.suggest_float('learning_rate',*cfg['learning_rate_range'],log=True),
                  feature_fraction=trial.suggest_float('feature_fraction',*cfg['feature_fraction_range']),
                  min_data_in_leaf=trial.suggest_int('min_data_in_leaf',*cfg['min_data_range'],log=True))
        curves, metrics, iterations = [], [], []
        for f, plan in enumerate(strategy['folds']):
            key = '_'.join(map(str,plan['train']))+'_to_'+str(plan['valid'])
            dt,dv,X,meta = fold_data(root,cfg,features,plan,key)
            LOG.info('%s trial %s fold %s train=%s valid=%s',name,trial.number,f,plan['train'],plan['valid'])
            start=time.monotonic()
            model=lgb.train(model_params(cfg,hp,cfg['seed']+f),dt,num_boost_round=hp['num_iterations'],
                valid_sets=[dv],feval=gain_evaluator(meta,cuts,cfg),callbacks=[lgb.early_stopping(cfg['early_stopping'],first_metric_only=True,verbose=False),lgb.log_evaluation(0)])
            pred=model.predict(X,num_iteration=model.best_iteration)
            curves.append(gain_curve(pred,meta[ID],meta[CLASE],cuts,cfg))
            iterations.append(int(model.best_iteration))
            metrics.append(dict(month=plan['valid'],auc=float(roc_auc_score(meta[TARGET],pred)),
                ap=float(average_precision_score(meta[TARGET],pred)),seconds=time.monotonic()-start))
            del dt,dv,X,meta,model,pred
            gc.collect()
        value,best_cuts=objective_value(curves,cuts,strategy['objective'],cfg['month_weights'])
        trial.set_user_attr('curves',np.asarray(curves).tolist())
        trial.set_user_attr('cuts',cuts.tolist())
        trial.set_user_attr('best_cuts',best_cuts)
        trial.set_user_attr('iterations',iterations)
        trial.set_user_attr('final_iterations',int(np.rint(np.median(iterations))))
        trial.set_user_attr('metrics',metrics)
        return value
# [Anotación · líneas 285–293] El callback checkpoint guarda el sampler en un pickle y la tabla de trials en
#   <nombre>_trials.csv después de cada trial. Se ejecutan de a uno (n_jobs=1) los trials que faltan para llegar
#   a cfg['trials'] completos.
    def checkpoint(study,trial):
        temp=sampler_path.with_suffix('.pkl.tmp')
        temp.write_bytes(pickle.dumps(study.sampler))
        temp.replace(sampler_path)
        study.trials_dataframe().to_csv(root/f'{name}_trials.csv',index=False)
        LOG.info('%s trial %s %s value=%s',name,trial.number,trial.state.name,trial.value)
    remaining=cfg['trials']-len(study.get_trials(states=[optuna.trial.TrialState.COMPLETE]))
    if remaining>0:
        study.optimize(objective,n_trials=remaining,n_jobs=1,callbacks=[checkpoint])
# [Anotación · líneas 294–311] Ordena los trials completos por valor descendente (y número de trial
#   ascendente), recorre la lista salteando combinaciones de parámetros repetidas y conserva las primeras
#   cfg['top_k'] (10); corta con error si no las hay. Las guarda en <nombre>_selected.json con sus parámetros,
#   valor y atributos. selected_configs lee esas listas para una o para todas las estrategias.
    ranked=sorted(study.get_trials(states=[optuna.trial.TrialState.COMPLETE]),key=lambda t:(-t.value,t.number))
    selected,seen=[],set()
    for t in ranked:
        identity=json.dumps(t.params,sort_keys=True)
        if identity in seen:
            continue
        seen.add(identity)
        selected.append(dict(strategy=name,trial=t.number,params=t.params,value=t.value,**t.user_attrs))
        if len(selected)==cfg['top_k']:
            break
    if len(selected)!=cfg['top_k']:
        raise ValueError(f'No hay {cfg["top_k"]} configuraciones distintas completas')
    write_json(root/f'{name}_selected.json',selected)


def selected_configs(cfg,root,strategy=None):
    names=[strategy] if strategy else cfg['strategies']
    return [item for name in names for item in json.loads((root/f'{name}_selected.json').read_text(encoding='utf-8'))]


# [Anotación · líneas 314–342] choose_cut (etapa select) no hace nada si ya existe frozen.json. Para cada
#   configuración seleccionada y cada fold obtiene la predicción de validación: la lee de un .npz si existe, o
#   reentrena el modelo con la misma semilla y la cantidad de iteraciones registrada en el trial para ese fold,
#   predice y la guarda. Acumula, por fold, el promedio de las predicciones de todas las configuraciones.
def choose_cut(cfg,root):
    if (root/'frozen.json').exists():
        return
    features=json.loads((root/'features.json').read_text(encoding='utf-8'))['features']
    selected=selected_configs(cfg,root)
    cuts=np.arange(cfg['n_min'],cfg['n_max']+1,cfg['n_step'])
    validation_months=[plan['valid'] for plan in cfg['strategies'][next(iter(cfg['strategies']))]['folds']]
    sums=[None]*len(validation_months)
    for item in selected:
        for f,plan in enumerate(cfg['strategies'][item['strategy']]['folds']):
            path=root/f'validation_{item["strategy"]}_trial{item["trial"]}_fold{f}.npz'
            if path.exists():
                with np.load(path,allow_pickle=False) as state:
                    pred=state['pred']
            else:
                key='_'.join(map(str,plan['train']))+'_to_'+str(plan['valid'])
                dt,dv,X,meta=fold_data(root,cfg,features,plan,key)
                # Misma semilla y best_iter del trial: reusa la selección congelada.
                model=lgb.train(model_params(cfg,item['params'],cfg['seed']+f),dt,
                                num_boost_round=item['iterations'][f])
                pred=model.predict(X,num_iteration=item['iterations'][f])
                temp=path.with_suffix('.npz.tmp')
                with temp.open('wb') as stream:
                    np.savez_compressed(stream,pred=pred)
                temp.replace(path)
                del dt,dv,X,meta,model
                gc.collect()
            month=plan['valid']
            sums[f]=pred/len(selected) if sums[f] is None else sums[f]+pred/len(selected)
# [Anotación · líneas 343–357] Calcula la curva de ganancia del promedio en cada fold, las pondera con
#   month_weights y toma el N de mayor ganancia ponderada. Escribe ensemble_validation_curve.csv (ganancia
#   ponderada y por fold para cada N), cut.json (N, criterio y meses usados) y frozen.json (N, configuraciones
#   seleccionadas y los SHA-256 de cut.json y features.json).
    curves=[]
    for f,month in enumerate(validation_months):
        meta=load_months(root,[month],[ID,CLASE])
        curves.append(gain_curve(sums[f],meta[ID],meta[CLASE],cuts,cfg))
    avg=np.asarray(cfg['month_weights'])@np.asarray(curves)
    n=int(cuts[avg.argmax()])
    if n not in cuts:
        raise ValueError('N manual fuera de grilla')
    table={'N':cuts,'weighted_gain':avg}
    table.update({f'gain_fold{f}_{month}':curve for f,(month,curve) in enumerate(zip(validation_months,curves))})
    pd.DataFrame(table).to_csv(root/'ensemble_validation_curve.csv',index=False)
    write_json(root/'cut.json',dict(N=n,criterion='max curva ponderada 50/25/25 del ensamble de validacion',
                                  development_months=validation_months,independent_test=False))
    write_json(root/'frozen.json',dict(N=n,selected=selected,cut_sha256=digest(root/'cut.json'),
        features_sha256=digest(root/'features.json'),selection='top10 gain; common N from ensemble validation'))


# [Anotación · líneas 360–392] score_final (etapa score) exige frozen.json y verifica que los SHA-256 de
#   features.json y cut.json coincidan con los congelados. Si faltan scores por generar y no existe
#   datasets/final.bin, carga los meses de final_train_months, aplica el submuestreo y guarda el Dataset binario
#   de LightGBM. Carga los ids del mes a predecir, verifica que no haya duplicados, crea las carpetas scores/ y
#   models/ y abre la matriz memmap de ese mes.
def score_final(cfg,root,strategy=None,combine=True):
    if not (root/'frozen.json').exists(): raise ValueError('Congelar hiperparámetros y TopN antes de score')
    frozen=json.loads((root/'frozen.json').read_text(encoding='utf-8'))
    if frozen['features_sha256']!=digest(root/'features.json') or frozen['cut_sha256']!=digest(root/'cut.json'):
        raise ValueError('Freeze alterado')
    features=json.loads((root/'features.json').read_text(encoding='utf-8'))['features']
    selected=frozen['selected']
    cache=root/'datasets'/'final.bin'
    pending=any(not (root/'scores'/f'{item["strategy"]}_trial{item["trial"]}_seed{seed}.npz').exists()
                for item in selected for seed in cfg['final_seeds'])
    if pending and not cache.exists():
        train=load_months(root,cfg['final_train_months'],list(dict.fromkeys(features+[ID,MES,CLASE,TARGET])))
        train=sample_training(train,cfg,root,'final')
        if train[TARGET].isna().any():
            raise ValueError('Target final inmaduro')
        params={k:fixed_params(cfg)[k] for k in ['max_bin','feature_pre_filter','data_random_seed']}
        dataset=lgb.Dataset(train[features],label=train[TARGET],params=params,
                            categorical_feature=[c for c in cfg['categorical_columns'] if c in features]).construct()
        temp=cache.with_suffix('.bin.tmp')
        if temp.exists(): temp.unlink()
        dataset.save_binary(str(temp));temp.replace(cache)
        del dataset,train
        gc.collect()
    dataset=(lgb.Dataset(str(cache),params={k:fixed_params(cfg)[k] for k in
        ['max_bin','feature_pre_filter','data_random_seed']}).construct()) if pending else None
    scoremeta=load_months(root,[cfg['score_month']],[ID])
    ids=scoremeta[ID].to_numpy(dtype='int64')
    if len(np.unique(ids))!=len(ids):
        raise ValueError('IDs score duplicados')
    scores_dir=root/'scores';scores_dir.mkdir(exist_ok=True)
    model_dir=root/'models';model_dir.mkdir(exist_ok=True)
    # Agosto se lee por bloques, evitando mantenerlo entero junto al dataset final.
    score_matrix=matrix_month(root,cfg['score_month'],features,cfg['score_batch_size'])
# [Anotación · líneas 393–415] Para cada configuración seleccionada y cada semilla de final_seeds (salteando
#   las que ya tienen archivo de scores): entrena LightGBM sobre el dataset final con final_iterations rondas,
#   predice el mes a predecir en lotes de score_batch_size filas, verifica que las predicciones sean finitas y
#   estén completas, guarda el modelo en texto si save_models es verdadero y guarda predicciones e ids en
#   scores/<estrategia>_trial<n>_seed<semilla>.npz.
    for item in selected:
        for seed in cfg['final_seeds']:
            tag=f'{item["strategy"]}_trial{item["trial"]}_seed{seed}'
            dest=scores_dir/f'{tag}.npz'
            if dest.exists():
                continue
            LOG.info('FINAL %s árboles=%s',tag,item['final_iterations'])
            model=lgb.train(model_params(cfg,item['params'],seed),dataset,num_boost_round=item['final_iterations'])
            pred=[]
            for start in range(0,len(ids),cfg['score_batch_size']):
                pred.append(model.predict(score_matrix[start:start+cfg['score_batch_size']],
                                          num_iteration=item['final_iterations']))
            pred=np.concatenate(pred)
            if len(pred)!=len(ids) or not np.isfinite(pred).all():
                raise ValueError('Score inválido')
            if cfg['save_models']:
                model.save_model(str(model_dir/f'{tag}.txt'))
            temp=dest.with_suffix('.npz.tmp')
            with temp.open('wb') as stream:
                np.savez_compressed(stream,pred=pred,ids=ids)
            temp.replace(dest)
            del model,pred
            gc.collect()
# [Anotación · líneas 416–436] Si combine es falso, deja un archivo <estrategia>_FINALIZADO.json y termina
#   (run llama a la función con combine verdadero). En otro caso promedia las predicciones de los archivos de
#   scores de las configuraciones seleccionadas, lee N de cut.json, ordena por promedio descendente y
#   numero_de_cliente ascendente y toma los primeros N. Escribe scores_agosto_ensemble.csv.gz (id y promedio de
#   todos los clientes), envio_agosto_top<N>.csv (sólo ids, sin encabezado) y FINALIZADO.json.
    if not combine:
        write_json(root/f'{strategy}_FINALIZADO.json',dict(strategy=strategy,
            models=len(selected)*len(cfg['final_seeds']),score_month=cfg['score_month']))
        LOG.info('Estrategia %s terminada; falta combinar ambas para el envío único',strategy)
        return
    avg=np.zeros(len(ids),dtype=np.float64)
    count=0
    for item in selected:
        for seed in cfg['final_seeds']:
            path=scores_dir/f'{item["strategy"]}_trial{item["trial"]}_seed{seed}.npz'
            with np.load(path,allow_pickle=False) as state:
                if not np.array_equal(ids,state['ids']):
                    raise ValueError('Orden de IDs incompatible en checkpoint')
                avg+=state['pred'];count+=1
    avg/=count
    n=json.loads((root/'cut.json').read_text())['N']
    if n>len(ids): raise ValueError('TopN superior a población agosto')
    order=np.lexsort((ids,-avg))[:n]
    pd.DataFrame({ID:ids,'score':avg}).to_csv(root/'scores_agosto_ensemble.csv.gz',index=False)
    pd.Series(ids[order]).to_csv(root/f'envio_agosto_top{n}.csv',header=False,index=False)
    write_json(root/'FINALIZADO.json',dict(models=count,N=n,features=len(features),score_month=cfg['score_month']))


# [Anotación · líneas 439–453] run lee la configuración y valida: max_columns no mayor a 1.000, semillas
#   finales no vacías y distintas, fracción de submuestreo en (0,1], pesos por fold no negativos que sumen 1,
#   igual cantidad de folds que de pesos, y que el mes de validación de cada fold esté al menos
#   min_train_valid_gap meses después del último mes de entrenamiento (2 si la clave no está en la
#   configuración).
def run(config_path, stage='all', resume=False):
    cfg=json.loads(Path(config_path).read_text(encoding='utf-8-sig'))
    cfg['raw_path']=str(Path(cfg['raw_path']).expanduser().resolve())
    root=Path(cfg['work_dir']).expanduser().resolve()
    if cfg['max_columns']>1000: raise ValueError('Máximo permitido: 1000 columnas')
    if not cfg['final_seeds'] or len(set(cfg['final_seeds']))!=len(cfg['final_seeds']): raise ValueError('Semillas distintas requeridas')
    if not 0<cfg['undersampling_continua']<=1:raise ValueError('Fracción CONTINUA inválida')
    if not np.isclose(sum(cfg['month_weights']),1) or any(w<0 for w in cfg['month_weights']):
        raise ValueError('Pesos mensuales no negativos que sumen uno requeridos')
    for name,strategy in cfg['strategies'].items():
        if len(strategy['folds'])!=len(cfg['month_weights']):
            raise ValueError('Número de folds y pesos diferente')
        for plan in strategy['folds']:
            if month_index(plan['valid'])-max(map(month_index,plan['train']))<cfg.get('min_train_valid_gap',2):
                raise ValueError('Validación debe ser posterior al entrenamiento con el gap configurado')
# [Anotación · líneas 454–471] Fuera de Windows consulta el tipo de sistema de archivos de la carpeta de
#   trabajo con el comando stat y corta si es FUSE. Crea la carpeta, toma un lock exclusivo sobre .run.lock
#   (msvcrt en Windows, fcntl en el resto) y configura el log hacia la consola y run.log.
    if os.name!='nt':
        import subprocess
        ancestor=next(p for p in [root,*root.parents] if p.exists())
        filesystem=subprocess.run(['stat','-f','-c','%T',str(ancestor)],capture_output=True,text=True,check=True).stdout
        if 'fuse' in filesystem.lower():
            raise ValueError('work_dir requiere disco local: no usar GCSFuse')
    root.mkdir(parents=True,exist_ok=True)
    # Lock del sistema: liberación automática al morir el proceso, Windows y Linux.
    with (root/'.run.lock').open('a+b') as lock:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',
            handlers=[logging.StreamHandler(),logging.FileHandler(root/'run.log',encoding='utf-8')],force=True)
# [Anotación · líneas 472–487] Arma la firma de la corrida: configuración, SHA-256 del CSV crudo, SHA-256 de
#   los .py de la carpeta y versiones de Python, lightgbm, optuna, duckdb, pandas y numpy; si la configuración
#   trae prepared_source_dir (clave ausente en CONFIG) agrega datos de esa carpeta. Si ya existe manifest.json
#   exige modo reanudación y firma idéntica; si no existe, lo escribe.
        raw_hash=digest(cfg['raw_path'])
        signature=dict(config=cfg,raw_sha256=raw_hash,
            code={p.name:digest(p) for p in Path(__file__).parent.iterdir() if p.suffix in ['.py'] or p.name=='dq_rules.json'},
            versions=dict(python=platform.python_version(),lightgbm=lgb.__version__,optuna=optuna.__version__,
                          duckdb=duckdb.__version__,pandas=pd.__version__,numpy=np.__version__))
        if cfg.get('prepared_source_dir'):
            source=Path(cfg['prepared_source_dir']).expanduser().resolve()
            signature['prepared_source_manifest_sha256']=digest(source/'manifest.json')
            signature['prepared_source_parquets']={str(month):dict(size=(source/f'month_{month}.parquet').stat().st_size,
                mtime_ns=(source/f'month_{month}.parquet').stat().st_mtime_ns) for month in cfg['months']}
        manifest=root/'manifest.json'
        if manifest.exists():
            if not resume or json.loads(manifest.read_text(encoding='utf-8'))!=signature:
                raise ValueError('Corrida existente: --resume exige misma config/código/CSV/versiones')
        else:
            write_json(manifest,signature)
# [Anotación · líneas 488–497] Registra la memoria disponible y la cantidad de CPU, convierte SIGTERM en una
#   interrupción y ejecuta las etapas según el argumento stage: prepare (preparación de datos), search (búsqueda
#   para cada estrategia), select (elección de configuraciones y corte) y score (entrenamiento final y envío).
        LOG.info('Etapa=%s RAM disponible %.1f GB; CPU=%s',stage,psutil.virtual_memory().available/1e9,os.cpu_count())
        def stop(signum,frame):
            raise KeyboardInterrupt('Interrupción: reanudar con --resume')
        signal.signal(signal.SIGTERM,stop)
        if stage in ['all','prepare']: prepare(cfg,root)
        if stage in ['all','search']:
            for name in cfg['strategies']: optimize(cfg,root,name)
        if stage in ['all','select']: choose_cut(cfg,root)
        if stage in ['all','score']: score_final(cfg,root)
        LOG.info('Etapa %s terminada',stage)


# [Anotación · líneas 500–525] entry_stage es una entrada alternativa por etapa que lee la configuración de
#   --config (por defecto config.local.json, archivo que no está en el repositorio) y reanuda si existe
#   manifest.json. El bloque final permite ejecutar pipeline.py directamente con --config, --stage y --resume,
#   registrando la excepción en el log si la etapa se interrumpe.
def entry_stage(stage):
    """Entradas separadas: reutilizan la misma configuración y preparación."""
    parser=argparse.ArgumentParser(description=f'Basal temporal: {stage}')
    parser.add_argument('--config',default=str(Path(__file__).with_name('config.local.json')))
    parser.add_argument('--resume',action='store_true',help='Compatible; reanudación automática en estas entradas')
    args=parser.parse_args()
    cfg=json.loads(Path(args.config).read_text(encoding='utf-8-sig'))
    exists=(Path(cfg['work_dir']).expanduser()/'manifest.json').exists()
    try:
        run(args.config,stage,resume=args.resume or exists)
    except BaseException:
        LOG.exception('Entrada %s interrumpida; checkpoints conservados',stage)
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default=str(Path(__file__).with_name('config.local.json')))
    parser.add_argument('--stage',choices=['all','prepare','search','select','score'],default='all')
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    try:
        run(args.config,args.stage,args.resume)
    except BaseException:
        LOG.exception('Etapa interrumpida o fallida; checkpoints conservados')
        raise
```

### Competencia_1/basal_features.py

Etapa de preparación de datos: carga el CSV en DuckDB, calcula la clase ternaria y el target binario, aplica las correcciones por mes, agrega los flags de aguinaldo y los signed ranks de las variables elegidas por PSI, genera lags y deltas de 1 y 2 meses y exporta un Parquet por mes.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–7] Docstring del módulo e importaciones: gc, json, Path, numpy, pandas y duckdb.
"""Features basales, calidad, aguinaldo y signed ranks por drift de desarrollo."""
import gc
import json
from pathlib import Path
import numpy as np
import pandas as pd
import duckdb


# [Anotación · líneas 10–17] signed_rank transforma una columna en un rank con signo: los ceros quedan en 0,
#   los valores positivos reciben su percentil (entre 0 y 1) dentro de los positivos y los negativos reciben el
#   percentil de su valor absoluto dentro de los negativos, con signo menos. Los faltantes quedan como NA.
def signed_rank(series):
    out=pd.Series(np.nan,index=series.index,dtype='float32')
    out.loc[series.eq(0)]=0
    for positive in [True,False]:
        mask=series.gt(0) if positive else series.lt(0)
        values=series.loc[mask] if positive else series.loc[mask].abs()
        out.loc[mask]=(values.rank(method='average',pct=True)*(1 if positive else -1)).astype('float32')
    return out


# [Anotación · líneas 20–35] aguinaldo_flags compara, para mpayroll y para la columna contador de
#   acreditaciones, el valor del mes actual con el del mes anterior del mismo cliente. Cada flag vale 1 si el
#   valor actual es mayor o igual al anterior multiplicado por el umbral (threshold para el monto,
#   count_threshold para el contador) y queda NA si falta algún valor o el anterior no es positivo.
#   cobra_aguinaldo vale 1 si alguno de los dos flags es 1, 0 si ambos son 0 y NA en otro caso.
def aguinaldo_flags(frame,previous,count_column,threshold,count_threshold=2.0):
    result={}
    for column,label in [('mpayroll','mpayroll'),(count_column,'cpayroll')]:
        if column not in frame or column not in previous:
            raise ValueError('Falta variable salarial: '+column)
        pairs=frame[['numero_de_cliente',column]].merge(previous[['numero_de_cliente',column]],
            on='numero_de_cliente',how='left',suffixes=('','_may'),sort=False,validate='one_to_one')
        a=pairs[column];b=pairs[column+'_may']
        known=np.isfinite(a) & np.isfinite(b) & b.gt(0)
        limit=threshold if label=='mpayroll' else count_threshold
        flag=(a.ge(b*limit)).astype('float32').where(known)
        result[label+'_dup_junio']=flag.to_numpy()
    pay=result['mpayroll_dup_junio'];count=result['cpayroll_dup_junio']
    result['cobra_aguinaldo']=np.where((pay==1)|(count==1),1,
        np.where((pay==0)&(count==0),0,np.nan)).astype('float32')
    return result


# [Anotación · líneas 38–49] prepare_basal: si ya existe prepared.json no hace nada. Abre la base
#   features.duckdb en la carpeta de trabajo, fija el límite de memoria, los hilos y la carpeta temporal, y
#   carga el CSV crudo completo en la tabla raw con read_csv_auto.
def prepare_basal(cfg,root):
    from pipeline import q,ID,MES,CLASE,TARGET,EXCLUDED,quality_month,psi,write_json,LOG
    if (root/'prepared.json').exists():
        LOG.info('Preparación basal completa reutilizada');return
    con=duckdb.connect(str(root/'features.duckdb'))
    try:
        con.execute(f"SET memory_limit='{cfg['duckdb_memory_gb']}GB'")
        con.execute('SET threads='+str(cfg['threads']))
        (root/'tmp_duckdb').mkdir(exist_ok=True)
        con.execute('SET temp_directory=?',[str(root/'tmp_duckdb')])
        con.execute('SET preserve_insertion_order=false')
        con.execute('CREATE OR REPLACE TABLE raw AS SELECT * FROM read_csv_auto(?,sample_size=-1)',[cfg['raw_path']])
# [Anotación · líneas 50–57] Verificaciones sobre la tabla cruda: que no haya pares cliente/mes repetidos, que
#   existan numero_de_cliente, foto_mes y mpayroll, que exista cpayroll o cpayroll_trx (se usa la primera que
#   esté) y que estén todos los meses de cfg['months'].
        if con.execute(f'SELECT count(*) FROM (SELECT {q(ID)},{q(MES)} FROM raw GROUP BY ALL HAVING count(*)>1)').fetchone()[0]:
            raise ValueError('Cliente/mes duplicado')
        rawcols=[r[0] for r in con.execute('DESCRIBE raw').fetchall()]
        if not {ID,MES,'mpayroll'}<=set(rawcols):raise ValueError('Faltan claves o sueldo')
        count_column='cpayroll' if 'cpayroll' in rawcols else 'cpayroll_trx'
        if count_column not in rawcols:raise ValueError('No existe cpayroll ni cpayroll_trx')
        observed={r[0] for r in con.execute(f'SELECT DISTINCT {q(MES)} FROM raw').fetchall()}
        if not set(cfg['months'])<=observed:raise ValueError('Faltan meses requeridos')
# [Anotación · líneas 58–69] Crea la tabla labeled con la clase calculada por SQL: une cada fila con el mismo
#   cliente en el mes siguiente y en el subsiguiente. La clase queda NULL si en el archivo no existe alguno de
#   esos dos meses, BAJA+1 si el cliente no está en el mes siguiente, BAJA+2 si no está en el subsiguiente y
#   CONTINUA en otro caso. El target binario vale 1 para BAJA+1 o BAJA+2, 0 para CONTINUA y NULL si no hay
#   clase; las columnas clase_ternaria y target_baja12 que traiga el CSV no se copian.
        fields=','.join('r.'+q(c) for c in rawcols if c not in EXCLUDED-{ID,MES})
        con.execute(f'''CREATE OR REPLACE TABLE labeled AS
          WITH b AS (SELECT *,CAST({q(MES)}//100*12+{q(MES)}%100 AS INTEGER) AS __month FROM raw),
          m AS (SELECT {fields},r.__month,CASE
            WHEN NOT EXISTS(SELECT 1 FROM b z WHERE z.__month=r.__month+1)
              OR NOT EXISTS(SELECT 1 FROM b z WHERE z.__month=r.__month+2) THEN NULL
            WHEN a.{q(ID)} IS NULL THEN 'BAJA+1'
            WHEN c.{q(ID)} IS NULL THEN 'BAJA+2' ELSE 'CONTINUA' END AS {q(CLASE)}
          FROM b r LEFT JOIN b a ON a.{q(ID)}=r.{q(ID)} AND a.__month=r.__month+1
          LEFT JOIN b c ON c.{q(ID)}=r.{q(ID)} AND c.__month=r.__month+2)
          SELECT *,CASE WHEN {q(CLASE)} IS NULL THEN NULL
            WHEN {q(CLASE)} IN ('BAJA+1','BAJA+2') THEN 1 ELSE 0 END AS {q(TARGET)} FROM m''')
# [Anotación · líneas 70–89] Recorre los meses de cfg['months']: lee el mes ordenado por cliente, guarda en
#   202105 los valores crudos de mpayroll y del contador, calcula en 202106 los flags de aguinaldo contra esos
#   valores de mayo (en los demás meses los tres flags valen 0), aplica quality_month con la regla
#   ccajas_depositos en 202105, agrega los flags, verifica que todos los predictores sean numéricos y los pasa a
#   float32, y escribe base_AAAAMM.parquet. Al final guarda el registro de correcciones en dq_corrections.csv.
        rules = {'ccajas_depositos': [202105]}
        reports=[]
        may_raw=None
        for month in cfg['months']:
            LOG.info('Basal/DQ mes %s',month)
            frame=con.execute(f'SELECT * FROM labeled WHERE {q(MES)}=? ORDER BY {q(ID)}',[month]).df()
            if month==202105:may_raw=frame[[ID,'mpayroll',count_column]].copy()
            flags=aguinaldo_flags(frame,may_raw,count_column,cfg['aguinaldo_ratio'],cfg['aguinaldo_count_ratio']) if month==202106 else {
                name:np.zeros(len(frame),dtype='float32') for name in ['mpayroll_dup_junio','cpayroll_dup_junio','cobra_aguinaldo']}
            # La duplicación se calcula sobre valores crudos, antes del IPC.
            frame,report=quality_month(frame,cfg,rules);reports.extend(report)
            for name,values in flags.items():frame[name]=values
            for c in frame:
                if c not in EXCLUDED:
                    if not pd.api.types.is_numeric_dtype(frame[c]):raise ValueError('Predictor no numérico: '+c)
                    frame[c]=frame[c].astype('float32').replace([np.inf,-np.inf],np.nan)
            path=root/f'base_{month}.parquet';temp=path.with_suffix('.parquet.tmp')
            frame.to_parquet(temp,index=False,compression='zstd');temp.replace(path)
            del frame;gc.collect()
        pd.DataFrame(reports).to_csv(root/'dq_corrections.csv',index=False)
# [Anotación · líneas 90–106] Calcula el PSI entre 202105 y 202106 de cada variable original no categórica,
#   sobre valores no nulos, y arma una tabla ordenada por PSI descendente con la proporción de faltantes de cada
#   mes. Elige para signed rank las variables con PSI mayor a drift_threshold, hasta drift_rank_top_k, y guarda
#   la tabla en drift_rank_selection.csv. Escribe aguinaldo_report.json con los umbrales y la cantidad de
#   clientes de junio marcados y sin dato.
        may=pd.read_parquet(root/'base_202105.parquet');june=pd.read_parquet(root/'base_202106.parquet')
        baseline=[c for c in rawcols if c not in EXCLUDED]
        drift=[]
        # Valores observados: NA no determina qué columnas se rankean.
        for c in baseline:
            if c in cfg['categorical_columns']:continue
            a=may[c].dropna().to_numpy();b=june[c].dropna().to_numpy()
            value=psi(a,b) if len(a) and len(b) else np.nan
            drift.append(dict(feature=c,psi_observed_may_june=value,
                missing_may=float(may[c].isna().mean()),missing_june=float(june[c].isna().mean())))
        table=pd.DataFrame(drift).sort_values(['psi_observed_may_june','feature'],ascending=[False,True])
        ranks=table.loc[table.psi_observed_may_june>cfg['drift_threshold'],'feature'].head(cfg['drift_rank_top_k']).tolist()
        table['signed_rank_selected']=table.feature.isin(ranks);table.to_csv(root/'drift_rank_selection.csv',index=False)
        write_json(root/'aguinaldo_report.json',dict(count_column=count_column,amount_threshold=cfg['aguinaldo_ratio'],count_threshold=cfg['aguinaldo_count_ratio'],
            definition='raw June amount >= 1.5 * May OR count >= 2 * May; positive May; heuristic, not verified SAC',
            flagged=int(june.cobra_aguinaldo.eq(1).sum()),unknown=int(june.cobra_aguinaldo.isna().sum())))
        del may,june;gc.collect()
# [Anotación · líneas 107–117] Para cada mes lee base_AAAAMM.parquet, agrega una columna srank_<variable> por
#   cada variable elegida, calculada con signed_rank sobre ese mes, e inserta la tabla en la tabla intrames de
#   DuckDB. La lista temporal queda con todas las columnas predictoras del primer mes.
        temporal=None
        for month in cfg['months']:
            frame=pd.read_parquet(root/f'base_{month}.parquet')
            additions={'srank_'+c:signed_rank(frame[c]) for c in ranks}
            frame=pd.concat([frame,pd.DataFrame(additions,index=frame.index)],axis=1)
            con.register('month_frame',frame)
            if temporal is None:
                temporal=[c for c in frame if c not in EXCLUDED]
                con.execute('CREATE OR REPLACE TABLE intrames AS SELECT * FROM month_frame')
            else:con.execute('INSERT INTO intrames BY NAME SELECT * FROM month_frame')
            con.unregister('month_frame');del frame;gc.collect()
# [Anotación · líneas 118–122] Arma las expresiones SQL de las variables históricas: para cada columna de
#   temporal y para k = 1 y 2, lag<k>_ (valor de k meses atrás) y delta<k>_ (valor actual menos el de k meses
#   atrás).
        expressions=[]
        for c in temporal:
            for k in (1,2):
                expressions.extend([f'CAST(p{k}.{q(c)} AS FLOAT) AS {q(f"lag{k}_"+c)}',
                    f'CAST(t.{q(c)}-p{k}.{q(c)} AS FLOAT) AS {q(f"delta{k}_"+c)}'])
# [Anotación · líneas 123–142] Para cada mes crea la tabla features uniendo las filas del mes con las del
#   mismo cliente en el mes anterior y en el de dos meses atrás (LEFT JOIN filtrado por mes). Corta si se supera
#   max_columns o si la lista de columnas difiere entre meses, y exporta el resultado ordenado por cliente a
#   month_AAAAMM.parquet con compresión ZSTD.
        features=None
        for month in cfg['months']:
            month_idx=int(month)//100*12+int(month)%100
            LOG.info('Lags/deltas por mes %s',month)
            # Filtrar los tres lados antes del join evita materializar todo el panel ancho.
            con.execute(f'''CREATE OR REPLACE TABLE features AS SELECT t.*,{','.join(expressions)}
                FROM (SELECT * FROM intrames WHERE __month={month_idx}) t
                LEFT JOIN (SELECT * FROM intrames WHERE __month={month_idx-1}) p1
                  ON p1.{q(ID)}=t.{q(ID)}
                LEFT JOIN (SELECT * FROM intrames WHERE __month={month_idx-2}) p2
                  ON p2.{q(ID)}=t.{q(ID)}''')
            names=[r[0] for r in con.execute('DESCRIBE features').fetchall()]
            if len(names)>cfg['max_columns']:raise ValueError('Se excede limite de columnas')
            current=[c for c in names if c not in EXCLUDED]
            if features is not None and current!=features:raise ValueError('Features distintas entre meses')
            features=current
            path=root/f'month_{month}.parquet';temp=path.with_suffix('.parquet.tmp')
            con.execute(f'COPY (SELECT * FROM features ORDER BY {q(ID)}) TO ? (FORMAT PARQUET,COMPRESSION ZSTD)',[str(temp)])
            temp.replace(path)
            con.execute('DROP TABLE features')
# [Anotación · líneas 143–148] Escribe features.json (lista de features, variables originales, variables con
#   signed rank y meses de referencia del drift) y prepared.json (cantidad de features y meses), ejecuta
#   CHECKPOINT y cierra la conexión.
        write_json(root/'features.json',dict(features=features,baseline=baseline,signed_rank_sources=ranks,
            drift_reference_months=[202105,202106],drift_is_development_selection=True,
            removed_psi=[],total_generated=len(features),removed_constant=[]))
        write_json(root/'prepared.json',dict(features=len(features),months=cfg['months']))
        con.execute('CHECKPOINT')
    finally:con.close()
```


## Explicaciones del alumno (texto original)

### Competencia_1/Readme.md

> # DMEyF 2026 · competencia_01
>
> ## 1. Resumen
>
> |  |  |
> |---|---|
> | Target de entrenamiento | BAJA+1/BAJA+2 contra CONTINUA con undersampling del 50% solo en la clase CONTINUA |
> | Features | Basales, flags, signed ranks por drift y lag/delta 1/2; 785 totales |
> | Pesos | 50%/25%/25% de las ganancias; sino Junio contaba 2 veces|
> | Búsqueda | 60 trials Optuna TPE, secuencial |
> | Selección | 10 configuraciones distintas; un único TopN de su curva ponderada |
> | Fit final | Marzo–junio; 20 semillas por configuración = 200 modelos |
> | Scoring | Agosto; julio sólo aporta historia de features |
> | Ensamble | Promedio uniforme de probabilidades de los 200 modelos |
> | Corte | 10.500, congelado antes del entrenamiento final |
>
> ## 2. Decisiones
>
> ### Calidad, inflación y préstamos
>
> Se corrigen problemas identificados por variable/mes: ccajas_depositos de mayo completo a NA (100% cero); ceros de Visa/Master_Finiciomora en mayo/agosto y de Visa/Master_fultimo_cierre en junio a NA. Internet fuera de 0/1 pasan a NA. 
>
> Los montos nominales se ajustan por IPC. La lista y los valores IPC quedan explícitos en el script.
>
> ### Aguinaldo
>
> La señal se calcula con valores crudos antes del IPC. Se marca cuando mpayroll de junio es ≥1,5 veces mayo, O el contador cpayroll_trx es ≥2 veces mayo. Si falta algún valor o mayo no es positivo, la señal individual queda NA; cualquiera positiva activa el flag combinado. Fuera de junio, los flags son cero.
>
>
> ### Features agregadas
>
> Se agregaron de las 152 variables basales sus lags1 y 2, delta lag 1 y 2. Tres flags de aguinaldo y signed ranks de Master_mlimitecompra y Master_Finiciomora. Probé muchas combinaciones de features intra-mes sin mejoras en la ganancia. En total son 785 variables.
>
>
> ### Tres folds, selección y corte
>
> Los folds 0 y 1 dejan un mes intermedio. El fold 2 incorpora mayo y evalúa junio sin gap intermedio. La primera prueba fue solo con folds 0 y 1, dejando el gap como de 1 mes, pero decidí agregar mayo como un tercer fold que entrena con marzo, abril y evalúa junio, para comparar los hiperparámetros con una ventana de entrenamiento más amplia.
>
> Se ejecutan 60 trials secuenciales con el sampler TPE, usando la semilla 700087. Cada trial evalúa una misma combinación de hiperparámetros en los tres folds y maximiza la ganancia ponderada descrita anteriormente.
> Busqueda:
>
> | Hiperparámetro | Espacio de búsqueda | Muestreo |
> |---|---|---|
> | `num_iterations` | 300–2.000 | Entero |
> | `num_leaves` | 20–256 | Entero |
> | `min_sum_hessian_in_leaf` | 0,01–20 | Logarítmico |
> | `learning_rate` | 0,01–0,10 | Logarítmico |
> | `feature_fraction` | 0,10–1,00 | Uniforme |
> | `min_data_in_leaf` | 100–3.000 | Entero logarítmico |
>
>
> Se mantienen fijos max_bin=31, bagging_fraction=0,7 y bagging_freq=1.
>
> Se conservan las 10 configuraciones con mayor ganancia ponderada. Para cada una, el número de árboles del entrenamiento final se fija como la mediana de las mejores iteraciones de sus tres folds
>
> Se evalúan N=7.000…15.000 cada 500 clientes. Cada trial maximiza:
>
> `0,50 × G_mayo(N) + 0,25 × G_junio_marabril(N) + 0,25 × G_junio_marabrilmay(N)`.
>
> Estos pesos equilibran mayo/junio; no son pesos óptimos demostrados y los dos folds de junio no son poblaciones independientes. La búsqueda usa la función de curva de ganancia.
>
> Se recuperan las predicciones de los top10, se promedian **dentro de cada fold** y se elige un único N de la curva ponderada del ensamble. 
>
> ### Semillas y ensamble
>
> Los 200 modelos combinan diversidad de diez modelos y veinte semillas. Se promedian probabilidades; promediar rangos no superó el mejor máximo de probabilidades. 
>
>
> ## 3. Archivos compartidos
>
> ```text
> README.md
> correr.py
> pipeline.py
> basal_features.py
> ```
>
>
> ## 4. Librerias
>
> | Versión |
> |---|---:|
> | duckdb | 1.5.5 |
> | lightgbm | 4.7.0 |
> | optuna | 3.6.1 |
> | numpy | 2.4.4 |
> | pandas | 3.0.1 |
> | pyarrow | 24.0.0 |
> | psutil | 7.2.2 |
> | scikit-learn | 1.9.1 |
>
>
> ## 5. Reproducir 
>
> Poné competencia_01_crudo.csv (se tiene que llamar asi) junto a los .py y ejecutá:
> python -u correr.py
>
>
> Los resultados se guardan en `runs/`:
>
> | Salida | Contenido |
> |---|---|
> | `envio_agosto_topN.csv` | Único envío final: N IDs enteros, sin encabezado, seleccionados por el promedio de probabilidades de los 200 modelos |
> | `scores_agosto_ensemble.csv.gz` | Todos los clientes de agosto y su probabilidad promedio |
> | `expanding_trials.csv` | Resultados de los 60 trials de Optuna |
> | `ensemble_validation_curve.csv` | Curva de ganancia del ensamble de validación por TopN |
> | `frozen.json` y `cut.json` | Configuraciones seleccionadas y corte elegido |
> | `models/` y `scores/` | Modelos y predicciones individuales |
> | `run.log` | Registro de avance y errores |
> | `FINALIZADO.json` | Confirmación de que la corrida terminó |

