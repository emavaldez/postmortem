# 008b — lag2, delta2 y ratio2 (+150 columnas)

**Hipótesis (profe, 1.4):** sumar lags y delta lags de orden 2 es superador.

**Problema de validación:** en los folds A/B/Bh el lag2 del train es todo NaN (202103/04 no tienen 202101/02), así que el modelo nunca lo ve y no se puede medir. Se usaron folds con train desde 202105 (lag2 real = 202103):
- **L:** train 202105 → valid 202106.
- **B2:** train 202104+05 → valid 202106 (202104 con lag2 NaN).

**Limitación:** el target de 202105 mira 202106–07 y el de 202106 mira 202107–08, o sea se solapan en 202107 (falta el mes de separación del resto del esquema). Afecta igual a todas las variantes: la diferencia pareada es informativa, el nivel absoluto no es comparable con A/B/Bh. `ccajas_depositos` va corregida (NA en 202105).

**Variantes** (20 semillas pareadas, params base, k=11000, pool de 345 columnas): V0 lag1 | V1 +lag2 (+150 cols) | V1c +lag2 con el bloque barajado dentro de cada mes (control).

| Variante | L (M ARS) | B2 (M ARS) |
|---|---|---|
| V0 lag1 | 363.6 | 387.9 |
| V1 lag2 | 374.4 | 385.5 |
| V1c lag2 barajado | 341.4 | 363.1 |

| Diferencia pareada | L (ee) | B2 (ee) |
|---|---|---|
| V1 − V0 | **+10.8** (3.3) | −2.4 (3.1) |
| V1c − V0 | −22.2 (4.3) | −24.8 (3.2) |
| V1 − V1c | +33.0 (4.2) | +22.4 (2.9) |

**Conclusión:** el lag2 trae información real (le gana al control barajado por 22–33M, AUC +0.003–0.005), pero **sobre lag1 el aporte es inconsistente**: +10.8M en L (3 ee) y −2.4M en B2 (no distinguible de 0). Con 150 columnas más, el costo de ruido es grande (el control barajado pierde 22–25M), así que el beneficio de lag2 se gasta en parte en ese costo. L entrena con lag2 completo; B2 tiene la mitad de las filas de train con lag2 NaN, y el modelo final (202103–06) tendrá aún más NaN (202103 y 202104).
**Decisión provisoria:** candidato débil. No lo adopto solo; entra a 008c (lags 1 y 2 sobre ~150 variables) junto con selección de columnas (top por importancia) para controlar el costo de ruido.
