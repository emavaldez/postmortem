# 032 y 033 — búsqueda dirigida de hiperparámetros para M2 (855 columnas)

**Motivo:** los hiperparámetros de M1 top1 se tunearon para 150 columnas (ff 0.129 ≈ 19 columnas por árbol; con 855 son ~110). No es un Optuna: L y B2 validan el mismo mes (202106, targets solapados) y no hay fold independiente para certificar; un cambio a la vez, pareado (3 semillas), y se acepta solo si mejora en ambos folds.
**032** (`run.py`, ~1 h): feature_fraction {0.05, 0.08, 0.20, 0.35}, num_leaves {100, 256}, min_data_in_leaf {15, 50}, rondas {500, 900, 1100}. Solo `min_data_in_leaf` muestra señal: 50 → +6.3 (ee 1.2) / +3.8 (2.2) en L/B2, 5/6 pares; 15 → −4.1 / −0.9, 0/6. El resto es ruido (ff, hojas, rondas dentro de ±3M sin consistencia entre folds).
**033** (`../033_min_data/run.py`, ~20 min): extensión de `min_data_in_leaf` a 80, 120 y 200 (mismas semillas, folds y base):

| min_data_in_leaf | L | B2 | pares |
|---|---|---|---|
| 15 | −4.1 | −0.9 | 0/6 |
| 27 (base) | 0 | 0 | — |
| 50 | +6.3 | +3.8 | 5/6 |
| **80** | +4.5 | +3.8 | **6/6** |
| 120 | −0.2 | −2.0 | 1/6 |
| 200 | −11.0 | −11.6 | 1/6 |

**Conclusión:** U invertida con meseta entre 50 y 80 (con más columnas, hojas más grandes regularizan); más allá de 120 se degrada. Para el final: `min_data_in_leaf` = 50, 65 y 80 en M1 top1, top2 y top3 (los extremos probados en top1; el 65, interior a la meseta). Supuesto no medido: que el mismo rango sirve para top2 y top3. Ganancia esperada ≈ +4 a +6M locales (L), +4M (B2); en el final cambia solo ~1% de los clientes (el blend con min_data nuevo solapa 99.1% con el viejo).
