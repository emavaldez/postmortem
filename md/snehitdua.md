# Snehit Dua — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: SnehitDua
- Repositorio: https://github.com/SnehitDua/Churn-Prediction-DMEyF
- Link posteado: https://github.com/SnehitDua/Churn-Prediction-DMEyF/
- Commit: b0f3d748e2bc563013b8f970df00f0c8a2fb0595
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/snehitdua/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/snehitdua.json

## Resumen

La entrega es un repositorio con un único notebook de Python (churn-prediction.ipynb), sin README, una carpeta modelos/ con 18 modelos LightGBM comprimidos y una carpeta output/ con la base SQLite del estudio de Optuna y un CSV de 11.000 líneas. El notebook lee competencia_01.csv con pandas, arma una clase binaria con positivo = BAJA+1 o BAJA+2, pasa a NaN ccajas_depositos en 202105 y agrega lag 1, lag 2, delta 1 y delta 2 de todas las columnas originales. Submuestrea al 10 % las filas de clase 0. Con Optuna (TPE) busca num_leaves y min_sum_hessian_in_leaf entrenando LightGBM sobre 202103–202105 y midiendo en 202106 una ganancia suavizada cada 32 iteraciones, hasta 2.000; los demás hiperparámetros están fijos en el código. Con los parámetros del trial de mayor ganancia y 1,1 veces su cantidad de iteraciones entrena sobre 202103–202106 un modelo por cada una de 18 semillas (o lo carga de modelos/ si el archivo existe), predice 202108, corrige las probabilidades por el submuestreo, las promedia y escribe los 11.000 clientes de mayor promedio.

**Qué entrega.** Un CSV sin encabezado con 11.000 numero_de_cliente de 202108, uno por línea: los de mayor probabilidad promedio entre los 18 modelos. El repositorio incluye output/final_submit_20261011.csv, con 11.000 líneas; ese nombre no figura en el código, que arma el nombre como <tag>_s00.csv dentro de una carpeta <tag> y además genera <tag>.zip (con las constantes escritas, tag = './outputfinal_submit').

**Cómo se ejecuta.** No se indica. No hay README ni otro texto con instrucciones. Del código surge que el notebook espera el dataset en ./data/competencia_01.csv, instala lightgbm y optuna con pip en la primera celda de código, guarda el estudio de Optuna en ./output/Optuna.db y busca modelos ya entrenados en ./modelos/.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: clase_binaria = 1 si clase_ternaria es BAJA+1 o BAJA+2 y 0 en otro caso (línea 46). Se usa la misma clase en la optimización, en la función de ganancia y en el modelo final.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** Conserva todas las filas con clase_binaria = 1 y, de las demás, cada una con probabilidad 0,1 (FRAC_NEGATIVOS), con numpy RandomState. En la optimización se aplica a 202103–202105 con semilla 236983; en el modelo final, a 202103–202106 con semilla 236983, y esa misma muestra se usa para los 18 modelos. Las probabilidades predichas se corrigen con frac·p / (frac·p + 1 − p).
- **Calidad de datos:** Asigna NaN a ccajas_depositos en las filas de 202105 (línea 55). No se observa otro tratamiento en el código.
- **Drifting:** No se observa en el código
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** Lag 1 y lag 2, y delta 1 y delta 2 (valor actual menos el lag), de todas las columnas originales salvo numero_de_cliente, foto_mes, clase_ternaria y clase_binaria. El lag sólo toma valor cuando la fila anterior es del mismo cliente y exactamente k meses antes; en otro caso queda NaN. Según la salida guardada en el .ipynb original, resultan 760 variables.
- **Selección de variables:** No se observa en el código
- **Optimización de hiperparámetros:** Optuna con TPESampler (seed 236983, 10 trials iniciales), dirección maximizar y estudio guardado en SQLite (./output/Optuna.db, load_if_exists = True). Busca num_leaves (8 a 2048, escala logarítmica) y min_sum_hessian_in_leaf (1e-8 a 0,1, escala logarítmica), con N_TRIALS = 33. Cada trial entrena 2.000 iteraciones sobre 202103–202105 submuestreado, con 1 semilla, y mide en 202106 la ganancia suavizada cada 32 iteraciones; el valor del trial es el máximo de esa curva después de una media móvil centrada de 5 puntos, y la iteración de ese máximo se guarda como best_iter. El output/Optuna.db del repositorio contiene 34 trials (32 COMPLETE y 2 FAIL).
- **Hiperparámetros finales:** Fijos en el código: objective binary, boosting gbdt, learning_rate 0,005, feature_fraction 0,50, feature_fraction_bynode 0,20, min_data_in_leaf 0, max_bin 31, feature_pre_filter False. num_leaves y min_sum_hessian_in_leaf se toman del trial de mayor valor del estudio, y la cantidad de iteraciones es la parte entera de best_iter × 1,1. Según la salida guardada de la celda 16 y output/Optuna.db: num_leaves 674, min_sum_hessian_in_leaf 0,0018489 y best_iter 1984; el modelo guardado de la semilla 236983 declara num_iterations 2182.
- **Semillas:** SEED = 236983 está escrita en el código. Los 18 modelos finales usan como seed de LightGBM los valores 236983 a 237000 (SEED + s). El submuestreo del conjunto final y el TPESampler usan 236983; en la optimización, el submuestreo y LightGBM usan SEED + k con k = 0.
- **Cantidad de semillas:** 18
- **Ensamble:** Promedio aritmético, cliente por cliente, de las probabilidades corregidas de 18 modelos LightGBM con los mismos hiperparámetros y los mismos datos, que difieren en la semilla (np.mean, línea 297).
- **Corte:** Cantidad fija: los 11.000 clientes de mayor probabilidad promedio (env_min = env_max = 11000 en la llamada de la línea 297). La función cuenta además cuántos clientes superan el umbral 27.500 / 1.100.000 = 0,025 y lo imprime cuando difiere de la cantidad escrita; según la salida guardada de la celda 19, el umbral daba 7.416.
- **Validación:** Un mes posterior al entrenamiento: entrena con 202103–202105 submuestreado y mide en 202106 completo. La métrica es el máximo de la curva de ganancia acumulada (1.100.000 por cada fila con clase_binaria = 1 y −27.500 por cada envío) suavizada con una media móvil de 1.001 envíos sobre los primeros 30.000. Se usa para elegir los dos hiperparámetros buscados y la cantidad de iteraciones.
- **Salidas:** El código escribe: el estudio de Optuna en ./output/Optuna.db; una carpeta <tag> con el CSV <tag>_s00.csv (sin encabezado, un numero_de_cliente por línea) y el archivo <tag>.zip. El repositorio incluye output/Optuna.db, output/final_submit_20261011.csv (11.000 líneas) y 18 archivos modelos/lgb_seed236983.zip a modelos/lgb_seed237000.zip, cada uno con un modelo en formato de texto de LightGBM. No se observa en el notebook la instrucción que guarda esos modelos.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: no
- Explica cómo ejecutar: no
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: No se declara en ningún texto. Los metadatos del .ipynb original indican kernel Python 3, versión de lenguaje 3.13.2 y origen Kaggle (dockerImageVersionId 28755, accelerator none); las salidas guardadas muestran rutas /kaggle/working y /usr/local/lib/python3.13/dist-packages. La tabla version_info de output/Optuna.db registra library_version 5.0.0. La línea 5 instala lightgbm y optuna sin indicar versión.

## Pasos del camino de la entrega

1. **Configuración.** Instala lightgbm y optuna, importa las librerías y define las constantes de la corrida: rutas relativas, 1.100.000 de ganancia por acierto y 27.500 de costo por envío, meses (optimización 202103–202105, validación 202106, modelo final 202103–202106, predicción 202108), lags 1 y 2, fracción de submuestreo 0,1, 33 trials, 2.000 iteraciones como máximo con medición cada 32, max_bin 31, factor 1,1 para las iteraciones finales, semilla base 236983 y 18 modelos finales. (`churn-prediction.ipynb` líneas 4–39)
2. **Lectura del dataset y clase binaria.** Lee ./data/competencia_01.csv con pandas y crea clase_binaria = 1 para BAJA+1 y BAJA+2. Según la salida guardada en el .ipynb original, el dataset tiene 983.061 filas y 156 columnas, con meses 202103 a 202108. (`churn-prediction.ipynb` líneas 45–48)
3. **Variable pasada a NaN.** Asigna NaN a ccajas_depositos en las filas de 202105. (`churn-prediction.ipynb` líneas 54–55)
4. **Lags y deltas.** Para cada columna original calcula el valor de 1 y de 2 meses atrás del mismo cliente (lag 1 y lag 2) y la diferencia del valor actual con cada uno (delta 1 y delta 2). Después descarta las filas de 202107, que sólo se usan para calcular los lags de 202108. Según la salida guardada en el .ipynb original, quedan 760 variables y 818.713 filas. (`churn-prediction.ipynb` líneas 58–84)
5. **Función de ganancia y corrección de probabilidad.** Define la curva de ganancia acumulada ordenando por probabilidad (1.100.000 por fila con etiqueta 1, −27.500 por envío), su versión suavizada con media móvil de 1.001 envíos sobre los primeros 30.000 y la fórmula que revierte en las probabilidades el efecto del submuestreo. (`churn-prediction.ipynb` líneas 92–109)
6. **Submuestreo y conjuntos de entrenamiento y validación.** Submuestrea 202103–202105 conservando todos los positivos y el 10 % de las demás filas (semilla 236983) y arma los Dataset de LightGBM de entrenamiento y de validación; la validación es 202106 completo. Según la salida guardada en el .ipynb original: 54.199 filas de entrenamiento con 6.095 positivos, y 164.114 filas de validación con 1.972 positivos. (`churn-prediction.ipynb` líneas 117–139)
7. **Búsqueda de hiperparámetros con Optuna.** Define los hiperparámetros fijos y el espacio de búsqueda (num_leaves y min_sum_hessian_in_leaf), y una función objetivo que entrena 2.000 iteraciones y devuelve el máximo de la ganancia suavizada medida en 202106 cada 32 iteraciones. Crea o retoma el estudio en ./output/Optuna.db y corre los trials que faltan hasta 33. El output/Optuna.db del repositorio contiene el estudio gan-frac0.1-lags1_2-bin31-tr202103_202104_202105-v202106-s1-it2000-baja12 con 34 trials (32 COMPLETE y 2 FAIL); con ese archivo en ./output, la cuenta max(0, 33 − 34) da 0 trials nuevos. (`churn-prediction.ipynb` líneas 146–208)
8. **Revisión de los trials.** Imprime la tabla de trials ordenada por ganancia y ejecuta una función que avisa si los 5 trials de mayor valor quedan cerca de un extremo del rango de búsqueda o si su best_iter mediano es al menos el 90 % de MAX_ITER. Según la salida guardada en el .ipynb original, el primer lugar es del trial 12 (ganancia 1.239946e+09, que cuenta como acierto BAJA+1 y BAJA+2 en 202106) y se imprime el aviso 'best_iter mediano = 1984 ~ MAX_ITER=2000'. (`churn-prediction.ipynb` líneas 211–233)
9. **Parámetros del modelo final.** Une los hiperparámetros fijos con los dos valores del trial de mayor ganancia y toma su best_iter. Según la salida guardada de la celda 16: num_leaves 674, min_sum_hessian_in_leaf 0,0018489173678270826 y best_iter 1984. (`churn-prediction.ipynb` líneas 236–240)
10. **Modelos finales con 18 semillas y predicción de 202108.** Submuestrea 202103–202106 (fracción 0,1, semilla 236983), fija las iteraciones en la parte entera de best_iter × 1,1 y, para cada semilla de 236983 a 237000, carga el modelo de ./modelos/ si existe o lo entrena. Cada modelo predice 202108 y la probabilidad se corrige por el submuestreo. El repositorio trae los 18 archivos modelos/lgb_seed<semilla>.zip; el de la semilla 236983 contiene un modelo de 2.182 árboles con num_leaves 674 y learning_rate 0,005. Según la salida guardada en el .ipynb original, la celda imprime hasta 'seed 18/20 lista' y termina con KeyboardInterrupt. (`churn-prediction.ipynb` líneas 247–274)
11. **Promedio, corte y archivo de salida.** Promedia las 18 predicciones por cliente, ordena de mayor a menor y escribe los primeros 11.000 numero_de_cliente en un CSV sin encabezado dentro de una carpeta nueva, que después comprime en un .zip. Según la salida guardada de la celda 19, 7.416 clientes superaban el umbral 0,025 y el archivo se escribió con 11.000. (`churn-prediction.ipynb` líneas 277–297)

## Archivos

- `churn-prediction.ipynb` · principal · Jupyter (python) · 297 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/snehitdua/churn-prediction.ipynb.txt) — Notebook de Python con todo el camino de la entrega: lectura del dataset, clase binaria, lags y deltas, submuestreo, búsqueda de hiperparámetros de LightGBM con Optuna validando en 202106, entrenamiento final con 18 semillas sobre 202103–202106 y escritura del CSV con 11.000 clientes de 202108.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### churn-prediction.ipynb

Notebook de Python con todo el camino de la entrega: lectura del dataset, clase binaria, lags y deltas, submuestreo, búsqueda de hiperparámetros de LightGBM con Optuna validando en 202106, entrenamiento final con 18 semillas sobre 202103–202106 y escritura del CSV con 11.000 clientes de 202108.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–5] Título de la sección 0 y celda que instala lightgbm y optuna con pip, sin indicar
#   versión.
#%% celda 1 [texto]
## 0. Configuración

#%% celda 2 [código]
!pip install -q lightgbm optuna

# [Anotación · líneas 7–28] Importa gc, os, numpy, pandas, lightgbm, optuna y shutil. Define la ruta del
#   dataset (./data/competencia_01.csv) y la de salida (./output), la ganancia por acierto (1.100.000, con el
#   comentario '2.200.000 * 0.5') y el costo por envío (27.500). Fija el mes a predecir (202108), los meses de
#   entrenamiento de la optimización (202103, 202104 y 202105), el de validación (202106) y los del modelo final
#   (202103 a 202106), los lags (1 y 2), la fracción de filas de clase 0 que conserva el submuestreo (0,1) y la
#   cantidad de trials (33).
#%% celda 3 [código]
import gc, os
import numpy as np
import pandas as pd
import lightgbm as lgb
import optuna
import shutil

DATA_PATH = './data/competencia_01.csv'
OUTPUT_PATH = './output'

GANANCIA_ACIERTO = 1_100_000  # 2.200.000 * 0.5
COSTO_ENVIO = 27_500

MES_TARGET = 202108
TRAIN_MESES = [202103, 202104, 202105]
VALID_MES = 202106
FINAL_MESES = [202103, 202104, 202105, 202106]

LAGS = [1, 2]
FRAC_NEGATIVOS = 0.1  # submuestreo de CONTINUA
N_TRIALS = 33  # llegue a correr hasta 33 trials

# [Anotación · líneas 30–39] Parámetros de la optimización: 1 semilla por trial, 2.000 iteraciones como
#   máximo, medición de la ganancia cada 32 iteraciones, media móvil de 5 puntos de medición, max_bin 31 y
#   factor 1,1 para la cantidad de iteraciones del modelo final. Define la semilla base 236983 y la cantidad de
#   modelos finales, 18.
# ----- Optimización de hiperparámetros -----
N_SEEDS_TRIAL = 1  # seeds por trial (cambian submuestreo y LightGBM); se promedia la curva de ganancia
MAX_ITER = 2000  # se entrena UNA vez hasta acá por trial y se elige la mejor iteración
EVAL_CADA = 32  # cada cuántas iteraciones se mide la ganancia
SUAVIZAR_CKPT = 5  # media móvil (en checkpoints) sobre la curva de ganancia vs iteración
MAX_BIN = 31  # hiperparametro fijo
FACTOR_ITER_FINAL = 1.1  # el final entrena con 4 meses y se optimizó con 2: algo más de iteraciones

SEED = 236983
N_SEEDS_SUBMIT = 18  # modelos finales (llegue a hacer solo 18 modelos)

# [Anotación · líneas 41–48] Lee el CSV completo con pandas y crea clase_binaria: 1 si clase_ternaria es
#   BAJA+2 o BAJA+1 y 0 en otro caso (int8). Imprime las dimensiones, la memoria usada y, por foto_mes, la suma,
#   la media y la cantidad de filas de clase_binaria.
#%% celda 4 [texto]
## 1. Carga de datos

#%% celda 5 [código]
df = pd.read_csv(DATA_PATH, low_memory=False)
df['clase_binaria'] = (df['clase_ternaria'].isin(['BAJA+2', 'BAJA+1'])).astype('int8')
print(df.shape, f"{df.memory_usage().sum()/1e9:.2f} GB")
print(df.groupby('foto_mes')['clase_binaria'].agg(['sum', 'mean', 'size']))

# [Anotación · líneas 50–55] Asigna NaN a ccajas_depositos en las filas de foto_mes 202105; el comentario
#   indica que la variable está rota en ese mes.
#%% celda 6 [texto]
## 2. Feature engineering

#%% celda 7 [código]
# ccajas_depositos esta roto en 202105
df.loc[df.foto_mes == 202105, "ccajas_depositos"] = np.nan

# [Anotación · líneas 57–74] Define agregar_lags: ordena por cliente y mes y calcula un índice de mes
#   consecutivo (año × 12 + mes). Para cada k de la lista arma una máscara que es verdadera cuando la fila
#   ubicada k posiciones antes es del mismo cliente y exactamente k meses anterior. Para cada columna guarda el
#   valor de esa fila como <col>_lag<k> (float32, NaN donde la máscara es falsa) y la diferencia entre el valor
#   actual y ese lag como <col>_delta<k>. Devuelve la tabla con las columnas nuevas agregadas.
#%% celda 8 [código]
def agregar_lags(df, cols, lags):
    df = df.sort_values(['numero_de_cliente', 'foto_mes']).reset_index(drop=True)
    cli  = df['numero_de_cliente'].values
    midx = (df['foto_mes'] // 100 * 12 + df['foto_mes'] % 100).values   # índice de mes consecutivo
    n = len(df)
    nuevas = {}
    for k in lags:
        ok = np.zeros(n, dtype=bool)                  # mismo cliente y exactamente k meses antes
        ok[k:] = (cli[k:] == cli[:-k]) & ((midx[k:] - midx[:-k]) == k)
        for c in cols:
            a = df[c].values.astype('float32')
            lag = np.full(n, np.nan, dtype='float32')
            lag[k:] = a[:-k]
            lag[~ok] = np.nan
            nuevas[f'{c}_lag{k}']   = lag
            nuevas[f'{c}_delta{k}'] = a - lag
    return pd.concat([df, pd.DataFrame(nuevas, index=df.index)], axis=1)

# [Anotación · líneas 76–84] Toma como columnas base todas menos numero_de_cliente, foto_mes, clase_ternaria y
#   clase_binaria y les aplica agregar_lags con k = 1 y 2. Después conserva sólo las filas de 202103, 202104,
#   202105, 202106 y 202108; el comentario indica que 202107 sólo sirve para los lags. Arma la lista features
#   con todas las columnas salvo las cuatro excluidas e imprime cuántas son y cuántas filas quedan.
excluir   = ['numero_de_cliente', 'foto_mes', 'clase_ternaria', 'clase_binaria']
cols_base = [c for c in df.columns if c not in excluir]

df = agregar_lags(df, cols_base, LAGS)
df = df[df['foto_mes'].isin(FINAL_MESES + [VALID_MES, MES_TARGET])].reset_index(drop=True)  # 202107 solo servía para los lags
gc.collect()

features = [c for c in df.columns if c not in excluir]
print('features:', len(features), '| filas:', len(df))

# [Anotación · líneas 86–102] Texto de la sección 3 y dos funciones. curva_ganancia ordena de mayor a menor
#   predicción, asigna 1.100.000 a cada fila con etiqueta 1, resta 27.500 por cada fila y devuelve la suma
#   acumulada. ganancia_suavizada toma los primeros 30.000 puntos de esa curva, calcula con sumas acumuladas la
#   media móvil de ventana 1.001 y devuelve el máximo de esa media y la posición del centro de la ventana donde
#   ocurre.
#%% celda 9 [texto]
## 3. Función de ganancia
Se ordenan los clientes por probabilidad y se calcula la ganancia acumulada según cuántos reciben estímulo.  
Para evitar quedarnos con un pico casual, se suaviza la curva con un promedio móvil.

#%% celda 10 [código]
def curva_ganancia(y, pred):
    orden = np.argsort(-pred, kind='stable')
    g = np.where(y[orden] == 1, GANANCIA_ACIERTO, 0) - COSTO_ENVIO
    return np.cumsum(g)

def ganancia_suavizada(y, pred, ventana=1001, top=30000):
    """Devuelve (ganancia máxima suavizada, cantidad de envíos donde ocurre)."""
    c = curva_ganancia(y, pred)[:top]
    cs = np.concatenate([[0], np.cumsum(c)])
    m = (cs[ventana:] - cs[:-ventana]) / ventana
    return m.max(), int(m.argmax() + ventana // 2)

# [Anotación · líneas 104–109] lgb_ganancia envuelve ganancia_suavizada con la forma que LightGBM espera de
#   una métrica propia que se maximiza (nombre, valor, True); no se la llama en el resto del notebook.
#   corregir_prob transforma una probabilidad p obtenida con submuestreo de fracción frac en frac·p / (frac·p +
#   1 − p).
def lgb_ganancia(preds, data):  # métrica custom para early stopping
    g, _ = ganancia_suavizada(data.get_label(), preds)
    return 'ganancia', g, True

def corregir_prob(p, frac):  # deshace el submuestreo de negativos
    return frac * p / (frac * p + (1 - p))

# [Anotación · líneas 111–123] Texto de la sección 4. submuestrear conserva todas las filas con clase_binaria
#   = 1 y, del resto, las que reciben un número uniforme menor a frac de un generador RandomState inicializado
#   con la semilla dada. DS_PARAMS fija feature_pre_filter = False y max_bin = 31 para los Dataset de LightGBM.
#%% celda 11 [texto]
## 4. Datasets de entrenamiento y validación
- **Train:** todos los BAJA+2 y BAJA+1 y una fracción de los negativos.
- **Validación:** el mes completo, sin submuestrear.

#%% celda 12 [código]
def submuestrear(d, frac, seed):
    rng = np.random.RandomState(seed)
    keep = (d['clase_binaria'] == 1).values | (rng.rand(len(d)) < frac)
    return d[keep]

# Params de Dataset: tienen que ser IDÉNTICOS en la optimización y en el modelo final
DS_PARAMS = {'feature_pre_filter': False, 'max_bin': MAX_BIN}

# [Anotación · líneas 125–139] Separa el mes 202106 completo como validación (X_valid, y_valid) y los meses
#   202103–202105 como base de entrenamiento. Para cada una de las N_SEEDS_TRIAL = 1 semillas submuestrea la
#   base con fracción 0,1 y semilla 236983 + k, y construye el Dataset de entrenamiento y el de validación
#   referenciado a él, ambos con free_raw_data = False. Guarda en n_train_opt la cantidad de filas de
#   entrenamiento e imprime filas y positivos de cada conjunto.
df_valid = df[df['foto_mes'] == VALID_MES]
X_valid  = df_valid[features]
y_valid  = df_valid['clase_binaria'].values
df_train_base = df[df['foto_mes'].isin(TRAIN_MESES)]

# un par (dtrain, dvalid) por seed: cada seed submuestrea distinto los negativos
dsets = []
for k in range(N_SEEDS_TRIAL):
    d_tr = submuestrear(df_train_base, FRAC_NEGATIVOS, SEED + k)
    dtrain = lgb.Dataset(d_tr[features], label=d_tr['clase_binaria'], params=DS_PARAMS, free_raw_data=False)
    dvalid = lgb.Dataset(X_valid, label=y_valid, reference=dtrain, free_raw_data=False)
    dsets.append((dtrain, dvalid))
    print(f'seed {k}: train {len(d_tr)} | positivos {int(d_tr["clase_binaria"].sum())}')
n_train_opt = len(d_tr)  # filas de train en la optimización (para comparar con el final)
print('valid:', len(df_valid), '| positivos:', int(y_valid.sum()))

# [Anotación · líneas 141–155] Título de la sección 5. PARAMS_FIJOS reúne los hiperparámetros que no se
#   buscan: objective binary, metric None, boosting gbdt, feature_pre_filter False, max_bin 31, min_data_in_leaf
#   0, feature_fraction 0,50, feature_fraction_bynode 0,20 y learning_rate 0,005. ESPACIO define los rangos de
#   búsqueda: num_leaves entre 8 y 2048 y min_sum_hessian_in_leaf entre 1e-8 y 0,1.
#%% celda 13 [texto]
## 5. Optimización bayesiana

#%% celda 14 [código]
# (1.7 Training Strategy)
PARAMS_FIJOS = dict(
    objective='binary', metric='None', verbosity=-1, boosting_type='gbdt',
    feature_pre_filter=False,
    max_bin=MAX_BIN,
    min_data_in_leaf=0,
    feature_fraction=0.50,
    feature_fraction_bynode=0.20,
    learning_rate=0.005
)
ESPACIO = {'num_leaves': (8, 2048), 'min_sum_hessian_in_leaf': (1e-8, 0.1)}

# [Anotación · líneas 157–166] Clase GananciaCada, que se pasa a LightGBM como métrica propia (feval): cuenta
#   las llamadas y calcula la ganancia suavizada sólo cuando el contador es múltiplo de `cada`; en las demás
#   devuelve NaN.
class GananciaCada:
    """feval: ganancia suavizada solo cada `cada` iteraciones (el resto devuelve NaN y se ignora)."""
    def __init__(self, cada):
        self.cada, self.i = cada, 0
    def __call__(self, preds, data):
        self.i += 1
        if self.i % self.cada:
            return 'ganancia', np.nan, True
        g, _ = ganancia_suavizada(data.get_label(), preds)
        return 'ganancia', g, True

# [Anotación · líneas 168–191] Función objetivo del estudio. Sugiere num_leaves (entero, escala logarítmica) y
#   min_sum_hessian_in_leaf (real, escala logarítmica) y, por cada par de datasets, entrena 2.000 iteraciones
#   con seed 236983 + k registrando la ganancia en validación. Toma los valores medidos cada 32 iteraciones (32,
#   64, …, 1984 cuando se completan las 2.000), los promedia entre semillas, les aplica una media móvil centrada
#   de 5 puntos y elige el punto de mayor valor. Guarda en el trial la iteración de ese punto (best_iter) y la
#   ganancia de cada semilla en ese punto sin la media móvil, y devuelve el valor suavizado. Si no hay ningún
#   punto medido lanza TrialPruned.
def objective(trial):
    params = dict(PARAMS_FIJOS,
        num_leaves=trial.suggest_int('num_leaves', *ESPACIO['num_leaves'], log=True),
        min_sum_hessian_in_leaf=trial.suggest_float('min_sum_hessian_in_leaf', *ESPACIO['min_sum_hessian_in_leaf'], log=True))

    curvas = []
    for k, (dtrain, dvalid) in enumerate(dsets):
        ev = {}
        lgb.train({**params, 'seed': SEED + k}, dtrain, num_boost_round=MAX_ITER,
                  valid_sets=[dvalid], valid_names=['valid'],
                  feval=GananciaCada(EVAL_CADA),
                  callbacks=[lgb.record_evaluation(ev)])
        curvas.append(np.array(ev['valid']['ganancia']))

    n = min(len(c) for c in curvas)  # LightGBM puede cortar antes si no hay más splits válidos
    idx = np.arange(EVAL_CADA - 1, n, EVAL_CADA)  # iteraciones donde se midió (0-based)
    if len(idx) == 0:
        raise optuna.TrialPruned()
    media = np.mean([c[idx] for c in curvas], axis=0)  # promedio entre seeds
    media = pd.Series(media).rolling(SUAVIZAR_CKPT, center=True, min_periods=1).mean().values
    i = int(media.argmax())
    trial.set_user_attr('best_iter', int(idx[i] + 1))
    trial.set_user_attr('ganancia_por_seed', [float(c[idx[i]]) for c in curvas])
    return float(media[i])

# [Anotación · líneas 193–208] Arma el nombre del estudio con la configuración (fracción, lags, max_bin,
#   meses, semillas por trial e iteraciones) y crea o retoma un estudio de Optuna que maximiza, con TPESampler
#   (seed 236983, 10 trials iniciales) y almacenamiento SQLite en ./output/Optuna.db (load_if_exists = True).
#   Corre la diferencia entre N_TRIALS = 33 y la cantidad de trials ya guardados, y al final imprime el valor,
#   la ganancia por semilla, los parámetros y el best_iter del trial de mayor valor.
STUDY_NAME = (f'gan-frac{FRAC_NEGATIVOS}-lags{"_".join(map(str, LAGS))}-bin{MAX_BIN}'
              f'-tr{"_".join(map(str, TRAIN_MESES))}-v{VALID_MES}-s{N_SEEDS_TRIAL}-it{MAX_ITER}-baja12')
study = optuna.create_study(
    direction='maximize',
    sampler=optuna.samplers.TPESampler(seed=SEED, n_startup_trials=10),
    study_name=STUDY_NAME,
    storage=f'sqlite:///{OUTPUT_PATH}/Optuna.db',
    load_if_exists=True)

pendientes = max(0, N_TRIALS - len(study.trials))
print(f'{STUDY_NAME}: {len(study.trials)} trials previos, {pendientes} por correr')
study.optimize(objective, n_trials=pendientes, show_progress_bar=True)

print('Mejor ganancia suavizada (media de seeds):', f'{study.best_value:,.0f}')
print('Ganancia por seed:', [f'{g:,.0f}' for g in study.best_trial.user_attrs['ganancia_por_seed']])
print('Mejores parámetros:', study.best_params, '| best_iter:', study.best_trial.user_attrs['best_iter'])

# [Anotación · líneas 210–214] Arma una tabla con número de trial, ganancia, best_iter, num_leaves y
#   min_sum_hessian_in_leaf de todos los trials, ordenada de mayor a menor ganancia, y la imprime.
#%% celda 15 [código]
t = study.trials_dataframe()[['number', 'value', 'user_attrs_best_iter',
                              'params_num_leaves', 'params_min_sum_hessian_in_leaf']]
t = t.rename(columns={'value': 'ganancia', 'user_attrs_best_iter': 'best_iter'}).sort_values('ganancia', ascending=False)
print(t.to_string())

# [Anotación · líneas 216–233] chequear_bordes toma los 5 trials de mayor valor y, para cada hiperparámetro,
#   calcula la mediana de su posición relativa dentro del rango en escala logarítmica; si queda por debajo de
#   0,10 o por encima de 0,90 imprime un aviso para ampliar el rango. También imprime un aviso si la mediana de
#   best_iter es mayor o igual al 90 % de MAX_ITER (1.800). Si no hay avisos imprime 'Bordes OK'. La última
#   línea ejecuta la función sobre el estudio.
def chequear_bordes(study, top=5, margen=0.10):
    """Avisa si los mejores trials se pegan a un borde del espacio (el óptimo estaría afuera)."""
    mejores = sorted([tr for tr in study.trials if tr.value is not None], key=lambda tr: -tr.value)[:top]
    ok = True
    for nombre, (lo, hi) in ESPACIO.items():
        pos = np.median([(np.log(tr.params[nombre]) - np.log(lo)) / (np.log(hi) - np.log(lo)) for tr in mejores])
        if pos < margen or pos > 1 - margen:
            ok = False
            print(f'⚠ {nombre}: los {top} mejores trials están pegados al borde {"inferior" if pos < margen else "superior"} '
                  f'de {ESPACIO[nombre]} -> ampliar el rango')
    bi = [tr.user_attrs['best_iter'] for tr in mejores]
    if np.median(bi) >= 0.9 * MAX_ITER:
        ok = False
        print(f'⚠ best_iter mediano = {int(np.median(bi))} ~ MAX_ITER={MAX_ITER} -> subir MAX_ITER')
    if ok:
        print('Bordes OK: los mejores trials no están pegados a los límites del espacio.')

chequear_bordes(study)

# [Anotación · líneas 235–240] Arma best_params uniendo PARAMS_FIJOS con el num_leaves y el
#   min_sum_hessian_in_leaf del trial de mayor valor, toma el best_iter de ese trial y muestra ambos.
#%% celda 16 [código]
bp = study.best_params
best_params = dict(PARAMS_FIJOS, num_leaves=bp['num_leaves'],
                   min_sum_hessian_in_leaf=bp['min_sum_hessian_in_leaf'])    # incluye max_bin
best_iter = study.best_trial.user_attrs['best_iter']
bp, best_iter

# [Anotación · líneas 242–257] Texto de la sección 6. Submuestrea los meses 202103–202106 con fracción 0,1 y
#   semilla 236983 y construye el Dataset final; separa las filas de 202108 y sus numero_de_cliente. Copia
#   best_params sin cambios en best_params_final y fija la cantidad de iteraciones en la parte entera de
#   best_iter × 1,1. Imprime la relación entre las filas del conjunto final y las de la optimización, las
#   iteraciones antes y después y el valor de min_sum_hessian_in_leaf.
#%% celda 17 [texto]
## 6. Modelo final y predicción para 202108
Se reentrena con los 4 meses etiquetados (202103–202106).

#%% celda 18 [código]
df_final = submuestrear(df[df['foto_mes'].isin(FINAL_MESES)], FRAC_NEGATIVOS, SEED)
dfinal = lgb.Dataset(df_final[features], label=df_final['clase_binaria'], params=DS_PARAMS)
df_target = df[df['foto_mes'] == MES_TARGET].copy()
ids_target = df_target['numero_de_cliente'].values.astype('int64')

# el final usa más datos que la optimización: se ajustan las iteraciones
ratio_datos = len(df_final) / n_train_opt
best_params_final = dict(best_params)
n_rounds = int(best_iter * FACTOR_ITER_FINAL)
print(f'filas final / filas optimización = {ratio_datos:.2f} | iteraciones: {best_iter} -> {n_rounds} | '
      f'min_sum_hessian: {best_params["min_sum_hessian_in_leaf"]:.2e} -> {best_params_final["min_sum_hessian_in_leaf"]:.2e}')

# [Anotación · líneas 259–274] Descomprime todos los .zip de ./modelos/ en esa misma carpeta. Para cada una de
#   las 18 semillas (236983 + s): si existe ./modelos/lgb_seed<semilla>.txt carga ese modelo; si no, entrena
#   LightGBM con best_params_final y esa semilla sobre el Dataset final. Con cada modelo predice las filas de
#   202108, corrige la probabilidad con corregir_prob (fracción 0,1) y guarda una predicción por semilla.
# for unziping
import glob, zipfile
for zip_path in glob.glob('./modelos/*.zip'):
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall('./modelos/')

preds_target = []  # una predicción por seed (prob. corregida por el submuestreo)
modelos = []
for s in range(N_SEEDS_SUBMIT):
    if os.path.exists(f'./modelos/lgb_seed{SEED + s}.txt'):
      m = lgb.Booster(model_file=f'./modelos/lgb_seed{SEED + s}.txt')
    else:
      m = lgb.train({**best_params_final, 'seed': SEED + s}, dfinal, num_boost_round=n_rounds)
    modelos.append(m)
    preds_target.append(corregir_prob(m.predict(df_target[features]), FRAC_NEGATIVOS))
    print(f'seed {s+1}/{N_SEEDS_SUBMIT} lista')

# [Anotación · líneas 276–295] generar_submit crea una carpeta con el nombre tag y se detiene con
#   FileExistsError si ya existe. Por cada predicción de la lista ordena los clientes de mayor a menor
#   probabilidad, cuenta cuántos superan el umbral (por defecto 27.500 / 1.100.000 = 0,025), acota esa cantidad
#   entre env_min y env_max, verifica que no haya ids repetidos y escribe los ids elegidos en <tag>_s<NN>.csv,
#   sin encabezado ni índice. Al final comprime la carpeta en un .zip e imprime las rutas.
#%% celda 19 [código]
def generar_submit(tag, preds_list, ids, umbral=COSTO_ENVIO / GANANCIA_ACIERTO, env_min=0, env_max=15000):
    """Un .csv por modelo: sin encabezado, ids enteros (nunca notación científica),
    con los clientes de prob > umbral, acotado a [env_min, env_max]."""
    carpeta = tag
    if os.path.exists(carpeta):
        raise FileExistsError(f'{carpeta} ya existe.')
    os.makedirs(carpeta)

    for s, p in enumerate(preds_list):
        orden = np.argsort(-p, kind='stable')
        n_umbral = int((p > umbral).sum())
        n = min(max(n_umbral, env_min), env_max)
        aviso = '' if n == n_umbral else f'  (recortado: el umbral daba {n_umbral})'
        sel = ids[orden[:n]]
        assert len(np.unique(sel)) == len(sel), 'ids repetidos'
        pd.Series(sel, dtype='int64').to_csv(os.path.join(carpeta, f'{tag}_s{s:02d}.csv'), header=False, index=False)
        print(f'{tag}_s{s:02d}.csv: {n} clientes{aviso}')
    zip_path = shutil.make_archive(tag, 'zip', carpeta)
    print(f'\nCarpeta: {carpeta}\nZip:     {zip_path}')

# [Anotación · líneas 297–297] Llama a generar_submit con una sola predicción, el promedio por cliente de las
#   18 (np.mean), y env_min = env_max = 11000, de modo que el archivo contiene los 11.000 clientes de mayor
#   probabilidad promedio. El tag es OUTPUT_PATH + 'final_submit', que con OUTPUT_PATH = './output' resulta
#   './outputfinal_submit'.
generar_submit(OUTPUT_PATH + 'final_submit', [np.mean(preds_target, axis=0)], ids_target, env_min= 11000, env_max= 11000)
```

