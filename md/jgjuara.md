# Juan Gabriel Juara — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: jgjuara
- Repositorio: https://github.com/jgjuara/dmeyf2026
- Link posteado: https://github.com/jgjuara/dmeyf2026/blob/main/juara/compe1/04py/ENTREGA_FINAL.md
- Commit: 1692a745450b8ec0a07b00f377e2480b9d061232
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/jgjuara/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/jgjuara.json

## Resumen

El link posteado apunta a `ENTREGA_FINAL.md`, dentro de `juara/compe1/04py/`, en un repositorio que contiene además notebooks de clase y otros intentos. La carpeta trae dos textos y siete scripts Python del experimento `04py-00`. Según `ENTREGA_FINAL.md`, el camino de la entrega es: (1) `1_bayesiana_lightgbm.py` busca con Optuna tres hiperparámetros de LightGBM (`num_iterations`, `num_leaves`, `min_sum_hessian_in_leaf`) maximizando el promedio de average precision en dos folds temporales (entrena 202103 y valida 202104; entrena 202103–202104 y valida 202105) y escribe `BO_log.txt` y `PARAM.yml`; (2) `6_prediccion_agosto_top20_semillas.py`, con `COMPE1_AGOSTO_RANKS=1` y `COMPE1_N_SEMILLAS_PRIMOS=3`, entrena con 202103–202106 tres modelos con los hiperparámetros de la primera fila de `BO_log.txt` y tres semillas distintas, predice 202108 y promedia las probabilidades; (3) un fragmento de Python incluido en el texto vuelve a promediar los 3 TSV por semilla y escribe el ranking con otro nombre, y `exportar_envio.py` corta los primeros N clientes. Las variables llegan de 8 parquets generados por scripts de `juara/fe/` (26 variables no continuas, percentiles por mes del resto, lags 1 y 2 y deltas). Los scripts `4_` y `5_` figuran en el texto como no ejecutados, `2_` como opcional y `7_` como alternativa que no fue el script de la entrega.

**Qué entrega.** CSV de una sola columna (`numero_de_cliente`, sin encabezado) con los primeros N clientes del ranking por probabilidad media de 3 modelos. Según `ENTREGA_FINAL.md` se generaron archivos con N entre 10000 y 12500 en pasos de 500, con nombre `{YYYYMMDDHHMMSS}_{n}env_rank01_exp04py-00.csv`. El repositorio no incluye esos CSV y el texto no indica cuál de los tamaños se envió.

**Cómo se ejecuta.** Según `ENTREGA_FINAL.md`, desde `juara/`: `uv sync`; colocar el dataset crudo en `juara/data/` y generar `competencia_01_clean_v1.parquet`; correr 8 scripts de variables (`uv run python fe/build_competencia_nocontinuas_v1.py`, sus lag1 y lag2, `fe/build_rankings_v1.py`, sus lag1, lag2, delta1 y delta2_v2); `uv run python compe1/04py/00/1_bayesiana_lightgbm.py`; luego, con `COMPE1_AGOSTO_RANKS=1` y `COMPE1_N_SEMILLAS_PRIMOS=3`, `uv run python compe1/04py/00/6_prediccion_agosto_top20_semillas.py`; un `uv run python -c` (sección 4 del texto) que promedia los 3 TSV por semilla y escribe `modelo_01_media_3semillas_ordenada.tsv`; y `uv run python compe1/exportar_envio.py --tsv ... --n N` para cada tamaño. Hay variantes en Bash y PowerShell y una opción `--vm` que sincroniza con un bucket de GCS indicado por `JUARA_GCS_BUCKET`.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria `clase01`: 1 si `clase_ternaria` es BAJA+1 o BAJA+2, 0 en cualquier otro caso (6_, líneas 109-114). La columna `clase_ternaria` llega en el primer parquet del join; según `juara/fe/nota.md` la calcula `fe/build_competencia_01_parquet_v1.py` a partir del CSV crudo.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202104, 202105
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica: `undersampling = 1.0` y `apply_undersampling: False` en `PARAM.yml` (1_, líneas 47 y 144-147); el 6_ entrena con todas las filas de 202103–202106.
- **Calidad de datos:** En los scripts de `04py` no se observa. En el repositorio, fuera de la carpeta posteada, `juara/fe/build_competencia_01_clean_v1.py` genera el parquet de entrada de las variables pasando `ccajas_depositos` a NULL en 202105.
- **Drifting:** Las variables que no están en la lista de 26 no continuas (`juara/docs/vars_nocontinuas.md`) entran al modelo sólo como percentil dentro de cada `foto_mes` (`PERCENT_RANK` particionado por mes y redondeado a 6 decimales, columnas `pct_*`), calculado en `juara/fe/build_rankings_v1.py`, fuera de la carpeta posteada. No se observa deflación ni otro ajuste.
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** Lag 1 y lag 2 de las 26 variables no continuas y de los percentiles `pct_*`; delta1 de los percentiles (valor menos lag 1) y delta2 (lag 1 menos lag 2). Se calculan con ventanas por `numero_de_cliente` ordenadas por `foto_mes` en scripts de `juara/fe/` (fuera de la carpeta posteada) y llegan como 6 de las 8 capas parquet que une `read_joined`.
- **Selección de variables:** No se observa selección por importancia. `campos_buenos` son todas las columnas del join de las 8 capas menos claves, clase y columnas auxiliares (`feature_columns` en `common/data.py`); el 1_ guarda la lista en `PARAM.yml` (línea 180) y el 6_ la lee de ahí (línea 69).
- **Optimización de hiperparámetros:** Optuna (`create_study` con dirección maximize, sin sampler indicado, almacenamiento SQLite `optuna.db` que permite reanudar), 150 trials por defecto (`COMPE1_BO_ITER`). Espacio: `num_iterations` entero 2000–8000, `num_leaves` entero 20–200, `min_sum_hessian_in_leaf` real 0.001–0.01. Objetivo: promedio en 2 folds temporales (202103 → 202104 y 202103–202104 → 202105) del máximo average precision de validación a lo largo de las iteraciones.
- **Hiperparámetros finales:** `num_iterations`, `num_leaves` y `min_sum_hessian_in_leaf` salen de la primera fila de `BO_log.txt` (mayor valor del objetivo); esos valores no están en el repositorio. El resto son fijos (`fixed_params_00` en `common/lgb_train.py`): `objective=binary`, `boosting=gbdt`, `learning_rate=0.005`, `feature_fraction=0.5`, `feature_fraction_bynode=0.20`, `max_bin=31`, `min_data_in_leaf=0`, `max_depth=-1`, `lambda_l1=0`, `lambda_l2=0`, `bagging_fraction=1.0`.
- **Semillas:** `SEMILLA_PRIMIGENIA = 427417` (1_, línea 32) se usa como `seed` en la BO. Para agosto, `semillas_primos(n, 427417)` toma una muestra de n primos entre 10.000 y 1.000.000 con `random.Random(427417)`; n sale de `COMPE1_N_SEMILLAS_PRIMOS` (10 por defecto). Según `ENTREGA_FINAL.md`, en la entrega n = 3 y las semillas son 114847, 178693 y 431621.
- **Cantidad de semillas:** 3
- **Ensamble:** Promedio de las probabilidades de 3 modelos LightGBM con los mismos hiperparámetros y distinta semilla (6_, líneas 126-165). El script admite varios ranks de la BO a la vez; según `ENTREGA_FINAL.md` se usó sólo el rank 1.
- **Corte:** Cantidad fija de clientes: `exportar_envio.py` toma los primeros N según la columna `orden`. Según `ENTREGA_FINAL.md` se generaron archivos con N = 10000, 10500, 11000, 11500, 12000 y 12500. No se indica cuál se envió ni cómo se eligió N.
- **Validación:** En el camino de la entrega sólo existe la de la BO: 2 folds temporales dentro de 202103–202105 (valida en 202104 y en 202105) medidos con average precision. El mes 202106 queda marcado como fold 2 (holdout) en `PARAM.yml`; los scripts que lo evalúan con ganancia figuran en `ENTREGA_FINAL.md` como no ejecutados (`4_`, `5_`) u opcional (`2_`).
- **Salidas:** En `juara/compe1/04py-00/resultados/`: `bo/optuna.db`, `bo/BO_log.txt` y `bo/PARAM.yml`; `agosto/modelo_01_<semilla>.txt` (modelo guardado), `agosto/modelo_01_<semilla>_20210801.tsv` (probabilidades por semilla), `agosto/prediccion_agosto_media.tsv`, `agosto/prediccion_agosto_media_ordenada.tsv` y `agosto/meta.yml`; además `agosto/modelo_01_media_3semillas_ordenada.tsv` y los CSV de envío. Ninguno de estos archivos está incluido en el repositorio.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Técnicas sólo exploradas

- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: `juara/pyproject.toml` pide Python >= 3.13 y lista dependencias con versión mínima (duckdb>=1.5.6, lightgbm>=4.7.0, optuna>=5.0.0, polars>=1.44.2, scikit-learn>=1.9.1, scipy>=1.18.1, pyyaml>=6.0.3, entre otras); `ENTREGA_FINAL.md` indica instalar con `uv sync`. El `.gitignore` excluye `uv.lock`. Los comandos se dan para Bash y PowerShell. Para la opción `--vm`, `juara/gce.md` muestra cómo crear una VM spot en Google Cloud (ejemplos con `e2-highmem-4` y `e2-highcpu-32`). No se declara en qué máquina se corrió la entrega.

## Pasos del camino de la entrega

1. **Preparación de datos y variables (fuera de la carpeta posteada).** `ENTREGA_FINAL.md` pide colocar el dataset crudo en `juara/data/`, instalar con `uv sync`, generar `competencia_01_clean_v1.parquet` y correr 8 scripts de `juara/fe/`. Cada script escribe una capa parquet: las 26 variables no continuas con claves y `clase_ternaria`, sus lag 1 y lag 2, los percentiles por `foto_mes` del resto de las variables (`pct_*`), sus lag 1 y lag 2, su delta1 (valor menos lag 1) y su delta2 (lag 1 menos lag 2). (`juara/compe1/04py/ENTREGA_FINAL.md` líneas 42–75; `juara/compe1/04py/README.md` líneas 9–38)
2. **Identificador del experimento y acceso a los módulos comunes.** `_bootstrap.py` agrega `juara/compe1` a `sys.path` para importar el paquete `common`, importa `common.vm_runtime` (que activa el modo VM si `--vm` está en la línea de comandos) y arma `EXPERIMENT_ID = 04py-00` con los nombres de las carpetas. Ese identificador define las 8 capas a unir y la carpeta de resultados `juara/compe1/04py-00/resultados/`. (`juara/compe1/04py/00/_bootstrap.py` líneas 1–16)
3. **Parámetros de la búsqueda de hiperparámetros.** Fija la semilla 427417 y el espacio de búsqueda (`num_iterations` 2000–8000, `num_leaves` 20–200, `min_sum_hessian_in_leaf` 0.001–0.01), 150 trials por defecto, `undersampling = 1.0`, fold 1 para desarrollo y fold 2 para holdout, y una grilla de cortes de 4000 a 19000 en pasos de 500 que se guarda en `PARAM.yml`. (`juara/compe1/04py/00/1_bayesiana_lightgbm.py` líneas 32–50)
4. **Lectura del dataset unido y partición temporal.** `preparar_holdout_temporal` une las 8 capas por `numero_de_cliente` y `foto_mes`, se queda con 202103–202106, agrega `clase01` y asigna fold 1 a 202103–202105 y fold 2 a 202106; devuelve también la lista de variables `campos_buenos`. La búsqueda usa sólo las filas del fold 1. Se cargan los hiperparámetros fijos de `fixed_params_00`. (`juara/compe1/04py/00/1_bayesiana_lightgbm.py` líneas 52–64)
5. **Estudio Optuna y función objetivo.** Crea (o retoma) un estudio Optuna guardado en `optuna.db` con dirección maximize. En cada trial propone los 3 hiperparámetros, los superpone a los fijos y calcula el promedio de average precision en dos folds temporales (entrena 202103 y valida 202104; entrena 202103–202104 y valida 202105). Lanza los trials que faltan para llegar a `COMPE1_BO_ITER`, salvo que se pida sólo exportar. (`juara/compe1/04py/00/1_bayesiana_lightgbm.py` líneas 66–106)
6. **Exportación de `BO_log.txt` y `PARAM.yml`.** Escribe `BO_log.txt` con un trial completo por fila, ordenado por el valor del objetivo de mayor a menor, y `PARAM.yml` con la semilla, los meses, la partición, los hiperparámetros fijos, los metadatos de la búsqueda, los hiperparámetros de la primera fila y la lista `campos_buenos`. (`juara/compe1/04py/00/1_bayesiana_lightgbm.py` líneas 108–187)
7. **Elección de hiperparámetros y semillas para agosto.** El 6_ lee `PARAM.yml` y, cuando no existe `top20_hiperparametros.tsv` (el caso de la entrega según el texto), toma las primeras 20 filas de `BO_log.txt` numeradas como rank 1 a 20. Los ranks a usar salen de `COMPE1_AGOSTO_RANKS` (1 en la entrega según el texto), o de `ganador.yml`, o valen 3 por defecto. Las semillas salen de `semillas_primos` con la semilla 427417 y la cantidad de `COMPE1_N_SEMILLAS_PRIMOS` (3 en la entrega; 10 por defecto). (`juara/compe1/04py/00/6_prediccion_agosto_top20_semillas.py` líneas 37–102; `juara/compe1/04py/ENTREGA_FINAL.md` líneas 90–115)
8. **Armado de entrenamiento (202103–202106) y del mes a predecir (202108).** Une las 8 capas para 202103–202106 y 202108. Las filas de 202103–202106 forman el entrenamiento, con `clase01 = 1` para BAJA+1 y BAJA+2; las de 202108 son las que se puntúan. Convierte ambos conjuntos a matrices con las columnas de `campos_buenos`. (`juara/compe1/04py/00/6_prediccion_agosto_top20_semillas.py` líneas 104–131)
9. **Entrenamiento por semilla y predicción de 202108.** Para cada rank y cada semilla entrena un LightGBM con los hiperparámetros fijos más los del rank, guarda el modelo, predice 202108, escribe un TSV de probabilidades por modelo y acumula las probabilidades. Al final verifica que la cantidad de modelos sea ranks × semillas. (`juara/compe1/04py/00/6_prediccion_agosto_top20_semillas.py` líneas 133–161)
10. **Promedio de probabilidades y ranking.** Divide la suma de probabilidades por la cantidad de modelos, escribe `prediccion_agosto_media.tsv`, ordena de mayor a menor probabilidad, agrega la columna `orden` y escribe `prediccion_agosto_media_ordenada.tsv` y `meta.yml`. (`juara/compe1/04py/00/6_prediccion_agosto_top20_semillas.py` líneas 163–191)
11. **TSV con el nombre usado en la entrega.** La sección 4 de `ENTREGA_FINAL.md` trae un fragmento de Python que lee los 3 TSV por semilla (114847, 178693, 431621), promedia `prob` por cliente y mes, y escribe `modelo_01_media_3semillas.tsv` y `modelo_01_media_3semillas_ordenada.tsv`. El texto indica que las probabilidades coinciden con las de `prediccion_agosto_media_ordenada.tsv`. (`juara/compe1/04py/ENTREGA_FINAL.md` líneas 119–161)
12. **Exportación de los CSV de envío.** `exportar_envio.py` (en `juara/compe1/`, fuera de la carpeta posteada) toma los primeros `--n` clientes por la columna `orden` y escribe un CSV de una columna `numero_de_cliente`, sin encabezado. El texto muestra el comando con `--n 11000` y un bucle para 10000, 10500, 11000, 11500, 12000 y 12500. (`juara/compe1/04py/ENTREGA_FINAL.md` líneas 163–186)

## Archivos

- `juara/compe1/04py/ENTREGA_FINAL.md` · explicacion · Markdown · 220 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jgjuara/juara/compe1/04py/ENTREGA_FINAL.md.txt) — Documento que el alumno posteó. Describe qué scripts formaron la entrega (`1_` y `6_` con rank 1 y 3 semillas, sin `4_` ni `5_`), los prerrequisitos, los comandos en orden, el fragmento que promedia las 3 semillas, la exportación de los CSV, la lista de artefactos y el protocolo completo que no se usó.
- `juara/compe1/04py/README.md` · explicacion · Markdown · 98 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jgjuara/juara/compe1/04py/README.md.txt) — Presenta el intento `04py`: las 8 capas parquet que une, los scripts de variables previos, los comandos del protocolo completo y del acortado, las variables de entorno, el modo `--vm` con GCS y una tabla de paridad con otros intentos del repositorio.
- `juara/compe1/04py/00/2_produccion_lightgbm.py` · secundario · Python · 77 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jgjuara/juara/compe1/04py/00/2_produccion_lightgbm.py.txt) — Entrena un modelo con 202103–202105 usando los hiperparámetros de mayor objetivo de `PARAM.yml` y lo evalúa en 202106 con la ganancia por corte. `ENTREGA_FINAL.md` lo presenta como opcional y aclara que no alimenta el CSV de envío.
- `juara/compe1/04py/00/6_prediccion_agosto_top20_semillas.py` · principal · Python · 195 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jgjuara/juara/compe1/04py/00/6_prediccion_agosto_top20_semillas.py.txt) — Entrena LightGBM con 202103–202106 para cada combinación de rank de la BO y semilla, predice 202108, promedia las probabilidades y escribe el ranking ordenado. Según `ENTREGA_FINAL.md`, la entrega lo corrió con rank 1 y 3 semillas.
- `juara/compe1/04py/00/5_analisis_top20_bo_semillas.py` · secundario · Python · 408 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jgjuara/juara/compe1/04py/00/5_analisis_top20_bo_semillas.py.txt) — Sin entrenar, lee los cortes de ganancia que deja el script `4_`, ordena los 20 ranks por su ganancia media máxima en 202106, escribe `ganador.yml` y compara el primer rank contra los demás con pruebas de Wilcoxon, binomial y Friedman, además de gráficos en PDF. `ENTREGA_FINAL.md` indica que no se ejecutó.
- `juara/compe1/04py/00/_bootstrap.py` · principal · Python · 16 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jgjuara/juara/compe1/04py/00/_bootstrap.py.txt) — Módulo que importan todos los scripts de la iteración: habilita la importación del paquete `common` y define `EXPERIMENT_ID` como `04py-00`.
- `juara/compe1/04py/00/7_prediccion_agosto_bo_topN_semillas.py` · secundario · Python · 157 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jgjuara/juara/compe1/04py/00/7_prediccion_agosto_bo_topN_semillas.py.txt) — Variante del script `6_` que no usa holdout: entrena con 202103–202106 las N primeras configuraciones de la BO (10 por defecto) con 10 semillas cada una, predice 202108 y promedia todas las probabilidades. `ENTREGA_FINAL.md` aclara que no fue el script de la entrega.
- `juara/compe1/04py/00/4_produccion_top20_bo_semillas.py` · secundario · Python · 214 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jgjuara/juara/compe1/04py/00/4_produccion_top20_bo_semillas.py.txt) — Para las 20 primeras configuraciones de `BO_log.txt` entrena 10 modelos con semillas distintas sobre 202103–202105 y calcula la ganancia por corte en 202106, por semilla y con la probabilidad media. `ENTREGA_FINAL.md` indica que no se ejecutó.
- `juara/compe1/04py/00/1_bayesiana_lightgbm.py` · principal · Python · 191 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/jgjuara/juara/compe1/04py/00/1_bayesiana_lightgbm.py.txt) — Búsqueda de hiperparámetros de LightGBM con Optuna sobre 202103–202105, con average precision en dos folds temporales como objetivo. Escribe `optuna.db`, `BO_log.txt` y `PARAM.yml`, que después lee el script `6_`.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### juara/compe1/04py/00/6_prediccion_agosto_top20_semillas.py

Entrena LightGBM con 202103–202106 para cada combinación de rank de la BO y semilla, predice 202108, promedia las probabilidades y escribe el ranking ordenado. Según `ENTREGA_FINAL.md`, la entrega lo corrió con rank 1 y 3 semillas.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–35] Importa `numpy`, `polars` y `yaml`, el identificador del experimento y, del
#   paquete `common`, los nombres y la escritura de modelos y predicciones de agosto, la lectura del dataset
#   unido, la sincronización con GCS, las rutas de resultados, el entrenamiento y el generador de semillas.
#!/usr/bin/env python3
"""Train mar–jun, predict agosto; media rank×semilla (04py)."""

from __future__ import annotations

import os

import numpy as np
import polars as pl
import yaml

import _bootstrap  # noqa: F401
from _bootstrap import EXPERIMENT_ID

from common.agosto_artifacts import (
    MODELO_LGB_PATRON,
    PREDICCION_TSV_PATRON,
    foto_mes_a_aniomesdia,
    persist_model_and_upload,
    persist_pred_tsv_and_upload,
)
from common.data import FOTO_MES_MAR_JUN, feature_matrix, read_joined
from common.gcs_upload import pull_resultados_subdir, sync_resultados_subdir
from pathlib import Path

from common.layers import (
    SUBDIR_AGOSTO,
    SUBDIR_BO,
    agosto_dir,
    assert_param_experiment_id,
    bo_dir,
    resultados_dir,
)
from common.lgb_train import decode_min_sum_hessian, merge_tuned, train_full
from common.partition import semillas_primos

# [Anotación · líneas 37–39] Valores por defecto: 10 semillas, rank 3 de la BO y 202108 como mes a predecir.
N_SEMILLAS_PRIMOS_DEFAULT = 10
RANKS_BO_DEFAULT = (3,)
FOTO_MES_PRED = 202108


# [Anotación · líneas 42–52] Decide qué ranks usar: si existe la variable de entorno `COMPE1_AGOSTO_RANKS`, la
#   separa por comas y la convierte a enteros; si no, lee `rank_ganador` de `ganador.yml` cuando ese archivo
#   existe; si tampoco, devuelve el rank 3.
def _ranks_desde_env_o_ganador(ganador_path: Path) -> list[int]:
    raw = os.environ.get("COMPE1_AGOSTO_RANKS", "").strip()
    if raw:
        return [int(x.strip()) for x in raw.split(",") if x.strip()]
    if ganador_path.exists():
        with ganador_path.open(encoding="utf-8") as f:
            ganador = yaml.safe_load(f) or {}
        rank_ganador = ganador.get("rank_ganador")
        if rank_ganador is not None:
            return [int(rank_ganador)]
    return list(RANKS_BO_DEFAULT)


# [Anotación · líneas 55–75] Ubica las carpetas de resultados y crea `agosto/`. En modo VM baja de GCS `bo/` y
#   `estudio/top20_bo_semillas`. Lee `bo/PARAM.yml`, comprueba que pertenezca a este experimento y toma de ahí
#   la lista de variables. Define los 4 hiperparámetros que se leen por rank: `num_iterations`, `num_leaves`,
#   `min_data_in_leaf` y `min_sum_hessian_in_leaf`.
def main() -> None:
    res_dir = resultados_dir(EXPERIMENT_ID)
    ht_dir = bo_dir(EXPERIMENT_ID)
    top20_estudio = res_dir / "estudio" / "top20_bo_semillas"
    out_dir = agosto_dir(EXPERIMENT_ID)
    out_dir.mkdir(parents=True, exist_ok=True)

    pull_resultados_subdir(EXPERIMENT_ID, SUBDIR_BO)
    pull_resultados_subdir(EXPERIMENT_ID, "estudio/top20_bo_semillas")

    with (ht_dir / "PARAM.yml").open(encoding="utf-8") as f:
        param = yaml.safe_load(f)
    assert_param_experiment_id(param, EXPERIMENT_ID)

    campos_buenos = list(param["campos_buenos"])
    hiperparams = (
        "num_iterations",
        "num_leaves",
        "min_data_in_leaf",
        "min_sum_hessian_in_leaf",
    )

# [Anotación · líneas 77–89] Carga la tabla de hiperparámetros candidatos: usa `top20_hiperparametros.tsv` si
#   existe (lo escribe el script `4_`); si no, toma las primeras 20 filas de `BO_log.txt` y las numera como rank
#   1 a 20. Termina con error si no hay ninguno de los dos archivos o si falta alguna columna.
    top20_meta = top20_estudio / "top20_hiperparametros.tsv"
    bo_log = ht_dir / "BO_log.txt"
    if top20_meta.exists():
        tb_top20 = pl.read_csv(top20_meta, separator="\t")
    elif bo_log.exists():
        tb_top20 = pl.read_csv(bo_log, separator="\t").head(20)
        tb_top20 = tb_top20.with_columns(pl.arange(1, tb_top20.height + 1).alias("rank"))
    else:
        raise FileNotFoundError(f"No existe {top20_meta} ni {bo_log}")

    faltantes = [c for c in ("rank", *hiperparams) if c not in tb_top20.columns]
    if faltantes:
        raise ValueError(f"tabla top-20 sin columnas: {faltantes}")

# [Anotación · líneas 91–102] Filtra la tabla por los ranks elegidos y termina con error si alguno no aparece.
#   Lee la cantidad de semillas de `COMPE1_N_SEMILLAS_PRIMOS` (10 por defecto) y las genera con
#   `semillas_primos`, que toma una muestra de números primos entre 10.000 y 1.000.000 usando la semilla
#   guardada en `PARAM.yml`. Imprime ranks y semillas.
    ganador_path = top20_estudio / "ganador.yml"
    ranks_usar = _ranks_desde_env_o_ganador(ganador_path)
    tb_ranks = tb_top20.filter(pl.col("rank").is_in(ranks_usar))
    if tb_ranks.height != len(ranks_usar):
        raise ValueError(f"Ranks BO fuera de rango: {ranks_usar}")

    n_semillas = int(
        os.environ.get("COMPE1_N_SEMILLAS_PRIMOS", N_SEMILLAS_PRIMOS_DEFAULT)
    )
    semillas = semillas_primos(n_semillas, int(param["semilla_primigenia"]))
    print("RANKS_BO:", ", ".join(str(r) for r in ranks_usar))
    print("semillas_train:", ", ".join(str(s) for s in semillas))

# [Anotación · líneas 104–121] Lee el dataset unido de las 8 capas para 202103, 202104, 202105, 202106 y
#   202108. Las filas de 202103–202106 forman el entrenamiento y reciben `clase01` (1 si `clase_ternaria` es
#   BAJA+1 o BAJA+2, 0 en otro caso); las de 202108 quedan para predecir. Termina con error si no hay filas de
#   202108 e imprime la cantidad de filas de cada conjunto.
    aniomesdia = foto_mes_a_aniomesdia(FOTO_MES_PRED)
    meses_leer = tuple(sorted(set(FOTO_MES_MAR_JUN) | {FOTO_MES_PRED}))
    dataset = read_joined(EXPERIMENT_ID, foto_mes=meses_leer)

    train_df = dataset.filter(pl.col("foto_mes").is_in(list(FOTO_MES_MAR_JUN)))
    train_df = train_df.with_columns(
        pl.when(pl.col("clase_ternaria").is_in(["BAJA+1", "BAJA+2"]))
        .then(1)
        .otherwise(0)
        .alias("clase01")
    )
    agosto_df = dataset.filter(pl.col("foto_mes") == FOTO_MES_PRED)
    if agosto_df.is_empty():
        raise ValueError(f"Sin filas para foto_mes={FOTO_MES_PRED}")

    n_train = train_df.height
    n_agosto = agosto_df.height
    print(f"train filas={n_train} | agosto filas={n_agosto}")

# [Anotación · líneas 123–131] Toma de `PARAM.yml` el valor de `undersampling` y los hiperparámetros fijos,
#   inicializa en cero el acumulador de probabilidades (una posición por fila de 202108) y el contador de
#   modelos, y convierte entrenamiento y agosto a matrices con las columnas de `campos_buenos`.
    undersampling = float(param["trainingstrategy"]["undersampling"])
    fixed = param["lgbm"]["param_fijos"]

    prob_sum = np.zeros(n_agosto, dtype=np.float64)
    n_modelos = 0

    X_tr = feature_matrix(train_df, campos_buenos)
    y_tr = train_df["clase01"].to_numpy()
    X_ag = feature_matrix(agosto_df, campos_buenos)

# [Anotación · líneas 133–157] Para cada rank superpone sus hiperparámetros a los fijos y pasa el resultado
#   por `decode_min_sum_hessian`, que sólo cambia `min_sum_hessian_in_leaf` (10 elevado al valor) cuando es
#   negativo. Para cada semilla divide `min_data_in_leaf` por `undersampling`, fija `seed`, entrena un LightGBM
#   con todas las filas de 202103–202106 durante `num_iterations` rondas y sin conjunto de validación, guarda el
#   modelo como `modelo_RR_<semilla>.txt`, predice 202108, suma las probabilidades al acumulador y escribe
#   `modelo_RR_<semilla>_20210801.tsv` con cliente, mes y probabilidad.
    for row in tb_ranks.iter_rows(named=True):
        rank_id = int(row["rank"])
        hp = {k: row[k] for k in hiperparams}
        param_final = decode_min_sum_hessian(merge_tuned(fixed, hp))
        print(f"\n=== rank_{rank_id:02d} ===")

        for primo in semillas:
            pnorm = dict(param_final)
            pnorm["min_data_in_leaf"] = int(
                round(float(param_final["min_data_in_leaf"]) / undersampling)
            )
            pnorm["seed"] = primo

            model = train_full(X_tr, y_tr, pnorm, seed=primo)
            persist_model_and_upload(model, out_dir, EXPERIMENT_ID, rank_id, primo)
            pred = model.predict(X_ag)
            n_modelos += 1
            prob_sum += pred

            tb_piece = agosto_df.select("numero_de_cliente", "foto_mes").with_columns(
                pl.Series("prob", pred)
            )
            persist_pred_tsv_and_upload(
                tb_piece, out_dir, EXPERIMENT_ID, rank_id, primo, aniomesdia
            )

# [Anotación · líneas 159–171] Comprueba que se hayan entrenado ranks × semillas modelos. Calcula la
#   probabilidad media dividiendo el acumulador por la cantidad de modelos y la escribe en
#   `prediccion_agosto_media.tsv`. Ordena de mayor a menor probabilidad, agrega la columna `orden` desde 1 y
#   escribe `prediccion_agosto_media_ordenada.tsv`.
    esperado = tb_ranks.height * len(semillas)
    if n_modelos != esperado:
        raise ValueError(f"Conteo de modelos inconsistente: {n_modelos} esperado={esperado}")

    tb_media = agosto_df.select("numero_de_cliente", "foto_mes").with_columns(
        (prob_sum / n_modelos).alias("prob")
    )
    tb_media.write_csv(out_dir / "prediccion_agosto_media.tsv", separator="\t")

    tb_ordenada = tb_media.sort("prob", descending=True).with_columns(
        pl.arange(1, tb_media.height + 1).alias("orden")
    )
    tb_ordenada.write_csv(out_dir / "prediccion_agosto_media_ordenada.tsv", separator="\t")

# [Anotación · líneas 173–195] Escribe `agosto/meta.yml` con el experimento, los ranks, la cantidad y la lista
#   de semillas, los meses de entrenamiento y de predicción, los patrones de nombres de archivo y las cantidades
#   de filas. Sincroniza `agosto/` con GCS (sólo en modo VM) y define el punto de entrada.
    meta = {
        "experiment_id": EXPERIMENT_ID,
        "ranks_bo": list(ranks_usar),
        "n_semillas_primos": n_semillas,
        "semillas_train": semillas,
        "foto_mes_train": list(FOTO_MES_MAR_JUN),
        "foto_mes_pred": FOTO_MES_PRED,
        "aniomesdia_pred": aniomesdia,
        "modelo_lgb_patron": MODELO_LGB_PATRON,
        "prediccion_tsv_patron": PREDICCION_TSV_PATRON,
        "n_train": n_train,
        "n_agosto": n_agosto,
        "n_predicciones_agregadas": tb_media.height,
    }
    with (out_dir / "meta.yml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)

    sync_resultados_subdir(EXPERIMENT_ID, SUBDIR_AGOSTO)
    print(f"\nFinalizado en {out_dir}")


if __name__ == "__main__":
    main()
```

### juara/compe1/04py/00/_bootstrap.py

Módulo que importan todos los scripts de la iteración: habilita la importación del paquete `common` y define `EXPERIMENT_ID` como `04py-00`.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–10] Calcula la carpeta `juara/compe1` (dos niveles arriba del archivo) y la agrega a
#   `sys.path` para poder importar el paquete `common`. Importa `common.vm_runtime`, que al cargarse activa el
#   modo VM si `--vm` figura entre los argumentos.
"""Añade juara/compe1 al sys.path; define ``EXPERIMENT_ID`` = ``{intento}-{iteración}``."""

import sys
from pathlib import Path

_COMPE1 = Path(__file__).resolve().parents[2]
if str(_COMPE1) not in sys.path:
    sys.path.insert(0, str(_COMPE1))

import common.vm_runtime  # noqa: E402, F401

# [Anotación · líneas 12–16] Toma el nombre de la carpeta padre (`04py`) como intento y el de la carpeta
#   propia (`00`) como iteración, y define `EXPERIMENT_ID` uniendo ambos con un guion: `04py-00`.
_ATTEMPT = Path(__file__).resolve().parents[1].name
_ITERATION = Path(__file__).resolve().parent.name
ATTEMPT_ID = _ATTEMPT
ITERATION = _ITERATION
EXPERIMENT_ID = f"{_ATTEMPT}-{_ITERATION}"
```

### juara/compe1/04py/00/1_bayesiana_lightgbm.py

Búsqueda de hiperparámetros de LightGBM con Optuna sobre 202103–202105, con average precision en dos folds temporales como objetivo. Escribe `optuna.db`, `BO_log.txt` y `PARAM.yml`, que después lee el script `6_`.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–30] Importa `optuna`, `polars` y `yaml`, el identificador del experimento desde
#   `_bootstrap` y, del paquete `common`, las utilidades de la búsqueda, la preparación de datos, la
#   sincronización con GCS, las rutas de resultados y el entrenamiento de LightGBM.
#!/usr/bin/env python3
"""BO Optuna + CV temporal mar–may (``experiment_id`` 04py-00, FE completo)."""

from __future__ import annotations

import os
from datetime import datetime

import optuna
import polars as pl
import yaml

import _bootstrap  # noqa: F401
from _bootstrap import EXPERIMENT_ID

from common.bo_space import (
    bo_export_at_last_complete,
    count_complete_trials,
    hyperparametertuning_meta,
    last_complete_trial_number,
    suggest_from_bo_space,
)
from common.data import FOTO_MES_MAR_JUN, FOTO_MES_MAR_MAY, preparar_holdout_temporal
from common.gcs_upload import pull_resultados_subdir, sync_every_trials, sync_resultados_subdir
from common.layers import SUBDIR_BO, bo_dir
from common.lgb_train import (
    fixed_params_00,
    merge_tuned,
    temporal_cv_average_precision_mar_may,
)

# [Anotación · líneas 32–38] Define la semilla 427417 y el espacio de búsqueda: `num_iterations` entero entre
#   2000 y 8000, `num_leaves` entero entre 20 y 200 y `min_sum_hessian_in_leaf` real entre 0.001 y 0.01.
SEMILLA_PRIMIGENIA = 427417

BO_SPACE = {
    "num_iterations": {"type": "int", "low": 2000, "high": 8000},
    "num_leaves": {"type": "int", "low": 20, "high": 200},
    "min_sum_hessian_in_leaf": {"type": "float", "low": 0.001, "high": 0.01},
}


# [Anotación · líneas 41–50] Ubica la carpeta `bo/` del experimento (en modo VM la baja antes desde GCS) y
#   fija los parámetros de la corrida: cantidad de trials desde `COMPE1_BO_ITER` (150 por defecto),
#   `undersampling = 1.0`, fold 1 para entrenamiento, fold 2 para prueba y una lista de 31 cortes de 4000 a
#   19000 en pasos de 500.
def main() -> None:
    ht_dir = bo_dir(EXPERIMENT_ID)
    pull_resultados_subdir(EXPERIMENT_ID, SUBDIR_BO, optional=True)
    ht_dir.mkdir(parents=True, exist_ok=True)

    n_iter = int(os.environ.get("COMPE1_BO_ITER", "150"))
    undersampling = 1.0
    fold_train = 1
    fold_test = 2
    cortes = list(range(4000, 19001, 500))

# [Anotación · líneas 52–64] Llama a `preparar_holdout_temporal`, que une las 8 capas parquet para
#   202103–202106, agrega `clase01` y marca 202103–202105 como fold 1 y 202106 como fold 2. Se queda con las
#   filas del fold 1 para la búsqueda, carga los hiperparámetros fijos con la semilla 427417 y guarda el
#   `min_data_in_leaf` fijo (0).
    prep = preparar_holdout_temporal(
        EXPERIMENT_ID,
        foto_mes=FOTO_MES_MAR_JUN,
        fold_train=fold_train,
        fold_test=fold_test,
    )
    df: pl.DataFrame = prep["data"]
    campos_buenos = prep["campos_buenos"]

    train_bo = df.filter(pl.col("fold") == fold_train)

    fijos = fixed_params_00(SEMILLA_PRIMIGENIA)
    mdil_fijo = int(fijos["min_data_in_leaf"])

# [Anotación · líneas 66–72] Crea el estudio Optuna `04py_00_temporal_cv_ap` con almacenamiento SQLite en
#   `bo/optuna.db`, dirección maximize y `load_if_exists=True`, de modo que una corrida posterior retoma los
#   trials ya guardados.
    storage = f"sqlite:///{ht_dir / 'optuna.db'}"
    study = optuna.create_study(
        study_name=f"{EXPERIMENT_ID.replace('-', '_')}_temporal_cv_ap",
        storage=storage,
        load_if_exists=True,
        direction="maximize",
    )

# [Anotación · líneas 74–86] Función objetivo: pide a Optuna un valor para cada hiperparámetro del espacio,
#   los superpone a los fijos y llama a `temporal_cv_average_precision_mar_may` sobre el fold 1. Esa función
#   entrena con 202103 y valida en 202104, entrena con 202103–202104 y valida en 202105, toma en cada fold el
#   máximo average precision entre las iteraciones y devuelve el promedio. Imprime una línea por trial con la
#   hora, el valor y los hiperparámetros.
    def objective(trial: optuna.Trial) -> float:
        hp = suggest_from_bo_space(trial, BO_SPACE)
        params = merge_tuned(fijos, hp)
        ap = temporal_cv_average_precision_mar_may(train_bo, campos_buenos, params)
        ts = datetime.now().strftime("%H:%M:%S")
        line = (
            f"[{ts}] trial={trial.number} | PR-AUC={ap:.6f} | "
            f"num_iterations={hp['num_iterations']} num_leaves={hp['num_leaves']} "
            f"min_sum_hessian={hp['min_sum_hessian_in_leaf']:.4g} "
            f"min_data_in_leaf={mdil_fijo}\n"
        )
        print(line, end="", flush=True)
        return ap

# [Anotación · líneas 88–93] Lee cada cuántos trials sincronizar (`COMPE1_GCS_SYNC_EVERY_TRIALS`, 1 por
#   defecto) y define un callback que sube la carpeta `bo/` a GCS con esa frecuencia; fuera del modo VM la
#   sincronización no hace nada.
    every = sync_every_trials()

    def gcs_trial_callback(study: optuna.Study, trial: optuna.trial.FrozenTrial) -> None:
        if (trial.number + 1) % every != 0:
            return
        sync_resultados_subdir(EXPERIMENT_ID, SUBDIR_BO)

# [Anotación · líneas 95–106] Si `COMPE1_BO_EXPORT_AT_LAST_COMPLETE` está activa no lanza trials nuevos. En
#   otro caso calcula cuántos faltan para llegar a la cantidad pedida, descontando los ya completos en el
#   estudio, y los ejecuta con barra de progreso y el callback de sincronización.
    export_at_last = bo_export_at_last_complete()
    if export_at_last:
        remaining = 0
    else:
        remaining = max(0, n_iter - count_complete_trials(study))
    if remaining:
        study.optimize(
            objective,
            n_trials=remaining,
            show_progress_bar=True,
            callbacks=[gcs_trial_callback],
        )

# [Anotación · líneas 108–129] Recorre los trials en estado COMPLETE y arma una fila por trial con sus
#   hiperparámetros, el `min_data_in_leaf` fijo, el valor del objetivo (`y`) y el número de iteración. Termina
#   con error si no hay ninguno. Ordena la tabla por `y` de mayor a menor y la escribe en `BO_log.txt` separada
#   por tabuladores.
    log_path = ht_dir / "BO_log.txt"
    rows = []
    for t in study.trials:
        if t.state != optuna.trial.TrialState.COMPLETE:
            continue
        row = dict(t.params)
        row.setdefault("min_data_in_leaf", mdil_fijo)
        row["y"] = t.value
        row["iter"] = t.number + 1
        rows.append(row)
    if not rows:
        raise RuntimeError("No hay trials COMPLETE en optuna.db; no se puede exportar BO.")
    n_exported = len(rows)
    if export_at_last:
        last_n = last_complete_trial_number(study)
        print(
            f"[BO] COMPE1_BO_EXPORT_AT_LAST_COMPLETE: "
            f"{n_exported} trials COMPLETE (último trial #{last_n}).",
            flush=True,
        )
    tb = pl.DataFrame(rows).sort("y", descending=True)
    tb.write_csv(log_path, separator="\t")

# [Anotación · líneas 131–137] Toma la primera fila de la tabla ordenada como la de mayor objetivo, extrae sus
#   hiperparámetros (todas las columnas menos `y` e `iter`) y cuenta las filas del fold 1 y del fold 2.
    iteraciones_report = n_exported if export_at_last else n_iter
    best = tb.row(0, named=True)
    hp_cols = [c for c in tb.columns if c not in ("y", "iter")]
    mejores = {k: best[k] for k in hp_cols}

    n_train = int(df.filter(pl.col("fold") == fold_train).height)
    n_test = int(df.filter(pl.col("fold") == fold_test).height)

# [Anotación · líneas 139–181] Arma el diccionario `param`: identificador del experimento, semilla, meses
#   202103–202106, cortes, estrategia de entrenamiento (`undersampling` 1.0 sin aplicar), descripción del
#   holdout temporal (entrena 202103–202105, prueba 202106, cantidad de filas), hiperparámetros fijos, metadatos
#   de la búsqueda (espacio, 2 folds, cantidad de iteraciones, objetivo `temporal_cv_average_precision`, ruta de
#   `optuna.db`), hiperparámetros de la primera fila con su valor y la lista de variables `campos_buenos`.
    param = {
        "experiment_id": EXPERIMENT_ID,
        "semilla_primigenia": SEMILLA_PRIMIGENIA,
        "foto_mes": list(FOTO_MES_MAR_JUN),
        "cortes": cortes,
        "trainingstrategy": {
            "undersampling": undersampling,
            "apply_undersampling": False,
        },
        "holdout": {
            "tipo": "temporal_mar_may_jun",
            "foto_mes_train": list(FOTO_MES_MAR_MAY),
            "foto_mes_test": 202106,
            "fold_train": fold_train,
            "fold_test": fold_test,
            "n_train": n_train,
            "n_test": n_test,
        },
        "lgbm": {"param_fijos": fijos},
        "hypeparametertuning": {
            **hyperparametertuning_meta(BO_SPACE),
            "xval_folds": 2,
            "iteraciones": iteraciones_report,
            "iteraciones_planificadas": n_iter,
            "export_at_last_complete": export_at_last,
            "ultimo_trial_complete": last_complete_trial_number(study),
            "objetivo": "temporal_cv_average_precision",
            "optimizer": "optuna",
            "storage": str(ht_dir / "optuna.db"),
        },
        "hyperparametertuning": {
            "xval_folds": 2,
            "iteraciones": iteraciones_report,
            "objetivo": "temporal_cv_average_precision",
        },
        "out": {
            "lgbm": {
                "mejores_hiperparametros": mejores,
                "y": float(best["y"]),
            }
        },
        "campos_buenos": campos_buenos,
    }

# [Anotación · líneas 183–191] Escribe `param` en `bo/PARAM.yml`, sincroniza la carpeta `bo/` con GCS (sólo en
#   modo VM), imprime el valor máximo del objetivo y define el punto de entrada del script.
    with (ht_dir / "PARAM.yml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(param, f, sort_keys=False, allow_unicode=True)

    sync_resultados_subdir(EXPERIMENT_ID, SUBDIR_BO)
    print(f"BO finalizada. Mejor PR-AUC={best['y']:.6f} → {ht_dir}")


if __name__ == "__main__":
    main()
```


## Explicaciones del alumno (texto original)

### juara/compe1/04py/ENTREGA_FINAL.md

> # Entrega final — experimento `04py-00`
>
> Documentación operativa para reproducir el experimento usado como **entrega final** de la competencia: BO Optuna (`04py`), **mejor trial** (rank BO **01**), [`6_prediccion_agosto_top20_semillas.py`](00/6_prediccion_agosto_top20_semillas.py) con **3 semillas** (sin `4_`/`5_`) y exportación de CSV de envíos.
>
> Referencias generales: [`README.md`](README.md), [`../README.md`](../README.md), [`../common/seleccion_envios.md`](../common/seleccion_envios.md), [`../../fe/nota.md`](../../fe/nota.md).
>
> ## Resumen
>
> | Concepto | Valor |
> |----------|--------|
> | Intento / iteración | `04py` / `00` |
> | `experiment_id` | `04py-00` ([`00/_bootstrap.py`](00/_bootstrap.py)) |
> | Features | 8 capas parquet (join en [`../common/layers.py`](../common/layers.py)) |
> | BO | Optuna, maximizar PR-AUC temporal mar–may (`SEMILLA_PRIMIGENIA=427417` en script `1_`) |
> | HP para agosto | Rank **1** de `BO_log.txt` (mejor trial; sin `top20_hiperparametros.tsv` del `4_`) |
> | Agosto | Script **`6_`**: mar–jun → `foto_mes=202108`, `COMPE1_AGOSTO_RANKS=1`, `COMPE1_N_SEMILLAS_PRIMOS=3` |
> | Scripts `4_` / `5_` | **No ejecutados** (falta de tiempo) |
> | TSV para envío | `modelo_01_media_3semillas_ordenada.tsv` (véase §4; equivalente numérico a `prediccion_agosto_media_ordenada.tsv` del `6_` con 3 semillas) |
> | Semillas | `114847`, `178693`, `431621` (`semillas_primos(3, semilla_primigenia)`) |
> | Export CSV | [`../exportar_envio.py`](../exportar_envio.py) |
>
> ### Alcance real de la entrega
>
> 1. **`1_bayesiana_lightgbm.py`** — BO y `BO_log.txt` / `PARAM.yml`.
> 2. **`6_prediccion_agosto_top20_semillas.py`** — un solo rank BO (**top 1**), **3** semillas primo; **sin** `4_` ni `5_` (no hay `ganador.yml`; el `6_` toma HP del `BO_log.txt`).
> 3. Media de `prob` sobre esas 3 corridas; ranking de envío en `modelo_01_media_3semillas_ordenada.tsv` (§4).
> 4. **`exportar_envio.py`** — varios cortes `N`.
>
> El protocolo completo (`4_` → `5_` → `6_` con 10 semillas y rank vía holdout) queda en §7 como referencia.
>
> ```mermaid
> flowchart TB
>   FE["FE: 8 parquets en juara/data"]
>   FE --> S1["1_ BO Optuna mar-may"]
>   S1 --> S6["6_ rank 1 x 3 semillas mar-jun → agosto"]
>   S6 --> TSVs["modelo_01_semilla_20210801.tsv x3"]
>   TSVs --> M3["media 3 semillas §4"]
>   M3 --> ORD["modelo_01_media_3semillas_ordenada.tsv"]
>   ORD --> CSV["exportar_envio.py"]
> ```
>
> ## 1. Prerrequisitos
>
> 1. Clonar el repositorio y colocar el dataset crudo según [`../../fe/nota.md`](../../fe/nota.md) en `juara/data/`.
> 2. Entorno Python del proyecto:
>
> ```bash
> cd juara
> uv sync
> ```
>
> 3. Generar `competencia_01_clean_v1.parquet` si no existe (cadena completa desde crudo: ver [`../README.md`](../README.md#parquets-requeridos-y-generación-fe)).
>
> 4. Tras regenerar parquets FE, verificar el join del target:
>
> ```bash
> uv run python compe1/common/verify_join_target.py
> ```
>
> ## 2. Feature engineering (04py)
>
> Requisito: `juara/data/competencia_01_clean_v1.parquet`. Desde `juara/`:
>
> ```bash
> uv run python fe/build_competencia_nocontinuas_v1.py
> uv run python fe/build_competencia_nocontinuas_v1_lag1.py
> uv run python fe/build_competencia_nocontinuas_v1_lag2.py
> uv run python fe/build_rankings_v1.py
> uv run python fe/build_rankings_v1_lag1.py
> uv run python fe/build_rankings_v1_lag2.py
> uv run python fe/build_rankings_v1_delta1.py
> uv run python fe/build_rankings_v1_delta2_v2.py
> ```
>
> Capas consumidas por `04py` (orden de join): nocontinuas + lag1/lag2; rankings + lag1/lag2 + delta1 + `rankings_v1_delta2_v2.parquet`.
>
> ## 3. Modelado — camino de la entrega
>
> Todos los comandos se ejecutan desde `juara/`. Artefactos bajo `juara/compe1/04py-00/resultados/`.
>
> ### 3.1 Bayesian optimization
>
> ```bash
> uv run python compe1/04py/00/1_bayesiana_lightgbm.py
> ```
>
> - **Salida:** `bo/optuna.db`, `bo/BO_log.txt`, `bo/PARAM.yml`.
> - **Opcional:** `COMPE1_BO_ITER`; `COMPE1_BO_EXPORT_AT_LAST_COMPLETE=1`.
>
> ### 3.2 Agosto (`6_`, rank 1 × 3 semillas)
>
> El `6_` lee hiperparámetros del **`BO_log.txt`** (primeras filas con columna `rank`) si no existe `estudio/top20_bo_semillas/top20_hiperparametros.tsv`.
>
> PowerShell:
>
> ```powershell
> cd juara
> $env:COMPE1_AGOSTO_RANKS = "1"
> $env:COMPE1_N_SEMILLAS_PRIMOS = "3"
> uv run python compe1/04py/00/6_prediccion_agosto_top20_semillas.py
> ```
>
> Bash:
>
> ```bash
> export COMPE1_AGOSTO_RANKS=1
> export COMPE1_N_SEMILLAS_PRIMOS=3
> uv run python compe1/04py/00/6_prediccion_agosto_top20_semillas.py
> ```
>
> **Salida en `agosto/`:**
>
> - `modelo_01_<semilla>_20210801.tsv` por cada semilla
> - `prediccion_agosto_media.tsv`, `prediccion_agosto_media_ordenada.tsv` (media sobre las **3** semillas)
> - `meta.yml` (`ranks_bo: [1]`, `n_semillas_primos: 3`, `semillas_train: [...]`)
>
> Opcional: `2_produccion_lightgbm.py` (holdout junio con mejor HP de `PARAM.yml`; no alimenta el CSV de envío).
>
> ## 4. Promedio de probabilidades y TSV de envío
>
> En la entrega el corte de competencia usó el nombre **`modelo_01_media_3semillas_ordenada.tsv`**. Con `COMPE1_N_SEMILLAS_PRIMOS=3`, las probabilidades coinciden con `prediccion_agosto_media_ordenada.tsv` del `6_`; §4 solo renombra/agrega el archivo esperado por el flujo de exportación documentado.
>
> Semillas (orden del `6_` con `semilla_primigenia` de `PARAM.yml`):
>
> - `114847`, `178693`, `431621`
>
> Reproducir el TSV con nombre de entrega (desde `juara/`):
>
> ```bash
> uv run python -c "
> from pathlib import Path
> import polars as pl
>
> out = Path('compe1/04py-00/resultados/agosto')
> aniomes = '20210801'
> semillas = (114847, 178693, 431621)
> rank = 1
>
> pieces = []
> for s in semillas:
>     p = out / f'modelo_{rank:02d}_{s}_{aniomes}.tsv'
>     if not p.is_file():
>         raise FileNotFoundError(p)
>     pieces.append(pl.read_csv(p, separator='\t').select('numero_de_cliente', 'foto_mes', 'prob'))
>
> tb = (
>     pl.concat(pieces, how='vertical')
>     .group_by('numero_de_cliente', 'foto_mes')
>     .agg(pl.col('prob').mean().alias('prob'))
> )
> tb.write_csv(out / 'modelo_01_media_3semillas.tsv', separator='\t')
>
> tb_ord = tb.sort('prob', descending=True).with_columns(
>     pl.arange(1, tb.height + 1).alias('orden')
> )
> tb_ord.write_csv(out / 'modelo_01_media_3semillas_ordenada.tsv', separator='\t')
> print('OK', out / 'modelo_01_media_3semillas_ordenada.tsv')
> "
> ```
>
> Alternativa: usar directamente `prediccion_agosto_media_ordenada.tsv` como `--tsv` en `exportar_envio.py`.
>
> ## 5. CSV de envíos
>
> Herramienta: [`../exportar_envio.py`](../exportar_envio.py).
>
> - **TSV de entrada:** `compe1/04py-00/resultados/agosto/modelo_01_media_3semillas_ordenada.tsv`
> - **Corte:** primeros `--n` clientes por columna `orden`
> - **Nombre del CSV:** `{YYYYMMDDHHMMSS}_{n}env_rank01_exp04py-00.csv`
> - **Formato:** una columna `numero_de_cliente`, sin encabezado, LF
>
> ```bash
> uv run python compe1/exportar_envio.py \
>   --tsv compe1/04py-00/resultados/agosto/modelo_01_media_3semillas_ordenada.tsv \
>   --n 11000
> ```
>
> Tamaños generados en la entrega (referencia): **10000–12500** (paso 500).
>
> ```powershell
> cd juara
> $tsv = "compe1/04py-00/resultados/agosto/modelo_01_media_3semillas_ordenada.tsv"
> 10000, 10500, 11000, 11500, 12000, 12500 | ForEach-Object {
>   uv run python compe1/exportar_envio.py --tsv $tsv --n $_
> }
> ```
>
> ## 6. Checklist de artefactos de entrega
>
> | Artefacto | Ubicación |
> |-----------|-----------|
> | BO | `04py-00/resultados/bo/` |
> | Predicciones por semilla | `agosto/modelo_01_114847_20210801.tsv`, `..._178693_...`, `..._431621_...` |
> | Metadatos | `agosto/meta.yml` |
> | Ranking para corte | `agosto/modelo_01_media_3semillas_ordenada.tsv` |
> | Envíos | `agosto/*_env_rank01_exp04py-00.csv` |
>
> ## 7. Pipeline completo del repo (no usado en la entrega)
>
> ```bash
> uv run python compe1/04py/00/2_produccion_lightgbm.py
> uv run python compe1/04py/00/4_produccion_top20_bo_semillas.py
> uv run python compe1/04py/00/5_analisis_top20_bo_semillas.py
> uv run python compe1/04py/00/6_prediccion_agosto_top20_semillas.py
> ```
>
> Sin `COMPE1_AGOSTO_RANKS` / `COMPE1_N_SEMILLAS_PRIMOS`, el `6_` de `04py` usa por defecto rank **3** (fallback sin `ganador.yml`) y **10** semillas.
>
> Alternativa sin holdout: [`7_prediccion_agosto_bo_topN_semillas.py`](00/7_prediccion_agosto_bo_topN_semillas.py) con `COMPE1_BO_TOP_N` (no fue el script de la entrega).
>
> ## 8. Reproducción en VM (opcional)
>
> ```bash
> export JUARA_GCS_BUCKET=juarajuangabriel_buckito2026
> export COMPE1_AGOSTO_RANKS=1
> export COMPE1_N_SEMILLAS_PRIMOS=3
> cd juara
> uv run python compe1/04py/00/1_bayesiana_lightgbm.py --vm
> uv run python compe1/04py/00/6_prediccion_agosto_top20_semillas.py --vm
> ```

### juara/compe1/04py/README.md

> # 04py
>
> **Entrega final:** BO + `6_` con rank **1** y **3 semillas** (sin `4_`/`5_`); detalle en [`ENTREGA_FINAL.md`](ENTREGA_FINAL.md).
>
> Port Python del protocolo [`00py`](../00py/README.md) con **FE completo** (8 capas parquet, equivalente a [`01_full_fe`](../archivo/01_full_fe/README.md) y [`01py`](../01py/README.md)): split temporal mar–may / test junio, BO con **Optuna** maximizando PR-AUC temporal. Sin script `3_escalar`.
>
> Convención intento–iteración: ver [`README.md`](../README.md#intentos-python-py). En la iteración `00`, **`experiment_id` = `04py-00`** (definido en [`00/_bootstrap.py`](00/_bootstrap.py)).
>
> **Capas parquet** (orden de join; ver capas del intento `04py` en [`common/layers.py`](../common/layers.py)):
>
> - `competencia_01_nocontinuas_v1.parquet`
> - `competencia_01_nocontinuas_v1_lag1.parquet`
> - `competencia_01_nocontinuas_v1_lag2.parquet`
> - `rankings_v1.parquet`
> - `rankings_v1_lag1.parquet`
> - `rankings_v1_lag2.parquet`
> - `rankings_v1_delta1.parquet`
> - `rankings_v1_delta2_v2.parquet`
>
> **Resultados:** `juara/compe1/04py-00/resultados/` (`bo/`, `produccion/`, `top20/`, `agosto/`, `estudio/top20_bo_semillas/`).
>
> **Utilidades:** [`common/layers.py`](../common/layers.py), [`common/data.py`](../common/data.py), [`common/lgb_train.py`](../common/lgb_train.py), [`common/bo_space.py`](../common/bo_space.py), [`common/gcs_upload.py`](../common/gcs_upload.py).
>
> ## Prerequisitos FE
>
> Desde `juara/`, con `competencia_01_clean_v1.parquet` en `juara/data/` (ver [`fe/nota.md`](../../fe/nota.md)):
>
> ```bash
> cd juara
> uv run python fe/build_competencia_nocontinuas_v1.py
> uv run python fe/build_competencia_nocontinuas_v1_lag1.py
> uv run python fe/build_competencia_nocontinuas_v1_lag2.py
> uv run python fe/build_rankings_v1.py
> uv run python fe/build_rankings_v1_lag1.py
> uv run python fe/build_rankings_v1_lag2.py
> uv run python fe/build_rankings_v1_delta1.py
> uv run python fe/build_rankings_v1_delta2_v2.py
> ```
>
> ## Comandos pipeline
>
> **Entrega (acortada):** ver [`ENTREGA_FINAL.md`](ENTREGA_FINAL.md) — `1_` BO, luego `6_` con `COMPE1_AGOSTO_RANKS=1` y `COMPE1_N_SEMILLAS_PRIMOS=3`.
>
> **Protocolo completo (holdout top-20 + `ganador.yml` + `6_`):**
>
> ```bash
> cd juara
> uv run python compe1/04py/00/1_bayesiana_lightgbm.py
> uv run python compe1/04py/00/2_produccion_lightgbm.py
> uv run python compe1/04py/00/4_produccion_top20_bo_semillas.py
> uv run python compe1/04py/00/5_analisis_top20_bo_semillas.py
> uv run python compe1/04py/00/6_prediccion_agosto_top20_semillas.py
> ```
>
> **Sin holdout top-20** (top-N BO directo a agosto, 10 semillas):
>
> ```bash
> COMPE1_BO_TOP_N=1 uv run python compe1/04py/00/7_prediccion_agosto_bo_topN_semillas.py
> ```
>
> Variables útiles:
>
> - `COMPE1_BO_ITER` — iteraciones Optuna (default `150`).
> - `COMPE1_BO_EXPORT_AT_LAST_COMPLETE=1` — no corre trials nuevos; exporta `BO_log.txt` y `PARAM.yml` con **todos** los trials COMPLETE presentes en `optuna.db` al ejecutar (corte en el último completado, sin fijar un número a mano).
>
> ## VM spot y GCS (`--vm`)
>
> Con `--vm`, los scripts bajan parquets desde `gs://<bucket>/data/` y sincronizan resultados con `gs://<bucket>/compe1/04py-00/resultados/`. Sin `--vm`, solo disco local (las variables de bucket no activan GCS por sí solas).
>
> ```bash
> export JUARA_GCS_BUCKET=juarajuangabriel_buckito2026
> cd juara
> uv run python compe1/04py/00/1_bayesiana_lightgbm.py --vm
> ```
>
> | Variable | Default | Uso |
> |----------|---------|-----|
> | `JUARA_GCS_BUCKET` / `COMPE1_GCS_BUCKET` | — | Bucket (obligatorio con `--vm`) |
> | `JUARA_GCS_PREFIX` | `data` | Parquets de entrada |
> | `COMPE1_GCS_PREFIX` | `compe1/04py-00/resultados` | Salidas del experimento |
> | `COMPE1_GCS_SYNC_EVERY_TRIALS` | `1` | Script 1: rsync de `bo/` cada N trials Optuna |
>
> Subidas incrementales: script 1 (cada trial según `COMPE1_GCS_SYNC_EVERY_TRIALS`), script 4 (cada `rank_##` y metadatos de estudio). Al terminar cada script se vuelve a sincronizar el directorio correspondiente.
>
> Requisitos en la VM: `gcloud` en PATH; scope de almacenamiento con escritura e IAM de escritura sobre el bucket (ver [`juara/gce.md`](../../gce.md)).
>
> ## Paridad
>
> | Componente | Paridad |
> |------------|---------|
> | Split temporal vs R | Mismo criterio por `foto_mes` (protocolo `*py`) |
> | Objetivo BO | `temporal_cv_average_precision_mar_may` (PR-AUC; 2 folds mar→abr, mar–abr→may) |
> | Features | 8 capas (mismo join que `01py` / `01_full_fe`) |
> | BO | No bit-a-bit (Optuna ≠ mlrMBO) |
> | `3_escalar` | No incluido |
> | Agosto (`6_`) | Usa `rank_ganador` de `ganador.yml` (paso `5_`); fallback rank `3` |
>
> Checkpoint BO: `04py-00/resultados/bo/optuna.db`.

