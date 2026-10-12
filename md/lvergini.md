# lvergini — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: lvergini
- Repositorio: https://github.com/lvergini/dmeyf2026-competencia1
- Link posteado: https://github.com/lvergini/dmeyf2026-competencia1
- Commit: 60033c058addeed97ca87d354181675162f704fb
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/lvergini/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/lvergini.json

## Resumen

Repositorio en R con una entrega para predecir BAJA+2 en 202108 con un semillerío de LightGBM. 00_pipeline.R ejecuta cuatro pasos, cada uno en un proceso de R aparte: (1) construye el dataset FE026 desde competencia_01.csv.gz: pasa ccajas_depositos a NA en 202105, agrega lags y deltas de orden 1 y 2 de todas las variables por mes calendario y reemplaza cada variable por su ranking con cero fijo dentro de cada mes; (2) toma los hiperparámetros de una optimización bayesiana con mlr3mbo (entrena con 202103 y 202104, mide AUC en 202106, sin préstamos personales); por defecto copia el log ya corrido, BO_log_corrido.txt; (3) entrena el modelo con 202103 a 202106, clase binaria (BAJA+1 y BAJA+2 positivos) y todas las variables, una vez por cada una de las 107 semillas de semillas_A.csv (primos de seis cifras repartidos en 4 sublistas), y predice 202108; (4) promedia las probabilidades por cliente, descartando las semillas con predicciones idénticas a otra, y escribe los 11.750 clientes de mayor probabilidad. La carpeta evaluacion_junio/ contiene el código que calcula la ganancia en 202106 por cantidad de envíos con 20 semillas; según el README, con esa evaluación se eligió el corte y no interviene en el archivo final. Incluye README.md, evaluacion_junio/LEEME.md y renv.lock.

**Qué entrega.** Un CSV sin encabezado con los numero_de_cliente de los 11.750 clientes de mayor probabilidad promedio en 202108, uno por línea: exp/entregas/<fecha_hora>_P069_prob/P069_prob_11750.csv. El archivo no está en el repositorio; lo generan los scripts (exp/ y datasets/ figuran en .gitignore).

**Cómo se ejecuta.** Según el README: instalar los paquetes con renv::restore(lockfile = 'renv.lock'), copiar competencia_01.csv.gz en datasets/ y correr, desde la carpeta de la entrega, Rscript 00_pipeline.R. Opciones: --paralelo corre las sublistas de la producción a la vez y --bayesiana repite la optimización en lugar de copiar el log. El README detalla también los pasos por separado: Rscript 01_datasets.R; Rscript modelo_A_FE026_B018/01_bayesiana.R (o copiar BO_log_corrido.txt a exp/B018/BO_log.txt y crear exp/B018/COMPLETA); Rscript modelo_A_FE026_B018/02_produccion.R <sublista> <proceso> para cada par de semillas_A.csv; Rscript 02_prediccion_final.R. La evaluación de junio se corre aparte, desde evaluacion_junio/, según su LEEME.md.

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: clase01 = 1 si clase_ternaria es BAJA+2 o BAJA+1 y 0 en otro caso (R/produccion.R línea 74; la misma definición en la optimización, modelo_A_FE026_B018/01_bayesiana.R línea 61).
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No aplica submuestreo: la optimización y el entrenamiento final usan todos los registros de sus meses de entrenamiento. En evaluacion_junio/ el parámetro undersampling vale 1,0 (se conservan todos los negativos).
- **Calidad de datos:** ccajas_depositos se pasa a NA en todos los registros de 202105 antes de calcular los lags (R/datasets.R líneas 49-50). Al leer el dataset se verifica que no haya pares (numero_de_cliente, foto_mes) repetidos y que todas las variables sean numéricas; la clase vacía se pasa a NA.
- **Drifting:** Ranking con cero fijo, por variable y dentro de cada foto_mes, de todas las columnas salvo numero_de_cliente, foto_mes y clase_ternaria (originales, lags y deltas): los positivos pasan a rank / cantidad de positivos, en (0, 1]; los negativos a -rank(|x|) / cantidad de negativos, en [-1, 0); el 0 queda en 0 y NA queda NA; empates con rango promedio. El valor rankeado reemplaza al original (R/datasets.R líneas 67-84).
- **Variables dentro del mes:** No se observa en el código del camino de la entrega. evaluacion_junio/R/fe.R define fe_combinaciones() y fe_negocio(), que la construcción de FE026 no llama.
- **Variables históricas:** Lag de orden 1 y 2 y delta (valor actual menos lag) de orden 1 y 2 de cada variable original, por mes calendario: el lag k es el valor del mismo cliente en el mes foto_mes - k y queda en NA si el cliente no tiene registro ese mes (R/datasets.R líneas 53-65). Lags y deltas entran después al ranking por mes. Según el README, FE026 tiene 763 columnas.
- **Selección de variables:** No hay selección por importancia. En la optimización bayesiana y en la evaluación de junio se excluyen mprestamos_personales y cprestamos_personales con sus lags y deltas; el entrenamiento final usa todas las columnas de FE026 salvo clase_ternaria y clase01, lo que incluye numero_de_cliente y foto_mes (R/produccion.R línea 75).
- **Optimización de hiperparámetros:** Optimización bayesiana con bbotk y mlr3mbo: modelo sustituto kriging (regr.km de DiceKriging), función de adquisición 'ei', optimizador de la adquisición por búsqueda al azar con 1.000 evaluaciones y terminador de 10 evaluaciones; el log incluido tiene 12 filas (según el README, por el diseño inicial al azar de 12). Busca num_iterations (64 a 4.096), num_leaves (16 a 2.048) y min_sum_hessian_in_leaf (1e-6 a 0,1). Entrena con 202103 y 202104, valida con 202106, métrica AUC, sin submuestreo y sin préstamos personales.
- **Hiperparámetros finales:** Fila de mayor métrica de BO_log_corrido.txt (iter 11, AUC 0,92064): num_iterations 2786, num_leaves 1080, min_sum_hessian_in_leaf 0,0473. Fijos: boosting gbdt, objective binary, learning_rate 0,005, feature_fraction 0,5, feature_fraction_bynode 0,2, max_bin 31, min_data_in_leaf 0, lambda_l1 0, lambda_l2 0, bagging_fraction 1, max_depth -1, min_gain_to_split 0, force_row_wise TRUE, deterministic TRUE, num_threads 8.
- **Semillas:** Números primos de seis cifras obtenidos con una criba, mezclados con set.seed(173207) y sample(), y repartidos en 4 sublistas (la sublista k toma las posiciones k, k + 4, k + 8, ...). modelo_A_FE026_B018/semillas_A.csv lista las 107 semillas de la entrega con su sublista, posición y proceso (7 pares sublista-proceso). La predicción final descarta las semillas cuyo vector de probabilidades es idéntico al de otra; según el README, se descarta 1 (694327, idéntica a 316817) y se promedian 106. La semilla 173207 se usa también en la optimización bayesiana.
- **Cantidad de semillas:** 107
- **Ensamble:** Semillerío: promedio por cliente de las probabilidades de todas las semillas de P069 que quedan tras descartar las de predicciones idénticas (02_prediccion_final.R líneas 31-45). El script admite combinar más de un modelo por promedio de probabilidades o de rankings normalizados, pero los argumentos fijan un solo modelo (P069).
- **Corte:** Cantidad fija escrita en el código: los 11.750 clientes de mayor probabilidad promedio (02_prediccion_final.R línea 20). Según el README, el corte se ubicó en el centro de la zona más alta de la curva de ganancia en 202106 suavizada con el promedio en ±500 envíos, calculada con 20 semillas; ese cálculo está en evaluacion_junio/curva_por_corte.R, que evalúa cortes de 10.500 a 12.500 cada 250.
- **Validación:** La optimización bayesiana entrena con 202103 y 202104 y mide AUC en 202106; 202105 no se usa en esa etapa. En evaluacion_junio/ la misma configuración se entrena con 202103 y 202104 con 20 semillas, sin préstamos personales, y se calcula en 202106 la ganancia acumulada por cantidad de envíos (+1.072.500 por BAJA+2 y -27.500 por cada otro envío), para el promedio de las semillas y para cada semilla. El entrenamiento final (202103 a 202106) no tiene conjunto de validación.
- **Salidas:** datasets/FE026.csv.gz; exp/B018/BO_log.txt y exp/B018/COMPLETA; exp/P069/semillas/prob_<semilla>.csv.gz (numero_de_cliente y prob de 202108, un archivo por semilla); exp/P069/importancia_<semilla>.csv de la primera semilla entrenada en cada proceso; exp/entregas/<fecha_hora>_P069_prob/ con P069_prob_11750.csv, probabilidades.csv.gz (numero_de_cliente, semillerio_P069 y puntaje) y resumen.txt; registros de cada paso en exp/registros/.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Técnicas sólo exploradas

- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Mínimos y máximos de ventana (`variables.min_max_ventana`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Clase artificial o pseudo-etiquetas para meses sin clase (`clase.clase_artificial`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Random Forest (`modelo.random_forest`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README: R 4.6.1 (renv.lock registra R 4.6.0 porque se generó en otra máquina) y los paquetes de renv.lock, entre ellos lightgbm 4.7.0, data.table 1.18.6.1 y mlr3mbo 1.2.1; 8 hilos para LightGBM fijos en el código; máquinas virtuales de Google Cloud e2-highmem-8 (8 vCPU, 64 GB de memoria); unos 4,5 GB de disco. El README declara que la reproducción byte a byte se verificó en máquinas e2-highmem-8.

## Pasos del camino de la entrega

1. **Orquestación de la entrega.** 00_pipeline.R lee las opciones --bayesiana y --paralelo y corre cada paso con Rscript en un proceso aparte, con la salida en exp/registros/. Si un paso termina con código distinto de 0, o no deja el archivo esperado, se detiene con un mensaje que indica el paso y su registro. (`00_pipeline.R` líneas 27–58)
2. **Lectura y controles del dataset.** 01_datasets.R llama a asegurar_FE026(). construir_FE026() lee datasets/competencia_01.csv.gz, verifica que no haya pares cliente-mes repetidos y que todas las variables sean numéricas, y pasa la clase vacía a NA. (`01_datasets.R` líneas 11–13; `R/datasets.R` líneas 30–46)
3. **ccajas_depositos a NA en 202105.** Antes de calcular los lags, ccajas_depositos se convierte a numérico y se pasa a NA en todos los registros de 202105. (`R/datasets.R` líneas 48–50)
4. **Lags y deltas de orden 1 y 2 por mes calendario.** Con un índice de período (año × 12 + mes), para k = 1 y 2 une la tabla consigo misma por cliente y período desplazado k meses y agrega <variable>_lag<k>; después agrega <variable>_delta<k> como valor actual menos lag. Se aplica a todas las variables salvo numero_de_cliente, foto_mes y clase_ternaria. (`R/datasets.R` líneas 52–65)
5. **Ranking con cero fijo dentro de cada mes.** Cada columna (originales, lags y deltas) se reemplaza, mes por mes, por su ranking normalizado: positivos en (0, 1], negativos en [-1, 0), el 0 en 0 y NA en NA, con empates en rango promedio. (`R/datasets.R` líneas 67–86)
6. **Grabado de FE026.** Si datasets/FE026.csv.gz no existe, se escribe con fwrite como archivo .parcial y se renombra; si existe, se reutiliza. El pipeline verifica que el archivo haya quedado. (`R/datasets.R` líneas 89–101; `00_pipeline.R` líneas 60–63)
7. **Parámetros fijos y espacio de búsqueda.** R/parametros.R define la semilla 173207, la lista de parámetros fijos de LightGBM (learning_rate 0,005, feature_fraction 0,5, max_bin 31, min_data_in_leaf 0, más feature_fraction_bynode 0,2), los rangos de los tres hiperparámetros que se optimizan y las variables de préstamos personales que se excluyen en la optimización. (`R/parametros.R` líneas 15–82)
8. **Optimización bayesiana (B018).** 01_bayesiana.R arma FE026 en memoria, entrena con 202103 y 202104 y valida con 202106 sin las columnas de préstamos personales, y optimiza num_iterations, num_leaves y min_sum_hessian_in_leaf con mlr3mbo (kriging, adquisición 'ei', 10 evaluaciones pedidas) usando AUC. Cada evaluación se agrega a exp/B018/BO_log.txt. Por defecto el pipeline no la corre: copia BO_log_corrido.txt, que tiene 12 evaluaciones. (`modelo_A_FE026_B018/01_bayesiana.R` líneas 53–133; `modelo_A_FE026_B018/BO_log_corrido.txt` líneas 1–13; `00_pipeline.R` líneas 65–82)
9. **Elección de la configuración.** producir() lee el log de la optimización, lo ordena por métrica descendente y toma la fila 1; sus valores se superponen a los parámetros fijos. 02_produccion.R la invoca con id P069, FE026.csv.gz y configuración 1. (`R/produccion.R` líneas 35–45; `modelo_A_FE026_B018/02_produccion.R` líneas 15–20)
10. **Semillas por sublista y proceso.** Se generan los primos de seis cifras, se mezclan con set.seed(173207) y se reparten en 4 sublistas. Las semillas de semillas_A.csv tienen que coincidir, en orden, con el tramo inicial de la sublista; de ellas se entrenan las del proceso indicado. El pipeline lanza un Rscript por cada par (sublista, proceso), en secuencia o con las sublistas en paralelo. (`R/produccion.R` líneas 47–67; `00_pipeline.R` líneas 84–127)
11. **Entrenamiento final y predicción por semilla.** Lee FE026, arma la clase binaria (BAJA+1 y BAJA+2 positivos), entrena con 202103 a 202106 con todas las columnas salvo clase_ternaria y clase01 y, para cada semilla, entrena un LightGBM cambiando sólo seed, predice 202108 y graba exp/P069/semillas/prob_<semilla>.csv.gz. Las semillas ya grabadas se saltean. (`R/produccion.R` líneas 69–110)
12. **Semillerío.** 02_prediccion_final.R lee todos los archivos de probabilidades de P069, descarta los que repiten exactamente las probabilidades de otro, verifica que los clientes coincidan y promedia la probabilidad por cliente. (`02_prediccion_final.R` líneas 31–54)
13. **Corte y archivo de envío.** Ordena los clientes por probabilidad promedio descendente y graba los primeros 11.750 numero_de_cliente, sin encabezado, en una carpeta con fecha y hora; también graba probabilidades.csv.gz y resumen.txt. (`02_prediccion_final.R` líneas 18–25; `02_prediccion_final.R` líneas 56–72)
14. **Evaluación en 202106 para el corte (fuera del pipeline).** No la ejecuta 00_pipeline.R. corridas/E079.R entrena la configuración de mayor AUC con 202103 y 202104, 20 semillas y sin préstamos personales, y el Rmd calcula la ganancia acumulada en 202106 de cada semilla y del promedio. curva_por_corte.R promedia la ganancia entre n - 500 y n + 500 envíos para cortes de 10.500 a 12.500 cada 250. Según el README, de esa curva salió el corte de 11.750. (`evaluacion_junio/corridas/E079.R` líneas 6–12; `evaluacion_junio/corridas/junio_comun.R` líneas 22–67; `evaluacion_junio/rmd/03_experimento.Rmd` líneas 238–309; `evaluacion_junio/curva_por_corte.R` líneas 19–37)

## Archivos

- `01_datasets.R` · principal · R · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/01_datasets.R.txt) — Carga R/datasets.R y llama a asegurar_FE026() para grabar datasets/FE026.csv.gz si no existe.
- `02_prediccion_final.R` · principal · R · 72 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/02_prediccion_final.R.txt) — Arma el semillerío de P069 (promedio por cliente de las probabilidades de las semillas, sin las de predicciones idénticas a otra), ordena los clientes y escribe el archivo de envío con los primeros 11.750, además de probabilidades.csv.gz y resumen.txt.
- `README.md` · explicacion · Markdown · 274 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/README.md.txt) — Presentación de la entrega: contenido de la carpeta, construcción de FE026, optimización bayesiana, cómo se eligieron los hiperparámetros y el corte, requisitos (R, renv.lock, máquina, disco), orden de corrida con tiempos medidos, formato del archivo final, tabla de semillas incluidas (107 listadas, 1 descartada, 106 usadas) y las verificaciones de reproducción que declara.
- `00_pipeline.R` · principal · R · 131 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/00_pipeline.R.txt) — Ejecuta la entrega completa en orden: dataset, bayesiana (o copia de su log), producción por sublista y proceso, y predicción final. Cada paso corre en un proceso de Rscript aparte y deja su salida en exp/registros/.
- `modelo_A_FE026_B018/02_produccion.R` · principal · R · 20 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/modelo_A_FE026_B018/02_produccion.R.txt) — Lanza la producción P069 para una sublista y un proceso recibidos por línea de comandos: llama a producir() con FE026.csv.gz, el log exp/B018/BO_log.txt, la configuración 1 y la lista semillas_A.csv.
- `modelo_A_FE026_B018/BO_log_corrido.txt` · configuracion · Texto · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/modelo_A_FE026_B018/BO_log_corrido.txt.txt) — Log de la optimización bayesiana usada en la entrega, separado por tabulaciones: una línea de títulos y 12 evaluaciones con todos los parámetros de LightGBM, el número de evaluación y el AUC. El pipeline lo copia a exp/B018/BO_log.txt y la producción toma su fila de mayor métrica.
- `modelo_A_FE026_B018/01_bayesiana.R` · principal · R · 133 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/modelo_A_FE026_B018/01_bayesiana.R.txt) — Optimización bayesiana B018 de tres hiperparámetros de LightGBM sobre FE026 armado en memoria: entrena con 202103 y 202104, valida con AUC en 202106, sin préstamos personales, y escribe exp/B018/BO_log.txt y exp/B018/COMPLETA.
- `R/produccion.R` · principal · R · 111 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/R/produccion.R.txt) — Define producir(): toma una configuración del log de la optimización, entrena LightGBM con 202103 a 202106 y todas las variables, una vez por semilla de la sublista y el proceso indicados, y graba la probabilidad de 202108 de cada semilla en exp/<id>/semillas/.
- `R/parametros.R` · configuracion · R · 82 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/R/parametros.R.txt) — Semilla 173207, parámetros fijos de LightGBM, rangos de los tres hiperparámetros de la optimización bayesiana y funciones que separan las columnas de préstamos personales y sus derivadas.
- `R/datasets.R` · principal · R · 101 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/R/datasets.R.txt) — Define construir_FE026() (NA en ccajas_depositos de 202105, lags y deltas de orden 1 y 2 por mes calendario y ranking con cero fijo por variable y mes) y asegurar_FE026(), que graba el resultado en datasets/FE026.csv.gz.
- `evaluacion_junio/LEEME.md` · explicacion · Markdown · 42 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/evaluacion_junio/LEEME.md.txt) — Explica la evaluación E079 en 202106 (20 semillas, 202103 y 202104, sin préstamos personales), cómo correrla desde evaluacion_junio/, el tiempo que declara (unos 12 minutos por semilla en una máquina de 8 vCPU) y qué hace cada archivo de la carpeta.
- `evaluacion_junio/curva_por_corte.R` · secundario · R · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/evaluacion_junio/curva_por_corte.R.txt) — A partir de las probabilidades por semilla de 202106 calcula, para cortes de 10.500 a 12.500 envíos cada 250, el promedio de la ganancia acumulada entre n - 500 y n + 500 envíos, del promedio de semillas y de cada semilla.
- `evaluacion_junio/corridas/junio_fe026.R` · secundario · R · 60 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/evaluacion_junio/corridas/junio_fe026.R.txt) — Define asegurar_FE026() con rutas de here::here() y correr_experimento_FE026(), que renderiza rmd/03_experimento.Rmd con los parámetros de la evaluación de junio sobre datasets/FE026.csv.gz.
- `evaluacion_junio/corridas/E079.R` · secundario · R · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/evaluacion_junio/corridas/E079.R.txt) — Lanza la evaluación E079: FE026 con la configuración 1 (mayor métrica) de exp/B018/BO_log.txt, exigiendo que la optimización tenga el archivo COMPLETA.
- `evaluacion_junio/corridas/junio_comun.R` · secundario · R · 67 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/evaluacion_junio/corridas/junio_comun.R.txt) — Configuración común de la evaluación en junio: 20 semillas, entrenamiento con 202103 y 202104, mes de medición 202106, sin undersampling, 8 hilos y exclusión de préstamos personales con sus lags y deltas.
- `evaluacion_junio/R/utils.R` · secundario · R · 148 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/evaluacion_junio/R/utils.R.txt) — Funciones de soporte: descargar_dataset(), particionar() (partición estratificada), loguear(), particionar_por_cliente() y filas_undersampling(), que conserva todos los positivos y una fracción al azar de los negativos.
- `evaluacion_junio/R/fe_FE026.R` · secundario · R · 77 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/evaluacion_junio/R/fe_FE026.R.txt) — Define construir_FE026() con los mismos tres pasos que R/datasets.R (NA en ccajas_depositos de 202105, lags y deltas de orden 1 y 2, ranking con cero fijo), con la ruta del dataset resuelta por here::here().
- `evaluacion_junio/R/experimentos.R` · secundario · R · 56 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/evaluacion_junio/R/experimentos.R.txt) — Registro de resultados: guardar_resultado() escribe exp/<experimento>/resultado.csv, experimento_registrado() indica si existe y consolidar_experimentos() reúne todos los resultado.csv en experimentos.csv.
- `evaluacion_junio/R/fe.R` · secundario · R · 711 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/evaluacion_junio/R/fe.R.txt) — Biblioteca de transformaciones que no usa la clase: construir_dataset_fe() (aplica una lista de pasos y guarda la especificación en fe_specs/), fe_lags(), fe_lags_mes(), fe_lags_variables(), rank_cero_fijo() y sus variantes por patrón o por lista, fe_anti_imputacion(), fe_eliminar(), fe_combinaciones() (suma, resta, producto y cociente de pares), fe_negocio() (5 cocientes), fe_payroll_binaria(), fe_historicas() (promedio, máximo, mínimo y cocientes sobre los 3 registros previos), fe_mecanismos() (17 variables tr_) y fe_agregar_columnas(). Según el LEEME, contiene funciones que el modelo de la entrega no usa.
- `evaluacion_junio/R/pipeline.R` · secundario · R · 347 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/evaluacion_junio/R/pipeline.R.txt) — Funciones que renderizan plantillas Rmd a partir de una configuración: correr_experimento(), correr_cola(), generar_entrega(), correr_bayesiana(), correr_bayesiana_cv(), correr_bayesiana_intrusos() y correr_etiquetador(). De las plantillas que nombra, el repositorio sólo incluye rmd/03_experimento.Rmd. La evaluación E079 carga este archivo y usa experimento_registrado() de R/experimentos.R.
- `evaluacion_junio/R/modelo.R` · secundario · R · 136 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/evaluacion_junio/R/modelo.R.txt) — Funciones de la evaluación: curva_ganancia() (ganancia acumulada con +1.072.500 por BAJA+2 y -27.500 por cada otro envío), evaluar_semillas(), average_precision() y resumir_cortes() (media, desvío, mínimo y máximo entre semillas en cada corte).
- `evaluacion_junio/R/evaluar_semillas_guardando.R` · secundario · R · 96 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/evaluacion_junio/R/evaluar_semillas_guardando.R.txt) — Define evaluar_semillas_guardando(): entrena un modelo por semilla, graba la probabilidad del mes futuro de cada una apenas termina y devuelve curvas de ganancia, matriz de probabilidades e importancia; las semillas ya grabadas se leen en lugar de reentrenarse.
- `evaluacion_junio/rmd/03_experimento.Rmd` · secundario · R Markdown · 379 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/lvergini/evaluacion_junio/rmd/03_experimento.Rmd.txt) — Plantilla parametrizada de experimento: entrena un LightGBM por semilla con la fila de mayor métrica de un log de optimización, mide la ganancia acumulada en el mes futuro por semilla y del promedio, y graba probabilidades, importancia, tablas por corte y resultado.csv en exp/<experimento>/. Tiene ramas opcionales (clase artificial, eliminación de registros 'intrusos', hojas de un bosque como variables) que la evaluación E079 deja desactivadas.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### 01_datasets.R

Carga R/datasets.R y llama a asegurar_FE026() para grabar datasets/FE026.csv.gz si no existe.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Encabezado con el uso; carga R/datasets.R y llama a asegurar_FE026(), que
#   construye FE026 desde datasets/competencia_01.csv.gz y lo graba en datasets/FE026.csv.gz sólo si ese archivo
#   no existe.
# =============================================================================
# 01_datasets.R
# uso, desde la carpeta de la entrega: Rscript 01_datasets.R
# Construye FE026 a partir de datasets/competencia_01.csv.gz y lo graba en
# datasets/FE026.csv.gz, que es el archivo que lee la producción. La
# optimización bayesiana no lo lee: arma FE026 en memoria, como en la corrida
# original.
# Si el archivo ya existe, no se vuelve a construir.
# =============================================================================

source(file.path("R", "datasets.R"))

asegurar_FE026()
```

### 02_prediccion_final.R

Arma el semillerío de P069 (promedio por cliente de las probabilidades de las semillas, sin las de predicciones idénticas a otra), ordena los clientes y escribe el archivo de envío con los primeros 11.750, además de probabilidades.csv.gz y resumen.txt.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–16] Encabezado: parámetros (método prob o rank, cortes, ids de modelos), qué lee y qué
#   escribe.
# =============================================================================
# 02_prediccion_final.R
# uso, desde la carpeta de la entrega: Rscript 02_prediccion_final.R
# Parámetros (fijados en args, más abajo):
#   metodo: prob (promedio de probabilidades) o rank (promedio de rankings)
#   cortes: separados por coma, por ejemplo 10500,11000,11500,12000
#   modelos: ids de producción, por ejemplo P069
# Para cada modelo lee exp/<id>/semillas/prob_*.csv.gz, descarta las semillas
# con predicciones idénticas a otra (misma semilla interna de LightGBM), y
# hace su semillerío (promedio de las semillas). Con más de un
# modelo, los combina por probabilidad o por ranking, con igual peso.
# Escribe un archivo de envío por corte con este formato: los
# numero_de_cliente de los primeros N, sin encabezado, enteros.
# Salida (nunca sobrescribe): exp/entregas/<fecha_hora>_<modelos>_<metodo>/
#   <modelos>_<metodo>_<corte>.csv, probabilidades.csv.gz y resumen.txt
# =============================================================================

# [Anotación · líneas 18–29] Carga data.table y fija los argumentos en el código: método 'prob', corte 11750 y
#   modelo P069. Define r01() (ranking normalizado por la cantidad de valores) y anotar(), que muestra cada
#   línea y la acumula para resumen.txt.
suppressPackageStartupMessages(library(data.table))
# Predicción final: semillerío del modelo A (P069), corte de 11.750 envíos.
args <- c("prob", "11750", "P069")
if (length(args) < 3) stop("Uso: Rscript 02_prediccion_final.R")
metodo <- args[1]
cortes <- as.integer(strsplit(args[2], ",")[[1]])
modelos <- args[-(1:2)]
stopifnot(metodo %in% c("prob", "rank"), !anyNA(cortes))

r01 <- function(p) frank(p, ties.method = "average") / length(p)
resumen <- character(0)
anotar <- function(...) { linea <- paste0(...); message(linea); resumen <<- c(resumen, linea) }

# [Anotación · líneas 31–45] semillerio(id): lee todos los exp/<id>/semillas/prob_<semilla>.csv.gz en orden de
#   nombre, descarta los que tienen un vector de probabilidades idéntico al de un archivo anterior, verifica que
#   todos tengan los mismos clientes en el mismo orden y devuelve el promedio por cliente.
semillerio <- function(id) {
  archivos <- sort(list.files(file.path("exp", id, "semillas"), pattern = "^prob_[0-9]+\\.csv\\.gz$", full.names = TRUE))
  if (length(archivos) == 0) stop(id, ": no hay semillas en exp/", id, "/semillas")
  probs <- lapply(archivos, fread)
  repetida <- duplicated(lapply(probs, `[[`, "prob"))
  if (any(repetida)) {
    anotar(id, ": descartadas por predicciones idénticas a otra semilla: ",
           paste(basename(archivos[repetida]), collapse = ", "))
    archivos <- archivos[!repetida]; probs <- probs[!repetida]
  }
  ids <- probs[[1]]$numero_de_cliente
  for (p in probs) stopifnot(identical(p$numero_de_cliente, ids))
  anotar(id, ": ", length(probs), " semillas")
  data.table(numero_de_cliente = ids, prob = rowMeans(sapply(probs, `[[`, "prob")))
}

# [Anotación · líneas 47–54] Calcula el semillerío de cada modelo. Con un solo modelo el puntaje es su
#   probabilidad promedio; con más de uno, alinea los clientes con el primero y promedia probabilidades (método
#   prob) o rankings normalizados (método rank) con igual peso.
sems <- lapply(modelos, semillerio)
ids <- sems[[1]]$numero_de_cliente
for (k in seq_along(sems)[-1]) {
  if (!setequal(sems[[k]]$numero_de_cliente, ids)) stop(modelos[k], ": los clientes de 202108 no coinciden con ", modelos[1])
  sems[[k]] <- sems[[k]][match(ids, numero_de_cliente)]
}
puntaje <- if (length(sems) == 1) sems[[1]]$prob else
  if (metodo == "prob") rowMeans(sapply(sems, `[[`, "prob")) else rowMeans(sapply(sems, function(s) r01(s$prob)))

# [Anotación · líneas 56–62] Crea exp/entregas/<fecha_hora>_<modelos>_<metodo>/ y graba probabilidades.csv.gz
#   con numero_de_cliente, una columna semillerio_<modelo> por modelo y el puntaje.
nombre <- paste(modelos, collapse = "+")
carpeta <- file.path("exp", "entregas", paste0(format(Sys.time(), "%Y%m%d_%H%M%S"), "_", gsub("\\+", "_", nombre), "_", metodo))
dir.create(carpeta, recursive = TRUE, showWarnings = FALSE)
tb <- data.table(numero_de_cliente = ids)
for (k in seq_along(sems)) tb[, (paste0("semillerio_", modelos[k])) := sems[[k]]$prob]
tb[, puntaje := puntaje]
fwrite(tb, file.path(carpeta, "probabilidades.csv.gz"))

# [Anotación · líneas 64–72] Ordena los clientes por puntaje descendente y, para cada corte, graba los
#   primeros N numero_de_cliente como enteros, sin encabezado, en <modelos>_<metodo>_<corte>.csv. Escribe
#   resumen.txt con las semillas usadas, las descartadas, los cortes y la cantidad de clientes.
orden <- ids[order(-puntaje)]
for (n in cortes) {
  f <- file.path(carpeta, sprintf("%s_%s_%d.csv", gsub("\\+", "_", nombre), metodo, n))
  fwrite(data.table(as.integer(orden[seq_len(n)])), f, col.names = FALSE)
}
anotar("Combinación: ", nombre, " por ", if (length(sems) == 1) "semillerío" else metodo,
       " | cortes: ", paste(cortes, collapse = ", "), " | ", length(ids), " clientes")
anotar("Archivos en ", carpeta)
writeLines(resumen, file.path(carpeta, "resumen.txt"))
```

### 00_pipeline.R

Ejecuta la entrega completa en orden: dataset, bayesiana (o copia de su log), producción por sublista y proceso, y predicción final. Cada paso corre en un proceso de Rscript aparte y deja su salida en exp/registros/.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–25] Encabezado: uso (Rscript 00_pipeline.R [--bayesiana] [--paralelo]) y descripción
#   de los cuatro pasos que ejecuta en orden.
# =============================================================================
# 00_pipeline.R
# uso, desde la carpeta de la entrega:
#   Rscript 00_pipeline.R [--bayesiana] [--paralelo]
# Ejecuta la entrega completa, en orden, llamando a los scripts de cada paso
# (cada uno en un proceso de R aparte):
#   1. 01_datasets.R: construye y graba datasets/FE026.csv.gz.
#   2. Bayesiana: por defecto copia el log de la optimización que se usó
#      (modelo_A_FE026_B018/BO_log_corrido.txt) a exp/B018/BO_log.txt y crea
#      exp/B018/COMPLETA; con --bayesiana corre la optimización completa
#      (modelo_A_FE026_B018/01_bayesiana.R).
#   3. Producción: para cada par (sublista, proceso) de
#      modelo_A_FE026_B018/semillas_A.csv corre
#      modelo_A_FE026_B018/02_produccion.R <sublista> <proceso>; los procesos
#      de una misma sublista van en orden. Por defecto las sublistas corren
#      una después de otra; con --paralelo, todas a la vez, cada una en su
#      propio proceso (cada producción usa 8 hilos y carga el dataset completo
#      en memoria, así que el paralelo necesita una máquina con lugar para
#      todas).
#   4. 02_prediccion_final.R: semillerío, corte y archivo final.
# Si un paso falla, se detiene con un mensaje que indica cuál y dónde está su
# registro. La salida de cada paso queda en exp/registros/.
# Las opciones también se pueden fijar abajo, en CORRER_BAYESIANA y
# PRODUCCION_EN_PARALELO.
# =============================================================================

# [Anotación · líneas 27–35] Define las opciones CORRER_BAYESIANA y PRODUCCION_EN_PARALELO, ambas FALSE por
#   defecto; lee los argumentos de la línea de comandos, se detiene si hay alguno distinto de --bayesiana o
#   --paralelo y activa las opciones pedidas.
CORRER_BAYESIANA <- FALSE
PRODUCCION_EN_PARALELO <- FALSE

opciones <- commandArgs(trailingOnly = TRUE)
desconocidas <- setdiff(opciones, c("--bayesiana", "--paralelo"))
if (length(desconocidas) > 0) stop("Opciones desconocidas: ", paste(desconocidas, collapse = " "),
                                    "\nUso: Rscript 00_pipeline.R [--bayesiana] [--paralelo]")
if ("--bayesiana" %in% opciones) CORRER_BAYESIANA <- TRUE
if ("--paralelo" %in% opciones) PRODUCCION_EN_PARALELO <- TRUE

# [Anotación · líneas 37–58] Ubica el ejecutable Rscript, crea exp/registros/ y define tres funciones:
#   avance() (mensaje con fecha y hora), correr_script() (lanza un script con system2 en otro proceso de R, con
#   stdout y stderr en un archivo de registro) y paso() (corre un script, mide el tiempo y detiene la ejecución
#   con un mensaje si el código de salida no es 0).
rscript <- file.path(R.home("bin"), "Rscript")
registros <- file.path("exp", "registros")
dir.create(registros, showWarnings = FALSE, recursive = TRUE)
avance <- function(...) message(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), " | ", ...)

# Corre un script en un proceso de R aparte, con su salida en un registro;
# devuelve el código de salida del proceso
correr_script <- function(script, argumentos = character(0), registro) {
  system2(rscript, c(script, argumentos), stdout = registro, stderr = registro)
}

# Corre un paso y se detiene si falla
paso <- function(nombre, script, argumentos = character(0)) {
  registro <- file.path(registros, paste0(gsub("[^A-Za-z0-9]+", "_", nombre), ".log"))
  avance(nombre, ": ", paste(c(script, argumentos), collapse = " "))
  t0 <- Sys.time()
  estado <- correr_script(script, argumentos, registro)
  if (!identical(as.integer(estado), 0L))
    stop("Falló el paso '", nombre, "' (", script, " terminó con código ", estado,
         "). Se detiene la entrega; ver ", registro, call. = FALSE)
  avance(nombre, ": terminado en ", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), " min")
}

# [Anotación · líneas 60–63] Paso 1: corre 01_datasets.R y verifica que exista datasets/FE026.csv.gz.
# --- 1. Dataset ---------------------------------------------------------------
paso("1 dataset", "01_datasets.R")
if (!file.exists(file.path("datasets", "FE026.csv.gz")))
  stop("El paso '1 dataset' no dejó datasets/FE026.csv.gz. Se detiene la entrega.", call. = FALSE)

# [Anotación · líneas 65–82] Paso 2: con --bayesiana corre modelo_A_FE026_B018/01_bayesiana.R; sin esa opción
#   copia BO_log_corrido.txt a exp/B018/BO_log.txt y crea el archivo COMPLETA. Si ya hay un BO_log.txt distinto
#   del de la entrega, se detiene. Al final verifica que existan el log y COMPLETA.
# --- 2. Bayesiana -------------------------------------------------------------
carpeta_bo <- file.path("exp", "B018")
log_bo <- file.path(carpeta_bo, "BO_log.txt")
log_corrido <- file.path("modelo_A_FE026_B018", "BO_log_corrido.txt")
if (CORRER_BAYESIANA) {
  paso("2 bayesiana", file.path("modelo_A_FE026_B018", "01_bayesiana.R"))
} else {
  avance("2 bayesiana: se usa el log de la optimización de la entrega (", log_corrido, ")")
  dir.create(carpeta_bo, showWarnings = FALSE, recursive = TRUE)
  if (file.exists(log_bo) && !identical(readLines(log_bo), readLines(log_corrido)))
    stop("Ya existe ", log_bo, " y no es igual a ", log_corrido, " (¿una optimización corrida antes?). ",
         "Para usarlo, correr con --bayesiana; para usar el de la entrega, borrar ", carpeta_bo, ".", call. = FALSE)
  if (!file.exists(log_bo)) file.copy(log_corrido, log_bo)
  writeLines("log de la optimización de la entrega, copiado por 00_pipeline.R", file.path(carpeta_bo, "COMPLETA"))
}
if (!file.exists(log_bo) || !file.exists(file.path(carpeta_bo, "COMPLETA")))
  stop("Falta ", log_bo, " o ", file.path(carpeta_bo, "COMPLETA"), " después del paso '2 bayesiana'. ",
       "Se detiene la entrega.", call. = FALSE)

# [Anotación · líneas 84–101] Paso 3: lee semillas_A.csv, arma para cada sublista la lista ordenada de sus
#   procesos y define correr_sublista(), que corre 02_produccion.R <sublista> <proceso> para cada proceso en
#   orden y devuelve la descripción del primero que termina con código distinto de 0, o una cadena vacía.
# --- 3. Producción ------------------------------------------------------------
lista <- read.csv(file.path("modelo_A_FE026_B018", "semillas_A.csv"))
if (nrow(lista) == 0) stop("modelo_A_FE026_B018/semillas_A.csv no tiene semillas. Se detiene la entrega.", call. = FALSE)
procesos_por_sublista <- lapply(split(lista$proceso, lista$sublista), function(p) sort(unique(p)))
avance("3 producción: ", nrow(lista), " semillas en ", length(procesos_por_sublista), " sublistas (",
       if (PRODUCCION_EN_PARALELO) "en paralelo" else "en secuencia", ")")

# Corre, en orden, los procesos de una sublista; devuelve "" si todos
# terminaron bien, o la descripción del que falló
correr_sublista <- function(sublista, procesos) {
  for (p in procesos) {
    registro <- file.path(registros, sprintf("3_produccion_sublista%d_proceso%d.log", sublista, p))
    estado <- correr_script(file.path("modelo_A_FE026_B018", "02_produccion.R"), c(sublista, p), registro)
    if (!identical(as.integer(estado), 0L))
      return(sprintf("sublista %d, proceso %d (código %s; ver %s)", sublista, p, estado, registro))
  }
  ""
}

# [Anotación · líneas 103–127] Corre las sublistas: con --paralelo y más de una sublista crea un cluster PSOCK
#   con un trabajador por sublista y las lanza a la vez con clusterMap; si no, las corre en secuencia y corta en
#   la primera que devuelve una descripción no vacía. Después se detiene si alguna sublista informó un proceso
#   con código distinto de 0 y verifica que exista exp/P069/semillas/prob_<semilla>.csv.gz para cada semilla de
#   la lista.
t0 <- Sys.time()
sublistas <- as.integer(names(procesos_por_sublista))
if (PRODUCCION_EN_PARALELO && length(sublistas) > 1) {
  cl <- parallel::makePSOCKcluster(length(sublistas))
  parallel::clusterCall(cl, setwd, getwd())
  parallel::clusterExport(cl, c("correr_script", "rscript", "registros"))
  fallas <- tryCatch(
    unlist(parallel::clusterMap(cl, correr_sublista, sublistas, procesos_por_sublista)),
    finally = parallel::stopCluster(cl))
} else {
  fallas <- character(0)
  for (k in seq_along(sublistas)) {
    avance("3 producción: sublista ", sublistas[k], ", procesos ", paste(procesos_por_sublista[[k]], collapse = ", "))
    fallas <- c(fallas, correr_sublista(sublistas[k], procesos_por_sublista[[k]]))
    if (tail(fallas, 1) != "") break
  }
}
fallas <- fallas[fallas != ""]
if (length(fallas) > 0)
  stop("Falló el paso '3 producción' en: ", paste(fallas, collapse = "; "), ". Se detiene la entrega.", call. = FALSE)
faltan <- lista$semilla[!file.exists(file.path("exp", "P069", "semillas", sprintf("prob_%d.csv.gz", lista$semilla)))]
if (length(faltan) > 0)
  stop("El paso '3 producción' no dejó las predicciones de ", length(faltan), " semillas (por ejemplo ",
       faltan[1], "). Se detiene la entrega.", call. = FALSE)
avance("3 producción: terminado en ", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), " min")

# [Anotación · líneas 129–131] Paso 4: corre 02_prediccion_final.R e informa que el archivo final queda en
#   exp/entregas/.
# --- 4. Predicción final ------------------------------------------------------
paso("4 prediccion final", "02_prediccion_final.R")
avance("Entrega completa. Archivo final en exp/entregas/ (ver ", file.path(registros, "4_prediccion_final.log"), ")")
```

### modelo_A_FE026_B018/02_produccion.R

Lanza la producción P069 para una sublista y un proceso recibidos por línea de comandos: llama a producir() con FE026.csv.gz, el log exp/B018/BO_log.txt, la configuración 1 y la lista semillas_A.csv.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Encabezado con el uso y los requisitos (datasets/FE026.csv.gz y
#   exp/B018/BO_log.txt con COMPLETA). Carga R/produccion.R y llama a producir() con id P069, dataset
#   FE026.csv.gz, configuración 1 del log, la sublista del primer argumento, el proceso del segundo (1 si no se
#   indica) y modelo_A_FE026_B018/semillas_A.csv como lista de semillas.
# =============================================================================
# 02_produccion.R del modelo A
# uso, desde la carpeta de la entrega:
#   Rscript modelo_A_FE026_B018/02_produccion.R <sublista 1-4> [<proceso>]
# Producción del modelo A (P069): FE026 con la configuración de mayor AUC de
# B018. Esquema de R/produccion.R (cuatro meses, préstamos incluidos, una
# semilla por vez, cada semilla grabada en exp/P069/semillas/).
# Entrena las semillas de semillas_A.csv de esa sublista y ese proceso
# (1 si no se indica), en el orden en que corrieron. Cada sublista y cada
# proceso se corre en un Rscript aparte, como en la producción original.
# Requiere datasets/FE026.csv.gz (01_datasets.R) y exp/B018/BO_log.txt con
# exp/B018/COMPLETA (01_bayesiana.R, o BO_log_corrido.txt copiado ahí).
# =============================================================================

source(file.path("R", "produccion.R"))
args <- commandArgs(trailingOnly = TRUE)
producir("P069", "FE026.csv.gz", "exp/B018/BO_log.txt", 1L,
         maquina = as.integer(args[1]),
         archivo_semillas = file.path("modelo_A_FE026_B018", "semillas_A.csv"),
         proceso = if (length(args) >= 2) as.integer(args[2]) else 1L)
```

### modelo_A_FE026_B018/01_bayesiana.R

Optimización bayesiana B018 de tres hiperparámetros de LightGBM sobre FE026 armado en memoria: entrena con 202103 y 202104, valida con AUC en 202106, sin préstamos personales, y escribe exp/B018/BO_log.txt y exp/B018/COMPLETA.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–19] Encabezado: uso y esquema de la optimización (parámetros fijos
#   param_fijos_tutoria, sin préstamos personales, entrenamiento 202103 y 202104, validación 202106, sin 202105,
#   sin undersampling, AUC, 8 hilos, 10 evaluaciones) y sus salidas.
# =============================================================================
# 01_bayesiana.R del modelo A
# uso, desde la carpeta de la entrega: Rscript modelo_A_FE026_B018/01_bayesiana.R
# Bayesiana frugal del modelo A (B018) sobre FE026, armado en memoria:
#   - parámetros fijos param_fijos_tutoria (incluye feature_fraction_bynode
#     = 0.20)
#   - sin mprestamos_personales, cprestamos_personales ni sus lags y deltas
#     (columnas_sin_excluidas)
#   - entrenamiento: 202103 y 202104 completos; validación: 202106 completo;
#     202105 no se usa (hueco de un mes, como entre los datos de
#     entrenamiento final y 202108)
#   - sin undersampling
#   - métrica AUC; 8 hilos
#   - 10 evaluaciones (mlr3mbo hace igual un diseño inicial al azar de
#     4 x 3 = 12)
# Salida: exp/B018/BO_log.txt; al terminar, exp/B018/COMPLETA.
# Si encuentra un BO_log incompleto (corrida interrumpida), lo renombra y
# empieza de nuevo (mlr3mbo no retoma una corrida).
# =============================================================================

# [Anotación · líneas 21–36] Verifica que estén instalados los 11 paquetes que usa (data.table, R.utils,
#   rlist, bbotk, mlr3, mlr3mbo, mlr3learners, paradox, DiceKriging, lightgbm y here), carga diez de ellos,
#   carga R/datasets.R y R/parametros.R y define avance() para los mensajes con fecha y hora.
paquetes <- c("data.table", "R.utils", "rlist", "bbotk", "mlr3", "mlr3mbo", "mlr3learners",
              "paradox", "DiceKriging", "lightgbm", "here")
faltan <- paquetes[!vapply(paquetes, requireNamespace, logical(1), quietly = TRUE)]
if (length(faltan) > 0) stop("Faltan paquetes: ", paste(faltan, collapse = ", "))

suppressPackageStartupMessages({
  library(data.table); library(R.utils); library(rlist); library(bbotk); library(mlr3)
  library(mlr3mbo); library(mlr3learners); library(paradox); library(DiceKriging); library(lightgbm)
})
source(file.path("R", "datasets.R"))
source(file.path("R", "parametros.R"))

if (!exists("param_fijos_tutoria") || !exists("columnas_sin_excluidas"))
  stop("R/parametros.R no tiene param_fijos_tutoria o columnas_sin_excluidas")

avance <- function(...) message(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), " [B018] ", ...)

# [Anotación · líneas 38–51] Crea exp/B018/. Si existe el archivo COMPLETA termina sin repetir la
#   optimización; si hay un BO_log.txt sin COMPLETA lo renombra a BO_log_interrumpido_<fecha_hora>.txt y empieza
#   de nuevo.
carpeta <- file.path("exp", "B018")
dir.create(carpeta, showWarnings = FALSE, recursive = TRUE)
archivo_log <- file.path(carpeta, "BO_log.txt")
archivo_completa <- file.path(carpeta, "COMPLETA")

if (file.exists(archivo_completa)) {
  avance("B018 ya está completa; no se repite")
  quit(save = "no", status = 0)
}
if (file.exists(archivo_log)) {
  viejo <- file.path(carpeta, paste0("BO_log_interrumpido_", format(Sys.time(), "%Y%m%d_%H%M%S"), ".txt"))
  file.rename(archivo_log, viejo)
  avance("BO_log incompleto renombrado a ", basename(viejo))
}

# [Anotación · líneas 53–57] PARAM: meses de entrenamiento 202103 y 202104, mes de validación 202106 y 10
#   iteraciones.
PARAM <- list(
  train = c(202103L, 202104L),
  validate = 202106L,
  iteraciones = 10
)

# [Anotación · líneas 59–78] Construye FE026 en memoria, arma clase01 (1 si BAJA+2 o BAJA+1), separa las
#   columnas de préstamos personales y sus derivadas y se detiene si no encuentra ninguna. Arma los lgb.Dataset
#   de entrenamiento (202103 y 202104) y de validación (202106) con las columnas restantes, que son todas salvo
#   clase_ternaria, clase01 y las excluidas.
# Dataset
dataset <- construir_FE026()
dataset[, clase01 := ifelse(clase_ternaria %in% c("BAJA+2", "BAJA+1"), 1L, 0L)]
todas <- setdiff(colnames(dataset), c("clase_ternaria", "clase01"))
excluidas <- columnas_excluidas(todas)
campos_buenos <- columnas_sin_excluidas(todas)
avance("Columnas excluidas (", length(excluidas), "): ", paste(excluidas, collapse = ", "))
if (length(excluidas) == 0) stop("No se encontró ninguna columna a excluir: revisar los nombres")
avance("Parámetro agregado: feature_fraction_bynode = ", param_fijos_tutoria$feature_fraction_bynode)

tr <- dataset[foto_mes %in% PARAM$train]
va <- dataset[foto_mes == PARAM$validate]
stopifnot(tr[, !anyNA(clase_ternaria)], va[, !anyNA(clase_ternaria)])
avance("Entrenamiento: ", nrow(tr), " registros (", paste(PARAM$train, collapse = "+"), ", positivos ",
       tr[, sum(clase01)], "); validación: ", nrow(va), " (", PARAM$validate, ", positivos ", va[, sum(clase01)],
       "); variables: ", length(campos_buenos))

dtrain <- lgb.Dataset(data = data.matrix(tr[, campos_buenos, with = FALSE]), label = tr$clase01, free_raw_data = FALSE)
dvalidate <- lgb.Dataset(data = data.matrix(va[, campos_buenos, with = FALSE]), label = va$clase01, free_raw_data = FALSE)
rm(dataset, tr, va); gc(verbose = FALSE)

# [Anotación · líneas 80–88] loguear(): agrega al log una línea separada por tabulaciones con fecha y hora y
#   todos los valores de la lista recibida; si el archivo no existe escribe antes la línea de títulos.
# Registro de cada evaluación
loguear <- function(preg, arch, verbose = TRUE) {
  t0 <- Sys.time()
  reg <- copy(preg)
  if (!file.exists(arch)) cat(paste0("fecha\t", paste(list.names(reg), collapse = "\t"), "\n"), file = arch)
  linea <- paste0(format(t0, "%Y%m%d.%H%M%S"), "\t", gsub(", ", "\t", toString(reg)), "\n")
  cat(linea, file = arch, append = TRUE)
  if (verbose) cat(linea)
}

# [Anotación · líneas 90–106] Estimar_lightgbm(xs): función objetivo. Superpone los tres hiperparámetros
#   propuestos a param_fijos_tutoria, entrena con lgb.train usando 202106 como conjunto de validación, toma
#   modelo$best_score (metric = auc) como métrica, registra la evaluación en el log y vuelve a fijar la semilla
#   del generador de R con 173207.
giter <- 0
Estimar_lightgbm <- function(xs) {
  flush.console()
  giter <<- giter + 1
  t0 <- Sys.time()
  param_completo <- modifyList(param_fijos_tutoria, xs)
  xx <- copy(param_completo)
  modelo <- lgb.train(data = dtrain, valids = list("val" = dvalidate), param = param_completo)
  xx$iter <- giter
  xx$metrica <- modelo$best_score
  loguear(xx, archivo_log)
  avance(sprintf("evaluación %d | %d árboles, %d hojas, hessian %.4g | AUC %.5f | %.1f min",
                 giter, xs$num_iterations, xs$num_leaves, xs$min_sum_hessian_in_leaf, xx$metrica,
                 as.numeric(difftime(Sys.time(), t0, units = "mins"))))
  set.seed(semilla_primigenia, kind = "L'Ecuyer-CMRG")
  list(metrica = xx$metrica)
}

# [Anotación · líneas 108–124] Configura la optimización con bbotk y mlr3mbo: objetivo a maximizar sobre
#   rangos_z495(), terminador de 10 evaluaciones, sustituto kriging (regr.km con BFGS y estimación de nugget),
#   función de adquisición 'ei', optimizador de la adquisición por búsqueda al azar con 1.000 evaluaciones y
#   ciclo bayesopt_ego.
# Optimización bayesiana
set.seed(semilla_primigenia, kind = "L'Ecuyer-CMRG")
objective <- ObjectiveRFun$new(
  fun = Estimar_lightgbm,
  domain = rangos_z495(),
  codomain = ps(metrica = p_dbl(tags = "maximize")),
  id = "BO_lightgbm"
)
instance <- OptimInstanceBatchSingleCrit$new(
  objective = objective,
  terminator = trm("evals", n_evals = PARAM$iteraciones)
)
surrogate <- srlrn(lrn("regr.km", optim.method = "BFGS", nugget.estim = TRUE, control = list(trace = FALSE)))
acq_function <- acqf("ei")
acq_optimizer <- acqo(optimizer = opt("random_search", batch_size = 1000), terminator = trm("evals", n_evals = 1000))
optimizer <- opt("mbo", loop_function = bayesopt_ego, surrogate = surrogate,
                 acq_function = acq_function, acq_optimizer = acq_optimizer)

# [Anotación · líneas 126–133] Ejecuta la optimización, lee el log ordenado por métrica descendente, informa
#   la evaluación de mayor AUC con sus tres hiperparámetros y escribe el archivo COMPLETA con la fecha y hora.
avance("Comienza la bayesiana")
optimizer$optimize(instance)

tb <- fread(archivo_log)
setorder(tb, -metrica)
avance("Terminada: ", nrow(tb), " evaluaciones; mejor AUC ", round(tb$metrica[1], 5), " (iter ", tb$iter[1],
       ": ", tb$num_iterations[1], " árboles, ", tb$num_leaves[1], " hojas, hessian ", signif(tb$min_sum_hessian_in_leaf[1], 4), ")")
writeLines(format(Sys.time()), archivo_completa)
```

### R/produccion.R

Define producir(): toma una configuración del log de la optimización, entrena LightGBM con 202103 a 202106 y todas las variables, una vez por semilla de la sublista y el proceso indicados, y graba la probabilidad de 202108 de cada semilla en exp/<id>/semillas/.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–24] Encabezado que describe el esquema de producción (cuatro meses, sin undersampling,
#   todas las variables, una semilla por vez, sublistas y procesos, importancia sólo en la primera semilla de
#   cada proceso); carga data.table, lightgbm y R/parametros.R.
# =============================================================================
# produccion.R
# Entrenamiento final: una configuración de una optimización bayesiana,
# entrenada sobre un dataset grabado en datasets/ con los cuatro meses con
# clase (202103-202106), sin undersampling y con todas las variables
# (préstamos personales incluidos), una semilla por vez; predice 202108.
#   - Cada semilla graba exp/<id>/semillas/prob_<semilla>.csv.gz apenas
#     termina (primero como .tmp); si se relanza, saltea las ya grabadas.
#   - Semillas: primos de 6 cifras en orden aleatorio (set.seed 173207),
#     repartidos en 4 sublistas disjuntas. El argumento 'maquina' es el
#     número de sublista (1 a 4; posiciones maquina, maquina + 4, ...), no la
#     máquina virtual que la corre.
#     En la entrega se entrenan solo las semillas de la lista
#     (archivo_semillas), que tienen que ser el tramo inicial de la sublista,
#     en el mismo orden; 'proceso' indica qué tramo de esa lista corrió en un
#     mismo proceso de R.
#   - Importancia de variables: solo en la primera semilla de cada proceso
#     (exp/<id>/importancia_<semilla>.csv), porque lgb.importance() de un
#     modelo grande tarda muchos minutos en un solo hilo.
#   - El avance y los tiempos se escriben en el log (stderr).
# =============================================================================

suppressPackageStartupMessages({ library(data.table); library(lightgbm) })
source(file.path("R", "parametros.R"))

# [Anotación · líneas 26–33] producir(): verifica que el número de sublista esté entre 1 y 4, define avance()
#   (escribe en stderr con fecha y hora) y crea exp/<id>/semillas/.
producir <- function(id, archivo_dataset, log_bo, configuracion, maquina, archivo_semillas, proceso = 1L) {
  if (is.na(maquina) || !maquina %in% 1:4) stop("maquina (número de sublista) tiene que ser 1, 2, 3 o 4")
  avance <- function(...) cat(format(Sys.time(), "%Y-%m-%d %H:%M:%S"), " [", id, "-", maquina, "] ",
                              ..., "\n", sep = "", file = stderr())

  carpeta_id <- file.path("exp", id)
  carpeta <- file.path(carpeta_id, "semillas")
  dir.create(carpeta, showWarnings = FALSE, recursive = TRUE)

# [Anotación · líneas 35–45] Exige que exista COMPLETA junto al log de la optimización, lee el log, lo ordena
#   por métrica descendente y toma la fila indicada por 'configuracion'; quita fecha, iter y metrica y superpone
#   el resto a param_fijos_tutoria, con num_threads = 8. Informa árboles, hojas, hessian y
#   feature_fraction_bynode.
  # Configuración
  if (!file.exists(file.path(dirname(log_bo), "COMPLETA"))) stop(log_bo, ": la bayesiana no terminó")
  tb <- fread(log_bo)
  setorder(tb, -metrica)
  conf <- as.list(tb[configuracion])
  conf[c("fecha", "iter", "metrica")] <- NULL
  param <- modifyList(param_fijos_tutoria, conf)
  param$num_threads <- 8L
  avance(sprintf("Configuración %d de %s: %d árboles, %d hojas, hessian %.4g, bynode %s",
                 configuracion, log_bo, param$num_iterations, param$num_leaves,
                 param$min_sum_hessian_in_leaf, format(param$feature_fraction_bynode)))

# [Anotación · líneas 47–54] Genera con una criba los números primos menores a 1.000.000, se queda con los de
#   seis cifras, los mezcla con set.seed(173207) y sample() y toma para esta sublista las posiciones maquina,
#   maquina + 4, maquina + 8, ...
  # Semillas de esta sublista
  es_primo <- rep(TRUE, 999999); es_primo[1] <- FALSE
  for (i in 2:999) if (es_primo[i]) es_primo[seq(i * i, 999999, by = i)] <- FALSE
  primos <- which(es_primo)
  primos <- primos[primos >= 100000]
  set.seed(semilla_primigenia)
  primos <- sample(primos)
  semillas <- primos[seq(maquina, length(primos), by = 4)]

# [Anotación · líneas 56–67] Lee semillas_A.csv, filtra la sublista, ordena por posición y verifica que sus
#   semillas coincidan, en orden, con el tramo inicial de la sublista calculada; después se queda con las
#   semillas del proceso indicado e informa cuántas son y entre qué posiciones.
  # Semillas de la lista de la entrega: las de esta sublista forman el tramo
  # inicial de la sublista, en el mismo orden; se toman las de este proceso
  lista <- fread(archivo_semillas)
  lista <- lista[sublista == maquina]
  setorder(lista, posicion)
  if (nrow(lista) == 0) stop(archivo_semillas, ": no hay semillas de la sublista ", maquina)
  stopifnot(identical(as.integer(lista$semilla), as.integer(semillas[seq_len(nrow(lista))])))
  este_proceso <- as.integer(proceso)
  semillas <- lista[proceso == este_proceso, semilla]
  if (length(semillas) == 0) stop(archivo_semillas, ": no hay semillas del proceso ", este_proceso, " en la sublista ", maquina)
  avance("Semillas de la lista: ", length(semillas), " (proceso ", este_proceso, ", de la ", lista[proceso == este_proceso, min(posicion)],
         " a la ", lista[proceso == este_proceso, max(posicion)], " de la sublista)")

# [Anotación · líneas 69–85] Lee datasets/FE026.csv.gz, arma clase01 (1 si BAJA+2 o BAJA+1, 0 en otro caso),
#   usa como variables todas las columnas salvo clase_ternaria y clase01, toma 202103 a 202106 como
#   entrenamiento (verificando que no tengan clase NA) y 202108 como futuro, y arma un único lgb.Dataset que se
#   reutiliza en todas las semillas del proceso.
  # Datos: todos los meses con clase, todas las variables
  ruta <- file.path("datasets", archivo_dataset)
  if (!file.exists(ruta)) stop("No existe ", ruta)
  avance("Leyendo ", ruta)
  dataset <- fread(ruta)
  dataset[, clase01 := ifelse(clase_ternaria %in% c("BAJA+2", "BAJA+1"), 1L, 0L)]
  campos <- setdiff(colnames(dataset), c("clase_ternaria", "clase01"))
  tr <- dataset[foto_mes %in% c(202103L, 202104L, 202105L, 202106L)]
  stopifnot(tr[, !anyNA(clase_ternaria)])
  futuro <- dataset[foto_mes == 202108L]
  stopifnot(nrow(futuro) > 0)
  dtrain <- lgb.Dataset(data = data.matrix(tr[, campos, with = FALSE]), label = tr$clase01, free_raw_data = FALSE)
  x_futuro <- data.matrix(futuro[, campos, with = FALSE])
  ids <- futuro$numero_de_cliente
  avance("Entrenamiento: ", nrow(tr), " registros (202103-202106, positivos ", tr[, sum(clase01)],
         "); futuro: ", length(ids), "; variables: ", length(campos))
  rm(dataset, tr, futuro); gc(verbose = FALSE)

# [Anotación · líneas 87–111] Para cada semilla que no tenga ya su archivo: entrena con lgb.train cambiando
#   sólo seed, predice 202108 y graba numero_de_cliente y prob en exp/<id>/semillas/prob_<semilla>.csv.gz
#   (primero con nombre .tmp y luego renombra). En la primera semilla entrenada del proceso graba además la
#   importancia de variables en exp/<id>/importancia_<semilla>.csv. Informa los minutos de entrenamiento y la
#   cantidad de semillas ya grabadas.
  primera <- TRUE
  for (s in semillas) {
    archivo <- file.path(carpeta, sprintf("prob_%d.csv.gz", s))
    if (file.exists(archivo)) next
    t0 <- Sys.time()
    modelo <- lgb.train(data = dtrain, param = modifyList(param, list(seed = s)))
    prob <- predict(modelo, x_futuro)
    tmp <- sub("\\.csv\\.gz$", ".tmp.csv.gz", archivo)
    fwrite(data.table(numero_de_cliente = ids, prob = prob), tmp)
    file.rename(tmp, archivo)
    t1 <- Sys.time()
    if (primera) {
      imp <- lgb.importance(modelo)
      imp[, semilla := s]
      archivo_imp <- file.path(carpeta_id, sprintf("importancia_%d.csv", s))
      fwrite(imp, archivo_imp)
      primera <- FALSE
    }
    rm(modelo); gc(verbose = FALSE)
    avance(sprintf("semilla %d | entrenamiento %.1f min | total %.1f min | semillas en la carpeta: %d", s,
                   as.numeric(difftime(t1, t0, units = "mins")),
                   as.numeric(difftime(Sys.time(), t0, units = "mins")),
                   length(list.files(carpeta, pattern = "^prob_[0-9]+\\.csv\\.gz$"))))
  }
}
```

### R/datasets.R

Define construir_FE026() (NA en ccajas_depositos de 202105, lags y deltas de orden 1 y 2 por mes calendario y ranking con cero fijo por variable y mes) y asegurar_FE026(), que graba el resultado en datasets/FE026.csv.gz.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–28] Encabezado con el orden de construcción de FE026 y la fórmula del ranking con cero
#   fijo; carga data.table.
# =============================================================================
# datasets.R
# Construcción del dataset FE026 a partir de competencia_01.csv.gz, y su
# grabado en datasets/.
#   construir_FE026()  NA en ccajas_depositos de 202105, lags y deltas de
#                      orden 1 y 2, ranking con cero fijo
#   asegurar_FE026()   graba datasets/FE026.csv.gz si no existe
# Las rutas son relativas a la carpeta de la entrega, que tiene que ser el
# directorio de trabajo.
# =============================================================================

# =============================================================================
# Dataset FE026
# Orden:
#   1. ccajas_depositos a NA en 202105 (el campo está roto ese mes), antes de
#      los lags para que no hereden el valor roto.
#   2. Lag 1, delta lag 1, lag 2 y delta lag 2 de cada variable, por mes
#      calendario: el lag k de un cliente es su valor en el mes foto_mes - k;
#      si el cliente no está en ese mes, el lag queda NA.
#   3. Ranking con cero fijo, por variable y por mes, de todas las variables
#      (originales, lags y deltas) salvo numero_de_cliente, foto_mes y
#      clase_ternaria: positivos -> rank / n+ en (0, 1]; negativos ->
#      -rank(|x|) / n- en [-1, 0); el 0 queda en 0; empates con rango
#      promedio; NA queda NA. El valor rankeado reemplaza al original.
# No se eliminan registros, meses ni variables (préstamos personales incluidos).
# =============================================================================

library(data.table)

# [Anotación · líneas 30–46] construir_FE026(): lee datasets/competencia_01.csv.gz con fread, verifica que
#   existan numero_de_cliente, foto_mes y clase_ternaria y que no haya pares cliente-mes repetidos, pasa la
#   clase vacía a NA y se detiene si alguna de las demás variables no es numérica. Informa la cantidad de
#   registros, de variables y los meses presentes.
construir_FE026 <- function(archivo = file.path("datasets", "competencia_01.csv.gz")) {

  avance <- function(...) message(format(Sys.time(), "%H:%M:%S"), " [FE026] ", ...)
  if (!file.exists(archivo)) stop("No existe ", archivo, ": copiar competencia_01.csv.gz en datasets/")

  avance("Leyendo ", archivo)
  d <- fread(archivo)
  fijas <- c("numero_de_cliente", "foto_mes", "clase_ternaria")
  stopifnot(all(fijas %in% names(d)))
  stopifnot(!anyDuplicated(d, by = c("numero_de_cliente", "foto_mes")))
  d[clase_ternaria == "", clase_ternaria := NA_character_]

  campos <- setdiff(names(d), fijas)
  no_numericas <- campos[!vapply(d[, ..campos], is.numeric, logical(1))]
  if (length(no_numericas) > 0) stop("Variables no numéricas: ", paste(no_numericas, collapse = ", "))
  avance(nrow(d), " registros, ", length(campos), " variables, meses ",
         paste(sort(unique(d$foto_mes)), collapse = ", "))

# [Anotación · líneas 48–50] Convierte ccajas_depositos a numérico y la pasa a NA en todos los registros de
#   202105.
  # 1. ccajas_depositos roto en 202105
  d[, ccajas_depositos := as.numeric(ccajas_depositos)]
  d[foto_mes == 202105L, ccajas_depositos := NA_real_]

# [Anotación · líneas 52–65] Calcula un índice de período (año × 12 + mes) y, para k = 1 y 2, une la tabla
#   consigo misma por cliente y período desplazado k meses para agregar <variable>_lag<k>; después agrega
#   <variable>_delta<k> = valor actual - lag. Si el cliente no tiene registro k meses antes, lag y delta quedan
#   en NA.
  # 2. Lags y delta lags por mes calendario
  d[, periodo := (foto_mes %/% 100L) * 12L + foto_mes %% 100L]
  for (k in 1:2) {
    nombres_lag <- paste0(campos, "_lag", k)
    previo <- d[, c("numero_de_cliente", "periodo", campos), with = FALSE]
    previo[, periodo := periodo + k]
    setnames(previo, campos, nombres_lag)
    d[previo, on = c("numero_de_cliente", "periodo"), (nombres_lag) := mget(paste0("i.", nombres_lag))]
    rm(previo); gc(verbose = FALSE)
    for (j in seq_along(campos))
      set(d, j = paste0(campos[j], "_delta", k), value = as.numeric(d[[campos[j]]]) - as.numeric(d[[nombres_lag[j]]]))
    avance("Lag y delta de orden ", k, " listos")
  }
  d[, periodo := NULL]

# [Anotación · líneas 67–87] Para cada columna salvo numero_de_cliente, foto_mes y clase_ternaria (originales,
#   lags y deltas) y dentro de cada foto_mes, reemplaza el valor por su ranking con cero fijo: los positivos por
#   rank / cantidad de positivos, los negativos por -rank(|x|) / cantidad de negativos, el 0 queda en 0 y NA
#   queda NA; empates con rango promedio. Devuelve la tabla.
  # 3. Ranking con cero fijo, por variable y por mes
  a_rankear <- setdiff(names(d), fijas)
  filas_mes <- split(seq_len(nrow(d)), d$foto_mes)
  for (v in a_rankear) {
    x <- as.numeric(d[[v]])
    r <- rep(NA_real_, length(x))
    for (filas in filas_mes) {
      xi <- x[filas]
      ri <- rep(NA_real_, length(xi))
      ri[!is.na(xi) & xi == 0] <- 0
      pos <- which(!is.na(xi) & xi > 0)
      if (length(pos) > 0) ri[pos] <- frank(xi[pos], ties.method = "average") / length(pos)
      neg <- which(!is.na(xi) & xi < 0)
      if (length(neg) > 0) ri[neg] <- -frank(-xi[neg], ties.method = "average") / length(neg)
      r[filas] <- ri
    }
    set(d, j = v, value = r)
  }
  avance("Ranking con cero fijo listo: ", length(a_rankear), " variables (", ncol(d), " columnas en total)")
  d
}

# [Anotación · líneas 89–101] asegurar_FE026(): si datasets/FE026.csv.gz no existe, escribe el resultado de
#   construir_FE026() con fwrite en un archivo .parcial y lo renombra a FE026.csv.gz; si existe, lo reutiliza.
#   Devuelve el nombre del archivo.
# Graba datasets/FE026.csv.gz si no existe
asegurar_FE026 <- function() {
  archivo <- file.path("datasets", "FE026.csv.gz")
  if (!file.exists(archivo)) {
    message("Grabando ", archivo)
    temporal <- paste0(archivo, ".parcial")
    data.table::fwrite(construir_FE026(), temporal)
    file.rename(temporal, archivo)
  } else {
    message("Dataset FE026 existente, se reutiliza")
  }
  basename(archivo)
}
```


## Explicaciones del alumno (texto original)

### README.md

> # Competencia 1 — Entrega reproducible
>
> Predicción de bajas (BAJA+2) de 202108. La entrega es un modelo LightGBM
> entrenado sobre el dataset FE026, en semillerío: el mismo modelo entrenado
> con muchas semillas y promediado por cliente. Se envían los 11.750 clientes
> con mayor probabilidad.
>
> Todo lo necesario para reproducir el archivo final está en esta carpeta y
> parte de `competencia_01.csv.gz`. Los comandos se ejecutan desde la carpeta
> de la entrega.
>
> Los nombres que aparecen en carpetas y archivos son identificadores de cada
> paso: FE026 es el dataset, B018 la optimización bayesiana de los
> hiperparámetros y P069 la producción (el entrenamiento final, semilla por
> semilla).
>
> ## Contenido
>
> ```
> README.md
> renv.lock                 versiones de los paquetes
> R/
>   parametros.R            semilla, parámetros fijos de LightGBM, rangos de la bayesiana, exclusión de préstamos
>   datasets.R              construcción y grabado de FE026
>   produccion.R            entrenamiento final y predicción de 202108
> 01_datasets.R             graba datasets/FE026.csv.gz
> modelo_A_FE026_B018/
>   01_bayesiana.R          optimización bayesiana
>   02_produccion.R         producción, una semilla por vez
>   semillas_A.csv          semillas que entran en la entrega
>   BO_log_corrido.txt      log de la optimización que se usó
> 02_prediccion_final.R     semillerío, corte y archivo final
> evaluacion_junio/         evaluación en 202106 con la que se eligió el corte (no interviene en el archivo final)
> ```
>
> ## Dataset FE026
>
> Se construye a partir de `competencia_01.csv.gz` (983.061 registros, 152
> variables, meses 202103 a 202108) sin eliminar registros, meses ni
> variables. La clase se toma como binaria: BAJA+1 y BAJA+2 son positivos.
> FE026 tiene 763 columnas:
>
> 1. `ccajas_depositos` pasa a NA en 202105, donde el campo está roto, antes de
>    calcular lags para que no hereden el valor erróneo.
> 2. Lag y delta lag de orden 1 y 2 de cada variable, por mes calendario: el
>    lag de orden k es el valor del cliente k meses antes, y queda en NA si el
>    cliente no estaba ese mes.
> 3. Ranking con cero fijo, por variable y dentro de cada mes, de todas las
>    columnas salvo `numero_de_cliente`, `foto_mes` y `clase_ternaria`: los
>    positivos pasan a su ranking normalizado en (0, 1], los negativos a
>    [-1, 0), el cero queda en cero, sin entrar en ninguno de los dos
>    rankings, y NA queda NA. El ranking reemplaza al valor original, lo que
>    hace comparables las variables entre meses y atenúa el efecto de la
>    inflación.
>
> ## Bayesiana
>
> Los hiperparámetros salen de una optimización bayesiana con pocas
> evaluaciones sobre un conjunto chico de hiperparámetros.
>
> - Entrena con 202103 y 202104 completos y valida con 202106. 202105 no se
>   usa, para dejar el mismo hueco de un mes que hay entre los datos de
>   entrenamiento final y 202108.
> - Sin undersampling. Métrica: AUC en validación.
> - Optimización bayesiana con mlr3mbo (modelo sustituto kriging, mejora
>   esperada), 10 evaluaciones pedidas; el diseño inicial al azar es de 12, así
>   que el log tiene 12 evaluaciones.
> - Parámetros fijos (definidos en `R/parametros.R`): gbdt, `max_bin` 31,
>   `min_data_in_leaf` 0, `feature_fraction` 0,5, `feature_fraction_bynode`
>   0,2, `learning_rate` 0,005, sin regularización ni bagging,
>   `deterministic = TRUE`, 8 hilos.
> - Hiperparámetros optimizados: `num_iterations` (64 a 4.096), `num_leaves`
>   (16 a 2.048) y `min_sum_hessian_in_leaf` (1e-6 a 0,1).
> - `mprestamos_personales`, `cprestamos_personales` y todos sus lags y deltas
>   se excluyen en la optimización. En la producción se usan todas las
>   variables.
>
> Se usa la configuración de mayor AUC del log: evaluación 11, AUC 0,92064,
> 2.786 árboles, 1.080 hojas y `min_sum_hessian_in_leaf` 0,0473.
>
> ## Cómo se eligieron los hiperparámetros y el corte
>
> Todas las decisiones se tomaron con modelos entrenados con 202103 y 202104 y
> evaluados en 202106, un mes que no interviene en ese entrenamiento. 202105 no
> se usa, para reproducir el hueco de un mes que hay entre los datos de
> entrenamiento final y 202108.
>
> - **Hiperparámetros:** la optimización bayesiana descripta arriba entrena con
>   202103 y 202104 y mide el AUC en 202106.
> - **Corte:** el modelo, con esos hiperparámetros, se entrenó con 202103 y
>   202104 con 20 semillas, sin préstamos personales. Se calculó la ganancia en
>   202106 para cada cantidad de envíos (+1.072.500 por cada BAJA+2 y −27.500
>   por cada envío), tanto del semillerío como de cada semilla. Como la curva
>   es irregular (cada baja suma de golpe), se usó la curva suavizada: el
>   promedio de la ganancia en ±500 envíos alrededor de cada corte. El corte se
>   ubicó en el centro de la zona más alta de esa curva.
>
> El código de esta evaluación está en `evaluacion_junio/`. No interviene en la
> producción del archivo final.
>
> ## Requisitos
>
> - R 4.6.1 (versión con la que corrió el modelo) y los paquetes de
>   `renv.lock` (entre otros, lightgbm 4.7.0, data.table 1.18.6.1, mlr3mbo
>   1.2.1). El archivo registra R 4.6.0 porque se generó en otra máquina. Para
>   instalar los paquetes:
>
>   ```bash
>   Rscript -e 'install.packages("renv"); renv::restore(lockfile = "renv.lock")'
>   ```
>
> - 8 hilos para LightGBM (fijo en el código).
> - El modelo se entrenó en máquinas virtuales de Google Cloud e2-highmem-8
>   (8 vCPU, 64 GB de memoria).
> - `competencia_01.csv.gz` en `datasets/` dentro de esta carpeta:
>
>   ```bash
>   mkdir -p datasets && cp <ruta>/competencia_01.csv.gz datasets/
>   ```
>
> - Disco: unos 4,5 GB. `competencia_01.csv.gz` ocupa 0,15 GB y
>   `FE026.csv.gz`, medido en una máquina virtual, 4,3 GB: se graba sin
>   comprimir aunque termine en `.gz` (ver "1. Dataset"). Las predicciones por
>   semilla ocupan poco.
>
> ## Orden de corrida
>
> `00_pipeline.R` ejecuta toda la entrega en orden, cada paso en un proceso de
> R aparte, y se detiene con un mensaje que indica qué paso falló; la salida de
> cada paso queda en `exp/registros/`. Por defecto usa el log de la
> optimización de la entrega (`BO_log_corrido.txt`) y corre las sublistas de
> la producción una después de otra. Con `--paralelo` corre las sublistas a la
> vez, cada una en su propio proceso, y con `--bayesiana` corre además la
> optimización completa:
>
> ```bash
> Rscript 00_pipeline.R
> Rscript 00_pipeline.R --paralelo
> Rscript 00_pipeline.R --bayesiana
> ```
>
> Casi todo el tiempo es de la producción: entre 24 y 27 minutos por semilla
> si las sublistas corren en secuencia; con `--paralelo`, el de la sublista
> más larga, siempre que la máquina tenga hilos y memoria para todas a la vez
> (cada sublista usa 8 hilos y carga el dataset completo). Para 100 semillas,
> son unas 40 horas en secuencia y unas 10 con `--paralelo` y cuatro
> sublistas, si cada sublista dispone de 8 hilos propios, como en la
> producción original, donde cada sublista corrió en una máquina de 8 vCPU.
> A eso se suman unos minutos de dataset y de predicción final, y entre 1 h
> 15 min y 1 h 22 min con `--bayesiana`. Los pasos siguientes describen lo que hace cada etapa.
>
> Los tiempos son los medidos en las máquinas virtuales, a partir de los
> registros de las corridas. Donde solo hay una cota, se indica.
>
> ### 1. Dataset
>
> ```bash
> Rscript 01_datasets.R
> ```
>
> Graba `datasets/FE026.csv.gz`, que lee la producción. La optimización
> bayesiana no lo lee: arma FE026 en memoria, como en la corrida original. El
> archivo queda sin comprimir aunque su nombre termine en `.gz`: se escribe
> primero como `.parcial` (`fwrite` comprime solo si el nombre termina en
> `.gz`) y después se renombra; `fread` lo lee igual. Así se grabó también en
> la producción original. Tiempo: armar FE026 en memoria tomó menos de 7
> minutos (cota que incluye además la primera evaluación de la bayesiana); la
> grabación no se midió por separado.
>
> ### 2. Bayesiana
>
> ```bash
> Rscript modelo_A_FE026_B018/01_bayesiana.R
> ```
>
> Deja su log en `exp/B018/BO_log.txt` y un archivo `COMPLETA` al terminar.
> Tiempo: entre 1 h 15 min y 1 h 22 min.
>
> `BO_log_corrido.txt` es el log de la optimización que se usó para la
> entrega. Para saltear este paso y producir con exactamente la misma
> configuración:
>
> ```bash
> mkdir -p exp/B018 && cp modelo_A_FE026_B018/BO_log_corrido.txt exp/B018/BO_log.txt && touch exp/B018/COMPLETA
> ```
>
> ### 3. Producción
>
> El modelo se entrena con 202103 a 202106 y predice 202108 una vez por
> semilla. Las semillas son los números primos de seis cifras en un orden
> aleatorio fijo (`set.seed(173207)`), repartidos en cuatro sublistas: la
> sublista k tiene las posiciones k, k + 4, k + 8, ... de esa lista. En la
> producción original cada sublista corrió en su propio proceso de R, que arma
> el dataset de LightGBM una vez y entrena sus semillas en orden, de la primera
> en adelante. La entrega reproduce ese esquema: si LightGBM usara la semilla
> del primer entrenamiento para construir los bins del dataset, el orden y la
> separación en procesos cambiarían el resultado.
>
> `semillas_A.csv` indica, para cada semilla que entra en la entrega, su
> sublista, su posición y el proceso en que se entrenó (un número mayor que 1
> indica que la producción se reinició en esa sublista). Las sublistas y
> procesos presentes se listan con:
>
> ```bash
> Rscript -e 'data.table::fread("modelo_A_FE026_B018/semillas_A.csv")[, .N, by = .(sublista, proceso)]'
> ```
>
> Para cada par (sublista, proceso) de la lista se corre un `Rscript` aparte;
> por ejemplo, sublista 1, proceso 1:
>
> ```bash
> Rscript modelo_A_FE026_B018/02_produccion.R 1 1
> ```
>
> Las sublistas son independientes entre sí y pueden correr en paralelo, en una
> o varias máquinas (cada una necesita el dataset y el log de la bayesiana).
> Cada semilla queda en `exp/P069/semillas/prob_<semilla>.csv.gz`; si un
> proceso se interrumpe, al relanzarlo saltea las semillas ya grabadas.
> Tiempo: entre 24 y 27 minutos por semilla. Con las cuatro sublistas en
> paralelo, la producción completa lleva del orden de (cantidad de semillas
> / 4) × 25 minutos; por ejemplo, unas 10 horas para 90 semillas.
>
> ### 4. Predicción final
>
> ```bash
> Rscript 02_prediccion_final.R
> ```
>
> Lee todas las semillas, descarta las que tienen predicciones idénticas a
> otra semilla (ocurre cuando dos semillas generan la misma semilla interna de
> LightGBM), promedia el resto por cliente y ordena los clientes de mayor a
> menor probabilidad. Tarda unos 3 minutos (medido en una computadora
> personal, con 83 semillas).
>
> ## Archivo final
>
> ```
> exp/entregas/<fecha_hora>_P069_prob/P069_prob_11750.csv
> ```
>
> Tiene los `numero_de_cliente` de los 11.750 clientes con mayor probabilidad,
> uno por línea, sin encabezado. En la misma carpeta quedan
> `probabilidades.csv.gz` (probabilidad de cada semilla y del semillerío, por
> cliente) y `resumen.txt` (semillas usadas y descartadas). La carpeta lleva la
> fecha y la hora de la corrida y nunca se sobrescribe.
>
> ## Semillas incluidas
>
> | Semillas en `semillas_A.csv` | Descartadas por predicciones idénticas | Usadas |
> |---|---|---|
> | 107 (4 sublistas, 7 procesos) | 1 (694327, idéntica a 316817) | 106 |
>
> ## Verificación
>
> Se verificó:
>
> - Dataset: FE026 construido con esta carpeta desde `competencia_01.csv.gz`
>   tiene la misma huella md5 que el usado en la producción
>   (175c5c33f47da426afeb25fdb29ce1c6).
> - Producción: en la misma máquina virtual que produjo la sublista 1, las dos
>   primeras semillas de esa sublista, entrenadas con esta carpeta y el log de
>   la optimización, dieron probabilidades idénticas byte a byte a las de la
>   producción original.
> - Lista de semillas: con el entrenamiento reemplazado por una simulación, la
>   producción entrena exactamente las semillas de cada sublista y proceso, en
>   orden, y se detiene si la lista no coincide con la sublista.
> - Predicción final: `02_prediccion_final.R` sobre las predicciones de la
>   producción da un archivo idéntico byte a byte al generado con el
>   procedimiento original.
>
> LightGBM es determinístico con `deterministic = TRUE`, `force_row_wise = TRUE`
> y una cantidad fija de hilos, pero en un procesador distinto puede dar
> diferencias mínimas. La reproducción exacta se verificó en máquinas virtuales
> e2-highmem-8.

### evaluacion_junio/LEEME.md

> # Evaluación en junio
>
> Código que midió el modelo en 202106: entrena el modelo de la entrega (FE026
> con la configuración de mayor AUC de la optimización) con 202103 y 202104,
> sin préstamos personales, con 20 semillas, y calcula la ganancia del
> semillerío y de cada semilla para cada cantidad de envíos.
> `curva_por_corte.R` calcula a partir de eso la ganancia promedio alrededor de
> cada corte. E079 es el identificador de esta evaluación.
>
> ## Cómo se corre
>
> Desde `evaluacion_junio/` (un archivo `.here` fija esta carpeta como raíz de
> las rutas):
>
> ```bash
> mkdir -p datasets exp/B018
> cp <ruta>/competencia_01.csv.gz datasets/
> cp ../modelo_A_FE026_B018/BO_log_corrido.txt exp/B018/BO_log.txt && touch exp/B018/COMPLETA
> Rscript corridas/E079.R
> Rscript curva_por_corte.R exp/E079/probabilidades_future.csv.gz exp/E079/curva_por_corte.csv
> ```
>
> `corridas/E079.R` construye FE026 si no existe (`datasets/FE026.csv.gz`) y
> deja en `exp/E079/` las ganancias por corte, la curva y las probabilidades
> por semilla.
>
> ## Tiempo
>
> Unos 12 minutos por semilla en una máquina virtual de 8 vCPU (20 semillas,
> unas 4 horas), más la construcción de FE026.
>
> ## Archivos
>
> | Archivo | Qué hace |
> |---|---|
> | `corridas/E079.R` | Lanza la evaluación: dataset FE026 y configuración de la optimización |
> | `corridas/junio_fe026.R` | Construye FE026 si no existe y renderiza el Rmd con los parámetros de la evaluación |
> | `corridas/junio_comun.R` | Esquema común: entrenamiento con 202103 y 202104, evaluación en 202106, 20 semillas, sin préstamos personales |
> | `rmd/03_experimento.Rmd` | Entrena las 20 semillas y calcula la ganancia por corte del semillerío y de cada semilla |
> | `R/evaluar_semillas_guardando.R`, `R/modelo.R`, `R/utils.R`, `R/experimentos.R` | Funciones que usa el Rmd |
> | `R/pipeline.R`, `R/fe.R`, `R/fe_FE026.R` | Funciones que cargan los scripts de la evaluación; `R/fe.R` es una biblioteca general de transformaciones y contiene también funciones que este modelo no usa |
> | `curva_por_corte.R` | Ganancia promedio alrededor de cada corte |

