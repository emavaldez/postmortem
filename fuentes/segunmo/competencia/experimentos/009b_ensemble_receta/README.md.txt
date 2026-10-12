# 009b — ¿la receta del profe suma al MIX6? ¿Rank o probabilidad?

**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`): MIX6 de 005 (3 mejores trials de M0 y de M1) vs. MIX6 + 2 modelos de la receta de 009 (128 y 256 hojas, r=0.1, 1000 rondas, columnas M1); 5 semillas nuevas, folds A, B, Bh, ccajas corregida; ganancia = media sobre k=8000..15000 (M ARS). ~45 min.

| Ensemble | A | B | Bh |
|---|---|---|---|
| MIX6 | 234.2 | 397.5 | 386.2 |
| MIX6 + REC2 (receta 25%) | 234.6 | 397.0 | 388.2 |
| MIX6 50/50 REC2 | 234.6 | 395.4 | 388.0 |
| REC2 sola | 233.0 | 389.5 | 382.7 |
| MIX6 por rank | 234.3 | 398.7 | 388.5 |
| MIX6 + REC2 por rank | 234.1 | 397.8 | 389.5 |

Diferencias pareadas (M ARS, ee): MIX6+REC2 − MIX6: **+0.4 (0.2) / −0.6 (0.7) / +1.9 (0.6)**; MIX6_rank − MIX6: **+0.1 (0.2) / +1.1 (0.6) / +2.3 (0.9)**; REC2 − MIX6: −1.2 / −8.0 / −3.6.

**Conclusiones**
1. **La receta no suma al ensemble** (±1–2M, un fold positivo y otro nulo): el MIX6 ya está saturado en diversidad. Sola pierde 1–8M. Se puede incluir como seguro de diversidad, pero no se espera ganancia.
2. **Promediar ranks en vez de probabilidades es ligeramente mejor y gratis**: no empeora en ningún fold (+0.1 / +1.1 / +2.3). Efecto chico (~1M); se adopta en el final por ser consistente.
3. **Techo de este camino:** ensemble y tuning de hiperparámetros están agotados (005, 005b, 009, 009b). Para subir de verdad hacen falta otra información (features, target, pesos de mes), no más modelos del mismo tipo.

## Actualización (2026-10-09)
Esto es sobre el MIX6 **binario**. En el MIX6 **multiclase** la receta sí suma al ensemble por diversidad (023: +0.6 a +3.5M con peso 1/7, 8/9 pares; 50/50 −0.9 / +3.5 / +7.3M en A/B/Bh) y entró al final (1/3 vía `exp024`).
