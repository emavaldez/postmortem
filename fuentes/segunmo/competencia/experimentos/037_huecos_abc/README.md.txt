# 037a / 037b / 037c — primer lote del plan de cierre de huecos (COBERTURA.md §7–8)

**Diseño** (`run.py`, `resultados.csv`, `comparacion.csv`, `columnas_canario_*.txt`, `log.txt`; ~20 min): harness del 036 (train 202103–06 → valid 202107, tarea BAJA+1, binario, hiperparámetros de M1 top1, 8 semillas pareadas), línea base = las 855 columnas de M2. Reglas fijadas antes de correr: t pareado unilateral (gl=7), Benjamini–Hochberg q=0.10 con m=8 (familia completa del plan), mínimo +3M.

| Variante | Columnas | Ganancia (M) | AUC | Δ vs base | ee | Pares | p unilateral | ¿Pasa? |
|---|---|---|---|---|---|---|---|---|
| BASE (855 columnas) | 855 | 606.7 | 0.9447 | — | — | — | — | — |
| 037b sin 202103 | 855 | 608.6 | 0.9443 | +1.9 | 1.6 | 5/8 | 0.14 | No |
| 037c deflactado | 855 | 605.4 | 0.9446 | −1.4 | 0.7 | 2/8 | 0.94 | No |
| 037a canarios > máximo | 22 | 484.5 | 0.9226 | −122.2 | 3.1 | 0/8 | 1.00 | No |
| 037a canarios > p90 | 30 | 484.3 | 0.9224 | −122.4 | 3.1 | 0/8 | 1.00 | No |

**Conclusiones**
1. **037a (canarios): no sirve en esta forma.** Con 20 canarios U(0,1) solo 22 de las 855 columnas (30 con p90) superan al canario más importante: un canario uniforme tiene muchos valores distintos y acumula "ganancia de ruido", así que casi cualquier variable real queda por debajo. Podar a 22–30 columnas destruye el modelo (−122M). Coherente con 004 (regla estricta: −37 a −93M). Probada la técnica de la cátedra: sin ganancia.
2. **037b (sin 202103): neutro** (+1.9 ± 1.6M; 5/8 pares, no pasa BH ni el mínimo de +3M). El mes sin historia no daña ni ayuda: se mantiene.
3. **037c (deflactado): ligeramente negativo** (−1.4 ± 0.7M). Cautela de interpretación: el factor mensual (1.000, 1.000, 1.027, 1.141, 1.115 para 202103–07) mezcla inflación con el aguinaldo de junio, así que prueba "deflactar por el nivel mensual de montos", no un ajuste por inflación puro. Un resultado negativo no refuta el ajuste por inflación en sí; sí muestra que esta versión no ayuda.
**Decisión:** ninguna se adopta (regla pre-registrada); no se prueban variantes para rescatarlas. El final no cambia. La confirmación en L/B2 no corresponde (nada pasó).
