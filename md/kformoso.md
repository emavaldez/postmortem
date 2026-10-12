# Karina Formoso — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: kformoso
- Repositorio: https://github.com/kformoso/Competencia1
- Link posteado: https://github.com/kformoso/Competencia1.git
- Commit: 56a820fd8ab10817ba06eb8a87e177c8b8682180
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/kformoso/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/kformoso.json

## Resumen

La entrega contiene un script en R (KF16.R), un README y un archivo CSV de predicción. El script lee competencia_01.csv.gz, pasa a NA la variable ccajas_depositos en 202105 (y en los meses donde vale siempre cero), calcula lags y deltas de orden 1 y 2 de todas las variables numéricas y agrega la pendiente y el promedio en una ventana de 3 filas por cliente con la función TendenciaYmuchomas, que el script identifica como código de la cátedra. Entrena LightGBM multiclase (CONTINUA, BAJA+1, BAJA+2) con 202104, 202105 y 202106, con hiperparámetros escritos en el código (learning_rate 0,027, num_leaves 31, min_data_in_leaf 200, feature_fraction 0,5, 500 rondas) y conservando el 20% de CONTINUA. Repite el entrenamiento con 60 semillas (primos desde 100003), guarda P(BAJA+1)+P(BAJA+2) de cada una para 202108, promedia y escribe los 12.000 clientes de mayor probabilidad promedio. El resultado de cada semilla queda en disco y, si el script se vuelve a ejecutar, entrena sólo las semillas que faltan. No contiene búsqueda de hiperparámetros ni validación; el comentario de cabecera menciona versiones anteriores (KF10, KF11) y un backtest de junio que no están en el repositorio.

**Qué entrega.** Un CSV de una columna, sin encabezado, con los 12.000 numero_de_cliente de 202108 de mayor probabilidad promedio; el script lo escribe en KF16/submits/KA_KF16_60semillas_12000.csv. El repositorio incluye el archivo 'KA_KF16_60semillas_12000 mi.csv', de 12.000 filas y una columna; el README nombra la entrega final como KA_KF16_60semillas_12000.csv.

**Cómo se ejecuta.** Según el README: con competencia_01.csv.gz en la misma carpeta, se corre con source('KF16.R').

## Ficha

- **Lenguajes:** R
- **Modelos:** LightGBM
- **Clase que entrena:** Multiclase de tres clases: 0 = CONTINUA, 1 = BAJA+1, 2 = BAJA+2 (columna clase01). Para ordenar a los clientes se usa P(BAJA+1) + P(BAJA+2).
- **Meses de entrenamiento:** 202104, 202105, 202106
- **Meses de validación:** —
- **Mes que predice:** 202108
- **Submuestreo:** En cada semilla se conservan todas las filas BAJA+1 y BAJA+2 de los meses de entrenamiento y las filas CONTINUA cuyo número uniforme al azar es menor o igual a 0,20 (UNDERSAMPLING = 0.20). El sorteo se repite con cada semilla. No se asignan pesos a las filas.
- **Calidad de datos:** ccajas_depositos se pasa a NA en 202105 (mes escrito en MESES_ROTOS_FORZADOS) y en todo mes donde sus valores no nulos son todos cero, antes de calcular los lags.
- **Drifting:** No se observa en el código
- **Variables dentro del mes:** No se observa en el código
- **Variables históricas:** Para todas las columnas numéricas originales salvo numero_de_cliente y foto_mes: lag 1 y lag 2, delta 1 y delta 2 (valor menos lag), con NA cuando la fila anterior no es del mismo cliente o no corresponde exactamente a k meses antes; y pendiente de mínimos cuadrados (_tend3) y promedio (_avg3) en una ventana de 3 filas consecutivas del mismo cliente, con TendenciaYmuchomas y fhistC (C++ vía Rcpp). Las opciones de mínimo, máximo y cocientes de ventana de esa función están en FALSE.
- **Selección de variables:** No se observa en el código. El modelo recibe todas las columnas salvo clase_ternaria y clase01 (numero_de_cliente y foto_mes quedan incluidas).
- **Optimización de hiperparámetros:** No se observa en el código. Los valores están escritos en PARAM_LGB y PARAM_DATASET.
- **Hiperparámetros finales:** objective multiclass, num_class 3, metric multi_logloss, boosting gbdt, learning_rate 0,027, num_leaves 31, min_data_in_leaf 200, feature_fraction 0,50, max_depth -1, lambda_l1 0, lambda_l2 0, min_gain_to_split 0, bagging_fraction 1, bagging_freq 0, max_bin 255, feature_pre_filter FALSE, force_row_wise TRUE, deterministic TRUE, 500 rondas (nrounds) sin parada temprana.
- **Semillas:** 60 semillas: los 60 primeros números primos a partir de 100003, calculados por la función primos_desde. Cada semilla se usa en set.seed (generador L'Ecuyer-CMRG) para el submuestreo de CONTINUA y como parámetro seed de LightGBM.
- **Cantidad de semillas:** 60
- **Ensamble:** Promedio aritmético por cliente de P(BAJA+1)+P(BAJA+2) de 60 modelos, uno por semilla, todos con los mismos hiperparámetros y cada uno entrenado sobre un sorteo distinto de CONTINUA.
- **Corte:** Cantidad fija: los 12.000 clientes de mayor probabilidad promedio (CORTE = 12000), con empates resueltos por orden de aparición. El comentario de cabecera indica que el valor pasa de 13.000 a 12.000 por un backtest de junio de la configuración KF11 con meseta de ganancia entre 10.816 y 12.263 envíos; ese backtest no está en el repositorio.
- **Validación:** No se observa en el código: el script no separa meses ni filas para medir. El comentario de cabecera (líneas 16 a 18) menciona un backtest de junio de la configuración KF11, que no está en el repositorio.
- **Salidas:** En la carpeta KF16/: semillas/seed_<semilla>.rds (vector de P(BAJA+1)+P(BAJA+2) de 202108 por semilla), ids_agosto.csv, firma.rds, log.txt, parametros.txt (parámetros, semillas y sessionInfo), prob_agosto_por_semilla.csv (probabilidad de cada semilla y promedio por cliente) y submits/KA_KF16_60semillas_12000.csv (archivo para enviar).

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Tres clases (CONTINUA, BAJA+1, BAJA+2) (`clase.multiclase`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: No se declara máquina, sistema ni versiones. El script carga data.table, lightgbm y Rcpp sin indicar versión; un comentario (línea 404) contempla la salida de predict en lightgbm 3.x y 4.x; al ejecutarse escribe sessionInfo() en KF16/parametros.txt, archivo que no está en el repositorio.

## Pasos del camino de la entrega

1. **Parámetros de la corrida.** Define el archivo de entrada (competencia_01.csv.gz), el nombre del experimento (KF16), los meses de entrenamiento (202104, 202105, 202106), el mes a predecir (202108), la variable rota y su mes forzado, la ventana de historia (3), la fracción de CONTINUA que se conserva (0,20), el corte (12.000), la cantidad de semillas (60), el primer primo (100003), las rondas (500) y las listas de parámetros del dataset y de LightGBM. (`KF16.R` líneas 37–79)
2. **Generación de las semillas.** La función primos_desde recorre los enteros desde 100003 y acumula los que no tienen divisores entre 2 y la parte entera de su raíz cuadrada, hasta juntar 60. El resultado queda en SEMILLAS. (`KF16.R` líneas 86–96)
3. **Carpetas, firma de parámetros y log.** Crea KF16/semillas y KF16/submits. Guarda en firma.rds la lista de parámetros de la corrida y detiene la ejecución si ya existe una firma distinta. Redirige la consola a KF16/log.txt, escribe parametros.txt con los parámetros y sessionInfo(), y calcula qué semillas todavía no tienen su archivo .rds. (`KF16.R` líneas 254–290)
4. **Lectura del dataset.** Si falta entrenar alguna semilla o no existe ids_agosto.csv, verifica que el archivo de datos esté en la carpeta de trabajo y lo lee completo con fread. (`KF16.R` líneas 297–302)
5. **Calidad de datos: ccajas_depositos a NA.** Busca los meses donde todos los valores no nulos de ccajas_depositos son cero, les suma el mes 202105 escrito en los parámetros y pone la variable en NA en esos meses. (`KF16.R` líneas 304–313)
6. **Lags y deltas de orden 1 y 2.** Ordena por cliente y mes y, para cada columna numérica original salvo numero_de_cliente y foto_mes, crea <campo>_lag1, <campo>_lag2, <campo>_delta1 y <campo>_delta2. El lag queda en NA cuando la fila desplazada es de otro cliente o cuando la distancia en meses no es exactamente k. (`KF16.R` líneas 315–341)
7. **Tendencia y promedio en ventana de 3.** Llama a TendenciaYmuchomas sobre las mismas columnas numéricas originales con ventana 3 y sólo tendencia y promedio activados: agrega <campo>_tend3 (pendiente de mínimos cuadrados del valor contra la posición en la ventana) y <campo>_avg3. El cálculo por fila lo hace fhistC, una función C++ compilada con Rcpp. Se ejecuta sobre todos los meses cargados, antes de filtrar. (`KF16.R` líneas 343–358; `KF16.R` líneas 108–173; `KF16.R` líneas 177–241)
8. **Filtro de meses y armado de la clase.** Conserva sólo las filas de 202104, 202105, 202106 y 202108. Crea clase01 con 0 para CONTINUA, 1 para BAJA+1 y 2 para BAJA+2. Define como variables del modelo todas las columnas salvo clase_ternaria y clase01, y como base de entrenamiento las filas de los tres meses con clase no nula. (`KF16.R` líneas 360–378)
9. **Matriz de predicción e identificadores de 202108.** Arma la matriz numérica con las filas de 202108 y guarda sus numero_de_cliente en KF16/ids_agosto.csv. (`KF16.R` líneas 380–381)
10. **Entrenamiento por semilla con submuestreo.** Para cada semilla pendiente fija el generador de números al azar, conserva todas las filas BAJA+1 y BAJA+2 y las CONTINUA con sorteo uniforme menor o igual a 0,20, arma el lgb.Dataset y entrena 500 rondas de LightGBM multiclase con esa semilla. (`KF16.R` líneas 385–402)
11. **Predicción y guardado por semilla.** Predice las tres probabilidades para 202108, suma las columnas de BAJA+1 y BAJA+2 y guarda el vector en KF16/semillas/seed_<semilla>.rds, escribiendo primero un archivo .tmp que luego renombra. Registra en el log la semilla, las filas de entrenamiento y el tiempo. (`KF16.R` líneas 404–420)
12. **Promedio de las 60 semillas y corte.** Lee los 60 archivos .rds en una matriz, promedia por fila, ordena de mayor a menor probabilidad promedio y escribe los numero_de_cliente de las primeras 12.000 posiciones en KF16/submits/KA_KF16_60semillas_12000.csv, en una columna sin encabezado. (`KF16.R` líneas 431–441)
13. **Salidas auxiliares y control del archivo.** Escribe prob_agosto_por_semilla.csv con la probabilidad de cada semilla y el promedio por cliente. Vuelve a leer el archivo de envío e imprime su cantidad de filas, la primera línea y el md5. (`KF16.R` líneas 443–455)

## Archivos

- `README.md` · explicacion · Markdown · 30 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/kformoso/README.md.txt) — Presentación de la entrega: indica que la entrega final es KA_KF16_60semillas_12000.csv generada con KF16.R, resume en una tabla el modelo (LightGBM multiclase, ranking por P(BAJA+1)+P(BAJA+2), meses 202104 a 202106, undersampling al 20%, hiperparámetros, 60 semillas, corte de 12.000), enumera las variables construidas y dice cómo correr el script.
- `KF16.R` · principal · R · 455 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/kformoso/KF16.R.txt) — Script único de la entrega: lee el dataset, corrige una variable, calcula lags, deltas, tendencia y promedio de ventana, entrena 60 modelos LightGBM multiclase con submuestreo de CONTINUA y escribe el archivo con los 12.000 clientes de mayor probabilidad promedio para 202108.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### KF16.R

Script único de la entrega: lee el dataset, corrige una variable, calcula lags, deltas, tendencia y promedio de ventana, entrena 60 modelos LightGBM multiclase con submuestreo de CONTINUA y escribe el archivo con los 12.000 clientes de mayor probabilidad promedio para 202108.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Comentario de cabecera. Describe KF16 como la versión KF11 (multiclase,
#   undersampling 0,20, con préstamos personales y sin quitar intrusos) más tendencia y promedio de 3 meses, 60
#   semillas promediadas en un archivo y corte en 12.000 en lugar de 13.000. Cita un backtest de junio de KF11
#   con meseta de ganancia entre 10.816 y 12.263 envíos. KF10, KF11 y ese backtest no están en el repositorio.
# ============================================================
# DM EyF 2026 - Primera Competencia
#
# KF16 = KF11 + feature engineering histórico de la cátedra
#
# KF11 = KF10 sin intrusos: con préstamos personales, sin quitar
#        intrusos, undersampling 0.20, multiclase. Fue mi mejor
#        archivo único (promedio de 50 semillas).
#
# Qué cambia respecto de KF11:
#  - Tendencia y promedio de los últimos 3 meses de cada variable,
#    con la función TendenciaYmuchomas de la cátedra (era el único
#    tip del profe que me faltaba).
#  - 60 semillas (números primos consecutivos desde 100.003),
#    promediadas en UN solo archivo.
#  - Corte 12.000 en vez de 13.000: el backtest de junio de la
#    configuración KF11 (CORTE_KF11) dio la meseta de ganancia entre
#    10.816 y 12.263 envíos, así que 13.000 quedaba afuera.

# ============================================================

# [Anotación · líneas 22–30] Vacía el entorno de R, carga data.table, lightgbm y Rcpp, y sube a 4096 la
#   cantidad de columnas que data.table reserva por tabla.
rm(list = ls(all.names = TRUE))
gc()

library(data.table)
library(lightgbm)
library(Rcpp)

# Más lugar para columnas nuevas (la tendencia agrega ~300)
options(datatable.alloccol = 4096L)


# [Anotación · líneas 33–54] Parámetros de la corrida: archivo competencia_01.csv.gz, experimento KF16,
#   entrenamiento en 202104, 202105 y 202106, predicción en 202108, variable rota ccajas_depositos con el mes
#   202105 forzado, ventana de historia 3, fracción de CONTINUA conservada 0,20, corte 12.000, 60 semillas a
#   partir del primo 100003 y 500 rondas.
# ============================================================
# 1. PARÁMETROS
# ============================================================

ARCHIVO     <- "competencia_01.csv.gz"
EXPERIMENTO <- "KF16"

MESES_TRAIN <- c(202104L, 202105L, 202106L)
MES_ENTREGA <- 202108L

VARIABLES_ROTAS      <- c("ccajas_depositos")
MESES_ROTOS_FORZADOS <- c(202105L)   # lo que dijo el profe

VENTANA_HISTORIA <- 3L   # meses para tendencia y promedio

UNDERSAMPLING <- 0.20    # fracción de CONTINUA que se conserva

CORTE        <- 12000L
N_SEMILLAS   <- 60L
PRIMER_PRIMO <- 100003L

NROUNDS <- 500L

# [Anotación · líneas 56–79] Parámetros del dataset de LightGBM (max_bin 255, feature_pre_filter FALSE) y del
#   modelo: objetivo multiclass con 3 clases, métrica multi_logloss, gbdt, learning_rate 0,027, num_leaves 31,
#   min_data_in_leaf 200, feature_fraction 0,50, sin límite de profundidad, sin regularización L1 ni L2, sin
#   bagging, force_row_wise y deterministic en TRUE.
PARAM_DATASET <- list(
  max_bin            = 255L,
  feature_pre_filter = FALSE
)

PARAM_LGB <- list(
  objective         = "multiclass",
  num_class         = 3L,
  metric            = "multi_logloss",
  boosting          = "gbdt",
  learning_rate     = 0.027,
  num_leaves        = 31L,
  min_data_in_leaf  = 200L,
  feature_fraction  = 0.50,
  max_depth         = -1L,
  lambda_l1         = 0,
  lambda_l2         = 0,
  min_gain_to_split = 0,
  bagging_fraction  = 1,
  bagging_freq      = 0L,
  force_row_wise    = TRUE,
  deterministic     = TRUE,
  verbosity         = -1L
)


# [Anotación · líneas 82–96] Define primos_desde: avanza de a uno desde el número inicial y acumula los
#   enteros que no son divisibles por ningún número entre 2 y la parte entera de su raíz cuadrada, hasta
#   completar la cantidad pedida. SEMILLAS recibe los 60 primos a partir de 100003.
# ============================================================
# 2. SEMILLAS: los N_SEMILLAS primos a partir de PRIMER_PRIMO
# ============================================================

primos_desde <- function(desde, cuantos) {
  out <- integer(0)
  n <- as.integer(desde)
  while (length(out) < cuantos) {
    if (all(n %% 2:floor(sqrt(n)) != 0L)) out <- c(out, n)
    n <- n + 1L
  }
  out
}

SEMILLAS <- primos_desde(PRIMER_PRIMO, N_SEMILLAS)


# [Anotación · líneas 99–136] Compila con Rcpp la función C++ fhistC, que recibe una columna y, para cada
#   fila, la primera fila de su ventana. Por cada fila guarda en el quinto bloque de la salida el valor de la
#   fila anterior (NA si la ventana empieza en la misma fila) y recorre la ventana juntando los valores no nulos
#   con su posición (1, 2, 3...).
# ============================================================
# 3. FEATURE ENGINEERING HISTÓRICO (código de la cátedra)
#
# fhistC: para cada fila, mira las filas del mismo cliente desde
# pdesde hasta la fila actual (sólo pasado y presente, nada del
# futuro) y calcula pendiente, mínimo, máximo, promedio y el valor
# del mes anterior.
# ============================================================

cppFunction("NumericVector fhistC(NumericVector pcolumna, IntegerVector pdesde )
{
  double  x[100] ;
  double  y[100] ;

  int n = pcolumna.size();
  NumericVector out( 5*n );

  for(int i = 0; i < n; i++)
  {
    if( pdesde[i]-1 < i )  out[ i + 4*n ]  =  pcolumna[i-1] ;
    else                   out[ i + 4*n ]  =  NA_REAL ;

    int  libre    = 0 ;
    int  xvalor   = 1 ;

    for( int j= pdesde[i]-1;  j<=i; j++ )
    {
       double a = pcolumna[j] ;

       if( !R_IsNA( a ) )
       {
          y[ libre ]= a ;
          x[ libre ]= xvalor ;
          libre++ ;
       }

       xvalor++ ;
    }

# [Anotación · líneas 138–173] Si la ventana tiene más de un valor no nulo, calcula las sumas necesarias y
#   escribe la pendiente de mínimos cuadrados del valor contra la posición, el mínimo, el máximo y el promedio;
#   si no, escribe NA en los cuatro. Devuelve un vector de largo 5n con los cinco bloques: pendiente, mínimo,
#   máximo, promedio y valor anterior.
    if( libre > 1 )
    {
      double  xsum  = x[0] ;
      double  ysum  = y[0] ;
      double  xysum = xsum * ysum ;
      double  xxsum = xsum * xsum ;
      double  vmin  = y[0] ;
      double  vmax  = y[0] ;

      for( int h=1; h<libre; h++)
      {
        xsum  += x[h] ;
        ysum  += y[h] ;
        xysum += x[h]*y[h] ;
        xxsum += x[h]*x[h] ;

        if( y[h] < vmin )  vmin = y[h] ;
        if( y[h] > vmax )  vmax = y[h] ;
      }

      out[ i ]  =  (libre*xysum - xsum*ysum)/(libre*xxsum -xsum*xsum) ;
      out[ i + n ]    =  vmin ;
      out[ i + 2*n ]  =  vmax ;
      out[ i + 3*n ]  =  ysum / libre ;
    }
    else
    {
      out[ i       ]  =  NA_REAL ;
      out[ i + n   ]  =  NA_REAL ;
      out[ i + 2*n ]  =  NA_REAL ;
      out[ i + 3*n ]  =  NA_REAL ;
    }
  }

  return  out;
}")

# [Anotación · líneas 175–206] Define TendenciaYmuchomas (por defecto ventana 6, con tendencia, mínimo, máximo
#   y promedio en TRUE y los dos cocientes en FALSE). Arma vector_desde, la primera fila de la ventana de cada
#   fila: la fila actual menos ventana más 1, con piso en 1; donde cambia el cliente la ventana arranca en esa
#   fila, y una segunda pasada impide que el inicio retroceda respecto del de la fila anterior. La ventana se
#   cuenta en filas del dataset ordenado por cliente y mes.
# Agrega al dataset (ordenado por cliente y mes) las columnas pedidas
# para cada variable de cols: _tend, _min, _max, _avg, _ratioavg, _ratiomax.
TendenciaYmuchomas <- function(
    dataset, cols, ventana = 6, tendencia = TRUE,
    minimo = TRUE, maximo = TRUE, promedio = TRUE,
    ratioavg = FALSE, ratiomax = FALSE) {
  gc(verbose = FALSE)
  ventana_regresion <- ventana

  last <- nrow(dataset)

  vector_ids <- dataset[, numero_de_cliente]

  # primera fila de la ventana para cada fila
  vector_desde <- seq(
    -ventana_regresion + 2,
    nrow(dataset) - ventana_regresion + 1
  )

  vector_desde[1:ventana_regresion] <- 1

  # la ventana no puede empezar en otro cliente
  for (i in 2:last) {
    if (vector_ids[i - 1] != vector_ids[i]) {
      vector_desde[i] <- i
    }
  }
  for (i in 2:last) {
    if (vector_desde[i] < vector_desde[i - 1]) {
      vector_desde[i] <- vector_desde[i - 1]
    }
  }

# [Anotación · líneas 208–241] Para cada variable de cols llama a fhistC y agrega, según las opciones activas,
#   las columnas <campo>_tend<ventana> (pendiente), _min, _max, _avg, _ratioavg (valor dividido por el promedio
#   de la ventana) y _ratiomax (valor dividido por el máximo de la ventana). El quinto bloque de fhistC (valor
#   de la fila anterior) no se convierte en columna.
  for (campo in cols) {
    nueva_col <- fhistC(dataset[, get(campo)], vector_desde)

    if (tendencia) {
      dataset[, paste0(campo, "_tend", ventana) :=
        nueva_col[(0 * last + 1):(1 * last)]]
    }

    if (minimo) {
      dataset[, paste0(campo, "_min", ventana) :=
        nueva_col[(1 * last + 1):(2 * last)]]
    }

    if (maximo) {
      dataset[, paste0(campo, "_max", ventana) :=
        nueva_col[(2 * last + 1):(3 * last)]]
    }

    if (promedio) {
      dataset[, paste0(campo, "_avg", ventana) :=
        nueva_col[(3 * last + 1):(4 * last)]]
    }

    if (ratioavg) {
      dataset[, paste0(campo, "_ratioavg", ventana) :=
        get(campo) / nueva_col[(3 * last + 1):(4 * last)]]
    }

    if (ratiomax) {
      dataset[, paste0(campo, "_ratiomax", ventana) :=
        get(campo) / nueva_col[(2 * last + 1):(3 * last)]]
    }
  }
}


# [Anotación · líneas 244–271] Crea las carpetas KF16/semillas y KF16/submits y define la ruta del .rds de
#   cada semilla y la de ids_agosto.csv. Arma una lista con meses, variables rotas, ventana, undersampling,
#   rondas y las dos listas de parámetros; si existe KF16/firma.rds con un contenido distinto detiene la
#   ejecución, y si no la guarda.
# ============================================================
# 4. CARPETAS, CONTROL DE PARÁMETROS Y LOG
#
#  KF16/
#    semillas/                 -> probabilidades de cada semilla (.rds)
#    submits/                  -> el archivo para subir al bot
#    prob_agosto_por_semilla.csv
#    parametros.txt, log.txt
# ============================================================

CARPETA_SEM <- file.path(EXPERIMENTO, "semillas")
CARPETA_SUB <- file.path(EXPERIMENTO, "submits")
dir.create(CARPETA_SEM, recursive = TRUE, showWarnings = FALSE)
dir.create(CARPETA_SUB, recursive = TRUE, showWarnings = FALSE)

arch_sem <- function(s) file.path(CARPETA_SEM, sprintf("seed_%d.rds", s))
ARCH_IDS <- file.path(EXPERIMENTO, "ids_agosto.csv")

# "Firma" de los parámetros: si la carpeta tiene semillas entrenadas
# con otros parámetros, se frena para no mezclar corridas distintas.
ARCH_FIRMA <- file.path(EXPERIMENTO, "firma.rds")
FIRMA <- list(MESES_TRAIN, MES_ENTREGA, VARIABLES_ROTAS, MESES_ROTOS_FORZADOS,
              VENTANA_HISTORIA, UNDERSAMPLING, NROUNDS, PARAM_DATASET, PARAM_LGB)
if (file.exists(ARCH_FIRMA) && !identical(readRDS(ARCH_FIRMA), FIRMA)) {
  stop("\n", EXPERIMENTO, " tiene semillas entrenadas con otros parametros. ",
       "Cambia EXPERIMENTO o borra la carpeta.")
}
saveRDS(FIRMA, ARCH_FIRMA)

# [Anotación · líneas 273–290] Cierra las redirecciones de consola abiertas y envía la salida a KF16/log.txt
#   (agregando al final y mostrando también en pantalla). Escribe KF16/parametros.txt con los parámetros, las
#   semillas y sessionInfo(). Calcula qué semillas no tienen todavía su archivo .rds e imprime cuántas faltan.
while (sink.number() > 0) sink()
sink(file.path(EXPERIMENTO, "log.txt"), split = TRUE, append = TRUE)

cat("\n========================================\n")
cat(EXPERIMENTO, "- inicio:", format(Sys.time()), "\n")
cat("========================================\n")

writeLines(capture.output(print(list(
  EXPERIMENTO = EXPERIMENTO, MESES_TRAIN = MESES_TRAIN, MES_ENTREGA = MES_ENTREGA,
  VARIABLES_ROTAS = VARIABLES_ROTAS, MESES_ROTOS_FORZADOS = MESES_ROTOS_FORZADOS,
  VENTANA_HISTORIA = VENTANA_HISTORIA, UNDERSAMPLING = UNDERSAMPLING, CORTE = CORTE,
  SEMILLAS = SEMILLAS, NROUNDS = NROUNDS,
  PARAM_DATASET = PARAM_DATASET, PARAM_LGB = PARAM_LGB,
  sesion = sessionInfo()
))), file.path(EXPERIMENTO, "parametros.txt"))

faltan <- SEMILLAS[!file.exists(vapply(SEMILLAS, arch_sem, ""))]
cat("Semillas:", length(SEMILLAS), "| faltan entrenar:", length(faltan), "\n")


# [Anotación · líneas 293–313] El bloque que sigue se ejecuta sólo si falta alguna semilla o no existe
#   ids_agosto.csv. Verifica que el archivo de datos exista y lo lee con fread. Para ccajas_depositos busca los
#   meses donde todos sus valores no nulos son cero, les une el mes 202105 y pone la variable en NA en esos
#   meses.
# ============================================================
# 5. DATOS, VARIABLES Y ENTRENAMIENTO (sólo si falta algo)
# ============================================================

if (length(faltan) > 0 || !file.exists(ARCH_IDS)) {

  if (!file.exists(ARCHIVO)) stop("\nNo encuentro ", ARCHIVO, "\nCarpeta actual: ", getwd())

  dataset <- fread(ARCHIVO)
  cat("\nFilas:", nrow(dataset), " Columnas:", ncol(dataset), "\n")

  # --- 5a. Data quality: variable rota -> NA (antes de los lags) ---
  for (v in intersect(VARIABLES_ROTAS, names(dataset))) {
    meses_todo_cero <- dataset[
      , .(todo_cero = all(.SD[[1]] == 0, na.rm = TRUE)),
      by = foto_mes, .SDcols = v
    ][todo_cero == TRUE, foto_mes]
    meses_rotos <- sort(unique(c(MESES_ROTOS_FORZADOS, meses_todo_cero)))
    dataset[foto_mes %in% meses_rotos, (v) := NA]
    cat(v, "-> NA en:", paste(meses_rotos, collapse = ", "), "\n")
  }

# [Anotación · líneas 315–341] Ordena por cliente y mes y calcula un índice de mes (año por 12 más mes). Toma
#   todas las columnas numéricas salvo numero_de_cliente y foto_mes y, para k = 1 y k = 2, crea el lag k con
#   shift y el delta k (valor menos lag). El lag se pone en NA en las filas donde la fila k posiciones atrás es
#   de otro cliente o donde la diferencia de índice de mes no es k.
  # --- 5b. Lags y deltas de orden 1 y 2, invalidando huecos de meses ---
  setorder(dataset, numero_de_cliente, foto_mes)
  periodo <- (dataset$foto_mes %/% 100L) * 12L + dataset$foto_mes %% 100L

  campos_lag <- setdiff(
    names(dataset)[vapply(dataset, is.numeric, logical(1))],
    c("numero_de_cliente", "foto_mes")
  )

  for (k in 1:2) {
    cli_prev <- shift(dataset$numero_de_cliente, k)
    per_prev <- shift(periodo, k)
    invalidas <- which(
      is.na(cli_prev) |
        cli_prev != dataset$numero_de_cliente |
        (periodo - per_prev) != k
    )
    for (campo in campos_lag) {
      x  <- dataset[[campo]]
      xl <- shift(x, k)
      xl[invalidas] <- NA
      set(dataset, j = paste0(campo, "_lag", k),   value = xl)
      set(dataset, j = paste0(campo, "_delta", k), value = x - xl)
    }
  }
  rm(periodo, cli_prev, per_prev, invalidas, x, xl)
  gc()

# [Anotación · líneas 343–362] Llama a TendenciaYmuchomas sobre las mismas columnas numéricas originales con
#   ventana 3, tendencia y promedio en TRUE y el resto en FALSE: agrega <campo>_tend3 y <campo>_avg3. Lo hace
#   con todos los meses cargados y después conserva sólo las filas de 202104, 202105, 202106 y 202108.
  # --- 5c. Tendencia y promedio de los últimos 3 meses (lo nuevo de KF16) ---
  # Se calcula con todos los meses cargados, antes de filtrar,
  # para que agosto tenga su historia (junio, julio, agosto).
  TendenciaYmuchomas(dataset,
    cols      = campos_lag,
    ventana   = VENTANA_HISTORIA,
    tendencia = TRUE,
    minimo    = FALSE,
    maximo    = FALSE,
    promedio  = TRUE,
    ratioavg  = FALSE,
    ratiomax  = FALSE
  )
  gc()

  cat("Columnas con lags, deltas, tendencia y promedio:", ncol(dataset), "\n")

  # --- 5d. Sólo los meses que se usan (ahorra memoria) ---
  dataset <- dataset[foto_mes %in% c(MESES_TRAIN, MES_ENTREGA)]
  gc()

# [Anotación · líneas 364–381] Crea clase01 (0 = CONTINUA, 1 = BAJA+1, 2 = BAJA+2, NA en otro caso) e imprime
#   la cantidad de filas por mes y clase. Las variables del modelo son todas las columnas salvo clase_ternaria y
#   clase01, por lo que numero_de_cliente y foto_mes quedan incluidas. Define las filas base de entrenamiento
#   (tres meses, clase no nula), arma la matriz de 202108 y guarda sus numero_de_cliente en KF16/ids_agosto.csv.
  # --- 5e. Clase multiclase: 0 = CONTINUA, 1 = BAJA+1, 2 = BAJA+2 ---
  dataset[, clase01 := fcase(
    clase_ternaria == "CONTINUA", 0L,
    clase_ternaria == "BAJA+1",   1L,
    clase_ternaria == "BAJA+2",   2L,
    default = NA_integer_
  )]

  print(dataset[, .N, by = .(foto_mes, clase_ternaria)][order(foto_mes, clase_ternaria)])

  campos_modelo <- setdiff(names(dataset), c("clase_ternaria", "clase01"))
  cat("\nVariables del modelo:", length(campos_modelo), "\n")

  idx_base   <- dataset[foto_mes %in% MESES_TRAIN & !is.na(clase01), which = TRUE]
  clase_base <- dataset$clase01[idx_base]

  X_pred <- data.matrix(dataset[foto_mes == MES_ENTREGA, ..campos_modelo])
  fwrite(data.table(numero_de_cliente = dataset[foto_mes == MES_ENTREGA, numero_de_cliente]), ARCH_IDS, scipen = 50L)

# [Anotación · líneas 383–402] Para cada semilla pendiente: fija set.seed con el generador L'Ecuyer-CMRG,
#   conserva todas las filas con clase 1 o 2 y las de clase 0 cuyo número uniforme es menor o igual a 0,20,
#   construye el lgb.Dataset con esas filas, copia los parámetros agregando seed igual a la semilla y entrena
#   500 rondas con lgb.train, sin conjunto de validación.
  # --- 5f. Semillerío: un modelo por semilla, cada uno con su
  #         undersampling de CONTINUA (se conservan todas las bajas) ---
  for (s in faltan) {

    t0 <- Sys.time()
    set.seed(s, kind = "L'Ecuyer-CMRG")

    conservar <- clase_base > 0L | runif(length(idx_base)) <= UNDERSAMPLING
    idx <- idx_base[conservar]

    dtrain <- lgb.Dataset(
      data   = data.matrix(dataset[idx, ..campos_modelo]),
      label  = dataset$clase01[idx],
      params = PARAM_DATASET
    )

    param      <- PARAM_LGB
    param$seed <- s

    modelo <- lgb.train(params = param, data = dtrain, nrounds = NROUNDS)

# [Anotación · líneas 404–424] Predice sobre la matriz de 202108; si la salida es un vector la reordena en una
#   matriz de 3 columnas. Guarda la suma de las columnas 2 y 3, es decir P(BAJA+1) + P(BAJA+2), en un archivo
#   .tmp que luego renombra a seed_<semilla>.rds. Imprime semilla, filas de entrenamiento, segundos y hora, y
#   libera memoria. Al terminar el ciclo borra el dataset y la matriz de predicción.
    # P(BAJA+1) + P(BAJA+2); lightgbm 3.x devuelve vector, 4.x matriz
    pr <- predict(modelo, X_pred)
    if (is.null(dim(pr))) pr <- matrix(pr, ncol = 3L, byrow = TRUE)

    # se guarda primero en .tmp y se renombra: si se corta a mitad
    # de la escritura no queda un archivo roto
    tmp <- paste0(arch_sem(s), ".tmp")
    saveRDS(pr[, 2] + pr[, 3], tmp)
    file.rename(tmp, arch_sem(s))

    cat(sprintf("  semilla %d | filas train %d | %.0f s | %s\n",
                s, length(idx), as.numeric(difftime(Sys.time(), t0, units = "secs")),
                format(Sys.time(), "%d/%m %H:%M")))

    rm(dtrain, modelo, pr)
    gc(verbose = FALSE)
  }

  rm(dataset, X_pred)
  gc()
}


# [Anotación · líneas 427–441] Lee los identificadores de 202108 y los .rds de las 60 semillas en una matriz
#   con una columna por semilla, promedia por fila y asigna un ranking de mayor a menor probabilidad promedio
#   con empates por orden de aparición. Escribe los numero_de_cliente con ranking hasta 12.000 en
#   KF16/submits/KA_KF16_60semillas_12000.csv, en una columna y sin encabezado.
# ============================================================
# 6. SUBMIT: promedio de las 60 semillas en UN archivo
# ============================================================

ids_agosto <- fread(ARCH_IDS)$numero_de_cliente

P <- sapply(SEMILLAS, function(s) readRDS(arch_sem(s)))
colnames(P) <- as.character(SEMILLAS)

prob <- rowMeans(P)
rk   <- frank(-prob, ties.method = "first")

# Una sola columna y SIN encabezado (el bot rechaza "numero_de_cliente")
archivo <- file.path(CARPETA_SUB, sprintf("KA_%s_%dsemillas_%d.csv", EXPERIMENTO, length(SEMILLAS), CORTE))
fwrite(data.table(ids_agosto[rk <= CORTE]), archivo, col.names = FALSE, scipen = 50L)

# [Anotación · líneas 443–455] Escribe KF16/prob_agosto_por_semilla.csv con numero_de_cliente, una columna
#   seed_<semilla> por cada semilla y prob_promedio. Vuelve a leer el archivo de envío e imprime su cantidad de
#   filas, su primera línea y su md5; imprime la hora de fin y cierra el log.
# Probabilidades por semilla y promedio: sirven para rearmar el
# submit con otro corte sin reentrenar.
out <- data.table(numero_de_cliente = ids_agosto)
for (s in colnames(P)) set(out, j = paste0("seed_", s), value = P[, s])
out[, prob_promedio := prob]
fwrite(out, file.path(EXPERIMENTO, "prob_agosto_por_semilla.csv"))

l <- readLines(archivo)
cat("\nCreado:", archivo, "|", length(l), "filas | primera:", l[1], "\n")
cat("md5:", tools::md5sum(archivo), "\n")

cat("\nFin:", format(Sys.time()), "\n")
sink()
```


## Explicaciones del alumno (texto original)

### README.md

> # DM EyF 2026 – Primera Competencia · Karina Formoso
>
> Predicción de churn (`BAJA+2`) para **202108** con LightGBM en R.
>
> **Entrega final:** `KA_KF16_60semillas_12000.csv`, generada con `KF16.R`.
>
> ## Modelo
>
> | Item | Valor |
> |---|---|
> | Algoritmo | LightGBM multiclase (CONTINUA / BAJA+1 / BAJA+2) |
> | Ranking | P(BAJA+1) + P(BAJA+2) |
> | Meses de entrenamiento | 202104, 202105, 202106 |
> | Mes a predecir | 202108 |
> | Undersampling | se conserva el 20% de CONTINUA |
> | Hiperparámetros | learning_rate 0.027 · num_leaves 31 · min_data_in_leaf 200 · feature_fraction 0.5 · max_bin 255 · 500 rondas |
> | Semillerío | 60 semillas (primos consecutivos desde 100003); se promedian las probabilidades |
> | Corte | 12000 envíos |
>
> ## Feature engineering
>
> - `ccajas_depositos` en NA en 202105 (variable rota).
> - Lags y deltas de orden 1 y 2.
> - Tendencia y promedio de los últimos 3 meses (`TendenciaYmuchomas`, código de la cátedra).
> - Con préstamos personales, sin quitar intrusos.
>
> ## Archivos
>
> - `KF16.R`: script completo; con `competencia_01.csv.gz` en la misma carpeta, se corre con `source("KF16.R")`.
> - `KA_KF16_60semillas_12000.csv`: archivo entregado.

