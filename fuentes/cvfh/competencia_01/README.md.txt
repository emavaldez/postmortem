# Competencia 01 — Predicción de churn bancario

## 1. Descripción del proyecto

Este repositorio contiene el código utilizado para generar las predicciones de la primera competencia de la materia DMEyF, centrada en la detección de churn bancario. En concreto, el objetivo es detectar en agosto los clientes que se darán de baja en octubre, explotando datos de negocio medidos en los seis meses anteriores.

Para la reproducción de los resultados obtenidos en la competencia, plantea una ejecución en dos etapas:

1. **Feature engineering:** Preprocesamiento de la base de datos original (provista por la cátedra) en SQL. En esta etapa se construye la variable objetivo y se generan variables explicativas, tanto históricas como intra-mes.
2. **Entrenamiento y predicción:** Aquí se trabaja con la base preprocesada. Se entrenan tres modelos LightGBM, sobre la base de distintas ventanas temporales. Se los ensambla y se generan las predicciones finales. Su resultado es una lista de IDs de clientes que en agosto muestran potencial de darse de baja pronto, designados destinatarios de una campaña de retención. 

## 2. Estructura del proyecto

El proyecto se organiza de la siguiente manera:

```text
competencia_01/
├── README.md
├── requirements.txt
├── primer_paso_FE_competencia_01.ipynb
├── modelo_final.py
└── data/
    ├── competencia_01_crudo.csv
    └── competencia_01_fev4.parquet
── resultados/
```
Los archivos de código correspondientes a cada una de las etapas aludidas se guardan en el directorio principal. La carpeta `data/` almacena las bases de trabajo. **Importante:** los archivos de datos no se incluyen en el repositorio. La base original debe colocarse en la carpeta `data/` antes de ejecutar el pipeline. El archivo Parquet se genera durante el feature engineering. En la carpeta `resultados/` se guardará el listado de clientes a estimular, que constituye el entregable final de la competencia. 

## 3. Requisitos

Para ejecutar el pipeline se requiere:

- **Python 3.13.12.**
- **DuckDB 1.5.5**, para el procesamiento de datos y la construcción de variables.
- **JupyterLab 4.5.6**, junto con **JupySQL 0.11.1** y **duckdb-engine 0.17.0**, para ejecutar el notebook de feature engineering.
- **LightGBM 4.7.0**, para el entrenamiento de los modelos predictivos.
- **pandas 3.0.3**, **NumPy 2.4.4** y **PyArrow 25.0.0**, para la manipulación de datos y la lectura y escritura de archivos.
- Las dependencias adicionales especificadas en `requirements.txt`.

El proyecto fue desarrollado en Windows 11. Las versiones completas de las librerías utilizadas se detallan en la sección 7.1.

Se recomienda utilizar las mismas versiones de Python y de las principales dependencias para facilitar la reproducción de los resultados.

## 4. Preparación del entorno

Clonar el repositorio y acceder a la carpeta de la competencia.

Instalar las dependencias:

```bash
python -m pip install -r requirements.txt
```

Colocar el archivo `competencia_01_crudo.csv` en el directorio `data/`.

## 5. Feature engineering

Se trabajará con el siguiente **archivo:** `primer_paso_FE_competencia_01.ipynb`

### 5.1. Ejecución

Desde el directorio `competencia_01/`, iniciar JupyterLab:

```bash
jupyter lab
```

Abrir el notebook `primer_paso_FE_competencia_01.ipynb` y ejecutar las celdas secuencialmente.

### 5.2. Procesamiento

El notebook realiza las siguientes operaciones:

**A. Carga de datos**

Importa la base original `competencia_01_crudo.csv` utilizando DuckDB.

**B. Construcción de la variable objetivo**

Genera `clase_ternaria` a partir de la presencia de cada cliente en los meses siguientes, distinguiendo las categorías `BAJA+1`, `BAJA+2` y `CONTINUA`.

Para los últimos meses, la disponibilidad de información futura determina qué clases pueden observarse.

**C. Feature engineering del mes actual**

Genera variables derivadas de los datos del mes de observación, incluyendo agregaciones de productos y transacciones, saldos, consumos, endeudamiento, ratios financieros e indicadores de actividad.

**D. Feature engineering histórico**

Genera automáticamente variables históricas para las columnas numéricas elegibles:

- `lag1`: valor de la observación anterior.
- `lag2`: valor de dos observaciones anteriores.
- `delta1`: diferencia entre el valor actual y `lag1`.
- `delta2`: diferencia entre el valor actual y `lag2`.

El procesamiento se realiza en bloques de 25 variables para gestionar el uso de memoria.

### 5.3. Archivo de salida

El resultado se exporta a:

```text
data/competencia_01_fev4.parquet
```

Formato: Parquet, compresión ZSTD.

Este archivo constituye la entrada para la etapa de entrenamiento y predicción.

## 6. Entrenamiento y predicción

Se trabajará con el siguiente **archivo:** `modelo_final.py`

Esta segunda etapa utiliza la base procesada `competencia_01_fev4.parquet` para entrenar y ensamblar modelos LightGBM y generar el listado de clientes a estimular.

### 6.1. Preparación de los datos

En primer lugar, se construyen dos variables objetivo binarias a partir de `clase_ternaria`:

- `clase_binaria12`: identifica conjuntamente a los clientes `BAJA+1` y `BAJA+2`, frente a `CONTINUA`.
- `clase_binaria2`: identifica exclusivamente a los clientes `BAJA+2`.

Los modelos se entrenan utilizando `clase_binaria12`, mientras que la evaluación de la ganancia se realiza sobre `BAJA+2`, que constituye el objetivo específico de la competencia.

Adicionalmente, se aplica una normalización mensual a las variables numéricas cuyos nombres comienzan con `m` (i.e.: que designan montos susceptibles a ser afectados por la inflación u otros factores de drift), conservando el cero como referencia. Las variables originales normalizadas son reemplazadas por sus correspondientes versiones con sufijo `_norm0`.

Por último, se excluyen las variables relacionadas con préstamos personales, siguiendo una recomendación de la cátedra.

### 6.2. Modelos y conjuntos de variables

Se entrenan tres modelos LightGBM que utilizan diferentes conjuntos de variables explicativas:

| Modelo | Variables utilizadas | Entrenamiento para validación | Entrenamiento final | Columnas del subconjunto inicial
|---|---|---|---|
| `current` | Variables del mes actual, sin históricos | Marzo–mayo | Marzo–junio | 177
| `hist1` | Variables históricas `lag1` y `delta1` | Abril–mayo | Abril–junio | 351 
| `hist2` | Variables históricas `lag2` y `delta2` | Mayo | Mayo–junio | 351

Los tres modelos utilizan la misma variable objetivo binaria y la misma configuración de hiperparámetros. Se probaron configuraciones de hiperparámetros alternativas y específicas para cada modelo, sin que se observe una mejora en su capacidad predictiva.

Durante la etapa de validación, se aplica undersampling de la clase `CONTINUA`, conservando aleatoriamente el 20% de sus observaciones y la totalidad de los casos de baja. Para el entrenamiento final se utiliza la totalidad de las observaciones de los meses seleccionados, sin undersampling.

### 6.3. Configuración de LightGBM

Se utiliza LightGBM con objetivo de clasificación binaria y boosting `gbdt`.

Los hiperparámetros seleccionados son:

| Hiperparámetro | Valor |
|---|---:|
| `num_leaves` | 18 |
| `learning_rate` | 0.00625238 |
| `min_data_in_leaf` | 1748 |
| `feature_fraction` | 0.939774 |
| `bagging_fraction` | 0.376689 |
| `bagging_freq` | 1 |
| `max_bin` | 31 |
| Número de iteraciones | 4928 |

Los valores provienen de la experimentación previa y se incorporan directamente al script. La búsqueda de hiperparámetros no forma parte de este pipeline de reproducción.

### 6.4. Validación y optimización del ensamble

Se utiliza junio de 2021 como período de validación, por ser el último mes para el cual se dispone de la clasificación completa necesaria para evaluar `BAJA+2`.

Cada modelo genera predicciones para junio. A partir de estas se comparan dos estrategias de ensamble:

**Ensamble de probabilidades:** promedio ponderado de las probabilidades predichas por `current`, `hist1` e `hist2`.

**Ensamble de rankings:** promedio ponderado de los rankings percentiles de las probabilidades predichas por los tres modelos.

En ambos casos se buscan combinaciones de pesos entre 0 y 1, con incrementos de 0.05 y sujetos a la restricción de que los tres pesos sumen 1.

La selección se realiza maximizando la ganancia monetaria sobre junio, considerando cantidades de estímulos entre 8.000 y 15.000 clientes, con incrementos de 1.000. Los resultados obtenidos son los siguientes: 

| Parámetro | Ensamble de probabilidades | Ensamble de rankings |
|-----------|---------------------------:|---------------------:|
| Peso Current | 0.35 | 0.15 |
| Peso Hist1 | 0.30 | 0.20 |
| Peso Hist2 | 0.35 | 0.65 |
| Cantidad óptima de envíos | 13.000 | 12.000 |
| Ganancia estimada en validación | 430.100.000 | 429.000.000 |

_La cantidad óptima de envíos identificada en esta etapa corresponde exclusivamente al conjunto de validación de junio de 2021. No debe confundirse con la cantidad de envíos de la predicción final de agosto, que se fijó en 10.500 clientes._

La función de ganancia utiliza los siguientes supuestos:

- Ganancia nominal por acierto: 2.200.000.
- Efectividad del estímulo: 50%.
- Costo por estímulo: 27.500.

Los pesos seleccionados se utilizan posteriormente para generar las predicciones de agosto.

### 6.5. Entrenamiento final y ensamble multisemilla

Una vez seleccionados los pesos del ensamble, se reentrenan los tres modelos incorporando junio a los respectivos conjuntos de entrenamiento.

Se utiliza un conjunto de semillas aleatorias generado a partir de una semilla inicial fija (`42`). Para cada semilla se entrenan nuevamente los tres modelos y se calculan las predicciones correspondientes a agosto de 2021.

Las predicciones se combinan en dos niveles:

1. **Ensamble entre modelos:** para cada semilla se combinan las predicciones de `current`, `hist1` e `hist2` utilizando los pesos seleccionados durante la validación.
2. **Ensamble entre semillas:** los scores de cada ensamble se convierten a rankings percentiles y posteriormente se promedian entre semillas, asignando el mismo peso a cada una.

Se generan por separado los resultados del ensamble de probabilidades y del ensamble de rankings. Para la entrega final, se retiene el ensamble de probabilidades, que demuestra de manera consistente una mejor performance en el __leaderboard__ público. 

### 6.6. Generación de predicciones

Los clientes de agosto se ordenan según el score obtenido en el ensamble multisemilla.

Se seleccionan los primeros 10.500 clientes del ranking, correspondientes a los destinatarios propuestos para la campaña de retención.

Los archivos CSV finales contienen exclusivamente los valores de `numero_de_cliente`, sin encabezado ni índice.

Los archivos se guardan en el directorio `resultados/`.


### 6.7. Ejecución

Una vez generado el archivo `data/competencia_01_fev4.parquet`, ejecutar desde el directorio principal:

```bash
python modelo_final.py
```

El script realiza la preparación de datos, el entrenamiento para validación, la selección de los pesos del ensamble, el entrenamiento final con múltiples semillas y la generación de los archivos de predicciones.

## 7. Reproducibilidad

El repositorio contiene el pipeline utilizado para generar las predicciones finales a partir de la base original proporcionada por la cátedra.

La reproducción requiere ejecutar secuencialmente las dos etapas documentadas:

1. Ejecutar `primer_paso_FE_competencia_01.ipynb` para generar `competencia_01_fev4.parquet`.
2. Ejecutar `modelo_final.py` para entrenar los modelos y generar las predicciones finales.

### 7.1. Dependencias y entorno

El proyecto fue desarrollado en Python, utilizando DuckDB y JupySQL para el procesamiento y la construcción de variables, y LightGBM para el entrenamiento de los modelos predictivos. Se emplearon asimismo pandas y NumPy para la manipulación de datos, PyArrow para la lectura y escritura de archivos Parquet, y JupyterLab para la ejecución del notebook de feature engineering.

Las dependencias necesarias para ejecutar el pipeline se encuentran especificadas en `requirements.txt`.

El entorno local utilizado durante el desarrollo presenta las siguientes características:

| Componente | Versión |
|---|---|
| Sistema operativo | Windows 11 |
| Python | 3.13.12 |
| DuckDB | 1.5.5 |
| pandas | 3.0.3 |
| NumPy | 2.4.4 |
| LightGBM | 4.7.0 |
| PyArrow | 25.0.0 |
| JupyterLab | 4.5.6 |
| JupySQL | 0.11.1 |
| Matplotlib | 3.10.8 |
| Plotly | 7.0.0 |
| SciPy | 1.17.1 |
| Scikit-learn | 1.8.0 |
| Optuna | 4.9.0 |
| DuckDB Engine | 0.17.0 |

Para facilitar la reproducción de los resultados, se recomienda utilizar las mismas versiones de Python y de las principales librerías empleadas durante el desarrollo.

### 7.2. Semillas y parámetros

Se utiliza una semilla inicial fija de `42` para generar la secuencia de semillas empleadas en el ensamble. El script conserva explícitamente los hiperparámetros seleccionados, los períodos de entrenamiento y validación, las reglas de construcción de variables y los procedimientos de combinación de predicciones. Se trabaja sobre 16 semillas. Se seleccionan 10.500 clientes para el estímulo. 

### 7.3. Archivos intermedios y resultados

El procesamiento produce un archivo Parquet con las variables explicativas y la variable objetivo.

Durante el entrenamiento final se guardan las predicciones por semilla en archivos Parquet, que permiten recuperar los rankings individuales y construir el ensamble multisemilla.

El directorio `resultados/` contiene estos archivos intermedios y los CSV finales de clientes seleccionados.

El procedimiento de reproducción debe ejecutarse desde el directorio principal del proyecto para asegurar la correcta resolución de las rutas relativas.

### 7.4. Alcance de la reproducción

El repositorio permite reproducir el procedimiento de feature engineering, entrenamiento, validación, ensamble y generación de predicciones finales, utilizando los hiperparámetros seleccionados durante la experimentación.

No se incluye el proceso completo de búsqueda y optimización de hiperparámetros. Sin embargo, el script de entrenamiento sí reproduce la optimización de los pesos del ensamble y de la cantidad de estímulos sobre el conjunto de validación de junio.

La reproducción requiere disponer de la base de datos original proporcionada por la cátedra. Asimismo, las predicciones pueden presentar diferencias según las versiones de las librerías y el entorno de ejecución, especialmente en el entrenamiento de los modelos LightGBM.

Para verificar la consistencia de los resultados, se recomienda comparar los identificadores de clientes seleccionados en los CSV finales, así como los scores y rankings intermedios.

Como comprobación de reproducibilidad, se compararon los CSV de envíos generados por la implementación original y por la versión definitiva del pipeline utilizando la primera semilla. Se verificó la coincidencia tanto de los identificadores de clientes seleccionados como de su orden de aparición. Esta comprobación corresponde a una ejecución de prueba y no constituye una verificación exhaustiva de las 16 semillas del ensamble final.

## 8. Lessons learned y próximos pasos

La participación en esta competencia implicó un proceso intenso de experimentación y aprendizaje. Las limitaciones de tiempo, de capacidad de cómputo y mi todavía escasa experiencia con herramientas en la nube dejaron una buena lista de experimentos pendientes para la próxima competencia. Entre ellos, destaco:

- **Análisis y selección de atributos (X).** Probé distintas versiones de los modelos excluyendo variables de baja relevancia, sin observar mejoras en su capacidad predictiva. Sin embargo, creo que hay margen para refinar este ejercicio. También incorporé algunas variables que dieron buenos resultados, especialmente ciertos *flags* asociados a señales tempranas de baja, pero me gustaría explorar nuevas posibilidades de manera más sistemática.

- **Estrategias de undersampling.** En este pipeline utilicé distintas estrategias de muestreo para la validación y el entrenamiento final. Me gustaría comparar sus efectos de manera más sistemática y evaluar cómo inciden en la capacidad predictiva y en el ranking de clientes.

- **Transformaciones de variables.** Experimenté con distintas transformaciones de los atributos originales, incluyendo rankings percentiles, indicadores de pertenencia a las colas de las distribuciones y la normalización con cero fijo utilizada en esta versión. Me hubiera gustado disponer de más tiempo para probar otras alternativas, como transformaciones logarítmicas de variables con distribuciones muy asimétricas y colas largas.

- **Optimización de hiperparámetros.** Debido a las restricciones de tiempo y recursos computacionales, limité tanto la cantidad de hiperparámetros explorados como el número de iteraciones de optimización. Considero que existe margen para mejorar este proceso y me gustaría profundizar mi conocimiento de los hiperparámetros de LightGBM y sus efectos sobre el desempeño de los modelos.

En definitiva, esta primera competencia me permitió poner en práctica distintas herramientas y estrategias, pero también identificar aspectos metodológicos y técnicos en los que quiero seguir profundizando. ¡Allá vamos, segunda competencia! _#AguantenLosLunes_
