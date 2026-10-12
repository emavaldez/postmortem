# 028 — la receta de los compañeros: lag1, lag2 y diferencias de TODAS las variables (multiclase)

**Motivo:** un compañero con Public > 100 usa lag1, lag2 y diferencias de todas las variables (762 columnas), sin selección. Mi 008c lo había probado en binario y con parámetros base.
**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; ~40 min): multiclase M1 top1 de 005 (score condicional), ccajas corregida, folds con lag2 real en el train: L (202105 → 202106) y B2 (202104+05 → 202106), con targets solapados en 202107 (informan la diferencia pareada, no el nivel); 4 semillas pareadas. V0 = M1 top150; V1 = V0 + lag2/d2/r2 de las 50 variables (lo que usa el final); V2 = pool completo (345 columnas) + lag1/d1 de las 92 variables extra + lag2/d2 de las 142 variables de 008c = **863 columnas, sin selección**.

| Variante | L | B2 |
|---|---|---|
| V0 top150 | 386.7 | 408.9 |
| V1 lag2 sobre 50 variables | 407.7 | 412.3 |
| V2 todas las variables con lags | 409.7 | 422.8 |

Diferencias pareadas (ee; pares positivos de 8): **V2 − V1: +2.1 (0.4) / +10.5 (2.7), 8/8**; V2 − V0: +23.0 (4.1) / +13.9 (1.6), 8/8; V1 − V0: +20.9 (4.1) / +3.4 (2.9), 7/8.

**Conclusión:** en el multiclase con hiperparámetros tuneados, **usar todas las variables con lag1, lag2 y diferencias supera a nuestro pool de 150 columnas con lag2 de 50** (+10.5M en B2, el fold más parecido al final; 8/8 pares). El cuello de botella era la selección de columnas sobre un pool con historia de solo 50 variables. Cautelas: folds con targets solapados (control con la historia barajada en 029) y el final tiene más NaN de historia (202103 sin lags, 202104 sin lag2). Pendiente: 029 (control), 030 (ensemble).
