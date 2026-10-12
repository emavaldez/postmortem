# DMEyF 2026 - Primera Competencia: entrega final

**Alumna:** María Mercedes Fiora (`MariaMercedesFiora` en el bot)

**Entrega final (último submit, un solo archivo):** `ensamble_K13000_ENTREGADO.csv`
- 13.000 `numero_de_cliente` de 202108, sin encabezado, una columna.
- Ganancia pública: **105,0225** (Submission ID `1620-1791758548105986`).
- MD5 del archivo: `038d426738376e6ac447e43e8dcbf9a6`

Este es **el único archivo exacto** que se subió como entrega final. El notebook `competencia_FINAL.ipynb` lo reproduce a partir del CSV crudo
y, al final, lo compara con ese archivo.

## Qué hay en esta carpeta

| Archivo | Para qué sirve |
|---|---|
| `competencia_FINAL.ipynb` | **Notebook que reproduce la predicción final** de principio a fin |
| `competencia_FINAL_ejecutado.ipynb` | El mismo notebook **ya ejecutado** (salidas incluidas), con la verificación contra el archivo entregado |
| `ensamble_K13000_ENTREGADO.csv` | El archivo exacto subido como entrega final (el notebook lo usa para verificar) |
| `bo_resultados.csv` | Los 30 trials de la Bayesian Optimization (el trial 27 da los hiperparámetros del modelo final) |
| `bayesiana_competencia_01_ejecutado.ipynb` | Notebook con el **código y la salida de la Bayesian Optimization** (Optuna/TPE, 30 trials, AUC) |
| `requirements.txt` | Versiones exactas de las librerías |
| `datos/LEEME.txt` | Cómo obtener `competencia_01_crudo.csv` (no se sube a git por su tamaño) |

## Cómo reproducir la predicción final

1. Crear el entorno e instalar las librerías (se usó Python 3.12.10):
   ```
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt      # en Linux/Mac: .venv/bin/pip install -r requirements.txt
   ```
2. Poner `competencia_01_crudo.csv` en la carpeta `datos/` (ver `datos/LEEME.txt`).
3. Ejecutar el notebook de arriba hacia abajo (el directorio de trabajo debe ser esta carpeta):
   ```
   .venv\Scripts\python -m jupyter nbconvert --to notebook --execute competencia_FINAL.ipynb --output competencia_FINAL_ejecutado.ipynb --ExecutePreprocessor.timeout=-1
   ```
   Tarda unas 2 horas y media en una CPU de 8 núcleos (preparación de datos y 20 modelos de ~8 minutos cada uno).
4. El resultado queda en `salida/entregas/ensamble_K13000.csv`. La última celda del notebook lo compara con `ensamble_K13000_ENTREGADO.csv`
   e imprime si los clientes, su orden y los bytes del archivo son idénticos.

## Qué hace el modelo

Predice **BAJA+2** del Paquete Premium en 202108 con LightGBM. Sigue la hoja de ruta de la cátedra:

1. **Clase:** `clase_ternaria` calculada mirando el futuro. El modelo se entrena con la clase binaria POS = {BAJA+1, BAJA+2} contra CONTINUA, sin undersampling.
   La ganancia (+1.072.500 por acierto, -27.500 por envío inútil) cuenta solo los BAJA+2.
2. **Data Quality (1.1):** `ccajas_depositos` está rota en 202105 (todos ceros) -> `NA` solo para ese mes.
3. **Data Drifting (1.2):** se eliminan 12 variables (`cprestamos_personales`, `mprestamos_personales` y las 10 con mayor KS entre 202103-05 y 202108)
   y se aplica **ranking mensual a las 41 variables monetarias `m*`** que quedan: de -1 a 1 con el cero fijo si tienen valores negativos, de 0 a 1 si no.
4. **Feature Engineering histórico (1.4):** lags y delta-lags de orden 1 y 2, calculados **después** del ranking, sobre los rangos. 700 features.
   No se usan `numero_de_cliente` ni `foto_mes` como features.
5. **Bayesian Optimization (1.7):** Optuna/TPE, 30 trials, métrica AUC de LightGBM, sin undersampling. Cada trial entrena con 202103-05 y valida con 202106.
   Hiperparámetros fijos: `max_bin=31`, `min_data_in_leaf=0`, `feature_fraction=0,50`, `feature_fraction_bynode=0,20`, `learning_rate=0,005`.
   Hiperparámetros optimizados (trial 27, AUC 0,90468): `num_iterations=1050`, `num_leaves=171`, `min_sum_hessian_in_leaf=7,2872`.
   El código y la salida de esta optimización están en `bayesiana_competencia_01_ejecutado.ipynb`; `competencia_FINAL.ipynb` lee sus resultados guardados (`bo_resultados.csv`)
   porque correrla de cero lleva unas 5 horas.
6. **Final Training (2.1):** 20 modelos con hiperparámetros idénticos y distinta `seed` de LightGBM, entrenados en 202103, 202104, 202105 y 202106.
7. **Scoring (2.2):** se aplican a 202108 y se promedian las probabilidades por `numero_de_cliente`.
8. **Classification (2.3):** se prueban cortes de 12.500 a 14.500 envíos contra el pseudo Kaggle. El entregado es **K = 13.000**.

## Reproducibilidad

- LightGBM en CPU con semillas fijas. Se verificó en la máquina de la autora que reentrenar una semilla da una predicción **idéntica bit a bit** a la guardada.
- En otra máquina (distinto sistema operativo, versión de librerías o cantidad de hilos) los modelos podrían diferir en los últimos decimales,
  lo que en casos extremos cambiaría el orden de clientes con probabilidades casi idénticas en el borde del corte.
- Entorno de la corrida: Windows 10, Python 3.12.10, `lightgbm==4.7.0`, `numpy==2.5.3`, `pandas==3.0.6`.

## Resultados de la verificación

El notebook se ejecutó **de principio a fin desde el CSV crudo** (`competencia_FINAL_ejecutado.ipynb` es esa ejecución, con todas sus salidas):

- Inicio 11-oct-2026 22:42, fin 12-oct-2026 01:06 (2 h 24 min), Windows 10, CPU de 8 núcleos, Python 3.12.10, `lightgbm==4.7.0`.
- **0 celdas con error.**
- El archivo generado (`salida/entregas/ensamble_K13000.csv`) resultó **idéntico byte a byte** al archivo entregado
  (`ensamble_K13000_ENTREGADO.csv`): mismos 13.000 clientes, mismo orden, **MD5 `038d426738376e6ac447e43e8dcbf9a6`** en ambos.
  Las últimas celdas del notebook ejecutado muestran esa comparación.

Nota sobre las semillas: las 20 semillas se entrenan en dos tandas de 10, cada una con su propio `Dataset` de LightGBM (el discretizado de las variables
depende de la primera semilla que usa el `Dataset`). El notebook replica esa estructura para reproducir exactamente el archivo entregado.
