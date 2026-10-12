# Predicción de baja de clientes - Paquete Premium

Pipeline que, a partir del dataset crudo de clientes, predice qué clientes
van a dar de baja el "Paquete Premium" en los próximos dos meses, y genera
los archivos de submission (listas de clientes a los que conviene ofrecerles
una acción de retención).

## Qué hace cada paso

```
┌──────────────────────┐
│ dataset_crudo.csv     │   un archivo mensual (foto_mes) por cliente,
│ (uno pone el suyo en  │   con ~150 variables: saldos, consumos,
│  data/)                │   tarjetas, préstamos, antigüedad, etc.
└───────────┬───────────┘
            │
            ▼
┌──────────────────────────────┐
│ 01_feature_engineering.py     │  calcula la clase a predecir y arma
│                                │  todas las columnas de entrada
└───────────┬───────────────────┘
            ▼
┌──────────────────────────────┐
│ data/dataset_features.csv     │  un cliente-mes por fila, ~740 columnas
└───────────┬───────────────────┘
            ▼
┌──────────────────────────────┐
│ 02_entrenar_ensamble.py       │  entrena los modelos (opcional: ya vienen
│                                │  entrenados en modelos/, ver más abajo)
└───────────┬───────────────────┘
            ▼
┌──────────────────────────────┐
│ modelos/*.txt, corte_optimo   │
└───────────┬───────────────────┘
            ▼
┌──────────────────────────────┐
│ 03_generar_submission.py      │  predice sobre el mes más reciente y
│                                │  arma los archivos finales
└───────────┬───────────────────┘
            ▼
┌──────────────────────────────┐
│ submissions/*.csv             │  6 archivos: uno por semilla + 1 promedio
└──────────────────────────────┘
```

## Cómo correrlo

```bash
# 1. Poner el dataset crudo en data/dataset_crudo.csv (no viene incluido en el repo)
uv sync

uv run python scripts/01_feature_engineering.py
uv run python scripts/02_entrenar_ensamble.py   # opcional, ver abajo
uv run python scripts/03_generar_submission.py
```

### Sobre `modelos/`

El repo ya incluye los modelos entrenados (15 archivos `lgb_seed_*.txt`, los
hiperparámetros y el corte óptimo) correspondientes al mejor resultado
obtenido hasta ahora. Esto permite correr directamente el paso 3
(`03_generar_submission.py`) sobre un `dataset_features.csv` recién generado
con el paso 1, sin tener que entrenar de nuevo.

Correr `02_entrenar_ensamble.py` es opcional: vuelve a entrenar los modelos
desde cero con la misma configuración (mismos hiperparámetros, mismo
criterio de corte) y **sobrescribe** los archivos de `modelos/`. Sirve para
verificar que el pipeline es reproducible, o para reentrenar si se usa un
dataset distinto (por ejemplo, con meses más recientes).

## El problema que se resuelve

Un cliente es `BAJA+2` si dentro de dos meses deja de tener el Paquete
Premium. La tarea es identificar, con los datos de HOY, a esos clientes para
poder ofrecerles una acción de retención a tiempo. A los que se dan de baja
el próximo mes (`BAJA+1`) ya se llega tarde.

Cada acierto (ofrecerle la acción a alguien que efectivamente se iba a dar de
baja) vale mucho más que el costo de ofrecérsela a alguien que de todos modos
iba a continuar, así que el modelo se evalúa con una métrica de ganancia de
negocio, no con accuracy ni AUC.

## `01_feature_engineering.py`: columnas que arma

| Técnica | Qué hace |
|---|---|
| **Clase objetivo (`clase_ternaria`)** | Para cada cliente y mes, mira si sigue existiendo 1 y 2 meses después. `CONTINUA` si sigue en los dos, `BAJA+1` si deja de existir al mes siguiente, `BAJA+2` si existe uno más pero no dos. |
| **Exclusión de columnas con drift** | 4 columnas (`Master_fultimo_cierre`, `Visa_fultimo_cierre`, `Master_Finiciomora`, `Visa_Finiciomora`) cambian de distribución de un mes a otro de forma brusca y no económica (ver detalle abajo). Se descartan por completo, ni crudas ni derivadas. |
| **`cobra_aguinaldo`** (columna nueva) | 1 si, en un mes de aguinaldo (junio o diciembre), el saldo del cliente sube a 1,4x o más de su propio promedio o máximo habitual (calculado con sus meses anteriores). Es una marca de "este mes el saldo está inflado por el aguinaldo, no por ahorro genuino". |
| **Corrección de `mcuentas_saldo`** | En las filas marcadas con `cobra_aguinaldo=1`, el saldo se divide por 1,111 (un ajuste fijo) antes de seguir usándolo. Evita que el modelo confunda "cobró el aguinaldo este mes" con "mejoró su situación económica". |
| **Lags y deltas, orden 1 y 2** | Para cada columna numérica (incluida `mcuentas_saldo` ya corregida), se agregan 4 columnas: `lag_1_X` y `lag_2_X` (el valor de esa variable 1 y 2 meses atrás) y `delta_1_X` y `delta_2_X` (la diferencia contra esos valores). Le da al modelo la tendencia de cada cliente, no solo su foto del mes actual. |

**Por qué se excluyen esas 4 columnas por drift**: se mide con PSI
(*Population Stability Index*, un indicador estándar para detectar cuándo la
distribución de una variable cambió demasiado entre dos períodos). Dos de
ellas (`Master_fultimo_cierre`, `Visa_fultimo_cierre`) pasan a tener ~77% de
ceros de golpe en un solo mes: un cambio en cómo se generó el dato, no un
cambio real de comportamiento de los clientes. Las otras dos
(`Master_Finiciomora`, `Visa_Finiciomora`) tienen más del 98% de valores
faltantes en todo el dataset.

## `02_entrenar_ensamble.py`: cómo se entrena

| Técnica | Qué hace |
|---|---|
| **LightGBM** | Modelo de árboles de gradient boosting, el estándar para este tipo de datos tabulares. |
| **Clase a predecir** | `BAJA+1` **o** `BAJA+2` cuentan como positivo (no solo `BAJA+2`). Los clientes que se van el próximo mes se comportan de forma parecida a los que se van en dos meses, así que sumarlos da más ejemplos positivos para aprender el patrón. |
| **Submuestreo de la clase mayoritaria** | Los clientes que continúan son muchísimo más numerosos que los que se dan de baja. Cada submodelo entrena con todos los positivos pero solo un 50% al azar de los que continúan: balancea el entrenamiento y lo acelera. `min_data_in_leaf` se ajusta (se divide por ese mismo 0,5) para compensar que hay menos filas. |
| **Ensamble de 5 semillas × 3 submodelos** | Por cada una de las 5 semillas, se entrenan 3 submodelos (cambiando una semilla interna, que varía qué filas y qué columnas ve cada árbol) y se promedian sus probabilidades. Reduce la varianza de confiar en un solo entrenamiento. |
| **Control de calidad (holdout)** | Antes de entrenar el modelo final, se entrena una versión que deja afuera el mes más reciente con clase conocida, y se mide la ganancia real ahí, para confirmar que el modelo generaliza antes de usarlo. |
| **Elección del corte** | Con esa medición, se recorre la cantidad de clientes a estimular (entre 8.000 y 15.000, de a pasos de 250) y se elige la que da mayor ganancia promedio entre las 5 semillas. |
| **Modelo de entrega** | Se reentrena con el mismo procedimiento pero usando todos los meses con clase conocida (incluido el que se usó de holdout), para aprovechar el máximo de información disponible. |

Los hiperparámetros de LightGBM (`num_leaves`, `learning_rate`,
`min_data_in_leaf`, `feature_fraction`, `bagging_fraction` y la cantidad de
árboles) ya vienen elegidos en `modelos/mejores_hiperparametros.json`. No se
buscan de nuevo en este script. La búsqueda que originó esos valores está
en `optimizacion_hiperparametros/`, con su propio README.

## `03_generar_submission.py`: cómo se arma la entrega

Predice sobre el mes más reciente del dataset, el único sin clase conocida.
Para cada semilla se promedian sus 3 submodelos; se toman los
`corte_optimo` clientes con mayor probabilidad y se guardan en un CSV (sin
encabezado, un `numero_de_cliente` por línea). Además se genera un sexto
archivo que promedia la probabilidad de las 5 semillas antes de rankear.

## Sensibilidad del corte

El corte se elige recorriendo la cantidad de clientes a estimular entre
8.000 y 15.000 (de a pasos de 250) y midiendo la ganancia real en el
holdout. La curva es bastante plana alrededor del óptimo: entre 10.750 y
12.000 la diferencia es menor al 1%.

| Clientes | Ganancia (holdout) |
|---|---|
| 8.000 | $368M |
| 9.500 | $379M |
| 10.750 | $391M |
| **11.500** | **$392M (máximo)** |
| 12.750 | $389M |
| 14.000 | $382M |
| 15.000 | $381M |

## Qué se probó y no funcionó

Antes de llegar a esta receta se probaron variantes de feature engineering
y de algoritmo que no mejoraron (o empeoraron) el resultado público. Se
deja documentado para no repetirlas:

| Variante probada | Resultado público | Contra la receta actual |
|---|---|---|
| Random Forest en vez de LightGBM, mismas columnas | 81,6 | peor |
| Agregar columnas de ratios entre variables del mismo mes (uso de límite de tarjeta, carga de préstamos sobre ingreso, etc.) | 85,1 a 92,6 según la base | peor en los dos casos probados |
| Ampliar la ventana de referencia del aguinaldo a más meses | 85,1 (combinado con los ratios de arriba) | peor |
| Selección de columnas por importancia contra variables aleatorias ("canaritos") | 66,4 | mucho peor |
| Submuestreo de la clase mayoritaria SIN el cambio de etiqueta (BAJA+1 y BAJA+2 positivos) | 93,3 | parecido, sin mejora clara |

Lo que sí mejoró, y es lo que incorpora la receta actual: tratar `BAJA+1` y
`BAJA+2` como positivos juntos, submuestrear la clase mayoritaria, y
descartar las columnas con drift detectado por PSI. Combinar probabilidades
de varias recetas de feature engineering distintas también sumó (95,2 de
una receta sola contra 96,6 combinando tres), aunque menos que el cambio de
etiqueta y submuestreo.

## Estructura del repo

```
competencia_01/
├── data/                        dataset_crudo.csv (lo pone el usuario) y
│                                dataset_features.csv (lo genera el paso 1)
├── modelos/                     hiperparámetros, corte óptimo y los 15
│                                modelos ya entrenados (5 semillas × 3)
├── optimizacion_hiperparametros/  búsqueda que originó esos hiperparámetros
│                                (base de Optuna + script), con su README
├── prediccion_final/            el CSV que se entregó y su hash SHA-256
├── scripts/
│   ├── config.py                rutas y constantes
│   ├── comun.py                  funciones compartidas
│   ├── 01_feature_engineering.py
│   ├── 02_entrenar_ensamble.py
│   └── 03_generar_submission.py
└── submissions/                  salida de 03_generar_submission.py
```
