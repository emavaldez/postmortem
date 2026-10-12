# CVFH — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: CVFH
- Repositorio: https://github.com/CVFH/DMEYF_CVFH
- Link posteado: https://github.com/CVFH/DMEYF_CVFH/tree/main/competencia_01
- Commit: 0539e935b9c0be6d484b2800bce86001e0d19cde
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/cvfh/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/cvfh.json

## Resumen

La entrega es la carpeta competencia_01: un README, un requirements.txt, un notebook de feature engineering y un script de entrenamiento. El notebook (DuckDB/SQL) lee el CSV crudo, arma clase_ternaria según la presencia del cliente en los dos meses siguientes, agrega 21 variables del mes (sumas Visa+Master, saldos, deuda, canales, cocientes, tickets, antigüedad de tarjetas y un flag), pasa ccajas_depositos a NULL en los meses en que es todo cero y calcula lag 1, lag 2, delta 1 y delta 2 de todas las columnas numéricas; exporta un Parquet. El script crea la clase binaria (BAJA+1 o BAJA+2), escala por mes las columnas cuyo nombre empieza con m, quita las de préstamos personales y separa tres subconjuntos de variables: del mes (current), lag1/delta1 (hist1) y lag2/delta2 (hist2). Entrena un LightGBM por subconjunto con hiperparámetros fijos, predice 202106 y busca en una grilla los pesos del promedio ponderado de mayor ganancia. Después reentrena los tres modelos sumando 202106, con 16 semillas, predice 202108, combina los modelos con esos pesos, promedia entre semillas los rankings percentiles y escribe los 10.500 clientes de mayor score.

**Qué entrega.** Un CSV sin encabezado ni índice con los 10.500 numero_de_cliente de 202108 de mayor score (resultados/multisemilla_ensemble_proba_10500_nsemillas_16.csv). El script escribe además la variante con ensamble de rankings (multisemilla_ensemble_rank_10500_nsemillas_16.csv); según el README, para la entrega final se retiene el ensamble de probabilidades. Los CSV no están en la carpeta posteada.

**Cómo se ejecuta.** Según el README: instalar las dependencias con python -m pip install -r requirements.txt; colocar competencia_01_crudo.csv en data/; desde competencia_01/ abrir JupyterLab y ejecutar en orden las celdas de primer_paso_FE_competencia_01.ipynb, que genera data/competencia_01_fev4.parquet; después ejecutar python modelo_final.py desde el directorio principal. El README llama modelo_final.py al script de la segunda etapa; el archivo que está en la carpeta se llama segundo_paso_entrenamiento_competencia_01.py.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria clase_binaria12: positivo = BAJA+1 o BAJA+2. La ganancia en validación se mide sólo contra BAJA+2. La clase ternaria se construye en el notebook a partir de la presencia del cliente en el mes siguiente y en el subsiguiente.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** En los modelos de validación: todas las filas cuya clase no es CONTINUA y una muestra al azar del 20% de las CONTINUA (random_state = 42), por separado en cada uno de los tres subconjuntos. Los modelos finales se entrenan con todas las filas, sin submuestreo.
- **Calidad de datos:** En el notebook, ccajas_depositos pasa a NULL en los meses en que todos sus valores son 0 o NULL. Las fechas de alta de tarjeta que no son mayores que 0 quedan en NULL al calcular la antigüedad. No se observa otro tratamiento en el código.
- **Drifting:** Cada columna numérica cuyo nombre empieza con m minúscula (incluidos sus lags y deltas) se divide, dentro de cada foto_mes, por el máximo del mes, o por el máximo valor absoluto del mes si hay valores negativos; el cero queda en cero. La columna escalada reemplaza a la original y se renombra con el sufijo _norm0.
- **Variables dentro del mes:** 21 variables calculadas en SQL sobre el mes: seis sumas Visa+Master (consumo, transacciones, saldo total, límite de compra, pago mínimo, pagado), saldo_liquido_total, deuda_prestamos_total, trx_digitales, trx_fisicas, un flag de cliente sin saldo ni consumo de tarjetas, sin descubierto preacordado y sin préstamos, cinco cocientes (utilización del límite, pagado sobre saldo, pagado sobre pago mínimo, liquidez sobre deuda, proporción de transacciones digitales), tres tickets promedio (Visa, Master, débito) y la antigüedad en meses de Visa y de Master.
- **Variables históricas:** Lag 1, lag 2, delta 1 y delta 2 de cada columna numérica de la tabla con las variables del mes (todas menos foto_mes, numero_de_cliente y clase_ternaria), tomando la fila anterior y la de dos filas atrás del mismo cliente ordenado por foto_mes; se calculan en bloques de 25 columnas. En el script, las columnas con lag1 o delta1 alimentan el modelo hist1 y las de lag2 o delta2 el modelo hist2.
- **Selección de variables:** No se observa selección por importancia en el código. Las columnas se reparten por nombre en tres subconjuntos (sin lag ni delta; lag1 y delta1; lag2 y delta2) y se quitan las que contienen prestamos_personales. Según el README se probaron versiones que excluían variables de baja relevancia; ese código no está en la carpeta posteada.
- **Optimización de hiperparámetros:** No se observa en el código: los valores están escritos en el script. Según el README provienen de experimentación previa que no forma parte de este pipeline. Lo que el script sí busca es la combinación de pesos del ensamble, en una grilla con paso 0,05, sobre 202106.
- **Hiperparámetros finales:** Los mismos para los tres modelos: objective = binary, boosting_type = gbdt, metric = auc, max_bin = 31, num_leaves = 18, learning_rate = 0.00625238, min_data_in_leaf = 1748, feature_fraction = 0.939774, bagging_fraction = 0.376689, bagging_freq = 1, boost_from_average = True, feature_pre_filter = False, 4928 iteraciones.
- **Semillas:** np.random.seed(42) seguido de np.random.choice(1000000, size=50, replace=False) genera 50 semillas; las primeras 16 se usan en el entrenamiento final. Los modelos de validación usan la primera de la lista. El submuestreo usa random_state = 42.
- **Cantidad de semillas:** 16
- **Ensamble:** Dos niveles. Por semilla: promedio ponderado de las probabilidades de los tres modelos (current, hist1, hist2) con los pesos de mayor ganancia en 202106; en paralelo, promedio ponderado de los rankings percentiles de los tres modelos con sus propios pesos. Entre semillas: el score de cada semilla se pasa a ranking percentil y se promedian las 16 con igual peso. Según el README se entrega la variante de probabilidades.
- **Corte:** Cantidad fija: los 10.500 clientes de mayor score (N_ENVIOS_FINAL = 10500). La grilla de validación recorre de 8.000 a 15.000 envíos de a 1.000, pero la cantidad que surge de ahí no se usa para el archivo final.
- **Validación:** Un mes posterior al entrenamiento: los tres modelos se entrenan con meses hasta 202105 (current 202103-202105, hist1 202104-202105, hist2 202105) y predicen 202106. Sobre 202106 se calcula la ganancia (2.200.000 × 0,5 − 27.500 por acierto y −27.500 por envío sin acierto, contra BAJA+2) para cada combinación de pesos y cada cantidad de envíos. Se usa una sola semilla.
- **Salidas:** En resultados/: por cada semilla, cinco Parquet (ranking de current, de hist1, de hist2, del ensamble de probabilidades y del ensamble de rankings); el archivo modelo_final_semillas_completadas.txt con las semillas terminadas; y dos CSV sin encabezado con 10.500 numero_de_cliente: multisemilla_ensemble_proba_10500_nsemillas_16.csv y multisemilla_ensemble_rank_10500_nsemillas_16.csv. El notebook escribe data/competencia_01_fev4.parquet.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Estandarización o normalización por mes (`drifting.estandarizacion_por_mes`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: Según el README: desarrollado en Windows 11 con Python 3.13.12, DuckDB 1.5.5, pandas 3.0.3, NumPy 2.4.4, LightGBM 4.7.0, PyArrow 25.0.0, JupyterLab 4.5.6, JupySQL 0.11.1 y duckdb-engine 0.17.0, además de Matplotlib 3.10.8, Plotly 7.0.0, SciPy 1.17.1, Scikit-learn 1.8.0 y Optuna 4.9.0. requirements.txt fija las mismas versiones. No se declara el hardware.

## Pasos del camino de la entrega

1. **Lectura del CSV crudo.** El notebook abre una conexión DuckDB en memoria, define la carpeta data/ dentro del directorio de trabajo y carga competencia_01_crudo.csv en la tabla competencia_01. (`competencia_01/primer_paso_FE_competencia_01.ipynb` líneas 4–31)
2. **Construcción de clase_ternaria.** Para cada fila busca al mismo cliente en el mes siguiente y en el subsiguiente de la lista de meses del dataset. Asigna BAJA+1 si no está en el siguiente, BAJA+2 si está en el siguiente y no en el subsiguiente, y CONTINUA si está en los dos. El último mes queda sin clase y el anteúltimo sólo puede tomar BAJA+1. (`competencia_01/primer_paso_FE_competencia_01.ipynb` líneas 36–132)
3. **Variables del mes.** Agrega 21 variables calculadas con datos del mismo mes: sumas Visa+Master, saldo líquido, deuda por préstamos, transacciones digitales y físicas, un flag, cinco cocientes, tres tickets promedio y la antigüedad en meses de cada tarjeta. (`competencia_01/primer_paso_FE_competencia_01.ipynb` líneas 137–266; `competencia_01/primer_paso_FE_competencia_01.ipynb` líneas 308–394)
4. **ccajas_depositos a NULL en los meses en cero.** Detecta los foto_mes en que ccajas_depositos es 0 o NULL en todas las filas y en esos meses reemplaza la columna por NULL. (`competencia_01/primer_paso_FE_competencia_01.ipynb` líneas 268–306)
5. **Lags y deltas por bloques.** Lista las columnas numéricas de la tabla y, en bloques de 25, calcula para cada una el lag 1 y el lag 2 por cliente ordenado por foto_mes; en un segundo recorrido calcula delta 1 y delta 2 como el valor actual menos cada lag. Cada bloque se calcula en una tabla temporal que se une a la tabla competencia_01_hist. (`competencia_01/primer_paso_FE_competencia_01.ipynb` líneas 399–606)
6. **Exportación a Parquet.** Escribe la tabla competencia_01_hist en data/competencia_01_fev4.parquet con compresión ZSTD. Ese archivo es la entrada del script de entrenamiento. (`competencia_01/primer_paso_FE_competencia_01.ipynb` líneas 611–619)
7. **Configuración y semillas.** El script fija la semilla 42, genera 50 semillas y toma las primeras 16 para el entrenamiento final; fija 10.500 envíos y las carpetas data/ y resultados/. (`competencia_01/segundo_paso_entrenamiento_competencia_01.py` líneas 15–37)
8. **Carga y clases binarias.** Lee el Parquet y crea clase_binaria12 (BAJA+1 o BAJA+2 contra el resto) y clase_binaria2 (BAJA+2 contra el resto). (`competencia_01/segundo_paso_entrenamiento_competencia_01.py` líneas 39–50)
9. **Escalado por mes de las columnas que empiezan con m.** Divide cada columna numérica cuyo nombre empieza con m por el máximo de su foto_mes (o por el máximo valor absoluto si en ese mes hay negativos), reemplaza la original y le agrega el sufijo _norm0. (`competencia_01/segundo_paso_entrenamiento_competencia_01.py` líneas 52–74)
10. **Tres subconjuntos de variables.** Separa las columnas por nombre en tres tablas: current (sin lag ni delta), hist1 (lag1 y delta1) e hist2 (lag2 y delta2). De las tres quita las columnas cuyo nombre contiene prestamos_personales. (`competencia_01/segundo_paso_entrenamiento_competencia_01.py` líneas 76–132)
11. **Meses de validación y submuestreo.** Para validar, current entrena con 202103-202105, hist1 con 202104-202105 e hist2 con 202105; los tres se prueban en 202106. En cada conjunto de entrenamiento se conservan todas las filas que no son CONTINUA y el 20% de las CONTINUA. (`competencia_01/segundo_paso_entrenamiento_competencia_01.py` líneas 134–197)
12. **Función de ganancia e hiperparámetros.** Define la ganancia por cantidad de envíos (acierto: 2.200.000 × 0,5 − 27.500; envío sin acierto: −27.500) y el diccionario de parámetros de LightGBM con 4928 iteraciones. (`competencia_01/segundo_paso_entrenamiento_competencia_01.py` líneas 199–243)
13. **Modelos de validación y búsqueda de pesos.** Entrena los tres modelos, predice 202106 y recorre una grilla de pesos (paso 0,05, suma 1) y de cantidades de envío (8.000 a 15.000 de a 1.000) para dos formas de combinar: promedio ponderado de probabilidades y de rankings percentiles. Se queda con los pesos de la fila de mayor ganancia de cada forma. (`competencia_01/segundo_paso_entrenamiento_competencia_01.py` líneas 245–366)
14. **Reentrenamiento con 202106 y 16 semillas.** Arma los conjuntos finales sumando 202106 y sin submuestreo (current 202103-202106, hist1 202104-202106, hist2 202105-202106). Para cada una de las 16 semillas entrena los tres modelos y predice 202108; un archivo de control permite saltear las semillas ya terminadas. (`competencia_01/segundo_paso_entrenamiento_competencia_01.py` líneas 369–493)
15. **Ensamble por semilla y guardado.** Con los pesos de la validación combina las tres predicciones de cada semilla (por probabilidades y por rankings) y guarda en resultados/ cinco Parquet por semilla. (`competencia_01/segundo_paso_entrenamiento_competencia_01.py` líneas 495–616)
16. **Ensamble multisemilla y archivo final.** Para cada forma de ensamble lee los 16 Parquet, pasa cada score a ranking percentil, promedia las 16 semillas, ordena de mayor a menor y escribe los primeros 10.500 numero_de_cliente en un CSV sin encabezado. (`competencia_01/segundo_paso_entrenamiento_competencia_01.py` líneas 619–682)

## Archivos

- `competencia_01/requirements.txt` · configuracion · Texto · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/cvfh/competencia_01/requirements.txt.txt) — Lista 13 paquetes de Python con versión exacta: duckdb 1.5.5, duckdb-engine 0.17.0, jupysql 0.11.1, jupyterlab 4.5.6, pandas 3.0.3, numpy 2.4.4, pyarrow 25.0.0, lightgbm 4.7.0, matplotlib 3.10.8, plotly 7.0.0, scipy 1.17.1, scikit-learn 1.8.0 y optuna 4.9.0. El notebook y el script importan duckdb, pandas, numpy y lightgbm; matplotlib, plotly, scipy, scikit-learn y optuna no aparecen importados en ellos.
- `competencia_01/README.md` · explicacion · Markdown · 304 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/cvfh/competencia_01/README.md.txt) — Texto de presentación de la entrega en ocho secciones: descripción, estructura de carpetas, requisitos con versiones, preparación del entorno, feature engineering, entrenamiento y predicción, reproducibilidad, y aprendizajes y próximos pasos. Describe los tres modelos con sus meses, los hiperparámetros, la validación en junio de 2021, el ensamble de 16 semillas y el corte en 10.500 clientes. Según el README, en 202106 el ensamble de probabilidades da 430.100.000 con pesos 0,35 / 0,30 / 0,35 y 13.000 envíos, y el de rankings 429.000.000 con pesos 0,15 / 0,20 / 0,65 y 12.000 envíos; indica que para la entrega final se retiene el ensamble de probabilidades. Nombra el script de la segunda etapa como modelo_final.py; el archivo de la carpeta se llama segundo_paso_entrenamiento_competencia_01.py.
- `competencia_01/primer_paso_FE_competencia_01.ipynb` · principal · Jupyter (python) · 619 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/cvfh/competencia_01/primer_paso_FE_competencia_01.ipynb.txt) — Primera etapa. Con DuckDB y SQL lee el CSV crudo, construye clase_ternaria, agrega variables del mes, pasa ccajas_depositos a NULL en los meses en que es todo cero, calcula lags y deltas de orden 1 y 2 para todas las columnas numéricas y exporta el resultado a data/competencia_01_fev4.parquet.
- `competencia_01/segundo_paso_entrenamiento_competencia_01.py` · principal · Python · 682 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/cvfh/competencia_01/segundo_paso_entrenamiento_competencia_01.py.txt) — Segunda etapa. Lee el Parquet del notebook, crea las clases binarias, escala por mes las columnas que empiezan con m, arma tres subconjuntos de variables, entrena tres LightGBM para validar en 202106 y elegir los pesos del ensamble, reentrena con 202106 y 16 semillas, predice 202108 y escribe los CSV con 10.500 clientes.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### competencia_01/primer_paso_FE_competencia_01.ipynb

Primera etapa. Con DuckDB y SQL lee el CSV crudo, construye clase_ternaria, agrega variables del mes, pasa ccajas_depositos a NULL en los meses en que es todo cero, calcula lags y deltas de orden 1 y 2 para todas las columnas numéricas y exporta el resultado a data/competencia_01_fev4.parquet.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–21] Importa duckdb, pandas y Path, abre una conexión DuckDB en memoria y carga la
#   extensión sql de JupySQL con salida a pandas y sin mensajes de feedback ni de conexión. Define la carpeta de
#   datos como data/ dentro del directorio de trabajo y el archivo de entrada competencia_01_crudo.csv.
#%% celda 1 [texto]
### Setup

#%% celda 2 [código]
import duckdb
import pandas as pd
from pathlib import Path

con = duckdb.connect()

%load_ext sql
%config SqlMagic.autopandas = True
%config SqlMagic.feedback = False
%config SqlMagic.displaycon = False

%sql con

#%% celda 3 [código]
base_path = Path.cwd()
dataset_path = str(base_path / "data") + "/"
dataset_file = "competencia_01_crudo.csv"

# [Anotación · líneas 23–31] Lee el CSV con read_csv_auto y lo guarda completo en la tabla competencia_01.
#%% celda 4 [texto]
### Cargo base cruda

#%% celda 5 [código]
%%sql

CREATE OR REPLACE TABLE competencia_01 AS
SELECT *
FROM read_csv_auto("{{dataset_path + dataset_file}}");

# [Anotación · líneas 33–60] Empieza la tabla competencia_01_clase con tres subconsultas: meses (primer y
#   último foto_mes), meses_distintos (la lista de meses presentes) y meses_siguientes, que con LEAD asigna a
#   cada mes el siguiente (mes_1) y el subsiguiente (mes_2) de esa lista.
#%% celda 6 [texto]
### Creo target ternario

#%% celda 7 [código]
%%sql

CREATE OR REPLACE TABLE competencia_01_clase AS

WITH meses AS (
    SELECT
        MIN(foto_mes) AS primer_mes,
        MAX(foto_mes) AS ultimo_mes
    FROM competencia_01
),

meses_distintos AS (
    SELECT DISTINCT
        foto_mes
    FROM competencia_01
),

meses_siguientes AS (
    SELECT
        foto_mes,
        LEAD(foto_mes, 1) OVER (ORDER BY foto_mes) AS mes_1,
        LEAD(foto_mes, 2) OVER (ORDER BY foto_mes) AS mes_2
    FROM meses_distintos
),

# [Anotación · líneas 62–92] Subconsulta base: une cada fila con la fila del mismo cliente en mes_1 y en mes_2
#   (dos LEFT JOIN de la tabla consigo misma) y guarda en esta_mes_1 y esta_mes_2 un 1 si el cliente aparece en
#   ese mes y un 0 si no.
base AS (
    SELECT
        c.*,
        ms.mes_1,
        ms.mes_2,

        -- ¿Existe el cliente en t+1?
        CASE
            WHEN c1.numero_de_cliente IS NOT NULL THEN 1
            ELSE 0
        END AS esta_mes_1,

        -- ¿Existe el cliente en t+2?
        CASE
            WHEN c2.numero_de_cliente IS NOT NULL THEN 1
            ELSE 0
        END AS esta_mes_2

    FROM competencia_01 c

    LEFT JOIN meses_siguientes ms
        ON c.foto_mes = ms.foto_mes

    LEFT JOIN competencia_01 c1
        ON c.numero_de_cliente = c1.numero_de_cliente
       AND c1.foto_mes = ms.mes_1

    LEFT JOIN competencia_01 c2
        ON c.numero_de_cliente = c2.numero_de_cliente
       AND c2.foto_mes = ms.mes_2
)

# [Anotación · líneas 94–132] Arma clase_ternaria y descarta las columnas auxiliares. En el último mes queda
#   NULL. En el anteúltimo, BAJA+1 si el cliente no está en el mes siguiente y NULL en caso contrario. En el
#   resto de los meses: BAJA+1 si no está en el siguiente, BAJA+2 si está en el siguiente pero no en el
#   subsiguiente, y CONTINUA si está en los dos.
SELECT
    * EXCLUDE (
        mes_1,
        mes_2,
        esta_mes_1,
        esta_mes_2
    ),

    CASE

        -- Último mes: no sabemos nada
        WHEN foto_mes = (SELECT ultimo_mes FROM meses)
            THEN NULL

        -- Anteúltimo mes:
        -- solamente podemos identificar BAJA+1
        WHEN foto_mes = (
            SELECT MAX(foto_mes)
            FROM meses_distintos
            WHERE foto_mes < (SELECT ultimo_mes FROM meses)
        )
        THEN
            CASE
                WHEN esta_mes_1 = 0 THEN 'BAJA+1'
                ELSE NULL
            END

        -- Resto de los meses
        WHEN esta_mes_1 = 0
            THEN 'BAJA+1'

        WHEN esta_mes_2 = 0
            THEN 'BAJA+2'

        ELSE 'CONTINUA'

    END AS clase_ternaria

FROM base;

# [Anotación · líneas 134–179] Empieza la tabla competencia_01_fe con la subconsulta base_agregaciones. Suma
#   Visa y Master, tomando los NULL como 0, para seis conceptos: consumo (mconsumototal_tc), cantidad de
#   transacciones (cconsumos_total_tc), saldo total (msaldototal_tc), límite de compra (mlimitecompra_total),
#   pago mínimo (mpagominimo_total) y monto pagado (mpagado_total).
#%% celda 8 [texto]
### FE current

#%% celda 9 [código]
%%sql

CREATE OR REPLACE TABLE competencia_01_fe AS

WITH base_agregaciones AS (

    SELECT
        *,

        -- ============================================================
        -- 1. Agregaciones totales de Tarjetas de Crédito
        -- ============================================================

        (
            COALESCE(mtarjeta_visa_consumo, 0)
            + COALESCE(mtarjeta_master_consumo, 0)
        ) AS mconsumototal_tc,

        (
            COALESCE(ctarjeta_visa_transacciones, 0)
            + COALESCE(ctarjeta_master_transacciones, 0)
        ) AS cconsumos_total_tc,

        (
            COALESCE(Visa_msaldototal, 0)
            + COALESCE(Master_msaldototal, 0)
        ) AS msaldototal_tc,

        (
            COALESCE(Visa_mlimitecompra, 0)
            + COALESCE(Master_mlimitecompra, 0)
        ) AS mlimitecompra_total,

        (
            COALESCE(Visa_mpagominimo, 0)
            + COALESCE(Master_mpagominimo, 0)
        ) AS mpagominimo_total,

        (
            COALESCE(Visa_mpagado, 0)
            + COALESCE(Master_mpagado, 0)
        ) AS mpagado_total,

# [Anotación · líneas 181–211] Cuatro sumas más, también con NULL como 0: saldo_liquido_total (saldo de
#   cuentas, plazo fijo en pesos, inversión 1 en pesos e inversión 2), deuda_prestamos_total (préstamos
#   personales, prendarios e hipotecarios), trx_digitales (homebanking y app móvil) y trx_fisicas (cajas,
#   cajeros automáticos y call center).
        -- ============================================================
        -- 2. Patrimonio líquido y deuda
        -- ============================================================

        (
            COALESCE(mcuentas_saldo, 0)
            + COALESCE(mplazo_fijo_pesos, 0)
            + COALESCE(minversion1_pesos, 0)
            + COALESCE(minversion2, 0)
        ) AS saldo_liquido_total,

        (
            COALESCE(mprestamos_personales, 0)
            + COALESCE(mprestamos_prendarios, 0)
            + COALESCE(mprestamos_hipotecarios, 0)
        ) AS deuda_prestamos_total,

        -- ============================================================
        -- 3. Canales
        -- ============================================================

        (
            COALESCE(chomebanking_transacciones, 0)
            + COALESCE(cmobile_app_trx, 0)
        ) AS trx_digitales,

        (
            COALESCE(ccajas_transacciones, 0)
            + COALESCE(catm_trx, 0)
            + COALESCE(ccallcenter_transacciones, 0)
        ) AS trx_fisicas,

# [Anotación · líneas 213–240] Convierte foto_mes en la fecha del día 1 de ese mes (fecha_foto) y las fechas
#   de alta de Visa y de Master en tipo fecha, con try_strptime y formato AAAAMMDD, cuando el valor es mayor que
#   0; en otro caso quedan NULL. Son columnas auxiliares para calcular la antigüedad.
        -- ============================================================
        -- 4. Fechas
        -- ============================================================

        strptime(
            CAST(foto_mes AS VARCHAR) || '01',
            '%Y%m%d'
        )::DATE AS fecha_foto,

        CASE
            WHEN Visa_fechaalta IS NOT NULL
                 AND Visa_fechaalta > 0
            THEN try_strptime(
                CAST(Visa_fechaalta AS VARCHAR),
                '%Y%m%d'
            )::DATE
            ELSE NULL
        END AS visa_fechaalta_date,

        CASE
            WHEN Master_fechaalta IS NOT NULL
                 AND Master_fechaalta > 0
            THEN try_strptime(
                CAST(Master_fechaalta AS VARCHAR),
                '%Y%m%d'
            )::DATE
            ELSE NULL
        END AS master_fechaalta_date,

# [Anotación · líneas 242–266] Crea flag_sin_tc_sin_acuerdos_sin_prestamos: vale 1 cuando son 0 o NULL a la
#   vez el saldo total y el consumo de Visa y de Master, cdescubierto_preacordado y los montos de préstamos
#   personales, prendarios e hipotecarios; vale 0 en otro caso. La subconsulta lee de competencia_01_clase.
        -- ============================================================
        -- 5. Flag:
        --    sin tarjeta + sin acuerdos descubiertos + sin préstamos
        -- ============================================================

        CASE
            WHEN
                COALESCE(Visa_msaldototal, 0) = 0
                AND COALESCE(Master_msaldototal, 0) = 0

                AND COALESCE(mtarjeta_visa_consumo, 0) = 0
                AND COALESCE(mtarjeta_master_consumo, 0) = 0

                AND COALESCE(cdescubierto_preacordado, 0) = 0

                AND COALESCE(mprestamos_personales, 0) = 0
                AND COALESCE(mprestamos_prendarios, 0) = 0
                AND COALESCE(mprestamos_hipotecarios, 0) = 0

            THEN 1
            ELSE 0
        END AS flag_sin_tc_sin_acuerdos_sin_prestamos

    FROM competencia_01_clase
),

# [Anotación · líneas 268–306] meses_ccajas marca, para cada foto_mes, si ccajas_depositos es 0 o NULL en
#   todas las filas del mes. base_corregida reemplaza ccajas_depositos por NULL en los meses marcados y la deja
#   igual en los demás.
-- ================================================================
-- 6. Detectar meses donde ccajas_depositos es todo 0 / NA
-- ================================================================

meses_ccajas AS (

    SELECT
        foto_mes,

        BOOL_AND(
            ccajas_depositos IS NULL
            OR ccajas_depositos = 0
        ) AS ccajas_todo_cero

    FROM base_agregaciones
    GROUP BY foto_mes
),

-- ================================================================
-- 7. Corregir ccajas_depositos
-- ================================================================

base_corregida AS (

    SELECT
        b.* EXCLUDE (ccajas_depositos),

        CASE
            WHEN mc.ccajas_todo_cero
                 AND COALESCE(b.ccajas_depositos, 0) = 0
            THEN NULL
            ELSE b.ccajas_depositos
        END AS ccajas_depositos

    FROM base_agregaciones b

    LEFT JOIN meses_ccajas mc
        ON b.foto_mes = mc.foto_mes
)

# [Anotación · líneas 308–354] Selección final: quita las tres fechas auxiliares y agrega cinco cocientes
#   redondeados a 4 decimales, con NULLIF para que un denominador 0 dé NULL: saldo de tarjetas sobre límite de
#   compra (ratio_utilizacion_limite), pagado sobre saldo (ratio_pago_vs_saldo), pagado sobre pago mínimo
#   (ratio_pago_minimo), saldo líquido sobre deuda por préstamos (ratio_liquidez_vs_deuda) y transacciones
#   digitales sobre el total de digitales y físicas (ratio_canal_digital).
-- ================================================================
-- 8. Features finales
-- ================================================================

SELECT
    * EXCLUDE (
        fecha_foto,
        visa_fechaalta_date,
        master_fechaalta_date
    ),

    -- ================================================================
    -- Ratios de Tarjetas
    -- ================================================================

    ROUND(
        msaldototal_tc / NULLIF(mlimitecompra_total, 0),
        4
    ) AS ratio_utilizacion_limite,

    ROUND(
        mpagado_total / NULLIF(msaldototal_tc, 0),
        4
    ) AS ratio_pago_vs_saldo,

    ROUND(
        mpagado_total / NULLIF(mpagominimo_total, 0),
        4
    ) AS ratio_pago_minimo,

    -- ================================================================
    -- Solvencia
    -- ================================================================

    ROUND(
        saldo_liquido_total / NULLIF(deuda_prestamos_total, 0),
        4
    ) AS ratio_liquidez_vs_deuda,

    -- ================================================================
    -- Intensidad digital
    -- ================================================================

    ROUND(
        trx_digitales / NULLIF(trx_digitales + trx_fisicas, 0),
        4
    ) AS ratio_canal_digital,

# [Anotación · líneas 356–394] Agrega tres tickets promedio redondeados a 2 decimales (consumo sobre cantidad
#   de transacciones para Visa y para Master; mautoservicio sobre transacciones con tarjeta de débito) y la
#   antigüedad en meses de cada tarjeta, como diferencia entre su fecha de alta y fecha_foto. Lee de
#   base_corregida.
    -- ================================================================
    -- Tickets
    -- ================================================================

    ROUND(
        mtarjeta_visa_consumo
        / NULLIF(ctarjeta_visa_transacciones, 0),
        2
    ) AS ticket_promedio_visa,

    ROUND(
        mtarjeta_master_consumo
        / NULLIF(ctarjeta_master_transacciones, 0),
        2
    ) AS ticket_promedio_master,

    ROUND(
        mautoservicio
        / NULLIF(ctarjeta_debito_transacciones, 0),
        2
    ) AS ticket_promedio_debito,

    -- ================================================================
    -- Antigüedad
    -- ================================================================

    DATE_DIFF(
        'month',
        visa_fechaalta_date,
        fecha_foto
    ) AS antiguedad_meses_visa,

    DATE_DIFF(
        'month',
        master_fechaalta_date,
        fecha_foto
    ) AS antiguedad_meses_master

FROM base_corregida;

# [Anotación · líneas 396–435] Consulta en information_schema las columnas de competencia_01_fe con su tipo y
#   arma lag_cols con las de tipo entero, decimal o de punto flotante, sin foto_mes, numero_de_cliente ni
#   clase_ternaria. Imprime cuántas son.
#%% celda 10 [texto]
### Historico

#%% celda 11 [código]
# ============================================================
# HISTÓRICO: LAGS + DELTAS
# Procesamiento por bloques para evitar OutOfMemory
# ============================================================

# ------------------------------------------------------------
# 1. Obtener columnas numéricas
# ------------------------------------------------------------

cols = con.sql("""
    SELECT
        column_name,
        data_type
    FROM information_schema.columns
    WHERE table_name = 'competencia_01_fe'
    ORDER BY ordinal_position
""").fetchall()

excluir = {
    "foto_mes",
    "numero_de_cliente",
    "clase_ternaria"
}

lag_cols = [
    column_name
    for column_name, data_type in cols
    if column_name not in excluir
    and (
        "INT" in data_type.upper()
        or "DECIMAL" in data_type.upper()
        or data_type.upper() in {"FLOAT", "DOUBLE", "REAL"}
    )
]

print(f"Variables numéricas: {len(lag_cols)}")


# [Anotación · líneas 438–446] Crea la tabla competencia_01_hist como copia de competencia_01_fe; sobre ella
#   se van agregando las columnas históricas.
# ------------------------------------------------------------
# 2. Crear tabla histórica base
# ------------------------------------------------------------

con.sql("""
    CREATE OR REPLACE TABLE competencia_01_hist AS
    SELECT *
    FROM competencia_01_fe
""")


# [Anotación · líneas 449–481] Fija el tamaño de bloque en 25 columnas. Para cada bloque arma el texto SQL de
#   dos expresiones por columna: LAG de 1 fila y LAG de 2 filas dentro de cada numero_de_cliente ordenado por
#   foto_mes, con los sufijos _lag1 y _lag2.
# ------------------------------------------------------------
# 3. Crear LAGS en bloques
# ------------------------------------------------------------

BLOQUE = 25

for inicio in range(0, len(lag_cols), BLOQUE):

    bloque = lag_cols[inicio:inicio + BLOQUE]

    lag_parts = []

    for col in bloque:

        lag_parts.append(
            f'''
            LAG("{col}", 1) OVER (
                PARTITION BY numero_de_cliente
                ORDER BY foto_mes
            ) AS "{col}_lag1"
            '''
        )

        lag_parts.append(
            f'''
            LAG("{col}", 2) OVER (
                PARTITION BY numero_de_cliente
                ORDER BY foto_mes
            ) AS "{col}_lag2"
            '''
        )

    lag_sql = ",\n".join(lag_parts)

# [Anotación · líneas 483–527] Guarda en la variable query un texto con ALTER TABLE que no se pasa a con.sql.
#   Calcula los lags del bloque en una tabla temporal (hist_lag_ más el índice de inicio del bloque) a partir de
#   competencia_01_fe, recrea competencia_01_hist sumándole esas columnas con un LEFT JOIN por numero_de_cliente
#   y foto_mes, borra la temporal e imprime el avance.
    query = f"""
        ALTER TABLE competencia_01_hist
        ADD COLUMN dummy_temp INTEGER
    """

    # DuckDB no permite agregar múltiples columnas calculadas
    # con ALTER TABLE de esta forma, por lo que usamos una tabla
    # temporal para cada bloque.

    temp_table = f"hist_lag_{inicio}"

    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE {temp_table} AS

        SELECT
            numero_de_cliente,
            foto_mes,
            {lag_sql}

        FROM competencia_01_fe
    """)

    # Agregar las columnas calculadas mediante JOIN
    con.sql(f"""
        CREATE OR REPLACE TABLE competencia_01_hist AS

        SELECT
            h.*,
            l.* EXCLUDE (
                numero_de_cliente,
                foto_mes
            )

        FROM competencia_01_hist h

        LEFT JOIN {temp_table} l
            USING (numero_de_cliente, foto_mes)
    """)

    con.sql(f"DROP TABLE {temp_table}")

    print(
        f"Lags procesados: "
        f"{min(inicio + BLOQUE, len(lag_cols))}/{len(lag_cols)}"
    )


# [Anotación · líneas 530–592] Segundo recorrido en bloques de 25: para cada columna calcula el valor actual
#   menos su lag 1 (sufijo _delta1) y menos su lag 2 (sufijo _delta2) sobre competencia_01_hist, en una tabla
#   temporal que se une del mismo modo y después se borra. Imprime el avance.
# ------------------------------------------------------------
# 4. Crear DELTAS en bloques
# ------------------------------------------------------------

for inicio in range(0, len(lag_cols), BLOQUE):

    bloque = lag_cols[inicio:inicio + BLOQUE]

    delta_parts = []

    for col in bloque:

        delta_parts.append(
            f'''
            "{col}" - "{col}_lag1"
            AS "{col}_delta1"
            '''
        )

        delta_parts.append(
            f'''
            "{col}" - "{col}_lag2"
            AS "{col}_delta2"
            '''
        )

    delta_sql = ",\n".join(delta_parts)

    temp_table = f"hist_delta_{inicio}"

    con.sql(f"""
        CREATE OR REPLACE TEMP TABLE {temp_table} AS

        SELECT
            numero_de_cliente,
            foto_mes,
            {delta_sql}

        FROM competencia_01_hist
    """)

    con.sql(f"""
        CREATE OR REPLACE TABLE competencia_01_hist AS

        SELECT
            h.*,
            d.* EXCLUDE (
                numero_de_cliente,
                foto_mes
            )

        FROM competencia_01_hist h

        LEFT JOIN {temp_table} d
            USING (numero_de_cliente, foto_mes)
    """)

    con.sql(f"DROP TABLE {temp_table}")

    print(
        f"Deltas procesados: "
        f"{min(inicio + BLOQUE, len(lag_cols))}/{len(lag_cols)}"
    )


# [Anotación · líneas 595–606] Imprime un resumen: cantidad de variables numéricas, de lags y de deltas (el
#   doble cada una) y de columnas nuevas (el cuádruple).
# ------------------------------------------------------------
# 5. Resultado
# ------------------------------------------------------------

print()
print("============================================")
print("competencia_01_hist creada correctamente")
print("============================================")
print(f"Variables numéricas : {len(lag_cols)}")
print(f"Lags                : {len(lag_cols) * 2}")
print(f"Deltas              : {len(lag_cols) * 2}")
print(f"Nuevas columnas     : {len(lag_cols) * 4}")

# [Anotación · líneas 608–619] Define la salida data/competencia_01_fev4.parquet y exporta competencia_01_hist
#   con COPY en formato Parquet y compresión ZSTD.
#%% celda 12 [texto]
### Guardo

#%% celda 13 [código]
output_path = f"{dataset_path}competencia_01_fev4.parquet"

#%% celda 14 [código]
%%sql

COPY competencia_01_hist
TO '{{output_path}}'
(FORMAT PARQUET, COMPRESSION ZSTD);
```

### competencia_01/segundo_paso_entrenamiento_competencia_01.py

Segunda etapa. Lee el Parquet del notebook, crea las clases binarias, escala por mes las columnas que empiezan con m, arma tres subconjuntos de variables, entrena tres LightGBM para validar en 202106 y elegir los pesos del ensamble, reentrena con 202106 y 16 semillas, predice 202108 y escribe los CSV con 10.500 clientes.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Importa pandas, numpy, Path, lightgbm, os y re.
# ENTRENAMIENTO Y PREDICCIONES FINALES 
#  
# ============================================================
# LIBRERÍAS
# ============================================================

import pandas as pd
import numpy as np
from pathlib import Path
import lightgbm as lgb

import os
import re

# [Anotación · líneas 15–37] Fija la semilla 42 en numpy y sortea 50 enteros distintos entre 0 y 999.999 como
#   lista de semillas. Define 16 semillas para el entrenamiento final (las primeras 16 de la lista) y 10.500
#   clientes a enviar, y verifica que la cantidad de semillas esté entre 1 y 50. Define el identificador de
#   corrida modelo_final y las carpetas data/ y resultados/ dentro del directorio de trabajo; crea resultados/
#   si no existe.
# ============================================================
# CONFIGURACIÓN
# ============================================================

# DEFINICIONES
semilla = 42
np.random.seed(semilla)
semillas = np.random.choice(1000000, size=50, replace=False).tolist()

# PENDIENTE: confirmar ambos valores antes de la entrega.
# Actualmente se utilizan las primeras 16 semillas generadas con np.random.seed(42).
N_SEMILLAS_FINAL = 16 # TO DO: confirmar si quedan 16 o se completan las 20
N_ENVIOS_FINAL = 10500  # TODO: confirmar el número definitivo de clientes
if not isinstance(N_SEMILLAS_FINAL, int) or not 1 <= N_SEMILLAS_FINAL <= len(semillas):
    raise ValueError(f"N_SEMILLAS_FINAL debe estar entre 1 y {len(semillas)}")
semillas_envio = semillas[:N_SEMILLAS_FINAL]

# Parámetros de guardado/carga
RUN_ID = "modelo_final"
base_path = Path.cwd()
dataset_path = str(base_path / "data") + "/"
resultados_path = str(base_path / "resultados") + "/"
os.makedirs(resultados_path, exist_ok=True)

# [Anotación · líneas 39–50] Lee data/competencia_01_fev4.parquet y crea dos columnas binarias:
#   clase_binaria12 (1 si clase_ternaria es BAJA+1 o BAJA+2) y clase_binaria2 (1 sólo si es BAJA+2).
# ============================================================
# CARGA Y PROCESAMIENTO DE DATA
# ============================================================

# CARGA DATA
dataset_file = 'competencia_01_fev4.parquet'  
data = pd.read_parquet(dataset_path + dataset_file)

# PROCESAMIENTO DE DATA
# Creo target binario
data['clase_binaria12'] = np.where(data['clase_ternaria'].isin(['BAJA+1', 'BAJA+2']), 1, 0)  # continua vs resto
data['clase_binaria2'] = np.where(data['clase_ternaria'].isin(['BAJA+2']), 1, 0)  # baja+2 vs resto

# [Anotación · líneas 52–74] Toma las columnas numéricas cuyo nombre empieza con m minúscula (los nombres que
#   empiezan con Master_ o Visa_ no cumplen esa condición). Para cada una, dentro de cada foto_mes, calcula un
#   divisor: el máximo del mes, o el máximo valor absoluto del mes si hay algún valor negativo; divide la
#   columna por ese divisor y deja el valor original si el divisor es 0 o no existe. Con modo = sustituir, la
#   columna escalada (float32) reemplaza a la original y se renombra con el sufijo _norm0. Imprime cuántas
#   columnas procesa y el total de columnas.
# Rankings con cero fijo y normalización
modo = "sustituir"  # "sustituir" o "anadir"
m_cols = [c for c in data.columns if c.startswith("m")
          and pd.api.types.is_numeric_dtype(data[c])]
 
for col in m_cols:
    valores = data[col]
    max_abs_mes = valores.abs().groupby(data["foto_mes"]).transform("max")
    min_mes = valores.groupby(data["foto_mes"]).transform("min")
    max_mes = valores.groupby(data["foto_mes"]).transform("max")
    divisor = max_abs_mes.where(min_mes < 0, max_mes)
    divisor = divisor.replace(0, np.nan)
    escalada = valores.div(divisor).where(divisor.notna(), valores)
    nombre = f"{col}_norm0"
    if modo == "sustituir":
        data[col] = escalada.astype("float32")
    else:
        data[nombre] = escalada.astype("float32")
if modo == "sustituir":
    data.rename(columns={c: f"{c}_norm0" for c in m_cols}, inplace=True)

print(f"Variables originales procesadas: {len(m_cols)}")
print(f"Modo: {modo} | Columnas finales: {data.shape[1]}")

# [Anotación · líneas 76–118] Define las cinco columnas fijas (cliente, mes y las tres clases) y arma tres
#   tablas. Marca como históricas las columnas cuyo nombre contiene lag o delta, sin distinguir mayúsculas; el
#   nombre flag_sin_tc_sin_acuerdos_sin_prestamos contiene lag, por lo que esa columna del mes entra en la lista
#   y no en data_current. data_hist1 lleva las columnas con lag1 o delta1; data_hist2, las de lag2 o delta2;
#   data_current, todas las que no están en la lista de históricas. Imprime las dimensiones de cada tabla.
# Separación entre sub-modelos/sub-datasets
cols_fijas = [
    "numero_de_cliente",
    "foto_mes",
    "clase_ternaria",
    "clase_binaria12",
    "clase_binaria2"
]

# Identificar TODAS las variables históricas
mask_hist = data.columns.str.contains(
    r"(lag|delta)",
    case=False,
    regex=True
)
cols_hist_todas = data.columns[mask_hist].tolist()

# HIST1: quedarse solamente con lag1 y delta1
cols_hist1 = [
    c for c in cols_hist_todas
    if __import__("re").search(r"(lag|delta)1(?!\d)", c, flags=__import__("re").IGNORECASE)
]
data_hist1 = data[cols_fijas + cols_hist1].copy()

# HIST2: quedarse solamente con lag2 y delta2
cols_hist2 = [
    c for c in cols_hist_todas
    if __import__("re").search(r"(lag|delta)2(?!\d)", c, flags=__import__("re").IGNORECASE)
]
data_hist2 = data[cols_fijas + cols_hist2].copy()

# CURRENT: eliminar TODAS las variables históricas
cols_current = [
    c for c in data.columns
    if c not in cols_hist_todas
    and c not in cols_fijas 
]
data_current = data[cols_fijas + cols_current].copy()

print("Original :", data.shape)
print("HIST 1   :", data_hist1.shape)
print("HIST 2   :", data_hist2.shape)
print("CURRENT  :", data_current.shape)

# [Anotación · líneas 120–132] Quita de las tres tablas las columnas cuyo nombre contiene
#   prestamos_personales, sin distinguir mayúsculas; el comentario lo atribuye a una sugerencia de la cátedra.
#   El filtro actúa sobre el nombre: deuda_prestamos_total y ratio_liquidez_vs_deuda, que el notebook calcula
#   con mprestamos_personales, tienen otro nombre y no se quitan.
# borro prestamos personales x sugerencia de la cátedra
data_hist1 = data_hist1.loc[
    :,
    ~data_hist1.columns.str.contains("prestamos_personales", case=False)
].copy()
data_hist2 = data_hist2.loc[
    :,
    ~data_hist2.columns.str.contains("prestamos_personales", case=False)
].copy()
data_current = data_current.loc[
    :,
    ~data_current.columns.str.contains("prestamos_personales", case=False)
].copy()

# [Anotación · líneas 134–153] Define los meses de cada modelo para la etapa de validación: current entrena
#   con 202103, 202104 y 202105; hist1 con 202104 y 202105; hist2 con 202105; los tres se prueban en 202106. Los
#   comentarios indican que se dejan fuera los meses en que las variables históricas son todas NaN. Arma la
#   lista de columnas que no entran como variables: las tres clases, foto_mes y numero_de_cliente.
# Separo train/test
mes_train_current = [202103, 202104, 202105]
mes_test_current = 202106
train_data_current = data_current[data_current['foto_mes'].isin(mes_train_current)]
test_data_current = data_current[data_current['foto_mes'] == mes_test_current]

mes_train_hist1 = [202104, 202105] # NO Incluimos marzo porque son puros NANS
mes_test_hist1 = 202106
train_data_hist1 = data_hist1[data_hist1['foto_mes'].isin(mes_train_hist1)]
test_data_hist1 = data_hist1[data_hist1['foto_mes'] == mes_test_hist1]

mes_train_hist2 = [202105] # NO Incluimos ni marzo ni abril porque son puros NANS
mes_test_hist2 = 202106
train_data_hist2 = data_hist2[data_hist2['foto_mes'].isin(mes_train_hist2)]
test_data_hist2 = data_hist2[data_hist2['foto_mes'] == mes_test_hist2]

# Tiro cols 
cols_target = ['clase_ternaria', 'clase_binaria12', 'clase_binaria2']
cols_inutiles = ['foto_mes', 'numero_de_cliente']
cols_a_drop = cols_target + cols_inutiles

# [Anotación · líneas 155–197] Para cada una de las tres tablas de entrenamiento conserva todas las filas cuya
#   clase_ternaria no es CONTINUA y una muestra al azar del 20% de las CONTINUA (random_state = 42). Separa
#   variables y etiqueta (clase_binaria12), arma el lgb.Dataset y prepara las variables de 202106. La etiqueta
#   con que se evalúa 202106 vale 1 sólo para BAJA+2.
# Undersampling + separación X e y + lgb data

# current
df_bajas_current = train_data_current[train_data_current["clase_ternaria"] != "CONTINUA"]
df_continua_current = train_data_current[train_data_current["clase_ternaria"] == "CONTINUA"].sample(
    frac=0.20, random_state=semilla)
train_under_current = pd.concat([df_bajas_current, df_continua_current])

X_train_current = train_under_current.drop(cols_a_drop, axis=1)
y_train_current = train_under_current['clase_binaria12']
 
X_test_current = test_data_current.drop(cols_a_drop, axis=1)
y_test_true_current = np.where(test_data_current['clase_ternaria'] == "BAJA+2", 1, 0) # deberia ser idem de arriba # dejo igual para legibilidad


train_data_lgb_current = lgb.Dataset(X_train_current, label= y_train_current)

# hist 1

df_bajas_hist1 = train_data_hist1[train_data_hist1["clase_ternaria"] != "CONTINUA"]
df_continua_hist1 = train_data_hist1[train_data_hist1["clase_ternaria"] == "CONTINUA"].sample(
    frac=0.20, random_state=semilla)
train_under_hist1 = pd.concat([df_bajas_hist1, df_continua_hist1])

X_train_hist1 = train_under_hist1.drop(cols_a_drop, axis=1)
y_train_hist1 = train_under_hist1['clase_binaria12']

X_test_hist1 = test_data_hist1.drop(cols_a_drop, axis=1)

train_data_lgb_hist1 = lgb.Dataset(X_train_hist1, label= y_train_hist1)

# hist 2
df_bajas_hist2 = train_data_hist2[train_data_hist2["clase_ternaria"] != "CONTINUA"]
df_continua_hist2 = train_data_hist2[train_data_hist2["clase_ternaria"] == "CONTINUA"].sample(
    frac=0.20, random_state=semilla)
train_under_hist2 = pd.concat([df_bajas_hist2, df_continua_hist2])

X_train_hist2 = train_under_hist2.drop(cols_a_drop, axis=1)
y_train_hist2 = train_under_hist2['clase_binaria12']
 
X_test_hist2 = test_data_hist2.drop(cols_a_drop, axis=1)

train_data_lgb_hist2 = lgb.Dataset(X_train_hist2, label= y_train_hist2)

# [Anotación · líneas 199–215] Define los valores de negocio: ganancia nominal 2.200.000, efectividad 0,5 y
#   costo por estímulo 27.500; la ganancia por acierto es 2.200.000 × 0,5 − 27.500. La función
#   ganancia_por_envios ordena las predicciones de mayor a menor, toma las primeras cant_envios y suma la
#   ganancia por acierto en los positivos y −27.500 en los demás.
# Funcion de ganancia / elementos de negocio

ganancia_nominal = 2_200_000
efectividad = 0.5
costo_estimulo = 27_500 
ganancia_acierto = ganancia_nominal * efectividad - costo_estimulo 

def ganancia_por_envios(y_pred, y_true, cant_envios): # para optimizar alpha abajo
    orden = np.argsort(y_pred)[::-1]
    y_ordenado = np.asarray(y_true)[orden]
    enviados = y_ordenado[:cant_envios]
    ganancia = np.where(
        enviados == 1,
        ganancia_acierto,
        -costo_estimulo
    )
    return ganancia.sum()

# [Anotación · líneas 217–243] Arma los parámetros de LightGBM: objective binary, boosting gbdt, max_bin 31,
#   boost_from_average True, feature_pre_filter False, seed igual a la primera semilla de la lista, num_leaves
#   18, learning_rate 0,00625238, min_data_in_leaf 1748, feature_fraction 0,939774, bagging_fraction 0,376689 y
#   bagging_freq 1. Al unir los diccionarios la métrica queda en auc. Fija 4928 iteraciones.
# PARAMETROS OPTIMIZADOS

FIXED_PARAMS = {
        'objective': 'binary',
        'metric': 'custom',
        'boosting_type': 'gbdt',  
        'first_metric_only': True,  
        'boost_from_average': True, 
        'feature_pre_filter': False,  
        'max_bin': 31,  
        'seed': semillas[0],
        'verbose': -1
}
OPT_PARAMS = {'num_leaves': 18,
 'learning_rate': 0.00625238,
 'min_data_in_leaf': 1748,
 'feature_fraction': 0.939774,
 'bagging_fraction': 0.376689,
 'bagging_freq': 1}

PARAMS = {
    **FIXED_PARAMS,
    **OPT_PARAMS,
    "metric": "auc",
}

NUM_ROUNDS = 4928 

# [Anotación · líneas 245–271] Entrena los tres modelos de validación (current, hist1, hist2) con los mismos
#   parámetros y 4928 iteraciones, sin conjunto de validación ni parada temprana, y predice 202106 con cada uno.
# ENTRENAMIENTO SOBRE CONJUNTO DE ENTRENAMIENTO

# CURRENT 
model_current = lgb.train(
    PARAMS,
    train_data_lgb_current,
    num_boost_round=NUM_ROUNDS
)

y_pred_current = model_current.predict(X_test_current)

# HIST 1 
model_hist1 = lgb.train(
    PARAMS,
    train_data_lgb_hist1,
    num_boost_round=NUM_ROUNDS
)
y_pred_hist1 = model_hist1.predict(X_test_hist1)

# HIST 2
model_hist2 = lgb.train(
    PARAMS,
    train_data_lgb_hist2,
    num_boost_round=NUM_ROUNDS
)

y_pred_hist2 = model_hist2.predict(X_test_hist2)


# [Anotación · líneas 274–336] Recorre una grilla de pesos de 0 a 1 con paso 0,05 para current e hist1; el
#   peso de hist2 es lo que falta para sumar 1, y se saltean las combinaciones en que queda fuera del rango de 0
#   a 1. Para cada combinación calcula dos scores sobre 202106: el promedio ponderado de las probabilidades y el
#   promedio ponderado de los rankings percentiles de cada modelo. Para cada score y cada cantidad de envíos de
#   8.000 a 15.000 de a 1.000 calcula la ganancia contra BAJA+2 y guarda el resultado en una tabla.
# OPTIMIZACION DE ENSAMBLE Y PUNTOS DE CORTE
# ==========================================
# OPTIMIZAR ENSEMBLE - JUNIO
# ==========================================

pesos = np.arange(0, 1.01, 0.05)
cant_envios = range(8000, 15001, 1000)
resultados_ensemble = []

# Rankings de cada modelo
rank_current = pd.Series(y_pred_current).rank(pct=True).values
rank_hist1 = pd.Series(y_pred_hist1).rank(pct=True).values
rank_hist2 = pd.Series(y_pred_hist2).rank(pct=True).values
for w_current in pesos:
    for w_hist1 in pesos:
        w_hist2 = 1 - w_current - w_hist1
        # solo combinaciones válidas
        if w_hist2 < -1e-10 or w_hist2 > 1 + 1e-10:
            continue
        # --------------------------
        # Ensemble de probabilidades
        # --------------------------
        score_proba = (
            w_current * y_pred_current
            + w_hist1 * y_pred_hist1
            + w_hist2 * y_pred_hist2
        )
        # --------------------------
        # Ensemble de rankings
        # --------------------------
        score_rank = (
            w_current * rank_current
            + w_hist1 * rank_hist1
            + w_hist2 * rank_hist2
        )
        for n in cant_envios:
            ganancia_proba = ganancia_por_envios(
                score_proba,
                y_test_true_current,
                n
            )
            resultados_ensemble.append({
                "tipo": "probas",
                "w_current": w_current,
                "w_hist1": w_hist1,
                "w_hist2": w_hist2,
                "cant_envios": n,
                "ganancia": ganancia_proba
            })
            ganancia_rank = ganancia_por_envios(
                score_rank,
                y_test_true_current,
                n
            )
            resultados_ensemble.append({
                "tipo": "rankings",
                "w_current": w_current,
                "w_hist1": w_hist1,
                "w_hist2": w_hist2,
                "cant_envios": n,
                "ganancia": ganancia_rank
            })
df_ensemble = pd.DataFrame(resultados_ensemble)

# [Anotación · líneas 338–366] Elige, para cada tipo de ensamble (probabilidades y rankings), la fila de mayor
#   ganancia, la imprime y guarda sus tres pesos. La cantidad de envíos de esa fila se imprime y no se usa más
#   adelante en el script.
# ==========================================
# MEJOR ENSEMBLE
# ==========================================

mejor_proba = df_ensemble[
    df_ensemble["tipo"] == "probas"
].loc[
    lambda x: x["ganancia"].idxmax()
]
mejor_rank = df_ensemble[
    df_ensemble["tipo"] == "rankings"
].loc[
    lambda x: x["ganancia"].idxmax()
]
print("MEJOR ENSEMBLE PROBAS")
print(mejor_proba)
print("\nMEJOR ENSEMBLE RANKINGS")
print(mejor_rank)

# ==========================================
# Pesos del mejor ensemble de 3 modelos
# ==========================================

w_current_proba = mejor_proba["w_current"]
w_hist1_proba = mejor_proba["w_hist1"]
w_hist2_proba = mejor_proba["w_hist2"]
w_current_rank = mejor_rank["w_current"]
w_hist1_rank = mejor_rank["w_hist1"]
w_hist2_rank = mejor_rank["w_hist2"]


# [Anotación · líneas 369–402] Prepara los datos del entrenamiento final, sin submuestreo y con la etiqueta
#   clase_binaria12: current con 202103 a 202106, hist1 con 202104 a 202106 e hist2 con 202105 y 202106. Para
#   cada tabla separa las variables de 202108 y los numero_de_cliente de ese mes.
# ==========================================
# Entrenamiento completo y creación de archivos para la entrega
# ==========================================

# ==========================================
# Data para entrega   
# ==========================================
# CURRENT

train_data_marzo_junio_current = data_current[data_current['foto_mes'].isin([202103, 202104, 202105, 202106])]
test_data_agosto_current = data_current[data_current['foto_mes'] == 202108]
X_train_marzo_junio_current = train_data_marzo_junio_current.drop(cols_a_drop, axis=1)
y_train_marzo_junio_current = train_data_marzo_junio_current['clase_binaria12']
train_data_lgb_current_final = lgb.Dataset(X_train_marzo_junio_current, label=y_train_marzo_junio_current)
X_agosto_current = test_data_agosto_current.drop(cols_a_drop, axis=1)
numero_cliente_agosto_current = test_data_agosto_current["numero_de_cliente"]

# HIST 1
train_data_abril_junio_hist1 = data_hist1[data_hist1['foto_mes'].isin([202104, 202105, 202106])]
test_data_agosto_hist1 = data_hist1[data_hist1['foto_mes'] == 202108]
X_train_abril_junio_hist1 = train_data_abril_junio_hist1.drop(cols_a_drop, axis=1)
y_train_abril_junio_hist1 = train_data_abril_junio_hist1['clase_binaria12']
train_data_lgb_hist_final1 = lgb.Dataset(X_train_abril_junio_hist1, label=y_train_abril_junio_hist1)
X_agosto_hist1 = test_data_agosto_hist1.drop(cols_a_drop, axis=1)
numero_cliente_agosto_hist1 = test_data_agosto_hist1["numero_de_cliente"]

# HIST 2
train_data_mayo_junio_hist2 = data_hist2[data_hist2['foto_mes'].isin([202105, 202106])]
test_data_agosto_hist2 = data_hist2[data_hist2['foto_mes'] == 202108]
X_train_mayo_junio_hist2 = train_data_mayo_junio_hist2.drop(cols_a_drop, axis=1)
y_train_mayo_junio_hist2 = train_data_mayo_junio_hist2['clase_binaria12']
train_data_lgb_hist_final2 = lgb.Dataset(X_train_mayo_junio_hist2, label=y_train_mayo_junio_hist2)
X_agosto_hist2 = test_data_agosto_hist2.drop(cols_a_drop, axis=1)
numero_cliente_agosto_hist2 = test_data_agosto_hist2["numero_de_cliente"]

# [Anotación · líneas 404–417] Verifica con assert que los clientes de 202108 están en el mismo orden en las
#   tres tablas e imprime cuántos son.
# ============================================================
# CHEQUEO: LOS CLIENTES DE AGOSTO COINCIDEN
# ============================================================
assert np.array_equal(
    numero_cliente_agosto_current.values,
    numero_cliente_agosto_hist1.values
), "ERROR: CURRENT y HIST1 no tienen los mismos clientes en el mismo orden."
assert np.array_equal(
    numero_cliente_agosto_current.values,
    numero_cliente_agosto_hist2.values
), "ERROR: CURRENT y HIST2 no tienen los mismos clientes en el mismo orden."
print(
    f"Clientes agosto: {len(numero_cliente_agosto_current)}"
)


# [Anotación · líneas 420–429] Copia los parámetros de cada modelo de validación y toma su cantidad de
#   iteraciones con current_iteration(), para usarlos en el entrenamiento final.
# Los envíos se guardan en resultados/ (sin subcarpetas).
# ============================================================
# PARAMETROS
# ============================================================
base_params_current = model_current.params.copy()
model_best_iter_current = model_current.current_iteration()
base_params_hist1 = model_hist1.params.copy()
model_best_iter_hist1 = model_hist1.current_iteration()
base_params_hist2 = model_hist2.params.copy()
model_best_iter_hist2 = model_hist2.current_iteration()

# [Anotación · líneas 431–460] Lee, si existe, el archivo modelo_final_semillas_completadas.txt de
#   resultados/. Recorre las 16 semillas: si una figura como completada y sus cinco Parquet existen, la saltea;
#   si falta alguno, la vuelve a ejecutar. Para cada semilla copia los parámetros de los tres modelos y
#   reemplaza seed por la semilla en curso.
# ============================================================
# LOOP DE SEMILLAS
# ============================================================
# Control de avance: una semilla completa no se repite.
# Se guardan rankings Parquet por semilla; los CSV se generan solo al final. 
checkpoint_path = os.path.join(resultados_path, f"{RUN_ID}_semillas_completadas.txt")
semillas_completadas = set()

if os.path.exists(checkpoint_path):
    with open(checkpoint_path, "r", encoding="utf-8") as f:
        semillas_completadas = {int(x.strip()) for x in f if x.strip()}
for seed in semillas_envio:
    if seed in semillas_completadas:
        archivos_semilla = [
            Path(resultados_path) / f"{RUN_ID}_{tipo}_seed_{seed}.parquet"
            for tipo in ("current", "hist1", "hist2", "ensemble_proba", "ensemble_rank")
        ]
        if all(ruta.exists() for ruta in archivos_semilla):
            print(f"Semilla {seed}: ya completada, se omite")
            continue
        print(f"Semilla {seed}: checkpoint incompleto, se vuelve a ejecutar")

    print(f"\n========== SEMILLA {seed} ==========")

    params_current = base_params_current.copy()
    params_current["seed"] = seed
    params_hist1 = base_params_hist1.copy()
    params_hist1["seed"] = seed
    params_hist2 = base_params_hist2.copy()
    params_hist2["seed"] = seed

# [Anotación · líneas 462–493] Con la semilla en curso entrena los tres modelos sobre los datos finales y
#   predice 202108 con cada uno.
    # --------------------------------------------------------
    # CURRENT
    # --------------------------------------------------------

    modelo_current = lgb.train(
        params_current,
        train_data_lgb_current_final,
        num_boost_round=model_best_iter_current
    )
    proba_current = modelo_current.predict(X_agosto_current)
    
    # --------------------------------------------------------
    # HIST 1
    # --------------------------------------------------------
    
    modelo_hist1 = lgb.train(
        params_hist1,
        train_data_lgb_hist_final1,
        num_boost_round=model_best_iter_hist1
    )
    proba_hist1 = modelo_hist1.predict(X_agosto_hist1)
    
    # --------------------------------------------------------
    # HIST 2
    # --------------------------------------------------------
    
    modelo_hist2 = lgb.train(
        params_hist2,
        train_data_lgb_hist_final2,
        num_boost_round=model_best_iter_hist2
    )
    proba_hist2 = modelo_hist2.predict(X_agosto_hist2)
    
# [Anotación · líneas 495–528] Combina los tres modelos de dos maneras: promedio ponderado de las
#   probabilidades con los pesos elegidos para probabilidades, y promedio ponderado de los rankings percentiles
#   de cada modelo con los pesos elegidos para rankings.
    # --------------------------------------------------------
    # ENSEMBLE PROBABILIDADES
    # --------------------------------------------------------
    
    score_ensemble_proba = (
        w_current_proba * proba_current
        + w_hist1_proba * proba_hist1
        + w_hist2_proba * proba_hist2
    )
    
    # --------------------------------------------------------
    # ENSEMBLE RANKINGS
    # --------------------------------------------------------
    
    rank_current = (
        pd.Series(proba_current)
        .rank(pct=True)
        .values
    )
    rank_hist1 = (
        pd.Series(proba_hist1)
        .rank(pct=True)
        .values
    )
    rank_hist2 = (
        pd.Series(proba_hist2)
        .rank(pct=True)
        .values
    )
    score_ensemble_rank = (
        w_current_rank * rank_current
        + w_hist1_rank * rank_hist1
        + w_hist2_rank * rank_hist2
    )
    
# [Anotación · líneas 530–568] Arma cinco tablas con numero_de_cliente y su valor, ordenadas de mayor a menor:
#   la probabilidad de cada uno de los tres modelos y el score de cada uno de los dos ensambles.
    # ========================================================
    # RANKINGS
    # ========================================================
    
    ranking_current = pd.DataFrame({
        "numero_de_cliente": numero_cliente_agosto_current.values,
        "proba": proba_current
    }).sort_values(
        "proba",
        ascending=False
    )
    ranking_hist1 = pd.DataFrame({
        "numero_de_cliente": numero_cliente_agosto_hist1.values,
        "proba": proba_hist1
    }).sort_values(
        "proba",
        ascending=False
    )
    ranking_hist2 = pd.DataFrame({
        "numero_de_cliente": numero_cliente_agosto_hist2.values,
        "proba": proba_hist2
    }).sort_values(
        "proba",
        ascending=False
    )
    ranking_proba = pd.DataFrame({
        "numero_de_cliente": numero_cliente_agosto_current.values,
        "score": score_ensemble_proba
    }).sort_values(
        "score",
        ascending=False
    )
    ranking_rank = pd.DataFrame({
        "numero_de_cliente": numero_cliente_agosto_current.values,
        "score": score_ensemble_rank
    }).sort_values(
        "score",
        ascending=False
    )
# [Anotación · líneas 569–616] Guarda las cinco tablas en resultados/ como Parquet, con el identificador de
#   corrida, el tipo y la semilla en el nombre. Después agrega la semilla al archivo de semillas completadas y
#   fuerza la escritura a disco.
    # ========================================================
    # GUARDAR RANKINGS
    # ========================================================
    
    ranking_current.to_parquet(
        os.path.join(
            resultados_path,
            f"{RUN_ID}_current_seed_{seed}.parquet"
        ),
        index=False
    )
    ranking_hist1.to_parquet(
        os.path.join(
            resultados_path,
            f"{RUN_ID}_hist1_seed_{seed}.parquet"
        ),
        index=False
    )
    ranking_hist2.to_parquet(
        os.path.join(
            resultados_path,
            f"{RUN_ID}_hist2_seed_{seed}.parquet"
        ),
        index=False
    )
    ranking_proba.to_parquet(
        os.path.join(
            resultados_path,
            f"{RUN_ID}_ensemble_proba_seed_{seed}.parquet"
        ),
        index=False
    )
    ranking_rank.to_parquet(
        os.path.join(
            resultados_path,
            f"{RUN_ID}_ensemble_rank_seed_{seed}.parquet"
        ),
        index=False
    )
    
    # No se generan CSV individuales: los rankings Parquet se combinan al final.

    # Registrar solamente después de guardar todos los resultados de la semilla.
    with open(checkpoint_path, "a", encoding="utf-8") as f:
        f.write(f"{seed}\n")
        f.flush()
        os.fsync(f.fileno())
    print("OK")


# [Anotación · líneas 619–653] Define ejecutar_ensemble_semillas. Valida que N_ENVIOS_FINAL sea un entero
#   positivo. Para cada método (proba y rank) lee el Parquet del ensamble de cada una de las 16 semillas; si
#   falta alguno, le faltan columnas o tiene clientes duplicados, lanza un error. Convierte el score de cada
#   semilla en ranking percentil.
# ============================================================
# ENSAMBLE MULTISEMILLA FINAL
# ============================================================
# Los archivos por semilla se generan arriba y se recuperan por su nombre exacto.
# La combinación es el promedio de los rankings percentiles por semilla,
# siguiendo el criterio del bloque de ensamble multisemilla original.

def ejecutar_ensemble_semillas():
    if N_ENVIOS_FINAL is None:
        print("PENDIENTE: definir N_ENVIOS_FINAL; no se generan CSVs finales.")
        return
    if not isinstance(N_ENVIOS_FINAL, int) or isinstance(N_ENVIOS_FINAL, bool) or N_ENVIOS_FINAL <= 0:
        raise ValueError("N_ENVIOS_FINAL debe ser un entero positivo")

    for metodo in ("proba", "rank"):
        partes = []
        for seed in semillas_envio:
            ruta = Path(resultados_path) / (
                f"{RUN_ID}_ensemble_{metodo}_seed_{seed}.parquet"
            )
            if not ruta.exists():
                raise FileNotFoundError(
                    f"Falta la predicción de la semilla {seed}: {ruta}. "
                    "No se generará un ensamble con menos semillas que las configuradas."
                )
            df = pd.read_parquet(ruta)
            if not {"numero_de_cliente", "score"}.issubset(df.columns):
                raise ValueError(f"Faltan columnas en {ruta}")
            if df["numero_de_cliente"].duplicated().any():
                raise ValueError(f"Clientes duplicados en {ruta}")
            partes.append(
                df[["numero_de_cliente"]].assign(
                    **{f"s{seed}": df["score"].rank(pct=True)}
                )
            )

# [Anotación · líneas 655–682] Une las 16 tablas por numero_de_cliente (unión interna uno a uno) y verifica
#   que todas tengan los mismos clientes. Promedia los 16 rankings percentiles, ordena por ese promedio de mayor
#   a menor y, en los empates, por numero_de_cliente ascendente. Escribe los primeros 10.500 numero_de_cliente
#   en un CSV sin encabezado ni índice, cuyo nombre lleva el método, la cantidad de envíos y la cantidad de
#   semillas. La última línea llama a la función.
        combinado = partes[0]
        for parte in partes[1:]:
            combinado = combinado.merge(
                parte, on="numero_de_cliente", how="inner", validate="one_to_one"
            )
        if len(combinado) != len(partes[0]) or any(
            len(combinado) != len(parte) for parte in partes
        ):
            raise ValueError("Las semillas no contienen exactamente los mismos clientes")

        columnas_semillas = [f"s{seed}" for seed in semillas_envio]
        combinado["score"] = combinado[columnas_semillas].mean(axis=1)
        ranking = combinado.sort_values(
            ["score", "numero_de_cliente"], ascending=[False, True]
        )
        if N_ENVIOS_FINAL > len(ranking):
            raise ValueError("N_ENVIOS_FINAL excede la cantidad de clientes")

        salida = Path(resultados_path) / (
            f"multisemilla_ensemble_{metodo}_{N_ENVIOS_FINAL}_nsemillas_{len(partes)}.csv"
        )
        ranking["numero_de_cliente"].head(N_ENVIOS_FINAL).astype("int64").to_csv(
            salida, index=False, header=False
        )
        print("Generado:", salida)


ejecutar_ensemble_semillas()
```


## Explicaciones del alumno (texto original)

### competencia_01/README.md

> # Competencia 01 — Predicción de churn bancario
>
> ## 1. Descripción del proyecto
>
> Este repositorio contiene el código utilizado para generar las predicciones de la primera competencia de la materia DMEyF, centrada en la detección de churn bancario. En concreto, el objetivo es detectar en agosto los clientes que se darán de baja en octubre, explotando datos de negocio medidos en los seis meses anteriores.
>
> Para la reproducción de los resultados obtenidos en la competencia, plantea una ejecución en dos etapas:
>
> 1. **Feature engineering:** Preprocesamiento de la base de datos original (provista por la cátedra) en SQL. En esta etapa se construye la variable objetivo y se generan variables explicativas, tanto históricas como intra-mes.
> 2. **Entrenamiento y predicción:** Aquí se trabaja con la base preprocesada. Se entrenan tres modelos LightGBM, sobre la base de distintas ventanas temporales. Se los ensambla y se generan las predicciones finales. Su resultado es una lista de IDs de clientes que en agosto muestran potencial de darse de baja pronto, designados destinatarios de una campaña de retención. 
>
> ## 2. Estructura del proyecto
>
> El proyecto se organiza de la siguiente manera:
>
> ```text
> competencia_01/
> ├── README.md
> ├── requirements.txt
> ├── primer_paso_FE_competencia_01.ipynb
> ├── modelo_final.py
> └── data/
>     ├── competencia_01_crudo.csv
>     └── competencia_01_fev4.parquet
> ── resultados/
> ```
> Los archivos de código correspondientes a cada una de las etapas aludidas se guardan en el directorio principal. La carpeta `data/` almacena las bases de trabajo. **Importante:** los archivos de datos no se incluyen en el repositorio. La base original debe colocarse en la carpeta `data/` antes de ejecutar el pipeline. El archivo Parquet se genera durante el feature engineering. En la carpeta `resultados/` se guardará el listado de clientes a estimular, que constituye el entregable final de la competencia. 
>
> ## 3. Requisitos
>
> Para ejecutar el pipeline se requiere:
>
> - **Python 3.13.12.**
> - **DuckDB 1.5.5**, para el procesamiento de datos y la construcción de variables.
> - **JupyterLab 4.5.6**, junto con **JupySQL 0.11.1** y **duckdb-engine 0.17.0**, para ejecutar el notebook de feature engineering.
> - **LightGBM 4.7.0**, para el entrenamiento de los modelos predictivos.
> - **pandas 3.0.3**, **NumPy 2.4.4** y **PyArrow 25.0.0**, para la manipulación de datos y la lectura y escritura de archivos.
> - Las dependencias adicionales especificadas en `requirements.txt`.
>
> El proyecto fue desarrollado en Windows 11. Las versiones completas de las librerías utilizadas se detallan en la sección 7.1.
>
> Se recomienda utilizar las mismas versiones de Python y de las principales dependencias para facilitar la reproducción de los resultados.
>
> ## 4. Preparación del entorno
>
> Clonar el repositorio y acceder a la carpeta de la competencia.
>
> Instalar las dependencias:
>
> ```bash
> python -m pip install -r requirements.txt
> ```
>
> Colocar el archivo `competencia_01_crudo.csv` en el directorio `data/`.
>
> ## 5. Feature engineering
>
> Se trabajará con el siguiente **archivo:** `primer_paso_FE_competencia_01.ipynb`
>
> ### 5.1. Ejecución
>
> Desde el directorio `competencia_01/`, iniciar JupyterLab:
>
> ```bash
> jupyter lab
> ```
>
> Abrir el notebook `primer_paso_FE_competencia_01.ipynb` y ejecutar las celdas secuencialmente.
>
> ### 5.2. Procesamiento
>
> El notebook realiza las siguientes operaciones:
>
> **A. Carga de datos**
>
> Importa la base original `competencia_01_crudo.csv` utilizando DuckDB.
>
> **B. Construcción de la variable objetivo**
>
> Genera `clase_ternaria` a partir de la presencia de cada cliente en los meses siguientes, distinguiendo las categorías `BAJA+1`, `BAJA+2` y `CONTINUA`.
>
> Para los últimos meses, la disponibilidad de información futura determina qué clases pueden observarse.
>
> **C. Feature engineering del mes actual**
>
> Genera variables derivadas de los datos del mes de observación, incluyendo agregaciones de productos y transacciones, saldos, consumos, endeudamiento, ratios financieros e indicadores de actividad.
>
> **D. Feature engineering histórico**
>
> Genera automáticamente variables históricas para las columnas numéricas elegibles:
>
> - `lag1`: valor de la observación anterior.
> - `lag2`: valor de dos observaciones anteriores.
> - `delta1`: diferencia entre el valor actual y `lag1`.
> - `delta2`: diferencia entre el valor actual y `lag2`.
>
> El procesamiento se realiza en bloques de 25 variables para gestionar el uso de memoria.
>
> ### 5.3. Archivo de salida
>
> El resultado se exporta a:
>
> ```text
> data/competencia_01_fev4.parquet
> ```
>
> Formato: Parquet, compresión ZSTD.
>
> Este archivo constituye la entrada para la etapa de entrenamiento y predicción.
>
> ## 6. Entrenamiento y predicción
>
> Se trabajará con el siguiente **archivo:** `modelo_final.py`
>
> Esta segunda etapa utiliza la base procesada `competencia_01_fev4.parquet` para entrenar y ensamblar modelos LightGBM y generar el listado de clientes a estimular.
>
> ### 6.1. Preparación de los datos
>
> En primer lugar, se construyen dos variables objetivo binarias a partir de `clase_ternaria`:
>
> - `clase_binaria12`: identifica conjuntamente a los clientes `BAJA+1` y `BAJA+2`, frente a `CONTINUA`.
> - `clase_binaria2`: identifica exclusivamente a los clientes `BAJA+2`.
>
> Los modelos se entrenan utilizando `clase_binaria12`, mientras que la evaluación de la ganancia se realiza sobre `BAJA+2`, que constituye el objetivo específico de la competencia.
>
> Adicionalmente, se aplica una normalización mensual a las variables numéricas cuyos nombres comienzan con `m` (i.e.: que designan montos susceptibles a ser afectados por la inflación u otros factores de drift), conservando el cero como referencia. Las variables originales normalizadas son reemplazadas por sus correspondientes versiones con sufijo `_norm0`.
>
> Por último, se excluyen las variables relacionadas con préstamos personales, siguiendo una recomendación de la cátedra.
>
> ### 6.2. Modelos y conjuntos de variables
>
> Se entrenan tres modelos LightGBM que utilizan diferentes conjuntos de variables explicativas:
>
> | Modelo | Variables utilizadas | Entrenamiento para validación | Entrenamiento final | Columnas del subconjunto inicial
> |---|---|---|---|
> | `current` | Variables del mes actual, sin históricos | Marzo–mayo | Marzo–junio | 177
> | `hist1` | Variables históricas `lag1` y `delta1` | Abril–mayo | Abril–junio | 351 
> | `hist2` | Variables históricas `lag2` y `delta2` | Mayo | Mayo–junio | 351
>
> Los tres modelos utilizan la misma variable objetivo binaria y la misma configuración de hiperparámetros. Se probaron configuraciones de hiperparámetros alternativas y específicas para cada modelo, sin que se observe una mejora en su capacidad predictiva.
>
> Durante la etapa de validación, se aplica undersampling de la clase `CONTINUA`, conservando aleatoriamente el 20% de sus observaciones y la totalidad de los casos de baja. Para el entrenamiento final se utiliza la totalidad de las observaciones de los meses seleccionados, sin undersampling.
>
> ### 6.3. Configuración de LightGBM
>
> Se utiliza LightGBM con objetivo de clasificación binaria y boosting `gbdt`.
>
> Los hiperparámetros seleccionados son:
>
> | Hiperparámetro | Valor |
> |---|---:|
> | `num_leaves` | 18 |
> | `learning_rate` | 0.00625238 |
> | `min_data_in_leaf` | 1748 |
> | `feature_fraction` | 0.939774 |
> | `bagging_fraction` | 0.376689 |
> | `bagging_freq` | 1 |
> | `max_bin` | 31 |
> | Número de iteraciones | 4928 |
>
> Los valores provienen de la experimentación previa y se incorporan directamente al script. La búsqueda de hiperparámetros no forma parte de este pipeline de reproducción.
>
> ### 6.4. Validación y optimización del ensamble
>
> Se utiliza junio de 2021 como período de validación, por ser el último mes para el cual se dispone de la clasificación completa necesaria para evaluar `BAJA+2`.
>
> Cada modelo genera predicciones para junio. A partir de estas se comparan dos estrategias de ensamble:
>
> **Ensamble de probabilidades:** promedio ponderado de las probabilidades predichas por `current`, `hist1` e `hist2`.
>
> **Ensamble de rankings:** promedio ponderado de los rankings percentiles de las probabilidades predichas por los tres modelos.
>
> En ambos casos se buscan combinaciones de pesos entre 0 y 1, con incrementos de 0.05 y sujetos a la restricción de que los tres pesos sumen 1.
>
> La selección se realiza maximizando la ganancia monetaria sobre junio, considerando cantidades de estímulos entre 8.000 y 15.000 clientes, con incrementos de 1.000. Los resultados obtenidos son los siguientes: 
>
> | Parámetro | Ensamble de probabilidades | Ensamble de rankings |
> |-----------|---------------------------:|---------------------:|
> | Peso Current | 0.35 | 0.15 |
> | Peso Hist1 | 0.30 | 0.20 |
> | Peso Hist2 | 0.35 | 0.65 |
> | Cantidad óptima de envíos | 13.000 | 12.000 |
> | Ganancia estimada en validación | 430.100.000 | 429.000.000 |
>
> _La cantidad óptima de envíos identificada en esta etapa corresponde exclusivamente al conjunto de validación de junio de 2021. No debe confundirse con la cantidad de envíos de la predicción final de agosto, que se fijó en 10.500 clientes._
>
> La función de ganancia utiliza los siguientes supuestos:
>
> - Ganancia nominal por acierto: 2.200.000.
> - Efectividad del estímulo: 50%.
> - Costo por estímulo: 27.500.
>
> Los pesos seleccionados se utilizan posteriormente para generar las predicciones de agosto.
>
> ### 6.5. Entrenamiento final y ensamble multisemilla
>
> Una vez seleccionados los pesos del ensamble, se reentrenan los tres modelos incorporando junio a los respectivos conjuntos de entrenamiento.
>
> Se utiliza un conjunto de semillas aleatorias generado a partir de una semilla inicial fija (`42`). Para cada semilla se entrenan nuevamente los tres modelos y se calculan las predicciones correspondientes a agosto de 2021.
>
> Las predicciones se combinan en dos niveles:
>
> 1. **Ensamble entre modelos:** para cada semilla se combinan las predicciones de `current`, `hist1` e `hist2` utilizando los pesos seleccionados durante la validación.
> 2. **Ensamble entre semillas:** los scores de cada ensamble se convierten a rankings percentiles y posteriormente se promedian entre semillas, asignando el mismo peso a cada una.
>
> Se generan por separado los resultados del ensamble de probabilidades y del ensamble de rankings. Para la entrega final, se retiene el ensamble de probabilidades, que demuestra de manera consistente una mejor performance en el __leaderboard__ público. 
>
> ### 6.6. Generación de predicciones
>
> Los clientes de agosto se ordenan según el score obtenido en el ensamble multisemilla.
>
> Se seleccionan los primeros 10.500 clientes del ranking, correspondientes a los destinatarios propuestos para la campaña de retención.
>
> Los archivos CSV finales contienen exclusivamente los valores de `numero_de_cliente`, sin encabezado ni índice.
>
> Los archivos se guardan en el directorio `resultados/`.
>
>
> ### 6.7. Ejecución
>
> Una vez generado el archivo `data/competencia_01_fev4.parquet`, ejecutar desde el directorio principal:
>
> ```bash
> python modelo_final.py
> ```
>
> El script realiza la preparación de datos, el entrenamiento para validación, la selección de los pesos del ensamble, el entrenamiento final con múltiples semillas y la generación de los archivos de predicciones.
>
> ## 7. Reproducibilidad
>
> El repositorio contiene el pipeline utilizado para generar las predicciones finales a partir de la base original proporcionada por la cátedra.
>
> La reproducción requiere ejecutar secuencialmente las dos etapas documentadas:
>
> 1. Ejecutar `primer_paso_FE_competencia_01.ipynb` para generar `competencia_01_fev4.parquet`.
> 2. Ejecutar `modelo_final.py` para entrenar los modelos y generar las predicciones finales.
>
> ### 7.1. Dependencias y entorno
>
> El proyecto fue desarrollado en Python, utilizando DuckDB y JupySQL para el procesamiento y la construcción de variables, y LightGBM para el entrenamiento de los modelos predictivos. Se emplearon asimismo pandas y NumPy para la manipulación de datos, PyArrow para la lectura y escritura de archivos Parquet, y JupyterLab para la ejecución del notebook de feature engineering.
>
> Las dependencias necesarias para ejecutar el pipeline se encuentran especificadas en `requirements.txt`.
>
> El entorno local utilizado durante el desarrollo presenta las siguientes características:
>
> | Componente | Versión |
> |---|---|
> | Sistema operativo | Windows 11 |
> | Python | 3.13.12 |
> | DuckDB | 1.5.5 |
> | pandas | 3.0.3 |
> | NumPy | 2.4.4 |
> | LightGBM | 4.7.0 |
> | PyArrow | 25.0.0 |
> | JupyterLab | 4.5.6 |
> | JupySQL | 0.11.1 |
> | Matplotlib | 3.10.8 |
> | Plotly | 7.0.0 |
> | SciPy | 1.17.1 |
> | Scikit-learn | 1.8.0 |
> | Optuna | 4.9.0 |
> | DuckDB Engine | 0.17.0 |
>
> Para facilitar la reproducción de los resultados, se recomienda utilizar las mismas versiones de Python y de las principales librerías empleadas durante el desarrollo.
>
> ### 7.2. Semillas y parámetros
>
> Se utiliza una semilla inicial fija de `42` para generar la secuencia de semillas empleadas en el ensamble. El script conserva explícitamente los hiperparámetros seleccionados, los períodos de entrenamiento y validación, las reglas de construcción de variables y los procedimientos de combinación de predicciones. Se trabaja sobre 16 semillas. Se seleccionan 10.500 clientes para el estímulo. 
>
> ### 7.3. Archivos intermedios y resultados
>
> El procesamiento produce un archivo Parquet con las variables explicativas y la variable objetivo.
>
> Durante el entrenamiento final se guardan las predicciones por semilla en archivos Parquet, que permiten recuperar los rankings individuales y construir el ensamble multisemilla.
>
> El directorio `resultados/` contiene estos archivos intermedios y los CSV finales de clientes seleccionados.
>
> El procedimiento de reproducción debe ejecutarse desde el directorio principal del proyecto para asegurar la correcta resolución de las rutas relativas.
>
> ### 7.4. Alcance de la reproducción
>
> El repositorio permite reproducir el procedimiento de feature engineering, entrenamiento, validación, ensamble y generación de predicciones finales, utilizando los hiperparámetros seleccionados durante la experimentación.
>
> No se incluye el proceso completo de búsqueda y optimización de hiperparámetros. Sin embargo, el script de entrenamiento sí reproduce la optimización de los pesos del ensamble y de la cantidad de estímulos sobre el conjunto de validación de junio.
>
> La reproducción requiere disponer de la base de datos original proporcionada por la cátedra. Asimismo, las predicciones pueden presentar diferencias según las versiones de las librerías y el entorno de ejecución, especialmente en el entrenamiento de los modelos LightGBM.
>
> Para verificar la consistencia de los resultados, se recomienda comparar los identificadores de clientes seleccionados en los CSV finales, así como los scores y rankings intermedios.
>
> Como comprobación de reproducibilidad, se compararon los CSV de envíos generados por la implementación original y por la versión definitiva del pipeline utilizando la primera semilla. Se verificó la coincidencia tanto de los identificadores de clientes seleccionados como de su orden de aparición. Esta comprobación corresponde a una ejecución de prueba y no constituye una verificación exhaustiva de las 16 semillas del ensamble final.
>
> ## 8. Lessons learned y próximos pasos
>
> La participación en esta competencia implicó un proceso intenso de experimentación y aprendizaje. Las limitaciones de tiempo, de capacidad de cómputo y mi todavía escasa experiencia con herramientas en la nube dejaron una buena lista de experimentos pendientes para la próxima competencia. Entre ellos, destaco:
>
> - **Análisis y selección de atributos (X).** Probé distintas versiones de los modelos excluyendo variables de baja relevancia, sin observar mejoras en su capacidad predictiva. Sin embargo, creo que hay margen para refinar este ejercicio. También incorporé algunas variables que dieron buenos resultados, especialmente ciertos *flags* asociados a señales tempranas de baja, pero me gustaría explorar nuevas posibilidades de manera más sistemática.
>
> - **Estrategias de undersampling.** En este pipeline utilicé distintas estrategias de muestreo para la validación y el entrenamiento final. Me gustaría comparar sus efectos de manera más sistemática y evaluar cómo inciden en la capacidad predictiva y en el ranking de clientes.
>
> - **Transformaciones de variables.** Experimenté con distintas transformaciones de los atributos originales, incluyendo rankings percentiles, indicadores de pertenencia a las colas de las distribuciones y la normalización con cero fijo utilizada en esta versión. Me hubiera gustado disponer de más tiempo para probar otras alternativas, como transformaciones logarítmicas de variables con distribuciones muy asimétricas y colas largas.
>
> - **Optimización de hiperparámetros.** Debido a las restricciones de tiempo y recursos computacionales, limité tanto la cantidad de hiperparámetros explorados como el número de iteraciones de optimización. Considero que existe margen para mejorar este proceso y me gustaría profundizar mi conocimiento de los hiperparámetros de LightGBM y sus efectos sobre el desempeño de los modelos.
>
> En definitiva, esta primera competencia me permitió poner en práctica distintas herramientas y estrategias, pero también identificar aspectos metodológicos y técnicos en los que quiero seguir profundizando. ¡Allá vamos, segunda competencia! _#AguantenLosLunes_

