# SUPERFINAL — de dónde salen los hiperparámetros

**Qué hice:** una sola corrida con las reglas escritas antes de ver resultados, para dejar de probar cosas de a una. Parte de C3 y decide en orden:

| Etapa | Qué decide | Cómo | Resultado |
|---|---|---|---|
| 0 | Con qué versión del dataset sigue | Corre B1 y elige la corrección que mejora la ganancia; si ninguna, dataset original | — |
| 1 | Qué variables | 10 representaciones (C3 solo, sin préstamos, con rankings, con estados…), 3 semillas y confirmación con 5, midiendo ganancia en junio | Quedó **C3** |
| 2 | Cuánto pesa cada mes de entrenamiento | 4 políticas: todos igual, o abril pesando más que marzo | Quedó **todos igual** (`EXPANDING`) |
| 3 | **Hiperparámetros** | **Optuna, 20 trials**, `TPESampler(seed=17)`, entrena marzo y mide ganancia en mayo; los 3 mejores se revalidan en junio con 5 semillas contra los parámetros base | Tabla de abajo |
| 4 | Corte y confirmación | 20 semillas en junio, ganancia de 8.000 a 15.000 de a 500 | **N = 13.500** |
| 5 | Producción | Entrena marzo–junio, predice agosto, 20 modelos | 98,5050 M ARS públicos |

Espacio que buscó Optuna (`run_superfinal100.py`, función `stage3`): `learning_rate` 0,015–0,06 (log), `num_leaves` 24–128, `min_data_in_leaf` 100–1200 (log), `feature_fraction` 0,55–1, `bagging_fraction` 0,65–1, `lambda_l1` 1e-8–5 (log), `lambda_l2` 1e-8–10 (log), `max_bin` ∈ {63, 127, 255}, rondas 200–550. Lo que maximiza es la ganancia robusta (promedio de la mejor meseta de 3 cortes consecutivos), no el logloss.

El resultado de esa búsqueda está en [`trials.csv`](trials.csv): los 20 trials ordenados por ganancia en mayo. Los tres primeros (trials 19, 14 y 11) se revalidaron en junio con 5 semillas, y el que quedó fue el **trial 11**: tercero en mayo, pero el que mejor anduvo en junio. Sus parámetros son exactamente los del modelo final.

Lo que eligió, y que heredó el modelo final sin volver a optimizar:

| num_iterations | learning_rate | num_leaves | min_data_in_leaf | feature_fraction | bagging_fraction | bagging_freq | max_bin | lambda_l1 | lambda_l2 |
|---|---|---|---|---|---|---|---|---|---|
| 361 | 0.015386775172063426 | 79 | 551 | 0.6866382166758678 | 0.6525364259464963 | 1 | 63 | 5.72231579234109e-06 | 0.013648797015113241 |

Además `objective=binary`, `metric=binary_logloss`, `boosting_type=gbdt`, `deterministic=true`, `num_threads=6`, `force_col_wise=true`.

| Archivo | Qué hace |
|---|---|
| `run_superfinal100_v2_safe.py` | Lanza todo (`--all`) y reanuda si se cortó |
| `superfinal100_v2.py` | Orquesta las etapas; construye un `Dataset` de LightGBM por semilla |
| `run_superfinal100.py` | Las etapas en sí, incluida la de **Optuna** (`stage3`) |
| `super_common.py` | Rutas, ganancia, exportación del CSV |
| `stage5_v2_safe.py` | Producción de agosto con checkpoint por semilla |
| `auditar_superfinal100_v2.py` | Sin entrenar: reconstruye el top-N desde los 20 modelos y compara con el CSV |
| `plan_superfinal100*.json` | Las reglas, congeladas |
| `trials.csv` | Los 20 trials de Optuna de la corrida original, con su ganancia en mayo |

```bash
python run_superfinal100_v2_safe.py --home $HOME --all
python auditar_superfinal100_v2.py --home $HOME
```

Salida: `$HOME/c1superfinal100v2/` con un `RESULT.json` por etapa. El modelo final lee de ahí la lista de variables (`stage1_representation`), la política de meses (`stage2_recency`), los parámetros y rondas (`stage3_tuning`, que también guarda `trials.csv` y `optuna.db`) y el banco final (`stage5_final/bank`).
