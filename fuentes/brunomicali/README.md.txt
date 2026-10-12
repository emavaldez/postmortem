# DMEyF 2026 · Competencia 01 · Entrega final

Autor: Bruno Micali Dejter

## Archivo a entregar

`entrega_ensamble3prop_50sem_k10750_202108_10750.csv`

10.750 `numero_de_cliente` de la foto 202108, uno por línea, sin encabezado, enteros y sin repetidos.

SHA-256 del archivo: `3c85bcbe055f01522bad34dcd7a73e04b7d5f491bb8f0e871f4f1860c46bb6d9`

## Cómo reproducirlo

Requisitos: Python 3.10 y las versiones exactas de `codigo/requirements.txt`. DuckDB tiene que ser 1.5.5, porque el submuestreo de negativos usa su función `hash()`.

```bash
cd codigo
pip install -r requirements.txt
# dataset de la cátedra en ../datos/competencia_01_crudo.csv, o bien:
export DMEYF_CSV=/ruta/a/competencia_01_crudo.csv
python reproducir.py
```

`reproducir.py` corre todas las etapas en orden. Al final compara la suma SHA-256 del archivo obtenido con la esperada (`codigo/sha256_esperado.txt`) e imprime `REPRODUCCIÓN EXACTA` o `EL ARCHIVO NO COINCIDE`. Cada etapa se puede reanudar: si se interrumpe, se vuelve a correr el mismo comando.

Dataset de entrada verificado: `competencia_01_crudo.csv`, 492.769.580 bytes, SHA-256 `c72c8f5c1149f1d972e996c2963c5e3dbb31eb38cfe41c2bb1bbaf847d7a7ca1`.

| Etapa | Script | Qué hace | Tiempo (2 CPU, 3 GB de RAM) |
|---|---|---|---|
| 1 | `01_target.py` | Agrega `clase_ternaria` al CSV y guarda `trabajo/base.parquet` | ~30 s |
| 2 | `03_features.py` | Arma las features por mes y las guarda en `trabajo/fe/` | ~3 min |
| 3 | `04_entrenar.py` | Entrena 150 modelos LightGBM y los guarda en `trabajo/modelos/` | ~35 min |
| 4 | `05_predecir_y_armar.py` | Puntúa 202108 y escribe `resultado/` | ~3 min |

Se necesitan unos 1,5 GB de disco para `trabajo/`.

### Verificación hecha

El paquete se corrió desde el CSV crudo en una carpeta vacía, y los resultados son idénticos byte a byte a los originales en las tres capas:

- **Features:** las de los seis meses (202103 a 202108) coinciden con las del pipeline de trabajo.
- **Modelos:** los 150 modelos coinciden con los originales.
- **Archivo final:** el que se genera es el mismo que se entrega.

LightGBM corre con `deterministic=True` y `force_row_wise=True`. Un mismo modelo dio predicciones idénticas con 1, 2 y 4 hilos, así que el resultado no depende de la cantidad de núcleos.

La verificación se hizo en Linux x86_64. En otro sistema operativo o arquitectura (Windows nativo, Mac con ARM) no está probado. Si el hash no coincide ahí, recomiendo correrlo en Linux o WSL con las mismas versiones.

## Método

**Etiqueta.** BAJA+1 si el cliente no aparece en m+1. BAJA+2 si aparece en m+1 pero no en m+2. CONTINUA en el resto. En 202107 solo se conoce BAJA+1.

**Features (`03_features.py`).** Columnas originales más variables de dominio: tarjetas, payroll, consumo sobre límite y transacciones totales. Para cada variable se calculan además las diferencias contra 1 y 2 meses atrás (d1 y d2). Se excluyen 6 variables de calendario que cambian con el foto_mes (`config.EXCLUIR`). A eso se agregan 4 proporciones de dónde está el dinero del cliente (`comun.ext_proporciones`). En total son 462 variables.

**Ensamble de tres familias LightGBM, 50 semillas cada una (150 modelos):**

| Familia | Positivo | Meses de entrenamiento |
|---|---|---|
| base | BAJA+2 | 202103 a 202106 |
| baja12_r | BAJA+1 o BAJA+2 | 202103 a 202107 |
| baja1_r | BAJA+1 | 202103 a 202107 |

En las dos familias `_r`, 202107 aporta la BAJA+1 recién conocida.

**Submuestreo.** Se conservan todas las filas de la clase positiva y el 10 % del resto, de forma determinística por semilla. La probabilidad se corrige por esa tasa.

**Hiperparámetros.** Están en `codigo/hiperparametros.json` y salen de la prueba 62 de Optuna. Se usan 275 rondas (250 × 1,1), porque el entrenamiento final tiene más meses que la validación.

**Puntaje.** Para cada semilla se promedian las posiciones relativas (rangos) de las tres familias, y después se promedia entre las 50 semillas.

**Corte.** Se envían los 10.750 primeros. En el leaderboard público la ganancia fue pareja entre K = 10.500 y 11.000, y 10.750 es el centro de esa meseta. Como referencia, 9.091 clientes tienen probabilidad media mayor a 2,5 % según la familia base.

## Qué no reproduce el script

Hay dos decisiones que se tomaron antes y quedan fijas en el código:

- **Hiperparámetros.** La búsqueda con Optuna está en `anexo_investigacion/codigo/09_experimentos.py`, modo `optuna`. La validación es walk-forward: entrena con 202103 y 202104 y valida en 202106, y entrena con 202103 y valida en 202105.
- **K = 10.750.** Se eligió mirando el leaderboard público.

## Contenido de la carpeta

- `codigo/`: el pipeline mínimo que genera el archivo.
  - `config.py` y `comun.py`: las funciones copiadas literalmente del pipeline de trabajo.
  - Los scripts de las cuatro etapas, `reproducir.py`, `requirements.txt`, `hiperparametros.json` y `sha256_esperado.txt`.
- `anexo_investigacion/`: todo el código de trabajo y los informes de los experimentos (rondas 1 a 9).
  - Incluye lo que se probó y no se adoptó: normalización mensual, canaritos, apilado, validación adversaria, ranking, supervivencia, GRU, entre otros.
  - No hace falta para reproducir la entrega.
- `trabajo/` y `resultado/`: los genera la reproducción. No forman parte del zip.
