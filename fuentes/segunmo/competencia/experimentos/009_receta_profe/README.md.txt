# 009 — receta del profe vs. Optuna, con y sin undersampling

**Hipótesis (profe, 1.7):** sin undersampling y con hiperparámetros fijos (max_bin 31, min_data_in_leaf 0, ff 0.5, ff_bynode 0.2, lr 0.005, AUC) y solo num_iterations/num_leaves/min_sum_hessian como variables, el modelo es igual o mejor. Nosotros medimos en 007 que r≈0.1 mejoraba.

**Diseño** (`run.py`, `resumen.py`, `resultados.csv`, `log.txt`): grilla 3 `num_leaves` (8/32/128) × 3 `min_sum_hessian_in_leaf` (0.05/0.5/2.0), 3.000 rondas puntuadas en 500/1000/1500/2000/3000; dos brazos (r=1.0 y r=0.1); referencia = M1 top1 de Optuna (005) con las mismas semillas y columnas (top150 con historia por fold); folds A, B, Bh; 2 semillas (852583, 771227); ganancia = media sobre k=8000..15000 (M ARS). Corrió ~100 min.

| Mejor configuración | A | B | Bh | media vs ref |
|---|---|---|---|---|
| Referencia Optuna M1 top1 | 233.4 | 405.3 | 389.8 | — |
| Receta + undersampling r=0.1 (128 hojas, h=0.05, 1000 rondas) | 234.8 | 396.6 | 386.8 | **−3.4** |
| Receta sin undersampling (128 hojas, h=2.0, 500 rondas) | 229.3 | 382.0 | 380.4 | −12.3 |

**Conclusiones**
1. **El undersampling sigue ayudando**: a igual receta, r=0.1 le gana al brazo sin undersampling por ~9–16M en B y ~5M en A/Bh (coherente con 007). Se mantiene como decisión (criterio acordado: "si ayuda, lo usamos").
2. **La receta del profe con r=0.1 queda cerca de Optuna** (A +1.4, B −8.7, Bh −3.0), sin haber hecho Optuna: es un modelo competitivo y distinto (lr 0.005, bynode 0.2, min_data_in_leaf 0) → buen candidato como **miembro de diversidad del ensemble**, no como reemplazo.
3. **Sin undersampling la receta sobreajusta rápido**: el mejor punto está en el primer checkpoint (500 rondas con lr 0.005) y cae a más rondas.
4. **Los óptimos están en el borde de la grilla** (128 hojas, el máximo): hojas 256+ podrían mejorar; no se exploró.
Ruido: 2 semillas, desvío de la referencia 0.3–8.4M entre semillas → diferencias de ±5M no son concluyentes.

## Actualización (2026-10-09) — esta conclusión quedó corregida
El "−12M sin undersampling" y "el undersampling sigue ayudando" valen **solo para este diseño**: modelo binario y una grilla truncada (el mejor punto estaba en el primer checkpoint, 500 rondas, y en el borde de hojas). En **021** se repitió en multiclase con grilla ampliada: sin undersampling la receta **no pierde** (+3.4M en promedio sobre Optuna en 150 columnas, en el borde de la grilla) y con undersampling queda por debajo (−1.4M). Por eso en el final la receta del profe va **sin** undersampling (componente del `exp024`). El undersampling con r≈0.1 se mantiene en los modelos de Optuna (M0/M1/M2).
