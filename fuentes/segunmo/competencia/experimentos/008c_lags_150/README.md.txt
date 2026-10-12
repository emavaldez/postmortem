# 008c — historia sobre 142 variables (en vez de 50), con y sin lag2

**Hipótesis:** los compañeros usan hasta 1.500 columnas y el profe recomienda lags 1 y 2: más variables con historia deberían ayudar.

**Diseño** (`run.py`, 10 semillas pareadas, params base, k=11000, ccajas corregida; `resultados.csv`, `comparacion.csv`, `variables_150.txt`):
- **V0** pool actual: lag1/delta1/ratio1 de 50 variables (referencia).
- **V1** lag1/delta1/ratio1 de 142 variables (92 nuevas).
- **V2** V1 + lag2/delta2/ratio2 de las mismas 142 (~1.100 columnas).
- Las 92 nuevas = originales numéricas de mayor importancia según `005_optuna/sel/importancias_Bh.csv` (modelo con solo 202104: ningún mes de validación), sin las variables de tiempo que 003a ya excluía. Salieron 142 y no 150 porque ese ranking no cubre más variables elegibles.
- Folds: B, Bh (lag1 real) y L, B2 (train desde 202105, lag2 real; con el solapamiento de targets de 008b: sirven para diferencias pareadas, no para niveles).

| Variante | B | Bh | L | B2 |
|---|---|---|---|---|
| V0 50 vars lag1 | 368.3 | 362.2 | 365.9 | 384.1 |
| V1 142 vars lag1 | 364.6 | 362.9 | 362.0 | 380.6 |
| V2 142 vars lag1+lag2 | 372.8 | 365.1 | 372.8 | 386.0 |

| Diferencia pareada (M ARS, ee) | B | Bh | L | B2 |
|---|---|---|---|---|
| V1 − V0 (más variables) | −3.6 (5.6) | +0.7 (3.2) | −3.9 (4.8) | −3.5 (4.3) |
| V2 − V1 (lag2) | — | — | **+10.8** (3.2) | +5.4 (4.3) |
| V2 − V0 (neto) | — | — | +6.9 (5.7) | +1.9 (5.5) |

**Conclusión:**
1. **Más variables con historia no ayudan**: los cuatro deltas son ≤ 1 ee y tres son negativos. Sumar ~90 variables × 3 columnas es ruido; el AUC tampoco mejora (−0.0005 a −0.001).
2. **Lag2 sí suma sobre lag1** en ambos folds (+10.8 y +5.4), consistente con 008b (50 variables: +10.8 / −2.4), pero el neto contra el pool actual (V2 − V0) no es significativo (+6.9 y +1.9, ee ≈ 5.5).
3. Lag2 sobre 50 variables rinde igual que sobre 142 con ~600 columnas menos → **se descarta la expansión a 142 variables**; el candidato es el pool actual + lag2 de las 50 (008b), ya validado en el submit de control (Public 98.97M).
Lo que "se dice" de las 1.500 columnas no se reproduce acá con lags de más variables; queda por probar otra clase de columnas (hojas de Random Forest, ver el mensaje del profe 1.5).

## Actualización (2026-10-09) — superado por 028
"Más variables con historia no ayudan" vale para este diseño: **binario, parámetros base, solo lag1/delta1/ratio1 y sin lag2**. En **028** (multiclase con hiperparámetros tuneados, lag1 + lag2 + diferencias, 142 variables, 855–863 columnas, sin selección) usar todas las variables **sí** ayuda: +10.5M sobre el pool de 150 columnas en B2, 8/8 pares; con control de historia barajada (029) y en ensemble (030). La receta ganadora es la que usaban compañeros con Public > 100. Este README conserva el resultado tal como se midió entonces.
