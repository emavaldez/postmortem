# Predicción final

## El archivo entregado

`lovrich_ensamble_corte11000.csv` es **el archivo exacto que subí al bot** como entrega final.

- Es la salida de `run_rank_prestamos_junbo_hist.R` en
  `entrega/corte_11000/lovrich_ensamble.csv`.
- Contenido: un `numero_de_cliente` por línea, sin encabezado; los **11000** clientes con mayor
  probabilidad estimada de ser BAJA+2 en 202108, según el ensamble de 40 semillas.
- Modelo: LightGBM, normalización por rango con signo + retrovisores + FE histórico (tendencia y
  promedio de 3 meses), hiperparámetros `256 / 0.0299943 / 1439` (ver `../optimizacion_bayesiana/`).

## Verificación de integridad

`SHA256.txt` contiene el hash SHA-256 del archivo de entrega, para verificar que una réplica
produjo el mismo archivo. Para comprobar:

```bash
# Linux / macOS
sha256sum -c SHA256.txt

# Windows (PowerShell)
Get-FileHash lovrich_ensamble_corte11000.csv -Algorithm SHA256
```

El hash de una réplica debe coincidir con el de `SHA256.txt`. (La reproducibilidad está
garantizada por `deterministic=TRUE` en LightGBM y las semillas fijas de la primigenia 100193.)

## Cómo se regenera

Corriendo el pipeline (ver el README principal, Opción A o B). El archivo de entrega queda en
`<DMEYF_EXP>/entrega/corte_11000/lovrich_ensamble.csv`.
