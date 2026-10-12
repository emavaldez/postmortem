# 008a — `ccajas_depositos` = NA solo en 202105

**Hipótesis (profe, 1.1):** `ccajas_depositos` viene rota en 202105 (todas las filas en 0; en los demás meses hay entre 831 y 6.486 filas distintas de cero). Es la única columna numérica con ese defecto (revisado para todas). Ponerla en NA ese mes evita que el modelo aprenda de ceros falsos.

**Diseño** (`run.py`): set M0 (152 originales + 26 `n_*`), params base, 20 semillas pareadas, k=11000. Flag `config.CORREGIR_CCAJAS` (default False para no alterar 001–007; la corrección se hace en la vista de DuckDB, `data.py`).
- **A** (train 202103 → valid 202105): delta **0 exacto por construcción**. El train no tiene NaN en la columna y LightGBM trata los NaN como 0 al predecir si no vio NaN al entrenar.
- **B y Bh** no tocan 202105: delta 0, no se corren.
- **L** (train 202105 → valid 202106) y **B2** (202104+05 → 202106): únicos folds con 202105 en el train, con el solapamiento de targets descrito en 008b.

| Fold | base | corregida | Δ (M ARS) | ee | ΔAUC |
|---|---|---|---|---|---|
| A | 224.1 | 224.1 | 0.0 | 0 | 0 |
| L | 338.9 | 338.0 | −0.9 | 2.6 | +0.0001 |
| B2 | 360.3 | 363.3 | +3.0 | 2.2 | 0 |

**Conclusión:** efecto no distinguible de cero (la variable es casi toda ceros). **Se aplica igual por corrección de datos**, no por ganancia medida: es una columna rota confirmada y no cuesta nada. Riesgo menor: el NaN solo existe en 202105, así que puede servir de huella de ese mes; el delta ≈ 0 no muestra daño. Los scripts nuevos (008c en adelante y el final) ponen `config.CORREGIR_CCAJAS = True`; los submits 001–005 se hicieron sin corregir.
