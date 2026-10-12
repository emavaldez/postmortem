# Luis Daniel Suárez — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: LuisDanielSuarez
- Repositorio: https://github.com/LuisDanielSuarez/dmeyf-competencia1
- Link posteado: https://github.com/LuisDanielSuarez/dmeyf-competencia1
- Commit: a48ed1ee7a4393c5f97c3c97d41807d26f6bdf4c
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/luisdanielsuarez/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/luisdanielsuarez.json

## Resumen

Repositorio en Python con un README y tres carpetas de experimento (L20, L22 y L22b), cada una con la copia de los scripts ejecutados y sus archivos de configuración, más cuatro scripts en la raíz para promediar modelos y armar los envíos. El camino de la entrega tiene cuatro etapas. (1) 01_preprocesamiento_L20.py lee el CSV de la competencia, pasa ccajas_depositos a NA en 202105, arma la clase binaria (BAJA+1 y BAJA+2 = 1), calcula lag1, lag2, delta1, delta2, tendencia y promedio de 3 meses para 142 variables, reemplaza cada variable por su ranking con cero fijo dentro del mes, agrega flags _zero y guarda un parquet. (2) 02_etapa1_L20.py busca con Optuna (10 trials) num_iterations, num_leaves y min_sum_hessian_in_leaf de LightGBM entrenando con 202103-202104 sin las columnas de préstamos personales y midiendo AUC en 202106. (3) 01_entrenar_08_L22.py entrena con 202103 a 202106 y todas las columnas un modelo por semilla y guarda la probabilidad de cada uno sobre 202108; según el README se usaron 45 modelos (33 de L22 y 12 de L22b, corridos en dos máquinas). (4) Los scripts de la raíz promedian las probabilidades y escriben archivos .csv con los N clientes de mayor probabilidad. La etapa 2 de L20 (clase artificial en 202105 y 202106) está en el repositorio y, según el README, no interviene en L22.

**Qué entrega.** Archivos .csv sin encabezado con un numero_de_cliente por línea. 03_submit_L22.py escribe uno con los N clientes de 202108 de mayor probabilidad promedio entre los modelos (N = --corte, entre 8000 y 15000; 10500 en el ejemplo del README). 04_submits_por_corte_L22.py escribe, para cada corte de 9000 a 13000 de a 500, un archivo por cada una de las primeras 20 semillas con los N clientes de mayor probabilidad de ese modelo. El repositorio no incluye los archivos generados ni indica cuál se envió.

**Cómo se ejecuta.** Según el README: copiar todos los archivos de las tres carpetas codigo/ a ~/dmeyf/ y correr desde allí, en orden: (1) python 01_preprocesamiento_L20.py --entrada /ruta/a/competencia_01_ternaria.csv --sin_bucket; (2) python 02_etapa1_L20.py --sin_bucket; (3) python 01_entrenar_08_L22.py --dataset ~/dmeyf/datasets/L20_dataset.parquet --hiperparametros ~/dmeyf/exp/L20/L20_e1_hiperparametros.json --volumen L22 --desde 0 --n_semillas 200 --sin_bucket, y de forma opcional en una segunda máquina el mismo comando con --volumen L22b --desde 200; (4) python 02_ensamblar_08_L22.py --volumen L22 --otros L22b; python 03_submit_L22.py --corte 10500 --volumen L22 --otros L22b; python 04_submits_por_corte_L22.py --volumen L22 --otros L22b --desde 9000 --hasta 13000 --paso 500 --n_semillas 20 --zip. Las carpetas L20 y L22 traen además los scripts correr_L20.sh y correr_L22.sh, que lanzan esos pasos con nohup y log.

## Ficha

- **Lenguajes:** Python, Shell
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (columna clase_binaria): BAJA+1 y BAJA+2 = 1, CONTINUA = 0; el resto de las filas queda en NA.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica: bagging_fraction, pos_bagging_fraction y neg_bagging_fraction valen 1.0, is_unbalance es False y scale_pos_weight es 1.0; se entrena con todas las filas de los meses de entrenamiento.
- **Calidad de datos:** ccajas_depositos se pasa a NA en 202105, después de verificar que en ese mes todos sus valores son cero. No se observa otra corrección en el código.
- **Drifting:** Ranking con cero fijo por variable y por mes, aplicado a las variables originales y a sus lag1, delta1, lag2, delta2, tend3 y avg3: los positivos pasan a (0, 1], los negativos a [−1, 0), el cero queda en cero y los NA se conservan. El valor rankeado reemplaza al crudo. numero_de_cliente, foto_mes y los flags _zero no se rankean.
- **Variables dentro del mes:** Un flag <variable>_zero (1 si el valor crudo es cero, 0 si no, NA si era NA) por cada variable original que alguna vez vale cero. No se arman sumas ni cocientes entre variables (el docstring del preprocesamiento dice "Sin variables derivadas").
- **Variables históricas:** Para 142 variables (las 152 originales menos 10 sin historia: cliente_edad, cliente_antiguedad y 8 fechas de Master y Visa): lag1, lag2, delta1, delta2, tend3 (pendiente de la recta de cuadrados mínimos sobre el mes actual y los 2 anteriores) y avg3 (promedio de esos 3 meses), calculados por unión con (cliente, mes − k); tend3 y avg3 requieren al menos 2 meses.
- **Selección de variables:** No hay selección por importancia. La búsqueda de hiperparámetros excluye 16 columnas (cprestamos_personales, mprestamos_personales y sus variantes _lag1, _delta1, _lag2, _delta2, _tend3, _avg3 y _zero). El entrenamiento final usa todas las columnas del parquet que no empiezan con "clase_", incluidas numero_de_cliente y foto_mes.
- **Optimización de hiperparámetros:** Optuna con TPESampler, 10 trials sobre num_iterations (64 a 4096), num_leaves (16 a 2048) y min_sum_hessian_in_leaf (1e-6 a 0.1); n_startup_trials = 12, con lo que, según el comentario del código, los 10 trials son aleatorios. Cada trial entrena con 202103 y 202104, sin las 16 columnas de préstamos y con la semilla 878443, y mide AUC en 202106. Se toma el trial de mayor AUC.
- **Hiperparámetros finales:** num_iterations 1856, num_leaves 556, min_sum_hessian_in_leaf 0.0368692 (trial 9, AUC 0.92036 en 202106 según L20_e1_hiperparametros.json). Fijos en el código: learning_rate 0.005, feature_fraction 0.50, feature_fraction_bynode 0.20, max_bin 31, min_data_in_leaf 0, max_depth −1, lambda_l1 0, lambda_l2 0, min_gain_to_split 0, bagging_fraction 1.0, boosting gbdt, objective binary. Sin detención temprana.
- **Semillas:** Lista determinística escrita en el código: 878443, 455471, 178447, 235397 y 409027, seguidas de 507928, 515847, … (se suma 7919 a partir de 500009). El volumen L22 toma las posiciones 0 a 199 y L22b las 200 a 399; según el README se usaron las 33 primeras de L22 y las 12 primeras de L22b.
- **Cantidad de semillas:** 45
- **Ensamble:** Promedio aritmético, sin pesos, de las probabilidades de todos los modelos disponibles; los modelos sólo difieren en la semilla. 04_submits_por_corte_L22.py no promedia: arma un archivo por semilla.
- **Corte:** Cantidad fija de clientes, pasada por argumento: --corte en 03_submit_L22.py (entre 8000 y 15000; 10500 en el ejemplo del README) y cortes de 9000 a 13000 de a 500 en 04_submits_por_corte_L22.py. El repositorio no indica qué corte se envió.
- **Validación:** Un mes posterior: la búsqueda entrena con 202103-202104 y mide AUC en 202106. Con los hiperparámetros elegidos, 02_etapa1_L20.py entrena además 10 semillas con 202103-202104 y guarda AUC y curva de ganancia en 202105 y 202106; esos archivos no son leídos por los scripts de L22.
- **Salidas:** datasets/L20_dataset.parquet y su manifiesto JSON; exp/L20/L20_e1_hiperparametros.json y archivos de la búsqueda; exp/<volumen>/ids_08.npy y pred_08/prob_<semilla>.npy; <volumen>_pred_08_ens_<n>modelos.parquet; exp/<volumen>/submit/<nombre>.csv; exp/<volumen>/submit_por_corte/cNNNNN/*.csv con mensajes_submit.txt y resumen.csv. Ninguna de estas salidas está en el repositorio, salvo los JSON de configuración e hiperparámetros.

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
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Optuna (`hiperparametros.optuna`)
- Búsqueda en grilla o al azar (`hiperparametros.grilla_o_azar`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Técnicas sólo exploradas

- Clase artificial o pseudo-etiquetas para meses sin clase (`clase.clase_artificial`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: Según el README: máquina virtual de GCP de 8 núcleos y 60 GB de RAM para L20 y L22, y una de 4 núcleos para L22b; carpeta de trabajo ~/dmeyf/ y bucket gs://luisdsuarez_buckito2026. Los config.json registran lightgbm 4.7.0, pandas 2.3.3 y rutas bajo /home/ds/dmeyf/. El docstring del preprocesamiento indica pip install pandas pyarrow gcsfs. No hay archivo de dependencias.

## Pasos del camino de la entrega

1. **Lectura del CSV y controles de entrada.** Lee competencia_01_ternaria.csv con las variables en float64 y verifica que haya 152 variables originales, que no haya pares (cliente, mes) duplicados y que existan las columnas esperadas. (`L20/codigo/01_preprocesamiento_L20.py` líneas 102–113)
2. **ccajas_depositos a NA en 202105.** Verifica que ccajas_depositos sea cero en todas las filas de 202105 y la pasa a NA en ese mes. (`L20/codigo/01_preprocesamiento_L20.py` líneas 115–123)
3. **Clase binaria.** Crea clase_binaria: BAJA+1 y BAJA+2 = 1, CONTINUA = 0, NA en el resto; verifica que 202103 a 202106 tengan clase y que 202108 no. (`L20/codigo/01_preprocesamiento_L20.py` líneas 125–132)
4. **Variables históricas por unión.** Con una clave cliente-período ubica la fila del mismo cliente 1 y 2 meses antes y calcula, para las 142 variables con historia, lag1, lag2, delta1, delta2, tend3 y avg3. Antes compara el lag1 con un merge de pandas y la tendencia y el promedio con np.polyfit sobre una muestra de 2.000 filas. (`L20/codigo/01_preprocesamiento_L20.py` líneas 134–171; `L20/codigo/01_preprocesamiento_L20.py` líneas 201–213; `L20/codigo/preproc_comun.py` líneas 45–83)
5. **Ranking con cero fijo por mes.** Cada variable original y cada variable histórica se reemplaza por su rango percentil dentro del mes: positivos en (0, 1], negativos en [−1, 0), cero en cero, NA en NA. (`L20/codigo/preproc_comun.py` líneas 29–42; `L20/codigo/01_preprocesamiento_L20.py` líneas 191–199)
6. **Flags _zero.** Para las variables originales que alguna vez valen cero agrega <variable>_zero (1, 0 o NA), calculado sobre el valor crudo y sin rankear. (`L20/codigo/01_preprocesamiento_L20.py` líneas 173–175; `L20/codigo/01_preprocesamiento_L20.py` líneas 214–219; `L20/codigo/preproc_comun.py` líneas 86–88)
7. **Escritura del dataset.** Escribe L20_dataset.parquet con compresión zstd y un manifiesto JSON con las listas de variables; de forma opcional copia ambos al bucket. (`L20/codigo/01_preprocesamiento_L20.py` líneas 230–251)
8. **Búsqueda de hiperparámetros.** Entrena con 202103 y 202104 sin las 16 columnas de préstamos y corre 10 trials de Optuna sobre num_iterations, num_leaves y min_sum_hessian_in_leaf, midiendo AUC en 202106. Guarda el trial de mayor AUC en L20_e1_hiperparametros.json (num_iterations 1856, num_leaves 556, min_sum_hessian_in_leaf 0.0368692). (`L20/codigo/02_etapa1_L20.py` líneas 67–89; `L20/codigo/comun_L20.py` líneas 171–209; `L20/L20_e1_hiperparametros.json` líneas 1–8)
9. **Entrenamiento final por semilla.** Con esos hiperparámetros entrena, sobre 202103 a 202106 y todas las columnas, un modelo LightGBM por semilla del rango pedido y guarda la probabilidad sobre 202108 en pred_08/prob_<semilla>.npy. Se corre en dos volúmenes: L22 (posiciones 0 a 199) y L22b (200 a 399). (`L22/codigo/01_entrenar_08_L22.py` líneas 64–114; `L22/codigo/comun_L22.py` líneas 159–162; `L22/config.json` líneas 38–50; `L22b/config.json` líneas 45–50)
10. **Promedio de los modelos.** Reúne las predicciones guardadas en las carpetas de los volúmenes, verifica que correspondan a los mismos clientes en el mismo orden y calcula prob_ens como el promedio de las probabilidades. (`02_ensamblar_08_L22.py` líneas 24–36; `comun_L22.py` líneas 275–315)
11. **Archivo de envío con el promedio.** Ordena los clientes de 202108 por prob_ens, toma los --corte primeros y escribe un .csv sin encabezado con un numero_de_cliente por línea; relee el archivo y verifica su formato. (`03_submit_L22.py` líneas 39–67)
12. **Archivos por corte y por semilla.** Para cada corte de la lista (9000 a 13000 de a 500 por defecto) y cada una de las primeras 20 semillas escribe un .csv con los clientes de mayor probabilidad de ese modelo, en una carpeta por corte, con un resumen y el texto de los mensajes. (`04_submits_por_corte_L22.py` líneas 46–95)

## Archivos

- `02_ensamblar_08_L22.py` · principal · Python · 40 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/02_ensamblar_08_L22.py.txt) — Promedia las probabilidades sobre 202108 de todos los modelos disponibles (del volumen y de los volúmenes de --otros) y escribe un parquet con numero_de_cliente y prob_ens.
- `README.md` · explicacion · Markdown · 95 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/README.md.txt) — Texto de presentación: resume el método en 4 pasos, muestra la estructura de carpetas (con prefijos exp/ e hiperparametros/; en el repositorio L20, L22 y L22b están en la raíz), declara el entorno (bucket de GCS, máquina de 8 núcleos y 60 GB, L22b en una de 4 núcleos) y da los comandos de reproducción paso a paso. Indica que de L22 se usaron las 33 primeras semillas y de L22b las 12 primeras.
- `04_submits_por_corte_L22.py` · principal · Python · 99 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/04_submits_por_corte_L22.py.txt) — Arma varios envíos, uno por línea de corte: para cada corte y cada una de las primeras --n_semillas semillas con predicción escribe un .csv con los clientes de mayor probabilidad según ese modelo individual (no según el promedio). Llama a cm.predicciones_08_disponibles, función que no está definida en las copias de comun_L22.py del repositorio.
- `comun_L22.py` · principal · Python · 315 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/comun_L22.py.txt) — Versión de comun_L22.py ubicada en la raíz, que importan los scripts 02, 03 y 04. Difiere de la copia de L22/codigo en que importa optuna dentro de un try/except y termina con un mensaje si se llama a la búsqueda sin optuna instalado.
- `03_submit_L22.py` · principal · Python · 71 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/03_submit_L22.py.txt) — Arma un archivo de envío: promedia las probabilidades de los modelos disponibles, ordena los clientes de 202108 por ese promedio y escribe en un .csv sin encabezado los --corte primeros numero_de_cliente.
- `L20/config_e1.json` · configuracion · JSON · 71 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L20/config_e1.json.txt) — Configuración registrada por la etapa 1 de L20: rangos de búsqueda, 10 trials, n_startup_trials 12, semilla 878443, parámetros fijos de LightGBM, ruta /home/ds/dmeyf/datasets/L20_dataset.parquet, las 10 semillas y las versiones lightgbm 4.7.0 y pandas 2.3.3.
- `L20/config_e2.json` · configuracion · JSON · 72 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L20/config_e2.json.txt) — Configuración registrada por la etapa 2 de L20: los mismos valores que config_e1.json más la ruta de L20_clase_artificial.parquet.
- `L20/L20_e1_hiperparametros.json` · configuracion · JSON · 62 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L20/L20_e1_hiperparametros.json.txt) — Salida de la búsqueda de la etapa 1: num_iterations 1856, num_leaves 556, min_sum_hessian_in_leaf 0.03686919557819343, trial 9, AUC de validación en 202106 de 0.92036; incluye los parámetros fijos, los meses de entrenamiento (202103, 202104) y las 16 columnas excluidas. Es el archivo que lee 01_entrenar_08_L22.py.
- `L20/codigo/preproc_comun.py` · principal · Python · 88 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L20/codigo/preproc_comun.py.txt) — Módulo con las funciones de cálculo que usa el preprocesamiento: ranking con cero fijo por mes, posición del mes anterior por unión, tendencia y promedio de 3 meses y flag de cero; define las 10 columnas sin historia y las 4 que no se rankean.
- `L20/codigo/comun_L20.py` · principal · Python · 263 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L20/codigo/comun_L20.py.txt) — Módulo compartido por las dos etapas de L20: semillas, parámetros fijos de LightGBM, configuración y bucle de la búsqueda con Optuna, entrenamiento por semilla, carga del parquet, curva de ganancia y respaldo al bucket.
- `L20/codigo/01_preprocesamiento_L20.py` · principal · Python · 255 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L20/codigo/01_preprocesamiento_L20.py.txt) — Genera el dataset L20_dataset.parquet a partir del CSV de la competencia: corrige ccajas_depositos en 202105, arma la clase binaria, calcula las variables históricas, aplica el ranking con cero fijo por mes y agrega los flags _zero.
- `L20/codigo/correr_L20.sh` · principal · Shell · 60 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L20/codigo/correr_L20.sh.txt) — Script de shell que ejecuta en cadena 01_preprocesamiento_L20.py, 02_etapa1_L20.py y 03_etapa2_L20.py (cada uno sólo si el anterior terminó con código 0), con candado contra corridas simultáneas, log, respaldo al bucket y apagado opcional de la máquina.
- `L20/codigo/02_etapa1_L20.py` · principal · Python · 126 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L20/codigo/02_etapa1_L20.py.txt) — Etapa 1 de L20. Parte A: búsqueda de 3 hiperparámetros entrenando con 202103-202104 sin las columnas de préstamos y midiendo AUC en 202106; escribe L20_e1_hiperparametros.json, que es la salida que usa L22. Partes B y C: 10 modelos que predicen 202105 y 202106 y clase artificial por mes (según el README, no intervienen en L22).
- `L20/codigo/03_etapa2_L20.py` · secundario · Python · 113 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L20/codigo/03_etapa2_L20.py.txt) — Etapa 2 de L20: repite la búsqueda y las 10 semillas entrenando con clase real en 202103-202104 y clase artificial en 202105-202106, sin las columnas de préstamos, y evalúa en 202106 con la clase real. Según el README no interviene en L22.
- `L22b/config.json` · configuracion · JSON · 83 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L22b/config.json.txt) — Configuración registrada por el entrenamiento del volumen L22b: igual a L22/config.json salvo el rango de semillas, posiciones 200 a 400 (de 2052133 a 3628014), y la lista de las primeras 25.
- `L22b/hiperparametros_origen.json` · configuracion · JSON · 62 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L22b/hiperparametros_origen.json.txt) — Copia de L20/L20_e1_hiperparametros.json hecha por la corrida del volumen L22b (contenido idéntico).
- `L22b/codigo/01_entrenar_08_L22.py` · principal · Python · 122 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L22b/codigo/01_entrenar_08_L22.py.txt) — Copia idéntica de L22/codigo/01_entrenar_08_L22.py guardada por la corrida del volumen L22b (segunda máquina, posiciones de semilla 200 a 399).
- `L22b/codigo/correr_L22.sh` · principal · Shell · 58 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L22b/codigo/correr_L22.sh.txt) — Copia idéntica de L22/codigo/correr_L22.sh guardada por la corrida del volumen L22b.
- `L22b/codigo/comun_L22.py` · principal · Python · 309 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L22b/codigo/comun_L22.py.txt) — Copia idéntica de L22/codigo/comun_L22.py guardada por la corrida del volumen L22b.
- `L22/config.json` · configuracion · JSON · 83 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L22/config.json.txt) — Configuración registrada por el entrenamiento del volumen L22: rutas del dataset y de los hiperparámetros, los 3 hiperparámetros buscados, los parámetros fijos, meses de entrenamiento 202103 a 202106, mes de predicción 202108, rango de semillas 0 a 200 (de 878443 a 2044214), las primeras 25 semillas y las versiones lightgbm 4.7.0 y pandas 2.3.3.
- `L22/hiperparametros_origen.json` · configuracion · JSON · 62 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L22/hiperparametros_origen.json.txt) — Copia de L20/L20_e1_hiperparametros.json hecha por 01_entrenar_08_L22.py (contenido idéntico).
- `L22/codigo/01_entrenar_08_L22.py` · principal · Python · 122 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L22/codigo/01_entrenar_08_L22.py.txt) — Entrenamiento final: con los hiperparámetros de L20 entrena un modelo LightGBM por semilla con 202103 a 202106 y todas las columnas, y guarda la probabilidad de cada modelo sobre 202108 en un archivo .npy por semilla; al final llama al ensamble.
- `L22/codigo/correr_L22.sh` · principal · Shell · 58 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L22/codigo/correr_L22.sh.txt) — Script de shell que lanza 01_entrenar_08_L22.py con los argumentos recibidos, con candado contra corridas simultáneas, log por volumen, respaldo al bucket y apagado opcional de la máquina.
- `L22/codigo/comun_L22.py` · principal · Python · 309 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/luisdanielsuarez/L22/codigo/comun_L22.py.txt) — Módulo compartido de L22: mismo contenido que comun_L20.py con VOLUMEN = "L22" más la función ensamblar_08, que promedia las probabilidades guardadas por semilla.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### 02_ensamblar_08_L22.py

Promedia las probabilidades sobre 202108 de todos los modelos disponibles (del volumen y de los volúmenes de --otros) y escribe un parquet con numero_de_cliente y prob_ens.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–17] Docstring: el script lee los pred_08/prob_<semilla>.npy ya terminados, los
#   promedia y escribe L22_pred_08_ens_<n>modelos.parquet. Muestra los usos con --n, --top y --otros y el
#   comando gsutil para traer las predicciones de otra máquina.
"""
02_ensamblar_08_L22.py — ensambla las predicciones sobre 08 disponibles hasta el momento (L22).

Se puede correr en cualquier momento, incluso mientras 01_entrenar_08_L22.py sigue entrenando: solo lee los
archivos pred_08/prob_<semilla>.npy ya terminados. Promedia las probabilidades de los modelos (promedio simple)
y escribe L22_pred_08_ens_<n>modelos.parquet con numero_de_cliente (int64) y prob_ens.
También muestra cuánto del top-N del ensamble ya está estabilizado con menos modelos.

Uso (desde ~/dmeyf):
    python 02_ensamblar_08_L22.py                  # todos los modelos disponibles
    python 02_ensamblar_08_L22.py --n 30           # solo los primeros 30 (en el orden fijo de semillas)
    python 02_ensamblar_08_L22.py --top 12000      # N de referencia para la estabilidad
    python 02_ensamblar_08_L22.py --otros L22b     # suma las predicciones de otra VM (carpeta exp/L22b); sin semillas repetidas

Para traer las predicciones de otra VM al bucket/VM actual:
    gsutil -m rsync -r gs://luisdsuarez_buckito2026/exp/L22b ~/dmeyf/exp/L22b
"""
# [Anotación · líneas 18–21] Importa argparse, os y el módulo comun_L22.
import argparse
import os

import comun_L22 as cm


# [Anotación · líneas 24–36] Argumentos --volumen (L22 por defecto), --dir_base (~/dmeyf), --n (usar sólo los
#   primeros n modelos), --top (11000), --otros y --sin_bucket. Arma las rutas exp/<volumen> y llama a
#   ensamblar_08 con la lista de 1000 semillas; luego respalda al bucket salvo que se pase --sin_bucket.
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volumen", default=cm.VOLUMEN)
    ap.add_argument("--dir_base", default=os.path.expanduser("~/dmeyf"))
    ap.add_argument("--n", type=int, default=None, help="usar solo los primeros n modelos disponibles")
    ap.add_argument("--top", type=int, default=11000)
    ap.add_argument("--otros", nargs="*", default=[], help="otros volúmenes (carpetas exp/<volumen>) con más predicciones")
    ap.add_argument("--sin_bucket", action="store_true")
    a = ap.parse_args()
    dir_exp = os.path.join(a.dir_base, "exp", a.volumen)
    otros = [os.path.join(a.dir_base, "exp", v) for v in a.otros]
    cm.ensamblar_08(dir_exp, a.volumen, cm.semillas_n(1000), n=a.n, top=a.top, otros_dirs=otros)
    cm.sync(dir_exp, a.volumen, not a.sin_bucket)


# [Anotación · líneas 39–40] Punto de entrada del script: ejecuta main().
if __name__ == "__main__":
    main()
```

### 04_submits_por_corte_L22.py

Arma varios envíos, uno por línea de corte: para cada corte y cada una de las primeras --n_semillas semillas con predicción escribe un .csv con los clientes de mayor probabilidad según ese modelo individual (no según el promedio). Llama a cm.predicciones_08_disponibles, función que no está definida en las copias de comun_L22.py del repositorio.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–19] Docstring: para cada corte y cada semilla escribe un archivo con los N clientes de
#   mayor probabilidad de ese modelo; cada corte queda en su carpeta cNNNNN dentro de
#   exp/<volumen>/submit_por_corte, junto con mensajes_submit.txt y resumen.csv. Muestra el comando con cortes
#   de 9000 a 13000 de a 500 y 20 semillas.
"""
04_submits_por_corte_L22.py — arma VARIOS submits (uno por línea de corte), cada uno con un archivo por semilla.

Para cada corte N y para cada una de las primeras --n_semillas semillas disponibles, escribe un .csv con los N clientes
de mayor probabilidad SEGÚN ESE MODELO (no según el ensamble), como pide la cátedra: varios modelos que solo cambian la
semilla, todos con el mismo corte; el bot devuelve la media y el desvío de las ganancias de esos archivos.
Cada corte queda en su propia carpeta:

    exp/<volumen>/submit_por_corte/c09000/L22_s878443_c09000_<fecha>.csv   (20 archivos por carpeta)
    exp/<volumen>/submit_por_corte/c09500/...
    exp/<volumen>/submit_por_corte/mensajes_submit.txt                     (el cuerpo del mensaje para cada carpeta)
    exp/<volumen>/submit_por_corte/resumen.csv

Formato (bot): .csv, SIN encabezado, un numero_de_cliente entero por línea, entre 8000 y 15000 registros.
"Primeras semillas": las primeras en el orden fijo de semillas que tengan predicción guardada (VM de este volumen + --otros).

Uso (desde ~/dmeyf):
    python 04_submits_por_corte_L22.py --volumen L22 --otros L22b --desde 9000 --hasta 13000 --paso 500 --n_semillas 20 --zip
"""
# [Anotación · líneas 20–30] Importa argparse, os, re, shutil, time, numpy, pandas y el módulo comun_L22.
import argparse
import os
import re
import shutil
import time

import numpy as np
import pandas as pd

import comun_L22 as cm
from comun_L22 import log


# [Anotación · líneas 33–44] Argumentos --volumen, --otros, --dir_base, --desde (9000), --hasta (13000),
#   --paso (500), --n_semillas (20), --zip y --prueba.
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volumen", default=cm.VOLUMEN)
    ap.add_argument("--otros", nargs="*", default=[])
    ap.add_argument("--dir_base", default=os.path.expanduser("~/dmeyf"))
    ap.add_argument("--desde", type=int, default=9000)
    ap.add_argument("--hasta", type=int, default=13000)
    ap.add_argument("--paso", type=int, default=500)
    ap.add_argument("--n_semillas", type=int, default=20, help="archivos por submit (el bot admite hasta 20)")
    ap.add_argument("--zip", action="store_true", help="además comprime todo en un .zip para descargarlo de la VM")
    ap.add_argument("--prueba", action="store_true", help="SOLO para probar el código: no exige 8000-15000")
    a = ap.parse_args()

# [Anotación · líneas 46–49] Arma la lista de cortes desde --desde hasta --hasta de a --paso; salvo con
#   --prueba exige que todos estén entre 8000 y 15000, y que la cantidad de semillas esté entre 1 y 20.
    cortes = list(range(a.desde, a.hasta + 1, a.paso))
    if not a.prueba:
        assert all(8000 <= c <= 15000 for c in cortes), "el bot acepta archivos con entre 8000 y 15000 registros"
    assert 1 <= a.n_semillas <= 20, "el bot admite hasta 20 archivos por submit"

# [Anotación · líneas 51–63] Pide a cm.predicciones_08_disponibles los ids de 202108 y la lista de (semilla,
#   ruta, carpeta) de las predicciones guardadas; esa función no figura en ninguna de las tres copias de
#   comun_L22.py del repositorio. Termina si hay menos modelos que los pedidos, toma los primeros --n_semillas,
#   carga sus probabilidades y verifica que tengan la longitud de los ids.
    dir_exp = os.path.join(a.dir_base, "exp", a.volumen)
    otros = [os.path.join(a.dir_base, "exp", v) for v in a.otros]
    ids, disp = cm.predicciones_08_disponibles(dir_exp, cm.semillas_n(1000), otros)
    log(f"  predicciones disponibles: {len(disp)} modelos ({sum(c == a.volumen for _, _, c in disp)} de {a.volumen}, "
        f"{sum(c != a.volumen for _, _, c in disp)} de otras carpetas)")
    if len(disp) < a.n_semillas:
        raise SystemExit(f"Solo hay {len(disp)} modelos y se pidieron {a.n_semillas}. Esperar a que haya más, "
                         f"o pedir menos con --n_semillas.")
    usar = disp[:a.n_semillas]
    log(f"  se usan las primeras {len(usar)} semillas: {[sd for sd, _, _ in usar]}")
    P = {sd: np.load(ruta) for sd, ruta, _ in usar}
    for sd, pr in P.items():
        assert len(pr) == len(ids), f"semilla {sd}: la predicción no tiene los clientes de ids_08"

# [Anotación · líneas 65–70] Toma la fecha y hora para los nombres, exige que exp/<volumen>/submit_por_corte
#   no exista o esté vacía, la crea e inicializa las listas de mensajes y de filas del resumen.
    fecha = time.strftime("%Y%m%d%H%M")
    raiz = os.path.join(dir_exp, "submit_por_corte")
    assert not os.path.exists(raiz) or not os.listdir(raiz), \
        f"{raiz} ya tiene contenido: moverlo o borrarlo antes (cada archivo debe tener un nombre distinto a todos los enviados)"
    os.makedirs(raiz, exist_ok=True)
    mensajes, filas = [], []
# [Anotación · líneas 71–85] Para cada corte crea la carpeta cNNNNN y, para cada semilla, ordena por la
#   probabilidad de ese modelo, toma los primeros c ids, escribe <volumen>_s<semilla>_c<corte>_<fecha>.csv sin
#   encabezado, lo relee y verifica cantidad de líneas y que sean sólo dígitos; guarda en el resumen la
#   probabilidad del último cliente incluido y agrega la línea "submit" de ese corte.
    for c in cortes:
        carpeta = os.path.join(raiz, f"c{c:05d}")
        os.makedirs(carpeta)
        for sd, _, vol in usar:
            orden = np.argsort(-P[sd], kind="stable")[:c]
            sel = ids[orden].astype("int64")
            assert len(np.unique(sel)) == c
            ruta = os.path.join(carpeta, f"{a.volumen}_s{sd}_c{c:05d}_{fecha}.csv")
            pd.Series(sel, dtype="int64").to_csv(ruta, index=False, header=False)
            with open(ruta) as fh:                                       # verificación leyendo el texto
                lin = fh.read().split("\n")
            assert lin[-1] == "" and len(lin) - 1 == c and all(re.fullmatch(r"[0-9]+", l) for l in lin[:-1]), ruta
            filas.append(dict(corte=c, semilla=sd, carpeta_origen=vol, prob_minima_enviada=float(P[sd][orden[-1]])))
        mensajes.append(f"c{c:05d}:  submit    {a.volumen}_{len(usar)}s_c{c:05d}_{fecha}")
        log(f"  corte {c:,}: {len(usar)} archivos en {carpeta}")
# [Anotación · líneas 86–95] Escribe mensajes_submit.txt con el cuerpo del mensaje para cada carpeta y
#   resumen.csv con corte, semilla, carpeta de origen y probabilidad mínima enviada. Con --zip comprime
#   submit_por_corte en un .zip. Imprime los mensajes.
    with open(os.path.join(raiz, "mensajes_submit.txt"), "w") as fh:
        fh.write("Cuerpo del mensaje a @competencia-uno para cada carpeta (adjuntar los archivos de esa carpeta):\n\n"
                 + "\n".join(mensajes) + "\n")
    pd.DataFrame(filas).to_csv(os.path.join(raiz, "resumen.csv"), index=False)
    total = len(cortes) * len(usar)
    log(f"  listo: {len(cortes)} carpetas, {total} archivos en {raiz}")
    if a.zip:
        z = shutil.make_archive(raiz, "zip", root_dir=dir_exp, base_dir="submit_por_corte")
        log(f"  comprimido para descargar: {z} ({os.path.getsize(z) / 1e6:.1f} MB)")
    print("\n" + open(os.path.join(raiz, "mensajes_submit.txt")).read())


# [Anotación · líneas 98–99] Punto de entrada del script: ejecuta main().
if __name__ == "__main__":
    main()
```

### comun_L22.py

Versión de comun_L22.py ubicada en la raíz, que importan los scripts 02, 03 y 04. Difiere de la copia de L22/codigo en que importa optuna dentro de un try/except y termina con un mensaje si se llama a la búsqueda sin optuna instalado.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Docstring del módulo. Nombra como scripts que lo importan a 02_etapa1_L22.py y
#   03_etapa2_L22.py, que no figuran en el repositorio; en esta entrega lo importan 01_entrenar_08_L22.py y los
#   scripts 02, 03 y 04 de la raíz. Enumera el contenido: parámetros fijos de LightGBM, configuración de la
#   búsqueda, entrenamiento por semilla y utilidades.
"""
comun_L22.py — funciones y parámetros compartidos por 02_etapa1_L22.py y 03_etapa2_L22.py (DMEyF, 1ra competencia).

No se ejecuta solo: lo importan los dos scripts de etapa. Debe estar en la misma carpeta que ellos (~/dmeyf).

Contenido:
  - parámetros fijos de LightGBM (los de z495 de Pasquini + feature_fraction_bynode de las recomendaciones),
  - configuración de la bayesiana (3 hiperparámetros, rangos de Pasquini, 10 trials aleatorios, semilla 878443),
  - bayesiana reproducible aunque se interrumpa (cada trial depende solo de su número y de los anteriores),
  - entrenamiento de N modelos con N semillas, reanudable (guarda cada predicción al terminar),
  - utilidades de carga, ganancia, respaldo al bucket.
"""
# [Anotación · líneas 13–32] Importa gc, json, os, shutil, subprocess, time, warnings, lightgbm, numpy,
#   pandas, pyarrow.parquet y roc_auc_score. optuna se importa dentro de un try/except: si no está instalado la
#   variable queda en None. Silencia un aviso de LightGBM sobre parámetros del Dataset de referencia.
import gc
import json
import os
import shutil
import subprocess
import time
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.metrics import roc_auc_score

try:                                    # solo lo usa la bayesiana (L22 no la corre)
    import optuna
except ImportError:
    optuna = None

warnings.filterwarnings("ignore", message="Overriding the parameters from Reference Dataset")

# [Anotación · líneas 34–48] Define VOLUMEN = "L22", el bucket gs://luisdsuarez_buckito2026 y las 5 semillas
#   878443, 455471, 178447, 235397 y 409027. semillas_n(n) devuelve esas 5 seguidas de valores generados sumando
#   7919 de forma sucesiva a partir de 500009 (507928, 515847, …) hasta completar n, y verifica que no haya
#   repetidos ni el valor 42.
VOLUMEN = "L22"
BUCKET = "gs://luisdsuarez_buckito2026"
SEMILLAS = [878443, 455471, 178447, 235397, 409027]       # asignadas; nunca 42


def semillas_n(n):
    """Las 5 asignadas + adicionales deterministas (misma función que L13). Nunca 42."""
    extra, x = [], 500009
    while len(SEMILLAS) + len(extra) < n:
        x += 7919
        if x != 42 and x not in SEMILLAS:
            extra.append(x)
    out = (SEMILLAS + extra)[:n]
    assert 42 not in out and len(set(out)) == len(out)
    return out


# [Anotación · líneas 51–71] PARAMS_FIJOS: parámetros de LightGBM que no se buscan: boosting gbdt, objective
#   binary, metric auc, max_depth −1, lambda_l1 y lambda_l2 en 0, max_bin 31, bagging_fraction 1.0 (también la
#   de positivos y la de negativos), is_unbalance False, scale_pos_weight 1.0, min_data_in_leaf 0,
#   feature_fraction 0.50, feature_fraction_bynode 0.20, learning_rate 0.005, deterministic True. PARAMS_DATASET
#   repite max_bin 31, feature_pre_filter False y min_data_in_leaf 0 para construir el Dataset.
# ---------------------------------------------------------------------------
# Hiperparámetros FIJOS (z495 + feature_fraction_bynode). num_iterations, num_leaves y
# min_sum_hessian_in_leaf los pone la bayesiana. Sin early stopping, sin undersampling, sin pesos.
# ---------------------------------------------------------------------------
PARAMS_FIJOS = dict(
    boosting="gbdt", objective="binary", metric="auc",
    first_metric_only=False, boost_from_average=True, force_row_wise=True, deterministic=True,
    verbosity=-1,
    max_depth=-1, min_gain_to_split=0.0, lambda_l1=0.0, lambda_l2=0.0,
    max_bin=31,
    bagging_fraction=1.0, pos_bagging_fraction=1.0, neg_bagging_fraction=1.0,
    is_unbalance=False, scale_pos_weight=1.0,
    drop_rate=0.1, max_drop=50, skip_drop=0.5,
    extra_trees=False,
    min_data_in_leaf=0,
    feature_fraction=0.50,
    feature_fraction_bynode=0.20,
    learning_rate=0.005,
    feature_pre_filter=False,
)
PARAMS_DATASET = dict(max_bin=31, feature_pre_filter=False, min_data_in_leaf=0, verbosity=-1)

# [Anotación · líneas 73–87] CFG: rangos de la búsqueda (num_iterations 64 a 4096, num_leaves 16 a 2048,
#   min_sum_hessian_in_leaf 1e-6 a 0.1), 10 trials, n_startup_trials 12, semilla de la búsqueda 878443, 10
#   semillas para las etapas de L20, proporción 0.01251 para la clase artificial, ganancia de 1.072.500 por
#   BAJA+2 y costo de −27.500 por envío. VARS_PRESTAMOS y SUFIJOS listan las 2 variables de préstamos personales
#   y los 8 sufijos de sus variantes.
# Configuración (dict mutable para que --prueba pueda achicarla)
CFG = dict(
    espacio=dict(num_iterations=(64, 4096),               # rangos del script de Pasquini (lineales)
                 num_leaves=(16, 2048),
                 min_sum_hessian_in_leaf=(1e-6, 0.1)),
    n_trials=10,                                           # como Pasquini: 10 evaluaciones
    n_startup_trials=12,                                   # 4 x 3 hiperparámetros > 10 -> los 10 son aleatorios
    semilla_bo=SEMILLAS[0],
    n_semillas=10,
    prop_baja_artificial=0.01251,                          # tasa de BAJA en 03-04 (1,251 %)
    ganancia_baja2=1_072_500,
    costo=-27_500,
)
VARS_PRESTAMOS = ["cprestamos_personales", "mprestamos_personales"]
SUFIJOS = ("", "_lag1", "_delta1", "_lag2", "_delta2", "_tend3", "_avg3", "_zero")   # variantes de cada variable de préstamos


# [Anotación · líneas 90–97] modo_prueba() reduce la configuración para probar el código (num_iterations 8 a
#   24, num_leaves 4 a 16, 3 trials, 3 semillas). log() imprime con la hora adelante y vacía el búfer.
def modo_prueba():
    """SOLO para probar el código con datos chicos."""
    CFG.update(espacio=dict(num_iterations=(8, 24), num_leaves=(4, 16), min_sum_hessian_in_leaf=(1e-6, 0.1)),
               n_trials=3, n_startup_trials=2, n_semillas=3)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# [Anotación · líneas 100–123] sync() copia la carpeta del experimento al bucket con gsutil rsync (tiempo
#   máximo 900 s); si gsutil da una excepción sólo registra un aviso. guardar_atomico() escribe en un archivo
#   .tmp y lo renombra al nombre final. preparar() crea exp/<volumen>/codigo y copia allí los scripts que se le
#   pasan y este módulo.
def sync(dir_exp, volumen, activo):
    """Respaldo al bucket; nunca frena el experimento."""
    if not activo:
        return
    try:
        subprocess.run(["gsutil", "-q", "-m", "rsync", "-r", dir_exp, f"{BUCKET}/exp/{volumen}"],
                       check=False, timeout=900, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log("  (aviso: falló el sync al bucket:", e, ")")


def guardar_atomico(escribir, ruta):
    tmp = ruta + ".tmp"
    escribir(tmp)
    os.replace(tmp, ruta)


def preparar(volumen, dir_base, scripts):
    """Crea exp/<volumen>/codigo y deja copia de los scripts y de este módulo."""
    dir_exp = os.path.join(dir_base, "exp", volumen)
    os.makedirs(os.path.join(dir_exp, "codigo"), exist_ok=True)
    for f in list(scripts) + [__file__]:
        shutil.copy(os.path.abspath(f), os.path.join(dir_exp, "codigo"))
    return dir_exp


# [Anotación · líneas 126–145] cargar() lee del parquet sólo las filas de los meses pedidos y arma una matriz
#   float64 con todas las columnas cuyo nombre no empieza con "clase_" (numero_de_cliente y foto_mes quedan
#   dentro de la matriz). Devuelve un diccionario con la matriz, los nombres de columnas, los ids, el mes, la
#   clase binaria y la clase ternaria.
def cargar(ruta_pq, meses):
    """Lee solo los meses pedidos. Matriz de features en float64 (numero_de_cliente no entra en float32).
    Ninguna columna 'clase_*' entra a la matriz de features."""
    tabla = pq.read_table(ruta_pq, filters=[("foto_mes", "in", [int(m) for m in meses])])
    cols = [c for c in tabla.column_names if not c.startswith("clase_")]
    assert not any(c.startswith("clase") for c in cols)
    n = tabla.num_rows
    X = np.empty((n, len(cols)), dtype="float64")
    for j, c in enumerate(cols):
        X[:, j] = tabla[c].to_numpy()
    D = dict(X=X, cols=cols,
             ids=tabla["numero_de_cliente"].to_numpy().astype("int64"),
             mes=tabla["foto_mes"].to_numpy(),
             yb=tabla["clase_binaria"].to_numpy().astype("float64"),
             tern=np.array(tabla["clase_ternaria"].to_pylist(), dtype=object))
    del tabla
    gc.collect()
    log(f"  datos cargados: X={X.shape}, {X.nbytes / 1e9:.1f} GB; features = foto_mes, numero_de_cliente y el resto; "
        f"ninguna clase")
    return D


# [Anotación · líneas 148–160] idx_sin_prestamos() devuelve los índices de las columnas que quedan al quitar
#   cprestamos_personales, mprestamos_personales y sus variantes _lag1, _delta1, _lag2, _delta2, _tend3, _avg3 y
#   _zero (16 columnas), y verifica que las 16 existan. curva_ganancia() ordena por probabilidad descendente y
#   acumula 1.072.500 por cada BAJA+2 y −27.500 por cada uno de los demás.
def idx_sin_prestamos(cols):
    """Índices de las columnas SIN las 2 variables de préstamos personales y todas sus variantes: lag1, delta1, lag2, delta2, tend3, avg3 y _zero (16 columnas)."""
    excl = [b + s for b in VARS_PRESTAMOS for s in SUFIJOS]
    faltan = [x for x in excl if x not in cols]
    assert not faltan, f"columnas de préstamos que no están en el dataset: {faltan}"
    idx = np.array([j for j, c in enumerate(cols) if c not in set(excl)])
    return idx, [cols[j] for j in idx], excl


def curva_ganancia(prob, ternaria):
    """Ganancia acumulada al enviar los N de mayor probabilidad (N = 1..n)."""
    o = np.argsort(-prob, kind="stable")
    return np.cumsum(np.where(ternaria[o] == "BAJA+2", CFG["ganancia_baja2"], CFG["costo"]))


# [Anotación · líneas 163–166] entrenar() combina PARAMS_FIJOS con la semilla, num_leaves y
#   min_sum_hessian_in_leaf recibidos y entrena LightGBM con num_iterations rondas, sin detención temprana.
def entrenar(params_bo, semilla, ds):
    p = dict(PARAMS_FIJOS, seed=semilla, num_leaves=int(params_bo["num_leaves"]),
             min_sum_hessian_in_leaf=float(params_bo["min_sum_hessian_in_leaf"]))
    return lgb.train(p, ds, num_boost_round=int(params_bo["num_iterations"]))     # todos los árboles


# [Anotación · líneas 169–185] correr_bayesiana(), preparación: si optuna no está instalado termina con un
#   mensaje. Define las distribuciones de los 3 hiperparámetros (enteras para num_iterations y num_leaves,
#   continua para min_sum_hessian_in_leaf) y lee del archivo .jsonl los trials ya completos, si existe.
# ---------------------------------------------------------------------------
# Bayesiana reproducible aunque se interrumpa.
# El registro de trials completos vive en un .jsonl (una línea por trial). Para proponer el trial k se arma
# un estudio nuevo en memoria con los k trials ya completos, en orden, y un muestreador con semilla = semilla_bo + k.
# La propuesta depende solo de k y de los resultados anteriores, no de cuántas veces ni dónde se cortó.
# ---------------------------------------------------------------------------
def correr_bayesiana(dtr, X_va, y_va, ruta_jsonl, despues_de_trial=None, etiqueta=""):
    if optuna is None:
        raise SystemExit("Falta instalar optuna (pip install optuna) para correr la bayesiana")
    esp = CFG["espacio"]
    dists = dict(num_iterations=optuna.distributions.IntDistribution(*esp["num_iterations"]),
                 num_leaves=optuna.distributions.IntDistribution(*esp["num_leaves"]),
                 min_sum_hessian_in_leaf=optuna.distributions.FloatDistribution(*esp["min_sum_hessian_in_leaf"]))
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    hist = [json.loads(l) for l in open(ruta_jsonl)] if os.path.exists(ruta_jsonl) else []
    if hist:
        log(f"  {etiqueta} retomando: {len(hist)} trials ya completos")
# [Anotación · líneas 186–209] Bucle hasta completar 10 trials. Para el trial k crea un estudio de Optuna que
#   maximiza, con TPESampler de semilla 878443 + k y n_startup_trials 12, le carga los trials anteriores, pide
#   una propuesta, entrena con la semilla 878443 y calcula el AUC sobre la matriz de validación. Agrega el
#   resultado como una línea del .jsonl y llama a la función de respaldo.
    while len(hist) < CFG["n_trials"]:
        k = len(hist)
        semilla_trial = CFG["semilla_bo"] + k
        estudio = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(
            seed=semilla_trial, n_startup_trials=CFG["n_startup_trials"]))
        for h in hist:
            estudio.add_trial(optuna.trial.create_trial(params=h["params"], distributions=dists, value=h["auc"]))
        trial = estudio.ask()
        t0 = time.time()
        hp = dict(num_iterations=trial.suggest_int("num_iterations", *esp["num_iterations"]),
                  num_leaves=trial.suggest_int("num_leaves", *esp["num_leaves"]),
                  min_sum_hessian_in_leaf=trial.suggest_float("min_sum_hessian_in_leaf", *esp["min_sum_hessian_in_leaf"]))
        m = entrenar(hp, CFG["semilla_bo"], dtr)                  # la bayesiana usa la primera semilla
        auc = float(roc_auc_score(y_va, m.predict(X_va)))
        del m
        gc.collect()
        seg = round(time.time() - t0)
        log(f"  {etiqueta} trial {k:>2}: it={hp['num_iterations']:>4} hojas={hp['num_leaves']:>4} "
            f"hess={hp['min_sum_hessian_in_leaf']:.6f} -> AUC {auc:.5f}  ({seg}s, semilla del muestreador {semilla_trial})")
        hist.append(dict(trial=k, params=hp, auc=auc, segundos=seg, semilla_muestreador=semilla_trial))
        with open(ruta_jsonl, "a") as fh:
            fh.write(json.dumps(hist[-1]) + "\n")
        if despues_de_trial:
            despues_de_trial()
# [Anotación · líneas 210–215] Elige el trial de mayor AUC (ante empate, el primero) y devuelve el historial,
#   los tres hiperparámetros de ese trial y su registro.
    mejor = max(hist, key=lambda h: h["auc"])                      # ante empate, el primero
    mejores = dict(num_iterations=int(mejor["params"]["num_iterations"]),
                   num_leaves=int(mejor["params"]["num_leaves"]),
                   min_sum_hessian_in_leaf=float(mejor["params"]["min_sum_hessian_in_leaf"]))
    log(f"  {etiqueta} MEJORES hiperparámetros (trial {mejor['trial']}, AUC {mejor['auc']:.5f}): {mejores}")
    return hist, mejores, mejor


# [Anotación · líneas 218–239] entrenar_semillas(): para cada semilla que no tenga todas sus predicciones
#   guardadas entrena un modelo, predice cada matriz recibida, guarda <nombre>_<semilla>.npy y registra el AUC
#   cuando hay clase para esa matriz. Devuelve las predicciones leídas de disco, por matriz y por semilla.
def entrenar_semillas(dtr, mejores, semillas, matrices, y_eval, dir_p, despues=None):
    """Entrena un modelo por semilla sobre dtr y predice cada matriz de `matrices` (dict nombre -> X).
    Guarda <nombre>_<semilla>.npy al terminar cada semilla (reanudable). Devuelve {nombre: {semilla: prob}}."""
    os.makedirs(dir_p, exist_ok=True)
    ruta = lambda nom, sd: os.path.join(dir_p, f"{nom}_{sd}.npy")
    pend = [sd for sd in semillas if not all(os.path.exists(ruta(n, sd)) for n in matrices)]
    log(f"  {len(semillas)} semillas {semillas}; pendientes {len(pend)}")
    for sd in pend:
        t = time.time()
        m = entrenar(mejores, sd, dtr)
        msg = []
        for nom, X in matrices.items():
            pr = m.predict(X).astype("float64")
            guardar_atomico(lambda r: np.save(open(r, "wb"), pr), ruta(nom, sd))
            if nom in y_eval:
                msg.append(f"AUC {nom} {roc_auc_score(y_eval[nom], pr):.5f}")
        log(f"  semilla {sd}: {', '.join(msg)}  ({time.time() - t:.0f}s)")
        del m
        gc.collect()
        if despues:
            despues()
    return {nom: {sd: np.load(ruta(nom, sd)) for sd in semillas} for nom in matrices}


# [Anotación · líneas 242–248] tabla_predicciones() arma un DataFrame con numero_de_cliente, foto_mes, las dos
#   clases, una columna prob_<semilla> por modelo y prob_ens, el promedio de esas columnas.
def tabla_predicciones(ids, mes, tern, yb, P):
    """DataFrame con identificación, clase real, una columna prob_<semilla> por semilla y prob_ens (promedio simple)."""
    out = pd.DataFrame(dict(numero_de_cliente=ids, foto_mes=mes, clase_ternaria=tern, clase_binaria=yb.astype("float32")))
    for sd, pr in P.items():
        out[f"prob_{sd}"] = pr
    out["prob_ens"] = out[[f"prob_{sd}" for sd in P]].mean(axis=1)
    return out


# [Anotación · líneas 251–269] resumen_mes() calcula el AUC de cada semilla y del promedio y lo guarda en
#   <prefijo>_auc.csv. Calcula la ganancia acumulada para envíos de 1.000 a 30.000 de a 100, por semilla, su
#   media y la del promedio de probabilidades, la guarda en <prefijo>_ganancia.csv y registra el máximo de las
#   dos últimas.
def resumen_mes(P, y_real, tern, prefijo, etiqueta):
    """AUC por semilla y del ensamble, y curva de ganancia (por semilla, media y ensamble) en un mes con clase real."""
    semillas = list(P)
    ens = np.mean([P[s] for s in semillas], axis=0)
    aucs = {s: float(roc_auc_score(y_real, P[s])) for s in semillas}
    auc_ens = float(roc_auc_score(y_real, ens))
    pd.DataFrame(dict(semilla=semillas + ["ensamble"], auc=list(aucs.values()) + [auc_ens])
                 ).to_csv(f"{prefijo}_auc.csv", index=False)
    log(f"  {etiqueta}: AUC media de semillas {np.mean(list(aucs.values())):.5f} "
        f"(sd {np.std(list(aucs.values()), ddof=1):.5f}), ensamble {auc_ens:.5f}")
    envios = np.arange(1000, min(30000, len(tern)) + 1, 100)
    tab = pd.DataFrame(dict(envios=envios, **{f"g_{s}": curva_ganancia(P[s], tern)[envios - 1] for s in semillas}))
    tab["g_media"] = tab[[f"g_{s}" for s in semillas]].mean(axis=1)
    tab["g_ens"] = curva_ganancia(ens, tern)[envios - 1]
    tab.to_csv(f"{prefijo}_ganancia.csv", index=False)
    for nombre in ("g_media", "g_ens"):
        k = int(tab[nombre].idxmax())
        log(f"  {etiqueta} {nombre}: máximo {tab[nombre][k] / 1e6:,.1f} M con {int(tab['envios'][k]):,} envíos "
            f"(mirar la curva suavizada, no solo el pico)")


# [Anotación · líneas 272–301] ensamblar_08(): lee ids_08.npy de la carpeta del volumen y de cada carpeta
#   adicional y exige que sean iguales. Recorre la lista ordenada de semillas, toma los
#   pred_08/prob_<semilla>.npy que existen (una semilla no puede estar en dos carpetas), se queda con los
#   primeros n si se pide, y calcula prob_ens como el promedio por fila de las probabilidades de esos modelos.
# ---------------------------------------------------------------------------
# Ensamble de las predicciones sobre 08 disponibles hasta el momento (se puede llamar en cualquier momento).
# ---------------------------------------------------------------------------
def ensamblar_08(dir_exp, volumen, semillas_orden, n=None, top=11000, guardar=True, otros_dirs=()):
    """Promedia las probabilidades guardadas en pred_08/prob_<semilla>.npy (en el orden de semillas_orden).
    otros_dirs: carpetas exp/<otro volumen> con más predicciones de las mismas características (mismo 08, mismo orden de
    clientes); no puede haber semillas repetidas entre carpetas. n: usar solo los primeros n modelos (None = todos)."""
    dirs = [dir_exp] + list(otros_dirs)
    ids = np.load(os.path.join(dir_exp, "ids_08.npy"))
    ruta_de = {}
    for d in dirs:
        ids_d = np.load(os.path.join(d, "ids_08.npy"))
        assert np.array_equal(ids_d, ids), f"{d}: ids_08.npy distinto: no son los mismos clientes de 08 en el mismo orden"
        dir_p = os.path.join(d, "pred_08")
        for sd in semillas_orden:
            f = os.path.join(dir_p, f"prob_{sd}.npy")
            if os.path.exists(f):
                assert sd not in ruta_de, f"la semilla {sd} está en dos carpetas ({ruta_de[sd]} y {f}): rangos de semillas superpuestos"
                ruta_de[sd] = f
    usadas = [sd for sd in semillas_orden if sd in ruta_de]
    if n:
        usadas = usadas[:n]
    if not usadas:
        raise SystemExit(f"No hay predicciones en {[os.path.join(d, 'pred_08') for d in dirs]}")
    P = np.column_stack([np.load(ruta_de[sd]) for sd in usadas])
    assert P.shape[0] == len(ids), "las predicciones no tienen la misma cantidad de clientes que ids_08.npy"
    ens = P.mean(axis=1)
    out = pd.DataFrame(dict(numero_de_cliente=ids, prob_ens=ens))
    log(f"  ensamble de {len(usadas)} modelos sobre {len(ids):,} clientes de 08"
        + (f" (carpetas: {', '.join(os.path.basename(d) for d in dirs)})" if len(dirs) > 1 else ""))
# [Anotación · líneas 302–309] Con 4 modelos o más, para k en 2, 5, 10, 20, 40, 80, 160 y 320 (los menores a
#   la cantidad de modelos) registra qué proporción de los primeros `top` clientes (11.000 por defecto) del
#   promedio de los primeros k modelos coincide con los del promedio de todos.
    # estabilidad: cuánto del top-N del ensamble completo ya está en el top-N del ensamble de los primeros k modelos
    if len(usadas) >= 4:
        top = min(top, len(ids))
        topN = set(np.argsort(-ens, kind="stable")[:top])
        ks = sorted({k for k in (2, 5, 10, 20, 40, 80, 160, 320) if k < len(usadas)})
        for k in ks:
            tk = set(np.argsort(-P[:, :k].mean(axis=1), kind="stable")[:top])
            log(f"  top {top:,}: con {k:>3} modelos coincide el {len(tk & topN) / top:.1%} con el ensamble de {len(usadas)}")
# [Anotación · líneas 310–315] Si guardar es verdadero escribe <etiqueta>_pred_08_ens_<n>modelos.parquet con
#   numero_de_cliente y prob_ens; la etiqueta une con "+" los nombres de las carpetas usadas. Devuelve la tabla
#   y la lista de semillas usadas.
    if guardar:
        etiqueta = "+".join(os.path.basename(d) for d in dirs) if len(dirs) > 1 else volumen
        ruta_out = os.path.join(dir_exp, f"{etiqueta}_pred_08_ens_{len(usadas)}modelos.parquet")
        guardar_atomico(lambda r: out.to_parquet(r, index=False), ruta_out)
        log(f"  guardado: {ruta_out}")
    return out, usadas
```

### 03_submit_L22.py

Arma un archivo de envío: promedia las probabilidades de los modelos disponibles, ordena los clientes de 202108 por ese promedio y escribe en un .csv sin encabezado los --corte primeros numero_de_cliente.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–14] Docstring: describe el archivo que arma (un numero_de_cliente por línea, sin
#   encabezado, entre 8000 y 15000 registros, ids enteros), el comando de uso con --corte 10500 y la ubicación
#   de la salida.
"""
03_submit_L22.py — arma UN archivo de submit con el ensamble de las predicciones sobre 08 disponibles.

Promedia las probabilidades de todos los modelos disponibles (de este volumen y de los volúmenes de --otros), ordena
los clientes por ese promedio y toma los --corte con mayor probabilidad. Escribe un .csv con el formato del bot:
    - extensión .csv, SIN encabezado, un numero_de_cliente por línea, entre 8000 y 15000 registros
    - ids como enteros (nunca notación científica: 48000000, no 4.8e+07)

Uso (desde ~/dmeyf):
    python 03_submit_L22.py --corte 10500 --volumen L22 --otros L22b

Salida: exp/<volumen>/submit/<nombre>.csv  (el nombre incluye cantidad de modelos, corte y fecha: es distinto en cada corrida)
y la línea para el cuerpo del mensaje a @competencia-uno:   submit <nombre>
"""
# [Anotación · líneas 15–24] Importa argparse, os, re, time, numpy, pandas y el módulo comun_L22.
import argparse
import os
import re
import time

import numpy as np
import pandas as pd

import comun_L22 as cm
from comun_L22 import log


# [Anotación · líneas 27–37] Argumentos --volumen, --otros, --dir_base, --corte (obligatorio), --nombre y
#   --prueba. Salvo con --prueba exige que el corte esté entre 8000 y 15000.
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volumen", default=cm.VOLUMEN)
    ap.add_argument("--otros", nargs="*", default=[], help="otros volúmenes (carpetas exp/<volumen>) con más predicciones")
    ap.add_argument("--dir_base", default=os.path.expanduser("~/dmeyf"))
    ap.add_argument("--corte", type=int, required=True, help="cantidad de clientes a enviar (los de mayor probabilidad)")
    ap.add_argument("--nombre", default=None, help="nombre del submit (sin espacios); por defecto se arma solo y es único")
    ap.add_argument("--prueba", action="store_true", help="SOLO para probar el código: no exige el rango 8000-15000")
    a = ap.parse_args()
    if not a.prueba:
        assert 8000 <= a.corte <= 15000, "el bot acepta archivos con entre 8000 y 15000 registros"

# [Anotación · líneas 39–41] Arma las rutas de los volúmenes y obtiene el promedio de probabilidades con
#   ensamblar_08, sin guardar el parquet.
    dir_exp = os.path.join(a.dir_base, "exp", a.volumen)
    otros = [os.path.join(a.dir_base, "exp", v) for v in a.otros]
    ens, usadas = cm.ensamblar_08(dir_exp, a.volumen, cm.semillas_n(1000), otros_dirs=otros, guardar=False)

# [Anotación · líneas 43–47] Ordena por prob_ens de mayor a menor (orden estable), toma los primeros --corte
#   clientes, verifica que no haya ids repetidos y registra la prob_ens del último cliente incluido.
    orden = np.argsort(-ens["prob_ens"].to_numpy(), kind="stable")[:a.corte]
    ids = ens["numero_de_cliente"].to_numpy().astype("int64")[orden]
    assert len(ids) == a.corte and len(np.unique(ids)) == a.corte, "ids repetidos o menos clientes que el corte"
    corte_prob = ens["prob_ens"].to_numpy()[orden[-1]]
    log(f"  corte {a.corte:,}: se envían los clientes con prob_ens >= {corte_prob:.5f}")

# [Anotación · líneas 49–55] Arma el nombre por defecto <volumen>_ens<n>m_c<corte>_<fecha y hora>, verifica
#   que sólo tenga letras, números, guion, guion bajo o punto, crea exp/<volumen>/submit, exige que el archivo
#   no exista y escribe los ids como enteros, sin encabezado.
    nombre = a.nombre or f"{a.volumen}_ens{len(usadas)}m_c{a.corte}_{time.strftime('%Y%m%d%H%M')}"
    assert re.fullmatch(r"[A-Za-z0-9_.-]+", nombre), "el nombre no puede tener espacios ni caracteres raros"
    carpeta = os.path.join(dir_exp, "submit")
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f"{nombre}.csv")
    assert not os.path.exists(ruta), f"ya existe {ruta}: cada submit debe tener un nombre distinto"
    pd.Series(ids, dtype="int64").to_csv(ruta, index=False, header=False)    # enteros, sin encabezado

# [Anotación · líneas 57–67] Relee el archivo como texto y verifica que termine en salto de línea, que tenga
#   --corte líneas y que cada línea tenga sólo dígitos. Imprime las primeras 7 líneas, la ruta y el texto
#   "submit <nombre>" para el mensaje a @competencia-uno.
    # verificación del archivo escrito, leyéndolo como texto
    with open(ruta) as fh:
        lineas = fh.read().split("\n")
    assert lineas[-1] == "", "el archivo debe terminar en salto de línea"
    lineas = lineas[:-1]
    assert len(lineas) == a.corte, (len(lineas), a.corte)
    assert all(re.fullmatch(r"[0-9]+", l) for l in lineas), "hay líneas que no son enteros puros (encabezado, decimales o notación científica)"
    log(f"  archivo verificado: {len(lineas):,} líneas, sin encabezado, todos enteros")
    log(f"  primeras 7 líneas: {lineas[:7]}")
    log(f"  guardado: {ruta}")
    print(f"\nCuerpo del mensaje a @competencia-uno:\n    submit    {nombre}\nArchivo adjunto:\n    {ruta}")


# [Anotación · líneas 70–71] Punto de entrada del script: ejecuta main().
if __name__ == "__main__":
    main()
```

### L20/codigo/preproc_comun.py

Módulo con las funciones de cálculo que usa el preprocesamiento: ranking con cero fijo por mes, posición del mes anterior por unión, tendencia y promedio de 3 meses y flag de cero; define las 10 columnas sin historia y las 4 que no se rankean.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–15] Docstring: describe las cuatro funciones del módulo y que cada experimento guarda
#   una copia propia en exp/Lxx/codigo/.
"""
preproc_comun.py — cálculo compartido de variables para el preprocesamiento de cada experimento (DMEyF).

Lo importan los scripts 01_preprocesamiento_Lxx.py. Cada experimento guarda una copia de este módulo en
exp/Lxx/codigo/, así todos calculan EXACTAMENTE lo mismo y cada uno sigue siendo reproducible por sí solo.

Contenido (recomendaciones del profesor, secciones 1.3 y 1.4):
  - rank_cero_fijo      ranking por mes con cero fijo y signo (clase 9).
  - posicion_de_lag     lags por UNIÓN con (cliente, mes - k): los meses faltantes quedan NA (no se usa shift por fila).
  - tendencia_promedio  pendiente de la recta de cuadrados mínimos y promedio sobre una ventana de 3 meses
                        (mes actual y los 2 anteriores). Réplica de fhistC del ejemplo en R con ventana=3,
                        pero por MES CALENDARIO y no por fila: cada mes disponible aporta un punto con su
                        posición real (1, 2, 3); se necesitan al menos 2 puntos, si no, NA.
  - flag_zero           variable _zero: 1 si el original vale cero, NA si era NA, 0 en el resto.
"""
# [Anotación · líneas 16–26] Importa numpy y pandas. SIN_HISTORIA lista 10 columnas (cliente_edad,
#   cliente_antiguedad y 8 fechas de Master y Visa) que se rankean y no reciben lags, deltas, tendencia ni
#   promedio. NO_RANKEAR lista numero_de_cliente, foto_mes, clase_ternaria y clase_binaria.
import numpy as np
import pandas as pd

# Columnas SIN historia: su valor cambia de forma determinística con el calendario
# (su delta sería constante) -> solo se rankean, no llevan lags, deltas, tendencia ni promedio.
SIN_HISTORIA = [
    "cliente_edad", "cliente_antiguedad",
    "Master_fechaalta", "Visa_fechaalta", "Master_Fvencimiento", "Visa_Fvencimiento",
    "Master_fultimo_cierre", "Visa_fultimo_cierre", "Master_Finiciomora", "Visa_Finiciomora",
]
NO_RANKEAR = ["numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria"]


# [Anotación · líneas 29–42] rank_cero_fijo(): dentro de cada mes, los ceros quedan en 0, los positivos
#   reciben su rango percentil entre los positivos (valores en (0, 1], empates con rango promedio), los
#   negativos reciben el rango percentil de su valor absoluto entre los negativos con signo menos (valores en
#   [−1, 0)) y los NA quedan en NA. Devuelve float32.
def rank_cero_fijo(v, idx_mes):
    """Ranking con cero fijo y signo, dentro de cada mes. v: float64. Devuelve float32."""
    out = np.full(v.shape, np.nan, dtype=np.float32)
    for idx in idx_mes:
        x = v[idx]
        r = np.full(len(x), np.nan)
        r[x == 0] = 0.0                                   # el cero se queda en cero
        pos, neg = x > 0, x < 0                           # (los NaN no entran en ninguna máscara)
        if pos.any():
            r[pos] = pd.Series(x[pos]).rank(method="average", pct=True).to_numpy()
        if neg.any():
            r[neg] = -pd.Series(-x[neg]).rank(method="average", pct=True).to_numpy()
        out[idx] = r
    return out


# [Anotación · líneas 45–62] posicion_de_lag(): ordena las claves cliente-período y busca con searchsorted,
#   para cada fila, la fila con clave − k; devuelve su posición o −1 si no existe. aplicar_lag() toma el valor
#   de esa posición y deja NA donde la posición es −1.
def posicion_de_lag(key, k):
    """Para cada fila, la posición de la fila del MISMO cliente en el mes (mes - k); -1 si no existe."""
    orden = np.argsort(key, kind="stable")
    ks = key[orden]
    objetivo = key - k
    i = np.searchsorted(ks, objetivo)
    i = np.clip(i, 0, len(ks) - 1)
    existe = ks[i] == objetivo
    pos = orden[i]
    pos[~existe] = -1
    return pos


def aplicar_lag(x, pos):
    out = np.full(x.shape, np.nan)
    ok = pos >= 0
    out[ok] = x[pos[ok]]
    return out


# [Anotación · líneas 65–83] tendencia_promedio(): con el valor actual y los de 1 y 2 meses atrás, ubicados en
#   x = 3, 2 y 1, acumula las sumas de los puntos no nulos y calcula la pendiente de la recta de cuadrados
#   mínimos y el promedio; con menos de 2 puntos devuelve NA en ambos.
def tendencia_promedio(x, l1, l2):
    """Ventana de 3 meses (x = mes actual, l1 = mes-1, l2 = mes-2; NaN si falta).
    Devuelve (pendiente de la recta de cuadrados mínimos, promedio), ambos float64.
    Los puntos tienen x = 1 (l2), 2 (l1) y 3 (actual); los NaN no aportan. Con menos de 2 puntos: NaN, NaN."""
    ys = (l2, l1, x)
    xs = (1.0, 2.0, 3.0)
    n = sx = sy = sxy = sxx = 0.0
    for xv, y in zip(xs, ys):
        m = ~np.isnan(y)
        n = n + m
        sx = sx + xv * m
        sy = sy + np.where(m, y, 0.0)
        sxy = sxy + xv * np.where(m, y, 0.0)
        sxx = sxx + (xv * xv) * m
    ok = n >= 2
    with np.errstate(divide="ignore", invalid="ignore"):
        pend = (n * sxy - sx * sy) / (n * sxx - sx * sx)
        prom = sy / n
    return np.where(ok, pend, np.nan), np.where(ok, prom, np.nan)


# [Anotación · líneas 86–88] flag_zero(): devuelve 1 si el valor es cero, 0 si es distinto de cero y NA si es
#   NA, en float32.
def flag_zero(x):
    """1.0 si x == 0, 0.0 si x != 0, NaN si x es NaN (float32). Estas variables NO se rankean."""
    return np.where(np.isnan(x), np.nan, (x == 0).astype("float32")).astype("float32")
```

### L20/codigo/comun_L20.py

Módulo compartido por las dos etapas de L20: semillas, parámetros fijos de LightGBM, configuración y bucle de la búsqueda con Optuna, entrenamiento por semilla, carga del parquet, curva de ganancia y respaldo al bucket.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Docstring del módulo: lo importan 02_etapa1_L20.py y 03_etapa2_L20.py y reúne los
#   parámetros fijos de LightGBM, la configuración de la búsqueda de hiperparámetros, el entrenamiento por
#   semilla y las utilidades de carga, ganancia y respaldo al bucket.
"""
comun_L20.py — funciones y parámetros compartidos por 02_etapa1_L20.py y 03_etapa2_L20.py (DMEyF, 1ra competencia).

No se ejecuta solo: lo importan los dos scripts de etapa. Debe estar en la misma carpeta que ellos (~/dmeyf).

Contenido:
  - parámetros fijos de LightGBM (los de z495 de Pasquini + feature_fraction_bynode de las recomendaciones),
  - configuración de la bayesiana (3 hiperparámetros, rangos de Pasquini, 10 trials aleatorios, semilla 878443),
  - bayesiana reproducible aunque se interrumpa (cada trial depende solo de su número y de los anteriores),
  - entrenamiento de N modelos con N semillas, reanudable (guarda cada predicción al terminar),
  - utilidades de carga, ganancia, respaldo al bucket.
"""
# [Anotación · líneas 13–28] Importa gc, json, os, shutil, subprocess, time, warnings, lightgbm, numpy,
#   optuna, pandas, pyarrow.parquet y roc_auc_score. Silencia un aviso de LightGBM sobre parámetros del Dataset
#   de referencia.
import gc
import json
import os
import shutil
import subprocess
import time
import warnings

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import pyarrow.parquet as pq
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore", message="Overriding the parameters from Reference Dataset")

# [Anotación · líneas 30–44] Define VOLUMEN = "L20", el bucket gs://luisdsuarez_buckito2026 y las 5 semillas
#   878443, 455471, 178447, 235397 y 409027. semillas_n(n) devuelve esas 5 seguidas de valores generados sumando
#   7919 de forma sucesiva a partir de 500009 (507928, 515847, …) hasta completar n, y verifica que no haya
#   repetidos ni el valor 42.
VOLUMEN = "L20"
BUCKET = "gs://luisdsuarez_buckito2026"
SEMILLAS = [878443, 455471, 178447, 235397, 409027]       # asignadas; nunca 42


def semillas_n(n):
    """Las 5 asignadas + adicionales deterministas (misma función que L13). Nunca 42."""
    extra, x = [], 500009
    while len(SEMILLAS) + len(extra) < n:
        x += 7919
        if x != 42 and x not in SEMILLAS:
            extra.append(x)
    out = (SEMILLAS + extra)[:n]
    assert 42 not in out and len(set(out)) == len(out)
    return out


# [Anotación · líneas 47–67] PARAMS_FIJOS: parámetros de LightGBM que no se buscan: boosting gbdt, objective
#   binary, metric auc, max_depth −1, lambda_l1 y lambda_l2 en 0, max_bin 31, bagging_fraction 1.0 (también la
#   de positivos y la de negativos), is_unbalance False, scale_pos_weight 1.0, min_data_in_leaf 0,
#   feature_fraction 0.50, feature_fraction_bynode 0.20, learning_rate 0.005, deterministic True. PARAMS_DATASET
#   repite max_bin 31, feature_pre_filter False y min_data_in_leaf 0 para construir el Dataset.
# ---------------------------------------------------------------------------
# Hiperparámetros FIJOS (z495 + feature_fraction_bynode). num_iterations, num_leaves y
# min_sum_hessian_in_leaf los pone la bayesiana. Sin early stopping, sin undersampling, sin pesos.
# ---------------------------------------------------------------------------
PARAMS_FIJOS = dict(
    boosting="gbdt", objective="binary", metric="auc",
    first_metric_only=False, boost_from_average=True, force_row_wise=True, deterministic=True,
    verbosity=-1,
    max_depth=-1, min_gain_to_split=0.0, lambda_l1=0.0, lambda_l2=0.0,
    max_bin=31,
    bagging_fraction=1.0, pos_bagging_fraction=1.0, neg_bagging_fraction=1.0,
    is_unbalance=False, scale_pos_weight=1.0,
    drop_rate=0.1, max_drop=50, skip_drop=0.5,
    extra_trees=False,
    min_data_in_leaf=0,
    feature_fraction=0.50,
    feature_fraction_bynode=0.20,
    learning_rate=0.005,
    feature_pre_filter=False,
)
PARAMS_DATASET = dict(max_bin=31, feature_pre_filter=False, min_data_in_leaf=0, verbosity=-1)

# [Anotación · líneas 69–83] CFG: rangos de la búsqueda (num_iterations 64 a 4096, num_leaves 16 a 2048,
#   min_sum_hessian_in_leaf 1e-6 a 0.1), 10 trials, n_startup_trials 12, semilla de la búsqueda 878443, 10
#   semillas para las etapas de L20, proporción 0.01251 para la clase artificial, ganancia de 1.072.500 por
#   BAJA+2 y costo de −27.500 por envío. VARS_PRESTAMOS y SUFIJOS listan las 2 variables de préstamos personales
#   y los 8 sufijos de sus variantes.
# Configuración (dict mutable para que --prueba pueda achicarla)
CFG = dict(
    espacio=dict(num_iterations=(64, 4096),               # rangos del script de Pasquini (lineales)
                 num_leaves=(16, 2048),
                 min_sum_hessian_in_leaf=(1e-6, 0.1)),
    n_trials=10,                                           # como Pasquini: 10 evaluaciones
    n_startup_trials=12,                                   # 4 x 3 hiperparámetros > 10 -> los 10 son aleatorios
    semilla_bo=SEMILLAS[0],
    n_semillas=10,
    prop_baja_artificial=0.01251,                          # tasa de BAJA en 03-04 (1,251 %)
    ganancia_baja2=1_072_500,
    costo=-27_500,
)
VARS_PRESTAMOS = ["cprestamos_personales", "mprestamos_personales"]
SUFIJOS = ("", "_lag1", "_delta1", "_lag2", "_delta2", "_tend3", "_avg3", "_zero")   # variantes de cada variable de préstamos


# [Anotación · líneas 86–93] modo_prueba() reduce la configuración para probar el código (num_iterations 8 a
#   24, num_leaves 4 a 16, 3 trials, 3 semillas). log() imprime con la hora adelante y vacía el búfer.
def modo_prueba():
    """SOLO para probar el código con datos chicos."""
    CFG.update(espacio=dict(num_iterations=(8, 24), num_leaves=(4, 16), min_sum_hessian_in_leaf=(1e-6, 0.1)),
               n_trials=3, n_startup_trials=2, n_semillas=3)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# [Anotación · líneas 96–119] sync() copia la carpeta del experimento al bucket con gsutil rsync (tiempo
#   máximo 900 s); si gsutil da una excepción sólo registra un aviso. guardar_atomico() escribe en un archivo
#   .tmp y lo renombra al nombre final. preparar() crea exp/<volumen>/codigo y copia allí los scripts que se le
#   pasan y este módulo.
def sync(dir_exp, volumen, activo):
    """Respaldo al bucket; nunca frena el experimento."""
    if not activo:
        return
    try:
        subprocess.run(["gsutil", "-q", "-m", "rsync", "-r", dir_exp, f"{BUCKET}/exp/{volumen}"],
                       check=False, timeout=900, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log("  (aviso: falló el sync al bucket:", e, ")")


def guardar_atomico(escribir, ruta):
    tmp = ruta + ".tmp"
    escribir(tmp)
    os.replace(tmp, ruta)


def preparar(volumen, dir_base, scripts):
    """Crea exp/<volumen>/codigo y deja copia de los scripts y de este módulo."""
    dir_exp = os.path.join(dir_base, "exp", volumen)
    os.makedirs(os.path.join(dir_exp, "codigo"), exist_ok=True)
    for f in list(scripts) + [__file__]:
        shutil.copy(os.path.abspath(f), os.path.join(dir_exp, "codigo"))
    return dir_exp


# [Anotación · líneas 122–141] cargar() lee del parquet sólo las filas de los meses pedidos y arma una matriz
#   float64 con todas las columnas cuyo nombre no empieza con "clase_" (numero_de_cliente y foto_mes quedan
#   dentro de la matriz). Devuelve un diccionario con la matriz, los nombres de columnas, los ids, el mes, la
#   clase binaria y la clase ternaria.
def cargar(ruta_pq, meses):
    """Lee solo los meses pedidos. Matriz de features en float64 (numero_de_cliente no entra en float32).
    Ninguna columna 'clase_*' entra a la matriz de features."""
    tabla = pq.read_table(ruta_pq, filters=[("foto_mes", "in", [int(m) for m in meses])])
    cols = [c for c in tabla.column_names if not c.startswith("clase_")]
    assert not any(c.startswith("clase") for c in cols)
    n = tabla.num_rows
    X = np.empty((n, len(cols)), dtype="float64")
    for j, c in enumerate(cols):
        X[:, j] = tabla[c].to_numpy()
    D = dict(X=X, cols=cols,
             ids=tabla["numero_de_cliente"].to_numpy().astype("int64"),
             mes=tabla["foto_mes"].to_numpy(),
             yb=tabla["clase_binaria"].to_numpy().astype("float64"),
             tern=np.array(tabla["clase_ternaria"].to_pylist(), dtype=object))
    del tabla
    gc.collect()
    log(f"  datos cargados: X={X.shape}, {X.nbytes / 1e9:.1f} GB; features = foto_mes, numero_de_cliente y el resto; "
        f"ninguna clase")
    return D


# [Anotación · líneas 144–156] idx_sin_prestamos() devuelve los índices de las columnas que quedan al quitar
#   cprestamos_personales, mprestamos_personales y sus variantes _lag1, _delta1, _lag2, _delta2, _tend3, _avg3 y
#   _zero (16 columnas), y verifica que las 16 existan. curva_ganancia() ordena por probabilidad descendente y
#   acumula 1.072.500 por cada BAJA+2 y −27.500 por cada uno de los demás.
def idx_sin_prestamos(cols):
    """Índices de las columnas SIN las 2 variables de préstamos personales y todas sus variantes: lag1, delta1, lag2, delta2, tend3, avg3 y _zero (16 columnas)."""
    excl = [b + s for b in VARS_PRESTAMOS for s in SUFIJOS]
    faltan = [x for x in excl if x not in cols]
    assert not faltan, f"columnas de préstamos que no están en el dataset: {faltan}"
    idx = np.array([j for j, c in enumerate(cols) if c not in set(excl)])
    return idx, [cols[j] for j in idx], excl


def curva_ganancia(prob, ternaria):
    """Ganancia acumulada al enviar los N de mayor probabilidad (N = 1..n)."""
    o = np.argsort(-prob, kind="stable")
    return np.cumsum(np.where(ternaria[o] == "BAJA+2", CFG["ganancia_baja2"], CFG["costo"]))


# [Anotación · líneas 159–162] entrenar() combina PARAMS_FIJOS con la semilla, num_leaves y
#   min_sum_hessian_in_leaf recibidos y entrena LightGBM con num_iterations rondas, sin detención temprana.
def entrenar(params_bo, semilla, ds):
    p = dict(PARAMS_FIJOS, seed=semilla, num_leaves=int(params_bo["num_leaves"]),
             min_sum_hessian_in_leaf=float(params_bo["min_sum_hessian_in_leaf"]))
    return lgb.train(p, ds, num_boost_round=int(params_bo["num_iterations"]))     # todos los árboles


# [Anotación · líneas 165–179] correr_bayesiana(), preparación: define las distribuciones de los 3
#   hiperparámetros (enteras para num_iterations y num_leaves, continua para min_sum_hessian_in_leaf) y lee del
#   archivo .jsonl los trials ya completos, si existe.
# ---------------------------------------------------------------------------
# Bayesiana reproducible aunque se interrumpa.
# El registro de trials completos vive en un .jsonl (una línea por trial). Para proponer el trial k se arma
# un estudio nuevo en memoria con los k trials ya completos, en orden, y un muestreador con semilla = semilla_bo + k.
# La propuesta depende solo de k y de los resultados anteriores, no de cuántas veces ni dónde se cortó.
# ---------------------------------------------------------------------------
def correr_bayesiana(dtr, X_va, y_va, ruta_jsonl, despues_de_trial=None, etiqueta=""):
    esp = CFG["espacio"]
    dists = dict(num_iterations=optuna.distributions.IntDistribution(*esp["num_iterations"]),
                 num_leaves=optuna.distributions.IntDistribution(*esp["num_leaves"]),
                 min_sum_hessian_in_leaf=optuna.distributions.FloatDistribution(*esp["min_sum_hessian_in_leaf"]))
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    hist = [json.loads(l) for l in open(ruta_jsonl)] if os.path.exists(ruta_jsonl) else []
    if hist:
        log(f"  {etiqueta} retomando: {len(hist)} trials ya completos")
# [Anotación · líneas 180–203] Bucle hasta completar 10 trials. Para el trial k crea un estudio de Optuna que
#   maximiza, con TPESampler de semilla 878443 + k y n_startup_trials 12, le carga los trials anteriores, pide
#   una propuesta, entrena con la semilla 878443 y calcula el AUC sobre la matriz de validación. Agrega el
#   resultado como una línea del .jsonl y llama a la función de respaldo.
    while len(hist) < CFG["n_trials"]:
        k = len(hist)
        semilla_trial = CFG["semilla_bo"] + k
        estudio = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(
            seed=semilla_trial, n_startup_trials=CFG["n_startup_trials"]))
        for h in hist:
            estudio.add_trial(optuna.trial.create_trial(params=h["params"], distributions=dists, value=h["auc"]))
        trial = estudio.ask()
        t0 = time.time()
        hp = dict(num_iterations=trial.suggest_int("num_iterations", *esp["num_iterations"]),
                  num_leaves=trial.suggest_int("num_leaves", *esp["num_leaves"]),
                  min_sum_hessian_in_leaf=trial.suggest_float("min_sum_hessian_in_leaf", *esp["min_sum_hessian_in_leaf"]))
        m = entrenar(hp, CFG["semilla_bo"], dtr)                  # la bayesiana usa la primera semilla
        auc = float(roc_auc_score(y_va, m.predict(X_va)))
        del m
        gc.collect()
        seg = round(time.time() - t0)
        log(f"  {etiqueta} trial {k:>2}: it={hp['num_iterations']:>4} hojas={hp['num_leaves']:>4} "
            f"hess={hp['min_sum_hessian_in_leaf']:.6f} -> AUC {auc:.5f}  ({seg}s, semilla del muestreador {semilla_trial})")
        hist.append(dict(trial=k, params=hp, auc=auc, segundos=seg, semilla_muestreador=semilla_trial))
        with open(ruta_jsonl, "a") as fh:
            fh.write(json.dumps(hist[-1]) + "\n")
        if despues_de_trial:
            despues_de_trial()
# [Anotación · líneas 204–209] Elige el trial de mayor AUC (ante empate, el primero) y devuelve el historial,
#   los tres hiperparámetros de ese trial y su registro.
    mejor = max(hist, key=lambda h: h["auc"])                      # ante empate, el primero
    mejores = dict(num_iterations=int(mejor["params"]["num_iterations"]),
                   num_leaves=int(mejor["params"]["num_leaves"]),
                   min_sum_hessian_in_leaf=float(mejor["params"]["min_sum_hessian_in_leaf"]))
    log(f"  {etiqueta} MEJORES hiperparámetros (trial {mejor['trial']}, AUC {mejor['auc']:.5f}): {mejores}")
    return hist, mejores, mejor


# [Anotación · líneas 212–233] entrenar_semillas(): para cada semilla que no tenga todas sus predicciones
#   guardadas entrena un modelo, predice cada matriz recibida, guarda <nombre>_<semilla>.npy y registra el AUC
#   cuando hay clase para esa matriz. Devuelve las predicciones leídas de disco, por matriz y por semilla.
def entrenar_semillas(dtr, mejores, semillas, matrices, y_eval, dir_p, despues=None):
    """Entrena un modelo por semilla sobre dtr y predice cada matriz de `matrices` (dict nombre -> X).
    Guarda <nombre>_<semilla>.npy al terminar cada semilla (reanudable). Devuelve {nombre: {semilla: prob}}."""
    os.makedirs(dir_p, exist_ok=True)
    ruta = lambda nom, sd: os.path.join(dir_p, f"{nom}_{sd}.npy")
    pend = [sd for sd in semillas if not all(os.path.exists(ruta(n, sd)) for n in matrices)]
    log(f"  {len(semillas)} semillas {semillas}; pendientes {len(pend)}")
    for sd in pend:
        t = time.time()
        m = entrenar(mejores, sd, dtr)
        msg = []
        for nom, X in matrices.items():
            pr = m.predict(X).astype("float64")
            guardar_atomico(lambda r: np.save(open(r, "wb"), pr), ruta(nom, sd))
            if nom in y_eval:
                msg.append(f"AUC {nom} {roc_auc_score(y_eval[nom], pr):.5f}")
        log(f"  semilla {sd}: {', '.join(msg)}  ({time.time() - t:.0f}s)")
        del m
        gc.collect()
        if despues:
            despues()
    return {nom: {sd: np.load(ruta(nom, sd)) for sd in semillas} for nom in matrices}


# [Anotación · líneas 236–242] tabla_predicciones() arma un DataFrame con numero_de_cliente, foto_mes, las dos
#   clases, una columna prob_<semilla> por modelo y prob_ens, el promedio de esas columnas.
def tabla_predicciones(ids, mes, tern, yb, P):
    """DataFrame con identificación, clase real, una columna prob_<semilla> por semilla y prob_ens (promedio simple)."""
    out = pd.DataFrame(dict(numero_de_cliente=ids, foto_mes=mes, clase_ternaria=tern, clase_binaria=yb.astype("float32")))
    for sd, pr in P.items():
        out[f"prob_{sd}"] = pr
    out["prob_ens"] = out[[f"prob_{sd}" for sd in P]].mean(axis=1)
    return out


# [Anotación · líneas 245–263] resumen_mes() calcula el AUC de cada semilla y del promedio y lo guarda en
#   <prefijo>_auc.csv. Calcula la ganancia acumulada para envíos de 1.000 a 30.000 de a 100, por semilla, su
#   media y la del promedio de probabilidades, la guarda en <prefijo>_ganancia.csv y registra el máximo de las
#   dos últimas.
def resumen_mes(P, y_real, tern, prefijo, etiqueta):
    """AUC por semilla y del ensamble, y curva de ganancia (por semilla, media y ensamble) en un mes con clase real."""
    semillas = list(P)
    ens = np.mean([P[s] for s in semillas], axis=0)
    aucs = {s: float(roc_auc_score(y_real, P[s])) for s in semillas}
    auc_ens = float(roc_auc_score(y_real, ens))
    pd.DataFrame(dict(semilla=semillas + ["ensamble"], auc=list(aucs.values()) + [auc_ens])
                 ).to_csv(f"{prefijo}_auc.csv", index=False)
    log(f"  {etiqueta}: AUC media de semillas {np.mean(list(aucs.values())):.5f} "
        f"(sd {np.std(list(aucs.values()), ddof=1):.5f}), ensamble {auc_ens:.5f}")
    envios = np.arange(1000, min(30000, len(tern)) + 1, 100)
    tab = pd.DataFrame(dict(envios=envios, **{f"g_{s}": curva_ganancia(P[s], tern)[envios - 1] for s in semillas}))
    tab["g_media"] = tab[[f"g_{s}" for s in semillas]].mean(axis=1)
    tab["g_ens"] = curva_ganancia(ens, tern)[envios - 1]
    tab.to_csv(f"{prefijo}_ganancia.csv", index=False)
    for nombre in ("g_media", "g_ens"):
        k = int(tab[nombre].idxmax())
        log(f"  {etiqueta} {nombre}: máximo {tab[nombre][k] / 1e6:,.1f} M con {int(tab['envios'][k]):,} envíos "
            f"(mirar la curva suavizada, no solo el pico)")
```

### L20/codigo/01_preprocesamiento_L20.py

Genera el dataset L20_dataset.parquet a partir del CSV de la competencia: corrige ccajas_depositos en 202105, arma la clase binaria, calcula las variables históricas, aplica el ranking con cero fijo por mes y agrega los flags _zero.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–36] Docstring: enumera los 7 pasos del preprocesamiento en orden (lectura,
#   ccajas_depositos a NA en 202105, clase binaria, variables históricas, ranking con cero fijo, variables
#   _zero, escritura), el comando de uso y las salidas en ~/dmeyf y en el bucket.
"""
01_preprocesamiento_L20.py — DMEyF, 1ra competencia, L20: base de datos con lo recomendado por el profesor.
PASO 1: genera la base de datos en parquet.

Qué hace (en este orden):
  1) Lee competencia_01_ternaria.csv.
  2) ccajas_depositos = NA solo en 202105 (la columna está rota ese mes: todos ceros).
  3) clase_binaria: BAJA+1 y BAJA+2 = 1, CONTINUA = 0, resto (07 no-baja y 08) = NA.
     Se conserva clase_ternaria (la ganancia necesita distinguir BAJA+2).
  4) Variables históricas de todas las columnas, EXCEPTO las 10 sin historia (edad, antigüedad y fechas relativas):
        lag1, lag2, delta1 = x - lag1, delta2 = x - lag2                       (orden 1 y 2)
        tend3 = pendiente de la recta de cuadrados mínimos sobre el mes actual y los 2 anteriores
        avg3  = promedio de esos 3 meses
     Todo por UNIÓN con (cliente, mes-k), no con shift por fila: los meses faltantes quedan como NA.
     tend3 y avg3 necesitan al menos 2 meses disponibles (si no, NA). Réplica de fhistC del ejemplo en R (ventana=3).
  5) Ranking con cero fijo, por variable y por mes, sobre los SIETE grupos
     (original, lag1, delta1, lag2, delta2, tend3, avg3). Reemplaza a la variable cruda:
        x > 0 -> rank entre los positivos del mes / n_positivos      en (0, 1]
        x = 0 -> 0
        x < 0 -> -(rank de |x| entre los negativos del mes / n_neg)  en [-1, 0)
        NA    -> NA
  6) Variables _zero (recomendación 1.3): para cada variable ORIGINAL que alguna vez vale cero, un flag:
     1 si vale cero, NA si el original era NA, 0 en el resto. Se calculan sobre el valor crudo y NO se rankean.
     Quedan SIN rankear: numero_de_cliente, foto_mes, clase_ternaria, clase_binaria y las _zero.
  7) Guarda parquet (numero_de_cliente en float64) y lo copia al bucket.
Sin variables derivadas. Requiere preproc_comun.py en la misma carpeta que este script.

Uso (terminal de la VM, desde ~/dmeyf):
    pip install pandas pyarrow gcsfs
    nohup python 01_preprocesamiento_L20.py > L20_prep.log 2>&1 &

Salidas:
    ~/dmeyf/datasets/L20_dataset.parquet           -> gs://luisdsuarez_buckito2026/datasets/L20_dataset.parquet
    ~/dmeyf/exp/L20/L20_dataset_manifest.json      -> gs://luisdsuarez_buckito2026/exp/L20/
    ~/dmeyf/exp/L20/codigo/                        (copia de este script y de preproc_comun.py)
"""
# [Anotación · líneas 37–62] Importa argparse, json, os, shutil, subprocess, time, numpy, pandas y pyarrow, y
#   las funciones de preproc_comun.py (termina con un mensaje si ese módulo no está en la carpeta). Define
#   VOLUMEN = "L20", el bucket, la ruta de entrada en el bucket, MES_ROTO = 202105 y COL_ROTA =
#   "ccajas_depositos".
import argparse
import json
import os
import shutil
import subprocess
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

try:
    import preproc_comun as pc
    from preproc_comun import (NO_RANKEAR, SIN_HISTORIA, aplicar_lag, flag_zero, posicion_de_lag, rank_cero_fijo,
                               tendencia_promedio)
except ImportError:
    raise SystemExit("Falta preproc_comun.py: copiarlo a la misma carpeta que este script (~/dmeyf).")

VOLUMEN = "L20"
BUCKET = "gs://luisdsuarez_buckito2026"
ENTRADA = f"{BUCKET}/datasets/competencia_01_ternaria.csv"

MES_ROTO = 202105
COL_ROTA = "ccajas_depositos"


# [Anotación · líneas 64–77] log() imprime con la hora. gsutil() ejecuta gsutil con tiempo máximo de 3600 s y
#   devuelve si terminó con código 0; ante un error sólo registra un aviso.
def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def gsutil(*args):
    """Corre gsutil sin frenar el proceso si falla (el respaldo nunca debe romper el cálculo)."""
    try:
        r = subprocess.run(["gsutil", "-q", *args], capture_output=True, text=True, timeout=3600)
        if r.returncode != 0:
            log("  (aviso gsutil:", r.stderr.strip()[:300], ")")
        return r.returncode == 0
    except Exception as e:
        log("  (aviso gsutil:", e, ")")
        return False


# [Anotación · líneas 80–100] Argumentos --entrada, --volumen, --dir_base, --sin_bucket y --forzar. Crea
#   exp/L20/codigo y datasets/, copia allí este script y preproc_comun.py, y termina sin hacer nada si el
#   parquet ya existe y no se pasó --forzar.
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default=ENTRADA)
    ap.add_argument("--volumen", default=VOLUMEN)
    ap.add_argument("--dir_base", default=os.path.expanduser("~/dmeyf"))
    ap.add_argument("--sin_bucket", action="store_true", help="no copia nada al bucket (pruebas)")
    ap.add_argument("--forzar", action="store_true", help="regenera aunque el parquet ya exista")
    a = ap.parse_args()

    dir_exp = os.path.join(a.dir_base, "exp", a.volumen)
    dir_ds = os.path.join(a.dir_base, "datasets")
    os.makedirs(os.path.join(dir_exp, "codigo"), exist_ok=True)
    os.makedirs(dir_ds, exist_ok=True)
    shutil.copy(os.path.abspath(__file__), os.path.join(dir_exp, "codigo"))
    shutil.copy(os.path.abspath(pc.__file__), os.path.join(dir_exp, "codigo"))
    ruta_pq = os.path.join(dir_ds, f"{a.volumen}_dataset.parquet")
    t00 = time.time()

    if os.path.exists(ruta_pq) and not a.forzar:
        log(f"{ruta_pq} ya existe; nada que hacer (usar --forzar para regenerar)")
        return

# [Anotación · líneas 102–113] Lee el CSV con todas las columnas en float64 salvo numero_de_cliente (int64),
#   foto_mes (int32) y clase_ternaria (texto). Verifica que haya 152 variables originales, que no haya pares
#   (cliente, mes) duplicados y que existan las 10 columnas sin historia y ccajas_depositos.
    # ------------------------------------------------------------------ 1) lectura
    log("leyendo", a.entrada)
    cabecera = pd.read_csv(a.entrada, nrows=0).columns.tolist()
    dtypes = {c: "float64" for c in cabecera if c not in NO_RANKEAR}
    dtypes.update(numero_de_cliente="int64", foto_mes="int32", clase_ternaria="object")
    df = pd.read_csv(a.entrada, dtype=dtypes)
    cols = [c for c in df.columns if c not in NO_RANKEAR]
    log(f"  filas={len(df):,}  columnas={df.shape[1]}  features originales={len(cols)}")
    assert len(cols) == 152, f"se esperaban 152 features originales y hay {len(cols)}"
    assert not df.duplicated(["numero_de_cliente", "foto_mes"]).any(), "hay (cliente, mes) duplicados"
    faltan = [c for c in SIN_HISTORIA + [COL_ROTA] if c not in df.columns]
    assert not faltan, f"columnas esperadas que no están en el dataset: {faltan}"

# [Anotación · líneas 115–123] Selecciona las filas de 202105, verifica que ccajas_depositos valga cero (o NA)
#   en todas ellas, registra qué proporción es distinta de cero en los demás meses y la pasa a NA en 202105.
    # ------------------------------------------------------------------ 2) ccajas_depositos en 202105
    m = (df["foto_mes"] == MES_ROTO).to_numpy()
    assert m.sum() > 0, f"no hay filas de {MES_ROTO}"
    v = df.loc[m, COL_ROTA]
    assert (v.fillna(0) == 0).all(), f"{COL_ROTA} en {MES_ROTO} NO es todo cero: revisar antes de poner NA"
    otros = df.loc[~m, COL_ROTA]
    log(f"  {COL_ROTA} en {MES_ROTO}: {m.sum():,} filas, todas cero -> NA. "
        f"(en los demás meses: {(otros != 0).mean():.2%} distintos de cero)")
    df.loc[m, COL_ROTA] = np.nan

# [Anotación · líneas 125–132] Crea clase_binaria: 1 si clase_ternaria es BAJA+1 o BAJA+2, 0 si es CONTINUA,
#   NA en el resto. Registra la tabla de clase_ternaria por mes y verifica que 202103 a 202106 tengan clase en
#   todas las filas y que 202108 no tenga ninguna.
    # ------------------------------------------------------------------ 3) clase binaria
    t = df["clase_ternaria"]
    df["clase_binaria"] = np.where(t.isin(["BAJA+1", "BAJA+2"]), 1.0, np.where(t == "CONTINUA", 0.0, np.nan))
    df["clase_binaria"] = df["clase_binaria"].astype("float32")
    log("  clase_ternaria por mes:\n" + pd.crosstab(df["foto_mes"], t.fillna("NA")).to_string())
    for mes in (202103, 202104, 202105, 202106):
        assert df.loc[df["foto_mes"] == mes, "clase_binaria"].notna().all(), f"faltan clases en {mes}"
    assert df.loc[df["foto_mes"] == 202108, "clase_binaria"].isna().all(), "202108 no debería tener clase"

# [Anotación · líneas 134–145] Ordena por mes y cliente, convierte foto_mes en un período consecutivo (año ×
#   12 + mes) y arma una clave cliente × 100 + período. Con esa clave obtiene, para cada fila, la posición de la
#   fila del mismo cliente 1 y 2 meses antes (−1 si no existe) y guarda los índices de filas de cada mes.
    # ------------------------------------------------------------------ 4) preparación de lags
    df = df.sort_values(["foto_mes", "numero_de_cliente"], ignore_index=True)
    n = len(df)
    mes = df["foto_mes"].to_numpy()
    p = (mes // 100) * 12 + (mes % 100)                 # período consecutivo (cruza años sin problema)
    p0 = p - p.min()
    assert p0.max() < 99
    key = df["numero_de_cliente"].to_numpy().astype("int64") * 100 + p0
    pos = {1: posicion_de_lag(key, 1), 2: posicion_de_lag(key, 2)}
    for k in (1, 2):
        log(f"  filas con lag{k} disponible: {(pos[k] >= 0).mean():.1%}")
    idx_mes = [np.flatnonzero(mes == mm) for mm in np.unique(mes)]

# [Anotación · líneas 147–153] Control del lag de 1 mes: lo recalcula con un merge de pandas por (cliente,
#   período + 1) para mrentabilidad y ccajas_depositos y exige que coincida con el calculado por posiciones.
    # verificación independiente del lag1 (con un merge de pandas) en dos columnas
    for c in ("mrentabilidad", COL_ROTA):
        prev = pd.DataFrame({"numero_de_cliente": df["numero_de_cliente"], "p": p + 1, "ref": df[c]})
        ref = df[["numero_de_cliente"]].assign(p=p).merge(prev, on=["numero_de_cliente", "p"], how="left")["ref"].to_numpy()
        mio = aplicar_lag(df[c].to_numpy(), pos[1])
        assert np.array_equal(mio, ref, equal_nan=True), f"lag1 de {c} no coincide con el merge de control"
    log("  verificación de lag1 por merge independiente: OK")

# [Anotación · líneas 155–171] Control de tendencia y promedio: para mrentabilidad, ctrx_quarter y
#   ccajas_depositos toma 2.000 filas al azar (generador con semilla 878443) y compara tend3 con la pendiente de
#   np.polyfit y avg3 con la media de los puntos disponibles; con menos de 2 puntos exige NA.
    # verificación independiente de tend3 / avg3: ajuste de mínimos cuadrados con np.polyfit sobre una muestra de filas
    rng = np.random.default_rng(878443)
    for c in ("mrentabilidad", "ctrx_quarter", COL_ROTA):
        x = df[c].to_numpy()
        valor = pd.Series(x, index=key)
        l1c, l2c = aplicar_lag(x, pos[1]), aplicar_lag(x, pos[2])
        tend, avg = tendencia_promedio(x, l1c, l2c)
        for r in rng.choice(n, size=min(2000, n), replace=False):
            pts = [(xv, yv) for xv, yv in ((1.0, valor.get(key[r] - 2, np.nan)), (2.0, valor.get(key[r] - 1, np.nan)),
                                           (3.0, x[r])) if not np.isnan(yv)]
            if len(pts) < 2:
                assert np.isnan(tend[r]) and np.isnan(avg[r])
            else:
                xs_, ys_ = zip(*pts)
                assert np.isclose(tend[r], np.polyfit(xs_, ys_, 1)[0], rtol=1e-7, atol=1e-7), (c, r)
                assert np.isclose(avg[r], np.mean(ys_), rtol=1e-9, atol=1e-9), (c, r)
    log("  verificación de tend3 y avg3 contra np.polyfit: OK")

# [Anotación · líneas 173–175] Arma la lista de variables originales que valen cero en al menos una fila; son
#   las que llevan flag _zero.
    # variables _zero: solo para originales que alguna vez valen cero (NaN == 0 es False)
    cols_zero = [c for c in cols if (df[c].to_numpy() == 0).any()]
    log(f"  variables que alguna vez valen cero (llevan _zero): {len(cols_zero)} de {len(cols)}")

# [Anotación · líneas 177–189] Empieza la tabla de salida con las 4 columnas que no se rankean:
#   numero_de_cliente en float64, foto_mes en int32, clase_ternaria como texto y clase_binaria en float32.
    # ------------------------------------------------------------------ 5) historia + ranking
    nombres, arrays, grupos = [], [], {}
    for c in NO_RANKEAR:
        if c == "numero_de_cliente":
            arr = df[c].to_numpy().astype("float64")      # float64: los IDs no entran en float32
        elif c == "foto_mes":
            arr = df[c].to_numpy().astype("int32")
        elif c == "clase_ternaria":
            arr = pa.array(df[c], type=pa.string(), from_pandas=True)   # NaN -> nulo
        else:
            arr = df[c].to_numpy().astype("float32")
        nombres.append(c)
        arrays.append(arr if isinstance(arr, pa.Array) else pa.array(arr))

# [Anotación · líneas 191–199] agregar(): aplica el ranking con cero fijo por mes a un vector, verifica que el
#   patrón de NA y el signo de cada valor no cambien, y agrega la columna rankeada a la salida anotando a qué
#   grupo pertenece.
    def agregar(nombre, valores, grupo):
        r = rank_cero_fijo(valores, idx_mes)
        # chequeos baratos: mismo patrón de NA, mismo signo, el cero se conserva
        assert np.array_equal(np.isnan(r), np.isnan(valores)), f"{nombre}: cambió el patrón de NA"
        ok = ~np.isnan(valores)
        assert np.all(np.sign(r[ok]) == np.sign(valores[ok])), f"{nombre}: cambió el signo/cero"
        nombres.append(nombre)
        arrays.append(pa.array(r))
        grupos.setdefault(grupo, []).append(nombre)

# [Anotación · líneas 201–221] Para cada una de las 152 variables agrega la original rankeada; si no está en
#   la lista sin historia agrega también, rankeadas, lag1, delta1 (valor − lag1), lag2, delta2 (valor − lag2),
#   tend3 y avg3; si alguna vez vale cero agrega el flag _zero sin rankear. Registra el avance cada 20
#   variables.
    zeros_sin_rank = []                                   # (nombre, array float32): no se rankean
    for j, c in enumerate(cols):
        x = df[c].to_numpy()                              # float64
        agregar(c, x, "original")
        if c not in SIN_HISTORIA:
            l1, l2 = aplicar_lag(x, pos[1]), aplicar_lag(x, pos[2])
            agregar(f"{c}_lag1", l1, "lag1")
            agregar(f"{c}_delta1", x - l1, "delta1")
            agregar(f"{c}_lag2", l2, "lag2")
            agregar(f"{c}_delta2", x - l2, "delta2")
            tend, avg = tendencia_promedio(x, l1, l2)
            agregar(f"{c}_tend3", tend, "tend3")
            agregar(f"{c}_avg3", avg, "avg3")
        if c in cols_zero:
            fz = flag_zero(x)
            assert np.array_equal(np.isnan(fz), np.isnan(x)) and np.array_equal(fz[~np.isnan(x)] == 1, x[~np.isnan(x)] == 0)
            nombres.append(f"{c}_zero")
            arrays.append(pa.array(fz))
            grupos.setdefault("zero", []).append(f"{c}_zero")
        if (j + 1) % 20 == 0:
            log(f"  columnas procesadas: {j + 1}/{len(cols)}")

# [Anotación · líneas 223–228] Verifica que la cantidad de variables finales sea 152 + 142 × 6 + la cantidad
#   de flags _zero, y que ccajas_depositos y ccajas_depositos_zero sean NA en todas las filas de 202105.
    n_feat = len(nombres) - len(NO_RANKEAR)
    log(f"  features finales: {n_feat}  " + str({g: len(v) for g, v in grupos.items()}))
    assert n_feat == 152 + 142 * 6 + len(cols_zero), n_feat
    # ccajas_depositos de 202105 debe haber quedado en NA (original y flag _zero)
    for nom in (COL_ROTA, f"{COL_ROTA}_zero"):
        assert np.isnan(arrays[nombres.index(nom)].to_numpy(zero_copy_only=False)[mes == MES_ROTO]).all(), nom

# [Anotación · líneas 230–251] Escribe el parquet con compresión zstd (primero a un .tmp que luego renombra) y
#   un manifiesto JSON con filas, columnas, listas de variables y cantidad por grupo. Salvo con --sin_bucket
#   copia el parquet y la carpeta del experimento al bucket.
    # ------------------------------------------------------------------ 6) escritura
    tabla = pa.Table.from_arrays(arrays, names=nombres)
    tmp = ruta_pq + ".tmp"
    pq.write_table(tabla, tmp, compression="zstd")
    os.replace(tmp, ruta_pq)
    log(f"parquet escrito: {ruta_pq}  ({os.path.getsize(ruta_pq) / 1e9:.2f} GB, {n:,} filas x {len(nombres)} columnas)")

    manifest = dict(volumen=a.volumen, entrada=a.entrada, filas=n, columnas=len(nombres),
                    sin_historia=SIN_HISTORIA, no_rankeadas=NO_RANKEAR + [f"{c}_zero" for c in cols_zero],
                    variables_con_zero=cols_zero,
                    grupos={g: len(v) for g, v in grupos.items()},
                    ccajas_depositos_NA_en=MES_ROTO,
                    ranking="cero fijo con signo, por variable y por mes (rank average / n); _zero sin rankear",
                    ventana_tendencia=3,
                    columnas_features=[c for c in nombres if c not in NO_RANKEAR])
    with open(os.path.join(dir_exp, f"{a.volumen}_dataset_manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)

    if not a.sin_bucket:
        gsutil("cp", ruta_pq, f"{BUCKET}/datasets/{a.volumen}_dataset.parquet")
        gsutil("-m", "rsync", "-r", dir_exp, f"{BUCKET}/exp/{a.volumen}")
    log(f"listo en {(time.time() - t00) / 60:.1f} min")


# [Anotación · líneas 254–255] Punto de entrada del script: ejecuta main().
if __name__ == "__main__":
    main()
```

### L20/codigo/correr_L20.sh

Script de shell que ejecuta en cadena 01_preprocesamiento_L20.py, 02_etapa1_L20.py y 03_etapa2_L20.py (cada uno sólo si el anterior terminó con código 0), con candado contra corridas simultáneas, log, respaldo al bucket y apagado opcional de la máquina.

```
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–10] Comentarios de uso: comando con y sin --apagar, cómo seguir el log y que la
#   corrida se puede relanzar tras un corte.
#!/bin/bash
# correr_L20.sh — corre el paso 1 y, si termina bien, el paso 2. Opcionalmente apaga la VM al final.
#
# Uso (desde ~/dmeyf, con los dos .py en la misma carpeta):
#     nohup bash correr_L20.sh --apagar > /dev/null 2>&1 &     # corre todo y apaga la VM
#     nohup bash correr_L20.sh           > /dev/null 2>&1 &    # corre todo y la deja encendida
#
# Seguimiento (estos comandos devuelven el prompt):   tail -n 30 L20_todo.log
# Es reanudable: si la VM spot se corta, encenderla y relanzar el mismo comando; cada script
# saltea lo que ya terminó.
# [Anotación · líneas 11–16] Se ubica en la carpeta del script, lee la opción --apagar, define el bucket y
#   redirige toda la salida a L20_todo.log.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
APAGAR=0
[ "$1" = "--apagar" ] && APAGAR=1
BUCKET=gs://luisdsuarez_buckito2026
LOG=L20_todo.log
exec >> "$LOG" 2>&1                       # todo lo que sigue va al log

# [Anotación · líneas 18–29] Toma un candado con flock sobre /tmp/correr_dmeyf.lock y termina si ya hay una
#   corrida; también termina si pgrep encuentra en ejecución algún script python con nombre 01_, 02_ o 03_ de
#   algún volumen.
# Candado: impide lanzar una segunda corrida mientras la primera sigue viva
# (dos procesos sobre el mismo estudio se pisan los núcleos y la RAM, y todo se vuelve lentísimo).
exec 9> /tmp/correr_dmeyf.lock                 # mismo candado para todos los volúmenes
if ! flock -n 9; then
    echo "$(date '+%F %T') YA HAY UNA CORRIDA EN CURSO: esta se cancela"
    exit 1
fi
# además: no arrancar si quedó algún script de CUALQUIER volumen todavía vivo (p. ej. L15)
if pgrep -f "^([^ ]*/)?python[0-9.]* +(\./)?0[123]_[a-z0-9_]*_L[0-9]+\.py" > /dev/null; then
    echo "$(date '+%F %T') HAY OTRO SCRIPT DE UN VOLUMEN ANTERIOR TODAVÍA CORRIENDO: esta corrida se cancela"
    exit 1
fi

# [Anotación · líneas 31–50] Copia el propio script a exp/L20/codigo y ejecuta el preprocesamiento; si
#   devuelve 0 ejecuta la etapa 1 y, si ésta devuelve 0, la etapa 2. Registra el código de salida y, si alguno
#   no fue 0, que las etapas siguientes no se corrieron.
mkdir -p exp/L20/codigo
cp "$(readlink -f "$0")" exp/L20/codigo/        # copia del código para reproducibilidad

echo "$(date '+%F %T') === inicio (apagar al final: $APAGAR)"
python 01_preprocesamiento_L20.py
RC=$?
if [ $RC -eq 0 ]; then
    echo "$(date '+%F %T') === paso 1 (preprocesamiento) OK; empieza la etapa 1"
    python 02_etapa1_L20.py
    RC=$?
fi
if [ $RC -eq 0 ]; then
    echo "$(date '+%F %T') === etapa 1 OK; empieza la etapa 2"
    python 03_etapa2_L20.py
    RC=$?
fi
if [ $RC -ne 0 ]; then
    echo "$(date '+%F %T') === algo falló (código $RC): las etapas siguientes NO se corrieron"
fi
echo "$(date '+%F %T') === fin (código $RC)"

# [Anotación · líneas 52–60] Copia el log a exp/L20, sincroniza esa carpeta con el bucket y, si se pasó
#   --apagar, apaga la máquina.
# respaldo del log junto al experimento (si el paso 1 falló, igual queda el diagnóstico)
mkdir -p exp/L20
cp "$LOG" exp/L20/
gsutil -q -m rsync -r exp/L20 "$BUCKET/exp/L20"

if [ $APAGAR -eq 1 ]; then
    echo "$(date '+%F %T') apagando la VM"
    sudo shutdown -h now
fi
```

### L20/codigo/02_etapa1_L20.py

Etapa 1 de L20. Parte A: búsqueda de 3 hiperparámetros entrenando con 202103-202104 sin las columnas de préstamos y midiendo AUC en 202106; escribe L20_e1_hiperparametros.json, que es la salida que usa L22. Partes B y C: 10 modelos que predicen 202105 y 202106 y clase artificial por mes (según el README, no intervienen en L22).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] Docstring: describe las tres partes del script (A: búsqueda de hiperparámetros, B:
#   10 modelos que predicen 202105 y 202106, C: clase artificial) y los archivos que deja en exp/L20/.
"""
02_etapa1_L20.py — DMEyF, 1ra competencia, L20 (data augmentation con 05 y 06). ETAPA 1.

Requiere 01_preprocesamiento_L20.py (con preproc_comun.py) y comun_L20.py (misma carpeta). Sin variables derivadas.
L20 = L19 + lo recomendado por el profesor: tendencia y promedio de 3 meses, y variables _zero.

  A) Bayesiana (primera semilla, 878443; 3 hiperparámetros con rangos de Pasquini; 10 trials aleatorios):
     entrena con 202103 y 202104 SIN las variables de préstamos (cprestamos_personales y mprestamos_personales
     y todas sus variantes: lag1, delta1, lag2, delta2, tend3, avg3 y _zero = 16 columnas) y valida con 202106 (clase real, AUC).
  B) Con los hiperparámetros encontrados: 10 modelos, 10 semillas, entrenados en 03-04 sin préstamos,
     que predicen 202105 y 202106. Se guardan las predicciones.
  C) CLASE ARTIFICIAL: con la probabilidad promedio de las 10 semillas, se etiqueta BAJA (1) a la proporción
     1,251 % de clientes con mayor probabilidad (CADA MES POR SEPARADO) y CONTINUA (0) al resto. 05 y 06.
     Se guarda en un archivo aparte; no se mezcla con la clase real ni con el dataset.

Salidas en ~/dmeyf/exp/L20/ (y copia en el bucket):
    config_e1.json, L20_e1_bo_trials.jsonl, L20_e1_bayesiana.csv, L20_e1_hiperparametros.json
    L20_e1_pred_05_06.parquet     predicciones (prob_<semilla> x10 + prob_ens) de 05 y 06, con la clase real
    L20_e1_auc_05.csv / _06.csv, L20_e1_ganancia_05.csv / _06.csv
    L20_clase_artificial.parquet  numero_de_cliente, foto_mes, clase_artificial (0/1), prob_ens, clase_binaria (real)

Uso:  nohup python 02_etapa1_L20.py > L20_e1.log 2>&1 &    (o con el runner correr_L20.sh)
"""
# [Anotación · líneas 24–33] Importa argparse, json, os, lightgbm, numpy, pandas y el módulo comun_L20.
import argparse
import json
import os

import lightgbm as lgb
import numpy as np
import pandas as pd

import comun_L20 as cm
from comun_L20 import log


# [Anotación · líneas 36–43] clase_artificial(): marca con 1 a la proporción `prop` de filas de mayor
#   probabilidad promedio y con 0 al resto; devuelve el vector y la cantidad marcada.
def clase_artificial(prob_ens, prop):
    """1 (BAJA) a la proporción `prop` de mayor probabilidad; 0 (CONTINUA) al resto."""
    n = len(prob_ens)
    k = int(round(prop * n))
    orden = np.argsort(-prob_ens, kind="stable")
    y = np.zeros(n, dtype="int8")
    y[orden[:k]] = 1
    return y, k


# [Anotación · líneas 46–65] Argumentos --volumen, --dir_base, --dataset, --sin_bucket y --prueba. Crea la
#   carpeta del experimento con la copia del código, obtiene las 10 semillas y escribe config_e1.json con la
#   configuración, los parámetros fijos, la ruta del dataset, las semillas y las versiones de lightgbm y pandas.
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volumen", default=cm.VOLUMEN)
    ap.add_argument("--dir_base", default=os.path.expanduser("~/dmeyf"))
    ap.add_argument("--dataset", default=None)
    ap.add_argument("--sin_bucket", action="store_true")
    ap.add_argument("--prueba", action="store_true", help="SOLO para probar el código: pocos trials y árboles chicos")
    a = ap.parse_args()
    if a.prueba:
        cm.modo_prueba()

    dir_exp = cm.preparar(a.volumen, a.dir_base, [__file__])
    ruta_pq = a.dataset or os.path.join(a.dir_base, "datasets", f"{a.volumen}_dataset.parquet")
    pref = os.path.join(dir_exp, f"{a.volumen}_e1")
    sync = lambda: cm.sync(dir_exp, a.volumen, not a.sin_bucket)
    semillas = cm.semillas_n(cm.CFG["n_semillas"])
    with open(os.path.join(dir_exp, "config_e1.json"), "w") as fh:
        json.dump(dict(CFG=cm.CFG, params_fijos=cm.PARAMS_FIJOS, dataset=ruta_pq, semillas=semillas,
                       versiones=dict(lightgbm=lgb.__version__, pandas=pd.__version__)), fh, indent=1, default=list)
    sync()

# [Anotación · líneas 67–75] Carga los meses 202103 a 202106, obtiene los índices de columnas sin las 16 de
#   préstamos y arma las máscaras de entrenamiento (202103 y 202104), de 202105 y de 202106; verifica que no
#   falte la clase binaria.
    log(f"=== ETAPA 1 ({a.volumen}): cargando meses 03 a 06 de {ruta_pq}")
    D = cm.cargar(ruta_pq, [202103, 202104, 202105, 202106])
    X, mes, yb, cols = D["X"], D["mes"], D["yb"], D["cols"]
    idx, cols_sp, excl = cm.idx_sin_prestamos(cols)
    log(f"  entrenamiento SIN {len(excl)} columnas de préstamos ({len(cols_sp)} de {len(cols)} features)")

    tr = np.isin(mes, [202103, 202104])
    m05, m06 = mes == 202105, mes == 202106
    assert not np.isnan(yb[tr]).any() and not np.isnan(yb[m06]).any() and not np.isnan(yb[m05]).any()

# [Anotación · líneas 77–89] Parte A: construye el Dataset de LightGBM con 202103-202104 sin préstamos y las
#   matrices de 202106 y 202105. Corre la búsqueda midiendo AUC en 202106, guarda la tabla de trials en
#   L20_e1_bayesiana.csv y escribe L20_e1_hiperparametros.json con los hiperparámetros del trial elegido, su
#   AUC, los parámetros fijos, los meses usados y las columnas excluidas.
    # ---------------------------------------------------------------- A) bayesiana
    log(f"=== A) Bayesiana: train 03-04 ({tr.sum():,} filas, {yb[tr].mean():.3%} positivos) -> valida 06 real")
    dtr = lgb.Dataset(X[np.ix_(np.flatnonzero(tr), idx)], yb[tr], feature_name=cols_sp, params=cm.PARAMS_DATASET).construct()
    X06 = X[np.ix_(np.flatnonzero(m06), idx)]
    X05 = X[np.ix_(np.flatnonzero(m05), idx)]
    hist, mejores, mejor = cm.correr_bayesiana(dtr, X06, yb[m06], f"{pref}_bo_trials.jsonl", sync, "[e1]")
    pd.DataFrame([dict(trial=h["trial"], auc=h["auc"], **h["params"], segundos=h["segundos"],
                       semilla_muestreador=h["semilla_muestreador"]) for h in hist]).to_csv(f"{pref}_bayesiana.csv", index=False)
    with open(f"{pref}_hiperparametros.json", "w") as fh:
        json.dump(dict(mejores_hiperparametros=mejores, auc_validacion_06=mejor["auc"], trial_ganador=mejor["trial"],
                       params_fijos=cm.PARAMS_FIJOS, semilla_bayesiana=cm.CFG["semilla_bo"],
                       entrenamiento=[202103, 202104], validacion=202106, columnas_excluidas=excl), fh, indent=1)
    sync()

# [Anotación · líneas 91–101] Parte B: con esos hiperparámetros entrena 10 modelos (uno por semilla) sobre el
#   mismo Dataset, predice 202105 y 202106, guarda L20_e1_pred_05_06.parquet y, para cada mes, los archivos de
#   AUC y de curva de ganancia.
    # ---------------------------------------------------------------- B) 10 modelos -> predicen 05 y 06
    log(f"=== B) 10 modelos (03-04, sin préstamos) que predicen 05 y 06")
    P = cm.entrenar_semillas(dtr, mejores, semillas, {"m05": X05, "m06": X06},
                             {"m05": yb[m05], "m06": yb[m06]}, os.path.join(dir_exp, "pred_e1"), sync)
    del dtr, X05, X06
    pred = pd.concat([
        cm.tabla_predicciones(D["ids"][m], mes[m], D["tern"][m], yb[m], P[nom]) for nom, m in (("m05", m05), ("m06", m06))
    ], ignore_index=True)
    cm.guardar_atomico(lambda r: pred.to_parquet(r, index=False), f"{pref}_pred_05_06.parquet")
    for nom, m, etq in (("m05", m05, "05"), ("m06", m06, "06")):
        cm.resumen_mes(P[nom], yb[m], D["tern"][m], f"{pref}_{etq}", f"[e1 {etq}]")

# [Anotación · líneas 103–122] Parte C: para 202105 y 202106 por separado marca como BAJA al 1,251 % de
#   clientes de mayor prob_ens, registra cuántos coinciden con la clase binaria real y guarda
#   L20_clase_artificial.parquet con cliente, mes, clase artificial, prob_ens y clase real.
    # ---------------------------------------------------------------- C) clase artificial
    prop = cm.CFG["prop_baja_artificial"]
    log(f"=== C) Clase artificial: {prop:.3%} de mayor probabilidad promedio = BAJA, por mes")
    partes = []
    for mm in (202105, 202106):
        s = pred[pred["foto_mes"] == mm].reset_index(drop=True)
        y_art, k = clase_artificial(s["prob_ens"].to_numpy(), prop)
        real = s["clase_binaria"].to_numpy() == 1
        aciertos = int(((y_art == 1) & real).sum())
        log(f"  {mm}: {len(s):,} clientes, {k:,} etiquetados BAJA | BAJA real: {int(real.sum()):,} | "
            f"coinciden {aciertos:,} (precisión {aciertos / k:.1%}, cobertura {aciertos / real.sum():.1%}) | "
            f"prob_ens de corte {s['prob_ens'].nlargest(k).iloc[-1]:.5f}")
        partes.append(pd.DataFrame(dict(numero_de_cliente=s["numero_de_cliente"].to_numpy().astype("int64"),
                                        foto_mes=s["foto_mes"].to_numpy().astype("int32"),
                                        clase_artificial=y_art, prob_ens=s["prob_ens"].to_numpy(),
                                        clase_binaria=s["clase_binaria"].to_numpy())))
    art = pd.concat(partes, ignore_index=True)
    cm.guardar_atomico(lambda r: art.to_parquet(r, index=False), os.path.join(dir_exp, f"{a.volumen}_clase_artificial.parquet"))
    sync()
    log("etapa 1 lista")


# [Anotación · líneas 125–126] Punto de entrada del script: ejecuta main().
if __name__ == "__main__":
    main()
```

### L22b/codigo/01_entrenar_08_L22.py

Copia idéntica de L22/codigo/01_entrenar_08_L22.py guardada por la corrida del volumen L22b (segunda máquina, posiciones de semilla 200 a 399).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–27] Docstring: entrenamiento final con 202103 a 202106 para predecir 202108, con los
#   hiperparámetros de la etapa 1 de L20 y todas las columnas. Explica que se puede interrumpir y retomar, cómo
#   repartir rangos de semillas entre dos máquinas (volúmenes L22 y L22b) y qué archivos deja en exp/<volumen>/.
"""
01_entrenar_08_L22.py — DMEyF, 1ra competencia, L22: entrenamiento FINAL con 03, 04, 05 y 06 reales para predecir 08.

Usa el dataset y los hiperparámetros de L20 (etapa 1, clase real). No hay bayesiana ni clase artificial.
Entrena MUCHOS modelos, uno por semilla, con TODAS las columnas (incluidas las variables de préstamos, que se
excluyeron solo para evaluar en 06), y guarda la predicción sobre 08 de cada modelo apenas termina.

SE PUEDE INTERRUMPIR EN CUALQUIER MOMENTO (kill o corte de la VM): cada predicción se guarda de forma atómica y al
relanzar el mismo comando se retoma con la primera semilla que falte. Solo se pierde el modelo en curso.
Para ensamblar lo disponible en cualquier momento (también mientras sigue corriendo este script):
    python 02_ensamblar_08_L22.py

VARIAS VM EN PARALELO: cada VM debe usar un rango de semillas distinto y su propio --volumen, por ejemplo
    VM 1:  bash correr_L22.sh                                          (semillas 0 a 199, volumen L22)
    VM 2:  bash correr_L22.sh --volumen L22b --desde 200               (semillas 200 a 399, volumen L22b)
Después se ensamblan juntas: python 02_ensamblar_08_L22.py --otros L22b

Uso (desde ~/dmeyf):
    nohup bash correr_L22.sh > /dev/null 2>&1 &         # recomendado
    # o directamente: nohup python 01_entrenar_08_L22.py > L22_modelos.log 2>&1 &

Salidas en ~/dmeyf/exp/L22/ (y copia en gs://luisdsuarez_buckito2026/exp/L22/):
    hiperparametros_origen.json    copia de los hiperparámetros de L20 que se usaron
    config.json, ids_08.npy        (orden de los clientes de 08 al que corresponden todas las predicciones)
    pred_08/prob_<semilla>.npy     probabilidad de BAJA para los clientes de 08, un archivo por modelo
    L22_pred_08_ens_<n>modelos.parquet   ensamble (numero_de_cliente, prob_ens), lo genera 02_ensamblar_08_L22.py
"""
# [Anotación · líneas 28–43] Importa argparse, json, os, shutil, time, lightgbm, numpy, pandas y el módulo
#   comun_L22. Define MESES_TRAIN = 202103, 202104, 202105 y 202106, MES_PRED = 202108 y MAX_SEMILLAS = 1000.
import argparse
import json
import os
import shutil
import time

import lightgbm as lgb
import numpy as np
import pandas as pd

import comun_L22 as cm
from comun_L22 import log

MESES_TRAIN = [202103, 202104, 202105, 202106]
MES_PRED = 202108
MAX_SEMILLAS = 1000                 # lista ordenada de semillas; el script se detiene al llegar a --n_semillas


# [Anotación · líneas 46–62] Argumentos: --volumen (L22 por defecto), --dir_base (~/dmeyf), --dataset,
#   --hiperparametros, --n_semillas (200 por defecto), --desde (posición inicial en la lista de semillas, 0 por
#   defecto) y --sin_bucket. Arma las rutas del parquet y del JSON de hiperparámetros de L20, crea la carpeta
#   del experimento con la copia del código y define la función de respaldo al bucket.
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volumen", default=cm.VOLUMEN)
    ap.add_argument("--dir_base", default=os.path.expanduser("~/dmeyf"))
    ap.add_argument("--dataset", default=None, help="por defecto ~/dmeyf/datasets/L20_dataset.parquet")
    ap.add_argument("--hiperparametros", default=None, help="por defecto ~/dmeyf/exp/L20/L20_e1_hiperparametros.json")
    ap.add_argument("--n_semillas", type=int, default=200, help="cantidad de semillas de este rango (tope de modelos; se puede interrumpir antes)")
    ap.add_argument("--desde", type=int, default=0,
                    help="posición inicial en la lista ordenada de semillas. Este rango usa las posiciones [desde, desde + n_semillas). "
                         "Para una segunda VM: --desde 200 (con el tope por defecto de 200 de la primera) y otro --volumen")
    ap.add_argument("--sin_bucket", action="store_true")
    a = ap.parse_args()

    ruta_pq = a.dataset or os.path.join(a.dir_base, "datasets", "L20_dataset.parquet")
    ruta_hp = a.hiperparametros or os.path.join(a.dir_base, "exp", "L20", "L20_e1_hiperparametros.json")
    dir_exp = cm.preparar(a.volumen, a.dir_base, [__file__])
    sync = lambda: cm.sync(dir_exp, a.volumen, not a.sin_bucket)

# [Anotación · líneas 64–76] Lee mejores_hiperparametros del JSON y verifica que tenga exactamente
#   num_iterations, num_leaves y min_sum_hessian_in_leaf; copia ese JSON como hiperparametros_origen.json. Toma
#   de la lista de 1000 semillas las posiciones [desde, desde + n_semillas) y escribe config.json con rutas,
#   hiperparámetros, meses, rango de semillas, las primeras 25 semillas y las versiones de lightgbm y pandas.
    with open(ruta_hp) as fh:
        mejores = json.load(fh)["mejores_hiperparametros"]
    assert set(mejores) == {"num_iterations", "num_leaves", "min_sum_hessian_in_leaf"}, mejores
    shutil.copy(ruta_hp, os.path.join(dir_exp, "hiperparametros_origen.json"))
    assert a.desde >= 0 and a.desde + a.n_semillas <= MAX_SEMILLAS, f"el rango debe caber en las {MAX_SEMILLAS} semillas disponibles"
    semillas = cm.semillas_n(MAX_SEMILLAS)[a.desde:a.desde + a.n_semillas]
    with open(os.path.join(dir_exp, "config.json"), "w") as fh:
        json.dump(dict(dataset=ruta_pq, hiperparametros=ruta_hp, mejores_hiperparametros=mejores,
                       params_fijos=cm.PARAMS_FIJOS, meses_entrenamiento=MESES_TRAIN, mes_prediccion=MES_PRED,
                       rango_semillas=dict(desde=a.desde, hasta_sin_incluir=a.desde + a.n_semillas,
                                           primera=semillas[0], ultima=semillas[-1]),
                       primeras_semillas=semillas[:25], n_semillas_tope=a.n_semillas,
                       versiones=dict(lightgbm=lgb.__version__, pandas=pd.__version__)), fh, indent=1)
# [Anotación · líneas 77–86] Carga del parquet los meses de entrenamiento y 202108, arma las máscaras de filas
#   de entrenamiento y de predicción y verifica que no falte la clase binaria en entrenamiento. Registra
#   cantidad de filas, proporción de positivos y cantidad de columnas.
    log(f"=== {a.volumen}: hiperparámetros de {ruta_hp}: {mejores}")
    log(f"=== semillas: posiciones {a.desde} a {a.desde + a.n_semillas - 1} de la lista fija (de {semillas[0]} a {semillas[-1]})")
    log(f"=== cargando meses {MESES_TRAIN + [MES_PRED]} de {ruta_pq}")
    D = cm.cargar(ruta_pq, MESES_TRAIN + [MES_PRED])
    X, mes, yb, cols = D["X"], D["mes"], D["yb"], D["cols"]
    tr, fut = np.isin(mes, MESES_TRAIN), mes == MES_PRED
    assert not np.isnan(yb[tr]).any(), "faltan clases reales en los meses de entrenamiento"
    assert fut.sum() > 0
    log(f"  entrenamiento: {tr.sum():,} filas, {yb[tr].mean():.3%} positivos, {len(cols)} features (TODAS, con préstamos) "
        f"| a predecir: {fut.sum():,} clientes de {MES_PRED}")

# [Anotación · líneas 88–93] Guarda en ids_08.npy los numero_de_cliente de 202108 en el orden de las
#   predicciones; si el archivo ya existe exige que coincida con los ids cargados.
    # los clientes de 08, en el orden al que corresponden todas las predicciones; protege contra mezclar corridas
    ruta_ids = os.path.join(dir_exp, "ids_08.npy")
    if os.path.exists(ruta_ids):
        assert np.array_equal(np.load(ruta_ids), D["ids"][fut]), "ids_08.npy no coincide: ¿otro dataset? No mezclar corridas"
    else:
        cm.guardar_atomico(lambda r: np.save(open(r, "wb"), D["ids"][fut]), ruta_ids)

# [Anotación · líneas 95–99] Arma la lista de semillas del rango que todavía no tienen
#   pred_08/prob_<semilla>.npy.
    dir_p = os.path.join(dir_exp, "pred_08")
    os.makedirs(dir_p, exist_ok=True)
    ruta = lambda sd: os.path.join(dir_p, f"prob_{sd}.npy")
    pend = [sd for sd in semillas if not os.path.exists(ruta(sd))]
    log(f"  modelos ya guardados: {len(semillas) - len(pend)} | pendientes hasta el tope de {len(semillas)}: {len(pend)}")
# [Anotación · líneas 100–114] Si hay semillas pendientes construye el Dataset de LightGBM con las filas de
#   entrenamiento y todas las columnas, y para cada semilla entrena un modelo, predice 202108, guarda las
#   probabilidades en prob_<semilla>.npy, libera el modelo, registra el tiempo y respalda al bucket.
    if pend:
        dtr = lgb.Dataset(X[tr], yb[tr], feature_name=cols, params=cm.PARAMS_DATASET).construct()
        X08 = X[fut]
        del X, D["X"]
        hechos, t_ini = len(semillas) - len(pend), time.time()
        for i, sd in enumerate(pend, 1):
            t = time.time()
            m = cm.entrenar(mejores, sd, dtr)
            pr = m.predict(X08).astype("float64")
            cm.guardar_atomico(lambda r: np.save(open(r, "wb"), pr), ruta(sd))
            del m
            cm.gc.collect()
            log(f"  modelo {hechos + i} (semilla {sd}): {time.time() - t:.0f}s | en esta corrida: {i} modelos, "
                f"{(time.time() - t_ini) / i / 60:.1f} min por modelo")
            sync()
# [Anotación · líneas 115–118] Al terminar el rango llama a ensamblar_08 con las predicciones del volumen y
#   respalda al bucket.
    log("tope de modelos alcanzado; ensamblando")
    cm.ensamblar_08(dir_exp, a.volumen, cm.semillas_n(MAX_SEMILLAS))
    sync()
    log("listo")


# [Anotación · líneas 121–122] Punto de entrada del script: ejecuta main().
if __name__ == "__main__":
    main()
```

### L22b/codigo/correr_L22.sh

Copia idéntica de L22/codigo/correr_L22.sh guardada por la corrida del volumen L22b.

```
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Comentarios de uso: comandos para la primera máquina (semillas 0 a 199, volumen
#   L22) y la segunda (--volumen L22b --desde 200), opción --apagar, cómo seguir el log y cómo interrumpir y
#   retomar.
#!/bin/bash
# correr_L22.sh — entrena modelos con 03-06 (una semilla tras otra) y guarda la predicción de 08 de cada uno.
#
# Uso (desde ~/dmeyf, con 01_entrenar_08_L22.py y comun_L22.py en la misma carpeta):
#     nohup bash correr_L22.sh > /dev/null 2>&1 &                                  # VM 1: semillas 0 a 199, volumen L22
#     nohup bash correr_L22.sh --volumen L22b --desde 200 > /dev/null 2>&1 &       # VM 2: semillas 200 a 399, volumen L22b
# Opciones: cualquier argumento de 01_entrenar_08_L22.py (--volumen, --desde, --n_semillas, --dataset, --hiperparametros)
#           y --apagar (apaga la VM al terminar; necesita sudo).
#
# Seguimiento (devuelve el prompt):   tail -n 30 <volumen>_todo.log     (L22_todo.log o L22b_todo.log)
# Se puede interrumpir cuando quieras (pkill -f 01_entrenar_08_L22.py): lo ya guardado queda, y se puede
# ensamblar con: python 02_ensamblar_08_L22.py
# Es reanudable: si la VM spot se corta, encenderla y relanzar el mismo comando.
# [Anotación · líneas 14–28] Se ubica en la carpeta del script, separa --apagar y --volumen del resto de los
#   argumentos, define el bucket y redirige toda la salida a <volumen>_todo.log.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
VOL=L22
APAGAR=0
ARGS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --apagar)  APAGAR=1 ;;
        --volumen) VOL="$2"; ARGS+=("$1" "$2"); shift ;;
        *)         ARGS+=("$1") ;;
    esac
    shift
done
BUCKET=gs://luisdsuarez_buckito2026
LOG=${VOL}_todo.log
exec >> "$LOG" 2>&1                       # todo lo que sigue va al log

# [Anotación · líneas 30–41] Toma un candado con flock sobre /tmp/correr_dmeyf.lock y termina si ya hay una
#   corrida en esa máquina; también termina si pgrep encuentra en ejecución algún script python con nombre 01_,
#   02_ o 03_ de algún volumen.
# Candado: impide lanzar una segunda corrida mientras la primera sigue viva EN ESTA VM
# (dos procesos de LightGBM se pisan los núcleos y la RAM, y todo se vuelve lentísimo).
exec 9> /tmp/correr_dmeyf.lock
if ! flock -n 9; then
    echo "$(date '+%F %T') YA HAY UNA CORRIDA EN CURSO: esta se cancela"
    exit 1
fi
# además: no arrancar si quedó algún script de CUALQUIER volumen todavía vivo
if pgrep -f "^([^ ]*/)?python[0-9.]* +(\./)?0[123]_[a-z0-9_]*_L[0-9]+[a-z]?\.py" > /dev/null; then
    echo "$(date '+%F %T') HAY OTRO SCRIPT DE UN VOLUMEN ANTERIOR TODAVÍA CORRIENDO: esta corrida se cancela"
    exit 1
fi

# [Anotación · líneas 43–49] Copia el propio script a exp/<volumen>/codigo, ejecuta 01_entrenar_08_L22.py con
#   los argumentos recibidos y registra el código de salida.
mkdir -p exp/$VOL/codigo
cp "$(readlink -f "$0")" exp/$VOL/codigo/        # copia del código para reproducibilidad

echo "$(date '+%F %T') === inicio: volumen $VOL, argumentos: ${ARGS[*]} (apagar al final: $APAGAR)"
python 01_entrenar_08_L22.py "${ARGS[@]}"
RC=$?
echo "$(date '+%F %T') === fin (código $RC)"

# [Anotación · líneas 51–58] Copia el log a la carpeta del experimento, sincroniza la carpeta con el bucket y,
#   si se pasó --apagar, apaga la máquina con shutdown.
# respaldo del log junto al experimento
cp "$LOG" exp/$VOL/
gsutil -q -m rsync -r exp/$VOL "$BUCKET/exp/$VOL"

if [ $APAGAR -eq 1 ]; then
    echo "$(date '+%F %T') apagando la VM"
    sudo shutdown -h now
fi
```

### L22b/codigo/comun_L22.py

Copia idéntica de L22/codigo/comun_L22.py guardada por la corrida del volumen L22b.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Docstring del módulo. Nombra como scripts que lo importan a 02_etapa1_L22.py y
#   03_etapa2_L22.py, que no figuran en el repositorio; en esta entrega lo importan 01_entrenar_08_L22.py y los
#   scripts 02, 03 y 04 de la raíz. Enumera el contenido: parámetros fijos de LightGBM, configuración de la
#   búsqueda, entrenamiento por semilla y utilidades.
"""
comun_L22.py — funciones y parámetros compartidos por 02_etapa1_L22.py y 03_etapa2_L22.py (DMEyF, 1ra competencia).

No se ejecuta solo: lo importan los dos scripts de etapa. Debe estar en la misma carpeta que ellos (~/dmeyf).

Contenido:
  - parámetros fijos de LightGBM (los de z495 de Pasquini + feature_fraction_bynode de las recomendaciones),
  - configuración de la bayesiana (3 hiperparámetros, rangos de Pasquini, 10 trials aleatorios, semilla 878443),
  - bayesiana reproducible aunque se interrumpa (cada trial depende solo de su número y de los anteriores),
  - entrenamiento de N modelos con N semillas, reanudable (guarda cada predicción al terminar),
  - utilidades de carga, ganancia, respaldo al bucket.
"""
# [Anotación · líneas 13–28] Importa gc, json, os, shutil, subprocess, time, warnings, lightgbm, numpy,
#   optuna, pandas, pyarrow.parquet y roc_auc_score. Silencia un aviso de LightGBM sobre parámetros del Dataset
#   de referencia.
import gc
import json
import os
import shutil
import subprocess
import time
import warnings

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import pyarrow.parquet as pq
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore", message="Overriding the parameters from Reference Dataset")

# [Anotación · líneas 30–44] Define VOLUMEN = "L22", el bucket gs://luisdsuarez_buckito2026 y las 5 semillas
#   878443, 455471, 178447, 235397 y 409027. semillas_n(n) devuelve esas 5 seguidas de valores generados sumando
#   7919 de forma sucesiva a partir de 500009 (507928, 515847, …) hasta completar n, y verifica que no haya
#   repetidos ni el valor 42.
VOLUMEN = "L22"
BUCKET = "gs://luisdsuarez_buckito2026"
SEMILLAS = [878443, 455471, 178447, 235397, 409027]       # asignadas; nunca 42


def semillas_n(n):
    """Las 5 asignadas + adicionales deterministas (misma función que L13). Nunca 42."""
    extra, x = [], 500009
    while len(SEMILLAS) + len(extra) < n:
        x += 7919
        if x != 42 and x not in SEMILLAS:
            extra.append(x)
    out = (SEMILLAS + extra)[:n]
    assert 42 not in out and len(set(out)) == len(out)
    return out


# [Anotación · líneas 47–67] PARAMS_FIJOS: parámetros de LightGBM que no se buscan: boosting gbdt, objective
#   binary, metric auc, max_depth −1, lambda_l1 y lambda_l2 en 0, max_bin 31, bagging_fraction 1.0 (también la
#   de positivos y la de negativos), is_unbalance False, scale_pos_weight 1.0, min_data_in_leaf 0,
#   feature_fraction 0.50, feature_fraction_bynode 0.20, learning_rate 0.005, deterministic True. PARAMS_DATASET
#   repite max_bin 31, feature_pre_filter False y min_data_in_leaf 0 para construir el Dataset.
# ---------------------------------------------------------------------------
# Hiperparámetros FIJOS (z495 + feature_fraction_bynode). num_iterations, num_leaves y
# min_sum_hessian_in_leaf los pone la bayesiana. Sin early stopping, sin undersampling, sin pesos.
# ---------------------------------------------------------------------------
PARAMS_FIJOS = dict(
    boosting="gbdt", objective="binary", metric="auc",
    first_metric_only=False, boost_from_average=True, force_row_wise=True, deterministic=True,
    verbosity=-1,
    max_depth=-1, min_gain_to_split=0.0, lambda_l1=0.0, lambda_l2=0.0,
    max_bin=31,
    bagging_fraction=1.0, pos_bagging_fraction=1.0, neg_bagging_fraction=1.0,
    is_unbalance=False, scale_pos_weight=1.0,
    drop_rate=0.1, max_drop=50, skip_drop=0.5,
    extra_trees=False,
    min_data_in_leaf=0,
    feature_fraction=0.50,
    feature_fraction_bynode=0.20,
    learning_rate=0.005,
    feature_pre_filter=False,
)
PARAMS_DATASET = dict(max_bin=31, feature_pre_filter=False, min_data_in_leaf=0, verbosity=-1)

# [Anotación · líneas 69–83] CFG: rangos de la búsqueda (num_iterations 64 a 4096, num_leaves 16 a 2048,
#   min_sum_hessian_in_leaf 1e-6 a 0.1), 10 trials, n_startup_trials 12, semilla de la búsqueda 878443, 10
#   semillas para las etapas de L20, proporción 0.01251 para la clase artificial, ganancia de 1.072.500 por
#   BAJA+2 y costo de −27.500 por envío. VARS_PRESTAMOS y SUFIJOS listan las 2 variables de préstamos personales
#   y los 8 sufijos de sus variantes.
# Configuración (dict mutable para que --prueba pueda achicarla)
CFG = dict(
    espacio=dict(num_iterations=(64, 4096),               # rangos del script de Pasquini (lineales)
                 num_leaves=(16, 2048),
                 min_sum_hessian_in_leaf=(1e-6, 0.1)),
    n_trials=10,                                           # como Pasquini: 10 evaluaciones
    n_startup_trials=12,                                   # 4 x 3 hiperparámetros > 10 -> los 10 son aleatorios
    semilla_bo=SEMILLAS[0],
    n_semillas=10,
    prop_baja_artificial=0.01251,                          # tasa de BAJA en 03-04 (1,251 %)
    ganancia_baja2=1_072_500,
    costo=-27_500,
)
VARS_PRESTAMOS = ["cprestamos_personales", "mprestamos_personales"]
SUFIJOS = ("", "_lag1", "_delta1", "_lag2", "_delta2", "_tend3", "_avg3", "_zero")   # variantes de cada variable de préstamos


# [Anotación · líneas 86–93] modo_prueba() reduce la configuración para probar el código (num_iterations 8 a
#   24, num_leaves 4 a 16, 3 trials, 3 semillas). log() imprime con la hora adelante y vacía el búfer.
def modo_prueba():
    """SOLO para probar el código con datos chicos."""
    CFG.update(espacio=dict(num_iterations=(8, 24), num_leaves=(4, 16), min_sum_hessian_in_leaf=(1e-6, 0.1)),
               n_trials=3, n_startup_trials=2, n_semillas=3)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# [Anotación · líneas 96–119] sync() copia la carpeta del experimento al bucket con gsutil rsync (tiempo
#   máximo 900 s); si gsutil da una excepción sólo registra un aviso. guardar_atomico() escribe en un archivo
#   .tmp y lo renombra al nombre final. preparar() crea exp/<volumen>/codigo y copia allí los scripts que se le
#   pasan y este módulo.
def sync(dir_exp, volumen, activo):
    """Respaldo al bucket; nunca frena el experimento."""
    if not activo:
        return
    try:
        subprocess.run(["gsutil", "-q", "-m", "rsync", "-r", dir_exp, f"{BUCKET}/exp/{volumen}"],
                       check=False, timeout=900, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log("  (aviso: falló el sync al bucket:", e, ")")


def guardar_atomico(escribir, ruta):
    tmp = ruta + ".tmp"
    escribir(tmp)
    os.replace(tmp, ruta)


def preparar(volumen, dir_base, scripts):
    """Crea exp/<volumen>/codigo y deja copia de los scripts y de este módulo."""
    dir_exp = os.path.join(dir_base, "exp", volumen)
    os.makedirs(os.path.join(dir_exp, "codigo"), exist_ok=True)
    for f in list(scripts) + [__file__]:
        shutil.copy(os.path.abspath(f), os.path.join(dir_exp, "codigo"))
    return dir_exp


# [Anotación · líneas 122–141] cargar() lee del parquet sólo las filas de los meses pedidos y arma una matriz
#   float64 con todas las columnas cuyo nombre no empieza con "clase_" (numero_de_cliente y foto_mes quedan
#   dentro de la matriz). Devuelve un diccionario con la matriz, los nombres de columnas, los ids, el mes, la
#   clase binaria y la clase ternaria.
def cargar(ruta_pq, meses):
    """Lee solo los meses pedidos. Matriz de features en float64 (numero_de_cliente no entra en float32).
    Ninguna columna 'clase_*' entra a la matriz de features."""
    tabla = pq.read_table(ruta_pq, filters=[("foto_mes", "in", [int(m) for m in meses])])
    cols = [c for c in tabla.column_names if not c.startswith("clase_")]
    assert not any(c.startswith("clase") for c in cols)
    n = tabla.num_rows
    X = np.empty((n, len(cols)), dtype="float64")
    for j, c in enumerate(cols):
        X[:, j] = tabla[c].to_numpy()
    D = dict(X=X, cols=cols,
             ids=tabla["numero_de_cliente"].to_numpy().astype("int64"),
             mes=tabla["foto_mes"].to_numpy(),
             yb=tabla["clase_binaria"].to_numpy().astype("float64"),
             tern=np.array(tabla["clase_ternaria"].to_pylist(), dtype=object))
    del tabla
    gc.collect()
    log(f"  datos cargados: X={X.shape}, {X.nbytes / 1e9:.1f} GB; features = foto_mes, numero_de_cliente y el resto; "
        f"ninguna clase")
    return D


# [Anotación · líneas 144–156] idx_sin_prestamos() devuelve los índices de las columnas que quedan al quitar
#   cprestamos_personales, mprestamos_personales y sus variantes _lag1, _delta1, _lag2, _delta2, _tend3, _avg3 y
#   _zero (16 columnas), y verifica que las 16 existan. curva_ganancia() ordena por probabilidad descendente y
#   acumula 1.072.500 por cada BAJA+2 y −27.500 por cada uno de los demás.
def idx_sin_prestamos(cols):
    """Índices de las columnas SIN las 2 variables de préstamos personales y todas sus variantes: lag1, delta1, lag2, delta2, tend3, avg3 y _zero (16 columnas)."""
    excl = [b + s for b in VARS_PRESTAMOS for s in SUFIJOS]
    faltan = [x for x in excl if x not in cols]
    assert not faltan, f"columnas de préstamos que no están en el dataset: {faltan}"
    idx = np.array([j for j, c in enumerate(cols) if c not in set(excl)])
    return idx, [cols[j] for j in idx], excl


def curva_ganancia(prob, ternaria):
    """Ganancia acumulada al enviar los N de mayor probabilidad (N = 1..n)."""
    o = np.argsort(-prob, kind="stable")
    return np.cumsum(np.where(ternaria[o] == "BAJA+2", CFG["ganancia_baja2"], CFG["costo"]))


# [Anotación · líneas 159–162] entrenar() combina PARAMS_FIJOS con la semilla, num_leaves y
#   min_sum_hessian_in_leaf recibidos y entrena LightGBM con num_iterations rondas, sin detención temprana.
def entrenar(params_bo, semilla, ds):
    p = dict(PARAMS_FIJOS, seed=semilla, num_leaves=int(params_bo["num_leaves"]),
             min_sum_hessian_in_leaf=float(params_bo["min_sum_hessian_in_leaf"]))
    return lgb.train(p, ds, num_boost_round=int(params_bo["num_iterations"]))     # todos los árboles


# [Anotación · líneas 165–179] correr_bayesiana(), preparación: define las distribuciones de los 3
#   hiperparámetros (enteras para num_iterations y num_leaves, continua para min_sum_hessian_in_leaf) y lee del
#   archivo .jsonl los trials ya completos, si existe.
# ---------------------------------------------------------------------------
# Bayesiana reproducible aunque se interrumpa.
# El registro de trials completos vive en un .jsonl (una línea por trial). Para proponer el trial k se arma
# un estudio nuevo en memoria con los k trials ya completos, en orden, y un muestreador con semilla = semilla_bo + k.
# La propuesta depende solo de k y de los resultados anteriores, no de cuántas veces ni dónde se cortó.
# ---------------------------------------------------------------------------
def correr_bayesiana(dtr, X_va, y_va, ruta_jsonl, despues_de_trial=None, etiqueta=""):
    esp = CFG["espacio"]
    dists = dict(num_iterations=optuna.distributions.IntDistribution(*esp["num_iterations"]),
                 num_leaves=optuna.distributions.IntDistribution(*esp["num_leaves"]),
                 min_sum_hessian_in_leaf=optuna.distributions.FloatDistribution(*esp["min_sum_hessian_in_leaf"]))
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    hist = [json.loads(l) for l in open(ruta_jsonl)] if os.path.exists(ruta_jsonl) else []
    if hist:
        log(f"  {etiqueta} retomando: {len(hist)} trials ya completos")
# [Anotación · líneas 180–203] Bucle hasta completar 10 trials. Para el trial k crea un estudio de Optuna que
#   maximiza, con TPESampler de semilla 878443 + k y n_startup_trials 12, le carga los trials anteriores, pide
#   una propuesta, entrena con la semilla 878443 y calcula el AUC sobre la matriz de validación. Agrega el
#   resultado como una línea del .jsonl y llama a la función de respaldo.
    while len(hist) < CFG["n_trials"]:
        k = len(hist)
        semilla_trial = CFG["semilla_bo"] + k
        estudio = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(
            seed=semilla_trial, n_startup_trials=CFG["n_startup_trials"]))
        for h in hist:
            estudio.add_trial(optuna.trial.create_trial(params=h["params"], distributions=dists, value=h["auc"]))
        trial = estudio.ask()
        t0 = time.time()
        hp = dict(num_iterations=trial.suggest_int("num_iterations", *esp["num_iterations"]),
                  num_leaves=trial.suggest_int("num_leaves", *esp["num_leaves"]),
                  min_sum_hessian_in_leaf=trial.suggest_float("min_sum_hessian_in_leaf", *esp["min_sum_hessian_in_leaf"]))
        m = entrenar(hp, CFG["semilla_bo"], dtr)                  # la bayesiana usa la primera semilla
        auc = float(roc_auc_score(y_va, m.predict(X_va)))
        del m
        gc.collect()
        seg = round(time.time() - t0)
        log(f"  {etiqueta} trial {k:>2}: it={hp['num_iterations']:>4} hojas={hp['num_leaves']:>4} "
            f"hess={hp['min_sum_hessian_in_leaf']:.6f} -> AUC {auc:.5f}  ({seg}s, semilla del muestreador {semilla_trial})")
        hist.append(dict(trial=k, params=hp, auc=auc, segundos=seg, semilla_muestreador=semilla_trial))
        with open(ruta_jsonl, "a") as fh:
            fh.write(json.dumps(hist[-1]) + "\n")
        if despues_de_trial:
            despues_de_trial()
# [Anotación · líneas 204–209] Elige el trial de mayor AUC (ante empate, el primero) y devuelve el historial,
#   los tres hiperparámetros de ese trial y su registro.
    mejor = max(hist, key=lambda h: h["auc"])                      # ante empate, el primero
    mejores = dict(num_iterations=int(mejor["params"]["num_iterations"]),
                   num_leaves=int(mejor["params"]["num_leaves"]),
                   min_sum_hessian_in_leaf=float(mejor["params"]["min_sum_hessian_in_leaf"]))
    log(f"  {etiqueta} MEJORES hiperparámetros (trial {mejor['trial']}, AUC {mejor['auc']:.5f}): {mejores}")
    return hist, mejores, mejor


# [Anotación · líneas 212–233] entrenar_semillas(): para cada semilla que no tenga todas sus predicciones
#   guardadas entrena un modelo, predice cada matriz recibida, guarda <nombre>_<semilla>.npy y registra el AUC
#   cuando hay clase para esa matriz. Devuelve las predicciones leídas de disco, por matriz y por semilla.
def entrenar_semillas(dtr, mejores, semillas, matrices, y_eval, dir_p, despues=None):
    """Entrena un modelo por semilla sobre dtr y predice cada matriz de `matrices` (dict nombre -> X).
    Guarda <nombre>_<semilla>.npy al terminar cada semilla (reanudable). Devuelve {nombre: {semilla: prob}}."""
    os.makedirs(dir_p, exist_ok=True)
    ruta = lambda nom, sd: os.path.join(dir_p, f"{nom}_{sd}.npy")
    pend = [sd for sd in semillas if not all(os.path.exists(ruta(n, sd)) for n in matrices)]
    log(f"  {len(semillas)} semillas {semillas}; pendientes {len(pend)}")
    for sd in pend:
        t = time.time()
        m = entrenar(mejores, sd, dtr)
        msg = []
        for nom, X in matrices.items():
            pr = m.predict(X).astype("float64")
            guardar_atomico(lambda r: np.save(open(r, "wb"), pr), ruta(nom, sd))
            if nom in y_eval:
                msg.append(f"AUC {nom} {roc_auc_score(y_eval[nom], pr):.5f}")
        log(f"  semilla {sd}: {', '.join(msg)}  ({time.time() - t:.0f}s)")
        del m
        gc.collect()
        if despues:
            despues()
    return {nom: {sd: np.load(ruta(nom, sd)) for sd in semillas} for nom in matrices}


# [Anotación · líneas 236–242] tabla_predicciones() arma un DataFrame con numero_de_cliente, foto_mes, las dos
#   clases, una columna prob_<semilla> por modelo y prob_ens, el promedio de esas columnas.
def tabla_predicciones(ids, mes, tern, yb, P):
    """DataFrame con identificación, clase real, una columna prob_<semilla> por semilla y prob_ens (promedio simple)."""
    out = pd.DataFrame(dict(numero_de_cliente=ids, foto_mes=mes, clase_ternaria=tern, clase_binaria=yb.astype("float32")))
    for sd, pr in P.items():
        out[f"prob_{sd}"] = pr
    out["prob_ens"] = out[[f"prob_{sd}" for sd in P]].mean(axis=1)
    return out


# [Anotación · líneas 245–263] resumen_mes() calcula el AUC de cada semilla y del promedio y lo guarda en
#   <prefijo>_auc.csv. Calcula la ganancia acumulada para envíos de 1.000 a 30.000 de a 100, por semilla, su
#   media y la del promedio de probabilidades, la guarda en <prefijo>_ganancia.csv y registra el máximo de las
#   dos últimas.
def resumen_mes(P, y_real, tern, prefijo, etiqueta):
    """AUC por semilla y del ensamble, y curva de ganancia (por semilla, media y ensamble) en un mes con clase real."""
    semillas = list(P)
    ens = np.mean([P[s] for s in semillas], axis=0)
    aucs = {s: float(roc_auc_score(y_real, P[s])) for s in semillas}
    auc_ens = float(roc_auc_score(y_real, ens))
    pd.DataFrame(dict(semilla=semillas + ["ensamble"], auc=list(aucs.values()) + [auc_ens])
                 ).to_csv(f"{prefijo}_auc.csv", index=False)
    log(f"  {etiqueta}: AUC media de semillas {np.mean(list(aucs.values())):.5f} "
        f"(sd {np.std(list(aucs.values()), ddof=1):.5f}), ensamble {auc_ens:.5f}")
    envios = np.arange(1000, min(30000, len(tern)) + 1, 100)
    tab = pd.DataFrame(dict(envios=envios, **{f"g_{s}": curva_ganancia(P[s], tern)[envios - 1] for s in semillas}))
    tab["g_media"] = tab[[f"g_{s}" for s in semillas]].mean(axis=1)
    tab["g_ens"] = curva_ganancia(ens, tern)[envios - 1]
    tab.to_csv(f"{prefijo}_ganancia.csv", index=False)
    for nombre in ("g_media", "g_ens"):
        k = int(tab[nombre].idxmax())
        log(f"  {etiqueta} {nombre}: máximo {tab[nombre][k] / 1e6:,.1f} M con {int(tab['envios'][k]):,} envíos "
            f"(mirar la curva suavizada, no solo el pico)")


# [Anotación · líneas 266–295] ensamblar_08(): lee ids_08.npy de la carpeta del volumen y de cada carpeta
#   adicional y exige que sean iguales. Recorre la lista ordenada de semillas, toma los
#   pred_08/prob_<semilla>.npy que existen (una semilla no puede estar en dos carpetas), se queda con los
#   primeros n si se pide, y calcula prob_ens como el promedio por fila de las probabilidades de esos modelos.
# ---------------------------------------------------------------------------
# Ensamble de las predicciones sobre 08 disponibles hasta el momento (se puede llamar en cualquier momento).
# ---------------------------------------------------------------------------
def ensamblar_08(dir_exp, volumen, semillas_orden, n=None, top=11000, guardar=True, otros_dirs=()):
    """Promedia las probabilidades guardadas en pred_08/prob_<semilla>.npy (en el orden de semillas_orden).
    otros_dirs: carpetas exp/<otro volumen> con más predicciones de las mismas características (mismo 08, mismo orden de
    clientes); no puede haber semillas repetidas entre carpetas. n: usar solo los primeros n modelos (None = todos)."""
    dirs = [dir_exp] + list(otros_dirs)
    ids = np.load(os.path.join(dir_exp, "ids_08.npy"))
    ruta_de = {}
    for d in dirs:
        ids_d = np.load(os.path.join(d, "ids_08.npy"))
        assert np.array_equal(ids_d, ids), f"{d}: ids_08.npy distinto: no son los mismos clientes de 08 en el mismo orden"
        dir_p = os.path.join(d, "pred_08")
        for sd in semillas_orden:
            f = os.path.join(dir_p, f"prob_{sd}.npy")
            if os.path.exists(f):
                assert sd not in ruta_de, f"la semilla {sd} está en dos carpetas ({ruta_de[sd]} y {f}): rangos de semillas superpuestos"
                ruta_de[sd] = f
    usadas = [sd for sd in semillas_orden if sd in ruta_de]
    if n:
        usadas = usadas[:n]
    if not usadas:
        raise SystemExit(f"No hay predicciones en {[os.path.join(d, 'pred_08') for d in dirs]}")
    P = np.column_stack([np.load(ruta_de[sd]) for sd in usadas])
    assert P.shape[0] == len(ids), "las predicciones no tienen la misma cantidad de clientes que ids_08.npy"
    ens = P.mean(axis=1)
    out = pd.DataFrame(dict(numero_de_cliente=ids, prob_ens=ens))
    log(f"  ensamble de {len(usadas)} modelos sobre {len(ids):,} clientes de 08"
        + (f" (carpetas: {', '.join(os.path.basename(d) for d in dirs)})" if len(dirs) > 1 else ""))
# [Anotación · líneas 296–303] Con 4 modelos o más, para k en 2, 5, 10, 20, 40, 80, 160 y 320 (los menores a
#   la cantidad de modelos) registra qué proporción de los primeros `top` clientes (11.000 por defecto) del
#   promedio de los primeros k modelos coincide con los del promedio de todos.
    # estabilidad: cuánto del top-N del ensamble completo ya está en el top-N del ensamble de los primeros k modelos
    if len(usadas) >= 4:
        top = min(top, len(ids))
        topN = set(np.argsort(-ens, kind="stable")[:top])
        ks = sorted({k for k in (2, 5, 10, 20, 40, 80, 160, 320) if k < len(usadas)})
        for k in ks:
            tk = set(np.argsort(-P[:, :k].mean(axis=1), kind="stable")[:top])
            log(f"  top {top:,}: con {k:>3} modelos coincide el {len(tk & topN) / top:.1%} con el ensamble de {len(usadas)}")
# [Anotación · líneas 304–309] Si guardar es verdadero escribe <etiqueta>_pred_08_ens_<n>modelos.parquet con
#   numero_de_cliente y prob_ens; la etiqueta une con "+" los nombres de las carpetas usadas. Devuelve la tabla
#   y la lista de semillas usadas.
    if guardar:
        etiqueta = "+".join(os.path.basename(d) for d in dirs) if len(dirs) > 1 else volumen
        ruta_out = os.path.join(dir_exp, f"{etiqueta}_pred_08_ens_{len(usadas)}modelos.parquet")
        guardar_atomico(lambda r: out.to_parquet(r, index=False), ruta_out)
        log(f"  guardado: {ruta_out}")
    return out, usadas
```

### L22/codigo/01_entrenar_08_L22.py

Entrenamiento final: con los hiperparámetros de L20 entrena un modelo LightGBM por semilla con 202103 a 202106 y todas las columnas, y guarda la probabilidad de cada modelo sobre 202108 en un archivo .npy por semilla; al final llama al ensamble.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–27] Docstring: entrenamiento final con 202103 a 202106 para predecir 202108, con los
#   hiperparámetros de la etapa 1 de L20 y todas las columnas. Explica que se puede interrumpir y retomar, cómo
#   repartir rangos de semillas entre dos máquinas (volúmenes L22 y L22b) y qué archivos deja en exp/<volumen>/.
"""
01_entrenar_08_L22.py — DMEyF, 1ra competencia, L22: entrenamiento FINAL con 03, 04, 05 y 06 reales para predecir 08.

Usa el dataset y los hiperparámetros de L20 (etapa 1, clase real). No hay bayesiana ni clase artificial.
Entrena MUCHOS modelos, uno por semilla, con TODAS las columnas (incluidas las variables de préstamos, que se
excluyeron solo para evaluar en 06), y guarda la predicción sobre 08 de cada modelo apenas termina.

SE PUEDE INTERRUMPIR EN CUALQUIER MOMENTO (kill o corte de la VM): cada predicción se guarda de forma atómica y al
relanzar el mismo comando se retoma con la primera semilla que falte. Solo se pierde el modelo en curso.
Para ensamblar lo disponible en cualquier momento (también mientras sigue corriendo este script):
    python 02_ensamblar_08_L22.py

VARIAS VM EN PARALELO: cada VM debe usar un rango de semillas distinto y su propio --volumen, por ejemplo
    VM 1:  bash correr_L22.sh                                          (semillas 0 a 199, volumen L22)
    VM 2:  bash correr_L22.sh --volumen L22b --desde 200               (semillas 200 a 399, volumen L22b)
Después se ensamblan juntas: python 02_ensamblar_08_L22.py --otros L22b

Uso (desde ~/dmeyf):
    nohup bash correr_L22.sh > /dev/null 2>&1 &         # recomendado
    # o directamente: nohup python 01_entrenar_08_L22.py > L22_modelos.log 2>&1 &

Salidas en ~/dmeyf/exp/L22/ (y copia en gs://luisdsuarez_buckito2026/exp/L22/):
    hiperparametros_origen.json    copia de los hiperparámetros de L20 que se usaron
    config.json, ids_08.npy        (orden de los clientes de 08 al que corresponden todas las predicciones)
    pred_08/prob_<semilla>.npy     probabilidad de BAJA para los clientes de 08, un archivo por modelo
    L22_pred_08_ens_<n>modelos.parquet   ensamble (numero_de_cliente, prob_ens), lo genera 02_ensamblar_08_L22.py
"""
# [Anotación · líneas 28–43] Importa argparse, json, os, shutil, time, lightgbm, numpy, pandas y el módulo
#   comun_L22. Define MESES_TRAIN = 202103, 202104, 202105 y 202106, MES_PRED = 202108 y MAX_SEMILLAS = 1000.
import argparse
import json
import os
import shutil
import time

import lightgbm as lgb
import numpy as np
import pandas as pd

import comun_L22 as cm
from comun_L22 import log

MESES_TRAIN = [202103, 202104, 202105, 202106]
MES_PRED = 202108
MAX_SEMILLAS = 1000                 # lista ordenada de semillas; el script se detiene al llegar a --n_semillas


# [Anotación · líneas 46–62] Argumentos: --volumen (L22 por defecto), --dir_base (~/dmeyf), --dataset,
#   --hiperparametros, --n_semillas (200 por defecto), --desde (posición inicial en la lista de semillas, 0 por
#   defecto) y --sin_bucket. Arma las rutas del parquet y del JSON de hiperparámetros de L20, crea la carpeta
#   del experimento con la copia del código y define la función de respaldo al bucket.
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volumen", default=cm.VOLUMEN)
    ap.add_argument("--dir_base", default=os.path.expanduser("~/dmeyf"))
    ap.add_argument("--dataset", default=None, help="por defecto ~/dmeyf/datasets/L20_dataset.parquet")
    ap.add_argument("--hiperparametros", default=None, help="por defecto ~/dmeyf/exp/L20/L20_e1_hiperparametros.json")
    ap.add_argument("--n_semillas", type=int, default=200, help="cantidad de semillas de este rango (tope de modelos; se puede interrumpir antes)")
    ap.add_argument("--desde", type=int, default=0,
                    help="posición inicial en la lista ordenada de semillas. Este rango usa las posiciones [desde, desde + n_semillas). "
                         "Para una segunda VM: --desde 200 (con el tope por defecto de 200 de la primera) y otro --volumen")
    ap.add_argument("--sin_bucket", action="store_true")
    a = ap.parse_args()

    ruta_pq = a.dataset or os.path.join(a.dir_base, "datasets", "L20_dataset.parquet")
    ruta_hp = a.hiperparametros or os.path.join(a.dir_base, "exp", "L20", "L20_e1_hiperparametros.json")
    dir_exp = cm.preparar(a.volumen, a.dir_base, [__file__])
    sync = lambda: cm.sync(dir_exp, a.volumen, not a.sin_bucket)

# [Anotación · líneas 64–76] Lee mejores_hiperparametros del JSON y verifica que tenga exactamente
#   num_iterations, num_leaves y min_sum_hessian_in_leaf; copia ese JSON como hiperparametros_origen.json. Toma
#   de la lista de 1000 semillas las posiciones [desde, desde + n_semillas) y escribe config.json con rutas,
#   hiperparámetros, meses, rango de semillas, las primeras 25 semillas y las versiones de lightgbm y pandas.
    with open(ruta_hp) as fh:
        mejores = json.load(fh)["mejores_hiperparametros"]
    assert set(mejores) == {"num_iterations", "num_leaves", "min_sum_hessian_in_leaf"}, mejores
    shutil.copy(ruta_hp, os.path.join(dir_exp, "hiperparametros_origen.json"))
    assert a.desde >= 0 and a.desde + a.n_semillas <= MAX_SEMILLAS, f"el rango debe caber en las {MAX_SEMILLAS} semillas disponibles"
    semillas = cm.semillas_n(MAX_SEMILLAS)[a.desde:a.desde + a.n_semillas]
    with open(os.path.join(dir_exp, "config.json"), "w") as fh:
        json.dump(dict(dataset=ruta_pq, hiperparametros=ruta_hp, mejores_hiperparametros=mejores,
                       params_fijos=cm.PARAMS_FIJOS, meses_entrenamiento=MESES_TRAIN, mes_prediccion=MES_PRED,
                       rango_semillas=dict(desde=a.desde, hasta_sin_incluir=a.desde + a.n_semillas,
                                           primera=semillas[0], ultima=semillas[-1]),
                       primeras_semillas=semillas[:25], n_semillas_tope=a.n_semillas,
                       versiones=dict(lightgbm=lgb.__version__, pandas=pd.__version__)), fh, indent=1)
# [Anotación · líneas 77–86] Carga del parquet los meses de entrenamiento y 202108, arma las máscaras de filas
#   de entrenamiento y de predicción y verifica que no falte la clase binaria en entrenamiento. Registra
#   cantidad de filas, proporción de positivos y cantidad de columnas.
    log(f"=== {a.volumen}: hiperparámetros de {ruta_hp}: {mejores}")
    log(f"=== semillas: posiciones {a.desde} a {a.desde + a.n_semillas - 1} de la lista fija (de {semillas[0]} a {semillas[-1]})")
    log(f"=== cargando meses {MESES_TRAIN + [MES_PRED]} de {ruta_pq}")
    D = cm.cargar(ruta_pq, MESES_TRAIN + [MES_PRED])
    X, mes, yb, cols = D["X"], D["mes"], D["yb"], D["cols"]
    tr, fut = np.isin(mes, MESES_TRAIN), mes == MES_PRED
    assert not np.isnan(yb[tr]).any(), "faltan clases reales en los meses de entrenamiento"
    assert fut.sum() > 0
    log(f"  entrenamiento: {tr.sum():,} filas, {yb[tr].mean():.3%} positivos, {len(cols)} features (TODAS, con préstamos) "
        f"| a predecir: {fut.sum():,} clientes de {MES_PRED}")

# [Anotación · líneas 88–93] Guarda en ids_08.npy los numero_de_cliente de 202108 en el orden de las
#   predicciones; si el archivo ya existe exige que coincida con los ids cargados.
    # los clientes de 08, en el orden al que corresponden todas las predicciones; protege contra mezclar corridas
    ruta_ids = os.path.join(dir_exp, "ids_08.npy")
    if os.path.exists(ruta_ids):
        assert np.array_equal(np.load(ruta_ids), D["ids"][fut]), "ids_08.npy no coincide: ¿otro dataset? No mezclar corridas"
    else:
        cm.guardar_atomico(lambda r: np.save(open(r, "wb"), D["ids"][fut]), ruta_ids)

# [Anotación · líneas 95–99] Arma la lista de semillas del rango que todavía no tienen
#   pred_08/prob_<semilla>.npy.
    dir_p = os.path.join(dir_exp, "pred_08")
    os.makedirs(dir_p, exist_ok=True)
    ruta = lambda sd: os.path.join(dir_p, f"prob_{sd}.npy")
    pend = [sd for sd in semillas if not os.path.exists(ruta(sd))]
    log(f"  modelos ya guardados: {len(semillas) - len(pend)} | pendientes hasta el tope de {len(semillas)}: {len(pend)}")
# [Anotación · líneas 100–114] Si hay semillas pendientes construye el Dataset de LightGBM con las filas de
#   entrenamiento y todas las columnas, y para cada semilla entrena un modelo, predice 202108, guarda las
#   probabilidades en prob_<semilla>.npy, libera el modelo, registra el tiempo y respalda al bucket.
    if pend:
        dtr = lgb.Dataset(X[tr], yb[tr], feature_name=cols, params=cm.PARAMS_DATASET).construct()
        X08 = X[fut]
        del X, D["X"]
        hechos, t_ini = len(semillas) - len(pend), time.time()
        for i, sd in enumerate(pend, 1):
            t = time.time()
            m = cm.entrenar(mejores, sd, dtr)
            pr = m.predict(X08).astype("float64")
            cm.guardar_atomico(lambda r: np.save(open(r, "wb"), pr), ruta(sd))
            del m
            cm.gc.collect()
            log(f"  modelo {hechos + i} (semilla {sd}): {time.time() - t:.0f}s | en esta corrida: {i} modelos, "
                f"{(time.time() - t_ini) / i / 60:.1f} min por modelo")
            sync()
# [Anotación · líneas 115–118] Al terminar el rango llama a ensamblar_08 con las predicciones del volumen y
#   respalda al bucket.
    log("tope de modelos alcanzado; ensamblando")
    cm.ensamblar_08(dir_exp, a.volumen, cm.semillas_n(MAX_SEMILLAS))
    sync()
    log("listo")


# [Anotación · líneas 121–122] Punto de entrada del script: ejecuta main().
if __name__ == "__main__":
    main()
```

### L22/codigo/correr_L22.sh

Script de shell que lanza 01_entrenar_08_L22.py con los argumentos recibidos, con candado contra corridas simultáneas, log por volumen, respaldo al bucket y apagado opcional de la máquina.

```
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Comentarios de uso: comandos para la primera máquina (semillas 0 a 199, volumen
#   L22) y la segunda (--volumen L22b --desde 200), opción --apagar, cómo seguir el log y cómo interrumpir y
#   retomar.
#!/bin/bash
# correr_L22.sh — entrena modelos con 03-06 (una semilla tras otra) y guarda la predicción de 08 de cada uno.
#
# Uso (desde ~/dmeyf, con 01_entrenar_08_L22.py y comun_L22.py en la misma carpeta):
#     nohup bash correr_L22.sh > /dev/null 2>&1 &                                  # VM 1: semillas 0 a 199, volumen L22
#     nohup bash correr_L22.sh --volumen L22b --desde 200 > /dev/null 2>&1 &       # VM 2: semillas 200 a 399, volumen L22b
# Opciones: cualquier argumento de 01_entrenar_08_L22.py (--volumen, --desde, --n_semillas, --dataset, --hiperparametros)
#           y --apagar (apaga la VM al terminar; necesita sudo).
#
# Seguimiento (devuelve el prompt):   tail -n 30 <volumen>_todo.log     (L22_todo.log o L22b_todo.log)
# Se puede interrumpir cuando quieras (pkill -f 01_entrenar_08_L22.py): lo ya guardado queda, y se puede
# ensamblar con: python 02_ensamblar_08_L22.py
# Es reanudable: si la VM spot se corta, encenderla y relanzar el mismo comando.
# [Anotación · líneas 14–28] Se ubica en la carpeta del script, separa --apagar y --volumen del resto de los
#   argumentos, define el bucket y redirige toda la salida a <volumen>_todo.log.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
VOL=L22
APAGAR=0
ARGS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --apagar)  APAGAR=1 ;;
        --volumen) VOL="$2"; ARGS+=("$1" "$2"); shift ;;
        *)         ARGS+=("$1") ;;
    esac
    shift
done
BUCKET=gs://luisdsuarez_buckito2026
LOG=${VOL}_todo.log
exec >> "$LOG" 2>&1                       # todo lo que sigue va al log

# [Anotación · líneas 30–41] Toma un candado con flock sobre /tmp/correr_dmeyf.lock y termina si ya hay una
#   corrida en esa máquina; también termina si pgrep encuentra en ejecución algún script python con nombre 01_,
#   02_ o 03_ de algún volumen.
# Candado: impide lanzar una segunda corrida mientras la primera sigue viva EN ESTA VM
# (dos procesos de LightGBM se pisan los núcleos y la RAM, y todo se vuelve lentísimo).
exec 9> /tmp/correr_dmeyf.lock
if ! flock -n 9; then
    echo "$(date '+%F %T') YA HAY UNA CORRIDA EN CURSO: esta se cancela"
    exit 1
fi
# además: no arrancar si quedó algún script de CUALQUIER volumen todavía vivo
if pgrep -f "^([^ ]*/)?python[0-9.]* +(\./)?0[123]_[a-z0-9_]*_L[0-9]+[a-z]?\.py" > /dev/null; then
    echo "$(date '+%F %T') HAY OTRO SCRIPT DE UN VOLUMEN ANTERIOR TODAVÍA CORRIENDO: esta corrida se cancela"
    exit 1
fi

# [Anotación · líneas 43–49] Copia el propio script a exp/<volumen>/codigo, ejecuta 01_entrenar_08_L22.py con
#   los argumentos recibidos y registra el código de salida.
mkdir -p exp/$VOL/codigo
cp "$(readlink -f "$0")" exp/$VOL/codigo/        # copia del código para reproducibilidad

echo "$(date '+%F %T') === inicio: volumen $VOL, argumentos: ${ARGS[*]} (apagar al final: $APAGAR)"
python 01_entrenar_08_L22.py "${ARGS[@]}"
RC=$?
echo "$(date '+%F %T') === fin (código $RC)"

# [Anotación · líneas 51–58] Copia el log a la carpeta del experimento, sincroniza la carpeta con el bucket y,
#   si se pasó --apagar, apaga la máquina con shutdown.
# respaldo del log junto al experimento
cp "$LOG" exp/$VOL/
gsutil -q -m rsync -r exp/$VOL "$BUCKET/exp/$VOL"

if [ $APAGAR -eq 1 ]; then
    echo "$(date '+%F %T') apagando la VM"
    sudo shutdown -h now
fi
```

### L22/codigo/comun_L22.py

Módulo compartido de L22: mismo contenido que comun_L20.py con VOLUMEN = "L22" más la función ensamblar_08, que promedia las probabilidades guardadas por semilla.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Docstring del módulo. Nombra como scripts que lo importan a 02_etapa1_L22.py y
#   03_etapa2_L22.py, que no figuran en el repositorio; en esta entrega lo importan 01_entrenar_08_L22.py y los
#   scripts 02, 03 y 04 de la raíz. Enumera el contenido: parámetros fijos de LightGBM, configuración de la
#   búsqueda, entrenamiento por semilla y utilidades.
"""
comun_L22.py — funciones y parámetros compartidos por 02_etapa1_L22.py y 03_etapa2_L22.py (DMEyF, 1ra competencia).

No se ejecuta solo: lo importan los dos scripts de etapa. Debe estar en la misma carpeta que ellos (~/dmeyf).

Contenido:
  - parámetros fijos de LightGBM (los de z495 de Pasquini + feature_fraction_bynode de las recomendaciones),
  - configuración de la bayesiana (3 hiperparámetros, rangos de Pasquini, 10 trials aleatorios, semilla 878443),
  - bayesiana reproducible aunque se interrumpa (cada trial depende solo de su número y de los anteriores),
  - entrenamiento de N modelos con N semillas, reanudable (guarda cada predicción al terminar),
  - utilidades de carga, ganancia, respaldo al bucket.
"""
# [Anotación · líneas 13–28] Importa gc, json, os, shutil, subprocess, time, warnings, lightgbm, numpy,
#   optuna, pandas, pyarrow.parquet y roc_auc_score. Silencia un aviso de LightGBM sobre parámetros del Dataset
#   de referencia.
import gc
import json
import os
import shutil
import subprocess
import time
import warnings

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import pyarrow.parquet as pq
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore", message="Overriding the parameters from Reference Dataset")

# [Anotación · líneas 30–44] Define VOLUMEN = "L22", el bucket gs://luisdsuarez_buckito2026 y las 5 semillas
#   878443, 455471, 178447, 235397 y 409027. semillas_n(n) devuelve esas 5 seguidas de valores generados sumando
#   7919 de forma sucesiva a partir de 500009 (507928, 515847, …) hasta completar n, y verifica que no haya
#   repetidos ni el valor 42.
VOLUMEN = "L22"
BUCKET = "gs://luisdsuarez_buckito2026"
SEMILLAS = [878443, 455471, 178447, 235397, 409027]       # asignadas; nunca 42


def semillas_n(n):
    """Las 5 asignadas + adicionales deterministas (misma función que L13). Nunca 42."""
    extra, x = [], 500009
    while len(SEMILLAS) + len(extra) < n:
        x += 7919
        if x != 42 and x not in SEMILLAS:
            extra.append(x)
    out = (SEMILLAS + extra)[:n]
    assert 42 not in out and len(set(out)) == len(out)
    return out


# [Anotación · líneas 47–67] PARAMS_FIJOS: parámetros de LightGBM que no se buscan: boosting gbdt, objective
#   binary, metric auc, max_depth −1, lambda_l1 y lambda_l2 en 0, max_bin 31, bagging_fraction 1.0 (también la
#   de positivos y la de negativos), is_unbalance False, scale_pos_weight 1.0, min_data_in_leaf 0,
#   feature_fraction 0.50, feature_fraction_bynode 0.20, learning_rate 0.005, deterministic True. PARAMS_DATASET
#   repite max_bin 31, feature_pre_filter False y min_data_in_leaf 0 para construir el Dataset.
# ---------------------------------------------------------------------------
# Hiperparámetros FIJOS (z495 + feature_fraction_bynode). num_iterations, num_leaves y
# min_sum_hessian_in_leaf los pone la bayesiana. Sin early stopping, sin undersampling, sin pesos.
# ---------------------------------------------------------------------------
PARAMS_FIJOS = dict(
    boosting="gbdt", objective="binary", metric="auc",
    first_metric_only=False, boost_from_average=True, force_row_wise=True, deterministic=True,
    verbosity=-1,
    max_depth=-1, min_gain_to_split=0.0, lambda_l1=0.0, lambda_l2=0.0,
    max_bin=31,
    bagging_fraction=1.0, pos_bagging_fraction=1.0, neg_bagging_fraction=1.0,
    is_unbalance=False, scale_pos_weight=1.0,
    drop_rate=0.1, max_drop=50, skip_drop=0.5,
    extra_trees=False,
    min_data_in_leaf=0,
    feature_fraction=0.50,
    feature_fraction_bynode=0.20,
    learning_rate=0.005,
    feature_pre_filter=False,
)
PARAMS_DATASET = dict(max_bin=31, feature_pre_filter=False, min_data_in_leaf=0, verbosity=-1)

# [Anotación · líneas 69–83] CFG: rangos de la búsqueda (num_iterations 64 a 4096, num_leaves 16 a 2048,
#   min_sum_hessian_in_leaf 1e-6 a 0.1), 10 trials, n_startup_trials 12, semilla de la búsqueda 878443, 10
#   semillas para las etapas de L20, proporción 0.01251 para la clase artificial, ganancia de 1.072.500 por
#   BAJA+2 y costo de −27.500 por envío. VARS_PRESTAMOS y SUFIJOS listan las 2 variables de préstamos personales
#   y los 8 sufijos de sus variantes.
# Configuración (dict mutable para que --prueba pueda achicarla)
CFG = dict(
    espacio=dict(num_iterations=(64, 4096),               # rangos del script de Pasquini (lineales)
                 num_leaves=(16, 2048),
                 min_sum_hessian_in_leaf=(1e-6, 0.1)),
    n_trials=10,                                           # como Pasquini: 10 evaluaciones
    n_startup_trials=12,                                   # 4 x 3 hiperparámetros > 10 -> los 10 son aleatorios
    semilla_bo=SEMILLAS[0],
    n_semillas=10,
    prop_baja_artificial=0.01251,                          # tasa de BAJA en 03-04 (1,251 %)
    ganancia_baja2=1_072_500,
    costo=-27_500,
)
VARS_PRESTAMOS = ["cprestamos_personales", "mprestamos_personales"]
SUFIJOS = ("", "_lag1", "_delta1", "_lag2", "_delta2", "_tend3", "_avg3", "_zero")   # variantes de cada variable de préstamos


# [Anotación · líneas 86–93] modo_prueba() reduce la configuración para probar el código (num_iterations 8 a
#   24, num_leaves 4 a 16, 3 trials, 3 semillas). log() imprime con la hora adelante y vacía el búfer.
def modo_prueba():
    """SOLO para probar el código con datos chicos."""
    CFG.update(espacio=dict(num_iterations=(8, 24), num_leaves=(4, 16), min_sum_hessian_in_leaf=(1e-6, 0.1)),
               n_trials=3, n_startup_trials=2, n_semillas=3)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# [Anotación · líneas 96–119] sync() copia la carpeta del experimento al bucket con gsutil rsync (tiempo
#   máximo 900 s); si gsutil da una excepción sólo registra un aviso. guardar_atomico() escribe en un archivo
#   .tmp y lo renombra al nombre final. preparar() crea exp/<volumen>/codigo y copia allí los scripts que se le
#   pasan y este módulo.
def sync(dir_exp, volumen, activo):
    """Respaldo al bucket; nunca frena el experimento."""
    if not activo:
        return
    try:
        subprocess.run(["gsutil", "-q", "-m", "rsync", "-r", dir_exp, f"{BUCKET}/exp/{volumen}"],
                       check=False, timeout=900, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log("  (aviso: falló el sync al bucket:", e, ")")


def guardar_atomico(escribir, ruta):
    tmp = ruta + ".tmp"
    escribir(tmp)
    os.replace(tmp, ruta)


def preparar(volumen, dir_base, scripts):
    """Crea exp/<volumen>/codigo y deja copia de los scripts y de este módulo."""
    dir_exp = os.path.join(dir_base, "exp", volumen)
    os.makedirs(os.path.join(dir_exp, "codigo"), exist_ok=True)
    for f in list(scripts) + [__file__]:
        shutil.copy(os.path.abspath(f), os.path.join(dir_exp, "codigo"))
    return dir_exp


# [Anotación · líneas 122–141] cargar() lee del parquet sólo las filas de los meses pedidos y arma una matriz
#   float64 con todas las columnas cuyo nombre no empieza con "clase_" (numero_de_cliente y foto_mes quedan
#   dentro de la matriz). Devuelve un diccionario con la matriz, los nombres de columnas, los ids, el mes, la
#   clase binaria y la clase ternaria.
def cargar(ruta_pq, meses):
    """Lee solo los meses pedidos. Matriz de features en float64 (numero_de_cliente no entra en float32).
    Ninguna columna 'clase_*' entra a la matriz de features."""
    tabla = pq.read_table(ruta_pq, filters=[("foto_mes", "in", [int(m) for m in meses])])
    cols = [c for c in tabla.column_names if not c.startswith("clase_")]
    assert not any(c.startswith("clase") for c in cols)
    n = tabla.num_rows
    X = np.empty((n, len(cols)), dtype="float64")
    for j, c in enumerate(cols):
        X[:, j] = tabla[c].to_numpy()
    D = dict(X=X, cols=cols,
             ids=tabla["numero_de_cliente"].to_numpy().astype("int64"),
             mes=tabla["foto_mes"].to_numpy(),
             yb=tabla["clase_binaria"].to_numpy().astype("float64"),
             tern=np.array(tabla["clase_ternaria"].to_pylist(), dtype=object))
    del tabla
    gc.collect()
    log(f"  datos cargados: X={X.shape}, {X.nbytes / 1e9:.1f} GB; features = foto_mes, numero_de_cliente y el resto; "
        f"ninguna clase")
    return D


# [Anotación · líneas 144–156] idx_sin_prestamos() devuelve los índices de las columnas que quedan al quitar
#   cprestamos_personales, mprestamos_personales y sus variantes _lag1, _delta1, _lag2, _delta2, _tend3, _avg3 y
#   _zero (16 columnas), y verifica que las 16 existan. curva_ganancia() ordena por probabilidad descendente y
#   acumula 1.072.500 por cada BAJA+2 y −27.500 por cada uno de los demás.
def idx_sin_prestamos(cols):
    """Índices de las columnas SIN las 2 variables de préstamos personales y todas sus variantes: lag1, delta1, lag2, delta2, tend3, avg3 y _zero (16 columnas)."""
    excl = [b + s for b in VARS_PRESTAMOS for s in SUFIJOS]
    faltan = [x for x in excl if x not in cols]
    assert not faltan, f"columnas de préstamos que no están en el dataset: {faltan}"
    idx = np.array([j for j, c in enumerate(cols) if c not in set(excl)])
    return idx, [cols[j] for j in idx], excl


def curva_ganancia(prob, ternaria):
    """Ganancia acumulada al enviar los N de mayor probabilidad (N = 1..n)."""
    o = np.argsort(-prob, kind="stable")
    return np.cumsum(np.where(ternaria[o] == "BAJA+2", CFG["ganancia_baja2"], CFG["costo"]))


# [Anotación · líneas 159–162] entrenar() combina PARAMS_FIJOS con la semilla, num_leaves y
#   min_sum_hessian_in_leaf recibidos y entrena LightGBM con num_iterations rondas, sin detención temprana.
def entrenar(params_bo, semilla, ds):
    p = dict(PARAMS_FIJOS, seed=semilla, num_leaves=int(params_bo["num_leaves"]),
             min_sum_hessian_in_leaf=float(params_bo["min_sum_hessian_in_leaf"]))
    return lgb.train(p, ds, num_boost_round=int(params_bo["num_iterations"]))     # todos los árboles


# [Anotación · líneas 165–179] correr_bayesiana(), preparación: define las distribuciones de los 3
#   hiperparámetros (enteras para num_iterations y num_leaves, continua para min_sum_hessian_in_leaf) y lee del
#   archivo .jsonl los trials ya completos, si existe.
# ---------------------------------------------------------------------------
# Bayesiana reproducible aunque se interrumpa.
# El registro de trials completos vive en un .jsonl (una línea por trial). Para proponer el trial k se arma
# un estudio nuevo en memoria con los k trials ya completos, en orden, y un muestreador con semilla = semilla_bo + k.
# La propuesta depende solo de k y de los resultados anteriores, no de cuántas veces ni dónde se cortó.
# ---------------------------------------------------------------------------
def correr_bayesiana(dtr, X_va, y_va, ruta_jsonl, despues_de_trial=None, etiqueta=""):
    esp = CFG["espacio"]
    dists = dict(num_iterations=optuna.distributions.IntDistribution(*esp["num_iterations"]),
                 num_leaves=optuna.distributions.IntDistribution(*esp["num_leaves"]),
                 min_sum_hessian_in_leaf=optuna.distributions.FloatDistribution(*esp["min_sum_hessian_in_leaf"]))
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    hist = [json.loads(l) for l in open(ruta_jsonl)] if os.path.exists(ruta_jsonl) else []
    if hist:
        log(f"  {etiqueta} retomando: {len(hist)} trials ya completos")
# [Anotación · líneas 180–203] Bucle hasta completar 10 trials. Para el trial k crea un estudio de Optuna que
#   maximiza, con TPESampler de semilla 878443 + k y n_startup_trials 12, le carga los trials anteriores, pide
#   una propuesta, entrena con la semilla 878443 y calcula el AUC sobre la matriz de validación. Agrega el
#   resultado como una línea del .jsonl y llama a la función de respaldo.
    while len(hist) < CFG["n_trials"]:
        k = len(hist)
        semilla_trial = CFG["semilla_bo"] + k
        estudio = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(
            seed=semilla_trial, n_startup_trials=CFG["n_startup_trials"]))
        for h in hist:
            estudio.add_trial(optuna.trial.create_trial(params=h["params"], distributions=dists, value=h["auc"]))
        trial = estudio.ask()
        t0 = time.time()
        hp = dict(num_iterations=trial.suggest_int("num_iterations", *esp["num_iterations"]),
                  num_leaves=trial.suggest_int("num_leaves", *esp["num_leaves"]),
                  min_sum_hessian_in_leaf=trial.suggest_float("min_sum_hessian_in_leaf", *esp["min_sum_hessian_in_leaf"]))
        m = entrenar(hp, CFG["semilla_bo"], dtr)                  # la bayesiana usa la primera semilla
        auc = float(roc_auc_score(y_va, m.predict(X_va)))
        del m
        gc.collect()
        seg = round(time.time() - t0)
        log(f"  {etiqueta} trial {k:>2}: it={hp['num_iterations']:>4} hojas={hp['num_leaves']:>4} "
            f"hess={hp['min_sum_hessian_in_leaf']:.6f} -> AUC {auc:.5f}  ({seg}s, semilla del muestreador {semilla_trial})")
        hist.append(dict(trial=k, params=hp, auc=auc, segundos=seg, semilla_muestreador=semilla_trial))
        with open(ruta_jsonl, "a") as fh:
            fh.write(json.dumps(hist[-1]) + "\n")
        if despues_de_trial:
            despues_de_trial()
# [Anotación · líneas 204–209] Elige el trial de mayor AUC (ante empate, el primero) y devuelve el historial,
#   los tres hiperparámetros de ese trial y su registro.
    mejor = max(hist, key=lambda h: h["auc"])                      # ante empate, el primero
    mejores = dict(num_iterations=int(mejor["params"]["num_iterations"]),
                   num_leaves=int(mejor["params"]["num_leaves"]),
                   min_sum_hessian_in_leaf=float(mejor["params"]["min_sum_hessian_in_leaf"]))
    log(f"  {etiqueta} MEJORES hiperparámetros (trial {mejor['trial']}, AUC {mejor['auc']:.5f}): {mejores}")
    return hist, mejores, mejor


# [Anotación · líneas 212–233] entrenar_semillas(): para cada semilla que no tenga todas sus predicciones
#   guardadas entrena un modelo, predice cada matriz recibida, guarda <nombre>_<semilla>.npy y registra el AUC
#   cuando hay clase para esa matriz. Devuelve las predicciones leídas de disco, por matriz y por semilla.
def entrenar_semillas(dtr, mejores, semillas, matrices, y_eval, dir_p, despues=None):
    """Entrena un modelo por semilla sobre dtr y predice cada matriz de `matrices` (dict nombre -> X).
    Guarda <nombre>_<semilla>.npy al terminar cada semilla (reanudable). Devuelve {nombre: {semilla: prob}}."""
    os.makedirs(dir_p, exist_ok=True)
    ruta = lambda nom, sd: os.path.join(dir_p, f"{nom}_{sd}.npy")
    pend = [sd for sd in semillas if not all(os.path.exists(ruta(n, sd)) for n in matrices)]
    log(f"  {len(semillas)} semillas {semillas}; pendientes {len(pend)}")
    for sd in pend:
        t = time.time()
        m = entrenar(mejores, sd, dtr)
        msg = []
        for nom, X in matrices.items():
            pr = m.predict(X).astype("float64")
            guardar_atomico(lambda r: np.save(open(r, "wb"), pr), ruta(nom, sd))
            if nom in y_eval:
                msg.append(f"AUC {nom} {roc_auc_score(y_eval[nom], pr):.5f}")
        log(f"  semilla {sd}: {', '.join(msg)}  ({time.time() - t:.0f}s)")
        del m
        gc.collect()
        if despues:
            despues()
    return {nom: {sd: np.load(ruta(nom, sd)) for sd in semillas} for nom in matrices}


# [Anotación · líneas 236–242] tabla_predicciones() arma un DataFrame con numero_de_cliente, foto_mes, las dos
#   clases, una columna prob_<semilla> por modelo y prob_ens, el promedio de esas columnas.
def tabla_predicciones(ids, mes, tern, yb, P):
    """DataFrame con identificación, clase real, una columna prob_<semilla> por semilla y prob_ens (promedio simple)."""
    out = pd.DataFrame(dict(numero_de_cliente=ids, foto_mes=mes, clase_ternaria=tern, clase_binaria=yb.astype("float32")))
    for sd, pr in P.items():
        out[f"prob_{sd}"] = pr
    out["prob_ens"] = out[[f"prob_{sd}" for sd in P]].mean(axis=1)
    return out


# [Anotación · líneas 245–263] resumen_mes() calcula el AUC de cada semilla y del promedio y lo guarda en
#   <prefijo>_auc.csv. Calcula la ganancia acumulada para envíos de 1.000 a 30.000 de a 100, por semilla, su
#   media y la del promedio de probabilidades, la guarda en <prefijo>_ganancia.csv y registra el máximo de las
#   dos últimas.
def resumen_mes(P, y_real, tern, prefijo, etiqueta):
    """AUC por semilla y del ensamble, y curva de ganancia (por semilla, media y ensamble) en un mes con clase real."""
    semillas = list(P)
    ens = np.mean([P[s] for s in semillas], axis=0)
    aucs = {s: float(roc_auc_score(y_real, P[s])) for s in semillas}
    auc_ens = float(roc_auc_score(y_real, ens))
    pd.DataFrame(dict(semilla=semillas + ["ensamble"], auc=list(aucs.values()) + [auc_ens])
                 ).to_csv(f"{prefijo}_auc.csv", index=False)
    log(f"  {etiqueta}: AUC media de semillas {np.mean(list(aucs.values())):.5f} "
        f"(sd {np.std(list(aucs.values()), ddof=1):.5f}), ensamble {auc_ens:.5f}")
    envios = np.arange(1000, min(30000, len(tern)) + 1, 100)
    tab = pd.DataFrame(dict(envios=envios, **{f"g_{s}": curva_ganancia(P[s], tern)[envios - 1] for s in semillas}))
    tab["g_media"] = tab[[f"g_{s}" for s in semillas]].mean(axis=1)
    tab["g_ens"] = curva_ganancia(ens, tern)[envios - 1]
    tab.to_csv(f"{prefijo}_ganancia.csv", index=False)
    for nombre in ("g_media", "g_ens"):
        k = int(tab[nombre].idxmax())
        log(f"  {etiqueta} {nombre}: máximo {tab[nombre][k] / 1e6:,.1f} M con {int(tab['envios'][k]):,} envíos "
            f"(mirar la curva suavizada, no solo el pico)")


# [Anotación · líneas 266–295] ensamblar_08(): lee ids_08.npy de la carpeta del volumen y de cada carpeta
#   adicional y exige que sean iguales. Recorre la lista ordenada de semillas, toma los
#   pred_08/prob_<semilla>.npy que existen (una semilla no puede estar en dos carpetas), se queda con los
#   primeros n si se pide, y calcula prob_ens como el promedio por fila de las probabilidades de esos modelos.
# ---------------------------------------------------------------------------
# Ensamble de las predicciones sobre 08 disponibles hasta el momento (se puede llamar en cualquier momento).
# ---------------------------------------------------------------------------
def ensamblar_08(dir_exp, volumen, semillas_orden, n=None, top=11000, guardar=True, otros_dirs=()):
    """Promedia las probabilidades guardadas en pred_08/prob_<semilla>.npy (en el orden de semillas_orden).
    otros_dirs: carpetas exp/<otro volumen> con más predicciones de las mismas características (mismo 08, mismo orden de
    clientes); no puede haber semillas repetidas entre carpetas. n: usar solo los primeros n modelos (None = todos)."""
    dirs = [dir_exp] + list(otros_dirs)
    ids = np.load(os.path.join(dir_exp, "ids_08.npy"))
    ruta_de = {}
    for d in dirs:
        ids_d = np.load(os.path.join(d, "ids_08.npy"))
        assert np.array_equal(ids_d, ids), f"{d}: ids_08.npy distinto: no son los mismos clientes de 08 en el mismo orden"
        dir_p = os.path.join(d, "pred_08")
        for sd in semillas_orden:
            f = os.path.join(dir_p, f"prob_{sd}.npy")
            if os.path.exists(f):
                assert sd not in ruta_de, f"la semilla {sd} está en dos carpetas ({ruta_de[sd]} y {f}): rangos de semillas superpuestos"
                ruta_de[sd] = f
    usadas = [sd for sd in semillas_orden if sd in ruta_de]
    if n:
        usadas = usadas[:n]
    if not usadas:
        raise SystemExit(f"No hay predicciones en {[os.path.join(d, 'pred_08') for d in dirs]}")
    P = np.column_stack([np.load(ruta_de[sd]) for sd in usadas])
    assert P.shape[0] == len(ids), "las predicciones no tienen la misma cantidad de clientes que ids_08.npy"
    ens = P.mean(axis=1)
    out = pd.DataFrame(dict(numero_de_cliente=ids, prob_ens=ens))
    log(f"  ensamble de {len(usadas)} modelos sobre {len(ids):,} clientes de 08"
        + (f" (carpetas: {', '.join(os.path.basename(d) for d in dirs)})" if len(dirs) > 1 else ""))
# [Anotación · líneas 296–303] Con 4 modelos o más, para k en 2, 5, 10, 20, 40, 80, 160 y 320 (los menores a
#   la cantidad de modelos) registra qué proporción de los primeros `top` clientes (11.000 por defecto) del
#   promedio de los primeros k modelos coincide con los del promedio de todos.
    # estabilidad: cuánto del top-N del ensamble completo ya está en el top-N del ensamble de los primeros k modelos
    if len(usadas) >= 4:
        top = min(top, len(ids))
        topN = set(np.argsort(-ens, kind="stable")[:top])
        ks = sorted({k for k in (2, 5, 10, 20, 40, 80, 160, 320) if k < len(usadas)})
        for k in ks:
            tk = set(np.argsort(-P[:, :k].mean(axis=1), kind="stable")[:top])
            log(f"  top {top:,}: con {k:>3} modelos coincide el {len(tk & topN) / top:.1%} con el ensamble de {len(usadas)}")
# [Anotación · líneas 304–309] Si guardar es verdadero escribe <etiqueta>_pred_08_ens_<n>modelos.parquet con
#   numero_de_cliente y prob_ens; la etiqueta une con "+" los nombres de las carpetas usadas. Devuelve la tabla
#   y la lista de semillas usadas.
    if guardar:
        etiqueta = "+".join(os.path.basename(d) for d in dirs) if len(dirs) > 1 else volumen
        ruta_out = os.path.join(dir_exp, f"{etiqueta}_pred_08_ens_{len(usadas)}modelos.parquet")
        guardar_atomico(lambda r: out.to_parquet(r, index=False), ruta_out)
        log(f"  guardado: {ruta_out}")
    return out, usadas
```


## Explicaciones del alumno (texto original)

### README.md

> # DMEyF — 1ra competencia: predicción de bajas (`BAJA+2`) en el mes 202108
>
> Código para reproducir las predicciones sobre el mes **202108** de la primera competencia de DMEyF (Maestría en Ciencia de Datos, FCEN-UBA): predecir qué clientes del paquete premium de un banco argentino abandonan el servicio.
>
> Resumen del método:
>
> 1. Preprocesamiento: corrección de `ccajas_depositos` en 202105, clase binaria `BAJA` (`BAJA+1` y `BAJA+2` = 1, `CONTINUA` = 0), variables históricas, ranking con cero fijo y flags `_zero`.
> 2. Bayesiana de 3 hiperparámetros de LightGBM (**L20**): entrena en 03-04, valida en 06, sin las variables de préstamos.
> 3. Entrenamiento final (**L22 / L22b**): 45 modelos que solo cambian la semilla, entrenados con los meses 03 a 06, que predicen 08.
> 4. Ensamble por promedio de probabilidades y archivos de submit (los `N` clientes de mayor probabilidad).
>
> ## Estructura
>
> ```
> exp/
> ├── L20/codigo/      preprocesamiento + bayesiana (+ etapa 2 con clase artificial, no usada en L22)
> ├── L22/codigo/      entrenamiento final, ensamble y submits (semillas 0 a 199, se usaron las 33 primeras)
> └── L22b/codigo/     entrenamiento final de una segunda VM (semillas 200 a 399, se usaron las 12 primeras)
> hiperparametros/
> └── L20_e1_hiperparametros.json
> ```
>
> Cada carpeta `codigo/` es la copia exacta de los scripts que se ejecutaron en ese experimento (cada script guarda una copia de sí mismo al correr).
>
>
> ## Entorno
>
> - Los scripts asumen una carpeta de trabajo plana `~/dmeyf/` y un bucket de GCS. El nombre del bucket está en la constante `BUCKET` de los scripts (`gs://luisdsuarez_buckito2026`).
> - Ejecución original: VM de GCP (8 núcleos, 60 GB de RAM).
> - L22b se corrió en VM de 4 nucleos
>
>
> Preparar la carpeta de trabajo copiando **todos** los archivos de las tres carpetas `codigo/` a `~/dmeyf/` (los nombres no se pisan; si `comun_L22.py` está en L22 y en L22b, es el mismo archivo salvo mejoras posteriores: usar la versión más reciente).
>
> ## Reproducción paso a paso
>
> Todos los comandos se corren desde `~/dmeyf/`.
>
> ### 1. Preprocesamiento (L20)
>
> ```bash
> python 01_preprocesamiento_L20.py --entrada /ruta/a/competencia_01_ternaria.csv --sin_bucket
> ```
>
> Genera `~/dmeyf/datasets/L20_dataset.parquet`. Pasos, en este orden:
>
> 1. `ccajas_depositos` = NA solo en 202105 (todos eran cero).
> 2. `clase_binaria`: `BAJA+1` y `BAJA+2` = 1; `CONTINUA` = 0; el resto (mes 07 sin etiqueta y mes 08) = NA.
> 3. Para todas las columnas salvo las 10 sin historia (edad, antigüedad y fechas relativas): `lag1`, `lag2`, `delta1`, `delta2`, `tend3` (pendiente de la recta de cuadrados mínimos sobre el mes actual y los 2 anteriores) y `avg3` (promedio), todos por unión con (cliente, mes − k), no por desplazamiento de filas.
> 4. Ranking con cero fijo, por variable y por mes, sobre los 7 grupos (original, lag1, delta1, lag2, delta2, tend3, avg3): los positivos rankean en (0, 1], los negativos en [−1, 0), el cero queda en cero y los NA se conservan. Reemplaza a la variable cruda.
> 5. Flags `<variable>_zero` (1 si el valor crudo es cero, NA si era NA, 0 en otro caso), sin rankear, para las variables que alguna vez valen cero.
>
> El cálculo vive en `preproc_comun.py`.
>
> ### 2. Bayesiana (L20, etapa 1)
>
> ```bash
> python 02_etapa1_L20.py --sin_bucket
> ```
>
> - Optuna, primera semilla (878443), 3 hiperparámetros con los rangos del script de GustavoPasquini (`num_iterations` 64-4096, `num_leaves` 16-2048, `min_sum_hessian_in_leaf` 1e-6-0.1, escala lineal), 10 trials aleatorios.
> - Entrena con 202103 y 202104, valida con 202106 (AUC), **sin** `cprestamos_personales` y `mprestamos_personales` ni ninguna de sus variantes (16 columnas).
> - Resto de los hiperparámetros fijos (ver `PARAMS_FIJOS` en `comun_L20.py`): sin submuestreo, sin pesos de clase.
> - La reanudación es reproducible: cada trial depende solo de su número y de los resultados anteriores.
>
> Salida que usa L22: `exp/L20/L20_e1_hiperparametros.json`. (La etapa 2 de L20, con clase artificial, no interviene en L22.)
>
> ### 3. Entrenamiento final para 08 (L22 / L22b)
>
> ```bash
> # VM 1: semillas en las posiciones 0 a 199 de la lista fija
> python 01_entrenar_08_L22.py --dataset ~/dmeyf/datasets/L20_dataset.parquet \
>        --hiperparametros ~/dmeyf/exp/L20/L20_e1_hiperparametros.json --volumen L22 --desde 0 --n_semillas 200 --sin_bucket
>
> # VM 2 (opcional): posiciones 200 a 399, otro volumen para no pisar archivos
> python 01_entrenar_08_L22.py --dataset ~/dmeyf/datasets/L20_dataset.parquet \
>        --hiperparametros ~/dmeyf/exp/L20/L20_e1_hiperparametros.json --volumen L22b --desde 200 --n_semillas 200 --sin_bucket
> ```
>
> - Entrena con los meses 03, 04, 05 y 06 (clase real) y **todas** las columnas, incluidas las de préstamos; los hiperparámetros son los de la bayesiana, encontrada sin ellas.
> - Un modelo por semilla; cada predicción sobre 08 se guarda al terminar en `exp/<volumen>/pred_08/prob_<semilla>.npy`. Se puede interrumpir en cualquier momento y retomar con el mismo comando.
> - Semillas: las 5 asignadas (878443, 455471, 178447, 235397, 409027) y luego una secuencia determinística (`semillas_n` en `comun_L22.py`: 507928, 515847, ...).
>
> ### 4. Ensamble y submits
>
> ```bash
> # ensamble de todos los modelos disponibles (promedio simple de las probabilidades)
> python 02_ensamblar_08_L22.py --volumen L22 --otros L22b
>
> # un único archivo de submit con los N clientes de mayor probabilidad del ensamble
> python 03_submit_L22.py --corte 10500 --volumen L22 --otros L22b
>
> # varios submits, uno por línea de corte, con un archivo por semilla (primeras 20), en carpetas separadas
> python 04_submits_por_corte_L22.py --volumen L22 --otros L22b --desde 9000 --hasta 13000 --paso 500 --n_semillas 20 --zip
> ```

