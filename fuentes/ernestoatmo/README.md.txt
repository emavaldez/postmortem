# prediccion_final_competencia1
# Replicación de la Predicción Final - Ensamble LightGBM

Esta carpeta contiene el código necesario para replicar de forma exacta la predicción final enviada para la competencia. La estrategia predictiva consiste en un **ensamble de 20 modelos LightGBM**, promediando las probabilidades obtenidas bajo distintas semillas aleatorias, utilizando hiperparámetros hallados mediante optimización bayesiana.

El archivo final seleccionado como entrega oficial es el de **12000 registros** (`prediccion_202108_corte_12000.csv`). Se optó por este corte conservador basándose en la estabilidad histórica del leaderboard y para mitigar el riesgo de *overfitting* a meses atípicos en validaciones locales.

## Estructura de Archivos

* `01_optimizacion_bayesiana.ipynb`: Script de Feature Engineering (Rankings con cero fijo, Lags y Deltas) y búsqueda de hiperparámetros mediante la librería Optuna maximizando el AUC.
* `02_corrida_ensamble.ipynb`: Script final que genera el ensamble de 20 modelos, calcula el promedio de probabilidades, limpia los IDs de notación científica y exporta los archivos de submission en distintos cortes.

## Instrucciones de Replicación

Ambos notebooks están diseñados para ejecutarse de forma secuencial en **Google Colab**. Descargarán automáticamente el dataset crudo (`competencia_01_crudo.csv`) si no se encuentra en el entorno, simulando la estructura de *buckets*.

### Paso 1: Optimización de Hiperparámetros (Opcional para replicación)
El archivo `01_optimizacion_bayesiana.ipynb` contiene el proceso de *tuning*. Se utilizó el algoritmo TPE de Optuna (20 trials) maximizando el AUC. 
Los mejores hiperparámetros identificados por el estudio fueron:
* `n_estimators`: 1273
* `num_leaves`: 721
* `min_sum_hessian_in_leaf`: 0.003055877921643489

### Paso 2: Ejecución del Ensamble y Predicción Final (Replicación Exacta)
Para replicar el archivo entregado, se debe ejecutar directamente el notebook `02_corrida_ensamble.ipynb`. 

**Nota sobre los parámetros:** A partir de los resultados de la optimización bayesiana, se realizó un redondeo manual de los hiperparámetros para la corrida del ensamble. Los parámetros exactos configurados en este notebook son:
* `n_estimators`: 1250
* `num_leaves`: 700
* `min_sum_hessian_in_leaf`: 0.003

El notebook entrenará iterativamente 20 modelos variando la semilla aleatoria de LightGBM (generadas a partir de la semilla base `331613`). Al finalizar, promediará las probabilidades.

### Paso 3: Archivo de Entrega
El script de ensamble generará una serie de cortes. El archivo que representa la predicción final oficial de esta entrega, con los IDs formateados correctamente como texto (sin `.0`), es:

**`prediccion_202108_corte_12000.csv`**
