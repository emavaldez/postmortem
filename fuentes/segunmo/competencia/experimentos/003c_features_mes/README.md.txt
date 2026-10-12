# 003c — features del mes actual (ratios entre variables y percentiles)

**Reemplaza** al 003c original (tendencias/lag2), que no se puede validar con los meses disponibles (ver 003b/README).

**Hipótesis:** normalizar por tamaño del cliente (ratios) o por posición dentro del mes (percentiles) ayuda al modelo y lo hace más robusto al drift.

**Diseño:** folds A (→202105) y B (→202106), 20 semillas pareadas, ganancia en k=11.000, mismas semillas que 002.
- **C1:** 17 ratios definidos a priori con criterio de negocio, sin mirar la validación (`features.ratios_entre_variables`): ticket promedio de tarjeta, uso del límite, pago/saldo, gasto vs. ingreso, deuda vs. saldo, etc. Denominador 0 → NaN.
- **C2:** percentil (0–1) dentro del mes de las 50 variables de `003a/variables_historia.txt` (`features.rangos_en_el_mes`).
- **C3:** C1 + C2.

**Resultados (millones ARS, diferencia pareada vs baseline; ee = error estándar):**

| Variante | Fold A | Fold B | Promedio A/B |
|---|---|---|---|
| C1 ratios | +0.4 (ee 3.3) | +3.6 (ee 3.0) | +2.0 |
| C2 percentiles | +0.3 (ee 3.2) | −4.6 (ee 3.3) | −2.2 |
| C3 ambas | +0.3 (ee 2.4) | −4.9 (ee 2.8) | −2.3 |

AUC prácticamente sin cambios (−0.002 a +0.002). Niveles: A 220.6 → 221.0/220.9/220.9; B 361.8 → 365.4/357.2/357.0.

**Lectura:** ninguna diferencia supera ~1.7 errores estándar. Los ratios son ligeramente positivos (+3.6M en B, ~1.2 ee): compatible con ruido. Los percentiles no aportan y en B van en contra (−4.6M, ~1.4 ee): no se justifican y agregan 50 columnas. Conclusión: **descartar los percentiles**; los ratios quedan como candidatos débiles y se dejan en el pool de 004 para que el criterio de los canaritos decida si alguno aporta.

**Nota operativa:** la corrida tardó horas de reloj porque la Mac se suspendía; el CPU real fue ~1 h (3 variantes × 2 folds × 20 semillas). Para 004/005 correr con `caffeinate -i -w <pid>` y la tapa abierta.

Reproducir: `venv/bin/python competencia/experimentos/003c_features_mes/run.py`.
