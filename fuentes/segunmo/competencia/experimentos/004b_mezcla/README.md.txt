# 004b — mezcla del modelo de originales (M0) y el de historia top150 (M1)

**Motivación:** el Public de `exp004_top150` (90.7M) fue peor que el baseline (94.2M) aunque localmente la historia suma. Como la ventaja de la historia no está demostrada (ver diagnóstico en 004), se prueba una mezcla (promedio de probabilidades) como cobertura.

**Diseño:** folds A, B, Bh; ganancia en k=11.000. M0 = 152 columnas originales; M1 = top150 del fold (solo train).
1. `run.py`: 20 semillas pareadas, 1 modelo por semilla y familia; MIX = (M0 + M1)/2 con la misma semilla.
2. `run_control.py`: mismo presupuesto de 10 modelos por variante (MIX = 5 M0 + 5 M1; M0x10 = 10 M0; M1x10 = 10 M1), 4 réplicas por fold, usando las 20 semillas en 4 grupos de 5.

**Resultados 1 (1 modelo por semilla, millones ARS; ee = error estándar):**

| Comparación | A | B | Bh |
|---|---|---|---|
| M1 − M0 | +0.6 (2.2) | +6.5 (3.0) | +14.7 (1.9) |
| MIX − M0 | +6.2 (1.4) | +13.9 (1.5) | +20.7 (1.5) |
| MIX − M1 | +5.7 (1.9) | +7.4 (2.2) | +5.9 (1.3) |

AUC: MIX 0.885 / 0.897 / 0.891 (A/B/Bh), M0 0.882 / 0.894 / 0.885, M1 0.884 / 0.893 / 0.889.

**Resultados 2 (control con 10 modelos cada uno):**

| Fold | M0 x10 | M1 x10 | MIX (5+5) | MIX − M0x10 | MIX − M1x10 |
|---|---|---|---|---|---|
| A | 237.6 | 231.0 | 235.1 | −2.5 | +4.1 |
| B | 370.2 | 381.7 | 382.2 | +12.1 | +0.5 |
| Bh | 366.3 | 380.0 | 379.0 | +12.7 | −1.1 |

(M0x5 → M0x10: +7.7 / +2.0 / +3.6M. M1x5 → M1x10: 0.0 / +1.4 / +6.8M.)

**Lecturas:**
- **La ventaja de la mezcla en (1) era sobre todo de promediar más modelos**, no de diversidad: con el mismo número de modelos, MIX ≈ M1 en B y Bh (+0.5 / −1.1M) y apenas por encima en A.
- **Más semillas ayudan de forma medible:** pasar de 5 a 10 modelos suma entre 0 y +8M. El submit final debería promediar bastantes más de 5 semillas (20–30), que es barato.
- **Historia vs originales (con 10 modelos):** M1 gana +11.6 / +13.8M en B y Bh, pero pierde −6.6M en A (donde el train no tiene historia, así que M1 solo aporta ruido/ratios). Ambos folds con historia validan el mismo mes (202106), y el Public de 202108 no la respalda; sigue sin estar demostrada fuera de 202106.
- **La mezcla es una cobertura barata:** frente al mejor de los dos modelos pierde como mucho 2.5M (A) y queda a ±1M en B/Bh, y siempre queda muy por encima del peor.

Reproducir: `venv/bin/python competencia/experimentos/004b_mezcla/run.py` y `run_control.py`.

**Public (entrega 4, `exp004b_mix`, 10+10 semillas, train 202103–06):** 94.04M ± 1.89M. Referencias: baseline 94.2M, 003a 93.1M, 004 90.7M. La mezcla vuelve al nivel del baseline (+3.3M sobre 004), consistente con que la historia no está demostrada para 202108 y que la cobertura sirve. Sigue siendo una diferencia dentro del ruido del Public (desvío ~5M para dos modelos con ~90% de solapamiento); no permite concluir que la mezcla supere al baseline.
