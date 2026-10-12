# 015 — curva de ganancia vs k del ensemble multiclase

**Diseño** (`run.py`, `curvas.csv`, `curva_media.csv`, `log.txt`; ~50 min): MIX6 multiclase (6 configuraciones de 005, score condicional, rank medio, ccajas corregida), folds A, B, Bh, 3 semillas (SEMILLAS_20[2:5]); ganancia ex post para k=6000..16000 (paso 500), M ARS.

| k | A | B | Bh | media 3 folds | pérdida media vs pico de cada fold |
|---|---|---|---|---|---|
| 9000 | 261.1 | 393.1 | 390.5 | 348.2 | −12.2 |
| 10000 | 254.5 | 407.4 | 398.2 | 353.3 | −7.1 |
| **10500** | 249.9 | 410.5 | 403.2 | **354.5** | **−5.9** |
| **11000** | 247.9 | 409.9 | 404.8 | 354.2 | −6.2 |
| 11500 | 245.5 | 412.7 | 402.0 | 353.4 | −7.0 |
| 12000 | 242.7 | 411.8 | 403.7 | 352.7 | −7.7 |
| 13000 | 234.7 | 414.0 | 405.9 | 351.5 | −8.9 |
| 15000 | 214.9 | 401.5 | 400.8 | 339.0 | −21.4 |

**Conclusiones**
1. **El pico depende de cuántos positivos tiene el mes**: A (870 positivos) pica en k≈7.500–8.000; B y Bh (1.098) en k≈12.000–13.000. El k óptimo ≈ 9–11× los positivos del mes. En 202108 no los conocemos (prevalencia histórica ~0.6–0.7% de ~164.6k filas → 960–1.140 positivos, o sea k óptimo ≈ 10–12k).
2. **La curva de la media de los 3 folds es plana entre 10.000 y 12.000** (352.7–354.5M, ≤ 1.8M de diferencia: ruido). Más allá de 13.000 y por debajo de 9.500 se pierde claramente (A cae ~15M de 11.500 a 13.000).
3. **El multiclase no corrió el k respecto del binario** (005c/PLAN: 10–14k). Elegimos **k = 11.000** (centro de la meseta, pérdida media 6.2M frente a 5.9M de 10.500 y 7.0M de 11.500; protege algo más si 202108 tiene pocos positivos como 202105).

## Actualización (2026-10-09)
El k=11.000 de acá se movió a **k=12.000** al estimar ~1.150–1.200 positivos en 202108 (018) y confirmarse una meseta en 11.5–12k en el Public (025: 97.5 / 98.0 / 98.2 / 96.8 / 96.6M para k = 11.0k…13.0k). El final usa k=12000.
