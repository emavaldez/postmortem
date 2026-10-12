# 036 — validación limpia en 202107 con BAJA+1 como tarea proxy

**Por qué:** todas las decisiones se tomaron sobre 202105/202106 (dos meses; 202106 tiene aguinaldo y la ola de salidas de clientes con préstamo y mora) y L/B2 tienen los targets solapados. 202107 es el mes más cercano a 202108, sin aguinaldo, con la ola, y de él se conoce BAJA+1 (quién no está en 202108).
**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; ~16 min): binario BAJA+1 vs resto; train 202103–06 (3.985 BAJA+1), valid 202107 (1.103 BAJA+1; 152 en el grupo préstamo&mora); hiperparámetros de M1 top1 de 005; 5 semillas pareadas; ganancia con la misma función sobre BAJA+1 y corte por cantidad (media k=8000..15000); AUC; recall a k=12000 del grupo préstamo&mora y del resto. Sin solapamiento de targets. **Límite:** BAJA+1 no es BAJA+2; sirve para decidir entre variantes de features, no para estimar la ganancia.

| Variante | Ganancia (M ARS) | AUC | Recall k=12000 grupo | Recall resto |
|---|---|---|---|---|
| V0 M1 top150 | 587.8 | 0.9410 | 0.883 | 0.746 |
| V1 + lag2 de 50 variables | 595.8 | 0.9419 | 0.883 | 0.752 |
| V2 855 columnas (M2) | 607.6 | 0.9444 | 0.891 | 0.764 |
| V2 con min_data_in_leaf=50 | 607.2 | 0.9447 | 0.897 | 0.762 |
| V3 855 sin columnas de calendario | 606.1 | 0.9446 | 0.888 | 0.762 |
| V4 top150 sin calendario | 588.3 | 0.9408 | 0.882 | 0.745 |
| V5 855 con peso 2 en 202106 | 606.4 | 0.9442 | 0.896 | 0.760 |

Diferencias pareadas (ee; pares positivos de 5): **V1 − V0: +8.0 (1.7), 5/5**; **V2 − V1: +11.7 (2.1), 5/5**; V2 − V0: +19.7 (2.1), 5/5; V2_md50 − V2: −0.4 (1.7), 1/5; V3 − V2: −1.5 (1.8), 1/5; V4 − V0: +0.5 (1.6), 3/5; V5 − V2: −1.1 (1.4), 1/5.

**Conclusiones**
1. **Confirmado en un mes limpio e independiente**: usar todas las variables con lag1, lag2 y diferencias (M2) supera al pool anterior en +11.7M (5/5 pares, AUC +0.0025), y el lag2 de 50 variables agrega +8.0M sobre el pool sin lag2. Es evidencia independiente de 028/029/030, sin solapamiento de targets, sin aguinaldo y en el mes más cercano a 202108.
2. **`min_data_in_leaf=50` no se confirma** (−0.4 ± 1.7): es neutro acá; el +4 a +6M de 032/033 era específico de L/B2 o del target BAJA+2. No hace daño, pero queda como mejora no confirmada.
3. **Las columnas de calendario no importan** en este mes (−1.5 ± 1.8 al sacarlas; +0.5 ± 1.6 en el pool chico) aunque el valor de 202107 (3) tampoco está en train: el riesgo que planteé en la revisión no se corrobora. No se cambian.
4. **Darle más peso a 202106 (el mes de la ola) no ayuda** (−1.1 ± 1.4), y el modelo ya recupera el 88–90% de las bajas del grupo préstamo&mora a k=12000 contra 75% del resto: las variables de saldo negativo y status ya capturan la ola.
**Decisión:** el final (`exp031`) no cambia. Esto no pudo probar el auxiliar de BAJA+1 con 202107 en M2 (el valid es justamente 202107).
