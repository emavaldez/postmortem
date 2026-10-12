# 004 — selección de variables con canaritos

**Pool de partida (319 columnas):** originales (~150) + historia 003b (lag1, delta1, ratio1 de 50 variables) + 17 ratios de 003c. Código en `pool.py`.

**Método:** (`src/seleccion.py`, `seleccion.py`) se agregan 20 columnas de ruido U(0,1) ("canaritos"), se entrena con 5 semillas y se promedia el gain relativo. Las listas salen **solo del train de cada fold** (`sel/importancias_<fold>.csv`), nunca de la validación. Luego (`run.py`) se mide, con 20 semillas pareadas, cuánta ganancia cuesta reducir el pool.

**Resultados (k=11.000, millones ARS; "vs full" = diferencia pareada contra las 319 columnas; ee = error estándar):**

| Set | Cols | A (vs full) | B (vs full) | Bh (vs full) | s/modelo (A / B / Bh) |
|---|---|---|---|---|---|
| P_full | 319 | 222.0 | 366.6 | 364.3 | 4.9 / 12.2 / 7.3 |
| P_canario (> p90 canaritos) | 12–18 | −36.9 (ee 1.9) | −61.3 (2.4) | −92.6 (1.6) | 2.1 / 2.5 / 2.2 |
| P_top80 | 80 | −6.0 (2.7) | −12.8 (2.3) | −21.8 (2.2) | 3.4 / 3.9 / 3.0 |
| **P_top150** | 150 | −1.9 (1.8) | +1.6 (3.5) | +0.9 (3.0) | 4.2 / 5.1 / 3.9 |

Contra el baseline de variables originales (V0: A 220.6, B 361.8, Bh 346.7), el pool completo da +1.4 / +4.8 / +17.6M.

**Lecturas:**
- **La regla estricta del canarito es un desastre** (−37 a −93M): con ~1000–4000 positivos en train, el ruido absorbe una parte grande del gain (cada canarito 0.5–1.5%, juntos ~9–28%), así que el umbral queda muy alto y se descartan variables que, en conjunto, sí predicen. Lección: el canarito sirve como piso para descartar lo claramente inútil, no como corte de selección.
- La ganancia se pierde de a poco: top80 pierde 6–22M; **top150 es estadísticamente igual al pool completo** (|Δ| ≤ 1 ee en B/Bh, −1.9 ee 1.8 en A) y entrena ~2.4× más rápido en B (12.2 → 5.1 s/modelo).
- **Decisión:** usar los top150 (`variables_final_top150.txt`, calculado con el train 202103–202106, sin canaritos) como set para Optuna y el modelo final. Se pierde información de 170 columnas sin costo medible y se reduce el tiempo de cada trial a menos de la mitad.
- Caveat: la lista final se calculó con 4 meses de train y fue validada indirectamente (con las listas por fold); no se puede validar la lista final en un mes fuera de muestra.

Reproducir (raíz): `venv/bin/python competencia/experimentos/004_seleccion_variables/seleccion.py` y luego `run.py`.

## Diagnóstico post-Public (2026-10-04)
Public de `exp004_top150`: 90.74M ± 1.47M (baseline 94.2M, 003a 93.1M). Se revisó si la historia está mal aplicada en 202108:
- **Pipeline:** el camino de scoring (`solo_con_target=False` + selección de columnas) reproduce la validación de 202106 (mismas filas y valores; AUC 0.893, 369.6M con 1 semilla). No hay bug mecánico. El lag de 202108 sale de 202107 (99.1% de clientes con lag).
- **Comportamiento de las predicciones:** el solapamiento del top-11000 entre el modelo con historia y el baseline es 0.856 en 202108 vs 0.814 en la validación 202106 (Spearman 0.919 vs 0.910): la historia no se comporta de forma anómala en 202108.
- **Drift:** el adversarial entre train y 202108 sin variables de calendario da AUC 0.90 (originales) y 0.94 (historia); en 202106 era 0.83 y 0.95, o sea similar. Se observa un salto nominal de montos en 202108 (p90 de `mcomisiones_mantenimiento` 2506 → 3007; `mcaja_ahorro_dolares` más alto) en variables de poca importancia (rank 76–138).
- **Ruido del Public:** simulando el 25% de clientes sobre 202106 (mismos dos modelos, 2000 muestras), la diferencia nuevo−base tiene media +3.8M y desvío 5.4M; observar −3.5M ocurre ~8% de las veces aun si el modelo fuera +16M mejor en el mes completo. El Public no discrimina diferencias de este tamaño.
- **Conclusión:** no hay evidencia de un error ni de que la historia sea inaplicable, pero tampoco de que ayude en 202108. La evidencia local a favor es de un único mes atípico (aguinaldo) y la del Public es muy ruidosa y levemente en contra: tratar la ventaja de la historia como NO demostrada.
