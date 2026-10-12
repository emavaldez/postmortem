# Valentín Turri — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: TURRIvalentin
- Repositorio: https://github.com/TURRIvalentin/dmeyf2026
- Link posteado: https://github.com/TURRIvalentin/dmeyf2026/tree/main/entrega_github_baseline
- Commit: 00875412f54bee1ed115a269e5807a5b8427ef4f
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/turrivalentin/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/turrivalentin.json

## Resumen

La entrega es la carpeta entrega_github_baseline de un fork: un paquete en Python con un orquestador (correr_todo.py), cuatro pasos numerados en src/, un módulo común y tres archivos JSON de configuración. El camino de la predicción lee el CSV crudo, calcula clase_ternaria según la presencia de cada cliente en los dos meses siguientes, pasa ccajas_depositos a NA en 202105, arma una matriz de 760 columnas (152 variables originales más sus lags y deltas de orden 1 y 2) y entrena 10 LightGBM con 202103-202106, sin submuestreo y con BAJA+1 y BAJA+2 como positivos. Cada modelo usa uno de los 10 juegos de hiperparámetros guardados en config/hiperparametros_baseline.json (que ese archivo atribuye a una búsqueda con Optuna de 30 trials cuyo código no está en el repositorio) y una semilla propia. Las probabilidades sobre 202108 se promedian y se escriben los 11.000 clientes de mayor probabilidad. El último paso verifica el formato y compara el sha256 del archivo generado con el de referencia/base_k11000.csv. El README narra además el recorrido previo (otros modelos, validación, variantes) y declara para esta entrega una ganancia de 108,57 en el Public Leaderboard.

**Qué entrega.** Un archivo base_k11000.csv con 11.000 numero_de_cliente de 202108, uno por línea y sin encabezado: los de mayor probabilidad promedio. El repositorio incluye en referencia/base_k11000.csv el archivo que, según el README, se envió al bot (11.000 líneas en el clon); el paquete lo regenera en salida/base_k11000.csv junto con salida/prediccion_completa_202108.csv (numero_de_cliente, Predicted con 1 o 0 para todos los clientes de 202108).

**Cómo se ejecuta.** Según el README: descargar competencia_01_crudo.csv (no está en el repositorio) y dejarlo en datos/competencia_01_crudo.csv o indicar su ruta con --crudo; instalar las dependencias con 'pip install -r requirements_minimos.txt' (Python 3.11.6, Windows 11); ejecutar 'python correr_todo.py --crudo RUTA/competencia_01_crudo.csv', que corre los pasos 01 a 04 en orden. El README indica entre 80 y 90 minutos con 16 núcleos y que la búsqueda de hiperparámetros no se vuelve a correr.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: 1 si clase_ternaria es BAJA+1 o BAJA+2 (lista lgbm_target_positivos de config/entrega.json), 0 en otro caso. La clase_ternaria se calcula en el paso 01: BAJA+1 si el cliente no está en el mes siguiente, BAJA+2 si está en el siguiente pero no dos meses después, CONTINUA en el resto.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica: el paso 02 entrena con todas las filas de 202103 a 202106 (comentario 'Sin undersampling' en src/02_entrenar_y_predecir.py, línea 27).
- **Calidad de datos:** ccajas_depositos se pasa a NA en 202105 antes de calcular los lags (variables_en_na en config/entrega.json). El paso 01 verifica que numero_de_cliente sea entero exacto, que no haya pares (cliente, mes) repetidos y que los conteos de clase_ternaria de 202103 a 202108 coincidan con los escritos en config/entrega.json.
- **Drifting:** No se observa en el código. El README menciona un cálculo de PSI y un AUC adversarial sobre 202108, sin código en el repositorio.
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** Lag 1 y lag 2 de cada una de las 152 variables y delta 1 y delta 2 (valor menos lag): 608 columnas agregadas, 760 en total. El lag toma el valor del mismo cliente exactamente k meses antes; si esa fila no existe queda NaN.
- **Selección de variables:** No se observa en el código: se usan las 152 variables listadas en config/features_crudas.json.
- **Optimización de hiperparámetros:** No se ejecuta en el paquete. config/hiperparametros_baseline.json declara una búsqueda con Optuna TPESampler(seed=252443) de 30 trials sobre num_iterations (entero en [500, 2000], paso 50), num_leaves (entero en [16, 1024], escala log) y min_sum_hessian_in_leaf (real en [0.001, 100], escala log), entrenando con 202103-202104 y midiendo AUC en 202106; el script que cita (mejoras_v11/01_bayesiana.py) no está en el repositorio.
- **Hiperparámetros finales:** Fijos para los 10 modelos: objective binary, max_bin 31, min_child_samples 0, feature_fraction 0.5, feature_fraction_bynode 0.2, learning_rate 0.005, metric auc, n_jobs -1. Por modelo, uno de 10 juegos (num_iterations, num_leaves, min_sum_hessian_in_leaf): el primero es (1650, 63, 11.58) y el décimo (1600, 55, 31.51); num_iterations va de 1000 a 1750, num_leaves de 48 a 606 y min_sum_hessian_in_leaf de 1.07 a 31.51.
- **Semillas:** 10 semillas escritas en config/entrega.json (252443, 645419, 856841, 750383, 537181, 100003, 200017, 300023, 400031, 500057); el modelo i usa la semilla i como random_state.
- **Cantidad de semillas:** 10
- **Ensamble:** Promedio de las probabilidades de 10 LightGBM; cada uno tiene un juego de hiperparámetros distinto y una semilla distinta.
- **Corte:** Cantidad fija: los 11.000 clientes de mayor probabilidad promedio (n_envios en config/entrega.json), con ordenamiento estable ante empates. Según el README, el valor 11.000 se eligió mirando el Public Leaderboard.
- **Validación:** El paquete no calcula métricas de validación. Según config/hiperparametros_baseline.json, la búsqueda de hiperparámetros entrenó con 202103-202104 y midió AUC en 202106 (valores entre 0.9185 y 0.9202 en los 10 juegos guardados). El paso 04 compara el sha256 del archivo generado con el esperado y con el del archivo de referencia.
- **Salidas:** salida/base_k11000.csv (11.000 IDs, uno por línea, sin encabezado); salida/prediccion_completa_202108.csv (numero_de_cliente, Predicted); intermedios trabajo/competencia_01.parquet y trabajo/probabilidades_202108.npz (una columna de probabilidades por modelo).

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optuna (`hiperparametros.optuna`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)
- El repositorio declara el uso de asistentes de IA (`proceso.uso_de_ia_declarado`)

## Técnicas sólo exploradas

- Random Forest (`modelo.random_forest`)
- XGBoost (`modelo.xgboost`)
- Regresión logística (`modelo.regresion_logistica`)
- Otro modelo (`modelo.otro_modelo`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Corta por umbral de probabilidad (`corte.umbral_probabilidad`)
- Genera archivos con varios cortes (`corte.varios_cortes`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Python 3.11.6 en Windows 11 (README). requirements_minimos.txt fija lightgbm 4.7.0, numpy 2.4.4, pandas 2.3.3, pyarrow 24.0.0, scikit-learn 1.8.0 y scipy 1.17.1; requirements.txt lista 338 entradas del entorno completo. El README indica 16 núcleos y entre 80 y 90 minutos, y que la reproducción exacta depende del orden de filas (config/orden_filas.npz), de las versiones de las librerías y de la cantidad de núcleos.

## Pasos del camino de la entrega

1. **Orquestación de los cuatro pasos.** correr_todo.py ejecuta en orden 01_preparar_datos.py, 02_entrenar_y_predecir.py, 03_generar_submit.py y 04_verificar.py como subprocesos con directorio de trabajo src/. Los argumentos de línea de comandos (--crudo) se pasan sólo a los pasos 01 y 04. Si un paso devuelve un código distinto de cero, la corrida termina. (`entrega_github_baseline/correr_todo.py` líneas 12–22)
2. **Carga de la configuración.** El módulo comun.py define las rutas de trabajo/ y salida/ relativas a la carpeta del paquete y lee de config/ las semillas, los meses de entrenamiento (202103 a 202106), el mes a predecir (202108), la cantidad de envíos (11.000), los órdenes de lag y delta (1 y 2), la lista de 152 variables, los parámetros fijos de LightGBM y los 10 juegos de hiperparámetros. (`entrega_github_baseline/src/comun.py` líneas 13–41; `entrega_github_baseline/config/entrega.json` líneas 3–36)
3. **Lectura del crudo.** El paso 01 resuelve la ruta del CSV crudo (--crudo, variable de entorno DMEYF_CRUDO o datos/competencia_01_crudo.csv), lo lee con las 152 variables en float32, verifica que numero_de_cliente sea entero exacto, lo convierte a int64 y comprueba que no haya pares (numero_de_cliente, foto_mes) repetidos. (`entrega_github_baseline/src/01_preparar_datos.py` líneas 14–24; `entrega_github_baseline/src/comun.py` líneas 44–48)
4. **Cálculo de clase_ternaria.** Numera los meses presentes y arma el conjunto de pares (cliente, índice de mes). Asigna BAJA+1 si el cliente no está en el mes siguiente, BAJA+2 si está en el siguiente pero no dos meses después y CONTINUA en el resto. Deja sin clase todo el último mes y, en el anteúltimo, a los clientes que sí aparecen en el mes siguiente. (`entrega_github_baseline/src/01_preparar_datos.py` líneas 26–38)
5. **Verificación de conteos por mes.** Cuenta las clases por foto_mes y compara cada conteo con conteo_clase_ternaria_esperado de config/entrega.json (202103 a 202108); una diferencia detiene la ejecución con un assert. (`entrega_github_baseline/src/01_preparar_datos.py` líneas 40–46; `entrega_github_baseline/config/entrega.json` líneas 37–74)
6. **Reordenamiento de filas y escritura del dataset.** Carga el arreglo 'orden' de config/orden_filas.npz, verifica que sea una permutación del largo del dataset, reordena las filas con él y escribe trabajo/competencia_01.parquet con numero_de_cliente, foto_mes, clase_ternaria y las 152 variables. (`entrega_github_baseline/src/01_preparar_datos.py` líneas 48–56)
7. **Corrección de ccajas_depositos.** El paso 02 lee el parquet y pasa a NaN las variables indicadas en variables_en_na para los meses indicados: ccajas_depositos en 202105. Se hace antes de calcular lags y deltas. (`entrega_github_baseline/src/02_entrenar_y_predecir.py` líneas 15–19; `entrega_github_baseline/config/entrega.json` líneas 32–36)
8. **Matriz de 760 columnas con lags y deltas.** Para las filas de 202103-202106 y de 202108 arma una matriz float32 con las 152 variables, sus lags de orden 1 y 2 y sus deltas (valor menos lag) de orden 1 y 2. El lag se calcula sobre todo el dataset buscando la fila del mismo cliente exactamente k meses antes; si no existe queda NaN. Luego separa X_train (202103-202106) y X_pred (202108). (`entrega_github_baseline/src/02_entrenar_y_predecir.py` líneas 20–26; `entrega_github_baseline/src/comun.py` líneas 51–86)
9. **Clase binaria de entrenamiento.** El vector objetivo vale 1 cuando clase_ternaria es BAJA+1 o BAJA+2 y 0 en otro caso, sobre todas las filas de entrenamiento, sin submuestreo. (`entrega_github_baseline/src/02_entrenar_y_predecir.py` líneas 27–30; `entrega_github_baseline/config/entrega.json` líneas 24–27)
10. **Juegos de hiperparámetros tomados de una búsqueda previa.** Los hiperparámetros no se buscan en el paquete: se leen de config/hiperparametros_baseline.json. Ese archivo declara que provienen de Optuna TPESampler(seed=252443) con 30 trials, entrenando con 202103-202104 y midiendo AUC en 202106, y guarda los 10 trials de mayor AUC con sus valores de num_iterations, num_leaves y min_sum_hessian_in_leaf. (`entrega_github_baseline/config/hiperparametros_baseline.json` líneas 3–35; `entrega_github_baseline/src/comun.py` líneas 37–41)
11. **Entrenamiento de 10 LightGBM y predicción de 202108.** Para cada uno de los 10 juegos crea un LGBMClassifier con los parámetros fijos, el juego i y la semilla i como random_state; lo entrena con 202103-202106 y guarda la probabilidad de la clase positiva para 202108. Tras cada modelo reescribe trabajo/probabilidades_202108.npz; si el archivo ya existe, los modelos presentes no se vuelven a entrenar. (`entrega_github_baseline/src/02_entrenar_y_predecir.py` líneas 32–42; `entrega_github_baseline/config/entrega.json` líneas 3–14)
12. **Promedio de probabilidades y corte en 11.000.** El paso 03 comprueba que estén los 10 modelos, promedia sus probabilidades por cliente, ordena de mayor a menor con ordenamiento estable y toma los primeros 11.000. (`entrega_github_baseline/src/03_generar_submit.py` líneas 8–18)
13. **Escritura de los archivos de salida.** Escribe salida/base_k11000.csv con un numero_de_cliente por línea, sin encabezado, y salida/prediccion_completa_202108.csv con numero_de_cliente y Predicted (1 para los 11.000 elegidos, 0 para el resto de los clientes de 202108). (`entrega_github_baseline/src/03_generar_submit.py` líneas 20–30)
14. **Verificación de formato y de hash.** El paso 04 revisa seis condiciones sobre el archivo generado: todas las líneas son enteros y no hay encabezado, no hay IDs repetidos, hay entre 8.000 y 15.000 líneas, no hay retornos de carro, todos los IDs están en 202108 del crudo y el sha256 coincide con sha256_submit_esperado y con el de referencia/base_k11000.csv. Termina con código 1 si alguna no se cumple. (`entrega_github_baseline/src/04_verificar.py` líneas 11–30; `entrega_github_baseline/config/entrega.json` líneas 75–75)

## Archivos

- `entrega_github_baseline/requirements.txt` · configuracion · Texto · 338 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/turrivalentin/entrega_github_baseline/requirements.txt.txt) — Listado de 338 entradas de un entorno de Python: 336 paquetes con versión fija (entre ellos lightgbm 4.7.0, optuna 4.9.0, xgboost 3.2.0, catboost 1.2.10 y torch 2.12.1) y dos instalaciones editables que apuntan a carpetas locales de Windows (líneas 59 y 301). El README no lo menciona en las instrucciones de ejecución.
- `entrega_github_baseline/correr_todo.py` · principal · Python · 22 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/turrivalentin/entrega_github_baseline/correr_todo.py.txt) — Orquestador: ejecuta los cuatro scripts de src/ en orden y corta la corrida si alguno termina con código distinto de cero.
- `entrega_github_baseline/requirements_minimos.txt` · configuracion · Texto · 6 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/turrivalentin/entrega_github_baseline/requirements_minimos.txt.txt) — Seis dependencias con versión fija, que el README indica instalar: lightgbm 4.7.0, numpy 2.4.4, pandas 2.3.3, pyarrow 24.0.0, scikit-learn 1.8.0 y scipy 1.17.1.
- `entrega_github_baseline/README.md` · explicacion · Markdown · 106 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/turrivalentin/entrega_github_baseline/README.md.txt) — Presenta la entrega final (base_k11000.csv, 11.000 clientes, ganancia declarada de 108,57 en el Public Leaderboard y su sha256), describe el modelo, narra en cinco etapas el recorrido previo con los puntajes públicos de cada una (Random Forest 85,36; LightGBM 88,03; blend 90,39, luego 97,00 y 99,41; el baseline 106,8, 107,0 y 108,6 con 10.000, 10.500 y 11.000 envíos) e incluye instrucciones de ejecución, limitaciones declaradas, el uso de Claude como asistente y la salida de una corrida de verificación de 88 minutos.
- `entrega_github_baseline/config/entrega.json` · configuracion · JSON · 76 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/turrivalentin/entrega_github_baseline/config/entrega.json.txt) — Parámetros de la entrega: semillas, meses de entrenamiento, mes a predecir, cantidad de envíos, nombre del archivo, clases positivas, órdenes de lag y delta, variables a pasar a NA, conteos esperados de clase_ternaria por mes y sha256 esperado.
- `entrega_github_baseline/config/features_crudas.json` · configuracion · JSON · 156 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/turrivalentin/entrega_github_baseline/config/features_crudas.json.txt) — Lista 'features' con los nombres de las 152 variables del dataset que entran al modelo, en el orden en que forman las columnas de la matriz.
- `entrega_github_baseline/config/hiperparametros_baseline.json` · configuracion · JSON · 36 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/turrivalentin/entrega_github_baseline/config/hiperparametros_baseline.json.txt) — Parámetros fijos de LightGBM, descripción de la búsqueda de la que salen los juegos de hiperparámetros y los 10 juegos usados por el paso 02, cada uno con su número de trial y su AUC en 202106.
- `entrega_github_baseline/src/04_verificar.py` · principal · Python · 30 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/turrivalentin/entrega_github_baseline/src/04_verificar.py.txt) — Paso 04: revisa el formato del archivo generado y compara su sha256 con el valor esperado de entrega.json y con el del archivo de referencia; devuelve código 1 si algún chequeo no se cumple.
- `entrega_github_baseline/src/01_preparar_datos.py` · principal · Python · 56 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/turrivalentin/entrega_github_baseline/src/01_preparar_datos.py.txt) — Paso 01: lee el CSV crudo, calcula clase_ternaria, compara los conteos por mes con los esperados, reordena las filas y escribe trabajo/competencia_01.parquet.
- `entrega_github_baseline/src/02_entrenar_y_predecir.py` · principal · Python · 42 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/turrivalentin/entrega_github_baseline/src/02_entrenar_y_predecir.py.txt) — Paso 02: pasa ccajas_depositos a NA en 202105, arma la matriz de 760 columnas, entrena 10 LGBMClassifier con 202103-202106 y guarda sus probabilidades para 202108.
- `entrega_github_baseline/src/03_generar_submit.py` · principal · Python · 30 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/turrivalentin/entrega_github_baseline/src/03_generar_submit.py.txt) — Paso 03: promedia las probabilidades de los 10 modelos, elige los 11.000 clientes de mayor promedio y escribe el archivo de envío y la predicción completa de 202108.
- `entrega_github_baseline/src/comun.py` · principal · Python · 86 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/turrivalentin/entrega_github_baseline/src/comun.py.txt) — Módulo compartido por los pasos 01 a 04: rutas, lectura de los JSON de config/ y las funciones lag y matriz que arman las columnas del modelo.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### entrega_github_baseline/correr_todo.py

Orquestador: ejecuta los cuatro scripts de src/ en orden y corta la corrida si alguno termina con código distinto de cero.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Docstring con la forma de uso (--crudo opcional; sin él se usa la variable de
#   entorno DMEYF_CRUDO o datos/competencia_01_crudo.csv). Importa os, subprocess, sys y time; define SRC como
#   la carpeta src/ ubicada junto al script y PASOS con los cuatro scripts numerados del 01 al 04.
"""Corre los pasos 01 a 04 en orden.

    python correr_todo.py [--crudo RUTA/competencia_01_crudo.csv]

Sin --crudo usa la variable de entorno DMEYF_CRUDO o datos/competencia_01_crudo.csv.
"""
import os
import subprocess
import sys
from time import time

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
PASOS = ['01_preparar_datos.py', '02_entrenar_y_predecir.py', '03_generar_submit.py', '04_verificar.py']

# [Anotación · líneas 15–22] Recorre PASOS e imprime el nombre de cada uno con los minutos transcurridos.
#   Ejecuta cada script con el mismo intérprete de Python y con src/ como directorio de trabajo; los argumentos
#   recibidos se reenvían sólo al primero y al cuarto (los que leen el crudo). Si el código de retorno no es
#   cero, sale con el mensaje '<paso> termino con error'. Al final imprime el tiempo total en minutos.
t0 = time()
for paso in PASOS:
    print(f'{paso} ({(time() - t0) / 60:.1f} min)', flush=True)
    # Solo 01 y 04 leen el crudo; el argumento se les pasa tal cual.
    args = sys.argv[1:] if paso in (PASOS[0], PASOS[3]) else []
    if subprocess.run([sys.executable, os.path.join(SRC, paso), *args], cwd=SRC).returncode != 0:
        sys.exit(f'{paso} termino con error')
print(f'listo en {(time() - t0) / 60:.1f} min')
```

### entrega_github_baseline/src/04_verificar.py

Paso 04: revisa el formato del archivo generado y compara su sha256 con el valor esperado de entrega.json y con el del archivo de referencia; devuelve código 1 si algún chequeo no se cumple.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–17] Lee en binario el archivo de envío generado, lo decodifica como ASCII, lo separa
#   por saltos de línea y convierte a entero las líneas formadas sólo por dígitos. Lee del crudo las columnas
#   numero_de_cliente y foto_mes y arma el conjunto de IDs de 202108. Calcula el sha256 del archivo generado y
#   el de referencia/base_k11000.csv.
"""Paso 04: verifica el formato del archivo y que sea idéntico (sha256) al que envié al bot.
Termina con código 1 si algún chequeo falla."""
import hashlib
import re
import sys

import pandas as pd

import comun as cm

contenido = open(cm.SUBMIT, 'rb').read()
lineas = contenido.decode('ascii').split('\n')
ids = [int(x) for x in lineas[:-1] if re.fullmatch(r'\d+', x)]
crudo = pd.read_csv(cm.ruta_crudo(), usecols=['numero_de_cliente', 'foto_mes'])
ids_mes = set(crudo.loc[crudo['foto_mes'] == cm.MES_PRED, 'numero_de_cliente'].astype('int64'))
sha = hashlib.sha256(contenido).hexdigest()
sha_ref = hashlib.sha256(open(cm.REFERENCIA, 'rb').read()).hexdigest()

# [Anotación · líneas 19–26] Define seis chequeos, cada uno con su mensaje: el archivo termina en salto de
#   línea y todas sus líneas son enteros; no hay IDs repetidos; la cantidad de líneas está entre 8.000 y 15.000;
#   no hay bytes de retorno de carro; todos los IDs pertenecen a 202108; el sha256 generado es igual al de
#   entrega.json y al del archivo de referencia.
chequeos = [
    (lineas[-1] == '' and len(ids) == len(lineas) - 1, f'{len(lineas) - 1:,} lineas, todas enteras sin encabezado'),
    (len(ids) == len(set(ids)), 'sin duplicados'),
    (8000 <= len(ids) <= 15000, 'entre 8.000 y 15.000 lineas'),
    (b'\r' not in contenido, 'sin retornos de carro'),
    (set(ids) <= ids_mes, f'todos los IDs estan en {cm.MES_PRED}'),
    (sha == cm.ENTREGA['sha256_submit_esperado'] == sha_ref, 'identico al archivo enviado'),
]
# [Anotación · líneas 27–30] Imprime 'OK' o 'FALLA' junto al mensaje de cada chequeo, luego el sha256 generado
#   y el esperado, y termina con código 0 si todos se cumplen o 1 en caso contrario.
for ok, msg in chequeos:
    print(('OK    ' if ok else 'FALLA ') + msg)
print(f'sha256 generado: {sha}\nsha256 esperado: {cm.ENTREGA["sha256_submit_esperado"]}')
sys.exit(0 if all(ok for ok, _ in chequeos) else 1)
```

### entrega_github_baseline/src/01_preparar_datos.py

Paso 01: lee el CSV crudo, calcula clase_ternaria, compara los conteos por mes con los esperados, reordena las filas y escribe trabajo/competencia_01.parquet.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–16] Docstring e importaciones (os, sys, numpy, pandas, comun). Obtiene la ruta del
#   crudo con cm.ruta_crudo() y, si el archivo no existe, termina con un mensaje que remite al README.
"""Paso 01: del crudo al dataset de entrenamiento (~15 s).

Calcula clase_ternaria con la definición de la notebook z101 de la cátedra, verifica los
conteos por mes y reordena las filas como en el entrenamiento original.
"""
import os
import sys

import numpy as np
import pandas as pd

import comun as cm

crudo = cm.ruta_crudo()
if not os.path.exists(crudo):
    sys.exit(f'No encuentro el crudo en {crudo} (ver README).')

# [Anotación · líneas 18–24] Lee el CSV con las 152 variables de la lista en float32. Verifica que
#   numero_de_cliente sea igual a su conversión a entero, lo pasa a int64 y verifica que no haya filas repetidas
#   por (numero_de_cliente, foto_mes).
# float32: es la precisión con la que se entrenaron los modelos de la entrega.
df = pd.read_csv(crudo, dtype={c: 'float32' for c in cm.FEATURES})
# Algunos IDs vienen en notación científica y pandas los lee como float.
ids = df['numero_de_cliente']
assert (ids == ids.astype('int64')).all(), 'numero_de_cliente no es entero exacto'
df['numero_de_cliente'] = ids.astype('int64')
assert not df.duplicated(['numero_de_cliente', 'foto_mes']).any()

# [Anotación · líneas 26–38] Calcula clase_ternaria. Asigna a cada mes un índice consecutivo y arma el
#   conjunto de pares (cliente, índice). Para cada fila consulta si el cliente está en el índice siguiente y en
#   el subsiguiente: BAJA+1 si no está en el siguiente, BAJA+2 si está en el siguiente y no en el subsiguiente,
#   CONTINUA en otro caso. Deja en None todas las filas del último mes y, en el anteúltimo, las de clientes
#   presentes en el mes siguiente.
# clase_ternaria: BAJA+1 si el cliente no está en m+1, BAJA+2 si está en m+1 pero no en m+2.
meses = sorted(df['foto_mes'].unique())
mi = df['foto_mes'].map({m: i for i, m in enumerate(meses)}).tolist()
cli = df['numero_de_cliente'].tolist()
presentes = set(zip(cli, mi))
en_m1 = np.fromiter(((c, m + 1) in presentes for c, m in zip(cli, mi)), bool, len(df))
en_m2 = np.fromiter(((c, m + 2) in presentes for c, m in zip(cli, mi)), bool, len(df))
clase = np.where(~en_m1, 'BAJA+1', np.where(~en_m2, 'BAJA+2', 'CONTINUA')).astype(object)
# Sin m+1 (último mes) no hay clase; sin m+2 (anteúltimo) solo se puede afirmar BAJA+1.
mi = np.array(mi)
clase[mi == len(meses) - 1] = None
clase[(mi == len(meses) - 2) & en_m1] = None
df['clase_ternaria'] = clase

# [Anotación · líneas 40–46] Arma la tabla de conteos de clase_ternaria por foto_mes (incluidos los vacíos,
#   rotulados 'nan') y compara cada valor con conteo_clase_ternaria_esperado de entrega.json; ante una
#   diferencia el assert corta con el mes, la clase y los dos números.
# Si el crudo no es el de la cátedra, los conteos no coinciden y conviene cortar acá.
conteo = df.groupby('foto_mes')['clase_ternaria'].value_counts(dropna=False).unstack(fill_value=0)
conteo.columns = [str(c) if pd.notna(c) else 'nan' for c in conteo.columns]
for mes, esperado in cm.ENTREGA['conteo_clase_ternaria_esperado'].items():
    for clase_, n in esperado.items():
        obtenido = int(conteo.loc[int(mes), clase_]) if clase_ in conteo.columns else 0
        assert obtenido == n, f'clase_ternaria {mes} {clase_}: {obtenido} != {n}'

# [Anotación · líneas 48–52] Carga el arreglo 'orden' de config/orden_filas.npz, verifica que tenga el largo
#   del dataset y que no repita posiciones, y reordena las filas con él. El comentario indica que ese es el
#   orden del dataset usado en el entrenamiento original.
# El bagging del LightGBM y el bootstrap del RF eligen filas por posición: sin este orden
# (el del dataset con el que entrené) los modelos y el archivo final cambian.
orden = np.load(os.path.join(cm.CONFIG, 'orden_filas.npz'))['orden']
assert len(orden) == len(df) and len(np.unique(orden)) == len(df), 'orden_filas no corresponde a este crudo'
df = df.iloc[orden].reset_index(drop=True)

# [Anotación · líneas 54–56] Crea la carpeta trabajo/ si no existe, escribe el parquet con numero_de_cliente,
#   foto_mes, clase_ternaria y las 152 variables, e imprime la cantidad de filas.
os.makedirs(cm.TRABAJO, exist_ok=True)
df[['numero_de_cliente', 'foto_mes', 'clase_ternaria'] + cm.FEATURES].to_parquet(cm.DATASET, index=False)
print(f'{len(df):,} filas, clase_ternaria verificada -> {cm.DATASET}')
```

### entrega_github_baseline/src/02_entrenar_y_predecir.py

Paso 02: pasa ccajas_depositos a NA en 202105, arma la matriz de 760 columnas, entrena 10 LGBMClassifier con 202103-202106 y guarda sus probabilidades para 202108.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Docstring (10 LightGBM, uno por juego de hiperparámetros; el modelo i usa la
#   semilla i; cada modelo se guarda al terminar) e importaciones: os, time, numpy, pandas, LGBMClassifier y
#   comun.
"""Paso 02: entrena 10 LightGBM con 202103-202106 y predice 202108 (~80 min).

Un modelo por cada uno de los 10 mejores juegos de hiperparámetros de la bayesiana; el modelo i
usa la semilla i. Cada modelo se guarda apenas termina, así una corrida cortada retoma donde quedó.
"""
import os
from time import time

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier

import comun as cm

# [Anotación · líneas 15–19] Lee trabajo/competencia_01.parquet y, para cada variable de variables_en_na, pone
#   NaN en los meses indicados: ccajas_depositos en 202105.
df = pd.read_parquet(cm.DATASET)
# ccajas_depositos está toda en cero en 202105 (dato roto): se pasa a NA antes de armar los lags,
# así tampoco contamina el lag de 202106 ni el lag2 de 202107.
for var, meses in cm.ENTREGA['variables_en_na'].items():
    df.loc[df['foto_mes'].isin(meses), var] = np.nan
# [Anotación · líneas 20–26] Marca las filas de entrenamiento (foto_mes en 202103-202106) y las de predicción
#   (202108), arma la matriz de 760 columnas para la unión de ambas y la separa en X_train y X_pred según el
#   mes. Según el comentario, los lags de 202108 toman valores de 202107 y 202106.
es_train = df['foto_mes'].isin(cm.MESES_TRAIN).to_numpy()
es_pred = (df['foto_mes'] == cm.MES_PRED).to_numpy()
# Los lags de 202108 usan 202107 y 202106: esos meses no tienen target, pero sus variables sí se conocen.
X = cm.matriz(df, es_train | es_pred)
mes = df.loc[es_train | es_pred, 'foto_mes'].to_numpy()
X_train, X_pred = X[mes != cm.MES_PRED], X[mes == cm.MES_PRED]
del X
# [Anotación · líneas 27–30] Construye el vector objetivo: 1 si clase_ternaria está en lgbm_target_positivos
#   (BAJA+1, BAJA+2) y 0 en otro caso, sobre todas las filas de entrenamiento. Imprime la cantidad de filas y
#   columnas de X_train.
# Sin undersampling. BAJA+1 como positivo duplica los casos de fuga para aprender; la ganancia
# se mide igual solo con BAJA+2.
y = np.isin(df.loc[es_train, 'clase_ternaria'].to_numpy(), cm.ENTREGA['lgbm_target_positivos']).astype(int)
print(f'train {X_train.shape[0]:,} filas x {X_train.shape[1]} columnas', flush=True)

# [Anotación · líneas 32–42] Si existe trabajo/probabilidades_202108.npz carga su contenido. Recorre en
#   paralelo los 10 juegos y las 10 semillas: saltea los modelos cuya clave m<i> ya está guardada; para el resto
#   crea un LGBMClassifier con los parámetros fijos, el juego i y random_state igual a la semilla i, lo entrena,
#   guarda la probabilidad de la clase positiva sobre X_pred, reescribe el archivo npz e imprime los segundos
#   que tardó.
probas = dict(np.load(cm.PROBAS)) if os.path.exists(cm.PROBAS) else {}
probas['numero_de_cliente'] = df.loc[es_pred, 'numero_de_cliente'].to_numpy()
for i, (juego, s) in enumerate(zip(cm.JUEGOS, cm.SEMILLAS)):
    if f'm{i}' in probas:
        continue
    t0 = time()
    m = LGBMClassifier(**cm.LGBM_FIJOS, **juego, random_state=s)
    m.fit(X_train, y)
    probas[f'm{i}'] = m.predict_proba(X_pred)[:, 1]
    np.savez(cm.PROBAS, **probas)
    print(f'modelo {i} {juego} semilla {s}: {time() - t0:.0f}s', flush=True)
```

### entrega_github_baseline/src/03_generar_submit.py

Paso 03: promedia las probabilidades de los 10 modelos, elige los 11.000 clientes de mayor promedio y escribe el archivo de envío y la predicción completa de 202108.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Carga trabajo/probabilidades_202108.npz y verifica con un assert que estén las
#   claves m0 a m9; toma el vector de numero_de_cliente y su largo.
"""Paso 03: promedio de los 10 modelos y archivo para el bot (segundos)."""
import os

import numpy as np

import comun as cm

pr = np.load(cm.PROBAS)
faltan = [f'm{i}' for i in range(len(cm.JUEGOS)) if f'm{i}' not in pr]
assert not faltan, f'faltan modelos del paso 02: {faltan}'
ids = pr['numero_de_cliente']
n = len(ids)

# [Anotación · líneas 14–18] Calcula la media de las 10 probabilidades por cliente, ordena de mayor a menor
#   con argsort estable (los empates conservan el orden de las filas) y toma los primeros N_ENVIOS = 11.000
#   índices.
# Los 10 modelos estiman lo mismo (P(BAJA+1 o BAJA+2)) con el mismo target: se promedian probabilidades.
p = np.mean([pr[f'm{i}'] for i in range(len(cm.JUEGOS))], axis=0)
# Orden estable: los empates se resuelven siempre igual y el archivo es reproducible.
orden = np.argsort(-p, kind='stable')
elegidos = orden[:cm.N_ENVIOS]

# [Anotación · líneas 20–30] Crea salida/ si no existe. Escribe el archivo de envío en ASCII con un ID entero
#   por línea y salto de línea '\n', sin encabezado. Escribe además prediccion_completa_202108.csv con
#   encabezado 'numero_de_cliente,Predicted' y un 1 para los elegidos y un 0 para el resto. Imprime cuántos
#   clientes se eligieron sobre el total.
os.makedirs(cm.SALIDA, exist_ok=True)
with open(cm.SUBMIT, 'w', encoding='ascii', newline='') as f:
    for v in ids[elegidos]:
        f.write(f'{int(v)}\n')
pred = np.zeros(n, dtype=int)
pred[elegidos] = 1
with open(cm.PREDICCION, 'w', encoding='ascii', newline='') as f:
    f.write('numero_de_cliente,Predicted\n')
    for v, q in zip(ids, pred):
        f.write(f'{int(v)},{int(q)}\n')
print(f'{cm.N_ENVIOS:,} de {n:,} clientes -> {cm.SUBMIT}')
```

### entrega_github_baseline/src/comun.py

Módulo compartido por los pasos 01 a 04: rutas, lectura de los JSON de config/ y las funciones lag y matriz que arman las columnas del modelo.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–19] Docstring e importaciones (argparse, json, os, numpy). Define RAIZ como la carpeta
#   que contiene a src/ y, a partir de ella, las carpetas config/, trabajo/ y salida/ y tres rutas de archivo:
#   trabajo/competencia_01.parquet (DATASET), trabajo/probabilidades_202108.npz (PROBAS) y
#   salida/prediccion_completa_202108.csv (PREDICCION).
"""Configuración y funciones compartidas por los pasos 01-04.

Todo lo que define el modelo sale de config/, no del código: parámetros fijos y los 10 juegos de
hiperparámetros de la búsqueda bayesiana, lista de variables, semillas, meses, cantidad de envíos
y hash esperado.
"""
import argparse
import json
import os

import numpy as np

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
CONFIG = os.path.join(RAIZ, 'config')
TRABAJO = os.path.join(RAIZ, 'trabajo')
SALIDA = os.path.join(RAIZ, 'salida')
DATASET = os.path.join(TRABAJO, 'competencia_01.parquet')
PROBAS = os.path.join(TRABAJO, 'probabilidades_202108.npz')
PREDICCION = os.path.join(SALIDA, 'prediccion_completa_202108.csv')


# [Anotación · líneas 22–35] Define leer_json, que abre un archivo de config/ en UTF-8. Carga entrega.json y
#   la lista 'features' de features_crudas.json y expone como constantes las semillas, los meses de
#   entrenamiento, el mes a predecir, la cantidad de envíos y los órdenes de lag y delta. SUBMIT es
#   salida/<archivo_submit> y REFERENCIA es referencia/<archivo_submit>.
def leer_json(nombre):
    with open(os.path.join(CONFIG, nombre), encoding='utf-8') as f:
        return json.load(f)


ENTREGA = leer_json('entrega.json')
FEATURES = leer_json('features_crudas.json')['features']
SEMILLAS = ENTREGA['semillas']
MESES_TRAIN = ENTREGA['meses_entrenamiento']
MES_PRED = ENTREGA['mes_a_predecir']
N_ENVIOS = ENTREGA['n_envios']
ORDENES = ENTREGA['ordenes_lag_y_delta']
SUBMIT = os.path.join(SALIDA, ENTREGA['archivo_submit'])
REFERENCIA = os.path.join(RAIZ, 'referencia', ENTREGA['archivo_submit'])

# [Anotación · líneas 37–41] Carga hiperparametros_baseline.json. LGBM_FIJOS son los params_fijos. JUEGOS es
#   una lista con un diccionario por cada entrada de top10, en el orden del archivo, que renombra num_iterations
#   como n_estimators y conserva num_leaves y min_sum_hessian_in_leaf.
_HIP = leer_json('hiperparametros_baseline.json')
LGBM_FIJOS = _HIP['params_fijos']
# Un juego por modelo, en el orden de la bayesiana (mejor AUC primero).
JUEGOS = [dict(n_estimators=j['num_iterations'], num_leaves=j['num_leaves'],
               min_sum_hessian_in_leaf=j['min_sum_hessian_in_leaf']) for j in _HIP['top10']]


# [Anotación · líneas 44–48] ruta_crudo: lee el argumento --crudo; si no se pasa, toma la variable de entorno
#   DMEYF_CRUDO y, si tampoco existe, datos/competencia_01_crudo.csv dentro del paquete.
def ruta_crudo():
    ap = argparse.ArgumentParser()
    ap.add_argument('--crudo', default=os.environ.get(
        'DMEYF_CRUDO', os.path.join(RAIZ, 'datos', 'competencia_01_crudo.csv')))
    return ap.parse_args().crudo


# [Anotación · líneas 51–67] lag: ordena las filas por cliente y mes. Para cada desplazamiento j de 1 a k
#   marca las filas cuya fila j posiciones antes es del mismo cliente y tiene un índice de mes exactamente k
#   menor, y les copia ese valor; las demás quedan en NaN. Devuelve el resultado en float32 y en el orden
#   original de las filas.
def lag(clientes, mes_idx, v, k):
    """Valor de k meses antes del mismo cliente, o NaN.
    Se exige que la fila buscada sea exactamente mes_idx - k: si el cliente faltó un mes, no
    debe heredar el valor de otro mes. Con los datos ordenados por cliente y mes, esa fila está
    a lo sumo k posiciones atrás."""
    orden = np.lexsort((mes_idx, clientes))
    cli, mi, vs = clientes[orden], mes_idx[orden], np.asarray(v)[orden]
    res = np.full(len(vs), np.nan, dtype='float32')
    for j in range(1, k + 1):
        hay = np.zeros(len(vs), dtype=bool)
        hay[j:] = (cli[j:] == cli[:-j]) & (mi[j:] - mi[:-j] == k)
        previo = np.zeros(len(vs), dtype=bool)
        previo[:-j] = hay[j:]
        res[hay] = vs[previo]
    out = np.empty_like(res)
    out[orden] = res
    return out


# [Anotación · líneas 70–86] matriz: numera los meses presentes de menor a mayor y arma, para las filas
#   pedidas, una matriz float32 de nf × (1 + 2 × no) columnas (152 × 5 = 760 con la configuración de la
#   entrega). Las primeras 152 son las variables originales; siguen, por variable, sus lags de orden 1 y 2; al
#   final, por variable, sus deltas (valor menos lag) de orden 1 y 2. El lag se calcula sobre todas las filas
#   del dataset y recién después se filtran las pedidas.
def matriz(df, filas):
    """Columnas del LightGBM, en este orden: las 152 crudas; para cada cruda sus lags de orden
    1 y 2; para cada cruda sus deltas (valor - lag) de orden 1 y 2. Total 760.
    float32 en todo el armado para que los valores sean idénticos a los del entrenamiento original."""
    meses = sorted(df['foto_mes'].unique())
    mi = df['foto_mes'].map({m: i for i, m in enumerate(meses)}).to_numpy()
    cli = df['numero_de_cliente'].to_numpy()
    nf, no = len(FEATURES), len(ORDENES)
    X = np.empty((int(filas.sum()), nf * (1 + 2 * no)), dtype='float32')
    for j, f in enumerate(FEATURES):
        v = df[f].to_numpy()
        X[:, j] = v[filas]
        for i, k in enumerate(ORDENES):
            lk = lag(cli, mi, v, k)
            X[:, nf + j * no + i] = lk[filas]
            X[:, nf * (1 + no) + j * no + i] = (v - lk)[filas]
    return X
```


## Explicaciones del alumno (texto original)

### entrega_github_baseline/README.md

> # DMEyF 2026 - Primera Competencia: entrega final
>
> **Entrega final:** `base_k11000.csv`, 11.000 clientes de 202108 a los que mando estímulo. Ganancia en el Public Leaderboard: **108,57**.
>
> **El archivo de mi entrega final está en `referencia/base_k11000.csv`**: es el mismo que mandé al bot. Este paquete lo reproduce exactamente desde el crudo, y el último paso compara los hashes para comprobarlo.
>
> sha256: `6d2f0f0419890ec7087bffef0e03fc1d0499af349dce67eaa844bcce79fa3712`
>
> ## El problema
>
> Elegir a qué clientes mandarles un estímulo en 202108 para retener a los que se van en dos meses (BAJA+2). Cada BAJA+2 acertado gana 1.072.500 y cada estímulo cuesta 27.500. Con esa asimetría el punto de equilibrio es una probabilidad de 2,5%, así que no se trata de clasificar bien sino de **ordenar bien y cortar en el lugar justo**.
>
> ## El modelo final
>
> Es el baseline que el profesor dejó en el tópico "En Limpio":
>
> - **Datos:** 152 variables originales más lags y deltas de orden 1 y 2 (760 columnas). `ccajas_depositos` viene toda en cero en 202105 (dato roto), así que la paso a NA en ese mes antes de calcular los lags.
> - **Target:** BAJA+1 y BAJA+2 como positivos. La ganancia se mide solo con BAJA+2.
> - **LightGBM** sin undersampling, con `max_bin` 31, `min_data_in_leaf` 0, `feature_fraction` 0,5, `feature_fraction_bynode` 0,2 y `learning_rate` 0,005.
> - **Optimización bayesiana** (30 trials) de `num_iterations`, `num_leaves` y `min_sum_hessian_in_leaf`, entrenando con 202103-202104 y midiendo AUC en 202106. El mejor trial: 1.650 iteraciones, 63 hojas y `min_sum_hessian_in_leaf` 11,6.
> - **Ensamble:** 10 LightGBM, uno por cada uno de los 10 mejores juegos de hiperparámetros, entrenados con 202103-202106. Promedio sus probabilidades.
> - **Corte:** 11.000 envíos.
>
> ## Cómo llegué hasta acá
>
> ### 1. Primeros modelos y validación
>
> Arranqué con un Random Forest y un LightGBM optimizados con Optuna. Lo primero que corregí fue la validación: el mismo cliente aparece en varios meses, así que partir filas al azar filtra información. Pasé a una **validación temporal en tres ventanas** (202104, 202105 y 202106), entrenando siempre con meses anteriores, midiendo la ganancia al mismo porcentaje de envíos y repitiendo cada variante con varias semillas. El ruido entre semillas resultó de unos 4M, así que solo consideré mejoras de al menos 6M.
>
> | Entrega | Public |
> |---|---|
> | Random Forest | 85,36 |
> | LightGBM | 88,03 |
> | Blend RF + LightGBM por ranking | 90,39 |
>
> ### 2. Target y variables históricas
>
> Los dos cambios que más aportaron en validación fueron usar **BAJA+1 y BAJA+2 como positivos** (+18,2M) y agregar **lags y deltas de orden 1** (+26,4M combinados). Con eso el blend llegó a **97,00**, y ajustando el corte a 10.000 envíos, a **99,41**.
>
> ### 3. Lo que aprendí de los datos
>
> - **202106 es atípico:** es el mes del aguinaldo (`mpayroll` +47%). Muchas variantes que mejoraban 202104 y 202105 empeoraban 202106.
> - **No hay variables rotas en 202108** (PSI < 0,12), pero `Visa_fultimo_cierre` y `Master_fultimo_cierre` identifican el mes (AUC adversarial 0,9998). Sacarlas no cambió la ganancia.
> - **La curva de ganancia es plana** entre 9.500 y 11.000 envíos. Por eso el corte importa poco dentro de ese rango.
>
> ### 4. Más de 100 variantes sin mejora
>
> Probé objetivos de ranking (lambdarank, rank_xendcg), selección de variables, LightGBM dart, regresión logística, XGBoost, ExtraTrees, variables de historia, variables de tarjetas, pesos por mes, corte por probabilidad calibrada y usar 202107 con etiqueta parcial. Ninguna pasó el umbral de validación. También mandé 16 variantes al Public Leaderboard y ninguna superó al blend.
>
> Una hipótesis que vale la pena contar: como 202106 tiene aguinaldo y 202108 no, probé variantes que ganaban en 202104/05 aunque perdieran en 202106. Todas dieron peor en el público (entre 92,8 y 96,3). También probé el peso de 202106 en el entrenamiento: 0 dio 95,65, 0,5 dio 94,02, 2 dio 96,31 y 3 dio 95,23. El óptimo era el peso normal. **202106, el mes más reciente, era el que mejor representaba a 202108.**
>
> ### 5. El baseline del profesor
>
> El profesor mostró que elegir por el Public Leaderboard es peligroso: un público alto no garantiza superar la línea de 300 en el privado. Recomendó construir el baseline de "En Limpio" como base segura. Lo implementé y dio **106,8, 107,0 y 108,6** con 10.000, 10.500 y 11.000 envíos: alto en los tres cortes, no un pico aislado. Elegí 11.000.
>
> ## Por qué mi validación no lo anticipaba
>
> En mi ventana de 202106 el baseline rendía 26M menos que el blend, y en el público rindió 9 puntos más. La explicación más probable es que **los hiperparámetros del blend se habían optimizado mirando 202106**, así que esa ventana era optimista para el blend. La diferencia clave del baseline con mis intentos parecidos está en **árboles chicos y muy regularizados** (63 hojas, `min_sum_hessian_in_leaf` alto) y en la **diversidad de 10 configuraciones distintas**, en lugar de 10 semillas de una sola.
>
> ## Cómo correrlo
>
> **1. Bajar el crudo**, que no está en el repo:
>
> https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv
>
> Dejarlo en `datos/competencia_01_crudo.csv`, o indicar la ruta con `--crudo`.
>
> **2. Instalar las dependencias** (Python 3.11.6, Windows 11):
>
> ```
> pip install -r requirements_minimos.txt
> ```
>
> **3. Correr:**
>
> ```
> python correr_todo.py --crudo RUTA/competencia_01_crudo.csv
> ```
>
> Tarda entre 80 y 90 minutos con 16 núcleos. No vuelve a correr la bayesiana: los 10 juegos de hiperparámetros están en `config/hiperparametros_baseline.json`.
>
> | Paso | Qué hace |
> |---|---|
> | `src/01_preparar_datos.py` | Lee el crudo, calcula `clase_ternaria` y deja las filas en el orden con el que entrené. |
> | `src/02_entrenar_y_predecir.py` | Arregla `ccajas_depositos`, arma las 760 columnas, entrena los 10 modelos y predice 202108. |
> | `src/03_generar_submit.py` | Promedia las probabilidades y escribe los 11.000 clientes. |
> | `src/04_verificar.py` | Chequea el formato y compara el hash con el archivo entregado (`referencia/base_k11000.csv`). |
>
> ## Limitaciones
>
> - El corte de 11.000 lo elegí mirando el público, que es solo el 25% de 202108.
> - "En Limpio" no detallaba el target, los rangos de búsqueda ni la validación de la bayesiana. Esas decisiones son mías.
> - La reproducción exacta depende del orden de filas (`config/orden_filas.npz`), de las versiones de las librerías y de la cantidad de núcleos.
>
> ## Herramientas
>
> Usé Claude como asistente para escribir código y explorar variantes. Las decisiones de validación y la elección de la entrega final son mías.
>
> ## Verificación
>
> Corrida desde cero en 88 minutos:
>
> ```
> sha256 generado: 6d2f0f0419890ec7087bffef0e03fc1d0499af349dce67eaa844bcce79fa3712
> sha256 esperado: 6d2f0f0419890ec7087bffef0e03fc1d0499af349dce67eaa844bcce79fa3712
> ```

