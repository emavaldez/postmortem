# 001 — Baseline LightGBM

## Hipótesis
Un LightGBM binario (BAJA+2 vs resto) con hiperparámetros razonables y SIN feature engineering ni optimización da un punto de partida sólido y fija el piso contra el cual comparar los experimentos siguientes.

## Diseño
- **Target:** `BAJA+2` = 1, resto = 0. Features: todas las columnas salvo `numero_de_cliente`, `foto_mes`, `clase_ternaria` (152).
- **Validación out-of-time:** train 202103+202104 → valid 202106 (202105 como separación). Ganancia sobre el mes completo (sin escalar). 5 semillas propias.
- **Final:** train con 202103–202106 (todos los meses con target) → scoring 202108, probabilidad = promedio de las 5 semillas.
- **Hiperparámetros fijos:** `num_leaves=31, learning_rate=0.05, min_data_in_leaf=200, feature_fraction=0.5, bagging_fraction=0.8 (freq 1), max_bin=31`, 300 rondas. No hay early stopping ni Optuna.
- **Corte:** por cantidad de envíos (top-k por probabilidad), k ∈ {8000…15000} (rango admitido por el bot); se generan 8 archivos para ver en un mismo submit cuál k rinde mejor en el Public LB.

## Reproducir
```
venv/bin/python competencia/experimentos/001_baseline_lgbm/run.py      # --sin-final para sólo validar
```
~1 min. Escribe `validacion.csv`, `curva_validacion.csv` y los CSV `exp001_baseline_k*.csv` en `competencia/submissions/`.

## Resultados (valid 202106, media ± desvío entre 5 semillas)
| Métrica | Valor |
|---|---|
| AUC | 0.894 ± 0.001 |
| Ganancia con umbral 0.025 (≈7.5k envíos) | 334.1M ± 11.7M |
| Ganancia con k=10000 / 11000 / 12000 / 13000 | 351.6M / 354.4M / 355.5M / 354.0M (± ~8–9M) |
| Máximo ex-post (óptimo teórico, optimista) | 365.6M ± 7.6M |
- La ganancia es plana en k ∈ [10000, 14000] (diferencias ≪ desvío entre semillas): el k exacto importa poco en ese rango; k=8000 pierde ~15M y k=15000 ~6M.
- El corte por umbral 0.025 queda ~20M por debajo del corte por cantidad: las probabilidades no están calibradas por el desvío de entrenamiento (3 meses) vs valid.
- Curva por rondas (promedio): la ganancia con umbral sube de 318M (50 rondas) a ~336M (200) y se estabiliza; AUC apenas baja con más rondas. 300 rondas es razonable, pero no está optimizado.
- En scoring 202108: 8553 clientes tienen p ≥ 0.025.

## Expectativa para el Public LB
El Public LB usa ≈25% de los clientes de 202108 y no se escala. Si 202108 se parece a 202106, esperar un Public Gain ≈ 340–360M × 0.25 ≈ **85–90M** (muy ruidoso: ±10% por azar de la muestra, y 202108 puede tener drift).

## Resultado del submit (Public LB)
`exp001_baseline` (8 archivos, k=8000…15000): **Public gain mean 94.2150M, std 2.4454M** (ID 1562-1791048958570663). Cayó por encima de la expectativa (85–90M). El desvío de 2.4M entre archivos es chico, coherente con la zona plana en k observada en validación. Ojo: la media de 8 archivos incluye los k extremos (8000 y 15000), por lo que el mejor k individual rinde algo más.

## Conclusión / próximos pasos
Baseline listo. Candidatos a experimentos (uno a la vez): optimizar hiperparámetros con Optuna (objetivo = media de ganancia en walk-forward), más meses de train, feature engineering histórico (lags/deltas), tratamiento de variables con drift (z701), clase binaria BAJA+1+2, undersampling. Medir contra este baseline con las mismas semillas y mes de validación.
