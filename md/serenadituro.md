# Serena — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: SerenaDituro
- Repositorio: https://github.com/SerenaDituro/Competencia1_DMEyF_2026
- Link posteado: https://github.com/SerenaDituro/Competencia1_DMEyF_2026.git
- Commit: 31d13c4c481551b2ceb209675439bbf16817f729
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/serenadituro/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/serenadituro.json

## Resumen

La entrega tiene dos notebooks de R, un README y la carpeta exp/HTC1_E012 con el registro de una optimización bayesiana. C1_E012_modelo-MH-entrega.ipynb produce el archivo entregado: parte del dataset crudo, calcula la clase ternaria, pasa ccajas_depositos a NA en 202105, agrega lag 1, delta 1, lag 2 y delta 2 de cada variable numérica y reemplaza todas las variables por su rank dentro del mes con cero fijo. Con hiperparámetros escritos en el código (num_iterations 2891, num_leaves 1056, min_sum_hessian_in_leaf 0,0135, learning_rate 0,005, feature_fraction 0,5) entrena 5 modelos LightGBM con 202103–202104 para medir la ganancia en 202106 por corte, y después 20 modelos con 202103–202106 completos, sin submuestreo, uno por cada semilla de una lista fija. Promedia por cliente las 20 probabilidades de 202108 y escribe los 12.000 clientes de mayor probabilidad. C1_E012_con-rank-final_BO.ipynb contiene el mismo feature engineering y la optimización bayesiana (mlrMBO, validación cruzada de 5 folds sobre 202103–202105, métrica AUC) de la que, según el README, salen esos hiperparámetros; la optimización se cortó a las 16 evaluaciones.

**Qué entrega.** Un archivo de texto sin encabezado con 12.000 numero_de_cliente, uno por línea: los de mayor probabilidad promedio de los 20 modelos para 202108. Según el README el archivo es exp/C1_E012_entrega_MH/zulip/C1_E012_ensamble_20S_12000.csv. El archivo no está en el repositorio.

**Cómo se ejecuta.** Según el README y la celda 2 de la notebook de entrega: copiar competencia_01_crudo.csv (también .csv.gz o .zip) en ~/buckets/b1/datasets/ (la carpeta tiene que existir; si se usa otra carpeta base, cambiar carpeta_base en la primera celda de código) y correr todas las celdas de C1_E012_modelo-MH-entrega.ipynb en orden (Run All). La notebook genera la clase ternaria y el dataset con feature engineering si no existen, y si la corrida se corta retoma desde las probabilidades ya guardadas. El README indica que los hiperparámetros no se optimizan en esa notebook: vienen de C1_E012_con-rank-final_BO.ipynb, que también se ejecuta de inicio a fin con la misma entrada. La sección 'Cómo reproducir la entrega' del README dice que hay dos formas de correrlo y el texto de la sección termina en esa frase.

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: clase01 = 1 si clase_ternaria es BAJA+1 o BAJA+2 y 0 si es CONTINUA. La clase ternaria se calcula en la misma notebook a partir del dataset crudo.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** Sin submuestreo: PARAM$undersampling = 1.0 en la notebook de entrega y PARAM$trainingstrategy$undersampling = 1.0 en la de la optimización bayesiana. Se usan todos los registros CONTINUA.
- **Calidad de datos:** ccajas_depositos se pasa a NA en todos los registros de 202105, antes de calcular lags y deltas. No se observan otras correcciones en el código.
- **Drifting:** Rank por mes con cero fijo de todas las variables numéricas (originales, lags y deltas) salvo numero_de_cliente y foto_mes: dentro de cada mes los valores positivos se reemplazan por su rank dividido por la cantidad de positivos (quedan en (0, 1]) y los negativos por el rank de su valor absoluto, con signo negativo, dividido por la cantidad de negativos (quedan en [-1, 0)); ceros y NA no cambian. El rank reemplaza el valor de la columna, no agrega columnas. Según la salida guardada de la notebook de desarrollo se rankean 760 columnas en 6 meses.
- **Variables dentro del mes:** No se observa en el código.
- **Variables históricas:** Lag 1 y delta 1, lag 2 y delta 2 de cada variable numérica original; quedan en NA cuando el cliente no tiene el registro del mes correspondiente. Según la salida guardada de la notebook de desarrollo son 152 variables originales y el dataset con FE queda con 763 columnas.
- **Selección de variables:** No se observa en el código. Se usan como variables todas las columnas salvo clase_ternaria y clase01 (la lista incluye numero_de_cliente y foto_mes); son 762 según la salida guardada. La importancia de variables de cada modelo se graba en archivos y no se usa para filtrar.
- **Optimización de hiperparámetros:** Optimización bayesiana con mlrMBO en C1_E012_con-rank-final_BO.ipynb sobre num_iterations (64–4096), num_leaves (16–2048) y min_sum_hessian_in_leaf (1e-06–0,1), con el resto fijo (learning_rate 0,005, feature_fraction 0,5, min_data_in_leaf 0, max_bin 31). Cada evaluación es un lgb.cv de 5 folds estratificados sobre 202103–202105, métrica AUC, sin submuestreo. Está configurada con 12 puntos iniciales y 10 iteraciones bayesianas; según el README y la notebook se cortó a mano a las 16 evaluaciones (12 iniciales y 4 bayesianas) y se tomó el punto de mayor AUC: 0,943422 según BO_log_kfold5_auc.txt, evaluación 8. La notebook de entrega no optimiza: tiene esos valores escritos.
- **Hiperparámetros finales:** num_iterations 2891, num_leaves 1056, min_sum_hessian_in_leaf 0,013485676441086, learning_rate 0,005, feature_fraction 0,50, min_data_in_leaf 0, max_bin 31, max_depth -1, lambda_l1 0, lambda_l2 0, min_gain_to_split 0, bagging_fraction 1,0, boosting gbdt, objective binary, extra_trees FALSE, early_stopping 0, num_threads 4.
- **Semillas:** 20 números primos de 6 cifras escritos en el código (PARAM$semillas_20, de 325229 a 122921); según el comentario salen de set.seed(110017, kind = "L'Ecuyer-CMRG") y sample(primes::generate_primes(100000, 999999), 20). Cada modelo final usa una como seed; data_random_seed queda en 110017 en todos. El test en 202106 usa las primeras 5.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio por cliente de las probabilidades de los 20 modelos, que tienen los mismos hiperparámetros y distinta semilla. También se arman ensambles con los primeros 5, 10 y 15 modelos.
- **Corte:** Cantidad fija: PARAM$envios = 12000, escrito en la última celda de código, que verifica que esté entre 9.500 y 15.000. Se toman los primeros 12.000 clientes del ensamble de 20 modelos ordenado por probabilidad promedio. Además se generan archivos con cortes de 9.500 a 15.000 de a 500 para los ensambles de 5, 10, 15 y 20 modelos. La sección 1.3, cuyo texto dice que sirve para elegir el corte, calcula la ganancia en 202106 en esos mismos cortes e imprime el de ganancia máxima del ensamble de 5 semillas; el código no traslada ese valor a PARAM$envios. En la salida guardada de la notebook esa línea imprime 11000.
- **Validación:** Test en un mes posterior: entrena con 202103–202104 y mide en 202106 con las primeras 5 semillas. Calcula la ganancia (+1.072.500 por cada BAJA+2 y −27.500 por cada otro registro) de cada semilla, del promedio de las semillas y del ensamble en los cortes de 9.500 a 15.000, y la curva de ganancia acumulada cada 50 envíos hasta 20.000. Según la salida guardada de la notebook, la ganancia del ensamble en 202106 va de 377.850.000 (14.500 envíos) a 389.400.000 (11.000 envíos) y es 387.200.000 en 12.000. La optimización bayesiana mide AUC con validación cruzada de 5 folds estratificados sobre 202103–202105.
- **Salidas:** En ~/buckets/b1/datasets/: competencia_01.csv.gz (dataset con clase ternaria) y competencia_01_fe_naccajas_lag1_delta1_lag2_delta2_rankfinal.fst (dataset con FE). En ~/buckets/b1/exp/C1_E012_entrega_MH/ (el nombre sale de PARAM$experimento; el texto de la celda 2 nombra la carpeta C1_E012_entrega): test/ con prob_test_NN.csv, impo_test_NN.txt, ganancia_test_cortes.csv, curva_ganancia_test.csv, curva_ganancia_test.png e impo_test.txt; probabilidades/ con un archivo prob_ y uno impo_ por semilla; impo.txt; cuatro archivos prediccion_<experimento>_ensNN_202108.csv; zulip_cortes/ensNN/<corte>/ con 48 archivos (4 ensambles por 12 cortes); y zulip/C1_E012_ensamble_20S_12000.csv. La notebook de la optimización escribe en exp/HTC1_E012/: BO_eval_kfold5_auc.txt, BO_log_kfold5_auc.txt, bayesiana_kfold5_auc.RDATA, estado_C1_E012.txt y PARAM.yml. De todo esto el repositorio trae BO_eval_kfold5_auc.txt, BO_log_kfold5_auc.txt y PARAM.yml.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Validación cruzada (`validacion.validacion_cruzada`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: sí
- Entorno declarado: VM de Google Cloud con 8 vCPU y 64 GB de RAM y notebooks de R, según el README y las celdas de texto. Los paquetes se cargan por nombre y se instalan si faltan, sin versión. Los metadatos de las dos notebooks registran el kernel de R 4.6.1.

## Pasos del camino de la entrega

1. **Configuración y parámetros de la corrida.** La notebook de entrega define la carpeta base ~/buckets/b1, carga los paquetes y arma PARAM: entrenamiento final 202103–202106, predicción 202108, sin submuestreo, test con 202103–202104 contra 202106, 20 semillas primas fijas, ensambles de 5, 10, 15 y 20 modelos, cortes de 9.500 a 15.000 y los parámetros fijos de LightGBM. (`C1_E012_modelo-MH-entrega.ipynb` líneas 49–63; `C1_E012_modelo-MH-entrega.ipynb` líneas 70–137)
2. **Clase ternaria.** Si no existe el dataset con clase, lee el crudo y calcula clase_ternaria mirando si cada cliente aparece en el mes siguiente y en el subsiguiente: BAJA+1 si falta el siguiente, BAJA+2 si está el siguiente y falta el subsiguiente, CONTINUA en el resto de los períodos anteriores al anteúltimo. Graba competencia_01.csv.gz. Según la salida guardada de la notebook de desarrollo, el dataset tiene 983.061 filas, 155 columnas y los meses 202103 a 202108. (`C1_E012_modelo-MH-entrega.ipynb` líneas 224–226; `C1_E012_modelo-MH-entrega.ipynb` líneas 238–276)
3. **ccajas_depositos a NA en 202105.** Asigna NA a ccajas_depositos en todos los registros de 202105, antes de calcular lags y deltas. (`C1_E012_modelo-MH-entrega.ipynb` líneas 283–286)
4. **Lags y deltas de orden 1 y 2.** Para cada variable numérica original agrega el valor del mes anterior (_lag1) y la diferencia con él (_delta1), y lo mismo con el valor de dos meses atrás (_lag2, _delta2). Las filas sin el mes correspondiente del mismo cliente quedan en NA. (`C1_E012_modelo-MH-entrega.ipynb` líneas 293–309; `C1_E012_modelo-MH-entrega.ipynb` líneas 316–329)
5. **Rank por mes con cero fijo.** Reemplaza cada variable numérica (originales, lags y deltas, salvo numero_de_cliente y foto_mes) por su rank dentro de cada mes: positivos entre 0 y 1, negativos entre -1 y 0, ceros y NA sin cambios. (`C1_E012_modelo-MH-entrega.ipynb` líneas 188–195; `C1_E012_modelo-MH-entrega.ipynb` líneas 336–349)
6. **Grabado y lectura del dataset con FE.** Graba el dataset ordenado por mes en un archivo .fst. Las secciones siguientes leen de ese archivo sólo el rango de filas de los meses que usan. Si el .fst ya existe, las celdas de preprocesamiento no se ejecutan. (`C1_E012_modelo-MH-entrega.ipynb` líneas 355–362; `C1_E012_modelo-MH-entrega.ipynb` líneas 158–167)
7. **Optimización bayesiana (notebook de desarrollo).** Sobre el mismo dataset con FE, C1_E012_con-rank-final_BO.ipynb busca num_iterations, num_leaves y min_sum_hessian_in_leaf con mlrMBO. Cada punto se evalúa con lgb.cv de 5 folds estratificados sobre 202103–202105 y métrica AUC. Cada evaluación se agrega a BO_eval_kfold5_auc.txt. La última celda arma BO_log_kfold5_auc.txt con las 16 evaluaciones hechas, ordenadas por AUC, y escribe PARAM.yml. (`C1_E012_con-rank-final_BO.ipynb` líneas 484–502; `C1_E012_con-rank-final_BO.ipynb` líneas 669–717; `C1_E012_con-rank-final_BO.ipynb` líneas 855–923; `C1_E012_con-rank-final_BO.ipynb` líneas 926–953; `exp/HTC1_E012/BO_log_kfold5_auc.txt` líneas 1–17)
8. **Hiperparámetros escritos en la notebook de entrega.** La notebook de entrega tiene escritos num_iterations 2891, num_leaves 1056 y min_sum_hessian_in_leaf 0,013485676441086 y los combina con los parámetros fijos. Una celda de control busca esos valores en el registro de la optimización, si está disponible, e informa a qué evaluación corresponden y en qué puesto quedaron por AUC. (`C1_E012_modelo-MH-entrega.ipynb` líneas 382–413)
9. **Test en 202106 con 5 semillas.** Lee los meses 202103 a 202106 y 202108, arma la clase binaria y la lista de variables, y entrena un modelo por cada una de las primeras 5 semillas con 202103–202104 para predecir 202106. Guarda las probabilidades y la importancia de variables de cada modelo. (`C1_E012_modelo-MH-entrega.ipynb` líneas 420–448)
10. **Ganancia por corte y curva de ganancia.** Con las probabilidades de 202106 calcula la ganancia de cada semilla, del promedio de las semillas y del ensamble en cada corte de 9.500 a 15.000, imprime la tabla y el corte de ganancia máxima del ensamble, y grafica la curva de ganancia acumulada hasta 20.000 envíos. (`C1_E012_modelo-MH-entrega.ipynb` líneas 450–493)
11. **Entrenamiento de los 20 modelos finales.** Arma una sola vez el lgb.Dataset con 202103–202106 y la matriz de 202108. Entrena 20 modelos que sólo difieren en la semilla, predice 202108 con cada uno y guarda las probabilidades por semilla; las semillas que ya tienen archivo no se vuelven a entrenar. Al final promedia la importancia de variables de los modelos. (`C1_E012_modelo-MH-entrega.ipynb` líneas 514–527; `C1_E012_modelo-MH-entrega.ipynb` líneas 536–565)
12. **Ensambles y archivos por corte.** Para 5, 10, 15 y 20 modelos promedia las probabilidades por cliente, ordena de mayor a menor y escribe un archivo de numero_de_cliente por cada corte de 9.500 a 15.000. (`C1_E012_modelo-MH-entrega.ipynb` líneas 576–599)
13. **Archivo final.** Toma el ensamble de 20 modelos, corta en PARAM$envios = 12000 y escribe C1_E012_ensamble_20S_12000.csv sin encabezado. Vuelve a leer el archivo e informa la cantidad de filas y de identificadores distintos. (`C1_E012_modelo-MH-entrega.ipynb` líneas 608–619)

## Archivos

- `C1_E012_con-rank-final_BO.ipynb` · principal · Jupyter (R) · 953 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/serenadituro/C1_E012_con-rank-final_BO.ipynb.txt) — Notebook de R de desarrollo del experimento C1_E012: genera la clase ternaria y el dataset con feature engineering (mismos pasos que la notebook de entrega, activables por banderas) y corre la optimización bayesiana de num_iterations, num_leaves y min_sum_hessian_in_leaf con mlrMBO y validación cruzada de 5 folds. Según el README, de aquí salen los hiperparámetros de la entrega.
- `README.md` · explicacion · Markdown · 47 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/serenadituro/README.md.txt) — Presentación de la entrega: entorno (VM de Google Cloud con 8 vCPU y 64 GB de RAM), dónde copiar el dataset crudo, tabla con lo que hace cada notebook y cada archivo de exp/HTC1_E012, resumen del feature engineering y de la optimización bayesiana, origen de los hiperparámetros (optimización cortada a las 16 evaluaciones, punto de mayor AUC) y el envío final: experimento C1_E012, 20 modelos en el ensamble, 12.000 envíos.
- `C1_E012_modelo-MH-entrega.ipynb` · principal · Jupyter (R) · 619 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/serenadituro/C1_E012_modelo-MH-entrega.ipynb.txt) — Notebook de R que va del dataset crudo al archivo de envío: clase ternaria, feature engineering, test en 202106 con 5 semillas, 20 modelos LightGBM finales con hiperparámetros escritos en el código, ensambles por promedio y archivos de numero_de_cliente por corte.
- `exp/HTC1_E012/BO_eval_kfold5_auc.txt` · secundario · Texto · 17 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/serenadituro/exp/HTC1_E012/BO_eval_kfold5_auc.txt.txt) — Registro de la optimización bayesiana en orden de ejecución: 16 filas con fecha, número de evaluación, num_iterations, num_leaves, min_sum_hessian_in_leaf, AUC y minutos. Las fechas van del 9 al 10 de octubre de 2026, los AUC de 0,925776 a 0,943422 y la duración de cada evaluación de 4,6 a 113 minutos.
- `exp/HTC1_E012/PARAM.yml` · configuracion · YAML · 167 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/serenadituro/exp/HTC1_E012/PARAM.yml.txt) — Volcado en YAML de la lista PARAM de la notebook de la optimización bayesiana: experimento C1_E012, semilla 110017, meses (train 202103–202104, validate 202105, test 202106, train_final 202103–202106, future 202108), undersampling 1,0, parámetros fijos de LightGBM, rangos de búsqueda, banderas de FE y el resultado (num_iterations 2891, num_leaves 1056, min_sum_hessian_in_leaf 0,0134857, AUC 0,9434219, 16 evaluaciones). Incluye además semilla_kaggle 314159, una lista de cortes de 4.000 a 19.000 y pct_validate 0,3.
- `exp/HTC1_E012/BO_log_kfold5_auc.txt` · secundario · Texto · 17 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/serenadituro/exp/HTC1_E012/BO_log_kfold5_auc.txt.txt) — Las mismas 16 evaluaciones ordenadas por AUC descendente, con las columnas del camino de optimización de mlrMBO (tipo de punto, tiempo de ejecución, expected improvement, media y error estándar del modelo sustituto). 12 filas son del diseño inicial (initdesign) y 4 de la fase bayesiana (infill_ei). La primera fila es num_iterations 2891, num_leaves 1056, min_sum_hessian_in_leaf 0,013485676441086, AUC 0,943422 (evaluación 8, del diseño inicial).

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### C1_E012_con-rank-final_BO.ipynb

Notebook de R de desarrollo del experimento C1_E012: genera la clase ternaria y el dataset con feature engineering (mismos pasos que la notebook de entrega, activables por banderas) y corre la optimización bayesiana de num_iterations, num_leaves y min_sum_hessian_in_leaf con mlrMBO y validación cruzada de 5 folds. Según el README, de aquí salen los hiperparámetros de la entrega.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–17] Celdas de texto de presentación: un enlace 'Open in Colab' que apunta a
#   z494_TareaHogar_04.ipynb del repositorio dmecoyfin/dmeyf2026 y la descripción de la notebook: feature
#   engineering (ccajas_depositos en NA para 202105, lag1, delta1, lag2 y delta2, rank por mes con cero fijo) y
#   optimización bayesiana con la definición de z495, k-fold 5 estratificado sobre 202103–05, métrica AUC, sin
#   undersampling, 12 puntos iniciales y 10 iteraciones bayesianas.
#%% celda 1 [texto]
<a href="https://colab.research.google.com/github/dmecoyfin/dmeyf2026/blob/ensembles_2026/ensembles/z494_TareaHogar_04.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

#%% celda 2 [texto]
# Competencia 01 — Optimización Bayesiana
**Ejecución:** de inicio a fin (Run All). Única entrada: el dataset crudo `competencia_01_crudo.csv` (o `.csv.gz` / `.zip`) en `~/buckets/b1/datasets/` (la carpeta tiene que existir). Todo lo demás se lee si existe y se crea si no; si se corta, retoma desde los checkpoints.

**Feature Engineering:**
1. `ccajas_depositos` en NA para 202105.
2. `lag1`, `delta1`, `lag2`, `delta2` de todas las variables originales (escala original).
3. Rank por mes con cero fijo de TODAS las variables (originales, lags y deltas), salvo `numero_de_cliente`, `foto_mes` y `clase_ternaria`
<br>Archivo: `competencia_01_fe_naccajas_lag1_delta1_lag2_delta2_rankfinal.fst`.

**BO** — definición de z495 (Gustavo Pasquini) sin undersampling
* Rangos: `num_iterations` 64–4096, `num_leaves` 16–2048, `min_sum_hessian_in_leaf` 1e-06–0.1. Fijos: `learning_rate` 0.005, `feature_fraction` 0.5, `min_data_in_leaf` 0, `max_bin` 31.
* k-fold 5 estratificado (`lgb.cv`, `nfold = 5`, `stratified = TRUE`) sobre 202103–05, **métrica AUC**, **sin undersampling**.
* 12 puntos iniciales + 10 iteraciones bayesianas (22 evaluaciones).

# [Anotación · líneas 19–33] Fija el repositorio de CRAN, define carpeta_base como ~/buckets/b1, detiene la
#   ejecución si no existe datasets/, crea exp/ y cambia el directorio de trabajo a carpeta_base.
#%% celda 3 [texto]
### 01 Configuración

#%% celda 4 [texto]
#### 1.1 - Entorno de trabajo

#%% celda 5 [código]
# definir el path de trabajo La corrí en una VM de Google Cloud con 8 vCPU y 64 GB de RAM
options(repos = c(CRAN = "https://cloud.r-project.org"))   # para que install.packages no pida mirror
carpeta_base <- path.expand("~/buckets/b1")
# datasets/ TIENE que existir: de ahi se lee el dataset crudo (unica entrada). Todo lo demas se crea si falta.
if (!dir.exists(file.path(carpeta_base, "datasets")))
  stop("No existe la carpeta ", file.path(carpeta_base, "datasets"), ": crearla y copiar ahi el dataset crudo")
dir.create(file.path(carpeta_base, "exp"), showWarnings = FALSE, recursive = TRUE)
setwd(carpeta_base)

# [Anotación · líneas 35–76] Carga fst, data.table y R.utils. Arma la lista CFG con las rutas del dataset
#   crudo (.csv, .csv.gz o .zip, el primero que exista), del dataset con clase y de la carpeta de experimentos;
#   los cuatro pasos de feature engineering como banderas (todas en TRUE) y dos banderas para forzar la
#   regeneración (en FALSE). El nombre del archivo .fst con FE se compone con un sufijo por cada bandera activa.
#%% celda 6 [texto]
#### 1.2 - Archivos y flags de preprocesamiento
Las secciones 02 y 03 solo se ejecutan si el archivo correspondiente no existe (o si se fuerza la regeneración).
<br>El nombre del archivo con FE se arma a partir de los flags, así cada combinación queda en su propio archivo. Se guarda en `.fst`: se lee en segundos y solo los meses que se usan.

#%% celda 7 [código]
# fst: formato binario, lectura rapida y por rango de filas (no descomprime un .csv.gz de varios GB)
if (!require("fst")) install.packages("fst")
require("fst")
if (!require("data.table")) install.packages("data.table")
require("data.table")
if (!require("R.utils")) install.packages("R.utils")   # fread / fwrite de .csv.gz
require("R.utils")

CFG <- list()
CFG$carpeta_datasets <- file.path(carpeta_base, "datasets")
# dataset crudo: UNICO archivo de entrada. Se acepta .csv, .csv.gz o .zip (el primero que exista)
crudos <- file.path(CFG$carpeta_datasets, paste0("competencia_01_crudo", c(".csv", ".csv.gz", ".zip")))
CFG$archivo_crudo <- if (any(file.exists(crudos))) crudos[file.exists(crudos)][1] else crudos[1]
rm(crudos)
CFG$carpeta_exp <- file.path(carpeta_base, "exp")
dir.create(CFG$carpeta_exp, showWarnings = FALSE, recursive = TRUE)
CFG$archivo_clase <- file.path(CFG$carpeta_datasets, "competencia_01.csv.gz")

# flags de feature engineering: TRUE = se aplica el paso
CFG$fe <- list(
  na_ccajas_202105 = TRUE,   # 1) ccajas_depositos en NA para 202105 (antes de calcular lags)
  lag1_delta1      = TRUE,   # 2) lag1 y delta1 de las variables originales
  lag2_delta2      = TRUE,   #    lag2 y delta2 de las variables originales
  rank_final       = TRUE    # 3) DESPUES de los lags: rank por mes con cero fijo de TODAS las variables
                             #    (originales, lags y deltas) salvo numero_de_cliente, foto_mes y clase_ternaria
)

# forzar regeneracion (por ejemplo si se modifico el codigo del FE sin cambiar los flags)
CFG$regenerar_clase <- FALSE
CFG$regenerar_fe    <- FALSE

# nombre del archivo con FE segun los flags activos
sufijos <- c(na_ccajas_202105 = "naccajas", lag1_delta1 = "lag1_delta1", lag2_delta2 = "lag2_delta2", rank_final = "rankfinal")
activos <- names(CFG$fe)[unlist(CFG$fe)]
CFG$archivo_fe <- file.path(CFG$carpeta_datasets, paste0(
  "competencia_01_fe_", if (length(activos)) paste(sufijos[activos], collapse = "_") else "sin_fe", ".fst"))

# [Anotación · líneas 78–104] fe_valido devuelve FALSE si el .fst no existe y, si existe, compara por nombre
#   de columna (sufijos _delta1, _delta2 y _rank) lo que contiene con lo que piden las banderas. Con eso decide
#   si en esta corrida hay que generar el FE y la clase, detiene la ejecución si hace falta el crudo y no está,
#   e imprime qué se va a generar.
# si el archivo con FE existe, verifico que sus columnas coincidan con los flags (lee solo los metadatos del .fst)
fe_valido <- function(archivo, flags) {
  if (!file.exists(archivo)) return(FALSE)
  cols <- metadata_fst(archivo)$columnNames
  tiene <- c(lag1_delta1 = any(grepl("_delta1$", cols)), lag2_delta2 = any(grepl("_delta2$", cols)),
             rank_monetarias = any(grepl("_rank$", cols)))
  esperado <- c(lag1_delta1 = isTRUE(flags$lag1_delta1), lag2_delta2 = isTRUE(flags$lag2_delta2),
                # con rank_reemplaza no hay columnas _rank (el rank queda con el nombre original)
                rank_monetarias = isTRUE(flags$rank_monetarias) && !isTRUE(flags$rank_reemplaza))
  # el NA de ccajas_depositos y el rank que reemplaza no se ven en las columnas: quedan identificados por el nombre del archivo
  ok <- identical(unname(tiene), unname(esperado))
  if (!ok) warning("Las columnas de ", basename(archivo), " no coinciden con los flags: se regenera")
  ok
}

# que hay que hacer en esta corrida
CFG$hacer_fe    <- CFG$regenerar_fe || CFG$regenerar_clase || !fe_valido(CFG$archivo_fe, CFG$fe)
CFG$hacer_clase <- CFG$regenerar_clase || (CFG$hacer_fe && !file.exists(CFG$archivo_clase))
if (CFG$hacer_clase && !file.exists(CFG$archivo_crudo))
  stop("Falta el dataset crudo: copiar competencia_01_crudo.csv (o .csv.gz / .zip) en ", CFG$carpeta_datasets)
cat("Dataset crudo:", CFG$archivo_crudo, "| existe:", file.exists(CFG$archivo_crudo), "\n")

rm(sufijos, activos, fe_valido)

cat("Generar clase_ternaria:", CFG$hacer_clase, "\n")
cat("Generar feature engineering:", CFG$hacer_fe, "\n")
cat("Archivo con FE:", CFG$archivo_fe, "\n")

# [Anotación · líneas 106–179] Si corresponde, lee el dataset crudo (descomprimiendo el .zip en una carpeta
#   temporal) y calcula clase_ternaria con el mismo procedimiento que la notebook de entrega: período
#   consecutivo por cliente, los dos períodos siguientes, CONTINUA para los períodos anteriores al anteúltimo,
#   BAJA+1 si falta el mes siguiente y BAJA+2 si está el siguiente y falta el subsiguiente. Graba
#   competencia_01.csv.gz. Si la clase ya existe y hay que rehacer el FE, la lee. La última celda muestra la
#   cantidad de registros por mes y clase.
#%% celda 8 [texto]
### 02 Generación de la clase_ternaria

#%% celda 9 [código]
require( "data.table" )

if (CFG$hacer_clase) {

  # leo el dataset crudo
  # descomprimo el .zip en el disco local de la VM (no en el bucket) y lo leo
  if (grepl("\\.zip$", CFG$archivo_crudo)) {
    # .zip: se descomprime al disco local de la VM (no en el bucket)
    csv_local <- utils::unzip(CFG$archivo_crudo, exdir = tempdir())
    dataset <- fread(csv_local[grepl("\\.csv$", csv_local)][1])
    unlink(csv_local)
  } else {
    dataset <- fread(CFG$archivo_crudo)   # .csv o .csv.gz
  }
  cat("Dataset crudo leido:", CFG$archivo_crudo, "|", nrow(dataset), "filas x", ncol(dataset), "columnas\n")

  # calculo el periodo0 consecutivo
  dsimple <- dataset[, list(
      "pos" = .I,
      numero_de_cliente,
      periodo0 = as.integer(foto_mes/100)*12 +  foto_mes%%100 ) ]

  # ordeno
  setorder( dsimple, numero_de_cliente, periodo0 )

  # calculo topes
  periodo_ultimo <- dsimple[, max(periodo0) ]
  periodo_anteultimo <- periodo_ultimo - 1

  # calculo los leads de orden 1 y 2
  dsimple[, c("periodo1", "periodo2") :=
      shift(periodo0, n=1:2, fill=NA, type="lead"),  numero_de_cliente ]

  # assign most common class values = "CONTINUA"
  dsimple[ periodo0 < periodo_anteultimo, clase_ternaria := "CONTINUA" ]

  # calculo BAJA+1
  dsimple[ periodo0 < periodo_ultimo &
      ( is.na(periodo1) | periodo0 + 1 < periodo1 ),
      clase_ternaria := "BAJA+1" ]

  # calculo BAJA+2
  dsimple[ periodo0 < periodo_anteultimo & (periodo0+1 == periodo1 )
      & ( is.na(periodo2) | periodo0 + 2 < periodo2 ),
      clase_ternaria := "BAJA+2" ]

  # pego el resultado en el dataset original y grabo
  setorder( dsimple, pos )
  dataset[, clase_ternaria := dsimple$clase_ternaria ]

  fwrite( dataset, file = CFG$archivo_clase, sep = "," )
  cat("clase_ternaria generada y guardada en:", CFG$archivo_clase, "\n")

  # libero memoria
  rm(dsimple, periodo_ultimo, periodo_anteultimo)
  gc(full = TRUE, verbose = FALSE)

} else if (CFG$hacer_fe) {

  # la clase ya existe: la leo solo porque hay que rehacer el FE
  dataset <- fread(CFG$archivo_clase)
  cat("clase_ternaria leida desde:", CFG$archivo_clase, "\n")

} else {
  cat("Se omite la seccion 02: ya existe el dataset con FE\n", CFG$archivo_fe, "\n")
}

#%% celda 10 [código]
# control de la clase (keyby no reordena el dataset)
if (exists("dataset")) dataset[, .N, keyby = list(foto_mes, clase_ternaria)]

# [Anotación · líneas 181–204] Pasa el dataset a la variable dataset_fe para la sección de FE. mostrar_fe
#   imprime, después de cada paso, las dimensiones de la tabla, su tamaño en GB, la cantidad de columnas nuevas
#   y las primeras filas de hasta 10 de ellas.
#%% celda 11 [texto]
### 03 Feature Engineering

#%% celda 12 [código]
if (CFG$hacer_fe) {
  dataset_fe <- dataset
  rm(dataset)
  gc(full = TRUE, verbose = FALSE)
  cat(nrow(dataset_fe), "filas x", ncol(dataset_fe), "columnas\n")
} else {
  cat("Se omite la seccion 03: se usara", CFG$archivo_fe, "\n")
}

#%% celda 13 [código]
mostrar_fe <- function(dt, nuevas, titulo, ver = head(nuevas, 10L), n = 5L, filas = NULL) {
  cat("\n=====", titulo, "=====\n")
  cat("Dimensiones:", format(nrow(dt), big.mark = ".", decimal.mark = ","), "filas x", ncol(dt),
      "columnas |", round(as.numeric(object.size(dt)) / 1024^3, 2), "GB\n")
  cat("Columnas nuevas/modificadas en este paso:", length(nuevas), "\n")
  idx <- if (is.null(filas)) seq_len(min(n, nrow(dt))) else head(which(filas), n)
  print(dt[idx, unique(c("numero_de_cliente", "foto_mes", ver)), with = FALSE])
  if (length(ver) < length(nuevas)) cat("(se muestran", length(ver), "de", length(nuevas), "columnas)\n")
  invisible(NULL)
}

# [Anotación · líneas 206–221] Si la bandera na_ccajas_202105 está activa, muestra el resumen de
#   ccajas_depositos en 202105, la pasa a NA en ese mes e imprime cuántos registros quedan en NA.
#%% celda 14 [texto]
#### 03.0 ccajas_depositos en NA para 202105
Corrección de los datos de base: se pone en NA **antes** de calcular los lags

#%% celda 15 [código]
if (CFG$hacer_fe && isTRUE(CFG$fe$na_ccajas_202105)) {
  stopifnot("ccajas_depositos" %in% names(dataset_fe))
  cat("ccajas_depositos en 202105 antes:\n")
  print(summary(dataset_fe[foto_mes == 202105, ccajas_depositos]))

  # data.table convierte NA al tipo de la columna (integer o numeric)
  dataset_fe[foto_mes == 202105, ccajas_depositos := NA]

  cat("Registros de 202105 con ccajas_depositos NA:", dataset_fe[foto_mes == 202105, sum(is.na(ccajas_depositos))],
      "de", dataset_fe[foto_mes == 202105, .N], "\n")
} else cat("NA ccajas_depositos 202105: se omite\n")

# [Anotación · líneas 223–262] Ordena por cliente y mes, toma las columnas numéricas (sin numero_de_cliente,
#   foto_mes ni las terminadas en _rank) y, con columnas auxiliares de período y cliente anterior, marca las
#   filas sin mes anterior consecutivo. Para cada variable agrega _lag1 (valor del mes anterior, NA en las filas
#   marcadas) y _delta1 (valor actual menos el anterior). Borra las columnas auxiliares y muestra el resultado
#   con mostrar_fe.
#%% celda 16 [texto]
#### 03.1 Lag1 y Delta1

#%% celda 17 [código]
if (CFG$hacer_fe && isTRUE(CFG$fe$lag1_delta1)) {

  # ---- Feature Engineering: lag1 y delta1 de todas las variables numericas originales ----
  setorder(dataset_fe, numero_de_cliente, foto_mes)

  cols_excluir <- c("numero_de_cliente", "foto_mes", "clase_ternaria")
  cols_fe <- setdiff(names(dataset_fe)[sapply(dataset_fe, is.numeric)], cols_excluir)
  cols_fe <- cols_fe[!grepl("_rank$", cols_fe)]   # en modo "agrega", las columnas _rank no se lagean

  # periodo consecutivo para detectar meses faltantes
  dataset_fe[, periodo0     := as.integer(foto_mes / 100) * 12L + foto_mes %% 100L]
  dataset_fe[, periodo_prev := shift(periodo0, 1L, type = "lag")]
  dataset_fe[, cliente_prev := shift(numero_de_cliente, 1L, type = "lag")]

  ok <- dataset_fe[, numero_de_cliente == cliente_prev & (periodo0 - periodo_prev) == 1L]
  ok[is.na(ok)] <- FALSE
  idx_sin_lag <- which(!ok)

  for (col in cols_fe) {
    v <- shift(dataset_fe[[col]], 1L, type = "lag")
    v[idx_sin_lag] <- NA
    set(dataset_fe, j = paste0(col, "_lag1"),   value = v)
    set(dataset_fe, j = paste0(col, "_delta1"), value = dataset_fe[[col]] - v)
  }

  dataset_fe[, c("periodo0", "periodo_prev", "cliente_prev") := NULL]
  cat("Columnas numéricas a aplicar lag1 y delta1:", length(cols_fe), "| Columnas totales del dataset:", ncol(dataset_fe), "\n")

  nuevas_lag <- unlist(lapply(cols_fe, function(col) paste0(col, c("_lag1", "_delta1"))))
  mostrar_fe(dataset_fe, nuevas_lag, "LAG1 / DELTA1")

  # libero objetos auxiliares
  rm(v, ok, idx_sin_lag, nuevas_lag)
  gc(full = TRUE, verbose = FALSE)

} else cat("Lag1 / Delta1: se omite\n")

# [Anotación · líneas 264–298] Sobre las variables originales (excluye las terminadas en _lag1, _delta1,
#   _lag2, _delta2 o _rank) agrega _lag2 y _delta2 con un desplazamiento de dos filas, dejando NA cuando el
#   registro de dos posiciones atrás no es del mismo cliente o no está exactamente dos meses antes.
#%% celda 18 [texto]
#### 03.2 Lag2 y Delta2 (sobre las variables originales)

#%% celda 19 [código]
if (CFG$hacer_fe && isTRUE(CFG$fe$lag2_delta2)) {

  # ---- Feature Engineering: lag2 y delta2 de las variables numericas ORIGINALES ----
  setorder(dataset_fe, numero_de_cliente, foto_mes)

  cols_excluir <- c("numero_de_cliente", "foto_mes", "clase_ternaria")
  cols_orig <- names(dataset_fe)[sapply(dataset_fe, is.numeric)]
  cols_orig <- setdiff(cols_orig[!grepl("_(lag1|delta1|lag2|delta2|rank)$", cols_orig)], cols_excluir)

  periodo0 <- as.integer(dataset_fe$foto_mes / 100) * 12L + dataset_fe$foto_mes %% 100L
  ok <- dataset_fe$numero_de_cliente == shift(dataset_fe$numero_de_cliente, 2L, type = "lag") &
        (periodo0 - shift(periodo0, 2L, type = "lag")) == 2L
  idx_sin_lag2 <- which(is.na(ok) | !ok)
  rm(periodo0, ok)

  for (col in cols_orig) {
    v <- shift(dataset_fe[[col]], 2L, type = "lag")
    v[idx_sin_lag2] <- NA
    set(dataset_fe, j = paste0(col, "_lag2"),   value = v)
    set(dataset_fe, j = paste0(col, "_delta2"), value = dataset_fe[[col]] - v)
  }

  cat("Columnas numericas a aplicar lag2 y delta2:", length(cols_orig), "| Columnas totales del dataset:", ncol(dataset_fe), "\n")
  nuevas_lag2 <- unlist(lapply(cols_orig, function(col) paste0(col, c("_lag2", "_delta2"))))
  mostrar_fe(dataset_fe, nuevas_lag2, "LAG2 / DELTA2")

  # libero objetos auxiliares
  rm(v, idx_sin_lag2, nuevas_lag2, cols_orig)
  gc(full = TRUE, verbose = FALSE)

} else cat("Lag2 / Delta2: se omite\n")

# [Anotación · líneas 300–341] Define rank_mes, con la misma lógica que rank_cero_fijo de la notebook de
#   entrega (positivos a (0, 1], negativos a [-1, 0), ceros y NA sin cambios), y la aplica a todas las columnas
#   numéricas salvo numero_de_cliente y foto_mes, mes por mes y columna por columna, reemplazando el valor
#   original. Informa el avance cada 100 columnas con el tiempo transcurrido.
#%% celda 20 [texto]
#### 03.3 Rank por mes con cero fijo de TODAS las variables
Para cada variable (originales, lags y deltas), por separado dentro de cada mes

#%% celda 21 [código]
if (CFG$hacer_fe && isTRUE(CFG$fe$rank_final)) {

  t0_rank <- Sys.time()
  cols_rank <- setdiff(names(dataset_fe), c("numero_de_cliente", "foto_mes", "clase_ternaria"))
  cols_rank <- cols_rank[vapply(cols_rank, function(cn) is.numeric(dataset_fe[[cn]]), logical(1))]

  rank_mes <- function(x) {
    out <- x
    pos <- !is.na(x) & x > 0
    neg <- !is.na(x) & x < 0
    if (any(pos)) out[pos] <-  frank( x[pos], ties.method = "average") / sum(pos)
    if (any(neg)) out[neg] <- -frank(-x[neg], ties.method = "average") / sum(neg)
    out
  }

  # columna por columna y mes por mes: no duplica el dataset
  idx_mes <- split(seq_len(nrow(dataset_fe)), dataset_fe$foto_mes)
  cat("Rank con cero fijo:", length(cols_rank), "columnas x", length(idx_mes), "meses\n")
  for (k in seq_along(cols_rank)) {
    v <- as.numeric(dataset_fe[[cols_rank[k]]])
    for (ix in idx_mes) v[ix] <- rank_mes(v[ix])
    set(dataset_fe, j = cols_rank[k], value = v)
    if (k %% 100 == 0 || k == length(cols_rank)) {
      cat(sprintf("  [%s] rankeadas %d de %d columnas (%.0f%%) | %.1f min\n", format(Sys.time(), "%H:%M:%S"),
                  k, length(cols_rank), 100 * k / length(cols_rank), as.numeric(difftime(Sys.time(), t0_rank, units = "mins"))))
      flush.console()
      gc(verbose = FALSE)
    }
  }

  cat("Rank final listo:", length(cols_rank), "columnas rankeadas por mes | columnas del dataset:", ncol(dataset_fe), "\n")
  mostrar_fe(dataset_fe, head(cols_rank, 30), "RANK FINAL (todas las variables)")

  rm(cols_rank, idx_mes, v, k, t0_rank)
  gc(full = TRUE, verbose = FALSE)

} else cat("Rank final: se omite\n")

# [Anotación · líneas 343–353] Ordena por foto_mes y numero_de_cliente, graba el dataset en .fst con
#   compresión 50 y lo borra de memoria.
#%% celda 22 [código]
if (CFG$hacer_fe) {
  setorder(dataset_fe, foto_mes, numero_de_cliente)

  write_fst(dataset_fe, CFG$archivo_fe, compress = 50)
  cat("Guardado:", nrow(dataset_fe), "filas x", ncol(dataset_fe), "columnas en", CFG$archivo_fe, "\n")

  # libero: la seccion 04 vuelve a leer solo los meses necesarios (con .fst tarda segundos)
  rm(dataset_fe)
  gc(full = TRUE, verbose = FALSE)
}

# [Anotación · líneas 355–415] Imprime la fecha y hora, borra todos los objetos del ambiente salvo CFG y carga
#   las librerías de la sección de optimización, instalando las que falten: data.table, fst, parallel, R.utils,
#   primes, utils, rlist, yaml, lightgbm, DiceKriging, mlrMBO, ggplot2, scales y jsonlite.
#%% celda 23 [texto]
### 04 Optimización de Hiperparámetros

#%% celda 24 [texto]
#### 4.1 Inicio

#%% celda 25 [texto]
limpio el ambiente de R

#%% celda 26 [código]
format(Sys.time(), "%a %b %d %X %Y")

#%% celda 27 [código]
# limpio la memoria, conservando solo la configuracion de archivos
rm(list = setdiff(ls(all.names = TRUE), "CFG"))
gc(full = TRUE, verbose = FALSE)

#%% celda 28 [texto]
#### 4.2 Carga de Librerias

#%% celda 29 [código]
# cargo las librerias que necesito (se instalan si faltan)
if( !require("data.table") ) install.packages("data.table")
require("data.table")

if( !require("fst") ) install.packages("fst")
require("fst")
require("parallel")

if(!require("R.utils")) install.packages("R.utils")
require("R.utils")

if( !require("primes") ) install.packages("primes")
require("primes")

if( !require("utils") ) install.packages("utils")
require("utils")

if( !require("rlist") ) install.packages("rlist")
require("rlist")

if( !require("yaml")) install.packages("yaml")
require("yaml")

if( !require("lightgbm") ) install.packages("lightgbm")
require("lightgbm")

if( !require("DiceKriging") ) install.packages("DiceKriging")
require("DiceKriging")

if( !require("mlrMBO") ) install.packages("mlrMBO")
require("mlrMBO")

if( !require("ggplot2") ) install.packages("ggplot2")
require("ggplot2")

if( !require("scales") ) install.packages("scales")
require("scales")

if( !require("jsonlite") ) install.packages("jsonlite")
require("jsonlite")

# [Anotación · líneas 417–435] Inicia PARAM con experimento C1_E012 y semilla_primigenia 110017. Define train
#   = 202103 y 202104, validate = 202105, train_test = 202103 y 202104, test = 202106 y undersampling 1,0.
#%% celda 30 [texto]
#### 4.3 Definición de Hiperparámetros

#%% celda 31 [código]
PARAM <- list()
PARAM$experimento <- "C1_E012"   
PARAM$semilla_primigenia <- 110017

#%% celda 32 [código]
# Esquema: BO entrena 202103-04 y valida en 202105
PARAM$train <- c(202103, 202104)      # entrenamiento de la BO
PARAM$validate <- c(202105)           # validacion de la BO (AUC)

# testing en mes conocido: entreno con train_test y mido ganancia en test
PARAM$train_test <- c(202103, 202104)
PARAM$test <- c(202106)   # ultimo mes con clase_ternaria completa

#%% celda 33 [código]
PARAM$trainingstrategy$undersampling <- 1.0   # SIN undersampling

# [Anotación · líneas 437–481] Fija 5 folds para la validación cruzada y la lista de parámetros de LightGBM
#   que no se optimizan (gbdt, objective binary, metric auc, max_bin 31, min_data_in_leaf 0, feature_fraction
#   0,50, learning_rate 0,005, bagging_fraction 1,0, lambda_l1 y lambda_l2 en 0). num_iterations, num_leaves y
#   min_sum_hessian_in_leaf figuran con valores iniciales que la optimización reemplaza.
#%% celda 34 [código]
# Parametros LightGBM
PARAM$hyperparametertuning$xval_folds <- 5        # BO con k-fold 5 estratificado (nfold + stratified)

# parametros fijos del LightGBM (definicion de z495, Gustavo Pasquini)
PARAM$lgbm$param_fijos <-  list(
  boosting= "gbdt", 
  objective= "binary",
  metric= "auc",
  feature_pre_filter= FALSE,
  first_metric_only= FALSE,
  boost_from_average= TRUE,
  force_row_wise= TRUE,
  deterministic= TRUE,
  verbosity= -100,

  seed= PARAM$semilla_primigenia,

  max_depth= -1L,
  min_gain_to_split= 0,
  lambda_l1= 0.0,
  lambda_l2= 0.0,
  max_bin= 31L,

  bagging_fraction= 1.0,
  pos_bagging_fraction= 1.0,
  neg_bagging_fraction= 1.0,
  is_unbalance= FALSE,
  scale_pos_weight= 1.0,

  drop_rate= 0.1,
  max_drop= 50,
  skip_drop= 0.5,

  extra_trees= FALSE,

  early_stopping= 0,
  min_data_in_leaf= 0,     # fijo, esto es FUNDAMENTAL
  feature_fraction= 0.50,  # fijo
  learning_rate= 0.005,    # fijo

  num_iterations= 20000,     # se modificara
  num_leaves= 1024,          # se modificara
  min_sum_hessian_in_leaf= 1e-06  # se modificara
)

# [Anotación · líneas 483–510] Define el espacio de búsqueda: num_iterations entero entre 64 y 4096,
#   num_leaves entero entre 16 y 2048 y min_sum_hessian_in_leaf real entre 1e-06 y 0,1. Arma PARAM$bo con los
#   meses de la optimización (202103, 202104 y 202105, la unión de train y validate), 10 iteraciones, 12 puntos
#   iniciales y los nombres de los archivos de estado y de registro. Deja en FALSE la opción de reutilizar los
#   hiperparámetros de otro experimento (bo_origen = C1_E010v2).
#%% celda 35 [código]
# Bordes de los hiperparametros de la BO: rangos de z495 (Gustavo Pasquini)
hs_ajustado <- makeParamSet(
  makeIntegerParam("num_iterations", lower= 64L, upper= 4096L),
  makeIntegerParam("num_leaves", lower= 16L, upper= 2048L),
  makeNumericParam("min_sum_hessian_in_leaf", lower= 1e-06, upper= 0.1)  # min_data_in_leaf queda fijo en CERO
)

# BO: k-fold 5 estratificado (nfold + stratified) sobre 202103, 202104 y 202105, SIN undersampling, metrica AUC.
# diseno inicial: el de mlrMBO por defecto (4 x 3 parametros = 12 puntos al azar) + 10 iteraciones bayesianas = 22 evaluaciones
PARAM$bo <- list(
  nombre      = "bo",
  meses       = c(PARAM$train, PARAM$validate),
  iteraciones = 10,
  n_inicial   = 12,   
  hs          = hs_ajustado,
  kbayesiana  = "bayesiana_kfold5_auc.RDATA",   # estado de mlrMBO (para mboContinue)
  log         = "BO_log_kfold5_auc.txt",        # resultado final de la BO (como en el script)
  log_eval    = "BO_eval_kfold5_auc.txt"        # una linea por evaluacion (checkpoint)
)
rm(hs_ajustado)
PARAM$bo_probar_tiempo <- FALSE   # TRUE = correr una evaluacion de prueba (system.time) antes de la BO

# ---- reutilizar los hiperparametros de otro experimento (no se corre la BO) ----
# TRUE : toma el mejor punto de BO_log_kfold5_auc.txt (o BO_eval_kfold5_auc.txt) de la carpeta HT<PARAM$bo_origen>
# FALSE: corre la BO de esta notebook (si ya termino, se toma de su propio log)
PARAM$bo_reutilizar_origen <- FALSE
PARAM$bo_origen <- "C1_E010v2"

# [Anotación · líneas 512–562] Tres funciones: particionar agrega una columna fold con una partición
#   estratificada; realidad_inicializar separa un mes en proporción 3 y 7 por clase con PARAM$semilla_kaggle;
#   realidad_evaluar calcula la ganancia (1.072.500 por BAJA+2, −27.500 por el resto) de una predicción en cada
#   parte y en el total. En las celdas de esta notebook no hay llamadas a realidad_inicializar ni a
#   realidad_evaluar.
#%% celda 36 [código]
# particionar agrega una columna llamada fold a un dataset
#   que consiste en una particion estratificada segun agrupa
# particionar( data=dataset, division=c(70,30),
#  agrupa=clase_ternaria, seed=semilla)   crea una particion 70, 30

particionar <- function(data, division, agrupa= "", campo= "fold", start= 1, seed= NA) {
  if (!is.na(seed)) set.seed(seed, "L'Ecuyer-CMRG")

  bloque <- unlist(mapply(
    function(x, y) {rep(y, x)},division, seq(from= start, length.out= length(division))))

  data[, (campo) := sample(rep(bloque,ceiling(.N / length(bloque))))[1:.N],by= agrupa]
}

#%% celda 37 [código]
# iniciliazo el dataset de realidad, para medir ganancia
realidad_inicializar <- function( pfuture, pparam) {

  # datos para verificar la ganancia
  drealidad <- pfuture[, list(numero_de_cliente, foto_mes, clase_ternaria)]

  particionar(drealidad,
    division= c(3, 7),
    agrupa= "clase_ternaria",
    seed= PARAM$semilla_kaggle
  )

  return( drealidad )
}

#%% celda 38 [código]
# evaluo ganancia en los datos de la realidad

realidad_evaluar <- function( prealidad, pprediccion) {

  prealidad[ pprediccion,
    on= c("numero_de_cliente", "foto_mes"),
    predicted:= i.Predicted
  ]

  tbl <- prealidad[, list("qty"=.N), list(fold, predicted, clase_ternaria)]

  res <- list()
  res$public  <- tbl[fold==1 & predicted==1L, sum(qty*ifelse(clase_ternaria=="BAJA+2", 1072500, -27500))]/0.3
  res$private <- tbl[fold==2 & predicted==1L, sum(qty*ifelse(clase_ternaria=="BAJA+2", 1072500, -27500))]/0.7
  res$total <- tbl[predicted==1L, sum(qty*ifelse(clase_ternaria=="BAJA+2", 1072500, -27500))]

  prealidad[, predicted:=NULL]
  return( res )
}

# [Anotación · líneas 564–627] Funciones de manejo de memoria y de avance: filtrar_filas_bajo_memoria (copia
#   las filas pedidas columna por columna), matriz_bajo_memoria (matriz numérica de un subconjunto de filas y
#   columnas), predecir_por_bloques (predice de a 50.000 filas), leer_meses_fst (lee del .fst sólo los meses
#   pedidos), reportar (imprime un mensaje con fecha y hora y lo agrega a estado_<experimento>.txt en la carpeta
#   del experimento) y fmt_min (formatea minutos u horas).
#%% celda 39 [texto]
#### Funciones de manejo de memoria
Se usan índices de filas en lugar de copiar `dataset` (`dataset[foto_mes %in% ...]` duplica todas las columnas), y las matrices para LightGBM se arman columna por columna.

#%% celda 40 [código]
# filtra filas SIN duplicar el data.table (copia columna por columna y borra la original)
filtrar_filas_bajo_memoria <- function(dt, filas) {
  cols <- copy(names(dt))
  out <- data.table(.fila_tmp = seq_along(filas))
  for (k in seq_along(cols)) {
    set(out, j = cols[k], value = dt[[cols[k]]][filas])
    set(dt, j = cols[k], value = NULL)
    if (k %% 50 == 0) gc(verbose = FALSE)
  }
  out[, .fila_tmp := NULL]
  gc(verbose = FALSE)
  out
}

# matriz para LightGBM sin pasar por un data.table intermedio
# (equivale a data.matrix(dataset[filas, campos, with = FALSE]) pero sin la copia intermedia)
matriz_bajo_memoria <- function(dt, filas, campos) {
  m <- matrix(NA_real_, nrow = length(filas), ncol = length(campos), dimnames = list(NULL, campos))
  for (j in seq_along(campos)) m[, j] <- as.numeric(dt[[campos[j]]][filas])
  m
}

# predict por bloques: nunca arma la matriz completa del mes
predecir_por_bloques <- function(modelo, dt, filas, campos, bloque = 50000L) {
  prob <- numeric(length(filas))
  for (ini in seq(1L, length(filas), by = bloque)) {
    idx <- ini:min(ini + bloque - 1L, length(filas))
    m <- matriz_bajo_memoria(dt, filas[idx], campos)
    prob[idx] <- predict(modelo, m)
    rm(m)
  }
  gc(verbose = FALSE)
  prob
}

# lectura del .fst: solo el rango de filas de los meses pedidos (el archivo esta ordenado por foto_mes)
leer_meses_fst <- function(archivo, meses) {
  fm <- read_fst(archivo, columns = "foto_mes")$foto_mes
  stopifnot(all(meses %in% fm))
  filas <- which(fm %in% meses)
  dt <- read_fst(archivo, from = min(filas), to = max(filas), as.data.table = TRUE)
  rm(fm, filas)
  # meses intermedios que no se usan: se sacan sin duplicar memoria
  filas <- which(dt$foto_mes %in% meses)
  if (length(filas) < nrow(dt)) dt <- filtrar_filas_bajo_memoria(dt, filas)
  gc(full = TRUE, verbose = FALSE)
  dt
}

# ---------- progreso: imprime por pantalla y agrega al archivo estado_<experimento>.txt ----------
# (el archivo queda en la carpeta del experimento; se puede seguir con: tail -f estado_<experimento>.txt)
reportar <- function(...) {
  linea <- paste0("[", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "] ", paste0(...))
  cat(linea, "\n"); flush.console()
  arch <- file.path(CFG$carpeta_exp, paste0("HT", PARAM$experimento), paste0("estado_", PARAM$experimento, ".txt"))
  if (dir.exists(dirname(arch))) cat(linea, "\n", file = arch, append = TRUE)
  invisible(linea)
}
fmt_min <- function(m) if (is.na(m)) "?" else if (m < 60) sprintf("%.0f min", m) else sprintf("%.1f h", m / 60)

# [Anotación · líneas 629–659] Crea la carpeta exp/HTC1_E012 y se posiciona en ella. Lee del .fst los meses
#   que resultan de unir train, train_test, test, train_final y future; PARAM$train_final y PARAM$future no se
#   asignan en las celdas de esta notebook y PARAM.yml los registra como 202103–202106 y 202108. Guarda en PARAM
#   las banderas de FE y el nombre del archivo. Define campos_buenos: todas las columnas menos clase_ternaria,
#   clase01, azar y training.
#%% celda 41 [texto]
### 4.4  Preprocesamiento

#%% celda 42 [código]
# carpeta base de experimentos (ruta absoluta)
carpeta_exp <- CFG$carpeta_exp
setwd(carpeta_exp)
exp_folder <- paste0("HT", PARAM$experimento)
dir.create(exp_folder, showWarnings = FALSE)
setwd(file.path(carpeta_exp, exp_folder))

#%% celda 43 [código]
# lectura del dataset con FE: solo los meses que se usan en el experimento
meses_usados <- sort(unique(c(PARAM$train, PARAM$train_test, PARAM$test, PARAM$train_final, PARAM$future)))
dataset <- leer_meses_fst(CFG$archivo_fe, meses_usados)

# trazabilidad del preprocesamiento
PARAM$fe <- CFG$fe
PARAM$archivo_fe <- basename(CFG$archivo_fe)

cat("Dataset con FE leido desde:", CFG$archivo_fe, "\n")
cat("Meses:", paste(meses_usados, collapse = ", "), "|", nrow(dataset), "filas x", ncol(dataset), "columnas |",
    round(as.numeric(object.size(dataset)) / 1024^3, 2), "GB\n")

#%% celda 44 [código]
# los campos que se van a utilizar

campos_buenos <- setdiff(
  colnames(dataset),
  c("clase_ternaria", "clase01", "azar", "training")
)

# [Anotación · líneas 661–717] Función objetivo de la optimización: recibe un punto (num_iterations,
#   num_leaves, min_sum_hessian_in_leaf), lo combina con los parámetros fijos y corre lgb.cv con 5 folds
#   estratificados sobre dtrain; devuelve best_score, el AUC promedio de validación. Mientras la optimización
#   está en marcha agrega una línea por evaluación a BO_eval_kfold5_auc.txt (fecha, número de evaluación,
#   hiperparámetros, AUC y minutos) e informa el AUC máximo hasta el momento y el tiempo estimado restante.
#%% celda 45 [texto]
### 4.4b Función objetivo
**BO con k-fold 5 estratificado**, con los rangos de z495, métrica AUC: sobre 202103, 202104 y 202105, **sin undersampling**.
<br>En cada evaluación se agrega una línea a `BO_eval_test_kfold5_auc.txt` con los hiperparámetros, la AUC y el tiempo.

#%% celda 46 [código]
# En el argumento x llegan los parámetros de la bayesiana y devuelve la AUC en cross validation del modelo entrenado

EstimarGanancia_AUC_lightgbm <- function(x) {

  t0_eval <- Sys.time()
  n_total <- PARAM$bo$n_inicial + PARAM$bo$iteraciones
  if (isTRUE(bo_logueando))
    reportar(sprintf("BO | evaluacion %d de ~%d arranca | num_iterations=%d num_leaves=%d min_sum_hessian=%.4g",
                     bo_iter + 1L, n_total, as.integer(x$num_iterations), as.integer(x$num_leaves), x$min_sum_hessian_in_leaf))

  # x pisa (o agrega) a param_fijos
  param_completo <- modifyList(PARAM$lgbm$param_fijos, x)

  # entreno LightGBM con k-fold 5 estratificado
  # best_score = AUC promedio en los 5 folds de validacion
  modelocv <- lgb.cv(
    data= dtrain,
    nfold= PARAM$hyperparametertuning$xval_folds,
    stratified= TRUE,
    param= param_completo
  )

  # obtengo la ganancia
  AUC <- modelocv$best_score

  # log por evaluacion (checkpoint: mlrMBO solo graba cada 600 s y entre iteraciones)
  if (isTRUE(bo_logueando)) {
    bo_iter <<- bo_iter + 1L
    fwrite(data.table(fecha = format(Sys.time(), "%Y%m%d %H:%M:%S"), bo = BO$nombre, iter = bo_iter,
                      num_iterations = x$num_iterations, num_leaves = x$num_leaves,
                      min_sum_hessian_in_leaf = x$min_sum_hessian_in_leaf, auc = AUC,
                      minutos = round(as.numeric(difftime(Sys.time(), t0_eval, units = "mins")), 1)),
           BO$log_eval, append = file.exists(BO$log_eval), sep = "\t")

    # progreso: mejor AUC hasta ahora, tiempo promedio por evaluacion y estimacion de lo que falta
    ev <- fread(BO$log_eval)
    min_prom <- mean(ev$minutos)
    faltan <- max(0L, n_total - nrow(ev))
    reportar(sprintf("BO | evaluacion %d de ~%d lista en %s | AUC=%.5f | mejor hasta ahora=%.5f | faltan ~%d (~%s)",
                     nrow(ev), n_total, fmt_min(as.numeric(difftime(Sys.time(), t0_eval, units = "mins"))),
                     AUC, max(ev$auc), faltan, fmt_min(faltan * min_prom)))
  }

  # hago espacio en la memoria
  rm(modelocv)
  gc(full= TRUE, verbose= FALSE)

  message(format(Sys.time(), "%a %b %d %X %Y"), " AUC ", AUC)

  return(AUC)
}

# [Anotación · líneas 719–752] mejor_bo_guardada lee BO_log_kfold5_auc.txt (o BO_eval_kfold5_auc.txt si el
#   primero no existe) de una carpeta, ordena por AUC descendente y devuelve los hiperparámetros de la primera
#   fila. Si bo_reutilizar_origen es TRUE los toma de la carpeta del experimento de origen; si ya existe el
#   registro final en la carpeta actual, de ahí; en otro caso bo_hecha queda en FALSE y se ejecutan las celdas
#   de la optimización.
#%% celda 47 [código]
# mejores hiperparametros guardados en una carpeta de experimento (BO_log si termino, si no BO_eval)
mejor_bo_guardada <- function(carpeta, BO) {
  arch_log <- file.path(carpeta, BO$log); arch_eval <- file.path(carpeta, BO$log_eval)
  if (file.exists(arch_log)) {
    tb <- fread(arch_log); origen <- paste(arch_log, "(BO terminada)")
  } else if (file.exists(arch_eval)) {
    tb <- fread(arch_eval); setnames(tb, "auc", "y")
    origen <- paste(arch_eval, "(BO sin terminar:", nrow(tb), "evaluaciones)")
  } else return(NULL)
  setorder(tb, -y)
  list(mejores_hiperparametros = tb[1, list(num_iterations = as.integer(num_iterations),
                                            num_leaves = as.integer(num_leaves),
                                            min_sum_hessian_in_leaf = as.numeric(min_sum_hessian_in_leaf))],
       y = tb[1, y], meses = BO$meses, origen = origen)
}

# carpeta del experimento
dir.create(file.path(CFG$carpeta_exp, paste0("HT", PARAM$experimento)), showWarnings = FALSE)
setwd(file.path(CFG$carpeta_exp, paste0("HT", PARAM$experimento)))

# si la BO ya termino (o se reutiliza la de otro experimento), se toma del log y se saltean las celdas de la BO
res <- if (isTRUE(PARAM$bo_reutilizar_origen)) {
  r <- mejor_bo_guardada(file.path(CFG$carpeta_exp, paste0("HT", PARAM$bo_origen)), PARAM$bo)
  if (is.null(r)) stop("No hay logs de la BO en HT", PARAM$bo_origen)
  r
} else if (file.exists(PARAM$bo$log)) mejor_bo_guardada(getwd(), PARAM$bo) else NULL

if (!is.null(res)) {
  PARAM$out$bo <- res
  cat("BO -> se usa", res$origen, "\n"); print(res$mejores_hiperparametros); cat("AUC:", res$y, "\n")
} else cat("BO -> se corre en esta notebook (o se retoma desde", PARAM$bo$kbayesiana, ")\n")
bo_hecha <- !is.null(res)
rm(res)

# [Anotación · líneas 754–806] Activa la configuración de la optimización y cuenta las evaluaciones ya
#   registradas. Si la optimización no está hecha: toma los índices de las filas de 202103–202105, arma una
#   tabla con cliente, mes y clase, crea clase01 (1 para BAJA+1 y BAJA+2, 0 para CONTINUA) y marca training = 1
#   en las filas BAJA y en las CONTINUA cuyo número al azar (semilla 110017) no supera el undersampling; con
#   undersampling 1,0 quedan todas marcadas.
#%% celda 48 [texto]
### 4.5 BO (única): k-fold 5 estratificado sobre 202103–202105, AUC, sin undersampling
Rangos de z495, 12 puntos iniciales + 10 iteraciones bayesianas. Cada evaluación son 5 entrenamientos sobre los tres meses completos, así que es la parte más larga de la notebook: antes y después de cada evaluación se imprime el avance (evaluación N de ~22, AUC, mejor AUC hasta ahora, tiempo estimado restante).
<br>Si se corta, al volver a correr retoma desde `bayesiana_kfold5_auc.RDATA` (mlrMBO graba cada 10 minutos); cada evaluación queda además en `BO_eval_kfold5_auc.txt`.

#%% celda 49 [código]
# BO activa: todas las celdas de este bloque usan BO
BO <- PARAM$bo
bo_logueando <- FALSE
bo_iter <- if (file.exists(BO$log_eval)) nrow(fread(BO$log_eval)) else 0L
cat("BO", BO$nombre, "| meses:", paste(BO$meses, collapse = ", "), "| evaluaciones ya logueadas:", bo_iter, "\n")

#%% celda 50 [código]
if (!bo_hecha) {

  # indices de las filas de training de la BO: no se copia el dataset,
  # dataset_train solo lleva las columnas necesarias para la clase, el undersampling y los folds
  filas_bo <- which(dataset$foto_mes %in% BO$meses)
  dataset_train <- dataset[filas_bo, list(numero_de_cliente, foto_mes, clase_ternaria)]

} else cat("BO resuelta: se omite esta celda\n")

#%% celda 51 [código]
if (!bo_hecha) {

  # paso la clase a binaria que tome valores {0,1}  enteros
  #  BAJA+1 y BAJA+2  son  1,   CONTINUA es 0
  #  a partir de ahora ya NO puedo cortar  por prob(BAJA+2) > 1/40

  dataset_train[,
    clase01 := ifelse(clase_ternaria %in% c("BAJA+2","BAJA+1"), 1L, 0L)
  ]

} else cat("BO resuelta: se omite esta celda\n")

#%% celda 52 [código]
if (!bo_hecha) {

  # defino los datos que forma parte del training
  # aqui se hace el undersampling de los CONTINUA
  # notar que para esto utilizo la SEGUNDA semilla

  set.seed(PARAM$semilla_primigenia, kind = "L'Ecuyer-CMRG")
  dataset_train[, azar := runif(nrow(dataset_train))]
  dataset_train[, training := 0L]

  dataset_train[
    foto_mes %in%  BO$meses &
      (azar <= PARAM$trainingstrategy$undersampling | clase_ternaria %in% c("BAJA+1", "BAJA+2")),
    training := 1L
  ]

} else cat("BO resuelta: se omite esta celda\n")

# [Anotación · líneas 808–827] Construye el lgb.Dataset de la optimización con las filas marcadas, las
#   columnas de campos_buenos, la etiqueta clase01 y max_bin 31, e imprime la cantidad de filas y de columnas.
#   Según la salida guardada son 489.952 filas y 762 columnas.
#%% celda 53 [código]
if (!bo_hecha) {

  # dejo los datos en el formato que necesita LightGBM

  dtrain <- lgb.Dataset(
    data= matriz_bajo_memoria(dataset, filas_bo[dataset_train$training == 1L], campos_buenos),
    label= dataset_train[training == 1L, clase01],
    params= list(max_bin = PARAM$lgbm$param_fijos$max_bin, feature_pre_filter = FALSE, seed = PARAM$semilla_primigenia),
    free_raw_data= TRUE
  )
  lgb.Dataset.construct(dtrain)
  cat("BO", BO$nombre, "| k-fold", PARAM$hyperparametertuning$xval_folds, "estratificado sobre",
      paste(BO$meses, collapse = ", "), "(", nrow(dtrain), "filas con undersampling", PARAM$trainingstrategy$undersampling, ")\n")
  gc(full = TRUE, verbose = FALSE)

  nrow(dtrain)
  ncol(dtrain)

} else cat("BO resuelta: se omite esta celda\n")

# [Anotación · líneas 829–852] armar_folds_agrupados reparte los clientes en 5 folds, por separado los que
#   tienen alguna fila positiva y los que no, y devuelve los índices de fila de cada fold, de modo que todas las
#   filas de un cliente caen en el mismo fold; el resultado se guarda en folds_grupales. La llamada a lgb.cv de
#   la función objetivo (líneas 682–687) usa nfold y stratified y no recibe este objeto. Luego libera la tabla
#   de training.
#%% celda 54 [código]
if (!bo_hecha) {

  # Folds agrupados por cliente

  armar_folds_agrupados <- function(dt, k, seed) {
    set.seed(seed, kind = "L'Ecuyer-CMRG")
    cli <- dt[, list(pos = max(clase01)), by = numero_de_cliente]
    cli[, fold := sample(rep(seq_len(k), length.out = .N)), by = pos]
    fold_fila <- cli[dt[, list(numero_de_cliente)], on = "numero_de_cliente", fold]
    lapply(seq_len(k), function(i) which(fold_fila == i))
  }

  folds_grupales <- armar_folds_agrupados(
    dataset_train[training == 1L],
    k = PARAM$hyperparametertuning$xval_folds,
    seed = PARAM$semilla_primigenia
  )

  # dtrain ya tiene los datos (free_raw_data = FALSE): libero la tabla de training
  rm(dataset_train, filas_bo)
  gc(full = TRUE, verbose = FALSE)

} else cat("BO resuelta: se omite esta celda\n")

# [Anotación · líneas 854–901] Configura mlrMBO: función objetivo de un solo criterio a maximizar, marcada
#   como ruidosa, sobre el espacio de búsqueda definido; guardado del estado cada 600 segundos en
#   bayesiana_kfold5_auc.RDATA; terminación a las 10 iteraciones; criterio de selección de puntos Expected
#   Improvement; modelo sustituto de kriging (regr.km) con covarianza matern3_2 y predicción con error estándar.
#%% celda 55 [código]
if (!bo_hecha) {

  # Aqui comienza la configuracion de la Bayesian Optimization

  # en este archivo quedan la evolucion binaria de la BO
  kbayesiana <- BO$kbayesiana

  funcion_optimizar <- EstimarGanancia_AUC_lightgbm # la funcion que voy a maximizar

  configureMlr(show.learner.output= FALSE)

  # configuro la busqueda bayesiana,  los hiperparametros que se van a optimizar
  # por favor, no desesperarse por lo complejo

  obj.fun <- makeSingleObjectiveFunction(
    fn= funcion_optimizar, # la funcion que voy a maximizar
    minimize= FALSE, # estoy Maximizando la ganancia
    noisy= TRUE,
    par.set= BO$hs, # definido al comienzo del programa
    has.simple.signature= FALSE # paso los parametros en una lista
  )

  # cada 600 segundos guardo el resultado intermedio
  ctrl <- makeMBOControl(
    save.on.disk.at.time= 600, # se graba cada 600 segundos
    save.file.path= kbayesiana
  ) # se graba cada 600 segundos

  # indico la cantidad de iteraciones que va a tener la Bayesian Optimization
  ctrl <- setMBOControlTermination(
    ctrl,
    iters= BO$iteraciones
  ) # cantidad de iteraciones

  # defino el método estandar para la creacion de los puntos iniciales,
  # los "No Inteligentes"
  ctrl <- setMBOControlInfill(ctrl, crit= makeMBOInfillCritEI())

  # establezco la funcion que busca el maximo
  surr.km <- makeLearner(
    "regr.km",
    predict.type= "se",
    covtype= "matern3_2",
    control= list(trace= TRUE)
  )

} else cat("BO resuelta: se omite esta celda\n")

# [Anotación · líneas 903–923] Activa el registro por evaluación y lanza la optimización con mbo si no existe
#   el archivo de estado, o la retoma con mboContinue si existe. Al terminar desactiva el registro e informa el
#   fin.
#%% celda 56 [código]
if (!bo_hecha) {

  # inicio la optimizacion bayesiana, retomando si ya existe
  # es la celda mas lenta de todo el notebook

  bo_logueando <- TRUE   # desde aca cada evaluacion se loguea en BO$log_eval

  reportar("BO | arranca: ", PARAM$bo$n_inicial, " puntos iniciales + ", BO$iteraciones, " iteraciones bayesianas | ",
           "evaluaciones ya hechas: ", bo_iter)
  if (!file.exists(kbayesiana)) {
    bayesiana_salida <- mbo(obj.fun, learner= surr.km, control= ctrl)
  } else {
    print("BO: retomo corrida ...")
    bayesiana_salida <- mboContinue(kbayesiana) # retomo en caso que ya exista
  }

  bo_logueando <- FALSE
  reportar("BO | terminada")

} else cat("BO resuelta: se omite esta celda\n")

# [Anotación · líneas 925–953] Celda para la optimización cortada a mano: lee BO_eval_kfold5_auc.txt, intenta
#   recuperar el camino de la optimización con mboFinalize sobre el archivo de estado y, si eso da error o tiene
#   menos evaluaciones, lo arma desde BO_eval. Ordena por AUC descendente y graba BO_log_kfold5_auc.txt. Guarda
#   en PARAM$out$bo los hiperparámetros de la primera fila, su AUC, los meses y la cantidad de evaluaciones,
#   escribe PARAM.yml y marca la optimización como hecha.
#%% celda 57 [código]
# BO cortada a mano a las 16 evaluaciones inclusive: arma los archivos finales con las evaluaciones hechas
setwd(file.path(CFG$carpeta_exp, paste0("HT", PARAM$experimento)))

ev <- fread(PARAM$bo$log_eval)   # una fila por evaluacion terminada
tb_bayesiana <- tryCatch(as.data.table(mboFinalize(PARAM$bo$kbayesiana)$opt.path),
                         error = function(e) NULL)

# si el estado de mlrMBO tiene menos evaluaciones que BO_eval (se graba cada 10 min), se arma desde BO_eval
if (is.null(tb_bayesiana) || nrow(tb_bayesiana) < nrow(ev)) {
  tb_bayesiana <- ev[, list(num_iterations, num_leaves, min_sum_hessian_in_leaf, y = auc)]
  cat("BO_log armado desde", PARAM$bo$log_eval, "\n")
} else cat("BO_log armado desde", PARAM$bo$kbayesiana, "(mboFinalize)\n")

tb_bayesiana[, iter := .I]
setorder(tb_bayesiana, -y)
fwrite(tb_bayesiana, file = PARAM$bo$log, sep = "\t")

PARAM$out$bo$mejores_hiperparametros <- tb_bayesiana[1, list(num_iterations = as.integer(num_iterations),
                                                            num_leaves = as.integer(num_leaves),
                                                            min_sum_hessian_in_leaf = as.numeric(min_sum_hessian_in_leaf))]
PARAM$out$bo$y <- tb_bayesiana[1, y]
PARAM$out$bo$meses <- PARAM$bo$meses
PARAM$out$bo$evaluaciones <- nrow(tb_bayesiana)
write_yaml(PARAM, file = "PARAM.yml")

bo_hecha <- TRUE   # las celdas siguientes de la BO se saltean
cat("BO cortada en", nrow(tb_bayesiana), "evaluaciones\n")
print(PARAM$out$bo$mejores_hiperparametros, digits = 17); cat("AUC:", PARAM$out$bo$y, "\n")
```

### C1_E012_modelo-MH-entrega.ipynb

Notebook de R que va del dataset crudo al archivo de envío: clase ternaria, feature engineering, test en 202106 con 5 semillas, 20 modelos LightGBM finales con hiperparámetros escritos en el código, ensambles por promedio y archivos de numero_de_cliente por corte.

````r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–40] Celdas de texto de presentación. Enumeran el contenido de la notebook (feature
#   engineering, LightGBM con hiperparámetros fijos, 20 modelos con semillas fijas entrenados con 202103 a
#   202106 sin undersampling, ensamble por promedio, archivos con 5, 10, 15 y 20 modelos y cortes de 9.500 a
#   15.000) y cómo correrla: dónde copiar el dataset crudo, ejecutar todas las celdas en orden y qué archivos
#   quedan.
#%% celda 1 [texto]
# Competencia 01 — Entrega final

Notebook para reproducir la entrega final de Zulip. Parte del dataset crudo, arma la clase y el feature engineering, entrena los modelos finales con los hiperparámetros que salieron de la optimización bayesiana y deja el archivo con los `numero_de_cliente` a enviar.

**Resumen del modelo**
- Feature engineering: `ccajas_depositos` en NA para 202105 → lag1/delta1 y lag2/delta2 de las variables originales → ranking por mes con cero fijo de todas las variables (originales, lags y deltas), salvo `numero_de_cliente`, `foto_mes` y `clase_ternaria`.
- LightGBM con hiperparámetros fijos.
- 20 modelos finales iguales salvo la semilla (semillas primas fijas), entrenados con 202103 a 202106 completos, sin undersampling.
- Ensamble: se promedian las probabilidades de los modelos por cliente y se ordena de mayor a menor. Se generan archivos con 5, 10, 15 y 20 modelos y cortes de 9.500 a 15.000.
- La entrega final es el ensamble de los 20 modelos cortado en `PARAM$envios` clientes.

#%% celda 2 [texto]
## Cómo correrla

**Entorno.** Notebook de R. La corrí en una VM de Google Cloud con 8 vCPU y 64 GB de RAM. Las librerías que falten se instalan.

**Datos crudos.** Copiar `competencia_01_crudo.csv` (también sirve `.csv.gz` o `.zip`) en:

```
~/buckets/b1/datasets/
```

La carpeta `datasets/` tiene que existir. Si se usa otra carpeta base, cambiar solo `carpeta_base` en la celda 0.1.

**Ejecución.** Correr todas las celdas en orden (*Run All*).
- La primera vez genera `datasets/competencia_01.csv.gz` (clase ternaria) y `datasets/competencia_01_fe_naccajas_lag1_delta1_lag2_delta2_rankfinal.fst` (dataset con FE). Si ya existen, los reutiliza.
- Cada modelo guarda su probabilidad apenas termina; si la corrida se corta, al volver a correr sigue desde el que faltaba.

**Archivos para probar en Zulip.** Ensambles de 5, 10, 15 y 20 modelos con cortes de 9.500 a 15.000 de a 500:

```
~/buckets/b1/exp/C1_E012_entrega/zulip_cortes/ens05/<corte>/C1_E012_ens05_c<corte>.csv   (y ens10, ens15, ens20)
```

**Archivo final para Zulip.** Lo genera la sección 3. Queda en:

```
~/buckets/b1/exp/C1_E012_entrega/zulip/C1_E012_ensamble_20S_<envios>.csv
```

# [Anotación · líneas 42–63] Fija el repositorio de CRAN, define carpeta_base como ~/buckets/b1 y detiene la
#   ejecución si no existe la subcarpeta datasets/. Carga data.table, R.utils, fst, yaml, lightgbm, primes y
#   ggplot2, instalando el paquete que falte.
#%% celda 3 [texto]
## 0. Configuración

#%% celda 4 [texto]
### 0.1 Carpetas y librerías

#%% celda 5 [código]
options(repos = c(CRAN = "https://cloud.r-project.org"))

# carpeta base: adentro tienen que estar datasets/ (con el crudo) y se crea exp/
carpeta_base <- path.expand("~/buckets/b1")

carpeta_datasets <- file.path(carpeta_base, "datasets")
if (!dir.exists(carpeta_datasets))
  stop("No existe ", carpeta_datasets, ". Crearla y copiar ahí competencia_01_crudo.csv")

for (paquete in c("data.table", "R.utils", "fst", "yaml", "lightgbm", "primes", "ggplot2")) {
  if (!require(paquete, character.only = TRUE)) {
    install.packages(paquete)
    library(paquete, character.only = TRUE)
  }
}

# [Anotación · líneas 65–89] Crea la lista PARAM con los parámetros de la corrida: experimento
#   C1_E012_entrega_MH, semilla_primigenia 110017, meses de entrenamiento final 202103 a 202106, mes a predecir
#   202108, undersampling 1,0, meses del test (entrena con 202103 y 202104, mide en 202106), 20 semillas para
#   los modelos finales, ensambles parciales de 5, 10, 15 y 20 modelos, cortes de 9.500 a 15.000 de a 500, 5
#   semillas para el test y 4 hilos.
#%% celda 6 [texto]
### 0.2 Parámetros del experimento
Meses, semillas, corte y parámetros fijos de LightGBM. Las semillas son las primeras `n_semillas` de una lista fija de 20 números primos (la misma que usé al experimentar), escrita a mano en la celda.

#%% celda 7 [código]
PARAM <- list()
PARAM$experimento <- "C1_E012_entrega_MH"
PARAM$semilla_primigenia <- 110017

PARAM$train_final <- c(202103, 202104, 202105, 202106)   # entrenamiento de los modelos finales
PARAM$future      <- 202108                              # mes a predecir
PARAM$undersampling <- 1.0                               # sin undersampling

PARAM$train_test  <- c(202103, 202104)                   # test (1.3): entrena
PARAM$test        <- 202106                              #             y mide

PARAM$n_semillas <- 20L                          # modelos finales
PARAM$bloques    <- c(5L, 10L, 15L, 20L)         # ensambles parciales para probar en Zulip
PARAM$cortes     <- seq(9500L, 15000L, by = 500L)

# test en 202106 con las primeras semillas
PARAM$test_n_semillas <- 5L

# hilos de LightGBM
PARAM$num_threads <- 4L

# [Anotación · líneas 91–122] Define los parámetros de LightGBM que no cambian entre modelos: boosting gbdt,
#   objective binary, metric auc, max_depth -1, lambda_l1 y lambda_l2 en 0, max_bin 31, bagging_fraction 1,0,
#   extra_trees FALSE, early_stopping 0, min_data_in_leaf 0, feature_fraction 0,50 y learning_rate 0,005, entre
#   otros.
#%% celda 8 [código]
# parametros fijos de LightGBM (los mismos de la BO)
PARAM$lgbm_fijos <- list(
  boosting = "gbdt",
  objective = "binary",
  metric = "auc",
  feature_pre_filter = FALSE,
  first_metric_only = FALSE,
  boost_from_average = TRUE,
  force_row_wise = TRUE,
  deterministic = TRUE,
  verbosity = -100,
  seed = PARAM$semilla_primigenia,
  max_depth = -1L,
  min_gain_to_split = 0,
  lambda_l1 = 0.0,
  lambda_l2 = 0.0,
  max_bin = 31L,
  bagging_fraction = 1.0,
  pos_bagging_fraction = 1.0,
  neg_bagging_fraction = 1.0,
  is_unbalance = FALSE,
  scale_pos_weight = 1.0,
  drop_rate = 0.1,
  max_drop = 50,
  skip_drop = 0.5,
  extra_trees = FALSE,
  early_stopping = 0,
  min_data_in_leaf = 0,
  feature_fraction = 0.50,
  learning_rate = 0.005
)

# [Anotación · líneas 124–137] Escribe la lista de 20 semillas (números primos de 6 cifras) y verifica que
#   sean 20 y sin repetidos; el comentario indica cómo se generaron (set.seed(110017) y una muestra de primos
#   entre 100.000 y 999.999). Agrega num_threads a los parámetros, arma las rutas del dataset con clase, del
#   dataset con FE y de la carpeta del experimento, y crea las subcarpetas probabilidades/ y zulip/.
# 20 semillas FIJAS (numeros primos de 6 cifras), siempre las mismas y en el mismo orden.
# Salen de: set.seed(110017, kind = "L'Ecuyer-CMRG"); sample(primes::generate_primes(100000, 999999), 20)
# Quedan escritas a mano para que no dependan de la version de R ni de ningun paquete.
PARAM$semillas_20 <- c(325229L, 622049L, 450451L, 225637L, 239297L, 219763L, 418981L, 182627L, 248351L, 387199L,
                       982703L, 342929L, 908893L, 793399L, 112249L, 162263L, 347987L, 910849L, 453667L, 122921L)
stopifnot(length(PARAM$semillas_20) == 20L, !anyDuplicated(PARAM$semillas_20))

PARAM$lgbm_fijos$num_threads <- PARAM$num_threads

archivo_clase <- file.path(carpeta_datasets, "competencia_01.csv.gz")
archivo_fe    <- file.path(carpeta_datasets, "competencia_01_fe_naccajas_lag1_delta1_lag2_delta2_rankfinal.fst")
carpeta_exp   <- file.path(carpeta_base, "exp", PARAM$experimento)
dir.create(file.path(carpeta_exp, "probabilidades"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(carpeta_exp, "zulip"), recursive = TRUE, showWarnings = FALSE)

# [Anotación · líneas 139–185] Funciones auxiliares de datos. filtrar_filas arma un data.table con las filas
#   pedidas copiando columna por columna y borrando cada columna del original. leer_meses_fst lee del .fst el
#   rango de filas que contiene los meses pedidos y descarta los meses intermedios que no se piden. armar_matriz
#   construye una matriz numérica con las filas y columnas indicadas. armar_dtrain crea el lgb.Dataset con esa
#   matriz, la etiqueta clase01, max_bin 31 y data_random_seed 110017.
#%% celda 9 [texto]
### 0.3 Funciones auxiliares
Para no duplicar el dataset en memoria se trabaja con índices de filas y las matrices de LightGBM se arman columna por columna.

#%% celda 10 [código]
# saca filas de un data.table sin tener dos copias completas en memoria
filtrar_filas <- function(dt, filas) {
  cols <- copy(names(dt))
  out <- data.table(.tmp = seq_along(filas))
  for (k in seq_along(cols)) {
    set(out, j = cols[k], value = dt[[cols[k]]][filas])
    set(dt, j = cols[k], value = NULL)
  }
  out[, .tmp := NULL]
  gc(verbose = FALSE)
  out
}

# lee del .fst solo los meses pedidos (el archivo esta ordenado por foto_mes)
leer_meses_fst <- function(archivo, meses) {
  fm <- read_fst(archivo, columns = "foto_mes")$foto_mes
  stopifnot(all(meses %in% fm))
  filas <- which(fm %in% meses)
  dt <- read_fst(archivo, from = min(filas), to = max(filas), as.data.table = TRUE)
  filas <- which(dt$foto_mes %in% meses)
  if (length(filas) < nrow(dt)) dt <- filtrar_filas(dt, filas)
  gc(full = TRUE, verbose = FALSE)
  dt
}

# matriz numerica para LightGBM a partir de un subconjunto de filas y columnas
armar_matriz <- function(dt, filas, campos) {
  m <- matrix(NA_real_, nrow = length(filas), ncol = length(campos), dimnames = list(NULL, campos))
  for (j in seq_along(campos)) m[, j] <- as.numeric(dt[[campos[j]]][filas])
  m
}

# lgb.Dataset con los mismos parametros de dataset en todos los modelos
armar_dtrain <- function(dt, filas, campos) {
  d <- lgb.Dataset(data = armar_matriz(dt, filas, campos), label = dt$clase01[filas],
                   params = list(max_bin = PARAM$lgbm_fijos$max_bin, feature_pre_filter = FALSE,
                                 data_random_seed = PARAM$semilla_primigenia),
                   free_raw_data = TRUE)
  lgb.Dataset.construct(d)
  gc(full = TRUE, verbose = FALSE)
  d
}

# [Anotación · líneas 187–214] rank_cero_fijo reemplaza los valores positivos por su rank (empates al
#   promedio) dividido por la cantidad de positivos, y los negativos por el rank de su valor absoluto, con signo
#   negativo, dividido por la cantidad de negativos; ceros y NA quedan igual. escribir_zulip escribe los
#   numero_de_cliente como enteros, uno por línea y sin encabezado, verifica que no haya repetidos y vuelve a
#   leer el archivo para compararlo. reportar imprime un mensaje con fecha y hora y lo agrega a archivo_estado
#   si esa variable existe.
# ranking por mes con cero fijo: positivos en (0, 1], negativos en [-1, 0), ceros y NA sin cambios
rank_cero_fijo <- function(x) {
  out <- x
  pos <- !is.na(x) & x > 0
  neg <- !is.na(x) & x < 0
  if (any(pos)) out[pos] <-  frank( x[pos], ties.method = "average") / sum(pos)
  if (any(neg)) out[neg] <- -frank(-x[neg], ties.method = "average") / sum(neg)
  out
}

# csv para Zulip: sin encabezado, solo numero_de_cliente como entero
escribir_zulip <- function(ids, archivo) {
  txt <- formatC(ids, format = "d", big.mark = "")
  stopifnot(!anyDuplicated(txt), all(grepl("^[0-9]+$", txt)))
  con <- file(archivo, open = "wb")
  writeLines(txt, con, sep = "\n")
  close(con)
  stopifnot(identical(readLines(archivo), txt))
  invisible(archivo)
}

# mensaje con hora, por pantalla y al archivo de estado
reportar <- function(...) {
  linea <- paste0("[", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "] ", paste0(...))
  cat(linea, "\n"); flush.console()
  if (exists("archivo_estado")) cat(linea, "\n", file = archivo_estado, append = TRUE)
  invisible(linea)
}

# [Anotación · líneas 216–226] Define dos banderas: hacer_fe es verdadera si no existe el archivo .fst con
#   feature engineering; hacer_clase, si además falta el archivo con la clase ternaria. Las celdas de
#   preprocesamiento que siguen se ejecutan según estas banderas.
#%% celda 11 [texto]
# 1. Desarrollo

#%% celda 12 [texto]
## 1.1 Preprocesamiento
Si el dataset con feature engineering ya existe en `datasets/`, se saltea todo este bloque.

#%% celda 13 [código]
hacer_fe    <- !file.exists(archivo_fe)
hacer_clase <- hacer_fe && !file.exists(archivo_clase)
cat("Generar clase ternaria:", hacer_clase, "| Generar feature engineering:", hacer_fe, "\n")

# [Anotación · líneas 228–276] Si hace falta, busca el dataset crudo (competencia_01_crudo con extensión .csv,
#   .csv.gz, .zip o .csv.zip; un .zip se descomprime en una carpeta temporal) y calcula clase_ternaria:
#   convierte foto_mes a un número de período consecutivo, ordena por cliente y período y obtiene los dos
#   períodos siguientes de cada cliente. Asigna CONTINUA a los períodos anteriores al anteúltimo, BAJA+1 cuando
#   el cliente no aparece en el mes siguiente y BAJA+2 cuando aparece en el siguiente y no en el subsiguiente.
#   Graba competencia_01.csv.gz. Si la clase ya existe y falta el FE, lee ese archivo. Imprime la cantidad de
#   registros por mes y clase.
#%% celda 14 [texto]
### Clase ternaria
Para cada cliente y mes se mira si sigue apareciendo en los meses siguientes:
- **BAJA+1**: no está en el mes siguiente.
- **BAJA+2**: está en el mes siguiente pero no en el subsiguiente.
- **CONTINUA**: el resto.

Los dos últimos meses quedan sin clase porque no hay información futura.

#%% celda 15 [código]
if (hacer_clase) {
  crudos <- file.path(carpeta_datasets, paste0("competencia_01_crudo", c(".csv", ".csv.gz", ".zip", ".csv.zip")))
  archivo_crudo <- crudos[file.exists(crudos)][1]
  if (is.na(archivo_crudo)) stop("No encuentro competencia_01_crudo.csv en ", carpeta_datasets)

  if (grepl("\\.zip$", archivo_crudo)) {
    csv_local <- utils::unzip(archivo_crudo, exdir = tempdir())
    dataset <- fread(csv_local[grepl("\\.csv$", csv_local)][1])
    unlink(csv_local)
  } else {
    dataset <- fread(archivo_crudo)
  }

  dsimple <- dataset[, list(pos = .I, numero_de_cliente,
                            periodo0 = as.integer(foto_mes / 100) * 12 + foto_mes %% 100)]
  setorder(dsimple, numero_de_cliente, periodo0)

  periodo_ultimo     <- dsimple[, max(periodo0)]
  periodo_anteultimo <- periodo_ultimo - 1

  dsimple[, c("periodo1", "periodo2") := shift(periodo0, n = 1:2, fill = NA, type = "lead"), numero_de_cliente]

  dsimple[periodo0 < periodo_anteultimo, clase_ternaria := "CONTINUA"]
  dsimple[periodo0 < periodo_ultimo & (is.na(periodo1) | periodo0 + 1 < periodo1),
          clase_ternaria := "BAJA+1"]
  dsimple[periodo0 < periodo_anteultimo & (periodo0 + 1 == periodo1) & (is.na(periodo2) | periodo0 + 2 < periodo2),
          clase_ternaria := "BAJA+2"]

  setorder(dsimple, pos)
  dataset[, clase_ternaria := dsimple$clase_ternaria]
  fwrite(dataset, file = archivo_clase, sep = ",")
  rm(dsimple)
  gc(full = TRUE, verbose = FALSE)

} else if (hacer_fe) {
  dataset <- fread(archivo_clase)
}

if (hacer_fe) print(dataset[, .N, keyby = list(foto_mes, clase_ternaria)])

# [Anotación · líneas 278–286] Asigna NA a ccajas_depositos en todos los registros de 202105 e imprime cuántos
#   quedan en NA. Se hace antes de calcular lags y deltas.
#%% celda 16 [texto]
### Corrección de `ccajas_depositos` en 202105
En 202105 esta variable tiene valores anómalos. La pongo en NA **antes** de calcular los lags para que el problema no se arrastre a los meses siguientes.

#%% celda 17 [código]
if (hacer_fe) {
  dataset[foto_mes == 202105, ccajas_depositos := NA]
  cat("ccajas_depositos en NA para 202105:", dataset[foto_mes == 202105, sum(is.na(ccajas_depositos))], "registros\n")
}

# [Anotación · líneas 288–309] Ordena por cliente y mes y toma como variables originales todas las columnas
#   numéricas salvo numero_de_cliente y foto_mes. Marca las filas cuya fila anterior no es del mismo cliente o
#   no corresponde al mes inmediatamente anterior. Para cada variable agrega <variable>_lag1 (valor del mes
#   anterior, NA en las filas marcadas) y <variable>_delta1 (valor actual menos el del mes anterior).
#%% celda 18 [texto]
### Lags y deltas de orden 1
Para cada variable numérica se agrega el valor del mes anterior (`_lag1`) y la diferencia con ese mes (`_delta1`). Si el cliente no estaba el mes anterior, quedan en NA.

#%% celda 19 [código]
if (hacer_fe) {
  setorder(dataset, numero_de_cliente, foto_mes)
  cols_orig <- setdiff(names(dataset)[sapply(dataset, is.numeric)], c("numero_de_cliente", "foto_mes", "clase_ternaria"))

  periodo0 <- as.integer(dataset$foto_mes / 100) * 12L + dataset$foto_mes %% 100L
  ok <- dataset$numero_de_cliente == shift(dataset$numero_de_cliente, 1L) & (periodo0 - shift(periodo0, 1L)) == 1L
  sin_lag <- which(is.na(ok) | !ok)

  for (col in cols_orig) {
    v <- shift(dataset[[col]], 1L)
    v[sin_lag] <- NA
    set(dataset, j = paste0(col, "_lag1"),   value = v)
    set(dataset, j = paste0(col, "_delta1"), value = dataset[[col]] - v)
  }
  rm(periodo0, ok, sin_lag, v)
  cat("Lag1 / delta1 de", length(cols_orig), "variables | columnas:", ncol(dataset), "\n")
}

# [Anotación · líneas 311–329] Repite el procedimiento con un desplazamiento de dos filas: marca las filas
#   cuyo registro de dos posiciones atrás no es del mismo cliente o no está exactamente dos meses antes, y
#   agrega <variable>_lag2 y <variable>_delta2 para cada variable original.
#%% celda 20 [texto]
### Lags y deltas de orden 2
Lo mismo con el valor de dos meses atrás (`_lag2`, `_delta2`), sobre las variables originales.

#%% celda 21 [código]
if (hacer_fe) {
  periodo0 <- as.integer(dataset$foto_mes / 100) * 12L + dataset$foto_mes %% 100L
  ok <- dataset$numero_de_cliente == shift(dataset$numero_de_cliente, 2L) & (periodo0 - shift(periodo0, 2L)) == 2L
  sin_lag <- which(is.na(ok) | !ok)

  for (col in cols_orig) {
    v <- shift(dataset[[col]], 2L)
    v[sin_lag] <- NA
    set(dataset, j = paste0(col, "_lag2"),   value = v)
    set(dataset, j = paste0(col, "_delta2"), value = dataset[[col]] - v)
  }
  rm(periodo0, ok, sin_lag, v)
  cat("Lag2 / delta2 de", length(cols_orig), "variables | columnas:", ncol(dataset), "\n")
}

# [Anotación · líneas 331–349] Toma todas las columnas numéricas salvo numero_de_cliente y foto_mes
#   (originales, lags y deltas), separa los índices de fila por foto_mes y, columna por columna, reemplaza los
#   valores de cada mes por el resultado de rank_cero_fijo. Informa el avance cada 100 columnas.
#%% celda 22 [texto]
### Ranking por mes con cero fijo de todas las variables
Después de los lags, cada variable (originales, lags y deltas) se reemplaza por su ranking dentro de cada mes, con el cero fijo: los positivos se ordenan entre sí y quedan entre 0 y 1, los negativos entre -1 y 0, y los ceros y NA no cambian. Quedan sin tocar `numero_de_cliente`, `foto_mes` y `clase_ternaria`. Se hace columna por columna para no duplicar el dataset en memoria.

#%% celda 23 [código]
if (hacer_fe) {
  cols_rank <- setdiff(names(dataset), c("numero_de_cliente", "foto_mes", "clase_ternaria"))
  cols_rank <- cols_rank[vapply(cols_rank, function(cn) is.numeric(dataset[[cn]]), logical(1))]
  idx_mes <- split(seq_len(nrow(dataset)), dataset$foto_mes)

  for (k in seq_along(cols_rank)) {
    v <- as.numeric(dataset[[cols_rank[k]]])
    for (ix in idx_mes) v[ix] <- rank_cero_fijo(v[ix])
    set(dataset, j = cols_rank[k], value = v)
    if (k %% 100 == 0) { cat("  rankeadas", k, "de", length(cols_rank), "\n"); gc(verbose = FALSE) }
  }
  rm(idx_mes, v)
  cat("Variables rankeadas:", length(cols_rank), "\n")
}

# [Anotación · líneas 351–362] Ordena el dataset por foto_mes y numero_de_cliente, lo graba en formato .fst
#   con compresión 50 y lo borra de memoria.
#%% celda 24 [texto]
### Grabado del dataset con FE

#%% celda 25 [código]
if (hacer_fe) {
  # se guarda ordenado por mes para poder leer despues solo los meses necesarios
  setorder(dataset, foto_mes, numero_de_cliente)
  write_fst(dataset, archivo_fe, compress = 50)
  cat("Dataset con FE guardado en", archivo_fe, "\n")
  rm(dataset)
  gc(full = TRUE, verbose = FALSE)
}

# [Anotación · líneas 364–390] Las celdas de texto describen la optimización bayesiana de la que salen los
#   hiperparámetros, hecha en C1_E012_con-rank-final_BO.ipynb. El código escribe los tres valores elegidos
#   (num_iterations 2891, num_leaves 1056, min_sum_hessian_in_leaf 0,013485676441086), los combina con los
#   parámetros fijos en param_final y divide min_data_in_leaf por el undersampling (0 dividido 1,0).
#%% celda 26 [texto]
## 1.2 Training strategy, optimización bayesiana y mejores hiperparámetros

**Cómo se buscaron los hiperparámetros.** Optimización bayesiana con `mlrMBO` sobre `num_iterations`, `num_leaves` y `min_sum_hessian_in_leaf`, con el resto de los parámetros fijos (celda 0.2) y `min_data_in_leaf = 0`.
- Validación: k-fold 5 estratificado (`lgb.cv`, `nfold = 5`, `stratified = TRUE`) sobre 202103, 202104 y 202105.
- Métrica: AUC. Sin undersampling: se usan todos los CONTINUA.
- Rangos (los de la notebook z495 de Gustavo Pasquini): `num_iterations` 64–4096, `num_leaves` 16–2048, `min_sum_hessian_in_leaf` 1e-06–0.1.

Cada evaluación lleva cerca de una hora, así que el código queda comentado como referencia y abajo se fijan los hiperparámetros elegidos.

#%% celda 27 [texto]
### Origen de los hiperparámetros
Los hiperparámetros **no se optimizan en esta notebook**: salen de la optimización bayesiana de **`C1_E012_con-rank-final_BO.ipynb`** (sección 4.5), con el mismo feature engineering, los mismos parámetros fijos y la misma estrategia (k-fold 5 sobre 202103–05, AUC, sin undersampling, rangos de z495).

- La BO se cortó a mano después de **16 evaluaciones** (12 puntos iniciales + 4 iteraciones bayesianas). Los archivos finales de la BO se armaron con la celda "BO cortada a mano".
- Registro de la BO: `exp/HTC1_E012/BO_eval_kfold5_auc.txt` (una línea por evaluación) y `exp/HTC1_E012/BO_log_kfold5_auc.txt` (las 16 ordenadas por AUC).

#%% celda 28 [código]
PARAM$mejores_hiperparametros <- list(
  num_iterations          = 2891L,      
  num_leaves              = 1056L,
  min_sum_hessian_in_leaf = 0.013485676441086
)

param_final <- modifyList(PARAM$lgbm_fijos, PARAM$mejores_hiperparametros)
param_final$min_data_in_leaf <- round(param_final$min_data_in_leaf / PARAM$undersampling)
str(PARAM$mejores_hiperparametros)

# [Anotación · líneas 392–413] Control contra el registro de la optimización bayesiana: busca
#   BO_eval_kfold5_auc.txt o BO_log_kfold5_auc.txt en exp/HTC1_E012 (o BO_eval_kfold5_auc.txt en
#   bo_logs/C1_E012), ordena las evaluaciones por AUC, imprime las tres primeras y busca la fila que coincide
#   con los hiperparámetros declarados para informar su número de evaluación y su puesto. Si no la encuentra
#   emite una advertencia; si no hay registro, avisa que se usan los valores declarados.
#%% celda 29 [código]
# control: busca los hiperparametros declarados en el log de la BO e informa su evaluacion y su puesto por AUC
logs <- c(file.path(carpeta_base, "exp", "HTC1_E012", "BO_eval_kfold5_auc.txt"),
          file.path(carpeta_base, "exp", "HTC1_E012", "BO_log_kfold5_auc.txt"),
          file.path("bo_logs", "C1_E012", "BO_eval_kfold5_auc.txt"))
arch_log <- logs[file.exists(logs)][1]

if (!is.na(arch_log) && !anyNA(unlist(PARAM$mejores_hiperparametros))) {
  ev <- fread(arch_log)
  if (!"y" %in% names(ev)) setnames(ev, "auc", "y")
  if (!"iter" %in% names(ev)) ev[, iter := .I]
  setorder(ev, -y)
  ev[, puesto := .I]
  hp <- PARAM$mejores_hiperparametros
  fila <- ev[num_iterations == hp$num_iterations & num_leaves == hp$num_leaves &
             abs(min_sum_hessian_in_leaf - hp$min_sum_hessian_in_leaf) < 1e-8]
  cat("Log de la BO:", arch_log, "|", nrow(ev), "evaluaciones\n")
  print(ev[1:min(3, .N), list(puesto, iter, num_iterations, num_leaves, min_sum_hessian_in_leaf, y)], digits = 17)
  if (nrow(fila) == 0) warning("Los hiperparametros declarados NO estan en el log de la BO")
  else cat(sprintf("Hiperparametros declarados = evaluacion %d de la BO, puesto %d de %d por AUC (%.6f)\n",
                   fila$iter[1], fila$puesto[1], nrow(ev), fila$y[1]))
} else cat("Log de la BO no disponible: se usan los valores declarados arriba\n")

# [Anotación · líneas 415–448] Lee del .fst los meses 202103, 202104, 202105, 202106 y 202108, crea clase01 (1
#   si la clase es BAJA+1 o BAJA+2, 0 en otro caso) y define como variables todas las columnas menos
#   clase_ternaria, clase01, azar y training. Para cada una de las primeras 5 semillas que no tenga su archivo
#   de probabilidades, entrena un LightGBM con 202103 y 202104 y los hiperparámetros finales, predice 202106 y
#   guarda las probabilidades (test/prob_test_NN.csv) y la importancia de variables (test/impo_test_NN.txt).
#%% celda 30 [texto]
## 1.3 Test en 202106 con varias semillas
Para elegir el corte: los mismos hiperparámetros y las primeras `PARAM$test_n_semillas` semillas, entrenando con todos los datos de 202103–04 y midiendo en 202106. Se calcula la ganancia de cada semilla y del ensamble (promedio de sus probabilidades) en los cortes de 9.500 a 15.000: +1.072.500 por cada BAJA+2 y −27.500 por cada uno de los demás. Las probabilidades quedan en `test/`; si ya existen, no se vuelven a entrenar. Además se grafica la curva de ganancia acumulada de cada semilla y del ensamble (`test/curva_ganancia_test.png` y `.csv`). De cada modelo de test también se guarda la importancia de variables (`test/impo_test_NN.txt`) y su promedio (`test/impo_test.txt`).

#%% celda 31 [código]
faltan_hp <- anyNA(unlist(PARAM$mejores_hiperparametros))
if (faltan_hp) stop("Falta definir los mejores hiperparametros en la celda 1.2")

# meses en el mismo orden que en la experimentacion (asi las probabilidades coinciden)
dataset <- leer_meses_fst(archivo_fe, sort(unique(c(PARAM$train_test, PARAM$test, PARAM$train_final, PARAM$future))))
dataset[, clase01 := ifelse(clase_ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)]
campos <- setdiff(colnames(dataset), c("clase_ternaria", "clase01", "azar", "training"))
dir.create(file.path(carpeta_exp, "test"), showWarnings = FALSE)

if (PARAM$test_n_semillas > 0) {
  arch_test <- file.path(carpeta_exp, "test", sprintf("prob_test_%02d.csv", seq_len(PARAM$test_n_semillas)))
  filas_te <- which(dataset$foto_mes %in% PARAM$test)
  faltan <- which(!file.exists(arch_test))

  if (length(faltan)) {
    dtest_train <- armar_dtrain(dataset, which(dataset$foto_mes %in% PARAM$train_test), campos)
    mtest <- armar_matriz(dataset, filas_te, campos)
    for (k in faltan) {
      t0 <- Sys.time()
      param_k <- modifyList(param_final, list(seed = PARAM$semillas_20[k], data_random_seed = PARAM$semilla_primigenia))
      modelo <- lgb.train(data = dtest_train, params = param_k)
      fwrite(data.table(numero_de_cliente = dataset$numero_de_cliente[filas_te], prob = predict(modelo, mtest)), arch_test[k])
      fwrite(lgb.importance(modelo), file.path(carpeta_exp, "test", sprintf("impo_test_%02d.txt", k)), sep = "\t")
      rm(modelo); gc(full = TRUE, verbose = FALSE)
      cat(sprintf("Test semilla %d de %d lista en %.1f min\n", k, PARAM$test_n_semillas,
                  as.numeric(difftime(Sys.time(), t0, units = "mins"))))
    }
    rm(dtest_train, mtest); gc(full = TRUE, verbose = FALSE)
  }

# [Anotación · líneas 450–467] Une las probabilidades de las 5 semillas por cliente y calcula el ensamble como
#   su promedio por fila. Para cada serie ordena de mayor a menor probabilidad y acumula +1.072.500 por cada
#   BAJA+2 y −27.500 por cada otro registro; toma la ganancia acumulada en cada corte de 9.500 a 15.000. Arma
#   una tabla con cada semilla, el ensamble y el promedio de las semillas, la graba en ganancia_test_cortes.csv,
#   la imprime e informa el corte donde el ensamble tiene la ganancia máxima.
  # ganancia por corte de cada semilla y del ensamble
  tt <- dataset[filas_te, list(numero_de_cliente, clase_ternaria)]
  for (k in seq_len(PARAM$test_n_semillas)) {
    p <- fread(arch_test[k])
    tt[p, on = "numero_de_cliente", (sprintf("s%02d", k)) := i.prob]
  }
  cols_t <- sprintf("s%02d", seq_len(PARAM$test_n_semillas))
  tt[, ensamble := rowMeans(.SD), .SDcols = cols_t]
  ganancia_cortes <- function(prob) cumsum(ifelse(tt$clase_ternaria[order(-prob)] == "BAJA+2", 1072500, -27500))[PARAM$cortes]
  tb_test <- data.table(envios = PARAM$cortes)
  for (cc in c(cols_t, "ensamble")) tb_test[, (cc) := ganancia_cortes(tt[[cc]])]
  tb_test[, promedio_semillas := rowMeans(.SD), .SDcols = cols_t]
  fwrite(tb_test, file.path(carpeta_exp, "test", "ganancia_test_cortes.csv"))

  options(scipen = 999)
  cat("\nGanancia en", PARAM$test, "por corte (cada semilla, su promedio y el ensamble):\n")
  print(tb_test)
  cat("Mejor corte del ensamble:", tb_test[which.max(ensamble), envios], "\n")

# [Anotación · líneas 469–493] Calcula la curva de ganancia acumulada cada 50 envíos hasta 20.000 para cada
#   semilla y para el ensamble, la graba en curva_ganancia_test.csv y la grafica con ggplot2: una línea gris por
#   semilla, una negra para el ensamble, la zona de cortes sombreada y una línea punteada en el corte de
#   ganancia máxima del ensamble. Guarda el gráfico en curva_ganancia_test.png.
  # curva de ganancia acumulada (cada 50 envios hasta 20.000): una por semilla y la del ensamble
  pos <- seq(50L, min(20000L, nrow(tt)), by = 50L)
  curvas <- rbindlist(lapply(c(cols_t, "ensamble"), function(cc) {
    g <- cumsum(ifelse(tt$clase_ternaria[order(-tt[[cc]])] == "BAJA+2", 1072500, -27500))
    data.table(serie = cc, envios = pos, ganancia = g[pos])
  }))
  fwrite(curvas, file.path(carpeta_exp, "test", "curva_ganancia_test.csv"))
  corte_ens <- tb_test[which.max(ensamble), envios]

  gra <- ggplot() +
    annotate("rect", xmin = min(PARAM$cortes), xmax = max(PARAM$cortes), ymin = -Inf, ymax = Inf, alpha = 0.08) +
    geom_line(data = curvas[serie != "ensamble"], aes(x = envios, y = ganancia, group = serie), color = "grey65") +
    geom_line(data = curvas[serie == "ensamble"], aes(x = envios, y = ganancia), color = "black", linewidth = 1) +
    geom_vline(xintercept = corte_ens, linetype = "dashed") +
    scale_y_continuous(labels = function(x) format(x, big.mark = ".", decimal.mark = ",", scientific = FALSE)) +
    labs(title = paste0("Ganancia acumulada en ", PARAM$test, " - ", PARAM$experimento),
         subtitle = paste0("Gris: cada semilla de test. Negro: ensamble de ", length(cols_t),
                           ". Sombreado: cortes ", min(PARAM$cortes), "-", max(PARAM$cortes),
                           ". Punteada: mejor corte del ensamble (", corte_ens, ")"),
         x = "Envios", y = "Ganancia") +
    theme_minimal(base_size = 13)
  ggsave(file.path(carpeta_exp, "test", "curva_ganancia_test.png"), gra, width = 12, height = 7)
  options(repr.plot.width = 12, repr.plot.height = 7)
  print(gra)
  rm(curvas, gra, pos)

# [Anotación · líneas 495–505] Lee los archivos de importancia de los modelos de test, promedia Gain y
#   Frequency por variable entre los modelos y graba impo_test.txt. Si test_n_semillas es 0, todo el bloque de
#   test se omite con un mensaje.
  # importancia de variables del test: promedio de las semillas (registro)
  arch_imp_t <- list.files(file.path(carpeta_exp, "test"), pattern = "^impo_test_[0-9]+\\.txt$", full.names = TRUE)
  if (length(arch_imp_t)) {
    imp_t <- rbindlist(lapply(arch_imp_t, fread))
    imp_t <- imp_t[, list(Gain = sum(Gain) / length(arch_imp_t), Frequency = sum(Frequency) / length(arch_imp_t),
                          modelos = .N), by = Feature][order(-Gain)]
    fwrite(imp_t, file.path(carpeta_exp, "test", "impo_test.txt"), sep = "\t")
    cat("Importancia del test (promedio de", length(arch_imp_t), "modelos):", file.path(carpeta_exp, "test", "impo_test.txt"), "\n")
  }
  rm(tt, filas_te, p)
} else cat("Test en 202106 omitido (PARAM$test_n_semillas = 0)\n")

# [Anotación · líneas 507–527] Toma las primeras 20 semillas de la lista, calcula los índices de las filas de
#   entrenamiento (202103 a 202106) y de las filas a predecir (202108), imprime la cantidad de registros por mes
#   y clase, y arma una sola vez el lgb.Dataset de entrenamiento y la matriz de 202108. Luego borra el dataset
#   de memoria.
#%% celda 32 [texto]
# 2. Producción

## 2.1 Dataset final
Del dataset ya leído en 1.3 se toman los meses de entrenamiento (202103 a 202106) y el mes a predecir (202108). La clase está en binario (BAJA+1 y BAJA+2 valen 1, CONTINUA vale 0) y se usan todas las columnas como variables salvo la clase.

#%% celda 33 [código]
PARAM$semillas <- PARAM$semillas_20[seq_len(PARAM$n_semillas)]

filas_train  <- which(dataset$foto_mes %in% PARAM$train_final)
filas_future <- which(dataset$foto_mes %in% PARAM$future)
ids_future   <- dataset$numero_de_cliente[filas_future]

print(dataset[filas_train, .N, keyby = list(foto_mes, clase_ternaria)])
cat("A predecir:", length(filas_future), "clientes de", PARAM$future, "| variables:", length(campos), "\n")

# datos en el formato de LightGBM: se arman una sola vez y sirven para las 20 semillas
dtrain  <- armar_dtrain(dataset, filas_train, campos)
mfuture <- armar_matriz(dataset, filas_future, campos)
rm(dataset, filas_train, filas_future)
gc(full = TRUE, verbose = FALSE)

# [Anotación · líneas 529–553] Para cada semilla: si ya existe su archivo de probabilidades, la saltea; si no,
#   entrena un LightGBM con param_final cambiando sólo seed (data_random_seed queda en 110017), predice 202108,
#   graba numero_de_cliente y probabilidad en probabilidades/prob_<experimento>_NN.csv y la importancia de
#   variables en impo_<experimento>_NN.txt, e imprime el tiempo y los 5 clientes de mayor probabilidad.
#%% celda 34 [texto]
## 2.2 LightGBM finales
20 modelos con los mismos hiperparámetros; lo único que cambia es la semilla. Cada uno entrena con todos los datos de 202103 a 202106 y predice la probabilidad de baja de cada cliente en 202108. La probabilidad de cada semilla se guarda en `probabilidades/`; si ya existe, no se vuelve a entrenar.

De cada modelo también se guarda la importancia de variables (`impo_..._NN.txt`, de `lgb.importance`), y al final se arma `impo.txt` con el promedio de los modelos finales.

#%% celda 35 [código]
arch_prob <- file.path(carpeta_exp, "probabilidades", sprintf("prob_%s_%02d.csv", PARAM$experimento, seq_along(PARAM$semillas)))

for (k in seq_along(PARAM$semillas)) {
  if (file.exists(arch_prob[k])) { cat("Semilla", PARAM$semillas[k], "ya calculada\n"); next }
  t0 <- Sys.time()
  param_k <- modifyList(param_final, list(seed = PARAM$semillas[k], data_random_seed = PARAM$semilla_primigenia))
  modelo <- lgb.train(data = dtrain, params = param_k)
  fwrite(data.table(numero_de_cliente = ids_future, prob = predict(modelo, mfuture)), arch_prob[k])
  fwrite(lgb.importance(modelo), sub("\\.csv$", ".txt", sub("prob_", "impo_", arch_prob[k])), sep = "\t")
  cat(sprintf("Semilla %d (%d de %d) lista en %.1f min | faltan %d\n", PARAM$semillas[k], k, length(PARAM$semillas),
              as.numeric(difftime(Sys.time(), t0, units = "mins")), sum(!file.exists(arch_prob))))
  # csv del modelo recien terminado
  p <- fread(arch_prob[k]); print(head(p[order(-prob)], 5)); rm(p)
  rm(modelo)
  gc(full = TRUE, verbose = FALSE)
}
rm(dtrain, mfuture)
gc(full = TRUE, verbose = FALSE)

# [Anotación · líneas 555–565] Junta los archivos de importancia de los modelos finales, promedia Gain y
#   Frequency por variable (una variable ausente en un modelo cuenta como 0 en ese modelo), graba impo.txt e
#   imprime las 30 primeras.
# importancia de variables: promedio de los modelos finales (Gain y Frequency; si una variable
# no se uso en un modelo cuenta como 0 en ese modelo)
arch_imp <- list.files(file.path(carpeta_exp, "probabilidades"), pattern = "^impo_.*\\.txt$", full.names = TRUE)
if (length(arch_imp)) {
  imp <- rbindlist(lapply(arch_imp, fread))
  imp_prom <- imp[, list(Gain = sum(Gain) / length(arch_imp), Frequency = sum(Frequency) / length(arch_imp),
                         modelos = .N), by = Feature][order(-Gain)]
  fwrite(imp_prom, file.path(carpeta_exp, "impo.txt"), sep = "\t")
  cat("Importancia de variables (promedio de", length(arch_imp), "modelos finales) en", file.path(carpeta_exp, "impo.txt"), "\n")
  print(head(imp_prom, 30))
}

# [Anotación · líneas 567–599] Para cada tamaño de ensamble (5, 10, 15 y 20): une por cliente las
#   probabilidades de los primeros n modelos verificando que tengan los mismos clientes, calcula el promedio por
#   fila y ordena de mayor a menor. Graba la tabla completa en prediccion_<experimento>_ensNN_202108.csv y, para
#   cada corte de 9.500 a 15.000, un archivo con los primeros clientes del orden en zulip_cortes/ensNN/<corte>/.
#   Guarda cada ensamble en la lista ensambles.
#%% celda 36 [texto]
## 2.3 Clasificación
Ensambles: para cada cliente se promedian las probabilidades de los primeros 5, 10, 15 y 20 modelos y se ordena de mayor a menor. De cada ensamble se generan los archivos para Zulip con los primeros 9.500, 10.000, …, 15.000 clientes del ranking.

```
zulip_cortes/ens05/<corte>/<experimento>_ens05_c<corte>.csv   (y ens10, ens15, ens20)
```

#%% celda 37 [código]
arch_prob <- file.path(carpeta_exp, "probabilidades", sprintf("prob_%s_%02d.csv", PARAM$experimento, seq_along(PARAM$semillas)))

ensambles <- list()
for (n in PARAM$bloques) {
  tb <- data.table(numero_de_cliente = ids_future, foto_mes = PARAM$future)
  for (k in seq_len(n)) {
    p <- fread(arch_prob[k])
    stopifnot(nrow(p) == nrow(tb), setequal(p$numero_de_cliente, tb$numero_de_cliente))
    tb[p, on = "numero_de_cliente", (sprintf("prob_%02d", k)) := i.prob]
  }
  tb[, prob := rowMeans(.SD), .SDcols = sprintf("prob_%02d", seq_len(n))]
  setorder(tb, -prob)

  etiqueta <- sprintf("ens%02d", n)
  fwrite(tb, file.path(carpeta_exp, paste0("prediccion_", PARAM$experimento, "_", etiqueta, "_", PARAM$future, ".csv")))
  for (corte in PARAM$cortes) {
    carpeta <- file.path(carpeta_exp, "zulip_cortes", etiqueta, corte)
    dir.create(carpeta, recursive = TRUE, showWarnings = FALSE)
    escribir_zulip(tb$numero_de_cliente[seq_len(corte)],
                   file.path(carpeta, sprintf("%s_%s_c%d.csv", sub("_entrega$", "", PARAM$experimento), etiqueta, corte)))
  }
  cat("Ensamble de", n, "modelos ->", file.path(carpeta_exp, "zulip_cortes", etiqueta), "\n")
  ensambles[[etiqueta]] <- tb[, list(numero_de_cliente, prob)]
}

# [Anotación · líneas 601–619] Fija PARAM$envios en 12000 y verifica que esté entre 9.500 y 15.000. Toma el
#   ensamble de 20 modelos, ya ordenado, y escribe los primeros 12.000 numero_de_cliente en
#   zulip/C1_E012_ensamble_20S_12000.csv. Vuelve a leer el archivo e imprime la cantidad de filas y de
#   identificadores distintos.
#%% celda 38 [texto]
# 3. Zulip
Archivo final para la entrega: el ensamble de los **20 modelos**, cortado en `PARAM$envios` clientes, sin encabezado y como enteros. Se sube por mensaje privado a `@competencia-uno`.

El archivo es el mismo que aparece en `zulip_cortes/ens20/12000/`.

#%% celda 39 [código]
PARAM$envios <- 12000   # cantidad de clientes a realizar envios

archivo_zulip <- file.path(carpeta_exp, "zulip", sprintf("C1_E012_ensamble_20S_%d.csv", PARAM$envios))
stopifnot(!is.na(PARAM$envios), PARAM$envios >= 9500L, PARAM$envios <= 15000L)

final <- ensambles[["ens20"]]          # ya ordenado por probabilidad promedio de los 20 modelos
escribir_zulip(final$numero_de_cliente[seq_len(PARAM$envios)], archivo_zulip)

control <- readLines(archivo_zulip)
cat("Archivo para Zulip:", archivo_zulip, "\n")
cat("Filas:", length(control), "| ids distintos:", uniqueN(control), "\n")
head(control)
````


## Explicaciones del alumno (texto original)

### README.md

> # DMEyF 2026 — Competencia 01
>
> Predicción de bajas (BAJA+2) de clientes del banco para 202108. Todas las notebooks están en R y se corrieron en una VM de Google Cloud con 8 vCPU y 64 GB de RAM.
>
> ## Datos
>
> Copiar el dataset crudo `competencia_01_crudo.csv` (también sirve `.csv.gz` o `.zip`) en:
>
> ```
> ~/buckets/b1/datasets/
> ```
>
> La carpeta tiene que existir. Las notebooks generan solas la clase ternaria y el dataset con feature engineering, y escriben sus resultados en `~/buckets/b1/exp/`. Si se usa otra carpeta base, cambiar `carpeta_base` en la primera celda de cada notebook.
>
> ## Notebooks
>
> | Notebook | Qué hace |
> |---|---|
> | `C1_E012_con-rank-final_BO.ipynb` | Desarrollo de la E012: feature engineering y **optimización bayesiana** |
> | `C1_E012_modelo-MH-entrega.ipynb` | Entrega de la E012: hiperparámetros fijos, test en 202106, 20 modelos finales, ensamble y archivo para Zulip |
> | `exp/HTC1_E012/BO_eval_kfold5_auc.txt` | Cada evaluación de la optimización bayesiana, en orden (hiperparámetros, AUC, minutos) |
> | `exp/HTC1_E012/BO_log_kfold5_auc.txt` | Las mismas evaluaciones ordenadas por AUC (archivo final de la BO cortada) |
>
> **Feature engineering**
> `ccajas_depositos` en NA para 202105 → lag1/delta1 y lag2/delta2 → ranking por mes con cero fijo de todas las variables (salvo `numero_de_cliente`, `foto_mes` y `clase_ternaria`).
>
> **Optimización bayesiana:** `mlrMBO`, k-fold 5 estratificado sobre 202103–202105, métrica AUC, sin undersampling, rangos de la notebook z495 (`num_iterations` 64–4096, `num_leaves` 16–2048, `min_sum_hessian_in_leaf` 1e-06–0.1).
>
> ## Cómo reproducir la entrega
>
> Los hiperparámetros de los modelos finales **no se optimizan en la notebook de entrega**: vienen de la BO de la notebook de desarrollo del mismo experimento. Por eso hay dos formas de correrlo.
>
> ## Origen de los hiperparámetros
>
> Los hiperparámetros de los modelos finales salen de la optimización bayesiana de la notebook de desarrollo `C1_E012_con-rank-final_BO.ipynb` (sección 4.5): k-fold 5 estratificado, métrica AUC, sin undersampling, rangos de la notebook z495. La BO se cortó después de 16 evaluaciones (12 puntos iniciales + 4 iteraciones bayesianas) y se tomó el punto de mayor AUC.
>
> El registro completo está en `exp/HTC1_E012/`:
> - `BO_eval_kfold5_auc.txt`: cada evaluación en el orden en que se hizo (hiperparámetros, AUC y minutos).
> - `BO_log_kfold5_auc.txt`: las mismas evaluaciones ordenadas por AUC.
>
> ### Envío final
>
> | Experimento | Modelos en el ensamble | Envíos | Archivo |
> |---|---|---|---|
> | C1_E012 | 20 | 12000 | `exp/C1_E012_entrega_MH/zulip/C1_E012_ensamble_20S_12000.csv` |
>
> El archivo es el ensamble de los 20 modelos (promedio por cliente de las probabilidades, 20 semillas fijas), ordenado de mayor a menor y cortado en la cantidad de envíos elegida.

