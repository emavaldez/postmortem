# Keila Zavaglia — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: keilazavaglia
- Repositorio: https://github.com/keilazavaglia/DMEyF_ksz
- Link posteado: https://github.com/keilazavaglia/DMEyF_ksz/tree/main/submits
- Commit: a2479a4a65931908299114316563bdbbfa77ec2a
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/keilazavaglia/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/keilazavaglia.json

## Resumen

La entrega es la carpeta submits/ de un repositorio en Python: 13 notebooks numerados según el envío al bot que generan, uno que prepara los datos, un README y un requirements.txt. El README indica como entrega final el submit 45. El camino tiene dos notebooks. datos_crear_parquet.ipynb convierte competencia_01.csv en parquet, recalcula clase_ternaria según la presencia del cliente en los dos meses siguientes y pone ccajas_depositos en NA para 202105. 45_ens70juntarZ028_11500_completo.ipynb agrega lag y delta de orden 1 y 2 de cada variable, arma un target binario (1 = BAJA+1 o BAJA+2), entrena con 202103 a 202106 sin submuestreo 70 modelos LightGBM (7 configuraciones de num_leaves, min_sum_hessian_in_leaf y cantidad de árboles × 10 semillas), promedia las 70 probabilidades de 202108 y escribe los 11.500 clientes de mayor promedio. Según el texto del notebook, las 7 configuraciones salen de una búsqueda con Optuna hecha en 0_exploracion/, carpeta que queda fuera del link posteado. Los demás notebooks corresponden a envíos anteriores: modelo con variables originales, lags con 5 semillas, ensambles con otros hiperparámetros, target sólo BAJA+2, lag de orden 3 y 54 variables nuevas.

**Qué entrega.** Un CSV de una columna y sin encabezado, 45_ens70juntarZ028_11500.csv, con los 11.500 numero_de_cliente de 202108 de mayor probabilidad promedio entre 70 modelos. El archivo no está en el repositorio: el README dice que los CSV y las probabilidades no se suben a GitHub.

**Cómo se ejecuta.** Según submits/README.md: usar Python 3.14.7 e instalar los paquetes con pip install -r submits/requirements.txt; copiar competencia_01.csv en la carpeta raíz del repositorio; correr submits/datos_crear_parquet.ipynb (~1 min), que crea competencia_01.parquet; correr submits/45_ens70juntarZ028_11500_completo.ipynb desde la carpeta submits/, de principio a fin y sin parámetros (~6,7 h desde cero). Si la corrida se corta, al volver a correr retoma desde las predicciones guardadas en probs_45/.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: 1 si clase_ternaria es BAJA+1 o BAJA+2, 0 en otro caso (el notebook la llama target juntar). Antes, datos_crear_parquet.ipynb recalcula clase_ternaria: BAJA+1 si el cliente no figura el mes siguiente, BAJA+2 si figura el mes siguiente y no el subsiguiente, CONTINUA si figura en los dos.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** —
- **Mes que predice:** 202108
- **Submuestreo:** No hay: entrena con todas las filas de 202103 a 202106 (el texto del notebook dice sin undersampling).
- **Calidad de datos:** datos_crear_parquet.ipynb pone ccajas_depositos en NA para 202105 y recalcula clase_ternaria; según su texto, respecto del CSV 29 filas pasan de CONTINUA a BAJA.
- **Drifting:** No se observa en el código
- **Variables dentro del mes:** No se observa en el código de la entrega. El notebook 33-37, de envíos anteriores, crea variables nuevas dentro del mes (sumas, cocientes, conteos e indicadores).
- **Variables históricas:** Lag 1, lag 2, delta 1 y delta 2 de todas las columnas salvo numero_de_cliente, foto_mes y clase_ternaria, con groupby por cliente y shift sobre la tabla ordenada por cliente y mes, en float32. Según el comentario del código quedan 761 variables contando las originales y numero_de_cliente.
- **Selección de variables:** No se observa en el código: usa todas las columnas salvo foto_mes y clase_ternaria.
- **Optimización de hiperparámetros:** El notebook de la entrega no busca hiperparámetros: trae escritas 7 configuraciones que, según su texto y sus comentarios, se copiaron de 0_exploracion/z028_optuna_trials.csv. Esa búsqueda está en 0_exploracion/z028_optuna_juntar.ipynb, fuera del link posteado: Optuna (TPE) con 40 trials sobre num_leaves (8 a 256) y min_sum_hessian_in_leaf (0,001 a 10), 5 semillas por trial, entrenamiento en 202104 y validación en 202106, con la ganancia máxima promedio como valor del trial; después evalúa 10 trials con 10 semillas en 202106 y en 202105.
- **Hiperparámetros finales:** Comunes: objective binary, learning_rate 0,005, min_data_in_leaf 0, feature_fraction 0,5, feature_fraction_bynode 0,2, max_bin 31. Por configuración (num_leaves; min_sum_hessian_in_leaf; árboles): trial 16 (64; 6,98; 1.420), trial 18 (47; 7,04; 1.525), trial 34 (65; 9,55; 1.427), trial 15 (42; 9,65; 1.532), trial 21 (38; 5,05; 1.660), trial 36 (106; 4,03; 1.248), trial 32 (53; 5,46; 1.443).
- **Semillas:** 10 semillas escritas en el código, en dos grupos de 5: 501419, 623353, 786349, 834569, 946331 y 270131, 417293, 583117, 692347, 851071. Cada grupo construye su lgb.Dataset con la primera semilla del grupo (501419 y 270131).
- **Cantidad de semillas:** 10
- **Ensamble:** Promedio sin pesos de las probabilidades de 70 modelos LightGBM: 7 configuraciones de hiperparámetros × 10 semillas.
- **Corte:** Cantidad fija: 11.500 clientes (ENVIOS = {45: 11_500}). Según el texto del notebook, el valor se toma de los resultados del público de cinco cortes enviados con el notebook 39-43: 10.500 → 103,62; 11.000 → 104,80; 11.500 → 104,61; 12.000 → 104,69; 12.500 → 102,08.
- **Validación:** El notebook de la entrega no separa meses de validación: entrena con 202103 a 202106 y predice 202108. Según su texto, las 7 configuraciones se evaluaron en junio y mayo; ese código está en 0_exploracion/z028_optuna_juntar.ipynb, fuera del link posteado (entrena en 202104 y valida en 202106, y entrena en 202103 y valida en 202105, midiendo ganancia). Las últimas celdas del notebook 45 comparan el CSV generado con el del submit 40 (byte a byte) y con el del submit 32 (porcentaje de clientes en común).
- **Salidas:** 45_ens70juntarZ028_11500.csv (11.500 numero_de_cliente, una columna, sin encabezado), 45_ens70_probs.parquet (probabilidad promedio por cliente de 202108), probs_45/t<trial>_s<semilla>.npy (una predicción por modelo) y 45_progreso.txt (hora y duración de cada modelo). datos_crear_parquet.ipynb escribe ../competencia_01.parquet.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optuna (`hiperparametros.optuna`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Técnicas sólo exploradas

- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: Según el README: Python 3.14.7, lightgbm 4.7.0, pandas 3.0.6, numpy 2.5.3, pyarrow 25.0.1, Windows 11, LightGBM con todos los núcleos (valor por defecto). requirements.txt lista 82 paquetes con versión fija.

## Pasos del camino de la entrega

1. **Recálculo de clase_ternaria desde el CSV.** datos_crear_parquet.ipynb lee ../competencia_01.csv, descarta la clase_ternaria original y la vuelve a calcular a partir de si cada cliente figura en el mes siguiente y en el subsiguiente. El último mes queda sin clase y en el penúltimo sólo quedan las filas BAJA+1. (`submits/datos_crear_parquet.ipynb` líneas 16–37)
2. **ccajas_depositos a NA en 202105 y escritura del parquet.** Pone NaN en ccajas_depositos para 202105, imprime la tabla de clases por mes y escribe ../competencia_01.parquet; si el archivo ya existe no lo reemplaza y sólo imprime si es igual al generado. (`submits/datos_crear_parquet.ipynb` líneas 39–48)
3. **Parámetros de la corrida.** El notebook 45 define meses de entrenamiento (202103 a 202106), mes a predecir (202108), el envío (submit 45 → 11.500 clientes) y la carpeta probs_45 para las predicciones de cada modelo. (`submits/45_ens70juntarZ028_11500_completo.ipynb` líneas 27–38)
4. **Semillas e hiperparámetros.** Escribe 10 semillas en dos grupos de 5, los hiperparámetros comunes (learning_rate 0,005, min_data_in_leaf 0, feature_fraction 0,5, feature_fraction_bynode 0,2, max_bin 31) y 7 configuraciones con num_leaves, min_sum_hessian_in_leaf y cantidad de árboles. (`submits/45_ens70juntarZ028_11500_completo.ipynb` líneas 40–62)
5. **Lectura del parquet y lags y deltas de orden 1 y 2.** Lee ../competencia_01.parquet, ordena por cliente y mes y calcula para cada columna (salvo numero_de_cliente, foto_mes y clase_ternaria) el valor de 1 y 2 filas antes del mismo cliente y la diferencia con cada uno. (`submits/45_ens70juntarZ028_11500_completo.ipynb` líneas 65–82)
6. **Target, entrenamiento y mes a predecir.** Arma la lista de variables (incluye numero_de_cliente), separa 202103 a 202106 como entrenamiento, define el target binario (1 = BAJA+1 o BAJA+2) y toma las filas de 202108. (`submits/45_ens70juntarZ028_11500_completo.ipynb` líneas 84–89)
7. **Funciones de armado del Dataset y de entrenamiento.** armar_dataset construye el lgb.Dataset con los hiperparámetros fijos y una semilla; entrenar_y_predecir entrena un modelo con una configuración y una semilla y devuelve la probabilidad para 202108. (`submits/45_ens70juntarZ028_11500_completo.ipynb` líneas 92–104)
8. **Entrenamiento de los 70 modelos.** Para cada grupo de semillas arma un Dataset con la primera semilla del grupo y entrena las 7 configuraciones con las 5 semillas. Cada predicción se guarda en un archivo .npy y las ya guardadas se saltean; la duración de cada modelo se anota en 45_progreso.txt. (`submits/45_ens70juntarZ028_11500_completo.ipynb` líneas 107–123)
9. **Ensamble.** Carga las 70 predicciones, las promedia por cliente, guarda el promedio en 45_ens70_probs.parquet y ordena los clientes de mayor a menor probabilidad. (`submits/45_ens70juntarZ028_11500_completo.ipynb` líneas 126–132)
10. **Corte y escritura del CSV.** Escribe los primeros 11.500 clientes en 45_ens70juntarZ028_11500.csv e imprime filas, valores únicos, si aparece notación científica y el porcentaje de coincidencia con el archivo del submit 32, que lee desde 32_ens100juntar_12000.csv. (`submits/45_ens70juntarZ028_11500_completo.ipynb` líneas 134–141)
11. **Comparación con el submit 40.** Compara byte a byte el CSV generado con 40_ens70juntarZ028_11500.csv e imprime el resultado. (`submits/45_ens70juntarZ028_11500_completo.ipynb` líneas 144–146)

## Archivos

- `submits/39-43_ens70juntarZ028_completo.ipynb` · secundario · Jupyter (python) · 160 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/39-43_ens70juntarZ028_completo.ipynb.txt) — Submits 39 a 43. Tiene el mismo código que el notebook 45; difiere en ENVIOS (cinco cortes: 12.000, 11.500, 11.000, 10.500 y 12.500), en la carpeta probs_39 y en los nombres del archivo de progreso y del parquet, y no tiene la celda de comparación con el submit 40. Su texto inicial explica el cambio de hiperparámetros respecto del submit 32 y su texto final registra los resultados del público de los submits 39 a 42. Según el texto del notebook 45, con este notebook se entrenaron los 70 modelos cuyas predicciones reutiliza aquél.
- `submits/29_lag3.ipynb` · secundario · Jupyter (python) · 112 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/29_lag3.ipynb.txt) — Submit 29. Entrena 10 trials de z005 con una semilla (270131), target BAJA+1 o BAJA+2 y lags y deltas de orden 1, 2 y 3, y escribe dos top 12.000: uno con lag 3 y otro sin lag 3, este último armado con las predicciones guardadas del submit 16.
- `submits/03-11_optuna_ens8.ipynb` · secundario · Jupyter (python) · 112 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/03-11_optuna_ens8.ipynb.txt) — Submits 3 a 11. Lee los 8 primeros trials de ../0_exploracion/z005_top10_5semillas.csv, entrena uno por trial con la semilla 501419, target BAJA+2 y lags y deltas de orden 1 y 2, promedia las probabilidades, las guarda en un parquet y escribe CSV para los cortes 11.500, 12.000 y 12.500. Según su texto, los nueve archivos numerados (cortes de 10.000 a 14.000) se generaron desde ese parquet.
- `submits/requirements.txt` · configuracion · Texto · 82 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/requirements.txt.txt) — Lista de 82 paquetes de Python con versión fija (==), entre ellos lightgbm 4.7.0, pandas 3.0.6, numpy 2.5.3, pyarrow 25.0.1, optuna 5.0.0, scikit-learn 1.9.1 y duckdb 1.5.6.
- `submits/14-15_ens50_juntar.ipynb` · secundario · Jupyter (python) · 111 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/14-15_ens50_juntar.ipynb.txt) — Submits 14 y 15. Entrena 10 trials de z005 × 5 semillas = 50 modelos con target BAJA+1 o BAJA+2 y lags y deltas de orden 1 y 2, promedia las probabilidades y escribe dos cortes: 13.000 y 12.000.
- `submits/00_modelo_base.ipynb` · secundario · Jupyter (python) · 83 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/00_modelo_base.ipynb.txt) — Submit 0. Un LightGBM con target BAJA+2 y las variables originales (learning_rate 0,05, num_leaves 31, min_data_in_leaf 100, feature_fraction 0,8, 300 árboles, semilla 501419), entrenado con 202103 a 202106; escribe los 10.000 clientes de mayor probabilidad de 202108 y agrega una fila a ../0_exploracion/resultados_experimentos.csv.
- `submits/33-37_ens100juntarBC_completo.ipynb` · secundario · Jupyter (python) · 244 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/33-37_ens100juntarBC_completo.ipynb.txt) — Submits 33 a 37. Igual al notebook 32 más 54 variables nuevas (versión BC_limpio): sumas de saldos, inversiones, ingresos y egresos, cocientes, conteos de transacciones y de servicios usados, indicadores y conteos de meses, con lag 1 y delta 1 para una parte. Entrena 100 modelos y escribe cinco cortes (12.000, 11.500, 11.000, 10.500 y 12.500). La celda final de resultados está sin completar.
- `submits/datos_crear_parquet.ipynb` · principal · Jupyter (python) · 48 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/datos_crear_parquet.ipynb.txt) — Crea ../competencia_01.parquet a partir de ../competencia_01.csv: recalcula clase_ternaria por presencia del cliente en los dos meses siguientes y pone ccajas_depositos en NA para 202105. Todos los notebooks de submits/ leen ese parquet.
- `submits/13_ens15_z012.ipynb` · secundario · Jupyter (python) · 120 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/13_ens15_z012.ipynb.txt) — Submit 13. Toma los 5 primeros trials de ../0_exploracion/z012_revalidacion.csv y sus hiperparámetros de z012_optuna_trials.csv, entrena 5 × 3 semillas = 15 modelos con target BAJA+2, promedia y escribe el top 12.000; imprime la coincidencia con el submit 12.
- `submits/README.md` · explicacion · Markdown · 51 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/README.md.txt) — Texto de presentación de la carpeta. Indica el submit 45 como entrega final, da cuatro pasos para replicarlo (entorno, datos, datos_crear_parquet.ipynb y notebook 45), declara versiones y sistema, la regla de numeración de los notebooks y dos tablas de submits con título en el bot, notebook, archivo, modelo y resultado público. Para los submits 16 a 38 remite a un archivo CLAUDE.md.
- `submits/01-02_lags_semillas.ipynb` · secundario · Jupyter (python) · 112 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/01-02_lags_semillas.ipynb.txt) — Submits 1 y 2. Agrega lags y deltas de orden 1 y 2, entrena un LightGBM con target BAJA+2 (learning_rate 0,05, num_leaves 31, min_data_in_leaf 100, feature_fraction 0,8, 300 árboles) con 5 semillas, escribe un CSV de 11.500 clientes por semilla y otro con el promedio de las 5 probabilidades. El comentario de TOP_N dice que 11.500 es el máximo de la curva promedio en validación (z003).
- `submits/12_ens100_z005.ipynb` · secundario · Jupyter (python) · 132 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/12_ens100_z005.ipynb.txt) — Submit 12. Entrena los 10 trials de ../0_exploracion/z005_top10_final.csv con 10 semillas (100 modelos), target BAJA+2 y lags y deltas de orden 1 y 2, promedia las probabilidades y escribe los cortes de 11.500 y 12.000.
- `submits/32_ens100juntar_12000_completo.ipynb` · secundario · Jupyter (python) · 141 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/32_ens100juntar_12000_completo.ipynb.txt) — Submit 32. Mismo esquema que el notebook 45 con otras configuraciones: 10 trials de z005 (num_leaves entre 61 y 241, entre 532 y 888 árboles) × 10 semillas = 100 modelos, target BAJA+1 o BAJA+2 y corte de 12.000. La última celda compara el resultado con 28_ens100juntar_12000.csv.
- `submits/44_ens70juntarZ028_12000_completo.ipynb` · secundario · Jupyter (python) · 143 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/44_ens70juntarZ028_12000_completo.ipynb.txt) — Submit 44. Mismo código que el notebook 45 con corte de 12.000 clientes y carpeta probs_44; la última celda compara el archivo con el del submit 39. El README lo señala como reemplazado por el 45.
- `submits/45_ens70juntarZ028_11500_completo.ipynb` · principal · Jupyter (python) · 146 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/45_ens70juntarZ028_11500_completo.ipynb.txt) — Notebook de la entrega final (submit 45). Calcula lags y deltas de orden 1 y 2, entrena 70 LightGBM (7 configuraciones × 10 semillas) con 202103 a 202106 y target BAJA+1 o BAJA+2, promedia las probabilidades de 202108 y escribe los 11.500 clientes de mayor promedio.
- `submits/16-17_distribucion_semillas.ipynb` · secundario · Jupyter (python) · 138 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/keilazavaglia/submits/16-17_distribucion_semillas.ipynb.txt) — Submits 16 y 17. Entrena dos versiones con 10 trials de z005 × 5 semillas cada una (100 modelos): target BAJA+1 o BAJA+2 y target BAJA+2. Por cada semilla promedia sus 10 trials y escribe un top 12.000 (5 archivos por versión), y calcula el porcentaje de clientes en común entre archivos. La celda final de texto registra los resultados del bot: 101,45 ± 0,53 para la primera versión y 95,63 ± 1,09 para la segunda.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### submits/datos_crear_parquet.ipynb

Crea ../competencia_01.parquet a partir de ../competencia_01.csv: recalcula clase_ternaria por presencia del cliente en los dos meses siguientes y pone ccajas_depositos en NA para 202105. Todos los notebooks de submits/ leen ese parquet.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Celda de texto: explica que el notebook crea competencia_01.parquet desde el CSV
#   con dos cambios (clase_ternaria recalculada y ccajas_depositos en NA para 202105) y que, si el parquet ya
#   existe, no lo reemplaza sino que compara. Declara que 29 filas pasan de CONTINUA a BAJA respecto del CSV.
#%% celda 1 [texto]
# Crear `competencia_01.parquet` a partir de `competencia_01.csv`

Todos los notebooks de `submits/` leen `../competencia_01.parquet`. Este notebook lo crea desde el CSV de la cátedra
(`competencia_01.csv`, en la carpeta raíz del repo) con **dos cambios**:

1. **`clase_ternaria` recalculada con la definición estricta**: BAJA+1 = el cliente no está el mes siguiente;
   BAJA+2 = está el mes siguiente pero no el subsiguiente; CONTINUA = está en los dos. 202107 solo puede ser BAJA+1
   (o vacío) y 202108 queda vacío. Respecto del CSV, 29 filas pasan de CONTINUA a BAJA (clientes que se van y vuelven).
2. **`ccajas_depositos` = NA en 202105** (en ese mes viene todo en cero: dato roto, recomendación del profesor).

Si `competencia_01.parquet` ya existe, **no lo pisa**: verifica que lo que se genera es idéntico (`DataFrame.equals`).
Tiempo: ~1 min.

# [Anotación · líneas 15–24] Importa os, numpy y pandas, define la ruta de entrada (../competencia_01.csv) y
#   la de salida (../competencia_01.parquet), lee el CSV y elimina la columna clase_ternaria original.
#%% celda 2 [código]
import os
import numpy as np
import pandas as pd

ENTRADA = "../competencia_01.csv"
SALIDA  = "../competencia_01.parquet"

df = pd.read_csv(ENTRADA)
df = df.drop(columns=["clase_ternaria"])            # se recalcula abajo

# [Anotación · líneas 26–31] Convierte foto_mes en un índice correlativo de meses (año × 12 + mes), arma el
#   conjunto de pares (cliente, mes) presentes en los datos y calcula para cada fila dos indicadores: si el
#   cliente figura en el mes siguiente y si figura dos meses después.
# Mes como número correlativo (202103 -> 2021*12 + 3) para poder sumar 1 y 2 meses
mes_idx = ((df["foto_mes"] // 100) * 12 + df["foto_mes"] % 100).values
cliente = df["numero_de_cliente"].values
presentes = set(zip(cliente, mes_idx))               # pares (cliente, mes) que existen
esta_mes1 = np.array([(c, m + 1) in presentes for c, m in zip(cliente, mes_idx)])   # ¿está el mes siguiente?
esta_mes2 = np.array([(c, m + 2) in presentes for c, m in zip(cliente, mes_idx)])   # ¿y el subsiguiente?

# [Anotación · líneas 33–37] Asigna la clase: BAJA+1 si el cliente no figura el mes siguiente; BAJA+2 si
#   figura el mes siguiente y no el subsiguiente; CONTINUA en otro caso. Deja sin clase todas las filas del
#   último mes y, en el penúltimo, las de los clientes que sí figuran el mes siguiente.
ultimo = mes_idx.max()
clase = np.where(~esta_mes1, "BAJA+1", np.where(~esta_mes2, "BAJA+2", "CONTINUA")).astype(object)
clase[mes_idx == ultimo] = None                      # 202108: no hay futuro
clase[(mes_idx == ultimo - 1) & esta_mes1] = None    # 202107: solo se sabe si es BAJA+1
df = df.assign(clase_ternaria=clase)

# [Anotación · líneas 39–41] Pone NaN en ccajas_depositos para las filas de 202105 e imprime la tabla de
#   cantidad de filas por mes y clase, contando los valores vacíos.
df.loc[df["foto_mes"] == 202105, "ccajas_depositos"] = np.nan   # dato roto en 202105

print(df.groupby("foto_mes")["clase_ternaria"].value_counts(dropna=False).unstack())

# [Anotación · líneas 43–48] Si el parquet de salida ya existe, lo lee e imprime si es igual al dataframe
#   generado (DataFrame.equals); si no existe, lo escribe sin índice e imprime ruta y dimensiones.
#%% celda 3 [código]
if os.path.exists(SALIDA):
    print("Ya existe: ¿es idéntico al que se genera?", df.equals(pd.read_parquet(SALIDA)))
else:
    df.to_parquet(SALIDA, index=False)
    print("Creado:", SALIDA, df.shape)
```

### submits/45_ens70juntarZ028_11500_completo.ipynb

Notebook de la entrega final (submit 45). Calcula lags y deltas de orden 1 y 2, entrena 70 LightGBM (7 configuraciones × 10 semillas) con 202103 a 202106 y target BAJA+1 o BAJA+2, promedia las probabilidades de 202108 y escribe los 11.500 clientes de mayor promedio.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–24] Celda de texto: presenta el submit 45 como copia exacta del submit 40 (público
#   104,61 según el texto), da los resultados del público de los cortes 10.500 a 12.500, enumera la receta en
#   seis puntos e indica que los 70 modelos se entrenaron con el notebook 39-43 y que este notebook reutiliza
#   esas predicciones copiadas a probs_45/.
#%% celda 1 [texto]
# Submit 45 (ENTREGA FINAL) — juntar con hiperparámetros de z028, top 11.500. Código completo de principio a fin

**Resultado:** `45_ens70juntarZ028_11500.csv` = los 11.500 clientes de 202108 con mayor probabilidad promedio de 70 modelos LightGBM.
Es copia exacta del submit 40 (público 104,61), reenviado como último submit para que quede como entrega.

**Por qué 11.500:** curva del público de este modelo: 10.500 103,62 · 11.000 104,80 · 11.500 104,61 · 12.000 104,69 · 12.500 102,08.
Meseta entre 11.000 y 12.000 con caída a los dos lados → se elige el centro de la meseta.

**Receta**
1. Datos: `competencia_01.parquet`, creado con `datos_crear_parquet.ipynb` (clase_ternaria estricta; `ccajas_depositos` = NA en 202105).
2. Variables: las 153 originales (incluye `numero_de_cliente`) + lags y deltas de orden 1 y 2 = **761 variables**.
3. Target "juntar": 1 si el cliente es BAJA+1 o BAJA+2, 0 si es CONTINUA.
4. Train: 202103, 202104, 202105 y 202106 completos (sin undersampling).
5. Modelos: 7 trials de la optimización bayesiana z028 (`0_exploracion/z028_optuna_juntar.ipynb`: Optuna con target juntar,
   5 semillas por trial, revalidados con 10 semillas en junio y mayo) × 10 semillas = **70 modelos**.
   Hiperparámetros fijos del profesor: learning_rate 0,005, min_data_in_leaf 0, max_bin 31, feature_fraction 0,5, feature_fraction_bynode 0,2.
6. Ensamble: promedio simple de las 70 probabilidades por cliente → top 11.500.

**Historia:** los 70 modelos se entrenaron con `39-43_ens70juntarZ028_completo.ipynb` (mismo código, 400 min). Este notebook
reusa esas predicciones (copiadas a `probs_45/`) y genera el archivo final. Reproducibilidad verificada: un modelo reentrenado
en un proceso nuevo con este código da una predicción idéntica (`np.array_equal` = True).

**Tiempo:** ~6,7 h desde cero (~5,7 min por modelo). Cada predicción se guarda en `probs_45/`: si se corta, volver a correr y retoma.

# [Anotación · líneas 26–38] Importa os, time, numpy, pandas y lightgbm. Define los meses de entrenamiento
#   (202103 a 202106), el mes a predecir (202108), el diccionario ENVIOS con un único envío (submit 45 → 11.500
#   clientes) y la carpeta probs_45, que crea si no existe.
#%% celda 2 [código]
# --- 1. Librerías y parámetros ---
import os
import time
import numpy as np
import pandas as pd
import lightgbm as lgb

MESES_FINAL = [202103, 202104, 202105, 202106]   # meses de entrenamiento
MES_PRED    = 202108                             # mes a predecir
ENVIOS      = {45: 11_500}                       # número de submit -> cantidad de clientes
CARPETA     = "probs_45"                         # una predicción por modelo (para retomar si se corta)
os.makedirs(CARPETA, exist_ok=True)

# [Anotación · líneas 40–50] Escribe las 10 semillas en dos grupos de 5, con las claves submit15 y submit16, y
#   los hiperparámetros comunes a todos los modelos: objective binary, learning_rate 0,005, min_data_in_leaf 0,
#   feature_fraction 0,5, feature_fraction_bynode 0,2 y max_bin 31.
# Las 10 semillas del 32, en los mismos dos grupos. Cada grupo usa su propio Dataset (ver celda 3).
GRUPOS_SEMILLAS = {
    "submit15": [501419, 623353, 786349, 834569, 946331],
    "submit16": [270131, 417293, 583117, 692347, 851071],
}

# Hiperparámetros fijos (recomendación del profesor)
params_fijos = {
    "objective": "binary", "learning_rate": 0.005, "min_data_in_leaf": 0,
    "feature_fraction": 0.5, "feature_fraction_bynode": 0.2, "max_bin": 31, "verbose": -1,
}

# [Anotación · líneas 52–62] Diccionario TRIALS con 7 configuraciones identificadas por número de trial (16,
#   18, 34, 15, 21, 36 y 32). Cada una fija num_leaves (entre 38 y 106), min_sum_hessian_in_leaf (entre 4,03 y
#   9,65) y la cantidad de árboles (entre 1.248 y 1.660). El comentario indica que se copiaron de
#   0_exploracion/z028_optuna_trials.csv y que la cantidad de árboles es el promedio del early stopping de 5
#   semillas.
# Los 7 trials de z028 elegidos: trial -> (num_leaves, min_sum_hessian_in_leaf, cantidad de árboles)
# (copiados de 0_exploracion/z028_optuna_trials.csv, con todos los decimales; árboles = promedio del early stopping de 5 semillas)
TRIALS = {
    16: (64, 6.982303130196578, 1420),
    18: (47, 7.044084165759745, 1525),
    34: (65, 9.553255512602105, 1427),
    15: (42, 9.65435654722589, 1532),
    21: (38, 5.046242592824922, 1660),
    36: (106, 4.026506925773964, 1248),
    32: (53, 5.459562821619835, 1443),
}

# [Anotación · líneas 64–69] Lee ../competencia_01.parquet y arma la lista cols con todas las columnas salvo
#   foto_mes, clase_ternaria y numero_de_cliente: son las columnas a las que se les calcula historia.
#%% celda 3 [código]
# --- 2. Datos, lags/deltas de orden 1 y 2, y target juntar ---
df = pd.read_parquet("../competencia_01.parquet")

no_usar = ["foto_mes", "clase_ternaria"]
cols = [c for c in df.columns if c not in no_usar and c != "numero_de_cliente"]   # a estas se les calculan lags

# [Anotación · líneas 71–82] Ordena la tabla por cliente y mes. Para k = 1 y k = 2 toma, dentro de cada
#   cliente, el valor de la fila k posiciones anterior (columnas con sufijo _lagk) y la diferencia entre el
#   valor actual y ese valor (sufijo _deltak), en float32. Une las cuatro tablas nuevas a la original y borra
#   los intermedios.
# Ordeno por cliente y mes para que shift(k) traiga el valor de k meses antes del MISMO cliente
df = df.sort_values(["numero_de_cliente", "foto_mes"]).reset_index(drop=True)
grupo = df.groupby("numero_de_cliente")[cols]
nuevas = []
for k in [1, 2]:
    lag = grupo.shift(k).astype("float32")              # valor de hace k meses
    delta = (df[cols] - lag).astype("float32")          # cuánto cambió desde entonces
    lag.columns   = [f"{c}_lag{k}" for c in cols]
    delta.columns = [f"{c}_delta{k}" for c in cols]
    nuevas += [lag, delta]
df = pd.concat([df] + nuevas, axis=1)
del nuevas, lag, delta, grupo

# [Anotación · líneas 84–89] Define variables como todas las columnas salvo foto_mes y clase_ternaria, de modo
#   que numero_de_cliente queda incluida. Separa las filas de 202103 a 202106 como entrenamiento, arma el target
#   (1 si clase_ternaria es BAJA+1 o BAJA+2, 0 en otro caso) y toma las filas de 202108 con sus variables.
#   Imprime cantidad de variables, de filas y de positivos.
variables = [c for c in df.columns if c not in no_usar]   # 761, incluye numero_de_cliente
final  = df[df["foto_mes"].isin(MESES_FINAL)]
y_final = final["clase_ternaria"].isin(["BAJA+1", "BAJA+2"]).astype(int)   # target juntar
futuro = df[df["foto_mes"] == MES_PRED][["numero_de_cliente"]].copy()
X_futuro = df.loc[futuro.index, variables]
print("Variables:", len(variables), "| filas train:", len(final), "| positivos:", y_final.sum())

# [Anotación · líneas 91–98] Función armar_dataset: construye el lgb.Dataset de entrenamiento con los
#   hiperparámetros fijos y la semilla recibida, con free_raw_data=False, y lo devuelve ya construido. Según el
#   comentario, la semilla interviene en la muestra con la que LightGBM arma los bines de cada variable.
#%% celda 4 [código]
# --- 3. Funciones ---
def armar_dataset(semilla_grupo):
    # LightGBM arma los "bines" de cada variable (max_bin = 31) con una muestra elegida con la semilla.
    # Igual que en el 32: un Dataset por grupo de semillas, armado con la primera semilla del grupo.
    datos = lgb.Dataset(final[variables], label=y_final, free_raw_data=False,
                        params={**params_fijos, "seed": semilla_grupo})
    return datos.construct()

# [Anotación · líneas 100–104] Función entrenar_y_predecir: toma de TRIALS el num_leaves, el
#   min_sum_hessian_in_leaf y la cantidad de árboles de la configuración, entrena un modelo con esa semilla
#   sobre el Dataset recibido y devuelve la probabilidad predicha para las filas de 202108.
def entrenar_y_predecir(datos, trial, semilla):
    hojas, hessian, arboles = TRIALS[trial]
    p = {**params_fijos, "num_leaves": hojas, "min_sum_hessian_in_leaf": hessian, "seed": semilla}
    modelo = lgb.train(p, datos, num_boost_round=arboles)
    return modelo.predict(X_futuro)                  # probabilidad de baja de cada cliente de 202108

# [Anotación · líneas 106–123] Recorre los dos grupos de semillas. Si ya existen los 35 archivos .npy del
#   grupo (7 configuraciones × 5 semillas) pasa al siguiente; si no, arma un Dataset con la primera semilla del
#   grupo y, para cada configuración y semilla sin archivo guardado, entrena, guarda la predicción en
#   probs_45/t<trial>_s<semilla>.npy y agrega una línea con hora y duración en 45_progreso.txt. Al final imprime
#   los minutos totales.
#%% celda 5 [código]
# --- 4. Entrenar los 70 modelos (retoma si se cortó) ---
inicio_total = time.time()
for nombre, semillas in GRUPOS_SEMILLAS.items():
    if all(os.path.exists(f"{CARPETA}/t{t}_s{s}.npy") for t in TRIALS for s in semillas):
        continue                                     # grupo completo: no hace falta armar el Dataset
    datos = armar_dataset(semillas[0])
    for trial in TRIALS:
        for semilla in semillas:
            archivo = f"{CARPETA}/t{trial}_s{semilla}.npy"
            if os.path.exists(archivo):              # ya estaba hecho: lo salteamos
                continue
            inicio = time.time()
            np.save(archivo, entrenar_y_predecir(datos, trial, semilla))
            with open("45_progreso.txt", "a", encoding="utf-8") as f:
                f.write(time.strftime("%H:%M:%S ") + f"{nombre} | trial {trial}, semilla {semilla}: {(time.time() - inicio) / 60:.1f} min\n")
    del datos
print(f"Total: {(time.time() - inicio_total) / 60:.0f} min")

# [Anotación · líneas 125–132] Carga las 70 predicciones guardadas, las promedia por cliente en la columna
#   prob_ensamble, guarda esa tabla en 45_ens70_probs.parquet y ordena los numero_de_cliente de mayor a menor
#   probabilidad promedio, convertidos a int64.
#%% celda 6 [código]
# --- 5. Ensamble (promedio de las 70 probabilidades) y un archivo por corte ---
todas = [s for semillas in GRUPOS_SEMILLAS.values() for s in semillas]
probs = [np.load(f"{CARPETA}/t{t}_s{s}.npy") for t in TRIALS for s in todas]
futuro["prob_ensamble"] = np.mean(probs, axis=0)
print("Modelos en el ensamble:", len(probs))
futuro.to_parquet("45_ens70_probs.parquet")
orden = futuro.sort_values("prob_ensamble", ascending=False)["numero_de_cliente"].astype("int64")

# [Anotación · líneas 134–141] Lee 32_ens100juntar_12000.csv (archivo que escribe el notebook 32) como
#   conjunto de clientes. Para cada entrada de ENVIOS escribe los primeros n clientes del orden en
#   <número>_ens70juntarZ028_<n>.csv, una columna sin encabezado; vuelve a leer el archivo e imprime cantidad de
#   filas, cantidad de valores únicos, si aparece el texto e+ y qué porcentaje de los clientes del archivo del
#   submit 32 está también en el nuevo.
entrega_32 = set(pd.read_csv("32_ens100juntar_12000.csv", header=None)[0])
for numero, n in ENVIOS.items():
    archivo = f"{numero}_ens70juntarZ028_{n}.csv"
    top = orden.head(n)
    top.to_csv(archivo, index=False, header=False)     # una columna, sin encabezado (formato del bot)
    contenido = open(archivo).read()
    print(f"{archivo} | filas: {len(contenido.splitlines())} | únicos: {top.nunique()} | ¿e+? {'e+' in contenido}"
          f" | coincide con el 32: {len(entrega_32 & set(top)) / len(entrega_32):.1%}")

# [Anotación · líneas 143–146] Lee en binario 45_ens70juntarZ028_11500.csv y 40_ens70juntarZ028_11500.csv
#   (archivo que escribe el notebook 39-43) e imprime si son idénticos byte a byte.
#%% celda 7 [código]
# --- 6. Verificación: ¿es el mismo archivo que el submit 40? ---
iguales = open("45_ens70juntarZ028_11500.csv", "rb").read() == open("40_ens70juntarZ028_11500.csv", "rb").read()
print("¿45 idéntico byte a byte al 40?", iguales)
```


## Explicaciones del alumno (texto original)

### submits/README.md

> # Submits — Primera competencia (202108)
>
> ## Cómo replicar la predicción final (para la cátedra)
>
> **Entrega final: submit 45 → `submits/45_ens70juntarZ028_11500_completo.ipynb` genera `45_ens70juntarZ028_11500.csv`**
> (70 modelos LightGBM: 7 trials de z028 × 10 semillas, target BAJA+1 + BAJA+2, top 11.500; público 104,61).
>
> 1. **Entorno:** Python 3.14.7 y los paquetes de `requirements.txt` (`pip install -r submits/requirements.txt`).
>    Versiones clave: lightgbm 4.7.0, pandas 3.0.6, numpy 2.5.3, pyarrow 25.0.1. Se corrió en Windows 11.
> 2. **Datos:** copiar `competencia_01.csv` (el de la cátedra) en la carpeta raíz del repo (al lado de `submits/`).
> 3. **Correr `submits/datos_crear_parquet.ipynb`** (~1 min): crea `competencia_01.parquet` (clase_ternaria estricta y
>    `ccajas_depositos` = NA en 202105). Verificado: idéntico al parquet usado en todos los submits.
> 4. **Correr `submits/45_ens70juntarZ028_11500_completo.ipynb`** desde la carpeta `submits/` (de principio a fin,
>    sin parámetros; ~6,7 h desde cero).
>    Entrena todos los modelos, guarda cada predicción en su carpeta `probs_*/` (si se corta, al volver a correr retoma)
>    y escribe el CSV enviado. La última celda informa filas, únicos y coincidencia con otros submits.
>
> Los hiperparámetros y semillas están escritos en cada notebook. LightGBM se corrió con todos los núcleos (default);
> el submit 32 se reprodujo byte a byte en esta máquina.
>
> **Regla:** cada submit (o tanda de cortes) tiene su notebook con el número adelante. Los notebooks de esta
> carpeta **solo generan archivos para el bot**; lo experimental está en `0_exploracion/`.
> Un notebook ya enviado no se modifica: si cambia algo, se hace uno nuevo con el número siguiente.
> Los CSV y las probabilidades (`probs_*/`, `*.parquet`) no se suben a GitHub.
>
> | N° | Título en el bot | Notebook | Archivo | Modelo | Público |
> |---|---|---|---|---|---|
> | 0 | base_0 | `00_modelo_base` | `0_modelo_base_todos_meses_10000.csv` | LightGBM base, 1 semilla, top 10.000 | 90,83 |
> | 1 | LagsSemillas01 | `01-02_lags_semillas` | `1_lags_s*_11500.csv` (5) | lags 1 y 2, receta vieja, 5 semillas | 92,67 ± 3,90 |
> | 2 | LagsEnsamble01 | `01-02_lags_semillas` | `2_lags_ensamble5_11500.csv` | ensamble de esas 5 semillas | 97,07 |
> | 3-11 | N_OptunaEns_corte | `03-11_optuna_ens8` | `N_optuna_ens8_corte.csv` | receta del profesor, 8 trials z005 × 1 semilla | máx 99,11 (11.500 y 12.000) |
> | 12 | 12_Ens100z005_12000 | `12_ens100_z005` | `12_ens100_12000.csv` | 10 trials z005 × 10 semillas = 100 modelos | 94,82 |
> | 13 | 13_Ens15z012_12000 | `13_ens15_z012` | `13_ens15z012_12000.csv` | 5 trials z012 × 3 semillas = 15 modelos | 93,20 |
> | 14 | 14_Ens50juntar_13000 | `14-15_ens50_juntar` | `14_ens50juntar_13000.csv` | 10 trials z005 × 5 semillas, target BAJA+1 + BAJA+2 | 99,36 |
> | 15 | 15_Ens50juntar_12000 | `14-15_ens50_juntar` | `15_ens50juntar_12000.csv` | ídem, top 12.000 | **101,92** |
>
> Cortes del 3 al 11 (público): 10.000 94,46 · 10.500 94,63 · 11.000 97,82 · 11.500 99,11 · 12.000 99,11 ·
> 12.500 96,42 · 13.000 95,18 · 13.500 93,72 · 14.000 94,63.
>
> Submits 16-38: ver CLAUDE.md (sección Submits). Los dos candidatos a entrega final:
>
> | N° | Título en el bot | Notebook | Archivo | Modelo | Público |
> |---|---|---|---|---|---|
> | 32 / 38 | 32_ens100juntar_12000 / 38 (copia) | `32_ens100juntar_12000_completo` | `32_ens100juntar_12000.csv` | 10 trials z005 × 10 semillas, target juntar | 102,11 |
> | 39 | 39_ens70juntarZ028_12000 | `39-43_ens70juntarZ028_completo` | `39_ens70juntarZ028_12000.csv` | 7 trials z028 × 10 semillas, target juntar | **104,69** |
> | 40 | 40_ens70juntarZ028_11500 | ídem | `40_ens70juntarZ028_11500.csv` | ídem, top 11.500 | 104,61 |
> | 41 | 41_ens70juntarZ028_11000 | ídem | `41_ens70juntarZ028_11000.csv` | ídem, top 11.000 | 104,80 |
> | 42 | 42_ens70juntarZ028_10500 | ídem | `42_ens70juntarZ028_10500.csv` | ídem, top 10.500 | 103,62 |
> | 44 | 44_ens70juntarZ028_12000_efinal | `44_ens70juntarZ028_12000_completo` | `44_ens70juntarZ028_12000.csv` | copia exacta del 39 (reemplazado por el 45) | 104,69 |
> | 43 | 43_ens70juntarZ028_12500 | `39-43_ens70juntarZ028_completo` | `43_ens70juntarZ028_12500.csv` | ídem, top 12.500 | 102,08 |
> | **45** | **45_ens70juntarZ028_11500_efinal** | `45_ens70juntarZ028_11500_completo` | `45_ens70juntarZ028_11500.csv` | **copia exacta del 40 → ENTREGA FINAL** (centro de la meseta 11.000-12.000) | 104,61 |

