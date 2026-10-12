# 037f — hojas de Random Forest como features (profe 1.5, libro 20.10)

**Diseño** (`run.py`, `run_numerico.py`, `bh_final.py`; `resultados*.csv`, `comparacion*.csv`, `log*.txt`; ~15 min en total): sin fuga. El RF (sklearn, 100 árboles, profundidad ≤ 8, `min_samples_leaf` 100, positivos + 10% de negativos, columnas M1 top150) se entrena con **202103–04** (etiqueta BAJA+1) y sus índices de hoja se agregan como 100 columnas; LightGBM entrena con **202105–06** (filas que el RF no vio) y se valida en 202107 (BAJA+1, proxy). F0 = 855 columnas; F1 = 855 + 100 hojas. 8 semillas pareadas (la semilla también sortea el RF). Reglas fijadas antes de correr (COBERTURA.md §7).

| Variante | Columnas | Ganancia (M) | AUC | Δ vs F0 | ee | Pares | p unilateral |
|---|---|---|---|---|---|---|---|
| F0 (855 columnas, 2 meses de train) | 855 | 604.1 | 0.9430 | — | — | — | — |
| F1 hojas **categóricas** (plan) | 955 | 557.5 | 0.9364 | **−46.5** | 1.5 | 0/8 | 1.00 |
| F2 hojas **numéricas** (posterior) | 955 | 592.0 | 0.942 | **−12.1** | 1.3 | 0/8 | 1.00 |
Contexto: BASE con 4 meses de train (037) = 606.7M; F0 con 2 meses = 604.1M, o sea quitar 202103–04 del LightGBM cuesta solo 2.6M.

**Conclusiones**
1. **Las hojas de RF no ayudan en este diseño**: −46.5M como categóricas (0/8 pares, AUC −0.0066) y −12.1M como numéricas (0/8). No pasa BH ni el mínimo de +3M.
2. **Qué parte fue defecto de codificación mío:** con categóricas el modelo pierde −46.5M y con numéricas −12.1M, o sea ~34M del desastre vienen de que LightGBM sobreajusta con 100 columnas categóricas de ~500 niveles. Con ambas codificaciones el signo es negativo en las 8 semillas.
3. **Honestidad del procedimiento:** el plan solo decía "agregar los índices de hoja como columnas"; elegí categóricas sin probar. Al ver −46M corrí una variante con numéricas **después** de conocer ese resultado: es exploratoria, y se cuenta en la familia de BH (m = 9, no 8) para no inflar descubrimientos.
4. **Límite:** solo se probó un diseño (RF con 2 meses, 100 árboles, profundidad 8, hojas crudas). No descarta que otra forma de usar las hojas (por ejemplo la probabilidad del RF como una columna, o RF y LightGBM entrenados sobre las mismas filas con validación cruzada por cliente) pueda aportar; no se probó.
**Decisión:** no se adopta.
