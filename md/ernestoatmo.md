# Ernesto Petino Zappala — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: ernestoatmo
- Repositorio: https://github.com/ernestoatmo/prediccion_final_competencia1
- Link posteado: https://github.com/ernestoatmo/prediccion_final_competencia1
- Commit: 8a80be50e5b928cf215288254dd713fb1c417853
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/ernestoatmo/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/ernestoatmo.json

## Resumen

La entrega contiene dos notebooks de Python preparados para Google Colab y un README. 01_optimizacion_bayesiana.ipynb arma una clase binaria (BAJA = BAJA+1 o BAJA+2), aplica a todas las variables un rank por mes con cero fijo, agrega lag 1, lag 2 y sus deltas, entrena LightGBM con 202103 y 202104 y busca con Optuna (sampler TPE, 20 trials) tres hiperparámetros maximizando el AUC en 202106. 02_corrida_ensamble.ipynb, que según el README es el que replica el archivo entregado, repite la misma preparación sobre todos los meses del dataset (con ccajas_depositos en NaN para 202105), entrena 20 modelos LightGBM con 202103 a 202106 cambiando sólo la semilla, con n_estimators 1250, num_leaves 700 y min_sum_hessian_in_leaf 0.003 (según el README, redondeo manual del resultado de la búsqueda), promedia las probabilidades sobre 202108 y escribe archivos CSV con los clientes de mayor probabilidad para varios cortes. Según el README, el archivo entregado es prediccion_202108_corte_12000.csv.

**Qué entrega.** Según el README, el archivo prediccion_202108_corte_12000.csv: un CSV con una sola columna, numero_de_cliente, con los 12.000 clientes de 202108 de mayor probabilidad promedio del ensamble. El notebook 02 escribe además los cortes de 10000, 10500, 11000 y 11500 y otros 17 archivos con cortes de 10000 a 12000 cada 125. El repositorio no incluye ninguno de esos archivos.

**Cómo se ejecuta.** Según el README, los dos notebooks se ejecutan de forma secuencial en Google Colab y descargan competencia_01_crudo.csv si no está en el entorno. El paso 1 (01_optimizacion_bayesiana.ipynb) figura como opcional para la replicación; para replicar el archivo entregado el README indica ejecutar directamente 02_corrida_ensamble.ipynb.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria. Positivo (BAJA, target = 1) cuando el cliente no tiene fila en el mes siguiente (BAJA+1) o la tiene en el mes siguiente pero no dos meses después (BAJA+2). Las demás filas de meses anteriores al anteúltimo del dataset son CONTINUA (target = 0).
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código: se usan todas las filas de los meses de entrenamiento.
- **Calidad de datos:** En 02_corrida_ensamble.ipynb se asigna NaN a ccajas_depositos en las filas de 202105 (línea 86). En 01_optimizacion_bayesiana.ipynb esa asignación no está.
- **Drifting:** Rank con cero fijo por mes sobre todas las variables originales: dentro de cada foto_mes, los valores positivos se reemplazan por su rank denso reescalado a [0.001, 1.0] y los negativos por su rank denso reescalado a [-1.0, -0.001]; los ceros y los NaN no se modifican. Se aplica antes de calcular lags y deltas.
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** Para cada variable original ya rankeada: _LAG1 y _LAG2 (valor del mismo cliente 1 y 2 meses atrás, en NaN si la fila anterior no está exactamente a esa distancia) y _DELTA-LAG1 y _DELTA-LAG2 (valor actual menos cada lag). Según la salida guardada en el notebook 01, las matrices quedan con 760 columnas.
- **Selección de variables:** No se observa en el código: se usan todas las columnas salvo numero_de_cliente, foto_mes, clase_binaria y target.
- **Optimización de hiperparámetros:** Optuna con sampler TPE (10 trials iniciales, seed 331613) y 20 trials, maximizando el AUC en 202106 de un LightGBM entrenado con 202103 y 202104. Se buscan n_estimators (64 a 4096), num_leaves (16 a 2048) y min_sum_hessian_in_leaf (1e-06 a 0.1), los tres en escala logarítmica; los demás parámetros quedan fijos. Según el README, el resultado fue n_estimators 1273, num_leaves 721 y min_sum_hessian_in_leaf 0.003055877921643489.
- **Hiperparámetros finales:** n_estimators 1250, num_leaves 700 y min_sum_hessian_in_leaf 0.003 (según el README, redondeo manual de los valores de la búsqueda); learning_rate 0.005, min_child_samples 0, colsample_bytree 0.50, max_depth -1, min_split_gain 0.0, reg_alpha 0.0, reg_lambda 0.0, max_bin 31, subsample 1.0, is_unbalance False, scale_pos_weight 1.0, extra_trees False, boosting_type gbdt, objective binary, feature_pre_filter False, deterministic True.
- **Semillas:** 20 semillas generadas con np.random.seed(331613) y np.random.randint(10000, 999999, size=20); cada una se usa como random_state de un LGBMClassifier. Según la salida guardada en el notebook 02, son 208426, 639613, 787255, 597221, 758579, 401645, 708272, 661056, 902817, 173416, 521898, 514154, 404227, 664050, 461070, 485685, 812553, 580064, 874841 y 50059. En la búsqueda del notebook 01 se usa 331613 como random_state del modelo y como seed del sampler.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio de las probabilidades de la clase 1 de 20 modelos LightGBM entrenados con los mismos datos e hiperparámetros, que difieren sólo en random_state.
- **Corte:** Cantidad fija de clientes: se ordena por probabilidad promedio descendente y se toman los primeros N. El código escribe los cortes 10000, 10500, 11000, 11500 y 12000 y, en una segunda celda, 17 cortes de 10000 a 12000 cada 125. Según el README, el archivo elegido es el de 12000.
- **Validación:** En el notebook 01: entrenamiento con 202103 y 202104 y medición del AUC (roc_auc_score) en 202106, usada para elegir hiperparámetros. En el notebook 02 no hay medición: se entrena con 202103 a 202106 y se predice 202108. No se calcula la ganancia de la competencia en ninguno de los dos.
- **Salidas:** En el directorio de trabajo: prediccion_202108_corte_<N>.csv para N en 10000, 10500, 11000, 11500 y 12000, y prediccion_202108_2_corte_<N>.csv para N de 10000 a 12000 cada 125. Cada archivo tiene una sola columna, numero_de_cliente (escrita como texto), con encabezado y sin índice.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: sí
- Entorno declarado: Google Colab, según el README. Los metadatos del notebook 02 indican machine_shape "hm". No se declaran versiones de Python, pandas, numpy ni lightgbm; optuna se instala con pip sin versión fijada, y la salida guardada de esa celda en el notebook 01 muestra optuna 5.0.0 y rutas de Python 3.13.

## Pasos del camino de la entrega

1. **Entorno de Colab y descarga del dataset.** Los dos notebooks montan Google Drive en /content/.drive, crean /content/buckets/b1 y /content/datasets y descargan competencia_01_crudo.csv desde storage.googleapis.com/open-courses/dmeyf2026-9c6f si no está presente; el dataset se lee desde /content/datasets. El notebook 01 lo hace con una celda de bash y wget; el 02, con os, urllib y shutil. (`01_optimizacion_bayesiana.ipynb` líneas 1–28; `02_corrida_ensamble.ipynb` líneas 28–53)
2. **Clase binaria para la búsqueda (notebook 01).** Calcula un período continuo (año × 12 + mes) y, por cliente, el período de las dos filas siguientes. Marca BAJA cuando el cliente no figura en el período siguiente o figura en el siguiente pero no dos períodos después, y CONTINUA en el resto de las filas anteriores al anteúltimo período. Elimina las filas que quedan sin clase y crea target (1 = BAJA, 0 = resto). (`01_optimizacion_bayesiana.ipynb` líneas 95–125)
3. **Rank con cero fijo por mes (notebook 01).** Todas las columnas salvo numero_de_cliente, foto_mes, clase_binaria y target se transforman dentro de cada foto_mes: los positivos pasan a su rank denso reescalado a [0.001, 1.0], los negativos a [-1.0, -0.001], y los ceros y NaN quedan igual. (`01_optimizacion_bayesiana.ipynb` líneas 45–91; `01_optimizacion_bayesiana.ipynb` líneas 130–134)
4. **Lags y deltas de orden 1 y 2 (notebook 01).** Sobre las variables ya rankeadas genera, por cliente, el valor de 1 y 2 meses atrás (_LAG1, _LAG2), puesto en NaN si la fila desplazada no está exactamente a 1 o 2 períodos, y la diferencia del valor actual con cada lag (_DELTA-LAG1, _DELTA-LAG2). Según la salida guardada en el notebook, resultan 760 columnas de variables. (`01_optimizacion_bayesiana.ipynb` líneas 139–169)
5. **Partición temporal para medir (notebook 01).** Entrenamiento con las filas de 202103 y 202104; medición con las filas de 202106. Según la salida guardada, 326.184 filas de entrenamiento y 164.114 de prueba. (`01_optimizacion_bayesiana.ipynb` líneas 173–181)
6. **Búsqueda de hiperparámetros con Optuna (notebook 01).** Estudio de Optuna con sampler TPE (10 trials iniciales, seed 331613) y 20 trials. Cada trial entrena un LGBMClassifier con n_estimators (64 a 4096), num_leaves (16 a 2048) y min_sum_hessian_in_leaf (1e-06 a 0.1) propuestos en escala logarítmica y el resto de los parámetros fijos (learning_rate 0.005, colsample_bytree 0.50, max_bin 31, min_child_samples 0, random_state 331613), y devuelve el AUC en 202106. Según el README y la salida guardada, el trial de mayor AUC (0.9144 según la salida) tiene n_estimators 1273, num_leaves 721 y min_sum_hessian_in_leaf 0.003055877921643489. (`01_optimizacion_bayesiana.ipynb` líneas 186–244)
7. **Carga, reducción de memoria y ccajas_depositos en NaN (notebook 02).** Lee el CSV, convierte cada columna numérica al tipo entero o flotante de menor tamaño con reducir_memoria y asigna NaN a ccajas_depositos en las filas de 202105. (`02_corrida_ensamble.ipynb` líneas 15–23; `02_corrida_ensamble.ipynb` líneas 82–86)
8. **Clase binaria conservando las filas sin clase (notebook 02).** Arma la clase con la misma lógica que el notebook 01 (BAJA = BAJA+1 o BAJA+2). El target vale 1 para BAJA, 0 para CONTINUA y NaN para las filas sin clase; esas filas no se eliminan, de modo que 202108 sigue en el dataset. (`02_corrida_ensamble.ipynb` líneas 88–105)
9. **Rank con cero fijo, lags y deltas sobre todos los meses (notebook 02).** Aplica el rank con cero fijo por foto_mes a todas las variables originales y luego genera _LAG1, _LAG2, _DELTA-LAG1 y _DELTA-LAG2 por cliente, con el mismo control de distancia exacta entre períodos; las columnas nuevas se guardan en float32. (`02_corrida_ensamble.ipynb` líneas 58–77; `02_corrida_ensamble.ipynb` líneas 111–137)
10. **Conjuntos de entrenamiento y de predicción (notebook 02).** Entrenamiento: filas de 202103, 202104, 202105 y 202106 con target no nulo. Predicción: filas de 202108, de las que se guarda numero_de_cliente. Después se borra el DataFrame completo de memoria. (`02_corrida_ensamble.ipynb` líneas 143–154)
11. **Semillas e hiperparámetros del ensamble (notebook 02).** Genera 20 semillas con np.random.seed(331613) y np.random.randint(10000, 999999, size=20) y define el diccionario de parámetros de LightGBM con n_estimators 1250, num_leaves 700, min_sum_hessian_in_leaf 0.003 y los mismos valores fijos que la búsqueda (learning_rate 0.005, colsample_bytree 0.50, max_bin 31, min_child_samples 0, entre otros). (`02_corrida_ensamble.ipynb` líneas 159–185)
12. **Entrenamiento de 20 modelos y promedio (notebook 02).** Para cada semilla entrena un LGBMClassifier con el conjunto de entrenamiento y acumula la probabilidad de la clase 1 predicha para 202108; al terminar divide el acumulado por 20. (`02_corrida_ensamble.ipynb` líneas 187–199)
13. **Archivos de salida por corte (notebook 02).** Ordena los clientes de 202108 por probabilidad promedio descendente y escribe, para cada corte de 10000, 10500, 11000, 11500 y 12000, un CSV prediccion_202108_corte_<corte>.csv con la columna numero_de_cliente (como texto) de las primeras filas. Según el README, el de 12000 es el archivo entregado. (`02_corrida_ensamble.ipynb` líneas 204–218)
14. **Cortes adicionales cada 125 (notebook 02).** Una segunda celda reutiliza df_resultados en memoria y escribe 17 archivos prediccion_202108_2_corte_<corte>.csv con cortes de 10000 a 12000 cada 125, con el mismo formato. (`02_corrida_ensamble.ipynb` líneas 221–241)

## Archivos

- `01_optimizacion_bayesiana.ipynb` · principal · Jupyter (python) · 244 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ernestoatmo/01_optimizacion_bayesiana.ipynb.txt) — Notebook de búsqueda de hiperparámetros: prepara el dataset (clase binaria, rank con cero fijo, lags y deltas), entrena LightGBM con 202103 y 202104 y ejecuta 20 trials de Optuna maximizando el AUC en 202106. Según el README, de su resultado salen, redondeados a mano, los hiperparámetros del notebook 02.
- `02_corrida_ensamble.ipynb` · principal · Jupyter (python) · 241 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ernestoatmo/02_corrida_ensamble.ipynb.txt) — Notebook que, según el README, replica el archivo entregado: prepara el dataset (clase binaria, rank con cero fijo, lags y deltas), entrena 20 modelos LightGBM con 202103 a 202106 variando la semilla, promedia las probabilidades sobre 202108 y escribe los CSV con distintos cortes.
- `README.md` · explicacion · Markdown · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ernestoatmo/README.md.txt) — Presenta la entrega como un ensamble de 20 modelos LightGBM con hiperparámetros hallados con Optuna, describe los dos notebooks, indica cómo replicar en Google Colab, lista los hiperparámetros que devolvió la búsqueda (1273, 721, 0.003055877921643489) y los que se usan en el ensamble tras un redondeo manual (1250, 700, 0.003), y señala prediccion_202108_corte_12000.csv como el archivo entregado. Sobre la elección del corte de 12000, dice que se basó en "la estabilidad histórica del leaderboard".

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### 01_optimizacion_bayesiana.ipynb

Notebook de búsqueda de hiperparámetros: prepara el dataset (clase binaria, rank con cero fijo, lags y deltas), entrena LightGBM con 202103 y 202104 y ejecuta 20 trials de Optuna maximizando el AUC en 202106. Según el README, de su resultado salen, redondeados a mano, los hiperparámetros del notebook 02.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–4] Monta Google Drive en /content/.drive con google.colab.drive.
#%% celda 1 [código]
# Montaje del Drive
from google.colab import drive
drive.mount('/content/.drive')

# [Anotación · líneas 6–28] Celda de bash: crea la carpeta dmeyf en el Drive y /content/buckets, enlaza
#   /content/buckets/b1 a esa carpeta del Drive y crea las subcarpetas exp y datasets y la carpeta
#   /content/datasets. Si competencia_01_crudo.csv no está en /content/buckets/b1/datasets lo descarga con wget
#   desde storage.googleapis.com/open-courses/dmeyf2026-9c6f, y si no está en /content/datasets lo copia allí.
#%% celda 2 [código]
%%bash
# Replicación de la estructura de carpetas
mkdir -p "/content/.drive/My Drive/dmeyf"
mkdir -p "/content/buckets"
ln -sfn "/content/.drive/My Drive/dmeyf" /content/buckets/b1

mkdir -p /content/buckets/b1/exp
mkdir -p /content/buckets/b1/datasets
mkdir -p /content/datasets

# Descarga condicional del crudo
FILE_DRIVE="/content/buckets/b1/datasets/competencia_01_crudo.csv"
FILE_LOCAL="/content/datasets/competencia_01_crudo.csv"
URL="https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"

if [ ! -f "$FILE_DRIVE" ]; then
  wget "$URL" -O "$FILE_DRIVE"
fi

if [ ! -f "$FILE_LOCAL" ]; then
  cp "$FILE_DRIVE" "$FILE_LOCAL"
fi

# [Anotación · líneas 30–40] Instala optuna con pip, sin versión fijada, e importa pandas, numpy, optuna,
#   LGBMClassifier de lightgbm y roc_auc_score de scikit-learn; desactiva los warnings.
#%% celda 3 [código]
!pip install optuna

#%% celda 4 [código]
import pandas as pd
import numpy as np
import optuna
from lightgbm import LGBMClassifier
from sklearn.metrics import roc_auc_score
import warnings
warnings.filterwarnings("ignore")

# [Anotación · líneas 42–91] Define aplicar_rank_cero_fijo(df, columnas_a_rankear), que trabaja sobre una
#   copia del DataFrame. Para cada columna separa los valores positivos y los negativos y, dentro de cada
#   foto_mes, reemplaza cada valor por su rank denso reescalado linealmente: los positivos al intervalo [0.001,
#   1.0] y los negativos a [-1.0, -0.001]. Los ceros y los NaN no se tocan. Si en un mes hay un único valor
#   distinto, el grupo recibe el extremo superior del intervalo (1.0 en positivos, -0.001 en negativos).
# =============================================================================
# 1. FUNCIÓN: RANKING CON CERO FIJO Y ESCALADO SIMÉTRICO
# =============================================================================
def aplicar_rank_cero_fijo(df, columnas_a_rankear):
    """
    Convierte variables numéricas a pseudo-percentiles por 'foto_mes' manteniendo el 0:
    - Positivos: Escalados proporcionalmente entre 0.001 y 1.0.
    - Negativos: Escalados proporcionalmente entre -1.0 y -0.001.
    - Ceros y NaNs: Se mantienen intactos.
    """
    df_out = df.copy()

    def escalar_rangos(s, val_min, val_max):
        if s.empty:
            return s

        # rank(method='dense') asigna rangos enteros consecutivos
        r = s.rank(method='dense')
        r_min, r_max = r.min(), r.max()

        # Si hay un único valor en la distribución del mes, se le asigna el máximo (en magnitud)
        if r_min == r_max:
            return pd.Series(val_max, index=s.index)

        # Escalado Min-Max a un rango [0, 1] y luego proyección al intervalo [val_min, val_max]
        p = (r - r_min) / (r_max - r_min)
        return val_min + p * (val_max - val_min)

    for col in columnas_a_rankear:
        # Máscaras booleanas (los NaN evalúan como False en ambas comparaciones)
        mask_pos = df_out[col] > 0
        mask_neg = df_out[col] < 0

        # Aplicar escalado a los positivos agrupados por foto_mes
        if mask_pos.any():
            df_out.loc[mask_pos, col] = (
                df_out.loc[mask_pos]
                .groupby('foto_mes')[col]
                .transform(lambda x: escalar_rangos(x, 0.001, 1.0))
            )

        # Aplicar escalado a los negativos agrupados por foto_mes
        if mask_neg.any():
            df_out.loc[mask_neg, col] = (
                df_out.loc[mask_neg]
                .groupby('foto_mes')[col]
                .transform(lambda x: escalar_rangos(x, -1.0, -0.001))
            )

    return df_out
# [Anotación · líneas 92–125] Lee /content/datasets/competencia_01_crudo.csv con pandas. Calcula periodo0 =
#   año × 12 + mes, ordena por cliente y período y obtiene con shift(-1) y shift(-2) el período de las dos filas
#   siguientes del mismo cliente. Asigna CONTINUA a las filas de períodos anteriores al anteúltimo, y BAJA si el
#   cliente no tiene fila en el período siguiente (filas anteriores al último período) o si la tiene en el
#   siguiente pero no dos períodos después (filas anteriores al anteúltimo). Elimina las columnas auxiliares y
#   las filas que quedaron sin clase, y crea target = 1 para BAJA y 0 para el resto.
# =============================================================================
# 2. CARGA Y CREACIÓN DE LA CLASE BINARIA
# =============================================================================
print("Cargando dataset...")
dataset = pd.read_csv("/content/datasets/competencia_01_crudo.csv")

# Cálculo de meses consecutivos para ubicar bajas
dataset['periodo0'] = (dataset['foto_mes'] // 100) * 12 + (dataset['foto_mes'] % 100)
dataset.sort_values(['numero_de_cliente', 'periodo0'], inplace=True)

# Leads para mirar hacia el futuro
dataset['periodo1'] = dataset.groupby('numero_de_cliente')['periodo0'].shift(-1)
dataset['periodo2'] = dataset.groupby('numero_de_cliente')['periodo0'].shift(-2)

periodo_ultimo = dataset['periodo0'].max()
periodo_anteultimo = periodo_ultimo - 1

dataset['clase_binaria'] = np.nan
dataset.loc[dataset['periodo0'] < periodo_anteultimo, 'clase_binaria'] = 'CONTINUA'

# Lógica BAJA (Agrupa BAJA+1 y BAJA+2 en una sola etiqueta)
mask_baja1 = (dataset['periodo0'] < periodo_ultimo) & \
             (dataset['periodo1'].isna() | (dataset['periodo0'] + 1 < dataset['periodo1']))

mask_baja2 = (dataset['periodo0'] < periodo_anteultimo) & \
             (dataset['periodo0'] + 1 == dataset['periodo1']) & \
             (dataset['periodo2'].isna() | (dataset['periodo0'] + 2 < dataset['periodo2']))

dataset.loc[mask_baja1 | mask_baja2, 'clase_binaria'] = 'BAJA'

# Limpieza y Target numérico
dataset.drop(columns=['periodo0', 'periodo1', 'periodo2'], inplace=True)
dataset.dropna(subset=['clase_binaria'], inplace=True) # Excluye meses 202107/08 sin clase
dataset['target'] = np.where(dataset['clase_binaria'] == 'BAJA', 1, 0)

# [Anotación · líneas 127–134] Arma features_base con todas las columnas menos numero_de_cliente, foto_mes,
#   clase_binaria y target, y les aplica aplicar_rank_cero_fijo.
# =============================================================================
# 3. APLICACIÓN DE RANKING (Previo a la creación de deltas/lags)
# =============================================================================
print("Aplicando Ranking Cero Fijo a las variables base...")
features_base = [c for c in dataset.columns if c not in ['numero_de_cliente', 'foto_mes', 'clase_binaria', 'target']]

# Se rankean primero las variables originales
dataset = aplicar_rank_cero_fijo(dataset, features_base)

# [Anotación · líneas 136–169] Ordena por cliente y foto_mes y crea periodo_temp (año × 12 + mes). Para cada
#   variable de features_base genera <variable>_LAG1 y <variable>_LAG2 con shift(1) y shift(2) por cliente, y
#   pone NaN en el lag cuando la fila desplazada no está exactamente a 1 o 2 períodos de distancia. Genera
#   <variable>_DELTA-LAG1 y <variable>_DELTA-LAG2 como valor actual menos cada lag. Elimina periodo_temp y
#   define features_totales con las variables originales más las cuatro derivadas de cada una.
# =============================================================================
# 4. FEATURE ENGINEERING: LAGS Y DELTAS (Sobre variables rankeadas)
# =============================================================================
print("Calculando Lags y Deltas...")
# Garantizar el orden estrictamente temporal
dataset.sort_values(['numero_de_cliente', 'foto_mes'], inplace=True)

# Recreamos un período continuo para validar distancias exactas de meses
dataset['periodo_temp'] = (dataset['foto_mes'] // 100) * 12 + (dataset['foto_mes'] % 100)

for col in features_base:
    # Lags crudos usando el desplazamiento de filas por cliente
    dataset[f'{col}_LAG1'] = dataset.groupby('numero_de_cliente')[col].shift(1)
    dataset[f'{col}_LAG2'] = dataset.groupby('numero_de_cliente')[col].shift(2)

    # Desplazamiento del período para verificar la temporalidad estricta
    periodo_lag1 = dataset.groupby('numero_de_cliente')['periodo_temp'].shift(1)
    periodo_lag2 = dataset.groupby('numero_de_cliente')['periodo_temp'].shift(2)

    # Si la fila anterior no es exactamente el mes pasado (diferencia != 1), forzar NaN
    dataset.loc[dataset['periodo_temp'] - periodo_lag1 != 1, f'{col}_LAG1'] = np.nan

    # Si dos filas atrás no son exactamente hace dos meses (diferencia != 2), forzar NaN
    dataset.loc[dataset['periodo_temp'] - periodo_lag2 != 2, f'{col}_LAG2'] = np.nan

    # Deltas: Si alguno de los componentes es NaN, pandas devuelve NaN automáticamente
    dataset[f'{col}_DELTA-LAG1'] = dataset[col] - dataset[f'{col}_LAG1']
    dataset[f'{col}_DELTA-LAG2'] = dataset[col] - dataset[f'{col}_LAG2']

# Limpieza de la columna temporal de soporte
dataset.drop(columns=['periodo_temp'], inplace=True)

# Actualizamos las features_totales para incluir las 4 nuevas variables por columna
features_totales = [c for c in dataset.columns if c not in ['numero_de_cliente', 'foto_mes', 'clase_binaria', 'target']]
# [Anotación · líneas 170–181] Separa por mes: X_train e y_train con las filas de 202103 y 202104; X_test e
#   y_test con las de 202106. Imprime las dimensiones de las dos matrices.
# =============================================================================
# 5. SPLIT TEMPORAL (Train: 202103/04 - Test: 202106)
# =============================================================================
train_mask = dataset['foto_mes'].isin([202103, 202104])
X_train = dataset.loc[train_mask, features_totales]
y_train = dataset.loc[train_mask, 'target']

test_mask = dataset['foto_mes'] == 202106
X_test = dataset.loc[test_mask, features_totales]
y_test = dataset.loc[test_mask, 'target']

print(f"Dimensiones Train: {X_train.shape} | Dimensiones Test: {X_test.shape}")

# [Anotación · líneas 183–226] Define la función objetivo de Optuna. En cada trial propone n_estimators entre
#   64 y 4096, num_leaves entre 16 y 2048 y min_sum_hessian_in_leaf entre 1e-06 y 0.1, los tres en escala
#   logarítmica; el resto queda fijo: learning_rate 0.005, min_child_samples 0, colsample_bytree 0.50, max_depth
#   -1, min_split_gain 0.0, reg_alpha 0.0, reg_lambda 0.0, max_bin 31, subsample 1.0, is_unbalance False,
#   scale_pos_weight 1.0, extra_trees False, boosting_type gbdt, objective binary, feature_pre_filter False,
#   deterministic True, random_state 331613. Entrena un LGBMClassifier con X_train, predice la probabilidad de
#   la clase 1 en X_test (202106) y devuelve el AUC.
# =============================================================================
# 6. OPTIMIZACIÓN BAYESIANA CON OPTUNA (Algoritmo TPE para LightGBM)
# =============================================================================
def objective(trial):
    # Espacio de búsqueda de hiperparámetros (LightGBM)
    params = {
        # --- 1. Hiperparámetros a optimizar (Búsqueda Logarítmica) ---
        'n_estimators': trial.suggest_int('n_estimators', 64, 4096, log=True),
        'num_leaves': trial.suggest_int('num_leaves', 16, 2048, log=True),
        'min_sum_hessian_in_leaf': trial.suggest_float('min_sum_hessian_in_leaf', 1e-06, 0.1, log=True),

        # --- 2. Parámetros fijos ---
        'learning_rate': 0.005,
        'min_child_samples': 0,        # Equivale a min_data_in_leaf (CERO fijo)
        'colsample_bytree': 0.50,      # Equivale a feature_fraction
        'max_depth': -1,
        'min_split_gain': 0.0,         # Equivale a min_gain_to_split
        'reg_alpha': 0.0,              # Equivale a lambda_l1
        'reg_lambda': 0.0,             # Equivale a lambda_l2
        'max_bin': 31,
        'subsample': 1.0,              # Equivale a bagging_fraction
        'is_unbalance': False,
        'scale_pos_weight': 1.0,
        'extra_trees': False,
        'boosting_type': 'gbdt',
        'objective': 'binary',
        'feature_pre_filter': False,
        'deterministic': True,
        'verbosity': -100,
        'random_state': 331613,        # Semilla actualizada
        'n_jobs': -1
    }

    # Instanciamos LightGBM
    clf = LGBMClassifier(**params)
    clf.fit(X_train, y_train)

    # Predecir probabilidades de BAJA (clase 1) en el mes de validación
    y_pred_proba = clf.predict_proba(X_test)[:, 1]

    # Métrica a maximizar: Área bajo la curva ROC
    auc = roc_auc_score(y_test, y_pred_proba)

    return auc

# [Anotación · líneas 228–244] Crea un sampler TPE con 10 trials iniciales y seed 331613 y un estudio llamado
#   HT_LightGBM_Optuna con dirección maximize; ejecuta 20 trials e imprime el AUC más alto y los hiperparámetros
#   del trial que lo obtuvo.
print("Iniciando búsqueda bayesiana de hiperparámetros...")

# Implementación del sampler TPE configurado con 10 trials de startup y la nueva semilla
sampler = optuna.samplers.TPESampler(n_startup_trials=10, seed=331613)

study = optuna.create_study(
    direction='maximize',
    study_name="HT_LightGBM_Optuna",
    sampler=sampler
)
study.optimize(objective, n_trials=20)

print("\n================ RESULTADOS ================")
print(f"Mejor AUC: {study.best_value}")
print("Mejores hiperparámetros identificados:")
for k, v in study.best_params.items():
    print(f"  {k}: {v}")
```

### 02_corrida_ensamble.ipynb

Notebook que, según el README, replica el archivo entregado: prepara el dataset (clase binaria, rank con cero fijo, lags y deltas), entrena 20 modelos LightGBM con 202103 a 202106 variando la semilla, promedia las probabilidades sobre 202108 y escribe los CSV con distintos cortes.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–10] Importa os, shutil, urllib.request, pandas, numpy, LGBMClassifier de lightgbm y
#   gc, y desactiva los warnings.
#%% celda 1 [código]
import os
import shutil
import urllib.request
import pandas as pd
import numpy as np
from lightgbm import LGBMClassifier
import gc
import warnings
warnings.filterwarnings("ignore")

# [Anotación · líneas 12–23] Define reducir_memoria(df): recorre las columnas que no son de tipo object y las
#   convierte con pd.to_numeric al tipo entero o flotante de menor tamaño que admite sus valores (downcast).
# =============================================================================
# 0. FUNCIONES DE OPTIMIZACIÓN DE MEMORIA
# =============================================================================
def reducir_memoria(df):
    for col in df.columns:
        col_type = df[col].dtype
        if col_type != object:
            if str(col_type)[:3] == 'int':
                df[col] = pd.to_numeric(df[col], downcast='integer')
            else:
                df[col] = pd.to_numeric(df[col], downcast='float')
    return df

# [Anotación · líneas 25–53] Si google.colab está disponible y /content/.drive no existe, monta Google Drive.
#   Crea la carpeta dmeyf del Drive, /content/buckets/b1/datasets y /content/datasets; a continuación, sólo si
#   /content/buckets/b1 no existe, crea un enlace simbólico de esa ruta a la carpeta dmeyf del Drive. Descarga
#   competencia_01_crudo.csv con urllib si no está en /content/buckets/b1/datasets y lo copia a
#   /content/datasets si no está allí.
# =============================================================================
# 1. MONTAJE DE DRIVE Y DESCARGA CONDICIONAL
# =============================================================================
try:
    from google.colab import drive
    if not os.path.exists('/content/.drive'):
        drive.mount('/content/.drive')
except ImportError:
    pass

os.makedirs("/content/.drive/My Drive/dmeyf", exist_ok=True)
os.makedirs("/content/buckets/b1/datasets", exist_ok=True)
os.makedirs("/content/datasets", exist_ok=True)

if not os.path.exists("/content/buckets/b1"):
    try:
        os.symlink("/content/.drive/My Drive/dmeyf", "/content/buckets/b1")
    except:
        pass

file_drive = "/content/buckets/b1/datasets/competencia_01_crudo.csv"
file_local = "/content/datasets/competencia_01_crudo.csv"
url = "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"

if not os.path.isfile(file_drive):
    urllib.request.urlretrieve(url, file_drive)

if not os.path.isfile(file_local):
    shutil.copy(file_drive, file_local)

# [Anotación · líneas 55–77] Define aplicar_rank_cero_fijo_inplace(df, columnas_a_rankear): la misma
#   transformación que el notebook 01 (rank denso dentro de cada foto_mes, positivos reescalados a [0.001, 1.0],
#   negativos a [-1.0, -0.001], ceros y NaN sin cambios; un grupo con un único valor distinto recibe el extremo
#   superior del intervalo), escrita sobre el mismo DataFrame que recibe, sin copiarlo.
# =============================================================================
# 2. FUNCIÓN: RANKING CON CERO FIJO IN-PLACE
# =============================================================================
def aplicar_rank_cero_fijo_inplace(df, columnas_a_rankear):
    def escalar_rangos(s, val_min, val_max):
        if s.empty:
            return s
        r = s.rank(method='dense')
        r_min, r_max = r.min(), r.max()
        if r_min == r_max:
            return pd.Series(val_max, index=s.index)
        p = (r - r_min) / (r_max - r_min)
        return val_min + p * (val_max - val_min)

    for col in columnas_a_rankear:
        mask_pos = df[col] > 0
        mask_neg = df[col] < 0

        if mask_pos.any():
            df.loc[mask_pos, col] = df.loc[mask_pos].groupby('foto_mes')[col].transform(lambda x: escalar_rangos(x, 0.001, 1.0))
        if mask_neg.any():
            df.loc[mask_neg, col] = df.loc[mask_neg].groupby('foto_mes')[col].transform(lambda x: escalar_rangos(x, -1.0, -0.001))
    return df

# [Anotación · líneas 79–86] Lee /content/datasets/competencia_01_crudo.csv con pandas, le aplica
#   reducir_memoria y asigna NaN a ccajas_depositos en las filas de foto_mes 202105.
# =============================================================================
# 3. CARGA, COMPRESIÓN Y CREACIÓN DE LA CLASE BINARIA
# =============================================================================
print("Cargando dataset...")
dataset = pd.read_csv(file_local)
dataset = reducir_memoria(dataset)

dataset.loc[dataset['foto_mes'] == 202105, 'ccajas_depositos'] = np.nan

# [Anotación · líneas 88–106] Calcula periodo0 = año × 12 + mes, ordena por cliente y período y obtiene con
#   shift(-1) y shift(-2) el período de las dos filas siguientes del mismo cliente. Asigna CONTINUA a las filas
#   de períodos anteriores al anteúltimo, y BAJA si el cliente no tiene fila en el período siguiente (filas
#   anteriores al último período) o si la tiene en el siguiente pero no dos períodos después (filas anteriores
#   al anteúltimo). Crea target = 1 para BAJA, 0 para CONTINUA y NaN para las filas sin clase, que no se
#   eliminan. Borra las columnas auxiliares y llama al recolector de memoria.
dataset['periodo0'] = (dataset['foto_mes'] // 100) * 12 + (dataset['foto_mes'] % 100)
dataset.sort_values(['numero_de_cliente', 'periodo0'], inplace=True)

dataset['periodo1'] = dataset.groupby('numero_de_cliente')['periodo0'].shift(-1)
dataset['periodo2'] = dataset.groupby('numero_de_cliente')['periodo0'].shift(-2)

periodo_ultimo = dataset['periodo0'].max()
periodo_anteultimo = periodo_ultimo - 1

dataset['clase_binaria'] = np.nan
dataset.loc[dataset['periodo0'] < periodo_anteultimo, 'clase_binaria'] = 'CONTINUA'

mask_baja1 = (dataset['periodo0'] < periodo_ultimo) & (dataset['periodo1'].isna() | (dataset['periodo0'] + 1 < dataset['periodo1']))
mask_baja2 = (dataset['periodo0'] < periodo_anteultimo) & (dataset['periodo0'] + 1 == dataset['periodo1']) & (dataset['periodo2'].isna() | (dataset['periodo0'] + 2 < dataset['periodo2']))

dataset.loc[mask_baja1 | mask_baja2, 'clase_binaria'] = 'BAJA'
dataset['target'] = np.where(dataset['clase_binaria'] == 'BAJA', 1, np.where(dataset['clase_binaria'] == 'CONTINUA', 0, np.nan))
dataset.drop(columns=['periodo0', 'periodo1', 'periodo2'], inplace=True)
gc.collect()

# [Anotación · líneas 108–114] Arma features_base con todas las columnas menos numero_de_cliente, foto_mes,
#   clase_binaria y target, y les aplica el rank con cero fijo sobre todos los meses del dataset.
# =============================================================================
# 4. APLICACIÓN DE RANKING
# =============================================================================
print("Aplicando Ranking Cero Fijo...")
features_base = [c for c in dataset.columns if c not in ['numero_de_cliente', 'foto_mes', 'clase_binaria', 'target']]
dataset = aplicar_rank_cero_fijo_inplace(dataset, features_base)
gc.collect()

# [Anotación · líneas 116–138] Ordena por cliente y foto_mes y crea periodo_temp (año × 12 + mes). Para cada
#   variable de features_base genera <variable>_LAG1 y <variable>_LAG2 con shift(1) y shift(2) por cliente, en
#   float32, y los pone en NaN cuando la fila desplazada no está exactamente a 1 o 2 períodos. Genera
#   <variable>_DELTA-LAG1 y <variable>_DELTA-LAG2 como valor actual menos cada lag, en float32. Elimina
#   periodo_temp y define features_totales con las variables originales más las cuatro derivadas de cada una.
# =============================================================================
# 5. FEATURE ENGINEERING: LAGS Y DELTAS
# =============================================================================
print("Calculando Lags y Deltas...")
dataset.sort_values(['numero_de_cliente', 'foto_mes'], inplace=True)
dataset['periodo_temp'] = (dataset['foto_mes'] // 100) * 12 + (dataset['foto_mes'] % 100)

for col in features_base:
    dataset[f'{col}_LAG1'] = dataset.groupby('numero_de_cliente')[col].shift(1).astype('float32')
    dataset[f'{col}_LAG2'] = dataset.groupby('numero_de_cliente')[col].shift(2).astype('float32')

    periodo_lag1 = dataset.groupby('numero_de_cliente')['periodo_temp'].shift(1)
    periodo_lag2 = dataset.groupby('numero_de_cliente')['periodo_temp'].shift(2)

    dataset.loc[dataset['periodo_temp'] - periodo_lag1 != 1, f'{col}_LAG1'] = np.nan
    dataset.loc[dataset['periodo_temp'] - periodo_lag2 != 2, f'{col}_LAG2'] = np.nan

    dataset[f'{col}_DELTA-LAG1'] = (dataset[col] - dataset[f'{col}_LAG1']).astype('float32')
    dataset[f'{col}_DELTA-LAG2'] = (dataset[col] - dataset[f'{col}_LAG2']).astype('float32')

dataset.drop(columns=['periodo_temp'], inplace=True)
features_totales = [c for c in dataset.columns if c not in ['numero_de_cliente', 'foto_mes', 'clase_binaria', 'target']]
gc.collect()

# [Anotación · líneas 140–154] Define meses_train = [202103, 202104, 202105, 202106] y arma X_train e y_train
#   con las filas de esos meses que tienen target. Arma X_predict con las filas de 202108 y guarda sus
#   numero_de_cliente. Borra el DataFrame completo y libera memoria.
# =============================================================================
# 6. SPLIT PARA ENSAMBLE Y LIBERACIÓN DE MEMORIA
# =============================================================================
print("Preparando particiones...")
meses_train = [202103, 202104, 202105, 202106]
train_mask = dataset['foto_mes'].isin(meses_train) & dataset['target'].notna()
X_train = dataset.loc[train_mask, features_totales]
y_train = dataset.loc[train_mask, 'target']

predict_mask = dataset['foto_mes'] == 202108
X_predict = dataset.loc[predict_mask, features_totales]
clientes_predict = dataset.loc[predict_mask, 'numero_de_cliente'].values

del dataset
gc.collect()

# [Anotación · líneas 156–185] Fija n_semillas = 20, inicializa el generador de numpy con 331613 y sortea las
#   20 semillas con np.random.randint(10000, 999999, size=20). Define los parámetros de LightGBM: n_estimators
#   1250, num_leaves 700, min_sum_hessian_in_leaf 0.003, learning_rate 0.005, min_child_samples 0,
#   colsample_bytree 0.50, max_depth -1, min_split_gain 0.0, reg_alpha 0.0, reg_lambda 0.0, max_bin 31,
#   subsample 1.0, is_unbalance False, scale_pos_weight 1.0, extra_trees False, boosting_type gbdt, objective
#   binary, feature_pre_filter False, deterministic True, n_jobs -1.
# =============================================================================
# 7. ENTRENAMIENTO DEL ENSAMBLE (20 SEMILLAS)
# =============================================================================
n_semillas = 20
np.random.seed(331613)
semillas = np.random.randint(10000, 999999, size=n_semillas)

params = {
    'n_estimators': 1250,
    'num_leaves': 700,
    'min_sum_hessian_in_leaf': 0.003,
    'learning_rate': 0.005,
    'min_child_samples': 0,
    'colsample_bytree': 0.50,
    'max_depth': -1,
    'min_split_gain': 0.0,
    'reg_alpha': 0.0,
    'reg_lambda': 0.0,
    'max_bin': 31,
    'subsample': 1.0,
    'is_unbalance': False,
    'scale_pos_weight': 1.0,
    'extra_trees': False,
    'boosting_type': 'gbdt',
    'objective': 'binary',
    'feature_pre_filter': False,
    'deterministic': True,
    'verbosity': -100,
    'n_jobs': -1
}

# [Anotación · líneas 187–199] Para cada una de las 20 semillas: la asigna a random_state, entrena un
#   LGBMClassifier con X_train e y_train, suma a un acumulador la probabilidad de la clase 1 predicha para
#   X_predict y libera el modelo. Al final divide el acumulado por 20 para obtener la probabilidad promedio.
predicciones_acumuladas = np.zeros(len(X_predict))
print(f"Iniciando entrenamiento del ensamble de {n_semillas} modelos...")

for i, semilla in enumerate(semillas, 1):
    print(f"Entrenando modelo {i}/{n_semillas} con semilla: {semilla}...")
    params['random_state'] = int(semilla)
    clf = LGBMClassifier(**params)
    clf.fit(X_train, y_train)
    predicciones_acumuladas += clf.predict_proba(X_predict)[:, 1]
    del clf
    gc.collect()

probabilidades_ensamble = predicciones_acumuladas / n_semillas

# [Anotación · líneas 201–218] Arma df_resultados con numero_de_cliente (convertido a int64 y luego a texto) y
#   la probabilidad promedio, y lo ordena de mayor a menor probabilidad. Para cada corte de la lista [10000,
#   10500, 11000, 11500, 12000] escribe prediccion_202108_corte_<corte>.csv con la columna numero_de_cliente de
#   las primeras <corte> filas, sin índice.
# =============================================================================
# 8. GENERACIÓN DE ARCHIVOS CSV LIMPIOS
# =============================================================================
df_resultados = pd.DataFrame({
    'numero_de_cliente': clientes_predict.astype('int64').astype(str),
    'probabilidad': probabilidades_ensamble
})

df_resultados = df_resultados.sort_values(by='probabilidad', ascending=False)
cortes = [10000, 10500, 11000, 11500, 12000]

print("\nGenerando archivos de salida...")
for corte in cortes:
    nombre_archivo = f"prediccion_202108_corte_{corte}.csv"
    df_resultados.head(corte)[['numero_de_cliente']].to_csv(nombre_archivo, index=False)
    print(f"Guardado: {nombre_archivo}")

print("Proceso finalizado.")

# [Anotación · líneas 220–241] Segunda celda: genera la lista de cortes de 10000 a 12000 cada 125 (17
#   valores), vuelve a convertir numero_de_cliente a int64 y a texto en el df_resultados que quedó en memoria y
#   escribe, para cada corte, prediccion_202108_2_corte_<corte>.csv con el mismo formato.
#%% celda 2 [código]
import pandas as pd

import pandas as pd

# Generar la lista de cortes: desde 10000 hasta 12000 (inclusive) con pasos de 125
cortes_extendidos = list(range(10000, 12001, 125))

print(f"Generando {len(cortes_extendidos)} nuevos cortes de validación...")

# Forzamos la limpieza de la columna directamente en memoria por si quedó algún .0 residual
df_resultados['numero_de_cliente'] = pd.to_numeric(df_resultados['numero_de_cliente']).astype('int64').astype(str)

for corte in cortes_extendidos:
    nombre_archivo = f"prediccion_202108_2_corte_{corte}.csv"

    # Exportar estrictamente la columna de IDs ya limpia
    df_resultados.head(corte)[['numero_de_cliente']].to_csv(nombre_archivo, index=False)

    print(f"Guardado: {nombre_archivo}")

print("¡Archivos extra generados con éxito y con los IDs limpios!")
```


## Explicaciones del alumno (texto original)

### README.md

> # prediccion_final_competencia1
> # Replicación de la Predicción Final - Ensamble LightGBM
>
> Esta carpeta contiene el código necesario para replicar de forma exacta la predicción final enviada para la competencia. La estrategia predictiva consiste en un **ensamble de 20 modelos LightGBM**, promediando las probabilidades obtenidas bajo distintas semillas aleatorias, utilizando hiperparámetros hallados mediante optimización bayesiana.
>
> El archivo final seleccionado como entrega oficial es el de **12000 registros** (`prediccion_202108_corte_12000.csv`). Se optó por este corte conservador basándose en la estabilidad histórica del leaderboard y para mitigar el riesgo de *overfitting* a meses atípicos en validaciones locales.
>
> ## Estructura de Archivos
>
> * `01_optimizacion_bayesiana.ipynb`: Script de Feature Engineering (Rankings con cero fijo, Lags y Deltas) y búsqueda de hiperparámetros mediante la librería Optuna maximizando el AUC.
> * `02_corrida_ensamble.ipynb`: Script final que genera el ensamble de 20 modelos, calcula el promedio de probabilidades, limpia los IDs de notación científica y exporta los archivos de submission en distintos cortes.
>
> ## Instrucciones de Replicación
>
> Ambos notebooks están diseñados para ejecutarse de forma secuencial en **Google Colab**. Descargarán automáticamente el dataset crudo (`competencia_01_crudo.csv`) si no se encuentra en el entorno, simulando la estructura de *buckets*.
>
> ### Paso 1: Optimización de Hiperparámetros (Opcional para replicación)
> El archivo `01_optimizacion_bayesiana.ipynb` contiene el proceso de *tuning*. Se utilizó el algoritmo TPE de Optuna (20 trials) maximizando el AUC. 
> Los mejores hiperparámetros identificados por el estudio fueron:
> * `n_estimators`: 1273
> * `num_leaves`: 721
> * `min_sum_hessian_in_leaf`: 0.003055877921643489
>
> ### Paso 2: Ejecución del Ensamble y Predicción Final (Replicación Exacta)
> Para replicar el archivo entregado, se debe ejecutar directamente el notebook `02_corrida_ensamble.ipynb`. 
>
> **Nota sobre los parámetros:** A partir de los resultados de la optimización bayesiana, se realizó un redondeo manual de los hiperparámetros para la corrida del ensamble. Los parámetros exactos configurados en este notebook son:
> * `n_estimators`: 1250
> * `num_leaves`: 700
> * `min_sum_hessian_in_leaf`: 0.003
>
> El notebook entrenará iterativamente 20 modelos variando la semilla aleatoria de LightGBM (generadas a partir de la semilla base `331613`). Al finalizar, promediará las probabilidades.
>
> ### Paso 3: Archivo de Entrega
> El script de ensamble generará una serie de cortes. El archivo que representa la predicción final oficial de esta entrega, con los IDs formateados correctamente como texto (sin `.0`), es:
>
> **`prediccion_202108_corte_12000.csv`**

