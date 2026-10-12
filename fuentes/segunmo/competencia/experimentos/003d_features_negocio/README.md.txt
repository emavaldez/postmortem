# 003d — sumas, restas y ratios por grupos de negocio

**Hipótesis:** agregados con sentido de negocio (ingresos, egresos, patrimonio, uso del límite total, mix digital/físico, productos activos) resumen mejor al cliente que las columnas sueltas.

**Diseño:** `features.features_negocio` agrega 26 columnas `n_*` definidas a priori sobre las originales (sin historia): ingresos, egresos y neto; payroll sobre ingresos; inversiones, deuda y patrimonio; saldo del paquete y share en dólares; límite y saldo total de tarjetas y su uso; comisiones y share de mantenimiento; descuentos; rentabilidad del mes vs. anual (×12); márgenes sobre rentabilidad; seguros; transacciones digitales y físicas y su share; cantidad de productos activos. Folds A, B, Bh, 20 semillas pareadas, k=11.000; N0 = originales, N1 = originales + `n_*`.

**Resultados (millones ARS, N1 − N0; ee = error estándar):**

| A | B | Bh |
|---|---|---|
| +3.5 (2.4) | +2.5 (3.1) | +4.6 (2.1) |

Niveles: A 220.6 → 224.1; B 361.8 → 364.3; Bh 348.2 → 352.8. AUC +0.001 / +0.001 / +0.002.

**Lectura:** positivo en los tres folds pero chico y con ruido (ninguno pasa de ~2.2 ee; B y Bh validan el mismo mes). Es el mismo patrón débil que los ratios de 003c. Costo bajo y signo consistente, incluso en A, que no depende de la historia. Se incorporan como candidatas al set final (M0 y M1), sin esperar que sean el factor decisivo.

Reproducir: `venv/bin/python competencia/experimentos/003d_features_negocio/run.py`.
