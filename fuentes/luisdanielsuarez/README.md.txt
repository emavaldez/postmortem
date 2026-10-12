# DMEyF — 1ra competencia: predicción de bajas (`BAJA+2`) en el mes 202108

Código para reproducir las predicciones sobre el mes **202108** de la primera competencia de DMEyF (Maestría en Ciencia de Datos, FCEN-UBA): predecir qué clientes del paquete premium de un banco argentino abandonan el servicio.

Resumen del método:

1. Preprocesamiento: corrección de `ccajas_depositos` en 202105, clase binaria `BAJA` (`BAJA+1` y `BAJA+2` = 1, `CONTINUA` = 0), variables históricas, ranking con cero fijo y flags `_zero`.
2. Bayesiana de 3 hiperparámetros de LightGBM (**L20**): entrena en 03-04, valida en 06, sin las variables de préstamos.
3. Entrenamiento final (**L22 / L22b**): 45 modelos que solo cambian la semilla, entrenados con los meses 03 a 06, que predicen 08.
4. Ensamble por promedio de probabilidades y archivos de submit (los `N` clientes de mayor probabilidad).

## Estructura

```
exp/
├── L20/codigo/      preprocesamiento + bayesiana (+ etapa 2 con clase artificial, no usada en L22)
├── L22/codigo/      entrenamiento final, ensamble y submits (semillas 0 a 199, se usaron las 33 primeras)
└── L22b/codigo/     entrenamiento final de una segunda VM (semillas 200 a 399, se usaron las 12 primeras)
hiperparametros/
└── L20_e1_hiperparametros.json
```

Cada carpeta `codigo/` es la copia exacta de los scripts que se ejecutaron en ese experimento (cada script guarda una copia de sí mismo al correr).


## Entorno

- Los scripts asumen una carpeta de trabajo plana `~/dmeyf/` y un bucket de GCS. El nombre del bucket está en la constante `BUCKET` de los scripts (`gs://luisdsuarez_buckito2026`).
- Ejecución original: VM de GCP (8 núcleos, 60 GB de RAM).
- L22b se corrió en VM de 4 nucleos


Preparar la carpeta de trabajo copiando **todos** los archivos de las tres carpetas `codigo/` a `~/dmeyf/` (los nombres no se pisan; si `comun_L22.py` está en L22 y en L22b, es el mismo archivo salvo mejoras posteriores: usar la versión más reciente).

## Reproducción paso a paso

Todos los comandos se corren desde `~/dmeyf/`.

### 1. Preprocesamiento (L20)

```bash
python 01_preprocesamiento_L20.py --entrada /ruta/a/competencia_01_ternaria.csv --sin_bucket
```

Genera `~/dmeyf/datasets/L20_dataset.parquet`. Pasos, en este orden:

1. `ccajas_depositos` = NA solo en 202105 (todos eran cero).
2. `clase_binaria`: `BAJA+1` y `BAJA+2` = 1; `CONTINUA` = 0; el resto (mes 07 sin etiqueta y mes 08) = NA.
3. Para todas las columnas salvo las 10 sin historia (edad, antigüedad y fechas relativas): `lag1`, `lag2`, `delta1`, `delta2`, `tend3` (pendiente de la recta de cuadrados mínimos sobre el mes actual y los 2 anteriores) y `avg3` (promedio), todos por unión con (cliente, mes − k), no por desplazamiento de filas.
4. Ranking con cero fijo, por variable y por mes, sobre los 7 grupos (original, lag1, delta1, lag2, delta2, tend3, avg3): los positivos rankean en (0, 1], los negativos en [−1, 0), el cero queda en cero y los NA se conservan. Reemplaza a la variable cruda.
5. Flags `<variable>_zero` (1 si el valor crudo es cero, NA si era NA, 0 en otro caso), sin rankear, para las variables que alguna vez valen cero.

El cálculo vive en `preproc_comun.py`.

### 2. Bayesiana (L20, etapa 1)

```bash
python 02_etapa1_L20.py --sin_bucket
```

- Optuna, primera semilla (878443), 3 hiperparámetros con los rangos del script de GustavoPasquini (`num_iterations` 64-4096, `num_leaves` 16-2048, `min_sum_hessian_in_leaf` 1e-6-0.1, escala lineal), 10 trials aleatorios.
- Entrena con 202103 y 202104, valida con 202106 (AUC), **sin** `cprestamos_personales` y `mprestamos_personales` ni ninguna de sus variantes (16 columnas).
- Resto de los hiperparámetros fijos (ver `PARAMS_FIJOS` en `comun_L20.py`): sin submuestreo, sin pesos de clase.
- La reanudación es reproducible: cada trial depende solo de su número y de los resultados anteriores.

Salida que usa L22: `exp/L20/L20_e1_hiperparametros.json`. (La etapa 2 de L20, con clase artificial, no interviene en L22.)

### 3. Entrenamiento final para 08 (L22 / L22b)

```bash
# VM 1: semillas en las posiciones 0 a 199 de la lista fija
python 01_entrenar_08_L22.py --dataset ~/dmeyf/datasets/L20_dataset.parquet \
       --hiperparametros ~/dmeyf/exp/L20/L20_e1_hiperparametros.json --volumen L22 --desde 0 --n_semillas 200 --sin_bucket

# VM 2 (opcional): posiciones 200 a 399, otro volumen para no pisar archivos
python 01_entrenar_08_L22.py --dataset ~/dmeyf/datasets/L20_dataset.parquet \
       --hiperparametros ~/dmeyf/exp/L20/L20_e1_hiperparametros.json --volumen L22b --desde 200 --n_semillas 200 --sin_bucket
```

- Entrena con los meses 03, 04, 05 y 06 (clase real) y **todas** las columnas, incluidas las de préstamos; los hiperparámetros son los de la bayesiana, encontrada sin ellas.
- Un modelo por semilla; cada predicción sobre 08 se guarda al terminar en `exp/<volumen>/pred_08/prob_<semilla>.npy`. Se puede interrumpir en cualquier momento y retomar con el mismo comando.
- Semillas: las 5 asignadas (878443, 455471, 178447, 235397, 409027) y luego una secuencia determinística (`semillas_n` en `comun_L22.py`: 507928, 515847, ...).

### 4. Ensamble y submits

```bash
# ensamble de todos los modelos disponibles (promedio simple de las probabilidades)
python 02_ensamblar_08_L22.py --volumen L22 --otros L22b

# un único archivo de submit con los N clientes de mayor probabilidad del ensamble
python 03_submit_L22.py --corte 10500 --volumen L22 --otros L22b

# varios submits, uno por línea de corte, con un archivo por semilla (primeras 20), en carpetas separadas
python 04_submits_por_corte_L22.py --volumen L22 --otros L22b --desde 9000 --hasta 13000 --paso 500 --n_semillas 20 --zip
```
