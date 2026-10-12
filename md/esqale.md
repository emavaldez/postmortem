# Alejandro Esquivel — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: esqale
- Repositorio: https://github.com/esqale/dmeyf2026
- Link posteado: https://github.com/esqale/dmeyf2026/tree/main/monday/Competencia_1
- Commit: d17036e93460473b525ba51e60c9d520fb3761fb
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/esqale/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/esqale.json

## Resumen

La entrega es la carpeta monday/Competencia_1: un pipeline en Python de siete scripts (pasos/p0 a p6) que correr_todo.py lanza en orden, con los parámetros en config.py, funciones compartidas en lib/, los hiperparámetros versionados en params/, dos scripts de experimentos y tres textos (README, docs/DECISIONES.md, experimentos/RESULTADOS.md). El camino de la entrega descarga el crudo, arma clase_ternaria con DuckDB, pasa ccajas_depositos a NULL en 202105 y genera dos datasets: fe_base (sumas Visa+Master, cocientes, actividad digital, cantidad de productos, percent_rank dentro del mes de 6 variables y lag_1, delta_1, media y pendiente de 3 meses de 7 variables y de esos rankings) y fe_final (fe_base más lag_1 y delta_1 de todas las variables numéricas del crudo). Optuna busca 7 hiperparámetros de LightGBM en 30 trials de 3 semillas sobre fe_base, entrenando con 202103 y 202104 y midiendo la ganancia en 202106. La validación repite esa ventana con 10 semillas sobre fe_final. El modelo final entrena con 202103 a 202106 (positivo = BAJA+1 o BAJA+2), escala min_data_in_leaf por la cantidad de filas y usa 20 semillas cuyas probabilidades para 202108 se promedian; se escriben los 12.000 clientes de mayor promedio y se compara el SHA-256 del archivo con el registrado en config.py.

**Qué entrega.** Un CSV sin encabezado con 12.000 numero_de_cliente de 202108 (salida/entrega/competencia_01_entrega_n12000.csv): los de mayor probabilidad promedio de 20 semillas. El archivo no está en el repositorio; el README y config.py registran su SHA-256 (7dede71a1cf1…) y, según el README, obtuvo 107,47 en el leaderboard público.

**Cómo se ejecuta.** Según el README: `pip install -r requirements.txt` y luego `python correr_todo.py` (todo desde el crudo, ~2 h con 16 núcleos) o `python correr_todo.py --sin-busqueda` (usa params/mejores_params.json en vez de volver a buscar, ~1 h 20). Cada paso se puede correr suelto y en orden (pasos/p0_descargar.py a pasos/p6_entrega.py). correr_todo.py admite además --desde <paso> y --sin-validacion. El crudo se descarga a datos/ y todo lo generado queda en salida/. Los experimentos se corren con `python experimentos/variantes.py --variantes …` y `python experimentos/rf_linea_base.py`, después de p1 y p2.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: positivo = BAJA+1 o BAJA+2 (config.CLASES_POSITIVAS); la curva de ganancia cuenta como acierto sólo BAJA+2. La clase ternaria se arma en p1_target.py a partir del crudo.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica en el camino de la entrega: el modelo final entrena con todas las filas de 202103 a 202106. lib/modelo.py admite la opción 'undersampling', que sólo usa experimentos/variantes.py con 25% de CONTINUA por semilla.
- **Calidad de datos:** ccajas_depositos se pasa a NULL en 202105 (p2_features.py; el docstring indica que vale 0 para todos los clientes ese mes). Quedan fuera de las variables todas las columnas cuyo nombre contiene 'fultimo_cierre' o 'Finiciomora', incluidas sus derivadas (config.DRIFT y lib/datos.py). numero_de_cliente se convierte a BIGINT antes de pasar las columnas DOUBLE a float32.
- **Drifting:** percent_rank dentro de cada foto_mes de 6 variables (mrentabilidad, mcuentas_saldo, mtarjeta_visa_consumo, mtarjeta_master_consumo, mpayroll, ctrx_quarter), agregado como columnas rank_*; las variables originales se mantienen. Las columnas con 'fultimo_cierre' y 'Finiciomora' se excluyen de las variables.
- **Variables dentro del mes:** 20 variables nuevas en fe_base: 6 sumas Visa+Master (saldo total, consumo total, límite de compra, pagado, cantidad de consumos, adelantos en efectivo), suma de delinquency y menor Fvencimiento de las dos tarjetas; 6 cocientes con división que devuelve NULL si el denominador es 0 (consumo/límite de tarjetas, préstamos/saldo, rentabilidad/rentabilidad anual mensualizada, antigüedad/edad en meses, comisiones/rentabilidad, saldo/sueldo); 3 de actividad digital (canales activos, transacciones digitales, su cociente con ctrx_quarter); 3 conteos de productos (seguros, inversiones, préstamos).
- **Variables históricas:** Para 7 variables (ctrx_quarter, mcuentas_saldo, mtarjeta_visa_consumo, mtarjeta_master_consumo, mpayroll, mrentabilidad, cpayroll_trx) y para los 6 rankings: lag_1, delta_1, ma_3 (promedio de la fila actual y las 2 anteriores del cliente) y slope_3 (regr_slope contra cliente_antiguedad en esa ventana). En fe_final se agregan lag_1 y delta_1 de todas las demás columnas numéricas del crudo. Las ventanas cuentan filas del cliente ordenadas por foto_mes. config.MA3_COMPLETO = False deja apagada la anulación de ma_3/slope_3 con menos de 3 meses.
- **Selección de variables:** No se observa selección por importancia. La lista de variables es: todas las columnas del dataset menos clase_ternaria, foto_mes, numero_de_cliente y las que contienen 'fultimo_cierre' o 'Finiciomora'. Según experimentos/RESULTADOS.md son 226 en fe_base y 508 en fe_final.
- **Optimización de hiperparámetros:** Optuna con TPESampler (semilla = primera del pool), 30 trials guardados en sqlite, sobre fe_base. Cada trial entrena 3 semillas con 202103+202104, promedia las probabilidades de 202106 y devuelve el máximo de la curva de ganancia suavizada (media móvil centrada de 3 cortes, cortes de 8.000 a 15.000 cada 500). Espacio: num_leaves 8–512, learning_rate 0,005–0,1, num_boost_round 100–1.500, min_data_in_leaf 20–4.000, lambda_l2 0,001–100 (todos en escala logarítmica), feature_fraction 0,1–0,9 y bagging_fraction 0,5–1,0.
- **Hiperparámetros finales:** params/mejores_params.json: num_leaves 108, learning_rate 0,010927, num_boost_round 1180, min_data_in_leaf 230, feature_fraction 0,3383, bagging_fraction 0,7249, lambda_l2 0,1681. En el modelo final min_data_in_leaf se multiplica por filas de 202103–202106 / filas de 202103–202104 (230 → 461 según docs/DECISIONES.md). Fijos en config.py: objective binary, gbdt, max_bin 31, bagging_freq 1, boost_from_average True, feature_pre_filter False, deterministic True, force_col_wise True, 16 hilos. Sin conjunto de validación ni early stopping en lgb.train.
- **Semillas:** Pool determinístico: np.random.RandomState(17).choice(1_000_000, size=50, replace=False); cada uso toma las primeras n: 3 por trial de Optuna, 10 en validación, 20 en el modelo final. La semilla se pasa a los parámetros de LightGBM y al lgb.Dataset, que se construye de nuevo para cada semilla.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio de las probabilidades de 20 LightGBM entrenados con los mismos datos e hiperparámetros y distinta semilla (p5_modelo_final.py guarda una columna por semilla y p6_entrega.py las promedia).
- **Corte:** Cantidad fija: config.N_ENVIOS = 12.000 clientes de mayor probabilidad promedio. p4_validacion.py calcula sobre 202106 el N de la curva media suavizada y la meseta (cortes a menos de 2.000.000 del máximo) e informa si 12.000 cae dentro. Según docs/DECISIONES.md (D12), la meseta de validación va de 11.000 a 13.000 y se toma su centro; el mismo texto cita mediciones en el leaderboard público con 10.500, 11.500, 12.500 y 13.500 envíos.
- **Validación:** Un mes posterior con dos meses de distancia: entrena con 202103+202104 y mide en 202106 sobre fe_final, con 10 semillas. Por semilla calcula la ganancia (1.072.500 por BAJA+2 y −27.500 por cualquier otro) en 15 cortes de 8.000 a 15.000; el resumen da N de la curva media suavizada, media, desvío, mínimo y meseta. Según el README: 421,0M de media y 5,5M de desvío. Las variantes de experimentos/ se comparan de a pares por semilla con la regla 'mejora media ≥ 5M y gana en ≥ 7 de 10'.
- **Salidas:** En salida/ (fuera del repositorio): datasets/competencia_01_clase.parquet, competencia_01_fe_base.parquet y competencia_01_fe_final.parquet; busqueda/optuna.db, trials.csv y mejores_params.json; validacion/por_semilla.csv y resumen.json; modelo_final/config.json y probabilidades_202108.parquet (una columna por semilla); entrega/competencia_01_entrega_n12000.csv y, con --por-semilla, un CSV por semilla.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Técnicas sólo exploradas

- Random Forest (`modelo.random_forest`)
- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Tres clases (CONTINUA, BAJA+1, BAJA+2) (`clase.multiclase`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Genera archivos con varios cortes (`corte.varios_cortes`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README y requirements.txt: Python 3.13, LightGBM 4.7.0, duckdb 1.5.5, numpy 2.2.4, optuna 4.9.0, pandas 2.2.3, pyarrow 22.0.0 y scikit-learn 1.9.0, con 16 hilos fijos; el README indica ~2 h con 16 núcleos para la corrida completa. No se declara sistema operativo ni memoria.

## Pasos del camino de la entrega

1. **Parámetros de la corrida.** config.py reúne rutas relativas a la carpeta de la entrega, constantes de ganancia (1.072.500 y 27.500), cortes de 8.000 a 15.000 cada 500, N = 12.000, meses de la ventana de desarrollo (202103, 202104 → 202106) y del modelo final (202103–202106 → 202108), listas de variables, cantidades de semillas (3, 10 y 20), parámetros fijos de LightGBM, espacio de Optuna (30 trials) y el SHA-256 del archivo entregado. (`monday/Competencia_1/config.py` líneas 1–93)
2. **Orquestación de los pasos.** correr_todo.py ejecuta en orden, cada uno como subproceso, p0_descargar, p1_target, p2_features, p3_busqueda, p4_validacion, p5_modelo_final y p6_entrega. --desde arranca en un paso posterior; --sin-busqueda y --sin-validacion saltean p3 y p4. (`monday/Competencia_1/correr_todo.py` líneas 21–39)
3. **Descarga del crudo.** Si datos/competencia_01_crudo.csv no existe, lo descarga de la URL del bucket de la cátedra escrita en config.URL_CRUDO. (`monday/Competencia_1/pasos/p0_descargar.py` líneas 14–21; `monday/Competencia_1/config.py` líneas 10–11)
4. **Armado de clase_ternaria.** Con DuckDB lee el CSV, numera los meses (año × 12 + mes) y mira las dos filas siguientes de cada cliente: BAJA+1 si no está en el mes siguiente, BAJA+2 si está en el siguiente y no en el subsiguiente, CONTINUA si está en ambos; el último mes queda sin clase y en el anteúltimo sólo se asigna BAJA+1 (el resto queda sin clase). Guarda competencia_01_clase.parquet. (`monday/Competencia_1/pasos/p1_target.py` líneas 20–61)
5. **Limpieza de datos.** Pasa ccajas_depositos a NULL en 202105. Al armar la lista de variables se excluyen clase_ternaria, foto_mes, numero_de_cliente y toda columna cuyo nombre contenga 'fultimo_cierre' o 'Finiciomora'. (`monday/Competencia_1/pasos/p2_features.py` líneas 141–142; `monday/Competencia_1/lib/datos.py` líneas 47–48; `monday/Competencia_1/config.py` líneas 40–42)
6. **Variables de fe_base.** En una consulta SQL agrega: percent_rank dentro del mes de 6 variables; 8 variables de tarjetas combinadas Visa+Master; 6 cocientes; 3 variables de actividad digital; 3 conteos de productos; y lag_1, delta_1, ma_3 y slope_3 (ventana de 3 filas por cliente) de 7 variables nominales y de los 6 rankings. Guarda competencia_01_fe_base.parquet, el dataset de la búsqueda de hiperparámetros. (`monday/Competencia_1/pasos/p2_features.py` líneas 27–90; `monday/Competencia_1/pasos/p2_features.py` líneas 144–146)
7. **lag_1 y delta_1 de todas las variables (fe_final).** Para cada columna numérica del crudo que no está en las 7 de tendencia agrega el valor de la fila anterior del cliente y la diferencia con él. El paso opcional que anula ma_3 y slope_3 con menos de 3 filas de historia no se ejecuta porque config.MA3_COMPLETO es False. Guarda competencia_01_fe_final.parquet, el dataset del modelo entregado. (`monday/Competencia_1/pasos/p2_features.py` líneas 93–127; `monday/Competencia_1/pasos/p2_features.py` líneas 148–153)
8. **Carga de datos, variables y semillas.** lib/datos.py lee del parquet los meses pedidos ordenados por foto_mes y numero_de_cliente, deja el id como entero y baja las columnas float64 a float32; arma la lista de variables; y devuelve las primeras n semillas de un pool de 50 generado con RandomState(17). (`monday/Competencia_1/lib/datos.py` líneas 18–48)
9. **Entrenamiento de un LightGBM por semilla.** entrenar_predecir arma la etiqueta binaria (1 si la clase es BAJA+1 o BAJA+2), construye un lgb.Dataset nuevo con la semilla y max_bin 31, entrena num_boost_round rondas con los parámetros fijos de config más los 6 buscados y devuelve las probabilidades del conjunto a predecir. (`monday/Competencia_1/lib/modelo.py` líneas 15–47; `monday/Competencia_1/config.py` líneas 60–75)
10. **Métrica: curva de ganancia por cantidad de envíos.** Ordena por probabilidad descendente, asigna 1.072.500 a cada BAJA+2 y −27.500 al resto, acumula y lee la ganancia en los 15 cortes de 8.000 a 15.000. La curva se suaviza con media móvil centrada de 3 cortes; el resumen por semillas da N, media, desvío, mínimo y meseta (cortes a menos de 2.000.000 del máximo). (`monday/Competencia_1/lib/ganancia.py` líneas 8–30; `monday/Competencia_1/config.py` líneas 25–29)
11. **Búsqueda de hiperparámetros con Optuna.** Sobre fe_base, entrenando con 202103+202104 y midiendo en 202106: 30 trials con TPE; cada trial promedia las probabilidades de 3 semillas y devuelve el máximo de la curva de ganancia suavizada. Escribe trials.csv y mejores_params.json en salida/busqueda/ e informa si coinciden con params/mejores_params.json. Con --sin-busqueda este paso se saltea y se usan los versionados. (`monday/Competencia_1/pasos/p3_busqueda.py` líneas 26–74; `monday/Competencia_1/config.py` líneas 78–89; `monday/Competencia_1/params/mejores_params.json` líneas 1–9)
12. **Validación en 202106 con 10 semillas.** Sobre fe_final y con los hiperparámetros elegidos, entrena 10 semillas con 202103+202104 y calcula la curva de ganancia de cada una en 202106. Guarda por_semilla.csv y resumen.json e informa si N = 12.000 cae dentro de la meseta. El docstring indica que este paso no es necesario para generar la entrega. (`monday/Competencia_1/pasos/p4_validacion.py` líneas 25–52)
13. **Modelo final: 202103–202106 → 202108, 20 semillas.** Entrena con los cuatro meses con clase sobre fe_final, con min_data_in_leaf multiplicado por filas de entrenamiento final / filas de 202103–202104. Para cada una de las 20 semillas predice 202108 y agrega una columna a probabilidades_202108.parquet, que se reescribe tras cada semilla; si el archivo ya tiene una semilla, no la repite. (`monday/Competencia_1/pasos/p5_modelo_final.py` líneas 31–58; `monday/Competencia_1/lib/modelo.py` líneas 8–12)
14. **Archivo de entrega y verificación.** Promedia las columnas de semillas, toma los 12.000 clientes de mayor promedio y escribe sus numero_de_cliente como enteros sin encabezado. Verifica formato, cantidad de filas, ids únicos y existentes en 202108; calcula el SHA-256 y lo compara con config.SHA256_ENTREGADO. (`monday/Competencia_1/pasos/p6_entrega.py` líneas 26–59; `monday/Competencia_1/config.py` líneas 91–93)

## Archivos

- `monday/Competencia_1/config.py` · configuracion · Python · 93 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/config.py.txt) — Parámetros de todo el pipeline: rutas, constantes de ganancia, cortes, N, meses, listas de variables, semillas, parámetros fijos de LightGBM, espacio de búsqueda de Optuna y SHA-256 del archivo entregado. Lo importan todos los scripts de pasos/, lib/ y experimentos/.
- `monday/Competencia_1/requirements.txt` · configuracion · Texto · 8 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/requirements.txt.txt) — Dependencias con versión exacta: duckdb 1.5.5, lightgbm 4.7.0, numpy 2.2.4, optuna 4.9.0, pandas 2.2.3, pyarrow 22.0.0 y scikit-learn 1.9.0; la primera línea indica Python 3.13.
- `monday/Competencia_1/correr_todo.py` · principal · Python · 43 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/correr_todo.py.txt) — Lanza los siete scripts de pasos/ en orden, uno por vez, como subprocesos; permite arrancar desde un paso y saltear la búsqueda o la validación.
- `monday/Competencia_1/README.md` · explicacion · Markdown · 94 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/README.md.txt) — Texto de presentación: qué se predice, archivo entregado con su SHA-256, puntaje público (107,47) y validación (421,0M de media, desvío 5,5M, 10 semillas) declarados, comandos para correr todo o cada paso con sus tiempos, estructura de carpetas, tabla con las elecciones del modelo, tabla de variantes probadas que no entraron y una sección de reproducibilidad con versiones.
- `monday/Competencia_1/pasos/p0_descargar.py` · principal · Python · 25 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/pasos/p0_descargar.py.txt) — Descarga el dataset crudo de la cátedra a datos/ si todavía no está.
- `monday/Competencia_1/pasos/p2_features.py` · principal · Python · 157 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/pasos/p2_features.py.txt) — Aplica la limpieza de ccajas_depositos y genera con SQL en DuckDB los dos datasets de variables: fe_base (usado en la búsqueda de hiperparámetros) y fe_final (usado en la validación y en el modelo entregado).
- `monday/Competencia_1/pasos/p3_busqueda.py` · principal · Python · 78 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/pasos/p3_busqueda.py.txt) — Búsqueda de hiperparámetros de LightGBM con Optuna sobre fe_base, con entrenamiento en 202103+202104 y medición en 202106; escribe el resultado en salida/busqueda/ y lo compara con params/mejores_params.json.
- `monday/Competencia_1/pasos/p4_validacion.py` · principal · Python · 56 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/pasos/p4_validacion.py.txt) — Mide el modelo en la ventana de desarrollo: 10 semillas sobre fe_final entrenando con 202103+202104 y prediciendo 202106; guarda la curva de ganancia por semilla y un resumen, e informa si N = 12.000 cae dentro de la meseta.
- `monday/Competencia_1/pasos/p1_target.py` · principal · Python · 65 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/pasos/p1_target.py.txt) — Lee el crudo con DuckDB, calcula clase_ternaria (BAJA+1, BAJA+2, CONTINUA o NULL) y guarda el resultado en salida/datasets/competencia_01_clase.parquet.
- `monday/Competencia_1/pasos/p5_modelo_final.py` · principal · Python · 62 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/pasos/p5_modelo_final.py.txt) — Entrena el modelo final con 202103–202106 sobre fe_final, una vez por semilla (20 por defecto), y guarda la probabilidad de cada cliente de 202108 por semilla en salida/modelo_final/probabilidades_202108.parquet.
- `monday/Competencia_1/pasos/p6_entrega.py` · principal · Python · 70 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/pasos/p6_entrega.py.txt) — Promedia las probabilidades por semilla, escribe el CSV con los N clientes de mayor promedio (12.000 por defecto), lo verifica y compara su SHA-256 con el del archivo entregado; opcionalmente escribe un archivo por semilla.
- `monday/Competencia_1/docs/DECISIONES.md` · explicacion · Markdown · 83 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/docs/DECISIONES.md.txt) — Dieciséis decisiones numeradas (D1 a D16) con su justificación: qué se predice, meses utilizables, ventana de desarrollo, clase binaria, limpieza, búsqueda de hiperparámetros, regla de adopción de variantes (mejora media ≥ 5M y ≥ 7 de 10 semillas), variables del modelo entregado, corte N = 12.000, modelo final, reproducibilidad, limitaciones declaradas (D15) y la variante ma_3/slope_3 no adoptada.
- `monday/Competencia_1/params/mejores_params.json` · configuracion · JSON · 9 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/params/mejores_params.json.txt) — Hiperparámetros del modelo entregado: num_leaves 108, learning_rate 0,010927, num_boost_round 1180, min_data_in_leaf 230, feature_fraction 0,3383, bagging_fraction 0,7249, lambda_l2 0,1681. lib/datos.py los usa cuando no existe salida/busqueda/mejores_params.json.
- `monday/Competencia_1/lib/datos.py` · principal · Python · 56 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/lib/datos.py.txt) — Funciones compartidas por los pasos y los experimentos: registro con tiempo transcurrido, pool de semillas, carga de meses desde un parquet, ids de un mes, lista de variables y lectura de los hiperparámetros.
- `monday/Competencia_1/lib/modelo.py` · principal · Python · 47 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/lib/modelo.py.txt) — Entrenamiento y predicción de un LightGBM para una semilla, armado de sus parámetros y escalado de min_data_in_leaf según la cantidad de filas.
- `monday/Competencia_1/lib/ganancia.py` · principal · Python · 39 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/lib/ganancia.py.txt) — Cálculo de la ganancia por cantidad de envíos, suavizado de la curva, resumen entre semillas (N, media, desvío, mínimo, meseta) y comparación pareada entre variantes.
- `monday/Competencia_1/experimentos/variantes.py` · secundario · Python · 241 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/experimentos/variantes.py.txt) — Mide 9 variantes de LightGBM en la ventana 202103+202104 → 202106 con 10 semillas y las compara con la referencia (fe_final con los hiperparámetros versionados); con --final entrena el modelo final de una variante de dataset. Según su docstring, ninguna entró al modelo entregado.
- `monday/Competencia_1/experimentos/RESULTADOS.md` · explicacion · Markdown · 66 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/experimentos/RESULTADOS.md.txt) — Registro de experimentos: tabla de las variantes de LightGBM medidas en la ventana 202103+202104 → 202106 con 10 semillas (ganancia media, diferencia con la referencia, semillas ganadas y decisión), resultado del Random Forest de referencia (394,0M según el archivo), ganancia pública declarada para 10.500, 11.500, 12.000, 12.500 y 13.500 envíos y el desempate de la variante ma_3/slope_3 en el leaderboard público.
- `monday/Competencia_1/experimentos/rf_linea_base.py` · secundario · Python · 104 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/esqale/monday/Competencia_1/experimentos/rf_linea_base.py.txt) — Random Forest de scikit-learn con clase ternaria sobre fe_base: búsqueda de 4 hiperparámetros con Optuna usando la probabilidad OOB de 202104 y validación 202104 → 202106 con 5 semillas. Su docstring indica que no entra en la entrega.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### monday/Competencia_1/correr_todo.py

Lanza los siete scripts de pasos/ en orden, uno por vez, como subprocesos; permite arrancar desde un paso y saltear la búsqueda o la validación.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–15] El docstring lista los siete pasos con lo que hace cada uno y sus tiempos, y tres
#   formas de uso: todo, --sin-busqueda (usa params/mejores_params.json) y --desde <paso>.
"""Corre el pipeline completo, un paso por vez (sin paralelizar: LightGBM usa todos los nucleos).

  p0_descargar     crudo de la catedra -> datos/
  p1_target        clase_ternaria
  p2_features      fe_base y fe_final
  p3_busqueda      Optuna sobre fe_base (~45 min)
  p4_validacion    10 semillas en 202103-04 -> 202106 (~15 min)
  p5_modelo_final  202103-06 -> 202108, 20 semillas (~60 min)
  p6_entrega       promedio, top N, verificacion y SHA-256

Uso:
  python correr_todo.py                    todo (~2 h)
  python correr_todo.py --sin-busqueda     sin p3: usa params/mejores_params.json (~1 h 20)
  python correr_todo.py --desde p5         desde un paso en adelante
"""
# [Anotación · líneas 16–21] Importa argparse, subprocess, sys y Path, y define la lista PASOS con los siete
#   nombres de script en orden de ejecución.
import argparse
import subprocess
import sys
from pathlib import Path

PASOS = ["p0_descargar", "p1_target", "p2_features", "p3_busqueda", "p4_validacion", "p5_modelo_final", "p6_entrega"]


# [Anotación · líneas 24–29] Define los argumentos --desde (por defecto p0_descargar), --sin-busqueda y --sin-
#   validacion.
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", choices=PASOS, default=PASOS[0])
    ap.add_argument("--sin-busqueda", action="store_true", help="saltea p3 y usa los hiperparametros versionados")
    ap.add_argument("--sin-validacion", action="store_true", help="saltea p4")
    args = ap.parse_args()

# [Anotación · líneas 31–39] Recorta la lista desde el paso indicado, quita p3_busqueda o p4_validacion si se
#   pidió y ejecuta cada paso con el mismo intérprete de Python en la carpeta de la entrega; check=True detiene
#   la corrida si un paso termina con código distinto de cero.
    raiz = Path(__file__).resolve().parent
    pasos = PASOS[PASOS.index(args.desde):]
    if args.sin_busqueda:
        pasos = [p for p in pasos if p != "p3_busqueda"]
    if args.sin_validacion:
        pasos = [p for p in pasos if p != "p4_validacion"]
    for paso in pasos:
        print(f"\n===== {paso} =====", flush=True)
        subprocess.run([sys.executable, "-u", str(raiz / "pasos" / f"{paso}.py")], cwd=raiz, check=True)


# [Anotación · líneas 42–43] Punto de entrada: llama a main() cuando el archivo se ejecuta como script.
if __name__ == "__main__":
    main()
```

### monday/Competencia_1/pasos/p0_descargar.py

Descarga el dataset crudo de la cátedra a datos/ si todavía no está.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–11] Docstring e importaciones; agrega la carpeta de la entrega a sys.path para
#   importar config y la función log de lib/datos.py.
"""Paso 0: descarga el dataset crudo de la catedra (si no esta ya en datos/).

Uso:  python pasos/p0_descargar.py
"""
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from lib.datos import log  # noqa: E402


# [Anotación · líneas 14–21] Si datos/competencia_01_crudo.csv ya existe, lo informa y termina. Si no, crea
#   datos/, descarga el archivo desde config.URL_CRUDO con urllib.request.urlretrieve e informa su tamaño en MB.
def main():
    if config.CRUDO.exists():
        log(f"ya existe {config.CRUDO.relative_to(config.RAIZ)}, no se descarga")
        return
    config.DATOS.mkdir(parents=True, exist_ok=True)
    log(f"descargando {config.URL_CRUDO}")
    urllib.request.urlretrieve(config.URL_CRUDO, config.CRUDO)
    log(f"listo -> {config.CRUDO.relative_to(config.RAIZ)} ({config.CRUDO.stat().st_size / 1e6:.0f} MB)")


# [Anotación · líneas 24–25] Punto de entrada: llama a main() cuando el archivo se ejecuta como script.
if __name__ == "__main__":
    main()
```

### monday/Competencia_1/pasos/p2_features.py

Aplica la limpieza de ccajas_depositos y genera con SQL en DuckDB los dos datasets de variables: fe_base (usado en la búsqueda de hiperparámetros) y fe_final (usado en la validación y en el modelo entregado).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–24] El docstring describe los dos datasets (fe_base y fe_final) y la limpieza de
#   ccajas_depositos en 202105. Importa duckdb, config y log.
"""Paso 2: limpieza y feature engineering -> dos datasets.

  fe_base   features de clase4 (z402): tarjetas combinadas Visa+Master, ratios con division
            segura, actividad digital, cantidad de productos, ranking dentro del mes (contra la
            inflacion) y tendencias por cliente (lag_1, delta_1, ma_3, slope_3) de 7 variables,
            nominales y sobre el ranking. Es el dataset de la busqueda de hiperparametros.
  fe_final  fe_base + lag_1 y delta_1 de TODAS las variables numericas del crudo.
            Si config.MA3_COMPLETO: ma_3 y slope_3 en NULL cuando el cliente tiene menos de 3
            meses de historia (en 202103-04 promediaban 1 o 2 meses).
            Es el dataset del modelo entregado (docs/DECISIONES.md, D10).

Limpieza: ccajas_depositos vale 0 para todos los clientes en 202105 (en el resto de los meses
hay entre 800 y 6.500 con valor): es un error de datos -> NULL.

Uso:  python pasos/p2_features.py
"""
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from lib.datos import log  # noqa: E402


# [Anotación · líneas 27–39] sql_fe_base arma tres fragmentos de SQL a partir de las listas de config:
#   percent_rank dentro de cada foto_mes para las 6 variables de CAMPOS_RANK (rank_*); para las 7 de
#   CAMPOS_TENDENCIA, lag_1, delta_1, ma_3 (promedio en la ventana de 3 filas) y slope_3 (regr_slope contra
#   cliente_antiguedad en esa ventana); y las mismas cuatro variables sobre cada rank_*.
def sql_fe_base():
    rank = "".join(f"\n        , percent_rank() OVER (PARTITION BY foto_mes ORDER BY {c}) AS rank_{c}"
                   for c in config.CAMPOS_RANK)
    tend = "".join(f"""
    , lag({c}, 1) OVER ventana_cliente AS lag_1_{c}
    , {c} - lag({c}, 1) OVER ventana_cliente AS delta_1_{c}
    , avg({c}) OVER ventana_3m AS ma_3_{c}
    , regr_slope({c}, cliente_antiguedad) OVER ventana_3m AS slope_3_{c}""" for c in config.CAMPOS_TENDENCIA)
    tend_rank = "".join(f"""
    , lag(rank_{c}, 1) OVER ventana_cliente AS lag_1_rank_{c}
    , rank_{c} - lag(rank_{c}, 1) OVER ventana_cliente AS delta_1_rank_{c}
    , avg(rank_{c}) OVER ventana_3m AS ma_3_rank_{c}
    , regr_slope(rank_{c}, cliente_antiguedad) OVER ventana_3m AS slope_3_rank_{c}""" for c in config.CAMPOS_RANK)
# [Anotación · líneas 40–48] Define dos macros: suma_sin_null (suma tomando NULL como 0) y ratio_seguro
#   (división que da NULL cuando el denominador es 0). Inicia la tabla competencia_01_fe a partir de una
#   subconsulta que agrega los rankings a todas las columnas.
    return f"""
CREATE OR REPLACE MACRO suma_sin_null(a, b) AS ifnull(a, 0) + ifnull(b, 0);
CREATE OR REPLACE MACRO ratio_seguro(a, b) AS a / nullif(b, 0);

CREATE OR REPLACE TABLE competencia_01_fe AS
WITH base_rank AS (
    SELECT c.* {rank}
    FROM competencia_01 c
)
# [Anotación · líneas 49–59] Tarjetas combinadas: suma Visa + Master de saldo total, consumo total, límite de
#   compra, pagado, cantidad de consumos y adelantos en efectivo; tc_cantidad_mora suma los dos delinquency y
#   tc_fvencimiento_menor toma el menor de los dos Fvencimiento.
SELECT
    br.*
    -- tarjetas combinadas (Visa + Master)
    , suma_sin_null(Visa_msaldototal, Master_msaldototal) AS tc_msaldototal
    , suma_sin_null(Visa_mconsumototal, Master_mconsumototal) AS tc_mconsumototal
    , suma_sin_null(Visa_mlimitecompra, Master_mlimitecompra) AS tc_mlimitecompra
    , suma_sin_null(Visa_mpagado, Master_mpagado) AS tc_mpagado
    , suma_sin_null(Visa_cconsumos, Master_cconsumos) AS tc_cconsumos
    , suma_sin_null(Visa_cadelantosefectivo, Master_cadelantosefectivo) AS tc_cadelantosefectivo
    , ifnull(Visa_delinquency, 0) + ifnull(Master_delinquency, 0) AS tc_cantidad_mora
    , least(Visa_Fvencimiento, Master_Fvencimiento) AS tc_fvencimiento_menor
# [Anotación · líneas 60–68] Seis cocientes: consumo sobre límite de tarjetas; suma de préstamos personales,
#   prendarios e hipotecarios sobre mcuentas_saldo; mrentabilidad sobre mrentabilidad_annual / 12;
#   cliente_antiguedad sobre cliente_edad × 12; mcomisiones sobre mrentabilidad; mcuentas_saldo sobre mpayroll.
    -- ratios de riesgo / uso
    , ratio_seguro(suma_sin_null(Visa_mconsumototal, Master_mconsumototal),
                   suma_sin_null(Visa_mlimitecompra, Master_mlimitecompra)) AS r_uso_limite_tc
    , ratio_seguro(ifnull(mprestamos_personales, 0) + ifnull(mprestamos_prendarios, 0)
                   + ifnull(mprestamos_hipotecarios, 0), mcuentas_saldo) AS r_endeudamiento_saldo
    , ratio_seguro(mrentabilidad, mrentabilidad_annual / 12.0) AS r_rentabilidad_vs_anual
    , ratio_seguro(cliente_antiguedad, cliente_edad * 12) AS r_antiguedad_vida
    , ratio_seguro(mcomisiones, mrentabilidad) AS r_comisiones_vs_rentabilidad
    , ratio_seguro(mcuentas_saldo, mpayroll) AS r_saldo_vs_sueldo
# [Anotación · líneas 69–81] Actividad digital: cantidad de canales activos (internet, thomebanking,
#   tmobile_app, tcallcenter), total de transacciones por homebanking, app y call center, y ese total sobre
#   ctrx_quarter. Productos: suma de 4 seguros, de 3 inversiones (cinversion1, cinversion2, cplazo_fijo) y de 3
#   tipos de préstamo.
    -- actividad digital
    , ifnull(internet, 0) + ifnull(thomebanking, 0) + ifnull(tmobile_app, 0) + ifnull(tcallcenter, 0)
        AS dig_canales_activos
    , ifnull(chomebanking_transacciones, 0) + ifnull(cmobile_app_trx, 0) + ifnull(ccallcenter_transacciones, 0)
        AS dig_trx_total
    , ratio_seguro(ifnull(chomebanking_transacciones, 0) + ifnull(cmobile_app_trx, 0)
                   + ifnull(ccallcenter_transacciones, 0), ctrx_quarter) AS dig_ratio_trx
    -- cantidad de productos
    , ifnull(cseguro_vida, 0) + ifnull(cseguro_auto, 0) + ifnull(cseguro_vivienda, 0)
      + ifnull(cseguro_accidentes_personales, 0) AS prod_total_seguros
    , ifnull(cinversion1, 0) + ifnull(cinversion2, 0) + ifnull(cplazo_fijo, 0) AS prod_total_inversiones
    , ifnull(cprestamos_personales, 0) + ifnull(cprestamos_prendarios, 0) + ifnull(cprestamos_hipotecarios, 0)
        AS prod_total_prestamos
# [Anotación · líneas 82–90] Inserta los fragmentos de tendencias (nominales y sobre el ranking) y define las
#   ventanas: ventana_cliente (filas del cliente ordenadas por foto_mes) y ventana_3m (la fila actual y las 2
#   anteriores del cliente).
    -- tendencia temporal por cliente (valor nominal)
    {tend}
    -- tendencia temporal por cliente (sobre el ranking, sin efecto inflacion)
    {tend_rank}
FROM base_rank br
WINDOW
    ventana_cliente AS (PARTITION BY numero_de_cliente ORDER BY foto_mes),
    ventana_3m AS (PARTITION BY numero_de_cliente ORDER BY foto_mes ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
"""


# [Anotación · líneas 93–96] columnas_numericas devuelve las columnas de tipo numérico de la tabla
#   competencia_01, sin numero_de_cliente ni foto_mes.
def columnas_numericas(con):
    tipos = ("BIGINT", "INTEGER", "DOUBLE", "FLOAT", "DECIMAL", "HUGEINT", "SMALLINT", "TINYINT")
    return [nombre for nombre, tipo, *_ in con.execute("DESCRIBE competencia_01").fetchall()
            if nombre not in ("numero_de_cliente", "foto_mes") and tipo.startswith(tipos)]


# [Anotación · líneas 99–114] sql_lags_todas genera, para cada columna numérica que no está en
#   CAMPOS_TENDENCIA, lag_1_<columna> y delta_1_<columna> (valor menos el de la fila anterior del cliente) y
#   reconstruye competencia_01_fe con esas columnas agregadas.
def sql_lags_todas(numericas):
    """lag_1 y delta_1 de todas las variables numericas del crudo (las 7 de CAMPOS_TENDENCIA ya estan)."""
    cols = []
    for c in numericas:
        if c in config.CAMPOS_TENDENCIA:
            continue
        cols += [f"lag({c}, 1) OVER ventana_cliente AS lag_1_{c}",
                 f"{c} - lag({c}, 1) OVER ventana_cliente AS delta_1_{c}"]
    lista = "\n    , ".join(cols)
    return f"""
CREATE OR REPLACE TABLE competencia_01_fe AS
SELECT f.*
    , {lista}
FROM competencia_01_fe f
WINDOW ventana_cliente AS (PARTITION BY numero_de_cliente ORDER BY foto_mes)
"""


# [Anotación · líneas 117–127] sql_ma3_completo reemplaza por NULL las columnas ma_3_* y slope_3_* cuando el
#   cliente tiene menos de 3 filas en la ventana (n_hist < 3). Sólo se usa si config.MA3_COMPLETO es True.
def sql_ma3_completo(con):
    """ma_3_* y slope_3_* en NULL si la ventana de 3 meses no esta completa."""
    cols = [c for c, *_ in con.execute("DESCRIBE competencia_01_fe").fetchall() if c.startswith(("ma_3_", "slope_3_"))]
    reemplazos = ", ".join(f"CASE WHEN n_hist < 3 THEN NULL ELSE {c} END AS {c}" for c in cols)
    return f"""
CREATE OR REPLACE TABLE competencia_01_fe AS
SELECT * EXCLUDE (n_hist) REPLACE ({reemplazos})
FROM (SELECT *, count(*) OVER (PARTITION BY numero_de_cliente ORDER BY foto_mes
                              ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS n_hist
      FROM competencia_01_fe)
"""


# [Anotación · líneas 130–134] guardar escribe la tabla competencia_01_fe en el parquet de destino e informa
#   la cantidad de columnas.
def guardar(con, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY competencia_01_fe TO '{destino.as_posix()}' (FORMAT PARQUET)")
    ncol = len(con.execute("SELECT * FROM competencia_01_fe LIMIT 0").description)
    log(f"listo -> {destino.relative_to(config.RAIZ)} ({ncol} columnas)")


# [Anotación · líneas 137–157] main carga el parquet con la clase, pasa ccajas_depositos a NULL en 202105,
#   crea las variables de fe_base y guarda competencia_01_fe_base.parquet; después agrega lag_1 y delta_1 de
#   todas las variables numéricas, aplica sql_ma3_completo sólo si está activado y guarda
#   competencia_01_fe_final.parquet.
def main():
    if not config.DATASET_CLASE.exists():
        raise SystemExit(f"falta {config.DATASET_CLASE}: correr pasos/p1_target.py")
    con = duckdb.connect()
    con.execute(f"CREATE TABLE competencia_01 AS SELECT * FROM read_parquet('{config.DATASET_CLASE.as_posix()}')")
    con.execute("UPDATE competencia_01 SET ccajas_depositos = NULL WHERE foto_mes = 202105")

    log("feature engineering base (clase4)")
    con.execute(sql_fe_base())
    guardar(con, config.DATASET_BASE)

    log("lag_1 y delta_1 de todas las variables")
    con.execute(sql_lags_todas(columnas_numericas(con)))
    if config.MA3_COMPLETO:
        log("ma_3 y slope_3 en NULL con menos de 3 meses de historia")
        con.execute(sql_ma3_completo(con))
    guardar(con, config.DATASET_FINAL)


if __name__ == "__main__":
    main()
```

### monday/Competencia_1/pasos/p3_busqueda.py

Búsqueda de hiperparámetros de LightGBM con Optuna sobre fe_base, con entrenamiento en 202103+202104 y medición en 202106; escribe el resultado en salida/busqueda/ y lo compara con params/mejores_params.json.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] El docstring resume el protocolo: fe_base, ventana 202103+202104 → 202106, 3
#   semillas por trial, 30 trials con TPE de semilla fija. Importa optuna, numpy y las funciones de lib/.
"""Paso 3: busqueda de hiperparametros de LightGBM con Optuna.

- Dataset: fe_base. Ventana: train 202103+202104 -> medir 202106 (la misma distancia de 2 meses
  entre la ultima baja aprendida y la baja a predecir que en la entrega, 202106 -> 202108).
- Cada trial entrena 3 semillas, promedia las probabilidades y mide la curva de ganancia
  suavizada sobre ese promedio: el valor del trial depende menos de la suerte de una semilla.
- 30 trials, TPE con semilla fija. Resultado: salida/busqueda/mejores_params.json, que se
  compara con params/mejores_params.json (los de la entrega).

Uso:  python pasos/p3_busqueda.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import optuna

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from lib.datos import cargar, features, log, semillas  # noqa: E402
from lib.ganancia import curva, suave  # noqa: E402
from lib.modelo import entrenar_predecir  # noqa: E402


# [Anotación · líneas 26–31] sugerir recorre config.ESPACIO_OPTUNA y pide a Optuna un entero o un real para
#   cada hiperparámetro, con su rango y su escala (logarítmica o lineal).
def sugerir(trial):
    p = {}
    for nombre, (tipo, desde, hasta, es_log) in config.ESPACIO_OPTUNA.items():
        sug = trial.suggest_int if tipo == "int" else trial.suggest_float
        p[nombre] = sug(nombre, desde, hasta, log=es_log)
    return p


# [Anotación · líneas 34–42] main carga de fe_base los meses 202103, 202104 y 202106, arma la lista de
#   variables, separa entrenamiento (202103 y 202104) y prueba (202106) y toma las 3 primeras semillas del pool.
def main():
    df = cargar([*config.MESES_VAL_TRAIN, config.MES_VAL_TEST], config.DATASET_BASE)
    feats = features(df)
    tr = df[df["foto_mes"].isin(config.MESES_VAL_TRAIN)].reset_index(drop=True)
    te = df[df["foto_mes"] == config.MES_VAL_TEST].reset_index(drop=True)
    del df
    sems = semillas(config.N_SEMILLAS_TRIAL)
    log(f"busqueda: train {config.MESES_VAL_TRAIN} {tr.shape} -> {config.MES_VAL_TEST}, {len(feats)} features, "
        f"{config.N_TRIALS} trials x {len(sems)} semillas")

# [Anotación · líneas 44–50] Función objetivo: con los hiperparámetros del trial entrena un modelo por
#   semilla, promedia las probabilidades de 202106, calcula la curva de ganancia en los cortes de 8.000 a
#   15.000, la suaviza y devuelve su máximo; guarda en el trial el corte donde se alcanza.
    def objective(trial):
        p = sugerir(trial)
        prob = np.mean([entrenar_predecir(tr, te, feats, p, s) for s in sems], axis=0)
        c = suave(curva(prob, te["clase_ternaria"]))
        i = int(np.argmax(c))
        trial.set_user_attr("N", config.CORTES[i])
        return float(c[i])

# [Anotación · líneas 52–56] Crea o reabre el estudio 'busqueda' en salida/busqueda/optuna.db (sqlite), en
#   dirección de maximizar, con TPESampler sembrado con la primera semilla del pool.
    config.DIR_BUSQUEDA.mkdir(parents=True, exist_ok=True)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize", study_name="busqueda", load_if_exists=True,
                                storage=f"sqlite:///{(config.DIR_BUSQUEDA / 'optuna.db').as_posix()}",
                                sampler=optuna.samplers.TPESampler(seed=semillas(1)[0]))

# [Anotación · líneas 58–64] El callback informa el valor de cada trial y el máximo acumulado. Cuenta los
#   trials completos y ejecuta sólo los que faltan para llegar a 30, de modo que una corrida interrumpida se
#   retoma.
    def cb(st, t):
        log(f"  trial {t.number}: {t.value / 1e6:6.1f}M N={t.user_attrs['N']} | mejor {st.best_value / 1e6:.1f}M "
            f"(trial {st.best_trial.number})")

    faltan = config.N_TRIALS - len([t for t in study.trials if t.state.name == "COMPLETE"])
    if faltan > 0:  # si se corto, retoma
        study.optimize(objective, n_trials=faltan, callbacks=[cb])

# [Anotación · líneas 66–78] Guarda trials.csv ordenado por valor y mejores_params.json con los
#   hiperparámetros del trial de mayor valor; lee params/mejores_params.json e informa SI o NO según coincidan.
#   Las últimas líneas son el punto de entrada.
    study.trials_dataframe().sort_values("value", ascending=False).to_csv(
        config.DIR_BUSQUEDA / "trials.csv", index=False)
    mejores = dict(study.best_params)
    (config.DIR_BUSQUEDA / "mejores_params.json").write_text(json.dumps(mejores, indent=2))
    log(f"mejor trial {study.best_trial.number} ({study.best_value / 1e6:.1f}M): {mejores}")

    entregados = json.loads(config.PARAMS_ENTREGA.read_text())
    log("coinciden con params/mejores_params.json (los de la entrega): "
        + ("SI" if mejores == entregados else f"NO -> entregados: {entregados}"))


if __name__ == "__main__":
    main()
```

### monday/Competencia_1/pasos/p4_validacion.py

Mide el modelo en la ventana de desarrollo: 10 semillas sobre fe_final entrenando con 202103+202104 y prediciendo 202106; guarda la curva de ganancia por semilla y un resumen, e informa si N = 12.000 cae dentro de la meseta.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–22] El docstring describe la validación (fe_final, 10 semillas, 202103+202104 →
#   202106) e indica que el paso no es necesario para generar la entrega. Importa pandas y las funciones de
#   lib/.
"""Paso 4: validacion del modelo en la ventana de desarrollo.

Dataset fe_final, hiperparametros del paso 3, 10 semillas, train 202103+202104 -> 202106.
Por semilla: curva de ganancia por cantidad de envios N. Resumen: N de la curva media
suavizada, desvio, minimo y meseta (cortes a menos de 2M del maximo). Chequea que
config.N_ENVIOS caiga dentro de la meseta.

No es necesario para generar la entrega: documenta cuanto rinde el modelo y de donde sale N.

Uso:  python pasos/p4_validacion.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from lib.datos import cargar, features, log, mejores_params, semillas  # noqa: E402
from lib.ganancia import curva, resumen  # noqa: E402
from lib.modelo import entrenar_predecir  # noqa: E402


# [Anotación · líneas 25–33] Lee los hiperparámetros (los de salida/busqueda/ si existen; si no, los de
#   params/), carga de fe_final los meses 202103, 202104 y 202106, separa entrenamiento y prueba y toma las 10
#   primeras semillas del pool.
def main():
    params = mejores_params()
    df = cargar([*config.MESES_VAL_TRAIN, config.MES_VAL_TEST], config.DATASET_FINAL)
    feats = features(df)
    tr = df[df["foto_mes"].isin(config.MESES_VAL_TRAIN)].reset_index(drop=True)
    te = df[df["foto_mes"] == config.MES_VAL_TEST].reset_index(drop=True)
    del df
    sems = semillas(config.N_SEMILLAS_VALIDACION)
    log(f"validacion: train {config.MESES_VAL_TRAIN} -> {config.MES_VAL_TEST}, {len(feats)} features, {len(sems)} semillas")

# [Anotación · líneas 35–39] Para cada semilla entrena, predice 202106 y calcula la ganancia en los 15 cortes;
#   guarda una fila por semilla e informa el corte de mayor ganancia.
    filas = []
    for s in sems:
        c = curva(entrenar_predecir(tr, te, feats, params, s), te["clase_ternaria"])
        filas.append({"semilla": s, **{str(n): v for n, v in zip(config.CORTES, c)}})
        log(f"  semilla {s}: mejor N={config.CORTES[int(c.argmax())]} -> {c.max() / 1e6:6.1f}M")

# [Anotación · líneas 41–47] Escribe salida/validacion/por_semilla.csv, calcula el resumen (N de la curva
#   media suavizada, media, desvío, mínimo, meseta) y lo guarda en resumen.json junto con la curva suavizada.
    tb = pd.DataFrame(filas)
    config.DIR_VALIDACION.mkdir(parents=True, exist_ok=True)
    tb.to_csv(config.DIR_VALIDACION / "por_semilla.csv", index=False)
    r = resumen(tb)
    (config.DIR_VALIDACION / "resumen.json").write_text(json.dumps(
        {k: v for k, v in r.items() if k != "curva_suave"} | {"curva_suave": {str(k): v for k, v in r["curva_suave"].items()}},
        indent=2, default=float))
# [Anotación · líneas 48–56] Informa N, media, desvío, mínimo y meseta en millones, la curva media suavizada
#   por corte y si config.N_ENVIOS (12.000) queda entre los extremos de la meseta. Las últimas líneas son el
#   punto de entrada.
    log(f"202106: N={r['N']}  media {r['media'] / 1e6:.1f}M  desvio {r['desvio'] / 1e6:.1f}M  "
        f"min {r['minimo'] / 1e6:.1f}M  meseta {r['meseta'][0]}-{r['meseta'][1]}")
    log("  curva media suavizada (M): " + "  ".join(f"{n}:{v / 1e6:.0f}" for n, v in r["curva_suave"].items()))
    dentro = r["meseta"][0] <= config.N_ENVIOS <= r["meseta"][1]
    log(f"N de la entrega ({config.N_ENVIOS}) dentro de la meseta: {'SI' if dentro else 'NO'}")


if __name__ == "__main__":
    main()
```

### monday/Competencia_1/pasos/p1_target.py

Lee el crudo con DuckDB, calcula clase_ternaria (BAJA+1, BAJA+2, CONTINUA o NULL) y guarda el resultado en salida/datasets/competencia_01_clase.parquet.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–18] El docstring define las tres clases según la presencia del cliente en t+1 y t+2 e
#   indica que los dos últimos meses quedan con clase NULL. Importa duckdb, config y log.
"""Paso 1: crudo -> clase_ternaria (logica de z101_target_sql_local).

Para cada cliente y foto t se mira si esta en t+1 y en t+2:
  BAJA+1    no esta en t+1 (o reaparece despues de un hueco)        -> requiere conocer t+1
  BAJA+2    esta en t+1 pero no en t+2                                -> requiere conocer t+2
  CONTINUA  esta en t+1 y en t+2
Los dos ultimos meses quedan con clase NULL (202107 solo puede ser BAJA+1): no son CONTINUA.

Uso:  python pasos/p1_target.py
"""
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from lib.datos import log  # noqa: E402

# [Anotación · líneas 20–33] Primera parte del SQL: lee el CSV completo (sample_size = -1), convierte
#   numero_de_cliente a BIGINT y numera cada mes como año × 12 + mes (periodo0); obtiene el último período del
#   dataset y, por cliente, el período de sus dos filas siguientes (periodo1 y periodo2).
SQL_TARGET = """
CREATE OR REPLACE TABLE competencia_01 AS
WITH base AS (
    SELECT * REPLACE (CAST(numero_de_cliente AS BIGINT) AS numero_de_cliente),
        (foto_mes // 100) * 12 + foto_mes % 100 AS periodo0
    FROM read_csv('{crudo}', sample_size = -1)
),
topes AS (SELECT max(periodo0) AS ultimo FROM base),
leads AS (
    SELECT b.*,
        lead(periodo0, 1) OVER (PARTITION BY numero_de_cliente ORDER BY periodo0) AS periodo1,
        lead(periodo0, 2) OVER (PARTITION BY numero_de_cliente ORDER BY periodo0) AS periodo2
    FROM base b
)
# [Anotación · líneas 34–43] Asigna la clase: BAJA+1 si no es el último mes y la fila siguiente no existe o no
#   es el mes inmediato; BAJA+2 si faltan al menos dos meses para el último, la fila siguiente es el mes
#   inmediato y la subsiguiente no existe o está más allá de t+2; CONTINUA en el resto de los meses anteriores
#   al anteúltimo; NULL en los demás casos. Descarta las columnas auxiliares.
SELECT * EXCLUDE (periodo0, periodo1, periodo2, ultimo),
    CASE
        WHEN periodo0 < ultimo AND (periodo1 IS NULL OR periodo1 > periodo0 + 1) THEN 'BAJA+1'
        WHEN periodo0 < ultimo - 1 AND periodo1 = periodo0 + 1
             AND (periodo2 IS NULL OR periodo2 > periodo0 + 2) THEN 'BAJA+2'
        WHEN periodo0 < ultimo - 1 THEN 'CONTINUA'
        ELSE NULL
    END AS clase_ternaria
FROM leads, topes
"""


# [Anotación · líneas 46–58] main verifica que exista el crudo, ejecuta el SQL en una base DuckDB en memoria e
#   informa por foto_mes la cantidad de BAJA+1, BAJA+2, CONTINUA y filas sin clase.
def main():
    if not config.CRUDO.exists():
        raise SystemExit(f"falta {config.CRUDO}: correr pasos/p0_descargar.py")
    con = duckdb.connect()
    log(f"leyendo {config.CRUDO.name} y armando clase_ternaria")
    con.execute(SQL_TARGET.format(crudo=config.CRUDO.as_posix()))
    for r in con.execute("""
            SELECT foto_mes, count(*) FILTER (WHERE clase_ternaria = 'BAJA+1'),
                   count(*) FILTER (WHERE clase_ternaria = 'BAJA+2'),
                   count(*) FILTER (WHERE clase_ternaria = 'CONTINUA'),
                   count(*) FILTER (WHERE clase_ternaria IS NULL)
            FROM competencia_01 GROUP BY 1 ORDER BY 1""").fetchall():
        log(f"  {r[0]}: BAJA+1 {r[1]:>5}  BAJA+2 {r[2]:>5}  CONTINUA {r[3]:>6}  sin clase {r[4]:>6}")
# [Anotación · líneas 59–65] Crea salida/datasets/ y escribe la tabla en competencia_01_clase.parquet; las dos
#   últimas líneas son el punto de entrada.
    config.DATASET_CLASE.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY competencia_01 TO '{config.DATASET_CLASE.as_posix()}' (FORMAT PARQUET)")
    log(f"listo -> {config.DATASET_CLASE.relative_to(config.RAIZ)}")


if __name__ == "__main__":
    main()
```

### monday/Competencia_1/pasos/p5_modelo_final.py

Entrena el modelo final con 202103–202106 sobre fe_final, una vez por semilla (20 por defecto), y guarda la probabilidad de cada cliente de 202108 por semilla en salida/modelo_final/probabilidades_202108.parquet.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] El docstring describe el paso: fe_final, entrenamiento con 202103–202106,
#   min_data_in_leaf escalado y 20 semillas. Importa numpy, pandas y las funciones de lib/.
"""Paso 5: modelo final y probabilidades de 202108.

- Dataset fe_final, entrenamiento con todos los meses con clase (202103-202106).
- min_data_in_leaf se escala por filas_final / filas_ventana (~x2): los hiperparametros se
  eligieron con 2 meses y el final usa 4.
- 20 semillas (semillerio): una probabilidad por semilla para cada cliente de 202108.
  Se guarda en salida/modelo_final/probabilidades_202108.parquet; si se corta, retoma.

Uso:  python pasos/p5_modelo_final.py [--semillas 20]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from lib.datos import cargar, features, ids_validos, log, mejores_params, semillas  # noqa: E402
from lib.modelo import entrenar_predecir, escalar_minimos  # noqa: E402


# [Anotación · líneas 26–29] Define el argumento --semillas, con valor por defecto config.N_SEMILLAS_FINAL
#   (20).
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--semillas", type=int, default=config.N_SEMILLAS_FINAL)
    args = ap.parse_args()

# [Anotación · líneas 31–40] Carga de fe_final los meses 202103 a 202106 y 202108; separa entrenamiento (los
#   cuatro meses con clase) y futuro (202108). Cuenta las filas de 202103 y 202104 y escala min_data_in_leaf por
#   filas de entrenamiento / filas de esa ventana. Verifica que los ids de 202108 coincidan en orden con los de
#   ids_validos y toma las semillas.
    df = cargar([*config.MESES_FINAL, config.MES_FUTURO], config.DATASET_FINAL)
    feats = features(df)
    tr = df[df["foto_mes"].isin(config.MESES_FINAL)].reset_index(drop=True)
    fu = df[df["foto_mes"] == config.MES_FUTURO].reset_index(drop=True)
    filas_ventana = int(df["foto_mes"].isin(config.MESES_VAL_TRAIN).sum())
    del df
    params = escalar_minimos(mejores_params(), filas_ventana, len(tr))
    ids = fu["numero_de_cliente"].to_numpy()
    assert np.array_equal(ids, ids_validos(config.MES_FUTURO, config.DATASET_FINAL)), "ids de 202108 desalineados"
    sems = semillas(args.semillas)

# [Anotación · líneas 42–46] Guarda en salida/modelo_final/config.json los hiperparámetros usados, los meses y
#   filas de entrenamiento, las filas de la ventana, las semillas y la lista de variables.
    config.DIR_FINAL.mkdir(parents=True, exist_ok=True)
    (config.DIR_FINAL / "config.json").write_text(json.dumps(
        {"params": params, "meses_train": config.MESES_FINAL, "filas_train": len(tr),
         "filas_ventana": filas_ventana, "semillas": sems, "features": feats}, indent=2))
    log(f"modelo final: {params}, train {config.MESES_FINAL} {tr.shape} -> {config.MES_FUTURO}, {len(sems)} semillas")

# [Anotación · líneas 48–58] Abre probabilidades_202108.parquet si existe (si no, parte de una tabla con los
#   ids) y verifica su alineación. Para cada semilla que no tenga columna, entrena con los cuatro meses, predice
#   202108, agrega la columna s<semilla> y reescribe el parquet.
    arch = config.DIR_FINAL / "probabilidades_202108.parquet"
    probs = pd.read_parquet(arch) if arch.exists() else pd.DataFrame({"numero_de_cliente": ids})
    assert np.array_equal(probs["numero_de_cliente"].to_numpy(), ids), "probabilidades guardadas desalineadas"
    for s in sems:
        if f"s{s}" in probs.columns:
            continue
        t0 = time.time()
        probs[f"s{s}"] = entrenar_predecir(tr, fu, feats, params, s)
        probs.to_parquet(arch, index=False)
        log(f"  semilla {s} ({time.time() - t0:.0f}s)")
    log(f"listo -> {arch.relative_to(config.RAIZ)}")


# [Anotación · líneas 61–62] Punto de entrada: llama a main() cuando el archivo se ejecuta como script.
if __name__ == "__main__":
    main()
```

### monday/Competencia_1/pasos/p6_entrega.py

Promedia las probabilidades por semilla, escribe el CSV con los N clientes de mayor promedio (12.000 por defecto), lo verifica y compara su SHA-256 con el del archivo entregado; opcionalmente escribe un archivo por semilla.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] El docstring describe la salida (sólo numero_de_cliente, sin encabezado, enteros),
#   las verificaciones y la opción --por-semilla. Importa hashlib, numpy, pandas y funciones de lib/datos.py.
"""Paso 6: archivo de entrega para el bot.

- Probabilidad final de cada cliente = promedio de las 20 semillas del paso 5.
- Se envia a los config.N_ENVIOS clientes de mayor probabilidad.
- Formato del bot: solo numero_de_cliente, sin encabezado, enteros (sin notacion cientifica).
- Verifica: cantidad de filas, ids unicos, todos existen en 202108, formato. Calcula el SHA-256
  y lo compara con el del archivo entregado (config.SHA256_ENTREGADO).

Con --por-semilla tambien escribe un archivo por semilla (para leer media y desvio en el bot).

Uso:  python pasos/p6_entrega.py [--n 12000] [--por-semilla]
"""
import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from lib.datos import ids_validos, log  # noqa: E402


# [Anotación · líneas 26–35] exportar ordena por probabilidad descendente con orden estable, toma los primeros
#   n ids y los escribe como int64 sin encabezado ni índice. Relee el archivo y verifica que no tenga notación
#   científica ni puntos, que tenga n líneas, que los ids no se repitan y que todos existan en 202108.
def exportar(ids, prob, n, destino, validos):
    orden = np.argsort(-np.asarray(prob), kind="stable")[:n]
    sel = pd.Series(np.asarray(ids)[orden]).astype("int64")
    sel.to_csv(destino, header=False, index=False)
    txt = destino.read_text()
    assert "e+" not in txt and "." not in txt, f"formato invalido en {destino}"
    assert len(txt.splitlines()) == n, f"cantidad de filas invalida en {destino}"
    assert sel.is_unique, f"ids repetidos en {destino}"
    malos = int((~sel.isin(set(validos))).sum())
    assert malos == 0, f"{malos} ids de {destino} no existen en {config.MES_FUTURO}"


# [Anotación · líneas 38–49] Define --n (por defecto 12.000) y --por-semilla. Lee las probabilidades, verifica
#   que sus ids estén alineados con los de 202108 e identifica las columnas de semillas (s seguido de dígitos).
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=config.N_ENVIOS)
    ap.add_argument("--por-semilla", action="store_true")
    args = ap.parse_args()

    probs = pd.read_parquet(config.DIR_FINAL / "probabilidades_202108.parquet")
    validos = ids_validos(config.MES_FUTURO, config.DATASET_FINAL)
    ids = probs["numero_de_cliente"].to_numpy()
    assert np.array_equal(ids, validos), "ids de las probabilidades desalineados con 202108"
    cols = [c for c in probs.columns if c.startswith("s") and c[1:].isdigit()]
    log(f"promedio de {len(cols)} semillas, N={args.n}")

# [Anotación · líneas 51–59] Escribe salida/entrega/competencia_01_entrega_n<N>.csv con el promedio de las
#   columnas de semillas y calcula su SHA-256. Si N es 12.000 y hay 20 semillas, informa si coincide con
#   config.SHA256_ENTREGADO; en otro caso informa que no se compara.
    config.DIR_ENTREGA.mkdir(parents=True, exist_ok=True)
    destino = config.DIR_ENTREGA / f"competencia_01_entrega_n{args.n}.csv"
    exportar(ids, probs[cols].mean(axis=1), args.n, destino, validos)
    sha = hashlib.sha256(destino.read_bytes()).hexdigest()
    log(f"listo -> {destino.relative_to(config.RAIZ)}  sha256 {sha}")
    if args.n == config.N_ENVIOS and len(cols) == config.N_SEMILLAS_FINAL:
        log("identico al archivo entregado: " + ("SI" if sha == config.SHA256_ENTREGADO else "NO"))
    else:
        log(f"no se compara con el archivo entregado (es N={config.N_ENVIOS} con {config.N_SEMILLAS_FINAL} semillas)")

# [Anotación · líneas 61–70] Con --por-semilla escribe, en la subcarpeta por_semilla_n<N>, un archivo con los
#   N de mayor probabilidad de cada semilla. Las últimas líneas son el punto de entrada.
    if args.por_semilla:
        carpeta = config.DIR_ENTREGA / f"por_semilla_n{args.n}"
        carpeta.mkdir(parents=True, exist_ok=True)
        for c in cols:
            exportar(ids, probs[c], args.n, carpeta / f"semilla_{c[1:]}_n{args.n}.csv", validos)
        log(f"{len(cols)} archivos por semilla -> {carpeta.relative_to(config.RAIZ)}")


if __name__ == "__main__":
    main()
```

### monday/Competencia_1/lib/datos.py

Funciones compartidas por los pasos y los experimentos: registro con tiempo transcurrido, pool de semillas, carga de meses desde un parquet, ids de un mes, lista de variables y lectura de los hiperparámetros.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–15] Importaciones y log, que imprime cada mensaje precedido por los segundos
#   transcurridos desde que se importó el módulo.
"""Carga de datos, lista de features, semillas y log."""
import json
import time
from pathlib import Path

import duckdb
import numpy as np

import config

_T0 = time.time()


def log(msg):
    print(f"[{time.time() - _T0:7.1f}s] {msg}", flush=True)


# [Anotación · líneas 18–21] semillas(n) genera con RandomState(17) 50 enteros distintos entre 0 y 999.999 y
#   devuelve los primeros n, por lo que la semilla i es la misma en todos los scripts. El comentario de
#   config.py los llama 'primos'; en esta función no hay un filtro de números primos.
def semillas(n):
    """Pool fijo: la semilla i es la misma en todos los pasos y experimentos."""
    rng = np.random.RandomState(config.SEMILLA_POOL)
    return rng.choice(1_000_000, size=50, replace=False).tolist()[:n]


# [Anotación · líneas 24–36] cargar lee del parquet las filas de los meses pedidos, ordenadas por foto_mes y
#   numero_de_cliente, con numero_de_cliente convertido a BIGINT; después pasa las columnas float64 a float32.
def cargar(meses, dataset):
    """Filas de los meses pedidos, ordenadas por (foto_mes, numero_de_cliente): los modelos dependen
    del orden de filas, asi el resultado es reproducible. El id se lee como entero y el resto de
    las columnas DOUBLE se bajan a float32 (float32 redondearia ids de mas de 16,7 millones)."""
    lista = ", ".join(str(m) for m in meses)
    df = duckdb.connect().execute(
        f"SELECT * REPLACE (CAST(numero_de_cliente AS BIGINT) AS numero_de_cliente) "
        f"FROM read_parquet('{Path(dataset).as_posix()}') WHERE foto_mes IN ({lista}) "
        f"ORDER BY foto_mes, numero_de_cliente"
    ).df()
    num = df.select_dtypes("float64").columns
    df[num] = df[num].astype("float32")
    return df


# [Anotación · líneas 39–44] ids_validos devuelve los numero_de_cliente de un mes en el mismo orden que usa
#   cargar.
def ids_validos(mes, dataset):
    """Ids reales del mes, en el mismo orden en que cargar() devuelve las filas."""
    return duckdb.connect().execute(
        f"SELECT CAST(numero_de_cliente AS BIGINT) FROM read_parquet('{Path(dataset).as_posix()}') "
        f"WHERE foto_mes = {mes} ORDER BY foto_mes, numero_de_cliente"
    ).df().iloc[:, 0].to_numpy()


# [Anotación · líneas 47–48] features devuelve las columnas que no son clase_ternaria, foto_mes ni
#   numero_de_cliente y cuyo nombre no contiene 'fultimo_cierre' ni 'Finiciomora'.
def features(df):
    return [c for c in df.columns if c not in config.FUERA and not any(d in c for d in config.DRIFT)]


# [Anotación · líneas 51–56] mejores_params lee salida/busqueda/mejores_params.json si existe y, si no,
#   params/mejores_params.json; informa de cuál de los dos se leyeron.
def mejores_params():
    """Los de la busqueda de esta corrida si existen; si no, los versionados en el repo."""
    propios = config.DIR_BUSQUEDA / "mejores_params.json"
    origen = propios if propios.exists() else config.PARAMS_ENTREGA
    log(f"hiperparametros desde {origen.relative_to(config.RAIZ)}")
    return json.loads(origen.read_text())
```

### monday/Competencia_1/lib/modelo.py

Entrenamiento y predicción de un LightGBM para una semilla, armado de sus parámetros y escalado de min_data_in_leaf según la cantidad de filas.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Importaciones y escalar_minimos: multiplica los parámetros listados en
#   config.PARAMS_MINIMOS (min_data_in_leaf) por filas_nuevas / filas_referencia, redondea al entero y aplica un
#   piso de 1; el resto de los parámetros no cambia.
"""LightGBM: parametros, entrenamiento por semilla y escalado de minimos."""
import lightgbm as lgb
import numpy as np

import config


def escalar_minimos(params, filas_referencia, filas_nuevas):
    """Los minimos de filas por hoja son absolutos: se escalan con la cantidad de filas para mantener
    la misma regularizacion relativa (misma idea que param_normalizado de z494)."""
    factor = filas_nuevas / filas_referencia
    return {k: (max(1, int(round(v * factor))) if k in config.PARAMS_MINIMOS else v) for k, v in params.items()}


# [Anotación · líneas 15–23] params_lgb combina los parámetros fijos de config con num_leaves, learning_rate,
#   min_data_in_leaf, feature_fraction, bagging_fraction y lambda_l2 del diccionario recibido y con la semilla.
def params_lgb(p, seed):
    return {**config.LGBM_FIJOS,
            "num_leaves": p["num_leaves"],
            "learning_rate": p["learning_rate"],
            "min_data_in_leaf": p["min_data_in_leaf"],
            "feature_fraction": p["feature_fraction"],
            "bagging_fraction": p["bagging_fraction"],
            "lambda_l2": p["lambda_l2"],
            "seed": seed}


# [Anotación · líneas 26–36] entrenar_predecir arma la etiqueta binaria: 1 si clase_ternaria está entre las
#   clases positivas (por defecto BAJA+1 y BAJA+2). Si se recibe 'peso_baja1' distinto de 1, asigna ese peso a
#   las filas BAJA+1 y 1 al resto; el camino de la entrega no lo usa.
def entrenar_predecir(df_train, df_apply, feats, p, seed):
    """Entrena con positivo = BAJA+1 o BAJA+2 y devuelve la probabilidad para df_apply.
    Opciones de p que solo usan los experimentos:
      'undersampling'  fraccion de CONTINUA por semilla
      'positivos'      clases positivas (por defecto config.CLASES_POSITIVAS)
      'peso_baja1'     peso de las filas BAJA+1 (por defecto 1)"""
    clases = df_train["clase_ternaria"]
    y = clases.isin(p.get("positivos", config.CLASES_POSITIVAS)).to_numpy().astype(int)
    pesos = None
    if p.get("peso_baja1", 1.0) != 1.0:
        pesos = np.where(clases.to_numpy() == "BAJA+1", p["peso_baja1"], 1.0)
# [Anotación · líneas 37–41] Si se recibe 'undersampling' menor a 1, conserva todas las filas que no son
#   CONTINUA y una fracción al azar de las CONTINUA (generador sembrado con la semilla), y escala
#   min_data_in_leaf por las filas que quedan; el camino de la entrega no lo usa.
    filas = np.ones(len(df_train), dtype=bool)
    us = p.get("undersampling", 1.0)
    if us < 1.0:
        filas = (clases != "CONTINUA").to_numpy() | (np.random.default_rng(seed).random(len(df_train)) < us)
        p = escalar_minimos(p, len(df_train), int(filas.sum()))
# [Anotación · líneas 42–47] Construye un lgb.Dataset nuevo con la semilla y max_bin 31, entrena con lgb.train
#   durante num_boost_round rondas, sin conjunto de validación, y devuelve las probabilidades del conjunto a
#   predecir usando 16 hilos.
    # un Dataset nuevo por semilla: LightGBM arma los bins muestreando filas con la semilla
    dtrain = lgb.Dataset(df_train.loc[filas, feats], label=y[filas],
                         weight=None if pesos is None else pesos[filas],
                         params={"seed": seed, "max_bin": config.LGBM_FIJOS["max_bin"]})
    m = lgb.train(params_lgb(p, seed), dtrain, num_boost_round=p["num_boost_round"])
    return m.predict(df_apply[feats], num_threads=config.HILOS)
```

### monday/Competencia_1/lib/ganancia.py

Cálculo de la ganancia por cantidad de envíos, suavizado de la curva, resumen entre semillas (N, media, desvío, mínimo, meseta) y comparación pareada entre variantes.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–5] Importa numpy, pandas y config, de donde salen las constantes de ganancia, los
#   cortes y el ancho del suavizado.
"""Curva de ganancia por cantidad de envios, suavizado, meseta y comparacion pareada."""
import numpy as np
import pandas as pd

import config


# [Anotación · líneas 8–14] curva ordena los clientes por probabilidad descendente (orden estable), asigna
#   1.072.500 a los BAJA+2 y −27.500 al resto, acumula y devuelve la ganancia acumulada en cada corte de
#   config.CORTES.
def curva(prob, clases):
    """Ganancia acumulada enviando a los N de mayor probabilidad, para cada N de config.CORTES.
    Solo BAJA+2 suma; cualquier otro estimulado resta."""
    orden = np.argsort(-np.asarray(prob), kind="stable")
    gan = np.where(np.asarray(clases)[orden] == "BAJA+2", config.GANANCIA_ACIERTO, -config.COSTO_ESTIMULO)
    acum = np.cumsum(gan)
    return np.array([acum[n - 1] for n in config.CORTES], dtype=float)


# [Anotación · líneas 17–19] suave aplica una media móvil centrada de 3 cortes; en los extremos promedia los
#   valores disponibles (min_periods=1).
def suave(c):
    """Media movil centrada: se elige la zona alta de la curva, no un pico aislado."""
    return pd.Series(c).rolling(config.SUAVIZADO, center=True, min_periods=1).mean().to_numpy()


# [Anotación · líneas 22–30] resumen recibe una fila por semilla: promedia las curvas, suaviza el promedio y
#   toma como N el corte de mayor valor; informa media, desvío y mínimo entre semillas de la ganancia sin
#   suavizar en ese N, y la meseta como primer y último corte cuya media suavizada está a menos de 2.000.000 del
#   máximo.
def resumen(tb):
    """tb: una fila por semilla con columnas str(N). N elegido sobre la curva media suavizada."""
    cortes = [str(n) for n in config.CORTES]
    media = suave(tb[cortes].mean().to_numpy())
    i = int(np.argmax(media))
    col = cortes[i]
    meseta = [n for n, v in zip(config.CORTES, media) if v >= media.max() - 2_000_000]
    return {"N": config.CORTES[i], "media": tb[col].mean(), "desvio": tb[col].std(), "minimo": tb[col].min(),
            "meseta": (meseta[0], meseta[-1]), "curva_suave": dict(zip(config.CORTES, media))}


# [Anotación · líneas 33–39] comparar calcula, semilla por semilla, la diferencia entre la ganancia de una
#   variante en su N y la de la referencia en el suyo; devuelve media, desvío, cantidad de semillas con
#   diferencia positiva y si cumple la regla de adopción (media ≥ 5.000.000 y al menos 7 semillas ganadas). Sólo
#   la usa experimentos/variantes.py.
def comparar(tb_base, tb_nueva, mejora_min=5_000_000, gana_min=7):
    """Comparacion pareada (misma semilla), cada variante en su N. Regla de adopcion:
    mejora media >= 5M y gana en >= 7 de 10 semillas."""
    nb, nn = resumen(tb_base)["N"], resumen(tb_nueva)["N"]
    d = (tb_nueva.set_index("semilla")[str(nn)] - tb_base.set_index("semilla")[str(nb)]).dropna()
    return {"diferencia": d.mean(), "desvio": d.std(), "gana": int((d > 0).sum()), "semillas": len(d),
            "adopta": bool(d.mean() >= mejora_min and (d > 0).sum() >= gana_min)}
```


## Explicaciones del alumno (texto original)

### monday/Competencia_1/README.md

> # Primera Competencia — DMEyF 2026 (comisión lunes)
>
> Alejandro Esquivel
>
> Predicción de los clientes **BAJA+2** del Paquete Premium en la foto **202108**: los que se van a dar de baja **dentro de 2 meses** (siguen siendo clientes en 202109, por lo que no son BAJA+1, y ya no están en 202110). La campaña de retención estimula a los **12.000** clientes con mayor probabilidad de ser BAJA+2.
>
> | | |
> |---|---|
> | Archivo entregado | `competencia_01_entrega_n12000.csv`: 12.000 `numero_de_cliente`, sin encabezado |
> | SHA-256 | `7dede71a1cf143dcb05937a3a0657fcc17d32f2d473e8f0ece75d529210421fd` |
> | Leaderboard público | 107,47 |
> | Validación (202106, 10 semillas) | 421,0M de media, desvío 5,5M |
>
> ## Cómo correrlo
>
> ```bash
> pip install -r requirements.txt
> python correr_todo.py                  # todo, desde el crudo (~2 h con 16 núcleos)
> python correr_todo.py --sin-busqueda   # usa params/mejores_params.json en vez de re-buscar (~1 h 20)
> ```
>
> El crudo se descarga solo del bucket de la cátedra a `datos/` (o se puede copiar ahí a mano). Todo lo generado queda en `salida/`. El archivo final es `salida/entrega/competencia_01_entrega_n12000.csv`, y el último paso imprime si es idéntico (SHA-256) al entregado.
>
> Cada paso se puede correr suelto, en orden:
>
> | Paso | Qué hace | Tiempo |
> |---|---|---|
> | `pasos/p0_descargar.py` | baja `competencia_01_crudo.csv` | — |
> | `pasos/p1_target.py` | `clase_ternaria` (CONTINUA / BAJA+1 / BAJA+2) | 30 s |
> | `pasos/p2_features.py` | limpieza + features → `fe_base` y `fe_final` | 1 min |
> | `pasos/p3_busqueda.py` | Optuna sobre `fe_base` → hiperparámetros | 45 min |
> | `pasos/p4_validacion.py` | 10 semillas en 202103–04 → 202106: ganancia por N y meseta | 15 min |
> | `pasos/p5_modelo_final.py` | 202103–06 → 202108, 20 semillas | 60 min |
> | `pasos/p6_entrega.py` | promedio, top 12.000, verificación y SHA-256 | segundos |
>
> `p6_entrega.py --por-semilla` además escribe un archivo por semilla, para leer media y desvío en el bot.
>
> ## Estructura
>
> ```
> config.py          todos los parámetros: rutas, meses, semillas, N, espacio de Optuna, hilos
> correr_todo.py     corre los pasos en orden
> pasos/             un script por etapa (p0 a p6)
> lib/               datos.py (carga, features), ganancia.py (curva por N, meseta, comparación),
>                    modelo.py (LightGBM por semilla, escalado de mínimos)
> params/            hiperparámetros del modelo entregado
> experimentos/      lo que se midió y no entró: variantes de LightGBM y Random Forest
> docs/DECISIONES.md cada decisión con su porqué
> ```
>
> ## El modelo, en una tabla
>
> | Pieza | Elección | Por qué (detalle en `docs/DECISIONES.md`) |
> |---|---|---|
> | Clase | positivo = BAJA+1 + BAJA+2; la ganancia cuenta solo BAJA+2 | D6 |
> | Features | clase4 (tarjetas combinadas, ratios, actividad digital, productos, rankings dentro del mes, tendencias) + **lag_1 y delta_1 de todas las variables** | D3, D10 |
> | Limpieza | fuera `*_fultimo_cierre` y `*_Finiciomora` (drift de datos); `ccajas_depositos` → NULL en 202105 | D7 |
> | Validación | entrenar 202103–04, medir 202106: misma distancia de 2 meses que la entrega | D5 |
> | Hiperparámetros | Optuna, 30 trials × 3 semillas promediadas por trial | D8, D11 |
> | Modelo final | LightGBM, 202103–06, 20 semillas promediadas, `min_data_in_leaf` escalado por filas | D13 |
> | Corte | N = 12.000, centro de la meseta de validación | D12 |
>
> ## Qué se probó y no entró
>
> Con la regla de adopción fijada antes de medir (≥ 5M y gana en ≥ 7 de 10 semillas):
>
> | Variante | vs modelo entregado |
> |---|---|
> | Target solo BAJA+2 | −31,7M, 0/10 |
> | Target BAJA+1 + BAJA+2 con BAJA+1 de peso 0,25 | −7,8M, 0/10 |
> | Undersampling de CONTINUA (25% por semilla) | −7,5M, 2/10 |
> | Entrenar sin 202103 (primer mes, sin lags) | −4,4M, 3/10 |
> | `ma_3`/`slope_3` en NULL con menos de 3 meses de historia | +4,2M, 9/10 (debajo de 5M); en el público 102,43, debajo del umbral fijado de 103,1 |
> | Rankings dentro del mes con cero fijo | −2,1M, 4/10 |
> | Re-búsqueda de hiperparámetros sobre el dataset final | −0,2M, 4/10 |
> | Marca de aguinaldo | no evaluable con la ventana de validación (sin junio en el entrenamiento) |
> | Random Forest | 394,0M en una validación no comparable (referencia) |
>
> Las limitaciones conocidas de la metodología (una sola ventana de validación, meses sin historia en el entrenamiento, sesgos de la búsqueda) están en `docs/DECISIONES.md` (D15).
>
> Detalle en `experimentos/RESULTADOS.md`. Para reproducirlos (requieren haber corrido `p1` y `p2`):
>
> ```bash
> python experimentos/variantes.py --variantes referencia solo_baja2 peso_baja1 sin_202103 ma3_completo
> python experimentos/variantes.py --variantes aguinaldo rank_cero undersampling busqueda_final
> python experimentos/variantes.py --final ma3_completo     # modelo final de una variante, para el público
> python experimentos/rf_linea_base.py                      # Random Forest (lento)
> ```
>
> ## Reproducibilidad
>
> **Verificado el 11/10/2026:** `python correr_todo.py --sin-busqueda`, desde el crudo y con `salida/` vacía, generó un archivo idéntico al entregado (mismo SHA-256) y la misma validación (421,0M, meseta 11.000–13.000). La búsqueda de Optuna (`p3`) se verificó por separado ese mismo día: desde cero encontró exactamente los hiperparámetros de `params/mejores_params.json`.
>
> Versiones usadas: las de `requirements.txt` (Python 3.13, LightGBM 4.7.0), con 16 hilos. Con otra cantidad de hilos o de versión, LightGBM puede cambiar los últimos decimales de las probabilidades. En el corte, la distancia entre el cliente 12.000 y el 12.001 es de 1,2e-5, así que no debería cambiar la lista. Detalle en `docs/DECISIONES.md` (D14).

### monday/Competencia_1/docs/DECISIONES.md

> # Decisiones
>
> Qué se decidió, por qué y qué se descartó. Los números de cada experimento están en `experimentos/RESULTADOS.md`.
>
> ---
>
> ## D1 — Qué se predice y en qué formato
> - Clientes de la foto **202108** que van a ser **BAJA+2**, es decir, que se dan de baja **dentro de 2 meses**: siguen siendo clientes en 202109 (no son BAJA+1) y ya no están en 202110. A los BAJA+1 se llega tarde para la campaña de retención.
> - Ganancia: +1.072.500 por cada BAJA+2 estimulado y −27.500 por cualquier otro estimulado.
> - Entrega: CSV con solo `numero_de_cliente`, sin encabezado, enteros, entre 8.000 y 15.000 filas. Por eso se elige una **cantidad de envíos N** (los N de mayor probabilidad), no un umbral.
>
> ## D2 — Meses utilizables
> - La clase de la foto *t* necesita ver *t+1* y *t+2*: solo **202103–202106** tienen clase completa.
> - 202107 (solo puede ser BAJA+1) y 202108 (sin clase) se usan únicamente para calcular features. Sus filas sin clase **no** son CONTINUA (z101).
>
> ## D3 — Todo desde el crudo, en código
> - `p1_target.py` arma la clase con la lógica de z101 y `p2_features.py` las features. No hay ningún dataset editado a mano.
> - Respecto de clase4, una corrección: la ventana de `ma_3` / `slope_3` es de 3 meses (`2 PRECEDING` + el actual; `3 PRECEDING` son 4 filas).
>
> ## D4 — LightGBM como modelo; Random Forest como línea de base
> - LightGBM es el modelo de los notebooks de la materia (z601) y es varias veces más rápido por modelo, lo que permite semillerío y búsqueda en el tiempo disponible.
> - El RF queda en `experimentos/rf_linea_base.py`. Su validación (394,0M) **no es comparable** con la de LightGBM (otra ventana, otra versión de features, otra búsqueda): es solo una referencia.
>
> ## D5 — Ventana de desarrollo: entrenar 202103 + 202104, medir 202106
> - En la entrega, la baja más reciente que se puede aprender es la de agosto (BAJA+2 de 202106) y la que se predice es la de octubre (202108): **2 meses de distancia**.
> - Entrenando con 202103–04 y midiendo en 202106 se reproduce exactamente esa situación (se aprende hasta las bajas de junio y se predicen las de agosto). Es el esquema de los notebooks de la materia (z301/z401/z601: 202103 → 202105).
> - **Descartado:** entrenar con 202103–05. Da más datos pero incluye bajas de julio, un mes "del futuro" si uno está parado en junio, así que la medición sale optimista.
>
> ## D6 — Target binario: BAJA+1 + BAJA+2
> - Positivo = BAJA+1 o BAJA+2 (z601, "(anti)Discriminación"): hay más ejemplos para aprender el patrón de baja. La ganancia se sigue midiendo contando solo BAJA+2.
> - **Medido:** solo BAJA+2 pierde 31,7M (0/10) y BAJA+1 con peso 0,25 pierde 7,8M (0/10). En el top 12.000 hay ~681 BAJA+2 y ~639 BAJA+1: cada BAJA+1 enviado cuesta, pero entrenar con ellos hace que el modelo encuentre más BAJA+2.
>
> ## D7 — Limpieza de datos
> - Fuera del modelo: `*_fultimo_cierre` y `*_Finiciomora` con todo lo derivado. Son drift de datos, no de comportamiento: `fultimo_cierre` tiene PSI ~30–39 (z701) y `Finiciomora` es casi todo nulo. También quedan fuera `numero_de_cliente` y `foto_mes`.
> - `ccajas_depositos` vale 0 para los 163.768 clientes de 202105, contra 800–6.500 con valor en los demás meses: error de datos → NULL en ese mes.
>
> ## D8 — Búsqueda de hiperparámetros
> - Optuna (TPE con semilla fija), 30 trials, sobre el dataset `fe_base`.
> - **Cada trial promedia 3 semillas** y se evalúa con la curva de ganancia suavizada (media móvil de 3 cortes): con una sola semilla el valor del trial tiene demasiado ruido (z301).
> - Espacio: `learning_rate` 0,005–0,1 · `num_leaves` 8–512 · `num_boost_round` 100–1.500 · `min_data_in_leaf` 20–4.000 · `feature_fraction` 0,1–0,9 · `bagging_fraction` 0,5–1 · `lambda_l2` 0,001–100.
> - Resultado (trial 24): `num_leaves` 108, `learning_rate` 0,0109, 1.180 árboles, `min_data_in_leaf` 230, `feature_fraction` 0,34, `bagging_fraction` 0,72, `lambda_l2` 0,17.
>
> ## D9 — Regla para adoptar una variante (fijada antes de medir)
> - Misma ventana, mismos hiperparámetros y 10 semillas pareadas, cada variante en su N.
> - Se adopta solo si la mejora media es **≥ 5M** y gana en **≥ 7 de 10** semillas.
> - Sin una regla previa se termina eligiendo lo que salió mejor por suerte (la maldición del ganador, z301).
>
> ## D10 — Features del modelo entregado: FE base + lag_1 y delta_1 de todas las variables
> - +7,5M sobre el FE base, gana en 9/10 semillas, y además baja el desvío (6,8M → 5,5M).
> - En el leaderboard público, con 20 archivos por modelo: 95,87 → 101,93.
> - Se probaron y **no** se adoptaron: rankings con cero fijo, undersampling, target solo BAJA+2 o con BAJA+1 de menor peso, y entrenar sin 202103 (ver RESULTADOS.md).
> - **El aguinaldo no se pudo evaluar:** la marca solo vale 1 en junio y diciembre, y el entrenamiento de la ventana (202103–04) no tiene ninguno de los dos meses.
>
> ## D11 — Se mantienen los hiperparámetros de la búsqueda sobre el FE base
> - Re-buscar con Optuna sobre el dataset final dio −0,2M y ganó en 4/10: no se encontró mejora, lo que no prueba que sean equivalentes. Se mantienen los que ya estaban validados y confirmados en el público.
>
> ## D12 — Corte: N = 12.000
> - Validación (10 semillas): meseta de 11.000 a 13.000, máximo en 11.500–12.000.
> - Público (20 archivos por punto): 10.500 → 101,07 · 11.500 → 101,93 · 12.500 → 102,19 · 13.500 → 99,56. 11.500 y 12.500 empatan (la diferencia es menor que el error de la media).
> - Ante empate, el centro de la meseta de validación. No se toma el punto más alto del público, porque esa diferencia es ruido.
>
> ## D13 — Modelo final: 202103–202106, 20 semillas promediadas
> - Se entrena con los 4 meses con clase. `min_data_in_leaf` se escala por la cantidad de filas (230 → 461): los mínimos de filas por hoja son absolutos, y sin escalar el modelo final quedaría menos regularizado que el validado (`param_normalizado`, z494).
> - 20 modelos idénticos salvo la semilla. La probabilidad final de cada cliente es el promedio, que baja la varianza respecto de depender de una sola semilla. En el público, el promedio dio 107,47 contra ~102 de la media de los archivos por semilla. Es un solo archivo, así que no prueba cuánto suma el promedio.
>
> ## D14 — Reproducibilidad
> - Filas ordenadas por (`foto_mes`, `numero_de_cliente`), un `lgb.Dataset` nuevo por semilla (LightGBM arma los bins muestreando con la semilla), `deterministic=True`, 16 hilos fijos, pool fijo de semillas (`RandomState(17)`).
> - `numero_de_cliente` viene del crudo como DOUBLE: se castea a entero **antes** de bajar el resto de las columnas a float32. Sin esto float32 redondea los ids de más de 16,7 millones (pasó en un primer envío y el bot lo rechazó).
> - `p6_entrega.py` verifica filas, ids únicos y existentes en 202108 y formato, y compara el SHA-256 con el del archivo entregado.
> - **Verificado el 11/10/2026:** la corrida de punta a punta (`correr_todo.py --sin-busqueda`, desde el crudo) reprodujo el archivo entregado con el mismo SHA-256, y `p3` desde cero encontró los mismos hiperparámetros.
>
> ## D15 — Limitaciones conocidas
> - **Una sola ventana de validación (202106).** Las comparaciones pareadas reducen el ruido entre variantes, pero no protegen contra decisiones que solo valen para junio (un mes con aguinaldo). La ganancia absoluta en 202106 tiene una incertidumbre de ~±30M solo por qué clientes caen en ese mes (~680 BAJA+2 en el top). El público de 202108 se usó como segundo control independiente.
> - **202103 no tiene lags ni deltas** (es el primer mes del dataset) y `ma_3`/`slope_3` promedian 1 o 2 meses en 202103–04. En la validación, la mitad del entrenamiento tiene esas columnas vacías o incompletas y el test no: lo más probable es que la validación subestime el aporte de las tendencias.
> - Las 3 semillas de cada trial de Optuna son las 3 primeras de las 10 de validación: hay un sesgo leve a favor de los hiperparámetros elegidos.
> - Optuna optimiza el máximo de la curva suavizada (un objetivo optimista) con 30 trials para 7 hiperparámetros: la búsqueda tiene poca cobertura.
> - `comparar` evalúa cada variante en su propio N, lo que le da un margen chico de selección a la variante.
> - `lag` y las ventanas cuentan filas, no meses: para los 23 clientes con algún mes faltante, "el mes anterior" no es el mes calendario anterior. Impacto despreciable.
>
> ## D16 — No se adopta `ma_3`/`slope_3` con historia completa
> - Validación: +4,2M y gana en 9/10, debajo del umbral de D9 (5M).
> - Desempate en el público con la regla fijada antes de mirar: adoptar solo si la media de 20 archivos en N = 12.000 es ≥ 103,1. Dio 102,43 ± 2,30.
> - Queda disponible en el código, apagado (`config.MA3_COMPLETO = False`).

### monday/Competencia_1/experimentos/RESULTADOS.md

> # Experimentos
>
> Todas las variantes de LightGBM se midieron con el mismo protocolo que el modelo entregado:
> - entrenamiento 202103 + 202104, medición en 202106;
> - mismos hiperparámetros (`params/mejores_params.json`), salvo que la variante sea justamente cambiarlos;
> - 10 semillas pareadas, cada variante en el N de su curva media suavizada.
>
> **Regla de adopción, fijada antes de medir:** mejora media ≥ 5M y gana en ≥ 7 de 10 semillas. El ruido entre semillas ronda los 5–7M.
>
> Script: `experimentos/variantes.py`.
>
> ## LightGBM
>
> | Variante | Qué cambia | Ganancia media 202106 | vs referencia | Gana en | Decisión |
> |---|---|---|---|---|---|
> | FE base | features de clase4 (226) | 413,5M | — | — | punto de partida |
> | **lags de todas** | + lag_1 y delta_1 de todas las variables (508) | **421,0M** | **+7,5M vs FE base** | **9/10** | ✅ **adoptada: es el modelo entregado** |
> | aguinaldo | + `cobra_aguinaldo`, `mpayroll_sin_sac` y sus tendencias | 418,1M | −2,9M | 4/10 | ⚠️ no evaluable (ver abajo) |
> | rankings con cero fijo | + ranking dentro del mes con 0 fijo de todos los montos | 418,9M | −2,1M | 4/10 | ❌ |
> | undersampling 25% | cada semilla: todas las bajas + su propio 25% de CONTINUA | 413,5M | −7,5M | 2/10 | ❌ |
> | búsqueda sobre el dataset final | Optuna (30×3) sobre las 508 features | 420,8M | −0,2M | 4/10 | ❌ (no se encontró mejora) |
> | target solo BAJA+2 | positivo = solo BAJA+2 | 389,3M | −31,7M | 0/10 | ❌ |
> | BAJA+1 con peso 0,25 | positivo = BAJA+1 + BAJA+2, filas BAJA+1 con peso 0,25 | 413,2M | −7,8M | 0/10 | ❌ |
> | sin 202103 | entrenar solo con 202104 (202103 no tiene lags) | 416,6M | −4,4M | 3/10 | ❌ |
> | `ma_3`/`slope_3` completos | NULL si el cliente tiene menos de 3 meses de historia | 425,1M | +4,2M | 9/10 | ❌ debajo del umbral de 5M; en el público 102,43 (umbral 103,1) |
>
> Lectura:
> - Lo que más aportó fue darle al modelo **la tendencia de cada variable** (lag y delta de todas).
> - **El target BAJA+1 + BAJA+2 está medido:** cuanto más peso tiene BAJA+1, mejor (solo BAJA+2: −31,7M; peso 0,25: −7,8M). En el top 12.000 del modelo hay ~681 BAJA+2 y ~639 BAJA+1. Aprender el patrón de baja con los dos le sirve para encontrar más BAJA+2.
> - **Sacar 202103** (que no tiene lags) pierde: sus filas aportan más de lo que ensucian.
> - **El experimento de aguinaldo no es válido con esta ventana.** `cobra_aguinaldo` solo puede valer 1 en junio y diciembre, y el entrenamiento (202103–04) no tiene ninguno de los dos: el modelo no puede aprender la variable. El −2,9M es ruido y no dice nada sobre su utilidad en el modelo final, que sí entrena con junio. Para evaluarlo hace falta una ventana con junio en el entrenamiento (o el leaderboard público).
> - El undersampling, además de perder ganancia, sube el desvío entre semillas (de 5,5M a 7,1M).
> - Re-buscar hiperparámetros sobre el dataset final no encontró mejora (−0,2M, 4/10). Eso no prueba que los dos conjuntos sean equivalentes: solo que la diferencia no se distingue del ruido.
>
> ## Random Forest (línea de base)
>
> Script: `experimentos/rf_linea_base.py`. Clase ternaria, imputación por mediana, Optuna sobre el OOB de 202104 (25 trials) y validación 202104 → 202106 con 5 semillas.
>
> | Modelo | Ganancia media 202106 | Desvío | N |
> |---|---|---|---|
> | RF (300 árboles, `max_depth` 27, `min_samples_leaf` 97, `max_features` 0,61) | 394,0M | 6,3M | 14.000 |
>
> **No es comparable con LightGBM:** se midió con una versión previa del FE base (sin la limpieza de `ccajas_depositos`), con 1 mes de entrenamiento en vez de 2, eligiendo hiperparámetros por OOB en ese mismo mes y con 5 semillas. Es solo una referencia de orden de magnitud. No siguió en el pipeline por costo (~4 minutos por modelo, contra ~1,5 de LightGBM).
>
> ## Corte (cantidad de envíos) en el leaderboard público
>
> Mismo modelo, 20 archivos por punto (uno por semilla), ganancia pública media:
>
> | N | 10.500 | 11.500 | 12.000 (promedio de semillas, 1 archivo) | 12.500 | 13.500 |
> |---|---|---|---|---|---|
> | Público | 101,07 ± 2,30 | 101,93 ± 2,79 | **107,47** | 102,19 ± 2,55 | 99,56 ± 1,98 |
>
> 11.500 y 12.500 empatan (la diferencia es menor que el error de la media). Se tomó 12.000, el centro de la meseta de validación (11.000–13.000), y se entrega el promedio de las 20 semillas.
>
> El 107,47 es **un solo archivo** sobre ~25% de 202108. Es compatible con que el promedio de semillas rinda más que cada semilla suelta, pero no lo prueba: puede incluir ruido de la muestra pública.
>
> ## `ma_3` / `slope_3` con historia completa: desempate en el público
>
> En validación dio +4,2M y ganó en 9/10, debajo del umbral de 5M. Se desempató en el público con una regla fijada antes de mirar: entrenar el final con el arreglo (`python experimentos/variantes.py --final ma3_completo`) y adoptarlo solo si la media de los 20 archivos en N = 12.000 era ≥ 103,1 (+1,0 sobre ~102,1, el promedio del modelo actual en 11.500 y 12.500).
>
> | Modelo (20 archivos, uno por semilla) | N | Público |
> |---|---|---|
> | Modelo entregado | 11.500 / 12.500 | 101,93 ± 2,79 / 102,19 ± 2,55 |
> | Con `ma_3`/`slope_3` completos | 12.000 | 102,43 ± 2,30 |
>
> **No se adopta.** En el público, con 20 archivos en N = 12.000, dio **102,43 ± 2,30**, debajo del umbral fijado antes de mirar (≥ 103,1, es decir +1,0 sobre ~102,1 del modelo actual en ese corte). La mejora de validación (+4,2M, 9/10) no se trasladó a 202108.

