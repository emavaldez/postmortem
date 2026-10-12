# B1 — Variables rotas

**Qué hice:** con los 20 modelos de C3 ya congelados por Q0, probé marcar como faltantes otras variables que tienen un mes anómalo (Visa y Master en junio, además de `ccajas_depositos` en mayo), en todas las combinaciones, y medí la ganancia en junio sin reentrenar.

SUPERFINAL lo ejecuta solo en su etapa 0 (`--prepare` y luego `--execute`) y con el resultado decide con qué versión del dataset sigue. No hace falta correrlo a mano.

Salida: `$HOME/c1b1rotas01/` con `LISTO.json`. El plan de brazos está en `plan_b1.json`.
