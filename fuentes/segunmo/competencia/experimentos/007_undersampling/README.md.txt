# 007 — undersampling de negativos en el train (adelantado: decide el presupuesto de Optuna)

**Hipótesis:** conservar todos los BAJA+2 y solo una fracción r del resto acelera el entrenamiento sin perder ganancia (se corta por top-k, así que la calibración no importa).

**Diseño:** `run.py`. Se sortea, para cada modelo, qué negativos (CONTINUA + BAJA+1) se conservan, con la semilla del propio modelo; la validación es el mes completo. Sets M0 (152 originales) y M1 (top150 con historia del fold), r ∈ {1.0, 0.5, 0.2, 0.1, 0.05}, folds A/B/Bh, 20 semillas pareadas contra r=1.0, k=11.000. Hiperparámetros fijos (incluido `min_data_in_leaf=200`, que no se reescala).

**Resultados (millones ARS, diferencia pareada vs r=1.0; ee = error estándar):**

| Set | r | A | B | Bh |
|---|---|---|---|---|
| M0 | 0.5 | −0.9 (2.4) | +10.1 (2.0) | +7.2 (2.4) |
| M0 | **0.2** | +5.1 (2.6) | +8.9 (2.3) | +9.1 (2.4) |
| M0 | 0.1 | +3.9 (2.7) | +8.6 (3.1) | +7.2 (2.9) |
| M0 | 0.05 | +0.2 (2.5) | +5.6 (2.3) | +3.4 (2.6) |
| M1 | 0.5 | +3.2 (2.0) | +6.2 (3.0) | +4.7 (2.5) |
| M1 | **0.2** | +6.3 (2.1) | **+15.1** (2.8) | +6.8 (2.8) |
| M1 | 0.1 | +3.4 (2.2) | +13.1 (2.4) | +8.4 (2.5) |
| M1 | 0.05 | −0.2 (2.3) | +10.0 (4.4) | +2.7 (3.1) |

**Lecturas:**
- **No pierde ganancia, la mejora**: con r=0.2 las 6 combinaciones (2 sets × 3 folds) son positivas, entre +5 y +15M, y 4 de 6 superan 2 errores estándar. Con r=0.1 también. r=0.05 empieza a perder.
- Se entrena con 5 veces menos filas (A: 163k → 33k; B: 326k → 67k), así que cada modelo es bastante más rápido. Los tiempos medidos por modelo están contaminados por otros procesos en la máquina (de 9 a 4s en B para M0), pero la tendencia es clara.
- **Posible explicación:** con 5 veces menos negativos y `min_data_in_leaf=200` fijo, las hojas tienen proporcionalmente más positivos, y el modelo queda menos regularizado en la dirección útil; además cada semilla ve un submuestreo distinto, lo que aumenta la diversidad del ensemble. Parte del efecto puede solaparse con lo que Optuna encontraría en `min_data_in_leaf` o `feature_fraction`.
- **Decisión:** incluir la fracción r como un hiperparámetro más de Optuna (rango 0.05–0.5) en vez de fijarla; usar r≈0.2 como punto de partida. En el modelo final, promediar semillas donde cada una hace un submuestreo distinto.

Reproducir: `venv/bin/python competencia/experimentos/007_undersampling/run.py`.
