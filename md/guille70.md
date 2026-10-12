# Guillermo Toyos — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: Guille70
- Repositorio: https://github.com/Guille70/dmeyf2026
- Link posteado: https://github.com/Guille70/dmeyf2026/tree/main/gtoyos/DMEyF_Competencia01_Entrega
- Commit: 51a1e75d9fb5a7979d38c7a2b14b49be45d2d496
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/guille70/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/guille70.json

## Resumen

El link posteado apunta a la carpeta gtoyos/DMEyF_Competencia01_Entrega de un repositorio que es un fork. La carpeta trae un README, un notebook de Python, un archivo con 100 semillas, una lista de 602 nombres de columnas, una base SQLite de Optuna y el CSV enviado. El notebook lee con DuckDB los meses 202104, 202106 y 202108 de un parquet con las variables ya calculadas (no incluido; el README da un enlace de descarga), tomando las columnas de la lista: según el README, 155 originales, 16 intra mes, 140 pr_, 140 nt10_ y 151 delta_1_. Define la optimización de hiperparámetros de LightGBM con Optuna (50 trials, validación cruzada sobre 202104 con clase BAJA+2 y métrica AUC) y la lee ya completa del .db. Con los hiperparámetros y la cantidad de rondas del trial 25 entrena sobre 202106, con clase binaria BAJA+1 o BAJA+2, un modelo por cada una de 20 semillas; promedia las probabilidades sobre 202108 y escribe los 12.000 clientes de mayor promedio. La última celda compara ese archivo con el enviado. El README describe además cómo se eligieron el trial 25 y el corte; el código de esa elección no está en la entrega.

**Qué entrega.** Un CSV sin encabezado con 12.000 numero_de_cliente de 202108, uno por línea, ordenados de mayor a menor probabilidad promedio: data/out/Sbm04ajaFE04bOptN12000_sem_final.csv (según el README, el archivo que se subió a Zulip). El notebook genera el mismo listado en data/out/submit04ajaFE04bOptN12000Sem/Sbm04ajaFE04bOptN12000_sem.csv.

**Cómo se ejecuta.** Según el README: (1) descargar competencia_01_fe03.parquet (1,86 GB) desde un enlace de Google Drive y dejarlo en data/; (2) abrir scripts/DMEyF_Competencia01_EntregaFinal.ipynb con scripts/ como carpeta de trabajo y ejecutar todas las celdas (20 a 25 minutos, 20 modelos). El notebook lee del .db incluido la optimización ya completa y no corre trials nuevos.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** Modelo final: binaria, clase_binaria_b12 = 1 si clase_ternaria es BAJA+1 o BAJA+2 y 0 en el resto de las filas. La optimización de hiperparámetros se define con otra clase binaria, clase_binaria_b2 = 1 si clase_ternaria es BAJA+2 y 0 en el resto (BAJA+1 queda en 0).
- **Meses de entrenamiento:** 202106
- **Meses de validación:** 202104, 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código
- **Calidad de datos:** La función cargar asigna NaN a ccajas_depositos en las filas de foto_mes 202105; la lista de meses que carga el notebook es [202104, 202106, 202108], que no incluye 202105. Según el README, ccajas_depositos tiene todos sus valores en cero en 202105 y se dejan fuera de la lista de columnas 10 variables derivadas de ella; en fe04_b_con_delta1.txt el único nombre que contiene ccajas_depositos es la variable original.
- **Drifting:** El modelo usa 140 columnas pr_ (percent_rank) y 140 nt10_ (ntile 10), que el README describe como variables intra mes de ranking; se leen ya calculadas del parquet y el código que las calcula no está en la entrega. En fe04_b_con_delta1.txt las pr_ y las nt10_ corresponden a las mismas 140 columnas base, que también figuran en la lista sin prefijo. No se observa deflación ni estandarización.
- **Variables dentro del mes:** No se calculan en el notebook: se leen del parquet competencia_01_fe03.parquet (no incluido). Según el README, la lista tiene 16 variables intra mes creadas a mano, 140 pr_ y 140 nt10_. En fe04_b_con_delta1.txt los últimos 16 nombres sin prefijo son total_saldo_tarjetas, total_consumo_tarjetas, total_pagado_tarjetas, visa_ratio_pagado_consumo, master_ratio_pagado_consumo, ratio_comisiones_saldo, antiguedad_sobre_edad, canales_digitales_activos, total_seguros, total_inversiones, total_trx_canales, pct_trx_cajas, pct_trx_atm_propio, pct_trx_homebanking, pct_trx_mobile y pct_trx_callcenter; ninguno de los 16 tiene versión pr_, nt10_ ni delta_1_ en la lista.
- **Variables históricas:** 151 columnas delta_1_ (históricas de orden 1 según el README), leídas ya calculadas del parquet. En fe04_b_con_delta1.txt hay un delta_1_ por cada una de las 155 columnas originales salvo numero_de_cliente, foto_mes, clase_ternaria y ccajas_depositos. El README indica que el parquet tiene además delta_2_, delta_3_, avg_3_, stddev_3_, min_3_, max_3_ y ratio_avg3_, que quedan fuera de la lista de columnas del modelo.
- **Selección de variables:** Lista fija de 602 nombres en data/fe04_b_con_delta1.txt (de las 1.614 columnas del parquet, según el README). Al modelo entran 599: se quitan clase_ternaria, numero_de_cliente, foto_mes y las dos clases binarias creadas en el notebook. No se observa selección por importancia.
- **Optimización de hiperparámetros:** Optuna, estudio cpt2_step1_b2_lgbm_sss_3000_con_FE04-b guardado en SQLite (data/databases/cpt2_optim_lgbm_Step1.db), dirección maximizar, objetivo de 50 trials. Cada trial corre lgb.cv sobre 202104 con clase BAJA+2 y métrica AUC, con StratifiedShuffleSplit de 5 particiones y 30% de prueba, hasta 3.000 rondas y early stopping de min(50 + 5/learning_rate, 1.000) rondas; guarda como best_iter la ronda de mayor AUC medio. Rangos: num_leaves 8 a 256; min_sum_hessian_in_leaf 0,001 a 100 (log); learning_rate 0,005 a 0,2 (log); feature_fraction 0,3 a 0,7; feature_fraction_bynode 0,1 a 0,5; bagging_fraction 0,6 a 1,0; bagging_freq 1 a 10. El notebook corre sólo los trials que falten para llegar a 50; con el .db incluido no corre ninguno (salida guardada: 'Tengo 50, corro 0 más').
- **Hiperparámetros finales:** Los del trial 25 del estudio, leídos del .db. Según la salida guardada en el notebook: num_leaves 220, min_sum_hessian_in_leaf 18,11, learning_rate 0,006015, feature_fraction 0,5816, feature_fraction_bynode 0,2332, bagging_fraction 0,7917, bagging_freq 6 y 1.052 rondas (best_iter). Escritos en el código: objective binary, boosting_type gbdt, max_bin 31, min_data_in_leaf 0, boost_from_average True, feature_pre_filter False, first_metric_only True, num_threads 10, verbose -1.
- **Semillas:** Lista SEMILLAS de 100 enteros en scripts/semillas.py (según su comentario, generados en random.org el 2026-09-01). Los 20 modelos finales usan semillas[20:40]; un comentario del notebook indica que semillas[:20] son las usadas en la validación. La optimización usa semillas[0] en el StratifiedShuffleSplit, en el parámetro seed de LightGBM y en lgb.cv; optuna.create_study se llama sin sampler ni semilla, y el README indica que la optimización no se reproduce exactamente.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio aritmético, cliente por cliente, de las probabilidades de 20 modelos LightGBM con la misma configuración (trial 25) y distinta semilla.
- **Corte:** Cantidad fija: los 12.000 clientes de 202108 con mayor probabilidad promedio (N_final = 12000). Según el README, el barrido de cortes se definió a partir del corte obtenido en junio, pasado a porcentaje de clientes y trasladado a agosto, y el valor 12.000 se eligió con el puntaje público del bot probando N entre 9.000 y 16.037.
- **Validación:** En el notebook: validación cruzada dentro de 202104 (lgb.cv con StratifiedShuffleSplit, 5 particiones, 30% de prueba, AUC) como objetivo de la optimización. Según el README, los 5 trials de mayor AUC se midieron con 20 semillas cada uno, entrenando con 202104 y calculando en 202106 la ganancia con BAJA+2 real (+1.072.500 por acierto, −27.500 en caso contrario). El notebook define mes_train = 202104, mes_test = 202106, ganancia_acierto y costo_estimulo y arma los conjuntos de junio, pero no contiene el código de esa medición. El modelo final se entrena con 202106 y no usa filas de 202104. La última celda compara el archivo generado con el archivo enviado.
- **Salidas:** data/out/submit04ajaFE04bOptN12000Sem/Sbm04ajaFE04bOptN12000_sem.csv (12.000 numero_de_cliente, uno por línea, sin encabezado); 20 modelos en texto en modelos/cpt04_modelos_TrainJun_FE04b_opt/; modelos/cpt04_TrainJun-FE04b_PredAgo_probb12_t25.pkl con las probabilidades por semilla y modelos/cpt04_TrainJun-FE04b_PredAgo_ids_pred.npy con los IDs. El repositorio incluye el archivo enviado, data/out/Sbm04ajaFE04bOptN12000_sem_final.csv, y no incluye la carpeta modelos/.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optuna (`hiperparametros.optuna`)
- Validación cruzada (`validacion.validacion_cruzada`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)

## Técnicas sólo exploradas

- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Mínimos y máximos de ventana (`variables.min_max_ventana`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Genera archivos con varios cortes (`corte.varios_cortes`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README: Python 3.11.16; lightgbm 4.7.0, optuna 5.0.0, duckdb 1.0.0, pandas 2.3.3, numpy 2.4.6, scikit-learn 1.9.1, plotly 7.0.0, matplotlib 3.11.1; lgb_threads = 10, con la aclaración de que LightGBM no garantiza resultados idénticos con otra cantidad de threads. Un comentario del notebook indica una máquina de 16 cores y 63,8 GB de RAM.

## Pasos del camino de la entrega

1. **Configuración, librerías y rutas.** Define la cantidad de threads (10 para LightGBM), importa las librerías, ubica la carpeta raíz de la entrega según el nombre de la carpeta de trabajo e importa la lista SEMILLAS de scripts/semillas.py. Arma las rutas data/, modelos/ y data/databases/ y el nombre del parquet. (`gtoyos/DMEyF_Competencia01_Entrega/scripts/DMEyF_Competencia01_EntregaFinal.ipynb` líneas 9–65; `gtoyos/DMEyF_Competencia01_Entrega/scripts/semillas.py` líneas 1–5)
2. **Lectura del dataset.** La función cargar lee de un archivo de texto los nombres de columnas y consulta el parquet competencia_01_fe03.parquet con DuckDB filtrando por foto_mes. Se cargan 202104, 202106 y 202108 con las 602 columnas de fe04_b_con_delta1.txt y se ordenan las filas por foto_mes y numero_de_cliente. La función asigna NaN a ccajas_depositos en las filas de 202105, mes que no está entre los cargados. (`gtoyos/DMEyF_Competencia01_Entrega/scripts/DMEyF_Competencia01_EntregaFinal.ipynb` líneas 71–111; `gtoyos/DMEyF_Competencia01_Entrega/README.md` líneas 28–52)
3. **Clase BAJA+2 y conjuntos de abril y junio.** Define la ganancia por acierto (1.072.500), el costo del estímulo (27.500), el mes de entrenamiento de la optimización (202104) y el de prueba (202106). Crea la clase binaria con positivo = BAJA+2 y arma las matrices y los lgb.Dataset de abril y de junio sin las columnas de clase, cliente y mes. (`gtoyos/DMEyF_Competencia01_Entrega/scripts/DMEyF_Competencia01_EntregaFinal.ipynb` líneas 117–146)
4. **Definición de la optimización de hiperparámetros.** Define la función objetivo de Optuna: propone 7 hiperparámetros de LightGBM, corre lgb.cv sobre abril con StratifiedShuffleSplit (5 particiones, 30% de prueba), hasta 3.000 rondas con early stopping, devuelve el AUC medio máximo y guarda en el trial la ronda en que se alcanza (best_iter). (`gtoyos/DMEyF_Competencia01_Entrega/scripts/DMEyF_Competencia01_EntregaFinal.ipynb` líneas 152–203)
5. **Lectura del estudio de Optuna.** Abre el estudio cpt2_step1_b2_lgbm_sss_3000_con_FE04-b del archivo SQLite data/databases/cpt2_optim_lgbm_Step1.db y corre sólo los trials que falten para llegar a 50. Según el README y la salida guardada del notebook, el .db ya tiene los 50 y no se corre ninguno. (`gtoyos/DMEyF_Competencia01_Entrega/scripts/DMEyF_Competencia01_EntregaFinal.ipynb` líneas 205–225; `gtoyos/DMEyF_Competencia01_Entrega/README.md` líneas 68–73)
6. **Clase fusionada y configuración del trial 25.** Crea la clase binaria con positivo = BAJA+1 o BAJA+2. Toma del estudio el trial número 25, su best_iter y sus 7 hiperparámetros, y arma el diccionario de parámetros con max_bin 31 y min_data_in_leaf 0. El README indica que el trial 25 se eligió entre los 5 de mayor AUC tras medirlos en junio con la ganancia. (`gtoyos/DMEyF_Competencia01_Entrega/scripts/DMEyF_Competencia01_EntregaFinal.ipynb` líneas 231–255; `gtoyos/DMEyF_Competencia01_Entrega/README.md` líneas 75–78)
7. **Datos de entrenamiento (junio) y de predicción (agosto).** Separa las filas de 202106 y de 202108, guarda los numero_de_cliente de agosto en el orden de las filas, quita las columnas de clase, cliente y mes y arma el lgb.Dataset de junio con la clase fusionada. (`gtoyos/DMEyF_Competencia01_Entrega/scripts/DMEyF_Competencia01_EntregaFinal.ipynb` líneas 261–280)
8. **Entrenamiento de 20 semillas y predicción.** Para cada semilla de semillas[20:40] entrena un LightGBM sobre junio con los parámetros del trial 25 y best_iter rondas, guarda el modelo y predice agosto. Guarda las 20 series de probabilidades en un .pkl y los IDs en un .npy. (`gtoyos/DMEyF_Competencia01_Entrega/scripts/DMEyF_Competencia01_EntregaFinal.ipynb` líneas 286–309)
9. **Promedio, corte y escritura del archivo.** Promedia las 20 probabilidades por cliente, ordena de mayor a menor, toma los primeros 12.000 y escribe sus numero_de_cliente, uno por línea y sin encabezado. Relee el archivo y verifica la cantidad de líneas, la ausencia de notación científica y que no haya IDs repetidos. El README describe cómo se llegó a N = 12.000. (`gtoyos/DMEyF_Competencia01_Entrega/scripts/DMEyF_Competencia01_EntregaFinal.ipynb` líneas 315–350; `gtoyos/DMEyF_Competencia01_Entrega/README.md` líneas 79–79)
10. **Comparación con el archivo enviado.** Lee data/out/Sbm04ajaFE04bOptN12000_sem_final.csv e imprime la cantidad de IDs de cada archivo, cuántos tienen en común y si el contenido es idéntico. Según el README y la salida guardada: 12.000 IDs en común y archivos idénticos. (`gtoyos/DMEyF_Competencia01_Entrega/scripts/DMEyF_Competencia01_EntregaFinal.ipynb` líneas 356–363; `gtoyos/DMEyF_Competencia01_Entrega/README.md` líneas 64–66)

## Archivos

- `gtoyos/DMEyF_Competencia01_Entrega/README.md` · explicacion · Markdown · 86 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/guille70/gtoyos/DMEyF_Competencia01_Entrega/README.md.txt) — Presenta la entrega: qué archivo se subió, la estructura de carpetas, los tres pasos para replicarla (descargar el parquet, lista de columnas, ejecutar el notebook), cómo se hizo la optimización de hiperparámetros, cómo se llegó al trial 25 y al corte N = 12.000, y una sección de reproducibilidad con la versión de Python y de las librerías.
- `gtoyos/DMEyF_Competencia01_Entrega/scripts/semillas.py` · configuracion · Python · 5 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/guille70/gtoyos/DMEyF_Competencia01_Entrega/scripts/semillas.py.txt) — Define la lista SEMILLAS con 100 enteros; el comentario inicial indica que se generaron en random.org el 2026-09-01. El notebook usa semillas[0] en la optimización y semillas[20:40] en los 20 modelos finales. En la copia mostrada la línea de la lista aparece recortada.
- `gtoyos/DMEyF_Competencia01_Entrega/scripts/DMEyF_Competencia01_EntregaFinal.ipynb` · principal · Jupyter (python) · 363 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/guille70/gtoyos/DMEyF_Competencia01_Entrega/scripts/DMEyF_Competencia01_EntregaFinal.ipynb.txt) — Notebook de Python con 26 celdas (14 de código y 12 de texto). Carga 202104, 202106 y 202108, define y lee la optimización de Optuna, entrena 20 LightGBM sobre junio con la configuración del trial 25 y la clase BAJA+1 o BAJA+2, promedia las probabilidades de agosto, escribe los 12.000 clientes de mayor promedio y compara el resultado con el archivo enviado.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### gtoyos/DMEyF_Competencia01_Entrega/scripts/DMEyF_Competencia01_EntregaFinal.ipynb

Notebook de Python con 26 celdas (14 de código y 12 de texto). Carga 202104, 202106 y 202108, define y lee la optimización de Optuna, entrena 20 LightGBM sobre junio con la configuración del trial 25 y la clase BAJA+1 o BAJA+2, promedia las probabilidades de agosto, escribe los 12.000 clientes de mayor promedio y compara el resultado con el archivo enviado.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–16] Título del notebook (junio con clase fusionada BAJA+1 + BAJA+2 para predecir
#   agosto, FE04b, trial 25, 20 semillas, N = 12.000). Define los recursos de la corrida: 12 threads y 45GB para
#   DuckDB, rf_n_jobs = 10 y lgb_threads = 10, y los imprime. De estos cuatro valores, el resto del notebook
#   sólo usa lgb_threads.
#%% celda 1 [texto]
### Competencia 1 - Entrega Final
Junio (target fusionado BAJA+1+BAJA+2) para predecir Agosto. FE04b, trial 25, 20 semillas y corte en N = 12.000

#%% celda 2 [texto]
##### Librerías y Path Variables

#%% celda 3 [código]
# Configuración de recursos (parámetros de la máquina: 16 cores, 63.8GB RAM)      

duckdb_threads = 12
duckdb_memory_limit = '45GB'
rf_n_jobs = 10
lgb_threads = 10          # CAMBIO: se dejan los 10 threads con los que se corrió el submit final

print(f"DuckDB: {duckdb_threads} threads, {duckdb_memory_limit} | RF: n_jobs={rf_n_jobs} | LGB: {lgb_threads} threads")

# [Anotación · líneas 18–40] Antepone al PATH la carpeta Library/bin del entorno de Python e importa duckdb,
#   pandas, numpy, pickle, matplotlib, plotly, StratifiedShuffleSplit de scikit-learn, lightgbm y optuna con
#   cuatro funciones de visualización. Matplotlib, plotly y las funciones de visualización no se llaman en las
#   celdas siguientes.
#%% celda 4 [código]
# Librerías

import os, sys
os.environ['PATH'] = os.path.join(sys.prefix, 'Library', 'bin') + os.pathsep + os.environ['PATH']
import duckdb

import pandas as pd
import numpy as np
import pickle

import matplotlib.pyplot as plt

from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px

from sklearn.model_selection import StratifiedShuffleSplit

import lightgbm as lgb

import optuna
from optuna.visualization import plot_optimization_history, plot_param_importances, plot_slice, plot_contour

# [Anotación · líneas 42–65] Determina la carpeta raíz según el nombre de la carpeta de trabajo: si es
#   'scripts' o '02_prediccion_final' toma la carpeta superior; si es '03_competencia_01', la actual; en otro
#   caso, la subcarpeta '03_competencia_01'. Agrega RAIZ/scripts al sys.path e importa SEMILLAS de semillas.py
#   con el nombre semillas. Imprime la carpeta raíz y si existen ella y scripts/semillas.py. Define las rutas
#   data/, modelos/ y data/databases/ y el archivo competencia_01_fe03.parquet.
#%% celda 5 [código]
# Paths Variables

from pathlib import Path
cwd = Path.cwd()
if cwd.name == 'scripts':
    RAIZ = cwd.parent
elif cwd.name == '03_competencia_01':
    RAIZ = cwd
elif cwd.name == '02_prediccion_final':      # CAMBIO: la notebook final vive en esta carpeta del repo
    RAIZ = cwd.parent
else:
    RAIZ = cwd / '03_competencia_01'

sys.path.insert(0, str(RAIZ / 'scripts'))
from semillas import SEMILLAS as semillas

base_path = str(RAIZ) + '/'
print(RAIZ, RAIZ.exists(), (RAIZ / 'scripts' / 'semillas.py').exists())

dataset_path = base_path + 'data/'
modelos_path = base_path + 'modelos/'
db_path = base_path + 'data/databases/'
dataset_file = 'competencia_01_fe03.parquet'

# [Anotación · líneas 67–92] Abre una conexión DuckDB en memoria y define cargar(archivo_cols, meses): lee los
#   nombres de columnas de un archivo de texto (uno por línea), arma un SELECT sobre el parquet con esas
#   columnas y con foto_mes dentro de los meses pedidos, y devuelve un DataFrame de pandas. Con ROTA_CONFIRMADA
#   = True, si ccajas_depositos está entre las columnas le asigna NaN en las filas de foto_mes 202105.
#%% celda 6 [texto]
##### Carga de Datos

#%% celda 7 [código]
# Función para cargar los datos de la competencia, filtrando por meses y columnas

ruta_fe03 = dataset_path + dataset_file       # .../data/competencia_01_fe03.parquet
ROTA = 'ccajas_depositos'
ROTA_CONFIRMADA = True                        # resultado del chequeo de la otra notebook
con = duckdb.connect()

def cargar(archivo_cols, meses):
    cols = Path(archivo_cols).read_text().split('\n')          # nombres de columnas, desde el .txt
    select_cols = ', '.join(f'"{c}"' for c in cols)            # "col1", "col2", ... para el SELECT
    lista_meses = ', '.join(str(m) for m in meses)             # 202103, 202104, ... para el WHERE

    df = con.execute(f"""
        select {select_cols} from read_parquet('{ruta_fe03}')
        where foto_mes in ({lista_meses})
    """).fetchdf()

  # la variable rota: NaN solo en mayo
    if ROTA_CONFIRMADA and ROTA in df.columns:
        df.loc[df['foto_mes'] == 202105, ROTA] = np.nan

    return df

# [Anotación · líneas 94–111] Carga los meses 202104, 202106 y 202108 con las columnas de
#   fe04_b_con_delta1.txt (OPCION = 'b'; el diccionario prevé también la opción 'a', fe04_a_sin_historicas.txt,
#   archivo que no está en la entrega). Ordena las filas por foto_mes y numero_de_cliente e imprime las
#   dimensiones y la cantidad de filas por mes. Salida guardada en el .ipynb: 492.045 filas y 602 columnas;
#   163.284, 164.114 y 164.647 filas por mes.
#%% celda 8 [código]
# Cargar los datos de la competencia, filtrando por meses y columnas

MESES = [202104, 202106, 202108]          # CAMBIO: abril (optimización), junio (entrena) y agosto (predice)

OPCION = 'b'      # '' = sin históricas | 'b' = con delta_1

archivos = {
    'a': dataset_path  + 'fe04_a_sin_historicas.txt',
    'b': dataset_path  + 'fe04_b_con_delta1.txt',
}

data = cargar(archivos[OPCION], MESES)

data = data.sort_values(['foto_mes', 'numero_de_cliente'])      # CAMBIO: orden fijo de filas

print(data.shape)
print(data['foto_mes'].value_counts().sort_index())   # filas por mes

# [Anotación · líneas 113–123] Define ganancia_acierto = 1.072.500, costo_estimulo = 27.500, mes_train =
#   202104 y mes_test = 202106. Las dos primeras variables no vuelven a aparecer en el notebook.
#%% celda 9 [texto]
##### Ganancia/Costo y Meses de Train/Test

#%% celda 10 [código]
# Ganancia y Costo y Selección de Meses para Entrenamiento y Test

ganancia_acierto = 1_072_500
costo_estimulo = 27_500

mes_train = 202104    # Abril - mes de entrenamiento
mes_test = 202106     # Junio - mes de testeo

# [Anotación · líneas 125–146] Crea clase_binaria_b2 (1 si clase_ternaria es BAJA+2, 0 en otro caso). Separa
#   abril como entrenamiento y junio como prueba, quita de las matrices clase_ternaria, clase_binaria_b2,
#   numero_de_cliente y foto_mes, y construye un lgb.Dataset para cada mes. El de abril (train_data_lgb), junto
#   con X_train e y_train_binaria, es el que usa la función objetivo; X_test, y_test_binaria, y_test_class y
#   test_data_lgb no se usan en las celdas siguientes.
#%% celda 11 [texto]
##### Clase Binaria BAJA+2 + X/Y Train/Test (para la Optimización)

#%% celda 12 [código]
data['clase_binaria_b2'] = np.where(data['clase_ternaria'] == 'BAJA+2', 1, 0)    # optimizo y mido con esta


# Preparación de datos para la optimización
cols_descartar = ['clase_ternaria', 'clase_binaria_b2', 'numero_de_cliente', 'foto_mes']

train_data = data[data['foto_mes'] == mes_train]
test_data  = data[data['foto_mes'] == mes_test]

X_train = train_data.drop(columns=cols_descartar)
y_train_binaria = train_data['clase_binaria_b2']

X_test = test_data.drop(columns=cols_descartar)
y_test_binaria = test_data['clase_binaria_b2']        # ← era 'clase_binaria'
y_test_class = test_data['clase_ternaria']            # solo para medir; no entra en X

train_data_lgb = lgb.Dataset(X_train, label=y_train_binaria)
test_data_lgb  = lgb.Dataset(X_test, label=y_test_binaria, reference=train_data_lgb)

# [Anotación · líneas 148–164] Crea un StratifiedShuffleSplit de 5 particiones con 30% de prueba y
#   random_state = semillas[0]. Empieza la función objective(trial), que propone 7 hiperparámetros: num_leaves
#   (entero, 8 a 256), min_sum_hessian_in_leaf (0,001 a 100, escala log), learning_rate (0,005 a 0,2, escala
#   log), feature_fraction (0,3 a 0,7), feature_fraction_bynode (0,1 a 0,5), bagging_fraction (0,6 a 1,0) y
#   bagging_freq (entero, 1 a 10).
#%% celda 13 [texto]
##### Optimización de Hiperparámetros (Abril, Cross-Validation). Levanta el Study del .db

#%% celda 14 [código]
sss_opt = StratifiedShuffleSplit(n_splits=5, test_size=0.3, random_state=semillas[0])   # stratified shuffle split para la optimización bayesiana 
                                                                                        # con 5 splits y 30% de testeo

def objective(trial):

    # bayesianos
    num_leaves = trial.suggest_int('num_leaves', 8, 256)                                # numero de hojas del árbol
    min_sum_hessian_in_leaf = trial.suggest_float('min_sum_hessian_in_leaf', 1e-3, 100, log=True)
    learning_rate = trial.suggest_float('learning_rate', 0.005, 0.2, log=True)          # mas bajo, más iteraciones necesita
    feature_fraction = trial.suggest_float('feature_fraction', 0.3, 0.7)                # columnas por árbol
    feature_fraction_bynode = trial.suggest_float('feature_fraction_bynode', 0.1, 0.5)  # columnas por nodo (se multiplica con la anterior)
    bagging_fraction = trial.suggest_float('bagging_fraction', 0.6, 1.0)                # submuestreo de filas por árbol
    bagging_freq = trial.suggest_int('bagging_freq', 1, 10)                             # > 0 para que el bagging funcione

# [Anotación · líneas 166–186] Arma el diccionario de parámetros de LightGBM del trial: objective binary,
#   metric auc, boosting_type gbdt, boost_from_average True, feature_pre_filter False, max_bin 31,
#   min_data_in_leaf 0, los 7 valores propuestos, seed = semillas[0], num_threads = lgb_threads y verbose -1.
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'boosting_type': 'gbdt',
        'boost_from_average': True,
        'feature_pre_filter': False,        
      # fijos de la cátedra
        'max_bin': 31,                       # número de bins para discretizar las variables continuas
        'min_data_in_leaf': 0,               # el freno pasa a min_sum_hessian_in_leaf
      # bayesianos
        'num_leaves': num_leaves,
        'min_sum_hessian_in_leaf': min_sum_hessian_in_leaf,
        'learning_rate': learning_rate,
        'feature_fraction': feature_fraction,
        'feature_fraction_bynode': feature_fraction_bynode,
        'bagging_fraction': bagging_fraction,
        'bagging_freq': bagging_freq,
        'seed': semillas[0],
        'num_threads': lgb_threads,
        'verbose': -1
    }
# [Anotación · líneas 187–203] Corre lgb.cv sobre el Dataset de abril con las particiones del
#   StratifiedShuffleSplit, hasta 3.000 rondas, con early stopping de min(50 + 5/learning_rate, 1.000) rondas y
#   seed = semillas[0]. Toma el máximo del AUC medio de validación, guarda en el trial como best_iter la ronda
#   en que se alcanza y devuelve ese máximo.
    num_boost_round = 3000                   # subido de 3000 porque el learning_rate mínimo es más bajo
    cv_results = lgb.cv(
        params,
        train_data_lgb,
        num_boost_round=num_boost_round,
        callbacks=[lgb.early_stopping(stopping_rounds=min(int(50 + 5 / learning_rate), num_boost_round // 3), verbose=False)],  
        folds=sss_opt.split(X_train, y_train_binaria),                    # usamos StratifiedShuffleSplit en vez del k-fold interno
        seed=semillas[0]
    )

    max_auc = max(cv_results['valid auc-mean'])
    best_iter = cv_results['valid auc-mean'].index(max_auc) + 1     # es el num_iterations

    # Guardamos cual es la mejor iteración del modelo
    trial.set_user_attr("best_iter", best_iter)

    return max_auc

# [Anotación · líneas 205–225] Abre con load_if_exists=True el estudio de Optuna
#   cpt2_step1_b2_lgbm_sss_3000_con_FE04-b en el archivo SQLite data/databases/cpt2_optim_lgbm_Step1.db, con
#   dirección maximizar, e imprime cuántos trials tiene. Calcula cuántos faltan para llegar a 50 y llama a
#   study.optimize sólo por esa diferencia. Salida guardada en el .ipynb: 'Tengo 50, corro 0 más'.
storage_name = "sqlite:///" + db_path + "cpt2_optim_lgbm_Step1.db"
study_name = "cpt2_step1_b2_lgbm_sss_3000_con_FE04-b"                            # se hizo con FE04b es decir con deltas además de intrames

study = optuna.create_study(
    direction="maximize",
    study_name=study_name,
    storage=storage_name,
    load_if_exists=True,
)

print(len(study.trials))     # debe dar 0 si la base es nueva

#%% celda 15 [texto]
##### Completar la Optimización (si el .db ya tiene los 50 trials, no corre nada)

#%% celda 16 [código]
objetivo_total = 50                                        # número de trials que queremos correr en total
faltan = objetivo_total - len(study.trials)
print(f"Tengo {len(study.trials)}, corro {faltan} más")
if faltan > 0:
    study.optimize(objective, n_trials=faltan)

# [Anotación · líneas 227–255] Crea clase_binaria_b12 (1 si clase_ternaria es BAJA+1 o BAJA+2, 0 en otro caso)
#   y la lista de columnas que no entran al modelo: clase_ternaria, las dos clases binarias, numero_de_cliente y
#   foto_mes. Busca en el estudio el trial número 25, toma su best_iter y arma params con objective binary,
#   boosting_type gbdt, first_metric_only, boost_from_average, feature_pre_filter False, max_bin 31,
#   min_data_in_leaf 0, los 7 hiperparámetros del trial, seed = semillas[0] y num_threads = lgb_threads. Imprime
#   best_iter y los hiperparámetros. Salida guardada en el .ipynb: best_iter = 1052; num_leaves 220,
#   min_sum_hessian_in_leaf 18,11, learning_rate 0,00602, feature_fraction 0,582, feature_fraction_bynode 0,233,
#   bagging_fraction 0,792, bagging_freq 6.
#%% celda 17 [texto]
##### Configuración del Trial 25 (Target Fusionado: BAJA+1 y BAJA+2)

#%% celda 18 [código]
# Target fusionado: BAJA+1 y BAJA+2 juntos (1) contra CONTINUA (0)
data['clase_binaria_b12'] = np.where(data['clase_ternaria'].isin(['BAJA+1', 'BAJA+2']), 1, 0)

# Se descartan el target, el id y el mes, para que no entren a X
cols_a_descartar = ['clase_ternaria', 'clase_binaria_b2', 'clase_binaria_b12', 'numero_de_cliente', 'foto_mes']

# Receta del trial 25: sus hiperparámetros y el número de árboles (best_iter) que guardó la optimización
trial_25 = next(t for t in study.trials if t.number == 25)
best_iter = trial_25.user_attrs['best_iter']
params = {
    'objective': 'binary',
    'boosting_type': 'gbdt',
    'first_metric_only': True,
    'boost_from_average': True,
    'feature_pre_filter': False,
    'max_bin': 31,                                         # fijo de la cátedra
    'min_data_in_leaf': 0,                                 # fijo de la cátedra: el freno es min_sum_hessian_in_leaf
    **trial_25.params,                                     # los 7 hiperparámetros de la optimización
    'seed': semillas[0],
    'num_threads': lgb_threads,
    'verbose': -1
}

print('best_iter =', best_iter, '(en la corrida original dio 1052)')
print(trial_25.params)

# [Anotación · líneas 257–280] Separa las filas de 202106 (entrenamiento) y de 202108 (predicción). Guarda los
#   numero_de_cliente de agosto antes de quitar columnas, arma X_train_jun, y_train_jun (clase_binaria_b12) y
#   X_pred_ago, y construye el lgb.Dataset de junio. Imprime las dimensiones y la cantidad de filas por clase.
#   Salida guardada en el .ipynb: 164.114 filas de junio y 164.647 de agosto, 599 columnas; 162.142 ceros y
#   1.972 unos en junio.
#%% celda 19 [texto]
##### Entrenamiento Final: Junio para Predecir Agosto

#%% celda 20 [código]
# Entrenamiento final: junio (con etiquetas) para predecir agosto (sin etiquetas)
mes_train_jun = 202106
mes_pred_ago = 202108

train_jun = data[data['foto_mes'] == mes_train_jun]
pred_ago = data[data['foto_mes'] == mes_pred_ago]

# IDs de los clientes a predecir, guardados ANTES del drop: son los que van al archivo del submit, en el mismo orden que las predicciones
ids_pred_ago = pred_ago['numero_de_cliente'].values

# El target es el fusionado (cols_a_descartar viene de la celda anterior)
X_train_jun = train_jun.drop(columns=cols_a_descartar)
y_train_jun = train_jun['clase_binaria_b12']
X_pred_ago = pred_ago.drop(columns=cols_a_descartar)

train_data_lgb_jun = lgb.Dataset(X_train_jun, label=y_train_jun)

# Chequeos: 599 columnas, 164.647 clientes a predecir, y cuántos positivos hay en junio
print(X_train_jun.shape, X_pred_ago.shape, len(ids_pred_ago))          # CAMBIO: sin la comparación con abril
print(y_train_jun.value_counts())

# [Anotación · líneas 282–309] Verifica que haya al menos 40 semillas y toma semillas[20:40]. Crea la carpeta
#   modelos/cpt04_modelos_TrainJun_FE04b_opt/. Para cada una de las 20 semillas reemplaza seed en params,
#   entrena con lgb.train sobre junio con best_iter rondas, guarda el modelo en un archivo de texto y predice
#   agosto, guardando las probabilidades en un diccionario con clave (25, semilla). Al terminar guarda el
#   diccionario en un .pkl y los IDs de agosto en un .npy.
#%% celda 21 [texto]
##### Agosto: 20 Semillas Nuevas con la Receta del Trial 25 (Target Fusionado), Entrenadas con Junio

#%% celda 22 [código]
# 20 semillas nuevas, distintas de las usadas en la validación (semillas[:20]); hacen falta al menos 40 semillas
assert len(semillas) >= 40
semillas_pred = semillas[20:40]

carpeta_modelos_pred = modelos_path + 'cpt04_modelos_TrainJun_FE04b_opt/'
os.makedirs(carpeta_modelos_pred, exist_ok=True)          # carpeta nueva: no se mezcla con los modelos de abril

resultados_pred_b12 = {}                                  # probabilidades de agosto de cada modelo: (trial, semilla) -> probabilidades

for seed in semillas_pred:
    params_seed = {**params, 'seed': seed}                # receta del trial 25 (params y best_iter de la celda del fusionado)

    # Entrena con junio (target fusionado), guarda el modelo y predice agosto
    model_seed = lgb.train(params_seed, train_data_lgb_jun, num_boost_round=best_iter)
    model_seed.save_model(carpeta_modelos_pred + f"cpt04_TrainJun-FE04b_PredAgo_modb12_t25_s{seed}.txt")
    resultados_pred_b12[(25, seed)] = model_seed.predict(X_pred_ago)
    print(f'semilla {seed} lista')

# Guarda las probabilidades y los IDs, en el mismo orden (van juntos para armar los submits)
with open(modelos_path + 'cpt04_TrainJun-FE04b_PredAgo_probb12_t25.pkl', 'wb') as f:
    pickle.dump(resultados_pred_b12, f)
np.save(modelos_path + 'cpt04_TrainJun-FE04b_PredAgo_ids_pred.npy', ids_pred_ago)

print(len(resultados_pred_b12), 'modelos entrenados con junio para predecir agosto')

# [Anotación · líneas 311–331] Define las partes del nombre del archivo (submit '04', meses 'aja',
#   'FE04bOpt'), N_final = 12000 y la carpeta de salida data/out/. Define escribir_ids(ruta, ids), que escribe
#   los IDs convertidos a entero, uno por línea y sin encabezado.
#%% celda 23 [texto]
##### Archivo Final: Semillerío con Corte N = 12.000

#%% celda 24 [código]
# Archivo final: semillerío (promedio de las 20 semillas de agosto) con corte en N

nro_submit = '04'            # número de submit
meses_sub = 'aja'            # abril-junio-agosto
fe_sub = 'FE04bOpt'          # dataset + otra información (FE04bOpt = con deltas + optimización)

N_final = 12000              # CAMBIO: corte final (~7,3% de los clientes de agosto), elegido con el público del bot

pref_carpeta = f'submit{nro_submit}{meses_sub}{fe_sub}'      # da 'submit04ajaFE04bOpt'
pref_archivo = f'Sbm{nro_submit}{meses_sub}{fe_sub}'         # da 'Sbm04ajaFE04bOpt'

carpeta_subs = dataset_path + 'out/'                    # los submits van en data/out

def escribir_ids(ruta, ids):
  # IDs como enteros (nunca notación científica), uno por línea, sin encabezado
    with open(ruta, 'w') as f:
        f.write('\n'.join(str(int(c)) for c in ids))

# [Anotación · líneas 333–345] Reúne las probabilidades de las 20 semillas y comprueba que cada serie tenga el
#   mismo largo que la lista de IDs de agosto. Las promedia cliente por cliente, ordena los índices de mayor a
#   menor promedio y toma los primeros 12.000; escribe esos numero_de_cliente en
#   data/out/submit04ajaFE04bOptN12000Sem/Sbm04ajaFE04bOptN12000_sem.csv.
# Probabilidades de agosto de las 20 semillas, cliente por cliente, en el mismo orden que ids_pred_ago
p_semillas = {seed: resultados_pred_b12[(25, seed)] for seed in semillas_pred}
assert all(len(p) == len(ids_pred_ago) for p in p_semillas.values())

# Semillerío: promedio de las 20 probabilidades, cliente por cliente
p_prom = np.mean(list(p_semillas.values()), axis=0)

# Un solo archivo: los N clientes con mayor probabilidad promedio
carpeta_sem = carpeta_subs + f'{pref_carpeta}N{N_final}Sem/'
os.makedirs(carpeta_sem, exist_ok=True)
ruta_final = carpeta_sem + f'{pref_archivo}N{N_final}_sem.csv'
idx = np.argsort(p_prom)[::-1][:N_final]
escribir_ids(ruta_final, ids_pred_ago[idx])

# [Anotación · líneas 347–350] Relee el archivo escrito e imprime tres chequeos: cantidad de líneas igual a
#   N_final, ausencia del texto 'e+' e IDs sin repetir. Salida guardada en el .ipynb: los tres en True.
# Chequeos antes de mandar
texto = open(ruta_final).read()
ids = texto.split('\n')
print(N_final, '| semillerío | N líneas:', len(ids) == N_final, '| sin e+:', 'e+' not in texto, '| IDs únicos:', len(set(ids)) == len(ids))

# [Anotación · líneas 352–363] Lee data/out/Sbm04ajaFE04bOptN12000_sem_final.csv, el archivo enviado al bot, e
#   imprime la cantidad de IDs enviados y generados, el tamaño de la intersección entre ambos conjuntos y si los
#   dos textos son idénticos. Salida guardada en el .ipynb: 12.000 enviados, 12.000 generados, 12.000 en común,
#   idénticos True.
#%% celda 25 [texto]
##### Comparación con el Archivo Enviado al Bot

#%% celda 26 [código]
# Compara el archivo recién generado con el que se envió como entrega final (se guarda en submit_final/)
archivo_enviado = dataset_path + 'out/Sbm04ajaFE04bOptN12000_sem_final.csv'     # el CSV que se subió al bot

texto_enviado = open(archivo_enviado).read()
ids_enviados = texto_enviado.split('\n')
print('IDs enviados:', len(ids_enviados), '| IDs generados:', len(ids))
print('IDs en común:', len(set(ids_enviados) & set(ids)))
print('Archivos idénticos (mismo orden):', texto_enviado == texto)
```


## Explicaciones del alumno (texto original)

### gtoyos/DMEyF_Competencia01_Entrega/README.md

> # DMEyF 2026 - Competencia 1 - Entrega final
>
> Predicción de BAJA+2 para agosto de 2026 (foto_mes 202108).
>
> **Entrega final (el archivo que se subió a zulip):** promedio de 20 semillas, LightGBM con FE04b y los hiperparámetros del trial 25 de la optimización, entrenado con junio (target fusionado BAJA+1 + BAJA+2) y con corte en **N = 12.000** clientes.
>
> Archivo: `data/out/Sbm04ajaFE04bOptN12000_sem_final.csv`
>
> ## Estructura
>
> ```
> DMEyF_Competencia01_Entrega/
> ├── README.md
> ├── scripts/
> │   ├── DMEyF_Competencia01_EntregaFinal.ipynb   <- notebook final: genera el archivo entregado
> │   └── semillas.py                              <- lista de semillas (SEMILLAS)
> └── data/
>     ├── fe04_b_con_delta1.txt                    <- columnas usadas por el modelo (602)
>     ├── competencia_01_fe03.parquet              <- NO está en el repo (1,86 GB): ver abajo
>     ├── databases/
>     │   └── cpt2_optim_lgbm_Step1.db             <- optimización bayesiana (Optuna, 50 trials)
>     └── out/
>         └── Sbm04ajaFE04bOptN12000_sem_final.csv <- archivo entregado
> ```
>
> ## Cómo replicar la entrega
>
> ### 1. Descargar `competencia_01_fe03.parquet`
>
> El parquet pesa 1,86 GB y no entra en GitHub. Descargarlo y dejarlo en `data/competencia_01_fe03.parquet`:
>
> **https://drive.google.com/file/d/1iHL2qZQgRHsGoHBrwUz-ELsM2gTyh5Zh/view?usp=sharing**
>
> (Google Drive puede mostrar un aviso de "no se puede analizar en busca de virus" por el tamaño; se puede descargar igual.)
>
> Contiene el dataset de la competencia (1.614 columnas) con el feature engineering y los tipos ya corregidos.
>
> ### 2. Lista de columnas
>
> `data/fe04_b_con_delta1.txt` (una columna por línea, 602) se construyó a partir de las columnas del parquet. Incluye:
>
> - las 155 columnas originales (con `numero_de_cliente`, `foto_mes` y `clase_ternaria`);
> - 16 variables intra mes creadas a mano;
> - las variables intra mes de ranking, `pr_` (percent_rank) y `nt10_` (ntile 10), 140 de cada una;
> - las 151 variables históricas de orden 1 (`delta_1_`).
>
> Se excluyen:
>
> - otras históricas (`delta_2_`, `delta_3_`, `avg_3_`, `stddev_3_`, `min_3_`, `max_3_`, `ratio_avg3_`);
> - 10 derivadas de `ccajas_depositos`, que está rota en 202105 (todos sus valores son cero).
>
> Total: 155 + 16 + 140 + 140 + 151 = 602. A `ccajas_depositos` se le asigna  NA para 202105 al cargar los datos (lo hace la función `cargar` de la notebook).
>
> ### 3. Ejecutar la notebook
>
> Abrir `scripts/DMEyF_Competencia01_EntregaFinal.ipynb` (la carpeta de trabajo tiene que ser `scripts/`) y ejecutar todas las celdas. Tarda unos 20-25 minutos (entrena 20 modelos). La notebook:
>
> 1. Carga los meses 202104, 202106 y 202108 con las columnas de `fe04_b_con_delta1.txt`.
> 2. Lee la optimización guardada en `data/databases/cpt2_optim_lgbm_Step1.db` (50 trials ya completos; no corre trials nuevos).
> 3. Toma los hiperparámetros y el `best_iter` del **trial 25**.
> 4. Entrena con junio (target fusionado BAJA+1 + BAJA+2) 20 modelos, uno por semilla (`semillas[20:40]`), y predice agosto.
> 5. Promedia las 20 probabilidades por cliente y toma los **12.000** clientes como punto de corte.
> 6. Guarda el archivo en `data/out/submit04ajaFE04bOptN12000Sem/Sbm04ajaFE04bOptN12000_sem.csv`.
> 7. Lo compara con el archivo enviado (`data/out/Sbm04ajaFE04bOptN12000_sem_final.csv`): deben coincidir los 12.000 IDs y el orden.
>
> Resultado de la corrida de verificación: `IDs en común: 12000` y `Archivos idénticos (mismo orden): True`.
>
> ## Optimización de hiperparámetros
>
> - Estudio de Optuna `cpt2_step1_b2_lgbm_sss_3000_con_FE04-b`, guardado en `data/databases/cpt2_optim_lgbm_Step1.db`.
> - Se optimizó con **abril** como mes de entrenamiento, con target BAJA+2 solo, maximizando el AUC en validación cruzada (`StratifiedShuffleSplit`, 5 splits, 30% de test) con FE04b.
> - Parámetros fijos: `max_bin = 31`, `min_data_in_leaf = 0`, `feature_pre_filter = False`. Parámetros optimizados: `num_leaves`, `min_sum_hessian_in_leaf`, `learning_rate`, `feature_fraction`, `feature_fraction_bynode`, `bagging_fraction`, `bagging_freq`. El número de árboles (`best_iter`) sale de la validación cruzada de cada trial.
> - La optimización **no es reproducible exactamente** (el sampler de Optuna no tiene semilla fija). Por eso se incluye el `.db`: la notebook final lee de ahí el trial 25 (la notebook imprime sus hiperparámetros y su `best_iter`).
>
> ## Cómo se llegó al trial 25 y al corte N = 12.000
>
> - **Trial 25:** se validaron los 5 mejores trials por AUC, cada uno con 20 semillas, entrenados con abril y medidos en junio con la ganancia real de BAJA+2. El trial 25 quedó entre los candidatos con ganancia más alta y se eligió para la configuración final.
> - **Entrenamiento final:** con junio y el target fusionado BAJA+1 + BAJA+2. La ganancia siempre se midió con BAJA+2 real (+1.072.500 si acierta, −27.500 si no).
> - **Corte N:** el barrido del corte se definió a partir del mejor corte en junio, pasado a porcentaje de clientes y trasladado a agosto. El valor final de **12.000** (≈ 7,3% de los clientes de agosto) se eligió con el puntaje público del bot, probando N entre 9.000 y 16.037. El puntaje público tiene ruido (≈ 25% de los clientes de agosto), así que se tomó una zona alta (10.000 a 13.122) y no un pico aislado. Como se eligió el máximo del público, ese puntaje puede estar algo inflado respecto del privado.
>
> ## Reproducibilidad
>
> - Los modelos usan semillas de `scripts/semillas.py`. Los 20 modelos finales usan `semillas[20:40]`.
> - La notebook usa `lgb_threads = 10`. LightGBM no garantiza resultados idénticos con otra cantidad de threads; en la máquina de desarrollo se obtuvo exactamente el mismo archivo. En otra máquina podría moverse algún cliente del borde del corte. El archivo entregado está en `data/out/Sbm04ajaFE04bOptN12000_sem_final.csv`.
> - No se incluyen los modelos entrenados: se regeneran al ejecutar la notebook.
> - Entorno: Python 3.11.16. Librerías principales y versiones: `lightgbm` 4.7.0, `optuna` 5.0.0, `duckdb` 1.0.0, `pandas` 2.3.3, `numpy` 2.4.6, `scikit-learn` 1.9.1, `plotly` 7.0.0, `matplotlib` 3.11.1.

