# Primera entrega – Feature engineering con ranking + LightGBM (BO + ensamble de semillas)


Predicción de bajas de clientes para el mes **202108** a partir de un LightGBM entrenado sobre variables rankeadas, con optimización bayesiana de hiperparámetros y un ensamble de 20 modelos finales (5 semillas con 501367, 10 con 898543 y 5 con 500153). Corte de 11000 enviado para la entrega.

---

## 1. Resumen del enfoque

| Etapa | Qué se hace |
|---|---|
| Datos | `competencia_01_crudo.csv` (983.061 filas × 154 columnas). Se genera `clase_ternaria`. |
| Feature engineering | Corrección de `ccajas_depositos`, lags y deltas 1 y 2, ranking con cero fijo por mes. |
| Data drift | KS entre variables rankeadas (abril vs junio como referencia, junio vs agosto). Informativo. |
| Optimización bayesiana | Train: marzo + abril. Validación: junio. Métrica: AUC, 1 semilla, 10 evaluaciones. |
| Curva de ganancia | Junio con 20 semillas promediadas, suavizada, para elegir el corte de envíos. |
| Modelo final | Train: marzo + abril + mayo + junio. 20 modelos (3 corridas: 5 + 10 + 5 semillas), probabilidad = promedio. |
| Envío | CSV con los `numero_de_cliente` a contactar, ordenados por probabilidad. |

## 2. Flujo del notebook

1. **Inicio y librerías:** `data.table`, `bbotk`, `mlr3`, `mlr3mbo`, `mlr3learners`, `paradox`, `DiceKriging`, `lightgbm`.
2. **Parámetros:** todo lo configurable está en un único objeto `PARAM`.
3. **Funciones auxiliares:** log de la BO, curva de ganancia y tabla de bajas por mes.
4. **Carga y chequeos:** existencia de los meses, clase presente en los meses de entrenamiento y un registro por cliente en agosto.
5. **Feature engineering** (ver sección 3).
6. **Diagnóstico de data drift.**
7. **Preprocesamiento:** armado de los `lgb.Dataset` sin undersampling.
8. **Optimización bayesiana.**
9. **Curva de ganancia de junio.**
10. **Modelo final y predicción de agosto.**
11. **Archivos de envío.**

## 3. Feature engineering

Se aplica **antes de cualquier entrenamiento**, en este orden:

1. **`ccajas_depositos` roto en 202105:** todos sus valores son 0 ese mes, por lo que se pasa a `NA` solo en 202105. Se hace primero para que los lags y deltas que dependen de ese valor también queden en `NA`.
2. **Lags y deltas 1 y 2** (marzo a agosto) para las 152 variables, excepto `foto_mes`, `numero_de_cliente`, `clase_ternaria` y `clase01`.
   * Los lags se calculan por **mes calendario**: si no hay registro de ese mes queda `NA` (marzo no tiene lags y abril no tiene lag 2).
   * `delta1 = valor_t − valor_t-1` y `delta2 = valor_t − valor_t-2`.
3. **Ranking con cero fijo dentro de cada `foto_mes`**, sobre las variables originales, los lags y los deltas: los negativos quedan en [-1, 0), los positivos en (0, 1] y el 0 se mantiene en 0. Los `NA` no se imputan.
4. Se eliminan las variables sin rankear, **salvo** `numero_de_cliente`, `foto_mes` y las clases.
5. Se guarda el dataset completo con FE en `competencia_01_crudo_FE_rank.csv` (983.061 filas × 764 columnas) para no repetir el proceso.

Resultado: **760 variables nuevas** con sufijos `_rank`, `_lag1_rank`, `_lag2_rank`, `_delta1_rank` y `_delta2_rank`.

## 4. Modelo

* **Variables de la BO (752):** `numero_de_cliente`, `foto_mes` y las rankeadas, **sin** `cprestamos_personales` ni `mprestamos_personales`.
* **Variables de la curva de junio y del modelo final (762):** las anteriores **más** los préstamos.
* **Sin undersampling** en ningún paso.
* **Parámetros fijos de LightGBM** (principales): `boosting= gbdt`, `objective= binary`, `learning_rate= 0.005`, `feature_fraction= 0.50`, `feature_fraction_bynode= 0.20`, `min_data_in_leaf= 0`, `max_bin= 31`.
* **Espacio de búsqueda de la BO:**

| Hiperparámetro | Rango |
|---|---|
| `num_iterations` | 64 – 4096 |
| `num_leaves` | 16 – 2048 |
| `min_sum_hessian_in_leaf` | 1e-06 – 0.1 |

* **Datos de entrenamiento / validación de la BO:** 326.184 filas (4.082 bajas) para entrenar y 164.114 filas (1.972 bajas) para validar.
* **Mejores hiperparámetros encontrados:**

| Hiperparámetro | Valor |
|---|---|
| `num_iterations` | 4028 |
| `num_leaves` | 1226 |
| `min_sum_hessian_in_leaf` | 0.00477222 |


## 5. Elección del corte de envíos

Agosto no tiene clase, por lo que el corte se estima con junio:

1. Se entrenan 20 modelos (uno por semilla) con marzo + abril y se promedian las probabilidades de junio.
2. Se calcula la ganancia acumulada para cada cantidad de envíos (cortes de 3.500 a 20.500 cada 50).
3. Se suaviza con una media móvil de 21 puntos (±500 envíos) y se toma el máximo.
4. Se identifica la **meseta** (valores ≥ 99% del máximo) y su centro.

La cantidad de envíos permitida es de 8.000 a 15.000.

## 6. Modelo final y archivos generados

El modelo final se entrena con **202103 + 202104 + 202105 + 202106** (654.066 filas, 8.067 bajas) con los mismos hiperparámetros, una semilla por modelo. Se hicieron **3 corridas finales**, cada una con una semilla primigenia distinta: **501367** (5 semillas), **898543** (10 semillas) y **500153** (5 semillas), es decir 20 modelos en total. La probabilidad de agosto (164.647 clientes) es el promedio de las semillas.

Archivos de salida en `~/buckets/b1/experimentos/primer_entrega_piloto_FE_rank_20semillas/`:

Cortes generados: 10.000, 11.000, 11.500, 12.000, 12.040, 12.350, 12.500, 12.700 y 13.000 envíos.

## 7. Reproducibilidad

* Semillas primigenias de las corridas finales: `501367` (5 semillas del modelo final), `898543` (10 semillas) y `500153` (5 semillas). La BO y la curva de junio se hicieron con `PARAM$semilla_primigenia = 501367`.

## 8. Cómo correrlo

1. Instalar los paquetes (hay una línea comentada en la celda de librerías):
   ```r
   install.packages(c("data.table", "bbotk", "mlr3", "mlr3mbo", "mlr3learners", "DiceKriging", "lightgbm"))
   ```
2. Ubicar el dataset en `~/buckets/b1/datasets/competencia_01_crudo.csv` (o ajustar `PARAM$carpeta_base` y `PARAM$archivo_dataset`).
3. Ejecutar las celdas en orden. La BO y los 20 entrenamientos (curva de junio y modelo final) son las partes más lentas.
4. Opciones útiles en `PARAM`:
   * `PARAM$correr_BO <- FALSE` para saltear la BO y usar `PARAM$hiperparametros_manuales`.
   * `PARAM$columnas_excluidas_modelo` para sacar columnas ya rankeadas (por ejemplo, según el diagnóstico de drift).
   * `PARAM$envios_manual` y `PARAM$cortes_envios` para fijar o probar cortes distintos.
5. Para no repetir el feature engineering, se puede cargar `competencia_01_crudo_FE_rank.csv` con `fread(..., stringsAsFactors= TRUE)`.
