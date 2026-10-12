# thenseler-gmail — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: thenseler-gmail
- Repositorio: https://github.com/thenseler-gmail/dmeyf2026
- Link posteado: https://github.com/thenseler-gmail/dmeyf2026/tree/6ea5f3dc13b4e5f7e83953bbf478997a17cd8218/entregas/entrega_final_43
- Commit: c436bf856a2fe4005996208bbfac1845ab17752a
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/thenseler-gmail/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/thenseler-gmail.json

## Resumen

La carpeta posteada (`entregas/entrega_final_43`) es un paquete para reproducir la lista enviada: código Python, cinco modelos LightGBM ya entrenados (`modelos/seed*.txt`), las probabilidades de agosto archivadas de esos cinco modelos y de TabPFN (`artefactos/predicciones_agosto.csv.gz`), la lista final y archivos JSON de configuración, procedencia e integridad. `reproducir.py` lee con DuckDB el mes 202108 y la historia 202103-202108, reconstruye 197 variables (152 originales, 37 históricas de lag, delta y variación relativa a un mes, y 8 de vínculos recurrentes), verifica el hash de la matriz, predice con los cinco modelos guardados (273 árboles cada uno) y compara con las probabilidades archivadas. El score es 0,5 × promedio de las cinco semillas LightGBM + 0,5 × probabilidad archivada de TabPFN; se seleccionan los clientes con score > 0,0275 (10.404) y se exige que el CSV coincida byte por byte, por SHA-256, con el entregado. Según el README, los modelos se entrenaron con abril y mayo de 2021: LightGBM con positivo = BAJA+1 o BAJA+2, y TabPFN con 202 variables y positivo = BAJA+2 en el servicio remoto de Prior Labs. El código que entrenó los LightGBM no está en la carpeta; `recalcular_tabpfn.py` permite volver a ejecutar TabPFN con una key propia.

**Qué entrega.** Un CSV (`prediccion_final.csv`) con 10.404 números de cliente, sin encabezado ni índice, un identificador por línea, ordenados por score descendente: los clientes de 202108 con score mayor que 0,0275. El repositorio incluye ese archivo y `reproducir.py` lo vuelve a generar en `resultado_43/prediccion_final.csv` junto con `resultado_43/VERIFICACION.json`.

**Cómo se ejecuta.** Según el README: crear un entorno con Python 3.14 (`py -3.14 -m venv .venv`) e instalar `requirements.txt`. Corrida principal: `python reproducir.py --dataset <ruta a competencia_01.csv> --salida resultado_43`, que recalcula las variables y las probabilidades LightGBM con los modelos guardados. Corrida sin dataset: `python reproducir.py --salida resultado_43`, que recalcula el ensamble y el corte desde las probabilidades archivadas. De forma opcional, `TABPFN_CATEDRA.md` describe tres pasos con `recalcular_tabpfn.py` en un entorno separado (`requirements-tabpfn.txt`) y la variable de entorno `TABPFN_TOKEN`: verificación local, `--cotizar` y `--ejecutar-api --max-creditos N`. No se indica cómo reentrenar los LightGBM.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM, TabPFN
- **Clase que entrena:** Dos clases binarias, una por modelo. LightGBM: positivo = BAJA+1 o BAJA+2, según el README y `target_lightgbm` de configuracion.json (el código de entrenamiento no está en la carpeta). TabPFN: positivo = BAJA+2 (recalcular_tabpfn.py línea 55 y `target` de configuracion_tabpfn.json).
- **Meses de entrenamiento:** 202104, 202105
- **Meses de validación:** —
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código. El README declara 327.052 filas de entrenamiento (abril y mayo de 2021) y recalcular_tabpfn.py exige esa misma cantidad de filas para la matriz de TabPFN (línea 43).
- **Calidad de datos:** Los valores infinitos se pasan a NaN y los valores de Visa_Fvencimiento y Master_Fvencimiento menores que -36500 se pasan a NaN (reproducir.py líneas 51-53; recalcular_tabpfn.py líneas 50-52). No hay imputación: los faltantes se conservan. Se controla que no haya claves cliente-mes duplicadas.
- **Drifting:** No se observa en el código
- **Variables dentro del mes:** Dos de las 8 variables de vínculos se calculan dentro del mes: `vinculos_familias_actuales` (cuántas de las 4 familias débitos, pagos, préstamos e inversiones tienen algún contador positivo) y `vinculos_servicios_recurrentes` (cuántos de los 5 contadores de débitos automáticos y pagos son mayores que cero). features.py define además `agregar_intrames` (cocientes y sumas de tarjetas y canales), pero ningún script de la carpeta la llama y sus columnas no figuran en las listas de variables.
- **Variables históricas:** Calculadas por mes calendario (unión por cliente y mes desplazado), con historia 202103-202108. En LightGBM, 37 variables: lag 1 y delta 1 de 12 variables (ctrx_quarter, mpayroll, mcuentas_saldo, cproductos, Visa_mconsumototal, Master_mconsumototal, ctarjeta_visa_transacciones, ctarjeta_master_transacciones, chomebanking_transacciones, cmobile_app_trx, ctarjeta_visa, ctarjeta_master), variación relativa a un mes de las mismas 12 (delta dividido por el valor absoluto del mes anterior) e indicador de mes anterior disponible. Además, 6 de las variables de vínculos comparan con el mes anterior (delta de familias, pérdida por familia, delta de servicios recurrentes). La lista de TabPFN suma 13 variables: cantidad de meses previos presentes entre los 3 anteriores y, para 4 variables, media de hasta 3 meses previos, diferencia con esa media y cantidad de observaciones.
- **Selección de variables:** No se observa en el código un procedimiento de selección. La lista de 197 variables de LightGBM está escrita en configuracion.json (`features_lightgbm`) y la de 202 de TabPFN en configuracion_tabpfn.json (`features`); comparten 189 variables, LightGBM agrega las 8 de vínculos y TabPFN las 13 de ventana de 3 meses.
- **Optimización de hiperparámetros:** No se observa en el código de la carpeta posteada. configuracion.json trae los valores ya fijados.
- **Hiperparámetros finales:** LightGBM (configuracion.json): objective binary, boosting_type gbdt, max_bin 31, num_leaves 66, learning_rate 0.06532218918370633, min_data_in_leaf 452, feature_fraction 0.16282786589535145, bagging_fraction 0.8281386632531902, bagging_freq 1, boost_from_average true, feature_pre_filter false, deterministic true, force_col_wise true, num_threads 4, 273 rondas. TabPFN (configuracion_tabpfn.json): model_version v3.5-fast, n_estimators 2, random_state 214363, fit_mode fit_preprocessors, inference_precision autocast, variables categóricas Visa_status, Master_status y tcuentas, SUBSAMPLE_SAMPLES null.
- **Semillas:** Cinco semillas de LightGBM escritas en configuracion.json: 541440, 408476, 741961, 248865 y 717444; a cada una le corresponde un modelo guardado `modelos/seed<semilla>.txt`. TabPFN usa random_state 214363.
- **Cantidad de semillas:** 5
- **Ensamble:** score = 0,5 × promedio de las probabilidades de los 5 LightGBM (uno por semilla) + 0,5 × probabilidad de TabPFN (reproducir.py línea 86; `pesos` en configuracion.json).
- **Corte:** Umbral sobre el score: se seleccionan los clientes con score estrictamente mayor que 0,0275 (reproducir.py línea 92; `umbral` y `operador` en configuracion.json). Resultan 10.404 clientes, ordenados por score descendente y por numero_de_cliente ascendente ante empate. No se observa en la carpeta cómo se eligió el valor 0,0275.
- **Validación:** No se observa en el código una partición de validación ni un cálculo de ganancia. Las comprobaciones del paquete son de reproducción: SHA-256 de los archivos, de la matriz de agosto y de la lista final, y tolerancia absoluta 1e-15 entre probabilidades recalculadas y archivadas. Según procedencia.json, la lista fue seleccionada por su mayor ganancia pública observada (mean 100,815; std dev 0,0).
- **Salidas:** `resultado_43/prediccion_final.csv` (10.404 identificadores, uno por línea, sin encabezado) y `resultado_43/VERIFICACION.json` (estado, cantidad de clientes, SHA-256 de la lista y de la matriz, modo de corrida y diferencia máxima por modelo). `recalcular_tabpfn.py` escribe en `resultado_tabpfn/`: PREPARACION.json, COTIZACION.json, ESTADO_API.json, tabpfn_recalculado.csv, prediccion_final_api.csv y COMPARACION.json.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Otro modelo (`modelo.otro_modelo`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Corta por umbral de probabilidad (`corte.umbral_probabilidad`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Python 3.14.6 (README y configuracion.json). requirements.txt: numpy 2.5.2, pandas 3.0.5, duckdb 1.5.5, lightgbm 4.7.0. Para TabPFN, entorno separado con requirements-tabpfn.txt: tabpfn-client 0.6.1, duckdb 1.5.6, numpy 2.5.3, pandas 2.3.3, scikit-learn 1.9.0, lightgbm 4.7.0. Los comandos de ejemplo son de Windows PowerShell, con indicación equivalente para Linux/macOS. Según el README, TabPFN se ejecutó en el servicio remoto de Prior Labs. No se declara hardware. El comando único (`reproducir.py`) hace inferencia con modelos guardados y probabilidades archivadas; no entrena.

## Pasos del camino de la entrega

1. **Verificación de integridad del paquete.** Antes de cualquier cálculo, `verificar_archivos` recalcula el SHA-256 de los 21 archivos listados en SHA256SUMS.json y detiene la ejecución con un error si alguno difiere. (`entregas/entrega_final_43/reproducir.py` líneas 14–22; `entregas/entrega_final_43/reproducir.py` líneas 76–76; `entregas/entrega_final_43/SHA256SUMS.json` líneas 1–23)
2. **Carga de la configuración y de las probabilidades archivadas.** Lee configuracion.json y `artefactos/predicciones_agosto.csv.gz`, que trae por cliente de 202108 la probabilidad de TabPFN (`p_tabpfn`), las cinco de LightGBM (`p_lgb_seed<semilla>`) y el score (`score_promedio5`). Exige 164.647 filas, todas de 202108 y sin clientes repetidos. (`entregas/entrega_final_43/reproducir.py` líneas 77–80)
3. **Lectura del dataset con DuckDB.** Con `--dataset`, lee el CSV con DuckDB (2 hilos): las filas de 202108 con todas las columnas menos `clase_ternaria` y, para 202103 a 202108, las claves más las 12 columnas fuente de las variables históricas y las 11 de vínculos. Se detiene si hay claves cliente-mes duplicadas. (`entregas/entrega_final_43/reproducir.py` líneas 31–42)
4. **Variables históricas.** `agregar_historicas_ampliadas` une la tabla consigo misma por cliente y mes calendario desplazado 1, 2 y 3 meses. Genera lag 1 y delta 1 de 12 variables, la variación relativa a un mes (delta dividido por el valor absoluto del mes anterior), un indicador de mes anterior disponible y, para 4 variables, la media de hasta 3 meses previos, su diferencia con el valor actual y la cantidad de observaciones. Las primeras 37 entran a LightGBM; las de ventana de 3 meses sólo figuran en la lista de TabPFN. (`entregas/entrega_final_43/features.py` líneas 25–62; `entregas/entrega_final_43/features.py` líneas 100–129; `entregas/entrega_final_43/reproducir.py` líneas 43–45)
5. **Variables de vínculos recurrentes.** `agregar_vinculos` agrupa 11 contadores en cuatro familias (débitos automáticos, pagos, préstamos, inversiones) y calcula 8 variables: cantidad de familias presentes en el mes y su diferencia con el mes calendario anterior, un indicador de pérdida por familia (presente el mes anterior y ausente en el actual) y la cantidad de servicios recurrentes con contador positivo y su diferencia con el mes anterior. (`entregas/entrega_final_43/features_vinculos.py` líneas 5–48; `entregas/entrega_final_43/reproducir.py` líneas 46–48)
6. **Matriz de agosto y limpieza.** Arma la matriz con las 197 columnas de `features_lightgbm` en el orden de configuracion.json, pasa los infinitos a NaN y los valores de Visa_Fvencimiento y Master_Fvencimiento menores que -36500 a NaN, sin imputar. Calcula el SHA-256 de la matriz en float32 y exige que coincida con `matriz_agosto_sha256`. (`entregas/entrega_final_43/reproducir.py` líneas 49–56; `entregas/entrega_final_43/configuracion.json` líneas 15–213; `entregas/entrega_final_43/configuracion.json` líneas 242–242)
7. **Predicción con los cinco LightGBM guardados.** Para cada una de las 5 semillas carga `modelos/seed<semilla>.txt`, comprueba que los nombres de variables coincidan con la lista y que el modelo tenga 273 árboles, predice sobre la matriz de agosto y compara con la probabilidad archivada con tolerancia absoluta 1e-15. Los modelos no se reentrenan; sus hiperparámetros están registrados en configuracion.json. (`entregas/entrega_final_43/reproducir.py` líneas 57–68; `entregas/entrega_final_43/configuracion.json` líneas 8–14; `entregas/entrega_final_43/configuracion.json` líneas 217–235)
8. **Componente TabPFN.** La probabilidad de TabPFN se toma de la columna archivada `p_tabpfn`. Según el README y procedencia.json, proviene de una corrida en el servicio remoto de Prior Labs entrenada con abril y mayo de 2021, 202 variables y positivo = BAJA+2. `recalcular_tabpfn.py` reconstruye esas matrices y, con `--ejecutar-api`, repite la corrida con la configuración de configuracion_tabpfn.json (v3.5-fast, 2 estimadores, random_state 214363); según VALIDACION.json, esa inferencia remota no se ejecutó al armar el paquete. (`entregas/entrega_final_43/reproducir.py` líneas 86–86; `entregas/entrega_final_43/configuracion_tabpfn.json` líneas 1–14; `entregas/entrega_final_43/configuracion_tabpfn.json` líneas 219–227; `entregas/entrega_final_43/recalcular_tabpfn.py` líneas 25–59; `entregas/entrega_final_43/recalcular_tabpfn.py` líneas 107–114; `entregas/entrega_final_43/procedencia.json` líneas 4–5)
9. **Ensamble.** score = 0,5 × promedio de las cinco probabilidades LightGBM + 0,5 × `p_tabpfn`. Comprueba que el score sea finito, esté entre 0 y 1 y coincida con `score_promedio5` archivado con tolerancia absoluta 1e-15. (`entregas/entrega_final_43/reproducir.py` líneas 86–89; `entregas/entrega_final_43/configuracion.json` líneas 236–239)
10. **Corte y orden de la lista.** Ordena por score descendente y por `numero_de_cliente` ascendente ante empate, y conserva los clientes con score estrictamente mayor que 0,0275. (`entregas/entrega_final_43/reproducir.py` líneas 90–93; `entregas/entrega_final_43/configuracion.json` líneas 240–241)
11. **Verificación de la lista y escritura de salidas.** Calcula el SHA-256 del texto de la lista y exige que sea igual a `prediccion_final_sha256` y que haya 10.404 clientes. Escribe `prediccion_final.csv` (un identificador por línea, sin encabezado) y `VERIFICACION.json` en la carpeta de `--salida`, e imprime el informe. (`entregas/entrega_final_43/reproducir.py` líneas 94–108; `entregas/entrega_final_43/configuracion.json` líneas 243–243)

## Archivos

- `entregas/entrega_final_43/reproducir.py` · principal · Python · 112 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/thenseler-gmail/entregas/entrega_final_43/reproducir.py.txt) — Script de entrada. Verifica los archivos del paquete, recalcula (con `--dataset`) o lee (sin él) las probabilidades de los cinco LightGBM, las combina con la probabilidad archivada de TabPFN, aplica el corte 0,0275 y escribe la lista y un informe de verificación.
- `entregas/entrega_final_43/features_vinculos.py` · principal · Python · 94 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/thenseler-gmail/entregas/entrega_final_43/features_vinculos.py.txt) — Calcula las 8 variables de vínculos recurrentes a partir de 11 contadores agrupados en cuatro familias, comparando cada mes con el mes calendario anterior. Trae además dos funciones de verificación (`verificar_independiente` y `verificar_ejemplos`) que reproducir.py no llama.
- `entregas/entrega_final_43/configuracion_tabpfn.json` · configuracion · JSON · 235 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/thenseler-gmail/entregas/entrega_final_43/configuracion_tabpfn.json.txt) — Configuración de la corrida de TabPFN: versión del modelo, cantidad de estimadores, semilla, variables categóricas, lista de 202 variables, meses, clase y hashes de las matrices y del target.
- `entregas/entrega_final_43/requirements.txt` · configuracion · Texto · 4 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/thenseler-gmail/entregas/entrega_final_43/requirements.txt.txt) — Dependencias con versión exacta para la corrida principal: numpy 2.5.2, pandas 3.0.5, duckdb 1.5.5 y lightgbm 4.7.0.
- `entregas/entrega_final_43/features.py` · principal · Python · 129 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/thenseler-gmail/entregas/entrega_final_43/features.py.txt) — Define las listas de variables fuente y las funciones que generan variables históricas por mes calendario (lag, delta, variación relativa y media de hasta 3 meses previos). Incluye también `agregar_intrames`, que ningún script de la carpeta llama.
- `entregas/entrega_final_43/README.md` · explicacion · Markdown · 106 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/thenseler-gmail/entregas/entrega_final_43/README.md.txt) — Texto de presentación de la entrega 43: instalación, corrida principal con el dataset, corrida desde probabilidades archivadas, descripción del modelo y de la regla de selección, lista de artefactos, alcance de la reproducción y resultado público informado (mean 100.8150, std dev 0.0000).
- `entregas/entrega_final_43/recalcular_tabpfn.py` · secundario · Python · 150 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/thenseler-gmail/entregas/entrega_final_43/recalcular_tabpfn.py.txt) — Script opcional, según el README: reconstruye las matrices de entrenamiento (abril y mayo) y de agosto de TabPFN con 202 variables y positivo = BAJA+2, verifica sus hashes y, con `--ejecutar-api`, envía la corrida al servicio de Prior Labs y compara la lista resultante con la entregada. Según VALIDACION.json, el modo remoto no se ejecutó al armar el paquete.
- `entregas/entrega_final_43/SHA256SUMS.json` · configuracion · JSON · 23 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/thenseler-gmail/entregas/entrega_final_43/SHA256SUMS.json.txt) — SHA-256 de 21 archivos del paquete (código, configuraciones, textos, los cinco modelos, las probabilidades archivadas y la lista final). `verificar_archivos` de reproducir.py lo usa para detener la corrida si algún archivo fue modificado.
- `entregas/entrega_final_43/requirements-tabpfn.txt` · configuracion · Texto · 8 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/thenseler-gmail/entregas/entrega_final_43/requirements-tabpfn.txt.txt) — Dependencias con versión exacta para el entorno separado de TabPFN: tabpfn-client 0.6.1, duckdb 1.5.6, numpy 2.5.3, pandas 2.3.3, scikit-learn 1.9.0 y lightgbm 4.7.0. Un comentario indica que la API de Prior Labs no necesita PyTorch ni CUDA local.
- `entregas/entrega_final_43/configuracion.json` · configuracion · JSON · 254 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/thenseler-gmail/entregas/entrega_final_43/configuracion.json.txt) — Parámetros de la entrega 43: meses de entrenamiento y de predicción, las 5 semillas, la lista ordenada de 197 variables de LightGBM, los hiperparámetros y las 273 rondas, los pesos del ensamble, el umbral, los hashes esperados y las versiones de bibliotecas.
- `entregas/entrega_final_43/VALIDACION.json` · explicacion · JSON · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/thenseler-gmail/entregas/entrega_final_43/VALIDACION.json.txt) — Registro de las comprobaciones hechas antes de publicar: corrida con dataset y modelos (estado identico_byte_por_byte, 10.404 clientes, diferencia máxima 0.0 en los cinco modelos), corrida desde probabilidades guardadas (mismo hash) y preparación local de TabPFN (327.052 filas de entrenamiento, 164.647 de agosto, 202 variables). Indica `inferencia_tabpfn_remota_ejecutada`: false.
- `entregas/entrega_final_43/procedencia.json` · explicacion · JSON · 41 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/thenseler-gmail/entregas/entrega_final_43/procedencia.json.txt) — Registro de procedencia: nombre del archivo original de la lista, origen de las probabilidades de TabPFN (entrega 8, reutilizada en las entregas 16 y 43), hashes de los modelos y del código, y el resultado público informado (public_gain_mean 100.815, std dev 0.0) con sus diferencias contra las entregas 36, 41 y 42. La nota final indica que la 43 fue seleccionada por su mayor ganancia pública observada.
- `entregas/entrega_final_43/TABPFN_CATEDRA.md` · explicacion · Markdown · 135 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/thenseler-gmail/entregas/entrega_final_43/TABPFN_CATEDRA.md.txt) — Instrucciones para que la cátedra ejecute TabPFN con cuenta y key propias de Prior Labs: creación de la key, entorno separado, verificación local de las matrices, consulta de costo y ejecución de la API con límite de créditos. Indica que la ejecución original estimaba 74.179 créditos y que el modo de inferencia remota del script no se ejecutó al armar el paquete.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### entregas/entrega_final_43/reproducir.py

Script de entrada. Verifica los archivos del paquete, recalcula (con `--dataset`) o lee (sin él) las probabilidades de los cinco LightGBM, las combina con la probabilidad archivada de TabPFN, aplica el corte 0,0275 y escribe la lista y un informe de verificación.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–11] Importa argparse, hashlib, json, pathlib, numpy y pandas. Define ROOT como la
#   carpeta donde está el script (todas las rutas del paquete son relativas a ella) y KEYS como el par
#   numero_de_cliente, foto_mes.
"""Reproduce la lista 43 desde modelos congelados o probabilidades guardadas."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
KEYS = ['numero_de_cliente', 'foto_mes']


# [Anotación · líneas 14–22] `sha` devuelve el SHA-256 de un archivo. `verificar_archivos` lee SHA256SUMS.json
#   y compara el hash de cada archivo listado con el esperado; si alguno difiere levanta ValueError con el
#   nombre del archivo.
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verificar_archivos():
    hashes = json.loads((ROOT / 'SHA256SUMS.json').read_text(encoding='utf-8'))
    for name, expected in hashes.items():
        if sha(ROOT / name) != expected:
            raise ValueError(f'Artefacto modificado: {name}')


# [Anotación · líneas 25–30] Comienzo de `inferir`, que sólo se usa cuando se pasa `--dataset`. Importa dentro
#   de la función duckdb, lightgbm y las listas y funciones de features.py y features_vinculos.py.
def inferir(dataset, ref, config):
    import duckdb
    import lightgbm as lgb
    from features import HISTORICAS, HISTORICAS_EXTRA, agregar_historicas_ampliadas
    from features_vinculos import FUENTES, agregar_vinculos

# [Anotación · líneas 31–42] Abre DuckDB con 2 hilos y registra el CSV como vista. Extrae las filas de 202108
#   con todas las columnas menos `clase_ternaria`, ordenadas por mes y cliente, y, para los meses 202103 a
#   202108, las claves más las columnas fuente de las variables históricas y de vínculos. Levanta un error si
#   hay claves cliente-mes duplicadas.
    # Las etiquetas no se extraen para inferencia, ni siquiera las de agosto.
    with duckdb.connect() as con:
        con.execute('SET threads=2')
        con.read_csv(str(dataset)).create_view('datos')
        raw = con.sql('SELECT * EXCLUDE(clase_ternaria) FROM datos '
                      'WHERE foto_mes=202108 ORDER BY foto_mes,numero_de_cliente').df()
        columns = list(dict.fromkeys(KEYS + HISTORICAS + HISTORICAS_EXTRA + FUENTES))
        history = con.sql('SELECT ' + ','.join(columns) + ' FROM datos '
                          'WHERE foto_mes BETWEEN 202103 AND 202108 '
                          'ORDER BY foto_mes,numero_de_cliente').df()
    if raw.duplicated(KEYS).any() or history.duplicated(KEYS).any():
        raise ValueError('Claves cliente-mes duplicadas')
# [Anotación · líneas 43–48] Calcula las variables históricas sobre los seis meses, se queda con las columnas
#   derivadas y las une uno a uno a las filas de agosto; hace lo mismo con las variables de vínculos. Comprueba
#   que las claves queden iguales y en el mismo orden que en el archivo de probabilidades archivadas.
    hist = agregar_historicas_ampliadas(history[KEYS + HISTORICAS + HISTORICAS_EXTRA])
    derived = [c for c in hist if c not in KEYS + HISTORICAS + HISTORICAS_EXTRA]
    raw = raw.merge(hist[KEYS + derived], on=KEYS, validate='one_to_one', sort=False)
    raw = raw.merge(agregar_vinculos(history[KEYS + FUENTES]), on=KEYS,
                    validate='one_to_one', sort=False)
    pd.testing.assert_frame_equal(raw[KEYS], ref[KEYS])
# [Anotación · líneas 49–56] Arma la matriz con las 197 columnas de `features_lightgbm` como float, reemplaza
#   +inf y -inf por NaN y pasa a NaN los valores de Visa_Fvencimiento y Master_Fvencimiento menores que -36500.
#   Calcula el SHA-256 de la matriz en float32 y levanta un error si no coincide con `matriz_agosto_sha256` de
#   la configuración.
    # Mismas reglas fijas de baseline.preparar; sin imputacion ni correccion posterior.
    x = raw[config['features_lightgbm']].astype(float).copy()
    x = x.replace([np.inf, -np.inf], np.nan)
    for c in ['Visa_Fvencimiento', 'Master_Fvencimiento']:
        x.loc[x[c] < -36500, c] = np.nan
    matrix_hash = hashlib.sha256(x.to_numpy(dtype=np.float32).tobytes()).hexdigest()
    if matrix_hash != config['matriz_agosto_sha256']:
        raise ValueError('La matriz de agosto difiere de la utilizada en la entrega 43')
# [Anotación · líneas 57–68] Para cada una de las 5 semillas carga el modelo `modelos/seed<semilla>.txt`,
#   exige que sus nombres de variables sean los de la lista y que tenga 273 árboles, predice con 4 hilos y
#   compara con la columna archivada `p_lgb_seed<semilla>` con tolerancia absoluta 1e-15. Guarda la diferencia
#   máxima por modelo y devuelve la matriz de probabilidades (una columna por semilla), el hash de la matriz y
#   las diferencias.
    probabilities = []
    errors = {}
    for seed in config['semillas']:
        model = lgb.Booster(model_file=str(ROOT / 'modelos' / f'seed{seed}.txt'))
        if model.feature_name() != config['features_lightgbm'] or model.num_trees() != 273:
            raise ValueError('Modelo incompatible')
        p = model.predict(x, validate_features=True, num_threads=4)
        expected = ref[f'p_lgb_seed{seed}'].to_numpy()
        np.testing.assert_allclose(p, expected, rtol=0, atol=1e-15)
        errors[str(seed)] = float(np.max(np.abs(p - expected)))
        probabilities.append(p)
    return np.column_stack(probabilities), matrix_hash, errors


# [Anotación · líneas 71–80] `main` define los argumentos `--dataset` (opcional) y `--salida` (por defecto
#   `resultado_43`), verifica los archivos del paquete, lee configuracion.json y
#   `artefactos/predicciones_agosto.csv.gz` con precisión de ida y vuelta para los decimales. Exige 164.647
#   filas, todas de 202108 y sin numero_de_cliente repetido.
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, help='competencia_01.csv original: recalcula LightGBM')
    parser.add_argument('--salida', type=Path, default=Path('resultado_43'))
    args = parser.parse_args()
    verificar_archivos()
    config = json.loads((ROOT / 'configuracion.json').read_text(encoding='utf-8'))
    ref = pd.read_csv(ROOT / 'artefactos' / 'predicciones_agosto.csv.gz', float_precision='round_trip')
    if len(ref) != 164647 or not ref.foto_mes.eq(202108).all() or ref.numero_de_cliente.duplicated().any():
        raise ValueError('Referencia de agosto incompatible')
# [Anotación · líneas 81–85] Si se pasó `--dataset`, las probabilidades LightGBM se recalculan con `inferir`;
#   si no, se toman las cinco columnas `p_lgb_seed<semilla>` archivadas.
    matrix_hash, errors = None, {}
    if args.dataset:
        probabilities, matrix_hash, errors = inferir(args.dataset.resolve(), ref, config)
    else:
        probabilities = ref[[f'p_lgb_seed{s}' for s in config['semillas']]].to_numpy()
# [Anotación · líneas 86–89] Calcula el score como 0,5 × promedio por fila de las cinco probabilidades
#   LightGBM + 0,5 × `p_tabpfn` archivada. Levanta un error si algún score no es finito o queda fuera de [0, 1],
#   y compara con la columna archivada `score_promedio5` con tolerancia absoluta 1e-15.
    score = .5 * probabilities.mean(axis=1) + .5 * ref.p_tabpfn.to_numpy()
    if not np.isfinite(score).all() or ((score < 0) | (score > 1)).any():
        raise ValueError('Scores invalidos')
    np.testing.assert_allclose(score, ref.score_promedio5, rtol=0, atol=1e-15)
# [Anotación · líneas 90–96] Ordena con np.lexsort por score descendente y numero_de_cliente ascendente,
#   conserva los que tienen score mayor que `umbral` (0,0275) y arma el texto con un identificador por línea.
#   Calcula su SHA-256 y levanta un error si no coincide con `prediccion_final_sha256` o si la cantidad no es
#   10.404.
    ids = ref.numero_de_cliente.to_numpy()
    selected = np.lexsort((ids, -score))
    selected = selected[score[selected] > config['umbral']]
    content = ''.join(f'{int(ids[i])}\n' for i in selected).encode('ascii')
    result_hash = hashlib.sha256(content).hexdigest()
    if result_hash != config['prediccion_final_sha256'] or len(selected) != 10404:
        raise ValueError('La lista generada no coincide exactamente con la entrega 43')
# [Anotación · líneas 97–108] Crea la carpeta de salida, rechaza escribir sobre el `prediccion_final.csv` del
#   paquete, y escribe `prediccion_final.csv` y `VERIFICACION.json` con el estado, la cantidad de clientes, el
#   SHA-256, el modo (`modelos_y_dataset` o `probabilidades_guardadas`), el hash de la matriz, la diferencia
#   máxima por modelo, `api` False y `creditos` 0. Imprime el mismo informe.
    args.salida.mkdir(parents=True, exist_ok=True)
    output = args.salida / 'prediccion_final.csv'
    # Nunca sobrescribir un artefacto firmado del paquete.
    if output.resolve().is_relative_to(ROOT) and output.resolve() == (ROOT / 'prediccion_final.csv').resolve():
        raise ValueError('Elegir otra carpeta de salida')
    output.write_bytes(content)
    report = dict(estado='identico_byte_por_byte', contactos=len(selected), sha256=result_hash,
                  modo='modelos_y_dataset' if args.dataset else 'probabilidades_guardadas',
                  matriz_agosto_sha256=matrix_hash, error_maximo_por_modelo=errors,
                  api=False, creditos=0)
    (args.salida / 'VERIFICACION.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


# [Anotación · líneas 111–112] Punto de entrada: ejecuta `main` cuando el archivo se corre como script.
if __name__ == '__main__':
    main()
```

### entregas/entrega_final_43/features_vinculos.py

Calcula las 8 variables de vínculos recurrentes a partir de 11 contadores agrupados en cuatro familias, comparando cada mes con el mes calendario anterior. Trae además dos funciones de verificación (`verificar_independiente` y `verificar_ejemplos`) que reproducir.py no llama.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–3] Docstring del módulo e importación de numpy y pandas.
"""Ocho señales de vínculos recurrentes; mes calendario anterior, sin etiquetas."""
import numpy as np
import pandas as pd

# [Anotación · líneas 5–14] FAMILIAS agrupa 11 contadores en cuatro familias: debitos (3 columnas de débitos
#   automáticos en cuenta, Visa y Master), pagos (cpagodeservicios, cpagomiscuentas), prestamos (personales,
#   prendarios, hipotecarios) e inversiones (cplazo_fijo, cinversion1, cinversion2). FUENTES es la lista de las
#   11 columnas y FEATURES los 8 nombres de salida.
KEYS=['numero_de_cliente','foto_mes']
FAMILIAS={
    'debitos':['ccuenta_debitos_automaticos','ctarjeta_visa_debitos_automaticos','ctarjeta_master_debitos_automaticos'],
    'pagos':['cpagodeservicios','cpagomiscuentas'],
    'prestamos':['cprestamos_personales','cprestamos_prendarios','cprestamos_hipotecarios'],
    'inversiones':['cplazo_fijo','cinversion1','cinversion2'],
}
FUENTES=[c for cols in FAMILIAS.values() for c in cols]
FEATURES=['vinculos_familias_actuales','vinculos_delta_familias']+[
    'vinculos_perdida_'+f for f in FAMILIAS]+['vinculos_servicios_recurrentes','vinculos_delta_servicios_recurrentes']

# [Anotación · líneas 16–22] `presentes` devuelve por familia 1 si alguna de sus columnas es mayor que cero, 0
#   si todas valen cero y NaN en cualquier otro caso (por ejemplo, faltantes o negativos sin ningún positivo).
def presentes(frame):
    flags={}
    for family,cols in FAMILIAS.items():
        positive=frame[cols].gt(0).any(axis=1)
        zero=frame[cols].eq(0).all(axis=1)
        flags[family]=positive.astype(float).where(positive|zero)
    return pd.DataFrame(flags,index=frame.index)

# [Anotación · líneas 24–34] `agregar_vinculos` levanta un error si las claves tienen nulos o duplicados, pasa
#   las 11 fuentes a float con los infinitos como NaN y obtiene los valores del mes calendario anterior de cada
#   cliente uniendo la tabla consigo misma por cliente y número de mes (año × 12 + mes) aumentado en 1.
def agregar_vinculos(datos):
    if datos[KEYS].isna().any().any() or datos.duplicated(KEYS).any():
        raise ValueError('Claves incompletas o duplicadas')
    x=datos[FUENTES].astype(float).replace([np.inf,-np.inf],np.nan)
    date=pd.to_datetime(datos.foto_mes.astype(str),format='%Y%m')
    ordinal=date.dt.year*12+date.dt.month
    previous=pd.concat([datos[['numero_de_cliente']].reset_index(drop=True),x.reset_index(drop=True)],axis=1)
    previous['_mes']=ordinal.to_numpy()+1
    current=datos[['numero_de_cliente']].copy();current['_mes']=ordinal.to_numpy()
    lag=current.merge(previous,on=['numero_de_cliente','_mes'],how='left',sort=False,validate='one_to_one')[FUENTES]
    lag.index=datos.index
# [Anotación · líneas 35–39] Calcula el estado por familia en el mes actual y en el anterior y cuenta las
#   familias presentes (0 a 4), dejando NaN si falta alguna de las 11 fuentes o si el estado de alguna familia
#   es desconocido. `vinculos_familias_actuales` es la cuenta actual y `vinculos_delta_familias` la cuenta
#   actual menos la del mes anterior.
    now=presentes(x);before=presentes(lag)
    count=now.sum(axis=1,min_count=4).where(x.notna().all(axis=1))
    count_before=before.sum(axis=1,min_count=4).where(lag.notna().all(axis=1))
    out=datos[KEYS].copy()
    out[FEATURES[0]]=count;out[FEATURES[1]]=count-count_before
# [Anotación · líneas 40–42] Para cada familia crea `vinculos_perdida_<familia>`: 1 si la familia estaba
#   presente el mes anterior y no lo está en el actual, 0 en otro caso, y NaN si alguno de los dos estados es
#   desconocido.
    for family in FAMILIAS:
        known=now[family].notna()&before[family].notna()
        out['vinculos_perdida_'+family]=((before[family]==1)&(now[family]==0)).astype(float).where(known)
# [Anotación · líneas 43–48] Toma las 5 columnas de débitos y pagos como servicios recurrentes.
#   `vinculos_servicios_recurrentes` cuenta cuántas son mayores que cero (NaN si falta alguna) y
#   `vinculos_delta_servicios_recurrentes` es esa cuenta menos la del mes anterior. Comprueba el orden de las
#   columnas de salida y devuelve la tabla.
    recurrent=FAMILIAS['debitos']+FAMILIAS['pagos']
    services=x[recurrent].gt(0).sum(axis=1).astype(float).where(x[recurrent].notna().all(axis=1))
    services_before=lag[recurrent].gt(0).sum(axis=1).astype(float).where(lag[recurrent].notna().all(axis=1))
    out[FEATURES[-2]]=services;out[FEATURES[-1]]=services-services_before
    assert list(out)==KEYS+FEATURES
    return out

# [Anotación · líneas 50–74] `verificar_independiente` vuelve a calcular las 8 variables con arreglos de NumPy
#   y un diccionario (cliente, mes) → fila para ubicar el mes anterior, sin usar merge, y exige igualdad exacta
#   con el resultado de `agregar_vinculos`. Devuelve un resumen con la cantidad de filas, fuentes y variables.
def verificar_independiente(datos,result):
    """Reconstrucción por diccionarios de familias y lookup calendario, sin merge."""
    pd.testing.assert_frame_equal(result[KEYS],datos[KEYS])
    x=datos[FUENTES].astype(float).replace([np.inf,-np.inf],np.nan)
    names=list(FAMILIAS)
    def state(arr):
        positive=(arr>0).any(axis=1);zero=(arr==0).all(axis=1)
        return np.where(positive,1.,np.where(zero,0.,np.nan))
    family={f:state(x[cols].to_numpy()) for f,cols in FAMILIAS.items()}
    flags=np.column_stack([family[f] for f in names])
    count=np.where(x.notna().all(axis=1),flags.sum(axis=1),np.nan)
    rc=FAMILIAS['debitos']+FAMILIAS['pagos']
    services=np.where(x[rc].notna().all(axis=1),(x[rc].to_numpy()>0).sum(axis=1),np.nan)
    months=pd.PeriodIndex(datos.foto_mes.astype(str),freq='M')
    lookup={(int(cid),month):i for i,(cid,month) in enumerate(zip(datos.numero_de_cliente,months))}
    indices=np.array([lookup.get((int(cid),month-1),-1) for cid,month in zip(datos.numero_de_cliente,months)])
    valid=indices>=0
    def prev(a):
        b=np.full(len(a),np.nan);b[valid]=a[indices[valid]];return b
    expected={FEATURES[0]:count,FEATURES[1]:count-prev(count),FEATURES[-2]:services,FEATURES[-1]:services-prev(services)}
    for f in names:
        before=prev(family[f]);current=family[f]
        expected['vinculos_perdida_'+f]=np.where(np.isfinite(before)&np.isfinite(current),((before==1)&(current==0)).astype(float),np.nan)
    for c in FEATURES:np.testing.assert_allclose(result[c],expected[c],rtol=0,atol=0,equal_nan=True)
    return dict(estado='verificado',filas=len(datos),fuentes=len(FUENTES),features=len(FEATURES),regla='mes calendario; faltantes desconocidos')

# [Anotación · líneas 76–94] `verificar_ejemplos` arma una tabla de 7 filas con 3 clientes que incluye un
#   cambio de año (202012 a 202101), un mes salteado, un NaN, un positivo parcial y un valor negativo, y
#   comprueba valores esperados de delta y pérdida. También comprueba que agregar una columna `clase_ternaria` o
#   reordenar las filas no cambia el resultado.
def verificar_ejemplos():
    toy=pd.DataFrame({'numero_de_cliente':[1,1,1,2,2,3,3],
        'foto_mes':[202012,202101,202103,202101,202102,202101,202102]})
    for c in FUENTES:toy[c]=[1.,0.,0.,0.,0.,0.,0.]
    toy.loc[3,FAMILIAS['debitos'][0]]=np.nan
    toy.loc[3,FAMILIAS['debitos'][1]]=1.
    toy.loc[5,FAMILIAS['prestamos'][0]]=-1.
    a=agregar_vinculos(toy);verificar_independiente(toy,a)
    assert a.loc[1,'vinculos_delta_familias']==-4
    assert a.loc[1,'vinculos_perdida_debitos']==1
    assert pd.isna(a.loc[2,'vinculos_delta_familias'])
    assert a.loc[4,'vinculos_perdida_debitos']==1
    assert pd.isna(a.loc[4,'vinculos_delta_familias'])
    assert pd.isna(a.loc[6,'vinculos_perdida_prestamos'])
    changed=toy.copy();changed['clase_ternaria']='BAJA+2'
    pd.testing.assert_frame_equal(a,agregar_vinculos(changed))
    reordered=toy.sample(frac=1,random_state=7)
    pd.testing.assert_frame_equal(a.sort_index(),agregar_vinculos(reordered).sort_index())
    return dict(estado='verificado',checks=['cambio de año','huecos','positivo parcial','nulos','negativos','sin etiquetas','orden'])
```

### entregas/entrega_final_43/features.py

Define las listas de variables fuente y las funciones que generan variables históricas por mes calendario (lag, delta, variación relativa y media de hasta 3 meses previos). Incluye también `agregar_intrames`, que ningún script de la carpeta llama.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–3] Docstring del módulo e importación de numpy y pandas.
"""Features intrames e históricas. No usan etiquetas ni aprenden del test."""
import numpy as np
import pandas as pd

# [Anotación · líneas 5–17] CANALES lista 8 contadores de transacciones por canal (home banking, app móvil,
#   tarjeta de débito, Visa, Master, cajeros, cajas y call center). BLOQUES asigna a tres bloques (actividad,
#   tarjetas, utilizacion) los nombres de las variables intra mes que genera `agregar_intrames`.
# Mismos ocho componentes del notebook previo; incluye canales y tarjetas.
CANALES = [
    'chomebanking_transacciones', 'cmobile_app_trx',
    'ctarjeta_debito_transacciones', 'ctarjeta_visa_transacciones',
    'ctarjeta_master_transacciones', 'catm_trx',
    'ccajas_transacciones', 'ccallcenter_transacciones',
]
BLOQUES = {
    'actividad': ['actividad_por_producto', 'cantidad_canales_activos'],
    'tarjetas': ['tarjetas_saldo_total', 'tarjetas_consumo_total', 'tarjetas_limite_total'],
    'utilizacion': ['Visa_saldo_sobre_limite', 'Visa_consumo_sobre_limite',
                    'Master_saldo_sobre_limite', 'Master_consumo_sobre_limite'],
}
# [Anotación · líneas 18–22] HISTORICAS son 4 variables (ctrx_quarter, mpayroll, mcuentas_saldo, cproductos) y
#   HISTORICAS_EXTRA otras 8 (consumo total y transacciones de Visa y Master, transacciones de home banking y de
#   la app móvil, y cantidad de tarjetas Visa y Master). Son las 12 fuentes de las variables históricas.
HISTORICAS = ['ctrx_quarter', 'mpayroll', 'mcuentas_saldo', 'cproductos']
HISTORICAS_EXTRA = ['Visa_mconsumototal', 'Master_mconsumototal',
                    'ctarjeta_visa_transacciones', 'ctarjeta_master_transacciones',
                    'chomebanking_transacciones', 'cmobile_app_trx',
                    'ctarjeta_visa', 'ctarjeta_master']


# [Anotación · líneas 25–37] `agregar_historicas_ampliadas` parte del resultado de `agregar_historicas` (lag 1
#   y delta 1 de las 4 HISTORICAS). Convierte foto_mes en un número de mes (año × 12 + mes) y prepara la tabla
#   de cliente y mes actual; las fuentes son las 12 variables.
def agregar_historicas_ampliadas(datos):
    """Bloque anterior + lags/deltas relativos y promedio de hasta 3 meses previos.

    Solo historia pasada; promedios ignoran faltantes y registran cobertura.
    La variación relativa usa el valor absoluto anterior, sin dividir por cero.
    """
    out = agregar_historicas(datos)
    keys = ['numero_de_cliente', 'foto_mes']
    fechas = pd.to_datetime(datos.foto_mes.astype(str), format='%Y%m')
    ordinal = fechas.dt.year * 12 + fechas.dt.month
    actual = datos[['numero_de_cliente']].copy()
    actual['_mes'] = ordinal.to_numpy()
    fuentes = HISTORICAS + HISTORICAS_EXTRA
# [Anotación · líneas 38–47] Para los desplazamientos 1, 2 y 3 copia las fuentes, suma el desplazamiento al
#   número de mes y une por cliente y mes, de modo que cada fila recibe los valores del mismo cliente 1, 2 y 3
#   meses calendario antes. Guarda esos valores y un indicador 0/1 de si el mes previo existe para el cliente.
    pasados = []
    coberturas = []
    for lag in (1, 2, 3):
        previo = datos[['numero_de_cliente', *fuentes]].copy()
        previo['_mes'] = ordinal.to_numpy() + lag
        previo['_presente'] = 1
        unido = actual.merge(previo, on=['numero_de_cliente', '_mes'], how='left',
                             sort=False, validate='one_to_one')
        pasados.append(unido[fuentes].reset_index(drop=True))
        coberturas.append(unido['_presente'].fillna(0).to_numpy())
# [Anotación · líneas 48–54] Para las 8 HISTORICAS_EXTRA crea `lag_1_<variable>` y `delta_1_<variable>` (valor
#   actual menos el del mes anterior). Para las 12 fuentes crea `variacion_relativa_1_<variable>`: el delta
#   dividido por el valor absoluto del mes anterior, mediante `ratio_seguro`.
    for c in HISTORICAS_EXTRA:
        anterior = pasados[0][c].to_numpy()
        out['lag_1_' + c] = anterior
        out['delta_1_' + c] = out[c] - anterior
    for c in fuentes:
        denominador = pd.Series(pasados[0][c].abs().to_numpy(), index=out.index)
        out['variacion_relativa_1_' + c] = ratio_seguro(out[c] - out['lag_1_' + c], denominador)
# [Anotación · líneas 55–62] `historial_meses_previos_3` cuenta cuántos de los 3 meses anteriores existen para
#   el cliente. Para las 4 HISTORICAS calcula `media_previa_3_` (media de hasta 3 meses previos, ignorando
#   faltantes), `delta_media_previa_3_` (valor actual menos esa media) y `observaciones_previas_3_` (cantidad de
#   valores no nulos entre los tres). Devuelve la tabla.
    out['historial_meses_previos_3'] = np.sum(coberturas, axis=0).astype(int)
    for c in HISTORICAS:
        valores = pd.concat([p[c] for p in pasados], axis=1)
        media = valores.mean(axis=1).to_numpy()
        out['media_previa_3_' + c] = media
        out['delta_media_previa_3_' + c] = out[c] - media
        out['observaciones_previas_3_' + c] = valores.notna().sum(axis=1).to_numpy()
    return out


# [Anotación · líneas 65–68] `ratio_seguro` divide numerador por denominador y devuelve NaN cuando el
#   denominador es menor o igual que cero, falta alguna de las dos fuentes o el resultado es infinito.
def ratio_seguro(numerador, denominador):
    """NaN si falta una fuente, el denominador es <= 0 o resulta infinito."""
    return (numerador / denominador.where(denominador > 0)).replace(
        [np.inf, -np.inf], np.nan)


# [Anotación · líneas 71–83] `agregar_intrames` recibe una tabla y una lista de bloques. Levanta un error si
#   se pide un bloque que no está en BLOQUES o si alguna de las columnas nuevas ya existe, y copia la tabla. Ni
#   reproducir.py ni recalcular_tabpfn.py importan esta función.
def agregar_intrames(x, bloques):
    """Conserva originales e índice. Los nulos no se convierten en ceros.

    Sumas de tarjetas estrictas: un componente desconocido deja total NaN.
    Canales: si alguno es desconocido, el conteo total es desconocido.
    No se normalizan ratios a [0,1]: exceder el límite puede ser información.
    """
    if set(bloques) - BLOQUES.keys():
        raise ValueError('Bloque intrames desconocido.')
    nuevas = [c for b in bloques for c in BLOQUES[b]]
    if set(nuevas) & set(x.columns):
        raise ValueError('Las features ya existen; no sobrescribirlas.')
    out = x.copy()
# [Anotación · líneas 84–97] Bloque actividad: `actividad_por_producto` = ctrx_quarter / cproductos y
#   `cantidad_canales_activos` = cantidad de los 8 canales con transacciones mayores que cero (NaN si falta
#   algún canal). Bloque tarjetas: suma Visa + Master de saldo total, consumo total y límite de compra. Bloque
#   utilizacion: para Visa y Master, saldo total y consumo total divididos por el límite de compra.
    if 'actividad' in bloques:
        out['actividad_por_producto'] = ratio_seguro(x.ctrx_quarter, x.cproductos)
        uso = x[CANALES].gt(0).astype(float).where(x[CANALES].notna())
        out['cantidad_canales_activos'] = uso.sum(axis=1, min_count=len(CANALES))
    if 'tarjetas' in bloques:
        for fuente, destino in [('msaldototal', 'saldo'), ('mconsumototal', 'consumo'),
                                ('mlimitecompra', 'limite')]:
            out[f'tarjetas_{destino}_total'] = x[f'Visa_{fuente}'] + x[f'Master_{fuente}']
    if 'utilizacion' in bloques:
        for marca in ['Visa', 'Master']:
            for fuente, destino in [('msaldototal', 'saldo'), ('mconsumototal', 'consumo')]:
                out[f'{marca}_{destino}_sobre_limite'] = ratio_seguro(
                    x[f'{marca}_{fuente}'], x[f'{marca}_mlimitecompra'])
    return out


# [Anotación · líneas 100–111] `agregar_historicas` levanta un error si las claves cliente-mes tienen nulos o
#   duplicados y convierte foto_mes en un número de mes (año × 12 + mes).
def agregar_historicas(datos):
    """Lag de un mes calendario y delta actual-anterior de cuatro variables.

    El argumento debe incluir historia auxiliar (por ejemplo abril para mayo).
    Conserva orden e índice. No hace shift por registro ni usa el target.
    No se usa todavía en el baseline: marzo no tiene febrero en el dataset.
    """
    keys = ['numero_de_cliente', 'foto_mes']
    if datos[keys].isna().any().any() or datos.duplicated(keys).any():
        raise ValueError('Claves incompletas o duplicadas.')
    meses = pd.to_datetime(datos.foto_mes.astype(str), format='%Y%m', errors='raise')
    numero_mes = meses.dt.year * 12 + meses.dt.month
# [Anotación · líneas 112–119] Arma una tabla con las 4 HISTORICAS renombradas a `lag_1_<variable>`, con el
#   número de mes aumentado en 1 y un indicador de disponibilidad, y la une por cliente y mes a las filas
#   actuales (unión izquierda, uno a uno). Así cada fila recibe los valores del mes calendario anterior del
#   mismo cliente.
    anterior = datos[['numero_de_cliente', *HISTORICAS]].copy()
    anterior['_mes'] = numero_mes.to_numpy() + 1
    anterior['historial_mes_anterior_disponible'] = 1
    anterior = anterior.rename(columns={c: 'lag_1_' + c for c in HISTORICAS})
    actual = datos[['numero_de_cliente']].copy()
    actual['_mes'] = numero_mes.to_numpy()
    unidos = actual.merge(anterior, on=['numero_de_cliente', '_mes'], how='left',
                           sort=False, validate='one_to_one')
# [Anotación · líneas 120–129] Agrega a una copia de la tabla `lag_1_<variable>` y `delta_1_<variable>` (valor
#   actual menos lag) para las 4 variables, levantando un error si ya existían, y
#   `historial_mes_anterior_disponible` (1 si el cliente tiene fila en el mes anterior, 0 si no). Devuelve la
#   tabla con el orden e índice originales.
    out = datos.copy()
    for c in HISTORICAS:
        lag = 'lag_1_' + c
        if lag in out or 'delta_1_' + c in out:
            raise ValueError('Las features históricas ya existen.')
        out[lag] = unidos[lag].to_numpy()
        out['delta_1_' + c] = out[c] - out[lag]
    out['historial_mes_anterior_disponible'] = unidos[
        'historial_mes_anterior_disponible'].fillna(0).astype(int).to_numpy()
    return out
```


## Explicaciones del alumno (texto original)

### entregas/entrega_final_43/README.md

> # Prediccion final de churn — entrega 43
>
> Esta carpeta contiene el codigo, los cinco modelos LightGBM y la salida congelada
> de TabPFN utilizados para reproducir **exactamente** la prediccion final. El CSV
> entregado tiene 10.404 clientes, sin encabezado ni indice, un identificador por
> linea. La reproduccion verifica su igualdad byte por byte mediante SHA-256:
>
> ```text
> 4dcf5eff118dafa41953f66999203db6818017975d52010bad33c4881985496e
> ```
>
> ## Instalacion
>
> Descargar o clonar el repositorio y abrir una terminal en esta carpeta. Se verifico
> con Python 3.14.6; las versiones exactas de las bibliotecas estan en
> `requirements.txt`. Ejemplo en Windows PowerShell:
>
> ```powershell
> py -3.14 -m venv .venv
> .\.venv\Scripts\python.exe -m pip install -r requirements.txt
> ```
>
> En Linux/macOS, crear el entorno con `python3.14 -m venv .venv` y usar
> `.venv/bin/python` en los comandos siguientes.
>
> ## Corrida principal: inferencia desde el dataset y los modelos
>
> Usar el archivo original `competencia_01.csv` provisto por la catedra, con los
> meses marzo a agosto de 2021 y los nombres de columnas originales. El dataset no
> se incluye en GitHub. Se puede pasar una ruta absoluta; no requiere moverlo al
> repositorio ni modificar configuraciones.
>
> ```powershell
> .\.venv\Scripts\python.exe reproducir.py --dataset "C:\ruta\competencia_01.csv" --salida resultado_43
> ```
>
> El script reconstruye las 197 variables de agosto usando historia pasada,
> comprueba el hash de la matriz original, carga los cinco modelos guardados y
> recalcula sus probabilidades. Luego incorpora las probabilidades originales de
> TabPFN, calcula el ensamble, aplica el corte y genera:
>
> - `resultado_43/prediccion_final.csv`: lista final identica a la entregada.
> - `resultado_43/VERIFICACION.json`: hash, cantidad de clientes, hash de la matriz
>   y diferencias contra las probabilidades historicas de cada modelo.
>
> En una corrida correcta se imprime `estado: identico_byte_por_byte`. La tolerancia
> de comparacion de probabilidades es 1e-15; la exigencia para el CSV es igualdad
> exacta. Una matriz o lista diferente provoca un error. La inferencia no extrae
> etiquetas y no requiere API, credenciales ni consumo de creditos.
>
> ## Corrida rapida: reconstruccion desde las probabilidades archivadas
>
> ```powershell
> .\.venv\Scripts\python.exe reproducir.py --salida resultado_43
> ```
>
> Esta alternativa no requiere el dataset: recalcula el ensamble y la seleccion
> desde sus seis componentes guardados. Permite auditar inmediatamente la lista;
> la corrida principal tambien verifica las variables y la inferencia LightGBM.
>
> ## Modelo y regla de seleccion
>
> Entrenamiento original: abril y mayo de 2021, 327.052 filas. Prediccion: agosto
> de 2021, 164.647 clientes. Los cinco LightGBM usan 197 variables (152 originales,
> 37 de historia y ocho de vinculos recurrentes), 273 arboles y las semillas
> 541440, 408476, 741961, 248865 y 717444. Su target es BAJA+1 o BAJA+2. Los parametros
> y el orden exacto de las variables estan en `configuracion.json`.
>
> TabPFN usa 202 variables y target BAJA+2; se reutiliza su prediccion original
> abril+mayo -> agosto. La mezcla es un score de seleccion:
>
> ```text
> score = 0.5 * promedio(p_lightgbm_de_las_5_semillas) + 0.5 * p_tabpfn
> seleccionar si score > 0.0275
> ordenar por score descendente, y por numero_de_cliente ascendente ante empate
> ```
>
> No hay segmentacion. Las variables historicas y los vinculos se calculan por
> mes calendario; los faltantes se preservan. Los valores no finitos se convierten
> en faltantes y los vencimientos Visa/Master menores que -36500 se convierten en
> faltantes, siguiendo el preprocesamiento original.
>
> ## Artefactos y alcance de la reproduccion
>
> - `reproducir.py`: inferencia, ensamble, seleccion y verificacion.
> - `features.py`, `features_vinculos.py`: codigo original de las variables.
> - `modelos/seed*.txt`: cinco modelos LightGBM originales, sin reentrenamiento.
> - `artefactos/predicciones_agosto.csv.gz`: probabilidades originales de los cinco
>   LightGBM, TabPFN y el score, con claves para verificar su alineacion.
> - `prediccion_final.csv`: referencia exacta de la lista entregada.
> - `configuracion.json`, `procedencia.json`, `SHA256SUMS.json`: configuracion,
>   procedencia y firmas de integridad.
> - `VALIDACION.json`: evidencia de las dos corridas verificadas antes de publicar.
>
> La reproduccion exacta corresponde a **inferencia y seleccion con artefactos
> congelados**. TabPFN se ejecuto originalmente en el servicio remoto de Prior Labs;
> se incluye su salida para evitar depender de acceso, costo y cambios del servicio.
> La corrida principal usa esa salida archivada. Adicionalmente,
> `recalcular_tabpfn.py` permite ejecutar la configuracion original con una key propia
> de la catedra y verificar si reproduce exactamente la lista. Las instrucciones
> estan en [TABPFN_CATEDRA.md](TABPFN_CATEDRA.md). Hasta comparar una nueva respuesta
> del servicio no se promete igualdad exacta para ese modo. Los modelos LightGBM
> tambien se incluyen ya entrenados.
>
> Resultado publico informado para esta lista: mean 100.8150, std dev 0.0000
> ($100.815.000). Fue una unica lista; ese desvio no mide estabilidad entre semillas.

### entregas/entrega_final_43/VALIDACION.json

> {
>   "inferencia": {
>     "estado": "identico_byte_por_byte",
>     "contactos": 10404,
>     "sha256": "4dcf5eff118dafa41953f66999203db6818017975d52010bad33c4881985496e",
>     "modo": "modelos_y_dataset",
>     "matriz_agosto_sha256": "6d784e36bdbfd4d257453aee6f53bf4ae617fc3e07e4e27e2f119a63ed81ff33",
>     "error_maximo_por_modelo": {
>       "541440": 0.0,
>       "408476": 0.0,
>       "741961": 0.0,
>       "248865": 0.0,
>       "717444": 0.0
>     },
>     "api": false,
>     "creditos": 0
>   },
>   "reconstruccion_rapida": {
>     "estado": "identico_byte_por_byte",
>     "contactos": 10404,
>     "sha256": "4dcf5eff118dafa41953f66999203db6818017975d52010bad33c4881985496e",
>     "modo": "probabilidades_guardadas",
>     "matriz_agosto_sha256": null,
>     "error_maximo_por_modelo": {},
>     "api": false,
>     "creditos": 0
>   },
>   "preparacion_tabpfn": {
>     "estado": "payload_original_verificado",
>     "filas_train": 327052,
>     "filas_agosto": 164647,
>     "variables": 202,
>     "target": "BAJA+2",
>     "datos_clientes_enviados": false
>   },
>   "inferencia_tabpfn_remota_ejecutada": false
> }

### entregas/entrega_final_43/procedencia.json

> {
>   "entrega": 43,
>   "archivo_original": "EnsembleVinculos197Promedio5Corte275_20261010_094750.csv",
>   "fuente_tabpfn": "Entrega 8: EnsembleAbrilMayo5_20261005_220000, reutilizada en entrega 16 y 43",
>   "tabpfn": "Probabilidades archivadas del servicio Prior Labs para 202 variables, entrenamiento abril+mayo y target BAJA+2. La corrida original usaba un servicio remoto; se congela su salida para reproduccion exacta sin credenciales.",
>   "predicciones_originales_sha256": "3efd9d9e1ab27e34ca5aad52c86124ea539148ddffb71f1a64ee3fc912efa074",
>   "modelos_sha256": {
>     "seed248865.txt": "5bf05be0c09e49e2bffee9c70cbd4abef8cc4e5a0ad6bd4f656d26378d2a33a5",
>     "seed408476.txt": "fd510ebab63108d7d2ace3af455b2fffac054c00b3bf13cef632083eb639604e",
>     "seed541440.txt": "4025ca2ca208d70ded3ca1e40f2e76540d831fad922e28982a11b1170973b31a",
>     "seed717444.txt": "87a627bbe4aa12717e9ae2d771912ba7c7035dae0b65f780f4273d4386178b1c",
>     "seed741961.txt": "5af405ec9f674485c9599b7a7e633ed822dc5d1179507a74d727c9ca51031092"
>   },
>   "codigo_historico_sha256": {
>     "features.py": "632ede2156787069296d388ebe6178851bd41f12eb6388707bc7eabd4ad02663",
>     "features_vinculos.py": "9fd182078602dc0457448c05222dc974442a0e6115358df42ea05ea52c8abeb4"
>   },
>   "resultado_publico": {
>     "fecha": "2026-10-10",
>     "entrega": 43,
>     "public_gain_mean": 100.815,
>     "public_gain_std_dev": 0.0,
>     "media_publica_pesos": 100815000,
>     "desvio_publico_pesos": 0,
>     "archivos": 1,
>     "submission_id": null,
>     "fuente": "Resultado informado explicitamente por Tomas en el chat: 43 -> mean100.8150/std0.0000",
>     "delta_vs_entrega36_pesos": 2640000,
>     "delta_vs_entrega41_pesos": 3740000,
>     "delta_vs_entrega42_pesos": 4400000,
>     "faltante_objetivo_100millones": 0,
>     "excedente_objetivo_100millones": 815000,
>     "objetivo_publico_alcanzado": true,
>     "mejor_entrega": 43,
>     "mejor_ganancia_publica_pesos": 100815000,
>     "faltante_mejor_al_objetivo": 0,
>     "escala": "Public gain ya corresponde al25%; no dividir nuevamente.",
>     "nota": "Una sola lista; desvio cero no mide estabilidad entre semillas ni en private."
>   },
>   "nota": "La 43 utiliza ocho vinculos recurrentes como variables de LightGBM. No utiliza clusters ni modelos por segmento. Seleccionada por su mayor ganancia publica observada; no constituye garantia de estabilidad o mejora privada."
> }

### entregas/entrega_final_43/TABPFN_CATEDRA.md

> # TabPFN con cuenta y key propias de la catedra
>
> La catedra crea su propia cuenta de Prior Labs y genera su token desde
> [API keys](https://platform.priorlabs.ai/account/api-keys). El SDK recibe esa
> credencial mediante `TABPFN_TOKEN`, segun la
> [documentacion oficial](https://github.com/PriorLabs/tabpfn-client#authentication).
> No es necesario recibir una key del autor de la entrega.
>
> Esta corrida requiere credito suficiente en esa cuenta. La ejecucion original
> estimaba 74.179 creditos; la cotizacion actual se consulta antes de ejecutar y
> puede cambiar. Crear una key no garantiza que la cuenta disponga de esa cuota.
>
> ## Crear la cuenta y generar la key
>
> 1. Abrir [Prior Labs Platform](https://platform.priorlabs.ai/) e iniciar sesion.
>    Si no tienen cuenta, elegir la opcion de registro y completar el flujo que
>    indique la plataforma, incluida la verificacion del correo si se solicita.
> 2. Con la sesion iniciada, abrir directamente
>    [Account / API keys](https://platform.priorlabs.ai/account/api-keys).
> 3. Elegir la opcion para crear una nueva API key. Si solicita un nombre,
>    usar uno descriptivo, por ejemplo `catedra-dmeyf-entrega43`, y confirmar
>    la creacion. Los nombres de los botones pueden variar segun la interfaz.
> 4. Copiar el token completo que devuelve la plataforma. Si se muestra solo al
>    crearlo, conservarlo en un gestor de contrasenas. No pegarlo en GitHub,
>    notebooks, archivos de configuracion ni capturas compartidas.
> 5. Revisar en la cuenta la cuota disponible. Para esta entrega, el presupuesto
>    de ejemplo es 80.000 creditos; primero consultar la cotizacion actual con el
>    comando de la seccion 2. Si la cuota no alcanza, gestionar el acceso o credito
>    necesario en Prior Labs antes de ejecutar la inferencia.
> 6. Instalar el entorno de la seccion siguiente y cargar la key en
>    `TABPFN_TOKEN` mediante el comando de entrada oculta. El script leera esa
>    variable; no hay que editar ningun archivo para agregar la credencial.
>
> Para comprobar el acceso, despues de instalar el entorno y cargar la variable:
>
> ```powershell
> .\.venv-tabpfn\Scripts\python.exe -c "from tabpfn_client import get_api_usage; print(get_api_usage())"
> ```
>
> Este comando consulta la cuota y no envia matrices de clientes ni ejecuta
> inferencia. Si devuelve un error de autenticacion, comprobar que la key sea de
> esa cuenta, este activa y se haya copiado completa, sin espacios adicionales.
> Una key revocada se reemplaza generando otra en la misma pagina.
>
> ## Entorno original de TabPFN
>
> Usar un entorno separado del de inferencia LightGBM: los dos componentes se
> ejecutaron originalmente con distintas versiones de numpy, pandas y duckdb.
> `requirements-tabpfn.txt` conserva las versiones de la corrida TabPFN original,
> incluido `tabpfn-client==0.6.1`.
>
> Desde esta carpeta, en PowerShell:
>
> ```powershell
> py -3.14 -m venv .venv-tabpfn
> .\.venv-tabpfn\Scripts\python.exe -m pip install -r requirements-tabpfn.txt
> ```
>
> Ingresar la key en la terminal con entrada oculta y guardarla solo en el entorno
> del proceso, sin escribirla en codigo ni en el repositorio:
>
> ```powershell
> $tokenCatedra = Read-Host "Key de Prior Labs" -AsSecureString
> $env:TABPFN_TOKEN = [System.Net.NetworkCredential]::new('', $tokenCatedra).Password
> ```
>
> En Linux/macOS, usar `.venv-tabpfn/bin/python` y configurar `TABPFN_TOKEN` en el
> entorno de la terminal.
>
> ## 1. Verificar los datos localmente
>
> ```powershell
> .\.venv-tabpfn\Scripts\python.exe recalcular_tabpfn.py --dataset "C:\ruta\competencia_01.csv" --salida resultado_tabpfn
> ```
>
> Reconstruye las 202 variables originales, las matrices de abril+mayo y agosto y
> el target BAJA+2. Comprueba sus tres hashes contra la corrida original. No hace
> llamadas a la API y no consume creditos.
>
> ## 2. Consultar el costo actual
>
> ```powershell
> .\.venv-tabpfn\Scripts\python.exe recalcular_tabpfn.py --dataset "C:\ruta\competencia_01.csv" --salida resultado_tabpfn --cotizar
> ```
>
> La consulta usa dimensiones de las matrices, sin enviar datos reales de clientes.
> Revisar `COTIZACION.json` y la cuota de la cuenta antes de la ejecucion.
>
> ## 3. Ejecutar TabPFN y comprobar la lista
>
> Ejemplo con limite de 80.000 creditos (elegir el presupuesto autorizado por la
> catedra):
>
> ```powershell
> .\.venv-tabpfn\Scripts\python.exe recalcular_tabpfn.py --dataset "C:\ruta\competencia_01.csv" --salida resultado_tabpfn --ejecutar-api --max-creditos 80000
> ```
>
> Este comando envia a Prior Labs las 202 variables de 327.052 filas de abril+mayo
> y su target BAJA+2, y las 202 variables de 164.647 filas de agosto para predecir.
> No envia identificadores, meses ni etiquetas de agosto. Si la cotizacion supera
> el limite, no ejecuta la inferencia. El limite es una comprobacion del script,
> no un limite configurado por key en el proveedor.
>
> Se fija `v3.5-fast`, dos estimadores, semilla 214363, `fit_preprocessors`,
> `autocast`, las categorias Visa_status/Master_status/tcuentas y
> `SUBSAMPLE_SAMPLES=None`, como en la ejecucion original. La configuracion completa
> y los hashes estan en `configuracion_tabpfn.json`.
>
> El script guarda:
>
> - `tabpfn_recalculado.csv`: respuesta nueva de TabPFN con claves locales.
> - `prediccion_final_api.csv`: ensamble con los cinco componentes LightGBM
>   originales y la nueva respuesta de TabPFN, corte estricto >2,75%.
> - `COMPARACION.json`: diferencia maxima de probabilidades, cambios de seleccion
>   y comparacion del hash de la lista final con la entrega 43.
> - `ESTADO_API.json`: registro del intento, para evitar repetir consumo por error.
>
> `csv_identico_byte_por_byte: true` confirma reproduccion exacta de la lista.
> Si es falso, el programa termina con error y conserva los resultados para
> inspeccion. Una misma version y semilla son controles de reproduccion; no se
> afirma igualdad de la nueva respuesta del servicio hasta verificarla. La corrida
> con artefactos archivados del README sigue reproduciendo la 43 exactamente.
>
> Si hubo un error despues de iniciar la API, revisar el consumo antes de reintentar.
> Una nueva corrida necesita otra carpeta de salida; no se reintenta automaticamente.
> Al finalizar, limpiar la credencial de esta terminal:
>
> ```powershell
> Remove-Item Env:TABPFN_TOKEN
> $tokenCatedra = $null
> ```
>
> El modo local de preparacion fue probado; el modo de inferencia remota de este
> script no se ejecuto durante el armado del paquete y requiere la cuenta, credito
> y autorizacion de la catedra.

