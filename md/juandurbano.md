# Juan Durbano — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: JuanDUrbano
- Repositorio: https://github.com/JuanDUrbano/dmeyf2026
- Link posteado: https://github.com/JuanDUrbano/dmeyf2026/tree/main/competencia_01_entrega
- Commit: f98898c2cc442c66f6559c0ed4fa677913d009b3
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/juandurbano/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/juandurbano.json

## Resumen

La entrega es la carpeta competencia_01_entrega, con un script en R (E780_entrega.R, 892 líneas) y un README. El script parte del crudo de la competencia, calcula clase_ternaria, pasa a NA ccajas_depositos en 202105 y reemplaza las 152 variables por su ranking con cero fijo dentro de cada mes, más los lags y deltas de orden 1 y 2 de esos rankings (760 columnas). Busca tres hiperparámetros de LightGBM (num_iterations, num_leaves y min_sum_hessian_in_leaf) evaluando 10 puntos de un hipercubo latino: entrena con 202103 y 202104 (202105 queda afuera de la búsqueda), sin las columnas de préstamos personales (750 columnas), mide AUC en 202106 y toma el punto de mayor AUC. Con esa configuración calcula una curva de ganancia en 202106 con 5 semillas. Después entrena 109 modelos con 202103 a 202106, sin submuestreo y con clase binaria (BAJA+1 y BAJA+2 positivos), que sólo difieren en la semilla; predice 202108, promedia las probabilidades por cliente y escribe un archivo por cada corte entre 8.000 y 15.000 (cada 500). Según el README, el archivo entregado es el del corte 11.000.

**Qué entrega.** Según el README, el archivo entregado es E780_ens109m_k11000_20261011.csv: los 11.000 clientes de mayor probabilidad promedio de 109 modelos LightGBM, un numero_de_cliente por línea y sin encabezado. El archivo no está en el repositorio; el script lo genera en colab_replica/C1-E780-PR2108-final/entrega/ensamble/, junto con los archivos de los otros 14 cortes.

**Cómo se ejecuta.** Según el README: crear una carpeta de trabajo vacía, poner en ella el crudo con el nombre competencia_01_crudo.csv (983.061 filas, 154 columnas), copiar E780_entrega.R y correr desde esa carpeta 'Rscript E780_entrega.R > E780.log 2>&1'. Los resultados quedan en colab_replica/C1-E780-PR2108-final/. Las variables de entorno DMEYF_CRUDO y DMEYF_EXP permiten indicar otras rutas. El README indica que la corrida es reanudable (saltea lo ya terminado) y declara un tiempo total aproximado de 17,5 horas, de las cuales 16,5 corresponden a los 109 modelos.

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase01): positivo = BAJA+1 o BAJA+2, negativo = CONTINUA. clase_ternaria se calcula en el script a partir de la presencia de cada cliente en los dos meses siguientes.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se submuestrea: PARAM$us y PARAM$us_bo valen 1.0 y el script se detiene si alguno es distinto de 1.0.
- **Calidad de datos:** ccajas_depositos se pasa a NA en 202105 (el código la describe como rota, todo cero, en ese mes), antes de calcular el ranking. Los NA se dejan como NA. No se elimina ninguna columna del crudo (PARAM$excluir está vacío).
- **Drifting:** Cada una de las 152 variables se reemplaza por su ranking dentro de cada mes con cero fijo: los positivos pasan a rango/cantidad de positivos, en (0, 1]; los negativos a menos el rango del valor absoluto/cantidad de negativos, en [-1, 0); el cero queda en cero y los NA quedan NA (frank con empates promediados). Las variables originales no entran al modelo.
- **Variables dentro del mes:** No se observa en el código: dentro del mes sólo se calcula el ranking de cada variable.
- **Variables históricas:** Lag 1 y lag 2 del ranking (valor del mismo cliente exactamente 1 y 2 meses calendario antes; NA si ese mes no existe) y delta 1 y delta 2 (ranking del mes menos cada lag). Cada variable deja 5 columnas: 152 x 5 = 760.
- **Selección de variables:** No hay selección por importancia. En la búsqueda de hiperparámetros se dejan afuera las columnas derivadas de cprestamos_personales y mprestamos_personales (750 columnas); en el modelo final entran las 760. numero_de_cliente y foto_mes no son variables del modelo.
- **Optimización de hiperparámetros:** El código la nombra BO y evalúa únicamente el diseño inicial de 10 puntos, sin iteraciones posteriores (así lo indica el propio script): un hipercubo latino elegido entre 2.000 sorteos por tener la mayor distancia mínima entre puntos (semilla 106937). Rangos: num_iterations 600 a 3500, num_leaves 16 a 128, min_sum_hessian_in_leaf 0,0005 a 0,03. Cada punto se entrena con 202103 y 202104 completos, una semilla (106937) y 750 columnas, y se mide el AUC en 202106. Se toma el punto de mayor AUC.
- **Hiperparámetros finales:** Fijos en el código: objective binary, metric auc, boosting gbdt, max_bin 31, min_data_in_leaf 0, feature_fraction 0,50, feature_fraction_bynode 0,20, learning_rate 0,005, boost_from_average, deterministic y force_row_wise en TRUE, feature_pre_filter en FALSE, verbosity -100, num_threads 16. Los otros tres (num_leaves, min_sum_hessian_in_leaf y num_iterations) se leen de bo_mejor_config.csv, que genera el propio script; según el README y un comentario del script, en la corrida entregada fueron num_leaves 45, min_sum_hessian_in_leaf 0,0244994712564396 y num_iterations 2428.
- **Semillas:** Semilla primigenia 106937. Con set.seed(106937) se sortean 1.000 primos entre 100.000 y 1.000.000 y se usan los primeros 109, en orden; el script compara los primeros 20 con una lista escrita en el código y se detiene si difieren. La búsqueda de hiperparámetros usa la semilla 106937 y la curva de junio, las primeras 5 de la lista.
- **Cantidad de semillas:** 109
- **Ensamble:** Media sin ponderar de la columna prob de todos los archivos prob_*.csv de la carpeta modelos/, agrupando por numero_de_cliente; el script se detiene si algún cliente no tiene un valor por cada modelo. Con el plan completo son 109 modelos, que tienen los mismos hiperparámetros y sólo cambian la semilla.
- **Corte:** Cantidad fija de clientes, ordenados por probabilidad promedio. El script no elige un corte: escribe un archivo del ensamble por cada uno de los 15 cortes de 8.000 a 15.000 (paso 500). El valor 11.000 está escrito en PARAM$k_por_modelo (corte de los archivos por modelo) y en el texto de cierre de la ficha, que nombra como entregado el archivo k11000. Según el README, se entregó el corte 11.000, elegido combinando la curva de cortes en el leaderboard público, la curva de ganancia en 202106 y el puntaje público.
- **Validación:** Un solo corte temporal, sin validación cruzada: entrena con 202103 y 202104 y valida en 202106 completo; 202105 no entra en la búsqueda. En cada evaluación calcula el AUC (por rangos) y la curva de ganancia en los cortes 8.000 a 15.000, con 1.072.500 por cada BAJA+2 y -27.500 por cualquier otro envío; la configuración se elige por AUC y la curva de ganancia se guarda aparte. La configuración elegida se evalúa además en 202106 con 5 semillas y con el promedio de sus probabilidades. Según el README, el AUC en 202106 de la configuración elegida es 0,917295 y el del promedio de 5 semillas, 0,91792.
- **Salidas:** En colab_replica/C1-E780-PR2108-final/: bo_diseno.csv, bo_evaluaciones_<id>.csv, bo_top_configs.csv y bo_mejor_config.csv; curva_ganancia_junio.csv, junio_curvas_por_semilla.csv y junio_probabilidades.csv; modelos/prob_modelo_s<semilla>.csv (probabilidad de cada cliente de 202108, un archivo por modelo); log_modelos_<id>.csv; FICHA, PARAM y sessionInfo en archivos de texto; entrega/ensamble/ (15 archivos, uno por corte), entrega/por_modelo/ (corte 11.000 para las primeras 20 semillas) y entrega/barrido_cortes/corte_<k>/ (las primeras 20 semillas en cada corte).

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Búsqueda en grilla o al azar (`hiperparametros.grilla_o_azar`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README: R 4.6.1 en Windows 11 x64, lightgbm 4.7.0 de CRAN (no zlightgbm), data.table 1.18.6.1; notebook con Ryzen 7 7435HS, 16 hilos y 16 GB de RAM. El script se detiene si lightgbm no es 4.7.0, fija num_threads en 16 y guarda la salida de sessionInfo() en un archivo. Las rutas de una PC y de una máquina virtual aparecen sólo en líneas comentadas.

## Pasos del camino de la entrega

1. **Paquetes, versión de LightGBM y rutas.** Carga data.table y lightgbm, se detiene si la versión de lightgbm no es 4.7.0 y define la ruta del crudo (competencia_01_crudo.csv en la carpeta de trabajo) y la de resultados (subcarpeta colab_replica), que se pueden reemplazar con las variables de entorno DMEYF_CRUDO y DMEYF_EXP. (`competencia_01_entrega/E780_entrega.R` líneas 28–61)
2. **Parámetros del experimento.** Reúne en la lista PARAM los meses (entrenamiento final 202103 a 202106, predicción 202108, búsqueda con 202103 y 202104 y validación en 202106), la clase positiva, la variable a pasar a NA, los hiperparámetros fijos de LightGBM, los rangos de la búsqueda, la cantidad de semillas (109), los cortes (8.000 a 15.000 cada 500) y los valores esperados de control. (`competencia_01_entrega/E780_entrega.R` líneas 67–146)
3. **Lista de semillas.** Genera los primos entre 100.000 y 1.000.000, sortea 1.000 con set.seed(106937), verifica que los primeros 20 coincidan con una lista escrita en el código y toma los primeros 109 como semillas de los modelos. (`competencia_01_entrega/E780_entrega.R` líneas 149–174)
4. **Lectura del crudo.** Lee el CSV con fread, imprime la cantidad de registros por mes y se detiene si falta alguno de los meses 202103 a 202108 o si hay columnas de texto. (`competencia_01_entrega/E780_entrega.R` líneas 319–329)
5. **Cálculo de clase_ternaria.** Calcula CONTINUA, BAJA+1 y BAJA+2 según la presencia del cliente en los dos meses siguientes y se detiene si algún registro de 202103 a 202106 queda sin clase. (`competencia_01_entrega/E780_entrega.R` líneas 336–352)
6. **Calidad de datos y clase binaria.** Pasa ccajas_depositos a NA sólo en 202105, antes del ranking, y no elimina ninguna columna del crudo. Crea clase01 = 1 para BAJA+1 y BAJA+2 y se detiene si los positivos de 202103 a 202105 no son 6.095. (`competencia_01_entrega/E780_entrega.R` líneas 358–371; `competencia_01_entrega/E780_entrega.R` líneas 374–379)
7. **Ranking con cero fijo por variable y por mes.** Para cada una de las 152 variables y cada mes calcula un ranking en el que los positivos quedan en (0, 1], los negativos en [-1, 0), el cero en cero y los NA en NA, y lo guarda en una columna nueva con sufijo _rank. (`competencia_01_entrega/E780_entrega.R` líneas 404–432)
8. **Lags y deltas de orden 1 y 2 sobre los rankings.** Antes del ranking calcula, para cada fila, la posición de la fila del mismo cliente 1 y 2 meses calendario antes. Los valores se calculan al armar cada matriz: por variable, el lag 1, el delta 1, el lag 2 y el delta 2 del ranking. Quedan 5 columnas por variable: 760 para el modelo final y 750 para la búsqueda, que no incluye los préstamos personales. (`competencia_01_entrega/E780_entrega.R` líneas 395–399; `competencia_01_entrega/E780_entrega.R` líneas 444–452; `competencia_01_entrega/E780_entrega.R` líneas 470–488)
9. **Búsqueda de hiperparámetros con un diseño de 10 puntos.** Genera 10 combinaciones de num_iterations, num_leaves y min_sum_hessian_in_leaf con un hipercubo latino, entrena cada una con 202103 y 202104 (semilla 106937, 750 columnas, sin submuestreo), mide el AUC y la curva de ganancia en 202106 y guarda en bo_mejor_config.csv la de mayor AUC. (`competencia_01_entrega/E780_entrega.R` líneas 547–557; `competencia_01_entrega/E780_entrega.R` líneas 564–641)
10. **Curva de ganancia en 202106 con la configuración elegida.** Entrena 5 modelos con las primeras 5 semillas sobre 202103 y 202104, predice 202106 y calcula la ganancia en cada corte para cada semilla y para el promedio de las 5 probabilidades. Según el README, esta curva no interviene en la predicción; según el texto DECISIONES del script, se usa junto con la curva de cortes del bot para decidir el corte. (`competencia_01_entrega/E780_entrega.R` líneas 540–544; `competencia_01_entrega/E780_entrega.R` líneas 644–677)
11. **Matrices finales y baja de las variables originales.** Lee la configuración elegida, arma la matriz de entrenamiento (202103 a 202106) y la de 202108 con las 760 columnas, elimina del dataset las variables originales y verifica que todas las columnas del modelo deriven de un ranking. (`competencia_01_entrega/E780_entrega.R` líneas 685–727)
12. **Entrenamiento de 109 modelos, uno por semilla.** Construye una vez el lgb.Dataset y entrena un modelo por semilla con los mismos hiperparámetros. Cada modelo predice 202108 y guarda numero_de_cliente y probabilidad en modelos/prob_modelo_s<semilla>.csv; los modelos cuyo archivo ya existe se saltean. (`competencia_01_entrega/E780_entrega.R` líneas 735–782)
13. **Ensamble por promedio de probabilidades.** Lee las probabilidades de todos los modelos terminados, verifica que cada uno tenga una fila por cliente de 202108 y calcula la media por numero_de_cliente. (`competencia_01_entrega/E780_entrega.R` líneas 806–817)
14. **Archivos por corte.** Escribe un archivo del ensamble por cada corte de 8.000 a 15.000 (cada 500) con los clientes de mayor probabilidad, y además archivos por modelo de las primeras 20 semillas: con corte 11.000 en por_modelo y con cada corte en barrido_cortes. (`competencia_01_entrega/E780_entrega.R` líneas 821–845)
15. **Validación de formato.** Verifica que cada archivo generado tenga entre 8.000 y 15.000 filas, sólo enteros sin encabezado, sin repetidos y sólo clientes de 202108, y se detiene si alguno no cumple. (`competencia_01_entrega/E780_entrega.R` líneas 853–871)

## Archivos

- `competencia_01_entrega/E780_entrega.R` · principal · R · 892 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/juandurbano/competencia_01_entrega/E780_entrega.R.txt) — Script único que va del crudo a los archivos de envío: clase, ranking con cero fijo por mes, lags y deltas, búsqueda de hiperparámetros con 10 puntos, curva de ganancia en 202106, 109 modelos LightGBM, promedio de probabilidades, un archivo por corte y validación de formato.
- `competencia_01_entrega/README.md` · explicacion · Markdown · 149 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/juandurbano/competencia_01_entrega/README.md.txt) — Texto de presentación de la entrega: qué archivo se entregó, versiones de R y de los paquetes, cómo correr el script, tiempos de ejecución declarados, los 10 pasos del script, los controles y la tabla de AUC esperados al replicar, los 7 cambios respecto del script original y cómo se eligió el corte de 11.000.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### competencia_01_entrega/E780_entrega.R

Script único que va del crudo a los archivos de envío: clase, ranking con cero fijo por mes, lags y deltas, búsqueda de hiperparámetros con 10 puntos, curva de ganancia en 202106, 109 modelos LightGBM, promedio de probabilidades, un archivo por corte y validación de formato.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] Encabezado en comentarios: enumera los 7 cambios hechos para la entrega, marcados
#   [ENTREGA 1] a [ENTREGA 7] (paquete, rutas, hilos, semillas, copia de archivos, línea de respaldo y nombres),
#   y el orden de los 13 pasos del script, desde la lectura del crudo hasta la validación de formato de los
#   archivos.
# ======================================================================
# E780 - PREDICCION FINAL DE LA COMPETENCIA 1 (DMEyF 2026)
#
# CAMBIOS PARA LA ENTREGA: marcados [ENTREGA n]. La linea ORIGINAL queda comentada con "#" y debajo esta la nueva.
#   [ENTREGA 1] Paquete: se fuerza lightgbm 4.7.0 (el original elegia zlightgbm si estaba instalado).
#   [ENTREGA 2] Rutas: relativas a la carpeta de trabajo (el original tenia las rutas locales de mi PC y de mi VM).
#   [ENTREGA 3] Hilos: num_threads = 16, los que uso LightGBM en mi notebook (el original no lo fijaba).
#   [ENTREGA 4] Semillas: las primeras 109 de la lista (el original entrenaba hasta que se creaba PARAR.txt, y paro en 109).
#   [ENTREGA 5] Se quita la copia de archivos ya calculados: la BO, la curva de junio y los 109 modelos se hacen aca.
#   [ENTREGA 6] Linea de respaldo (comentada) que fija la configuracion que eligio la BO, por si la BO eligiera otra.
#   [ENTREGA 7] Nombres: se cambiaron el nombre de la carpeta del experimento y el prefijo de los archivos de cada modelo
#               (modelos/prob_modelo_s<semilla>.csv). No afecta el calculo: el archivo de entrega se llama igual.
#
# ORDEN DE LOS PASOS
#   1 lectura del crudo -> 2 clase_ternaria -> 3 dq1 (NA en ccajas_depositos de 202105) y clase01
#   -> 4 ranking por variable y por mes con cero fijo (columnas nuevas, TODAS las variables, prestamos incluidos)
#   -> 5 lags y delta lags 1 y 2 de los rankings -> 6 se eliminan las variables originales (valores crudos)
#   -> 7 BO sin undersampling (train 202103-04, validacion 202106, AUC, 750 columnas sin prestamos) + curva de ganancia de junio
#   -> 8 entrenamiento final 202103-06 sin undersampling con los prestamos reincorporados (760 columnas)
#   -> 9 N semillas con los mismos hiperparametros -> 10 promedio de probabilidades por cliente
#   -> 11 barrido de cortes 8000-15000 -> 12 ensamble en un unico archivo por corte -> 13 validacion de formato.
#   (Las matrices de la BO se arman con los rankings antes de borrar las originales; el borrado ocurre al final del armado.)
#

# [Anotación · líneas 25–41] Vacía el entorno de R y carga data.table. Fija el paquete en lightgbm, detiene el
#   script si la versión instalada no es 4.7.0 o si el paquete falta, y lo carga. La línea 34, comentada, es la
#   versión original, que elegía zlightgbm cuando estaba instalado.
# ======================================================================
# LIBRERIAS Y RUTAS
# ======================================================================
rm(list= ls(all.names= TRUE))
invisible(gc(full= TRUE, verbose= FALSE))

suppressMessages(library(data.table))
# El paquete usado queda escrito en el log y en la ficha.
# [ENTREGA 1] ORIGINAL (elegia zlightgbm si estaba instalado; en mi notebook no lo estaba, asi que se uso lightgbm 4.7.0):
# pkg_lgb <- Sys.getenv("DMEYF_LGB", unset= if (requireNamespace("zlightgbm", quietly= TRUE)) "zlightgbm" else "lightgbm")
# [ENTREGA 1] NUEVO: siempre lightgbm, y se exige la version 4.7.0 (otra version puede dar otras predicciones)
pkg_lgb <- "lightgbm"
if (requireNamespace(pkg_lgb, quietly= TRUE) && as.character(packageVersion(pkg_lgb)) != "4.7.0") {
  stop("Se necesita lightgbm 4.7.0 (la version con la que se genero la entrega). Version instalada: ", as.character(packageVersion(pkg_lgb)))
}
if (!requireNamespace(pkg_lgb, quietly= TRUE)) stop("Falta el paquete ", pkg_lgb, ": ver la linea de instalacion de zlightgbm arriba o install.packages('lightgbm')")
suppressMessages(library(pkg_lgb, character.only= TRUE))

# [Anotación · líneas 43–61] Define las rutas: el crudo se busca como competencia_01_crudo.csv en la carpeta
#   de trabajo y los resultados van a la subcarpeta colab_replica; las variables de entorno DMEYF_CRUDO y
#   DMEYF_EXP las reemplazan si están definidas. Las líneas 44 a 51, comentadas, son las rutas originales de una
#   PC con Windows y de una máquina virtual. Imprime la versión de R, de lightgbm y de data.table, el sistema y
#   la cantidad de núcleos.
# [ENTREGA 2] ORIGINAL (rutas locales de mi PC y de mi VM; solo funcionan ahi):
# if (.Platform$OS.type == "windows") {
#   PATH_CRUDO <- "C:/Users/Invitadisimos/Desktop/materia/competencia_01_crudo.csv"
#   PATH_EXP   <- "C:/Users/Invitadisimos/Desktop/materia/01_competencia1/colab_replica"
# } else {
#   base_vm <- if (dir.exists("/home/ds/dmeyf2026")) "/home/ds/dmeyf2026" else path.expand("~/dmeyf2026")
#   PATH_CRUDO <- file.path(base_vm, "competencia_01_crudo.csv")
#   PATH_EXP   <- file.path(base_vm, "colab_replica")
# }
# [ENTREGA 2] NUEVO: el crudo en la carpeta de trabajo y los resultados en la subcarpeta colab_replica (rutas absolutas desde getwd()).
PATH_CRUDO <- file.path(getwd(), "competencia_01_crudo.csv")
PATH_EXP   <- file.path(getwd(), "colab_replica")
# para pruebas: se pueden pisar con variables de entorno
if (nzchar(Sys.getenv("DMEYF_CRUDO"))) PATH_CRUDO <- Sys.getenv("DMEYF_CRUDO")
if (nzchar(Sys.getenv("DMEYF_EXP")))   PATH_EXP   <- Sys.getenv("DMEYF_EXP")

cat("R:", R.version.string, "| paquete LightGBM:", pkg_lgb, as.character(packageVersion(pkg_lgb)),
    "| data.table:", as.character(packageVersion("data.table")), "\n")
cat("sistema:", .Platform$OS.type, "| nucleos:", parallel::detectCores(), "\n")

# [Anotación · líneas 63–90] Abre la lista PARAM: experimento 780, identificador C1-E780-PR2108-final y
#   semilla primigenia 106937. Meses: entrenamiento final 202103 a 202106, predicción 202108, búsqueda de
#   hiperparámetros con entrenamiento en 202103 y 202104 y validación en 202106. Submuestreo en 1.0 (ninguno) en
#   ambos casos. Clase positiva: BAJA+1 y BAJA+2. Variable a pasar a NA: ccajas_depositos en 202105. La lista de
#   exclusión está vacía; cprestamos_personales y mprestamos_personales se declaran aparte para sacarlos sólo de
#   la búsqueda. numero_de_cliente no entra como variable y el ranking del mes sí.
# ======================================================================
# PARAM (todo lo que define el experimento esta aca)
# ======================================================================
# Cualquier cambio de metodologia se hace SOLO en este bloque; el resto del script no tiene numeros "escondidos".
PARAM <- list()
PARAM$experimento <- 780L                      # identificador del experimento (nombre de la carpeta y de los archivos)
PARAM$nombre <- "final"                        # nombre del experimento (carpeta C1-E780-PR2108-final)
PARAM$id <- sprintf("C1-E%03d-PR2108-%s", PARAM$experimento, PARAM$nombre)
PARAM$semilla_primigenia <- 106937L            # MI semilla primigenia

# meses
PARAM$train  <- c(202103, 202104, 202105, 202106)   # entrenamiento FINAL
PARAM$future <- 202108                               # mes a predecir
PARAM$bo$train <- c(202103, 202104)                  # BO: train en los meses 3 y 4; 202105 queda afuera
PARAM$bo$valid <- 202106                             # BO: validar contra el mes 6

# undersampling de los CONTINUA: 1.0 = ninguno. La BO y el entrenamiento final van SIN undersampling;
# el script se detiene si alguno es distinto de 1.0.
PARAM$us    <- 1.0                             # entrenamiento final
PARAM$us_bo <- 1.0                             # BO

PARAM$clase_positiva <- c("BAJA+1", "BAJA+2")  # clase01 = 1
PARAM$dq1$campo    <- "ccajas_depositos"       # Data Quality: NA solo en el mes roto
PARAM$dq1$mes_roto <- 202105
PARAM$excluir <- character(0)                  # no se elimina ninguna variable del dataset (los prestamos se sacan SOLO de la BO, ver abajo)
PARAM$prestamos <- c("cprestamos_personales", "mprestamos_personales")   # fuera de la BO, dentro del final (ya rankeados)
PARAM$id_como_feature <- FALSE                 # numero_de_cliente NO entra como feature
PARAM$rank_actual_como_feature <- TRUE         # el ranking del mes SI entra (lo que se saca son las variables ORIGINALES, con valores crudos)

# [Anotación · líneas 92–111] Hiperparámetros de LightGBM que no se buscan: objective binary, metric auc,
#   boosting gbdt, boost_from_average, force_row_wise y deterministic en TRUE, feature_pre_filter en FALSE,
#   verbosity -100, max_bin 31, min_data_in_leaf 0, feature_fraction 0.50, feature_fraction_bynode 0.20,
#   learning_rate 0.005 y num_threads 16. Los comentarios [ENTREGA 3] indican que num_threads no estaba en la
#   versión original.
# hiperparametros FIJOS de LightGBM
PARAM$lgb <- list(
  objective= "binary",
  metric= "auc",
  boosting= "gbdt",
  boost_from_average= TRUE,
  feature_pre_filter= FALSE,
  force_row_wise= TRUE,
  deterministic= TRUE,
  verbosity= -100,
  max_bin= 31L,
  min_data_in_leaf= 0L,                        # muy importante
  feature_fraction= 0.50,
  feature_fraction_bynode= 0.20,
  # [ENTREGA 3] ORIGINAL (ultima linea de la lista):  learning_rate= 0.005                         # muy importante
  learning_rate= 0.005,                        # muy importante
  # [ENTREGA 3] ORIGINAL: no habia num_threads (LightGBM usaba los 16 hilos de mi notebook: Ryzen 7 7435HS, 16 hilos).
  # [ENTREGA 3] NUEVO: se fija en 16 para que en otra maquina se use la misma cantidad de hilos que en la corrida entregada.
  num_threads= 16L
)

# [Anotación · líneas 113–146] Parámetros de la búsqueda: 10 puntos de diseño, 2.000 sorteos de hipercubos,
#   num_iterations entre 600 y 3500, num_leaves entre 16 y 128, min_sum_hessian_in_leaf entre 0.0005 y 0.03.
#   Curva de junio con 5 semillas. Plan de semillas: lista de 1.000, de la que se usan las posiciones 1 a 109;
#   los archivos por modelo y el barrido se limitan a las primeras 20. Corte de los archivos por modelo: 11.000;
#   cortes del barrido: 8.000 a 15.000 cada 500. Valores esperados de control: 6.095 positivos en 202103-05, 152
#   variables, 760 columnas del modelo final y 750 de la búsqueda; según el comentario, sólo el primero detiene
#   el script y los demás avisan. Detiene el script si hay submuestreo, si el mes de validación está en el
#   entrenamiento de la búsqueda o si no está entre los meses del entrenamiento final.
# hiperparametros BAYESIANOS: num_iterations, num_leaves, min_sum_hessian_in_leaf. Puntos del diseno de la BO y rangos:
PARAM$bo$n_diseno   <- 10L
PARAM$bo$n_sorteos  <- 2000L
PARAM$bo$iter_min  <- 600L;   PARAM$bo$iter_max  <- 3500L
PARAM$bo$hojas_min <- 16L;    PARAM$bo$hojas_max <- 128L
PARAM$bo$hess_min  <- 0.0005; PARAM$bo$hess_max  <- 0.03

# Curva de ganancia en 202106 con la configuracion elegida: n_semillas modelos entrenados en 202103-04 (mismas columnas que la BO)
PARAM$junio$n_semillas <- 5L

# semillas: se arma una lista de max_semillas semillas y se entrenan EN ORDEN las indicadas en semillas_idx. Con la misma primigenia,
# sample(primos, n) empieza siempre con las mismas semillas para cualquier n (se verifica mas abajo).
# Si se crea el archivo PARAR.txt en la carpeta del experimento, termina el modelo en curso y pasa al armado de archivos.
PARAM$max_semillas <- 1000L
# [ENTREGA 4] ORIGINAL (se entrenaba en orden hasta que se creaba PARAR.txt; la corrida entregada paro con 109 modelos):
# PARAM$semillas_idx <- seq_len(PARAM$max_semillas)
# [ENTREGA 4] NUEVO: las primeras 109 de la MISMA lista de 1000 (son exactamente las semillas de los 109 modelos de la entrega).
PARAM$semillas_idx <- 1:109
PARAM$barrido_max_modelos <- 20L               # archivos por_modelo y barrido de cortes solo de las primeras 20 semillas (tope del bot)

# envios: rango valido del bot 8000 a 15000, paso de 500.
PARAM$k_por_modelo <- 11000L                   # corte de los archivos por_modelo
PARAM$cortes <- seq(8000L, 15000L, by= 500L)   # barrido de cortes

# anclas de reproducibilidad: valores esperados; sirven para detectar que cambio el dato o la clase.
# npos frena el script si no coincide; los demas solo avisan.
PARAM$ancla$npos_202103_05 <- 6095L            # BAJA+1 y BAJA+2 de 202103-05
PARAM$ancla$vars_base <- 152L                  # variables base del crudo (sin numero_de_cliente ni foto_mes)
PARAM$ancla$ncols_final <- 760L                # 152 variables x 5 (ranking + lag1 + delta1 + lag2 + delta2)
PARAM$ancla$ncols_bo <- 750L                   # 150 variables (sin los 2 prestamos) x 5

if (PARAM$us != 1 || PARAM$us_bo != 1) stop("la BO y el entrenamiento final van SIN undersampling (us y us_bo = 1.0)")
if (PARAM$bo$valid %in% PARAM$bo$train) stop("la validacion de la BO no puede estar en su train")
if (!(PARAM$bo$valid %in% PARAM$train)) stop("el mes de validacion de la BO tiene que estar entre los meses de train")

# [Anotación · líneas 148–177] Genera los primos entre 100.000 y 1.000.000 con una criba y, con
#   set.seed(106937), sortea 20, 50, 100 y 1.000 de ellos. Compara los primeros 20 con una lista escrita en el
#   código y verifica que cada sorteo más largo empiece con las mismas semillas y no tenga repetidas; si algo
#   difiere, se detiene. Las semillas del plan son las primeras 109 de la lista de 1.000. La variable de entorno
#   E780_SOLO_ARMAR=1 activa un modo que no entrena y sólo arma los archivos con los modelos ya guardados.
# ---- semillas ----
primos_entre <- function(a, b) {
  x <- rep(TRUE, b)
  x[1] <- FALSE
  for (i in 2:floor(sqrt(b))) if (x[i]) x[seq(i * i, b, by= i)] <- FALSE
  p <- which(x)
  p[p >= a]
}
primos <- primos_entre(100000L, 1000000L)
set.seed(PARAM$semilla_primigenia); semillas20 <- sample(primos, 20)
esperadas20 <- c(388891L, 458219L, 587417L, 312289L, 394501L, 687683L, 207497L, 539347L, 455989L, 687779L,
                 308093L, 633271L, 618883L, 882653L, 435769L, 786433L, 781493L, 570467L, 363277L, 531337L)
if (!all(semillas20 == esperadas20)) stop("las 20 primeras semillas NO coinciden con las esperadas: no sigo")
set.seed(PARAM$semilla_primigenia); semillas50 <- sample(primos, 50)
if (!all(semillas50[1:20] == semillas20)) stop("sample(primos, 50) no empieza con las mismas 20: no sigo")
if (anyDuplicated(semillas50) > 0) stop("hay semillas repetidas")
# verificacion de que la lista se extiende sin cambiar sus primeras semillas (50 -> 100 -> max_semillas)
set.seed(PARAM$semilla_primigenia); semillas100 <- sample(primos, 100)
if (!all(semillas100[1:50] == semillas50)) stop("sample(primos, 100) no empieza con las mismas 50: no sigo")
if (anyDuplicated(semillas100) > 0) stop("hay semillas repetidas en las 100")
# lista larga de max_semillas semillas
set.seed(PARAM$semilla_primigenia); semillas_max <- sample(primos, PARAM$max_semillas)
if (!all(semillas_max[1:100] == semillas100)) stop("sample(primos, max_semillas) no empieza con las mismas 100: no sigo")
if (anyDuplicated(semillas_max) > 0) stop("hay semillas repetidas en la lista larga")
if (anyDuplicated(PARAM$semillas_idx) > 0 || any(PARAM$semillas_idx < 1L | PARAM$semillas_idx > PARAM$max_semillas)) stop("semillas_idx debe ser un subconjunto de 1:max_semillas sin repetidos")
PARAM$semillas <- semillas_max[PARAM$semillas_idx]
cat("semillas del plan (", length(PARAM$semillas), "; las primeras 100 verificadas). Primeras 10:", PARAM$semillas[1:10], "\n")

SOLO_ARMAR <- identical(Sys.getenv("E780_SOLO_ARMAR"), "1")   # 1 = no entrena ni arma matrices: solo ensambla lo que haya y arma los archivos
if (SOLO_ARMAR) cat("*** MODO SOLO_ARMAR: no se entrena nada, se arman los archivos con los modelos ya terminados ***\n")

# [Anotación · líneas 179–224] Crea la carpeta del experimento (colab_replica/C1-E780-PR2108-final) y la fija
#   como directorio de trabajo. Las líneas 189 a 212, comentadas, son el bloque original que copiaba de la
#   carpeta de otra corrida (E765) la configuración de la búsqueda, las curvas de junio y los modelos ya
#   entrenados. Avisa si existe PARAR.txt, arma una marca de fecha y hora y define ficha(), que imprime un texto
#   y lo agrega al archivo FICHA_<id>_<marca>.txt.
# ======================================================================
# CARPETA DEL EXPERIMENTO, FICHA Y AUXILIARES
# ======================================================================
dir_exp <- file.path(PATH_EXP, PARAM$id)
dir.create(dir_exp, showWarnings= FALSE, recursive= TRUE)
setwd(dir_exp)
cat("carpeta del experimento:", getwd(), "\n")

# [ENTREGA 5] ORIGINAL: se copiaban de la carpeta de una corrida anterior (hecha con este mismo codigo) la BO, la curva de junio y
# los modelos ya entrenados, y el script frenaba si no los encontraba. En la entrega se quita: este script hace todo desde el crudo.
# # ---- E780: se COPIA (nunca se pisa) lo ya hecho en E765: config de la BO, curvas de junio y probabilidades de los modelos ----
# # Asi no se repite la BO ni se reentrenan los modelos ya terminados. Si la carpeta de E765 no esta y aca no hay base, el script frena.
# dir_origen <- file.path(PATH_EXP, PARAM$origen_id)
# if (dir.exists(dir_origen)) {
#   dir.create(file.path(dir_exp, "modelos"), showWarnings= FALSE, recursive= TRUE)
#   planos <- list.files(dir_origen, pattern= "^(bo_.*|curva_ganancia_junio|junio_.*)\\.csv$")
#   planos_dest <- sub(PARAM$origen_id, PARAM$id, planos, fixed= TRUE)
#   mods <- list.files(file.path(dir_origen, "modelos"), pattern= "^prob_.*\\.csv$")
#   n_copiados <- 0L
#   for (i_ in seq_along(planos)) {
#     dst <- file.path(dir_exp, planos_dest[i_])
#     if (!file.exists(dst)) { file.copy(file.path(dir_origen, planos[i_]), dst); n_copiados <- n_copiados + 1L }
#   }
#   for (m_ in mods) {
#     dst <- file.path(dir_exp, "modelos", m_)
#     if (!file.exists(dst)) { file.copy(file.path(dir_origen, "modelos", m_), dst); n_copiados <- n_copiados + 1L }
#   }
#   cat("copiado desde", PARAM$origen_id, ":", n_copiados, "archivos nuevos (", length(mods), "modelos en el origen )\n")
# } else cat("AVISO: no existe la carpeta de origen", dir_origen, "\n")
# if (!file.exists(file.path(dir_exp, "bo_mejor_config.csv")) ||
#     length(list.files(file.path(dir_exp, "modelos"), pattern= "^prob_.*\\.csv$")) == 0) {
#   stop("E780 necesita bo_mejor_config.csv y los prob_*.csv ya entrenados en su carpeta (se copian de E765): ",
#        "si no, reentrenaria todo de cero. Copialos a ", dir_exp, " y volve a lanzar.")
# }
# [ENTREGA 5] NUEVO: no se copia nada; si la carpeta del experimento ya tiene modelos terminados, se reutilizan (el script es reanudable).

f_parar <- file.path(dir_exp, "PARAR.txt")
if (file.exists(f_parar)) cat("AVISO: ya existe PARAR.txt: no se va a entrenar ningun modelo nuevo (borralo para que siga entrenando)\n")
marca <- format(Sys.time(), "%Y%m%d_%H%M%S")
f_ficha <- file.path(dir_exp, paste0("FICHA_", PARAM$id, "_", marca, ".txt"))

# la FICHA queda en el .log (porque se imprime) y en un .txt dentro de la carpeta del experimento
ficha <- function(lineas) {
  cat(paste0(lineas, collapse= "\n"), "\n", sep= "")
  cat(paste0(lineas, collapse= "\n"), "\n", file= f_ficha, append= TRUE, sep= "")
}

# [Anotación · líneas 226–254] Vector de texto DECISIONES con las definiciones del experimento en prosa:
#   meses, búsqueda sin submuestreo y con una semilla, métrica AUC, tratamiento de los préstamos personales,
#   ranking con cero fijo, lags y deltas, 760 columnas, promedio de 109 semillas, cortes de 8.000 a 15.000 y la
#   indicación de que no se usan clase artificial, pesos de recencia ni eutanasia.
# Tabla de decisiones (se imprime en el log y queda en la FICHA)
DECISIONES <- c(
  "  Se predice 202108. Entrenamiento final = 202103+04+05+06 SIN undersampling.",
  "  BO: train en 202103+04, validacion en 202106. 202105 queda afuera de la BO.",
  "  La BO es SIN undersampling y con UNA semilla, la primigenia.",
  "  La BO es solo el diseno inicial de 10 puntos, sin iteraciones inteligentes. Se elige la mejor por AUC.",
  "  Metrica AUC. Fijos: max_bin 31, min_data_in_leaf 0, feature_fraction 0.5, feature_fraction_bynode 0.2, learning_rate 0.005.",
  "  Bayesianos: num_iterations, num_leaves, min_sum_hessian_in_leaf. Rangos 600-3500 arboles, 16-128 hojas, hessiano 0.0005-0.03.",
  "  Train en 202103+04 y validacion en 202106 (un solo corte temporal): SIN cross validation.",
  "  PRESTAMOS PERSONALES (cprestamos_personales, mprestamos_personales): se eliminan SOLO para la BO (750 columnas); en el entrenamiento final se",
  "      reincorporan YA RANKEADOS (ranking + lags + deltas; nunca en crudo) al dataset con que se optimizaron los hiperparametros: 760 columnas.",
  "  Los prestamos se rankean junto con las demas variables desde el inicio y la BO usa solo las columnas de las otras 150 variables (equivalente: el ranking es por variable).",
  "  dq1: ccajas_depositos esta rota en 202105 (todo cero) -> NA solo en ese mes. Se aplica ANTES del ranking.",
  "  clase01 = 1 si clase_ternaria es BAJA+1 o BAJA+2.",
  "  Ranking por variable y por mes con cero fijo (positivos 0 a 1, negativos -1 a 0, el 0 queda 0) en todas las variables menos numero_de_cliente, foto_mes y clase_ternaria. NA se dejan como NA.",
  "  Primero el ranking, luego lags y delta lags de orden 1 y 2, y luego se sacan las variables originales (valores crudos, con drift).",
  "  El ranking del mes actual SI queda como feature: 152 variables x 5 columnas = 760.",
  "  Lag de orden k = valor del mismo cliente exactamente k meses calendario antes (NA si ese mes no existe; con train en 202103-04 el lag2 queda en NA).",
  "  numero_de_cliente y foto_mes NO son features.",
  "  Las N semillas usan los MISMOS hiperparametros; se promedian las probabilidades por numero_de_cliente (promedio simple).",
  "  Semillas: primigenia 106937, sin repetidas. Ensamble final de 109 semillas (menos variabilidad entre semillas).",
  "  Para decidir el corte: curva de cortes (bot) y envios optimos en junio. Se calcula la curva de ganancia en 202106 para las 10 configuraciones de la BO (1 semilla cada una) y para la elegida (5 semillas + ensamble).",
  "      Se guardan las curvas por semilla y las probabilidades de junio (junio_curvas_por_semilla.csv, junio_probabilidades.csv).",
  "  Cortes entre 8000 y 15000, paso de 500. Los archivos por_modelo usan el corte 11000.",
  "  Un archivo por modelo con el mismo corte en cada carpeta del barrido y UN archivo final del ensamble. Elegir el corte por la forma de la curva y no por el pico.",
  "  por_modelo y barrido de cortes solo para las primeras 20 semillas (el bot acepta hasta 20 archivos por submit); el ensamble usa todas las semillas terminadas.",
  "  No se usa clase artificial, ni pesos de recencia, ni eutanasia.",
  "  deterministic= TRUE, force_row_wise= TRUE, boost_from_average= TRUE."
)

# [Anotación · líneas 256–297] Escribe en el log y en el archivo FICHA la descripción del experimento: los 9
#   pasos del pipeline armados con los valores de PARAM, los hiperparámetros fijos, los rangos de la búsqueda,
#   las primeras 10 semillas, el vector DECISIONES y el paquete usado. Guarda además PARAM completo (dput) y la
#   salida de sessionInfo() en archivos de texto dentro de la carpeta del experimento.
ficha(c(
  "",
  paste(rep("=", 78), collapse= ""),
  paste0("FICHA DEL EXPERIMENTO ", PARAM$id, "   (", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), ")"),
  paste(rep("=", 78), collapse= ""),
  "PIPELINE (en orden):",
  "  1. Lectura del crudo y clase_ternaria.",
  sprintf("  2. Data Quality dq1: %s = NA solo en %d. NO se elimina ninguna variable del dataset. Los NA se dejan como NA.", PARAM$dq1$campo, PARAM$dq1$mes_roto),
  "  3. Ranking por variable y por mes con CERO FIJO, en columnas nuevas (<variable>_rank), sobre las 152 variables (prestamos incluidos).",
  "  4. Lags y delta lags de orden 1 y 2 calculados SOBRE los rankings (valor del cliente 1 y 2 meses calendario antes; NA si ese mes no existe).",
  "  5. Se eliminan las variables ORIGINALES (valores crudos). Cada variable deja 5 columnas: ranking del mes, lag1, delta1, lag2 y delta2.",
  sprintf("  6. BO SIN undersampling: train %s -> validacion %d, metrica AUC, sin CV, 1 semilla, %d puntos de diseno, SIN los prestamos personales (%d columnas).",
          paste(PARAM$bo$train, collapse= "+"), PARAM$bo$valid, PARAM$bo$n_diseno, PARAM$ancla$ncols_bo),
  sprintf("     Curva de ganancia en %d para las %d configuraciones y para la elegida (%d semillas + ensamble).", PARAM$bo$valid, PARAM$bo$n_diseno, PARAM$junio$n_semillas),
  sprintf("  7. Entrenamiento final: %s SIN undersampling, CON los prestamos reincorporados ya rankeados (%d columnas); aplicado a %d.",
          paste(PARAM$train, collapse= "+"), PARAM$ancla$ncols_final, PARAM$future),
  # [ENTREGA 4] ORIGINAL (texto de la ficha):
  # "  8. Modelos que solo cambian la semilla (mismos hiperparametros), sin limite hasta PARAR.txt. Promedio simple de PROBABILIDADES por numero_de_cliente.",
  "  8. 109 modelos que solo cambian la semilla (mismos hiperparametros; las primeras 109 de la lista). Promedio simple de PROBABILIDADES por numero_de_cliente.",
  sprintf("  9. Barrido de cortes %d a %d cada %d (primeras %d semillas). Ensamble final = UN archivo con un solo corte.",
          min(PARAM$cortes), max(PARAM$cortes), PARAM$cortes[2] - PARAM$cortes[1], PARAM$barrido_max_modelos),
  "",
  "HIPERPARAMETROS FIJOS (LightGBM):",
  paste0("  ", names(PARAM$lgb), " = ", sapply(PARAM$lgb, function(z) format(z)), collapse= "\n"),
  sprintf("HIPERPARAMETROS BAYESIANOS: num_iterations [%d,%d] | num_leaves [%d,%d] | min_sum_hessian_in_leaf [%g,%g]",
          PARAM$bo$iter_min, PARAM$bo$iter_max, PARAM$bo$hojas_min, PARAM$bo$hojas_max, PARAM$bo$hess_min, PARAM$bo$hess_max),
  sprintf("  BO: solo el diseno inicial de %d puntos, sin iteraciones inteligentes.", PARAM$bo$n_diseno),
  "",
  "SEMILLAS: las primeras 109 de la lista generada con la primigenia 106937.",
  sprintf("  semillas: %d (se entrenan en orden); primeras 10: %s", length(PARAM$semillas), paste(PARAM$semillas[1:10], collapse= " ")),
  "",
  "DECISIONES:",
  DECISIONES,
  "",
  sprintf("PAQUETE LightGBM usado: %s %s.", pkg_lgb, as.character(packageVersion(pkg_lgb))),
  "No se envia nada a Zulip desde este script.",
  paste(rep("=", 78), collapse= ""),
  ""
))

writeLines(capture.output(dput(PARAM)), file.path(dir_exp, paste0("PARAM_", PARAM$id, "_", marca, ".txt")))
writeLines(capture.output(sessionInfo()), file.path(dir_exp, paste0("sessionInfo_", PARAM$id, "_", marca, ".txt")))

# [Anotación · líneas 299–311] Define reporte_ram(), que en sistemas con /proc lee la memoria del proceso (RSS
#   y pico) y la disponible y total del sistema y las imprime con el nombre de la etapa; en otros sistemas
#   imprime que la medición no está disponible. La llama con la etiqueta inicio y registra la hora de inicio.
reporte_ram <- function(etapa) {
  if (!file.exists("/proc/self/status")) { cat("[RAM]", etapa, "(medicion no disponible en este sistema)\n"); return(invisible(NULL)) }
  leer <- function(archivo, clave) {
    x <- readLines(archivo); x <- x[grepl(paste0("^", clave, ":"), x)]
    as.numeric(sub("^\\S+\\s+(\\d+).*$", "\\1", x, perl= TRUE)) / 1024
  }
  cat(sprintf("[RAM] %-34s RSS %6.0f MB | pico R %6.0f MB | sistema disponible %6.0f de %6.0f MB\n", etapa,
              leer("/proc/self/status", "VmRSS"), leer("/proc/self/status", "VmHWM"),
              leer("/proc/meminfo", "MemAvailable"), leer("/proc/meminfo", "MemTotal")))
  invisible(NULL)
}
reporte_ram("inicio")
t_script <- Sys.time()

# [Anotación · líneas 313–329] Abre el bloque que se ejecuta salvo en modo SOLO_ARMAR. Lee el crudo con fread,
#   imprime filas, columnas y cantidad de registros por mes, y se detiene si falta el archivo, si falta alguno
#   de los meses 202103 a 202108 o si hay columnas de texto.
if (!SOLO_ARMAR) {   # ---- todo lo que sigue hasta "fin de la cadena" se saltea con E780_SOLO_ARMAR=1 ----
# ======================================================================
# PASO 1 - LECTURA DEL CRUDO
# ======================================================================
# Se lee con fread. Controles: estan los meses necesarios (train, 202107 y el mes a predecir) y no hay columnas de texto
# (LightGBM solo recibe numericas).
if (!file.exists(PATH_CRUDO)) stop("No encuentro el crudo en: ", PATH_CRUDO)
dataset <- fread(PATH_CRUDO)
cat("filas:", nrow(dataset), " columnas:", ncol(dataset), "\n")
print(dataset[, .N, foto_mes][order(foto_mes)])

faltan <- setdiff(c(PARAM$train, 202107, PARAM$future), unique(dataset$foto_mes))
if (length(faltan) > 0) stop(paste("faltan meses en el crudo:", paste(faltan, collapse= ", ")))
if (any(sapply(dataset, is.character))) {
  stop(paste("hay columnas de texto en el crudo:", paste(names(dataset)[sapply(dataset, is.character)], collapse= ", ")))
}
reporte_ram("crudo leido")

# [Anotación · líneas 331–352] Calcula clase_ternaria: numera los meses como enteros consecutivos, ordena por
#   cliente y mes y obtiene los dos períodos siguientes de cada cliente. Asigna CONTINUA a los registros
#   anteriores al anteúltimo mes; BAJA+1, en todos los meses menos el último, si el cliente no tiene registro en
#   el mes siguiente; y BAJA+2, en los meses anteriores al anteúltimo, si está en el siguiente pero no en el
#   subsiguiente. En el anteúltimo mes sólo se asigna BAJA+1 y el resto queda en NA; el último mes queda entero
#   en NA. Imprime la tabla de mes por clase y se detiene si algún registro de los meses de entrenamiento queda
#   sin clase.
# ======================================================================
# PASO 2 - CLASE_TERNARIA
# ======================================================================
# BAJA+1: el cliente no esta el mes siguiente. BAJA+2: esta el mes siguiente pero no a los dos meses. CONTINUA: el resto.
# Los ultimos meses del crudo quedan con clase NA porque faltan meses futuros para saberla.
dsimple <- dataset[, list(
    "pos" = .I,
    numero_de_cliente,
    periodo0 = as.integer(foto_mes/100)*12 +  foto_mes%%100 ) ]
setorder( dsimple, numero_de_cliente, periodo0 )
periodo_ultimo <- dsimple[, max(periodo0) ]
periodo_anteultimo <- periodo_ultimo - 1
dsimple[, c("periodo1", "periodo2") := shift(periodo0, n=1:2, fill=NA, type="lead"), numero_de_cliente ]
dsimple[ periodo0 < periodo_anteultimo, clase_ternaria := "CONTINUA" ]
dsimple[ periodo0 < periodo_ultimo & ( is.na(periodo1) | periodo0 + 1 < periodo1 ), clase_ternaria := "BAJA+1" ]
dsimple[ periodo0 < periodo_anteultimo & (periodo0+1 == periodo1 ) & ( is.na(periodo2) | periodo0 + 2 < periodo2 ),
         clase_ternaria := "BAJA+2" ]
setorder( dsimple, pos )
dataset[, clase_ternaria := dsimple$clase_ternaria ]
rm(dsimple)
print(dataset[, .N, list(foto_mes, clase_ternaria)][order(foto_mes, clase_ternaria)])
if (dataset[foto_mes %in% PARAM$train & is.na(clase_ternaria), .N] > 0) stop("hay registros de los meses de train SIN clase_ternaria")

# [Anotación · líneas 354–379] Pasa ccajas_depositos a NA en 202105 e imprime cuántos valores no NA quedan en
#   ese mes. La lista de exclusión está vacía, así que no elimina columnas; verifica que existan las dos
#   variables de préstamos personales. Crea clase01 (1 si clase_ternaria es BAJA+1 o BAJA+2, 0 en otro caso),
#   cuenta los positivos de 202103 a 202105 y se detiene si no son 6.095.
# ======================================================================
# PASO 3 - DATA QUALITY (dq1), EXCLUSIONES Y CLASE BINARIA
# ======================================================================
# Orden: dq1 va ANTES del ranking, porque el ranking tomaria el valor roto de ccajas_depositos como si fuera real.
if (PARAM$dq1$campo %in% names(dataset)) {
  dataset[foto_mes == PARAM$dq1$mes_roto, (PARAM$dq1$campo) := NA]
  cat("dq1: no-NA de", PARAM$dq1$campo, "en", PARAM$dq1$mes_roto, "=",
      dataset[foto_mes == PARAM$dq1$mes_roto, sum(!is.na(get(PARAM$dq1$campo)))], "(debe ser 0)\n")
} else stop("no existe la columna ", PARAM$dq1$campo)

# Exclusion de variables del dataset: PARAM$excluir esta vacio, asi que NO se elimina ninguna columna del crudo.
# (Los prestamos personales NO se eliminan aca: se rankean con todas las demas y se sacan solo de la matriz de la BO.)
excl <- intersect(PARAM$excluir, names(dataset))
if (length(excl) > 0) {
  cat("excluyo:", paste(excl, collapse= ", "), "\n")
  dataset[, (excl) := NULL]
} else cat("no se excluye ninguna variable del dataset\n")
if (!all(PARAM$prestamos %in% names(dataset))) stop("no estan en el crudo los prestamos personales: ", paste(PARAM$prestamos, collapse= ", "))

# clase binaria: 1 = BAJA+1 o BAJA+2 (lo que el modelo aprende a predecir); 0 = CONTINUA
dataset[, clase01 := ifelse(clase_ternaria %in% PARAM$clase_positiva, 1L, 0L)]
# ancla: cantidad de positivos en 202103-05. Si no coincide con el valor esperado, el dato o la clase cambiaron y el script se detiene.
npos_ancla <- dataset[foto_mes %in% c(202103, 202104, 202105) & clase01 == 1L, .N]
cat("npos 202103-05 =", npos_ancla, "| ancla =", PARAM$ancla$npos_202103_05,
    if (npos_ancla == PARAM$ancla$npos_202103_05) "-> OK\n" else "-> *** DIFIERE ***\n")
if (npos_ancla != PARAM$ancla$npos_202103_05) stop("la clase no coincide con el ancla (npos 202103-05): no sigo")

# [Anotación · líneas 381–408] Ordena el dataset por cliente y mes. Arma una clave numérica de cliente y mes
#   y, con match, obtiene para cada fila la posición de la fila del mismo cliente 1 mes y 2 meses calendario
#   antes (NA si no existe); se detiene si hay más de una fila por cliente y mes. Define la lista de variables a
#   rankear (todas menos numero_de_cliente, foto_mes, clase_ternaria y clase01) y los nombres de sus columnas
#   _rank, e informa si son 152.
# ======================================================================
# PASOS 4 Y 5 - RANKING Y LAGS / DELTA LAGS  (la baja de las originales es el PASO 6, mas abajo)
# ======================================================================
# Orden: (4) ranking por mes -> (5) lags y delta lags SOBRE los rankings -> (6) se eliminan las variables
# originales (valores crudos), para que el arbol no pueda cortar por ellas (tienen drift, por ejemplo el aguinaldo de 202106).
# El modelo ve SOLO columnas derivadas de rankings. Se rankean las 152 variables, prestamos incluidos.
t_fe <- Sys.time()
setorder(dataset, numero_de_cliente, foto_mes)   # orden fijo (cliente, mes): hace reproducible el orden de filas
N   <- nrow(dataset)
cli <- dataset$numero_de_cliente
i   <- seq_len(N)

# ---- indices de los lags (se usan al armar las matrices) ----
# lag de orden k = valor del MISMO cliente exactamente k meses calendario antes (NA si ese mes no existe)
per <- as.integer(dataset$foto_mes / 100) * 12L + dataset$foto_mes %% 100L   # mes como numero entero consecutivo
clave <- as.numeric(cli) * 1e5 + per                  # clave unica cliente x mes; < 2^53, asi que es exacta
if (anyDuplicated(clave) > 0) stop("hay mas de una fila por cliente y mes")
idx1 <- match(clave - 1, clave)                       # fila del MISMO cliente en el mes anterior (NA si no existe)
idx2 <- match(clave - 2, clave)                       # fila del MISMO cliente hace dos meses (NA si no existe)
rm(clave, per)

# ---- variables a rankear ----
# todas menos numero_de_cliente, foto_mes, clase_ternaria (y la clase01 que acabamos de crear)
cols_fe   <- setdiff(names(dataset), c("numero_de_cliente", "foto_mes", "clase_ternaria", "clase01"))   # variables ORIGINALES
cols_rank <- paste0(cols_fe, "_rank")                                                                   # su ranking (columnas nuevas)
if (any(cols_rank %in% names(dataset))) stop("ya existen columnas terminadas en _rank en el crudo")
cat("variables base a rankear:", length(cols_fe), "| esperadas:", PARAM$ancla$vars_base,
    if (length(cols_fe) == PARAM$ancla$vars_base) "-> OK\n" else "-> *** DIFIERE (revisar antes de interpretar resultados) ***\n")

# [Anotación · líneas 410–432] Define rank_cero_fijo(): los NA quedan NA, el cero queda en 0, los positivos se
#   reemplazan por su rango dividido por la cantidad de positivos (valores en (0, 1]) y los negativos por menos
#   el rango de su valor absoluto dividido por la cantidad de negativos (valores en [-1, 0)); los empates
#   reciben el rango promedio. La aplica a cada variable mes por mes y guarda el resultado en una columna nueva
#   <variable>_rank.
# ---- PASO 4: ranking con cero fijo ----
# Para un vector x (una variable en un mes):
#   NA -> NA (se deja)  |  0 -> 0  |  positivos -> rango/cantidad en (0, 1]  |  negativos -> -(rango del valor absoluto)/cantidad en [-1, 0)
# Si la variable no tiene negativos solo actua la rama positiva (el tratamiento es el mismo para todas las variables).
rank_cero_fijo <- function(x) {
  r <- rep(NA_real_, length(x))                       # los NA se quedan NA
  r[!is.na(x) & x == 0] <- 0                          # el cero queda en cero
  p <- !is.na(x) & x > 0
  if (any(p)) r[p] <- frank(x[p], ties.method= "average") / sum(p)          # positivos: (0, 1]
  n <- !is.na(x) & x < 0
  if (any(n)) r[n] <- -frank(-x[n], ties.method= "average") / sum(n)        # negativos: [-1, 0)
  r
}

idx_mes <- split(i, dataset$foto_mes)                 # filas de cada mes: el ranking es por variable Y POR MES
for (k in seq_along(cols_fe)) {
  x <- as.numeric(dataset[[cols_fe[k]]])              # valor crudo de la variable
  for (ii in idx_mes) x[ii] <- rank_cero_fijo(x[ii])  # se rankea cada mes por separado
  set(dataset, j= cols_rank[k], value= x)             # se guarda en una columna NUEVA; el crudo todavia no se toca
  if (k %% 25L == 0L) { cat("  rankeadas", k, "de", length(cols_fe), "variables\n"); invisible(gc(verbose= FALSE)) }
}
cat("ranking con cero fijo aplicado a", length(cols_fe), "variables, mes por mes (", length(idx_mes), "meses )\n")
rm(idx_mes)

# [Anotación · líneas 434–467] Determina las filas de cada conjunto: entrenamiento final (202103 a 202106 con
#   clase), entrenamiento de la búsqueda (202103 y 202104), validación (202106) y predicción (202108); se
#   detiene si la validación no es el mes completo. nom_cols() arma los nombres de columnas: por cada variable,
#   _rank, _lag1, _delta1, _lag2 y _delta2. El modelo final usa todas las variables y la búsqueda las que no son
#   préstamos personales; imprime si las cantidades de columnas coinciden con las esperadas (760 y 750). Se
#   detiene si los préstamos no aportan 10 columnas, si alguna de ellas no deriva de un ranking, si la búsqueda
#   contiene columnas de préstamos personales o si sus columnas no son un subconjunto de las del modelo final.
# ---- filas de cada conjunto (SIN undersampling: todos los clientes con clase conocida) ----
meses_f  <- dataset$foto_mes
rows_all <- which(meses_f %in% PARAM$train & !is.na(dataset$clase_ternaria))   # train final: 202103-06
rows_trbo <- rows_all[meses_f[rows_all] %in% PARAM$bo$train]                     # train de la BO: 202103+04
rows_va  <- rows_all[meses_f[rows_all] == PARAM$bo$valid]                        # validacion de la BO: 202106 completo
rows_fut <- which(meses_f == PARAM$future)                                       # mes a predecir
if (length(rows_va) != sum(meses_f == PARAM$bo$valid)) stop("la validacion de la BO no es el mes completo")

# ---- columnas: modelo final (todas las variables) y modelo de la BO (sin los prestamos personales) ----
# Por cada variable v quedan 5 columnas: v_rank (ranking del mes), v_lag1, v_delta1 (= rank - lag1), v_lag2, v_delta2 (= rank - lag2).
vars_all <- seq_along(cols_fe)
vars_bo  <- which(!(cols_fe %in% PARAM$prestamos))          # BO: las otras 150 variables
nom_cols <- function(vars) {
  v <- cols_fe[vars]
  n <- c(if (PARAM$rank_actual_como_feature) paste0(v, "_rank"),
         paste0(v, "_lag1"), paste0(v, "_delta1"), paste0(v, "_lag2"), paste0(v, "_delta2"))
  if (PARAM$id_como_feature) n <- c(n, "numero_de_cliente")
  n
}
nombres_all <- nom_cols(vars_all)
nombres_bo  <- nom_cols(vars_bo)
cols_prestamos <- setdiff(nombres_all, nombres_bo)          # las columnas que solo entran al modelo final
cat("columnas del modelo FINAL:", length(nombres_all), "| esperadas:", PARAM$ancla$ncols_final,
    if (length(nombres_all) == PARAM$ancla$ncols_final) "-> OK\n" else "-> *** DIFIERE ***\n")
cat("columnas de la BO (sin prestamos personales):", length(nombres_bo), "| esperadas:", PARAM$ancla$ncols_bo,
    if (length(nombres_bo) == PARAM$ancla$ncols_bo) "-> OK\n" else "-> *** DIFIERE ***\n")
cat("columnas de los prestamos (solo en el final, YA RANKEADAS):", paste(cols_prestamos, collapse= " "), "\n")
# controles de los prestamos personales:
if (length(cols_prestamos) != 5L * length(PARAM$prestamos)) stop("los prestamos deberian aportar 5 columnas cada uno")
# el control mira los nombres EXACTOS de los prestamos personales (con el guion bajo que sigue), no el prefijo cprestamos/mprestamos:
# hay otras variables legitimas (por ejemplo prendarios o hipotecarios) que empiezan igual y SI van en la BO.
if (any(sapply(paste0(PARAM$prestamos, "_"), function(p) any(startsWith(nombres_bo, p))))) stop("la BO tiene columnas de prestamos personales")
if (!all(grepl("_(rank|lag1|delta1|lag2|delta2)$", cols_prestamos))) stop("los prestamos tienen que entrar rankeados (_rank/_lag/_delta), nunca en crudo")
if (!all(nombres_bo %in% nombres_all)) stop("las columnas de la BO tienen que ser un subconjunto de las del modelo final")

# [Anotación · líneas 469–488] armar_matriz() construye una matriz numérica para las filas y variables
#   pedidas. Por cada variable toma su columna _rank, obtiene el ranking del mismo cliente 1 y 2 meses antes con
#   los índices ya calculados y llena cinco columnas: ranking del mes, lag1, delta1 (ranking menos lag1), lag2 y
#   delta2 (ranking menos lag2).
# armar_matriz: matriz con las filas pedidas y las columnas de las variables `vars`. Lee SOLO las columnas _rank; los crudos no se usan.
armar_matriz <- function(filas, vars) {
  nombres <- nom_cols(vars)
  nv <- length(vars)
  m <- matrix(NA_real_, nrow= length(filas), ncol= length(nombres), dimnames= list(NULL, nombres))
  o <- if (PARAM$rank_actual_como_feature) 1L else 0L    # corrimiento de columnas si el ranking del mes va primero
  for (k in seq_len(nv)) {
    x  <- dataset[[cols_rank[vars[k]]]]               # ranking de la variable en TODAS las filas del dataset
    l1 <- x[idx1]                                     # ranking del mismo cliente 1 mes antes (NA si no existe)
    l2 <- x[idx2]                                     # ranking del mismo cliente 2 meses antes (NA si no existe)
    if (PARAM$rank_actual_como_feature) m[, k] <- x[filas]    # v_rank
    m[, o * nv + k]          <- l1[filas]             # v_lag1
    m[, (o + 1L) * nv + k]   <- (x - l1)[filas]       # v_delta1
    m[, (o + 2L) * nv + k]   <- l2[filas]             # v_lag2
    m[, (o + 3L) * nv + k]   <- (x - l2)[filas]       # v_delta2
    if (k %% 25L == 0L) invisible(gc(verbose= FALSE))
  }
  if (PARAM$id_como_feature) m[, ncol(m)] <- as.numeric(dataset$numero_de_cliente[filas])
  m
}

# [Anotación · líneas 490–512] Guarda en vectores la clase binaria de cada conjunto, la clase ternaria y los
#   clientes de 202106 y los clientes de 202108; se detiene si hay NA en la clase o clientes repetidos en
#   202108. Escribe en la ficha la cantidad de filas y de positivos del entrenamiento final, las filas por mes,
#   el tamaño de los conjuntos de la búsqueda y la cantidad de columnas.
# vectores que se necesitan despues (se calculan ahora porque el dataset se libera al final del armado de matrices)
y_all    <- dataset$clase01[rows_all]
y_trbo   <- dataset$clase01[rows_trbo]
y_va     <- dataset$clase01[rows_va]
clase_va <- dataset$clase_ternaria[rows_va]
ids_va   <- dataset$numero_de_cliente[rows_va]      # clientes de la validacion (202106), para guardar sus probabilidades
ids_fut  <- dataset$numero_de_cliente[rows_fut]
if (anyNA(y_all) || anyNA(y_va)) stop("hay NA en la clase de train o de validacion")
if (anyDuplicated(ids_fut) > 0) stop("hay numero_de_cliente repetidos en el mes a predecir")
ntrain <- length(rows_all); npos <- sum(y_all == 1L); nfut <- length(rows_fut)
meses_tr <- meses_f[rows_all]
cat(sprintf("preprocesamiento (ranking + indices): %.1f min\n", as.numeric(difftime(Sys.time(), t_fe, units= "mins"))))

ficha(c(
  "DATOS ARMADOS:",
  sprintf("  train final: %d filas (%d positivos, %.2f%%) | meses: %s", ntrain, npos, 100 * npos / ntrain,
          paste(names(table(meses_tr)), table(meses_tr), sep= ":", collapse= " ")),
  sprintf("  train de la BO: %d filas (%s) | validacion %d: %d clientes (%d BAJA+2 reales) | futuro %d: %d clientes",
          length(rows_trbo), paste(PARAM$bo$train, collapse= "+"), PARAM$bo$valid, length(y_va),
          sum(clase_va == "BAJA+2"), PARAM$future, nfut),
  sprintf("  columnas: BO %d (sin prestamos) | final %d (con prestamos rankeados)", length(nombres_bo), length(nombres_all))
))
reporte_ram("features listos (indices y rankings)")

# [Anotación · líneas 514–557] Define los nombres de los archivos de la búsqueda y de la curva de junio, y
#   tres funciones. auc_rank() calcula el AUC por rangos (Mann-Whitney). gan_curva() ordena por probabilidad
#   descendente y acumula 1.072.500 por cada BAJA+2 y -27.500 por cualquier otro envío, en millones, para cada
#   corte. diseno_lhs() sortea n_sorteos hipercubos latinos de n puntos y devuelve, llevado a los rangos de cada
#   parámetro, el que tiene la mayor distancia mínima entre puntos.
# ======================================================================
# PASO 7 - TRAINING STRATEGY: BO SIN UNDERSAMPLING (solo el diseno inicial) + CURVA DE GANANCIA DE JUNIO
# ======================================================================
# Que hace: busca los 3 hiperparametros bayesianos (num_iterations, num_leaves, min_sum_hessian_in_leaf) SOLO con el diseno inicial:
#   n_diseno puntos repartidos en los rangos. No hay iteraciones inteligentes.
# Cada evaluacion entrena con 202103+04 COMPLETOS (sin undersampling, UNA semilla = la primigenia, columnas SIN prestamos personales)
# y mide el AUC sobre 202106 completo. La mejor por AUC es la configuracion que se usa en el entrenamiento final. 202105 queda afuera.
# De cada evaluacion se guarda ademas la curva de ganancia en 202106 (ganancia de enviar los k mejores, para cada corte):
#   sirve para comparar modelos con la validacion del mes 6 y para ver los envios optimos en junio. NO se usa para elegir la config.
# Despues se calcula la curva de junio de la configuracion elegida con varias semillas y su ensamble.
# Resultados: bo_evaluaciones_*.csv, bo_top_configs.csv, bo_mejor_config.csv, curva_ganancia_junio.csv.
f_cfg    <- file.path(dir_exp, "bo_mejor_config.csv")
f_top    <- file.path(dir_exp, "bo_top_configs.csv")
f_diseno <- file.path(dir_exp, "bo_diseno.csv")
f_evals  <- file.path(dir_exp, paste0("bo_evaluaciones_", PARAM$id, ".csv"))
f_junio  <- file.path(dir_exp, "curva_ganancia_junio.csv")
f_junio_cs <- file.path(dir_exp, "junio_curvas_por_semilla.csv")   # curva de ganancia de CADA semilla y del ensamble
f_junio_pr <- file.path(dir_exp, "junio_probabilidades.csv")       # probabilidad de cada semilla y del ensamble para cada cliente de junio

# AUC (Mann-Whitney): probabilidad de que un positivo tenga mayor prob que un negativo
auc_rank <- function(p, y) {
  r <- frank(p, ties.method= "average")
  n1 <- sum(y == 1L); n0 <- length(y) - n1
  (sum(r[y == 1L]) - n1 * (n1 + 1) / 2) / (n1 * n0)
}
# ganancia (millones) de enviar los k mejores, para cada k en `cortes`: BAJA+2 suma 1.072.500 y cualquier otro envio resta 27.500
gan_curva <- function(prob, clase, cortes) {
  o <- order(-prob)
  g <- cumsum(ifelse(clase[o] == "BAJA+2", 1072500, -27500)) / 1e6
  g[cortes]
}
# hipercubo latino maximin aproximado, en R base: cada parametro se divide en n tramos y cada tramo se usa UNA vez;
# entre n_sorteos hipercubos al azar se queda con el que deja los puntos mas separados entre si (en el cubo unitario).
diseno_lhs <- function(n, lo, hi, semilla, n_sorteos) {
  set.seed(semilla)
  k <- length(lo)
  mejor <- NULL; mejor_d <- -Inf
  for (s in seq_len(n_sorteos)) {
    u <- sapply(seq_len(k), function(j) (sample.int(n) - runif(n)) / n)   # matriz n x k con valores en (0,1)
    d <- min(dist(u))
    if (d > mejor_d) { mejor_d <- d; mejor <- u }
  }
  sweep(sweep(mejor, 2, hi - lo, "*"), 2, lo, "+")                         # se lleva de (0,1) a los rangos reales
}

# [Anotación · líneas 559–593] Las líneas 559 a 563 son un respaldo comentado que escribiría
#   bo_mejor_config.csv con 45 hojas, hessiano 0.0244994712564396 y 2428 árboles. La búsqueda y la curva de
#   junio se ejecutan sólo si faltan sus archivos de resultado. Arma las matrices de entrenamiento (202103 y
#   202104) y de validación (202106) con las 750 columnas, construye el lgb.Dataset y define prob_validacion(),
#   que entrena con una cantidad de hojas, un hessiano mínimo, una cantidad de árboles y una semilla dados y
#   devuelve la probabilidad sobre 202106.
# [ENTREGA 6] RESPALDO (comentado: NO corre). La BO de la corrida entregada eligio la iteracion 10 (45 hojas, hessiano 0.0244994712564396,
# 2428 arboles, AUC 0.917294901499082) por solo 0.00001 de AUC sobre la iteracion 2. Si al replicar la BO eligiera otra configuracion
# (ver bo_top_configs.csv y README.md), descomentar la linea siguiente y volver a correr en una carpeta NUEVA: escribe bo_mejor_config.csv
# con los valores de la entrega y el script usa esa configuracion (no repite la BO si el archivo existe).
# if (!file.exists(f_cfg)) fwrite(data.table(fuente= "BO_diseno_AUC", num_leaves= 45L, min_sum_hessian_in_leaf= 0.0244994712564396, num_iterations= 2428L, auc_bo= 0.917294901499082), f_cfg)
necesita_bo    <- !file.exists(f_cfg)
necesita_junio <- !file.exists(f_junio)
t_bo <- Sys.time()
if (necesita_bo || necesita_junio) {
  reporte_ram("antes de armar las matrices de la BO")
  # Matrices de la BO: SIN los prestamos personales (750 columnas). Se arman con los rankings (las originales todavia no se borraron).
  mat_bo_tr <- armar_matriz(rows_trbo, vars_bo)
  mat_bo_va <- armar_matriz(rows_va, vars_bo)
  if (!identical(colnames(mat_bo_tr), nombres_bo) || !identical(colnames(mat_bo_va), nombres_bo)) stop("las matrices de la BO no tienen las columnas esperadas")
  invisible(gc(full= TRUE, verbose= FALSE))
  dtrain_bo <- lgb.Dataset(
    data= mat_bo_tr, label= y_trbo,
    params= list(max_bin= PARAM$lgb$max_bin, feature_pre_filter= FALSE,
                 min_data_in_leaf= PARAM$lgb$min_data_in_leaf, verbosity= -100),
    free_raw_data= FALSE)
  dtrain_bo$construct()
  reporte_ram("matrices y dataset de la BO listos")

  # entrena con la configuracion dada sobre el train de la BO y devuelve la probabilidad sobre 202106 completo
  prob_validacion <- function(nl, hess, nr, semilla) {
    p <- PARAM$lgb
    p$num_leaves <- as.integer(nl)
    p$min_sum_hessian_in_leaf <- as.numeric(hess)
    p$seed <- as.integer(semilla)
    mod <- lgb.train(params= p, data= dtrain_bo, nrounds= as.integer(nr), verbose= -1L)
    pr <- predict(mod, mat_bo_va)
    rm(mod); invisible(gc(full= TRUE, verbose= FALSE))
    if (length(pr) != length(y_va)) stop("la prediccion de validacion no tiene una fila por cliente")
    pr
  }

# [Anotación · líneas 595–641] Genera el diseño de 10 puntos (num_iterations y num_leaves redondeados a
#   enteros dentro de sus rangos) y lo guarda en bo_diseno.csv. Para cada punto aún no evaluado entrena con la
#   semilla 106937, calcula el AUC y la curva de ganancia en 202106 y agrega una fila a
#   bo_evaluaciones_<id>.csv. Con las 10 evaluaciones calcula la ganancia máxima de cada una y su corte, ordena
#   por AUC descendente, guarda bo_top_configs.csv y escribe en bo_mejor_config.csv la configuración de mayor
#   AUC. Si bo_mejor_config.csv ya existe, no repite la búsqueda.
  if (necesita_bo) {
    # ---- diseno inicial: n_diseno puntos de un hipercubo latino ----
    lo <- c(PARAM$bo$iter_min, PARAM$bo$hojas_min, PARAM$bo$hess_min)
    hi <- c(PARAM$bo$iter_max, PARAM$bo$hojas_max, PARAM$bo$hess_max)
    pts <- diseno_lhs(PARAM$bo$n_diseno, lo, hi, PARAM$semilla_primigenia, PARAM$bo$n_sorteos)
    tb_dis <- data.table(iter= seq_len(PARAM$bo$n_diseno),
                         num_iterations= pmin(pmax(as.integer(round(pts[, 1])), PARAM$bo$iter_min), PARAM$bo$iter_max),
                         num_leaves= pmin(pmax(as.integer(round(pts[, 2])), PARAM$bo$hojas_min), PARAM$bo$hojas_max),
                         min_sum_hessian_in_leaf= pts[, 3])
    if (!file.exists(f_diseno)) fwrite(tb_dis, f_diseno)
    cat("diseno inicial de la BO (", nrow(tb_dis), "puntos):\n"); print(tb_dis)

    ya <- if (file.exists(f_evals)) fread(f_evals)$iter else integer(0)
    cat("evaluaciones ya hechas:", length(ya), "| a hacer:", length(setdiff(tb_dis$iter, ya)), "\n")
    for (j in setdiff(tb_dis$iter, ya)) {
      d <- tb_dis[iter == j]
      t0 <- Sys.time()
      pr  <- prob_validacion(d$num_leaves, d$min_sum_hessian_in_leaf, d$num_iterations, PARAM$semilla_primigenia)
      auc <- auc_rank(pr, y_va)
      gv  <- gan_curva(pr, clase_va, PARAM$cortes)
      seg <- as.numeric(difftime(Sys.time(), t0, units= "secs"))
      fila <- as.data.table(c(list(iter= j, fecha= format(Sys.time(), "%Y-%m-%d %H:%M:%S"),
                                   num_iterations= d$num_iterations, num_leaves= d$num_leaves,
                                   min_sum_hessian_in_leaf= d$min_sum_hessian_in_leaf, auc= auc, segundos= round(seg, 1)),
                              as.list(setNames(gv, paste0("gan_", PARAM$cortes)))))
      fwrite(fila, f_evals, append= file.exists(f_evals), col.names= !file.exists(f_evals))
      cat(sprintf("[BO %d/%d] hojas %d | hessiano %.5f | arboles %d -> AUC %.5f | ganancia en 202106 a 10500: %.1f M | %.1f min\n",
                  j, PARAM$bo$n_diseno, d$num_leaves, d$min_sum_hessian_in_leaf, d$num_iterations, auc,
                  gv[match(10500L, PARAM$cortes)], seg / 60))
    }

    ev <- fread(f_evals)
    if (nrow(ev) != PARAM$bo$n_diseno || anyNA(ev$auc)) stop("la BO no tiene todas sus evaluaciones validas")
    cols_gan <- paste0("gan_", PARAM$cortes)
    ev[, gan_max := do.call(pmax, .SD), .SDcols= cols_gan]
    ev[, corte_gan_max := PARAM$cortes[max.col(as.matrix(.SD), ties.method= "first")], .SDcols= cols_gan]
    setorder(ev, -auc)
    ev[, rank_auc := .I]
    fwrite(ev, f_top)
    cat("\n=== LAS", nrow(ev), "CONFIGURACIONES, ordenadas por AUC en", PARAM$bo$valid, "(sin cross validation; sin undersampling) ===\n")
    print(ev[, .(rank_auc, iter, num_leaves, min_sum_hessian_in_leaf, num_iterations, auc, gan_10500, gan_max, corte_gan_max)])
    cat("La elegida es la de mayor AUC. Si la de mayor ganancia en junio es otra, queda a la vista en esta tabla y en bo_top_configs.csv.\n")
    fwrite(data.table(fuente= "BO_diseno_AUC", num_leaves= ev$num_leaves[1], min_sum_hessian_in_leaf= ev$min_sum_hessian_in_leaf[1],
                      num_iterations= ev$num_iterations[1], auc_bo= ev$auc[1]), f_cfg)
  } else cat("bo_mejor_config.csv ya existe: no se repite la BO\n")

  cat("minutos de BO:", round(as.numeric(difftime(Sys.time(), t_bo, units= "mins")), 1), "\n")

# [Anotación · líneas 643–683] Con la configuración elegida entrena 5 modelos (las primeras 5 semillas de la
#   lista) sobre 202103 y 202104 y predice 202106. Calcula la curva de ganancia de cada semilla y la del
#   promedio de las 5 probabilidades, y guarda curva_ganancia_junio.csv (ganancia del ensamble, media, desvío,
#   mínimo y máximo por corte), junio_curvas_por_semilla.csv y junio_probabilidades.csv. Imprime el AUC del
#   ensamble y el corte de mayor ganancia. Libera las matrices de la búsqueda y registra los minutos de la
#   etapa.
  # ---- curva de ganancia en junio de la configuracion elegida (varias semillas + ensamble) ----
  if (necesita_junio) {
    cfg_j <- fread(f_cfg)
    sem_j <- semillas50[seq_len(PARAM$junio$n_semillas)]
    cat("curva de junio con la configuracion elegida:", cfg_j$num_leaves[1], "hojas, hessiano", cfg_j$min_sum_hessian_in_leaf[1],
        ",", cfg_j$num_iterations[1], "arboles | semillas:", sem_j, "\n")
    prs <- list(); curvas <- list()
    for (s in seq_along(sem_j)) {
      t0 <- Sys.time()
      prs[[s]] <- prob_validacion(cfg_j$num_leaves[1], cfg_j$min_sum_hessian_in_leaf[1], cfg_j$num_iterations[1], sem_j[s])
      curvas[[s]] <- gan_curva(prs[[s]], clase_va, PARAM$cortes)
      cat(sprintf("  semilla %d (%d/%d): AUC %.5f | %.1f min\n", sem_j[s], s, length(sem_j), auc_rank(prs[[s]], y_va),
                  as.numeric(difftime(Sys.time(), t0, units= "mins"))))
    }
    mc <- do.call(cbind, curvas)
    pr_ens <- rowMeans(do.call(cbind, prs))                       # ensamble de las semillas: promedio simple de probabilidades
    tb_j <- data.table(corte= PARAM$cortes, gan_ensamble= gan_curva(pr_ens, clase_va, PARAM$cortes),
                       gan_media_semillas= rowMeans(mc), gan_sd_semillas= apply(mc, 1, sd), gan_min= apply(mc, 1, min), gan_max= apply(mc, 1, max))
    # Se guardan tambien las curvas POR SEMILLA y las probabilidades de junio: asi otro modelo evaluado con el mismo protocolo
    # (train 202103-04 sin undersampling, validacion 202106 completo, mismos cortes y semillas) se puede comparar con las mismas filas,
    # semilla contra semilla, y se pueden probar ensambles de modelos en junio. Nunca se pisan archivos existentes.
    tb_cs <- as.data.table(mc); setnames(tb_cs, paste0("gan_s", sem_j))
    tb_cs[, `:=`(corte= PARAM$cortes, gan_ensamble= tb_j$gan_ensamble)]
    setcolorder(tb_cs, "corte")
    pm <- do.call(cbind, prs); colnames(pm) <- paste0("prob_s", sem_j)
    tb_pj <- data.table(numero_de_cliente= ids_va, clase_ternaria= clase_va, clase01= y_va, as.data.table(pm), prob_ensamble= pr_ens)
    if (!file.exists(f_junio_cs)) fwrite(tb_cs, f_junio_cs)
    if (!file.exists(f_junio_pr)) fwrite(tb_pj, f_junio_pr)
    fwrite(tb_j, f_junio)
    cat("\n=== CURVA DE GANANCIA EN", PARAM$bo$valid, "(millones; escala distinta a la del bot: usar la FORMA) ===\n"); print(round(tb_j, 2))
    cat("AUC del ensamble en junio:", round(auc_rank(pr_ens, y_va), 5), "\n")
    cat("Envios optimos en junio: ensamble ->", tb_j$corte[which.max(tb_j$gan_ensamble)],
        "| media de las semillas ->", tb_j$corte[which.max(tb_j$gan_media_semillas)], "\n")
    rm(prs, curvas, mc, pr_ens, pm, tb_pj, tb_cs)
  } else cat("curva_ganancia_junio.csv ya existe: no se repite\n")

  rm(dtrain_bo, mat_bo_tr, mat_bo_va)
  invisible(gc(full= TRUE, verbose= FALSE))
  reporte_ram("fin de la BO y la curva de junio")
} else cat("bo_mejor_config.csv y curva_ganancia_junio.csv ya existen: se saltea la BO\n")
min_bo <- as.numeric(difftime(Sys.time(), t_bo, units= "mins"))

# [Anotación · líneas 685–694] Lee bo_mejor_config.csv, guarda num_leaves, min_sum_hessian_in_leaf y
#   num_iterations en PARAM$final y los escribe en la ficha junto con el AUC de la búsqueda.
cfg <- fread(f_cfg)
PARAM$final <- list(num_leaves= as.integer(cfg$num_leaves[1]), min_sum_hessian_in_leaf= as.numeric(cfg$min_sum_hessian_in_leaf[1]),
                    num_iterations= as.integer(cfg$num_iterations[1]), fuente= cfg$fuente[1])
ficha(c(
  "HIPERPARAMETROS FINALES (iguales para todas las semillas):",
  sprintf("  fuente: %s | num_leaves %d | min_sum_hessian_in_leaf %.10f | num_iterations %d | AUC en la BO: %s",
          PARAM$final$fuente, PARAM$final$num_leaves, PARAM$final$min_sum_hessian_in_leaf, PARAM$final$num_iterations,
          format(cfg$auc_bo[1])),
  ""
))

# [Anotación · líneas 696–727] Arma la tabla del plan con las 109 semillas y el archivo de probabilidades de
#   cada una (modelos/prob_modelo_s<semilla>.csv) y cuenta cuántos faltan. Si falta alguno, arma la matriz de
#   entrenamiento final (202103 a 202106) y la de 202108 con las 760 columnas y controla que sean las de la
#   búsqueda más las de los préstamos. Después elimina del dataset las variables originales, verifica que todas
#   las columnas del modelo deriven de un ranking y libera el dataset.
# ======================================================================
# PASOS 6 Y 8 - MATRICES DEL MODELO FINAL (CON los prestamos rankeados) Y BAJA DE LAS VARIABLES ORIGINALES
# ======================================================================
dir_modelos <- file.path(dir_exp, "modelos")
dir.create(dir_modelos, showWarnings= FALSE, recursive= TRUE)
tb_plan <- data.table(idx= PARAM$semillas_idx, semilla= PARAM$semillas)
tb_plan[, nombre := sprintf("modelo_s%d", semilla)]
tb_plan[, f_prob := file.path(dir_modelos, paste0("prob_", nombre, ".csv"))]
faltan <- tb_plan[!file.exists(f_prob), .N]
cat("modelos del plan:", nrow(tb_plan), "| ya terminados:", nrow(tb_plan) - faltan, "| a entrenar:", faltan, "\n")

if (faltan > 0) {
  reporte_ram("antes de armar las matrices finales")
  # Matriz FINAL: las 150 variables de la BO MAS los prestamos personales, todo ya rankeado (760 columnas).
  mat_all <- armar_matriz(rows_all, vars_all)
  mat_fut <- armar_matriz(rows_fut, vars_all)
  if (!identical(colnames(mat_all), nombres_all) || !identical(colnames(mat_fut), nombres_all)) stop("las matrices finales no tienen las columnas esperadas")
  if (!all(nombres_bo %in% colnames(mat_all)) || !setequal(setdiff(colnames(mat_all), nombres_bo), cols_prestamos)) {
    stop("el modelo final tiene que ser las columnas de la BO mas las de los prestamos rankeados")
  }
  invisible(gc(full= TRUE, verbose= FALSE))
  reporte_ram("matrices finales listas")
}

# ---- PASO 6: se eliminan las variables ORIGINALES (valores crudos), despues de calcular los lags y delta lags ----
dataset[, (cols_fe) := NULL]
if (any(cols_fe %in% names(dataset))) stop("quedaron variables originales en el dataset")
if (any(nombres_all %in% cols_fe)) stop("hay una variable original entre las columnas del modelo")
if (!all(grepl("_(rank|lag1|delta1|lag2|delta2)$", setdiff(nombres_all, "numero_de_cliente")))) stop("hay columnas del modelo que no derivan de un ranking")
cat("variables originales eliminadas:", length(cols_fe), "| columnas del modelo final:", length(nombres_all), "(todas derivadas de rankings)\n")
rm(dataset, cli, idx1, idx2, rows_all, rows_trbo, rows_va, rows_fut)
invisible(gc(full= TRUE, verbose= FALSE))

# [Anotación · líneas 729–782] Construye una vez el lgb.Dataset final. Para cada semilla del plan sin archivo
#   de probabilidades, entrena un modelo con los hiperparámetros fijos, los tres de la búsqueda y esa semilla,
#   predice 202108, escribe numero_de_cliente y prob en un archivo temporal que luego renombra, y agrega una
#   fila a log_modelos_<id>.csv con la semilla, los hiperparámetros, las filas de entrenamiento y los minutos.
#   Antes de empezar cada modelo mira si existe PARAR.txt; si existe, corta el ciclo.
# ======================================================================
# PASO 9 - ENTRENAMIENTO FINAL (202103-06, sin undersampling) Y CADENA DE MODELOS, UNO POR SEMILLA (reanudable)
# ======================================================================
# El lgb.Dataset se construye UNA vez. Luego se entrena un modelo por semilla con hiperparametros IDENTICOS (los de la BO);
# lo unico que cambia entre modelos es la semilla. Cada modelo predice 202108 y guarda modelos/prob_<semilla>.csv
# (numero_de_cliente, prob). Si el archivo ya existe, el modelo se salta (por eso se puede reanudar).
f_log <- file.path(dir_exp, paste0("log_modelos_", PARAM$id, ".csv"))
cat("plan:", nrow(tb_plan), "semillas posibles | modelos en disco:", nrow(tb_plan) - faltan, "| el entrenamiento sigue hasta que exista", f_parar, "\n")
t_cadena <- Sys.time()
if (faltan > 0) {
  dtrain <- lgb.Dataset(
    data= mat_all, label= y_all,
    params= list(max_bin= PARAM$lgb$max_bin, feature_pre_filter= FALSE,
                 min_data_in_leaf= PARAM$lgb$min_data_in_leaf, verbosity= -100),
    free_raw_data= TRUE)
  seg_dataset <- system.time(dtrain$construct())[[ "elapsed" ]]
  rm(mat_all)
  invisible(gc(full= TRUE, verbose= FALSE))
  cat("segundos en construir el lgb.Dataset final:", round(seg_dataset, 1), "\n")
  reporte_ram("lgb.Dataset final construido")

  for (j in seq_len(nrow(tb_plan))) {
    m <- tb_plan[j]
    if (file.exists(m$f_prob)) next
    # parada ordenada (PARAR.txt). Se mira ANTES de empezar cada modelo; el que esta en curso siempre termina y se guarda.
    if (file.exists(f_parar)) { cat(sprintf("PARAR.txt detectado: no se empieza el modelo %d. Paso al armado de archivos.\n", j)); break }

    param <- c(PARAM$lgb, list(num_leaves= PARAM$final$num_leaves,
                               min_sum_hessian_in_leaf= PARAM$final$min_sum_hessian_in_leaf,
                               seed= m$semilla))
    cat(sprintf("[%d/%d] %s | %d arboles | modelos en disco: %d | %s\n", j, nrow(tb_plan), m$nombre, PARAM$final$num_iterations,
                length(list.files(dir_modelos, pattern= "^prob_.*\\.csv$")), format(Sys.time(), "%X")))
    t0 <- Sys.time()
    modelo <- lgb.train(params= param, data= dtrain, nrounds= PARAM$final$num_iterations, verbose= -1L)
    prob <- predict(modelo, mat_fut)
    seg_total <- as.numeric(difftime(Sys.time(), t0, units= "secs"))
    if (length(prob) != nfut) stop("la prediccion no tiene una fila por cliente")

    f_tmp <- paste0(m$f_prob, ".tmp")                     # primero a un temporal y despues se renombra
    fwrite(data.table(numero_de_cliente= ids_fut, prob= prob), f_tmp)
    file.rename(f_tmp, m$f_prob)
    fwrite(data.table(fecha= format(Sys.time(), "%Y-%m-%d %H:%M:%S"), id= PARAM$id, modelo= m$nombre, semilla= m$semilla,
                      arboles= PARAM$final$num_iterations, hojas= PARAM$final$num_leaves,
                      hess= PARAM$final$min_sum_hessian_in_leaf, fuente_hiper= PARAM$final$fuente,
                      us= PARAM$us, ntrain= ntrain, npos= npos, minutos= round(seg_total / 60, 1)),
           f_log, append= file.exists(f_log), col.names= !file.exists(f_log))
    cat(sprintf("     listo en %.1f min | acumulado %.0f min\n", seg_total / 60,
                as.numeric(difftime(Sys.time(), t_cadena, units= "mins"))))
    rm(modelo, prob)
    invisible(gc(full= TRUE, verbose= FALSE))
  }
} else cat("todos los modelos del plan ya estan terminados: solo se rearma el ensamble\n")
min_modelos <- as.numeric(difftime(Sys.time(), t_cadena, units= "mins"))
reporte_ram("fin de la cadena")
# [Anotación · líneas 783–789] Rama del modo SOLO_ARMAR: lee del crudo sólo numero_de_cliente y foto_mes para
#   obtener los clientes de 202108 y se detiene si no hay ninguno o hay repetidos.
} else {   # SOLO_ARMAR: solo hace falta la lista de clientes de 202108 (liviano: dos columnas del crudo)
  dir_modelos <- file.path(dir_exp, "modelos")
  ids_fut <- fread(PATH_CRUDO, select= c("numero_de_cliente", "foto_mes"))[foto_mes == PARAM$future, numero_de_cliente]
  nfut <- length(ids_fut); min_bo <- 0; min_modelos <- 0
  if (nfut == 0 || anyDuplicated(ids_fut) > 0) stop("no pude leer bien los clientes de 202108")
  cat("clientes de", PARAM$future, ":", nfut, "\n")
}

# [Anotación · líneas 791–817] Crea las carpetas entrega/por_modelo, entrega/ensamble y
#   entrega/barrido_cortes. Lee todos los archivos prob_*.csv de modelos/, controla que cada modelo tenga una
#   fila por cliente de 202108, sin clientes de otro mes ni repetidos, y calcula el ensamble: la media de prob
#   por numero_de_cliente, verificando que cada cliente tenga tantos valores como modelos.
# ======================================================================
# PASOS 10 A 12 - ENSAMBLE (promedio simple de PROBABILIDADES por cliente) Y BARRIDO DE CORTES
# ======================================================================
# a) por_modelo/: el top-k de CADA modelo con el corte base (variabilidad entre semillas). Solo las primeras 20 semillas.
# b) barrido_cortes/corte_<k>/: el top-k de cada modelo para cada corte k; un submit por carpeta (mismo corte = misma cantidad de filas).
#  Solo las primeras 20 semillas: el bot acepta hasta 20 archivos por submit.
# c) ensamble/: se promedia la probabilidad de TODOS los modelos terminados por numero_de_cliente y se toma el top-k; un archivo por corte.
#    El archivo final es UNO de estos, con el corte que se elija mirando la curva del barrido (y la curva de junio).
dir_ent <- file.path(dir_exp, "entrega")
dir_pm  <- file.path(dir_ent, "por_modelo")
dir_en  <- file.path(dir_ent, "ensamble")
dir_bc  <- file.path(dir_ent, "barrido_cortes")
for (d in c(dir_pm, dir_en, dir_bc)) dir.create(d, showWarnings= FALSE, recursive= TRUE)
fecha <- format(Sys.time(), "%Y%m%d")

archivos <- list.files(dir_modelos, pattern= "^prob_.*\\.csv$", full.names= TRUE)
if (length(archivos) == 0) stop("no hay ningun modelo terminado")
cat("modelos terminados:", length(archivos), "\n")
probs <- rbindlist(lapply(archivos, function(f) { x <- fread(f); x[, modelo := sub("^prob_(.*)\\.csv$", "\\1", basename(f))]; x }))
if (any(probs[, .N, modelo]$N != nfut)) stop("algun modelo no tiene una fila por cliente de 202108")
if (!all(probs$numero_de_cliente %in% ids_fut)) stop("hay clientes que no estan en 202108")
if (anyDuplicated(probs[, .(modelo, numero_de_cliente)]) > 0) stop("hay clientes repetidos dentro de un modelo")

# ENSAMBLE: se promedia por numero_de_cliente (se UNE por cliente, nunca por posicion)
ens <- probs[, list(prob= mean(prob), nmod= .N), numero_de_cliente]
nm <- length(archivos)
if (nrow(ens) != nfut || any(ens$nmod != nm)) stop("el promedio no uso todos los modelos para todos los clientes")

# [Anotación · líneas 819–845] escribir_envio() ordena por probabilidad descendente, toma los primeros k
#   clientes y los escribe uno por línea, sin encabezado; no escribe si el archivo ya existe o si existe uno
#   igual con otra fecha en el nombre. Con ella genera: un archivo por modelo con corte 11.000 para las primeras
#   20 semillas; para cada corte de 8.000 a 15.000, una carpeta con un archivo por cada uno de esos modelos; y
#   un archivo del ensamble por corte, con nombre E780_ens<modelos>m_k<corte>_<fecha>.csv. Imprime, para cada
#   uno de esos modelos, la proporción de sus primeros 11.000 clientes que coincide con los del ensamble.
# escribe el top-k de `tb` (ordenado por prob) a un archivo de un numero_de_cliente por linea, sin encabezado.
# Nunca pisa un archivo y tampoco duplica uno ya existente con otra fecha en el nombre (por si se reanuda otro dia).
escribir_envio <- function(tb, k, archivo) {
  if (file.exists(archivo)) return(invisible(FALSE))
  if (length(Sys.glob(sub("_[0-9]{8}\\.csv$", "_*.csv", archivo))) > 0) return(invisible(FALSE))
  ids <- tb[order(-prob)][seq_len(k), as.integer(numero_de_cliente)]
  fwrite(data.table(ids), archivo, col.names= FALSE, quote= FALSE, scipen= 100, eol= "\n")
  invisible(TRUE)
}

modelos <- unique(probs$modelo)
modelos_envio <- intersect(paste0("modelo_s", semillas50[seq_len(PARAM$barrido_max_modelos)]), modelos)   # primeras 20 semillas, en orden
cat("modelos con archivos por_modelo y barrido:", length(modelos_envio), "\n")
# a) un archivo por modelo con el corte base
for (nm_ in modelos_envio) escribir_envio(probs[modelo == nm_], PARAM$k_por_modelo,
                                          file.path(dir_pm, sprintf("E%d_%s_k%d_%s.csv", PARAM$experimento, nm_, PARAM$k_por_modelo, fecha)))
# b) barrido de cortes: una carpeta por corte con UN archivo por modelo (mismo corte = misma cantidad de registros)
for (k in PARAM$cortes) {
  dk <- file.path(dir_bc, sprintf("corte_%d", k)); dir.create(dk, showWarnings= FALSE)
  for (nm_ in modelos_envio) escribir_envio(probs[modelo == nm_], k, file.path(dk, sprintf("E%d_%s_k%d_%s.csv", PARAM$experimento, nm_, k, fecha)))
}
# c) ensamble: UN archivo por corte (el archivo final es uno de estos); el nombre dice cuantos modelos entraron
for (k in PARAM$cortes) escribir_envio(ens, k, file.path(dir_en, sprintf("E%d_ens%dm_k%d_%s.csv", PARAM$experimento, nm, k, fecha)))

top_ens <- ens[order(-prob)][seq_len(PARAM$k_por_modelo), numero_de_cliente]
print(probs[modelo %in% modelos_envio, list(solape_top_con_ensamble= round(
  length(intersect(numero_de_cliente[order(-prob)][seq_len(PARAM$k_por_modelo)], top_ens)) / PARAM$k_por_modelo, 3)), modelo])

# [Anotación · líneas 847–871] Lee cada CSV de la carpeta entrega y verifica que tenga entre 8.000 y 15.000
#   filas, sólo enteros sin encabezado, sin repetidos y sólo clientes de 202108; si alguno no cumple, lo imprime
#   y se detiene. Verifica además que en cada carpeta del barrido todos los archivos tengan la misma cantidad de
#   filas y que haya uno por modelo.
# ======================================================================
# PASO 13 - VALIDACION DE FORMATO DE TODOS LOS ARCHIVOS
# ======================================================================
# Cada archivo debe tener entre 8000 y 15000 filas, solo enteros sin encabezado, sin repetidos y solo clientes de 202108.
# Ademas, todos los archivos de una carpeta del barrido deben tener la misma cantidad de filas y haber uno por modelo.
# Si algo falla, el script se detiene.
validar_envio <- function(archivo) {
  x <- readLines(archivo)
  solo_enteros <- all(grepl("^[0-9]+$", x))
  data.table(archivo= basename(archivo), filas= length(x),
             filas_8000_a_15000= (length(x) >= 8000 & length(x) <= 15000),
             enteros_sin_encabezado= solo_enteros, sin_repetidos= !anyDuplicated(x),
             clientes_de_202108= (solo_enteros && all(as.integer(x) %in% ids_fut)))
}
csvs <- list.files(dir_ent, pattern= "\\.csv$", recursive= TRUE, full.names= TRUE)
tb_val <- rbindlist(lapply(csvs, validar_envio))
cat("archivos validados:", nrow(tb_val), "\n")
if (!all(as.matrix(tb_val[, 3:6]))) { print(tb_val[!(filas_8000_a_15000 & enteros_sin_encabezado & sin_repetidos & clientes_de_202108)]); stop("hay archivos que NO pasan la validacion de formato: no los envies") }
chk <- rbindlist(lapply(list.dirs(dir_bc, recursive= FALSE), function(d) {
  f <- list.files(d, pattern= "\\.csv$", full.names= TRUE)
  data.table(carpeta= basename(d), archivos= length(f), filas_distintas= uniqueN(sapply(f, function(z) length(readLines(z)))))
}))
print(chk)
if (any(chk$filas_distintas != 1L)) stop("hay carpetas del barrido con archivos de distinta cantidad de registros")
if (any(chk$archivos != length(modelos_envio))) stop("alguna carpeta del barrido no tiene un archivo por modelo")

# [Anotación · líneas 873–892] Escribe el cierre de la ficha: minutos totales, minutos de la búsqueda con la
#   curva de junio y de los modelos, cantidad de modelos del ensamble, contenido de cada carpeta de salida y el
#   nombre del archivo entregado (entrega/ensamble/E780_ens109m_k11000_<fecha>.csv). Imprime el último reporte
#   de memoria y la fecha.
min_total <- as.numeric(difftime(Sys.time(), t_script, units= "mins"))
ficha(c(
  "",
  paste(rep("=", 78), collapse= ""),
  paste0("FIN ", PARAM$id, " | minutos totales de esta corrida: ", round(min_total, 1),
         " | BO + curva de junio: ", round(min_bo, 1), " | modelos: ", round(min_modelos, 1)),
  paste0("Modelos en el ensamble: ", nm, " | archivos por modelo y barrido: ", length(modelos_envio), " modelos."),
  "Todos los archivos pasan la validacion de formato.",
  paste0("  por_modelo/      : un archivo por modelo, corte ", PARAM$k_por_modelo),
  "  barrido_cortes/  : una carpeta por corte, un archivo por modelo (un submit por carpeta)",
  "  ensamble/        : el promedio de las probabilidades, un archivo por corte (UNO de estos es la entrega final)",
  "  curva_ganancia_junio.csv, junio_curvas_por_semilla.csv, junio_probabilidades.csv y bo_top_configs.csv: curvas y probabilidades en 202106 (envios optimos en junio, comparacion de modelos).",
  "ARCHIVO ENTREGADO: entrega/ensamble/E780_ens109m_k11000_<fecha>.csv (corte 11000; ver README.md).",
  "  Para armar los archivos con lo que haya SIN entrenar: E780_SOLO_ARMAR=1 (variable de entorno) y lanzar el mismo script.",
  "No se envio nada a Zulip desde este script.",
  paste(rep("=", 78), collapse= ""),
  ""
))
reporte_ram("final")
format(Sys.time(), "%a %b %d %X %Y")
```


## Explicaciones del alumno (texto original)

### competencia_01_entrega/README.md

> # Competencia 1 · DMEyF 2026 · Entrega final (E780)
>
> Esta carpeta contiene todo lo necesario para replicar en forma exacta la predicción final entregada.
>
> |Archivo|Qué es|
> |-|-|
> |`E780_entrega.R`|Script único que, partiendo del crudo de la competencia, hace todo: clase, preprocesamiento, optimización de hiperparámetros, curva de junio, 109 modelos, ensamble y archivos de envío.|
> |`README.md`|Este archivo: instrucciones, tiempos, resultados esperados y decisiones.|
>
> No hace falta ningún otro archivo: la optimización de hiperparámetros que dio origen a la configuración final está dentro del mismo script y se vuelve a correr.
>
> ## Archivo entregado
>
> **`E780_ens109m_k11000_20261011.csv`**
>
> Es el ensamble (promedio simple de probabilidades) de 109 modelos LightGBM que solo difieren en la semilla, con los **11.000** clientes de mayor probabilidad.
>
> El script genera el ensamble para los 15 cortes entre 8000 y 15000 (cada 500). El entregado es el del corte indicado arriba. Se encuentra en:
>
> ```
> colab_replica/C1-E780-PR2108-final/entrega/ensamble/E780_ens109m_k<corte>_<fecha>.csv
> ```
>
> La fecha del nombre es la del día en que se corre el script; la de la entrega fue `20261011`. El contenido no depende de la fecha.
>
> ## Requisitos
>
> |Componente|Versión usada|
> |-|-|
> |R|4.6.1 (Windows 11 x64)|
> |lightgbm|**4.7.0** (paquete de CRAN, **no** zlightgbm)|
> |data.table|1.18.6.1|
> |Hardware|Ryzen 7 7435HS, 16 hilos, 16 GB de RAM|
>
> El script se detiene si la versión de lightgbm no es 4.7.0, porque otra versión puede dar otras predicciones. LightGBM corre con `num_threads = 16`, `deterministic = TRUE` y `force_row_wise = TRUE`.
>
> ## Cómo correrlo
>
> 1. Crear una carpeta de trabajo **vacía** y poner en ella el crudo de la competencia con el nombre `competencia_01_crudo.csv` (983.061 filas, 154 columnas).
> 2. Copiar `E780_entrega.R` a esa carpeta.
> 3. Desde esa carpeta, correr:
>
> ```
> Rscript E780_entrega.R > E780.log 2>&1
> ```
>
> Los resultados quedan en `colab_replica/C1-E780-PR2108-final/`. Si se prefieren otras rutas, se pueden indicar con las variables de entorno `DMEYF_CRUDO` (ruta del crudo) y `DMEYF_EXP` (carpeta de resultados).
>
> **Es reanudable:** si la corrida se corta, al volver a lanzarla en la misma carpeta saltea lo que ya terminó (evaluaciones de la BO, curva de junio y cada modelo). El script nunca pisa archivos existentes y no envía nada a Zulip.
>
> ## Tiempo de ejecución
>
> Tiempos reales en la notebook descripta arriba:
>
> |Etapa|Tiempo|
> |-|-|
> |Lectura, clase y ranking|menos de 1 min|
> |Optimización de hiperparámetros (10 evaluaciones)|33 min|
> |Curva de ganancia en junio (5 modelos)|17 min|
> |109 modelos finales (\~9,1 min cada uno)|\~16,5 h|
> |**Total aproximado**|**\~17,5 h**|
>
> ## Qué hace el script
>
> 1. **Lee el crudo** y calcula `clase_ternaria`. Clase binaria: BAJA+1 y BAJA+2 = 1.
> 2. **Data quality:** `ccajas_depositos` está rota en 202105 (todo cero), así que se pone NA solo en ese mes.
> 3. **Ranking con cero fijo**, por variable y por mes: positivos en (0, 1], negativos en \[−1, 0), el cero queda en cero y los NA quedan NA. Se aplica a las 152 variables.
> 4. **Lags y delta lags de orden 1 y 2** calculados sobre los rankings. Después se eliminan las variables originales. Cada variable deja 5 columnas: ranking, lag1, delta1, lag2 y delta2.
> 5. **Optimización de hiperparámetros sin undersampling:**
>
>    * train 202103+04, validación 202106 completo, métrica AUC, una semilla (106937), sin los préstamos personales (750 columnas);
>    * solo el diseño inicial de 10 puntos, sin iteraciones inteligentes;
>    * se elige la configuración de mayor AUC.
> 6. **Curva de ganancia en junio** de la configuración elegida, con 5 semillas y su ensamble. Es para mirar los envíos óptimos en junio y no interviene en la predicción.
> 7. **Entrenamiento final:** 202103 a 202106, sin undersampling, con los préstamos personales reincorporados ya rankeados (760 columnas).
> 8. **109 modelos** con los mismos hiperparámetros, uno por semilla. Se usan las primeras 109.
> 9. **Ensamble:** promedio simple de probabilidades por `numero_de_cliente`, y un archivo por corte con los clientes de mayor probabilidad.
> 10. **Validación de formato** de todos los archivos: entre 8000 y 15000 filas, enteros sin encabezado, sin repetidos y solo clientes de 202108.
>
> ## Resultados esperados (para verificar la réplica)
>
> **Controles que imprime el log:**
>
> ```
> npos 202103-05 = 6095 | ancla = 6095 -> OK
> variables base a rankear: 152 | esperadas: 152 -> OK
> columnas del modelo FINAL: 760 | esperadas: 760 -> OK
> columnas de la BO (sin prestamos personales): 750 | esperadas: 750 -> OK
> modelos terminados: 109
> archivos validados: 335
> ```
>
> **Optimización de hiperparámetros** (debe dar esta tabla; se guarda en `bo_top_configs.csv`):
>
> |Iteración|Hojas|Hessiano|Árboles|AUC en 202106|
> |-|-|-|-|-|
> |**10 (elegida)**|**45**|**0,0244994712564396**|**2428**|**0,917295**|
> |2|65|0,001693|2058|0,917282|
> |6|80|0,013967|3259|0,917214|
> |1|96|0,005135|1226|0,917200|
> |3|111|0,028195|1011|0,917185|
> |4|31|0,011653|3017|0,917177|
> |8|89|0,019771|2049|0,916909|
> |7|128|0,016312|2685|0,916299|
> |5|18|0,007160|1708|0,915654|
> |9|51|0,023864|779|0,914558|
>
> **Curva de junio:** AUC del ensamble de 5 semillas en 202106 = 0,91792.
>
> ### Si la optimización eligiera otra configuración
>
> La iteración 10 le gana a la 2 por solo 0,00001 de AUC. Con lightgbm 4.7.0 y 16 hilos se reproduce exactamente; con otro entorno, una diferencia numérica mínima podría invertir la elección.
>
> Si `bo_mejor_config.csv` no muestra 45 hojas, hessiano 0,0244994712564396 y 2428 árboles, hay que:
>
> 1. descomentar en el script la línea marcada **`[ENTREGA 6] RESPALDO`**, que escribe `bo_mejor_config.csv` con esos valores;
> 2. volver a correr en una carpeta **nueva**.
>
> El script usa entonces esa configuración sin repetir la optimización.
>
> ## Cambios respecto del script original
>
> En el código, cada cambio está marcado `[ENTREGA n]`, con la línea original comentada y la nueva debajo.
>
> |Marca|Original|En la entrega|Motivo|
> |-|-|-|-|
> |ENTREGA 1|Usaba zlightgbm si estaba instalado, si no lightgbm|Siempre lightgbm, y exige la versión 4.7.0|En la notebook se usó lightgbm 4.7.0; zlightgbm daría otras predicciones|
> |ENTREGA 2|Rutas locales de mi PC y de mi VM (solo funcionan ahí)|Rutas relativas a la carpeta de trabajo|Que corra en cualquier máquina|
> |ENTREGA 3|Sin `num_threads` (LightGBM usaba los 16 hilos de la notebook)|`num_threads = 16`|Misma cantidad de hilos en otra máquina|
> |ENTREGA 4|Entrenaba semillas en orden hasta que se creaba `PARAR.txt` (paró en 109)|Las primeras 109 de la misma lista|Que la cantidad de modelos quede fija en el código|
> |ENTREGA 5|Copiaba archivos ya calculados con este mismo código (BO, curva de junio y modelos ya entrenados)|No copia nada: hace todo desde el crudo|Que el script sea autocontenido|
> |ENTREGA 6|—|Línea comentada de respaldo con la configuración elegida|Por si la optimización eligiera otra (ver arriba)|
> |ENTREGA 7|Otro nombre de carpeta del experimento y de los archivos de cada modelo|`C1-E780-PR2108-final` y `prob_modelo_s<semilla>.csv`|Nombres más claros; no afecta el cálculo ni el nombre del archivo entregado|
>
> ## Elección del corte
>
> El corte se eligió combinando tres fuentes:
>
> * **Curva de cortes en el leaderboard público:** promedio de 20 semillas en cada corte entre 8000 y 15000, más ensambles de 20, 50 y 109 semillas.
> * **Curva de ganancia en junio:** es el mes de validación.
> * **Puntaje público:** se tomó con cautela.
>
> **Lo que mostraron las curvas:**
>
> * Las dos tienen un acantilado por debajo de unos 10.000 envíos y una meseta desde ahí.
> * En el tramo 10.500 a 12.000, ningún corte pierde más de 1,2 % respecto del mejor de cada curva.
> * Se evitaron los picos aislados del público.
>
> **Corte elegido: 11.000.** Está dentro de la meseta de las dos curvas y deja margen respecto del "acantilado", que puede correrse en agosto (se consideró que era mejor pasarse que quedarse corto). En junio rinde apenas mejor que 10.500, y en el público la diferencia entre ambos puede ser ruido.

