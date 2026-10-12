# 014 — modelo auxiliar de BAJA+1 con un mes más de datos (+ control de pesos)

**Hipótesis (alumno + research B2):** en 202108 se conoce BAJA+1 de 202107 pero no su BAJA+2. El término P(BAJA+1) del score condicional `P(BAJA+2)/(1−P(BAJA+1))` puede estimarse con un modelo auxiliar que vea ese mes extra, el más cercano al mes a predecir.

**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; 43 min): réplica honesta en los folds con 202105 como mes "extra" (BAJA+1 conocido porque ya vemos 202106; su BAJA+2 no se usa). Fold B: principal multiclase (M1 top1 de 005) con 202103+04, auxiliar con 202103+04+05; Fold Bh: principal con 202104, auxiliar con 202104+05; valida 202106. Auxiliar = binario BAJA+1 vs resto (resto submuestreado con la misma r), mismas columnas e hiperparámetros. 10 semillas nuevas pareadas; ganancia = media sobre k=8000..15000 (M ARS).

| Variante | B | Bh |
|---|---|---|
| V0 actual (P1 del propio multiclase) | 406.9 | 394.8 |
| V1 auxiliar con mes extra | 407.8 | 396.2 |
| V2 auxiliar con los mismos meses que el principal | 407.6 | 395.5 |
| V3 promedio de P1 | 407.2 | 395.7 |
| V4 peso 2× en 202103 (control "copiar el mes viejo") | 403.2 | — |

Diferencias pareadas (M ARS, ee; pares positivos de 20): **V1 − V0: +0.88 (0.32) / +1.46 (0.45), 16/20**; V2 − V0: +0.67 (0.27) / +0.78 (0.29), 16/20; **V1 − V2 (efecto del mes extra): +0.21 (0.28) / +0.67 (0.23)**, 12/20; V3 − V0: +0.23 / +0.89; **V4 − V0: −3.67 (1.04), 2/10**.

**Conclusiones**
1. **Mejora chica pero consistente** (+0.9 a +1.5M, ~3 ee, 16/20 pares). Cumple el criterio del plan (> 2 ee en B y Bh) pero es del orden del ruido del Public: no se va a ver ahí.
2. **La mayor parte viene de estimar P(BAJA+1) con un modelo binario dedicado** (V2: +0.7/+0.8M), no del mes extra: el mes extra aporta solo +0.2 (B, no significativo) y +0.7M (Bh, 3 ee).
3. **Copiar/duplicar el mes más viejo perjudica** (V4 −3.7M, 2/10 pares): duplicar no agrega información y sesga hacia meses lejanos; descarta la idea de "meses copiados".
Costo de adoptarlo: 6 modelos binarios más en el final (baratos). Por el tamaño del efecto era opcional; **el alumno decidió incluirlo en el final (017)**. Para el final el auxiliar usaría 202103–07 y el principal 202103–06; verificar cómo viene codificado BAJA+1 en 202107 en `clase_ternaria` antes de usarlo.
