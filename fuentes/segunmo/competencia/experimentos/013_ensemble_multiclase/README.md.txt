# 013 — ¿el ENSEMBLE multiclase conserva la ventaja de B1?

**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; ~85 min): las 6 configuraciones del MIX6 de 005 (3 mejores trials de M0 y de M1, con su r e hiperparámetros) entrenadas como multiclase (BAJA+1 y BAJA+2 completos + fracción r de CONTINUA), score `P(BAJA+2)/(1−P(BAJA+1))`, ccajas corregida; folds A, B, Bh; 5 semillas (SEMILLAS_20[2:7]); comparación pareada contra el MIX6 binario de 009b (mismas semillas, folds y columnas). Ganancia = media sobre k=8000..15000 (M ARS).

| Ensemble | A | B | Bh |
|---|---|---|---|
| MIX6 binario (009b) | 234.2 | 397.5 | 386.2 |
| MIX6 binario por rank | 234.3 | 398.7 | 388.5 |
| **MC_MIX6** (prob) | 243.2 | 403.4 | 395.0 |
| **MC_MIX6_rank** | 243.1 | 404.2 | 397.9 |
| MC solo M1 (rank) | 239.7 | 404.6 | 395.6 |
| M1_top1 multiclase solo | 237.4 | 405.8 | 392.7 |

Diferencias pareadas (M ARS, ee; pares positivos): **MC_MIX6 − BIN_MIX6: +9.0 (0.9) / +5.9 (1.0) / +8.8 (0.8), 15/15**; MC_MIX6_rank − BIN_MIX6_rank: +8.8 / +5.5 / +9.3, 15/15; rank − prob (multiclase): −0.1 / +0.8 / +2.9 (12/15); MC solo M1 − MC 6 configs (rank): −3.4 (0.7) / +0.4 (0.3) / −2.2 (1.7).

**Conclusiones**
1. **La ventaja del multiclase se confirma en ensemble**: +5.5 a +9.3M sobre el MIX6 binario, en los 15 pares fold-semilla (> 5 ee en todos los folds). No era que el ensemble binario ya la captara.
2. **Rank ≥ probabilidad** también con multiclase (+0.8 en B, +2.9 en Bh, ≈0 en A): se mantiene el rank medio.
3. **M0 aporta**: sacar las 3 de M0 pierde 3.4M en A y 2.2M en Bh, y gana 0.4M en B → se mantiene el ensemble de 6.
4. El ensemble supera al mejor modelo individual en A (+5.7M) y Bh (+5.2M) y lo iguala en B (−1.6M): mezclar sigue sirviendo.
**Decisión:** el pipeline final es MIX6 multiclase, score condicional, rank medio, ccajas corregida (como `exp010_mc_h2`). Los dos pendientes de entonces se resolvieron: 014 (auxiliar de BAJA+1: +0.9 a +1.5M, incluido en el 017) y multiclase + lag2 (016: +5.4M en B2). El final posterior (031) agrega todas las variables con lags (028).
