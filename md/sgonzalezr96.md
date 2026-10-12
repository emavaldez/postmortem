# sgonzalezr96 — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: sgonzalezr96
- Repositorio: https://github.com/sgonzalezr96/DMFyE_C1
- Link posteado: https://github.com/sgonzalezr96/DMFyE_C1
- Commit: 7390f7ac11152fe6c0847945cdae9addc32eaf23
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/sgonzalezr96/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/sgonzalezr96.json

## Resumen

La entrega contiene dos notebooks de Python, un README, un requirements.txt, la carpeta registro/ con cuatro JSON de la corrida y la carpeta referencia/ con dos CSV de IDs. La notebook 01_target_sql.ipynb arma clase_ternaria con SQL en DuckDB a partir del archivo crudo y exporta competencia_01.csv. La notebook 19_Modelo_Final.ipynb parte de ese archivo: pasa ccajas_depositos de 202105 a nulo, calcula lags y deltas de 1 y 2 meses y tendencia y promedio de tres observaciones, divide cada variable por su máximo absoluto del mes y excluye préstamos personales. Luego selecciona variables con canaritos, busca tres hiperparámetros de LightGBM con Optuna (5 trials, AUC en 202106, entrenando con 202103–202104), valida con 10 semillas, reentrena con 202103–202106 y promedia las probabilidades de 202108 de las 10 semillas. Escribe listas de IDs para 11 cortes entre 10.000 y 15.000. Según el README, el envío final es el corte de 12.500, con ganancia pública 101,4200; registro/envio_final.json anota public_gain 100.43 para ese mismo archivo.

**Qué entrega.** Un CSV sin encabezado con una columna de numero_de_cliente: los clientes de mayor probabilidad promedio en 202108. El repositorio incluye en referencia/ dos archivos del mismo ensamble: SofiaCerca19Ensamble_20261011_162005_top12500.csv (12.500 IDs) y SofiaCerca19Ensamble_20261011_162005_top13000.csv (13.000 IDs, cuyos primeros 12.500 son los del otro archivo). El README (líneas 3, 44 y 50) y registro/envio_final.json indican como envío final el de 12.500; el paso 5 del README y la variable CORTE_FINAL = 13000 de la notebook 19 nombran como candidato final el de 13.000.

**Cómo se ejecuta.** Según el README: usar Python 3.14.7, crear un entorno e instalar con 'python -m pip install -r requirements.txt'; crear data/ en la raíz del repositorio y colocar allí competencia_01.csv (no incluido); abrir notebooks/19_Modelo_Final.ipynb, reiniciar el kernel y ejecutar todas las celdas en orden; el ensamble queda en resultados/exploracion19_…/envios/…/SofiaCerca19Ensamble_…/. Para generar competencia_01.csv desde data/competencia_01_crudo.csv: instalar además jupysql, sqlalchemy y duckdb-engine, abrir Jupyter desde la carpeta notebooks y ejecutar 01_target_sql.ipynb en orden. Para comparar el resultado con el archivo de referencia/, el README indica cambiar sólo CSV_REFERENCIA en la celda de configuración.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: positivo = BAJA+2; CONTINUA y BAJA+1 valen 0. Las filas sin clase_ternaria quedan fuera del entrenamiento y de la validación. La clase ternaria se arma en la notebook 01 según la presencia del cliente en los dos períodos siguientes.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código: se entrena con todas las filas con clase de los meses elegidos. Un comentario de la notebook 19 (línea 54) dice 'No bagging ni undersampling'.
- **Calidad de datos:** ccajas_depositos de 202105 pasa a nulo en tres lugares: en la tabla base de DuckDB, al cargar los datos para modelar y al calcular tendencia y promedio. Los valores no finitos de las variables numéricas pasan a nulo. Con assert se verifica que no haya claves cliente-mes nulas ni duplicadas y que el mes esté entre 1 y 12. Los lags sin mes de origen quedan nulos; no se reemplazan por cero.
- **Drifting:** Cada variable original, lag, delta, tendencia y promedio se divide por el máximo del valor absoluto de esa variable dentro de su foto_mes (columnas con sufijo _norm_mes); si ese máximo es 0 el resultado es 0 y los nulos se conservan. El modelo recibe sólo las columnas _norm_mes.
- **Variables dentro del mes:** No se observa en el código.
- **Variables históricas:** Para cada variable numérica: lag 1 y lag 2 por mes calendario exacto (unión de la tabla consigo misma por cliente e índice de mes) y delta 1 y delta 2 (valor actual menos el lag). Además, tendencia (pendiente de mínimos cuadrados) y promedio sobre la fila actual y las dos filas anteriores del mismo cliente, con al menos 2 valores válidos (sufijos tend3 y avg3), calculados desde el CSV original, que incluye 202107. Todas entran al modelo normalizadas por mes.
- **Selección de variables:** Canaritos: se agregan columnas de ruido uniforme en cantidad igual al 20 % de las variables evaluables (mínimo 10), se entrena un LightGBM con 202103–202104 (1000 árboles, 31 hojas, min_sum_hessian_in_leaf 10, semilla 17) y se ordenan las columnas por importancia gain. Se conservan las variables reales ubicadas antes de la posición 'mediana de las posiciones de los canaritos menos un desvío muestral', más las que tienen a lo sumo un valor distinto en entrenamiento. registro/features_seleccionadas.json lista 400 variables.
- **Optimización de hiperparámetros:** Optuna con TPESampler(seed=17), 5 trials en secuencia, estudio nuevo en memoria. Cada trial entrena con 202103–202104 y la búsqueda maximiza el AUC de 202106. Rangos: num_iterations 1000–2000 de a 100, num_leaves 8–128, min_sum_hessian_in_leaf 0,1–100 en escala logarítmica. La ganancia con umbral 0,025 se guarda como atributo de cada trial.
- **Hiperparámetros finales:** Fijos en el código: objective binary, max_bin 31, min_data_in_leaf 0, feature_fraction 0,50, feature_fraction_bynode 0,20, learning_rate 0,005, deterministic True, force_col_wise True. Los tres buscados se toman del trial de mayor AUC; según el README y registro/configuracion_corrida.json: num_iterations 1000, num_leaves 103, min_sum_hessian_in_leaf 9.311090875055461.
- **Semillas:** Diez semillas escritas en el código: 17, 103, 211, 307, 401, 503, 601, 701, 809 y 907; cada una se asigna a seed, feature_fraction_seed y data_random_seed. La búsqueda con Optuna y los canaritos usan la semilla 17.
- **Cantidad de semillas:** 10
- **Ensamble:** Promedio con pesos iguales de las probabilidades de 202108 de los 10 modelos (misma configuración, una semilla cada uno), leídas de los rankings que se guardan por semilla.
- **Corte:** Cantidad fija de clientes, ordenados por probabilidad promedio descendente con desempate por numero_de_cliente ascendente. La notebook escribe 11 cortes (10.000 a 15.000 de a 500) y marca como final CORTE_FINAL = 13000. El README (líneas 3 y 44), registro/envio_final.json y registro/configuracion_corrida.json (corte_final 12500) indican 12.500 como corte del envío. Según el README, la elección consideró la validación de 202106 y la comparación pública de 202108.
- **Validación:** Mes futuro: con modelos entrenados en 202103–202104 se mide en 202106 el AUC, la ganancia con umbral 0,025 y la ganancia acumulada en cada corte (10.000 a 15.000), para cada una de las 10 semillas y para el promedio de sus probabilidades. La ganancia suma 1.072.500 por cada BAJA+2 incluido y resta 27.500 por cada otro cliente incluido.
- **Salidas:** Dentro de resultados/exploracion19_<fecha>/: el CSV con lags, deltas y normalización y fe/config_fe.json; historia3.pkl; importancias.csv y seleccion.json; comparacion_seleccion.json; trials.csv; tablas de validación por semilla, por corte y del promedio; configuracion.json y requirements_versiones.txt; por semilla, modelo_seed<semilla>.txt, ranking_seed<semilla>_ANALISIS.csv y 11 CSV de IDs; para el promedio, ranking_ensamble_ANALISIS.csv, ensamble.json y 11 CSV <prefijo>_top<corte>.csv sin encabezado; y comparacion_csv.json si existe el archivo de referencia.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Estandarización o normalización por mes (`drifting.estandarizacion_por_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Python 3.14.7 (README y registro/configuracion_corrida.json). requirements.txt fija pandas 3.0.6, numpy 2.5.3, lightgbm 4.7.0, optuna 5.0.0, duckdb 1.5.5 e ipykernel 7.3.0. Para la notebook 01 el README pide además jupysql, sqlalchemy y duckdb-engine, sin versión. No se declara máquina ni sistema operativo. Las notebooks usan rutas relativas (../data y la carpeta que contiene data/competencia_01.csv); los JSON de registro/ guardan como origen del dataset la ruta C:\Users\sofia\Desktop\DMEyF\data\competencia_01.csv. La notebook 19 configura DuckDB con límite de memoria de 8 GB y 2 hilos (1 hilo para lags y normalización).

## Pasos del camino de la entrega

1. **Construcción de clase_ternaria desde el archivo crudo.** La notebook 01 carga data/competencia_01_crudo.csv en DuckDB, arma la grilla de clientes por períodos, marca la presencia de cada cliente en el mes y en los dos períodos siguientes y asigna CONTINUA, BAJA+2, BAJA+1 o NULL. Exporta data/competencia_01.csv con las filas en las que el cliente está presente. Según el README, este paso se omite si ya se dispone del archivo con clase_ternaria. (`notebooks/01_target_sql.ipynb` líneas 31–35; `notebooks/01_target_sql.ipynb` líneas 145–190; `notebooks/01_target_sql.ipynb` líneas 233–238; `README.md` líneas 5–22)
2. **Parámetros de la corrida.** La notebook 19 define los meses (búsqueda 202103–202104, validación 202106, final 202103–202106, predicción 202108), 5 trials, las 10 semillas, los 11 cortes, el umbral 0,025, los valores de ganancia, los parámetros fijos de LightGBM, los rangos de búsqueda y una carpeta de salida nueva con fecha y hora. (`notebooks/19_Modelo_Final.ipynb` líneas 17–64)
3. **Lectura del dataset, controles y corrección de ccajas_depositos.** Carga competencia_01.csv en DuckDB, verifica claves y meses, arma la lista de variables numéricas y crea la tabla base con los valores no finitos en NULL, ccajas_depositos de 202105 en NULL y un índice de mes consecutivo. (`notebooks/19_Modelo_Final.ipynb` líneas 93–122)
4. **Lags y deltas de 1 y 2 meses.** Para cada variable numérica calcula el valor del mismo cliente 1 y 2 meses calendario antes (lag1, lag2) y la diferencia entre el valor actual y cada lag (delta1, delta2), uniendo la tabla base consigo misma por cliente e índice de mes. (`notebooks/19_Modelo_Final.ipynb` líneas 129–145)
5. **Normalización por máximo absoluto del mes y exportación.** Divide cada variable original, lag y delta por el máximo de su valor absoluto dentro del foto_mes y guarda el resultado con sufijo _norm_mes. Verifica que ninguna columna normalizada supere 1 en valor absoluto y exporta la tabla completa a un CSV dentro de la carpeta de salida. (`notebooks/19_Modelo_Final.ipynb` líneas 148–188)
6. **Carga para modelar, exclusión de préstamos personales y clase binaria.** Lee del CSV de variables sólo las columnas _norm_mes y las de identificación, sin cprestamos_personales, mprestamos_personales ni sus derivadas, para los meses 202103–202106 y 202108. Vuelve a poner en NaN ccajas_depositos de 202105, arma entrenamiento (202103–202104) y validación (202106) y define la etiqueta 1 = BAJA+2. (`notebooks/19_Modelo_Final.ipynb` líneas 191–232)
7. **Tendencia y promedio de tres observaciones.** Relee el CSV original ordenado por cliente y mes y, para cada variable, calcula la pendiente de mínimos cuadrados y el promedio sobre la fila actual y las dos anteriores del mismo cliente (con al menos 2 valores válidos). Normaliza ambos por el máximo absoluto del mes, conserva las filas de 202103–202106 y 202108 y las une al conjunto de datos. (`notebooks/19_Modelo_Final.ipynb` líneas 239–326)
8. **Funciones de AUC, ganancia y entrenamiento.** Define el cálculo del AUC por rangos, la ganancia con umbral 0,025, la ganancia acumulada por corte y la función que entrena LightGBM con los parámetros fijos, la configuración recibida y una semilla. (`notebooks/19_Modelo_Final.ipynb` líneas 333–359)
9. **Selección de variables con canaritos.** Agrega columnas de ruido uniforme (20 % de las variables evaluables, mínimo 10), entrena un LightGBM de 1000 árboles con 202103–202104 y conserva las variables reales cuya posición por importancia gain es menor que la mediana de las posiciones de los canaritos menos un desvío muestral, más las que tienen a lo sumo un valor distinto. Después compara la selección con una lista de referencia de 400 variables escrita en el código, sin reemplazarla. (`notebooks/19_Modelo_Final.ipynb` líneas 366–457; `registro/features_seleccionadas.json` líneas 1–402)
10. **Búsqueda de hiperparámetros con Optuna.** Ejecuta 5 trials con TPESampler(seed=17): cada uno propone num_iterations, num_leaves y min_sum_hessian_in_leaf, entrena con 202103–202104 y devuelve el AUC de 202106. Guarda trials.csv e imprime si los parámetros encontrados coinciden con una configuración de referencia. Según registro/configuracion_corrida.json, la configuración elegida es num_iterations 1000, num_leaves 103 y min_sum_hessian_in_leaf 9.311090875055461. (`notebooks/19_Modelo_Final.ipynb` líneas 464–506; `registro/configuracion_corrida.json` líneas 472–476)
11. **Validación en 202106 con diez semillas.** Con la configuración elegida entrena un modelo por semilla con 202103–202104 y mide en 202106 AUC, ganancia con umbral y ganancia por corte; también evalúa el promedio de las 10 probabilidades. Guarda las tablas y la configuración de la corrida con las versiones instaladas. (`notebooks/19_Modelo_Final.ipynb` líneas 512–553)
12. **Entrenamiento final con 202103–202106 y predicción de 202108.** Para cada una de las 10 semillas entrena con las filas con clase de 202103–202106, guarda el modelo, predice 202108 y escribe el ranking con probabilidades y un CSV de IDs por cada uno de los 11 cortes. (`notebooks/19_Modelo_Final.ipynb` líneas 559–594)
13. **Promedio de las diez semillas y archivos por corte.** Lee los 10 rankings, verifica que tengan los mismos clientes, promedia las probabilidades con pesos iguales y ordena por probabilidad descendente e ID ascendente. Escribe el ranking promedio y un CSV de IDs sin encabezado para cada corte entre 10.000 y 15.000, y registra como CSV final el del corte CORTE_FINAL. (`notebooks/19_Modelo_Final.ipynb` líneas 600–735)
14. **Corte del envío y comparación con un CSV de referencia.** La notebook marca como final el archivo del corte 13000. El README indica como envío final el corte de 12.500 (envío 'sofia13', ganancia pública 101,4200 según el README) y registro/envio_final.json identifica el archivo …_top12500.csv con 12.500 filas (submit 'sofia9', public_gain 100.43). La última celda compara clientes, orden y bytes del CSV final contra CSV_REFERENCIA si ese archivo existe. (`notebooks/19_Modelo_Final.ipynb` líneas 61–64; `notebooks/19_Modelo_Final.ipynb` líneas 741–754; `README.md` líneas 3–3; `README.md` líneas 44–58; `registro/envio_final.json` líneas 1–8; `registro/configuracion_corrida.json` líneas 587–587)

## Archivos

- `requirements.txt` · configuracion · Texto · 6 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/sgonzalezr96/requirements.txt.txt) — Seis paquetes con versión exacta: pandas 3.0.6, numpy 2.5.3, lightgbm 4.7.0, optuna 5.0.0, duckdb 1.5.5 e ipykernel 7.3.0.
- `README.md` · explicacion · Markdown · 70 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/sgonzalezr96/README.md.txt) — Presenta la entrega: modelo final de la notebook 19, ensamble de diez semillas y corte de 12.500; declara el envío 'sofia13' con ganancia pública 101,4200 reportada por el bot. Explica la preparación del target desde el archivo crudo, los pasos de ejecución, el método (calidad de datos, variables históricas, canaritos, búsqueda, semillas y corte), la verificación contra el CSV enviado con su SHA256 y el contenido de cada carpeta. Menciona un .gitignore; ese archivo no figura entre los archivos del repositorio.
- `registro/envio_final.json` · configuracion · JSON · 8 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/sgonzalezr96/registro/envio_final.json.txt) — Identificación de un envío: submit 'sofia9', batch_id, public_gain 100.43, nombre del archivo SofiaCerca19Ensamble_20261011_162005_top12500.csv, su SHA256 y 12.500 filas.
- `registro/configuracion_historia.json` · configuracion · JSON · 10 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/sgonzalezr96/registro/configuracion_historia.json.txt) — Firma del cálculo de tendencia y promedio: versión 'ventana3_filas_originales_maxabs_v1', ruta, tamaño (581.933.884 bytes) y fecha de modificación del CSV original, y las dos variables excluidas (cprestamos_personales y mprestamos_personales). Tiene las mismas claves que el configuracion.json que la notebook 19 escribe en la carpeta historia_<clave>.
- `registro/features_seleccionadas.json` · configuracion · JSON · 402 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/sgonzalezr96/registro/features_seleccionadas.json.txt) — Lista de 400 nombres de variables terminadas en _norm_mes: 62 de variables del mes, 10 de lag1, 150 de lag2, 8 de delta1, 150 de delta2, 6 de tend3 y 14 de avg3. Es igual, en contenido y orden, a FEATURES_REFERENCIA de la notebook 19 y a protocolo.features de registro/configuracion_corrida.json.
- `registro/configuracion_corrida.json` · configuracion · JSON · 1140 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/sgonzalezr96/registro/configuracion_corrida.json.txt) — Configuración de una corrida con las claves que la notebook 19 escribe en la carpeta de envíos: protocolo de la búsqueda (meses 202103–202104 y 202106, objetivo auc, parámetros fijos, rangos, semilla 17, 400 variables, versiones de lightgbm y optuna, umbral y valores de ganancia), SHA256 del CSV de variables, firma de la historia, las 10 semillas, mejor_configuracion (num_iterations 1000, num_leaves 103, min_sum_hessian_in_leaf 9.311090875055461), las 10 configuraciones finales (todas del trial 1), meses_final, mes_prediccion, Python 3.14.7 y versiones de paquetes, n_trials 5, corte_final 12500 y 110 archivos candidatos (10 semillas por 11 cortes).
- `notebooks/01_target_sql.ipynb` · principal · Jupyter (python) · 238 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/sgonzalezr96/notebooks/01_target_sql.ipynb.txt) — Notebook con SQL sobre DuckDB (magias %sql) que lee data/competencia_01_crudo.csv, construye clase_ternaria según la presencia del cliente en los dos períodos siguientes y exporta data/competencia_01.csv, el archivo que consume la notebook 19. Según el README se incluye sin modificaciones, como antecedente, y no se volvió a ejecutar. En el archivo original conserva salidas guardadas: la de la celda 9 muestra los meses 202103 a 202108 y la de la celda 19, clases asignadas en 202103–202106 y todas las filas de 202107 y 202108 sin clase.
- `notebooks/19_Modelo_Final.ipynb` · principal · Jupyter (python) · 754 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/sgonzalezr96/notebooks/19_Modelo_Final.ipynb.txt) — Notebook que produce la predicción: a partir de data/competencia_01.csv genera las variables (lags, deltas, tendencia, promedio y normalización por mes), selecciona variables con canaritos, busca hiperparámetros con Optuna, valida en 202106 con 10 semillas, reentrena con 202103–202106 y escribe los CSV de IDs del promedio de las 10 semillas para 11 cortes. En el repositorio no tiene salidas guardadas.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### notebooks/01_target_sql.ipynb

Notebook con SQL sobre DuckDB (magias %sql) que lee data/competencia_01_crudo.csv, construye clase_ternaria según la presencia del cliente en los dos períodos siguientes y exporta data/competencia_01.csv, el archivo que consume la notebook 19. Según el README se incluye sin modificaciones, como antecedente, y no se volvió a ejecutar. En el archivo original conserva salidas guardadas: la de la celda 9 muestra los meses 202103 a 202108 y la de la celda 19, clases asignadas en 202103–202106 y todas las filas de 202107 y 202108 sin clase.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Define la ruta del archivo crudo, ../data/competencia_01_crudo.csv, la imprime y
#   muestra si el archivo existe.
#%% celda 1 [código]
from pathlib import Path

dataset_path = Path("../data")
dataset_filename = "competencia_01_crudo.csv"

file_path = dataset_path / dataset_filename

print(file_path)

#%% celda 2 [código]
print(file_path.exists())

# [Anotación · líneas 14–29] Importa duckdb y pandas, carga la extensión de SQL para notebooks (%load_ext
#   sql), configura que las consultas devuelvan DataFrames de pandas sin mensajes de estado y abre, en dos
#   celdas seguidas, la conexión a una base DuckDB en memoria (duckdb:///).
#%% celda 3 [código]
import duckdb
import pandas as pd

#%% celda 4 [código]
%load_ext sql

#%% celda 5 [código]
%config SqlMagic.autopandas = True
%config SqlMagic.feedback = False
%config SqlMagic.displaycon = False

%sql duckdb:///

#%% celda 6 [código]
%sql duckdb:///

# [Anotación · líneas 31–48] Carga el CSV crudo en la tabla competencia_01_crudo con read_csv_auto, muestra 5
#   filas y cuenta las filas por foto_mes.
#%% celda 7 [código]
%%sql
CREATE OR REPLACE TABLE competencia_01_crudo AS
SELECT *
FROM read_csv_auto('../data/competencia_01_crudo.csv');

#%% celda 8 [código]
%sql SELECT * FROM competencia_01_crudo LIMIT 5

#%% celda 9 [código]
%%sql

SELECT
    foto_mes,
    COUNT(*) AS cantidad
FROM competencia_01_crudo
GROUP BY foto_mes
ORDER BY foto_mes;

# [Anotación · líneas 50–96] Consultas de exploración sobre clientes puntuales: para el cliente 12159854
#   muestra mrentabilidad por mes y, con LEAD y LAG, sus valores uno y dos meses adelante y atrás; para el
#   cliente 60112254 lista los meses en los que aparece.
#%% celda 10 [código]
%%sql

SELECT
    numero_de_cliente,
    foto_mes,
    mrentabilidad
FROM competencia_01_crudo
WHERE numero_de_cliente = 12159854
ORDER BY foto_mes;

#%% celda 11 [código]
%%sql

SELECT
    numero_de_cliente,
    foto_mes,
    mrentabilidad,
    LEAD(mrentabilidad, 1) OVER (
        PARTITION BY numero_de_cliente
        ORDER BY foto_mes
    ) AS mrentabilidad_mas_1,
    LAG(mrentabilidad, 1) OVER (
        PARTITION BY numero_de_cliente
        ORDER BY foto_mes
    ) AS mrentabilidad_menos_1,
    LEAD(mrentabilidad, 2) OVER (
        PARTITION BY numero_de_cliente
        ORDER BY foto_mes
    ) AS mrentabilidad_mas_2,
    LAG(mrentabilidad, 2) OVER (
        PARTITION BY numero_de_cliente
        ORDER BY foto_mes
    ) AS mrentabilidad_menos_2
FROM competencia_01_crudo
WHERE numero_de_cliente = 12159854
ORDER BY foto_mes;

#%% celda 12 [código]
%%sql

SELECT
    numero_de_cliente,
    foto_mes
FROM competencia_01_crudo
WHERE numero_de_cliente = 60112254
ORDER BY foto_mes;

# [Anotación · líneas 98–143] Arma la grilla de todos los clientes por todos los períodos (CROSS JOIN de
#   clientes distintos y foto_mes distintos) y la muestra para el cliente 60112254. Luego la une con la tabla
#   cruda (LEFT JOIN) y marca mes_0 = 1 si el cliente está presente en ese mes y 0 si no.
#%% celda 13 [código]
%%sql

WITH periodos AS (
    SELECT DISTINCT foto_mes
    FROM competencia_01_crudo
),
clientes AS (
    SELECT DISTINCT numero_de_cliente
    FROM competencia_01_crudo
)
SELECT
    numero_de_cliente,
    foto_mes
FROM clientes
CROSS JOIN periodos
WHERE numero_de_cliente = 60112254
ORDER BY foto_mes;

#%% celda 14 [código]
%%sql

WITH periodos AS (
    SELECT DISTINCT foto_mes
    FROM competencia_01_crudo
),
clientes AS (
    SELECT DISTINCT numero_de_cliente
    FROM competencia_01_crudo
),
todo AS (
    SELECT
        numero_de_cliente,
        foto_mes
    FROM clientes
    CROSS JOIN periodos
)
SELECT
    t.numero_de_cliente,
    t.foto_mes,
    IF(c.numero_de_cliente IS NULL, 0, 1) AS mes_0
FROM todo t
LEFT JOIN competencia_01_crudo c
    USING (numero_de_cliente, foto_mes)
WHERE t.numero_de_cliente = 60112254
ORDER BY foto_mes;

# [Anotación · líneas 145–190] Crea la tabla competencia_01. Sobre la grilla calcula mes_0 (presencia en el
#   mes) y, con LEAD por cliente ordenado por foto_mes, mes_1 y mes_2 (presencia en los dos períodos
#   siguientes). Asigna clase_ternaria: CONTINUA si mes_1 = 1 y mes_2 = 1; BAJA+2 si mes_1 = 1 y mes_2 = 0;
#   BAJA+1 si mes_1 = 0 y mes_2 = 0; NULL en cualquier otro caso. Conserva sólo las filas con mes_0 = 1 y quita
#   las tres columnas auxiliares.
#%% celda 15 [código]
%%sql

CREATE OR REPLACE TABLE competencia_01 AS

WITH periodos AS (
    SELECT DISTINCT foto_mes
    FROM competencia_01_crudo
),
clientes AS (
    SELECT DISTINCT numero_de_cliente
    FROM competencia_01_crudo
),
todo AS (
    SELECT
        numero_de_cliente,
        foto_mes
    FROM clientes
    CROSS JOIN periodos
),
clase_ternaria AS (
    SELECT
        c.*,
        IF(c.numero_de_cliente IS NULL, 0, 1) AS mes_0,
        LEAD(mes_0, 1) OVER (
            PARTITION BY t.numero_de_cliente
            ORDER BY foto_mes
        ) AS mes_1,
        LEAD(mes_0, 2) OVER (
            PARTITION BY t.numero_de_cliente
            ORDER BY foto_mes
        ) AS mes_2,
        CASE
            WHEN mes_1 = 1 AND mes_2 = 1 THEN 'CONTINUA'
            WHEN mes_1 = 1 AND mes_2 = 0 THEN 'BAJA+2'
            WHEN mes_1 = 0 AND mes_2 = 0 THEN 'BAJA+1'
            ELSE NULL
        END AS clase_ternaria
    FROM todo t
    LEFT JOIN competencia_01_crudo c
        USING (numero_de_cliente, foto_mes)
)
SELECT
    * EXCLUDE (mes_0, mes_1, mes_2)
FROM clase_ternaria
WHERE mes_0 = 1;

# [Anotación · líneas 192–231] Consultas de control: clase_ternaria por mes del cliente 60112254, cantidad
#   total de filas y dos tablas PIVOT con la cantidad de clientes por clase y foto_mes, la segunda contando los
#   NULL como 'SIN_TARGET'.
#%% celda 16 [código]
%%sql

SELECT
    numero_de_cliente,
    foto_mes,
    clase_ternaria
FROM competencia_01
WHERE numero_de_cliente = 60112254
ORDER BY foto_mes;

#%% celda 17 [código]
%sql SELECT COUNT(*) AS cantidad FROM competencia_01

#%% celda 18 [código]
%%sql

PIVOT competencia_01
ON clase_ternaria
USING COUNT(numero_de_cliente)
GROUP BY foto_mes
ORDER BY foto_mes;

#%% celda 19 [código]
%%sql

PIVOT (
    SELECT
        foto_mes,
        numero_de_cliente,
        CASE
            WHEN clase_ternaria IS NULL THEN 'SIN_TARGET'
            ELSE clase_ternaria
        END AS clase_ternaria
    FROM competencia_01
)
ON clase_ternaria
USING COUNT(numero_de_cliente)
GROUP BY foto_mes
ORDER BY foto_mes;

# [Anotación · líneas 233–238] Exporta la tabla competencia_01 a ../data/competencia_01.csv en formato CSV con
#   encabezado.
#%% celda 20 [código]
%%sql

COPY competencia_01
TO '../data/competencia_01.csv'
(FORMAT CSV, HEADER);
```

### notebooks/19_Modelo_Final.ipynb

Notebook que produce la predicción: a partir de data/competencia_01.csv genera las variables (lags, deltas, tendencia, promedio y normalización por mes), selecciona variables con canaritos, busca hiperparámetros con Optuna, valida en 202106 con 10 semillas, reentrena con 202103–202106 y escribe los CSV de IDs del promedio de las 10 semillas para 11 cortes. En el repositorio no tiene salidas guardadas.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Celda de texto de presentación. Indica que la notebook parte de
#   data/competencia_01.csv y se ejecuta en un kernel nuevo, y enumera las etapas: lags, deltas y normalización
#   por máximo absoluto; tendencia y promedio de tres observaciones; canaritos; búsqueda con cinco trials;
#   validación con diez semillas; reentrenamiento con marzo–junio para predecir agosto. Nombra como referencia
#   el archivo SofiaCerca19Ensamble_20261011_162005_top13000.csv con resultado público 101,4200 y señala que el
#   cambio respecto de 'la 18' es el rango de árboles 1000–2000 en pasos de 100.
#%% celda 1 [texto]
# 19. Explorar alrededor de 1500 árboles, paso 100

Parte de `data/competencia_01.csv`. Ejecutar en un kernel nuevo. Reconstruye lags/deltas y normalización por máximo absoluto; agrega tendencia y promedio de tres observaciones; ejecuta canaritos; busca hiperparámetros con cinco trials; valida diez semillas y reentrena con marzo–junio para predecir agosto.

No agrega flags cero. No lee la base Optuna, modelos, datasets FE ni selecciones de otras corridas. Usa el rango de árboles 1000–2000 en pasos de 100. Se mantienen parámetros fijos, sin undersampling y semilla 17 de búsqueda. Con cinco trials, TPE predeterminado realiza su fase inicial aleatoria; se conserva esa configuración para repetir la experimentación real.

Referencia: `SofiaCerca19Ensamble_20261011_162005_top13000.csv`, resultado público 101,4200. La coincidencia no está verificada: se debe comparar el CSV generado contra el original. La lista anterior de 400 variables se incorpora únicamente para auditar la selección nueva, no para reemplazarla. Tampoco se fijan los hiperparámetros ganadores: salen de Optuna.

Colocar opcionalmente el CSV ganador en `referencia/SofiaHist3Ensamble_20261010_203913_top12500.csv` para comparar clientes, orden y bytes al final. Los nombres y fechas de los nuevos archivos serán distintos.

Experimento nuevo: único cambio en búsqueda respecto a la 18, rango y paso de árboles. Hojas (8–128) y Hessian (0,1–100, log) conservan sus rangos originales. No fija esos dos hiperparámetros alrededor del ganador. Con 5 trials no recorre todas las cantidades de árboles y el sampler permanece en su fase inicial aleatoria. No se espera reproducir el CSV ganador; las comparaciones finales son referencias para medir el cambio. Conservar la 18 como reproducción del candidato ya enviado.

# [Anotación · líneas 14–46] Instala con %pip las versiones fijadas de pandas, numpy, lightgbm, optuna e
#   ipykernel (duckdb sin versión) e importa las librerías. BASE es la primera carpeta, entre la actual y sus
#   superiores, que contiene data/competencia_01.csv. Define los meses (búsqueda 202103–202104, validación
#   202106, final 202103–202106, predicción 202108), N_TRIALS = 5, objetivo 'auc', semilla de búsqueda 17, las
#   10 semillas, los 11 cortes de 10.000 a 15.000 de a 500, el umbral 0,025 y los valores de ganancia (1.072.500
#   por acierto y 27.500 de costo). Dos assert verifican el objetivo y que haya 10 semillas distintas.
#%% celda 2 [código]
%pip install pandas==3.0.6 numpy==2.5.3 lightgbm==4.7.0 optuna==5.0.0 ipykernel==7.3.0 duckdb

#%% celda 3 [código]
from pathlib import Path
from datetime import datetime
import json, hashlib, platform, time
import importlib.metadata as metadata
import pandas as pd
import numpy as np
import lightgbm as lgb
import optuna
from IPython.display import display

BASE = next((p for p in [Path.cwd(), *Path.cwd().parents] if (p / "data" / "competencia_01.csv").is_file()), Path.cwd())
CSV = BASE / "data" / "competencia_01_fe_lags_norm.csv"
CSV_ORIGINAL = BASE / "data" / "competencia_01.csv"
MESES_BUSQUEDA = [202103, 202104]
MES_VALIDACION = 202106
MESES_FINAL = [202103, 202104, 202105, 202106]
MES_PREDICCION = 202108
N_TRIALS = 5
OBJETIVO_OPTUNA = "auc"  # alternativa: "ganancia" con umbral fijo
VERSION_ESTUDIO = "canarios_hist3_rapida_v1"
SEMILLA_BUSQUEDA = 17
SEMILLAS = [17, 103, 211, 307, 401, 503, 601, 701, 809, 907]
N_CONFIGURACIONES_FINAL = 1
CORTES = list(range(10000, 15001, 500))
UMBRAL = 0.025
GANANCIA_ACIERTO = 1_072_500
COSTO_ESTIMULO = 27_500
assert OBJETIVO_OPTUNA in ["auc", "ganancia"]
assert len(SEMILLAS) == len(set(SEMILLAS)) == 10
# [Anotación · líneas 47–56] Parámetros de LightGBM que no se buscan: objective binary, metric auc, max_bin
#   31, min_data_in_leaf 0, feature_fraction 0,50, feature_fraction_bynode 0,20, learning_rate 0,005,
#   deterministic y force_col_wise en True y todos los hilos. RANGOS fija los intervalos de búsqueda:
#   num_iterations 1000–2000 con paso 100, num_leaves 8–128 y min_sum_hessian_in_leaf 0,1–100.
PARAMETROS_FIJOS = {
    "objective": "binary", "metric": "auc", "max_bin": 31,
    "min_data_in_leaf": 0, "feature_fraction": 0.50,
    "feature_fraction_bynode": 0.20, "learning_rate": 0.005,
    "verbosity": -1, "num_threads": -1,
    "deterministic": True, "force_col_wise": True,
}
# No bagging ni undersampling. Cambia la selección de variables por semilla.
RANGOS = {"num_iterations": [1000, 2000, 100],
          "num_leaves": [8, 128], "min_sum_hessian_in_leaf": [0.1, 100.0]}
# [Anotación · líneas 57–64] Crea una carpeta de salida nueva, resultados/exploracion19_<fecha y hora con
#   microsegundos> (con exist_ok=False, da error si ya existe), y apunta CSV al dataset de variables que se
#   escribirá dentro de ella. Fija CORTE_FINAL = 13000, verifica que exista el CSV original y define
#   CSV_REFERENCIA como referencia/SofiaHist3Ensamble_20261010_203913_top12500.csv.
# Carpeta exclusiva: evita reutilización de cachés o estudios anteriores.
SALIDA = BASE / "resultados" / ("exploracion19_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
SALIDA.mkdir(parents=True, exist_ok=False)
CSV = SALIDA / "competencia_01_fe_lags_norm.csv"
CORTE_FINAL = 13000
assert CSV_ORIGINAL.is_file(), f"Falta {CSV_ORIGINAL}"

CSV_REFERENCIA = BASE / "referencia" / "SofiaHist3Ensamble_20261010_203913_top12500.csv"

# [Anotación · líneas 66–91] Abre una base DuckDB en la subcarpeta fe/ de la salida (features.duckdb) con
#   límite de memoria de 8 GB, 2 hilos y sin preservar el orden de inserción. Define NORMALIZAR_HISTORICOS =
#   True (se normalizan también lags y deltas) y dos funciones auxiliares, qi y qs, que ponen comillas a
#   identificadores y a textos para armar el SQL. Verifica que la entrada exista y que no sea el mismo archivo
#   que la salida.
#%% celda 4 [texto]
## 1. Reconstruir lags, deltas y normalización desde el original

#%% celda 5 [código]
from pathlib import Path
import duckdb
import json
from IPython.display import display
BASE = BASE
ENTRADA = BASE / "data" / "competencia_01.csv"
SALIDA_FE = CSV
TRABAJO = SALIDA / "fe"
TRABAJO.mkdir(parents=True, exist_ok=True)
# True: normalizar también lags y deltas. False: normalizar solo originales.
NORMALIZAR_HISTORICOS = True
assert ENTRADA.exists(), f"No existe {ENTRADA}"
assert ENTRADA.resolve() != SALIDA_FE.resolve()
def qi(nombre): return '"' + nombre.replace('"', '""') + '"'
def qs(texto): return "'" + str(texto).replace("'", "''") + "'"
con = duckdb.connect(str(TRABAJO / "features.duckdb"))
con.execute("SET memory_limit='8GB'")
con.execute("SET threads=2")
con.execute("SET preserve_insertion_order=false")
print('DuckDB:', duckdb.__version__)
print('Entrada:', ENTRADA)


# [Anotación · líneas 93–106] Carga data/competencia_01.csv completo en la tabla raw (read_csv_auto con
#   sample_size=-1). Verifica que existan numero_de_cliente, foto_mes y clase_ternaria, que no haya claves nulas
#   ni pares cliente-mes duplicados y que el mes esté entre 1 y 12. Arma la lista de variables: columnas de tipo
#   numérico o booleano, sin numero_de_cliente, foto_mes ni las que empiezan con 'clase'. Muestra la cantidad de
#   filas por mes.
con.execute(f"CREATE OR REPLACE TABLE raw AS SELECT * FROM read_csv_auto({qs(ENTRADA)}, sample_size=-1)")
esquema = con.execute("DESCRIBE raw").fetchall()
columnas = [r[0] for r in esquema]
assert {'numero_de_cliente', 'foto_mes', 'clase_ternaria'} <= set(columnas)
assert con.execute('SELECT count(*) FROM raw WHERE numero_de_cliente IS NULL OR foto_mes IS NULL').fetchone()[0] == 0
assert con.execute('SELECT count(*) FROM (SELECT numero_de_cliente, foto_mes FROM raw GROUP BY ALL HAVING count(*)>1)').fetchone()[0] == 0, 'Claves cliente-mes duplicadas'
assert con.execute('SELECT count(*) FROM raw WHERE foto_mes % 100 NOT BETWEEN 1 AND 12').fetchone()[0] == 0
numeric_types = ('TINYINT', 'SMALLINT', 'INTEGER', 'BIGINT', 'HUGEINT', 'UTINYINT', 'USMALLINT', 'UINTEGER', 'UBIGINT', 'FLOAT', 'DOUBLE', 'DECIMAL', 'BOOLEAN')
variables = [nombre for nombre, tipo, *_ in esquema
             if tipo.startswith(numeric_types)
             and nombre not in ('numero_de_cliente', 'foto_mes')
             and not nombre.lower().startswith('clase')]
print('Predictores numéricos:', len(variables))
display(con.execute('SELECT foto_mes, count(*) AS filas FROM raw GROUP BY foto_mes ORDER BY foto_mes').df())


# [Anotación · líneas 109–122] Crea la tabla base: cada variable de la lista se convierte a DOUBLE y los
#   valores no finitos pasan a NULL; ccajas_depositos queda en NULL para foto_mes 202105. Agrega _mes_idx = año
#   × 12 + mes, un índice de mes consecutivo. Muestra cuántos valores no nulos de ccajas_depositos hay por mes.
limpias = []
for nombre in columnas:
    q = qi(nombre)
    if nombre in variables:
        expr = f"CASE WHEN isfinite(CAST({q} AS DOUBLE)) THEN CAST({q} AS DOUBLE) ELSE NULL END"
        if nombre == 'ccajas_depositos':
            expr = f"CASE WHEN foto_mes=202105 THEN NULL ELSE {expr} END"
        limpias.append(f"{expr} AS {q}")
    else:
        limpias.append(q)
con.execute('CREATE OR REPLACE TABLE base AS SELECT ' + ', '.join(limpias) +
            ', CAST(floor(foto_mes / 100) AS INTEGER)*12 + CAST(foto_mes % 100 AS INTEGER) AS _mes_idx FROM raw')
if 'ccajas_depositos' in columnas:
    display(con.execute('SELECT foto_mes, count(ccajas_depositos) AS valores_no_nulos FROM base GROUP BY foto_mes ORDER BY foto_mes').df())


# [Anotación · líneas 125–145] Baja DuckDB a 1 hilo. Para cada variable y para k = 1 y 2 define
#   <variable>_lag<k> (valor del mismo cliente k meses calendario antes) y <variable>_delta<k> (valor actual
#   menos ese lag). La tabla historia se arma uniendo base consigo misma dos veces (LEFT JOIN por cliente y
#   _mes_idx − 1 y − 2); si el mes anterior no existe, lag y delta quedan en NULL. Verifica que no cambie la
#   cantidad de filas.
con.execute("SET memory_limit='8GB'")
con.execute("SET threads=1")
con.execute("SET preserve_insertion_order=false")

historicas = []
expresiones = []
for v in variables:
    q = qi(v)
    for k in (1, 2):
        lag, delta = f'{v}_lag{k}', f'{v}_delta{k}'
        historicas.extend([lag, delta])
        expresiones.extend([f'p{k}.{q} AS {qi(lag)}',
                            f'b.{q} - p{k}.{q} AS {qi(delta)}'])
assert not set(historicas) & set(columnas), 'El archivo ya tiene nombres de features históricos'
seleccion = ', '.join(['b.' + qi(c) for c in columnas] + expresiones)
con.execute(f"""CREATE OR REPLACE TABLE historia AS
SELECT {seleccion} FROM base b
LEFT JOIN base p1 ON b.numero_de_cliente=p1.numero_de_cliente AND p1._mes_idx=b._mes_idx-1
LEFT JOIN base p2 ON b.numero_de_cliente=p2.numero_de_cliente AND p2._mes_idx=b._mes_idx-2""")
assert con.execute('SELECT count(*) FROM historia').fetchone()[0] == con.execute('SELECT count(*) FROM raw').fetchone()[0]
print('Lags y deltas creados:', len(historicas))


# [Anotación · líneas 148–161] Normalización por mes: para cada variable original, lag y delta calcula el
#   máximo del valor absoluto dentro de cada foto_mes (tabla maximos) y crea <nombre>_norm_mes = valor / máximo;
#   NULL se mantiene y, si el máximo es 0, el resultado es 0. La tabla features contiene las columnas
#   originales, las históricas y las normalizadas. Imprime la cantidad de columnas de cada grupo.
a_normalizar = variables + (historicas if NORMALIZAR_HISTORICOS else [])
normalizadas = [v + '_norm_mes' for v in a_normalizar]
assert not set(normalizadas) & (set(columnas) | set(historicas))
# Cada denominador corresponde a UNA variable y UN mes, no a toda la fila.
maximos = ', '.join(f'max(abs({qi(v)})) AS {qi(v)}' for v in a_normalizar)
con.execute(f'CREATE OR REPLACE TABLE maximos AS SELECT foto_mes, {maximos} FROM historia GROUP BY foto_mes')
expr_norm = []
for v, salida in zip(a_normalizar, normalizadas):
    q = qi(v)
    expr_norm.append(f"CASE WHEN h.{q} IS NULL THEN NULL WHEN m.{q}=0 THEN 0 ELSE h.{q}/m.{q} END AS {qi(salida)}")
con.execute('CREATE OR REPLACE TABLE features AS SELECT h.*, ' + ', '.join(expr_norm) +
            ' FROM historia h JOIN maximos m ON h.foto_mes=m.foto_mes')
print('Originales:', len(columnas), '| Históricas:', len(historicas), '| Normalizadas:', len(normalizadas))
print('Total de columnas:', len(columnas) + len(historicas) + len(normalizadas))


# [Anotación · líneas 164–174] Cuenta, para cada columna normalizada, los valores con valor absoluto mayor que
#   1,000000001 y exige que no haya ninguno. Muestra 12 filas de ejemplo con las dos primeras variables y sus
#   lags, deltas y versión normalizada.
# Controlar que todas las normalizadas estén dentro del rango permitido.
checks = ', '.join(f'count(*) FILTER (WHERE abs({qi(v)}) > 1.000000001) AS {qi(v)}' for v in normalizadas)
fuera_de_rango = con.execute('SELECT ' + checks + ' FROM features').fetchone()
assert sum(fuera_de_rango) == 0
muestra = variables[:2]
campos = ['numero_de_cliente', 'foto_mes']
for v in muestra:
    campos += [v, v+'_lag1', v+'_lag2', v+'_delta1', v+'_delta2', v+'_norm_mes']
display(con.execute('SELECT ' + ', '.join(map(qi, campos)) +
                    ' FROM features ORDER BY numero_de_cliente, foto_mes LIMIT 12').df())
print('Controles correctos. No se reemplazaron lags faltantes por cero.')


# [Anotación · líneas 177–188] Exporta la tabla features ordenada por cliente y mes a
#   competencia_01_fe_lags_norm.csv dentro de la carpeta de salida y escribe fe/config_fe.json con la entrada,
#   la salida, la versión de DuckDB, las listas de variables y la descripción de la corrección, el lag, el delta
#   y la normalización. Imprime el tamaño del archivo y cierra la conexión.
SALIDA_FE.parent.mkdir(parents=True, exist_ok=True)
con.execute(f"COPY (SELECT * FROM features ORDER BY numero_de_cliente, foto_mes) TO {qs(SALIDA_FE)} (HEADER, DELIMITER ',')")
manifest = dict(entrada=str(ENTRADA), salida=str(SALIDA_FE),
                duckdb_version=duckdb.__version__, normalizar_historicos=NORMALIZAR_HISTORICOS,
                variables=variables, historicas=historicas, normalizadas=normalizadas,
                correccion='ccajas_depositos=NA en 202105',
                lag='mes calendario exacto', delta='actual menos lag',
                normalizacion='valor / max(abs(valor)) por variable y foto_mes')
(TRABAJO / 'config_fe.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
print('Dataset listo:', SALIDA_FE)
print('Tamaño GB:', round(SALIDA_FE.stat().st_size / 1e9, 3))
con.close()

# [Anotación · líneas 190–202] Lee el encabezado del CSV de variables y elige las columnas a cargar: las
#   terminadas en _norm_mes más numero_de_cliente, foto_mes, clase_ternaria y ccajas_depositos, descartando
#   cprestamos_personales, mprestamos_personales y todas sus derivadas (nombres que empiezan con esas variables
#   seguidas de '_'). Lee el archivo en bloques de 10.000 filas como float32 y conserva sólo los meses
#   202103–202106 y 202108.
#%% celda 6 [código]
assert CSV.is_file(), f"No encuentro {CSV}"
columnas = pd.read_csv(CSV, nrows=0).columns.tolist()
excluir = lambda c: any(c == v or c.startswith(v+'_') for v in ['cprestamos_personales','mprestamos_personales'])
columnas = [c for c in columnas if not excluir(c) and (c.endswith("_norm_mes") or c in ["numero_de_cliente", "foto_mes", "clase_ternaria", "ccajas_depositos"])]
assert any(c.endswith("_norm_mes") for c in columnas), "El CSV debe ser el dataset de FE con columnas _norm_mes"
tipos = {c:'float32' for c in columnas if c not in ['numero_de_cliente','foto_mes','clase_ternaria'] and not c.startswith('clase_')}
partes = []
for chunk in pd.read_csv(CSV, usecols=columnas, dtype=tipos, chunksize=10000, low_memory=True):
    partes.append(chunk.loc[chunk.foto_mes.isin(MESES_FINAL+[MES_PREDICCION])].copy())
data = pd.concat(partes, ignore_index=True)
del partes, chunk
print('Préstamos personales y derivados excluidos en TODAS las etapas.')
# [Anotación · líneas 203–222] Verifica columnas obligatorias, claves sin nulos ni duplicados y presencia de
#   los cinco meses; convierte foto_mes a entero y quita espacios de clase_ternaria. Muestra los valores de
#   ccajas_depositos de 202105, pone en NaN ccajas_depositos y ccajas_depositos_norm_mes de ese mes y elimina la
#   columna sin normalizar. La lista features queda formada por todas las columnas terminadas en _norm_mes, que
#   se verifican numéricas.
CLASES = ["CONTINUA", "BAJA+1", "BAJA+2"]
assert {"numero_de_cliente", "foto_mes", "clase_ternaria", "ccajas_depositos"} <= set(data.columns)
assert not data[["numero_de_cliente", "foto_mes"]].isna().any().any()
data["foto_mes"] = pd.to_numeric(data["foto_mes"], errors="raise").astype(int)
data["clase_ternaria"] = data["clase_ternaria"].astype("string").str.strip()
assert not data.duplicated(["numero_de_cliente", "foto_mes"]).any(), "Duplicados cliente–mes"
assert set(MESES_FINAL + [MES_PREDICCION]).issubset(data.foto_mes.unique())
print("ccajas_depositos de mayo antes de corregir:")
print(data.loc[data.foto_mes == 202105, "ccajas_depositos"].value_counts(dropna=False).head())
data.loc[data.foto_mes == 202105, "ccajas_depositos"] = np.nan
if "ccajas_depositos_norm_mes" in data.columns:
    data.loc[data.foto_mes == 202105, "ccajas_depositos_norm_mes"] = np.nan
# La columna original se leyó solo para auditar calidad; no entra al modelo.
data.drop(columns=["ccajas_depositos"], inplace=True)
features = [c for c in data.columns if c.endswith("_norm_mes")]
assert features and all(not excluir(c) for c in features)
print("Solo predictores normalizados:", len(features))
print("Ejemplos:", features[:12])
no_numericas = data[features].select_dtypes(exclude=["number", "bool"]).columns.tolist()
assert not no_numericas, f"Revisar columnas no numéricas: {no_numericas}"
# [Anotación · líneas 223–232] Arma entrenamiento (202103 y 202104) y validación (202106) con las filas cuya
#   clase es CONTINUA, BAJA+1 o BAJA+2 y reemplaza ±infinito por NaN. La etiqueta vale 1 si clase_ternaria es
#   BAJA+2 y 0 en otro caso. Verifica que ambas particiones tengan las dos etiquetas y que validación tenga al
#   menos 15.000 filas; muestra la tabla de clases por mes del entrenamiento.
train = data[data.foto_mes.isin(MESES_BUSQUEDA) & data.clase_ternaria.isin(CLASES)].copy()
valid = data[(data.foto_mes == MES_VALIDACION) & data.clase_ternaria.isin(CLASES)].copy()
X_train = train[features].replace([np.inf, -np.inf], np.nan)
X_valid = valid[features].replace([np.inf, -np.inf], np.nan)
y_train = (train.clase_ternaria == "BAJA+2").astype(int).to_numpy()
y_valid = (valid.clase_ternaria == "BAJA+2").astype(int).to_numpy()
assert len(np.unique(y_train)) == len(np.unique(y_valid)) == 2
assert len(valid) >= max(CORTES)
print("Train:", len(train), "Validación:", len(valid), "Variables:", len(features))
display(pd.crosstab(train.foto_mes, train.clase_ternaria))

# [Anotación · líneas 234–257] Función estadisticas_tres: recibe el valor actual y los dos anteriores, los
#   ubica en x = 1, 2 y 3 y cuenta cuántos son finitos. Devuelve la pendiente de la recta de mínimos cuadrados y
#   el promedio de los valores válidos, ambos sólo cuando hay al menos 2 valores válidos (y denominador positivo
#   en el caso de la pendiente); en otro caso devuelve NaN.
#%% celda 7 [texto]
## Historia nueva desde el CSV original (incluye julio)
Calcula tendencia y promedio, los normaliza y los agrega al dataset existente.

#%% celda 8 [código]
import gc
assert CSV_ORIGINAL.is_file(), f"No encuentro {CSV_ORIGINAL}"
# Cálculo vectorizado equivalente a fhistC para ventana de tres filas.
def estadisticas_tres(a, anterior1, anterior2):
    y = np.stack([anterior2, anterior1, a]).astype(np.float64)
    ok = np.isfinite(y)
    x = np.array([1., 2., 3.])[:, None]
    n = ok.sum(axis=0)
    limpio = np.where(ok, y, 0.)
    sy = limpio.sum(axis=0)
    sx = (ok * x).sum(axis=0)
    sxx = (ok * x*x).sum(axis=0)
    sxy = (limpio * x).sum(axis=0)
    denom = n*sxx - sx*sx
    avg = np.full(len(a), np.nan)
    tend = np.full(len(a), np.nan)
    np.divide(sy, n, out=avg, where=n >= 2)
    np.divide(n*sxy - sx*sy, denom, out=tend, where=(n >= 2) & (denom > 0))
    return tend.astype("float32"), avg.astype("float32")

# [Anotación · líneas 259–269] Arma una firma con la versión del cálculo, la ruta, el tamaño y la fecha de
#   modificación del CSV original y las dos variables excluidas; con los primeros 16 caracteres de su SHA256
#   nombra la carpeta historia_<clave>. Si allí ya existe historia3.pkl, lo lee en lugar de recalcular.
firma_hist = {"version": "ventana3_filas_originales_maxabs_v1",
    "original": str(CSV_ORIGINAL.resolve()), "bytes": CSV_ORIGINAL.stat().st_size,
    "mtime": CSV_ORIGINAL.stat().st_mtime_ns,
    "excluir": ["cprestamos_personales", "mprestamos_personales"]}
clave_hist = hashlib.sha256(json.dumps(firma_hist, sort_keys=True).encode()).hexdigest()[:16]
HIST_DIR = SALIDA / f"historia_{clave_hist}"
HIST_DIR.mkdir(exist_ok=True)
CACHE_HIST = HIST_DIR / "historia3.pkl"
if CACHE_HIST.is_file():
    historia = pd.read_pickle(CACHE_HIST)
    print("Historia recuperada:", CACHE_HIST, flush=True)
# [Anotación · líneas 270–285] Si no hay caché: lee del CSV original todas las columnas salvo préstamos
#   personales, sus derivadas y las que empiezan con 'clase_' (como float32), verifica que no haya duplicados,
#   ordena por cliente y mes y pone en NaN ccajas_depositos de 202105. Construye dos máscaras que indican si la
#   fila anterior y la de dos posiciones atrás pertenecen al mismo cliente.
else:
    cols_raw = pd.read_csv(CSV_ORIGINAL, nrows=0).columns.tolist()
    meta = ["numero_de_cliente", "foto_mes", "clase_ternaria"]
    cols_raw = [c for c in cols_raw if c in meta or (not excluir(c) and not c.startswith("clase_"))]
    tipos_raw = {c: "float32" for c in cols_raw if c not in meta}
    original = pd.read_csv(CSV_ORIGINAL, usecols=cols_raw, dtype=tipos_raw, low_memory=True)
    assert not original.duplicated(["numero_de_cliente", "foto_mes"]).any()
    original = original.sort_values(["numero_de_cliente", "foto_mes"]).reset_index(drop=True)
    original.loc[original.foto_mes == 202105, "ccajas_depositos"] = np.nan
    cols_hist = [c for c in cols_raw if c not in meta]
    cliente = original.numero_de_cliente.to_numpy()
    meses = original.foto_mes
    iguales1 = np.zeros(len(original), dtype=bool)
    iguales2 = np.zeros(len(original), dtype=bool)
    iguales1[1:] = cliente[1:] == cliente[:-1]
    iguales2[2:] = cliente[2:] == cliente[:-2]
# [Anotación · líneas 286–301] Para cada variable: pasa a NaN los no finitos, obtiene los valores de la fila
#   anterior y de dos filas atrás del mismo cliente (NaN si es otro cliente) y calcula tendencia y promedio con
#   estadisticas_tres. Cada resultado se divide por el máximo de su valor absoluto dentro del mes (0 si ese
#   máximo es 0) y se guarda como <variable>_tend3_norm_mes y <variable>_avg3_norm_mes. Informa el avance cada
#   25 variables.
    nuevas = {}
    for i, c in enumerate(cols_hist, 1):
        a = original[c].to_numpy(dtype="float32", copy=True)
        a[~np.isfinite(a)] = np.nan
        a1 = np.roll(a, 1); a1[~iguales1] = np.nan
        a2 = np.roll(a, 2); a2[~iguales2] = np.nan
        tend, avg = estadisticas_tres(a, a1, a2)
        for sufijo, valores in [("tend3", tend), ("avg3", avg)]:
            serie = pd.Series(valores)
            escala = serie.abs().groupby(meses).transform("max").to_numpy()
            norm = np.full(len(serie), np.nan, dtype="float32")
            np.divide(valores, escala, out=norm, where=np.isfinite(escala) & (escala > 0))
            norm[np.isfinite(valores) & (escala == 0)] = 0.
            nuevas[f"{c}_{sufijo}_norm_mes"] = norm
        if i % 25 == 0 or i == len(cols_hist):
            print(f"Historia {i}/{len(cols_hist)}", flush=True)
# [Anotación · líneas 302–310] Une las columnas nuevas con numero_de_cliente y foto_mes y conserva sólo las
#   filas de 202103–202106 y 202108 (202107 interviene como historia de 202108 pero sus filas no se guardan).
#   Graba historia3.pkl mediante un archivo temporal, escribe configuracion.json con la firma y libera memoria.
    historia = pd.concat([original[["numero_de_cliente", "foto_mes"]], pd.DataFrame(nuevas)], axis=1)
    # Julio aporta historia, pero no necesitamos guardar sus filas para entrenar.
    historia = historia[historia.foto_mes.isin(MESES_FINAL + [MES_PREDICCION])].copy()
    temp_hist = CACHE_HIST.with_suffix(".tmp")
    historia.to_pickle(temp_hist)
    temp_hist.replace(CACHE_HIST)
    (HIST_DIR / "configuracion.json").write_text(json.dumps(firma_hist, indent=2), encoding="utf-8")
    del original, nuevas, a, a1, a2, tend, avg
    gc.collect()
# [Anotación · líneas 311–326] Verifica que las columnas nuevas no existan ya en data y que todas las claves
#   cliente-mes de data estén en la historia; une por cliente y mes (uno a uno) y agrega las columnas a
#   features. Rehace entrenamiento, validación, matrices y etiquetas con el conjunto ampliado e imprime la
#   cantidad de variables antes de canaritos.
cols_nuevas = [c for c in historia.columns if c not in ["numero_de_cliente", "foto_mes"]]
assert not set(cols_nuevas) & set(data.columns), "Ya existen features tend3/avg3"
# No mezclar una fila sin historia con una fila ausente del CSV original.
assert pd.MultiIndex.from_frame(data[["numero_de_cliente", "foto_mes"]]).isin(
    pd.MultiIndex.from_frame(historia[["numero_de_cliente", "foto_mes"]])).all()
data = data.merge(historia, on=["numero_de_cliente", "foto_mes"], how="left", validate="one_to_one")
features += cols_nuevas
train = data[data.foto_mes.isin(MESES_BUSQUEDA) & data.clase_ternaria.isin(CLASES)].copy()
valid = data[(data.foto_mes == MES_VALIDACION) & data.clase_ternaria.isin(CLASES)].copy()
X_train = train[features].replace([np.inf, -np.inf], np.nan)
X_valid = valid[features].replace([np.inf, -np.inf], np.nan)
y_train = (train.clase_ternaria == "BAJA+2").astype(int).to_numpy()
y_valid = (valid.clase_ternaria == "BAJA+2").astype(int).to_numpy()
print("Features históricas nuevas:", len(cols_nuevas), "Total antes de canaritos:", len(features))
del historia
gc.collect()

# [Anotación · líneas 328–359] Funciones de evaluación y entrenamiento. auc_score calcula el AUC a partir de
#   los rangos promedio de las probabilidades, sin sklearn. ganancia_umbral suma 1.072.500 por cada BAJA+2 y
#   −27.500 por cada otro caso entre las filas con probabilidad mayor o igual a 0,025. tabla_cortes ordena por
#   probabilidad descendente (desempate por ID ascendente) y devuelve la ganancia acumulada en cada corte.
#   entrenar combina los parámetros fijos con la configuración recibida, asigna la semilla a seed,
#   feature_fraction_seed y data_random_seed y entrena con num_iterations rondas.
#%% celda 9 [texto]
## 2. Funciones de evaluación
AUC se calcula con rangos promedio para empates, sin importar sklearn. La ganancia por corte usa el ranking descendente y desempata por ID.

#%% celda 10 [código]
def auc_score(y, p):
    y = np.asarray(y); p = np.asarray(p, dtype=float)
    assert y.shape == p.shape and np.isfinite(p).all()
    n1 = int((y == 1).sum()); n0 = int((y == 0).sum())
    assert n1 > 0 and n0 > 0
    rangos = pd.Series(p).rank(method="average").to_numpy()
    return float((rangos[y == 1].sum() - n1*(n1+1)/2) / (n1*n0))

def ganancia_umbral(y, p):
    pagos = np.where(np.asarray(y) == 1, GANANCIA_ACIERTO, -COSTO_ESTIMULO)
    return int(pagos[np.asarray(p) >= UMBRAL].sum())

def tabla_cortes(y, p, ids):
    ranking = pd.DataFrame({"id": np.asarray(ids), "p": p,
        "pago": np.where(np.asarray(y) == 1, GANANCIA_ACIERTO, -COSTO_ESTIMULO)})
    ranking = ranking.sort_values(["p", "id"], ascending=[False, True])
    acumulada = ranking.pago.cumsum().to_numpy()
    return pd.DataFrame({"envios": CORTES,
                         "ganancia": [int(acumulada[k-1]) for k in CORTES]})

def entrenar(config, dataset, seed, valid_sets=None):
    config = dict(config)
    arboles = int(config.pop("num_iterations"))
    params = {**PARAMETROS_FIJOS, **config, "seed": int(seed),
              "feature_fraction_seed": int(seed), "data_random_seed": int(seed)}
    return lgb.train(params, dataset, num_boost_round=arboles,
        valid_sets=valid_sets, callbacks=[lgb.log_evaluation(0)])

# [Anotación · líneas 361–388] Parámetros de la selección con canaritos: semilla 17, 1000 árboles, proporción
#   0,20, 31 hojas y min_sum_hessian_in_leaf 10. Arma un protocolo con la firma de la historia, el CSV, las
#   variables, los meses y los parámetros; su hash nombra la carpeta seleccion_<firma>. Si allí existe
#   seleccion.json con el mismo protocolo, toma de él la lista de variables.
#%% celda 11 [texto]
## 3. Selección con canaritos desde cero
Mismos parámetros y criterio de la 13. Sin flags. Se conservan aparte predictores vacíos o constantes.

#%% celda 12 [código]
import gc
CAN_SEED = 17
CAN_ARBOLES = 1000
CAN_PROPORCION = 0.20
CAN_CONFIG = {"num_iterations": CAN_ARBOLES, "num_leaves": 31,
              "min_sum_hessian_in_leaf": 10.0}
features_antes = list(features)
stat_csv = CSV.stat()
clave_can = {"historia": clave_hist, "csv": str(CSV.resolve()), "bytes": stat_csv.st_size,
    "mtime_ns": stat_csv.st_mtime_ns, "features": features_antes,
    "meses": MESES_BUSQUEDA, "config": CAN_CONFIG, "fijos": PARAMETROS_FIJOS,
    "seed": CAN_SEED, "proporcion": CAN_PROPORCION,
    "regla": "gain_rank_median_minus_sample_std_keep_uninformative_v1",
    "lightgbm": lgb.__version__}
firma_can = hashlib.sha256(json.dumps(clave_can, sort_keys=True).encode()).hexdigest()[:16]
CAN_DIR = SALIDA / f"seleccion_{firma_can}"
CAN_DIR.mkdir(exist_ok=True)
CACHE_CAN = CAN_DIR / "seleccion.json"
if CACHE_CAN.is_file():
    resultado_can = json.loads(CACHE_CAN.read_text(encoding="utf-8"))
    assert resultado_can["protocolo"] == clave_can
    features = resultado_can["features"]
    print("Selección recuperada:", CACHE_CAN, flush=True)
# [Anotación · líneas 389–410] Si no hay caché: aparta como 'protegidas' las variables con a lo sumo un valor
#   distinto en entrenamiento y deja el resto como evaluables. Genera max(10, 20 % de las evaluables) columnas
#   de ruido uniforme en [0, 1) con un generador de semilla 17, las agrega a las evaluables y entrena un
#   LightGBM de 1000 rondas con 202103–202104.
else:
    # No se consideran malas las variables que no tienen variación en el train.
    cardinalidad = X_train.nunique(dropna=True)
    protegidas = cardinalidad[cardinalidad <= 1].index.tolist()
    evaluables = [c for c in features_antes if c not in protegidas]
    assert evaluables, "No hay predictores evaluables"
    n_can = max(10, int(np.ceil(len(evaluables) * CAN_PROPORCION)))
    nombres_can = [f"__canarito_{i:04d}" for i in range(n_can)]
    assert not set(nombres_can) & set(features_antes)
    rng = np.random.default_rng(CAN_SEED)
    matriz_can = X_train[evaluables].copy()
    ruido = pd.DataFrame(rng.random((len(matriz_can), n_can), dtype=np.float32),
                         columns=nombres_can, index=matriz_can.index)
    matriz_can = pd.concat([matriz_can, ruido], axis=1)
    del ruido
    print(f"Seleccionando: {len(evaluables)} variables y {n_can} canaritos; {len(protegidas)} protegidas", flush=True)
    parametros_can = {**PARAMETROS_FIJOS, "num_leaves": 31,
        "min_sum_hessian_in_leaf": 10.0, "seed": CAN_SEED,
        "feature_fraction_seed": CAN_SEED, "data_random_seed": CAN_SEED}
    ds_can = lgb.Dataset(matriz_can, label=y_train)
    modelo_can = lgb.train(parametros_can, ds_can, num_boost_round=CAN_ARBOLES,
                          valid_sets=[ds_can], callbacks=[lgb.log_evaluation(100)])
# [Anotación · líneas 411–432] Obtiene la importancia gain de cada columna y las ordena de mayor a menor; en
#   los empates las variables reales quedan antes que los canaritos. El límite es la mediana de las posiciones
#   de los canaritos menos su desvío estándar muestral. Conserva las variables reales con posición menor que el
#   límite más las protegidas, guarda importancias.csv y seleccion.json y libera memoria.
    importancia = pd.DataFrame({"variable": modelo_can.feature_name(),
         "gain": modelo_can.feature_importance(importance_type="gain")})
    importancia["canarito"] = importancia.variable.isin(nombres_can)
    # Empates conservadores: las variables reales preceden a los canaritos.
    importancia = importancia.sort_values(["gain", "canarito", "variable"],
         ascending=[False, True, True]).reset_index(drop=True)
    importancia["posicion"] = np.arange(1, len(importancia) + 1)
    posiciones = importancia.loc[importancia.canarito, "posicion"]
    limite = float(posiciones.median() - posiciones.std(ddof=1))
    candidatas = set(importancia.loc[(~importancia.canarito) &
                         (importancia.posicion < limite), "variable"])
    candidatas.update(protegidas)
    features = [c for c in features_antes if c in candidatas]
    assert features and any(c in features for c in evaluables), "Filtro sin variables evaluables: revisar importancias"
    importancia["conservada"] = importancia.variable.isin(features)
    importancia.to_csv(CAN_DIR / "importancias.csv", index=False)
    resultado_can = {"protocolo": clave_can, "features": features,
        "protegidas": protegidas, "limite_posicion": limite,
        "cantidad_antes": len(features_antes), "cantidad_despues": len(features)}
    CACHE_CAN.write_text(json.dumps(resultado_can, indent=2), encoding="utf-8")
    del modelo_can, ds_can, matriz_can, importancia
    gc.collect()
# [Anotación · líneas 433–445] Imprime cuántas variables quedan y cuántas protegidas hay. Reduce data,
#   entrenamiento y validación a las columnas de identificación y las variables seleccionadas, y crea los
#   Dataset de LightGBM de entrenamiento y validación.
print(f"Features conservadas: {len(features)} / {len(features_antes)}", flush=True)
print("Vacías o constantes conservadas aparte:", len(resultado_can["protegidas"]))
print("Selección guardada en:", CAN_DIR)
# Liberar columnas eliminadas antes de optimizar y entrenar modelos finales.
meta_cols = ["numero_de_cliente", "foto_mes", "clase_ternaria"]
data = data[meta_cols + features].copy()
train = train[meta_cols + features].copy()
valid = valid[meta_cols + features].copy()
X_train = train[features].replace([np.inf, -np.inf], np.nan)
X_valid = valid[features].replace([np.inf, -np.inf], np.nan)
gc.collect()
train_lgb = lgb.Dataset(X_train, label=y_train, free_raw_data=False)
valid_lgb = lgb.Dataset(X_valid, label=y_valid, reference=train_lgb, free_raw_data=False)

# [Anotación · líneas 447–457] FEATURES_REFERENCIA es una lista escrita en el código con las variables de una
#   selección anterior (la línea está recortada en esta copia; en el archivo original tiene 400 nombres).
#   Compara lista y orden con la selección recién calculada, guarda en comparacion_seleccion.json cuáles faltan
#   y cuáles son nuevas e imprime un aviso si difieren; la selección calculada no se reemplaza.
#%% celda 13 [código]
FEATURES_REFERENCIA = ['active_quarter_norm_mes', 'internet_norm_mes', 'cliente_edad_norm_mes', 'cliente_antiguedad_norm_mes', 'mrentabilidad_norm_mes', 'mrentabilidad_annual_norm_mes', 'mcomisiones_norm_mes', 'mactivos_margen_norm_mes', 'mpasivos_margen_norm_mes', 'cproductos_norm_mes', 'mcuenta_corriente_norm_mes', 'mcaja_ahorro_norm_mes', 'mcuentas_saldo_norm_mes', 'ctarjeta_debito_transacciones_norm_mes', 'mautoservicio_norm_mes', 'ctarjeta_visa_norm_mes', 'ctarjeta_visa_transacciones_norm_mes', 'mtarjeta_visa_consumo_norm_mes', 'mtarjeta_master_consumo_norm_mes', 'ccaja_seguridad_norm_mes', 'cpayroll_trx_norm_mes', 'mpayroll_norm_mes', 'ccuenta_debitos_automaticos_norm_mes', 'mcuenta_debitos_automaticos_norm_mes', 'cpagomiscuentas_norm_mes', 'mpagomiscuentas_norm_mes', 'ccomisiones_mantenimiento_norm_mes', 'mcomisiones_mantenimiento_norm_mes', 'ccomisiones_otras_norm_mes', 'mcomisiones_otras_norm_mes', 'ctransferencias_recibidas_norm_mes', 'mtransferencias_recibidas_norm_mes', 'ctransferencias_emitidas_norm_mes', 'mtransferencias_emitidas_norm_mes', 'cextraccion_autoservicio_norm_mes', 'mextraccion_autoservicio_norm_mes', 'chomebanking_transacciones_norm_mes', 'ccajas_consultas_norm_mes', 'catm_trx_norm_mes', 'matm_norm_mes', 'ctrx_quarter_norm_mes', 'Master_status_norm_mes', 'Master_mfinanciacion_limite_norm_mes', 'Master_Fvencimiento_norm_mes', 'Master_msaldototal_norm_mes', 'Master_msaldopesos_norm_mes', 'Master_fechaalta_norm_mes', 'Master_mpagominimo_norm_mes', 'Visa_status_norm_mes', 'Visa_Fvencimiento_norm_mes', 'Visa_msaldototal_norm_mes', 'Visa_msaldopesos_norm_mes', 'Visa_mconsumospesos_norm_mes', 'Visa_mconsumosdolares_norm_mes', 'Visa_mlimitecompra_norm_mes', 'Visa_madelantodolares_norm_mes', 'Visa_mpagospesos_norm_mes', 'Visa_fechaalta_norm_mes', 'Visa_mconsumototal_norm_mes', 'Visa_cconsumos_norm_mes', 'Visa_cadelantosefectivo_norm_mes', 'Visa_mpagominimo_norm_mes', 'active_quarter_lag2_norm_mes', 'active_quarter_delta2_norm_mes', 'cliente_vip_lag2_norm_mes', 'cliente_vip_delta2_norm_mes', 'internet_lag2_norm_mes', 'internet_delta2_norm_mes', 'cliente_edad_lag2_norm_mes', 'cliente_edad_delta2_norm_mes', 'cliente_antiguedad_delta1_norm_mes', 'cliente_antiguedad_lag2_norm_mes', 'cliente_antiguedad_delta2_norm_mes', 'mrentabilidad_lag2_norm_mes', 'mrentabilidad_delta2_norm_mes', 'mrentabilidad_annual_lag1_norm_mes', 'mrentabilidad_annual_delta1_norm_mes', 'mrentabilidad_annual_lag2_norm_mes', 'mrentabilidad_annual_delta2_norm_mes', 'mcomisiones_lag1_norm_mes', 'mcomisiones_lag2_norm_mes', 'mcomisiones_delta2_norm_mes', 'mactivos_margen_delta1_norm_mes', 'mactivos_margen_lag2_norm_mes', 'mactivos_margen_delta2_norm_mes', 'mpasivos_margen_lag1_norm_mes', 'mpasivos_margen_lag2_norm_mes', 'mpasivos_margen_delta2_norm_mes', 'cproductos_lag1_norm_mes', 'cproductos_delta1_norm_mes', 'cproductos_lag2_norm_mes', 'cproductos_delta2_norm_mes', 'tcuentas_lag2_norm_mes', 'tcuentas_delta2_norm_mes', 'ccuenta_corriente_delta1_norm_mes', 'ccuenta_corriente_lag2_norm_mes', 'ccuenta_corriente_delta2_norm_mes', 'mcuenta_corriente_adicional_lag2_norm_mes', 'mcuenta_corriente_adicional_delta2_norm_mes', 'mcuenta_corriente_lag1_norm_mes', 'mcuenta_corriente_delta1_norm_mes', 'mcuenta_corriente_lag2_norm_mes', 'mcuenta_corriente_delta2_norm_mes', 'ccaja_ahorro_lag2_norm_mes', 'ccaja_ahorro_delta2_norm_mes', 'mcaja_ahorro_lag1_norm_mes', 'mcaja_ahorro_lag2_norm_mes', 'mcaja_ahorro_delta2_norm_mes', 'mcaja_ahorro_adicional_lag2_norm_mes', 'mcaja_ahorro_adicional_delta2_norm_mes', 'mcaja_ahorro_dolares_lag2_norm_mes', 'mcaja_ahorro_dolares_delta2_norm_mes', 'cdescubierto_preacordado_lag2_norm_mes', 'cdescubierto_preacordado_delta2_norm_mes', 'mcuentas_saldo_lag1_norm_mes', 'mcuentas_saldo_lag2_norm_mes', 'mcuentas_saldo_delta2_norm_mes', 'ctarjeta_debito_lag2_norm_mes', 'ctarjeta_debito_delta2_norm_mes', 'ctarjeta_debito_transacciones_lag2_norm_mes', 'ctarjeta_debito_transacciones_delta2_norm_mes', 'mautoservicio_lag2_norm_mes', 'mautos …[línea recortada]
seleccion_igual = features == FEATURES_REFERENCIA
reporte_seleccion = {"coincide_lista_y_orden": seleccion_igual,
    "cantidad": len(features), "esperada": len(FEATURES_REFERENCIA),
    "faltan": sorted(set(FEATURES_REFERENCIA)-set(features)),
    "nuevas": sorted(set(features)-set(FEATURES_REFERENCIA))}
(SALIDA / "comparacion_seleccion.json").write_text(json.dumps(reporte_seleccion, indent=2), encoding="utf-8")
print("Selección idéntica a las 400 variables anteriores:", seleccion_igual)
if not seleccion_igual:
    print("ATENCIÓN: cambió la selección; esta corrida no reproduce la configuración original. No se reemplaza la selección calculada.")

# [Anotación · líneas 459–476] Función objetivo de Optuna: propone num_iterations (1000–2000, paso 100),
#   num_leaves (8–128) y min_sum_hessian_in_leaf (0,1–100, escala logarítmica), entrena con 202103–202104 y
#   semilla 17, predice 202106 y calcula AUC y ganancia con umbral. Guarda ambos como atributos del trial y
#   devuelve el AUC, porque OBJETIVO_OPTUNA es 'auc'.
#%% celda 14 [texto]
## 4. Repetir los cinco trials originales
Estudio vacío, semilla 17, AUC de junio. Rango de árboles: 1000–2000, paso 100. No se fijan los parámetros elegidos.

#%% celda 15 [código]
def objective(trial):
    config = {
        "num_iterations": trial.suggest_int("num_iterations", *RANGOS["num_iterations"][:2], step=RANGOS["num_iterations"][2]),
        "num_leaves": trial.suggest_int("num_leaves", *RANGOS["num_leaves"]),
        "min_sum_hessian_in_leaf": trial.suggest_float("min_sum_hessian_in_leaf", *RANGOS["min_sum_hessian_in_leaf"], log=True),
    }
    model = entrenar(config, train_lgb, SEMILLA_BUSQUEDA, [valid_lgb])
    p = model.predict(X_valid)
    auc = auc_score(y_valid, p)
    gan = ganancia_umbral(y_valid, p)
    trial.set_user_attr("auc_junio", auc)
    trial.set_user_attr("ganancia_umbral_junio", gan)
    return auc if OBJETIVO_OPTUNA == "auc" else gan

# [Anotación · líneas 478–499] Calcula el SHA256 del CSV de variables y arma el protocolo de la búsqueda
#   (meses, objetivo, parámetros fijos, rangos, semilla, variables, versiones, umbral y valores de ganancia);
#   con ambos nombra el estudio y su carpeta. Crea un estudio nuevo que maximiza, con TPESampler(seed=17), y
#   ejecuta 5 trials de a uno. Exige al menos 1 trial completo, muestra los trials ordenados por valor y guarda
#   trials.csv.
h = hashlib.sha256()
with CSV.open("rb") as f:
    for b in iter(lambda: f.read(1024*1024), b""):
        h.update(b)
HASH_CSV = h.hexdigest()
protocolo = {"version": VERSION_ESTUDIO, "train": MESES_BUSQUEDA, "valid": MES_VALIDACION,
    "objetivo": OBJETIVO_OPTUNA, "fijos": PARAMETROS_FIJOS, "rangos": RANGOS,
    "seed": SEMILLA_BUSQUEDA, "features": features, "firma_canaritos": firma_can, "calidad": "ccajas_depositos_mayo_nan",
    "lgb": lgb.__version__, "optuna": optuna.__version__, "umbral": UMBRAL,
    "ganancia_acierto": GANANCIA_ACIERTO, "costo": COSTO_ESTIMULO}
firma = hashlib.sha256(json.dumps(protocolo, sort_keys=True).encode()).hexdigest()[:12]
estudio = f"profesor_{HASH_CSV[:12]}_{firma}"
RUN_DIR = SALIDA / estudio
RUN_DIR.mkdir(exist_ok=True)
study = optuna.create_study(direction="maximize", study_name=estudio,
    sampler=optuna.samplers.TPESampler(seed=SEMILLA_BUSQUEDA))
study.optimize(objective, n_trials=N_TRIALS, n_jobs=1)
completos = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
assert len(completos) >= N_CONFIGURACIONES_FINAL, "Completar al menos diez trials."
print("Mejor trial:", study.best_trial.number, "Objetivo:", OBJETIVO_OPTUNA, "Valor:", study.best_value)
display(study.trials_dataframe().sort_values("value", ascending=False).head(10))
study.trials_dataframe().to_csv(RUN_DIR / "trials.csv", index=False)

# [Anotación · líneas 501–506] Imprime los parámetros encontrados y si son iguales a PARAMETROS_REFERENCIA
#   (num_iterations 1500, num_leaves 103, min_sum_hessian_in_leaf 9.311090875055461), junto con un AUC de
#   referencia escrito como texto (0.9048495713188451).
#%% celda 16 [código]
PARAMETROS_REFERENCIA = {"num_iterations": 1500, "num_leaves": 103,
                         "min_sum_hessian_in_leaf": 9.311090875055461}
print("Parámetros encontrados:", study.best_params)
print("Coinciden con ganador original:", study.best_params == PARAMETROS_REFERENCIA)
print("AUC original de referencia: 0.9048495713188451")

# [Anotación · líneas 508–538] Validación en 202106: con los parámetros del trial de mayor valor entrena un
#   modelo por cada una de las 10 semillas con 202103–202104 y predice 202106. Para cada semilla registra AUC,
#   ganancia con umbral y ganancia por corte; muestra media, desvío, mínimo y máximo. Guarda
#   validacion_3_semillas.csv y cortes_3_semillas.csv, promedia las probabilidades de las 10 semillas, imprime
#   el AUC del promedio y guarda su ganancia por corte en validacion_ensamble.csv.
#%% celda 17 [texto]
## 5. Validación del ensamble elegido en junio

#%% celda 18 [código]
config_mejor = dict(study.best_params)
probs = []
filas = []
filas_cortes = []
for i, seed in enumerate(SEMILLAS, 1):
    modelo = entrenar(config_mejor, train_lgb, seed)
    p = modelo.predict(X_valid)
    probs.append(p)
    filas.append({"seed": seed, "auc": auc_score(y_valid, p),
                  "ganancia_umbral": ganancia_umbral(y_valid, p)})
    tc = tabla_cortes(y_valid, p, valid.numero_de_cliente)
    tc["seed"] = seed
    filas_cortes.append(tc)
    print(f"Semilla {i}/{len(SEMILLAS)} terminada", flush=True)
por_semilla = pd.DataFrame(filas)
por_corte = pd.concat(filas_cortes, ignore_index=True)
print("Media y desvío de resultados individuales:")
display(por_semilla[["auc", "ganancia_umbral"]].agg(["mean", "std", "min", "max"]))
resumen_cortes = por_corte.groupby("envios").ganancia.agg(["mean", "std", "min", "max"])
display(resumen_cortes)
por_semilla.to_csv(RUN_DIR / "validacion_3_semillas.csv", index=False)
por_corte.to_csv(RUN_DIR / "cortes_3_semillas.csv", index=False)

p_valid = np.mean(probs, axis=0)
print("AUC ensamble junio:", auc_score(y_valid, p_valid))
tabla_cortes(y_valid, p_valid, valid.numero_de_cliente).to_csv(RUN_DIR / "validacion_ensamble.csv", index=False)
del probs

# [Anotación · líneas 540–553] Arma las 10 configuraciones finales (los mismos parámetros con cada semilla) y
#   un diccionario con el protocolo, el hash del CSV, la firma de la historia, las semillas, los meses, la
#   versión de Python y las versiones instaladas de pandas, numpy, lightgbm, optuna, duckdb e ipykernel. Lo
#   guarda en configuracion.json junto con requirements_versiones.txt y luego le agrega n_trials, flags_zero
#   (lista vacía) y corte_final.
#%% celda 19 [código]
configs_finales = [{"trial": study.best_trial.number, "params": dict(config_mejor), "seed": seed} for seed in SEMILLAS]
versiones = {p: metadata.version(p) for p in ["pandas", "numpy", "lightgbm", "optuna", "duckdb", "ipykernel"]}
configuracion = {"protocolo": protocolo, "sha256_csv": HASH_CSV, "historia": firma_hist,
    "semillas": SEMILLAS, "mejor_configuracion": config_mejor,
    "configuraciones_finales": configs_finales,
    "meses_final": MESES_FINAL, "mes_prediccion": MES_PREDICCION,
    "version_python": platform.python_version(), "versiones": versiones}
(RUN_DIR / "configuracion.json").write_text(json.dumps(configuracion, indent=2), encoding="utf-8")
(RUN_DIR / "requirements_versiones.txt").write_text("\n".join(f"{p}=={v}" for p,v in versiones.items()), encoding="utf-8")

configuracion["n_trials"] = N_TRIALS
configuracion["flags_zero"] = []
configuracion["corte_final"] = CORTE_FINAL

# [Anotación · líneas 555–573] Arma el conjunto final con las filas de 202103–202106 que tienen clase y el
#   conjunto de 202108 a predecir; verifica que 202108 tenga al menos 15.000 filas e IDs únicos. La etiqueta es
#   1 para BAJA+2. Crea el Dataset de LightGBM, nombra la carpeta de envíos SofiaCerca19_<firma del
#   protocolo>_<firma de las configuraciones> y verifica que los IDs sean enteros.
#%% celda 20 [texto]
## 6. Entrenamiento final y predicción de agosto

#%% celda 21 [código]
final = data[data.foto_mes.isin(MESES_FINAL) & data.clase_ternaria.isin(CLASES)].copy()
agosto = data[data.foto_mes == MES_PREDICCION].copy()
assert len(agosto) >= max(CORTES)
assert agosto.numero_de_cliente.notna().all() and agosto.numero_de_cliente.is_unique
X_final = final[features].replace([np.inf, -np.inf], np.nan)
y_final = (final.clase_ternaria == "BAJA+2").astype(int).to_numpy()
X_agosto = agosto[features].replace([np.inf, -np.inf], np.nan)
ds_final = lgb.Dataset(X_final, label=y_final, free_raw_data=False)
firma_final = hashlib.sha256(json.dumps(configs_finales, sort_keys=True).encode()).hexdigest()[:8]
nombre = f"SofiaCerca19_{firma}_{firma_final}"
ENVIO_DIR = SALIDA / "envios" / nombre
ENVIO_DIR.mkdir(parents=True, exist_ok=True)
archivos = []
ids = pd.to_numeric(agosto.numero_de_cliente, errors="raise")
assert np.isfinite(ids.to_numpy(dtype=float)).all() and (ids == np.floor(ids)).all()
# [Anotación · líneas 574–594] Para cada una de las 10 semillas entrena con 202103–202106, guarda el modelo en
#   modelo_seed<semilla>.txt, predice 202108 y graba el ranking con probabilidades
#   (ranking_seed<semilla>_ANALISIS.csv), ordenado por probabilidad descendente e ID ascendente. Para cada uno
#   de los 11 cortes escribe un CSV con los primeros k IDs, sin encabezado, y verifica que tenga k líneas
#   distintas y numéricas. Al final guarda configuracion.json (con la lista de archivos) y
#   requirements_versiones.txt en la carpeta de envíos.
for i, conf in enumerate(configs_finales, 1):
    seed = conf["seed"]
    ruta_modelo = ENVIO_DIR / f"modelo_seed{seed}.txt"
    m = entrenar(conf["params"], ds_final, seed)
    m.save_model(str(ruta_modelo))
    p = m.predict(X_agosto)
    ranking = pd.DataFrame({"numero_de_cliente": ids.astype("int64").to_numpy(), "probabilidad": p})
    ranking = ranking.sort_values(["probabilidad", "numero_de_cliente"], ascending=[False, True])
    ranking.to_csv(ENVIO_DIR / f"ranking_seed{seed}_ANALISIS.csv", index=False)
    for k in CORTES:
        destino = ENVIO_DIR / f"{nombre}_seed{seed}_top{k}.csv"
        ranking.head(k)[["numero_de_cliente"]].to_csv(destino, index=False, header=False)
        lineas = destino.read_text().splitlines()
        assert len(lineas) == k and len(set(lineas)) == k and all(s.isdigit() for s in lineas)
        archivos.append({"seed": seed, "envios": k, "archivo": destino.name})
    print(f"Modelo final {i}/{len(configs_finales)} listo, semilla {seed}", flush=True)
configuracion["archivos_candidatos"] = archivos
(ENVIO_DIR / "configuracion.json").write_text(json.dumps(configuracion, indent=2), encoding="utf-8")
(ENVIO_DIR / "requirements_versiones.txt").write_text((RUN_DIR / "requirements_versiones.txt").read_text(), encoding="utf-8")
print("Carpeta:", ENVIO_DIR)
print("Adjuntar solo CSV con seed y top en el nombre; los rankings son para análisis.")

# [Anotación · líneas 596–617] Inicio del ensamble: toma los archivos ranking_seed<semilla>_ANALISIS.csv de
#   las 10 semillas en la carpeta de envíos, verifica que existan y los agrupa por semilla leyendo el número del
#   nombre del archivo.
#%% celda 22 [texto]
## 7. Ensamble y candidato de 13.000 clientes

#%% celda 23 [código]
import re

CORTES_ENSAMBLE = CORTES

# Rankings individuales del experimento actual.
rutas = [ENVIO_DIR / f"ranking_seed{seed}_ANALISIS.csv" for seed in SEMILLAS]
assert all(p.is_file() for p in rutas)
assert rutas, f"No encontré rankings en {ENVIO_DIR}"

por_seed = {}

for ruta in rutas:
    coincidencia = re.fullmatch(
        r"ranking_seed(\d+)_ANALISIS\.csv", ruta.name
    )
    if coincidencia:
        seed = int(coincidencia.group(1))
        por_seed.setdefault(seed, []).append(ruta)

# [Anotación · líneas 619–661] Para cada semilla, en orden ascendente, lee su ranking y verifica columnas, IDs
#   únicos y probabilidades finitas entre 0 y 1; si una semilla tuviera más de un archivo, exige que las
#   predicciones sean iguales. Acumula la suma de probabilidades por cliente, verificando que todas las semillas
#   tengan los mismos IDs, y exige al menos dos modelos.
suma = None
semillas_usadas = []

for seed, archivos in sorted(por_seed.items()):
    serie_seed = None

    for ruta in archivos:
        df = pd.read_csv(
            ruta,
            dtype={"numero_de_cliente": "int64"}
        )
        assert {"numero_de_cliente", "probabilidad"} <= set(df.columns)
        assert df.numero_de_cliente.is_unique
        assert np.isfinite(df.probabilidad).all()
        assert df.probabilidad.between(0, 1).all()

        serie = df.set_index("numero_de_cliente")[
            "probabilidad"
        ].sort_index()

        # Si una semilla aparece en dos carpetas, debe ser el mismo ranking.
        if serie_seed is None:
            serie_seed = serie
        else:
            assert serie.index.equals(serie_seed.index), (
                f"IDs distintos para semilla {seed}"
            )
            assert np.allclose(
                serie.to_numpy(), serie_seed.to_numpy(),
                rtol=1e-10, atol=1e-12
            ), f"Hay predicciones distintas para la semilla {seed}"

    if suma is None:
        suma = serie_seed.copy()
    else:
        assert suma.index.equals(serie_seed.index), (
            f"La semilla {seed} tiene otros clientes"
        )
        suma += serie_seed

    semillas_usadas.append(seed)

assert len(semillas_usadas) >= 2, "Se necesitan al menos dos modelos"

# [Anotación · líneas 663–681] Verifica que los IDs sumados sean exactamente los clientes de 202108. Divide la
#   suma por la cantidad de semillas (promedio con pesos iguales) y ordena por probabilidad descendente, con
#   desempate por numero_de_cliente ascendente.
# Comprobar que son todos los clientes de agosto de esta notebook.
ids_agosto = pd.to_numeric(
    agosto.numero_de_cliente, errors="raise"
)
assert ids_agosto.notna().all()
assert (ids_agosto == np.floor(ids_agosto)).all()
assert set(suma.index) == set(ids_agosto.astype("int64"))

promedio = suma / len(semillas_usadas)

ranking_ensamble = (
    promedio.rename("probabilidad")
    .rename_axis("numero_de_cliente")
    .reset_index()
    .sort_values(
        ["probabilidad", "numero_de_cliente"],
        ascending=[False, True]
    )
)

# [Anotación · líneas 683–710] Crea la carpeta SofiaCerca19Ensamble_<fecha y hora> dentro de la carpeta de
#   envíos (no puede existir), guarda el ranking promedio con probabilidades en ranking_ensamble_ANALISIS.csv y
#   escribe ensamble.json con el método, las semillas, los cortes y los archivos de origen.
# Carpeta nueva para identificar exactamente este ensamble.
marca = datetime.now().strftime("%Y%m%d_%H%M%S")
prefijo = f"SofiaCerca19Ensamble_{marca}"
CARPETA_ENSAMBLE = ENVIO_DIR / prefijo
CARPETA_ENSAMBLE.mkdir(exist_ok=False)

ranking_ensamble.to_csv(
    CARPETA_ENSAMBLE / "ranking_ensamble_ANALISIS.csv",
    index=False
)

resumen = {
    "metodo": "promedio simple de probabilidades",
    "semillas": semillas_usadas,
    "cantidad_modelos": len(semillas_usadas),
    "cortes": CORTES_ENSAMBLE,
    "archivos_fuente": [
        str(ruta)
        for seed in semillas_usadas
        for ruta in por_seed[seed]
    ],
}
(CARPETA_ENSAMBLE / "ensamble.json").write_text(
    json.dumps(resumen, indent=2), encoding="utf-8"
)

print("Semillas incluidas:", semillas_usadas)
print("Cantidad de modelos:", len(semillas_usadas))

# [Anotación · líneas 712–735] Para cada corte (cada uno tiene que estar entre 8.000 y 15.000) escribe
#   <prefijo>_top<corte>.csv con los primeros IDs del ranking promedio, sin encabezado, y verifica la cantidad
#   de líneas, que no se repitan y que sean numéricas. Comprueba que se usaron las 10 semillas, define CSV_FINAL
#   como el archivo del corte CORTE_FINAL (13000), agrega su nombre y su SHA256 a la configuración y la guarda
#   en la carpeta del ensamble.
for corte in CORTES_ENSAMBLE:
    assert 8000 <= corte <= 15000
    assert corte <= len(ranking_ensamble)

    destino = CARPETA_ENSAMBLE / f"{prefijo}_top{corte}.csv"
    ranking_ensamble.head(corte)[["numero_de_cliente"]].to_csv(
        destino, index=False, header=False
    )

    lineas = destino.read_text().splitlines()
    assert len(lineas) == corte
    assert len(set(lineas)) == corte
    assert all(linea.isdigit() for linea in lineas)

    print("CSV listo:", destino.name)

print("\nCarpeta:", CARPETA_ENSAMBLE)
print("Adjuntar únicamente los archivos *_top*.csv")
assert semillas_usadas == sorted(SEMILLAS)
CSV_FINAL = CARPETA_ENSAMBLE / f"{prefijo}_top{CORTE_FINAL}.csv"
configuracion["csv_final"] = CSV_FINAL.name
configuracion["sha256_csv_final"] = hashlib.sha256(CSV_FINAL.read_bytes()).hexdigest()
(CARPETA_ENSAMBLE / "configuracion.json").write_text(json.dumps(configuracion, indent=2), encoding="utf-8")
print("Candidato final:", CSV_FINAL)

# [Anotación · líneas 737–754] La celda de texto enumera los archivos a conservar e indica que la notebook fue
#   revisada sintácticamente y que falta comparar dos ejecuciones completas. La celda final, si existe
#   CSV_REFERENCIA, lee ese archivo y CSV_FINAL como listas de IDs, exige que la referencia tenga IDs únicos y
#   CORTE_FINAL filas, y guarda en comparacion_csv.json si coinciden clientes, orden y bytes, la cantidad de
#   clientes en común y ambos SHA256; si no existe, imprime un aviso.
#%% celda 24 [texto]
La notebook fue revisada sintácticamente. Falta entrenar con el dataset y comparar dos ejecuciones completas para comprobar la reproducción. Guardar requirements_versiones.txt, trials.csv, seleccion.json, importancias.csv, configuracion.json y el CSV elegido. Instalar las versiones registradas antes de repetir. No modificar N_TRIALS ni SEMILLAS después de elegir el envío sin generar y probar un nuevo candidato.

#%% celda 25 [código]
if CSV_REFERENCIA.is_file():
    original_ids = pd.read_csv(CSV_REFERENCIA, header=None, names=["id"], dtype={"id":"int64"})
    nuevos_ids = pd.read_csv(CSV_FINAL, header=None, names=["id"], dtype={"id":"int64"})
    assert original_ids.id.is_unique and len(original_ids) == CORTE_FINAL
    reporte = {"mismos_clientes": set(original_ids.id) == set(nuevos_ids.id),
               "mismo_orden": original_ids.id.tolist() == nuevos_ids.id.tolist(),
               "mismos_bytes": CSV_REFERENCIA.read_bytes() == CSV_FINAL.read_bytes(),
               "clientes_comunes": len(set(original_ids.id) & set(nuevos_ids.id)),
               "sha256_referencia": hashlib.sha256(CSV_REFERENCIA.read_bytes()).hexdigest(),
               "sha256_nuevo": hashlib.sha256(CSV_FINAL.read_bytes()).hexdigest()}
    (CARPETA_ENSAMBLE / "comparacion_csv.json").write_text(json.dumps(reporte, indent=2), encoding="utf-8")
    print(reporte)
else:
    print("No se comparó con el ganador: falta", CSV_REFERENCIA)
```


## Explicaciones del alumno (texto original)

### README.md

> # Competencia 1 — Sofía González Romero
>
> Modelo final: notebook 19, ensamble de diez semillas, corte de 12.500 clientes. Envío `sofia13`, ID `1627-1791748586270969`, ganancia pública **101,4200** reportada por el bot.
>
> ## Preparación del target desde el archivo crudo
>
> La notebook `notebooks/01_target_sql.ipynb` se incluye sin modificaciones. Parte de `data/competencia_01_crudo.csv` y exporta `data/competencia_01.csv`, que luego consume la 19. Si ya se dispone del archivo con clase_ternaria, ejecutar directamente la 19.
>
> Para ejecutar la notebook de target, instalar primero las versiones de requirements.txt y además `python -m pip install jupysql sqlalchemy duckdb-engine`. Estas tres dependencias adicionales no estaban registradas en la configuración del modelo; sus versiones originales no se conocen. Abrir Jupyter desde la carpeta notebooks para que las rutas relativas `../data` se resuelvan correctamente, y ejecutar la notebook de target en orden. No ejecutar celdas de exportación sobre un archivo que se quiera conservar sin guardar antes una copia.
>
> El SQL construye una grilla de clientes por períodos observados, marca presencia/ausencia y consulta la presencia en los dos períodos siguientes:
>
> | Presencia siguiente | Presencia dos períodos después | Clase |
> | --- | --- | --- |
> | Sí | Sí | CONTINUA |
> | Sí | No | BAJA+2 |
> | No | No | BAJA+1 |
> | Otras combinaciones o futuro no disponible | | NULL |
>
> Solo se exportan filas en las que el cliente está presente en el período actual. Los últimos períodos pueden quedar sin target. La definición supone que los períodos observados son meses consecutivos: LEAD opera por posición dentro de la grilla de períodos. La 19 usa BAJA+2=1 y CONTINUA/BAJA+1=0; excluye filas sin target del entrenamiento.
>
> Se incluye el procedimiento original como antecedente; no se ha ejecutado de nuevo aquí ni comparado su exportación con el dataset utilizado en el envío. La consulta COPY original no fija ORDER BY: no se garantiza el mismo orden de filas o hash del CSV exportado. Para verificar la cadena completa desde crudo hay que comparar claves, valores y target del archivo generado con el utilizado en la corrida final.
>
> ## Ejecución del modelo desde competencia_01.csv
>
> 1. Usar preferentemente Python **3.14.7**, la versión registrada en la corrida.
> 2. Crear un entorno e instalar dependencias: `python -m pip install -r requirements.txt`.
> 3. Crear `data/` en la raíz de este repositorio y colocar allí **competencia_01.csv** de la competencia. El dataset no se incluye.
> 4. Abrir `notebooks/19_Modelo_Final.ipynb`, elegir ese entorno, reiniciar el kernel y ejecutar todas las celdas en orden.
> 5. Buscar el ensamble en `resultados/exploracion19_…/envios/…/SofiaCerca19Ensamble_…/`. El archivo terminado en `_top13000.csv` es el candidato final. Los archivos ANALISIS contienen probabilidades y no son envíos.
>
> La notebook no requiere una base de Optuna, modelos, FE ni selecciones de corridas anteriores. Reconstruye todo desde el original. Cada ejecución utiliza una carpeta nueva. El CSV de referencia es solo para verificar; no se usa para entrenar ni predecir.
>
> ## Método
>
> Se corrige ccajas_depositos de mayo a NA. Se excluyen préstamos personales y sus derivadas. Se generan lags de uno y dos meses calendario y deltas; se normalizan por máximo absoluto de cada variable dentro del mes. Tendencia y promedio usan la observación actual y dos anteriores por cliente, con al menos dos valores válidos; no necesariamente son tres meses consecutivos. Julio aporta historia para agosto. No se agregan flags cero ni ranking percentil.
>
> Canaritos: semilla 17, 1000 árboles, 31 hojas, Hessian mínimo 10; ruido uniforme equivalente al 20 % de las variables evaluables, con mínimo diez canaritos. La selección usa posiciones de importancia gain, mediana de posiciones de canaritos menos un desvío muestral; conserva aparte columnas vacías o constantes. La lista anterior de 400 variables en la notebook sirve únicamente para comparar, nunca para sustituir la selección nueva.
>
> Búsqueda: marzo–abril para entrenamiento, junio para validación; target BAJA+2=1 y CONTINUA/BAJA+1=0, sin undersampling. Se maximizó AUC con cinco trials secuenciales, semilla 17, estudio vacío. Rangos: árboles 1000–2000, paso 100; hojas 8–128; Hessian mínimo 0,1–100 en escala logarítmica. TPESampler predeterminado tiene diez trials iniciales aleatorios: esta búsqueda de cinco trials permanece en esa fase, sin etapa adaptativa TPE.
>
> Parámetros fijos de la cátedra: max_bin=31, min_data_in_leaf=0, feature_fraction=0.50, feature_fraction_bynode=0.20, learning_rate=0.005. La configuración ganadora fue **1000 árboles, 103 hojas y min_sum_hessian_in_leaf=9.311090875055461**. Es un resultado de búsqueda; la notebook lo vuelve a buscar.
>
> Se valida con diez semillas y se reentrena con marzo–junio. Semillas: [17, 103, 211, 307, 401, 503, 601, 701, 809, 907]. Se promedian las probabilidades de agosto con pesos iguales y se ordenan de mayor a menor, desempate por ID ascendente. El CSV contiene IDs sin encabezado. El corte final es 12.500.
>
> La variante se exploró alrededor de los 1500 árboles del experimento anterior. Su elección consideró la validación de junio y la comparación pública de agosto; el resultado público no constituye una evaluación independiente de la selección final.
>
> ## Verificación contra el envío
>
> El CSV final está en `referencia/SofiaCerca19Ensamble_20261011_162005_top12500.csv`. SHA256: `f2827098eaa3b85bfea46a3094c9da8bb58c30c05c9ebd2e46d3b134c9bdd3a0`.
>
> La última celda original compara contra un CSV anterior de la 13 si existe; no es la referencia del envío final de la 19. Para comparar con este envío, cambiar **solo** CSV_REFERENCIA en la celda de configuración a:
>
> ```python
> CSV_REFERENCIA = BASE / "referencia" / "SofiaCerca19Ensamble_20261011_162005_top13000.csv"
> ```
>
> Esto no cambia entrenamiento ni predicciones. Al final muestra coincidencia de clientes, orden y bytes. Distintos saltos de línea pueden cambiar bytes sin cambiar IDs ni orden. La comparación de parámetros que menciona 1500 árboles es contra la corrida anterior; False es esperable para la 19.
>
> La estructura de la notebook, configuración y formato del CSV se comprobaron. El dataset original y modelos no están disponibles en este paquete: no se volvió a ejecutar el entrenamiento aquí ni se comprobó una segunda ejecución exacta contra este CSV. Conservar las versiones registradas y verificar el CSV regenerado; plataformas y versiones pueden afectar resultados.
>
> ## Archivos
>
> - `notebooks/01_target_sql.ipynb`: preparación original del target desde el dataset crudo.
> - `notebooks/19_Modelo_Final.ipynb`: código suministrado, sin cambios al entrenamiento.
> - `requirements.txt`: versiones registradas en la configuración.
> - `registro/`: configuración de corrida e historia, selección e identificación del envío.
> - `referencia/`: CSV final enviado.
>
> No subir a GitHub el dataset, las bases DuckDB ni la carpeta resultados. Son archivos regenerables y quedan excluidos por .gitignore.

