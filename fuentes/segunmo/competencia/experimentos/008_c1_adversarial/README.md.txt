# 008 C1 — Adversarial validation (sin target)

**Hipótesis:** si 202108 fuera mucho más distinguible del train que lo que se distinguen entre sí dos meses consecutivos, habría drift multivariado que el PSI univariado de 002 no ve.

**Diseño** (`run.py`, `resultados.csv`): LightGBM chico (`drift.adversarial`, hold-out 30%) que separa el mes A del mes B con las variables originales. Se excluyen ID, mes, target, `*fultimo_cierre` (calendario puro, AUC 1.0 según 002) y `ccajas_depositos` (rota en 202105: delata al mes por artefacto de datos; en una primera corrida la dejé con NA solo en 202105 y salió AUC 1.0, un error de control mío).

**Resultado (AUC):**

| Par | AUC | Variable que más separa |
|---|---|---|
| 202103 vs 202104 | 0.838 | Master_mlimitecompra |
| 202104 vs 202105 | 0.831 | Visa_mlimitecompra |
| 202105 vs 202106 | 0.877 | mpayroll |
| 202106 vs 202107 | 0.918 | mcomisiones_mantenimiento (0.33) |
| 202107 vs 202108 | 0.841 | Visa_mpagado |
| 202103–06 vs 202108 | 0.924 | mcomisiones_mantenimiento (0.46) |

**Conclusión:** entre meses consecutivos el AUC ya es 0.83–0.92 (los montos nominales crecen mes a mes), y 202108 contra el train (0.92) está en ese rango: **no hay drift extraordinario en 202108**. Lo único que sobresale es `mcomisiones_mantenimiento` (salto nominal de la comisión: p90 2506 → 3007), que explica 0.3–0.46 de la importancia adversarial desde 202106. Es candidata a probar sacándola o normalizándola (en 004 estaba en rank 76–138 de importancia para el target, así que se espera poco efecto).
