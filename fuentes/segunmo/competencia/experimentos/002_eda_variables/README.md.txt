# 002 — EDA de variables

Notebook: [`eda.ipynb`](eda.ipynb) (ejecutado, con gráficos) · Scripts: `run.py` (5 semillas), `run_potencia.py` (20 semillas) · Código reutilizable: `src/features.py`, `src/drift.py`, `src/validacion.py`.

## Hipótesis
Algunas variables (en especial las de fecha en días) mezclan "quién es el cliente" con "en qué mes estamos"; transformarlas podría mejorar la ganancia y la robustez ante 202108.

## Hallazgos
1. `fechaalta`, `Fvencimiento`, `Finiciomora` y `cliente_antiguedad` son **tiempo transcurrido**: para el mismo cliente avanzan 30/31 días (1 mes) por mes. `Finiciomora` solo existe para clientes en mora (~0.5%); su máximo crece ~30 por mes.
2. `Master/Visa_fultimo_cierre` es **calendario puro**: ~77% de los clientes comparte el mismo valor en cada mes (1, 2, 5, 0, 3, 6 de marzo a agosto) y otros dos ciclos de facturación a +7 y +21 días. Identifica el mes (AUC adversarial = 1.0); 202108 usa un valor (6) ausente en train.
3. **Artefacto de Visa en 202105 y 202108**: ~3.200 clientes (2%) con `Visa_delinquency=1` y `Visa_Finiciomora=0`; cero filas así en los otros meses. Su tasa de BAJA+2 es normal (0.81% en 202105) → no es mora real.
4. Centinela "sin fecha" (≈ −2.914.000) en `Visa_Fvencimiento` (~450 clientes por mes).
5. **202108 no presenta drift poblacional importante** (PSI máx. 0.07 vs 202107, 0.06 vs 202105; sin calendario, AUC adversarial 0.85–0.92 por diferencias nominales/de nómina). El drift fuerte (`mpayroll`, `cpayroll_trx`, probable aguinaldo) cae en **202106**, el mes del fold B, que por eso no es representativo (fold B ≈ 360M vs fold A ≈ 220M).
6. Las variables de tiempo transcurrido tienen peso real en el baseline (puestos 14–25 de 152). Hay 5 variables con importancia 0; las 30 mejores explican ~70% y las 60 mejores ~90% de la ganancia (insumo para el experimento 004).

## Diseño del experimento
Una transformación por vez contra el baseline 001, en los 2 folds de `PLAN.md`, ganancia con k=11000, diferencias pareadas por semilla.
- V1 `cierre_relativo`: `fultimo_cierre` − moda del mes · V2 `fechas_absolutas`: fecha de foto − días (centinela → NaN), antigüedad → mes de ingreso · V3 `artefacto_visa`: filas con `Finiciomora==0` → NaN · V4 sacar `fultimo_cierre` · V5 = V1+V2+V3.
- Primero 5 semillas (`run.py`); como las diferencias quedaron en el ruido, las variantes principales se repitieron con 20 semillas (`run_potencia.py`: las 5 propias + 15 derivadas de la primera, `RandomState(852583)`).

## Resultados (ΔGanancia k=11000 vs baseline, millones, ± error estándar de la diferencia con 20 semillas)
| Variante | Fold A | Fold B |
|---|---|---|
| V2 fechas absolutas | −0.7 ± 2.4 | −0.4 ± 3.6 |
| V4 sin `fultimo_cierre` | −0.6 ± 2.8 | −4.2 ± 2.3 |
| V5 V1+V2+V3 | +1.6 ± 2.6 | −3.3 ± 3.2 |

Baseline con 20 semillas: A 220.6M ± 9.6M, B 361.8M ± 9.9M (con 5 semillas B daba 354.4M). Con 5 semillas, V2 en el fold B parecía +13.4M; con 20 es −0.4M: era ruido.

## Conclusión y receta
- **Ninguna transformación mejora la ganancia**; se mantienen las variables crudas. Las funciones quedan en `src/features.py`.
- **Receta metodológica:** para decidir cambios de pocos millones usar ≥ 20 semillas y diferencias pareadas; con 5 semillas el ruido de la media es de ±4–8M.
- Para 003 (lags/deltas): no calcular deltas de las variables de tiempo transcurrido (su delta es constante) ni de `fultimo_cierre`.
- Pendiente en 202108 (resuelto): el artefacto de Visa está presente en scoring y en un solo mes de train (202105). El final entrena con 202103–06, o sea que lo incluye; las transformaciones V1–V5 de este experimento no mejoraron (ver tabla), así que no se trató.
