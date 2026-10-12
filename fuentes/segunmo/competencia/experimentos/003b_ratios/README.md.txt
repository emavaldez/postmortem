# 003b — cambio relativo (ratio) vs lag1

**Hipótesis:** el cambio relativo `v/lag1 − 1` normaliza por el tamaño del cliente y aporta más que el delta absoluto (`v − lag1`).

**Diseño:** sobre 003a (lag1 + delta1) se agregan 50 columnas `v_r1 = v/lag1 − 1` (NaN si no hay lag o lag = 0), mismas 50 variables. Folds B (03+04 → 202106) y Bh (solo 202104 → 202106); A se omite porque su train no tiene historia. 20 semillas pareadas, ganancia en k=11.000. Baseline y H1 se reutilizan de `003a/resultados.csv`.

**Resultados (millones ARS, diferencia pareada; ee = error estándar):**

| Comparación | B | Bh |
|---|---|---|
| H2 (lag1+delta+ratio) − baseline | +5.7 (ee 2.8) | **+12.5** (ee 2.2) |
| H1 (003a) − baseline | +4.5 (ee 3.4) | +5.7 (ee 2.4) |
| **H2 − H1** (efecto marginal de los ratios) | +1.2 (ee 2.9) | **+6.8** (ee 3.0) |

Niveles: B 361.8 → 366.4 (H1) → 367.5 (H2); Bh 346.7 → 352.4 → 359.2.

**Lectura:** el signo es positivo en ambos folds, pero el aporte marginal de los ratios es significativo solo en Bh (2.3 ee), donde el train es de un solo mes; en B es ruido (0.4 ee). B y Bh validan el mismo mes (202106), así que no son evidencia independiente. Se conserva H2 como set de historia, con cautela.

**Hallazgo estructural (cambia el plan):** con 202103–202106 como únicos meses con target, **no hay forma de validar honestamente lag2, medias móviles de 3 meses ni tendencias**: para tener lag2 el train debería ser 202105 en adelante, y entonces el único mes de validación posible (202106 o posterior con target) rompe la separación de un mes entre train y valid (el target de 202105 mira hasta 202107). Por eso 003c "tendencia/min/max" no se puede medir localmente; solo podría entrar al modelo final sin validación, lo cual no recomiendo.

Reproducir: `venv/bin/python competencia/experimentos/003b_ratios/run.py` (requiere `003a/variables_historia.txt` y `003a/resultados.csv`).
