# 011 — agregados de cambios, lags de features derivadas, eventos de productos, comisiones normalizadas

**Hipótesis (discusión de FE del 07-oct):** (V1) un conteo de "cuántas variables cayeron a la mitad / pasaron a cero" resume una señal difusa que un árbol no puede construir; (V2) las features que más pesan son las derivadas (`n_*`, `r_*`) y nunca les calculamos historia; (V3) los eventos de productos (perdidos/ganados, dejó de cobrar sueldo, dejó de usar tarjeta/homebanking) son el mecanismo típico de fuga; (V4) normalizar `mcomisiones_mantenimiento` por la mediana del mes corrige el salto nominal que detectó C1.

**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; ~100 min): cada idea se suma por separado a la misma base multiclase B1 (score P(BAJA+2)/(1−P(BAJA+1)), hiperparámetros y rondas de M1 top1, top150 por fold, ccajas corregida), folds B y Bh, 10 semillas nuevas pareadas, ganancia = media sobre k=8000..15000 (M ARS). Código nuevo en `src/features.py` (`agregados_cambios`, `eventos_productos`, `comisiones_normalizadas`) y `src/historia.py` (`lags_crudos`, `lag_derivadas`).

| Variante | Cols | B | Bh |
|---|---|---|---|
| V0 base | 150 | 406.9 | 394.8 |
| V1 agregados `g_*` | +6 | 407.0 | 397.4 |
| V2 lags de 20 derivadas | +60 | 397.9 | 390.7 |
| V3 eventos `e_*` | +8 | 402.4 | 395.7 |
| V4 comisiones norm. | ±0 | 406.7 | 394.6 |

Diferencia pareada vs V0 (M ARS, ee) y pares positivos de 20: **V1** +0.04 (1.1) / +2.65 (1.7), 13/20; **V2** −9.0 (1.8) / −4.1 (1.5), 2/20; **V3** −4.5 (1.7) / +0.9 (2.3), 9/20; **V4** −0.3 (1.0) / −0.2 (0.9), 8/20.

**Conclusión: ninguna de las cuatro ayuda.** V1 es neutra en B y +2.7M (1.5 ee) en Bh: no concluyente, no justifica entrar. V2 **perjudica** claramente (2/20 pares positivos): 60 columnas más con los mismos hiperparámetros diluyen un modelo tuneado para 150 (feature_fraction≈0.27), coherente con 008c. V3 y V4 son ruido. El nivel de V0 (406.9 / 394.8) reproduce el de B1 (405.8 / 392.7), así que la base es estable.
Lectura: con el modelo actual y 6 meses de datos, el espacio de features está cerca de saturado; los candidatos nuevos no aportan información que la historia lag1/lag2 y las `n_*`/`r_*` del mes no tengan ya. Dos salvedades: los hiperparámetros no se reajustaron con las columnas nuevas, y los eventos/agregados solo usan 1 mes de historia (el lag2 no existe en el train de B/Bh). **No entran al final.**

## Actualización (2026-10-09)
"El espacio de features está cerca de saturado" valía para el modelo de entonces (150 columnas con historia de 50 variables). En **028** apareció la veta que faltaba: lag1, lag2 y diferencias de **todas** las variables (+10.5M en B2). Lo de 011 (agregados, eventos de productos, lags de derivadas, comisiones normalizadas) sigue sin aportar. En **035** las tendencias por variable (aceleración, cambio relativo a la media de 3 meses) sobre las 855 columnas dieron +1 a +3M y no pasaron la regla.
