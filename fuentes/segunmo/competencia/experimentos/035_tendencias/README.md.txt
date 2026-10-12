# 035 — features de tendencia por variable sobre las 855 columnas

**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; ~40 min): para cada una de las variables con lag2 no excluido por PSI, aceleración (v − 2·lag1 + lag2) y cambio relativo a la media de 3 meses (v / mean(v, lag1, lag2) − 1); E2 (855 columnas) vs E2 + tendencias; multiclase M1 top1 con min_data=50; folds L y B2; 3 semillas pareadas; ganancia = media sobre k=8000..15000 (M ARS).

| | L | B2 |
|---|---|---|
| E2 | 414.1 | 422.9 |
| E2 + tendencias | 415.2 | 425.7 |

E2_tend − E2: **+1.05 (ee 1.56) / +2.84 (0.18), 5/6 pares**.
**Conclusión:** mejora chica y de signo consistente (+1 a +3M locales), pero **no cumple la regla** fijada para esta ronda (> 2 ee en ambos folds: en L son 0.7 ee). Equivale a ~+0.5M en escala Public. No se adopta: reentrenar M2 (~50 min) por un efecto de este tamaño, medido solo en dos folds del mismo mes, sería perseguir ruido. Queda registrada como la mejor candidata si hubiera un mes de validación más.
