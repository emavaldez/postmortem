# mariofreites — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: mariofreites
- Repositorio: https://github.com/mariofreites/dmeyf-primera-competencia
- Link posteado: https://github.com/mariofreites/dmeyf-primera-competencia
- Commit: d9e572e7acc080910e92c38141158c8b14fbb7ba
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/mariofreites/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/mariofreites.json

## Resumen

La entrega contiene dos notebooks de Python encadenados, un README, un documento de diseño por notebook y una carpeta resultados/ con salidas de las corridas originales. El primero, c9920, arma 760 variables (152 campos originales con lag1, delta_lag1, lag2 y delta_lag2, con ranking con cero fijo por mes), agrega 152 canaritos y elimina las variables que quedan por detrás de la media + 2 desvíos de la posición de los canaritos en la importancia por gain; quedan 128 variables según listas.json. El segundo, c9923, toma esas 128, suma 11 atributos nuevos del mes con sus lags y deltas y agrega promedio y pendiente de 3 observaciones (299 variables según el log), busca num_iterations, num_leaves y min_sum_hessian_in_leaf con Optuna (25 corridas, entrena 202103–202105 y maximiza el AUC de 202106) y, con los valores de la corrida de mayor AUC, entrena zLightGBM de 202103 a 202106 con 60 semillas para predecir 202108. Promedia las probabilidades y escribe un CSV por corte de 9.000 a 15.000 clientes. Según el README, el envío final es el corte de 11.000 (c9923_60sem_corte11000.csv).

**Qué entrega.** Un CSV sin encabezado con 11.000 números de cliente, uno por línea: los de mayor probabilidad promediada sobre 60 semillas (c9923_60sem_corte11000.csv, incluido en resultados/c9923/). Según el README, obtuvo 106,205 en el leaderboard público.

**Cómo se ejecuta.** Según el README: en las máquinas virtuales de Google Cloud de la cátedra, con el bucket montado en ~/buckets/b1, se clona el repositorio y se ejecuta cada notebook completo con nohup y jupyter nbconvert --to notebook --execute: primero 01_c9920_canaritos_asesinos/c9920_CanaritosAsesinos.ipynb (unas 3 horas con 8 hilos) y, cuando termina, en otra máquina, 02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb (unas 6,5 horas con 12 hilos). Cada notebook baja el dataset, compila zLightGBM y al terminar borra la máquina. El envío queda en ~/buckets/b1/exp/c9923/5_cortes/c9923_60sem_corte11000.csv. Atajo: con DMEYF_C9920_DIR apuntando a resultados/c9920, c9923 corre sin ejecutar antes c9920. Con MODO_PRUEBA=1 corre con el 5 % de los clientes en unos 15 minutos, en una subcarpeta prueba/. Si la máquina se corta, el mismo comando retoma desde lo guardado en el bucket.

## Ficha

- **Lenguajes:** Python
- **Modelos:** zLightGBM, LightGBM
- **Clase que entrena:** Binaria: positivo = BAJA+1 o BAJA+2 (toda fila cuya clase ternaria no es CONTINUA). La clase ternaria no se lee del dataset: cada notebook la arma mirando si el cliente aparece uno y dos meses después.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** El modelo final y las búsquedas de hiperparámetros entrenan con todas las filas, sin submuestreo. Sólo el modelo de selección de variables de c9920 usa todas las BAJA+1 y BAJA+2 y el 10 % de CONTINUA de 202105.
- **Calidad de datos:** ccajas_depositos se pone en NA en 202105. Al leer el CSV cada campo se convierte a número y lo no numérico pasa a NA. En los atributos nuevos los infinitos se reemplazan por NA. No se observa en el código otra corrección de variables.
- **Drifting:** Ranking con cero fijo por variable y por mes, aplicado a todas las columnas después de calcular lags, deltas, promedios y pendientes con los valores crudos: 0 queda en 0, NA en NA, positivos en (0, 1] y negativos en [−1, 0), con rango promedio en los empates. Agosto se rankea dentro de agosto.
- **Variables dentro del mes:** 11 atributos: mfondos_pesos_total, ctc_transacciones_total, mtc_saldo_total, mmargen_activo_pasivo y mtc_pagominimo_total (sumas o restas con NA como 0), rtc_saldo_limite y rdigital_trx (cocientes, NA si el denominador es 0 o NA), cproductos_perdidos, tperdio_payroll y tinicio_comision (comparan con la observación anterior del cliente) y mpatrimonio_neto (activos menos deudas).
- **Variables históricas:** lag1 y lag2 (valor de la observación anterior y de dos atrás del mismo cliente) y delta_lag1 y delta_lag2 (actual − lag), para los 152 campos originales en c9920 y para los 11 atributos nuevos en c9923. _avg3 (promedio) y _slope3 (pendiente de mínimos cuadrados contra el mes) sobre las observaciones t−2, t−1 y t con mínimo 2 valores, para los campos base presentes en la lista de 128 y para los 11 nuevos. Según el log de c9923: 128 + 55 + 116 = 299 variables.
- **Selección de variables:** En c9920: con 760 variables y 152 canaritos (20 %) entrena un LightGBM sin el parámetro canaritos sobre 202105, ordena por gain y numera las variables usadas; calcula media y desvío de los números de los canaritos y sobrevive la variable con número menor que media + k desvíos (k = 1 y 2) en al menos 2 de 3 repeticiones. Según listas.json quedan 95 y 128 variables. La regla de decisión (mayor mejora media de ganancia de junio frente a la lista sin eliminar, con t pareado ≥ 2 sobre 5 semillas) elige media_2desvios (128), según el log. c9923 usa esas 128 sin volver a seleccionar. Además, en cada entrenamiento zLightGBM recibe un canarito por variable y no corta por ellos.
- **Optimización de hiperparámetros:** Optuna con TPESampler multivariado, 25 corridas (la primera con los valores de c9920, luego al azar hasta 11 corridas completas y el resto guiadas) sobre num_iterations (64–4.096), num_leaves (16–2.048) y min_sum_hessian_in_leaf (1e-6–1). Cada corrida entrena con 202103–202105 y semilla 101737 y maximiza el AUC de 202106 (positivos BAJA+1 y BAJA+2). El estudio se guarda en SQLite. c9920 hace antes una búsqueda de 21 corridas con TPESampler sobre su lista de 128 variables.
- **Hiperparámetros finales:** Modelo final: zLightGBM (paquete lightgbm 4.6.0 con el núcleo compilado de zlightgbm 4.6.0.99; el LightGBM sin el parámetro canaritos sólo se usa en la selección de variables de c9920). Según resultados/c9923/mejores_hiperparametros.json: num_iterations 3304, num_leaves 1125, min_sum_hessian_in_leaf 0,5947 (corrida 20, con 1.580 árboles registrados). Fijos en el código: objective binary, boosting gbdt, learning_rate 0,005, feature_fraction 0,5, feature_fraction_bynode 0,2, min_data_in_leaf 0, max_bin 31, feature_pre_filter False, force_col_wise True y canaritos igual a la cantidad de variables.
- **Semillas:** 60 semillas para agosto: las 10 escritas en el código (101737, 303011, 602909, 707717, 906007, 568318, 641463, 591763, 616818, 193376) y 50 primos de 6 cifras generados con numpy.random.default_rng(20261009). La búsqueda usa la semilla 101737 y la referencia de junio usa 101737, 303011 y 602909. Cada semilla fija también las columnas de canaritos.
- **Cantidad de semillas:** 60
- **Ensamble:** Promedio de las probabilidades de agosto de las 60 semillas del mismo modelo (mismas variables e hiperparámetros).
- **Corte:** Cantidad fija: los 11.000 clientes de mayor probabilidad promedio. El notebook escribe 13 archivos (9.000 a 15.000 de a 500) con la ganancia suavizada de junio de cada corte. Según el README, se enviaron al bot los cortes 10.500, 11.000, 11.500 y 12.000 y se eligió 11.000 por ser el comienzo de una meseta de la ganancia de junio (11.000 a 13.500) y el de mayor puntaje público de los cuatro.
- **Validación:** 202106 como mes de validación. Las búsquedas entrenan con 202103–202105 y miden el AUC de junio con BAJA+1 y BAJA+2 como positivos; se registran además la average precision con sólo BAJA+2 y la ganancia suavizada (media móvil centrada de 501 posiciones sobre la ganancia acumulada, con +1,0725 por BAJA+2 y −0,0275 por el resto). En c9920 las listas de variables se comparan en junio con 5 semillas y t pareado sobre la ganancia máxima suavizada. La referencia de junio promedia 3 semillas y da la ganancia por corte.
- **Salidas:** c9923 escribe en su carpeta de resultados: log.txt, variables.json, 2_bayesiana/ (estudio.db, corridas.csv, mejores_hiperparametros.json y las predicciones de junio de cada corrida), 3_referencia_junio/ (predicciones de junio, junio_ensamble.npy y ganancia_junio_por_corte.csv), 4_agosto/ (ids_agosto.npy, un .npy y un .json por semilla y probabilidades_agosto.csv.gz), 5_cortes/ (13 CSV c9923_<semillas>sem_corte<corte>.csv) y cortes.csv. El repositorio incluye en resultados/c9923 el envío c9923_60sem_corte11000.csv, corridas.csv, cortes.csv, ganancia_junio_por_corte.csv, log.txt y mejores_hiperparametros.json, y en resultados/c9920 las listas de variables, los valores elegidos y el log.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: no
- Entorno declarado: Según el README: máquinas virtuales de Google Cloud de la cátedra con el bucket montado en ~/buckets/b1; c9920 corrió con 8 hilos y c9923 en una máquina de 96 GB de RAM y 12 vCPU; unas 9,5 horas entre los dos; Optuna 5.0.0. Los notebooks instalan lightgbm==4.6.0 y compilan zlightgbm 4.6.0.99; Optuna se instala sin versión fija. No hay archivo de dependencias y no se declaran versiones de Python, numpy ni pandas. Fuera de Google Cloud los notebooks usan carpetas dentro del repositorio (outputs/ y data/) o las que indiquen DMEYF_OUT_DIR, DMEYF_DATA_DIR y DMEYF_C9920_DIR.

## Pasos del camino de la entrega

1. **Lectura del dataset y clase ternaria.** Cada notebook baja competencia_01_crudo.csv si no está, arma la clase ternaria (CONTINUA, BAJA+1, BAJA+2) a partir de la presencia del cliente en los dos meses siguientes y carga en memoria las filas de 202103 a 202108 con los 152 campos como float32. ccajas_depositos se pone en NA en 202105. (`01_c9920_canaritos_asesinos/c9920_CanaritosAsesinos.ipynb` líneas 304–385; `02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb` líneas 325–406)
2. **Lags, deltas y ranking con cero fijo (c9920).** c9920 arma 760 variables: los 152 campos y, para la observación anterior y la de dos atrás de cada cliente, el valor (lag) y la diferencia con el actual (delta). Después reemplaza cada columna, dentro de cada mes, por su ranking con cero fijo: 0 queda en 0, positivos en (0, 1] y negativos en [−1, 0). (`01_c9920_canaritos_asesinos/c9920_CanaritosAsesinos.ipynb` líneas 387–431; `01_c9920_canaritos_asesinos/c9920_CanaritosAsesinos.ipynb` líneas 489–517)
3. **Selección con canaritos (c9920).** Tres repeticiones (semillas 101737, 303011 y 602909): con las filas de 202105 (todas las BAJA+1 y BAJA+2 y el 10 % de CONTINUA) y 152 columnas al azar agregadas, entrena un LightGBM sin el parámetro canaritos (2.848 iteraciones, 71 hojas), ordena las variables por gain y numera las usadas. Calcula media y desvío de los números de los canaritos y los puntos media + 1 desvío y media + 2 desvíos. (`01_c9920_canaritos_asesinos/c9920_CanaritosAsesinos.ipynb` líneas 648–742)
4. **Listas de variables (c9920).** En cada repetición sobrevive la variable real con número menor que el punto de corte; entra en la lista la que sobrevive en al menos 2 de las 3 repeticiones. Se guardan en listas.json las listas sin_eliminar (760), media_1desvio (95) y media_2desvios (128). (`01_c9920_canaritos_asesinos/c9920_CanaritosAsesinos.ipynb` líneas 750–791; `resultados/c9920/listas.json` líneas 861–990)
5. **Comparación de listas y regla de decisión (c9920).** Cada lista se entrena con zLightGBM (1.155 iteraciones, 126 hojas, min_sum_hessian_in_leaf 0,094, un canarito por variable) sobre 202103–202105 y se mide en 202106 con 5 semillas, las mismas para todas. Se calcula la diferencia de ganancia máxima suavizada contra sin_eliminar semilla por semilla y su t pareado; gana la lista de mayor mejora media positiva con t ≥ 2. Según el log, la elegida es media_2desvios. (`01_c9920_canaritos_asesinos/c9920_CanaritosAsesinos.ipynb` líneas 808–838; `01_c9920_canaritos_asesinos/c9920_CanaritosAsesinos.ipynb` líneas 848–887; `resultados/c9920/log.txt` líneas 20–37)
6. **Búsqueda de hiperparámetros de c9920.** Optuna (TPE) con 21 corridas sobre num_iterations, num_leaves y min_sum_hessian_in_leaf, entrenando 202103–202105 y maximizando el AUC de 202106. La corrida de mayor AUC se guarda en mejores_hiperparametros.json (3981, 675 y 0,468 según el archivo). El notebook sigue con una referencia de junio, 20 semillas de agosto y sus cortes; de eso c9923 sólo lee el promedio de junio, para comparar. (`01_c9920_canaritos_asesinos/c9920_CanaritosAsesinos.ipynb` líneas 897–976; `resultados/c9920/mejores_hiperparametros.json` líneas 1–15; `01_c9920_canaritos_asesinos/c9920_CanaritosAsesinos.ipynb` líneas 984–1087)
7. **Entradas de c9923.** c9923 lee de la carpeta de c9920 la lista media_2desvios (128 variables) y los tres valores de la corrida de mayor AUC de c9920, y verifica que estén dentro de su espacio de búsqueda. (`02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb` líneas 217–236)
8. **Atributos nuevos del mes (c9923).** Con los valores crudos calcula 11 atributos: cinco sumas o restas de montos y cantidades, dos cocientes (saldo de tarjetas sobre límite de compra, transacciones digitales sobre el total de canales), la cantidad de productos perdidos respecto de la observación anterior, dos banderas (dejó de tener transacciones de payroll, empezó a pagar comisión de mantenimiento) y un patrimonio neto (activos menos deudas). (`02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb` líneas 500–550)
9. **Variables históricas y matriz final (c9923).** La lista final junta las 128 variables de c9920, los 11 atributos nuevos con lag1, delta_lag1, lag2 y delta_lag2 (55 columnas) y, para cada campo base presente en las 128 y cada atributo nuevo, el promedio (_avg3) y la pendiente de mínimos cuadrados (_slope3) de las observaciones t−2, t−1 y t, con mínimo 2 valores. Según el log son 299 variables. Se construyen las matrices de 202103–202106 y de 202108, y la clase binaria con positivo = BAJA+1 o BAJA+2. (`02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb` líneas 582–697; `resultados/c9923/log.txt` líneas 13–13)
10. **Ranking con cero fijo (c9923).** Cada una de las columnas se reemplaza, dentro de cada mes de entrenamiento y dentro de agosto, por su ranking con cero fijo, entre −1 y 1. (`02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb` líneas 758–786)
11. **Modelo: zLightGBM con un canarito por variable.** Cada entrenamiento antepone a las variables reales igual cantidad de columnas uniformes al azar y pasa esa cantidad en el parámetro canaritos. Los parámetros fijos son objective binary, learning_rate 0,005, feature_fraction 0,5, feature_fraction_bynode 0,2, min_data_in_leaf 0 y max_bin 31. Si el modelo usa un canarito en algún corte, el notebook corta con error. (`02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb` líneas 255–303; `02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb` líneas 862–906)
12. **Búsqueda de hiperparámetros con Optuna (c9923).** 25 corridas con TPE multivariado: la primera con los valores de c9920, las siguientes al azar hasta completar 11 y el resto guiadas. Cada una entrena con 202103–202105 y semilla 101737, predice 202106 y devuelve el AUC con BAJA+1 y BAJA+2 como positivos; registra también average precision de BAJA+2 y ganancia suavizada. Se toma la corrida de mayor AUC: según mejores_hiperparametros.json, num_iterations 3304, num_leaves 1125 y min_sum_hessian_in_leaf 0,5947. (`02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb` líneas 932–1032; `resultados/c9923/mejores_hiperparametros.json` líneas 1–19; `resultados/c9923/log.txt` líneas 17–42)
13. **Referencia de junio y ganancia por corte.** Con los valores elegidos y las semillas 101737, 303011 y 602909 promedia tres predicciones de 202106 y calcula la ganancia suavizada en cada corte de 9.000 a 15.000, junto a la de c9920 si está disponible. (`02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb` líneas 1040–1084; `resultados/c9923/log.txt` líneas 45–48)
14. **Semillas de agosto.** Para cada una de las 60 semillas (10 escritas en el código y 50 primos generados con una semilla fija) entrena con todas las filas de 202103 a 202106 y los valores elegidos, predice 202108 y guarda las probabilidades. Antes de cada semilla revisa si existe el archivo PARAR. (`02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb` líneas 115–141; `02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb` líneas 1143–1170)
15. **Promedio y archivos por corte.** Después de cada semilla promedia las probabilidades de las semillas guardadas, ordena los clientes de mayor a menor y escribe 13 CSV sin encabezado con los primeros 9.000, 9.500, …, 15.000 números de cliente, además de cortes.csv con la ganancia de junio de cada corte y probabilidades_agosto.csv.gz. (`02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb` líneas 1108–1140)
16. **Corte enviado.** Según el README, se enviaron los cortes 10.500, 11.000, 11.500 y 12.000 y el envío final es el de 11.000 (c9923_60sem_corte11000.csv), con ganancia de junio 400,9 y 106,205 en el leaderboard público. (`README.md` líneas 5–5; `README.md` líneas 20–31)

## Archivos

- `README.md` · explicacion · Markdown · 79 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mariofreites/README.md.txt) — Presentación de la entrega: nombra el envío final (c9923_60sem_corte11000.csv), resume los dos experimentos encadenados y la validación en junio, da la tabla de los cuatro cortes enviados con su ganancia de junio y su puntaje público, la estructura de carpetas, los comandos para reproducir en las máquinas de Google Cloud de la cátedra y notas sobre nombres y reproducibilidad.
- `resultados/c9920/listas.json` · configuracion · JSON · 991 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mariofreites/resultados/c9920/listas.json.txt) — Las tres listas de variables que escribe c9920: sin_eliminar (760), media_1desvio (95) y media_2desvios (128). c9923 lee de este archivo la lista media_2desvios.
- `resultados/c9920/mejores_hiperparametros.json` · configuracion · JSON · 15 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mariofreites/resultados/c9920/mejores_hiperparametros.json.txt) — Corrida de mayor AUC de la búsqueda de c9920: num_iterations 3981, num_leaves 675, min_sum_hessian_in_leaf 0,468, con AUC de junio 0,9235 y sus demás métricas. c9923 usa estos tres valores como primera corrida de su búsqueda.
- `resultados/c9920/log.txt` · secundario · Texto · 88 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mariofreites/resultados/c9920/log.txt.txt) — Log que escribió c9920 en su corrida original (figura como z9920), del 2026-10-10 de 14:16 a 17:09, con 8 hilos: conteos por mes y clase, las tres repeticiones de la selección, las 15 corridas de la comparación de listas, la lista elegida (media_2desvios, 128 variables), las 21 corridas de la búsqueda, la referencia de junio y las 20 semillas de agosto.
- `resultados/c9923/mejores_hiperparametros.json` · configuracion · JSON · 19 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mariofreites/resultados/c9923/mejores_hiperparametros.json.txt) — Corrida de mayor AUC de la búsqueda de c9923 (corrida 20): num_iterations 3304, num_leaves 1125, min_sum_hessian_in_leaf 0,5947, con AUC de junio 0,92455, average precision 0,0710, ganancia máxima suavizada 402,15 en la posición 12.478 y 1.580 árboles. Con estos valores se entrenan las semillas de agosto.
- `resultados/c9923/log.txt` · secundario · Texto · 172 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mariofreites/resultados/c9923/log.txt.txt) — Log que escribió c9923 en su corrida original (figura como z9923), del 2026-10-11 de 04:42 a 11:07, con 12 hilos: tamaño del panel (983.061 filas), 299 variables, las 25 corridas de la búsqueda con AUC, average precision y ganancia de junio, la corrida elegida, la referencia de junio frente a c9920 y las 60 semillas de agosto con la reescritura de cortes después de cada una.
- `02_c9923_variables_nuevas/design.md` · explicacion · Markdown · 56 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mariofreites/02_c9923_variables_nuevas/design.md.txt) — Documento de diseño de c9923: variables (las 128 de c9920, los 11 atributos nuevos con su fórmula, _avg3 y _slope3), pasos (búsqueda, referencia de junio, agosto, apagado), archivos de control para cortar la corrida, cómo retoma y las pruebas hechas antes de la corrida.
- `02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb` · principal · Jupyter (python) · 1181 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mariofreites/02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb.txt) — Notebook que produce el envío: lee la lista de 128 variables y los valores de c9920, agrega 11 atributos nuevos, lags, deltas, promedios y pendientes, aplica ranking con cero fijo, busca hiperparámetros con Optuna validando en 202106 y entrena 60 semillas de zLightGBM sobre 202103–202106 para predecir 202108, con un CSV por corte. Cada sección de código está precedida por una celda de texto del autor.
- `01_c9920_canaritos_asesinos/design.md` · explicacion · Markdown · 35 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mariofreites/01_c9920_canaritos_asesinos/design.md.txt) — Documento de diseño de c9920: la pregunta del experimento, la receta de canaritos, los ocho pasos (datos, selección, listas, comparación, regla de decisión, búsqueda, referencia de junio, agosto), los motivos que da el autor para esas decisiones y el uso de Google Cloud.
- `01_c9920_canaritos_asesinos/c9920_CanaritosAsesinos.ipynb` · principal · Jupyter (python) · 1097 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/mariofreites/01_c9920_canaritos_asesinos/c9920_CanaritosAsesinos.ipynb.txt) — Notebook previo del que c9923 toma la lista de variables y los valores iniciales de su búsqueda: arma 760 variables, las selecciona con canaritos en tres repeticiones, compara las listas en 202106, busca hiperparámetros con Optuna para la lista elegida y genera su propia predicción de 202108 con 20 semillas.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### 02_c9923_variables_nuevas/c9923_VariablesNuevas.ipynb

Notebook que produce el envío: lee la lista de 128 variables y los valores de c9920, agrega 11 atributos nuevos, lags, deltas, promedios y pendientes, aplica ranking con cero fijo, busca hiperparámetros con Optuna validando en 202106 y entrena 60 semillas de zLightGBM sobre 202103–202106 para predecir 202108, con un CSV por corte. Cada sección de código está precedida por una celda de texto del autor.

````python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

#%% celda 1 [texto]
# c9923 — c9920 + variables nuevas, con bayesiana propia

**Qué es:** el modelo de `c9920` (su lista de 128 variables, zLightGBM con canaritos 1 a 1, los fijos del profesor) con **variables nuevas** y una **optimización bayesiana propia**, porque con otras variables el óptimo de hiperparámetros puede moverse. Termina en semillas de agosto listas para el bot y para ensamblar.

**Variables** (todas con los valores crudos de cada mes y después ranking con cero fijo por mes, como el resto):

1. **Base:** las 128 de `c9920` (`media_2desvios`), sin volver a seleccionar.
2. **11 atributos nuevos del mes**, cada uno con lag1, delta_lag1, lag2 y delta_lag2 (55 columnas): `mfondos_pesos_total`, `ctc_transacciones_total`, `mtc_saldo_total`, `mmargen_activo_pasivo`, `mtc_pagominimo_total`, `rtc_saldo_limite`, `rdigital_trx`, `cproductos_perdidos`, `tperdio_payroll`, `tinicio_comision`, `mpatrimonio_neto`.
3. **`_avg3` y `_slope3`** (ventana t−2, t−1, t; mínimo 2 valores) para los campos base que aparecen en las 128 y para los 11 nuevos.

Prefijos como en el dataset: `m` monto, `c` cantidad, `t` bandera, `r` ratio. "Mes anterior" es la observación anterior del cliente, igual que en los lags de siempre.

**Pasos** (todo con un solo *Run All*):

1. Datos y variables (igual que `c9920` + las nuevas). Imprime cuántas columnas quedaron.
2. **Bayesiana:** Optuna (TPE multivariado) sobre `num_iterations`, `num_leaves` y `min_sum_hessian_in_leaf`. Entrena marzo a mayo, predice junio, semilla 101737, **maximiza el AUC de junio**. La primera corrida usa los valores de `c9920`. Cada corrida guarda también la *average precision* (solo BAJA+2) y la ganancia.
3. **Referencia de junio:** 3 semillas con los mejores valores, contra la referencia de `c9920` con las mismas semillas.
4. **Agosto:** marzo a junio → agosto con los mejores valores, una semilla tras otra (primero las 10 de `s0004`, después primos), tope `N_SEMILLAS_AGOSTO` = 60. **Después de cada semilla** se rehacen los CSV de cortes (9.000 a 15.000) y las probabilidades del ensamble.
5. Al terminar (o al encontrar `PARAR`), borra la máquina virtual. Todo queda en el bucket.

## Cómo correrlo en la máquina de la cátedra

```bash
cd ~/dmeyf-primera-competencia/02_c9923_variables_nuevas
# 1) prueba corta (~15 min, 5 % de los clientes, escribe en exp/c9923/prueba, no apaga la máquina)
MODO_PRUEBA=1 jupyter nbconvert --to notebook --execute c9923_VariablesNuevas.ipynb --output c9923_prueba.ipynb --ExecutePreprocessor.timeout=-1
# 2) corrida real, en segundo plano (sigue aunque se cierre la terminal o el navegador)
nohup jupyter nbconvert --to notebook --execute c9923_VariablesNuevas.ipynb --output c9923_corrida.ipynb --ExecutePreprocessor.timeout=-1 > c9923_run.txt 2>&1 &
```

- **Seguimiento:** `tail -f ~/buckets/b1/exp/c9923/log.txt`
- **Parar las semillas de agosto:** `touch ~/buckets/b1/exp/c9923/PARAR`, **solo cuando ya empezó agosto** (si se crea antes, agosto no corre ninguna semilla). Antes de cada semilla nueva el notebook mira si existe: si está, no empieza otra, deja los cortes al día y apaga la máquina. La semilla en curso termina primero (se espera como mucho una). Al arrancar una corrida nueva se borra solo.
- **Cortar la bayesiana antes** (si se hace tarde): `touch ~/buckets/b1/exp/c9923/CORTAR_BAYESIANA`. Termina la corrida en curso y sigue con la referencia de junio y agosto con lo mejor que haya. Este archivo no se borra solo (así, si se corta la máquina, al retomar no vuelve a la bayesiana): para una corrida nueva desde cero, borralo.
- **Lo que se manda:** los CSV de `exp/c9923/5_cortes/` siempre tienen todas las semillas terminadas hasta ese momento.
- **Si Google borra la máquina spot:** otra máquina, el mismo comando. Cada corrida, semilla y el estudio de Optuna se guardan en el bucket apenas terminan; saltea lo hecho y sigue.

#%% celda 2 [código]
# [Anotación · líneas 39–58] Importa las bibliotecas (numpy, pandas y módulos estándar), fija el identificador
#   del experimento en c9923 y lee la variable de entorno MODO_PRUEBA. Fuera del modo prueba quedan activadas
#   dos banderas: borrar la máquina virtual al terminar y borrarla si una celda termina con error.
from pathlib import Path
from urllib.request import urlretrieve
import gc
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import warnings

import numpy as np
import pandas as pd

EXP_ID = "c9923"

MODO_PRUEBA = os.environ.get("MODO_PRUEBA", "0") == "1"  # o poner True a mano para probar con *Run All*
APAGAR_AL_TERMINAR = not MODO_PRUEBA  # al final borra la máquina virtual (solo en Google Cloud; los resultados quedan en el bucket)
APAGAR_SI_FALLA = not MODO_PRUEBA  # si una celda falla, borra la máquina para no gastar créditos

# [Anotación · líneas 60–88] Parámetros de datos y de la búsqueda: URL del dataset, meses de entrenamiento
#   final 202103 a 202106, mes a predecir 202108, meses que se leen (202103 a 202108), lags de orden 1 y 2 y
#   cantidad de hilos igual a la de CPU. La lista base es media_2desvios de c9920. La búsqueda entrena con
#   202103–202105 y valida en 202106, con learning_rate 0,005, feature_fraction 0,5, feature_fraction_bynode
#   0,2, min_data_in_leaf 0 y max_bin 31 fijos; el espacio es num_iterations 64–4.096, num_leaves 16–2.048 y
#   min_sum_hessian_in_leaf 1e-6–1, con 25 corridas (11 iniciales), semilla de entrenamiento 101737 y semilla
#   del muestreador 20261011.
# Datos (igual que c9920)
DATA_URL = "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
FIT_MONTHS = [202103, 202104, 202105, 202106]  # semillas de agosto
PREDICT_MONTH = 202108
NEEDED_MONTHS = {202103, 202104, 202105, 202106, 202107, 202108}
LAG_ORDERS = [1, 2]
NUM_THREADS = os.cpu_count() or 4

# Base: c9920
LISTA_C9920 = "media_2desvios"  # la lista del envío c9920c11000

# Bayesiana: entrena marzo a mayo, valida junio
BO_TRAIN_MONTHS = [202103, 202104, 202105]
VALID_MONTH = 202106
LEARNING_RATE = 0.005
FEATURE_FRACTION = 0.50
FEATURE_FRACTION_BYNODE = 0.20
MIN_DATA_IN_LEAF = 0
MAX_BIN = 31
LGB_METRIC = "auc"  # como pide la cátedra; sin conjunto de validación no cambia el modelo
SEARCH_SPACE = {
    "num_iterations": (64, 4096),
    "num_leaves": (16, 2048),
    "min_sum_hessian_in_leaf": (1e-6, 1.0),
}
N_TRIALS = 25  # 1 con los valores de c9920 + 10 al azar + 14 guiadas
N_STARTUP_TRIALS = 11
BO_SEED = 101737
SAMPLER_SEED = 20261011

# [Anotación · líneas 90–103] Semillas de la referencia de junio (101737, 303011, 602909), tope de 60 semillas
#   para agosto, lista de 10 semillas escritas en el código y semilla 20261009 del generador que completa la
#   lista. Ganancia: +1,0725 por cada BAJA+2 y −0,0275 por cada otro registro, suavizada con una ventana de 501
#   posiciones. Cortes de 9.000 a 15.000 de a 500 (13 cortes) y corte de referencia 11.000.
# Referencia de junio
JUNE_SEEDS = [101737, 303011, 602909]  # las de la referencia de junio de c9920

# Agosto
N_SEMILLAS_AGOSTO = 60
SEEDS_S0004 = [101737, 303011, 602909, 707717, 906007, 568318, 641463, 591763, 616818, 193376]
SEED_LIST_RNG = 20261009  # la misma lista de primos de s0005, s0006 y c9920

# Ganancia y cortes
GAIN_BAJA2 = 1.0725
GAIN_OTHER = -0.0275
GAIN_WINDOW = 501
CORTES = list(range(9_000, 15_001, 500))
CORTE_REF = 11_000  # el corte de c9920c11000

# [Anotación · líneas 105–112] En modo prueba reemplaza los parámetros: 5 % de los clientes, num_iterations
#   entre 20 y 80, num_leaves entre 16 y 1.024, 4 corridas (2 iniciales), 3 semillas de agosto, ventana de 51 y
#   cortes de 300, 500 y 700.
PRUEBA_FRACCION_CLIENTES = 0.05
if MODO_PRUEBA:
    SEARCH_SPACE = {"num_iterations": (20, 80), "num_leaves": (16, 1024), "min_sum_hessian_in_leaf": (1e-6, 1.0)}
    N_TRIALS, N_STARTUP_TRIALS = 4, 2
    N_SEMILLAS_AGOSTO = 3
    GAIN_WINDOW = 51
    CORTES = [300, 500, 700]
    CORTE_REF = 500


# [Anotación · líneas 115–141] Define is_prime() y prime_seeds(), que extrae enteros de 6 cifras con
#   numpy.random.default_rng(20261009) y conserva los primos no repetidos. La lista final de semillas son las 10
#   escritas en el código seguidas de 50 primos generados así; un assert exige 60 semillas distintas.
def is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 2
    return True


def prime_seeds(n, exclude, rng_seed=SEED_LIST_RNG, low=100_000, high=999_999):
    """n primos distintos de 6 cifras, siempre en el mismo orden (la lista de s0005, s0006 y c9920)."""
    rng = np.random.default_rng(rng_seed)
    seeds, taken = [], set(exclude)
    while len(seeds) < n:
        candidate = int(rng.integers(low, high + 1))
        if candidate not in taken and is_prime(candidate):
            seeds.append(candidate)
            taken.add(candidate)
    return seeds


FINAL_SEEDS = (SEEDS_S0004 + prime_seeds(max(N_SEMILLAS_AGOSTO - len(SEEDS_S0004), 0), exclude=SEEDS_S0004))[:N_SEMILLAS_AGOSTO]
assert len(set(FINAL_SEEDS)) == len(FINAL_SEEDS) == N_SEMILLAS_AGOSTO

# [Anotación · líneas 143–170] Elige las carpetas. Si existe ~/buckets/b1 y no está definida DMEYF_OUT_DIR,
#   escribe los resultados en ~/buckets/b1/exp/c9923, los temporales en ~/local/c9923, los datos en ~/datasets y
#   busca la entrada de c9920 en ~/buckets/b1/exp/c9920 (o en DMEYF_C9920_DIR). Si no, busca la raíz del
#   repositorio y usa outputs/c9923, data/ y outputs/c9920, modificables por variables de entorno. En modo
#   prueba agrega la subcarpeta prueba/. Crea 2_bayesiana, 3_referencia_junio, 4_agosto y 5_cortes, y define
#   log.txt y los archivos de control PARAR y CORTAR_BAYESIANA.
# Carpetas. En Google Cloud: resultados en el bucket (sobreviven si se borra la máquina) y temporales en el disco local.
BUCKET = Path.home() / "buckets" / "b1"
EN_GCP = BUCKET.is_dir() and "DMEYF_OUT_DIR" not in os.environ
if EN_GCP:
    OUT_DIR = BUCKET / "exp" / EXP_ID
    LOCAL_DIR = Path.home() / "local" / EXP_ID
    DATA_DIR = Path.home() / "datasets"
    C9920_DIR = Path(os.environ.get("DMEYF_C9920_DIR", BUCKET / "exp" / "c9920"))
else:
    cwd = Path.cwd().resolve()
    BASE_DIR = next((p for p in [cwd, *cwd.parents] if (p / "01_c9920_canaritos_asesinos").is_dir()), cwd)  # raíz del repo
    OUT_DIR = Path(os.environ.get("DMEYF_OUT_DIR", BASE_DIR / "outputs" / EXP_ID))
    LOCAL_DIR = OUT_DIR / "local"
    DATA_DIR = Path(os.environ.get("DMEYF_DATA_DIR", BASE_DIR / "data"))
    C9920_DIR = Path(os.environ.get("DMEYF_C9920_DIR", BASE_DIR / "outputs" / "c9920"))
if MODO_PRUEBA:
    OUT_DIR, LOCAL_DIR = OUT_DIR / "prueba", LOCAL_DIR / "prueba"

BO_DIR = OUT_DIR / "2_bayesiana"
JUNE_DIR = OUT_DIR / "3_referencia_junio"
AUG_DIR = OUT_DIR / "4_agosto"
CUTS_DIR = OUT_DIR / "5_cortes"
for folder in (DATA_DIR, OUT_DIR, LOCAL_DIR, BO_DIR, JUNE_DIR, AUG_DIR, CUTS_DIR):
    folder.mkdir(parents=True, exist_ok=True)

LOG_PATH = OUT_DIR / "log.txt"
STOP_FILE = OUT_DIR / "PARAR"  # touch ~/buckets/b1/exp/c9923/PARAR -> no empieza más semillas de agosto
STOP_BO_FILE = OUT_DIR / "CORTAR_BAYESIANA"  # touch ... -> termina la corrida en curso y pasa a junio y agosto


# [Anotación · líneas 173–214] log() imprime cada mensaje y lo agrega con fecha y hora a log.txt. apagar_vm()
#   lanza en un proceso separado el script ~/machina/direct/apagar_vm.sh y después un gcloud compute instances
#   delete con los datos del servidor de metadatos; no hace nada si no está en Google Cloud o el script no
#   existe, y la parte de gcloud se saltea si el nombre de la máquina empieza con desktop o es instance-
#   instalacion. _apagar_si_falla se registra como callback post_run_cell de IPython: ante un error distinto de
#   KeyboardInterrupt lo escribe en el log y, si la bandera está activa, borra la máquina.
def log(*parts):
    """Imprime y además deja la línea en log.txt (en el bucket), por si se cierra el navegador."""
    text = " ".join(str(part) for part in parts)
    print(text, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(time.strftime("%Y-%m-%d %H:%M:%S  ") + text + "\n")


def apagar_vm(motivo):
    """Borra esta máquina virtual con el script de la cátedra (las plantillas spot se borran, no se apagan)."""
    script = Path.home() / "machina" / "direct" / "apagar_vm.sh"
    if not EN_GCP or not script.exists():
        log(f"[apagado] {motivo}: no estoy en una máquina virtual de la cátedra, no apago nada.")
        return
    log(f"[apagado] {motivo}: borrando la máquina virtual. Los resultados quedaron en {OUT_DIR}")
    # Si el script de la cátedra no encuentra el proyecto (fcur_project_id vacío), borra igual con los metadatos de Google (nunca una desktop).
    respaldo = f"""bash {script}
case "$(hostname)" in desktop*|instance-instalacion) exit 0;; esac
MD=http://metadata.google.internal/computeMetadata/v1; H="Metadata-Flavor: Google"
ZONA=$(curl -s -H "$H" $MD/instance/zone)
gcloud --quiet compute instances delete "$(curl -s -H "$H" $MD/instance/name)" --zone="${{ZONA##*/}}" --project="$(curl -s -H "$H" $MD/project/project-id)"
"""
    with open(OUT_DIR / "apagado.txt", "a") as salida:
        subprocess.Popen(["bash", "-c", respaldo], stdout=salida, stderr=subprocess.STDOUT, start_new_session=True)


def _apagar_si_falla(result):
    error = result.error_in_exec
    if error is not None and not isinstance(error, KeyboardInterrupt):
        log(f"[error] {type(error).__name__}: {error}")
        if APAGAR_SI_FALLA:
            apagar_vm("una celda falló")


try:
    _ip = get_ipython()
    for _callback in list(_ip.events.callbacks["post_run_cell"]):
        if getattr(_callback, "__name__", "") == "_apagar_si_falla":
            _ip.events.unregister("post_run_cell", _callback)
    _ip.events.register("post_run_cell", _apagar_si_falla)
except NameError:
    pass


# [Anotación · líneas 217–236] find_input() busca un archivo de c9920 en su subcarpeta o directamente en la
#   carpeta de entrada. Lee listas.json y toma la lista media_2desvios como LIST_A; lee
#   mejores_hiperparametros.json y guarda num_iterations, num_leaves y min_sum_hessian_in_leaf como
#   C9920_VALUES. Verifica que esos valores estén dentro del espacio de búsqueda y, si no, corta con error.
def find_input(name, subfolder):
    """Busca un archivo de c9920 en su subcarpeta del bucket (o directo en la carpeta de entrada)."""
    for path in (C9920_DIR / subfolder / name, C9920_DIR / name):
        if path.exists():
            return path
    raise FileNotFoundError(f"Falta {name} de c9920: tiene que estar en {C9920_DIR / subfolder}")


C9920_LISTS = json.loads(find_input("listas.json", "1_seleccion").read_text(encoding="utf-8"))
if LISTA_C9920 not in C9920_LISTS:
    raise KeyError(f"listas.json no tiene la lista {LISTA_C9920!r}: {list(C9920_LISTS)}")
LIST_A = list(C9920_LISTS[LISTA_C9920])
_c9920_best = json.loads(find_input("mejores_hiperparametros.json", "3_bayesiana").read_text(encoding="utf-8"))["valores"]
C9920_VALUES = {"num_iterations": int(_c9920_best["num_iterations"]), "num_leaves": int(_c9920_best["num_leaves"]),
                "min_sum_hessian_in_leaf": float(_c9920_best["min_sum_hessian_in_leaf"])}
if MODO_PRUEBA:
    C9920_VALUES = {**C9920_VALUES, "num_iterations": 60, "num_leaves": min(C9920_VALUES["num_leaves"], 1024)}
for _key, (_low, _high) in SEARCH_SPACE.items():
    if not _low <= C9920_VALUES[_key] <= _high:
        raise ValueError(f"El valor de c9920 {_key} = {C9920_VALUES[_key]} cae fuera del rango {(_low, _high)}")

# [Anotación · líneas 238–247] Borra un archivo PARAR que haya quedado de una corrida anterior y escribe en el
#   log la configuración: modo, carpetas, lista base, valores de c9920, cantidad de corridas y de semillas.
if STOP_FILE.exists():  # un PARAR viejo frenaría agosto apenas empieza: se borra al arrancar
    STOP_FILE.unlink()
    print("Había un PARAR de una corrida anterior: lo borré.")

log("=" * 70)
log(f"{EXP_ID} | modo prueba: {MODO_PRUEBA} | Google Cloud: {EN_GCP} | hilos: {NUM_THREADS}")
log("Resultados:", OUT_DIR, "| datos:", DATA_DIR, "| entrada de c9920:", C9920_DIR)
log(f"Base: {LISTA_C9920} ({len(LIST_A)} variables) | valores de c9920 (primera corrida): {C9920_VALUES}")
log(f"Bayesiana: {N_TRIALS} corridas, {SEARCH_SPACE} | agosto: hasta {N_SEMILLAS_AGOSTO} semillas")
log(f"Para parar agosto: touch {STOP_FILE} | para cortar la bayesiana: touch {STOP_BO_FILE}")

#%% celda 3 [texto]
## Instalación de zLightGBM y Optuna (igual que `c9920`)

zLightGBM no es un paquete de Python: se compila su núcleo C++ y se coloca dentro del paquete `lightgbm==4.6.0`, en `~/zlgb` (unos minutos, una vez por máquina). Con `canaritos = n`, nunca corta por las primeras n columnas.

#%% celda 4 [código]
# [Anotación · líneas 255–287] Arma un script de bash que baja zlightgbm_4.6.0.99.tar.gz, compila sus fuentes
#   C++ con g++ (-O3, OpenMP) en lib_lightgbm.so, instala lightgbm==4.6.0 en una carpeta aparte y reemplaza su
#   biblioteca por la compilada, todo en ~/zlgb (o en ZLGB_DIR). Lo ejecuta sólo si la biblioteca no existe.
#   Pone esa carpeta primera en sys.path, importa lightgbm y corta con error si el módulo se cargó desde otro
#   lugar.
ZLGB_URL = "https://storage.googleapis.com/open-courses/dmeyf2025-e4a2/zlightgbm_4.6.0.99.tar.gz"
BUILD_SCRIPT = r"""
set -euo pipefail
TARGET="$1"
WORK="$TARGET"_build
mkdir -p "$WORK" && cd "$WORK"
curl -sSfLO {url}
tar xzf zlightgbm_4.6.0.99.tar.gz
S=zlightgbm/src
FILES=$(find $S/src -name '*.cpp' -not -path '*/cuda/*' -not -name lightgbm_R.cpp -not -name main.cpp | grep -v 'gpu_tree_learner\|cuda')
g++ -O3 -std=c++17 -fPIC -shared -fopenmp -DUSE_SOCKET -DMM_MALLOC -DMM_PREFETCH -DFMT_HEADER_ONLY \
  -I$S/include -I$S/external_libs/fmt/include -I$S/external_libs/fast_double_parser/include \
  $FILES -o lib_lightgbm.so
"{python}" -m pip install -q "lightgbm==4.6.0" --target "$WORK/pkg" --no-deps
rm -rf "$TARGET" && mkdir -p "$TARGET"
cp -r "$WORK/pkg/lightgbm" "$TARGET/lightgbm"
cp "$WORK/lib_lightgbm.so" "$TARGET/lightgbm/lib/lib_lightgbm.so"
""".format(url=ZLGB_URL, python=sys.executable)

ZLGB_DIR = Path(os.environ.get("ZLGB_DIR", Path.home() / "zlgb"))
if not (ZLGB_DIR / "lightgbm" / "lib" / "lib_lightgbm.so").exists():
    log("Compilando zlightgbm en", ZLGB_DIR, "(tarda unos minutos)...")
    start = time.perf_counter()
    subprocess.run(["bash", "-c", BUILD_SCRIPT, "build", str(ZLGB_DIR)], check=True)
    log(f"zlightgbm compilado en {(time.perf_counter() - start) / 60:.1f} min")

if "lightgbm" in sys.modules and not Path(sys.modules["lightgbm"].__file__).resolve().is_relative_to(ZLGB_DIR.resolve()):
    raise RuntimeError("El kernel ya tiene cargado otro lightgbm. Reiniciá el kernel y volvé a ejecutar.")
sys.path.insert(0, str(ZLGB_DIR))
import lightgbm as lgb

if not Path(lgb.__file__).resolve().is_relative_to(ZLGB_DIR.resolve()):
    raise RuntimeError(f"Se cargó lightgbm desde {lgb.__file__}, no desde {ZLGB_DIR}.")

# [Anotación · líneas 289–303] Prueba con datos sintéticos (20.000 filas, 10 columnas uniformes adelante y 10
#   normales): entrena 20 rondas con y sin el parámetro canaritos = 10 y exige que con el parámetro haya 0
#   cortes en las primeras 10 columnas y sin él al menos uno; si no se cumple, corta con error.
# Prueba: con canaritos adelante, zlightgbm nunca los usa; sin el parámetro, sí (LightGBM común).
_rng = np.random.default_rng(0)
_X = _rng.normal(size=(20_000, 10))
_y = ((_X[:, 0] + _X[:, 1] * _X[:, 2] + _rng.normal(size=20_000) * 2) > 1).astype(int)
_Xc = np.hstack([_rng.uniform(size=(20_000, 10)), _X])
_params = dict(objective="binary", num_leaves=256, min_data_in_leaf=5, learning_rate=0.05,
               verbose=-1, seed=1, num_threads=NUM_THREADS)
_plain = lgb.train(_params, lgb.Dataset(_Xc, label=_y), num_boost_round=20)
_canary = lgb.train({**_params, "canaritos": 10}, lgb.Dataset(_Xc, label=_y), num_boost_round=20)
_splits_plain = int(_plain.feature_importance("split")[:10].sum())
_splits_canary = int(_canary.feature_importance("split")[:10].sum())
if _splits_canary != 0 or _splits_plain == 0:
    raise RuntimeError("Este lightgbm no parece ser zlightgbm: el parámetro canaritos no tuvo efecto.")
del _rng, _X, _y, _Xc, _plain, _canary
log(f"zlightgbm OK ({lgb.__file__}): cortes en canaritos sin el parámetro {_splits_plain}, con el parámetro 0")

# [Anotación · líneas 305–315] Importa Optuna (lo instala con pip, sin versión fija, si no está), baja su
#   nivel de mensajes a WARNING, silencia ExperimentalWarning y escribe la versión en el log.
try:
    import optuna
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "optuna"], check=True)
    import importlib
    importlib.invalidate_caches()
    import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore", category=optuna.exceptions.ExperimentalWarning)
from optuna.trial import TrialState
log("Optuna", optuna.__version__)

#%% celda 5 [texto]
## Datos (igual que `c9920`)

- **Clase ternaria:** se arma con todas las fotos (CONTINUA, BAJA+1, BAJA+2). Julio y agosto quedan sin clase. Positivos: BAJA+1 y BAJA+2.
- `ccajas_depositos` en NA en 202105. Sin undersampling.
- En modo prueba se usa el 5 % de los clientes (siempre los mismos).

#%% celda 6 [código]
# [Anotación · líneas 325–332] Busca competencia_01_crudo.csv en la carpeta de datos (acepta también el nombre
#   comptetencia_01_crudo.csv); si no está, lo baja de DATA_URL a un archivo temporal y lo renombra.
data_start = time.perf_counter()
RAW_PATH = next((p for p in [DATA_DIR / "competencia_01_crudo.csv", DATA_DIR / "comptetencia_01_crudo.csv"] if p.exists()), None)
if RAW_PATH is None:
    RAW_PATH = DATA_DIR / "competencia_01_crudo.csv"
    log("Bajando el dataset a", RAW_PATH)
    urlretrieve(DATA_URL, RAW_PATH.with_suffix(".tmp"))
    os.replace(RAW_PATH.with_suffix(".tmp"), RAW_PATH)
log("Dataset:", RAW_PATH, f"({RAW_PATH.stat().st_size / 2**20:.0f} MB)")

# [Anotación · líneas 334–356] Arma la clase ternaria con todos los meses del archivo. Convierte foto_mes a un
#   número de mes corrido (año × 12 + mes), ordena por cliente y obtiene los dos períodos siguientes de cada
#   cliente. Marca CONTINUA los registros anteriores al penúltimo período; BAJA+1 los anteriores al último cuyo
#   período siguiente falta o no es el mes consecutivo; BAJA+2 los anteriores al penúltimo que tienen el mes
#   siguiente y no el subsiguiente. Las asignaciones posteriores pisan a las anteriores. El último período queda
#   sin clase y el penúltimo sólo recibe BAJA+1 cuando falta el mes siguiente. Devuelve las etiquetas en el
#   orden de filas del CSV.
# Clase ternaria con todas las fotos (idéntico a s0004, s0006 y c9920).
keys = pd.read_csv(RAW_PATH, usecols=["numero_de_cliente", "foto_mes"])
work = keys.copy()
work["_row_id"] = np.arange(len(work), dtype=np.int64)
work["periodo0"] = (work["foto_mes"] // 100) * 12 + work["foto_mes"] % 100
work = work.sort_values(["numero_de_cliente", "periodo0"], kind="mergesort")
periods = work.groupby("numero_de_cliente", sort=False)["periodo0"]
work["periodo1"] = periods.shift(-1)
work["periodo2"] = periods.shift(-2)
last_period = int(work["periodo0"].max())
penultimate_period = last_period - 1
clase = pd.Series(pd.NA, index=work.index, dtype="string")
continua = work["periodo0"] < penultimate_period
baja_1 = (work["periodo0"] < last_period) & (work["periodo1"].isna() | (work["periodo0"] + 1 < work["periodo1"]))
baja_2 = (
    (work["periodo0"] < penultimate_period)
    & (work["periodo0"] + 1 == work["periodo1"])
    & (work["periodo2"].isna() | (work["periodo0"] + 2 < work["periodo2"]))
)
clase.loc[continua] = "CONTINUA"
clase.loc[baja_1] = "BAJA+1"
clase.loc[baja_2] = "BAJA+2"
labels = pd.Series(clase.to_numpy(), index=work["_row_id"].to_numpy()).sort_index().reset_index(drop=True)


# [Anotación · líneas 359–372] release_memory() llama al recolector de basura y a malloc_trim de libc.
#   client_in_sample() devuelve todos los clientes salvo en modo prueba, donde conserva aquellos cuyo número
#   multiplicado por 2654435761, módulo 1.000, es menor que 50 (5 %).
def release_memory():
    gc.collect()
    try:
        import ctypes
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:
        pass


def client_in_sample(client_ids):
    """Modo prueba: el mismo 5 % de los clientes siempre (por número de cliente)."""
    if not MODO_PRUEBA:
        return np.ones(len(client_ids), dtype=bool)
    return (np.asarray(client_ids, dtype=np.int64) * 2654435761 % 1000) < PRUEBA_FRACCION_CLIENTES * 1000


# [Anotación · líneas 375–403] Lee el encabezado y toma como campos base todas las columnas menos
#   numero_de_cliente, foto_mes y clase_ternaria. Recorre el CSV en bloques de 25.000 filas, conserva las de los
#   meses 202103 a 202108, les asigna la clase por número de fila y convierte cada campo a float32 (lo no
#   numérico pasa a NA). Concatena los bloques en panel_keys (cliente, mes, fila, clase) y en la matriz
#   base_values.
csv_columns = list(pd.read_csv(RAW_PATH, nrows=0).columns)
KEY_COLUMNS = {"numero_de_cliente", "foto_mes", "clase_ternaria", "_row_id"}
base_feature_names = [c for c in csv_columns if c not in KEY_COLUMNS]
n_base = len(base_feature_names)

key_parts, value_parts = [], []
offset = 0
for chunk in pd.read_csv(RAW_PATH, chunksize=25_000, low_memory=False):
    chunk_row_ids = np.arange(offset, offset + len(chunk), dtype=np.int64)
    offset += len(chunk)
    keep = chunk["foto_mes"].isin(NEEDED_MONTHS).to_numpy() & client_in_sample(chunk["numero_de_cliente"].to_numpy())
    if not keep.any():
        continue
    part = pd.DataFrame({
        "numero_de_cliente": chunk["numero_de_cliente"].to_numpy()[keep],
        "foto_mes": chunk["foto_mes"].to_numpy()[keep],
        "_row_id": chunk_row_ids[keep],
    })
    part["clase_ternaria"] = labels.iloc[part["_row_id"].to_numpy()].to_numpy()
    values = np.empty((int(keep.sum()), n_base), dtype=np.float32)
    for j, column in enumerate(base_feature_names):
        values[:, j] = pd.to_numeric(chunk[column], errors="coerce").astype("float32").to_numpy()[keep]
    key_parts.append(part)
    value_parts.append(values)
del chunk, part, values, keys, work, clase, labels
panel_keys = pd.concat(key_parts, ignore_index=True)
base_values = np.concatenate(value_parts)
del key_parts, value_parts
release_memory()

# [Anotación · líneas 405–406] Pone en NA ccajas_depositos en todas las filas de 202105 y verifica que haya
#   152 campos base.
base_values[panel_keys["foto_mes"].eq(202105).to_numpy(), base_feature_names.index("ccajas_depositos")] = np.nan
assert n_base == 152

# [Anotación · líneas 408–426] Para k = 1 y 2 calcula, para cada fila, la posición de la observación k lugares
#   antes del mismo cliente (ordenando por cliente, mes y número de fila) y una máscara que indica si existe.
#   Guarda también el mes de cada fila y su número de mes corrido, que se usa como eje x de la pendiente.
#   Escribe en el log el tamaño del panel.
# Posición de la observación anterior (k = 1) y de dos antes (k = 2) del mismo cliente (idéntico a c9920).
clients = panel_keys["numero_de_cliente"].to_numpy()
order = np.lexsort((panel_keys["_row_id"].to_numpy(), panel_keys["foto_mes"].to_numpy(), clients))
sorted_clients = clients[order]
sorted_positions = np.arange(len(order))
previous = {}
for k in LAG_ORDERS:
    valid_sorted = sorted_positions >= k
    valid_sorted[valid_sorted] = sorted_clients[sorted_positions[valid_sorted] - k] == sorted_clients[valid_sorted]
    position = np.zeros(len(order), dtype=np.int64)
    valid = np.zeros(len(order), dtype=bool)
    position[order] = np.where(valid_sorted, order[np.maximum(sorted_positions - k, 0)], 0)
    valid[order] = valid_sorted
    previous[k] = (position, valid)
del clients, order, sorted_clients, sorted_positions, valid_sorted, position, valid

row_months = panel_keys["foto_mes"].to_numpy()
row_period = ((row_months // 100) * 12 + row_months % 100).astype(np.float64)  # para la pendiente (x = mes)
log(f"Panel: {len(panel_keys)} filas de {sorted(NEEDED_MONTHS)} | {n_base} campos originales")

#%% celda 7 [texto]
## Atributos nuevos del mes (11)

Con los valores crudos de cada mes, antes de lags y ranking. Sumas: un NA cuenta como 0 (si todos son NA, queda NA). Ratios: NA si el denominador es 0 o NA. Las banderas y `cproductos_perdidos` miran la observación anterior del cliente (sin observación anterior, NA).

| Variable | Cálculo |
|---|---|
| `mfondos_pesos_total` | mcaja_ahorro + mcuenta_corriente + mplazo_fijo_pesos |
| `ctc_transacciones_total` | ctarjeta_visa_transacciones + ctarjeta_master_transacciones |
| `mtc_saldo_total` | Visa_msaldototal + Master_msaldototal |
| `mmargen_activo_pasivo` | mactivos_margen − mpasivos_margen |
| `mtc_pagominimo_total` | Visa_mpagominimo + Master_mpagominimo |
| `rtc_saldo_limite` | mtc_saldo_total / (Visa_mlimitecompra + Master_mlimitecompra) |
| `rdigital_trx` | (homebanking + app) / (homebanking + app + callcenter + cajas + cajeros propios + otros cajeros), transacciones del mes |
| `cproductos_perdidos` | productos activos el mes anterior e inactivos en este (8 productos, tabla en el código) |
| `tperdio_payroll` | 1 si cpayroll_trx anterior > 0 y actual = 0; 0 si los dos existen y no pasa |
| `tinicio_comision` | 1 si mcomisiones_mantenimiento actual > 0 y anterior ≤ 0; 0 si los dos existen y no pasa |
| `mpatrimonio_neto` | (mcuentas_saldo + plazos fijos + inversiones) − (préstamos + saldos de Visa y Master) |

#%% celda 8 [código]
# [Anotación · líneas 448–467] raw() devuelve un campo base como float64. suma() suma columnas tratando NA
#   como 0 y devuelve NA sólo si todos los sumandos son NA. ratio() divide y devuelve NA cuando el denominador
#   es 0 o alguno de los dos valores no es finito.
_base_pos = {name: j for j, name in enumerate(base_feature_names)}


def raw(name):
    return base_values[:, _base_pos[name]].astype(np.float64)


def suma(*arrays):
    """Suma con NA como 0; NA solo si todos son NA."""
    stack = np.column_stack(arrays)
    total = np.nansum(stack, axis=1)
    total[np.isnan(stack).all(axis=1)] = np.nan
    return total


def ratio(numerator, denominator):
    out = np.full(len(numerator), np.nan)
    ok = np.isfinite(numerator) & np.isfinite(denominator) & (denominator != 0)
    out[ok] = numerator[ok] / denominator[ok]
    return out


# [Anotación · líneas 470–490] anterior() devuelve el valor de la observación anterior del cliente (NA si no
#   hay). bandera() convierte una condición en 1/0 y pone NA si falta alguno de los valores que mira.
#   estado_producto() da 1 si alguna de las columnas del producto es mayor que 0, 0 si todas son 0 y NA en el
#   resto de los casos.
_prev_position, _prev_valid = previous[1]


def anterior(values):
    """El valor de la observación anterior del cliente (NA si no hay)."""
    out = values[_prev_position].copy()
    out[~_prev_valid] = np.nan
    return out


def bandera(condition, *arrays):
    """1/0 según la condición; NA si falta alguno de los valores que mira."""
    out = np.where(condition, 1.0, 0.0)
    out[~np.all([np.isfinite(a) for a in arrays], axis=0)] = np.nan
    return out


def estado_producto(columns):
    """1 si alguna fuente > 0; 0 si todas son 0; NA si ninguna es > 0 y alguna es NA."""
    stack = np.column_stack([raw(c) for c in columns])
    return np.where((stack > 0).any(axis=1), 1.0, np.where((stack == 0).all(axis=1), 0.0, np.nan))


# [Anotación · líneas 493–498] Asserts con valores escritos a mano para suma(), ratio() y bandera().
# Pruebas de las funciones con valores a mano
assert np.allclose(suma(np.array([1.0, np.nan, np.nan]), np.array([2.0, 3.0, np.nan])), [3.0, 3.0, np.nan], equal_nan=True)
assert np.allclose(ratio(np.array([1.0, 1.0, np.nan, 2.0]), np.array([4.0, 0.0, 1.0, np.nan])), [0.25, np.nan, np.nan, np.nan], equal_nan=True)
_p, _c = np.array([5.0, 5.0, 0.0, np.nan, 5.0]), np.array([0.0, 3.0, 0.0, 0.0, np.nan])
assert np.allclose(bandera((_p > 0) & (_c == 0), _p, _c), [1, 0, 0, np.nan, np.nan], equal_nan=True)
del _p, _c

# [Anotación · líneas 500–519] Define 8 productos con sus columnas de origen (tarjetas de crédito, sueldo,
#   débitos automáticos, pagos, préstamos, inversiones, seguros y caja de seguridad), 6 columnas de activos y 5
#   de deudas. Verifica que todas las columnas necesarias existan en el dataset y, si falta alguna, corta con
#   KeyError.
PRODUCTOS = {
    "tarjetas_credito": ["ctarjeta_visa", "ctarjeta_master"],
    "sueldo": ["cpayroll_trx", "cpayroll2_trx"],
    "debitos_automaticos": ["ccuenta_debitos_automaticos", "ctarjeta_visa_debitos_automaticos", "ctarjeta_master_debitos_automaticos"],
    "pagos": ["cpagodeservicios", "cpagomiscuentas"],
    "prestamos": ["cprestamos_personales", "cprestamos_prendarios", "cprestamos_hipotecarios"],
    "inversiones": ["cplazo_fijo", "cinversion1", "cinversion2"],
    "seguros": ["cseguro_vida", "cseguro_auto", "cseguro_vivienda", "cseguro_accidentes_personales"],
    "caja_seguridad": ["ccaja_seguridad"],
}
ACTIVOS = ["mcuentas_saldo", "mplazo_fijo_pesos", "mplazo_fijo_dolares", "minversion1_pesos", "minversion1_dolares", "minversion2"]
DEUDAS = ["mprestamos_personales", "mprestamos_prendarios", "mprestamos_hipotecarios", "Visa_msaldototal", "Master_msaldototal"]
_needed = {c for cols in PRODUCTOS.values() for c in cols} | set(ACTIVOS) | set(DEUDAS) | {
    "mcaja_ahorro", "mcuenta_corriente", "ctarjeta_visa_transacciones", "ctarjeta_master_transacciones", "mactivos_margen",
    "mpasivos_margen", "Visa_mpagominimo", "Master_mpagominimo", "Visa_mlimitecompra", "Master_mlimitecompra",
    "chomebanking_transacciones", "cmobile_app_trx", "ccallcenter_transacciones", "ccajas_transacciones", "catm_trx",
    "catm_trx_other", "cpayroll_trx", "mcomisiones_mantenimiento"}
_missing = sorted(_needed - set(base_feature_names))
if _missing:
    raise KeyError(f"Faltan columnas en el dataset: {_missing}")

# [Anotación · líneas 521–532] Calcula valores intermedios: saldo total de tarjetas (Visa + Master),
#   transacciones digitales (homebanking + app), transacciones por todos los canales, cpayroll_trx y
#   mcomisiones_mantenimiento actuales y de la observación anterior. Cuenta los productos perdidos: para cada
#   uno de los 8 productos suma 1 si estaba activo en la observación anterior e inactivo en la actual, y deja NA
#   si no hay observación anterior. El patrimonio es activos menos deudas con NA como 0, y NA si ambos son NA.
mtc_saldo = suma(raw("Visa_msaldototal"), raw("Master_msaldototal"))
digital = suma(raw("chomebanking_transacciones"), raw("cmobile_app_trx"))
canales = suma(digital, raw("ccallcenter_transacciones"), raw("ccajas_transacciones"), raw("catm_trx"), raw("catm_trx_other"))
payroll, payroll_ant = raw("cpayroll_trx"), anterior(raw("cpayroll_trx"))
comision, comision_ant = raw("mcomisiones_mantenimiento"), anterior(raw("mcomisiones_mantenimiento"))
productos_perdidos = np.zeros(len(base_values))
for _cols in PRODUCTOS.values():
    _estado = estado_producto(_cols)
    productos_perdidos += (anterior(_estado) == 1) & (_estado == 0)
productos_perdidos[~_prev_valid] = np.nan
activos, deudas = suma(*[raw(c) for c in ACTIVOS]), suma(*[raw(c) for c in DEUDAS])
patrimonio = np.where(np.isnan(activos) & np.isnan(deudas), np.nan, np.nan_to_num(activos) - np.nan_to_num(deudas))

# [Anotación · líneas 534–550] Arma los 11 atributos nuevos: mfondos_pesos_total, ctc_transacciones_total,
#   mtc_saldo_total, mmargen_activo_pasivo, mtc_pagominimo_total, rtc_saldo_limite (saldo de tarjetas sobre suma
#   de límites de compra), rdigital_trx (transacciones digitales sobre el total de canales),
#   cproductos_perdidos, tperdio_payroll (cpayroll_trx anterior > 0 y actual = 0), tinicio_comision (comisión de
#   mantenimiento actual > 0 y anterior ≤ 0) y mpatrimonio_neto. Verifica que sean 11 y que no repitan nombres
#   del dataset, los apila en una matriz float32 y reemplaza los infinitos por NA.
NEW_FIELDS = {
    "mfondos_pesos_total": suma(raw("mcaja_ahorro"), raw("mcuenta_corriente"), raw("mplazo_fijo_pesos")),
    "ctc_transacciones_total": suma(raw("ctarjeta_visa_transacciones"), raw("ctarjeta_master_transacciones")),
    "mtc_saldo_total": mtc_saldo,
    "mmargen_activo_pasivo": suma(raw("mactivos_margen"), -raw("mpasivos_margen")),
    "mtc_pagominimo_total": suma(raw("Visa_mpagominimo"), raw("Master_mpagominimo")),
    "rtc_saldo_limite": ratio(mtc_saldo, suma(raw("Visa_mlimitecompra"), raw("Master_mlimitecompra"))),
    "rdigital_trx": ratio(digital, canales),
    "cproductos_perdidos": productos_perdidos,
    "tperdio_payroll": bandera((payroll_ant > 0) & (payroll == 0), payroll_ant, payroll),
    "tinicio_comision": bandera((comision > 0) & (comision_ant <= 0), comision, comision_ant),
    "mpatrimonio_neto": patrimonio,
}
NEW_NAMES = list(NEW_FIELDS)
assert len(NEW_NAMES) == 11 and not set(NEW_NAMES) & set(base_feature_names)
new_values = np.column_stack([v.astype(np.float32) for v in NEW_FIELDS.values()])
new_values[~np.isfinite(new_values)] = np.nan  # nada de infinitos

# [Anotación · líneas 552–572] Controles con assert: rdigital_trx entre 0 y 1, las dos banderas sólo con 0 y
#   1, cproductos_perdidos entre 0 y 8, y las tres variables que miran la observación anterior todas en NA en
#   202103. Muestra una tabla con porcentaje de NA, media, mediana y medias de junio y agosto. Une los 152
#   campos base y los 11 nuevos en field_values y libera los intermedios.
# Controles: proporciones razonables y rangos esperados
_months = pd.Series(row_months)
_check = pd.DataFrame(new_values, columns=NEW_NAMES)
assert np.nanmin(_check["rdigital_trx"]) >= 0 and np.nanmax(_check["rdigital_trx"]) <= 1
assert set(np.unique(_check["tperdio_payroll"].dropna())) <= {0.0, 1.0}
assert set(np.unique(_check["tinicio_comision"].dropna())) <= {0.0, 1.0}
assert np.nanmin(_check["cproductos_perdidos"]) >= 0 and np.nanmax(_check["cproductos_perdidos"]) <= len(PRODUCTOS)
assert _check.loc[_months.eq(202103).to_numpy(), ["cproductos_perdidos", "tperdio_payroll", "tinicio_comision"]].isna().all().all()
_resumen = pd.DataFrame({"NA %": _check.isna().mean() * 100, "media": _check.mean(), "mediana": _check.median()})
_resumen["media junio"] = _check[_months.eq(202106).to_numpy()].mean()
_resumen["media agosto"] = _check[_months.eq(202108).to_numpy()].mean()
display(_resumen.round(4))

del NEW_FIELDS, mtc_saldo, digital, canales, payroll, payroll_ant, comision, comision_ant, productos_perdidos
del activos, deudas, patrimonio, _check, _resumen, _months
field_names = base_feature_names + NEW_NAMES
field_values = np.hstack([base_values, new_values])
field_pos = {name: j for j, name in enumerate(field_names)}
del base_values, new_values
release_memory()
log(f"Atributos nuevos: {NEW_NAMES}")

#%% celda 9 [texto]
## Variables del modelo

- Las 128 de `c9920`, con su mismo cálculo (los lags son el valor de la observación anterior del cliente; el delta, actual − lag).
- Los 11 atributos nuevos con lag1, delta_lag1, lag2 y delta_lag2.
- `_avg3`: promedio de los valores disponibles en t, t−1 y t−2 (mínimo 2). `_slope3`: pendiente de mínimos cuadrados de esos valores contra el mes (mínimo 2). Para los campos base de las 128 y los 11 nuevos.

#%% celda 10 [código]
# [Anotación · líneas 582–601] parse_feature() separa el nombre de una variable en campo, tipo (original, lag,
#   delta, avg3 o slope3) y orden k según su sufijo. expand() genera, para una lista de campos, los nombres del
#   original y de _lag1, _delta_lag1, _lag2 y _delta_lag2.
def parse_feature(name):
    """'campo', 'campo_lag1', 'campo_delta_lag2', 'campo_avg3', 'campo_slope3' -> (campo, tipo, k)."""
    for suffix, kind in (("_avg3", "avg3"), ("_slope3", "slope3")):
        if name.endswith(suffix):
            return name[: -len(suffix)], kind, 0
    for k in LAG_ORDERS:
        if name.endswith(f"_delta_lag{k}"):
            return name[: -len(f"_delta_lag{k}")], "delta", k
        if name.endswith(f"_lag{k}"):
            return name[: -len(f"_lag{k}")], "lag", k
    return name, "original", 0


def expand(fields):
    """Original, lag1, delta_lag1, lag2, delta_lag2 (el orden de c9920)."""
    names = list(fields)
    for k in LAG_ORDERS:
        for field in fields:
            names += [f"{field}_lag{k}", f"{field}_delta_lag{k}"]
    return names


# [Anotación · líneas 604–628] window_stats() recibe los valores y los meses de t−2, t−1 y t y calcula, con
#   los valores disponibles, el promedio y la pendiente de mínimos cuadrados del valor contra el mes. Devuelve
#   NA si hay menos de 2 valores (y pendiente NA si los meses no varían). Sigue un assert con cinco filas
#   escritas a mano.
def window_stats(values, months):
    """values, months: (n, 3) con t−2, t−1, t (NA donde falta). Devuelve promedio y pendiente con mínimo 2 valores."""
    mask = np.isfinite(values)
    count = mask.sum(axis=1)
    safe = np.where(mask, values, 0.0)
    x = np.where(mask, months, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        y_mean = safe.sum(axis=1) / count
        x_mean = x.sum(axis=1) / count
        dx = np.where(mask, months - x_mean[:, None], 0.0)
        dy = np.where(mask, values - y_mean[:, None], 0.0)
        denominator = (dx * dx).sum(axis=1)
        slope = (dx * dy).sum(axis=1) / denominator
    ok = count >= 2
    avg = np.where(ok, y_mean, np.nan)
    slope = np.where(ok & (denominator > 0), slope, np.nan)
    return avg, slope


_v = np.array([[1, 2, 4], [np.nan, 2, 4], [np.nan, np.nan, 4], [3, np.nan, 7], [np.nan, np.nan, np.nan]], dtype=float)
_m = np.array([[1, 2, 3], [1, 2, 3], [1, 2, 3], [1, 2, 3], [1, 2, 3]], dtype=float)
_avg, _slope = window_stats(_v, _m)
assert np.allclose(_avg, [7 / 3, 3, np.nan, 5, np.nan], equal_nan=True), _avg
assert np.allclose(_slope, [1.5, 2, np.nan, 2, np.nan], equal_nan=True), _slope
del _v, _m, _avg, _slope

# [Anotación · líneas 630–643] Verifica que cada nombre de la lista de c9920 corresponda a un campo base. Toma
#   los campos base distintos que aparecen en esa lista más los 11 nuevos como campos con historia. La lista
#   final de variables es: las de c9920 en su orden, los 11 nuevos expandidos con lags y deltas (55 columnas) y
#   un _avg3 y un _slope3 por cada campo con historia. Verifica que no haya nombres repetidos y calcula una
#   huella SHA-1 de 12 caracteres de la lista.
unknown = [n for n in LIST_A if parse_feature(n)[0] not in base_feature_names or parse_feature(n)[1] in ("avg3", "slope3")]
if unknown:
    raise ValueError(f"La lista de c9920 tiene nombres que no reconozco: {unknown[:5]}")
HIST_FIELDS = list(dict.fromkeys(parse_feature(n)[0] for n in LIST_A)) + NEW_NAMES
N_BASE_FIELDS = len(HIST_FIELDS) - len(NEW_NAMES)
NEW_COLUMNS = expand(NEW_NAMES)
HIST_COLUMNS = [f"{f}_avg3" for f in HIST_FIELDS] + [f"{f}_slope3" for f in HIST_FIELDS]
FEATURES = LIST_A + NEW_COLUMNS + HIST_COLUMNS  # las de c9920 primero, en su mismo orden
if len(set(FEATURES)) != len(FEATURES):
    raise ValueError("Hay nombres de variables repetidos")
feature_index = {name: i for i, name in enumerate(FEATURES)}
COLUMNS = list(range(len(FEATURES)))
FEATURES_HASH = hashlib.sha1(",".join(FEATURES).encode()).hexdigest()[:12]
assert len(FEATURES) == len(LIST_A) + 5 * len(NEW_NAMES) + 2 * len(HIST_FIELDS)

# [Anotación · líneas 645–647] Separa las filas de entrenamiento (202103 a 202106, ordenadas por mes) y las de
#   202108.
fit_rows = np.flatnonzero(np.isin(row_months, FIT_MONTHS))
fit_rows = fit_rows[np.argsort(row_months[fit_rows], kind="stable")]
future_rows = np.flatnonzero(row_months == PREDICT_MONTH)


# [Anotación · líneas 650–679] fill_columns() construye, en bloques de 20.000 filas, la matriz de las
#   variables pedidas: el valor actual para las originales, el valor de la observación k lugares antes para los
#   lags (NA si no existe), la resta actual − lag para los deltas, y promedio o pendiente de la ventana (lag2,
#   lag1, actual) con window_stats() para _avg3 y _slope3, calculando cada campo una sola vez por bloque.
def fill_columns(rows, names, block=20_000):
    """Originales, lags y deltas igual que c9920; avg3 y slope3 sobre t−2, t−1, t."""
    specs = [(field_pos[f], kind, k) for f, kind, k in (parse_feature(n) for n in names)]
    out_all = np.empty((len(rows), len(names)), dtype=np.float32)
    for start in range(0, len(rows), block):
        block_rows = rows[start:start + block]
        current = field_values[block_rows]
        lagged, lag_period = {}, {}
        for k in LAG_ORDERS:
            position, valid = previous[k]
            values = field_values[position[block_rows]]
            values[~valid[block_rows]] = np.nan
            lagged[k] = values
            lag_period[k] = row_period[position[block_rows]]
        months = np.column_stack([lag_period[2], lag_period[1], row_period[block_rows]])
        out = out_all[start:start + len(block_rows)]
        window_cache = {}
        for i, (j, kind, k) in enumerate(specs):
            if kind == "original":
                out[:, i] = current[:, j]
            elif kind == "lag":
                out[:, i] = lagged[k][:, j]
            elif kind == "delta":
                out[:, i] = current[:, j] - lagged[k][:, j]
            else:
                if j not in window_cache:
                    window = np.column_stack([lagged[2][:, j], lagged[1][:, j], current[:, j]]).astype(np.float64)
                    window_cache[j] = window_stats(window, months)
                out[:, i] = window_cache[j][0 if kind == "avg3" else 1]
    return out_all


# [Anotación · líneas 682–697] Construye R_fit (202103–202106) y R_pred (202108), guarda cliente, mes y clase
#   de las filas de entrenamiento y los números de cliente de agosto. La clase binaria vale 1 cuando la clase
#   ternaria no es CONTINUA (BAJA+1 o BAJA+2). Libera el panel y calcula huellas SHA-1 del orden de las filas de
#   entrenamiento y de agosto, que se usan al retomar una corrida.
R_fit = fill_columns(fit_rows, FEATURES)
R_pred = fill_columns(future_rows, FEATURES)
fit_info = panel_keys.loc[fit_rows, ["numero_de_cliente", "foto_mes", "clase_ternaria"]].reset_index(drop=True)
future_ids = panel_keys.loc[future_rows, "numero_de_cliente"].to_numpy(dtype=np.int64)
y_fit = (~fit_info["clase_ternaria"].eq("CONTINUA")).astype(np.int8).to_numpy()
del panel_keys, field_values, previous, row_months, row_period


def ids_hash(*arrays):
    """Huella del orden de las filas: al retomar, solo se reusan predicciones guardadas con el mismo orden de clientes."""
    return hashlib.sha1(b"".join(np.ascontiguousarray(a, dtype=np.int64).tobytes() for a in arrays)).hexdigest()[:12]


FIT_IDS_HASH = ids_hash(fit_info["numero_de_cliente"].to_numpy(), fit_info["foto_mes"].to_numpy())
AUG_IDS_HASH = ids_hash(future_ids)
release_memory()

# [Anotación · líneas 699–721] Ubica el bloque contiguo de filas de cada mes dentro de R_fit (corta con error
#   si no es contiguo) y define las filas de la búsqueda (202103–202105), las de validación (202106) y todas.
#   Arma dos máscaras de junio: positivos (BAJA+1 o BAJA+2) y sólo BAJA+2.
fit_months = fit_info["foto_mes"].to_numpy()
MONTH_SLICES = {}
for month in FIT_MONTHS:
    rows = np.flatnonzero(fit_months == month)
    if len(rows) == 0 or rows[-1] - rows[0] + 1 != len(rows):
        raise RuntimeError(f"Las filas de {month} no forman un bloque contiguo")
    MONTH_SLICES[month] = slice(int(rows[0]), int(rows[-1]) + 1)
del rows


def months_slice(months):
    months = sorted(months)
    selector = slice(MONTH_SLICES[months[0]].start, MONTH_SLICES[months[-1]].stop)
    if sorted(np.unique(fit_months[selector]).tolist()) != months:
        raise RuntimeError(f"El bloque {months} no es contiguo")
    return selector


BO_ROWS = months_slice(BO_TRAIN_MONTHS)
VALID_ROWS = MONTH_SLICES[VALID_MONTH]
ALL_ROWS = slice(0, R_fit.shape[0])
june_positive = y_fit[VALID_ROWS].astype(bool)
june_baja2 = fit_info["clase_ternaria"].eq("BAJA+2").to_numpy(dtype=bool)[VALID_ROWS]

# [Anotación · líneas 723–736] Controles con assert: todas las filas de entrenamiento tienen clase, los meses
#   están ordenados, R_fit y R_pred tienen la misma cantidad de columnas, ccajas_depositos está en NA en 202105,
#   mtc_saldo_total_lag2 está en NA en 202104, y _avg3 y _slope3 de mtc_saldo_total están en NA en 202103. En
#   junio más de la mitad de las filas tiene valor en cuatro variables nuevas de muestra, y en agosto en
#   mtc_saldo_total_avg3.
# Controles
assert fit_info["clase_ternaria"].notna().all()
assert (np.diff(fit_months) >= 0).all()
assert R_fit.shape[1] == R_pred.shape[1] == len(FEATURES)
if "ccajas_depositos" in feature_index:
    assert np.isnan(R_fit[MONTH_SLICES[202105], feature_index["ccajas_depositos"]]).all()
assert np.isnan(R_fit[MONTH_SLICES[202104], feature_index["mtc_saldo_total_lag2"]]).all()  # abril no tiene lag2
assert np.isnan(R_fit[MONTH_SLICES[202103], feature_index["mtc_saldo_total_avg3"]]).all()  # marzo no tiene historia
assert np.isnan(R_fit[MONTH_SLICES[202103], feature_index["mtc_saldo_total_slope3"]]).all()
_june = R_fit[VALID_ROWS]
for _name in ("mtc_saldo_total_avg3", "mtc_saldo_total_slope3", "tperdio_payroll", "cproductos_perdidos_lag2"):
    assert np.isfinite(_june[:, feature_index[_name]]).mean() > 0.5, _name
assert np.isfinite(R_pred[:, feature_index["mtc_saldo_total_avg3"]]).mean() > 0.5
del _june

# [Anotación · líneas 738–750] Muestra una tabla con la cantidad de columnas por bloque (base de c9920, nuevas
#   con lags y deltas, _avg3 y _slope3, total), escribe variables.json con la lista y su huella, y deja en el
#   log la cantidad de registros por mes y clase, de filas y de variables.
columns_table = pd.DataFrame([
    {"bloque": "base c9920", "columnas": len(LIST_A)},
    {"bloque": "11 atributos nuevos x 5 (con lags y deltas)", "columnas": len(NEW_COLUMNS)},
    {"bloque": f"_avg3 y _slope3 ({N_BASE_FIELDS} campos base + {len(NEW_NAMES)} nuevos)", "columnas": len(HIST_COLUMNS)},
    {"bloque": "total (más el mismo número de canaritos)", "columnas": len(FEATURES)},
])
display(columns_table)
(OUT_DIR / "variables.json").write_text(json.dumps({"variables": FEATURES, "hash": FEATURES_HASH}, ensure_ascii=False,
                                                  indent=2), encoding="utf-8")
log(f"Clase: {fit_info.groupby(['foto_mes', 'clase_ternaria']).size().unstack().to_dict('index')}")
log(f"Filas: {R_fit.shape[0]} de marzo a junio, {R_pred.shape[0]} de agosto | variables: {len(LIST_A)} de c9920 + "
    f"{len(NEW_COLUMNS)} nuevas + {len(HIST_COLUMNS)} avg3/slope3 ({N_BASE_FIELDS} campos base) = {len(FEATURES)} | "
    f"datos en {(time.perf_counter() - data_start) / 60:.1f} min")

#%% celda 11 [texto]
## Ranking con cero fijo (igual que `c9920`)

Cada columna, por separado y por mes: 0 → 0, NA → NA, positivos en (0, 1], negativos en [−1, 0), empates con rango promedio.

#%% celda 12 [código]
# [Anotación · líneas 758–775] rank_cero_fijo() transforma un vector: el 0 queda en 0 y el NA en NA; los
#   positivos se reemplazan por su rango promedio dividido por la cantidad de positivos, en (0, 1]; los
#   negativos, por menos el rango de su valor absoluto dividido por la cantidad de negativos, en [−1, 0). Sigue
#   un assert con un ejemplo de 10 valores.
def rank_cero_fijo(values):
    ranked = np.full(values.shape, np.nan, dtype=np.float32)
    ranked[values == 0] = 0.0
    positive = values > 0
    negative = values < 0
    n_positive = int(positive.sum())
    n_negative = int(negative.sum())
    if n_positive:
        ranked[positive] = pd.Series(values[positive]).rank(method="average").to_numpy() / n_positive
    if n_negative:
        ranked[negative] = -pd.Series(-values[negative]).rank(method="average").to_numpy() / n_negative
    return ranked


_test = rank_cero_fijo(np.array([0, -50, 10, np.nan, 30, -5, 10, 1000, -50, -1], dtype=np.float32))
_expected = np.array([0, -0.875, 0.375, np.nan, 0.75, -0.5, 0.375, 1, -0.875, -0.25], dtype=np.float32)
assert np.allclose(_test, _expected, equal_nan=True), _test
del _test, _expected

# [Anotación · líneas 777–786] Aplica rank_cero_fijo() a cada columna por separado dentro de cada uno de los
#   cuatro meses de R_fit y dentro de agosto en R_pred. Verifica que la cantidad de NA no cambie y que todo
#   quede entre −1 y 1.
rank_start = time.perf_counter()
for matrix, selector in [*[(R_fit, MONTH_SLICES[m]) for m in FIT_MONTHS], (R_pred, slice(0, R_pred.shape[0]))]:
    block = matrix[selector]
    na_before = np.isnan(block).sum()
    for j in range(block.shape[1]):
        block[:, j] = rank_cero_fijo(block[:, j])
    assert np.isnan(block).sum() == na_before
    assert np.nanmin(block) >= -1.0 and np.nanmax(block) <= 1.0
release_memory()
log(f"Ranking listo en {time.perf_counter() - rank_start:.0f} s")

#%% celda 13 [texto]
## Funciones comunes

Métricas de junio (AUC con BAJA+1 y BAJA+2 positivos, *average precision* con solo BAJA+2, ganancia suavizada), guardado seguro (escribe un temporal y lo renombra) y entrenamiento con canaritos 1 a 1 adelante.

#%% celda 14 [código]
# [Anotación · líneas 794–815] Funciones de guardado: save_atomic() escribe en un archivo .tmp y lo renombra;
#   save_json() y save_npy() la usan; load_json() lee un JSON; canonical() pasa un objeto por JSON para
#   compararlo con lo guardado.
def save_atomic(path, write):
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as handle:
        write(handle)
    os.replace(tmp, path)


def save_json(path, data):
    text = json.dumps(data, ensure_ascii=False, indent=2)
    save_atomic(path, lambda handle: handle.write(text.encode("utf-8")))


def save_npy(path, array):
    save_atomic(path, lambda handle: np.save(handle, array))


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(data):
    return json.loads(json.dumps(data))


# [Anotación · líneas 818–833] auc_score() calcula el AUC a partir de la suma de rangos de los positivos.
#   average_precision() ordena de mayor a menor puntaje y promedia la precisión en la posición de cada positivo.
def auc_score(positive, scores):
    positive = np.asarray(positive, dtype=bool)
    n_positive = int(positive.sum())
    n_negative = len(positive) - n_positive
    ranks = pd.Series(np.asarray(scores, dtype=np.float64)).rank(method="average").to_numpy()
    return float((ranks[positive].sum() - n_positive * (n_positive + 1) / 2) / (n_positive * n_negative))


def average_precision(positive, scores):
    """Promedio de la precisión en la posición de cada positivo (lista ordenada de mayor a menor)."""
    order = np.argsort(-np.asarray(scores, dtype=np.float64), kind="stable")
    hits = np.asarray(positive, dtype=bool)[order]
    if not hits.any():
        return float("nan")
    precision_at = np.cumsum(hits) / np.arange(1, len(hits) + 1)
    return float(precision_at[hits].mean())


# [Anotación · líneas 836–859] gain_curve() ordena por puntaje descendente, acumula +1,0725 por cada BAJA+2 y
#   −0,0275 por cada otro registro, y suaviza la curva con una media móvil centrada de 501 posiciones.
#   june_metrics() devuelve para junio el AUC (positivos BAJA+1 y BAJA+2), la average precision con sólo BAJA+2,
#   el máximo de la ganancia suavizada, la posición donde ocurre y la ganancia suavizada en el corte 11.000.
#   Siguen dos asserts con valores a mano.
def gain_curve(baja2, scores):
    order = np.argsort(-np.asarray(scores, dtype=np.float64), kind="stable")
    cumulative = np.cumsum(np.where(baja2[order], GAIN_BAJA2, GAIN_OTHER))
    smooth = pd.Series(cumulative).rolling(window=GAIN_WINDOW, center=True, min_periods=GAIN_WINDOW).mean().to_numpy()
    return cumulative, smooth


def june_metrics(scores):
    _, smooth = gain_curve(june_baja2, scores)
    best = int(np.nanargmax(smooth))
    return {
        "auc": auc_score(june_positive, scores),
        "ap_baja2": average_precision(june_baja2, scores),
        "ganancia_maxima": float(smooth[best]),
        "mejor_corte": best + 1,
        f"ganancia_corte_{CORTE_REF}": float(smooth[CORTE_REF - 1]),
    }


_positive = np.array([1, 0, 1, 0, 0, 1, 0, 0], dtype=bool)
_scores = np.array([0.9, 0.8, 0.8, 0.5, 0.4, 0.4, 0.2, 0.1])
assert np.isclose(auc_score(_positive, _scores), 12 / 15)
assert np.isclose(average_precision(np.array([1, 0, 1, 0], dtype=bool), np.array([0.9, 0.8, 0.7, 0.1])), (1 + 2 / 3) / 2)
del _positive, _scores


# [Anotación · líneas 862–881] zlgb_params() arma los parámetros del modelo: objective binary, metric auc,
#   boosting gbdt, canaritos igual a la cantidad de canaritos, learning_rate 0,005, feature_fraction 0,5,
#   feature_fraction_bynode 0,2, min_data_in_leaf 0, max_bin 31, feature_pre_filter False, force_col_wise True,
#   y num_leaves, min_sum_hessian_in_leaf y seed recibidos.
def zlgb_params(values, n_canaries, seed):
    """Fijos del profesor (como c9920) con canaritos 1 a 1. num_iterations va aparte."""
    return {
        "objective": "binary",
        "metric": LGB_METRIC,
        "boosting": "gbdt",
        "canaritos": int(n_canaries),
        "learning_rate": LEARNING_RATE,
        "feature_fraction": FEATURE_FRACTION,
        "feature_fraction_bynode": FEATURE_FRACTION_BYNODE,
        "min_data_in_leaf": MIN_DATA_IN_LEAF,
        "num_leaves": int(values["num_leaves"]),
        "min_sum_hessian_in_leaf": float(values["min_sum_hessian_in_leaf"]),
        "max_bin": MAX_BIN,
        "num_threads": NUM_THREADS,
        "feature_pre_filter": False,
        "force_col_wise": True,
        "verbose": -1,
        "seed": int(seed),
    }


# [Anotación · líneas 884–906] with_canaries() arma la matriz de entrenamiento con n columnas de números
#   uniformes al azar (generadas con la semilla) seguidas de las n variables reales. train_zlgb() entrena
#   zLightGBM con esa matriz durante num_iterations rondas y corta con error si el modelo usó algún canarito en
#   un corte.
def with_canaries(real, columns, seed):
    """Matriz [canaritos | variables reales], con un canarito por variable (zLightGBM los quiere adelante)."""
    n = len(columns)
    out = np.empty((real.shape[0], 2 * n), dtype=np.float32)
    out[:, :n] = np.random.default_rng(seed).random((real.shape[0], n), dtype=np.float32)
    out[:, n:] = real[:, columns]
    return out


def train_zlgb(columns, values, seed, train_rows):
    """zLightGBM con las variables `columns` y n canaritos adelante. Verifica que no corte por canaritos."""
    n = len(columns)
    X = with_canaries(R_fit[train_rows], columns, seed)
    names = [f"canarito_{i:04d}" for i in range(1, n + 1)] + [FEATURES[j] for j in columns]
    dataset = lgb.Dataset(X, label=y_fit[train_rows], feature_name=names, free_raw_data=True,
                          params=zlgb_params(values, n, seed))
    booster = lgb.train(zlgb_params(values, n, seed), dataset, num_boost_round=int(values["num_iterations"]))
    del X, dataset
    release_memory()
    canary_splits = int(booster.feature_importance("split")[:n].sum())
    if canary_splits:
        raise RuntimeError(f"El modelo cortó {canary_splits} veces por canaritos: zlightgbm no está podando")
    return booster


# [Anotación · líneas 909–922] predict_june() predice las filas de junio, con canaritos generados con semilla
#   + 1. gain_by_group() calcula qué proporción del gain de las variables reales corresponde a cada bloque: base
#   de c9920, nuevas y _avg3/_slope3.
def predict_june(booster, columns, seed):
    return booster.predict(with_canaries(R_fit[VALID_ROWS], columns, seed + 1))


def gain_by_group(booster, n):
    """Proporción del gain de las variables reales por bloque (base c9920, nuevas, avg3/slope3)."""
    gain = booster.feature_importance("gain")[n:]
    total = gain.sum()
    groups = {"base": gain[:len(LIST_A)].sum(), "nuevas": gain[len(LIST_A):len(LIST_A) + len(NEW_COLUMNS)].sum(),
              "avg3_slope3": gain[len(LIST_A) + len(NEW_COLUMNS):].sum()}
    return {f"gain_{k}": round(float(v / total), 4) if total > 0 else 0.0 for k, v in groups.items()}


log("Funciones listas")

#%% celda 15 [texto]
## 1. Optimización bayesiana

Optuna (TPE multivariado): 25 corridas = 1 con los valores de `c9920` + 10 al azar + 14 guiadas. Cada corrida entrena un zLightGBM completo con marzo a mayo (semilla 101737), predice junio y se califica con el **AUC de junio**. Se guardan además la AP (solo BAJA+2), la ganancia y las predicciones de junio de cada corrida.

El estudio (SQLite) vive en el disco local porque SQLite no funciona bien sobre el bucket; después de cada corrida se copia al bucket, y al empezar se recupera de ahí si la máquina es nueva. Con `CORTAR_BAYESIANA` en la carpeta del experimento termina la corrida en curso y sigue.

#%% celda 16 [código]
# [Anotación · líneas 932–948] Arma la configuración de la búsqueda (huellas de variables y filas, espacio,
#   meses, semilla y parámetros fijos). Abre o crea el estudio de Optuna en un SQLite del disco local,
#   recuperándolo del bucket si en el disco no está, con dirección maximize; corta con error si el estudio
#   guardado es de otra configuración. El muestreador es TPESampler multivariado con 11 corridas iniciales y
#   semilla 20261011 más la cantidad de corridas ya registradas.
BO_CONFIG = canonical({"variables": FEATURES_HASH, "filas": FIT_IDS_HASH, "search_space": SEARCH_SPACE,
                       "n_startup_trials": N_STARTUP_TRIALS, "meses": BO_TRAIN_MONTHS, "valida": VALID_MONTH,
                       "seed": BO_SEED, "prueba": MODO_PRUEBA,
                       "fijos": {k: v for k, v in zlgb_params(C9920_VALUES, 0, BO_SEED).items()
                                 if k not in ("num_leaves", "min_sum_hessian_in_leaf", "canaritos", "num_threads")}})
LOCAL_DB, BUCKET_DB = LOCAL_DIR / "estudio.db", BO_DIR / "estudio.db"
if not LOCAL_DB.exists() and BUCKET_DB.exists():
    shutil.copy(BUCKET_DB, LOCAL_DB)
    log("Estudio recuperado del bucket")
study = optuna.create_study(study_name=f"{EXP_ID}_bayesiana", storage=f"sqlite:///{LOCAL_DB.as_posix()}",
                            direction="maximize", load_if_exists=True)
if not study.trials:
    study.set_user_attr("config", BO_CONFIG)
elif study.user_attrs.get("config") != BO_CONFIG:
    raise RuntimeError(f"{LOCAL_DB} es de otra configuración. Movelo (y el del bucket) para empezar de cero.")
study.sampler = optuna.samplers.TPESampler(n_startup_trials=N_STARTUP_TRIALS, seed=SAMPLER_SEED + len(study.trials),
                                           multivariate=True)


# [Anotación · líneas 951–960] Encola como primera corrida los valores de c9920 si todavía no hay una corrida
#   completa con ellos ni una en espera.
def completed_trials():
    return [t for t in study.trials if t.state == TrialState.COMPLETE]


# Una corrida que quedó a medias (se cortó la máquina) queda como RUNNING y no cuenta: se vuelve a hacer otra.
if not any(t.params == C9920_VALUES for t in completed_trials()) \
        and not any(t.state == TrialState.WAITING for t in study.trials):
    study.enqueue_trial(C9920_VALUES)

bo_timing = []


# [Anotación · líneas 963–990] Función objetivo: pide a Optuna num_iterations, num_leaves y
#   min_sum_hessian_in_leaf dentro del espacio, entrena zLightGBM con todas las variables de la lista sobre
#   202103–202105 con semilla 101737, predice junio, guarda las predicciones en un .npy y registra en la corrida
#   las métricas de junio, el reparto del gain por bloque, la cantidad de árboles, los minutos y el tipo (c9920,
#   azar o guiada). Devuelve el AUC de junio.
def objective(trial):
    values = {
        "num_iterations": trial.suggest_int("num_iterations", *SEARCH_SPACE["num_iterations"]),
        "num_leaves": trial.suggest_int("num_leaves", *SEARCH_SPACE["num_leaves"]),
        "min_sum_hessian_in_leaf": trial.suggest_float("min_sum_hessian_in_leaf", *SEARCH_SPACE["min_sum_hessian_in_leaf"]),
    }
    n_before = len(completed_trials())
    kind = "c9920" if values == C9920_VALUES else ("azar" if n_before < N_STARTUP_TRIALS else "guiada")
    start = time.perf_counter()
    booster = train_zlgb(COLUMNS, values, BO_SEED, BO_ROWS)
    scores = predict_june(booster, COLUMNS, BO_SEED)
    num_trees = int(booster.num_trees())
    groups = gain_by_group(booster, len(COLUMNS))
    del booster
    metrics = june_metrics(scores)
    minutes = (time.perf_counter() - start) / 60
    save_npy(BO_DIR / f"junio_corrida_{trial.number:03d}.npy", scores)
    for key, value in {**metrics, **groups, "num_trees": num_trees, "minutos": round(minutes, 1), "tipo": kind}.items():
        trial.set_user_attr(key, value)
    bo_timing.append((values["num_iterations"], minutes * 60))
    per_iteration = sum(s for _, s in bo_timing) / sum(n for n, _ in bo_timing)
    left = N_TRIALS - n_before - 1
    log(f"  corrida {n_before + 1:2d}/{N_TRIALS} ({kind:6s}) iter {values['num_iterations']:4d} | hojas "
        f"{values['num_leaves']:4d} | hessian {values['min_sum_hessian_in_leaf']:.5f} -> AUC {metrics['auc']:.5f} | "
        f"AP {metrics['ap_baja2']:.4f} | ganancia {metrics['ganancia_maxima']:.1f} con {metrics['mejor_corte']} | "
        f"{num_trees} árboles | gain nuevas {groups['gain_nuevas']:.0%} avg/slope {groups['gain_avg3_slope3']:.0%} | "
        f"{minutes:.1f} min | faltan ~{left * per_iteration * sum(SEARCH_SPACE['num_iterations']) / 2 / 3600:.1f} h")
    return metrics["auc"]


# [Anotación · líneas 993–1008] trials_table() arma la tabla de corridas completas ordenada por AUC.
#   checkpoint() se ejecuta después de cada corrida: escribe corridas.csv, copia el SQLite al bucket (si la
#   copia da error sólo deja un aviso en el log) y detiene el estudio si existe el archivo CORTAR_BAYESIANA.
def trials_table():
    rows = [{"corrida": t.number, **t.params, **t.user_attrs} for t in completed_trials()]
    table = pd.DataFrame(rows)
    return table.sort_values("auc", ascending=False).reset_index(drop=True) if len(table) else table


def checkpoint(study_, trial_):
    try:  # un error pasajero del bucket no frena la noche: la copia se repite en la próxima corrida
        trials_table().to_csv(BO_DIR / "corridas.csv", index=False)
        shutil.copy(LOCAL_DB, BO_DIR / "estudio.db.tmp")
        os.replace(BO_DIR / "estudio.db.tmp", BUCKET_DB)
    except Exception as error:
        log(f"[aviso] no pude copiar el estudio al bucket: {error!r}")
    if STOP_BO_FILE.exists() and completed_trials():
        log(f"Encontré {STOP_BO_FILE.name}: corto la bayesiana con {len(completed_trials())} corridas.")
        study_.stop()


# [Anotación · líneas 1011–1032] Ejecuta las corridas que faltan hasta 25 (ninguna si existe CORTAR_BAYESIANA
#   y ya hay corridas completas). Guarda corridas.csv, toma la corrida de mayor AUC de junio y escribe sus tres
#   valores y sus métricas en mejores_hiperparametros.json. Deja en el log, a título informativo, qué corrida
#   tiene mayor average precision y cuál mayor ganancia.
remaining = N_TRIALS - len(completed_trials())
if STOP_BO_FILE.exists() and completed_trials():
    log(f"{STOP_BO_FILE.name} existe: no corro más corridas de la bayesiana.")
    remaining = 0
log(f"Bayesiana: {len(completed_trials())} de {N_TRIALS} corridas hechas")
if remaining > 0:
    study.optimize(objective, n_trials=remaining, callbacks=[checkpoint])
bo_table = trials_table()
bo_table.to_csv(BO_DIR / "corridas.csv", index=False)
display(bo_table.round(5))
best_trial = study.best_trial
BEST_VALUES = {"num_iterations": int(best_trial.params["num_iterations"]),
               "num_leaves": int(best_trial.params["num_leaves"]),
               "min_sum_hessian_in_leaf": float(best_trial.params["min_sum_hessian_in_leaf"])}
save_json(BO_DIR / "mejores_hiperparametros.json", {"corrida": best_trial.number, "valores": BEST_VALUES,
                                                   **best_trial.user_attrs})
log("Mejores valores (AUC):", BEST_VALUES, f"| corrida {best_trial.number} | AUC junio {best_trial.value:.5f} | "
    f"AP {best_trial.user_attrs['ap_baja2']:.4f} | ganancia {best_trial.user_attrs['ganancia_maxima']:.1f}")
for _metric in ("ap_baja2", "ganancia_maxima"):
    _row = bo_table.sort_values(_metric, ascending=False).iloc[0]
    log(f"  (informativo) la mejor por {_metric} es la corrida {int(_row['corrida'])}: iter {int(_row['num_iterations'])}, "
        f"hojas {int(_row['num_leaves'])}, hessian {_row['min_sum_hessian_in_leaf']:.5f}")

#%% celda 17 [texto]
## 2. Referencia de junio

Los mejores valores, 3 semillas (marzo a mayo → junio): 101737 se reusa de la bayesiana, las otras dos se entrenan. Se compara contra la referencia de junio de `c9920` (mismas 3 semillas, su lista y sus valores), leída del bucket. Da la curva de ganancia de junio por corte, para elegir el corte y para validar ensambles.

#%% celda 18 [código]
# [Anotación · líneas 1040–1060] Referencia de junio con las semillas 101737, 303011 y 602909: para 101737
#   reusa las predicciones de la corrida elegida; para las otras dos entrena con 202103–202105 y los valores
#   elegidos y predice junio (o reusa lo guardado si la configuración coincide). Promedia las tres predicciones
#   y guarda junio_ensamble.npy.
june_scores = {}
for seed in JUNE_SEEDS:
    if seed == BO_SEED:
        june_scores[seed] = np.load(BO_DIR / f"junio_corrida_{best_trial.number:03d}.npy")
        continue
    base = JUNE_DIR / f"junio_seed{seed}"
    config = canonical({"seed": seed, "valores": BEST_VALUES, "bayesiana": BO_CONFIG})
    if base.with_suffix(".npy").exists() and base.with_suffix(".json").exists() \
            and load_json(base.with_suffix(".json")) == config:
        june_scores[seed] = np.load(base.with_suffix(".npy"))
        continue
    start = time.perf_counter()
    booster = train_zlgb(COLUMNS, BEST_VALUES, seed, BO_ROWS)
    june_scores[seed] = predict_june(booster, COLUMNS, seed)
    del booster
    save_json(base.with_suffix(".json"), config)
    save_npy(base.with_suffix(".npy"), june_scores[seed])
    log(f"  referencia semilla {seed}: ganancia {june_metrics(june_scores[seed])['ganancia_maxima']:.1f} | "
        f"{(time.perf_counter() - start) / 60:.1f} min")
c9923_june = np.column_stack([june_scores[s] for s in JUNE_SEEDS]).mean(axis=1)
save_npy(JUNE_DIR / "junio_ensamble.npy", c9923_june)

# [Anotación · líneas 1062–1084] Carga, si existe, el promedio de junio de c9920 y lo usa sólo si tiene la
#   misma cantidad de filas y un AUC mayor que 0,8 contra las clases de este junio. Para cada corte de 9.000 a
#   15.000 toma la ganancia suavizada de junio de c9923 (y la de c9920 y su diferencia, si está). Escribe
#   ganancia_junio_por_corte.csv y deja las métricas en el log.
june_curves = {"c9923": c9923_june}
_c9920_june_path = next((p for p in (C9920_DIR / "4_referencia_junio" / "junio_ensamble.npy",
                                     C9920_DIR / "junio_ensamble.npy") if p.exists()), None)
if _c9920_june_path is not None and len(np.load(_c9920_june_path)) == len(c9923_june):
    _c9920_june = np.load(_c9920_june_path)
    if auc_score(june_positive, _c9920_june) > 0.8:  # si el orden de filas no coincidiera, el AUC daría ~0,5
        june_curves["c9920"] = _c9920_june
    else:
        log("  la referencia de c9920 no coincide fila a fila con este junio: no la comparo")
else:
    log("  no encontré la referencia de junio de c9920 (o es de otro tamaño, como en modo prueba): no la comparo")

june_by_cut = pd.DataFrame({"corte": CORTES})
for label, scores in june_curves.items():
    _, smooth = gain_curve(june_baja2, scores)
    june_by_cut[label] = [float(smooth[c - 1]) for c in CORTES]
    m = june_metrics(scores)
    log(f"  ensamble de {len(JUNE_SEEDS)} {label}: AUC {m['auc']:.5f} | AP {m['ap_baja2']:.4f} | "
        f"ganancia máxima {m['ganancia_maxima']:.1f} con {m['mejor_corte']} | en {CORTE_REF}: {m[f'ganancia_corte_{CORTE_REF}']:.1f}")
if "c9920" in june_by_cut:
    june_by_cut["diferencia"] = june_by_cut["c9923"] - june_by_cut["c9920"]
june_by_cut.to_csv(JUNE_DIR / "ganancia_junio_por_corte.csv", index=False)
display(june_by_cut.round(1))

#%% celda 19 [texto]
## 3. Semillas de agosto y cortes

Los mejores valores, marzo a junio → agosto, hasta `N_SEMILLAS_AGOSTO` semillas (primero las de `s0004`, después los primos de `s0005`). Cada semilla se guarda apenas termina y **enseguida se rehacen los cortes** (un CSV por corte en `5_cortes/`, con la ganancia de junio al lado, y las probabilidades del ensamble en `4_agosto/probabilidades_agosto.csv.gz`).

Antes de cada semilla nueva mira si existe `PARAR` en la carpeta del experimento: si está, no empieza otra.

#%% celda 20 [código]
# [Anotación · líneas 1094–1105] Guarda los números de cliente de agosto. aug_config() describe la
#   configuración de una semilla (semilla, huellas, valores, meses, configuración de la búsqueda) y
#   saved_seeds() devuelve las semillas ya guardadas con esa misma configuración.
save_npy(AUG_DIR / "ids_agosto.npy", future_ids)


def aug_config(seed):
    return canonical({"seed": seed, "variables": FEATURES_HASH, "ids_agosto": AUG_IDS_HASH, "valores": BEST_VALUES,
                      "meses": FIT_MONTHS, "bayesiana": BO_CONFIG, "prueba": MODO_PRUEBA})


def saved_seeds():
    """Semillas de agosto guardadas con la configuración actual, en el orden de FINAL_SEEDS."""
    return [s for s in FINAL_SEEDS if (AUG_DIR / f"seed_{s}.npy").exists() and (AUG_DIR / f"seed_{s}.json").exists()
            and load_json(AUG_DIR / f"seed_{s}.json") == aug_config(s)]


# [Anotación · líneas 1108–1140] write_cuts() promedia las probabilidades de agosto de las semillas guardadas,
#   ordena los clientes de mayor a menor y, para cada corte (exige entre 8.000 y 15.000), escribe un CSV sin
#   encabezado con los primeros números de cliente, uno por línea, con nombre
#   c9923_<semillas>sem_corte<corte>.csv. Borra los CSV de cortes anteriores, escribe cortes.csv con la ganancia
#   de junio de cada corte y guarda probabilidades_agosto.csv.gz con cliente y probabilidad promedio.
def write_cuts():
    """Promedia las semillas guardadas y reescribe un CSV por corte (escritura segura: temporal y renombre)."""
    seeds = saved_seeds()
    if not seeds:
        log("Cortes: todavía no hay semillas de agosto")
        return None
    ids = np.load(AUG_DIR / "ids_agosto.npy")
    assert ids_hash(ids) == AUG_IDS_HASH, "ids_agosto.npy no tiene el orden de clientes de esta corrida"
    ensemble = np.column_stack([np.load(AUG_DIR / f"seed_{s}.npy") for s in seeds]).mean(axis=1)
    assert len(ensemble) == len(ids) == len(np.unique(ids))
    ranking = np.argsort(-ensemble, kind="stable")
    june_gain = june_by_cut.set_index("corte")["c9923"]
    written, rows = set(), []
    for cut in CORTES:
        if not MODO_PRUEBA and not 8_000 <= cut <= 15_000:
            raise ValueError(f"El bot acepta entre 8.000 y 15.000 registros: {cut}")
        chosen = ids[ranking[:cut]].astype(np.int64)
        assert len(np.unique(chosen)) == cut
        path = CUTS_DIR / f"{EXP_ID}_{len(seeds)}sem_corte{cut}.csv"
        text = "\n".join(map(str, chosen)) + "\n"
        save_atomic(path, lambda handle: handle.write(text.encode("utf-8")))
        written.add(path.name)
        rows.append({"corte": cut, "archivo": path.name, "ganancia_junio_c9923": round(float(june_gain[cut]), 1)})
    for old in CUTS_DIR.glob("*.csv"):
        if old.name not in written:
            old.unlink()
    cuts_table = pd.DataFrame(rows)
    save_atomic(OUT_DIR / "cortes.csv", lambda handle: handle.write(cuts_table.to_csv(index=False).encode("utf-8")))
    probabilities = pd.DataFrame({"numero_de_cliente": ids, "score": ensemble})
    save_atomic(AUG_DIR / "probabilidades_agosto.csv.gz",
                lambda handle: probabilities.to_csv(handle, index=False, compression={"method": "gzip"}))
    log(f"  cortes al día: {len(CORTES)} CSV con {len(seeds)} semillas en {CUTS_DIR}")
    return cuts_table


# [Anotación · líneas 1143–1170] Recorre las semillas pendientes. Antes de cada una mira si existe el archivo
#   PARAR y, si está, no empieza otra. Entrena zLightGBM con los valores elegidos sobre todas las filas de
#   202103 a 202106, predice agosto (canaritos con semilla + 1), guarda seed_<semilla>.npy y su configuración, y
#   rehace los cortes; un error al rehacerlos sólo queda como aviso en el log. Al terminar el ciclo vuelve a
#   escribir los cortes y muestra la tabla.
done = saved_seeds()
pending = [s for s in FINAL_SEEDS if s not in done]
log(f"Agosto: {len(done)} semillas guardadas, faltan {len(pending)} (tope {N_SEMILLAS_AGOSTO})")
stopped = False
aug_start = time.perf_counter()
for i, seed in enumerate(pending):
    if STOP_FILE.exists():
        log(f"Encontré {STOP_FILE.name}: no empiezo más semillas ({len(saved_seeds())} terminadas).")
        stopped = True
        break
    start = time.perf_counter()
    booster = train_zlgb(COLUMNS, BEST_VALUES, seed, ALL_ROWS)
    probabilities = booster.predict(with_canaries(R_pred, COLUMNS, seed + 1))
    del booster
    save_npy(AUG_DIR / f"seed_{seed}.npy", probabilities)
    save_json(AUG_DIR / f"seed_{seed}.json", aug_config(seed))
    per_seed = (time.perf_counter() - aug_start) / (i + 1)
    left = len(pending) - i - 1
    log(f"  [{len(done) + i + 1}/{len(FINAL_SEEDS)}] semilla {seed}: {(time.perf_counter() - start) / 60:.1f} min | "
        f"si nadie lo para, faltan ~{left * per_seed / 3600:.1f} h")
    try:  # un error pasajero del bucket no frena la noche: los cortes se rehacen con la próxima semilla
        write_cuts()
    except Exception as error:
        log(f"[aviso] no pude rehacer los cortes: {error!r}")

cuts_table = write_cuts()
if cuts_table is not None:
    display(cuts_table)

#%% celda 21 [texto]
## 4. Fin y apagado

Si `APAGAR_AL_TERMINAR = True` y estás en una máquina virtual de la cátedra, la borra. Todo quedó en el bucket, en la carpeta que muestra la primera celda.

#%% celda 22 [código]
# [Anotación · líneas 1178–1181] Escribe en el log el fin de la corrida con la cantidad de semillas de agosto
#   y, si la bandera está activa, borra la máquina virtual.
log(f"{EXP_ID} terminado (modo prueba: {MODO_PRUEBA}{', parado con PARAR' if stopped else ''}). "
    f"{len(saved_seeds())} semillas de agosto. Resultados en {OUT_DIR}")
if APAGAR_AL_TERMINAR:
    apagar_vm("fin del notebook")
````

### 01_c9920_canaritos_asesinos/c9920_CanaritosAsesinos.ipynb

Notebook previo del que c9923 toma la lista de variables y los valores iniciales de su búsqueda: arma 760 variables, las selecciona con canaritos en tres repeticiones, compara las listas en 202106, busca hiperparámetros con Optuna para la lista elegida y genera su propia predicción de 202108 con 20 semillas.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

#%% celda 1 [texto]
# c9920 — Canaritos asesinos

**Pregunta:** ¿eliminar las variables que no le ganan a los canaritos mejora el modelo de `s0006`?

Receta del profesor ("canaritos asesinos"): agregar un 20 % de canaritos, entrenar un LightGBM razonable, numerar las variables por importancia (1 = la más importante), calcular la media y el desvío de los números de los canaritos, y eliminar toda variable con número mayor que **media + desvío** o **media + 2 desvíos**.

**Cómo funciona** (todo con *Run All*):

1. **Datos:** igual que `s0006` (clase ternaria armada desde el crudo, lags, deltas, ranking con cero fijo; 760 variables reales).
2. **Selección:** LightGBM común con los parámetros del notebook z495 del profesor, 760 variables + 152 canaritos (20 %), entrenado con **mayo** (todas las BAJA y el 10 % de CONTINUA). Se repite con 3 semillas (canaritos y undersampling distintos).
3. **Listas:** para cada punto (media + 1 desvío, media + 2 desvíos) sobrevive la variable que pasa en al menos 2 de las 3 repeticiones. Se suma "sin eliminar" (las 760).
4. **Comparación:** zLightGBM con la configuración de `s0006` (sus fijos y sus mejores valores), canaritos 1 a 1, marzo a mayo → junio, **5 semillas por lista**. Mismas semillas en todas las listas: la única diferencia son las variables.
5. **Decisión:** gana una lista si mejora la ganancia de junio frente a "sin eliminar" con t pareado ≥ 2. Si ninguna gana, el notebook lo dice, no sigue y apaga la máquina.
6. **Bayesiana** (solo la lista ganadora): igual que `s0006`, 21 corridas, AUC de junio.
7. **Referencia de junio:** la ganadora con sus mejores valores (3 semillas) contra "sin eliminar" (las mismas 3 semillas).
8. **Agosto:** la ganadora, marzo a junio → agosto, `N_SEMILLAS_AGOSTO` semillas, y un CSV por corte.
9. **Apagado:** borra la máquina virtual (todo lo importante ya quedó en el bucket).

**Por qué la selección se entrena con mayo:** lag2 y delta_lag2 están vacíos en marzo y abril. Si la selección usara esos meses, las 304 variables de lag2 no tendrían importancia y morirían todas sin haber sido evaluadas. Mayo es el primer mes con lag2 completo, y junio queda limpio para juzgar. Por lo mismo, la comparación y la bayesiana entrenan con marzo a mayo (en `s0006` era marzo + abril).

**Si se corta** (por ejemplo, Google borra la máquina spot): cada resultado se guarda en el bucket apenas termina. Creá otra máquina, cloná el repo y hacé *Run All*: saltea lo que ya está y sigue.

**Modo prueba** (`MODO_PRUEBA=1` o `MODO_PRUEBA = True` a mano): el mismo camino con el 5 % de los clientes y pocos árboles, en unos 15 minutos. Sirve para probar la máquina virtual. Escribe en otra carpeta (`.../prueba`), no se mezcla con la corrida real y no apaga la máquina, así después se larga la corrida real en la misma.

#%% celda 2 [código]
# [Anotación · líneas 27–46] Importa las bibliotecas, fija el identificador c9920 y lee la variable de entorno
#   MODO_PRUEBA. Fuera del modo prueba quedan activadas las banderas de borrar la máquina virtual al terminar y
#   ante un error.
from pathlib import Path
from urllib.request import urlretrieve
import gc
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

import numpy as np
import pandas as pd

EXP_ID = "c9920"

MODO_PRUEBA = os.environ.get("MODO_PRUEBA", "0") == "1"  # o poner True a mano: prueba corta de la máquina virtual
APAGAR_AL_TERMINAR = not MODO_PRUEBA  # al final borra la máquina virtual (solo en Google Cloud; los resultados quedan en el bucket)
APAGAR_SI_FALLA = not MODO_PRUEBA  # si una celda falla, borra la máquina para no gastar créditos (en la prueba, no)

# [Anotación · líneas 48–64] Parámetros de datos (meses 202103 a 202106 para entrenar, 202108 para predecir,
#   lags 1 y 2) y de la selección: mes 202105, 10 % de CONTINUA, canaritos equivalentes al 20 % de las columnas
#   reales, 3 semillas, 2.848 iteraciones, 71 hojas, min_sum_hessian_in_leaf 0,0067, learning_rate 0,005,
#   feature_fraction 0,5, min_data_in_leaf 0 y max_bin 31. Los puntos de corte son media + 1 desvío y media + 2
#   desvíos, y una variable sobrevive con al menos 2 votos de 3.
# Datos (igual que s0006)
DATA_URL = "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
TRAIN_MONTHS = [202103, 202104, 202105, 202106]  # semillas de agosto
PREDICT_MONTH = 202108
NEEDED_MONTHS = {202103, 202104, 202105, 202106, 202107, 202108}
LAG_ORDERS = [1, 2]
NUM_THREADS = os.cpu_count() or 4

# 1) Selección: LightGBM común con los parámetros del notebook z495 del profesor
SEL_MONTH = 202105  # primer mes con lag2 completo
SEL_UNDERSAMPLING = 0.10  # todas las BAJA + el 10 % de CONTINUA, como z495
SEL_CANARY_FRACTION = 0.20  # 20 % de canaritos respecto de las columnas reales
SEL_SEEDS = [101737, 303011, 602909]  # 3 repeticiones
SEL_VALUES = {"num_iterations": 2848, "num_leaves": 71, "min_sum_hessian_in_leaf": 0.0067}  # z495
SEL_FIXED = {"learning_rate": 0.005, "feature_fraction": 0.50, "min_data_in_leaf": 0, "max_bin": 31}  # z495
CUT_POINTS = {"media_1desvio": 1.0, "media_2desvios": 2.0}  # punto de asesinato = media + k * desvío
MIN_VOTES = 2  # una variable sobrevive si sobrevive en al menos 2 de las 3 repeticiones

# [Anotación · líneas 66–77] Parámetros de la comparación de listas: entrena 202103–202105 y valida 202106 con
#   5 semillas, con 1.155 iteraciones, 126 hojas y min_sum_hessian_in_leaf 0,094, learning_rate 0,005,
#   feature_fraction 0,5, feature_fraction_bynode 0,2, min_data_in_leaf 0 y max_bin 31. Una lista gana con t
#   pareado ≥ 2; FORZAR_LISTA (None) permite seguir con una lista dada.
# 2) Comparación de listas: zLightGBM con la configuración de s0006
CMP_TRAIN_MONTHS = [202103, 202104, 202105]
VALID_MONTH = 202106
CMP_SEEDS = [101737, 303011, 602909, 707717, 906007]
S0006_VALUES = {"num_iterations": 1155, "num_leaves": 126, "min_sum_hessian_in_leaf": 0.094}  # mejores de s0006
LEARNING_RATE = 0.005
FEATURE_FRACTION = 0.50
FEATURE_FRACTION_BYNODE = 0.20
MIN_DATA_IN_LEAF = 0
MAX_BIN = 31
WIN_MIN_T = 2.0  # una lista gana si mejora la ganancia de junio con t pareado >= 2
FORZAR_LISTA = None  # nombre de una lista para seguir con ella aunque no gane (None = decide la regla)

# [Anotación · líneas 79–103] Parámetros de la búsqueda (num_iterations 64–4.096, num_leaves 16–2.048,
#   min_sum_hessian_in_leaf 1e-6–1; 21 corridas con 11 iniciales, semilla 101737, semilla del muestreador
#   20261010), de la referencia de junio (3 semillas), de agosto (20 semillas: 10 escritas en el código y el
#   resto primos generados con la semilla 20261009), de la ganancia (+1,0725 y −0,0275, ventana 501) y de los
#   cortes (9.000 a 15.000 de a 500; referencia 10.000).
# 3) Bayesiana (solo la lista ganadora): como s0006, con el techo del hessian en 1 (el mejor de s0006 quedó en 0,094)
SEARCH_SPACE = {
    "num_iterations": (64, 4096),
    "num_leaves": (16, 2048),
    "min_sum_hessian_in_leaf": (1e-6, 1.0),
}
N_TRIALS = 21  # 1 con los valores de s0006 + 10 al azar + 10 guiadas
N_STARTUP_TRIALS = 11
BO_SEED = 101737
SAMPLER_SEED = 20261010

# 4) Referencia de junio: 3 semillas
JUNE_SEEDS = CMP_SEEDS[:3]

# 5) Agosto
N_SEMILLAS_AGOSTO = 20
SEEDS_S0004 = [101737, 303011, 602909, 707717, 906007, 568318, 641463, 591763, 616818, 193376]
SEED_LIST_RNG = 20261009  # la misma lista de primos de s0005 y s0006

# Ganancia y cortes
GAIN_BAJA2 = 1.0725
GAIN_OTHER = -0.0275
GAIN_WINDOW = 501
CORTES = list(range(9_000, 15_001, 500))
CORTE_REF = 10_000  # el corte de s0006 y s0007

# [Anotación · líneas 105–118] En modo prueba reduce iteraciones, semillas, corridas, ventana y cortes, y
#   fuerza la lista media_1desvio para recorrer todos los pasos.
PRUEBA_FRACCION_CLIENTES = 0.05
if MODO_PRUEBA:
    SEL_VALUES = {**SEL_VALUES, "num_iterations": 100}
    S0006_VALUES = {**S0006_VALUES, "num_iterations": 60}
    CMP_SEEDS = CMP_SEEDS[:2]
    JUNE_SEEDS = CMP_SEEDS[:2]
    SEARCH_SPACE = {"num_iterations": (20, 80), "num_leaves": (16, 128), "min_sum_hessian_in_leaf": (1e-6, 1.0)}
    N_TRIALS, N_STARTUP_TRIALS = 3, 2
    N_SEMILLAS_AGOSTO = 2
    GAIN_WINDOW = 51
    CORTES = [300, 500, 700]
    CORTE_REF = 500
    if FORZAR_LISTA is None:
        FORZAR_LISTA = "media_1desvio"  # en la prueba se sigue igual, para recorrer todo el camino


# [Anotación · líneas 121–146] Define is_prime() y prime_seeds() y arma la lista de 20 semillas de agosto: las
#   10 escritas en el código y 10 primos de 6 cifras generados con numpy.random.default_rng(20261009).
def is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 2
    return True


def prime_seeds(n, exclude, rng_seed=SEED_LIST_RNG, low=100_000, high=999_999):
    """n primos distintos de 6 cifras, siempre en el mismo orden (la lista de s0005)."""
    rng = np.random.default_rng(rng_seed)
    seeds, taken = [], set(exclude)
    while len(seeds) < n:
        candidate = int(rng.integers(low, high + 1))
        if candidate not in taken and is_prime(candidate):
            seeds.append(candidate)
            taken.add(candidate)
    return seeds


FINAL_SEEDS = (SEEDS_S0004 + prime_seeds(max(N_SEMILLAS_AGOSTO - len(SEEDS_S0004), 0), exclude=SEEDS_S0004))[:N_SEMILLAS_AGOSTO]

# [Anotación · líneas 148–173] Elige las carpetas: ~/buckets/b1/exp/c9920, ~/local/c9920 y ~/datasets si
#   existe el bucket y no está definida DMEYF_OUT_DIR; si no, outputs/c9920 y data/ dentro del repositorio,
#   modificables por variables de entorno. Crea 1_seleccion, 2_comparacion, 3_bayesiana, 4_referencia_junio,
#   5_agosto y 6_cortes, y define log.txt.
# Carpetas. En Google Cloud: resultados en el bucket (sobreviven si se borra la máquina) y temporales en el disco local.
BUCKET = Path.home() / "buckets" / "b1"
EN_GCP = BUCKET.is_dir() and "DMEYF_OUT_DIR" not in os.environ
if EN_GCP:
    OUT_DIR = BUCKET / "exp" / EXP_ID
    LOCAL_DIR = Path.home() / "local" / EXP_ID
    DATA_DIR = Path.home() / "datasets"
else:
    cwd = Path.cwd().resolve()
    BASE_DIR = next((p for p in [cwd, *cwd.parents] if (p / "01_c9920_canaritos_asesinos").is_dir()), cwd)  # raíz del repo
    OUT_DIR = Path(os.environ.get("DMEYF_OUT_DIR", BASE_DIR / "outputs" / EXP_ID))
    LOCAL_DIR = OUT_DIR / "local"
    DATA_DIR = Path(os.environ.get("DMEYF_DATA_DIR", BASE_DIR / "data"))
if MODO_PRUEBA:
    OUT_DIR, LOCAL_DIR = OUT_DIR / "prueba", LOCAL_DIR / "prueba"

SEL_DIR = OUT_DIR / "1_seleccion"
CMP_DIR = OUT_DIR / "2_comparacion"
BO_DIR = OUT_DIR / "3_bayesiana"
JUNE_DIR = OUT_DIR / "4_referencia_junio"
AUG_DIR = OUT_DIR / "5_agosto"
CUTS_DIR = OUT_DIR / "6_cortes"
for folder in (DATA_DIR, OUT_DIR, LOCAL_DIR, SEL_DIR, CMP_DIR, BO_DIR, JUNE_DIR, AUG_DIR, CUTS_DIR):
    folder.mkdir(parents=True, exist_ok=True)

LOG_PATH = OUT_DIR / "log.txt"


# [Anotación · líneas 176–217] log() imprime cada mensaje y lo agrega con fecha y hora a log.txt. apagar_vm()
#   lanza en un proceso separado el script ~/machina/direct/apagar_vm.sh y después un gcloud compute instances
#   delete con los datos del servidor de metadatos; no hace nada si no está en Google Cloud o el script no
#   existe, y la parte de gcloud se saltea si el nombre de la máquina empieza con desktop o es instance-
#   instalacion. _apagar_si_falla se registra como callback post_run_cell de IPython: ante un error distinto de
#   KeyboardInterrupt lo escribe en el log y, si la bandera está activa, borra la máquina.
def log(*parts):
    """Imprime y además deja la línea en log.txt (en el bucket), por si se cierra el navegador."""
    text = " ".join(str(part) for part in parts)
    print(text, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(time.strftime("%Y-%m-%d %H:%M:%S  ") + text + "\n")


def apagar_vm(motivo):
    """Borra esta máquina virtual con el script de la cátedra (las plantillas spot se borran, no se apagan)."""
    script = Path.home() / "machina" / "direct" / "apagar_vm.sh"
    if not EN_GCP or not script.exists():
        log(f"[apagado] {motivo}: no estoy en una máquina virtual de la cátedra, no apago nada.")
        return
    log(f"[apagado] {motivo}: borrando la máquina virtual. Los resultados quedaron en {OUT_DIR}")
    # Si el script de la cátedra no encuentra el proyecto (fcur_project_id vacío), borra igual con los metadatos de Google (nunca una desktop).
    respaldo = f"""bash {script}
case "$(hostname)" in desktop*|instance-instalacion) exit 0;; esac
MD=http://metadata.google.internal/computeMetadata/v1; H="Metadata-Flavor: Google"
ZONA=$(curl -s -H "$H" $MD/instance/zone)
gcloud --quiet compute instances delete "$(curl -s -H "$H" $MD/instance/name)" --zone="${{ZONA##*/}}" --project="$(curl -s -H "$H" $MD/project/project-id)"
"""
    with open(OUT_DIR / "apagado.txt", "a") as salida:
        subprocess.Popen(["bash", "-c", respaldo], stdout=salida, stderr=subprocess.STDOUT, start_new_session=True)


def _apagar_si_falla(result):
    error = result.error_in_exec
    if error is not None and not isinstance(error, KeyboardInterrupt):
        log(f"[error] {type(error).__name__}: {error}")
        if APAGAR_SI_FALLA:
            apagar_vm("una celda falló")


try:
    _ip = get_ipython()
    for _callback in list(_ip.events.callbacks["post_run_cell"]):
        if getattr(_callback, "__name__", "") == "_apagar_si_falla":
            _ip.events.unregister("post_run_cell", _callback)
    _ip.events.register("post_run_cell", _apagar_si_falla)
except NameError:
    pass

# [Anotación · líneas 219–225] Escribe en el log la configuración de la corrida: carpetas, parámetros de la
#   selección y de la comparación y las semillas de agosto.
log("=" * 70)
log(f"{EXP_ID} | modo prueba: {MODO_PRUEBA} | Google Cloud: {EN_GCP} | hilos: {NUM_THREADS}")
log("Resultados:", OUT_DIR)
log("Datos:", DATA_DIR, "| temporales:", LOCAL_DIR)
log("Selección:", SEL_VALUES, SEL_FIXED, "| mes", SEL_MONTH, "| semillas", SEL_SEEDS)
log("Comparación:", S0006_VALUES, "| meses", CMP_TRAIN_MONTHS, "->", VALID_MONTH, "| semillas", CMP_SEEDS)
log("Semillas de agosto:", FINAL_SEEDS)

#%% celda 3 [texto]
## Instalación de zLightGBM y Optuna

zLightGBM no es un paquete de Python: se compila su núcleo C++ y se coloca dentro del paquete `lightgbm==4.6.0`, en `~/zlgb` (unos minutos, una vez por máquina). Sin el parámetro `canaritos` se comporta como LightGBM común: así se usa en la selección. Con `canaritos = n`, nunca corta por las primeras n columnas.

#%% celda 4 [código]
# [Anotación · líneas 233–265] Arma un script de bash que baja zlightgbm_4.6.0.99.tar.gz, compila sus fuentes
#   C++ con g++ (-O3, OpenMP) en lib_lightgbm.so, instala lightgbm==4.6.0 en una carpeta aparte y reemplaza su
#   biblioteca por la compilada, todo en ~/zlgb (o en ZLGB_DIR). Lo ejecuta sólo si la biblioteca no existe.
#   Pone esa carpeta primera en sys.path, importa lightgbm y corta con error si el módulo se cargó desde otro
#   lugar.
ZLGB_URL = "https://storage.googleapis.com/open-courses/dmeyf2025-e4a2/zlightgbm_4.6.0.99.tar.gz"
BUILD_SCRIPT = r"""
set -euo pipefail
TARGET="$1"
WORK="$TARGET"_build
mkdir -p "$WORK" && cd "$WORK"
curl -sSfLO {url}
tar xzf zlightgbm_4.6.0.99.tar.gz
S=zlightgbm/src
FILES=$(find $S/src -name '*.cpp' -not -path '*/cuda/*' -not -name lightgbm_R.cpp -not -name main.cpp | grep -v 'gpu_tree_learner\|cuda')
g++ -O3 -std=c++17 -fPIC -shared -fopenmp -DUSE_SOCKET -DMM_MALLOC -DMM_PREFETCH -DFMT_HEADER_ONLY \
  -I$S/include -I$S/external_libs/fmt/include -I$S/external_libs/fast_double_parser/include \
  $FILES -o lib_lightgbm.so
"{python}" -m pip install -q "lightgbm==4.6.0" --target "$WORK/pkg" --no-deps
rm -rf "$TARGET" && mkdir -p "$TARGET"
cp -r "$WORK/pkg/lightgbm" "$TARGET/lightgbm"
cp "$WORK/lib_lightgbm.so" "$TARGET/lightgbm/lib/lib_lightgbm.so"
""".format(url=ZLGB_URL, python=sys.executable)

ZLGB_DIR = Path(os.environ.get("ZLGB_DIR", Path.home() / "zlgb"))
if not (ZLGB_DIR / "lightgbm" / "lib" / "lib_lightgbm.so").exists():
    log("Compilando zlightgbm en", ZLGB_DIR, "(tarda unos minutos)...")
    start = time.perf_counter()
    subprocess.run(["bash", "-c", BUILD_SCRIPT, "build", str(ZLGB_DIR)], check=True)
    log(f"zlightgbm compilado en {(time.perf_counter() - start) / 60:.1f} min")

if "lightgbm" in sys.modules and not Path(sys.modules["lightgbm"].__file__).resolve().is_relative_to(ZLGB_DIR.resolve()):
    raise RuntimeError("El kernel ya tiene cargado otro lightgbm. Reiniciá el kernel y volvé a ejecutar.")
sys.path.insert(0, str(ZLGB_DIR))
import lightgbm as lgb

if not Path(lgb.__file__).resolve().is_relative_to(ZLGB_DIR.resolve()):
    raise RuntimeError(f"Se cargó lightgbm desde {lgb.__file__}, no desde {ZLGB_DIR}.")

# [Anotación · líneas 267–281] Prueba con datos sintéticos (20.000 filas, 10 columnas uniformes adelante y 10
#   normales): entrena 20 rondas con y sin el parámetro canaritos = 10 y exige que con el parámetro haya 0
#   cortes en las primeras 10 columnas y sin él al menos uno; si no se cumple, corta con error.
# Prueba: con canaritos adelante, zlightgbm nunca los usa; sin el parámetro, sí (LightGBM común).
_rng = np.random.default_rng(0)
_X = _rng.normal(size=(20_000, 10))
_y = ((_X[:, 0] + _X[:, 1] * _X[:, 2] + _rng.normal(size=20_000) * 2) > 1).astype(int)
_Xc = np.hstack([_rng.uniform(size=(20_000, 10)), _X])
_params = dict(objective="binary", num_leaves=256, min_data_in_leaf=5, learning_rate=0.05,
               verbose=-1, seed=1, num_threads=NUM_THREADS)
_plain = lgb.train(_params, lgb.Dataset(_Xc, label=_y), num_boost_round=20)
_canary = lgb.train({**_params, "canaritos": 10}, lgb.Dataset(_Xc, label=_y), num_boost_round=20)
_splits_plain = int(_plain.feature_importance("split")[:10].sum())
_splits_canary = int(_canary.feature_importance("split")[:10].sum())
if _splits_canary != 0 or _splits_plain == 0:
    raise RuntimeError("Este lightgbm no parece ser zlightgbm: el parámetro canaritos no tuvo efecto.")
del _rng, _X, _y, _Xc, _plain, _canary
log(f"zlightgbm OK ({lgb.__file__}): cortes en canaritos sin el parámetro {_splits_plain}, con el parámetro 0")

# [Anotación · líneas 283–292] Importa Optuna (lo instala con pip, sin versión fija, si no está), baja su
#   nivel de mensajes a WARNING y escribe la versión en el log.
try:
    import optuna
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "optuna"], check=True)
    import importlib
    importlib.invalidate_caches()
    import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)
from optuna.trial import TrialState
log("Optuna", optuna.__version__)

#%% celda 5 [texto]
## Datos (igual que `s0006`)

- **Clase ternaria:** el crudo no la trae. Se arma con todas las fotos: para cada cliente y mes se mira si aparece uno y dos meses después (CONTINUA, BAJA+1, BAJA+2). Julio y agosto quedan sin clase. Positivos: BAJA+1 y BAJA+2.
- `ccajas_depositos` en NA en 202105; se conservan los préstamos personales (152 campos).
- lag1, delta_lag1, lag2 y delta_lag2 con valores crudos; después ranking con cero fijo por variable y por mes. 760 variables reales.
- Las variables reales quedan en memoria (`R_fit`: marzo a junio ordenado por mes; `R_pred`: agosto). Los canaritos se agregan en cada entrenamiento.
- En modo prueba se usa el 5 % de los clientes (siempre los mismos).

#%% celda 6 [código]
# [Anotación · líneas 304–311] Busca competencia_01_crudo.csv en la carpeta de datos (acepta también el nombre
#   comptetencia_01_crudo.csv); si no está, lo baja de DATA_URL a un archivo temporal y lo renombra.
data_start = time.perf_counter()
RAW_PATH = next((p for p in [DATA_DIR / "competencia_01_crudo.csv", DATA_DIR / "comptetencia_01_crudo.csv"] if p.exists()), None)
if RAW_PATH is None:
    RAW_PATH = DATA_DIR / "competencia_01_crudo.csv"
    log("Bajando el dataset a", RAW_PATH)
    urlretrieve(DATA_URL, RAW_PATH.with_suffix(".tmp"))
    os.replace(RAW_PATH.with_suffix(".tmp"), RAW_PATH)
log("Dataset:", RAW_PATH, f"({RAW_PATH.stat().st_size / 2**20:.0f} MB)")

# [Anotación · líneas 313–335] Arma la clase ternaria con todos los meses del archivo. Convierte foto_mes a un
#   número de mes corrido (año × 12 + mes), ordena por cliente y obtiene los dos períodos siguientes de cada
#   cliente. Marca CONTINUA los registros anteriores al penúltimo período; BAJA+1 los anteriores al último cuyo
#   período siguiente falta o no es el mes consecutivo; BAJA+2 los anteriores al penúltimo que tienen el mes
#   siguiente y no el subsiguiente. Las asignaciones posteriores pisan a las anteriores. El último período queda
#   sin clase y el penúltimo sólo recibe BAJA+1 cuando falta el mes siguiente. Devuelve las etiquetas en el
#   orden de filas del CSV.
# Clase ternaria con todas las fotos (idéntico a s0004 y s0006).
keys = pd.read_csv(RAW_PATH, usecols=["numero_de_cliente", "foto_mes"])
work = keys.copy()
work["_row_id"] = np.arange(len(work), dtype=np.int64)
work["periodo0"] = (work["foto_mes"] // 100) * 12 + work["foto_mes"] % 100
work = work.sort_values(["numero_de_cliente", "periodo0"], kind="mergesort")
periods = work.groupby("numero_de_cliente", sort=False)["periodo0"]
work["periodo1"] = periods.shift(-1)
work["periodo2"] = periods.shift(-2)
last_period = int(work["periodo0"].max())
penultimate_period = last_period - 1
clase = pd.Series(pd.NA, index=work.index, dtype="string")
continua = work["periodo0"] < penultimate_period
baja_1 = (work["periodo0"] < last_period) & (work["periodo1"].isna() | (work["periodo0"] + 1 < work["periodo1"]))
baja_2 = (
    (work["periodo0"] < penultimate_period)
    & (work["periodo0"] + 1 == work["periodo1"])
    & (work["periodo2"].isna() | (work["periodo0"] + 2 < work["periodo2"]))
)
clase.loc[continua] = "CONTINUA"
clase.loc[baja_1] = "BAJA+1"
clase.loc[baja_2] = "BAJA+2"
labels = pd.Series(clase.to_numpy(), index=work["_row_id"].to_numpy()).sort_index().reset_index(drop=True)


# [Anotación · líneas 338–351] release_memory() llama al recolector de basura y a malloc_trim de libc.
#   client_in_sample() devuelve todos los clientes salvo en modo prueba, donde conserva aquellos cuyo número
#   multiplicado por 2654435761, módulo 1.000, es menor que 50 (5 %).
def release_memory():
    gc.collect()
    try:
        import ctypes
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:
        pass


def client_in_sample(client_ids):
    """Modo prueba: el mismo 5 % de los clientes siempre (por número de cliente)."""
    if not MODO_PRUEBA:
        return np.ones(len(client_ids), dtype=bool)
    return (np.asarray(client_ids, dtype=np.int64) * 2654435761 % 1000) < PRUEBA_FRACCION_CLIENTES * 1000


# [Anotación · líneas 354–385] Nombra las dos columnas de préstamos personales (se usan más abajo en un
#   assert). Toma como campos base todas las columnas menos numero_de_cliente, foto_mes y clase_ternaria,
#   recorre el CSV en bloques de 25.000 filas, conserva los meses 202103 a 202108, asigna la clase por número de
#   fila y convierte cada campo a float32. Pone en NA ccajas_depositos en 202105.
LOAN_COLUMNS = ["cprestamos_personales", "mprestamos_personales"]
csv_columns = list(pd.read_csv(RAW_PATH, nrows=0).columns)
KEY_COLUMNS = {"numero_de_cliente", "foto_mes", "clase_ternaria", "_row_id"}
base_feature_names = [c for c in csv_columns if c not in KEY_COLUMNS]
n_base = len(base_feature_names)

key_parts, value_parts = [], []
offset = 0
for chunk in pd.read_csv(RAW_PATH, chunksize=25_000, low_memory=False):
    chunk_row_ids = np.arange(offset, offset + len(chunk), dtype=np.int64)
    offset += len(chunk)
    keep = chunk["foto_mes"].isin(NEEDED_MONTHS).to_numpy() & client_in_sample(chunk["numero_de_cliente"].to_numpy())
    if not keep.any():
        continue
    part = pd.DataFrame({
        "numero_de_cliente": chunk["numero_de_cliente"].to_numpy()[keep],
        "foto_mes": chunk["foto_mes"].to_numpy()[keep],
        "_row_id": chunk_row_ids[keep],
    })
    part["clase_ternaria"] = labels.iloc[part["_row_id"].to_numpy()].to_numpy()
    values = np.empty((int(keep.sum()), n_base), dtype=np.float32)
    for j, column in enumerate(base_feature_names):
        values[:, j] = pd.to_numeric(chunk[column], errors="coerce").astype("float32").to_numpy()[keep]
    key_parts.append(part)
    value_parts.append(values)
del chunk, part, values, keys, work, clase, labels
panel_keys = pd.concat(key_parts, ignore_index=True)
base_values = np.concatenate(value_parts)
del key_parts, value_parts
release_memory()

base_values[panel_keys["foto_mes"].eq(202105).to_numpy(), base_feature_names.index("ccajas_depositos")] = np.nan

# [Anotación · líneas 387–406] Para k = 1 y 2 calcula la posición de la observación k lugares antes del mismo
#   cliente y si existe. Separa las filas de entrenamiento (202103 a 202106, ordenadas por mes) y las de 202108.
# Posición de la observación anterior (k = 1) y de dos antes (k = 2) del mismo cliente.
clients = panel_keys["numero_de_cliente"].to_numpy()
order = np.lexsort((panel_keys["_row_id"].to_numpy(), panel_keys["foto_mes"].to_numpy(), clients))
sorted_clients = clients[order]
sorted_positions = np.arange(len(order))
previous = {}
for k in LAG_ORDERS:
    valid_sorted = sorted_positions >= k
    valid_sorted[valid_sorted] = sorted_clients[sorted_positions[valid_sorted] - k] == sorted_clients[valid_sorted]
    position = np.zeros(len(order), dtype=np.int64)
    valid = np.zeros(len(order), dtype=bool)
    position[order] = np.where(valid_sorted, order[np.maximum(sorted_positions - k, 0)], 0)
    valid[order] = valid_sorted
    previous[k] = (position, valid)
del clients, order, sorted_clients, sorted_positions, valid_sorted, position, valid

row_months = panel_keys["foto_mes"].to_numpy()
train_rows = np.flatnonzero(np.isin(row_months, TRAIN_MONTHS))
train_rows = train_rows[np.argsort(row_months[train_rows], kind="stable")]
future_rows = np.flatnonzero(row_months == PREDICT_MONTH)

# [Anotación · líneas 408–431] Arma los nombres de las variables: los campos originales y, para k = 1 y 2,
#   _lag{k} y _delta_lag{k} de cada campo (152 × 5 = 760). fill_real_columns() llena la matriz en bloques de
#   20.000 filas: valor actual, valor de la observación k lugares antes (NA si no existe) y la diferencia actual
#   − lag.
feature_names = list(base_feature_names)
for k in LAG_ORDERS:
    for column in base_feature_names:
        feature_names += [f"{column}_lag{k}", f"{column}_delta_lag{k}"]
N_REAL = len(feature_names)
feature_index = {name: i for i, name in enumerate(feature_names)}


def fill_real_columns(rows, block=20_000):
    """Originales, lags y deltas en el orden de feature_names."""
    out_all = np.empty((len(rows), N_REAL), dtype=np.float32)
    for start in range(0, len(rows), block):
        block_rows = rows[start:start + block]
        current = base_values[block_rows]
        out = out_all[start:start + len(block_rows)]
        out[:, :n_base] = current
        for k in LAG_ORDERS:
            position, valid = previous[k]
            lagged = base_values[position[block_rows]]
            lagged[~valid[block_rows]] = np.nan
            first = n_base * (2 * k - 1)
            out[:, first:first + 2 * n_base:2] = lagged
            out[:, first + 1:first + 2 * n_base:2] = current - lagged
    return out_all


# [Anotación · líneas 434–466] Construye R_fit (202103–202106) y R_pred (202108), guarda cliente, mes y clase,
#   la disponibilidad de cada lag y los clientes de agosto. La clase binaria vale 1 si la clase ternaria no es
#   CONTINUA. Ubica el bloque de filas de cada mes y define las filas de la comparación (202103–202105), las de
#   validación (202106) y todas, junto con las máscaras de junio de positivos y de BAJA+2.
R_fit = fill_real_columns(train_rows)
R_pred = fill_real_columns(future_rows)
train_info = panel_keys.loc[train_rows, ["numero_de_cliente", "foto_mes", "clase_ternaria"]].reset_index(drop=True)
lag_available = {k: {"train": previous[k][1][train_rows], "future": previous[k][1][future_rows]} for k in LAG_ORDERS}
future_ids = panel_keys.loc[future_rows, "numero_de_cliente"].to_numpy(dtype=np.int64)
y_fit = (~train_info["clase_ternaria"].eq("CONTINUA")).astype(np.int8).to_numpy()
del panel_keys, base_values, previous, row_months
release_memory()

fit_months = train_info["foto_mes"].to_numpy()
MONTH_SLICES = {}
for month in TRAIN_MONTHS:
    rows = np.flatnonzero(fit_months == month)
    if len(rows) == 0 or rows[-1] - rows[0] + 1 != len(rows):
        raise RuntimeError(f"Las filas de {month} no forman un bloque contiguo")
    MONTH_SLICES[month] = slice(int(rows[0]), int(rows[-1]) + 1)
del rows


def months_slice(months):
    months = sorted(months)
    selector = slice(MONTH_SLICES[months[0]].start, MONTH_SLICES[months[-1]].stop)
    if sorted(np.unique(fit_months[selector]).tolist()) != months:
        raise RuntimeError(f"El bloque {months} no es contiguo")
    return selector


CMP_ROWS = months_slice(CMP_TRAIN_MONTHS)
VALID_ROWS = MONTH_SLICES[VALID_MONTH]
ALL_ROWS = slice(0, R_fit.shape[0])
june_ids = train_info["numero_de_cliente"].to_numpy(dtype=np.int64)[VALID_ROWS]
june_positive = y_fit[VALID_ROWS].astype(bool)
june_baja2 = train_info["clase_ternaria"].eq("BAJA+2").to_numpy(dtype=bool)[VALID_ROWS]

# [Anotación · líneas 468–481] Controles con assert: 152 campos base que incluyen cprestamos_personales y
#   mprestamos_personales, 760 variables sin nombres repetidos, todas las filas de entrenamiento con clase,
#   ccajas_depositos en NA en 202105, lag2 ausente en 202103 y 202104 y presente en más del 80 % de las filas de
#   202105, 202106 y 202108. Deja en el log los conteos por mes y clase.
# Auditoría básica (la completa está en s0006, con el mismo código).
assert n_base == 152 and all(c in base_feature_names for c in LOAN_COLUMNS)
assert N_REAL == 760 and len(set(feature_names)) == N_REAL
assert train_info["clase_ternaria"].notna().all()
assert (np.diff(fit_months) >= 0).all()
assert np.isnan(R_fit[MONTH_SLICES[202105], feature_index["ccajas_depositos"]]).all()
coverage = pd.DataFrame({"foto_mes": fit_months, "tiene_lag2": lag_available[2]["train"]}).groupby("foto_mes").mean()
assert coverage.loc[[202103, 202104], "tiene_lag2"].max() == 0
assert coverage.loc[[202105, 202106], "tiene_lag2"].min() > 0.8
assert lag_available[2]["future"].mean() > 0.8

log(f"Clase: {train_info.groupby(['foto_mes', 'clase_ternaria']).size().unstack().to_dict('index')}")
log(f"Filas: {R_fit.shape[0]} de marzo a junio, {R_pred.shape[0]} de agosto | {N_REAL} variables reales | "
    f"datos en {(time.perf_counter() - data_start) / 60:.1f} min")

#%% celda 7 [texto]
## Ranking con cero fijo (igual que `s0006`)

Cada variable real, por separado y por mes: 0 → 0, NA → NA, positivos en (0, 1], negativos en [−1, 0), empates con rango promedio.

#%% celda 8 [código]
# [Anotación · líneas 489–506] rank_cero_fijo() transforma un vector: el 0 queda en 0 y el NA en NA; los
#   positivos se reemplazan por su rango promedio dividido por la cantidad de positivos, en (0, 1]; los
#   negativos, por menos el rango de su valor absoluto dividido por la cantidad de negativos, en [−1, 0). Sigue
#   un assert con un ejemplo de 10 valores.
def rank_cero_fijo(values):
    ranked = np.full(values.shape, np.nan, dtype=np.float32)
    ranked[values == 0] = 0.0
    positive = values > 0
    negative = values < 0
    n_positive = int(positive.sum())
    n_negative = int(negative.sum())
    if n_positive:
        ranked[positive] = pd.Series(values[positive]).rank(method="average").to_numpy() / n_positive
    if n_negative:
        ranked[negative] = -pd.Series(-values[negative]).rank(method="average").to_numpy() / n_negative
    return ranked


_test = rank_cero_fijo(np.array([0, -50, 10, np.nan, 30, -5, 10, 1000, -50, -1], dtype=np.float32))
_expected = np.array([0, -0.875, 0.375, np.nan, 0.75, -0.5, 0.375, 1, -0.875, -0.25], dtype=np.float32)
assert np.allclose(_test, _expected, equal_nan=True), _test
del _test, _expected

# [Anotación · líneas 508–517] Aplica rank_cero_fijo() a cada una de las 760 columnas por separado dentro de
#   cada mes de R_fit y dentro de agosto en R_pred. Verifica que la cantidad de NA no cambie y que todo quede
#   entre −1 y 1.
rank_start = time.perf_counter()
for matrix, selector in [*[(R_fit, MONTH_SLICES[m]) for m in TRAIN_MONTHS], (R_pred, slice(0, R_pred.shape[0]))]:
    block = matrix[selector]
    na_before = np.isnan(block).sum()
    for j in range(N_REAL):
        block[:, j] = rank_cero_fijo(block[:, j])
    assert np.isnan(block).sum() == na_before
    assert np.nanmin(block) >= -1.0 and np.nanmax(block) <= 1.0
release_memory()
log(f"Ranking listo en {time.perf_counter() - rank_start:.0f} s")

#%% celda 9 [texto]
## Funciones comunes

Métricas de junio (AUC, ganancia suavizada como en `s0006`), guardado seguro (escribe un temporal y lo renombra) y armado de matrices con canaritos.

#%% celda 10 [código]
# [Anotación · líneas 525–546] Funciones de guardado: save_atomic() escribe en un archivo .tmp y lo renombra;
#   save_json() y save_npy() la usan; load_json() lee un JSON; canonical() pasa un objeto por JSON para
#   compararlo con lo guardado.
def save_atomic(path, write):
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as handle:
        write(handle)
    os.replace(tmp, path)


def save_json(path, data):
    text = json.dumps(data, ensure_ascii=False, indent=2)
    save_atomic(path, lambda handle: handle.write(text.encode("utf-8")))


def save_npy(path, array):
    save_atomic(path, lambda handle: np.save(handle, array))


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(data):
    return json.loads(json.dumps(data))


# [Anotación · líneas 549–578] auc_score() calcula el AUC por suma de rangos. gain_curve() acumula +1,0725 por
#   cada BAJA+2 y −0,0275 por cada otro registro en orden de puntaje descendente y suaviza con una media móvil
#   centrada de 501 posiciones. june_metrics() devuelve el AUC de junio, el máximo de la ganancia suavizada, su
#   posición y la ganancia en el corte 10.000. Sigue un assert del AUC con valores a mano.
def auc_score(positive, scores):
    positive = np.asarray(positive, dtype=bool)
    n_positive = int(positive.sum())
    n_negative = len(positive) - n_positive
    ranks = pd.Series(np.asarray(scores, dtype=np.float64)).rank(method="average").to_numpy()
    return float((ranks[positive].sum() - n_positive * (n_positive + 1) / 2) / (n_positive * n_negative))


def gain_curve(baja2, scores):
    order = np.argsort(-np.asarray(scores, dtype=np.float64), kind="stable")
    cumulative = np.cumsum(np.where(baja2[order], GAIN_BAJA2, GAIN_OTHER))
    smooth = pd.Series(cumulative).rolling(window=GAIN_WINDOW, center=True, min_periods=GAIN_WINDOW).mean().to_numpy()
    return cumulative, smooth


def june_metrics(scores):
    _, smooth = gain_curve(june_baja2, scores)
    best = int(np.nanargmax(smooth))
    return {
        "auc": auc_score(june_positive, scores),
        "ganancia_maxima": float(smooth[best]),
        "mejor_corte": best + 1,
        f"ganancia_corte_{CORTE_REF}": float(smooth[CORTE_REF - 1]),
    }


_positive = np.array([1, 0, 1, 0, 0, 1, 0, 0], dtype=bool)
_scores = np.array([0.9, 0.8, 0.8, 0.5, 0.4, 0.4, 0.2, 0.1])
assert np.isclose(auc_score(_positive, _scores), 12 / 15)
del _positive, _scores


# [Anotación · líneas 581–600] zlgb_params() arma los parámetros de zLightGBM: objective binary, metric None,
#   boosting gbdt, canaritos igual a la cantidad de canaritos, learning_rate 0,005, feature_fraction 0,5,
#   feature_fraction_bynode 0,2, min_data_in_leaf 0, max_bin 31, y num_leaves, min_sum_hessian_in_leaf y seed
#   recibidos.
def zlgb_params(values, n_canaries, seed):
    """Configuración de s0006 con canaritos 1 a 1. num_iterations va aparte."""
    return {
        "objective": "binary",
        "metric": "None",
        "boosting": "gbdt",
        "canaritos": int(n_canaries),
        "learning_rate": LEARNING_RATE,
        "feature_fraction": FEATURE_FRACTION,
        "feature_fraction_bynode": FEATURE_FRACTION_BYNODE,
        "min_data_in_leaf": MIN_DATA_IN_LEAF,
        "num_leaves": int(values["num_leaves"]),
        "min_sum_hessian_in_leaf": float(values["min_sum_hessian_in_leaf"]),
        "max_bin": MAX_BIN,
        "num_threads": NUM_THREADS,
        "feature_pre_filter": False,
        "force_col_wise": True,
        "verbose": -1,
        "seed": int(seed),
    }


# [Anotación · líneas 603–632] with_canaries() arma la matriz con n columnas uniformes al azar seguidas de las
#   n variables elegidas. train_zlgb() entrena zLightGBM durante num_iterations rondas y corta con error si el
#   modelo usó algún canarito en un corte. predict_june() predice junio con canaritos generados con semilla + 1.
def with_canaries(real, columns, seed):
    """Matriz [canaritos | variables reales elegidas], con un canarito por variable (zLightGBM los quiere adelante)."""
    n = len(columns)
    out = np.empty((real.shape[0], 2 * n), dtype=np.float32)
    out[:, :n] = np.random.default_rng(seed).random((real.shape[0], n), dtype=np.float32)
    out[:, n:] = real[:, columns]
    return out


def train_zlgb(columns, values, seed, train_rows):
    """zLightGBM con las variables `columns` y n canaritos adelante. Verifica que no corte por canaritos."""
    n = len(columns)
    X = with_canaries(R_fit[train_rows], columns, seed)
    names = [f"canarito_{i:04d}" for i in range(1, n + 1)] + [feature_names[j] for j in columns]
    dataset = lgb.Dataset(X, label=y_fit[train_rows], feature_name=names, free_raw_data=True,
                          params=zlgb_params(values, n, seed))
    booster = lgb.train(zlgb_params(values, n, seed), dataset, num_boost_round=int(values["num_iterations"]))
    del X, dataset
    release_memory()
    canary_splits = int(booster.feature_importance("split")[:n].sum())
    if canary_splits:
        raise RuntimeError(f"El modelo cortó {canary_splits} veces por canaritos: zlightgbm no está podando")
    return booster


def predict_june(booster, columns, seed):
    return booster.predict(with_canaries(R_fit[VALID_ROWS], columns, seed + 1))


log("Funciones listas")

#%% celda 11 [texto]
## 1. Selección: LightGBM común con 20 % de canaritos (3 repeticiones)

En cada repetición:

1. Filas de **mayo**: todas las BAJA+1 y BAJA+2 y el 10 % de CONTINUA (como z495).
2. Se agregan 152 canaritos (20 % de 760) con números al azar entre 0 y 1.
3. LightGBM común con los parámetros de z495: 2.848 árboles, 71 hojas, `min_sum_hessian_in_leaf` 0,0067, learning_rate 0,005, `feature_fraction` 0,5, `min_data_in_leaf` 0, `max_bin` 31.
4. Importancia por **gain**. Se numeran las variables usadas: 1 = la de más gain. Las que el modelo nunca usó no reciben número (como `lgb.importance` en R) y mueren.
5. Media y desvío de los números de los canaritos (desvío muestral, como `sd` en R) y los puntos de asesinato: media + 1 desvío y media + 2 desvíos.

Para controlar que el modelo sea "razonable" se muestra su AUC en junio (solo informativo, no decide nada).

#%% celda 12 [código]
# [Anotación · líneas 648–671] Calcula la cantidad de canaritos de la selección como el 20 % de las variables
#   reales redondeado, arma sus nombres y la configuración que se guarda con cada repetición. selection_params()
#   define un LightGBM sin el parámetro canaritos: objective binary, learning_rate 0,005, feature_fraction 0,5,
#   min_data_in_leaf 0, max_bin 31, 71 hojas y min_sum_hessian_in_leaf 0,0067.
N_SEL_CANARIES = int(round(SEL_CANARY_FRACTION * N_REAL))
SEL_CANARY_NAMES = [f"canarito_{i:04d}" for i in range(1, N_SEL_CANARIES + 1)]
SEL_CONFIG = canonical({
    "mes": SEL_MONTH, "undersampling": SEL_UNDERSAMPLING, "canaritos": N_SEL_CANARIES,
    "valores": SEL_VALUES, "fijos": SEL_FIXED, "variables": feature_names, "prueba": MODO_PRUEBA,
})


def selection_params(seed):
    return {
        "objective": "binary",
        "metric": "None",
        "boosting": "gbdt",
        "learning_rate": SEL_FIXED["learning_rate"],
        "feature_fraction": SEL_FIXED["feature_fraction"],
        "min_data_in_leaf": SEL_FIXED["min_data_in_leaf"],
        "max_bin": SEL_FIXED["max_bin"],
        "num_leaves": SEL_VALUES["num_leaves"],
        "min_sum_hessian_in_leaf": SEL_VALUES["min_sum_hessian_in_leaf"],
        "num_threads": NUM_THREADS,
        "feature_pre_filter": False,
        "verbose": -1,
        "seed": int(seed),
    }


# [Anotación · líneas 674–701] run_selection() hace una repetición: toma de 202105 todas las filas positivas
#   (BAJA+1 o BAJA+2) y cada CONTINUA con probabilidad 0,10, agrega las columnas de canaritos después de las
#   reales y entrena 2.848 rondas. Calcula el AUC de junio como dato informativo, ordena las variables por gain
#   descendente y numera desde 1 las que tienen gain mayor que 0; las no usadas quedan sin número.
def run_selection(seed):
    """Una repetición de la selección. Devuelve la tabla de importancia con los números (ids)."""
    month = MONTH_SLICES[SEL_MONTH]
    rng = np.random.default_rng(seed)
    month_rows = np.arange(month.start, month.stop)
    keep = (y_fit[month_rows] == 1) | (rng.random(len(month_rows)) < SEL_UNDERSAMPLING)
    rows = month_rows[keep]
    X = np.empty((len(rows), N_REAL + N_SEL_CANARIES), dtype=np.float32)  # [variables reales | 152 canaritos]
    X[:, :N_REAL] = R_fit[rows]
    X[:, N_REAL:] = rng.random((len(rows), N_SEL_CANARIES), dtype=np.float32)
    names = feature_names + SEL_CANARY_NAMES
    dataset = lgb.Dataset(X, label=y_fit[rows], feature_name=names, free_raw_data=True, params=selection_params(seed))
    booster = lgb.train(selection_params(seed), dataset, num_boost_round=SEL_VALUES["num_iterations"])
    X_june = np.empty((VALID_ROWS.stop - VALID_ROWS.start, N_REAL + N_SEL_CANARIES), dtype=np.float32)
    X_june[:, :N_REAL] = R_fit[VALID_ROWS]
    X_june[:, N_REAL:] = rng.random((len(X_june), N_SEL_CANARIES), dtype=np.float32)
    june_auc = auc_score(june_positive, booster.predict(X_june))
    table = pd.DataFrame({
        "variable": names,
        "canarito": [False] * N_REAL + [True] * N_SEL_CANARIES,
        "gain": booster.feature_importance("gain"),
        "splits": booster.feature_importance("split"),
    }).sort_values("gain", ascending=False, kind="stable").reset_index(drop=True)
    used = table["gain"] > 0
    table["id"] = np.where(used, np.arange(1, len(table) + 1), np.nan)
    del X, X_june, dataset, booster
    release_memory()
    return table, {"filas": int(len(rows)), "positivos": int(y_fit[rows].sum()), "auc_junio": june_auc}


# [Anotación · líneas 704–718] cut_stats() toma los números de los canaritos usados y calcula su media y su
#   desvío muestral; los puntos de corte son media + 1 desvío y media + 2 desvíos. Con menos de 2 canaritos
#   usados fija el corte después de la última posición, de modo que sólo se eliminan las variables no usadas.
def cut_stats(table):
    canary_ids = table.loc[table["canarito"] & table["id"].notna(), "id"].to_numpy(dtype=float)
    stats = {
        "variables_usadas": int(table["id"].notna().sum()),
        "canaritos_usados": int(len(canary_ids)),
        "primer_canarito": float(canary_ids.min()) if len(canary_ids) else None,
    }
    if len(canary_ids) >= 2:
        mean, sd = float(canary_ids.mean()), float(canary_ids.std(ddof=1))
        stats.update({"media": mean, "desvio": sd})
        stats.update({f"corte_{name}": mean + k * sd for name, k in CUT_POINTS.items()})
    else:  # sin canaritos usados no hay contra qué medir: no se mata por el punto (solo las no usadas)
        stats.update({"media": None, "desvio": None})
        stats.update({f"corte_{name}": float(len(table) + 1) for name in CUT_POINTS})
    return stats


# [Anotación · líneas 721–742] Ejecuta la selección con las semillas 101737, 303011 y 602909, o reusa lo
#   guardado si la configuración coincide. Guarda por semilla la tabla de importancia y un resumen (filas,
#   positivos, AUC de junio, media, desvío, cortes) y escribe resumen.csv.
selection = {}
for seed in SEL_SEEDS:
    table_path, info_path = SEL_DIR / f"importancia_seed{seed}.csv", SEL_DIR / f"resumen_seed{seed}.json"
    if table_path.exists() and info_path.exists() and load_json(info_path)["config"] == SEL_CONFIG:
        table, info = pd.read_csv(table_path), load_json(info_path)
        log(f"  selección semilla {seed}: ya estaba guardada")
    else:
        start = time.perf_counter()
        table, info = run_selection(seed)
        info = {**info, **cut_stats(table), "minutos": round((time.perf_counter() - start) / 60, 1), "config": SEL_CONFIG}
        table.to_csv(table_path.with_name(table_path.name + ".tmp"), index=False)
        os.replace(table_path.with_name(table_path.name + ".tmp"), table_path)
        save_json(info_path, info)
        log(f"  selección semilla {seed}: {info['filas']} filas ({info['positivos']} positivos), "
            f"AUC junio {info['auc_junio']:.4f}, {info['minutos']} min")
    selection[seed] = (table, info)

sel_summary = pd.DataFrame([
    {"semilla": seed, **{k: v for k, v in info.items() if k != "config"}} for seed, (_, info) in selection.items()
])
sel_summary.to_csv(SEL_DIR / "resumen.csv", index=False)
display(sel_summary.round(3))

#%% celda 13 [texto]
## 2. Listas de variables sobrevivientes

En cada repetición sobrevive la variable real con número **menor** al punto de asesinato. En la lista final queda la que sobrevive en al menos 2 de las 3 repeticiones. Se muestra cuántas quedan por tipo (originales, lag1, lag2) y cuánto coinciden las repeticiones. Si una lista sale igual a otra, se descarta la repetida.

#%% celda 14 [código]
# [Anotación · líneas 750–777] survivors() devuelve las variables reales con número menor que el punto de
#   corte. Para cada punto cuenta en cuántas de las 3 repeticiones sobrevive cada variable y arma la lista con
#   las que tienen al menos 2 votos; calcula la coincidencia entre pares de repeticiones (intersección sobre
#   unión) y descarta una lista vacía o igual a otra. La lista sin_eliminar contiene todas las variables.
def survivors(table, cut):
    real = table[~table["canarito"]]
    alive = real.loc[real["id"].notna() & (real["id"] < cut), "variable"]
    return set(alive)


LISTS = {"sin_eliminar": list(range(N_REAL))}
list_rows, overlap_rows = [], []
for name in CUT_POINTS:
    per_rep = {seed: survivors(table, info[f"corte_{name}"]) for seed, (table, info) in selection.items()}
    votes = pd.Series(0, index=feature_names)
    for alive in per_rep.values():
        votes[list(alive)] += 1
    columns = [feature_index[v] for v in feature_names if votes[v] >= MIN_VOTES]
    sets = list(per_rep.values())
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            union = sets[i] | sets[j]
            overlap_rows.append({"punto": name, "par": f"{SEL_SEEDS[i]}-{SEL_SEEDS[j]}",
                                 "coincidencia": len(sets[i] & sets[j]) / len(union) if union else 1.0})
    duplicate = next((other for other, cols in LISTS.items() if cols == columns), None)
    if not columns:
        log(f"  {name}: no sobrevive ninguna variable, se descarta")
        continue
    if duplicate:
        log(f"  {name}: igual a {duplicate}, se descarta")
        continue
    LISTS[name] = columns

# [Anotación · líneas 779–791] Cuenta cuántas variables de cada lista son originales, de lag1 o de lag2,
#   guarda listas.json y listas.csv y deja en el log cuántas variables quedan y cuántas se eliminan en cada
#   lista.
for name, columns in LISTS.items():
    kinds = pd.Series(["lag2" if feature_names[j].endswith(("_lag2", "_delta_lag2")) else
                       "lag1" if feature_names[j].endswith(("_lag1", "_delta_lag1")) else "original" for j in columns])
    list_rows.append({"lista": name, "variables": len(columns), **kinds.value_counts().to_dict()})
lists_table = pd.DataFrame(list_rows).fillna(0)
display(lists_table)
display(pd.DataFrame(overlap_rows).round(3))
save_json(SEL_DIR / "listas.json", {name: [feature_names[j] for j in cols] for name, cols in LISTS.items()})
lists_table.to_csv(SEL_DIR / "listas.csv", index=False)
for name, columns in LISTS.items():
    if name != "sin_eliminar":
        killed = sorted(set(feature_names) - {feature_names[j] for j in columns})
        log(f"  {name}: {len(columns)} variables ({len(killed)} eliminadas). Algunas eliminadas: {killed[:8]}")

#%% celda 15 [texto]
## 3. Comparación de listas (zLightGBM, configuración de `s0006`, mismas semillas)

Cada lista con los fijos de `s0006` y sus mejores valores (1.155 / 126 / 0,094), canaritos 1 a 1, marzo a mayo → junio. Las semillas son las mismas en todas las listas (y fijan los canaritos), así que la única diferencia son las variables. Cada corrida se guarda apenas termina.

#%% celda 16 [código]
# [Anotación · líneas 799–805] list_hash() calcula una huella SHA-1 de una lista de variables y cmp_config()
#   describe la configuración de cada corrida de la comparación, para reusar lo ya guardado.
def list_hash(columns):
    return hashlib.sha1(",".join(feature_names[j] for j in columns).encode()).hexdigest()[:12]


def cmp_config(name, seed):
    return canonical({"lista": name, "hash": list_hash(LISTS[name]), "seed": seed, "valores": S0006_VALUES,
                      "meses": CMP_TRAIN_MONTHS, "valida": VALID_MONTH, "prueba": MODO_PRUEBA})


# [Anotación · líneas 808–838] Para cada una de las 5 semillas y cada lista entrena zLightGBM con 1.155
#   iteraciones, 126 hojas y min_sum_hessian_in_leaf 0,094 sobre 202103–202105, con un canarito por variable,
#   predice junio y guarda predicciones y métricas (AUC, ganancia máxima suavizada, posición, árboles). Escribe
#   corridas.csv.
cmp_scores, cmp_rows = {}, []
cmp_start, n_done = time.perf_counter(), 0
n_total = len(LISTS) * len(CMP_SEEDS)
for seed in CMP_SEEDS:  # semilla por semilla: si se corta, ya hay pares completos para comparar
    for name, columns in LISTS.items():
        base = CMP_DIR / f"{name}_seed{seed}"
        config = cmp_config(name, seed)
        if base.with_suffix(".npy").exists() and base.with_suffix(".json").exists() \
                and load_json(base.with_suffix(".json"))["config"] == config:
            scores, summary = np.load(base.with_suffix(".npy")), load_json(base.with_suffix(".json"))["resumen"]
        else:
            start = time.perf_counter()
            booster = train_zlgb(columns, S0006_VALUES, seed, CMP_ROWS)
            scores = predict_june(booster, columns, seed)
            summary = {"lista": name, "semilla": seed, "variables": len(columns), "arboles": int(booster.num_trees()),
                       **june_metrics(scores), "minutos": round((time.perf_counter() - start) / 60, 1)}
            del booster
            save_json(base.with_suffix(".json"), {"resumen": summary, "config": config})
            save_npy(base.with_suffix(".npy"), scores)
            n_done += 1
            per_run = (time.perf_counter() - cmp_start) / n_done
            left = n_total - len(cmp_rows) - 1
            log(f"  {name:15s} semilla {seed}: AUC {summary['auc']:.5f} | ganancia {summary['ganancia_maxima']:.1f} "
                f"con {summary['mejor_corte']} | {summary['arboles']} árboles | {summary['minutos']} min | "
                f"faltan {left} (~{left * per_run / 3600:.1f} h)")
        cmp_scores[(name, seed)] = scores
        cmp_rows.append(summary)

cmp_table = pd.DataFrame(cmp_rows)
cmp_table.to_csv(CMP_DIR / "corridas.csv", index=False)
log(f"Comparación: {n_total} corridas ({n_done} nuevas) en {(time.perf_counter() - cmp_start) / 60:.0f} min")

#%% celda 17 [texto]
## 4. Decisión

Para cada lista, diferencia con "sin eliminar" semilla por semilla (misma semilla = mismos canaritos y mismo azar): media, desvío y t pareado, en ganancia máxima suavizada y en AUC. También el ensamble de las semillas de cada lista.

**Regla (fijada antes de ver los resultados):** gana la lista con mayor mejora media de ganancia, siempre que sea positiva y con t ≥ 2. Si ninguna cumple, no hay envío: el notebook no sigue y apaga la máquina. `FORZAR_LISTA` permite seguir con una lista igual.

#%% celda 18 [código]
# [Anotación · líneas 848–870] Arma la tabla de decisión: por lista, media y desvío de la ganancia máxima
#   entre semillas, AUC medio y métricas del promedio de las 5 semillas. Para las listas distintas de
#   sin_eliminar calcula la diferencia de ganancia semilla por semilla, su media, su desvío, el t pareado (media
#   sobre desvío dividido raíz de n), en cuántas semillas la diferencia es positiva y la diferencia media de
#   AUC. Guarda decision.csv.
decision_rows = []
base_by_seed = cmp_table[cmp_table["lista"].eq("sin_eliminar")].set_index("semilla")
for name in LISTS:
    rows = cmp_table[cmp_table["lista"].eq(name)].set_index("semilla").loc[CMP_SEEDS]
    ensemble = np.column_stack([cmp_scores[(name, s)] for s in CMP_SEEDS]).mean(axis=1)
    ens = june_metrics(ensemble)
    row = {"lista": name, "variables": len(LISTS[name]),
           "ganancia_media": rows["ganancia_maxima"].mean(), "ganancia_desvio": rows["ganancia_maxima"].std(ddof=1),
           "auc_media": rows["auc"].mean(), "ensamble_ganancia": ens["ganancia_maxima"],
           "ensamble_corte": ens["mejor_corte"], f"ensamble_corte_{CORTE_REF}": ens[f"ganancia_corte_{CORTE_REF}"]}
    if name != "sin_eliminar":
        diff = rows["ganancia_maxima"] - base_by_seed.loc[CMP_SEEDS, "ganancia_maxima"]
        diff_auc = rows["auc"] - base_by_seed.loc[CMP_SEEDS, "auc"]
        sd = diff.std(ddof=1)
        row.update({
            "dif_ganancia_media": diff.mean(), "dif_ganancia_desvio": sd,
            "t_pareado": diff.mean() / (sd / np.sqrt(len(diff))) if sd > 0 else np.nan,
            "gana_en": f"{int((diff > 0).sum())} de {len(diff)}", "dif_auc_media": diff_auc.mean(),
        })
    decision_rows.append(row)
decision = pd.DataFrame(decision_rows)
decision.to_csv(CMP_DIR / "decision.csv", index=False)
display(decision.round(4))

# [Anotación · líneas 872–887] Aplica la regla: entre las listas con diferencia media positiva y t pareado ≥ 2
#   elige la de mayor diferencia media. Si FORZAR_LISTA tiene un nombre, sigue con esa lista. Guarda
#   ganadora.json; si ninguna lista cumple, las celdas siguientes no entrenan nada.
candidates = decision[(decision["lista"] != "sin_eliminar") & (decision["dif_ganancia_media"] > 0)
                      & (decision["t_pareado"] >= WIN_MIN_T)]
WINNER = None if candidates.empty else candidates.sort_values("dif_ganancia_media").iloc[-1]["lista"]
log("Regla: gana la mayor mejora de ganancia con t pareado >=", WIN_MIN_T, "->", WINNER or "ninguna lista gana")
if FORZAR_LISTA is not None:
    if FORZAR_LISTA not in LISTS:
        raise KeyError(f"FORZAR_LISTA = {FORZAR_LISTA!r} no es una lista: {list(LISTS)}")
    log(f"FORZAR_LISTA: se sigue con {FORZAR_LISTA}" + (" (modo prueba)" if MODO_PRUEBA else ""))
    WINNER = FORZAR_LISTA
save_json(CMP_DIR / "ganadora.json", {"ganadora": WINNER, "forzada": FORZAR_LISTA is not None,
                                      "regla_t": WIN_MIN_T, "tabla": decision.to_dict("records")})
if WINNER is None:
    log("Ninguna lista mejora a 'sin eliminar': no hay envío. Las celdas siguientes no hacen nada y la máquina se apaga.")
else:
    WINNER_COLUMNS = LISTS[WINNER]
    log(f"Lista elegida: {WINNER} ({len(WINNER_COLUMNS)} variables)")

#%% celda 19 [texto]
## 5. Optimización bayesiana de la lista elegida

Igual que `s0006`: Optuna (TPE), 21 corridas = 1 con los valores de `s0006` + 10 al azar + 10 guiadas, una sola semilla (101737), AUC de junio. Cambios: entrena con marzo a mayo, usa solo las variables de la lista (con sus canaritos 1 a 1) y el techo de `min_sum_hessian_in_leaf` es 1.

El estudio (SQLite) vive en el disco local porque SQLite no funciona bien sobre el bucket; después de cada corrida se copia al bucket, y al empezar se recupera de ahí si la máquina es nueva.

#%% celda 20 [código]
# [Anotación · líneas 897–922] Si hay lista elegida, arma la configuración de la búsqueda y abre o crea el
#   estudio de Optuna en SQLite (recuperándolo del bucket si hace falta), con dirección maximize y TPESampler
#   con 11 corridas iniciales y semilla 20261010 más la cantidad de corridas registradas. Encola como primera
#   corrida los valores 1.155, 126 y 0,094.
if WINNER is not None:
    BO_CONFIG = canonical({"lista": WINNER, "hash": list_hash(WINNER_COLUMNS), "search_space": SEARCH_SPACE,
                           "n_startup_trials": N_STARTUP_TRIALS, "meses": CMP_TRAIN_MONTHS, "valida": VALID_MONTH,
                           "seed": BO_SEED, "prueba": MODO_PRUEBA,
                           "fijos": {k: v for k, v in zlgb_params(S0006_VALUES, 0, BO_SEED).items()
                                     if k not in ("num_leaves", "min_sum_hessian_in_leaf", "canaritos", "num_threads")}})
    LOCAL_DB, BUCKET_DB = LOCAL_DIR / "estudio.db", BO_DIR / "estudio.db"
    if not LOCAL_DB.exists() and BUCKET_DB.exists():
        shutil.copy(BUCKET_DB, LOCAL_DB)
        log("Estudio recuperado del bucket")
    study = optuna.create_study(study_name=f"{EXP_ID}_bayesiana", storage=f"sqlite:///{LOCAL_DB.as_posix()}",
                                direction="maximize", load_if_exists=True)
    if not study.trials:
        study.set_user_attr("config", BO_CONFIG)
    elif study.user_attrs.get("config") != BO_CONFIG:
        raise RuntimeError(f"{LOCAL_DB} es de otra configuración. Movelo (y el del bucket) para empezar de cero.")
    study.sampler = optuna.samplers.TPESampler(n_startup_trials=N_STARTUP_TRIALS, seed=SAMPLER_SEED + len(study.trials))

    def completed_trials():
        return [t for t in study.trials if t.state == TrialState.COMPLETE]

    if not any(t.params == S0006_VALUES for t in completed_trials()) \
            and not any(t.state == TrialState.WAITING for t in study.trials):
        study.enqueue_trial(S0006_VALUES)

    bo_timing = []

# [Anotación · líneas 924–959] Función objetivo: entrena zLightGBM con las variables de la lista elegida sobre
#   202103–202105 con semilla 101737, predice junio, guarda las predicciones y devuelve el AUC de junio.
#   trials_table() arma la tabla de corridas y checkpoint() copia el estudio al bucket después de cada corrida.
    def objective(trial):
        values = {
            "num_iterations": trial.suggest_int("num_iterations", *SEARCH_SPACE["num_iterations"]),
            "num_leaves": trial.suggest_int("num_leaves", *SEARCH_SPACE["num_leaves"]),
            "min_sum_hessian_in_leaf": trial.suggest_float("min_sum_hessian_in_leaf", *SEARCH_SPACE["min_sum_hessian_in_leaf"]),
        }
        n_before = len(completed_trials())
        kind = "s0006" if values == S0006_VALUES else ("azar" if n_before < N_STARTUP_TRIALS else "guiada")
        start = time.perf_counter()
        booster = train_zlgb(WINNER_COLUMNS, values, BO_SEED, CMP_ROWS)
        scores = predict_june(booster, WINNER_COLUMNS, BO_SEED)
        num_trees = int(booster.num_trees())
        del booster
        metrics = june_metrics(scores)
        minutes = (time.perf_counter() - start) / 60
        save_npy(BO_DIR / f"junio_corrida_{trial.number:03d}.npy", scores)
        for key, value in {**metrics, "num_trees": num_trees, "minutos": round(minutes, 1), "tipo": kind}.items():
            trial.set_user_attr(key, value)
        bo_timing.append((values["num_iterations"], minutes * 60))
        per_iteration = sum(s for _, s in bo_timing) / sum(n for n, _ in bo_timing)
        left = N_TRIALS - n_before - 1
        log(f"  corrida {n_before + 1:2d}/{N_TRIALS} ({kind:6s}) iter {values['num_iterations']:4d} | hojas "
            f"{values['num_leaves']:4d} | hessian {values['min_sum_hessian_in_leaf']:.5f} -> AUC {metrics['auc']:.5f} | "
            f"ganancia {metrics['ganancia_maxima']:.1f} con {metrics['mejor_corte']} | {num_trees} árboles | "
            f"{minutes:.1f} min | faltan ~{left * per_iteration * sum(SEARCH_SPACE['num_iterations']) / 2 / 3600:.1f} h")
        return metrics["auc"]

    def trials_table():
        rows = [{"corrida": t.number, **t.params, **t.user_attrs} for t in completed_trials()]
        table = pd.DataFrame(rows)
        return table.sort_values("auc", ascending=False).reset_index(drop=True) if len(table) else table

    def checkpoint(study_, trial_):
        trials_table().to_csv(BO_DIR / "corridas.csv", index=False)
        shutil.copy(LOCAL_DB, BO_DIR / "estudio.db.tmp")
        os.replace(BO_DIR / "estudio.db.tmp", BUCKET_DB)

# [Anotación · líneas 961–976] Ejecuta las corridas que faltan hasta 21, toma la de mayor AUC de junio y
#   escribe sus valores y métricas en mejores_hiperparametros.json. Si no hay lista elegida, sólo deja un
#   mensaje en el log.
    remaining = N_TRIALS - len(completed_trials())
    log(f"Bayesiana: {len(completed_trials())} de {N_TRIALS} corridas hechas")
    if remaining > 0:
        study.optimize(objective, n_trials=remaining, callbacks=[checkpoint])
    bo_table = trials_table()
    bo_table.to_csv(BO_DIR / "corridas.csv", index=False)
    display(bo_table.round(5))
    best_trial = study.best_trial
    BEST_VALUES = {"num_iterations": int(best_trial.params["num_iterations"]),
                   "num_leaves": int(best_trial.params["num_leaves"]),
                   "min_sum_hessian_in_leaf": float(best_trial.params["min_sum_hessian_in_leaf"])}
    save_json(BO_DIR / "mejores_hiperparametros.json", {"corrida": best_trial.number, "valores": BEST_VALUES,
                                                       **best_trial.user_attrs})
    log("Mejores valores:", BEST_VALUES, f"| AUC junio {best_trial.value:.5f}")
else:
    log("Bayesiana: no corre (ninguna lista ganó)")

#%% celda 21 [texto]
## 6. Referencia de junio

La lista elegida con sus mejores valores, 3 semillas (marzo a mayo → junio), contra "sin eliminar" con los valores de `s0006` y las mismas 3 semillas (ya entrenadas en la comparación). Ganancia de junio de cada ensamble por corte. La corrida 101737 se reusa de la bayesiana si es la mejor.

#%% celda 22 [código]
# [Anotación · líneas 984–1017] Referencia de junio: la lista elegida con los valores de la búsqueda y 3
#   semillas (reusa la 101737 de la búsqueda), promediadas, frente al promedio de sin_eliminar con las mismas 3
#   semillas de la comparación. Guarda junio_ensamble.npy y ganancia_junio_por_corte.csv con la ganancia
#   suavizada de cada corte y la diferencia.
if WINNER is not None:
    june_scores = {}
    for seed in JUNE_SEEDS:
        if seed == BO_SEED:
            june_scores[seed] = np.load(BO_DIR / f"junio_corrida_{best_trial.number:03d}.npy")
            continue
        base = JUNE_DIR / f"junio_seed{seed}"
        config = canonical({"seed": seed, "valores": BEST_VALUES, "bayesiana": BO_CONFIG})
        if base.with_suffix(".npy").exists() and load_json(base.with_suffix(".json")) == config:
            june_scores[seed] = np.load(base.with_suffix(".npy"))
            continue
        start = time.perf_counter()
        booster = train_zlgb(WINNER_COLUMNS, BEST_VALUES, seed, CMP_ROWS)
        june_scores[seed] = predict_june(booster, WINNER_COLUMNS, seed)
        del booster
        save_json(base.with_suffix(".json"), config)
        save_npy(base.with_suffix(".npy"), june_scores[seed])
        log(f"  referencia semilla {seed}: {june_metrics(june_scores[seed])['ganancia_maxima']:.1f} | "
            f"{(time.perf_counter() - start) / 60:.1f} min")
    winner_ens = np.column_stack([june_scores[s] for s in JUNE_SEEDS]).mean(axis=1)
    base_ens = np.column_stack([cmp_scores[("sin_eliminar", s)] for s in JUNE_SEEDS]).mean(axis=1)
    save_npy(JUNE_DIR / "junio_ensamble.npy", winner_ens)
    june_by_cut = pd.DataFrame({"corte": CORTES})
    for label, scores in [(WINNER + "_optimizada", winner_ens), ("sin_eliminar_s0006", base_ens)]:
        _, smooth = gain_curve(june_baja2, scores)
        june_by_cut[label] = [float(smooth[c - 1]) for c in CORTES]
        m = june_metrics(scores)
        log(f"  ensamble de {len(JUNE_SEEDS)} {label}: AUC {m['auc']:.5f} | ganancia máxima {m['ganancia_maxima']:.1f} "
            f"con {m['mejor_corte']}")
    june_by_cut["diferencia"] = june_by_cut.iloc[:, 1] - june_by_cut.iloc[:, 2]
    june_by_cut.to_csv(JUNE_DIR / "ganancia_junio_por_corte.csv", index=False)
    display(june_by_cut.round(1))
else:
    log("Referencia de junio: no corre (ninguna lista ganó)")

#%% celda 23 [texto]
## 7. Semillas de agosto

La lista elegida con sus mejores valores, marzo a junio → agosto, `N_SEMILLAS_AGOSTO` semillas (primero las de `s0004`, después los primos de `s0005`). Cada semilla se guarda apenas termina; si la máquina se corta, al volver a correr sigue con las que faltan. Para cortar antes: *Interrupt* y después correr las celdas de cortes y apagado.

#%% celda 24 [código]
# [Anotación · líneas 1025–1049] Para cada una de las 20 semillas entrena con la lista elegida y los valores
#   de la búsqueda sobre 202103 a 202106, predice 202108 y guarda las probabilidades y la configuración. Las
#   semillas ya guardadas con la misma configuración se saltean; ante una interrupción manual conserva las
#   terminadas.
if WINNER is not None:
    save_npy(AUG_DIR / "ids_agosto.npy", future_ids)

    def aug_config(seed):
        return canonical({"seed": seed, "lista": WINNER, "hash": list_hash(WINNER_COLUMNS), "valores": BEST_VALUES,
                          "meses": TRAIN_MONTHS, "prueba": MODO_PRUEBA})

    done = [s for s in FINAL_SEEDS if (AUG_DIR / f"seed_{s}.npy").exists()
            and load_json(AUG_DIR / f"seed_{s}.json") == aug_config(s)]
    pending = [s for s in FINAL_SEEDS if s not in done]
    log(f"Agosto: {len(done)} semillas guardadas, faltan {len(pending)}")
    try:
        for seed in pending:
            start = time.perf_counter()
            booster = train_zlgb(WINNER_COLUMNS, BEST_VALUES, seed, ALL_ROWS)
            probabilities = booster.predict(with_canaries(R_pred, WINNER_COLUMNS, seed + 1))
            del booster
            save_json(AUG_DIR / f"seed_{seed}.json", aug_config(seed))
            save_npy(AUG_DIR / f"seed_{seed}.npy", probabilities)
            done.append(seed)
            log(f"  [{len(done)}/{len(FINAL_SEEDS)}] semilla {seed}: {(time.perf_counter() - start) / 60:.1f} min")
    except KeyboardInterrupt:
        log("Interrumpido: la semilla en curso se descarta; las terminadas quedaron guardadas.")
else:
    log("Agosto: no corre (ninguna lista ganó)")

#%% celda 25 [texto]
## 8. Promedio y cortes

Promedia las semillas de agosto guardadas y escribe un CSV por corte en `6_cortes/`, con la ganancia de junio de la referencia en el mismo corte. Se puede volver a correr sola después de la primera celda (lee todo del bucket).

#%% celda 26 [código]
# [Anotación · líneas 1057–1087] Promedia las semillas de agosto guardadas (verifica que compartan
#   configuración), ordena los clientes de mayor a menor probabilidad y escribe un CSV por corte con los
#   primeros números de cliente, con nombre c9920_<lista>_<semillas>sem_corte<corte>.csv. Escribe cortes.csv con
#   la ganancia de junio de cada corte y probabilidades_agosto.csv.gz.
saved = sorted(AUG_DIR.glob("seed_*.npy"), key=lambda p: p.stat().st_mtime)
if saved:
    ids = np.load(AUG_DIR / "ids_agosto.npy")
    configs = [load_json(p.with_suffix(".json")) for p in saved]
    if any({k: v for k, v in c.items() if k != "seed"} != {k: v for k, v in configs[0].items() if k != "seed"}
           for c in configs):
        raise RuntimeError("Las semillas guardadas no tienen la misma configuración")
    ensemble = np.column_stack([np.load(p) for p in saved]).mean(axis=1)
    lista = configs[0]["lista"]
    june_table = JUNE_DIR / "ganancia_junio_por_corte.csv"
    june_gain = pd.read_csv(june_table).set_index("corte").iloc[:, 0] if june_table.exists() else None
    for old in CUTS_DIR.glob("*.csv"):
        old.unlink()
    rows = []
    for cut in CORTES:
        if not MODO_PRUEBA and not 8_000 <= cut <= 15_000:
            raise ValueError(f"El bot acepta entre 8.000 y 15.000 registros: {cut}")
        chosen = ids[np.argsort(-ensemble, kind="stable")[:cut]]
        assert len(np.unique(chosen)) == cut
        path = CUTS_DIR / f"{EXP_ID}_{lista}_{len(saved)}sem_corte{cut}.csv"
        np.savetxt(path, chosen.astype(np.int64), fmt="%d")
        rows.append({"corte": cut, "archivo": path.name,
                     "ganancia_junio": None if june_gain is None or cut not in june_gain.index else round(june_gain[cut], 1)})
    cuts_table = pd.DataFrame(rows)
    cuts_table.to_csv(OUT_DIR / "cortes.csv", index=False)
    pd.DataFrame({"numero_de_cliente": ids, "score": ensemble}).to_csv(AUG_DIR / "probabilidades_agosto.csv.gz",
                                                                       index=False, compression="gzip")
    display(cuts_table)
    log(f"Cortes: {len(CORTES)} CSV con {len(saved)} semillas de {lista} en {CUTS_DIR}")
else:
    log("Cortes: no hay semillas de agosto guardadas")

#%% celda 27 [texto]
## 9. Fin y apagado

Si `APAGAR_AL_TERMINAR = True` y estás en una máquina virtual de la cátedra, la borra (como hacen sus scripts con las máquinas creadas desde las plantillas). Todo quedó en el bucket, en la carpeta que muestra la primera celda.

#%% celda 28 [código]
# [Anotación · líneas 1095–1097] Escribe en el log el fin de la corrida y, si la bandera está activa, borra la
#   máquina virtual.
log(f"{EXP_ID} terminado (modo prueba: {MODO_PRUEBA}). Resultados en {OUT_DIR}")
if APAGAR_AL_TERMINAR:
    apagar_vm("fin del notebook")
```


## Explicaciones del alumno (texto original)

### README.md

> # DMEyF 2026: primera competencia - Mario Freites
>
> Este repo tiene el código y los resultados para reproducir el envío final de la primera competencia: la predicción de BAJA+2 para 202108.
>
> **Envío final:** `c9923_60sem_corte11000.csv`. Tiene los 11.000 clientes de mayor probabilidad promediada sobre 60 semillas. Obtuvo **106,205 en el leaderboard público**.
>
> ## El modelo
>
> Son dos experimentos encadenados:
>
> 1. **c9920, canaritos asesinos.** Parte de 760 variables: las originales y sus lag1, delta_lag1, lag2 y delta_lag2, con ranking con cero fijo por mes. Elimina las que no le ganan a los canaritos, con el corte en media + 2 desvíos. Quedan 128 variables. También hace una optimización bayesiana sobre esa lista.
> 2. **c9923, variables nuevas.** Toma esas 128 variables y les suma 11 atributos nuevos, con sus lags y deltas, más promedios y pendientes de 3 meses: 299 variables en total. Hace una bayesiana propia de 25 corridas que maximiza el AUC de junio. Después entrena de marzo a junio con los mejores valores (3304 iteraciones, 1125 hojas, `min_sum_hessian_in_leaf` 0,595) y predice agosto con **60 semillas**.
>
> Los dos usan zLightGBM con canaritos 1 a 1, learning_rate 0,005, feature_fraction 0,5 y max_bin 31. El detalle de cada uno está en su `design.md`.
>
> ## Validación
>
> Junio es el mes de validación. c9920 elige la lista de variables con mayo y compara las listas en junio. Las dos bayesianas entrenan con marzo a mayo y miden el AUC sobre junio, con BAJA+1 y BAJA+2 como positivos. El modelo final entrena con marzo a junio y predice agosto. Julio no se usa para entrenar porque todavía no tiene la clase completa.
>
> ## Por qué el corte 11.000
>
> c9923 genera un CSV por corte, de 9.000 a 15.000 de a 500. Se mandaron cuatro al bot:
>
> | Corte | Ganancia en junio | Público |
> |---|---|---|
> | 10.500 | 394,7 | 105,408 |
> | **11.000** | **400,9** | **106,205** |
> | 11.500 | 399,7 | 103,620 |
> | 12.000 | 398,6 | 103,400 |
>
> En junio, la ganancia forma una meseta entre 11.000 y 13.500 (de 398 a 404). 11.000 es el comienzo de esa meseta y el mejor de los cuatro en el público. La ganancia de junio de todos los cortes está en `resultados/c9923/ganancia_junio_por_corte.csv`.
>
> ## Estructura
>
> ```
> 01_c9920_canaritos_asesinos/   notebook y diseño de c9920
> 02_c9923_variables_nuevas/     notebook y diseño de c9923
> resultados/c9920/              listas de variables, mejores hiperparámetros y log de la corrida
> resultados/c9923/              envío final, bayesiana, ganancia de junio por corte y log de la corrida
> ```
>
> ## Cómo reproducirlo
>
> Los notebooks están pensados para las máquinas virtuales de Google Cloud de la cátedra, con el bucket montado en `~/buckets/b1`. Cada notebook descarga el dataset y compila zLightGBM solo. Los resultados quedan en `~/buckets/b1/exp/<experimento>/`, y al terminar el notebook borra la máquina.
>
> **Máquina:** c9920 corrió con 8 hilos, y c9923 en una máquina de 96 GB de RAM y 12 vCPU. Entre los dos son unas 9,5 horas. Con menos hilos funciona igual, pero tarda más.
>
> ```bash
> git clone https://github.com/mariofreites/dmeyf-primera-competencia.git ~/dmeyf-primera-competencia
>
> # 1) c9920 (unas 3 horas con 8 hilos)
> cd ~/dmeyf-primera-competencia/01_c9920_canaritos_asesinos
> nohup jupyter nbconvert --to notebook --execute c9920_CanaritosAsesinos.ipynb \
>   --output c9920_corrida.ipynb --ExecutePreprocessor.timeout=-1 > c9920_run.txt 2>&1 &
>
> # 2) c9923 en otra máquina, cuando termine c9920 (unas 6,5 horas con 12 hilos)
> cd ~/dmeyf-primera-competencia/02_c9923_variables_nuevas
> nohup jupyter nbconvert --to notebook --execute c9923_VariablesNuevas.ipynb \
>   --output c9923_corrida.ipynb --ExecutePreprocessor.timeout=-1 > c9923_run.txt 2>&1 &
> ```
>
> c9923 lee de `exp/c9920/` la lista `media_2desvios` y los mejores hiperparámetros de c9920, que usa como primera corrida de su bayesiana. El envío queda en `~/buckets/b1/exp/c9923/5_cortes/c9923_60sem_corte11000.csv`.
>
> **Atajo:** se puede evitar correr c9920, ya que c9923 puede leer los archivos guardados en `resultados/c9920`:
>
> ```bash
> DMEYF_C9920_DIR=~/dmeyf-primera-competencia/resultados/c9920 nohup jupyter nbconvert ...   # el mismo comando de c9923
> ```
>
> En ese caso se saltea la comparación de junio contra c9920, que no influye en el envío.
>
> **Prueba corta:** con `MODO_PRUEBA=1` delante del comando, el notebook corre con el 5 % de los clientes en unos 15 minutos. Escribe en una subcarpeta `prueba/` y no apaga la máquina.
>
> **Para seguir la corrida:** `tail -f ~/buckets/b1/exp/c9923/log.txt`. Si Google borra la máquina spot, alcanza con volver a lanzar el mismo comando en otra: el notebook retoma desde lo que ya estaba guardado en el bucket.
>
> ## Notas
>
> - **Nombres.** Estos experimentos corrieron como z9920 y z9923 en el repo de trabajo original. Acá se les cambió la letra a `c` para no confundirlos con los experimentos de la cátedra. El cambio no toca ningún cálculo. Los logs y los CSV de `resultados/` son los archivos originales de las corridas, así que todavía dicen z9920 y z9923. Las referencias a s0004, s0005, s0006 y z9918 son experimentos anteriores de ese repo de trabajo, y z495 es un notebook de la cátedra. Los valores que hacen falta de esos experimentos ya están fijos en el código.
> - **Reproducibilidad.** Las semillas están fijas, pero LightGBM con varios hilos puede dar diferencias mínimas entre máquinas, y eso puede mover algo la bayesiana. Para comparar, en `resultados/` están las corridas originales. Se usó Optuna 5.0.0.

### 02_c9923_variables_nuevas/design.md

> # c9923: c9920 + variables nuevas, con bayesiana propia (diseño)
>
> Notebook: `c9923_VariablesNuevas.ipynb`. Pensado para correr de noche en una máquina virtual de Google Cloud de la cátedra, con los resultados en el bucket (`~/buckets/b1/exp/c9923/`).
>
> ## Qué es
>
> El modelo de `c9920` (envío `c9920c11000`, 104,75 en el público) con variables nuevas y una optimización bayesiana propia, porque al cambiar las variables el óptimo de hiperparámetros puede moverse. Termina en semillas de agosto listas para el bot y para ensamblar.
>
> ## Variables
>
> Todas se calculan con los valores crudos de cada mes y después pasan por el ranking con cero fijo por variable y por mes, como en `c9920`. "Mes anterior" es la observación anterior del cliente, igual que en los lags.
>
> 1. **Base:** las 128 de `c9920` (`media_2desvios`), leídas de `exp/c9920/1_seleccion/listas.json`, sin volver a seleccionar.
> 2. **11 atributos nuevos**, cada uno con lag1, delta_lag1, lag2 y delta_lag2 (55 columnas). Sumas: NA cuenta como 0 (NA si todos son NA). Ratios: NA si el denominador es 0 o NA.
>
> | Variable | Cálculo |
> |---|---|
> | `mfondos_pesos_total` | mcaja_ahorro + mcuenta_corriente + mplazo_fijo_pesos |
> | `ctc_transacciones_total` | ctarjeta_visa_transacciones + ctarjeta_master_transacciones |
> | `mtc_saldo_total` | Visa_msaldototal + Master_msaldototal |
> | `mmargen_activo_pasivo` | mactivos_margen − mpasivos_margen |
> | `mtc_pagominimo_total` | Visa_mpagominimo + Master_mpagominimo |
> | `rtc_saldo_limite` | mtc_saldo_total / (Visa_mlimitecompra + Master_mlimitecompra) |
> | `rdigital_trx` | (chomebanking_transacciones + cmobile_app_trx) / (las dos + ccallcenter_transacciones + ccajas_transacciones + catm_trx + catm_trx_other) |
> | `cproductos_perdidos` | productos activos el mes anterior e inactivos en este; NA sin mes anterior |
> | `tperdio_payroll` | 1 si cpayroll_trx anterior > 0 y actual = 0; 0 si los dos existen y no pasa; NA sin mes anterior |
> | `tinicio_comision` | 1 si mcomisiones_mantenimiento actual > 0 y anterior ≤ 0; 0 si los dos existen y no pasa; NA sin mes anterior |
> | `mpatrimonio_neto` | (mcuentas_saldo + mplazo_fijo_pesos + mplazo_fijo_dolares + minversion1_pesos + minversion1_dolares + minversion2) − (mprestamos_personales + mprestamos_prendarios + mprestamos_hipotecarios + Visa_msaldototal + Master_msaldototal) |
>
> Productos de `cproductos_perdidos` (activo si alguna fuente > 0, inactivo si todas son 0, NA si ninguna es > 0 y alguna es NA): tarjetas (ctarjeta_visa, ctarjeta_master), sueldo (cpayroll_trx, cpayroll2_trx), débitos automáticos (ccuenta_debitos_automaticos, ctarjeta_visa_debitos_automaticos, ctarjeta_master_debitos_automaticos), pagos (cpagodeservicios, cpagomiscuentas), préstamos (cprestamos_personales, cprestamos_prendarios, cprestamos_hipotecarios), inversiones (cplazo_fijo, cinversion1, cinversion2), seguros (cseguro_vida, cseguro_auto, cseguro_vivienda, cseguro_accidentes_personales) y caja de seguridad (ccaja_seguridad).
>
> 3. **`_avg3` y `_slope3`** para cada campo base que aparece en las 128 (como original, lag o delta) y para los 11 nuevos: promedio y pendiente de mínimos cuadrados (contra el mes) de los valores disponibles en la observación actual y las dos anteriores, con mínimo 2 valores.
>
> Total: 128 + 55 + 2 × (N + 11) columnas, con N = campos base de la lista (el notebook lo imprime), y el mismo número de canaritos.
>
> ## Pasos
>
> 1. **Bayesiana:** Optuna TPE multivariado, 25 corridas (1 con los valores de `c9920`, 3.981 / 675 / 0,468, + 10 al azar + 14 guiadas) sobre `num_iterations` (64–4.096), `num_leaves` (16–2.048) y `min_sum_hessian_in_leaf` (1e-6–1). Entrena marzo a mayo, predice junio, semilla 101737, **maximiza el AUC de junio** (BAJA+1 y BAJA+2 positivos), con `metric = "auc"` en LightGBM. Se guardan también la *average precision* (solo BAJA+2) y la ganancia suavizada, como información. Los fijos son los de `c9920` (learning_rate 0,005, feature_fraction 0,5, bynode 0,2, min_data_in_leaf 0, max_bin 31) y canaritos 1 a 1.
> 2. **Referencia de junio:** los mejores valores con las semillas 101737, 303011 y 602909, comparada con la referencia de junio de `c9920` (mismas semillas) si está en el bucket.
> 3. **Agosto:** marzo a junio → agosto con los mejores valores de la bayesiana (sin volver a los de `c9920`), hasta 60 semillas: las 10 de `s0004` y después la lista de primos de `s0005`/`s0006`/`c9920`. Después de cada semilla se rehacen los CSV de cortes (9.000 a 15.000 de a 500) y las probabilidades del ensamble.
> 4. **Apagado:** al terminar, al encontrar `PARAR` o si una celda falla (en la corrida real), borra la máquina. Todo queda en el bucket.
>
> ## Cómo se corta
>
> - `touch ~/buckets/b1/exp/c9923/PARAR`, solo cuando ya empezó agosto: antes de cada semilla el notebook lo busca; si está, no empieza otra, deja los cortes al día y apaga. Se borra solo al arrancar una corrida nueva.
> - `touch ~/buckets/b1/exp/c9923/CORTAR_BAYESIANA`: termina la corrida de la bayesiana en curso y sigue con junio y agosto con lo mejor que haya. No se borra solo (al retomar no vuelve a la bayesiana); para empezar de cero hay que borrarlo.
> - Un error pasajero del bucket al rehacer los cortes o al copiar el estudio queda en el log como aviso y no frena la corrida.
> - Si Google borra la máquina spot: otra máquina, el mismo comando. El estudio de Optuna, cada referencia de junio y cada semilla de agosto se guardan en el bucket al terminar; saltea lo hecho.
> - Cada predicción guardada lleva una huella del orden de los clientes (marzo a junio en la bayesiana y junio; agosto en cada semilla). Al retomar, una semilla de agosto guardada con otro orden se rehace, y un estudio guardado con otro orden de marzo a junio frena la corrida con un error, en vez de mezclar clientes.
>
> ## Pruebas antes de entregarlo
>
> Fuera de Google Cloud, en un entorno aparte con el dataset completo y una lista de 128 variables armada al azar en lugar de la de `c9920` (que en ese momento estaba solo en el bucket):
>
> - Modo prueba de punta a punta (5 % de los clientes), retomando después de matar el proceso en medio de la bayesiana y en medio de agosto (también sin el disco local, como en una máquina nueva), y con `PARAR` y `CORTAR_BAYESIANA`.
> - Con los datos completos y la configuración real: datos, atributos nuevos, controles y ranking, más una medición de tiempos de entrenamiento.

### 01_c9920_canaritos_asesinos/design.md

> # c9920: canaritos asesinos (diseño)
>
> Notebook: `c9920_CanaritosAsesinos.ipynb`. Pensado para correr en una máquina virtual de Google Cloud (plantillas spot de la cátedra), con los resultados en el bucket.
>
> ## Pregunta
>
> ¿Eliminar las variables que no le ganan a los canaritos mejora el modelo de `s0006`?
>
> ## Receta del profesor
>
> Agregar un 20 % de canaritos, entrenar un LightGBM razonable, numerar las variables por importancia (1 = la más importante), calcular media y desvío de los números de los canaritos y eliminar toda variable con número mayor que media + desvío o media + 2 desvíos. No se corta en el primer canarito (demasiado agresivo).
>
> ## Diseño
>
> 1. **Datos:** igual que `s0006` (760 variables reales: originales, lag1, delta_lag1, lag2, delta_lag2, con ranking con cero fijo; préstamos personales incluidos).
> 2. **Selección:** LightGBM común con los parámetros de z495 (2.848 árboles, 71 hojas, `min_sum_hessian_in_leaf` 0,0067, learning_rate 0,005, `feature_fraction` 0,5, `min_data_in_leaf` 0, `max_bin` 31). 760 variables + 152 canaritos. Entrena con **mayo**: todas las BAJA + 10 % de CONTINUA. Importancia por gain; las variables no usadas no reciben número y mueren. 3 repeticiones con semillas distintas (canaritos y undersampling).
>    - Mayo y no marzo + abril: lag2 está vacío en marzo y abril, y las 304 variables de lag2 morirían sin ser evaluadas. Junio queda libre para juzgar.
> 3. **Listas:** media + 1 desvío y media + 2 desvíos (los dos puntos del profesor). Una variable sobrevive si sobrevive en al menos 2 de 3 repeticiones. Más "sin eliminar".
> 4. **Comparación:** zLightGBM con los fijos y los mejores valores de `s0006` (1.155 / 126 / 0,094), canaritos 1 a 1, marzo a mayo → junio, 5 semillas por lista, las mismas en todas las listas.
> 5. **Regla (fijada antes de ver resultados):** gana la lista con mayor mejora media de ganancia de junio (máxima suavizada) frente a "sin eliminar", si es positiva y con t pareado ≥ 2. Si ninguna gana, no hay envío.
> 6. **Bayesiana de la ganadora:** como `s0006` (21 corridas, TPE, AUC de junio, semilla 101737), marzo a mayo → junio, techo de `min_sum_hessian_in_leaf` en 1.
> 7. **Referencia de junio:** ganadora optimizada contra "sin eliminar" con los valores de `s0006`, mismas 3 semillas.
> 8. **Agosto:** ganadora, marzo a junio → agosto, 20 semillas, un CSV por corte (9.000 a 15.000).
>
> ## Por qué así
>
> - Lista y semillas separadas de la bayesiana: en `s0006` el AUC casi no cambió con los hiperparámetros (0,909 a 0,913). Si la lista fuera un hiperparámetro más, una lista podría ganar por suerte. Con los mismos valores y las mismas semillas, la única diferencia entre listas son las variables.
> - Solo los dos puntos del profesor: menos comparaciones, menos ganadores por azar (lo de `ccomisiones_otras` en z9918), y z9918 no encontró columnas que dañen claramente.
>
> ## Google Cloud
>
> - Resultados en `~/buckets/b1/exp/c9920/` (sobreviven si Google borra la máquina spot); el estudio de Optuna en disco local, copiado al bucket después de cada corrida.
> - Retoma: cada selección, corrida, prueba de la bayesiana y semilla se guarda al terminar; *Run All* en una máquina nueva saltea lo hecho.
> - Al terminar (o si una celda falla, en la corrida real) borra la máquina con `~/machina/direct/apagar_vm.sh` de la cátedra.
> - `MODO_PRUEBA=1` (o `MODO_PRUEBA = True` a mano): 5 % de los clientes y pocos árboles, en otra carpeta, sin apagar. Probado de punta a punta fuera de Google Cloud, incluida la recuperación del estudio desde el bucket.

