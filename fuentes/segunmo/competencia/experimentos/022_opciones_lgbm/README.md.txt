# 022 — opciones de LightGBM nunca exploradas (multiclase M1 top1)

**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`): multiclase M1 top1 de 005 (mismas rondas y r), un cambio por variante; folds A, B, Bh; 4 semillas pareadas (SEMILLAS_20[2:6]); ganancia = media sobre k=8000..15000 (M ARS).

| Variante | A | B | Bh |
|---|---|---|---|
| base | 236.0 | 405.1 | 392.0 |
| extra_trees | 233.9 | 396.6 | 387.2 |
| path_smooth=5 | 235.9 | 404.4 | 392.6 |
| path_smooth=20 | 236.1 | 404.6 | 393.2 |
| min_gain_to_split=0.5 | 237.0 | 398.6 | 389.9 |
| extra_trees + path_smooth=5 | 233.6 | 394.1 | 385.6 |

Diferencias pareadas vs base (ee): extra_trees −2.1 (2.5) / **−8.5 (3.6)** / −4.8 (2.7), 3/12; path_smooth5 −0.1 / −0.7 / +0.7, 6/12; path_smooth20 +0.1 / −0.6 / +1.2, 5/12; min_gain0.5 +1.1 / **−6.5 (2.3)** / −2.1, 3/12; extra+smooth5 −2.3 / **−11.0 (2.7)** / −6.4, 2/12.

**Conclusión:** ninguna ayuda. `extra_trees` y `min_gain_to_split` perjudican (−5 a −11M en B); `path_smooth` es neutro (±1M, ruido). Con 6 variantes en juego tampoco hay una ganancia aislada que tentara a adoptar. Descartado: los hiperparámetros de Optuna siguen siendo la mejor región de este espacio.
