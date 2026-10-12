# 003a — lag1 + delta1 de 50 variables

**Hipótesis:** el valor del mes anterior y su cambio (`x - x_lag1`) dicen más sobre una baja inminente que el valor actual solo.

**Diseño (acordado: híbrido, 20 semillas pareadas, mismos params que el baseline):**
- Variables: top 50 por importancia (gain) de un baseline entrenado solo con 202103+04 (`seleccion_vars.py` → `variables_historia.txt`, `importancias_train.csv`). Se excluyen fechas en días y `fultimo_cierre` (su delta es calendario).
- Features: `v_lag1` (join por cliente y mes anterior; NaN si el cliente no estaba) y `v_d1 = v - v_lag1` → +100 columnas.
- Folds: **A** (train 202103, sin historia: control, delta esperado 0), **B** (03+04 → 202106, NaN nativo en 202103), **Bh** (solo 202104, filas con historia → 202106).
- Control **H1c**: mismas columnas históricas barajadas entre clientes dentro de cada mes (mantiene distribución y NaN, rompe la información). Detecta si la mejora viene del patrón de NaN/calendario.
- Métrica: ganancia con k=11.000, diferencia pareada por semilla vs baseline. `ee` = error estándar de la diferencia (20 semillas).

**Resultados (millones ARS, Δ vs baseline):**

| Variante | A | B | Bh |
|---|---|---|---|
| H1 lag1+delta1 | +0.2 (ee 2.6) | **+4.5** (ee 3.4) | **+5.7** (ee 2.4) |
| H1c control barajado | +0.2 | −25.3 (ee 4.0) | −26.9 (ee 2.5) |

Niveles: baseline A 220.6 / B 361.8 / Bh 346.7; H1 220.8 / 366.4 / 352.4. AUC prácticamente igual (−0.002 a +0.003).

**Lectura:**
- A ≈ 0, como se esperaba (sin historia en train, las columnas no se usan).
- B y Bh coinciden en signo, y Bh (sin NaN artificiales) no es peor que B: no hay evidencia de proxy de calendario. El control barajado **empeora** mucho (−25M), o sea que el modelo sí usa estas columnas y la información real las vuelve útiles.
- Efecto chico y débil: Bh ≈ 2.4 errores estándar, B ≈ 1.3. B y Bh validan el **mismo** mes (202106, atípico por aguinaldo), así que no son evidencia independiente. La mejora en AUC es nula.
- Conclusión provisional: la historia lag1/delta1 aporta poco pero positivo; vale conservarla como base de 003b/003c. No decide nada por sí sola.

**Limitaciones:** train de 1–2 meses; un solo mes de validación con historia (202106). Probar lag2 y medias móviles queda limitado a 2 meses de train completos (05 y 06) en el modelo final.

Reproducir (raíz del repo): `venv/bin/python competencia/experimentos/003a_lag1_delta/seleccion_vars.py` y luego `run.py`.
