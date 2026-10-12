# 037d / 037e — M2 sin undersampling y diversidad con configuraciones M0

Mismo harness del 036/037 (train 202103–06 → valid 202107, tarea BAJA+1, binario, 855 columnas, hiperparámetros de M1 top1). Reglas fijadas antes de correr: t pareado unilateral, BH q=0.10 con m=8 sobre toda la familia, mínimo +3M. `run.py`, `resultados_d.csv`, `resultados_e.csv`, `comparacion_d.csv`, `comparacion_e.csv`, `log.txt` (~40 min).

## 037d — sin undersampling (profe 1.7)
r = 0.3 y 1.0 contra la base r = 0.0986; 5 semillas pareadas; `min_data_in_leaf` sin retunear (confusión declarada: con más filas pesa relativamente menos).
| Variante | Filas de train | Δ vs base (M) | ee | Pares | p unilateral |
|---|---|---|---|---|---|
| r = 0.3 | ~3× | **+2.9** | 2.2 | 3/5 | 0.13 |
| r = 1.0 (sin undersampling) | ~10× | **+1.8** | 2.9 | 3/5 | 0.29 |
**Conclusión:** ni más datos de la clase mayoritaria ayudan de forma detectable (ambas dentro de ~1 ee, 3/5 pares, no pasan BH ni el mínimo de +3M); r = 1.0 además es mucho más variable entre semillas (−6.6 a +11.0). El undersampling con r≈0.1 no pierde, y ahorra ~10× de cómputo. Coherente con 021 (la receta sin undersampling no perdía, pero tampoco ganaba por mucho). El pedido del profe se probó con la base de este modelo: **sin ganancia detectable**.

## 037e — diversidad con M0 (profe 2.1)
Ensemble rank medio de 3 configuraciones M1 vs 6 (M1 + M0), mismas 855 columnas, 8 semillas.
| | E3 (M1) | E6 (M1+M0) | Δ | ee | Pares | p |
|---|---|---|---|---|---|---|
| Ganancia media (M) | 610.2 | 610.8 | **+0.6** | 0.5 | 4/8 | 0.16 |
**Conclusión:** sumar las 3 configuraciones M0 a las 3 de M1 sobre las mismas columnas no mejora (+0.6 ± 0.5M). Los modelos individuales ya rinden parecido (598–618M) y el ensemble está saturado, igual que en 009b. No pasa.
**Decisión:** ninguna se adopta (regla pre-registrada).
