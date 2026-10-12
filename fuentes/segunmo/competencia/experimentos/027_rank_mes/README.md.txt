# 027 — rank del mes en [−1, 1] REEMPLAZANDO a las variables crudas

Motivo: los montos son nominales (la inflación los corre ~1.7% por mes) y un corte aprendido en 202103–06 no significa lo mismo en 202108; un compañero preguntó por rankings en [−1, 1]. 003c solo *agregó* percentiles de 50 variables (−4.6M en B).
**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; 45 min): multiclase M1 top1 de 005 (score condicional), columnas M1 top150 por fold; V1 reemplaza todas las continuas (>20 valores distintos) por 2·percentil−1 dentro de su foto_mes; V2 reemplaza solo las de monto (nombre que empieza con m, Master_m o Visa_m, incl. lags/deltas); NaN se conserva. Folds A, B, Bh; 5 semillas pareadas. El fold B valida a 2 meses del último mes de train, como el final.

| Variante | A | B | Bh |
|---|---|---|---|
| V0 crudas | 237.4 | 405.8 | 392.7 |
| V1 rank de todas las continuas | 233.6 | 386.6 | 374.7 |
| V2 rank solo de montos | 236.6 | 400.0 | 385.6 |

Diferencias pareadas (ee): V1 − V0: **−3.8 (1.2) / −19.3 (2.0) / −18.0 (1.5), 0/15**; V2 − V0: −0.8 (0.8) / −5.9 (0.6) / −7.1 (1.9), 3/15.

**Conclusión:** normalizar por rank del mes **perjudica con claridad** (0/15 pares positivos con V1). El nivel absoluto de los montos lleva información útil (tamaño del cliente) que el rank destruye, y eso pesa más que la protección contra la inflación. Tampoco sirve parcialmente (solo montos: −6 a −7M). Descartado, junto con 003c; el nominal crudo se mantiene.
