# Pedro Bosch — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: pedro-bosch
- Repositorio: https://github.com/pedro-bosch/dmeyf2026
- Link posteado: https://github.com/pedro-bosch/dmeyf2026/tree/competencia01/competencia01
- Commit: df60f331bf2e3461a94d419d4fd121e698de0dbc
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/pedro-bosch/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/pedro-bosch.json

## Resumen

La carpeta posteada (competencia01/) contiene un README, una notebook de feature engineering en Python con DuckDB, una notebook de modelado con LightGBM y Optuna, la base SQLite de Optuna, 12 modelos guardados en .txt y un manifiesto JSON del ensamble. El feature engineering lee competencia_01.csv, agrega 42 sumas y reglas de negocio, 17 ratios y 3 reglas históricas, y para 214 campos numéricos calcula lag 1, lag 2, delta 1, media, mínimo, máximo y pendiente sobre las observaciones anteriores del cliente (1.498 columnas). La notebook de modelado entrena una clase binaria (positivo = BAJA+1 o BAJA+2), busca hiperparámetros con Optuna entrenando en 202104 y 202105 y midiendo la ganancia en 202106, revalida los diez trials de mayor valor con dos backtests (202104→202105 y 202105→202106) y cinco de ellos con 1.000 particiones 25 %/75 % de junio, y entrena el ensamble final con 202104, 202105 y 202106: trials 78 y 25, con min_sum_hessian_in_leaf y min_gain_to_split multiplicados por 1,5 y las rondas por 1,1, cada uno con 6 semillas. La predicción de 202108 es el promedio de las 12 probabilidades; se exportan CSV con los primeros N clientes del ranking para varios cortes fijos.

**Qué entrega.** Archivos CSV sin encabezado ni índice con los numero_de_cliente de los primeros N clientes del ranking de 202108, uno por corte: 19 cortes entre 10.000 y 15.000 (incluido corte_manual = 11.175) y otros 6 entre 11.125 y 11.275. Los CSV no están en el repositorio y no se indica cuál se envió. El repositorio sí incluye los 12 modelos .txt, el manifiesto JSON del ensamble y la base de Optuna.

**Cómo se ejecuta.** El README describe dos recorridos. Recorrido corto: con el manifiesto JSON, los 12 modelos .txt y el Parquet de agosto (no incluido), un bloque de código del README carga cada modelo con lightgbm.Booster, suma las predicciones con peso 1/12 y ordena el ranking. Reconstrucción: colocar competencia_01.csv en Datasets/, ejecutar en orden las celdas de la notebook de FE con CREAR_FLAGS=False, generar los dos Parquet (el README indica que la notebook no tiene esa exportación activa) y ejecutar LGBM_Workflow_v1_4.ipynb: imports, rutas, carga, Optuna (o carga del estudio entregado), pasos 2 a 6. Las rutas son las de una VM (/home/ds/buckets/b1); en otro entorno el README indica editar las cuatro asignaciones de rutas.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase_binaria2): positivo = BAJA+1 o BAJA+2, negativo = CONTINUA. La ganancia se calcula sólo sobre BAJA+2, que se distingue por el peso 1,00002 (BAJA+1 lleva 1,00001 y CONTINUA 1,0).
- **Meses de entrenamiento:** 202104, 202105, 202106
- **Meses de validación:** 202105, 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica en Optuna ni en el entrenamiento final: la función muestrear_continua (fracción 0,30 de CONTINUA) está comentada. En la revalidación temporal cada repetición entrena con una muestra del 50 % del mes de origen, estratificada por clase_ternaria (StratifiedShuffleSplit).
- **Calidad de datos:** La notebook de modelado elimina todas las columnas cuyo nombre contiene 'ccajas_depositos'; el texto indica que es por tener todo cero en mayo. En el FE los faltantes se mantienen como NULL y se propagan: sumas, ratios y acumulados dan NULL si falta un insumo; ratio_seguro devuelve NULL con denominador cero o resultado no finito. Se agrega el contador n_campos_nulos.
- **Drifting:** No se observa en el código
- **Variables dentro del mes:** 42 variables de negocio: 37 sumas de columnas originales (cantidades, montos y totales Visa + Master) y 5 expresiones (balance_net, m_utilizacion_debito, m_transferencias_neto, mayor y menor fecha de vencimiento de tarjetas). 17 ratios calculados con ratio_seguro (utilización y consumo sobre límite, pago mínimo sobre saldo, saldo y préstamos sobre payroll, rentabilidad por producto, participación online, fee_load, fees_per_tx, rent_per_tx, util_visa, util_master, %_pago_minimo, cash_advance_share, share_usd). Además n_campos_nulos.
- **Variables históricas:** Para 214 campos numéricos (152 originales, 42 de negocio, 17 ratios y 3 reglas temporales) se calculan 7 históricos: lag_1 y lag_2 (mes calendario exacto t−1 y t−2), delta_1 (actual − lag_1) y media, mínimo, máximo y pendiente (regr_slope contra el índice de mes) sobre todas las observaciones anteriores del cliente, sin la actual; en total 1.498 columnas. Reglas temporales: saldo_mean (media anterior de mcuentas_saldo), ingresos (máximo anterior de mcaja_ahorro) y util_saldo = saldo_mean / (ingresos + 1). Cobertura: n_observaciones_previas y meses_desde_ultima_observacion.
- **Selección de variables:** No se observa una selección. Se calcula la importancia (gain y split) con el trial de mayor valor y se muestran las 30 primeras variables, sin quitar columnas. El modelo usa las 1.709 columnas del manifiesto, entre ellas numero_de_cliente y foto_mes.
- **Optimización de hiperparámetros:** Optuna con TPESampler (semilla 12, 20 trials iniciales), estudio guardado en SQLite, 50 trials por ejecución de la celda. Busca num_leaves (5–200, log), feature_fraction (0,2–0,4), bagging_fraction (0,2–0,6), min_gain_to_split (0,01–0,85) y min_sum_hessian_in_leaf (1–150, log). Fijos: learning_rate 0,005, max_bin 31, min_data_in_leaf 0, bagging_freq 1, feature_fraction_bynode 0,20, is_unbalance True. Entrena con 202104 y 202105, valida en 202106 con hasta 15.000 rondas y early stopping de 1.050; el valor del trial es el máximo de la curva de ganancia. Según el README, el estudio tiene 81 trials completos y 3 fallidos.
- **Hiperparámetros finales:** Según el manifiesto JSON. Trial 78: num_leaves 65, feature_fraction 0,2789, bagging_fraction 0,3654, min_gain_to_split 0,7086, min_sum_hessian_in_leaf 210,31, 3.513 rondas. Trial 25: num_leaves 47, feature_fraction 0,2608, bagging_fraction 0,3569, min_gain_to_split 0,9846, min_sum_hessian_in_leaf 223,43, 3.058 rondas. Comunes: learning_rate 0,005, max_bin 31, min_data_in_leaf 0, bagging_freq 1, feature_fraction_bynode 0,2, is_unbalance True. Respecto de Optuna, min_gain_to_split y min_sum_hessian_in_leaf están multiplicados por 1,5 y las rondas (best_iter 3.194 y 2.780) por 1,1.
- **Semillas:** Entrenamiento final: 1977, 1978, 2000, 2001, 2003 y 2007 para cada una de las dos configuraciones. Optuna, las particiones de la revalidación y los modelos de los backtests usan la semilla 12.
- **Cantidad de semillas:** 6
- **Ensamble:** Promedio con peso 1/12 de las probabilidades de 12 modelos: 2 configuraciones (trials 78 y 25) × 6 semillas.
- **Corte:** Cantidad fija escrita a mano: corte_manual = 11.175. Se exportan además archivos para 18 cortes más entre 10.000 y 15.000 y para 11.125, 11.150, 11.175, 11.225, 11.250 y 11.275. La notebook dibuja una curva de ganancia de junio del trial 78 como referencia; el texto indica que el corte de exportación se mantiene manual.
- **Validación:** Tres instancias, todas con la ganancia de la competencia. (1) Optuna: entrena en 202104 y 202105 y mide en 202106. (2) Revalidación temporal de los 10 trials de mayor valor: 5 repeticiones con el 50 % del mes de origen, backtest A 202104→202105 y backtest B 202105→202106; se resume media, desvío, P10, P25, mínimo y máximo. (3) Pseudo público/privado: los 5 primeros trials del backtest A se entrenan una vez con 202104 y 202105, predicen 202106 y se evalúan en 1.000 particiones aleatorias 25 %/75 %; se calcula ranking medio, frecuencia de top-1 y top-3 y regret.
- **Salidas:** FE: base DuckDB, competencia_01_fe_v3.csv, diccionario de variables en CSV y un JSON de validación (no incluidos). Modelado: base SQLite de Optuna, 12 modelos .txt y manifiesto JSON (incluidos), y CSV de numero_de_cliente por corte en /home/ds/buckets/b1/V1/predicciones/V1.4/ (no incluidos).

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Mínimos y máximos de ventana (`variables.min_max_ventana`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: no
- Entorno declarado: El README indica Python 3.11 para el FE (la salida guardada usa Python 3.11.13 y DuckDB 1.3.2), DuckDB con MEMORIA='1GB', HILOS=1 y hasta 20GB de temporales, y que la notebook de modelado conserva las rutas de una VM (/home/ds/buckets/b1). La notebook de FE nombra el kernel DM_EyF_v1. El README no lista versiones de lightgbm, optuna, pandas ni scikit-learn. En la raíz del repositorio, fuera de la carpeta posteada, hay un pyproject.toml (requires-python >=3.11, con versiones mínimas de duckdb, lightgbm, optuna, pandas, scikit-learn y otros) y un .python-version con 3.11.

## Pasos del camino de la entrega

1. **Importación del CSV y control de claves.** La notebook de FE abre una base DuckDB persistente (1 GB de memoria, 1 hilo), lee competencia_01.csv con tipos explícitos, agrega un índice de mes (año × 12 + mes) y verifica que no haya claves nulas, meses inválidos ni duplicados cliente-mes. Cada etapa se registra con una firma para poder reanudar. (`competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb` líneas 51–122; `competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb` líneas 180–212; `competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb` líneas 264–296)
2. **Sumas y reglas de negocio del mes.** Se definen 37 sumas de columnas originales y 5 expresiones adicionales (42 variables) y se materializan en la tabla fe_01_negocio. Un insumo NULL deja el resultado en NULL. (`competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb` líneas 313–374)
3. **Ratios del mes.** Se definen 17 ratios como pares numerador/denominador y se calculan con la macro ratio_seguro, que devuelve NULL si falta un insumo o el denominador es cero. Se materializan en fe_02_ratios. (`competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb` líneas 134–146; `competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb` líneas 390–419)
4. **Variables históricas.** Se unen originales, reglas de negocio, ratios y tres reglas temporales en fe_04_insumo. Para cada uno de los 214 campos numéricos se calculan lag_1, lag_2, delta_1 y media, mínimo, máximo y pendiente sobre las observaciones anteriores del cliente. El cálculo se hace de a 2 campos por bloque y cada bloque se incorpora a la tabla final competencia_01_fe_v3. (`competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb` líneas 434–493; `competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb` líneas 505–560; `competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb` líneas 662–683)
5. **Controles y exportación del feature engineering.** Se ejecutan pruebas sobre una tabla sintética y controles sobre la tabla final, se comparan los históricos de 24 clientes con un cálculo independiente en Python, se escribe el diccionario de variables y se exporta la tabla a CSV verificando huellas por mes. La notebook no exporta a Parquet; el README indica que ese paso no está incluido. (`competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb` líneas 570–650; `competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb` líneas 699–845; `competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb` líneas 856–896; `competencia01/README.md` líneas 121–123)
6. **Lectura del dataset y preparación de la clase.** La notebook de modelado lee competencia_01_fe_v3.parquet desde la ruta de la VM, elimina las columnas que contienen 'ccajas_depositos', crea clase_peso (1,00002 para BAJA+2, 1,00001 para BAJA+1, 1,0 para el resto) y la etiqueta binaria clase_binaria2 (1 para BAJA+1 y BAJA+2). (`competencia01/codigos/LGBM_Workflow_v1_4.ipynb` líneas 69–81; `competencia01/codigos/LGBM_Workflow_v1_4.ipynb` líneas 85–94; `competencia01/codigos/LGBM_Workflow_v1_4.ipynb` líneas 100–109)
7. **Función de ganancia.** lgb_gan_eval asigna 1.072.500 a cada BAJA+2 y −27.500 al resto, ordena por probabilidad descendente y devuelve el máximo de la ganancia acumulada. (`competencia01/codigos/LGBM_Workflow_v1_4.ipynb` líneas 113–119)
8. **Partición temporal para la optimización.** Entrenamiento con 202104 y 202105 completos y validación con 202106 completo. Las variables son todas las columnas salvo clase_ternaria, clase_peso y las dos etiquetas binarias. (`competencia01/codigos/LGBM_Workflow_v1_4.ipynb` líneas 132–167)
9. **Optimización de hiperparámetros con Optuna.** La función objetivo propone 5 hiperparámetros, entrena hasta 15.000 rondas con early stopping de 1.050 sobre la ganancia en junio y guarda en el trial la ronda de mayor ganancia y los parámetros completos. El estudio se guarda en SQLite con TPESampler (semilla 12) y se ejecutan 50 trials por corrida. (`competencia01/codigos/LGBM_Workflow_v1_4.ipynb` líneas 186–270)
10. **Revalidación temporal de los 10 trials de mayor valor.** Con 5 repeticiones de una muestra estratificada del 50 % del mes de origen, se entrena cada trial con su best_iter y se evalúa en el mes siguiente completo: backtest A (202104→202105) y backtest B (202105→202106). Se resume la ganancia por trial y se comparan ambos backtests. (`competencia01/codigos/LGBM_Workflow_v1_4.ipynb` líneas 343–447; `competencia01/codigos/LGBM_Workflow_v1_4.ipynb` líneas 455–490)
11. **Pseudo público/privado en junio.** Los 5 primeros trials del backtest A se entrenan una vez con 202104 y 202105 y predicen 202106. Sobre esas predicciones se generan 1.000 particiones aleatorias 25 %/75 % y se calculan, por trial, ganancia media, ranking medio, frecuencia de top-1 y top-3 y regret en cada parte, y el regret de seguir al primero del público. (`competencia01/codigos/LGBM_Workflow_v1_4.ipynb` líneas 515–564; `competencia01/codigos/LGBM_Workflow_v1_4.ipynb` líneas 570–660)
12. **Configuración del entrenamiento final.** Se fijan los trials 78 y 25, los meses 202104, 202105 y 202106 y las semillas 1977, 1978, 2000, 2001, 2003 y 2007. A los parámetros de cada trial se les multiplica min_sum_hessian_in_leaf y min_gain_to_split por 1,5 y las rondas por 1,1. (`competencia01/codigos/LGBM_Workflow_v1_4.ipynb` líneas 674–715)
13. **Ensamble final y predicción de agosto.** Se entrenan 12 modelos (2 configuraciones × 6 semillas) con los tres meses, cada uno predice 202108 desde competencia_01_fe_v3_Ago.parquet y se guarda en un .txt. Las probabilidades se promedian, se arma el ranking descendente y se escribe el manifiesto JSON. (`competencia01/codigos/LGBM_Workflow_v1_4.ipynb` líneas 758–835; `competencia01/modelos/v1_4_ensamble_t78_25_202104_202105_202106.json` líneas 1719–2069)
14. **Exportación por cortes.** Para cada cantidad de envíos se escribe un CSV con los numero_de_cliente de los primeros N del ranking, sin encabezado: primero 19 cortes entre 10.000 y 15.000 (con corte_manual = 11.175) y luego 6 cortes entre 11.125 y 11.275. (`competencia01/codigos/LGBM_Workflow_v1_4.ipynb` líneas 846–947)

## Archivos

- `competencia01/README.md` · explicacion · Markdown · 172 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pedro-bosch/competencia01/README.md.txt) — Guía de reproducción: lista los archivos incluidos, el entorno, los datos necesarios y las rutas, un bloque de código para predecir agosto con los 12 modelos entregados, los pasos para reconstruir el FE y el workflow, y una tabla con los parámetros de los trials 78 y 25.
- `competencia01/modelos/v1_4_ensamble_t78_25_202104_202105_202106.json` · configuracion · JSON · 2069 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pedro-bosch/competencia01/modelos/v1_4_ensamble_t78_25_202104_202105_202106.json.txt) — Manifiesto del ensamble escrito por la notebook de modelado: estudio de Optuna, meses de entrenamiento, las 1.709 columnas en orden y, para cada uno de los 12 modelos, trial, semilla, rondas, peso, archivo y parámetros.
- `competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb` · principal · Jupyter (python) · 953 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pedro-bosch/competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb.txt) — Notebook de feature engineering con DuckDB: importa competencia_01.csv a una base persistente, crea sumas y reglas de negocio, ratios y siete históricos por campo, valida el resultado y exporta la tabla final a CSV. La conversión a los Parquet que lee la notebook de modelado no está en este archivo.
- `competencia01/codigos/LGBM_Workflow_v1_4.ipynb` · principal · Jupyter (python) · 947 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pedro-bosch/competencia01/codigos/LGBM_Workflow_v1_4.ipynb.txt) — Notebook de modelado: prepara la clase y la función de ganancia, optimiza hiperparámetros de LightGBM con Optuna, revalida los trials con backtests temporales y particiones pseudo público/privado, entrena el ensamble final de 12 modelos, predice 202108 y exporta los CSV por corte.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### competencia01/FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb

Notebook de feature engineering con DuckDB: importa competencia_01.csv a una base persistente, crea sumas y reglas de negocio, ratios y siete históricos por campo, valida el resultado y exporta la tabla final a CSV. La conversión a los Parquet que lee la notebook de modelado no está en este archivo.

````python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–2] Celda de texto con una nota pendiente: agregar la exportación a Parquet.
#%% celda 1 [texto]
AÑADIR EXPORT A PARQUET

# [Anotación · líneas 4–48] Celda de texto que presenta la versión 3 del feature engineering:
#   CREAR_FLAGS=False omite los indicadores *_es_nulo; lista los siete históricos por variable (lag_1, lag_2,
#   delta_1 y media, mínimo, máximo y pendiente sobre observaciones anteriores); indica que un NULL en el
#   historial de un campo deja en NULL sus acumulados y que cada bloque se incorpora a la tabla final con COMMIT
#   y CHECKPOINT.
#%% celda 2 [texto]
# Feature engineering v3: flags opcionales y DuckDB persistente

Versión basada en `competencia_01_Feature_Engineering_DuckDB_v2.ipynb`, con salidas propias.
`CREAR_FLAGS=False` omite todos los indicadores `*_es_nulo`, tanto en los
bloques intermedios como en la tabla final y el CSV. `True` los habilita.
Se mantienen las mismas fórmulas, ventanas y propagación de NULL de la v2.
`n_campos_nulos` y los dos contadores de cobertura se conservan en ambos modos.
Usar el kernel **DM_EyF_v1**. Sólo requiere DuckDB y la biblioteca estándar;
se verifica con DuckDB 1.3.2 sin instalar ni actualizar paquetes.

Para todos los predictores numéricos originales y de negocio (incluidos ratios):

| Variable | Información utilizada para la foto t |
|---|---|
| `*_lag_1`, `*_lag_2` | Mes calendario exacto t−1 y t−2 |
| `*_delta_1` | Valor actual − valor de t−1 |
| `*_media_hist_prev`, `*_min_hist_prev`, `*_max_hist_prev` | Todas las observaciones anteriores del cliente |
| `*_pendiente_hist_prev` | Regresión sobre todos los meses anteriores, con la distancia mensual real |

Los acumulados excluyen el actual y requieren uno o más valores previos; la
pendiente requiere dos. **Se mantiene la propagación estricta de faltantes:**
si existe un NULL en el historial de un campo, sus acumulados son NULL. Un mes
sin fila no es una observación; no se inventan filas ni se rellenan valores.
La ampliación de la ventana evita exigir tres meses completos, pero no imputa
los datos ausentes. SQL NULL se exporta como campo vacío en el CSV.

Se excluyen claves, etiqueta y coordenada mensual interna (id, target y fechames). Los flags y contadores
de cobertura no reciben históricos recursivos. Las variables `saldo_mean`,
`ingresos` y `util_saldo`, por ser reglas de negocio, sí reciben históricos;
su primer NULL puede dejar sus acumulados posteriores en NULL bajo esta política.
Los códigos categóricos numéricos también se incluyen por pedido (revisar de cara  a competencia 1); evaluar su
interpretación antes del modelado.

## 1. Configuración

Cada bloque se guarda en la base y se incorpora a la tabla final mediante una
actualización de sus columnas, con COMMIT y CHECKPOINT. No se hace una unión de
cientos de bloques ni un ordenamiento global del CSV. `memory_limit` limita el
administrador de memoria de DuckDB, no toda la memoria del proceso.

Fuentes: [memoria](https://duckdb.org/2024/07/09/memory-management),
[ventanas](https://duckdb.org/docs/current/sql/functions/window_functions),
[actualizaciones](https://duckdb.org/docs/current/sql/statements/update),
[checkpoint](https://duckdb.org/docs/current/sql/statements/checkpoint).

# [Anotación · líneas 50–82] Importa pathlib, csv, hashlib, json, math, shutil, sys, time y duckdb. Busca
#   hacia arriba desde el directorio actual la carpeta que contiene Datasets/competencia_01.csv y define las
#   rutas de salida en Clases/Clase 4/FE (base DuckDB, CSV final y temporales). Fija MEMORIA='1GB', HILOS=1,
#   MAX_TEMPORALES='20GB', CREAR_FLAGS=False y REHACER=False, y crea las carpetas.
#%% celda 3 [código]
from pathlib import Path
import csv
import hashlib
import json
import math
import shutil
import sys
import time
import duckdb

# Encuentra el proyecto desde la carpeta FE o desde la raíz del proyecto.
RAIZ = next((p for p in (Path.cwd(), *Path.cwd().parents)
             if (p / 'Datasets' / 'competencia_01.csv').is_file()), None)
if RAIZ is None:
    raise FileNotFoundError('Ejecutar dentro del proyecto que contiene Datasets/competencia_01.csv')
CARPETA_FE = RAIZ / 'Clases' / 'Clase 4' / 'FE'
CSV_ORIGEN = RAIZ / 'Datasets' / 'competencia_01.csv'
BASE = CARPETA_FE / 'competencia_01_fe_v3.duckdb'
CSV_FINAL = CARPETA_FE / 'competencia_01_fe_v3.csv'
TEMPORALES = CARPETA_FE / 'duckdb_tmp_v3'
MEMORIA = '1GB'
HILOS = 1
MAX_TEMPORALES = '20GB'
CREAR_FLAGS = False  # True agrega *_es_nulo; False no genera ninguno.
REHACER = False  # True recalcula las tablas generadas por ESTA notebook.
# Al cambiar CREAR_FLAGS en una base existente: REHACER=True y ejecutar todo.
# Para conservar ambas variantes, cambiar también BASE y CSV_FINAL.
if type(CREAR_FLAGS) is not bool:
    raise TypeError('CREAR_FLAGS debe ser True o False (booleano).')

CARPETA_FE.mkdir(parents=True, exist_ok=True)
TEMPORALES.mkdir(exist_ok=True)

# [Anotación · líneas 84–95] Define tres funciones auxiliares: literal e identificador escapan comillas para
#   armar SQL, y sha256_archivo calcula el hash SHA-256 de un archivo leyéndolo en bloques de 4 MiB.
def literal(valor):
    return "'" + str(valor).replace("'", "''") + "'"

def identificador(nombre):
    return '"' + str(nombre).replace('"', '""') + '"'

def sha256_archivo(ruta):
    h = hashlib.sha256()
    with ruta.open('rb') as archivo:
        for bloque in iter(lambda: archivo.read(4 * 1024 * 1024), b''):
            h.update(bloque)
    return h.hexdigest()

# [Anotación · líneas 97–122] Calcula el hash del CSV de origen y abre la base DuckDB con el límite de
#   memoria, 1 hilo, carpeta de temporales y sin preservar el orden de inserción. Imprime el intérprete de
#   Python, la versión de DuckDB, el espacio libre y los ajustes efectivos. Define el nombre de la tabla final
#   (competencia_01_fe_v3), 2 campos por bloque y la exportación a CSV activada.
HUELLA_CSV = sha256_archivo(CSV_ORIGEN)
if 'con' in globals():
    con.close()
con = duckdb.connect(str(BASE), config={
    'memory_limit': MEMORIA,
    'threads': str(HILOS),
    'temp_directory': str(TEMPORALES),
    'max_temp_directory_size': MAX_TEMPORALES,
    'preserve_insertion_order': 'false',
})
print('Python:', sys.executable)
print('DuckDB:', duckdb.__version__)
print('Base:', BASE)
print('Crear indicadores *_es_nulo:', CREAR_FLAGS)
print('CSV SHA256:', HUELLA_CSV)
print('Espacio libre (GiB):', round(shutil.disk_usage(CARPETA_FE).free / 2**30, 2))
for fila in con.execute("""
    SELECT name, value FROM duckdb_settings()
    WHERE name IN ('memory_limit', 'threads', 'temp_directory',
                   'max_temp_directory_size', 'preserve_insertion_order')
    ORDER BY name
""").fetchall():
    print(fila)
TABLA_FINAL = 'competencia_01_fe_v3'
CAMPOS_POR_BLOQUE = 2
EXPORTAR_CSV = True

# [Anotación · líneas 124–156] Tras la celda de texto sobre etapas reanudables, crea tres macros SQL:
#   ratio_seguro (división que devuelve NULL si falta un insumo, el denominador es cero o algún valor no es
#   finito), mayor_estricto y menor_estricto (máximo y mínimo que devuelven NULL si falta alguno). Crea la tabla
#   _fe_etapas, donde cada etapa queda registrada con firma, filas, columnas y duración, e inicializa el
#   registro de firmas y el diccionario de variables.
#%% celda 4 [texto]
## 2. Etapas reanudables

`_fe_etapas` guarda las firmas del CSV, SQL, dependencias y `CREAR_FLAGS`. Con `REHACER=False`
se reutiliza lo ya terminado. Si cambia una fórmula o `CREAR_FLAGS`, usar otra BASE o activar
`REHACER=True` y ejecutar desde el inicio. Las actualizaciones de cada bloque y
su registro se confirman juntos: una interrupción no deja un bloque a medias.
La tabla final sólo debe consumirse cuando exista la marca `v3_completa`.

#%% celda 5 [código]
MACROS_SQL = """
CREATE OR REPLACE MACRO ratio_seguro(a, b) AS
    CASE WHEN a IS NULL OR b IS NULL OR b = 0
                   OR NOT isfinite(a::DOUBLE) OR NOT isfinite(b::DOUBLE)
         THEN NULL
         WHEN isfinite(a::DOUBLE / b::DOUBLE) THEN a::DOUBLE / b::DOUBLE
         ELSE NULL END;
CREATE OR REPLACE MACRO mayor_estricto(a, b) AS
    CASE WHEN a IS NULL OR b IS NULL THEN NULL ELSE greatest(a, b) END;
CREATE OR REPLACE MACRO menor_estricto(a, b) AS
    CASE WHEN a IS NULL OR b IS NULL THEN NULL ELSE least(a, b) END;
"""
con.execute(MACROS_SQL)
con.execute("""
CREATE TABLE IF NOT EXISTS _fe_etapas (
    etapa VARCHAR PRIMARY KEY, firma VARCHAR, tabla VARCHAR,
    filas BIGINT, columnas BIGINT, segundos DOUBLE,
    finalizado TIMESTAMP, sql VARCHAR
)
""")
con.execute('CHECKPOINT')
firmas = {}
diccionario = []

# [Anotación · líneas 158–178] registrar agrega una variable al diccionario (nombre, etapa, expresión SQL,
#   descripción, temporalidad). firma_consulta calcula un SHA-256 con la versión, CREAR_FLAGS, el hash del CSV,
#   la versión de DuckDB, las macros, el SQL y las firmas de las dependencias. existe_tabla consulta
#   information_schema y guardar_registro reemplaza la fila de una etapa en _fe_etapas.
def registrar(nombre, etapa, expresion, descripcion, temporal='foto actual'):
    diccionario.append({
        'variable': nombre, 'etapa': etapa, 'expresion_sql': expresion,
        'descripcion': descripcion, 'temporalidad': temporal,
    })

def firma_consulta(sql, dependencias=()):
    contenido = json.dumps([{'version': 'v3', 'crear_flags': CREAR_FLAGS},
                            HUELLA_CSV, duckdb.__version__, MACROS_SQL, sql,
                            [firmas[d] for d in dependencias]], ensure_ascii=False)
    return hashlib.sha256(contenido.encode('utf-8')).hexdigest()

def existe_tabla(tabla):
    return con.execute('SELECT count(*) FROM information_schema.tables '
                       'WHERE table_schema = ? AND table_name = ?',
                       ['main', tabla]).fetchone()[0] == 1

def guardar_registro(etapa, firma, tabla, filas, columnas, segundos, sql):
    con.execute('DELETE FROM _fe_etapas WHERE etapa = ?', [etapa])
    con.execute('INSERT INTO _fe_etapas VALUES (?, ?, ?, ?, ?, ?, current_timestamp, ?)',
                [etapa, firma, tabla, filas, columnas, segundos, sql])

# [Anotación · líneas 180–212] materializar crea una tabla a partir de un SQL. Si la etapa ya está registrada
#   con la misma firma y REHACER=False, la reutiliza tras verificar la cantidad de filas; si la firma cambió y
#   REHACER=False, lanza un error. En otro caso crea la tabla dentro de una transacción, controla las filas
#   esperadas, registra la etapa, confirma y hace CHECKPOINT; ante una excepción hace ROLLBACK.
def materializar(tabla, sql, dependencias=(), filas_esperadas=None):
    firma = firma_consulta(sql, dependencias)
    previo = con.execute('SELECT firma, filas FROM _fe_etapas WHERE etapa = ?',
                         [tabla]).fetchone()
    if previo and previo[0] != firma and not REHACER:
        raise RuntimeError(f'{tabla}: cambiaron los insumos/SQL o CREAR_FLAGS. Usar otra BASE o REHACER=True y ejecutar todo.')
    if previo and previo[0] == firma and existe_tabla(tabla) and not REHACER:
        n = con.execute(f'SELECT count(*) FROM {identificador(tabla)}').fetchone()[0]
        if n != previo[1] or (filas_esperadas is not None and n != filas_esperadas):
            raise RuntimeError(f'{tabla}: la tabla persistida fue modificada; reconstruir.')
        firmas[tabla] = firma
        print(f'Reutilizada {tabla}: {n:,} filas')
        return n
    inicio = time.perf_counter()
    print(f'Creando {tabla}...', flush=True)
    con.execute('BEGIN TRANSACTION')
    try:
        con.execute("DELETE FROM _fe_etapas WHERE etapa = 'v3_completa'")
        con.execute(f'CREATE OR REPLACE TABLE {identificador(tabla)} AS {sql}')
        n = con.execute(f'SELECT count(*) FROM {identificador(tabla)}').fetchone()[0]
        if filas_esperadas is not None and n != filas_esperadas:
            raise AssertionError(f'{tabla}: {n} filas, se esperaban {filas_esperadas}')
        columnas = len(con.execute(f'DESCRIBE {identificador(tabla)}').fetchall())
        guardar_registro(tabla, firma, tabla, n, columnas, time.perf_counter()-inicio, sql)
        con.execute('COMMIT')
    except BaseException:
        con.execute('ROLLBACK')
        raise
    con.execute('CHECKPOINT')
    firmas[tabla] = firma
    print(f'Guardada {tabla}: {n:,} filas, {columnas} columnas, '
          f'{time.perf_counter()-inicio:.1f} s; base {BASE.stat().st_size/2**20:.1f} MiB')
    return n

# [Anotación · líneas 214–255] esquema devuelve nombres y tipos de las columnas de una tabla.
#   incorporar_bloque agrega a la tabla final las columnas de un bloque (ALTER TABLE ADD COLUMN) y las completa
#   con un UPDATE unido por numero_de_cliente y foto_mes dentro de una transacción; verifica que se actualicen
#   N_FILAS filas, registra la etapa y hace CHECKPOINT. Si la etapa ya está registrada con la misma firma, no
#   repite el trabajo.
def esquema(tabla):
    return [(r[0], r[1]) for r in con.execute(f'DESCRIBE {identificador(tabla)}').fetchall()]

def incorporar_bloque(origen):
    """Agrega/actualiza sólo las columnas del bloque; no reescribe las anteriores."""
    campos = [(c, t) for c, t in esquema(origen) if c not in CLAVES]
    asignaciones = ', '.join(f'{identificador(c)} = h.{identificador(c)}' for c, _ in campos)
    sql = (f'UPDATE {identificador(TABLA_FINAL)} AS f SET {asignaciones} '
           f'FROM {identificador(origen)} AS h '
           'WHERE f.numero_de_cliente = h.numero_de_cliente AND f.foto_mes = h.foto_mes')
    firma = firma_consulta(sql, [TABLA_FINAL, origen])
    etapa = 'incorporar_' + origen
    previo = con.execute('SELECT firma, filas FROM _fe_etapas WHERE etapa=?', [etapa]).fetchone()
    actuales = dict(esquema(TABLA_FINAL))
    if previo and previo[0] != firma and not REHACER:
        raise RuntimeError(f'{etapa}: cambió la receta; reconstruir en orden.')
    if previo and previo[0] == firma and not REHACER:
        assert previo[1] == N_FILAS and all(actuales.get(c) == t for c, t in campos)
        firmas[TABLA_FINAL] = firma
        print('Reutilizado:', etapa, flush=True)
        return
    inicio = time.perf_counter()
    con.execute('BEGIN')
    try:
        con.execute("DELETE FROM _fe_etapas WHERE etapa = 'v3_completa'")
        for campo, tipo in campos:
            if campo not in actuales:
                con.execute(f'ALTER TABLE {identificador(TABLA_FINAL)} ADD COLUMN {identificador(campo)} {tipo}')
            elif actuales[campo] != tipo:
                raise TypeError(f'Tipo inesperado: {campo}')
        actualizadas = con.execute(sql).fetchone()[0]
        assert actualizadas == N_FILAS, (origen, actualizadas, N_FILAS)
        guardar_registro(etapa, firma, TABLA_FINAL, actualizadas,
                         len(actuales) + sum(c not in actuales for c, _ in campos),
                         time.perf_counter()-inicio, sql)
        con.execute('COMMIT')
    except BaseException:
        con.execute('ROLLBACK')
        raise
    con.execute('CHECKPOINT')
    firmas[TABLA_FINAL] = firma
    print(f'Incorporado {origen}: {len(campos)} columnas; {time.perf_counter()-inicio:.1f} s', flush=True)

# [Anotación · líneas 257–279] Lee el encabezado del CSV y separa claves (numero_de_cliente, foto_mes),
#   etiqueta (clase_ternaria) y predictores. Asigna tipos: VARCHAR para la etiqueta, DOUBLE para las columnas
#   que empiezan con 'm', 'Master_m' o 'Visa_m' y BIGINT para el resto. Materializa fe_00_base leyendo el CSV
#   con read_csv, tratando '', NA, NaN y NULL como faltantes, y agrega _mes_indice = año × 12 + mes.
#%% celda 6 [texto]
## 3. Importación y claves

Lectura directa del CSV, sin pandas. Se validan identificadores, meses y una fila
por cliente-mes. `_mes_indice` permite cruzar correctamente diciembre y enero.

#%% celda 7 [código]
with CSV_ORIGEN.open(encoding='utf-8-sig', newline='') as archivo:
    columnas_originales = next(csv.reader(archivo))
CLAVES = ['numero_de_cliente', 'foto_mes']
OBJETIVO = 'clase_ternaria'
PREDICTORES = [c for c in columnas_originales if c not in CLAVES + [OBJETIVO]]
tipos = {c: ('VARCHAR' if c == OBJETIVO else
             'DOUBLE' if c.startswith(('m', 'Master_m', 'Visa_m')) else 'BIGINT')
         for c in columnas_originales}
tipos_sql = '{' + ', '.join(f'{literal(c)}: {literal(t)}' for c, t in tipos.items()) + '}'
sql_base = f"""
SELECT *, (foto_mes // 100 * 12 + foto_mes % 100)::INTEGER AS _mes_indice
FROM read_csv({literal(CSV_ORIGEN.as_posix())},
    header=true, delim=',', types={tipos_sql},
    nullstr=['', 'NA', 'NaN', 'nan', 'NAN', 'NULL', 'null'], parallel=false)
"""
N_FILAS = materializar('fe_00_base', sql_base)
# [Anotación · líneas 280–296] Verifica con assert que haya filas, que no haya claves nulas ni meses fuera de
#   1–12 o años fuera de 1900–2200, y que no existan duplicados cliente-mes. Imprime la cantidad de filas por
#   mes y la cantidad de clientes distintos.
assert N_FILAS > 0, 'CSV sin filas'
assert con.execute("""
    SELECT count(*) FROM fe_00_base
    WHERE numero_de_cliente IS NULL OR foto_mes IS NULL
       OR foto_mes % 100 NOT BETWEEN 1 AND 12
       OR foto_mes // 100 NOT BETWEEN 1900 AND 2200
""").fetchone()[0] == 0, 'Claves o meses inválidos'
assert con.execute("""
    SELECT count(*) FROM (
        SELECT numero_de_cliente, foto_mes FROM fe_00_base
        GROUP BY numero_de_cliente, foto_mes HAVING count(*) > 1
    )
""").fetchone()[0] == 0, 'Hay duplicados cliente-mes: resolver antes del FE'
MESES = con.execute('SELECT foto_mes, count(*) FROM fe_00_base '
                    'GROUP BY foto_mes ORDER BY foto_mes').fetchall()
print('Filas y meses:', MESES)
print('Clientes:', con.execute('SELECT count(DISTINCT numero_de_cliente) FROM fe_00_base').fetchone()[0])

# [Anotación · líneas 298–310] Celda de texto: indica que las sumas son estrictas (un insumo NULL produce
#   NULL) y lista decisiones de nombres: mttarjeta_visa_debitos_automaticos como nombre real, una sola
#   definición de m_limite_compra y adelantos separados en pesos y en dólares.
#%% celda 8 [texto]
## 4. Sumas y reglas de negocio de la foto actual

Se conservan las reglas anteriores y se añaden las solicitadas. Todas las sumas
son estrictas. Las listas de actividad pueden solapar operaciones y deben leerse
como índices aditivos, no como conteos de operaciones únicas.

Decisiones confirmadas:

- `mtarjeta_visa_debitos_automaticos` se resuelve al nombre real **mttarjeta_visa_debitos_automaticos**.
- `m_limite_compra` se define una sola vez, aunque fue pedido dos veces; equivale al `tc_limite_compra` existente.
- Los adelantos van en **m_adelanto_pesos** y **m_adelanto_dolares**. No se genera una suma que mezcle monedas.
- Se mantienen alias solicitados aunque coincidan con otros totales existentes; el diccionario deja visibles sus fórmulas.

# [Anotación · líneas 312–356] Define SUMAS_NEGOCIO con 37 sumas de columnas originales: cantidades (tarjetas
#   de crédito, préstamos, utilización de Visa y de Master, inversiones, seguros, payroll, forex,
#   transferencias, cheques rechazados, uso de sucursales, canales online, débito, adelantos, suma de
#   delinquency), montos (transferencias, préstamos, payroll, cheques rechazados, inversiones en pesos y en
#   dólares, crédito Visa y Master, adelantos) y totales Visa + Master (saldo total, en pesos y en dólares,
#   límite de compra, consumo, pago mínimo, adelantos).
#%% celda 9 [código]
SUMAS_NEGOCIO = {
    'c_tarjetas_credito': ['ctarjeta_visa', 'ctarjeta_master'],
    'c_prestamos': ['cprestamos_personales', 'cprestamos_prendarios', 'cprestamos_hipotecarios'],
    'c_utilizacion_credito_master': ['ctarjeta_master_transacciones', 'ctarjeta_master_debitos_automaticos',
        'ctarjeta_master_descuentos', 'Master_cconsumos', 'Master_cadelantosefectivo'],
    'c_utilizacion_credito_visa': ['ctarjeta_visa_transacciones', 'ctarjeta_visa_debitos_automaticos',
        'ctarjeta_visa_descuentos', 'Visa_cconsumos', 'Visa_cadelantosefectivo'],
    'c_inversiones': ['cplazo_fijo', 'cinversion1', 'cinversion2'],
    'c_seguros': ['cseguro_vida', 'cseguro_auto', 'cseguro_vivienda', 'cseguro_accidentes_personales'],
    'c_payrroll': ['cpayroll_trx', 'cpayroll2_trx'],
    'c_forex': ['cforex', 'cforex_buy', 'cforex_sell'],
    'c_transferencias': ['ctransferencias_recibidas', 'ctransferencias_emitidas'],
    'c_cheques_rechazados': ['ccheques_depositados_rechazados', 'ccheques_emitidos_rechazados'],
    'c_utilizacion_sucursales': ['ccajas_transacciones', 'ccajas_consultas', 'ccajas_depositos',
        'ccajas_extracciones', 'ccajas_otras', 'catm_trx', 'catm_trx_other', 'cextraccion_autoservicio'],
    'c_online': ['cmobile_app_trx', 'chomebanking_transacciones'],
    'delinquencia': ['Master_delinquency', 'Visa_delinquency'],
    'c_utilizacion_debito': ['ctarjeta_debito', 'ctarjeta_debito_transacciones', 'ccuenta_debitos_automaticos'],
    'c_utilizacion_tc': ['ctarjeta_visa_debitos_automaticos', 'ctarjeta_master_debitos_automaticos'],
    'c_adelantos_efectivo': ['Master_cadelantosefectivo', 'Visa_cadelantosefectivo'],
    'm_transferencias': ['mtransferencias_recibidas', 'mtransferencias_emitidas'],
    'm_utilizacion_tc': ['mttarjeta_visa_debitos_automaticos', 'mttarjeta_master_debitos_automaticos'],
    'm_prestamos': ['mprestamos_personales', 'mprestamos_prendarios', 'mprestamos_hipotecarios'],
    'm_payroll': ['mpayroll', 'mpayroll2'],
    'm_cheques_rechazados': ['mcheques_depositados_rechazados', 'mcheques_emitidos_rechazados'],
    'm_inversiones_pesos': ['mplazo_fijo_pesos', 'minversion1_pesos'],
    'm_inversiones_dolares': ['mplazo_fijo_dolares', 'minversion1_dolares'],
    'tc_saldo_total': ['Master_msaldototal', 'Visa_msaldototal'],
    'tc_saldo_pesos': ['Master_msaldopesos', 'Visa_msaldopesos'],
    'tc_saldo_dolares': ['Master_msaldodolares', 'Visa_msaldodolares'],
    'tc_limite_compra': ['Master_mlimitecompra', 'Visa_mlimitecompra'],
    'tc_consumo_total': ['Master_mconsumototal', 'Visa_mconsumototal'],
    'tc_pago_minimo': ['Master_mpagominimo', 'Visa_mpagominimo'],
    'tc_adelantos_pesos': ['Master_madelantopesos', 'Visa_madelantopesos'],
    'tc_adelantos_dolares': ['Master_madelantodolares', 'Visa_madelantodolares'],
}
SUMAS_NEGOCIO.update({
    'm_consumo_dolares': ['Master_mconsumosdolares', 'Visa_mconsumosdolares'],
    'm_limite_compra': ['Master_mlimitecompra', 'Visa_mlimitecompra'],
    'm_credito_visa': ['mttarjeta_visa_debitos_automaticos', 'mtarjeta_visa_consumo', 'mtarjeta_visa_descuentos'],
    'm_credito_master': ['mttarjeta_master_debitos_automaticos', 'mtarjeta_master_consumo', 'mtarjeta_master_descuentos'],
    'm_adelanto_pesos': ['Visa_madelantopesos', 'Master_madelantopesos'],
    'm_adelanto_dolares': ['Visa_madelantodolares', 'Master_madelantodolares'],
})
# [Anotación · líneas 357–374] Arma la expresión SQL de cada suma verificando que sus campos existan entre los
#   predictores y agrega cinco expresiones: balance_net (mpasivos_margen − mactivos_margen),
#   m_utilizacion_debito, m_transferencias_neto (recibidas − emitidas) y el mayor y el menor entre
#   Master_Fvencimiento y Visa_Fvencimiento. Registra las variables en el diccionario y materializa
#   fe_01_negocio.
expresiones_negocio = {}
for nombre, campos in SUMAS_NEGOCIO.items():
    assert set(campos) <= set(PREDICTORES), f'Campos inválidos en {nombre}'
    expresiones_negocio[nombre] = ' + '.join(identificador(c) for c in campos)
expresiones_negocio.update({
    'balance_net': 'mpasivos_margen - mactivos_margen',
    'm_utilizacion_debito': 'mcuenta_debitos_automaticos',
    'm_transferencias_neto': 'mtransferencias_recibidas - mtransferencias_emitidas',
    'tc_fvencimiento_mayor': 'mayor_estricto(Master_Fvencimiento, Visa_Fvencimiento)',
    'tc_fvencimiento_menor': 'menor_estricto(Master_Fvencimiento, Visa_Fvencimiento)',
})
for nombre, expr in expresiones_negocio.items():
    registrar(nombre, 'fe_01_negocio', expr, 'Operación estricta: cualquier insumo NULL produce NULL.')
sql_negocio = 'SELECT numero_de_cliente, foto_mes,\n' + ',\n'.join(
    f'{expr} AS {identificador(nombre)}' for nombre, expr in expresiones_negocio.items()
) + '\nFROM fe_00_base'
materializar('fe_01_negocio', sql_negocio, ['fe_00_base'], N_FILAS)
print('Variables de negocio:', len(expresiones_negocio))

# [Anotación · líneas 376–387] Celda de texto: indica que hay 9 ratios previos y 8 agregados, que el +1 del
#   denominador se aplica donde se definió, que %_pago_minimo es una razón sin multiplicar por 100 y que
#   share_usd no convierte moneda.
#%% celda 10 [texto]
## 5. Ratios actuales

Se conservan los nueve ratios anteriores y se agregan los ocho solicitados.
Los `+1` se aplican exactamente donde se pidieron. Si aun así el denominador
resulta cero, el ratio seguro produce NULL. `%_pago_minimo` conserva ese nombre
y devuelve una **razón**, no un porcentaje multiplicado por 100.

Para `share_usd`, por confirmación del usuario, se usan los campos existentes
`Visa_mconsumosdolares + Master_mconsumosdolares` y el total
`Visa_mconsumototal + Master_mconsumototal + 1`. No se convierte moneda: no debe
interpretarse automáticamente como una participación monetaria homogénea.

# [Anotación · líneas 389–419] Define 17 ratios como pares numerador/denominador calculados con ratio_seguro:
#   utilización y consumo sobre límite de tarjetas, pago mínimo sobre saldo, saldo y préstamos sobre payroll,
#   rentabilidad por producto, participación online, fee_load, fees_per_tx, rent_per_tx, util_visa, util_master,
#   %_pago_minimo, cash_advance_share y share_usd. Materializa fe_02_ratios uniendo fe_00_base con
#   fe_01_negocio.
#%% celda 11 [código]
RATIOS = {
    'ratio_utilizacion_limite_tc': ('n.tc_saldo_total', 'n.tc_limite_compra'),
    'ratio_consumo_limite_tc': ('n.tc_consumo_total', 'n.tc_limite_compra'),
    'ratio_pago_minimo_saldo_tc': ('n.tc_pago_minimo', 'n.tc_saldo_total'),
    'ratio_utilizacion_limite_visa': ('b.Visa_msaldototal', 'b.Visa_mlimitecompra'),
    'ratio_utilizacion_limite_master': ('b.Master_msaldototal', 'b.Master_mlimitecompra'),
    'ratio_saldo_payroll': ('b.mcuentas_saldo', 'n.m_payroll'),
    'ratio_prestamos_payroll': ('n.m_prestamos', 'n.m_payroll'),
    'ratio_rentabilidad_por_producto': ('b.mrentabilidad', 'b.cproductos'),
    'ratio_participacion_online': ('n.c_online', '(n.c_online + n.c_utilizacion_sucursales)'),
}
RATIOS.update({
    'fee_load': ('b.mcomisiones', '(b.mcomisiones + b.mrentabilidad + 1)'),
    'fees_per_tx': ('b.mcomisiones', '(b.ctrx_quarter + 1)'),
    'rent_per_tx': ('b.mrentabilidad', '(b.ctrx_quarter + 1)'),
    'util_visa': ('b.Visa_msaldototal', '(b.Visa_mfinanciacion_limite + 1)'),
    'util_master': ('b.Master_msaldototal', '(b.Master_mfinanciacion_limite + 1)'),
    '%_pago_minimo': ('(b.Visa_mpagominimo + b.Master_mpagominimo)',
                     '(b.Visa_mpagado + b.Master_mpagado + 1)'),
    'cash_advance_share': ('(b.Visa_cadelantosefectivo + b.Master_cadelantosefectivo)',
                           '(b.Visa_cconsumos + b.Master_cconsumos + 1)'),
    'share_usd': ('n.m_consumo_dolares', '(n.tc_consumo_total + 1)'),
})
expresiones_ratios = {nombre: f'ratio_seguro({a}, {b})' for nombre, (a, b) in RATIOS.items()}
for nombre, expr in expresiones_ratios.items():
    registrar(nombre, 'fe_02_ratios', expr, 'Razón segura; NULL si falta un insumo o el denominador es cero.')
sql_ratios = 'SELECT b.numero_de_cliente, b.foto_mes, ' + ', '.join(
    f'{expr} AS {identificador(c)}' for c, expr in expresiones_ratios.items()
) + ' FROM fe_00_base b JOIN fe_01_negocio n USING (numero_de_cliente, foto_mes)'
materializar('fe_02_ratios', sql_ratios, ['fe_00_base', 'fe_01_negocio'], N_FILAS)

# [Anotación · líneas 421–447] Tras la celda de texto sobre las ventanas, expresiones_historicas genera para
#   cada campo el SQL de lag_1 y lag_2 (valor en el mes exacto t−1 y t−2) y de cuatro acumulados sobre la
#   ventana 'historia': media, mínimo y máximo (requieren al menos 1 observación anterior) y pendiente con
#   regr_slope contra _mes_indice (requiere 2). Cada acumulado se calcula sólo si ninguna observación anterior
#   del campo es NULL.
#%% celda 12 [texto]
## 6. Funciones temporales

`RANGE ... 1 PRECEDING / 2 PRECEDING` busca meses exactos. La ventana acumulada
usa `ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING` sobre claves únicas:
incluye todas las observaciones anteriores y nunca el actual ni el futuro.
El control `count(campo) = count(*)` impide que los agregados omitan NULL.

`saldo_mean` y `ingresos` son, respectivamente, la media anterior de
`mcuentas_saldo` y el máximo anterior de `mcaja_ahorro`, por cliente.
`util_saldo = saldo_mean / (ingresos + 1)` usa esos dos valores históricos.

#%% celda 13 [código]
def expresiones_historicas(campos):
    expresiones = {}
    for campo in campos:
        q = identificador(campo)
        for k in (1, 2):
            expresiones[f'{campo}_lag_{k}'] = f'max({q}) OVER v{k}'
        for funcion, sufijo, minimo in [('avg', 'media', 1), ('min', 'min', 1),
                                        ('max', 'max', 1), ('regr_slope', 'pendiente', 2)]:
            args = f'{q}, _mes_indice' if funcion == 'regr_slope' else q
            expresiones[f'{campo}_{sufijo}_hist_prev'] = (
                f'CASE WHEN count(*) OVER historia >= {minimo} '
                f'AND count({q}) OVER historia = count(*) OVER historia '
                f'THEN {funcion}({args}) OVER historia END')
    return expresiones

# [Anotación · líneas 449–467] sql_historicos arma la consulta completa para una lista de campos: define las
#   ventanas v1 y v2 (RANGE de 1 y 2 meses exactos hacia atrás por cliente) e historia (todas las filas
#   anteriores del cliente, sin la actual), calcula los seis históricos y agrega delta_1 = valor actual − lag_1.
#   Devuelve las claves y los históricos.
def sql_historicos(origen, campos):
    columnas = ', '.join(identificador(c) for c in campos)
    calculos = ', '.join(f'{expr} AS {identificador(c)}'
                         for c, expr in expresiones_historicas(campos).items())
    deltas = ', '.join(f'{identificador(c)} - {identificador(c + "_lag_1")} '
                       f'AS {identificador(c + "_delta_1")}' for c in campos)
    return f"""
    WITH historico AS (
        SELECT numero_de_cliente, foto_mes, _mes_indice, {columnas}, {calculos}
        FROM {identificador(origen)}
        WINDOW v1 AS (PARTITION BY numero_de_cliente ORDER BY _mes_indice
                      RANGE BETWEEN 1 PRECEDING AND 1 PRECEDING),
               v2 AS (PARTITION BY numero_de_cliente ORDER BY _mes_indice
                      RANGE BETWEEN 2 PRECEDING AND 2 PRECEDING),
               historia AS (PARTITION BY numero_de_cliente ORDER BY _mes_indice
                            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
    )
    SELECT * EXCLUDE (_mes_indice, {columnas}), {deltas} FROM historico
    """

# [Anotación · líneas 469–493] sql_negocio_temporal calcula por cliente saldo_mean (media de mcuentas_saldo en
#   las observaciones anteriores), ingresos (máximo anterior de mcaja_ahorro) y util_saldo = saldo_mean /
#   (ingresos + 1). Se materializa como fe_03_negocio_temporal y las tres variables se registran en el
#   diccionario.
def sql_negocio_temporal(origen):
    return f"""
    WITH anteriores AS (
        SELECT numero_de_cliente, foto_mes,
               CASE WHEN count(*) OVER historia >= 1
                      AND count(mcuentas_saldo) OVER historia = count(*) OVER historia
                    THEN avg(mcuentas_saldo) OVER historia END AS saldo_mean,
               CASE WHEN count(*) OVER historia >= 1
                      AND count(mcaja_ahorro) OVER historia = count(*) OVER historia
                    THEN max(mcaja_ahorro) OVER historia END AS ingresos
        FROM {identificador(origen)}
        WINDOW historia AS (PARTITION BY numero_de_cliente ORDER BY _mes_indice
                            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
    )
    SELECT *, ratio_seguro(saldo_mean, ingresos + 1) AS util_saldo FROM anteriores
    """

sql_temporal_negocio = sql_negocio_temporal('fe_00_base')
materializar('fe_03_negocio_temporal', sql_temporal_negocio, ['fe_00_base'], N_FILAS)
for campo, expr in {
    'saldo_mean': 'media estricta de mcuentas_saldo en todas las observaciones previas del cliente',
    'ingresos': 'máximo estricto de mcaja_ahorro en todas las observaciones previas del cliente',
    'util_saldo': 'ratio_seguro(saldo_mean, ingresos + 1)',
}.items():
    registrar(campo, 'fe_03_negocio_temporal', expr, expr, 'sólo meses anteriores')

# [Anotación · líneas 495–524] Une fe_00_base, fe_01_negocio, fe_02_ratios y fe_03_negocio_temporal en
#   fe_04_insumo. CAMPOS_HISTORICOS toma todas sus columnas numéricas salvo claves, etiqueta y _mes_indice, y
#   verifica que coincidan con predictores originales + reglas de negocio + ratios + las tres reglas temporales.
#   Imprime los conteos y la cantidad de históricos a crear (7 por campo).
#%% celda 14 [texto]
## 7. Insumo unificado y selección de campos

Se materializa una tabla que contiene las originales, reglas actuales, ratios y
las tres reglas históricas. Sobre sus columnas numéricas se calcula una sola
capa de siete históricos. Así también reciben ventanas las variables de negocio.
Si `CREAR_FLAGS=True`, se calcula un indicador por variable, sin flags de
otros flags. Con `False` se omite su SQL y su registro en el diccionario.

#%% celda 15 [código]
sql_insumo = """
SELECT b.*, n.* EXCLUDE (numero_de_cliente, foto_mes),
       r.* EXCLUDE (numero_de_cliente, foto_mes),
       t.* EXCLUDE (numero_de_cliente, foto_mes)
FROM fe_00_base b
JOIN fe_01_negocio n USING (numero_de_cliente, foto_mes)
JOIN fe_02_ratios r USING (numero_de_cliente, foto_mes)
JOIN fe_03_negocio_temporal t USING (numero_de_cliente, foto_mes)
"""
materializar('fe_04_insumo', sql_insumo,
             ['fe_00_base', 'fe_01_negocio', 'fe_02_ratios', 'fe_03_negocio_temporal'], N_FILAS)
CAMPOS_HISTORICOS = [c for c, tipo in esquema('fe_04_insumo')
                    if c not in CLAVES + [OBJETIVO, '_mes_indice']
                    and tipo in {'BIGINT', 'DOUBLE', 'INTEGER', 'HUGEINT'}]
assert set(CAMPOS_HISTORICOS) == set(PREDICTORES) | set(expresiones_negocio) | set(RATIOS) | {'saldo_mean', 'ingresos', 'util_saldo'}
assert len(CAMPOS_HISTORICOS) == len(set(CAMPOS_HISTORICOS))
print('Originales:', len(PREDICTORES))
print('Reglas de negocio y ratios:', len(CAMPOS_HISTORICOS)-len(PREDICTORES))
print('Campos con ventanas:', len(CAMPOS_HISTORICOS))
print('Históricos a crear:', 7*len(CAMPOS_HISTORICOS))

# [Anotación · líneas 526–535] Materializa fe_05_cobertura con dos variables por fila: n_observaciones_previas
#   (cantidad de filas anteriores del cliente) y meses_desde_ultima_observacion (diferencia de _mes_indice con
#   la fila anterior).
sql_cobertura = """
SELECT numero_de_cliente, foto_mes,
       row_number() OVER historia - 1 AS n_observaciones_previas,
       _mes_indice - lag(_mes_indice) OVER historia AS meses_desde_ultima_observacion
FROM fe_00_base
WINDOW historia AS (PARTITION BY numero_de_cliente ORDER BY _mes_indice)
"""
materializar('fe_05_cobertura', sql_cobertura, ['fe_00_base'], N_FILAS)
for c in ['n_observaciones_previas', 'meses_desde_ultima_observacion']:
    registrar(c, 'fe_05_cobertura', sql_cobertura, 'Cobertura del pasado observado.', 'sólo pasado')

# [Anotación · líneas 537–560] agregar_flags añade un indicador *_es_nulo por campo sólo si CREAR_FLAGS=True;
#   con False devuelve el SQL sin cambios. Define n_campos_nulos como la cantidad de predictores originales en
#   NULL y materializa la tabla final inicial con el insumo, la cobertura y ese contador. Borra la marca
#   v3_completa, que se vuelve a escribir al final de las validaciones.
def agregar_flags(sql, campos, etapa):
    if not CREAR_FLAGS or not campos:
        return sql
    expresiones = []
    for campo in campos:
        nombre = campo + '_es_nulo'
        expr = f'({identificador(campo)} IS NULL)::UTINYINT'
        expresiones.append(f'{expr} AS {identificador(nombre)}')
        registrar(nombre, etapa, expr, '1 si falta el valor; 0 si está presente. No imputa datos.',
                  'disponibilidad de la variable en la foto actual')
    return 'SELECT *, ' + ', '.join(expresiones) + ' FROM (' + sql + ') valores'

expr_nulos = ' + '.join(f'({identificador(c)} IS NULL)::INTEGER' for c in PREDICTORES)
registrar('n_campos_nulos', TABLA_FINAL, expr_nulos, 'Faltantes en los predictores originales; excluye etiqueta.')
sql_inicio = ('SELECT i.* EXCLUDE (_mes_indice), c.* EXCLUDE (numero_de_cliente, foto_mes), '
              + expr_nulos + ' AS n_campos_nulos FROM fe_04_insumo i '
              'JOIN fe_05_cobertura c USING (numero_de_cliente, foto_mes)')
CANDIDATOS_FLAGS = CAMPOS_HISTORICOS + ['n_observaciones_previas', 'meses_desde_ultima_observacion', 'n_campos_nulos']
CAMPOS_FLAGS = CANDIDATOS_FLAGS.copy() if CREAR_FLAGS else []
sql_inicio = agregar_flags(sql_inicio, CAMPOS_FLAGS, TABLA_FINAL)
materializar(TABLA_FINAL, sql_inicio, ['fe_04_insumo', 'fe_05_cobertura'], N_FILAS)
# La marca final se emite nuevamente sólo después de validar la receta completa.
con.execute("DELETE FROM _fe_etapas WHERE etapa = 'v3_completa'")
con.execute('CHECKPOINT')

# [Anotación · líneas 562–591] Define comprobar (lanza AssertionError si la condición es falsa y anota el
#   control aprobado), iguales y filas_iguales (comparación numérica con tolerancia). Comprueba que las sumas y
#   los extremos estrictos propagan NULL y que ratio_seguro devuelve NULL con faltantes, denominador cero o NaN.
#%% celda 16 [texto]
## 8. Pruebas de lógica temporal y faltantes

Se prueban más de tres meses de historia, huecos de calendario, cambio de año,
faltantes y alteraciones del futuro. Estas pruebas llaman las mismas funciones
que generan los históricos y las reglas de negocio temporales.

#%% celda 17 [código]
comprobaciones = {}
def comprobar(nombre, condicion):
    if not condicion:
        raise AssertionError(nombre)
    comprobaciones[nombre] = True
    print('OK:', nombre, flush=True)

def iguales(a, b):
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(float(a), float(b), rel_tol=1e-8, abs_tol=1e-6)

def filas_iguales(a, b):
    return len(a) == len(b) and all(len(x) == len(y) and all(iguales(u, v) for u, v in zip(x, y))
                                   for x, y in zip(a, b))

comprobar('sumas y extremos propagan NULL', con.execute(
    'SELECT 5 + NULL, mayor_estricto(5, NULL), menor_estricto(NULL, 5)').fetchone() == (None, None, None))
comprobar('ratios: faltantes, cero y no finitos producen NULL', con.execute("""
    SELECT ratio_seguro(NULL, 2), ratio_seguro(2, NULL), ratio_seguro(3, -1+1),
           ratio_seguro('NaN'::DOUBLE, 2), ratio_seguro(4, 2)
""").fetchone() == (None, None, None, None, 2.0))
# [Anotación · líneas 592–609] Crea una tabla temporal de prueba con 4 clientes y meses entre 202010 y 202103,
#   con valores NULL, un hueco de calendario y un cambio de año, y ejecuta sobre ella sql_historicos para el
#   campo x.
con.execute("""
CREATE OR REPLACE TEMP TABLE prueba_historia AS
SELECT *, x AS mcuentas_saldo, x + 1 AS mcaja_ahorro,
       (foto_mes // 100 * 12 + foto_mes % 100)::INTEGER AS _mes_indice
FROM (SELECT numero_de_cliente, foto_mes, x::DOUBLE AS x FROM (VALUES
 (1, 202010, 0.0), (1, 202011, 10.0), (1, 202012, 20.0), (1, 202101, 30.0),
 (1, 202102, 999.0), (1, 202103, NULL),
 (2, 202011, 10.0), (2, 202012, NULL), (2, 202101, 30.0), (2, 202102, 40.0),
 (3, 202011, 10.0), (3, 202101, 30.0), (3, 202102, 40.0),
 (4, 202012, 0.0), (4, 202101, 5.0)
) t(numero_de_cliente, foto_mes, x)) datos
""")
orden = ' ORDER BY numero_de_cliente, foto_mes'
consulta_prueba = sql_historicos('prueba_historia', ['x'])
cur = con.execute(consulta_prueba + orden)
nombres_prueba = [c[0] for c in cur.description]
filas_prueba = cur.fetchall()
prueba = {(r[0], r[1]): dict(zip(nombres_prueba, r)) for r in filas_prueba}
# [Anotación · líneas 610–632] Comprueba sobre la tabla de prueba: que los acumulados usan todas las
#   observaciones anteriores y excluyen la actual; que con un valor previo hay media, mínimo y máximo y la
#   pendiente requiere dos; que un NULL anterior anula los acumulados; que con huecos los lags usan el mes
#   calendario exacto; que el delta es NULL si el valor actual es NULL; y que salen siete históricos por campo.
p = prueba[(1, 202102)]
comprobar('acumulados usan más de tres meses, excluyen el actual y cruzan el año',
          p['x_media_hist_prev'] == 15 and p['x_min_hist_prev'] == 0
          and p['x_max_hist_prev'] == 30 and iguales(p['x_pendiente_hist_prev'], 10)
          and p['x_delta_1'] == 969)
comprobar('un valor previo permite media, min y max; pendiente requiere dos',
          prueba[(1, 202011)]['x_media_hist_prev'] == 0
          and prueba[(1, 202011)]['x_pendiente_hist_prev'] is None
          and iguales(prueba[(1, 202012)]['x_pendiente_hist_prev'], 10))
comprobar('un NULL anterior invalida todos los acumulados de ese campo',
          all(prueba[(2, 202102)][f'x_{s}_hist_prev'] is None
              for s in ['media', 'min', 'max', 'pendiente']))
comprobar('huecos: lags calendario exactos, acumulados sobre filas existentes',
          prueba[(3, 202101)]['x_lag_1'] is None
          and prueba[(3, 202101)]['x_lag_2'] == 10
          and prueba[(3, 202102)]['x_media_hist_prev'] == 20
          and iguales(prueba[(3, 202102)]['x_pendiente_hist_prev'], 10))
comprobar('actual NULL: delta NULL y media del pasado completo válida',
          prueba[(1, 202103)]['x_delta_1'] is None
          and iguales(prueba[(1, 202103)]['x_media_hist_prev'], (0+10+20+30+999)/5))
comprobar('siete históricos por campo; no lag_3 ni variacion_1',
          len(nombres_prueba) == 9 and 'x_lag_3' not in nombres_prueba
          and 'x_variacion_1' not in nombres_prueba)
# [Anotación · líneas 633–650] Comprueba saldo_mean, ingresos y util_saldo en un caso conocido, y que los
#   históricos de los meses hasta 202101 no cambian al quitar los meses posteriores ni al alterar sus valores.
#   Elimina las tablas de prueba.
negocio_prueba = con.execute(sql_negocio_temporal('prueba_historia') + orden).fetchall()
negocio_febrero = next(r for r in negocio_prueba if r[:2] == (1, 202102))
comprobar('saldo_mean, ingresos y util_saldo se calculan sólo con el pasado',
          filas_iguales([negocio_febrero], [(1, 202102, 15, 31, 15/32)]))
con.execute('CREATE OR REPLACE TEMP TABLE prueba_truncada AS '
            'SELECT * FROM prueba_historia WHERE foto_mes <= 202101')
pasado = [r for r in filas_prueba if r[1] <= 202101]
negocio_pasado = [r for r in negocio_prueba if r[1] <= 202101]
comprobar('agregar futuro no modifica históricos ni reglas temporales previas',
          filas_iguales(pasado, con.execute(sql_historicos('prueba_truncada', ['x']) + orden).fetchall())
          and filas_iguales(negocio_pasado, con.execute(sql_negocio_temporal('prueba_truncada') + orden).fetchall()))
con.execute('UPDATE prueba_historia SET x=-123456789, mcuentas_saldo=-98765, mcaja_ahorro=88888 '
            'WHERE foto_mes > 202101')
comprobar('alterar futuro no modifica históricos ni reglas temporales previas',
          filas_iguales(pasado, [r for r in con.execute(consulta_prueba + orden).fetchall() if r[1] <= 202101])
          and filas_iguales(negocio_pasado, [r for r in con.execute(sql_negocio_temporal('prueba_historia') + orden).fetchall() if r[1] <= 202101]))
for tabla in ['prueba_historia', 'prueba_truncada']:
    con.execute(f'DROP TABLE {tabla}')

# [Anotación · líneas 652–683] Recorre CAMPOS_HISTORICOS de a 2 campos: para cada bloque registra las
#   definiciones en el diccionario, materializa la tabla fe_06_hist_NNN con los siete históricos de cada campo y
#   la incorpora a la tabla final con incorporar_bloque. Al terminar imprime filas, columnas totales, columnas
#   nuevas, históricos y flags.
#%% celda 18 [texto]
## 9. Históricos por bloques persistentes

Cada bloque procesa dos campos del insumo completo. Sus siete históricos se
guardan en `fe_06_hist_NNN`; los flags sólo se agregan si `CREAR_FLAGS=True`.
Luego se incorporan esas columnas a la tabla final mediante un único JOIN con
ese bloque. Se confirma y se hace CHECKPOINT antes de continuar. Las columnas
anteriores se conservan. Con `False`, ningún bloque crea columnas `*_es_nulo`.

#%% celda 19 [código]
TABLAS_HISTORICAS = []
for inicio in range(0, len(CAMPOS_HISTORICOS), CAMPOS_POR_BLOQUE):
    campos = CAMPOS_HISTORICOS[inicio:inicio+CAMPOS_POR_BLOQUE]
    tabla = f'fe_06_hist_{inicio // CAMPOS_POR_BLOQUE + 1:03d}'
    definiciones = expresiones_historicas(campos)
    for c in campos:
        definiciones[c + '_delta_1'] = f'{identificador(c)} - {identificador(c + "_lag_1")}'
    for nombre, expr in definiciones.items():
        registrar(nombre, tabla, expr, 'Ver definición del sufijo; propagación estricta de NULL.',
                  'actual y t-1' if nombre.endswith('_delta_1') else 'sólo observaciones anteriores')
    sql = agregar_flags(sql_historicos('fe_04_insumo', campos), list(definiciones), tabla)
    materializar(tabla, sql, ['fe_04_insumo'], N_FILAS)
    incorporar_bloque(tabla)
    TABLAS_HISTORICAS.append(tabla)
    if CREAR_FLAGS:
        CAMPOS_FLAGS.extend(definiciones)
    print(f'Avance: {min(inicio+CAMPOS_POR_BLOQUE, len(CAMPOS_HISTORICOS))}/{len(CAMPOS_HISTORICOS)} campos', flush=True)

columnas_finales = [c for c, _ in esquema(TABLA_FINAL)]
nuevas = [c for c in columnas_finales if c not in columnas_originales]
print('Filas:', N_FILAS, '| Columnas:', len(columnas_finales), '| Nuevas:', len(nuevas))
print('Históricos:', len(CAMPOS_HISTORICOS)*7, '| Flags:', len(CAMPOS_FLAGS))

# [Anotación · líneas 685–696] Celda de texto: describe los controles sobre la tabla final y la verificación
#   de todos los históricos contra un cálculo independiente en Python para una muestra de 24 clientes.
#%% celda 20 [texto]
## 10. Validación completa y referencia independiente

Se comprueban filas, claves, conservación de originales y etiqueta, cobertura del
diccionario y cumplimiento de `CREAR_FLAGS`. Con `False`, se comprueba
que ninguna tabla de la base contenga columnas `*_es_nulo`. Los controles de muchas columnas se
dividen en grupos para no construir expresiones excesivamente grandes.

Para una muestra determinista de 24 clientes se verifican todos los históricos
contra cálculos independientes en Python. La pendiente usa coordenadas mensuales
centradas; no supone tres meses ni distancias consecutivas. Las reglas nuevas se
contrastan con sus insumos originales en esa misma muestra.

# [Anotación · líneas 698–729] Controla sobre la tabla final: cantidad de filas, claves únicas, presencia de
#   los siete históricos de cada campo, ausencia de lag_3 y variacion_1, que claves y etiqueta no se usen como
#   entradas históricas, que el diccionario cubra las columnas nuevas, que no existan columnas *_es_nulo con
#   CREAR_FLAGS=False y que la cantidad de columnas sea 8 por campo + 2 claves + etiqueta + 3 auxiliares.
#%% celda 21 [código]
comprobar('tabla final conserva filas', con.execute(f'SELECT count(*) FROM {identificador(TABLA_FINAL)}').fetchone()[0] == N_FILAS)
comprobar('claves únicas en tabla final', con.execute(f"""
    SELECT count(*) FROM (SELECT numero_de_cliente, foto_mes FROM {identificador(TABLA_FINAL)}
                         GROUP BY numero_de_cliente, foto_mes HAVING count(*) != 1)
""").fetchone()[0] == 0)
comprobar('todos los originales, negocios y ratios tienen siete históricos',
          all(c + sufijo in columnas_finales for c in CAMPOS_HISTORICOS
              for sufijo in ['_lag_1', '_lag_2', '_delta_1', '_media_hist_prev', '_min_hist_prev', '_max_hist_prev', '_pendiente_hist_prev']))
comprobar('no existen lag_3 ni variacion_1',
          not any(c.endswith(('_lag_3', '_variacion_1')) for c in columnas_finales))
comprobar('no se usan claves, etiqueta ni flags como entradas históricas',
          not (set(CLAVES + [OBJETIVO, '_mes_indice']) & set(CAMPOS_HISTORICOS))
          and not any(c.endswith('_es_nulo') for c in CAMPOS_HISTORICOS))
comprobar('diccionario cubre exactamente las columnas nuevas',
          len(diccionario) == len(nuevas) and {r['variable'] for r in diccionario} == set(nuevas))
flags_finales = {c for c in columnas_finales if c.endswith('_es_nulo')}
if CREAR_FLAGS:
    comprobar('flags cubren todas las variables originales y calculadas sin recursión',
              len(CAMPOS_FLAGS) == len(set(CAMPOS_FLAGS))
              and {c + '_es_nulo' for c in CAMPOS_FLAGS} == flags_finales
              and set(CAMPOS_FLAGS) == set(columnas_finales) - set(CLAVES + [OBJETIVO]) - flags_finales)
else:
    comprobar('CREAR_FLAGS=False: ninguna tabla contiene indicadores _es_nulo',
              not CAMPOS_FLAGS and not flags_finales
              and con.execute("SELECT count(*) FROM information_schema.columns "
                              "WHERE table_schema = 'main' AND right(column_name, 8) = '_es_nulo'").fetchone()[0] == 0)
    comprobar('CREAR_FLAGS=False: diccionario sin indicadores _es_nulo',
              not any(r['variable'].endswith('_es_nulo') for r in diccionario))
columnas_sin_flags = len(CAMPOS_HISTORICOS)*8 + len(CLAVES) + 1 + 3
comprobar('cantidad de columnas corresponde a históricos, auxiliares y flags elegidos',
          len(columnas_finales) == columnas_sin_flags + len(CAMPOS_FLAGS))

# [Anotación · líneas 731–752] huella_columnas calcula por mes el conteo de filas y dos agregados de un hash
#   de las columnas indicadas. Con esa huella verifica que las columnas originales y la etiqueta sean iguales en
#   fe_00_base y en la tabla final. Si hay flags, controla que coincidan con los NULL. Luego cuenta, de a 40
#   columnas, valores infinitos o NaN en las columnas nuevas y exige que sean cero.
def huella_columnas(tabla, columnas):
    # Dos agregados del hash y el conteo por mes; no requieren ordenar las filas.
    expr = 'hash(' + ','.join(identificador(c) for c in columnas) + ')'
    return con.execute(f'SELECT foto_mes, count(*), sum({expr}::HUGEINT), bit_xor({expr}) '
                       f'FROM {identificador(tabla)} GROUP BY foto_mes ORDER BY foto_mes').fetchall()

comprobar('originales y etiqueta conservados: huellas por mes',
          huella_columnas('fe_00_base', columnas_originales) == huella_columnas(TABLA_FINAL, columnas_originales))
if CREAR_FLAGS:
    errores_flags = 0
    for inicio in range(0, len(CAMPOS_FLAGS), 40):
        condiciones = ' OR '.join(
            f'{identificador(c + "_es_nulo")} IS DISTINCT FROM ({identificador(c)} IS NULL)::UTINYINT'
            for c in CAMPOS_FLAGS[inicio:inicio+40])
        errores_flags += con.execute(f'SELECT count(*) FROM {identificador(TABLA_FINAL)} WHERE {condiciones}').fetchone()[0]
    comprobar('todos los flags coinciden con los NULL de sus variables', errores_flags == 0)
no_finitos = 0
for inicio in range(0, len(nuevas), 40):
    condiciones = ' OR '.join(f'({identificador(c)} IS NOT NULL AND NOT isfinite({identificador(c)}::DOUBLE))'
                              for c in nuevas[inicio:inicio+40])
    no_finitos += con.execute(f'SELECT count(*) FROM {identificador(TABLA_FINAL)} WHERE {condiciones}').fetchone()[0]
comprobar('nuevas sin infinito ni NaN flotante; faltantes representados como NULL', no_finitos == 0)

# [Anotación · líneas 754–789] Toma los 24 clientes de menor numero_de_cliente y trae sus filas del insumo y
#   de la tabla final. Define funciones de referencia en Python: suma_estricta, dividir y acumulados_python
#   (media, mínimo, máximo y pendiente por mínimos cuadrados con el mes centrado; devuelve None si falta algún
#   valor previo).
ids = [r[0] for r in con.execute('SELECT DISTINCT numero_de_cliente FROM fe_00_base '
                                'ORDER BY numero_de_cliente LIMIT 24').fetchall()]
filtro = ','.join(str(int(c)) for c in ids)
def muestra(tabla):
    cur = con.execute(f'SELECT * FROM {identificador(tabla)} WHERE numero_de_cliente IN ({filtro}) '
                      'ORDER BY numero_de_cliente, foto_mes')
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]

insumos_muestra = muestra('fe_04_insumo')
salidas_muestra = muestra(TABLA_FINAL)
por_cliente = {}
for fila in insumos_muestra:
    por_cliente.setdefault(fila['numero_de_cliente'], []).append(fila)
por_clave = {(r['numero_de_cliente'], r['foto_mes']): r for r in salidas_muestra}

def suma_estricta(valores):
    return None if any(v is None for v in valores) else sum(valores)

def dividir(a, b):
    if a is None or b is None or b == 0:
        return None
    valor = a/b
    return valor if math.isfinite(valor) else None

def acumulados_python(previos, campo):
    valores = [r[campo] for r in previos]
    if not valores or any(v is None for v in valores):
        return dict(media=None, min=None, max=None, pendiente=None)
    media = math.fsum(valores)/len(valores)
    pendiente = None
    if len(valores) >= 2:
        xs = [r['_mes_indice'] for r in previos]
        centro = math.fsum(xs)/len(xs)
        pendiente = math.fsum((x-centro)*(y-media) for x, y in zip(xs, valores))/math.fsum((x-centro)**2 for x in xs)
    return dict(media=media, min=min(valores), max=max(valores), pendiente=pendiente)

# [Anotación · líneas 791–834] Para cada cliente de la muestra y cada mes recalcula en Python lag_1, lag_2,
#   delta_1 y los cuatro acumulados de cada campo y los compara con la tabla final. También compara las sumas de
#   negocio, saldo_mean, ingresos, util_saldo, balance_net y ocho ratios con sus insumos originales. Cuenta las
#   comparaciones realizadas.
total_comparaciones = 0
for cliente, filas in por_cliente.items():
    calendario = {r['_mes_indice']: r for r in filas}
    for i, actual in enumerate(filas):
        salida = por_clave[(cliente, actual['foto_mes'])]
        anteriores = filas[:i]
        for campo in CAMPOS_HISTORICOS:
            lag1 = calendario.get(actual['_mes_indice']-1, {}).get(campo)
            lag2 = calendario.get(actual['_mes_indice']-2, {}).get(campo)
            delta = actual[campo]-lag1 if actual[campo] is not None and lag1 is not None else None
            esperados = {campo+'_lag_1': lag1, campo+'_lag_2': lag2, campo+'_delta_1': delta}
            esperados.update({campo+'_'+k+'_hist_prev': v for k, v in acumulados_python(anteriores, campo).items()})
            for nombre, esperado in esperados.items():
                assert iguales(salida[nombre], esperado), (cliente, actual['foto_mes'], nombre, salida[nombre], esperado)
                total_comparaciones += 1
        for nombre, campos in SUMAS_NEGOCIO.items():
            assert iguales(actual[nombre], suma_estricta([actual[c] for c in campos])), nombre
        media_saldo = acumulados_python(anteriores, 'mcuentas_saldo')['media']
        max_caja = acumulados_python(anteriores, 'mcaja_ahorro')['max']
        assert iguales(actual['saldo_mean'], media_saldo)
        assert iguales(actual['ingresos'], max_caja)
        assert iguales(actual['util_saldo'], dividir(media_saldo, max_caja+1 if max_caja is not None else None))
        # Fórmulas adicionales contrastadas con sus componentes originales.
        esperado_balance = (actual['mpasivos_margen'] - actual['mactivos_margen']
                            if actual['mpasivos_margen'] is not None and actual['mactivos_margen'] is not None else None)
        assert iguales(actual['balance_net'], esperado_balance)
        esperados_ratios = {
            'fee_load': (actual['mcomisiones'], suma_estricta([actual['mcomisiones'], actual['mrentabilidad'], 1])),
            'fees_per_tx': (actual['mcomisiones'], suma_estricta([actual['ctrx_quarter'], 1])),
            'rent_per_tx': (actual['mrentabilidad'], suma_estricta([actual['ctrx_quarter'], 1])),
            'util_visa': (actual['Visa_msaldototal'], suma_estricta([actual['Visa_mfinanciacion_limite'], 1])),
            'util_master': (actual['Master_msaldototal'], suma_estricta([actual['Master_mfinanciacion_limite'], 1])),
            '%_pago_minimo': (suma_estricta([actual['Visa_mpagominimo'], actual['Master_mpagominimo']]),
                              suma_estricta([actual['Visa_mpagado'], actual['Master_mpagado'], 1])),
            'cash_advance_share': (suma_estricta([actual['Visa_cadelantosefectivo'], actual['Master_cadelantosefectivo']]),
                                   suma_estricta([actual['Visa_cconsumos'], actual['Master_cconsumos'], 1])),
            'share_usd': (suma_estricta([actual['Visa_mconsumosdolares'], actual['Master_mconsumosdolares']]),
                          suma_estricta([actual['Visa_mconsumototal'], actual['Master_mconsumototal'], 1])),
        }
        for nombre, (a, b) in esperados_ratios.items():
            assert iguales(actual[nombre], dividir(a, b)), nombre
comprobar('todos los históricos contrastados con referencia independiente en 24 clientes', total_comparaciones > 0)
comprobar('sumas y nuevas reglas de negocio contrastadas con insumos originales', True)
print('Comparaciones históricas independientes:', total_comparaciones)

# [Anotación · líneas 836–845] Escribe el diccionario de variables en competencia_01_fe_v3_diccionario.csv y
#   en la tabla _fe_diccionario de la base.
campos_diccionario = ['variable', 'etapa', 'expresion_sql', 'descripcion', 'temporalidad']
with (CARPETA_FE / 'competencia_01_fe_v3_diccionario.csv').open('w', encoding='utf-8-sig', newline='') as archivo:
    escritor = csv.DictWriter(archivo, fieldnames=campos_diccionario)
    escritor.writeheader()
    escritor.writerows(diccionario)
con.execute('CREATE OR REPLACE TABLE _fe_diccionario ('
            'variable VARCHAR, etapa VARCHAR, expresion_sql VARCHAR, descripcion VARCHAR, temporalidad VARCHAR)')
con.executemany('INSERT INTO _fe_diccionario VALUES (?, ?, ?, ?, ?)',
                [[r[c] for c in campos_diccionario] for r in diccionario])
con.execute('CHECKPOINT')

# [Anotación · líneas 847–879] Exporta la tabla final a un CSV parcial con COPY (NULL como campo vacío), lo
#   relee con el esquema exacto y compara sus huellas por mes con las de la base; si coinciden lo renombra a
#   competencia_01_fe_v3.csv. Registra la marca v3_completa, cierra la base y la reabre en sólo lectura para
#   comprobar filas, esquema y marca.
#%% celda 22 [texto]
## 11. CSV final y cierre de la base

La exportación es directa, sin pandas y sin ordenar globalmente las filas. Se
verifica el CSV completo con el esquema exacto y huellas por mes de todas las
columnas. Luego se publica el `.csv` y se marca la tabla como completa.
La base se cierra y se reabre para comprobar que las tablas persisten.

#%% celda 23 [código]
if EXPORTAR_CSV:
    parcial = CSV_FINAL.with_suffix('.csv.partial')
    inicio = time.perf_counter()
    print('Exportando CSV...', flush=True)
    con.execute(f"COPY {identificador(TABLA_FINAL)} TO {literal(parcial.as_posix())} (FORMAT CSV, HEADER true, NULL '')")
    tipos_finales = '{' + ', '.join(f'{literal(c)}: {literal(t)}' for c, t in esquema(TABLA_FINAL)) + '}'
    con.execute(f"CREATE OR REPLACE TEMP VIEW csv_verificacion AS SELECT * FROM read_csv("
                f"{literal(parcial.as_posix())}, header=true, delim=',', types={tipos_finales}, nullstr='', parallel=false)")
    print('Verificando CSV completo...', flush=True)
    comprobar('CSV completo: conteos y huellas por mes coinciden con la base',
              huella_columnas(TABLA_FINAL, columnas_finales) == huella_columnas('csv_verificacion', columnas_finales))
    con.execute('DROP VIEW csv_verificacion')
    parcial.replace(CSV_FINAL)
    print('CSV verificado (s):', round(time.perf_counter()-inicio, 1))
guardar_registro('v3_completa', firmas[TABLA_FINAL], TABLA_FINAL, N_FILAS, len(columnas_finales), 0,
                 'Validaciones completas; consultar _fe_diccionario para las fórmulas.')
con.execute('CHECKPOINT')
con.close()
con = duckdb.connect(str(BASE), read_only=True, config={'memory_limit': MEMORIA, 'threads': str(HILOS)})
comprobar('base reabierta: filas, esquema y marca de finalización persisten',
          con.execute(f'SELECT count(*) FROM {identificador(TABLA_FINAL)}').fetchone()[0] == N_FILAS
          and len(esquema(TABLA_FINAL)) == len(columnas_finales)
          and con.execute("SELECT count(*) FROM _fe_etapas WHERE etapa='v3_completa'").fetchone()[0] == 1)
con.close()
# [Anotación · líneas 880–896] Arma un resumen (versión, CREAR_FLAGS, versión de DuckDB, hash del CSV, filas,
#   cantidades de columnas, comparaciones, configuración, tamaños de base y de CSV, controles aprobados) y lo
#   guarda en competencia_01_fe_v3_validacion.json.
resumen = {
    'version': 'v3', 'crear_flags': CREAR_FLAGS,
    'duckdb_version': duckdb.__version__, 'python': sys.executable,
    'fuente_sha256': HUELLA_CSV, 'filas': N_FILAS,
    'originales': len(columnas_originales), 'campos_con_historicos': len(CAMPOS_HISTORICOS),
    'columnas_historicas': len(CAMPOS_HISTORICOS)*7, 'flags': len(CAMPOS_FLAGS),
    'columnas_finales': len(columnas_finales), 'nuevas': len(nuevas),
    'comparaciones_historicas_independientes': total_comparaciones,
    'configuracion': {'crear_flags': CREAR_FLAGS, 'memory_limit': MEMORIA, 'threads': HILOS, 'temp_directory': str(TEMPORALES),
                      'max_temp_directory_size': MAX_TEMPORALES, 'preserve_insertion_order': False},
    'base_bytes': BASE.stat().st_size,
    'csv_bytes': CSV_FINAL.stat().st_size if EXPORTAR_CSV else None,
    'validaciones': comprobaciones,
}
(CARPETA_FE / 'competencia_01_fe_v3_validacion.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in resumen.items() if k != 'validaciones'}, ensure_ascii=False, indent=2))
print('Controles aprobados:', len(comprobaciones))

# [Anotación · líneas 898–929] Celda de texto: muestra cómo consultar la base terminada y declara el resultado
#   de la ejecución con CREAR_FLAGS=False: 983.061 filas, 1.718 columnas, 214 campos con 1.498 históricos, 26
#   controles aprobados y 215.712 comparaciones; base de 7,29 GB y CSV de 7,43 GB.
#%% celda 24 [texto]
## Consulta posterior

La base y el CSV v3 tienen nombres propios. Para consultar desde esta carpeta:

```python
from pathlib import Path
import duckdb
con = duckdb.connect(str(Path.cwd() / 'competencia_01_fe_v3.duckdb'),
                     read_only=True, config={'memory_limit': '1GB', 'threads': '1'})
con.execute("SELECT numero_de_cliente, foto_mes, m_credito_visa, m_credito_visa_media_hist_prev FROM competencia_01_fe_v3 LIMIT 10").fetchall()
con.close()
```

Las salidas nuevas usan el prefijo `competencia_01_fe_v3`. El diccionario cubre
todas las variables calculadas. No es necesario ejecutar el FE para consultar
la base terminada. Para reconstruir, ejecutar todas las celdas en orden; las
firmas evitan mezclar recetas. Sólo consumir la tabla al finalizar las validaciones.

La configuración entregada es `CREAR_FLAGS=False`. Para generar los indicadores,
cambiarla a `True`, activar `REHACER=True` si se usa la misma base, y ejecutar todas
las celdas en orden. Volver a `REHACER=False` después de completar la reconstrucción.
Si se quieren conservar ambas variantes, elegir otras rutas para BASE y CSV_FINAL.

Ver [validaciones](competencia_01_fe_v3_validacion.json),
[recursos](competencia_01_fe_v3_recursos.json),
[diccionario](competencia_01_fe_v3_diccionario.csv) y
[guía de uso](LEEME_Feature_Engineering_v3.md).

**Ejecución verificada con `CREAR_FLAGS=False`:** 983.061 filas, 1.718 columnas y **cero indicadores `*_es_nulo`**. Se mantienen 214 campos con 1.498 históricos. Pasaron los 26 controles, incluidas 215,712 comparaciones históricas independientes, la lectura del CSV completo y la reapertura de la base.

Base: 7.29 GB. CSV: 7.43 GB (unidades decimales).

# [Anotación · líneas 931–953] Celda comentada (no se ejecuta): ejemplo para abrir la base desde una ruta de
#   Windows y pasar a pandas las filas cuyo foto_mes no es 202107 ni 202108.
#%% celda 25 [texto]
PB: para consultar base y pasar a pandas:

#%% celda 26 [código]
# import duckdb

# ruta_db = (
#     r"C:\Users\pedro\OneDrive\Escritorio\MAESTRIA"
#     r"\Especialización 2C 2026\DM_EyF_2026"
#     r"\Clases\Clase 4\FE\competencia_01_fe_v3.duckdb"
# )

# consulta = consulta = """
# SELECT *
# FROM competencia_01_fe_v3
# WHERE foto_mes NOT IN  (202107, 202108)
# """

# with duckdb.connect(ruta_db, read_only=True) as con:
#     df = con.execute(consulta).fetchdf()

# print(df.shape)
# df.head()
````

### competencia01/codigos/LGBM_Workflow_v1_4.ipynb

Notebook de modelado: prepara la clase y la función de ganancia, optimiza hiperparámetros de LightGBM con Optuna, revalida los trials con backtests temporales y particiones pseudo público/privado, entrena el ensamble final de 12 modelos, predice 202108 y exporta los CSV por corte.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] Celda de texto con el plan de la versión 1.4: optimización con Optuna entrenando
#   en abril y mayo y validando en junio; revalidación temporal de los 10 trials de mayor valor (abril→mayo y
#   mayo→junio); validación pseudo público/privado de 5 trials partiendo junio en 25 %/75 %; aumento manual de
#   algunos hiperparámetros para el entrenamiento con abril, mayo y junio; ensamble de semillas. Indica que se
#   elimina ccajas_depositos por tener todo cero en mayo.
#%% celda 1 [texto]
# LGBM Workflow V1.4

- Esta version optimiza abril+mayo y valida en junio. Busca obtener hiperparametros podados. <br>
Workflow: <br>
1) Optimización Optuna con rangos acotados entrenamiento abril+mayo validación en junio.
2) Validación temporal con SSS, mejores 10 trials, 50-50
    - Backtest A: Train Abril y Validación Mayo. Priorizar esta para eleccion.
    - Backest B: Train Mayo y Validación Junio
3) Elegir los 5 mejores trials previos y validarlos con pseudo-public-private particionando Junio en 25-75. 
        - Probar primero 50 splits, si es rapido pasar a 500. 
        - Calcular media de ganancia (total no por mes), desviacion, P10/P25, ranking medio, frecuencia de top-1/top-3, regret. Exponiendo tablas separadas para public y private
        - El regret es max Gain_private_i - max_gain_private* ("¿qué tan peligroso sería confiar en mi leaderboard público?")

- La idea es incorporar revalidacion temporal y particion publico-privado.
- Se elimina ccajas_depositos por tener todo cero en mayo
- Entrenamiento final varia.
- Predicción y exportación: agosto.
4) Aumento manual de algunos hiperparametros para entrenamiento definitivo abril+mayo+junio
        -Podria ser min_sum_hessian_in_leaf, num_boost_round y algunos mas
5) Ensamble de 10 semillas para modelo final. 
        -Tambien podria hacerse ensamble de 2 o 3 mejores configuraciones x 6 semillas
        

# [Anotación · líneas 25–59] Importa pandas, numpy, seaborn, matplotlib, scipy, scikit-learn (árboles,
#   particiones, random forest, imputación, AUC), lightgbm, joblib, optuna con sus gráficos, y utilidades de
#   tiempo y pickle.
#%% celda 2 [texto]
## Librerias y Dataset

#%% celda 3 [código]
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timezone, timedelta

from tqdm.notebook import tqdm

from scipy.stats import gaussian_kde
from scipy.stats import ks_2samp

from sklearn.tree import DecisionTreeClassifier, plot_tree,  _tree
from sklearn.model_selection import train_test_split
from sklearn.model_selection import ShuffleSplit, StratifiedShuffleSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score

import lightgbm as lgb


from joblib import Parallel, delayed

import optuna
from optuna.visualization import plot_optimization_history, plot_param_importances, plot_slice, plot_contour

from time import time
from time import perf_counter

import pickle

# [Anotación · líneas 61–81] Tras una celda comentada, define las rutas de la VM (/home/ds/buckets/b1 y sus
#   subcarpetas datasets, V1/modelos y V1/db), el archivo competencia_01_fe_v3.parquet, la ganancia por acierto
#   (1.072.500) y el costo por estímulo (27.500), y lee el Parquet completo con pandas.
#%% celda 4 [código]
# from pathlib import Path

# print("Directorio de trabajo:", Path.cwd())
# print("Ruta que se intenta leer:",
#       Path("buckets/b1/datasets/competencia_01_fe_v3.parquet").resolve())

#%% celda 5 [código]
base_path = '/home/ds/buckets/b1'
dataset_path = base_path + '/datasets/'
modelos_path = base_path + '/V1/modelos/'
db_path = base_path + '/V1/db/'
dataset_file = 'competencia_01_fe_v3.parquet'
#buckets/b1/datasets/competencia_01_fe_v3.parquet

# Métricas
ganancia_acierto = 1_072_500
costo_estimulo = 27_500

# Dataframe
data = pd.read_parquet(dataset_path + dataset_file)

# [Anotación · líneas 83–94] Fija la semilla 12 para numpy y define una lista de 5 semillas (12, 2000, 2001,
#   2003, 2007). Elimina del dataset todas las columnas cuyo nombre contiene 'ccajas_depositos'.
#%% celda 6 [código]
# Semillas
semilla = 12
np.random.seed(semilla)
semillas = [12, 2000, 2001, 2003, 2007] 

#%% celda 7 [código]
# Se dropean columnas asociadas a ccajas_depositos
data.drop(
    columns=data.columns[data.columns.str.contains('ccajas_depositos', regex=False)],
    inplace=True
)

# [Anotación · líneas 96–109] Crea clase_peso: 1,00002 para BAJA+2, 1,00001 para BAJA+1 y 1,0 para el resto;
#   ese peso permite distinguir las clases al calcular la ganancia. Crea dos etiquetas binarias: clase_binaria1
#   (1 sólo para BAJA+2) y clase_binaria2 (1 para BAJA+1 y BAJA+2).
#%% celda 8 [texto]
## Transformaciones Iniciales

#%% celda 9 [código]
data['clase_peso'] = 1.0

data.loc[data['clase_ternaria'] == 'BAJA+2', 'clase_peso'] = 1.00002
data.loc[data['clase_ternaria'] == 'BAJA+1', 'clase_peso'] = 1.00001 #este es un truco para poder distinguirlos y calcular correctamente la ganancia

#%% celda 10 [código]
data['clase_binaria1'] = 0
data['clase_binaria2'] = 0
data['clase_binaria1'] = np.where(data['clase_ternaria'] == 'BAJA+2', 1, 0)
data['clase_binaria2'] = np.where(data['clase_ternaria'] == 'CONTINUA', 0, 1)

# [Anotación · líneas 111–122] lgb_gan_eval es la métrica que recibe LightGBM: asigna 1.072.500 a las filas
#   con peso 1,00002 (BAJA+2) y −27.500 al resto, ordena por probabilidad descendente, acumula y devuelve el
#   máximo de la curva (con piso 0). La celda de texto indica que el target agrupa BAJA+1 y BAJA+2 y que la
#   ganancia premia sólo BAJA+2.
#%% celda 11 [código]
# Funcion de ganancia que use cursada anterior
def lgb_gan_eval(y_pred, data):
    weight = data.get_weight()
    ganancia = np.where(weight == 1.00002, ganancia_acierto, 0) - np.where(weight < 1.00002, costo_estimulo, 0)
    ganancia = ganancia[np.argsort(-y_pred, kind="stable")]
    ganancia = np.cumsum(ganancia)

    return 'gan_eval', max(0.0, float(np.max(ganancia))), True

#%% celda 12 [texto]
El target de entrenamiento agrupa BAJA+1 y BAJA+2; la ganancia premia solo BAJA+2.

# [Anotación · líneas 124–143] Define los meses de entrenamiento de la optimización (202104 y 202105) y el mes
#   de validación (202106). La función de submuestreo de CONTINUA (fracción 0,30) queda comentada.
#%% celda 13 [texto]
## Deficiniones temporales
Entrenamiento: abril y mayo completo

Validación: junio completo.

#%% celda 14 [código]
# Definición temporal
meses_train = [202104, 202105]
mes_valid = 202106

# fraccion_continua = 0.30

# def muestrear_continua(df, fraccion=0.30, seed=12):
#     bajas = df.loc[df["clase_ternaria"].isin(["BAJA+1", "BAJA+2"])]
#     continua = df.loc[df["clase_ternaria"] == "CONTINUA"].sample(
#         frac=fraccion,
#         random_state=seed,
#     )
#     return pd.concat([bajas, continua]).sort_index()

# [Anotación · líneas 145–167] Separa entrenamiento (202104 y 202105) y validación (202106). X_train quita
#   clase_ternaria, clase_peso y las dos etiquetas binarias; las demás columnas, incluidas numero_de_cliente y
#   foto_mes, quedan como variables. Arma etiquetas y pesos de cada parte e imprime los tamaños.
#%% celda 15 [código]
# Meses de entrenamiento y validación
train_data = data[data['foto_mes'].isin(meses_train)]
val_data = data[data['foto_mes'] == mes_valid]

# # Aplicar una sola vez el muestreo sobre los dos meses combinados.
# train_data = muestrear_continua(
#     train_data_completo, fraccion_continua, semilla
# )

X_train = train_data.drop(['clase_ternaria', 'clase_peso', 'clase_binaria1', 'clase_binaria2'], axis=1)
y_train_binaria1 = train_data['clase_binaria1']
y_train_binaria2 = train_data['clase_binaria2']
w_train = train_data['clase_peso']

X_val = val_data.loc[:, X_train.columns]
y_val_binaria1 = val_data['clase_binaria1']
y_val_binaria2 = val_data['clase_binaria2']
w_val = val_data['clase_peso']

print(f'Meses de entrenamiento: {meses_train}')
print(f'Registros de entrenamiento muestreados: {len(train_data):,}')
print(f'Mes de validación: {mes_valid} | Registros: {len(val_data):,}')

# [Anotación · líneas 169–182] Celda con notas en comentarios para un experimento posterior: dos folds
#   temporales (hasta abril → mayo y hasta mayo → junio) y un learning rate mínimo de 0,05.
#%% celda 16 [texto]
### 1 ) Optimización 

#%% celda 17 [código]
# Para siguiente experimento, incorporar:
# Fold 1
# Train: hasta abril
# Valid: mayo

# Fold 2
# Train: hasta mayo
# Valid: junio

# y poner learning rate minimo en 0.05

# [Anotación · líneas 184–217] Inicio de objective: Optuna propone num_leaves (5 a 200, escala log),
#   feature_fraction (0,2 a 0,4), bagging_fraction (0,2 a 0,6), min_gain_to_split (0,01 a 0,85) y
#   min_sum_hessian_in_leaf (1 a 150, escala log). Quedan fijos learning_rate 0,005, max_bin 31,
#   min_data_in_leaf 0, bagging_freq 1, feature_fraction_bynode 0,20, is_unbalance True, objetivo binario,
#   métrica propia y seed 12.
#%% celda 18 [código]
#Optuna Version V1.4
def objective(trial):

    num_leaves = trial.suggest_int('num_leaves', 5, 200, log=True) #ver de reducir para corrida local
    learning_rate = 0.005 #denicolay
    # min_data_in_leaf = trial.suggest_int('min_data_in_leaf', 50, 3000) #se puede aumentar en entrenamiento final
    feature_fraction = trial.suggest_float('feature_fraction', 0.2, 0.4) #poner por debajo de 0.5 para mayor velocidad
    bagging_fraction = trial.suggest_float('bagging_fraction', 0.2, 0.6) #revisar
    min_gain_to_split = trial.suggest_float('min_gain_to_split', 0.01, 0.85) #corta splits debiles
    min_sum_hessian_in_leaf = trial.suggest_float('min_sum_hessian_in_leaf',  1.0, 150.0, log=True) #ver valores


    params = { #considerar regularizacion para competencia 2
        'objective': 'binary',
        'metric': 'custom',
        'boosting_type': 'gbdt',
        'first_metric_only': True,
        'boost_from_average': True,
        'feature_pre_filter': False,
        'max_bin': 31, #bajar a 31. Ver si conviene subir en entrenamiento final
        'num_leaves': num_leaves,
        'learning_rate': learning_rate,
        'min_data_in_leaf': 0, #se fija en cero porque hessiano controla las hojas
        'feature_fraction': feature_fraction,
        'bagging_fraction': bagging_fraction,
        'bagging_freq': 1,
        'min_gain_to_split': min_gain_to_split,
        'seed': semilla, #lo modifique a semilla despues de ultima ejecucion
        'verbose': -1,
        'feature_fraction_bynode': 0.20, # denicolay
        'min_sum_hessian_in_leaf': min_sum_hessian_in_leaf,
        'is_unbalance': True
    }
# [Anotación · líneas 218–253] Arma los datasets de LightGBM con clase_binaria2 y clase_peso y entrena hasta
#   15.000 rondas con early stopping de 1.050 rondas (50 + 5 / learning_rate) sobre la ganancia en junio. Toma
#   la ronda de mayor ganancia, la guarda en el trial como best_iter junto con los parámetros completos y
#   devuelve esa ganancia.
    train_dataset = lgb.Dataset(X_train,
                              label=y_train_binaria2, # eligir la clase
                              weight=w_train)
    val_dataset = lgb.Dataset(X_val,
                              label=y_val_binaria2,
                              weight=w_val,
                              reference=train_dataset)

    # Para almacenar los resultados de evaluación
    evals_result = {}

    # Crear el callback para guardar resultados
    record_eval = lgb.record_evaluation(evals_result)

    # Entrenar modelo
    model = lgb.train(
        params,
        train_dataset,
        valid_sets=[val_dataset],
        num_boost_round=15000, #para entrenamiento final, usar best_iteration * aumento% de dataset
       callbacks=[
            lgb.early_stopping(stopping_rounds=int(50 + 5 / learning_rate)),
            record_eval],
        feval=lgb_gan_eval,
    )

    # Acceder a los resultados de validación 
    val_gan_history = evals_result['valid_0']['gan_eval']
    max_gan = max(val_gan_history)
    best_iter = val_gan_history.index(max_gan) + 1

    # Guardamos cual es la mejor iteración del modelo y parametros
    trial.set_user_attr("best_iter", best_iter)
    trial.set_user_attr("params_completos", params.copy())

    return max_gan

# [Anotación · líneas 255–270] Crea (o carga, si ya existe) el estudio
#   V1_4_train202104_202105_valid202106_full_4 en una base SQLite, con dirección maximizar y TPESampler con
#   semilla 12 y 20 trials iniciales, y ejecuta 50 trials.


Path(db_path).mkdir(parents=True, exist_ok=True)
storage_name = "sqlite:///" + db_path + "optimization_lgbm_VM_V1_4.db"
study_name = "V1_4_train202104_202105_valid202106_full_4"

study = optuna.create_study(
    direction="maximize",
    study_name=study_name,
    storage=storage_name,
    sampler=optuna.samplers.TPESampler(seed=semilla, n_startup_trials=20),
    load_if_exists=True,
)

#%% celda 19 [código]
study.optimize(objective, n_trials=50)   #tarda 10min promedio

# [Anotación · líneas 272–294] Pasa los trials a un DataFrame, muestra los 15 de mayor valor, imprime el trial
#   de mayor valor con sus parámetros y grafica la historia de optimización, la importancia de hiperparámetros,
#   los slices y los contornos.
#%% celda 20 [código]
# Guardar historial de trials
df_trials = study.trials_dataframe()

#%% celda 21 [código]
# Ver historial de trials:
df_trials.sort_values(by='value', ascending=False).head(15)

#%% celda 22 [código]
print(study.best_trial)
print(study.best_params)

#%% celda 23 [código]
optuna.visualization.plot_optimization_history(study)

#%% celda 24 [código]
plot_param_importances(study)

#%% celda 25 [código]
plot_slice(study)

#%% celda 26 [código]
plot_contour(study)

# [Anotación · líneas 296–328] Reentrena un modelo con los parámetros y el best_iter del trial de mayor valor
#   sobre abril y mayo y muestra las 30 variables de mayor importancia por gain (tabla con gain y split, y
#   gráfico). La celda de texto siguiente anota probar eliminando las últimas 700 columnas por importancia.
#%% celda 27 [código]
# Feature Importance
best_trial = study.best_trial
params = best_trial.user_attrs["params_completos"].copy()
params.update(study.best_params)

modelo_importancia = lgb.train(
    params,
    lgb.Dataset(X_train, label=y_train_binaria2, weight=w_train),
    num_boost_round=int(best_trial.user_attrs["best_iter"]),
)

importancias = pd.DataFrame({
    "variable": modelo_importancia.feature_name(),
    "gain": modelo_importancia.feature_importance(importance_type="gain"),
    "split": modelo_importancia.feature_importance(importance_type="split"),
}).sort_values("gain", ascending=False)

display(importancias.head(30))

lgb.plot_importance(
    modelo_importancia,
    importance_type="gain",
    max_num_features=30,
    figsize=(10, 10),
    title=f"Feature importance — Trial {best_trial.number}",
    xlabel="Gain",
    ylabel="Variable",
)
plt.show()

#%% celda 28 [texto]
Probar dropeando las ultimas 700 columnas for feature importance
# [Anotación · líneas 329–357] Selecciona los 10 trials completos de mayor valor (top_trials), arma un
#   diccionario de trials por número y guarda la lista de columnas del modelo. Fija 5 repeticiones y fracción de
#   entrenamiento 0,5 para la revalidación; la celda de texto previa menciona 70 %.

#%% celda 29 [texto]
### 2) Revalidación temporal con SSS — preparación

#%% celda 30 [texto]
Se seleccionan los diez mejores trials de Optuna. Cada repetición entrena sobre el **70 %**
del mes de origen, estratificando por las tres clases; el 30 % restante se descarta.
El mes siguiente se evalúa completo. Los modelos conservan sus parámetros y `best_iter`,
sin early stopping adicional. El dataset de entrenamiento se construye una vez por repetición. No se construyen datasets de validación.

#%% celda 31 [código]
# Selección de trials y definición de split y partición
from time import perf_counter

top_trials = sorted(
    [t for t in study.trials
     if t.state == optuna.trial.TrialState.COMPLETE and t.value is not None],
    key=lambda t: t.value,
    reverse=True,
)[:10]

trials_por_numero = {
    t.number: t for t in study.trials
    if t.state == optuna.trial.TrialState.COMPLETE
}
columnas_modelo = X_train.columns.tolist()
n_splits_temporal = 5
fraccion_train_sss = 0.5


# [Anotación · líneas 359–384] ganancias_individuales asigna 1.072.500 a BAJA+2 y −27.500 al resto.
#   mejor_ganancia_ordenada recibe ganancias ya ordenadas y devuelve el máximo de la curva acumulada (incluido
#   el caso de cero envíos) y su posición. resumen_ganancias agrega por trial media, desvío, P10, P25, mínimo,
#   máximo y repeticiones, y ordena por media descendente y desvío ascendente.
def ganancias_individuales(clases):
    return np.where(
        np.asarray(clases) == "BAJA+2", ganancia_acierto, -costo_estimulo
    ).astype(np.float64)


def mejor_ganancia_ordenada(ganancias):
    curva = np.r_[0.0, np.cumsum(ganancias)]
    corte = int(np.argmax(curva))
    return float(curva[corte]), corte


def resumen_ganancias(df):
    return (
        df.groupby("trial")
        .agg(
            ganancia_media=("ganancia", "mean"),
            ganancia_std=("ganancia", "std"),
            ganancia_p10=("ganancia", lambda x: x.quantile(0.10)),
            ganancia_p25=("ganancia", lambda x: x.quantile(0.25)),
            ganancia_min=("ganancia", "min"),
            ganancia_max=("ganancia", "max"),
            repeticiones=("ganancia", "size"),
        )
        .sort_values(["ganancia_media", "ganancia_std"], ascending=[False, True])
    )


# [Anotación · líneas 387–412] evaluar_backtest_sss toma el mes de origen y el mes de destino completos. Con
#   StratifiedShuffleSplit (5 repeticiones, 50 % de entrenamiento, semilla 12, estratificado por clase_ternaria)
#   arma en cada repetición un dataset de LightGBM con la muestra del mes de origen, etiqueta clase_binaria2 y
#   peso clase_peso.
def evaluar_backtest_sss(mes_origen, mes_destino, nombre):
    origen = data.loc[data["foto_mes"] == mes_origen]
    X_destino = data.loc[data["foto_mes"] == mes_destino, columnas_modelo]
    ganancias_destino = ganancias_individuales(
        data.loc[data["foto_mes"] == mes_destino, "clase_ternaria"]
    )
    sss = StratifiedShuffleSplit(
        n_splits=n_splits_temporal,
        train_size=fraccion_train_sss,
        random_state=semilla,
    )
    resultados = []
    for fold, (idx_train, _) in enumerate(
        sss.split(origen, origen["clase_ternaria"]), start=1
    ):
        inicio_fold = perf_counter()
        train_fold = origen.iloc[idx_train]
        ds_train = lgb.Dataset(
            train_fold.loc[:, columnas_modelo],
            label=train_fold["clase_binaria2"],
            weight=train_fold["clase_peso"],
            params=top_trials[0].user_attrs["params_completos"].copy(),
        )
        ds_train.construct()
        n_train = len(train_fold)
        del train_fold

# [Anotación · líneas 414–447] En cada repetición entrena los 10 trials con sus parámetros y su best_iter, sin
#   early stopping, predice el mes de destino completo, ordena por probabilidad y registra la ganancia máxima de
#   la curva y su corte. Devuelve el detalle por trial y repetición y el resumen por trial.
        for trial in top_trials:
            inicio_trial = perf_counter()
            params_trial = trial.user_attrs["params_completos"].copy()
            rondas = int(trial.user_attrs["best_iter"])
            modelo = lgb.train(
                params_trial, ds_train,
                num_boost_round=rondas, keep_training_booster=True,
            )
            pred = modelo.predict(X_destino, num_iteration=rondas)
            orden = np.argsort(-pred, kind="stable")
            ganancia, corte = mejor_ganancia_ordenada(ganancias_destino[orden])
            resultados.append({
                "trial": trial.number, "fold": fold, "backtest": nombre,
                "mes_train": mes_origen, "mes_valid": mes_destino,
                "best_iter": rondas, "n_train": n_train,
                "n_valid": len(X_destino), "ganancia": ganancia,
                "mejor_corte": corte,
            })
            del modelo, pred, orden
            print(
                f"{nombre} | Repetición {fold}/{n_splits_temporal} | "
                f"Trial {trial.number} | Ganancia: ${ganancia:,.0f} | "
                f"{(perf_counter() - inicio_trial) / 60:.1f} min",
                flush=True,
            )

        del ds_train
        print(
            f"{nombre} | Repetición {fold}/{n_splits_temporal} completada | "
            f"{(perf_counter() - inicio_fold) / 60:.1f} min",
            flush=True,
        )
    detalle = pd.DataFrame(resultados)
    return detalle, resumen_ganancias(detalle)

# [Anotación · líneas 449–467] Ejecuta el backtest A (entrena con muestras de 202104 y evalúa en 202105), que
#   la celda de texto define como criterio principal, y el backtest B (202105 → 202106), y muestra el resumen y
#   el detalle de cada uno.
#%% celda 32 [texto]
#### 2.A Abril -> Mayo - Criterio Principal
Los cinco primeros de `resumen_A` son la propuesta
inicial para el paso 3 (mayor media; menor desvío como desempate).

#%% celda 33 [código]
df_sss_A, resumen_A = evaluar_backtest_sss(202104, 202105, "A: abril → mayo")
display(resumen_A.round(2))
display(df_sss_A)

#%% celda 34 [texto]
#### 2.B Mayo -> Junio - Diagnóstico Complementario
Este bloque puede ejecutarse independientemente de 2A, después de la preparación común.
No modifica la selección de candidatos basada en A.

#%% celda 35 [código]
df_sss_B, resumen_B = evaluar_backtest_sss(202105, 202106, "B: mayo → junio")
display(resumen_B.round(2))
display(df_sss_B)

# [Anotación · líneas 469–490] Une los resúmenes de A y B por trial y dibuja dos boxplots de ganancia por
#   trial, en el orden del resumen A.
#%% celda 36 [código]
# Comparación: conservar el orden de preferencia del backtest A.
comparacion_temporal = resumen_A.add_suffix("_A").join(
    resumen_B.add_suffix("_B")
)
display(comparacion_temporal.round(2))

fig, axes = plt.subplots(1, 2, figsize=(15, 6), constrained_layout=True)
orden_trials = resumen_A.index.tolist()
for ax, detalle, titulo in [
    (axes[0], df_sss_A, "A: abril → mayo"),
    (axes[1], df_sss_B, "B: mayo → junio"),
]:
    valores = [detalle.loc[detalle["trial"] == t, "ganancia"] for t in orden_trials]
    ax.boxplot(valores, vert=False, showmeans=True)
    ax.set_yticks(np.arange(1, len(orden_trials) + 1))
    ax.set_yticklabels([f"Trial {t}" for t in orden_trials])
    ax.invert_yaxis()
    ax.set_title(titulo)
    ax.set_xlabel("Ganancia total ($)")
    ax.grid(axis="x", alpha=0.2)
plt.show()

# [Anotación · líneas 492–519] Tras la celda de texto que define la métrica y el regret, toma como candidatos
#   los 5 primeros trials del resumen A (la lista [55, 78, 53, 25, 80] queda comentada como alternativa) y fija
#   la semilla 12.
#%% celda 37 [texto]
### 3. Pseudo público/privado en junio
Editar `trials_evaluar` para indicar los números de trials deseados. Por defecto se proponen
los cinco mejores de A. Cada candidato se entrena **una vez** con abril + mayo y predice junio.
Las particiones posteriores reutilizan esas predicciones y los rankings precalculados.

No se estratifica junio, mismas particiones
para todos los trials. La métrica mantiene la convención anterior: máximo de la curva de ganancia
en cada subconjunto, incluyendo cero envíos. Por tanto, es un diagnóstico de estabilidad del
ranking de configuraciones con cortes óptimos retrospectivos; no simula un envío con corte fijo
ni la transferencia del corte público al privado. Las ganancias son totales de cada subconjunto.

Para cada partición `s`, se elige `t_publico = argmax_t G_publico(s,t)` y se calcula:

`regret_seleccion(s) = max_t G_privado(s,t) - G_privado(s,t_publico)`.

Las tablas por candidato incluyen además el regret contra el mejor candidato de su propio tablero.
Los empates de ranking se resuelven por número de trial ascendente. Las frecuencias top-1/top-3
son proporciones entre 0 y 1. El pseudo privado reutiliza junio, ya visto por Optuna;
sus resultados no son una estimación independiente de agosto.

#%% celda 38 [código]
# Lista editable: reemplazar por los números de trials que quieras evaluar.
trials_evaluar = resumen_A.head(5).index.astype(int).tolist()
# trials_evaluar = [55, 78, 53, 25, 80]

semilla_pp = semilla
print("Trials para público/privado:", trials_evaluar)

# [Anotación · líneas 521–539] Arma el entrenamiento con 202104 y 202105 completos y los datos de junio
#   (variables, clases y ganancia individual), y construye un único dataset de LightGBM para todos los
#   candidatos.
#%% celda 39 [código]
# Entrenar solo una vez por candidato; no repetir al pasar de 50 a 500 splits.
train_pp = data.loc[data["foto_mes"].isin([202104, 202105])]
X_train_pp = train_pp.loc[:, columnas_modelo]
mascara_junio = data["foto_mes"] == 202106
X_junio = data.loc[mascara_junio, columnas_modelo]
clases_junio = data.loc[mascara_junio, "clase_ternaria"].to_numpy()
ganancias_junio = ganancias_individuales(clases_junio)

params_dataset_pp = trials_por_numero[trials_evaluar[0]].user_attrs["params_completos"].copy()
params_dataset_pp["seed"] = semilla_pp
ds_train_pp = lgb.Dataset(
    X_train_pp,
    label=train_pp["clase_binaria2"],
    weight=train_pp["clase_peso"],
    params=params_dataset_pp,
)
ds_train_pp.construct()
del train_pp, X_train_pp

# [Anotación · líneas 541–564] Para cada candidato entrena una vez con sus parámetros y su best_iter, predice
#   junio y guarda las probabilidades, el orden descendente y las ganancias individuales en ese orden.
predicciones_junio = {}
ordenes_junio = {}
ganancias_ordenadas_junio = {}
for numero_trial in trials_evaluar:
    inicio = perf_counter()
    trial = trials_por_numero[numero_trial]
    params_pp = trial.user_attrs["params_completos"].copy()
    params_pp["seed"] = semilla_pp
    rondas = int(trial.user_attrs["best_iter"])
    modelo = lgb.train(
        params_pp, ds_train_pp,
        num_boost_round=rondas, keep_training_booster=True,
    )
    pred = modelo.predict(X_junio, num_iteration=rondas)
    orden = np.argsort(-pred, kind="stable")
    predicciones_junio[numero_trial] = pred
    ordenes_junio[numero_trial] = orden
    ganancias_ordenadas_junio[numero_trial] = ganancias_junio[orden]
    del modelo
    print(
        f"Trial {numero_trial}: predicciones de junio guardadas | "
        f"{(perf_counter() - inicio) / 60:.1f} min", flush=True,
    )
del ds_train_pp

# [Anotación · líneas 566–610] Genera 1.000 particiones aleatorias de junio con ShuffleSplit (25 % público, 75
#   % privado, semilla 12). En cada partición y para cada candidato calcula la ganancia máxima y el corte en la
#   parte pública y en la privada, filtrando el ranking ya ordenado. Luego calcula por partición el ranking de
#   cada trial en cada tablero, si quedó primero o entre los tres primeros y el regret contra el trial de mayor
#   ganancia del tablero.
#%% celda 40 [código]
# Cambiar solamente este valor a 500 y volver a ejecutar desde esta celda.
from sklearn.model_selection import ShuffleSplit

n_splits_pp = 1000

sss_pp = ShuffleSplit(
    n_splits=n_splits_pp,
    test_size=0.75,  # 25 % público y 75 % privado.
    random_state=semilla,
)

resultados_pp = []
inicio_pp = perf_counter()

for split, (idx_public, idx_private) in enumerate(
    sss_pp.split(X_junio), start=1
):
    es_publico = np.zeros(len(X_junio), dtype=bool)
    es_publico[idx_public] = True
    for numero_trial in trials_evaluar:
        # Filtrar un ranking ya ordenado evita ordenar de nuevo en cada split.
        mascara_ordenada = es_publico[ordenes_junio[numero_trial]]
        ganancias_ordenadas = ganancias_ordenadas_junio[numero_trial]
        gain_public, corte_public = mejor_ganancia_ordenada(
            ganancias_ordenadas[mascara_ordenada]
        )
        gain_private, corte_private = mejor_ganancia_ordenada(
            ganancias_ordenadas[~mascara_ordenada]
        )
        resultados_pp.append({
            "split": split, "trial": numero_trial,
            "gain_public": gain_public, "gain_private": gain_private,
            "corte_public": corte_public, "corte_private": corte_private,
            "n_public": len(idx_public), "n_private": len(idx_private),
        })
    # print(f"Público/privado: partición {split}/{n_splits_pp} completada", flush=True)

df_pp = pd.DataFrame(resultados_pp).sort_values(["split", "trial"])
for tablero in ["public", "private"]:
    grupo = df_pp.groupby("split")[f"gain_{tablero}"]
    df_pp[f"ranking_{tablero}"] = grupo.rank(ascending=False, method="first")
    df_pp[f"top1_{tablero}"] = df_pp[f"ranking_{tablero}"].eq(1)
    df_pp[f"top3_{tablero}"] = df_pp[f"ranking_{tablero}"].le(3)
    df_pp[f"regret_{tablero}"] = grupo.transform("max") - df_pp[f"gain_{tablero}"]


# [Anotación · líneas 613–636] resumir_tablero agrega por trial media, desvío, P10 y P25 de la ganancia,
#   ranking medio, frecuencia de top-1 y top-3, regret medio y P90, ordenado por ranking medio. Muestra la tabla
#   del 25 % público y la del 75 % privado.
def resumir_tablero(tablero):
    return (
        df_pp.groupby("trial")
        .agg(
            ganancia_media=(f"gain_{tablero}", "mean"),
            ganancia_std=(f"gain_{tablero}", "std"),
            ganancia_p10=(f"gain_{tablero}", lambda x: x.quantile(0.10)),
            ganancia_p25=(f"gain_{tablero}", lambda x: x.quantile(0.25)),
            ranking_medio=(f"ranking_{tablero}", "mean"),
            frecuencia_top1=(f"top1_{tablero}", "mean"),
            frecuencia_top3=(f"top3_{tablero}", "mean"),
            regret_medio=(f"regret_{tablero}", "mean"),
            regret_p90=(f"regret_{tablero}", lambda x: x.quantile(0.90)),
        )
        .sort_values(["ranking_medio", "ganancia_media"], ascending=[True, False])
    )


resumen_public = resumir_tablero("public")
resumen_private = resumir_tablero("private")
print("PÚBLICO — ganancia total del 25 %")
display(resumen_public.round(2))
print("PRIVADO — ganancia total del 75 %")
display(resumen_private.round(2))

# [Anotación · líneas 638–660] Para cada partición toma el trial que quedó primero en el público y registra su
#   ganancia y su regret en el privado. Resume media, desvío, mínimo, máximo, P10, P25 y P90, e imprime la
#   frecuencia de particiones con regret positivo y el tiempo.
# Regret de CONFIAR EN EL PÚBLICO: seguir al ganador público al tablero privado.
df_regret = df_pp.loc[df_pp["top1_public"], [
    "split", "trial", "gain_public", "gain_private", "ranking_private", "regret_private"
]].rename(columns={
    "trial": "trial_elegido_publico",
    "gain_private": "ganancia_privada_elegido",
    "regret_private": "regret_seleccion",
}).copy()
df_regret["mejor_ganancia_privada"] = (
    df_regret["ganancia_privada_elegido"] + df_regret["regret_seleccion"]
)
resumen_regret = df_regret[["regret_seleccion", "ganancia_privada_elegido"]].agg(
    ["mean", "std", "min", "max"]
)
resumen_regret.loc["P10"] = df_regret[["regret_seleccion", "ganancia_privada_elegido"]].quantile(0.10)
resumen_regret.loc["P25"] = df_regret[["regret_seleccion", "ganancia_privada_elegido"]].quantile(0.25)
resumen_regret.loc["P90"] = df_regret[["regret_seleccion", "ganancia_privada_elegido"]].quantile(0.90)

print("REGRET — pérdida privada por elegir el ganador público")
display(resumen_regret.round(2))
display(df_regret)
print(f"Frecuencia de regret positivo: {df_regret['regret_seleccion'].gt(0).mean():.1%}")
print(f"Tiempo de particiones y resúmenes: {perf_counter() - inicio_pp:.1f} s")

# [Anotación · líneas 662–694] Tras la celda de texto sobre los ajustes manuales, fija trial_elegido = 78
#   (para la curva de referencia), los meses finales 202104, 202105 y 202106, los trials finales 78 y 25 y las 6
#   semillas 1977, 1978, 2000, 2001, 2003 y 2007. Define los factores 1,5 para min_sum_hessian_in_leaf, 1,1 para
#   las rondas y 1,5 para min_gain_to_split; el diccionario de ajustes adicionales queda vacío.
#%% celda 41 [texto]
### 4. Elección y ajustes manuales del entrenamiento definitivo
La elección por defecto conserva la prioridad de A entre los trials de la lista evaluada.
Las tablas público/privado sirven para revisar esa elección; no se selecciona automáticamente
por el pseudo privado. Editar `trial_elegido` o `trials_finales` para otra decisión.

Los factores comienzan en 1.0: los aumentos son manuales, no proporcionales automáticamente
al tamaño de los datos. `ajustes_params_finales` permite cambiar otros parámetros de LightGBM.
Las rondas se modifican en su variable específica. Los ajustes y el ensamble final no están
revalidados por los resultados previos. El corte de exportación se mantiene manual.

#%% celda 42 [código]
# trial_elegido = int(resumen_A.loc[resumen_A.index.isin(trials_evaluar)].index[0])
trial_elegido = 78 #trial individual para la curva de referencia posterior

meses_train_final = [202104, 202105, 202106]
trials_finales = [78, 25]
semillas_finales = [1977, 1978, 2000, 2001, 2003, 2007]

# Alternativa: dos o tres configuraciones, cada una con seis semillas.
# trials_finales = resumen_A.loc[resumen_A.index.isin(trials_evaluar)].head(3).index.tolist()
# semillas_finales = [12, 2000, 2001, 2003, 2007, 2011]

factor_hessiano_final = 1.5    # Ejemplo: 1.25 aumenta el mínimo un 25 %. En version Abril-Junio utilice 1.5
factor_rondas_final = 1.1      # Ejemplo: 1.20 aumenta las rondas un 20 %. En version Abril-Junio utilice 1.1
factor_gain_final = 1.5   #En version Abril-Junio utilice 1.5
num_boost_round_final = None  # Un entero fija las rondas para todos los trials.
ajustes_params_finales = {
    # "min_data_in_leaf": 500,
    # "min_gain_to_split": 0.7,
    # "learning_rate": 0.005,
    # "min_sum_hessian_in_leaf": 100.0,  # Valor absoluto; prevalece sobre el factor.
}

# [Anotación · líneas 696–715] Para cada trial final copia sus parámetros completos, multiplica
#   min_sum_hessian_in_leaf y min_gain_to_split por sus factores y calcula las rondas como best_iter × 1,1
#   redondeado. Muestra la tabla de configuraciones, los meses, las semillas y la cantidad de modelos (2 × 6 =
#   12).
configuraciones_finales = []
for numero_trial in trials_finales:
    trial = trials_por_numero[numero_trial]
    params_finales = trial.user_attrs["params_completos"].copy()
    params_finales["min_sum_hessian_in_leaf"] *= factor_hessiano_final
    params_finales["min_gain_to_split"] *= factor_gain_final
    params_finales.update(ajustes_params_finales)
    rondas = (
        int(round(trial.user_attrs["best_iter"] * factor_rondas_final))
        if num_boost_round_final is None else int(num_boost_round_final)
    )
    configuraciones_finales.append((numero_trial, params_finales, rondas))

display(pd.DataFrame([
    {"trial": numero, "rondas": rondas, **params}
    for numero, params, rondas in configuraciones_finales
]))
print("Meses finales:", meses_train_final)
print("Semillas:", semillas_finales)
print("Cantidad de modelos:", len(trials_finales) * len(semillas_finales))

# [Anotación · líneas 717–744] Con las predicciones de junio del trial 78 (entrenado con abril y mayo) dibuja
#   con plotly la curva de ganancia acumulada por cantidad de envíos, marca el máximo e imprime ese corte y su
#   ganancia.
#%% celda 43 [texto]
#### Curva de referencia del trial elegido
Se reutilizan las predicciones de junio obtenidas entrenando con abril + mayo.
Esta curva no corresponde al ensamble final ni evalúa un modelo entrenado con junio.
El máximo orienta la elección manual del corte; no sustituye la validación del ensamble.

#%% celda 44 [código]
import plotly.graph_objects as go

pred_val = predicciones_junio[trial_elegido]
orden = ordenes_junio[trial_elegido]
ganancia_acumulada = np.r_[0.0, np.cumsum(ganancias_junio[orden])]
mejor_corte = int(np.argmax(ganancia_acumulada))
mejor_ganancia = float(ganancia_acumulada[mejor_corte])
limite = min(len(pred_val), max(20_000, int(np.ceil(mejor_corte * 1.10))))

fig = go.Figure(go.Scatter(
    x=np.arange(limite + 1), y=ganancia_acumulada[:limite + 1],
    mode="lines", name="Ganancia acumulada",
))
fig.add_vline(x=mejor_corte, line_dash="dash", annotation_text=f"Máximo: {mejor_corte:,}")
fig.update_layout(
    title=f"Junio — trial {trial_elegido}, entrenado en abril + mayo (antes del ensamble)",
    xaxis_title="Cantidad de envíos", yaxis_title="Ganancia total ($)",
    template="plotly_white",
)
fig.show()
print(f"Corte de referencia: {mejor_corte:,} | Ganancia: ${mejor_ganancia:,.0f}")

# [Anotación · líneas 746–781] Arma el entrenamiento final con los meses 202104, 202105 y 202106 (etiqueta
#   clase_binaria2, peso clase_peso), lee competencia_01_fe_v3_Ago.parquet, filtra 202108 y selecciona las
#   mismas columnas del modelo. Define el nombre del ensamble (v1_4_ensamble_t78_25_202104_202105_202106) e
#   inicializa el acumulador de probabilidades. La variable ejecucion_final (fecha y hora en UTC−3) se calcula y
#   no interviene en el nombre.
#%% celda 45 [texto]
### 5. Ensamble final y predicción de agosto

#%% celda 46 [texto]
Se promedian los scores de todos los modelos con el mismo peso. Cada modelo se guarda en
`modelos_path` y se libera después de predecir agosto; no se mantienen todos los árboles en RAM.
Se conserva la ruta de agosto que estaba comentada en el borrador y se activa su lectura.
El manifiesto guarda configuración, semillas, rondas y archivos para reconstruir el ensamble.

#%% celda 47 [código]
import json

train_data_final = data.loc[data["foto_mes"].isin(meses_train_final)]
X_train_final = train_data_final.loc[:, columnas_modelo]
y_train_final = train_data_final["clase_binaria2"]
w_train_final = train_data_final["clase_peso"]

mes_prediccion = 202108
datos_agosto = pd.read_parquet(
    Path(dataset_path) / "competencia_01_fe_v3_Ago.parquet"
)
datos_agosto = datos_agosto.loc[datos_agosto["foto_mes"] == mes_prediccion]
# Seleccionar las variables de entrenamiento también excluye ccajas_depositos de agosto.
X_agosto = datos_agosto.loc[:, columnas_modelo]

Path(modelos_path).mkdir(parents=True, exist_ok=True)
periodo_final = "_".join(str(mes) for mes in meses_train_final)
trials_texto = "_".join(str(t) for t in trials_finales)
ejecucion_final = datetime.now(timezone(timedelta(hours=-3))).strftime("%Y%m%d_%H%M%S_%f")
nombre_ensamble = (
    f"v1_4_ensamble_t{trials_texto}_{periodo_final}"
)

proba_agosto = np.zeros(len(X_agosto), dtype=np.float64)
registros_modelos = []
total_modelos = len(configuraciones_finales) * len(semillas_finales)

# [Anotación · líneas 783–815] Para cada configuración (2) y cada semilla (6): copia los parámetros con esa
#   semilla, construye su propio dataset, entrena las rondas fijadas, suma la predicción de agosto al
#   acumulador, guarda el modelo en un .txt y registra trial, semilla, rondas, árboles entrenados, peso 1/12,
#   archivo y parámetros.
for numero_trial, params_base, rondas in configuraciones_finales:
    for seed in semillas_finales:
        inicio = perf_counter()
        params_modelo = params_base.copy()
        params_modelo["seed"] = int(seed)

        # Dataset propio: permite variar semillas de discretización y parámetros manuales.
        dataset_final = lgb.Dataset(
            X_train_final, label=y_train_final, weight=w_train_final,
            params=params_modelo,
        )
        model_final = lgb.train(
            params_modelo, dataset_final,
            num_boost_round=rondas, keep_training_booster=True,
        )
        proba_agosto += model_final.predict(X_agosto, num_iteration=rondas)
        archivo_modelo = Path(modelos_path) / (
            f"{nombre_ensamble}_trial{numero_trial}_seed{seed}.txt" #nombre de archivo
        )
        model_final.save_model(str(archivo_modelo))
        registros_modelos.append({
            "trial": int(numero_trial), "seed": int(seed),
            "rondas_solicitadas": rondas,
            "arboles_entrenados": model_final.current_iteration(),
            "peso_ensamble": 1 / total_modelos,
            "archivo": str(archivo_modelo), "params": params_modelo,
        })
        del model_final, dataset_final
        print(
            f"Modelo {len(registros_modelos)}/{total_modelos} | "
            f"Trial {numero_trial} | Semilla {seed} | "
            f"{(perf_counter() - inicio) / 60:.1f} min", flush=True,
        )

# [Anotación · líneas 817–835] Divide el acumulado por 12, arma el ranking de agosto ordenado por probabilidad
#   descendente y escribe el manifiesto JSON con el nombre del estudio, los meses de entrenamiento, la lista de
#   columnas y el registro de cada modelo.
proba_agosto /= total_modelos
ranking_agosto = pd.DataFrame({
    "numero_de_cliente": datos_agosto["numero_de_cliente"].to_numpy(),
    "probabilidad": proba_agosto,
}).sort_values("probabilidad", ascending=False, kind="stable").reset_index(drop=True)

archivo_manifiesto = Path(modelos_path) / f"{nombre_ensamble}.json"
archivo_manifiesto.write_text(
    json.dumps({
        "estudio": study.study_name,
        "meses_train_final": meses_train_final,
        "columnas": columnas_modelo,
        "modelos": registros_modelos,
    }, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
display(pd.DataFrame(registros_modelos).drop(columns="params"))
print(f"Manifiesto: {archivo_manifiesto}")
print(f"Clientes de agosto: {len(ranking_agosto):,}")

# [Anotación · líneas 837–855] Define corte_manual = 11.175 y una lista de 19 cortes entre 10.000 y 15.000 que
#   lo incluye, y la carpeta de salida V1/predicciones/V1.4/v1_4_ensemble78_25_full_1 dentro de la ruta de la
#   VM.
#%% celda 48 [texto]
### 6. Exportación Agosto
Se conserva exactamente la carpeta de salida del borrador, aunque su nombre haga referencia
a V1.2/trial56. Los nombres de los archivos identifican el ensamble actual. Se conserva la
convención de exportar solamente los IDs seleccionados, sin encabezado ni índice.
`corte_manual` y la grilla de envíos se mantienen editables con los valores del borrador.

#%% celda 49 [código]
# Exportación: elegir manualmente el corte del ensamble de agosto.
corte_manual=11175
cortes = sorted(set([
    10000, 10500,10700, 10800, 10900, 11000, 11100, 11200, 11300, 11400,
    11500, 12000, 12500, 13000, 13500, 14000, 14500, 15000,
    corte_manual,
]))

# Archivos separados de Desarrollo 1; nombre corto para evitar rutas largas.
carpeta_salida = Path(base_path) / "V1" / "predicciones" / "V1.4" / "v1_4_ensemble78_25_full_1"  #CAMBIAR ULTIMO ARGUMENTO
nombre_modelo = nombre_ensamble


# [Anotación · líneas 858–905] exportar_cortes escribe, para cada corte, un CSV con los numero_de_cliente de
#   los primeros N del ranking, sin encabezado ni índice. El nombre incluye el modelo, la cantidad de envíos y
#   la fecha (UTC−3); el archivo se abre en modo de creación exclusiva y, si ya existe, se prueba con un sufijo
#   numérico. Devuelve la tabla de archivos generados.
def exportar_cortes(ranking, cortes, carpeta, nombre_modelo):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)

    clientes = ranking["numero_de_cliente"]

    # Hora de Argentina (UTC-3).
    fecha = datetime.now(
        timezone(timedelta(hours=-3))
    ).strftime("%Y%m%d")

    archivos = []

    for n_envios in cortes:
        seleccion = clientes.iloc[:n_envios].astype("int64")

        nombre_base = (
            f"{nombre_modelo}"
            f"_{n_envios}_envios"
            f"_{fecha}"
        )

        consecutivo = 0

        while True:
            sufijo = f"_{consecutivo}" if consecutivo else ""
            archivo = carpeta / f"{nombre_base}{sufijo}.csv"

            # Modo "x": crea el archivo solo si no existe.
            try:
                salida = archivo.open(
                    mode="x", encoding="utf-8", newline=""
                )
            except FileExistsError:
                consecutivo += 1
                continue

            with salida:
                seleccion.to_csv(salida, index=False, header=False)

            break

        archivos.append({
            "envios": n_envios,
            "archivo": archivo.name,
        })

    return pd.DataFrame(archivos)


# [Anotación · líneas 908–916] Exporta los 19 cortes del ranking de agosto y muestra la carpeta y los archivos
#   generados.
archivos_generados = exportar_cortes(
    ranking=ranking_agosto,
    cortes=cortes,
    carpeta=carpeta_salida,
    nombre_modelo=nombre_modelo,
)

print(f"Carpeta de salida: {carpeta_salida}")
display(archivos_generados)

# [Anotación · líneas 918–947] Exporta una segunda tanda con 6 cortes (11.125, 11.150, 11.175, 11.225, 11.250
#   y 11.275) en una carpeta con el nombre del ensamble.
#%% celda 50 [código]
# Exportacion con cortes manuales:
# Lista editable de cantidades de clientes a contactar.
cortes_manuales = [
    11125,
    11150,
    11175,
    11225,
    11250,
    11275
]

carpeta_salida = (
    Path(base_path)
    / "V1"
    / "predicciones"
    / "V1.4"
    / nombre_ensamble
)

archivos_generados = exportar_cortes(
    ranking=ranking_agosto,
    cortes=sorted(set(cortes_manuales)),
    carpeta=carpeta_salida,
    nombre_modelo=nombre_ensamble,
)

print(f"Ensamble: {nombre_ensamble}")
print(f"Carpeta de salida: {carpeta_salida}")
display(archivos_generados)
```


## Explicaciones del alumno (texto original)

### competencia01/README.md

> # Competencia 01 — reproducción del proceso
>
> Este entregable contiene el feature engineering, el workflow de LightGBM, el historial de Optuna y los **12 modelos del ensamble final**. Hay dos recorridos:
>
> - **Generar las predicciones de agosto:** cargar los modelos incluidos y promediar sus scores. No requiere Optuna, SSS ni reentrenamiento.
> - **Reconstruir el proceso:** preparar los datos, recuperar o ejecutar Optuna, realizar los backtests y entrenar nuevamente el ensamble.
>
> Los datos de entrada no están incluidos en esta carpeta. Para reproducir las predicciones se necesita el Parquet de agosto con el mismo feature engineering utilizado en el entrenamiento.
>
> ## 1. Archivos incluidos
>
> ```text
> competencia01/
> ├── README.md
> ├── FE/
> │   └── competencia_01_Feature_Engineering_DuckDB_v3.ipynb
> ├── codigos/
> │   └── LGBM_Workflow_v1_4.ipynb
> ├── db/
> │   └── optimization_lgbm_VM_V1_4.db
> └── modelos/
>     ├── v1_4_ensamble_t78_25_202104_202105_202106.json
>     └── ...txt  (12 modelos: trials 78 y 25 × 6 semillas)
> ```
>
> El manifiesto JSON contiene 1.709 nombres de variables en orden, los meses de entrenamiento, los parámetros finales y el peso de cada modelo. Cada `.txt` permite predecir sin reconstruir el entrenamiento.
>
> ## 2. Entorno y dependencias
>
> Preparar un entorno Python con Jupyter y las dependencias de ambas notebooks. Para recrear el entorno de FE se puede usar Python 3.11: la salida guardada utiliza Python 3.11.13 y DuckDB 1.3.2. 
>
> El FE procesa datos en DuckDB con `MEMORIA='1GB'`, `HILOS=1` y hasta `20GB` de temporales. La salida histórica guardada informa aproximadamente 7,29 GB de base y 7,43 GB de CSV. 
>
> ## 3. Datos y rutas
>
> | Archivo necesario | Uso | ¿Incluido? |
> |---|---|---|
> | `competencia_01.csv` | Datos originales completos para generar variables históricas | No |
> | `competencia_01_fe_v3.parquet` | Fotos etiquetadas de abril, mayo y junio de 2021 | No |
> | `competencia_01_fe_v3_Ago.parquet` | Foto de agosto de 2021 con las mismas variables | No |
> | Base de Optuna y modelos finales | Recuperar experimentos y predecir | Sí |
>
> Obtener los datos de la fuente de la competencia. Para reconstruir el FE, conservar toda la historia disponible en el CSV, incluidos los meses intermedios: **filtrar abril–junio y agosto después de calcular las variables históricas**, no antes.
>
> La notebook de modelado conserva las rutas de la VM:
>
> ```python
> base_path = '/home/ds/buckets/b1'
> dataset_path = base_path + '/datasets/'
> modelos_path = base_path + '/V1/modelos/'
> db_path = base_path + '/V1/db/'
> ```
>
> En esa VM, ubicar ambos Parquet en `/home/ds/buckets/b1/datasets/`. En otro entorno, editar esas cuatro asignaciones antes de leer datos.
>
> ### Diferencias del entregable que deben considerarse
>  **Rutas de modelos en el JSON:** apuntan a la VM y a nombres que tenían fecha y hora. Los `.txt` entregados fueron renombrados.
>
>
> ## 4. Recorrido rápido: predecir agosto con los modelos entregados
>
> Ejecutar este bloque en una notebook con el entorno anterior. Solo requiere el manifiesto, los doce `.txt` y el Parquet de agosto. La carga desde archivo está soportada por [`lightgbm.Booster`](https://lightgbm.readthedocs.io/en/stable/pythonapi/lightgbm.Booster.html).
>
> ```python
> from pathlib import Path
> import json
> import numpy as np
> import pandas as pd
> import lightgbm as lgb
>
> ROOT = Path('/ruta/absoluta/competencia01')  # Editar.
> DATASETS = Path('/home/ds/buckets/b1/datasets')  # Editar si corresponde.
>
> archivo_manifiesto = ROOT / 'modelos' / 'v1_4_ensamble_t78_25_202104_202105_202106.json'
> manifiesto = json.loads(archivo_manifiesto.read_text(encoding='utf-8'))
> nombre_ensamble = archivo_manifiesto.stem
>
> datos_agosto = pd.read_parquet(DATASETS / 'competencia_01_fe_v3_Ago.parquet')
> datos_agosto = datos_agosto.loc[datos_agosto['foto_mes'] == 202108]
> X_agosto = datos_agosto.loc[:, manifiesto['columnas']]
> proba_agosto = np.zeros(len(X_agosto), dtype=np.float64)
>
> for registro in manifiesto['modelos']:
>     archivo = next((ROOT / 'modelos').glob(
>         f"*trial{registro['trial']}_seed{registro['seed']}.txt"
>     ))
>     modelo = lgb.Booster(model_file=str(archivo))
>     proba_agosto += registro['peso_ensamble'] * modelo.predict(
>         X_agosto, num_iteration=registro['arboles_entrenados']
>     )
>     print(f"Trial {registro['trial']} | Semilla {registro['seed']}: predicción completa")
>     del modelo
>
> ranking_agosto = pd.DataFrame({
>     'numero_de_cliente': datos_agosto['numero_de_cliente'].to_numpy(),
>     'probabilidad': proba_agosto,
> }).sort_values('probabilidad', ascending=False, kind='stable').reset_index(drop=True)
> ```
>
> Mantener solamente los doce modelos entregados en esa carpeta, o adaptar la selección de archivos si se agregan otras ejecuciones con el mismo trial y semilla. Seleccionar las columnas del manifiesto conserva su orden y excluye las variables `ccajas_depositos`, sin necesidad de regenerar targets para agosto.
>
>
> ## 5. Reconstrucción del feature engineering
>
> Abrir [la notebook de FE](FE/competencia_01_Feature_Engineering_DuckDB_v3.ipynb) y ejecutar las celdas en orden, con `CREAR_FLAGS=False`. La configuración original busca `Datasets/competencia_01.csv` en el directorio actual o sus padres, y escribe en `Clases/Clase 4/FE`.
>
> Para trabajar dentro del entregable, crear `Datasets/`, colocar allí el CSV original y reemplazar las asignaciones de búsqueda de raíz y carpeta de salida de la primera celda de código por:
>
> ```python
> RAIZ = Path('/ruta/absoluta/competencia01')  # Editar.
> CARPETA_FE = RAIZ / 'FE'
> CSV_ORIGEN = RAIZ / 'Datasets' / 'competencia_01.csv'
> ```
>
> Mantener las asignaciones siguientes de `BASE`, `CSV_FINAL` y `TEMPORALES`, que dependen de `CARPETA_FE`. La notebook crea reglas de negocio, ratios, lags de uno y dos meses, deltas y agregados sobre observaciones anteriores del cliente. Los acumulados excluyen la foto actual y propagan faltantes según las fórmulas de la notebook. No activar los indicadores `*_es_nulo` para reproducir esta versión.
>
> `REHACER=False` permite recuperar etapas terminadas en DuckDB. Cambiarlo a `True` solo para recalcular una base existente cuando cambian la receta o los datos. Consumir la tabla final después de completar las validaciones y obtener la marca `v3_completa`.
>
> Las salidas históricas guardadas en la notebook registran 983.061 filas, 1.718 columnas y 26 controles aprobados. 
>
> ### Puente necesario: generar los dos Parquet
>
> La notebook incluida exporta DuckDB y CSV; **no contiene una exportación activa a Parquet**. 
>
> ## 6. Recuperar Optuna y ejecutar el workflow
>
> Abrir [LGBM_Workflow_v1_4.ipynb](codigos/LGBM_Workflow_v1_4.ipynb). Ejecutar los imports, la configuración de rutas, la carga y las transformaciones iniciales. 
>
>
> ### Reutilizar el estudio entregado
>
> Para reproducir la selección histórica, reemplazar la creación de `study` por la carga explícita del estudio ya creado. 
>
> La base contiene tres estudios. El estudio `_full_4` tiene **81 trials completos y 3 fallidos** en la copia entregada; allí existen los trials 78 y 25. Su mejor trial es el 78, con valor de Optuna de $435.765.000.
>
>
> ## 7. Orden de revalidación y entrenamiento final
>
> | Paso de la notebook | Configuración activa | Salida principal |
> |---|---|---|
> | 2. Preparación | Top 10 de Optuna; SSS estratificado, **5 repeticiones y 50 % para entrenamiento** | Funciones y `trials_por_numero` |
> | 2.A | Muestra del 50 % de abril → mayo completo | `df_sss_A`, `resumen_A` |
> | 2.B | Muestra del 50 % de mayo → junio completo | `df_sss_B`, `resumen_B` |
> | Comparación | Prioridad de A | `comparacion_temporal` y boxplots |
> | 3. Candidatos | Cinco mejores de A, lista editable | `trials_evaluar` |
> | 3. Predicciones | Abril + mayo completos → junio; un entrenamiento por candidato | Predicciones de junio |
> | 3. Pseudo público/privado | **1.000 ShuffleSplit sin estratificación**, 25 % público / 75 % privado | Tablas y regret |
> | 4. Configuración final | Trials 78 y 25, ajustes manuales | `configuraciones_finales` |
> | 5. Ensamble | Abril + mayo + junio completos; 12 modelos | Modelos, manifiesto y ranking de agosto |
> | 6. Exportación | Cortes manuales | CSV de IDs |
>
>
> El paso 3 entrena una vez por candidato. Para cambiar la cantidad de particiones, modificar `n_splits_pp` y repetir solo la celda de particionado y resúmenes. En el código entregado, el print por partición está comentado. Para reproducir la comparación concreta discutida durante el desarrollo, se puede fijar la lista comentada `[55, 78, 53, 25, 80]`; para seguir la selección automática actual, mantener `resumen_A.head(5)`.
>
> La curva de referencia del paso 4 requiere que el trial 78 haya sido incluido en `trials_evaluar`, porque reutiliza sus predicciones de junio. Es una curva de un modelo entrenado con abril + mayo, no del ensamble definitivo.
>
> ### Ensamble incluido
>
> | Parámetro | Trial 78 | Trial 25 |
> |---|---:|---:|
> | Rondas de Optuna | 3.194 | 2.780 |
> | Rondas finales: factor 1,1 y redondeo | 3.513 | 3.058 |
> | `num_leaves` | 65 | 47 |
> | `min_sum_hessian_in_leaf` final: factor 1,5 | 210,313113 | 223,427096 |
> | `min_gain_to_split` final: factor 1,5 | 0,708610 | 0,984553 |
> | `learning_rate` | 0,005 | 0,005 |
>
> Semillas para cada configuración: **1977, 1978, 2000, 2001, 2003 y 2007**. Cada uno de los doce modelos pesa `1/12`: se promedian scores, se ordenan de mayor a menor y se eligen los primeros N clientes. No se votan clases ni se promedian ganancias.
>
> Para **solo reentrenar el ensamble**: ejecutar la preparación de datos, cargar el estudio, ejecutar la celda de preparación del paso 2 que define `trials_por_numero` y `columnas_modelo`, luego la configuración del paso 4 y el entrenamiento del paso 5. Omitir la curva de referencia, que sí depende de las predicciones del paso 3.
>
> El bloque final guarda cada `.txt` después de entrenarlo y escribe el JSON al finalizar todos los modelos. No implementa reanudación automática: después de una interrupción, los modelos guardados pueden cargarse para predecir, pero repetir el bucle original vuelve a entrenar.

