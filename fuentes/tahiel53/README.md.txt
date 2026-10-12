# Competencia 01 · DMEyF 2026

Predicción de los clientes que se van a dar de baja (BAJA+2) en **202108**, para una campaña de retención.

**Entrega final:** Los **11.750** clientes con mayor probabilidad según un **ensemble de 40 LightGBM**.

![Pipeline](pipeline.png)

---

## Resumen del modelo

| Etapa | Qué se hace |
|---|---|
| **Clase** | Clase ternaria (BAJA+1, BAJA+2, CONTINUA) calculada con los meses siguientes. El modelo es binario: positivos = BAJA+1 y BAJA+2 |
| **Data quality** | `ccajas_depositos` está rota en 202105 (todos ceros), así que se pone `NA` en ese mes |
| **Data drifting** | Se eliminan `cprestamos_personales` y `mprestamos_personales` |
| **Feature engineering** | Lags y delta lags de orden 1 y 2 de todas las variables (`_lag1`, `_lag2`, `_delta1`, `_delta2`) |
| **Ranking por mes** | Para cada variable y cada mes por separado, ranking con cero fijo: positivos equiespaciados en (0, 1], negativos en [−1, 0), el 0 queda en 0 y los NA quedan NA. Reemplaza a los valores originales, incluidos lags y deltas. No se transforman `numero_de_cliente`, `foto_mes` ni `clase_ternaria` |
| **Variables del modelo** | Todas las transformadas y `numero_de_cliente` (no se usa `foto_mes`) |
| **Hiperparámetros fijos** | `max_bin` 31, `min_data_in_leaf` 0, `feature_fraction` 0.5, `feature_fraction_bynode` 0.2, `learning_rate` 0.005, sin bagging, `use_missing` TRUE |
| **Bayesian Optimization** | Optimiza `num_iterations` (64–4096), `num_leaves` (16–2048) y `min_sum_hessian_in_leaf` (1e-6–1). Métrica AUC. Training 202103 + 202104 completo (sin undersampling), testing 202106. 10 iteraciones, semilla 370003. Se guardan los **2 mejores sets** |
| **Modelos finales** | 20 semillas generadas a partir de 370003. Con cada set y cada semilla se entrena un LightGBM en **202103–202106** completo (sin undersampling) y se predice **202108**: 2 sets × 20 semillas = **40 modelos** |
| **Ensemble** | Promedio simple de las probabilidades de los 40 modelos, por `numero_de_cliente` |
| **Corte** | Se envía estímulo a los **11.750** clientes con mayor probabilidad. Se eligió con la curva de ganancia de un backtest (mismos sets y semillas, entrenados en 202103 + 202104 y aplicados a 202106) y con la ganancia pública de varios cortes |

**Los 2 sets de hiperparámetros** (de `exp/mejores_hiperparametros.txt`):

| Set | num_iterations | num_leaves | min_sum_hessian_in_leaf | AUC en 202106 |
|---|---|---|---|---|
| 1 | 3172 | 943 | 0.02584 | 0.92043 |
| 2 | 2033 | 1874 | 0.08125 | 0.91990 |

**Las 20 semillas** (generadas con `set.seed(370003); sample(100000:999999, 20)`):
195361, 236655, 403489, 450862, 490646, 520928, 547247, 593810, 598549, 623217,
674659, 697241, 805062, 907503, 943042, 944552, 962589, 967354, 976901, 991514

---

## Contenido del repositorio

```
.
├── README.md
├── pipeline.png                                  diagrama del proceso
├── 0_preprocesamiento.ipynb                      clase, data quality, drifting, lags y ranking por mes
├── 1_optimizacion_bayesiana.ipynb                BO (10 iteraciones, semilla 370003)
├── 2_modelos_semillas.ipynb                      backtest + modelos finales de un set (se corre 2 veces)
├── 3b_corte_y_entrega_sets_combinados.ipynb      ensemble de los 40 modelos, curva de ganancia y archivo final
├── datos/                                        acá el notebook 0 deja el dataset preprocesado (no se sube)
└── exp/                                          resultados intermedios ("checkpoints")
    ├── BO/BO_log.txt                             las 10 iteraciones de la BO
    ├── mejores_hiperparametros.txt               los 2 mejores sets
    ├── modelos/                                  probabilidad de cada cliente, una por modelo:
    │     final_set{1,2}_s{semilla}.txt             40 modelos finales (202108)
    │     backtest_set{1,2}_s{semilla}.txt          10 modelos del backtest (202106)
    ├── ganancia_vs_envios_sets12.png             curva de ganancia del backtest
    └── entregas/resumen_10102129.txt             resumen de la entrega final
```

Los notebooks se suben **con las salidas de la corrida original**, para que se vea lo que se ejecutó.

---

## Requisitos

- **Jupyter (JupyterLab) con kernel de R** (IRkernel). Se corrió en una VM de Google Cloud con **12 vCPU**.
- **Paquetes de R:** se instalan solos la primera vez que se corre cada notebook:
  `data.table`, `R.utils`, `fst`, `lightgbm`, `bbotk`, `mlr3`, `mlr3mbo`, `mlr3learners`, `DiceKriging` y `ggplot2`.
- **⚠️ El dataset va en la carpeta de arriba del repositorio**, porque los notebooks lo leen de
  `../competencia_01_crudo.csv`:

Cada notebook se abre en JupyterLab desde la carpeta del repositorio y se corre con **Run → Run All Cells**.

---

## Cómo reproducir la entrega

Hay tres formas, según desde dónde se quiera partir. Todas terminan en el mismo archivo.

### Opción A · Desde los modelos ya entrenados (el más rapido)

Usa las predicciones de los 40 modelos que están en `exp/modelos/`.

1. `0_preprocesamiento.ipynb` (~3 min). Genera `datos/dataset_preprocesado.fst`. El notebook 3b lo usa
   para la clase de 202106 del backtest.
2. `3b_corte_y_entrega_sets_combinados.ipynb`. Ya tiene fijado el corte (`CORTES <- c(11750)`).

El archivo de submit queda en `exp/entregas/v3_sets12_40mod_c11750_<fecha-hora>.csv`. El nombre cambia por la
fecha y la hora, pero el contenido es idéntico al entregado: los mismos 11.750 clientes, en el mismo orden.

### Opción B · Reentrenando los modelos con los hiperparámetros de la BO (~17 horas)

Usa los 2 sets de `exp/mejores_hiperparametros.txt`.

1. Borrar la carpeta `exp/modelos/` (si no, el notebook 2 encuentra los modelos y no los vuelve a entrenar).
2. `0_preprocesamiento.ipynb` (~3 min).
3. `2_modelos_semillas.ipynb` con `PARAM$set_hiperparametros <- 1` (~8 h: 5 modelos de backtest de ~11 min
   y 20 finales de ~22 min).
4. `2_modelos_semillas.ipynb` otra vez, con `PARAM$set_hiperparametros <- 2` (~8 h).
5. `3b_corte_y_entrega_sets_combinados.ipynb`.

### Opción C · Desde cero (~18 horas)

1. Borrar `exp/BO/`, `exp/mejores_hiperparametros.txt` y `exp/modelos/`.
2. `0_preprocesamiento.ipynb` (~3 min).
3. `1_optimizacion_bayesiana.ipynb` (~75 min).
4. Seguir desde el paso 3 de la opción B.

**Notas sobre la reproducibilidad:**
- Todo usa semillas fijas, y LightGBM corre con `deterministic = TRUE` y `force_row_wise = TRUE`.
- El notebook 2 quedó guardado con `PARAM$set_hiperparametros <- 2` porque fue la última corrida
  (primero se corrió con 1 y después con 2, como en la opción B).
- Si una corrida se corta, se vuelve a correr el mismo notebook y sigue desde donde quedó.
  La BO retoma desde `exp/BO/BO_log.txt`, y el notebook 2 saltea los modelos que ya están en `exp/modelos/`.
