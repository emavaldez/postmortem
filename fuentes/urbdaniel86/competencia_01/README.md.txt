# Competencia 01

Mi predicción de bajas de clientes para `202108`.

## Cómo correr

Todos los comandos se corren desde esta carpeta (`competencia_01/`).

**1. Crear el environment**

```
conda env create -f env.yaml
conda activate dmeyf-competencia-01
```

**2. Generar el dataset con features**

```
python fe_competencia_01.py --path <ruta>/competencia_01.csv
```

`competencia_01.csv` es el dataset de la competencia con `clase_ternaria` ya calculada.
El script deja `competencia_01_fe.parquet` en la misma carpeta que el CSV e imprime su
ruta al terminar.

**3. Generar la entrega**

```
python modelar_competencia_01.py --modo entrega --desde experimentos/20261011_0840_tres_meses_v1_hess --archivos 1 --dataset <ruta>/competencia_01_fe.parquet
```

Usa los hiperparámetros, el corte y la receta de meses del experimento de
`experimentos/20261011_0840_tres_meses_v1_hess/`. El archivo final queda en
`entregas/DU<fecha y hora>tres_meses_v1_hess/`, con una línea por cliente y sin
encabezado.

## Qué tiene la entrega

### Target

Binario: `BAJA+1` y `BAJA+2` son positivos, `CONTINUA` es negativo. La ganancia, en
cambio, paga solo los `BAJA+2`: +1.072.500 por acierto y −27.500 por cada estímulo a
otro cliente.

### Feature engineering (`fe_competencia_01.py`)

Sobre las 155 columnas originales:

- **Calidad de datos:** `ccajas_depositos` pasa a NULL en `202105`, donde viene en cero
  para todos los clientes.
- **Historia de 12 variables:** `ctrx_quarter`, `mrentabilidad`, `mcomisiones`,
  `mcuentas_saldo`, `mpasivos_margen`, `mactivos_margen`, `mtarjeta_visa_consumo`,
  `mtarjeta_master_consumo`, `cproductos`, `ctarjeta_visa_transacciones`, `mpayroll`,
  `mcaja_ahorro`. A cada una:
  - `lag_1`, `lag_2` y sus deltas contra el valor actual. El lag busca el mes
    calendario exacto: si al cliente le falta un mes, queda NULL.
  - `media_3`, `min_3`, `max_3` y `slope_3` (pendiente por mínimos cuadrados) sobre los
    últimos 3 meses.
- **Rankings dentro del mes** de las 9 variables de monto de la lista, para que el
  modelo no dependa del nivel de precios de cada mes.
- **Combinaciones:** saldo y consumo total de tarjetas (Visa + Master), consumo de
  tarjetas sobre saldo, y comisiones sobre rentabilidad.

En total, 109 features nuevas: 264 columnas, 261 de ellas usadas por el modelo.

### Meses

- **Optimización:** `202103` a `202105` apilados.
- **Entrega:** se reentrena con `202103` a `202106` y se predice `202108`.

### Optimización de hiperparámetros

Optuna (TPE, 40 trials) maximizando el AUC promedio de una validación cruzada de 3
folds. Los folds se parten por cliente (`StratifiedGroupKFold`), para que un mismo
cliente no quede en train con un mes y en validación con otro.

| parámetro | valor |
|---|---|
| `learning_rate` | 0.005 (fijo) |
| `max_bin` | 31 (fijo) |
| `min_data_in_leaf` | 0 (fijo) |
| `feature_fraction` | 0.5 (fijo) |
| `feature_fraction_bynode` | 0.2 (fijo) |
| `num_leaves` | buscado en [4, 200] |
| `num_iterations` | buscado en [200, 10000] |
| `min_sum_hessian_in_leaf` | buscado en [0.0001, 100], escala log |

Las tres mejores configuraciones:

| trial | `num_leaves` | `num_iterations` | `min_sum_hessian_in_leaf` |
|---|---|---|---|
| 18 | 36 | 2375 | 19.22 |
| 34 | 25 | 3760 | 17.61 |
| 38 | 34 | 3627 | 17.38 |

### Ensemble y corte

Las tres configuraciones se reentrenan con 5 semillas cada una: 15 modelos. Cada modelo
convierte sus probabilidades en ranking percentil, y la predicción final es el promedio
de los 15 rankings. Se estimula a los **10.160** clientes con mejor ranking, que es el
corte de máxima ganancia medido en `202106`.

### Medición

El modelo se midió entrenando con `202103`–`202105` y prediciendo `202106`. De
`202106` se excluyeron los clientes que eran positivos en los meses de train: con un
solo mes de distancia siguen presentes, el modelo los vio y no pagan, mientras que en la
entrega real ya no estarían.
