# pablogarciaparisi — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: pablogarciaparisi
- Repositorio: https://github.com/pablogarciaparisi/dmeyf2026-competencia1
- Link posteado: https://github.com/pablogarciaparisi/dmeyf2026-competencia1/tree/main
- Commit: bd3a7318275cf1a2506a7a23f6363b543950f55b
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/pablogarciaparisi/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/pablogarciaparisi.json

## Resumen

La entrega contiene tres notebooks de R (kernel IRkernel) y un README de tres líneas que indica correrlos en orden. El notebook 1 (SAFE P2) descarga el dataset crudo, calcula la clase, arma para cada variable el valor actual, lag 1, delta 1, lag 2 y delta 2, los convierte en un rank con signo dentro de cada mes (cero fijo), excluye los préstamos personales, corre una optimización bayesiana (entrena en 202103+202104 y valida en 202106 por AUC), retira de mayo y junio el 5% de las filas CONTINUA con mayor probabilidad fuera de fold y entrena LightGBM en 202105+202106 con 10 semillas, cuyas probabilidades promedia. El notebook 2 (E012) usa las variables crudas con lags y deltas de 1 a 4 meses (1.348 variables), busca hiperparámetros en una partición 80/20 de junio, entrena en junio completo y promedia las semillas. El notebook 3 lee las probabilidades de agosto de ambos modelos, las convierte en posiciones, promedia las posiciones con pesos 50% y 50% y escribe la lista de los 12.500 clientes de menor posición promedio, además de un archivo por cada corte de 10.500 a 15.000.

**Qué entrega.** Según el README, el archivo final es SUBMISSION_FINAL__P2_E012__RANK__P2_50p00pct__E012_50p00pct__dc97cf4f7614__TOP12500.csv, en la carpeta /home/ds/Expe/metaensemblesCorr//P2_E012__RANK__P2_50p00pct__E012_50p00pct__dc97cf4f7614/. Por el código del notebook 3 es una columna sin encabezado con los 12.500 numero_de_cliente de menor posición promedio entre P2 y E012. El archivo no está en el repositorio.

**Cómo se ejecuta.** El README indica correr los tres notebooks en el orden de su numeración (1, 2, 3), preparados para una misma VM. Cada notebook trae una sección de uso: kernel R, revisar el BLOQUE 1 y ejecutar todas las celdas en orden; al volver a ejecutar, los checkpoints guardados evitan repetir entrenamientos. En el notebook 3 se edita sólo el BLOQUE 1 (rutas, semillas declaradas, combinación, método y corte).

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (binaria2): positivo = BAJA+1 o BAJA+2, negativo = CONTINUA. La clase ternaria se calcula en el propio notebook a partir del crudo, con los dos períodos siguientes de cada cliente; 202108 queda sin clase.
- **Meses de entrenamiento:** 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa submuestreo al azar de CONTINUA. En P2 se retira de 202105 y de 202106 el 5% de las filas CONTINUA con mayor probabilidad fuera de fold (floor(n × 5/100) por mes; 8.087 y 8.107 filas según la salida guardada) y se conservan todas las BAJA. E012 entrena con junio completo.
- **Calidad de datos:** ccajas_depositos se pasa a NA en 202105 antes de calcular lags y deltas, en los dos notebooks de entrenamiento. No se imputan valores faltantes. Se comparan con valores escritos en el código la cantidad de filas por mes, los conteos por mes y clase y los 164.647 clientes de 202108.
- **Drifting:** En SAFE P2 cada variable, con sus lags y deltas, se reemplaza por un rank con signo calculado dentro de cada mes: negativos entre -1 y 0, cero fijo en 0, positivos entre 0 y 1 y NA conservados. En E012 las variables entran crudas.
- **Variables dentro del mes:** No se observa en el código.
- **Variables históricas:** SAFE P2: lag 1, delta 1, lag 2 y delta 2 de cada variable numérica incluida, por cliente y mes calendario, todas pasadas a rank con signo (según la salida guardada, 142 variables por bloque y 710 en total con las actuales). E012: lags 1 a 4 de 150 variables, deltas 1 a 4 de 148 (Master_status y Visa_status sin delta) y cuatro indicadores lagK_disponible; 1.348 variables en total con las actuales.
- **Selección de variables:** No se observa selección por importancia. SAFE P2 toma todas las columnas numéricas que no son metadatos ni fechas (expresión regular sobre el nombre) y excluye cprestamos_personales y mprestamos_personales en sus cinco versiones. E012 usa listas de nombres escritas en el código (150 con lag, 148 con delta), sin los dos préstamos personales, e incluye numero_de_cliente y foto_mes como predictores.
- **Optimización de hiperparámetros:** Optimización bayesiana con mlr3mbo y bbotk en los dos modelos: surrogate Kriging (regr.km, BFGS, nugget estimado), adquisición EI con búsqueda al azar de 1.000 puntos, 20 evaluaciones como máximo, presupuesto bo_horas=8, semilla 727777 y AUC como métrica. Busca num_iterations (64–4096), num_leaves y min_sum_hessian_in_leaf (0,000001–0,1). SAFE P2: 6 puntos iniciales LHS + 14 de EI, num_leaves 16–1024, entrena en 202103+202104 y valida en 202106. E012: 10 LHS + 10 EI, num_leaves 16–2048, entrena en el 80% de junio y valida en el 20%. Se toma la evaluación de mayor AUC; en empates, la más temprana.
- **Hiperparámetros finales:** Los tres hiperparámetros buscados se leen del checkpoint de selección de cada BO; no están escritos en el código. Según las salidas guardadas en los notebooks: SAFE P2 usa num_iterations=3246, num_leaves=951, min_sum_hessian_in_leaf=0,009123316 (evaluación 9) y E012 usa num_iterations=2077, num_leaves=682, min_sum_hessian_in_leaf=0,0626847 (evaluación 17). Fijos en ambos: learning_rate=0,005, feature_fraction=0,50, min_data_in_leaf=0, max_bin=31, max_depth=-1, lambda_l1=0, lambda_l2=0, bagging_fraction=1, objetivo binario, sin early stopping. SAFE P2 agrega feature_fraction_bynode=0,20 y num_threads=4.
- **Semillas:** Diez semillas escritas en el código (727777, 773777, 775777, 777737, 787777, 777727, 777773, 777775, 777787, 797777), extendidas a 50 con sample.int bajo set.seed(727777) y L'Ecuyer-CMRG. P2 entrena con las primeras 10. E012 entrena con 10 y luego la celda 17 sube n_semillas a 20; el notebook 3 lee el ensemble E012 de 12 semillas (carpeta n12_*) y el de P2 de 10 (n10_*). La BO, la partición 80/20 y los folds de la OOF de E012 usan la semilla 727777; los folds del HNC, set.seed(727777 + y) con y = 0 y 1. La salida guardada del notebook 3 muestra P2 declarada con 5 semillas.
- **Cantidad de semillas:** 12
- **Ensamble:** Dos niveles. Dentro de cada modelo: promedio aritmético de las probabilidades de agosto entre semillas (P2: columna prediction; E012: prediction_media, y además rank_medio, que el notebook 3 no lee). Entre modelos (notebook 3, método RANK): cada probabilidad promedio se convierte en posición con frank(-p) y empates promedio, y las posiciones se promedian con pesos 0,50 para P2 y 0,50 para E012; se ordena por posición promedio ascendente y, en empates, por numero_de_cliente.
- **Corte:** Cantidad fija escrita en el código: corte_final=12.500 clientes. El notebook 3 escribe además un archivo por cada corte de 10.500 a 15.000 de a 500 (10 cortes). Los notebooks 1 y 2 escriben listas propias de cada modelo para cortes de 9.500 a 15.000 y de 9.000 a 15.000.
- **Validación:** SAFE P2: la BO entrena en 202103+202104 y mide AUC en 202106; por cada evaluación guarda también la curva de ganancia de junio (+1.072.500 por BAJA+2, −27.500 por el resto) y GainBand, el promedio de la ganancia acumulada en los cortes 11.500 a 15.000 de a 500. La limpieza HNC usa 5 folds agrupados por cliente sobre 202105+202106. E012: la BO mide AUC y Brier en un 20% de junio sorteado dentro de cada clase ternaria y entrena en el 80% restante; después de la producción calcula predicciones fuera de fold de junio con 5 folds y 5 semillas, con AUC, GainBand (11.500 a 13.500) y ganancia en 12.500. Los hiperparámetros se eligen por AUC.
- **Salidas:** Notebook 1, en OUT/checkpoints: predicciones de agosto por semilla y, por cada cantidad de semillas, una carpeta ensembles/P2/nNN_<firma> con <nombre>_probabilidades_agosto.csv, el ranking completo y 12 listas _topK.csv. Notebook 2: predicciones_agosto.csv por semilla, carpetas ensembles/nNN_<firma> con ensemble_agosto_ambos_criterios.csv, dos rankings y 26 listas, y los archivos de la OOF de junio. Notebook 3, en /home/ds/Expe/metaensemblesCorr/<etiqueta>/: PREDICCIONES_RANKING_COMPLETO__*.csv, diez SUBMISSION__*__TOPn.csv, SUBMISSION_FINAL__*__TOP12500.csv, RESUMEN__*.csv y manifiesto.rds. Ninguno de estos archivos está en el repositorio.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)
- Validación cruzada (`validacion.validacion_cruzada`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: El README indica que los notebooks están preparados para correr en una misma VM. Los notebooks piden kernel R (IRkernel) y, para el respaldo, gcloud autenticado; las rutas por defecto son /home/ds/Expe y un bucket gs:// propio (respaldo desactivado en el código guardado). El texto del notebook 1 menciona pruebas en R 4.3.3 con mlr3mbo 1.2.1 y bbotk 1.13.1; los metadatos de los .ipynb registran R 4.6.1. El código lista 11 paquetes sin versión, instala los que falten y guarda sessionInfo() en un checkpoint que no está en el repositorio. El notebook 1 fija num_threads=4.

## Pasos del camino de la entrega

1. **Configuración y semillas (notebook 1).** Define carpetas, URL del crudo, interruptores (P2 activo, P3 inactivo, 10 semillas, bo_horas=8), las 10 semillas base con su extensión a 50, la lista PARAM con meses, cortes y valores de ganancia, y los parámetros fijos de LightGBM. (`1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb` líneas 62–157)
2. **Escritura atómica y checkpoints.** Funciones que escriben cada resultado en un temporal, lo verifican y lo cierran con un COMMIT firmado por MD5; al volver a ejecutar, lo ya cerrado se reutiliza. El respaldo en GCS está desactivado en el código guardado. Las mismas funciones se repiten en el notebook 2. (`1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb` líneas 159–333; `2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb` líneas 90–264)
3. **Lectura del crudo y cálculo de la clase.** Descarga competencia_01_crudo.csv, comprueba los meses 202103 a 202108, calcula CONTINUA, BAJA+1 y BAJA+2 con los dos períodos siguientes de cada cliente y crea binaria2 (1 = BAJA+1 o BAJA+2). Compara los conteos por mes y clase con una tabla escrita en el código. (`1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb` líneas 337–359; `1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb` líneas 475–533)
4. **Corrección de ccajas_depositos.** Pasa ccajas_depositos a NA en 202105 antes de calcular lags y deltas. El notebook 2 hace lo mismo. (`1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb` líneas 535–541; `2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb` líneas 429–435)
5. **Variables SAFE: lags, deltas y rank con signo por mes.** Para 202103 a 202106 y 202108 calcula, por variable numérica, valor actual, lag 1, delta 1, lag 2 y delta 2, y reemplaza cada una por su rank con signo dentro del mes (cero fijo, NA conservados). Después quita del conjunto de variables las cinco versiones de cprestamos_personales y mprestamos_personales. (`1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb` líneas 360–369; `1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb` líneas 543–640)
6. **Optimización bayesiana SAFE.** Entrena en 202103+202104 y mide AUC en 202106 con hasta 20 evaluaciones (6 LHS + 14 EI) sobre num_iterations, num_leaves y min_sum_hessian_in_leaf; guarda además la curva de ganancia de junio. Elige la evaluación de mayor AUC y la deja fija en un checkpoint. (`1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb` líneas 642–815; `1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb` líneas 844–872)
7. **Limpieza HNC de mayo y junio.** Con los hiperparámetros elegidos entrena 5 modelos en folds agrupados por cliente sobre 202105+202106 y obtiene una probabilidad fuera de fold por fila. En cada mes marca para excluir el 5% de las filas CONTINUA de mayor probabilidad; las BAJA se conservan. (`1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb` líneas 874–1001)
8. **Entrenamiento P2 y promedio de semillas.** Entrena un LightGBM por semilla (10) con 202105+202106 sin las filas marcadas, predice 202108 y promedia las probabilidades. Escribe el archivo de probabilidades de agosto que lee el notebook 3 y listas para 12 cortes. (`1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb` líneas 1003–1151)
9. **E012: datos y variables crudas con historia de 4 meses.** El notebook 2 vuelve a leer el crudo y a calcular la clase. Para 202106 y 202108 arma 1.348 variables: las actuales (incluidos numero_de_cliente y foto_mes), lags 1 a 4 de 150 variables, deltas 1 a 4 de 148 e indicadores de disponibilidad de cada lag, sin los préstamos personales. (`2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb` líneas 394–437; `2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb` líneas 439–588; `2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb` líneas 590–675)
10. **E012: partición 80/20 de junio y optimización bayesiana.** Sortea el 20% de cada clase ternaria de junio como validación y corre la BO (10 LHS + 10 EI) entrenando en el 80% y midiendo AUC en el 20%. Elige la evaluación de mayor AUC. (`2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb` líneas 677–703; `2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb` líneas 705–876; `2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb` líneas 917–945)
11. **E012: entrenamiento en junio completo y ensembles.** Entrena un LightGBM por semilla con las 164.114 filas de junio y predice agosto. Después de cada semilla escribe ensemble_agosto_ambos_criterios.csv con la probabilidad media y el rank medio de las semillas disponibles. Corre primero con 10 semillas y luego con n_semillas=20. (`2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb` líneas 962–1077)
12. **E012: OOF de junio posterior a la producción.** Con 5 folds y 5 semillas calcula predicciones fuera de fold de junio y registra AUC, GainBand y ganancia en 12.500; dos celdas finales leen esas métricas y copian el ensemble a otra ruta. Esta parte no interviene en la predicción de agosto. (`2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb` líneas 1079–1205; `2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb` líneas 1214–1317)
13. **Metaensemble: lectura y alineación de las dos entradas.** El notebook 3 busca el archivo del ensemble E012 de 12 semillas y el de P2 de 10, lee de cada uno numero_de_cliente y la probabilidad, exige 164.647 clientes con probabilidades entre 0 y 1 y alinea ambas tablas por ID. (`3-DMEYF2026_METAENSEMBLES_SUBMISSIONS_FINAL.ipynb` líneas 16–67; `3-DMEYF2026_METAENSEMBLES_SUBMISSIONS_FINAL.ipynb` líneas 99–142; `3-DMEYF2026_METAENSEMBLES_SUBMISSIONS_FINAL.ipynb` líneas 298–317)
14. **Combinación por promedio de posiciones.** Convierte la probabilidad de cada modelo en posición (1 = mayor probabilidad, empates promedio), suma 0,50 × posición de P2 y 0,50 × posición de E012 y ordena de menor a mayor, con numero_de_cliente como desempate. (`3-DMEYF2026_METAENSEMBLES_SUBMISSIONS_FINAL.ipynb` líneas 118–125; `3-DMEYF2026_METAENSEMBLES_SUBMISSIONS_FINAL.ipynb` líneas 144–163)
15. **Escritura de las listas y del archivo final.** En una carpeta cuyo nombre lleva la combinación, el método, los pesos y una firma de 12 caracteres, escribe el ranking completo, una lista por cada corte de 10.500 a 15.000 y SUBMISSION_FINAL con los primeros 12.500 clientes, todas sin encabezado. No envía nada. (`3-DMEYF2026_METAENSEMBLES_SUBMISSIONS_FINAL.ipynb` líneas 188–259; `3-DMEYF2026_METAENSEMBLES_SUBMISSIONS_FINAL.ipynb` líneas 319–331)

## Archivos

- `3-DMEYF2026_METAENSEMBLES_SUBMISSIONS_FINAL.ipynb` · principal · Jupyter (R) · 331 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pablogarciaparisi/3-DMEYF2026_METAENSEMBLES_SUBMISSIONS_FINAL.ipynb.txt) — Notebook de R que combina las probabilidades de agosto de P2 y E012 por promedio ponderado de posiciones (50% y 50%) y escribe las listas de clientes para cortes de 10.500 a 15.000 y la lista final de 12.500.
- `2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb` · principal · Jupyter (R) · 1317 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pablogarciaparisi/2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb.txt) — Notebook de R que produce el modelo E012: variables crudas con lags y deltas de 1 a 4 meses (1.348), BO en junio 80/20, entrenamiento en junio completo por semilla y ensembles por probabilidad media y por rank medio; deja el archivo que lee el notebook 3. Después corre una OOF de junio y dos celdas de consulta.
- `README.md` · explicacion · Markdown · 3 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pablogarciaparisi/README.md.txt) — Tres líneas: indica correr los notebooks en orden en una misma VM y da el nombre y la carpeta del archivo final de envío.
- `1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb` · principal · Jupyter (R) · 1176 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pablogarciaparisi/1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb.txt) — Notebook de R que produce el modelo SAFE P2: descarga el crudo, arma la clase y las variables con rank con signo por mes, busca hiperparámetros, aplica la limpieza HNC del 5% y entrena LightGBM en 202105+202106 con 10 semillas; deja las probabilidades promedio de agosto que lee el notebook 3. Contiene también la variante P3 (202103 a 202106), desactivada en el código guardado.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### 3-DMEYF2026_METAENSEMBLES_SUBMISSIONS_FINAL.ipynb

Notebook de R que combina las probabilidades de agosto de P2 y E012 por promedio ponderado de posiciones (50% y 50%) y escribe las listas de clientes para cortes de 10.500 a 15.000 y la lista final de 12.500.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–14] Celda de texto. Indica que el notebook sólo lee y combina predicciones ya
#   generadas (no entrena ni envía), que se edita únicamente el BLOQUE 1, y define los dos métodos: RANK
#   (promedio ponderado de posiciones; menor posición va primero) y PROB (promedio ponderado de probabilidades).
#   Señala que las entradas se alinean por ID y que se exige el universo de 164.647 clientes.
#%% celda 1 [texto]
# DMEyF 2026 — Metaensembles finales de agosto

**Sólo lectura y combinación de predicciones.** No descarga el dataset, no entrena, no ejecuta BO/OOF, no modifica E012, E015 ni SAFE, y no envía submissions.

**Uso:** editar únicamente el **BLOQUE 1** (rutas, semillas, combinaciones, método y corte). Ejecutar los bloques 1 a 5 en orden. El BLOQUE 4 hace pruebas muy pequeñas en una carpeta temporal; el BLOQUE 5 exporta los candidatos reales.

- **RANK**: promedio ponderado de posiciones (menor = mejor). 
- **PROB**: promedio ponderado de `prediction_media` (E012) o `prediction` (E015/SAFE); mayor = mejor. No confundir los dos métodos.
- Todas las entradas se alinean **por ID**, nunca por orden físico. Se exige el universo idéntico de 164.647 clientes y probabilidades en [0,1].
- Si los archivos todavía están repartidos entre VM, copiarlos sin modificarlos a la VM de ejecución y completar las rutas en el BLOQUE 1. También sirven directamente las carpetas de checkpoints cuando todos los experimentos estén juntos.
- La carpeta de salida usa nombres descriptivos y una firma basada en los **archivos de entrada**. Una segunda ejecución idéntica reutiliza sólo salidas completas y verificadas; jamás sobrescribe una salida diferente.

**Nota:** La cantidad de semillas se declara en la configuración y aparece en el resumen, pero este notebook no reentrena ni determina el número a partir de probabilidades: conviene verificarlo contra el checkpoint original.

# [Anotación · líneas 16–36] Carga data.table y define las rutas absolutas de entrada
#   (/home/ds/Expe/experimentos) y de salida (/home/ds/Expe/metaensemblesCorr/). Busca con Sys.glob el archivo
#   ensemble_agosto_ambos_criterios.csv del ensemble E012 de 12 semillas (carpeta n12_*) y el archivo
#   *_n10_probabilidades_agosto.csv del ensemble P2 de 10 semillas, y exige que haya exactamente uno de cada
#   uno.
#%% celda 2 [código]
# BLOQUE 1 — CONFIGURACIÓN: EDITAR SÓLO ESTA CELDA #####
suppressPackageStartupMessages(library(data.table))

raiz <- "/home/ds/Expe/experimentos"
#salida <- "/home/ds/Expe/metaensembles/DMEYF2026_V1"
salida <- "/home/ds/Expe/metaensemblesCorr/"

archivo_E012 <- Sys.glob(file.path(
  raiz,
  "C01_E012_RAW_T4_BO_FINAL_V1/checkpoints/ensembles/n12_*/ensemble_agosto_ambos_criterios.csv"
))

archivo_P2 <- Sys.glob(file.path(
  raiz,
  "SAFE_P2_P3_FINAL_HNC5_V1/checkpoints/ensembles/P2/n10_*/*_n10_probabilidades_agosto.csv"
))

stopifnot(length(archivo_E012) == 1L)
stopifnot(length(archivo_P2) == 1L)


# [Anotación · líneas 38–51] Asigna las rutas a los modelos E012 y P2 (E015 y P3 quedan en NA), declara la
#   cantidad de semillas de cada uno (E012=12, P2=10) y la columna de probabilidad a leer: prediction_media para
#   E012 y prediction para los demás. No se configura columna de rank, por lo que la posición se calcula a
#   partir de la probabilidad.
# Cambiar una ruta al pasar de 5 a 10/12/20 semillas. NA = aún no disponible.
rutas <- c(
  E012 = archivo_E012,
  E015 = NA_character_,
  P2   = archivo_P2,
  P3   = NA_character_
)
    
semillas <- c(E012=12L, E015=NA_integer_,P2=10L, P3=NA_integer_)

# Columnas confirmadas en las implementaciones originales.
# Si una nueva versión exporta otra columna, corregir aquí tras inspeccionar el CSV.
columnas_prob <- c(E012="prediction_media", E015="prediction", P2="prediction", P3="prediction")
columnas_rank <- c(E012=NA_character_, E015=NA_character_, P2=NA_character_, P3=NA_character_) #"rank_medio"

# [Anotación · líneas 53–67] Elige el método RANK y una única combinación activa, P2_E012, con pesos 0,50 y
#   0,50 (las otras cuatro están comentadas). Define los cortes de 10.500 a 15.000 de a 500, el corte final de
#   12.500 y el tamaño esperado de 164.647 clientes.
metodo <- "RANK"                     # "RANK" o "PROB"
combinaciones <- list(
  #E012_E015 = c(E012=0.50, E015=0.50),
  P2_E012 = c(P2=0.50, E012=0.50)
  # P2_E015 = c(P2=0.50, E015=0.50),
  # P2_E012_E015 = c(P2=1/3, E012=1/3, E015=1/3),
  # P3_E012 = c(P3=0.50, E012=0.50)
)

cortes <- seq(10500L, 15000L, by=500L)
corte_final <- 12500L              # También genera una copia marcada "FINAL"
n_clientes <- 164647L

message("Configuración: ", metodo, " | ", length(combinaciones),
        " combinación(es) | corte final ", corte_final)

# [Anotación · líneas 69–97] validar_config() comprueba método, nombres de combinaciones, cortes y corte
#   final. normalizar_pesos() exige pesos positivos con nombres de modelos conocidos y los divide por su suma.
#%% celda 3 [código]
# BLOQUE 2 — LEER Y VALIDAR CADA ENTRADA #####
validar_config <- function() {
  if (!metodo %in% c("RANK","PROB")) stop("metodo debe ser RANK o PROB")
  if (!length(combinaciones) || is.null(names(combinaciones)) ||
      anyNA(names(combinaciones)) || any(!nzchar(names(combinaciones))) ||
      anyDuplicated(names(combinaciones))) stop("Nombrar cada combinación sin duplicados")
  if (any(!grepl("^[A-Za-z0-9_]+$",names(combinaciones))))
    stop("Nombres de combinaciones: sólo letras, números y guión bajo")
  if (anyNA(cortes) || any(cortes != as.integer(cortes)) ||
      any(cortes < 1L | cortes > n_clientes) || anyDuplicated(cortes))
    stop("Cortes inválidos")
  if (length(corte_final)!=1L || is.na(corte_final) ||
      corte_final != as.integer(corte_final) || corte_final < 1L ||
      corte_final > n_clientes) stop("corte_final inválido")
  if (length(n_clientes)!=1L || is.na(n_clientes) || n_clientes<1L)
    stop("n_clientes inválido")
  invisible(TRUE)
}

normalizar_pesos <- function(p) {
  if (!is.numeric(p) || is.null(names(p)) || !length(p) ||
      anyNA(names(p)) || any(!nzchar(names(p))) || anyDuplicated(names(p)))
    stop("Los pesos deben ser un vector numérico con nombres de modelos únicos")
  if (any(!names(p) %in% names(rutas))) stop("Modelo desconocido: ",
                                               paste(setdiff(names(p),names(rutas)),collapse=", "))
  if (any(!is.finite(p)) || any(p<=0) || sum(p)<=0) stop("Pesos no positivos o inválidos")
  p/sum(p)
}

# [Anotación · líneas 99–126] leer_modelo(): comprueba que el CSV exista y tenga las columnas configuradas,
#   lee numero_de_cliente como texto y la probabilidad, exige la cantidad de filas esperada, IDs sin NA ni
#   duplicados y probabilidades entre 0 y 1. Si no hay columna de rank calcula la posición como
#   frank(-probabilidad) con empates promedio.
leer_modelo <- function(modelo, archivo, esperado=n_clientes) {
  if (length(archivo)!=1L || is.na(archivo) || !nzchar(archivo) || !file.exists(archivo))
    stop("Falta el CSV de ",modelo,". Completar rutas en el BLOQUE 1: ",archivo)
  pcol <- unname(columnas_prob[modelo]); rcol <- unname(columnas_rank[modelo])
  if (is.na(pcol) || !nzchar(pcol)) stop("Falta columna de probabilidad configurada para ",modelo)
  columnas <- c("numero_de_cliente",pcol,if (!is.na(rcol)) rcol)
  cabecera <- names(fread(archivo,nrows=0L,showProgress=FALSE))
  faltantes <- setdiff(columnas,cabecera)
  if (length(faltantes)) stop("En ",modelo," faltan columnas: ",paste(faltantes,collapse=", "),
                             "; existen: ",paste(cabecera,collapse=", "))
  d <- fread(archivo,select=columnas,
             colClasses=c(numero_de_cliente="character"),showProgress=FALSE)
  if (nrow(d)!=esperado) stop(modelo,": ",nrow(d)," filas; esperadas ",esperado)
  ids <- d[["numero_de_cliente"]]
  if (anyNA(ids) || any(!nzchar(ids)) || anyDuplicated(ids))
    stop(modelo,": IDs NA, vacíos o duplicados")
  p <- d[[pcol]]
  if (!is.numeric(p) || anyNA(p) || any(!is.finite(p)) || any(p<0 | p>1))
    stop(modelo,": probabilidades no numéricas, NA o fuera de [0,1]")
  if (!is.na(rcol)) {
    r <- d[[rcol]]
    if (!is.numeric(r) || anyNA(r) || any(!is.finite(r)) || any(r<1 | r>esperado))
      stop(modelo,": rank_medio no numérico o fuera de [1,N]")
  } else {
    r <- frank(-p,ties.method="average")
  }
  data.table(numero_de_cliente=ids,probabilidad=as.numeric(p),ranking=as.numeric(r))
}

# [Anotación · líneas 128–142] alinear_modelos(): toma los IDs del primer modelo como base, exige que cada
#   modelo tenga exactamente el mismo conjunto de clientes y reordena cada tabla por coincidencia de ID.
alinear_modelos <- function(entradas,modelos) {
  base <- entradas[[modelos[1L]]]$numero_de_cliente
  for (m in modelos) {
    d <- entradas[[m]]
    if (length(d$numero_de_cliente)!=length(base) ||
        !setequal(base,d$numero_de_cliente))
      stop("Los clientes de ",m," no coinciden exactamente con el universo")
    ix <- match(base,d$numero_de_cliente)
    if (anyNA(ix)) stop("Fallo de alineación de ",m)
    entradas[[m]] <- d[ix]
    if (!identical(entradas[[m]]$numero_de_cliente,base))
      stop("Fallo de alineación de ",m)
  }
  entradas[modelos]
}

# [Anotación · líneas 144–163] combinar(): suma, para cada cliente, peso × posición (RANK) o peso ×
#   probabilidad (PROB) de cada modelo en score_meta. Ordena por score_meta ascendente en RANK o descendente en
#   PROB, con numero_de_cliente como desempate, y numera la posición final; conserva las columnas prob_ y rank_
#   de cada modelo.
combinar <- function(entradas,pesos,criterio) {
  if (!criterio %in% c("RANK","PROB")) stop("Método inválido")
  ms <- names(pesos)
  d <- data.table(numero_de_cliente=entradas[[ms[1L]]]$numero_de_cliente)
  puntuacion <- numeric(nrow(d))
  for (m in ms) {
    e <- entradas[[m]]
    set(d,j=paste0("prob_",m),value=e$probabilidad)
    set(d,j=paste0("rank_",m),value=e$ranking)
    valores <- if (criterio=="RANK") e$ranking else e$probabilidad
    puntuacion <- puntuacion + unname(pesos[m])*valores
  }
  d[, score_meta := puntuacion]
  if (criterio=="RANK") setorderv(d,c("score_meta","numero_de_cliente"),c(1L,1L))
  else setorderv(d,c("score_meta","numero_de_cliente"),c(-1L,1L))
  d[, posicion := seq_len(.N)]
  setcolorder(d,c("numero_de_cliente","posicion","score_meta",
                  setdiff(names(d),c("numero_de_cliente","posicion","score_meta"))))
  d
}

# [Anotación · líneas 165–186] firma_texto() devuelve el MD5 de unas líneas de texto, etiqueta_pesos() arma el
#   texto de pesos del nombre de carpeta (por ejemplo P2_50p00pct) y validar_top() relee un archivo de envío y
#   comprueba que tenga n líneas únicas, sin comas, iguales a los primeros n IDs del orden.
#%% celda 4 [código]
# BLOQUE 3 — EXPORTACIÓN SEGURA: TOP N, FINAL Y RESUMEN #####
firma_texto <- function(lineas) {
  f <- tempfile("firma_meta_")
  on.exit(unlink(f),add=TRUE)
  writeLines(lineas,f,useBytes=TRUE)
  unname(tools::md5sum(f))
}

etiqueta_pesos <- function(p) {
  partes <- paste0(names(p),"_",gsub("\\.","p",sprintf("%05.2f",100*unname(p))),"pct")
  paste(partes,collapse="__")
}

validar_top <- function(archivo,orden,n) {
  lineas <- readLines(archivo,warn=FALSE)
  if (length(lineas)!=n || anyNA(lineas) || any(!nzchar(lineas)) ||
      anyDuplicated(lineas) || any(grepl(",",lineas,fixed=TRUE)) ||
      !identical(lineas,head(orden$numero_de_cliente,n)))
    stop("Submission inválida: ",archivo)
  invisible(TRUE)
}

# [Anotación · líneas 188–215] exportar_meta(), inicio: alinea y combina las entradas, calcula una firma con
#   el nombre, el método, los pesos, el MD5 de cada CSV de entrada, las semillas declaradas y los cortes, y arma
#   la etiqueta de la carpeta con los primeros 12 caracteres. Si la carpeta ya existe la reutiliza sólo cuando
#   su manifiesto y los MD5 de sus archivos coinciden; si no, se detiene sin sobrescribir.
exportar_meta <- function(nombre,pesos,criterio,entradas,archivos,conteos,
                          carpeta_raiz=salida,lista_cortes=cortes,final=corte_final) {
  modelos <- names(pesos)
  entradas <- alinear_modelos(entradas,modelos)
  datos <- combinar(entradas,pesos,criterio)
  md5_entradas <- unname(tools::md5sum(archivos[modelos]))
  if (anyNA(md5_entradas)) stop("No se pudieron firmar los CSV de entrada")
  lineas_firma <- c("META2026_V1",nombre,criterio,
                    paste(modelos,sprintf("%.16g",unname(pesos)),sep="="),
                    paste(modelos,md5_entradas,sep="="),
                    paste(modelos,conteos[modelos],sep="="),
                    paste(lista_cortes,collapse=","),as.character(final))
  firma <- firma_texto(lineas_firma)
  etiqueta <- paste0(nombre,"__",criterio,"__",etiqueta_pesos(pesos),
                    "__",substr(firma,1L,12L))
  destino <- file.path(carpeta_raiz,etiqueta)
  if (dir.exists(destino)) {
    meta_path <- file.path(destino,"manifiesto.rds")
    if (!file.exists(meta_path)) stop("Salida preexistente incompleta: ",destino)
    meta <- readRDS(meta_path)
    archivos_salida <- file.path(destino,meta$archivos)
    if (!identical(meta$firma,firma) || !all(file.exists(archivos_salida)) ||
        !identical(unname(tools::md5sum(archivos_salida)),unname(meta$md5)))
      stop("Salida existente modificada/incompleta: ",destino,
           ". No se sobrescribe automáticamente.")
    message("Resultado existente, verificado y reutilizado: ",destino)
    return(meta$resumen)
  }
# [Anotación · líneas 216–235] Crea una carpeta temporal y escribe
#   PREDICCIONES_RANKING_COMPLETO__<etiqueta>.csv con todos los clientes, un archivo
#   SUBMISSION__<etiqueta>__TOPn.csv por cada corte (una columna de IDs sin encabezado) y
#   SUBMISSION_FINAL__<etiqueta>__TOP12500.csv con los primeros corte_final clientes; valida cada archivo al
#   escribirlo.
  dir.create(carpeta_raiz,recursive=TRUE,showWarnings=FALSE)
  temporal <- tempfile(pattern=paste0(etiqueta,"_TMP_"),tmpdir=carpeta_raiz)
  if (!dir.create(temporal)) stop("No se pudo crear directorio temporal")
  on.exit(if (dir.exists(temporal)) unlink(temporal,recursive=TRUE),add=TRUE)

  completo <- paste0("PREDICCIONES_RANKING_COMPLETO__",etiqueta,".csv")
  fwrite(datos,file.path(temporal,completo))
  submissions <- character()
  for (n in lista_cortes) {
    nm <- paste0("SUBMISSION__",etiqueta,"__TOP",n,".csv")
    fwrite(datos[seq_len(n),.(numero_de_cliente)],file.path(temporal,nm),
           col.names=FALSE,quote=FALSE)
    validar_top(file.path(temporal,nm),datos,n)
    submissions <- c(submissions,nm)
  }

  final_nombre <- paste0("SUBMISSION_FINAL__",etiqueta,"__TOP",final,".csv")
  fwrite(datos[seq_len(final),.(numero_de_cliente)],file.path(temporal,final_nombre),
         col.names=FALSE,quote=FALSE)
  validar_top(file.path(temporal,final_nombre),datos,final)

# [Anotación · líneas 237–259] Arma la tabla resumen (combinación, método, modelo, peso, semillas declaradas,
#   archivo de origen y su MD5, corte final, rutas) y la guarda como RESUMEN__<etiqueta>.csv; escribe
#   manifiesto.rds con los MD5 de las salidas y renombra la carpeta temporal a su nombre definitivo.
  resumen <- data.table(combinacion=nombre,metodo=criterio,
                        modelo=modelos,peso=unname(pesos),
                        semillas=as.integer(conteos[modelos]),
                        origen=unname(archivos[modelos]),
                        md5_origen=md5_entradas,corte_final=final,
                        carpeta=destino,
                        predicciones_completas=file.path(destino,completo),
                        submission_final=file.path(destino,final_nombre),
                        cortes_generados=paste(lista_cortes,collapse=","),
                        firma=firma)
  resumen_nombre <- paste0("RESUMEN__",etiqueta,".csv")
  fwrite(resumen,file.path(temporal,resumen_nombre))

  lista_archivos <- c(completo,submissions,final_nombre,resumen_nombre)
  meta <- list(firma=firma,archivos=lista_archivos,
               md5=unname(tools::md5sum(file.path(temporal,lista_archivos))),
               resumen=resumen)
  saveRDS(meta,file.path(temporal,"manifiesto.rds"))
  if (!file.rename(temporal,destino)) stop("No se pudo confirmar la carpeta final")
  message("CANDIDATO: ",nombre," | ",criterio," | ",paste(modelos,collapse="+"))
  message("SUBMISSION FINAL: ",file.path(destino,final_nombre))
  resumen
}

# [Anotación · líneas 261–296] Pruebas en una carpeta temporal con seis clientes ficticios: lectura de dos
#   CSV, alineación por ID con el segundo en orden inverso, combinación por PROB y por RANK, rechazo de un ID
#   cambiado y exportación con cortes 2 y 4 y final 3.
#%% celda 5 [código]
# BLOQUE 4 — PRUEBAS R PEQUEÑAS (no utilizan datos reales) #####
local({
  tmp <- tempfile("meta_test_"); dir.create(tmp)
  on.exit(unlink(tmp,recursive=TRUE),add=TRUE)
  ids <- c("102","103","104","105","106","107")
  f1 <- file.path(tmp,"e012.csv"); f2 <- file.path(tmp,"e015.csv")
  fwrite(data.table(numero_de_cliente=ids,
                    prediction_media=c(.90,.80,.70,.60,.20,.10),
                    rank_medio=c(1,2,3,4,5,6)),f1)
  fwrite(data.table(numero_de_cliente=rev(ids),
                    prediction=c(.10,.20,.60,.70,.80,.90)),f2)
  a <- leer_modelo("E012",f1,6L)
  b <- leer_modelo("E015",f2,6L)
  ent <- alinear_modelos(list(E012=a,E015=b),c("E012","E015"))
  stopifnot(identical(ent$E012$numero_de_cliente,ent$E015$numero_de_cliente),
            identical(ent$E015$probabilidad, c(.90,.80,.70,.60,.20,.10)))
  pesos_test <- c(E012=0.5,E015=0.5)
  p <- combinar(ent,pesos_test,"PROB")
  r <- combinar(ent,pesos_test,"RANK")
  stopifnot(nrow(p)==6L,nrow(r)==6L,p$numero_de_cliente[1L]=="102",
            r$numero_de_cliente[1L]=="102",p$posicion[6L]==6L)
  # Error deliberado: un ID cambiado no debe superar el control.
  malo <- copy(b); malo$numero_de_cliente[1L] <- "999"
  stopifnot(inherits(try(alinear_modelos(list(E012=a,E015=malo),
                                        c("E012","E015")),silent=TRUE),"try-error"))
  res <- exportar_meta("PRUEBA",pesos_test,"RANK",ent,
                       c(E012=f1,E015=f2),c(E012=12L,E015=5L),
                       carpeta_raiz=file.path(tmp,"exportados"),
                       lista_cortes=c(2L,4L),final=3L)
  stopifnot(file.exists(res$submission_final[1L]),
            length(readLines(res$submission_final[1L]))==3L,
            file.exists(res$predicciones_completas[1L]))
  message("PRUEBAS PEQUEÑAS OK: lectura, columnas, alineación por ID, RANK, PROB, ",
          "IDs inconsistentes, cortes sin cabecera y archivo FINAL.")
})

# [Anotación · líneas 298–317] Valida la configuración, normaliza los pesos de cada combinación, comprueba que
#   cada modelo usado tenga semillas declaradas y ruta existente, y lee y valida las entradas contra el universo
#   de 164.647 clientes.
#%% celda 6 [código]
# BLOQUE 5 — GENERAR METAENSEMBLES Y SUBMISSIONS REALES #####
validar_config()

pesos_por_combo <- lapply(combinaciones,normalizar_pesos)
modelos_usados <- unique(unlist(lapply(pesos_por_combo,names),use.names=FALSE))
if (!length(modelos_usados)) stop("No hay modelos elegidos")
for (m in modelos_usados) {
  if (is.na(semillas[m]) || semillas[m]<1L)
    stop("Declarar cantidad de semillas de ",m," en el BLOQUE 1")
  if (is.na(rutas[m]) || !file.exists(rutas[m]))
    stop("Completar ruta del CSV de ",m," en el BLOQUE 1: ",rutas[m])
}

entradas <- setNames(vector("list",length(modelos_usados)),modelos_usados)
for (m in modelos_usados) {
  entradas[[m]] <- leer_modelo(m,rutas[m],n_clientes)
  message("ENTRADA OK ",m,": ",nrow(entradas[[m]]),
          " clientes; ",semillas[m]," semillas declaradas")
}

# [Anotación · líneas 319–331] Exporta cada combinación con exportar_meta(), imprime el resumen y la ruta de
#   los archivos SUBMISSION_FINAL y avisa que no se envía nada. La salida guardada de esta celda lista dos
#   combinaciones (E012_E015 y P2_E012) con P2 declarada con 5 semillas y E012 con 12, y la carpeta P2_E012
#   lleva la firma dc97cf4f7614 que nombra el README.
resultados <- list()
for (nombre in names(pesos_por_combo)) {
  pp <- pesos_por_combo[[nombre]]
  resultados[[nombre]] <- exportar_meta(nombre,pp,metodo,
                                        entradas[names(pp)],rutas,semillas)
}
resumen_final <- rbindlist(resultados,use.names=TRUE,fill=TRUE)
print(resumen_final[,.(combinacion,metodo,modelo,peso,semillas,corte_final)])
message("SUBMISSIONS FINALES PARA DESCARGAR DESDE JUPYTER:")

for (f in unique(resumen_final$submission_final)) message("  ",f)
message("El archivo final se llama SUBMISSION_FINAL")
message("No se envió ningún archivo a la competencia.")
```

### 2-C01_E012_RAW_T4_BO_PRODUCCION_FINAL.ipynb

Notebook de R que produce el modelo E012: variables crudas con lags y deltas de 1 a 4 meses (1.348), BO en junio 80/20, entrenamiento en junio completo por semilla y ensembles por probabilidad media y por rank medio; deja el archivo que lee el notebook 3. Después corre una OOF de junio y dos celdas de consulta.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–10] Celda de texto. Presenta el modelo E012: entrena sólo con 202106 completo y
#   predice 202108, con variables crudas e historia de hasta cuatro meses sin imputación; la BO parte junio en
#   80/20 estratificado por las tres clases y elige por AUC. Enumera las diferencias que declara respecto de
#   versiones previas (se conservan Master_fultimo_cierre y Visa_fultimo_cierre, se excluyen los dos préstamos
#   personales, numero_de_cliente y foto_mes quedan como predictores, ccajas_depositos pasa a NA en mayo) y
#   señala que la OOF de junio posterior a la BO no es independiente de la elección de hiperparámetros.
#%% celda 1 [texto]
# DMEyF 2026 — E012 RAW T4 · BO junio 80/20 · producción agosto

**Notebook único para Google Cloud, IRkernel / R.** Fuente oficial de Pasquini; cinco meses de historia posible, ninguna imputación. E012 utiliza únicamente junio 202106 FULL como entrenamiento y agosto 202108 como producción. La BO estratifica junio por sus tres clases y selecciona por AUC en un 20% fijo. Primero produce cinco semillas y los dos ensembles; luego completa hasta diez (o 20/50); OOF al final, opcional. No ejecuta nada en Drive ni sube submissions a Kaggle.

**Diferencias obligatorias frente a referencias:** se retienen `Master_fultimo_cierre` y `Visa_fultimo_cierre` en current/lag/delta; sólo se excluyen los dos préstamos personales en todas sus versiones. Se retienen `numero_de_cliente` y `foto_mes` como predictores *current* para respetar E012 original; es una decisión metodológica deliberada (la evaluación junio 80/20 comparte mes), no una recomendación universal. `Master_status` y `Visa_status` tienen lag, no delta. `ccajas_depositos` se convierte en NA exclusivamente en mayo ANTES de temporalizar.

**Advertencia de validación:** la OOF de junio posterior a BO no es independiente de la selección de HP: todas las etiquetas de junio pudieron influir en la elección. Ganancias de junio completo y GainBand 11.500–13.500 son indicadores de decisión; el Public de agosto es posterior y no está disponible desde este notebook. No se fabrica ganancia real de agosto.

**Operación:** revisar BLOQUE 1 y ejecutar todas las celdas R en orden. En la VM debe existir `gcloud` con acceso al bucket. Cambiar sólo `n_semillas`, `n_semillas_OOF`, `bo_horas`, `ejecutar_OOF`, `solo_ensembles` o `limite_ART` para reanudar la misma versión. El backup E012 usa exclusivamente su propio prefijo; SAFE, E010 y demás experimentos no se tocan. **No ejecutar dos instancias de E012 en paralelo en el mismo prefijo.** Los entrenamientos no se han ejecutado durante la creación de este notebook.

# [Anotación · líneas 12–36] Configuración: carpeta raíz (variable E012_ROOT; por defecto /home/ds/Expe si
#   existe), experimento C01_E012_RAW_T4_BO_FINAL_V1, URL del crudo, n_semillas=10, n_semillas_OOF=5,
#   ejecutar_OOF=TRUE, solo_ensembles=FALSE, bo_horas=8, respaldo_GCS=FALSE, guardar_modelos=FALSE, sin límite
#   horario y margen de 30 minutos. Comprueba que n_semillas sea 5, 10, 20 o 50.
#%% celda 2 [código]
# BLOQUE 1 — Configuración, dependencias y presupuesto #####
options(repos=c(CRAN="https://cloud.r-project.org"),warn=1,timeout=1800)
ROOT <- Sys.getenv("E012_ROOT", unset=if (dir.exists("/home/ds")) "/home/ds/Expe" else file.path(path.expand("~"),"Expe"))
EXPERIMENTO <- "C01_E012_RAW_T4_BO_FINAL_V1"
OUT <- file.path(ROOT,"experimentos",EXPERIMENTO)
url_oficial <- "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
crudo_oficial <- file.path(OUT,"fuentes","competencia_01_crudo.csv")

n_semillas <- 10L                     # 5, 10, 20 o 50; 5 primeras antes de las adicionales
n_semillas_OOF <- 5L                 # 1..5; la primera siempre se ejecuta primero
ejecutar_OOF <- TRUE                 # ocurre DESPUÉS de la producción
solo_ensembles <- FALSE             # no entrena ni BO ni OOF; reconstruye ensembles disponibles
bo_horas <- 8                       # horas efectivamente invertidas (acumuladas) en BO
respaldo_GCS <- FALSE                # requisito para producción en las VM del proyecto
guardar_modelos <- FALSE            # modelos LightGBM opcionales; probabilidades obligatorias
GCS <- Sys.getenv("E012_FINAL_GCS",unset=paste0(
  "gs://pabloparisidat_buckito2026/Expe/experimentos/",EXPERIMENTO))
limite_ART <- NA_character_  # cambiar a NA_character_ para correr luego del deadline
margen_minutos <- 30                # no inicia entrenamientos nuevos en el margen final
limite <- if (is.na(limite_ART)) as.POSIXct(NA) else
  as.POSIXct(limite_ART,tz="America/Argentina/Buenos_Aires")-margen_minutos*60
hay_tiempo <- function() is.na(limite) || Sys.time()<limite
stopifnot(n_semillas %in% c(5L,10L,20L,50L),n_semillas_OOF %in% 1:5,
          is.numeric(bo_horas),length(bo_horas)==1L,bo_horas>=0,margen_minutos>=0)
# [Anotación · líneas 37–56] Crea las carpetas y la biblioteca local, instala los paquetes que falten de la
#   misma lista de 11 y los carga. Define las 10 semillas base y la extensión a 50 con set.seed(727777) y
#   sample.int, igual que en el notebook 1.
dir.create(OUT,recursive=TRUE,showWarnings=FALSE)
dir.create(file.path(ROOT,"R_libs"),recursive=TRUE,showWarnings=FALSE)
.libPaths(c(file.path(ROOT,"R_libs"),.libPaths()))
paquetes <- c("data.table","lightgbm","DiceKriging","mlr3","mlr3mbo",
              "mlr3learners","paradox","bbotk","lhs","jsonlite","rgenoud")
faltan <- paquetes[!vapply(paquetes,requireNamespace,logical(1),quietly=TRUE)]
if (length(faltan)) install.packages(faltan,lib=.libPaths()[1],Ncpus=2L)
faltan <- paquetes[!vapply(paquetes,requireNamespace,logical(1),quietly=TRUE)]
if (length(faltan)) stop("Faltan paquetes: ",paste(faltan,collapse=", "))
suppressPackageStartupMessages({
  library(data.table); library(lightgbm); library(DiceKriging)
  library(mlr3); library(mlr3mbo); library(mlr3learners)
  library(paradox); library(bbotk)
})
semillas_originales <- c(727777L,773777L,775777L,777737L,787777L,
                        777727L,777773L,777775L,777787L,797777L)
set.seed(727777L,kind="L'Ecuyer-CMRG",normal.kind="Inversion",sample.kind="Rejection")
semillas_50 <- c(semillas_originales,
  head(setdiff(sample.int(1000000000L,100L),semillas_originales),40L))
stopifnot(length(semillas_50)==50L,!anyDuplicated(semillas_50))
# [Anotación · líneas 57–79] PARAM: entrena en 202106 y predice 202108; semilla de BO 727777; 10 puntos LHS +
#   10 de EI, 20 evaluaciones; 5 folds; excluye cprestamos_personales y mprestamos_personales; nombra las dos
#   variables de cierre; cortes de 9.000 a 15.000 de a 500 (13); GainBand de 11.500 a 13.500; ganancia 1.072.500
#   y costo 27.500. Parámetros fijos de LightGBM: learning_rate=0,005, feature_fraction=0,50,
#   min_data_in_leaf=0, max_bin=31, métrica auc, sin feature_fraction_bynode.
PARAM <- list(
  version="E012_RAW_T4_BO80_20_V1_20261011",train=202106L,score=202108L,
  seed_BO=727777L,n_LHS=10L,n_EI=10L,n_total=20L,n_folds=5L,
  excluidas=c("cprestamos_personales","mprestamos_personales"),
  cierres=c("Master_fultimo_cierre","Visa_fultimo_cierre"),
  cortes=seq(9000L,15000L,by=500L),gainband=seq(11500L,13500L,by=500L),#ACA!!!
  ganancia_baja2=1072500,costo_estimulo=27500,
  semillas=semillas_50,
  space=list(num_iterations=c(64L,4096L),num_leaves=c(16L,2048L),
             min_sum_hessian_in_leaf=c(1e-6,0.1))
)
# Parámetros E012 originales; ÚNICO cambio de métrica: average_precision -> auc.
# feature_fraction_bynode no figura: no se importa 0.20 desde SAFE.
PARAM$lgbm_fijos <- list(
  boosting="gbdt",objective="binary",metric="auc",feature_pre_filter=FALSE,
  first_metric_only=FALSE,boost_from_average=TRUE,force_row_wise=TRUE,
  deterministic=TRUE,verbosity=-100,use_missing=TRUE,zero_as_missing=FALSE,
  max_depth=-1L,min_gain_to_split=0,lambda_l1=0,lambda_l2=0,
  bagging_fraction=1.0,pos_bagging_fraction=1.0,neg_bagging_fraction=1.0,
  is_unbalance=FALSE,scale_pos_weight=1.0,drop_rate=0.1,max_drop=50,
  skip_drop=0.5,extra_trees=FALSE,early_stopping=0,
  learning_rate=0.005,feature_fraction=0.50,min_data_in_leaf=0L,max_bin=31L
)
# [Anotación · líneas 80–88] Registra versiones de R, paquetes y dependencias e imprime la configuración.
versiones <- c(R=as.character(getRversion()),vapply(paquetes,
  function(p) as.character(packageVersion(p)),character(1)))
dependencias <- sort(unique(c(paquetes,unlist(tools::package_dependencies(
  paquetes,db=installed.packages(),which=c("Depends","Imports","LinkingTo"),recursive=TRUE)))))
dependencias <- setdiff(dependencias,"R")
versiones_dependencias <- vapply(dependencias,
  function(p) as.character(packageVersion(p)),character(1))
message("E012 salida: ",OUT," | GCS: ",GCS," | seeds: ",n_semillas,
        " | OOF: ",ejecutar_OOF," | BO horas: ",bo_horas)

# [Anotación · líneas 90–128] Mismas funciones de escritura que el notebook 1: md5, firma(), rds_atomico()
#   (aquí con opción de no comprimir) y csv_atomico() con relectura de control. Calcula CONFIG_ID y comprueba
#   gcloud si el respaldo está activo.
#%% celda 3 [código]
# BLOQUE 2 — Escritura atómica, GCS y recuperación #####
md5 <- function(f) unname(tools::md5sum(f))
firma <- function(x) {
  f <- tempfile(); on.exit(unlink(f), add=TRUE)
  saveRDS(x, f, compress=FALSE, version=3)
  md5(f)
}
rds_atomico <- function(x, f, comprimir=TRUE) {
  dir.create(dirname(f), recursive=TRUE, showWarnings=FALSE)
  t <- paste0(f,".tmp_",Sys.getpid()); on.exit(unlink(t), add=TRUE)
  saveRDS(x, t, compress=if(comprimir) "gzip" else FALSE, version=3)
  invisible(readRDS(t))
  if (!file.rename(t,f)) stop("No se pudo promover: ", f)
  invisible(f)
}
csv_atomico <- function(x, f, encabezado=TRUE) {
  dir.create(dirname(f), recursive=TRUE, showWarnings=FALSE)
  t <- paste0(f,".tmp_",Sys.getpid()); on.exit(unlink(t), add=TRUE)
  fwrite(x, t, col.names=encabezado, na="NA")
  z <- fread(t, header=encabezado, na.strings=c("","NA"), showProgress=FALSE)
  if (!identical(dim(z),dim(x))) stop("CSV cambió dimensiones: ", f)
  if (encabezado && !identical(names(z),names(x))) stop("CSV cambió columnas: ",f)
  for (j in seq_along(x)) {
    if (!identical(is.na(z[[j]]),is.na(x[[j]]))) stop("CSV cambió NA: ",f)
    ok <- if (is.numeric(x[[j]])) isTRUE(all.equal(as.numeric(z[[j]]),
      as.numeric(x[[j]]), tolerance=1e-12, check.attributes=FALSE)) else
      identical(as.character(z[[j]]),as.character(x[[j]]))
    if (!ok) stop("CSV cambió valores: ",f)
  }
  if (!file.rename(t,f)) stop("No se pudo promover CSV: ",f)
  invisible(f)
}
CONFIG_ID <- firma(list(PARAM=PARAM, versiones=versiones,
                       versiones_dependencias=versiones_dependencias))
GCS <- sub("/+$", "", GCS)
gcloud <- unname(Sys.which("gcloud"))
if (respaldo_GCS && (!nzchar(gcloud) || !grepl("^gs://[^/]+/.+",GCS)))
  stop("Configurar gcloud y GCS con un prefijo propio, o desactivar GCS fuera de esta VM.")

# [Anotación · líneas 130–177] Funciones de Google Cloud Storage iguales a las del notebook 1: ejecutar gcloud
#   distinguiendo un objeto ausente de otros errores, metadatos, comparación de MD5 y tamaño, subida sólo si el
#   objeto no existe y descarga verificada.
gcs_comando <- function(args, permitir_ausente=FALSE) {
  err <- tempfile(); on.exit(unlink(err), add=TRUE)
  out <- suppressWarnings(system2(gcloud, vapply(c(args,"--quiet"),shQuote,character(1)),
                                  stdout=TRUE, stderr=err))
  status <- attr(out,"status")
  if (!is.null(status) && status!=0L) {
    detalle <- paste(readLines(err,warn=FALSE),collapse="\n")
    # Sólo una ausencia inequívoca es un experimento/objeto nuevo. 403/red NO lo son.
    if (permitir_ausente && grepl("(?i)(404|not found|no such object|matched no objects|no urls matched|does not exist)",
                                 detalle,perl=TRUE) &&
        !grepl("(?i)(403|permission|forbidden|access denied)",detalle,perl=TRUE)) return(NULL)
    stop("GCS falló; no se inicia el siguiente trabajo. ", detalle)
  }
  out
}
gcs_info <- function(uri) {
  z <- gcs_comando(c("storage","objects","describe",uri,"--raw","--format=json"),TRUE)
  if (is.null(z)) return(NULL)
  jsonlite::fromJSON(paste(z,collapse="\n"))
}
md5_base64 <- function(h) jsonlite::base64_enc(as.raw(strtoi(
  substring(h,seq(1,31,2),seq(2,32,2)),16L)))
verificar_remoto <- function(info, f) {
  !is.null(info) && identical(info$md5Hash,md5_base64(md5(f))) &&
    isTRUE(as.numeric(info$size)==file.info(f)$size)
}
subir_inmutable <- function(f, uri) {
  info <- gcs_info(uri)
  if (is.null(info)) {
    gcs_comando(c("storage","cp",f,uri,"--if-generation-match=0",
                  paste0("--content-md5=",md5_base64(md5(f)))))
    info <- gcs_info(uri)
  }
  if (!verificar_remoto(info,f)) stop("Objeto remoto diferente o sin MD5 verificable: ",uri)
  invisible(TRUE)
}
descargar_verificado <- function(uri, f, hash=NULL) {
  info <- gcs_info(uri)
  if (is.null(info)) stop("Falta un objeto de un checkpoint confirmado: ",uri)
  dir.create(dirname(f),recursive=TRUE,showWarnings=FALSE)
  t <- paste0(f,".download_",Sys.getpid()); on.exit(unlink(t),add=TRUE)
  gcs_comando(c("storage","cp",uri,t))
  if (!verificar_remoto(info,t) || (!is.null(hash) && md5(t)!=hash))
    stop("Descarga no verificable: ",uri)
  if (file.exists(f) && md5(f)!=md5(t)) stop("Conflicto local, no se sobrescribe: ",f)
  if (!file.exists(f) && !file.rename(t,f)) stop("No se pudo recuperar: ",f)
  invisible(f)
}
# [Anotación · líneas 178–204] Rutas local y remota de los checkpoints, validación del COMMIT y respaldar(),
#   que no hace nada con respaldo_GCS=FALSE.
ck_dir <- function(key) file.path(OUT,"checkpoints",key)
ck_uri <- function(key) paste0(GCS,"/checkpoints/",key,".rds")
confirmados_sesion <- new.env(parent=emptyenv())
clave_confirmacion <- function(key) paste(GCS,CONFIG_ID,key,sep="|")

validar_commit <- function(z,key,sig=NULL) {
  if (!is.list(z) || !identical(z$key,key) || !identical(z$config_id,CONFIG_ID) ||
      (!is.null(sig) && !identical(z$firma,sig)))
    stop("Checkpoint de otro experimento/configuración: ",key)
  a <- z$archivos
  if (!nrow(a) || anyDuplicated(a$archivo) || anyNA(a) ||
      any(basename(a$archivo)!=a$archivo) || any(!grepl("^[a-f0-9]{32}$",a$md5)))
    stop("Manifiesto de archivos inválido: ",key)
  invisible(TRUE)
}
respaldar <- function(key,z) {
  if (!respaldo_GCS) return(invisible(TRUE))
  for (i in seq_len(nrow(z$archivos))) {
    a <- z$archivos[i,]
    subir_inmutable(file.path(ck_dir(key),a$archivo),paste0(GCS,"/objetos/",a$md5,"/",a$archivo))
  }
  # El commit remoto se publica ÚLTIMO. Sólo él declara terminado el trabajo.
  subir_inmutable(file.path(ck_dir(key),"COMMIT.rds"),ck_uri(key))
  assign(clave_confirmacion(key),md5(file.path(ck_dir(key),"COMMIT.rds")),
         envir=confirmados_sesion)
  invisible(TRUE)
}
# [Anotación · líneas 205–251] abrir_checkpoint(), iniciar_checkpoint() y cerrar_checkpoint(), con el mismo
#   comportamiento que en el notebook 1: verificación por firma, MD5 y tamaño, carpeta aparte para intentos
#   incompletos y COMMIT.rds escrito al final.
abrir_checkpoint <- function(key,sig=NULL,remoto=TRUE) {
  d <- ck_dir(key); f <- file.path(d,"COMMIT.rds")
  confirmado <- file.exists(f) && exists(clave_confirmacion(key),envir=confirmados_sesion,inherits=FALSE) &&
    identical(get(clave_confirmacion(key),envir=confirmados_sesion),md5(f))
  info <- if (respaldo_GCS && remoto && !confirmado) gcs_info(ck_uri(key)) else NULL
  if (!file.exists(f) && !is.null(info)) {
    descargar_verificado(ck_uri(key),f)
    message("Recuperado desde GCS: ",key)
  }
  if (!file.exists(f)) return(NULL)
  z <- readRDS(f); validar_commit(z,key,sig)
  if (!is.null(info) && !verificar_remoto(info,f)) stop("Conflicto de commits: ",key)
  for (i in seq_len(nrow(z$archivos))) {
    a <- z$archivos[i,]; p <- file.path(d,a$archivo)
    if (!file.exists(p) && respaldo_GCS && remoto)
      descargar_verificado(paste0(GCS,"/objetos/",a$md5,"/",a$archivo),p,a$md5)
    if (!file.exists(p) || md5(p)!=a$md5 || file.info(p)$size!=a$bytes)
      stop("Checkpoint corrupto/incompleto: ",key," / ",a$archivo)
  }
  # Si el backup falló luego del commit local, ahora se completa sin reentrenar.
  if (remoto && !confirmado) respaldar(key,z)
  z
}
iniciar_checkpoint <- function(key) {
  d <- ck_dir(key)
  if (file.exists(file.path(d,"COMMIT.rds"))) stop("No sobrescribir checkpoint: ",key)
  if (dir.exists(d) && length(list.files(d,all.files=TRUE,no..=TRUE))) {
    destino <- paste0(d,"_incompleto_",format(Sys.time(),"%Y%m%d%H%M%OS6"),"_",Sys.getpid())
    if (!file.rename(d,destino)) stop("No se pudo apartar intento incompleto: ",d)
    message("Intento interrumpido conservado: ",destino)
  }
  dir.create(d,recursive=TRUE,showWarnings=FALSE)
  d
}
cerrar_checkpoint <- function(key,sig,remoto=TRUE) {
  d <- ck_dir(key)
  fs <- list.files(d,full.names=TRUE)
  fs <- fs[!grepl("COMMIT\\.rds$|\\.tmp_|\\.download_",fs)]
  stopifnot(length(fs)>0L, !any(file.info(fs)$isdir))
  z <- list(key=key, config_id=CONFIG_ID, firma=sig,
    archivos=data.frame(archivo=basename(fs),md5=unname(tools::md5sum(fs)),
                         bytes=unname(file.info(fs)$size),stringsAsFactors=FALSE))
  validar_commit(z,key,sig)
  rds_atomico(z,file.path(d,"COMMIT.rds"))
  if (remoto) respaldar(key,z)             # ERROR de GCS se propaga; nunca un mero warning
  invisible(z)
}
# [Anotación · líneas 252–264] Consulta el bucket si hay respaldo y crea el checkpoint config/base con
#   config.rds, sessionInfo.txt y semillas.csv si no existe.
if (respaldo_GCS) {
  bucket <- sub("^(gs://[^/]+).*", "\\1",GCS)
  invisible(gcs_comando(c("storage","buckets","describe",bucket,"--format=json")))
}
if (is.null(abrir_checkpoint("config/base",CONFIG_ID))) {
  d <- iniciar_checkpoint("config/base")
  rds_atomico(list(PARAM=PARAM,versiones=versiones,dependencias=versiones_dependencias,
                   config_id=CONFIG_ID),file.path(d,"config.rds"))
  writeLines(capture.output(sessionInfo()),file.path(d,"sessionInfo.txt"))
  csv_atomico(data.table(orden=seq_along(semillas_50),seed=semillas_50,
    origen=c(rep("SAFE_original",10),rep("extension_determinista",40))),file.path(d,"semillas.csv"))
  cerrar_checkpoint("config/base",CONFIG_ID)
}

# [Anotación · líneas 266–290] generar_targets(): misma lógica que en el notebook 1. Con los dos períodos
#   siguientes de cada cliente asigna CONTINUA, BAJA+1 o BAJA+2 y crea binaria2 = 1 para BAJA+1 o BAJA+2.
#%% celda 4 [código]
# BLOQUE 3 — Targets Pasquini, métricas y funciones compartidas #####
generar_targets <- function(dataset) {
  if (anyNA(dataset$numero_de_cliente) || anyNA(dataset$foto_mes) ||
      anyDuplicated(dataset,by=c("numero_de_cliente","foto_mes")))
    stop("IDs/meses faltantes o duplicados cliente-mes en fuente oficial.")
  dsimple <- dataset[,.(pos=.I,numero_de_cliente,
    periodo0=as.integer(foto_mes/100)*12L+foto_mes%%100L)]
  setorder(dsimple,numero_de_cliente,periodo0)
  periodo_ultimo <- max(dsimple$periodo0)
  periodo_anteultimo <- periodo_ultimo-1L
  dsimple[,c("periodo1","periodo2") := shift(periodo0,n=1:2,fill=NA,type="lead"),
          by=numero_de_cliente]
  dsimple[,clase_ternaria := NA_character_]
  dsimple[periodo0<periodo_anteultimo,clase_ternaria := "CONTINUA"]
  dsimple[periodo0<periodo_ultimo & (is.na(periodo1) | periodo0+1L<periodo1),
          clase_ternaria := "BAJA+1"]
  dsimple[periodo0<periodo_anteultimo & periodo0+1L==periodo1 &
          (is.na(periodo2) | periodo0+2L<periodo2),clase_ternaria := "BAJA+2"]
  setorder(dsimple,pos)
  dataset[,clase_ternaria := dsimple$clase_ternaria]
  dataset[,binaria2 := fifelse(is.na(clase_ternaria),NA_integer_,
    as.integer(clase_ternaria %in% c("BAJA+1","BAJA+2")))]
  dataset
}
# [Anotación · líneas 291–333] Funciones auxiliares: mes_anterior(), validación de probabilidades y de IDs,
#   AUC por suma de ranks, curva de ganancia acumulada (+1.072.500 por BAJA+2, −27.500 por el resto, orden por
#   probabilidad descendente) y validación de la clase.
mes_anterior <- function(ym,k) {
  total <- (ym%/%100L)*12L+ym%%100L-1L-as.integer(k)
  as.integer((total%/%12L)*100L+total%%12L+1L)
}
validar_prob <- function(p,n=length(p)) {
  if (length(p)!=n || anyNA(p) || any(!is.finite(p)) || any(p<0 | p>1))
    stop("Predicciones inválidas, incompletas o fuera de [0,1].")
  invisible(TRUE)
}
validar_ids <- function(ids,referencia) {
  if (anyNA(ids) || anyDuplicated(ids) ||
      !identical(as.character(ids),as.character(referencia)))
    stop("IDs duplicados o en distinto orden.")
  invisible(TRUE)
}
auc_binaria <- function(y,p) {
  validar_prob(p,length(y))
  if (anyNA(y) || any(!y %in% 0:1)) stop("Target inválido para AUC.")
  n1 <- sum(y==1L); n0 <- sum(y==0L)
  if (!n1 || !n0) stop("AUC requiere ambas clases.")
  (sum(rank(p,ties.method="average")[y==1L])-n1*(n1+1)/2)/(n1*n0)
}
curva_ganancia <- function(d,p) {
  validar_prob(p,nrow(d))
  x <- d[,.(numero_de_cliente,clase_ternaria)]
  x[,prediction := p]
  setorder(x,-prediction,numero_de_cliente)
  x[,baja2 := as.integer(clase_ternaria=="BAJA+2")]
  x[,.(cutoff=seq_len(.N),numero_de_cliente,prediction,
    bajas2_acumuladas=cumsum(baja2),
    ganancia_acumulada=cumsum(fifelse(baja2==1L,PARAM$ganancia_baja2,-PARAM$costo_estimulo)))]
}
validar_target <- function(d,etiquetado=TRUE) {
  if (!identical(is.na(d$clase_ternaria),is.na(d$binaria2)) ||
      any(!is.na(d$clase_ternaria) & !d$clase_ternaria %in% c("CONTINUA","BAJA+1","BAJA+2")))
    stop("Máscara de target alterada.")
  if (etiquetado && (anyNA(d$binaria2) ||
      any(d$binaria2 != as.integer(d$clase_ternaria %in% c("BAJA+1","BAJA+2")))))
    stop("Target incorrecto.")
  if (!etiquetado && (!all(is.na(d$clase_ternaria)) || !all(is.na(d$binaria2))))
    stop("Agosto debe estar íntegramente sin etiquetas.")
  invisible(TRUE)
}
# [Anotación · líneas 334–351] Nombres de los tres hiperparámetros buscados, armado de la lista de parámetros
#   de un modelo (fijos + los tres + semilla) y matriz_E012(), que pasa FEATURES a matriz numérica comprobando
#   que no cambien NA ni valores.
hp_campos <- c("num_iterations","num_leaves","min_sum_hessian_in_leaf")
hp_lista <- function(hp) list(num_iterations=as.integer(hp$num_iterations),
  num_leaves=as.integer(hp$num_leaves),
  min_sum_hessian_in_leaf=as.numeric(hp$min_sum_hessian_in_leaf))
param_modelo <- function(hp,seed) modifyList(PARAM$lgbm_fijos,
  c(hp_lista(hp),list(seed=as.integer(seed))))
matriz_E012 <- function(d) {
  if (!identical(names(d[,..FEATURES]),FEATURES)) stop("Manifiesto distinto en matriz.")
  x <- data.matrix(d[,..FEATURES])
  if (!identical(colnames(x),FEATURES) || nrow(x)!=nrow(d)) stop("Error de dimensiones.")
  for (j in seq_along(FEATURES)) {
    v <- d[[FEATURES[j]]]
    if (!identical(is.na(x[,j]),is.na(v)) ||
        any(!is.na(x[,j]) & !is.finite(x[,j])))
      stop("data.matrix modificó NA, valor o tipo: ",FEATURES[j])
  }
  x
}
# [Anotación · líneas 352–370] ajustar_E012(): entrena un LightGBM con lgb.train sobre la matriz y la etiqueta
#   recibidas, sin validación ni early stopping, predice sobre la matriz de puntuación y devuelve probabilidades
#   y tiempos; guarda el modelo sólo si se pide.
ajustar_E012 <- function(X,y,Xscore,hp,seed,modelo_archivo=NULL) {
  stopifnot(identical(colnames(X),FEATURES),identical(colnames(Xscore),FEATURES),
            !anyNA(y),all(y %in% 0:1))
  t0 <- proc.time()[["elapsed"]]
  dtrain <- lgb.Dataset(X,label=y,params=list(max_bin=31L,feature_pre_filter=FALSE,
    use_missing=TRUE,zero_as_missing=FALSE))
  modelo <- lgb.train(params=param_modelo(hp,seed),data=dtrain)
  t1 <- proc.time()[["elapsed"]]
  p <- as.numeric(predict(modelo,Xscore))
  validar_prob(p,nrow(Xscore))
  if (!is.null(modelo_archivo)) {
    t <- paste0(modelo_archivo,".tmp_",Sys.getpid())
    on.exit(unlink(t),add=TRUE)
    lgb.save(modelo,t)
    invisible(lgb.load(t))
    if (!file.rename(t,modelo_archivo)) stop("No se pudo guardar modelo.")
  }
  list(p=p,seg_entrenamiento=t1-t0,seg_prediccion=proc.time()[["elapsed"]]-t1)
}

# [Anotación · líneas 372–392] Pruebas con datos de ejemplo: mes_anterior en varios casos, clases de tres
#   clientes ficticios y escritura de un CSV de IDs sin encabezado.
#%% celda 5 [código]
# BLOQUE 3b — Pruebas pequeñas de targets, fechas, NA y submissions #####
local({
  stopifnot(mes_anterior(202106L,1L)==202105L,
            mes_anterior(202106L,4L)==202102L,
            mes_anterior(202108L,3L)==202105L,
            mes_anterior(202108L,4L)==202104L)
  ej <- data.table(numero_de_cliente=c(rep(1L,6),rep(2L,3),rep(3L,4)),
    foto_mes=c(202103L:202108L,202103L:202105L,202103L,202105L,202106L,202108L))
  ej <- generar_targets(ej)
  stopifnot(ej[numero_de_cliente==2L & foto_mes==202104L,clase_ternaria]=="BAJA+2",
            ej[numero_de_cliente==2L & foto_mes==202105L,clase_ternaria]=="BAJA+1",
            ej[numero_de_cliente==3L & foto_mes==202103L,clase_ternaria]=="BAJA+1",
            ej[numero_de_cliente==1L & foto_mes==202106L,binaria2]==0L,
            all(is.na(ej[foto_mes==202108L,binaria2])))
  f <- tempfile(fileext=".csv"); on.exit(unlink(f),add=TRUE)
  csv_atomico(data.table(numero_de_cliente=c(9L,2L,7L)),f,encabezado=FALSE)
  stopifnot(length(readLines(f))==3L,
            identical(as.integer(fread(f,header=FALSE)[[1L]]),c(9L,2L,7L)))
  message("Pruebas pequeñas iniciales OK.")
})

# [Anotación · líneas 394–415] Descarga el crudo si no está, lo lee, comprueba que los meses sean 202103 a
#   202108 sin duplicados cliente-mes y que la cantidad de filas por mes coincida con seis valores escritos en
#   el código (de 162.900 a 164.647). Genera las clases y valida los meses con y sin clase.
#%% celda 6 [código]
# BLOQUE 4 — Descarga cruda y preparación oficial sin alterar fuente #####
dir.create(dirname(crudo_oficial),recursive=TRUE,showWarnings=FALSE)
if (!file.exists(crudo_oficial)) {
  tmp <- paste0(crudo_oficial,".descarga")
  if (file.exists(tmp)) unlink(tmp)
  download.file(url_oficial,tmp,mode="wb",quiet=FALSE)
  if (!file.exists(tmp) || file.info(tmp)$size==0) stop("Descarga oficial vacía.")
  if (!file.rename(tmp,crudo_oficial)) stop("No se pudo promover descarga.")
}
raw_md5 <- md5(crudo_oficial)
dataset <- fread(crudo_oficial,na.strings=c("","NA"),showProgress=TRUE)
stopifnot(identical(sort(unique(dataset$foto_mes)),202103L:202108L),
          !anyDuplicated(dataset,by=c("numero_de_cliente","foto_mes")))
filas_oficiales <- data.table(foto_mes=202103L:202108L,
  N=c(162900L,163284L,163768L,164114L,164348L,164647L))
if (!isTRUE(all.equal(as.data.frame(dataset[,.(N=.N),by=foto_mes]),
                     as.data.frame(filas_oficiales),check.attributes=FALSE)))
  stop("Conteos mensuales oficiales inesperados.")
dataset <- generar_targets(dataset)
validar_target(dataset[foto_mes %in% 202103L:202106L])
validar_target(dataset[foto_mes==202108L],FALSE)
# [Anotación · líneas 416–437] Compara los conteos por mes y clase con la tabla escrita en el código, define
#   UNIVERSO (164.647 clientes de 202108), pasa ccajas_depositos a NA en 202105 antes de armar la historia y
#   calcula DATA_ID.
conteos_pasquini <- data.table(
  foto_mes=c(rep(202103L:202106L,each=3),202107L,202107L,202108L),
  clase_ternaria=c(rep(c("BAJA+1","BAJA+2","CONTINUA"),4),
                   NA_character_,"BAJA+1",NA_character_),
  N=c(1019L,960L,160921L,964L,1139L,161181L,1143L,870L,161755L,
      874L,1098L,162142L,163245L,1103L,164647L))
conteos <- dataset[,.N,by=.(foto_mes,clase_ternaria)]
setorderv(conteos,c("foto_mes","clase_ternaria"),na.last=TRUE)
setorderv(conteos_pasquini,c("foto_mes","clase_ternaria"),na.last=TRUE)
if (!isTRUE(all.equal(as.data.frame(conteos),as.data.frame(conteos_pasquini),check.attributes=FALSE)))
  stop("Targets difieren del inventario oficial de Pasquini/SAFE.")
UNIVERSO <- dataset[foto_mes==202108L,numero_de_cliente]
stopifnot(length(UNIVERSO)==164647L,!anyNA(UNIVERSO),!anyDuplicated(UNIVERSO))
# ÚNICA corrección DQ: exclusivamente en mayo y antes de temporalizar.
stopifnot("ccajas_depositos" %in% names(dataset))
no_mayo <- dataset[foto_mes!=202105L,ccajas_depositos]
dataset[foto_mes==202105L,ccajas_depositos := NA_real_]
stopifnot(all(is.na(dataset[foto_mes==202105L,ccajas_depositos])),
          identical(no_mayo,dataset[foto_mes!=202105L,ccajas_depositos]))
rm(no_mayo)
DATA_ID <- firma(list(version=PARAM$version,raw_md5=raw_md5,
  mes=filas_oficiales))

# [Anotación · líneas 439–492] vars_lag: lista literal de 148 nombres de variables del dataset a las que se
#   les calcula lag.
#%% celda 7 [código]
# BLOQUE 5 — Vectores literales E012 RAW T4 (referencia original) #####
vars_lag <- c(
  "active_quarter", "cliente_vip", "internet",
  "cliente_edad", "cliente_antiguedad", "mrentabilidad",
  "mrentabilidad_annual", "mcomisiones", "mactivos_margen",
  "mpasivos_margen", "cproductos", "tcuentas",
  "ccuenta_corriente", "mcuenta_corriente_adicional", "mcuenta_corriente",
  "ccaja_ahorro", "mcaja_ahorro", "mcaja_ahorro_adicional",
  "mcaja_ahorro_dolares", "cdescubierto_preacordado", "mcuentas_saldo",
  "ctarjeta_debito", "ctarjeta_debito_transacciones", "mautoservicio",
  "ctarjeta_visa", "ctarjeta_visa_transacciones", "mtarjeta_visa_consumo",
  "ctarjeta_master", "ctarjeta_master_transacciones", "mtarjeta_master_consumo",
  "cprestamos_prendarios", "mprestamos_prendarios", "cprestamos_hipotecarios",
  "mprestamos_hipotecarios", "cplazo_fijo", "mplazo_fijo_dolares",
  "mplazo_fijo_pesos", "cinversion1", "minversion1_pesos",
  "minversion1_dolares", "cinversion2", "minversion2",
  "cseguro_vida", "cseguro_auto", "cseguro_vivienda",
  "cseguro_accidentes_personales", "ccaja_seguridad", "cpayroll_trx",
  "mpayroll", "mpayroll2", "cpayroll2_trx",
  "ccuenta_debitos_automaticos", "mcuenta_debitos_automaticos", "ctarjeta_visa_debitos_automaticos",
  "mttarjeta_visa_debitos_automaticos", "ctarjeta_master_debitos_automaticos", "mttarjeta_master_debitos_automaticos",
  "cpagodeservicios", "mpagodeservicios", "cpagomiscuentas",
  "mpagomiscuentas", "ccajeros_propios_descuentos", "mcajeros_propios_descuentos",
  "ctarjeta_visa_descuentos", "mtarjeta_visa_descuentos", "ctarjeta_master_descuentos",
  "mtarjeta_master_descuentos", "ccomisiones_mantenimiento", "mcomisiones_mantenimiento",
  "ccomisiones_otras", "mcomisiones_otras", "cforex",
  "cforex_buy", "mforex_buy", "cforex_sell",
  "mforex_sell", "ctransferencias_recibidas", "mtransferencias_recibidas",
  "ctransferencias_emitidas", "mtransferencias_emitidas", "cextraccion_autoservicio",
  "mextraccion_autoservicio", "ccheques_depositados", "mcheques_depositados",
  "ccheques_emitidos", "mcheques_emitidos", "ccheques_depositados_rechazados",
  "mcheques_depositados_rechazados", "ccheques_emitidos_rechazados", "mcheques_emitidos_rechazados",
  "tcallcenter", "ccallcenter_transacciones", "thomebanking",
  "chomebanking_transacciones", "ccajas_transacciones", "ccajas_consultas",
  "ccajas_depositos", "ccajas_extracciones", "ccajas_otras",
  "catm_trx", "matm", "catm_trx_other",
  "matm_other", "ctrx_quarter", "tmobile_app",
  "cmobile_app_trx", "Master_delinquency", "Master_status",
  "Master_mfinanciacion_limite", "Master_Fvencimiento", "Master_Finiciomora",
  "Master_msaldototal", "Master_msaldopesos", "Master_msaldodolares",
  "Master_mconsumospesos", "Master_mconsumosdolares", "Master_mlimitecompra",
  "Master_madelantopesos", "Master_madelantodolares", "Master_mpagado",
  "Master_mpagospesos", "Master_mpagosdolares", "Master_fechaalta",
  "Master_mconsumototal", "Master_cconsumos", "Master_cadelantosefectivo",
  "Master_mpagominimo", "Visa_delinquency", "Visa_status",
  "Visa_mfinanciacion_limite", "Visa_Fvencimiento", "Visa_Finiciomora",
  "Visa_msaldototal", "Visa_msaldopesos", "Visa_msaldodolares",
  "Visa_mconsumospesos", "Visa_mconsumosdolares", "Visa_mlimitecompra",
  "Visa_madelantopesos", "Visa_madelantodolares", "Visa_mpagado",
  "Visa_mpagospesos", "Visa_mpagosdolares", "Visa_fechaalta",
  "Visa_mconsumototal", "Visa_cconsumos", "Visa_cadelantosefectivo",
  "Visa_mpagominimo"
)

# [Anotación · líneas 494–544] vars_delta: lista literal de 146 nombres a los que se les calcula delta; es la
#   lista anterior sin Master_status ni Visa_status.
vars_delta <- c(
  "active_quarter", "cliente_vip", "internet",
  "cliente_edad", "cliente_antiguedad", "mrentabilidad",
  "mrentabilidad_annual", "mcomisiones", "mactivos_margen",
  "mpasivos_margen", "cproductos", "tcuentas",
  "ccuenta_corriente", "mcuenta_corriente_adicional", "mcuenta_corriente",
  "ccaja_ahorro", "mcaja_ahorro", "mcaja_ahorro_adicional",
  "mcaja_ahorro_dolares", "cdescubierto_preacordado", "mcuentas_saldo",
  "ctarjeta_debito", "ctarjeta_debito_transacciones", "mautoservicio",
  "ctarjeta_visa", "ctarjeta_visa_transacciones", "mtarjeta_visa_consumo",
  "ctarjeta_master", "ctarjeta_master_transacciones", "mtarjeta_master_consumo",
  "cprestamos_prendarios", "mprestamos_prendarios", "cprestamos_hipotecarios",
  "mprestamos_hipotecarios", "cplazo_fijo", "mplazo_fijo_dolares",
  "mplazo_fijo_pesos", "cinversion1", "minversion1_pesos",
  "minversion1_dolares", "cinversion2", "minversion2",
  "cseguro_vida", "cseguro_auto", "cseguro_vivienda",
  "cseguro_accidentes_personales", "ccaja_seguridad", "cpayroll_trx",
  "mpayroll", "mpayroll2", "cpayroll2_trx",
  "ccuenta_debitos_automaticos", "mcuenta_debitos_automaticos", "ctarjeta_visa_debitos_automaticos",
  "mttarjeta_visa_debitos_automaticos", "ctarjeta_master_debitos_automaticos", "mttarjeta_master_debitos_automaticos",
  "cpagodeservicios", "mpagodeservicios", "cpagomiscuentas",
  "mpagomiscuentas", "ccajeros_propios_descuentos", "mcajeros_propios_descuentos",
  "ctarjeta_visa_descuentos", "mtarjeta_visa_descuentos", "ctarjeta_master_descuentos",
  "mtarjeta_master_descuentos", "ccomisiones_mantenimiento", "mcomisiones_mantenimiento",
  "ccomisiones_otras", "mcomisiones_otras", "cforex",
  "cforex_buy", "mforex_buy", "cforex_sell",
  "mforex_sell", "ctransferencias_recibidas", "mtransferencias_recibidas",
  "ctransferencias_emitidas", "mtransferencias_emitidas", "cextraccion_autoservicio",
  "mextraccion_autoservicio", "ccheques_depositados", "mcheques_depositados",
  "ccheques_emitidos", "mcheques_emitidos", "ccheques_depositados_rechazados",
  "mcheques_depositados_rechazados", "ccheques_emitidos_rechazados", "mcheques_emitidos_rechazados",
  "tcallcenter", "ccallcenter_transacciones", "thomebanking",
  "chomebanking_transacciones", "ccajas_transacciones", "ccajas_consultas",
  "ccajas_depositos", "ccajas_extracciones", "ccajas_otras",
  "catm_trx", "matm", "catm_trx_other",
  "matm_other", "ctrx_quarter", "tmobile_app",
  "cmobile_app_trx", "Master_delinquency", "Master_mfinanciacion_limite",
  "Master_Fvencimiento", "Master_Finiciomora", "Master_msaldototal",
  "Master_msaldopesos", "Master_msaldodolares", "Master_mconsumospesos",
  "Master_mconsumosdolares", "Master_mlimitecompra", "Master_madelantopesos",
  "Master_madelantodolares", "Master_mpagado", "Master_mpagospesos",
  "Master_mpagosdolares", "Master_fechaalta", "Master_mconsumototal",
  "Master_cconsumos", "Master_cadelantosefectivo", "Master_mpagominimo",
  "Visa_delinquency", "Visa_mfinanciacion_limite", "Visa_Fvencimiento",
  "Visa_Finiciomora", "Visa_msaldototal", "Visa_msaldopesos",
  "Visa_msaldodolares", "Visa_mconsumospesos", "Visa_mconsumosdolares",
  "Visa_mlimitecompra", "Visa_madelantopesos", "Visa_madelantodolares",
  "Visa_mpagado", "Visa_mpagospesos", "Visa_mpagosdolares",
  "Visa_fechaalta", "Visa_mconsumototal", "Visa_cconsumos",
  "Visa_cadelantosefectivo", "Visa_mpagominimo"
)
# [Anotación · líneas 545–558] Agrega Master_fultimo_cierre y Visa_fultimo_cierre a ambas listas y comprueba
#   los tamaños (150 con lag, 148 con delta), que sólo los dos status tengan lag sin delta, que no estén los
#   préstamos personales y que las variables de cierre existan y sean numéricas.
# Cambio explícito respecto del E012 previo: se RESTITUYEN ambas variables de cierre.
vars_lag <- c(vars_lag,PARAM$cierres)
vars_delta <- c(vars_delta,PARAM$cierres)
if (length(vars_lag)!=150L || uniqueN(vars_lag)!=150L ||
    length(vars_delta)!=148L || uniqueN(vars_delta)!=148L)
  stop("Conteo literal inesperado para RAW T4 corregido.")
if (!setequal(vars_delta,setdiff(vars_lag,c("Master_status","Visa_status"))))
  stop("Sólo los status tienen lag sin delta.")
if (any(PARAM$excluidas %in% c(vars_lag,vars_delta))) stop("Préstamos presentes.")
stopifnot(!any(c("numero_de_cliente","foto_mes","clase_ternaria","binaria2") %in% vars_lag))
for (v in PARAM$cierres) {
  if (!v %in% names(dataset)) stop("Cierre no presente en crudo: ",v)
  if (!is.numeric(dataset[[v]])) stop("Cierre no es numérico y no puede temporalizarse: ",v)
}
# [Anotación · líneas 559–588] Define CURRENT (numero_de_cliente, foto_mes y las 150 variables) y FEATURES:
#   CURRENT, lag1 a lag4 de las 150, delta1 a delta4 de las 148 y cuatro indicadores lagK_disponible. Comprueba
#   que sean 1.348, que CURRENT coincida con todas las columnas del crudo menos los dos préstamos y que todas
#   sean numéricas. Guarda el inventario por bloque en el checkpoint features/manifiesto.
CURRENT <- c("numero_de_cliente","foto_mes",vars_lag)
FEATURES <- c(CURRENT,
  unlist(lapply(1:4,function(k) paste0("lag",k,"_",vars_lag)),use.names=FALSE),
  unlist(lapply(1:4,function(k) paste0("delta",k,"_",vars_delta)),use.names=FALSE),
  paste0("lag",1:4,"_disponible"))
if (length(FEATURES)!=1348L || anyDuplicated(FEATURES)) stop("Inventario != 1348.")
if (length(setdiff(c(vars_lag,vars_delta),names(dataset)))) stop("Faltan columnas.")
fuentes_reales <- setdiff(names(dataset),c("clase_ternaria","binaria2",PARAM$excluidas))
if (!setequal(fuentes_reales,CURRENT))
  stop("El conjunto CURRENT difiere del esquema E012 original corregido. Revisar fuente.")
no_numericas <- CURRENT[!vapply(dataset[,..CURRENT],is.numeric,logical(1))]
if (length(no_numericas)) stop("Predictores no numéricos: ",paste(no_numericas,collapse=", "))
PIPE_ID <- firma(list(data=DATA_ID,vars_lag=vars_lag,vars_delta=vars_delta,
  features=FEATURES,correccion="ccajas_depositos_202105_NA"))
FEATURE_ID <- firma(FEATURES)
inventario <- rbindlist(list(data.table(bloque="current",feature=CURRENT),
  rbindlist(lapply(1:4,function(k) data.table(bloque=paste0("lag",k),feature=paste0("lag",k,"_",vars_lag)))),
  rbindlist(lapply(1:4,function(k) data.table(bloque=paste0("delta",k),feature=paste0("delta",k,"_",vars_delta)))),
  data.table(bloque="flags",feature=paste0("lag",1:4,"_disponible"))))
stopifnot(identical(inventario$feature,FEATURES))
if (is.null(abrir_checkpoint("features/manifiesto",PIPE_ID))) {
  d <- iniciar_checkpoint("features/manifiesto")
  csv_atomico(inventario,file.path(d,"features.csv"))
  csv_atomico(inventario[,.(N=.N),by=bloque],file.path(d,"inventario_resumen.csv"))
  rds_atomico(list(CURRENT=CURRENT,vars_lag=vars_lag,vars_delta=vars_delta,
    FEATURES=FEATURES,DATA_ID=DATA_ID,FEATURE_ID=FEATURE_ID,PIPE_ID=PIPE_ID),file.path(d,"manifiesto.rds"))
  csv_atomico(conteos,file.path(d,"conteos_oficiales.csv"))
  cerrar_checkpoint("features/manifiesto",PIPE_ID)
}
print(inventario[,.(N=.N),by=bloque]); message("Features RAW T4: ",length(FEATURES))

# [Anotación · líneas 590–619] construir_mes(): para un mes y para k de 1 a 4 busca el mes calendario k meses
#   antes, empareja por numero_de_cliente, crea el indicador lagK_disponible (1 si el cliente está en ese mes),
#   copia el valor de cada variable como lagK_ y calcula deltaK_ como valor actual menos lag. Los faltantes
#   quedan en NA.
#%% celda 8 [código]
# BLOQUE 6 — Historia exacta por cliente/mes y caches verificadas #####
construir_mes <- function(origen,mes) {
  act <- origen[foto_mes==mes]
  if (!nrow(act) || anyDuplicated(act$numero_de_cliente)) stop("Mes actual inválido: ",mes)
  d <- copy(act[,c("numero_de_cliente","foto_mes","clase_ternaria","binaria2",vars_lag),with=FALSE])
  for (k in 1:4) {
    mes_k <- mes_anterior(mes,k)
    hist <- origen[foto_mes==mes_k]
    if (anyDuplicated(hist$numero_de_cliente)) stop("Duplicados en historia: ",mes_k)
    pos <- match(d$numero_de_cliente,hist$numero_de_cliente)
    flag <- as.integer(!is.na(pos))
    set(d,j=paste0("lag",k,"_disponible"),value=flag)
    for (v in vars_lag) {
      value <- hist[[v]][pos]
      # En historia global ausente, se crea un vector NA del tipo correcto.
      if (!length(hist)) value <- rep(NA_real_,nrow(d))
      set(d,j=paste0("lag",k,"_",v),value=value)
    }
    for (v in vars_delta)
      set(d,j=paste0("delta",k,"_",v),
          value=d[[v]]-d[[paste0("lag",k,"_",v)]])
    stopifnot(all(d[[paste0("lag",k,"_disponible")]]==flag))
    message("Mes ",mes," lag",k," = ",mes_k," / clientes con historia ",sum(flag))
  }
  setcolorder(d,c("numero_de_cliente","foto_mes","clase_ternaria","binaria2",FEATURES[-(1:2)]))
  stopifnot(identical(names(d)[-(3:4)],FEATURES),nrow(d)==nrow(act),
            identical(as.character(d$numero_de_cliente),as.character(act$numero_de_cliente)))
  d
}
# [Anotación · líneas 620–642] cache_mes(): si existe el archivo RDS del mes con su metadato, comprueba firma,
#   MD5, columnas y cantidad de filas y lo devuelve; si no, construye el mes, valida la clase y lo guarda sin
#   comprimir en OUT/cache.
cache_mes <- function(m) {
  f <- file.path(OUT,"cache",paste0("mes_",m,"_RAW_T4.rds"))
  meta_f <- paste0(f,".meta.rds")
  sig <- firma(list(pipe=PIPE_ID,mes=m,raw_md5=raw_md5))
  if (file.exists(f) && file.exists(meta_f)) {
    meta <- readRDS(meta_f)
    if (!identical(meta$sig,sig) || !identical(meta$md5,md5(f)))
      stop("Cache existente incompatible/corrupta: ",f)
    z <- readRDS(f)
    if (!identical(names(z)[-(3:4)],FEATURES) ||
        any(z$foto_mes!=m) || nrow(z)!=filas_oficiales[foto_mes==m,N])
      stop("Cache no superó controles: ",f)
    message("Cache verificada: ",f)
    return(z)
  }
  if (file.exists(f) || file.exists(meta_f)) stop("Cache incompleta; conservar y revisar: ",f)
  z <- construir_mes(dataset,m)
  validar_target(z,m!=202108L)
  rds_atomico(z,f,comprimir=FALSE)
  rds_atomico(list(sig=sig,md5=md5(f),n=nrow(z),features=FEATURE_ID),meta_f)
  message("Cache creada e íntegra: ",f)
  z
}
# [Anotación · líneas 643–675] Construye 202106 y 202108. Comprueba las cantidades de filas (164.114 y
#   164.647), que los indicadores de disponibilidad coincidan con la presencia del cliente en cada mes anterior,
#   que el lag 4 de junio (202102) no tenga datos, que los lags y deltas de ccajas_depositos que caen en mayo
#   sean NA y que todas las variables sean numéricas. Libera el crudo de memoria.
JUNIO <- cache_mes(202106L)
AGOSTO <- cache_mes(202108L)
validar_ids(AGOSTO$numero_de_cliente,UNIVERSO)
stopifnot(nrow(JUNIO)==164114L,nrow(AGOSTO)==164647L,
          identical(names(JUNIO),names(AGOSTO)),
          identical(names(JUNIO)[-(3:4)],FEATURES))
# Disponibilidad exacta, incluidas las ausencias en febrero.
for (k in 1:4) {
  mj <- mes_anterior(202106L,k)
  ma <- mes_anterior(202108L,k)
  nj <- JUNIO[[paste0("lag",k,"_disponible")]]
  na <- AGOSTO[[paste0("lag",k,"_disponible")]]
  stopifnot(identical(nj,as.integer(JUNIO$numero_de_cliente %in%
                       dataset[foto_mes==mj,numero_de_cliente])),
            identical(na,as.integer(AGOSTO$numero_de_cliente %in%
                       dataset[foto_mes==ma,numero_de_cliente])))
  if (k==4L) stopifnot(all(nj==0L))
}
# Mayo ccajas_depositos corregido: sus lags/deltas de junio/agosto deben ser NA.
stopifnot(all(is.na(JUNIO[lag1_disponible==1L,lag1_ccajas_depositos])),
          all(is.na(JUNIO[lag1_disponible==1L,delta1_ccajas_depositos])),
          all(is.na(AGOSTO[lag3_disponible==1L,lag3_ccajas_depositos])),
          all(is.na(AGOSTO[lag3_disponible==1L,delta3_ccajas_depositos])),
          all(is.na(JUNIO$lag4_ccajas_depositos)),all(is.na(JUNIO$delta4_ccajas_depositos)))
# Verificar tipos/NA al convertir a data.matrix; no imputar nada.
for (v in FEATURES)
  if (!is.numeric(JUNIO[[v]]) || !is.numeric(AGOSTO[[v]]))
    stop("Feature no numérica: ",v)
stopifnot(identical(is.na(data.matrix(JUNIO[1:20,..FEATURES])),
                    is.na(as.matrix(JUNIO[1:20,..FEATURES]))))
# El crudo en memoria puede liberarse: junio y agosto son autosuficientes.
rm(dataset); gc(verbose=FALSE)
message("Preflight OK: 1348 RAW; sin febrero; mayo depósitos NA; junio/agosto íntegros.")

# [Anotación · líneas 677–703] Partición fija de junio para la BO: con set.seed(727777), dentro de cada clase
#   (BAJA+1, BAJA+2, CONTINUA) sortea el 20% de las filas como validación y deja el resto como entrenamiento. La
#   guarda en el checkpoint bo/split, la relee, la valida e imprime las fracciones.
#%% celda 9 [código]
# BLOQUE 7 — Split BO fijo, estratificado en tres clases y persistido #####
SPLIT_ID <- firma(list(pipe=PIPE_ID,mes=202106L,pct=0.20,seed=727777L,
  criterio="ESTRATIFICADO_CLASE_TERNARIA"))
ck <- abrir_checkpoint("bo/split",SPLIT_ID)
if (is.null(ck)) {
  part <- JUNIO[,.(numero_de_cliente,clase_ternaria)]
  part[,split := "train"]
  set.seed(727777L,kind="L'Ecuyer-CMRG",normal.kind="Inversion",sample.kind="Rejection")
  for (cl in c("BAJA+1","BAJA+2","CONTINUA")) {
    idx <- which(part$clase_ternaria==cl)
    valid_idx <- sample(idx,size=as.integer(round(length(idx)*0.20)))
    set(part,i=valid_idx,j="split",value="valid")
  }
  d <- iniciar_checkpoint("bo/split")
  csv_atomico(part,file.path(d,"particion_junio_80_20.csv"))
  csv_atomico(part[,.(N=.N),by=.(clase_ternaria,split)],file.path(d,"conteos_strata.csv"))
  cerrar_checkpoint("bo/split",SPLIT_ID)
}
part <- fread(file.path(ck_dir("bo/split"),"particion_junio_80_20.csv"))
validar_ids(part$numero_de_cliente,JUNIO$numero_de_cliente)
stopifnot(!anyNA(part$split),all(part$split %in% c("train","valid")),
          all(part$clase_ternaria==JUNIO$clase_ternaria),
          !length(intersect(part[split=="train",numero_de_cliente],
                            part[split=="valid",numero_de_cliente])))
print(part[,.(N=.N,fraccion=.N/sum(JUNIO$clase_ternaria==clase_ternaria[1L])),
  by=.(clase_ternaria,split)][order(clase_ternaria,split)])

# [Anotación · líneas 705–714] Espacio de búsqueda: num_iterations 64–4096, num_leaves 16–2048,
#   min_sum_hessian_in_leaf 0,000001–0,1. BO_ID firma el método con 10 puntos iniciales y 10 de EI.
#%% celda 10 [código]
# BLOQUE 8 — BO E012: Kriging + EI; 10 LHS + 10 EGO #####
dominio_BO <- function() ps(
  num_iterations=p_int(lower=64L,upper=4096L),
  num_leaves=p_int(lower=16L,upper=2048L),
  min_sum_hessian_in_leaf=p_dbl(lower=1e-6,upper=0.1)
)
BO_ID <- firma(list(pipe=PIPE_ID,split=SPLIT_ID,metodo="REGR_KM_BFGS_EI_RANDOM1000_EGO",
                   iniciales=10L,EI=10L,seed=727777L,escala="LINEAL"))
BO_CTX <- new.env(parent=emptyenv())

# [Anotación · líneas 716–740] objetivo_BO(): entrena con el 80% de junio y la semilla 727777, predice el 20%
#   restante y calcula AUC y Brier; devuelve el AUC como métrica a maximizar y vuelve a fijar la semilla.
# Función global: al serializar el motor NO se incrustan matrices de entrenamiento.
objetivo_BO <- function(xs) {
  hp <- hp_lista(xs)
  if (!identical(hp,BO_CTX$hp)) stop("La propuesta BO no coincide con el checkpoint pendiente.")
  t0 <- proc.time()[["elapsed"]]
  resultado <- ajustar_E012(BO_CTX$X,BO_CTX$y,BO_CTX$Xvalid,hp,PARAM$seed_BO)
  pred <- copy(BO_CTX$valid)
  pred[,prediction := resultado$p]
  auc <- auc_binaria(pred$binaria2,pred$prediction)
  stopifnot(is.finite(auc))
  BO_CTX$resultado <- list(pred=pred,meta=data.table(
    eval_id=BO_CTX$eval_id,origen=BO_CTX$origen,
    num_iterations=hp$num_iterations,num_leaves=hp$num_leaves,
    min_sum_hessian_in_leaf=hp$min_sum_hessian_in_leaf,
    seed=PARAM$seed_BO,AUC=auc,
    brier=mean((pred$prediction-pred$binaria2)^2),
    contexto="HOLDOUT_20PC_JUNIO_NO_GANANCIA_COMPLETA",feature_id=FEATURE_ID,
    n_train=nrow(BO_CTX$X),n_valid=nrow(pred),
    seg_entrenamiento=resultado$seg_entrenamiento,seg_prediccion=resultado$seg_prediccion,
    seg_evaluacion=proc.time()[["elapsed"]]-t0-resultado$seg_entrenamiento,
    seg_total=proc.time()[["elapsed"]]-t0))
  # Reset presente en SAFE efectivamente ejecutado y en Pasquini.
  set.seed(PARAM$seed_BO,kind="L'Ecuyer-CMRG",normal.kind="Inversion",sample.kind="Rejection")
  list(metrica=auc)
}
# [Anotación · líneas 741–784] Motor de la BO (instancia bbotk con tope de 20 evaluaciones, surrogate Kriging
#   regr.km, adquisición EI con búsqueda al azar de 1.000 puntos), propuesta del siguiente punto, guardado y
#   reposición del generador aleatorio y validación del estado guardado (10 puntos LHS).
nuevo_motor_BO <- function(fun=objetivo_BO) {
  instancia <- OptimInstanceBatchSingleCrit$new(
    objective=ObjectiveRFun$new(fun=fun,domain=dominio_BO(),
      codomain=ps(metrica=p_dbl(tags="maximize")),id="BO_E012_JUNIO_80_20"),
    terminator=trm("evals",n_evals=PARAM$n_total))
  surrogate <- srlrn(lrn("regr.km",optim.method="BFGS",nugget.estim=TRUE,
                         control=list(trace=FALSE)))
  acq <- acqf("ei")
  acqopt <- acqo(optimizer=opt("random_search",batch_size=1000),
                terminator=trm("evals",n_evals=1000))
  surrogate$archive <- instancia$archive
  acq$surrogate <- surrogate
  acqopt$acq_function <- acq
  list(instance=instancia,surrogate=surrogate,acq_function=acq,acq_optimizer=acqopt)
}
proponer_EI <- function(motor) {
  # Las mismas tres llamadas del cuerpo de bayesopt_ego(), separadas para poder
  # confirmar la propuesta ANTES de entrenar. No se cambia el optimizador de EI.
  motor$surrogate$archive <- motor$instance$archive
  motor$acq_function$surrogate <- motor$surrogate
  motor$acq_optimizer$acq_function <- motor$acq_function
  motor$surrogate$update()
  motor$acq_function$update()
  x <- motor$acq_optimizer$optimize()
  as.data.table(x)[,..hp_campos]
}
guardar_rng <- function() list(kind=RNGkind(),seed=get(".Random.seed",envir=.GlobalEnv))
restaurar_rng <- function(rng) {
  do.call(RNGkind,as.list(rng$kind))
  assign(".Random.seed",rng$seed,envir=.GlobalEnv)
}
validar_estado_BO <- function(z,n) {
  stopifnot(identical(z$bo_id,BO_ID),nrow(z$historia)==n,
            z$motor$instance$archive$n_evals==n,
            nrow(z$lhs)==10L,identical(names(z$lhs),hp_campos))
  if (n) {
    stopifnot(identical(as.integer(z$historia$eval_id),seq_len(n)))
    ar <- z$motor$instance$archive$data
    stopifnot(isTRUE(all.equal(ar$metrica,z$historia$AUC,tolerance=1e-14)))
    for (v in hp_campos) stopifnot(isTRUE(all.equal(as.numeric(ar[[v]]),
      as.numeric(z$historia[[v]]),tolerance=1e-14)))
  }
  invisible(TRUE)
}

# [Anotación · líneas 786–815] ejecutar_BO(), inicio: genera el diseño LHS de 10 puntos bajo la semilla 727777
#   si no hay checkpoint bo/inicio, recupera las evaluaciones cerradas y devuelve el estado sin entrenar si la
#   selección ya está fijada, no queda tiempo o ya hay 20 evaluaciones.
ejecutar_BO <- function() {
  on.exit({rm(list=ls(BO_CTX),envir=BO_CTX);gc(verbose=FALSE)},add=TRUE)
  if (is.null(abrir_checkpoint("bo/inicio",BO_ID))) {
    set.seed(PARAM$seed_BO,kind="L'Ecuyer-CMRG",normal.kind="Inversion",sample.kind="Rejection")
    lhs <- paradox::generate_design_lhs(dominio_BO(),n=10L)$data
    lhs <- lhs[,..hp_campos]
    lhs[,`:=`(num_iterations=as.integer(num_iterations),num_leaves=as.integer(num_leaves))]
    stopifnot(nrow(lhs)==10L,!anyDuplicated(lhs))
    motor <- nuevo_motor_BO()
    set.seed(PARAM$seed_BO,kind="L'Ecuyer-CMRG",normal.kind="Inversion",sample.kind="Rejection")
    estado <- list(bo_id=BO_ID,motor=motor,lhs=lhs,historia=data.table(),
                   rng=guardar_rng(),seg_acumulados=0)
    d <- iniciar_checkpoint("bo/inicio")
    rds_atomico(estado,file.path(d,"estado.rds"))
    csv_atomico(lhs,file.path(d,"LHS_10.csv"))
    cerrar_checkpoint("bo/inicio",BO_ID)
  }
  ultima <- "bo/inicio"; n <- 0L
  # Recuperación automática de TODOS los trabajos confirmados, en orden; no replay de modelos.
  for (i in seq_len(PARAM$n_total)) {
    key <- sprintf("bo/eval_%02d",i)
    ck <- abrir_checkpoint(key,firma(list(bo=BO_ID,eval_id=i)))
    if (is.null(ck)) break
    ultima <- key; n <- i
  }
  estado <- readRDS(file.path(ck_dir(ultima),"estado.rds"))
  validar_estado_BO(estado,n)
  fijada <- abrir_checkpoint("bo/seleccion",BO_ID)
  if (!is.null(fijada) || solo_ensembles || !hay_tiempo() ||
      estado$seg_acumulados>=bo_horas*3600 || n==PARAM$n_total) return(estado)

# [Anotación · líneas 817–851] Arma las matrices de entrenamiento (filas train de la partición) y de
#   validación (filas valid). En cada vuelta toma la propuesta pendiente guardada o genera una nueva (fila del
#   LHS para las evaluaciones 1 a 10, EI desde la 11) y la guarda en un checkpoint antes de entrenar.
  it <- which(part$split=="train"); iv <- which(part$split=="valid")
  BO_CTX$X <- matriz_E012(JUNIO[it]); BO_CTX$y <- JUNIO$binaria2[it]
  BO_CTX$Xvalid <- matriz_E012(JUNIO[iv])
  BO_CTX$valid <- JUNIO[iv,.(numero_de_cliente,foto_mes,clase_ternaria,binaria2)]
  rm(it,iv); gc(verbose=FALSE)
  base_tiempo <- estado$seg_acumulados
  inicio_sesion <- proc.time()[["elapsed"]]
  while (n<PARAM$n_total) {
    gastado <- base_tiempo+proc.time()[["elapsed"]]-inicio_sesion
    if (gastado>=bo_horas*3600 || !hay_tiempo()) break
    i <- n+1L
    key_p <- sprintf("bo/propuesta_%02d",i)
    sig_p <- firma(list(bo=BO_ID,propuesta=i))
    ck_p <- abrir_checkpoint(key_p,sig_p)
    if (!is.null(ck_p)) {
      pendiente <- readRDS(file.path(ck_dir(key_p),"pendiente.rds"))
      estado <- pendiente$estado
      hp <- pendiente$hp
      validar_estado_BO(estado,n)
      restaurar_rng(estado$rng)
      message("Reanudando la misma propuesta BO ",i)
    } else {
      restaurar_rng(estado$rng)
      hp <- if (i<=10L) copy(estado$lhs[i]) else proponer_EI(estado$motor)
      hp <- as.data.table(hp_lista(hp))
      # El continuo de Hessian hace improbable una repetición; nunca la reentrenamos silenciosamente.
      if (n && any(vapply(seq_len(n),function(k)
          identical(hp_lista(estado$historia[k]),hp_lista(hp)),logical(1))))
        stop("EI propuso HP ya evaluados; revisar la adquisición sin repetir entrenamiento.")
      estado$rng <- guardar_rng()
      d <- iniciar_checkpoint(key_p)
      rds_atomico(list(estado=estado,hp=hp),file.path(d,"pendiente.rds"))
      csv_atomico(hp,file.path(d,"hiperparametros.csv"))
      cerrar_checkpoint(key_p,sig_p)
    }
# [Anotación · líneas 852–876] Evalúa la propuesta, agrega el resultado a la historia y cierra el checkpoint
#   de la evaluación con las predicciones del 20% de junio, las métricas, el historial y el estado. Imprime AUC,
#   Brier y minutos.
    # El backup de la propuesta también consume tiempo: volver a consultar el límite.
    if (base_tiempo+proc.time()[["elapsed"]]-inicio_sesion>=bo_horas*3600 || !hay_tiempo()) break
    BO_CTX$hp <- hp_lista(hp); BO_CTX$eval_id <- i
    BO_CTX$origen <- if (i<=10L) "LHS" else "EI"
    message("BO ",i,"/20: ",paste(unlist(BO_CTX$hp),collapse=" / "))
    restaurar_rng(estado$rng)
    estado$motor$instance$eval_batch(hp)
    z <- BO_CTX$resultado
    estado$historia <- rbindlist(list(estado$historia,z$meta),use.names=TRUE,fill=TRUE)
    estado$rng <- guardar_rng()
    estado$seg_acumulados <- base_tiempo+proc.time()[["elapsed"]]-inicio_sesion
    validar_estado_BO(estado,i)
    key <- sprintf("bo/eval_%02d",i); d <- iniciar_checkpoint(key)
    csv_atomico(z$pred,file.path(d,"predicciones_junio.csv"))
    csv_atomico(z$meta,file.path(d,"metricas.csv"))
    csv_atomico(estado$historia,file.path(d,"historial_BO.csv"))
    rds_atomico(estado,file.path(d,"estado.rds"))
    cerrar_checkpoint(key,firma(list(bo=BO_ID,eval_id=i)))
    n <- i
    message(sprintf("BO %d confirmada: AUC %.8f | Brier %.6f | %.1f min",
                    i,z$meta$AUC,z$meta$brier,z$meta$seg_total/60))
    rm(z); BO_CTX$resultado <- NULL; gc(verbose=FALSE)
  }
  estado
}

# [Anotación · líneas 878–915] Redefine gcs_comando() con la misma lógica y expresiones regulares que piden
#   404 y 403 como palabras completas. La celda siguiente vuelve a poner respaldo_GCS en FALSE.
#%% celda 11 [código]
gcs_comando <- function(args, permitir_ausente=FALSE) {
  err <- tempfile()
  on.exit(unlink(err), add=TRUE)

  out <- suppressWarnings(system2(
    gcloud, vapply(c(args, "--quiet"), shQuote, character(1)),
    stdout=TRUE, stderr=err
  ))

  status <- attr(out, "status")

  if (!is.null(status) && status != 0L) {
    detalle <- paste(readLines(err, warn=FALSE), collapse="\n")

    ausente <- grepl(
      "(?i)(\\b404\\b|not found|no such object|matched no objects|no urls matched|does not exist)",
      detalle, perl=TRUE
    )

    permisos <- grepl(
      "(?i)(\\b403\\b|permission|forbidden|access denied)",
      detalle, perl=TRUE
    )

    if (permitir_ausente && ausente && !permisos)
      return(NULL)

    stop("GCS falló; no se inicia el siguiente trabajo. ", detalle)
  }

  out
}

#%% celda 12 [código]
respaldo_GCS <- FALSE
message("GCS interno desactivado; checkpoints locales activos")
print(respaldo_GCS)

# [Anotación · líneas 917–945] Ejecuta o reanuda la BO, ordena la historia por AUC descendente (empates por
#   evaluación más temprana) y guarda la primera como selección en bo/seleccion. HP queda con esos
#   hiperparámetros. Según la salida guardada: 20 evaluaciones (10 LHS + 10 EI), elegida la 17 con AUC
#   0,9116981, num_iterations=2077, num_leaves=682, min_sum_hessian_in_leaf=0,0626847.
#%% celda 13 [código]
# BLOQUE 9 — Reanudar BO y congelar HP ganadores por AUC #####
estado_BO <- ejecutar_BO()
HIST_BO <- estado_BO$historia
if (!nrow(HIST_BO)) stop("No hay evaluaciones BO terminadas. Ampliar bo_horas/límite y reanudar.")
if (is.null(abrir_checkpoint("bo/seleccion",BO_ID))) {
  if (solo_ensembles) stop("No existe selección congelada; ejecutar el pipeline para crearla.")
  ranking <- copy(HIST_BO)
  setorder(ranking,-AUC,eval_id)
  seleccion <- list(hp=hp_lista(ranking[1]),eval_id=ranking$eval_id[1],
    auc=ranking$AUC[1],brier=ranking$brier[1],n_evaluaciones=nrow(HIST_BO),
    n_LHS=sum(HIST_BO$origen=="LHS"),n_EI=sum(HIST_BO$origen=="EI"),
    bo_id=BO_ID,feature_id=FEATURE_ID,criterio="AUC_HOLDOUT_JUNIO_20PC",
    cierre=if(nrow(HIST_BO)==20L) "20_EVALUACIONES" else "PRESUPUESTO_O_LIMITE")
  d <- iniciar_checkpoint("bo/seleccion")
  rds_atomico(seleccion,file.path(d,"seleccion.rds"))
  csv_atomico(ranking,file.path(d,"ranking_AUC.csv"))
  cerrar_checkpoint("bo/seleccion",BO_ID)
}
seleccion <- readRDS(file.path(ck_dir("bo/seleccion"),"seleccion.rds"))
HP <- seleccion$hp
HP_ID <- firma(list(bo=BO_ID,seleccion=seleccion))
stopifnot(seleccion$n_evaluaciones==nrow(HIST_BO),identical(seleccion$feature_id,FEATURE_ID))
message("HP congelados tras ",seleccion$n_evaluaciones," evaluaciones (",
        seleccion$n_LHS," LHS + ",seleccion$n_EI," EI). BO posterior no se mezcla con esta producción.")
print(data.table(eval_id=seleccion$eval_id,AUC=seleccion$auc,
  Brier_holdout=seleccion$brier,as.data.table(HP)))
rm(estado_BO)
gc(verbose=FALSE)

# [Anotación · líneas 947–960] Celda con todas sus líneas comentadas: una envoltura de gcs_comando() para
#   tratar como ausente un error terminado en 'not found: 404'. No se ejecuta.
#%% celda 14 [código]
# gcs_comando_original <- gcs_comando

# gcs_comando <- function(args, permitir_ausente=FALSE) {
#   tryCatch(
#     gcs_comando_original(args, permitir_ausente),
#     error=function(e) {
#       if (permitir_ausente &&
#           grepl("not found: 404\\.?$", conditionMessage(e), ignore.case=TRUE))
#         return(NULL)
#       stop(e)
#     }
#   )
# }

# [Anotación · líneas 962–976] Clave y firma del checkpoint de cada semilla y leer_pred_semilla(), que
#   devuelve las probabilidades de agosto de una semilla ya cerrada, validadas contra el universo.
#%% celda 15 [código]
# BLOQUE 10 — Predicción agosto por semilla; checkpoints GCS #####
clave_semilla <- function(s) paste0("produccion/seed_",s)
firma_semilla <- function(s) firma(list(pipe=PIPE_ID,split=SPLIT_ID,hp=HP_ID,
  mes_train=202106L,mes_score=202108L,seed=as.integer(s)))
leer_pred_semilla <- function(s) {
  key <- clave_semilla(s)
  if (is.null(abrir_checkpoint(key,firma_semilla(s)))) return(NULL)
  meta <- readRDS(file.path(ck_dir(key),"meta.rds"))
  stopifnot(identical(meta$hp_id,HP_ID),identical(meta$feature_id,FEATURE_ID),meta$seed==s)
  p <- fread(file.path(ck_dir(key),"predicciones_agosto.csv"))
  validar_ids(p$numero_de_cliente,UNIVERSO)
  validar_prob(p$prediction,length(UNIVERSO))
  p
}
# [Anotación · líneas 977–999] generar_ensemble(), agregación: entre las semillas disponibles suma las
#   probabilidades y también las posiciones de cada semilla (frank(-probabilidad), empates promedio). Calcula
#   prediction_media y rank_medio dividiendo por la cantidad de semillas y define la carpeta
#   ensembles/nNN_<firma>.
# Ambas agregaciones son diferentes: average(p) != average(rank(p)).
# Rank ascendente numérico es la posición de mayor probabilidad (rank=1).
generar_ensemble <- function(max_semillas=n_semillas) {
  permitidas <- PARAM$semillas[seq_len(max_semillas)]
  suma_p <- numeric(length(UNIVERSO))
  suma_rank <- numeric(length(UNIVERSO))
  usadas <- integer()
  for (s in permitidas) {
    p <- leer_pred_semilla(s)
    if (is.null(p)) next
    suma_p <- suma_p+p$prediction
    # E012 original: frank(-prediction, ties.method="average").
    # El desempate por ID aplica SOLO al ordenar el ensemble/submission.
    rk <- frank(-p$prediction,ties.method="average")
    suma_rank <- suma_rank+rk
    usadas <- c(usadas,s)
  }
  n <- length(usadas)
  if (!n) return(list(n=0L,completo=FALSE,carpeta=NA_character_))
  ens <- data.table(numero_de_cliente=UNIVERSO,prediction_media=suma_p/n,rank_medio=suma_rank/n)
  sig <- firma(list(pipe=PIPE_ID,hp=HP_ID,semillas=usadas,
                    agregacion=c("prediction_media","rank_medio"),cortes=PARAM$cortes))
  key <- paste0("ensembles/n",sprintf("%02d",n),"_",substr(sig,1,12))
# [Anotación · líneas 1000–1032] Escribe ensemble_agosto_ambos_criterios.csv (numero_de_cliente,
#   prediction_media, rank_medio). Para cada criterio ordena (probabilidad media descendente o rank medio
#   ascendente; empates por ID como texto), guarda el ranking y, para cada uno de los 13 cortes de 9.000 a
#   15.000, un archivo de IDs sin encabezado que relee y comprueba. Guarda el manifiesto de listas y meta.rds.
  if (is.null(abrir_checkpoint(key,sig))) {
    d <- iniciar_checkpoint(key)
    csv_atomico(ens,file.path(d,"ensemble_agosto_ambos_criterios.csv"))
    submits <- list()
    for (tipo in c("prediction_media","rank_medio")) {
      orden <- if (tipo=="prediction_media")
        order(-ens$prediction_media,as.character(ens$numero_de_cliente),method="radix") else
        order(ens$rank_medio,as.character(ens$numero_de_cliente),method="radix")
      ranking <- ens[orden,.(numero_de_cliente,prediction_media,rank_medio)]
      ranking[,posicion := seq_len(.N)]
      csv_atomico(ranking,file.path(d,paste0(tipo,"_ranking_agosto.csv")))
      for (topN in PARAM$cortes) {
        arch <- paste0("E012_RAW_T4_BO",sprintf("%02d",seleccion$eval_id),"_",
          tipo,"_n",sprintf("%02d",n),"_top",topN,".csv")
        csv_atomico(ranking[seq_len(topN),.(numero_de_cliente)],file.path(d,arch),encabezado=FALSE)
        ids <- fread(file.path(d,arch),header=FALSE)[[1L]]
        stopifnot(length(ids)==topN,!anyDuplicated(ids))
        validar_ids(ids,ranking$numero_de_cliente[seq_len(topN)])
        submits[[length(submits)+1L]] <- data.table(tipo=tipo,n_semillas=n,
          topN=topN,archivo=arch,md5=md5(file.path(d,arch)))
      }
    }
    csv_atomico(rbindlist(submits),file.path(d,"manifiesto_submissions.csv"))
    rds_atomico(list(hp=HP,hp_id=HP_ID,feature_id=FEATURE_ID,
      semillas=usadas,n_semillas=n,objetivo_al_crear=max_semillas,
      metodos=c("media probabilidades","frank(-prob) por seed con empates promedio; desempate final ID texto ascendente")),
      file.path(d,"meta.rds"))
    cerrar_checkpoint(key,sig)
    message("Ensemble E012 de ",n," semillas; 2 criterios × ",length(PARAM$cortes),
            " submissions, verificados y respaldados.")
  }
  list(n=n,completo=n==max_semillas,carpeta=ck_dir(key),checkpoint=key)
}
# [Anotación · líneas 1033–1061] ejecutar_produccion(): exporta el ensemble con lo disponible; luego arma la
#   matriz con junio completo (164.114 filas) y la de agosto (164.647) y, para cada semilla sin checkpoint entre
#   las primeras n_semillas, entrena, guarda predicciones_agosto.csv y metadatos, cierra el checkpoint y
#   regenera el ensemble.
ejecutar_produccion <- function() {
  estado <- generar_ensemble()
  if (estado$completo || solo_ensembles || !hay_tiempo()) return(estado)
  X <- matriz_E012(JUNIO); y <- JUNIO$binaria2
  Xscore <- matriz_E012(AGOSTO)
  stopifnot(!anyNA(y),nrow(X)==164114L,nrow(Xscore)==164647L,
            identical(colnames(X),colnames(Xscore)))
  for (s in PARAM$semillas[seq_len(n_semillas)]) {
    key <- clave_semilla(s); sig <- firma_semilla(s)
    if (!is.null(abrir_checkpoint(key,sig))) next
    if (!hay_tiempo()) break
    d <- iniciar_checkpoint(key)
    message("E012 producción seed ",s," (junio FULL => agosto)")
    z <- ajustar_E012(X,y,Xscore,HP,s,
      modelo_archivo=if (guardar_modelos) file.path(d,"modelo.txt") else NULL)
    p <- data.table(numero_de_cliente=UNIVERSO,prediction=z$p)
    validar_ids(p$numero_de_cliente,UNIVERSO)
    csv_atomico(p,file.path(d,"predicciones_agosto.csv"))
    rds_atomico(list(seed=as.integer(s),hp=HP,hp_id=HP_ID,
      feature_id=FEATURE_ID,train=202106L,score=202108L,n_train=nrow(X),
      n_score=length(UNIVERSO),seg_entrenamiento=z$seg_entrenamiento,
      seg_prediccion=z$seg_prediccion),file.path(d,"meta.rds"))
    cerrar_checkpoint(key,sig)
    rm(z,p);gc(verbose=FALSE)
    # Primera submission tras seed 1, otras tras cada seed; seed 5 queda garantizada.
    estado <- generar_ensemble()
  }
  generar_ensemble()
}

# [Anotación · líneas 1063–1077] Ejecuta la producción con n_semillas=10 e informa cuántas semillas quedan
#   listas. La celda siguiente cambia n_semillas a 20 y vuelve a ejecutar la producción, que entrena sólo las
#   semillas que faltan; cada cantidad de semillas deja su propia carpeta de ensemble (el notebook 3 lee la de
#   12).
#%% celda 16 [código]
# BLOQUE 11 — Ejecutar producción prioritaria: cinco y luego diez semillas #####
# La misma función confirma un checkpoint por semilla y ensambla tras cada una.
# Las 5 primeras están antes que las adicionales en PARAM$semillas.
PRODUCCION <- ejecutar_produccion()
if (PRODUCCION$n>=5L) message("CINCO semillas de producción y ambos ensembles disponibles.")
if (PRODUCCION$n<n_semillas)
  message("Producción parcial: ",PRODUCCION$n,"/",n_semillas,
          ". Reanudar para completar las faltantes.")
print(data.table(semillas_listas=PRODUCCION$n,objetivo=n_semillas,
  ruta=PRODUCCION$carpeta))

#%% celda 17 [código]
n_semillas <- 20L
PRODUCCION <- ejecutar_produccion()

# [Anotación · líneas 1079–1116] OOF de junio, preparación: crear_folds() reparte las filas de junio en 5
#   folds dentro de cada clase ternaria con set.seed(727777) y los guarda; leer_oof_fold() devuelve las
#   predicciones de un fold ya cerrado. Esta parte se ejecuta después de la producción y no interviene en las
#   predicciones de agosto.
#%% celda 18 [código]
# BLOQUE 12 — Folds OOF junio (tres clases, deterministas, postproducción) #####
OOF_ID <- firma(list(pipe=PIPE_ID,split=SPLIT_ID,hp=HP_ID,
  criterio="5_FOLDS_ESTRATIFICADOS_TERNARIA",seed=727777L,mes=202106L))
crear_folds <- function() {
  ck <- abrir_checkpoint("oof/folds",OOF_ID)
  if (!is.null(ck)) {
    f <- fread(file.path(ck_dir("oof/folds"),"folds.csv"))
  } else {
    f <- JUNIO[,.(numero_de_cliente,clase_ternaria)]
    f[,fold := NA_integer_]
    set.seed(727777L,kind="L'Ecuyer-CMRG",normal.kind="Inversion",sample.kind="Rejection")
    for (cl in c("BAJA+1","BAJA+2","CONTINUA")) {
      idx <- which(f$clase_ternaria==cl)
      sh <- sample(idx,length(idx))
      set(f,i=sh,j="fold",value=rep(1:5,length.out=length(sh)))
    }
    d <- iniciar_checkpoint("oof/folds")
    csv_atomico(f,file.path(d,"folds.csv"))
    csv_atomico(f[,.(N=.N),by=.(fold,clase_ternaria)],file.path(d,"conteos_fold.csv"))
    cerrar_checkpoint("oof/folds",OOF_ID)
  }
  validar_ids(f$numero_de_cliente,JUNIO$numero_de_cliente)
  stopifnot(!anyNA(f$fold),all(f$fold %in% 1:5),
            all(f$clase_ternaria==JUNIO$clase_ternaria))
  f
}
leer_oof_fold <- function(seed,k,ff) {
  key <- paste0("oof/seed_",seed,"/fold_",k)
  sig <- firma(list(oof=OOF_ID,seed=as.integer(seed),fold=as.integer(k)))
  if (is.null(abrir_checkpoint(key,sig))) return(NULL)
  d <- fread(file.path(ck_dir(key),"predicciones.csv"))
  ids <- JUNIO$numero_de_cliente[which(ff$fold==k)]
  validar_ids(d$numero_de_cliente,ids)
  validar_prob(d$prediction,length(ids))
  stopifnot(all(d$fold==k))
  d
}
# [Anotación · líneas 1117–1153] ejecutar_oof(): sólo corre si ejecutar_OOF es TRUE y la producción está
#   completa. Para cada una de las primeras n_semillas_OOF=5 semillas y cada fold entrena con los otros cuatro
#   folds y predice el fold, con un checkpoint por semilla y fold.
ejecutar_oof <- function() {
  if (!ejecutar_OOF || solo_ensembles || !isTRUE(PRODUCCION$completo)) {
    message("OOF no ejecutada: desactivada o producción pendiente.")
    return(invisible(NULL))
  }
  ff <- crear_folds()
  X <- NULL
  for (s in PARAM$semillas[seq_len(n_semillas_OOF)]) {
    preds <- rep(NA_real_,nrow(JUNIO))
    for (k in 1:5) {
      it <- which(ff$fold!=k);iv <- which(ff$fold==k)
      stopifnot(!length(intersect(JUNIO$numero_de_cliente[it],JUNIO$numero_de_cliente[iv])))
      p <- leer_oof_fold(s,k,ff)
      if (is.null(p)) {
        if (!hay_tiempo()) {
          message("Deadline: OOF pausada en seed ",s," fold ",k)
          return(invisible(NULL))
        }
        if (is.null(X)) X <- matriz_E012(JUNIO)
        key <- paste0("oof/seed_",s,"/fold_",k)
        sig <- firma(list(oof=OOF_ID,seed=as.integer(s),fold=as.integer(k)))
        d <- iniciar_checkpoint(key)
        message("E012 OOF: seed ",s," fold ",k,"/5")
        z <- ajustar_E012(X[it,,drop=FALSE],JUNIO$binaria2[it],
          X[iv,,drop=FALSE],HP,s,
          modelo_archivo=if(guardar_modelos) file.path(d,"modelo.txt") else NULL)
        p <- JUNIO[iv,.(numero_de_cliente,foto_mes,clase_ternaria,binaria2)]
        p[,`:=`(fold=k,seed=as.integer(s),prediction=z$p)]
        csv_atomico(p,file.path(d,"predicciones.csv"))
        rds_atomico(list(seed=s,fold=k,hp_id=HP_ID,feature_id=FEATURE_ID,
          n_train=length(it),n_valid=length(iv),seg_entrenamiento=z$seg_entrenamiento),
          file.path(d,"meta.rds"))
        cerrar_checkpoint(key,sig)
        rm(z);gc(verbose=FALSE)
      }
      preds[iv] <- p$prediction
    }
# [Anotación · líneas 1154–1173] Por semilla calcula sobre junio completo el AUC, la curva de ganancia,
#   GainBand (promedio de la ganancia acumulada en 11.500, 12.000, 12.500, 13.000 y 13.500) y la ganancia en
#   12.500, y guarda las predicciones fuera de fold, la curva completa, la ganancia en los cortes y las
#   métricas.
    validar_prob(preds,nrow(JUNIO))
    key <- paste0("oof/resumen_seed_",s)
    sig <- firma(list(oof=OOF_ID,seed=as.integer(s),resumen="GAIN_JUNIO_COMPLETO"))
    if (is.null(abrir_checkpoint(key,sig))) {
      d <- iniciar_checkpoint(key)
      curva <- curva_ganancia(JUNIO,preds)
      metricas <- data.table(seed=s,auc=auc_binaria(JUNIO$binaria2,preds),
        GainBand=mean(curva$ganancia_acumulada[PARAM$gainband]),
        ganancia_top12500=curva$ganancia_acumulada[12500L],
        n_junio=nrow(JUNIO),n_folds=5L,independiente_BO=FALSE)
      csv_atomico(JUNIO[,.(numero_de_cliente,foto_mes,clase_ternaria,binaria2)][,
        prediction := preds],file.path(d,"OOF_junio.csv"))
      csv_atomico(curva,file.path(d,"curva_completa.csv"))
      csv_atomico(curva[cutoff %in% PARAM$cortes],file.path(d,"ganancia_topN.csv"))
      csv_atomico(metricas,file.path(d,"metricas.csv"))
      cerrar_checkpoint(key,sig)
      message(sprintf("OOF seed %d: AUC %.7f | GainBand %.3f M",s,
                      metricas$auc,metricas$GainBand/1e6))
    }
  }
# [Anotación · líneas 1174–1197] Reúne las métricas de las semillas disponibles, imprime media, desvío, mínimo
#   y máximo de AUC y GainBand y guarda el agregado en un checkpoint.
  disponible <- rbindlist(lapply(PARAM$semillas[1:n_semillas_OOF],function(s) {
    key <- paste0("oof/resumen_seed_",s)
    sig <- firma(list(oof=OOF_ID,seed=as.integer(s),resumen="GAIN_JUNIO_COMPLETO"))
    if (is.null(abrir_checkpoint(key,sig))) return(NULL)
    fread(file.path(ck_dir(key),"metricas.csv"))
  }),fill=TRUE)
  if (nrow(disponible)) {
    print(disponible)
    print(disponible[,.(semillas=.N,AUC_media=mean(auc),AUC_sd=if(.N>1)sd(auc) else NA_real_,
      GainBand_media=mean(GainBand),GainBand_sd=if(.N>1)sd(GainBand) else NA_real_,
      GainBand_min=min(GainBand),GainBand_max=max(GainBand))])
    sig <- firma(list(oof=OOF_ID,seeds=disponible$seed,resumen="AGREGADO"))
    key <- paste0("oof/agregado_n",nrow(disponible),"_",substr(sig,1,12))
    if (is.null(abrir_checkpoint(key,sig))) {
      d <- iniciar_checkpoint(key)
      csv_atomico(disponible,file.path(d,"metricas_por_semilla.csv"))
      csv_atomico(disponible[,.(N=.N,AUC_media=mean(auc),AUC_sd=if(.N>1)sd(auc) else NA_real_,
        GainBand_media=mean(GainBand),GainBand_sd=if(.N>1)sd(GainBand) else NA_real_)],
        file.path(d,"resumen.csv"))
      cerrar_checkpoint(key,sig)
    }
  }
  invisible(disponible)
}

# [Anotación · líneas 1199–1212] Ejecuta la OOF e imprime mensajes de cierre con las semillas de producción
#   completadas y la carpeta del ensemble. Sigue una celda de texto sobre la recuperación desde checkpoints, el
#   presupuesto bo_horas, el límite horario y la relación entre la OOF y la BO.
#%% celda 19 [código]
# BLOQUE 13 — OOF opcional posterior a la producción #####
RESUMEN_OOF <- ejecutar_oof()
message("E012 completó lo habilitado por configuraciones y límite horario.")
message("Producción: ",PRODUCCION$n,"/",n_semillas," semillas; carpeta: ",PRODUCCION$carpeta)
message("Submissions: IDs únicos SIN cabecera; tipos prediction_media y rank_medio; topN 9000:15000.")
message("Nunca se suben automáticamente a Kaggle; los commits GCS son independientes de SAFE.")

#%% celda 20 [texto]
## Recuperación, límites y trazabilidad

Cada `checkpoints/` confirmado tiene metadatos, tamaño, MD5 de todos sus archivos, COMMIT local y copia GCS inmutable. Al reiniciar otra VM se recupera de GCS antes de entrenar otra vez. Un checkpoint local sin copia remota se termina de respaldar sin volver a entrenar. Las caches grandes RAW T4 se regeneran desde la URL oficial (sin dependencia de Drive). El crudo original permanece intacto. Si hay un cambio de librerías, datos, features o HP, las firmas impiden mezclar resultados.

**Importante sobre deadline:** `bo_horas` es un presupuesto acumulado que permite terminar la BO antes de las 20 evaluaciones, pero una evaluación en curso no se interrumpe. La selección de HP se congela una sola vez; ampliar `bo_horas` después de congelarla no vuelve a optimizar. La producción puede quedar parcial y deja submissions utilizables de cada conjunto de semillas completadas; si se quiere reanudar luego de 23:59 ART hay que actualizar `limite_ART` a `NA_character_`. La OOF se programa al final y exige producción completa de `n_semillas`, salvo que se reduzca ese control para priorizarla. Ninguna OOF posterior se presenta como evaluación externa de la BO.

# [Anotación · líneas 1214–1258] Celda de consulta con ruta absoluta /home/ds/Expe/...: lee la selección de la
#   BO y las métricas OOF de cinco semillas, promedia entre semillas la ganancia acumulada de junio por corte e
#   imprime los 10 cortes de mayor ganancia media. No escribe archivos.
#%% celda 21 [código]
library(data.table)

base <- "/home/ds/Expe/experimentos/C01_E012_RAW_T4_BO_FINAL_V1/checkpoints"

# 1. HIPERPARÁMETROS GANADORES DE LA BO

sel <- readRDS(file.path(base, "bo/seleccion/seleccion.rds"))

print(sel[c("eval_id", "auc", "n_evaluaciones")])
print(sel$hp)

# 2. GANANCIA OOF DE JUNIO POR SEMILLA

semillas <- c(727777L, 773777L, 775777L, 777737L, 787777L)

metricas <- rbindlist(lapply(semillas, function(s) {
  fread(file.path(base, paste0("oof/resumen_seed_", s), "metricas.csv"))
}))

print(metricas)

print(metricas[, .(
  AUC_media = mean(auc),
  GainBand_media = mean(GainBand),
  ganancia_top12500_media = mean(ganancia_top12500)
)])

# 3. CURVA DE GANANCIA DE JUNIO, PROMEDIO DE 5 SEMILLAS

curvas <- rbindlist(lapply(semillas, function(s) {
  x <- fread(file.path(base, paste0("oof/resumen_seed_", s), "ganancia_topN.csv"))
  x[, seed := s]
  x
}))

resumen <- curvas[, .(
  ganancia_media = mean(ganancia_acumulada),
  ganancia_sd = sd(ganancia_acumulada),
  bajas2_media = mean(bajas2_acumuladas)
), by = cutoff][order(-ganancia_media)]

# 4. MEJORES 10 CUTOFFS DE JUNIO

print(head(resumen, 10))

# [Anotación · líneas 1260–1317] Celda de utilidad con ruta absoluta: busca las carpetas de ensembles
#   cerradas, elige la que tiene más semillas, comprueba el archivo (164.647 filas, tres columnas,
#   probabilidades entre 0 y 1) y lo copia a E012_AGOSTO_<NN>_SEMILLAS_PREDICCIONES_COMPLETAS.csv verificando el
#   MD5 de la copia. El notebook 3 no lee esta copia.
#%% celda 22 [código]
library(data.table)

base <- "/home/ds/Expe/experimentos/C01_E012_RAW_T4_BO_FINAL_V1"

# Buscar ensembles terminados
carpetas <- list.files(
  file.path(base, "checkpoints", "ensembles"),
  full.names = TRUE
)
carpetas <- carpetas[dir.exists(carpetas)]

carpetas <- carpetas[
  file.exists(file.path(carpetas, "COMMIT.rds")) &
  file.exists(file.path(carpetas, "meta.rds")) &
  file.exists(file.path(carpetas, "ensemble_agosto_ambos_criterios.csv"))
]

if (!length(carpetas)) stop("No se encontraron ensembles terminados")

# Elegir el que tenga más semillas
metas <- lapply(carpetas, function(d) readRDS(file.path(d, "meta.rds")))
ns <- vapply(metas, function(m) m$n_semillas, integer(1))
i <- which.max(ns)

origen <- file.path(carpetas[i], "ensemble_agosto_ambos_criterios.csv")

# Verificar predicciones
pred <- fread(origen)

stopifnot(
  nrow(pred) == 164647L,
  identical(names(pred), c("numero_de_cliente", "prediction_media", "rank_medio")),
  !anyNA(pred),
  !anyDuplicated(pred$numero_de_cliente),
  all(is.finite(pred$prediction_media)),
  all(pred$prediction_media >= 0 & pred$prediction_media <= 1)
)

# Guardar copia fácilmente accesible
destino <- file.path(
  base,
  sprintf("E012_AGOSTO_%02d_SEMILLAS_PREDICCIONES_COMPLETAS.csv", ns[i])
)

if (!file.copy(origen, destino, overwrite=TRUE))
  stop("No se pudo copiar el archivo")

stopifnot(
  identical(
    unname(tools::md5sum(origen)),
    unname(tools::md5sum(destino))
  )
)

message("Semillas: ", ns[i])
message("Clientes: ", nrow(pred))
message("Archivo guardado: ", destino)
```

### 1-C01_SAFE_P2_P3_FINAL_HNC5.ipynb

Notebook de R que produce el modelo SAFE P2: descarga el crudo, arma la clase y las variables con rank con signo por mes, busca hiperparámetros, aplica la limpieza HNC del 5% y entrena LightGBM en 202105+202106 con 10 semillas; deja las probabilidades promedio de agosto que lee el notebook 3. Contiene también la variante P3 (202103 a 202106), desactivada en el código guardado.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–27] Celda de texto. Presenta el notebook (kernel R) y una tabla con las decisiones
#   declaradas: fuente y etiquetas, diseño, presupuesto y espacio de la BO, parámetros fijos de LightGBM,
#   variables, exclusiones, HNC, producción P2/P3, semillas, cutoffs y cálculo de la ganancia de junio. El texto
#   indica 10 LHS + 10 EI, num_leaves 16–2048, cutoffs 9.500–13.500 y GainBand 11.500–13.500; el código de las
#   celdas 2 y 8 usa 6 LHS + 14 EI, num_leaves 16–1024, cortes 9.500–15.000 y GainBand 11.500–15.000.
#%% celda 1 [texto]
# C01 · SAFE P2/P3 · producción final HNC 5%

**Un único notebook, kernel R (IRkernel).** Descarga la fuente oficial, prepara targets y SAFE RANK T2, ejecuta una BO compartida, genera una limpieza OOF de mayo+junio y produce P2 antes que P3. No necesita Drive, scripts auxiliares, caches privados ni HP anteriores. No se envían submissions automáticamente.

## Auditoría previa a los entrenamientos


| Aspecto | Referencias y decisión aplicada |
|---|---|
| Fuente y etiquetas | URL oficial de la consigna. Leads por cliente y período consecutivo de Pasquini. `binaria2=1` para BAJA+1 o BAJA+2; `0` para CONTINUA. Se conservan NA cuando la clase es desconocida; agosto íntegramente sin etiqueta. Conteos contrastados con la tabla de V5.3. |
| Diseño BO | SAFE ejecutado: marzo+abril → junio, FULL, AUC, sin HNC, sin early stopping. Se conserva; no se traslada el split ni el undersampling del ejemplo docente. |
| Presupuesto | El SAFE adjunto tiene **4 LHS + 10 EI**. La consigna pide **10 LHS + 10 EI, máximo 20**, que es lo implementado. El límite de tiempo puede cerrar antes, incluso durante LHS, siempre que exista al menos una evaluación terminada. |
| Espacio | `num_iterations`: entero 64–4096; `num_leaves`: entero 16–2048; Hessian: real 0.000001–0.1. **Los tres son lineales**, sin transformaciones logarítmicas. |
| Optimización | `regr.km`, BFGS, `nugget.estim=TRUE`; EI; `random_search(batch_size=1000)` y terminación de adquisición a 1000 evaluaciones. Son las llamadas del bucle EGO original, separadas en propuesta, evaluación y checkpoint. Semilla 727777, L'Ecuyer-CMRG; reset tras cada evaluación como en el SAFE ejecutado. Ante fallo del surrogate se detiene: no sustituye silenciosamente EI por otra búsqueda. |
| Fijos LightGBM | Configuración SAFE: learning rate 0.005; feature fraction 0.50; bynode 0.20; min data in leaf 0; max bin 31; GBDT binario, AUC, determinista, row-wise, sin undersampling ni early stopping. Lista completa en el bloque 1. `use_missing=TRUE`, `zero_as_missing=FALSE` explícitos como en V5.3/HNC. |
| Ingeniería | `current`, `lag1`, `delta1`, `lag2`, `delta2`; historia por ID y mes calendario real. Corrección de `ccajas_depositos` sólo en mayo, antes de temporales. Signed ranks positivos y negativos separados, con empates promedio, ceros fijos y NA preservados, dentro de cada mes completo. |
| Exclusiones | SAFE antiguo exige KEEP ALL. La consigna prevalece: se retiran de **todos** los modelos las 5 versiones temporales de cada préstamo y sus ranks. El crudo queda intacto. Se conservan las demás exclusiones SAFE de fechas, metadatos y variables no numéricas. El esquema de las referencias tiene 144 fuentes/720 ranks; al retirar dos fuentes se esperan 710 predictores, pero el manifiesto se deriva de la fuente, sin imponer 740. |
| HNC | Una semilla 727777, cinco folds agrupados por cliente y estratificados por `max(binaria2)` del cliente, sobre mayo+junio. Cada mes retira `floor(n_CONTINUA*5/100)`, por OOF descendente y **ID convertido a texto** en los empates, como HNC V1. Conserva todas las BAJA. No hay screening de porcentajes ni HP transferidos. |
| RNG de HNC | El HNC adjunto usa `set.seed(seed+y)` sin fijar `RNGkind`. Se explicita Mersenne-Twister/Inversion/Rejection, default de una sesión R autónoma, para que no herede L'Ecuyer de la BO. Esta elección queda registrada en la firma HNC. |
| Producción | P2: mayo+junio limpios → agosto. P3: marzo+abril completos + la misma limpieza de mayo+junio → agosto. Ambos usan los mismos HP y features. Los ranks no se recalculan después de excluir filas. |
| Semillas | Se conservan exactamente las 10 semillas y el orden de `PARAM$seeds_final`. **No hay una secuencia histórica 11–50 en los archivos.** Para satisfacer la ampliación se incorpora una extensión determinista explícita, independiente del RNG de BO/OOF, congelada en `config/base/semillas.csv`; no se presenta como una secuencia de la referencia. |
| Cutoffs | Se toman del SAFE principal: 9500, 10000, 10500, 11000, 11500, 12000, 12500, 13000, 13500. HNC V1 usa otra grilla (11000–15000); aquí prevalece la grilla SAFE que pide la consigna. Una columna de IDs, **sin encabezado**. |

**Ganancia de junio:** +1.072.500 por BAJA+2 y −27.500 por las demás observaciones, como las referencias. Se guarda la curva para **todos** los cutoffs y BAJA+2 acumuladas. GainBand es la media de ganancias en 11.500, 12.000, 12.500, 13.000 y 13.500, conforme al SAFE original. HP seleccionado exclusivamente por AUC; empates por evaluación más temprana. La ganancia es evidencia de la **validación temporal sin HNC** utilizada para seleccionar HP, no una estimación independiente de P2/P3 limpios. No se calcula una supuesta ganancia real de agosto sin etiquetas.

Con los conteos oficiales, HNC debe retirar **8.087 CONTINUA de mayo y 8.107 de junio**. Se esperan 311.688 filas de train P2 y 637.872 de P3; la identidad de las filas excluidas depende de las OOF generadas con los HP ganadores.

# [Anotación · líneas 29–38] Celda de texto (continúa). Describe el esquema de checkpoints: qué guarda cada
#   evaluación de la BO, cada fold y cada semilla, la escritura atómica, la subida a GCS verificada por MD5, la
#   recuperación en otra VM y el uso de firmas para no mezclar resultados de configuraciones distintas.
## Checkpoints y recuperación

- Cada evaluación BO conserva predicciones, curva, métricas, historial, diseño LHS, archivo de observaciones de `bbotk`, surrogate y adquisición de `mlr3mbo`, RNG y tiempo acumulado. **La propuesta también se guarda antes de entrenar.** Una interrupción en la 17 conserva las 16 confirmadas y permite retomar exactamente la propuesta pendiente.
- Cada fold y semilla guarda predicciones, HP, firma de features y metadatos. La limpieza guarda todas las filas OOF y su exclusión, el fold, los conteos y la comprobación de BAJA conservadas.
- Los archivos se escriben atómicamente. En GCS se suben como objetos identificados por MD5 y se comprueban tamaño y MD5 remoto; un commit se publica **al final**. Un error de subida detiene la ejecución antes del próximo trabajo. Un resultado local terminado cuyo respaldo falló se respalda al reanudar sin volver a entrenarlo.
- En una VM nueva, el notebook descarga automáticamente los commits y archivos que necesita. Los caches de ranks son locales y regenerables desde el crudo; los resultados costosos, el estado BO y los manifiestos están en GCS. No se borra ni sincroniza destructivamente el bucket.
- Las firmas incluyen parámetros, datos, orden de features, limpieza y versiones de R/paquetes. Un conflicto se detiene; no se reemplazan resultados incompatibles. Para retomar se necesitan las mismas versiones registradas en `config/base/config.rds` y `sessionInfo.txt`. Un cambio metodológico o de versiones requiere otro experimento/prefijo, o restablecer el entorno anterior.
- Una vez elegidos los HP, `bo/seleccion` queda congelado. Reanudar o ampliar semillas no continúa una BO cerrada ni cambia silenciosamente la limpieza. Antes de cerrar por tiempo se puede ampliar `bo_horas`; después de la selección, una BO distinta requiere otro experimento.

Ejecutar **una sola instancia activa** por carpeta/prefijo. No reutilizar este nombre para otro diseño.

# [Anotación · líneas 40–50] Celda de texto (continúa). Instrucciones de uso: ejecutar todas las celdas en
#   orden con kernel R, cómo reanudar, cómo actúan bo_horas, limite_ART y margen_minutos, cómo activar P2 y P3,
#   cómo ampliar n_semillas de 10 a 20 o 50 y dónde quedan las salidas (OUT/checkpoints).
## Uso

1. **Desde cero:** abrir con kernel R, revisar el bloque 1 y ejecutar todas las celdas en orden. Instala sólo paquetes faltantes. La VM necesita `gcloud` autenticado con lectura/escritura en el prefijo configurado. No modifica credenciales ni instala gcloud.
2. **Reanudar:** en esta VM o una nueva, conservar `EXPERIMENTO`, `GCS`, parámetros metodológicos y versiones; volver a ejecutar desde arriba. La raíz local puede cambiar.
3. **Tiempo:** `bo_horas=4` es el presupuesto activo acumulado por defecto; no limita un modelo ya iniciado. `limite_ART` y `margen_minutos=30` impiden iniciar otro trabajo pasada la reserva para el cierre. Tampoco cortan un modelo en curso: un entrenamiento largo puede sobrepasar ese horario. Para reproducción posterior al 11/10/2026, usar `limite_ART <- NA_character_`.
4. **Familias:** cambiar `producir_P2` y `producir_P3`. Si P2 está activo, P3 sólo empieza cuando P2 alcanza el número solicitado y su ensemble/submissions están confirmados. Si el tiempo deja P2 parcial, se conserva y P3 espera. Para producir sólo P3, desactivar P2.
5. **10 → 20 → 50:** cambiar únicamente `n_semillas`. No cambiar la secuencia, HP, features ni HNC. Sólo entrena semillas faltantes; los ensembles anteriores permanecen identificados por el número y conjunto exacto de semillas.
6. **Parciales:** se exporta y respalda un ensemble después de cada semilla terminada. `solo_ensembles <- TRUE` recupera/exporta lo ya disponible sin entrenar; requiere que BO y HNC estén completadas. Los metadatos registran el número real, las semillas y el objetivo al crear el archivo.
7. **GCS:** `respaldo_GCS=TRUE` es obligatorio para esta producción. `SAFE_FINAL_GCS` o `GCS` permiten otro prefijo. Un evaluador externo puede poner `respaldo_GCS <- FALSE`: el pipeline sigue siendo reproducible desde la URL pública, pero los resultados quedarán sólo en su almacenamiento local.

Las salidas están en `OUT/checkpoints`: `bo`, `hnc`, `produccion/P2`, `ensembles/P2`, luego `produccion/P3`, `ensembles/P3`. Cada ensemble contiene probabilidades, ranking completo, nueve submissions y su manifiesto. Los nombres identifican familia, evaluación HP, firma, versión HNC, número de semillas y cutoff. No se mezclan P2 y P3 ni se incluyen metaensembles con E012. Los modelos binarios/texto de LightGBM son opcionales (`guardar_modelos`); predicciones y metadatos siempre se guardan.

# [Anotación · líneas 52–60] Celda de texto (continúa). Declara un máximo inicial de 45 entrenamientos (20 BO
#   + 5 OOF + 10 P2 + 10 P3), tiempos medidos en ejecuciones previas con otros hiperparámetros y una previsión
#   de 12 a 16 horas con 10 semillas. Cita referencias de mlr3mbo y de GCS.
## Costo orientativo y validación del entregable

El máximo inicial es **45 entrenamientos: 20 BO + 5 OOF + 10 P2 + 10 P3**. En las salidas adjuntas la BO original acumuló 194,4 minutos para 14 evaluaciones (0,6–23,8 min cada una); P2 rondó 17,2–18,4 min/semilla y P3 30,1–35,4. Son mediciones de otros HP y entorno, no promesas para esta corrida.

Con 10 semillas, producción sola ≈8–9 h; sumar BO, cinco OOF, preparación, escrituras y GCS. Una previsión práctica de **12–16 h** tiene incertidumbre; recalibrar con los tiempos guardados de las primeras evaluaciones. Veinte semillas por familia pueden llevar el total a ≈20–25 h; cincuenta probablemente excedan el cierre. No se estima dinero sin la tarifa de la VM. P2 tiene prioridad y los presupuestos evitan exigir 20 evaluaciones para obtener una producción útil.

La auditoría realizada y sus límites se registran al final del notebook. Ningún entrenamiento sobre el dataset de la competencia se ejecutó durante la construcción del entregable.

Referencias técnicas de implementación: [bucle EGO de mlr3mbo](https://mlr3mbo.mlr-org.com/reference/mlr_loop_functions_ego.html), [metadatos de objetos GCS](https://docs.cloud.google.com/sdk/gcloud/reference/storage/objects/describe), [precondiciones de escritura GCS](https://docs.cloud.google.com/storage/docs/request-preconditions). La metodología y los parámetros proceden de los notebooks adjuntos y la consigna.

# [Anotación · líneas 62–91] Define la carpeta raíz (variable de entorno SAFE_ROOT; por defecto /home/ds/Expe
#   si existe, si no ~/Expe), el experimento SAFE_P2_P3_FINAL_HNC5_V1, la URL del dataset crudo y los
#   interruptores de la corrida: producir_P2=TRUE, producir_P3=FALSE, n_semillas=10, bo_horas=8,
#   solo_ensembles=FALSE, guardar_modelos=FALSE, respaldo_GCS=FALSE, sin límite horario (limite_ART=NA) y margen
#   de 30 minutos. La salida guardada de esta celda en el .ipynb muestra P3=TRUE y GCS obligatorio=TRUE.
#%% celda 2 [código]
# BLOQUE 1 — Configuración y bibliotecas #####
options(repos=c(CRAN="https://cloud.r-project.org"), warn=1, timeout=1800)

ROOT <- Sys.getenv("SAFE_ROOT", unset=if (dir.exists("/home/ds"))
  "/home/ds/Expe" else file.path(path.expand("~"), "Expe"))
EXPERIMENTO <- "SAFE_P2_P3_FINAL_HNC5_V1"
OUT <- file.path(ROOT, "experimentos", EXPERIMENTO)
crudo_oficial <- file.path(OUT, "fuentes", "competencia_01_crudo.csv")
url_oficial <- "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"

producir_P2 <- TRUE
producir_P3 <- FALSE
n_semillas <- 10L                       # 10, 20 o 50; conserva las ya terminadas
bo_horas <- 8                           # presupuesto activo ACUMULADO; máximo 20 evaluaciones
solo_ensembles <- FALSE                 # TRUE: exporta lo disponible, sin nuevos entrenamientos
guardar_modelos <- FALSE                # opcional; predicciones y metadatos se guardan siempre

# En esta VM es obligatorio. Para reproducir fuera del entorno: respaldo_GCS <- FALSE.
respaldo_GCS <- FALSE
GCS <- Sys.getenv("SAFE_FINAL_GCS", unset=paste0(
  "gs://pabloparisidat_buckito2026/Expe/experimentos/", EXPERIMENTO))

# No se inicia un trabajo después de este límite. No interrumpe un modelo a mitad.
# Para reproducir después de la competencia: limite_ART <- NA_character_.
limite_ART <- NA_character_
margen_minutos <- 30                    # reserva para terminar / exportar / subir submission
limite <- if (is.na(limite_ART)) as.POSIXct(NA) else
  as.POSIXct(limite_ART, tz="America/Argentina/Buenos_Aires") - margen_minutos*60

# [Anotación · líneas 92–107] Comprueba que n_semillas sea 10, 20 o 50, crea las carpetas de salida y una
#   biblioteca local R_libs, instala los paquetes que falten de una lista de 11 (data.table, lightgbm,
#   DiceKriging, mlr3, mlr3mbo, mlr3learners, paradox, bbotk, lhs, jsonlite, rgenoud) y carga los que usa.
stopifnot(n_semillas %in% c(10L,20L,50L), length(bo_horas)==1L,
          !is.na(bo_horas), bo_horas >= 0, margen_minutos >= 0)
dir.create(OUT, recursive=TRUE, showWarnings=FALSE)
dir.create(file.path(ROOT,"R_libs"), recursive=TRUE, showWarnings=FALSE)
.libPaths(c(file.path(ROOT,"R_libs"), .libPaths()))
paquetes <- c("data.table","lightgbm","DiceKriging","mlr3","mlr3mbo",
              "mlr3learners","paradox","bbotk","lhs","jsonlite","rgenoud")
faltan <- paquetes[!vapply(paquetes, requireNamespace, logical(1), quietly=TRUE)]
if (length(faltan)) install.packages(faltan, lib=.libPaths()[1], Ncpus=2L)
faltan <- paquetes[!vapply(paquetes, requireNamespace, logical(1), quietly=TRUE)]
if (length(faltan)) stop("Faltan paquetes: ", paste(faltan, collapse=", "))
suppressPackageStartupMessages({
  library(data.table); library(lightgbm); library(DiceKriging)
  library(mlr3); library(mlr3mbo); library(mlr3learners)
  library(paradox); library(bbotk)
})

# [Anotación · líneas 109–117] Escribe las 10 semillas base y arma una secuencia de 50: fija set.seed(727777)
#   con L'Ecuyer-CMRG, sortea 100 enteros entre 1 y 1.000.000.000 y agrega los primeros 40 que no repiten las 10
#   base.
# Exactamente las diez semillas presentes en las referencias, en su orden original.
semillas_originales <- c(727777L,773777L,775777L,777737L,787777L,
                        777727L,777773L,777775L,777787L,797777L)
# Las referencias NO especifican semillas 11–50. Extensión operativa explícita,
# independiente del RNG de BO/OOF; se congela íntegra desde la primera ejecución.
set.seed(727777L, kind="L'Ecuyer-CMRG", normal.kind="Inversion", sample.kind="Rejection")
semillas_50 <- c(semillas_originales,
  head(setdiff(sample.int(1000000000L, 100L), semillas_originales), 40L))
stopifnot(length(semillas_50)==50L, !anyDuplicated(semillas_50))

# [Anotación · líneas 119–135] Lista PARAM con los parámetros de la corrida: la BO entrena en 202103 y 202104
#   y valida en 202106; meses que se preparan (202103 a 202106 y 202108); entrenamiento final P2 = 202105 y
#   202106, P3 = 202103 a 202106; predicción en 202108; semilla 727777 para BO y OOF; 20 evaluaciones como
#   máximo, 5 folds, HNC de 5%; variables excluidas (cprestamos_personales, mprestamos_personales); cortes de
#   9.500 a 15.000 de a 500; GainBand de 11.500 a 15.000; ganancia de 1.072.500 por BAJA+2 y costo de 27.500;
#   nombres de metadatos y expresión regular de fechas.
PARAM <- list(
  version="SAFE_P2_P3_FINAL_HNC5_V1_20261011",
  BO_train=c(202103L,202104L), BO_valid=202106L,
  meses_cache=c(202103L,202104L,202105L,202106L,202108L),
  P_final=list(P2=c(202105L,202106L), P3=c(202103L,202104L,202105L,202106L)),
  mes_score=202108L, seed_BO=727777L, seed_OOF=727777L,
  n_iniciales=10L, n_EI=10L, n_total=20L, n_folds=5L, hnc_pct=5,
  excluidas=c("cprestamos_personales","mprestamos_personales"),
  cortes=seq(9500L,15000L,500L), gainband=seq(11500L,15000L,500L),
  ganancia_baja2=1072500, costo_estimulo=27500,
  semillas=semillas_50,
  space=list(num_iterations=c(64L,4096L), num_leaves=c(16L,2048L),
             min_sum_hessian_in_leaf=c(1e-6,0.1)),
  metadata=c("numero_de_cliente","foto_mes","clase_ternaria","clase01",
             "binaria2","target","azar","training","fold"),
  fechas="fecha|fvencimiento|finiciomora|fechaalta|fultimo|ultimo_cierre"
)
# [Anotación · líneas 136–146] Parámetros fijos de LightGBM: gbdt, objetivo binario, métrica auc,
#   learning_rate=0,005, feature_fraction=0,50, feature_fraction_bynode=0,20, min_data_in_leaf=0, max_bin=31,
#   max_depth=-1, lambda_l1=0, lambda_l2=0, bagging_fraction=1, early_stopping=0, deterministic=TRUE y
#   force_row_wise=TRUE.
PARAM$lgbm_fijos <- list(
  boosting="gbdt", objective="binary", metric="auc", feature_pre_filter=FALSE,
  first_metric_only=FALSE, boost_from_average=TRUE, force_row_wise=TRUE,
  use_missing=TRUE, zero_as_missing=FALSE, deterministic=TRUE, verbosity=-100,
  max_depth=-1L, min_gain_to_split=0, lambda_l1=0.0, lambda_l2=0.0,
  bagging_fraction=1.0, pos_bagging_fraction=1.0, neg_bagging_fraction=1.0,
  is_unbalance=FALSE, scale_pos_weight=1.0, drop_rate=0.1, max_drop=50,
  skip_drop=0.5, extra_trees=FALSE, early_stopping=0,
  learning_rate=0.005, feature_fraction=0.50, feature_fraction_bynode=0.20,
  min_data_in_leaf=0L, max_bin=31L
)
# [Anotación · líneas 147–157] Registra la versión de R, la de cada paquete de la lista y la de sus
#   dependencias instaladas, define hay_tiempo() (verdadero si no hay límite o todavía no se alcanzó) e imprime
#   la configuración.
versiones <- c(R=as.character(getRversion()),
  vapply(paquetes, function(p) as.character(packageVersion(p)), character(1)))
# Lista estable: no depende de qué celdas se ejecutaron antes en este kernel.
dependencias <- sort(unique(c(paquetes,unlist(tools::package_dependencies(
  paquetes,db=installed.packages(),which=c("Depends","Imports","LinkingTo"),recursive=TRUE)))))
dependencias <- setdiff(dependencias,"R")
versiones_dependencias <- vapply(dependencias,
  function(p) as.character(packageVersion(p)), character(1))
hay_tiempo <- function() is.na(limite) || Sys.time() < limite
message("Salida: ", OUT, " | GCS obligatorio: ", respaldo_GCS,
        " | P2=", producir_P2, " | P3=", producir_P3, " | semillas=", n_semillas)

# [Anotación · líneas 159–197] Funciones de escritura: md5 de un archivo, firma() (MD5 de un objeto
#   serializado), rds_atomico() y csv_atomico(), que escriben en un archivo temporal, lo releen para comparar
#   dimensiones, columnas, NA y valores y recién entonces lo renombran. Calcula CONFIG_ID como firma de PARAM y
#   de las versiones, y detiene la ejecución si respaldo_GCS está activo y no hay gcloud o un prefijo gs://.
#%% celda 3 [código]
# BLOQUE 2 — Escritura atómica y checkpoints confirmados en GCS #####
md5 <- function(f) unname(tools::md5sum(f))
firma <- function(x) {
  f <- tempfile(); on.exit(unlink(f), add=TRUE)
  saveRDS(x, f, compress=FALSE, version=3)
  md5(f)
}
rds_atomico <- function(x, f) {
  dir.create(dirname(f), recursive=TRUE, showWarnings=FALSE)
  t <- paste0(f,".tmp_",Sys.getpid()); on.exit(unlink(t), add=TRUE)
  saveRDS(x, t, compress="gzip", version=3)
  invisible(readRDS(t))
  if (!file.rename(t,f)) stop("No se pudo promover: ", f)
  invisible(f)
}
csv_atomico <- function(x, f, encabezado=TRUE) {
  dir.create(dirname(f), recursive=TRUE, showWarnings=FALSE)
  t <- paste0(f,".tmp_",Sys.getpid()); on.exit(unlink(t), add=TRUE)
  fwrite(x, t, col.names=encabezado, na="NA")
  z <- fread(t, header=encabezado, na.strings=c("","NA"), showProgress=FALSE)
  if (!identical(dim(z),dim(x))) stop("CSV cambió dimensiones: ", f)
  if (encabezado && !identical(names(z),names(x))) stop("CSV cambió columnas: ",f)
  for (j in seq_along(x)) {
    if (!identical(is.na(z[[j]]),is.na(x[[j]]))) stop("CSV cambió NA: ",f)
    ok <- if (is.numeric(x[[j]])) isTRUE(all.equal(as.numeric(z[[j]]),
      as.numeric(x[[j]]), tolerance=1e-12, check.attributes=FALSE)) else
      identical(as.character(z[[j]]),as.character(x[[j]]))
    if (!ok) stop("CSV cambió valores: ",f)
  }
  if (!file.rename(t,f)) stop("No se pudo promover CSV: ",f)
  invisible(f)
}
CONFIG_ID <- firma(list(PARAM=PARAM, versiones=versiones,
                       versiones_dependencias=versiones_dependencias))
GCS <- sub("/+$", "", GCS)
gcloud <- unname(Sys.which("gcloud"))
if (respaldo_GCS && (!nzchar(gcloud) || !grepl("^gs://[^/]+/.+",GCS)))
  stop("Configurar gcloud y GCS con un prefijo propio, o desactivar GCS fuera de esta VM.")

# [Anotación · líneas 199–246] Funciones para Google Cloud Storage a través del comando gcloud: ejecutar un
#   comando distinguiendo un objeto ausente de otros errores, consultar metadatos, convertir un MD5 a base64,
#   comparar MD5 y tamaño remoto con el archivo local, subir sólo si el objeto no existe y descargar a un
#   temporal verificando el contenido antes de dejarlo en su lugar.
gcs_comando <- function(args, permitir_ausente=FALSE) {
  err <- tempfile(); on.exit(unlink(err), add=TRUE)
  out <- suppressWarnings(system2(gcloud, vapply(c(args,"--quiet"),shQuote,character(1)),
                                  stdout=TRUE, stderr=err))
  status <- attr(out,"status")
  if (!is.null(status) && status!=0L) {
    detalle <- paste(readLines(err,warn=FALSE),collapse="\n")
    # Sólo una ausencia inequívoca es un experimento/objeto nuevo. 403/red NO lo son.
    if (permitir_ausente && grepl("(?i)(404|not found|no such object|matched no objects|no urls matched|does not exist)",
                                 detalle,perl=TRUE) &&
        !grepl("(?i)(403|permission|forbidden|access denied)",detalle,perl=TRUE)) return(NULL)
    stop("GCS falló; no se inicia el siguiente trabajo. ", detalle)
  }
  out
}
gcs_info <- function(uri) {
  z <- gcs_comando(c("storage","objects","describe",uri,"--raw","--format=json"),TRUE)
  if (is.null(z)) return(NULL)
  jsonlite::fromJSON(paste(z,collapse="\n"))
}
md5_base64 <- function(h) jsonlite::base64_enc(as.raw(strtoi(
  substring(h,seq(1,31,2),seq(2,32,2)),16L)))
verificar_remoto <- function(info, f) {
  !is.null(info) && identical(info$md5Hash,md5_base64(md5(f))) &&
    isTRUE(as.numeric(info$size)==file.info(f)$size)
}
subir_inmutable <- function(f, uri) {
  info <- gcs_info(uri)
  if (is.null(info)) {
    gcs_comando(c("storage","cp",f,uri,"--if-generation-match=0",
                  paste0("--content-md5=",md5_base64(md5(f)))))
    info <- gcs_info(uri)
  }
  if (!verificar_remoto(info,f)) stop("Objeto remoto diferente o sin MD5 verificable: ",uri)
  invisible(TRUE)
}
descargar_verificado <- function(uri, f, hash=NULL) {
  info <- gcs_info(uri)
  if (is.null(info)) stop("Falta un objeto de un checkpoint confirmado: ",uri)
  dir.create(dirname(f),recursive=TRUE,showWarnings=FALSE)
  t <- paste0(f,".download_",Sys.getpid()); on.exit(unlink(t),add=TRUE)
  gcs_comando(c("storage","cp",uri,t))
  if (!verificar_remoto(info,t) || (!is.null(hash) && md5(t)!=hash))
    stop("Descarga no verificable: ",uri)
  if (file.exists(f) && md5(f)!=md5(t)) stop("Conflicto local, no se sobrescribe: ",f)
  if (!file.exists(f) && !file.rename(t,f)) stop("No se pudo recuperar: ",f)
  invisible(f)
}
# [Anotación · líneas 247–273] Define la ruta local y remota de cada checkpoint, valida el contenido de un
#   COMMIT (clave, CONFIG_ID, firma y lista de archivos con MD5) y respaldar(), que sube cada archivo y al final
#   el COMMIT; con respaldo_GCS=FALSE no hace nada.
ck_dir <- function(key) file.path(OUT,"checkpoints",key)
ck_uri <- function(key) paste0(GCS,"/checkpoints/",key,".rds")
confirmados_sesion <- new.env(parent=emptyenv())
clave_confirmacion <- function(key) paste(GCS,CONFIG_ID,key,sep="|")

validar_commit <- function(z,key,sig=NULL) {
  if (!is.list(z) || !identical(z$key,key) || !identical(z$config_id,CONFIG_ID) ||
      (!is.null(sig) && !identical(z$firma,sig)))
    stop("Checkpoint de otro experimento/configuración: ",key)
  a <- z$archivos
  if (!nrow(a) || anyDuplicated(a$archivo) || anyNA(a) ||
      any(basename(a$archivo)!=a$archivo) || any(!grepl("^[a-f0-9]{32}$",a$md5)))
    stop("Manifiesto de archivos inválido: ",key)
  invisible(TRUE)
}
respaldar <- function(key,z) {
  if (!respaldo_GCS) return(invisible(TRUE))
  for (i in seq_len(nrow(z$archivos))) {
    a <- z$archivos[i,]
    subir_inmutable(file.path(ck_dir(key),a$archivo),paste0(GCS,"/objetos/",a$md5,"/",a$archivo))
  }
  # El commit remoto se publica ÚLTIMO. Sólo él declara terminado el trabajo.
  subir_inmutable(file.path(ck_dir(key),"COMMIT.rds"),ck_uri(key))
  assign(clave_confirmacion(key),md5(file.path(ck_dir(key),"COMMIT.rds")),
         envir=confirmados_sesion)
  invisible(TRUE)
}
# [Anotación · líneas 274–320] abrir_checkpoint() devuelve NULL si no hay COMMIT local (ni remoto recuperable)
#   y, si lo hay, comprueba firma, MD5 y tamaño de cada archivo. iniciar_checkpoint() no pisa un checkpoint
#   cerrado y aparta con otro nombre la carpeta de un intento incompleto. cerrar_checkpoint() arma la lista de
#   archivos con MD5 y bytes, escribe COMMIT.rds y llama al respaldo.
abrir_checkpoint <- function(key,sig=NULL,remoto=TRUE) {
  d <- ck_dir(key); f <- file.path(d,"COMMIT.rds")
  confirmado <- file.exists(f) && exists(clave_confirmacion(key),envir=confirmados_sesion,inherits=FALSE) &&
    identical(get(clave_confirmacion(key),envir=confirmados_sesion),md5(f))
  info <- if (respaldo_GCS && remoto && !confirmado) gcs_info(ck_uri(key)) else NULL
  if (!file.exists(f) && !is.null(info)) {
    descargar_verificado(ck_uri(key),f)
    message("Recuperado desde GCS: ",key)
  }
  if (!file.exists(f)) return(NULL)
  z <- readRDS(f); validar_commit(z,key,sig)
  if (!is.null(info) && !verificar_remoto(info,f)) stop("Conflicto de commits: ",key)
  for (i in seq_len(nrow(z$archivos))) {
    a <- z$archivos[i,]; p <- file.path(d,a$archivo)
    if (!file.exists(p) && respaldo_GCS && remoto)
      descargar_verificado(paste0(GCS,"/objetos/",a$md5,"/",a$archivo),p,a$md5)
    if (!file.exists(p) || md5(p)!=a$md5 || file.info(p)$size!=a$bytes)
      stop("Checkpoint corrupto/incompleto: ",key," / ",a$archivo)
  }
  # Si el backup falló luego del commit local, ahora se completa sin reentrenar.
  if (remoto && !confirmado) respaldar(key,z)
  z
}
iniciar_checkpoint <- function(key) {
  d <- ck_dir(key)
  if (file.exists(file.path(d,"COMMIT.rds"))) stop("No sobrescribir checkpoint: ",key)
  if (dir.exists(d) && length(list.files(d,all.files=TRUE,no..=TRUE))) {
    destino <- paste0(d,"_incompleto_",format(Sys.time(),"%Y%m%d%H%M%OS6"),"_",Sys.getpid())
    if (!file.rename(d,destino)) stop("No se pudo apartar intento incompleto: ",d)
    message("Intento interrumpido conservado: ",destino)
  }
  dir.create(d,recursive=TRUE,showWarnings=FALSE)
  d
}
cerrar_checkpoint <- function(key,sig,remoto=TRUE) {
  d <- ck_dir(key)
  fs <- list.files(d,full.names=TRUE)
  fs <- fs[!grepl("COMMIT\\.rds$|\\.tmp_|\\.download_",fs)]
  stopifnot(length(fs)>0L, !any(file.info(fs)$isdir))
  z <- list(key=key, config_id=CONFIG_ID, firma=sig,
    archivos=data.frame(archivo=basename(fs),md5=unname(tools::md5sum(fs)),
                         bytes=unname(file.info(fs)$size),stringsAsFactors=FALSE))
  validar_commit(z,key,sig)
  rds_atomico(z,file.path(d,"COMMIT.rds"))
  if (remoto) respaldar(key,z)             # ERROR de GCS se propaga; nunca un mero warning
  invisible(z)
}
# [Anotación · líneas 321–333] Si el respaldo está activo consulta el bucket. Si no existe el checkpoint
#   config/base lo crea con config.rds (PARAM y versiones), sessionInfo.txt y semillas.csv (las 50 semillas con
#   su orden y origen).
if (respaldo_GCS) {
  bucket <- sub("^(gs://[^/]+).*", "\\1",GCS)
  invisible(gcs_comando(c("storage","buckets","describe",bucket,"--format=json")))
}
if (is.null(abrir_checkpoint("config/base",CONFIG_ID))) {
  d <- iniciar_checkpoint("config/base")
  rds_atomico(list(PARAM=PARAM,versiones=versiones,dependencias=versiones_dependencias,
                   config_id=CONFIG_ID),file.path(d,"config.rds"))
  writeLines(capture.output(sessionInfo()),file.path(d,"sessionInfo.txt"))
  csv_atomico(data.table(orden=seq_along(semillas_50),seed=semillas_50,
    origen=c(rep("SAFE_original",10),rep("extension_determinista",40))),file.path(d,"semillas.csv"))
  cerrar_checkpoint("config/base",CONFIG_ID)
}

# [Anotación · líneas 335–359] generar_targets(): convierte foto_mes en un número de período, ordena por
#   cliente y período y toma los dos períodos siguientes de cada cliente. Asigna CONTINUA a los meses anteriores
#   al anteúltimo, BAJA+1 si el cliente no aparece el mes siguiente y BAJA+2 si aparece el mes siguiente pero no
#   el posterior; el último mes queda en NA. Crea binaria2 = 1 para BAJA+1 o BAJA+2, 0 para CONTINUA y NA cuando
#   no hay clase.
#%% celda 4 [código]
# BLOQUE 3 — Targets, ranks, métricas y entrenamiento SAFE #####
generar_targets <- function(dataset) {
  if (anyNA(dataset$numero_de_cliente) || anyNA(dataset$foto_mes) ||
      anyDuplicated(dataset,by=c("numero_de_cliente","foto_mes")))
    stop("Crudo: IDs/meses faltantes o duplicados cliente-mes.")
  dsimple <- dataset[,.(pos=.I,numero_de_cliente,
    periodo0=as.integer(foto_mes/100)*12L + foto_mes%%100L)]
  setorder(dsimple,numero_de_cliente,periodo0)
  periodo_ultimo <- max(dsimple$periodo0)
  periodo_anteultimo <- periodo_ultimo - 1L
  dsimple[,c("periodo1","periodo2") := shift(periodo0,n=1:2,fill=NA,type="lead"),
          by=numero_de_cliente]
  dsimple[,clase_ternaria := NA_character_]
  dsimple[periodo0 < periodo_anteultimo,clase_ternaria := "CONTINUA"]
  dsimple[periodo0 < periodo_ultimo & (is.na(periodo1) | periodo0+1L < periodo1),
          clase_ternaria := "BAJA+1"]
  dsimple[periodo0 < periodo_anteultimo & periodo0+1L==periodo1 &
          (is.na(periodo2) | periodo0+2L < periodo2),clase_ternaria := "BAJA+2"]
  setorder(dsimple,pos)
  dataset[,clase_ternaria := dsimple$clase_ternaria]
  dataset[,binaria2 := fifelse(is.na(clase_ternaria),NA_integer_,
    as.integer(clase_ternaria %in% c("BAJA+1","BAJA+2")))]
  dataset
}
# [Anotación · líneas 360–373] signed_rank(): rank con signo de un vector. Los negativos reciben menos el rank
#   de su valor absoluto dividido por la cantidad de negativos, los ceros quedan en 0, los positivos reciben su
#   rank dividido por la cantidad de positivos (empates promedio) y los NA se conservan. mes_anterior() devuelve
#   el mes calendario k meses antes de un AAAAMM.
signed_rank <- function(x) {
  z <- rep(NA_real_,length(x))
  neg <- !is.na(x) & x < 0
  cer <- !is.na(x) & x == 0
  pos <- !is.na(x) & x > 0
  if (any(neg)) z[neg] <- -frank(abs(x[neg]),ties.method="average")/sum(neg)
  z[cer] <- 0
  if (any(pos)) z[pos] <- frank(x[pos],ties.method="average")/sum(pos)
  z
}
mes_anterior <- function(ym,k) {
  total <- (ym%/%100L)*12L + ym%%100L - 1L - as.integer(k)
  as.integer((total%/%12L)*100L + total%%12L + 1L)
}
# [Anotación · líneas 374–395] Validaciones que detienen la ejecución: probabilidades completas, finitas y
#   entre 0 y 1; IDs sin NA ni duplicados y en el mismo orden que una referencia; clase ternaria y binaria2
#   coherentes entre sí, y 202108 sin clase.
validar_prob <- function(p,n=length(p)) {
  if (length(p)!=n || anyNA(p) || any(!is.finite(p)) || any(p<0 | p>1))
    stop("Predicciones incompletas/no finitas/fuera de [0,1].")
  invisible(TRUE)
}
validar_ids <- function(ids,referencia) {
  if (anyNA(ids) || anyDuplicated(ids) ||
      !identical(as.character(ids),as.character(referencia)))
    stop("IDs/orden diferentes del universo de referencia.")
  invisible(TRUE)
}
validar_target <- function(d,etiquetado=TRUE) {
  if (!identical(is.na(d$clase_ternaria),is.na(d$binaria2)) ||
      any(!is.na(d$clase_ternaria) & !d$clase_ternaria %in% c("CONTINUA","BAJA+1","BAJA+2")))
    stop("Target desconocido o máscara NA alterada.")
  if (etiquetado && (anyNA(d$binaria2) ||
      any(d$binaria2!=as.integer(d$clase_ternaria %in% c("BAJA+1","BAJA+2")))))
    stop("Target binaria2 incorrecto.")
  if (!etiquetado && (!all(is.na(d$clase_ternaria)) || !all(is.na(d$binaria2))))
    stop("Agosto debe carecer de etiquetas y target.")
  invisible(TRUE)
}
# [Anotación · líneas 396–412] auc_binaria() calcula el AUC con la suma de ranks de los positivos.
#   curva_ganancia() ordena por probabilidad descendente (empates por numero_de_cliente) y acumula +1.072.500
#   por cada BAJA+2 y −27.500 por cada otra fila, junto con las BAJA+2 acumuladas en cada posición.
auc_binaria <- function(y,p) {
  validar_prob(p,length(y))
  if (anyNA(y) || any(!y %in% 0:1)) stop("AUC: target inválido.")
  n1 <- sum(y==1L); n0 <- sum(y==0L)
  if (!n1 || !n0) stop("AUC requiere las dos clases.")
  (sum(rank(p,ties.method="average")[y==1L])-n1*(n1+1)/2)/(n1*n0)
}
curva_ganancia <- function(d,p) {
  validar_prob(p,nrow(d))
  x <- d[,.(numero_de_cliente,clase_ternaria)]
  x[,prediction := p]
  setorder(x,-prediction,numero_de_cliente)
  x[,baja2 := as.integer(clase_ternaria=="BAJA+2")]
  x[,.(cutoff=seq_len(.N),numero_de_cliente,prediction,
    bajas2_acumuladas=cumsum(baja2),
    ganancia_acumulada=cumsum(fifelse(baja2==1L,PARAM$ganancia_baja2,-PARAM$costo_estimulo)))]
}
# [Anotación · líneas 413–427] Nombra los tres hiperparámetros que se buscan (num_iterations, num_leaves,
#   min_sum_hessian_in_leaf), arma la lista de parámetros de un modelo sumando esos tres y la semilla a los
#   fijos, y matriz_SAFE() convierte las columnas de FEATURES a matriz numérica comprobando que no cambien los
#   NA.
hp_campos <- c("num_iterations","num_leaves","min_sum_hessian_in_leaf")
hp_lista <- function(hp) list(num_iterations=as.integer(hp$num_iterations),
  num_leaves=as.integer(hp$num_leaves),
  min_sum_hessian_in_leaf=as.numeric(hp$min_sum_hessian_in_leaf))
param_modelo <- function(hp,seed) modifyList(PARAM$lgbm_fijos,
  c(hp_lista(hp),list(seed=as.integer(seed))))
matriz_SAFE <- function(d) {
  x <- data.matrix(d[,..FEATURES])
  stopifnot(identical(colnames(x),FEATURES),nrow(x)==nrow(d))
  for (j in seq_along(FEATURES)) {
    if (!identical(is.na(x[,j]),is.na(d[[FEATURES[j]]])) ||
        any(!is.na(x[,j]) & !is.finite(x[,j]))) stop("Matriz alteró NA/valores: ",FEATURES[j])
  }
  x
}
# [Anotación · líneas 428–449] ajustar_SAFE(): crea el lgb.Dataset (max_bin=31), entrena con lgb.train sin
#   conjunto de validación ni early stopping (las líneas de valids están comentadas), predice sobre la matriz de
#   puntuación, valida las probabilidades y, si se pide, guarda el modelo. Devuelve las probabilidades y los
#   tiempos de entrenamiento y predicción.
# Todas las etapas llaman a esta misma función con el MISMO manifiesto y parámetros fijos.
ajustar_SAFE <- function(X,y,Xscore,hp,seed,valid_y=NULL,modelo_archivo=NULL) {
  stopifnot(identical(colnames(X),FEATURES),identical(colnames(Xscore),FEATURES),
            ncol(X)==length(FEATURES),!anyNA(y),all(y %in% 0:1))
  t0 <- proc.time()[["elapsed"]]
  dtrain <- lgb.Dataset(X,label=y,params=list(max_bin=31L,feature_pre_filter=FALSE,
                                            use_missing=TRUE,zero_as_missing=FALSE))
  #valids <- if (is.null(valid_y)) list() else list(val=lgb.Dataset(Xscore,label=valid_y,
   # params=list(max_bin=31L,feature_pre_filter=FALSE,use_missing=TRUE,zero_as_missing=FALSE)))
  model <- lgb.train(params=param_modelo(hp,seed),data=dtrain)
  t1 <- proc.time()[["elapsed"]]
  p <- as.numeric(predict(model,Xscore))
  validar_prob(p,nrow(Xscore))
  if (!is.null(modelo_archivo)) {
    t <- paste0(modelo_archivo,".tmp_",Sys.getpid())
    on.exit(unlink(t),add=TRUE)
    lgb.save(model,t)
    invisible(lgb.load(t))
    if (!file.rename(t,modelo_archivo)) stop("No se pudo guardar modelo.")
  }
  list(p=p,seg_entrenamiento=t1-t0,seg_prediccion=proc.time()[["elapsed"]]-t1)
}

# [Anotación · líneas 451–473] Pruebas con datos de ejemplo, sin entrenar: resultado de signed_rank sobre un
#   vector con NA, negativos, ceros y empates; mes_anterior en un cambio de año; clases de tres clientes
#   ficticios (uno con baja y uno con un mes faltante); y conservación de NA al escribir y releer un CSV.
#%% celda 5 [código]
# BLOQUE 3b — Comprobaciones pequeñas, sin entrenamientos #####
local({
  x <- c(NA_real_,-4,-1,-1,0,1,2,2)
  esperado <- c(NA_real_,-1,-0.5,-0.5,0,1/3,5/6,5/6)
  stopifnot(isTRUE(all.equal(signed_rank(x),esperado)),
            identical(is.na(signed_rank(x)),is.na(x)),
            mes_anterior(202101L,1L)==202012L,
            mes_anterior(202103L,2L)==202101L)
  ejemplo <- data.table(numero_de_cliente=c(rep(1L,6),rep(2L,3),rep(3L,4)),
    foto_mes=c(202103L:202108L,202103L:202105L,202103L,202105L,202106L,202108L))
  ejemplo <- generar_targets(ejemplo)
  stopifnot(ejemplo[numero_de_cliente==2L & foto_mes==202104L,clase_ternaria]=="BAJA+2",
            ejemplo[numero_de_cliente==2L & foto_mes==202105L,clase_ternaria]=="BAJA+1",
            ejemplo[numero_de_cliente==3L & foto_mes==202103L,clase_ternaria]=="BAJA+1",
            ejemplo[numero_de_cliente==1L & foto_mes==202106L,binaria2]==0L,
            all(is.na(ejemplo[foto_mes==202108L,binaria2])))
  z <- data.table(numero=c(NA_real_,0,0.125),texto=c(NA_character_,"a","b"))
  f <- tempfile(fileext=".csv"); on.exit(unlink(f),add=TRUE)
  csv_atomico(z,f)
  stopifnot(identical(is.na(fread(f,na.strings=c("","NA"))),is.na(z)))
  message("Pruebas pequeñas OK: targets, huecos de historia, signos, ceros y NA.")
})

# [Anotación · líneas 475–490] Descarga el crudo desde la URL a un archivo .descarga y lo renombra si no
#   estaba, calcula su MD5, lo lee con fread y comprueba que estén las columnas requeridas y que los meses sean
#   exactamente 202103 a 202108.
#%% celda 6 [código]
# BLOQUE 4 — Fuente oficial y targets de Pasquini #####
dir.create(dirname(crudo_oficial),recursive=TRUE,showWarnings=FALSE)
if (!file.exists(crudo_oficial)) {
  t <- paste0(crudo_oficial,".descarga")
  if (file.exists(t)) unlink(t)           # sólo la descarga incompleta de esta salida
  download.file(url_oficial,t,mode="wb",quiet=FALSE)
  if (!file.exists(t) || file.info(t)$size==0) stop("Descarga vacía.")
  if (!file.rename(t,crudo_oficial)) stop("No se pudo promover la descarga.")
}
raw_md5 <- md5(crudo_oficial)
dataset <- fread(crudo_oficial,na.strings=c("","NA"),showProgress=TRUE)
requeridas <- c("numero_de_cliente","foto_mes","ccajas_depositos",PARAM$excluidas)
if (length(setdiff(requeridas,names(dataset)))) stop("Fuente oficial: faltan columnas.")
if (!identical(sort(unique(dataset$foto_mes)),202103L:202108L))
  stop("Meses de la fuente distintos de marzo–agosto 2021.")

# [Anotación · líneas 492–509] Lee 5.000 filas para clasificar cada columna: metadato o clase, fecha (por
#   expresión regular sobre el nombre), predictor numérico o no numérica. CURRENT queda con los predictores
#   numéricos. Genera las clases sobre todo el dataset y valida 202103–202106 con clase y 202108 sin clase.
# Mismo criterio y orden de columnas que SAFE; muestra de 5.000 filas, explícitamente NA.
muestra <- fread(crudo_oficial,nrows=5000L,na.strings=c("","NA"),stringsAsFactors=TRUE)
fuentes <- data.table(variable=names(muestra),tipo=vapply(muestra,
  function(x) paste(class(x),collapse="/"),character(1)))
fuentes[,decision := vapply(variable,function(v) {
  if (v %in% PARAM$metadata || grepl("^clase",tolower(v))) return("METADATA_TARGET")
  if (grepl(PARAM$fechas,tolower(v),perl=TRUE)) return("FECHA_METADATA")
  if (is.numeric(muestra[[v]]) || is.integer(muestra[[v]]) || is.logical(muestra[[v]]))
    return("RANK_PREDICTOR")
  "NO_NUMERICA"
},character(1))]
CURRENT <- fuentes[decision=="RANK_PREDICTOR",variable]
stopifnot(length(CURRENT)>0L, all(PARAM$excluidas %in% CURRENT),
          !any(PARAM$metadata %in% CURRENT))
rm(muestra)
dataset <- generar_targets(dataset)       # el CSV crudo queda intacto
validar_target(dataset[foto_mes %in% 202103L:202106L])
validar_target(dataset[foto_mes==202108L],FALSE)

# [Anotación · líneas 511–533] Compara los conteos por mes y clase con una tabla de 15 valores escrita en el
#   código, define UNIVERSO como los 164.647 clientes de 202108, calcula DATA_ID y guarda el checkpoint
#   datos/referencia con la fuente, los conteos, las clases, el universo y la clasificación de columnas.
# Conteos publicados en la referencia V5.3; no se inventan ni se toman de caches privados.
conteos_pasquini <- data.table(
  foto_mes=c(rep(202103L:202106L,each=3),202107L,202107L,202108L),
  clase_ternaria=c(rep(c("BAJA+1","BAJA+2","CONTINUA"),4),NA_character_,"BAJA+1",NA_character_),
  N=c(1019L,960L,160921L,964L,1139L,161181L,1143L,870L,161755L,
      874L,1098L,162142L,163245L,1103L,164647L))
conteos <- dataset[,.N,by=.(foto_mes,clase_ternaria)]
setorderv(conteos,c("foto_mes","clase_ternaria"),na.last=TRUE)
setorderv(conteos_pasquini,c("foto_mes","clase_ternaria"),na.last=TRUE)
stopifnot(isTRUE(all.equal(as.data.frame(conteos),as.data.frame(conteos_pasquini),check.attributes=FALSE)))
UNIVERSO <- dataset[foto_mes==202108L,numero_de_cliente]
stopifnot(length(UNIVERSO)==164647L,!anyNA(UNIVERSO),!anyDuplicated(UNIVERSO))
DATA_ID <- firma(list(config=CONFIG_ID,raw_md5=raw_md5,CURRENT=CURRENT,
                     universo=as.character(UNIVERSO)))
if (is.null(abrir_checkpoint("datos/referencia",DATA_ID))) {
  d <- iniciar_checkpoint("datos/referencia")
  rds_atomico(list(url=url_oficial,raw_md5=raw_md5,data_id=DATA_ID),file.path(d,"fuente.rds"))
  csv_atomico(conteos,file.path(d,"conteos_mes_clase.csv"))
  csv_atomico(dataset[,.(numero_de_cliente,foto_mes,clase_ternaria,binaria2)],file.path(d,"targets.csv"))
  csv_atomico(data.table(numero_de_cliente=UNIVERSO),file.path(d,"universo_agosto.csv"))
  csv_atomico(fuentes,file.path(d,"fuentes_columnas.csv"))
  cerrar_checkpoint("datos/referencia",DATA_ID)
}

# [Anotación · líneas 535–541] Pasa ccajas_depositos a NA en 202105, antes de construir lags y deltas, y
#   comprueba que los demás meses no cambien. Imprime los conteos.
# Única corrección DQ. Se aplica en memoria ANTES de cualquier temporalización.
no_mayo <- dataset[foto_mes!=202105L,ccajas_depositos]
dataset[foto_mes==202105L,ccajas_depositos := NA_real_]
stopifnot(all(is.na(dataset[foto_mes==202105L,ccajas_depositos])),
          identical(no_mayo,dataset[foto_mes!=202105L,ccajas_depositos]))
rm(no_mayo)
print(conteos)

# [Anotación · líneas 543–549] Arma los nombres de las cinco versiones de cada variable (actual, lag1_,
#   delta1_, lag2_, delta2_) y les agrega el sufijo _rank_signed.
#%% celda 7 [código]
# BLOQUE 5 — RAW T2 → signed_rank mensual → exclusión → manifiesto congelado #####
prefijos <- c("","lag1_","delta1_","lag2_","delta2_")
bloques <- c("current","lag1","delta1","lag2","delta2")
RAW_T2 <- unlist(lapply(prefijos,function(p) paste0(p,CURRENT)),use.names=FALSE)
RANK_T2 <- paste0(RAW_T2,"_rank_signed")
stopifnot(!anyDuplicated(RANK_T2))

# [Anotación · líneas 551–586] construir_mes(): para un mes toma las filas de ese mes y las de uno y dos meses
#   calendario antes, emparejadas por numero_de_cliente. Para cada variable calcula el valor actual, el de un
#   mes atrás, la diferencia con él, el de dos meses atrás y la diferencia con él; a cada una de las cinco le
#   aplica signed_rank dentro del mes y comprueba rango, signos, ceros y NA. Registra por variable la cantidad
#   de NA, de ceros y de clientes sin historia.
construir_mes <- function(origen,m,current=CURRENT) {
  actual <- origen[foto_mes==m]
  anterior1 <- origen[foto_mes==mes_anterior(m,1L)]
  anterior2 <- origen[foto_mes==mes_anterior(m,2L)]
  i1 <- match(actual$numero_de_cliente,anterior1$numero_de_cliente)
  i2 <- match(actual$numero_de_cliente,anterior2$numero_de_cliente)
  d <- actual[,.(numero_de_cliente,foto_mes,clase_ternaria,binaria2)]
  auditoria <- vector("list",length(current)*5L); k <- 0L
  # Se construyen las cinco versiones RAW de cada variable antes de rankearlas.
  # El orden final es por bloques, exactamente el de SAFE, no por variable.
  for (v in current) {
    x0 <- as.numeric(actual[[v]])
    x1 <- as.numeric(anterior1[[v]][i1])
    x2 <- as.numeric(anterior2[[v]][i2])
    raw <- list(x0,x1,x0-x1,x2,x0-x2)
    for (j in seq_along(raw)) {
      x <- raw[[j]]; z <- signed_rank(x)
      if (any(!is.na(x) & !is.finite(x)) || !identical(is.na(x),is.na(z)) ||
          any(z[!is.na(z)] < -1 | z[!is.na(z)] > 1) ||
          any(z[!is.na(x) & x==0]!=0) ||
          any(sign(z[!is.na(x)])!=sign(x[!is.na(x)])))
        stop("Rank/máscara/signos incorrectos en ",m," / ",v)
      nombre <- paste0(prefijos[j],v,"_rank_signed")
      set(d,j=nombre,value=z)
      k <- k+1L
      auditoria[[k]] <- data.table(foto_mes=m,feature=nombre,n_na=sum(is.na(x)),
        n_ceros=sum(x==0,na.rm=TRUE),sin_historia=if(j %in% c(2L,3L)) sum(is.na(i1)) else
          if(j %in% c(4L,5L)) sum(is.na(i2)) else 0L)
    }
  }
  nombres <- paste0(unlist(lapply(prefijos,function(p) paste0(p,current)),use.names=FALSE),"_rank_signed")
  setcolorder(d,c("numero_de_cliente","foto_mes","clase_ternaria","binaria2",nombres))
  validar_ids(d$numero_de_cliente,actual$numero_de_cliente)
  validar_target(d,m!=202108L)
  list(data=d,auditoria=rbindlist(auditoria))
}
# [Anotación · líneas 587–600] Para 202103, 202104, 202105, 202106 y 202108 construye el mes si no hay cache
#   local y guarda ranks.rds y auditoria_NA.csv en un checkpoint local (sin subir a GCS).
for (m in PARAM$meses_cache) {
  key <- paste0("cache/mes_",m)
  sig <- firma(list(data=DATA_ID,mes=m,rank=RANK_T2))
  if (is.null(abrir_checkpoint(key,sig,remoto=FALSE))) {
    message("Construyendo ranks: ",m)
    d <- iniciar_checkpoint(key)
    z <- construir_mes(dataset,m)
    rds_atomico(z$data,file.path(d,"ranks.rds"))
    csv_atomico(z$auditoria,file.path(d,"auditoria_NA.csv"))
    # Caches regenerables: locales. Todos los resultados costosos van a GCS.
    cerrar_checkpoint(key,sig,remoto=FALSE)
    rm(z); gc(verbose=FALSE)
  }
}

# [Anotación · líneas 602–623] Arma el manifiesto de variables: marca como no incluidas las cinco versiones de
#   cprestamos_personales y mprestamos_personales y deja FEATURES con el resto, en orden por bloque. Comprueba
#   la cantidad (5 × (fuentes − 2)) y guarda el checkpoint features/manifiesto con las variables finales, las
#   excluidas y las columnas descartadas antes.
# Los préstamos ya fueron temporalizados y rankeados sobre el mes COMPLETO.
# Ahora se excluyen únicamente del manifiesto que recibirá LightGBM.
manifiesto_total <- data.table(bloque=rep(bloques,each=length(CURRENT)),
  source_variable=rep(CURRENT,5L),source_feature=RAW_T2,model_feature=RANK_T2)
manifiesto_total[,incluida := !source_variable %in% PARAM$excluidas]
manifiesto <- manifiesto_total[incluida==TRUE]
manifiesto[,posicion := seq_len(.N)]
setcolorder(manifiesto,c("posicion","bloque","source_variable","source_feature","model_feature","incluida"))
FEATURES <- manifiesto$model_feature
FEATURE_ID <- firma(FEATURES)
stopifnot(length(FEATURES)==5L*(length(CURRENT)-2L),!anyDuplicated(FEATURES),
          all(grepl("_rank_signed$",FEATURES)),
          !any(grepl("(cprestamos_personales|mprestamos_personales)",FEATURES)))
PIPE_ID <- firma(list(data=DATA_ID,features=FEATURES))
if (is.null(abrir_checkpoint("features/manifiesto",PIPE_ID))) {
  d <- iniciar_checkpoint("features/manifiesto")
  csv_atomico(manifiesto,file.path(d,"features_finales.csv"))
  csv_atomico(manifiesto_total[incluida==FALSE],file.path(d,"prestamos_excluidos_RAW_y_RANK.csv"))
  csv_atomico(fuentes[decision!="RANK_PREDICTOR"],file.path(d,"otras_exclusiones.csv"))
  rds_atomico(list(FEATURES=FEATURES,feature_id=FEATURE_ID,pipe_id=PIPE_ID),file.path(d,"features.rds"))
  cerrar_checkpoint("features/manifiesto",PIPE_ID)
}
# [Anotación · líneas 624–640] cargar_mes() lee el cache de un mes, lo valida y devuelve las columnas de
#   identificación, clase y FEATURES; cargar_meses() apila varios meses. Libera el dataset crudo de memoria e
#   imprime la cantidad de variables por bloque (según la salida guardada: 144 fuentes, 142 por bloque, 710 en
#   total).
cargar_mes <- function(m) {
  key <- paste0("cache/mes_",m)
  sig <- firma(list(data=DATA_ID,mes=m,rank=RANK_T2))
  if (is.null(abrir_checkpoint(key,sig,remoto=FALSE))) stop("Falta cache: ",m)
  d <- readRDS(file.path(ck_dir(key),"ranks.rds"))
  stopifnot(identical(names(d)[-(1:4)],RANK_T2),all(d$foto_mes==m),
            !anyDuplicated(d$numero_de_cliente))
  validar_target(d,m!=202108L)
  if (m==202108L) validar_ids(d$numero_de_cliente,UNIVERSO)
  d[,c("numero_de_cliente","foto_mes","clase_ternaria","binaria2",FEATURES),with=FALSE]
}
cargar_meses <- function(meses) rbindlist(lapply(meses,cargar_mes),use.names=TRUE)
rm(dataset)
gc(verbose=FALSE)
message("Manifiesto congelado: ",length(FEATURES)," features; ",length(CURRENT),
        " fuentes rankeables antes de excluir préstamos.")
print(manifiesto[, .N,by=bloque])

# [Anotación · líneas 642–650] Espacio de búsqueda de la BO: num_iterations entero 64–4096, num_leaves entero
#   16–1024 y min_sum_hessian_in_leaf real 0,000001–0,1, en escala lineal. BO_ID firma el método con 6 puntos
#   iniciales, 14 de EI y semilla 727777.
#%% celda 8 [código]
# BLOQUE 6 — BO SAFE: Kriging + EI; 10 LHS + 10 EGO #####
dominio_BO <- function() ps(
  num_iterations=p_int(lower=64L,upper=4096L),
  num_leaves=p_int(lower=16L,upper=1024L),
  min_sum_hessian_in_leaf=p_dbl(lower=1e-6,upper=0.1)
)
BO_ID <- firma(list(  pipe=PIPE_ID,  metodo="REGR_KM_BFGS_EI_RANDOM1000_EGO",  iniciales=6L,  EI=14L,  seed=727777L,  escala="LINEAL",  max_hojas=1024L,  version="BO_NUEVA"))
BO_CTX <- new.env(parent=emptyenv())

# [Anotación · líneas 652–678] objetivo_BO(): entrena con los datos de entrenamiento de la BO y la semilla
#   727777, predice sobre 202106, calcula el AUC, la curva de ganancia y GainBand (promedio de la ganancia
#   acumulada en los cortes 11.500 a 15.000 de a 500), deja los resultados en BO_CTX, vuelve a fijar la semilla
#   y devuelve el AUC como métrica a maximizar.
# Función global: al serializar el motor NO se incrustan matrices de entrenamiento.
objetivo_BO <- function(xs) {
  hp <- hp_lista(xs)
  if (!identical(hp,BO_CTX$hp)) stop("La propuesta BO no coincide con el checkpoint pendiente.")
  t0 <- proc.time()[["elapsed"]]
  resultado <- ajustar_SAFE(BO_CTX$X,BO_CTX$y,BO_CTX$Xvalid,hp,PARAM$seed_BO,
                            valid_y=BO_CTX$valid$binaria2)
  pred <- copy(BO_CTX$valid)
  pred[,prediction := resultado$p]
  auc <- auc_binaria(pred$binaria2,pred$prediction)
  curva <- curva_ganancia(pred,pred$prediction)
  stopifnot(max(PARAM$gainband)<=nrow(curva),is.finite(auc))
  BO_CTX$resultado <- list(pred=pred,curva=curva,meta=data.table(
    eval_id=BO_CTX$eval_id,origen=BO_CTX$origen,
    num_iterations=hp$num_iterations,num_leaves=hp$num_leaves,
    min_sum_hessian_in_leaf=hp$min_sum_hessian_in_leaf,
    seed=PARAM$seed_BO,AUC=auc,
    GainBand_junio=mean(curva$ganancia_acumulada[PARAM$gainband]),
    contexto="VALIDACION_TEMPORAL_SIN_HNC",feature_id=FEATURE_ID,
    n_train=nrow(BO_CTX$X),n_valid=nrow(pred),
    seg_entrenamiento=resultado$seg_entrenamiento,seg_prediccion=resultado$seg_prediccion,
    seg_evaluacion=proc.time()[["elapsed"]]-t0-resultado$seg_entrenamiento,
    seg_total=proc.time()[["elapsed"]]-t0))
  # Reset presente en SAFE efectivamente ejecutado y en Pasquini.
  set.seed(PARAM$seed_BO,kind="L'Ecuyer-CMRG",normal.kind="Inversion",sample.kind="Rejection")
  list(metrica=auc)
}
# [Anotación · líneas 679–693] nuevo_motor_BO(): crea la instancia de bbotk con tope de 20 evaluaciones, el
#   surrogate Kriging (regr.km con BFGS y nugget estimado), la función de adquisición EI y su optimizador por
#   búsqueda al azar con 1.000 evaluaciones.
nuevo_motor_BO <- function(fun=objetivo_BO) {
  instancia <- OptimInstanceBatchSingleCrit$new(
    objective=ObjectiveRFun$new(fun=fun,domain=dominio_BO(),
      codomain=ps(metrica=p_dbl(tags="maximize")),id="BO_SAFE_FINAL"),
    terminator=trm("evals",n_evals=PARAM$n_total))
  surrogate <- srlrn(lrn("regr.km",optim.method="BFGS",nugget.estim=TRUE,
                         control=list(trace=FALSE)))
  acq <- acqf("ei")
  acqopt <- acqo(optimizer=opt("random_search",batch_size=1000),
                terminator=trm("evals",n_evals=1000))
  surrogate$archive <- instancia$archive
  acq$surrogate <- surrogate
  acqopt$acq_function <- acq
  list(instance=instancia,surrogate=surrogate,acq_function=acq,acq_optimizer=acqopt)
}
# [Anotación · líneas 694–722] proponer_EI() actualiza el surrogate y la adquisición y devuelve el siguiente
#   punto a evaluar. guardar_rng() y restaurar_rng() guardan y reponen el estado del generador aleatorio.
#   validar_estado_BO() comprueba que el estado guardado coincida con la historia (6 puntos LHS, AUC e
#   hiperparámetros de cada evaluación).
proponer_EI <- function(motor) {
  # Las mismas tres llamadas del cuerpo de bayesopt_ego(), separadas para poder
  # confirmar la propuesta ANTES de entrenar. No se cambia el optimizador de EI.
  motor$surrogate$archive <- motor$instance$archive
  motor$acq_function$surrogate <- motor$surrogate
  motor$acq_optimizer$acq_function <- motor$acq_function
  motor$surrogate$update()
  motor$acq_function$update()
  x <- motor$acq_optimizer$optimize()
  as.data.table(x)[,..hp_campos]
}
guardar_rng <- function() list(kind=RNGkind(),seed=get(".Random.seed",envir=.GlobalEnv))
restaurar_rng <- function(rng) {
  do.call(RNGkind,as.list(rng$kind))
  assign(".Random.seed",rng$seed,envir=.GlobalEnv)
}
validar_estado_BO <- function(z,n) {
  stopifnot(identical(z$bo_id,BO_ID),nrow(z$historia)==n,
            z$motor$instance$archive$n_evals==n,
            nrow(z$lhs)==6L,identical(names(z$lhs),hp_campos))
  if (n) {
    stopifnot(identical(as.integer(z$historia$eval_id),seq_len(n)))
    ar <- z$motor$instance$archive$data
    stopifnot(isTRUE(all.equal(ar$metrica,z$historia$AUC,tolerance=1e-14)))
    for (v in hp_campos) stopifnot(isTRUE(all.equal(as.numeric(ar[[v]]),
      as.numeric(z$historia[[v]]),tolerance=1e-14)))
  }
  invisible(TRUE)
}

# [Anotación · líneas 724–753] ejecutar_BO(), inicio: si no hay checkpoint bo_n/inicio genera un diseño LHS de
#   6 puntos con paradox bajo la semilla 727777, crea el motor y guarda el estado. Luego recupera en orden las
#   evaluaciones ya cerradas y devuelve el estado sin entrenar si la selección ya está fijada, si solo_ensembles
#   está activo, si se agotó el tiempo o bo_horas, o si ya hay 20 evaluaciones.
ejecutar_BO <- function() {
  on.exit({rm(list=ls(BO_CTX),envir=BO_CTX);gc(verbose=FALSE)},add=TRUE)
  if (is.null(abrir_checkpoint("bo_n/inicio",BO_ID))) {
    set.seed(PARAM$seed_BO,kind="L'Ecuyer-CMRG",normal.kind="Inversion",sample.kind="Rejection")
    lhs <- paradox::generate_design_lhs(dominio_BO(),n=6L)$data
    lhs <- lhs[,..hp_campos]
    lhs[,`:=`(num_iterations=as.integer(num_iterations),num_leaves=as.integer(num_leaves))]
    stopifnot(nrow(lhs)==6L,!anyDuplicated(lhs))
    motor <- nuevo_motor_BO()
    set.seed(PARAM$seed_BO,kind="L'Ecuyer-CMRG",normal.kind="Inversion",sample.kind="Rejection")
    estado <- list(bo_id=BO_ID,motor=motor,lhs=lhs,historia=data.table(),
                   rng=guardar_rng(),seg_acumulados=0)
    d <- iniciar_checkpoint("bo_n/inicio")
    rds_atomico(estado,file.path(d,"estado.rds"))
    csv_atomico(lhs,file.path(d,"LHS_6.csv"))
    cerrar_checkpoint("bo_n/inicio",BO_ID)
  }
  ultima <- "bo_n/inicio"; n <- 0L
  # Recuperación automática de TODOS los trabajos confirmados, en orden; no replay de modelos.
  for (i in seq_len(PARAM$n_total)) {
    key <- sprintf("bo_n/eval_%02d",i)
    ck <- abrir_checkpoint(key,firma(list(bo=BO_ID,eval_id=i)))
    if (is.null(ck)) break
    ultima <- key; n <- i
  }
  estado <- readRDS(file.path(ck_dir(ultima),"estado.rds"))
  validar_estado_BO(estado,n)
  fijada <- abrir_checkpoint("bo_n/seleccion",BO_ID)
  if (!is.null(fijada) || solo_ensembles || !hay_tiempo() ||
      estado$seg_acumulados>=bo_horas*3600 || n==PARAM$n_total) return(estado)

# [Anotación · líneas 755–789] Carga 202103+202104 como entrenamiento y 202106 como validación. En cada vuelta
#   comprueba el presupuesto de tiempo y toma la propuesta pendiente si quedó guardada o genera una nueva: la
#   fila del LHS para las evaluaciones 1 a 6 y una propuesta de EI desde la 7. Se detiene si la propuesta repite
#   hiperparámetros ya evaluados y guarda la propuesta en un checkpoint antes de entrenar.
  train <- cargar_meses(PARAM$BO_train); valid <- cargar_mes(PARAM$BO_valid)
  BO_CTX$X <- matriz_SAFE(train); BO_CTX$y <- train$binaria2
  BO_CTX$Xvalid <- matriz_SAFE(valid)
  BO_CTX$valid <- valid[,.(numero_de_cliente,foto_mes,clase_ternaria,binaria2)]
  rm(train,valid); gc(verbose=FALSE)
  base_tiempo <- estado$seg_acumulados
  inicio_sesion <- proc.time()[["elapsed"]]
  while (n<PARAM$n_total) {
    gastado <- base_tiempo+proc.time()[["elapsed"]]-inicio_sesion
    if (gastado>=bo_horas*3600 || !hay_tiempo()) break
    i <- n+1L
    key_p <- sprintf("bo_n/propuesta_%02d",i)
    sig_p <- firma(list(bo=BO_ID,propuesta=i))
    ck_p <- abrir_checkpoint(key_p,sig_p)
    if (!is.null(ck_p)) {
      pendiente <- readRDS(file.path(ck_dir(key_p),"pendiente.rds"))
      estado <- pendiente$estado
      hp <- pendiente$hp
      validar_estado_BO(estado,n)
      restaurar_rng(estado$rng)
      message("Reanudando la misma propuesta BO ",i)
    } else {
      restaurar_rng(estado$rng)
      hp <- if (i<=6L) copy(estado$lhs[i]) else proponer_EI(estado$motor)
      hp <- as.data.table(hp_lista(hp))
      # El continuo de Hessian hace improbable una repetición; nunca la reentrenamos silenciosamente.
      if (n && any(vapply(seq_len(n),function(k)
          identical(hp_lista(estado$historia[k]),hp_lista(hp)),logical(1))))
        stop("EI propuso HP ya evaluados; revisar la adquisición sin repetir entrenamiento.")
      estado$rng <- guardar_rng()
      d <- iniciar_checkpoint(key_p)
      rds_atomico(list(estado=estado,hp=hp),file.path(d,"pendiente.rds"))
      csv_atomico(hp,file.path(d,"hiperparametros.csv"))
      cerrar_checkpoint(key_p,sig_p)
    }
# [Anotación · líneas 790–815] Evalúa la propuesta con el motor, agrega el resultado a la historia, actualiza
#   el tiempo acumulado y cierra el checkpoint de la evaluación con las predicciones de junio, la curva de
#   ganancia, las métricas, el historial y el estado. Imprime AUC, GainBand y minutos.
    # El backup de la propuesta también consume tiempo: volver a consultar el límite.
    if (base_tiempo+proc.time()[["elapsed"]]-inicio_sesion>=bo_horas*3600 || !hay_tiempo()) break
    BO_CTX$hp <- hp_lista(hp); BO_CTX$eval_id <- i
    BO_CTX$origen <- if (i<=6L) "LHS" else "EI"
    message("BO ",i,"/20: ",paste(unlist(BO_CTX$hp),collapse=" / "))
    restaurar_rng(estado$rng)
    estado$motor$instance$eval_batch(hp)
    z <- BO_CTX$resultado
    estado$historia <- rbindlist(list(estado$historia,z$meta),use.names=TRUE,fill=TRUE)
    estado$rng <- guardar_rng()
    estado$seg_acumulados <- base_tiempo+proc.time()[["elapsed"]]-inicio_sesion
    validar_estado_BO(estado,i)
    key <- sprintf("bo_n/eval_%02d",i); d <- iniciar_checkpoint(key)
    csv_atomico(z$pred,file.path(d,"predicciones_junio.csv"))
    csv_atomico(z$curva,file.path(d,"curva_junio_completa.csv"))
    csv_atomico(z$meta,file.path(d,"metricas.csv"))
    csv_atomico(estado$historia,file.path(d,"historial_BO.csv"))
    rds_atomico(estado,file.path(d,"estado.rds"))
    cerrar_checkpoint(key,firma(list(bo=BO_ID,eval_id=i)))
    n <- i
    message(sprintf("BO %d confirmada: AUC %.8f | GainBand %.3f M | %.1f min",
                    i,z$meta$AUC,z$meta$GainBand_junio/1e6,z$meta$seg_total/60))
    rm(z); BO_CTX$resultado <- NULL; gc(verbose=FALSE)
  }
  estado
}

# [Anotación · líneas 817–842] Tres celdas de ajuste: vuelve a poner respaldo_GCS en FALSE, imprime el espacio
#   de búsqueda con el tope de evaluaciones y bo_horas, y agrega num_threads=4 a los parámetros fijos de
#   LightGBM.
#%% celda 9 [código]
respaldo_GCS <- FALSE
message("GCS interno desactivado; checkpoints locales activos")
print(respaldo_GCS)

#%% celda 10 [código]
print(dominio_BO())
print(c(
  total = PARAM$n_total,
  GCS_interno = respaldo_GCS,
  horas_BO = bo_horas
))

#%% celda 11 [código]
PARAM$lgbm_fijos$num_threads <- 4L

stopifnot(param_modelo(
  list(
    num_iterations=50L,
    num_leaves=869L,
    min_sum_hessian_in_leaf=0.096488455638161
  ),
  727777L
)$num_threads == 4L)

cat("SAFE configurado con 4 hilos\n")

# [Anotación · líneas 844–872] Ejecuta o reanuda la BO. Si no hay selección guardada, ordena la historia por
#   AUC descendente (empates por evaluación más temprana), toma la primera y la guarda en el checkpoint
#   bo_n/seleccion con su ranking. Lee de ahí HP, los hiperparámetros que usan el HNC y la producción. Según la
#   salida guardada: 20 evaluaciones (6 LHS + 14 EI), elegida la 9 con AUC 0,9199935, num_iterations=3246,
#   num_leaves=951, min_sum_hessian_in_leaf=0,009123316.
#%% celda 12 [código]
# BLOQUE 7 — Ejecutar/reanudar BO y congelar un único HP ganador #####
estado_BO <- ejecutar_BO()
HIST_BO <- estado_BO$historia
if (!nrow(HIST_BO)) stop("No hay evaluaciones BO terminadas. Ampliar bo_horas/límite y reanudar.")
if (is.null(abrir_checkpoint("bo_n/seleccion",BO_ID))) {
  if (solo_ensembles) stop("No existe selección congelada; ejecutar el pipeline para crearla.")
  ranking <- copy(HIST_BO)
  setorder(ranking,-AUC,eval_id)
  seleccion <- list(hp=hp_lista(ranking[1]),eval_id=ranking$eval_id[1],
    auc=ranking$AUC[1],gainband=ranking$GainBand_junio[1],n_evaluaciones=nrow(HIST_BO),
    n_LHS=sum(HIST_BO$origen=="LHS"),n_EI=sum(HIST_BO$origen=="EI"),
    bo_id=BO_ID,feature_id=FEATURE_ID,criterio="AUC_JUNIO_SIN_HNC",
    cierre=if(nrow(HIST_BO)==20L) "20_EVALUACIONES" else "PRESUPUESTO_O_LIMITE")
  d <- iniciar_checkpoint("bo_n/seleccion")
  rds_atomico(seleccion,file.path(d,"seleccion.rds"))
  csv_atomico(ranking,file.path(d,"ranking_AUC.csv"))
  cerrar_checkpoint("bo_n/seleccion",BO_ID)
}
seleccion <- readRDS(file.path(ck_dir("bo_n/seleccion"),"seleccion.rds"))
HP <- seleccion$hp
HP_ID <- firma(list(bo=BO_ID,seleccion=seleccion))
stopifnot(seleccion$n_evaluaciones==nrow(HIST_BO),identical(seleccion$feature_id,FEATURE_ID))
message("HP congelados tras ",seleccion$n_evaluaciones," evaluaciones (",
        seleccion$n_LHS," LHS + ",seleccion$n_EI," EI). BO posterior no se mezcla con esta producción.")
print(data.table(eval_id=seleccion$eval_id,AUC=seleccion$auc,
  GainBand_junio_sin_HNC=seleccion$gainband,as.data.table(HP)))
rm(estado_BO)
gc(verbose=FALSE)

# [Anotación · líneas 874–901] validar_claves() compara claves cliente-mes entre dos tablas. make_folds(): con
#   el generador Mersenne-Twister y set.seed(727777 + y), reparte los clientes en 5 folds por separado según
#   tengan o no alguna baja (máximo de binaria2 por cliente); todas las filas de un cliente quedan en el mismo
#   fold.
#%% celda 13 [código]
# BLOQUE 8 — HNC original: cinco folds por cliente, una semilla, 5% por mes #####
validar_claves <- function(a,b) {
  if (nrow(a)!=nrow(b) || anyDuplicated(a,by=c("numero_de_cliente","foto_mes")) ||
      !identical(as.character(a$numero_de_cliente),as.character(b$numero_de_cliente)) ||
      !identical(as.integer(a$foto_mes),as.integer(b$foto_mes)))
    stop("OOF: claves cliente-mes desalineadas/duplicadas.")
  invisible(TRUE)
}
make_folds <- function(dt) {
  # El HNC original es autónomo y usa set.seed(seed+y), sin cambiar RNGkind.
  # Fijamos explícitamente el default de una sesión R nueva, para que la BO previa
  # (L'Ecuyer) no altere accidentalmente los folds del notebook HNC original.
  anterior <- guardar_rng(); on.exit(restaurar_rng(anterior),add=TRUE)
  RNGkind("Mersenne-Twister","Inversion","Rejection")
  grp <- dt[,.(ymax=max(binaria2)),by=numero_de_cliente]
  grp[,fold := NA_integer_]
  for (y in c(0L,1L)) {
    idx <- which(grp$ymax==y)
    set.seed(PARAM$seed_OOF+y)
    if (length(idx)>1L) idx <- sample(idx,length(idx))
    grp$fold[idx] <- rep(seq_len(PARAM$n_folds),length.out=length(idx))
  }
  folds <- grp$fold[match(dt$numero_de_cliente,grp$numero_de_cliente)]
  stopifnot(!anyNA(folds),!anyDuplicated(grp$numero_de_cliente),
            all(folds %in% seq_len(PARAM$n_folds)))
  list(grp=grp,fold=folds)
}
# [Anotación · líneas 902–924] marcar_HNC(): en cada mes ordena las filas CONTINUA por probabilidad fuera de
#   fold descendente (empates por ID como texto) y marca para excluir las primeras floor(n × 5/100). Resume por
#   mes cuántas se eliminan y comprueba que ninguna BAJA quede marcada. HNC_BASE_ID firma los parámetros de la
#   limpieza.
marcar_HNC <- function(dt,prob,folds) {
  validar_prob(prob,nrow(dt))
  stopifnot(length(folds)==nrow(dt),!anyNA(folds))
  out <- dt[,.(numero_de_cliente,foto_mes,clase_ternaria,binaria2)]
  out[,`:=`(prob_OOF=prob,fold=as.integer(folds),excluir=FALSE)]
  for (m in sort(unique(out$foto_mes))) {
    idx <- which(out$foto_mes==m & out$clase_ternaria=="CONTINUA")
    k <- as.integer(floor(length(idx)*PARAM$hnc_pct/100))
    if (k) {
      ix <- idx[order(-prob[idx],as.character(out$numero_de_cliente[idx]))[seq_len(k)]]
      set(out,i=ix,j="excluir",value=TRUE)
    }
  }
  resumen <- out[,.(continua=sum(clase_ternaria=="CONTINUA"),
    eliminados=sum(excluir),bajas_antes=sum(binaria2==1L),
    bajas_despues=sum(binaria2==1L & !excluir),bajas_eliminadas=sum(binaria2==1L & excluir)),by=foto_mes]
  stopifnot(all(resumen$eliminados==floor(resumen$continua*PARAM$hnc_pct/100)),
            all(resumen$bajas_eliminadas==0L),all(out$clase_ternaria[out$excluir]=="CONTINUA"))
  list(manifiesto=out,resumen=resumen)
}
HNC_BASE_ID <- firma(list(pipe=PIPE_ID,hp=HP_ID,meses=c(202105L,202106L),
  seed=727777L,folds=5L,pct=5,RNG="Mersenne-Twister/Inversion/Rejection",
  desempate="order(-prob_OOF,as.character(numero_de_cliente))"))

# [Anotación · líneas 926–943] ejecutar_HNC(), inicio: devuelve la limpieza guardada si existe; si no, carga
#   202105 y 202106, arma los folds y los guarda en un checkpoint (o comprueba que coincidan con los guardados).
ejecutar_HNC <- function() {
  ck <- abrir_checkpoint("hnc/limpieza",HNC_BASE_ID)
  if (!is.null(ck)) return(readRDS(file.path(ck_dir("hnc/limpieza"),"limpieza.rds")))
  if (solo_ensembles) stop("Aún no existe limpieza HNC confirmada.")
  dt <- cargar_meses(c(202105L,202106L))
  ff <- make_folds(dt)
  fold_id <- firma(as.data.frame(ff$grp))
  sig_f <- firma(list(hnc=HNC_BASE_ID,folds=fold_id))
  if (is.null(abrir_checkpoint("hnc/folds",sig_f))) {
    d <- iniciar_checkpoint("hnc/folds")
    rds_atomico(ff,file.path(d,"folds.rds"))
    csv_atomico(ff$grp,file.path(d,"folds_por_cliente.csv"))
    cerrar_checkpoint("hnc/folds",sig_f)
  } else {
    guardado <- readRDS(file.path(ck_dir("hnc/folds"),"folds.rds"))
    stopifnot(identical(guardado$fold,ff$fold),
              identical(as.data.frame(guardado$grp),as.data.frame(ff$grp)))
  }
# [Anotación · líneas 944–976] Para cada uno de los 5 folds entrena con las filas de los otros cuatro, con los
#   hiperparámetros elegidos y la semilla 727777, y predice las filas del fold. Guarda las predicciones y
#   metadatos de cada fold en su checkpoint y completa el vector de probabilidades fuera de fold; si se alcanza
#   el límite horario devuelve NULL y conserva los folds hechos.
  pred <- rep(NA_real_,nrow(dt)); X <- NULL
  for (f in seq_len(PARAM$n_folds)) {
    it <- which(ff$fold!=f); iv <- which(ff$fold==f)
    stopifnot(length(it)>0L,length(iv)>0L,
      !length(intersect(unique(dt$numero_de_cliente[it]),unique(dt$numero_de_cliente[iv]))))
    key <- sprintf("hnc/fold_%02d",f)
    sig <- firma(list(hnc=HNC_BASE_ID,fold_id=fold_id,fold=f))
    ck <- abrir_checkpoint(key,sig)
    if (is.null(ck)) {
      if (!hay_tiempo()) {
        message("Límite alcanzado: HNC pendiente desde fold ",f,"; folds previos conservados.")
        return(NULL)
      }
      if (is.null(X)) X <- matriz_SAFE(dt)
      d <- iniciar_checkpoint(key)
      message("OOF HNC fold ",f,"/5; seed 727777; HP BO ",seleccion$eval_id)
      z <- ajustar_SAFE(X[it,,drop=FALSE],dt$binaria2[it],X[iv,,drop=FALSE],HP,PARAM$seed_OOF,
        modelo_archivo=if(guardar_modelos) file.path(d,"modelo.txt") else NULL)
      p <- dt[iv,.(numero_de_cliente,foto_mes,clase_ternaria,binaria2)]
      p[,`:=`(fold=f,prob_OOF=z$p)]
      csv_atomico(p,file.path(d,"predicciones_OOF.csv"))
      rds_atomico(list(hp=HP,hp_id=HP_ID,feature_id=FEATURE_ID,seed=PARAM$seed_OOF,
        fold=f,fold_id=fold_id,n_train=length(it),n_valid=length(iv),
        sin_clientes_compartidos=TRUE,seg_entrenamiento=z$seg_entrenamiento,
        seg_prediccion=z$seg_prediccion),file.path(d,"meta.rds"))
      cerrar_checkpoint(key,sig)
      rm(z,p); gc(verbose=FALSE)
    }
    p <- fread(file.path(ck_dir(key),"predicciones_OOF.csv"),na.strings=c("","NA"))
    validar_claves(p,dt[iv]); validar_prob(p$prob_OOF,length(iv))
    stopifnot(all(p$fold==f))
    pred[iv] <- p$prob_OOF
  }
# [Anotación · líneas 977–990] Con las probabilidades completas llama a marcar_HNC(), calcula la firma y la
#   versión de la limpieza (HNC5_ más 12 caracteres) y guarda el checkpoint hnc/limpieza con el manifiesto fila
#   por fila y los conteos por mes.
  validar_prob(pred,nrow(dt))
  clean <- marcar_HNC(dt,pred,ff$fold)
  clean$clean_id <- firma(list(hnc=HNC_BASE_ID,fold_id=fold_id,
    ids=as.character(clean$manifiesto$numero_de_cliente),mes=clean$manifiesto$foto_mes,
    prob=clean$manifiesto$prob_OOF,excluir=clean$manifiesto$excluir))
  clean$hp_id <- HP_ID; clean$feature_id <- FEATURE_ID
  clean$version <- paste0("HNC5_",substr(clean$clean_id,1L,12L))
  d <- iniciar_checkpoint("hnc/limpieza")
  csv_atomico(clean$manifiesto,file.path(d,"manifiesto_HNC_mayo_junio.csv"))
  csv_atomico(clean$resumen,file.path(d,"conteos_HNC_por_mes.csv"))
  rds_atomico(clean,file.path(d,"limpieza.rds"))
  cerrar_checkpoint("hnc/limpieza",HNC_BASE_ID)
  clean
}

# [Anotación · líneas 992–1001] Ejecuta la limpieza HNC, comprueba que corresponda a los hiperparámetros y
#   variables vigentes e imprime el resumen. Según la salida guardada se retiran 8.087 filas CONTINUA de 202105
#   y 8.107 de 202106.
#%% celda 14 [código]
# BLOQUE 9 — Generar/reutilizar la única limpieza de mayo + junio #####
HNC <- ejecutar_HNC()
if (!is.null(HNC)) {
  stopifnot(identical(HNC$hp_id,HP_ID),identical(HNC$feature_id,FEATURE_ID),
            all(HNC$resumen$bajas_eliminadas==0L))
  print(HNC$resumen)
  message("Limpieza confirmada: ",HNC$version)
}
gc(verbose=FALSE)

# [Anotación · líneas 1003–1019] Funciones de nombres y firmas por familia y semilla, y leer_pred_semilla(),
#   que abre el checkpoint de una semilla, comprueba sus metadatos y devuelve sus probabilidades de agosto
#   validadas contra el universo.
#%% celda 15 [código]
# BLOQUE 10 — Producción progresiva y ensembles por promedio de probabilidades #####
clave_semilla <- function(P,s) paste0("produccion/",P,"/seed_",s)
firma_semilla <- function(P,s) firma(list(pipe=PIPE_ID,hp=HP_ID,hnc=HNC$clean_id,
                                        P=P,seed=as.integer(s),train=PARAM$P_final[[P]]))
etiqueta <- function(P) paste0(P,"_HP_BO",sprintf("%02d",seleccion$eval_id),"_",
                               substr(HP_ID,1,8),"_",HNC$version)
leer_pred_semilla <- function(P,s) {
  key <- clave_semilla(P,s)
  if (is.null(abrir_checkpoint(key,firma_semilla(P,s)))) return(NULL)
  meta <- readRDS(file.path(ck_dir(key),"meta.rds"))
  stopifnot(identical(meta$hp_id,HP_ID),identical(meta$feature_id,FEATURE_ID),
            identical(meta$clean_id,HNC$clean_id),identical(meta$P,P),meta$seed==s)
  p <- fread(file.path(ck_dir(key),meta$pred_file),na.strings=c("","NA"))
  validar_ids(p$numero_de_cliente,UNIVERSO); validar_prob(p$prediction,length(UNIVERSO))
  p
}
# [Anotación · líneas 1020–1043] generar_ensemble(): suma las probabilidades de agosto de las semillas
#   disponibles entre las primeras n_semillas y las divide por la cantidad (promedio aritmético). Escribe
#   <nombre>_probabilidades_agosto.csv, ordena por probabilidad descendente (empates por numero_de_cliente) y
#   escribe el ranking completo.
generar_ensemble <- function(P) {
  semillas <- PARAM$semillas[seq_len(n_semillas)]
  suma <- rep(0,length(UNIVERSO)); usadas <- integer()
  for (s in semillas) {
    p <- leer_pred_semilla(P,s)
    if (is.null(p)) next
    suma <- suma+p$prediction
    usadas <- c(usadas,s)
  }
  n <- length(usadas)
  if (!n) return(list(P=P,n=0L,completo=FALSE,carpeta=NA_character_))
  sig <- firma(list(pipe=PIPE_ID,hp=HP_ID,hnc=HNC$clean_id,P=P,semillas=usadas,
                    metodo="MEDIA_ARITMETICA_PROBABILIDADES",cortes=PARAM$cortes))
  key <- paste0("ensembles/",P,"/n",sprintf("%02d",n),"_",substr(sig,1,12))
  ck <- abrir_checkpoint(key,sig)
  if (is.null(ck)) {
    d <- iniciar_checkpoint(key)
    nombre <- paste0(etiqueta(P),"_n",sprintf("%02d",n))
    ens <- data.table(numero_de_cliente=UNIVERSO,prediction=suma/n)
    validar_prob(ens$prediction,length(UNIVERSO)); validar_ids(ens$numero_de_cliente,UNIVERSO)
    csv_atomico(ens,file.path(d,paste0(nombre,"_probabilidades_agosto.csv")))
    setorder(ens,-prediction,numero_de_cliente)
    ens[,ranking := seq_len(.N)]
    csv_atomico(ens,file.path(d,paste0(nombre,"_ranking_agosto.csv")))
# [Anotación · líneas 1044–1069] Para cada corte de PARAM$cortes (12 valores, de 9.500 a 15.000) escribe un
#   archivo _topK.csv con los primeros K numero_de_cliente, sin encabezado, y lo relee para comprobarlo. Guarda
#   manifest_submissions.csv y meta.rds con las semillas usadas y cierra el checkpoint
#   ensembles/<familia>/nNN_<firma>.
    salidas <- vector("list",length(PARAM$cortes))
    for (j in seq_along(PARAM$cortes)) {
      k <- PARAM$cortes[j]
      stopifnot(k<=nrow(ens))
      nombre_sub <- paste0(nombre,"_top",k,".csv")
      f <- file.path(d,nombre_sub)
      csv_atomico(ens[seq_len(k),.(numero_de_cliente)],f,encabezado=FALSE)
      ids <- fread(f,header=FALSE)[[1L]]
      validar_ids(ids,ens$numero_de_cliente[seq_len(k)])
      stopifnot(length(ids)==k,all(ids %in% UNIVERSO))
      salidas[[j]] <- data.table(modelo=P,eval_BO=seleccion$eval_id,
        num_iterations=HP$num_iterations,num_leaves=HP$num_leaves,
        min_sum_hessian_in_leaf=HP$min_sum_hessian_in_leaf,
        n_semillas=n,cutoff=k,HNC=HNC$version,archivo=nombre_sub,md5=md5(f))
    }
    csv_atomico(rbindlist(salidas),file.path(d,"manifest_submissions.csv"))
    rds_atomico(list(P=P,hp=HP,hp_id=HP_ID,feature_id=FEATURE_ID,clean_id=HNC$clean_id,
      HNC_version=HNC$version,semillas=usadas,n_semillas=n,
      objetivo_al_crear=n_semillas,provisional_al_crear=n<n_semillas,
      agregacion="promedio aritmetico de probabilidades",desempate="ID numerico ascendente"),
      file.path(d,"meta.rds"))
    cerrar_checkpoint(key,sig)
    message(P,": ensemble de ",n," semillas y ",length(PARAM$cortes)," submissions confirmados.")
  }
  list(P=P,n=n,completo=n==n_semillas,carpeta=ck_dir(key),checkpoint=key)
}
# [Anotación · líneas 1070–1082] entrenamiento_final(): carga los meses de la familia (P2: 202105 y 202106) y
#   quita las filas que el manifiesto HNC marca para excluir, comprobando que no se elimine ninguna BAJA ni
#   filas de 202103 o 202104. Los ranks no se recalculan después de quitar filas.
entrenamiento_final <- function(P) {
  dt <- cargar_meses(PARAM$P_final[[P]])
  claves <- paste(HNC$manifiesto$foto_mes,HNC$manifiesto$numero_de_cliente,sep="|")
  idx <- match(paste(dt$foto_mes,dt$numero_de_cliente,sep="|"),claves)
  mayo_junio <- dt$foto_mes %in% c(202105L,202106L)
  stopifnot(!anyNA(idx[mayo_junio]),all(is.na(idx[!mayo_junio])))
  quitar <- rep(FALSE,nrow(dt))
  quitar[mayo_junio] <- HNC$manifiesto$excluir[idx[mayo_junio]]
  stopifnot(!any(dt$binaria2[quitar]==1L),
    sum(quitar)==sum(HNC$resumen$eliminados),
    !any(quitar[dt$foto_mes %in% c(202103L,202104L)]))
  dt[!quitar]                             # NUNCA recalcular ranks después de HNC
}
# [Anotación · líneas 1083–1117] ejecutar_produccion(): primero exporta el ensemble con lo disponible. Después
#   arma las matrices de entrenamiento y de 202108 y, para cada semilla sin checkpoint, entrena un LightGBM con
#   los hiperparámetros elegidos, guarda sus probabilidades de agosto, los conteos de entrenamiento y metadatos,
#   y vuelve a generar el ensemble.
ejecutar_produccion <- function(P) {
  # Primero recupera/exporta todo lo disponible, incluso si ya venció el límite.
  estado <- generar_ensemble(P)
  if (estado$completo || solo_ensembles || !hay_tiempo()) return(estado)
  train <- entrenamiento_final(P)
  score <- cargar_mes(PARAM$mes_score)
  validar_ids(score$numero_de_cliente,UNIVERSO)
  X <- matriz_SAFE(train); y <- train$binaria2; Xscore <- matriz_SAFE(score)
  conteos_train <- train[,.N,by=.(foto_mes,clase_ternaria)]
  n_train <- nrow(train)
  rm(train,score); gc(verbose=FALSE)
  for (s in PARAM$semillas[seq_len(n_semillas)]) {
    key <- clave_semilla(P,s); sig <- firma_semilla(P,s)
    if (!is.null(abrir_checkpoint(key,sig))) next
    if (!hay_tiempo()) break
    d <- iniciar_checkpoint(key)
    message(P," seed ",s,": train ",n_train," / agosto ",length(UNIVERSO))
    z <- ajustar_SAFE(X,y,Xscore,HP,s,
      modelo_archivo=if(guardar_modelos) file.path(d,"modelo.txt") else NULL)
    nombre <- paste0(etiqueta(P),"_seed",s,"_agosto.csv")
    p <- data.table(numero_de_cliente=UNIVERSO,prediction=z$p)
    validar_ids(p$numero_de_cliente,UNIVERSO)
    csv_atomico(p,file.path(d,nombre))
    csv_atomico(conteos_train,file.path(d,"filas_train.csv"))
    rds_atomico(list(P=P,seed=as.integer(s),hp=HP,hp_id=HP_ID,feature_id=FEATURE_ID,
      clean_id=HNC$clean_id,HNC_version=HNC$version,fijos=PARAM$lgbm_fijos,
      train=PARAM$P_final[[P]],score=PARAM$mes_score,n_train=n_train,n_score=length(UNIVERSO),
      pred_file=nombre,seg_entrenamiento=z$seg_entrenamiento,seg_prediccion=z$seg_prediccion),
      file.path(d,"meta.rds"))
    cerrar_checkpoint(key,sig)             # antes de la siguiente semilla
    rm(z,p); gc(verbose=FALSE)
    estado <- generar_ensemble(P)          # siempre queda una submission parcial utilizable
  }
  generar_ensemble(P)
}

# [Anotación · líneas 1119–1151] Si la limpieza HNC está completa ejecuta P2 y, si producir_P3 es TRUE y P2
#   está completo o no se pidió producir P2, P3. Imprime y guarda un resumen con las semillas completas por
#   familia y la carpeta de salida. Según la salida guardada, cada semilla de P2 entrena con 311.688 filas y
#   cada ensemble trae 12 listas.
#%% celda 16 [código]
# BLOQUE 11 — P2 completo y respaldado → P3; sin mezclar familias #####
resultados <- list()
if (is.null(HNC)) {
  message("HNC aún incompleta; reanudar este notebook. No se inició producción.")
} else {
  if (producir_P2) resultados$P2 <- ejecutar_produccion("P2")
  if (producir_P3) {
    if (!producir_P2 || isTRUE(resultados$P2$completo)) {
      resultados$P3 <- ejecutar_produccion("P3")
    } else {
      # P3 ya existente puede exportarse con solo_ensembles, sin iniciar ningún modelo.
      if (solo_ensembles) resultados$P3 <- generar_ensemble("P3")
      message("P3 pendiente: completar y respaldar P2, o desactivar producir_P2 explícitamente.")
    }
  }
}
if (length(resultados)) {
  resumen <- rbindlist(lapply(resultados,function(z) data.table(
    modelo=z$P,semillas_completas=z$n,objetivo=n_semillas,
    estado=if(z$completo) "COMPLETO" else "PROVISIONAL",carpeta=z$carpeta)))
  print(resumen)
  resumen_id <- firma(as.data.frame(resumen))
  key <- paste0("reportes/resumen_",substr(resumen_id,1,16))
  if (is.null(abrir_checkpoint(key,resumen_id))) {
    d <- iniciar_checkpoint(key)
    csv_atomico(resumen,file.path(d,"salidas_disponibles.csv"))
    cerrar_checkpoint(key,resumen_id)
  }
}
message("BO: ",nrow(HIST_BO),"/20 evaluaciones; AUC elegida=",round(seleccion$auc,8),
  "; GainBand junio SIN HNC=",round(seleccion$gainband/1e6,3)," M.")
message("Submissions: una columna de IDs, sin encabezado. No se envían automáticamente.")

# [Anotación · líneas 1153–1176] Celda de texto. Tabla de pruebas que el texto declara ejecutadas sobre las
#   funciones del notebook en R 4.3.3 con mlr3mbo 1.2.1 y bbotk 1.13.1 (clases, rank con signo, folds, HNC,
#   checkpoints, GCS simulado, bucle de BO, ensemble) y los límites que declara: datos pequeños y un sustituto
#   del entrenamiento de LightGBM.
#%% celda 17 [texto]
## Validación realizada antes de entregar

Se ejecutaron pruebas pequeñas en **R 4.3.3**, con `mlr3mbo 1.2.1` y `bbotk 1.13.1`, sobre las funciones de este notebook:

| Prueba | Resultado |
|---|---|
| Parseo de todas las celdas de código R; estructura JSON y kernel R | Correcto. Celdas sin resultados de entrenamientos precargados. |
| Targets: BAJA+1, BAJA+2, desapariciones, huecos de meses y agosto desconocido | Correcto en casos pequeños con respuestas conocidas. |
| Signed rank: negativos, positivos, empates, cero y NA | Coincide con resultados esperados; no imputa valores. |
| Temporales por ID/mes: cliente sin abril; mayo corregido propagado a junio; marzo sin historia | Correcto. No desplaza la observación de otro mes para rellenar el faltante. |
| Folds HNC | Coinciden con la función original bajo el RNG de una sesión autónoma. Sin clientes compartidos entre train/valid del fold. |
| HNC 5% y empates | Cantidad exacta por `floor`, desempate por ID como texto y ninguna BAJA eliminada. |
| Checkpoint, firma incorrecta y archivo corrupto | Checkpoint válido aceptado; los otros dos rechazados. |
| GCS simulado: fallo de subida, reintento y pérdida de archivos locales | Se bloquea el avance; se completa el respaldo pendiente y se restauran bytes verificados. |
| Bucle EGO: función matemática pequeña | Las 10 propuestas EI coinciden con `bayesopt_ego()` nativo tras el mismo LHS, incluso serializando/restaurando el motor entre pasos. |
| Interrupción BO en la evaluación 17 y fallo después del commit local de la 18 | Reanuda la misma secuencia; sólo se repite el intento interrumpido de la 17. Ninguna evaluación completada vuelve a entrenarse. |
| BO parcial y selección congelada | Selecciona con dos evaluaciones disponibles; ampliar posteriormente el presupuesto no cambia una selección ya cerrada. |
| Flujo HNC → P2 → P3 y ampliación P2 de 10 a 20 semillas | Una HNC reutilizada; sólo diez semillas adicionales al ampliar; archivos anteriores intactos. |
| Ensemble y submissions | Promedio aritmético de probabilidades, ranking consistente, IDs exactos y exportación parcial con el número real de semillas. |

**Límites de esta validación:** los ensayos de orquestación usaron un sustituto determinista del entrenamiento LightGBM sobre datos diminutos; la BO de prueba sí utilizó el surrogate y la adquisición reales de `mlr3mbo`. No se entrenaron modelos de la competencia ni se descargó el dataset completo para esta auditoría. Tampoco se accedió al bucket privado: el protocolo GCS se probó con un CLI simulado y sus llamadas se contrastaron con la documentación oficial. La primera ejecución real verificará permisos, versiones, conteos, matrices y transferencias en la VM.

Las pruebas pequeñas integradas del bloque 3b se ejecutan al abrir el pipeline; las comprobaciones de datos, OOF y archivos están incorporadas a sus etapas. No se adjunta ningún script auxiliar.
```


## Explicaciones del alumno (texto original)

### README.md

> Se deben Correr en ese orden. Estan preparado para hacerlo en una misma VM. El archivo final de submission sera: 
> SUBMISSION_FINAL__P2_E012__RANK__P2_50p00pct__E012_50p00pct__dc97cf4f7614__TOP12500.csv
> En la carpeta: /home/ds/Expe/metaensemblesCorr//P2_E012__RANK__P2_50p00pct__E012_50p00pct__dc97cf4f7614/

