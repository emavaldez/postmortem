# 016 — lag2 en el modelo multiclase

**Hipótesis:** 008b midió lag2 en el binario (+10.8 en L, −2.4 en B2, inconsistente); ¿con el multiclase y el score condicional el lag2 suma?

**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; 95 min): ensemble de las 3 configuraciones M1 de 005 pasadas a multiclase (score condicional, rank medio), con y sin lag2/delta2/ratio2 de las 50 variables (+150 columnas) y control con el bloque lag2 barajado en el train; folds con lag2 real: L (202105 → 202106) y B2 (202104+05 → 202106; 202104 con lag2 NaN, como pasará con 202103–04 en el final); columnas base = `top150_Bh` (selección con 202104 solo); 5 semillas pareadas. Los folds tienen el solapamiento de targets en 202107 (informan la diferencia pareada, no el nivel). Ganancia = media sobre k=8000..15000 (M ARS).

| Variante | L | B2 |
|---|---|---|
| V0 sin lag2 | 393.9 | 410.0 |
| V1 con lag2 | 412.8 | 415.4 |
| V1c lag2 barajado | 390.5 | 390.3 |

Diferencias pareadas (ee): **V1 − V0: +18.9 (3.7) / +5.4 (2.3), 9/10 pares positivos**; V1c − V0: −3.4 (6.5) / −19.7 (3.6), 2/10; **V1 − V1c: +22.4 (7.1) / +25.1 (4.9), 10/10**.

**Conclusión:** en el multiclase el lag2 **sí suma**, a diferencia del binario: +5.4M en B2 (el fold más parecido al final, con parte del train sin lag2) y +18.9M en L, y gana en 9 de 10 pares. El control barajado no mejora (empeora −19.7M en B2), así que la ganancia viene de la información de la historia y no del patrón de NaN. Se adopta lag2 en las configuraciones M1 del final (`--lag2`). Cautelas: el efecto de L (+19M) es inflado por tener una sola mes de train, y los folds tienen targets solapados; lo prudente es esperar algo cercano a B2 (+5M).
