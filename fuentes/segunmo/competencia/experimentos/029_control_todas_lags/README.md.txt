# 029 — control del 028: historia barajada

**Pregunta:** ¿la ganancia de "todas las variables con lag1, lag2 y diferencias" (028) viene de la información de la historia o de un artefacto de los folds solapados (calendario, patrón de NaN)?
**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; ~35 min): V2 (863 columnas) contra V2c: mismas columnas pero las 668 columnas históricas (lags, diferencias, ratios) barajadas dentro de cada mes en el TRAIN (el valid queda intacto). Se conservan las distribuciones y el patrón de NaN por mes, se rompe el vínculo con el cliente. Folds L y B2, 4 semillas, multiclase M1 top1.

| | L | B2 |
|---|---|---|
| V2 (historia real) | 409.7 | 422.8 |
| V2c (historia barajada) | 336.4 | 391.3 |

V2c − V2: **−73.4 (ee 5.8) / −31.5 (4.5), 0/8 pares positivos**.
**Conclusión:** con la historia barajada la ganancia no solo desaparece sino que cae muy por debajo de la base (V0: 386.7 / 408.9): el modelo no estaba usando un artefacto de calendario o NaN, sino información real del cliente. (La caída por debajo de la base se debe a que el modelo aprende relaciones con ruido en 668 columnas y después se encuentra con historia real en el valid.) El control no elimina el solapamiento de targets, que sigue afectando por igual a todas las variantes, pero descarta la explicación del proxy.
