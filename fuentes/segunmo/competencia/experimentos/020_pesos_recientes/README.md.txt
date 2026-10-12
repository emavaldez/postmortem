# 020 — pesos por cercanía del mes (más peso a los meses recientes)

**Hipótesis:** en 014 duplicar el mes MÁS VIEJO perjudicó (−3.7M); ¿darle más peso al mes RECIENTE mejora?
**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; 35 min): multiclase M1 top1 de 005 (score condicional, ccajas corregida), 6 semillas pareadas; folds con 2 meses de train: B (202103+04 → 202106) y B2 (202104+05 → 202106, targets solapados en 202107). Peso del mes más reciente: 1 (base), 2, 3 (`lgb.Dataset(weight=...)`). Ganancia = media sobre k=8000..15000 (M ARS).

| Variante | B | B2 |
|---|---|---|
| P11 (pesos iguales) | 406.2 | 409.0 |
| P12 (reciente ×2) | 403.4 | 406.4 |
| P13 (reciente ×3) | 403.8 | 405.2 |

Diferencias pareadas (ee): P12 − P11: **−2.70 (0.84) / −2.64 (2.10)**, 2/12 pares positivos; P13 − P11: **−2.34 (1.34) / −3.87 (1.44)**, 2/12.

**Conclusión:** darle más peso al mes reciente **perjudica** (≈ −2.5M en ambos folds). Junto con 014 (más peso al mes viejo: −3.7M), el reparto parejo entre meses es lo mejor; cualquier reponderación pierde. Descartado. El final entrena con pesos iguales.
