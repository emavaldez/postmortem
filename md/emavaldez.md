# emavaldez — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: emavaldez
- Repositorio: https://github.com/emavaldez/primeracompetencia
- Link posteado: https://github.com/emavaldez/primeracompetencia
- Commit: ec1fa7569b19bddcbbe7f0d721526fd544665fce
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/emavaldez/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/emavaldez.json

## Resumen

La entrega contiene un README, la lista entregada (TipsAleBolanoFE_final.csv, 11.250 clientes) y la carpeta codigo/ con tres archivos de Python, un requirements.txt y un JSON de huellas sha256. reproducir.py lee el dataset crudo, arma clase_ternaria, genera las variables y corre el modelo una vez por cada una de 25 semillas; promedia las probabilidades y escribe los 11.250 clientes de mayor probabilidad de 202108. El modelo de cada semilla tiene tres piezas con LightGBM: un modelo general de tres clases entrenado con 202104 a 202106 (submuestreo 0,2 de CONTINUA, BAJA+1 con peso 0,5); un modelo binario para los clientes con internet >= 1 entrenado con 202106, que elige sus variables con canaritos y se combina con el general; y una segunda etapa de 4 hojas y 100 rondas que reordena los puestos 8.000 a 30.000 de los clientes con internet = 0, entrenada con esas franjas de 202105 y 202106 puntuadas por un modelo entrenado con 202103 y 202104. Las variables incluyen lags y deltas de orden 1 y 2, razones, promedio, mínimo, máximo y tendencia de una ventana de 3 meses, percentil dentro del mes con cero fijo para 14 montos y una variable pasada a NA en 202105. Los hiperparámetros están escritos en el código. El README declara que todo el código lo escribió un agente de IA.

**Qué entrega.** TipsAleBolanoFE_final.csv: 11.250 numero_de_cliente, uno por línea y sin encabezado (los de mayor probabilidad promedio para 202108). El archivo está en la raíz del repositorio y reproducir.py lo vuelve a escribir en codigo/salida/.

**Cómo se ejecuta.** Según el README: ubicar el dataset crudo en ~/competencia_01_crudo.csv (declara su tamaño, 492.769.580 bytes, y su sha256), crear un entorno virtual con Python 3.12 o posterior y ejecutar `cd codigo`, `pip install -r requirements.txt` y `python reproducir.py`. Con `python reproducir.py --prueba` corre sólo la primera semilla. En macOS indica instalar libomp con Homebrew. Para rehacer todo desde cero indica borrar codigo/salida/. El README declara unos 20 minutos de corrida y unos 21 GB de memoria en la máquina que describe. La ruta del dataset es relativa a la carpeta personal de quien ejecuta; las demás rutas son relativas a la carpeta del script.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** prepare.py arma clase_ternaria según la presencia del cliente en los dos meses siguientes. Modelo general: tres clases (CONTINUA = 0, BAJA+1 = 1, BAJA+2 = 2) y la probabilidad que se usa es P(BAJA+1) + P(BAJA+2). Especialista de deudores: binaria, positivo = BAJA+1 o BAJA+2. Segunda etapa: binaria, BAJA+2 contra CONTINUA, sin las filas BAJA+1.
- **Meses de entrenamiento:** 202104, 202105, 202106
- **Meses de validación:** —
- **Mes que predice:** 202108
- **Submuestreo:** En el modelo general se conserva el 20% de las filas CONTINUA (UNDERSAMPLING = 0,2), sorteadas con un generador sembrado con la semilla de la corrida, y todas las BAJA+1 y BAJA+2. El especialista de deudores se entrena sin submuestreo y su probabilidad se transforma con p / (p + 0,2 (1 − p)). La segunda etapa no submuestrea.
- **Calidad de datos:** ccajas_depositos se pasa a NA en 202105 (tabla ROTAS) antes de calcular lags y deltas. prepare.py exige con un assert que la cantidad de BAJA+2 por mes coincida con una tabla escrita en el código (202103: 960, 202104: 1139, 202105: 870, 202106: 1098).
- **Drifting:** 14 montos (lista PERCENTIL_CERO_FIJO) se reemplazan por su percentil dentro del mes en escala −100 a 100, con positivos y negativos ordenados por separado y el cero en 0; sus lags y deltas se calculan sobre el percentil. A Visa_fultimo_cierre y Master_fultimo_cierre se les resta la moda del mes. Las cinco columnas de internet (cruda, 2 lags, 2 deltas) se ponen en 0 en los meses de entrenamiento anteriores al último. Los lags, deltas, razones y ventanas de las variables Visa_* y Master_* no entran a los modelos.
- **Variables dentro del mes:** No se observa en el código: no se crean variables nuevas por combinación de variables del mismo mes. Las transformaciones dentro del mes (percentil de 14 montos y resta de la moda en dos fechas) reemplazan a la variable original.
- **Variables históricas:** Para todas las columnas salvo numero_de_cliente y foto_mes: lag 1, lag 2, delta 1 y delta 2 por cliente. Para las variables de monto o conteo (nombre que empieza con m o c, con o sin prefijo Visa_/Master_, menos 6 excepciones): razón contra el lag 1, promedio, mínimo y máximo de la ventana de 3 meses (mes actual, lag 1 y lag 2) y razón contra el promedio y contra el máximo. Para las variables con lag que no son Visa_*, Master_* ni internet: pendiente por cuadrados mínimos de los tres valores (_tend3) y, donde no existe _avg3, el promedio de la ventana (_avg3p).
- **Selección de variables:** El especialista de deudores elige sus variables durante la corrida: agrega 50 columnas de números al azar (canaritos), entrena 5 veces con 200 rondas, promedia la importancia "gain" y conserva las variables cuya importancia media supera la del canarito de mayor importancia (mínimo 5). Según el README quedan 24 de 1.160 para 202106 y 20 de 1.160 para 202104. El modelo general usa todas las columnas menos clase_ternaria, numero_de_cliente y la historia de Visa_*/Master_*. La segunda etapa usa una lista de 25 variables escrita en el código (VARIABLES_2); el comentario indica que se eligió con canaritos y el código de esa selección no está en el repositorio.
- **Optimización de hiperparámetros:** No se observa en el código: los hiperparámetros están escritos como constantes.
- **Hiperparámetros finales:** General (multiclass, 3 clases): learning_rate 0,027, num_leaves 31, min_data_in_leaf 200, feature_fraction 0,5, max_bin 255, 500 rondas. Especialista (binary): learning_rate 0,03, num_leaves 15, min_data_in_leaf 50, feature_fraction 0,3, max_bin 255, 200 rondas. Segunda etapa (binary): learning_rate 0,03, num_leaves 4, min_data_in_leaf 200, feature_fraction 0,3, lambda_l2 20, max_bin 63, 100 rondas.
- **Semillas:** 25 semillas escritas en la lista SEMILLAS de reproducir.py (de 800029 a 801197). Cada una se usa para el sorteo del submuestreo y como seed de los tres LightGBM de esa corrida. El modelo que puntúa 202105 y 202106 para la segunda etapa usa la semilla 800011; la selección con canaritos usa seeds 9000 a 9004 y generadores cuya semilla depende del mes y de la repetición.
- **Cantidad de semillas:** 25
- **Ensamble:** Dentro de cada semilla: en los clientes con internet >= 1 se combinan el general y el especialista (los valores son el máximo de los dos, ordenado, y se asignan según la suma de los logit de ambos); después una segunda etapa reordena los puestos 8.000 a 30.000 de los clientes con internet = 0. Entre semillas: promedio de las probabilidades de las 25 corridas.
- **Corte:** Cantidad fija: los 11.250 clientes de mayor probabilidad promedio (CORTE = 11250), con orden estable ante empates. No se observa en el código cómo se eligió esa cantidad.
- **Validación:** No se observa en el código medición de ganancia ni partición de validación. Lo que hay: un assert que compara la cantidad de BAJA+2 por mes con una tabla de referencia; la comparación del sha256 de cada lista con esperado.json y el conteo de clientes en común con la lista incluida en el repositorio; y, en la segunda etapa, las probabilidades de 202105 y 202106 obtenidas con un modelo entrenado con 202103 y 202104, que se usan como entrada de entrenamiento y no como medición. Los comentarios citan mediciones (PSI, KS, tasas de baja por mes) cuyo cálculo no está en el repositorio.
- **Salidas:** En codigo/salida/: competencia_01.parquet (dataset con la clase), parcial/ids.npy y parcial/<semilla>.npy (probabilidades por semilla), semilla_<semilla>.csv (lista de cada semilla) y TipsAleBolanoFE_final.csv (lista final, un numero_de_cliente por línea, sin encabezado). Por pantalla: las variables elegidas por el especialista, el tiempo de cada semilla, el sha256 de la lista final y su comparación con esperado.json.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Tres clases (CONTINUA, BAJA+1, BAJA+2) (`clase.multiclase`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Estandarización o normalización por mes (`drifting.estandarizacion_por_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Mínimos y máximos de ventana (`variables.min_max_ventana`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Stacking (un modelo sobre las salidas de otros) (`ensamble.stacking`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El repositorio declara el uso de asistentes de IA (`proceso.uso_de_ia_declarado`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README y la cabecera de reproducir.py: MacBook Pro (Mac17,6), chip Apple M5 Max de 18 núcleos, 128 GB de memoria, macOS 27.0.1 (arm64); Python 3.14.4 (CPython), pip 26.2.1; LightGBM 4.7.0 (rueda de PyPI para macOS arm64, con libomp 23.1.2 de Homebrew), pandas 3.0.5, NumPy 2.5.2, PyArrow 25.0.1, SciPy 1.18.1 y narwhals 2.25.0. requirements.txt fija esas seis versiones de paquetes.

## Pasos del camino de la entrega

1. **Parámetros de la corrida.** reproducir.py fija el archivo de modelo, las 25 semillas y el corte de 11.250 clientes; lee las huellas de referencia y carga el módulo del modelo. (`codigo/reproducir.py` líneas 44–57)
2. **Lectura del dataset y armado de la clase.** prepare.py lee ~/competencia_01_crudo.csv, calcula clase_ternaria según la presencia de cada cliente en los dos meses siguientes, compara la cantidad de BAJA+2 de 202103 a 202106 con una tabla de referencia y guarda el resultado en parquet. Si el parquet ya existe, lo lee en lugar del CSV. (`codigo/prepare.py` líneas 18–21; `codigo/prepare.py` líneas 29–55)
3. **Separación en entrenamiento, mes a puntuar y mes intermedio.** _split3 toma los meses hasta 202108, calcula las variables sobre todas esas filas sin la columna de clase y devuelve train (202103 a 202106, con clase), score (202108) e intermedio (202107). (`codigo/prepare.py` líneas 58–71; `codigo/reproducir.py` líneas 64–67)
4. **Variable pasada a NA y tratamiento de deriva.** Antes de calcular la historia: ccajas_depositos pasa a NA en 202105; 14 montos se reemplazan por su percentil dentro del mes con cero fijo (escala −100 a 100); a Visa_fultimo_cierre y Master_fultimo_cierre se les resta la moda del mes. (`codigo/modelos/tips_ale_bolano_fe.py` líneas 59–59; `codigo/modelos/tips_ale_bolano_fe.py` líneas 73–77; `codigo/modelos/tips_ale_bolano_fe.py` líneas 82–82; `codigo/modelos/tips_ale_bolano_fe.py` líneas 85–94; `codigo/modelos/tips_ale_bolano_fe.py` líneas 100–105)
5. **Lags y deltas de orden 1 y 2.** Para todas las columnas salvo numero_de_cliente y foto_mes se calculan, por cliente, lag 1, lag 2, delta 1 y delta 2. (`codigo/modelos/tips_ale_bolano_fe.py` líneas 106–114)
6. **Ventana de 3 meses y razones.** Para las variables de monto y conteo se calculan promedio, mínimo y máximo de la ventana (mes actual, lag 1 y lag 2) y las razones del valor actual contra el lag 1, contra el promedio y contra el máximo. (`codigo/modelos/tips_ale_bolano_fe.py` líneas 35–48; `codigo/modelos/tips_ale_bolano_fe.py` líneas 117–145)
7. **Tendencia y promedio de 3 meses.** Para las variables con lag que no son Visa_*, Master_* ni internet se calcula la pendiente por cuadrados mínimos de los tres valores (_tend3) y, donde no existe _avg3, el promedio de la ventana (_avg3p). (`codigo/modelos/tips_ale_bolano_fe.py` líneas 156–174)
8. **Meses y columnas del modelo.** base() usa los últimos 3 meses con clase (202104, 202105 y 202106) y todas las columnas menos clase_ternaria, numero_de_cliente y los lags, deltas, razones y ventanas de las variables Visa_* y Master_*. (`codigo/modelos/tips_ale_bolano_fe.py` líneas 179–179; `codigo/modelos/tips_ale_bolano_fe.py` líneas 197–213; `codigo/modelos/tips_ale_bolano_fe.py` líneas 289–292)
9. **Especialista de deudores con canaritos.** Con los clientes de 202106 con internet >= 1 se seleccionan variables comparando su importancia "gain" con la de 50 canaritos (5 repeticiones) y se entrena un LightGBM binario (positivo = BAJA+1 o BAJA+2) de 200 rondas, sin submuestreo y sin las columnas _tend3 y _avg3p. Su probabilidad se transforma con p / (p + 0,2 (1 − p)). (`codigo/modelos/tips_ale_bolano_fe.py` líneas 223–284; `codigo/modelos/tips_ale_bolano_fe.py` líneas 295–295)
10. **Modelo general de tres clases.** Submuestreo de CONTINUA al 20%, peso 0,5 para las BAJA+1, columnas de internet en 0 en 202104 y 202105, y un LightGBM multiclass de 500 rondas. La probabilidad de cada cliente de 202108 es P(BAJA+1) + P(BAJA+2). (`codigo/modelos/tips_ale_bolano_fe.py` líneas 181–194; `codigo/modelos/tips_ale_bolano_fe.py` líneas 296–313)
11. **Combinación de general y especialista.** En los clientes con internet >= 1 del mes a puntuar, los valores finales son el máximo de las dos probabilidades, ordenados de mayor a menor, y se asignan a los clientes según la suma de los logit de los dos modelos. (`codigo/modelos/tips_ale_bolano_fe.py` líneas 314–347)
12. **Base fuera de muestra para 202105 y 202106.** Una vez por proceso se entrena base() con 202103 y 202104 (semilla 800011) y se puntúan 202105 y 202106, para tener probabilidades de esos meses sin haber usado su clase. (`codigo/modelos/tips_ale_bolano_fe.py` líneas 394–418)
13. **Segunda etapa sobre los puestos 8.000 a 30.000.** Con los clientes de internet = 0 ubicados entre los puestos 8.000 y 30.000 de 202105 y 202106 (sin las BAJA+1) se entrena un LightGBM binario de 4 hojas y 100 rondas, BAJA+2 contra CONTINUA, con 25 variables fijas y partiendo del logit calibrado de la base. En 202108 reordena esa misma franja: los valores de probabilidad son los mismos y cambia a qué cliente se asigna cada uno. (`codigo/modelos/tips_ale_bolano_fe.py` líneas 352–366; `codigo/modelos/tips_ale_bolano_fe.py` líneas 421–456)
14. **Una corrida por semilla.** Para cada una de las 25 semillas se llama a train_and_predict (base más segunda etapa) y se guardan las probabilidades en salida/parcial/<semilla>.npy; las semillas que ya tienen archivo no se recalculan. (`codigo/reproducir.py` líneas 61–75; `codigo/prepare.py` líneas 74–78; `codigo/modelos/tips_ale_bolano_fe.py` líneas 462–463)
15. **Promedio de semillas, corte y escritura de la lista.** Se promedian las probabilidades de las 25 semillas y se escriben los 11.250 numero_de_cliente de mayor promedio, uno por línea y sin encabezado, en salida/TipsAleBolanoFE_final.csv. También se escribe la lista de cada semilla por separado. (`codigo/reproducir.py` líneas 78–92)
16. **Comparación con las huellas de referencia.** Se compara el sha256 de cada lista con el de esperado.json y se cuenta cuántos clientes de la lista generada están en la lista incluida en la raíz del repositorio. (`codigo/reproducir.py` líneas 88–97; `codigo/esperado.json` líneas 1–30)

## Archivos

- `README.md` · explicacion · Markdown · 84 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/emavaldez/README.md.txt) — Presenta la entrega: qué archivos hay, el modelo en tres puntos, cómo reproducir la lista (ubicación, tamaño y sha256 del dataset, comandos, requisitos de Python y de memoria), las dos líneas que imprime la selección de variables del especialista, la máquina y las versiones usadas, y una declaración de que el código lo escribió un agente de IA (Claude Code).
- `codigo/reproducir.py` · principal · Python · 97 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/emavaldez/codigo/reproducir.py.txt) — Punto de entrada. Carga los datos y el modelo, corre el modelo una vez por cada una de las 25 semillas, promedia las probabilidades, escribe la lista de 11.250 clientes y compara su sha256 con el de referencia.
- `codigo/requirements.txt` · configuracion · Texto · 9 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/emavaldez/codigo/requirements.txt.txt) — Seis paquetes con versión exacta: lightgbm 4.7.0, pandas 3.0.5, numpy 2.5.2, pyarrow 25.0.1, narwhals 2.25.0 y scipy 1.18.1. Los comentarios indican Python 3.14.4 en macOS 27.0.1 (arm64) y que narwhals y scipy son dependencias de LightGBM.
- `codigo/esperado.json` · configuracion · JSON · 30 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/emavaldez/codigo/esperado.json.txt) — Huellas sha256 de referencia: una para la lista final (campo final) y una para la lista de cada una de las 25 semillas. reproducir.py las lee para informar si las listas generadas coinciden. El sha256 del archivo TipsAleBolanoFE_final.csv de la raíz del repositorio es igual al campo final.
- `codigo/prepare.py` · principal · Python · 78 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/emavaldez/codigo/prepare.py.txt) — Lee el CSV crudo, arma clase_ternaria, guarda el dataset en parquet y separa las filas en entrenamiento (meses con clase), mes a puntuar y meses intermedios. También contiene la función que llama al modelo.
- `codigo/modelos/tips_ale_bolano_fe.py` · principal · Python · 463 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/emavaldez/codigo/modelos/tips_ale_bolano_fe.py.txt) — Define las variables (make_features) y el modelo (train_and_predict): modelo general LightGBM de tres clases, especialista binario para clientes con internet >= 1 con selección de variables por canaritos, combinación de ambos y una segunda etapa que reordena los puestos 8.000 a 30.000 de los clientes con internet = 0.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### codigo/reproducir.py

Punto de entrada. Carga los datos y el modelo, corre el modelo una vez por cada una de las 25 semillas, promedia las probabilidades, escribe la lista de 11.250 clientes y compara su sha256 con el de referencia.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–30] Texto de cabecera: enumera los cuatro pasos de la corrida (leer el CSV y armar la
#   clase, armar las variables, entrenar y puntuar 202108 una vez por semilla, promediar y cortar), los archivos
#   que se escriben en salida/, las dos formas de uso (con y sin --prueba), la máquina y las versiones con que
#   se hizo, y la declaración de autoría del código por un agente de IA.
"""Reproduce, desde el dataset crudo, la lista de la entrega de la competencia 01 (DMEyF 2026): "Tips Ale Bolaño" con el FE
histórico de la cátedra.

De principio a fin:
  1. Lee ~/competencia_01_crudo.csv y arma clase_ternaria (prepare.py).
  2. Arma las variables (make_features, en modelos/tips_ale_bolano_fe.py).
  3. Entrena el modelo con la clase conocida hasta 202106 y puntúa 202108, una vez por cada semilla de SEMILLAS
     (train_and_predict, en el mismo archivo).
  4. Promedia las probabilidades de las semillas y escribe los CORTE clientes de mayor probabilidad.

Escribe en salida/:
  competencia_01.parquet       el dataset con la clase (para no volver a leer el CSV)
  parcial/<semilla>.npy        probabilidades de cada semilla; se guardan apenas terminan: si se corta, al relanzar sigue
  semilla_<semilla>.csv        la lista de cada semilla sola
  TipsAleBolanoFE_final.csv    la lista de la entrega
Al terminar compara el sha256 de cada archivo con el de referencia (esperado.json).

Uso:
  python reproducir.py            # la lista de la entrega
  python reproducir.py --prueba   # prueba rápida: sólo la primera semilla

Con qué se hizo (todo en una sola máquina, una Mac):
  MacBook Pro (Mac17,6), chip Apple M5 Max de 18 núcleos (6 + 12), 128 GB de memoria, macOS 27.0.1 (arm64).
  Python 3.14.4 (CPython) | LightGBM 4.7.0 (rueda de PyPI para macOS arm64, con libomp 23.1.2 de Homebrew) | pandas 3.0.5 |
  NumPy 2.5.2 | PyArrow 25.0.1 | SciPy 1.18.1 y narwhals 2.25.0 (dependencias de LightGBM) | pip 26.2.1.
  Las versiones exactas de las librerías están en requirements.txt. Las huellas de esperado.json salieron de esta máquina.

Autoría: Emmanuel Valdez no escribió ni tocó una sola línea de este código. Todo (la preparación de los datos, el modelo y
este script) lo hizo su agente de IA, Claude Code (Anthropic), siguiendo sus indicaciones.
"""
# [Anotación · líneas 31–42] Importa hashlib, importlib, json, sys, time, pathlib y numpy; agrega la carpeta
#   del propio script a sys.path e importa el módulo prepare.
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import numpy as np

import prepare

# [Anotación · líneas 44–49] Define el nombre del archivo de modelo (tips_ale_bolano_fe), la lista SEMILLAS
#   con 25 enteros entre 800029 y 801197, y CORTE = 11250, la cantidad de clientes de la lista.
MODELO = "tips_ale_bolano_fe"
SEMILLAS = [
    800029, 800083, 800119, 800131, 800209, 800221, 800333, 800357, 800419, 800441, 800477, 800497, 800509,
    800519, 800593, 800669, 800707, 800743, 800759, 800861, 800897, 800971, 800993, 801179, 801197,
]  # una corrida del modelo por semilla; la lista sale del promedio de todas
CORTE = 11250  # clientes de la lista

# [Anotación · líneas 51–57] Si se pasa --prueba usa sólo la primera semilla. Lee esperado.json y carga el
#   módulo modelos/tips_ale_bolano_fe.py por su ruta con importlib.
prueba = "--prueba" in sys.argv
seeds = SEMILLAS[:1] if prueba else SEMILLAS
esperado = json.loads((AQUI / "esperado.json").read_text())

spec = importlib.util.spec_from_file_location(f"modelo_{MODELO}", AQUI / "modelos" / f"{MODELO}.py")
modelo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modelo)

# [Anotación · líneas 59–73] Crea salida/parcial y determina qué semillas no tienen todavía su archivo .npy.
#   Si falta alguna: carga el dataset, llama a prepare._split3 con último mes con clase 202106 y mes a puntuar
#   202108 (ahí se calculan las variables con make_features), guarda los numero_de_cliente de 202108 en ids.npy
#   y, por cada semilla faltante, llama a train_and_predict, guarda las probabilidades en un archivo temporal
#   que después renombra a <semilla>.npy e imprime los segundos que tardó.
out = AQUI / "salida"
(out / "parcial").mkdir(parents=True, exist_ok=True)
faltan = [s for s in seeds if not (out / "parcial" / f"{s}.npy").exists()]
print(f"{len(seeds)} semillas, faltan {len(faltan)}; lista de {CORTE} clientes", flush=True)
if faltan:
    df = prepare.load_data()
    tr, sc, mid = prepare._split3(df, prepare.SUBMIT["last_label"], prepare.SUBMIT["score"], modelo.make_features)
    ids = sc.numero_de_cliente.to_numpy().astype("int64")
    np.save(out / "parcial" / "ids.npy", ids)
    for s in faltan:
        t = time.time()
        p = np.asarray(prepare.predecir(modelo.train_and_predict, tr, sc, s, mid), dtype=np.float64)
        np.save(out / "parcial" / f"{s}.tmp.npy", p)
        (out / "parcial" / f"{s}.tmp.npy").rename(out / "parcial" / f"{s}.npy")
        print(f"  semilla {s}: {time.time() - t:.0f}s", flush=True)
# [Anotación · líneas 74–75] Lee ids.npy y apila en una matriz las probabilidades guardadas de todas las
#   semillas de la corrida (una fila por semilla).
ids = np.load(out / "parcial" / "ids.npy")
probs = np.stack([np.load(out / "parcial" / f"{s}.npy") for s in seeds])


# [Anotación · líneas 78–85] lista(p) ordena de mayor a menor probabilidad con orden estable, toma los
#   primeros 11.250 numero_de_cliente y los devuelve como texto, uno por línea y sin encabezado. escribir(ruta,
#   texto) graba ese texto como bytes y devuelve su sha256.
def lista(p):
    """Los CORTE clientes de mayor probabilidad, uno por línea, sin encabezado (orden estable ante empates)."""
    return "\n".join(str(int(x)) for x in ids[np.argsort(-p, kind="stable")[:CORTE]]) + "\n"


def escribir(ruta, texto):
    ruta.write_bytes(texto.encode())  # bytes tal cual: en Windows write_text cambiaría los saltos de línea
    return hashlib.sha256(texto.encode()).hexdigest()


# [Anotación · líneas 88–97] Escribe semilla_<semilla>.csv con la lista de cada semilla y cuenta cuántas
#   tienen el mismo sha256 que figura en esperado.json. Sin --prueba, promedia las probabilidades de las 25
#   semillas, escribe salida/TipsAleBolanoFE_final.csv e imprime su sha256 y si coincide con el campo final de
#   esperado.json; si existe TipsAleBolanoFE_final.csv en la carpeta superior, imprime cuántos clientes tienen
#   en común las dos listas sin considerar el orden.
iguales = sum(escribir(out / f"semilla_{s}.csv", lista(p)) == esperado["semillas"].get(str(s)) for s, p in zip(seeds, probs))
print(f"listas por semilla: {len(seeds)} archivos en {out} | idénticas a las de referencia: {iguales} de {len(seeds)}")
if not prueba:
    h = escribir(out / "TipsAleBolanoFE_final.csv", lista(probs.mean(axis=0)))
    print(f"lista de la entrega: {out / 'TipsAleBolanoFE_final.csv'} (promedio de {len(seeds)} semillas, {CORTE} clientes)")
    print(f"  sha256 {h} | idéntica a la de referencia: {'sí' if h == esperado['final'] else 'NO'}")
    entregada = AQUI.parent / "TipsAleBolanoFE_final.csv"  # la lista entregada, al lado de codigo/
    if entregada.exists():  # el sha256 mira también el orden; esto cuenta los clientes en común sin mirarlo
        comun = set(entregada.read_text().split()) & set((out / "TipsAleBolanoFE_final.csv").read_text().split())
        print(f"  clientes en común con la lista entregada ({entregada.name}): {len(comun)} de {CORTE}")
```

### codigo/prepare.py

Lee el CSV crudo, arma clase_ternaria, guarda el dataset en parquet y separa las filas en entrenamiento (meses con clase), mes a puntuar y meses intermedios. También contiene la función que llama al modelo.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–10] Texto de cabecera: describe las funciones build_cache, _split3 y predecir, e
#   indica que make_features recibe sólo meses menores o iguales al mes a puntuar y sin la columna de clase.
"""
prepare.py — datos de la competencia 01 de DMEyF 2026: lee el dataset crudo, arma clase_ternaria y separa lo que se entrena
de lo que se puntúa.

  build_cache()  lee el CSV crudo, arma clase_ternaria con la receta de la cátedra (controla la cantidad de BAJA+2 de cada mes
                 contra la de la cátedra) y lo guarda en parquet, para no volver a leer el CSV en cada corrida.
  _split3()      devuelve train (los meses con clase, hasta 202106), score (202108) e intermedio (202107, sin clase).
  predecir()     llama al modelo.
make_features recibe SÓLO meses <= mes a puntuar y SIN la clase, así no hay fuga.
"""
# [Anotación · líneas 11–21] Importa inspect, os, pathlib, numpy y pandas. Define la ubicación del CSV crudo
#   (~/competencia_01_crudo.csv), la del parquet intermedio (salida/competencia_01.parquet, junto al script) y
#   SUBMIT: último mes con clase 202106 y mes a puntuar 202108.
import inspect
import os
from pathlib import Path

import numpy as np
import pandas as pd

CSV = Path(os.path.expanduser("~/competencia_01_crudo.csv"))
CACHE = Path(__file__).resolve().parent / "salida" / "competencia_01.parquet"

SUBMIT = {"last_label": 202106, "score": 202108}  # último mes con clase y mes que se puntúa


# [Anotación · líneas 24–26] _next_month devuelve el mes siguiente en formato AAAAMM (de diciembre pasa a
#   enero del año siguiente).
def _next_month(m):
    y, mm = divmod(int(m), 100)
    return (y + 1) * 100 + 1 if mm == 12 else m + 1


# [Anotación · líneas 29–44] build_cache lee el CSV con el motor pyarrow y arma el conjunto de pares (cliente,
#   mes) presentes. Para cada fila verifica si el cliente aparece en el mes siguiente y en el subsiguiente: si
#   no aparece en el siguiente, la clase es BAJA+1; si aparece en el siguiente y no en el subsiguiente, BAJA+2;
#   en otro caso, CONTINUA. En el anteúltimo mes del dataset sólo queda BAJA+1 para quienes no aparecen en el
#   último mes y el resto queda sin clase; el último mes queda sin clase.
def build_cache():
    df = pd.read_csv(CSV, engine="pyarrow")
    pres = df[["numero_de_cliente", "foto_mes"]]
    k = set(zip(pres.numero_de_cliente.to_numpy(), pres.foto_mes.to_numpy()))
    m1 = df.foto_mes.map(_next_month).to_numpy()
    m2 = pd.Series(m1).map(_next_month).to_numpy()
    ids = df.numero_de_cliente.to_numpy()
    in1 = np.fromiter(((c, m) in k for c, m in zip(ids, m1)), bool, len(df))
    in2 = np.fromiter(((c, m) in k for c, m in zip(ids, m2)), bool, len(df))
    last = df.foto_mes.max()
    anteultimo = sorted(df.foto_mes.unique())[-2]
    clase = np.where(~in1, "BAJA+1", np.where(~in2, "BAJA+2", "CONTINUA")).astype(object)
    clase[df.foto_mes.to_numpy() >= anteultimo] = None
    clase[(df.foto_mes.to_numpy() == anteultimo) & ~in1] = "BAJA+1"
    clase[df.foto_mes.to_numpy() == last] = None
    df["clase_ternaria"] = clase
# [Anotación · líneas 45–49] Cuenta las BAJA+2 por mes y, con un assert, exige que coincidan con una tabla
#   escrita en el código (202103: 960, 202104: 1139, 202105: 870, 202106: 1098). Crea la carpeta salida/ y
#   guarda el dataset con clase_ternaria en parquet.
    ref = {202103: 960, 202104: 1139, 202105: 870, 202106: 1098}
    got = df[df.clase_ternaria == "BAJA+2"].foto_mes.value_counts().to_dict()
    assert all(got.get(m) == n for m, n in ref.items()), f"clase_ternaria no coincide con la cátedra: {got}"
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE)


# [Anotación · líneas 52–55] load_data llama a build_cache si el parquet no existe y devuelve el contenido del
#   parquet.
def load_data():
    if not CACHE.exists():
        build_cache()
    return pd.read_parquet(CACHE)


# [Anotación · líneas 58–71] _split3 se queda con las filas de meses hasta el mes a puntuar, conserva la clase
#   sólo hasta el último mes con clase y llama a make_features sobre esas filas sin la columna clase_ternaria;
#   un assert exige que el resultado tenga el mismo índice que la entrada. Devuelve tres tablas: train (filas
#   con clase, con clase_ternaria agregada), score (filas del mes a puntuar) e intermedio (meses entre el último
#   con clase y el que se puntúa; 202107 en esta entrega).
def _split3(df, last_label, score_month, make_features):
    visible = df[df.foto_mes <= score_month]
    clase = visible.clase_ternaria.where(visible.foto_mes <= last_label)
    feats = make_features(visible.drop(columns=["clase_ternaria"]).copy())
    assert feats.index.equals(visible.index), "make_features debe devolver una fila por fila de entrada, mismo índice y orden"
    feats = feats.reset_index(drop=True)
    clase = clase.reset_index(drop=True)
    train = feats[clase.notna().to_numpy()].copy()
    train["clase_ternaria"] = clase[clase.notna()].to_numpy()
    score = feats[(feats.foto_mes == score_month).to_numpy()].copy()
    # meses SIN clase entre el último etiquetado y el que se puntúa (202107 al predecir 202108). No traen clase; el modelo
    # de esta entrega los recibe y no los usa (202107 sólo entra como historia de las filas de 202108: lags, deltas y ventana).
    intermedio = feats[((feats.foto_mes > last_label) & (feats.foto_mes < score_month)).to_numpy()].copy()
    return train, score, intermedio


# [Anotación · líneas 74–78] predecir inspecciona la cantidad de parámetros de train_and_predict: si acepta
#   cuatro o más le pasa también la tabla de meses intermedios; si no, sólo train, score y semilla. Devuelve el
#   resultado como arreglo de numpy.
def predecir(train_and_predict, train, score, seed, intermedio):
    """Llama a train_and_predict; si acepta un 4º argumento, le pasa los meses intermedios sin clase."""
    if len(inspect.signature(train_and_predict).parameters) >= 4:
        return np.asarray(train_and_predict(train, score, seed, intermedio))
    return np.asarray(train_and_predict(train, score, seed))
```

### codigo/modelos/tips_ale_bolano_fe.py

Define las variables (make_features) y el modelo (train_and_predict): modelo general LightGBM de tres clases, especialista binario para clientes con internet >= 1 con selección de variables por canaritos, combinación de ambos y una segunda etapa que reordena los puestos 8.000 a 30.000 de los clientes con internet = 0.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–26] Texto de cabecera: describe las tres piezas que se entrenan por semilla (modelo
#   general multiclase, especialista de deudores binario con selección por canaritos, y segunda etapa sobre los
#   puestos 8.000 a 30.000), indica que make_features y train_and_predict son la interfaz que usa reproducir.py
#   y que VARIABLES_2 es una lista fija.
"""
Tips Ale Bolaño: modelo de la competencia 01 (DMEyF 2026). Predice BAJA+2 de 202108.

Tres piezas, todas entrenadas con la clase conocida (hasta 202106). Hay dos grupos de
clientes definidos a mano (deudores = internet >= 1; franja dudosa = puestos 8.000 a 30.000 sin marca internet); lo que se
hace con cada uno lo aprende un modelo.

Por semilla:
  1. GENERAL: LightGBM multiclase (CONTINUA / BAJA+1 / BAJA+2) con los tres últimos meses con clase, submuestreo 0,2 de los
     CONTINUA, variables crudas + lags y deltas de 1 y 2 meses + razones y ventana de 3 meses, con sus tratamientos de deriva
     (ver los comentarios de cada bloque). Las BAJA+1 pesan la mitad al entrenar (PESO_BAJA1): la clase que paga es BAJA+2.
     Suma el FE histórico de la cátedra: tendencia y promedio de 3 meses (ver fe_historico_catedra).
  2. ESPECIALISTA DE DEUDORES: binario, sólo clientes con internet >= 1 del último mes con clase. Elige sus variables con
     canaritos (columnas de números al azar): quedan las que rinden más que el mejor canarito (24 de ~1.160). Se combina con el
     general por reparto: el nivel lo pone el máximo de los dos y el orden la suma de sus logit.
  3. SEGUNDA ETAPA: un LightGBM muy chico (4 hojas, 100 rondas, 25 variables) que aprende a corregir al modelo en la franja
     dudosa. Se entrena con los clientes sin marca internet que el modelo deja entre los puestos 8.000 y 30.000 en mayo y
     junio, puntuados por un modelo que NO vio la clase de esos meses, y después reordena esa misma franja del mes a puntuar.
     No cambia los valores de probabilidad: cambia a quién le toca cada uno.
     El modelo que puntúa mayo y junio se entrena una sola vez por corrida (no por semilla) con marzo y abril, que casi no
     tienen historia: es un modelo más pobre que el de la entrega (mayo le queda a un mes y junio a dos).
     VARIABLES_2 es una lista fija (no se recalcula en la corrida): se eligió con canaritos sobre las franjas de mayo y junio.

Se usa desde reproducir.py (make_features y train_and_predict son la interfaz); no se corre solo. train tiene que traer TODOS
los meses con clase desde el primero del dataset: con clase sólo hasta 202104 la segunda etapa no actúa.
"""
# [Anotación · líneas 27–48] Importa lightgbm, numpy y pandas. NO_MAGNITUD lista 6 variables que empiezan con
#   c y quedan fuera del grupo de magnitudes (cliente_edad, cliente_antiguedad, cliente_vip,
#   cdescubierto_preacordado, ccajas_transacciones, cmobile_app_trx). es_magnitud devuelve verdadero para las
#   variables cuyo nombre, quitado el prefijo Visa_ o Master_, empieza con m o con c y no está en esa lista.
import lightgbm as lgb
import numpy as np
import pandas as pd

# ---------------------------------------------------------------- features

# Empiezan con c pero no son conteos: edades (crecen solas: no llevan razones ni ventana; sí lags, deltas y el FE de la
# cátedra) y banderas 0/1.
NO_MAGNITUD = {
    "cliente_edad", "cliente_antiguedad",
    "cliente_vip", "cdescubierto_preacordado", "ccajas_transacciones", "cmobile_app_trx",
}


def es_magnitud(c: str) -> bool:
    """Montos (m*) y conteos (c*), del cliente o de sus tarjetas (Visa_m*, Master_c*): 128 de las 152 variables.

    Quedan afuera las fechas (F*, f*), las banderas y los códigos (t*, status, delinquency, internet, active_quarter):
    ahí una razón o un promedio no significan nada.
    """
    nombre = c.split("_", 1)[1] if c.startswith(("Visa_", "Master_")) else c
    return nombre[0] in "mc" and c not in NO_MAGNITUD


# [Anotación · líneas 51–54] razon divide dos arreglos y devuelve NaN donde el denominador es 0.
def razon(num, den):
    """num / den; con denominador 0 da NaN (nunca infinito)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den == 0, np.nan, num / den)


# [Anotación · líneas 57–59] ROTAS es la tabla de variables que se pasan a NA en meses puntuales:
#   ccajas_depositos en 202105.
# Data Quality (tips de la cátedra, 5-oct): una variable rota en un mes se pasa a NA sólo en ese mes, antes de lags y
# deltas. Tabla fija. ccajas_depositos está rota en 202105 (todos ceros).
ROTAS = {"ccajas_depositos": (202105,)}

# [Anotación · líneas 61–82] PERCENTIL_CERO_FIJO lista 14 montos que se reemplazan por su percentil dentro del
#   mes (entre ellos mcuentas_saldo, mpayroll, mcaja_ahorro, mrentabilidad y Visa_msaldototal). RESTAR_MODA
#   lista Visa_fultimo_cierre y Master_fultimo_cierre, a las que se les resta la moda del mes. Los comentarios
#   describen el criterio con que se armaron las listas (cambio de cuartiles entre 202103-05 y 202106-08,
#   importancia en el modelo y PSI); el cálculo de esa selección no está en el archivo.
# Data Drifting. Mirando las 152 variables mes a mes, la escala de estos montos se corre de un mes a
# otro: aguinaldo (202106: mpayroll x1,56; el saldo y la caja de ahorro quedan inflados en 202106-07, con el primer cuartil
# del saldo x5) e inflación en tarjeta, comisiones y transferencias (+15 a +55% en 202106-08 contra 202103-05). El modelo
# aprende con 202104-06 y agosto se puntúa con lags de junio y julio: un corte en pesos aprendido en abril no vale lo mismo
# en agosto, y "cayó respecto de junio" en agosto es la resaca del aguinaldo, no una fuga.
# Selección en dos pasos: (1) montos (m*) con algún cuartil de 202106-08 a más de 25% del promedio de 202103-05 y al menos
# 0,5% de la ganancia del modelo (la importancia "gain" de LightGBM); (2) de esos, sólo los que con el percentil quedan MÁS
# parecidos entre el entrenamiento (202104-06) y agosto (PSI de sus columnas, ponderado por esa ganancia: 0,057 -> 0,010
# en estos 14).
# Quedaron afuera los que el percentil empeora, que son los de pocos valores distintos o con muchos empates:
# cpayroll_trx (1, 2, 3: el percentil de "1" pasa de 30 a 15 en junio), mcomisiones_mantenimiento (lista de precios),
# mcaja_ahorro_dolares, Visa_mpagominimo, Visa_mpagospesos y mttarjeta_visa_debitos_automaticos. Los préstamos no derivan.
PERCENTIL_CERO_FIJO = [
    "mcuentas_saldo", "mpayroll", "mcaja_ahorro", "mpasivos_margen", "mtarjeta_visa_consumo", "mcuenta_corriente",
    "mtransferencias_recibidas", "mrentabilidad", "mcomisiones_otras", "mcomisiones", "Visa_msaldototal",
    "Visa_msaldopesos", "mautoservicio", "mtransferencias_emitidas",
]
# Corrimiento de calendario: son "días desde el último cierre" y el grupo mayoritario (69% de los clientes) vale
# 1 / 2 / 5 / 0 / 3 / 6 en 202103..08; el segundo grupo va 7 días atrás. Se le resta la moda del mes: queda el grupo de
# cierre del cliente (0, 7, ...), igual todos los meses. (El percentil no sirve acá: da 36,18 / 36,22 / 36,27... y esos
# decimales le dejan al árbol separar los meses.)
RESTAR_MODA = ["Visa_fultimo_cierre", "Master_fultimo_cierre"]


# [Anotación · líneas 85–94] percentil_cero_fijo calcula, dentro de cada mes, el percentil de los valores
#   positivos entre sí y el de los negativos entre sí. El resultado va de −100 a 100: los positivos en (0, 100],
#   los negativos en [−100, 0), el cero en 0 y los NA sin cambio.
def percentil_cero_fijo(x: pd.Series, mes: pd.Series) -> pd.Series:
    """Percentil (0 a 100) dentro del mes: usa sólo las filas de ese mes, así que no mira ni adelante ni atrás.

    Los positivos se ordenan entre sí (0, 100], los negativos entre sí [-100, 0) y el cero queda en 0: se conservan el signo
    y el "no tiene", que es lo que el ranking simple borra.
    La escala 0-100 es para que el redondeo a centavos de la ventana no le coma resolución.
    """
    pos = x.where(x > 0).groupby(mes).rank(pct=True)
    neg = (-x).where(x < 0).groupby(mes).rank(pct=True)
    return (100 * (pos.fillna(0) - neg.fillna(0))).where(x.notna())


# [Anotación · líneas 97–114] lags_y_deltas ordena por cliente y mes, pasa a NA las variables de ROTAS en sus
#   meses, aplica el percentil a las 14 variables de PERCENTIL_CERO_FIJO y resta la moda mensual a las dos de
#   RESTAR_MODA. Después, para todas las columnas salvo numero_de_cliente y foto_mes, obtiene con shift dentro
#   de cada cliente el valor de la fila anterior y el de dos filas atrás (lag1 y lag2) y la diferencia del valor
#   actual con cada uno (delta1 y delta2). Devuelve la tabla en el orden original de filas.
def lags_y_deltas(df: pd.DataFrame) -> pd.DataFrame:
    order = df.sort_values(["numero_de_cliente", "foto_mes"]).index
    df = df.loc[order]
    for c, meses in ROTAS.items():
        df[c] = df[c].where(~df.foto_mes.isin(meses))
    for c in PERCENTIL_CERO_FIJO:
        df[c] = percentil_cero_fijo(df[c], df.foto_mes)
    for c in RESTAR_MODA:
        df[c] = df[c] - df.groupby("foto_mes")[c].transform(lambda v: v.mode().iloc[0])
    base = [c for c in df.columns if c not in ("numero_de_cliente", "foto_mes")]
    g = df.groupby("numero_de_cliente")[base]
    new = {}
    for k in (1, 2):  # Feature Engineering histórico de la cátedra: lags y delta lags de orden 1 y 2
        lag = g.shift(k)
        new.update({f"{c}_lag{k}": lag[c] for c in base})
        new.update({f"{c}_delta{k}": df[c] - lag[c] for c in base})
    df = pd.concat([df, pd.DataFrame(new, index=df.index)], axis=1)
    return df.sort_index()


# [Anotación · líneas 117–132] historia recibe una variable con su lag1 y su lag2 y devuelve seis columnas:
#   razón contra el lag1 (ratiolag1), promedio de los valores disponibles de la ventana de 3 meses (avg3, con la
#   suma redondeada a 2 decimales), mínimo (min3), máximo (max3), razón contra el promedio (ratioavg3) y razón
#   contra el máximo (ratiomax3). Los NA de la ventana se saltean.
def historia(x, l1, l2):
    """FE histórico de la cátedra para una variable, sobre la ventana que dejan 6 meses de datos: el mes actual (x),
    lag1 y lag2, con los que haya."""
    v = np.stack([x, l1, l2])
    # los montos traen centavos: se redondea para que lo que da 0 sea 0 exacto y no un resto de punto flotante
    prom = razon(np.nansum(v, axis=0).round(2), (~np.isnan(v)).sum(axis=0))
    maxi = np.fmax.reduce(v)  # fmax y fmin saltean los NaN
    return {
        # razones sin escala: un árbol no las arma solo y no se corren con la inflación
        "ratiolag1": razon(x, l1),
        "ratioavg3": razon(x, prom),
        "avg3": prom,
        "min3": np.fmin.reduce(v),
        "max3": maxi,
        "ratiomax3": razon(x, maxi),
    }


# [Anotación · líneas 135–145] make_features identifica las variables de magnitud, llama a lags_y_deltas,
#   calcula las seis columnas de historia para cada magnitud guardándolas como float32 y pasa la tabla
#   resultante a fe_historico_catedra.
def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Recibe todas las filas de meses <= mes a puntuar (sin clase). Una fila de salida por fila de entrada."""
    magnitudes = [c for c in df.columns if es_magnitud(c)]
    df = lags_y_deltas(df)
    # Se calcula fila a fila a partir de los lags: sólo mira hacia atrás. Las columnas nuevas no llevan lag ni delta.
    # float32: son 768 columnas más sobre ~980.000 filas y al árbol le sobran 7 dígitos.
    hist = {}
    for c in magnitudes:
        for k, a in historia(*(df[n].to_numpy(float) for n in (c, f"{c}_lag1", f"{c}_lag2"))).items():
            hist[f"{c}_{k}"] = a.astype("float32")
    return fe_historico_catedra(pd.concat([df, pd.DataFrame(hist, index=df.index)], axis=1))


# [Anotación · líneas 148–174] fe_historico_catedra toma las columnas que tienen lag1 y lag2, excepto las
#   Visa_*, las Master_* e internet. Para cada una ajusta por cuadrados mínimos la pendiente de los valores
#   (lag2, lag1, actual) sobre las posiciones 1, 2 y 3 usando los valores disponibles (NA si hay menos de dos) y
#   la guarda como <variable>_tend3; el promedio de la ventana se guarda como <variable>_avg3p sólo si la
#   variable no tiene ya una columna _avg3.
# ---------------------------------------------------------------- FE histórico de la cátedra: tendencia y promedio de 3 meses
#
# Es lo que agregó la cátedra a su Feature Engineering Histórico (función TendenciaYmuchomas con ventana 3, tendencia y
# promedio): la pendiente por cuadrados mínimos de los últimos tres valores y su promedio, para todas las variables con lag.
# Con los tres meses la pendiente es (x - lag2) / 2; con dos, x - lag1; con uno queda vacía (igual que en su código).
# Quedan afuera el detalle del resumen de tarjeta (Visa_*, Master_*: su historia no entra, ver historia_de_resumen) e internet
# (tiene su propio tratamiento). El promedio sólo se agrega a las variables que no lo tenían (las que no son montos ni conteos).
# Estas columnas las ve sólo el modelo general.
FE_CATEDRA = ("_tend3", "_avg3p")


def fe_historico_catedra(d: pd.DataFrame) -> pd.DataFrame:
    crudas = [c for c in d.columns if f"{c}_lag1" in d.columns and f"{c}_lag2" in d.columns
              and not c.startswith(("Visa_", "Master_")) and c != "internet"]
    nuevo = {}
    for c in crudas:
        y = d[[f"{c}_lag2", f"{c}_lag1", c]].to_numpy(float)
        x = np.array([1.0, 2.0, 3.0]); ok = ~np.isnan(y); n = ok.sum(1); y0 = np.where(ok, y, 0)
        sx, sy, sxy, sxx = (ok * x).sum(1), y0.sum(1), (y0 * x).sum(1), (ok * x * x).sum(1)
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (n * sxy - sx * sy) / (n * sxx - sx * sx)
            a = sy / n
        t[n < 2] = np.nan; a[n < 2] = np.nan
        nuevo[f"{c}_tend3"] = t.astype("float32")
        if f"{c}_avg3" not in d.columns:
            nuevo[f"{c}_avg3p"] = a.astype("float32")
    return pd.concat([d, pd.DataFrame(nuevo, index=d.index)], axis=1)


# [Anotación · líneas 177–197] Constantes del modelo general: TRAIN_MONTHS_BACK = 3 (últimos tres meses con
#   clase), PARAMS (learning_rate 0,027, num_leaves 31, min_data_in_leaf 200, feature_fraction 0,5, max_bin 255,
#   16 hilos; el objective "binary" se reemplaza después por multiclass), 500 rondas, UNDERSAMPLING = 0,2 y
#   PESO_BAJA1 = 0,5. POSITIVOS se define y no se usa en el resto del archivo. HISTORIA reúne los diez sufijos
#   de las columnas derivadas (lags, deltas, razones y ventana).
# ---------------------------------------------------------------- modelo

TRAIN_MONTHS_BACK = 3  # entrega: 202104-06 (todos con lag1); excluye 202103, que no tiene historia (el modelo que puntúa mayo y junio para la segunda etapa sí lo usa: no tiene otro)

PARAMS = dict(
    objective="binary",  # sin efecto: base() lo pisa con "multiclass" de 3 clases
    learning_rate=0.027,
    num_leaves=31,
    min_data_in_leaf=200,
    feature_fraction=0.5,
    max_bin=255,
    verbosity=-1,
    num_threads=16,
)
NUM_ROUNDS = 500
UNDERSAMPLING = 0.2  # fracción de CONTINUA que se conserva
POSITIVOS = ["BAJA+1", "BAJA+2"]  # las dos clases de baja
PESO_BAJA1 = 0.5  # las BAJA+1 pesan la mitad al entrenar el general: se van en un mes y no pagan; BAJA+2 es la clase que paga


HISTORIA = tuple(f"_{s}" for s in ("lag1", "delta1", "lag2", "delta2", "ratiolag1", "ratioavg3", "avg3", "min3", "max3", "ratiomax3"))


# [Anotación · líneas 200–213] historia_de_resumen devuelve verdadero para las columnas que empiezan con Visa_
#   o Master_ y terminan con alguno de los diez sufijos de HISTORIA; esas columnas quedan fuera de la lista de
#   columnas que arma base().
def historia_de_resumen(c: str) -> bool:
    """Historia derivada (lags, deltas, razones, ventana) del detalle del resumen de tarjeta (Visa_*, Master_*): no entra.

    Esas 44 variables son la foto del último resumen y dependen de en qué día cae el cierre (fultimo_cierre), que se
    corre con el calendario: es el bloque que más cambia de distribución entre los meses de entrenamiento y el mes a
    puntuar (KS mediano de sus derivadas 0,037 contra 0,016 del resto; las fechas llegan a 0,7-1,0). La diferencia de
    un saldo de resumen contra el mes anterior mezcla el ciclo del resumen con lo que hizo el cliente. Entran crudas
    (el modelo sigue viendo saldo, pago mínimo, mora y límite de hoy), y la historia del uso de la tarjeta queda en los
    agregados del banco (ctarjeta_*_transacciones, mtarjeta_*_consumo), que sí conservan sus derivadas.
    Junto con el tratamiento de la deriva: Visa_msaldototal y Visa_msaldopesos (a percentil dentro del mes) y los dos
    fultimo_cierre (menos la moda del mes) son de este bloque, así que entran sólo con su valor del mes ya corregido;
    de los 14 montos a percentil, los otros 12 son del banco y conservan su historia, calculada sobre el percentil.
    """
    return c.startswith(("Visa_", "Master_")) and c.endswith(HISTORIA)

# [Anotación · líneas 215–239] Constantes del especialista de deudores: segmento internet >= 1; PARAMS_ESP
#   (binary, learning_rate 0,03, num_leaves 15, min_data_in_leaf 50, feature_fraction 0,3, max_bin 255, 4
#   hilos), 200 rondas, mínimo de 200 filas para entrenar, 50 canaritos, 5 repeticiones, mínimo de 5 variables
#   elegidas y el diccionario _ELEGIDAS, que guarda la selección para no recalcularla.
# ---------------------------------------------------------------- especialista de deudores, con canaritos
#
# Por qué existe el especialista: `internet` con valor 1 a 3 marca deudores en problemas (saldo negativo, mora de tarjeta, 3 o más
# préstamos). Sus bajas son cierres que decide el banco y cambian de un mes a otro (2,3% de BAJA+2 en 202104, 1,6% en 202105 y
# 4,3% en 202106); el general promedia los tres meses y los subestima. El especialista mira SÓLO a ese grupo y SÓLO el último
# mes con clase. Por qué con canaritos: con ~6.000 filas y ~380 bajas, 1.160
# variables son demasiadas y el especialista ajusta ruido. Los canaritos miden cuánta ganancia junta una columna de números
# al azar; sólo quedan las variables reales que juntan más que el mejor de ellos.
SEGMENTO_INTERNET = 1  # "tiene / no tiene" la marca
PARAMS_ESP = dict(
    objective="binary",
    learning_rate=0.03,
    num_leaves=15,  # el segmento son ~6.000 filas y ~380 bajas: árboles chicos
    min_data_in_leaf=50,
    feature_fraction=0.3,
    max_bin=255,
    verbosity=-1,
    num_threads=4,  # con tan pocas filas más hilos no aceleran
)
NUM_ROUNDS_ESP = 200
MIN_FILAS_ESP = 200  # resguardo: con menos filas o una sola clase no hay nada que aprender
CANARITOS = 50    # cuántas columnas de ruido
REPETICIONES = 5  # corridas con canaritos que se promedian
MINIMO = 5        # nunca menos variables que éstas
_ELEGIDAS = {}    # train del segmento -> lista: la selección no depende de la semilla, se calcula una vez por proceso


# [Anotación · líneas 242–264] le_ganan_al_ruido agrega 50 columnas de números uniformes al azar al train del
#   segmento y entrena 5 LightGBM de 200 rondas (seeds 9000 a 9004; los canaritos salen de un generador cuya
#   semilla depende del mes y de la repetición). Promedia la importancia "gain" de las 5 corridas y devuelve, de
#   mayor a menor, las variables reales cuya importancia media supera la del canarito de mayor importancia; si
#   quedan menos de 5 devuelve las 5 primeras. El resultado se guarda en _ELEGIDAS con una clave que identifica
#   el train y sus columnas, y se imprime.
def le_ganan_al_ruido(tr: pd.DataFrame, cols: list, y: np.ndarray) -> list:
    """Variables de cols cuya ganancia media supera a la del mejor canarito, ordenadas de mayor a menor ganancia."""
    mes = int(tr.foto_mes.iloc[0])
    clave = (mes, len(tr), int(tr.numero_de_cliente.sum()), int(y.sum()), tuple(cols))  # el train exacto y sus columnas
    if clave not in _ELEGIDAS:
        X = tr[cols].reset_index(drop=True)
        ruido = [f"canarito_{i}" for i in range(CANARITOS)]
        ganancias = []
        for j in range(REPETICIONES):
            rng = np.random.default_rng(10_000 * CANARITOS + 100 * (mes % 100) + j)
            D = pd.concat([X, pd.DataFrame(rng.random((len(X), CANARITOS)), columns=ruido)], axis=1)
            model = lgb.train({**PARAMS_ESP, "seed": 9000 + j}, lgb.Dataset(D, label=y), num_boost_round=NUM_ROUNDS_ESP)
            ganancias.append(model.feature_importance("gain"))
        g = np.mean(ganancias, axis=0)
        real, vara = g[:len(cols)], g[len(cols):].max()
        orden = np.argsort(-real, kind="stable")
        elegidas = [cols[i] for i in orden if real[i] > vara]
        _ELEGIDAS[clave] = elegidas if len(elegidas) >= MINIMO else [cols[i] for i in orden[:MINIMO]]
        # Para diagnóstico: el conjunto y el ORDEN de estas variables son parte del modelo (feature_fraction sortea por
        # posición). Si en otra máquina la lista final no coincide, lo primero a mirar es si salen las mismas.
        print(f"  especialista de deudores ({mes}): {len(_ELEGIDAS[clave])} de {len(cols)} variables le ganan al ruido: "
              + ", ".join(_ELEGIDAS[clave]), flush=True)
    return _ELEGIDAS[clave]


# [Anotación · líneas 267–284] especialista marca las filas de score con internet >= 1 y arma su train con las
#   filas del último mes con clase que cumplen la misma condición; la clase es 1 si clase_ternaria no es
#   CONTINUA. Si hay menos de 200 filas, una sola clase o ninguna fila de score en el segmento, devuelve None.
#   Si no, selecciona variables con le_ganan_al_ruido (sin foto_mes), entrena un LightGBM binario de 200 rondas
#   con la semilla de la corrida, puntúa el segmento y transforma la probabilidad con p / (p + 0,2 (1 − p)).
def especialista(train: pd.DataFrame, score: pd.DataFrame, cols: list, seed: int):
    """Probabilidad de baja (BAJA+1 o BAJA+2) de los clientes del segmento, en la escala del general.

    Devuelve (máscara de filas de score que son del segmento, probabilidad de esas filas) o (máscara, None) si no se pudo
    entrenar. Se entrena sin submuestreo y se corrige a la escala del general, p / (p + 0,2 (1 - p)), sólo
    con las variables que le ganan al ruido.
    """
    en_seg = (score.internet >= SEGMENTO_INTERNET).to_numpy()
    ultimo = train.foto_mes.max()
    tr = train[(train.foto_mes == ultimo).to_numpy() & (train.internet >= SEGMENTO_INTERNET).to_numpy()]
    y = (tr.clase_ternaria != "CONTINUA").to_numpy().astype(int)
    if len(tr) < MIN_FILAS_ESP or y.min() == y.max() or not en_seg.any():
        return en_seg, None
    cols_e = [c for c in cols if c != "foto_mes"]  # un solo mes: foto_mes es constante
    elegidas = le_ganan_al_ruido(tr, cols_e, y)
    model = lgb.train({**PARAMS_ESP, "seed": int(seed)}, lgb.Dataset(tr[elegidas], label=y), num_boost_round=NUM_ROUNDS_ESP)
    p = model.predict(score.loc[en_seg, elegidas])
    return en_seg, p / (p + UNDERSAMPLING * (1 - p))


# [Anotación · líneas 287–300] base se queda con los últimos 3 meses con clase y define las columnas del
#   modelo: todas menos clase_ternaria, numero_de_cliente y las que marca historia_de_resumen (foto_mes queda
#   incluida). Llama a especialista con esas columnas sin las terminadas en _tend3 o _avg3p. Para el modelo
#   general conserva las filas CONTINUA cuyo número al azar (generador sembrado con la semilla) es menor a 0,2 y
#   todas las de baja; codifica la clase como 0, 1 y 2, y asigna peso 0,5 a las BAJA+1 y 1 al resto.
def base(train: pd.DataFrame, score: pd.DataFrame, seed: int) -> np.ndarray:
    """General + especialista de deudores con reparto. Devuelve P(BAJA+1) + P(BAJA+2) del general, con el reparto en el segmento."""
    months = sorted(train.foto_mes.unique())[-TRAIN_MONTHS_BACK:]
    train = train[train.foto_mes.isin(months)]
    # Columnas: todas menos la historia del resumen de tarjetas (ver historia_de_resumen); el FE de la cátedra lo ve sólo el general.
    cols = [c for c in train.columns if c not in ("clase_ternaria", "numero_de_cliente") and not historia_de_resumen(c)]
    # El especialista va antes del submuestreo (usa todas las filas del segmento) y antes de enmascarar internet:
    # igual sólo mira el último mes con clase, que el enmascarado no toca.
    en_seg, p_esp = especialista(train, score, [c for c in cols if not c.endswith(FE_CATEDRA)], seed)  # el especialista no ve el FE de la cátedra
    # modelo general, para todos los clientes: multiclase, con submuestreo de los CONTINUA y las BAJA+1 a medio peso
    keep = np.random.default_rng(seed).random(len(train)) < UNDERSAMPLING
    train = train[keep | (train.clase_ternaria != "CONTINUA").to_numpy()]
    y = train.clase_ternaria.map({"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2})
    w = np.where(train.clase_ternaria == "BAJA+1", PESO_BAJA1, 1.0)
# [Anotación · líneas 301–313] Verifica con un assert que haya 5 columnas cuyo nombre empieza con internet y
#   las pone en 0 en las filas de entrenamiento de meses anteriores al último. Entrena un LightGBM multiclass de
#   3 clases con PARAMS, la semilla y 500 rondas, y calcula para las filas de score la suma de las
#   probabilidades de BAJA+1 y BAJA+2.
    # internet cambió de régimen: a igual actividad, tener internet >= 2 dos meses seguidos no subía la baja en 202104-05
    # (1-3% contra 2-6% del resto) y en 202106 la duplica (6-7% contra 2-4%). El promedio de los tres meses borra lo que
    # vale hoy, así que su efecto se aprende SÓLO del último mes con clase: en los meses anteriores de entrenamiento va
    # en 0 (el valor del 96%). No en NaN: "internet falta" marcaría el mes y el árbol aprendería un efecto de junio.
    # Va junto con la quita de la historia del resumen porque no se pisan: aquel filtro sólo mira Visa_*/Master_* y acá
    # quedan las 5 columnas de internet (cruda, 2 lags, 2 deltas). El assert es para que un cambio de nombres no deje
    # el enmascarado vacío sin avisar (el modelo entrenaría igual, con internet promediado en los tres meses).
    internet = [c for c in cols if c.startswith("internet")]
    assert len(internet) == 5, f"se esperaban 5 columnas de internet y hay {internet}"
    train.loc[(train.foto_mes < months[-1]).to_numpy(), internet] = 0
    dtrain = lgb.Dataset(train[cols], label=y, weight=w, free_raw_data=True)
    model = lgb.train({**PARAMS, "objective": "multiclass", "num_class": 3, "seed": seed}, dtrain, num_boost_round=NUM_ROUNDS)
    p = model.predict(score[cols])[:, 1:].sum(axis=1)
# [Anotación · líneas 314–323] Si el especialista devolvió probabilidades, reemplaza, mes por mes, las
#   probabilidades de las filas del segmento por el resultado de repartir (general y especialista). Devuelve el
#   vector de probabilidades.
    if p_esp is not None:
        # Mes por mes: el perfil y el orden son de los clientes de UN mes. Al puntuar 202108 hay un solo mes (da lo mismo),
        # pero base_fuera_de_muestra puntúa mayo y junio en una sola llamada, y repartir todo junto le daría a un cliente
        # de junio un valor sacado de los de mayo.
        mes_seg, p_seg = score.foto_mes.to_numpy()[en_seg], p[en_seg]
        for m in np.unique(mes_seg):
            k = mes_seg == m
            p_seg[k] = repartir(p_seg[k], p_esp[k])
        p[en_seg] = p_seg
    return p


# [Anotación · líneas 326–347] logit recorta la probabilidad a [1e-9, 1 − 1e-9] y calcula log(p / (1 − p)).
#   repartir toma el máximo entre general y especialista para cada cliente del segmento, ordena esos valores de
#   mayor a menor y los asigna a los clientes según el orden decreciente de la suma de los logit de los dos
#   modelos: el conjunto de valores es el del máximo y la asignación sigue a la suma.
def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return np.log(p / (1 - p))


def repartir(p_gen: np.ndarray, p_esp: np.ndarray) -> np.ndarray:
    """Probabilidad final de los clientes del segmento: CUÁNTO sube el grupo lo decide el máximo; A QUIÉN, los dos modelos.

    Si cada cliente del segmento se quedara con max(general, especialista), el grupo sube, que es lo que hace falta (el
    general lo subestima), pero a quién se sube lo elige el ruido del especialista: sube el cliente en el que el
    especialista, con sus ~6.000 filas, se pasó para arriba.
    Acá se separan las dos cosas:
      - el perfil: los valores de max(general, especialista) del segmento, ordenados. Son exactamente los mismos números
        que daría el máximo, así que por semilla entra a la lista la misma cantidad de deudores y con el mismo nivel;
      - el orden: esos valores se reparten de mayor a menor según el promedio de los logit de los dos modelos, con pesos
        iguales.
    """
    perfil = np.sort(np.maximum(p_gen, p_esp))[::-1]
    orden = np.argsort(-(logit(p_gen) + logit(p_esp)), kind="stable")
    out = np.empty_like(p_gen)
    out[orden] = perfil
    return out


# [Anotación · líneas 350–367] Constantes de la segunda etapa: FRANJA = puestos 8.000 a 30.000; PARAMS_2
#   (binary, learning_rate 0,03, num_leaves 4, min_data_in_leaf 200, feature_fraction 0,3, lambda_l2 20, max_bin
#   63, 3 hilos), 100 rondas, MESES_DETRAS = 2, SEMILLAS_FUERA = (800011,) y VARIABLES_2, una lista fija de 25
#   variables. _FUERA guarda la base fuera de muestra para calcularla una sola vez por proceso.
# ---------------------------------------------------------------- segunda etapa sobre la franja dudosa

FRANJA = (8000, 30000)  # puestos de la base, sólo clientes sin marca internet
PARAMS_2 = dict(objective="binary", learning_rate=0.03, num_leaves=4, min_data_in_leaf=200, feature_fraction=0.3, lambda_l2=20.0,
                max_bin=63, verbosity=-1, num_threads=3)
RONDAS_2 = 100
MESES_DETRAS = 2             # meses de datos que tiene que tener detrás un mes para entrenar con él
SEMILLAS_FUERA = (800011,)  # semillas de la base fuera de muestra (se promedian si hay varias); se entrena una vez por proceso
VARIABLES_2 = [  # las que les ganan a los canaritos (percentil 95), en orden de ganancia
    "mcomisiones_mantenimiento_lag2", "mrentabilidad_max3", "mcuentas_saldo_delta2", "mcomisiones_mantenimiento_ratioavg3",
    "ccomisiones_mantenimiento_lag2", "ctrx_quarter_lag2", "mtarjeta_master_consumo_lag1", "ctrx_quarter_delta2", "cliente_edad_lag2",
    "chomebanking_transacciones_ratiomax3", "cproductos_ratiomax3", "ctrx_quarter_lag1", "mcuenta_corriente", "cliente_edad_lag1",
    "mtransferencias_recibidas_ratioavg3", "mtarjeta_master_consumo_ratiolag1", "ctransferencias_recibidas_ratioavg3",
    "chomebanking_transacciones_ratioavg3", "ccaja_ahorro_lag2", "cproductos_ratioavg3", "mcomisiones_mantenimiento",
    "ccomisiones_mantenimiento_ratioavg3", "mpagomiscuentas_delta2", "ctarjeta_visa_transacciones_ratioavg3",
    "ctarjeta_visa_transacciones_ratiomax3",
]
_FUERA = {}  # train -> {mes: base fuera de muestra}; se calcula una vez por proceso


# [Anotación · líneas 370–381] puesto devuelve la posición de cada cliente al ordenar de mayor a menor
#   probabilidad (0 es la mayor), con orden estable. grupo devuelve la máscara de clientes cuyo puesto está
#   entre 8.000 (incluido) y 30.000 (excluido) y cuyo valor de internet es 0.
def puesto(p):
    """Puesto de cada cliente (0 = el más probable), con orden estable."""
    r = np.empty(len(p), int)
    r[np.argsort(-p, kind="stable")] = np.arange(len(p))
    return r


def grupo(internet, p, franja=None):
    """Clientes de un mes en la franja de puestos de p y sin marca internet."""
    franja = franja or FRANJA
    r = puesto(p)
    return (r >= franja[0]) & (r < franja[1]) & (np.asarray(internet) == 0)


# [Anotación · líneas 384–391] calibracion ajusta una regresión logística de dos coeficientes (ordenada y
#   pendiente sobre el logit de entrada) con 40 iteraciones de Newton y un término 1e-8 en la diagonal.
def calibracion(l, y):
    """Regresión logística y ~ c0 + c1 * l, por Newton."""
    A = np.column_stack([np.ones(len(l)), l])
    c = np.zeros(2)
    for _ in range(40):
        mu = 1 / (1 + np.exp(-A @ c))
        c += np.linalg.solve(A.T @ (A * (mu * (1 - mu))[:, None]) + 1e-8 * np.eye(2), A.T @ (y - mu))
    return c


# [Anotación · líneas 394–397] meses_de_entrenamiento devuelve los dos últimos meses con clase que tienen al
#   menos 2 meses antes en train; con clase de 202103 a 202106 son 202105 y 202106.
def meses_de_entrenamiento(train):
    """Los dos últimos meses con clase que tienen MESES_DETRAS meses de datos antes (mayo y junio en la entrega)."""
    meses = sorted(int(m) for m in train.foto_mes.unique())
    return [m for i, m in enumerate(meses) if i >= MESES_DETRAS][-2:]


# [Anotación · líneas 400–418] base_fuera_de_muestra entrena base() con las filas con clase anteriores al
#   primero de esos dos meses (202103 y 202104), con la semilla 800011, y puntúa las filas de 202105 y 202106
#   sin su clase. Devuelve por mes los numero_de_cliente y su probabilidad, y guarda el resultado en _FUERA para
#   reutilizarlo en todas las semillas.
def base_fuera_de_muestra(train: pd.DataFrame) -> dict:
    """{mes: (clientes, probabilidad de la base para esas filas, sin haber visto su clase)} para mayo y junio.

    UN corte: la base se entrena con las filas con clase ANTERIORES al primero de los dos meses (clase <= 202104) y puntúa
    los dos; si SEMILLAS_FUERA trae más de una, se promedian. Se calcula una vez por proceso y vale para todas las semillas de la entrega.
    """
    meses = meses_de_entrenamiento(train)
    clave = (tuple(meses), len(train), int(train.numero_de_cliente.sum()))
    if clave not in _FUERA:
        out = {}
        if meses:
            antes = train[(train.foto_mes < meses[0]).to_numpy()]
            a_puntuar = train[train.foto_mes.isin(meses).to_numpy()].drop(columns=["clase_ternaria"])
            p = np.mean([np.asarray(base(antes, a_puntuar, s), dtype=np.float64) for s in SEMILLAS_FUERA], axis=0)
            mes = a_puntuar.foto_mes.to_numpy()
            ids = a_puntuar.numero_de_cliente.to_numpy()
            out = {m: (ids[mes == m], p[mes == m]) for m in meses}
        _FUERA[clave] = out
    return _FUERA[clave]


# [Anotación · líneas 421–441] segunda_etapa copia la probabilidad de base y arma su conjunto de
#   entrenamiento: para 202105 y 202106 toma las filas de la franja (puestos 8.000 a 30.000 según la base fuera
#   de muestra, internet = 0) que no son BAJA+1, con las 25 columnas de VARIABLES_2, clase 1 si es BAJA+2 y el
#   logit de la probabilidad fuera de muestra. Si no hay meses disponibles, hay menos de 400 filas o una sola
#   clase, devuelve la probabilidad sin cambios.
def segunda_etapa(train: pd.DataFrame, score: pd.DataFrame, seed: int, p_base: np.ndarray) -> np.ndarray:
    """Probabilidad corregida, del mismo largo que p_base (la de base() para las filas de score, con esa semilla).

    Entrena con las franjas de mayo y junio (por el orden de la base fuera de muestra), sin marca internet y sin las BAJA+1;
    clase: BAJA+2 contra CONTINUA; punto de partida c0 + c1 * logit(base), la calibración de la base dentro de la franja.
    Sin meses con qué entrenar (clase sólo hasta abril) devuelve p_base sin tocar.
    """
    p = np.asarray(p_base, dtype=np.float64).copy()
    fuera = base_fuera_de_muestra(train)
    if not fuera:
        return p
    X, y, l = [], [], []
    for m, (ids_m, pm) in fuera.items():
        t = train[(train.foto_mes == m).to_numpy()]
        assert np.array_equal(t.numero_de_cliente.to_numpy(), ids_m), "la base fuera de muestra no está alineada con las filas del mes"
        clase = t.clase_ternaria.to_numpy()
        k = grupo(t.internet.to_numpy(), pm) & (clase != "BAJA+1")
        X.append(t.loc[k, VARIABLES_2]); y.append((clase[k] == "BAJA+2").astype(float)); l.append(logit(pm[k]))
    X, y, l = pd.concat(X, ignore_index=True), np.concatenate(y), np.concatenate(l)
    if len(y) < 2 * PARAMS_2["min_data_in_leaf"] or y.min() == y.max():  # con muy pocas filas o una sola clase no hay con qué aprender
        return p
# [Anotación · líneas 442–456] Ajusta la calibración del logit de la base dentro de la franja y entrena un
#   LightGBM binario de 100 rondas que parte de ese valor calibrado (init_score). En el mes a puntuar, para los
#   clientes de la franja calcula el puntaje del modelo más la calibración, suma el rango de ese puntaje con el
#   rango de la probabilidad de base y reasigna las mismas probabilidades de la franja, de mayor a menor, según
#   esa suma.
    c = calibracion(l, y)
    modelo = lgb.train({**PARAMS_2, "seed": seed}, lgb.Dataset(X, label=y, init_score=c[0] + c[1] * l), num_boost_round=RONDAS_2)
    mes, internet = score.foto_mes.to_numpy(), score.internet.to_numpy()
    for m in np.unique(mes):  # mes por mes: el puesto y el reparto son de los clientes de UN mes
        f = np.flatnonzero(mes == m)
        idx = f[grupo(internet[f], p[f])]
        if not len(idx):
            continue
        s = modelo.predict(score.iloc[idx][VARIABLES_2], raw_score=True) + c[0] + c[1] * logit(p[idx])
        s = pd.Series(s).rank().to_numpy() + pd.Series(p[idx]).rank().to_numpy()  # suma de puestos: corregido + base
        orden = np.argsort(-s, kind="stable")
        nuevo = np.empty(len(idx))
        nuevo[orden] = np.sort(p[idx])[::-1]  # los mismos valores, repartidos por el orden nuevo
        p[idx] = nuevo
    return p



# [Anotación · líneas 460–463] train_and_predict es la función que llama reproducir.py: calcula base() para la
#   semilla y le aplica segunda_etapa(). El cuarto parámetro (intermedio) se recibe y no se usa.
# ---------------------------------------------------------------- el modelo

def train_and_predict(train: pd.DataFrame, score: pd.DataFrame, seed: int, intermedio=None) -> np.ndarray:
    return segunda_etapa(train, score, seed, base(train, score, seed))
```


## Explicaciones del alumno (texto original)

### README.md

> # Entrega final — competencia 01 (DMEyF 2026)
>
> "Tips Ale Bolaño" con el FE histórico de la cátedra. Predice BAJA+2 de 202108.
>
> ## Qué hay
>
> - `TipsAleBolanoFE_final.csv` — la lista entregada: 11.250 clientes, uno por línea, sin encabezado.
> - `codigo/` — todo lo necesario para rehacerla desde el dataset crudo, de principio a fin.
>   - `reproducir.py`: el único comando. Lee el dataset, arma las variables, entrena, promedia y escribe la lista.
>   - `prepare.py`: lee el CSV crudo, arma `clase_ternaria` y separa lo que se entrena (hasta 202106) de lo que se puntúa (202108).
>   - `modelos/tips_ale_bolano_fe.py`: el modelo (`make_features` y `train_and_predict`). El encabezado explica las tres piezas.
>   - `esperado.json`: huella (sha256) de la lista de la entrega y de la lista de cada semilla sola.
>   - `requirements.txt`: versiones exactas, incluidas las dos dependencias de LightGBM. Importan: la selección de variables por canaritos depende de ellas.
>
> ## El modelo, en tres líneas
>
> 1. Modelo general: LightGBM de tres clases con abril, mayo y junio; las BAJA+1 pesan la mitad al entrenar. Incluye el FE histórico que publicó la cátedra (tendencia y promedio de 3 meses).
> 2. Especialista de deudores (clientes con `internet` >= 1), que elige sus variables con canaritos y se combina con el general.
> 3. Segunda etapa: un modelo chico que aprende en mayo y junio a corregir la franja dudosa y la reordena en agosto.
>
> La lista es un ensamble de semillas: el modelo se corre 25 veces, una por semilla (`SEMILLAS`, en `reproducir.py`), se
> promedian las probabilidades y quedan los 11.250 clientes de mayor probabilidad (`CORTE`).
>
> Los hiperparámetros y dos listas fijas de variables (`PERCENTIL_CERO_FIJO` y `VARIABLES_2`) están escritos en
> `modelos/tips_ale_bolano_fe.py` y no se recalculan al correr; la única selección de variables que se hace al correr es la del
> especialista (canaritos).
>
> ## Cómo reproducir
>
> El dataset crudo va en `~/competencia_01_crudo.csv`. El que se usó pesa 492.769.580 bytes y tiene 983.061 filas (más el
> encabezado), 154 columnas y `foto_mes` de 202103 a 202108; su sha256 es
> `c72c8f5c1149f1d972e996c2963c5e3dbb31eb38cfe41c2bb1bbaf847d7a7ca1` (`shasum -a 256 ~/competencia_01_crudo.csv`; en Linux,
> `sha256sum`). La lista depende de los valores y también del orden de las filas y de las columnas del archivo: con otra
> exportación del mismo dataset puede no coincidir.
>
> ```bash
> cd codigo
> pip install -r requirements.txt
> python reproducir.py
> ```
>
> Hace falta Python 3.12 o más nuevo (se hizo con 3.14.4), en un entorno virtual nuevo para que `python` y `pip` sean los de ese
> entorno (`python3 -m venv ~/venv-entrega && source ~/venv-entrega/bin/activate`, antes del `pip install`). En macOS, LightGBM
> necesita OpenMP: `brew install libomp`.
> La lista idéntica, cliente por cliente y en el mismo orden, está comprobada en la máquina que se describe más abajo; con otro
> sistema operativo u otro procesador LightGBM puede dar diferencias chicas en las probabilidades. En ese caso el sha256 puede no
> coincidir aunque la lista sea casi la misma, porque compara también el orden de las líneas; `reproducir.py` dice además
> cuántos clientes tiene en común con la lista entregada, sin mirar el orden.
>
> Escribe `codigo/salida/TipsAleBolanoFE_final.csv` y dice si salió idéntica a la de referencia (y cuántas de las 25 listas por
> semilla coinciden). Tarda unos 20 minutos en una Mac de 18 núcleos (75 s la primera semilla, unos 40 s las demás) y usa unos
> 21 GB de memoria (más en el pico, mientras arma las variables: conviene una máquina con 32 GB o más). Cada semilla se guarda apenas termina: si se corta, al relanzar sigue por la que falta. Para rehacer todo de
> cero hay que borrar `codigo/salida/`: lo que ya está guardado ahí (el dataset en parquet y las semillas) no se vuelve a calcular.
>
> `python reproducir.py --prueba` corre sólo la primera semilla y compara su lista con la de referencia.
>
> Al entrenar imprime dos listas de variables elegidas por el especialista (24 para 202106 y 20 para 202104; la de 202104 es
> del modelo que puntúa mayo y junio para la segunda etapa). Las dos son parte
> del modelo: si en otra máquina la lista no coincide, lo primero a mirar es si salieron las mismas variables y si las versiones
> son las de `requirements.txt`.
>
> Las dos líneas que imprime la corrida de referencia (el orden de las variables también es parte del modelo):
>
> ```
> especialista de deudores (202106): 24 de 1160 variables le ganan al ruido: ctrx_quarter, ctrx_quarter_min3, ctrx_quarter_avg3, ctrx_quarter_lag1, mprestamos_personales_delta1, mprestamos_personales_ratiomax3, mcuenta_corriente_delta2, mpayroll, ctrx_quarter_max3, mtransferencias_recibidas, mprestamos_personales_ratiolag1, Visa_mpagominimo, mpasivos_margen_ratioavg3, ctrx_quarter_lag2, ctrx_quarter_ratiomax3, Visa_msaldototal, mprestamos_personales_ratioavg3, mpasivos_margen_ratiolag1, cdescubierto_preacordado, ctrx_quarter_ratioavg3, mpayroll_lag1, ctrx_quarter_ratiolag1, cliente_edad_lag1, Visa_msaldopesos
> especialista de deudores (202104): 20 de 1160 variables le ganan al ruido: mprestamos_personales, ctrx_quarter, ctrx_quarter_min3, ctrx_quarter_avg3, mprestamos_personales_ratioavg3, mprestamos_personales_min3, ctrx_quarter_lag1, ctrx_quarter_max3, mtarjeta_visa_consumo, mprestamos_personales_ratiomax3, mprestamos_personales_ratiolag1, mprestamos_personales_avg3, cprestamos_personales_ratiolag1, cprestamos_personales_ratioavg3, cprestamos_personales, Master_status, internet_lag1, Visa_msaldototal, mtarjeta_visa_consumo_min3, cproductos
> ```
>
> ## Con qué se hizo
>
> Todo se hizo y se corrió en una sola máquina, una Mac:
>
> - MacBook Pro (Mac17,6), chip Apple M5 Max de 18 núcleos (6 + 12), 128 GB de memoria, macOS 27.0.1 (arm64).
> - Python 3.14.4 (CPython), pip 26.2.1.
> - LightGBM 4.7.0 (rueda de PyPI para macOS arm64, con libomp 23.1.2 de Homebrew), pandas 3.0.5, NumPy 2.5.2, PyArrow 25.0.1 y
>   SciPy 1.18.1 y narwhals 2.25.0 (dependencias de LightGBM).
>
> Las huellas de `esperado.json` salieron de esa máquina. La corrida de punta a punta, desde el CSV crudo, dio la lista
> idéntica a la entregada (25 de 25 semillas y la lista final).
>
> ## Autoría
>
> Emmanuel Valdez no escribió ni tocó una sola línea de este código. Todo (la preparación de los datos, el modelo y el script que
> reproduce la lista) lo hizo su agente de IA, Claude Code (Anthropic), siguiendo sus indicaciones.

