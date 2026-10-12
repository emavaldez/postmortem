# 5 — Predicción final

| | |
|---|---|
| Archivo enviado | `C1CLAW2C065771C9ENS13500.csv` |
| Mensaje al bot | `submit C1CLAW2C065771C9ENS13500` |
| Fecha | 09/10/2026 |
| Submission ID | `1586-1791569183206183` |
| Ganancia pública | **101,0900 M ARS** |
| Filas | 13.500 `numero_de_cliente` de agosto, una columna, sin encabezado, ordenados de menor a mayor |
| SHA-256 | `a1ced864e5e6de15fbd3c65a12c29506387d1bece5f6a87435b45ff907f549ff` |

Respuesta del bot:

```
Submission received: 1 candidate model
Public gain -> mean: 101.0900, std dev: 0.0000
Submission ID: 1586-1791569183206183
This is now your final submission -- your LAST pre-deadline submit always is, with no separate step needed.
```

`MANIFIESTO_CLAW2_TRANSCRIPTO.json` es el `MANIFEST.json` que escribió el modelo final al generar ese CSV: identidad de la corrida, los 16 parámetros de LightGBM, rondas, pesos por grupo y el hash. Lo copié del bucket; por eso dice "transcripto".

Para comprobar un CSV regenerado con el paso 4:

```bash
python 5_prediccion_final/verificar_csv_final.py /RUTA/C1CLAW2C065771C9ENS13500.csv \
  --sha256 a1ced864e5e6de15fbd3c65a12c29506387d1bece5f6a87435b45ff907f549ff --n 13500
```

Con `--dataset /RUTA/competencia_01_crudo.csv` también verifica que todos los IDs existan en agosto.

El CSV no está en el repo: la cátedra tiene el que se adjuntó al bot, y el pipeline lo regenera.
