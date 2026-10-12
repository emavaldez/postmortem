# 030 — ensemble con "todas las variables con lags"

**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; ~45 min): las 3 configuraciones M1 de 005 (top1-3) en multiclase, score condicional, rank medio; E1 = M1 top150 + lag2 de 50 variables (lo que usa el final), E2 = 863 columnas (028), E12 = mezcla 50/50 de los rankings; folds L y B2 (targets solapados en 202107), 3 semillas pareadas.

| Ensemble | L | B2 |
|---|---|---|
| E1 (final actual) | 408.7 | 413.9 |
| E2 (todas las variables con lags) | 412.3 | 422.7 |
| E12 (50/50) | 412.5 | 419.8 |

Diferencias pareadas vs E1 (ee): **E2: +3.6 (0.9) / +8.8 (3.1), 6/6 pares**; **E12: +3.9 (0.3) / +5.9 (1.4), 6/6**.
**Conclusión:** la ventaja de las 863 columnas se mantiene en ensemble (+3.6 y +8.8M). La mezcla 50/50 con E1 conserva la mayor parte (+3.9 / +5.9M) y reduce la dependencia de un solo set de columnas; E2 solo es mejor en B2 (+2.9M sobre la mezcla) y empata en L. Decisión: M2 (E2) como componente principal del final, con un peso mayoritario y el resto del blend actual como cobertura (`031_final_todas_lags`).
