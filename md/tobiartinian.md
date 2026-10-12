# Tobias Artinian — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: tobiartinian
- Repositorio: https://github.com/tobiartinian/Econom-a-y-Finanzas
- Link posteado: https://github.com/tobiartinian/Econom-a-y-Finanzas/blob/main/EDA.ipynb
- Commit: 39656949b062172cf3caff15b5289ee644092929
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/tobiartinian/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/tobiartinian.json

## Resumen

El repositorio contiene seis notebooks de Python, cada uno con un enlace para abrirlo en Google Colab, y un README de dos líneas. El enlace posteado apunta a EDA.ipynb, un análisis exploratorio con consultas SQL en DuckDB y un Random Forest que ordena las variables por importancia; ese notebook no genera predicciones. El archivo de predicción que el código llama final sale de dos notebooks: z101_target_sql.ipynb construye clase_ternaria a partir del dataset crudo y exporta competencia_01.csv, y Submission.ipynb agrega a cada variable su valor en la fila anterior del cliente (lag 1), carga los hiperparámetros de un estudio de Optuna guardado en Google Drive (el código de esa optimización no está en el repositorio), entrena un LightGBM binario (positivo = BAJA+2) con los meses 202103 a 202106 durante 400 iteraciones con random_state 772859, predice 202108 y escribe submission_final.csv con los clientes de probabilidad mayor o igual a 0.025. Modelo.ipynb contiene otra variante, con hiperparámetros escritos en el código, partición aleatoria 80/20, detención temprana y una función de ganancia, que escribe submission_2.csv. Features_Enginering.ipynb guarda en Drive la tabla con lags de 202103 a 202106 y Clase_3.ipynb entrena árboles de decisión sobre 202104 y busca sus hiperparámetros con Optuna. El repositorio no indica cuál de los archivos se envió.

**Qué entrega.** Submission.ipynb escribe submission_final.csv: una columna sin encabezado con los numero_de_cliente de 202108 cuya probabilidad predicha es mayor o igual a 0.025. Según la salida guardada en el notebook, son 8295 clientes. El archivo no está en el repositorio y ningún texto indica cuál fue el envío; Modelo.ipynb escribe otro archivo, submission_2.csv (8371 clientes según su salida guardada).

**Cómo se ejecuta.** No se indica. Cada notebook empieza con un enlace para abrirlo en Google Colab y usa rutas de Google Drive (/content/drive/MyDrive/...).

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: target = 1 si clase_ternaria es 'BAJA+2' y 0 en cualquier otro caso (Submission.ipynb, línea 77).
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** —
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código: entrena con todas las filas de 202103 a 202106.
- **Calidad de datos:** No se observa en el código
- **Drifting:** No se observa en el código
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** Lag de orden 1 de cada columna del CSV salvo foto_mes, numero_de_cliente y clase_ternaria, calculado en DuckDB con LAG(col, 1) OVER (PARTITION BY numero_de_cliente ORDER BY foto_mes) y sufijo _lag1: toma el valor de la fila anterior del mismo cliente. Un comentario y la salida guardada de Modelo.ipynb mencionan 152 variables con lag.
- **Selección de variables:** No se observa en el código: usa todas las columnas de la tabla (originales y lags) salvo foto_mes, numero_de_cliente y clase_ternaria.
- **Optimización de hiperparámetros:** Submission.ipynb no ejecuta una búsqueda: carga con optuna.load_study un estudio existente (exp_101_lgbm-opt) desde el archivo SQLite /content/drive/MyDrive/DMEyF/2026/notebooks/data/optimization_lgbm.db y toma study.best_params. El código que crea y corre ese estudio no está en el repositorio.
- **Hiperparámetros finales:** Los de study.best_params más objective=binary, metric=auc, boosting_type=gbdt, random_state=772859, n_jobs=1 y verbose=-1, con num_boost_round=400. Según la salida guardada en Submission.ipynb, los valores recuperados del estudio son learning_rate=0.05407060814866634, num_leaves=20, min_child_samples=355, feature_fraction=0.7683542504735678, bagging_fraction=0.7923122547071753 y bagging_freq=1.
- **Semillas:** Una semilla escrita en el código: random_state=772859 en los parámetros de LightGBM (Submission.ipynb, línea 62).
- **Cantidad de semillas:** 1
- **Ensamble:** No se observa en el código: entrena un solo modelo.
- **Corte:** Umbral de probabilidad fijo: conserva los clientes de 202108 con probabilidad mayor o igual a 0.025 (variable umbral_optimo).
- **Validación:** No se observa en Submission.ipynb: entrena con todas las filas de 202103 a 202106, sin conjunto de validación. Fuera del camino de la entrega, Modelo.ipynb separa esos mismos meses al azar en 80 % y 20 % (estratificado, random_state=42) y mide AUC y una función de ganancia con umbral 0.025.
- **Salidas:** submission_final.csv, con la columna numero_de_cliente sin índice ni encabezado. El notebook también crea el archivo de base de datos competencia.duckdb en el directorio de trabajo.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Lags (`variables.lags`)
- Optuna (`hiperparametros.optuna`)
- Corta por umbral de probabilidad (`corte.umbral_probabilidad`)

## Técnicas sólo exploradas

- Random Forest (`modelo.random_forest`)
- Árbol de decisión (rpart u otro) (`modelo.arbol_decision`)
- Tres clases (CONTINUA, BAJA+1, BAJA+2) (`clase.multiclase`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: no
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: No se declara en ningún texto. Los notebooks traen metadatos y enlaces de Google Colab; las salidas guardadas de las celdas de instalación muestran rutas de Python 3.13 (/usr/local/lib/python3.13/dist-packages) y la descarga de optuna 5.0.0.

## Pasos del camino de la entrega

1. **Descarga del dataset crudo.** Monta Google Drive y, si competencia_01_crudo.csv no está en la carpeta /content/drive/MyDrive/Economía y finanzas, lo descarga con requests desde storage.googleapis.com/open-courses/dmeyf2026-9c6f. (`z101_target_sql.ipynb` líneas 11–40)
2. **Carga del crudo en DuckDB.** Abre una conexión DuckDB en memoria para las celdas SQL y crea la tabla competencia_01_crudo leyendo el CSV con read_csv_auto. (`z101_target_sql.ipynb` líneas 55–65; `z101_target_sql.ipynb` líneas 80–85)
3. **Construcción de clase_ternaria.** Cruza todos los clientes con todos los períodos, marca con mes_0 si el cliente tiene fila en cada mes y con mes_1 y mes_2 si la tiene uno y dos períodos después, y asigna en orden: CONTINUA si mes_2 = 1; BAJA+2 si mes_1 = 1 y mes_2 = 0; BAJA+1 si mes_1 = 0; nulo si mes_1 o mes_2 son nulos. Conserva las filas con mes_0 = 1 en la tabla competencia_01. (`z101_target_sql.ipynb` líneas 238–264)
4. **Exportación a CSV.** Exporta la tabla competencia_01 a un CSV con encabezado mediante COPY; la ruta se arma con el valor de dataset_path seguido de competencia_01.csv. (`z101_target_sql.ipynb` líneas 292–293)
5. **Tabla con lags de orden 1.** Submission.ipynb abre competencia.duckdb y, si la tabla competencia_01 no existe, la crea desde /content/drive/MyDrive/Economía y finanzas/competencia_01.csv con todas las columnas más el lag 1 de cada una (salvo foto_mes, numero_de_cliente y clase_ternaria), particionando por numero_de_cliente y ordenando por foto_mes. (`Submission.ipynb` líneas 14–45)
6. **Hiperparámetros desde un estudio de Optuna.** Carga el estudio exp_101_lgbm-opt desde un archivo SQLite en Google Drive, toma study.best_params y le agrega objective=binary, metric=auc, boosting_type=gbdt, random_state=772859, n_jobs=1 y verbose=-1. (`Submission.ipynb` líneas 47–65)
7. **Conjunto de entrenamiento y clase binaria.** Define como variables todas las columnas de la tabla salvo foto_mes, numero_de_cliente y clase_ternaria, y trae las filas de 202103 a 202106 con una columna target que vale 1 cuando clase_ternaria es 'BAJA+2'. (`Submission.ipynb` líneas 67–84)
8. **Entrenamiento del LightGBM.** Entrena un modelo con lgb.train sobre todas esas filas durante 400 iteraciones, sin conjunto de validación. (`Submission.ipynb` líneas 86–93)
9. **Predicción sobre 202108.** Trae las filas de foto_mes = 202108, selecciona las mismas variables del entrenamiento y calcula la probabilidad de cada cliente. (`Submission.ipynb` líneas 95–108)
10. **Corte por umbral y archivo de salida.** Conserva los clientes con probabilidad mayor o igual a 0.025 y escribe sus numero_de_cliente en submission_final.csv, sin índice ni encabezado. (`Submission.ipynb` líneas 110–118)

## Archivos

- `EDA.ipynb` · secundario · Jupyter (python) · 349 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tobiartinian/EDA.ipynb.txt) — Notebook al que apunta el enlace posteado. Análisis exploratorio de competencia_01.csv con consultas SQL en DuckDB (active_quarter, cliente_vip, internet, cliente_edad y mpasivos_margen por clase_ternaria y por mes), un Random Forest sobre 202103 para listar las 30 variables de mayor importancia y un gráfico de barras. No entrena el modelo de la entrega ni escribe archivos.
- `Modelo.ipynb` · secundario · Jupyter (python) · 201 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tobiartinian/Modelo.ipynb.txt) — Variante del modelo fuera del camino de la entrega: arma la tabla con lags, entrena un LightGBM con hiperparámetros escritos en el código sobre una partición aleatoria 80/20 de 202103 a 202106, calcula AUC y ganancia en la validación, predice 202108 y escribe submission_2.csv. Según sus salidas guardadas: detención en la iteración 257, AUC de validación 0.90630, ganancia 310832500 sobre el 20 % de validación y 8371 clientes en el archivo.
- `z101_target_sql.ipynb` · principal · Jupyter (python) · 311 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tobiartinian/z101_target_sql.ipynb.txt) — Notebook con formato de guía (textos explicativos, preguntas y consultas de ejemplo) que descarga competencia_01_crudo.csv, lo carga en DuckDB, construye clase_ternaria con SQL y exporta el resultado a CSV. La línea 258 conserva el comentario 'Replazar null por la lógica que genera el target' junto a la expresión que asigna la clase.
- `README.md` · explicacion · Markdown · 2 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tobiartinian/README.md.txt) — Dos líneas: el nombre del repositorio y la frase 'Ejercicios y proyectos de economía y finanzas'. No menciona la competencia ni los notebooks.
- `Clase_3.ipynb` · secundario · Jupyter (python) · 207 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tobiartinian/Clase_3.ipynb.txt) — Entrena árboles de decisión de scikit-learn sobre las filas de 202104 con clase_ternaria como variable a predecir, mide la ganancia en 31 particiones aleatorias 70/30 con dos configuraciones y corre un estudio de Optuna de 5 ensayos sobre criterion, max_depth y min_samples_split. Usa las variables data, ganancia_acierto y costo_estimulo, que no se definen en ninguna celda del notebook.
- `Features_Enginering.ipynb` · secundario · Jupyter (python) · 104 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tobiartinian/Features_Enginering.ipynb.txt) — Arma en DuckDB la misma tabla con lags de orden 1 que Modelo.ipynb y Submission.ipynb, trae a pandas las filas de 202103 a 202106 con la columna target y las guarda en /content/drive/MyDrive/Economía y finanzas/df_filtrado.csv. Ningún otro notebook del repositorio lee ese archivo. Define semilla = 772859, que no se usa en el resto del notebook.
- `Submission.ipynb` · principal · Jupyter (python) · 118 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/tobiartinian/Submission.ipynb.txt) — Notebook de una celda de instalación y una celda de código que arma la tabla con lags en DuckDB, recupera los hiperparámetros de un estudio de Optuna, entrena un LightGBM con 202103 a 202106, predice 202108 y escribe submission_final.csv. Según su salida guardada, el archivo tiene 8295 clientes.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### z101_target_sql.ipynb

Notebook con formato de guía (textos explicativos, preguntas y consultas de ejemplo) que descarga competencia_01_crudo.csv, lo carga en DuckDB, construye clase_ternaria con SQL y exporta el resultado a CSV. La línea 258 conserva el comentario 'Replazar null por la lógica que genera el target' junto a la expresión que asigna la clase.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–9] Enlace a Colab y texto que plantea el objetivo del notebook: crear
#   competencia_01.csv a partir de competencia_01_crudo.csv agregando la variable clase_ternaria con las
#   categorías CONTINUA, BAJA+1 y BAJA+2.
#%% celda 1 [texto]
<a href="https://colab.research.google.com/github/tobiartinian/Econom-a-y-Finanzas/blob/main/z101_target_sql.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

#%% celda 2 [texto]
# Crear la clase  Target

Hay que crear el archivo competencia_01.csv, usando el competencia_01_crudo.csv con una variable adicional llamada clase_ternaria, que contenga las categorías **CONTINUA, BAJA+1 y BAJA+2**

Para esto primero es necesario descargar el dataset.

# [Anotación · líneas 11–13] Monta Google Drive en /content/drive.
#%% celda 3 [código]
from google.colab import drive
drive.mount('/content/drive')

# [Anotación · líneas 15–40] Define la URL del dataset crudo (storage.googleapis.com/open-
#   courses/dmeyf2026-9c6f/competencia_01_crudo.csv) y la carpeta de destino /content/drive/MyDrive/Economía y
#   finanzas. Si el archivo no existe en esa carpeta lo descarga con requests en bloques de 8192 bytes; captura
#   e imprime los errores de descarga.
#%% celda 4 [código]
import os
import requests

file_url = "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
dataset_filename = "competencia_01_crudo.csv"
dataset_path = "/content/drive/MyDrive/Economía y finanzas"

file_path = os.path.join(dataset_path, dataset_filename)

if os.path.exists(file_path):
    print(f"Ya está el dataset, continue")
else:
    print(f"Falta el dataset, a bajarlo...")
    try:
        response = requests.get(file_url, stream=True)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded '{dataset_filename}' to {dataset_path}.")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# [Anotación · líneas 42–50] Texto que presenta SQL y DuckDB, e instalación de jupysql y duckdb-engine con
#   pip.
#%% celda 5 [texto]
Luego, para generar la clase vamos a usar el lenguaje **SQL**, a través de una base de datos **OLAP** llamada **DuckDB**.

La documentación la puede encontrar [aquí](https://duckdb.org/docs/current/) Procedemos a instalar componentes adicionales para utilizar directamente el lenguaje en la notebook

#%% celda 6 [código]
%%bash
pip install jupysql
pip install duckdb-engine

# [Anotación · líneas 52–65] Importa duckdb y pandas, carga la extensión sql de Jupyter, configura que las
#   consultas devuelvan DataFrames sin mensajes adicionales ni datos de conexión, y abre una conexión DuckDB en
#   memoria (duckdb:///).
#%% celda 7 [texto]
Configuramos el entorno de ejecución. Si ya tiene todo instalado, solo necesita ejecutar esta celda para empezar a usar **duckdb**

#%% celda 8 [código]
import duckdb
import pandas as pd

#permite utilizar SQL desde una consulta
%load_ext sql
%config SqlMagic.autopandas = True # Devuleve las salidas como dataframes
%config SqlMagic.feedback = False #Desactiva mensajes adicionales que SQL Magic suele mostrar.
%config SqlMagic.displaycon = False #Evita que SQL Magic muestre información de la conexión utilizada cada vez que ejecutás una consulta.

%sql duckdb:///

# [Anotación · líneas 67–75] Textos intermedios y consulta de prueba select 'hola mundo'.
#%% celda 9 [texto]
Support for third party widgets will remain active for the duration of the session. To disable support:

#%% celda 10 [texto]
Y ya podemos usar **SQL** dentro de una notebook!

#%% celda 11 [código]
%%sql
select 'hola mundo'

# [Anotación · líneas 77–85] Crea la tabla competencia_01_crudo leyendo el CSV crudo con read_csv_auto.
#%% celda 12 [texto]
Cargamos el archivo `.csv` a una tabla pasando su ubicación

#%% celda 13 [código]
%%sql
create or replace table competencia_01_crudo as
select
    *
from read_csv_auto("{{dataset_path + '/' +  dataset_filename}}")

# [Anotación · líneas 87–106] Consultas de control: primeras 5 filas, cantidad de filas por foto_mes, copia de
#   la tabla completa a un DataFrame df y listado de sus columnas.
#%% celda 14 [texto]
Hagamos unas queries básicas para comprobar que todo esta funcionando bien.

#%% celda 15 [código]
%sql select * from competencia_01_crudo limit 5

#%% celda 16 [código]
%%sql
select
    foto_mes
    , count(*) as cantidad -- cuenta cuantos casos hay en cada foto_mes
                           -- y lo guarda en un campo llamado cantidad
from competencia_01_crudo
group by foto_mes

#%% celda 17 [código]
df = %sql SELECT * FROM competencia_01_crudo

#%% celda 18 [código]
df.columns

# [Anotación · líneas 108–141] Texto sobre la cláusula WITH y un ejemplo que calcula el promedio de
#   mrentabilidad por cliente y marca cada fila como 'mayor' o 'menor' respecto de ese promedio.
#%% celda 19 [texto]
Antes de avanzar con la construcción del **target** veamos repasemos un poco de **SQL**

## WITH

Un escenario común es necesitar realizar una consulta a no a una tabla, sino a otra consulta. Una forma tradicional de hacerlo es usando es:
* Creando una tabla temporal con esa consulta
* Usando `selects from select`.

Esta necesidad es muy común, pero como todo en la vida hay peros.
- Crear una tabla en una base de datos que va a ser usada UNA SOLA VEZ ensucia los esquemas con un montón de tablas que no son útiles y además del desorden ocupan espacio innecesario
- El `select from select`, debe ser de las cosas peor vistas por los administradores de BBDD. Tienen sus razones técnicas, en general la recomendación es no usarlo a menos que uno conozca bien como funciona la base de datos por dentro, ya que hay casos donde terminan ocasionando muchos problemas

Y que hacer? bueno hay una clausula en **SQL** llamada `WITH`, que nos permite crear esas (plural) tablas para ser usadas en la **query** principal. Ejemplo si queremos comparar el valor de una variable con su promedio a través de todos los meses.

#%% celda 20 [código]
%%sql
with promedios as (
    select
        numero_de_cliente
        , avg(mrentabilidad) as avg_mrentabilidad
    from competencia_01_crudo
    group by numero_de_cliente
) select
    cp.numero_de_cliente
    , cp.foto_mes
    , if(cp.mrentabilidad > p.avg_mrentabilidad, 'mayor', 'menor') as comparacion
from competencia_01_crudo cp
join promedios p using (numero_de_cliente)

#%% celda 21 [texto]
- Usar esa clausula tiene muchos beneficios, entre ellos sumar legibilidad de código y le permite al motor de **SQL** optimizar mejor, ya que entiende todo lo que se buscar hacer y planifica como resolverlo en el menor tiempo posible.

**NOTA**: Hay un tipo de tabla que se llaman temporales, que se borran solas una vez que uno se desconecta de la base de datos. Es una mejor alternativa frente al `CREATE`, sin embargo si la tabla que se esta creando se usa una sola vez es conveniente usar el `WITH` porque permite optimizar la ejecución. Si esa tabla va a ser usada mas de una vez dentro del proceso, las tablas temporales son la mejor opción.

# [Anotación · líneas 143–172] Texto sobre funciones analíticas y dos consultas sobre el cliente 12159854: una
#   lista mrentabilidad por foto_mes y la otra agrega los valores de 1 y 2 filas hacia adelante y hacia atrás
#   con lead y lag.
#%% celda 22 [texto]
# Funciones Analíticas

Las funciones analíticas en SQL son un conjunto de funciones que te permiten realizar cálculos avanzados sobre un conjunto de filas relacionadas dentro de una consulta conservando las filas individuales y calculando sobre ventanas de datos relacionadas.

Veamos un ejemplo para que quede más claro:

#%% celda 23 [código]
%%sql
select
    numero_de_cliente
    , foto_mes
    , mrentabilidad
from competencia_01_crudo
where numero_de_cliente = 12159854
order by foto_mes

#%% celda 24 [código]
%%sql
select
    numero_de_cliente
    , foto_mes
    , mrentabilidad
    , lead(mrentabilidad, 1) over (partition by numero_de_cliente order by foto_mes) as mrentabilidad_mas_1
    , lag(mrentabilidad, 1) over (partition by numero_de_cliente order by foto_mes) as mrentabilidad_menos_1
    , lead(mrentabilidad, 2) over (partition by numero_de_cliente order by foto_mes) as mrentabilidad_mas_2
    , lag(mrentabilidad, 2) over (partition by numero_de_cliente order by foto_mes) as mrentabilidad_menos_2
from competencia_01_crudo
where numero_de_cliente = 12159854
order by foto_mes

# [Anotación · líneas 174–231] Textos y consultas sobre el cliente 60112254: lista los meses en que aparece,
#   genera todas las combinaciones de cliente y período con un cross join y marca con mes_0 (1 o 0) si el
#   cliente tiene fila en cada período.
#%% celda 25 [texto]
* Qué paso?
* ¿Cómo esta construyendo las nuevas variables?
* ¿ Nos puede ayudar a construir targets ?

¿Dondé puedo leer un poco más de esta magia negra? https://duckdb.org/docs/sql/window_functions.html

## Los casos raros

Que pasa con el cliente **60112254** y la foto **202104**?

#%% celda 26 [código]
%%sql
select
    numero_de_cliente
    , foto_mes
from competencia_01_crudo
where numero_de_cliente = 60112254
order by foto_mes

#%% celda 27 [texto]
* ¿Cuál debería ser la clase para cada periodo?

### Una pista

Podemos generar todas las posibles combinaciones de clientes y periodos de manera muy simple

#%% celda 28 [código]
%%sql
with periodos as (
  select distinct foto_mes from competencia_01_crudo
), clientes as (
  select distinct numero_de_cliente from competencia_01_crudo
)
select numero_de_cliente, foto_mes from clientes cross join periodos
where numero_de_cliente = 60112254
order by foto_mes

#%% celda 29 [texto]
Solo nos queda saber si estuvo o no el banco el cliente en ese periodo y armar el

#%% celda 30 [código]
%%sql
with periodos as (
    select distinct foto_mes from competencia_01_crudo -- Esto también se puede hacer con secuencias
), clientes as (
    select distinct numero_de_cliente from competencia_01_crudo
), todo as (
    select numero_de_cliente, foto_mes from clientes cross join periodos
)
select
    t.numero_de_cliente
    , t.foto_mes
    , if(c.numero_de_cliente is null, 0, 1) as mes_0
from todo t
left join competencia_01_crudo c using (numero_de_cliente, foto_mes)
where t.numero_de_cliente = 60112254
order by foto_mes

# [Anotación · líneas 233–264] Crea la tabla competencia_01. Sobre el cruce de todos los clientes con todos
#   los períodos calcula mes_0 (1 si el cliente tiene fila ese mes), mes_1 y mes_2 (el valor de mes_0 uno y dos
#   períodos adelante) y asigna clase_ternaria evaluando en orden: 'CONTINUA' si mes_2 = 1; 'BAJA+2' si mes_1 =
#   1 y mes_2 = 0; 'BAJA+1' si mes_1 = 0; nulo si mes_1 o mes_2 son nulos. Conserva sólo las filas con mes_0 = 1
#   y descarta las tres columnas auxiliares.
#%% celda 31 [texto]
Antes de continuar, tomémonos un momento para reflexionar. Con todas estas piezas, ¿cómo podemos ensamblar el target?

Una vez que lo tengamos claro sobre el papel, proceda a completar el código que sigue.

#%% celda 32 [código]
%%sql
create or replace table competencia_01 as
with periodos as (
    select distinct foto_mes from competencia_01_crudo
), clientes as (
    select distinct numero_de_cliente from competencia_01_crudo
), todo as (
    select numero_de_cliente, foto_mes from clientes cross join periodos
), clase_ternaria as (
    select
        c.*
        , if(c.numero_de_cliente is null, 0, 1) as mes_0
        , lead(mes_0, 1) over (partition by t.numero_de_cliente order by foto_mes) as mes_1
        , lead(mes_0, 2) over (partition by t.numero_de_cliente order by foto_mes) as mes_2
        , case
            when mes_2 = 1 then 'CONTINUA'
            when mes_1 = 1 and mes_2 = 0 then 'BAJA+2'
            when mes_1 = 0 then 'BAJA+1'
            when mes_1 is null or mes_2 is null then null
          end as clase_ternaria-- Replazar null por la lógica que genera el target
    from todo t
    left join competencia_01_crudo c using (numero_de_cliente, foto_mes)
) select
  * EXCLUDE (mes_0, mes_1, mes_2)
from clase_ternaria
where mes_0 = 1

# [Anotación · líneas 266–283] Consultas de control: cantidad total de filas de competencia_01 y tabla pivote
#   con la cantidad de clientes por clase_ternaria y foto_mes.
#%% celda 33 [texto]
Revisamos que todo salga como esperamos

#%% celda 34 [código]
%sql select count(*) from competencia_01

#%% celda 35 [texto]
Y vemos la cardinalidad de las clases por periodo

#%% celda 36 [texto]
* ¿Cuál es la nominalidad de cada clase?

#%% celda 37 [código]
%%sql
PIVOT competencia_01
on clase_ternaria
USING count(numero_de_cliente)
GROUP BY foto_mes

# [Anotación · líneas 285–293] Exporta la tabla a CSV con encabezado mediante COPY. La ruta de salida se arma
#   con la plantilla {{dataset_path}}competencia_01.csv: el valor de dataset_path definido en la línea 21
#   (/content/drive/MyDrive/Economía y finanzas) seguido del nombre del archivo, sin barra entre ambos.
#%% celda 38 [texto]
* ¿Cuál es la proporción del target?

## Guardar tabla en .csv

Para guardar a un `.csv` simplemente debe ejecutar la siguiente sentencia

#%% celda 39 [código]
%%sql COPY competencia_01 TO '{{dataset_path}}competencia_01.csv' (FORMAT CSV, HEADER)

# [Anotación · líneas 295–311] Texto final que enumera características de la sintaxis de DuckDB: uso de alias,
#   función IF y SELECT * EXCLUDE.
#%% celda 40 [texto]

## El pato del amor

DuckDB no es una base de datos SQL estándar; su sintaxis moderna facilita significativamente la escritura de consultas. A continuación, te menciono algunas características destacadas:

+ Uso de variables: En DuckDB, no es necesario reescribir las variables; puedes utilizar tus variables una vez definidas, lo que simplifica el código.

+ Función IF: DuckDB soporta la función IF(condición, valor_si_verdadero, valor_si_falso), lo que hace que tu código sea más claro y legible en comparación con el uso de CASE WHEN.

+ Exclusión de campos: Puedes utilizar SELECT * EXCLUDE(field1, ...) para excluir campos específicos de la lista de selección, lo que ahorra tiempo y esfuerzo.

+ Alias en cláusulas: Es posible utilizar alias en las cláusulas WHERE, GROUP BY y HAVING, lo que añade flexibilidad a la escritura de consultas.

+ Uso de alias en cálculos: DuckDB permite el uso de alias dentro del cálculo de otros campos, facilitando la manipulación y transformación de datos en una consulta.

Estas son solo algunas de las capacidades que hacen de DuckDB una herramienta poderosa. Te recomiendo leer la documentación y el blog oficial para explorar más a fondo su potencial.
```

### Submission.ipynb

Notebook de una celda de instalación y una celda de código que arma la tabla con lags en DuckDB, recupera los hiperparámetros de un estudio de Optuna, entrena un LightGBM con 202103 a 202106, predice 202108 y escribe submission_final.csv. Según su salida guardada, el archivo tiene 8295 clientes.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–5] Enlace para abrir el notebook en Google Colab e instalación de optuna con %pip.
#%% celda 1 [texto]
<a href="https://colab.research.google.com/github/tobiartinian/Econom-a-y-Finanzas/blob/main/Submission.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

#%% celda 2 [código]
%pip install optuna

# [Anotación · líneas 7–15] Importa lightgbm, duckdb, optuna, pandas y os, y abre (o crea) el archivo de base
#   de datos competencia.duckdb en el directorio de trabajo.
#%% celda 3 [código]
import lightgbm as lgb
import duckdb
import optuna
import pandas as pd
import os

# 1. Conectar a DuckDB
con = duckdb.connect("competencia.duckdb")

# [Anotación · líneas 17–45] Lista las tablas de esa base. Si no existe competencia_01, lee el encabezado de
#   /content/drive/MyDrive/Economía y finanzas/competencia_01.csv, arma para cada columna salvo foto_mes,
#   numero_de_cliente y clase_ternaria una expresión LAG(col, 1) particionada por numero_de_cliente y ordenada
#   por foto_mes (sufijo _lag1), y crea la tabla con todas las columnas del CSV más esos lags. Si la tabla ya
#   existe, sólo imprime un aviso.
# 2. Verificar si la tabla competencia_01 existe, y si no, recrearla desde el CSV
tablas_existentes = [row[0] for row in con.execute("SHOW TABLES;").fetchall()]

if "competencia_01" not in tablas_existentes:
    print("⚠️ La tabla 'competencia_01' no está en esta sesión. Generándola desde el CSV...")

    file_path = "/content/drive/MyDrive/Economía y finanzas/competencia_01.csv" # Ajusta tu ruta si es necesario

    # Leer header para las variables con lag
    df_header = pd.read_csv(file_path, nrows=0)
    excluir = {'foto_mes', 'numero_de_cliente', 'clase_ternaria'}
    variables_lag_validas = [col for col in df_header.columns if col not in excluir]

    lags_sql = ",\n    ".join([
        f"LAG({col}, 1) OVER (PARTITION BY numero_de_cliente ORDER BY foto_mes) AS {col}_lag1"
        for col in variables_lag_validas
    ])

    query_create = f"""
    CREATE OR REPLACE TABLE competencia_01 AS
    SELECT
        *,
        {lags_sql}
    FROM read_csv_auto('{file_path}');
    """
    con.execute(query_create)
    print("¡Tabla creada y cargada con éxito en DuckDB!")
else:
    print("✅ La tabla 'competencia_01' ya existe en DuckDB.")

# [Anotación · líneas 47–56] Carga el estudio de Optuna exp_101_lgbm-opt desde el archivo SQLite
#   /content/drive/MyDrive/DMEyF/2026/notebooks/data/optimization_lgbm.db, toma study.best_params y los imprime.
#   El código que genera ese estudio no está en el repositorio.
# 3. Recuperar los mejores hiperparámetros de Optuna
storage_name = "sqlite:////content/drive/MyDrive/DMEyF/2026/notebooks/data/optimization_lgbm.db"
study_name = "exp_101_lgbm-opt"

study = optuna.load_study(study_name=study_name, storage=storage_name)
best_params = study.best_params

print("\n🏆 Mejores hiperparámetros recuperados de Optuna:")
for k, v in best_params.items():
    print(f"  - {k}: {v}")

# [Anotación · líneas 58–65] Agrega a esos parámetros objective=binary, metric=auc, boosting_type=gbdt,
#   random_state=772859, n_jobs=1 y verbose=-1.
best_params.update({
    "objective": "binary",
    "metric": "auc",
    "boosting_type": "gbdt",
    "random_state": 772859,
    "n_jobs": 1,
    "verbose": -1
})

# [Anotación · líneas 67–71] Obtiene los nombres de columna de la tabla con una consulta LIMIT 0 y define como
#   variables de entrada todas menos foto_mes, numero_de_cliente y clase_ternaria.
# 4. Extraer features y entrenar
df_header = con.execute("SELECT * FROM competencia_01 LIMIT 0").df()
excluir = {"foto_mes", "numero_de_cliente", "clase_ternaria"}
features = [col for col in df_header.columns if col not in excluir]
features_sql = ", ".join(features)

# [Anotación · líneas 73–84] Trae de DuckDB las filas con foto_mes entre 202103 y 202106 con esas variables y
#   una columna target que vale 1 cuando clase_ternaria es 'BAJA+2' y 0 en otro caso; separa X_train e y_train.
print("\nCargando datos de entrenamiento desde DuckDB...")
query_train = f"""
    SELECT
        {features_sql},
        CASE WHEN clase_ternaria = 'BAJA+2' THEN 1 ELSE 0 END AS target
    FROM competencia_01
    WHERE foto_mes BETWEEN 202103 AND 202106
"""
df_train = con.execute(query_train).df()

X_train = df_train.drop(columns=["target"])
y_train = df_train["target"]

# [Anotación · líneas 86–93] Construye un lgb.Dataset con todas esas filas y entrena con lgb.train durante 400
#   iteraciones (num_boost_round=400), sin conjunto de validación ni detención temprana.
print("Entrenando el modelo final de LightGBM...")
train_data = lgb.Dataset(X_train, label=y_train)

model = lgb.train(
    best_params,
    train_data,
    num_boost_round=400
)

# [Anotación · líneas 95–108] Trae todas las columnas de las filas de foto_mes = 202108, selecciona las mismas
#   variables del entrenamiento y guarda la probabilidad predicha en la columna probabilidad.
# 5. Cargar datos de test y generar submission
mes_test = 202108
print(f"Cargando datos del mes de test ({mes_test})...")

query_test = f"""
    SELECT *
    FROM competencia_01
    WHERE foto_mes = {mes_test}
"""
df_test = con.execute(query_test).df()
X_test = df_test[features]

print("Generando predicciones...")
df_test['probabilidad'] = model.predict(X_test)

# [Anotación · líneas 110–118] Conserva las filas con probabilidad mayor o igual a 0.025, se queda con la
#   columna numero_de_cliente y la escribe en submission_final.csv sin índice ni encabezado; imprime la cantidad
#   de clientes guardados y muestra los primeros 10.
umbral_optimo = 0.025
df_bajas_predichas = df_test[df_test['probabilidad'] >= umbral_optimo].copy()
df_submission = df_bajas_predichas[['numero_de_cliente']].copy()

output_filename = 'submission_final.csv'
df_submission.to_csv(output_filename, index=False, header=False)

print(f"\n✨ ¡Listo! Se filtraron y guardaron {len(df_submission)} clientes predichos como baja+2 en '{output_filename}'.")
df_submission.head(10)
```


## Explicaciones del alumno (texto original)

### README.md

> # Econom-a-y-Finanzas
> Ejercicios y proyectos de economía y finanzas

