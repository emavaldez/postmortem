# Marcos Federico Rios — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: MarcosFedericoRios
- Repositorio: https://github.com/MarcosFedericoRios/primeracompetenciadmeyf
- Link posteado: https://github.com/MarcosFedericoRios/primeracompetenciadmeyf
- Commit: a29db2fa28312c1feca1d57552469354fa6ef259
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/marcosfedericorios/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/marcosfedericorios.json

## Resumen

La entrega tiene dos notebooks de R para Google Colab y un README con el orden de ejecución. Los dos notebooks descargan competencia_01_crudo.csv, calculan clase_ternaria y agregan, para cada variable, la diferencia con el valor de la fila anterior y con el de dos filas atrás del mismo cliente (d_<variable>_lag1 y d_<variable>_lag2). Competencia_1_3_20s_(RDATA).ipynb corre una optimización bayesiana con mlrMBO (20 iteraciones) de cinco hiperparámetros de LightGBM: clase binaria con BAJA+1 y BAJA+2 como positivo, meses 202103 a 202106, 20 % de los CONTINUA y AUC en validación cruzada de 5 folds; el estado queda en bayesiana.RDATA. Según el README, ese archivo se copia a la carpeta del experimento 4992 y Competencia_1_5_20s.ipynb lo retoma, toma los hiperparámetros de mayor AUC, entrena LightGBM sobre 202103 a 202106 sin submuestreo con 20 semillas, promedia las probabilidades para 202108 y escribe 11 archivos con los primeros 9500 a 12500 clientes.

**Qué entrega.** Competencia_1_5_20s.ipynb escribe 11 archivos /content/MI_ENTREGA_ZULIP_<corte>.csv, cada uno con una columna sin encabezado de numero_de_cliente: los primeros 9500, 10000, 10250, 10500, 10750, 11000, 11250, 11500, 11750, 12000 y 12500 clientes de 202108 ordenados por la probabilidad promedio de 20 semillas. El repositorio no incluye esos archivos ni indica cuál de ellos se envió.

**Cómo se ejecuta.** Según el README: (1) ejecutar Competencia_1_3_20s_(RDATA).ipynb, que genera un archivo .RDATA con los hiperparámetros de la optimización bayesiana en /content/buckets/b1/exp/HT4990; (2) crear la carpeta /content/buckets/b1/exp/HT4992 y pegar allí ese archivo; (3) ejecutar Competencia_1_5_20s.ipynb. Las celdas de texto de los notebooks indican usar el runtime Python 3 de Google Colab para montar Google Drive y el runtime R para el resto.

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria (clase01): 1 para BAJA+1 y BAJA+2, 0 para CONTINUA. La clase_ternaria se calcula en el notebook a partir de la presencia del cliente en los dos períodos siguientes.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** —
- **Mes que predice:** 202108
- **Submuestreo:** En la optimización bayesiana entran todas las filas BAJA+1 y BAJA+2 y las demás filas con un número al azar uniforme menor o igual a 0.2 (undersampling = 0.2, set.seed 137363); según la salida guardada quedan 137113 filas. El entrenamiento final usa todas las filas de 202103 a 202106, sin submuestreo, y reemplaza min_data_in_leaf por round(min_data_in_leaf / 0.2).
- **Calidad de datos:** No se observa tratamiento de variables ni imputaciones. Competencia_1_3_20s_(RDATA).ipynb tiene una celda que elimina de la tabla en memoria las filas de 202108 de los clientes que no están en 202107 (1402 clientes según la salida guardada); se ejecuta después de grabar competencia_01.csv.gz y antes de que el notebook borre los objetos y relea ese archivo. Competencia_1_5_20s.ipynb no tiene esa celda.
- **Drifting:** No se observa en el código
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** Para cada columna salvo numero_de_cliente, foto_mes y clase_ternaria: d_<columna>_lag1 (valor menos el de la fila anterior del mismo cliente, con la tabla ordenada por cliente y mes) y d_<columna>_lag2 (valor menos el de dos filas atrás), con NA cuando la fila anterior o la de dos atrás es de otro cliente. Según la salida guardada, el dataset queda con 459 columnas.
- **Selección de variables:** No se observa selección. Entran al modelo todas las columnas menos clase_ternaria, clase01, azar y training (458 según la salida guardada), incluidas numero_de_cliente y foto_mes. La importancia de variables de modelo_final se graba en impo.txt y no se vuelve a usar.
- **Optimización de hiperparámetros:** Optimización bayesiana con mlrMBO: modelo sustituto kriging (regr.km, covarianza matern3_2), criterio Expected Improvement, 20 iteraciones, estado guardado en bayesiana.RDATA cada 300 segundos. Espacio de búsqueda: num_iterations 200 a 600, learning_rate 0.02 a 0.10, feature_fraction 0.20 a 0.70, num_leaves 32 a 256, min_data_in_leaf 500 a 4000. La función objetivo es el AUC de lgb.cv con 5 folds estratificados. Según la salida guardada de Competencia_1_3_20s_(RDATA).ipynb, se evalúan 20 puntos de diseño inicial y 20 iteraciones.
- **Hiperparámetros finales:** param_fijos (boosting gbdt, objective binary, metric auc, max_depth -1, max_bin 31, lambda_l1 0, lambda_l2 0, min_gain_to_split 0, min_sum_hessian_in_leaf 0.001, bagging_fraction 1.0, extra_trees FALSE) más la fila de mayor AUC de la optimización. Según la salida guardada de la celda 59 de Competencia_1_5_20s.ipynb: num_iterations 590, learning_rate 0.04982431, feature_fraction 0.5267277, num_leaves 256, min_data_in_leaf 501, con AUC 0.9384878 en validación cruzada. Para el entrenamiento final min_data_in_leaf pasa a round(min_data_in_leaf / 0.2), que con 501 es 2505.
- **Semillas:** semilla_primigenia 137363 para el submuestreo, el seed de LightGBM durante la optimización y modelo_final. Para el promedio final, 20 semillas escritas en el código: 137363, 284309, 417563, 638417, 873457, 100003, 300007, 500041, 700089, 900103, 150001, 220009, 350003, 450007, 550021, 680003, 750019, 800011, 850009 y 890003. semilla_kaggle 314159 para la partición 3 a 7 de realidad_inicializar.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio de las probabilidades de 20 LightGBM entrenados con los mismos datos e hiperparámetros y distinto seed.
- **Corte:** Cantidades escritas en el código: 11 archivos con los primeros 9500, 10000, 10250, 10500, 10750, 11000, 11250, 11500, 11750, 12000 y 12500 clientes ordenados por probabilidad descendente. El repositorio no indica cuál se envió. PARAM$cortes (4000 a 19000 cada 500) se define y se muestra, y no se usa para generar archivos.
- **Validación:** Validación cruzada de 5 folds estratificados (lgb.cv) con métrica AUC sobre 202103 a 202106 submuestreado, dentro de la optimización bayesiana. No hay mes de validación separado. Se definen realidad_inicializar y realidad_evaluar para medir ganancia con una partición 3 a 7; realidad_evaluar no se llama. La ganancia acumulada (1072500 por BAJA+2, -27500 por el resto) se calcula sobre las filas de 202108, que según la salida guardada de la celda 20 tienen clase_ternaria NA.
- **Salidas:** /content/datasets/competencia_01.csv.gz (dataset con clase y deltas). En /content/buckets/b1/exp/HT4990 (primer notebook) y HT4992 (segundo): bayesiana.RDATA, BO_log.txt y PARAM.yml. En /content/buckets/b1/exp/exp4992: impo.txt, modelo.txt, prediccion.txt (numero_de_cliente, foto_mes, prob) y PARAM.yml. En /content: 11 archivos MI_ENTREGA_ZULIP_<corte>.csv.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Validación cruzada (`validacion.validacion_cruzada`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: Google Colab con Google Drive montado en /content/.drive y la carpeta 'My Drive/dmeyf' enlazada como /content/buckets/b1. Las celdas de texto indican runtime Python 3 para el montaje y runtime R para el resto; los metadatos de los dos notebooks declaran kernel R (ir). Los paquetes de R se instalan con install.packages si faltan; no se declaran versiones de R ni de paquetes.

## Pasos del camino de la entrega

1. **Preparación del entorno en Google Colab.** Una celda de Python monta Google Drive en /content/.drive. Una celda de shell crea 'My Drive/dmeyf', la enlaza como /content/buckets/b1, crea las carpetas exp y datasets, descarga competencia_01_crudo.csv desde storage.googleapis.com/open-courses/dmeyf2026-9c6f si no está en el bucket y lo copia a /content/datasets. Las mismas celdas están en los dos notebooks. (`Competencia_1_3_20s_(RDATA).ipynb` líneas 61–99; `Competencia_1_5_20s.ipynb` líneas 61–99)
2. **Cálculo de clase_ternaria.** Convierte foto_mes en un índice de período (año × 12 + mes), ordena por cliente y período y obtiene con shift los dos períodos siguientes de cada cliente. Asigna CONTINUA a los períodos anteriores al anteúltimo y luego reemplaza por BAJA+1 donde el cliente no está en el período siguiente y por BAJA+2 donde está en el siguiente y no en el subsiguiente. Según la salida guardada de la celda 20, 202103 a 202106 quedan con las tres clases, 202107 con BAJA+1 o NA y 202108 con NA. (`Competencia_1_3_20s_(RDATA).ipynb` líneas 104–135; `Competencia_1_5_20s.ipynb` líneas 104–135)
3. **Deltas contra las dos filas anteriores.** Con la tabla ordenada por cliente y mes, para cada columna salvo numero_de_cliente, foto_mes y clase_ternaria crea d_<columna>_lag1 (valor menos el de la fila anterior) y d_<columna>_lag2 (valor menos el de dos filas atrás). Pone NA en lag1 cuando la fila anterior es de otro cliente y en lag2 cuando la fila anterior o la de dos atrás es de otro cliente. Graba el resultado en /content/datasets/competencia_01.csv.gz; según la salida guardada, con 459 columnas. (`Competencia_1_3_20s_(RDATA).ipynb` líneas 137–169; `Competencia_1_5_20s.ipynb` líneas 137–167)
4. **Filtro de clientes nuevos de agosto (sólo en el primer notebook).** Competencia_1_3_20s_(RDATA).ipynb identifica los clientes presentes en 202108 que no están en 202107 y, con BORRAR_NUEVOS_AGOSTO = TRUE, elimina sus filas de 202108 de la tabla en memoria (1402 clientes según la salida guardada). La celda se ejecuta después de grabar competencia_01.csv.gz; más adelante el notebook borra todos los objetos y vuelve a leer ese archivo. Competencia_1_5_20s.ipynb no tiene esta celda. (`Competencia_1_3_20s_(RDATA).ipynb` líneas 181–203; `Competencia_1_3_20s_(RDATA).ipynb` líneas 220–223; `Competencia_1_3_20s_(RDATA).ipynb` líneas 418–420)
5. **Parámetros de la corrida.** PARAM fija experimento 4990 en el primer notebook y 4992 en el segundo. En ambos: semilla_primigenia 137363, train y train_final con 202103, 202104, 202105 y 202106, future 202108, semilla_kaggle 314159, cortes de 4000 a 19000 cada 500 y undersampling 0.2. (`Competencia_1_3_20s_(RDATA).ipynb` líneas 267–284; `Competencia_1_5_20s.ipynb` líneas 241–259)
6. **Hiperparámetros fijos y espacio de búsqueda.** param_fijos define boosting gbdt, objective binary, metric auc, max_depth -1, max_bin 31, lambda_l1 y lambda_l2 en 0, bagging_fraction 1.0, extra_trees FALSE y valores de resguardo para los cinco hiperparámetros que se buscan. El espacio de búsqueda es num_iterations entre 200 y 600, learning_rate entre 0.02 y 0.10, feature_fraction entre 0.20 y 0.70, num_leaves entre 32 y 256 y min_data_in_leaf entre 500 y 4000, con 20 iteraciones bayesianas y 5 folds. (`Competencia_1_3_20s_(RDATA).ipynb` líneas 286–353; `Competencia_1_5_20s.ipynb` líneas 261–328)
7. **Datos de entrenamiento de la búsqueda de hiperparámetros.** Lee competencia_01.csv.gz, se queda con 202103 a 202106, crea clase01 (1 para BAJA+1 y BAJA+2, 0 para el resto) y marca training = 1 en todas las filas BAJA+1 y BAJA+2 y en las demás filas con un número al azar uniforme menor o igual a 0.2 (set.seed 137363). campos_buenos toma todas las columnas menos clase_ternaria, clase01, azar y training. Según la salida guardada, el lgb.Dataset tiene 137113 filas y 458 columnas. (`Competencia_1_3_20s_(RDATA).ipynb` líneas 410–468)
8. **Función objetivo: AUC en validación cruzada.** EstimarGanancia_AUC_lightgbm superpone los hiperparámetros propuestos a param_fijos, corre lgb.cv con 5 folds estratificados y devuelve modelocv$best_score, que el código llama AUC. (`Competencia_1_3_20s_(RDATA).ipynb` líneas 473–500)
9. **Optimización bayesiana con mlrMBO.** Define la función objetivo a maximizar (noisy), un control que guarda el estado en bayesiana.RDATA cada 300 segundos y termina a las 20 iteraciones, el criterio Expected Improvement y un modelo kriging (regr.km, covarianza matern3_2). Corre mbo, ordena el historial por AUC descendente, lo graba en BO_log.txt, guarda la primera fila en PARAM$out$lgbm$mejores_hiperparametros y escribe PARAM.yml. Según la salida guardada: 20 puntos de diseño inicial y 20 iteraciones; primera fila con num_iterations 590, learning_rate 0.04982431, feature_fraction 0.5267277, num_leaves 256, min_data_in_leaf 501 y AUC 0.9384878. (`Competencia_1_3_20s_(RDATA).ipynb` líneas 502–600)
10. **Traslado de bayesiana.RDATA y reanudación en el segundo notebook.** El README indica copiar el .RDATA de la carpeta HT4990 a HT4992. Competencia_1_5_20s.ipynb trabaja en /content/buckets/b1/exp/HT4992, repite el armado de datos y la configuración y, como bayesiana.RDATA existe, llama a mboContinue en lugar de mbo. Según la salida guardada, mboContinue avisa que la búsqueda ya terminó y devuelve el resultado almacenado. Luego repite el ordenamiento por AUC, BO_log.txt y PARAM.yml. (`README.md` líneas 3–5; `Competencia_1_5_20s.ipynb` líneas 385–443; `Competencia_1_5_20s.ipynb` líneas 525–575)
11. **Datos e hiperparámetros del entrenamiento final.** Cambia a la carpeta exp4992, crea clase01 en todo el dataset y arma dtrain_final con todas las filas de 202103 a 202106, sin submuestreo (645999 CONTINUA, 4067 BAJA+2 y 4000 BAJA+1 según la salida guardada). param_final une param_fijos con la fila de mayor AUC; param_normalizado reemplaza min_data_in_leaf por round(min_data_in_leaf / 0.2). (`Competencia_1_5_20s.ipynb` líneas 584–629)
12. **Modelo con la semilla primigenia, importancia y modelo guardado.** Entrena modelo_final con lgb.train y param_normalizado (seed 137363), graba la importancia de variables en impo.txt y el modelo en modelo.txt. La celda que aplica este modelo a 202108 tiene todas sus líneas comentadas. (`Competencia_1_5_20s.ipynb` líneas 631–668)
13. **Semillerio de 20 semillas y predicción de 202108.** Para cada una de las 20 semillas escritas en el código copia param_normalizado, cambia seed, entrena un LightGBM sobre dtrain_final y suma su predicción sobre las filas de 202108. La probabilidad final es la suma dividida por 20. Graba numero_de_cliente, foto_mes y prob en prediccion.txt. (`Competencia_1_5_20s.ipynb` líneas 670–734)
14. **Curva de ganancia acumulada y revisiones.** Ordena por probabilidad descendente, calcula gan (1072500 si clase_ternaria es BAJA+2, -27500 en otro caso), su suma acumulada y la posición, y grafica las primeras 30000 posiciones con ggplot2. Según la salida guardada de la celda 81, las primeras seis filas tienen clase_ternaria vacía y gan -27500; el gráfico guardado es una recta descendente desde 0. Después llama a realidad_inicializar, muestra PARAM$cortes, graba PARAM.yml, muestra un resumen de prob y cuenta las filas por mes según tengan clase. (`Competencia_1_5_20s.ipynb` líneas 736–790)
15. **Archivos de entrega con 11 cortes.** Con la tabla ordenada por probabilidad descendente, para cada corte en 9500, 10000, 10250, 10500, 10750, 11000, 11250, 11500, 11750, 12000 y 12500 graba /content/MI_ENTREGA_ZULIP_<corte>.csv con los primeros numero_de_cliente como entero, sin encabezado. (`Competencia_1_5_20s.ipynb` líneas 792–811)

## Archivos

- `Competencia_1_5_20s.ipynb` · principal · Jupyter (R) · 811 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/marcosfedericorios/Competencia_1_5_20s.ipynb.txt) — Notebook de R para Google Colab (experimento 4992): repite la preparación de datos, retoma bayesiana.RDATA, entrena LightGBM sobre 202103 a 202106 con 20 semillas, promedia las probabilidades de 202108 y escribe 11 archivos MI_ENTREGA_ZULIP_<corte>.csv.
- `Competencia_1_3_20s_(RDATA).ipynb` · principal · Jupyter (R) · 600 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/marcosfedericorios/Competencia_1_3_20s_%28RDATA%29.ipynb.txt) — Notebook de R para Google Colab (experimento 4990): descarga el dataset, calcula clase_ternaria y los deltas contra las dos filas anteriores, y corre la optimización bayesiana de cinco hiperparámetros de LightGBM con AUC en validación cruzada de 5 folds. Deja bayesiana.RDATA, BO_log.txt y PARAM.yml en /content/buckets/b1/exp/HT4990.
- `README.md` · explicacion · Markdown · 5 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/marcosfedericorios/README.md.txt) — Instrucciones de ejecución en tres pasos: correr Competencia_1_3_20s_(RDATA).ipynb, crear la carpeta HT4992 y pegar allí el .RDATA generado en HT4990, y correr Competencia_1_5_20s.ipynb.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### Competencia_1_5_20s.ipynb

Notebook de R para Google Colab (experimento 4992): repite la preparación de datos, retoma bayesiana.RDATA, entrena LightGBM sobre 202103 a 202106 con 20 semillas, promedia las probabilidades de 202108 y escribe 11 archivos MI_ENTREGA_ZULIP_<corte>.csv.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–59] Celdas de texto 1 a 12: título, objetivos de una tarea sobre hiperparámetros de
#   LightGBM y optimización bayesiana, enlaces a la documentación de LightGBM y a tres artículos, e indicación
#   de usar el runtime Python 3 de Google Colab y conectar Google Drive.
#%% celda 1 [texto]
# 1° COMPETENCIA DM EyF

#%% celda 2 [texto]
##  1. Big Picture

#%% celda 3 [texto]
LightGBM es el algoritmo estado del arte para datasets estructurados.
<br> La Bayesian Optimization es el estado del arte para optimización de hiperparámetros
<br> Las soluciones a las tres competencias de la asignatura contendrán LightGBMs y Bayesian Optimizations
<br> LightGBM ha aumentado en forma no darwiniana sus hiperparámetros en los últimos ocho años; no todos los existentes son útiles.
<br> Es necesario lograr entender cuales son los hiperparámetros relevantes de LightGBM

#%% celda 4 [texto]
## 2. Hiperparámetros del LightGBM

#%% celda 5 [texto]
Los objetivos de esta tarea son:


*   Aumentar la rentabilidad de la campaña de marketing de retención proactiva de clientes.
*   Generar un mejor modelo optimizando sus hiperparámetros
*   Conceptual : investigar los mas relevantes hiperparámetros de LightGBM
*   Familiarizarse con la Bayesian Optimization, sus largos tiempos de corrida y opciones para reducirlos
*   Familiarizarse con el uso de máquinas virtuales de Google Colab
*   Ver un pipeline completo de optimización de hiperparámetros y puesta en producción

#%% celda 6 [texto]
LightGBM cuenta con mas de 60 hiperparámetros, siendo posible utilizar 40 al mismo tiempo, aunque no razonable.
<br> La documentación oficial de los hiperparámetros de LightGBM es  https://lightgbm.readthedocs.io/en/latest/Parameters.html#core-parameters

#%% celda 7 [texto]
Se lo alerta sobre que una Optimizacion Bayesiana lleva varias horas de corrida, y usted deberá correr VARIAS optimizaciones para descubrir cuales parámetros conviene optimizar.
<br> A pesar que la próxima clase es recien en viernes 01 de agosto, inicie la tarea con tiempo, aprenda a planificar estratégicamente sus corridas como un@ científ@  de datos.

#%% celda 8 [texto]
Es necesario investigar cuales son los hiperparámetros de LightGBM que vale la pena optimizar en una Bayesian Optimization, ya que los realmente utiles son apenas un reducido subconjunto.
<br>Usted deberá investigar cuales son los hiperparámetros mas relevantes de LightGBM, su primer alternativa es preguntándole a su amigo con capacidades especiales ChatGPT o sus endogámicos familiares Claude, DeepSeek, Gemini, Grok, etc
<br> La segunda alternativa es la propia documentación de LightGBM  https://lightgbm.readthedocs.io/en/latest/Parameters-Tuning.html

#%% celda 9 [texto]
Adicionalmente podra buscar información como la que proveen esta diminuta muestra aleatoria de artículos ligeros:
*  https://medium.com/@sarahzouinina/a-deep-dive-into-lightgbm-how-to-choose-and-tune-parameters-7c584945842e
*  https://www.kaggle.com/code/somang1418/tuning-hyperparameters-under-10-minutes-lgbm
*  https://towardsdatascience.com/beginners-guide-to-the-must-know-lightgbm-hyperparameters-a0005a812702/


<br>  La muestra anterior se brinda a modo de ejemplo, usted deberá buscar muuuuchas  fuentes adicionales de información
<br> Tenga presente que LightGBM es el estado del arte en modelado predictivo para datasets estructurado, que son el 90% del trabajo del 95% de los Data Scientists en Argentina.

#%% celda 10 [texto]
#### 2.1  Seteo del ambiente en Google Colab

#%% celda 11 [texto]
Esta parte se debe correr con el runtime en Python3
<br>Ir al menu, Runtime -> Change Runtime Type -> Runtime type ->  **Python 3**

#%% celda 12 [texto]
Conectar la virtual machine donde esta corriendo Google Colab con el  Google Drive, para poder tener persistencia de archivos

# [Anotación · líneas 61–99] Monta Google Drive en /content/.drive (celda de Python). En una celda de shell
#   crea 'My Drive/dmeyf', la enlaza como /content/buckets/b1 y crea las carpetas exp, datasets y
#   /content/datasets; si competencia_01_crudo.csv no está en el bucket lo descarga con wget desde
#   storage.googleapis.com/open-courses/dmeyf2026-9c6f, y lo copia al disco local si falta.
#%% celda 13 [código]
# primero establecer el Runtime de Python 3
from google.colab import drive
drive.mount('/content/.drive')

#%% celda 14 [texto]
Para correr la siguiente celda es fundamental en Arranque en Frio haber copiado el archivo kaggle.json al Google Drive, en la carpeta indicada en el instructivo

<br>los siguientes comando estan en shell script de Linux
*   Crear las carpetas en el Google Drive
*   "instalar" el archivo kaggle.json desde el Google Drive a la virtual machine para que pueda ser utilizado por la libreria  kaggle de Python
*   Bajar el  **dataset_pequeno**  al  Google Drive  y tambien al disco local de la virtual machine que esta corriendo Google Colab

#%% celda 15 [código]
%%shell

mkdir -p "/content/.drive/My Drive/dmeyf"
mkdir -p "/content/buckets"
ln -s "/content/.drive/My Drive/dmeyf" /content/buckets/b1


mkdir -p /content/buckets/b1/exp
mkdir -p /content/buckets/b1/datasets
mkdir -p /content/datasets



archivo_origen="https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
archivo_destino="/content/datasets/competencia_01_crudo.csv"
archivo_destino_bucket="/content/buckets/b1/datasets/competencia_01_crudo.csv"

if ! test -f $archivo_destino_bucket; then
  wget  $archivo_origen  -O $archivo_destino_bucket
fi


if ! test -f $archivo_destino; then
  cp  $archivo_destino_bucket  $archivo_destino
fi

# [Anotación · líneas 101–135] Lee competencia_01_crudo.csv con fread y calcula clase_ternaria: arma una tabla
#   auxiliar con la posición original, el cliente y el período como año × 12 + mes, y con shift de tipo lead
#   obtiene los dos períodos siguientes de cada cliente. Asigna CONTINUA a los períodos anteriores al
#   anteúltimo, luego BAJA+1 donde falta el período siguiente (en períodos anteriores al último) y BAJA+2 donde
#   está el siguiente y falta el subsiguiente. Vuelve al orden original y copia la clase al dataset.
#%% celda 16 [texto]
DELTA LAGS 1 y 2

#%% celda 17 [código]
require("data.table")

dataset <- fread("/content/datasets/competencia_01_crudo.csv")

# Calcular la clase_ternaria
dsimple <- dataset[, list(
    "pos" = .I,
    numero_de_cliente,
    periodo0 = as.integer(foto_mes/100)*12 + foto_mes%%100 ) ]

setorder(dsimple, numero_de_cliente, periodo0)

periodo_ultimo <- dsimple[, max(periodo0)]
periodo_anteultimo <- periodo_ultimo - 1

dsimple[, c("periodo1", "periodo2") :=
    shift(periodo0, n=1:2, fill=NA, type="lead"), numero_de_cliente]

dsimple[periodo0 < periodo_anteultimo, clase_ternaria := "CONTINUA"]

dsimple[periodo0 < periodo_ultimo &
    (is.na(periodo1) | periodo0 + 1 < periodo1),
    clase_ternaria := "BAJA+1"]

dsimple[periodo0 < periodo_anteultimo & (periodo0+1 == periodo1)
    & (is.na(periodo2) | periodo0 + 2 < periodo2),
    clase_ternaria := "BAJA+2"]

setorder(dsimple, pos)
dataset[, clase_ternaria := dsimple$clase_ternaria]
rm(dsimple)

# [Anotación · líneas 137–167] Ordena por cliente y mes. Para cada columna que no es numero_de_cliente,
#   foto_mes ni clase_ternaria crea d_<columna>_lag1 = valor menos el de la fila anterior y d_<columna>_lag2 =
#   valor menos el de dos filas atrás. Marca las filas cuya fila anterior, o la de dos atrás, pertenece a otro
#   cliente y en ellas pone NA: en lag1 con la primera marca, en lag2 con cualquiera de las dos. Graba la tabla
#   en /content/datasets/competencia_01.csv.gz e imprime la cantidad de columnas.
# DELTA LAG1 Y DELTA LAG2
setorder(dataset, numero_de_cliente, foto_mes)

cols_id <- c("numero_de_cliente", "foto_mes", "clase_ternaria")
cols_features <- setdiff(colnames(dataset), cols_id)

cols_deltas_lag1 <- paste0("d_", cols_features, "_lag1")
cols_deltas_lag2 <- paste0("d_", cols_features, "_lag2")

dataset[, (cols_deltas_lag1) := .SD - shift(.SD, n = 1, type = "lag"),
        .SDcols = cols_features]

es_nuevo_cliente_1 <- dataset$numero_de_cliente != shift(dataset$numero_de_cliente, n = 1, type = "lag")
es_nuevo_cliente_1[1] <- TRUE
dataset[es_nuevo_cliente_1, (cols_deltas_lag1) := NA]


dataset[, (cols_deltas_lag2) := .SD - shift(.SD, n = 2, type = "lag"),
        .SDcols = cols_features]

es_nuevo_cliente_2 <- dataset$numero_de_cliente != shift(dataset$numero_de_cliente, n = 2, type = "lag")
es_nuevo_cliente_2[1:2] <- TRUE
dataset[es_nuevo_cliente_1 | es_nuevo_cliente_2, (cols_deltas_lag2) := NA]

# Limpiar variables auxiliares
rm(es_nuevo_cliente_1, es_nuevo_cliente_2)

# Guardar
fwrite(dataset, file = "/content/datasets/competencia_01.csv.gz", sep = ",")

cat("Proceso completado. Total de columnas guardadas:", ncol(dataset), "\n")

# [Anotación · líneas 169–177] Ordena el dataset por foto_mes, clase_ternaria y numero_de_cliente y cuenta las
#   filas por mes y clase. Las celdas de texto indican que esta parte se corre con el runtime R.
#%% celda 18 [texto]
## Generacion de la clase_ternaria

#%% celda 19 [texto]
Esta parte se debe correr con el runtime en lenguaje **R** Ir al menu, Runtime -> Change Runtime Tipe -> Runtime type -> R

#%% celda 20 [código]
setorder( dataset, foto_mes, clase_ternaria, numero_de_cliente)
dataset[, .N, list(foto_mes, clase_ternaria)]

# [Anotación · líneas 179–232] Imprime fecha y hora, borra todos los objetos del ambiente y libera memoria.
#   Carga data.table y parallel, e instala si faltan y carga R.utils, primes, utils, rlist, yaml, lightgbm,
#   DiceKriging y mlrMBO.
#%% celda 21 [texto]
### 2.2 Optimizacion Hiperparámetros

#%% celda 22 [texto]
Esta parte se debe correr con el runtime en lenguaje R Ir al menu, Runtime -> Change Runtime Type -> Runtime type -> R

#%% celda 23 [texto]
### 2.2.1 Inicio

#%% celda 24 [texto]
limpio el ambiente de R

#%% celda 25 [código]
format(Sys.time(), "%a %b %d %X %Y")

#%% celda 26 [código]
# limpio la memoria
rm(list=ls(all.names=TRUE)) # remove all objects
gc(full=TRUE, verbose=FALSE) # garbage collection

#%% celda 27 [texto]
### 2.2.2 Carga de Librerias

#%% celda 28 [texto]
Esta parte lleva varios minutos la primera vez en Google Colab

#%% celda 29 [código]
# cargo las librerias que necesito
require("data.table")
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

# [Anotación · líneas 234–259] Crea la lista PARAM: experimento 4992, semilla_primigenia 137363, train y
#   train_final con 202103, 202104, 202105 y 202106, future 202108, semilla_kaggle 314159, cortes de 4000 a
#   19000 cada 500 y undersampling 0.2 (proporción de CONTINUA que se conserva).
#%% celda 30 [texto]
### 2.2.3 Definicion de Parametros

#%% celda 31 [texto]
aqui debe cargar SU semilla primigenia
<br>recuerde cambiar el numero de experimento en cada corrida nueva

#%% celda 32 [código]
###CAMBIAR NRO DE EXPERIMENTO###
PARAM <- list()
PARAM$experimento <- 4992
PARAM$semilla_primigenia <- 137363

#%% celda 33 [código]
# training y future
PARAM$train <- c(202103, 202104, 202105, 202106)
PARAM$train_final <- c(202103, 202104, 202105, 202106)
PARAM$future <- c(202108)
PARAM$semilla_kaggle <- 314159
PARAM$cortes <- seq(4000, 19000, by= 500)

#%% celda 34 [código]
# un undersampling de 0.1  toma solo el 10% de los CONTINUA
# undersampling de 1.0  implica tomar TODOS los datos

PARAM$trainingstrategy$undersampling <- 0.2

# [Anotación · líneas 261–304] Fija 5 folds para la validación cruzada y la lista param_fijos de LightGBM:
#   boosting gbdt, objective binary, metric auc, seed = semilla_primigenia, max_depth -1, min_gain_to_split 0,
#   min_sum_hessian_in_leaf 0.001, lambda_l1 y lambda_l2 0, max_bin 31, fracciones de bagging 1.0, is_unbalance
#   FALSE, scale_pos_weight 1.0, drop_rate 0.1, max_drop 50, skip_drop 0.5, extra_trees FALSE y valores de
#   resguardo num_iterations 600, learning_rate 0.03, feature_fraction 0.50, num_leaves 256 y min_data_in_leaf
#   1000.
#%% celda 35 [código]
# Parametros LightGBM

PARAM$hyperparametertuning$xval_folds <- 5

# parametros fijos del LightGBM que se pisaran con la parte variable de la BO
PARAM$lgbm$param_fijos <- list(
  boosting = "gbdt",
  objective = "binary",
  metric = "auc",
  first_metric_only = FALSE,
  boost_from_average = TRUE,
  feature_pre_filter = FALSE,
  force_row_wise = TRUE,
  verbosity = -100,

  seed = PARAM$semilla_primigenia,

  max_depth = -1L, # -1 significa no limitar
  min_gain_to_split = 0,
  min_sum_hessian_in_leaf = 0.001,
  lambda_l1 = 0.0,
  lambda_l2 = 0.0,
  max_bin = 31L, # Fijo, no participa de la BO

  bagging_fraction = 1.0,
  pos_bagging_fraction = 1.0,
  neg_bagging_fraction = 1.0,
  is_unbalance = FALSE,
  scale_pos_weight = 1.0,

  drop_rate = 0.1,
  max_drop = 50,
  skip_drop = 0.5,

  extra_trees = FALSE, # Cambiar a TRUE si deseas probar la variante Extra Trees

  # Valores por defecto de resguardo (se sobreescriben en cada iteración de la BO)
  num_iterations = 600,
  learning_rate = 0.03,
  feature_fraction = 0.50,
  num_leaves = 256,
  min_data_in_leaf = 1000
)

# [Anotación · líneas 306–328] Define el espacio de búsqueda con makeParamSet: num_iterations entero entre 200
#   y 600, learning_rate entre 0.02 y 0.10, feature_fraction entre 0.20 y 0.70, num_leaves entero entre 32 y 256
#   y min_data_in_leaf entero entre 500 y 4000. Fija 20 iteraciones bayesianas.
#%% celda 36 [texto]
Aqui se definen los hiperparámetros de LightGBM que participan de la Bayesian Optimization
<br> si es un numero entero debe ir  makeIntegerParam
<br> si es un numero real (con decimales) debe ir  makeNumericParam
<br> es muy importante leer cuales son un lower y upper  permitidos y ademas razonables

#%% celda 37 [código]
#Límites acotados de los árboles
PARAM$hypeparametertuning$hs <- makeParamSet(
  makeIntegerParam("num_iterations", lower = 200L, upper = 600L),
  makeNumericParam("learning_rate", lower = 0.02, upper = 0.10),
  makeNumericParam("feature_fraction", lower = 0.20, upper = 0.70),
  makeIntegerParam("num_leaves", lower = 32L, upper = 256L),
  makeIntegerParam("min_data_in_leaf", lower = 500L, upper = 4000L)
)

#%% celda 38 [texto]
A mayor cantidad de hiperparámetros, se debe aumentar las iteraciones de la Bayesian Optimization
<br> 30 es un valor muy tacaño, pero corre rápido
<br> deberia partir de 50, alcanzando los 100 si se dispone de tiempo

#%% celda 39 [código]
PARAM$hyperparametertuning$iteraciones <- 20 # iteraciones bayesianas

# [Anotación · líneas 330–380] Define tres funciones. particionar agrega una columna fold con una partición al
#   azar en las proporciones pedidas, estratificada por el campo indicado y con semilla opcional.
#   realidad_inicializar toma cliente, mes y clase de una tabla y la parte en proporción 3 a 7 por
#   clase_ternaria con semilla_kaggle. realidad_evaluar une una predicción y calcula la ganancia (1072500 por
#   cada BAJA+2 enviado, -27500 por el resto) en el fold 1 dividida por 0.3, en el fold 2 dividida por 0.7 y
#   total. En este notebook realidad_evaluar no se llama.
#%% celda 40 [código]
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

#%% celda 41 [código]
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

#%% celda 42 [código]
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

# [Anotación · líneas 382–407] Crea y fija como carpeta de trabajo /content/buckets/b1/exp/HT4992. Lee
#   competencia_01.csv.gz, se queda con las filas de los meses de PARAM$train y crea clase01: 1 para BAJA+1 y
#   BAJA+2, 0 para el resto.
#%% celda 43 [texto]
### 2.2.4  Preprocesamiento

#%% celda 44 [código]
# carpeta de trabajo

setwd("/content/buckets/b1/exp")
experimento_folder <- paste0("HT", PARAM$experimento)
dir.create(experimento_folder, showWarnings=FALSE)
setwd( paste0("/content/buckets/b1/exp/", experimento_folder ))

#%% celda 45 [código]
# lectura del dataset
dataset <- fread("/content/datasets/competencia_01.csv.gz", stringsAsFactors= TRUE)

#%% celda 46 [código]
dataset_train <- dataset[foto_mes %in% PARAM$train]

#%% celda 47 [código]
# paso la clase a binaria que tome valores {0,1}  enteros
#  BAJA+1 y BAJA+2  son  1,   CONTINUA es 0
#  a partir de ahora ya NO puedo cortar  por prob(BAJA+2) > 1/40

dataset_train[,
  clase01 := ifelse(clase_ternaria %in% c("BAJA+2","BAJA+1"), 1L, 0L)
]

# [Anotación · líneas 409–443] Con set.seed(137363) genera un número uniforme por fila (azar) y marca training
#   = 1 en las filas BAJA+1 y BAJA+2 y en las demás filas con azar menor o igual a 0.2. campos_buenos son todas
#   las columnas menos clase_ternaria, clase01, azar y training; numero_de_cliente y foto_mes quedan incluidas.
#   Arma el lgb.Dataset dtrain con las filas training = 1 y muestra su cantidad de filas y columnas.
#%% celda 48 [código]
# defino los datos que forma parte del training
# aqui se hace el undersampling de los CONTINUA
# notar que para esto utilizo la SEGUNDA semilla

set.seed(PARAM$semilla_primigenia, kind = "L'Ecuyer-CMRG")
dataset_train[, azar := runif(nrow(dataset_train))]
dataset_train[, training := 0L]

dataset_train[
  foto_mes %in%  PARAM$train &
    (azar <= PARAM$trainingstrategy$undersampling | clase_ternaria %in% c("BAJA+1", "BAJA+2")),
  training := 1L
]

#%% celda 49 [código]
###¿El ID de los clientes?
# los campos que se van a utilizar

campos_buenos <- setdiff(
  colnames(dataset_train),
  c("clase_ternaria", "clase01", "azar", "training")
)

#%% celda 50 [código]
# dejo los datos en el formato que necesita LightGBM

dtrain <- lgb.Dataset(
  data= data.matrix(dataset_train[training == 1L, campos_buenos, with= FALSE]),
  label= dataset_train[training == 1L, clase01],
  free_raw_data= FALSE
)

nrow(dtrain)
ncol(dtrain)

# [Anotación · líneas 445–475] EstimarGanancia_AUC_lightgbm recibe los hiperparámetros propuestos, los
#   superpone a param_fijos, corre lgb.cv sobre dtrain con 5 folds estratificados y devuelve modelocv$best_score
#   como AUC. Libera memoria e imprime la hora y el valor.
#%% celda 51 [texto]
2.2.5 Configuracion Bayesian Optimization

#%% celda 52 [código]
# En el argumento x llegan los parmaetros de la bayesiana
#  devuelve la AUC en cross validation del modelo entrenado

EstimarGanancia_AUC_lightgbm <- function(x) {

  # x pisa (o agrega) a param_fijos
  param_completo <- modifyList(PARAM$lgbm$param_fijos, x)

  # entreno LightGBM
  modelocv <- lgb.cv(
    data= dtrain,
    nfold= PARAM$hyperparametertuning$xval_folds,
    stratified= TRUE,
    param= param_completo
  )

  # obtengo la ganancia
  AUC <- modelocv$best_score

  # hago espacio en la memoria
  rm(modelocv)
  gc(full= TRUE, verbose= FALSE)

  message(format(Sys.time(), "%a %b %d %X %Y"), " AUC ", AUC)

  return(AUC)
}

# [Anotación · líneas 477–520] Configura mlrMBO: archivo de estado bayesiana.RDATA; función de un solo
#   objetivo a maximizar, marcada como ruidosa (noisy), sobre el espacio de búsqueda; guardado en disco cada 300
#   segundos; término a las 20 iteraciones; criterio de infill Expected Improvement; modelo sustituto regr.km
#   (kriging) con covarianza matern3_2 y predicción con error estándar.
#%% celda 53 [código]
# Aqui comienza la configuracion de la Bayesian Optimization

# en este archivo quedan la evolucion binaria de la BO
kbayesiana <- "bayesiana.RDATA"

funcion_optimizar <- EstimarGanancia_AUC_lightgbm # la funcion que voy a maximizar

configureMlr(show.learner.output= FALSE)

# configuro la busqueda bayesiana,  los hiperparametros que se van a optimizar
# por favor, no desesperarse por lo complejo

obj.fun <- makeSingleObjectiveFunction(
  fn= funcion_optimizar, # la funcion que voy a maximizar
  minimize= FALSE, # estoy Maximizando la ganancia
  noisy= TRUE,
  par.set= PARAM$hypeparametertuning$hs, # definido al comienzo del programa
  has.simple.signature= FALSE # paso los parametros en una lista
)

# cada 300 segundos guardo el resultado intermedio
ctrl <- makeMBOControl(
  save.on.disk.at.time= 300, # se graba cada 300 segundos
  save.file.path= kbayesiana
) # se graba cada 300 segundos

# indico la cantidad de iteraciones que va a tener la Bayesian Optimization
ctrl <- setMBOControlTermination(
  ctrl,
  iters= PARAM$hyperparametertuning$iteraciones
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

# [Anotación · líneas 522–575] Si bayesiana.RDATA no existe en la carpeta HT4992 corre mbo; si existe, llama a
#   mboContinue con ese archivo. Convierte el historial (opt.path) en tabla, numera las filas, las ordena por y
#   (AUC) descendente y graba BO_log.txt. Guarda en PARAM$out$lgbm$mejores_hiperparametros las columnas de
#   hiperparámetros de la primera fila y en PARAM$out$lgbm$y su AUC; escribe PARAM.yml e imprime ambos.
#%% celda 54 [texto]
2.2.6 Corrida Bayesian Optimization

#%% celda 55 [código]

# inicio la optimizacion bayesiana, retomando si ya existe
# es la celda mas lenta de todo el notebook

if (!file.exists(kbayesiana)) {
  bayesiana_salida <- mbo(obj.fun, learner= surr.km, control= ctrl)
} else {
  bayesiana_salida <- mboContinue(kbayesiana) # retomo en caso que ya exista
}

#%% celda 56 [código]

tb_bayesiana <- as.data.table(bayesiana_salida$opt.path)
colnames( tb_bayesiana)

#%% celda 57 [código]
# almaceno los resultados de la Bayesian Optimization
# y capturo los mejores hiperparametros encontrados

tb_bayesiana <- as.data.table(bayesiana_salida$opt.path)

tb_bayesiana[, iter := .I]

# ordeno en forma descendente por AUC = y
setorder(tb_bayesiana, -y)

# grabo para eventualmente poder utilizarlos en OTRA corrida
fwrite( tb_bayesiana,
  file= "BO_log.txt",
  sep= "\t"
)

# los mejores hiperparámetros son los que quedaron en el registro 1 de la tabla
PARAM$out$lgbm$mejores_hiperparametros <- tb_bayesiana[
  1, # el primero es el de mejor AUC
  setdiff(colnames(tb_bayesiana),
    c("y","dob","eol","error.message","exec.time","ei","error.model",
      "train.time","prop.type","propose.time","se","mean","iter")),
  with= FALSE
]


PARAM$out$lgbm$y <- tb_bayesiana[1, y]

#%% celda 58 [código]
write_yaml( PARAM, file="PARAM.yml")

#%% celda 59 [código]
print(PARAM$out$lgbm$mejores_hiperparametros)
print(PARAM$out$lgbm$y)

# [Anotación · líneas 577–610] Crea y fija como carpeta de trabajo /content/buckets/b1/exp/exp4992. Crea
#   clase01 en todo el dataset, filtra los meses de PARAM$train_final, cuenta filas por clase y arma
#   dtrain_final con todas esas filas y las columnas de campos_buenos.
#%% celda 60 [texto]
## 2.3  Produccion

#%% celda 61 [texto]
### Final Training
Construyo el modelo final, que es uno solo, no hace ningun tipo de particion < training, validation, testing>]

#%% celda 62 [código]
setwd("/content/buckets/b1/exp")
experimento <- paste0("exp", PARAM$experimento)
dir.create(experimento, showWarnings= FALSE)
setwd( paste0("/content/buckets/b1/exp/", experimento ))

#%% celda 63 [texto]
#### Final Training Dataset

Aqui esta la gran decision de en qué meses hago el Final Training
<br> debo utilizar los mejores hiperparámetros que encontré en la  optimización bayesiana

#%% celda 64 [código]
# clase01
dataset[, clase01 := ifelse(clase_ternaria %in% c("BAJA+1", "BAJA+2"), 1L, 0L)]

#%% celda 65 [código]
dataset_train <- dataset[foto_mes %in% PARAM$train_final]
dataset_train[,.N,clase_ternaria]

#%% celda 66 [código]
# dejo los datos en el formato que necesita LightGBM

dtrain_final <- lgb.Dataset(
  data= data.matrix(dataset_train[, campos_buenos, with= FALSE]),
  label= dataset_train[, clase01]
)

# [Anotación · líneas 612–652] param_final superpone a param_fijos los hiperparámetros de la primera fila de
#   la búsqueda. param_normalizado copia param_final y reemplaza min_data_in_leaf por round(min_data_in_leaf /
#   0.2). Entrena modelo_final con lgb.train sobre dtrain_final, graba la tabla de importancia de variables en
#   impo.txt y el modelo en modelo.txt.
#%% celda 67 [texto]
#### Final Training Hyperparameters

#%% celda 68 [código]
param_final <- modifyList(PARAM$lgbm$param_fijos,
  PARAM$out$lgbm$mejores_hiperparametros)

param_final

#%% celda 69 [texto]
#### Training
Genero el modelo final, siempre sobre TODOS los datos de  final_train, sin hacer ningun tipo de undersampling de la clase mayoritaria y mucho menos cross validation.

#%% celda 70 [código]
# este punto es muy SUTIL  y será revisado en la Clase 05

param_normalizado <- copy(param_final)
param_normalizado$min_data_in_leaf <-  round(param_final$min_data_in_leaf / PARAM$trainingstrategy$undersampling)

#%% celda 71 [código]
# entreno LightGBM

modelo_final <- lgb.train(
  data= dtrain_final,
  param= param_normalizado
)

#%% celda 72 [código]
# ahora imprimo la importancia de variables

tb_importancia <- as.data.table(lgb.importance(modelo_final))
archivo_importancia <- "impo.txt"

fwrite(tb_importancia,
  file= archivo_importancia,
  sep= "\t"
)

#%% celda 73 [código]
# grabo a disco el modelo en un formato para seres humanos ... ponele ...
lgb.save(modelo_final, "modelo.txt" )

# [Anotación · líneas 654–668] Celda con todas sus líneas comentadas: el filtrado de dfuture y el predict de
#   modelo_final sobre los meses de PARAM$future.
#%% celda 74 [texto]
### Scoring

#%% celda 75 [texto]
Aplico el modelo final a los datos del futuro

#%% celda 76 [código]
# aplico el modelo a los datos sin clase
#dfuture <- dataset[foto_mes %in% PARAM$future]

# aplico el modelo a los datos nuevos
#prediccion <- predict(
  #modelo_final,
  #data.matrix(dfuture[, campos_buenos, with= FALSE])
#)

# [Anotación · líneas 670–720] Filtra las filas de 202108 (dfuture), las pasa a matriz y crea una tabla con
#   numero_de_cliente y prob_acum en 0. Recorre un vector de 20 semillas: en cada vuelta copia
#   param_normalizado, asigna la semilla a seed, entrena un LightGBM sobre dtrain_final, suma su predicción a
#   prob_acum y libera memoria. prediccion es prob_acum dividido por 20. Arma tb_prediccion con cliente y prob y
#   la ordena por prob descendente.
#%% celda 77 [código]
# Preparo los datos de scoring para Agosto (202108)
dfuture <- dataset[foto_mes %in% PARAM$future]
dmat_future <- data.matrix(dfuture[, campos_buenos, with = FALSE])

# Tabla para acumular las probabilidades de las 20 semillas
tb_predicciones <- dfuture[, .(numero_de_cliente)]
tb_predicciones[, prob_acum := 0]

semillas <- c(
  137363, 284309, 417563, 638417, 873457,
  100003, 300007, 500041, 700089, 900103,
  150001, 220009, 350003, 450007, 550021,
  680003, 750019, 800011, 850009, 890003
)

cat("Iniciando entrenamiento y scoring del ensamble de", length(semillas), "semillas...\n")

for (i in seq_along(semillas)) {
  s <- semillas[i]
  cat(format(Sys.time(), "%X"), "- Entrenando Semilla", i, "de", length(semillas), ":", s, "...\n")

  # Asignamos la semilla actual sobre los parámetros normalizados
  param_semilla <- copy(param_normalizado)
  param_semilla$seed <- s

  # Entrenamos LightGBM
  m_semilla <- lgb.train(
    data = dtrain_final,
    param = param_semilla
  )

  # Acumulamos la predicción de Agosto
  tb_predicciones[, prob_acum := prob_acum + predict(m_semilla, dmat_future)]

  # Limpiea de memoria
  rm(m_semilla)
  gc(full = TRUE, verbose = FALSE)
}

# 'prediccion' guarda el promedio exacto de las 20 semillas
prediccion <- tb_predicciones$prob_acum / length(semillas)

# Creamos la tabla final lista para los cortes de envío
tb_prediccion <- data.table(
  numero_de_cliente = dfuture$numero_de_cliente,
  prob = prediccion
)

# Reconfirmamos el orden descendente por probabilidad
setorder(tb_prediccion, -prob)

# [Anotación · líneas 722–734] Vuelve a armar tb_prediccion desde dfuture con numero_de_cliente, foto_mes y
#   clase_ternaria, le agrega prob y graba cliente, mes y prob en prediccion.txt separado por tabulaciones.
#%% celda 78 [texto]
#### Tabla Prediccion

#%% celda 79 [código]
# tabla de prediccion
tb_prediccion <- dfuture[, list(numero_de_cliente, foto_mes,clase_ternaria)]
tb_prediccion[, prob := prediccion ]

# grabo las probabilidad del modelo
fwrite(tb_prediccion[,list(numero_de_cliente,foto_mes,prob)],
  file= "prediccion.txt",
  sep= "\t"
)

# [Anotación · líneas 736–764] Ordena por prob descendente y agrega gan (1072500 si clase_ternaria es BAJA+2,
#   -27500 en otro caso), ganancia_acumulada (suma acumulada de gan) y pos (posición). Muestra las primeras
#   filas y grafica con ggplot2 la ganancia acumulada de las primeras 30000 posiciones.
#%% celda 80 [código]
# Dibujo la curva de ganancia acumulada
setorder(tb_prediccion,-prob)

tb_prediccion[, gan := ifelse(clase_ternaria == "BAJA+2", 1072500, -27500)]
tb_prediccion[, ganancia_acumulada := cumsum(gan)]
tb_prediccion[, pos := sequence(.N)]

#%% celda 81 [código]
tb_prediccion |> head()

#%% celda 82 [código]
# defino hasta donde muestra el grafico
amostrar <- 30000

#%% celda 83 [código]
require("ggplot2")

#%% celda 84 [código]
# observamos la curva de ganancia
gra <- ggplot(
           data= tb_prediccion[pos <= amostrar],
           aes( x= pos, y= ganancia_acumulada)
             ) + geom_line()

gra <- gra + theme(text = element_text(size = 16))

options(repr.plot.width=16, repr.plot.height=9)
print( gra )

# [Anotación · líneas 766–790] Llama a realidad_inicializar con dfuture, muestra PARAM$cortes, graba PARAM.yml
#   en la carpeta exp4992 e imprime fecha y hora. Muestra el resumen estadístico de prob y cuenta las filas del
#   dataset por mes según tengan o no clase_ternaria.
#%% celda 85 [texto]
Revisamos ganancia bajo distintos cortes

#%% celda 86 [código]
# inicilizo el dataset  drealidad
drealidad <- realidad_inicializar( dfuture, PARAM)

#%% celda 87 [código]
PARAM$cortes

#%% celda 88 [código]
write_yaml( PARAM, file="PARAM.yml")

#%% celda 89 [código]
format(Sys.time(), "%a %b %d %X %Y")

#%% celda 90 [texto]
Finalmente usted deberá cargar el resultado de su corrida en la Google Sheet Colaborativa,  hoja **TareaHogar04**
<br> Siéntase libre de agregar las columnas que hagan falta a la planilla

#%% celda 91 [código]
summary(tb_prediccion$prob)

#%% celda 92 [código]
dataset[, .N, by = .(foto_mes, tiene_baja = (clase_ternaria != "" & !is.na(clase_ternaria)))]

# [Anotación · líneas 792–811] Ordena tb_prediccion por prob descendente y, para cada corte de la lista 9500,
#   10000, 10250, 10500, 10750, 11000, 11250, 11500, 11750, 12000 y 12500, graba
#   /content/MI_ENTREGA_ZULIP_<corte>.csv con los primeros numero_de_cliente convertidos a entero, sin
#   encabezado, e imprime el nombre del archivo.
#%% celda 93 [código]
setorder(tb_prediccion, -prob)

cortes_altos <- c(
  9500,
  10000, 10250, 10500, 10750,
  11000, 11250, 11500, 11750,
  12000, 12500
)

# Generar cada archivo automáticamente
for (corte in cortes_altos) {
  fwrite(
    tb_prediccion[1:corte, .(numero_de_cliente = as.integer(numero_de_cliente))],
    file = paste0("/content/MI_ENTREGA_ZULIP_", corte, ".csv"),
    col.names = FALSE,
    sep = ","
  )
  cat("Archivo generado: MI_ENTREGA_ZULIP_", corte, ".csv\n", sep = "")
}
```

### Competencia_1_3_20s_(RDATA).ipynb

Notebook de R para Google Colab (experimento 4990): descarga el dataset, calcula clase_ternaria y los deltas contra las dos filas anteriores, y corre la optimización bayesiana de cinco hiperparámetros de LightGBM con AUC en validación cruzada de 5 folds. Deja bayesiana.RDATA, BO_log.txt y PARAM.yml en /content/buckets/b1/exp/HT4990.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–59] Celdas de texto 1 a 12: título, objetivos de una tarea sobre hiperparámetros de
#   LightGBM y optimización bayesiana, enlaces a la documentación de LightGBM y a tres artículos, e indicación
#   de usar el runtime Python 3 de Google Colab y conectar Google Drive.
#%% celda 1 [texto]
# 1° COMPETECIA DM EyF

#%% celda 2 [texto]
##  1. Big Picture

#%% celda 3 [texto]
LightGBM es el algoritmo estado del arte para datasets estructurados.
<br> La Bayesian Optimization es el estado del arte para optimización de hiperparámetros
<br> Las soluciones a las tres competencias de la asignatura contendrán LightGBMs y Bayesian Optimizations
<br> LightGBM ha aumentado en forma no darwiniana sus hiperparámetros en los últimos ocho años; no todos los existentes son útiles.
<br> Es necesario lograr entender cuales son los hiperparámetros relevantes de LightGBM

#%% celda 4 [texto]
## 2. Hiperparámetros del LightGBM

#%% celda 5 [texto]
Los objetivos de esta tarea son:


*   Aumentar la rentabilidad de la campaña de marketing de retención proactiva de clientes.
*   Generar un mejor modelo optimizando sus hiperparámetros
*   Conceptual : investigar los mas relevantes hiperparámetros de LightGBM
*   Familiarizarse con la Bayesian Optimization, sus largos tiempos de corrida y opciones para reducirlos
*   Familiarizarse con el uso de máquinas virtuales de Google Colab
*   Ver un pipeline completo de optimización de hiperparámetros y puesta en producción

#%% celda 6 [texto]
LightGBM cuenta con mas de 60 hiperparámetros, siendo posible utilizar 40 al mismo tiempo, aunque no razonable.
<br> La documentación oficial de los hiperparámetros de LightGBM es  https://lightgbm.readthedocs.io/en/latest/Parameters.html#core-parameters

#%% celda 7 [texto]
Se lo alerta sobre que una Optimizacion Bayesiana lleva varias horas de corrida, y usted deberá correr VARIAS optimizaciones para descubrir cuales parámetros conviene optimizar.
<br> A pesar que la próxima clase es recien en viernes 01 de agosto, inicie la tarea con tiempo, aprenda a planificar estratégicamente sus corridas como un@ científ@  de datos.

#%% celda 8 [texto]
Es necesario investigar cuales son los hiperparámetros de LightGBM que vale la pena optimizar en una Bayesian Optimization, ya que los realmente utiles son apenas un reducido subconjunto.
<br>Usted deberá investigar cuales son los hiperparámetros mas relevantes de LightGBM, su primer alternativa es preguntándole a su amigo con capacidades especiales ChatGPT o sus endogámicos familiares Claude, DeepSeek, Gemini, Grok, etc
<br> La segunda alternativa es la propia documentación de LightGBM  https://lightgbm.readthedocs.io/en/latest/Parameters-Tuning.html

#%% celda 9 [texto]
Adicionalmente podra buscar información como la que proveen esta diminuta muestra aleatoria de artículos ligeros:
*  https://medium.com/@sarahzouinina/a-deep-dive-into-lightgbm-how-to-choose-and-tune-parameters-7c584945842e
*  https://www.kaggle.com/code/somang1418/tuning-hyperparameters-under-10-minutes-lgbm
*  https://towardsdatascience.com/beginners-guide-to-the-must-know-lightgbm-hyperparameters-a0005a812702/


<br>  La muestra anterior se brinda a modo de ejemplo, usted deberá buscar muuuuchas  fuentes adicionales de información
<br> Tenga presente que LightGBM es el estado del arte en modelado predictivo para datasets estructurado, que son el 90% del trabajo del 95% de los Data Scientists en Argentina.

#%% celda 10 [texto]
#### 2.1  Seteo del ambiente en Google Colab

#%% celda 11 [texto]
Esta parte se debe correr con el runtime en Python3
<br>Ir al menu, Runtime -> Change Runtime Type -> Runtime type ->  **Python 3**

#%% celda 12 [texto]
Conectar la virtual machine donde esta corriendo Google Colab con el  Google Drive, para poder tener persistencia de archivos

# [Anotación · líneas 61–99] Monta Google Drive en /content/.drive (celda de Python). En una celda de shell
#   crea 'My Drive/dmeyf', la enlaza como /content/buckets/b1 y crea las carpetas exp, datasets y
#   /content/datasets; si competencia_01_crudo.csv no está en el bucket lo descarga con wget desde
#   storage.googleapis.com/open-courses/dmeyf2026-9c6f, y lo copia al disco local si falta.
#%% celda 13 [código]
# primero establecer el Runtime de Python 3
from google.colab import drive
drive.mount('/content/.drive')

#%% celda 14 [texto]
Para correr la siguiente celda es fundamental en Arranque en Frio haber copiado el archivo kaggle.json al Google Drive, en la carpeta indicada en el instructivo

<br>los siguientes comando estan en shell script de Linux
*   Crear las carpetas en el Google Drive
*   "instalar" el archivo kaggle.json desde el Google Drive a la virtual machine para que pueda ser utilizado por la libreria  kaggle de Python
*   Bajar el  **dataset_pequeno**  al  Google Drive  y tambien al disco local de la virtual machine que esta corriendo Google Colab

#%% celda 15 [código]
%%shell

mkdir -p "/content/.drive/My Drive/dmeyf"
mkdir -p "/content/buckets"
ln -s "/content/.drive/My Drive/dmeyf" /content/buckets/b1


mkdir -p /content/buckets/b1/exp
mkdir -p /content/buckets/b1/datasets
mkdir -p /content/datasets



archivo_origen="https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
archivo_destino="/content/datasets/competencia_01_crudo.csv"
archivo_destino_bucket="/content/buckets/b1/datasets/competencia_01_crudo.csv"

if ! test -f $archivo_destino_bucket; then
  wget  $archivo_origen  -O $archivo_destino_bucket
fi


if ! test -f $archivo_destino; then
  cp  $archivo_destino_bucket  $archivo_destino
fi

# [Anotación · líneas 101–135] Lee competencia_01_crudo.csv con fread y calcula clase_ternaria: arma una tabla
#   auxiliar con la posición original, el cliente y el período como año × 12 + mes, y con shift de tipo lead
#   obtiene los dos períodos siguientes de cada cliente. Asigna CONTINUA a los períodos anteriores al
#   anteúltimo, luego BAJA+1 donde falta el período siguiente (en períodos anteriores al último) y BAJA+2 donde
#   está el siguiente y falta el subsiguiente. Vuelve al orden original y copia la clase al dataset.
#%% celda 16 [texto]
DELTA LAGS 1 y 2

#%% celda 17 [código]
require("data.table")

dataset <- fread("/content/datasets/competencia_01_crudo.csv")

# Calcular la clase_ternaria
dsimple <- dataset[, list(
    "pos" = .I,
    numero_de_cliente,
    periodo0 = as.integer(foto_mes/100)*12 + foto_mes%%100 ) ]

setorder(dsimple, numero_de_cliente, periodo0)

periodo_ultimo <- dsimple[, max(periodo0)]
periodo_anteultimo <- periodo_ultimo - 1

dsimple[, c("periodo1", "periodo2") :=
    shift(periodo0, n=1:2, fill=NA, type="lead"), numero_de_cliente]

dsimple[periodo0 < periodo_anteultimo, clase_ternaria := "CONTINUA"]

dsimple[periodo0 < periodo_ultimo &
    (is.na(periodo1) | periodo0 + 1 < periodo1),
    clase_ternaria := "BAJA+1"]

dsimple[periodo0 < periodo_anteultimo & (periodo0+1 == periodo1)
    & (is.na(periodo2) | periodo0 + 2 < periodo2),
    clase_ternaria := "BAJA+2"]

setorder(dsimple, pos)
dataset[, clase_ternaria := dsimple$clase_ternaria]
rm(dsimple)

# [Anotación · líneas 137–169] Ordena por cliente y mes. Para cada columna que no es numero_de_cliente,
#   foto_mes ni clase_ternaria crea d_<columna>_lag1 = valor menos el de la fila anterior y d_<columna>_lag2 =
#   valor menos el de dos filas atrás. Marca las filas cuya fila anterior, o la de dos atrás, pertenece a otro
#   cliente y en ellas pone NA: en lag1 con la primera marca, en lag2 con cualquiera de las dos. Graba la tabla
#   en /content/datasets/competencia_01.csv.gz e imprime la cantidad de columnas.

# DELTA LAG1 Y DELTA LAG2
setorder(dataset, numero_de_cliente, foto_mes)

cols_id <- c("numero_de_cliente", "foto_mes", "clase_ternaria")
cols_features <- setdiff(colnames(dataset), cols_id)


cols_deltas_lag1 <- paste0("d_", cols_features, "_lag1")
cols_deltas_lag2 <- paste0("d_", cols_features, "_lag2")

dataset[, (cols_deltas_lag1) := .SD - shift(.SD, n = 1, type = "lag"),
        .SDcols = cols_features]

es_nuevo_cliente_1 <- dataset$numero_de_cliente != shift(dataset$numero_de_cliente, n = 1, type = "lag")
es_nuevo_cliente_1[1] <- TRUE
dataset[es_nuevo_cliente_1, (cols_deltas_lag1) := NA]


dataset[, (cols_deltas_lag2) := .SD - shift(.SD, n = 2, type = "lag"),
        .SDcols = cols_features]

es_nuevo_cliente_2 <- dataset$numero_de_cliente != shift(dataset$numero_de_cliente, n = 2, type = "lag")
es_nuevo_cliente_2[1:2] <- TRUE
dataset[es_nuevo_cliente_1 | es_nuevo_cliente_2, (cols_deltas_lag2) := NA]

# Limpieza de variables
rm(es_nuevo_cliente_1, es_nuevo_cliente_2)

# Guardar
fwrite(dataset, file = "/content/datasets/competencia_01.csv.gz", sep = ",")

cat("Proceso completado. Total de columnas guardadas:", ncol(dataset), "\n")

# [Anotación · líneas 171–179] Ordena el dataset por foto_mes, clase_ternaria y numero_de_cliente y cuenta las
#   filas por mes y clase. Las celdas de texto indican que esta parte se corre con el runtime R.
#%% celda 18 [texto]
## Generacion de la clase_ternaria

#%% celda 19 [texto]
Esta parte se debe correr con el runtime en lenguaje **R** Ir al menu, Runtime -> Change Runtime Tipe -> Runtime type -> R

#%% celda 20 [código]
setorder( dataset, foto_mes, clase_ternaria, numero_de_cliente)
dataset[, .N, list(foto_mes, clase_ternaria)]

# [Anotación · líneas 181–203] Obtiene los clientes de 202107 y de 202108 y calcula los que están en 202108 y
#   no en 202107; imprime ambas cantidades. Con BORRAR_NUEVOS_AGOSTO = TRUE elimina de la tabla en memoria las
#   filas de 202108 de esos clientes. La tabla en memoria se borra en la celda 27 y la celda 46 lee el archivo
#   grabado en la celda 17.
#%% celda 21 [código]
# 1. Obtener los IDs de clientes presentes en 202107 y 202108
clientes_julio  <- dataset[foto_mes == 202107, unique(numero_de_cliente)]
clientes_agosto <- dataset[foto_mes == 202108, unique(numero_de_cliente)]

# 2. Identificar clientes nuevos (en agosto pero NO en julio)
clientes_nuevos_agosto <- setdiff(clientes_agosto, clientes_julio)

cat("--------------------------------------------------\n")
cat("Total de clientes en Agosto (202108):", length(clientes_agosto), "\n")
cat("Clientes nuevos en Agosto (no estaban en Julio):", length(clientes_nuevos_agosto), "\n")
cat("--------------------------------------------------\n")

# 3. OPCIÓN DE CONFIGURACIÓN: ¿Deseas borrarlos? (TRUE = Borrar / FALSE = Mantener)
BORRAR_NUEVOS_AGOSTO <- TRUE  # <-- Cambiá a FALSE si decidís conservarlos

if (BORRAR_NUEVOS_AGOSTO) {
  # Filtrar el dataset removiendo estos clientes
  dataset <- dataset[!(foto_mes == 202108 & numero_de_cliente %in% clientes_nuevos_agosto)]
  cat("--> Se han eliminado los", length(clientes_nuevos_agosto), "clientes nuevos de Agosto del dataset.\n")
} else {
  cat("--> Se mantuvieron los clientes nuevos en el dataset.\n")
}

# [Anotación · líneas 205–258] Imprime fecha y hora, borra todos los objetos del ambiente y libera memoria.
#   Carga data.table y parallel, e instala si faltan y carga R.utils, primes, utils, rlist, yaml, lightgbm,
#   DiceKriging y mlrMBO.
#%% celda 22 [texto]
### 2.2 Optimizacion Hiperparámetros

#%% celda 23 [texto]
Esta parte se debe correr con el runtime en lenguaje R Ir al menu, Runtime -> Change Runtime Type -> Runtime type -> R

#%% celda 24 [texto]
### 2.2.1 Inicio

#%% celda 25 [texto]
limpio el ambiente de R

#%% celda 26 [código]
format(Sys.time(), "%a %b %d %X %Y")

#%% celda 27 [código]
# limpio la memoria
rm(list=ls(all.names=TRUE)) # remove all objects
gc(full=TRUE, verbose=FALSE) # garbage collection

#%% celda 28 [texto]
### 2.2.2 Carga de Librerias

#%% celda 29 [texto]
Esta parte lleva varios minutos la primera vez en Google Colab

#%% celda 30 [código]
# cargo las librerias que necesito
require("data.table")
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

# [Anotación · líneas 260–284] Crea la lista PARAM: experimento 4990, semilla_primigenia 137363, train y
#   train_final con 202103, 202104, 202105 y 202106, future 202108, semilla_kaggle 314159, cortes de 4000 a
#   19000 cada 500 y undersampling 0.2 (proporción de CONTINUA que se conserva).
#%% celda 31 [texto]
### 2.2.3 Definicion de Parametros

#%% celda 32 [texto]
aqui debe cargar SU semilla primigenia
<br>recuerde cambiar el numero de experimento en cada corrida nueva

#%% celda 33 [código]
PARAM <- list()
PARAM$experimento <- 4990
PARAM$semilla_primigenia <- 137363

#%% celda 34 [código]
# training y future
PARAM$train <- c(202103, 202104, 202105, 202106)
PARAM$train_final <- c(202103, 202104, 202105, 202106)
PARAM$future <- c(202108)
PARAM$semilla_kaggle <- 314159
PARAM$cortes <- seq(4000, 19000, by= 500)

#%% celda 35 [código]
# un undersampling de 0.1  toma solo el 10% de los CONTINUA
# undersampling de 1.0  implica tomar TODOS los datos

PARAM$trainingstrategy$undersampling <- 0.2

# [Anotación · líneas 286–329] Fija 5 folds para la validación cruzada y la lista param_fijos de LightGBM:
#   boosting gbdt, objective binary, metric auc, seed = semilla_primigenia, max_depth -1, min_gain_to_split 0,
#   min_sum_hessian_in_leaf 0.001, lambda_l1 y lambda_l2 0, max_bin 31, fracciones de bagging 1.0, is_unbalance
#   FALSE, scale_pos_weight 1.0, drop_rate 0.1, max_drop 50, skip_drop 0.5, extra_trees FALSE y valores de
#   resguardo num_iterations 600, learning_rate 0.03, feature_fraction 0.50, num_leaves 256 y min_data_in_leaf
#   1000.
#%% celda 36 [código]
# Parametros LightGBM

PARAM$hyperparametertuning$xval_folds <- 5

# parametros fijos del LightGBM que se pisaran con la parte variable de la BO
PARAM$lgbm$param_fijos <- list(
  boosting = "gbdt",
  objective = "binary",
  metric = "auc",
  first_metric_only = FALSE,
  boost_from_average = TRUE,
  feature_pre_filter = FALSE,
  force_row_wise = TRUE, # para reducir warnings
  verbosity = -100,

  seed = PARAM$semilla_primigenia,

  max_depth = -1L, # -1 significa no limitar
  min_gain_to_split = 0,
  min_sum_hessian_in_leaf = 0.001,
  lambda_l1 = 0.0,
  lambda_l2 = 0.0,
  max_bin = 31L, # Fijo, no participa de la BO

  bagging_fraction = 1.0,
  pos_bagging_fraction = 1.0,
  neg_bagging_fraction = 1.0,
  is_unbalance = FALSE,
  scale_pos_weight = 1.0,

  drop_rate = 0.1,
  max_drop = 50,
  skip_drop = 0.5,

  extra_trees = FALSE, # Cambiar a TRUE si deseas probar la variante Extra Trees

  # Valores por defecto de resguardo (se sobreescriben en cada iteración de la BO)
  num_iterations = 600,
  learning_rate = 0.03,
  feature_fraction = 0.50,
  num_leaves = 256,
  min_data_in_leaf = 1000
)

# [Anotación · líneas 331–353] Define el espacio de búsqueda con makeParamSet: num_iterations entero entre 200
#   y 600, learning_rate entre 0.02 y 0.10, feature_fraction entre 0.20 y 0.70, num_leaves entero entre 32 y 256
#   y min_data_in_leaf entero entre 500 y 4000. Fija 20 iteraciones bayesianas.
#%% celda 37 [texto]
Aqui se definen los hiperparámetros de LightGBM que participan de la Bayesian Optimization
<br> si es un numero entero debe ir  makeIntegerParam
<br> si es un numero real (con decimales) debe ir  makeNumericParam
<br> es muy importante leer cuales son un lower y upper  permitidos y ademas razonables

#%% celda 38 [código]
#Límites acotados de los árboles
PARAM$hypeparametertuning$hs <- makeParamSet(
  makeIntegerParam("num_iterations", lower = 200L, upper = 600L),
  makeNumericParam("learning_rate", lower = 0.02, upper = 0.10),
  makeNumericParam("feature_fraction", lower = 0.20, upper = 0.70),
  makeIntegerParam("num_leaves", lower = 32L, upper = 256L),
  makeIntegerParam("min_data_in_leaf", lower = 500L, upper = 4000L)
)

#%% celda 39 [texto]
A mayor cantidad de hiperparámetros, se debe aumentar las iteraciones de la Bayesian Optimization
<br> 30 es un valor muy tacaño, pero corre rápido
<br> deberia partir de 50, alcanzando los 100 si se dispone de tiempo

#%% celda 40 [código]
PARAM$hyperparametertuning$iteraciones <- 20 # iteraciones bayesianas

# [Anotación · líneas 355–405] Define tres funciones. particionar agrega una columna fold con una partición al
#   azar en las proporciones pedidas, estratificada por el campo indicado y con semilla opcional.
#   realidad_inicializar toma cliente, mes y clase de una tabla y la parte en proporción 3 a 7 por
#   clase_ternaria con semilla_kaggle. realidad_evaluar une una predicción y calcula la ganancia (1072500 por
#   cada BAJA+2 enviado, -27500 por el resto) en el fold 1 dividida por 0.3, en el fold 2 dividida por 0.7 y
#   total. En este notebook ninguna de las tres se llama.
#%% celda 41 [código]
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

#%% celda 42 [código]
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

#%% celda 43 [código]
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

# [Anotación · líneas 407–432] Crea y fija como carpeta de trabajo /content/buckets/b1/exp/HT4990. Lee
#   competencia_01.csv.gz, se queda con las filas de los meses de PARAM$train y crea clase01: 1 para BAJA+1 y
#   BAJA+2, 0 para el resto.
#%% celda 44 [texto]
### 2.2.4  Preprocesamiento

#%% celda 45 [código]
# carpeta de trabajo

setwd("/content/buckets/b1/exp")
experimento_folder <- paste0("HT", PARAM$experimento)
dir.create(experimento_folder, showWarnings=FALSE)
setwd( paste0("/content/buckets/b1/exp/", experimento_folder ))

#%% celda 46 [código]
# lectura del dataset
dataset <- fread("/content/datasets/competencia_01.csv.gz", stringsAsFactors= TRUE)

#%% celda 47 [código]
dataset_train <- dataset[foto_mes %in% PARAM$train]

#%% celda 48 [código]
# paso la clase a binaria que tome valores {0,1}  enteros
#  BAJA+1 y BAJA+2  son  1,   CONTINUA es 0
#  a partir de ahora ya NO puedo cortar  por prob(BAJA+2) > 1/40

dataset_train[,
  clase01 := ifelse(clase_ternaria %in% c("BAJA+2","BAJA+1"), 1L, 0L)
]

# [Anotación · líneas 434–468] Con set.seed(137363) genera un número uniforme por fila (azar) y marca training
#   = 1 en las filas BAJA+1 y BAJA+2 y en las demás filas con azar menor o igual a 0.2. campos_buenos son todas
#   las columnas menos clase_ternaria, clase01, azar y training; numero_de_cliente y foto_mes quedan incluidas.
#   Arma el lgb.Dataset dtrain con las filas training = 1 y muestra su cantidad de filas y columnas.
#%% celda 49 [código]
# defino los datos que forma parte del training
# aqui se hace el undersampling de los CONTINUA
# notar que para esto utilizo la SEGUNDA semilla

set.seed(PARAM$semilla_primigenia, kind = "L'Ecuyer-CMRG")
dataset_train[, azar := runif(nrow(dataset_train))]
dataset_train[, training := 0L]

dataset_train[
  foto_mes %in%  PARAM$train &
    (azar <= PARAM$trainingstrategy$undersampling | clase_ternaria %in% c("BAJA+1", "BAJA+2")),
  training := 1L
]

#%% celda 50 [código]
###¿El ID de los clientes?
# los campos que se van a utilizar

campos_buenos <- setdiff(
  colnames(dataset_train),
  c("clase_ternaria", "clase01", "azar", "training")
)

#%% celda 51 [código]
# dejo los datos en el formato que necesita LightGBM

dtrain <- lgb.Dataset(
  data= data.matrix(dataset_train[training == 1L, campos_buenos, with= FALSE]),
  label= dataset_train[training == 1L, clase01],
  free_raw_data= FALSE
)

nrow(dtrain)
ncol(dtrain)

# [Anotación · líneas 470–500] EstimarGanancia_AUC_lightgbm recibe los hiperparámetros propuestos, los
#   superpone a param_fijos, corre lgb.cv sobre dtrain con 5 folds estratificados y devuelve modelocv$best_score
#   como AUC. Libera memoria e imprime la hora y el valor.
#%% celda 52 [texto]
2.2.5 Configuracion Bayesian Optimization

#%% celda 53 [código]
# En el argumento x llegan los parmaetros de la bayesiana
#  devuelve la AUC en cross validation del modelo entrenado

EstimarGanancia_AUC_lightgbm <- function(x) {

  # x pisa (o agrega) a param_fijos
  param_completo <- modifyList(PARAM$lgbm$param_fijos, x)

  # entreno LightGBM
  modelocv <- lgb.cv(
    data= dtrain,
    nfold= PARAM$hyperparametertuning$xval_folds,
    stratified= TRUE,
    param= param_completo
  )

  # obtengo la ganancia
  AUC <- modelocv$best_score

  # hago espacio en la memoria
  rm(modelocv)
  gc(full= TRUE, verbose= FALSE)

  message(format(Sys.time(), "%a %b %d %X %Y"), " AUC ", AUC)

  return(AUC)
}

# [Anotación · líneas 502–545] Configura mlrMBO: archivo de estado bayesiana.RDATA; función de un solo
#   objetivo a maximizar, marcada como ruidosa (noisy), sobre el espacio de búsqueda; guardado en disco cada 300
#   segundos; término a las 20 iteraciones; criterio de infill Expected Improvement; modelo sustituto regr.km
#   (kriging) con covarianza matern3_2 y predicción con error estándar.
#%% celda 54 [código]
# Aqui comienza la configuracion de la Bayesian Optimization

# en este archivo quedan la evolucion binaria de la BO
kbayesiana <- "bayesiana.RDATA"

funcion_optimizar <- EstimarGanancia_AUC_lightgbm # la funcion que voy a maximizar

configureMlr(show.learner.output= FALSE)

# configuro la busqueda bayesiana,  los hiperparametros que se van a optimizar
# por favor, no desesperarse por lo complejo

obj.fun <- makeSingleObjectiveFunction(
  fn= funcion_optimizar, # la funcion que voy a maximizar
  minimize= FALSE, # estoy Maximizando la ganancia
  noisy= TRUE,
  par.set= PARAM$hypeparametertuning$hs, # definido al comienzo del programa
  has.simple.signature= FALSE # paso los parametros en una lista
)

# cada 600 segundos guardo el resultado intermedio
ctrl <- makeMBOControl(
  save.on.disk.at.time= 300, # se graba cada 300 segundos
  save.file.path= kbayesiana
) # se graba cada 300 segundos

# indico la cantidad de iteraciones que va a tener la Bayesian Optimization
ctrl <- setMBOControlTermination(
  ctrl,
  iters= PARAM$hyperparametertuning$iteraciones
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

# [Anotación · líneas 547–600] Si bayesiana.RDATA no existe corre mbo; si existe, llama a mboContinue con ese
#   archivo. Convierte el historial (opt.path) en tabla, numera las filas, las ordena por y (AUC) descendente y
#   graba BO_log.txt. Guarda en PARAM$out$lgbm$mejores_hiperparametros las columnas de hiperparámetros de la
#   primera fila y en PARAM$out$lgbm$y su AUC; escribe PARAM.yml e imprime ambos. El notebook termina aquí.
#%% celda 55 [texto]
2.2.6 Corrida Bayesian Optimization

#%% celda 56 [código]

# inicio la optimizacion bayesiana, retomando si ya existe
# es la celda mas lenta de todo el notebook

if (!file.exists(kbayesiana)) {
  bayesiana_salida <- mbo(obj.fun, learner= surr.km, control= ctrl)
} else {
  bayesiana_salida <- mboContinue(kbayesiana) # retomo en caso que ya exista
}

#%% celda 57 [código]

tb_bayesiana <- as.data.table(bayesiana_salida$opt.path)
colnames( tb_bayesiana)

#%% celda 58 [código]
# almaceno los resultados de la Bayesian Optimization
# y capturo los mejores hiperparametros encontrados

tb_bayesiana <- as.data.table(bayesiana_salida$opt.path)

tb_bayesiana[, iter := .I]

# ordeno en forma descendente por AUC = y
setorder(tb_bayesiana, -y)

# grabo para eventualmente poder utilizarlos en OTRA corrida
fwrite( tb_bayesiana,
  file= "BO_log.txt",
  sep= "\t"
)

# los mejores hiperparámetros son los que quedaron en el registro 1 de la tabla
PARAM$out$lgbm$mejores_hiperparametros <- tb_bayesiana[
  1, # el primero es el de mejor AUC
  setdiff(colnames(tb_bayesiana),
    c("y","dob","eol","error.message","exec.time","ei","error.model",
      "train.time","prop.type","propose.time","se","mean","iter")),
  with= FALSE
]


PARAM$out$lgbm$y <- tb_bayesiana[1, y]

#%% celda 59 [código]
write_yaml( PARAM, file="PARAM.yml")

#%% celda 60 [código]
print(PARAM$out$lgbm$mejores_hiperparametros)
print(PARAM$out$lgbm$y)
```


## Explicaciones del alumno (texto original)

### README.md

> # Instrucciones de Ejecución
>
> 1. **Paso 1:** Ejecutar el notebook `Competencia_1_3_20s_(RDATA).ipynb`. Esto generará un archivo `.RDATA` con los hiperparámetros de la optimización bayesiana dentro de la carpeta `/content/buckets/b1/exp/HT4990`.
> 2. **Paso 2:** Crear la carpeta `/content/buckets/b1/exp/HT4992` y pegar el archivo `.RDATA` generado en el paso anterior.
> 3. **Paso 3:** Ejecutar el notebook `Competencia_1_5_20s.ipynb`.

