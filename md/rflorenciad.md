# Florencia Rodriguez — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: rflorenciad
- Repositorio: https://github.com/rflorenciad/dmeyf2026
- Link posteado: https://github.com/rflorenciad/dmeyf2026/blob/main/primera_competencia/README.md
- Commit: 9945c4187da6abdb754aba1f607896cfd5ae1389
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/rflorenciad/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/rflorenciad.json

## Resumen

La entrega es la carpeta primera_competencia/ de un repositorio en Python: un README, tres scripts (reproducir.py, entrenar.py y 01_optimizacion/optimizar.py), un módulo de datos (src/datos.py), archivos JSON de configuración y verificación, doce modelos LightGBM guardados, el estudio Optuna en SQLite y el CSV final. El camino de la predicción: src/datos.py lee el CSV de la competencia (202103–202108) con DuckDB, pasa ccajas_depositos de 202105 a NA, agrega lag 1, lag 2 y sus deltas a 152 variables (762 columnas en total) y reemplaza 365 columnas monetarias por un rank por mes separado por signo. La clase de entrenamiento es binaria, con BAJA+1 y BAJA+2 como positivos. Una búsqueda Optuna (TPE, 12 trials completos) sobre num_leaves, min_sum_hessian_in_leaf y tope de árboles, evaluada por AUC en dos folds temporales (202103→202105 y 202103–202104→202106), da doce configuraciones. entrenar.py entrena las doce en 202103–202106, cada una con su semilla y su cantidad de árboles. reproducir.py predice 202108 con los doce modelos, promedia las probabilidades con igual peso, ordena y escribe los 12.000 clientes de mayor promedio. Cada etapa compara hashes SHA-256 de matrices, modelos y CSV contra los valores guardados en configuracion.json.

**Qué entrega.** Un CSV sin encabezado, con una columna de 12.000 numero_de_cliente de 202108 (03_prediccion_final/FlorFinalV88_completo12_k12000.csv): los de mayor probabilidad promedio de doce modelos LightGBM. Según el README, se envió con el mensaje FlorFinalV88Completo12k12000 y tuvo una ganancia pública de 104,8575 M.

**Cómo se ejecuta.** Según el README: crear un entorno virtual con Python 3.11 e instalar requirements.txt; luego `python reproducir.py --dataset "/ruta/competencia_01.csv" --salida salida`, que reconstruye las variables, carga los doce modelos guardados y genera y verifica el CSV. Pasos opcionales que el README describe: `python entrenar.py --datos salida/datos --salida reentrenamiento` para entrenar de nuevo los doce modelos y `python reproducir.py --dataset ... --modelos reentrenamiento --salida salida_reentrenada` para generar el CSV con ellos; `python 01_optimizacion/optimizar.py verificar`, `repetir` o `nueva` para comprobar el origen de los hiperparámetros, reevaluar las doce configuraciones o correr una búsqueda nueva.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: positivo = BAJA+1 o BAJA+2 (etiquetas 1 y 2), negativo = CONTINUA (etiqueta 0). Las etiquetas salen de clase_ternaria si el CSV la trae; si no, se reconstruyen para 202103–202106 según la presencia del cliente en los dos meses siguientes.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202105, 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código submuestreo de CONTINUA: el entrenamiento usa todas las filas de 202103–202106. LightGBM corre con bagging_fraction 0,7 y bagging_freq 1 (70% de las filas en cada iteración).
- **Calidad de datos:** ccajas_depositos se pasa a NA en 202105 antes de calcular sus lags y deltas. El código corta con error si hay pares cliente/mes duplicados, si los meses no son 202103–202108, si falta alguna de las 154 columnas o si la matriz tiene valores infinitos. Los NA se conservan.
- **Drifting:** 365 columnas (73 variables monetarias y sus lag1, lag2, delta1 y delta2) se reemplazan por un rank percentil calculado dentro de cada mes y separado por signo: positivos en (0, 1], negativos en [−1, 0), el cero queda en 0 y los NA quedan NA; los empates toman el rango medio.
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** Lag 1, lag 2, delta 1 y delta 2 de las 152 variables originales (todas menos numero_de_cliente y foto_mes): 608 columnas que, con las 154 originales, suman 762. Los lags buscan al cliente en el mes calendario anterior y en el de dos meses atrás; para ccajas_depositos se usan las observaciones previas del cliente. 202107 se usa sólo para la historia de 202108.
- **Selección de variables:** No se observa en el código. Las 762 columnas y su orden están listados en configuracion.json.
- **Optimización de hiperparámetros:** Optuna con sampler TPE (semilla 882026, 4 trials iniciales); el estudio guardado tiene 12 trials completos y uno fallido. Espacio: tope de árboles {2000, 4000, 8000}, num_leaves {8, 16, 24, 32, 48, 64} y min_sum_hessian_in_leaf entre 1 y 100 en escala logarítmica. Objetivo a maximizar: promedio del AUC (positivo = BAJA+1 o BAJA+2) en dos folds temporales, con early stopping de 150 iteraciones. La cantidad de árboles de cada configuración es el promedio redondeado de las iteraciones elegidas en los dos folds.
- **Hiperparámetros finales:** Comunes a los doce modelos (configuracion.json): objective binary, learning_rate 0,005, max_bin 31, min_data_in_leaf 0, feature_fraction 0,5, feature_fraction_bynode 0,2, bagging_fraction 0,7, bagging_freq 1, deterministic y force_col_wise en true, feature_pre_filter en false. Por modelo, índices 0 a 11 (configuraciones.json): num_leaves 8, 32, 8, 32, 24, 24, 24, 48, 64, 48, 16, 64; min_sum_hessian_in_leaf 2,74; 53,43; 2,74; 53,43; 1,81; 1,10; 58,48; 5,99; 6,86; 10,76; 26,90; 8,82; num_iterations 3686, 2725, 3880, 2815, 2000, 2000, 1990, 1815, 1665, 1835, 2840, 1785.
- **Semillas:** Una semilla por modelo, escrita en configuraciones.json y configuracion.json y derivada como 882026 + 1009 × número de trial: 882026, 884044, 885053, 886062, 887071, 888080, 889089, 890098, 891107, 892116, 893125, 894134. El sampler TPE usa la semilla 882026.
- **Cantidad de semillas:** 12
- **Ensamble:** Promedio con igual peso de las probabilidades de doce modelos LightGBM, uno por cada configuración completa de la búsqueda Optuna, cada uno con su semilla, sus hojas, su mínimo de Hessian y su cantidad de árboles.
- **Corte:** Cantidad fija: los 12.000 clientes de mayor probabilidad promedio, con desempate por numero_de_cliente ascendente. Según el README, el valor 12.000 se fijó tras comparar nueve cortes entre 9.500 y 13.500 en el tablero público; ese proceso no está en el código.
- **Validación:** Dos folds temporales dentro de la búsqueda de hiperparámetros: entrenar en 202103 y validar en 202105; entrenar en 202103–202104 y validar en 202106. En cada fold se registran el AUC con ambas bajas (el que se optimiza), el AUC de BAJA+2 y la ganancia con 10.500 envíos. El entrenamiento final no usa conjunto de validación.
- **Salidas:** reproducir.py escribe salida/predicciones_finales/FlorFinalV88_completo12_k12000.csv (12.000 IDs, una columna, sin encabezado), salida/VERIFICACION.json y, en salida/datos/, los archivos x_, ids_ e y_ de cada mes en .npy más VERIFICACION_DATOS.json. entrenar.py escribe modelo_XX.txt y VERIFICACION_ENTRENAMIENTO.json. optimizar.py escribe los modelos de cada fold, reevaluacion.json o un estudio.sqlite nuevo.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optuna (`hiperparametros.optuna`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: entorno.json registra Python 3.11.8, sistema Darwin, arquitectura arm64 y las versiones numpy 2.4.6, pandas 3.0.5, lightgbm 4.7.0, scikit-learn 1.9.0, scipy 1.17.1, optuna 5.0.0 y duckdb 1.5.5, las mismas que fija requirements.txt. El README indica Python 3.11, 16 GB de RAM como mínimo y 8 GB libres en disco, y que LightGBM necesita OpenMP (libomp en macOS, libgomp en Linux). El dataset no está en el repositorio.

## Pasos del camino de la entrega

1. **Lectura y controles del dataset.** Lee el CSV con DuckDB (3 hilos, límite de 8 GB), toma las 154 columnas listadas en raw_features ordenadas por cliente y mes, y corta con error si falta alguna columna, si hay pares cliente/mes duplicados o si los meses no son 202103–202108. Arma por mes el vector de IDs y una tabla indexada por cliente, y lee clase_ternaria si está. (`primera_competencia/src/datos.py` líneas 32–56; `primera_competencia/configuracion.json` líneas 783–938)
2. **ccajas_depositos de 202105 a NA.** Pasa ccajas_depositos a NA en 202105 y calcula para esa variable lag 1, lag 2 y sus deltas con un desplazamiento dentro de las filas de cada cliente (observaciones previas del cliente, no mes calendario). (`primera_competencia/src/datos.py` líneas 57–62)
3. **Lags y deltas por mes calendario.** Para cada mes y cada una de las 152 variables distintas de numero_de_cliente y foto_mes, busca el valor del mismo cliente en el mes anterior y en el de dos meses atrás (NA si el cliente no está o el mes no existe en los datos) y calcula la diferencia con cada uno. Después pisa las cinco columnas de ccajas_depositos con las del paso anterior. (`primera_competencia/src/datos.py` líneas 63–78)
4. **Matriz de 762 columnas y rank por mes.** Arma la matriz del mes en float32 con las 762 columnas en el orden de configuracion.json y reemplaza 365 de ellas (73 montos y sus lags y deltas) por un rank percentil dentro del mes: positivos en (0, 1], negativos en [−1, 0), cero en 0 y NA en NA. (`primera_competencia/src/datos.py` líneas 19–29; `primera_competencia/src/datos.py` líneas 79–84; `primera_competencia/configuracion.json` líneas 939–1305)
5. **Etiquetas por mes.** Para 202103–202106 codifica CONTINUA = 0, BAJA+1 = 1 y BAJA+2 = 2 a partir de clase_ternaria; si el CSV no la trae, asigna 0 al cliente que aparece dos meses después, 2 al que aparece el mes siguiente pero no dos meses después, y 1 al que no aparece en ninguno. 202107 y 202108 quedan con 255 (sin etiqueta). (`primera_competencia/src/datos.py` líneas 85–95)
6. **Guardado y verificación de las matrices.** Guarda por mes x_, ids_ e y_ en .npy, calcula el SHA-256 de cada archivo y lo compara con el valor de configuracion.json; si no coincide corta con error. Al final escribe VERIFICACION_DATOS.json. (`primera_competencia/src/datos.py` líneas 96–111; `primera_competencia/configuracion.json` líneas 1435–1458)
7. **Folds temporales para la búsqueda.** Arma dos folds: entrenamiento en 202103 con validación en 202105, y entrenamiento en 202103 y 202104 con validación en 202106. La clase es binaria con las etiquetas 1 y 2 como positivos, y los datasets se construyen con max_bin 31. (`primera_competencia/01_optimizacion/optimizar.py` líneas 86–92; `primera_competencia/entrenar.py` líneas 12–21)
8. **Búsqueda de hiperparámetros con Optuna.** Crea un estudio con TPESampler (semilla 882026, 4 trials iniciales) que maximiza el promedio del AUC de los dos folds. Cada trial propone tope de árboles {2000, 4000, 8000}, num_leaves {8, 16, 24, 32, 48, 64} y min_sum_hessian_in_leaf entre 1 y 100 (escala logarítmica), con semilla 882026 + 1009 × número de trial; el resto de los parámetros sale de fixed_params. (`primera_competencia/01_optimizacion/optimizar.py` líneas 103–117; `primera_competencia/configuracion.json` líneas 1321–1336)
9. **Evaluación de cada configuración en los folds.** Entrena en cada fold con early stopping de 150 iteraciones sobre el AUC de validación (nativo, o recalculado cada 10 iteraciones), predice el mes de validación y registra la iteración elegida, el AUC con ambas bajas, el AUC de BAJA+2 y la ganancia de los 10.500 clientes de mayor probabilidad, calculada como 1.100.000 por cada BAJA+2 menos 27.500 por cada envío. (`primera_competencia/01_optimizacion/optimizar.py` líneas 39–64)
10. **Doce configuraciones con su cantidad de árboles.** configuraciones.json guarda, para los doce trials completos, semilla, num_leaves, min_sum_hessian_in_leaf, métricas por fold y num_iterations. La función verificar comprueba que coincidan con el estudio guardado y que num_iterations sea el promedio redondeado de las iteraciones elegidas en los dos folds. (`primera_competencia/01_optimizacion/optimizar.py` líneas 18–36; `primera_competencia/01_optimizacion/configuraciones.json` líneas 1–30)
11. **Entrenamiento de los doce modelos finales.** Concatena las matrices de 202103, 202104, 202105 y 202106 en un único dataset con clase binaria (BAJA+1 o BAJA+2 = 1) y entrena un LightGBM por configuración, con los parámetros comunes más num_leaves, min_sum_hessian_in_leaf, semilla y cantidad fija de árboles de esa configuración, sin conjunto de validación. Guarda cada modelo como texto. (`primera_competencia/entrenar.py` líneas 12–21; `primera_competencia/entrenar.py` líneas 37–54; `primera_competencia/configuracion.json` líneas 1314–1319)
12. **Control del reentrenamiento contra la referencia.** Predice 202108 con cada modelo recién entrenado, mide la máxima diferencia absoluta contra las probabilidades guardadas en predicciones_referencia.npz, la anota en VERIFICACION_ENTRENAMIENTO.json y corta con error si supera 1e-12. (`primera_competencia/entrenar.py` líneas 55–66)
13. **Predicción de 202108 con los doce modelos.** Carga la matriz y los IDs de 202108 y, para cada modelo (los .txt.gz de 02_modelos/ o los de la carpeta indicada en --modelos), comprueba el hash del archivo y los nombres de las 762 variables, predice y compara las probabilidades con la referencia con tolerancia 1e-12. (`primera_competencia/reproducir.py` líneas 28–51; `primera_competencia/configuracion.json` líneas 1337–1434)
14. **Promedio, orden y corte en 12.000.** Promedia con igual peso las probabilidades de los doce modelos, ordena por promedio descendente y por numero_de_cliente ascendente ante empates, toma los primeros 12.000 y escribe un ID por línea, sin encabezado. (`primera_competencia/reproducir.py` líneas 52–63; `primera_competencia/configuracion.json` líneas 1459–1480)
15. **Comparación del CSV con el archivo de referencia.** Compara el CSV generado byte por byte y por SHA-256 con 03_prediccion_final/FlorFinalV88_completo12_k12000.csv; si difiere corta con error. Escribe VERIFICACION.json con el estado, los hashes, el error máximo por modelo y los segundos de la corrida. (`primera_competencia/reproducir.py` líneas 64–75)

## Archivos

- `primera_competencia/reproducir.py` · principal · Python · 79 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rflorenciad/primera_competencia/reproducir.py.txt) — Script que genera el CSV entregado: prepara o verifica las matrices, predice 202108 con los doce modelos, promedia, ordena, corta en 12.000 y compara el resultado con el archivo de referencia.
- `primera_competencia/requirements.txt` · configuracion · Texto · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rflorenciad/primera_competencia/requirements.txt.txt) — Dependencias con versión fija: numpy 2.4.6, pandas 3.0.5, lightgbm 4.7.0, scikit-learn 1.9.0, scipy 1.17.1, optuna 5.0.0 y duckdb 1.5.5.
- `primera_competencia/README.md` · explicacion · Markdown · 146 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rflorenciad/primera_competencia/README.md.txt) — Texto de presentación de la entrega. Declara el archivo final, su mensaje de envío y su ganancia pública, y explica instalación, reproducción del CSV, variables y modelo, origen de los hiperparámetros, reentrenamiento, construcción del ensamble y elección del corte de 12.000.
- `primera_competencia/entorno.json` · configuracion · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rflorenciad/primera_competencia/entorno.json.txt) — Registro del entorno de la corrida verificada: Python 3.11.8, sistema Darwin, arquitectura arm64 y las versiones de los siete paquetes de requirements.txt.
- `primera_competencia/SHA256SUMS.json` · configuracion · JSON · 29 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rflorenciad/primera_competencia/SHA256SUMS.json.txt) — Hashes SHA-256 de 27 archivos de la carpeta: scripts, JSON, README, los doce modelos comprimidos, el estudio SQLite, el CSV final y las probabilidades de referencia.
- `primera_competencia/VERIFICACION.json` · configuracion · JSON · 136 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rflorenciad/primera_competencia/VERIFICACION.json.txt) — Informe de una corrida de verificación guardado en el repositorio: estado 'identico_byte_por_byte', error máximo 0,0 en los doce modelos, 248,63 segundos, hashes de las matrices de los seis meses, el reentrenamiento del componente 8 (641,87 segundos, error 0,0) y los datos del envío final.
- `primera_competencia/configuracion.json` · configuracion · JSON · 1498 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rflorenciad/primera_competencia/configuracion.json.txt) — Configuración que leen los scripts: versión V88, corte de 12.000, listas de 762 variables, 154 columnas originales y 365 columnas a rankear, meses, parámetros comunes de LightGBM, los doce modelos con semilla, hilos y hashes, hashes esperados de matrices, IDs y etiquetas, definición del ensamble y datos de los envíos.
- `primera_competencia/entrenar.py` · principal · Python · 70 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rflorenciad/primera_competencia/entrenar.py.txt) — Script que entrena los doce modelos LightGBM del ensamble con las matrices de 202103–202106 y las configuraciones de 01_optimizacion/configuraciones.json, y compara sus predicciones de 202108 con las de referencia.
- `primera_competencia/01_optimizacion/optimizar.py` · principal · Python · 121 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rflorenciad/primera_competencia/01_optimizacion/optimizar.py.txt) — Script de la búsqueda de hiperparámetros con Optuna, con tres modos: verificar (compara configuraciones.json con el estudio guardado en estudio.sqlite), repetir (reevalúa las doce configuraciones en los dos folds) y nueva (corre una búsqueda con el mismo espacio y objetivo). Según el README, no hace falta para reproducir el CSV final.
- `primera_competencia/01_optimizacion/configuraciones.json` · configuracion · JSON · 350 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rflorenciad/primera_competencia/01_optimizacion/configuraciones.json.txt) — Lista de las doce configuraciones que salen del estudio Optuna (trials 0 y 2 a 12). Cada entrada tiene índice, número de trial, semilla, num_iterations, num_leaves, min_sum_hessian_in_leaf, el AUC promedio y, por fold (202105 y 202106), iteración elegida, tope de árboles, si se alcanzó el tope, AUC con ambas bajas, AUC de BAJA+2 y ganancia en millones.
- `primera_competencia/src/datos.py` · principal · Python · 111 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rflorenciad/primera_competencia/src/datos.py.txt) — Módulo que construye, a partir del CSV de la competencia, las matrices mensuales de 762 variables (originales, lags, deltas y ranks por mes), los IDs y las etiquetas, y verifica sus hashes. Lo usan reproducir.py, entrenar.py y optimizar.py.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### primera_competencia/reproducir.py

Script que genera el CSV entregado: prepara o verifica las matrices, predice 202108 con los doce modelos, promedia, ordena, corta en 12.000 y compara el resultado con el archivo de referencia.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–9] Importa argparse, gzip, json, time, lightgbm y numpy, y trae de src/datos.py la
#   carpeta raíz (ROOT), la configuración (CONFIG) y las funciones preparar y sha256.
"""Genera y verifica el CSV final desde el dataset de la competencia."""
import argparse
import gzip
import json
import time
from pathlib import Path
import lightgbm as lgb
import numpy as np
from src.datos import ROOT, CONFIG, preparar, sha256


# [Anotación · líneas 12–19] Define los argumentos: --dataset (CSV de la competencia) o --datos (matrices ya
#   construidas), uno de los dos obligatorio; --salida, con valor por defecto 'salida'; y --modelos, una carpeta
#   alternativa con modelos reentrenados.
def main():
    p = argparse.ArgumentParser(description=__doc__)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument('--dataset', type=Path)
    source.add_argument('--datos', type=Path, help='Matrices previamente reconstruidas y verificadas.')
    p.add_argument('--salida', type=Path, default=Path('salida'))
    p.add_argument('--modelos', type=Path, help='Carpeta alternativa de modelos reentrenados.')
    args = p.parse_args()
# [Anotación · líneas 20–27] Inicia el cronómetro y crea la carpeta de salida. Con --dataset llama a preparar
#   para construir las matrices en salida/datos; con --datos comprueba el SHA-256 de x, ids e y de los seis
#   meses contra configuracion.json.
    start = time.monotonic()
    output = args.salida.resolve()
    output.mkdir(parents=True, exist_ok=True)
    data = preparar(args.dataset, output / 'datos') if args.dataset else args.datos.resolve()
    if args.datos:
        for month in CONFIG['months']:
            for prefix, key in [('x', 'matrix_sha256'), ('ids', 'ids_sha256'), ('y', 'labels_sha256')]:
                assert sha256(data / f'{prefix}_{month}.npy') == CONFIG[key][str(month)]
# [Anotación · líneas 28–31] Carga la matriz de 202108 mapeada en memoria, los IDs de 202108 y el archivo
#   predicciones_referencia.npz, y exige que los IDs coincidan con los de la referencia.
    x = np.load(data / 'x_202108.npy', mmap_mode='r')
    ids = np.load(data / 'ids_202108.npy')
    reference = np.load(ROOT / '03_prediccion_final/predicciones_referencia.npz')
    assert np.array_equal(ids, reference['ids'])
# [Anotación · líneas 32–51] Para cada uno de los doce modelos de CONFIG['models']: lo carga desde --modelos
#   (modelo_XX.txt) o desde 02_modelos/ (descomprimiendo el .gz después de comprobar su SHA-256), exige que sus
#   variables sean las 762 de la configuración, predice 202108 con la cantidad de hilos indicada para ese
#   modelo, exige valores finitos y calcula la máxima diferencia absoluta contra las probabilidades de
#   referencia; si supera 1e-12 corta con error.
    scores = []
    checks = []
    for j, entry in enumerate(CONFIG['models']):
        if args.modelos:
            path = args.modelos / f'modelo_{entry["index"]:02d}.txt'
            b = lgb.Booster(model_file=str(path))
        else:
            path = ROOT / entry['file']
            assert sha256(path) == entry['sha256_compressed']
            with gzip.open(path, 'rt') as f:
                b = lgb.Booster(model_str=f.read())
        assert b.feature_name() == CONFIG['features']
        pred = b.predict(x, num_threads=entry['threads'])
        assert np.isfinite(pred).all()
        error = float(np.max(np.abs(pred - reference['probabilities'][j])))
        if error > 1e-12:
            raise ValueError(f'Predicciones distintas para modelo {entry["index"]}: {error}')
        scores.append(pred)
        checks.append({'index': entry['index'], 'max_abs_error': error, 'file_sha256': sha256(path)})
        print(f'Modelo {entry["index"]:02d}: predicciones verificadas.', flush=True)
# [Anotación · líneas 52–56] Apila las predicciones en una matriz de doce filas, arma el diccionario de índice
#   de modelo a posición y crea la carpeta predicciones_finales.
    scores = np.stack(scores)
    positions = {entry['index']: j for j, entry in enumerate(CONFIG['models'])}
    destinations = output / 'predicciones_finales'
    destinations.mkdir(exist_ok=True)
    files = []
# [Anotación · líneas 57–69] Para el único ensamble de la configuración (índices 0 a 11): promedia las
#   probabilidades de esos modelos, ordena por promedio descendente y por ID ascendente ante empate, toma los
#   primeros 12.000 (CONFIG['cutoff']), comprueba que no haya IDs repetidos y escribe un ID por línea. Compara
#   el archivo con el de 03_prediccion_final byte por byte y por SHA-256, y corta con error si difiere.
    for entry in CONFIG['ensembles']:
        mean = scores[[positions[i] for i in entry['model_indices']]].mean(axis=0)
        selected = ids[np.lexsort((ids, -mean))[:CONFIG['cutoff']]]
        assert len(selected) == len(np.unique(selected)) == CONFIG['cutoff']
        expected = ROOT / entry['file']
        destination = destinations / expected.name
        destination.write_bytes(''.join(f'{int(client)}\n' for client in selected).encode('ascii'))
        digest = sha256(destination)
        if destination.read_bytes() != expected.read_bytes() or digest != entry['sha256']:
            raise ValueError(f'El ensamble {entry["ensemble"]} no coincide con la referencia.')
        files.append({'ensemble': entry['ensemble'], 'file': destination.name,
                      'rows': len(selected), 'sha256': digest, 'expected_sha256': entry['sha256']})
        print(f'Ensamble {entry["ensemble"]:02d}: CSV idéntico byte por byte.', flush=True)
# [Anotación · líneas 70–75] Exige que se haya generado un solo archivo y escribe VERIFICACION.json con el
#   estado, la cantidad de filas, los hashes, el error máximo de cada modelo y los segundos transcurridos.
    assert len(files) == 1
    report = {'status': 'identico_byte_por_byte', 'candidate_models': len(files),
              'rows_per_file': CONFIG['cutoff'], 'files': files, 'models': checks,
              'seconds': round(time.monotonic() - start, 2)}
    (output / 'VERIFICACION.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'OK: CSV final verificado en {destinations}', flush=True)


# [Anotación · líneas 78–79] Punto de entrada: ejecuta main cuando el archivo se corre como script.
if __name__ == '__main__':
    main()
```

### primera_competencia/entrenar.py

Script que entrena los doce modelos LightGBM del ensamble con las matrices de 202103–202106 y las configuraciones de 01_optimizacion/configuraciones.json, y compara sus predicciones de 202108 con las de referencia.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–9] Importa argparse, gc, json, time, lightgbm y numpy, y trae ROOT, CONFIG, preparar y
#   sha256 de src/datos.py.
"""Reentrenamiento de los doce componentes del ensamble final."""
import argparse
import gc
import json
import time
from pathlib import Path
import lightgbm as lgb
import numpy as np
from src.datos import ROOT, CONFIG, preparar, sha256


# [Anotación · líneas 12–21] cargar_entrenamiento concatena las matrices x y las etiquetas y de los meses
#   pedidos, exige que ninguna fila tenga la etiqueta 255 (sin clase) y construye un lgb.Dataset con clase
#   binaria: 1 si la etiqueta es 1 o 2 (BAJA+1 o BAJA+2) y 0 si no. Usa los nombres de variables de la
#   configuración, max_bin 31 y feature_pre_filter en False.
def cargar_entrenamiento(data, months, threads):
    arrays = [np.load(data / f'x_{m}.npy', mmap_mode='r') for m in months]
    x = np.concatenate(arrays)
    labels = np.concatenate([np.load(data / f'y_{m}.npy') for m in months])
    assert (labels != 255).all()
    d = lgb.Dataset(x, label=np.isin(labels, [1, 2]).astype('int8'),
                    feature_name=CONFIG['features'], free_raw_data=True,
                    params={'max_bin': 31, 'feature_pre_filter': False, 'num_threads': threads})
    d.construct()
    return d


# [Anotación · líneas 24–31] Define los argumentos: --dataset o --datos (uno obligatorio), --salida con valor
#   por defecto 'reentrenamiento' y --indices para entrenar sólo un subconjunto de los componentes.
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--dataset', type=Path)
    source.add_argument('--datos', type=Path, help='Matrices creadas por reproducir.py.')
    parser.add_argument('--salida', type=Path, default=Path('reentrenamiento'))
    parser.add_argument('--indices', type=int, nargs='+', help='Subconjunto opcional para comprobar una corrida.')
    args = parser.parse_args()
# [Anotación · líneas 32–36] Crea la carpeta de salida, construye las matrices desde el CSV o toma las
#   indicadas, y comprueba el SHA-256 de x e y de los seis meses contra configuracion.json.
    args.salida.mkdir(parents=True, exist_ok=True)
    data = preparar(args.dataset, args.salida / 'datos') if args.dataset else args.datos.resolve()
    for m in CONFIG['months']:
        assert sha256(data / f'x_{m}.npy') == CONFIG['matrix_sha256'][str(m)]
        assert sha256(data / f'y_{m}.npy') == CONFIG['labels_sha256'][str(m)]
# [Anotación · líneas 37–43] Lee configuraciones.json, filtra los modelos según --indices (error si no queda
#   ninguno), carga las probabilidades de referencia y la matriz de 202108, y construye el dataset de
#   entrenamiento con los meses de CONFIG['train_months'] (202103 a 202106).
    configs = json.loads((ROOT / '01_optimizacion/configuraciones.json').read_text())
    entries = [m for m in CONFIG['models'] if args.indices is None or m['index'] in args.indices]
    if not entries:
        raise ValueError('No hay componentes seleccionados.')
    reference = np.load(ROOT / '03_prediccion_final/predicciones_referencia.npz')
    xt = np.load(data / 'x_202108.npy', mmap_mode='r')
    d = cargar_entrenamiento(data, CONFIG['train_months'], entries[0]['threads'])
# [Anotación · líneas 44–54] Para cada componente arma los parámetros: los comunes de fixed_params más
#   num_leaves, min_sum_hessian_in_leaf y semilla de su configuración y la cantidad de hilos del modelo. Entrena
#   con lgb.train durante num_iterations iteraciones, sin conjunto de validación, y guarda el modelo como
#   modelo_XX.txt.
    report = []
    for entry in entries:
        start = time.monotonic()
        i = entry['index']
        c = configs[i]
        params = dict(CONFIG['fixed_params'], num_leaves=c['num_leaves'],
                      min_sum_hessian_in_leaf=c['min_sum_hessian_in_leaf'],
                      seed=c['seed'], num_threads=entry['threads'])
        b = lgb.train(params, d, num_boost_round=c['num_iterations'])
        path = args.salida / f'modelo_{i:02d}.txt'
        b.save_model(str(path))
# [Anotación · líneas 55–66] Predice 202108 con el modelo recién entrenado y calcula la máxima diferencia
#   absoluta contra las probabilidades de referencia de ese componente. Agrega al informe el índice, el SHA-256
#   del archivo, el error y los segundos, reescribe VERIFICACION_ENTRENAMIENTO.json después de cada modelo y
#   corta con error si la diferencia supera 1e-12. Libera el modelo de memoria.
        pred = b.predict(xt, num_threads=entry['threads'])
        j = CONFIG['selected_model_indices'].index(i)
        error = float(np.max(np.abs(pred - reference['probabilities'][j])))
        record = {'index': i, 'sha256': sha256(path), 'max_abs_prediction_error': error,
                  'seconds': round(time.monotonic() - start, 2)}
        report.append(record)
        (args.salida / 'VERIFICACION_ENTRENAMIENTO.json').write_text(json.dumps(report, indent=2) + '\n')
        print(record, flush=True)
        if error > 1e-12:
            raise ValueError('Reentrenamiento distinto; revisar versiones y entorno antes de continuar.')
        del b
        gc.collect()


# [Anotación · líneas 69–70] Punto de entrada: ejecuta main cuando el archivo se corre como script.
if __name__ == '__main__':
    main()
```

### primera_competencia/01_optimizacion/optimizar.py

Script de la búsqueda de hiperparámetros con Optuna, con tres modos: verificar (compara configuraciones.json con el estudio guardado en estudio.sqlite), repetir (reevalúa las doce configuraciones en los dos folds) y nueva (corre una búsqueda con el mismo espacio y objetivo). Según el README, no hace falta para reproducir el CSV final.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–15] Agrega la carpeta primera_competencia al path de importación; importa lightgbm,
#   numpy, optuna y roc_auc_score, las utilidades de src/datos.py y cargar_entrenamiento de entrenar.py. HERE es
#   la carpeta del script.
"""Origen de parámetros, reevaluación temporal y búsqueda nueva con Optuna."""
import argparse
import gc
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lightgbm as lgb
import numpy as np
import optuna
from sklearn.metrics import roc_auc_score
from src.datos import ROOT, CONFIG, preparar, sha256
from entrenar import cargar_entrenamiento

HERE = Path(__file__).resolve().parent


# [Anotación · líneas 18–21] estudio_original abre estudio.sqlite, exige que contenga un único estudio y lo
#   carga.
def estudio_original():
    names = optuna.study.get_all_study_names(storage=f'sqlite:///{HERE / "estudio.sqlite"}')
    assert len(names) == 1
    return optuna.load_study(study_name=names[0], storage=f'sqlite:///{HERE / "estudio.sqlite"}')


# [Anotación · líneas 24–36] verificar toma los trials en estado COMPLETE del estudio y las entradas de
#   configuraciones.json, exige que haya 12 de cada uno y comprueba, par a par, número de trial, semilla,
#   num_leaves, min_sum_hessian_in_leaf, métricas por fold y AUC, y que num_iterations sea el promedio
#   redondeado de best_iteration de los folds.
def verificar():
    study = estudio_original()
    complete = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    configs = json.loads((HERE / 'configuraciones.json').read_text())
    assert len(complete) == len(configs) == 12
    for c, t in zip(configs, complete):
        assert c['trial'] == t.number and c['seed'] == t.user_attrs['seed']
        assert c['num_leaves'] == t.params['num_leaves']
        assert c['min_sum_hessian_in_leaf'] == t.params['min_sum_hessian_in_leaf']
        assert c['num_iterations'] == round(np.mean([f['best_iteration'] for f in t.user_attrs['folds']]))
        assert c['folds'] == t.user_attrs['folds'] and c['auc'] == t.value
    print('Las doce configuraciones coinciden con el estudio original.', flush=True)
    return study, configs


# [Anotación · líneas 39–51] evaluate recorre los folds y entrena LightGBM hasta el tope de árboles 'cap' con
#   early stopping de 150 iteraciones sobre el conjunto de validación. La métrica es el AUC nativo de LightGBM
#   (native=True) o una función propia que recalcula el AUC con roc_auc_score en la primera iteración y cada 10,
#   y devuelve el último valor calculado en las demás.
def evaluate(params, cap, folds, destination, trial, native=False):
    metrics = []
    for month, data, x, y, valid, ids in folds:
        counter, cached = [0], [0.0]
        def periodic_auc(pred, dataset):
            counter[0] += 1
            if counter[0] == 1 or counter[0] % 10 == 0:
                cached[0] = float(roc_auc_score(dataset.get_label(), pred))
            return 'auc', cached[0], True
        metric = {'metric': 'auc'} if native else {'metric': 'None'}
        b = lgb.train(dict(params, **metric), data, num_boost_round=cap,
                      valid_sets=[valid], feval=None if native else periodic_auc,
                      callbacks=[lgb.early_stopping(150, verbose=False)])
# [Anotación · líneas 52–64] Predice el mes de validación, ordena por probabilidad descendente e ID ascendente
#   y toma los primeros 10.500. Registra la iteración elegida, si se alcanzó el tope, el AUC con positivos =
#   etiquetas 1 y 2, el AUC con positivo = etiqueta 2 y la ganancia en millones: (1.100.000 × cantidad de BAJA+2
#   entre los 10.500 − 27.500 × 10.500) / 1e6. Guarda el modelo del fold y libera memoria.
        pred = b.predict(x, num_threads=3)
        order = np.lexsort((ids, -pred))[:10500]
        best = b.best_iteration or b.current_iteration()
        metrics.append({'month': month, 'best_iteration': best, 'cap': cap,
                        'cap_reached': best >= cap,
                        'auc_both': roc_auc_score(np.isin(y, [1, 2]), pred),
                        'auc_baja2': roc_auc_score(y == 2, pred),
                        'gain_m': (1100000 * int((y[order] == 2).sum()) - 27500 * 10500) / 1e6})
        b.save_model(str(destination / f'trial{trial:02d}_{month}.txt'))
        print(f'Trial {trial}, mes {month}: {metrics[-1]}', flush=True)
        del b
        gc.collect()
    return metrics


# [Anotación · líneas 67–78] Define los argumentos: modo (verificar, repetir o nueva), --dataset o --datos,
#   --salida con valor por defecto 'optimizacion_nueva' y --trials con valor por defecto 12. Siempre corre
#   verificar primero y termina ahí si el modo es verificar.
def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('modo', choices=['verificar', 'repetir', 'nueva'])
    group = p.add_mutually_exclusive_group()
    group.add_argument('--dataset', type=Path)
    group.add_argument('--datos', type=Path)
    p.add_argument('--salida', type=Path, default=Path('optimizacion_nueva'))
    p.add_argument('--trials', type=int, default=12)
    args = p.parse_args()
    old, configs = verificar()
    if args.modo == 'verificar':
        return
# [Anotación · líneas 79–85] Exige --dataset o --datos, construye o toma las matrices y comprueba el SHA-256
#   de x e y de los seis meses.
    if args.dataset is None and args.datos is None:
        p.error('Indicar --dataset o --datos para entrenar.')
    args.salida.mkdir(parents=True, exist_ok=True)
    data = preparar(args.dataset, args.salida / 'datos') if args.dataset else args.datos.resolve()
    for month in CONFIG['months']:
        assert sha256(data / f'x_{month}.npy') == CONFIG['matrix_sha256'][str(month)]
        assert sha256(data / f'y_{month}.npy') == CONFIG['labels_sha256'][str(month)]
# [Anotación · líneas 86–92] Arma los dos folds: entrenar con 202103 y validar en 202105; entrenar con 202103
#   y 202104 y validar en 202106. Para cada uno guarda el dataset de entrenamiento (3 hilos), la matriz, las
#   etiquetas y los IDs del mes de validación, y un lgb.Dataset de validación con clase binaria (etiquetas 1 y 2
#   como positivos).
    folds = []
    for months, month in [([202103], 202105), ([202103, 202104], 202106)]:
        d = cargar_entrenamiento(data, months, 3)
        x = np.load(data / f'x_{month}.npy', mmap_mode='r')
        y = np.load(data / f'y_{month}.npy')
        valid = lgb.Dataset(x, label=np.isin(y, [1, 2]).astype('int8'), reference=d)
        folds.append((month, d, x, y, valid, np.load(data / f'ids_{month}.npy')))
# [Anotación · líneas 93–102] Modo repetir: para cada una de las doce configuraciones arma los parámetros
#   (fixed_params más semilla, num_leaves y min_sum_hessian_in_leaf), la evalúa con el tope de árboles del trial
#   original, con AUC nativo sólo para el trial 0, y escribe reevaluacion.json con las métricas nuevas junto a
#   las originales.
    if args.modo == 'repetir':
        report = []
        for c in configs:
            t = old.trials[c['trial']]
            params = dict(CONFIG['fixed_params'], seed=c['seed'], num_leaves=c['num_leaves'],
                          min_sum_hessian_in_leaf=c['min_sum_hessian_in_leaf'])
            metrics = evaluate(params, t.params['num_iterations'], folds, args.salida, t.number, native=t.number == 0)
            report.append({'trial': t.number, 'folds': metrics, 'original_folds': c['folds']})
            (args.salida / 'reevaluacion.json').write_text(json.dumps(report, indent=2) + '\n')
        return
# [Anotación · líneas 103–117] Modo nueva: crea el estudio 'rank_directo' en un estudio.sqlite dentro de
#   --salida, con dirección maximizar y TPESampler(seed=882026, n_startup_trials=4). Cada trial propone tope de
#   árboles entre {2000, 4000, 8000}, num_leaves entre {8, 16, 24, 32, 48, 64} y min_sum_hessian_in_leaf entre 1
#   y 100 en escala logarítmica; usa la semilla 882026 + número de trial × 1009, evalúa en los dos folds, guarda
#   métricas y semilla como atributos del trial y devuelve el promedio del AUC con ambas bajas. Corre la
#   cantidad de trials pedida.
    study = optuna.create_study(study_name='rank_directo',
            storage=f'sqlite:///{args.salida.resolve() / "estudio.sqlite"}',
            direction='maximize', sampler=optuna.samplers.TPESampler(seed=882026, n_startup_trials=4))
    def objective(t):
        cap = t.suggest_categorical('num_iterations', [2000, 4000, 8000])
        leaves = t.suggest_categorical('num_leaves', [8, 16, 24, 32, 48, 64])
        hessian = t.suggest_float('min_sum_hessian_in_leaf', 1, 100, log=True)
        seed = 882026 + t.number * 1009
        params = dict(CONFIG['fixed_params'], num_leaves=leaves, min_sum_hessian_in_leaf=hessian, seed=seed)
        metrics = evaluate(params, cap, folds, args.salida, t.number)
        t.set_user_attr('folds', metrics)
        t.set_user_attr('seed', seed)
        return float(np.mean([m['auc_both'] for m in metrics]))
    study.optimize(objective, n_trials=args.trials)
    print(f'Búsqueda nueva guardada en {args.salida}. No modifica la configuración final.')


# [Anotación · líneas 120–121] Punto de entrada: ejecuta main cuando el archivo se corre como script.
if __name__ == '__main__':
    main()
```

### primera_competencia/src/datos.py

Módulo que construye, a partir del CSV de la competencia, las matrices mensuales de 762 variables (originales, lags, deltas y ranks por mes), los IDs y las etiquetas, y verifica sus hashes. Lo usan reproducir.py, entrenar.py y optimizar.py.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–11] Importa pathlib, gc, hashlib, json, duckdb, numpy y pandas. Define ROOT como la
#   carpeta que contiene a src/ y carga configuracion.json en CONFIG.
"""Construcción de variables mensuales y verificación de las matrices."""
from pathlib import Path
import gc
import hashlib
import json
import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'configuracion.json').read_text())


# [Anotación · líneas 14–16] sha256 devuelve el hash SHA-256 en hexadecimal del archivo indicado.
def sha256(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


# [Anotación · líneas 19–29] rank_signo recibe una columna y devuelve un vector float32: los valores no
#   finitos quedan NA, los ceros quedan en 0, los positivos se reemplazan por su rank percentil entre los
#   positivos (valores en (0, 1]) y los negativos por el rank percentil de su valor absoluto entre los
#   negativos, con signo menos (valores en [−1, 0)). Los empates toman el rango medio.
def rank_signo(values):
    values = np.asarray(values)
    result = np.full(values.shape, np.nan, dtype='float32')
    finite = np.isfinite(values)
    result[finite & (values == 0)] = 0
    for sign in (1, -1):
        use = finite & (values * sign > 0)
        if use.any():
            result[use] = sign * pd.Series(np.abs(values[use])).rank(
                method='average', pct=True).to_numpy(dtype='float32')
    return result


# [Anotación · líneas 32–49] preparar abre DuckDB con 3 hilos y límite de memoria de 8 GB, lee el CSV, corta
#   con error si falta alguna de las 154 columnas de raw_features y carga esas columnas en pandas ordenadas por
#   numero_de_cliente y foto_mes. Corta con error si hay pares cliente/mes duplicados o si los meses no son
#   exactamente 202103 a 202108.
def preparar(dataset, output):
    dataset = Path(dataset).resolve()
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    months = CONFIG['months']
    con = duckdb.connect()
    con.execute("SET threads=3; SET memory_limit='8GB'")
    relation = con.read_csv(str(dataset), header=True)
    missing = set(CONFIG['raw_features']) - set(relation.columns)
    if missing:
        raise ValueError(f'Faltan columnas: {sorted(missing)}')
    relation.create_view('entrada')
    columns = ','.join('"' + x + '"' for x in CONFIG['raw_features'])
    d = con.execute(f'SELECT {columns} FROM entrada ORDER BY numero_de_cliente, foto_mes').df()
    if d.duplicated(['numero_de_cliente', 'foto_mes']).any():
        raise ValueError('Hay pares cliente/mes duplicados.')
    if sorted(d.foto_mes.unique().tolist()) != months:
        raise ValueError('Se esperan los meses 202103–202108 de la competencia.')
# [Anotación · líneas 50–56] Arma, por mes, el vector de IDs en int64 y una tabla indexada por
#   numero_de_cliente. Si el CSV trae clase_ternaria, la lee en el mismo orden. Cierra la conexión.
    # Los identificadores conservan int64; el modelo recibe una copia float32.
    ids = {m: d.loc[d.foto_mes.eq(m), 'numero_de_cliente'].to_numpy(dtype='int64') for m in months}
    parts = {m: d[d.foto_mes.eq(m)].set_index('numero_de_cliente', drop=False) for m in months}
    supplied = None
    if 'clase_ternaria' in relation.columns:
        supplied = con.execute('SELECT clase_ternaria FROM entrada ORDER BY numero_de_cliente, foto_mes').df()['clase_ternaria']
    con.close()
# [Anotación · líneas 57–62] Pasa ccajas_depositos a NA en 202105. Para esa variable calcula lag 1 y lag 2
#   desplazando una y dos filas dentro de cada cliente (observaciones previas del cliente) y delta 1 y delta 2
#   como la diferencia con esos lags.
    d.loc[d.foto_mes.eq(202105), 'ccajas_depositos'] = np.nan
    # Esta familia conserva la regla de observaciones previas del entrenamiento.
    dep = {'ccajas_depositos': d.ccajas_depositos}
    for lag in (1, 2):
        dep[f'lag{lag}_ccajas_depositos'] = d.groupby('numero_de_cliente', sort=False).ccajas_depositos.shift(lag)
        dep[f'delta{lag}_ccajas_depositos'] = d.ccajas_depositos - dep[f'lag{lag}_ccajas_depositos']
# [Anotación · líneas 63–75] Para cada mes toma las 154 columnas originales en float64 y, para cada variable
#   distinta de numero_de_cliente y foto_mes, calcula lag 1 y lag 2 buscando al mismo cliente en la tabla del
#   mes menos 1 y del mes menos 2 (NA si el cliente no figura o si ese mes no está en los datos) y delta 1 y
#   delta 2 como valor actual menos lag.
    records = {}
    for month in months:
        current = parts[month]
        index = ids[month]
        values = {c: current[c].to_numpy(dtype='float64', na_value=np.nan) for c in CONFIG['raw_features']}
        for c in CONFIG['raw_features']:
            if c in ('numero_de_cliente', 'foto_mes'):
                continue
            for lag in (1, 2):
                past = month - lag
                prior = parts[past][c].reindex(index).to_numpy(dtype='float64', na_value=np.nan) if past in parts else np.full(len(index), np.nan)
                values[f'lag{lag}_{c}'] = prior
                values[f'delta{lag}_{c}'] = values[c] - prior
# [Anotación · líneas 76–84] Reemplaza las cinco columnas de ccajas_depositos por las calculadas antes para
#   esa variable. Arma la matriz del mes en float32 con las 762 columnas en el orden de CONFIG['features'],
#   aplica rank_signo sobre las filas del mes a cada una de las 365 columnas de rank_columns y corta con error
#   si queda algún valor infinito.
        mask = d.foto_mes.eq(month)
        for name, series in dep.items():
            values[name] = series.loc[mask].to_numpy(dtype='float64', na_value=np.nan)
        x = np.asfortranarray(np.column_stack([values[c] for c in CONFIG['features']]), dtype='float32')
        for col in CONFIG['rank_columns']:
            j = CONFIG['features'].index(col)
            x[:, j] = rank_signo(x[:, j])
        if not np.isfinite(x[~np.isnan(x)]).all():
            raise ValueError('La matriz contiene valores infinitos.')
# [Anotación · líneas 85–95] Crea el vector de etiquetas con 255 (sin clase). Para los meses hasta 202106: si
#   hay clase_ternaria exige que todos los valores sean CONTINUA, BAJA+1 o BAJA+2 y los codifica como 0, 1 y 2;
#   si no, asigna 0 al cliente presente dos meses después, 2 al presente el mes siguiente pero no dos meses
#   después, y 1 al que no está en ninguno de los dos.
        y = np.full(len(index), 255, dtype='uint8')
        if month <= 202106:
            if supplied is not None:
                label = supplied.loc[mask]
                if not label.isin(['CONTINUA', 'BAJA+1', 'BAJA+2']).all():
                    raise ValueError(f'Etiquetas incompletas en {month}.')
                y = label.map({'CONTINUA': 0, 'BAJA+1': 1, 'BAJA+2': 2}).to_numpy(dtype='uint8')
            else:
                next1 = np.isin(index, ids[month + 1])
                next2 = np.isin(index, ids[month + 2])
                y = np.where(next2, 0, np.where(next1, 2, 1)).astype('uint8')
# [Anotación · líneas 96–109] Guarda x_<mes>.npy, ids_<mes>.npy e y_<mes>.npy, calcula el SHA-256 de cada uno
#   y lo compara con el esperado en configuracion.json; si no coincide corta con error. Imprime la cantidad de
#   filas y de variables del mes y libera memoria.
        np.save(output / f'x_{month}.npy', x)
        np.save(output / f'ids_{month}.npy', index)
        np.save(output / f'y_{month}.npy', y)
        record = {}
        for prefix, key in [('x', 'matrix_sha256'), ('ids', 'ids_sha256'), ('y', 'labels_sha256')]:
            digest = sha256(output / f'{prefix}_{month}.npy')
            expected = CONFIG[key][str(month)]
            if digest != expected:
                raise ValueError(f'No coincide {prefix}_{month}: {digest}, esperado {expected}')
            record[prefix] = digest
        records[str(month)] = record
        print(f'Mes {month}: {len(index):,} filas, {x.shape[1]} variables, hashes verificados.', flush=True)
        del x, values
        gc.collect()
# [Anotación · líneas 110–111] Escribe VERIFICACION_DATOS.json con el SHA-256 del dataset de entrada y los
#   hashes de cada mes, y devuelve la carpeta de salida.
    (output / 'VERIFICACION_DATOS.json').write_text(json.dumps({'dataset_sha256': sha256(dataset), 'months': records}, indent=2) + '\n')
    return output
```


## Explicaciones del alumno (texto original)

### primera_competencia/README.md

> # Predicción de baja de clientes — Primera competencia
>
> Florencia Rodriguez · DMEyF 2026
>
> La predicción final es **un único archivo con 12.000 clientes de agosto de 2021**, generado por el promedio simple de las probabilidades de los **doce modelos LightGBM de V88**. Este paquete reconstruye las variables desde el dataset y reproduce exactamente ese CSV. Incluye el reentrenamiento y la optimización original que dio origen a sus parámetros.
>
> | Referencia | Valor |
> |---|---|
> | Archivo final | `03_prediccion_final/FlorFinalV88_completo12_k12000.csv` |
> | Formato | Una columna de IDs enteros, sin encabezado ni índice |
> | Filas | 12.000 |
> | Mensaje de submit | FlorFinalV88Completo12k12000 |
> | Submission ID | 1567-1791772073752266 |
> | Ganancia pública | 104,8575 M |
> | Desvío informado | 0,0000 M; un único archivo |
> | SHA-256 | `087d379dbc269b08cf139f91b9b8542b5855657965b379524b2d948d753c1d43` |
>
> ## 1. Instalación
>
> Entorno verificado: **Python 3.11**, versiones fijadas en `requirements.txt`. Se recomienda 16 GB de RAM como mínimo y 8 GB libres en disco para matrices y salidas. El dataset no se incluye en el repositorio.
>
> Desde esta carpeta:
>
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> python -m pip install -r requirements.txt
> ```
>
> En Windows, activar con `.venv\Scripts\activate`. LightGBM requiere OpenMP; si falta en macOS, instalar `libomp` con Homebrew. En Linux se necesita la biblioteca `libgomp`.
>
> ## 2. Reproducir la predicción exacta
>
> Usar el CSV original con los meses **202103–202108** y los nombres originales de sus columnas. Acepta `clase_ternaria` ya incluida. Si no está, reconstruye las etiquetas de marzo–junio por presencia de clientes en los dos meses siguientes; julio/agosto quedan sin etiqueta.
>
> ```bash
> python reproducir.py --dataset "/ruta/competencia_01.csv" --salida salida
> ```
>
> El comando:
>
> 1. Reconstruye las 762 variables, su orden y sus valores `float32`.
> 2. Verifica SHA-256 de las seis matrices mensuales, IDs y etiquetas contra la corrida original.
> 3. Carga los doce modelos guardados y recalcula las probabilidades de los 164.647 clientes de agosto.
> 4. Comprueba las probabilidades contra la referencia, con tolerancia absoluta `1e-12`.
> 5. Promedia las probabilidades de los doce modelos, en orden de índice y con igual peso; ordena por score descendente y por ID ascendente ante empate; toma los primeros 12.000.
> 6. Compara el CSV final, byte por byte, contra la referencia incluida.
>
> Las salidas son `salida/predicciones_finales/FlorFinalV88_completo12_k12000.csv`, `salida/VERIFICACION.json` y `salida/datos/VERIFICACION_DATOS.json`. Si la lista no coincide, el programa termina con error. La referencia de probabilidades sirve para auditar: **la predicción se calcula desde los datos y los modelos**, no se copia de esa referencia.
>
> La inferencia no necesita credenciales, servicios externos ni volver a optimizar. El tiempo de la reproducción completa está registrado en `VERIFICACION.json`. Las matrices también se verificaron desde el CSV crudo sin target.
>
> ## 3. Variables y modelo
>
> - **Target de entrenamiento:** BAJA+1 o BAJA+2 = 1; CONTINUA = 0. La ganancia de evaluación recompensa únicamente BAJA+2: +1.072.500 por acierto y −27.500 por contacto incorrecto.
> - **Entrenamiento final:** marzo, abril, mayo y junio de 2021, sin undersampling de clases ni pesos de recencia. El bagging de LightGBM toma 70% de filas por iteración; no es un muestreo específico de CONTINUA.
> - **Historia:** lags 1 y 2 y deltas contra esos lags de las variables originales, excepto ID y mes. Los lags generales buscan el mes calendario exacto. Se usa julio para construir la historia de agosto.
> - **Calidad:** `ccajas_depositos` pasa a NA en mayo antes de reconstruir su historia. Para reproducir exactamente el entrenamiento, esa familia conserva lags por observaciones previas del cliente; es la única excepción a los lags por calendario. Los faltantes se preservan.
> - **Rankings:** después de calcular historia y convertir a `float32`, 365 campos monetarios actuales e históricos se reemplazan por rankings dentro de cada mes. Los positivos quedan en (0, 1], los negativos en [−1, 0), cero conserva cero y NA conserva NA. Los empates usan rango medio. La población de referencia es el conjunto completo de clientes observado en cada mes, sin usar etiquetas.
> - **Orden de columnas:** fijado en `configuracion.json`. Se conservan ID, mes, personales y fechas.
> - **Parámetros fijos:** learning rate 0,005; max_bin 31; min_data_in_leaf 0; feature_fraction 0,50; feature_fraction_bynode 0,20; bagging_fraction 0,70; bagging_freq 1. `deterministic` y `force_col_wise` están activados.
> - **Ensamble final:** promedio completo de los doce componentes, índices 0 a 11 en ese orden, con igual peso. Los índices, semillas y parámetros están fijados en `configuracion.json`. Se promedian probabilidades antes de ordenar; no se promedian IDs ni selecciones binarias.
>
> ## 4. De dónde salen los hiperparámetros
>
> `01_optimizacion/estudio.sqlite` es la base Optuna original: **12 trials completos y uno interrumpido**. Se incluyen las doce configuraciones, y la lista final utiliza los doce con igual peso.
>
> - Objetivo: media de AUC para ambas bajas en **marzo→mayo** y **marzo–abril→junio**. Se registra además AUC BAJA+2 y ganancia a 10.500 contactos.
> - Sampler: TPE, semilla 882026, cuatro trials iniciales.
> - Espacio: tope de árboles {2.000, 4.000, 8.000}; hojas {8, 16, 24, 32, 48, 64}; mínimo Hessian de 1 a 100 en escala logarítmica.
> - Early stopping: 150 árboles. El trial 0 evaluó AUC nativa en cada árbol. Tras una interrupción se evaluó AUC exacta cada diez árboles, conservando su último valor entre evaluaciones; el AUC final se recalculó sobre la predicción elegida.
> - La configuración del trial interrumpido se volvió a encolar. Hubo un reinicio del sampler; por eso repetir una búsqueda nueva con la misma semilla no garantiza la misma secuencia de candidatos.
> - Árboles finales por modelo: promedio redondeado de las mejores iteraciones de los dos folds. Se conservaron los doce trials completos: no hubo selección de trials por resultados públicos.
>
> Comprobar el origen sin entrenar:
>
> ```bash
> python 01_optimizacion/optimizar.py verificar
> ```
>
> Reevaluar las doce configuraciones originales en sus folds, respetando la evaluación especial del trial 0:
>
> ```bash
> python 01_optimizacion/optimizar.py repetir --datos salida/datos --salida reevaluacion
> ```
>
> Ejecutar una búsqueda nueva con el mismo espacio y objetivo:
>
> ```bash
> python 01_optimizacion/optimizar.py nueva --datos salida/datos --salida nueva_busqueda --trials 12
> ```
>
> La búsqueda puede tardar varias horas. No es necesaria para reproducir el CSV final y no sobrescribe parámetros, estudio ni modelos de la entrega. Los folds fueron usados para desarrollo; no son un test independiente.
>
> ## 5. Reentrenar los modelos finales
>
> Para entrenar nuevamente los doce componentes con las configuraciones y semillas fijadas:
>
> ```bash
> python entrenar.py --datos salida/datos --salida reentrenamiento
> ```
>
> También puede iniciarse desde el CSV con `--dataset "/ruta/competencia_01.csv"` en lugar de `--datos`. La corrida usa todas las filas etiquetadas de marzo–junio. Guarda doce modelos nuevos, mide sus diferencias contra las probabilidades históricas y registra el tiempo de cada uno.
>
> Generar el CSV final usando esos nuevos modelos:
>
> ```bash
> python reproducir.py --dataset "/ruta/competencia_01.csv" --modelos reentrenamiento --salida salida_reentrenada
> ```
>
> La reproducción exacta verificada se realiza con los modelos incluidos. El reentrenamiento depende también de la versión nativa de LightGBM, arquitectura y aritmética del entorno; por eso tiene comprobaciones explícitas y no se promete igualdad en cualquier plataforma. `entorno.json` registra las versiones de la corrida verificada. Como comprobación adicional, se reentrenó el componente 08 en 10 minutos y 42 segundos: sus probabilidades coincidieron exactamente. No se repitieron los doce entrenamientos ni toda la búsqueda durante la preparación de esta carpeta.
>
> ## 6. Construcción y corte de la lista final
>
> Los experimentos de desarrollo usaron veinte combinaciones de diez modelos del pool de doce. La entrega final usa un único promedio completo de los doce modelos, sin escoger una combinación por su resultado público. Las predicciones individuales proceden de los mismos modelos ya entrenados y auditados.
>
> El corte de 12.000 se fijó tras comparar nueve cortes del mismo ranking de desarrollo, de 9.500 a 13.500. Entre 11.000 y 13.000 la media pública fue aproximadamente plana; se eligió el centro de esa zona en lugar del máximo puntual. Esa curva corresponde a los veinte subconjuntos exploratorios y orienta el corte.
>
> El archivo final se firma en `configuracion.json`, `VERIFICACION.json` y `SHA256SUMS.json`. La ejecución recalcula las probabilidades desde los modelos y comprueba la lista completa. Los doce modelos se conservan, junto con el estudio Optuna que originó sus hiperparámetros.
>
> ## Archivos
>
> ```text
> README.md
> requirements.txt
> configuracion.json
> entorno.json
> reproducir.py
> entrenar.py
> src/datos.py
> 01_optimizacion/
>     optimizar.py
>     estudio.sqlite
>     configuraciones.json
> 02_modelos/
>     modelo_XX.txt.gz
> 03_prediccion_final/
>     FlorFinalV88_completo12_k12000.csv
>     predicciones_referencia.npz
> VERIFICACION.json
> SHA256SUMS.json
> ```
>
> No hace falta ningún archivo de otros directorios del proyecto. Las salidas y el dataset quedan excluidos mediante `.gitignore`.
>
> Dudas o consultas: [correo]

