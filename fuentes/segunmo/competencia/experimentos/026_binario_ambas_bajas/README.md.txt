# 026 — binario con ambas bajas (BAJA+1 y BAJA+2) como positivos (el 006 del plan, nunca corrido)

Motivo: compañeros con Public > 100 entrenan con ambas bajas como positivos; 018 ya mostraba que sumar P1 al score ayuda.
**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `log.txt`; 25 min): mismas filas (BAJA+1, BAJA+2 y fracción r de CONTINUA), columnas (M1 top150 por fold) e hiperparámetros (M1 top1 de 005) que el multiclase; cambia solo el objetivo. Ganancia siempre sobre BAJA+2, k=8000..15000 (M ARS). 5 semillas pareadas (SEMILLAS_20[2:7]).

| Variante | A | B | Bh |
|---|---|---|---|
| MC_cond (referencia: multiclase, P2/(1−P1)) | 237.4 | 405.8 | 392.7 |
| MC_suma (P1+P2 del multiclase) | 246.9 | 405.6 | 402.1 |
| B12 (binario BAJA+1/2 vs CONTINUA) | 246.6 | 401.2 | 398.5 |
| B12 con peso 0.5 en BAJA+1 | 246.2 | 401.8 | 396.6 |
| MC+B12 (rank medio) | 244.6 | 405.3 | 399.5 |

Diferencias pareadas vs MC_cond (ee; pares positivos de 15): **MC_suma +9.5 (1.2) / −0.2 (0.8) / +9.4 (1.2), 13/15**; **B12 +9.2 (1.5) / −4.6 (1.0) / +5.8 (0.6), 10/15**; B12_w05 +8.8 / −4.0 / +3.9, 11/15; MC+B12 +7.2 (0.7) / −0.5 (1.1) / +6.8 (0.6), 12/15.

**Conclusiones**
1. **Entrenar con ambas bajas como positivos funciona**: con 1 mes de train (A y Bh) gana +6 a +9M sobre nuestro score condicional. Es lo que hacen los compañeros con Public > 100, y confirma que la señal de "propenso a irse" es lo que aporta.
2. **Pero la ventaja desaparece con 2 meses de train (B)**: el binario pierde −4.6M y la suma P1+P2 empata (−0.2M). Es el mismo patrón que en 018 (α óptimo baja con más datos): con pocos datos, agregar P1 compensa la escasez de positivos; con más datos, el score condicional ya alcanza. B y Bh validan el mismo mes (202106): lo único que cambia es agregar 202103 al train.
3. **El final entrena con 4 meses**, más lejos de A/Bh que B, así que no se espera ganancia; el binario directo (B12) no es mejor que el multiclase en el régimen más parecido al final. La mezcla MC+B12 es neutra en B (−0.5M, ee 1.1): sin motivo para incluirla. **No se adopta.** (No se puede validar el efecto con 3–4 meses de train por falta de meses con target.)

## 026b — experimento completo en el régimen del final (train 202103–06 → 202108) y comparación en el Public
Mismo diseño que 010 (6 configuraciones de 005 × 6 semillas, rank medio, k=12000, un archivo por envío); un solo cambio: objetivo binario con BAJA+1 y BAJA+2 como positivos en lugar de multiclase (`final_b12.py`).

| Envío | Public |
|---|---|
| `exp026_mc` (multiclase, control) | 99.99 |
| `exp026_b12` (binario ambas bajas) | **101.31** |
| `exp026_mix` (rank medio de ambos) | **101.31** |

b12 − mc = **+1.32M**. Solapamientos del top-12000: mc–b12 93.8%, mc–mix 97.0%, b12–mix 96.8%. **Lectura:** el Public no distingue los modelos con este nivel de ruido, pero en el régimen de 4 meses el binario no muestra la pérdida que daba el fold B (−4.6M ≈ −1.15M en escala Public); el +1.32M se parece más a lo que dan A y Bh (+9.2 y +5.8M ≈ +2.3 y +1.45M en escala Public). Ojo con la escala: las diferencias locales son de un mes completo y el Public es ~25%, así que hay que dividir por ~4 para compararlas; con el ruido de ±2M el experimento tenía poca potencia (la regla de ≥3M que fijé antes era inalcanzable). Los envíos son válidos y distintos; las igualdades al centavo (mc = 99.99 como el `exp010` de k=11500; mix = b12) son coincidencias de resultados discretos. Candidato a componente del blend final (`blend_final3.py`, `exp027_final3_k12000.csv`).

## Actualización (2026-10-09)
Con las 855 columnas de M2 (034) el binario con ambas bajas **pierde** frente al multiclase en L y B2 (−4.0 / −9.0M), incluso con 1 mes de train; queda descartado como componente del final.
