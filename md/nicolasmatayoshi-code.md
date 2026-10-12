# NicoMata — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: nicolasmatayoshi-code
- Repositorio: https://github.com/nicolasmatayoshi-code/dmeyf2026-competencia1-entrega
- Link posteado: https://github.com/nicolasmatayoshi-code/dmeyf2026-competencia1-entrega
- Commit: 37d68bc70f07abe1ca8a7c42cc9499d3d58cc9c6
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/nicolasmatayoshi-code/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/nicolasmatayoshi-code.json

## Resumen

La entrega contiene un README, dos scripts en R y los registros de sus corridas originales. 02_modelo_final/modelo_final.R parte del dataset crudo, calcula clase_ternaria, pone NA en ccajas_depositos en 202105, agrega lag y delta de orden 1 y 2 a las 152 variables (760 columnas con valores originales, sin submuestreo) y entrena 50 modelos LightGBM en 202103-202106 con los mismos hiperparámetros (254 hojas, 2000 árboles, learning_rate 0.005) y semillas distintas; predice 202108, promedia las probabilidades por cliente y escribe los 10.000 clientes de mayor promedio. 01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R entrena 3 modelos en 202103-04 con 4000 árboles y mide la ganancia en 202106 usando de 1000 a 4000 árboles; según el README, de esa corrida se tomó a mano el valor 2000 y el paso es opcional porque no escribe nada que lea el script final. El resto de los hiperparámetros está escrito en el código; el README declara que no hay optimización bayesiana. resultado_esperado/ trae el archivo entregado y sus huellas MD5 y SHA256.

**Qué entrega.** Un CSV sin encabezado con 10.000 numero_de_cliente, uno por línea: los de mayor probabilidad promedio del ensamble de 50 modelos. El archivo E01_prof2000_ens50m_k10000.csv está en resultado_esperado/ junto con sus huellas MD5 y SHA256. Según el README, se entregó por el bot de Zulip con el nombre E01prof_ens50.

**Cómo se ejecuta.** Según el README: poner competencia_01_crudo.csv en la carpeta desde donde se ejecuta (o definir DMEYF_CRUDO) y, opcionalmente, DMEYF_EXP para la salida (por defecto ./salida). Paso 1 (opcional): Rscript 01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R (55 min aprox.). Paso 2: Rscript 02_modelo_final/modelo_final.R (10 a 12 h; 12 a 15 min por modelo). Paso 3: md5sum del archivo generado y comparación con resultado_esperado/MD5.txt. El README indica que el paso 2 se puede volver a ejecutar si se corta, porque saltea los modelos ya terminados.

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase01): 1 si clase_ternaria es BAJA+1 o BAJA+2 y 0 en el resto. clase_ternaria se calcula dentro del script a partir del dataset crudo, según la presencia del cliente en los dos meses siguientes.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica: el modelo final entrena con todas las filas de 202103 a 202106 (bagging_fraction = 1, pos_bagging_fraction = 1, neg_bagging_fraction = 1). Según el README, la matriz de entrenamiento tiene 654.066 filas.
- **Calidad de datos:** ccajas_depositos se pasa a NA sólo en 202105 (el comentario del código indica que en ese mes viene toda en cero). Las demás variables no se modifican y los NA se dejan como NA. Las variables base que no son numéricas se convierten a numérico.
- **Drifting:** No se observa en el código: se usan los valores originales, sin ranking ni transformación (comentario de la línea 132 de modelo_final.R).
- **Variables dentro del mes:** No se observa en el código.
- **Variables históricas:** Para cada una de las 152 variables base: lag de orden 1 y 2 (valor del mismo cliente exactamente 1 y 2 meses calendario antes; NA si ese mes no existe) y delta de orden 1 y 2 (valor actual menos lag). Con la variable original son 5 columnas por variable, 760 en total.
- **Selección de variables:** No se observa en el código: el modelo recibe las 760 columnas.
- **Optimización de hiperparámetros:** No hay optimización bayesiana (README y comentario de la línea 51 de modelo_final.R). num_leaves = 254 y min_sum_hessian_in_leaf = 4.84e-4 están escritos en el código; el README los describe como fijados a mano, y a learning_rate, max_bin, min_data_in_leaf, feature_fraction, feature_fraction_bynode y metric como fijos según los tips de la cátedra. La cantidad de árboles sale de eleccion_cantidad_de_arboles.R: 3 modelos (semillas 125269, 175853 y 691651) entrenados en 202103-04 con 4000 árboles y evaluados en 202106 con 1000, 1500, 2000, 2500, 3000, 3500 y 4000 árboles del mismo modelo. La elección de 2000 es manual: el script sólo imprime la tabla y un texto fijo con la decisión.
- **Hiperparámetros finales:** num_iterations = 2000, num_leaves = 254, min_sum_hessian_in_leaf = 4.84e-4, learning_rate = 0.005, feature_fraction = 0.5, feature_fraction_bynode = 0.2, max_bin = 31, min_data_in_leaf = 0, max_depth = -1, min_gain_to_split = 0, lambda_l1 = 0, lambda_l2 = 0, bagging_fraction = 1, is_unbalance = FALSE, scale_pos_weight = 1, extra_trees = FALSE, boosting = gbdt, objective = binary, metric = auc, force_row_wise = TRUE, feature_pre_filter = FALSE, num_threads = 14.
- **Semillas:** 50 semillas derivadas de una semilla primigenia: se generan los números primos entre 100.000 y 1.000.000, se fija set.seed(765461) y se toman 50 con sample(). El script se detiene si hay repetidas o si las cinco primeras no son 125269, 175853, 691651, 593507 y 593083. La cantidad se puede cambiar con la variable de entorno DMEYF_NMODELOS (50 por defecto).
- **Cantidad de semillas:** 50
- **Ensamble:** Promedio, por numero_de_cliente, de las probabilidades de los 50 modelos, que tienen los mismos hiperparámetros y sólo cambian la semilla.
- **Corte:** Cantidad fija: los 10.000 clientes de mayor probabilidad promedio (PARAM$corte_final = 10000). Según el README, el corte se fijó a mano dentro de lo que acepta el bot (8.000 a 15.000).
- **Validación:** modelo_final.R no mide ganancia. eleccion_cantidad_de_arboles.R entrena en 202103-202104 y evalúa en 202106 con la ganancia de la competencia (1.072.500 por cada BAJA+2 enviado y -27.500 por cualquier otro): para cada cantidad de árboles calcula el promedio de la ganancia acumulada en los cortes de 9.000 a 14.000 envíos cada 500, por semilla y para el promedio de probabilidades de las 3 semillas, además de la ganancia máxima, la cantidad de envíos donde ocurre y la ganancia a 10.000 envíos. Según el README, ese promedio para el ensamble de 3 semillas fue, en millones: 389,2 con 1000 árboles; 395,4 con 1500; 393,1 con 2000; 392,8 con 2500; 389,3 con 3000; 387,6 con 3500 y 386,6 con 4000.
- **Salidas:** modelo_final.R escribe en la carpeta de salida: PARAM.txt, sessionInfo.txt, 50 archivos modelos/prob_prof_s<semilla>.csv (numero_de_cliente, prob), prob_ensamble_202108.csv y entrega/ensamble/E01_prof2000_ens50m_k10000.csv (un numero_de_cliente por línea, sin encabezado). eleccion_cantidad_de_arboles.R escribe PARAM.txt, sessionInfo.txt, un pseudo_prof_s<semilla>.rds por semilla y pseudo_profundo_por_arboles.csv.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Búsqueda en grilla o al azar (`hiperparametros.grilla_o_azar`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README: Windows 11 x64, R 4.3.1 (ucrt), data.table 1.14.8, zlightgbm 4.6.0.99 (con su comando de instalación), Matrix 1.5-4.1 y jsonlite 1.8.7; 14 hilos en una PC de 16 núcleos; la matriz de entrenamiento ocupa unos 4 GB, el proceso llega a 7 GB y se indican 16 GB de RAM. El README agrega que LightGBM no se corrió con deterministic = TRUE. Los dos scripts guardan sessionInfo.txt en la carpeta de salida.

## Pasos del camino de la entrega

1. **Parámetros, valores de control y semillas.** Los dos scripts definen la lista PARAM con los meses (entrenamiento final 202103-202106, predicción 202108), la clase positiva, la variable a tratar, los órdenes de lag 1 y 2, los parámetros de LightGBM y tres valores de control (4082 positivos en 202103-04, 152 variables base, 760 columnas). Las semillas salen de los primos entre 100.000 y 1.000.000 con set.seed(765461): 50 en el modelo final y las 3 primeras en la elección de árboles. (`02_modelo_final/modelo_final.R` líneas 28–74; `01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R` líneas 26–76)
2. **Lectura del dataset crudo.** Lee competencia_01_crudo.csv con fread (ruta por variable de entorno DMEYF_CRUDO o carpeta actual) y se detiene si falta alguno de los meses 202103 a 202106 o 202108. (`02_modelo_final/modelo_final.R` líneas 84–88; `01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R` líneas 86–90)
3. **Cálculo de clase_ternaria.** Convierte foto_mes a un número de período correlativo, obtiene por cliente los dos períodos siguientes y asigna CONTINUA, BAJA+1 (el cliente no figura el mes siguiente) o BAJA+2 (figura el mes siguiente y no a los dos meses). Se detiene si queda alguna fila de 202103-202106 sin clase. (`02_modelo_final/modelo_final.R` líneas 95–108; `01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R` líneas 97–110)
4. **Calidad de datos y clase binaria.** Pone NA en ccajas_depositos sólo en 202105. Crea clase01 = 1 para BAJA+1 y BAJA+2 y 0 para el resto, y se detiene si los positivos de 202103-04 no son 4082. Ordena por cliente y mes y verifica que haya 152 variables base. (`02_modelo_final/modelo_final.R` líneas 114–127; `01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R` líneas 116–129)
5. **Lags y deltas de orden 1 y 2.** Arma una clave numérica cliente × mes y con match ubica, para cada fila, la fila del mismo cliente 1 y 2 meses calendario antes (NA si no existe). Define los 760 nombres de columna: cada variable, su _lag1, _delta1, _lag2 y _delta2. (`02_modelo_final/modelo_final.R` líneas 135–144; `01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R` líneas 137–146)
6. **Armado de las matrices.** Selecciona las filas de 202103-202106 y las de 202108, ordenadas por mes y cliente, y llena columna por columna dos matrices numéricas de 760 columnas con el valor original, el lag y el delta (valor actual menos lag). Luego elimina el dataset de memoria. (`02_modelo_final/modelo_final.R` líneas 150–178; `01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R` líneas 152–182)
7. **Elección de la cantidad de árboles con 202106.** En eleccion_cantidad_de_arboles.R: entrena un modelo por cada una de 3 semillas con las filas de 202103-04 y 4000 árboles, predice 202106 usando los primeros 1000, 1500, ..., 4000 árboles y calcula la ganancia acumulada (1.072.500 por BAJA+2, -27.500 por el resto). Arma una tabla por cantidad de árboles con el promedio de ganancia en los cortes de 9.000 a 14.000 envíos y la guarda en pseudo_profundo_por_arboles.csv. El valor 2000 se copia a mano en PARAM$arboles del script final. (`01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R` líneas 185–188; `01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R` líneas 203–228; `02_modelo_final/modelo_final.R` líneas 54–54)
8. **Entrenamiento de 50 modelos y predicción de 202108.** Para cada semilla entrena un LightGBM con las filas de 202103-202106, 2000 árboles, 254 hojas y min_sum_hessian_in_leaf 4.84e-4, predice 202108 y guarda numero_de_cliente y prob en modelos/prob_prof_s<semilla>.csv. Si el archivo de una semilla ya existe, la saltea. (`02_modelo_final/modelo_final.R` líneas 181–186; `02_modelo_final/modelo_final.R` líneas 192–207)
9. **Ensamble por promedio.** Lee los 50 archivos de probabilidades, verifica que cada modelo tenga una fila por cliente de 202108 y sin repetidos, promedia prob por numero_de_cliente y guarda prob_ensamble_202108.csv. (`02_modelo_final/modelo_final.R` líneas 212–219)
10. **Corte en 10.000 clientes y escritura del archivo.** Ordena por probabilidad promedio descendente, toma los primeros 10.000 numero_de_cliente y los escribe como enteros, uno por línea y sin encabezado, en entrega/ensamble/E01_prof2000_ens50m_k10000.csv. (`02_modelo_final/modelo_final.R` líneas 222–225)
11. **Verificación de formato del archivo.** Relee el archivo generado y verifica que tenga entre 8.000 y 15.000 líneas, sólo dígitos, sin repetidos y sólo clientes presentes en 202108. (`02_modelo_final/modelo_final.R` líneas 231–234)

## Archivos

- `README.md` · explicacion · Markdown · 120 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicolasmatayoshi-code/README.md.txt) — Presenta la entrega (nombre del submit, archivo entregado, envío por el bot de Zulip), el enfoque, una tabla con cada hiperparámetro y cómo se fijó, la estructura de carpetas, versiones y requisitos, la descarga del dataset con su MD5, el orden de ejecución con tiempos, las verificaciones realizadas (MD5 de dos modelos reentrenados y del tramo posterior) y lo que no se verificó, y una nota sobre la reproducción exacta con varios hilos.
- `02_modelo_final/modelo_final.R` · principal · R · 234 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicolasmatayoshi-code/02_modelo_final/modelo_final.R.txt) — Script que va del dataset crudo al archivo entregado: calcula la clase, trata ccajas_depositos, arma lags y deltas de orden 1 y 2, entrena 50 modelos LightGBM en 202103-202106 que sólo difieren en la semilla, predice 202108, promedia las probabilidades y escribe los 10.000 clientes de mayor promedio.
- `02_modelo_final/log_original/PARAM_original.txt` · configuracion · Texto · 38 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicolasmatayoshi-code/02_modelo_final/log_original/PARAM_original.txt.txt) — Volcado (dput) del objeto PARAM de la corrida original del modelo final: experimento E01_prof2000, n_modelos = 50, las 50 semillas, corte_final = 10000 y los parámetros de LightGBM. Incluye campos que no están en el PARAM de modelo_final.R: usar_ranking = FALSE, hilos = 14, correr_pseudo = FALSE, una lista profundo (hojas = 254, hessiano = 0.000484, arboles_max = 2000, arboles_final = 2000) y una lista configs con cinco configuraciones de árboles, hojas y hessiano llamadas c1_denicolay, c2_guido, c3_pablo, c4_ludmila y c5_bo32.
- `resultado_esperado/SHA256.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicolasmatayoshi-code/resultado_esperado/SHA256.txt.txt)
- `resultado_esperado/MD5.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicolasmatayoshi-code/resultado_esperado/MD5.txt.txt)
- `01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R` · principal · R · 229 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicolasmatayoshi-code/01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R.txt) — Script del paso 1 del README, que lo declara opcional: entrena 3 modelos en 202103-04 con 4000 árboles y mide la ganancia en 202106 con siete cantidades de árboles. No escribe ningún archivo que lea modelo_final.R; el valor 2000 figura escrito en PARAM$arboles de ese script. Según el README, esta versión se limpió para el repositorio y sólo se comprobó su sintaxis; los resultados publicados son de una versión anterior del mismo código.
- `01_eleccion_cantidad_de_arboles/log_original/PARAM_original.txt` · configuracion · Texto · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicolasmatayoshi-code/01_eleccion_cantidad_de_arboles/log_original/PARAM_original.txt.txt) — Volcado (dput) del objeto PARAM de la corrida original de la elección de árboles: experimento E01_profundo, n_modelos = 20 con 20 semillas, correr_pseudo = TRUE y la lista profundo con hojas = 254, hessiano = 0.000484, arboles_max = 4000, puntos de 1000 a 4000 cada 500 y n_semillas = 3. Incluye también usar_ranking = FALSE y la misma lista configs de cinco configuraciones que el volcado del modelo final.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### 02_modelo_final/modelo_final.R

Script que va del dataset crudo al archivo entregado: calcula la clase, trata ccajas_depositos, arma lags y deltas de orden 1 y 2, entrena 50 modelos LightGBM en 202103-202106 que sólo difieren en la semilla, predice 202108, promedia las probabilidades y escribe los 10.000 clientes de mayor promedio.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Encabezado: describe la cadena (crudo, clase_ternaria, ccajas_depositos a NA en
#   202105, lags y deltas de orden 1 y 2, 50 modelos entrenados en 202103-202106, predicción de 202108, promedio
#   de probabilidades, 10.000 clientes), el comando de uso y las variables de entorno DMEYF_CRUDO y DMEYF_EXP.
#   Indica que el script es reanudable y que no hace envíos.
# ======================================================================
# MODELO FINAL (entrega E01prof_ens50): 50 modelos LightGBM, ensamble, 10.000 envios
# ======================================================================
# Primera Competencia DMEyF 2026: prediccion de BAJA+2 en 202108.
# Parte del dataset crudo y llega al archivo final de la entrega.
# Pipeline: crudo -> clase_ternaria -> data quality (ccajas_depositos = NA en 202105) -> lags y delta lags 1 y 2
# (760 columnas, valores originales, sin undersampling) -> 50 modelos con identicos hiperparametros y semillas distintas,
# entrenados en 202103-202106 -> prediccion de 202108 -> promedio simple de probabilidades -> 10.000 mejores clientes.
# Uso:   Rscript modelo_final.R > modelo_final.log 2>&1
# Rutas (variables de entorno, opcionales):
#   DMEYF_CRUDO = ruta de competencia_01_crudo.csv   (por defecto ./competencia_01_crudo.csv)
#   DMEYF_EXP   = carpeta de salida                  (por defecto ./salida)
# Reanudable: lo que ya esta guardado en la carpeta de salida no se recalcula. No envia nada a ningun sitio.

# [Anotación · líneas 15–23] Carga data.table y el paquete de LightGBM (zlightgbm si está instalado; si no,
#   lightgbm), imprime las versiones y resuelve la ruta del dataset y la carpeta de salida desde variables de
#   entorno, con valores por defecto relativos (competencia_01_crudo.csv y salida). Crea la carpeta de salida.
suppressMessages(library(data.table))
paquete_lgb <- if (requireNamespace("zlightgbm", quietly= TRUE)) "zlightgbm" else "lightgbm"   # se uso zlightgbm 4.6.0.99
suppressMessages(library(paquete_lgb, character.only= TRUE))
cat("R:", R.version.string, "| LightGBM:", paquete_lgb, as.character(packageVersion(paquete_lgb)),
    "| data.table:", as.character(packageVersion("data.table")), "\n")

RUTA_CRUDO  <- normalizePath(Sys.getenv("DMEYF_CRUDO", unset= "competencia_01_crudo.csv"), mustWork= FALSE)
RUTA_SALIDA <- normalizePath(Sys.getenv("DMEYF_EXP",   unset= "salida"), mustWork= FALSE)
dir.create(RUTA_SALIDA, showWarnings= FALSE, recursive= TRUE)

# [Anotación · líneas 25–38] Crea la lista PARAM: experimento E01_prof2000, semilla primigenia 765461, meses
#   de entrenamiento 202103 a 202106, mes a predecir 202108, meses 202103-04 para el control de cantidad de
#   positivos, clase positiva BAJA+1 y BAJA+2, variable ccajas_depositos a tratar en 202105 y órdenes de lag 1 y
#   2.
# ======================================================================
# PARAMETROS
# ======================================================================
PARAM <- list()
PARAM$experimento <- "E01_prof2000"
PARAM$semilla_primigenia <- 765461L                 # de ella salen todas las semillas de los modelos

PARAM$meses_final  <- c(202103, 202104, 202105, 202106)   # meses de entrenamiento del modelo final
PARAM$mes_futuro   <- 202108                              # mes a predecir
PARAM$meses_pseudo <- c(202103, 202104)                   # solo para la verificacion del positivo-ancla
PARAM$clase_positiva <- c("BAJA+1", "BAJA+2")             # clase01 = 1; CONTINUA = 0
PARAM$dq_campo    <- "ccajas_depositos"                   # variable rota en 202105 (todos ceros): se pone NA
PARAM$dq_mes_roto <- 202105
PARAM$ordenes_lag <- 1:2                                  # lag y delta lag de orden 1 y 2

# [Anotación · líneas 40–56] Parámetros de LightGBM comunes a todos los modelos (gbdt, objetivo binario,
#   métrica auc, max_bin 31, min_data_in_leaf 0, sin bagging, sin regularización L1 ni L2, learning_rate 0.005,
#   feature_fraction 0.5, feature_fraction_bynode 0.2, 14 hilos) y los tres propios del modelo: 254 hojas,
#   min_sum_hessian_in_leaf 4.84e-4 y 2000 árboles. La cantidad de modelos se lee de DMEYF_NMODELOS (50 por
#   defecto) y el corte es 10.000.
# LightGBM: parametros fijos (iguales en todos los modelos). num_threads fijo y explicito: 14 (corrida original).
PARAM$lgb <- list(
  boosting= "gbdt", objective= "binary", metric= "auc", first_metric_only= FALSE,
  boost_from_average= TRUE, feature_pre_filter= FALSE, force_row_wise= TRUE, verbosity= -1,
  max_depth= -1L, min_gain_to_split= 0, lambda_l1= 0, lambda_l2= 0,
  max_bin= 31L, min_data_in_leaf= 0L,
  bagging_fraction= 1, pos_bagging_fraction= 1, neg_bagging_fraction= 1,
  is_unbalance= FALSE, scale_pos_weight= 1, extra_trees= FALSE,
  learning_rate= 0.005, feature_fraction= 0.5, feature_fraction_bynode= 0.2,
  num_threads= 14L
)
# Hiperparametros del modelo. Fijados a mano; NO provienen de una optimizacion bayesiana (no hay ninguna en esta cadena).
PARAM$hojas    <- 254L          # num_leaves
PARAM$hessiano <- 4.84e-4       # min_sum_hessian_in_leaf
PARAM$arboles  <- 2000L         # num_iterations: elegido con 01_eleccion_cantidad_de_arboles (centro de la meseta 1500-2500)
PARAM$n_modelos <- as.integer(Sys.getenv("DMEYF_NMODELOS", unset= "50"))   # entrega final: 50 (un valor menor solo sirve para pruebas)
PARAM$corte_final <- 10000L     # clientes enviados (el bot acepta 8000 a 15000)

# [Anotación · líneas 58–61] Valores de control que el script llama anclas: 4082 positivos en 202103-04, 152
#   variables base y 760 columnas. Más adelante el script se detiene si lo que calcula no coincide con ellos.
# Anclas: si no coinciden, el dato cambio y el script se detiene.
PARAM$ancla_npos_pseudo <- 4082L     # positivos BAJA+1/BAJA+2 de 202103-04
PARAM$ancla_vars_base   <- 152L      # variables del crudo sin numero_de_cliente, foto_mes ni clase
PARAM$ancla_ncols       <- 760L      # 152 variables x (original + lag1 + delta1 + lag2 + delta2)

# [Anotación · líneas 63–74] Genera con una criba los números primos entre 100.000 y 1.000.000, fija
#   set.seed(765461) y toma n_modelos de ellos con sample(). Se detiene si hay semillas repetidas o si las cinco
#   primeras no son 125269, 175853, 691651, 593507 y 593083. Imprime las semillas.
# Semillas (metodo de la catedra): primos entre 100000 y 1000000, set.seed(primigenia), sample(primos, n).
primos_entre <- function(a, b) {
  x <- rep(TRUE, b); x[1] <- FALSE
  for (i in 2:floor(sqrt(b))) if (x[i]) x[seq(i * i, b, by= i)] <- FALSE
  p <- which(x)
  p[p >= a]
}
set.seed(PARAM$semilla_primigenia)
PARAM$semillas <- sample(primos_entre(100000L, 1000000L), PARAM$n_modelos)
if (anyDuplicated(PARAM$semillas) > 0) stop("hay semillas repetidas")
if (!all(PARAM$semillas[1:min(5, PARAM$n_modelos)] == c(125269L, 175853L, 691651L, 593507L, 593083L)[1:min(5, PARAM$n_modelos)])) stop("las semillas no coinciden con las esperadas")
cat("semillas:", PARAM$semillas, "\n")

# [Anotación · líneas 76–79] Guarda en la carpeta de salida el volcado de PARAM (PARAM.txt) y la salida de
#   sessionInfo() (sessionInfo.txt). Registra la hora de inicio y define una función que devuelve los minutos
#   transcurridos.
writeLines(capture.output(dput(PARAM)), file.path(RUTA_SALIDA, "PARAM.txt"))
writeLines(capture.output(sessionInfo()), file.path(RUTA_SALIDA, "sessionInfo.txt"))
t_inicio <- Sys.time()
minutos <- function(desde) round(as.numeric(difftime(Sys.time(), desde, units= "mins")), 1)

# [Anotación · líneas 81–88] Lee el dataset crudo con fread, imprime cantidad de filas y columnas y se detiene
#   si el archivo no existe o si falta alguno de los meses 202103 a 202106 o 202108.
# ======================================================================
# PASO 1 - LECTURA DEL DATASET CRUDO
# ======================================================================
if (!file.exists(RUTA_CRUDO)) stop("No encuentro el dataset en: ", RUTA_CRUDO)
dataset <- fread(RUTA_CRUDO)
cat("filas:", nrow(dataset), " columnas:", ncol(dataset), "\n")
faltan <- setdiff(c(PARAM$meses_final, PARAM$mes_futuro), unique(dataset$foto_mes))
if (length(faltan) > 0) stop("faltan meses en el crudo: ", paste(faltan, collapse= ", "))

# [Anotación · líneas 90–108] Calcula clase_ternaria: convierte foto_mes a un número de período correlativo
#   (año × 12 + mes), obtiene por cliente los dos períodos siguientes con shift(type = "lead") y asigna CONTINUA
#   a las filas anteriores al anteúltimo mes, BAJA+1 cuando el cliente no figura el mes siguiente y BAJA+2
#   cuando figura el mes siguiente y no a los dos meses. Devuelve la clase al dataset en su orden original y se
#   detiene si alguna fila de entrenamiento queda sin clase.
# ======================================================================
# PASO 2 - CLASE_TERNARIA (codigo de la catedra)
# ======================================================================
# BAJA+1: no esta el mes siguiente. BAJA+2: esta el mes siguiente pero no a los dos meses. CONTINUA: el resto.
# Los ultimos dos meses del crudo quedan con clase NA (falta futuro para saberla).
tabla_periodos <- dataset[, list(pos= .I, numero_de_cliente,
                                 periodo0= as.integer(foto_mes / 100) * 12 + foto_mes %% 100)]
setorder(tabla_periodos, numero_de_cliente, periodo0)
periodo_ultimo     <- tabla_periodos[, max(periodo0)]
periodo_anteultimo <- periodo_ultimo - 1
tabla_periodos[, c("periodo1", "periodo2") := shift(periodo0, n= 1:2, fill= NA, type= "lead"), numero_de_cliente]
tabla_periodos[periodo0 < periodo_anteultimo, clase_ternaria := "CONTINUA"]
tabla_periodos[periodo0 < periodo_ultimo & (is.na(periodo1) | periodo0 + 1 < periodo1), clase_ternaria := "BAJA+1"]
tabla_periodos[periodo0 < periodo_anteultimo & (periodo0 + 1 == periodo1) & (is.na(periodo2) | periodo0 + 2 < periodo2),
               clase_ternaria := "BAJA+2"]
setorder(tabla_periodos, pos)
dataset[, clase_ternaria := tabla_periodos$clase_ternaria]
rm(tabla_periodos)
if (dataset[foto_mes %in% PARAM$meses_final & is.na(clase_ternaria), .N] > 0) stop("hay filas de entrenamiento sin clase_ternaria")

# [Anotación · líneas 110–120] Pone NA en ccajas_depositos sólo en las filas de 202105. Crea clase01 con 1
#   para BAJA+1 y BAJA+2 y 0 para el resto, cuenta los positivos de 202103-04 y se detiene si no son 4082.
# ======================================================================
# PASO 3 - DATA QUALITY Y CLASE BINARIA
# ======================================================================
# ccajas_depositos esta rota en 202105 (todos ceros): NA solo en ese mes.
if (!(PARAM$dq_campo %in% names(dataset))) stop("no existe la columna ", PARAM$dq_campo)
dataset[foto_mes == PARAM$dq_mes_roto, (PARAM$dq_campo) := NA_real_]

dataset[, clase01 := ifelse(clase_ternaria %in% PARAM$clase_positiva, 1L, 0L)]
npos_pseudo <- dataset[foto_mes %in% PARAM$meses_pseudo & clase01 == 1L, .N]
cat("positivos 202103-04:", npos_pseudo, "| ancla:", PARAM$ancla_npos_pseudo, "\n")
if (npos_pseudo != PARAM$ancla_npos_pseudo) stop("la clase no coincide con el ancla: no sigo")

# [Anotación · líneas 122–127] Ordena el dataset por cliente y mes. Define las variables base como todas las
#   columnas menos numero_de_cliente, foto_mes, clase_ternaria y clase01, convierte a numérico las que no lo son
#   y se detiene si no son 152.
# orden fijo (cliente, mes): hace reproducible el orden de las filas
setorder(dataset, numero_de_cliente, foto_mes)
vars_base <- setdiff(names(dataset), c("numero_de_cliente", "foto_mes", "clase_ternaria", "clase01"))
for (v in vars_base) if (!is.numeric(dataset[[v]])) set(dataset, j= v, value= as.numeric(dataset[[v]]))
cat("variables base:", length(vars_base), "| ancla:", PARAM$ancla_vars_base, "\n")
if (length(vars_base) != PARAM$ancla_vars_base) stop("la cantidad de variables base no coincide con el ancla")

# [Anotación · líneas 129–144] Construye una clave numérica por fila (numero_de_cliente × 100.000 + período) y
#   verifica que no se repita. Con match busca, para k = 1 y 2, la fila cuya clave es la actual menos k, es
#   decir el mismo cliente k meses antes (NA si no existe). Arma los 760 nombres de columna: las 152 variables,
#   luego _lag1 y _delta1, luego _lag2 y _delta2, y verifica la cantidad.
# ======================================================================
# PASO 4 - LAGS Y DELTA LAGS DE ORDEN 1 Y 2
# ======================================================================
# Se usan los valores originales (sin ranking ni transformacion). Los NA se dejan como NA.
# lag de orden k = valor del MISMO cliente exactamente k meses calendario antes (NA si ese mes no existe).
# delta = valor actual - lag. Cada variable queda con 5 columnas: original, lag1, delta1, lag2, delta2.
id_cliente <- dataset$numero_de_cliente
mes_entero <- as.integer(dataset$foto_mes / 100) * 12L + dataset$foto_mes %% 100L
clave      <- as.numeric(id_cliente) * 1e5 + mes_entero        # clave unica cliente x mes (< 2^53)
if (anyDuplicated(clave) > 0) stop("hay mas de una fila por cliente y mes")
fila_lag <- lapply(PARAM$ordenes_lag, function(k) match(clave - k, clave))   # fila del mismo cliente k meses antes
names(fila_lag) <- PARAM$ordenes_lag
rm(clave, mes_entero)

nombres_columnas <- c(vars_base, unlist(lapply(PARAM$ordenes_lag, function(k) c(paste0(vars_base, "_lag", k), paste0(vars_base, "_delta", k)))))
if (length(nombres_columnas) != PARAM$ancla_ncols) stop("la cantidad de columnas no coincide con el ancla")

# [Anotación · líneas 146–153] Obtiene los índices de las filas de entrenamiento (202103 a 202106) y de las de
#   202108, ordenados por mes y por cliente.
# ======================================================================
# PASO 5 - MATRICES (se arman por columna para no duplicar memoria)
# ======================================================================
# Orden de filas: por mes y por cliente.
meses_dataset <- dataset$foto_mes
filas_ordenadas <- function(filas) filas[order(meses_dataset[filas], id_cliente[filas])]
filas_final  <- filas_ordenadas(which(meses_dataset %in% PARAM$meses_final))
filas_futuro <- filas_ordenadas(which(meses_dataset == PARAM$mes_futuro))

# [Anotación · líneas 155–167] Función armar_matriz: crea una matriz numérica de tantas filas como se pidan y
#   760 columnas, y la llena variable por variable con el valor original, el lag de orden k (valor de la fila
#   ubicada k meses antes) y el delta de orden k (valor actual menos lag), para k = 1 y 2.
armar_matriz <- function(filas) {
  m <- matrix(NA_real_, nrow= length(filas), ncol= length(nombres_columnas), dimnames= list(NULL, nombres_columnas))
  for (j in seq_along(vars_base)) {
    x <- dataset[[vars_base[j]]]
    m[, vars_base[j]] <- x[filas]
    for (k in PARAM$ordenes_lag) {
      lag_k <- x[fila_lag[[as.character(k)]]]
      m[, paste0(vars_base[j], "_lag", k)]   <- lag_k[filas]
      m[, paste0(vars_base[j], "_delta", k)] <- (x - lag_k)[filas]
    }
  }
  m
}

# [Anotación · líneas 169–178] Extrae la clase binaria de las filas de entrenamiento y los numero_de_cliente
#   de 202108 (se detiene si hay repetidos), arma la matriz de entrenamiento y la de 202108, elimina el dataset
#   y los índices de memoria e imprime dimensiones, cantidad de clientes y cantidad y porcentaje de positivos.
y_final    <- dataset$clase01[filas_final]
ids_futuro <- id_cliente[filas_futuro]
if (anyDuplicated(ids_futuro) > 0) stop("hay clientes repetidos en el mes a predecir")

matriz_final  <- armar_matriz(filas_final)
matriz_futuro <- armar_matriz(filas_futuro)
rm(dataset, fila_lag, filas_final, filas_futuro, meses_dataset, id_cliente)
invisible(gc(full= TRUE, verbose= FALSE))
cat(sprintf("matriz de entrenamiento: %d x %d | futuro %d: %d clientes | positivos: %d (%.2f%%)\n",
            nrow(matriz_final), ncol(matriz_final), PARAM$mes_futuro, nrow(matriz_futuro), sum(y_final), 100 * mean(y_final)))

# [Anotación · líneas 180–186] Función entrenar_modelo: une los parámetros comunes con num_iterations,
#   num_leaves = 254, min_sum_hessian_in_leaf = 4.84e-4 y la semilla, crea el lgb.Dataset con max_bin 31 y
#   feature_pre_filter = FALSE y entrena con lgb.train.
# entrena un modelo LightGBM con la semilla dada (lo unico que cambia entre modelos es la semilla)
entrenar_modelo <- function(matriz, y, arboles, semilla) {
  p <- modifyList(PARAM$lgb, list(num_iterations= arboles, num_leaves= PARAM$hojas,
                                  min_sum_hessian_in_leaf= PARAM$hessiano, seed= semilla))
  dtrain <- lgb.Dataset(matriz, label= y, params= list(feature_pre_filter= FALSE, max_bin= PARAM$lgb$max_bin))
  lgb.train(params= p, data= dtrain, nrounds= arboles)
}

# [Anotación · líneas 188–207] Arma una tabla con una fila por semilla y el nombre de su archivo de salida.
#   Para cada semilla: si modelos/prob_prof_s<semilla>.csv ya existe pasa a la siguiente; si no, entrena con la
#   matriz de 202103-202106 y 2000 árboles, predice la matriz de 202108, verifica que haya una predicción por
#   cliente y guarda numero_de_cliente y prob (escribe un .tmp y lo renombra). Imprime el tiempo de cada modelo
#   y el acumulado.
# ======================================================================
# PASO 6 - ENTRENAMIENTO FINAL (202103-06, sin undersampling) Y PREDICCION DE 202108
# ======================================================================
# Un modelo por semilla; cada uno guarda modelos/prob_prof_s<semilla>.csv. Si el archivo existe se salta (reanudable).
dir_modelos <- file.path(RUTA_SALIDA, "modelos"); dir.create(dir_modelos, showWarnings= FALSE)
plan <- data.table(semilla= PARAM$semillas)
plan[, nombre := sprintf("prof_s%d", semilla)]
plan[, archivo := file.path(dir_modelos, paste0("prob_", nombre, ".csv"))]
t_modelos <- Sys.time()
for (i in seq_len(nrow(plan))) {
  m <- plan[i]
  if (file.exists(m$archivo)) { cat(sprintf("[%d/%d] %s ya existe\n", i, nrow(plan), m$nombre)); next }
  t0 <- Sys.time()
  prob <- predict(entrenar_modelo(matriz_final, y_final, PARAM$arboles, m$semilla), matriz_futuro)
  if (length(prob) != length(ids_futuro)) stop("la prediccion no tiene una fila por cliente")
  fwrite(data.table(numero_de_cliente= ids_futuro, prob= prob), paste0(m$archivo, ".tmp"))
  file.rename(paste0(m$archivo, ".tmp"), m$archivo)
  cat(sprintf("[%d/%d] %s listo en %.1f min | acumulado %.0f min\n", i, nrow(plan), m$nombre, minutos(t0), minutos(t_modelos)))
  invisible(gc())
}

# [Anotación · líneas 209–219] Lee los archivos de probabilidades de todas las semillas y les agrega el nombre
#   del modelo. Verifica que cada modelo tenga una fila por cliente de 202108 y que no haya clientes repetidos
#   dentro de un modelo. Promedia prob por numero_de_cliente, verifica que cada promedio use todos los modelos y
#   guarda prob_ensamble_202108.csv.
# ======================================================================
# PASO 7 - ENSAMBLE (promedio simple de probabilidades por numero_de_cliente) Y CORTE
# ======================================================================
probs <- rbindlist(lapply(plan$archivo, function(f) {
  x <- fread(f); x[, modelo := sub("^prob_(.*)\\.csv$", "\\1", basename(f))]; x
}))
if (any(probs[, .N, modelo]$N != length(ids_futuro))) stop("algun modelo no tiene una fila por cliente de 202108")
if (anyDuplicated(probs[, .(modelo, numero_de_cliente)]) > 0) stop("hay clientes repetidos dentro de un modelo")
ensamble <- probs[, list(prob= mean(prob), n_modelos= .N), numero_de_cliente]
if (nrow(ensamble) != length(ids_futuro) || any(ensamble$n_modelos != nrow(plan))) stop("el promedio no uso todos los modelos")
fwrite(ensamble[, .(numero_de_cliente, prob)], file.path(RUTA_SALIDA, "prob_ensamble_202108.csv"))

# [Anotación · líneas 221–225] Ordena el ensamble por probabilidad promedio descendente, toma los primeros
#   10.000 numero_de_cliente como enteros y los escribe sin encabezado, uno por línea, en
#   entrega/ensamble/E01_prof2000_ens50m_k10000.csv (el nombre se arma con el experimento, la cantidad de
#   modelos y el corte).
# Envio: los PARAM$corte_final clientes con mayor probabilidad promedio. Un id por linea, entero, sin encabezado.
dir_ens <- file.path(RUTA_SALIDA, "entrega", "ensamble"); dir.create(dir_ens, recursive= TRUE, showWarnings= FALSE)
archivo_final <- file.path(dir_ens, sprintf("%s_ens%dm_k%d.csv", PARAM$experimento, nrow(plan), PARAM$corte_final))
ids_envio <- ensamble[order(-prob)][seq_len(PARAM$corte_final), as.integer(numero_de_cliente)]
fwrite(data.table(ids_envio), archivo_final, col.names= FALSE, quote= FALSE, scipen= 100, eol= "\n")

# [Anotación · líneas 227–234] Relee el archivo generado y verifica con stopifnot que tenga entre 8.000 y
#   15.000 líneas, que todas sean sólo dígitos, que no haya repetidos y que todos los ids sean clientes de
#   202108. Imprime el nombre del archivo, la cantidad de filas y los minutos totales.
# ======================================================================
# PASO 8 - VALIDACION DE FORMATO
# ======================================================================
# Entre 8000 y 15000 filas, solo enteros sin encabezado, sin repetidos y solo clientes de 202108.
x <- readLines(archivo_final)
stopifnot(length(x) >= 8000, length(x) <= 15000, all(grepl("^[0-9]+$", x)), !anyDuplicated(x), all(as.integer(x) %in% ids_futuro))
cat("archivo final:", archivo_final, "|", length(x), "filas | formato OK\n")
cat("FIN | minutos totales:", minutos(t_inicio), "\n")
```

### 01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R

Script del paso 1 del README, que lo declara opcional: entrena 3 modelos en 202103-04 con 4000 árboles y mide la ganancia en 202106 con siete cantidades de árboles. No escribe ningún archivo que lea modelo_final.R; el valor 2000 figura escrito en PARAM$arboles de ese script. Según el README, esta versión se limpió para el repositorio y sólo se comprobó su sintaxis; los resultados publicados son de una versión anterior del mismo código.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–11] Encabezado: indica que el script entrena 3 modelos (254 hojas, hessiano 4.84e-4)
#   con hasta 4000 árboles sobre 202103-04 y mide la ganancia en 202106 usando 1000, 1500, ..., 4000 árboles del
#   mismo modelo. Incluye el comando de uso y las variables de entorno DMEYF_CRUDO y DMEYF_EXP.
# ======================================================================
# ELECCION DEL NUMERO DE ARBOLES (pseudo-Kaggle: entrena 202103-04, evalua 202106)
# ======================================================================
# Primera Competencia DMEyF 2026: prediccion de BAJA+2 en 202108.
# Entrena 3 modelos (254 hojas, hessiano 4.84e-4) con hasta 4000 arboles sobre 202103-04 y mide la ganancia en 202106
# usando 1000, 1500, ..., 4000 arboles del mismo modelo. De ahi se elige el numero de arboles del modelo final.
# Uso:   Rscript eleccion_cantidad_de_arboles.R > arboles.log 2>&1
# Rutas (variables de entorno, opcionales):
#   DMEYF_CRUDO = ruta de competencia_01_crudo.csv   (por defecto ./competencia_01_crudo.csv)
#   DMEYF_EXP   = carpeta de salida                  (por defecto ./salida)
# Reanudable: lo que ya esta guardado en la carpeta de salida no se recalcula. No envia nada a ningun sitio.

# [Anotación · líneas 13–21] Carga data.table y el paquete de LightGBM (zlightgbm si está instalado; si no,
#   lightgbm), imprime las versiones y resuelve la ruta del dataset y la carpeta de salida desde variables de
#   entorno, con valores por defecto relativos. Crea la carpeta de salida.
suppressMessages(library(data.table))
paquete_lgb <- if (requireNamespace("zlightgbm", quietly= TRUE)) "zlightgbm" else "lightgbm"   # se uso zlightgbm 4.6.0.99
suppressMessages(library(paquete_lgb, character.only= TRUE))
cat("R:", R.version.string, "| LightGBM:", paquete_lgb, as.character(packageVersion(paquete_lgb)),
    "| data.table:", as.character(packageVersion("data.table")), "\n")

RUTA_CRUDO  <- normalizePath(Sys.getenv("DMEYF_CRUDO", unset= "competencia_01_crudo.csv"), mustWork= FALSE)
RUTA_SALIDA <- normalizePath(Sys.getenv("DMEYF_EXP",   unset= "salida"), mustWork= FALSE)
dir.create(RUTA_SALIDA, showWarnings= FALSE, recursive= TRUE)

# [Anotación · líneas 23–37] Crea la lista PARAM con los mismos valores que el script del modelo final
#   (semilla primigenia 765461, meses 202103-202106 y 202108, clase positiva BAJA+1 y BAJA+2, ccajas_depositos
#   en 202105, lags 1 y 2) y agrega los de la prueba: entrenamiento en 202103-04 y evaluación en 202106.
# ======================================================================
# PARAMETROS
# ======================================================================
PARAM <- list()
PARAM$experimento <- "E01_prof2000"
PARAM$semilla_primigenia <- 765461L                 # de ella salen todas las semillas de los modelos

PARAM$meses_final  <- c(202103, 202104, 202105, 202106)   # meses de entrenamiento del modelo final
PARAM$mes_futuro   <- 202108                              # mes a predecir
PARAM$meses_pseudo <- c(202103, 202104)                   # pseudo-Kaggle: entrena en estos meses
PARAM$mes_validar  <- 202106                              # ... y evalua en este (clase conocida)
PARAM$clase_positiva <- c("BAJA+1", "BAJA+2")             # clase01 = 1; CONTINUA = 0
PARAM$dq_campo    <- "ccajas_depositos"                   # variable rota en 202105 (todos ceros): se pone NA
PARAM$dq_mes_roto <- 202105
PARAM$ordenes_lag <- 1:2                                  # lag y delta lag de orden 1 y 2

# [Anotación · líneas 39–58] Parámetros de LightGBM iguales a los del modelo final (learning_rate 0.005,
#   feature_fraction 0.5, feature_fraction_bynode 0.2, max_bin 31, min_data_in_leaf 0, 14 hilos), 254 hojas y
#   min_sum_hessian_in_leaf 4.84e-4. Define el máximo de 4000 árboles, las siete cantidades a evaluar (1000 a
#   4000 cada 500), 3 semillas, los cortes de 9.000 a 14.000 envíos cada 500 y la ganancia por envío: 1.072.500
#   si es BAJA+2 y -27.500 en otro caso.
# LightGBM: parametros fijos (iguales en todos los modelos). num_threads fijo y explicito: 14 (corrida original).
PARAM$lgb <- list(
  boosting= "gbdt", objective= "binary", metric= "auc", first_metric_only= FALSE,
  boost_from_average= TRUE, feature_pre_filter= FALSE, force_row_wise= TRUE, verbosity= -1,
  max_depth= -1L, min_gain_to_split= 0, lambda_l1= 0, lambda_l2= 0,
  max_bin= 31L, min_data_in_leaf= 0L,
  bagging_fraction= 1, pos_bagging_fraction= 1, neg_bagging_fraction= 1,
  is_unbalance= FALSE, scale_pos_weight= 1, extra_trees= FALSE,
  learning_rate= 0.005, feature_fraction= 0.5, feature_fraction_bynode= 0.2,
  num_threads= 14L
)
# Hiperparametros del modelo. Fijados a mano; NO provienen de una optimizacion bayesiana (no hay ninguna en esta cadena).
PARAM$hojas    <- 254L          # num_leaves
PARAM$hessiano <- 4.84e-4       # min_sum_hessian_in_leaf
PARAM$arboles_max <- 4000L      # el modelo se entrena con 4000 arboles y se evalua con menos
PARAM$puntos <- c(1000L, 1500L, 2000L, 2500L, 3000L, 3500L, 4000L)   # numeros de arboles evaluados
PARAM$n_semillas <- 3L
PARAM$cortes <- seq(9000L, 14000L, by= 500L)                         # cortes usados para la meseta
PARAM$ganancia_acierto <- 1072500                                    # BAJA+2 enviado
PARAM$ganancia_error   <- -27500                                     # cualquier otro enviado

# [Anotación · líneas 60–63] Valores de control: 4082 positivos en 202103-04, 152 variables base y 760
#   columnas.
# Anclas: si no coinciden, el dato cambio y el script se detiene.
PARAM$ancla_npos_pseudo <- 4082L     # positivos BAJA+1/BAJA+2 de 202103-04
PARAM$ancla_vars_base   <- 152L      # variables del crudo sin numero_de_cliente, foto_mes ni clase
PARAM$ancla_ncols       <- 760L      # 152 variables x (original + lag1 + delta1 + lag2 + delta2)

# [Anotación · líneas 65–76] Genera los primos entre 100.000 y 1.000.000, fija set.seed(765461), toma 20 con
#   sample() y se queda con los 3 primeros. Se detiene si hay repetidos o si no son 125269, 175853 y 691651.
# Semillas (metodo de la catedra): primos entre 100000 y 1000000, set.seed(primigenia), sample(primos, n).
primos_entre <- function(a, b) {
  x <- rep(TRUE, b); x[1] <- FALSE
  for (i in 2:floor(sqrt(b))) if (x[i]) x[seq(i * i, b, by= i)] <- FALSE
  p <- which(x)
  p[p >= a]
}
set.seed(PARAM$semilla_primigenia)
PARAM$semillas <- sample(primos_entre(100000L, 1000000L), 20L)[seq_len(PARAM$n_semillas)]
if (anyDuplicated(PARAM$semillas) > 0) stop("hay semillas repetidas")
if (!all(PARAM$semillas == c(125269L, 175853L, 691651L))) stop("las semillas no coinciden con las esperadas")
cat("semillas:", PARAM$semillas, "\n")

# [Anotación · líneas 78–81] Guarda PARAM.txt y sessionInfo.txt en la carpeta de salida, registra la hora de
#   inicio y define la función que devuelve los minutos transcurridos.
writeLines(capture.output(dput(PARAM)), file.path(RUTA_SALIDA, "PARAM.txt"))
writeLines(capture.output(sessionInfo()), file.path(RUTA_SALIDA, "sessionInfo.txt"))
t_inicio <- Sys.time()
minutos <- function(desde) round(as.numeric(difftime(Sys.time(), desde, units= "mins")), 1)

# [Anotación · líneas 83–90] Lee el dataset crudo con fread, imprime filas y columnas y se detiene si el
#   archivo no existe o si falta alguno de los meses 202103 a 202106 o 202108.
# ======================================================================
# PASO 1 - LECTURA DEL DATASET CRUDO
# ======================================================================
if (!file.exists(RUTA_CRUDO)) stop("No encuentro el dataset en: ", RUTA_CRUDO)
dataset <- fread(RUTA_CRUDO)
cat("filas:", nrow(dataset), " columnas:", ncol(dataset), "\n")
faltan <- setdiff(c(PARAM$meses_final, PARAM$mes_futuro), unique(dataset$foto_mes))
if (length(faltan) > 0) stop("faltan meses en el crudo: ", paste(faltan, collapse= ", "))

# [Anotación · líneas 92–110] Calcula clase_ternaria con el mismo procedimiento que el script del modelo
#   final: período correlativo por fila, los dos períodos siguientes de cada cliente con shift(type = "lead") y
#   asignación de CONTINUA, BAJA+1 y BAJA+2. Se detiene si alguna fila de 202103-202106 queda sin clase.
# ======================================================================
# PASO 2 - CLASE_TERNARIA (codigo de la catedra)
# ======================================================================
# BAJA+1: no esta el mes siguiente. BAJA+2: esta el mes siguiente pero no a los dos meses. CONTINUA: el resto.
# Los ultimos dos meses del crudo quedan con clase NA (falta futuro para saberla).
tabla_periodos <- dataset[, list(pos= .I, numero_de_cliente,
                                 periodo0= as.integer(foto_mes / 100) * 12 + foto_mes %% 100)]
setorder(tabla_periodos, numero_de_cliente, periodo0)
periodo_ultimo     <- tabla_periodos[, max(periodo0)]
periodo_anteultimo <- periodo_ultimo - 1
tabla_periodos[, c("periodo1", "periodo2") := shift(periodo0, n= 1:2, fill= NA, type= "lead"), numero_de_cliente]
tabla_periodos[periodo0 < periodo_anteultimo, clase_ternaria := "CONTINUA"]
tabla_periodos[periodo0 < periodo_ultimo & (is.na(periodo1) | periodo0 + 1 < periodo1), clase_ternaria := "BAJA+1"]
tabla_periodos[periodo0 < periodo_anteultimo & (periodo0 + 1 == periodo1) & (is.na(periodo2) | periodo0 + 2 < periodo2),
               clase_ternaria := "BAJA+2"]
setorder(tabla_periodos, pos)
dataset[, clase_ternaria := tabla_periodos$clase_ternaria]
rm(tabla_periodos)
if (dataset[foto_mes %in% PARAM$meses_final & is.na(clase_ternaria), .N] > 0) stop("hay filas de entrenamiento sin clase_ternaria")

# [Anotación · líneas 112–122] Pone NA en ccajas_depositos sólo en 202105, crea clase01 (1 para BAJA+1 y
#   BAJA+2, 0 para el resto) y se detiene si los positivos de 202103-04 no son 4082.
# ======================================================================
# PASO 3 - DATA QUALITY Y CLASE BINARIA
# ======================================================================
# ccajas_depositos esta rota en 202105 (todos ceros): NA solo en ese mes.
if (!(PARAM$dq_campo %in% names(dataset))) stop("no existe la columna ", PARAM$dq_campo)
dataset[foto_mes == PARAM$dq_mes_roto, (PARAM$dq_campo) := NA_real_]

dataset[, clase01 := ifelse(clase_ternaria %in% PARAM$clase_positiva, 1L, 0L)]
npos_pseudo <- dataset[foto_mes %in% PARAM$meses_pseudo & clase01 == 1L, .N]
cat("positivos 202103-04:", npos_pseudo, "| ancla:", PARAM$ancla_npos_pseudo, "\n")
if (npos_pseudo != PARAM$ancla_npos_pseudo) stop("la clase no coincide con el ancla: no sigo")

# [Anotación · líneas 124–129] Ordena por cliente y mes, define las variables base (todas menos
#   numero_de_cliente, foto_mes, clase_ternaria y clase01), convierte a numérico las que no lo son y se detiene
#   si no son 152.
# orden fijo (cliente, mes): hace reproducible el orden de las filas
setorder(dataset, numero_de_cliente, foto_mes)
vars_base <- setdiff(names(dataset), c("numero_de_cliente", "foto_mes", "clase_ternaria", "clase01"))
for (v in vars_base) if (!is.numeric(dataset[[v]])) set(dataset, j= v, value= as.numeric(dataset[[v]]))
cat("variables base:", length(vars_base), "| ancla:", PARAM$ancla_vars_base, "\n")
if (length(vars_base) != PARAM$ancla_vars_base) stop("la cantidad de variables base no coincide con el ancla")

# [Anotación · líneas 131–146] Construye la clave numérica cliente × período, ubica con match la fila del
#   mismo cliente 1 y 2 meses antes y arma los 760 nombres de columna (variable, _lag1, _delta1, _lag2,
#   _delta2), verificando la cantidad.
# ======================================================================
# PASO 4 - LAGS Y DELTA LAGS DE ORDEN 1 Y 2
# ======================================================================
# Se usan los valores originales (sin ranking ni transformacion). Los NA se dejan como NA.
# lag de orden k = valor del MISMO cliente exactamente k meses calendario antes (NA si ese mes no existe).
# delta = valor actual - lag. Cada variable queda con 5 columnas: original, lag1, delta1, lag2, delta2.
id_cliente <- dataset$numero_de_cliente
mes_entero <- as.integer(dataset$foto_mes / 100) * 12L + dataset$foto_mes %% 100L
clave      <- as.numeric(id_cliente) * 1e5 + mes_entero        # clave unica cliente x mes (< 2^53)
if (anyDuplicated(clave) > 0) stop("hay mas de una fila por cliente y mes")
fila_lag <- lapply(PARAM$ordenes_lag, function(k) match(clave - k, clave))   # fila del mismo cliente k meses antes
names(fila_lag) <- PARAM$ordenes_lag
rm(clave, mes_entero)

nombres_columnas <- c(vars_base, unlist(lapply(PARAM$ordenes_lag, function(k) c(paste0(vars_base, "_lag", k), paste0(vars_base, "_delta", k)))))
if (length(nombres_columnas) != PARAM$ancla_ncols) stop("la cantidad de columnas no coincide con el ancla")

# [Anotación · líneas 148–155] Obtiene los índices de las filas de 202103 a 202106 y de las de 202108,
#   ordenados por mes y por cliente.
# ======================================================================
# PASO 5 - MATRICES (se arman por columna para no duplicar memoria)
# ======================================================================
# Orden de filas: por mes y por cliente.
meses_dataset <- dataset$foto_mes
filas_ordenadas <- function(filas) filas[order(meses_dataset[filas], id_cliente[filas])]
filas_final  <- filas_ordenadas(which(meses_dataset %in% PARAM$meses_final))
filas_futuro <- filas_ordenadas(which(meses_dataset == PARAM$mes_futuro))

# [Anotación · líneas 157–169] Función armar_matriz: llena una matriz numérica de 760 columnas con el valor
#   original, el lag y el delta (valor actual menos lag) de orden 1 y 2 de cada variable.
armar_matriz <- function(filas) {
  m <- matrix(NA_real_, nrow= length(filas), ncol= length(nombres_columnas), dimnames= list(NULL, nombres_columnas))
  for (j in seq_along(vars_base)) {
    x <- dataset[[vars_base[j]]]
    m[, vars_base[j]] <- x[filas]
    for (k in PARAM$ordenes_lag) {
      lag_k <- x[fila_lag[[as.character(k)]]]
      m[, paste0(vars_base[j], "_lag", k)]   <- lag_k[filas]
      m[, paste0(vars_base[j], "_delta", k)] <- (x - lag_k)[filas]
    }
  }
  m
}

# [Anotación · líneas 171–182] Extrae de las filas de 202103-202106 la clase binaria, la clase_ternaria y el
#   mes de cada fila, y los numero_de_cliente de 202108. Arma las dos matrices, elimina el dataset de memoria e
#   imprime dimensiones y positivos. En el resto del script la matriz de 202108 no se vuelve a usar.
y_final     <- dataset$clase01[filas_final]
clase_final <- dataset$clase_ternaria[filas_final]
meses_final <- meses_dataset[filas_final]
ids_futuro <- id_cliente[filas_futuro]
if (anyDuplicated(ids_futuro) > 0) stop("hay clientes repetidos en el mes a predecir")

matriz_final  <- armar_matriz(filas_final)
matriz_futuro <- armar_matriz(filas_futuro)
rm(dataset, fila_lag, filas_final, filas_futuro, meses_dataset, id_cliente)
invisible(gc(full= TRUE, verbose= FALSE))
cat(sprintf("matriz de entrenamiento: %d x %d | futuro %d: %d clientes | positivos: %d (%.2f%%)\n",
            nrow(matriz_final), ncol(matriz_final), PARAM$mes_futuro, nrow(matriz_futuro), sum(y_final), 100 * mean(y_final)))

# [Anotación · líneas 184–188] Función curva_ganancia: ordena por probabilidad descendente y devuelve la
#   ganancia acumulada, sumando 1.072.500 por cada BAJA+2 y -27.500 por cada fila de otra clase.
# ganancia acumulada al enviar los k mejores
curva_ganancia <- function(prob, clase) {
  o <- order(-prob)
  cumsum(ifelse(clase[o] == "BAJA+2", PARAM$ganancia_acierto, PARAM$ganancia_error))
}

# [Anotación · líneas 190–196] Función entrenar_modelo: une los parámetros comunes con num_iterations,
#   num_leaves = 254, min_sum_hessian_in_leaf = 4.84e-4 y la semilla, crea el lgb.Dataset con max_bin 31 y
#   entrena con lgb.train.
# entrena un modelo LightGBM con la semilla dada (lo unico que cambia entre modelos es la semilla)
entrenar_modelo <- function(matriz, y, arboles, semilla) {
  p <- modifyList(PARAM$lgb, list(num_iterations= arboles, num_leaves= PARAM$hojas,
                                  min_sum_hessian_in_leaf= PARAM$hessiano, seed= semilla))
  dtrain <- lgb.Dataset(matriz, label= y, params= list(feature_pre_filter= FALSE, max_bin= PARAM$lgb$max_bin))
  lgb.train(params= p, data= dtrain, nrounds= arboles)
}

# [Anotación · líneas 198–219] Separa de la matriz las filas de 202103-04 (entrenamiento) y las de 202106
#   (evaluación, con su clase_ternaria). Para cada una de las 3 semillas: si existe pseudo_prof_s<semilla>.rds
#   lo lee; si no, entrena con 4000 árboles, predice 202106 con los primeros 1000, 1500, ..., 4000 árboles
#   (argumento num_iteration de predict) y guarda la matriz de probabilidades, una columna por cantidad de
#   árboles, en ese .rds.
# ======================================================================
# PASO 6 - PSEUDO-KAGGLE: ENTRENA EN 202103-04 Y EVALUA EN 202106 (clase conocida)
# ======================================================================
# Un modelo por semilla entrenado con PARAM$arboles_max; se predice con distintos numeros de arboles (num_iteration)
# y se mide la ganancia media entre 9000 y 14000 envios (la "meseta"), para cada semilla y para el promedio de ellas.
i_tr <- which(meses_final %in% PARAM$meses_pseudo)
i_te <- which(meses_final == PARAM$mes_validar)
Xtr <- matriz_final[i_tr, , drop= FALSE]; ytr <- y_final[i_tr]
Xte <- matriz_final[i_te, , drop= FALSE]; clase_te <- clase_final[i_te]
cat("PSEUDO-KAGGLE: train", nrow(Xtr), "filas ->", PARAM$mes_validar, nrow(Xte), "filas\n")
probs_sem <- list()
for (s in seq_len(PARAM$n_semillas)) {
  f_rds <- file.path(RUTA_SALIDA, sprintf("pseudo_prof_s%d.rds", PARAM$semillas[s]))
  if (file.exists(f_rds)) { probs_sem[[s]] <- readRDS(f_rds); cat("semilla", PARAM$semillas[s], "ya hecha\n"); next }
  t0 <- Sys.time()
  mod <- entrenar_modelo(Xtr, ytr, PARAM$arboles_max, PARAM$semillas[s])
  probs_sem[[s]] <- sapply(PARAM$puntos, function(it) predict(mod, Xte, num_iteration= it))
  colnames(probs_sem[[s]]) <- PARAM$puntos
  saveRDS(probs_sem[[s]], f_rds)
  cat(sprintf("semilla %d lista en %.1f min\n", PARAM$semillas[s], minutos(t0)))
  rm(mod); invisible(gc())
}
# [Anotación · líneas 220–229] Para cada cantidad de árboles calcula, en millones: el promedio entre semillas
#   de la ganancia media en los 11 cortes de 9.000 a 14.000 envíos (meseta_ind_media_M); la misma medida sobre
#   el promedio de probabilidades de las 3 semillas (meseta_ens_M); la ganancia máxima de ese promedio
#   (max_ens_M), la cantidad de envíos donde ocurre (envios_max) y la ganancia a 10.000 envíos (g10000_M).
#   Imprime la tabla, la guarda en pseudo_profundo_por_arboles.csv e imprime un texto fijo que dice que la
#   decisión es manual y que el valor del modelo final es 2000.
res <- rbindlist(lapply(seq_along(PARAM$puntos), function(p) {
  g_ind <- sapply(probs_sem, function(m) mean(curva_ganancia(m[, p], clase_te)[PARAM$cortes]) / 1e6)
  g_ens <- curva_ganancia(rowMeans(sapply(probs_sem, function(m) m[, p])), clase_te)
  data.table(arboles= PARAM$puntos[p], meseta_ind_media_M= mean(g_ind), meseta_ens_M= mean(g_ens[PARAM$cortes]) / 1e6,
             max_ens_M= max(g_ens) / 1e6, envios_max= which.max(g_ens), g10000_M= g_ens[10000] / 1e6)
}))
print(res)
fwrite(res, file.path(RUTA_SALIDA, "pseudo_profundo_por_arboles.csv"))
cat("Decision (manual): el numero de arboles del modelo final (2000) es el centro de la meseta de mayor ganancia (1500-2500).\n")
cat("FIN | minutos totales:", minutos(t_inicio), "\n")
```


## Explicaciones del alumno (texto original)

### README.md

> # Primera Competencia DMEyF 2026 - Entrega final
>
> Prediccion de BAJA+2 en el mes 202108 (churn bancario). La entrega es **un solo archivo**: los **10.000** clientes con mayor
> probabilidad promedio de un ensamble de **50 modelos LightGBM** que solo se diferencian en la semilla.
>
> - Nombre del submit: `E01prof_ens50`
> - Archivo entregado: `E01_prof2000_ens50m_k10000.csv` (esta en `resultado_esperado/`)
> - La entrega se hizo por el bot de Zulip (`@competencia-uno`), no por Kaggle.
>
> ## Enfoque
>
> - Variables: las 152 variables originales del dataset (valores crudos, NA sin tocar) mas **lag y delta lag de orden 1 y 2**
>   de cada una (760 columnas). Sin ranking, sin undersampling, sin seleccion de variables.
> - Data quality: `ccajas_depositos` se pone en `NA` solo en 202105 (mes en el que viene toda en cero).
> - Clase: 1 si `clase_ternaria` es BAJA+1 o BAJA+2; 0 si es CONTINUA. `clase_ternaria` se calcula con el codigo de la catedra.
> - Entrenamiento: 202103 a 202106. Prediccion: 202108.
> - Modelo: LightGBM, 254 hojas, 2000 arboles, 50 semillas distintas con identicos hiperparametros. Ensamble por promedio simple de
>   probabilidades por `numero_de_cliente`. Se envian los 10.000 mejores.
>
> ## Hiperparametros: de donde salen (leer con atencion)
>
> **No hay una optimizacion bayesiana en esta cadena.** No existe un log de BO del que se tomen los hiperparametros.
>
> | Hiperparametro | Valor | Como se fijo |
> |---|---|---|
> | learning_rate | 0.005 | fijo, segun los tips de la catedra |
> | max_bin | 31 | fijo, segun los tips de la catedra |
> | min_data_in_leaf | 0 | fijo, segun los tips de la catedra |
> | feature_fraction | 0.50 | fijo, segun los tips de la catedra |
> | feature_fraction_bynode | 0.20 | fijo, segun los tips de la catedra |
> | metric | auc | fijo, segun los tips de la catedra |
> | num_leaves | 254 | **fijado a mano** |
> | min_sum_hessian_in_leaf | 4.84e-4 | **fijado a mano** |
> | num_iterations | 2000 | elegido con la corrida `01_eleccion_cantidad_de_arboles` (decision manual sobre sus resultados) |
>
> Para el numero de arboles, `01_eleccion_cantidad_de_arboles` entrena 3 modelos con 254 hojas y hessiano 4.84e-4 sobre 202103-04,
> con hasta 4000 arboles, y mide la ganancia en 202106 (mes con clase conocida) con 1000 a 4000 arboles del mismo modelo. La ganancia
> media entre 9000 y 14000 envios del ensamble de las 3 semillas fue (millones): 389,2 con 1000 arboles; 395,4 con 1500; 393,1 con 2000;
> 392,8 con 2500; 389,3 con 3000; 387,6 con 3500; 386,6 con 4000. Se tomo **2000**, el centro de la meseta de 1500 a 2500, y no el pico.
> El resultado de la corrida original esta en `01_eleccion_cantidad_de_arboles/log_original/`.
>
> El corte de **10.000** envios se fijo a mano dentro de lo que acepta el bot (8000 a 15000).
>
> ## Estructura
>
> ```
> README.md
> .gitignore
> resultado_esperado/
>     E01_prof2000_ens50m_k10000.csv           archivo exacto subido como entrega final
>     MD5.txt, SHA256.txt                      huellas del archivo
> 01_eleccion_cantidad_de_arboles/
>     eleccion_cantidad_de_arboles.R           script (opcional: solo justifica los 2000 arboles)
>     log_original/                            log, PARAM y resultado de la corrida original
> 02_modelo_final/
>     modelo_final.R                           script: del dataset crudo al archivo final
>     log_original/                            logs de las 3 corridas encadenadas y PARAM original
> ```
>
> ## Requisitos y versiones
>
> - R 4.3.1 (ucrt, Windows 11), `data.table` 1.14.8 y `zlightgbm` 4.6.0.99 (el paquete LightGBM de la catedra; si no esta, el script usa
>   `lightgbm`, pero el resultado puede variar). Sistema: Windows 11 x64, R 4.3.1 (ucrt), `Matrix` 1.5-4.1, `jsonlite` 1.8.7.
> - Instalacion de zlightgbm: `install.packages("https://storage.googleapis.com/open-courses/dmeyf2025-e4a2/zlightgbm_4.6.0.99.tar.gz", repos = NULL, type = "source")`
> - RAM: la matriz de entrenamiento (654.066 filas x 760 columnas) ocupa unos 4 GB; el proceso llega a 7 GB. Recomendados 16 GB.
> - Threads: `num_threads = 14` fijo en el script (la corrida original uso 14 hilos en una PC de 16 nucleos).
>
> ## Dataset
>
> No se incluye en el repositorio. Se descarga de la catedra:
>
> ```bash
> wget https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv
> ```
>
> MD5 del archivo usado: `b6f759764c5d04cbf068548517ae1249`.
>
> ## Como reproducir (orden de ejecucion)
>
> Poner `competencia_01_crudo.csv` en la carpeta desde donde se ejecuta (o definir `DMEYF_CRUDO`) y, opcionalmente, `DMEYF_EXP` para la salida
> (por defecto `./salida`).
>
> | Paso | Comando | Produce | Tiempo aprox. |
> |---|---|---|---|
> | 1 (opcional) | `Rscript 01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R` | `salida/pseudo_profundo_por_arboles.csv` | 55 min |
> | 2 | `Rscript 02_modelo_final/modelo_final.R` | 50 archivos `salida/modelos/prob_prof_s<semilla>.csv` y `salida/entrega/ensamble/E01_prof2000_ens50m_k10000.csv` | 10 a 12 h (12 a 15 min por modelo) |
> | 3 | `md5sum salida/entrega/ensamble/E01_prof2000_ens50m_k10000.csv` y comparar con `resultado_esperado/MD5.txt` | MD5 del archivo generado | segundos |
>
> El paso 1 no alimenta al paso 2: es la evidencia de la eleccion de los 2000 arboles, que en el paso 2 figura en `PARAM$arboles`.
> El script del paso 2 es reanudable: si se corta, se vuelve a ejecutar y salta los modelos ya terminados.
>
> **Aclaracion sobre la BO.** Como no hay BO, no hay un paso "(a) todo desde la BO". La unica ruta es la de arriba, que parte del dataset crudo.
> La cadena original se corrio en tres tandas del mismo script (modelos 1 a 5, luego hasta 20 y luego hasta 50, reutilizando los modelos ya
> terminados); los tres logs estan en `02_modelo_final/log_original/`.
>
> ## Verificacion realizada
>
> No se repitio la corrida completa (50 modelos, unas 10 a 12 horas). Se verifico asi:
>
> 1. **Reproduccion de modelos.** Con una sesion nueva de R, desde el dataset crudo y con el script `02_modelo_final/modelo_final.R` limpio
>    (con `DMEYF_NMODELOS=2`), se reentrenaron los dos primeros modelos (semillas 125269 y 175853) en la misma maquina y con 14 hilos.
>    Los archivos de probabilidades resultantes tienen el **mismo MD5** que los de la corrida original:
>
>    | Modelo | MD5 reproducido | MD5 original |
>    |---|---|---|
>    | `prob_prof_s125269.csv` | a047f5c7a1fc6d6f11c7fe8683028689 | a047f5c7a1fc6d6f11c7fe8683028689 |
>    | `prob_prof_s175853.csv` | fa94c6f765ab90386dde4af729eb6f4f | fa94c6f765ab90386dde4af729eb6f4f |
>
> 2. **Tramo posterior a los modelos.** A partir de las 50 probabilidades guardadas de la corrida original, el promedio por cliente y los 10.000
>    mejores dan exactamente los mismos ids y en el mismo orden que el archivo entregado.
> 3. **Lo que no se verifico.** No se reentrenaron los otros 48 modelos. El script `01_eleccion_cantidad_de_arboles/eleccion_cantidad_de_arboles.R`
>    se limpio para este repositorio y solo se comprobo que su sintaxis es valida; sus resultados son los de la corrida original
>    (`01_eleccion_cantidad_de_arboles/log_original/`), que se hizo con una version anterior del mismo codigo.
>    El archivo entregado es la reunion de las tres tandas descritas arriba; el paso de unirlas es el de la verificacion 2.
>
> ## Sobre la reproduccion exacta
>
> LightGBM no se corrio con `deterministic = TRUE` y entrena con varios hilos. Con otra cantidad de hilos, otra version del paquete u otro
> sistema operativo es posible que las probabilidades cambien en los ultimos decimales y que algunos clientes del borde del corte de 10.000
> cambien. El archivo generado debe tener el MD5 de `resultado_esperado/MD5.txt`; si no coincide, conviene comparar cuantos ids tienen en comun.

