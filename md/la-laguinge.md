# llaguinge — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: la-laguinge
- Repositorio: https://github.com/la-laguinge/dmeyf-2026-competencia-01
- Link posteado: https://github.com/la-laguinge/dmeyf-2026-competencia-01
- Commit: 715cddf0993e23d83ec1e7e4ce6ebf848cd96fe1
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/la-laguinge/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/la-laguinge.json

## Resumen

La entrega contiene cuatro scripts de Python numerados, un README, un requirements.txt, el archivo de predicción RECREACION_Candidato_B_I11_4M_Base_K11500.csv (11.500 clientes), tres modelos LightGBM guardados como texto y la base SQLite de un estudio de Optuna. El camino es: el script 01 lee competencia_01.csv, calcula clase_ternaria si falta, crea clase_peligro (1 = BAJA+1 o BAJA+2) y escribe competencia_01_fe_v12_NA.csv; el 02 busca hiperparámetros de LightGBM con Optuna entrenando en 202103–202105 y midiendo en 202106 la ganancia de los 11.500 clientes de mayor probabilidad; el 03 pasa ccajas_depositos de 202105 a NaN, agrega lag1, lag2, delta1 y delta2 de 9 variables y, para las semillas 578777, 377717 y 717797, carga un modelo guardado o entrena en 202103–202106, promedia las probabilidades de 202108 y escribe los 11.500 clientes de mayor promedio; el 04 compara el SHA256 del archivo generado con el del archivo enviado. Los tres modelos guardados listan 415 variables: las 36 que crea el script 03, 225 con prefijos lag_1_, lag_2_, delta_1_, delta_2_, avg_3_, max_3_, min_3_, slope_3_, avg_6_, std_6_ y rank_intra_, y 154 más; ningún script del repositorio crea columnas con esos prefijos.

**Qué entrega.** Un CSV sin encabezado con 11.500 numero_de_cliente de 202108, uno por línea: los de mayor probabilidad promedio de tres modelos LightGBM. El repositorio incluye RECREACION_Candidato_B_I11_4M_Base_K11500.csv (11.500 líneas, sin repetidos), que según el README es la entrega final, con 103,7 M en el leaderboard público. El script 03 escribe su salida con el nombre ENTREGA_FINAL_M4_4M_Base_K11500.csv.

**Cómo se ejecuta.** El README da el orden: 1) 01_preprocesamiento/01_generar_dataset_fe_v12.py; 2) 02_optimizacion_bayesiana/02_optuna_bimodal_v64.py (indica que no hace falta volver a ejecutarlo para generar el archivo final); 3) 03_modelo_final/03_entrenar_y_predecir_M4_final.py; 4) 03_modelo_final/04_verificar_entrega.py. Según el README se corre en Google Colab con GPU; con USAR_MODELOS_GUARDADOS = True el script 03 carga los modelos guardados y con False entrena las tres semillas. Los scripts leen y escriben en /content/drive/MyDrive/DMEyF/2026/notebooks/data/.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: clase_peligro = 1 si clase_ternaria es BAJA+1 o BAJA+2 y 0 en el resto (las filas sin clase quedan en 0). En la búsqueda de hiperparámetros la ganancia se mide sólo contra BAJA+2.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código. Se entrena con todas las filas de los meses elegidos; LightGBM recibe is_unbalance=True.
- **Calidad de datos:** ccajas_depositos se pasa a NaN en las filas de 202105 (scripts 02 y 03). Las columnas float64 se convierten a float32.
- **Drifting:** No se observa en el código. Los modelos guardados listan 19 columnas con prefijo rank_intra_, cuya creación no figura en ningún script del repositorio.
- **Variables dentro del mes:** No se observa en el código. Los modelos guardados listan las columnas tc_saldo_total y ratio_trx_edad, cuya creación no figura en ningún script del repositorio.
- **Variables históricas:** Para 9 variables (ctrx_quarter, mcaja_ahorro, mtarjeta_visa_consumo, mcuentas_saldo, mpayroll, cpayroll_trx, mprestamos_personales, mactivos_margen, Visa_mlimitecompra) se crean lag1 y lag2 (valor de la fila anterior y de dos filas atrás, si son del mismo cliente) y delta1 y delta2 (valor actual menos cada lag): 36 columnas. El desplazamiento es por posición de fila con la tabla ordenada por cliente y mes. La consulta del script 03 no incluye 202107, de modo que en las filas de 202108 lag1 toma el valor de la fila previa cargada del mismo cliente (202106 si el cliente está en ese mes). Los modelos guardados listan además 206 columnas con prefijos lag_1_, lag_2_, delta_1_, delta_2_, avg_3_, max_3_, min_3_, slope_3_, avg_6_ y std_6_ que ningún script del repositorio crea.
- **Selección de variables:** El modelo usa todas las columnas del CSV de entrada salvo clase_ternaria, numero_de_cliente, foto_mes, peso_temporal y clase_peligro, más las 36 columnas de lags y deltas. Las 9 variables a las que se les calculan lags y deltas están escritas a mano en una lista; según el README son las 9 de mayor ganancia de información, y el cálculo de esa importancia no se observa en el código.
- **Optimización de hiperparámetros:** Optuna: estudio Optuna_Low que maximiza, con almacenamiento SQLite, timeout de 1.200 segundos y 4 trabajos en paralelo, sin sampler declarado. Fijos en la búsqueda: max_bin 31, min_data_in_leaf 0, learning_rate 0.005, is_unbalance True. Rangos: n_estimators 1500–3000, num_leaves 12–35, min_sum_hessian_in_leaf 0.01–5.0 (escala logarítmica), feature_fraction 0.3–0.6, feature_fraction_bynode 0.15–0.4, bagging_fraction 0.7–1.0, bagging_freq 1–5. Cada trial entrena en 202103–202105 y devuelve la ganancia de los 11.500 clientes de mayor probabilidad en 202106. Al terminar imprime el segundo trial completo ordenado por valor. El archivo optuna_low.db del repositorio contiene 27 trials (19 completos y 8 en estado RUNNING); el valor más alto registrado es 399.850.000 (trial número 15) y tres trials comparten el valor siguiente, 397.650.000; uno de ellos, el número 13, tiene parámetros que, redondeados a 4 decimales, coinciden con los de PARAMS_M4.
- **Hiperparámetros finales:** Escritos en el diccionario PARAMS_M4: objective binary, metric auc, boosting_type gbdt, is_unbalance True, device gpu, n_jobs -1, max_bin 31, min_data_in_leaf 0, learning_rate 0.005, n_estimators 2098, num_leaves 33, min_sum_hessian_in_leaf 0.0763, feature_fraction 0.5831, feature_fraction_bynode 0.2806, bagging_fraction 0.7040, bagging_freq 5.
- **Semillas:** 578777, 377717 y 717797, escritas en la lista SEMILLAS y pasadas como random_state. En la búsqueda de Optuna, random_state = 17 + número de trial.
- **Cantidad de semillas:** 3
- **Ensamble:** Promedio de las probabilidades de 3 modelos LightGBM con los mismos hiperparámetros y distinta semilla.
- **Corte:** Cantidad fija: los 11.500 clientes de mayor probabilidad promedio (K_EVAL = 11500). El mismo valor 11.500 se usa como corte al medir la ganancia en la búsqueda de hiperparámetros.
- **Validación:** En la búsqueda de hiperparámetros: entrenamiento en 202103–202105 y ganancia en 202106 sobre los 11.500 clientes de mayor probabilidad (1.072.500 por cada BAJA+2 y −27.500 por cada uno de los demás). En el script del modelo final no hay validación. El script 04 compara el SHA256 del archivo generado con el del archivo enviado al bot.
- **Salidas:** Script 01: competencia_01_fe_v12_NA.csv. Script 02: optuna_low.db y la impresión del segundo trial por valor. Script 03: ENTREGA_FINAL_M4_4M_Base_K11500.csv (sin encabezado, un numero_de_cliente por línea) y, cuando entrena, un archivo lgb_seed_<semilla>.txt por semilla. El repositorio incluye RECREACION_Candidato_B_I11_4M_Base_K11500.csv, optuna_low.db y los tres lgb_seed_*.txt.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: no
- Entorno declarado: Según el README, Google Colab con GPU (device = 'gpu', n_jobs = -1). requirements.txt lista numpy, pandas, duckdb, lightgbm, optuna y scikit-learn sin números de versión. Los modelos guardados registran formato version=v4, device_type gpu y num_threads 8. Las consultas de DuckDB fijan memory_limit en 45GB.

## Pasos del camino de la entrega

1. **Lectura del dataset original y cálculo de clase_ternaria.** El script 01 lee competencia_01.csv completo con DuckDB. Si la tabla no trae clase_ternaria, la calcula: BAJA+1 si el cliente no aparece en el mes siguiente, BAJA+2 si aparece en el siguiente pero no en el subsiguiente, CONTINUA en el resto; deja sin clase el último mes y, en el penúltimo, las filas de clientes que siguen presentes. (`01_preprocesamiento/01_generar_dataset_fe_v12.py` líneas 14–33)
2. **Clase binaria clase_peligro y exportación.** Crea clase_peligro con 1 para BAJA+1 y BAJA+2 y 0 para el resto, y escribe la tabla completa en competencia_01_fe_v12_NA.csv. (`01_preprocesamiento/01_generar_dataset_fe_v12.py` líneas 35–39)
3. **Preparación de datos para la búsqueda de hiperparámetros.** El script 02 lee competencia_01_fe_v12_NA.csv completo, pasa las columnas float64 a float32, pone ccajas_depositos en NaN en 202105 y ordena por cliente y mes. (`02_optimizacion_bayesiana/02_optuna_bimodal_v64.py` líneas 26–40)
4. **Lags y deltas de 9 variables (búsqueda).** Para cada una de las 9 variables de top_vars crea lag1, lag2, delta1 y delta2 por desplazamiento de filas, con NaN cuando la fila desplazada es de otro cliente. (`02_optimizacion_bayesiana/02_optuna_bimodal_v64.py` líneas 20–24; `02_optimizacion_bayesiana/02_optuna_bimodal_v64.py` líneas 42–54)
5. **Partición temporal para la búsqueda.** Conserva 202103–202106; entrena con 202103–202105 y clase_peligro, y valida en 202106 contra un vector que marca sólo BAJA+2. (`02_optimizacion_bayesiana/02_optuna_bimodal_v64.py` líneas 56–67)
6. **Búsqueda con Optuna.** Cada trial entrena un LGBMClassifier con max_bin 31, min_data_in_leaf 0 y learning_rate 0.005 fijos y 7 hiperparámetros muestreados, y devuelve la ganancia de los 11.500 clientes de mayor probabilidad en 202106. El estudio Optuna_Low maximiza ese valor durante 1.200 segundos con 4 trabajos en paralelo y guarda los trials en optuna_low.db. (`02_optimizacion_bayesiana/02_optuna_bimodal_v64.py` líneas 69–97)
7. **Elección de la configuración.** El script 02 imprime el segundo trial completo ordenado por valor. El script 03 tiene los hiperparámetros escritos en PARAMS_M4; según el README son los de esa búsqueda (LowTop2). (`02_optimizacion_bayesiana/02_optuna_bimodal_v64.py` líneas 99–102; `03_modelo_final/03_entrenar_y_predecir_M4_final.py` líneas 38–45)
8. **Carga de datos para el modelo final.** El script 03 lee de competencia_01_fe_v12_NA.csv los meses 202101 a 202106 y 202108, pasa float64 a float32 y pone ccajas_depositos en NaN en 202105. (`03_modelo_final/03_entrenar_y_predecir_M4_final.py` líneas 50–59)
9. **Lags y deltas de 9 variables (modelo final).** Ordena por cliente y mes, guarda la lista de columnas de entrada y agrega lag1, lag2, delta1 y delta2 de las 9 variables de top_9_vars (36 columnas). Las variables del modelo son las columnas de entrada más esas 36. (`03_modelo_final/03_entrenar_y_predecir_M4_final.py` líneas 61–79)
10. **Conjuntos de entrenamiento y de predicción.** Entrenamiento: filas de 202103, 202104, 202105 y 202106 con clase_peligro como objetivo (NaN pasa a 0). Predicción: filas de 202108. (`03_modelo_final/03_entrenar_y_predecir_M4_final.py` líneas 81–89)
11. **Tres semillas: carga del modelo guardado o entrenamiento.** Para cada semilla de SEMILLAS, si USAR_MODELOS_GUARDADOS es True y existe lgb_seed_<semilla>.txt en la carpeta de modelos, carga ese modelo y predice 202108; si no, entrena un LGBMClassifier con PARAMS_M4 y random_state igual a la semilla, guarda el modelo como texto y predice. Acumula un tercio de cada probabilidad. (`03_modelo_final/03_entrenar_y_predecir_M4_final.py` líneas 94–116)
12. **Corte y escritura del archivo.** Ordena los clientes de 202108 por probabilidad promedio descendente con ordenamiento estable, toma los primeros 11.500 y escribe sus numero_de_cliente sin encabezado en ENTREGA_FINAL_M4_4M_Base_K11500.csv. (`03_modelo_final/03_entrenar_y_predecir_M4_final.py` líneas 118–122)
13. **Verificación contra el archivo enviado.** El script 04 calcula el SHA256 del archivo enviado al bot y del archivo generado, cuenta los clientes en común y detiene la ejecución con un assert si los dos hashes difieren. (`03_modelo_final/04_verificar_entrega.py` líneas 14–28)

## Archivos

- `requirements.txt` · configuracion · Texto · 6 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/la-laguinge/requirements.txt.txt) — Lista seis paquetes de Python sin números de versión: numpy, pandas, duckdb, lightgbm, optuna y scikit-learn.
- `README.md` · explicacion · Markdown · 61 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/la-laguinge/README.md.txt) — Presenta la entrega en tres secciones: arquitectura del modelo final (3 semillas de LightGBM sobre 202103–202106, lags y deltas de 9 variables, clase_peligro, hiperparámetros LowTop2 y corte en 11.500), lista de experimentos descartados y de pasos previos con las ganancias públicas que declara, e instrucciones de reproducción con el orden de los cuatro scripts y una nota sobre la variación entre corridas en GPU y el uso de los modelos guardados. Declara 103,7 M en el leaderboard público para el archivo final.
- `03_modelo_final/04_verificar_entrega.py` · secundario · Python · 28 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/la-laguinge/03_modelo_final/04_verificar_entrega.py.txt) — Compara el archivo que escribe el script 03 con el archivo enviado al bot: calcula el SHA256 de ambos y la cantidad de clientes en común. Las comprobaciones de cantidad de líneas, duplicados y pertenencia a 202108 que menciona el README no se observan en el código.
- `03_modelo_final/03_entrenar_y_predecir_M4_final.py` · principal · Python · 122 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/la-laguinge/03_modelo_final/03_entrenar_y_predecir_M4_final.py.txt) — Arma las variables, obtiene las probabilidades de 202108 con tres modelos LightGBM (cargados desde archivos de texto o entrenados en 202103–202106), las promedia y escribe los 11.500 clientes de mayor promedio.
- `02_optimizacion_bayesiana/02_optuna_bimodal_v64.py` · principal · Python · 102 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/la-laguinge/02_optimizacion_bayesiana/02_optuna_bimodal_v64.py.txt) — Búsqueda de hiperparámetros de LightGBM con Optuna: arma lags y deltas de 9 variables, entrena en 202103–202105 y mide en 202106 la ganancia de los 11.500 clientes de mayor probabilidad. Según el README, de esta búsqueda salen los hiperparámetros del modelo final.
- `01_preprocesamiento/01_generar_dataset_fe_v12.py` · principal · Python · 42 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/la-laguinge/01_preprocesamiento/01_generar_dataset_fe_v12.py.txt) — Lee competencia_01.csv, calcula clase_ternaria si la columna no existe, crea la clase binaria clase_peligro y escribe competencia_01_fe_v12_NA.csv.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### 03_modelo_final/03_entrenar_y_predecir_M4_final.py

Arma las variables, obtiene las probabilidades de 202108 con tres modelos LightGBM (cargados desde archivos de texto o entrenados en 202103–202106), las promedia y escribe los 11.500 clientes de mayor promedio.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Importa duckdb, pandas, numpy, lightgbm y LGBMClassifier y silencia las
#   advertencias.
"""
Paso 03: Entrenamiento y Predicción del Modelo Final M4 (4 Meses Base + Ensamble 3 Semillas).
Apunta directamente a la carpeta donde se guardaron los modelos .txt de la recreación ganadora
para garantizar reproducción 100% exacta bit a bit (o re-entrenar si USAR_MODELOS_GUARDADOS=False).
"""
import os, gc, duckdb, datetime, time
import pandas as pd, numpy as np
import lightgbm as lgb
from lightgbm import LGBMClassifier
import warnings

warnings.filterwarnings('ignore')

# [Anotación · líneas 14–30] Define las rutas en Google Drive: carpeta de datos, carpeta
#   evaluacion_recreacion_final/Candidato_B_I11_4M_Base y, dentro, la carpeta modelos (la crea si no existe); la
#   entrada es competencia_01_fe_v12_NA.csv. Fija USAR_MODELOS_GUARDADOS en True, las columnas que no entran
#   como variables, las tres semillas 578777, 377717 y 717797 y el corte K_EVAL = 11500.
# ==========================================
# 0. RUTAS Y CONFIGURACIÓN
# ==========================================
base_path = '/content/drive/MyDrive/DMEyF/2026/notebooks/data/'
carpeta_m4 = os.path.join(base_path, 'evaluacion_recreacion_final', 'Candidato_B_I11_4M_Base')
modelos_dir = os.path.join(carpeta_m4, 'modelos')
os.makedirs(modelos_dir, exist_ok=True)

dataset_path = os.path.join(base_path, 'competencia_01_fe_v12_NA.csv')

# True: Carga los 3 árboles .txt congelados en modelos/ (Reproducción 100.00% idéntica SHA256)
# False: Re-entrena las 3 semillas desde cero en GPU
USAR_MODELOS_GUARDADOS = True

cols_basura = ['clase_ternaria', 'numero_de_cliente', 'foto_mes', 'peso_temporal']
SEMILLAS = [578777, 377717, 717797]
K_EVAL = 11500

# [Anotación · líneas 32–45] Lista las 9 variables a las que se les calculan lags y deltas y define PARAMS_M4:
#   objective binary, metric auc, gbdt, is_unbalance True, n_jobs -1, device gpu, max_bin 31, min_data_in_leaf
#   0, learning_rate 0.005, n_estimators 2098, num_leaves 33, min_sum_hessian_in_leaf 0.0763, feature_fraction
#   0.5831, feature_fraction_bynode 0.2806, bagging_fraction 0.7040 y bagging_freq 5.
top_9_vars = [
    'ctrx_quarter', 'mcaja_ahorro', 'mtarjeta_visa_consumo', 'mcuentas_saldo',
    'mpayroll', 'cpayroll_trx', 'mprestamos_personales', 'mactivos_margen', 
    'Visa_mlimitecompra'
]

PARAMS_M4 = {
    'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt', 'is_unbalance': True,
    'n_jobs': -1, 'verbose': -1, 'device': 'gpu', 
    'max_bin': 31, 'min_data_in_leaf': 0, 'learning_rate': 0.005, 
    'n_estimators': 2098, 'num_leaves': 33, 'min_sum_hessian_in_leaf': 0.0763,
    'feature_fraction': 0.5831, 'feature_fraction_bynode': 0.2806,
    'bagging_fraction': 0.7040, 'bagging_freq': 5
}

# [Anotación · líneas 47–59] Lee con DuckDB (límite de memoria de 45GB) las filas de 202101, 202102, 202103,
#   202104, 202105, 202106 y 202108; 202107 no está en la lista. Convierte float64 a float32 y pone
#   ccajas_depositos en NaN en las filas de 202105.
# ==========================================
# 1. CARGA E INGENIERÍA DE ATRIBUTOS (TOP 9 LAGS & DELTAS)
# ==========================================
print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📂 Cargando datos e ingeniería M4 (4 Meses Base)...")
con = duckdb.connect()
con.execute("PRAGMA memory_limit='45GB'")
df = con.execute(f"SELECT * FROM read_csv_auto('{dataset_path}') WHERE foto_mes IN (202101, 202102, 202103, 202104, 202105, 202106, 202108)").df()
con.close()

for c in df.columns:
    if df[c].dtype == 'float64': df[c] = df[c].astype('float32', copy=False)
if 'ccajas_depositos' in df.columns:
    df.loc[df['foto_mes'] == 202105, 'ccajas_depositos'] = np.nan

# [Anotación · líneas 61–66] Ordena por numero_de_cliente y foto_mes y reinicia el índice. Guarda como
#   cols_originales todas las columnas salvo clase_ternaria, numero_de_cliente, foto_mes, peso_temporal y
#   clase_peligro. Calcula los vectores que indican si la fila anterior y la de dos posiciones atrás son del
#   mismo cliente.
df.sort_values(by=['numero_de_cliente', 'foto_mes'], inplace=True)
df.reset_index(drop=True, inplace=True)

cols_originales = [c for c in df.columns if c not in cols_basura + ['clase_peligro']]
es_mismo_1 = (df['numero_de_cliente'] == df['numero_de_cliente'].shift(1)).values
es_mismo_2 = (df['numero_de_cliente'] == df['numero_de_cliente'].shift(2)).values

# [Anotación · líneas 68–79] Para cada una de las 9 variables crea _lag1 y _lag2 (valor de la fila anterior y
#   de dos filas atrás, NaN si es otro cliente) y _delta1 y _delta2 (valor actual menos cada lag), en float32:
#   36 columnas. El desplazamiento es por posición de fila sobre los meses cargados. La lista de variables del
#   modelo, cols_activas, une cols_originales con esas 36.
base_top9 = []
for col in top_9_vars:
    if col in df.columns:
        v = df[col].values
        l1 = np.where(es_mismo_1, df[col].shift(1).values, np.nan).astype(np.float32)
        l2 = np.where(es_mismo_2, df[col].shift(2).values, np.nan).astype(np.float32)
        df[f'{col}_lag1'] = l1; df[f'{col}_lag2'] = l2
        df[f'{col}_delta1'] = np.where(es_mismo_1, v - l1, np.nan).astype(np.float32)
        df[f'{col}_delta2'] = np.where(es_mismo_2, v - l2, np.nan).astype(np.float32)
        base_top9.extend([f'{col}_lag1', f'{col}_lag2', f'{col}_delta1', f'{col}_delta2'])

cols_activas = cols_originales + base_top9

# [Anotación · líneas 81–89] Separa entrenamiento (202103 a 202106, objetivo clase_peligro con NaN pasado a 0)
#   y predicción (202108), guarda los numero_de_cliente de 202108 y libera la tabla completa.
mask_tr = df['foto_mes'].isin([202103, 202104, 202105, 202106])
mask_te = df['foto_mes'] == 202108

X_tr = df.loc[mask_tr, cols_activas]
y_tr = df.loc[mask_tr, 'clase_peligro'].fillna(0).astype(np.int8).values
X_te = df.loc[mask_te, cols_activas]
num_cliente = df.loc[mask_te, 'numero_de_cliente'].values

del df; gc.collect()

# [Anotación · líneas 91–101] Inicia en cero el acumulador de probabilidades. Para cada semilla arma la ruta
#   lgb_seed_<semilla>.txt; si USAR_MODELOS_GUARDADOS es True y el archivo existe, carga el modelo con
#   lgb.Booster y predice sobre las filas de 202108.
# ==========================================
# 2. PREDICCIÓN DESDE MODELOS GUARDADOS O RE-ENTRENAMIENTO
# ==========================================
probas = np.zeros(len(X_te), dtype=np.float64)

for seed in SEMILLAS:
    ruta_txt = os.path.join(modelos_dir, f'lgb_seed_{seed}.txt')
    if USAR_MODELOS_GUARDADOS and os.path.exists(ruta_txt):
        print(f"   📦 Cargando modelo congelado: lgb_seed_{seed}.txt")
        booster = lgb.Booster(model_file=ruta_txt)
        prob = booster.predict(X_te)
# [Anotación · líneas 102–116] En caso contrario copia PARAMS_M4, fija random_state en la semilla y entrena un
#   LGBMClassifier con 202103–202106; si el ajuste lanza una excepción, quita el parámetro device y vuelve a
#   entrenar. Guarda el modelo como texto y predice la probabilidad de la clase 1 en 202108. En ambos casos suma
#   al acumulador la probabilidad dividida por 3.
    else:
        print(f"   🚀 Entrenando semilla {seed}...")
        p = PARAMS_M4.copy()
        p['random_state'] = seed
        try:
            m = LGBMClassifier(**p)
            m.fit(X_tr, y_tr)
        except Exception:
            p.pop('device', None)
            m = LGBMClassifier(**p)
            m.fit(X_tr, y_tr)
        m.booster_.save_model(ruta_txt)
        prob = m.predict_proba(X_te)[:, 1]
        
    probas += prob / len(SEMILLAS)

# [Anotación · líneas 118–122] Arma una tabla con numero_de_cliente y probabilidad promedio, la ordena de
#   mayor a menor con mergesort (ordenamiento estable), toma las primeras 11.500 filas y escribe los
#   numero_de_cliente como enteros, sin encabezado ni índice, en ENTREGA_FINAL_M4_4M_Base_K11500.csv. Imprime la
#   ruta del archivo.
df_ens = pd.DataFrame({'numero_de_cliente': num_cliente, 'prob': probas}).sort_values(by='prob', ascending=False, kind='mergesort')
ruta_salida = os.path.join(carpeta_m4, f"ENTREGA_FINAL_M4_4M_Base_K{K_EVAL}.csv")
df_ens.head(K_EVAL)['numero_de_cliente'].astype(int).to_csv(ruta_salida, index=False, header=False)

print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] 🏁 Archivo final exportado en:\n   {ruta_salida}")
```

### 02_optimizacion_bayesiana/02_optuna_bimodal_v64.py

Búsqueda de hiperparámetros de LightGBM con Optuna: arma lags y deltas de 9 variables, entrena en 202103–202105 y mide en 202106 la ganancia de los 11.500 clientes de mayor probabilidad. Según el README, de esta búsqueda salen los hiperparámetros del modelo final.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–18] Importa duckdb, pandas, numpy, optuna y LGBMClassifier y silencia las
#   advertencias. Define la carpeta de datos en Google Drive, crea la carpeta de corrida
#   run_v64_Optuna_Bimodal_20min, fija como entrada competencia_01_fe_v12_NA.csv y lista las columnas que no
#   entran como variables: clase_ternaria, numero_de_cliente, foto_mes y peso_temporal.
"""
Paso 02: Optimización Bayesiana (Origen de los hiperparámetros LowTop2 del modelo M4).
Entrena en 202103-202105 y valida ganancia directa en 202106 (corte K=11500).
"""
import os, gc, duckdb, datetime
import pandas as pd, numpy as np
import optuna
from lightgbm import LGBMClassifier
import warnings

warnings.filterwarnings('ignore')

base_path = '/content/drive/MyDrive/DMEyF/2026/notebooks/data/'
run_base_path = os.path.join(base_path, 'run_v64_Optuna_Bimodal_20min')
os.makedirs(run_base_path, exist_ok=True)

dataset_path = os.path.join(base_path, 'competencia_01_fe_v12_NA.csv')
cols_basura = ['clase_ternaria', 'numero_de_cliente', 'foto_mes', 'peso_temporal']

# [Anotación · líneas 20–24] Lista las 9 variables a las que se les calculan lags y deltas: ctrx_quarter,
#   mcaja_ahorro, mtarjeta_visa_consumo, mcuentas_saldo, mpayroll, cpayroll_trx, mprestamos_personales,
#   mactivos_margen y Visa_mlimitecompra.
top_vars = [
    'ctrx_quarter', 'mcaja_ahorro', 'mtarjeta_visa_consumo', 'mcuentas_saldo',
    'mpayroll', 'cpayroll_trx', 'mprestamos_personales', 'mactivos_margen',
    'Visa_mlimitecompra'
]

# [Anotación · líneas 26–34] Lee el CSV completo con DuckDB (límite de memoria de 45GB) a un DataFrame de
#   pandas y convierte las columnas float64 a float32.
print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Preparando datos para Optuna (202103-202106)...")
con = duckdb.connect()
con.execute("PRAGMA memory_limit='45GB'")
df = con.execute(f"SELECT * FROM read_csv_auto('{dataset_path}')").df()
con.close()

for c in df.columns:
    if df[c].dtype == 'float64':
        df[c] = df[c].astype('float32', copy=False)

# [Anotación · líneas 36–40] Pone ccajas_depositos en NaN en las filas de 202105, ordena la tabla por
#   numero_de_cliente y foto_mes y reinicia el índice.
if 'ccajas_depositos' in df.columns:
    df.loc[df['foto_mes'] == 202105, 'ccajas_depositos'] = np.nan

df.sort_values(by=['numero_de_cliente', 'foto_mes'], inplace=True)
df.reset_index(drop=True, inplace=True)

# [Anotación · líneas 42–54] Calcula dos vectores booleanos que indican si la fila anterior y la de dos
#   posiciones atrás pertenecen al mismo cliente. Para cada una de las 9 variables crea _lag1 y _lag2 (valor de
#   esas filas) y _delta1 y _delta2 (valor actual menos el de esas filas), en float32, con NaN cuando la fila
#   desplazada es de otro cliente.
es_mismo_cliente_1 = (df['numero_de_cliente'] == df['numero_de_cliente'].shift(1)).values
es_mismo_cliente_2 = (df['numero_de_cliente'] == df['numero_de_cliente'].shift(2)).values

for col in top_vars:
    if col in df.columns:
        val_actual = df[col].values
        val_lag1 = df[col].shift(1).values
        val_lag2 = df[col].shift(2).values

        df[f'{col}_lag1'] = np.where(es_mismo_cliente_1, val_lag1, np.nan).astype(np.float32)
        df[f'{col}_lag2'] = np.where(es_mismo_cliente_2, val_lag2, np.nan).astype(np.float32)
        df[f'{col}_delta1'] = np.where(es_mismo_cliente_1, val_actual - val_lag1, np.nan).astype(np.float32)
        df[f'{col}_delta2'] = np.where(es_mismo_cliente_2, val_actual - val_lag2, np.nan).astype(np.float32)

# [Anotación · líneas 56–67] Conserva los meses 202103 a 202106. Define entrenamiento como foto_mes hasta
#   202105 y validación como 202106. Arma el vector de validación con 1 sólo para BAJA+2, separa clase_peligro
#   como objetivo (NaN pasa a 0), quita las columnas de cols_basura y deja las matrices de entrenamiento y de
#   validación.
df_train = df[df['foto_mes'].isin([202103, 202104, 202105, 202106])].copy()
del df; gc.collect()

mask_tr = df_train['foto_mes'] <= 202105
mask_val = df_train['foto_mes'] == 202106

y_val_baja2 = (df_train.loc[mask_val, 'clase_ternaria'] == 'BAJA+2').astype(np.int8).values
y_train = df_train.pop('clase_peligro').fillna(0).astype(np.int8)
df_train.drop(columns=cols_basura, inplace=True, errors='ignore')

X_tr_opt, y_tr_opt = df_train[mask_tr], y_train[mask_tr]
X_val_opt = df_train[mask_val]

# [Anotación · líneas 69–81] Función objetivo de Optuna. Parámetros fijos: objective binary, metric auc, gbdt,
#   is_unbalance True, random_state 17 + número de trial, n_jobs 2, max_bin 31, min_data_in_leaf 0,
#   learning_rate 0.005, device gpu. Parámetros muestreados: n_estimators entre 1500 y 3000, num_leaves entre 12
#   y 35, min_sum_hessian_in_leaf entre 0.01 y 5.0 en escala logarítmica, feature_fraction entre 0.3 y 0.6,
#   feature_fraction_bynode entre 0.15 y 0.4, bagging_fraction entre 0.7 y 1.0 y bagging_freq entre 1 y 5.
def objective_low(trial):
    params = {
        'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt', 'is_unbalance': True,
        'random_state': 17 + trial.number, 'n_jobs': 2, 'verbose': -1, 'max_bin': 31,
        'min_data_in_leaf': 0, 'learning_rate': 0.005, 'device': 'gpu',
        'n_estimators': trial.suggest_int('n_estimators', 1500, 3000),
        'num_leaves': trial.suggest_int('num_leaves', 12, 35),
        'min_sum_hessian_in_leaf': trial.suggest_float('min_sum_hessian_in_leaf', 0.01, 5.0, log=True),
        'feature_fraction': trial.suggest_float('feature_fraction', 0.3, 0.6),
        'feature_fraction_bynode': trial.suggest_float('feature_fraction_bynode', 0.15, 0.4),
        'bagging_fraction': trial.suggest_float('bagging_fraction', 0.7, 1.0),
        'bagging_freq': trial.suggest_int('bagging_freq', 1, 5)
    }
# [Anotación · líneas 82–93] Entrena un LGBMClassifier con 202103–202105; si el ajuste lanza una excepción,
#   quita el parámetro device y vuelve a entrenar. Predice la probabilidad en 202106, ordena de mayor a menor y
#   devuelve la ganancia de los primeros 11.500: 1.072.500 por cada BAJA+2 y −27.500 por cada uno de los demás.
    try:
        model = LGBMClassifier(**params)
        model.fit(X_tr_opt, y_tr_opt)
    except Exception:
        params.pop('device', None)
        model = LGBMClassifier(**params)
        model.fit(X_tr_opt, y_tr_opt)

    prob_val = model.predict_proba(X_val_opt)[:, 1]
    orden = np.argsort(prob_val)[::-1]
    y_val_ordenado = y_val_baja2[orden]
    return np.sum(np.where(y_val_ordenado[:11500] == 1, 1072500, -27500))

# [Anotación · líneas 95–97] Crea, o retoma si ya existe, el estudio Optuna_Low con dirección maximize y
#   almacenamiento SQLite en optuna_low.db dentro de la carpeta de corrida. Ejecuta la búsqueda con timeout de
#   1.200 segundos y 4 trabajos en paralelo.
db_path_low = os.path.join(run_base_path, 'optuna_low.db')
study_low = optuna.create_study(direction='maximize', study_name='Optuna_Low', storage=f'sqlite:///{db_path_low}', load_if_exists=True)
study_low.optimize(objective_low, timeout=1200, n_jobs=4)

# [Anotación · líneas 99–102] Pasa los trials a un DataFrame, conserva los de estado COMPLETE, los ordena por
#   valor descendente e imprime la segunda fila (posición 1).
top_low = study_low.trials_dataframe()
top_low = top_low[top_low['state'] == 'COMPLETE'].sort_values(by='value', ascending=False)
print("\n=== PARÁMETROS DEL LOW TOP 2 SELECCIONADO ===")
print(top_low.iloc[1])
```

### 01_preprocesamiento/01_generar_dataset_fe_v12.py

Lee competencia_01.csv, calcula clase_ternaria si la columna no existe, crea la clase binaria clase_peligro y escribe competencia_01_fe_v12_NA.csv.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Importa os, duckdb, numpy y pandas y define las rutas: una carpeta de Google Drive
#   montada en Colab, el archivo de entrada competencia_01.csv y el de salida competencia_01_fe_v12_NA.csv.
"""
Paso 01: Generación de competencia_01_fe_v12_NA.csv a partir del dataset original de la cátedra.
Construye clase_ternaria (si se parte del crudo sin target), define clase_peligro y preserva NAs.
"""
import os
import duckdb
import numpy as np
import pandas as pd

BASE_PATH = '/content/drive/MyDrive/DMEyF/2026/notebooks/data/'
INPUT_CSV = os.path.join(BASE_PATH, 'competencia_01.csv')
OUTPUT_CSV = os.path.join(BASE_PATH, 'competencia_01_fe_v12_NA.csv')

# [Anotación · líneas 14–19] Abre una conexión de DuckDB con límite de memoria de 45GB, lee el CSV completo
#   con read_csv_auto, lo pasa a un DataFrame de pandas y cierra la conexión.
def main():
    print("Cargando dataset original con DuckDB...")
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='45GB'")
    df = con.execute(f"SELECT * FROM read_csv_auto('{INPUT_CSV}')").df()
    con.close()

# [Anotación · líneas 21–33] Sólo si la tabla no trae clase_ternaria: numera los meses en orden, arma el
#   conjunto de pares (cliente, índice de mes) presentes y, para cada fila, verifica si el cliente aparece en el
#   mes siguiente y en el subsiguiente. Asigna BAJA+1 si no aparece en el siguiente, BAJA+2 si aparece en el
#   siguiente y no en el subsiguiente, y CONTINUA en el resto. Deja sin clase las filas del último mes y las del
#   penúltimo cuyo cliente aparece en el último.
    # Si el archivo es el crudo sin clase_ternaria, se calcula según contigüidad m+1 y m+2
    if 'clase_ternaria' not in df.columns:
        meses = sorted(df['foto_mes'].unique())
        mi = df['foto_mes'].map({m: i for i, m in enumerate(meses)}).tolist()
        cli = df['numero_de_cliente'].tolist()
        presentes = set(zip(cli, mi))
        en_m1 = np.fromiter(((c, m + 1) in presentes for c, m in zip(cli, mi)), bool, len(df))
        en_m2 = np.fromiter(((c, m + 2) in presentes for c, m in zip(cli, mi)), bool, len(df))
        clase = np.where(~en_m1, 'BAJA+1', np.where(~en_m2, 'BAJA+2', 'CONTINUA')).astype(object)
        mi_arr = np.array(mi)
        clase[mi_arr == len(meses) - 1] = None
        clase[(mi_arr == len(meses) - 2) & en_m1] = None
        df['clase_ternaria'] = clase

# [Anotación · líneas 35–39] Crea clase_peligro como entero de 8 bits: 1 cuando clase_ternaria es BAJA+1 o
#   BAJA+2 y 0 en cualquier otro caso, incluidas las filas sin clase. Escribe la tabla completa a CSV sin índice
#   e imprime la cantidad de filas y de columnas.
    # Target binario unificado: BAJA+1 y BAJA+2 como positivos (1)
    df['clase_peligro'] = df['clase_ternaria'].isin(['BAJA+1', 'BAJA+2']).astype(np.int8)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Dataset exportado exitosamente en: {OUTPUT_CSV} ({df.shape[0]:,} filas, {df.shape[1]} columnas)")

# [Anotación · líneas 41–42] Punto de entrada: ejecuta main() cuando el archivo se corre como script.
if __name__ == '__main__':
    main()
```


## Explicaciones del alumno (texto original)

### README.md

> # dmeyf-2026-competencia-01
> Esta es mi entrega a la competencia 1 para la materia DMEyF:
>
> # DMEyF 2026 — Primera Competencia: Predicción de Churn Bancario (202108)
> **Autor:** Luis María Laguinge  
> **Entrega Final:** `RECREACION_Candidato_B_I11_4M_Base_K11500.csv` (**103.7 M** en Leaderboard Público)
>
> ---
>
> ## 1. Arquitectura de la Solución Final (Modelo M4 - 4 Meses Base)
>
> La solución final consiste en un **Ensamble homogéneo de 3 semillas (`578777`, `377717`, `717797`) de LightGBM**, entrenado sobre la ventana histórica de **4 meses (`202103`, `202104`, `202105`, `202106`)**, utilizando ingeniería de atributos focalizada sobre las 9 variables de mayor ganancia de información y los hiperparámetros óptimos obtenidos mediante Optimización Bayesiana restringida (`LowTop2`).
>
> ### Componentes Clave del Pipeline:
> 1. **Data Quality (Regla Cátedra):** Imputación a `NaN` de la variable `ccajas_depositos` en `202105` debido a la anomalía de carga detectada en ese mes (100% de valores en cero).
> 2. **Feature Engineering Focalizado (Top 9 Variables):** Cálculo en memoria (DuckDB + NumPy) de rezagos de orden 1 y 2 (`lag1`, `lag2`) y variaciones absolutas (`delta1`, `delta2`) verificando estricta contigüidad por cliente sobre las 9 variables núcleo:
>    * `ctrx_quarter`, `mcaja_ahorro`, `mtarjeta_visa_consumo`, `mcuentas_saldo`, `mpayroll`, `cpayroll_trx`, `mprestamos_personales`, `mactivos_margen` y `Visa_mlimitecompra`.
> 3. **Target Binario Ampliado (`clase_peligro`):** Se entrena considerando `BAJA+1` y `BAJA+2` como clase positiva (`1`) para duplicar los casos de aprendizaje de fuga, mientras que la validación en Optuna y el corte se evalúan estrictamente contra la ganancia real de `BAJA+2` (`+$1.072.500` por acierto, `-$27.500` por estímulo).
> 4. **Optimización Bayesiana (`LowTop2`):** Búsqueda realizada con Optuna entrenando en `202103–202105` y evaluando la ganancia directa en `202106` en el corte `K = 11.500`, respetando los parámetros estructurales de la cátedra (`max_bin = 31`, `min_data_in_leaf = 0`, `learning_rate = 0.005`) y acotando `num_leaves` al rango `[12, 35]` para prevenir el sobreajuste.
>    * **Hiperparámetros Ganadores (`LowTop2`):**
>      * `n_estimators`: `2098`
>      * `num_leaves`: `33`
>      * `min_sum_hessian_in_leaf`: `0.0763`
>      * `feature_fraction`: `0.5831`
>      * `feature_fraction_bynode`: `0.2806`
>      * `bagging_fraction`: `0.7040`
>      * `bagging_freq`: `5`
> 5. **Ensamble de Semillas y Corte:** Se entrenan 3 modelos independientes sobre `202103–202106` con las semillas `578777`, `377717` y `717797`, se promedian sus probabilidades predichas para `202108` y se seleccionan los `K = 11.500` clientes de mayor probabilidad.
>
> ---
>
> ## 2. Evolución de Experimentos y Enfoques Descartados
>
> A lo largo de la competencia se ejecutaron múltiples iteraciones documentadas en el Leaderboard Público:
>
> ### A. Qué NO funcionó (Hipótesis Descartadas)
> * **Expansión por "Fuerza Bruta" (Lags y Deltas sobre las 152 variables crudas):** Generar más de 450 columnas diluyó la relevancia de las variables principales en el muestreo por nodo (`feature_fraction_bynode`), incrementando la varianza entre semillas y degradando la ganancia pública.
> * **Validación con Fuga Temporal Deliberada (Train 202101–202106 / Val 202106):** Optimizar hiperparámetros evaluando sobre el mismo mes incluido en el entrenamiento indujo un sobreajuste severo (ganancia pública cayendo a `88.83 M` con desvío estándar de `4.69 M`).
> * **Selectores Dinámicos de Familias de Variables dentro de Optuna:** Permitir que Optuna activara o desactivara bloques enteros de variables al mismo tiempo que buscaba hiperparámetros afectó la convergencia (`98.2 M – 102.3 M`), rindiendo por debajo del conjunto fijo de 9 variables núcleo.
> * **Árboles Profundos (`num_leaves > 35`) con `min_data_in_leaf = 0`:** Superar las 35 hojas sin restricción de tamaño mínimo de hoja generó memorización de ruido local y desvíos estándar superiores a `2.70 M` entre semillas.
> * **Exclusión de Variables de Haberes (`mpayroll`, `cpayroll_trx`):** Eliminar las variables de acreditación de sueldos por el efecto aguinaldo de junio restó poder predictivo en agosto (`202108`).
> * **Agregado de Variables Complejas Aisladas (`Lag3`, Aceleración, Ratios):** Incorporar rezagos de orden 3 (`100.37 M`), aceleración (`101.17 M`) o ratios de uso de límite (`102.65 M`) de forma aislada sobre el modelo de 4 meses redujo la ganancia respecto del modelo Base limpio (`103.7 M – 103.9 M`).
>
> ### B. Progreso Iterativo hacia el Modelo Final
> 1. **Semillas Individuales en 4 Meses (`LowTop2`):** `102.81 M` de ganancia media con bajo desvío (`0.40 M`).
> 2. **Pruebas en 6 Meses y Combinaciones (`ComboFull`):** Alcanzaron picos altos pero presentaron sensibilidad en el borde del corte entre recreaciones en GPU.
> 3. **Ensamble de 3 Semillas sobre 4 Meses Base (`Modelo M4`):** Promediar las probabilidades de las 3 semillas sobre el modelo limpio de 4 meses (`202103–202106`) eliminó la varianza individual y consolidó una ganancia pública estable de **`103.7 M – 103.92 M`**, siendo elegido como entrega final por su parsimonia, solidez y reproducibilidad.
>
> ---
>
> ## 3. Instrucciones de Reproducción
>
> ### Orden de Ejecución
> 1. **`01_preprocesamiento/01_generar_dataset_fe_v12.py`:** Parte del dataset original de la competencia (`competencia_01.csv`), construye el target binario `clase_peligro` (`BAJA+1` y `BAJA+2` = 1) y genera `competencia_01_fe_v12_NA.csv`.
> 2. **`02_optimizacion_bayesiana/02_optuna_bimodal_v64.py`:** Script de la búsqueda con Optuna (`Optuna_Low`) de donde surgieron los hiperparámetros `LowTop2`. No es necesario volver a ejecutar esta búsqueda para generar el archivo final.
> 3. **`03_modelo_final/03_entrenar_y_predecir_M4_final.py`:** Construye las features sobre las 9 variables principales, entrena (o carga desde `modelos/`) las 3 semillas sobre `202103–202106` y genera el archivo único final `RECREACION_Candidato_B_I11_4M_Base_K11500.csv`.
> 4. **`03_modelo_final/04_verificar_entrega.py`:** Verifica formato (11.500 líneas enteras sin encabezado ni duplicados), pertenencia a `202108` y coincidencia exacta (`SHA256`) con el archivo entregado al bot.
>
> ### Nota sobre Reproducibilidad Exacta y Determinismo en GPU
> El entrenamiento en Google Colab utiliza aceleración por GPU (`device = 'gpu'`, `n_jobs = -1`). Debido a que las reducciones paralelas de histogramas en punto flotante en GPU son asíncronas a nivel de hilos de hardware, re-entrenar desde cero en distintas sesiones de GPU puede variar ~0.4% de los clientes ubicados exactamente en la frontera del puesto `11.500`.  
> Para garantizar **reproducibilidad 100.00% exacta bit a bit (`SHA256` idéntico)** en cualquier entorno, la carpeta `03_modelo_final/modelos/` incluye los 3 árboles entrenados en formato texto (`lgb_seed_*.txt`). Con `USAR_MODELOS_GUARDADOS = True` (activado por defecto), el script `03_entrenar_y_predecir_M4_final.py` reproduce exactamente el mismo archivo enviado al bot en menos de 10 segundos (y cambiando a `False` permite re-entrenar los 3 modelos desde cero).

