# Daniel Ramirez — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: urbdaniel86
- Repositorio: https://github.com/urbdaniel86/DMEyF
- Link posteado: https://github.com/urbdaniel86/DMEyF/tree/main/competencia_01
- Commit: cc1ab23a5ffa2e6c325a8277cd78a4e074a28f14
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/urbdaniel86/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/urbdaniel86.json

## Resumen

La entrega está en la carpeta competencia_01/ y tiene dos scripts de Python, un README, un env.yaml y la carpeta de un experimento (config.yaml, hiperparametros.json, resultado.json, optuna.db y cuatro gráficos). fe_competencia_01.py carga el CSV en DuckDB, pasa ccajas_depositos a NULL en 202105 y agrega 109 variables: lags, deltas, media, mínimo, máximo y pendiente de 3 meses para 12 variables, rank dentro del mes para 9 montos y 4 combinaciones de tarjetas, saldo, comisiones y rentabilidad; escribe competencia_01_fe.parquet. modelar_competencia_01.py tiene dos modos. El modo experimento optimiza LightGBM con Optuna (40 trials, AUC promedio en 3 folds agrupados por cliente sobre 202103–202105), reentrena los 3 trials de mayor AUC con 5 semillas cada uno, mide la ganancia en 202106 y guarda el corte de máxima ganancia. El modo entrega lee de la carpeta del experimento los hiperparámetros y el corte (10.160), entrena 15 modelos con 202103–202106, promedia sus rankings percentiles sobre 202108 y escribe un CSV con los clientes de mayor ranking. La clase de entrenamiento es binaria, con BAJA+1 y BAJA+2 como positivos.

**Qué entrega.** Un CSV sin encabezado con un numero_de_cliente por línea: los 10.160 clientes de 202108 con mayor ranking promedio del ensamble, en entregas/DU<fecha y hora>tres_meses_v1_hess/. El archivo de predicción no está incluido en el repositorio.

**Cómo se ejecuta.** Según el README, desde la carpeta competencia_01/: (1) `conda env create -f env.yaml` y `conda activate dmeyf-competencia-01`; (2) `python fe_competencia_01.py --path <ruta>/competencia_01.csv`, donde el CSV es el dataset de la competencia con clase_ternaria ya calculada, que deja competencia_01_fe.parquet junto al CSV; (3) `python modelar_competencia_01.py --modo entrega --desde experimentos/20261011_0840_tres_meses_v1_hess --archivos 1 --dataset <ruta>/competencia_01_fe.parquet`.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: positivo = BAJA+1 o BAJA+2, negativo = CONTINUA (`CLASES_POSITIVAS` y `construir_target`). La ganancia se calcula sólo sobre BAJA+2. Un comentario del código menciona pruebas con peso entre 0,5 y 1,0 para los BAJA+1; ese código no está en el repositorio.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código: se entrena con todas las filas de los meses elegidos.
- **Calidad de datos:** `ccajas_depositos` pasa a NULL en todas las filas de 202105 (según el README, en ese mes viene en cero para todos los clientes). Los lags sólo se completan cuando la fila anterior del cliente corresponde al mes inmediato anterior del dataset (o al de dos meses atrás, para el lag 2); si falta, quedan en NULL.
- **Drifting:** Para 9 variables de monto (mrentabilidad, mcomisiones, mcuentas_saldo, mpasivos_margen, mactivos_margen, mtarjeta_visa_consumo, mtarjeta_master_consumo, mpayroll, mcaja_ahorro) agrega una columna `_rank` con la posición dentro del mes llevada a la escala 0–1: (rank − 1) / (cantidad de valores no nulos del mes − 1). Las columnas originales en pesos se conservan. `foto_mes` no se usa como variable del modelo. No se observa deflación.
- **Variables dentro del mes:** 4 variables: `tc_msaldototal` (Master_msaldototal + Visa_msaldototal), `tc_mconsumototal` (Master_mconsumototal + Visa_mconsumototal), `tc_consumo_sobre_saldo` (consumo total de tarjetas / mcuentas_saldo) y `comisiones_sobre_rentabilidad` (mcomisiones / mrentabilidad). Las sumas tratan los nulos como 0 y los cocientes devuelven NULL si el denominador es 0 o nulo.
- **Variables históricas:** Para 12 variables (ctrx_quarter, mrentabilidad, mcomisiones, mcuentas_saldo, mpasivos_margen, mactivos_margen, mtarjeta_visa_consumo, mtarjeta_master_consumo, cproductos, ctarjeta_visa_transacciones, mpayroll, mcaja_ahorro): lag 1 y lag 2, delta 1 y delta 2 (valor actual menos el lag), y media, mínimo, máximo y pendiente por mínimos cuadrados (`regr_slope` contra el índice de mes) sobre una ventana del mes actual y los dos anteriores. Son 96 variables.
- **Selección de variables:** No hay selección: `resolver_features` usa todas las columnas del parquet menos `numero_de_cliente`, `foto_mes` y `clase_ternaria` (261 variables según resultado.json). El docstring de esa función declara que filtrar variables con canaritos se midió con 261, 69 y 17 variables y que por eso no hay opción de filtrado; el código de canaritos no está en el repositorio.
- **Optimización de hiperparámetros:** Optuna con `TPESampler(seed=100019)` y `MedianPruner(n_startup_trials=10, n_warmup_steps=1)`, 40 trials y un límite de 5 horas, con el estudio guardado en SQLite (`optuna.db`). Maximiza el AUC promedio de 3 folds de `StratifiedGroupKFold` agrupados por `numero_de_cliente` sobre 202103–202105 apilados. Busca `num_iterations` en [200, 10000], `num_leaves` en [4, 200] y `min_sum_hessian_in_leaf` en [0,0001, 100] en escala logarítmica. Quedan fijos learning_rate 0,005, max_bin 31, min_data_in_leaf 0, feature_fraction 0,5 y feature_fraction_bynode 0,2. Se conservan los 3 trials completos de mayor AUC.
- **Hiperparámetros finales:** Tres configuraciones (hiperparametros.json): trial 18 con num_leaves 36, num_iterations 2375 y min_sum_hessian_in_leaf 19,22; trial 34 con 25, 3760 y 17,61; trial 38 con 34, 3627 y 17,38. Comunes a las tres: learning_rate 0,005, max_bin 31, min_data_in_leaf 0, feature_fraction 0,5, feature_fraction_bynode 0,2, objective binary, metric auc, deterministic True, force_row_wise True, num_threads 16.
- **Semillas:** 5 semillas por configuración: los primeros 5 de 50 enteros distintos menores que 1.000.000 generados con `np.random.RandomState(100019)` (`semillas_del_curso`). El valor 100019 se usa además como semilla del sampler de Optuna, de la partición en folds y de los modelos de la optimización.
- **Cantidad de semillas:** 5
- **Ensamble:** 15 modelos LightGBM: 3 configuraciones × 5 semillas, todos entrenados con los mismos meses apilados. Las probabilidades de cada modelo se convierten en ranking percentil (`rank(pct=True)`) y el puntaje final es el promedio de los 15 rankings.
- **Corte:** Cantidad de clientes leída de `corte_optimo` en resultado.json: 10.160, la posición del máximo de la curva de ganancia acumulada del ensamble medido en 202106. El modo entrega lleva ese valor al rango 8.000–15.000 si queda fuera y escribe los ids de mayor ranking promedio hasta esa cantidad. La opción `--corte` permite pasar uno o varios cortes a mano (una carpeta por corte); el comando del README no la usa.
- **Validación:** Dos mediciones en el modo experimento. (1) Validación cruzada de 3 folds por cliente sobre 202103–202105 con AUC, para Optuna. (2) Entrenamiento con 202103–202105 y prueba en 202106 con la ganancia de la competencia (+1.072.500 por BAJA+2, −27.500 por el resto), quitando de 202106 a los clientes que son BAJA+1 o BAJA+2 en los meses de entrenamiento (`excluir_positivos_del_train: true`, `permitir_gap_corto: true`). Según resultado.json: auc_cv 0,92987, ganancia_ensemble 422.400.000 en el corte 10.160, ganancia media por modelo 422.310.167 con desvío 2.633.392 sobre 15 modelos. Con un solo mes de entrenamiento el código usa `StratifiedShuffleSplit` con `test_size`; esa rama no se ejecuta con este config.
- **Salidas:** fe_competencia_01.py: `competencia_01_fe.parquet`. Modo entrega: carpeta `entregas/DU<AAAAMMDDHHMM>tres_meses_v1_hess/` con el archivo `..._m01.csv` (un `numero_de_cliente` por línea, sin encabezado), copia de `config.yaml`, `submit.txt`, `viene_de.txt`, `resultado_bot.txt` y `detalle_archivos.json`. Modo experimento: carpeta en `experimentos/` con `config.yaml`, `optuna.db`, tres gráficos de Optuna, `hiperparametros.json`, `curva_ganancia.csv`, `curva_ganancia.png` y `resultado.json`, más `experimentos/experimentos.csv`.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Mínimos y máximos de ventana (`variables.min_max_ventana`)
- Optuna (`hiperparametros.optuna`)
- Validación cruzada (`validacion.validacion_cruzada`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Técnicas sólo exploradas

- Genera archivos con varios cortes (`corte.varios_cortes`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: env.yaml declara un entorno conda `dmeyf-competencia-01` (canal conda-forge) con python 3.10.19, pandas 2.3.3, numpy 2.2.5, lightgbm 4.7.0, optuna 5.0.0, scikit-learn 1.7.2, pyarrow 21.0.0, duckdb 1.5.5, pyyaml 6.0.3, matplotlib 3.10.9 y sqlite (sin versión). resultado.json registra las mismas versiones de python, lightgbm, optuna, pandas, numpy y scikit-learn. Un comentario de modelar_competencia_01.py indica que la entrega se generó con 16 hilos (`num_threads: 16`). No se declara sistema operativo ni hardware.

## Pasos del camino de la entrega

1. **Lectura del CSV e índice de mes.** fe_competencia_01.py recibe la ruta del CSV por `--path`, lo carga en una base DuckDB en memoria con `read_csv_auto` y agrega la columna `t`, el número de orden de `foto_mes` (`dense_rank`). (`competencia_01/fe_competencia_01.py` líneas 5–20)
2. **Corrección de ccajas_depositos en 202105.** Pasa `ccajas_depositos` a NULL en todas las filas de `foto_mes = 202105`. (`competencia_01/fe_competencia_01.py` líneas 22–28)
3. **Variables históricas de 12 variables.** Para cada variable de `campos_fe` arma lag 1, lag 2, delta 1, delta 2, y media, mínimo, máximo y pendiente sobre la ventana del mes actual y los dos anteriores del mismo cliente. Los lags quedan en NULL si la fila anterior no es la del mes `t-1` o `t-2`. Son 96 variables. (`competencia_01/fe_competencia_01.py` líneas 44–49; `competencia_01/fe_competencia_01.py` líneas 61–75; `competencia_01/fe_competencia_01.py` líneas 102–105)
4. **Rank dentro del mes de 9 variables de monto.** Para las variables de `campos_fe` cuyo nombre empieza con `m` calcula la posición dentro de `foto_mes` en escala 0–1: (rank − 1) / (cantidad de no nulos del mes − 1), con NULL si el valor es nulo. (`competencia_01/fe_competencia_01.py` líneas 51–52; `competencia_01/fe_competencia_01.py` líneas 77–82)
5. **Combinaciones dentro del mes.** Con las macros `suma_sin_null` y `ratio_seguro` agrega el saldo total y el consumo total de tarjetas (Master + Visa), el consumo de tarjetas sobre `mcuentas_saldo` y `mcomisiones` sobre `mrentabilidad`. (`competencia_01/fe_competencia_01.py` líneas 30–40; `competencia_01/fe_competencia_01.py` líneas 54–57; `competencia_01/fe_competencia_01.py` líneas 84–93)
6. **Escritura del parquet con variables.** Ejecuta una sola consulta que crea `competencia_01_fe` con las columnas originales (sin `t`) más las 109 expresiones, y la guarda como `competencia_01_fe.parquet` con compresión ZSTD en la carpeta del CSV. (`competencia_01/fe_competencia_01.py` líneas 95–119)
7. **Configuración del experimento.** El config.yaml del experimento declara: entrenamiento 202103–202105 apilado, test 202106, 5 semillas, 40 trials, 3 folds, top_n 3, cinco parámetros fijos de LightGBM, tres rangos de búsqueda y los meses de la entrega (202103–202106). `cargar_config` valida las claves y separa los parámetros en fijos (escalares) y buscados (listas de dos valores). (`competencia_01/experimentos/20261011_0840_tres_meses_v1_hess/config.yaml` líneas 1–41; `competencia_01/modelar_competencia_01.py` líneas 339–420)
8. **Clase binaria y variables del modelo.** La clase vale 1 si `clase_ternaria` es BAJA+1 o BAJA+2 y 0 en otro caso. Las variables del modelo son todas las columnas del parquet menos `numero_de_cliente`, `foto_mes` y `clase_ternaria`. (`competencia_01/modelar_competencia_01.py` líneas 42–54; `competencia_01/modelar_competencia_01.py` líneas 476–491)
9. **Optimización con Optuna y validación cruzada por cliente.** En el modo experimento, Optuna (TPE con semilla 100019 y poda por mediana) corre hasta 40 trials. Cada trial entrena un LightGBM por fold de `StratifiedGroupKFold` (3 folds, grupo = cliente) sobre 202103–202105 y devuelve el AUC promedio. Los 3 trials completos de mayor AUC se guardan en hiperparametros.json (trials 18, 34 y 38). (`competencia_01/modelar_competencia_01.py` líneas 150–179; `competencia_01/modelar_competencia_01.py` líneas 223–307; `competencia_01/experimentos/20261011_0840_tres_meses_v1_hess/hiperparametros.json` líneas 1–46)
10. **Medición en 202106 y elección del corte.** El modo experimento quita de 202106 a los clientes que fueron positivos en los meses de entrenamiento, entrena las 3 configuraciones con 5 semillas sobre 202103–202105, promedia los rankings sobre 202106 y calcula la curva de ganancia acumulada (sólo BAJA+2 suma). Guarda en resultado.json el corte del máximo (10.160) y la ganancia del ensamble (422.400.000). (`competencia_01/modelar_competencia_01.py` líneas 110–138; `competencia_01/modelar_competencia_01.py` líneas 658–677; `competencia_01/modelar_competencia_01.py` líneas 693–706; `competencia_01/experimentos/20261011_0840_tres_meses_v1_hess/resultado.json` líneas 60–68)
11. **Modo entrega: lectura de hiperparámetros, corte y meses.** Con `--modo entrega --desde <carpeta>` el script lee config.yaml, hiperparametros.json y resultado.json del experimento, toma el corte de `corte_optimo`, usa los meses de `meses_train_entrega` (202103–202106) y carga del parquet esos meses más 202108. (`competencia_01/modelar_competencia_01.py` líneas 745–813; `competencia_01/modelar_competencia_01.py` líneas 425–441; `competencia_01/experimentos/20261011_0840_tres_meses_v1_hess/config.yaml` líneas 34–38)
12. **Entrenamiento de 15 modelos y promedio de rankings.** Genera 5 semillas a partir de 100019 y entrena un LightGBM por cada configuración y semilla (3 × 5) con los cuatro meses apilados. Cada modelo predice 202108 y sus probabilidades se pasan a ranking percentil. (`competencia_01/modelar_competencia_01.py` líneas 328–330; `competencia_01/modelar_competencia_01.py` líneas 496–534; `competencia_01/modelar_competencia_01.py` líneas 821–826)
13. **Escritura y verificación del CSV.** Con `--archivos 1` promedia los rankings de los 15 modelos, ordena los clientes de mayor a menor y escribe los primeros 10.160 `numero_de_cliente` en un CSV sin encabezado. El archivo se relee para verificar cantidad de líneas (8.000–15.000), que sean sólo dígitos, que no haya repetidos y que todos los ids sean de 202108. (`competencia_01/modelar_competencia_01.py` líneas 828–865; `competencia_01/modelar_competencia_01.py` líneas 539–563)
14. **Archivos de trazabilidad de la entrega.** Junto al CSV escribe `submit.txt`, `viene_de.txt` (experimento de origen, trials, ganancia medida, corte y meses), `resultado_bot.txt` y `detalle_archivos.json`, e imprime las indicaciones para enviar el archivo por mensaje privado. (`competencia_01/modelar_competencia_01.py` líneas 867–902)

## Archivos

- `competencia_01/env.yaml` · configuracion · YAML · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/urbdaniel86/competencia_01/env.yaml.txt) — Definición del entorno conda `dmeyf-competencia-01` con las versiones de python, pandas, numpy, lightgbm, optuna, scikit-learn, pyarrow, duckdb, pyyaml y matplotlib, más sqlite.
- `competencia_01/README.md` · explicacion · Markdown · 108 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/urbdaniel86/competencia_01/README.md.txt) — Texto de presentación de la entrega: cómo crear el entorno y correr los dos scripts, y qué tiene la entrega (clase, variables nuevas, meses, optimización de hiperparámetros con las tres configuraciones elegidas, ensamble, corte y forma de medición).
- `competencia_01/fe_competencia_01.py` · principal · Python · 122 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/urbdaniel86/competencia_01/fe_competencia_01.py.txt) — Carga el CSV de la competencia en DuckDB, pasa `ccajas_depositos` a NULL en 202105, agrega 109 variables (históricas, de rank dentro del mes y combinaciones) con una consulta SQL y escribe `competencia_01_fe.parquet`.
- `competencia_01/modelar_competencia_01.py` · principal · Python · 950 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/urbdaniel86/competencia_01/modelar_competencia_01.py.txt) — Script con dos modos. `experimento`: optimiza LightGBM con Optuna, reentrena las configuraciones elegidas con varias semillas, mide la ganancia en el mes de test y guarda hiperparámetros, corte y resultado en una carpeta. `entrega`: lee esa carpeta, entrena el ensamble con los meses de la entrega, puntúa 202108 y escribe el CSV.
- `competencia_01/experimentos/20261011_0840_tres_meses_v1_hess/config.yaml` · configuracion · YAML · 41 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/urbdaniel86/competencia_01/experimentos/20261011_0840_tres_meses_v1_hess/config.yaml.txt) — Config del experimento `tres_meses_v1_hess`: campo `pregunta` con el motivo de la corrida, meses de entrenamiento 202103–202105 apilados, test 202106, 5 semillas, 40 trials, 3 folds, top_n 3, parámetros fijos y rangos de LightGBM, meses de la entrega 202103–202106, `permitir_gap_corto`, `excluir_positivos_del_train` y límite de 5 horas para Optuna.
- `competencia_01/experimentos/20261011_0840_tres_meses_v1_hess/hiperparametros.json` · configuracion · JSON · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/urbdaniel86/competencia_01/experimentos/20261011_0840_tres_meses_v1_hess/hiperparametros.json.txt) — Las tres configuraciones de LightGBM que usa el modo entrega (trials 18, 34 y 38), cada una con su AUC de validación cruzada, `num_iterations` y parámetros.
- `competencia_01/experimentos/20261011_0840_tres_meses_v1_hess/resultado.json` · configuracion · JSON · 78 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/urbdaniel86/competencia_01/experimentos/20261011_0840_tres_meses_v1_hess/resultado.json.txt) — Resultado del experimento, del que el modo entrega lee `corte_optimo` (10160): fecha, commit, meses, 261 variables, las tres configuraciones, auc_cv, gap 1, ganancia_ensemble 422400000, ganancia media y desvío por modelo, 15 modelos, 15549 segundos y versiones de los paquetes.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### competencia_01/fe_competencia_01.py

Carga el CSV de la competencia en DuckDB, pasa `ccajas_depositos` a NULL en 202105, agrega 109 variables (históricas, de rank dentro del mes y combinaciones) con una consulta SQL y escribe `competencia_01_fe.parquet`.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Importa argparse, duckdb y Path. `main()` lee el argumento `--path` (por defecto
#   `../data/competencia_01.csv`) y abre una base DuckDB en memoria.
import argparse
import duckdb
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', default='../data/competencia_01.csv')
    args = parser.parse_args()

    dataset_path = args.path

    con = duckdb.connect(':memory:')

# [Anotación · líneas 14–20] Carga el CSV con `read_csv_auto` en la tabla `competencia_01` y agrega la columna
#   `t`: el número de orden del mes (`dense_rank` sobre `foto_mes`), que vale 1 para el primer mes y sube de a 1
#   por cada mes presente en el archivo.
    # Carga del archivo CSV en DuckDB
    
    con.execute("""
        CREATE OR REPLACE TABLE competencia_01 AS
        SELECT *, dense_rank() OVER (ORDER BY foto_mes) AS t
        FROM read_csv_auto(?)
    """, [dataset_path])

# [Anotación · líneas 22–28] Pasa `ccajas_depositos` a NULL en todas las filas de `foto_mes = 202105`.
    # Corregir ccajas_depositos para 202105
    
    con.execute("""
        UPDATE competencia_01
        SET ccajas_depositos = null
        WHERE foto_mes = 202105
    """)

# [Anotación · líneas 30–40] Define dos macros SQL: `ratio_seguro(a, b)` divide tratando los nulos como 0 y
#   devuelve NULL cuando el denominador es 0 o nulo; `suma_sin_null(a, b)` suma tratando los nulos como 0.
    # Macros para evitar errores de division por cero y sumar nulls como 0

    con.execute("""
        CREATE OR REPLACE MACRO ratio_seguro(a, b) AS
        IFNULL(a, 0) / NULLIF(IFNULL(b, 0), 0)
    """)

    con.execute("""
        CREATE OR REPLACE MACRO suma_sin_null(a, b) AS 
        IFNULL(a, 0) + IFNULL(b, 0)
    """)

# [Anotación · líneas 42–59] Define las listas de trabajo: `campos_fe` con 12 variables (ctrx_quarter,
#   mrentabilidad, mcomisiones, mcuentas_saldo, mpasivos_margen, mactivos_margen, mtarjeta_visa_consumo,
#   mtarjeta_master_consumo, cproductos, ctarjeta_visa_transacciones, mpayroll, mcaja_ahorro); `campos_rank` con
#   las 9 de esa lista cuyo nombre empieza con `m`; `pares_tc` con los pares Master/Visa de `msaldototal` y
#   `mconsumototal`; y `feats`, la lista de expresiones SQL que se va llenando.
    # Creación de features: historia, orden y combinaciones horizontales

    campos_fe = [
        'ctrx_quarter', 'mrentabilidad', 'mcomisiones', 'mcuentas_saldo',
        'mpasivos_margen', 'mactivos_margen', 'mtarjeta_visa_consumo',
        'mtarjeta_master_consumo', 'cproductos', 'ctarjeta_visa_transacciones',
        'mpayroll', 'mcaja_ahorro',
    ]

    # Los montos son los que sufren data drifting -> les agregamos variables de orden
    campos_rank = [c for c in campos_fe if c.startswith('m')]

    pares_tc = [
        ('Master_msaldototal', 'Visa_msaldototal', 'tc_msaldototal'),
        ('Master_mconsumototal', 'Visa_mconsumototal', 'tc_mconsumototal'),
    ]

    feats = []

# [Anotación · líneas 61–75] Para cada una de las 12 variables arma 8 expresiones: `lag_1` y `lag_2` (el valor
#   de 1 y 2 filas atrás del mismo cliente, sólo si esa fila corresponde al mes `t-1` o `t-2`; si no, NULL),
#   `delta_1` y `delta_2` (valor actual menos cada lag), y `media_3`, `min_3`, `max_3` y `slope_3` (pendiente de
#   la regresión de la variable contra `t`) sobre la ventana de 3 meses. Son 96 expresiones.
    # Historia: valor pasado, delta, ventana movil de 3 meses y tendencia
    for c in campos_fe:
        lag1 = f'case when lag(t, 1) over ventana_cliente = t - 1 then lag({c}, 1) over ventana_cliente end'
        lag2 = f'case when lag(t, 2) over ventana_cliente = t - 2 then lag({c}, 2) over ventana_cliente end'

        feats += [
            f'{lag1} as {c}_lag_1',
            f'{c} - ({lag1}) as {c}_delta_1',
            f'{lag2} as {c}_lag_2',
            f'{c} - ({lag2}) as {c}_delta_2',
            f'avg({c}) over ventana_3 as {c}_media_3',
            f'min({c}) over ventana_3 as {c}_min_3',
            f'max({c}) over ventana_3 as {c}_max_3',
            f'regr_slope({c}, t) over ventana_3 as {c}_slope_3',
        ]

# [Anotación · líneas 77–82] Para cada una de las 9 variables de monto arma `<variable>_rank`: la posición
#   dentro del mes llevada a la escala 0–1, calculada como (rank − 1) / (cantidad de valores no nulos del mes −
#   1); queda NULL si el valor es nulo.
    # Orden dentro del mes: inmune al drift de los montos
    for c in campos_rank:
        rank = (f'case when {c} is null then null else '
                f'(rank() over (partition by foto_mes order by {c}) - 1.0) '
                f'/ nullif(count({c}) over (partition by foto_mes) - 1, 0) end')
        feats.append(f'{rank} as {c}_rank')

# [Anotación · líneas 84–93] Agrega `tc_msaldototal` y `tc_mconsumototal` (suma Master + Visa con
#   `suma_sin_null`) y dos cocientes con `ratio_seguro`: `tc_consumo_sobre_saldo` (consumo total de tarjetas
#   sobre `mcuentas_saldo`) y `comisiones_sobre_rentabilidad` (`mcomisiones` sobre `mrentabilidad`).
    # Combinacion horizontal Visa + Master
    for a, b, alias in pares_tc:
        feats.append(f'suma_sin_null({a}, {b}) as {alias}')

    # Ratios: siempre con ratio_seguro, nunca con "/"
    feats += [
        'ratio_seguro(suma_sin_null(Master_mconsumototal, Visa_mconsumototal), mcuentas_saldo)'
        ' as tc_consumo_sobre_saldo',
        'ratio_seguro(mcomisiones, mrentabilidad) as comisiones_sobre_rentabilidad',
    ]

# [Anotación · líneas 95–109] Une las expresiones en una sola consulta que crea la tabla `competencia_01_fe`
#   con todas las columnas originales menos `t` más las variables nuevas. Define dos ventanas: `ventana_cliente`
#   (por `numero_de_cliente`, ordenada por `t`) y `ventana_3` (misma partición, filas cuyo `t` está entre el
#   actual menos 2 y el actual). Imprime la cantidad de variables nuevas.
    bloque = '\n    , '.join(feats)

    query_fe = f"""create or replace table competencia_01_fe as
        select
            * exclude (t)
            , {bloque}
        from competencia_01
        window
            ventana_cliente as (partition by numero_de_cliente order by t),
            ventana_3 as (partition by numero_de_cliente order by t
                        range between 2 preceding and current row)
    """
    con.execute(query_fe)

    print(f'{len(feats)} features nuevas')

# [Anotación · líneas 111–122] Escribe la tabla en `competencia_01_fe.parquet` (formato Parquet, compresión
#   ZSTD) en la misma carpeta del CSV de entrada, imprime la ruta y define el punto de entrada del script.
    # Guardar el dataset final en un CSV

    out_path = Path(args.path).parent / "competencia_01_fe.parquet"

    con.execute(f"""
        COPY competencia_01_fe TO '{out_path}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)

    print(f'Dataset con features: {out_path}')

if __name__ == "__main__":
    main()
```

### competencia_01/modelar_competencia_01.py

Script con dos modos. `experimento`: optimiza LightGBM con Optuna, reentrena las configuraciones elegidas con varias semillas, mide la ganancia en el mes de test y guarda hiperparámetros, corte y resultado en una carpeta. `entrega`: lee esa carpeta, entrena el ensamble con los meses de la entrega, puntúa 202108 y escribe el CSV.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–32] Docstring con los dos modos del script (`experimento` y `entrega`) y un ejemplo de
#   invocación de cada uno. Importa argparse, json, platform, shutil, subprocess, sys, time, datetime, Path,
#   lightgbm, numpy, optuna, pandas y yaml.
# -*- coding: utf-8 -*-
"""Modelado de la competencia 01: optimiza, mide, y genera las entregas.

    python modelar_competencia_01.py --modo experimento
    python modelar_competencia_01.py --modo entrega --desde experimentos/2026...

DOS MODOS

  experimento : (datos + rangos de hiperparametros) -> Optuna -> reentrena con los
                ganadores -> mide contra el mes de test. Escribe una carpeta en
                experimentos/ y apendea una linea a experimentos/experimentos.csv.
  entrega     : toma de una carpeta de experimentos/ los hiperparametros Y el corte
                optimo que midio, entrena, scorea el mes de aplicacion y escribe los
                .csv del submit en entregas/.

"""

import argparse
import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import yaml

# [Anotación · líneas 34–68] Constantes del problema: ganancia por acierto 1.072.500 y costo por estímulo
#   27.500; clases positivas del entrenamiento `BAJA+1` y `BAJA+2`; columnas que nunca son variables del modelo
#   (`numero_de_cliente`, `foto_mes`, `clase_ternaria`, `clase_binaria`, `t`); mes de aplicación 202108; rango
#   de registros aceptado para un archivo (8.000 a 15.000); semilla base 100019; y las carpetas `experimentos/`
#   y `entregas/` con el archivo `experimentos/experimentos.csv`.
# ------------------------------------------------------------------- constantes

# El caso de negocio. El 0.025 de la catedra es exactamente
# COSTO / (GANANCIA + COSTO) = 27.500 / 1.100.000: la probabilidad de equilibrio, o sea
# a partir de que probabilidad estimular deja de ser plata perdida.
GANANCIA_ACIERTO = 1_072_500
COSTO_ESTIMULO = 27_500

# El target de entrenamiento: BAJA+1 y BAJA+2 juntos contra CONTINUA. z601 lo midio mejor
# que BAJA+2 contra el resto, y en pruebas posteriores la curva es plana entre dar peso 0.5
# y 1.0 a los BAJA+1. OJO con la asimetria: la ganancia se cobra SOLO por BAJA+2. El target
# de entrenamiento y la metrica de negocio son distintos a proposito.
CLASES_POSITIVAS = ['BAJA+1', 'BAJA+2']

# Nunca son features: la llave, el tiempo y cualquier cosa derivada del target.
# 'foto_mes' se saca ademas por una razon propia: con varios meses apilados el modelo
# partiria por ella, y el mes de aplicacion es un valor que ningun arbol vio, asi que
# todas sus filas caerian para el mismo lado del corte.
# 't' y 'clase_binaria' no estan en el parquet actual (fe_competencia_01.py hace
# 'exclude (t)'); quedan como guarda porque 't' es foto_mes disfrazada.
COLS_PROHIBIDAS = {'numero_de_cliente', 'foto_mes', 'clase_ternaria', 'clase_binaria', 't'}

# El bot rechaza los archivos fuera de este rango.
# El mes a predecir. Es un hecho de la competencia, no un parametro del experimento:
# si viviera en el yaml, alguien lo cambiaria por accidente y la entrega saldria
# sobre un mes equivocado sin que nada se queje.
MES_APLICACION = 202108

MIN_REGISTROS, MAX_REGISTROS = 8_000, 15_000

SEMILLA_BASE = 100019

DIR_EXPERIMENTOS = Path('experimentos')
DIR_ENTREGAS = Path('entregas')
CSV_LOG = DIR_EXPERIMENTOS / 'experimentos.csv'

# [Anotación · líneas 70–105] Define qué claves del YAML son opciones del script (`CLAVES_NO_LGB`) y qué 13
#   parámetros de LightGBM se aceptan (`PARAMS_LGB`), cada uno con su tipo y si se busca en escala logarítmica
#   (`min_sum_hessian_in_leaf`, `learning_rate`, `lambda_l1` y `lambda_l2`). `PARAMS_FIJOS_SIEMPRE` fija para
#   todos los modelos: objective binary, metric auc, verbose -1, deterministic True, force_row_wise True y
#   num_threads 16.
# Las claves del yaml que NO son parametros de LightGBM. Todo lo demas se interpreta como
# tal: escalar = fijo, lista [min, max] = rango que busca Optuna.
CLAVES_NO_LGB = {'nombre', 'pregunta', 'dataset', 'meses_train', 'estrategia_meses',
                 'mes_test', 'semillas', 'trials', 'folds', 'test_size', 'top_n',
                 'mes_aplicacion', 'permitir_gap_corto', 'meses_train_entrega',
                 'permitir_test_en_train', 'excluir_positivos_del_train',
                 'optuna_timeout_horas'}

# Whitelist de parametros de LightGBM aceptados. Sirve para atrapar typos: sin esto, una
# clave mal escrita en el yaml se pasaria a LightGBM, que solo avisa con un warning y
# sigue — el parametro quedaria en su default y nadie se enteraria.
# (tipo, escala logaritmica). min_sum_hessian_in_leaf va en log porque su rango abarca 5
# ordenes de magnitud: en lineal, Optuna gastaria casi todos los trials entre 1 y 10 y
# practicamente nunca probaria 0.001.
PARAMS_LGB = {
    'max_bin': ('int', False),
    'num_leaves': ('int', False),
    'num_iterations': ('int', False),
    'min_data_in_leaf': ('int', False),
    'min_sum_hessian_in_leaf': ('float', True),
    'feature_fraction': ('float', False),
    'feature_fraction_bynode': ('float', False),
    'bagging_fraction': ('float', False),
    'bagging_freq': ('int', False),
    'learning_rate': ('float', True),
    'lambda_l1': ('float', True),
    'lambda_l2': ('float', True),
    'min_gain_to_split': ('float', False),
}

# Los que el script fija siempre; no se configuran.
# num_threads fijo y no 0: con 0 LightGBM usa todos los nucleos de la maquina, y con
# otra cantidad de hilos los arboles pueden no salir identicos. La entrega se genero
# con 16 (lo que daba 0 en esa maquina), asi que replicarla exacta pide 16.
PARAMS_FIJOS_SIEMPRE = {'objective': 'binary', 'metric': 'auc', 'verbose': -1,
                        'deterministic': True, 'force_row_wise': True, 'num_threads': 16}


# [Anotación · líneas 108–145] Tres funciones de ganancia. `ganancia_curva` ordena los clientes por puntaje
#   descendente (orden estable) y devuelve la ganancia acumulada: +1.072.500 por cada BAJA+2 y −27.500 por cada
#   cliente que no lo es. `mejor_corte` devuelve la posición del máximo de esa curva y su ganancia.
#   `curva_en_grilla` muestrea la curva cada 250 clientes.
# ---------------------------------------------------------------------- ganancia

def ganancia_curva(proba, es_baja2):
    """Ganancia acumulada ordenando los clientes por `proba` descendente.

    `proba` puede ser una probabilidad o un ranking promediado: solo importa el orden.
    Devuelve un array donde la posicion i es la ganancia de estimular a los i+1 clientes
    de mayor score.

    Se cobra SOLO por BAJA+2: cada uno estimulado suma GANANCIA_ACIERTO, y cada estimulo
    que no era BAJA+2 cuesta COSTO_ESTIMULO. Un BAJA+1 paga lo mismo que un CONTINUA, que
    es cero.

    No asume que recibe el mes completo: trabaja con las filas que le pasen, que es lo que
    va a necesitar la simulacion publico/privado.

    `kind='stable'` para que los empates se desempaten por orden original y la salida sea
    reproducible. Importa porque el ensemble promedia RANKINGS, y los promedios de rangos
    colisionan mas seguido que las probabilidades crudas.
    """
    ganancia = (np.where(es_baja2 == 1, GANANCIA_ACIERTO, 0)
                - np.where(es_baja2 == 0, COSTO_ESTIMULO, 0))
    orden = np.argsort(proba, kind='stable')[::-1]
    return np.cumsum(ganancia[orden])


def mejor_corte(proba, es_baja2):
    """(corte, ganancia) en el maximo de la curva acumulada."""
    acum = ganancia_curva(proba, es_baja2)
    corte = int(np.argmax(acum)) + 1
    return corte, float(acum[corte - 1])


def curva_en_grilla(proba, es_baja2, paso=250):
    """La curva muestreada cada `paso` clientes, para graficar y para comparar corridas."""
    acum = ganancia_curva(proba, es_baja2)
    cortes = range(paso, len(acum) + 1, paso)
    return pd.DataFrame([{'corte': c, 'ganancia': float(acum[c - 1])} for c in cortes])


# [Anotación · líneas 148–179] `objetivo_optuna`: arma los parámetros de un trial (fijos del config,
#   `PARAMS_FIJOS_SIEMPRE`, seed 100019 y un valor sugerido por Optuna para cada parámetro con rango), separa
#   `num_iterations` para usarlo como cantidad de rondas, entrena un LightGBM por fold y calcula el AUC en la
#   parte de validación. Tras cada fold informa a Optuna el promedio acumulado y corta el trial si el pruner lo
#   indica. Devuelve el AUC promedio.
# ------------------------------------------------------------------ optimizacion

def objetivo_optuna(trial, X, y, folds, fijos, buscados):
    """Lo que Optuna maximiza: el AUC promedio entre folds.
    """
    from sklearn.metrics import roc_auc_score

    params = dict(fijos)
    params.update(PARAMS_FIJOS_SIEMPRE)
    params['seed'] = SEMILLA_BASE

    for nombre, (lo, hi) in buscados.items():
        tipo, log = PARAMS_LGB[nombre]
        params[nombre] = (trial.suggest_int(nombre, int(lo), int(hi), log=log)
                          if tipo == 'int' else
                          trial.suggest_float(nombre, float(lo), float(hi), log=log))

    # num_iterations va aparte, como num_boost_round. Se guarda ya, antes de cualquier
    # poda posible, para que el mejor trial siempre lo tenga.
    n_iter = int(params.pop('num_iterations'))
    trial.set_user_attr('num_iterations', n_iter)

    aucs = []
    for paso, (idx_tr, idx_va) in enumerate(folds, 1):
        modelo = lgb.train(params, lgb.Dataset(X.iloc[idx_tr], label=y.iloc[idx_tr]),
                           num_boost_round=n_iter)
        aucs.append(roc_auc_score(y.iloc[idx_va], modelo.predict(X.iloc[idx_va])))
        trial.report(float(np.mean(aucs)), step=paso)
        if trial.should_prune():
            raise optuna.TrialPruned()

    return float(np.mean(aucs))


# [Anotación · líneas 182–220] `graficar_optuna`: genera y guarda en la carpeta del experimento tres gráficos
#   del estudio (`optuna_slice.png`, `optuna_history.png`, `optuna_importances.png`) con matplotlib en modo sin
#   pantalla. Si un gráfico da error, imprime un aviso y continúa.
def graficar_optuna(study, carpeta):
    """Tres graficos para decidir como ajustar los rangos del config.

    slice        : cada hiperparametro contra el AUC. Si los mejores trials se apilan
                   contra un borde del rango, el rango esta mal puesto y conviene
                   extenderlo hacia ese lado.
    history      : el mejor AUC acumulado contra el numero de trial. Si la curva esta
                   plana desde hace muchos trials, mas trials no van a aportar; si
                   todavia sube, conviene seguir.
    importances  : cuanto mueve el resultado cada hiperparametro. Los que no mueven nada
                   se pueden fijar y liberar presupuesto de busqueda para los que si.
    """
    import warnings
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from optuna.visualization import matplotlib as ovm

    graficos = {'optuna_slice': ovm.plot_slice,
                'optuna_history': ovm.plot_optimization_history,
                'optuna_importances': ovm.plot_param_importances}

    for nombre, fn in graficos.items():
        try:
            with warnings.catch_warnings():
                # Los graficos de optuna estan marcados como experimentales desde la v2.2
                warnings.simplefilter('ignore')
                ax = fn(study)
            # plot_slice devuelve un array de Axes (uno por hiperparametro); el resto, uno
            fig = (ax.flatten()[0] if isinstance(ax, np.ndarray) else ax).figure
            fig.set_size_inches(max(9, 4 * (len(ax) if isinstance(ax, np.ndarray) else 1)),
                                4.5)
            fig.tight_layout()
            fig.savefig(carpeta / f'{nombre}.png', dpi=120)
            plt.close(fig)
        except Exception as e:
            # Un grafico que falla no tiene por que tirar abajo la corrida
            print(f'  (no pude generar {nombre}: {type(e).__name__}: {str(e)[:70]})')
    plt.close('all')


# [Anotación · líneas 223–251] `optimizar`, primera parte: toma las filas de los meses de entrenamiento del
#   config y arma la clase binaria. Con más de un mes parte los datos con `StratifiedGroupKFold` (cantidad de
#   folds del config, shuffle, random_state 100019) usando `numero_de_cliente` como grupo; con un solo mes usa
#   `StratifiedShuffleSplit` con el `test_size` del config.
def optimizar(data, features, cfg, fijos, buscados, db_path, carpeta):
    """Corre Optuna y devuelve una LISTA con los top-N trials."""
    from sklearn.model_selection import StratifiedGroupKFold, StratifiedShuffleSplit

    train = data[data['foto_mes'].isin(cfg['meses_train'])]
    X, y = train[features], construir_target(train)

    # Con VARIOS meses hay que partir por CLIENTE, no por fila. Si no, el mismo cliente
    # cae en train (con su fila de un mes) y en validacion (con la del otro), con
    # features casi iguales y label correlacionado. Medido sobre 202103+202104: el 81.6%
    # de los clientes de validacion estaban tambien en train.
    #
    # No es cosmetico. Esa fuga premia memorizar, y empuja la busqueda a modelos mucho
    # mas grandes: con un mes Optuna prefiere 8-49 hojas, con dos meses y fuga pedia
    # 170-192. Un factor de 10 a 20 de capacidad, elegido por el artefacto.
    if len(cfg['meses_train']) > 1:
        sgk = StratifiedGroupKFold(n_splits=cfg['folds'], shuffle=True,
                                   random_state=SEMILLA_BASE)
        folds = list(sgk.split(X, y, groups=train['numero_de_cliente']))
        print(f'CV: StratifiedGroupKFold por cliente ({cfg["folds"]} folds), '
              f'{len(cfg["meses_train"])} meses apilados')
    else:
        # Con un solo mes cada cliente aparece una vez, asi que partir filas ya parte
        # clientes y el ShuffleSplit permite elegir el test_size.
        sss = StratifiedShuffleSplit(n_splits=cfg['folds'], test_size=cfg['test_size'],
                                     random_state=SEMILLA_BASE)
        folds = list(sss.split(X, y))
        print(f'CV: StratifiedShuffleSplit ({cfg["folds"]} folds, '
              f'test_size={cfg["test_size"]})')

# [Anotación · líneas 253–280] Crea o reabre el estudio de Optuna `competencia_01` guardado en SQLite
#   (`optuna.db`), con dirección maximizar, `TPESampler(seed=100019)` y `MedianPruner(n_startup_trials=10,
#   n_warmup_steps=1)`. Cuenta los trials completos y podados ya hechos, corre los que faltan hasta `trials` con
#   un límite de tiempo de `optuna_timeout_horas`, informa cuántos se podaron y genera los gráficos.
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        direction='maximize', study_name='competencia_01',
        storage=f'sqlite:///{db_path}', load_if_exists=True,
        sampler=optuna.samplers.TPESampler(seed=SEMILLA_BASE),
        # n_startup_trials=10: no poda nada hasta tener 10 trials con que comparar.
        pruner=optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=1))

    # Los podados cuentan como hechos: si no, al reanudar se volverian a correr.
    terminados = (optuna.trial.TrialState.COMPLETE, optuna.trial.TrialState.PRUNED)
    hechos = len([t for t in study.trials if t.state in terminados])
    faltan = max(0, cfg['trials'] - hechos)
    print(f'Optuna: {hechos} trials hechos, corro {faltan} mas ({cfg["folds"]} folds)')
    if faltan:
        # Con un tope de horas, Optuna deja de lanzar trials nuevos al vencer (el que
        # esta corriendo termina). Sirve para que una corrida nocturna llegue a la
        # manana con resultado aunque los trials salgan mas lentos de lo estimado.
        horas = cfg.get('optuna_timeout_horas')
        study.optimize(lambda t: objetivo_optuna(t, X, y, folds, fijos, buscados),
                       n_trials=faltan, show_progress_bar=True,
                       timeout=float(horas) * 3600 if horas else None)

    podados = len([t for t in study.trials
                   if t.state == optuna.trial.TrialState.PRUNED])
    if podados:
        print(f'  ({podados} trials podados antes de terminar los folds)')

    graficar_optuna(study, carpeta)

# [Anotación · líneas 282–307] Ordena los trials completos por AUC descendente, termina con error si no hay
#   ninguno, y arma la lista de los `top_n` primeros: número de trial, AUC de la validación cruzada,
#   `num_iterations` y parámetros (los fijos más los del trial). Imprime la lista y la devuelve.
    # Solo los COMPLETE: un trial podado no tiene el AUC de todos los folds, asi que su
    # valor no es comparable con el de uno que los corrio todos.
    completos = sorted([t for t in study.trials
                        if t.state == optuna.trial.TrialState.COMPLETE],
                       key=lambda t: t.value, reverse=True)
    if not completos:
        sys.exit('ERROR: ningun trial termino. Si todos quedaron podados, subi '
                 'n_startup_trials o corre mas trials.')

    top_n = int(cfg.get('top_n', 1))
    elegidos = []
    for t in completos[:top_n]:
        params = dict(fijos)
        params.update(t.params)
        params.pop('num_iterations', None)
        elegidos.append({'trial': t.number, 'auc_cv': float(t.value),
                         'num_iterations': int(t.user_attrs['num_iterations']),
                         'params': params})

    print(f'\nTop {len(elegidos)} de {len(completos)} trials completos:')
    for i, e in enumerate(elegidos, 1):
        extra = ' '.join(f'{k}={v}' for k, v in sorted(e['params'].items())
                         if k in buscados)
        print(f'  {i}. trial {e["trial"]:3d}  AUC {e["auc_cv"]:.5f}  '
              f'{e["num_iterations"]:4d} arboles  {extra}')
    return elegidos


# [Anotación · líneas 310–330] Utilidades: `git_commit` devuelve el hash corto del commit actual (o
#   `sin_git`); `versiones` devuelve las versiones de python, lightgbm, optuna, pandas, numpy y scikit-learn;
#   `semillas_del_curso` genera 50 enteros distintos menores que 1.000.000 con `RandomState(100019)` y devuelve
#   los primeros `cantidad`.
# ------------------------------------------------------------------- utilidades

def git_commit():
    """Si el codigo cambio entre dos corridas, no son comparables. Es lo que uno olvida."""
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'],
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return 'sin_git'


def versiones():
    import sklearn
    return {'python': platform.python_version(), 'lightgbm': lgb.__version__,
            'optuna': optuna.__version__, 'pandas': pd.__version__,
            'numpy': np.__version__, 'scikit-learn': sklearn.__version__}


def semillas_del_curso(cantidad):
    return np.random.RandomState(SEMILLA_BASE).choice(
        1000000, size=50, replace=False).tolist()[:cantidad]


# [Anotación · líneas 333–373] `cargar_config`, primera parte: lee el YAML y termina con error si faltan
#   claves obligatorias (`nombre`, `dataset`, `meses_train`, `mes_test`, `semillas`, `trials`, `folds`,
#   `test_size`), si `estrategia_meses` no es `por_mes` ni `apilado` o si `top_n` es menor que 1. Si `mes_test`
#   está dentro de `meses_train`, termina con error salvo que el config traiga `permitir_test_en_train`, en cuyo
#   caso imprime un aviso.
# ------------------------------------------------------------------------ config

CLAVES_OBLIGATORIAS = ['nombre', 'dataset', 'meses_train', 'mes_test', 'semillas',
                       'trials', 'folds', 'test_size']


def cargar_config(ruta):
    """Lee el yaml, lo valida, y separa los parametros de LightGBM en fijos y buscados."""
    ruta = Path(ruta)
    if not ruta.exists():
        sys.exit(f'ERROR: no encuentro {ruta}')
    with open(ruta, encoding='utf-8') as fh:
        cfg = yaml.safe_load(fh)

    faltan = [k for k in CLAVES_OBLIGATORIAS if k not in cfg]
    if faltan:
        sys.exit(f'ERROR: al config le faltan claves: {faltan}')
    if cfg.get('estrategia_meses', 'por_mes') not in ('por_mes', 'apilado'):
        sys.exit(f"ERROR: estrategia_meses '{cfg['estrategia_meses']}' no es por_mes "
                 'ni apilado')
    if int(cfg.get('top_n', 1)) < 1:
        sys.exit('ERROR: top_n tiene que ser >= 1')
    if cfg['mes_test'] in cfg['meses_train']:
        if not cfg.get('permitir_test_en_train'):
            sys.exit(
                f"ERROR: mes_test {cfg['mes_test']} esta en meses_train. El test "
                'tiene que ser un mes que el modelo no vio.\n'
                '  Si lo queres igual (por ejemplo para sacar hiperparametros de '
                'TODOS los\n  meses etiquetados, sabiendo que no sobra ninguno para testear), agrega\n'
                '  al config:\n    permitir_test_en_train: true')
        print('=' * 78)
        print(f"AVISO FUERTE: mes_test {cfg['mes_test']} ESTA en meses_train.")
        print('  ganancia_ensemble y corte_optimo de esta corrida se miden sobre '
              'datos que')
        print('  el modelo ya vio: NO son mediciones validas y no se comparan con '
              'las de los')
        print('  demas experimentos. Lo unico utilizable es hiperparametros.json, '
              'que sale')
        print('  de la CV por cliente dentro de meses_train.')
        print('  El corte de la entrega hay que pasarlo a mano con --corte.')
        print('=' * 78)

# [Anotación · líneas 375–392] Calcula el gap como `mes_test` menos el último mes de entrenamiento y termina
#   con error si es menor que 2, salvo que el config traiga `permitir_gap_corto: true`.
    # El gap entre el ultimo mes de train y el de test tiene que ser de 2 meses.
    # clase_ternaria mira dos meses adelante, asi que con gap 1 los positivos del train
    # SON los mismos clientes que hay que acertar en el test: medido, el 43-54% de los
    # positivos se repite. El modelo los memoriza y se lleva el credito, y la ganancia
    # sale inflada. Con gap 2 el solapamiento es exactamente cero: un BAJA+2 del mes de
    # train ya no existe en el mes de test.
    # Ademas gap 2 es la estructura real de la entrega (train 202106 -> score 202108).
    gap = cfg['mes_test'] - max(cfg['meses_train'])
    if gap < 2 and not cfg.get('permitir_gap_corto'):
        sys.exit(
            f"ERROR: el gap entre el ultimo mes de train ({max(cfg['meses_train'])}) y "
            f"el mes de test ({cfg['mes_test']}) es de {gap} mes.\n"
            '  Con gap 1 el 43-54% de los positivos del train son los MISMOS clientes '
            'que\n  hay que acertar en el test, asi que la ganancia sale inflada.\n'
            '  Pone mes_test = ultimo mes de train + 2.\n'
            '  Si lo queres igual (por ejemplo para comparar dos variantes que comparten '
            'el\n  mismo gap, donde la inflacion afecta a las dos), agrega al config:\n'
            '    permitir_gap_corto: true')

# [Anotación · líneas 394–420] Recorre las demás claves del config: un escalar queda como parámetro fijo de
#   LightGBM y una lista de dos elementos como rango `[mínimo, máximo]` para Optuna. Termina con error ante
#   claves que no están en `PARAMS_LGB`, listas que no tienen 2 elementos o `num_iterations` ausente o fijo.
#   Devuelve el config, los fijos y los buscados.
    # Un escalar es un valor fijo; una lista [min, max] es un rango para Optuna.
    fijos, buscados, desconocidas = {}, {}, []
    for clave, valor in cfg.items():
        if clave in CLAVES_NO_LGB:
            continue
        if clave not in PARAMS_LGB:
            desconocidas.append(clave)
        elif isinstance(valor, (list, tuple)):
            if len(valor) != 2:
                sys.exit(f"ERROR: '{clave}' es una lista de {len(valor)} elementos; "
                         'un rango para Optuna tiene que ser [minimo, maximo]')
            buscados[clave] = valor
        else:
            fijos[clave] = valor

    if desconocidas:
        sys.exit(f'ERROR: claves del config que no son parametros de LightGBM conocidos '
                 f'ni opciones del script: {desconocidas}\n'
                 'Si es un typo, corregilo. Si es un parametro de LightGBM que falta, '
                 'agregalo a PARAMS_LGB en este script.')
    if 'num_iterations' not in buscados and 'num_iterations' not in fijos:
        sys.exit('ERROR: falta num_iterations en el config (fijo o como rango)')
    if 'num_iterations' in fijos:
        sys.exit('ERROR: num_iterations tiene que ser un rango [min, max]. No hay early '
                 'stopping, asi que lo elige Optuna.')

    return cfg, fijos, buscados


# [Anotación · líneas 423–458] `meses_para_entrega`: devuelve `meses_train_entrega` si el config lo declara.
#   Si no, desplaza cada mes de `meses_train` tantas posiciones (en la lista ordenada de meses del dataset) como
#   separan a `mes_test` de 202108, y termina con error si algún mes cae fuera del dataset.
# -------------------------------------------------------------------------- datos

def meses_para_entrega(cfg, meses_disponibles):
    """Los meses con que entrenar la entrega: la MISMA receta, corrida hasta 202108.

    Un experimento mide una receta dos meses para atras: por ejemplo "2 meses apilados
    con gap 2" se mide como train 202103+202104 -> test 202106. Para aplicarla hay que
    desplazarla: train 202105+202106 -> score 202108, que conserva el gap.

    Si se entregara con los mismos meses del experimento, el gap seria de 4 meses. Y
    medimos que UN mes de distancia cuesta 45M, asi que seria desastroso.

    Se puede declarar a mano en el config con `meses_train_entrega`. Si no esta, se
    deriva desplazando por la misma cantidad de meses que separa mes_test de
    MES_APLICACION. El desplazamiento se hace por POSICION en la lista de meses del
    dataset y no restando los enteros, porque 202112 + 1 no es 202113.
    """
    if cfg.get('meses_train_entrega'):
        return list(cfg['meses_train_entrega'])

    orden = {m: i for i, m in enumerate(sorted(meses_disponibles))}
    if MES_APLICACION not in orden or cfg['mes_test'] not in orden:
        sys.exit('ERROR: no puedo derivar los meses de entrega; declaralos en el config '
                 'con meses_train_entrega')
    desplazamiento = orden[MES_APLICACION] - orden[cfg['mes_test']]
    inverso = {i: m for m, i in orden.items()}

    derivados = []
    for m in cfg['meses_train']:
        destino = orden[m] + desplazamiento
        if destino not in inverso:
            sys.exit(f'ERROR: al desplazar la receta, el mes {m} caeria fuera del '
                     'dataset. Declara meses_train_entrega a mano en el config.')
        # int() y no el numpy int que trae el parquet: si no, ensucia el yaml y el json
        derivados.append(int(inverso[destino]))
    return sorted(derivados)


# [Anotación · líneas 461–473] `cargar_datos`: lee del parquet sólo las filas de los meses pedidos (filtro en
#   la lectura), termina con error si el archivo no existe o no hay filas, y devuelve la tabla ordenada por
#   `foto_mes` y `numero_de_cliente`.
def cargar_datos(cfg, meses):
    """Lee solo los meses que hacen falta. Filtrar en la lectura evita traer 983k filas."""
    ruta = Path(cfg['dataset'])
    if not ruta.exists():
        sys.exit(f'ERROR: no encuentro {ruta}.\n'
                 'Generalo con: python fe_competencia_01.py')
    data = pd.read_parquet(ruta, filters=[('foto_mes', 'in', list(meses))])
    if data.empty:
        sys.exit(f'ERROR: no hay filas para los meses {list(meses)}')
    # El FE no garantiza el orden de las filas (duckdb arma la tabla en paralelo), y
    # LightGBM si depende de el: arma los cortes de los histogramas con una muestra de
    # filas. Sin ordenar, dos parquets con el mismo contenido dan modelos distintos.
    return data.sort_values(['foto_mes', 'numero_de_cliente']).reset_index(drop=True)


# [Anotación · líneas 476–491] `resolver_features` devuelve todas las columnas del dataset que no están en
#   `COLS_PROHIBIDAS`. `construir_target` devuelve 1 si `clase_ternaria` es `BAJA+1` o `BAJA+2` y 0 en otro
#   caso.
def resolver_features(data):
    """Todas las columnas del dataset menos las prohibidas.

    Medido el 2026-10-08: filtrar features con canaritos PIERDE (261 features 410.7M,
    69 features 393.1M, 17 features 297.4M, en train 202104 -> test 202106). Por eso no
    hay opcion para filtrar: se usan todas.
    """
    features = [c for c in data.columns if c not in COLS_PROHIBIDAS]
    colados = COLS_PROHIBIDAS & set(features)
    assert not colados, f'se colo el target o la llave en las features: {colados}'
    return features


def construir_target(data):
    """1 si el cliente es BAJA+1 o BAJA+2, 0 si no."""
    return data['clase_ternaria'].isin(CLASES_POSITIVAS).astype(int)


# [Anotación · líneas 494–534] `entrenar_ensemble`: separa las filas del mes objetivo y arma los grupos de
#   entrenamiento (un solo grupo con todos los meses si la estrategia es `apilado`; un grupo por mes si es
#   `por_mes`). Para cada grupo, cada configuración de hiperparámetros y cada semilla entrena un LightGBM con
#   `num_iterations` rondas, predice el mes objetivo y convierte las probabilidades en ranking percentil
#   (`rank(pct=True)`). Devuelve el promedio de todos los rankings, las filas del mes objetivo y el detalle por
#   modelo.
# -------------------------------------------------------------- entrenar y scorear

def entrenar_ensemble(data, features, cfg, configs, mes_objetivo, semillas):
    """Un modelo por (config x grupo de meses x semilla). Devuelve (ranking, filas, detalle).
    """
    objetivo = data[data['foto_mes'] == mes_objetivo]
    if objetivo.empty:
        sys.exit(f'ERROR: no hay filas de {mes_objetivo} en el dataset')

    # 'por_mes' = un modelo por cada mes: los miembros ven datos distintos, lo que los
    # decorrelaciona, y un ensemble rinde mas cuanto menos correlacionados estan.
    # 'apilado' = un solo dataset con todos los meses: mas filas y mas positivos, pero
    # promedia regimenes distintos dentro de la funcion de perdida.
    if cfg.get('estrategia_meses', 'por_mes') == 'apilado':
        grupos = [list(cfg['meses_train'])]
    else:
        grupos = [[m] for m in cfg['meses_train']]

    detalle = []
    total = len(configs) * len(grupos) * len(semillas)
    hecho = 0

    for grupo in grupos:
        train = data[data['foto_mes'].isin(grupo)]
        ds = lgb.Dataset(train[features], label=construir_target(train))
        for cfg_i, config in enumerate(configs, 1):
            for semilla in semillas:
                p = dict(config['params'])
                p.update(PARAMS_FIJOS_SIEMPRE)
                p['seed'] = int(semilla)
                modelo = lgb.train(p, ds, num_boost_round=config['num_iterations'])
                proba = modelo.predict(objetivo[features])
                detalle.append({'meses_train': grupo, 'config': cfg_i,
                                'trial': config['trial'], 'semilla': int(semilla),
                                'ranking': pd.Series(proba).rank(pct=True).to_numpy()})
                hecho += 1
                print(f'  modelo {hecho}/{total} (meses {grupo}, config {cfg_i} '
                      f'[trial {config["trial"]}], semilla {semilla})', flush=True)

    ranking = np.mean([d['ranking'] for d in detalle], axis=0)
    return ranking, objetivo, detalle


# [Anotación · líneas 537–563] `escribir_csv_entrega`: escribe los `numero_de_cliente` como enteros, uno por
#   línea, sin encabezado ni índice. Después relee el archivo y termina con error si la cantidad de líneas está
#   fuera de 8.000–15.000, si alguna línea no es sólo dígitos, si hay ids repetidos o si algún id no pertenece
#   al mes de aplicación. Devuelve la cantidad de líneas.
# ----------------------------------------------------------------------- salidas

def escribir_csv_entrega(ids, ruta, ids_validos):
    """Escribe un .csv y lo valida releyendolo del disco."""
    import re
    serie = pd.Series(ids, name='numero_de_cliente')
    if serie.isna().any():
        sys.exit(f'ERROR: hay numero_de_cliente nulos para {ruta.name}')
    serie.astype('int64').to_csv(ruta, header=False, index=False)

    with open(ruta, encoding='utf-8') as fh:
        lineas = [l.strip() for l in fh if l.strip()]
    problemas = []
    if not MIN_REGISTROS <= len(lineas) <= MAX_REGISTROS:
        problemas.append(f'{len(lineas)} registros, fuera de '
                         f'[{MIN_REGISTROS}, {MAX_REGISTROS}]')
    malas = [l for l in lineas if not re.fullmatch(r'\d+', l)]
    if malas:
        problemas.append(f'{len(malas)} ids que no son solo digitos, ej {malas[:3]}')
    if len(set(lineas)) != len(lineas):
        problemas.append(f'{len(lineas) - len(set(lineas))} ids repetidos')
    ajenos = set(map(int, lineas)) - ids_validos
    if ajenos:
        problemas.append(f'{len(ajenos)} ids que no estan en el mes de aplicacion')
    if problemas:
        sys.exit(f'ERROR en {ruta}:\n  ' + '\n  '.join(problemas))
    return len(lineas)


# [Anotación · líneas 566–585] `regenerar_log`: recorre las subcarpetas de `experimentos/`, lee cada
#   `resultado.json` y reescribe `experimentos/experimentos.csv` con una fila por corrida, ordenadas por
#   `timestamp`; los valores que son listas o diccionarios se guardan como texto JSON.
def regenerar_log():
    """Rearma el csv de experimentos entero, una linea por resultado.json.

    Antes se apendeaba una linea por corrida, con el header escrito solo la primera
    vez. Cuando resultado.json gano campos nuevos, las filas nuevas quedaron mas
    largas que el header y pandas dejo de poder leer el archivo. Regenerandolo desde
    los json, que son la fuente de verdad, las columnas son siempre la union de
    todas y una corrida borrada desaparece del csv la proxima vez.
    """
    filas = []
    for d in sorted(DIR_EXPERIMENTOS.iterdir()):
        ruta = d / 'resultado.json'
        if not ruta.is_file():
            continue
        with open(ruta, encoding='utf-8') as fh:
            r = json.load(fh)
        filas.append({k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
                      for k, v in r.items()})
    pd.DataFrame(filas).sort_values('timestamp').to_csv(CSV_LOG, index=False)
    print(f'{CSV_LOG} regenerado: {len(filas)} corridas')


# [Anotación · líneas 588–606] `graficar_curva`: dibuja la ganancia acumulada (en millones) contra el corte,
#   marca con una línea vertical y una etiqueta el punto de máxima ganancia y guarda la figura en PNG.
def graficar_curva(curva, ruta, titulo):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(curva['corte'], curva['ganancia'] / 1e6, lw=1.2)
    mejor = curva.loc[curva['ganancia'].idxmax()]
    ax.axvline(mejor['corte'], ls='--', c='crimson', lw=1)
    ax.annotate(f"optimo {int(mejor['corte']):,}\n{mejor['ganancia'] / 1e6:.1f}M",
                xy=(mejor['corte'], mejor['ganancia'] / 1e6),
                xytext=(8, -26), textcoords='offset points', color='crimson', fontsize=9)
    ax.set_xlabel('corte (cantidad de clientes estimulados)')
    ax.set_ylabel('ganancia acumulada (millones)')
    ax.set_title(titulo)
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(ruta, dpi=120)
    plt.close(fig)


# [Anotación · líneas 609–625] `carpetas_con_nombre`: devuelve, ordenadas, las carpetas de `experimentos/`
#   cuyo nombre tiene la forma `AAAAMMDD_HHMM_<nombre>` y cuya tercera parte coincide con el nombre pedido.
# -------------------------------------------------------------------------- modos

def carpetas_con_nombre(nombre):
    """Las carpetas de experimentos/ cuyo `nombre` coincide, mas nuevas al final.

    El formato es YYYYMMDD_HHMM_nombre, asi que se parte en 3 y se compara la tercera
    parte. No alcanza con endswith('_' + nombre): con nombre='base', la carpeta
    '..._mi_base' daria un falso positivo.
    """
    if not DIR_EXPERIMENTOS.exists():
        return []
    halladas = []
    for d in DIR_EXPERIMENTOS.iterdir():
        partes = d.name.split('_', 2)
        if d.is_dir() and len(partes) == 3 and partes[2] == nombre:
            halladas.append(d)
    return sorted(halladas)


# [Anotación · líneas 628–656] `modo_experimento`, inicio: si ya existe una corrida con el mismo `nombre`
#   termina con error, salvo con `--reanudar`, que reutiliza la carpeta más reciente. En una corrida nueva crea
#   `experimentos/<AAAAMMDD_HHMM>_<nombre>`. Copia el config a esa carpeta y carga del parquet los meses de
#   entrenamiento y el mes de test.
def modo_experimento(cfg, fijos, buscados, ruta_config, args):
    nombre = cfg['nombre']
    previas = carpetas_con_nombre(nombre)

    if previas and not args.reanudar:
        sys.exit(
            f"ERROR: ya hay {len(previas)} corrida(s) con el nombre '{nombre}':\n"
            + '\n'.join(f'  {d}' for d in previas) + '\n\n'
            'Lo mas probable es que te hayas olvidado de cambiar `nombre` en el config.\n'
            'Si es otro experimento, cambiale el nombre (y la pregunta).\n'
            'Si querias CONTINUAR el anterior, corre con --reanudar: reusa la carpeta y\n'
            'su optuna.db, asi los trials ya hechos no se vuelven a correr.')

    if args.reanudar:
        if not previas:
            sys.exit(f"ERROR: --reanudar pero no hay ninguna corrida con el nombre "
                     f"'{nombre}' para continuar")
        carpeta = previas[-1]
        print(f'Reanudando {carpeta}')
    else:
        sello = datetime.now().strftime('%Y%m%d_%H%M')
        carpeta = DIR_EXPERIMENTOS / f'{sello}_{nombre}'
        carpeta.mkdir(parents=True, exist_ok=True)

    shutil.copy(ruta_config, carpeta / 'config.yaml')
    arranque = time.time()

    meses = sorted(set(cfg['meses_train']) | {cfg['mes_test']})
    data = cargar_datos(cfg, meses)

# [Anotación · líneas 658–686] Si el config trae `excluir_positivos_del_train`, quita del mes de test a los
#   clientes que son `BAJA+1` o `BAJA+2` en alguno de los meses de entrenamiento e imprime cuántos quita y
#   cuántos de ellos eran `BAJA+2` en el test. Después resuelve la lista de variables, genera las semillas e
#   imprime el encabezado de la corrida.
    # Con gap 2 (y en la entrega) TODOS los positivos del train ya se fueron del mes
    # de test: un BAJA+1 de 202104 no esta en 202105, y un BAJA+2 de 202104 no esta
    # en 202106. Con gap 1 no: los BAJA+2 del train siguen presentes en el test, como
    # BAJA+1. El modelo los memorizo y los pone arriba de la lista, pero NO pagan,
    # asi que son costo puro y la ganancia sale pesimista.
    #
    # Sacarlos del test no es limpiar a favor: es lo que hace que una medicion con
    # gap 1 tenga la misma estructura que la entrega. Medido en 202105 -> 202106 son
    # 867 clientes, y ninguno de los 1,098 que pagan esta entre ellos.
    if cfg.get('excluir_positivos_del_train'):
        pos = set(data.loc[data['foto_mes'].isin(cfg['meses_train'])
                           & data['clase_ternaria'].isin(CLASES_POSITIVAS),
                           'numero_de_cliente'])
        en_test = data['foto_mes'] == cfg['mes_test']
        fuera = en_test & data['numero_de_cliente'].isin(pos)
        paga = data['clase_ternaria'] == 'BAJA+2'
        print(f'Excluidos del test {fuera.sum():,} de {en_test.sum():,} clientes por '
              f'haber sido positivos en el train ({(fuera & paga).sum()} de ellos '
              f'pagaban).')
        data = data[~fuera]

    features = resolver_features(data)
    semillas = semillas_del_curso(cfg['semillas'])

    print(f"\n=== {cfg['nombre']}")
    print(f"{cfg.get('pregunta', '(sin pregunta)')}")
    print(f"train {cfg['meses_train']} ({cfg.get('estrategia_meses', 'por_mes')}) "
          f"-> test {cfg['mes_test']} | {len(features)} features | "
          f'{len(semillas)} semillas\n')

# [Anotación · líneas 688–706] Corre la optimización y guarda las configuraciones elegidas en
#   `hiperparametros.json`. Entrena el ensamble con esas configuraciones y predice el mes de test. Con la marca
#   de `BAJA+2` calcula el corte y la ganancia máxima del ranking promedio y de cada modelo por separado, y
#   guarda la curva de ganancia en `curva_ganancia.csv` y `curva_ganancia.png`.
    configs = optimizar(data, features, cfg, fijos, buscados,
                        carpeta / 'optuna.db', carpeta)
    with open(carpeta / 'hiperparametros.json', 'w', encoding='utf-8') as fh:
        json.dump({'configs': configs}, fh, indent=2)

    print(f'\nReentrenando sobre el mes completo y midiendo en {cfg["mes_test"]}:')
    ranking, test, detalle = entrenar_ensemble(
        data, features, cfg, configs, cfg['mes_test'], semillas)
    es_baja2 = (test['clase_ternaria'] == 'BAJA+2').to_numpy()

    # El ensemble es lo que se entrega; el detalle por modelo es la barra de error.
    corte_ens, gan_ens = mejor_corte(ranking, es_baja2)
    por_modelo = [mejor_corte(d['ranking'], es_baja2) for d in detalle]
    gan_modelo = [g for _, g in por_modelo]

    curva = curva_en_grilla(ranking, es_baja2)
    curva.to_csv(carpeta / 'curva_ganancia.csv', index=False)
    graficar_curva(curva, carpeta / 'curva_ganancia.png',
                   f"{cfg['nombre']}: train {cfg['meses_train']} -> test {cfg['mes_test']}")

# [Anotación · líneas 708–742] Escribe `resultado.json` con nombre, pregunta, fecha, commit, meses, cantidad
#   de variables, configuraciones, AUC de la validación cruzada, gap, ganancia del ensamble, corte de máxima
#   ganancia, media y desvío de la ganancia por modelo, cantidad de modelos, segundos y versiones. Regenera
#   `experimentos.csv`, imprime el resumen y avisa si el corte queda fuera de 8.000–15.000.
    resultado = {
        'nombre': cfg['nombre'], 'pregunta': cfg.get('pregunta'),
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'carpeta': str(carpeta), 'git_commit': git_commit(),
        'meses_train': cfg['meses_train'],
        'estrategia_meses': cfg.get('estrategia_meses', 'por_mes'),
        'mes_test': cfg['mes_test'], 'n_features': len(features),
        'top_n': len(configs), 'configs': configs,
        'auc_cv': configs[0]['auc_cv'],
        'medicion_valida': cfg['mes_test'] not in cfg['meses_train'],
        'gap': cfg['mes_test'] - max(cfg['meses_train']),
        'excluir_positivos_del_train': bool(cfg.get('excluir_positivos_del_train')),
        'ganancia_ensemble': gan_ens, 'corte_optimo': corte_ens,
        'ganancia_media_modelo': float(np.mean(gan_modelo)),
        'sd_modelo': float(np.std(gan_modelo, ddof=1)) if len(gan_modelo) > 1 else None,
        'n_modelos': len(detalle), 'segundos': round(time.time() - arranque),
        'versiones': versiones(),
    }
    with open(carpeta / 'resultado.json', 'w', encoding='utf-8') as fh:
        json.dump(resultado, fh, indent=2, ensure_ascii=False)

    regenerar_log()

    sd = np.std(gan_modelo, ddof=1) if len(gan_modelo) > 1 else 0
    print(f'\n--- {cfg["nombre"]}')
    print(f'  AUC CV (mejor)      {configs[0]["auc_cv"]:.5f}')
    print(f'  modelos             {len(detalle)} '
          f'({len(configs)} configs x {len(semillas)} semillas x meses)')
    print(f'  ganancia ENSEMBLE   {gan_ens / 1e6:,.1f}M  en el corte {corte_ens:,}')
    print(f'  por modelo          {np.mean(gan_modelo) / 1e6:,.1f}M +- {sd / 1e6:,.1f}M')
    print(f'  carpeta             {carpeta}')
    if not MIN_REGISTROS <= corte_ens <= MAX_REGISTROS:
        print(f'\n  AVISO: el corte optimo ({corte_ens:,}) esta FUERA del rango que acepta '
              f'el bot [{MIN_REGISTROS:,}, {MAX_REGISTROS:,}].\n'
              '  La entrega lo va a recortar al limite mas cercano.')


# [Anotación · líneas 745–772] `modo_entrega`, inicio: exige `--desde` y verifica que la carpeta tenga
#   `resultado.json`, `hiperparametros.json` y `config.yaml`. Carga ese config, reemplaza la ruta del dataset si
#   se pasa `--dataset`, avisa si el config trae `mes_aplicacion` (se ignora) y lee las configuraciones de
#   hiperparámetros y el resultado del experimento.
def modo_entrega(args):
    """Entrega lo que midio UN experimento. Todo sale de su carpeta, nada del yaml actual.
    """
    if not args.desde:
        sys.exit('ERROR: --modo entrega necesita --desde <carpeta de experimentos/>')
    origen = Path(args.desde)
    ruta_res = origen / 'resultado.json'
    ruta_hp = origen / 'hiperparametros.json'
    ruta_config = origen / 'config.yaml'
    for r in (ruta_res, ruta_hp, ruta_config):
        if not r.exists():
            sys.exit(f'ERROR: no encuentro {r}')

    cfg, _, _ = cargar_config(ruta_config)
    if args.dataset:
        print(f"Dataset: {args.dataset} (el config del experimento decia "
              f"{cfg['dataset']})")
        cfg['dataset'] = args.dataset
    if 'mes_aplicacion' in cfg:
        print(f"AVISO: el config trae mes_aplicacion="
              f"{cfg['mes_aplicacion']}, se IGNORA; el script usa la "
              f"constante MES_APLICACION={MES_APLICACION}.")

    with open(ruta_hp, encoding='utf-8') as fh:
        hp = json.load(fh)
    with open(ruta_res, encoding='utf-8') as fh:
        res = json.load(fh)
    configs = hp['configs']

# [Anotación · líneas 774–798] Toma el corte de `corte_optimo` de `resultado.json`. Con `--corte` usa los
#   valores pasados (termina con error si alguno está fuera de 8.000–15.000); sin `--corte` lleva el corte
#   medido al límite más cercano de ese rango si queda fuera. Arma el nombre base de la entrega: `DU` + fecha y
#   hora + `nombre` del config.
    # El corte sale del experimento, no del config: es el optimo que midio la curva de
    # ganancia acumulada en el mes de test. Recortado al rango que acepta el bot.
    corte = int(res['corte_optimo'])
    nota_corte = ''
    if args.corte:
        fuera = [c for c in args.corte
                 if not MIN_REGISTROS <= c <= MAX_REGISTROS]
        if fuera:
            sys.exit(f'ERROR: los cortes {fuera} estan fuera del rango que acepta '
                     f'el bot [{MIN_REGISTROS:,}, {MAX_REGISTROS:,}]')
        cortes = sorted(set(args.corte))
        nota_corte = ', forzado por --corte'
        print(f'Cortes forzados por --corte: '
              f'{", ".join(f"{c:,}" for c in cortes)} '
              f'(el experimento habia medido {corte:,}).')
    else:
        ajustado = min(max(corte, MIN_REGISTROS), MAX_REGISTROS)
        if ajustado != corte:
            print(f'AVISO: el corte optimo medido es {corte:,}, fuera del rango del '
                  f'bot. Se usa {ajustado:,}.')
        cortes = [ajustado]

    sello = datetime.now().strftime('%Y%m%d%H%M')
    base = ''.join(ch for ch in f"DU{sello}{cfg['nombre']}"
                   if ch.isalnum() or ch in '_-')

# [Anotación · líneas 800–826] Lee los meses presentes en el parquet, obtiene los meses de entrenamiento de la
#   entrega con `meses_para_entrega` y avisa si el gap respecto de 202108 difiere del gap del experimento cuando
#   los meses no están declarados a mano. Carga esos meses más 202108, resuelve variables y semillas, y entrena
#   el ensamble con los meses de la entrega para puntuar 202108. Guarda los ids del mes de aplicación.
    # Todos los meses del dataset, para poder derivar el desplazamiento por posicion
    todos = pd.read_parquet(cfg['dataset'], columns=['foto_mes'])['foto_mes'].unique()
    meses_entrega = meses_para_entrega(cfg, todos)
    gap_entrega = sorted(todos).index(MES_APLICACION) - \
                  sorted(todos).index(max(meses_entrega))
    if gap_entrega != cfg['mes_test'] - max(cfg['meses_train']) and \
            not cfg.get('meses_train_entrega'):
        print(f'AVISO: el gap de la entrega ({gap_entrega}) no coincide con el del '
              f'experimento. Revisa meses_train_entrega.')

    meses = sorted(set(meses_entrega) | {MES_APLICACION})
    data = cargar_datos(cfg, meses)
    features = resolver_features(data)
    semillas = semillas_del_curso(cfg['semillas'])

    lista_cortes = ", ".join(f"{c:,}" for c in cortes)
    print(f"\n=== entrega {base}")
    print(f"train {meses_entrega} ({cfg.get('estrategia_meses', 'por_mes')}) "
          f"-> score {MES_APLICACION} (gap {gap_entrega}) | {len(features)} features | "
          f'{len(semillas)} semillas | {"cortes" if len(cortes) > 1 else "corte"} {lista_cortes}\n')

    cfg_entrega = dict(cfg)
    cfg_entrega['meses_train'] = meses_entrega
    _, aplicacion, detalle = entrenar_ensemble(
        data, features, cfg_entrega, configs, MES_APLICACION, semillas)
    ids_todos = aplicacion['numero_de_cliente'].to_numpy()
    validos = set(aplicacion['numero_de_cliente'].astype('int64'))

# [Anotación · líneas 828–839] Define cuántos modelos promedia cada archivo: todos si `--archivos` es 1; si
#   no, el mayor entre 4 y la mitad de los modelos. Con más de un archivo termina con error si ese número
#   alcanza al total de modelos entrenados.
    n_archivos = args.archivos
    # Un solo archivo es la entrega final (la catedra pide que el ultimo submit lleve
    # uno solo): promedia TODOS los modelos, no un subconjunto al azar.
    por_archivo = len(detalle) if n_archivos == 1 else max(4, len(detalle) // 2)

    if n_archivos > 1 and por_archivo >= len(detalle):
        sys.exit(
            f'ERROR: {len(detalle)} modelos entrenados no alcanzan para armar '
            f'{n_archivos} archivos con diversidad real.\n'
            f'  Cada archivo promedia {por_archivo} modelos, que es todo el conjunto.\n'
            f'  Subi semillas en el config a 16 o mas (con estrategia por_mes, los\n'
            f'  modelos son semillas x meses, asi que varios meses tambien suman).')

# [Anotación · líneas 841–865] Para cada corte crea la carpeta `entregas/<nombre>` y copia el config. Para
#   cada archivo promedia los rankings de sus modelos (todos, o un subconjunto elegido al azar con un generador
#   sembrado con 100019), ordena los clientes de mayor a menor y escribe los primeros `corte_usado` ids en
#   `<nombre>_m<NN>.csv` con `escribir_csv_entrega`.
    resumen = []
    for corte_usado in cortes:
        # Re-sembrado A PROPOSITO en cada corte: asi el archivo m07 del corte 9000
        # promedia los MISMOS modelos que el m07 del corte 13000, y las dos listas
        # quedan anidadas. Sin esto, cada corte tendria su propio ranking y las
        # diferencias entre cortes volverian a cargar el ruido entero del publico.
        rng = np.random.default_rng(SEMILLA_BASE)
        nombre = f'{base}_c{corte_usado}' if len(cortes) > 1 else base
        carpeta = DIR_ENTREGAS / nombre
        carpeta.mkdir(parents=True, exist_ok=True)
        shutil.copy(ruta_config, carpeta / 'config.yaml')

        print(f'\nEscribiendo {n_archivos} archivos de {corte_usado:,} registros en {carpeta}:')
        generados, miembros_por_archivo = [], []
        for i in range(1, n_archivos + 1):
            idx = (np.arange(len(detalle)) if n_archivos == 1 else
                   rng.choice(len(detalle), size=min(por_archivo, len(detalle)),
                              replace=False))
            sub = np.mean([detalle[j]['ranking'] for j in idx], axis=0)
            ids = ids_todos[np.argsort(sub, kind='stable')[::-1]][:corte_usado]
            ruta = carpeta / f'{nombre}_m{i:02d}.csv'
            n = escribir_csv_entrega(ids, ruta, validos)
            generados.append(ruta.name)
            miembros_por_archivo.append([int(detalle[j]['semilla']) for j in idx])
            print(f'  OK {ruta.name} ({n:,} registros, {len(idx)} modelos promediados)')

# [Anotación · líneas 867–887] En la carpeta de cada corte escribe `submit.txt` (texto `submit` + nombre),
#   `viene_de.txt` (carpeta de origen, AUC, trials usados, ganancia medida, corte medido y usado, meses medidos
#   y meses de la entrega, commit), `resultado_bot.txt` (plantilla para pegar la respuesta del bot) y
#   `detalle_archivos.json` (corte, modelos por archivo y semillas de cada archivo).
        cuerpo = f'submit    {nombre}'
        (carpeta / 'submit.txt').write_text(cuerpo + '\n', encoding='utf-8')
        (carpeta / 'viene_de.txt').write_text(
            f'hiperparametros y corte de: {origen}\n'
            f'auc_cv del mejor config: {configs[0]["auc_cv"]}\n'
            f'configs usados: {len(configs)}, trials {[c["trial"] for c in configs]}\n'
            f'ganancia_ensemble en {res["mes_test"]}: {res["ganancia_ensemble"]:,.0f}\n'
            f'corte optimo medido: {corte:,} (usado: {corte_usado:,}{nota_corte})\n'
            f'receta medida con: {cfg["meses_train"]} -> {cfg["mes_test"]}\n'
            f'entregada con:     {meses_entrega} -> {MES_APLICACION}\n'
            f'commit: {git_commit()}\n', encoding='utf-8')
        (carpeta / 'resultado_bot.txt').write_text(
            '# Pega aca la respuesta del bot cuando mandes el submit.\n'
            '# Sin esto, en dos semanas no vas a poder reconstruir que dio cada entrega.\n',
            encoding='utf-8')
        with open(carpeta / 'detalle_archivos.json', 'w', encoding='utf-8') as fh:
            json.dump({'corte': corte_usado, 'modelos_por_archivo': por_archivo,
                       'semillas_de_cada_archivo': dict(zip(generados,
                                                            miembros_por_archivo))},
                      fh, indent=2)
        resumen.append((corte_usado, cuerpo, carpeta, len(generados)))

# [Anotación · líneas 889–902] Imprime, para cada corte, el texto del mensaje, la cantidad de archivos y su
#   carpeta, con la indicación de enviarlos por mensaje privado a `@competencia-uno`.
    print('\n' + '=' * 78)
    print('PARA MANDAR: un mensaje privado a @competencia-uno POR CADA corte,')
    print('cada uno con su cuerpo exacto y sus archivos adjuntos.')
    print('=' * 78)
    for corte_usado, cuerpo, carpeta, n_gen in resumen:
        print(f'\n  corte {corte_usado:,}')
        print(f'      cuerpo : {cuerpo}')
        print(f'      {n_gen} archivos de: {carpeta}')
        print(f'      respuesta del bot -> {carpeta / "resultado_bot.txt"}')
    if len(resumen) > 1:
        print('\nSON SUBMITS SEPARADOS: el bot informa media y desvio de los archivos de')
        print('UN mensaje, asi que mandarlos juntos da un solo numero y se pierde el')
        print('barrido. Uno por mensaje = un numero por corte.')
    print('\nOJO: el ultimo submit antes del deadline es el final, automaticamente.')


# [Anotación · líneas 905–950] `main`: define los argumentos `--modo` (obligatorio: `experimento` o
#   `entrega`), `--config` (por defecto `config.yaml`), `--desde`, `--reanudar`, `--dataset`, `--corte` (uno o
#   varios enteros) y `--archivos` (por defecto 20). Con `--modo entrega` llama a `modo_entrega`; en otro caso
#   carga el config y llama a `modo_experimento`.
# --------------------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--modo', required=True, choices=['experimento', 'entrega'])
    parser.add_argument('--config', default='config.yaml',
                        help='solo para --modo experimento (default: ./config.yaml; pasale el de una carpeta de experimentos/ para repetir una corrida). La entrega ignora este flag: usa el config del experimento que indica --desde')
    parser.add_argument('--desde', help='carpeta de experimentos/ de donde tomar los '
                                        'hiperparametros y el corte (solo para --modo '
                                        'entrega)')
    parser.add_argument('--reanudar', action='store_true',
                        help='continua la ultima corrida que tenga el mismo `nombre` del '
                             'config, en lugar de abortar. Reusa su optuna.db, asi los '
                             'trials ya hechos no se repiten: sirve cuando se corto una '
                             'corrida larga o para sumarle trials subiendo `trials`')
    parser.add_argument('--dataset',
                        help='parquet con features, pisando la ruta del config del '
                             'experimento (solo --modo entrega)')
    parser.add_argument('--corte', type=int, nargs='+', metavar='N',
                        help='uno o varios cortes, pisando el optimo que midio el '
                             'experimento (solo --modo entrega). Con varios, entrena '
                             'UNA vez y escribe una carpeta por corte. Sirve para dos '
                             'cosas: barrer cortes del MISMO modelo, donde las listas '
                             'son subconjuntos anidados y el ruido del publico se '
                             'cancela en las diferencias; y entregar un experimento '
                             'cuyo mes_test cae dentro del train, donde el corte '
                             'medido no vale nada')
    parser.add_argument('--archivos', type=int, default=20,
                        help='cuantos .csv lleva el submit (default: 20). Es una '
                             'decision tactica del momento, no un parametro del '
                             'experimento, asi que vive aca y no en el yaml')
    args = parser.parse_args()

    pd.set_option('display.width', 200)

    if args.modo == 'entrega':
        # La entrega no mira el config del root: lee el del experimento que entrega.
        modo_entrega(args)
    else:
        cfg, fijos, buscados = cargar_config(args.config)
        modo_experimento(cfg, fijos, buscados, args.config, args)


if __name__ == '__main__':
    main()
```


## Explicaciones del alumno (texto original)

### competencia_01/README.md

> # Competencia 01
>
> Mi predicción de bajas de clientes para `202108`.
>
> ## Cómo correr
>
> Todos los comandos se corren desde esta carpeta (`competencia_01/`).
>
> **1. Crear el environment**
>
> ```
> conda env create -f env.yaml
> conda activate dmeyf-competencia-01
> ```
>
> **2. Generar el dataset con features**
>
> ```
> python fe_competencia_01.py --path <ruta>/competencia_01.csv
> ```
>
> `competencia_01.csv` es el dataset de la competencia con `clase_ternaria` ya calculada.
> El script deja `competencia_01_fe.parquet` en la misma carpeta que el CSV e imprime su
> ruta al terminar.
>
> **3. Generar la entrega**
>
> ```
> python modelar_competencia_01.py --modo entrega --desde experimentos/20261011_0840_tres_meses_v1_hess --archivos 1 --dataset <ruta>/competencia_01_fe.parquet
> ```
>
> Usa los hiperparámetros, el corte y la receta de meses del experimento de
> `experimentos/20261011_0840_tres_meses_v1_hess/`. El archivo final queda en
> `entregas/DU<fecha y hora>tres_meses_v1_hess/`, con una línea por cliente y sin
> encabezado.
>
> ## Qué tiene la entrega
>
> ### Target
>
> Binario: `BAJA+1` y `BAJA+2` son positivos, `CONTINUA` es negativo. La ganancia, en
> cambio, paga solo los `BAJA+2`: +1.072.500 por acierto y −27.500 por cada estímulo a
> otro cliente.
>
> ### Feature engineering (`fe_competencia_01.py`)
>
> Sobre las 155 columnas originales:
>
> - **Calidad de datos:** `ccajas_depositos` pasa a NULL en `202105`, donde viene en cero
>   para todos los clientes.
> - **Historia de 12 variables:** `ctrx_quarter`, `mrentabilidad`, `mcomisiones`,
>   `mcuentas_saldo`, `mpasivos_margen`, `mactivos_margen`, `mtarjeta_visa_consumo`,
>   `mtarjeta_master_consumo`, `cproductos`, `ctarjeta_visa_transacciones`, `mpayroll`,
>   `mcaja_ahorro`. A cada una:
>   - `lag_1`, `lag_2` y sus deltas contra el valor actual. El lag busca el mes
>     calendario exacto: si al cliente le falta un mes, queda NULL.
>   - `media_3`, `min_3`, `max_3` y `slope_3` (pendiente por mínimos cuadrados) sobre los
>     últimos 3 meses.
> - **Rankings dentro del mes** de las 9 variables de monto de la lista, para que el
>   modelo no dependa del nivel de precios de cada mes.
> - **Combinaciones:** saldo y consumo total de tarjetas (Visa + Master), consumo de
>   tarjetas sobre saldo, y comisiones sobre rentabilidad.
>
> En total, 109 features nuevas: 264 columnas, 261 de ellas usadas por el modelo.
>
> ### Meses
>
> - **Optimización:** `202103` a `202105` apilados.
> - **Entrega:** se reentrena con `202103` a `202106` y se predice `202108`.
>
> ### Optimización de hiperparámetros
>
> Optuna (TPE, 40 trials) maximizando el AUC promedio de una validación cruzada de 3
> folds. Los folds se parten por cliente (`StratifiedGroupKFold`), para que un mismo
> cliente no quede en train con un mes y en validación con otro.
>
> | parámetro | valor |
> |---|---|
> | `learning_rate` | 0.005 (fijo) |
> | `max_bin` | 31 (fijo) |
> | `min_data_in_leaf` | 0 (fijo) |
> | `feature_fraction` | 0.5 (fijo) |
> | `feature_fraction_bynode` | 0.2 (fijo) |
> | `num_leaves` | buscado en [4, 200] |
> | `num_iterations` | buscado en [200, 10000] |
> | `min_sum_hessian_in_leaf` | buscado en [0.0001, 100], escala log |
>
> Las tres mejores configuraciones:
>
> | trial | `num_leaves` | `num_iterations` | `min_sum_hessian_in_leaf` |
> |---|---|---|---|
> | 18 | 36 | 2375 | 19.22 |
> | 34 | 25 | 3760 | 17.61 |
> | 38 | 34 | 3627 | 17.38 |
>
> ### Ensemble y corte
>
> Las tres configuraciones se reentrenan con 5 semillas cada una: 15 modelos. Cada modelo
> convierte sus probabilidades en ranking percentil, y la predicción final es el promedio
> de los 15 rankings. Se estimula a los **10.160** clientes con mejor ranking, que es el
> corte de máxima ganancia medido en `202106`.
>
> ### Medición
>
> El modelo se midió entrenando con `202103`–`202105` y prediciendo `202106`. De
> `202106` se excluyeron los clientes que eran positivos en los meses de train: con un
> solo mes de distancia siguen presentes, el modelo los vio y no pagan, mientras que en la
> entrega real ya no estarían.

