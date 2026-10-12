# B1 (010) — modelo multiclase CONTINUA / BAJA+1 / BAJA+2

**Hipótesis (research/03, B1):** el negativo mezcla CONTINUA (sano) con BAJA+1 (ya se está yendo, se parece mucho a un BAJA+2 y es el error más caro). Con 3 clases el modelo aprende "se va ya" vs "se va en 2 meses". El binario `P(BAJA+2)` y el multiclase se comparan cambiando SOLO el objetivo.

**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; ~28 min): columnas M1 (top150 por fold), hiperparámetros y rondas de M1 top1 de Optuna, ccajas corregida, 5 semillas nuevas, folds A, B, Bh, ganancia = media sobre k=8000..15000 (M ARS). Filas del multiclase y del `BIN_misma`: todos los BAJA+2 y BAJA+1 + fracción r≈0.1 de CONTINUA. `BIN_005`: binario como en 005 (negativos submuestreados con r). Scores del multiclase: `MC_p2` = P(BAJA+2); `MC_h2` = P(BAJA+2) / (1 − P(BAJA+1)) (riesgo condicional: "se va en 2 meses dado que sigue en 1").

| Modelo | A | B | Bh |
|---|---|---|---|
| BIN_005 (referencia histórica) | 229.9 | 395.3 | 384.4 |
| BIN_misma | 215.4 | 381.5 | 367.6 |
| MC_p2 | 231.9 | 401.2 | 386.5 |
| **MC_h2** | **237.4** | **405.8** | **392.7** |

Diferencias pareadas (M ARS, ee): **MC_h2 − BIN_005: +7.5 (1.5) / +10.5 (2.1) / +8.3 (2.0)**, positivo en 15/15 pares fold-semilla; MC_h2 − MC_p2: +5.5 / +4.6 / +6.2 (ee ≤ 0.5); MC_p2 − BIN_005: +2.0 / +5.9 / +2.1. AUC: MC_h2 0.893 / 0.9035 / 0.9006 vs BIN_005 0.8905 / 0.9018 / 0.8979.

**Conclusiones**
1. **El multiclase con score condicional es la mejora más grande desde Optuna**: +7.5 a +10.5M con un solo modelo, consistente en los tres folds (> 4 ee) y en 15/15 pares. Dividir por (1 − P(BAJA+1)) aporta +5M extra sobre usar P(BAJA+2) a secas. **Corrección (2026-10-08):** la versión anterior de este párrafo decía que esto 'baja en el ranking a quienes ya se están yendo'; es al revés. `P2/(1−P1)` = `P2/(P0+P2)` es la probabilidad de BAJA+2 *condicional a no ser BAJA+1*, y **sube** el score de quien tiene P1 alto (con P2=0.05: P1=0 → 0.05; P1=0.5 → 0.10). La mejora es empírica (+5M, 15/15 pares); el mecanismo más probable es que el score incorpora la señal 'propenso a irse pronto' (parecida a la del target BAJA+1+2 que se había descartado), no que descarte a los BAJA+1. Mecanismo no demostrado: ver 018 (familia de scores).
2. **Dejar los BAJA+1 completos como negativos en un binario perjudica** (`BIN_misma` −14 a −17M vs `BIN_005`): son parecidos a los positivos y confunden al binario; el multiclase los separa.
3. **Mezclar binario + multiclase por rank no sirve** (BIN+MC < MC_h2): el binario arrastra al multiclase hacia abajo.
Limitaciones: hiperparámetros tuneados para binario (el multiclase podría mejorar con su propio Optuna); falta validar el ensemble multiclase de 6 configuraciones (M0 y M1). El número de rondas del multiclase equivale a 3 árboles por ronda.

## Actualización (2026-10-09)
La limitación de arriba ("falta validar el ensemble multiclase de 6 configuraciones") se resolvió en **013** (+5.5 a +9.3M sobre el MIX6 binario, 15/15 pares). Sobre el score: 018 mostró que sumar P1 ayuda con poco train y que la ventaja se achica con más datos; con las 855 columnas (034) el binario con ambas bajas pierde, así que no hace falta sumar P1 explícitamente.
