# mmfiora — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: mmfiora
- Repositorio: https://github.com/mmfiora/dmeyf2026-competencia-01
- Link posteado: https://github.com/mmfiora/dmeyf2026-competencia-01
- Commit: 631d8a333e5c256c04571e88e5fc695d80ba990a
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/mmfiora/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/mmfiora.json

## Resumen

El link posteado es el repositorio completo; el README de la raíz remite a la carpeta entrega_final/, que contiene dos notebooks en Python (uno de ellos en dos copias, sin ejecutar y ejecutado), un README, requirements.txt, el CSV entregado y los resultados de la búsqueda de hiperparámetros. competencia_FINAL.ipynb lee competencia_01_crudo.csv, calcula clase_ternaria, pasa ccajas_depositos a NA en 202105, elimina 12 variables, reemplaza las variables monetarias (nombre que empieza con m) por su ranking dentro de cada mes, con cero fijo cuando tienen negativos, y agrega lags y delta-lags de orden 1 y 2. Entrena 20 modelos LightGBM con los mismos hiperparámetros y distinta semilla sobre 202103-202106, sin submuestreo, con clase binaria (positivo = BAJA+1 o BAJA+2), promedia las probabilidades sobre 202108 y escribe los 13.000 clientes de mayor probabilidad. Tres hiperparámetros (num_leaves, min_sum_hessian_in_leaf y num_iterations) provienen del trial 27 de una búsqueda con Optuna de 30 trials (entrena en 202103-202105 y mide AUC en 202106), cuyo código está en bayesiana_competencia_01_ejecutado.ipynb y cuyos resultados el notebook final lee de bo_resultados.csv. La última celda compara el archivo generado con el entregado.

**Qué entrega.** Un CSV sin encabezado, de una columna, con los numero_de_cliente de los 13.000 clientes de 202108 de mayor probabilidad promedio: salida/entregas/ensamble_K13000.csv. El repositorio incluye el archivo subido como entrega_final/ensamble_K13000_ENTREGADO.csv (13.000 líneas). Según el README, es el único archivo de la entrega final y su ganancia pública es 105,0225.

**Cómo se ejecuta.** Según entrega_final/README.md: (1) crear un entorno virtual con Python 3.12.10 e instalar requirements.txt; (2) poner competencia_01_crudo.csv en entrega_final/datos/ (datos/LEEME.txt da la URL de descarga y un ejemplo con curl); (3) con entrega_final/ como directorio de trabajo, ejecutar competencia_FINAL.ipynb de arriba hacia abajo con jupyter nbconvert --to notebook --execute y --ExecutePreprocessor.timeout=-1; (4) el resultado queda en salida/entregas/ensamble_K13000.csv y la última celda lo compara con ensamble_K13000_ENTREGADO.csv. El README indica una duración de unas 2 horas y media en una CPU de 8 núcleos. La búsqueda de hiperparámetros no se vuelve a correr: el notebook lee bo_resultados.csv; el README indica que correrla desde cero lleva unas 5 horas.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** Modelo final: binaria, y_pos = 1 si clase_ternaria es BAJA+1 o BAJA+2 y 0 si es CONTINUA (competencia_FINAL.ipynb, línea 159). clase_ternaria se calcula en el mismo notebook a partir del CSV crudo (líneas 74-93). En la búsqueda de hiperparámetros (bayesiana_competencia_01_ejecutado.ipynb, línea 142) la clase de cada trial es y = 1 sólo si BAJA+2.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica: el entrenamiento final usa todas las filas de 202103 a 202106 (competencia_FINAL.ipynb, líneas 191-193), 654.066 según la salida guardada en competencia_FINAL_ejecutado.ipynb. La búsqueda de hiperparámetros tampoco submuestrea.
- **Calidad de datos:** ccajas_depositos se pasa a NA sólo en 202105 (línea 103); la celda de texto indica que en ese mes la variable tiene todos ceros. No se observa en el código otro tratamiento de variables rotas ni imputación.
- **Drifting:** Dos acciones (líneas 47-50 y 115-129). Se eliminan 12 variables: cprestamos_personales, mprestamos_personales y otras 10 que el comentario describe como las de mayor KS; según el README, el KS se mide entre 202103-05 y 202108, y su cálculo no está en el repositorio. A las columnas cuyo nombre empieza con 'm' minúscula se les aplica un ranking dentro de cada foto_mes: las que no tienen valores negativos pasan a su rango porcentual (0 a 1); las que tienen negativos pasan a un rango de -1 a 1 con cero fijo (positivos rankeados entre sí de 0 a 1, negativos de -1 a 0, cero en 0, NA se conserva). Según la salida guardada son 41 variables: 31 sin negativos y 10 con negativos. El ranking se calcula antes de los lags.
- **Variables dentro del mes:** No se observa en el código.
- **Variables históricas:** Lag 1 y lag 2 y delta-lag 1 y 2 (valor del mes menos el lag) de todas las columnas salvo numero_de_cliente, foto_mes, periodo0 y clase_ternaria (líneas 137-156), calculados sobre los valores ya rankeados. El lag se obtiene uniendo por numero_de_cliente y periodo0 desplazado k meses; si el cliente no tiene fila en ese mes queda NA. Resultan cinco columnas por variable base; 700 variables de entrada según el README y la salida guardada.
- **Selección de variables:** Exclusión a mano de las 12 variables de VARIABLES_ELIMINADAS (líneas 47-50 y 115). numero_de_cliente, foto_mes, periodo0 y clase_ternaria quedan fuera de las variables de entrada (líneas 51 y 158). No se observa selección por importancia ni canaritos.
- **Optimización de hiperparámetros:** Optuna con TPESampler (seed 285937, n_startup_trials = 8), 30 trials, estudio guardado en SQLite (bayesiana_competencia_01_ejecutado.ipynb, líneas 175-197). Cada trial entrena con 202103-202105 y valida en 202106; el valor del trial es el AUC de validación en la última iteración. Busca num_leaves (entero de 8 a 1.024, escala logarítmica), min_sum_hessian_in_leaf (0,001 a 50, escala logarítmica) y num_iterations (entero de 300 a 2.500). Ese notebook prepara los datos sin la eliminación de las 12 variables y sin el ranking mensual (760 variables según su salida guardada) y usa la clase y = BAJA+2. competencia_FINAL.ipynb no corre la búsqueda: lee bo_resultados.csv, toma la fila de mayor value y comprueba con assert que coincide con los valores escritos en PARAMS (líneas 173-178).
- **Hiperparámetros finales:** objective = binary, metric = auc, boosting = gbdt, max_bin = 31, min_data_in_leaf = 0, feature_fraction = 0.50, feature_fraction_bynode = 0.20, learning_rate = 0.005, feature_pre_filter = False, force_row_wise = True, num_leaves = 171, min_sum_hessian_in_leaf = 7.28721427391867 y num_iterations = 1050 (líneas 60-64). Los tres últimos corresponden al trial 27 de bo_resultados.csv (AUC 0,90468 según el README).
- **Semillas:** 20 semillas escritas en SEMILLAS (líneas 54-55): 285937, 474619, 502487, 600673, 666637, 326219, 213727, 962341, 884959, 305759, 274583, 556123, 182129, 752489, 852199, 362927, 130307, 212227, 301331 y 915727. Cada una se pasa como seed de LightGBM (línea 208). El comentario indica que las 5 primeras son las propias y las otras 15 son primos sorteados con la semilla 285937; el código que las sortea está en bayesiana_competencia_01_ejecutado.ipynb (líneas 237-244). Se crea un lgb.Dataset nuevo al empezar la semilla 1 y la semilla 11 (líneas 206-207).
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio aritmético de las probabilidades de los 20 modelos sobre los clientes de 202108 (línea 219). Todos los modelos tienen los mismos hiperparámetros y difieren en la semilla.
- **Corte:** Cantidad fija: los 13.000 clientes de mayor probabilidad promedio (K_ENTREGA = 13000, línea 57). El notebook genera además un archivo por cada corte de 12.500 a 14.500 de a 250 (líneas 56 y 241-242). Según el README, esos cortes se probaron contra el pseudo Kaggle y el entregado es K = 13.000; el código no contiene esa comparación.
- **Validación:** En la búsqueda de hiperparámetros: entrenamiento en 202103-202105 y AUC sobre 202106 (bayesiana_competencia_01_ejecutado.ipynb, líneas 42-43 y 156-186). Ese mismo notebook calcula sobre 202106 la curva de ganancia acumulada (+1.072.500 y -27.500) del promedio de los 10 trials de mayor AUC (líneas 210-228). En competencia_FINAL.ipynb no hay mes de validación: entrena con 202103-202106 y la última celda compara el archivo generado con ensamble_K13000_ENTREGADO.csv (líneas 255-263).
- **Salidas:** En salida/: pred_202108_seed{semilla}.npy (uno por semilla, 20 archivos), scores_202108.csv (numero_de_cliente y prob, ordenado de mayor a menor), entregas/ensamble_K{k}.csv para 9 cortes (12.500 a 14.500 de a 250; sin encabezado, una columna, fin de línea \r\n) y config.json. La carpeta salida/ está en .gitignore; el repositorio trae aparte ensamble_K13000_ENTREGADO.csv y bo_resultados.csv.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Técnicas sólo exploradas

- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Según entrega_final/README.md: Windows 10, CPU de 8 núcleos, Python 3.12.10, lightgbm==4.7.0, numpy==2.5.3 y pandas==3.0.6; corrida de principio a fin en 2 h 24 min. requirements.txt fija 12 paquetes con versión exacta. El README indica que en otra máquina los modelos podrían diferir en los últimos decimales.

## Pasos del camino de la entrega

1. **Configuración.** Define rutas relativas (datos/ y salida/), meses de entrenamiento (202103 a 202106) y de predicción (202108), las 12 variables a eliminar, las 20 semillas, los cortes (12.500 a 14.500 de a 250; entrega con 13.000) y los hiperparámetros de LightGBM. (`entrega_final/competencia_FINAL.ipynb` líneas 25–65)
2. **Lectura del dataset y cálculo de clase_ternaria.** Lee competencia_01_crudo.csv (o un parquet ya guardado), calcula periodo0 y arma clase_ternaria mirando si el cliente tiene registro en el mes siguiente y en el subsiguiente. Pasa las columnas numéricas a float32 y guarda el resultado en competencia_01.parquet. (`entrega_final/competencia_FINAL.ipynb` líneas 74–95)
3. **Calidad de datos: ccajas_depositos en 202105.** Asigna NA a ccajas_depositos sólo en el mes 202105. (`entrega_final/competencia_FINAL.ipynb` líneas 102–104)
4. **Eliminación de 12 variables y ranking mensual de las monetarias.** Elimina las 12 variables de la lista y reemplaza cada columna cuyo nombre empieza con 'm' por su ranking dentro de cada foto_mes: de 0 a 1 si no tiene negativos; de -1 a 1 con el cero fijo si los tiene. (`entrega_final/competencia_FINAL.ipynb` líneas 47–50; `entrega_final/competencia_FINAL.ipynb` líneas 115–129)
5. **Lags y delta-lags de orden 1 y 2.** Sobre los valores ya rankeados, agrega para cada variable el valor de 1 y 2 meses atrás y la diferencia entre el valor del mes y cada lag, uniendo por cliente y período. Arma la lista de variables de entrada y la clase binaria y_pos (BAJA+1 o BAJA+2). (`entrega_final/competencia_FINAL.ipynb` líneas 137–161)
6. **Búsqueda de hiperparámetros con Optuna (notebook aparte).** bayesiana_competencia_01_ejecutado.ipynb corre 30 trials de Optuna/TPE que entrenan en 202103-202105 y miden AUC en 202106, buscando num_leaves, min_sum_hessian_in_leaf y num_iterations, y guarda la tabla de trials en bo_resultados.csv. Ese notebook usa la clase y = BAJA+2 y no incluye la eliminación de variables ni el ranking. El notebook final lee bo_resultados.csv y comprueba con assert que la fila de mayor AUC (trial 27) coincide con los hiperparámetros escritos en PARAMS. (`entrega_final/bayesiana_competencia_01_ejecutado.ipynb` líneas 156–202; `entrega_final/competencia_FINAL.ipynb` líneas 173–179)
7. **Entrenamiento final con 20 semillas.** Entrena 20 modelos LightGBM de 1.050 iteraciones sobre 202103-202106, con los mismos hiperparámetros y distinta seed, sin submuestreo. Crea un Dataset nuevo en la semilla 1 y en la 11. Cada modelo predice 202108 y su predicción se guarda en un archivo .npy. (`entrega_final/competencia_FINAL.ipynb` líneas 191–211)
8. **Promedio de las 20 predicciones.** Promedia las probabilidades de las 20 semillas por cliente, ordena de mayor a menor y guarda scores_202108.csv. (`entrega_final/competencia_FINAL.ipynb` líneas 218–226)
9. **Corte y archivos de salida.** Escribe un CSV sin encabezado con los primeros k clientes para cada corte de 12.500 a 14.500 de a 250; el de 13.000 es el que el notebook señala como entregado. Guarda la configuración de la corrida en config.json. (`entrega_final/competencia_FINAL.ipynb` líneas 234–248)
10. **Comparación con el archivo entregado.** Compara salida/entregas/ensamble_K13000.csv con ensamble_K13000_ENTREGADO.csv: mismos clientes, mismo orden y mismos bytes. Según el README y la salida guardada del notebook ejecutado, las tres comparaciones dieron True. (`entrega_final/competencia_FINAL.ipynb` líneas 255–263)

## Archivos

- `README.md` · explicacion · Markdown · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mmfiora/README.md.txt) — README de la raíz: indica que todo lo necesario para replicar la entrega está en entrega_final/ y enlaza el CSV entregado (ganancia pública 105,0225 según el texto), el notebook que lo reproduce y el README de esa carpeta.
- `entrega_final/competencia_FINAL_ejecutado.ipynb` · principal · Jupyter (python) · 263 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mmfiora/entrega_final/competencia_FINAL_ejecutado.ipynb.txt) — El mismo notebook que competencia_FINAL.ipynb, con las salidas de una ejecución guardadas en el .ipynb original. En la copia canónica (sólo celdas de código y texto) coincide línea por línea con competencia_FINAL.ipynb, por lo que las anotaciones son las mismas.
- `entrega_final/bayesiana_competencia_01_ejecutado.ipynb` · principal · Jupyter (python) · 321 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mmfiora/entrega_final/bayesiana_competencia_01_ejecutado.ipynb.txt) — Notebook en Python con la búsqueda de hiperparámetros (Optuna/TPE, 30 trials, AUC en 202106) que produce bo_resultados.csv, del que el notebook final toma num_leaves, min_sum_hessian_in_leaf y num_iterations (celdas 3 a 12). Las celdas 13 a 20 contienen una curva de ganancia en 202106, un entrenamiento final con 20 semillas, el promedio y la generación de archivos con cortes de 8.000 a 15.000; esas salidas no las lee competencia_FINAL.ipynb. No incluye la eliminación de las 12 variables ni el ranking mensual, y su clase es y = BAJA+2.
- `entrega_final/requirements.txt` · configuracion · Texto · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mmfiora/entrega_final/requirements.txt.txt) — Lista de 12 paquetes de Python con versión exacta: numpy 2.5.3, pandas 3.0.6, lightgbm 4.7.0, pyarrow 25.0.1, scikit-learn 1.9.1, scipy 1.18.1, optuna 5.0.0, matplotlib 3.11.2, jupyterlab 4.6.3, ipykernel 7.3.0, nbconvert 7.17.1 y nbformat 5.11.1.
- `entrega_final/README.md` · explicacion · Markdown · 79 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mmfiora/entrega_final/README.md.txt) — Texto de presentación de la entrega: describe el archivo entregado (13.000 clientes, ganancia pública y MD5), lista los archivos de la carpeta, da los pasos para reproducir la predicción, resume el modelo en 8 puntos (clase, calidad de datos, drifting, lags, búsqueda bayesiana, entrenamiento final, scoring y corte) y declara el entorno y el resultado de la verificación byte a byte.
- `entrega_final/competencia_FINAL.ipynb` · principal · Jupyter (?) · 263 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mmfiora/entrega_final/competencia_FINAL.ipynb.txt) — Notebook en Python que, desde el CSV crudo, prepara los datos, entrena 20 modelos LightGBM sobre 202103-202106, promedia sus probabilidades sobre 202108 y escribe los archivos de corte; la última celda compara el de 13.000 clientes con el archivo entregado. Copia sin salidas guardadas.
- `entrega_final/datos/LEEME.txt` · explicacion · Texto · 9 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mmfiora/entrega_final/datos/LEEME.txt.txt) — Indica que en esa carpeta va competencia_01_crudo.csv, que no se sube al repositorio por su tamaño, y da la URL de descarga y un ejemplo con curl.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### entrega_final/competencia_FINAL_ejecutado.ipynb

El mismo notebook que competencia_FINAL.ipynb, con las salidas de una ejecución guardadas en el .ipynb original. En la copia canónica (sólo celdas de código y texto) coincide línea por línea con competencia_FINAL.ipynb, por lo que las anotaciones son las mismas.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] Celdas de texto de presentación: tabla con las etapas del notebook (0, 1.1, 1.2,
#   1.4, 1.7, 2.1, 2.2 y 2.3), los valores de ganancia (+1.072.500 por BAJA+2 enviado, -27.500 por envío sin
#   acierto) y la definición de la clase de entrenamiento (positivo = BAJA+1 o BAJA+2, negativo = CONTINUA).
#%% celda 1 [texto]
# DMEyF 2026 - Primera Competencia: modelo final (rank_signo, 20 semillas)

Predicción de **BAJA+2** del Paquete Premium. Este notebook reproduce, desde el CSV crudo, el archivo que se entregó:
**`ensamble_K13000.csv`** (13.000 clientes de 202108), con una ganancia pública de **105,02**.

| Etapa | Qué hace |
|---|---|
| 0 | Carga el CSV crudo y calcula `clase_ternaria` |
| 1.1 | Data Quality: `ccajas_depositos` rota en 202105 (todos ceros) -> `NA` solo en ese mes |
| 1.2 | Data Drifting: se eliminan 12 variables (`cprestamos_personales`, `mprestamos_personales` y las 10 con mayor KS entre 202103-05 y 202108) y se aplica **ranking mensual** a las variables monetarias `m*` (de -1 a 1 con el cero fijo si tienen valores negativos; de 0 a 1 si no). El ranking se hace **antes** de calcular lags y deltas |
| 1.4 | Feature Engineering histórico: lags y delta-lags de orden 1 y 2 |
| 1.7 | Bayesian Optimization (Optuna/TPE, AUC, sin undersampling): ver la sección correspondiente |
| 2.1 | Final training: 20 semillas con los mismos hiperparámetros, en 202103-202106, sin undersampling |
| 2.2 | Scoring de 202108 y ensamble promediando las probabilidades por `numero_de_cliente` |
| 2.3 | Cortes de envíos K (12.500 a 14.500) para probar contra el pseudo Kaggle |

Ganancia: acierto (BAJA+2 enviado) = **+1.072.500**, envío inútil = **-27.500**.
La clase de entrenamiento es binaria, POS = {BAJA+1, BAJA+2} y NEG = CONTINUA; la ganancia solo cuenta los BAJA+2.

#%% celda 2 [texto]
## Configuración

# [Anotación · líneas 24–45] Importa json, time, platform, warnings, pathlib, numpy, pandas y lightgbm e
#   imprime las versiones. Define las rutas: la carpeta de datos es datos/ si contiene competencia_01_crudo.csv
#   o competencia_01.parquet y, si no, ../datos; las salidas van a salida/. Fija los meses de entrenamiento
#   (202103, 202104, 202105 y 202106), el mes a predecir (202108) y los valores de ganancia (1.072.500) y costo
#   (-27.500).
#%% celda 3 [código]
import json, time, platform, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb

warnings.filterwarnings("ignore")
print("python", platform.python_version(), "| numpy", np.__version__, "| pandas", pd.__version__, "| lightgbm", lgb.__version__)

_hay = lambda d: (d / "competencia_01_crudo.csv").exists() or (d / "competencia_01.parquet").exists()
DATA_DIR = Path("datos") if _hay(Path("datos")) else Path("..") / "datos"   # carpeta con competencia_01_crudo.csv
RAW = DATA_DIR / "competencia_01_crudo.csv"
CACHE = DATA_DIR / "competencia_01.parquet"
OUT_DIR = Path("salida")                            # resultados de este notebook
OUT_DIR.mkdir(parents=True, exist_ok=True)

MESES_FINAL = [202103, 202104, 202105, 202106]
MES_APLICAR = 202108
MESES_USO = sorted(set(MESES_FINAL + [MES_APLICAR]))
GANANCIA_ACIERTO, COSTO_ENVIO = 1_072_500, -27_500

# [Anotación · líneas 46–51] Lista las 12 variables que se eliminan: cprestamos_personales,
#   mprestamos_personales, Master_fultimo_cierre, Visa_fultimo_cierre, Master_Finiciomora, Visa_Finiciomora,
#   mcomisiones_mantenimiento, Visa_mpagado, mrentabilidad, Master_Fvencimiento, mpasivos_margen y
#   Visa_Fvencimiento. EXCLUIR nombra las 4 columnas que no entran como variables de entrada: numero_de_cliente,
#   foto_mes, periodo0 y clase_ternaria.
# 12 variables eliminadas: prestamos_personales (la catedra las marca como data drifting) y las 10 con mayor KS
VARIABLES_ELIMINADAS = ["cprestamos_personales", "mprestamos_personales",
                        "Master_fultimo_cierre", "Visa_fultimo_cierre", "Master_Finiciomora", "Visa_Finiciomora",
                        "mcomisiones_mantenimiento", "Visa_mpagado", "mrentabilidad", "Master_Fvencimiento",
                        "mpasivos_margen", "Visa_Fvencimiento"]
EXCLUIR = {"numero_de_cliente", "foto_mes", "periodo0", "clase_ternaria"}
# [Anotación · líneas 52–57] Escribe las 20 semillas (el comentario indica que las 5 primeras son las propias
#   y las otras 15 son primos sorteados con la semilla 285937) y los cortes: KS va de 12.500 a 14.500 de a 250
#   (9 valores) y K_ENTREGA = 13000.

# 20 semillas (las 5 propias, primos entre 100003 y 999983, y 15 primos al azar con la semilla 285937)
SEMILLAS = [285937, 474619, 502487, 600673, 666637, 326219, 213727, 962341, 884959, 305759,
            274583, 556123, 182129, 752489, 852199, 362927, 130307, 212227, 301331, 915727]
KS = list(range(12500, 14501, 250))                 # cortes de envios a probar
K_ENTREGA = 13000                                   # corte entregado
# [Anotación · líneas 58–66] Hiperparámetros de LightGBM en PARAMS: objective binary, metric auc, boosting
#   gbdt, max_bin 31, min_data_in_leaf 0, feature_fraction 0.50, feature_fraction_bynode 0.20, learning_rate
#   0.005, feature_pre_filter False, force_row_wise True, num_leaves 171 y min_sum_hessian_in_leaf
#   7.28721427391867; NUM_ITERATIONS = 1050. DS_PARAMS repite max_bin, min_data_in_leaf y feature_pre_filter
#   para construir el Dataset.

# Hiperparametros: los fijos de la catedra y los 3 optimizados por la Bayesian Optimization (trial 27, ver seccion 1.7)
PARAMS = dict(objective="binary", metric="auc", boosting="gbdt", verbosity=-1,
              max_bin=31, min_data_in_leaf=0, feature_fraction=0.50, feature_fraction_bynode=0.20,
              learning_rate=0.005, feature_pre_filter=False, force_row_wise=True,
              num_leaves=171, min_sum_hessian_in_leaf=7.28721427391867)
NUM_ITERATIONS = 1050
DS_PARAMS = dict(max_bin=31, min_data_in_leaf=0, feature_pre_filter=False)

# [Anotación · líneas 67–96] Si existe competencia_01.parquet lo lee; si no, lee el CSV crudo, ordena por
#   cliente y mes y calcula periodo0 (año × 12 + mes). Con el período del registro siguiente y del subsiguiente
#   de cada cliente arma clase_ternaria: CONTINUA para los meses anteriores al anteúltimo, BAJA+1 si el cliente
#   no tiene registro en el mes siguiente, BAJA+2 si lo tiene en el siguiente y no en el subsiguiente; el último
#   mes queda sin clase y el anteúltimo sólo puede recibir BAJA+1. Pasa las columnas numéricas a float32, guarda
#   el parquet y muestra la cantidad de filas por mes y clase.
#%% celda 4 [texto]
## 0. Dataset y clase_ternaria
El CSV crudo no trae la clase. Se calcula mirando hacia el futuro, igual que el script en R de la cátedra:
`BAJA+1` si el cliente no está en el mes siguiente, `BAJA+2` si está el mes siguiente pero no el subsiguiente, `CONTINUA` el resto.
Los últimos dos meses del dataset quedan sin clase completa (por eso solo se entrena hasta 202106).

#%% celda 5 [código]
if CACHE.exists():
    df = pd.read_parquet(CACHE)
else:
    df = pd.read_csv(RAW, engine="pyarrow")
    df = df.sort_values(["numero_de_cliente", "foto_mes"]).reset_index(drop=True)
    df["periodo0"] = (df.foto_mes // 100) * 12 + df.foto_mes % 100
    g = df.groupby("numero_de_cliente")["periodo0"]
    p1, p2 = g.shift(-1), g.shift(-2)
    ultimo = df.periodo0.max(); anteultimo = ultimo - 1
    clase = np.full(len(df), None, dtype=object)
    clase[(df.periodo0 < anteultimo).to_numpy()] = "CONTINUA"
    m1 = (df.periodo0 < ultimo) & (p1.isna() | (df.periodo0 + 1 < p1))
    clase[m1.to_numpy()] = "BAJA+1"
    m2 = (df.periodo0 < anteultimo) & (df.periodo0 + 1 == p1) & (p2.isna() | (df.periodo0 + 2 < p2))
    clase[m2.to_numpy()] = "BAJA+2"
    df["clase_ternaria"] = clase
    for c in df.columns:                              # float32 para ahorrar memoria
        if c not in ("numero_de_cliente", "foto_mes", "periodo0", "clase_ternaria") and pd.api.types.is_numeric_dtype(df[c]):
            df[c] = df[c].astype("float32")
    df.to_parquet(CACHE)
print(df.shape)
df.groupby(["foto_mes", "clase_ternaria"], dropna=False).size().unstack(fill_value=0)

# [Anotación · líneas 97–105] Imprime cuántos valores distintos de cero tiene ccajas_depositos en 202105,
#   asigna NA a esa variable sólo en ese mes e imprime cuántos valores no nulos quedan.
#%% celda 6 [texto]
## 1.1 Data Quality
`ccajas_depositos` está rota en 202105 (todos ceros) -> se asigna `NA` solo para ese mes.

#%% celda 7 [código]
print("antes: valores no cero en 202105 =", int((df.loc[df.foto_mes == 202105, "ccajas_depositos"] != 0).sum()))
df.loc[df.foto_mes == 202105, "ccajas_depositos"] = np.nan
print("despues: valores no nulos en 202105 =", int(df.loc[df.foto_mes == 202105, "ccajas_depositos"].notna().sum()))

# [Anotación · líneas 106–130] Elimina las 12 variables de VARIABLES_ELIMINADAS. Toma como monetarias las
#   columnas cuyo nombre empieza con 'm' minúscula y las separa según tengan o no algún valor negativo. Las que
#   no tienen negativos se reemplazan por su rango porcentual dentro de cada foto_mes (0 a 1). En las que tienen
#   negativos rankea por mes los positivos entre sí (0 a 1) y los negativos entre sí por valor absoluto, con
#   signo negativo (-1 a 0); el cero queda en 0 y los NA se conservan. El resultado se guarda en float32 sobre
#   la misma columna.
#%% celda 8 [texto]
## 1.2 Data Drifting
Se eliminan 12 variables (listadas en la configuración) y se aplica **ranking mensual** a las variables monetarias `m*`:
- las que tienen valores negativos pasan a un rango de **-1 a 1 con el cero fijo** (los positivos se rankean entre sí de 0 a 1, los negativos de -1 a 0);
- las que no tienen negativos pasan a un rango de **0 a 1**.

El ranking se calcula dentro de cada `foto_mes` y **antes** de calcular los lags y deltas.

#%% celda 9 [código]
df = df.drop(columns=[c for c in VARIABLES_ELIMINADAS if c in df.columns])
MONETARIAS = [c for c in df.columns if c.startswith("m")]
CON_NEGATIVOS = [c for c in MONETARIAS if (df[c] < 0).any()]
SIN_NEGATIVOS = [c for c in MONETARIAS if c not in CON_NEGATIVOS]
print("monetarias rankeadas:", len(MONETARIAS), "| con negativos (-1 a 1):", len(CON_NEGATIVOS), "| sin negativos (0 a 1):", len(SIN_NEGATIVOS))

df[SIN_NEGATIVOS] = df.groupby("foto_mes")[SIN_NEGATIVOS].rank(pct=True).astype("float32")
mes = df["foto_mes"]
for c in CON_NEGATIVOS:
    x = df[c]
    pos = x.where(x > 0).groupby(mes).rank(pct=True)          # positivos: 0 a 1
    neg = (-x).where(x < 0).groupby(mes).rank(pct=True)       # negativos: -1 a 0
    out = np.where(x > 0, pos, np.where(x < 0, -neg, 0.0))    # el cero queda fijo en 0
    out[x.isna().to_numpy()] = np.nan                         # los NA siguen siendo NA
    df[c] = out.astype("float32")

# [Anotación · líneas 131–162] Define agregar_lags: se queda con las filas de los meses de uso (202103 a
#   202106 y 202108) y, para k = 1 y 2, suma k a periodo0 en una copia de la tabla completa y la une por
#   numero_de_cliente y periodo0, con lo que obtiene el valor de k meses atrás (_lag{k}); si el cliente no tiene
#   fila en ese mes queda NA. El delta (_dlag{k}) es el valor del mes menos ese lag. Lo aplica a todas las
#   columnas salvo las 4 de EXCLUIR, arma la lista FEATURES y crea y_pos (1 si BAJA+1 o BAJA+2) e y_gan (1 si
#   BAJA+2); y_gan no se usa en las celdas siguientes.
#%% celda 10 [texto]
## 1.4 Feature Engineering histórico
Lags y delta-lags (valor actual menos valor del lag) de orden 1 y 2 para todas las variables numéricas (calculados sobre los rangos de la sección anterior).
Se calculan alineando por (cliente, período) y no por posición, para no cruzar meses si a un cliente le falta alguno.

#%% celda 11 [código]
cols_base = [c for c in df.columns if c not in EXCLUIR]

def agregar_lags(df, meses_uso, cols, ks=(1, 2)):
    clave = ["numero_de_cliente", "periodo0"]
    uso = df[df.foto_mes.isin(meses_uso)].copy()
    base = df[clave + cols]
    nuevas = []
    for k in ks:
        r = base.copy()
        r["periodo0"] = r["periodo0"] + k                 # el valor de hace k meses cae en el periodo actual
        r.columns = clave + [f"{c}_lag{k}" for c in cols]
        lag = uso[clave].merge(r, on=clave, how="left").drop(columns=clave)
        lag.index = uso.index
        delta = pd.DataFrame(uso[cols].to_numpy() - lag.to_numpy(),
                             columns=[f"{c}_dlag{k}" for c in cols], index=uso.index)
        nuevas += [lag, delta]
    return pd.concat([uso] + nuevas, axis=1)

t0 = time.time()
ds = agregar_lags(df, MESES_USO, cols_base)
del df
FEATURES = [c for c in ds.columns if c not in EXCLUIR]           # sin numero_de_cliente ni foto_mes
ds["y_pos"] = ds.clase_ternaria.isin(["BAJA+1", "BAJA+2"]).astype("int8")   # clase de entrenamiento
ds["y_gan"] = (ds.clase_ternaria == "BAJA+2").astype("int8")                # clase que da la ganancia
print(f"{ds.shape[0]:,} filas, {len(FEATURES)} features, {time.time() - t0:.0f}s")

# [Anotación · líneas 163–180] Lee bo_resultados.csv de la carpeta de trabajo (o de ../exp si no está), lo
#   ordena por value descendente y toma la primera fila. Con assert comprueba que num_leaves, num_iterations y
#   min_sum_hessian_in_leaf de esa fila coinciden con los escritos en PARAMS y NUM_ITERATIONS, y muestra los 8
#   trials de mayor value. La celda de texto describe la búsqueda (Optuna/TPE, 30 trials, AUC, entrenamiento
#   202103-202105, validación 202106) y nombra el notebook de origen como competencia_01.ipynb.
#%% celda 12 [texto]
## 1.7 Bayesian Optimization
Los 3 hiperparámetros optimizados (`num_iterations`, `num_leaves`, `min_sum_hessian_in_leaf`) salen del **trial 27** de la optimización bayesiana del notebook
`competencia_01.ipynb` (Optuna/TPE con `n_startup_trials=8` y semilla 285937, 30 trials, métrica AUC en LightGBM, sin undersampling,
entrenando en 202103-202105 y validando en 202106). Sus resultados completos están guardados en `bo_resultados.csv`
(30 trials; el mejor es el trial 27, AUC 0,90468: 1.050 iteraciones, 171 hojas, `min_sum_hessian_in_leaf` 7,287).
Los hiperparámetros fijos son: `max_bin=31`, `min_data_in_leaf=0`, `feature_fraction=0,50`, `feature_fraction_bynode=0,20`, `learning_rate=0,005`.
Correr la optimización desde cero lleva unas 5 horas, por eso aquí se leen los resultados guardados.

#%% celda 13 [código]
bo = pd.read_csv("bo_resultados.csv") if Path("bo_resultados.csv").exists() else pd.read_csv(Path("..") / "exp" / "bo_resultados.csv")
bo = bo.sort_values("value", ascending=False)
mejor = bo.iloc[0]
assert int(mejor["params_num_leaves"]) == PARAMS["num_leaves"] and int(mejor["params_num_iterations"]) == NUM_ITERATIONS
assert abs(float(mejor["params_min_sum_hessian_in_leaf"]) - PARAMS["min_sum_hessian_in_leaf"]) < 1e-9
print("trial", int(mejor["number"]), "| AUC", round(mejor["value"], 5), "| hiperparametros coinciden con los usados abajo")
bo[["number", "value", "params_num_leaves", "params_min_sum_hessian_in_leaf", "params_num_iterations"]].head(8)

# [Anotación · líneas 181–212] Arma la matriz de entrenamiento con las filas de 202103 a 202106 y la clase
#   y_pos, y la matriz de 202108 con sus numero_de_cliente (verifica que no se repitan). Recorre las 20
#   semillas: en la primera y en la undécima crea un lgb.Dataset nuevo; entrena 1.050 iteraciones con PARAMS y
#   la semilla como seed, predice 202108, guarda las probabilidades en salida/pred_202108_seed{semilla}.npy e
#   imprime el tiempo de cada modelo.
#%% celda 14 [texto]
## 2.1 Final training
Se entrenan 20 modelos con **hiperparámetros idénticos**, cambiando solo la `seed` de LightGBM, en 202103-202106 y sin ningún tipo de undersampling.
Se aplican a los datos de 202108 (sección 2.2).

**Nota de reproducibilidad.** LightGBM discretiza las variables en *bins* la primera vez que se usa un `Dataset`, y esa construcción depende de la semilla
del primer entrenamiento que lo usa. Las 20 semillas se entrenaron en **dos tandas de 10** (semillas 1 a 10 y 11 a 20), cada una con su propio `Dataset`
construido en el primer uso. Para reproducir exactamente el archivo entregado se replica esa estructura: se crea un `Dataset` nuevo al empezar cada tanda.

#%% celda 15 [código]
fin = ds[ds.foto_mes.isin(MESES_FINAL)]
X_fin = fin[FEATURES].to_numpy(np.float32)
y_fin = fin["y_pos"].to_numpy()

def crear_dataset():
    return lgb.Dataset(X_fin, y_fin, params=DS_PARAMS)
apl = ds[ds.foto_mes == MES_APLICAR]
X_apl = apl[FEATURES].to_numpy(np.float32)
ids_apl = apl["numero_de_cliente"].to_numpy().round().astype("int64")
assert len(set(ids_apl)) == len(ids_apl)
print("entrenamiento:", fin.shape[0], "filas | agosto:", apl.shape[0], "clientes")

preds = {}
for i, sem in enumerate(SEMILLAS):
    t0 = time.time()
    if i in (0, 10):          # un Dataset nuevo al empezar cada tanda de 10 semillas (ver la nota de arriba)
        dfinal = crear_dataset()
    modelo = lgb.train(dict(PARAMS, seed=sem), dfinal, num_boost_round=NUM_ITERATIONS)
    preds[sem] = modelo.predict(X_apl).astype("float32")
    np.save(OUT_DIR / f"pred_202108_seed{sem}.npy", preds[sem])
    print(f"modelo {i + 1}/{len(SEMILLAS)}  semilla {sem}  {time.time() - t0:.0f}s", flush=True)

# [Anotación · líneas 213–227] Promedia las probabilidades de las 20 semillas, ordena los clientes de mayor a
#   menor promedio y guarda numero_de_cliente y prob en salida/scores_202108.csv.
#%% celda 16 [texto]
## 2.2 Scoring y ensamble
Cada semilla da un ranking de los clientes de 202108. El ensamble promedia las probabilidades por `numero_de_cliente`.

#%% celda 17 [código]
# promedio de las probabilidades de las 20 semillas, por numero_de_cliente (mismo orden de clientes en todas las semillas)
prob = np.mean(np.vstack([preds[s] for s in SEMILLAS]), axis=0)
orden = np.argsort(-prob)
ids_ordenados = ids_apl[orden]                        # clientes de mayor a menor probabilidad
scores = pd.DataFrame({"numero_de_cliente": ids_ordenados, "prob": prob[orden]})
assert scores.numero_de_cliente.is_unique
scores.to_csv(OUT_DIR / "scores_202108.csv", index=False)
print(scores.shape)
scores.head()

# [Anotación · líneas 228–249] guardar_ids escribe un CSV sin encabezado, de una columna de enteros y con fin
#   de línea \r\n, y exige entre 8.000 y 15.000 ids sin repetir. Genera salida/entregas/ensamble_K{k}.csv con
#   los primeros k clientes para cada k de KS y para K_ENTREGA (12.500 a 14.500 de a 250, 9 archivos) y guarda
#   en salida/config.json las semillas, los cortes, los hiperparámetros, las variables eliminadas y los meses.
#%% celda 18 [texto]
## 2.3 Classification y archivos para el bot
Formato exigido por `@competencia-uno`: `.csv` **sin encabezado**, una sola columna con los `numero_de_cliente` a estimular (enteros), entre 8.000 y 15.000 registros por archivo.
Se generan varios cortes K para compararlos contra el pseudo Kaggle; el entregado es **K = 13.000**.

#%% celda 19 [código]
def guardar_ids(ids, ruta):
    ids = np.asarray(ids).astype("int64")
    assert 8000 <= len(ids) <= 15000 and len(set(ids)) == len(ids)
    pd.DataFrame({"id": ids}).to_csv(ruta, header=False, index=False, lineterminator="\r\n")   # mismos bytes en cualquier sistema operativo

ENT = OUT_DIR / "entregas"
ENT.mkdir(exist_ok=True)
for k in sorted(set(KS + [K_ENTREGA])):
    guardar_ids(ids_ordenados[:k], ENT / f"ensamble_K{k}.csv")

json.dump(dict(semillas=SEMILLAS, ks=KS, k_entrega=K_ENTREGA, params=PARAMS, num_iterations=NUM_ITERATIONS,
               variables_eliminadas=VARIABLES_ELIMINADAS, meses_final=MESES_FINAL, mes_aplicar=MES_APLICAR),
          open(OUT_DIR / "config.json", "w"), indent=2, default=str)
print("archivos en", ENT.resolve())
print("archivo entregado:", ENT / f"ensamble_K{K_ENTREGA}.csv", "|", K_ENTREGA, "clientes")

# [Anotación · líneas 250–263] Si existe ensamble_K13000_ENTREGADO.csv en la carpeta de trabajo, lo compara
#   con salida/entregas/ensamble_K13000.csv e imprime tres resultados: si contienen los mismos clientes como
#   conjunto, si coinciden fila por fila y si los bytes de ambos archivos son iguales. Si no existe, imprime un
#   aviso.
#%% celda 20 [texto]
## Verificación
Compara el archivo generado aquí con el archivo exacto que se subió como entrega final (`ensamble_K13000_ENTREGADO.csv`, ganancia pública 105,0225).

#%% celda 21 [código]
ENTREGADO = Path("ensamble_K13000_ENTREGADO.csv")
if ENTREGADO.exists():
    a = pd.read_csv(ENT / f"ensamble_K{K_ENTREGA}.csv", header=None)[0].to_numpy()
    b = pd.read_csv(ENTREGADO, header=None)[0].to_numpy()
    print("mismos clientes (como conjunto):", set(a) == set(b))
    print("mismo orden fila por fila      :", bool((a == b).all()))
    print("archivos identicos byte a byte :", (ENT / f"ensamble_K{K_ENTREGA}.csv").read_bytes() == ENTREGADO.read_bytes())
else:
    print("no se encontro ensamble_K13000_ENTREGADO.csv en esta carpeta; nada que comparar")
```

### entrega_final/bayesiana_competencia_01_ejecutado.ipynb

Notebook en Python con la búsqueda de hiperparámetros (Optuna/TPE, 30 trials, AUC en 202106) que produce bo_resultados.csv, del que el notebook final toma num_leaves, min_sum_hessian_in_leaf y num_iterations (celdas 3 a 12). Las celdas 13 a 20 contienen una curva de ganancia en 202106, un entrenamiento final con 20 semillas, el promedio y la generación de archivos con cortes de 8.000 a 15.000; esas salidas no las lee competencia_FINAL.ipynb. No incluye la eliminación de las 12 variables ni el ranking mensual, y su clase es y = BAJA+2.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–19] Celdas de texto de presentación: tabla de etapas del notebook (0 carga y
#   clase_ternaria, 1.1 calidad de datos, 1.4 lags y delta-lags, 1.7 búsqueda bayesiana con Optuna/TPE, 2.1
#   entrenamiento final con 20 semillas, 2.2 scoring, 2.3 corte y archivos para el bot) y valores de ganancia
#   (+1.072.500 y -27.500).
#%% celda 1 [texto]
# DMEyF 2026 - Primera Competencia
Predicción de **BAJA+2** del Paquete Premium. Notebook en Python / LightGBM que sigue la hoja de ruta de Gustavo Denicolay.

| Etapa | Qué hace |
|---|---|
| 0 | Carga el dataset crudo y calcula `clase_ternaria` |
| 1.1 | Data Quality: `ccajas_depositos` rota en 202105 -> `NaN` |
| 1.4 | Feature Engineering histórico: lags y delta-lags de orden 1 y 2 |
| 1.7 | Bayesian Optimization (Optuna/TPE), métrica AUC, sin undersampling |
| 2.1 | Final training: mejor trial, 20 semillas distintas, en 202103-202106 |
| 2.2 | Scoring de 202108, un archivo por semilla + ensamble promediado |
| 2.3 | Corte por cantidad de envíos K y archivos para el bot `@competencia-uno` |

Ganancia: acierto (BAJA+2 enviado) = **+1.072.500**, envío inútil = **-27.500**.

#%% celda 2 [texto]
## Configuración

# [Anotación · líneas 20–47] Importa numpy, pandas, lightgbm, optuna y matplotlib. Define las 5 semillas
#   propias (285937, 474619, 502487, 600673 y 666637) y toma la primera como SEMILLA. Usa las rutas relativas
#   ../datos y ../exp; el comentario indica que ../datos es un acceso a una carpeta de Google Drive. Fija los
#   meses: cada trial entrena con 202103, 202104 y 202105 y valida en 202106; el entrenamiento final usa 202103
#   a 202106 y se aplica a 202108.
#%% celda 3 [código]
import json, time, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb
import optuna
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

# ---- mis semillas (primos entre 100003 y 999983) ----
SEMILLAS_PROPIAS = [285937, 474619, 502487, 600673, 666637]
SEMILLA = SEMILLAS_PROPIAS[0]

DATA_DIR = Path("..") / "datos"      # acceso (junction) a G:/My Drive/dmeyf/datasets, no se commitea
EXP_DIR = Path("..") / "exp"                        # resultados del experimento
EXP_DIR.mkdir(exist_ok=True, parents=True)
RAW = DATA_DIR / "competencia_01_crudo.csv"
CACHE = DATA_DIR / "competencia_01.parquet"

MESES_BO_TRAIN = [202103, 202104, 202105]   # entrena cada trial de la optimización
MES_BO_VALID = 202106                        # valida cada trial (último mes con clase completa)
MESES_FINAL = [202103, 202104, 202105, 202106]
MES_APLICAR = 202108

GANANCIA_ACIERTO, COSTO_ENVIO = 1_072_500, -27_500
# [Anotación · líneas 48–60] Parámetros de la corrida: 30 trials, 10 trials para la curva de ganancia en
#   validación, 20 semillas, num_iterations entre 300 y 2.500 y cortes de 8.000 a 15.000 de a 500. MODO_RAPIDO
#   está en False; en True reduce a 3 trials, 2 semillas y 50 a 150 iteraciones y escribe en ../exp/rapido.

N_TRIALS = 30            # trials de la Bayesian Optimization
N_TOP_VALID = 10         # mejores trials usados solo para la curva de ganancia en validación
N_SEMILLAS = 20          # modelos finales: mismos hiperparámetros, cambia solo la seed (máx 20 archivos por submit)
NITER_MIN, NITER_MAX = 300, 2500
KS = list(range(8000, 15001, 500))   # cantidades de envíos a probar (el bot acepta 8000-15000 por archivo)

MODO_RAPIDO = False      # True = prueba de humo con pocos datos, NO usar para la entrega
if MODO_RAPIDO:
    N_TRIALS, N_SEMILLAS, NITER_MIN, NITER_MAX = 3, 2, 50, 150
    EXP_DIR = EXP_DIR / "rapido"; EXP_DIR.mkdir(exist_ok=True, parents=True)
print("semilla", SEMILLA, "| rapido" if MODO_RAPIDO else "| entrega real")

# [Anotación · líneas 61–99] Lee competencia_01.parquet si existe; si no, lee el CSV crudo, calcula periodo0 y
#   clase_ternaria con el período del registro siguiente y del subsiguiente de cada cliente (CONTINUA, BAJA+1,
#   BAJA+2; sin clase donde falta información futura), pasa las columnas numéricas a float32 y guarda el
#   parquet. Imprime las dimensiones, las columnas no numéricas y la cantidad de filas por mes y clase.
#%% celda 4 [texto]
## 0. Dataset y clase_ternaria
El CSV crudo no trae la clase. Se calcula mirando hacia el futuro, igual que el script en R de la cátedra:
`BAJA+1` si el cliente no está en el mes siguiente, `BAJA+2` si está el mes siguiente pero no el subsiguiente, `CONTINUA` el resto.
Los últimos dos meses del dataset quedan sin clase completa (por eso solo se puede entrenar hasta 202106).

#%% celda 5 [código]
if CACHE.exists():
    df = pd.read_parquet(CACHE)
else:
    t0 = time.time()
    df = pd.read_csv(RAW, engine="pyarrow")
    df = df.sort_values(["numero_de_cliente", "foto_mes"]).reset_index(drop=True)
    df["periodo0"] = (df.foto_mes // 100) * 12 + df.foto_mes % 100

    g = df.groupby("numero_de_cliente")["periodo0"]
    p1, p2 = g.shift(-1), g.shift(-2)
    ultimo = df.periodo0.max(); anteultimo = ultimo - 1

    clase = np.full(len(df), None, dtype=object)
    clase[(df.periodo0 < anteultimo).to_numpy()] = "CONTINUA"
    m1 = (df.periodo0 < ultimo) & (p1.isna() | (df.periodo0 + 1 < p1))
    clase[m1.to_numpy()] = "BAJA+1"
    m2 = (df.periodo0 < anteultimo) & (df.periodo0 + 1 == p1) & (p2.isna() | (df.periodo0 + 2 < p2))
    clase[m2.to_numpy()] = "BAJA+2"
    df["clase_ternaria"] = clase

    # float32 para ahorrar memoria
    for c in df.columns:
        if c not in ("numero_de_cliente", "foto_mes", "periodo0", "clase_ternaria") \
                and pd.api.types.is_numeric_dtype(df[c]):
            df[c] = df[c].astype("float32")
    df.to_parquet(CACHE)
    print(f"clase_ternaria calculada y cacheada en {time.time()-t0:.0f}s")

print(df.shape)
print("columnas no numéricas:", [c for c in df.columns if df[c].dtype == object and c != "clase_ternaria"])
df.groupby(["foto_mes", "clase_ternaria"], dropna=False).size().unstack(fill_value=0)

# [Anotación · líneas 100–111] Si existe la columna ccajas_depositos, imprime cuántos valores distintos tiene
#   en 202105, le asigna NaN en ese mes e imprime cuántos no nulos quedan; si no existe, imprime un aviso.
#%% celda 6 [texto]
## 1.1 Data Quality
`ccajas_depositos` está rota en 202105 (todos ceros) -> se asigna `NaN` solo para ese mes.

#%% celda 7 [código]
if "ccajas_depositos" in df.columns:
    print("antes: valores distintos en 202105 =", df.loc[df.foto_mes == 202105, "ccajas_depositos"].nunique())
    df.loc[df.foto_mes == 202105, "ccajas_depositos"] = np.nan
    print("despues: no nulos en 202105 =", df.loc[df.foto_mes == 202105, "ccajas_depositos"].notna().sum())
else:
    print("ATENCION: no existe la columna ccajas_depositos, revisar el diccionario de datos")

# [Anotación · líneas 112–146] Define agregar_lags (lag 1 y 2 y delta-lag 1 y 2, uniendo por numero_de_cliente
#   y periodo0 desplazado k meses) y la aplica a todas las columnas salvo numero_de_cliente, foto_mes, periodo0
#   y clase_ternaria, para los meses 202103 a 202106 y 202108. Crea la clase y = 1 si clase_ternaria es BAJA+2 y
#   0 en el resto. Imprime la cantidad de filas y de variables y la proporción de valores no nulos de cinco
#   columnas _lag2 en 202103.
#%% celda 8 [texto]
## 1.4 Feature Engineering histórico
Lags y delta-lags (valor actual menos valor del lag) de orden 1 y 2 para todas las variables numéricas.
Se calculan alineando por (cliente, período) y no por posición, para no cruzar meses si a un cliente le falta alguno.

#%% celda 9 [código]
EXCLUIR = {"numero_de_cliente", "foto_mes", "periodo0", "clase_ternaria"}
cols_base = [c for c in df.columns if c not in EXCLUIR]
MESES_USO = sorted(set(MESES_FINAL + [MES_APLICAR]))

def agregar_lags(df, meses_uso, cols, ks=(1, 2)):
    clave = ["numero_de_cliente", "periodo0"]
    uso = df[df.foto_mes.isin(meses_uso)].copy()
    base = df[clave + cols]
    nuevas = []
    for k in ks:
        r = base.copy()
        r["periodo0"] = r["periodo0"] + k          # el valor de hace k meses cae en el período actual
        r.columns = clave + [f"{c}_lag{k}" for c in cols]
        lag = uso[clave].merge(r, on=clave, how="left").drop(columns=clave)
        lag.index = uso.index
        delta = pd.DataFrame(uso[cols].to_numpy() - lag.to_numpy(),
                             columns=[f"{c}_dlag{k}" for c in cols], index=uso.index)
        nuevas += [lag, delta]
    return pd.concat([uso] + nuevas, axis=1)

t0 = time.time()
ds = agregar_lags(df, MESES_USO, cols_base)
del df
FEATURES = [c for c in ds.columns if c not in EXCLUIR]
ds["y"] = (ds.clase_ternaria == "BAJA+2").astype("int8")
print(f"{ds.shape[0]:,} filas, {len(FEATURES)} features, {time.time()-t0:.0f}s")
print("lags 1 y 2 disponibles en 202103:",
      ds.loc[ds.foto_mes == 202103, [c for c in FEATURES if c.endswith("_lag2")][:5]].notna().mean().round(2).to_dict())

# [Anotación · líneas 147–174] Separa entrenamiento (202103 a 202105) y validación (202106) y arma las
#   matrices en float32. FIJOS contiene los hiperparámetros que no se buscan: objective binary, metric auc,
#   boosting gbdt, max_bin 31, min_data_in_leaf 0, feature_fraction 0.50, feature_fraction_bynode 0.20,
#   learning_rate 0.005, feature_pre_filter False, force_row_wise True y seed 285937. Crea los Dataset de
#   LightGBM de entrenamiento y de validación y la carpeta ../exp/pred_valid.
#%% celda 10 [texto]
## 1.7 Bayesian Optimization
- Sin undersampling de la clase mayoritaria.
- Métrica **AUC** en LightGBM.
- Hiperparámetros fijos: `max_bin=31`, `min_data_in_leaf=0`, `feature_fraction=0.50`, `feature_fraction_bynode=0.20`, `learning_rate=0.005`.
- Hiperparámetros bayesianos: `num_iterations`, `num_leaves`, `min_sum_hessian_in_leaf`.
- Cada trial entrena en 202103-202105 y valida en 202106.

#%% celda 11 [código]
tr = ds[ds.foto_mes.isin(MESES_BO_TRAIN)]
va = ds[ds.foto_mes == MES_BO_VALID]
if MODO_RAPIDO:
    tr = tr.sample(frac=0.10, random_state=SEMILLA)
X_tr, y_tr = tr[FEATURES].to_numpy(np.float32), tr["y"].to_numpy()
X_va, y_va = va[FEATURES].to_numpy(np.float32), va["y"].to_numpy()
print(f"train {X_tr.shape}  positivos {y_tr.mean():.4%} | valid {X_va.shape}  positivos {y_va.mean():.4%}")

FIJOS = dict(
    objective="binary", metric="auc", boosting="gbdt", verbosity=-1,
    max_bin=31, min_data_in_leaf=0, feature_fraction=0.50, feature_fraction_bynode=0.20,
    learning_rate=0.005, feature_pre_filter=False, force_row_wise=True, seed=SEMILLA,
)
DS_PARAMS = dict(max_bin=31, min_data_in_leaf=0, feature_pre_filter=False)
dtrain = lgb.Dataset(X_tr, y_tr, params=DS_PARAMS, free_raw_data=False)
dvalid = lgb.Dataset(X_va, y_va, reference=dtrain, params=DS_PARAMS, free_raw_data=False)

PRED_DIR = EXP_DIR / "pred_valid"; PRED_DIR.mkdir(exist_ok=True)

# [Anotación · líneas 175–198] objective propone num_leaves (entero entre 8 y 1.024, escala logarítmica),
#   min_sum_hessian_in_leaf (entre 0,001 y 50, escala logarítmica) y num_iterations (entero entre 300 y 2.500),
#   entrena esa cantidad de iteraciones sin detención temprana, guarda la predicción sobre 202106 en un .npy por
#   trial y devuelve el AUC de validación de la última iteración. El estudio de Optuna maximiza, usa TPESampler
#   con seed 285937 y 8 trials iniciales, se guarda en ../exp/bo.db y, si ya existe, corre sólo los trials que
#   faltan hasta 30.
def objective(trial):
    params = dict(FIJOS)
    params["num_leaves"] = trial.suggest_int("num_leaves", 8, 1024, log=True)
    params["min_sum_hessian_in_leaf"] = trial.suggest_float("min_sum_hessian_in_leaf", 1e-3, 50.0, log=True)
    n_iter = trial.suggest_int("num_iterations", NITER_MIN, NITER_MAX)
    evals = {}
    t0 = time.time()
    booster = lgb.train(params, dtrain, num_boost_round=n_iter, valid_sets=[dvalid],
                        valid_names=["valid"], callbacks=[lgb.record_evaluation(evals)])
    np.save(PRED_DIR / f"trial_{trial.number}.npy", booster.predict(X_va).astype("float32"))
    trial.set_user_attr("segundos", round(time.time() - t0))
    return evals["valid"]["auc"][-1]

study = optuna.create_study(
    direction="maximize", study_name="bo_lgbm",
    storage=f"sqlite:///{(EXP_DIR / 'bo.db').as_posix()}", load_if_exists=True,
    sampler=optuna.samplers.TPESampler(seed=SEMILLA, n_startup_trials=8),
)
faltan = N_TRIALS - len([t for t in study.trials if t.state.name == "COMPLETE"])
print("trials a correr:", max(faltan, 0), "(si se corta, volver a correr esta celda: retoma desde donde quedó)")
if faltan > 0:
    study.optimize(objective, n_trials=faltan,
                   callbacks=[lambda s, t: print(f"trial {t.number:>3}  AUC {t.value:.5f}  {t.params}  {t.user_attrs['segundos']}s")])

# [Anotación · líneas 199–203] Pasa los trials completos a una tabla ordenada por AUC descendente, la guarda
#   en ../exp/bo_resultados.csv y muestra los 12 primeros.
#%% celda 12 [código]
bo = study.trials_dataframe().query("state == 'COMPLETE'").sort_values("value", ascending=False)
bo.to_csv(EXP_DIR / "bo_resultados.csv", index=False)
bo[["number", "value", "params_num_leaves", "params_min_sum_hessian_in_leaf", "params_num_iterations", "user_attrs_segundos"]].head(12)

# [Anotación · líneas 204–229] Promedia las predicciones sobre 202106 de los 10 trials de mayor AUC, ordena
#   los clientes por ese promedio y calcula la ganancia acumulada (+1.072.500 si y = 1, -27.500 si no). Imprime
#   el máximo, la cantidad y la proporción de envíos en que ocurre y su equivalente en cantidad de clientes de
#   202108, y grafica la curva escalada a 202108 con líneas verticales en 8.000 y 15.000.
#%% celda 13 [texto]
## Ganancia en validación según cantidad de envíos
Ensamble de los mejores trials sobre 202106 (que ningún modelo vio al entrenar). Sirve de guía para elegir K:
la ganancia máxima sale para una proporción de envíos, que se traslada a 202108.

#%% celda 14 [código]
top = bo.head(N_TOP_VALID)
pv = np.mean([np.load(PRED_DIR / f"trial_{int(n)}.npy") for n in top["number"]], axis=0)
orden = np.argsort(-pv)
g = np.where(y_va[orden] == 1, GANANCIA_ACIERTO, COSTO_ENVIO).cumsum()
prop = np.arange(1, len(g) + 1) / len(g)

n_apl = int((ds.foto_mes == MES_APLICAR).sum())
mejor = g.argmax()
print(f"clientes en 202106: {len(g):,} | en {MES_APLICAR}: {n_apl:,}")
print(f"máximo en validación: {g[mejor]:,.0f} con {mejor+1:,} envíos ({prop[mejor]:.2%}) "
      f"-> equivalente a ~{int(prop[mejor]*n_apl):,} envíos en {MES_APLICAR}")

plt.figure(figsize=(9, 4))
plt.plot(prop * n_apl, g * (n_apl / len(g)))
for k in (KS[0], KS[-1]):
    plt.axvline(k, color="gray", ls=":")
plt.xlabel(f"envíos (escalado a {MES_APLICAR})"); plt.ylabel("ganancia (escalada)")
plt.title("Curva de ganancia en validación (202106), ensamble de los mejores trials"); plt.grid(alpha=.3)
plt.show()

# [Anotación · líneas 230–252] Completa la lista de semillas hasta 20: parte de las 5 propias y agrega primos
#   entre 100.003 y 999.983 sorteados con numpy.random.default_rng(285937). Toma la primera fila de la tabla de
#   trials (mayor AUC) y arma los hiperparámetros finales con su num_leaves, min_sum_hessian_in_leaf y
#   num_iterations.
#%% celda 15 [texto]
## 2.1 Final training
Se toma el **mejor trial** de la optimización y se entrenan `N_SEMILLAS` modelos con hiperparámetros idénticos,
cambiando solo la `seed` de LightGBM, en 202103-202106 y sin undersampling.
Así el bot devuelve la media y el desvío de la ganancia y se reduce el overfitting al Public Leaderboard.

#%% celda 16 [código]
def es_primo(n):
    return n > 1 and all(n % i for i in range(2, int(n ** 0.5) + 1))
rng = np.random.default_rng(SEMILLA)
semillas = SEMILLAS_PROPIAS[:N_SEMILLAS]   # primero las 5 propias, el resto se completa con primos al azar
while len(semillas) < N_SEMILLAS:
    p = int(rng.integers(100_003, 999_983))
    if es_primo(p) and p not in semillas:
        semillas.append(p)

mejor_t = bo.iloc[0]
params_final = dict(FIJOS,
                    num_leaves=int(mejor_t["params_num_leaves"]),
                    min_sum_hessian_in_leaf=float(mejor_t["params_min_sum_hessian_in_leaf"]))
n_iter_final = int(mejor_t["params_num_iterations"])
print("mejor trial", int(mejor_t["number"]), "AUC", round(mejor_t["value"], 5), params_final, "iteraciones", n_iter_final)

# [Anotación · líneas 253–268] Arma un único Dataset con las filas de 202103 a 202106 y la clase y (BAJA+2), y
#   la matriz de 202108. Entrena un modelo por semilla, predice 202108 y guarda cada predicción en
#   ../exp/pred_202108_seed{semilla}.npy.
fin = ds[ds.foto_mes.isin(MESES_FINAL)]
if MODO_RAPIDO:
    fin = fin.sample(frac=0.10, random_state=SEMILLA)
dfinal = lgb.Dataset(fin[FEATURES].to_numpy(np.float32), fin["y"].to_numpy(), params=DS_PARAMS, free_raw_data=False)
apl = ds[ds.foto_mes == MES_APLICAR]
X_apl = apl[FEATURES].to_numpy(np.float32)
ids_apl = apl["numero_de_cliente"].to_numpy()

preds = {}
for i, sem in enumerate(semillas):
    t0 = time.time()
    m = lgb.train(dict(params_final, seed=sem), dfinal, num_boost_round=n_iter_final)
    preds[sem] = m.predict(X_apl)
    np.save(EXP_DIR / f"pred_202108_seed{sem}.npy", preds[sem].astype("float32"))
    print(f"modelo {i+1}/{N_SEMILLAS}  semilla {sem}  {time.time()-t0:.0f}s")

# [Anotación · líneas 269–282] Arma una tabla con una columna de probabilidades por semilla, calcula prob como
#   el promedio por fila, ordena de mayor a menor y la guarda en ../exp/scores_202108.csv.
#%% celda 17 [texto]
## 2.2 Scoring y ensamble
Cada semilla da un ranking de los clientes de 202108. El ensamble promedia las probabilidades por `numero_de_cliente`.

#%% celda 18 [código]
scores = pd.DataFrame({f"s{sem}": p for sem, p in preds.items()})
scores.insert(0, "numero_de_cliente", ids_apl)
assert scores.numero_de_cliente.is_unique
scores["prob"] = scores.drop(columns="numero_de_cliente").mean(axis=1)
scores = scores.sort_values("prob", ascending=False).reset_index(drop=True)
scores.to_csv(EXP_DIR / "scores_202108.csv", index=False)
print(scores.shape)
scores[["numero_de_cliente", "prob"]].head()

# [Anotación · líneas 283–321] guardar_ids escribe un CSV sin encabezado con una columna de enteros (entre
#   8.000 y 15.000 ids sin repetir). Borra y vuelve a crear ../exp/entregas; genera ensamble/ensamble_K{k}.csv
#   para k de 8.000 a 15.000 de a 500 y, para K = 11.000, un archivo por semilla con los 11.000 clientes de
#   mayor probabilidad de ese modelo (carpeta semillas_K11000). Guarda config.json e imprime las primeras 7
#   líneas del archivo de K = 8.000. La celda de texto describe el formato que pide el bot y el mensaje de
#   envío.
#%% celda 19 [texto]
## 2.3 Classification y archivos para el bot
Formato exigido por `@competencia-uno`: `.csv` **sin encabezado**, una sola columna con los `numero_de_cliente` a estimular
(enteros, nunca en notación científica), entre 8000 y 15000 registros por archivo.

- `entregas/ensamble/ensamble_K{K}.csv`: un archivo por K (ensamble). Se pueden mandar varios K en un mismo submit para compararlos.
- `entregas/semillas_K{K}/seed_*.csv`: un archivo por semilla con ese K (máx. 20): el bot informa media y desvío de la ganancia.

Mensaje al bot (privado): cuerpo `submit NombreSinEspacios` + los .csv adjuntos. Vale el **último** submit antes del domingo 11-oct 23:59.

#%% celda 20 [código]
import shutil

def guardar_ids(ids, ruta):
    ids = np.asarray(ids).astype("int64")
    assert 8000 <= len(ids) <= 15000 and len(set(ids)) == len(ids)
    pd.DataFrame({"id": ids}).to_csv(ruta, header=False, index=False)   # sin encabezado, enteros

ENT = EXP_DIR / "entregas"
if ENT.exists():
    shutil.rmtree(ENT)
(ENT / "ensamble").mkdir(parents=True)

for k in KS:
    guardar_ids(scores.numero_de_cliente.iloc[:k], ENT / "ensamble" / f"ensamble_K{k}.csv")

K_SEMILLAS = [11000]   # K(s) para los que se genera el set de archivos por semilla; ajustar según el Public Leaderboard
for k in K_SEMILLAS:
    carpeta = ENT / f"semillas_K{k}"; carpeta.mkdir()
    for sem, p in preds.items():
        top_k = ids_apl[np.argsort(-p)[:k]]
        guardar_ids(top_k, carpeta / f"seed_{sem}_K{k}.csv")

json.dump(dict(semilla=SEMILLA, meses_final=MESES_FINAL, mes_aplicar=MES_APLICAR, n_trials=N_TRIALS,
               semillas_finales=semillas, ks=KS, mejor_trial=params_final, num_iterations=n_iter_final),
          open(EXP_DIR / "config.json", "w"), indent=2, default=str)

print(ENT.resolve())
print(open(ENT / "ensamble" / f"ensamble_K{KS[0]}.csv").read().splitlines()[:7])
```

### entrega_final/competencia_FINAL.ipynb

Notebook en Python que, desde el CSV crudo, prepara los datos, entrena 20 modelos LightGBM sobre 202103-202106, promedia sus probabilidades sobre 202108 y escribe los archivos de corte; la última celda compara el de 13.000 clientes con el archivo entregado. Copia sin salidas guardadas.

```
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] Celdas de texto de presentación: tabla con las etapas del notebook (0, 1.1, 1.2,
#   1.4, 1.7, 2.1, 2.2 y 2.3), los valores de ganancia (+1.072.500 por BAJA+2 enviado, -27.500 por envío sin
#   acierto) y la definición de la clase de entrenamiento (positivo = BAJA+1 o BAJA+2, negativo = CONTINUA).
#%% celda 1 [texto]
# DMEyF 2026 - Primera Competencia: modelo final (rank_signo, 20 semillas)

Predicción de **BAJA+2** del Paquete Premium. Este notebook reproduce, desde el CSV crudo, el archivo que se entregó:
**`ensamble_K13000.csv`** (13.000 clientes de 202108), con una ganancia pública de **105,02**.

| Etapa | Qué hace |
|---|---|
| 0 | Carga el CSV crudo y calcula `clase_ternaria` |
| 1.1 | Data Quality: `ccajas_depositos` rota en 202105 (todos ceros) -> `NA` solo en ese mes |
| 1.2 | Data Drifting: se eliminan 12 variables (`cprestamos_personales`, `mprestamos_personales` y las 10 con mayor KS entre 202103-05 y 202108) y se aplica **ranking mensual** a las variables monetarias `m*` (de -1 a 1 con el cero fijo si tienen valores negativos; de 0 a 1 si no). El ranking se hace **antes** de calcular lags y deltas |
| 1.4 | Feature Engineering histórico: lags y delta-lags de orden 1 y 2 |
| 1.7 | Bayesian Optimization (Optuna/TPE, AUC, sin undersampling): ver la sección correspondiente |
| 2.1 | Final training: 20 semillas con los mismos hiperparámetros, en 202103-202106, sin undersampling |
| 2.2 | Scoring de 202108 y ensamble promediando las probabilidades por `numero_de_cliente` |
| 2.3 | Cortes de envíos K (12.500 a 14.500) para probar contra el pseudo Kaggle |

Ganancia: acierto (BAJA+2 enviado) = **+1.072.500**, envío inútil = **-27.500**.
La clase de entrenamiento es binaria, POS = {BAJA+1, BAJA+2} y NEG = CONTINUA; la ganancia solo cuenta los BAJA+2.

#%% celda 2 [texto]
## Configuración

# [Anotación · líneas 24–45] Importa json, time, platform, warnings, pathlib, numpy, pandas y lightgbm e
#   imprime las versiones. Define las rutas: la carpeta de datos es datos/ si contiene competencia_01_crudo.csv
#   o competencia_01.parquet y, si no, ../datos; las salidas van a salida/. Fija los meses de entrenamiento
#   (202103, 202104, 202105 y 202106), el mes a predecir (202108) y los valores de ganancia (1.072.500) y costo
#   (-27.500).
#%% celda 3 [código]
import json, time, platform, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb

warnings.filterwarnings("ignore")
print("python", platform.python_version(), "| numpy", np.__version__, "| pandas", pd.__version__, "| lightgbm", lgb.__version__)

_hay = lambda d: (d / "competencia_01_crudo.csv").exists() or (d / "competencia_01.parquet").exists()
DATA_DIR = Path("datos") if _hay(Path("datos")) else Path("..") / "datos"   # carpeta con competencia_01_crudo.csv
RAW = DATA_DIR / "competencia_01_crudo.csv"
CACHE = DATA_DIR / "competencia_01.parquet"
OUT_DIR = Path("salida")                            # resultados de este notebook
OUT_DIR.mkdir(parents=True, exist_ok=True)

MESES_FINAL = [202103, 202104, 202105, 202106]
MES_APLICAR = 202108
MESES_USO = sorted(set(MESES_FINAL + [MES_APLICAR]))
GANANCIA_ACIERTO, COSTO_ENVIO = 1_072_500, -27_500

# [Anotación · líneas 46–51] Lista las 12 variables que se eliminan: cprestamos_personales,
#   mprestamos_personales, Master_fultimo_cierre, Visa_fultimo_cierre, Master_Finiciomora, Visa_Finiciomora,
#   mcomisiones_mantenimiento, Visa_mpagado, mrentabilidad, Master_Fvencimiento, mpasivos_margen y
#   Visa_Fvencimiento. EXCLUIR nombra las 4 columnas que no entran como variables de entrada: numero_de_cliente,
#   foto_mes, periodo0 y clase_ternaria.
# 12 variables eliminadas: prestamos_personales (la catedra las marca como data drifting) y las 10 con mayor KS
VARIABLES_ELIMINADAS = ["cprestamos_personales", "mprestamos_personales",
                        "Master_fultimo_cierre", "Visa_fultimo_cierre", "Master_Finiciomora", "Visa_Finiciomora",
                        "mcomisiones_mantenimiento", "Visa_mpagado", "mrentabilidad", "Master_Fvencimiento",
                        "mpasivos_margen", "Visa_Fvencimiento"]
EXCLUIR = {"numero_de_cliente", "foto_mes", "periodo0", "clase_ternaria"}
# [Anotación · líneas 52–57] Escribe las 20 semillas (el comentario indica que las 5 primeras son las propias
#   y las otras 15 son primos sorteados con la semilla 285937) y los cortes: KS va de 12.500 a 14.500 de a 250
#   (9 valores) y K_ENTREGA = 13000.

# 20 semillas (las 5 propias, primos entre 100003 y 999983, y 15 primos al azar con la semilla 285937)
SEMILLAS = [285937, 474619, 502487, 600673, 666637, 326219, 213727, 962341, 884959, 305759,
            274583, 556123, 182129, 752489, 852199, 362927, 130307, 212227, 301331, 915727]
KS = list(range(12500, 14501, 250))                 # cortes de envios a probar
K_ENTREGA = 13000                                   # corte entregado
# [Anotación · líneas 58–66] Hiperparámetros de LightGBM en PARAMS: objective binary, metric auc, boosting
#   gbdt, max_bin 31, min_data_in_leaf 0, feature_fraction 0.50, feature_fraction_bynode 0.20, learning_rate
#   0.005, feature_pre_filter False, force_row_wise True, num_leaves 171 y min_sum_hessian_in_leaf
#   7.28721427391867; NUM_ITERATIONS = 1050. DS_PARAMS repite max_bin, min_data_in_leaf y feature_pre_filter
#   para construir el Dataset.

# Hiperparametros: los fijos de la catedra y los 3 optimizados por la Bayesian Optimization (trial 27, ver seccion 1.7)
PARAMS = dict(objective="binary", metric="auc", boosting="gbdt", verbosity=-1,
              max_bin=31, min_data_in_leaf=0, feature_fraction=0.50, feature_fraction_bynode=0.20,
              learning_rate=0.005, feature_pre_filter=False, force_row_wise=True,
              num_leaves=171, min_sum_hessian_in_leaf=7.28721427391867)
NUM_ITERATIONS = 1050
DS_PARAMS = dict(max_bin=31, min_data_in_leaf=0, feature_pre_filter=False)

# [Anotación · líneas 67–96] Si existe competencia_01.parquet lo lee; si no, lee el CSV crudo, ordena por
#   cliente y mes y calcula periodo0 (año × 12 + mes). Con el período del registro siguiente y del subsiguiente
#   de cada cliente arma clase_ternaria: CONTINUA para los meses anteriores al anteúltimo, BAJA+1 si el cliente
#   no tiene registro en el mes siguiente, BAJA+2 si lo tiene en el siguiente y no en el subsiguiente; el último
#   mes queda sin clase y el anteúltimo sólo puede recibir BAJA+1. Pasa las columnas numéricas a float32, guarda
#   el parquet y muestra la cantidad de filas por mes y clase.
#%% celda 4 [texto]
## 0. Dataset y clase_ternaria
El CSV crudo no trae la clase. Se calcula mirando hacia el futuro, igual que el script en R de la cátedra:
`BAJA+1` si el cliente no está en el mes siguiente, `BAJA+2` si está el mes siguiente pero no el subsiguiente, `CONTINUA` el resto.
Los últimos dos meses del dataset quedan sin clase completa (por eso solo se entrena hasta 202106).

#%% celda 5 [código]
if CACHE.exists():
    df = pd.read_parquet(CACHE)
else:
    df = pd.read_csv(RAW, engine="pyarrow")
    df = df.sort_values(["numero_de_cliente", "foto_mes"]).reset_index(drop=True)
    df["periodo0"] = (df.foto_mes // 100) * 12 + df.foto_mes % 100
    g = df.groupby("numero_de_cliente")["periodo0"]
    p1, p2 = g.shift(-1), g.shift(-2)
    ultimo = df.periodo0.max(); anteultimo = ultimo - 1
    clase = np.full(len(df), None, dtype=object)
    clase[(df.periodo0 < anteultimo).to_numpy()] = "CONTINUA"
    m1 = (df.periodo0 < ultimo) & (p1.isna() | (df.periodo0 + 1 < p1))
    clase[m1.to_numpy()] = "BAJA+1"
    m2 = (df.periodo0 < anteultimo) & (df.periodo0 + 1 == p1) & (p2.isna() | (df.periodo0 + 2 < p2))
    clase[m2.to_numpy()] = "BAJA+2"
    df["clase_ternaria"] = clase
    for c in df.columns:                              # float32 para ahorrar memoria
        if c not in ("numero_de_cliente", "foto_mes", "periodo0", "clase_ternaria") and pd.api.types.is_numeric_dtype(df[c]):
            df[c] = df[c].astype("float32")
    df.to_parquet(CACHE)
print(df.shape)
df.groupby(["foto_mes", "clase_ternaria"], dropna=False).size().unstack(fill_value=0)

# [Anotación · líneas 97–105] Imprime cuántos valores distintos de cero tiene ccajas_depositos en 202105,
#   asigna NA a esa variable sólo en ese mes e imprime cuántos valores no nulos quedan.
#%% celda 6 [texto]
## 1.1 Data Quality
`ccajas_depositos` está rota en 202105 (todos ceros) -> se asigna `NA` solo para ese mes.

#%% celda 7 [código]
print("antes: valores no cero en 202105 =", int((df.loc[df.foto_mes == 202105, "ccajas_depositos"] != 0).sum()))
df.loc[df.foto_mes == 202105, "ccajas_depositos"] = np.nan
print("despues: valores no nulos en 202105 =", int(df.loc[df.foto_mes == 202105, "ccajas_depositos"].notna().sum()))

# [Anotación · líneas 106–130] Elimina las 12 variables de VARIABLES_ELIMINADAS. Toma como monetarias las
#   columnas cuyo nombre empieza con 'm' minúscula y las separa según tengan o no algún valor negativo. Las que
#   no tienen negativos se reemplazan por su rango porcentual dentro de cada foto_mes (0 a 1). En las que tienen
#   negativos rankea por mes los positivos entre sí (0 a 1) y los negativos entre sí por valor absoluto, con
#   signo negativo (-1 a 0); el cero queda en 0 y los NA se conservan. El resultado se guarda en float32 sobre
#   la misma columna.
#%% celda 8 [texto]
## 1.2 Data Drifting
Se eliminan 12 variables (listadas en la configuración) y se aplica **ranking mensual** a las variables monetarias `m*`:
- las que tienen valores negativos pasan a un rango de **-1 a 1 con el cero fijo** (los positivos se rankean entre sí de 0 a 1, los negativos de -1 a 0);
- las que no tienen negativos pasan a un rango de **0 a 1**.

El ranking se calcula dentro de cada `foto_mes` y **antes** de calcular los lags y deltas.

#%% celda 9 [código]
df = df.drop(columns=[c for c in VARIABLES_ELIMINADAS if c in df.columns])
MONETARIAS = [c for c in df.columns if c.startswith("m")]
CON_NEGATIVOS = [c for c in MONETARIAS if (df[c] < 0).any()]
SIN_NEGATIVOS = [c for c in MONETARIAS if c not in CON_NEGATIVOS]
print("monetarias rankeadas:", len(MONETARIAS), "| con negativos (-1 a 1):", len(CON_NEGATIVOS), "| sin negativos (0 a 1):", len(SIN_NEGATIVOS))

df[SIN_NEGATIVOS] = df.groupby("foto_mes")[SIN_NEGATIVOS].rank(pct=True).astype("float32")
mes = df["foto_mes"]
for c in CON_NEGATIVOS:
    x = df[c]
    pos = x.where(x > 0).groupby(mes).rank(pct=True)          # positivos: 0 a 1
    neg = (-x).where(x < 0).groupby(mes).rank(pct=True)       # negativos: -1 a 0
    out = np.where(x > 0, pos, np.where(x < 0, -neg, 0.0))    # el cero queda fijo en 0
    out[x.isna().to_numpy()] = np.nan                         # los NA siguen siendo NA
    df[c] = out.astype("float32")

# [Anotación · líneas 131–162] Define agregar_lags: se queda con las filas de los meses de uso (202103 a
#   202106 y 202108) y, para k = 1 y 2, suma k a periodo0 en una copia de la tabla completa y la une por
#   numero_de_cliente y periodo0, con lo que obtiene el valor de k meses atrás (_lag{k}); si el cliente no tiene
#   fila en ese mes queda NA. El delta (_dlag{k}) es el valor del mes menos ese lag. Lo aplica a todas las
#   columnas salvo las 4 de EXCLUIR, arma la lista FEATURES y crea y_pos (1 si BAJA+1 o BAJA+2) e y_gan (1 si
#   BAJA+2); y_gan no se usa en las celdas siguientes.
#%% celda 10 [texto]
## 1.4 Feature Engineering histórico
Lags y delta-lags (valor actual menos valor del lag) de orden 1 y 2 para todas las variables numéricas (calculados sobre los rangos de la sección anterior).
Se calculan alineando por (cliente, período) y no por posición, para no cruzar meses si a un cliente le falta alguno.

#%% celda 11 [código]
cols_base = [c for c in df.columns if c not in EXCLUIR]

def agregar_lags(df, meses_uso, cols, ks=(1, 2)):
    clave = ["numero_de_cliente", "periodo0"]
    uso = df[df.foto_mes.isin(meses_uso)].copy()
    base = df[clave + cols]
    nuevas = []
    for k in ks:
        r = base.copy()
        r["periodo0"] = r["periodo0"] + k                 # el valor de hace k meses cae en el periodo actual
        r.columns = clave + [f"{c}_lag{k}" for c in cols]
        lag = uso[clave].merge(r, on=clave, how="left").drop(columns=clave)
        lag.index = uso.index
        delta = pd.DataFrame(uso[cols].to_numpy() - lag.to_numpy(),
                             columns=[f"{c}_dlag{k}" for c in cols], index=uso.index)
        nuevas += [lag, delta]
    return pd.concat([uso] + nuevas, axis=1)

t0 = time.time()
ds = agregar_lags(df, MESES_USO, cols_base)
del df
FEATURES = [c for c in ds.columns if c not in EXCLUIR]           # sin numero_de_cliente ni foto_mes
ds["y_pos"] = ds.clase_ternaria.isin(["BAJA+1", "BAJA+2"]).astype("int8")   # clase de entrenamiento
ds["y_gan"] = (ds.clase_ternaria == "BAJA+2").astype("int8")                # clase que da la ganancia
print(f"{ds.shape[0]:,} filas, {len(FEATURES)} features, {time.time() - t0:.0f}s")

# [Anotación · líneas 163–180] Lee bo_resultados.csv de la carpeta de trabajo (o de ../exp si no está), lo
#   ordena por value descendente y toma la primera fila. Con assert comprueba que num_leaves, num_iterations y
#   min_sum_hessian_in_leaf de esa fila coinciden con los escritos en PARAMS y NUM_ITERATIONS, y muestra los 8
#   trials de mayor value. La celda de texto describe la búsqueda (Optuna/TPE, 30 trials, AUC, entrenamiento
#   202103-202105, validación 202106) y nombra el notebook de origen como competencia_01.ipynb.
#%% celda 12 [texto]
## 1.7 Bayesian Optimization
Los 3 hiperparámetros optimizados (`num_iterations`, `num_leaves`, `min_sum_hessian_in_leaf`) salen del **trial 27** de la optimización bayesiana del notebook
`competencia_01.ipynb` (Optuna/TPE con `n_startup_trials=8` y semilla 285937, 30 trials, métrica AUC en LightGBM, sin undersampling,
entrenando en 202103-202105 y validando en 202106). Sus resultados completos están guardados en `bo_resultados.csv`
(30 trials; el mejor es el trial 27, AUC 0,90468: 1.050 iteraciones, 171 hojas, `min_sum_hessian_in_leaf` 7,287).
Los hiperparámetros fijos son: `max_bin=31`, `min_data_in_leaf=0`, `feature_fraction=0,50`, `feature_fraction_bynode=0,20`, `learning_rate=0,005`.
Correr la optimización desde cero lleva unas 5 horas, por eso aquí se leen los resultados guardados.

#%% celda 13 [código]
bo = pd.read_csv("bo_resultados.csv") if Path("bo_resultados.csv").exists() else pd.read_csv(Path("..") / "exp" / "bo_resultados.csv")
bo = bo.sort_values("value", ascending=False)
mejor = bo.iloc[0]
assert int(mejor["params_num_leaves"]) == PARAMS["num_leaves"] and int(mejor["params_num_iterations"]) == NUM_ITERATIONS
assert abs(float(mejor["params_min_sum_hessian_in_leaf"]) - PARAMS["min_sum_hessian_in_leaf"]) < 1e-9
print("trial", int(mejor["number"]), "| AUC", round(mejor["value"], 5), "| hiperparametros coinciden con los usados abajo")
bo[["number", "value", "params_num_leaves", "params_min_sum_hessian_in_leaf", "params_num_iterations"]].head(8)

# [Anotación · líneas 181–212] Arma la matriz de entrenamiento con las filas de 202103 a 202106 y la clase
#   y_pos, y la matriz de 202108 con sus numero_de_cliente (verifica que no se repitan). Recorre las 20
#   semillas: en la primera y en la undécima crea un lgb.Dataset nuevo; entrena 1.050 iteraciones con PARAMS y
#   la semilla como seed, predice 202108, guarda las probabilidades en salida/pred_202108_seed{semilla}.npy e
#   imprime el tiempo de cada modelo.
#%% celda 14 [texto]
## 2.1 Final training
Se entrenan 20 modelos con **hiperparámetros idénticos**, cambiando solo la `seed` de LightGBM, en 202103-202106 y sin ningún tipo de undersampling.
Se aplican a los datos de 202108 (sección 2.2).

**Nota de reproducibilidad.** LightGBM discretiza las variables en *bins* la primera vez que se usa un `Dataset`, y esa construcción depende de la semilla
del primer entrenamiento que lo usa. Las 20 semillas se entrenaron en **dos tandas de 10** (semillas 1 a 10 y 11 a 20), cada una con su propio `Dataset`
construido en el primer uso. Para reproducir exactamente el archivo entregado se replica esa estructura: se crea un `Dataset` nuevo al empezar cada tanda.

#%% celda 15 [código]
fin = ds[ds.foto_mes.isin(MESES_FINAL)]
X_fin = fin[FEATURES].to_numpy(np.float32)
y_fin = fin["y_pos"].to_numpy()

def crear_dataset():
    return lgb.Dataset(X_fin, y_fin, params=DS_PARAMS)
apl = ds[ds.foto_mes == MES_APLICAR]
X_apl = apl[FEATURES].to_numpy(np.float32)
ids_apl = apl["numero_de_cliente"].to_numpy().round().astype("int64")
assert len(set(ids_apl)) == len(ids_apl)
print("entrenamiento:", fin.shape[0], "filas | agosto:", apl.shape[0], "clientes")

preds = {}
for i, sem in enumerate(SEMILLAS):
    t0 = time.time()
    if i in (0, 10):          # un Dataset nuevo al empezar cada tanda de 10 semillas (ver la nota de arriba)
        dfinal = crear_dataset()
    modelo = lgb.train(dict(PARAMS, seed=sem), dfinal, num_boost_round=NUM_ITERATIONS)
    preds[sem] = modelo.predict(X_apl).astype("float32")
    np.save(OUT_DIR / f"pred_202108_seed{sem}.npy", preds[sem])
    print(f"modelo {i + 1}/{len(SEMILLAS)}  semilla {sem}  {time.time() - t0:.0f}s", flush=True)

# [Anotación · líneas 213–227] Promedia las probabilidades de las 20 semillas, ordena los clientes de mayor a
#   menor promedio y guarda numero_de_cliente y prob en salida/scores_202108.csv.
#%% celda 16 [texto]
## 2.2 Scoring y ensamble
Cada semilla da un ranking de los clientes de 202108. El ensamble promedia las probabilidades por `numero_de_cliente`.

#%% celda 17 [código]
# promedio de las probabilidades de las 20 semillas, por numero_de_cliente (mismo orden de clientes en todas las semillas)
prob = np.mean(np.vstack([preds[s] for s in SEMILLAS]), axis=0)
orden = np.argsort(-prob)
ids_ordenados = ids_apl[orden]                        # clientes de mayor a menor probabilidad
scores = pd.DataFrame({"numero_de_cliente": ids_ordenados, "prob": prob[orden]})
assert scores.numero_de_cliente.is_unique
scores.to_csv(OUT_DIR / "scores_202108.csv", index=False)
print(scores.shape)
scores.head()

# [Anotación · líneas 228–249] guardar_ids escribe un CSV sin encabezado, de una columna de enteros y con fin
#   de línea \r\n, y exige entre 8.000 y 15.000 ids sin repetir. Genera salida/entregas/ensamble_K{k}.csv con
#   los primeros k clientes para cada k de KS y para K_ENTREGA (12.500 a 14.500 de a 250, 9 archivos) y guarda
#   en salida/config.json las semillas, los cortes, los hiperparámetros, las variables eliminadas y los meses.
#%% celda 18 [texto]
## 2.3 Classification y archivos para el bot
Formato exigido por `@competencia-uno`: `.csv` **sin encabezado**, una sola columna con los `numero_de_cliente` a estimular (enteros), entre 8.000 y 15.000 registros por archivo.
Se generan varios cortes K para compararlos contra el pseudo Kaggle; el entregado es **K = 13.000**.

#%% celda 19 [código]
def guardar_ids(ids, ruta):
    ids = np.asarray(ids).astype("int64")
    assert 8000 <= len(ids) <= 15000 and len(set(ids)) == len(ids)
    pd.DataFrame({"id": ids}).to_csv(ruta, header=False, index=False, lineterminator="\r\n")   # mismos bytes en cualquier sistema operativo

ENT = OUT_DIR / "entregas"
ENT.mkdir(exist_ok=True)
for k in sorted(set(KS + [K_ENTREGA])):
    guardar_ids(ids_ordenados[:k], ENT / f"ensamble_K{k}.csv")

json.dump(dict(semillas=SEMILLAS, ks=KS, k_entrega=K_ENTREGA, params=PARAMS, num_iterations=NUM_ITERATIONS,
               variables_eliminadas=VARIABLES_ELIMINADAS, meses_final=MESES_FINAL, mes_aplicar=MES_APLICAR),
          open(OUT_DIR / "config.json", "w"), indent=2, default=str)
print("archivos en", ENT.resolve())
print("archivo entregado:", ENT / f"ensamble_K{K_ENTREGA}.csv", "|", K_ENTREGA, "clientes")

# [Anotación · líneas 250–263] Si existe ensamble_K13000_ENTREGADO.csv en la carpeta de trabajo, lo compara
#   con salida/entregas/ensamble_K13000.csv e imprime tres resultados: si contienen los mismos clientes como
#   conjunto, si coinciden fila por fila y si los bytes de ambos archivos son iguales. Si no existe, imprime un
#   aviso.
#%% celda 20 [texto]
## Verificación
Compara el archivo generado aquí con el archivo exacto que se subió como entrega final (`ensamble_K13000_ENTREGADO.csv`, ganancia pública 105,0225).

#%% celda 21 [código]
ENTREGADO = Path("ensamble_K13000_ENTREGADO.csv")
if ENTREGADO.exists():
    a = pd.read_csv(ENT / f"ensamble_K{K_ENTREGA}.csv", header=None)[0].to_numpy()
    b = pd.read_csv(ENTREGADO, header=None)[0].to_numpy()
    print("mismos clientes (como conjunto):", set(a) == set(b))
    print("mismo orden fila por fila      :", bool((a == b).all()))
    print("archivos identicos byte a byte :", (ENT / f"ensamble_K{K_ENTREGA}.csv").read_bytes() == ENTREGADO.read_bytes())
else:
    print("no se encontro ensamble_K13000_ENTREGADO.csv en esta carpeta; nada que comparar")
```


## Explicaciones del alumno (texto original)

### README.md

> # DMEyF 2026 - Primera Competencia (María Mercedes Fiora)
>
> Todo lo necesario para replicar la entrega final está en la carpeta [`entrega_final/`](entrega_final/).
>
> - Entrega final (último submit, un solo archivo): [`entrega_final/ensamble_K13000_ENTREGADO.csv`](entrega_final/ensamble_K13000_ENTREGADO.csv) - ganancia pública 105,0225.
> - Notebook que la reproduce desde el CSV crudo: [`entrega_final/competencia_FINAL.ipynb`](entrega_final/competencia_FINAL.ipynb).
> - Instrucciones, descripción del modelo y entorno: [`entrega_final/README.md`](entrega_final/README.md).

### entrega_final/README.md

> # DMEyF 2026 - Primera Competencia: entrega final
>
> **Alumna:** María Mercedes Fiora (`MariaMercedesFiora` en el bot)
>
> **Entrega final (último submit, un solo archivo):** `ensamble_K13000_ENTREGADO.csv`
> - 13.000 `numero_de_cliente` de 202108, sin encabezado, una columna.
> - Ganancia pública: **105,0225** (Submission ID `1620-1791758548105986`).
> - MD5 del archivo: `038d426738376e6ac447e43e8dcbf9a6`
>
> Este es **el único archivo exacto** que se subió como entrega final. El notebook `competencia_FINAL.ipynb` lo reproduce a partir del CSV crudo
> y, al final, lo compara con ese archivo.
>
> ## Qué hay en esta carpeta
>
> | Archivo | Para qué sirve |
> |---|---|
> | `competencia_FINAL.ipynb` | **Notebook que reproduce la predicción final** de principio a fin |
> | `competencia_FINAL_ejecutado.ipynb` | El mismo notebook **ya ejecutado** (salidas incluidas), con la verificación contra el archivo entregado |
> | `ensamble_K13000_ENTREGADO.csv` | El archivo exacto subido como entrega final (el notebook lo usa para verificar) |
> | `bo_resultados.csv` | Los 30 trials de la Bayesian Optimization (el trial 27 da los hiperparámetros del modelo final) |
> | `bayesiana_competencia_01_ejecutado.ipynb` | Notebook con el **código y la salida de la Bayesian Optimization** (Optuna/TPE, 30 trials, AUC) |
> | `requirements.txt` | Versiones exactas de las librerías |
> | `datos/LEEME.txt` | Cómo obtener `competencia_01_crudo.csv` (no se sube a git por su tamaño) |
>
> ## Cómo reproducir la predicción final
>
> 1. Crear el entorno e instalar las librerías (se usó Python 3.12.10):
>    ```
>    python -m venv .venv
>    .venv\Scripts\pip install -r requirements.txt      # en Linux/Mac: .venv/bin/pip install -r requirements.txt
>    ```
> 2. Poner `competencia_01_crudo.csv` en la carpeta `datos/` (ver `datos/LEEME.txt`).
> 3. Ejecutar el notebook de arriba hacia abajo (el directorio de trabajo debe ser esta carpeta):
>    ```
>    .venv\Scripts\python -m jupyter nbconvert --to notebook --execute competencia_FINAL.ipynb --output competencia_FINAL_ejecutado.ipynb --ExecutePreprocessor.timeout=-1
>    ```
>    Tarda unas 2 horas y media en una CPU de 8 núcleos (preparación de datos y 20 modelos de ~8 minutos cada uno).
> 4. El resultado queda en `salida/entregas/ensamble_K13000.csv`. La última celda del notebook lo compara con `ensamble_K13000_ENTREGADO.csv`
>    e imprime si los clientes, su orden y los bytes del archivo son idénticos.
>
> ## Qué hace el modelo
>
> Predice **BAJA+2** del Paquete Premium en 202108 con LightGBM. Sigue la hoja de ruta de la cátedra:
>
> 1. **Clase:** `clase_ternaria` calculada mirando el futuro. El modelo se entrena con la clase binaria POS = {BAJA+1, BAJA+2} contra CONTINUA, sin undersampling.
>    La ganancia (+1.072.500 por acierto, -27.500 por envío inútil) cuenta solo los BAJA+2.
> 2. **Data Quality (1.1):** `ccajas_depositos` está rota en 202105 (todos ceros) -> `NA` solo para ese mes.
> 3. **Data Drifting (1.2):** se eliminan 12 variables (`cprestamos_personales`, `mprestamos_personales` y las 10 con mayor KS entre 202103-05 y 202108)
>    y se aplica **ranking mensual a las 41 variables monetarias `m*`** que quedan: de -1 a 1 con el cero fijo si tienen valores negativos, de 0 a 1 si no.
> 4. **Feature Engineering histórico (1.4):** lags y delta-lags de orden 1 y 2, calculados **después** del ranking, sobre los rangos. 700 features.
>    No se usan `numero_de_cliente` ni `foto_mes` como features.
> 5. **Bayesian Optimization (1.7):** Optuna/TPE, 30 trials, métrica AUC de LightGBM, sin undersampling. Cada trial entrena con 202103-05 y valida con 202106.
>    Hiperparámetros fijos: `max_bin=31`, `min_data_in_leaf=0`, `feature_fraction=0,50`, `feature_fraction_bynode=0,20`, `learning_rate=0,005`.
>    Hiperparámetros optimizados (trial 27, AUC 0,90468): `num_iterations=1050`, `num_leaves=171`, `min_sum_hessian_in_leaf=7,2872`.
>    El código y la salida de esta optimización están en `bayesiana_competencia_01_ejecutado.ipynb`; `competencia_FINAL.ipynb` lee sus resultados guardados (`bo_resultados.csv`)
>    porque correrla de cero lleva unas 5 horas.
> 6. **Final Training (2.1):** 20 modelos con hiperparámetros idénticos y distinta `seed` de LightGBM, entrenados en 202103, 202104, 202105 y 202106.
> 7. **Scoring (2.2):** se aplican a 202108 y se promedian las probabilidades por `numero_de_cliente`.
> 8. **Classification (2.3):** se prueban cortes de 12.500 a 14.500 envíos contra el pseudo Kaggle. El entregado es **K = 13.000**.
>
> ## Reproducibilidad
>
> - LightGBM en CPU con semillas fijas. Se verificó en la máquina de la autora que reentrenar una semilla da una predicción **idéntica bit a bit** a la guardada.
> - En otra máquina (distinto sistema operativo, versión de librerías o cantidad de hilos) los modelos podrían diferir en los últimos decimales,
>   lo que en casos extremos cambiaría el orden de clientes con probabilidades casi idénticas en el borde del corte.
> - Entorno de la corrida: Windows 10, Python 3.12.10, `lightgbm==4.7.0`, `numpy==2.5.3`, `pandas==3.0.6`.
>
> ## Resultados de la verificación
>
> El notebook se ejecutó **de principio a fin desde el CSV crudo** (`competencia_FINAL_ejecutado.ipynb` es esa ejecución, con todas sus salidas):
>
> - Inicio 11-oct-2026 22:42, fin 12-oct-2026 01:06 (2 h 24 min), Windows 10, CPU de 8 núcleos, Python 3.12.10, `lightgbm==4.7.0`.
> - **0 celdas con error.**
> - El archivo generado (`salida/entregas/ensamble_K13000.csv`) resultó **idéntico byte a byte** al archivo entregado
>   (`ensamble_K13000_ENTREGADO.csv`): mismos 13.000 clientes, mismo orden, **MD5 `038d426738376e6ac447e43e8dcbf9a6`** en ambos.
>   Las últimas celdas del notebook ejecutado muestran esa comparación.
>
> Nota sobre las semillas: las 20 semillas se entrenan en dos tandas de 10, cada una con su propio `Dataset` de LightGBM (el discretizado de las variables
> depende de la primera semilla que usa el `Dataset`). El notebook replica esa estructura para reproducir exactamente el archivo entregado.

### entrega_final/datos/LEEME.txt

> Poner aqui el archivo de datos (no se sube a git por su tamano):
>
>     competencia_01_crudo.csv
>
> Descarga (la misma que usa la catedra):
>     https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv
>
> Ejemplo:
>     curl -L -o datos/competencia_01_crudo.csv https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv

