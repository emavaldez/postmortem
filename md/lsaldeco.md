# Laura Aldeco — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: lsaldeco
- Repositorio: https://github.com/lsaldeco/Entrega_Competencia01
- Link posteado: https://github.com/lsaldeco/Entrega_Competencia01/tree/main
- Commit: 4bfbb082716c74c885c22f7912959b9692a815ef
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/lsaldeco/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/lsaldeco.json

## Resumen

La entrega es el repositorio completo: siete scripts de Python numerados y un README que indica el orden de ejecución. 01 calcula clase_ternaria con DuckDB a partir de competencia_01_crudo.csv. 02 pone en NaN ccajas_depositos de 202105, imputa nulos con el promedio del registro anterior y el siguiente del mismo cliente, agrega lag 1, lag 2, delta 1 y un cociente de variación contra el registro anterior, calcula para cada columna numérica un rank de cero fijo dentro de cada mes y agrega banderas _zero. 03 busca cinco hiperparámetros de LightGBM con Optuna (60 trials) sobre 202103 y 202104, con 5 particiones aleatorias estratificadas y una métrica de ganancia. 04 entrena con 202103 y 202104 y predice 202106 con 20 semillas; 05 grafica las curvas de ganancia acumulada de junio. 06 toma el trial de mayor valor del estudio, entrena 70 modelos (uno por semilla) con 202103 a 202106 usando sólo las columnas _rank y _zero y predice 202108. 07 promedia las 70 probabilidades, ordena y escribe un CSV con los primeros CORTE clientes.

**Qué entrega.** Un CSV sin encabezado ni índice, con una columna: numero_de_cliente de los primeros CORTE clientes de 202108 ordenados por el promedio de las probabilidades de las 70 semillas. En el código CORTE = 1000 y el archivo se llama agosto_media_70_sem_10k.csv. Según el README, ese CSV es el que se sube al bot y el envío final se definió según la ganancia pública del bot. El repositorio no incluye el archivo enviado ni indica el valor de corte final.

**Cómo se ejecuta.** Según el README, los scripts se ejecutan en este orden: 01_target.py, 02_limpieza_fe.py, 03_optuna_LGBM.py, 04_validacion_junio.py, 05_curvas_ganancia.py, 06_prediccion_agosto.py y 07_cortes_media.py; al principio de cada script está la ruta para cambiarla. La entrada del primero es competencia_01_crudo.csv. En 07 el valor de CORTE se cambia a mano (comentario «ir cambiando el valor de corte»). No se indica el comando ni el entorno.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria, positivo = BAJA+2: clase_binaria vale 1 si clase_ternaria es BAJA+2 y 0 en el resto (BAJA+1, CONTINUA y nulos). La clase_ternaria se calcula en 01_target.py con una consulta SQL en DuckDB.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código
- **Calidad de datos:** En 02_limpieza_fe.py se asigna NaN a ccajas_depositos en 202105. Después, para todas las columnas salvo numero_de_cliente, foto_mes, clase_ternaria, cliente_vip e internet, cada valor nulo se reemplaza por el promedio entre el registro anterior y el siguiente del mismo cliente (ordenado por foto_mes) cuando ambos existen y no son nulos; ccajas_depositos no está en la lista de exclusión de esa función. Las columnas float64 se pasan a float32.
- **Drifting:** Rank de cero fijo calculado dentro de cada foto_mes para cada columna numérica (variables originales, lag1, lag2, delta1 y ratio1): los valores positivos reciben su rank percentil entre los positivos del mes; los negativos reciben, con signo menos, el rank percentil de su valor absoluto entre los negativos del mes; los ceros y los nulos quedan en 0. El modelo usa las columnas _rank y no los valores originales. No se observa deflación ni otro ajuste monetario.
- **Variables dentro del mes:** Una bandera _zero por cada variable numérica original (sin cliente_vip ni internet): vale 1 si el valor es 0, NaN si el valor es nulo y 0 en el resto. No se observan sumas ni cocientes entre variables del mismo mes.
- **Variables históricas:** Para cada columna salvo numero_de_cliente, foto_mes, clase_ternaria, cliente_vip e internet: lag1 y lag2 (valor del registro anterior y del segundo anterior del mismo cliente), delta1 (valor menos lag1) y ratio1 ((valor − lag1) / (|lag1| + 0,00001)). Sobre todas ellas se calcula después el rank por mes. No se observa en el código un delta contra el valor de dos meses atrás ni ventanas de más de dos meses.
- **Selección de variables:** Por sufijo del nombre: sólo entran las columnas que terminan en _rank o en _zero. En la búsqueda de hiperparámetros (03) y en la validación de junio (04) se excluyen además las columnas cuyo nombre empieza con mprestamos_personales o cprestamos_personales; en el entrenamiento final (06) se incluyen. cliente_vip e internet no generan columnas _rank ni _zero, por lo que no entran al modelo. No se observa selección por importancia.
- **Optimización de hiperparámetros:** Optuna, 60 trials, estudio exp_4_lgbm_sss guardado en SQLite (optimization_lgbm_4.db), sin sampler especificado, dirección maximizar. Busca num_leaves (8 a 100), learning_rate (0,001 a 0,1), min_data_in_leaf (1 a 1000), feature_fraction (0,1 a 1,0) y bagging_fraction (0,1 a 1,0). Cada trial corre lgb.cv sobre 202103 y 202104 con 5 particiones StratifiedShuffleSplit (30 % para validar), hasta 3000 iteraciones con parada temprana de int(50 + 5/learning_rate) rondas y una sola semilla, y devuelve el máximo de la ganancia media entre particiones; la iteración de ese máximo se guarda como best_iter.
- **Hiperparámetros finales:** Escritos en 06: objective binary, metric auc, boosting_type gbdt, first_metric_only True, boost_from_average True, feature_pre_filter False, max_bin 31, n_jobs 6. num_leaves, learning_rate, min_data_in_leaf, feature_fraction y bagging_fraction se leen del trial completo de mayor valor del estudio de Optuna, y la cantidad de iteraciones es el best_iter guardado en ese trial. Los valores numéricos elegidos no figuran en el repositorio.
- **Semillas:** 70 semillas escritas como lista en 06_prediccion_agosto.py; las primeras 20 son las mismas de 04 y 05 (un comentario las describe como 5 asignadas + 15 más). En 03 se usa una sola semilla: el primer elemento de 50 números generados con np.random.choice después de np.random.seed(777781).
- **Cantidad de semillas:** 70
- **Ensamble:** Promedio aritmético de las probabilidades de 70 modelos LightGBM que comparten datos, hiperparámetros y cantidad de iteraciones y sólo cambian la semilla (07_cortes_media.py).
- **Corte:** Cantidad fija: los primeros CORTE clientes ordenados por la probabilidad promedio. En el código CORTE = 1000, con el comentario «ir cambiando el valor de corte», y el archivo de salida se llama agosto_media_70_sem_10k.csv. Según el README, la curva de ganancia acumulada de junio se usó para estimar posibles valores de corte y el envío final se definió según la ganancia pública del bot; el valor de corte del envío final no figura en el repositorio.
- **Validación:** En la búsqueda de hiperparámetros: 5 particiones aleatorias estratificadas 70/30 dentro de 202103 y 202104, con una métrica de ganancia (1.072.500 por cada BAJA+2 y −27.500 por el resto entre las filas con probabilidad mayor o igual a 0,025, dividida por 0,3). En 04: entrena con 202103 y 202104 y predice 202106 con 20 semillas; por semilla calcula la ganancia de las filas del 30 % de mayor probabilidad y la guarda en una lista que no se imprime ni se escribe. En 05: curva de ganancia acumulada de junio por semilla y para el promedio de las 20, con la cantidad de envíos donde cada curva alcanza su máximo.
- **Salidas:** competencia_01.csv (01), competencia_01_exp4.parquet (02), optimization_lgbm_4.db con el estudio de Optuna (03), pred_junio_exp4.parquet con una columna de probabilidad por semilla para junio (04), un gráfico en pantalla (05), predicciones_agosto_exp4.parquet con numero_de_cliente y 70 columnas pred_seed_ (06) y el CSV de envío agosto_media_70_sem_10k.csv, sin encabezado, con numero_de_cliente (07).

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)
- Validación cruzada (`validacion.validacion_cruzada`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: No se declara. Las rutas escritas en los scripts tienen la forma /home/laura/…(modificar)…/DMEyF/ (carpetas datos, db y competencia01) y el README indica que la ruta está al principio de cada script para cambiarla. Los scripts de entrenamiento fijan n_jobs = 6.

## Pasos del camino de la entrega

1. **Construcción de clase_ternaria.** Con DuckDB en memoria se arman todas las combinaciones cliente–mes de competencia_01_crudo.csv, se unen con el CSV y se marca si el cliente tiene registro en el mes, en el siguiente y dos meses después. De esas marcas sale BAJA+1, BAJA+2 o CONTINUA. El resultado se guarda en competencia_01.csv. (`01_target.py` líneas 18–55)
2. **ccajas_depositos de mayo e imputación de nulos.** Se asigna NaN a ccajas_depositos en 202105. Luego, para cada columna salvo cinco excluidas, los valores nulos se reemplazan por el promedio del registro anterior y el siguiente del mismo cliente cuando ambos están presentes. (`02_limpieza_fe.py` líneas 13–47)
3. **Lags, delta y cociente de variación.** En bloques de 20 columnas se calculan lag1, lag2, delta1 (valor menos lag1) y ratio1 ((valor − lag1) / (|lag1| + 0,00001)) por cliente. (`02_limpieza_fe.py` líneas 51–108)
4. **Rank de cero fijo por mes.** Para cada columna numérica (originales, lags, delta y ratio) se crea una columna _rank: dentro de cada foto_mes, rank percentil de los positivos, rank percentil con signo menos de los negativos y 0 para ceros y nulos. (`02_limpieza_fe.py` líneas 112–177)
5. **Banderas _zero y guardado del dataset.** Para cada variable numérica original se agrega una bandera _zero (1 si el valor es 0, NaN si es nulo, 0 en el resto) y el dataset completo se guarda en competencia_01_exp4.parquet. (`02_limpieza_fe.py` líneas 181–220)
6. **Clase binaria y columnas para la búsqueda de hiperparámetros.** Se crea clase_binaria (1 = BAJA+2) y se eligen las columnas que terminan en _rank o _zero, sin las que empiezan con mprestamos_personales o cprestamos_personales. El entrenamiento son los meses 202103 y 202104. (`03_optuna_LGBM.py` líneas 31–66)
7. **Búsqueda de hiperparámetros con Optuna.** 60 trials sobre cinco hiperparámetros de LightGBM. Cada trial corre lgb.cv con 5 particiones StratifiedShuffleSplit (30 % para validar) y la métrica de ganancia con umbral 0,025; se guarda la iteración de mayor ganancia media como best_iter. El estudio queda en optimization_lgbm_4.db. (`03_optuna_LGBM.py` líneas 92–169)
8. **Validación en junio con 20 semillas.** Se recuperan los hiperparámetros y best_iter del estudio, se entrena con 202103 y 202104 una vez por cada una de 20 semillas y se predice 202106. Las probabilidades por semilla se guardan en pred_junio_exp4.parquet. (`04_validacion_junio.py` líneas 48–75; `04_validacion_junio.py` líneas 77–114; `04_validacion_junio.py` líneas 136–179)
9. **Curvas de ganancia acumulada de junio.** Para cada semilla y para el promedio de las 20 se ordena junio por probabilidad, se acumula la ganancia (1.072.500 por BAJA+2, −27.500 por el resto), se imprime la cantidad de envíos donde la curva es máxima y se grafican las curvas. Según el README, esta curva se usó para estimar posibles valores de corte. (`05_curvas_ganancia.py` líneas 29–85; `05_curvas_ganancia.py` líneas 87–120; `README.md` líneas 25–25)
10. **Recuperación del trial y parámetros finales.** Se carga el estudio de Optuna, se toma el trial completo de mayor valor con su best_iter y se combinan sus cinco hiperparámetros con los parámetros fijos (binary, auc, gbdt, max_bin 31, n_jobs 6). (`06_prediccion_agosto.py` líneas 95–127)
11. **Carga de 202103 a 202106 y de 202108.** Se leen los cuatro meses de entrenamiento de a uno, con todas las columnas _rank y _zero (incluidas las de préstamos personales) y la clase binaria, y se apilan en matrices float32. Se leen las filas de 202108 con las mismas columnas. (`06_prediccion_agosto.py` líneas 129–188)
12. **Entrenamiento de 70 modelos y predicción de agosto.** Para cada una de las 70 semillas se entrena un LightGBM con los cuatro meses durante best_iter iteraciones y se predice 202108. Las 70 columnas de probabilidad se guardan en predicciones_agosto_exp4.parquet. (`06_prediccion_agosto.py` líneas 19–92; `06_prediccion_agosto.py` líneas 190–222)
13. **Promedio de semillas, corte y CSV de envío.** Se promedian las probabilidades de todas las semillas, se ordena de mayor a menor y se escriben los numero_de_cliente de las primeras CORTE filas (1000 en el código) en un CSV sin encabezado. (`07_cortes_media.py` líneas 9–42)

## Archivos

- `06_prediccion_agosto.py` · principal · Python · 229 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lsaldeco/06_prediccion_agosto.py.txt) — Toma del estudio de Optuna el trial de mayor valor, entrena 70 modelos LightGBM (uno por semilla) con 202103 a 202106 sobre todas las columnas _rank y _zero y predice 202108. Guarda una columna de probabilidad por semilla en predicciones_agosto_exp4.parquet.
- `03_optuna_LGBM.py` · principal · Python · 180 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lsaldeco/03_optuna_LGBM.py.txt) — Busca hiperparámetros de LightGBM con Optuna (60 trials) sobre 202103 y 202104, con lgb.cv en 5 particiones aleatorias estratificadas y una métrica de ganancia. Guarda el estudio en una base SQLite que leen 04 y 06.
- `README.md` · explicacion · Markdown · 27 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lsaldeco/README.md.txt) — Presenta el repositorio como los scripts usados para generar los envíos, lista los siete scripts en orden de ejecución con una línea por cada uno y agrega aclaraciones sobre faltantes, variables, entrenamiento, validación y predicción de agosto. Según el README: la búsqueda con Optuna usa 60 trials y 1 semilla; la validación de junio, 20 semillas; la predicción de agosto, 70 semillas; y el envío final se definió según la ganancia pública del bot.
- `02_limpieza_fe.py` · principal · Python · 220 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lsaldeco/02_limpieza_fe.py.txt) — Lee competencia_01.csv, pone en NaN ccajas_depositos de 202105, imputa nulos, agrega lags, delta y ratio, calcula el rank de cero fijo por mes y las banderas _zero, y guarda todo en competencia_01_exp4.parquet.
- `07_cortes_media.py` · principal · Python · 48 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lsaldeco/07_cortes_media.py.txt) — Lee predicciones_agosto_exp4.parquet, promedia las probabilidades de todas las semillas, ordena de mayor a menor y escribe en un CSV sin encabezado los numero_de_cliente de las primeras CORTE filas.
- `04_validacion_junio.py` · principal · Python · 183 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lsaldeco/04_validacion_junio.py.txt) — Entrena con 202103 y 202104 usando los hiperparámetros del estudio de Optuna y predice 202106 con 20 semillas. Guarda las probabilidades por semilla en pred_junio_exp4.parquet, que lee 05_curvas_ganancia.py; 06 y 07 no leen esa salida.
- `01_target.py` · principal · Python · 73 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lsaldeco/01_target.py.txt) — Calcula clase_ternaria con una consulta SQL en DuckDB sobre competencia_01_crudo.csv y guarda el resultado en competencia_01.csv. Imprime la cantidad de clientes por mes y clase.
- `05_curvas_ganancia.py` · principal · Python · 120 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lsaldeco/05_curvas_ganancia.py.txt) — Lee pred_junio_exp4.parquet, calcula la curva de ganancia acumulada de junio para cada una de las 20 semillas y para su promedio, imprime la cantidad de envíos donde cada curva es máxima y muestra el gráfico. No escribe archivos.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### 06_prediccion_agosto.py

Toma del estudio de Optuna el trial de mayor valor, entrena 70 modelos LightGBM (uno por semilla) con 202103 a 202106 sobre todas las columnas _rank y _zero y predice 202108. Guarda una columna de probabilidad por semilla en predicciones_agosto_exp4.parquet.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–17] Importa gc, time, lightgbm, numpy, optuna y pandas. Define las rutas de la base de
#   Optuna, del dataset parquet y de la salida predicciones_agosto_exp4.parquet, y el nombre del estudio
#   (exp_4_lgbm_sss) con su base SQLite (optimization_lgbm_4.db).
# -*- coding: utf-8 -*-
import gc
import time
import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

# --- CONFIGURACIÓN DE RUTAS Y CONSTANTES ---
db_path = "/home/laura/...(modificar).../DMEyF/db/"
dataset_path = (
    "/home/laura/...(modificar).../DMEyF/datos/competencia_01_exp4.parquet"
)
pred_agosto_path = "/home/laura/----(modificar).../DMEyF/competencia01/predicciones_agosto_exp4.parquet"

study_name = "exp_4_lgbm_sss"
storage_name = "sqlite:///" + db_path + "optimization_lgbm_4.db"

# [Anotación · líneas 19–92] Lista de 70 semillas escritas a mano. Las primeras 20 son las de
#   04_validacion_junio.py; siguen 50 más.
# 20 semillas (5 asignadas + 15 más)
semillas = [
    # --- Tus 20 semillas originales ---
    777781,
    500041,
    600011,
    800077,
    200023,
    388890,
    1555565,
    790126,
    250020,
    1000085,
    512386,
    300005,
    1200025,
    612356,
    400038,
    1600157,
    812422,
    100011,
    400049,
    212368,
    111111,
    222222,
    333333,
    444444,
    555555,
    666666,
    777777,
    888888,
    999999,
    123789,
    456123,
    789456,
    321654,
    987321,
    654987,
    112233,
    445566,
    778899,
    102030,
    405060,
    708090,
    152637,
    485960,
    718293,
    142536,
    475869,
    708192,
    132435,
    465768,
    798091,
    246810,
    135792,
    864209,
    975318,
    192837,
    465870,
    791827,
    364554,
    829103,
    506172,
    617283,
    728394,
    839405,
    940516,
    151617,
    262728,
    373839,
    484950,
    596071,
    607182,
]


# [Anotación · líneas 95–114] Carga el estudio de Optuna, se queda con los trials completos, los ordena por
#   valor descendente y toma el primero. Lee su best_iter (corta con ValueError si no está guardado) e imprime
#   el número de trial, su ganancia en la validación cruzada y best_iter.
# --- 1. CARGA DE OPTUNA & RECUPERACIÓN DEL MEJOR TRIAL ---
print("Conectando a Optuna para recuperar el mejor trial...")
study = optuna.load_study(study_name=study_name, storage=storage_name)

completed_trials = [
    t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE
]
completed_trials.sort(key=lambda t: t.value, reverse=True)
best_trial = completed_trials[0]

best_iter = best_trial.user_attrs.get("best_iter", None)
if best_iter is None:
  raise ValueError(
      f"El trial #{best_trial.number} no tiene 'best_iter' guardado en"
      " user_attrs."
  )

print(f" -> Mejor trial ID: {best_trial.number}")
print(f" -> Ganancia en CV del mejor trial: ${best_trial.value:,.0f}")
print(f" -> Mejor cantidad de iteraciones (best_iter): {best_iter}")

# [Anotación · líneas 116–127] Arma los parámetros: objective binary, metric auc, gbdt, first_metric_only
#   True, boost_from_average True, feature_pre_filter False, max_bin 31, verbose −1, n_jobs 6, y les suma los
#   cinco hiperparámetros del trial elegido.
params_base = {
    "objective": "binary",
    "metric": "auc",
    "boosting_type": "gbdt",
    "first_metric_only": True,
    "boost_from_average": True,
    "feature_pre_filter": False,
    "max_bin": 31,
    "verbose": -1,
    "n_jobs": 6,
}
params_base.update(best_trial.params)

# [Anotación · líneas 129–169] Lee del parquet los meses 202103, 202104, 202105 y 202106 de a uno. Con el
#   primero define las variables: todas las columnas que terminan en _rank o _zero, sin excluir las de préstamos
#   personales. Para cada mes crea la clase binaria (1 = BAJA+2), pasa variables y clase a matrices float32 y,
#   al final, apila los cuatro meses en X_train_final e y_train_final.
# --- 2. CARGA FRACCIONADA MES A MES (Con préstamos incluidos) ---
print(
    "\nCargando datos de entrenamiento mes a mes con préstamos (Marzo a"
    " Junio)..."
)
meses_train = [202103, 202104, 202105, 202106]
X_train_list = []
y_train_list = []
cols_features = None

for m in meses_train:
  print(f" -> Leyendo mes {m}...")
  df_m = pd.read_parquet(dataset_path, filters=[("foto_mes", "==", m)])

  if cols_features is None:
    # Seleccionamos TODOS los _rank y _zero SIN excluir préstamos
    cols_features = [
        c for c in df_m.columns if c.endswith("_rank") or c.endswith("_zero")
    ]
    print(
        f"    Cantidad total de variables seleccionadas (Rankings + Flags_Zeros e incluyo"
        f" préstamos): {len(cols_features)}"
    )

  clase_bin = np.where(df_m["clase_ternaria"] == "BAJA+2", 1, 0).astype(
      np.float32
  )

  X_train_list.append(df_m[cols_features].to_numpy(dtype=np.float32))
  y_train_list.append(clase_bin)

  del df_m
  gc.collect()

print("Concatenando matrices de entrenamiento...")
X_train_final = np.vstack(X_train_list)
y_train_final = np.concatenate(y_train_list)
del X_train_list, y_train_list
gc.collect()

print(f"Shape final X_train: {X_train_final.shape}")

# [Anotación · líneas 171–188] Lee las filas de 202108, arma la matriz de variables de agosto con las mismas
#   columnas y crea una tabla con numero_de_cliente donde se van a guardar las predicciones.
print("\nCargando datos de predicción de Agosto...")
agosto_raw = pd.read_parquet(
    dataset_path,
    filters=[("foto_mes", "==", 202108)],
)
cols_meta = ["numero_de_cliente", "foto_mes", "clase_ternaria"]
df_agosto = agosto_raw[
    [c for c in cols_meta if c in agosto_raw.columns] + cols_features
].copy()
X_agosto = df_agosto[cols_features].to_numpy(dtype=np.float32)

del agosto_raw
gc.collect()

# DataFrame base para almacenar el cliente y las predicciones individuales
df_preds_individuales = pd.DataFrame(
    {"numero_de_cliente": df_agosto["numero_de_cliente"]}
)

# [Anotación · líneas 190–216] Para cada una de las 70 semillas copia los parámetros, fija la semilla, entrena
#   un LightGBM con los cuatro meses durante best_iter iteraciones, predice agosto y guarda la probabilidad en
#   pred_seed_{semilla}. Mide e imprime el tiempo de cada semilla.
# --- 3. BUCLE MULTISEMILLA: ENTRENAMIENTO Y GUARDADO INDIVIDUAL ---
print(
    f"\nIniciando entrenamiento de {len(semillas)} modelos con train completo..."
)
tiempo_inicio_total = time.time()

for i, seed in enumerate(semillas, 1):
  tiempo_inicio_semilla = time.time()
  print(f" -> [{i}/{len(semillas)}] Entrenando con Semilla: {seed}...")

  params_seed = params_base.copy()
  params_seed["seed"] = seed

  train_data_final_lgb = lgb.Dataset(
      X_train_final, label=y_train_final, free_raw_data=True
  )
  final_model = lgb.train(
      params_seed, train_data_final_lgb, num_boost_round=best_iter
  )

  df_preds_individuales[f"pred_seed_{seed}"] = final_model.predict(X_agosto)

  tiempo_semilla = time.time() - tiempo_inicio_semilla
  print(f"    [OK] Semilla {seed} finalizada en {tiempo_semilla:.1f} segundos.")

  del final_model, train_data_final_lgb
  gc.collect()

# [Anotación · líneas 218–229] Escribe la tabla con numero_de_cliente y las 70 columnas de probabilidad en
#   predicciones_agosto_exp4.parquet e imprime el tiempo total.
# --- 4. GUARDADO DE RESULTADOS ---
print(
    "\nGuardando archivo Parquet con las predicciones de Agosto ..."
)
df_preds_individuales.to_parquet(pred_agosto_path, index=False)

tiempo_total = time.time() - tiempo_inicio_total
print("\n" + "=" * 50)
print("¡Proceso de predicción de Agosto finalizado!")
print(f"Tiempo total transcurrido: {tiempo_total / 60:.2f} minutos.")
print(f"Archivo guardado en: {pred_agosto_path}")
print("=" * 50)
```

### 03_optuna_LGBM.py

Busca hiperparámetros de LightGBM con Optuna (60 trials) sobre 202103 y 202104, con lgb.cv en 5 particiones aleatorias estratificadas y una métrica de ganancia. Guarda el estudio en una base SQLite que leen 04 y 06.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] Importa gc, time, lightgbm, numpy, optuna, pandas y StratifiedShuffleSplit.
#   También importa matplotlib, plotly, funciones de optuna.visualization y de scipy.stats (gaussian_kde,
#   ks_2samp), que no se usan en el resto del archivo.
# -*- coding: utf-8 -*-
"""
Optimizacion con Optuna + LightGBM 
"""

import gc
import time
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import optuna
from optuna.visualization import (
    plot_contour,
    plot_optimization_history,
    plot_param_importances,
    plot_slice,
)
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import gaussian_kde, ks_2samp
from sklearn.model_selection import StratifiedShuffleSplit

# [Anotación · líneas 25–42] Define la carpeta de la base de Optuna y lee competencia_01_exp4.parquet. Fija la
#   ganancia por acierto (1.072.500) y el costo por estímulo (27.500), los meses de entrenamiento (202103 y
#   202104) y mes_test = 202106. Con np.random.seed(777781) genera 50 semillas. Crea clase_binaria: 1 si
#   clase_ternaria es BAJA+2, 0 en el resto.
# 1. Leés tu archivo parquet actual
db_path = "/home/laura/----(modificar).../DMEyF/db/"
data = pd.read_parquet(
    "/home/laura/----(modificar).../DMEyF/datos/competencia_01_exp4.parquet"
)

ganancia_acierto = 1_072_500
costo_estimulo = 27_500

meses_train = [202103, 202104]
mes_test = 202106

# agregue sus semillas
semilla = 777781
np.random.seed(semilla)
semillas = np.random.choice(1000000, size=50, replace=False).tolist()

data["clase_binaria"] = np.where(data["clase_ternaria"] == "BAJA+2", 1, 0)

# [Anotación · líneas 44–70] Elige como variables las columnas que terminan en _rank o _zero y cuyo nombre no
#   empieza con mprestamos_personales ni cprestamos_personales. Filtra entrenamiento (202103 y 202104) y prueba
#   (202106) con esas columnas más las de control, y borra de memoria el dataset completo.
# ==============================================================================
# SELECCIÓN DE COLUMNAS: RANKINGS + FLAGS_ZEROS (Y EXCLUSIÓN DE COL.PRÉSTAMOS)
# ==============================================================================
# Identificar columnas que terminan en _rank o en _zero
cols_features = [
    c
    for c in data.columns
    if (c.endswith("_rank") or c.endswith("_zero"))
    and not c.startswith("mprestamos_personales")
    and not c.startswith("cprestamos_personales")
]

# Columnas de control necesarias
cols_meta = ["numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria"]

print(
    f"Cantidad de variables seleccionadas (Rankings + Flags_Zeros):"
    f" {len(cols_features)}"
)

# Filtrar train y test quedándonos solo con meta + las features elegidas
train_data = data[data["foto_mes"].isin(meses_train)][cols_meta + cols_features]
test_data = data[data["foto_mes"] == mes_test][cols_meta + cols_features]

# ¡PARA LA RAM: Borramos el dataframe gigante original y liberamos memoria
del data
gc.collect()

# [Anotación · líneas 72–87] Separa variables y clase de entrenamiento y de junio y crea los Dataset de
#   LightGBM. test_data_lgb, X_test, y_test_binaria e y_test_class no se usan en el resto del archivo.
# --- ENTRENAMIENTO ---
X_train = train_data[cols_features]
y_train_binaria = train_data["clase_binaria"]

# --- TEST / EVALUACIÓN ---
X_test = test_data[cols_features]
y_test_binaria = test_data["clase_binaria"]
y_test_class = test_data["clase_ternaria"]

# Crear Datasets de LightGBM (free_raw_data=True ahorra un 50% de RAM)
train_data_lgb = lgb.Dataset(
    X_train, label=y_train_binaria, free_raw_data=True
)
test_data_lgb = lgb.Dataset(
    X_test, label=y_test_binaria, reference=train_data_lgb, free_raw_data=True
)

# [Anotación · líneas 89–103] Crea un StratifiedShuffleSplit de 5 particiones con 30 % para validar. Define la
#   métrica gan_prob: suma 1.072.500 por cada positivo y −27.500 por cada negativo entre las filas con
#   probabilidad mayor o igual a 0,025 y divide el total por 0,3; se declara como métrica a maximizar.
# ==============================================================================
# EVALUACIÓN Y OPTUNA
# ==============================================================================
sss_opt = StratifiedShuffleSplit(
    n_splits=5, test_size=0.3, random_state=semillas[0]
)


def ganancia_prob_lgm(y_pred, data, prop=0.3):
  y_true = data.get_label()
  ganancia = (
      np.where(y_true == 1, ganancia_acierto, 0)
      - np.where(y_true == 0, costo_estimulo, 0)
  )
  return "gan_prob", ganancia[y_pred >= 0.025].sum() / prop, True


# [Anotación · líneas 106–130] Empieza la función objetivo de Optuna: propone num_leaves (8 a 100),
#   learning_rate (0,001 a 0,1), min_data_in_leaf (1 a 1000), feature_fraction (0,1 a 1,0) y bagging_fraction
#   (0,1 a 1,0). El resto queda fijo: objective binary, metric custom, gbdt, max_bin 31, feature_pre_filter
#   False, boost_from_average True, semilla = primera de las 50, n_jobs −1.
# hiperparametros para LGBM
def objective(trial):
  num_leaves = trial.suggest_int("num_leaves", 8, 100)
  learning_rate = trial.suggest_float("learning_rate", 0.001, 0.1)
  min_data_in_leaf = trial.suggest_int("min_data_in_leaf", 1, 1000)
  feature_fraction = trial.suggest_float("feature_fraction", 0.1, 1.0)
  bagging_fraction = trial.suggest_float("bagging_fraction", 0.1, 1.0)

  params = {
      "objective": "binary",
      "metric": "custom",
      "boosting_type": "gbdt",
      "first_metric_only": True,
      "boost_from_average": True,
      "feature_pre_filter": False,
      "max_bin": 31,
      "num_leaves": num_leaves,
      "learning_rate": learning_rate,
      "min_data_in_leaf": min_data_in_leaf,
      "feature_fraction": feature_fraction,
      "bagging_fraction": bagging_fraction,
      "seed": semillas[0],
      "verbose": -1,
      "n_jobs": -1,
  }

# [Anotación · líneas 132–152] Corre lgb.cv sobre el entrenamiento con las 5 particiones, hasta 3000
#   iteraciones y parada temprana de int(50 + 5/learning_rate) rondas, evaluando con gan_prob. Toma el máximo de
#   la ganancia media entre particiones, guarda en el trial la iteración donde ocurre (best_iter) y devuelve ese
#   máximo.
  cv_results = lgb.cv(
      params,
      train_data_lgb,
      num_boost_round=3000,
      callbacks=[
          lgb.early_stopping(
              stopping_rounds=int(50 + 5 / learning_rate), verbose=False
          )
      ],
      feval=ganancia_prob_lgm,
      folds=sss_opt.split(X_train, y_train_binaria),
      seed=semillas[0],
  )

  max_gan = max(cv_results["valid gan_prob-mean"])
  best_iter = cv_results["valid gan_prob-mean"].index(max_gan) + 1

  # Guardamos cual es la mejor iteración del modelo
  trial.set_user_attr("best_iter", best_iter)

  return max_gan


# [Anotación · líneas 155–163] Crea o reabre (load_if_exists=True) el estudio exp_4_lgbm_sss en la base SQLite
#   optimization_lgbm_4.db, con dirección maximizar.
storage_name = "sqlite:///" + db_path + "optimization_lgbm_4.db"
study_name = "exp_4_lgbm_sss"

study = optuna.create_study(
    direction="maximize",
    study_name=study_name,
    storage=storage_name,
    load_if_exists=True,
)

# [Anotación · líneas 165–180] Ejecuta 60 trials y muestra el tiempo transcurrido en segundos, minutos y, si
#   pasa de una hora, en horas.
# 1. Guardamos el tiempo de inicio
start_time = time.time()

# optimizo usando optuna
study.optimize(objective, n_trials=60)

elapsed_time = time.time() - start_time
minutos = elapsed_time / 60
horas = minutos / 60

# 4. Cálculo del tiempo de ejecución
print(f"\n--- TIEMPO DE EJECUCIÓN ---")
print(f"Segundos: {elapsed_time:.2f}")
print(f"Minutos:  {minutos:.2f}")
if horas >= 1:
  print(f"Horas:    {horas:.2f}")
```

### 02_limpieza_fe.py

Lee competencia_01.csv, pone en NaN ccajas_depositos de 202105, imputa nulos, agrega lags, delta y ratio, calcula el rank de cero fijo por mes y las banderas _zero, y guarda todo en competencia_01_exp4.parquet.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–11] Importa gc, numpy y pandas. Define la carpeta de datos, el archivo de entrada
#   competencia_01.csv y la salida competencia_01_exp4.parquet, y lee el CSV completo con pandas.
# -*- coding: utf-8 -*-
"""Limpieza + Lags/Deltas + Ranking + imputacion faltantes + flags para ceros"""

import gc
import numpy as np
import pandas as pd

dataset_path = "/home/laura/----(modificar).../DMEyF/datos/"
dataset_file = "competencia_01.csv"
output_path = ("/home/laura/----(modificar).../DMEyF/datos/competencia_01_exp4.parquet")
data = pd.read_csv(dataset_path + dataset_file)

# [Anotación · líneas 13–15] Copia el dataset y asigna NaN a ccajas_depositos en las filas de 202105.
# 1. NaN en la columna ccajas_depositos de Mayo
data_1 = data.copy()
data_1.loc[data_1["foto_mes"] == 202105, "ccajas_depositos"] = np.nan


# [Anotación · líneas 18–47] Define imputacion_general_dataset y la aplica. Ordena por cliente y mes y, para
#   cada columna salvo numero_de_cliente, foto_mes, clase_ternaria, cliente_vip e internet, toma el valor del
#   registro anterior y del siguiente del mismo cliente; donde el valor es nulo y ambos vecinos no lo son, lo
#   reemplaza por el promedio de los dos. El resultado queda en data_limpia.
# 2. Imputación general con promedio entre mes siguiente y mes previo
def imputacion_general_dataset(df, cols_excluir=None):
  if cols_excluir is None:
    cols_excluir = [
        "numero_de_cliente",
        "foto_mes",
        "clase_ternaria",
        "cliente_vip",
        "internet",
    ]

  df_clean = df.copy()
  df_clean = df_clean.sort_values(
      by=["numero_de_cliente", "foto_mes"]
  ).reset_index(drop=True)
  cols_a_imputar = [c for c in df_clean.columns if c not in cols_excluir]

  print(f"Procesando {len(cols_a_imputar)} variables para interpolación...")
  for col in cols_a_imputar:
    lag = df_clean.groupby("numero_de_cliente")[col].shift(1)
    lead = df_clean.groupby("numero_de_cliente")[col].shift(-1)
    mask_nan = df_clean[col].isnull() & lag.notnull() & lead.notnull()
    if mask_nan.sum() > 0:
      df_clean.loc[mask_nan, col] = (lag[mask_nan] + lead[mask_nan]) / 2.0

  print("¡Limpieza completa!")
  return df_clean


data_limpia = imputacion_general_dataset(data_1)


# [Anotación · líneas 50–75] Empieza agregar_lags_y_deltas_por_bloques: ordena por cliente y mes, pasa las
#   columnas float64 a float32, arma la lista de variables (todas salvo las mismas cinco columnas excluidas) e
#   inicia la lista de resultados con el dataset base.
# 3. Creación de columnas con deltas y lags por bloques
def agregar_lags_y_deltas_por_bloques(
    df, cols_excluir=None, batch_size=20, eps=1e-5
):
  if cols_excluir is None:
    cols_excluir = [
        "numero_de_cliente",
        "foto_mes",
        "clase_ternaria",
        "cliente_vip",
        "internet",
    ]

  df_base = df.sort_values(by=["numero_de_cliente", "foto_mes"]).reset_index(
      drop=True
  )
  cols_float = df_base.select_dtypes(include=["float64"]).columns
  df_base[cols_float] = df_base[cols_float].astype("float32")

  cols_features = [c for c in df_base.columns if c not in cols_excluir]
  print(
      f"Calculando lags y deltas para {len(cols_features)} variables en bloques"
      f" de {batch_size}..."
  )

  lista_df_resultados = [df_base]

# [Anotación · líneas 77–108] Recorre las variables en bloques de 20. Para cada una calcula lag1 y lag2 (valor
#   del registro anterior y del segundo anterior del mismo cliente), delta1 (valor menos lag1) y ratio1 ((valor
#   − lag1) dividido por |lag1| + 0,00001). Cada bloque se guarda como float32 y al final se concatena todo por
#   columnas. Se aplica a data_limpia y deja data_completa.
  for i in range(0, len(cols_features), batch_size):
    batch_cols = cols_features[i : i + batch_size]
    dict_batch = {}

    for col in batch_cols:
      dict_batch[f"{col}_lag1"] = df_base.groupby("numero_de_cliente")[
          col
      ].shift(1)
      dict_batch[f"{col}_lag2"] = df_base.groupby("numero_de_cliente")[
          col
      ].shift(2)

    for col in batch_cols:
      lag1 = dict_batch[f"{col}_lag1"]
      dict_batch[f"{col}_delta1"] = df_base[col] - lag1
      dict_batch[f"{col}_ratio1"] = (df_base[col] - lag1) / (
          np.abs(lag1) + eps
      )

    df_batch = pd.DataFrame(dict_batch, index=df_base.index).astype("float32")
    lista_df_resultados.append(df_batch)
    del dict_batch, df_batch
    gc.collect()

  df_final = pd.concat(lista_df_resultados, axis=1)
  del lista_df_resultados
  gc.collect()
  print(f"¡Lags y deltas listos! Forma actual: {df_final.shape}")
  return df_final


data_completa = agregar_lags_y_deltas_por_bloques(data_limpia, batch_size=20)


# [Anotación · líneas 111–138] Empieza agregar_ranking_cero_fijo_por_bloques: pasa float64 a float32 y arma la
#   lista de columnas a rankear: las numéricas que no están entre las cinco excluidas y cuyo nombre no termina
#   en _zero (variables originales, lag1, lag2, delta1 y ratio1).
# 4. Creación del ranking de cero fijo mes a mes
def agregar_ranking_cero_fijo_por_bloques(df, cols_excluir=None, batch_size=20):
  if cols_excluir is None:
    cols_excluir = [
        "numero_de_cliente",
        "foto_mes",
        "clase_ternaria",
        "cliente_vip",
        "internet",
    ]

  cols_float = df.select_dtypes(include=["float64"]).columns
  if len(cols_float) > 0:
    df[cols_float] = df[cols_float].astype("float32")

  cols_features = [
      c
      for c in df.columns
      if c not in cols_excluir
      and not c.endswith("_zero")
      and pd.api.types.is_numeric_dtype(df[c])
  ]
  print(
      f"Calculando ranking de cero fijo para {len(cols_features)} variables en"
      f" bloques de {batch_size}..."
  )

  lista_df_resultados = [df]

# [Anotación · líneas 140–177] En bloques de 20 columnas crea {columna}_rank. La serie arranca en 0 y, dentro
#   de cada foto_mes, los valores positivos reciben su rank percentil entre los positivos del mes y los
#   negativos reciben, con signo menos, el rank percentil de su valor absoluto entre los negativos del mes;
#   ceros y nulos quedan en 0. Concatena los bloques y deja data_con_ranks.
  for i in range(0, len(cols_features), batch_size):
    batch_cols = cols_features[i : i + batch_size]
    dict_batch = {}

    for col in batch_cols:
      serie_rank = pd.Series(0.0, index=df.index, dtype="float32")
      for mes, idx_mes in df.groupby("foto_mes").groups.items():
        sub_datos = df.loc[idx_mes, col]

        mask_pos = sub_datos > 0
        if mask_pos.any():
          serie_rank.loc[idx_mes[mask_pos]] = (
              sub_datos[mask_pos].rank(pct=True).astype("float32")
          )

        mask_neg = sub_datos < 0
        if mask_neg.any():
          serie_rank.loc[idx_mes[mask_neg]] = (
              -(sub_datos[mask_neg].abs().rank(pct=True))
          ).astype("float32")

      dict_batch[f"{col}_rank"] = serie_rank

    df_batch = pd.DataFrame(dict_batch, index=df.index).astype("float32")
    lista_df_resultados.append(df_batch)
    del dict_batch, df_batch
    gc.collect()

  df_final = pd.concat(lista_df_resultados, axis=1)
  del lista_df_resultados
  gc.collect()
  print(f"¡Ranking completo! shape actual: {df_final.shape}")
  return df_final


data_con_ranks = agregar_ranking_cero_fijo_por_bloques(
    data_completa, batch_size=20
)


# [Anotación · líneas 180–216] Define agregar_variables_zero_final y la aplica. Para cada variable numérica de
#   data_limpia (las originales, sin las cinco excluidas) crea {columna}_zero: 1 si el valor es 0, NaN si el
#   valor es nulo y 0 en el resto. Las agrega al dataset con los ranks y deja data_final.
# 5. Agregar las banderas _zero SOLAMENTE sobre las variables numéricas originales
def agregar_variables_zero_final(df, cols_excluir=None):
  if cols_excluir is None:
    cols_excluir = [
        "numero_de_cliente",
        "foto_mes",
        "clase_ternaria",
        "cliente_vip",
        "internet",
    ]

  cols_base_numericas = [
      c
      for c in data_limpia.columns
      if c not in cols_excluir and pd.api.types.is_numeric_dtype(data_limpia[c])
  ]
  print(
      f"Agregando banderas _zero estáticas solo para"
      f" {len(cols_base_numericas)} variables base numéricas..."
  )

  dict_zero = {}
  for col in cols_base_numericas:
    s = data_limpia[col]
    zero_col = pd.Series(0.0, index=df.index, dtype="float32")
    zero_col[s.isna()] = np.nan
    zero_col[s == 0] = 1.0
    dict_zero[f"{col}_zero"] = zero_col

  df_final = pd.concat([df, pd.DataFrame(dict_zero, index=df.index)], axis=1)
  del dict_zero
  gc.collect()
  print(f"¡Feature Engineering completo! Forma final: {df_final.shape}")
  return df_final


data_final = agregar_variables_zero_final(data_con_ranks)

# [Anotación · líneas 218–220] Guarda data_final en competencia_01_exp4.parquet e imprime la ruta.
# Guardar dataset final
data_final.to_parquet(output_path, index=False)
print(f"¡Dataset guardado exitosamente en: {output_path}")
```

### 07_cortes_media.py

Lee predicciones_agosto_exp4.parquet, promedia las probabilidades de todas las semillas, ordena de mayor a menor y escribe en un CSV sin encabezado los numero_de_cliente de las primeras CORTE filas.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Importa os y pandas. Define la ruta de predicciones_agosto_exp4.parquet y la del
#   CSV de salida (exp4/media/agosto_media_70_sem_10k.csv), fija CORTE = 1000 con el comentario «ir cambiando el
#   valor de corte» y crea la carpeta de salida si no existe.
# -*- coding: utf-8 -*-
import os
import pandas as pd

# --- RUTAS ---
pred_agosto_path = "/home/laura/...(modificar).../DMEyF/competencia01/predicciones_agosto_exp4.parquet"
csv_salida_path = ("/home/laura/...(modificar).../DMEyF/competencia01/exp4/media/agosto_media_70_sem_10k.csv")

#ir cambiando el valor de corte
CORTE = 1000

# Creamos la carpeta de salida si no existe
os.makedirs(os.path.dirname(csv_salida_path), exist_ok=True)

# [Anotación · líneas 15–25] Lee el parquet de predicciones de agosto, identifica las columnas que empiezan
#   con pred_seed_ e interrumpe con ValueError si no hay ninguna.
print("Cargando predicciones individuales de las 70 semillas (.parquet)...")
df_preds = pd.read_parquet(pred_agosto_path)

# Identificamos todas las columnas de semillas
cols_semillas = [c for c in df_preds.columns if c.startswith("pred_seed_")]
print(f"Cantidad de semillas encontradas para ensamble: {len(cols_semillas)}")

if len(cols_semillas) == 0:
  raise ValueError(
      "No se encontraron columnas que empiecen con 'pred_seed_' en el archivo."
  )

# [Anotación · líneas 27–29] Calcula prob_ensemble como el promedio por fila de todas las columnas pred_seed_.
# --- PROMEDIAR LAS PROBABILIDADES (Ensemble) ---
print("Calculando la media de las probabilidades de todas las semillas...")
df_preds["prob_ensemble"] = df_preds[cols_semillas].mean(axis=1)

# [Anotación · líneas 31–39] Ordena por prob_ensemble descendente y se queda con numero_de_cliente de las
#   primeras CORTE filas.
# --- ORDENAR Y APLICAR EL CORTE ---
print(f"Ordenando y seleccionando los mejores {CORTE} clientes...")

df_sorted = df_preds.sort_values(by="prob_ensemble", ascending=False).reset_index(
    drop=True
)

# Nos quedamos estrictamente con los primeros CORTE clientes
df_envio = df_sorted.head(CORTE)[["numero_de_cliente"]].copy()

# [Anotación · líneas 41–48] Escribe esos numero_de_cliente en el CSV, sin índice ni encabezado, e imprime la
#   ruta y la cantidad de clientes.
# --- GUARDAR ARCHIVO ---
df_envio.to_csv(csv_salida_path, index=False, header=False)

print("\n" + "=" * 50)
print(f"¡CSV de envío final generado en:")
print(f"{csv_salida_path}")
print(f"Total de clientes seleccionados: {len(df_envio)}")
print("=" * 50)
```

### 04_validacion_junio.py

Entrena con 202103 y 202104 usando los hiperparámetros del estudio de Optuna y predice 202106 con 20 semillas. Guarda las probabilidades por semilla en pred_junio_exp4.parquet, que lee 05_curvas_ganancia.py; 06 y 07 no leen esa salida.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–14] Importa gc, lightgbm, numpy, optuna y pandas. Define las rutas del dataset
#   parquet, de la salida pred_junio_exp4.parquet y de la carpeta de la base de Optuna.
# -*- coding: utf-8 -*-

import gc
import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

# --- CONFIGURACIÓN de paths---
dataset_path = (
    "/home/laura/----(modificar).../DMEyF/datos/competencia_01_exp4.parquet"
)
output_path = "/home/laura/----(modificar).../DMEyF/competencia01/pred_junio_exp4.parquet"
db_path = "/home/laura/----(modificar).../DMEyF/db/"


# [Anotación · líneas 17–46] Lista de 20 semillas escritas a mano (el comentario dice 5 asignadas + 15 más).
#   Define cols_a_excluir, que no se usa en el resto del archivo.
# 20 semillas (5 asignadas + 15 más)
semillas = [
    777781,
    500041,
    600011,
    800077,
    200023,
    388890,
    1555565,
    790126,
    250020,
    1000085,
    512386,
    300005,
    1200025,
    612356,
    400038,
    1600157,
    812422,
    100011,
    400049,
    212368,
]

cols_a_excluir = [
    "clase_ternaria",
    "clase_binaria",
    "numero_de_cliente",
    "foto_mes",
]

# [Anotación · líneas 48–75] Carga el estudio exp_4_lgbm_sss de optimization_lgbm_4.db y toma
#   study.best_params y el best_iter guardado en el trial de mayor valor (1000 si no está). Si la carga da error
#   usa valores por defecto: num_leaves 31, learning_rate 0,02, min_data_in_leaf 200, feature_fraction 0,5,
#   bagging_fraction 1,0 y 500 iteraciones.
# --- RECUPERAR EL MEJOR MODELO Y PARÁMETROS DESDE OPTUNA ---
storage_name = "sqlite:///" + db_path + "optimization_lgbm_4.db"
study_name = "exp_4_lgbm_sss"

try:
  study = optuna.load_study(study_name=study_name, storage=storage_name)
  best_params_optuna = study.best_params
  # Recuperamos la mejor iteración guardada en los atributos del mejor trial
  best_iter_optuna = study.best_trial.user_attrs.get("best_iter", 1000)

  print(f"\n[Optuna] ¡Configuración óptima recuperada con éxito!")
  print(f" -> Mejor ganancia en CV: ${study.best_value:,.0f}")
  print(f" -> Mejores hiperparámetros: {best_params_optuna}")
  print(f" -> Mejor cantidad de árboles (best_iter): {best_iter_optuna}")

except Exception as e:
  print(
      f"\n[Aviso] No se pudo cargar el estudio de Optuna ({e}). Usando valores"
      " por defecto."
  )
  best_params_optuna = {
      "num_leaves": 31,
      "learning_rate": 0.02,
      "min_data_in_leaf": 200,
      "feature_fraction": 0.5,
      "bagging_fraction": 1.0,
  }
  best_iter_optuna = 500

# [Anotación · líneas 77–114] Lee del parquet sólo 202103, 202104 y 202106 y crea clase_binaria (1 = BAJA+2).
#   Elige las columnas _rank y _zero sin las que empiezan con mprestamos_personales o cprestamos_personales.
#   Arma el entrenamiento con 202103 y 202104, las variables de 202106 y una tabla de resultados con
#   numero_de_cliente, clase_ternaria y clase_binaria de junio. Libera memoria.
# --- 1. CARGA OPTIMIZADA DE DATOS (Marzo, Abril y Junio) ---
print("\n[1/2] Cargando datos de validación (Marzo, Abril y Junio)...")
data = pd.read_parquet(
    dataset_path, filters=[("foto_mes", "in", [202103, 202104, 202106])]
)
data["clase_binaria"] = np.where(data["clase_ternaria"] == "BAJA+2", 1, 0)

# Selección exclusiva de Rankings + Zeros (excluyendo préstamos personales)
cols_features = [
    c
    for c in data.columns
    if (c.endswith("_rank") or c.endswith("_zero"))
    and not c.startswith("mprestamos_personales")
    and not c.startswith("cprestamos_personales")
]

cols_meta = ["numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria"]
print(
    f"Cantidad de variables seleccionadas (Rankings + Zeros sin préstamos):"
    f" {len(cols_features)}"
)

train_mask = data["foto_mes"].isin([202103, 202104])
test_mask = data["foto_mes"] == 202106

train_data = data.loc[train_mask, cols_meta + cols_features]
test_data = data.loc[test_mask, cols_meta + cols_features]

X_train = train_data[cols_features]
y_train = train_data["clase_binaria"]
X_junio = test_data[cols_features]

df_resultados = test_data[
    ["numero_de_cliente", "clase_ternaria", "clase_binaria"]
].copy()

del data, train_data, test_data
gc.collect()

# [Anotación · líneas 116–134] Fija ganancia por acierto (1.072.500) y costo por estímulo (27.500). Define
#   calcular_ganancia_array: ordena por probabilidad descendente, toma la primera fracción prop de las filas
#   (0,3 por defecto) y suma 1.072.500 por cada positivo y −27.500 por cada otro caso.
# --- 2. BUCLE SEGURO POR CADA SEMILLA ---
print(
    f"\n[2/2] Entrenando modelo y prediciendo para {len(semillas)} semillas..."
)

ganancia_acierto = 1_072_500
costo_estimulo = 27_500


def calcular_ganancia_array(y_true, y_pred, prop=0.3):
  df_temp = pd.DataFrame({"y_true": y_true, "y_pred": y_pred})
  df_temp = df_temp.sort_values(by="y_pred", ascending=False)
  n_estimulos = int(len(df_temp) * prop)
  enviados = df_temp.iloc[:n_estimulos]
  ganancia_total = np.where(
      enviados["y_true"] == 1, ganancia_acierto, -costo_estimulo
  ).sum()
  return ganancia_total


# [Anotación · líneas 136–176] Para cada una de las 20 semillas arma los parámetros (binary, metric auc, gbdt,
#   max_bin 31, los cinco hiperparámetros de Optuna, la semilla, n_jobs 6), entrena con 202103 y 202104 durante
#   best_iter iteraciones, predice junio y guarda la probabilidad en la columna pred_seed_{semilla}. Calcula la
#   ganancia de esa semilla con prop = 0,3 y la agrega a una lista que no se imprime ni se guarda.
ganancias_por_semilla = []

for i, seed in enumerate(semillas, 1):
  print(f" -> [{i}/{len(semillas)}] Entrenando con semilla: {seed}...")

  # Armamos el diccionario combinando la estructura fija con los hiperparámetros de Optuna
  params = {
      "objective": "binary",
      "metric": "auc",
      "boosting_type": "gbdt",
      "first_metric_only": True,
      "boost_from_average": True,
      "feature_pre_filter": False,
      "max_bin": 31,
      # Hiperparámetros optimizados dinámicamente por Optuna:
      "num_leaves": int(best_params_optuna.get("num_leaves", 31)),
      "learning_rate": float(best_params_optuna.get("learning_rate", 0.02)),
      "min_data_in_leaf": int(best_params_optuna.get("min_data_in_leaf", 200)),
      "feature_fraction": float(best_params_optuna.get("feature_fraction", 0.5)),
      "bagging_fraction": float(best_params_optuna.get("bagging_fraction", 1.0)),
      "seed": seed,
      "verbose": -1,
      "n_jobs": 6,
  }

  train_data_lgb = lgb.Dataset(X_train, label=y_train, free_raw_data=True)

  # Usamos el best_iter exacto que arrojó el estudio de Optuna
  model_val = lgb.train(params, train_data_lgb, num_boost_round=best_iter_optuna)

  preds = model_val.predict(X_junio)
  df_resultados[f"pred_seed_{seed}"] = preds

  # Calculamos ganancia individual por semilla
  ganancia_semilla = calcular_ganancia_array(
      df_resultados["clase_binaria"].values, preds, prop=0.3
  )
  ganancias_por_semilla.append(ganancia_semilla)

  del model_val, train_data_lgb
  gc.collect()

# [Anotación · líneas 178–183] Escribe la tabla de junio con las 20 columnas de probabilidad en
#   pred_junio_exp4.parquet e imprime el aviso final.
# --- 3. GUARDAR RESULTADOS A DISCO ---
df_resultados.to_parquet(output_path, index=False)
print("\n" + "=" * 50)
print("¡PValidacion multisemilla de Junio finalizado!")
print(f"Archivo guardado en: {output_path}")
print("=" * 50)
```

### 01_target.py

Calcula clase_ternaria con una consulta SQL en DuckDB sobre competencia_01_crudo.csv y guarda el resultado en competencia_01.csv. Imprime la cantidad de clientes por mes y clase.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–11] Importa os, duckdb y pandas. Define la carpeta de datos
#   (/home/laura/(modificar)/DMEyF/datos/), el archivo de entrada competencia_01_crudo.csv y el de salida
#   competencia_01.csv, y arma las rutas completas.
import os
import duckdb
import pandas as pd

# 1. Definir rutas (modificar path)
dataset_path = "/home/laura/(modificar)/DMEyF/datos/"
dataset_filename = "competencia_01_crudo.csv"
output_filename = "competencia_01.csv"

file_path = os.path.join(dataset_path, dataset_filename)
output_path = os.path.join(dataset_path, output_filename)

# [Anotación · líneas 13–16] Abre una base DuckDB en memoria e imprime un aviso de inicio.
# 2. Inicializar conexión a DuckDB
con = duckdb.connect(database=":memory:")

print("Cargando dataset crudo y calculando la clase ternaria...")

# [Anotación · líneas 18–29] Inicia la consulta que crea la tabla competencia_01. Lee del CSV crudo los meses
#   distintos y los clientes distintos y arma todas las combinaciones cliente–mes (CROSS JOIN).
# 3. Ejecutar la query para crear la tabla con la clase ternaria
con.execute(f"""
    CREATE OR REPLACE TABLE competencia_01 AS
    WITH periodos AS (
        SELECT DISTINCT foto_mes FROM read_csv_auto('{file_path}')
    ),
    clientes AS (
        SELECT DISTINCT numero_de_cliente FROM read_csv_auto('{file_path}')
    ),
    todo AS (
        SELECT numero_de_cliente, foto_mes FROM clientes CROSS JOIN periodos
    ),
# [Anotación · líneas 30–44] Une esas combinaciones con el CSV crudo (LEFT JOIN) y define mes_0 = 1 si el
#   cliente tiene registro en ese mes y 0 si no. Con LEAD toma esa misma marca un mes y dos meses adelante
#   (mes_1 y mes_2) y asigna clase_ternaria: BAJA+1 si está en el mes y no en el siguiente; BAJA+2 si está en el
#   mes y en el siguiente y no dos meses después; CONTINUA si está en los tres; NULL en cualquier otro caso.
    clase_ternaria AS (
        SELECT
            c.*
            , IF(c.numero_de_cliente IS NULL, 0, 1) AS mes_0
            , LEAD(mes_0, 1) OVER (PARTITION BY t.numero_de_cliente ORDER BY foto_mes) AS mes_1
            , LEAD(mes_0, 2) OVER (PARTITION BY t.numero_de_cliente ORDER BY foto_mes) AS mes_2
            , CASE
                WHEN mes_0 = 1 AND mes_1 = 0 THEN 'BAJA+1'
                WHEN mes_0 = 1 AND mes_1 = 1 AND mes_2 = 0 THEN 'BAJA+2'
                WHEN mes_0 = 1 AND mes_1 = 1 AND mes_2 = 1 THEN 'CONTINUA'
                ELSE NULL
              END AS clase_ternaria
        FROM todo t
        LEFT JOIN read_csv_auto('{file_path}') c USING (numero_de_cliente, foto_mes)
    )
# [Anotación · líneas 45–48] Conserva sólo las filas en que el cliente tiene registro (mes_0 = 1) y quita las
#   columnas auxiliares mes_0, mes_1 y mes_2.
    SELECT * EXCLUDE (mes_0, mes_1, mes_2)
    FROM clase_ternaria
    WHERE mes_0 = 1
""")

# [Anotación · líneas 50–55] Exporta la tabla competencia_01 a competencia_01.csv con encabezado.
print(f"Guardando el resultado procesado en '{output_path}'...")

# 4. Exportar la tabla resultante a un nuevo archivo CSV
con.execute(f"""
    COPY competencia_01 TO '{output_path}' (FORMAT CSV, HEADER)
""")

# [Anotación · líneas 57–73] Cuenta clientes por foto_mes y por valor de clase_ternaria con PIVOT, dejando
#   afuera 202108, y muestra la tabla por pantalla.
# 5. Generar y mostrar por pantalla la tabla pivoteada de control
print("\n--- Distribución de la Clase Ternaria por Mes ---")
df_pivot = con.execute("""

PIVOT (
    SELECT *
    FROM competencia_01
    WHERE foto_mes != 202108
)
ON clase_ternaria
USING count(numero_de_cliente)
GROUP BY foto_mes
ORDER BY foto_mes;
""").fetchdf()

print(df_pivot)
print("\n¡Listo!")
```

### 05_curvas_ganancia.py

Lee pred_junio_exp4.parquet, calcula la curva de ganancia acumulada de junio para cada una de las 20 semillas y para su promedio, imprime la cantidad de envíos donde cada curva es máxima y muestra el gráfico. No escribe archivos.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–17] Importa matplotlib, numpy y pandas. Define la ruta de pred_junio_exp4.parquet, la
#   ganancia por acierto (1.072.500), el costo por estímulo (27.500) y las mismas 20 semillas de
#   04_validacion_junio.py.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Ruta al archivo multisemilla que acabamos de generar
multisemilla_path = ("/home/laura/...(modificar).../DMEyF/competencia01/pred_junio_exp4.parquet")

ganancia_acierto = 1_072_500
costo_estimulo = 27_500
semillas = [
    777781, 500041, 600011, 800077, 200023, 
    388890, 1555565, 790126, 250020, 1000085, 
    512386, 300005, 1200025, 612356, 400038, 
    1600157, 812422, 100011, 400049, 212368
]


# [Anotación · líneas 20–27] Lee el parquet de predicciones de junio, abre una figura de 12 × 7 y crea el
#   diccionario picos_optimos.
# 1. Cargar el archivo
print("Cargando predicciones multisemilla...")
df = pd.read_parquet(multisemilla_path)

plt.figure(figsize=(12, 7))

# Diccionario para guardar los picos óptimos de cada semilla
picos_optimos = {}

# [Anotación · líneas 29–62] Para cada semilla ordena los clientes de junio por su probabilidad descendente,
#   asigna 1.072.500 a cada BAJA+2 y −27.500 al resto y acumula. Busca la posición donde la ganancia acumulada
#   es máxima, guarda e imprime esa cantidad de envíos y esa ganancia, y dibuja la curva en millones.
# 2. Iterar por cada semilla, calcular su curva y graficarla
for seed in semillas:
    col_pred = f"pred_seed_{seed}"

    # Ordenar de mayor a menor probabilidad para esta semilla
    df_sorted = df.sort_values(by=col_pred, ascending=False).reset_index(
        drop=True
    )

    # Ganancia acumulada
    df_sorted["ganancia_ind"] = np.where(
        df_sorted["clase_binaria"] == 1, ganancia_acierto, -costo_estimulo
    )
    df_sorted["ganancia_acum"] = df_sorted["ganancia_ind"].cumsum()

    # Encontrar pico
    pico_idx = df_sorted["ganancia_acum"].idxmax()
    n_optimo = pico_idx + 1
    ganancia_max = df_sorted.loc[pico_idx, "ganancia_acum"]
    picos_optimos[seed] = (n_optimo, ganancia_max)

    print(
        f"Semilla {seed}: N* óptimo = {n_optimo:,} envíos | Ganancia Máxima ="
        f" ${ganancia_max:,.0f}"
    )

    # Graficar curva tenue para esta semilla
    plt.plot(
        df_sorted.index + 1,
        df_sorted["ganancia_acum"] / 1e6,
        alpha=0.4,
        linewidth=1.2,
        label=f"Semilla {seed} (N*={n_optimo:,})",
    )

# [Anotación · líneas 64–85] Promedia las 20 probabilidades por cliente (pred_promedio), repite el
#   ordenamiento y la ganancia acumulada con ese promedio e imprime la cantidad de envíos del máximo y la
#   ganancia máxima.
# 3. Calcular y graficar el PROMEDIO de las predicciones (estrategia de ensembling)
cols_preds = [f"pred_seed_{s}" for s in semillas]
df["pred_promedio"] = df[cols_preds].mean(axis=1)

df_prom_sorted = df.sort_values(by="pred_promedio", ascending=False).reset_index(
    drop=True
)
df_prom_sorted["ganancia_ind"] = np.where(
    df_prom_sorted["clase_binaria"] == 1, ganancia_acierto, -costo_estimulo
)
df_prom_sorted["ganancia_acum"] = df_prom_sorted["ganancia_ind"].cumsum()

pico_prom_idx = df_prom_sorted["ganancia_acum"].idxmax()
n_optimo_prom = pico_prom_idx + 1
ganancia_max_prom = df_prom_sorted.loc[pico_prom_idx, "ganancia_acum"]

print("=" * 60)
print(
    f" PROMEDIO DE SEMILLAS: N* óptimo = {n_optimo_prom:,} envíos | Ganancia"
    f" Máxima = ${ganancia_max_prom:,.0f}"
)
print("=" * 60)

# [Anotación · líneas 87–120] Dibuja la curva del promedio en negro con línea punteada y da formato al
#   gráfico: título, ejes, eje X de 0 a 25.000 clientes con marcas cada 2.500, eje Y de −50 a 500 millones,
#   grilla y leyenda. Muestra el gráfico en pantalla.
# Graficar la curva del promedio bien marcada en negro/rojo
plt.plot(
    df_prom_sorted.index + 1,
    df_prom_sorted["ganancia_acum"] / 1e6,
    color="black",
    linewidth=2.5,
    linestyle="--",
    label=f"PROMEDIO (N*={n_optimo_prom:,})",
)

# 4. Formato del gráfico con zoom en el Eje Y
plt.title(
    "Curvas de Ganancia Acumulada - Múltiples Semillas vs Promedio (Junio"
    " 2021)",
    fontsize=14,
    pad=12,
)
plt.xlabel("Cantidad de Clientes Estimulados (Ordenados por Score)", fontsize=11)
plt.ylabel("Ganancia Acumulada en Millones de $", fontsize=11)

# --- ACÁ AJUSTAMOS LAS ESCALAS PARA QUE SE VEA PERFECTO ---
plt.xlim(0, 25000)  # Zoom en el eje X (de 0 a 25.000 clientes)
plt.ylim(
    -50, 500
)  # Zoom en el eje Y (de -50M a 450M para apreciar el pico de las curvas)
# ---------------------------------------------------------

plt.grid(True, linestyle="--", alpha=0.6)
plt.legend(fontsize=9, loc="lower right")
plt.tight_layout()
# Definir marcas en el eje X cada 2,500 clientes para ver más detalle
plt.xticks(np.arange(0, 26000, 2500))

plt.show()
```


## Explicaciones del alumno (texto original)

### README.md

> # Entrega_Competencia01
> Repo con scripts que se usaron para generar los submits 
> Al principio de cada script está el path para poder cambiarlo. Deben ejecutarse en este orden:
>
> 01_target.py (genera la columna ternaria a partir del archivo competencia_01_crudo.csv)
>
> 02_limpieza_fe.py (limpeza del dataset + feature enginering)
>
> 03_optuna_LGBM.py (optimización con Optuna+LightGBM, 60 trials, 1 semilla, se usa marzo+abril para predecir junio)
>
> 04_validacion_junio.py (valida junio con un total de 20 semillas)
>
> 05_curvas_ganancia.py (grafica las curvas de ganancia de la validacion de junio con todas sus semillas)
>
> 06_prediccion_agosto.py (usa marzo, abril, mayo y junio para predecir agosto, usa el mejor modelo de la optimizacion)
>
> 07_cortes_media.py (promedia las probabilidades de las semillas y genera el csv para subir al bot)
>
>
> # Algunas aclaraciones
> Respecto de los faltantes se los imputó con el promedio del mes siguiente y el mes previo, a la columna ccajas_depositos de mayo se la imputó con NaN por recomendación de la cátedra, se crearon columnas de deltas y lags de 1 y 2 meses, se aplicó ranking de 0 fijo a todas las variables numéricas, se crearon columnas con flags para cuando las variables son nulas (recomendación de la cátedra)
>
> Respecto del entrenamiento se usó marzo y abril para predecir el mes de junio. Se tomaron sólo las columnas del ranking + las columnas de flags, se dejaron afueran del entrenamiento las columnas con variables originales y las asociadas a prestamos personales (ccprestamos_personales y mprestamos_personales).
>
> Respecto a la validacion se utilizaron 20 semillas para validar el mes de junio con el mejor modelo obtenido y luego obtener la curva de ganancia acumulada que se utilizó para estimar posibles valores de corte para el submit.
>
> Para la predicción de agosto se utilizó el mejor modelo + 70 semillas y se definió el submit final de acuerdo al public gain del bot. Por recomendacion de la cátedra se tuvieron en cuenta las columnas asociadas a préstamos_personales que no se habían tenido en cuenta para el entrenamiento.

