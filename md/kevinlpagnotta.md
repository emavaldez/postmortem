# kevinlpagnotta — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: kevinlpagnotta
- Repositorio: https://github.com/kevinlpagnotta/DMEyF---Primera-Competencia
- Link posteado: https://github.com/kevinlpagnotta/DMEyF---Primera-Competencia
- Commit: 391d0f979f71c4beca9198f9e2d8fd88c9c24f62
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/kevinlpagnotta/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/kevinlpagnotta.json

## Resumen

Entrega del repositorio kevinlpagnotta/DMEyF---Primera-Competencia para la Primera Competencia DMEyF 2026: un notebook en R (FV8.ipynb, con una función en C++ vía Rcpp), BO_log.txt y README.md. El camino que produce la predicción de 202108 arma la clase ternaria desde el dataset crudo, calcula percentiles por mes, lags, deltas, acumulados, tendencia y promedio de 3 meses, y selecciona variables con dos rondas de canaritos LightGBM por Gain. Después agrega interacciones entre variables, toma las 5 recetas de mayor métrica de BO_log.txt, hace una limpieza cruzada A/B de 202103 a 202106 con modelos de 20 semillas y submuestreo de CONTINUA al 10 %, y promedia 5 modelos LightGBM entrenados sin submuestreo. La salida son 15 archivos con los 8.000 a 15.000 clientes de mayor probabilidad, cada 500. La prueba sobre 202106 está desactivada en el código.

**Qué entrega.** Un conjunto de 15 archivos CSV, HT4960-FV8_08000.csv a HT4960-FV8_15000.csv (cada 500 clientes), con una sola columna numero_de_cliente sin encabezado. Los clientes de 202108 van ordenados por la probabilidad del modelo sobre la clase binaria clase01 (BAJA+1 o BAJA+2); según el README, el objetivo declarado es BAJA+2. Los archivos se escriben en exp/HT4960-FV8/entregas/ y el repositorio no trae ninguno de ellos.

**Cómo se ejecuta.** Según el README: en una VM con 256 GB de RAM y 12 vCPU (tipo n2-custom-12-262144-ext, aprovisionamiento Standard), con kernel de Jupyter ir, desde ~/buckets/b1/datasets se lanza con nohup el comando jupyter nbconvert --to notebook --execute FV8.ipynb --output FV8_ejecutada.ipynb --ExecutePreprocessor.timeout=-1 --ExecutePreprocessor.kernel_name=ir, seguido de sudo shutdown -h now. Requiere ~/buckets/b1/datasets/competencia_01_crudo.csv y BO_log.txt de HT4960-FV4 (obligatorio); los tres CSV de la carpeta Opcional/ son opcionales y, si se copian a exp/HT4960-FV8/, el notebook los reutiliza. Si la VM se corta, se relanza el mismo comando y retoma desde los checkpoints.

## Ficha

- **Lenguajes:** R, C++
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: clase01 = 1 si clase_ternaria es BAJA+1 o BAJA+2, y 0 si es CONTINUA (línea 640). La clase_ternaria de tres valores se arma en la celda 3 (líneas 47 a 58) a partir de periodo_ultimo y periodo_anteultimo del dataset crudo.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202103, 202104
- **Mes que predice:** 202108
- **Submuestreo:** Submuestreo de CONTINUA al 10 % (PARAM$undersampling30 = 0.10, línea 136) en el modelo30 de la limpieza cruzada (línea 985): entrena con todas las bajas y con las CONTINUA cuyo número aleatorio es menor o igual a 0,10. El mismo submuestreo aparece en la limpieza previa de la bayesiana (línea 861), que no se ejecuta en esta entrega. El ensamble final (líneas 1102 a 1106) se entrena sobre las filas con aporta_final igual a 1, sin submuestreo.
- **Calidad de datos:** Elimina cprestamos_personales y mprestamos_personales (línea 375). En 202105 pasa a NA los valores 0 de ccajas_depositos (líneas 377 y 378). Verifica que todas las originales sean numéricas y que las 12 excepciones existan (líneas 381 a 385). Limpieza cruzada A/B sobre 202103 a 202106 (líneas 970 a 1001): cada mitad se evalúa con un modelo30 de 20 semillas entrenado con la otra mitad; se descartan las CONTINUA con probabilidad promedio mayor a 0,5 (PARAM$umbral_prob30, línea 137) y las bajas se conservan siempre (línea 999).
- **Drifting:** Percentil por foto_mes de las originales menos las 12 excepciones (líneas 388 y 408 a 410). Dentro de cada mes, 0 queda en 0; los positivos reciben su rango dividido por la cantidad de positivos, quedando en (0, 1]; los negativos reciben el rango de su valor absoluto con signo negativo, quedando en [-1, 0) (líneas 397 a 405). Las 12 excepciones quedan en crudo. No se observa en el código deflación por IPC, dólar o UVA, ni estandarización por mes.
- **Variables dentro del mes:** Ronda 1 (líneas 654 a 656): para cada par de originales, tres columnas A__x__B, A__div__B y B__div__A; según el README, unas 150 originales y unas 33.500 columnas. Ronda 2 (líneas 774 a 794): 20 ejes y candidatos, con e__X2__c, e__DIV2__c y c__DIV2__e sin repetir pares; según el README, 21.870 columnas nuevas. La función valor_col (líneas 273 a 284) multiplica en __x__ y __X2__, y divide en __div__ y __DIV2__ con safe_div (líneas 230 a 234), que pone 0 donde el divisor es 0. En el canarito 1 las interacciones se calculan sólo para 202104; las de campos_finales se calculan para todas las filas (líneas 823 a 827).
- **Variables históricas:** Sobre los percentiles y las 12 excepciones (línea 424): lag1, lag2 y lag3 del mismo cliente, en NA si el mes no es consecutivo (líneas 431 a 446); delta1 = x - lag1, delta2 = lag1 - lag2 y delta3 = lag2 - lag3 (líneas 452 a 454); acum = x menos el valor del primer mes del cliente (líneas 447 y 455). Script del docente (líneas 616 a 627): _tend3, pendiente por cuadrados mínimos sobre una ventana de hasta 3 meses del mismo cliente, y _avg3, promedio de esa ventana. Los mínimos, máximos y ratios de ventana están desactivados (líneas 622 a 623 y 625 a 626).
- **Selección de variables:** Canarito 1 (líneas 675 a 756, llamada en la línea 763): juzga las variables base sin las forzadas más la RONDA1; agrega canaritos uniformes en número ceil(0,20 por cantidad de variables) (líneas 682 y 311); el juez es un LightGBM con la receta de mayor metrica de BO_log.txt, entrenado con 202104 completo y sin submuestreo (líneas 358 a 361 y 701 a 702); una semilla (PARAM$juez_semillas = 1, línea 128); importancia por Gain (líneas 720 a 727); corte en la media más dos desvíos de los puestos de los canaritos, y sobreviven las variables reales con puesto menor que el corte (líneas 745 a 746). Ronda 2 (líneas 775 a 797): ejes, las 20 primeras sobrevivientes. Canarito 2 (línea 805): juzga las sobrevivientes del canarito 1, las _tend3 y _avg3 y la ronda 2. campos_finales (líneas 812 y 813) son numero_de_cliente, foto_mes, las _lag2, _lag3, _delta2 y _delta3 (regex de la línea 131, siempre incluidas) y las sobrevivientes del canarito 2. Según Opcional/campos_finales.csv del repositorio, la lista tiene 5.199 variables: 788 base (incluye numero_de_cliente, foto_mes y las 600 _lag2, _lag3, _delta2 y _delta3), 1.901 de ronda 1, 2.462 de ronda 2 y 48 _tend3 o _avg3; ningún canarito.
- **Optimización de hiperparámetros:** Optimización bayesiana con mlr3mbo (bayesopt_ego, línea 925; función de adquisición EI, línea 928; sustituto regr.km de DiceKriging con optimizador BFGS, línea 926; búsqueda aleatoria de 1.000 puntos por iteración, línea 930). Espacio: num_iterations de 64 a 4.096, num_leaves de 16 a 2.048 y min_sum_hessian_in_leaf de 1e-06 a 0,1 (líneas 210 a 214). Termina con 50 evaluaciones (PARAM$bo_iteraciones, líneas 140 y 922). Cada evaluación promedia el AUC de 5 semillas, entrenando con el fold 1 y las filas aporta igual a 1, y evaluando sobre el fold 2 (líneas 882 a 907). En esta entrega BO_log.txt ya tiene 50 filas, así que la celda 32 no entrena nuevas evaluaciones (líneas 841 a 843 y 946 a 948).
- **Hiperparámetros finales:** Cinco recetas: las filas de mayor metrica de BO_log.txt, sin combinaciones repetidas (líneas 952 a 958). Según BO_log.txt, (num_iterations, num_leaves, min_sum_hessian_in_leaf) y metrica son: (3337, 1855, 0,054840) 0,934156; (3904, 1495, 0,083680) 0,934142; (3226, 623, 0,042796) 0,934139; (3153, 641, 0,017217) 0,934137; (3136, 336, 0,017597) 0,934135. El resto son los parámetros fijos de las líneas 161 a 201: boosting gbdt, objective binary, metric auc, learning_rate 0,005, feature_fraction 0,50, max_bin 31, min_data_in_leaf 0, lambda_l1 y lambda_l2 en 0, drop_rate 0,1, max_drop 50, skip_drop 0,5 y deterministic TRUE. El modelo30 de la limpieza usa num_iterations 2180, num_leaves 30 y min_sum_hessian_in_leaf 0,1141634103 (líneas 204 a 208).
- **Semillas:** PARAM$semilla_primigenia = 379531 (línea 105). Pool: con set.seed(379531, L'Ecuyer-CMRG) se toman las primeras 100 semillas únicas de c(379531, sample(100000:999999, 200)) (líneas 156 y 157). Usos: el juez de los canaritos usa la semilla primigenia más 10 por etapa para las columnas uniformes (líneas 699 y 713, esta última más 1 para el control) y PARAM$semillas[1] para el modelo (línea 684); la bayesiana usa PARAM$semillas[1:5] (línea 896), que la columna seed de BO_log.txt registra como 379531, 130215, 201028, 676718 y 209925; la limpieza cruzada usa 20 semillas por mitad (línea 974); el ensamble final usa una semilla por receta, PARAM$semillas[1] a [5] (línea 1018), las mismas cinco. La partición 70/30 usa la primigenia (línea 642) y la limpieza cruzada la primigenia más 1 (línea 972).
- **Cantidad de semillas:** 5
- **Ensamble:** Promedio simple de las probabilidades de 5 modelos LightGBM, uno por receta y una semilla por receta (PARAM$semillas_por_receta = 1, línea 146), entrenados con las filas de 202103 a 202106 que tienen aporta_final igual a 1 (líneas 1102 y 1106) y predichos sobre 202108 (líneas 1011 a 1025: la suma se divide por n_mod). La limpieza cruzada promedia 20 modelos modelo30 por mitad (líneas 981 a 993). La prueba de un ensamble entrenado con 202103 y 202104 y predicho sobre 202106 (líneas 1033 a 1056) está desactivada.
- **Corte:** Se ordenan los clientes de 202108 de mayor a menor probabilidad (línea 1110) y se escriben 15 archivos con los primeros n clientes, con n igual a 8.000, 8.500, ..., 15.000 (PARAM$cortes, línea 151; líneas 1122 a 1124). No hay umbral de probabilidad ni corte por ganancia. La ganancia de la prueba (líneas 1058 a 1065) sólo se calcula si PARAM$hacer_prueba es TRUE, y está en FALSE (línea 145).
- **Validación:** Según el código de la celda 32, la métrica de BO_log.txt es el AUC promedio de 5 semillas sobre el fold 2 (30 %) de 202103 y 202104 (líneas 882 a 887 y 896 a 907). Ese fold sale de una partición aleatoria estratificada por clase_ternaria de esos dos meses (líneas 642 a 647). En el juez de los canaritos, el AUC de control se calcula sobre una muestra de 202106 con todas las bajas y hasta 50.000 filas en total (líneas 707 a 712); se registra y no interviene en el corte (líneas 731 a 733). La prueba sobre 202106 (líneas 1033 a 1077) está desactivada con PARAM$hacer_prueba = FALSE (línea 145). El modelo final se entrena con 202103 a 202106, que incluye los meses usados para validar.
- **Salidas:** 15 archivos entregas/HT4960-FV8_08000.csv a HT4960-FV8_15000.csv, con una columna numero_de_cliente sin encabezado, verificados al escribir: n líneas, todas numéricas y sin duplicados (líneas 1120 a 1129). Intermedios en exp/HT4960-FV8/: prediccion_202108.csv con numero_de_cliente y prob (líneas 1108 a 1112); recetas.csv (línea 959); campos_finales.csv (línea 813); filtro_canaritos_etapa1.csv y filtro_canaritos_etapa2.csv (líneas 678 y 747); checkpoints/ con aporta*.csv.gz (líneas 876, 1043 y 1093); y log_FV8.txt (líneas 226 y 227). La carpeta Opcional/ del repositorio trae campos_finales.csv (5.199 variables), filtro_canaritos_etapa1.csv (40.950 filas de datos) y filtro_canaritos_etapa2.csv (31.311 filas de datos).

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README: VM de tipo n2-custom-12-262144-ext (12 vCPU, 256 GB de RAM, aprovisionamiento Standard) con disco de arranque de 256 GB; R con kernel de Jupyter ir; Rcpp necesita compilador C++; los paquetes se instalan solos si faltan, sin versiones declaradas; con 96 GB de RAM la etapa de canaritos se queda sin memoria (pico de unos 117 GB). El código usa todos los núcleos: setDTthreads(0) (línea 94) y num_threads = parallel::detectCores() (línea 153).

## Pasos del camino de la entrega

1. **Clase ternaria desde el dataset crudo.** Lee competencia_01_crudo.csv (línea 35) y calcula el periodo en meses de cada registro (línea 40). Asigna CONTINUA a los registros anteriores al penúltimo mes del dataset (línea 50), BAJA+1 si el cliente no tiene registro del mes siguiente (líneas 52 a 54) y BAJA+2 si tiene el mes siguiente pero no el subsiguiente (líneas 56 a 58). Guarda competencia_01.csv.gz (líneas 63 a 66). (`FV8.ipynb` líneas 33–68)
2. **Parámetros y LightGBM fijo.** Define en PARAM el experimento HT4960-FV8, la semilla primigenia 379531, los meses de entrenamiento final 202103 a 202106 y de predicción 202108, las 12 excepciones que quedan en crudo, el 20 % de canaritos, 20 ejes para la ronda 2, 20 semillas para la limpieza, 5 recetas, 50 iteraciones de la bayesiana y los cortes de 8.000 a 15.000 cada 500 (líneas 101 a 157). Fija los parámetros de LightGBM (líneas 161 a 201), los del modelo30 (líneas 204 a 208) y el rango de la bayesiana (líneas 210 a 214). (`FV8.ipynb` líneas 101–157; `FV8.ipynb` líneas 161–214)
3. **Carpeta de trabajo y receta del juez.** Crea exp/HT4960-FV8 en ~/buckets/b1 con las subcarpetas entregas y checkpoints (líneas 343 a 347). Si falta, copia BO_log.txt desde HT4960-FV4 (líneas 351 a 356). Toma la fila de mayor metrica de BO_log.txt como receta del juez de los canaritos, con force_col_wise (líneas 357 a 363). (`FV8.ipynb` líneas 342–366)
4. **Lectura y correcciones.** Lee competencia_01.csv.gz (líneas 373 y 374), elimina cprestamos_personales y mprestamos_personales (línea 375), pasa a NA los ceros de ccajas_depositos en 202105 (líneas 377 a 379) y verifica que las originales sean numéricas y que las 12 excepciones existan (líneas 381 a 390). (`FV8.ipynb` líneas 372–390)
5. **Percentil por mes.** Para cada original que no es excepción crea la columna _pct dentro de cada foto_mes (línea 409). Los ceros quedan en 0; los positivos se reemplazan por su rango dividido por la cantidad de positivos, en (0, 1]; los negativos, por el rango de su valor absoluto con signo negativo, en [-1, 0) (líneas 397 a 405). Las 12 excepciones no se transforman (línea 388). (`FV8.ipynb` líneas 396–417)
6. **Lags, deltas y acumulado.** Sobre los percentiles y las 12 excepciones (línea 424) calcula lag1 a lag3 del mismo cliente, en NA si el mes no es consecutivo (líneas 431 a 446); delta1 = x - lag1, delta2 = lag1 - lag2, delta3 = lag2 - lag3 y acum = x menos el valor del primer mes del cliente (líneas 447 a 455). (`FV8.ipynb` líneas 423–461)
7. **Tendencia y promedio de 3 meses (script del docente).** Usa fhistC, función en C++ vía Rcpp, y TendenciaYmuchomas para calcular la pendiente por cuadrados mínimos (_tend3) y el promedio (_avg3) de una ventana de hasta 3 meses del mismo cliente, sobre las mismas variables de los lags (líneas 616 a 627). Los mínimos, máximos y ratios quedan desactivados (líneas 622 a 626). (`FV8.ipynb` líneas 470–540; `FV8.ipynb` líneas 616–628)
8. **Preparación: clase binaria, fold y grupos de variables.** Quita 202107 del dataset, que sólo aporta historia para 202108 (líneas 636 y 637). Crea clase01 = 1 para BAJA+1 o BAJA+2 (línea 640). Asigna fold 1 (70 %) y fold 2 (30 %) sobre 202103 y 202104, estratificado por clase_ternaria (líneas 642 a 647). Separa las forzadas _lag2, _lag3, _delta2 y _delta3 de las variables juzgables (líneas 650 a 652) y arma RONDA1 con todas las combinaciones de pares de originales (líneas 654 a 656). (`FV8.ipynb` líneas 636–656)
9. **Canarito 1 sobre 202104.** Para las juzgables y RONDA1 arma en 202104 una matriz con canaritos uniformes en 20 % de las columnas (líneas 682, 683 y 699 y 700). Entrena el juez con la receta de mayor metrica, con 202104 completo y sin submuestreo (líneas 701 y 702 y 716 a 718), y calcula la importancia por Gain (líneas 719 a 727). Promedia el puesto de cada variable y corta en la media más dos desvíos de los puestos de los canaritos (líneas 741 a 746). Registra el AUC de control en 202106 (líneas 707 a 712 y 731 a 733). Se ejecuta con correr_canarito(1) (línea 763). (`FV8.ipynb` líneas 675–766)
10. **Ronda 2 de interacciones.** Toma las 20 primeras sobrevivientes del canarito 1 como ejes (línea 775). Los candidatos son las sobrevivientes que no son interacciones de ronda 1 ni originales, más los ejes (líneas 776 y 777). Para cada eje y cada candidato genera e__X2__c, e__DIV2__c y c__DIV2__e, sin repetir pares y sin pares de dos originales (líneas 779 a 794). Según el README son 21.870 columnas nuevas. (`FV8.ipynb` líneas 774–798)
11. **Canarito 2 y campos_finales.** Juzga con el mismo procedimiento las sobrevivientes del canarito 1, las variables _tend3 y _avg3 y la ronda 2 (línea 805). campos_finales son numero_de_cliente, foto_mes, las forzadas y las sobrevivientes del canarito 2 (líneas 808 a 814). (`FV8.ipynb` líneas 804–817)
12. **Interacciones finales en todas las filas.** Calcula en todas las filas las interacciones de campos_finales a partir de su nombre (líneas 824 a 828) y elimina del dataset las columnas que no están en campos_finales (líneas 831 y 832). (`FV8.ipynb` líneas 823–834)
13. **Recetas desde BO_log.txt.** Cuenta las filas de BO_log.txt (línea 841). Como son 50, igual que PARAM$bo_iteraciones, no corre la bayesiana (líneas 842, 843 y 946 a 948). Toma las cinco filas de mayor métrica sin combinaciones repetidas (líneas 952 a 958) y las guarda en recetas.csv (línea 959). (`FV8.ipynb` líneas 841–843; `FV8.ipynb` líneas 946–948; `FV8.ipynb` líneas 951–960)
14. **Limpieza cruzada A/B de 202103 a 202106.** Parte las filas de los cuatro meses en dos mitades estratificadas por clase_ternaria (línea 972; líneas 254 a 263). Para cada mitad entrena 20 modelos modelo30 con la otra mitad, con todas las bajas y 10 % de las CONTINUA, y promedia sus probabilidades (líneas 976 a 996). Marca aporta igual a 1 para las bajas y para las CONTINUA con probabilidad menor o igual a 0,5 (línea 999). En el modelo final se ejecuta sobre 202103 a 202106 (línea 1091). (`FV8.ipynb` líneas 254–263; `FV8.ipynb` líneas 970–1001; `FV8.ipynb` líneas 1084–1096)
15. **Ensamble de 5 recetas y predicción de 202108.** Entrena un LightGBM por receta, con una semilla por receta (PARAM$semillas[1] a [5]), sobre las filas de 202103 a 202106 con aporta_final igual a 1 y sin submuestreo (líneas 1003 a 1020 y 1102 y 1106). Promedia las probabilidades de los 5 modelos y predice 202108 (líneas 1025 y 1106). Ordena por probabilidad de mayor a menor y guarda prediccion_202108.csv (líneas 1108 a 1112). (`FV8.ipynb` líneas 1003–1026; `FV8.ipynb` líneas 1098–1113)
16. **Archivos de entrega.** Escribe 15 archivos HT4960-FV8_NNNNN.csv con los primeros n clientes de la lista ordenada, con n de 8.000 a 15.000 cada 500, sin encabezado (líneas 1120 a 1124). Cada archivo se vuelve a leer y se verifica que tenga n líneas numéricas sin duplicados; si no cumple, detiene la ejecución (líneas 1126 a 1129). (`FV8.ipynb` líneas 1120–1131)

## Archivos

- `FV8.ipynb` · principal · Jupyter (R) · 1131 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/kevinlpagnotta/FV8.ipynb.txt) — Notebook en R que contiene el camino completo de la predicción: clase ternaria, percentiles, lags, canaritos, interacciones, recetas, limpieza cruzada, ensamble y los 15 archivos de entrega. Las celdas de texto y de código aparecen como líneas marcadas con #%% celda N.
- `BO_log.txt` · configuracion · Texto · 51 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/kevinlpagnotta/BO_log.txt.txt) — Tabla de 50 evaluaciones de la optimización bayesiana, una fila por iteración, con los hiperparámetros de LightGBM, las 5 semillas unidas por guion bajo, la métrica (AUC promedio de 5 semillas) y el número de iteración. El notebook lee sus filas para elegir el juez de los canaritos (línea 357) y las 5 recetas del ensamble (línea 952).
- `README.md` · explicacion · Markdown · 72 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/kevinlpagnotta/README.md.txt) — Presenta la entrega: qué predice, la VM requerida, los archivos que deben estar en su lugar, el comando de ejecución con nbconvert, la carpeta Opcional y un pipeline de 12 pasos.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### FV8.ipynb

Notebook en R que contiene el camino completo de la predicción: clase ternaria, percentiles, lags, canaritos, interacciones, recetas, limpieza cruzada, ensamble y los 15 archivos de entrega. Las celdas de texto y de código aparecen como líneas marcadas con #%% celda N.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–31] Celda de texto con el resumen de FV8 (FV4 con el feature engineering, los
#   canaritos y la limpieza nuevos), tabla de 12 pasos con meses y modelos, y notas sobre checkpoints y FV9.
#   Indica un ensamble de 10 recetas, mientras que PARAM$n_recetas (línea 144) vale 5.
#%% celda 1 [texto]
# Predicción de bajas – FV8 (HT4960-FV8)

**FV8 = FV4 con el feature engineering, los canaritos y la limpieza nuevos** (ver `modificaciones_proximo_experimento.md`). El final es el de FV4: limpieza cruzada de los 4 meses + un ensamble de 10 recetas.

| # | Paso | Meses | Modelos |
|---|---|---|---|
| 1 | Se eliminan los préstamos personales; `ccajas_depositos` de 202105 → NA | todos | — |
| 2 | **Percentil por mes** para todas las originales (0 → 0; positivos en (0, 1]; negativos en [−1, 0)), menos 12 excepciones que quedan en crudo | todos | — |
| 3 | Lags 1–3, diferencias 1–3 y acumulado **sobre los percentiles** (y sobre las 12 excepciones) | todos | — |
| 3 bis | **Script del docente:** tendencia (`_tend3`) y promedio (`_avg3`) de 3 meses sobre las mismas variables; se juzgan en el canarito 2 | todos | — |
| 4 | **Ronda 1:** todas contra todas entre las originales (×, ÷, ÷ invertido) | solo 202104 | — |
| 5 | **Canarito 1:** juez = mejor receta de FV4, entrenado con 202104 completo, importancia por **Gain**, 1 semilla, corte media + 2 desvíos | 202104 (control: 202106) | 5 |
| 6 | **Ronda 2:** las 20 mejores sobrevivientes (ejes) contra las sobrevivientes que no participaron de la ronda 1 | solo 202104 | — |
| 7 | **Canarito 2** (mismo juez) → `campos_finales` | 202104 (control: 202106) | 5 |
| 8 | Las interacciones de `campos_finales` se calculan en todos los meses; se borran las originales en crudo | todos | — |
| 9 | Bayesiana: **se reusa `BO_log.txt` de FV4** (solo corre si faltan iteraciones; en ese caso, antes limpia con el modelo30 del docente) | — | — |
| 10 | **Prueba:** limpieza cruzada A/B de 202103–04 + 10 recetas, predice 202106 | 202103 + 202104 | 20 × 2 + 10 |
| 11 | **Final (como FV4):** limpieza cruzada A/B de los 4 meses + 10 recetas, predice 202108 | 202103 a 202106 | 20 × 2 + 10 |
| 12 | 15 archivos de entrega | 202108 | — |

- `_lag2`, `_lag3`, `_delta2`, `_delta3` son 100% NA en 202104: **no pasan por el canarito y se conservan siempre**.
- Los canaritos se sortean una vez por filtro (la matriz del juez se arma una sola vez, para no duplicar memoria); las 5 semillas cambian el modelo.
- **Checkpoints:** cada semilla de cada canarito, los filtros, `campos_finales`, las limpiezas, la prueba y la predicción final se guardan. Si la VM se corta, se relanza **el mismo comando** y retoma.
- **FV9** (la versión con el final de FV5) va a copiar de acá los canaritos, `campos_finales`, la limpieza de la prueba y la prueba.

Runtime: **R**.

#%% celda 2 [texto]
## 0. Clase ternaria

# [Anotación · líneas 32–46] Lee competencia_01_crudo.csv con data.table y calcula para cada registro
#   periodo0, el mes expresado como año por 12 más mes. Ordena por cliente y periodo, y agrega periodo1 y
#   periodo2 con los periodos de los dos registros siguientes del mismo cliente.
#%% celda 3 [código]
require( "data.table" )

dataset <- fread("~/buckets/b1/datasets/competencia_01_crudo.csv" )

dsimple <- dataset[, list(
    "pos" = .I,
    numero_de_cliente,
    periodo0 = as.integer(foto_mes/100)*12 +  foto_mes%%100 ) ]

setorder( dsimple, numero_de_cliente, periodo0 )

periodo_ultimo <- dsimple[, max(periodo0) ]
periodo_anteultimo <- periodo_ultimo - 1

# [Anotación · líneas 47–59] Asigna clase_ternaria: CONTINUA a los registros anteriores a periodo_anteultimo;
#   BAJA+1 si el cliente no tiene registro en el mes siguiente, para registros anteriores al último mes; BAJA+2
#   si tiene registro en el mes siguiente pero no en el subsiguiente, para registros anteriores a
#   periodo_anteultimo.
dsimple[, c("periodo1", "periodo2") :=
    shift(periodo0, n=1:2, fill=NA, type="lead"),  numero_de_cliente ]

dsimple[ periodo0 < periodo_anteultimo, clase_ternaria := "CONTINUA" ]

dsimple[ periodo0 < periodo_ultimo &
    ( is.na(periodo1) | periodo0 + 1 < periodo1 ),
    clase_ternaria := "BAJA+1" ]

dsimple[ periodo0 < periodo_anteultimo & (periodo0+1 == periodo1 )
    & ( is.na(periodo2) | periodo0 + 2 < periodo2 ),
    clase_ternaria := "BAJA+2" ]

# [Anotación · líneas 60–69] Restituye el orden original de las filas, copia clase_ternaria a dataset y
#   escribe competencia_01.csv.gz en ~/buckets/b1/datasets. Cuenta los registros por foto_mes y clase_ternaria.
setorder( dsimple, pos )
dataset[, clase_ternaria := dsimple$clase_ternaria ]

fwrite( dataset,
    file =  "~/buckets/b1/datasets/competencia_01.csv.gz",
    sep = ","
)

dataset[, .N, keyby = list(foto_mes, clase_ternaria)]

# [Anotación · líneas 70–96] Borra el entorno de R, instala los paquetes que faltan (data.table, R.utils,
#   rlist, bbotk, mlr3, mlr3mbo, mlr3learners, DiceKriging, lightgbm, Rcpp) y los carga. Fija setDTthreads(0),
#   es decir todos los núcleos de la VM.
#%% celda 4 [texto]
## 1. Librerías

#%% celda 5 [código]
rm(list = ls(all.names = TRUE))
gc(verbose = FALSE)

paquetes <- c("data.table", "R.utils", "rlist",
              "bbotk", "mlr3", "mlr3mbo", "mlr3learners", "DiceKriging",
              "lightgbm", "Rcpp")
faltantes <- paquetes[!paquetes %in% rownames(installed.packages())]
if (length(faltantes) > 0) install.packages(faltantes)

library(data.table)
library(R.utils)
library(rlist)
library(bbotk)
library(mlr3)
library(mlr3mbo)
library(mlr3learners)
library(DiceKriging)
library(lightgbm)
library(Rcpp)

setDTthreads(0)   # todos los núcleos de la VM
format(Sys.time(), "%a %b %d %X %Y")

# [Anotación · líneas 97–122] Texto de la sección de parámetros: la semilla primigenia es la misma de FV4 y
#   FV5. PARAM fija el experimento HT4960-FV8, la semilla 379531, el dataset competencia_01.csv.gz, los meses de
#   prueba 202103 y 202104 con futuro 202106, los de final 202103 a 202106 con futuro 202108, 202107 sólo para
#   historia y las 12 excepciones que quedan en crudo.
#%% celda 6 [texto]
## 2. Parámetros
Todo lo ajustable está acá. Las semillas se generan solas a partir de la primigenia (la primera de la lista es la primigenia). **Misma primigenia que FV4/FV5**, para que FV9 pueda reusar lo que calcula FV8.

#%% celda 7 [código]
PARAM <- list()
PARAM$experimento <- "HT4960-FV8"
PARAM$bo_log_origen <- "HT4960-FV4"   # de acá se copia BO_log.txt (recetas y juez de los canaritos)
PARAM$semilla_primigenia <- 379531

# rutas
PARAM$carpeta_base <- path.expand("~/buckets/b1")
PARAM$dataset <- file.path(PARAM$carpeta_base, "datasets", "competencia_01.csv.gz")

# meses
PARAM$train_prueba  <- c(202103, 202104)
PARAM$future_prueba <- c(202106)
PARAM$train_final   <- c(202103, 202104, 202105, 202106)
PARAM$future_final  <- c(202108)
PARAM$mes_solo_historia <- c(202107)   # solo da historia (lags) a 202108

# feature engineering: variables que quedan en crudo (sin percentil)
PARAM$excepciones <- c("cliente_vip", "cliente_edad", "cliente_antiguedad", "cproductos",
                       "ctarjeta_visa", "ctarjeta_master",
                       "Master_delinquency", "Master_status", "Master_Finiciomora",
                       "Visa_delinquency", "Visa_status", "Visa_Finiciomora")
# [Anotación · líneas 123–157] Fija el juez de los canaritos (entrenamiento en 202104, control en 202106 con
#   hasta 50.000 filas, 1 semilla, 20 % de canaritos y 20 ejes), la regex de forzadas, el modelo30 (partición 70
#   %, 20 semillas, submuestreo de CONTINUA al 10 % y umbral 0,5), la bayesiana (50 iteraciones y 5 semillas), 5
#   recetas con 1 semilla cada una, la prueba desactivada, las ganancias de 1.072.500 y -27.500, los cortes de
#   8.000 a 15.000 cada 500 y un pool de 100 semillas derivado de la primigenia.

# canaritos (juez nuevo)
PARAM$juez_mes_train     <- 202104   # el juez entrena con este mes completo
PARAM$juez_mes_control   <- 202106   # solo control: AUC del juez
PARAM$juez_filas_control <- 50000    # muestra de 202106 para el control (todas las bajas + CONTINUA)
PARAM$juez_semillas      <- 1   # (era 5) 1 semilla por tiempo: entrega el domingo
PARAM$canaritos_pct      <- 0.20
PARAM$n_ejes             <- 20       # ronda 2: mejores sobrevivientes del canarito 1
PARAM$regex_forzadas     <- "_(lag2|lag3|delta2|delta3)$"   # 100% NA en 202104: se conservan siempre

# modelo30 (limpiezas)
PARAM$training_pct    <- 70     # partición 70/30 de 202103+202104 (limpieza de la bayesiana)
PARAM$n_semillas30    <- 20
PARAM$undersampling30 <- 0.10   # % de CONTINUA que usa el modelo30
PARAM$umbral_prob30   <- 0.5    # CONTINUA con prob30 mayor a esto se sacan

# bayesiana (solo corre si BO_log.txt tiene menos iteraciones que esto)
PARAM$bo_iteraciones <- 50
PARAM$bo_semillas    <- 5

# ensamble de recetas (prueba y final)
PARAM$n_recetas           <- 5    # (era 10) por tiempo: entrega el domingo
PARAM$hacer_prueba        <- FALSE   # (por tiempo) sin prueba sobre 202106: se compara con la ganancia pública
PARAM$semillas_por_receta <- 1

# ganancia y entrega
PARAM$ganancia_acierto <- 1072500
PARAM$ganancia_error   <- -27500
PARAM$cortes <- seq(8000, 15000, by = 500)

PARAM$num_threads <- parallel::detectCores()   # se adapta a la VM

# pool de semillas
set.seed(PARAM$semilla_primigenia, kind = "L'Ecuyer-CMRG")
PARAM$semillas <- unique(c(PARAM$semilla_primigenia, sample(100000:999999, 200)))[1:100]
# [Anotación · líneas 158–201] Lista de parámetros fijos de LightGBM: boosting gbdt, objective binary, metric
#   auc, deterministic TRUE, max_bin 31, max_depth -1, lambda_l1 y lambda_l2 en 0, drop_rate 0,1,
#   feature_fraction 0,50 y learning_rate 0,005. num_iterations, num_leaves y min_sum_hessian_in_leaf quedan con
#   valores de referencia que, según el comentario de la línea 160, la bayesiana sobrescribe.

#%% celda 8 [código]
# parámetros fijos del LightGBM (la bayesiana pisa num_iterations, num_leaves y min_sum_hessian_in_leaf)
PARAM$lgbm$param_fijos <- list(
  boosting= "gbdt",
  objective= "binary",
  metric= "auc",
  feature_pre_filter= FALSE,
  first_metric_only= FALSE,
  boost_from_average= TRUE,
  force_row_wise= TRUE,
  deterministic= TRUE,
  verbosity= -100,
  num_threads= PARAM$num_threads,

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

  num_iterations= 20000,
  num_leaves= 1024,
  min_sum_hessian_in_leaf= 1e-06
)
# [Anotación · líneas 202–214] Define el modelo30 del docente como param_fijos con 2180 iteraciones, 30 hojas
#   y min_sum_hessian_in_leaf 0,1141634103. Define el espacio de búsqueda de la bayesiana: num_iterations de 64
#   a 4096, num_leaves de 16 a 2048 y min_sum_hessian_in_leaf de 1e-06 a 0,1.

# modelo30 (parámetros del docente)
PARAM$lgbm$param30 <- modifyList(PARAM$lgbm$param_fijos, list(
  num_iterations= 2180L,
  num_leaves= 30L,
  min_sum_hessian_in_leaf= 0.1141634103
))

PARAM$hs <- ps(
  num_iterations= p_int(lower= 64L,  upper= 4096L),
  num_leaves= p_int(lower= 16L,  upper= 2048L),
  min_sum_hessian_in_leaf= p_dbl(lower= 1e-06, upper= 0.1)
)
# [Anotación · líneas 215–241] reloj() imprime la hora, el mensaje y la RAM usada, y lo agrega a
#   exp/HT4960-FV8/log_FV8.txt. safe_div() divide y pone 0 donde el divisor es 0. auc() calcula el AUC por suma
#   de rangos: resta n1 por (n1 + 1) / 2 a la suma de rangos de los positivos y divide por n1 por n0.

#%% celda 9 [código]
# ---------- funciones auxiliares ----------
# reloj: imprime y además escribe en log_FV8.txt (nbconvert no muestra nada hasta terminar)
memoria_vm <- function() {
  m <- tryCatch(system("free -g | awk 'NR==2{print $3\"/\"$2}'", intern = TRUE), error = function(e) "?")
  paste0("RAM ", m, " GB")
}
reloj <- function(msg) {
  linea <- paste(format(Sys.time(), "%d/%m %H:%M:%S"), "-", msg, "-", memoria_vm())
  cat(linea, "\n")
  arch <- file.path(PARAM$carpeta_base, "exp", PARAM$experimento, "log_FV8.txt")
  if (dir.exists(dirname(arch))) cat(linea, "\n", file = arch, append = TRUE)
}

safe_div <- function(a, b) {
  r <- a / b
  r[!is.na(b) & b == 0] <- 0
  r
}

# AUC calculada por rangos
auc <- function(y, p) {
  r <- frank(p, ties.method = "average")
  n1 <- sum(y == 1); n0 <- sum(y == 0)
  (sum(r[y == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0)
}
# [Anotación · líneas 242–251] loguear() agrega al archivo indicado una fila con la fecha y los valores de la
#   lista (los vectores se unen con guion bajo), creando antes el encabezado si el archivo no existe, y además
#   la imprime.

loguear <- function(reg, arch) {
  if (!file.exists(arch)) {
    cat(paste0("fecha\t", paste(names(reg), collapse = "\t"), "\n"), file = arch)
  }
  valores <- sapply(reg, function(x) paste(x, collapse = "_"))
  linea <- paste0(format(Sys.time(), "%Y%m%d.%H%M%S"), "\t", paste(valores, collapse = "\t"), "\n")
  cat(linea, file = arch, append = TRUE)
  cat(linea)
}
# [Anotación · líneas 252–265] partir_mitades() reparte un vector de filas en dos mitades al azar con la
#   semilla dada, estratificadas por clase_ternaria. NO_FEATURES enumera las columnas que no son variables:
#   clase_ternaria, clase01, fold, prob30, aporta, aporta_prueba y aporta_final.

# divide filas en 2 mitades, estratificado por clase
partir_mitades <- function(idx, semilla) {
  set.seed(semilla, kind = "L'Ecuyer-CMRG")
  cl <- dataset$clase_ternaria[idx]
  mitad <- integer(length(idx))
  for (k in unique(cl)) {
    pos <- which(cl == k)
    mitad[pos] <- sample(rep(1:2, length.out = length(pos)))
  }
  mitad
}

NO_FEATURES <- c("clase_ternaria", "clase01", "fold", "prob30", "aporta", "aporta_prueba", "aporta_final")
# [Anotación · líneas 266–298] Los nombres de las interacciones codifican la fórmula: __x__ y __X2__
#   multiplican, __div__ y __DIV2__ dividen. valor_col() calcula una columna a partir de su nombre, y
#   nuevo_operando() guarda en caché los operandos para las filas indicadas. La ronda 1 combina originales y la
#   ronda 2 combina cualquier variable.

# ---------- interacciones ----------
# Ronda 1: A__x__B, A__div__B   (A y B son originales)
# Ronda 2: E__X2__C, E__DIV2__C (E y C pueden ser cualquier variable, incluso de la ronda 1)
# El nombre codifica la fórmula: cualquier interacción se puede recalcular en cualquier mes.
OPS <- c("__X2__", "__DIV2__", "__x__", "__div__")   # primero los de la ronda 2

valor_col <- function(nm, idx, operando) {
  for (op in OPS) {
    if (grepl(op, nm, fixed = TRUE)) {
      p <- strsplit(nm, op, fixed = TRUE)[[1]]
      if (length(p) != 2) stop("Nombre de interacción inválido: ", nm)
      a <- operando(p[1]); b <- operando(p[2])
      return(if (op %in% c("__X2__", "__x__")) a * b else safe_div(a, b))
    }
  }
  if (!nm %in% names(dataset)) stop("Columna desconocida: ", nm)
  as.numeric(dataset[[nm]][idx])
}

# devuelve una función que calcula (y recuerda) los operandos para las filas idx
nuevo_operando <- function(idx) {
  cache <- new.env(hash = TRUE)
  operando <- function(nm) {
    v <- cache[[nm]]
    if (is.null(v)) {
      v <- valor_col(nm, idx, operando)
      assign(nm, v, envir = cache)
    }
    v
  }
  operando
}
# [Anotación · líneas 299–322] armar_matriz() arma una matriz numérica con las columnas pedidas para las filas
#   indicadas; si hay canaritos, agrega columnas uniformes con runif y la semilla dada, e imprime el avance cada
#   5.000 columnas. tipo_de() clasifica cada nombre como canarito, ronda2, ronda1, docente o base.

# matriz numérica (filas idx) con las columnas pedidas + canaritos uniformes, sin copias intermedias
armar_matriz <- function(campos, idx, nombres_can = character(0), semilla_can = NULL) {
  operando <- nuevo_operando(idx)
  X <- matrix(NA_real_, nrow = length(idx), ncol = length(campos) + length(nombres_can),
              dimnames = list(NULL, c(campos, nombres_can)))
  for (j in seq_along(campos)) {
    X[, j] <- valor_col(campos[j], idx, operando)
    if (j %% 5000 == 0) reloj(paste("  columnas", j, "/", length(campos)))
  }
  if (length(nombres_can) > 0) {
    set.seed(semilla_can, kind = "L'Ecuyer-CMRG")
    for (k in seq_along(nombres_can)) X[, length(campos) + k] <- runif(length(idx))
  }
  rm(operando); gc(verbose = FALSE)
  X
}

tipo_de <- function(v) {
  fifelse(grepl("^canarito_", v), "canarito",
  fifelse(grepl("__X2__|__DIV2__", v), "ronda2",
  fifelse(grepl("__x__|__div__", v), "ronda1",
  fifelse(grepl("_(tend3|avg3)$", v), "docente", "base"))))
}
# [Anotación · líneas 323–340] Funciones de checkpoints: ck() arma la ruta en checkpoints/, guardar_ck()
#   escribe un temporal y lo renombra, leer_ck() lee, e ids_texto() y clave() convierten ids y meses a texto.
#   posiciones_ck() ubica cada fila guardada en el dataset por numero_de_cliente y foto_mes, y se detiene si
#   alguna no coincide.

# ---------- checkpoints ----------
ck <- function(nombre) file.path("checkpoints", nombre)
guardar_ck <- function(dt, nombre) {
  tmp <- file.path("checkpoints", paste0("tmp_", nombre))   # misma extensión: fwrite comprime igual
  fwrite(dt, tmp)
  file.rename(tmp, ck(nombre))
  cat("Checkpoint guardado:", nombre, "\n")
}
ids_texto <- function(x) if (is.character(x)) x else format(x, scientific = FALSE, trim = TRUE)
clave <- function(cli, mes) paste(ids_texto(cli), mes)
leer_ck <- function(nombre) fread(ck(nombre), colClasses = list(character = "numero_de_cliente"))
posiciones_ck <- function(dt_ck) {
  pos <- match(clave(dt_ck$numero_de_cliente, dt_ck$foto_mes),
               clave(dataset$numero_de_cliente, dataset$foto_mes))
  if (anyNA(pos)) stop("El checkpoint no coincide con el dataset")
  pos
}
# [Anotación · líneas 341–366] Crea exp/HT4960-FV8 en ~/buckets/b1 con las subcarpetas entregas y checkpoints,
#   y se posiciona allí. Si falta BO_log.txt lo copia desde HT4960-FV4; toma como receta del juez la fila de
#   mayor metrica, con force_col_wise TRUE y force_row_wise FALSE, e imprime esa receta.

#%% celda 10 [código]
carpeta_exp <- file.path(PARAM$carpeta_base, "exp", PARAM$experimento)
dir.create(carpeta_exp, recursive = TRUE, showWarnings = FALSE)
setwd(carpeta_exp)
dir.create("entregas", showWarnings = FALSE)
dir.create("checkpoints", showWarnings = FALSE)
cat("Carpeta de trabajo:", getwd(), "\n")

# BO_log.txt de FV4: recetas del ensamble y receta del juez de los canaritos
if (!file.exists("BO_log.txt")) {
  origen_bo <- file.path(PARAM$carpeta_base, "exp", PARAM$bo_log_origen, "BO_log.txt")
  if (!file.exists(origen_bo)) stop("No se encontró ", origen_bo)
  file.copy(origen_bo, "BO_log.txt")
  cat("Copiado BO_log.txt desde", PARAM$bo_log_origen, "\n")
}
tb_bo <- fread("BO_log.txt")
setorder(tb_bo, -metrica)
receta_juez <- tb_bo[1, list(num_iterations = as.integer(num_iterations),
                             num_leaves = as.integer(num_leaves),
                             min_sum_hessian_in_leaf = as.double(min_sum_hessian_in_leaf))]
PARAM$lgbm$param_juez <- modifyList(PARAM$lgbm$param_fijos, c(as.list(receta_juez),
  list(force_row_wise = FALSE, force_col_wise = TRUE)))   # col-wise: menos memoria con muchas columnas
reloj(paste("Comienza", PARAM$experimento, "-", PARAM$num_threads, "núcleos"))
cat("Juez de los canaritos (mejor receta de", PARAM$bo_log_origen, "):\n")
print(tb_bo[1, list(num_iterations, num_leaves, min_sum_hessian_in_leaf, metrica)])
# [Anotación · líneas 367–390] Celda 11, texto de la sección de feature engineering. Celda 12: lee
#   competencia_01.csv.gz, elimina cprestamos_personales y mprestamos_personales, cuenta los ceros de
#   ccajas_depositos en 202105 y los pasa a NA. Verifica que las originales sean numéricas, que existan las 12
#   excepciones y que ningún nombre contenga doble guion bajo.

#%% celda 11 [texto]
## 3. Feature engineering
### 3.1 Lectura y correcciones

#%% celda 12 [código]
reloj("Leyendo el dataset")
dataset <- fread(PARAM$dataset)
dataset[, c("cprestamos_personales", "mprestamos_personales") := NULL]

n_ceros <- dataset[foto_mes == 202105 & ccajas_depositos == 0, .N]
dataset[foto_mes == 202105, ccajas_depositos := NA]
cat("ccajas_depositos en 202105:", n_ceros, "ceros pasados a NA\n")

ORIGINALES <- setdiff(names(dataset), c("numero_de_cliente", "foto_mes", "clase_ternaria"))
no_num <- ORIGINALES[!sapply(dataset[, ORIGINALES, with = FALSE], is.numeric)]
if (length(no_num) > 0) stop(paste("Variables no numéricas:", paste(no_num, collapse = ", ")))
faltan <- setdiff(PARAM$excepciones, ORIGINALES)
if (length(faltan) > 0) stop(paste("Excepciones no encontradas:", paste(faltan, collapse = ", ")))
if (any(grepl("__", ORIGINALES, fixed = TRUE))) stop("Hay originales con '__' en el nombre")

CON_PCT <- setdiff(ORIGINALES, PARAM$excepciones)   # llevan percentil; en crudo se borran al final
cat("Originales:", length(ORIGINALES), " con percentil:", length(CON_PCT),
    " excepciones (en crudo):", length(PARAM$excepciones), "\n")
# [Anotación · líneas 391–417] Celda 13 describe la regla de percentil. Celda 14: pct_signo() deja los ceros
#   en 0, asigna a los positivos su rango dividido por la cantidad de positivos y a los negativos el rango de su
#   valor absoluto con signo negativo. Crea la columna _pct por foto_mes para cada original sin excepción e
#   imprime mínimo, máximo, ceros y NA de las 8 primeras.

#%% celda 13 [texto]
### 3.2 Percentil por mes (regla nueva)
Dentro de cada `foto_mes`: **0 → 0**; positivos equidistantes en **(0, 1]** (el más grande vale 1); negativos equidistantes en **[−1, 0)** (el más negativo vale −1); NA → NA. Empates: puesto promedio. Columna nueva: `<variable>_pct`.

#%% celda 14 [código]
pct_signo <- function(x) {
  r <- rep(NA_real_, length(x))
  r[!is.na(x) & x == 0] <- 0
  p <- which(x > 0)
  if (length(p) > 0) r[p] <- frank(x[p], ties.method = "average") / length(p)
  n <- which(x < 0)
  if (length(n) > 0) r[n] <- -frank(-x[n], ties.method = "average") / length(n)
  r
}

reloj("Calculando percentiles")
for (col in CON_PCT) {
  dataset[, (paste0(col, "_pct")) := pct_signo(get(col)), by = foto_mes]
}
VARS_PCT <- paste0(CON_PCT, "_pct")
cat("Percentiles creados:", length(VARS_PCT), "\n")

# control: rango de algunos percentiles
print(rbindlist(lapply(head(VARS_PCT, 8), function(v)
  data.table(variable = v, min = min(dataset[[v]], na.rm = TRUE), max = max(dataset[[v]], na.rm = TRUE),
             ceros = sum(dataset[[v]] == 0, na.rm = TRUE), na = sum(is.na(dataset[[v]]))))))
# [Anotación · líneas 418–438] Celda 15 (texto): las derivadas se calculan sobre los percentiles y las
#   excepciones, con diferencias y no con tasas. Celda 16: vars_lag junta percentiles y excepciones, ordena por
#   cliente y foto_mes, calcula periodo en meses, arma valido[k] (el registro k meses atrás es del mismo cliente
#   y del mes correspondiente) y marca el primer registro de cada cliente.

#%% celda 15 [texto]
### 3.3 Lags, diferencias y acumulado
Sobre los percentiles y las 12 excepciones (las originales en crudo no llevan derivadas). Siempre diferencias, nunca tasas.

#%% celda 16 [código]
vars_lag <- c(VARS_PCT, PARAM$excepciones)
cat("Variables a las que se les calculan lags:", length(vars_lag), "\n")

setorder(dataset, numero_de_cliente, foto_mes)
cliente <- dataset$numero_de_cliente
periodo <- (dataset$foto_mes %/% 100L) * 12L + dataset$foto_mes %% 100L

valido <- lapply(1:3, function(k) {
  cl <- shift(cliente, k)
  pe <- shift(periodo, k)
  !is.na(cl) & cl == cliente & pe == periodo - k
})
pos_primera <- match(cliente, cliente)
es_primera  <- pos_primera == seq_along(cliente)

# [Anotación · líneas 439–461] Para cada variable de vars_lag calcula lag1, lag2 y lag3 con shift, en NA
#   cuando valido no se cumple; delta1 = x - lag1, delta2 = lag1 - lag2, delta3 = lag2 - lag3, y acum = x menos
#   el valor del primer mes del cliente. Imprime el avance cada 25 variables, borra los auxiliares y cuenta las
#   columnas.
reloj("Calculando lags, diferencias y acumulado")
for (i in seq_along(vars_lag)) {
  v <- vars_lag[i]
  x <- as.numeric(dataset[[v]])

  l1 <- shift(x, 1); l1[!valido[[1]]] <- NA
  l2 <- shift(x, 2); l2[!valido[[2]]] <- NA
  l3 <- shift(x, 3); l3[!valido[[3]]] <- NA
  acum <- x - x[pos_primera]; acum[es_primera] <- NA

  dataset[, (paste0(v, "_lag1"))   := l1]
  dataset[, (paste0(v, "_lag2"))   := l2]
  dataset[, (paste0(v, "_lag3"))   := l3]
  dataset[, (paste0(v, "_delta1")) := x - l1]
  dataset[, (paste0(v, "_delta2")) := l1 - l2]
  dataset[, (paste0(v, "_delta3")) := l2 - l3]
  dataset[, (paste0(v, "_acum"))   := acum]

  if (i %% 25 == 0) reloj(paste(i, "/", length(vars_lag)))
}
rm(cliente, periodo, valido, pos_primera, es_primera, x, l1, l2, l3, acum)
gc(verbose = FALSE)
cat("Columnas después de los lags:", ncol(dataset), "\n")
# [Anotación · líneas 462–484] Celda 17 (texto): el script del docente se aplica a las mismas variables de los
#   lags con ventana de 3 meses, antes de quitar 202107, y sus columnas no pasan por el canarito 1. Celda 18:
#   cppFunction define en C++ fhistC, con arreglos x e y de 100 posiciones y un vector de salida de 5 bloques de
#   n filas; el quinto bloque guarda el valor de la fila anterior, salvo en la primera fila de cada cliente.

#%% celda 17 [texto]
### 3.3 bis Tendencia y promedio de 3 meses (script del docente)
Código del docente, sin cambios en las funciones (`fhistC` en C vía Rcpp + `TendenciaYmuchomas`). Se aplica a las mismas variables que los lags (percentiles + 12 excepciones), con `ventana = 3`, `tendencia = TRUE` y `promedio = TRUE` → columnas `_tend3` y `_avg3`.
- Se calcula **antes de sacar 202107**, para que la ventana de 202108 use 202106–202107–202108.
- En 202104 la ventana solo tiene 202103 y 202104 (los datos empiezan en 202103); en 202103 quedan NA.
- **No pasan por el canarito 1** (así se reusa la semilla ya calculada): se juzgan recién en el **canarito 2**, junto con las sobrevivientes del canarito 1 y la ronda 2. No son ejes ni "contra" de la ronda 2.

#%% celda 18 [código]
cppFunction("NumericVector fhistC(NumericVector pcolumna, IntegerVector pdesde )
{
  /* Aqui se cargan los valores para la regresion */
  double  x[100] ;
  double  y[100] ;

  int n = pcolumna.size();
  NumericVector out( 5*n );

  for(int i = 0; i < n; i++)
  {
    //lag
    if( pdesde[i]-1 < i )  out[ i + 4*n ]  =  pcolumna[i-1] ;
    else                   out[ i + 4*n ]  =  NA_REAL ;
# [Anotación · líneas 485–523] Para cada fila i toma los valores de la columna desde pdesde[i] hasta i,
#   conserva los no NA con su posición en la ventana y, si hay al menos dos, acumula las sumas para la pendiente
#   por cuadrados mínimos y los valores mínimo y máximo.


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

    /* Si hay al menos dos valores */
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
# [Anotación · líneas 524–540] Calcula la pendiente (libre * xysum - xsum * ysum) / (libre * xxsum - xsum^2),
#   el mínimo, el máximo y el promedio de la ventana, cada uno en su bloque del vector de salida; con menos de
#   dos valores deja NA. Devuelve el vector de 5n valores.

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
# [Anotación · líneas 541–567] Comentarios del docente y la función TendenciaYmuchomas, con los argumentos
#   cols, ventana, tendencia, minimo, maximo, promedio, ratioavg y ratiomax. Calcula vector_desde, la posición
#   donde empieza la ventana de cada fila, con seq y con 1 en las primeras ventana filas.
#------------------------------------------------------------------------------

# calcula la tendencia de las variables cols de los ultimos 6 meses
# la tendencia es la pendiente de la recta que ajusta por cuadrados minimos
# La funcionalidad de ratioavg es autoria de  Daiana Sparta,  UAustral  2021

TendenciaYmuchomas <- function(
    dataset, cols, ventana = 6, tendencia = TRUE,
    minimo = TRUE, maximo = TRUE, promedio = TRUE,
    ratioavg = FALSE, ratiomax = FALSE) {
  gc(verbose= FALSE)
  # Esta es la cantidad de meses que utilizo para la historia
  ventana_regresion <- ventana

  last <- nrow(dataset)

  # creo el vector_desde que indica cada ventana
  # de esta forma se acelera el procesamiento ya que lo hago una sola vez
  vector_ids <- dataset[ , numero_de_cliente ]

  vector_desde <- seq(
    -ventana_regresion + 2,
    nrow(dataset) - ventana_regresion + 1
  )

  vector_desde[1:ventana_regresion] <- 1

# [Anotación · líneas 568–600] Corrige vector_desde en dos recorridos: el primero reinicia la ventana en cada
#   cambio de cliente y el segundo impide que la ventana retroceda. Para cada variable de cols llama a fhistC y
#   crea las columnas _tend<ventana>, _min, _max y _avg según los flags; en la llamada del docente sólo se crean
#   _tend3 y _avg3.
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
# [Anotación · líneas 601–614] Crea las columnas de ratio contra el promedio y contra el máximo de la ventana
#   sólo si ratioavg o ratiomax son TRUE; en la llamada del docente ambos son FALSE. Cierra la función, que
#   modifica dataset por referencia.

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
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
# [Anotación · líneas 615–630] Llama a TendenciaYmuchomas sobre vars_lag con ventana 3, tendencia y promedio
#   en TRUE, y mínimo, máximo y ratios en FALSE. Verifica que existan las columnas _tend3 y _avg3 de todas las
#   variables y lo imprime.

reloj("Tendencia y promedio de 3 meses (docente)")
setorderv(dataset, c("numero_de_cliente", "foto_mes"))
TendenciaYmuchomas(dataset,
  cols= vars_lag,
  ventana= 3,
  tendencia= TRUE,
  minimo= FALSE,
  maximo= FALSE,
  promedio= TRUE,
  ratioavg= FALSE,
  ratiomax= FALSE
)
VARS_DOCENTE <- c(paste0(vars_lag, "_tend3"), paste0(vars_lag, "_avg3"))
if (!all(VARS_DOCENTE %in% names(dataset))) stop("Faltan columnas _tend3/_avg3")
reloj(paste("Variables del docente creadas:", length(VARS_DOCENTE)))
# [Anotación · líneas 631–663] Celda 19 (texto) y celda 20: quita 202107, crea clase01 (1 para BAJA+1 o
#   BAJA+2), asigna fold 1 (70 %) o 2 (30 %) sobre 202103 y 202104 estratificado por clase_ternaria, define
#   BASE, FORZADAS (_lag2, _lag3, _delta2, _delta3), JUZGABLES_BASE y RONDA1 (A__x__B, A__div__B y B__div__A
#   para cada par de originales), e imprime filas y columnas.

#%% celda 19 [texto]
### 3.4 Preparación
Se saca 202107 (solo daba historia a 202108), se crea `clase01` y la partición 70/30 de 202103+202104 (la usa la limpieza de la bayesiana, si se corre). Se definen los grupos de variables.

#%% celda 20 [código]
dataset <- dataset[!(foto_mes %in% PARAM$mes_solo_historia)]
gc(verbose = FALSE)

dataset[, clase01 := as.integer(clase_ternaria %in% c("BAJA+1", "BAJA+2"))]

set.seed(PARAM$semilla_primigenia, kind = "L'Ecuyer-CMRG")
bloque <- c(rep(1L, PARAM$training_pct), rep(2L, 100L - PARAM$training_pct))
dataset[, fold := NA_integer_]
dataset[foto_mes %in% PARAM$train_prueba,
        fold := sample(rep(bloque, ceiling(.N / length(bloque))))[1:.N],
        by = clase_ternaria]

# grupos de variables
BASE <- setdiff(names(dataset), c(NO_FEATURES, CON_PCT, VARS_DOCENTE, "numero_de_cliente", "foto_mes"))
FORZADAS <- c("numero_de_cliente", "foto_mes", grep(PARAM$regex_forzadas, BASE, value = TRUE))
JUZGABLES_BASE <- setdiff(BASE, FORZADAS)

pares1 <- combn(ORIGINALES, 2, simplify = FALSE)
RONDA1 <- unlist(lapply(pares1, function(p)
  c(paste0(p[1], "__x__", p[2]), paste0(p[1], "__div__", p[2]), paste0(p[2], "__div__", p[1]))))

cat("Filas:", nrow(dataset), " Columnas:", ncol(dataset), "\n")
cat("Base (variables del modelo antes de interacciones):", length(BASE), "\n")
cat("  forzadas (no pasan por el canarito):", length(FORZADAS), "\n")
cat("  juzgadas por el canarito 1:", length(JUZGABLES_BASE), "\n")
cat("Ronda 1 (todas contra todas entre", length(ORIGINALES), "originales):", length(RONDA1), "columnas\n")
dataset[, .N, keyby = foto_mes]
# [Anotación · líneas 664–674] Celda 21 (texto) describe el canarito: matriz con 202104 completo y 20 % de
#   canaritos uniformes, juez con la receta de FV4, importancia por Gain, AUC de control en 202106 y corte en
#   media más dos desvíos. El texto menciona 5 semillas para el juez, pero PARAM$juez_semillas (línea 128) vale
#   1.

#%% celda 21 [texto]
## 4. Canarito (función)
1. Arma **una matriz con 202104 completo**: las variables a juzgar + 20% de canaritos uniformes (las interacciones se calculan solo para estas filas).
2. Juez = **mejor receta de FV4**, sin undersampling. Se entrena con **5 semillas** sobre el mismo `lgb.Dataset`.
3. Importancia = **Gain** de LightGBM (`lgb.importance`). Puesto 1 = más Gain; las no usadas (Gain 0) van al último puesto.
4. **Control:** AUC de cada semilla sobre una muestra de 202106 (todas las bajas + CONTINUA hasta 50.000). No interviene en el corte.
5. Se promedia el puesto entre las 5 semillas y se corta en **media + 2 desvíos** de los puestos de los canaritos. Sobreviven las variables reales por encima del corte.

Cada semilla se guarda en `checkpoints/`; si la VM se corta, solo se rehacen las que faltan.

# [Anotación · líneas 675–695] Define correr_canarito(etapa, campos): si existe filtro_canaritos_etapaN.csv lo
#   lee y termina; si no, calcula la cantidad de canaritos como ceil(0,20 por la cantidad de variables), los
#   nombres canarito_00001 en adelante y las semillas pendientes, y verifica que los checkpoints guardados
#   correspondan a la misma lista de variables.
#%% celda 22 [código]
correr_canarito <- function(etapa, campos) {
  arch <- sprintf("filtro_canaritos_etapa%d.csv", etapa)
  if (file.exists(arch)) {
    reloj(paste("Checkpoint: canarito", etapa, "ya estaba hecho"))
    return(fread(arch))
  }
  n_can <- ceiling(PARAM$canaritos_pct * length(campos))
  nombres_can <- sprintf("canarito_%05d", seq_len(n_can))
  semillas <- PARAM$semillas[seq_len(PARAM$juez_semillas)]
  arch_sem <- function(s) ck(sprintf("canarito%d_semilla_%d.csv", etapa, s))
  hechas <- semillas[file.exists(sapply(semillas, arch_sem))]
  for (s in hechas) {   # una semilla guardada tiene que ser de esta misma lista de variables
    if (!setequal(fread(arch_sem(s), select = "variable")$variable, c(campos, nombres_can)))
      stop("El checkpoint ", arch_sem(s), " es de otra lista de variables: borrá checkpoints/canarito",
           etapa, "_semilla_*.csv y relanzá")
  }
  pendientes <- setdiff(semillas, hechas)
  cat("Canarito", etapa, "- variables reales:", length(campos), " canaritos:", n_can,
      " semillas pendientes:", length(pendientes), "\n")

# [Anotación · líneas 696–715] Si hay semillas pendientes, arma en 202104 la matriz de variables y canaritos
#   con semilla primigenia más 10 por etapa, construye el lgb.Dataset con la receta de mayor metrica en col-
#   wise, y arma la muestra de control de 202106 con todas las bajas y hasta 50.000 filas en total, con una
#   semilla propia.
  if (length(pendientes) > 0) {
    idx_tr <- dataset[, which(foto_mes == PARAM$juez_mes_train)]
    reloj(paste("Armando la matriz de", PARAM$juez_mes_train))
    X <- armar_matriz(campos, idx_tr, nombres_can, PARAM$semilla_primigenia + 10 * etapa)
    reloj(paste("Matriz:", nrow(X), "x", ncol(X), "-", round(8 * as.numeric(nrow(X)) * ncol(X) / 2^30, 1), "GB"))
    dtrain <- lgb.Dataset(X, label = dataset$clase01[idx_tr], free_raw_data = TRUE,
                          params = modifyList(PARAM$lgbm$param_juez, list(seed = pendientes[1])))
    lgb.Dataset.construct(dtrain)
    rm(X); gc(verbose = FALSE)
    reloj("lgb.Dataset construido")

    # control: muestra de 202106
    idx_c <- dataset[, which(foto_mes == PARAM$juez_mes_control)]
    set.seed(PARAM$semilla_primigenia, kind = "L'Ecuyer-CMRG")
    pos <- idx_c[dataset$clase01[idx_c] == 1L]
    neg <- idx_c[dataset$clase01[idx_c] == 0L]
    idx_c <- c(pos, sample(neg, max(0, min(length(neg), PARAM$juez_filas_control - length(pos)))))
    Xc <- armar_matriz(campos, idx_c, nombres_can, PARAM$semilla_primigenia + 10 * etapa + 1)
    yc <- dataset$clase01[idx_c]

# [Anotación · líneas 716–734] Para cada semilla pendiente entrena el juez, calcula el AUC de control, toma la
#   importancia por Gain y da el último puesto a las variables sin Gain. Guarda la tabla de la semilla en
#   checkpoints/ y registra el AUC de control en pantalla y en el log.
    for (s in pendientes) {
      t0 <- Sys.time()
      modelo <- lgb.train(data = dtrain, params = modifyList(PARAM$lgbm$param_juez, list(seed = s)))
      auc_c <- auc(yc, predict(modelo, Xc))
      imp <- lgb.importance(modelo)
      tb_s <- data.table(variable = c(campos, nombres_can))
      tb_s <- merge(tb_s, imp[, list(variable = Feature, gain = Gain)], by = "variable", all.x = TRUE)
      tb_s[is.na(gain), gain := 0]
      setorder(tb_s, -gain)
      n_total <- nrow(tb_s)
      tb_s[, puesto := as.numeric(seq_len(.N))]
      tb_s[gain == 0, puesto := as.numeric(n_total)]
      tb_s[, `:=`(semilla = s, auc_control = auc_c)]
      guardar_ck(tb_s, basename(arch_sem(s)))
      rm(modelo, imp); gc(verbose = FALSE)
      reloj(sprintf("Canarito %d: semilla %d lista (%.1f min) - AUC control %d = %.4f",
                    etapa, s, as.numeric(difftime(Sys.time(), t0, units = "mins")),
                    PARAM$juez_mes_control, auc_c))
    }
# [Anotación · líneas 735–756] Libera memoria, lee las tablas de las semillas, imprime el AUC y el AUC y la
#   cantidad de variables con Gain mayor que cero por semilla, promedia el puesto y el Gain de cada variable, y
#   corta en la media más dos desvíos de los puestos de los canaritos. Sobreviven las variables reales con
#   puesto menor que el corte; la tabla se guarda en el archivo del canarito y se imprime por tipo.
    rm(dtrain, Xc); gc(verbose = FALSE)
  }

  rankings <- rbindlist(lapply(semillas, function(s) fread(arch_sem(s))))
  print(rankings[, list(auc_control = auc_control[1], usadas = sum(gain > 0)), by = semilla])

  tb <- rankings[, list(puesto = mean(puesto), gain = mean(gain)), by = variable]
  tb[, canarito := variable %in% nombres_can]
  tb[, tipo := tipo_de(variable)]
  setorder(tb, puesto)
  corte <- tb[canarito == TRUE, mean(puesto) + 2 * sd(puesto)]
  tb[, sobrevive := !canarito & puesto < corte]
  fwrite(tb, arch)

  mejor_can <- tb[canarito == TRUE, min(puesto)]
  cat("\nCanarito", etapa, "- corte (media + 2 desvíos):", round(corte, 1),
      " de", nrow(tb), "puestos. Mejor canarito:", round(mejor_can, 1), "\n")
  cat("Reales mejores que todos los canaritos:", tb[canarito == FALSE & puesto < mejor_can, .N], "\n")
  print(tb[canarito == FALSE, list(reales = .N, sobreviven = sum(sobrevive),
                                   pct = round(100 * mean(sobrevive), 1)), keyby = tipo])
  tb
}
# [Anotación · líneas 757–766] Celda 23 (texto) y celda 24: ejecuta correr_canarito(1) con las variables
#   juzgables y RONDA1, toma las sobrevivientes ordenadas por puesto, cuenta cuántas son e imprime las 30
#   primeras con puesto, variable, Gain y tipo.

#%% celda 23 [texto]
## 5. Canarito 1
Juzga: percentiles + derivadas (sin las forzadas) + las 12 excepciones + **la ronda 1 completa** (todas contra todas entre las originales, calculada solo en 202104).

#%% celda 24 [código]
tabla1 <- correr_canarito(1, c(JUZGABLES_BASE, RONDA1))
sobrev1 <- tabla1[sobrevive == TRUE][order(puesto), variable]
reloj(paste("Sobrevivientes del canarito 1:", length(sobrev1)))
print(tabla1[1:30, list(puesto, variable, gain, tipo)])
# [Anotación · líneas 767–799] Celda 25 (texto): los ejes son las 20 primeras sobrevivientes, y los candidatos
#   son las sobrevivientes que no son interacciones de ronda 1 ni originales. Celda 26: para cada eje y cada
#   candidato genera e__X2__c, e__DIV2__c y c__DIV2__e, sin repetir pares (registro vistos) y sin pares de dos
#   originales, y cuenta las columnas nuevas.

#%% celda 25 [texto]
## 6. Ronda 2 de interacciones
- **Ejes:** las 20 mejores sobrevivientes del canarito 1, de cualquier tipo.
- **Contra:** las sobrevivientes que **no participaron de la ronda 1** (ni interacciones de la ronda 1 ni originales), más los ejes entre sí.
- Para cada par: eje × otra, eje ÷ otra, otra ÷ eje. Cada par se genera una sola vez y se saltean los pares de originales (ya probados en la ronda 1). Sin filtros de redundancia.

#%% celda 26 [código]
ejes <- head(sobrev1, PARAM$n_ejes)
contra <- sobrev1[!grepl("__x__|__div__", sobrev1) & !(sobrev1 %in% ORIGINALES)]
candidatos <- unique(c(contra, ejes))

vistos <- new.env(hash = TRUE)
RONDA2 <- vector("list", length(ejes))
for (i in seq_along(ejes)) {
  e <- ejes[i]
  nuevas <- character(0)
  for (c2 in candidatos) {
    if (c2 == e) next
    if (e %in% ORIGINALES && c2 %in% ORIGINALES) next   # ya probado en la ronda 1
    k <- paste(sort(c(e, c2)), collapse = "|")
    if (exists(k, envir = vistos, inherits = FALSE)) next
    assign(k, TRUE, envir = vistos)
    nuevas <- c(nuevas, paste0(e, "__X2__", c2), paste0(e, "__DIV2__", c2), paste0(c2, "__DIV2__", e))
  }
  RONDA2[[i]] <- nuevas
}
RONDA2 <- unlist(RONDA2)
rm(vistos)

reloj(paste("Ronda 2 - ejes:", length(ejes), " contra:", length(contra), " columnas nuevas:", length(RONDA2)))
print(data.table(eje = ejes, tipo = tipo_de(ejes)))

# [Anotación · líneas 800–818] Celda 27 (texto) y celda 28: ejecuta correr_canarito(2) con las sobrevivientes
#   del canarito 1, las _tend3 y _avg3 y la ronda 2. campos_finales son las forzadas más las sobrevivientes del
#   canarito 2; se guardan en campos_finales.csv o se recuperan si el archivo existe, e imprime su conteo por
#   tipo.
#%% celda 27 [texto]
## 7. Canarito 2 → `campos_finales`
Juzga las sobrevivientes del canarito 1 + las variables del docente (`_tend3`, `_avg3`) + la ronda 2. `campos_finales` = sobrevivientes del canarito 2 + forzadas (`numero_de_cliente`, `foto_mes` y todas las `_lag2`, `_lag3`, `_delta2`, `_delta3`).

#%% celda 28 [código]
tabla2 <- correr_canarito(2, c(sobrev1, VARS_DOCENTE, RONDA2))
sobrev2 <- tabla2[sobrevive == TRUE][order(puesto), variable]

if (file.exists("campos_finales.csv")) {
  campos_finales <- fread("campos_finales.csv")$variable
  cat("Checkpoint: campos_finales.csv recuperado\n")
} else {
  campos_finales <- c(FORZADAS, sobrev2)
  fwrite(data.table(variable = campos_finales), "campos_finales.csv")
}
reloj(paste("Variables finales:", length(campos_finales)))
print(table(tipo_de(campos_finales)))
print(tabla2[1:30, list(puesto, variable, gain, tipo)])

# [Anotación · líneas 819–835] Celda 29 (texto) y celda 30: calcula en todas las filas las interacciones de
#   campos_finales a partir de su nombre, y elimina del dataset las columnas que no están en campos_finales ni
#   en NO_FEATURES, imprimiendo cuántas se eliminan.
#%% celda 29 [texto]
## 8. Interacciones finales en todos los meses
Las interacciones de `campos_finales` (de las dos rondas) se calculan para todas las filas a partir de su nombre. Después se borran las originales en crudo (menos las 12 excepciones) y todo lo que no quedó en `campos_finales`.

#%% celda 30 [código]
inter_finales <- grep("__x__|__div__|__X2__|__DIV2__", campos_finales, value = TRUE)
reloj(paste("Calculando", length(inter_finales), "interacciones en todas las filas"))
operando <- nuevo_operando(seq_len(nrow(dataset)))
for (nm in inter_finales) dataset[, (nm) := valor_col(nm, seq_len(nrow(dataset)), operando)]
rm(operando); gc(verbose = FALSE)

if (!all(campos_finales %in% names(dataset))) stop("Faltan variables de campos_finales en el dataset")
sobran <- setdiff(names(dataset), c(campos_finales, NO_FEATURES))
dataset[, (sobran) := NULL]
gc(verbose = FALSE)
cat("Columnas eliminadas:", length(sobran), " Quedan:", ncol(dataset), "\n")

# [Anotación · líneas 836–844] Celda 31 (texto): si BO_log.txt tiene las 50 iteraciones, no corre nada. Celda
#   32: cuenta las filas de BO_log.txt en n_previas y marca bo_completa cuando son al menos
#   PARAM$bo_iteraciones.
#%% celda 31 [texto]
## 9. Bayesiana (se reusa la de FV4)
Si `BO_log.txt` ya tiene las 50 iteraciones, **no corre nada** y se pasa a las recetas. Si faltaran iteraciones, primero limpia (modelo30 del docente, 20 semillas, sin canaritos, 10% de CONTINUA: el 30% juzga al 70% y se sacan los CONTINUA con prob30 > 0,5) y después corre las que faltan (AUC, 5 semillas).

#%% celda 32 [código]
n_previas <- nrow(fread("BO_log.txt"))
bo_completa <- n_previas >= PARAM$bo_iteraciones
cat("Iteraciones previas:", n_previas, "- bayesiana completa:", bo_completa, "\n")

# [Anotación · líneas 845–878] Si la bayesiana no está completa: lee aporta.csv.gz del checkpoint o, si no
#   existe, entrena 20 modelos modelo30 con el fold 2 de 202103 y 202104 (todas las bajas y 10 % de CONTINUA),
#   predice el fold 1 y promedia. Guarda prob30 y aporta, que vale 1 para las bajas o para prob30 menor o igual
#   a 0,5, y guarda el checkpoint.
if (!bo_completa) {
  # ---- limpieza para la bayesiana (modelo30 del docente, 20 semillas, sin canaritos) ----
  if (file.exists(ck("aporta.csv.gz"))) {
    ck_ap <- leer_ck("aporta.csv.gz")
    pos <- posiciones_ck(ck_ap)
    dataset[, aporta := 0L]
    dataset[pos, aporta := ck_ap$aporta]
  } else {
    idx_f2 <- dataset[, which(foto_mes %in% PARAM$train_prueba & fold == 2L)]
    idx_f1 <- dataset[, which(foto_mes %in% PARAM$train_prueba & fold == 1L)]
    X_f1 <- data.matrix(dataset[idx_f1, campos_finales, with = FALSE])
    prob <- numeric(length(idx_f1))
    semillas30 <- PARAM$semillas[seq_len(PARAM$n_semillas30)]
    for (s in semillas30) {
      set.seed(s, kind = "L'Ecuyer-CMRG")
      az <- runif(length(idx_f2))
      idx_tr <- idx_f2[az <= PARAM$undersampling30 | dataset$clase01[idx_f2] == 1L]
      modelo <- lgb.train(
        data = lgb.Dataset(data.matrix(dataset[idx_tr, campos_finales, with = FALSE]),
                           label = dataset$clase01[idx_tr]),
        params = modifyList(PARAM$lgbm$param30, list(seed = s)))
      prob <- prob + predict(modelo, X_f1)
      rm(modelo)
    }
    prob <- prob / length(semillas30)
    rm(X_f1); gc(verbose = FALSE)
    dataset[, prob30 := NA_real_]
    dataset[idx_f1, prob30 := prob]
    dataset[, aporta := 0L]
    dataset[fold == 1L & (clase01 == 1L | prob30 <= PARAM$umbral_prob30), aporta := 1L]
    idx_ck <- dataset[, which(foto_mes %in% PARAM$train_prueba)]
    guardar_ck(dataset[idx_ck, list(numero_de_cliente = ids_texto(numero_de_cliente),
                                    foto_mes, aporta)], "aporta.csv.gz")
  }
# [Anotación · líneas 879–891] Imprime el conteo del fold 1 por foto_mes, clase_ternaria y aporta, y arma las
#   matrices de la bayesiana: entrenamiento con el fold 1 y aporta igual a 1, validación con el fold 2 de 202103
#   y 202104, el lgb.Dataset de entrenamiento y la última iteración registrada en BO_log.txt.
  print(dataset[fold == 1L, .N, keyby = list(foto_mes, clase_ternaria, aporta)])

  # ---- bayesiana ----
  idx_bo_train <- dataset[, which(foto_mes %in% PARAM$train_prueba & fold == 1L & aporta == 1L)]
  idx_bo_valid <- dataset[, which(foto_mes %in% PARAM$train_prueba & fold == 2L)]
  X_bo_train <- data.matrix(dataset[idx_bo_train, campos_finales, with = FALSE])
  y_bo_train <- dataset$clase01[idx_bo_train]
  X_bo_valid <- data.matrix(dataset[idx_bo_valid, campos_finales, with = FALSE])
  y_bo_valid <- dataset$clase01[idx_bo_valid]
  dtrain_bo <- lgb.Dataset(X_bo_train, label = y_bo_train, free_raw_data = FALSE)

  giter <- fread("BO_log.txt")[, max(iter)]

# [Anotación · líneas 892–912] Estimar_lightgbm() es la función objetivo: combina param_fijos con los
#   hiperparámetros propuestos, entrena con 5 semillas (PARAM$semillas[1:5]), calcula el AUC sobre el fold 2 con
#   cada una, guarda el promedio como una fila de BO_log.txt con su número de iteración y devuelve la métrica.
  Estimar_lightgbm <- function(xs) {
    t0 <- Sys.time()
    giter <<- giter + 1
    param <- modifyList(PARAM$lgbm$param_fijos, xs)
    semillas_bo <- PARAM$semillas[seq_len(PARAM$bo_semillas)]
    aucs <- c()
    for (s in semillas_bo) {
      param$seed <- s
      modelo <- lgb.train(data = dtrain_bo, params = param)
      aucs <- c(aucs, auc(y_bo_valid, predict(modelo, X_bo_valid)))
      rm(modelo)
    }
    xx <- param
    xx$seed <- paste(semillas_bo, collapse = "_")
    xx$iter <- giter
    xx$metrica <- mean(aucs)
    loguear(xx, "BO_log.txt")
    cat("  iteración", giter, "-", round(difftime(Sys.time(), t0, units = "mins"), 1), "minutos\n")
    set.seed(PARAM$semilla_primigenia, kind = "L'Ecuyer-CMRG")
    return(list(metrica = xx$metrica))
  }
# [Anotación · líneas 913–941] Define ObjectiveRFun con dominio PARAM$hs y criterio de maximizar, la instancia
#   con 50 evaluaciones y el optimizador mbo con bayesopt_ego, regr.km de DiceKriging, función de adquisición EI
#   y búsqueda aleatoria de 1.000 puntos por iteración. Carga en la instancia las evaluaciones previas de
#   BO_log.txt.

  objective <- ObjectiveRFun$new(
    fun= Estimar_lightgbm,
    domain= PARAM$hs,
    codomain= ps(metrica = p_dbl(tags = "maximize")),
    id= "BO_lightgbm"
  )
  instance <- OptimInstanceBatchSingleCrit$new(
    objective= objective,
    terminator= trm("evals", n_evals = PARAM$bo_iteraciones)
  )
  optimizer <- opt("mbo",
    loop_function = bayesopt_ego,
    surrogate= srlrn(lrn("regr.km", optim.method = "BFGS", nugget.estim = TRUE,
                         control= list(trace = FALSE))),
    acq_function= acqf("ei"),
    acq_optimizer= acqo(
      optimizer  = opt("random_search", batch_size = 1000),
      terminator = trm("evals", n_evals = 1000))
  )
  tb_BO_previo <- fread("BO_log.txt")
  if (nrow(tb_BO_previo) > 0) {
    instance$archive$add_evals(
      xdt = tb_BO_previo[, list(num_iterations = as.integer(num_iterations),
                                num_leaves = as.integer(num_leaves),
                                min_sum_hessian_in_leaf = as.double(min_sum_hessian_in_leaf))],
      ydt = tb_BO_previo[, list(metrica = as.double(metrica))])
  }

# [Anotación · líneas 942–948] Si la bayesiana no está completa, ejecuta la optimización y libera memoria. Si
#   ya tiene 50 iteraciones, imprime que se usan las recetas de BO_log.txt de FV4 y no entrena nada.
  reloj("Comienza la bayesiana")
  bayesiana_salida <- optimizer$optimize(instance)
  reloj("Terminó la bayesiana")
  rm(X_bo_train, X_bo_valid, dtrain_bo); gc(verbose = FALSE)
} else {
  cat("Bayesiana completa: se usan las recetas de BO_log.txt (FV4)\n")
}
# [Anotación · líneas 949–969] Celda 33: lee BO_log.txt, ordena por metrica de mayor a menor y toma las
#   primeras PARAM$n_recetas combinaciones únicas de num_iterations, num_leaves, min_sum_hessian_in_leaf y
#   metrica, numeradas. El comentario de la línea 951 dice 10 mejores, pero la cantidad la define
#   PARAM$n_recetas, que vale 5; guarda recetas.csv. Celda 34 (texto) describe las funciones de limpieza y
#   ensamble.

#%% celda 33 [código]
# las 10 mejores recetas de BO_log.txt
tb_bayesiana <- fread("BO_log.txt")
setorder(tb_bayesiana, -metrica)
recetas <- head(unique(tb_bayesiana[, list(num_iterations = as.integer(num_iterations),
                                           num_leaves = as.integer(num_leaves),
                                           min_sum_hessian_in_leaf = as.double(min_sum_hessian_in_leaf),
                                           metrica)]), PARAM$n_recetas)
recetas[, receta := .I]
fwrite(recetas, "recetas.csv")
print(recetas)

#%% celda 34 [texto]
## 10. Limpieza cruzada y ensamble de recetas (funciones)

**`limpiar_cruzado(meses)`:** divide las filas de esos meses en dos mitades (estratificadas por clase). Un modelo30 entrenado con la mitad 1 (20 semillas, 10% de CONTINUA) juzga a la mitad 2, y viceversa. Los CONTINUA con `prob30` promedio > 0,5 quedan afuera. Las bajas se conservan todas. Usa `campos_finales`, sin canaritos.

**`entrenar_ensamble(idx_train, idx_pred)`:** entrena un modelo por receta con las filas indicadas, sin undersampling, y promedia las probabilidades sobre `idx_pred`.

#%% celda 35 [código]
# [Anotación · líneas 970–1002] limpiar_cruzado(meses): toma las filas de esos meses, las parte en dos mitades
#   estratificadas (línea 972), entrena para cada mitad 20 modelos modelo30 con la otra mitad y promedia sus
#   probabilidades. Devuelve aporta: 1 para las bajas y para las CONTINUA con probabilidad promedio menor o
#   igual a 0,5, y 0 en el resto.
limpiar_cruzado <- function(meses) {
  idx <- dataset[, which(foto_mes %in% meses)]
  mitad <- partir_mitades(idx, PARAM$semilla_primigenia + 1)
  prob <- numeric(length(idx))
  semillas30 <- PARAM$semillas[seq_len(PARAM$n_semillas30)]

  for (h in 1:2) {
    idx_eval <- idx[mitad == h]
    idx_otra <- idx[mitad != h]
    X_eval <- data.matrix(dataset[idx_eval, campos_finales, with = FALSE])
    acum <- numeric(length(idx_eval))
    for (i in seq_along(semillas30)) {
      s <- semillas30[i]
      set.seed(s, kind = "L'Ecuyer-CMRG")
      az <- runif(length(idx_otra))
      idx_tr <- idx_otra[az <= PARAM$undersampling30 | dataset$clase01[idx_otra] == 1L]
      modelo <- lgb.train(
        data = lgb.Dataset(data.matrix(dataset[idx_tr, campos_finales, with = FALSE]),
                           label = dataset$clase01[idx_tr]),
        params = modifyList(PARAM$lgbm$param30, list(seed = s)))
      acum <- acum + predict(modelo, X_eval)
      rm(modelo)
    }
    prob[mitad == h] <- acum / length(semillas30)
    rm(X_eval); gc(verbose = FALSE)
    reloj(paste("Limpieza cruzada: mitad", h, "lista"))
  }

  aporta <- integer(nrow(dataset))
  aporta[idx] <- as.integer(dataset$clase01[idx] == 1L | prob <= PARAM$umbral_prob30)
  aporta
}

# [Anotación · líneas 1003–1027] entrenar_ensamble(idx_train, idx_pred): para cada receta y cada semilla por
#   receta (una), entrena un LightGBM con param_fijos y con num_iterations, num_leaves y min_sum_hessian_in_leaf
#   de la receta, la semilla PARAM$semillas[n_mod] y sin submuestreo; suma las probabilidades sobre idx_pred y
#   devuelve el promedio por cantidad de modelos.
entrenar_ensamble <- function(idx_train, idx_pred, label_col = "clase01") {
  X_train <- data.matrix(dataset[idx_train, campos_finales, with = FALSE])
  dtrain <- lgb.Dataset(X_train, label = dataset[[label_col]][idx_train], free_raw_data = FALSE)
  rm(X_train)
  X_pred <- data.matrix(dataset[idx_pred, campos_finales, with = FALSE])

  pred <- numeric(nrow(X_pred))
  n_mod <- 0
  for (r in seq_len(nrow(recetas))) {
    for (k in seq_len(PARAM$semillas_por_receta)) {
      n_mod <- n_mod + 1
      param <- modifyList(PARAM$lgbm$param_fijos, list(
        num_iterations = recetas$num_iterations[r],
        num_leaves = recetas$num_leaves[r],
        min_sum_hessian_in_leaf = recetas$min_sum_hessian_in_leaf[r],
        seed = PARAM$semillas[n_mod]))
      modelo <- lgb.train(data = dtrain, params = param)
      pred <- pred + predict(modelo, X_pred)
      rm(modelo); gc(verbose = FALSE)
      reloj(paste("Receta", r, "semilla", k, "lista"))
    }
  }
  pred / n_mod
}

# [Anotación · líneas 1028–1047] Celda 36 (texto) describe la prueba, que la celda 37 sólo ejecuta si
#   PARAM$hacer_prueba es TRUE. Celda 37: recupera o calcula aporta_prueba con limpiar_cruzado sobre 202103 y
#   202104, guarda su checkpoint y cuenta las filas por clase y aporta_prueba.
#%% celda 36 [texto]
## 11. Prueba sobre 202106 (SALTEADA por tiempo: `PARAM$hacer_prueba = FALSE`)
Si se activa: limpieza cruzada de 202103+202104 y ensamble de recetas entrenado con los dos meses juntos; mide la ganancia en 202106.

#%% celda 37 [código]
if (PARAM$hacer_prueba) {
  if (file.exists(ck("aporta_prueba.csv.gz"))) {
    reloj("Checkpoint: se recupera la limpieza cruzada de la prueba")
    ck_p <- leer_ck("aporta_prueba.csv.gz")
    pos <- posiciones_ck(ck_p)
    dataset[, aporta_prueba := 0L]
    dataset[pos, aporta_prueba := ck_p$aporta_prueba]
  } else {
    dataset[, aporta_prueba := limpiar_cruzado(PARAM$train_prueba)]
    idx_ck <- dataset[, which(foto_mes %in% PARAM$train_prueba)]
    guardar_ck(dataset[idx_ck, list(numero_de_cliente = ids_texto(numero_de_cliente),
                                    foto_mes, aporta_prueba)], "aporta_prueba.csv.gz")
  }
  dataset[foto_mes %in% PARAM$train_prueba, .N, keyby = list(foto_mes, clase_ternaria, aporta_prueba)]
  
# [Anotación · líneas 1048–1078] Bloque de la prueba: entrena el ensamble con 202103 y 202104 (aporta_prueba
#   igual a 1), predice 202106 y arma la ganancia acumulada, con +1.072.500 por cada BAJA+2 y -27.500 por cada
#   registro de otra clase, en cada corte de 8.000 a 15.000 cada 500; guarda ganancia_prueba_202106.csv. Con
#   FALSE sólo imprime que se salteó.
  if (file.exists("ganancia_prueba_202106.csv")) {
    cat("Checkpoint: la prueba ya estaba hecha\n")
    print(fread("ganancia_prueba_202106.csv"))
  } else {
    idx_tr_prueba <- dataset[, which(foto_mes %in% PARAM$train_prueba & aporta_prueba == 1L)]
    idx_prueba    <- dataset[, which(foto_mes %in% PARAM$future_prueba)]
    cat("Entrenamiento de la prueba:", length(idx_tr_prueba), "filas\n")
  
    pred_prueba <- entrenar_ensamble(idx_tr_prueba, idx_prueba)
  
    tb_prueba <- dataset[idx_prueba, list(numero_de_cliente, clase_ternaria)]
    tb_prueba[, prob := pred_prueba]
    tb_prueba[, gan := ifelse(clase_ternaria == "BAJA+2", PARAM$ganancia_acierto, PARAM$ganancia_error)]
    setorder(tb_prueba, -prob)
    tb_prueba[, ganancia_acumulada := cumsum(gan)]
  
    tabla_ganancia <- data.table(envios = PARAM$cortes,
                                 ganancia = tb_prueba$ganancia_acumulada[PARAM$cortes])
    fwrite(tabla_ganancia[, list(envios, ganancia = format(ganancia, scientific = FALSE))],
           "ganancia_prueba_202106.csv")
  
    cat("\nEnvíos\tGanancia\n")
    for (k in seq_len(nrow(tabla_ganancia))) {
      cat(tabla_ganancia$envios[k], "\t", format(tabla_ganancia$ganancia[k], big.mark = ".", scientific = FALSE), "\n")
    }
    cat("\nMejor corte:", tabla_ganancia[which.max(ganancia), envios], "envíos\n")
  }
} else {
  reloj("Prueba sobre 202106 salteada (PARAM$hacer_prueba = FALSE)")
}

# [Anotación · líneas 1079–1096] Celda 38 (texto) define el modelo final como limpieza cruzada de los cuatro
#   meses y ensamble de 10 recetas; el código usa PARAM$n_recetas, que vale 5. Celda 39: recupera aporta_final
#   del checkpoint o llama a limpiar_cruzado sobre 202103 a 202106, guarda el checkpoint y cuenta las filas por
#   foto_mes, clase_ternaria y aporta_final.
#%% celda 38 [texto]
## 12. Modelo final (como FV4: entrena 202103–202106 juntos, predice 202108)
Limpieza cruzada de los 4 meses y ensamble de 10 recetas con todas las filas limpias.

#%% celda 39 [código]
if (file.exists(ck("aporta_final.csv.gz"))) {
  reloj("Checkpoint: se recupera la limpieza cruzada del final")
  ck_f <- leer_ck("aporta_final.csv.gz")
  pos <- posiciones_ck(ck_f)
  dataset[, aporta_final := 0L]
  dataset[pos, aporta_final := ck_f$aporta_final]
} else {
  dataset[, aporta_final := limpiar_cruzado(PARAM$train_final)]
  idx_ck <- dataset[, which(foto_mes %in% PARAM$train_final)]
  guardar_ck(dataset[idx_ck, list(numero_de_cliente = ids_texto(numero_de_cliente),
                                  foto_mes, aporta_final)], "aporta_final.csv.gz")
}
dataset[foto_mes %in% PARAM$train_final, .N, keyby = list(foto_mes, clase_ternaria, aporta_final)]
# [Anotación · líneas 1097–1114] Si no existe prediccion_202108.csv, entrena con las filas de 202103 a 202106
#   con aporta_final igual a 1, predice las filas de 202108 con entrenar_ensamble, arma numero_de_cliente y
#   prob, las ordena de mayor a menor prob y las escribe en un temporal que luego renombra. Si el archivo
#   existe, lo lee.

if (file.exists("prediccion_202108.csv")) {
  cat("Checkpoint: la predicción final ya estaba hecha\n")
  tb_entrega <- fread("prediccion_202108.csv", colClasses = list(character = "numero_de_cliente"))
} else {
  idx_tr_final <- dataset[, which(foto_mes %in% PARAM$train_final & aporta_final == 1L)]
  idx_entrega  <- dataset[, which(foto_mes %in% PARAM$future_final)]
  cat("Entrenamiento final:", length(idx_tr_final), "filas\n")

  pred_final <- entrenar_ensamble(idx_tr_final, idx_entrega)

  tb_entrega <- dataset[idx_entrega, list(numero_de_cliente = ids_texto(numero_de_cliente))]
  tb_entrega[, prob := pred_final]
  setorder(tb_entrega, -prob)
  fwrite(tb_entrega, "prediccion_202108.csv.tmp")
  file.rename("prediccion_202108.csv.tmp", "prediccion_202108.csv")
}

# [Anotación · líneas 1115–1119] Celda 40 (texto): 15 archivos de 8.000 a 15.000 cada 500, una sola columna
#   numero_de_cliente, sin encabezado y con ids enteros. Celda 41: encabezado del bloque de escritura.
#%% celda 40 [texto]
## 13. Archivos para la entrega
15 archivos (8.000 a 15.000 cada 500), una sola columna `numero_de_cliente`, sin encabezado y con ids enteros. Cada archivo se relee y se verifica.

#%% celda 41 [código]
# [Anotación · líneas 1120–1131] Para cada corte n de PARAM$cortes escribe entregas/HT4960-FV8_NNNNN.csv con
#   los primeros n ids, sin encabezado y sin comillas; lo vuelve a leer y verifica que tenga n líneas, que todas
#   sean dígitos y que no haya duplicados; si no cumple, detiene el proceso. Al final escribe el mensaje de
#   cierre en log_FV8.txt.
ids <- ids_texto(tb_entrega$numero_de_cliente)

for (n in PARAM$cortes) {
  archivo <- file.path("entregas", sprintf("%s_%05d.csv", PARAM$experimento, n))
  fwrite(data.table(ids[1:n]), archivo, col.names = FALSE, quote = FALSE)

  lineas <- readLines(archivo)
  ok <- length(lineas) == n && all(grepl("^[0-9]+$", lineas)) && !anyDuplicated(lineas)
  cat(archivo, "-", length(lineas), "filas -", if (ok) "OK" else "ERROR", "\n")
  if (!ok) stop(paste("Problema en", archivo))
}
reloj("FV8 terminada: entregas listas")
```


## Explicaciones del alumno (texto original)

### README.md

> # FV8 — Predicción de bajas (DMEyF, 1° competencia)
>
> Notebook en R (`FV8.ipynb`, experimento `HT4960-FV8`) que entrena con 202103–202106 y predice los clientes de **202108** con mayor probabilidad de ser **BAJA+2**.
>
>
> ---
>
> ## Contenido del repositorio
>
> | Archivo | Para qué |
> |---|---|
> | `FV8.ipynb` | Notebook completa. |
> | `BO_log.txt` | Optimización bayesiana en base a 5 semillas y 50 iteraciones. **Imprescindible**: de acá salen las 5 recetas del ensamble y la receta para ejecutar canaritos. |
> | `campos_finales.csv`, `filtro_canaritos_etapa1.csv`, `filtro_canaritos_etapa2.csv` | *(Opcionales)* Resultado de los canaritos. Si se copian a `exp/HT4960-FV8/`, la notebook los reutiliza y saltea la etapa más cara de cómputo (~8 h). |
>
> ---
>
> ## Cómo correrla
>
> ### 1. Requisitos
>
> - **VM con 256 GB de RAM y 12 vCPU** (se usó `n2-custom-12-262144-ext`, aprovisionamiento *Standard*). Con 96 GB se queda sin memoria en los canaritos: el pico fue de ~117 GB.
> - Disco de arranque de 256 GB.
> - R con kernel de Jupyter `ir`. Los paquetes (`data.table`, `R.utils`, `lightgbm`, `Rcpp`, `mlr3`, `mlr3mbo`, `DiceKriging`, etc.) se instalan solos si faltan. `Rcpp` necesita compilador C++.
>
> ### 2. Archivos en su lugar
>
> ```
> ~/buckets/b1/datasets/competencia_01_crudo.csv     # dataset de la cátedra
> ~/buckets/b1/datasets/FV8.ipynb
> ~/buckets/b1/exp/HT4960-FV4/BO_log.txt             # obligatorio
> ~/buckets/b1/exp/HT4960-FV8/campos_finales.csv     # opcional (saltea canaritos)
> ~/buckets/b1/exp/HT4960-FV8/filtro_canaritos_etapa1.csv   # opcional
> ~/buckets/b1/exp/HT4960-FV8/filtro_canaritos_etapa2.csv   # opcional
> ```
>
> ### 3. Lanzar
>
> ```bash
> cd ~/buckets/b1/datasets
> nohup bash -c '
>   jupyter nbconvert --to notebook --execute FV8.ipynb \
>     --output FV8_ejecutada.ipynb \
>     --ExecutePreprocessor.timeout=-1 \
>     --ExecutePreprocessor.kernel_name=ir ;
>   sudo shutdown -h now
> ' >> ~/buckets/b1/corrida_FV8.log 2>&1 &
> ```
>
> - El avance se sigue en `~/buckets/b1/exp/HT4960-FV8/log_FV8.txt` (cada paso con hora y RAM usada):
>   `tail -f ~/buckets/b1/exp/HT4960-FV8/log_FV8.txt`
> - **Checkpoints:** si la VM se corta, se relanza el mismo comando y retoma desde la última etapa guardada.
> - Al terminar, la VM se apaga sola.
>
>
> ## Qué hace (pipeline)
>
> 1. **Clase ternaria** a partir del dataset crudo (BAJA+1, BAJA+2, CONTINUA). `clase01` = BAJA+1 ∪ BAJA+2.
> 2. **Correcciones:** se eliminan `cprestamos_personales` y `mprestamos_personales`; `ccajas_depositos` de 202105 pasa a NA (dato roto).
> 3. **Percentil por mes** para todas las variables originales (`_pct`): 0 → 0; positivos repartidos en (0, 1]; negativos en [−1, 0); NA → NA. Quedan en crudo 12 variables categóricas/estables (`cliente_vip`, `cliente_edad`, `cliente_antiguedad`, `cproductos`, `ctarjeta_visa`, `ctarjeta_master`, `Master/Visa_delinquency`, `_status`, `_Finiciomora`).
> 4. **Historia:** lags 1–3, diferencias 1–3 y acumulado (t − primer mes) sobre los percentiles y las 12 excepciones. 
> 5. **Tendencia y promedio:** tendencia (`_tend3`, pendiente por cuadrados mínimos) y promedio (`_avg3`) de 3 meses.
> 6. **Ronda 1 de interacciones:** todas contra todas entre las ~150 originales (A×B, A÷B, B÷A): ~33.500 columnas.
> 7. **Canarito 1** (selección de variables):
>    - 20 % de columnas de ruido uniforme ("canaritos");
>    - juez: LightGBM con la mejor receta de la bayesiana, entrenado con **202104 completo**;
>    - importancia por **Gain**; corte en *media + 2 desvíos* del puesto de los canaritos;
> 8. **Ronda 2 de interacciones:** las 20 mejores sobrevivientes (ejes) × las sobrevivientes que no participaron de la ronda 1: 21.870 columnas nuevas, sin repetir pares.
> 9. **Canarito 2** sobre sobrevivientes + ronda 2 + variables del docente → **5.199 variables finales** (AUC de control 0,9185).
> 10. **Limpieza cruzada A/B** de 202103–202106: dos mitades estratificadas; entrenado con una mitad predice la otra. Se descartan los CONTINUA con probabilidad > 0,5. Las bajas nunca se tocan.
> 11. **Ensamble final:** las 5 mejores recetas de `BO_log.txt`, entrenadas con 202103–202106 limpios, sin undersampling; se promedian las probabilidades y se predice 202108.
> 12. **Entregas:** 15 archivos (8.000 a 15.000 envíos cada 500).

