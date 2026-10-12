# ARojasV — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: ArielRojasV
- Repositorio: https://github.com/ArielRojasV/PrediccionBajas_DMEyF
- Link posteado: https://github.com/ArielRojasV/PrediccionBajas_DMEyF
- Commit: 9f30b843e7698d63719c40293c6f456bb5932fed
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/arielrojasv/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/arielrojasv.json

## Resumen

El repositorio tiene un README y tres notebooks de Google Colab. IngenieriaAtributos.ipynb (Python con SQL sobre DuckDB) lee competencia_01_crudo.csv y agrega lag 1, lag 2 y sus deltas para 26 variables de montos, lags de Master_status y Visa_status, la suma de seguros, dos cocientes contra el promedio del mes y una marca de payroll alto; exporta competencia_01_fe_Final.csv. Optimizador_HiperParametros.ipynb (R) calcula clase_ternaria, corre una optimización bayesiana de 12 evaluaciones sobre num_iterations, num_leaves y min_sum_hessian_in_leaf de LightGBM con 202103 y 202104 (partición 70/30, métrica auc), y después entrena con esos dos meses y calcula en 202106 la ganancia para cortes de 9.000 a 15.000 envíos. Modelo_Final.ipynb (R) tiene escritos los tres hiperparámetros resultantes (2021, 945 y 0.0875), usa clase binaria con BAJA+1 y BAJA+2 como positivos, entrena 5 LightGBM con semillas distintas sobre los meses de PARAM$train_final, promedia las probabilidades de 202108 y escribe exp_final_115.csv con los 11.500 clientes de mayor probabilidad. PARAM$train_final está escrito como c(202103, 202104, 2021505, 202106): el tercer valor tiene siete dígitos y el filtro por igualdad selecciona las filas de 202103, 202104 y 202106.

**Qué entrega.** Un CSV, exp_final_115.csv, con la columna numero_de_cliente de los 11.500 clientes de 202108 con mayor probabilidad promedio. Se escribe en la carpeta del experimento en Google Drive (/content/drive/MyDrive/dmeyf/exp/HT4950-ExpFinal/); el archivo no está en el repositorio.

**Cómo se ejecuta.** Según el README: primero IngenieriaAtributos.ipynb, que genera el CSV con los atributos nuevos; después Modelo_Final.ipynb, que genera el CSV con los números de cliente. Optimizador_HiperParametros.ipynb va después de IngenieriaAtributos y el README indica que puede saltearse porque sus hiperparámetros ya están escritos en Modelo_Final. Los notebooks de R indican montar Google Drive con el runtime de Colab en Python 3 y luego cambiar el runtime a R.

## Ficha

- **Lenguajes:** Python, SQL, R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase01): 1 para BAJA+1 y BAJA+2, 0 para el resto. La clase_ternaria se calcula en los notebooks de R a partir de los meses en que aparece cada cliente (leads de orden 1 y 2 del período).
- **Meses de entrenamiento:** 202103, 202104, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica. En el optimizador PARAM$trainingstrategy$undersampling vale 1 (todas las filas de CONTINUA quedan en entrenamiento) y Modelo_Final no tiene paso de submuestreo. El README dice 'No se uso undersampling'.
- **Calidad de datos:** No se observa corrección de valores. El texto de los notebooks de R dice que ccajas_depositos se elimina por dato faltante en 202105; en la lista de exclusión el nombre está escrito como 'ccajas_depositos ' (con un espacio al final).
- **Drifting:** Se quitan de las columnas del modelo cprestamos_personales y mprestamos_personales; el texto del notebook dice que cambian de distribución entre 202104 y 202106. Los lags y deltas de mprestamos_personales generados en la ingeniería de atributos no figuran en la lista de exclusión. No se observa rank ni deflación. Dos variables nuevas dividen el valor por el promedio del mes (mpayroll_relativa y mrentabilidad_relativa); las originales no se modifican.
- **Variables dentro del mes:** cseguros (suma de cseguro_vida, cseguro_auto, cseguro_vivienda y cseguro_accidentes_personales); mpayroll_relativa y mrentabilidad_relativa (valor dividido por el promedio de esa variable en el mes, redondeado a 2 decimales); flag_superior_payroll (1 si mpayroll supera el 95% del máximo de mpayroll del mes, 0 en otro caso).
- **Variables históricas:** Con funciones de ventana SQL por numero_de_cliente ordenadas por foto_mes: lag 1, lag 2, delta contra lag 1 y delta contra lag 2 de 26 variables de montos (mpayroll, mcuentas_saldo, mrentabilidad, mcomisiones, mactivos_margen, mpasivos_margen, mcuenta_corriente, mcaja_ahorro, mautoservicio, consumos de tarjeta, préstamos prendarios y personales, plazos fijos, débitos automáticos, extracciones, matm y consumo, límite, saldo y pagos de Visa y Master); lag 1 y lag 2 de Master_status y Visa_status. No se observan tendencias, promedios ni mínimos o máximos de ventana.
- **Selección de variables:** Exclusión a mano de siete nombres: cprestamos_personales, mprestamos_personales, 'ccajas_depositos ' (escrito con espacio final) y las cuatro variables de seguros que se sumaron en cseguros. El resto de las columnas del CSV, entre ellas numero_de_cliente y foto_mes, queda en campos_buenos. No se observa selección por importancia.
- **Optimización de hiperparámetros:** Optimización bayesiana con bbotk y mlr3mbo (bayesopt_ego, modelo sustituto regr.km de DiceKriging, adquisición ei, búsqueda al azar de 1000 puntos) con terminador de 12 evaluaciones. Rangos: num_iterations 64 a 4096, num_leaves 16 a 2048, min_sum_hessian_in_leaf 1e-06 a 0.1. Cada evaluación entrena con el 70% de 202103 y 202104 y mide auc en el 30% restante. Según la salida guardada en el notebook, las 12 configuraciones se evalúan en un único lote y la de mayor auc (0.9306129) es la número 10: num_iterations 2021, num_leaves 945, min_sum_hessian_in_leaf 0.08749677.
- **Hiperparámetros finales:** Escritos en Modelo_Final: boosting gbdt, objective binary, metric auc, learning_rate 0.005, feature_fraction 0.50, num_iterations 2021, num_leaves 945, min_sum_hessian_in_leaf 0.087496770828561, min_data_in_leaf 0, max_bin 31, max_depth -1, lambda_l1 0, lambda_l2 0, min_gain_to_split 0, bagging_fraction 1.0, is_unbalance FALSE, scale_pos_weight 1.0, extra_trees FALSE, early_stopping 0.
- **Semillas:** Semilla primigenia 366889. Con set.seed(366889) y sample(1:100000, 5) se sortean 5 semillas; cada una reemplaza el parámetro seed de LightGBM en un entrenamiento.
- **Cantidad de semillas:** 5
- **Ensamble:** Promedio aritmético de las probabilidades de 5 modelos LightGBM con los mismos datos e hiperparámetros y distinta semilla.
- **Corte:** Cantidad fija: los 11.500 clientes de mayor probabilidad promedio (pos <= 11500). El README dice que el corte se determinó con la curva de envíos de 202106 que imprime el optimizador para 13 cortes, de 9.000 a 15.000 de a 500. Según la salida guardada de ese notebook: 11.000 envíos 432.300.000; 11.500 envíos 432.850.000; 12.000 envíos 435.600.000; 12.500 envíos 432.850.000.
- **Validación:** En el optimizador: partición aleatoria de 202103 y 202104 en 70% y 30%, estratificada por clase_ternaria, con auc sobre el 30% como métrica de la optimización; después un modelo entrenado con 202103 y 202104 completos se aplica a 202106 y se calcula la ganancia (1072500 por cada BAJA+2 y -27500 por el resto) para cortes de 9.000 a 15.000 envíos. Modelo_Final no tiene validación: entrena con las filas cuyo foto_mes está en PARAM$train_final, escrito como c(202103, 202104, 2021505, 202106), y predice 202108.
- **Salidas:** IngenieriaAtributos: competencia_01_fe_Final.csv en /content/drive/MyDrive/dmeyf/datasets/. Notebooks de R: competencia_01_fe_Final.csv.gz (con clase_ternaria) en la misma carpeta. Optimizador: BO_log.txt en /content/drive/MyDrive/dmeyf/exp/HT4950-ExpFinal/ y la curva de ganancia de 202106 impresa en pantalla. Modelo_Final: exp_final_115.csv con la columna numero_de_cliente (posiciones 1 a 11500) en la carpeta del experimento.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: Google Colab con Google Drive montado en /content/drive (rutas /content/drive/MyDrive/dmeyf/datasets/ y /content/drive/MyDrive/dmeyf/exp/). El notebook de atributos usa kernel Python 3; los de predicción indican montar Drive con runtime Python 3 y pasar después a runtime R. Los paquetes se instalan dentro de los notebooks (%pip install, install.packages) sin indicar versión.

## Pasos del camino de la entrega

1. **Carga del CSV crudo en DuckDB.** IngenieriaAtributos instala jupysql y duckdb-engine, abre una conexión DuckDB en memoria, monta Google Drive y crea la tabla competencia_01 a partir de competencia_01_crudo.csv con read_csv_auto. (`Script_IngenieriaData/IngenieriaAtributos.ipynb` líneas 11–41)
2. **Lags y deltas de orden 1 y 2.** Una consulta SQL con funciones de ventana por numero_de_cliente, ordenadas por foto_mes, agrega para 26 variables de montos el valor de la fila anterior, el de dos filas atrás y la diferencia del valor actual con cada uno. Para Master_status y Visa_status agrega sólo los dos lags. (`Script_IngenieriaData/IngenieriaAtributos.ipynb` líneas 52–55; `Script_IngenieriaData/IngenieriaAtributos.ipynb` líneas 58–161)
3. **Variables dentro del mes.** La misma consulta suma las cuatro cantidades de seguros en cseguros y, uniendo con una subconsulta por foto_mes (promedio y máximo de mpayroll, promedio de mrentabilidad), calcula mpayroll_relativa, mrentabilidad_relativa y flag_superior_payroll (mpayroll mayor al 95% del máximo del mes). (`Script_IngenieriaData/IngenieriaAtributos.ipynb` líneas 56–57; `Script_IngenieriaData/IngenieriaAtributos.ipynb` líneas 162–174)
4. **Exportación del dataset con atributos.** La consulta está dentro de un COPY que escribe todas las columnas originales más las nuevas en competencia_01_fe_Final.csv, en la carpeta de datasets de Google Drive. (`Script_IngenieriaData/IngenieriaAtributos.ipynb` líneas 46–51; `Script_IngenieriaData/IngenieriaAtributos.ipynb` líneas 176–177)
5. **Cálculo de clase_ternaria.** Los dos notebooks de R empiezan con el mismo bloque: leen competencia_01_fe_Final.csv, convierten foto_mes en un número de período consecutivo, calculan los dos períodos siguientes de cada cliente y asignan CONTINUA, BAJA+1 o BAJA+2; graban el resultado como competencia_01_fe_Final.csv.gz y cuentan filas por mes y clase. Según la salida guardada, el archivo tiene los meses 202103 a 202108 y la clase queda sin valor en 202108 y en parte de 202107. (`Prediccion/Optimizador_HiperParametros.ipynb` líneas 27–77; `Prediccion/Modelo_Final.ipynb` líneas 25–75)
6. **Parámetros y partición para la optimización.** El optimizador fija la semilla 366889, toma 202103 y 202104, los reparte al azar en 70% y 30% estratificando por clase_ternaria, arma la clase binaria (BAJA+1 y BAJA+2 = 1) y deja como columnas del modelo todas menos las auxiliares y los siete nombres excluidos. El espacio de búsqueda es num_iterations 64 a 4096, num_leaves 16 a 2048 y min_sum_hessian_in_leaf 1e-06 a 0.1; el resto de los parámetros de LightGBM queda fijo (learning_rate 0.005, feature_fraction 0.50). (`Prediccion/Optimizador_HiperParametros.ipynb` líneas 128–203; `Prediccion/Optimizador_HiperParametros.ipynb` líneas 256–316)
7. **Optimización bayesiana de 12 evaluaciones.** Cada evaluación entrena un LightGBM con el 70% y toma como métrica el auc sobre el 30%; el resultado se agrega a BO_log.txt. La optimización usa mlr3mbo (bayesopt_ego) con modelo sustituto de kriging, adquisición ei y terminador de 12 evaluaciones. Según la salida guardada, las 12 configuraciones se evalúan en un único lote, el auc va de 0.9117 a 0.9306 y la de mayor auc tiene num_iterations 2021, num_leaves 945 y min_sum_hessian_in_leaf 0.08749677. (`Prediccion/Optimizador_HiperParametros.ipynb` líneas 321–427)
8. **Prueba en 202106 y curva de ganancia por cantidad de envíos.** El optimizador toma del log la fila de mayor métrica, entrena un modelo con 202103 y 202104 completos, predice 202106 y, ordenando por probabilidad, imprime la ganancia (1072500 por BAJA+2, -27500 por el resto) para 13 cortes. Según la salida guardada: 9000 → 412.500.000; 9500 → 424.050.000; 10000 → 425.700.000; 10500 → 431.750.000; 11000 → 432.300.000; 11500 → 432.850.000; 12000 → 435.600.000; 12500 → 432.850.000; 13000 → 432.300.000; 13500 → 426.250.000; 14000 → 416.900.000; 14500 → 409.750.000; 15000 → 403.700.000. El README dice que esta curva se usó para determinar el corte. (`Prediccion/Optimizador_HiperParametros.ipynb` líneas 441–508)
9. **Parámetros del modelo final.** Modelo_Final define el experimento HT4950-ExpFinal, la semilla 366889, los meses de entrenamiento c(202103, 202104, 2021505, 202106), el mes a predecir 202108 y los parámetros de LightGBM con num_iterations 2021, num_leaves 945 y min_sum_hessian_in_leaf 0.087496770828561 escritos en el código. (`Prediccion/Modelo_Final.ipynb` líneas 122–177)
10. **Selección de columnas, clase binaria y filas de entrenamiento.** Lee competencia_01_fe_Final.csv.gz, arma campos_buenos con todas las columnas menos clase_ternaria y los siete nombres excluidos, crea clase01 (BAJA+1 y BAJA+2 = 1) y se queda con las filas cuyo foto_mes está en PARAM$train_final. El filtro compara por igualdad: con la lista tal como está escrita coinciden las filas de 202103, 202104 y 202106. (`Prediccion/Modelo_Final.ipynb` líneas 187–189; `Prediccion/Modelo_Final.ipynb` líneas 205–209; `Prediccion/Modelo_Final.ipynb` líneas 225–235)
11. **Entrenamiento con 5 semillas y promedio.** Sortea 5 semillas con set.seed(366889) y sample(1:100000, 5). Para cada una entrena un LightGBM con los mismos datos y parámetros, predice las filas de 202108 y acumula la probabilidad; al final divide por 5. (`Prediccion/Modelo_Final.ipynb` líneas 240–279)
12. **Ordenamiento y archivo de salida.** Ordena los clientes de 202108 de mayor a menor probabilidad promedio, numera las posiciones y escribe en exp_final_115.csv la columna numero_de_cliente de las primeras 11500. (`Prediccion/Modelo_Final.ipynb` líneas 281–293)

## Archivos

- `README.md` · explicacion · Markdown · 44 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/arielrojasv/README.md.txt) — Describe las dos carpetas y los tres notebooks, el orden de ejecución, el uso de SQL para los atributos y de R para el modelo, los tres hiperparámetros que se optimizan (num_iterations, num_leaves, min_sum_hessian_in_leaf), que no se usa undersampling, que la métrica optimizada es auc y que la curva de envíos de 202106 se usa para determinar el corte. Indica que el optimizador toma como base un script de Gustavo Pasquini.
- `Prediccion/Optimizador_HiperParametros.ipynb` · principal · Jupyter (R) · 512 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/arielrojasv/Prediccion/Optimizador_HiperParametros.ipynb.txt) — Notebook de R para Colab que calcula clase_ternaria, optimiza tres hiperparámetros de LightGBM con optimización bayesiana sobre 202103 y 202104 y calcula en 202106 la ganancia por cantidad de envíos. Según el README, sus resultados (hiperparámetros y corte) son los que usa Modelo_Final.
- `Prediccion/Modelo_Final.ipynb` · principal · Jupyter (R) · 293 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/arielrojasv/Prediccion/Modelo_Final.ipynb.txt) — Notebook de R para Colab que calcula clase_ternaria, entrena 5 LightGBM con semillas distintas y los hiperparámetros escritos en el código, promedia las probabilidades de 202108 y escribe exp_final_115.csv con 11.500 clientes.
- `Script_IngenieriaData/IngenieriaAtributos.ipynb` · principal · Jupyter (python) · 177 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/arielrojasv/Script_IngenieriaData/IngenieriaAtributos.ipynb.txt) — Notebook de Python para Colab que carga el CSV crudo en DuckDB y, con una sola consulta SQL, agrega lags, deltas y variables calculadas dentro del mes; escribe competencia_01_fe_Final.csv.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### Prediccion/Optimizador_HiperParametros.ipynb

Notebook de R para Colab que calcula clase_ternaria, optimiza tres hiperparámetros de LightGBM con optimización bayesiana sobre 202103 y 202104 y calcula en 202106 la ganancia por cantidad de envíos. Según el README, sus resultados (hiperparámetros y corte) son los que usa Modelo_Final.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–19] Título 'LightGBM Optimizacion Bayesiana', con la indicación de que se basa en un
#   archivo de Gustavo Pasquini (2026), e instrucciones de Colab: con el runtime en Python 3 se monta Google
#   Drive en /content/drive.
#%% celda 1 [texto]
# LightGBM  Optimizacion Bayesiana

En base a archivo - Gustavo Pasquini: 2026

#%% celda 2 [texto]
#### 2.1  Seteo del ambiente en Google Colab

#%% celda 3 [texto]
Esta parte se debe correr con el runtime en Python3
<br>Ir al menu, Runtime -> Change Runtime Type -> Runtime type ->  **Python 3**

#%% celda 4 [texto]
Conectar la virtual machine donde esta corriendo Google Colab con el  Google Drive, para poder tener persistencia de archivos

#%% celda 5 [código]
# primero establecer el Runtime de Python 3
from google.colab import drive
drive.mount('/content/drive')

# [Anotación · líneas 21–50] Con el runtime en R, lee competencia_01_fe_Final.csv con data.table y arma la
#   tabla auxiliar dsimple con la posición de cada fila, el cliente y periodo0 (año × 12 + mes, un número de mes
#   consecutivo). Ordena por cliente y período, guarda el último período y el anteúltimo, y agrega para cada
#   fila los períodos de las dos filas siguientes del mismo cliente (periodo1 y periodo2).
#%% celda 6 [texto]
## Generacion de la clase_ternaria

#%% celda 7 [texto]
Esta parte se debe correr con el runtime en lenguaje **R** Ir al menu, Runtime -> Change Runtime Tipe -> Runtime type -> R

#%% celda 8 [código]
require( "data.table" )

# leo el dataset
dataset <- fread("/content/drive/MyDrive/dmeyf/datasets/competencia_01_fe_Final.csv" )

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

# [Anotación · líneas 52–63] Asigna clase_ternaria: CONTINUA a las filas anteriores al anteúltimo período;
#   BAJA+1 a las filas anteriores al último período cuyo cliente no tiene fila siguiente o la tiene a más de un
#   mes; BAJA+2 a las filas anteriores al anteúltimo período cuyo cliente está en el mes siguiente y no tiene
#   una segunda fila o la tiene a más de dos meses. Las filas que no entran en ningún caso quedan sin clase.
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

# [Anotación · líneas 65–77] Vuelve al orden original, copia clase_ternaria al dataset y lo graba como
#   competencia_01_fe_Final.csv.gz en la carpeta de datasets. La celda siguiente cuenta filas por foto_mes y
#   clase_ternaria.

# pego el resultado en el dataset original y grabo
setorder( dsimple, pos )
dataset[, clase_ternaria := dsimple$clase_ternaria ]

fwrite( dataset,
    file =  "/content/drive/MyDrive/dmeyf/datasets/competencia_01_fe_Final.csv.gz",
    sep = ","
)

#%% celda 9 [código]
setorder( dataset, foto_mes, clase_ternaria, numero_de_cliente)
dataset[, .N, list(foto_mes, clase_ternaria)]

# [Anotación · líneas 79–123] Sección de optimización: muestra fecha y hora, borra todos los objetos de
#   memoria, instala R.utils, rlist, bbotk, mlr3, mlr3mbo, mlr3learners, DiceKriging y lightgbm, y carga esas
#   librerías junto con data.table.
#%% celda 10 [texto]
## 2.2 Optimizacion Hiperparámetros

#%% celda 11 [texto]
Esta parte se debe correr con el runtime en lenguaje R Ir al menu, Runtime -> Change Runtime Type -> Runtime type -> R

#%% celda 12 [texto]
### 2.2.1 Inicio

#%% celda 13 [texto]
limpio el ambiente de R

#%% celda 14 [código]
format(Sys.time(), "%a %b %d %X %Y")

#%% celda 15 [código]
# limpio la memoria
rm(list=ls(all.names=TRUE)) # remove all objects
gc(full=TRUE, verbose=FALSE) # garbage collection

#%% celda 16 [texto]
### 2.2.2 Carga de Librerias

#%% celda 17 [código]
# instalo paquetes
install.packages( c("R.utils", "rlist" ) )

#%% celda 18 [código]
# Librerias  modernas  para la Bayesian Optimization
install.packages( c("bbotk", "mlr3", "mlr3mbo", "mlr3learners", "DiceKriging") )

#%% celda 19 [código]
# el LightGBM
install.packages(c("lightgbm"))

#%% celda 20 [código]
library(data.table)
library(R.utils)
library(rlist)
library(bbotk)
library(mlr3)
library(mlr3mbo)
library(mlr3learners)
library(DiceKriging)
library(lightgbm)

# [Anotación · líneas 125–147] Define PARAM: experimento 'HT4950-ExpFinal', semilla_primigenia 366889,
#   training_pct 70, train y train_final c(202103, 202104), future 202106, cortes de 9000 a 15000 de a 500,
#   undersampling 1 (se toman todas las filas) y 12 iteraciones para la optimización.
#%% celda 21 [texto]
### 2.2.3 Definicion de Parametros

#%% celda 22 [código]
PARAM <- list()
PARAM$experimento <- "HT4950-ExpFinal"
PARAM$semilla_primigenia <-  366889  # Semilla primigenia

#%% celda 23 [código]
# training y future
PARAM$training_pct <- 70
PARAM$train <- c( 202103, 202104)
PARAM$train_final <- c( 202103, 202104)
PARAM$future <- c(202106)  # Mes a predecir
PARAM$cortes <- seq(9000, 15000, by= 500)

#%% celda 24 [código]
# undersampling de 1.0  implica tomar TODOS los datos

PARAM$trainingstrategy$undersampling <- 1

#%% celda 25 [código]
PARAM$hyperparametertuning$iteraciones <- 12 # iteraciones bayesianas

# [Anotación · líneas 149–192] Parámetros fijos de LightGBM: boosting gbdt, objective binary, metric auc, seed
#   366889, max_bin 31, min_data_in_leaf 0, feature_fraction 0.50, learning_rate 0.005, sin bagging ni
#   regularización l1/l2. Los tres que la optimización reemplaza figuran con valores iniciales: num_iterations
#   20000, num_leaves 1024 y min_sum_hessian_in_leaf 1e-06.
#%% celda 26 [código]
# Parametros LightGBM

# parametros fijos del LightGBM que se pisaran con la parte variable de la BO
PARAM$lgbm$param_fijos <-  list(
  boosting= "gbdt", # puede ir  dart  , ni pruebe random_forest
  objective= "binary",
  metric= "auc" ,
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
  min_data_in_leaf= 0,     # fijo
  feature_fraction= 0.50,  # fijo
  learning_rate= 0.005,    # fijo

  num_iterations= 20000,     # se modificara
  num_leaves= 1024,          # se modificara
  min_sum_hessian_in_leaf= 1e-06  # se modificara
)

# [Anotación · líneas 194–203] Espacio de búsqueda: num_iterations entero entre 64 y 4096, num_leaves entero
#   entre 16 y 2048 y min_sum_hessian_in_leaf real entre 1e-06 y 0.1.
#%% celda 27 [texto]
Aqui se definen los hiperparámetros de LightGBM que participan de la Bayesian Optimization

#%% celda 28 [código]
# Hiperparametros a optimizar
PARAM$hypeparametertuning$hs <- ps(
  num_iterations= p_int(lower= 64L,  upper= 4096L),
  num_leaves= p_int(lower= 16L,  upper= 2048L),
  min_sum_hessian_in_leaf= p_dbl( lower=1e-06, upper=0.1)
)

# [Anotación · líneas 205–215] Función particionar: agrega al dataset una columna (por defecto fold) que
#   reparte las filas al azar en bloques con las proporciones de division, por separado dentro de cada valor de
#   la columna agrupa y con semilla opcional.
#%% celda 29 [código]
# particionar agrega una columna llamada fold a un dataset que consiste en una particion estratificada segun agrupa

particionar <- function(data, division, agrupa= "", campo= "fold", start= 1, seed= NA) {
  if (!is.na(seed)) set.seed(seed, "L'Ecuyer-CMRG")

  bloque <- unlist(mapply(
    function(x, y) {rep(y, x)},division, seq(from= start, length.out= length(division))))

  data[, (campo) := sample(rep(bloque,ceiling(.N / length(bloque))))[1:.N],by= agrupa]
}

# [Anotación · líneas 217–246] Función loguear: agrega un registro a un archivo de texto separado por
#   tabulaciones. Si el archivo no existe escribe primero la línea de títulos; cada registro lleva fecha y hora
#   y los valores de la lista recibida, y también se imprime en pantalla.
#%% celda 30 [código]
# logueo al archivo BO_log.txt
loguear  <- function( preg, arch=NA, verbose=TRUE )
{
  t0 <- Sys.time()
  reg <- copy( preg )
  if( "feature_contri" %in%  names(reg) ) {
    reg$feature_contri <- reg$feature_contri[1]
  }
  archivo <- arch
  if( is.na(arch) ) archivo <- paste0( folder, substitute( reg), ext )


  if( !file.exists( archivo ) )
  {
    # Escribo los titulos
    linea  <- paste0( "fecha\t",
                      paste( list.names(reg), collapse="\t" ), "\n" )

    cat( linea, file=archivo )
  }

  # escribo el registro
  linea  <- paste0( format(t0, "%Y%m%d.%H%M%S"),  "\t",     # la fecha y hora
                    gsub( ", ", "\t", toString( reg ) ),  "\n" )

  cat( linea, file=archivo, append=TRUE )  # grabo al archivo

  if( verbose )  cat( linea )   # imprimo por pantalla
}

# [Anotación · líneas 248–268] Fija como directorio de trabajo la carpeta del experimento, lee
#   competencia_01_fe_Final.csv.gz, se queda con las filas de 202103 y 202104 y las reparte con particionar en
#   fold 1 (70%) y fold 2 (30%), estratificando por clase_ternaria con la semilla 366889.
#%% celda 31 [texto]
### 2.2.4  Preprocesamiento

#%% celda 32 [código]
setwd("/content/drive/MyDrive/dmeyf/exp/")
dir.create(PARAM$experimento, showWarnings=FALSE)
setwd( paste0("/content/drive/MyDrive/dmeyf/exp/", PARAM$experimento))

#%% celda 33 [código]
# lectura del dataset
dataset <- fread("/content/drive/MyDrive/dmeyf/datasets/competencia_01_fe_Final.csv.gz", stringsAsFactors= TRUE)

#%% celda 34 [código]
dataset_train <- dataset[foto_mes %in% PARAM$train]

#%% celda 35 [código]
  particionar(dataset_train,
    division= c(PARAM$training_pct, 100L -PARAM$training_pct),
    agrupa= "clase_ternaria",
    seed= PARAM$semilla_primigenia
  )

# [Anotación · líneas 270–298] Crea clase01 (1 para BAJA+1 y BAJA+2, 0 para CONTINUA), una columna azar con
#   valores uniformes y la marca training, que vale 1 en las filas de fold 1 cuyo azar es menor o igual a
#   undersampling (1, es decir todas) o que son BAJA+1 o BAJA+2, y 0 en el resto. campos_buenos son todas las
#   columnas menos clase_ternaria, clase01, fold, azar y training.
#%% celda 36 [código]
# paso la clase a binaria que tome valores {0,1}  enteros
#  BAJA+1 y BAJA+2  son  1,   CONTINUA es 0

dataset_train[,
  clase01 := ifelse(clase_ternaria %in% c("BAJA+2","BAJA+1"), 1L, 0L)
]

#%% celda 37 [código]
# defino los datos que forma parte del training
# aqui se hace el undersampling de los CONTINUA

set.seed(PARAM$semilla_primigenia, kind = "L'Ecuyer-CMRG")
dataset_train[, azar := runif(nrow(dataset_train))]
dataset_train[, training := 0L]

dataset_train[
  foto_mes %in%  PARAM$train &  fold==1 &
    (azar <= PARAM$trainingstrategy$undersampling | clase_ternaria %in% c("BAJA+1", "BAJA+2")),
  training := 1L
]

#%% celda 38 [código]
# los campos que se van a utilizar

campos_buenos <- setdiff(
  colnames(dataset_train),
  c("clase_ternaria", "clase01", "fold", "azar", "training")
)

# [Anotación · líneas 300–316] El texto indica qué variables se eliminan y por qué (préstamos personales por
#   cambio de distribución entre 202104 y 202106, ccajas_depositos por dato faltante en 202105, seguros por
#   estar sumados en una sola variable). El código quita de campos_buenos siete nombres: cprestamos_personales,
#   mprestamos_personales, 'ccajas_depositos ' (escrito con un espacio al final) y las cuatro cseguro_*. setdiff
#   quita sólo los nombres que coinciden exactamente.
#%% celda 39 [texto]
#### 2.2.4.1  Variables a eliminar

#%% celda 40 [texto]
En esa exploracion gráfica del Data Drifting, se vio que estas variables cambian de distribucion entre 202104 y 202106, y se decidió brutalmente eliminarlas

cprestamos_personales

mprestamos_personales

ccajas_depositos se elimina por data faltante en 202105

las variables de seguros se eliminan porque en el feature enginering se sumaron todas en una sola variable.

#%% celda 41 [código]
campos_buenos <- setdiff( campos_buenos, c("cprestamos_personales", "mprestamos_personales" , "ccajas_depositos " ,
                                            "cseguro_vida" , "cseguro_auto" , "cseguro_vivienda" , "cseguro_accidentes_personales") )

# [Anotación · líneas 318–327] Inicializa en 0 el contador de iteraciones giter; si ya existe BO_log.txt lo
#   lee y continúa desde el mayor valor de iter.
#%% celda 42 [texto]
2.2.5 Configuracion Bayesian Optimization

#%% celda 43 [código]
giter <- 0

if( file.exists("BO_log.txt") ){
  tb_BO <- fread("BO_log.txt")
  giter <- tb_BO[, max(iter)]
}

# [Anotación · líneas 329–357] Función objetivo Estimar_lightgbm: combina los parámetros fijos con los tres
#   que propone la optimización, entrena un LightGBM con dtrain y con dvalidate como conjunto de validación,
#   toma modelo$best_score (el auc en validación) como métrica, registra parámetros, iteración y métrica en
#   BO_log.txt y devuelve la métrica.
#%% celda 44 [código]
# En el argumento x llegan los parametros de la bayesiana

Estimar_lightgbm <- function(xs) {

  flush.console()
  giter <<- giter + 1

  # x pisa (o agrega) a param_fijos
  param_completo <- modifyList(PARAM$lgbm$param_fijos, xs)
  xx <- copy(param_completo)

  # entreno LightGBM
  modelo <- lgb.train(
    data= dtrain,
    valids= list( "val"=dvalidate),
    param= param_completo
  )


  # obtengo la ganancia
  xx$iter <- giter
  xx$metrica <- modelo$best_score

  loguear( xx, "BO_log.txt")
  set.seed(PARAM$semilla_primigenia, kind = "L'Ecuyer-CMRG")  # le reordeno a mlr3MBO

  return( list( metrica = xx$metrica) )
}

# [Anotación · líneas 359–380] Arma los lgb.Dataset: dtrain con las filas training == 1 y dvalidate con las
#   filas training == 0 (el fold 2), ambos con campos_buenos como matriz numérica y clase01 como etiqueta, y
#   muestra filas y columnas de cada uno. Según la salida guardada: 228.319 y 97.865 filas, 264 columnas.
#%% celda 45 [código]
# dejo los datos de training en el formato que necesita LightGBM

dtrain <- lgb.Dataset(
  data= data.matrix(dataset_train[training == 1L, campos_buenos, with= FALSE]),
  label= dataset_train[training == 1L, clase01],
  free_raw_data= FALSE
)

nrow(dtrain)
ncol(dtrain)

#%% celda 46 [código]
# datos de validatin en el formato que necesita LightGBM
dvalidate <- lgb.Dataset(
  data= data.matrix(dataset_train[training == 0L, campos_buenos, with= FALSE]),
  label= dataset_train[training == 0L, clase01],
  free_raw_data= FALSE
)

nrow(dvalidate)
ncol(dvalidate)

# [Anotación · líneas 382–421] Configura la optimización: objetivo ObjectiveRFun que maximiza 'metrica' sobre
#   el espacio de búsqueda, instancia OptimInstanceBatchSingleCrit con terminador de 12 evaluaciones, modelo
#   sustituto de kriging (regr.km con optim.method BFGS y nugget.estim), función de adquisición ei (expected
#   improvement), optimizador de la adquisición por búsqueda al azar de 1000 puntos y optimizador 'mbo' con
#   bayesopt_ego. La variable kbayesiana ('bayesiana.RDATA') se define y no vuelve a usarse.
#%% celda 47 [código]
# Aqui comienza la configuracion de la Bayesian Optimization

# en este archivo quedan la evolucion binaria de la BO
kbayesiana <- "bayesiana.RDATA"

funcion_optimizar <- Estimar_lightgbm # la funcion que voy a maximizar

objective <- ObjectiveRFun$new(
  fun= funcion_optimizar,
  domain= PARAM$hypeparametertuning$hs,
  codomain= ps(metrica = p_dbl(tags="maximize")),
  id= "BO_lightgbm"
)


instance <- OptimInstanceBatchSingleCrit$new(
  objective= objective,
  terminator=  trm("evals", n_evals = PARAM$hyperparametertuning$iteraciones)
)


surrogate <- srlrn(lrn("regr.km",
  optim.method = "BFGS",
  nugget.estim = TRUE,
  control= list(trace = FALSE)))

acq_function  <- acqf("ei")

acq_optimizer  <- acqo(
  optimizer  = opt("random_search", batch_size= 1000),
  terminator = trm("evals", n_evals= 1000)
)

optimizer <- opt("mbo",
  loop_function = bayesopt_ego,
  surrogate= surrogate,
  acq_function= acq_function,
  acq_optimizer= acq_optimizer
)

# [Anotación · líneas 423–427] Ejecuta la optimización con optimizer$optimize(instance) y guarda el resultado
#   en bayesiana_salida.
#%% celda 48 [texto]
2.2.6 Corrida Bayesian Optimization

#%% celda 49 [código]
bayesiana_salida <- optimizer$optimize(instance)

# [Anotación · líneas 429–445] Sección de producción: fija la carpeta del experimento, lee BO_log.txt, lo
#   ordena por metrica de mayor a menor y guarda la primera fila como lista de hiperparámetros elegidos.
#%% celda 50 [texto]
## 2.3  Produccion

#%% celda 51 [texto]
### Final Training
Construyo el modelo final, que es uno solo, no hace ningun tipo de particion < training, validation, testing>]

#%% celda 52 [código]
setwd("/content/drive/MyDrive/dmeyf/exp/")
dir.create(PARAM$experimento, showWarnings= FALSE)
setwd( paste0("/content/drive/MyDrive/dmeyf/exp/", PARAM$experimento ))

#%% celda 53 [código]
 # cergo los mejores hiperparametros, que son los de mayor metrica
 tb_bayesiana <- fread("BO_log.txt")
 setorder( tb_bayesiana, -metrica )
 PARAM$out$lgbm$mejores_hiperparametros <- as.list(tb_bayesiana[1])

# [Anotación · líneas 447–482] Crea clase01 en todo el dataset, arma dataset_train con 202103 y 202104
#   completos y muestra el conteo por mes y clase; pisa los parámetros fijos con la fila elegida del log, separa
#   dfuture con las filas de 202106, arma el lgb.Dataset con campos_buenos y clase01 y entrena un único modelo.
#%% celda 54 [texto]
#### Final Training Dataset

#%% celda 55 [código]
# clase01
dataset[, clase01 := ifelse(clase_ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)]

#%% celda 56 [código]
dataset_train <- dataset[foto_mes %in% PARAM$train_final]
dataset_train[,.N, list(foto_mes, clase_ternaria)]

#%% celda 57 [texto]
#### Final Training Hyperparameters

#%% celda 58 [código]
param_final <- modifyList(PARAM$lgbm$param_fijos,
  PARAM$out$lgbm$mejores_hiperparametros)

param_final

#%% celda 59 [código]
# aplico el modelo a los datos sin clase
dfuture <- dataset[foto_mes %in% PARAM$future]

#%% celda 60 [código]
# Entreno el modelo sobre todo el periodo

dtrain_final <- lgb.Dataset(
  data= data.matrix(dataset_train[, campos_buenos, with= FALSE]),
  label= dataset_train[, clase01]
)

modelo_final <- lgb.train(
  data= dtrain_final,
  param= param_final
)

# [Anotación · líneas 484–512] Predice 202106 y arma la tabla con cliente, mes, clase y probabilidad; asigna a
#   cada fila la ganancia 1072500 si es BAJA+2 y -27500 en otro caso, ordena de mayor a menor probabilidad y
#   calcula ganancia acumulada y posición. Para cada valor de PARAM$cortes imprime la cantidad de envíos y la
#   suma de ganancias de esas primeras filas. La última celda muestra la tabla.
#%% celda 61 [código]
# hago el predict en los datos del futuro, y calculo la ganancia

# aplico el modelo a los datos nuevos
prediccion <- predict(
  modelo_final,
  data.matrix(dfuture[, campos_buenos, with= FALSE])
)

#%% celda 62 [código]
# calculo la ganancia en los datos ddel futuro para todos los cortes
tb_prediccion <- dfuture[, list(numero_de_cliente, foto_mes,clase_ternaria)]
tb_prediccion[, prob := prediccion ]
tb_prediccion[, gan := ifelse(clase_ternaria == "BAJA+2", 1072500, -27500)]

# lgb.save(modelo_final, "modelo.txt" )
# Dibujo la curva de ganancia acumulada
setorder(tb_prediccion, -prob)
tb_prediccion[, ganancia_acumulada := cumsum(gan)]
tb_prediccion[, pos := sequence(.N)]

for (envios in PARAM$cortes) {
  ganancia <- tb_prediccion[1:envios, sum(gan)]
  cat( envios, "\t", ganancia, "\n")
}

#%% celda 63 [código]
# Clientes y probabilidades
tb_prediccion
```

### Prediccion/Modelo_Final.ipynb

Notebook de R para Colab que calcula clase_ternaria, entrena 5 LightGBM con semillas distintas y los hiperparámetros escritos en el código, promedia las probabilidades de 202108 y escribe exp_final_115.csv con 11.500 clientes.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–17] Título e instrucciones de Colab en celdas de texto: con el runtime en Python 3 se
#   monta Google Drive en /content/drive.
#%% celda 1 [texto]
# Modelo Final com LightGBM

#%% celda 2 [texto]
#### 2.1  Seteo del ambiente en Google Colab

#%% celda 3 [texto]
Esta parte se debe correr con el runtime en Python3
<br>Ir al menu, Runtime -> Change Runtime Type -> Runtime type ->  **Python 3**

#%% celda 4 [texto]
Conectar la virtual machine donde esta corriendo Google Colab con el  Google Drive, para poder tener persistencia de archivos

#%% celda 5 [código]
# primero establecer el Runtime de Python 3
from google.colab import drive
drive.mount('/content/drive')

# [Anotación · líneas 19–48] Con el runtime en R, lee competencia_01_fe_Final.csv con data.table y arma la
#   tabla auxiliar dsimple con la posición de cada fila, el cliente y periodo0 (año × 12 + mes, un número de mes
#   consecutivo). Ordena por cliente y período, guarda el último período y el anteúltimo, y agrega para cada
#   fila los períodos de las dos filas siguientes del mismo cliente (periodo1 y periodo2).
#%% celda 6 [texto]
## Generacion de la clase_ternaria

#%% celda 7 [texto]
Esta parte se debe correr con el runtime en lenguaje **R** Ir al menu, Runtime -> Change Runtime Tipe -> Runtime type -> R

#%% celda 8 [código]
require( "data.table" )

# leo el dataset
dataset <- fread("/content/drive/MyDrive/dmeyf/datasets/competencia_01_fe_Final.csv" )

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

# [Anotación · líneas 50–61] Asigna clase_ternaria: CONTINUA a las filas anteriores al anteúltimo período;
#   BAJA+1 a las filas anteriores al último período cuyo cliente no tiene fila siguiente o la tiene a más de un
#   mes; BAJA+2 a las filas anteriores al anteúltimo período cuyo cliente está en el mes siguiente y no tiene
#   una segunda fila o la tiene a más de dos meses. Las filas que no entran en ningún caso quedan sin clase.
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


# [Anotación · líneas 64–75] Vuelve al orden original, copia clase_ternaria al dataset y lo graba como
#   competencia_01_fe_Final.csv.gz en la carpeta de datasets. La celda siguiente cuenta filas por foto_mes y
#   clase_ternaria.
# pego el resultado en el dataset original y grabo
setorder( dsimple, pos )
dataset[, clase_ternaria := dsimple$clase_ternaria ]

fwrite( dataset,
    file =  "/content/drive/MyDrive/dmeyf/datasets/competencia_01_fe_Final.csv.gz",
    sep = ","
)

#%% celda 9 [código]
setorder( dataset, foto_mes, clase_ternaria, numero_de_cliente)
dataset[, .N, list(foto_mes, clase_ternaria)]

# [Anotación · líneas 77–113] Sección de reentrenamiento: muestra fecha y hora, borra todos los objetos de
#   memoria (rm y gc), instala R.utils, rlist y lightgbm, y carga data.table, R.utils, rlist y lightgbm.
#%% celda 10 [texto]
## 2.2 Reentreno modelo con nueva información

#%% celda 11 [texto]
Esta parte se debe correr con el runtime en lenguaje R Ir al menu, Runtime -> Change Runtime Type -> Runtime type -> R

#%% celda 12 [texto]
### 2.2.1 Inicio

#%% celda 13 [texto]
limpio el ambiente de R

#%% celda 14 [código]
format(Sys.time(), "%a %b %d %X %Y")

#%% celda 15 [código]
# limpio la memoria
rm(list=ls(all.names=TRUE)) # remove all objects
gc(full=TRUE, verbose=FALSE) # garbage collection

#%% celda 16 [texto]
### 2.2.2 Carga de Librerias

#%% celda 17 [código]
# instalo paquetes
install.packages( c("R.utils", "rlist" ) )

#%% celda 18 [código]
# el LightGBM
install.packages(c("lightgbm"))

#%% celda 19 [código]
# Cargo Librerias
library(data.table)
library(R.utils)
library(rlist)
library(lightgbm)

# [Anotación · líneas 115–132] Define PARAM: experimento 'HT4950-ExpFinal', semilla_primigenia 366889,
#   training_pct 70, train_final c(202103, 202104, 2021505, 202106), future 202108 y cortes de 9000 a 15000 de a
#   500. El tercer valor de train_final está escrito con siete dígitos (2021505). training_pct y cortes no
#   vuelven a usarse en este notebook.
#%% celda 20 [texto]
### 2.2.3 Definicion de Parametros

#%% celda 21 [texto]
aqui debe cargar SU semilla primigenia
<br>recuerde cambiar el numero de experimento en cada corrida nueva

#%% celda 22 [código]
PARAM <- list()
PARAM$experimento <- "HT4950-ExpFinal"
PARAM$semilla_primigenia <-  366889   # semilla primigenia

#%% celda 23 [código]
# training y future
PARAM$training_pct <- 70
PARAM$train_final <- c( 202103, 202104, 2021505, 202106)  # Todos los meses salvo julio y agosto
PARAM$future <- c(202108)
PARAM$cortes <- seq(9000, 15000, by= 500)

# [Anotación · líneas 134–177] Parámetros de LightGBM: boosting gbdt, objective binary, metric auc, seed igual
#   a la semilla primigenia, max_depth -1, max_bin 31, lambda_l1 y lambda_l2 0, bagging_fraction 1.0,
#   is_unbalance FALSE, scale_pos_weight 1.0, early_stopping 0, min_data_in_leaf 0, feature_fraction 0.50 y
#   learning_rate 0.005. Los tres últimos, num_iterations 2021, num_leaves 945 y min_sum_hessian_in_leaf
#   0.087496770828561, llevan un comentario que indica que provienen del optimizador.
#%% celda 24 [código]
# Parametros LightGBM

# parametros fijos del LightGBM que se pisaran con la parte variable de la BO
PARAM$lgbm$param_fijos <-  list(
  boosting= "gbdt",
  objective= "binary",
  metric= "auc" ,
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
  min_data_in_leaf= 0,
  feature_fraction= 0.50,
  learning_rate= 0.005,

  num_iterations= 2021,     ## Mejor Hiperparametro a partir optimizador
  num_leaves= 945,          ## Mejor Hiperparametro a partir optimizador
  min_sum_hessian_in_leaf= 0.087496770828561    ## Mejor Hiperparametro a partir optimizador
)

# [Anotación · líneas 179–189] Crea la carpeta del experimento dentro de /content/drive/MyDrive/dmeyf/exp/, la
#   fija como directorio de trabajo y lee competencia_01_fe_Final.csv.gz con las columnas de texto como
#   factores.
#%% celda 25 [texto]
### 2.2.4  Preprocesamiento

#%% celda 26 [código]
setwd("/content/drive/MyDrive/dmeyf/exp/")
dir.create(PARAM$experimento, showWarnings=FALSE)
setwd( paste0("/content/drive/MyDrive/dmeyf/exp/", PARAM$experimento))

#%% celda 27 [código]
# lectura del dataset
dataset <- fread("/content/drive/MyDrive/dmeyf/datasets/competencia_01_fe_Final.csv.gz", stringsAsFactors= TRUE)

# [Anotación · líneas 191–209] La celda de texto indica que cprestamos_personales y mprestamos_personales se
#   eliminan porque cambian de distribución entre 202104 y 202106, ccajas_depositos por dato faltante en 202105
#   y las variables de seguros porque ya se sumaron en una sola. El código arma campos_buenos con todas las
#   columnas menos clase_ternaria y menos siete nombres: las dos de préstamos, 'ccajas_depositos ' (escrito con
#   un espacio al final) y las cuatro cseguro_*. setdiff quita sólo los nombres que coinciden exactamente.
#%% celda 28 [texto]
#### 2.2.4.1  Variables a eliminar

#%% celda 29 [texto]
En esa exploracion gráfica del Data Drifting, se vio que estas variables cambian de distribucion entre 202104 y 202106, y se decidió brutalmente eliminarlas

cprestamos_personales

mprestamos_personales

ccajas_depositos se elimina por data faltante en 202105

las variables de seguros se eliminan porque en el feature enginering se sumaron todas en una sola variable.

#%% celda 30 [código]
campos_buenos <- setdiff( colnames(dataset), c("clase_ternaria") )

campos_buenos <- setdiff( campos_buenos, c("cprestamos_personales", "mprestamos_personales" , "ccajas_depositos " ,
                                            "cseguro_vida" , "cseguro_auto" , "cseguro_vivienda" , "cseguro_accidentes_personales") )

# [Anotación · líneas 211–235] Sección de producción: vuelve a fijar la carpeta del experimento, crea clase01
#   (1 si clase_ternaria es BAJA+1 o BAJA+2, 0 en otro caso), arma dataset_train con las filas cuyo foto_mes
#   está en PARAM$train_final y quita clase01 de campos_buenos. El filtro compara por igualdad: con la lista tal
#   como está escrita coinciden las filas de 202103, 202104 y 202106.
#%% celda 31 [texto]
## 2.3  Produccion

#%% celda 32 [texto]
### Final Training

#%% celda 33 [código]
setwd("/content/drive/MyDrive/dmeyf/exp/")
dir.create(PARAM$experimento, showWarnings= FALSE)
setwd( paste0("/content/drive/MyDrive/dmeyf/exp/", PARAM$experimento ))

#%% celda 34 [texto]
Entreno con todos los meses salvo 202107 - 202108

#%% celda 35 [código]
# Redefino las clases
dataset[, clase01 := ifelse(clase_ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)]

#%% celda 36 [código]
# Data set de entrenamiento
dataset_train <- dataset[foto_mes %in% PARAM$train_final]

#%% celda 37 [código]
# Sin campo de clase
campos_buenos <- setdiff( campos_buenos, c("clase01") )

# [Anotación · líneas 237–257] Fija set.seed(366889) y sortea 5 semillas entre 1 y 100000. Separa dfuture con
#   las filas de 202108, arma el lgb.Dataset de entrenamiento con campos_buenos como matriz numérica y clase01
#   como etiqueta, inicializa en cero el vector de predicciones acumuladas y copia los parámetros en
#   param_final.
#%% celda 38 [texto]
#### Prediccion de 202108, con 5 semillas calculando un promedio

#%% celda 39 [código]
# Defino 5 semillas
set.seed(366889) # Semilla base para generar las otras 5
semillas <- sample(1:100000, 5)

# Configuro dataset a predecir
dfuture <- dataset[foto_mes %in% PARAM$future]

dtrain_final <- lgb.Dataset(
  data  = data.matrix(dataset_train[, campos_buenos, with = FALSE]),
  label = dataset_train[, clase01]
)

# Predicciones acumuladas
prediccion_acumulada <- rep(0, nrow(dfuture))

# Mejores Hiperparametros
param_final <- PARAM$lgbm$param_fijos

# [Anotación · líneas 259–279] Para cada una de las 5 semillas reemplaza seed en los parámetros, entrena un
#   LightGBM sobre el mismo dataset de entrenamiento, predice la probabilidad de las filas de 202108 y la suma
#   al acumulado. Al terminar divide el acumulado por la cantidad de semillas para obtener el promedio.
for (semilla in semillas) {
  param_final$seed <- semilla

  # Entrenar el modelo con la semilla
  modelo_final <- lgb.train(
    data  = dtrain_final,
    param = param_final
  )

  # Predicción de la semilla
  prediccion_actual <- predict(
    modelo_final,
    data.matrix(dfuture[, campos_buenos, with = FALSE])
  )

  # Acumulo
  prediccion_acumulada <- prediccion_acumulada + prediccion_actual
}

# Calcular promedio
prediccion_final <- prediccion_acumulada / length(semillas)

# [Anotación · líneas 281–293] Arma la tabla con numero_de_cliente, foto_mes, clase_ternaria y la probabilidad
#   promedio, la ordena de mayor a menor probabilidad y numera las posiciones. Muestra las primeras 12500 y
#   escribe con write_csv de readr la columna numero_de_cliente de las primeras 11500 en exp_final_115.csv.
#  Tabla final
tb_prediccion <- dfuture[, list(numero_de_cliente, foto_mes, clase_ternaria)]
tb_prediccion[, prob := prediccion_final]

setorder(tb_prediccion, -prob)
tb_prediccion[, pos := sequence(.N)]

#%% celda 40 [código]
tb_prediccion[pos <= 12500]

#%% celda 41 [código]
library(readr)
write_csv(tb_prediccion[pos <= 11500, "numero_de_cliente"], "exp_final_115.csv")  # Exporto archivo de clientes hasta 11500
```

### Script_IngenieriaData/IngenieriaAtributos.ipynb

Notebook de Python para Colab que carga el CSV crudo en DuckDB y, con una sola consulta SQL, agrega lags, deltas y variables calculadas dentro del mes; escribe competencia_01_fe_Final.csv.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–9] Celda de título ('Genero nuevos atributos para el dataset') e importación de pandas
#   y numpy.
#%% celda 1 [texto]
## Clientes Banco

Genero nuevos atributos para el dataset

#%% celda 2 [código]
# Importo librerias
import pandas as pd
import numpy as np

# [Anotación · líneas 11–24] Instala jupysql y duckdb-engine con %pip, importa duckdb, carga la extensión sql
#   de Jupyter configurada para devolver los resultados como DataFrame de pandas y abre una conexión DuckDB en
#   memoria (duckdb://).
#%% celda 3 [código]
# Instalo duckdb
%pip install jupysql
%pip install duckdb-engine

#%% celda 4 [código]
import duckdb

%load_ext sql
%config SqlMagic.autopandas = True
%config SqlMagic.feedback = False
%config SqlMagic.displaycon = False

%sql duckdb://

# [Anotación · líneas 26–34] Monta Google Drive en /content/drive y define la carpeta de datos
#   '/content/drive/MyDrive/dmeyf/datasets/' y el archivo de entrada 'competencia_01_crudo.csv'.
#%% celda 5 [código]
# Carpeta Drive
from google.colab import drive
drive.mount("/content/drive")

#%% celda 6 [código]
# Carpetas y archivo a usar
dataset_path = '/content/drive/MyDrive/dmeyf/datasets/'
dataset_file = 'competencia_01_crudo.csv'

# [Anotación · líneas 36–41] Crea o reemplaza la tabla competencia_01 en DuckDB con todas las columnas del
#   CSV, leído con read_csv_auto.
#%% celda 7 [código]
# Cargo archivo original
%%sql
create or replace table competencia_01 as
select *
from read_csv_auto("{{dataset_path + dataset_file}}")

# [Anotación · líneas 43–51] Abre una sentencia COPY cuyo contenido es una consulta 'select *': conserva todas
#   las columnas y agrega las que se definen en las líneas siguientes.
#%% celda 8 [código]
# Genero nuevos atributos y los guardo en un nuevo archivo

%%sql

COPY
(
  select
  *
# [Anotación · líneas 52–57] Para mpayroll calcula, con funciones de ventana por numero_de_cliente ordenadas
#   por foto_mes, el valor de la fila anterior (mpayroll_lag) y el de dos filas atrás (mpayroll_lag2), y la
#   diferencia del valor actual con cada uno (delta_mpayroll y delta_mpayroll_l2). Agrega mpayroll_relativa
#   (mpayroll dividido por el promedio de mpayroll del mes, redondeado a 2 decimales) y cseguros (suma de
#   cseguro_vida, cseguro_auto, cseguro_vivienda y cseguro_accidentes_personales).
  , lag(mpayroll, 1) over (partition by numero_de_cliente order by ori.foto_mes)  as mpayroll_lag
  , lag(mpayroll, 2) over (partition by numero_de_cliente order by ori.foto_mes)  as mpayroll_lag2
  , ( mpayroll - lag(mpayroll, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mpayroll
  , ( mpayroll - lag(mpayroll, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mpayroll_l2
  , round(( mpayroll / paym.mpayroll_prom),2)  as mpayroll_relativa
  , (cseguro_vida + cseguro_auto + cseguro_vivienda + cseguro_accidentes_personales) as cseguros
# [Anotación · líneas 58–89] Repite las cuatro columnas (lag 1, lag 2, delta contra lag 1 y delta contra lag
#   2) para 8 variables: mcuentas_saldo, mrentabilidad, mcomisiones, mactivos_margen, mpasivos_margen,
#   mcuenta_corriente, mcaja_ahorro y mautoservicio. Los alias siguen el patrón variable_lag, variable_lag_2,
#   delta_variable y delta_variable_l2; en la línea 68 el alias está escrito 'asmcomisiones_lag_2', sin espacio
#   después de 'as'.
  , lag(mcuentas_saldo, 1) over (partition by numero_de_cliente order by ori.foto_mes)  as mcuentas_saldo_lag
  , lag(mcuentas_saldo, 2) over (partition by numero_de_cliente order by ori.foto_mes)  as mcuentas_saldo_lag_2
  , ( mcuentas_saldo - lag(mcuentas_saldo, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mcuentas_saldo
  , ( mcuentas_saldo - lag(mcuentas_saldo, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mcuentas_saldo_l2
  , lag(mrentabilidad, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mrentabilidad_lag
  , ( mrentabilidad - lag(mrentabilidad, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mrentabilidad
  , lag(mrentabilidad, 2) over (partition by numero_de_cliente order by ori.foto_mes) as mrentabilidad_lag_2
  , ( mrentabilidad - lag(mrentabilidad, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mrentabilidad_l2
  , lag(mcomisiones, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mcomisiones_lag
  , ( mcomisiones - lag(mcomisiones, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mcomisiones
  , lag(mcomisiones, 2) over (partition by numero_de_cliente order by ori.foto_mes) asmcomisiones_lag_2
  , ( mcomisiones - lag(mcomisiones, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mcomisiones_l2
  , lag(mactivos_margen, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mactivos_margen_lag
  , ( mactivos_margen - lag(mactivos_margen, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mactivos_margen
  , lag(mactivos_margen, 2) over (partition by numero_de_cliente order by ori.foto_mes) as mactivos_margen_lag_2
  , ( mactivos_margen - lag(mactivos_margen, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mactivos_margen_l2
  , lag(mpasivos_margen, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mpasivos_margen_lag
  , ( mpasivos_margen - lag(mpasivos_margen, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mpasivos_margen
  , lag(mpasivos_margen, 2) over (partition by numero_de_cliente order by ori.foto_mes) as mpasivos_margen_lag_2
  , ( mpasivos_margen - lag(mpasivos_margen, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mpasivos_margen_l2
  , lag(mcuenta_corriente, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mcuenta_corriente_lag
  , ( mcuenta_corriente - lag(mcuenta_corriente, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mcuenta_corriente
  , lag(mcuenta_corriente, 2) over (partition by numero_de_cliente order by ori.foto_mes) as mcuenta_corriente_lag_2
  , ( mcuenta_corriente - lag(mcuenta_corriente, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mcuenta_corriente_l2
  , lag(mcaja_ahorro, 1) over (partition by numero_de_cliente order by ori.foto_mes)  as  mcaja_ahorro_lag
  , ( mcaja_ahorro - lag(mcaja_ahorro, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mcaja_ahorro
  , lag(mcaja_ahorro, 2) over (partition by numero_de_cliente order by ori.foto_mes)  as  mcaja_ahorro_lag_2
  , ( mcaja_ahorro - lag(mcaja_ahorro, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mcaja_ahorro_l2
  , lag(mautoservicio, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mautoservicio_lag
  , ( mautoservicio - lag(mautoservicio, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mautoservicio
  , lag(mautoservicio, 2) over (partition by numero_de_cliente order by ori.foto_mes) as mautoservicio_lag_2
  , ( mautoservicio - lag(mautoservicio, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mautoservicio_l2
# [Anotación · líneas 90–125] Las mismas cuatro columnas para 9 variables: mtarjeta_visa_consumo,
#   mtarjeta_master_consumo, mprestamos_prendarios, mprestamos_personales, mplazo_fijo_pesos,
#   mplazo_fijo_dolares, mcuenta_debitos_automaticos, mextraccion_autoservicio y matm.
  , lag(mtarjeta_visa_consumo, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mtarjeta_visa_consumo_lag
  , ( mtarjeta_visa_consumo - lag(mtarjeta_visa_consumo, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mtarjeta_visa_consumo
  , lag(mtarjeta_visa_consumo, 2) over (partition by numero_de_cliente order by ori.foto_mes) as mtarjeta_visa_consumo_lag_2
  , ( mtarjeta_visa_consumo - lag(mtarjeta_visa_consumo, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mtarjeta_visa_consumo_l2
  , lag(mtarjeta_master_consumo, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mtarjeta_master_consumo_lag
  , ( mtarjeta_master_consumo - lag(mtarjeta_master_consumo, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mtarjeta_master_consumo
  , lag(mtarjeta_master_consumo, 2) over (partition by numero_de_cliente order by ori.foto_mes) as mtarjeta_master_consumo_lag_2
  , ( mtarjeta_master_consumo - lag(mtarjeta_master_consumo, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mtarjeta_master_consumo_l2
  , lag(mprestamos_prendarios, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mprestamos_prendarios_lag
  , ( mprestamos_prendarios - lag(mprestamos_prendarios, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mprestamos_prendarios
  , lag(mprestamos_prendarios, 2) over (partition by numero_de_cliente order by ori.foto_mes) as mprestamos_prendarios_lag_2
  , ( mprestamos_prendarios - lag(mprestamos_prendarios, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mprestamos_prendarios_l2
  , lag(mprestamos_personales, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mprestamos_personales_lag
  , ( mprestamos_personales - lag(mprestamos_personales, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mprestamos_personales
  , lag(mprestamos_personales, 2) over (partition by numero_de_cliente order by ori.foto_mes) as mprestamos_personales_lag_2
  , ( mprestamos_personales - lag(mprestamos_personales, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mprestamos_personales_l2
  , lag(mplazo_fijo_pesos, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mplazo_fijo_pesos_lag
  , ( mplazo_fijo_pesos - lag(mplazo_fijo_pesos, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mplazo_fijo_pesos
  , lag(mplazo_fijo_pesos, 2) over (partition by numero_de_cliente order by ori.foto_mes) as mplazo_fijo_pesos_lag_2
  , ( mplazo_fijo_pesos - lag(mplazo_fijo_pesos, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mplazo_fijo_pesos_l2
  , lag(mplazo_fijo_dolares, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mplazo_fijo_dolares_lag
  , ( mplazo_fijo_dolares - lag(mplazo_fijo_dolares, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mplazo_fijo_dolares
  , lag(mplazo_fijo_dolares, 2) over (partition by numero_de_cliente order by ori.foto_mes) as mplazo_fijo_dolares_lag_2
  , ( mplazo_fijo_dolares - lag(mplazo_fijo_dolares, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mplazo_fijo_dolares_l2
  , lag(mcuenta_debitos_automaticos, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mcuenta_debitos_automaticos_lag
  , ( mcuenta_debitos_automaticos - lag(mcuenta_debitos_automaticos, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mcuenta_debitos_automaticos
  , lag(mcuenta_debitos_automaticos, 2) over (partition by numero_de_cliente order by ori.foto_mes) as mcuenta_debitos_automaticos_lag_2
  , ( mcuenta_debitos_automaticos - lag(mcuenta_debitos_automaticos, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mcuenta_debitos_automaticos_l2
  , lag(mextraccion_autoservicio, 1) over (partition by numero_de_cliente order by ori.foto_mes) as mextraccion_autoservicio_lag
  , ( mextraccion_autoservicio - lag(mextraccion_autoservicio, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mextraccion_autoservicio
  , lag(mextraccion_autoservicio, 2) over (partition by numero_de_cliente order by ori.foto_mes) as mextraccion_autoservicio_lag_2
  , ( mextraccion_autoservicio - lag(mextraccion_autoservicio, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_mextraccion_autoservicio_l2
  , lag(matm, 1) over (partition by numero_de_cliente order by ori.foto_mes) as matm_lag
  , ( matm - lag(matm, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_matm
  , lag(matm, 2) over (partition by numero_de_cliente order by ori.foto_mes) as matm_lag_2
  , ( matm - lag(matm, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_matm_l2
# [Anotación · líneas 126–157] Las mismas cuatro columnas para 8 variables de tarjetas: Visa_mconsumototal,
#   Visa_mlimitecompra, Visa_msaldototal, Visa_mpagospesos, Master_mconsumototal, Master_mlimitecompra,
#   Master_msaldototal y Master_mpagospesos. En las líneas 134 y 136 el lag 1 y el lag 2 de Visa_msaldototal
#   llevan el mismo alias, Visa_msaldototal_lag.
  , lag(Visa_mconsumototal, 1) over (partition by numero_de_cliente order by ori.foto_mes) as Visa_mconsumototal_lag
  , ( Visa_mconsumototal - lag(Visa_mconsumototal, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Visa_mconsumototal
  , lag(Visa_mconsumototal, 2) over (partition by numero_de_cliente order by ori.foto_mes) as Visa_mconsumototal_lag_2
  , ( Visa_mconsumototal - lag(Visa_mconsumototal, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Visa_mconsumototal_l2
  , lag(Visa_mlimitecompra, 1) over (partition by numero_de_cliente order by ori.foto_mes) as  Visa_mlimitecompra_lag
  , ( Visa_mlimitecompra - lag(Visa_mlimitecompra, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Visa_mlimitecompra
  , lag(Visa_mlimitecompra, 2) over (partition by numero_de_cliente order by ori.foto_mes) as  Visa_mlimitecompra_lag_2
  , ( Visa_mlimitecompra - lag(Visa_mlimitecompra, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Visa_mlimitecompra_l2
  , lag(Visa_msaldototal, 1) over (partition by numero_de_cliente order by ori.foto_mes) as Visa_msaldototal_lag
  , ( Visa_msaldototal - lag(Visa_msaldototal, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Visa_msaldototal
  , lag(Visa_msaldototal, 2) over (partition by numero_de_cliente order by ori.foto_mes) as Visa_msaldototal_lag
  , ( Visa_msaldototal - lag(Visa_msaldototal, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Visa_msaldototal_l2
  , lag(Visa_mpagospesos, 1) over (partition by numero_de_cliente order by ori.foto_mes) as Visa_mpagospesos_lag
  , ( Visa_mpagospesos - lag(Visa_mpagospesos, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Visa_mpagospesos
  , lag(Visa_mpagospesos, 2) over (partition by numero_de_cliente order by ori.foto_mes) as Visa_mpagospesos_lag_2
  , ( Visa_mpagospesos - lag(Visa_mpagospesos, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Visa_mpagospesos_l2
  , lag(Master_mconsumototal, 1) over (partition by numero_de_cliente order by ori.foto_mes) as Master_mconsumototal_lag
  , ( Master_mconsumototal - lag(Master_mconsumototal, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Master_mconsumototal
  , lag(Master_mconsumototal, 2) over (partition by numero_de_cliente order by ori.foto_mes) as Master_mconsumototal_lag_2
  , ( Master_mconsumototal - lag(Master_mconsumototal, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Master_mconsumototal_l2
  , lag(Master_mlimitecompra, 1) over (partition by numero_de_cliente order by ori.foto_mes) as Master_mlimitecompra_lag
  , ( Master_mlimitecompra - lag(Master_mlimitecompra, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Master_mlimitecompra
  , lag(Master_mlimitecompra, 2) over (partition by numero_de_cliente order by ori.foto_mes) as Master_mlimitecompra_lag_2
  , ( Master_mlimitecompra - lag(Master_mlimitecompra, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Master_mlimitecompra_l2
  , lag(Master_msaldototal, 1) over (partition by numero_de_cliente order by ori.foto_mes) as Master_msaldototal_lag
  , ( Master_msaldototal - lag(Master_msaldototal, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Master_msaldototal
  , lag(Master_msaldototal, 2) over (partition by numero_de_cliente order by ori.foto_mes) as Master_msaldototal_lag_2
  , ( Master_msaldototal - lag(Master_msaldototal, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Master_msaldototal_l2
  , lag(Master_mpagospesos, 1) over (partition by numero_de_cliente order by ori.foto_mes) as Master_mpagospesos_lag
  , ( Master_mpagospesos - lag(Master_mpagospesos, 1) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Master_mpagospesos
  , lag(Master_mpagospesos, 2) over (partition by numero_de_cliente order by ori.foto_mes) as Master_mpagospesos_lag_2
  , ( Master_mpagospesos - lag(Master_mpagospesos, 2) over (partition by numero_de_cliente order by ori.foto_mes)) as delta_Master_mpagospesos_l2
# [Anotación · líneas 158–163] Lag 1 y lag 2 de Master_status y de Visa_status, sin deltas.
#   flag_superior_payroll vale 1 cuando mpayroll supera el 95% del máximo de mpayroll del mes y 0 en otro caso.
#   mrentabilidad_relativa es mrentabilidad dividida por el promedio de mrentabilidad del mes, redondeada a 2
#   decimales.
  , lag(Master_status, 1) over (partition by numero_de_cliente order by ori.foto_mes) as Master_status_lag
  , lag(Master_status, 2) over (partition by numero_de_cliente order by ori.foto_mes) as Master_status_lag_2
  , lag(Visa_status, 1) over (partition by numero_de_cliente order by ori.foto_mes) as Visa_status_lag
  , lag(Visa_status, 2) over (partition by numero_de_cliente order by ori.foto_mes) as Visa_status_lag_2
  , case when ori.mpayroll > (paym.mpayroll_max * .95) then 1 else 0 end as flag_superior_payroll
  , round(( mrentabilidad / paym.mrentabilidad_prom),2)  as mrentabilidad_relativa
# [Anotación · líneas 164–174] Origen de la consulta: la tabla competencia_01 (alias ori) unida por foto_mes
#   con una subconsulta (alias paym) que calcula, para cada mes, el promedio y el máximo de mpayroll y el
#   promedio de mrentabilidad. Como la selección es 'select *', las columnas de la subconsulta también forman
#   parte del resultado.
    from competencia_01 ori
    inner join
    (
        select foto_mes
        , avg(mpayroll) as mpayroll_prom
        , max(mpayroll) as mpayroll_max
        , avg(mrentabilidad) as mrentabilidad_prom
        from competencia_01
        group by foto_mes
    ) paym
    on ori.foto_mes = paym.foto_mes

# [Anotación · líneas 176–177] Cierra el COPY: escribe el resultado en
#   '/content/drive/MyDrive/dmeyf/datasets/competencia_01_fe_Final.csv', en formato CSV con encabezado.
)
TO '/content/drive/MyDrive/dmeyf/datasets/competencia_01_fe_Final.csv' (FORMAT CSV, HEADER TRUE);
```


## Explicaciones del alumno (texto original)

### README.md

> # Predicción Bajas en Agosto
>
> El repositorio cuenta con 2 carpetas:
>
> - Predicción: contiene 2 scripts, "Optimizador_Hiperparametros.ipynb" y "Modelo_Final.ipynb".
>
> - Script_IngenieraData: contiene 1 solo script, "IngenieriaAtributos.ipynb"
>
>
> En primer lugar se debe ejecutar el script de "IngenieriaAtributos". Este toma el archivo inicial y genera 
> una variedad de atributos, como lags de orden 1 y 2, delta lags de orden 1 y 2, combina atributos y calcula 
> algunas relaciones entre los mismos. 
>
> Para realizar esta tarea se utiliza SQL.
>
> Este archivo se exporta como csv.
>
>
> En segundo lugar se puede ejecutar el script de "Modelo_Final", el cual genera el listado final de clientes, 
> creando un csv con el detalle de los numeros de clientes. 
>
> En este se utiliza lenguaje R.
>
>
> El script de "Optimizador_Hiperparametros", permite determinar los mejores hiperparametros tomando como entrenamiento
> los meses de 202103 y 202104, testeando en 202106.
>
> Este script se deberia ejecutar luego de "IngenieriaAtributos". El resultado del mismo se utiliza en el 
> script que genera el modelo final, el cual ya posee los mejores hiperparametros del modelo, con lo cual en este caso 
> puede saltearse este paso.
>
> Para este script se tomo como base el "Gustavo Pasquini", optimizando 3 hiperparametros:
> - num_iterations
> - num_leaves
> - min_sum_hessian_in_leaf
>
> No se uso undersampling.
>
> La métrica a optimizar es "auc".
>
> El script también devuelve la curva de envios para 202106 con las ganancias estimadas, que se uso para determinar
> el corte óptimo.
>
> Los mejores hiperparametros de este se utilizan en el Modelo Final, para reentrenar con los nuevos meses y predecir 202108.

