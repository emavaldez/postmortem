# 005 — Optuna sobre LightGBM (con undersampling como hiperparámetro)

**Diseño** (`optuna_run.py`, `reevaluar.py`, `final.py`, `seleccion.py`, `progreso.py`):
- Dos estudios que se alternan trial a trial (SQLite en `artifacts/optuna/005_optuna.db`, no versionado; los hiperparámetros elegidos quedan en `mejores_trials.json`).
  - **M0:** 152 columnas originales + 26 `n_*` de negocio (178 columnas).
  - **M1:** top150 con historia sobre el pool de 345 columnas (selección con importancias de train de cada fold; `sel/`).
- Cada trial sortea `r` (fracción de negativos que se conserva, 0.05–0.5), `num_leaves` (8–256), `learning_rate` (0.01–0.2), `min_data_in_leaf` (20–1000), `feature_fraction` (0.1–1), `bagging_fraction` (0.4–1), `lambda_l1`, `lambda_l2` y `num_boost_round` (100–800).
- Objetivo: índice = media de (ganancia / referencia) en los folds A (→202105) y B (→202106) con 2 semillas de búsqueda; la ganancia de cada fold es la media sobre k = 8.000…15.000 (no se optimiza un único corte). Sampler TPE multivariado (semilla 771227), pruner por percentil tras el fold A. El primer trial es el baseline con r=0.2.
- 241 trials por set en ~8 h (22:08 → 06:08), ~60–70 s por trial.

**Resultado de la búsqueda:** índice del baseline (r=0.2) M0 1.004 / M1 1.015 → mejor M0 1.083, M1 1.093. Los mejores trials convergen a la misma región: lr ≈ 0.010–0.013 (borde inferior del rango), 600–740 rondas (cerca del máximo 800), 95–195 hojas, `min_data_in_leaf` 24–55, `feature_fraction` 0.12–0.35, `bagging_fraction` 0.65–0.83, `r` ≈ 0.07–0.11, lambdas chicas.

**Reevaluación honesta** (10 semillas distintas a las de la búsqueda, folds A, B y Bh —Bh no entró en la búsqueda—; ganancia media sobre k=8.000…15.000, millones ARS):

| Config | A | B | Bh |
|---|---|---|---|
| M0 base (sin undersampling) | 213.7 | 356.6 | 347.5 |
| M0 base + r=0.2 (trial 0) | 220.7 | 368.1 | 351.5 |
| **M0 top1 de Optuna** | 231.9 | 385.0 | 368.3 |
| M1 base (sin undersampling) | 212.8 | 362.6 | 348.2 |
| M1 base + r=0.2 (trial 0) | 220.5 | 370.8 | 363.7 |
| **M1 top1 de Optuna** | 229.7 | 399.0 | 387.4 |
| MIX1 (top1 M0 + top1 M1) | 232.5 | 397.7 | 385.8 |
| **MIX6 (3 mejores de cada set)** | **233.9** | **398.4** | **387.0** |

Diferencias pareadas (media, entre paréntesis el error estándar):
- Tuning vs. baseline r=0.2: M0 +11.2 / +16.9 / +16.8 (ee 2–4); M1 +9.2 / +28.2 / +23.7 (ee ≈1.5). Vs. baseline sin undersampling: +17 a +39M.
- M1 − M0 (tuneados): −2.2 (A, sin historia en train) / +14.0 (B) / +19.1 (Bh): la historia aporta a los dos folds donde el train la tiene.
- MIX6 − M1 top1: +4.1 (A) / −0.5 (B) / −0.4 (Bh): la mezcla de 6 no pierde contra el mejor modelo y cubre el riesgo de que la historia no sirva en 202108.
- AUC: M0 0.890/0.901/0.895, M1 0.891/0.902/0.898, MIX6 0.892/0.903/0.899 (baseline 0.883/0.894/0.888).

**Curva ganancia vs. k de MIX6** (media 10 semillas): A pico en k=8.000 (253M) y cae a 240 en k=11.000; B/Bh pican en k=12.000 (410 / 398M) y a k=11.000 están a −4M del pico. Se usa k≈11.000 como compromiso.

**Cautelas:**
- La reevaluación usa semillas nuevas pero los mismos meses de validación (202105, 202106) que eligieron los hiperparámetros: queda algo de sobreajuste a esos meses (best-of-241 con 2 semillas). Con ganancias de +10 a +40M sobre el baseline el sesgo de selección no explica todo, pero no hay mes limpio de validación; el Public de 202108 es la única medida independiente.
- Los bordes del espacio (lr = 0.01, rondas hasta 800) sugieren que lr más bajo con más rondas podría dar algo más.

Reproducir: `seleccion.py` → `optuna_run.py --horas 8` → `reevaluar.py` → `final.py`.

**Public (entrega 5, `exp005_mix6`):** 96.73M ± 2.75M (baseline 94.2, 004b 94.0). Es el mejor Public hasta ahora (+2.7M vs 004b), en la dirección esperada, pero menor que lo que sugería la validación local (+20 a +40M en mes completo ≈ +5 a +10M en el 25% del Public). Compatible con ruido de muestreo (~5M) y con algo de sobreajuste a 202105/202106.

## Ronda 2 (rangos corridos: lr 0.003–0.03, rondas 300–1800, hojas 16–400, `min_data_in_leaf` 10–300, `feature_fraction` 0.05–0.6, `r` 0.03–0.3, + `max_bin` ∈ {15, 31, 63, 127})
Estudios `M0_r2` y `M1_r2`, 7 h (12:15 → 19:18), 205 trials cada uno (167 / 132 completos). Se anclaron con los 5 mejores de la ronda 1 (reproducen exactamente los mismos índices con las mismas semillas, así que el pipeline es determinista).
- M0: mejor 1.0833 vs. 1.0830 (ancla): sin mejora. M1: mejor 1.0970 vs. 1.0934 (ancla): +0.004, compatible con ruido de selección (2 semillas, 132 trials).
- Un learning rate menor (hasta 0.003) con más rondas (hasta 1800) no mejoró. **La región de la ronda 1 era una meseta**: se queda la ronda 1 (reevaluada con 10 semillas y 3 folds). No se reevalúa la ronda 2.

## Elegir k con probabilidades corregidas por el undersampling (`k_calibrado.py`) — DESCARTADO
**Idea:** el undersampling infla las probabilidades de forma conocida (`q = p/(p + r(1-p))`); invirtiéndola, `p = q·r/(1 - q + q·r)`. Con `p` corregida, cada cliente aporta en esperanza `1.1M·p − 27.5k`, y el k óptimo sería el número de clientes con `p ≥ 0.025`.
**Prueba:** MIX6 (6 configuraciones, 3 semillas) en los folds A, B y Bh; ranking con el promedio de probabilidades crudas, corrección con la `r` de cada configuración.

| Fold | Positivos reales | Esperados (suma de p corregida) | k estimado | k óptimo real | Ganancia en k estimado | Ganancia en k=11.500 | Ganancia máxima |
|---|---|---|---|---|---|---|---|
| A | 870 | 640 | 5.741 | 8.564 | 228.2M | 241.4M | 261.7M |
| B | 1.098 | 727 | 6.140 | 13.184 | 324.0M | 409.8M | 418.4M |
| Bh | 1.098 | 714 | 5.853 | 10.778 | 310.9M | 399.8M | 405.4M |

**Resultado:** el método subestima los positivos en 25–35% y estima un k ≈ 6.000, la mitad del óptimo real; usarlo costaría entre 13 y 89M respecto de k=11.500. Las probabilidades de LightGBM sobre clientes no vistos no están calibradas (el modelo se sobreajusta y las predicciones salen sistemáticamente bajas) y la fórmula supone que el undersampling es el único sesgo. Coherente con la cátedra: el corte por cantidad de envíos funciona mejor que el umbral.
**Lo que queda:** el k óptimo real varía entre meses (8.564 / 13.184 / 10.778), pero k=11.500 queda a 9–20M del máximo en los tres folds. Se mantiene k≈11.500 como compromiso.
