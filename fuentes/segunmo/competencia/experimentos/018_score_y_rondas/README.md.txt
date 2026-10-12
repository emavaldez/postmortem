# 018 — familia de scores, positivos esperados en 202108 y rondas vs tamaño del train

Respuesta a la revisión del 08-oct. Modelo: multiclase M1 top1 de 005 (r≈0.099, 688 rondas), ccajas corregida, 5 semillas (SEMILLAS_20[2:7]), ganancia = media sobre k=8000..15000 (M ARS). `run.py`, `scores.csv`, `rondas.csv`, `log.txt` (~80 min).

## (A) Familia de scores (mismo modelo, mismas predicciones P0, P1, P2)
| Score | A | B | Bh | A vs actual | B vs actual | Bh vs actual |
|---|---|---|---|---|---|---|
| P2 | 231.9 | 401.2 | 386.5 | −5.5 | −4.7 | −6.2 |
| P2/(1−P1) (actual) | 237.4 | 405.8 | 392.7 | 0 | 0 | 0 |
| P2+0.1·P1 | 238.2 | 405.5 | 393.7 | +0.7 | −0.3 | +1.0 |
| P2+0.25·P1 | 241.8 | 407.1 | 397.4 | +4.4 | +1.3 | +4.7 |
| P2+0.5·P1 | 244.9 | 407.5 | 400.2 | +7.5 | +1.7 | +7.5 |
| P2+P1 | 246.9 | 405.6 | 402.1 | +9.5 | −0.2 | +9.4 |
| P2+2·P1 | 247.9 | 402.4 | 402.1 | +10.5 | −3.4 | +9.4 |
**Lectura.** (1) Sumar P1 al score ayuda: el aporte del score condicional sobre P2 sola (+4.7 a +6.2M) viene de incorporar la señal "propenso a irse", no de descartar a nadie (corrige la explicación original, ver 010). (2) **El α óptimo baja cuando el train crece**: con 1 mes de train (A, Bh) el mejor es α≥1 (+9.5 a +10.5M sobre el actual); con 2 meses (B) el mejor es α=0.5 (+1.7M) y α≥1 ya no gana. El final entrena con 4 meses, así que se espera una ventaja aún menor. (3) La regla previa (elegir α en A, adoptar solo si gana también en B) selecciona α=2, que **no** gana en B; el máximo α que gana en los tres folds es 0.5 (+7.5 / +1.7 / +7.5M). **Decisión:** se mantiene P2/(1−P1) en el final: con 4 meses de train el margen esperado es ≤ ~1.7M (el valor de B), dentro del ruido, y cambiarlo exigiría reentrenar 4.5 h (los scores guardados del 010 y 017 ya vienen combinados).

## (C) Rondas vs tamaño del train
Ganancia por número de rondas: A (1 mes) óptimo 688, B (2 meses) óptimo 688, Bh (1 mes) óptimo 300. Curvas planas (B: 402.3 a 300, 405.8 a 688, 402.3 a 1400). **No hay señal de sub-ajuste por tener más datos**: las rondas de Optuna siguen en el óptimo.

## (B) Positivos esperados en 202108
Razón suma(P2)/positivos reales: A 3.77, B 3.63 (estable entre folds). Suma(P2) del modelo entrenado con 202103–06 sobre 202108: 4.349 → **~1.150 (razón A) a ~1.200 (razón B) positivos esperados** (202105: 870; 202106: 1.098). Parecido a B/Bh, que tienen su pico de ganancia en k≈12–13k (≈ 9–11.4 veces los positivos). Limitaciones: la razón sale de 2 folds y el modelo de 202108 tiene más meses de train. **Decisión: k=12000** (la curva de 015 es plana en 11–12k; la diferencia entre 11.000 y 12.000 es < 2M en cualquier fold salvo A, que ya no es el escenario esperado).
