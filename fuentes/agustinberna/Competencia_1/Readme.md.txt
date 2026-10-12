# DMEyF 2026 · competencia_01

## 1. Resumen

|  |  |
|---|---|
| Target de entrenamiento | BAJA+1/BAJA+2 contra CONTINUA con undersampling del 50% solo en la clase CONTINUA |
| Features | Basales, flags, signed ranks por drift y lag/delta 1/2; 785 totales |
| Pesos | 50%/25%/25% de las ganancias; sino Junio contaba 2 veces|
| Búsqueda | 60 trials Optuna TPE, secuencial |
| Selección | 10 configuraciones distintas; un único TopN de su curva ponderada |
| Fit final | Marzo–junio; 20 semillas por configuración = 200 modelos |
| Scoring | Agosto; julio sólo aporta historia de features |
| Ensamble | Promedio uniforme de probabilidades de los 200 modelos |
| Corte | 10.500, congelado antes del entrenamiento final |

## 2. Decisiones

### Calidad, inflación y préstamos

Se corrigen problemas identificados por variable/mes: ccajas_depositos de mayo completo a NA (100% cero); ceros de Visa/Master_Finiciomora en mayo/agosto y de Visa/Master_fultimo_cierre en junio a NA. Internet fuera de 0/1 pasan a NA. 

Los montos nominales se ajustan por IPC. La lista y los valores IPC quedan explícitos en el script.

### Aguinaldo

La señal se calcula con valores crudos antes del IPC. Se marca cuando mpayroll de junio es ≥1,5 veces mayo, O el contador cpayroll_trx es ≥2 veces mayo. Si falta algún valor o mayo no es positivo, la señal individual queda NA; cualquiera positiva activa el flag combinado. Fuera de junio, los flags son cero.


### Features agregadas

Se agregaron de las 152 variables basales sus lags1 y 2, delta lag 1 y 2. Tres flags de aguinaldo y signed ranks de Master_mlimitecompra y Master_Finiciomora. Probé muchas combinaciones de features intra-mes sin mejoras en la ganancia. En total son 785 variables.


### Tres folds, selección y corte

Los folds 0 y 1 dejan un mes intermedio. El fold 2 incorpora mayo y evalúa junio sin gap intermedio. La primera prueba fue solo con folds 0 y 1, dejando el gap como de 1 mes, pero decidí agregar mayo como un tercer fold que entrena con marzo, abril y evalúa junio, para comparar los hiperparámetros con una ventana de entrenamiento más amplia.

Se ejecutan 60 trials secuenciales con el sampler TPE, usando la semilla 700087. Cada trial evalúa una misma combinación de hiperparámetros en los tres folds y maximiza la ganancia ponderada descrita anteriormente.
Busqueda:

| Hiperparámetro | Espacio de búsqueda | Muestreo |
|---|---|---|
| `num_iterations` | 300–2.000 | Entero |
| `num_leaves` | 20–256 | Entero |
| `min_sum_hessian_in_leaf` | 0,01–20 | Logarítmico |
| `learning_rate` | 0,01–0,10 | Logarítmico |
| `feature_fraction` | 0,10–1,00 | Uniforme |
| `min_data_in_leaf` | 100–3.000 | Entero logarítmico |


Se mantienen fijos max_bin=31, bagging_fraction=0,7 y bagging_freq=1.

Se conservan las 10 configuraciones con mayor ganancia ponderada. Para cada una, el número de árboles del entrenamiento final se fija como la mediana de las mejores iteraciones de sus tres folds

Se evalúan N=7.000…15.000 cada 500 clientes. Cada trial maximiza:

`0,50 × G_mayo(N) + 0,25 × G_junio_marabril(N) + 0,25 × G_junio_marabrilmay(N)`.

Estos pesos equilibran mayo/junio; no son pesos óptimos demostrados y los dos folds de junio no son poblaciones independientes. La búsqueda usa la función de curva de ganancia.

Se recuperan las predicciones de los top10, se promedian **dentro de cada fold** y se elige un único N de la curva ponderada del ensamble. 

### Semillas y ensamble

Los 200 modelos combinan diversidad de diez modelos y veinte semillas. Se promedian probabilidades; promediar rangos no superó el mejor máximo de probabilidades. 


## 3. Archivos compartidos

```text
README.md
correr.py
pipeline.py
basal_features.py
```


## 4. Librerias

| Versión |
|---|---:|
| duckdb | 1.5.5 |
| lightgbm | 4.7.0 |
| optuna | 3.6.1 |
| numpy | 2.4.4 |
| pandas | 3.0.1 |
| pyarrow | 24.0.0 |
| psutil | 7.2.2 |
| scikit-learn | 1.9.1 |


## 5. Reproducir 

Poné competencia_01_crudo.csv (se tiene que llamar asi) junto a los .py y ejecutá:
python -u correr.py


Los resultados se guardan en `runs/`:

| Salida | Contenido |
|---|---|
| `envio_agosto_topN.csv` | Único envío final: N IDs enteros, sin encabezado, seleccionados por el promedio de probabilidades de los 200 modelos |
| `scores_agosto_ensemble.csv.gz` | Todos los clientes de agosto y su probabilidad promedio |
| `expanding_trials.csv` | Resultados de los 60 trials de Optuna |
| `ensemble_validation_curve.csv` | Curva de ganancia del ensamble de validación por TopN |
| `frozen.json` y `cut.json` | Configuraciones seleccionadas y corte elegido |
| `models/` y `scores/` | Modelos y predicciones individuales |
| `run.log` | Registro de avance y errores |
| `FINALIZADO.json` | Confirmación de que la corrida terminó |
