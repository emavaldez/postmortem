# 021 — la receta del profe en multiclase (sin undersampling, menos rondas)

**Por qué:** el −12M de 009 salió en binario con una grilla truncada: el mejor punto sin undersampling estaba en el primer checkpoint y en el borde de hojas. Acá se repite en multiclase con grilla ampliada.
**Diseño** (`run.py`, `resultados.csv`, `log.txt`; ~3 h): receta (max_bin 31, min_data_in_leaf 0, ff 0.5, ff_bynode 0.2, lr 0.005), 800 rondas puntuadas en 100/200/300/500/800; grilla hojas {128, 256, 512} × min_sum_hessian {0.05, 2.0}; dos brazos (r=1.0 sin undersampling, r=0.1); referencia = M1 top1 multiclase de 005 con las mismas semillas; folds A, B, Bh; 2 semillas (SEMILLAS_20[2:4]); columnas M1 top150 por fold. Ganancia = media sobre k=8000..15000 (M ARS). Referencia: A 234.5 / B 405.7 / Bh 393.2.

| Configuración | A | B | Bh | media vs ref |
|---|---|---|---|---|
| sin undersampling, 512 hojas, hess 0.05, 800 rondas | +4.1 | +0.1 | +6.0 | **+3.4** |
| sin undersampling, 256 hojas, hess 2.0, 800 rondas | +4.2 | +1.5 | +3.0 | +2.9 |
| sin undersampling, 512 hojas, hess 0.05, 500 rondas | +5.5 | −0.8 | +4.5 | +3.1 |
| mejor con undersampling r=0.1 (128 hojas, hess 2.0, 800) | +7.3 | −8.2 | −3.3 | −1.4 |

**Conclusiones**
1. **En multiclase la receta sin undersampling no pierde frente a nuestro Optuna**: las mejores configuraciones quedan +3 M por encima (A +4/+7, Bh +3/+6) y en B empatan (−2 a +2). Corrige el "−12M" de 009, que era un artefacto de binario + grilla truncada. Con undersampling la receta queda por debajo (−1.4M).
2. **El óptimo vuelve a estar en el borde** (512 hojas, 800 rondas, que son los máximos probados): hay margen para más hojas y más rondas.
3. **Cautelas:** 2 semillas, ~60 combinaciones (el mejor está sesgado hacia arriba), y B (el fold más parecido al final, con 2 meses) no confirma (+0.1). Efecto verdadero esperable ≈ 0 a +2M; el valor práctico más probable es como **miembro del ensemble** por diversidad (otro lr, otra regularización, sin undersampling). Se mide en 023.
