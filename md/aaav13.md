# Alexander Arias — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: aaav13
- Repositorio: https://github.com/aaav13/Competencia_01_DMEyF
- Link posteado: https://github.com/aaav13/Competencia_01_DMEyF.git
- Commit: f18361ab435ae12d79817afcaa00231e2cd0b1b4
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/aaav13/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/aaav13.json

## Resumen

El repositorio contiene tres notebooks de Python, un README de una línea y el archivo de predicción competencia1_aa_v21.csv. Feature_Eng_Competencia_1.ipynb (Google Colab) lee competencia_01.csv con DuckDB, agrega 9 variables calculadas dentro del mes (cocientes de uso de canales digitales, utilización de tarjetas, pago mínimo, productos por antigüedad, cheques rechazados, mora máxima de tarjetas y pasivos sobre activos) y exporta churn_features_lightgbm.csv. src01_preprocessing_v21.ipynb (rutas de Windows) lee ese CSV, entrena un LGBMClassifier con los meses 202103 a 202107 y clase binaria (1 = BAJA+1 o BAJA+2) con n_estimators=500, learning_rate=0.09, max_depth=7 y random_state=42, predice 202108 y escribe los 9.300 clientes de mayor probabilidad en competencia1_aa_v21.csv. Model_Creation.ipynb contiene una búsqueda de hiperparámetros con Optuna (30 pruebas, validación cruzada estratificada de 3 particiones, AUC) que guarda otro modelo (modelo_lgb_churn.pkl); src01_preprocessing_v21.ipynb no lee ese modelo ni el resultado de la búsqueda.

**Qué entrega.** competencia1_aa_v21.csv: los numero_de_cliente de los 9.300 clientes de 202108 con mayor probabilidad. La copia incluida en el repositorio tiene 9.300 líneas, todas numéricas, sin repetidos y sin línea de encabezado; el código la escribe con to_csv(index=False), que antepone el nombre de la columna.

**Cómo se ejecuta.** El README tiene una sola línea: "Cada archivo tiene los pasos a seguir". No indica el orden de los notebooks ni cómo llega churn_features_lightgbm.csv desde Google Drive (donde lo escribe Feature_Eng_Competencia_1.ipynb) a la carpeta local que leen los otros dos. Dentro de cada notebook los comentarios numeran los pasos de la celda.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: target = 1 si clase_ternaria es BAJA+1 o BAJA+2 y 0 en cualquier otro caso, incluidas las filas sin valor de clase (np.where sobre isin).
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106, 202107
- **Meses de validación:** —
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código. Se entrena con todas las filas de 202103 a 202107 (848.635 filas, 9.170 positivas y 839.465 negativas, según la salida guardada en src01_preprocessing_v21.ipynb).
- **Calidad de datos:** No se observa en el código tratamiento de las variables originales. En las variables nuevas, los nulos de los sumandos se toman como 0 con COALESCE y las divisiones por cero se evitan con NULLIF o con CASE.
- **Drifting:** No se observa en el código
- **Variables dentro del mes:** 9 variables creadas en SQL (DuckDB): ratio_digital_trx, share_homebanking, visa_utilization_ratio, master_utilization_ratio, visa_ratio_pago_minimo, productos_por_antiguedad, total_cheques_rechazados, max_delinquency_cards y ratio_pasivos_activos.
- **Variables históricas:** No se observa en el código
- **Selección de variables:** No se observa en el código. Entran todas las columnas menos numero_de_cliente, clase_ternaria, foto_mes y target (161 variables según la salida guardada en src01_preprocessing_v21.ipynb).
- **Optimización de hiperparámetros:** En el camino de la entrega no hay búsqueda: los valores están escritos en src01_preprocessing_v21.ipynb. Model_Creation.ipynb hace una búsqueda con Optuna de 30 pruebas (n_estimators 100-500, learning_rate 0,01-0,1 en escala logarítmica, num_leaves 15-63, max_depth 3-8, min_child_samples 20-200, subsample y colsample_bytree 0,6-1,0) que maximiza el AUC promedio de una validación cruzada estratificada de 3 particiones. Según la salida guardada en ese notebook, la búsqueda devuelve n_estimators=496, learning_rate=0,0917, num_leaves=60, max_depth=7, min_child_samples=155, subsample=0,961 y colsample_bytree=0,936, con AUC promedio 0,9449.
- **Hiperparámetros finales:** LGBMClassifier con n_estimators=500, learning_rate=0.09, max_depth=7, random_state=42 y n_jobs=-1; los demás parámetros quedan en los valores por defecto de la librería.
- **Semillas:** Una semilla: random_state=42 en el LGBMClassifier.
- **Cantidad de semillas:** 1
- **Ensamble:** No se observa en el código. La predicción sale de un único modelo.
- **Corte:** Cantidad fija: CANTIDAD_ENVIOS = 9300, los clientes de 202108 con mayor probabilidad.
- **Validación:** No se observa en el camino de la entrega: src01_preprocessing_v21.ipynb entrena y predice sin medir sobre datos con clase. En Model_Creation.ipynb hay validación cruzada estratificada de 3 particiones (StratifiedKFold con shuffle y random_state=42) medida con AUC, sobre todas las filas con clase_ternaria no nula.
- **Salidas:** churn_features_lightgbm.csv (dataset con las variables nuevas, en Google Drive); modelo_lgb_churn_entrenado.pkl y features_entrenamiento.pkl (carpeta Modelos); competencia1_aa_v21.csv con los numero_de_cliente seleccionados.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)

## Técnicas sólo exploradas

- Optuna (`hiperparametros.optuna`)
- Validación cruzada (`validacion.validacion_cruzada`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: no
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: no
- Entorno declarado: No se declara en un texto. De los notebooks surge: Feature_Eng_Competencia_1.ipynb usa google.colab con Drive montado en /content/drive e instala jupysql y duckdb-engine con %pip, sin versión; Model_Creation.ipynb y src01_preprocessing_v21.ipynb usan la carpeta C:\Users\Admin\Documents\Maestria DM\DM EyF y sus metadatos registran Python 3.14.0. Los paquetes importados (pandas, numpy, lightgbm, optuna, scikit-learn, joblib, duckdb) no llevan versión.

## Pasos del camino de la entrega

1. **Preparación del entorno en Colab.** Monta Google Drive, instala jupysql y duckdb-engine y carga la extensión sql con una conexión DuckDB en memoria. (`Feature_Eng_Competencia_1.ipynb` líneas 1–18)
2. **Lectura del dataset original.** Abre una conexión DuckDB en memoria y crea la tabla dataset_original leyendo /content/drive/MyDrive/DMEyF/competencia_01.csv con read_csv_auto. (`Feature_Eng_Competencia_1.ipynb` líneas 20–40)
3. **Variables nuevas dentro del mes.** Una consulta SQL crea churn_features_final con todas las columnas originales más 9 variables: dos cocientes de transacciones por canales digitales, utilización de límite de Visa y Master, pago de Visa sobre pago mínimo, productos sobre antigüedad, total de cheques rechazados, mora máxima entre las dos tarjetas y margen de pasivos sobre margen de activos. Cada variable usa sólo columnas de la misma fila. (`Feature_Eng_Competencia_1.ipynb` líneas 42–90)
4. **Exportación del dataset con variables.** Copia churn_features_final a /content/drive/MyDrive/DMEyF/churn_features_lightgbm.csv con encabezado y separador coma. (`Feature_Eng_Competencia_1.ipynb` líneas 92–99)
5. **Lectura del dataset con variables.** Lee churn_features_lightgbm.csv desde C:\Users\Admin\Documents\Maestria DM\DM EyF con pandas, dos veces: en la celda 1 mediante la función cargar_y_preprocesar, que imprime dimensiones y primeras columnas, y en la celda 2 de forma directa. (`src01_preprocessing_v21.ipynb` líneas 1–41)
6. **Separación de meses y armado de la clase.** df_train toma foto_mes de 202103 a 202107 y df_agosto toma 202108. La columna target vale 1 cuando clase_ternaria es BAJA+2 o BAJA+1 y 0 en el resto de las filas. (`src01_preprocessing_v21.ipynb` líneas 44–54)
7. **Lista de variables de entrada.** Usa todas las columnas menos numero_de_cliente, clase_ternaria, foto_mes y target, y arma X_train, y_train y X_agosto. (`src01_preprocessing_v21.ipynb` líneas 56–62)
8. **Entrenamiento del modelo.** Ajusta un LGBMClassifier con n_estimators=500, learning_rate=0.09, max_depth=7 y random_state=42 sobre las filas de 202103 a 202107. (`src01_preprocessing_v21.ipynb` líneas 64–75)
9. **Guardado del modelo.** Guarda con joblib el modelo en modelo_lgb_churn_entrenado.pkl y la lista de variables en features_entrenamiento.pkl, dentro de la carpeta Modelos. (`src01_preprocessing_v21.ipynb` líneas 78–81)
10. **Predicción sobre 202108 y corte.** Calcula la probabilidad de la clase 1 para cada fila de 202108, ordena de mayor a menor y toma las primeras 9.300 (CANTIDAD_ENVIOS). (`src01_preprocessing_v21.ipynb` líneas 83–91)
11. **Escritura del archivo de salida.** Escribe la columna numero_de_cliente de los 9.300 seleccionados en competencia1_aa_v21.csv e imprime un resumen de la corrida. (`src01_preprocessing_v21.ipynb` líneas 93–100)

## Archivos

- `README.md` · explicacion · Markdown · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/aaav13/README.md.txt) — Texto de presentación de una línea: "Cada archivo tiene los pasos a seguir".
- `Model_Creation.ipynb` · secundario · Jupyter (python) · 145 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/aaav13/Model_Creation.ipynb.txt) — Notebook que busca hiperparámetros de LightGBM con Optuna (30 pruebas, validación cruzada estratificada de 3 particiones, AUC) sobre todas las filas con clase, entrena un modelo con el resultado y lo guarda en modelo_lgb_churn.pkl. src01_preprocessing_v21.ipynb no carga ese modelo ni lee el resultado de la búsqueda.
- `Feature_Eng_Competencia_1.ipynb` · principal · Jupyter (python) · 99 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/aaav13/Feature_Eng_Competencia_1.ipynb.txt) — Notebook de Google Colab que lee competencia_01.csv desde Drive con DuckDB, agrega 9 variables calculadas con columnas del mismo mes y exporta el resultado como churn_features_lightgbm.csv.
- `src01_preprocessing_v21.ipynb` · principal · Jupyter (python) · 100 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/aaav13/src01_preprocessing_v21.ipynb.txt) — Notebook que lee churn_features_lightgbm.csv, entrena un LGBMClassifier con los meses 202103 a 202107 y clase binaria, predice 202108 y escribe los 9.300 clientes de mayor probabilidad en competencia1_aa_v21.csv.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### Feature_Eng_Competencia_1.ipynb

Notebook de Google Colab que lee competencia_01.csv desde Drive con DuckDB, agrega 9 variables calculadas con columnas del mismo mes y exporta el resultado como churn_features_lightgbm.csv.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–7] Celdas 1 y 2. Monta Google Drive en /content/drive e instala los paquetes jupysql y
#   duckdb-engine con %pip.
#%% celda 1 [código]
from google.colab import drive
drive.mount('/content/drive')

#%% celda 2 [código]
%pip install jupysql
%pip install duckdb-engine

# [Anotación · líneas 9–18] Celda 3. Importa duckdb y pandas, carga la extensión sql de Jupyter, la configura
#   para que las consultas devuelvan DataFrames de pandas sin mensajes adicionales y abre una conexión DuckDB en
#   memoria para la magia %sql. Las celdas siguientes no contienen consultas %sql.
#%% celda 3 [código]
import duckdb
import pandas as pd

%load_ext sql
%config SqlMagic.autopandas = True
%config SqlMagic.feedback = False
%config SqlMagic.displaycon = False

%sql duckdb://

# [Anotación · líneas 20–40] Celda 4, primera parte. Vuelve a montar Drive, arma la ruta
#   /content/drive/MyDrive/DMEyF/competencia_01.csv, abre una conexión DuckDB en memoria con duckdb.connect y
#   crea la tabla dataset_original leyendo el CSV con read_csv_auto.
#%% celda 4 [código]
import duckdb
from google.colab import drive

# 1. Montar Google Drive
drive.mount('/content/drive')

# 2. Definir las rutas
dataset_path = '/content/drive/MyDrive/DMEyF/'
dataset_file = 'competencia_01.csv'
ruta_completa = dataset_path + dataset_file

# 3. Conectar a DuckDB
con = duckdb.connect(database=':memory:', read_only=False)

# 4. Cargar el dataset original usando la ruta completa
print(f"Cargando datos desde: {ruta_completa}...")
con.execute(f"""
    CREATE TABLE dataset_original AS
    SELECT * FROM read_csv_auto('{ruta_completa}');
""")

# [Anotación · líneas 42–54] Comienza la consulta que crea la tabla churn_features_final con todas las
#   columnas originales más las nuevas. Bloque A: ratio_digital_trx = (chomebanking_transacciones +
#   cmobile_app_trx) / ctrx_quarter, con nulos del numerador como 0 y resultado NULL si ctrx_quarter es 0;
#   share_homebanking = chomebanking_transacciones / (cmobile_app_trx + chomebanking_transacciones), con
#   resultado NULL si el denominador es 0.
# 5. Ejecutar la ingeniería de características optimizada para LightGBM
print("Calculando features de ingeniería...")
query_features = f"""
CREATE OR REPLACE TABLE churn_features_final AS
SELECT
    *,

    -- === A. INTENSIDAD DIGITAL Y CANALES ===
    (COALESCE(chomebanking_transacciones, 0) + COALESCE(cmobile_app_trx, 0)) /
    NULLIF(CAST(ctrx_quarter AS DOUBLE), 0) AS ratio_digital_trx,

    COALESCE(chomebanking_transacciones, 0) /
    NULLIF(CAST(cmobile_app_trx AS DOUBLE) + COALESCE(chomebanking_transacciones, 0), 0) AS share_homebanking,

# [Anotación · líneas 56–70] Bloque B. visa_utilization_ratio y master_utilization_ratio dividen el saldo
#   total de cada tarjeta por su límite de compra y valen 0 cuando el límite no es mayor a 0.
#   visa_ratio_pago_minimo divide Visa_mpagado por Visa_mpagominimo y vale 1 cuando el pago mínimo no es mayor a
#   0.
    -- === B. UTILIZACIÓN DE LÍNEAS DE CRÉDITO ===
    CASE
        WHEN Visa_mlimitecompra > 0 THEN Visa_msaldototal / Visa_mlimitecompra
        ELSE 0
    END AS visa_utilization_ratio,

    CASE
        WHEN Master_mlimitecompra > 0 THEN Master_msaldototal / Master_mlimitecompra
        ELSE 0
    END AS master_utilization_ratio,

    CASE
        WHEN Visa_mpagominimo > 0 THEN Visa_mpagado / Visa_mpagominimo
        ELSE 1
    END AS visa_ratio_pago_minimo,

# [Anotación · líneas 72–79] Bloque C: productos_por_antiguedad = cproductos / (cliente_antiguedad + 1).
#   Bloque D: total_cheques_rechazados suma ccheques_depositados_rechazados y ccheques_emitidos_rechazados;
#   max_delinquency_cards toma el mayor entre Visa_delinquency y Master_delinquency. En ambos los nulos se toman
#   como 0.
    -- === C. PROFUNDIZACIÓN Y DENSIDAD DE PRODUCTOS ===
    cproductos / (cliente_antiguedad + 1.0) AS productos_por_antiguedad,

    -- === D. ESTRÉS FINANCIERO Y RIESGO ===
    COALESCE(ccheques_depositados_rechazados, 0) +
    COALESCE(ccheques_emitidos_rechazados, 0) AS total_cheques_rechazados,

    GREATEST(COALESCE(Visa_delinquency, 0), COALESCE(Master_delinquency, 0)) AS max_delinquency_cards,

# [Anotación · líneas 81–90] Bloque E: ratio_pasivos_activos = mpasivos_margen / mactivos_margen, con valor 0
#   cuando mactivos_margen no es mayor a 0. Cierra la consulta sobre dataset_original y la ejecuta en la
#   conexión.
    -- === E. RATIOS FINANCIEROS Y MÁRGENES ===
    CASE
        WHEN mactivos_margen > 0 THEN mpasivos_margen / mactivos_margen
        ELSE 0
    END AS ratio_pasivos_activos

FROM dataset_original;
"""

con.execute(query_features)

# [Anotación · líneas 92–99] Exporta churn_features_final a
#   /content/drive/MyDrive/DMEyF/churn_features_lightgbm.csv con encabezado y separador coma (COPY ... TO) e
#   imprime un mensaje de finalización.
# 6. Exportar el nuevo dataset enriquecido de vuelta a Google Drive
output_file = dataset_path + 'churn_features_lightgbm.csv'
print(f"Exportando resultado a: {output_file}...")
con.execute(f"""
    COPY churn_features_final TO '{output_file}' (HEADER, DELIMITER ',');
""")

print("¡Proceso finalizado con éxito! El archivo ya está disponible en tu Google Drive.")
```

### src01_preprocessing_v21.ipynb

Notebook que lee churn_features_lightgbm.csv, entrena un LGBMClassifier con los meses 202103 a 202107 y clase binaria, predice 202108 y escribe los 9.300 clientes de mayor probabilidad en competencia1_aa_v21.csv.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–26] Celda 1. Define la ruta C:\Users\Admin\Documents\Maestria DM\DM
#   EyF\churn_features_lightgbm.csv y la función cargar_y_preprocesar, que verifica que el archivo exista, lo
#   lee con pandas, imprime la cantidad de filas y columnas y los nombres de las primeras 10 columnas, y
#   devuelve el DataFrame. Al ejecutarse la celda, el resultado queda en df_clientes.
#%% celda 1 [código]
import pandas as pd
import numpy as np
import os

DATA_PATH = "C:\\Users\\Admin\\Documents\\Maestria DM\\DM EyF\\churn_features_lightgbm.csv"

def cargar_y_preprocesar():
    print("Iniciando la carga del archivo CSV...")
    
    if not os.path.exists(DATA_PATH):
        print(f"Error: No se encuentra el archivo en {DATA_PATH}. Verifica la ruta.")
        return None

    # Carga directa del CSV
    df = pd.read_csv(DATA_PATH)
    
    print(f"Dimensiones originales del dataset: {df.shape[0]} filas, {df.shape[1]} columnas.")


    print("Primeras columnas:", list(df.columns[:10]))

    return df

if __name__ == "__main__":
    df_clientes = cargar_y_preprocesar()

# [Anotación · líneas 28–41] Celda 2. Importa pandas, numpy, os, lightgbm y joblib y vuelve a leer
#   churn_features_lightgbm.csv de la misma carpeta, reemplazando df_clientes.
#%% celda 2 [código]
import pandas as pd
import numpy as np
import os
import lightgbm as lgb
import joblib

# 1. Cargar el dataset completo

dir_path = r'C:\Users\Admin\Documents\Maestria DM\DM EyF'
dataset_path = os.path.join(dir_path, 'churn_features_lightgbm.csv') 

print("Cargando el dataset...")
df_clientes = pd.read_csv(dataset_path)


# [Anotación · líneas 44–54] Separa df_train (foto_mes entre 202103 y 202107) y df_agosto (foto_mes 202108).
#   Crea target = 1 si clase_ternaria es BAJA+2 o BAJA+1 y 0 en las demás filas, incluidas las que no tienen
#   valor de clase. Si la columna clase_ternaria no existiera, sólo cambia el nombre guardado en target_col a
#   clase_binaria.
print("Preparando conjuntos de entrenamiento y predicción...")
df_train = df_clientes[(df_clientes['foto_mes'] >= 202103) & (df_clientes['foto_mes'] <= 202107)].copy()
df_agosto = df_clientes[df_clientes['foto_mes'] == 202108].copy()

id_col = 'numero_de_cliente'
target_col = 'clase_ternaria'

if target_col in df_train.columns:
    df_train['target'] = np.where(df_train[target_col].isin(['BAJA+2', 'BAJA+1']), 1, 0)
else:
    target_col = 'clase_binaria' 

# [Anotación · líneas 56–62] Arma la lista features con todas las columnas menos numero_de_cliente,
#   clase_ternaria, foto_mes y target, y construye X_train e y_train para el entrenamiento y X_agosto para la
#   predicción.
ignore_cols = [id_col, target_col, 'clase_ternaria', 'foto_mes', 'target']
features = [col for col in df_train.columns if col not in ignore_cols]

X_train = df_train[features]
y_train = df_train['target']

X_agosto = df_agosto[features]

# [Anotación · líneas 64–75] Crea un LGBMClassifier con n_estimators=500, learning_rate=0.09, max_depth=7,
#   random_state=42 y n_jobs=-1 y lo ajusta con X_train e y_train (meses 202103 a 202107).
# 5. Entrenar el modelo LightGBM con los datos de marzo a julio
print("Entrenando el modelo LightGBM con meses 202103 a 202107...")

modelo = lgb.LGBMClassifier(
    n_estimators=500,
    learning_rate=0.09,
    max_depth=7,
    random_state=42,
    n_jobs=-1
)

modelo.fit(X_train, y_train)


# [Anotación · líneas 78–81] Crea la carpeta Modelos si no existe y guarda con joblib el modelo
#   (modelo_lgb_churn_entrenado.pkl) y la lista de variables (features_entrenamiento.pkl).
modelos_dir = r'C:\Users\Admin\Documents\Maestria DM\DM EyF\Modelos'
os.makedirs(modelos_dir, exist_ok=True)
joblib.dump(modelo, os.path.join(modelos_dir, 'modelo_lgb_churn_entrenado.pkl'))
joblib.dump(features, os.path.join(modelos_dir, 'features_entrenamiento.pkl'))

# [Anotación · líneas 83–91] Calcula con predict_proba la probabilidad de la clase 1 para las filas de 202108
#   y la guarda en probabilidad_churn. Ordena de mayor a menor y se queda con las primeras 9.300 filas
#   (CANTIDAD_ENVIOS).
# 6. Generar probabilidades de churn para agosto (202108)
print("Generando probabilidades de churn para agosto...")
y_prob_agosto = modelo.predict_proba(X_agosto)[:, 1]
df_agosto['probabilidad_churn'] = y_prob_agosto

# 7. Seleccionar los mejores candidatos mediante número fijo de envíos
CANTIDAD_ENVIOS = 9300

clientes_a_estimular = df_agosto.sort_values(by='probabilidad_churn', ascending=False).head(CANTIDAD_ENVIOS).copy()

# [Anotación · líneas 93–100] Escribe la columna numero_de_cliente de los seleccionados en
#   competencia1_aa_v21.csv con to_csv(index=False) e imprime los meses de entrenamiento, la cantidad de
#   clientes seleccionados y la ruta del archivo.
# 8. Exportar el resultado al CSV
output_path = r'C:\Users\Admin\Documents\Maestria DM\DM EyF\competencia1_aa_v21.csv'
clientes_a_estimular[[id_col]].to_csv(output_path, index=False)

print(f"\n¡Proceso finalizado con éxito!")
print(f"Se entrenó con los meses: 202103 a 202107.")
print(f"Se seleccionaron los {len(clientes_a_estimular)} mejores clientes candidatos a estímulo para 202108.")
print(f"Listado guardado en: {output_path}")
```


## Explicaciones del alumno (texto original)

### README.md

> Cada archivo tiene los pasos a seguir

