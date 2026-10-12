# Fernando Steeb — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: FSteeb1
- Repositorio: https://github.com/FSteeb1/dmeyf2026
- Link posteado: https://github.com/FSteeb1/dmeyf2026/tree/main/fernando/entrega_competencia_01
- Commit: 0ec1c637c3f20b16e8406677acf9b22bd6a2bf51
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/fsteeb1/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/fsteeb1.json

## Resumen

La entrega es la carpeta fernando/entrega_competencia_01 del repositorio. Contiene un README, un notebook que arma clase_ternaria con SQL sobre DuckDB, cuatro módulos de construcción de variables, tres scripts de entrenamiento que comparten 3_modelos/comun.py, un script de ensamble, cuatro scripts de selección de variables y las probabilidades de 202108 guardadas en archivos .npy. El camino de la entrega entrena 27 modelos LightGBM con los mismos hiperparámetros fijos (2.000 árboles, learning_rate 0,005, num_leaves 63) sobre 202103 a 202106, con clase binaria donde BAJA+1 y BAJA+2 son positivos. Los modelos se reparten en tres familias que agregan variables una sobre otra: historia (5 semillas), historia_comportamiento (9) e historia_comportamiento_flujos (13). Las variables incluyen 155 features base de una lista fija, lags y deltas de 1 y 2 meses de todas las variables numéricas, tendencia, mínimo, máximo y cocientes en ventana de 6 meses para 40 variables, y una copia de los montos convertida a rank dentro de cada mes con el cero fijo. armar_ensamble.py promedia las 27 probabilidades y escribe los 11.000 clientes de mayor promedio.

**Qué entrega.** Un CSV sin encabezado, 4_ensamble/salida/prediccion_final.csv, con el numero_de_cliente de los 11.000 clientes de 202108 con mayor probabilidad promedio. El archivo no está en el repositorio (4_ensamble/salida/ figura en el .gitignore de la entrega): lo genera armar_ensamble.py a partir de las probabilidades guardadas en probabilidades/. El README declara su SHA-256: 2a5a508683301735e4f4b5ab07ccc50c102459479691baf9211e68c3e496663a.

**Cómo se ejecuta.** Según el README: pip install -r requirements.txt y después cuatro pasos. 1) Correr 1_datos/construccion_target.ipynb, que genera data/competencia_01.csv con clase_ternaria. 2) python 1_datos/construir_historia.py, que deja los parquet en trabajo/historia/. 3) En cada carpeta de 3_modelos/, python entrenar.py, respetando las corridas definidas en CORRIDAS y el orden de las semillas. 4) python 4_ensamble/armar_ensamble.py. El README indica que el paso 4 se puede correr directamente porque las probabilidades de los 27 modelos están en probabilidades/, y que python 3_modelos/verificar_semilla.py historia corrida_1 reentrena la primera semilla de una corrida y la compara con la guardada.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: positivo = BAJA+1 o BAJA+2, negativo = CONTINUA (comun.py, línea 141). clase_ternaria se arma en el notebook con el criterio que evalúa primero la presencia a dos meses: un cliente ausente el mes siguiente y presente el subsiguiente queda como CONTINUA.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** —
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica: el dataset de entrenamiento toma todas las filas de 202103 a 202106 (comun.py, líneas 138 a 144).
- **Calidad de datos:** ccajas_depositos se pasa a NA en 202105 (el comentario del código dice que en ese mes viene toda en cero), tanto al construir la historia como al armar la matriz de entrenamiento. En los cocientes, las divisiones por cero quedan en NA.
- **Drifting:** Rank dentro de cada mes con el cero fijo: para cada columna de monto (las que empiezan con m, Visa_m o Master_m, y los lags, deltas, tendencia, mínimo y máximo de las variables de monto) se agrega una copia rk_ donde los positivos pasan a (0, 1], los negativos a [-1, 0) y el cero y los NA no cambian. En la familia historia_comportamiento_flujos también se rankean los flujos en pesos. Las columnas sin rankear se mantienen. Según el README, el propósito es comparar entre meses frente a la inflación y el aguinaldo de junio.
- **Variables dentro del mes:** features_perfiles.py: vinculos (cantidad de 7 tipos de vínculo con el banco) y dos señales del mes (saldo negativo con 10 movimientos o menos; Visa_status o Master_status mayor a cero). features_comportamiento.py: 17 variables del mes (entradas y salidas de dinero, cantidad de productos activos y de canales usados, y 13 cocientes como consumo sobre límite de tarjeta, comisiones sobre saldo o consumo de tarjeta sobre sueldo). features_flujos.py: 3 tipos de entrada y 5 de salida, neto (entradas menos salidas) y cantidad de productos.
- **Variables históricas:** features_perfiles.py: lag, delta y cociente contra el mes anterior de 21 variables (la lista de 155 conserva 54 de ellos, todos de 1 mes) y 6 señales que comparan con el mes anterior (corte de sueldo, inicio de comisión de mantenimiento, desarme de plazo fijo, fin de préstamo y dos de caída de movimientos; la de plazo fijo no está en la lista de 155). features_historia.py: lag y delta de 1 y 2 meses de todas las variables numéricas, y tendencia (pendiente), mínimo, máximo, actual/promedio y actual/máximo en ventana de 6 meses, que el modelo toma para 40 variables. features_comportamiento.py, ventana de 4 meses: meses desde el máximo, racha de caídas y coeficiente de variación de todas las variables; lag, delta, mínimo y máximo de las 17 variables del mes; productos perdidos respecto del máximo. features_flujos.py, ventana de 4 meses: tendencia, actual/máximo y actual/promedio de 7 columnas (6 flujos y la cantidad de productos), neto acumulado e indicador de producto que dejó de tener.
- **Selección de variables:** El modelo usa dos listas fijas escritas en listas_de_variables.py: FEATURES_BASE_155 (según su docstring, las 150 de mayor importancia del ranking de 2_seleccion_de_variables más 5 de préstamos personales) y FEATURES_HISTORIA_40 (las variables que reciben las columnas de ventana de 6 meses). Los scripts paso_1 a paso_4 que producen esos rankings (importancia gain, descarte de variables sin uso, constantes o con correlación de Spearman mayor a 0,95) están en la entrega y no se ejecutan en el camino de la predicción. Master_fultimo_cierre y Visa_fultimo_cierre figuran en los conjuntos EXCLUIR de features_historia.py y features_comportamiento.py y no están en FEATURES_BASE_155.
- **Optimización de hiperparámetros:** No se observa en el código: los hiperparámetros están escritos como constantes en 3_modelos/comun.py.
- **Hiperparámetros finales:** objective=binary, max_bin=31, min_data_in_leaf=0, feature_fraction=0.5, feature_fraction_bynode=0.2, learning_rate=0.005, num_leaves=63, min_sum_hessian_in_leaf=10.0, num_threads=4 y 2.000 árboles (num_boost_round), iguales para los 27 modelos.
- **Semillas:** 27 entrenamientos con semillas escritas en cada entrenar.py: 5 en historia, 9 en historia_comportamiento (corridas de 5, 1, 2 y 1) y 13 en historia_comportamiento_flujos (corridas de 5, 3 y 5). Son los primeros 5, 9 y 13 valores de SEMILLAS_MODELOS, una lista de 20 que según el docstring de listas_de_variables.py sale de np.random.default_rng(SEMILLA).choice(1_000_000, size=20, replace=False), con SEMILLA = 130399 (semillas.py). En total hay 13 valores de semilla distintos. Según el docstring de comun.py, cada corrida arma el dataset de LightGBM una sola vez y los bins dependen de la primera semilla que se entrena.
- **Cantidad de semillas:** 27
- **Ensamble:** Promedio de las probabilidades de 27 modelos LightGBM, cada uno con el mismo peso: 5 de la familia historia, 9 de historia_comportamiento y 13 de historia_comportamiento_flujos. Las familias difieren en el conjunto de variables y comparten los hiperparámetros.
- **Corte:** Cantidad fija: los 11.000 clientes de mayor probabilidad promedio (CORTE = 11_000 en armar_ensamble.py); los empates se resuelven por numero_de_cliente.
- **Validación:** El camino de la entrega no incluye validación: entrena con 202103 a 202106 y predice 202108. Fuera de ese camino, paso_1 entrena con 202103 y 202104 y paso_3 con 202104, y ambos calculan en 202106 la ganancia acumulada por corte (1.072.500 por cada BAJA+2 y -27.500 por cada uno de los demás).
- **Salidas:** data/competencia_01.csv (notebook); trabajo/historia/claves.parquet y bloque_NNN.parquet (construir_historia.py); probabilidades/<familia>_<corrida>.npy y numero_de_cliente_agosto.npy (entrenar.py); 4_ensamble/salida/prediccion_final.csv y meta.json (armar_ensamble.py).

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Mínimos y máximos de ventana (`variables.min_max_ventana`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)

## Técnicas sólo exploradas

- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Random Forest (`modelo.random_forest`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: no
- Entorno declarado: Según el README: Python 3.12.10 en Windows, 4 núcleos (num_threads = 4) y las versiones de requirements.txt (lightgbm 4.7.0, numpy 2.5.3, pandas 3.0.5, pyarrow 25.0.1, scipy 1.18.1, scikit-learn 1.9.1, duckdb 1.5.5, entre otras). El README declara además el SHA-256 del dataset usado y el de la predicción. Los scripts .py arman sus rutas a partir de la ubicación del propio archivo; el notebook usa la ruta de Drive /content/drive/MyDrive/DMEyF/2026/notebooks/data/ sólo cuando detecta Colab y, en local, busca la carpeta data/ subiendo desde el directorio de trabajo. armar_ensamble.py guarda en meta.json las versiones y el sistema con que se corre.

## Pasos del camino de la entrega

1. **Construcción de clase_ternaria.** El notebook carga competencia_01_crudo.csv en DuckDB, arma la grilla completa de clientes por períodos, obtiene con lead la presencia a 1 y 2 meses y asigna CONTINUA, BAJA+2 o BAJA+1 evaluando primero la presencia a 2 meses. Exporta las 6 fotos a data/competencia_01.csv. (`fernando/entrega_competencia_01/1_datos/construccion_target.ipynb` líneas 143–164; `fernando/entrega_competencia_01/1_datos/construccion_target.ipynb` líneas 189–246; `fernando/entrega_competencia_01/1_datos/construccion_target.ipynb` líneas 651–653)
2. **Variables de historia en parquet.** construir_historia.py llama a features_historia.construir, que para todas las variables numéricas calcula por bloques de 15 columnas los lags y deltas de 1 y 2 meses y, en ventana de 6 meses, tendencia, mínimo, máximo, actual/promedio y actual/máximo. Antes pasa ccajas_depositos a NA en 202105. Guarda claves.parquet y un parquet por bloque en trabajo/historia/. (`fernando/entrega_competencia_01/1_datos/construir_historia.py` líneas 9–14; `fernando/entrega_competencia_01/features_historia.py` líneas 18–60)
3. **Lectura del dataset y lista de montos.** preparar lee data/competencia_01.csv, pasa ccajas_depositos a NA en 202105 e identifica como montos las columnas numéricas que empiezan con m, Visa_m o Master_m. (`fernando/entrega_competencia_01/3_modelos/comun.py` líneas 50–55)
4. **Variables de comportamiento y de flujos (según la familia).** En las familias historia_comportamiento e historia_comportamiento_flujos se construyen las columnas x_ (ventana de 4 meses sobre todas las variables y 17 variables del mes con su historia). En historia_comportamiento_flujos se suman las columnas x2_ (entradas y salidas por tipo, neto, tendencias y productos que dejó de tener), sin x2_entradas ni x2_salidas. (`fernando/entrega_competencia_01/3_modelos/comun.py` líneas 57–71; `fernando/entrega_competencia_01/features_comportamiento.py` líneas 71–106; `fernando/entrega_competencia_01/features_flujos.py` líneas 42–67)
5. **Variables de perfiles y lista de 155 features base.** agregar_features suma lags, deltas y cociente contra el mes anterior de 21 variables, 8 señales binarias y vinculos. De la tabla resultante se conservan los meses 202103 a 202106 y 202108 y las 155 columnas de FEATURES_BASE_155, ordenadas por foto_mes. (`fernando/entrega_competencia_01/3_modelos/comun.py` líneas 73–78; `fernando/entrega_competencia_01/features_perfiles.py` líneas 17–56; `fernando/entrega_competencia_01/listas_de_variables.py` líneas 10–166)
6. **Elección de columnas de historia y lista de features.** De los parquet se toman lag 1, lag 2, delta 1 y delta 2 de todas las variables y las cinco columnas de ventana de 6 meses sólo para las 40 variables de FEATURES_HISTORIA_40. La lista de features suma base, historia y una copia rk_ de cada columna de monto (1.395 columnas, verificado con assert), más las columnas de la familia. (`fernando/entrega_competencia_01/3_modelos/comun.py` líneas 80–98; `fernando/entrega_competencia_01/listas_de_variables.py` líneas 168–209)
7. **Armado de la matriz y rank por mes con cero fijo.** Se alinean las filas con los parquet mediante claves.parquet y se llena una matriz float32 columna por columna. Para cada columna con copia rk_ se calcula rankear_con_cero_fijo: percentil dentro del mes para los positivos, percentil negado para los negativos, y cero y NA sin cambios. (`fernando/entrega_competencia_01/3_modelos/comun.py` líneas 42–47; `fernando/entrega_competencia_01/3_modelos/comun.py` líneas 100–136)
8. **Clase binaria y dataset de LightGBM.** Las filas de 202103 a 202106 forman el entrenamiento, con clase 1 si clase_ternaria es BAJA+1 o BAJA+2; las de 202108 quedan como matriz a predecir. Se construye un lgb.Dataset con max_bin 31. (`fernando/entrega_competencia_01/3_modelos/comun.py` líneas 138–145)
9. **Entrenamiento por corridas y semillas.** Cada entrenar.py define sus corridas y semillas (5 en historia; 5, 1, 2 y 1 en historia_comportamiento; 5, 3 y 5 en historia_comportamiento_flujos). entrenar_corrida entrena 2.000 árboles por semilla sobre el mismo dataset, predice 202108 y guarda las probabilidades de la corrida en un .npy. (`fernando/entrega_competencia_01/3_modelos/comun.py` líneas 33–39; `fernando/entrega_competencia_01/3_modelos/comun.py` líneas 148–160; `fernando/entrega_competencia_01/3_modelos/historia/entrenar.py` líneas 14–26; `fernando/entrega_competencia_01/3_modelos/historia_comportamiento/entrenar.py` líneas 14–29; `fernando/entrega_competencia_01/3_modelos/historia_comportamiento_flujos/entrenar.py` líneas 15–29)
10. **Promedio de los 27 modelos y corte.** armar_ensamble.py apila las probabilidades de las 8 corridas (27 filas), promedia por cliente, ordena de mayor a menor con desempate por numero_de_cliente y toma los primeros 11.000. (`fernando/entrega_competencia_01/4_ensamble/armar_ensamble.py` líneas 19–39)
11. **Escritura del CSV, verificación de formato y hash.** Escribe prediccion_final.csv con un numero_de_cliente por línea, verifica cantidad, repetidos, que sean enteros y que pertenezcan a 202108, calcula el SHA-256, lo compara con el declarado y guarda meta.json. (`fernando/entrega_competencia_01/4_ensamble/armar_ensamble.py` líneas 41–60)

## Archivos

- `fernando/entrega_competencia_01/features_comportamiento.py` · principal · Python · 106 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/features_comportamiento.py.txt) — Construye las columnas x_ que usan las familias historia_comportamiento e historia_comportamiento_flujos: para todas las variables numéricas, meses desde el máximo, racha de caídas y coeficiente de variación en ventana de 4 meses; y 17 variables del mes (flujos de dinero, productos, canales y cocientes) con su lag, delta, mínimo y máximo.
- `fernando/entrega_competencia_01/semillas.py` · configuracion · Python · 4 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/semillas.py.txt) — Define SEMILLAS, una tupla de 5 números (primos, según su docstring), y SEMILLA = 130399 (el primero). La importan los cuatro scripts de 2_seleccion_de_variables/.
- `fernando/entrega_competencia_01/requirements.txt` · configuracion · Texto · 15 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/requirements.txt.txt) — Dependencias con versión exacta: lightgbm 4.7.0, numpy 2.5.3, pandas 3.0.5, pyarrow 25.0.1, scipy 1.18.1, scikit-learn 1.9.1, matplotlib 3.11.2, duckdb 1.5.5, duckdb-engine 0.17.0, SQLAlchemy 2.0.54, jupysql 0.11.1, requests 2.34.2, jupyter 1.1.1, nbconvert 7.17.1 e ipykernel 7.3.0.
- `fernando/entrega_competencia_01/features_perfiles.py` · principal · Python · 56 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/features_perfiles.py.txt) — Define agregar_features, que suma a la tabla 114 columnas: lag y delta de 1 y 2 meses y cociente contra el mes anterior de 21 variables, 8 señales binarias (sen_) y vinculos. Devuelve la tabla ampliada y la lista de nombres nuevos.
- `fernando/entrega_competencia_01/features_flujos.py` · principal · Python · 71 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/features_flujos.py.txt) — Construye las columnas x2_ que usa la familia historia_comportamiento_flujos: entradas y salidas de dinero por tipo, neto, y en ventana de 4 meses tendencia, actual/máximo, actual/promedio, neto acumulado e indicadores de producto que el cliente dejó de tener. Define MONTOS_X2, la lista de flujos en pesos.
- `fernando/entrega_competencia_01/README.md` · explicacion · Markdown · 57 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/README.md.txt) — Presenta la entrega: ensamble de 27 LightGBM con corte en 11.000 clientes, SHA-256 del archivo, descripción de las tres familias de modelos, pasos para replicar, entorno usado y contenido de cada carpeta. Indica que 2_seleccion_de_variables/ contiene los pasos con los que se llegó a las listas fijas de features.
- `fernando/entrega_competencia_01/features_historia.py` · principal · Python · 71 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/features_historia.py.txt) — Calcula las variables de historia con prefijo h_ para todas las columnas numéricas (lags y deltas de 1 y 2 meses; tendencia, mínimo, máximo y dos cocientes en ventana de 6 meses) y las guarda en parquet por bloques de 15 columnas. También define cargar, que lee esos parquet para un conjunto de meses.
- `fernando/entrega_competencia_01/listas_de_variables.py` · configuracion · Python · 211 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/listas_de_variables.py.txt) — Listas fijas que importa comun.py: FEATURES_BASE_155 (155 features base) y FEATURES_HISTORIA_40 (40 variables que reciben las columnas de ventana de 6 meses). También contiene SEMILLAS_MODELOS, una lista de 20 semillas que ningún otro archivo de la entrega importa.
- `fernando/entrega_competencia_01/3_modelos/verificar_semilla.py` · secundario · Python · 35 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/3_modelos/verificar_semilla.py.txt) — Utilidad de comprobación: reentrena la primera semilla de una corrida de la familia indicada y compara sus probabilidades de 202108 con las guardadas en probabilidades/.
- `fernando/entrega_competencia_01/3_modelos/comun.py` · principal · Python · 160 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/3_modelos/comun.py.txt) — Código compartido por las tres familias: define meses, hiperparámetros y cantidad de árboles; preparar arma la matriz de features de la familia pedida (base, historia, copias rankeadas por mes y variables extra) y el dataset de LightGBM; entrenar_corrida entrena una semilla tras otra y guarda las probabilidades de 202108.
- `fernando/entrega_competencia_01/3_modelos/historia_comportamiento/entrenar.py` · principal · Python · 29 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/3_modelos/historia_comportamiento/entrenar.py.txt) — Entrena la familia historia_comportamiento: 4 corridas con 5, 1, 2 y 1 semillas (9 modelos).
- `fernando/entrega_competencia_01/3_modelos/historia_comportamiento_flujos/entrenar.py` · principal · Python · 29 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/3_modelos/historia_comportamiento_flujos/entrenar.py.txt) — Entrena la familia historia_comportamiento_flujos: 3 corridas con 5, 3 y 5 semillas (13 modelos).
- `fernando/entrega_competencia_01/3_modelos/historia/entrenar.py` · principal · Python · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/3_modelos/historia/entrenar.py.txt) — Entrena la familia historia: una corrida con 5 semillas (975935, 98956, 619348, 491242, 983565).
- `fernando/entrega_competencia_01/1_datos/construir_historia.py` · principal · Python · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/1_datos/construir_historia.py.txt) — Script de entrada del paso 2: llama a features_historia.construir con data/competencia_01.csv y deja los parquet en trabajo/historia/.
- `fernando/entrega_competencia_01/1_datos/construccion_target.ipynb` · principal · Jupyter (python) · 695 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/1_datos/construccion_target.ipynb.txt) — Notebook de Python con SQL sobre DuckDB que parte de competencia_01_crudo.csv (202103 a 202108) y genera competencia_01.csv con la columna clase_ternaria. Incluye consultas de control, un análisis de los clientes intermitentes y un chequeo entre BAJA+2 de un mes y BAJA+1 del siguiente.
- `fernando/entrega_competencia_01/4_ensamble/armar_ensamble.py` · principal · Python · 60 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/4_ensamble/armar_ensamble.py.txt) — Lee las probabilidades de las 8 corridas, promedia los 27 modelos, escribe en salida/prediccion_final.csv los 11.000 clientes de mayor promedio, verifica el formato y compara el SHA-256 con el declarado.
- `fernando/entrega_competencia_01/2_seleccion_de_variables/paso_3_ranking_importancia.py` · secundario · Python · 59 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/2_seleccion_de_variables/paso_3_ranking_importancia.py.txt) — Paso 3 de la selección: ranking de importancia (gain) de las features del paso 2 sin las de préstamos personales, entrenando con 202104, 20 semillas y 400 árboles. Guarda trabajo/seleccion/paso_3/importancia_gain.csv.
- `fernando/entrega_competencia_01/2_seleccion_de_variables/paso_4_variables_con_historia.py` · secundario · Python · 93 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/2_seleccion_de_variables/paso_4_variables_con_historia.py.txt) — Paso 4 de la selección: calcula la importancia de las columnas de historia entrenando con 202103 a 202106 un LightGBM de 2.000 árboles sobre las 155 features, los lags y deltas de 1 y 2 meses de todas las variables, 10 reglas binarias y hojas de un random forest. Guarda trabajo/seleccion/paso_4/importancia_semilla1.csv.
- `fernando/entrega_competencia_01/2_seleccion_de_variables/paso_2_seleccion_features.py` · secundario · Python · 71 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/2_seleccion_de_variables/paso_2_seleccion_features.py.txt) — Paso 2 de la selección: descarta las features con importancia cero en el paso 1, las constantes y, de cada par con correlación de Spearman mayor a 0,95, una de las dos. Guarda las listas en trabajo/seleccion/paso_2/seleccion.json.
- `fernando/entrega_competencia_01/2_seleccion_de_variables/paso_1_importancia_features_perfiles.py` · secundario · Python · 109 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/fsteeb1/fernando/entrega_competencia_01/2_seleccion_de_variables/paso_1_importancia_features_perfiles.py.txt) — Paso 1 de la selección: calcula la importancia (gain) de las variables originales y de las de perfiles entrenando con 202103 y 202104, 10 semillas y 400 árboles, y mide la ganancia en 202106. Guarda importancia.csv y validacion_202106.csv en trabajo/seleccion/paso_1/.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### fernando/entrega_competencia_01/features_comportamiento.py

Construye las columnas x_ que usan las familias historia_comportamiento e historia_comportamiento_flujos: para todas las variables numéricas, meses desde el máximo, racha de caídas y coeficiente de variación en ventana de 4 meses; y 17 variables del mes (flujos de dinero, productos, canales y cocientes) con su lag, delta, mínimo y máximo.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–14] Docstring, ventana de 4 meses y conjunto de 11 columnas excluidas:
#   identificadores, clase, 6 fechas de tarjetas, cliente_edad y cliente_antiguedad.
"""Features de comportamiento del cliente (ventana de 4 meses).

1. Contra su propio pasado, para todas las variables: meses desde el máximo, racha de caídas, coeficiente de variación.
2. Flujos de dinero del mes: entradas, salidas, salidas / entradas, saldo / entradas.
3. Cartera: productos activos, canales usados, productos perdidos respecto del máximo de 4 meses.
4. Relaciones entre productos del mismo mes: consumo / límite de tarjeta, comisiones / saldo, consumo / sueldo, etc.
Para 2, 3 y 4 también: valor del mes anterior, cambio, mínimo y máximo de la ventana.
"""
import numpy as np
import pandas as pd

VENTANA = 4
EXCLUIR = {"numero_de_cliente", "foto_mes", "clase_ternaria", "Master_fultimo_cierre", "Visa_fultimo_cierre",
           "Master_Fvencimiento", "Visa_Fvencimiento", "Master_fechaalta", "Visa_fechaalta", "cliente_edad", "cliente_antiguedad"}


# [Anotación · líneas 17–24] Funciones auxiliares: _z devuelve una columna con los NA en cero (o una serie de
#   ceros si la columna no existe) y _div divide dejando NA donde el denominador es cero.
def _z(df, c):
    return df[c].fillna(0).astype(np.float64) if c in df else pd.Series(0.0, index=df.index)


def _div(a, b):
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    with np.errstate(all="ignore"):
        return np.where(np.abs(b) > 0, a / np.where(b == 0, np.nan, b), np.nan).astype(np.float32)


# [Anotación · líneas 27–39] intrames suma las entradas de dinero (sueldos, transferencias recibidas y cheques
#   depositados) y las salidas (transferencias emitidas, extracciones, cajeros, pagos de servicios, débitos
#   automáticos y cheques emitidos), y arma 12 indicadores de productos activos y 6 de canales usados.
def intrames(df):
    """Variables del mes. df = crudo con todas las filas."""
    z = lambda c: _z(df, c)
    entradas = z("mpayroll") + z("mpayroll2") + z("mtransferencias_recibidas") + z("mcheques_depositados")
    salidas = (z("mtransferencias_emitidas") + z("mextraccion_autoservicio") + z("matm") + z("matm_other") + z("mpagodeservicios")
               + z("mpagomiscuentas") + z("mcuenta_debitos_automaticos") + z("mttarjeta_visa_debitos_automaticos")
               + z("mttarjeta_master_debitos_automaticos") + z("mcheques_emitidos"))
    prods = [z("ctarjeta_visa") > 0, z("ctarjeta_master") > 0, z("cprestamos_personales") > 0, z("cprestamos_prendarios") > 0,
             z("cprestamos_hipotecarios") > 0, z("cplazo_fijo") > 0, (z("cinversion1") + z("cinversion2")) > 0,
             (z("cseguro_vida") + z("cseguro_auto") + z("cseguro_vivienda") + z("cseguro_accidentes_personales")) > 0,
             z("ccaja_seguridad") > 0, z("ccuenta_debitos_automaticos") > 0, z("cpayroll_trx") > 0, z("mcaja_ahorro_dolares") > 0]
    canales = [z("chomebanking_transacciones") > 0, z("cmobile_app_trx") > 0, (z("catm_trx") + z("catm_trx_other")) > 0,
               z("ccajas_transacciones") > 0, z("ccallcenter_transacciones") > 0, z("ctarjeta_debito_transacciones") > 0]
# [Anotación · líneas 40–57] Arma 17 variables del mes: entradas, salidas, salidas/entradas, saldo/entradas,
#   cantidad de productos activos y de canales usados, consumo y saldo de tarjeta sobre el límite de compra,
#   comisiones sobre saldo y sobre rentabilidad, mantenimiento sobre rentabilidad, margen de pasivos sobre
#   margen de activos, consumo de tarjeta y saldo sobre sueldo, transacciones por producto y pagos de tarjeta
#   sobre saldo de tarjeta.
    cons_t = z("mtarjeta_visa_consumo") + z("mtarjeta_master_consumo")
    out = {
        "x_entradas": entradas.astype(np.float32), "x_salidas": salidas.astype(np.float32),
        "x_salidas_sobre_entradas": _div(salidas, entradas), "x_saldo_sobre_entradas": _div(z("mcuentas_saldo"), entradas),
        "x_productos_activos": np.sum(prods, axis=0).astype(np.float32), "x_canales_usados": np.sum(canales, axis=0).astype(np.float32),
        "x_visa_consumo_sobre_limite": _div(z("mtarjeta_visa_consumo"), z("Visa_mlimitecompra")),
        "x_master_consumo_sobre_limite": _div(z("mtarjeta_master_consumo"), z("Master_mlimitecompra")),
        "x_visa_saldo_sobre_limite": _div(z("Visa_msaldototal"), z("Visa_mlimitecompra")),
        "x_comisiones_sobre_saldo": _div(z("mcomisiones"), np.abs(z("mcuentas_saldo")) + 1),
        "x_comisiones_sobre_rentabilidad": _div(z("mcomisiones"), np.abs(z("mrentabilidad")) + 1),
        "x_mantenimiento_sobre_rentabilidad": _div(z("mcomisiones_mantenimiento"), np.abs(z("mrentabilidad")) + 1),
        "x_pasivos_sobre_activos_margen": _div(z("mpasivos_margen"), np.abs(z("mactivos_margen")) + 1),
        "x_consumo_tarjeta_sobre_sueldo": _div(cons_t, z("mpayroll") + z("mpayroll2")),
        "x_saldo_sobre_sueldo": _div(z("mcuentas_saldo"), z("mpayroll") + z("mpayroll2")),
        "x_trx_por_producto": _div(z("ctrx_quarter"), np.sum(prods, axis=0) + 1),
        "x_pagos_tarjeta_sobre_saldo_tarjeta": _div(z("Visa_mpagado") + z("Master_mpagado"), z("Visa_msaldototal") + z("Master_msaldototal")),
    }
    return pd.DataFrame(out, index=df.index)


# [Anotación · líneas 60–68] _ventana arma un arreglo de 4 capas con el valor actual y el de hace 1, 2 y 3
#   meses de las columnas pedidas, uniendo por cliente e índice de mes desplazado.
def _ventana(df, cols):
    """V[k] = valor de hace k meses (k = 0..VENTANA-1), alineado a las filas de df."""
    idx = ((df.foto_mes // 100) * 12 + df.foto_mes % 100).values
    k0 = pd.DataFrame({"numero_de_cliente": df.numero_de_cliente.values, "idx": idx})
    base = df[["numero_de_cliente"] + cols].assign(idx=idx)
    V = [df[cols].values.astype(np.float32)]
    for k in range(1, VENTANA):
        V.append(k0.merge(base.assign(idx=base.idx + k), on=["numero_de_cliente", "idx"], how="left")[cols].values.astype(np.float32))
    return np.stack(V)                                            # (VENTANA, filas, columnas)


# [Anotación · líneas 71–92] construir recorre todas las columnas numéricas no excluidas en bloques de 25 y
#   calcula para cada una, en la ventana de 4 meses: meses desde el máximo (0 si el máximo es el mes actual),
#   racha de caídas (cantidad de bajas consecutivas mes a mes contando desde el mes actual hacia atrás, de 0 a
#   3) y coeficiente de variación (desvío sobre valor absoluto del promedio, con al menos 2 valores).
def construir(crudo):
    """Devuelve DataFrame (numero_de_cliente, foto_mes, x_* ...) para todas las filas del crudo."""
    crudo = crudo.reset_index(drop=True)
    base_cols = [c for c in crudo.columns if c not in EXCLUIR and pd.api.types.is_numeric_dtype(crudo[c])]
    out = {}
    # 1. contra el propio pico, para todas las variables del crudo (en bloques)
    for b in range(0, len(base_cols), 25):
        cs = base_cols[b:b + 25]
        V = _ventana(crudo, cs); cur = V[0]
        with np.errstate(all="ignore"):
            ok = ~np.isnan(V)
            Vm = np.where(ok, V, -np.inf)
            desde_max = np.argmax(Vm, axis=0).astype(np.float32)          # 0 = el máximo es hoy
            desde_max[~ok.any(0)] = np.nan
            baja = (V[:-1] < V[1:])                                       # V[k] < V[k+1]: bajó del mes k+1 al k
            racha = np.zeros(cur.shape, dtype=np.float32); sigue = np.ones(cur.shape, dtype=bool)
            for k in range(VENTANA - 1):
                sigue &= baja[k]; racha += sigue
            n = ok.sum(0); media = np.nanmean(V, axis=0); desv = np.nanstd(V, axis=0)
            cv = np.where((n >= 2) & (np.abs(media) > 0), desv / np.abs(np.where(media == 0, np.nan, media)), np.nan).astype(np.float32)
        for j, c in enumerate(cs):
            out[f"x_{c}_meses_desde_max"] = desde_max[:, j]; out[f"x_{c}_racha_caidas"] = racha[:, j]; out[f"x_{c}_cv"] = cv[:, j]
# [Anotación · líneas 93–106] Calcula las 17 variables del mes y para cada una agrega el valor del mes
#   anterior, la diferencia con él y el mínimo y el máximo de la ventana de 4 meses. Suma
#   x_productos_perdidos_vs_max4 (máximo de productos activos en la ventana menos la cantidad actual) y devuelve
#   una tabla con numero_de_cliente, foto_mes y las columnas x_.
    # 2–4. variables intrames y su historia
    I = intrames(crudo)
    I = pd.concat([crudo[["numero_de_cliente", "foto_mes"]], I], axis=1)
    icols = [c for c in I.columns if c.startswith("x_")]
    V = _ventana(I, icols); cur = V[0]
    with np.errstate(all="ignore"):
        vmin, vmax = np.nanmin(V, axis=0), np.nanmax(V, axis=0)
    for j, c in enumerate(icols):
        out[c] = cur[:, j]; out[f"{c}_lag1"] = V[1][:, j]; out[f"{c}_delta1"] = cur[:, j] - V[1][:, j]
        out[f"{c}_min4"] = vmin[:, j]; out[f"{c}_max4"] = vmax[:, j]
    prod_max = np.nanmax(V[:, :, icols.index("x_productos_activos")], axis=0)
    out["x_productos_perdidos_vs_max4"] = (prod_max - cur[:, icols.index("x_productos_activos")]).astype(np.float32)
    res = pd.DataFrame(out); res.insert(0, "foto_mes", crudo.foto_mes.values); res.insert(0, "numero_de_cliente", crudo.numero_de_cliente.values)
    return res
```

### fernando/entrega_competencia_01/features_perfiles.py

Define agregar_features, que suma a la tabla 114 columnas: lag y delta de 1 y 2 meses y cociente contra el mes anterior de 21 variables, 8 señales binarias (sen_) y vinculos. Devuelve la tabla ampliada y la lista de nombres nuevos.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–14] Docstring y lista VARS_LAG de 21 variables: movimientos, saldos, sueldo, consumos
#   de tarjeta, comisión de mantenimiento, préstamos personales, plazos fijos, homebanking, transferencias
#   recibidas, rentabilidad, márgenes, cantidad de productos y saldos de Visa y Master.
"""Features de perfiles: lags, deltas y ratio de 1 y 2 meses para 21 variables, señales de baja y cantidad de vínculos con el banco.

agregar_features(df) devuelve (df con las features, lista de features nuevas).
Los lags se toman por mes calendario. Quedan vacíos si el cliente no está ese mes.
"""
import numpy as np
import pandas as pd

VARS_LAG = ["ctrx_quarter", "mcuentas_saldo", "mcaja_ahorro", "cpayroll_trx", "mpayroll",
            "mtarjeta_visa_consumo", "mtarjeta_master_consumo", "ctarjeta_debito_transacciones",
            "mcomisiones_mantenimiento", "mprestamos_personales", "mplazo_fijo_pesos",
            "mplazo_fijo_dolares", "chomebanking_transacciones", "mtransferencias_recibidas",
            "ctransferencias_recibidas", "mrentabilidad", "mactivos_margen", "mpasivos_margen",
            "cproductos", "Visa_msaldototal", "Master_msaldototal"]


# [Anotación · líneas 17–28] agregar_features calcula un índice de mes consecutivo y, para k = 1 y 2, une la
#   tabla consigo misma por cliente e índice desplazado para obtener el valor de hace k meses de las 21
#   variables (lag) y la diferencia del valor actual con ese lag (delta).
def agregar_features(df):
    idx = (df.foto_mes // 100) * 12 + df.foto_mes % 100
    base = df[["numero_de_cliente"] + VARS_LAG].assign(idx_mes=idx.values)
    keys = pd.DataFrame({"numero_de_cliente": df.numero_de_cliente.values, "idx_mes": idx.values})
    nuevas = {}
    for k in (1, 2):
        lag = base.assign(idx_mes=base.idx_mes + k).rename(columns={v: f"{v}_lag{k}" for v in VARS_LAG})
        m = keys.merge(lag, on=["numero_de_cliente", "idx_mes"], how="left")
        assert len(m) == len(df)
        for v in VARS_LAG:
            nuevas[f"{v}_lag{k}"] = m[f"{v}_lag{k}"].values
            nuevas[f"{v}_delta{k}"] = df[v].values - m[f"{v}_lag{k}"].values
# [Anotación · líneas 29–31] Para cada una de las 21 variables calcula ratio1: valor actual dividido por el
#   del mes anterior, con NA cuando el mes anterior es cero o falta.
    for v in VARS_LAG:
        l1 = nuevas[f"{v}_lag1"]
        nuevas[f"{v}_ratio1"] = np.where(np.abs(l1) > 0, df[v].values / np.where(l1 == 0, np.nan, l1), np.nan)

# [Anotación · líneas 33–48] Define 8 señales binarias: acreditación de sueldo que pasa de positiva a cero,
#   comisión de mantenimiento que pasa de cero a positiva, plazo fijo (pesos más dólares) que pasa de positivo a
#   cero, préstamo personal que pasa de positivo a cero, ctrx_quarter en 90% o menos y en 70% o menos del mes
#   anterior, saldo negativo con 10 movimientos o menos en el trimestre, y Visa_status o Master_status mayor a
#   cero.
    cero = lambda x: np.nan_to_num(np.asarray(x, dtype=float), nan=0.0)
    l1 = lambda v: nuevas[f"{v}_lag1"]
    pf = cero(df.mplazo_fijo_pesos) + cero(df.mplazo_fijo_dolares)
    pf1 = cero(l1("mplazo_fijo_pesos")) + cero(l1("mplazo_fijo_dolares"))
    sig = {
        "sen_corte_sueldo": (cero(df.cpayroll_trx) == 0) & (cero(l1("cpayroll_trx")) > 0),
        "sen_inicio_mantenimiento": (cero(df.mcomisiones_mantenimiento) > 0) & (cero(l1("mcomisiones_mantenimiento")) == 0) & ~np.isnan(l1("mcomisiones_mantenimiento")),
        "sen_desarme_pf": (pf == 0) & (pf1 > 0),
        "sen_fin_prestamo": (cero(df.mprestamos_personales) == 0) & (cero(l1("mprestamos_personales")) > 0),
        "sen_caida_mov10": nuevas["ctrx_quarter_ratio1"] <= 0.9,
        "sen_caida_mov30": nuevas["ctrx_quarter_ratio1"] <= 0.7,
        "sen_rojo_sin_mov": (df.mcuentas_saldo.values < 0) & (cero(df.ctrx_quarter) <= 10),
        "sen_tarjeta_cierre": (cero(df.Visa_status) > 0) | (cero(df.Master_status) > 0),
    }
    for k, v in sig.items():
        nuevas[k] = np.asarray(v, dtype=np.int8)
# [Anotación · líneas 49–56] Calcula vinculos como la cantidad, de 0 a 7, de estas condiciones: acreditación
#   de sueldo, débitos automáticos en cuenta, débitos automáticos en tarjeta, pago de servicios o
#   pagomiscuentas, plazo fijo, algún seguro y algún préstamo. Devuelve la tabla con las columnas nuevas y la
#   lista de sus nombres.
    vinc = [df.cpayroll_trx > 0, df.ccuenta_debitos_automaticos > 0,
            (df.ctarjeta_visa_debitos_automaticos > 0) | (df.ctarjeta_master_debitos_automaticos > 0),
            (df.cpagomiscuentas > 0) | (df.cpagodeservicios > 0), df.cplazo_fijo > 0,
            df[["cseguro_vida", "cseguro_auto", "cseguro_vivienda", "cseguro_accidentes_personales"]].fillna(0).sum(1) > 0,
            df[["cprestamos_personales", "cprestamos_prendarios", "cprestamos_hipotecarios"]].fillna(0).sum(1) > 0]
    nuevas["vinculos"] = np.sum([v.fillna(False).values for v in vinc], axis=0).astype(np.int8)
    out = pd.concat([df.reset_index(drop=True), pd.DataFrame(nuevas)], axis=1)
    return out, list(nuevas)
```

### fernando/entrega_competencia_01/features_flujos.py

Construye las columnas x2_ que usa la familia historia_comportamiento_flujos: entradas y salidas de dinero por tipo, neto, y en ventana de 4 meses tendencia, actual/máximo, actual/promedio, neto acumulado e indicadores de producto que el cliente dejó de tener. Define MONTOS_X2, la lista de flujos en pesos.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–11] Docstring e importación de VENTANA, _z, _div y _ventana desde
#   features_comportamiento.
"""Features de flujos de dinero (4 meses).

1. Entradas por tipo (sueldo, transferencias, cheques) y salidas por tipo (transferencias, cajero, débitos automáticos,
   pagos de servicios, cheques). Neto = entradas - salidas, y neto acumulado en la ventana de tiempo.
2. Para entradas, salidas y neto: tendencia, actual / máximo y actual / promedio de la ventana de tiempo.
3. Qué producto dejó de tener (lo tuvo en la ventana y hoy no).
"""
import numpy as np
import pandas as pd

from features_comportamiento import VENTANA, _z, _div, _ventana


# [Anotación · líneas 14–28] _base calcula 3 componentes de entradas (sueldo, transferencias y cheques) y 5 de
#   salidas (transferencias, cajero, débitos automáticos, servicios y cheques), los totales de entradas y de
#   salidas y el neto (entradas menos salidas).
def _base(df):
    z = lambda c: _z(df, c)
    comp = {
        "x2_ent_sueldo": z("mpayroll") + z("mpayroll2"),
        "x2_ent_transf": z("mtransferencias_recibidas"),
        "x2_ent_cheques": z("mcheques_depositados"),
        "x2_sal_transf": z("mtransferencias_emitidas"),
        "x2_sal_cajero": z("mextraccion_autoservicio") + z("matm") + z("matm_other"),
        "x2_sal_debitos": z("mcuenta_debitos_automaticos") + z("mttarjeta_visa_debitos_automaticos") + z("mttarjeta_master_debitos_automaticos"),
        "x2_sal_servicios": z("mpagodeservicios") + z("mpagomiscuentas"),
        "x2_sal_cheques": z("mcheques_emitidos"),
    }
    ent = comp["x2_ent_sueldo"] + comp["x2_ent_transf"] + comp["x2_ent_cheques"]
    sal = sum(v for k, v in comp.items() if k.startswith("x2_sal_"))
    comp["x2_entradas"], comp["x2_salidas"], comp["x2_neto"] = ent, sal, ent - sal
# [Anotación · líneas 29–39] Arma 10 indicadores de tenencia de producto (Visa, Master, préstamo, plazo fijo,
#   inversión, seguro, caja de seguridad, débito automático, sueldo y caja de ahorro en dólares) y la cantidad
#   de productos, y devuelve todo en float32 con numero_de_cliente y foto_mes.
    prods = {"visa": z("ctarjeta_visa") > 0, "master": z("ctarjeta_master") > 0, "prestamo": (z("cprestamos_personales") + z("cprestamos_prendarios") + z("cprestamos_hipotecarios")) > 0,
             "plazo_fijo": z("cplazo_fijo") > 0, "inversion": (z("cinversion1") + z("cinversion2")) > 0,
             "seguro": (z("cseguro_vida") + z("cseguro_auto") + z("cseguro_vivienda") + z("cseguro_accidentes_personales")) > 0,
             "caja_seguridad": z("ccaja_seguridad") > 0, "debito_auto": z("ccuenta_debitos_automaticos") > 0, "sueldo": z("cpayroll_trx") > 0,
             "dolares": z("mcaja_ahorro_dolares") > 0}
    for k, v in prods.items():
        comp[f"x2_tiene_{k}"] = v.astype(np.float64)
    comp["x2_productos"] = np.sum([v for v in prods.values()], axis=0).astype(np.float64)
    out = pd.DataFrame({k: np.asarray(v, dtype=np.float32) for k, v in comp.items()})
    out.insert(0, "foto_mes", df.foto_mes.values); out.insert(0, "numero_de_cliente", df.numero_de_cliente.values)
    return out


# [Anotación · líneas 42–57] construir2 toma los 11 montos y x2_productos como columnas de salida, arma la
#   ventana de 4 meses de montos, indicadores y cantidad de productos, y calcula por columna la pendiente de
#   mínimos cuadrados contra la posición del mes, el máximo, el promedio y la suma de la ventana.
def construir2(crudo):
    crudo = crudo.reset_index(drop=True)
    B = _base(crudo)
    montos = [c for c in B.columns if c.startswith(("x2_ent_", "x2_sal_")) or c in ("x2_entradas", "x2_salidas", "x2_neto")]
    tiene = [c for c in B.columns if c.startswith("x2_tiene_")]
    out = {c: B[c].values for c in montos + ["x2_productos"]}
    V = _ventana(B, montos + tiene + ["x2_productos"]); cur = V[0]
    cols = montos + tiene + ["x2_productos"]; j = {c: i for i, c in enumerate(cols)}
    x = -np.arange(VENTANA, dtype=np.float32)
    with np.errstate(all="ignore"):
        ok = ~np.isnan(V); n = ok.sum(0)
        Vz = np.where(ok, V, 0.0); xs = np.where(ok, x[:, None, None], 0.0)
        mx = xs.sum(0) / np.maximum(n, 1); my = Vz.sum(0) / np.maximum(n, 1)
        cov = (np.where(ok, (x[:, None, None] - mx) * (V - my), 0.0)).sum(0); var = (np.where(ok, (x[:, None, None] - mx) ** 2, 0.0)).sum(0)
        tend = np.where((n >= 2) & (var > 0), cov / np.where(var > 0, var, 1), np.nan).astype(np.float32)
        vmax = np.nanmax(V, axis=0); vavg = np.nanmean(V, axis=0); vsum = np.nansum(V, axis=0)
# [Anotación · líneas 58–67] Para 7 columnas (entradas, salidas, neto, sueldo, transferencias emitidas, cajero
#   y cantidad de productos) agrega tendencia, actual/máximo y actual/promedio de la ventana. Agrega el neto
#   acumulado de 4 meses y, por cada uno de los 10 productos, un indicador de que lo tuvo en la ventana y en el
#   mes actual no.
    for c in ("x2_entradas", "x2_salidas", "x2_neto", "x2_ent_sueldo", "x2_sal_transf", "x2_sal_cajero", "x2_productos"):
        k = j[c]
        out[f"{c}_tend4"] = tend[:, k]
        out[f"{c}_sobre_max4"] = _div(cur[:, k], vmax[:, k])
        out[f"{c}_sobre_prom4"] = _div(cur[:, k], vavg[:, k])
    out["x2_neto_acum4"] = vsum[:, j["x2_neto"]].astype(np.float32)
    for c in tiene:       # lo tuvo en la ventana y hoy no
        k = j[c]; out[c.replace("x2_tiene_", "x2_perdio_")] = ((vmax[:, k] > 0) & (cur[:, k] == 0)).astype(np.float32)
    res = pd.DataFrame(out); res.insert(0, "foto_mes", crudo.foto_mes.values); res.insert(0, "numero_de_cliente", crudo.numero_de_cliente.values)
    return res


# [Anotación · líneas 70–71] MONTOS_X2: lista de 12 columnas en pesos que comun.py consulta para decidir qué
#   flujos reciben una copia rankeada por mes.
MONTOS_X2 = ["x2_ent_sueldo", "x2_ent_transf", "x2_ent_cheques", "x2_sal_transf", "x2_sal_cajero", "x2_sal_debitos", "x2_sal_servicios",
             "x2_sal_cheques", "x2_entradas", "x2_salidas", "x2_neto", "x2_neto_acum4"]
```

### fernando/entrega_competencia_01/features_historia.py

Calcula las variables de historia con prefijo h_ para todas las columnas numéricas (lags y deltas de 1 y 2 meses; tendencia, mínimo, máximo y dos cocientes en ventana de 6 meses) y las guarda en parquet por bloques de 15 columnas. También define cargar, que lee esos parquet para un conjunto de meses.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–15] Docstring con la definición de las variables h_ y dos constantes: bloques de 15
#   columnas y columnas excluidas (numero_de_cliente, foto_mes, clase_ternaria, Master_fultimo_cierre y
#   Visa_fultimo_cierre).
"""Features de historia para todas las variables numéricas (prefijo h_).

- lag1, lag2: valor de hace 1 y 2 meses (mismo cliente, si no estaba en ese mes -> queda NA)
- delta1, delta2: valor actual menos el lag
- en la ventana del mes actual y hasta 5 anteriores: tend (pendiente), min, max, ratioavg (actual / promedio),
  ratiomax (actual / máximo)
Se calcula por bloques de columnas y se guarda en parquet (float32), tuve que hacerlo así para no agotar la RAM de mi PC.
Las divisiones por cero quedan NA.
"""
import os
import numpy as np
import pandas as pd

BLOQUE = 15
EXCLUIR = {"numero_de_cliente", "foto_mes", "clase_ternaria", "Master_fultimo_cierre", "Visa_fultimo_cierre"}


# [Anotación · líneas 18–28] construir lee el CSV, pasa ccajas_depositos a NA en 202105, convierte a float32
#   todas las columnas numéricas no excluidas, calcula un índice de mes consecutivo (año × 12 + mes) y guarda
#   claves.parquet con numero_de_cliente y foto_mes. Define la posición de cada mes de la ventana: 0, -1, …, -5.
def construir(ruta_csv, carpeta_out):
    os.makedirs(carpeta_out, exist_ok=True)
    df = pd.read_csv(ruta_csv)
    df.loc[df.foto_mes == 202105, "ccajas_depositos"] = np.nan   # en 202105 viene toda en cero
    cols = [c for c in df.columns if c not in EXCLUIR and pd.api.types.is_numeric_dtype(df[c])]
    df[cols] = df[cols].astype(np.float32)
    idx = ((df.foto_mes // 100) * 12 + df.foto_mes % 100).values
    claves = pd.DataFrame({"numero_de_cliente": df.numero_de_cliente.values, "idx": idx})
    claves[["numero_de_cliente", "foto_mes"]] = df[["numero_de_cliente", "foto_mes"]].values
    claves[["numero_de_cliente", "foto_mes"]].to_parquet(os.path.join(carpeta_out, "claves.parquet"))
    x = -np.arange(6, dtype=np.float32)          # posición de cada mes de la ventana: 0, -1, ..., -5
# [Anotación · líneas 29–36] Para cada bloque de 15 columnas arma un arreglo V de 6 capas, donde V[k] es el
#   valor de hace k meses del mismo cliente. Lo obtiene uniendo la tabla consigo misma por cliente e índice de
#   mes desplazado; queda NA si el cliente no está en ese mes.
    for b in range(0, len(cols), BLOQUE):
        bc = cols[b:b + BLOQUE]
        base = df[["numero_de_cliente"] + bc].assign(idx=idx)
        V = [df[bc].values]                       # V[k] = valor de hace k meses
        for k in range(1, 6):
            m = claves[["numero_de_cliente", "idx"]].merge(base.assign(idx=base.idx + k), on=["numero_de_cliente", "idx"], how="left")
            V.append(m[bc].values.astype(np.float32))
        V = np.stack(V)                           # (6, filas, columnas)
# [Anotación · líneas 37–42] Calcula lag 1 y lag 2 (valor de hace 1 y 2 meses) y delta 1 y delta 2 (valor
#   actual menos el lag) de cada columna del bloque.
        nuevo = {}
        with np.errstate(all="ignore"):
            cur = V[0]
            for k in (1, 2):
                for j, c in enumerate(bc):
                    nuevo[f"h_{c}_lag{k}"] = V[k][:, j]; nuevo[f"h_{c}_delta{k}"] = cur[:, j] - V[k][:, j]
# [Anotación · líneas 43–52] Sobre la ventana de 6 meses y usando sólo los valores presentes calcula: la
#   tendencia como pendiente de mínimos cuadrados del valor contra la posición del mes (NA con menos de 2
#   valores), el mínimo, el máximo, el promedio, el cociente actual/promedio y el cociente actual/máximo (NA
#   cuando el denominador es cero).
            ok = ~np.isnan(V); n = ok.sum(0)
            Vz = np.where(ok, V, 0.0)
            xs = np.where(ok, x[:, None, None], 0.0)
            mx = xs.sum(0) / np.maximum(n, 1); my = Vz.sum(0) / np.maximum(n, 1)
            cov = (np.where(ok, (x[:, None, None] - mx) * (V - my), 0.0)).sum(0)
            var = (np.where(ok, (x[:, None, None] - mx) ** 2, 0.0)).sum(0)
            tend = np.where((n >= 2) & (var > 0), cov / np.where(var > 0, var, 1), np.nan)
            vmin = np.nanmin(V, axis=0); vmax = np.nanmax(V, axis=0); vavg = np.nanmean(V, axis=0)
            ravg = np.where(np.abs(vavg) > 0, cur / np.where(vavg == 0, np.nan, vavg), np.nan)
            rmax = np.where(np.abs(vmax) > 0, cur / np.where(vmax == 0, np.nan, vmax), np.nan)
# [Anotación · líneas 53–60] Guarda las columnas del bloque (lag, delta, tend, min, max, ratioavg y ratiomax
#   con prefijo h_) en bloque_NNN.parquet en float32, imprime el avance, libera memoria y al terminar devuelve
#   la lista de columnas procesadas.
        for j, c in enumerate(bc):
            nuevo[f"h_{c}_tend"] = tend[:, j]; nuevo[f"h_{c}_min"] = vmin[:, j]; nuevo[f"h_{c}_max"] = vmax[:, j]
            nuevo[f"h_{c}_ratioavg"] = ravg[:, j]; nuevo[f"h_{c}_ratiomax"] = rmax[:, j]
        pd.DataFrame({k: np.asarray(v, dtype=np.float32) for k, v in nuevo.items()}).to_parquet(
            os.path.join(carpeta_out, f"bloque_{b // BLOQUE:03d}.parquet"))
        print(f"bloque {b // BLOQUE + 1}/{-(-len(cols) // BLOQUE)} listo ({len(nuevo)} columnas)", flush=True)
        del V, Vz, xs, nuevo
    return cols


# [Anotación · líneas 63–71] cargar devuelve las claves y las columnas pedidas de todos los bloques sólo para
#   los meses indicados. En la entrega la llama paso_4_variables_con_historia.py; comun.py lee los parquet por
#   su cuenta.
def cargar(carpeta, meses, columnas=None):
    """Devuelve (claves, X) solo para los meses pedidos, concatenando los bloques en float32."""
    cl = pd.read_parquet(os.path.join(carpeta, "claves.parquet"))
    mask = cl.foto_mes.isin(meses).values
    partes = []
    for f in sorted(p for p in os.listdir(carpeta) if p.startswith("bloque_")):
        t = pd.read_parquet(os.path.join(carpeta, f), columns=columnas and [c for c in columnas if c in pd.read_parquet(os.path.join(carpeta, f)).columns])
        partes.append(t[mask].reset_index(drop=True))
    return cl[mask].reset_index(drop=True), pd.concat(partes, axis=1)
```

### fernando/entrega_competencia_01/3_modelos/comun.py

Código compartido por las tres familias: define meses, hiperparámetros y cantidad de árboles; preparar arma la matriz de features de la familia pedida (base, historia, copias rankeadas por mes y variables extra) y el dataset de LightGBM; entrenar_corrida entrena una semilla tras otra y guarda las probabilidades de 202108.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–31] Docstring con la composición de las tres familias y la nota sobre el orden de las
#   semillas, imports y rutas: el dataset se busca en data/competencia_01.csv dos niveles arriba de la carpeta
#   de la entrega, la historia en trabajo/historia y las probabilidades en probabilidades/.
"""Código compartido por las tres familias de modelos: arma la matriz de features y entrena una corrida.

Cada familia agrega features a la anterior:
- historia: features_perfiles (155 seleccionadas) + lags y deltas de 1 y 2 meses de todas las variables + tendencia,
  mínimo, máximo y ratios de 6 meses para 40 variables + ranking con cero fijo de los montos.
- historia_comportamiento: lo anterior + features_comportamiento.
- historia_comportamiento_flujos: lo anterior + features_flujos + ranking con cero fijo de los flujos en pesos.

Una corrida construye el dataset de LightGBM una sola vez y entrena las semillas en el orden dado. LightGBM arma los
bins del dataset con la semilla del primer entrenamiento, así que para obtener las mismas probabilidades hay que repetir
las mismas corridas con las semillas en el mismo orden.
"""
import gc
import os
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ENTREGA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ENTREGA)
from features_perfiles import agregar_features
import features_comportamiento
import features_flujos
from listas_de_variables import FEATURES_BASE_155, FEATURES_HISTORIA_40

DATOS = os.path.join(os.path.dirname(os.path.dirname(ENTREGA)), "data", "competencia_01.csv")
HISTORIA = os.path.join(ENTREGA, "trabajo", "historia")
PROBABILIDADES = os.path.join(ENTREGA, "probabilidades")

# [Anotación · líneas 33–39] Constantes: nombres de las tres familias, meses que se cargan (202103 a 202106 y
#   202108), meses de entrenamiento (202103 a 202106), sufijos de las columnas de ventana de 6 meses,
#   hiperparámetros de LightGBM (learning_rate 0,005, num_leaves 63, feature_fraction 0,5,
#   feature_fraction_bynode 0,2, max_bin 31, min_data_in_leaf 0, min_sum_hessian_in_leaf 10) y 2.000 árboles.
FAMILIAS = ("historia", "historia_comportamiento", "historia_comportamiento_flujos")
MESES = [202103, 202104, 202105, 202106, 202108]
MESES_ENTRENAMIENTO = [202103, 202104, 202105, 202106]
EXTRAS = ("tend", "min", "max", "ratioavg", "ratiomax")
PARAMETROS = dict(objective="binary", max_bin=31, min_data_in_leaf=0, feature_fraction=0.5, feature_fraction_bynode=0.2,
                  learning_rate=0.005, num_leaves=63, min_sum_hessian_in_leaf=10.0, verbose=-1, num_threads=4)
ARBOLES = 2000


# [Anotación · líneas 42–47] rankear_con_cero_fijo reemplaza cada valor por su posición relativa dentro del
#   mes: los positivos se rankean entre sí y quedan en (0, 1], los negativos se rankean por valor absoluto y
#   quedan en [-1, 0), y el cero y los NA no cambian.
def rankear_con_cero_fijo(x, mes):
    """Posición de cada valor dentro de su mes: positivos en (0, 1], negativos en [-1, 0), cero y NA sin cambios."""
    x = pd.Series(x, dtype=np.float64)
    pos = x.where(x > 0).groupby(mes).rank(pct=True).values
    neg = -(-x.where(x < 0)).groupby(mes).rank(pct=True).values
    return np.where(x > 0, pos, np.where(x < 0, neg, x.values)).astype(np.float32)


# [Anotación · líneas 50–55] preparar lee el CSV, pasa ccajas_depositos a NA en 202105 y arma la lista de
#   montos: columnas numéricas cuyo nombre empieza con m, Visa_m o Master_m.
def preparar(familia, carpeta_historia=HISTORIA):
    """Devuelve el dataset de entrenamiento, la matriz de agosto y los numero_de_cliente de agosto."""
    assert familia in FAMILIAS
    crudo = pd.read_csv(DATOS)
    crudo.loc[crudo.foto_mes == 202105, "ccajas_depositos"] = np.nan   # en 202105 viene toda en cero
    montos = [c for c in crudo.columns if c.startswith(("m", "Visa_m", "Master_m")) and pd.api.types.is_numeric_dtype(crudo[c])]

# [Anotación · líneas 57–71] Para las familias distintas de historia construye las variables de comportamiento
#   y, en historia_comportamiento_flujos, les une las de flujos sin x2_entradas ni x2_salidas. En esa familia
#   define qué columnas extra se rankean: las de MONTOS_X2, las que empiezan con x_entradas o x_salidas y las
#   tendencias de 4 meses que no son de cantidad de productos, quitando las que tienen 'sobre' en el nombre.
    extra, cols_extra, cols_extra_rk = None, [], []
    if familia != "historia":
        extra = features_comportamiento.construir(crudo)
        extra = extra[extra.foto_mes.isin(MESES)].reset_index(drop=True)
        if familia == "historia_comportamiento_flujos":
            flujos = features_flujos.construir2(crudo)
            flujos = flujos[flujos.foto_mes.isin(MESES)].drop(columns=["x2_entradas", "x2_salidas"]).reset_index(drop=True)
            extra = extra.merge(flujos, on=["numero_de_cliente", "foto_mes"], how="left")
            del flujos
        gc.collect()
        cols_extra = [c for c in extra.columns if c.startswith(("x_", "x2_"))]
        if familia == "historia_comportamiento_flujos":
            cols_extra_rk = [c for c in cols_extra if c in features_flujos.MONTOS_X2 or c.startswith(("x_entradas", "x_salidas"))
                             or (c.endswith("_tend4") and not c.startswith("x2_productos"))]
            cols_extra_rk = [c for c in cols_extra_rk if "sobre" not in c]

# [Anotación · líneas 73–78] Agrega las variables de perfiles al dataset, conserva los 5 meses, los
#   identificadores, la clase y las 155 features base en float32, y ordena por foto_mes.
    base = FEATURES_BASE_155
    full, _ = agregar_features(crudo)
    del crudo
    full = full[full.foto_mes.isin(MESES)][["numero_de_cliente", "foto_mes", "clase_ternaria"] + base].reset_index(drop=True)
    full[base] = full[base].astype(np.float32)
    full = full.sort_values("foto_mes", kind="stable").reset_index(drop=True)

# [Anotación · líneas 80–85] Lee el esquema de los parquet de historia y elige las columnas a usar: lag 1, lag
#   2, delta 1 y delta 2 de todas las variables, más tend, min, max, ratioavg y ratiomax de las 40 variables de
#   FEATURES_HISTORIA_40.
    # columnas de historia: lags y deltas de todas las variables + ventana de 6 meses para las 40 elegidas
    bloques = sorted(f for f in os.listdir(carpeta_historia) if f.startswith("bloque_"))
    esquema = {f: pq.read_schema(os.path.join(carpeta_historia, f)).names for f in bloques}
    todas_h = [c for f in bloques for c in esquema[f]]
    cols_h = [c for c in todas_h if c.endswith(("_lag1", "_lag2", "_delta1", "_delta2"))]
    cols_h += [f"h_{c}_{s}" for c in FEATURES_HISTORIA_40 for s in EXTRAS if f"h_{c}_{s}" in todas_h]

# [Anotación · líneas 87–98] es_monto decide qué columnas reciben una copia rankeada: ninguna con 'ratio' en
#   el nombre; de las h_, los lags, deltas, tendencia, mínimo y máximo de variables de monto; del resto, las que
#   empiezan con m, Visa_m o Master_m. La lista de features queda formada por base, historia y copias rk_
#   (verifica que sean 1.395), más las variables extra de la familia y las copias rk_ de los flujos.
    def es_monto(c):
        if "ratio" in c:
            return False
        if c.startswith("h_"):
            return c.endswith(("_lag1", "_lag2", "_delta1", "_delta2", "_tend", "_min", "_max")) and c[2:].rsplit("_", 1)[0] in montos
        return c.startswith(("m", "Visa_m", "Master_m"))

    feats = base + cols_h
    feats = feats + [f"rk_{c}" for c in feats if es_monto(c)]
    assert len(feats) == 1395, len(feats)
    feats = feats + cols_extra + [f"rk_{c}" for c in cols_extra_rk]
    print(f"{familia}: {len(feats)} features", flush=True)

# [Anotación · líneas 100–106] Con claves.parquet calcula, para cada fila del dataset, su número de fila en
#   los parquet de historia, y verifica que todas tengan correspondencia.
    # fila i de la matriz = fila pos[i] de los parquet de historia
    claves = pd.read_parquet(os.path.join(carpeta_historia, "claves.parquet"))
    claves["_fila"] = np.arange(len(claves))
    pos = full[["numero_de_cliente", "foto_mes"]].merge(claves, on=["numero_de_cliente", "foto_mes"], how="left")["_fila"]
    assert pos.notna().all() and len(pos) == len(full)
    pos = pos.values.astype(np.int64)
    mes = full.foto_mes.values

# [Anotación · líneas 108–136] Llena la matriz X en float32 columna por columna: las features base, las de
#   historia leídas bloque por bloque y las extra de la familia. Cuando la columna tiene copia rk_ la calcula
#   con rankear_con_cero_fijo usando el mes de cada fila.
    X = np.empty((len(full), len(feats)), dtype=np.float32)
    col = {c: j for j, c in enumerate(feats)}
    for c in base:
        v = full[c].values
        X[:, col[c]] = v
        if f"rk_{c}" in col:
            X[:, col[f"rk_{c}"]] = rankear_con_cero_fijo(v, mes)
    pedidas = set(cols_h)
    for f in bloques:
        cs = [c for c in esquema[f] if c in pedidas]
        if not cs:
            continue
        t = pq.read_table(os.path.join(carpeta_historia, f), columns=cs).to_pandas()
        for c in cs:
            v = t[c].values.astype(np.float32)[pos]
            X[:, col[c]] = v
            if f"rk_{c}" in col:
                X[:, col[f"rk_{c}"]] = rankear_con_cero_fijo(v, mes)
        del t
        gc.collect()
    if extra is not None:
        ex = full[["numero_de_cliente", "foto_mes"]].merge(extra, on=["numero_de_cliente", "foto_mes"], how="left")
        del extra
        for c in cols_extra:
            v = ex[c].values.astype(np.float32)
            X[:, col[c]] = v
            if c in cols_extra_rk:
                X[:, col[f"rk_{c}"]] = rankear_con_cero_fijo(v, mes)
        del ex

# [Anotación · líneas 138–145] Separa las filas de entrenamiento (202103 a 202106) de las de 202108, arma la
#   clase binaria (1 si clase_ternaria es BAJA+1 o BAJA+2) y construye el Dataset de LightGBM con max_bin 31.
#   Devuelve el dataset, la matriz de 202108 y sus numero_de_cliente.
    n_entrenamiento = int(full.foto_mes.isin(MESES_ENTRENAMIENTO).sum())
    assert full.foto_mes.values[:n_entrenamiento].max() <= 202106 and (full.foto_mes.values[n_entrenamiento:] == 202108).all()
    ids = full.numero_de_cliente.values[n_entrenamiento:].astype(np.int64)
    y = full.clase_ternaria.isin(["BAJA+1", "BAJA+2"]).astype(int).values[:n_entrenamiento]
    del full
    gc.collect()
    dataset = lgb.Dataset(X[:n_entrenamiento], label=y, feature_name=feats, params={"max_bin": 31}, free_raw_data=True)
    return dataset, X[n_entrenamiento:], ids


# [Anotación · líneas 148–160] entrenar_corrida prepara el dataset una vez y, para cada semilla de la corrida
#   en orden, entrena 2.000 árboles con los hiperparámetros fijos y predice 202108. Guarda las probabilidades de
#   todas las semillas en probabilidades/<familia>_<corrida>.npy y los numero_de_cliente en
#   numero_de_cliente_agosto.npy.
def entrenar_corrida(familia, nombre_corrida, semillas, carpeta_historia=HISTORIA):
    """Entrena las semillas en orden sobre un único dataset y guarda las probabilidades de agosto."""
    os.makedirs(PROBABILIDADES, exist_ok=True)
    salida = os.path.join(PROBABILIDADES, f"{familia}_{nombre_corrida}.npy")
    dataset, x_agosto, ids = preparar(familia, carpeta_historia)
    probabilidades = []
    for i, s in enumerate(semillas, 1):
        modelo = lgb.train({**PARAMETROS, "seed": s}, dataset, num_boost_round=ARBOLES)
        probabilidades.append(modelo.predict(x_agosto))
        print(f"semilla {s} lista ({i} de {len(semillas)})", flush=True)
    np.save(salida, np.array(probabilidades))
    np.save(os.path.join(PROBABILIDADES, "numero_de_cliente_agosto.npy"), ids)
    print(f"guardado: {salida}", flush=True)
```

### fernando/entrega_competencia_01/3_modelos/historia_comportamiento/entrenar.py

Entrena la familia historia_comportamiento: 4 corridas con 5, 1, 2 y 1 semillas (9 modelos).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Docstring de uso, import de entrenar_corrida y definición de la familia
#   historia_comportamiento con 4 corridas: corrida_1 con 5 semillas, corrida_2 con 1 (530890), corrida_3 con 2
#   (363290, 507674) y corrida_4 con 1 (49894).
"""Entrena los modelos de la familia historia_comportamiento y guarda sus probabilidades para agosto en ../../probabilidades.

Uso:
    python entrenar.py                 corre todas las corridas, en orden
    python entrenar.py --corrida corrida_2    corre solo esa corrida
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from comun import HISTORIA, entrenar_corrida

FAMILIA = "historia_comportamiento"
CORRIDAS = {
    "corrida_1": [975935, 98956, 619348, 491242, 983565],
    "corrida_2": [530890],
    "corrida_3": [363290, 507674],
    "corrida_4": [49894],
}

# [Anotación · líneas 22–29] Lee los argumentos --corrida y --historia y ejecuta entrenar_corrida para cada
#   corrida pedida (todas si no se indica ninguna).
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--corrida", choices=list(CORRIDAS))
    p.add_argument("--historia", default=HISTORIA)
    a = p.parse_args()
    for nombre, semillas in CORRIDAS.items():
        if a.corrida in (None, nombre):
            entrenar_corrida(FAMILIA, nombre, semillas, a.historia)
```

### fernando/entrega_competencia_01/3_modelos/historia_comportamiento_flujos/entrenar.py

Entrena la familia historia_comportamiento_flujos: 3 corridas con 5, 3 y 5 semillas (13 modelos).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Docstring de uso, import de entrenar_corrida y definición de la familia
#   historia_comportamiento_flujos con 3 corridas: corrida_1 con 5 semillas, corrida_2 con 3 y corrida_3 con 5.
"""Entrena los modelos de la familia historia_comportamiento_flujos y guarda sus probabilidades para agosto en ../../probabilidades.

Uso:
    python entrenar.py                 corre todas las corridas, en orden
    python entrenar.py --corrida corrida_2    corre solo esa corrida
Opcional: --historia CARPETA, si los parquet de 1_datos/construir_historia.py quedaron en otra carpeta.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from comun import HISTORIA, entrenar_corrida

FAMILIA = "historia_comportamiento_flujos"
CORRIDAS = {
    "corrida_1": [975935, 98956, 619348, 491242, 983565],
    "corrida_2": [530890, 363290, 507674],
    "corrida_3": [49894, 408731, 356218, 305115, 428226],
}

# [Anotación · líneas 22–29] Lee los argumentos --corrida y --historia y ejecuta entrenar_corrida para cada
#   corrida pedida (todas si no se indica ninguna).
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--corrida", choices=list(CORRIDAS))
    p.add_argument("--historia", default=HISTORIA)
    a = p.parse_args()
    for nombre, semillas in CORRIDAS.items():
        if a.corrida in (None, nombre):
            entrenar_corrida(FAMILIA, nombre, semillas, a.historia)
```

### fernando/entrega_competencia_01/3_modelos/historia/entrenar.py

Entrena la familia historia: una corrida con 5 semillas (975935, 98956, 619348, 491242, 983565).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–17] Docstring de uso, import de entrenar_corrida desde comun.py y definición de la
#   familia historia con una corrida de 5 semillas.
"""Entrena los modelos de la familia historia y guarda sus probabilidades para agosto en ../../probabilidades.

Uso:
    python entrenar.py                 corre todas las corridas, en orden
    python entrenar.py --corrida corrida_2    corre solo esa corrida
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from comun import HISTORIA, entrenar_corrida

FAMILIA = "historia"
CORRIDAS = {
    "corrida_1": [975935, 98956, 619348, 491242, 983565],
}

# [Anotación · líneas 19–26] Lee los argumentos --corrida y --historia y ejecuta entrenar_corrida para cada
#   corrida pedida (todas si no se indica ninguna).
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--corrida", choices=list(CORRIDAS))
    p.add_argument("--historia", default=HISTORIA)
    a = p.parse_args()
    for nombre, semillas in CORRIDAS.items():
        if a.corrida in (None, nombre):
            entrenar_corrida(FAMILIA, nombre, semillas, a.historia)
```

### fernando/entrega_competencia_01/1_datos/construir_historia.py

Script de entrada del paso 2: llama a features_historia.construir con data/competencia_01.csv y deja los parquet en trabajo/historia/.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–14] Agrega la carpeta de la entrega al path, arma la ruta del dataset
#   (data/competencia_01.csv, dos niveles arriba de la carpeta de la entrega) y ejecuta construir con salida en
#   trabajo/historia.
"""Construye las features de historia (h_*) para todas las variables y las guarda en ../trabajo/historia.

Necesita data/competencia_01.csv en la raíz del repo (lo genera construccion_target.ipynb).
Uso: python construir_historia.py
"""
import os
import sys

ENTREGA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ENTREGA)
from features_historia import construir

DATOS = os.path.join(os.path.dirname(os.path.dirname(ENTREGA)), "data", "competencia_01.csv")
construir(DATOS, os.path.join(ENTREGA, "trabajo", "historia"))
```

### fernando/entrega_competencia_01/1_datos/construccion_target.ipynb

Notebook de Python con SQL sobre DuckDB que parte de competencia_01_crudo.csv (202103 a 202108) y genera competencia_01.csv con la columna clase_ternaria. Incluye consultas de control, un análisis de los clientes intermitentes y un chequeo entre BAJA+2 de un mes y BAJA+1 del siguiente.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–25] Celdas de texto de presentación: el notebook parte de competencia_01_crudo.csv
#   (fotos 202103 a 202108) y genera competencia_01.csv con clase_ternaria. Indica que, respecto del archivo
#   z101_target_sql.ipynb, la ruta del dataset se detecta según se corra en Colab o en local.
#%% celda 1 [texto]
# Crear la clase Target - `clase_ternaria`

Partimos de `competencia_01_crudo.csv` (fotos **202103 a 202108**, sin target) y generamos
`competencia_01.csv` con la columna adicional `clase_ternaria`, con las categorías
**CONTINUA, BAJA+1 y BAJA+2** (más `NULL` cuando corresponde).

Además de construir el target, producimos:

1. la tabla de **cantidad de clientes por clase y por `foto_mes`**,
2. un **análisis de sensibilidad** del tratamiento de clientes intermitentes (con y sin tratamiento),
3. un **chequeo de consistencia** entre los `BAJA+2` de un mes y los `BAJA+1` del mes siguiente,
4. el `.csv` final.

#%% celda 2 [texto]
## 0. Descarga del dataset y setup

Una sola diferencia con respecto al archivo original `z101_target_sql.ipynb`: `dataset_path` se autodetecta, así el
mismo notebook puede correr en **Colab** y en **local** (VS Code) sin tocar nada.

* en Colab: `/content/drive/MyDrive/DMEyF/2026/notebooks/data/` (hay que montar el Drive antes)
* en local: la carpeta `data/` del repo, es decir `../data/` respecto de `monday/`

Si el dataset ya esta descargado, la celda no vuelve a bajarlo.

# [Anotación · líneas 26–71] Define la URL y el nombre del dataset crudo. Si detecta Colab usa
#   /content/drive/MyDrive/DMEyF/2026/notebooks/data/; en local sube hasta 4 niveles desde el directorio de
#   trabajo buscando una carpeta data o .git. Descarga el archivo con requests sólo si no existe.
#%% celda 3 [código]
import os
import sys
import requests

file_url = "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
dataset_filename = "competencia_01_crudo.csv"

# Colab vs local: mismo notebook, distinta ubicacion del dataset
EN_COLAB = "google.colab" in sys.modules or os.path.isdir("/content")

if EN_COLAB:
    dataset_path = "/content/drive/MyDrive/DMEyF/2026/notebooks/data/"
else:
    # El notebook vive en <repo>/monday/ y el dataset en <repo>/data/, pero el
    # working directory depende del editor (VS Code lo controla con la opcion
    # jupyter.notebookFileRoot). Buscamos data/ subiendo desde el cwd.
    raiz = os.getcwd()
    for _ in range(4):
        if os.path.isdir(os.path.join(raiz, "data")) or os.path.isdir(os.path.join(raiz, ".git")):
            break
        raiz = os.path.dirname(raiz)
    dataset_path = os.path.join(raiz, "data") + os.sep

os.makedirs(dataset_path, exist_ok=True)
print(f"dataset_path = {dataset_path}")

file_path = os.path.join(dataset_path, dataset_filename)

if os.path.exists(file_path):
    print(f"Dataset cargado")
else:
    print(f"Falta el dataset, hay que descargarlo")
    try:
        response = requests.get(file_url, stream=True)
        response.raise_for_status()

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded '{dataset_filename}' to {dataset_path}.")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# [Anotación · líneas 72–93] Instala jupysql, duckdb-engine y duckdb, carga la extensión sql conectada a una
#   base DuckDB en memoria y crea la tabla competencia_01_crudo leyendo el CSV con read_csv_auto.
#%% celda 4 [código]
# %pip en lugar de %%bash
%pip install --quiet jupysql duckdb-engine duckdb

#%% celda 5 [código]
import duckdb
import pandas as pd

%load_ext sql
%config SqlMagic.autopandas = True
%config SqlMagic.feedback = False
%config SqlMagic.displaycon = False

%sql duckdb:///

#%% celda 6 [código]
%%sql
create or replace table competencia_01_crudo as
select
    *
from read_csv_auto("{{dataset_path + dataset_filename}}")

# [Anotación · líneas 94–104] Consulta de control: cantidad de filas y de clientes distintos por foto_mes.
#%% celda 7 [código]
%%sql
-- control basico: deben ser 6 fotos, de 202103 a 202108
select
    foto_mes
    , count(*) as cantidad
    , count(distinct numero_de_cliente) as clientes
from competencia_01_crudo
group by foto_mes
order by foto_mes

# [Anotación · líneas 105–142] Celda de texto con las reglas de construcción: se trabaja con toda la base sin
#   filtrar por cliente_vip, no se agrega información del futuro salvo la clase y 202108 queda sin clase.
#   Presenta la decisión A (clientes intermitentes) y la decisión B (BAJA+1 de 202107).
#%% celda 8 [texto]
## 1. Reglas definidas para construir el target

**1.  Trabajamos con TODA la base, nunca filtrando por `cliente_vip`.** Hay que trabajar con toda la base de
datos, son los Paquete Premium, y no tendria sentido modelar sobre los ~458 registros con
`cliente_vip = 1` en lugar de los ~164 mil por mes. No se hace ningun filtro por
atributo de cliente; la celda de control de la seccion 2 lo verifica mes a mes.

**2. No se agrega NINGUNA informacion del futuro salvo el target.** 

**3. 202108 no tiene clase, y es el mes con el que se predice.** Een 202107 hay que predecir a los que se van a ir en 202109, y el periodo 202108 es
con el que hay que predecir para la primera competencia -- no tiene clase. Es exactamente lo que
implementa la seccion 4.

---

## 1.1 Decisiones de criterio

### Decision A - clientes intermitentes (`TRATAR_INTERMITENTES`)

Hay clientes con huecos: estan, desaparecen un mes, y vuelven (`1 -> 0 -> 1`).
Para la foto en la que todavia estan presentes hay dos lecturas posibles:

| valor | regla | resultado para `1 -> 0 -> 1` |
|---|---|---|
| `True` (**default**) | el `CASE` evalua **`mes_2` primero**: si el cliente esta en `mes_2`, es `CONTINUA` | `CONTINUA` |
| `False` | el `CASE` evalua **`mes_1` primero** (regla ingenua): si falta en `mes_1`, es `BAJA+1` | `BAJA+1` |

Ambas se calculan siempre, en dos columnas distintas, para poder cuantificar el impacto
(seccion 5). Solo una se exporta.

### Decision B - el `BAJA+1` "parcial" de 202107 (`INCLUIR_BAJA1_PARCIAL_202107`)

En 202107 se puede observar `mes_1` (=202108) pero no `mes_2` (=202109, no existe). Es decir:
se puede afirmar `BAJA+1`, pero **no** se puede afirmar `CONTINUA` ni `BAJA+2`.
El parametro **no** cambia la construccion del target (202107 se etiqueta siempre que se pueda);
cambia solamente si ese mes entra o no al set de entrenamiento (seccion 7).

# [Anotación · líneas 143–164] Fija TRATAR_INTERMITENTES = True e INCLUIR_BAJA1_PARCIAL_202107 = False, y
#   elige clase_ternaria_tratada como columna de clase.
#%% celda 9 [código]
# ---------------------------------------------------------------------------
# Decision A: tratamiento de clientes intermitentes (1 -> 0 -> 1)
#   True  = prioriza la presencia futura (mes_2) => el intermitente es CONTINUA
#   False = prioriza la ausencia (mes_1) => el intermitente es BAJA+1
# Ver el analisis de sensibilidad de la seccion 5 antes de cambiarlo.
TRATAR_INTERMITENTES = True

# ---------------------------------------------------------------------------
# Decision B: 202107 solo admite BAJA+1 (no hay 202109 para distinguir
# CONTINUA de BAJA+2). Este flag NO afecta al target, solo al set de training.
#   False = training hasta 202106 inclusive (unicos meses con las 3 clases observables)
#   True  = suma los BAJA+1 de 202107, aceptando la asimetria de clases de ese mes
INCLUIR_BAJA1_PARCIAL_202107 = False

# Columna de target segun la Decision A
COL_TARGET = "clase_ternaria_tratada" if TRATAR_INTERMITENTES else "clase_ternaria_ingenua"

print(f"Criterio intermitentes : {'TRATADO (CONTINUA)' if TRATAR_INTERMITENTES else 'INGENUO (BAJA+1)'}")
print(f"Columna de target      : {COL_TARGET}")
print(f"202107 en training     : {INCLUIR_BAJA1_PARCIAL_202107}")

# [Anotación · líneas 165–188] Celda de texto que describe la construcción: grilla completa de clientes por
#   períodos, indicador de presencia mes_0 y sus adelantos mes_1 y mes_2, y qué clases se pueden afirmar en
#   202107 y en 202108.
#%% celda 10 [texto]
## 2. Construccion del target

1. `periodos` x `clientes` -> `todo`: el producto cartesiano, para que **la ausencia de un cliente
   en un mes tambien sea una fila**.
2. `mes_0`: 1 si el cliente esta en la foto, 0 si no (el `left join` deja `NULL` cuando no esta).
3. `mes_1`, `mes_2`: `lead(mes_0, 1)` y `lead(mes_0, 2)` sobre la grilla completa. Como la grilla
   esta completa, `lead` devuelve `NULL` **solo** al salirse del borde del dataset:
   `mes_2` es `NULL` en 202107 y 202108, y `mes_1` es `NULL` en 202108.
4. El `CASE`. Dos versiones, una por criterio.
5. `where mes_0 = 1`: solo clasificamos las fotos en las que el cliente realmente esta.

### Los bordes, explicitos

| foto_mes | `mes_1` | `mes_2` | que se puede afirmar |
|---|---|---|---|
| 202103..202106 | observable | observable | las tres clases |
| **202107** | observable (202108) | **no existe** (202109) | solo `BAJA+1`; `CONTINUA` y `BAJA+2` quedan `NULL` |
| **202108** | **no existe** | **no existe** | nada: todo `NULL` |

> En SQL `NULL = 0` **no** es verdadero, es `NULL`, y un `NULL` en un `CASE`
> no dispara la rama. Por eso las ramas estan escritas de forma que un `mes_2` desconocido nunca
> pueda caer en `CONTINUA` ni en `BAJA+2`, y se vaya al `else null`.

# [Anotación · líneas 189–234] Crea competencia_01_ambos_criterios: arma el producto cartesiano de clientes y
#   períodos, marca la presencia (mes_0) y con lead obtiene la presencia a 1 y 2 meses. Calcula dos columnas de
#   clase: la 'tratada' evalúa primero mes_2 (presente a dos meses = CONTINUA; presente a un mes y ausente a dos
#   = BAJA+2; ausente a un mes = BAJA+1) y la 'ingenua' evalúa primero mes_1. Conserva sólo las filas en que el
#   cliente está presente.
#%% celda 11 [código]
%%sql
create or replace table competencia_01_ambos_criterios as
with periodos as (
    select distinct foto_mes
    from competencia_01_crudo
), clientes as (
    select distinct numero_de_cliente
    from competencia_01_crudo
), todo as (
    -- producto cartesiano: las ausencias tambien son filas
    select numero_de_cliente, foto_mes
    from clientes cross join periodos
), presencias as (
    select
        c.*
        , if(c.numero_de_cliente is null, 0, 1) as mes_0
        , lead(mes_0, 1) over (partition by t.numero_de_cliente order by foto_mes) as mes_1
        , lead(mes_0, 2) over (partition by t.numero_de_cliente order by foto_mes) as mes_2
    from todo t
    left join competencia_01_crudo c using (numero_de_cliente, foto_mes)
), clasificado as (
    select
        * EXCLUDE (mes_0, mes_1, mes_2)
        -- Criterio TRATADO: evalua mes_2 primero.
        -- El intermitente (mes_1 = 0, mes_2 = 1) cae en CONTINUA.
        , case
            when mes_2 = 1               then 'CONTINUA'  -- presente en el subsiguiente
            when mes_1 = 1 and mes_2 = 0 then 'BAJA+2'    -- esta el proximo, no el subsiguiente
            when mes_1 = 0               then 'BAJA+1'    -- ya no esta el mes proximo
            else null                                     -- futuro insuficiente (202107 / 202108)
          end as clase_ternaria_tratada
        -- Criterio INGENUO: evalua mes_1 primero.
        -- El intermitente (mes_1 = 0, mes_2 = 1) cae en BAJA+1.
        , case
            when mes_1 = 0               then 'BAJA+1'
            when mes_1 = 1 and mes_2 = 0 then 'BAJA+2'
            when mes_1 = 1 and mes_2 = 1 then 'CONTINUA'
            else null
          end as clase_ternaria_ingenua
    from presencias
    where mes_0 = 1
)
select *
from clasificado

# [Anotación · líneas 235–246] Crea la tabla competencia_01 con una sola columna clase_ternaria, tomada de la
#   columna indicada en COL_TARGET.
#%% celda 12 [texto]
La tabla que se entrega lleva **una sola** columna `clase_ternaria`, con exactamente los tres
valores de la consigna mas `NULL`. 

#%% celda 13 [código]
%%sql
create or replace table competencia_01 as
select
    * EXCLUDE (clase_ternaria_tratada, clase_ternaria_ingenua)
    , {{COL_TARGET}} as clase_ternaria
from competencia_01_ambos_criterios

# [Anotación · líneas 247–265] Controles: cantidad de filas por valor de clase_ternaria y comparación de la
#   cantidad total de filas contra el crudo.
#%% celda 14 [código]
%%sql
-- control: no debe aparecer ningun valor distinto de los tres de la consigna
select
    clase_ternaria
    , count(*) as cantidad
from competencia_01
group by clase_ternaria
order by cantidad desc

#%% celda 15 [código]
%%sql
-- control: la cantidad de filas debe ser identica a la del crudo
select
    (select count(*) from competencia_01_crudo) as filas_crudo
    , (select count(*) from competencia_01)     as filas_target
    , (select count(*) from competencia_01_crudo)
      = (select count(*) from competencia_01)   as coinciden

# [Anotación · líneas 266–318] Dos consultas de control: compara las filas por foto_mes entre el crudo y la
#   tabla con clase, y verifica con information_schema que la única columna agregada sea clase_ternaria y que no
#   falte ninguna del crudo.
#%% celda 16 [texto]
### Control de las reglas 1 y 2 de la seccion 1

Dos guardas que conviene mirar cada vez que se toque este notebook:

* **anti-filtrado**: la cantidad de filas por `foto_mes` tiene que ser exactamente la del crudo. Si
  bajara, en algun lado se colo un filtro (por `cliente_vip` o por lo que sea).
* **anti-leakage**: la unica columna nueva respecto del crudo debe ser `clase_ternaria`. Si
  aparecieran `mes_1` o `mes_2`, se estarian exportando variables construidas mirando el futuro.

#%% celda 17 [código]
%%sql
-- Guarda anti-filtrado: ni un cliente de menos en ningun mes
select
    foto_mes
    , c.filas as filas_crudo
    , t.filas as filas_target
    , if(c.filas = t.filas, 'OK', 'REVISAR - se perdieron registros') as control
from (select foto_mes, count(*) as filas from competencia_01_crudo group by foto_mes) c
full join (select foto_mes, count(*) as filas from competencia_01 group by foto_mes) t
    using (foto_mes)
order by foto_mes

#%% celda 18 [código]
%%sql
-- Guarda anti-leakage: la unica columna agregada debe ser clase_ternaria
with cols_crudo as (
    select column_name
    from information_schema.columns
    where table_name = 'competencia_01_crudo'
), cols_target as (
    select column_name
    from information_schema.columns
    where table_name = 'competencia_01'
), agregadas as (
    select column_name from cols_target
    except
    select column_name from cols_crudo
), perdidas as (
    select column_name from cols_crudo
    except
    select column_name from cols_target
)
select
    (select count(*) from cols_crudo)                  as columnas_crudo
    , (select count(*) from cols_target)               as columnas_target
    , (select string_agg(column_name, ', ') from agregadas) as columnas_agregadas
    , (select count(*) from perdidas)                  as columnas_perdidas
    , if((select string_agg(column_name, ', ') from agregadas) = 'clase_ternaria'
         and (select count(*) from perdidas) = 0,
         'OK - solo se agrego el target',
         'REVISAR - hay columnas de mas o de menos')   as control

# [Anotación · líneas 319–348] Tabla de cantidad de clientes por clase y foto_mes, primero con PIVOT y después
#   con una columna adicional para los registros sin clase.
#%% celda 19 [texto]
## 3. Cantidad de clientes por clase y por `foto_mes`

Esta es la tabla que pide la consigna.

#%% celda 20 [código]
%%sql
PIVOT competencia_01
on clase_ternaria
USING count(numero_de_cliente)
GROUP BY foto_mes
ORDER BY foto_mes

#%% celda 21 [texto]
La misma tabla en formato explicito, agregando la columna de registros sin clase (los `NULL` de
202107 / 202108). Es una columna de **reporte**, no una clase del dataset.

#%% celda 22 [código]
%%sql
select
    foto_mes
    , count(*) filter (where clase_ternaria = 'BAJA+1')   as "BAJA+1"
    , count(*) filter (where clase_ternaria = 'BAJA+2')   as "BAJA+2"
    , count(*) filter (where clase_ternaria = 'CONTINUA') as "CONTINUA"
    , count(*) filter (where clase_ternaria is null)      as "sin_clase (NULL)"
    , count(*)                                            as total
from competencia_01
group by foto_mes
order by foto_mes

# [Anotación · líneas 349–385] Verificación de bordes: marca OK si 202108 no tiene clase, si 202107 sólo tiene
#   BAJA+1 y si los meses hasta 202106 no tienen nulos; en cualquier otro caso marca REVISAR.
#%% celda 23 [texto]
## 4. Verificacion de los bordes (202107 y 202108)

Los dos controles que hay que mirar antes de dar por buena cualquier implementacion:

* **202108 no puede tener ninguna clase.** No existen 202109 ni 202110.
* **202107 no puede tener `CONTINUA` ni `BAJA+2`.** Requeririan 202109, que no existe.
  Solo puede tener `BAJA+1`.

Si alguna de estas dos condiciones falla, la logica esta mal: la query estaria "sabiendo" algo que
el dataset no contiene.

#%% celda 24 [código]
%%sql
select
    foto_mes
    , count(*) filter (where clase_ternaria is not null)  as clasificados
    , count(*) filter (where clase_ternaria = 'CONTINUA') as continua
    , count(*) filter (where clase_ternaria = 'BAJA+2')   as baja_mas_2
    , count(*) filter (where clase_ternaria = 'BAJA+1')   as baja_mas_1
    , case
        when foto_mes = 202108
             and count(*) filter (where clase_ternaria is not null) = 0
            then 'OK - 202108 sin clase, como debe ser'
        when foto_mes = 202107
             and count(*) filter (where clase_ternaria in ('CONTINUA', 'BAJA+2')) = 0
             and count(*) filter (where clase_ternaria = 'BAJA+1') > 0
            then 'OK - 202107 solo BAJA+1'
        when foto_mes <= 202106
             and count(*) filter (where clase_ternaria is null) = 0
            then 'OK - mes completo, sin nulos'
        else 'REVISAR'
      end as control
from competencia_01
group by foto_mes
order by foto_mes

# [Anotación · líneas 386–448] Texto y dos consultas sobre los clientes intermitentes: cuántos registros y
#   clientes cambian de clase según el criterio, por foto_mes, y las cantidades de BAJA+1, BAJA+2 y CONTINUA
#   bajo cada criterio con su diferencia.
#%% celda 25 [texto]
## 5. Analisis de sensibilidad: clientes intermitentes

No alcanza con elegir un criterio, hay que **cuantificar cuanto se
mueven las cardinalidades con y sin tratamiento**.

Las dos reglas difieren en **exactamente un caso**: `mes_1 = 0 and mes_2 = 1`. En todas las demas
combinaciones dan lo mismo. Por lo tanto el efecto total del criterio es, por construccion, un
trasvase de registros `BAJA+1 -> CONTINUA` y nada mas.

> **Atencion con el conteo de intermitentes.** "Cliente intermitente" y "cliente cuya clase depende
> del criterio" **no** son el mismo conjunto. Un cliente que desaparece **dos o mas meses** y vuelve
> tiene `mes_1 = 0` *y* `mes_2 = 0`: los dos criterios lo llaman `BAJA+1` por igual, y sin embargo
> reaparece. Con dos meses de horizonte esos casos son invisibles, no hay orden del `CASE` que los
> arregle. La celda 5.e los separa.

#%% celda 26 [código]
%%sql
-- 5.a Cuantos registros / clientes cambian de clase segun el criterio, y en que foto
select
    foto_mes
    , count(*) as registros_afectados
    , count(distinct numero_de_cliente) as clientes_afectados
from competencia_01_ambos_criterios
where clase_ternaria_tratada is distinct from clase_ternaria_ingenua
group by foto_mes
order by foto_mes

#%% celda 27 [código]
%%sql
-- 5.b Cardinalidades por foto_mes bajo cada criterio, y el delta
with tratado as (
    select
        foto_mes
        , count(*) filter (where clase_ternaria_tratada = 'BAJA+1')   as baja1
        , count(*) filter (where clase_ternaria_tratada = 'BAJA+2')   as baja2
        , count(*) filter (where clase_ternaria_tratada = 'CONTINUA') as continua
    from competencia_01_ambos_criterios
    group by foto_mes
), ingenuo as (
    select
        foto_mes
        , count(*) filter (where clase_ternaria_ingenua = 'BAJA+1')   as baja1
        , count(*) filter (where clase_ternaria_ingenua = 'BAJA+2')   as baja2
        , count(*) filter (where clase_ternaria_ingenua = 'CONTINUA') as continua
    from competencia_01_ambos_criterios
    group by foto_mes
)
select
    t.foto_mes
    , i.baja1                 as baja1_ingenuo
    , t.baja1                 as baja1_tratado
    , t.baja1 - i.baja1       as delta_baja1
    , i.baja2                 as baja2_ingenuo
    , t.baja2                 as baja2_tratado
    , t.baja2 - i.baja2       as delta_baja2
    , i.continua              as continua_ingenuo
    , t.continua              as continua_tratado
    , t.continua - i.continua as delta_continua
from tratado t
join ingenuo i using (foto_mes)
order by foto_mes

# [Anotación · líneas 449–498] Para los clientes cuya clase depende del criterio arma una cadena de 0 y 1 con
#   su presencia de 202103 a 202108 y cuenta cuántos clientes hay por patrón.
#%% celda 28 [código]
%%sql
-- 5.c El detalle: historia completa de presencia de cada cliente afectado.
-- Permite distinguir el patron corto (1 -> 0 -> 1) del largo (1 -> 1 -> 0 -> 1).
with afectados as (
    select distinct numero_de_cliente
    from competencia_01_ambos_criterios
    where clase_ternaria_tratada is distinct from clase_ternaria_ingenua
), periodos as (
    select distinct foto_mes from competencia_01_crudo
), grilla as (
    select numero_de_cliente, foto_mes
    from afectados cross join periodos
)
select
    g.numero_de_cliente
    , string_agg(if(c.numero_de_cliente is null, '0', '1'), '' order by g.foto_mes)
        as patron_202103_a_202108
from grilla g
left join competencia_01_crudo c using (numero_de_cliente, foto_mes)
group by g.numero_de_cliente
order by patron_202103_a_202108, g.numero_de_cliente

#%% celda 29 [código]
%%sql
-- 5.d Resumen: cuantos clientes por forma de intermitencia
with afectados as (
    select distinct numero_de_cliente
    from competencia_01_ambos_criterios
    where clase_ternaria_tratada is distinct from clase_ternaria_ingenua
), periodos as (
    select distinct foto_mes from competencia_01_crudo
), grilla as (
    select numero_de_cliente, foto_mes
    from afectados cross join periodos
), patrones as (
    select
        g.numero_de_cliente
        , string_agg(if(c.numero_de_cliente is null, '0', '1'), '' order by g.foto_mes) as patron
    from grilla g
    left join competencia_01_crudo c using (numero_de_cliente, foto_mes)
    group by g.numero_de_cliente
)
select
    patron
    , count(*) as clientes
from patrones
group by patron
order by clientes desc, patron

# [Anotación · líneas 499–554] Sobre todos los clientes cuenta, con expresiones regulares sobre el patrón de
#   presencia, los que tienen huecos de 1, 2, 3 y 4 meses entre dos presencias. Después calcula cuántos
#   registros por mes se perderían si se excluyeran los clientes cuya clase depende del criterio.
#%% celda 30 [texto]
### 5.e Todos los huecos, no solo los que cambian de clase

Universo completo de clientes con al menos un hueco entre dos presencias, abierto por **largo del
hueco**. Solo la primera fila (hueco de 1 mes) es sensible al criterio de la Decision A; el resto
queda etiquetado `BAJA+1` bajo los dos criterios y aun asi reaparece.

#%% celda 31 [código]
%%sql
with periodos as (
    select distinct foto_mes from competencia_01_crudo
), clientes as (
    select distinct numero_de_cliente from competencia_01_crudo
), grilla as (
    select numero_de_cliente, foto_mes
    from clientes cross join periodos
), patrones as (
    select
        g.numero_de_cliente
        , string_agg(if(c.numero_de_cliente is null, '0', '1'), '' order by g.foto_mes) as patron
    from grilla g
    left join competencia_01_crudo c using (numero_de_cliente, foto_mes)
    group by g.numero_de_cliente
)
select
    count(*) filter (where regexp_matches(patron, '1+0+1')) as con_hueco_total
    , count(*) filter (where regexp_matches(patron, '101'))   as hueco_1_mes_sensible_al_criterio
    , count(*) filter (where regexp_matches(patron, '1001'))  as hueco_2_meses
    , count(*) filter (where regexp_matches(patron, '10001')) as hueco_3_meses
    , count(*) filter (where regexp_matches(patron, '100001'))as hueco_4_meses
    , count(*)                                                as clientes_totales
from patrones

#%% celda 32 [texto]
**Tercera opcion, la de "ignorarlos":** sacar del dataset a los clientes con intermitencias en vez
de decidir como etiquetarlos. La celda siguiente mide cuanto costaria.

#%% celda 33 [código]
%%sql
-- 5.f Escenario "excluir intermitentes": cuantos registros se perderian por foto_mes
with intermitentes as (
    select distinct numero_de_cliente
    from competencia_01_ambos_criterios
    where clase_ternaria_tratada is distinct from clase_ternaria_ingenua
)
select
    foto_mes
    , count(*) filter (where clase_ternaria = 'BAJA+1')   as "BAJA+1"
    , count(*) filter (where clase_ternaria = 'BAJA+2')   as "BAJA+2"
    , count(*) filter (where clase_ternaria = 'CONTINUA') as "CONTINUA"
    , count(*) filter (where numero_de_cliente in (select numero_de_cliente from intermitentes))
        as registros_que_se_perderian
from competencia_01
group by foto_mes
order by foto_mes

# [Anotación · líneas 555–612] Chequeo de consistencia: compara la cantidad de BAJA+2 de cada mes con la de
#   BAJA+1 del mes siguiente, en forma agregada y cliente por cliente.
#%% celda 34 [texto]
## 6. Chequeo de consistencia: `BAJA+2` de un mes vs `BAJA+1` del mes siguiente

Un `BAJA+2` en la foto `t` significa: presente en `t`, presente en `t+1`, ausente en `t+2`.
Mirando a ese mismo cliente parado en la foto `t+1`, esta presente y su `mes_1` (= `t+2`) es 0,
o sea es un `BAJA+1` en `t+1`.

De ahi sale la relacion esperada:

> **`BAJA+1(t+1) >= BAJA+2(t)`**, y la diferencia son los clientes que **no estaban** en `t`
> (altas nuevas de `t+1`) y se van en `t+2`.

Bajo el criterio **ingenuo** la desigualdad se cumple siempre, por construccion. Bajo el criterio
**tratado** puede romperse hacia abajo por unos pocos registros: un intermitente que en `t+1` seria
`BAJA+1` pasa a `CONTINUA` y se resta del lado izquierdo. Un desvio de esa magnitud (unidades) es
esperable; un desvio grande seria sintoma de un bug.

#%% celda 35 [código]
%%sql
with cardinalidad as (
    select
        foto_mes
        , count(*) filter (where clase_ternaria = 'BAJA+2') as baja2
        , count(*) filter (where clase_ternaria = 'BAJA+1') as baja1
    from competencia_01
    group by foto_mes
)
select
    foto_mes
    , baja2                                        as baja2_en_t
    , lead(baja1) over (order by foto_mes)         as baja1_en_t_mas_1
    , lead(baja1) over (order by foto_mes) - baja2 as diferencia
from cardinalidad
order by foto_mes

#%% celda 36 [código]
%%sql
-- Verificacion a nivel cliente, no agregada: de los BAJA+2 de t,
-- cuantos aparecen efectivamente como BAJA+1 en t+1
with pares as (
    select
        numero_de_cliente
        , foto_mes
        , clase_ternaria
        , lead(clase_ternaria) over (partition by numero_de_cliente order by foto_mes)
            as clase_mes_siguiente
    from competencia_01
)
select
    foto_mes
    , count(*)                                                              as baja2_en_t
    , count(*) filter (where clase_mes_siguiente = 'BAJA+1')                as siguen_como_baja1
    , count(*) filter (where clase_mes_siguiente is distinct from 'BAJA+1') as excepciones
from pares
where clase_ternaria = 'BAJA+2'
group by foto_mes
order by foto_mes

# [Anotación · líneas 613–645] Crea competencia_01_training con las filas que tienen clase y foto_mes hasta
#   202106 (o todas las que tienen clase si INCLUIR_BAJA1_PARCIAL_202107 es True) y muestra sus cantidades por
#   clase y mes. Esta tabla no se exporta.
#%% celda 37 [texto]
## 7. Set de entrenamiento (Decision B)

Un mes es "limpio" para entrenar solo si sus **tres** clases son observables.
Eso vale hasta **202106**.

* `INCLUIR_BAJA1_PARCIAL_202107 = False` (default): entrenamos hasta 202106.
* `INCLUIR_BAJA1_PARCIAL_202107 = True`: sumamos los `BAJA+1` de 202107. Son etiquetas reales y
  verificables, pero ese mes aporta **solo negativos**, con lo cual su distribucion de clases no es
  comparable con la de los demas meses.

En ninguno de los dos casos entra 202108: es el mes a predecir.

#%% celda 38 [código]
%%sql
create or replace table competencia_01_training as
select *
from competencia_01
where clase_ternaria is not null
  and (foto_mes <= 202106 or {{INCLUIR_BAJA1_PARCIAL_202107}})

#%% celda 39 [código]
%%sql
select
    foto_mes
    , count(*) filter (where clase_ternaria = 'BAJA+1')   as "BAJA+1"
    , count(*) filter (where clase_ternaria = 'BAJA+2')   as "BAJA+2"
    , count(*) filter (where clase_ternaria = 'CONTINUA') as "CONTINUA"
    , count(*)                                            as total
from competencia_01_training
group by foto_mes
order by foto_mes

# [Anotación · líneas 646–654] Exporta la tabla competencia_01 completa (las 6 fotos, incluidos los registros
#   sin clase de 202107 y 202108) a competencia_01.csv dentro de dataset_path.
#%% celda 40 [texto]
## 8. Guardar `competencia_01.csv`

Se exporta la tabla completa (las 6 fotos, incluidos los `NULL` de 202107 y 202108). 

#%% celda 41 [código]
# Ojo: aca va %sql (line magic), no %%sql, porque no es un bloque sino una sola linea de comando.
%sql COPY competencia_01 TO '{{dataset_path}}competencia_01.csv' (FORMAT CSV, HEADER)

# [Anotación · líneas 655–695] Celda de texto con las decisiones que el notebook deja abiertas (patrones de
#   intermitencia, huecos de 2 meses o más, BAJA+1 de 202107, baja de categoría) y una consulta que calcula la
#   cantidad y el porcentaje de registros con cliente_vip = 1 por foto_mes.
#%% celda 42 [texto]
## 9. Decisiones que quedan abiertas

1. **El patron largo `1 -> 1 -> 0 -> 1`.** Con el criterio tratado ese cliente recibe `BAJA+2` en
   `t` y `CONTINUA` en `t+1`, lo cual es contraintuitivo (se "fue" y sigue). Con el criterio ingenuo
   recibe `BAJA+2` y despues `BAJA+1`, una alternativa que se mencionó que es 
   igualmente válida. Es decir, no hay un único criterio válido: se resuelve empiricamente cuando
   corramos los primeros modelos.
2. **Si la intermitencia es comportamiento real o error del dataset.** No sabemos por ahora cuáles son casos reales y cuáles errores. 
3. **Los huecos de 2 meses o mas (celda 5.e).** Ningun criterio de ordenamiento del `CASE` los
   distingue: con `mes_1 = 0` y `mes_2 = 0` el cliente es `BAJA+1` para las dos reglas, y aun asi
   reaparece. Son ruido de etiqueta que el horizonte de dos meses no puede ver. Habria que decidir
   aparte si se los excluye, y esa decision es independiente de la Decision A.
4. **La asimetria interna del criterio tratado en 202107.** Si un intermitente puede volver, un
   cliente presente en 202107 y ausente en 202108 podria reaparecer en 202109 y no ser `BAJA+1`.
   Es decir: el `BAJA+1` de 202107 es estrictamente confiable solo bajo el criterio ingenuo. Dada
   la magnitud del fenomeno (seccion 5.a) el impacto es de unidades, pero la inconsistencia existe
   y es otra razon para el default `INCLUIR_BAJA1_PARCIAL_202107 = False`.
5. **El "downgrade" de categoria como baja parcial.** Un cliente que baja de categoria sin irse del banco 
   no es una baja para `clase_ternaria`, pero quizas si para el negocio. Queda anotado como linea exploratoria 
   para cuando corramos modelos.

---

### Una anomalia de datos detectada de paso (no afecta al target)

`cliente_vip` tiene un pico en **202106**: 921 registros con `cliente_vip = 1` (0,561%) contra
423-458 (0,26-0,28%) en los otros cinco meses. Vuelve a la normalidad en 202107. 

#%% celda 43 [código]
%%sql
-- Chequeo de consistencia longitudinal de cliente_vip.
-- NO se usa para construir el target; queda como registro del hallazgo.
select
    foto_mes
    , count(*) filter (where cliente_vip = 1) as vip
    , count(*)                                as total
    , round(100.0 * count(*) filter (where cliente_vip = 1) / count(*), 3) as pct_vip
from competencia_01
group by foto_mes
order by foto_mes
```

### fernando/entrega_competencia_01/4_ensamble/armar_ensamble.py

Lee las probabilidades de las 8 corridas, promedia los 27 modelos, escribe en salida/prediccion_final.csv los 11.000 clientes de mayor promedio, verifica el formato y compara el SHA-256 con el declarado.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Docstring, imports, rutas de probabilidades y de salida, corte de 11.000 clientes
#   y SHA-256 del archivo entregado.
"""Arma la entrega final: promedio de las probabilidades de los 27 modelos y los 11.000 clientes con mayor probabilidad.

Lee las probabilidades de ../probabilidades (las que dejan los entrenar.py de 3_modelos), escribe
salida/prediccion_final.csv, valida el formato y compara su SHA-256 con el del archivo que entregué.
Uso: python armar_ensamble.py
"""
import hashlib
import json
import os
import platform

import lightgbm
import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
PROBABILIDADES = os.path.join(os.path.dirname(AQUI), "probabilidades")
SALIDA = os.path.join(AQUI, "salida")
CORTE = 11_000
SHA256_ENTREGADO = "2a5a508683301735e4f4b5ab07ccc50c102459479691baf9211e68c3e496663a"

# [Anotación · líneas 22–32] Lista de las 8 corridas en el orden en que se promedian: 4 de
#   historia_comportamiento, 3 de historia_comportamiento_flujos y 1 de historia. El comentario indica que el
#   orden cambia los últimos decimales del promedio.
# en este orden se promediaron para la entrega (el orden cambia los últimos decimales del promedio)
CORRIDAS = [
    "historia_comportamiento_corrida_1",
    "historia_comportamiento_corrida_2",
    "historia_comportamiento_corrida_3",
    "historia_comportamiento_corrida_4",
    "historia_comportamiento_flujos_corrida_1",
    "historia_comportamiento_flujos_corrida_2",
    "historia_comportamiento_flujos_corrida_3",
    "historia_corrida_1",
]

# [Anotación · líneas 34–39] Carga los numero_de_cliente de 202108 y apila las probabilidades de las 8
#   corridas en una matriz de 27 filas. Promedia por cliente, ordena de mayor a menor promedio con desempate por
#   numero_de_cliente y toma los primeros 11.000.
ids = np.load(os.path.join(PROBABILIDADES, "numero_de_cliente_agosto.npy"))
modelos = np.vstack([np.load(os.path.join(PROBABILIDADES, f"{c}.npy")) for c in CORRIDAS])
assert modelos.shape == (27, len(ids)), modelos.shape
promedio = modelos.mean(0)
orden = np.lexsort((ids, -promedio))   # mayor probabilidad primero, empate por numero_de_cliente
elegidos = ids[orden][:CORTE]

# [Anotación · líneas 41–49] Escribe prediccion_final.csv con un numero_de_cliente por línea, sin encabezado,
#   y verifica que tenga 11.000 líneas sin repetidos, que todos los valores sean enteros y que pertenezcan a
#   202108.
os.makedirs(SALIDA, exist_ok=True)
archivo = os.path.join(SALIDA, "prediccion_final.csv")
pd.Series(elegidos).to_csv(archivo, index=False, header=False)

texto = open(archivo, encoding="utf-8").read()
lineas = texto.split()
assert len(lineas) == CORTE and len(set(lineas)) == CORTE, "cantidad de clientes o repetidos"
assert all(x.isdigit() for x in lineas), "hay valores que no son enteros"
assert set(map(int, lineas)) <= set(ids.tolist()), "hay clientes que no son de 202108"

# [Anotación · líneas 51–60] Calcula el SHA-256 del archivo, guarda meta.json con cantidad de modelos, corte,
#   hash, versiones de Python, LightGBM, NumPy y pandas, sistema y núcleos, e imprime si el hash coincide con el
#   entregado.
sha = hashlib.sha256(open(archivo, "rb").read()).hexdigest()
json.dump({"modelos": int(modelos.shape[0]), "corte": CORTE, "sha256": sha, "python": platform.python_version(),
           "lightgbm": lightgbm.__version__, "numpy": np.__version__, "pandas": pd.__version__,
           "sistema": platform.platform(), "nucleos": os.cpu_count()},
          open(os.path.join(SALIDA, "meta.json"), "w", encoding="utf-8"), indent=1)

print(f"archivo generado: {archivo} ({CORTE} clientes)")
print(f"SHA-256 generado:  {sha}")
print(f"SHA-256 entregado: {SHA256_ENTREGADO}")
print(f"coinciden: {'sí' if sha == SHA256_ENTREGADO else 'NO'}")
```


## Explicaciones del alumno (texto original)

### fernando/entrega_competencia_01/README.md

> # Primera Competencia DMEyF 2026 — Fernando Steeb
>
> Entrega final para la competencia 1: un ensamble a partir del promedio de las probabilidades de 27 modelos LightGBM, tomando como punto de corte los 11.000 clientes con mayor probabilidad.
>
> | | |
> |---|---|
> | Archivo | `4_ensamble/salida/prediccion_final.csv` (lo genera `armar_ensamble.py`) |
> | Clientes | 11.000 |
> | SHA-256 | `2a5a508683301735e4f4b5ab07ccc50c102459479691baf9211e68c3e496663a` |
>
> ## Descripción del ensamble final
>
> Entreno con marzo, abril, mayo y junio, con BAJA+1 y BAJA+2 como positivos. Todos los modelos usan los mismos hiperparámetros (están en `3_modelos/comun.py`). Solo cambia la semilla. 
>
> Los 27 modelos se reparten en tres familias. Cada una agrega features a la anterior:
>
> - **historia** (5 modelos): las features de perfiles (`features_perfiles.py`), los lags y deltas de 1 y 2 meses de todas las variables, el mínimo, el máximo y la tendencia de los últimos 6 meses para 40 variables, y el ranking de los montos dentro de cada mes.
> - **historia_comportamiento** (9 modelos): lo anterior más features de cada cliente contra su propio pasado, de entradas y salidas de dinero, de cantidad de productos y canales, y relaciones entre productos del mismo mes (`features_comportamiento.py`).
> - **historia_comportamiento_flujos** (13 modelos): lo anterior más las entradas y salidas desglosadas por tipo, el saldo neto y qué producto dejó de tener (`features_flujos.py`).
>
> Para facilitar la comparación entre meses y controlar el drift producto de la inflación y el aguinaldo de junio, agregué una copia de cada monto con su posición dentro del mes: los positivos entre 0 y 1, los negativos entre −1 y 0, y el cero queda en cero.
>
> ## Cómo replicar la entrega
>
> Usé Python 3.12.10 en Windows, con 4 núcleos (`num_threads = 4`) y las versiones de `requirements.txt`:
>
> ```
> pip install -r requirements.txt
> ```
>
> 1. **Datos.** Correr `1_datos/construccion_target.ipynb`. Genera `data/competencia_01.csv` con `clase_ternaria`. El archivo que usé tiene este SHA-256: `5a33cf43d805f411bde1a65bc86e1df8311d2660c2b162e47f2a78985155b87d`.
> 2. **Features de historia.** `python 1_datos/construir_historia.py`. Deja los parquet en `trabajo/historia/`.
> 3. **Modelos.** En cada carpeta de `3_modelos/`, `python entrenar.py`. Cada familia de modelos se entrenó en varias corridas (están en `CORRIDAS`, dentro de cada `entrenar.py`). Cada corrida arma el dataset de LightGBM con la primera semilla que entrena, así que para obtener exactamente las mismas probabilidades hay que respetar las corridas y el orden de las semillas. Las probabilidades quedan en `probabilidades/`.
> 4. **Ensamble.** `python 4_ensamble/armar_ensamble.py`. Promedia los 27 modelos, toma los 11.000 clientes con mayor probabilidad (ante empate, por `numero_de_cliente`), valida el formato y compara el SHA-256 con el de la entrega.
>
> Las probabilidades de los 27 modelos ya están en `probabilidades/`, así que el paso 4 se puede correr directamente. Para comprobar que el código reproduce uno de los modelos sin reentrenar los 27, `3_modelos/verificar_semilla.py` reentrena la primera semilla de una corrida y la compara con la guardada:
>
> ```
> python 3_modelos/verificar_semilla.py historia corrida_1
> ```
>
> ## Aclaración sobre las listas de features
>
> `listas_de_variables.py` tiene las dos listas fijas que usan los modelos: las 155 features base y las 40 variables con historia de 6 meses. En `2_seleccion_de_variables/` están ordenados los pasos con los que llegué a esas listas (`paso_1` a `paso_4`). Los dejé por si se quiere revisar cómo fue el proceso.
>
> ## Carpetas
>
> ```
> 1_datos/                      clase_ternaria y features de historia
> 2_seleccion_de_variables/     pasos con los que armé las listas de features
> 3_modelos/                    comun.py y una carpeta por familia, con su entrenar.py
> 4_ensamble/                   promedio de los 27 modelos, corte y verificación
> probabilidades/               probabilidades de agosto de cada corrida
> features_*.py                 construcción de las features
> listas_de_variables.py        listas fijas de features y semillas
> semillas.py                   semilla general
> ```

