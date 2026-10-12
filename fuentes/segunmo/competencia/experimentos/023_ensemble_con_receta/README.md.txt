# 023 — ¿suma la receta del profe al ensemble MIX6 multiclase?

**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; 86 min): las 6 configuraciones de 005 en multiclase (score condicional, rank medio) vs ese ensemble + un modelo de la receta (multiclase **sin undersampling**, 512 hojas, min_sum_hessian 0.05, 800 rondas, lr 0.005, min_data_in_leaf 0, ff 0.5, bynode 0.2; columnas M1 top150); folds A, B, Bh; 3 semillas (SEMILLAS_20[2:5]); ccajas corregida; ganancia = media sobre k=8000..15000 (M ARS).

| Modelo | A | B | Bh |
|---|---|---|---|
| MIX6 multiclase | 242.4 | 403.7 | 397.6 |
| MIX6 + REC (REC pesa 1/7) | 243.0 | 405.5 | 401.1 |
| 50/50 (rank de MIX6 y rank de REC) | 241.5 | 407.1 | 404.9 |
| REC sola (1 modelo) | 237.0 | 405.9 | 400.0 |

Diferencias pareadas vs MIX6 (ee; pares positivos de 9): **MIX6+REC: +0.6 (0.7) / +1.8 (1.1) / +3.5 (0.8), 8/9**; **50/50: −0.9 (1.8) / +3.5 (1.4) / +7.3 (1.3), 7/9**; REC sola: −5.5 (3.6) / +2.2 (2.1) / +2.4 (3.0), 5/9.

**Conclusiones**
1. **La receta aporta diversidad real**: agregarla (aun con peso 1/7) mejora en los tres folds (8/9 pares). Un solo modelo de la receta, sin undersampling, empata con el ensemble de 6 en B y Bh (+2.2 / +2.4M) y pierde en A (1 mes de train).
2. **El peso 50/50 gana más donde hay más datos** (B +3.5, Bh +7.3) y pierde levemente en A (−0.9, dentro del ruido): el final entrena con 4 meses, más cerca de B. Promedio de los 3 folds: 50/50 +3.3M, 1/7 +2.0M.
3. **Cautelas:** 3 semillas, dos meses de evidencia (202105 y 202106), un solo modelo REC por semilla (en el final se promedian varios, lo que debería mejorarlo); el 50/50 se eligió entre dos pesos mirando los tres folds. Esperable en 202108: entre +1 y +3M, con incertidumbre.
**Decisión propuesta:** final = rank 50/50 entre el blend actual (017+010) y un ensemble de modelos de la receta entrenados con 202103–06 (ver `024_final_receta`).
