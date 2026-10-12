# MLDEVGIT — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: MLDEVGIT
- Repositorio: https://github.com/MLDEVGIT/dmeyf2026-competencia-01
- Link posteado: https://github.com/MLDEVGIT/dmeyf2026-competencia-01?utm_source=chatgpt.com
- Commit: f803c8d0e90b955df93ea0be1a50421408b172eb
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/mldevgit/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/mldevgit.json

## Resumen

Repositorio con seis scripts de Python en src/, tres textos (README.md, REPRODUCCION.md, AUDITORIA_ENTREGA.md), un manifiesto JSON y requirements.txt; no trae datos ni salidas. El camino de la entrega son cinco scripts numerados; los cuatro primeros importan src/common.py y el quinto no. El primero lee data/competencia_01.csv, comprueba su SHA256 y sus conteos y genera dos parquet: FULL457 (152 variables originales, su valor un mes antes, la diferencia contra ese valor y un indicador de disponibilidad) y FULL762 (lo anterior más el valor dos meses antes, su diferencia y su indicador). El segundo entrena LightGBM multiclase sobre FULL762 y el tercero CatBoost multiclase sobre FULL457, ambos con 202104, 202105 y 202106, pesos por mes 0,75/1/1, hiperparámetros fijos y las mismas cinco semillas; cada familia promedia la probabilidad de BAJA+2 de sus cinco modelos sobre 202108. El cuarto convierte cada promedio en un rank normalizado entre 0 y 1, combina 0,75 de LightGBM con 0,25 de CatBoost y escribe los 12.000 clientes de mayor puntaje. El quinto verifica formato, pertenencia a 202108 y SHA256 del CSV. Según el README, la ganancia pública fue 98,6150 M.

**Qué entrega.** Un CSV, output/submit_z636_c25_full762_n12000.csv, con 12.000 numero_de_cliente de 202108 en una sola columna, sin encabezado ni índice. El archivo no está en el repositorio; el código exige que su SHA256 sea 00534f4c23bb87c5e0962ee615a0f81740cf1e2f3e64232c7af5bc83aae697a0. Según el README, ese envío obtuvo una ganancia pública de 98,6150 M (Submission ID 1560-1791746981180245).

**Cómo se ejecuta.** Según el README: colocar el dataset en data/competencia_01.csv, crear un entorno virtual con Python 3.12 (py -3.12 -m venv .venv), instalar requirements.txt y ejecutar en orden, desde la carpeta del repositorio y con python -B, src/01_feature_engineering.py, src/02_train_lightgbm.py, src/03_train_catboost.py, src/04_build_final_c25.py y src/05_verify_submission.py. El primer paso requiere que output/ no exista; todos aceptan --output-dir, el primero acepta --input y el verificador --submission y --features.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM, CatBoost
- **Clase que entrena:** Tres clases: se entrena con clase_ternaria sin transformar (CONTINUA, BAJA+1, BAJA+2), con objective multiclass y num_class 3 en LightGBM y loss_function MultiClass en CatBoost. De la salida se toma la columna de probabilidad de BAJA+2, ubicada con classes_. No se definen pesos por clase; el peso de cada fila depende del mes (202104: 0,75; 202105 y 202106: 1).
- **Meses de entrenamiento:** 202104, 202105, 202106
- **Meses de validación:** —
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código. Se entrena con las 491.166 filas de los tres meses; las filas de 202104 llevan peso 0,75 y las de 202105 y 202106 peso 1 (suma de pesos exigida: 450.345).
- **Calidad de datos:** No se observa corrección ni exclusión de variables. El código comprueba la fuente antes de usarla: SHA256 del CSV, 983.061 filas, 155 columnas, 152 variables numéricas, claves cliente/mes sin nulos ni duplicados, foto_mes con formato AAAAMM, cantidad de filas y de cada clase en 202104, 202105 y 202106, y 164.647 clientes únicos en 202108. Los NaN se conservan sin imputar; CatBoost se configura con nan_mode Min.
- **Drifting:** No se observa en el código.
- **Variables dentro del mes:** No se observa en el código.
- **Variables históricas:** Para cada una de las 152 variables originales: valor del mismo cliente un mes calendario antes (_lag1), diferencia actual menos ese valor (_delta_lag1), valor dos meses calendario antes (_lag2) y diferencia actual menos ese valor (_delta_lag2); más dos indicadores 0/1 (lag1_disponible, lag2_disponible) de existencia del registro anterior. Si el registro no existe, lag y delta quedan en NaN. CatBoost recibe 457 columnas (originales, lag1, delta_lag1 e indicador) y LightGBM 762 (se agregan lag2, delta_lag2 e indicador).
- **Selección de variables:** No se observa en el código. Se usan las 152 variables originales (todas las columnas del CSV salvo numero_de_cliente, foto_mes y clase_ternaria) y todas las derivadas.
- **Optimización de hiperparámetros:** No se observa en el código. Los hiperparámetros están escritos como diccionarios en src/common.py; el README indica que no hay tuning ni early stopping.
- **Hiperparámetros finales:** LightGBM: objective multiclass, num_class 3, n_estimators 1200, learning_rate 0.02, num_leaves 750, max_depth -1, min_child_samples 5000, max_bin 31, colsample_bytree 0.5, subsample 1.0, reg_alpha 0.0, reg_lambda 0.0, n_jobs -1, verbosity -1. CatBoost: loss_function MultiClass, iterations 1000, learning_rate 0.03, depth 6, l2_leaf_reg 3.0, grow_policy SymmetricTree, boosting_type Plain, bootstrap_type Bayesian, bagging_temperature 1.0, random_strength 1.0, rsm 1.0, border_count 254, nan_mode Min, thread_count 8, task_type CPU, allow_writing_files False, verbose False, use_best_model False.
- **Semillas:** Cinco semillas escritas en src/common.py: 290497, 100003, 200003, 300007 y 400009. Se usan las mismas en LightGBM (random_state) y en CatBoost (random_seed): diez ajustes en total.
- **Cantidad de semillas:** 5
- **Ensamble:** Dentro de cada familia se promedian las probabilidades de BAJA+2 de las cinco semillas. Cada promedio se ordena (probabilidad descendente, numero_de_cliente ascendente) y se convierte en u = (M - rank)/(M - 1), con M = 164.647 y rank desde 1. El puntaje final es 0,75 por u de LightGBM FULL762 más 0,25 por u de CatBoost FULL457.
- **Corte:** Cantidad fija: los primeros 12.000 clientes del ranking combinado (puntaje descendente, numero_de_cliente ascendente). No se usa umbral de probabilidad.
- **Validación:** No se observa en el código: los scripts no separan meses de validación ni calculan ganancia. Según el README, el peso 75/25 se seleccionó en mayo y junio y el agregado de lag2 se evaluó en junio con la medida que el texto llama TP (LightGBM de 669 a 686 TP; la combinación de 688 a 695 TP; mayo sin cambio en 520); ese código no está en el repositorio.
- **Salidas:** Todo en output/ (ignorada por Git): competencia_01_historico_lag1.parquet y competencia_01_historico_lag2_full762.parquet (983.061 filas cada uno), feature_audit.json, las carpetas lightgbm/ y catboost/ con scores_seed_<semilla>.parquet, ranking_ensemble.parquet y auditoria.json, ranking_c25.parquet, final_audit.json y submit_z636_c25_full762_n12000.csv (12.000 numero_de_cliente, una columna, sin encabezado, UTF-8, saltos LF).

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- CatBoost (`modelo.catboost`)
- Tres clases (CONTINUA, BAJA+1, BAJA+2) (`clase.multiclase`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: Python 3.12.0, 'preferentemente Windows x64', comandos en PowerShell con un entorno virtual .venv; versiones exactas de 12 paquetes en requirements.txt. El README pide al menos 16 GB de RAM y unos 4 GB adicionales de disco para matrices temporales. REPRODUCCION.md informa 3 h 04 min 26 s para la corrida completa. No se declara el hardware usado.

## Pasos del camino de la entrega

1. **Parámetros del protocolo.** src/common.py fija las rutas por defecto (data/competencia_01.csv y output/, relativas a la carpeta del repositorio), las cinco semillas, los pesos por mes (202104: 0,75; 202105 y 202106: 1), los SHA256 esperados de la entrada, de las listas de variables y del CSV final, y los conteos de filas y de clases esperados en los tres meses de entrenamiento. (`src/common.py` líneas 8–31)
2. **Control del archivo de entrada y lectura.** El primer script exige que la carpeta de salida no exista y que el SHA256 del CSV coincida con el esperado, lee el encabezado para armar la lista de variables (todas las columnas salvo claves y clase), construye las listas de nombres FULL457 y FULL762 y carga el CSV completo con pandas. (`src/01_feature_engineering.py` líneas 7–15; `src/common.py` líneas 37–42; `src/common.py` líneas 55–61)
3. **Auditoría de la fuente.** Se comprueban 983.061 filas, 155 columnas, 152 variables numéricas, claves sin nulos ni duplicados, meses con formato AAAAMM, la cantidad de filas y de cada clase en 202104, 202105 y 202106, y 164.647 clientes únicos en 202108. Cualquier diferencia detiene la ejecución con ValueError. (`src/common.py` líneas 63–89; `src/01_feature_engineering.py` líneas 16–16)
4. **Localización del registro anterior de cada cliente.** Para cada fila se busca la posición de la fila del mismo cliente exactamente uno y dos meses calendario antes, con aritmética de meses que contempla el cambio de año y una unión por cliente y mes. Donde ese registro no existe queda NaN; no se busca un mes más antiguo. (`src/common.py` líneas 44–53; `src/common.py` líneas 91–99; `src/01_feature_engineering.py` líneas 17–20)
5. **Lags y deltas de uno y dos meses.** Por bloques de filas se arman las columnas _lag1 y _delta_lag1 (actual menos lag1) de las 152 variables y el indicador lag1_disponible: 457 variables. Para el segundo esquema se agregan _lag2, _delta_lag2 y lag2_disponible: 762 variables. No se imputan valores. (`src/common.py` líneas 101–135)
6. **Escritura y relectura de los dos parquet.** Para cada esquema (457 y 762) se escribe un archivo .partial en bloques de 50.000 filas con compresión snappy, se relee completo comparando cada bloque con el recalculado en memoria y recién entonces se lo enlaza con su nombre definitivo y se borra el parcial. (`src/01_feature_engineering.py` líneas 21–43; `src/common.py` líneas 137–173)
7. **Registro de la ingeniería de variables.** Se cuenta, para 202104, 202105, 202106 y 202108, cuántas filas tienen registro dos meses antes y se guarda feature_audit.json con las listas de nombres, los hashes y esos porcentajes. (`src/01_feature_engineering.py` líneas 44–52)
8. **Matrices de LightGBM.** Del parquet FULL762 se leen claves y clase de los tres meses de entrenamiento ordenadas por cliente y mes (491.166 filas) y los clientes de 202108 ordenados por número (164.647). Las 762 variables se copian en lotes de 5.000 filas a dos matrices float64 respaldadas en disco dentro de una carpeta temporal. De 202108 no se lee la clase. (`src/common.py` líneas 231–274)
9. **Entrenamiento de LightGBM con cinco semillas.** Para cada semilla se ajusta un LGBMClassifier multiclase de 1.200 árboles con pesos por fila según el mes, se predice 202108 y se guarda la probabilidad de BAJA+2. Luego se promedian las cinco probabilidades y se guarda el ranking de la familia con su rank normalizado. (`src/02_train_lightgbm.py` líneas 1–7; `src/common.py` líneas 174–180; `src/common.py` líneas 276–309)
10. **Carga de datos para CatBoost.** Del parquet FULL457 se leen los tres meses de entrenamiento con clase y las filas de 202108 sin clase; el entrenamiento se ordena por cliente y mes y se repiten los controles de 491.166 filas, conteos por clase, suma de pesos 450.345 y 164.647 clientes únicos. (`src/common.py` líneas 211–229)
11. **Entrenamiento de CatBoost con cinco semillas.** Para cada semilla se ajusta un CatBoostClassifier MultiClass de 1.000 iteraciones en CPU con los mismos pesos por fila, se predice 202108 y se guarda la probabilidad de BAJA+2. Se promedian las cinco probabilidades y se guarda el ranking de la familia. (`src/03_train_catboost.py` líneas 1–7; `src/common.py` líneas 181–184; `src/common.py` líneas 311–338)
12. **Controles previos a la combinación.** El cuarto script exige que no existan el CSV final ni ranking_c25.parquet, lee auditoria.json de cada familia (5 ajustes, mismas semillas, 762 y 457 variables, hash de nombres), carga los dos rankings, alinea CatBoost al orden de clientes de LightGBM y recalcula el promedio de las cinco semillas exigiendo igualdad exacta con el puntaje guardado. (`src/04_build_final_c25.py` líneas 5–24)
13. **Rank normalizado y combinación 0,75 / 0,25.** Cada promedio de familia se transforma en u = (M - rank)/(M - 1), con orden por probabilidad descendente y numero_de_cliente ascendente. El puntaje combinado es 0,75 por u de LightGBM más 0,25 por u de CatBoost, y se ordena con el mismo criterio. (`src/04_build_final_c25.py` líneas 25–27; `src/common.py` líneas 186–193; `src/common.py` líneas 206–209)
14. **Selección de 12.000 clientes y escritura del CSV.** Se toman los primeros 12.000 numero_de_cliente del ranking combinado, se guarda ranking_c25.parquet y se escribe el CSV de una columna sin encabezado. Se calcula su SHA256, se guarda final_audit.json y el script termina con error si el hash difiere del esperado. (`src/04_build_final_c25.py` líneas 28–38)
15. **Verificación del CSV final.** El quinto script, cuyos import son argparse, hashlib, re, pathlib y pandas, exige 12.000 líneas con un entero cada una y sin repetidos, que todos los identificadores pertenezcan a los 164.647 clientes de 202108 del parquet de variables y que el SHA256 del archivo sea el esperado. Imprime FINAL REPRODUCIBILITY: PASS o FAIL. (`src/05_verify_submission.py` líneas 8–36)

## Archivos

- `REPRODUCCION.md` · explicacion · Markdown · 61 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mldevgit/REPRODUCCION.md.txt) — Informe de una ejecución completa de los cinco scripts fechada el 2026-10-11 (de 17:00 a 20:05; 3 h 04 min 26 s) con resultado PASS: tiempo por etapa (115,8 s; 7.266,2 s; 3.678,4 s; 3,4 s; 1,3 s), versión de Python y de los 12 paquetes, comandos usados con --output-dir data/reproduccion_final_z636 y los tres hashes obtenidos.
- `requirements.txt` · configuracion · Texto · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mldevgit/requirements.txt.txt) — Doce paquetes con versión exacta: numpy 2.5.2, pandas 3.0.5, scipy 1.18.1, scikit-learn 1.9.0, lightgbm 4.7.0, catboost 1.2.10, pyarrow 25.0.0, graphviz 0.21, matplotlib 3.11.1, plotly 7.0.0, six 1.17.0 y python-dateutil 2.9.0.post0.
- `AUDITORIA_ENTREGA.md` · explicacion · Markdown · 67 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mldevgit/AUDITORIA_ENTREGA.md.txt) — Informe de una auditoría estática del paquete con resultado PASS: alcance, lista de los 12 archivos, controles ejecutados sin entrenar modelos (sintaxis, hashes de variables, casos de prueba de lags, comparación de semillas y parámetros, verificación del CSV, inventario y .gitignore) y una sección final que indica que la reproducción completa queda pendiente.
- `README.md` · explicacion · Markdown · 80 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mldevgit/README.md.txt) — Presentación de la entrega: identifica el modelo final como Z636 C25 FULL762, indica entrada, entorno y comandos, describe las variables FULL457 y FULL762, los meses y pesos de entrenamiento (abril, mayo y junio de 2021; indica que no se entrena con julio), las semillas, la fórmula de combinación y el formato del CSV. Declara una ganancia pública de 98,6150 M, el SHA256 esperado del CSV, una reproducción completa con resultado PASS en 3 h 04 min 26 s y, en la sección de selección metodológica, que el peso 75/25 y el agregado de lag2 se evaluaron en mayo y junio.
- `fuentes_auditadas.json` · configuracion · JSON · 62 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mldevgit/fuentes_auditadas.json.txt) — Manifiesto con el nombre del modelo final, la ganancia pública y el identificador de envío informados por el autor, los hashes de FULL457, FULL762 y del CSV final, seis referencias (Z621, Z633, Z636, Z635, Z637 y el componente CatBoost original) con el SHA256 de su código, el SHA256 de los seis scripts y de requirements.txt y el estado de la auditoría estática. El campo full_reproduction_status figura como NOT_EXECUTED. Los scripts no leen este archivo.
- `src/01_feature_engineering.py` · principal · Python · 54 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mldevgit/src/01_feature_engineering.py.txt) — Primer paso: controla el CSV de entrada, calcula lags y deltas de uno y dos meses y escribe los dos parquet de variables (457 y 762) y feature_audit.json en una carpeta de salida nueva.
- `src/05_verify_submission.py` · principal · Python · 38 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mldevgit/src/05_verify_submission.py.txt) — Quinto paso: verifica el CSV final (12.000 identificadores enteros únicos, pertenecientes a 202108) y su SHA256. Sus import son argparse, hashlib, re, pathlib y pandas; no usa common.py.
- `src/common.py` · principal · Python · 338 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mldevgit/src/common.py.txt) — Módulo que importan los scripts 01 a 04: constantes del protocolo, controles de la fuente, cálculo de lags y deltas, hiperparámetros de LightGBM y CatBoost, funciones de ranking y las funciones que cargan los datos y entrenan cada familia con cinco semillas.
- `src/04_build_final_c25.py` · principal · Python · 40 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mldevgit/src/04_build_final_c25.py.txt) — Cuarto paso: combina los rankings de LightGBM y CatBoost con pesos 0,75 y 0,25 sobre el rank normalizado, escribe el CSV con 12.000 clientes y compara su SHA256 con el esperado.
- `src/03_train_catboost.py` · principal · Python · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mldevgit/src/03_train_catboost.py.txt) — Tercer paso: lee --output-dir y llama a train_family de common.py con la familia 'catboost' (cinco semillas sobre FULL457).
- `src/02_train_lightgbm.py` · principal · Python · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mldevgit/src/02_train_lightgbm.py.txt) — Segundo paso: lee --output-dir y llama a train_family de common.py con la familia 'lightgbm' (cinco semillas sobre FULL762).

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### src/01_feature_engineering.py

Primer paso: controla el CSV de entrada, calcula lags y deltas de uno y dos meses y escribe los dos parquet de variables (457 y 762) y feature_audit.json en una carpeta de salida nueva.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–5] Importa csv, pyarrow y, con from common import *, todo lo definido o importado en
#   common.py (constantes, controles, funciones de generación de variables y los nombres np, pd, pq y Path).
"""FULL457 y FULL762: meses calendario exactos, NaN y orden CSV preservados."""
import csv
import pyarrow as pa
from common import *

# [Anotación · líneas 6–14] Lee los argumentos --output-dir e --input, exige que la carpeta de salida no
#   exista y que el SHA256 del CSV sea el esperado. Lee sólo el encabezado, exige nombres sin repetir y la
#   presencia de claves y clase, toma como variables las demás columnas y arma las listas de nombres FULL457 y
#   FULL762.
def main():
    p=args(__doc__); p.add_argument('--input',type=Path,default=INPUT); opts=p.parse_args()
    output=opts.output_dir
    exigir(not output.exists(),'La carpeta de salida debe ser NUEVA')
    exigir(sha256_archivo(opts.input)==EXPECTED_INPUT,'SHA256 fuente diferente al original validado')
    with opts.input.open(encoding='utf-8-sig',newline='') as f: header=next(csv.reader(f))
    exigir(len(header)==len(set(header)) and set(CLAVES+[TARGET]).issubset(header),'Encabezado inválido')
    features=[c for c in header if c not in {*CLAVES,TARGET}]
    full,full762=nombres_features(features)
# [Anotación · líneas 15–20] Carga el CSV completo con pandas, ejecuta auditar_fuente, comprueba la aritmética
#   de dos meses atrás con cuatro meses de ejemplo (incluye enero y febrero de 2022) y calcula, para cada fila,
#   la posición del registro del mismo cliente uno y dos meses antes.
    base=pd.read_csv(opts.input,encoding='utf-8-sig',low_memory=False)
    digest=auditar_fuente(base,features,full)
    exigir(meses_atras(np.array([202105,202106,202201,202202]),2).tolist()
           ==[202103,202104,202111,202112],'Aritmética lag2 incorrecta')
    previous=predecesores(base)
    previous2=predecesores(base,lag=2)
# [Anotación · líneas 21–37] Crea la carpeta de salida y, para cada esquema (457 y 762), escribe un archivo
#   features_<tamaño>.partial recorriendo la tabla en bloques de 50.000 filas: genera el bloque de variables
#   correspondiente y lo agrega con ParquetWriter (compresión snappy, formato 2.6, grupos de 50.000 filas).
    output.mkdir(parents=True)
    import os
    # Dos esquemas explícitos: CatBoost no recibe columnas lag2.
    for size,name in [(457,PARQUET457),(762,PARQUET762)]:
        pending=output/f'features_{size}.partial'
        with pending.open('xb') as f:
            writer=None
            try:
                for start in range(0,len(base),50000):
                    end=min(start+50000,len(base))
                    block=(generar_lote(base,features,full,previous,start,end) if size==457 else
                           generar_lote_full762(base,features,full,full762,previous,previous2,start,end))
                    table=pa.Table.from_pandas(block,preserve_index=False)
                    if writer is None: writer=pq.ParquetWriter(f,table.schema,compression='snappy',version='2.6')
                    writer.write_table(table,row_group_size=50000)
            finally:
                if writer is not None: writer.close()
# [Anotación · líneas 38–43] Relee el archivo parcial con la función de verificación de su esquema y, si pasa,
#   crea un enlace duro con el nombre definitivo del parquet y borra el parcial.
        if size==457:
            verificar_parquet(pending,base,features,full,previous,50000)
        else:
            verificar_full762(pending,base,features,full,full762,previous,previous2,50000)
        os.link(pending,output/name)
        pending.unlink()
# [Anotación · líneas 44–54] Para 202104, 202105, 202106 y 202108 cuenta las filas y cuántas tienen registro
#   dos meses antes, y guarda feature_audit.json con cantidad de filas, hashes, listas de nombres, SHA256 de la
#   entrada y esa disponibilidad. La última línea ejecuta main cuando el archivo se corre como script.
    availability=[]
    for month in [202104,202105,202106,202108]:
        mask=base.foto_mes.eq(month)
        rows=int(mask.sum()); count=int((mask & previous2.notna()).sum())
        availability.append(dict(foto_mes=month,filas=rows,lag2_disponible=count,porcentaje=100*count/rows))
    save_json(output/'feature_audit.json',dict(rows=len(base),FULL457_hash=digest,FULL762_hash=HASH_FULL762,
              FULL457=full,FULL762=full762,input_sha256=EXPECTED_INPUT,
              lag1='MES_CALENDARIO_ANTERIOR_EXACTO',lag2='DOS_MESES_CALENDARIO_ANTES_EXACTO',
              validation='PASS',row_order='CSV original',lag2_availability=availability))

if __name__=='__main__': main()
```

### src/05_verify_submission.py

Quinto paso: verifica el CSV final (12.000 identificadores enteros únicos, pertenecientes a 202108) y su SHA256. Sus import son argparse, hashlib, re, pathlib y pandas; no usa common.py.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–6] Importa argparse, hashlib, re, pathlib y pandas y repite como constantes propias el
#   SHA256 esperado y el nombre del CSV final.
"""Verificación byte a byte y pertenencia a August; sin librerías de modelos."""
import argparse, hashlib, re
from pathlib import Path
import pandas as pd
EXPECTED='00534f4c23bb87c5e0962ee615a0f81740cf1e2f3e64232c7af5bc83aae697a0'
NAME='submit_z636_c25_full762_n12000.csv'
# [Anotación · líneas 7–13] verify exige que el archivo exista, lo lee en bytes y exige 12.000 líneas formadas
#   sólo por dígitos y sin identificadores repetidos.

def verify(path,features_path):
    if not path.is_file(): raise ValueError('Archivo inexistente')
    raw=path.read_bytes(); lines=raw.splitlines()
    if len(lines)!=12000 or any(re.fullmatch(rb'[0-9]+',x) is None for x in lines):
        raise ValueError('Se requieren 12000 líneas de un ID entero sin header/index')
    if len({int(x) for x in lines})!=12000: raise ValueError('IDs duplicados')
# [Anotación · líneas 14–24] Lee del parquet de variables sólo la columna numero_de_cliente de 202108, exige
#   164.647 identificadores únicos y que todos los del CSV pertenezcan a ese conjunto. Calcula el SHA256 de los
#   bytes, lo imprime y lanza error si difiere del esperado.
    # Proyección sólo de IDs; nunca cargar target August.
    august=pd.read_parquet(features_path,columns=['numero_de_cliente'],
                           filters=[('foto_mes','==',202108)],engine='pyarrow')
    if len(august)!=164647 or not august.numero_de_cliente.is_unique:
        raise ValueError('Universo August inválido')
    if not {int(x) for x in lines}.issubset(set(august.numero_de_cliente)):
        raise ValueError('IDs ajenos a August')
    digest=hashlib.sha256(raw).hexdigest()
    print('SHA256:',digest)
    if digest!=EXPECTED: raise ValueError('SHA256 diferente del oficial')
    return digest
# [Anotación · líneas 25–38] main define --output-dir, --submission y --features (por defecto el CSV y el
#   parquet FULL457 dentro de la carpeta de salida), llama a verify y, ante un error, imprime FINAL
#   REPRODUCIBILITY: FAIL y sale con código 1; si no, imprime FINAL REPRODUCIBILITY: PASS.

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parents[1]/'output')
    p.add_argument('--submission',type=Path)
    p.add_argument('--features',type=Path)
    opts=p.parse_args()
    try: verify(opts.submission or opts.output_dir/NAME,
                opts.features or opts.output_dir/'competencia_01_historico_lag1.parquet')
    except (OSError,ValueError) as error:
        print('FINAL REPRODUCIBILITY: FAIL'); p.exit(1,str(error)+'\n')
    print('FINAL REPRODUCIBILITY: PASS')

if __name__=='__main__': main()
```

### src/common.py

Módulo que importan los scripts 01 a 04: constantes del protocolo, controles de la fuente, cálculo de lags y deltas, hiperparámetros de LightGBM y CatBoost, funciones de ranking y las funciones que cargan los datos y entrenan cada familia con cinco semillas.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Importa argparse, gc, hashlib, json, platform, tempfile, time, Path, numpy,
#   pandas, pyarrow.parquet y pyarrow.dataset, y define las constantes del protocolo: carpeta base (la que
#   contiene a src/), salida por defecto output/, entrada por defecto data/competencia_01.csv, las cinco
#   semillas (290497, 100003, 200003, 300007, 400009), los pesos por mes (202104: 0,75; 202105: 1; 202106: 1),
#   los SHA256 esperados del CSV de entrada, del CSV final y de las dos listas de nombres de variables, el
#   nombre del CSV final y los nombres de los dos parquet.
"""Protocolo final congelado. Todas las salidas se crean exclusivamente."""
import argparse, gc, hashlib, json, platform, tempfile, time
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pyarrow.dataset as ds
BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / 'output'
INPUT = BASE / 'data' / 'competencia_01.csv'
SEEDS = [290497,100003,200003,300007,400009]
PESOS = {202104:.75,202105:1.0,202106:1.0}
EXPECTED_CSV = '00534f4c23bb87c5e0962ee615a0f81740cf1e2f3e64232c7af5bc83aae697a0'
SUBMISSION_NAME = 'submit_z636_c25_full762_n12000.csv'
EXPECTED_INPUT = '53fd6265cfa565224fa4370e1fabe72d343a5c76540eb769758686a194bb5dfd'
HASH_FULL457 = "c3578882fcf1adf79df9c20c472864719672522fa2ee9283d4a9b1c0fe080c12"
HASH_FULL762 = '1e9747955f214a8ddcb405af0e3a71d4a516f1818bf829c0d6c14ca0f934e8f6'
PARQUET457 = 'competencia_01_historico_lag1.parquet'
PARQUET762 = 'competencia_01_historico_lag2_full762.parquet'

# [Anotación · líneas 21–31] Define las claves (numero_de_cliente, foto_mes), la columna de clase
#   (clase_ternaria), la cantidad total de filas esperada (983.061) y las cantidades por mes que se exigen más
#   adelante: 202104 con 163.284 filas (161.188 CONTINUA, 957 BAJA+1 y 1.139 BAJA+2), 202105 con 163.768
#   (161.759, 1.139 y 870) y 202106 con 164.114 (162.145, 871 y 1.098).
CLAVES = ["numero_de_cliente", "foto_mes"]

TARGET = "clase_ternaria"

FILAS = 983061

ESPERADOS = {
    202104: {"filas": 163284, "CONTINUA": 161188, "BAJA+1": 957, "BAJA+2": 1139},
    202105: {"filas": 163768, "CONTINUA": 161759, "BAJA+1": 1139, "BAJA+2": 870},
    202106: {"filas": 164114, "CONTINUA": 162145, "BAJA+1": 871, "BAJA+2": 1098},
}

# [Anotación · líneas 33–42] exigir lanza ValueError con un mensaje cuando una condición no se cumple; se usa
#   como control en todo el código. sha256_archivo calcula el SHA256 de un archivo leyéndolo en bloques de 8 MB.
def exigir(condicion, mensaje):
    if not condicion:
        raise ValueError(mensaje)

def sha256_archivo(ruta):
    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(8 * 1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()

# [Anotación · líneas 44–53] Aritmética de meses AAAAMM. mes_anterior devuelve el mes calendario previo (enero
#   pasa a diciembre del año anterior). meses_atras admite lag 1 o 2 y exige meses entre 1 y 12: convierte el
#   mes en un número serial de meses, resta el lag y lo vuelve a formato AAAAMM.
def mes_anterior(meses):
    return np.where(meses % 100 == 1, (meses // 100 - 1) * 100 + 12, meses - 1)

def meses_atras(meses, lag):
    meses = np.asarray(meses, dtype=np.int64)
    exigir(lag in (1, 2), 'Sólo se permiten lag1 y lag2 congelados')
    exigir(((meses % 100 >= 1) & (meses % 100 <= 12) & (meses // 100 >= 1)).all(),
           'Mes calendario inválido')
    serial = (meses // 100) * 12 + (meses % 100 - 1) - lag
    return (serial // 12) * 100 + serial % 12 + 1

# [Anotación · líneas 55–61] nombres_features arma las dos listas de nombres: FULL457 (las variables
#   originales, sus _lag1, sus _delta_lag1 y lag1_disponible) y FULL762 (FULL457 más _lag2, _delta_lag2 y
#   lag2_disponible). Exige 457 y 762 nombres sin repetir y que el SHA256 de los nombres unidos por salto de
#   línea coincida con el esperado.
def nombres_features(features):
    full457 = features + [f'{f}_lag1' for f in features] + [f'{f}_delta_lag1' for f in features] + ['lag1_disponible']
    full762 = full457 + [f'{f}_lag2' for f in features] + [f'{f}_delta_lag2' for f in features] + ['lag2_disponible']
    for names, size, expected in [(full457, 457, HASH_FULL457), (full762, 762, HASH_FULL762)]:
        exigir(len(names) == len(set(names)) == size, 'Cantidad/nombres de features inválidos')
        exigir(hashlib.sha256('\n'.join(names).encode()).hexdigest() == expected, 'Hash de features incorrecto')
    return full457, full762

# [Anotación · líneas 63–89] auditar_fuente comprueba el CSV ya cargado: 983.061 filas, 155 columnas, 152
#   variables numéricas, hash de FULL457, claves sin nulos ni duplicados y foto_mes con mes entre 1 y 12. Para
#   202104, 202105 y 202106 exige la cantidad de filas y de cada clase definida en ESPERADOS y que no haya clase
#   nula; para 202108 exige 164.647 filas con numero_de_cliente único. Comprueba mes_anterior con tres meses de
#   ejemplo (202105, 202106 y 202201) y devuelve el hash de FULL457.
def auditar_fuente(base, features, full457):
    exigir(len(base) == FILAS, f"Filas incorrectas: {len(base)} != {FILAS}")
    exigir(len(base.columns) == 155, "La fuente no tiene 155 columnas")
    exigir(len(features) == 152, f"Features originales: {len(features)} != 152")
    exigir(len(full457) == 457 and len(set(full457)) == 457, "FULL457 no tiene 457 nombres únicos")
    digest = hashlib.sha256("\n".join(full457).encode("utf-8")).hexdigest()
    exigir(digest == HASH_FULL457, f"Hash FULL457 incorrecto: {digest}")
    exigir(not base[CLAVES].isna().any().any(), "Claves nulas en la fuente")
    exigir(not base.duplicated(CLAVES).any(), "Claves cliente/mes duplicadas")
    meses = pd.to_numeric(base.foto_mes, errors="raise")
    exigir(not ((meses % 1 != 0) | (meses // 100 < 1) | (~(meses % 100).between(1, 12))).any(),
           "foto_mes no contiene meses calendario YYYYMM válidos")
    for feature in features:
        exigir(pd.api.types.is_numeric_dtype(base[feature]), f"Feature no numérica: {feature}")
    for mes, esperado in ESPERADOS.items():
        datos = base.loc[base.foto_mes.eq(mes)]
        exigir(len(datos) == esperado["filas"], f"Filas incorrectas en {mes}")
        exigir(not datos[TARGET].isna().any(), f"Target nulo en {mes}")
        observado = datos[TARGET].value_counts().to_dict()
        requerido = {k: v for k, v in esperado.items() if k != "filas"}
        exigir(observado == requerido, f"Target incorrecto en {mes}: {observado} != {requerido}")
    agosto = base.loc[base.foto_mes.eq(202108)]
    exigir(len(agosto) == 164647, "Filas incorrectas en 202108")
    exigir(agosto.numero_de_cliente.is_unique, "IDs no únicos en 202108")
    exigir(mes_anterior(np.array([202105, 202106, 202201])).tolist() == [202104, 202105, 202112],
           "Error en aritmética de mes calendario anterior")
    return digest

# [Anotación · líneas 91–99] predecesores busca, para cada fila, la posición de la fila del mismo cliente uno
#   o dos meses calendario antes: reemplaza foto_mes por el mes buscado y une por cliente y mes contra la tabla
#   original (unión izquierda, uno a uno). Devuelve una serie alineada con la tabla, con NaN donde ese registro
#   no existe.
def predecesores(base, lag=1):
    izquierda = base[CLAVES].copy()
    meses = base.foto_mes.to_numpy(dtype='int64')
    izquierda["foto_mes"] = mes_anterior(meses) if lag == 1 else meses_atras(meses, lag)
    izquierda["_fila_actual"] = np.arange(len(base), dtype="int64")
    derecha = base[CLAVES].copy()
    derecha["_fila_lag"] = np.arange(len(base), dtype="int64")
    unidos = izquierda.merge(derecha, on=CLAVES, how="left", sort=False, validate="one_to_one")
    return unidos.set_index("_fila_actual")["_fila_lag"].reindex(base.index)

# [Anotación · líneas 101–117] generar_lote construye, para las filas entre inicio y fin, el bloque FULL457:
#   toma los valores de las 152 variables en la fila predecesora (NaN si no hay), los pasa a float64 como _lag1,
#   calcula _delta_lag1 como valor actual menos lag, agrega lag1_disponible (1 si existe el registro del mes
#   anterior, tipo int8) y deja las columnas en el orden claves, FULL457, clase_ternaria.
def generar_lote(base, features, full457, anterior, inicio, fin):
    actuales = base.iloc[inicio:fin]
    indices = anterior.iloc[inicio:fin]
    # reindex inserta NaN cuando no existe predecesor; no busca meses más antiguos.
    # float64 permite NaN y garantiza el mismo esquema de lag/delta entre lotes.
    lag = base[features].reindex(indices.fillna(-1).astype("int64").to_numpy())
    lag.index = actuales.index
    lag = lag.astype("float64")
    delta = actuales[features] - lag
    salida = pd.concat([
        actuales[CLAVES + features],
        lag.rename(columns={f: f"{f}_lag1" for f in features}),
        delta.rename(columns={f: f"{f}_delta_lag1" for f in features}),
        indices.notna().astype("int8").rename("lag1_disponible"), actuales[[TARGET]],
    ], axis=1)
    exigir(salida.columns.tolist() == CLAVES + full457 + [TARGET], "Orden de columnas incorrecto en lote")
    return salida

# [Anotación · líneas 119–135] generar_lote_full762 llama a generar_lote para el prefijo FULL457 y repite el
#   mismo cálculo con el predecesor de dos meses: _lag2, _delta_lag2 (actual menos lag2) y lag2_disponible. Deja
#   las columnas en el orden claves, FULL762, clase_ternaria.
def generar_lote_full762(base, features, full457, full762, anterior, anterior2, inicio, fin):
    # El prefijo FULL457 usa la implementación ya auditada sin cambios.
    prefijo = generar_lote(base, features, full457, anterior, inicio, fin)
    actuales = base.iloc[inicio:fin]
    indices = anterior2.iloc[inicio:fin]
    lag2 = base[features].reindex(indices.fillna(-1).astype('int64').to_numpy())
    lag2.index = actuales.index
    lag2 = lag2.astype('float64')
    delta2 = actuales[features] - lag2
    salida = pd.concat([
        prefijo.drop(columns=[TARGET]),
        lag2.rename(columns={f: f'{f}_lag2' for f in features}),
        delta2.rename(columns={f: f'{f}_delta_lag2' for f in features}),
        indices.notna().astype('int8').rename('lag2_disponible'), actuales[[TARGET]],
    ], axis=1)
    exigir(salida.columns.tolist() == CLAVES + full762 + [TARGET], 'Orden FULL762 incorrecto')
    return salida

# [Anotación · líneas 137–151] verificar_full762 relee el parquet FULL762 por bloques: exige 983.061 filas, el
#   esquema claves + FULL762 + clase y el hash de nombres, y compara cada bloque releído, valor por valor, con
#   el bloque recalculado desde la tabla en memoria.
def verificar_full762(ruta, base, features, full457, full762, anterior, anterior2, lote):
    archivo = pq.ParquetFile(ruta)
    exigir(archivo.metadata.num_rows == FILAS and archivo.schema_arrow.names == CLAVES + full762 + [TARGET],
           'Filas/schema FULL762 incorrectos')
    exigir(hashlib.sha256('\n'.join(archivo.schema_arrow.names[2:-1]).encode()).hexdigest() == HASH_FULL762,
           'Hash FULL762 incorrecto al releer')
    posicion = 0
    for bloque in archivo.iter_batches(batch_size=lote):
        releido = bloque.to_pandas().reset_index(drop=True)
        fin = posicion + len(releido)
        esperado = generar_lote_full762(base, features, full457, full762, anterior, anterior2, posicion, fin).reset_index(drop=True)
        pd.testing.assert_frame_equal(releido, esperado, check_dtype=False, check_exact=True)
        posicion = fin
    exigir(posicion == FILAS, 'Relectura FULL762 incompleta')
    print('FULL762: relectura exacta de claves, target, features y NaN PASS', flush=True)

# [Anotación · líneas 153–173] verificar_parquet hace la misma relectura para el parquet FULL457: filas, orden
#   de columnas, hash de nombres, igualdad de claves y clase con el CSV e igualdad exacta de cada bloque con el
#   recalculado. Imprime el avance por bloque.
def verificar_parquet(ruta, base, features, full457, anterior, lote):
    archivo = pq.ParquetFile(ruta)
    exigir(archivo.metadata.num_rows == FILAS, "Filas incorrectas en parquet")
    columnas = archivo.schema_arrow.names
    exigir(columnas == CLAVES + full457 + [TARGET], "Columnas/orden incorrectos en parquet")
    hash_releido = hashlib.sha256("\n".join(columnas[2:-1]).encode("utf-8")).hexdigest()
    exigir(hash_releido == HASH_FULL457, "Hash FULL457 incorrecto al releer")
    posicion = 0
    # Relectura completa sin cargar a la vez los 460 campos de todo el parquet.
    for bloque in archivo.iter_batches(batch_size=lote):
        releido = bloque.to_pandas().reset_index(drop=True)
        fin = posicion + len(releido)
        original = base.iloc[posicion:fin][CLAVES + [TARGET]].reset_index(drop=True)
        pd.testing.assert_frame_equal(releido[CLAVES + [TARGET]], original, check_dtype=False)
        esperado = generar_lote(base, features, full457, anterior, posicion, fin).reset_index(drop=True)
        pd.testing.assert_frame_equal(releido, esperado, check_dtype=False, check_exact=True)
        posicion = fin
        print(f"Relectura validada: {posicion}/{FILAS}", flush=True)
    exigir(posicion == FILAS, "Relectura incompleta")
    print(f"Parquet releído: {posicion} filas; {len(columnas)} columnas; hash FULL457={hash_releido}")
    print("Preservación exacta de numero_de_cliente/foto_mes/clase_ternaria y valores FULL457: PASS")
# [Anotación · líneas 174–184] Hiperparámetros fijos. LightGBM (COMUNES y MULTICLASS): objective multiclass
#   con 3 clases, 1.200 árboles, learning_rate 0,02, num_leaves 750, max_depth -1, min_child_samples 5.000,
#   max_bin 31, colsample_bytree 0,5, subsample 1, reg_alpha 0, reg_lambda 0, n_jobs -1 y verbosity -1. CatBoost
#   (PARAMETROS): MultiClass, 1.000 iteraciones, learning_rate 0,03, depth 6, l2_leaf_reg 3, SymmetricTree,
#   boosting Plain, bootstrap Bayesian con bagging_temperature 1, random_strength 1, rsm 1, border_count 254,
#   nan_mode Min, 8 hilos en CPU, allow_writing_files, verbose y use_best_model en False.
COMUNES = dict(
    n_estimators=1200, learning_rate=0.02, num_leaves=750, max_depth=-1,
    min_child_samples=5000, max_bin=31, colsample_bytree=0.5,
    subsample=1.0, reg_alpha=0.0, reg_lambda=0.0, n_jobs=-1, verbosity=-1,
)

MULTICLASS = dict(objective="multiclass", num_class=3, **COMUNES)
PARAMETROS=dict(loss_function='MultiClass',iterations=1000,learning_rate=.03,depth=6,
    l2_leaf_reg=3.0,grow_policy='SymmetricTree',boosting_type='Plain',bootstrap_type='Bayesian',
    bagging_temperature=1.0,random_strength=1.0,rsm=1.0,border_count=254,nan_mode='Min',
    thread_count=8,task_type='CPU',allow_writing_files=False,verbose=False,use_best_model=False)

# [Anotación · líneas 186–193] orden exige valores finitos y devuelve el orden de los clientes por
#   probabilidad descendente y, ante empate, numero_de_cliente ascendente. normalizar asigna rank desde 1 con
#   ese orden y devuelve (M - rank)/(M - 1): 1 para el primero y 0 para el último.
def orden(prob,ids):
    exigir(np.isfinite(prob).all(),'Score no finito')
    return np.lexsort((ids,-prob))

def normalizar(prob,ids):
    ranks=np.empty(len(ids),dtype=np.int64)
    ranks[orden(prob,ids)]=np.arange(1,len(ids)+1)
    return (len(ids)-ranks)/(len(ids)-1)

# [Anotación · líneas 195–209] Utilidades: args crea el parser con la opción --output-dir; save_json y
#   save_parquet abren el destino en modo de creación exclusiva, por lo que no escriben sobre un archivo
#   existente; ranking arma una tabla con numero_de_cliente, score y columnas extra, ordenada con orden y con
#   una columna rank desde 1.
def args(description):
    p=argparse.ArgumentParser(description=description)
    p.add_argument('--output-dir',type=Path,default=OUTPUT)
    return p

def save_json(path,data):
    with path.open('x',encoding='utf-8') as f: json.dump(data,f,indent=2,ensure_ascii=False,allow_nan=False)

def save_parquet(path,frame):
    with path.open('xb') as f: frame.to_parquet(f,index=False,engine='pyarrow')

def ranking(ids,score,extras):
    t=pd.DataFrame(dict(numero_de_cliente=ids,score=score,**extras)).iloc[orden(score,ids)].reset_index(drop=True)
    t.insert(0,'rank',np.arange(1,len(ids)+1))
    return t

# [Anotación · líneas 211–229] load_training lee del parquet FULL457 el entrenamiento (202104, 202105 y
#   202106, con claves, 457 variables y clase) y las filas de 202108 sólo con numero_de_cliente y variables, sin
#   la clase. Con sort_catboost ordena el entrenamiento por cliente y mes. Exige 491.166 filas sin claves
#   repetidas, los conteos por mes y clase, que los pesos por mes sumen 450.345 y 164.647 clientes únicos en
#   202108. Devuelve variables, clase, pesos, variables de 202108 e identificadores.
def load_training(output,sort_catboost=False):
    path=output/PARQUET457
    meta=pq.ParquetFile(path)
    features=meta.schema_arrow.names[2:-1]
    exigir(meta.metadata.num_rows==FILAS and len(features)==457 and hashlib.sha256('\n'.join(features).encode()).hexdigest()==HASH_FULL457,'Parquet/FULL457 inválido')
    train=pd.read_parquet(path,columns=CLAVES+features+[TARGET],filters=[('foto_mes','in',list(PESOS))],engine='pyarrow').reset_index(drop=True)
    # Proyección August explícitamente SIN target.
    august=pd.read_parquet(path,columns=['numero_de_cliente']+features,filters=[('foto_mes','==',202108)],engine='pyarrow').reset_index(drop=True)
    if sort_catboost:
        train=train.sort_values(CLAVES,kind='stable').reset_index(drop=True)
    exigir(len(train)==491166 and not train.duplicated(CLAVES).any(),'Train inválido')
    for mes,expected in ESPERADOS.items():
        q=train.loc[train.foto_mes.eq(mes)]
        exigir(len(q)==expected['filas'] and q[TARGET].value_counts().to_dict()=={k:v for k,v in expected.items() if k!='filas'},'Conteos train inválidos')
    weights=train.foto_mes.map(PESOS).to_numpy()
    exigir(weights.sum()==450345.0,'Pesos inválidos')
    ids=august.numero_de_cliente.to_numpy()
    exigir(len(ids)==164647 and len(np.unique(ids))==164647 and pd.api.types.is_integer_dtype(ids.dtype),'August IDs inválidos')
    return train[features],train[TARGET],weights,august[features],ids

# [Anotación · líneas 231–253] load_lightgbm_matrices, primera parte: valida el parquet FULL762 (filas, 762
#   nombres, hash), lee claves y clase de los tres meses de entrenamiento ordenadas por cliente y mes, repite
#   los controles de filas, conteos y suma de pesos, y lee los numero_de_cliente de 202108 ordenados de menor a
#   mayor. Arma los índices que fijan la posición de cada fila en las matrices.
def load_lightgbm_matrices(output, temporary):
    path = output/PARQUET762
    meta = pq.ParquetFile(path)
    features = meta.schema_arrow.names[2:-1]
    exigir(meta.metadata.num_rows == FILAS and len(features) == 762
           and hashlib.sha256('\n'.join(features).encode()).hexdigest() == HASH_FULL762,
           'Parquet/FULL762 inválido')
    keys = pd.read_parquet(path, columns=CLAVES+[TARGET], filters=[('foto_mes','in',list(PESOS))])
    keys = keys.sort_values(CLAVES, kind='stable').reset_index(drop=True)
    exigir(len(keys) == 491166 and not keys.duplicated(CLAVES).any() and not keys[CLAVES+[TARGET]].isna().any().any(), 'Train inválido')
    for mes, expected in ESPERADOS.items():
        q = keys.loc[keys.foto_mes.eq(mes)]
        exigir(len(q) == expected['filas'] and q[TARGET].value_counts().to_dict()
               == {k:v for k,v in expected.items() if k!='filas'}, 'Conteos train inválidos')
    weights = keys.foto_mes.map(PESOS).to_numpy()
    exigir(weights.sum() == 450345., 'Pesos inválidos')
    # Sólo IDs en August; su target nunca entra en las matrices o labels.
    august = pd.read_parquet(path, columns=['numero_de_cliente'], filters=[('foto_mes','==',202108)])
    august = august.sort_values('numero_de_cliente', kind='stable').reset_index(drop=True)
    ids = august.numero_de_cliente.to_numpy()
    exigir(len(ids) == 164647 and len(np.unique(ids)) == 164647 and pd.api.types.is_integer_dtype(ids.dtype), 'August IDs inválidos')
    index_train = pd.MultiIndex.from_frame(keys[CLAVES])
    index_august = pd.Index(ids)
# [Anotación · líneas 254–274] Segunda parte: crea dos matrices float64 respaldadas en disco (np.memmap)
#   dentro de la carpeta temporal, una de 491.166 x 762 para entrenar y otra de 164.647 x 762 para 202108.
#   Recorre el parquet en lotes de 5.000 filas sin hilos, ubica cada fila por su clave y copia sus 762 valores;
#   exige que cada posición se llene una sola vez y que no quede ninguna vacía. Devuelve matrices, clase, pesos,
#   identificadores y nombres.
    matrices = []
    dataset = ds.dataset(path, format='parquet')
    for name, index, filter_ in [
        ('train',index_train,ds.field('foto_mes').isin(list(PESOS))),
        ('august',index_august,ds.field('foto_mes')==202108),
    ]:
        matrix = np.memmap(temporary/name, mode='w+', dtype=np.float64, shape=(len(index),762), order='C')
        seen = np.zeros(len(index), dtype=bool)
        scanner = dataset.scanner(columns=CLAVES+features, filter=filter_, batch_size=5000,
                                  batch_readahead=1,fragment_readahead=1,use_threads=False)
        for batch in scanner.to_batches():
            frame = batch.to_pandas()
            wanted = pd.MultiIndex.from_frame(frame[CLAVES]) if name=='train' else frame.numero_de_cliente
            positions = index.get_indexer(wanted)
            exigir((positions>=0).all() and not seen[positions].any(), 'Universo de matriz incorrecto')
            matrix[positions] = frame[features].to_numpy(dtype=np.float64)
            seen[positions] = True
        exigir(seen.all(), 'Matriz incompleta')
        matrix.flush()
        matrices.append(matrix)
    return matrices[0], keys[TARGET].to_numpy(), weights, matrices[1], ids, features

# [Anotación · líneas 276–285] train_lightgbm_full762: importa lightgbm, exige que output/lightgbm no exista,
#   la crea, abre dentro una carpeta temporal con prefijo _temporary_, exige que esa carpeta quede dentro de
#   output/lightgbm y carga allí las matrices con load_lightgbm_matrices.
def train_lightgbm_full762(output):
    import lightgbm
    destination = output/'lightgbm'
    exigir(not destination.exists(), 'Salida LightGBM existente')
    destination.mkdir()
    probabilities, records = [], []
    with tempfile.TemporaryDirectory(dir=destination, prefix='_temporary_') as directory:
        temporary = Path(directory).resolve()
        exigir(temporary.is_relative_to(destination.resolve()), 'Directorio temporal inseguro')
        x,y,w,a,ids,features = load_lightgbm_matrices(output,temporary)
# [Anotación · líneas 286–304] Para cada una de las cinco semillas entrena un LGBMClassifier con los
#   parámetros MULTICLASS, random_state igual a la semilla y los pesos por fila; exige 1.200 árboles y 762
#   variables; toma de predict_proba la columna de BAJA+2 según classes_ para 202108, exige valores entre 0 y 1
#   y la guarda en scores_seed_<semilla>.parquet, registrando el tiempo del ajuste. Al terminar cierra las
#   matrices en disco.
        try:
            for seed in SEEDS:
                print(f'INICIO LightGBM FULL762 seed={seed}',flush=True)
                start = time.perf_counter()
                model = lightgbm.LGBMClassifier(**MULTICLASS,random_state=seed)
                model.fit(x,y,sample_weight=w,feature_name=features)
                exigir(model.n_estimators_==1200 and model.n_features_in_==762, 'Fit incompleto')
                classes = list(model.classes_)
                prob = model.predict_proba(a)[:,classes.index('BAJA+2')]
                exigir(len(prob)==len(ids) and np.isfinite(prob).all() and ((prob>=0)&(prob<=1)).all(), 'Probabilidades inválidas')
                probabilities.append(prob)
                save_parquet(destination/f'scores_seed_{seed}.parquet',pd.DataFrame(dict(numero_de_cliente=ids,prob_BAJA2=prob)))
                records.append(dict(seed=seed,classes=classes,iterations=model.n_estimators_,seconds=time.perf_counter()-start))
                print(records[-1],flush=True)
                del model
                gc.collect()
        finally:
            x._mmap.close()
            a._mmap.close()
# [Anotación · líneas 305–309] Promedia las cinco probabilidades y guarda ranking_ensemble.parquet (rank,
#   numero_de_cliente, score promedio, u normalizado y una columna p_seed_ por semilla) y auditoria.json con
#   semillas, parámetros, cantidad de variables, hash, pesos y los registros de cada ajuste.
    score = np.mean(np.stack(probabilities),axis=0)
    save_parquet(destination/'ranking_ensemble.parquet',ranking(ids,score,dict(u=normalizar(score,ids),**{f'p_seed_{s}':p for s,p in zip(SEEDS,probabilities)})))
    save_json(destination/'auditoria.json',dict(fits=5,seeds=SEEDS,parameters=MULTICLASS,features=762,
              feature_hash=HASH_FULL762,weights=PESOS,row_order='numero_de_cliente ASC, foto_mes ASC',
              matrix_dtype='float64',target_August_used=False,target_July_used=False,records=records))

# [Anotación · líneas 311–322] train_family despacha según la familia: 'lightgbm' llama a
#   train_lightgbm_full762; 'catboost' exige que output/catboost no exista, carga con load_training el
#   entrenamiento FULL457 ordenado por cliente y mes, importa CatBoostClassifier, define un constructor con
#   PARAMETROS y random_seed igual a la semilla, crea la carpeta e inicia las listas de probabilidades y de
#   registros.
def train_family(output,family):
    exigir(family in ('lightgbm','catboost'), 'Familia desconocida')
    if family == 'lightgbm':
        return train_lightgbm_full762(output)
    destination=output/family
    exigir(not destination.exists(),f'Salida existente: {destination}')
    x,y,w,a,ids=load_training(output,sort_catboost=family=='catboost')
    from catboost import CatBoostClassifier
    constructor=lambda seed:CatBoostClassifier(**PARAMETROS,random_seed=seed)
    destination.mkdir()
    probabilities=[]
    records=[]
# [Anotación · líneas 323–333] Para cada una de las cinco semillas ajusta CatBoost con los pesos por fila,
#   toma la probabilidad de BAJA+2 para 202108 según classes_, exige valores entre 0 y 1 y la guarda en
#   scores_seed_<semilla>.parquet con el tiempo del ajuste.
    for seed in SEEDS:
        print(f'INICIO {family} seed={seed}',flush=True)
        start=time.perf_counter(); model=constructor(seed)
        model.fit(x,y,sample_weight=w)
        classes=list(model.classes_)
        prob=model.predict_proba(a)[:,classes.index('BAJA+2')]
        exigir(len(prob)==len(ids) and np.isfinite(prob).all() and ((prob>=0)&(prob<=1)).all(),'Probabilidades inválidas')
        probabilities.append(prob)
        save_parquet(destination/f'scores_seed_{seed}.parquet',pd.DataFrame(dict(numero_de_cliente=ids,prob_BAJA2=prob)))
        records.append(dict(seed=seed,classes=classes,seconds=time.perf_counter()-start))
        print(records[-1],flush=True); del model; gc.collect()
# [Anotación · líneas 334–338] Promedia las cinco probabilidades de CatBoost y guarda ranking_ensemble.parquet
#   y auditoria.json con el mismo formato que en LightGBM, registrando 457 variables.
    score=np.mean(np.stack(probabilities),axis=0)
    save_parquet(destination/'ranking_ensemble.parquet',ranking(ids,score,dict(u=normalizar(score,ids),**{f'p_seed_{s}':p for s,p in zip(SEEDS,probabilities)})))
    save_json(destination/'auditoria.json',dict(fits=5,seeds=SEEDS,parameters=PARAMETROS,features=457,
              feature_hash=HASH_FULL457,weights=PESOS,row_order='numero_de_cliente ASC, foto_mes ASC',
              target_August_used=False,target_July_used=False,records=records))
```

### src/04_build_final_c25.py

Cuarto paso: combina los rankings de LightGBM y CatBoost con pesos 0,75 y 0,25 sobre el rank normalizado, escribe el CSV con 12.000 clientes y compara su SHA256 con el esperado.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–7] Importa todo common.py con from common import *, toma la carpeta de salida y exige
#   que no existan todavía el CSV final ni ranking_c25.parquet.
"""Z636 congelado: .75*rank_normalizado(LGBM FULL762)+.25*rank_normalizado(CatBoost FULL457)."""
from common import *

def main():
    output=args(__doc__).parse_args().output_dir
    dest=output/SUBMISSION_NAME
    exigir(not dest.exists() and not (output/'ranking_c25.parquet').exists(),'Salida existente')
# [Anotación · líneas 8–11] Lee auditoria.json de cada familia y exige 5 ajustes, las mismas cinco semillas,
#   762 variables en LightGBM y 457 en CatBoost y el hash de nombres de cada lista.
    for family,size,digest in [('lightgbm',762,HASH_FULL762),('catboost',457,HASH_FULL457)]:
        audit=json.loads((output/family/'auditoria.json').read_text(encoding='utf-8'))
        exigir(audit['fits']==5 and audit['seeds']==SEEDS and audit['features']==size
               and audit['feature_hash']==digest,'Familia/features incorrectas')
# [Anotación · líneas 12–16] Carga ranking_ensemble.parquet de las dos familias, toma el orden de clientes de
#   LightGBM, exige 164.647 identificadores únicos y el mismo conjunto en ambas, y reordena CatBoost a ese
#   orden.
    l=pd.read_parquet(output/'lightgbm/ranking_ensemble.parquet',engine='pyarrow')
    c=pd.read_parquet(output/'catboost/ranking_ensemble.parquet',engine='pyarrow')
    ids=l.numero_de_cliente.to_numpy()
    exigir(len(ids)==164647 and l.numero_de_cliente.is_unique and c.numero_de_cliente.is_unique and np.array_equal(np.sort(ids),np.sort(c.numero_de_cliente)),'IDs entre familias inválidos')
    c=c.set_index('numero_de_cliente').reindex(ids)
# [Anotación · líneas 17–24] Para cada familia toma las cinco columnas p_seed_, exige valores finitos entre 0
#   y 1, recalcula el promedio y exige que sea idéntico a la columna score guardada.
    means=[]
    for q in [l,c]:
        cols=[f'p_seed_{s}' for s in SEEDS]
        probabilities=[q[col].to_numpy() for col in cols]
        exigir(all(np.isfinite(p).all() and ((p>=0)&(p<=1)).all() for p in probabilities),'Scores inválidos')
        mean=np.mean(np.stack(probabilities),axis=0)
        exigir(np.array_equal(mean,q.score.to_numpy()),'Ensemble no es media de 5 seeds')
        means.append(mean)
# [Anotación · líneas 25–30] Convierte cada promedio en rank normalizado u, calcula score = 0,75 por u de
#   LightGBM más 0,25 por u de CatBoost, arma el ranking combinado, toma los primeros 12.000 numero_de_cliente,
#   exige que sean únicos y del universo de 202108 y guarda ranking_c25.parquet.
    ul,uc=[normalizar(p,ids) for p in means]
    score=.75*ul+.25*uc
    result=ranking(ids,score,dict(u_lgbm=ul,u_catboost=uc))
    selected=result.numero_de_cliente.iloc[:12000].to_numpy()
    exigir(len(np.unique(selected))==12000 and np.isin(selected,ids).all(),'Selección inválida')
    save_parquet(output/'ranking_c25.parquet',result)
# [Anotación · líneas 31–40] Escribe el CSV de una columna sin encabezado ni índice con saltos LF, calcula su
#   SHA256, guarda final_audit.json con el hash obtenido, el esperado y la fórmula, y termina con error si el
#   hash difiere del esperado; si coincide imprime FINAL REPRODUCIBILITY: PASS.
    with dest.open('x',encoding='utf-8',newline='') as f:
        pd.Series(selected).to_csv(f,header=False,index=False,lineterminator='\n')
    digest=sha256_archivo(dest)
    save_json(output/'final_audit.json',dict(model='Z636 C25 FULL762',SHA256=digest,expected=EXPECTED_CSV,
              match=digest==EXPECTED_CSV,formula='.75*u_lgbm_FULL762+.25*u_catboost_FULL457',
              target_August_used=False,features_LightGBM=762,features_CatBoost=457))
    exigir(digest==EXPECTED_CSV,'CSV diferente del hash oficial: reproducción FAIL')
    print('FINAL REPRODUCIBILITY: PASS')

if __name__=='__main__': main()
```

### src/03_train_catboost.py

Tercer paso: lee --output-dir y llama a train_family de common.py con la familia 'catboost' (cinco semillas sobre FULL457).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–7] Importa args y train_family de common.py, lee --output-dir y ejecuta el
#   entrenamiento de la familia 'catboost'; toda la lógica está en common.py.
from common import args, train_family

def main():
    opts=args('5 seeds CatBoost FULL457 finales congeladas; sin features lag2').parse_args()
    train_family(opts.output_dir,'catboost')

if __name__=='__main__': main()
```

### src/02_train_lightgbm.py

Segundo paso: lee --output-dir y llama a train_family de common.py con la familia 'lightgbm' (cinco semillas sobre FULL762).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–7] Importa args y train_family de common.py, lee --output-dir y ejecuta el
#   entrenamiento de la familia 'lightgbm'; toda la lógica está en common.py.
from common import args, train_family

def main():
    opts=args('5 seeds LightGBM FULL762 finales congeladas; orden cliente/mes').parse_args()
    train_family(opts.output_dir,'lightgbm')

if __name__=='__main__': main()
```


## Explicaciones del alumno (texto original)

### REPRODUCCION.md

> # Z636 FULL END-TO-END REPRODUCTION: PASS
>
> Inicio: 2026-10-11T17:00:45.059857-03:00. Fin: 2026-10-11T20:05:11.172386-03:00.
> Tiempo total: 3 h 04 min 26 s (11065.923 segundos).
>
> Input de datos exclusivo: `data/competencia_01.csv`. Codigo exclusivo: `competencia_01_final/src/`. Salida nueva: `data/reproduccion_final_z636/`.
>
> Entorno: .venv actual, sin copia ni reinstalacion. Se habilitaron las ubicaciones ya instaladas de las bibliotecas LightGBM/PyArrow. No se leyeron ni reutilizaron artefactos predictivos historicos.
>
> Las copias temporales de preparacion del entorno y la primera salida parcial interrumpida por captura de consola se eliminaron antes de esta ejecucion. Esta ejecucion genero ambos parquet y realizo diez fits desde cero.
>
> El codigo y toda la documentacion del paquete permanecieron identicos a sus hashes iniciales. REPRODUCCION.md del paquete no se modifico por la ultima instruccion; este informe registra los resultados reales fuera del paquete.
>
> | Etapa | Segundos | Resultado |
> |---|---:|---|
> | 01_feature_engineering.py | 115.777 | PASS |
> | 02_train_lightgbm.py | 7266.237 | PASS |
> | 03_train_catboost.py | 3678.410 | PASS |
> | 04_build_final_c25.py | 3.421 | PASS |
> | 05_verify_submission.py | 1.292 | PASS |
>
> ## Versiones
>
> Python 3.12.0.
> - numpy==2.5.2
> - pandas==3.0.5
> - scipy==1.18.1
> - scikit-learn==1.9.0
> - lightgbm==4.7.0
> - catboost==1.2.10
> - pyarrow==25.0.0
> - graphviz==0.21
> - matplotlib==3.11.1
> - plotly==7.0.0
> - six==1.17.0
> - python-dateutil==2.9.0.post0
>
> ## Comandos
>
> Con el .venv auditado y las ubicaciones de bibliotecas instaladas habilitadas:
>
> ```powershell
> .venv/Scripts/python.exe -B competencia_01_final/src/01_feature_engineering.py --output-dir data/reproduccion_final_z636 --input data/competencia_01.csv
> .venv/Scripts/python.exe -B competencia_01_final/src/02_train_lightgbm.py --output-dir data/reproduccion_final_z636
> .venv/Scripts/python.exe -B competencia_01_final/src/03_train_catboost.py --output-dir data/reproduccion_final_z636
> .venv/Scripts/python.exe -B competencia_01_final/src/04_build_final_c25.py --output-dir data/reproduccion_final_z636
> .venv/Scripts/python.exe -B competencia_01_final/src/05_verify_submission.py --output-dir data/reproduccion_final_z636
> ```
>
> ## Controles
>
> FULL457: `c3578882fcf1adf79df9c20c472864719672522fa2ee9283d4a9b1c0fe080c12`.
> FULL762: `1e9747955f214a8ddcb405af0e3a71d4a516f1818bf829c0d6c14ca0f934e8f6`.
> CSV: `00534f4c23bb87c5e0962ee615a0f81740cf1e2f3e64232c7af5bc83aae697a0`.
> 12000 IDs unicos, sin header/index, todos August. Cinco scores finitos por familia, 164647 IDs por seed; ensemble igual a media aritmetica de cinco probabilidades.
>
> No se utilizo target August para entrenar, predecir ni verificar IDs. La ingenieria transporta el target y valida su preservacion, conforme al codigo auditado.
>
> La comparacion con los originales historicos no se realizo para respetar la ultima prohibicion de lectura de esos artefactos. La identidad byte a byte exigida del CSV queda demostrada por el hash oficial.
>
> No se modifico competencia_01_final/, .venv ni ningun artefacto historico. No se ejecutaron comandos git ni uploads.

### AUDITORIA_ENTREGA.md

> # Auditoría de entrega — FINAL Z636 C25 FULL762
>
> **Z636 PACKAGE STATIC AUDIT: PASS**
>
> Alcance: código, features, parámetros, orden, fórmula, verificación del CSV y seguridad del paquete. La reproducción end-to-end está diferida. No se ejecutan fits, tuning, uploads, git add, commit ni push. No se modifica el repositorio de entrega publicado.
>
> Modelo final oficial: Z636 C25 FULL762. Public gain informado: 98.6150 M. Submission ID: 1560-1791746981180245.
>
> LightGBM usa FULL762 y CatBoost FULL457; ambos entrenan April+May+June con pesos .75/1/1 y orden estable cliente/mes. Los hiperparámetros y seeds se conservan, definidos en `src/common.py`. La etapa LightGBM utiliza matrices float64 por lotes para limitar memoria, con valores y orden idénticos al protocolo de referencia. Los temporales propios se eliminan al cerrar las matrices. CatBoost conserva FULL457, tipos numéricos y configuración original.
>
> FULL457:
> `c3578882fcf1adf79df9c20c472864719672522fa2ee9283d4a9b1c0fe080c12`
>
> FULL762:
> `1e9747955f214a8ddcb405af0e3a71d4a516f1818bf829c0d6c14ca0f934e8f6`
>
> CSV final:
> `00534f4c23bb87c5e0962ee615a0f81740cf1e2f3e64232c7af5bc83aae697a0`
>
> ## Seguridad y autonomía
>
> Sólo código y documentación. Fuente original en `data/competencia_01.csv`, aportada externamente por el usuario. Las salidas se crean en `output/`, excluido de Git. No hay acceso a modelos, scores o código histórico desde los scripts del paquete. Las referencias del manifiesto son informativas y nunca se resuelven como rutas.
>
> Las proyecciones de modelado y verificación August excluyen target. La ingeniería transporta la columna de target, y sólo audita los meses del train. No se entrena ni selecciona con etiquetas July/August.
>
> Requirements permanece intacto con versiones exactas: numpy 2.5.2, pandas 3.0.5, scipy 1.18.1, scikit-learn 1.9.0, lightgbm 4.7.0, catboost 1.2.10, pyarrow 25.0.0, graphviz 0.21, matplotlib 3.11.1, plotly 7.0.0, six 1.17.0 y python-dateutil 2.9.0.post0. Python 3.12.0. No se agregaron dependencias ni se instalaron paquetes.
>
> ## Archivos exactos del paquete
>
> ```text
> .gitignore
> AUDITORIA_ENTREGA.md
> README.md
> REPRODUCCION.md
> fuentes_auditadas.json
> requirements.txt
> src/01_feature_engineering.py
> src/02_train_lightgbm.py
> src/03_train_catboost.py
> src/04_build_final_c25.py
> src/05_verify_submission.py
> src/common.py
> ```
>
> ## Controles ejecutados
>
> - Sintaxis e importación de los seis módulos: PASS; no se invocó ningún fit.
> - Igualdad de FULL457/FULL762 y sus hashes con las referencias: PASS.
> - Fixture de 152 variables: huecos mensuales, enero/febrero y cambio de año, registro existente con NaN, deltas sin imputación e indicadores int8: PASS.
> - Prefijo FULL457 exactamente igual a la implementación anterior: PASS. Valores FULL762 float64 iguales a las funciones puras de la referencia: PASS.
> - Roundtrip de un parquet sintético pequeño y orden cliente/mes: PASS; temporales propios eliminados, fuera del paquete.
> - Seeds, pesos y diccionarios de parámetros comparados por igualdad con las auditorías de referencia: PASS. CatBoost permanece en 457 columnas; LightGBM en 762.
> - Ranking con empate, normalización y combinación en memoria con probabilidades existentes: SHA256 oficial exacto. No se crearon CSV finales ni se incorporaron scores al paquete.
> - Verificador sobre el CSV oficial existente en lectura: 12000 IDs únicos, sin header/index, pertenencia a August usando sólo la columna de IDs y SHA256 exacto: PASS.
> - Requirements intacto, todas sus versiones exactas: PASS; sin nuevas dependencias ni instalaciones.
> - Inventario: exactamente los 12 archivos listados. No hay datos, parquet, scores, modelos, CSV, archivos privados, credenciales, claves ni archivos grandes.
> - Referencias restantes al modelo anterior: 0. Las referencias a Z636 corresponden a modelo oficial, nombre del CSV, documentación y manifiesto informativo.
> - Rutas absolutas personales y dependencias históricas en el código: NONE. Imports locales limitados a `common.py`; sólo se consumen el CSV original y las salidas propias.
> - Git ignore comprobado con paths NUL-delimited: dataset, parquet, CSV final, scores, modelos, `.env`, claves y archivos históricos excluidos; código y documentación previstos incluidos.
>
> La entrada predeterminada pasó a `data/competencia_01.csv` dentro del paquete. No se copió el dataset. El fichero `fuentes_auditadas.json` registra hashes de las fuentes informativas y del código actual, sin ubicaciones privadas ni dependencias de ejecución.
>
> **0 fits. 0 tuning. 0 uploads. 0 git add. 0 commit. 0 push.**
>
> ## Alcance pendiente
>
> PASS estático no demuestra identidad de nuevos entrenamientos. Se debe ejecutar una reproducción completa independiente para confirmar el CSV final byte a byte, usando el entorno fijado y sin cambiar parámetros ante diferencias. El tiempo observado de la referencia no es una medición del paquete actualizado. Public sólo es metadata informativa suministrada por el autor.

### README.md

> # Competencia 01 — FINAL Z636 C25 FULL762
>
> **FINAL = Z636 C25 FULL762.** Public gain: **98.6150 M**. Submission ID: **1560-1791746981180245**. Resultado informado por el autor; no participa en el pipeline ni en la selección metodológica.
>
> Entrega autocontenida en código. Requiere el dataset original, que **no se incluye**. Tampoco se incluyen parquet, scores, modelos ni CSV final. No realiza uploads.
>
> ## Entrada y entorno
>
> Obtener el CSV por el canal autorizado y colocarlo en `data/competencia_01.csv` dentro de esta carpeta. No publicarlo. SHA256 de la fuente:
>
> ```text
> 53fd6265cfa565224fa4370e1fabe72d343a5c76540eb769758686a194bb5dfd
> ```
>
> Requiere Python **3.12.0**, preferentemente Windows x64, y las versiones exactas de `requirements.txt`. Desde esta carpeta, en PowerShell:
>
> ```powershell
> py -3.12 -m venv .venv
> .venv/Scripts/python.exe -m pip install -r requirements.txt
> .venv/Scripts/python.exe -B src/01_feature_engineering.py
> .venv/Scripts/python.exe -B src/02_train_lightgbm.py
> .venv/Scripts/python.exe -B src/03_train_catboost.py
> .venv/Scripts/python.exe -B src/04_build_final_c25.py
> .venv/Scripts/python.exe -B src/05_verify_submission.py
> ```
>
> Ejecutar los cinco pasos exactamente en ese orden. El primero requiere una carpeta `output/` nueva. Ningún paso sobrescribe salidas; ante un error, detenerse e investigar sin cambiar parámetros. Todos aceptan `--output-dir`; usar la misma ruta en todos los pasos. El primer paso admite `--input` para otra ubicación del CSV. El verificador admite `--submission` y `--features` si se necesitan rutas explícitas. Los valores predeterminados se resuelven respecto de esta carpeta, sin rutas personales ni dependencias del directorio de trabajo.
>
> ## Arquitectura congelada
>
> **LightGBM utiliza exclusivamente FULL762. CatBoost utiliza exclusivamente FULL457.** Ambos entrenan cinco seeds desde cero en una reproducción completa; el código no reutiliza modelos o scores históricos.
>
> FULL457, preservando el orden de las 152 variables originales en el CSV:
>
> 1. 152 originales.
> 2. 152 `<feature>_lag1`.
> 3. 152 `<feature>_delta_lag1`.
> 4. `lag1_disponible`.
>
> Lag1 corresponde al mismo cliente exactamente un mes calendario antes. FULL762 conserva ese prefijo y agrega 152 `<feature>_lag2`, 152 `<feature>_delta_lag2` y `lag2_disponible`. Lag2 corresponde al mismo cliente exactamente **dos meses calendario antes**, incluyendo cambios de año; no es un shift por filas. Un registro de hace dos meses puede existir aunque falte el mes intermedio. Cada delta es actual menos lag, sin imputación. Los indicadores miden existencia del registro, aunque sus variables sean NaN.
>
> Hashes SHA256 de nombres unidos con `\n` en UTF-8, sin salto final:
>
> | Features | SHA256 |
> |---|---|
> | FULL457 | `c3578882fcf1adf79df9c20c472864719672522fa2ee9283d4a9b1c0fe080c12` |
> | FULL762 | `1e9747955f214a8ddcb405af0e3a71d4a516f1818bf829c0d6c14ca0f934e8f6` |
>
> La ingeniería genera dos parquet independientes, con 983061 filas cada uno, conserva el orden del CSV y relee sus valores antes de aceptarlos. En ambos modelos el train se ordena estable por `numero_de_cliente ASC, foto_mes ASC`: abril+mayo+junio de 2021, 491166 filas, pesos 0.75/1/1 y suma 450345. No se entrena con July. August tiene 164647 IDs únicos y se proyecta sin target para entrenamiento/predicción y verificación de IDs. La ingeniería transporta `clase_ternaria`; sólo se auditan las etiquetas de los meses de entrenamiento.
>
> Seeds, en orden: **290497, 100003, 200003, 300007, 400009**. Hiperparámetros exactos en `src/common.py`: LightGBM multiclass, 1200 iteraciones; CatBoost MultiClass CPU, 1000 iteraciones, FULL457 y sin class weights. No hay tuning, early stopping ni cambios de pesos. LightGBM usa matrices float64 por lotes con respaldo temporal en disco, sin reducir precisión; CatBoost conserva las columnas FULL457 y sus tipos numéricos.
>
> Se extrae P(BAJA+2) usando `classes_`. Cada familia promedia las cinco probabilidades antes de rankear todos los clientes, score DESC e ID ASC. Con rank desde 1:
>
> ```text
> u = (M-rank)/(M-1)
> C25 = 0.75*u_lgbm_full762 + 0.25*u_catboost_full457
> ```
>
> C25 se ordena directamente por ese score DESC e ID ASC, sin otra normalización. Se escriben 12000 IDs, una columna, sin header/index, UTF-8 sin BOM y LF incluyendo el final.
>
> ## Selección metodológica
>
> El peso 75/25 se seleccionó históricamente en May/June antes de transferir el modelo a August. Lag2 se evaluó sin utilizar August: en June, LightGBM FULL762 mejoró de 669 a 686 TP (**+17**) y mejoraron **5/5 seeds**. Dentro de C25, sustituir sólo LightGBM manteniendo CatBoost FULL457 produjo 688 a 695 TP (**+7**), con **5/5 seeds** positivas; May permaneció en 520. July no proporcionaba target completo utilizable y no se imputaron etiquetas.
>
> La transferencia estructural June→August se auditó antes de submission. No se utilizaron labels August para seleccionar modelo, features, peso ni hiperparámetros. El resultado Public indicado arriba es posterior e informativo.
>
> ## Salida y estado de reproducción
>
> Salida final: `output/submit_z636_c25_full762_n12000.csv`. SHA256 obligatorio:
>
> ```text
> 00534f4c23bb87c5e0962ee615a0f81740cf1e2f3e64232c7af5bc83aae697a0
> ```
>
> El constructor y el verificador terminan con error si el hash difiere. `output/` contiene los dos parquet, auditoría de features, cinco scores y ranking ensemble por familia, `ranking_c25.parquet`, `final_audit.json` y el CSV. Todo queda ignorado por Git.
>
> **Reproducción integral Z636: PASS.**
> Se ejecutó el pipeline completo desde cero, incluyendo generación de features, entrenamiento de cinco seeds LightGBM FULL762, cinco seeds CatBoost FULL457, construcción del ensamble C25 y verificación del CSV final. Tiempo total: 3 h 04 min 26 s. Se verificaron 12.000 IDs únicos, sin encabezado, correspondientes a agosto, y el SHA256 final 00534f4c23bb87c5e0962ee615a0f81740cf1e2f3e64232c7af5bc83aae697a0.
> El estado y el alcance de las verificaciones están en `REPRODUCCION.md` y `AUDITORIA_ENTREGA.md`. La generación de referencia FULL762 observada tardó **1 h 57 min 50 s**, reutilizando CatBoost; ese tiempo no es una medición end-to-end de este paquete. Reservar varias horas, al menos 16 GB RAM y espacio para ambos parquet y unos 4 GB adicionales de matrices temporales. Los tiempos dependen de hardware/carga. Un SHA de parquet distinto por serialización no determina identidad predictiva; el CSV sí debe coincidir exactamente.

