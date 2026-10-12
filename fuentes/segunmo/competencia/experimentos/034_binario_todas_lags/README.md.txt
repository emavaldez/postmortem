# 034 — binario con ambas bajas sobre las 855 columnas de M2

**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; ~60 min): 3 configuraciones M1 de 005 con los min_data del final (50/65/80), 855 columnas (todas las variables con lags 1 y 2 y diferencias, sin las 8 con PSI>0.20); EM = ensemble multiclase (score condicional, rank medio), EB = ensemble binario BAJA+1/2 (mismas filas, configs e hiperparámetros), M50 = rank 50/50, M67 = 2/3 EM + 1/3 EB. Folds L y B2 (targets solapados en 202107), 3 semillas pareadas, ganancia = media sobre k=8000..15000 (M ARS).

| | L | B2 |
|---|---|---|
| EM (multiclase) | 414.6 | 424.5 |
| EB (binario ambas bajas) | 410.6 | 415.5 |
| M50 | 417.3 | 423.7 |
| M67 | 417.8 | 425.4 |

Diferencias pareadas vs EM (ee; pares positivos de 6): **EB: −4.0 (3.2) / −9.0 (1.9), 1/6**; M50: +2.8 (1.8) / −0.8 (1.8), 4/6; M67: +3.2 (1.3) / +0.9 (1.1), 5/6.
**Conclusión:** con las columnas de M2 el binario de ambas bajas **pierde** frente al multiclase, incluso con 1 mes de train (L), donde con 150 columnas (026) ganaba +6 a +9M. Con más historia en las features, la señal de "propenso a irse" ya está en las columnas y el truco de sumar P1 no aporta. La mezcla M67 mejora en L pero no en B2 (+0.9, 0.8 ee): no cumple la regla (> 2 ee en ambos folds). **No se adopta**; el binario queda descartado como componente.
