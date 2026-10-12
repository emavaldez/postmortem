# nicobaranek — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: nicobaranek
- Repositorio: https://github.com/nicobaranek/dmeyf-competencia-01
- Link posteado: https://github.com/nicobaranek/dmeyf-competencia-01
- Commit: 88ed240e913aa4eb765ad435eb4abfa740cacfe6
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/nicobaranek/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/nicobaranek.json

## Resumen

Repositorio en R (con una celda de carga en Python) formado por una notebook de entrega, una notebook de la optimización bayesiana de origen, scripts en codigo/ que reproducen la misma ruta sin Jupyter, nueve scripts de experimentos apagados por interruptores, fuentes de corridas anteriores en procedencia/, resultados de experimentos en evidencia/ e historiales de búsquedas en procedencia_bo/. El camino de la entrega verifica el MD5 del dataset, reconstruye la clase ternaria desde la presencia mensual de cada cliente, pasa ccajas_depositos de 202105 a NA y calcula lags y deltas de orden 1 y 2 de todas las variables. Entrena LightGBM con clase binaria (BAJA+1 o BAJA+2 = 1) sobre 202103-202106, con todas las filas y 752 predictores: incluye numero_de_cliente, foto_mes y préstamos personales, y excluye la familia de fechas de último cierre de Visa y Master. Usa 1907 iteraciones, 77 hojas y min_sum_hessian_in_leaf 2,837, leídos del resultado guardado de una optimización bayesiana (mlrMBO, 12 evaluaciones, entrenamiento 202103-202104 y ganancia de 202106 en el corte 11.500). Entrena 10 semillas, promedia las probabilidades de 202108 y escribe los 10.375 clientes de mayor probabilidad. Al final compara el SHA256 del archivo con un valor esperado y se detiene si no coincide.

**Qué entrega.** Un archivo SINCIERRES_PROB10_K10375.csv con 10.375 numero_de_cliente, uno por línea y sin encabezado: los clientes de 202108 con mayor probabilidad promedio de 10 modelos LightGBM. El repositorio incluye una copia en referencia/ y el SHA256 esperado (7715cbb9…5caa).

**Cómo se ejecuta.** Según el README: ubicar el crudo en datos/competencia_01_crudo.csv o definir DMEYF_DATOS; abrir DMEyF_Nicky_Entrega_Final.ipynb, ejecutar la sección 1 con kernel Python y la sección 2 con kernel R en orden, con reproducir_final=TRUE y el resto de los interruptores en FALSE. Alternativa sin Jupyter, desde la carpeta de la entrega: DMEYF_DATOS=/ruta/competencia_01_crudo.csv Rscript --vanilla REPRODUCIR_FINAL.R. DMEYF_SALIDA y DMEYF_ENTREGA cambian las carpetas de salida y de código. El archivo queda en salida/final/. Para repetir la búsqueda de hiperparámetros el README indica ejecutar BO_Origen.ipynb en una salida vacía.

## Ficha

- **Lenguajes:** R, Python
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: 1 = BAJA+1 o BAJA+2, 0 = CONTINUA. La clase ternaria se reconstruye desde la presencia mensual de cada cliente y se contrasta con la columna clase_ternaria del crudo si existe.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se aplica: el modelo final entrena con las 654.066 filas de 202103-202106 (bagging_fraction 1, sin filtrar CONTINUA).
- **Calidad de datos:** ccajas_depositos de 202105 se pasa a NA; los valores numéricos no finitos se pasan a NA; las columnas no numéricas se convierten a códigos enteros. Se exige que no haya pares cliente-mes duplicados y que el MD5 del crudo sea b6f759764c5d04cbf068548517ae1249.
- **Drifting:** No se observa en el código del camino de la entrega: no hay ranking, deflación ni estandarización. La función rank_cero (rango por mes con cero fijo) se usa sólo en variantes con interruptor en FALSE.
- **Variables dentro del mes:** No se observa en el código del camino de la entrega. Los scripts experimentos/vinculacion.R, tarjetas.R y rank_zero_tend3.R crean indicadores dentro del mes en variantes apagadas.
- **Variables históricas:** Lag 1 y lag 2 de todas las variables por mes calendario exacto (NA si el cliente no tiene registro de ese mes) y delta 1 y delta 2 (valor actual menos lag) de las numéricas.
- **Selección de variables:** Sin selección por importancia. Se excluye a mano la familia Visa_fultimo_cierre y Master_fultimo_cierre (10 columnas: nivel, lags y deltas). Los préstamos personales (10 columnas) se excluyen en la optimización de hiperparámetros y se incluyen en el modelo final. numero_de_cliente y foto_mes se usan como predictores. Total: 752 predictores.
- **Optimización de hiperparámetros:** Optimización bayesiana con mlrMBO (kriging con covarianza Matérn 3/2, criterio de mejora esperada): 4 puntos iniciales y 8 iteraciones sobre num_iterations (512-4096), num_leaves (8-256) y log10 de min_sum_hessian_in_leaf (-3 a 1). Entrena 202103-202104 con la semilla 100613 y maximiza la ganancia de 202106 en el corte 11.500. La ruta final no la reejecuta: lee el resultado guardado en procedencia_bo/.
- **Hiperparámetros finales:** num_iterations 1907, num_leaves 77, min_sum_hessian_in_leaf 2,83699883991516; learning_rate 0,005, feature_fraction 0,50, feature_fraction_bynode 0,20, max_bin 31, min_data_in_leaf 0, max_depth -1, lambda_l1 0, lambda_l2 0, sin bagging, objetivo binary, métrica average_precision; lgb.train se llama sin conjunto de validación ni parada temprana.
- **Semillas:** 100613, 100267, 101611, 102481, 103651, 104729, 105019, 105613, 106013 y 106619, escritas en PARAM$semillas; una por modelo.
- **Cantidad de semillas:** 10
- **Ensamble:** Promedio con pesos iguales de las probabilidades de los 10 modelos (mismos datos e hiperparámetros, distinta semilla), cliente por cliente.
- **Corte:** Cantidad fija escrita en el código (CORTE_FINAL): los 10.375 clientes de mayor probabilidad promedio, con desempate por ID creciente. Según REGISTRO_EXPERIMENTOS.csv el valor se eligió 'combinando meseta, dispersión y público'; codigo/cortes.R tabula la ganancia de junio en siete cortes entre 10.000 y 11.500 y evidencia/CIERRE_CORTES_SINCIERRES_V1 guarda tablas de ese tipo.
- **Validación:** Entrenamiento en 202103-202104 y medición en 202106 con la ganancia de la competencia (1.072.500 por BAJA+2, -27.500 por el resto) en un corte fijo de 11.500; esa ganancia es el objetivo de la optimización bayesiana. El modelo final se reentrena con 202103-202106 y no tiene medición propia. El README indica que junio se reutilizó para desarrollar y seleccionar.
- **Salidas:** salida/final/SINCIERRES_PROB10_K10375.csv (10.375 IDs, una columna sin encabezado), PROBABILIDADES_AGOSTO.csv (probabilidad promedio de los 164.647 clientes), MODELO_<semilla>.txt y SCORES_<semilla>.rds por semilla, ENSAMBLE_FINAL.rds y VERIFICACION_FINAL.txt, además de archivos de auditoría, log y bloques de variables bajo salida/.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optimización bayesiana (mlrMBO, mlr3mbo, bbotk, skopt u otra) (`hiperparametros.optimizacion_bayesiana`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Técnicas sólo exploradas

- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Clase artificial o pseudo-etiquetas para meses sin clase (`clase.clase_artificial`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Genera archivos con varios cortes (`corte.varios_cortes`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README: Linux x86_64, R 4.6.1, LightGBM 4.7.0.99 y data.table 1.18.6.1 (el código detiene la ejecución con otras versiones), paquetes data.table, lightgbm, digest, jsonlite y filelock, y para las búsquedas mlrMBO 1.1.6, DiceKriging 1.6.1, mlr, ParamHelpers y smoof; seis hilos en LightGBM; Python para la carga. El dataset y la salida se ubican por rutas relativas o variables de entorno; las rutas de máquina escritas en el código principal son /home/ds/.local/lib/R/site-library (se agrega sólo si existe), ~/.cache/dmeyf_locks para bloqueos, /proc/meminfo y la URL de descarga del dataset.

## Pasos del camino de la entrega

1. **Ubicación y verificación del dataset crudo.** La celda Python de la notebook toma la ruta de DMEYF_DATOS o datos/competencia_01_crudo.csv, descarga el archivo si no existe, comprueba que su MD5 sea b6f759764c5d04cbf068548517ae1249 y deja la ruta en RUTA_DATOS.txt. La configuración en R repite la comprobación del MD5 antes de continuar. (`DMEyF_Nicky_Entrega_Final.ipynb` líneas 11–27; `codigo/configuracion.R` líneas 26–34)
2. **Parámetros, interruptores y control de versiones.** Se fijan las 10 semillas, 6 hilos, los meses de entrenamiento histórico (202103-202104) y final (202103-202106), el mes de validación (202106), el de predicción (202108), lags de orden 2, el corte de 10.375 y el SHA256 esperado. Sólo reproducir_final queda en TRUE. La ejecución se detiene si las versiones no son R 4.6.1, lightgbm 4.7.0.99 y data.table 1.18.6.1. (`codigo/configuracion.R` líneas 1–44; `DMEyF_Nicky_Entrega_Final.ipynb` líneas 35–80)
3. **Reconstrucción de la clase ternaria.** cargar_base() lee el crudo, exige los meses 202103 a 202108 sin duplicados cliente-mes y reconstruye CONTINUA, BAJA+1 y BAJA+2 a partir de la presencia de cada cliente en los dos meses siguientes. Si el crudo trae clase_ternaria compara ambas, se detiene ante cualquier discrepancia y completa con la reconstruida las filas sin clase. (`codigo/motor.R` líneas 47–70; `DMEyF_Nicky_Entrega_Final.ipynb` líneas 134–157)
4. **Corrección de datos.** ccajas_depositos de 202105 se pasa a NA; las columnas no numéricas se convierten a códigos enteros y los valores numéricos no finitos a NA. El resultado se guarda en caché con su firma. (`codigo/motor.R` líneas 71–84; `DMEyF_Nicky_Entrega_Final.ipynb` líneas 158–171)
5. **Lags y deltas de orden 1 y 2.** preparar_features() calcula, para cada variable y para los meses 202103 a 202108, el valor del mismo cliente 1 y 2 meses calendario antes (NA si no hay registro de ese mes) y, para las numéricas, la diferencia con el valor actual. Guarda un bloque .rds por mes y arma la lista ordenada de predictores, que incluye numero_de_cliente y foto_mes. La ruta final exige que el identificador de esta representación sea c9527308…. (`codigo/motor.R` líneas 85–120; `codigo/preparacion.R` líneas 1–6)
6. **Optimización bayesiana de origen.** bayes() busca num_iterations (512-4096), num_leaves (8-256) y log10 de min_sum_hessian_in_leaf (-3 a 1) con mlrMBO: 4 puntos iniciales y 8 iteraciones con criterio de mejora esperada. Cada evaluación entrena con 202103-202104 (sin préstamos personales, semilla 100613), predice 202106 y mide la ganancia en el corte 11.500. BO_Origen.ipynb activa esta búsqueda; la ruta final no la reejecuta. Según procedencia_bo/52fc1b5d…/HISTORIAL.csv hay 12 evaluaciones y la de mayor ganancia (471,35) corresponde a 1907 iteraciones, 77 hojas y Hessian mínimo 2,837. (`codigo/motor.R` líneas 155–213; `BO_Origen.ipynb` líneas 80–103)
7. **Lectura de los hiperparámetros guardados.** La ruta final lee procedencia_bo/52fc1b5d…/TERMINADO.rds, toma la primera configuración y comprueba que sea num_iterations 1907, num_leaves 77 y min_sum_hessian_in_leaf 2,83699883991516. Define la receta ORIGINAL_LAG2 sobre la representación con lags. (`codigo/preparacion.R` líneas 7–15; `DMEyF_Nicky_Entrega_Final.ipynb` líneas 438–446)
8. **Armado de los predictores del modelo final.** Se leen los bloques de 202103-202106 (654.066 filas) y de 202108 (164.647 clientes). A los 752 campos de la receta sin préstamos se agregan las 10 columnas de préstamos personales y se quitan las 10 de Visa_fultimo_cierre y Master_fultimo_cierre con sus lags y deltas; la lista de 752 predictores resultante se compara con referencia/FEATURES.csv. (`codigo/final.R` líneas 1–13; `DMEyF_Nicky_Entrega_Final.ipynb` líneas 461–473)
9. **Entrenamiento de 10 modelos LightGBM.** La etiqueta es 1 para BAJA+1 y BAJA+2 y 0 para CONTINUA, con todas las filas. Se construye un único lgb.Dataset (max_bin 31) y, para cada una de las 10 semillas, se entrena con 1907 iteraciones, 77 hojas, min_sum_hessian_in_leaf 2,837, learning_rate 0,005, feature_fraction 0,50 y feature_fraction_bynode 0,20. Cada modelo predice 202108 y se guardan modelo y probabilidades. (`codigo/final.R` líneas 14–45; `codigo/motor.R` líneas 31–35; `DMEyF_Nicky_Entrega_Final.ipynb` líneas 474–505)
10. **Promedio, corte y archivo de salida.** Se promedian las 10 probabilidades por cliente, se ordena de mayor a menor con desempate por ID creciente y se escriben los primeros 10.375 numero_de_cliente en salida/final/SINCIERRES_PROB10_K10375.csv, uno por línea y sin encabezado. También se guardan las probabilidades promedio de todos los clientes. (`codigo/final.R` líneas 46–56; `DMEyF_Nicky_Entrega_Final.ipynb` líneas 506–516)
11. **Verificación del archivo por SHA256.** Se calcula el SHA256 del CSV y se compara con 7715cbb9…5caa; si difiere, la ejecución se detiene con un mensaje, y si coincide se escribe VERIFICACION_FINAL.txt. El archivo VERIFICACION_FINAL.txt incluido en el repositorio registra una ejecución con ese hash. (`codigo/final.R` líneas 57–64; `DMEyF_Nicky_Entrega_Final.ipynb` líneas 517–524; `VERIFICACION_FINAL.txt` líneas 1–3)
12. **Variantes apagadas y evaluación de cortes.** Con sus interruptores en FALSE no se ejecutan: control y ranking con 20 semillas, etiquetas artificiales, ranking de montos, clase sólo BAJA+2, indicadores de estado de tarjetas, vinculación, exclusión de cierres medida en junio, ceros y tendencias, una segunda búsqueda bayesiana, grupos de 5 semillas, mezcla de dos ensambles y la tabla de ganancia de junio por corte (10.000 a 11.500, incluido 10.375). REGISTRO_EXPERIMENTOS.csv lista cada interruptor con la decisión anotada por el autor. (`codigo/experimentos.R` líneas 1–161; `codigo/cortes.R` líneas 1–17; `DMEyF_Nicky_Entrega_Final.ipynb` líneas 531–690)

## Archivos

- `ESTADO_VALIDACION.json` · explicacion · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/ESTADO_VALIDACION.json.txt) — Registro del estado de verificación: formato de notebooks, sintaxis de Python y R, procedencia de hiperparámetros, semillas y columnas, SHA256 del CSV de referencia y réplica desde el crudo figuran como OK o verificados. Declara corte 10375, un campo 'publico' con valor 106.3975, un identificador de envío, el texto 'K11500; falta reenvío K10375' en ultimo_submit_confirmado y fecha de verificación 2026-10-11 22:45:49.
- `VALIDAR_Y_LANZAR.py` · secundario · Python · 43 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/VALIDAR_Y_LANZAR.py.txt) — Script Python de validación y lanzamiento: comprueba el MD5 del crudo (ruta por DMEYF_DATOS o /home/ds/buckets/b1/datasets/competencia_01_crudo.csv), analiza la sintaxis de cada celda de las dos notebooks (Python con ast, R con Rscript), ejecuta VALIDAR_SINTAXIS.R, verifica paquetes y versiones y lanza en segundo plano Rscript REPRODUCIR_FINAL.R con salida en salida_verificacion/ y log en REPLICA.log.
- `BO_Origen.ipynb` · principal · Jupyter (R) · 110 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/BO_Origen.ipynb.txt) — Notebook de la optimización bayesiana que produjo los hiperparámetros usados en la entrega. Repite la carga y la configuración, activa bo_origen y ejecuta bayes() (definida en codigo/motor.R) sobre la receta ORIGINAL_LAG2; al final imprime el historial guardado en procedencia_bo/.
- `VERIFICACION_FINAL.txt` · explicacion · Texto · 3 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/VERIFICACION_FINAL.txt.txt) — Constancia de tres líneas con el formato que escribe final.R: 'REPRODUCCION EXACTA: OK', el SHA256 7715cbb9…5caa y la ruta del CSV generado en una carpeta /home/ds/buckets/b1/exp/ENTREGA_REPLICA_K10375/.
- `README.md` · explicacion · Markdown · 78 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/README.md.txt) — Presentación de la entrega en primera persona: predicción elegida, secuencia de ejecución (notebook o Rscript), receta del modelo final, optimización de origen, ambiente y versiones, lista de experimentos e interruptores, y estado de verificación con el SHA256 esperado.
- `MANIFIESTO_ARCHIVOS.json` · configuracion · JSON · 678 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/MANIFIESTO_ARCHIVOS.json.txt) — Lista de 169 archivos del repositorio con el SHA256 de cada uno (campos archivo y sha256).
- `DMEyF_Nicky_Entrega_Final.ipynb` · principal · Jupyter (R) · 697 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/DMEyF_Nicky_Entrega_Final.ipynb.txt) — Notebook de la entrega. Una celda Python ubica y verifica el dataset; las celdas R definen parámetros e interruptores, las funciones del motor (mismo contenido que codigo/motor.R), la preparación (clase, corrección de datos, lags y deltas), el entrenamiento final de 10 semillas con promedio, corte en 10.375 y verificación por SHA256, y los bloques de experimentos y de cortes, que sólo corren si su interruptor está en TRUE.
- `VALIDAR_SINTAXIS.R` · secundario · R · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/VALIDAR_SINTAXIS.R.txt) — Recorre todos los archivos .R del repositorio y aplica parse() a cada uno; imprime una línea por archivo.
- `REPRODUCIR_FINAL.R` · principal · R · 3 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/REPRODUCIR_FINAL.R.txt) — Punto de entrada sin Jupyter: ejecuta con source() configuracion.R, preparacion.R y final.R de la carpeta codigo/.
- `procedencia/fuentes_originales/SIN_CIERRES_P_V1/ENTRENAR.R` · secundario · R · 140 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/SIN_CIERRES_P_V1/ENTRENAR.R.txt) — Versión anterior de la producción Sin cierres, con rutas /home/ds/buckets/b1/exp/…: entrena las 10 semillas con 202103-202106 y los mismos 752 predictores, y escribe archivos de 10.500 clientes por semilla, por 20 grupos de 5 semillas y para el promedio de las 10. Hay una copia idéntica en procedencia/fuentes_experimentos/FINAL_COMPARACIONES_V1/ENTREGA/.
- `procedencia/fuentes_originales/SIN_CIERRES_H_V1/EJECUTAR_SIN_CIERRES.R` · secundario · R · 194 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/SIN_CIERRES_H_V1/EJECUTAR_SIN_CIERRES.R.txt) — Versión anterior de experimentos/sin_cierres_historico.R; difiere en que las carpetas y el archivo de bloqueo están escritos como rutas /home/ds/….
- `procedencia/fuentes_originales/fuentes_integral/CELDA_19.R` · secundario · R · 265 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/fuentes_integral/CELDA_19.R.txt)
- `procedencia/fuentes_originales/fuentes_integral/CELDA_22.R` · secundario · R · 39 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/fuentes_integral/CELDA_22.R.txt)
- `procedencia/fuentes_originales/fuentes_integral/CELDA_07.R` · secundario · R · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/fuentes_integral/CELDA_07.R.txt)
- `procedencia/fuentes_originales/fuentes_integral/CELDA_03.R` · secundario · R · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/fuentes_integral/CELDA_03.R.txt)
- `procedencia/fuentes_originales/fuentes_integral/CELDA_04.R` · secundario · R · 337 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/fuentes_integral/CELDA_04.R.txt)
- `procedencia/fuentes_originales/fuentes_integral/CELDA_21.R` · secundario · R · 70 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/fuentes_integral/CELDA_21.R.txt)
- `procedencia/fuentes_originales/fuentes_integral/CELDA_25.R` · secundario · R · 64 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/fuentes_integral/CELDA_25.R.txt)
- `procedencia/fuentes_originales/fuentes_integral/CELDA_05.R` · secundario · R · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/fuentes_integral/CELDA_05.R.txt)
- `procedencia/fuentes_originales/fuentes_integral/EJECUTAR_MINIMOS.R` · secundario · R · 1121 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/fuentes_integral/EJECUTAR_MINIMOS.R.txt) — Archivo de 1.121 líneas que reúne, en ese orden, el contenido de las celdas 03, 04, 05, 06, 07, 19, 20, 21, 22, 23, otra vez 21, y 25 de una notebook anterior: plan e interruptores, funciones del motor, carga, recetas, motor de variantes, búsquedas por receta, producción de agosto, armado de lotes de archivos y cierre.
- `procedencia/fuentes_originales/fuentes_integral/CELDA_20.R` · secundario · R · 73 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/fuentes_integral/CELDA_20.R.txt)
- `procedencia/fuentes_originales/fuentes_integral/CELDA_23.R` · secundario · R · 99 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/fuentes_integral/CELDA_23.R.txt)
- `procedencia/fuentes_originales/fuentes_integral/CELDA_06.R` · secundario · R · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_originales/fuentes_integral/CELDA_06.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_19.R` · secundario · R · 265 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_19.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_07.R` · secundario · R · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_07.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_03.R` · secundario · R · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_03.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_04.R` · secundario · R · 337 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_04.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_21.R` · secundario · R · 70 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_21.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_05.R` · secundario · R · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_05.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_20.R` · secundario · R · 73 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_20.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/REANUDAR_ENTORNO_20261010_140950.R` · secundario · R · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/REANUDAR_ENTORNO_20261010_140950.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/EJECUTAR_HISTORIA.R` · secundario · R · 40 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/EJECUTAR_HISTORIA.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_06.R` · secundario · R · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_H/CELDA_06.R.txt)
- `procedencia/fuentes_experimentos/RANK_ZERO_TEND3_H_V1/EJECUTAR.R` · secundario · R · 255 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/RANK_ZERO_TEND3_H_V1/EJECUTAR.R.txt)
- `procedencia/fuentes_experimentos/STATUS_TRANSICIONES_H_V1/EJECUTAR_STATUS.R` · secundario · R · 229 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/STATUS_TRANSICIONES_H_V1/EJECUTAR_STATUS.R.txt)
- `procedencia/fuentes_experimentos/SIN_CIERRES_BO_FINAL_V1/EJECUTAR.R` · secundario · R · 227 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/SIN_CIERRES_BO_FINAL_V1/EJECUTAR.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/EJECUTAR_PRODUCCION.R` · secundario · R · 126 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/EJECUTAR_PRODUCCION.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_19.R` · secundario · R · 265 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_19.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_07.R` · secundario · R · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_07.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_03.R` · secundario · R · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_03.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_04.R` · secundario · R · 337 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_04.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_05.R` · secundario · R · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_05.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_20.R` · secundario · R · 73 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_20.R.txt)
- `procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_06.R` · secundario · R · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ARTIFICIALES_RANK_P_V1/fuentes/CELDA_06.R.txt)
- `procedencia/fuentes_experimentos/VISA_COMPARACIONES_H_V1/COMPARAR_VERIFICADO.R` · secundario · R · 120 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/VISA_COMPARACIONES_H_V1/COMPARAR_VERIFICADO.R.txt)
- `procedencia/fuentes_experimentos/CORTES_ROBUSTOS_H_V1/ANALIZAR.R` · secundario · R · 115 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/CORTES_ROBUSTOS_H_V1/ANALIZAR.R.txt) — Análisis de cortes en junio para cuatro recetas con 20 semillas cada una: en una grilla de 8.000 a 12.000 cada 250 calcula ganancia del promedio, media y mínimo en una ventana de ±500 y dispersión entre semillas; toma como centro el corte de mayor media de ventana y guarda ese corte y sus vecinos ±250.
- `procedencia/fuentes_experimentos/SIN_CIERRES_COMPARACIONES_H_V1/COMPARAR_VERIFICADO.R` · secundario · R · 120 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/SIN_CIERRES_COMPARACIONES_H_V1/COMPARAR_VERIFICADO.R.txt)
- `procedencia/fuentes_experimentos/VINCULACION_H_V1/FUENTE_STATUS_ORIGINAL.R` · secundario · R · 229 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/VINCULACION_H_V1/FUENTE_STATUS_ORIGINAL.R.txt)
- `procedencia/fuentes_experimentos/VINCULACION_H_V1/EJECUTAR_VINCULACION.R` · secundario · R · 258 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/VINCULACION_H_V1/EJECUTAR_VINCULACION.R.txt)
- `procedencia/fuentes_experimentos/STATUS_ABLACIONES_H_V1/SOLO_MASTER/EJECUTAR.R` · secundario · R · 230 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/STATUS_ABLACIONES_H_V1/SOLO_MASTER/EJECUTAR.R.txt)
- `procedencia/fuentes_experimentos/STATUS_ABLACIONES_H_V1/SOLO_VISA/EJECUTAR.R` · secundario · R · 230 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/STATUS_ABLACIONES_H_V1/SOLO_VISA/EJECUTAR.R.txt)
- `procedencia/fuentes_experimentos/FINAL_COMPARACIONES_V1/PREPARAR_FINAL.R` · secundario · R · 115 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/FINAL_COMPARACIONES_V1/PREPARAR_FINAL.R.txt) — A partir de las probabilidades guardadas de las 10 semillas Sin cierres escribe archivos con cortes 10.000, 10.250, 10.500, 10.750, 11.000 y 11.500; busca además modelos de control de agosto compatibles ya guardados y, si encuentra los 10, exporta su promedio y 20 grupos de 5 semillas con corte 10.500.
- `procedencia/fuentes_experimentos/FINAL_COMPARACIONES_V1/ENTREGA/ENTRENAR.R` · secundario · R · 140 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/FINAL_COMPARACIONES_V1/ENTREGA/ENTRENAR.R.txt)
- `procedencia/fuentes_experimentos/ENSAMBLES5_STATUS_V1/EJECUTAR.R` · secundario · R · 216 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ENSAMBLES5_STATUS_V1/EJECUTAR.R.txt)
- `procedencia/fuentes_experimentos/ENSAMBLES5_STATUS_V1/STATUS_CORREGIDO_JUNIO/CORREGIR_AUDITORIA.R` · secundario · R · 123 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/procedencia/fuentes_experimentos/ENSAMBLES5_STATUS_V1/STATUS_CORREGIDO_JUNIO/CORREGIR_AUDITORIA.R.txt)
- `codigo/preparacion.R` · principal · R · 22 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/codigo/preparacion.R.txt) — Ejecuta la carga de la base y el cálculo de lags y deltas, lee de procedencia_bo/ los hiperparámetros de la optimización de origen y define la receta ORIGINAL_LAG2. Mismo contenido que la celda 9 de la notebook de entrega.
- `codigo/motor.R` · principal · R · 337 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/codigo/motor.R.txt) — Funciones compartidas: caché con firma y bloqueo, parámetros base de LightGBM, reconstrucción de la clase y corrección de datos (cargar_base), lags y deltas (preparar_features), armado de datasets, entrenamiento con predicción y ganancia (fit_score), optimización bayesiana (bayes) y funciones de variantes que la ruta final no invoca (canaritos, filtro de negativos, etiquetas artificiales, ablaciones, auditoría de distribuciones). Idéntico a la celda 7 de la notebook de entrega.
- `codigo/cortes.R` · secundario · R · 17 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/codigo/cortes.R.txt) — Tabla de ganancia de junio por corte para el ensamble del experimento Sin cierres histórico; corre sólo con cortes_historicos en TRUE. Mismo contenido que la celda 15 de la notebook. REPRODUCIR_FINAL.R no lo carga.
- `codigo/motor_integral.R` · secundario · R · 131 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/codigo/motor_integral.R.txt) — Funciones que usan sólo los experimentos: ranking de todas las variables después de lags, predicción de un mes con un modelo guardado, etiquetas artificiales con un modelo docente, promedio de probabilidades alineado por cliente y resumen de ganancia de junio por cortes.
- `codigo/final.R` · principal · R · 64 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/codigo/final.R.txt) — Entrena 10 modelos LightGBM con 202103-202106 y 752 predictores, promedia las probabilidades de 202108, escribe los 10.375 clientes de mayor probabilidad y verifica el SHA256 del archivo. Mismo contenido que la celda 11 de la notebook de entrega.
- `codigo/configuracion.R` · principal · R · 44 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/codigo/configuracion.R.txt) — Parámetros de la corrida (semillas, meses, límites de la búsqueda), interruptores, corte y SHA256 esperados, resolución de carpetas por variables de entorno, verificación del MD5 del crudo y de las versiones de R y paquetes; al final carga motor.R. Mismo contenido que la celda 5 de la notebook de entrega más la línea que carga el motor.
- `codigo/experimentos.R` · secundario · R · 161 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/codigo/experimentos.R.txt) — Bloque de experimentos, apagado en la entrega. Si algún interruptor está en TRUE trabaja en salida/laboratorio con 20 semillas y ejecuta las variantes pedidas: control, ranking de todas las variables, etiquetas artificiales, ranking de montos, clase sólo BAJA+2, los scripts de experimentos/, grupos de 5 semillas, comparaciones y mezcla de dos ensambles. Equivale a la celda 13 de la notebook, con tres interruptores adicionales (visa_comparaciones, sin_cierres_comparaciones, mezcla_control_rank). REPRODUCIR_FINAL.R no lo carga.
- `experimentos/vinculacion.R` · secundario · R · 258 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/experimentos/vinculacion.R.txt) — Agrega 26 variables VN_: indicadores de actividad en el mes para seis grupos de productos (haberes, débitos automáticos, pagos, tarjeta de crédito, tarjeta de débito, canales digitales), su pérdida o ganancia respecto del mes anterior, conteos y combinaciones; compara en junio, con 10 semillas, contra los modelos de control.
- `experimentos/solo_master.R` · secundario · R · 230 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/experimentos/solo_master.R.txt) — Igual a tarjetas.R, usando sólo los indicadores de historia y de Master_status.
- `experimentos/visa_comparaciones.R` · secundario · R · 120 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/experimentos/visa_comparaciones.R.txt) — Misma comparación que sin_cierres_comparaciones.R, aplicada a los resultados de solo_visa.R contra el control.
- `experimentos/sin_cierres_historico.R` · secundario · R · 194 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/experimentos/sin_cierres_historico.R.txt) — Experimento Sin cierres en junio: reentrena 10 semillas con 202103-202104 quitando las 10 columnas de Visa_fultimo_cierre y Master_fultimo_cierre (742 predictores) y compara la ganancia de 202106 contra los modelos de control, por semilla y en el promedio de 10.
- `experimentos/bo_sin_cierres_nueva.R` · secundario · R · 227 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/experimentos/bo_sin_cierres_nueva.R.txt) — Segunda optimización bayesiana sobre los 742 predictores sin cierres ni préstamos: diseño de 4 puntos (los hiperparámetros vigentes y 3 generados) más 2 iteraciones de mlrMBO, objetivo ganancia de junio en el corte 10.500 con métrica auc. Confirma con 3 semillas contra los hiperparámetros vigentes y, si la media 10.000-11.500 es mayor y la ganancia en 10.500 no es menor, entrena 10 semillas con 202103-202106 y escribe archivos con cortes 10.000, 10.250, 10.500 y 10.750.
- `experimentos/tarjetas.R` · secundario · R · 229 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/experimentos/tarjetas.R.txt) — Agrega indicadores de transición de Visa_status y Master_status contra 1 y 2 meses antes (pasa a NA, sale de NA, NA persistente, cambio, estable, ambas o alguna tarjeta) y compara en junio, con 10 semillas, contra los modelos de control.
- `experimentos/rank_zero_tend3.R` · secundario · R · 255 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/experimentos/rank_zero_tend3.R.txt) — Sobre la receta con ranking de todas las variables agrega, por variable, un indicador de valor cero, la pendiente y el promedio de los últimos tres meses calendario (estos dos con rank_cero por mes) y compara en junio, con 10 semillas, contra los modelos de esa receta.
- `experimentos/sin_cierres_comparaciones.R` · secundario · R · 120 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/experimentos/sin_cierres_comparaciones.R.txt) — Sin entrenar modelos, compara en junio el promedio de 10 semillas de control con el de Sin cierres: curvas de ganancia, diferencias en el corte 10.500 y en dos ventanas, 20 grupos de 5 semillas, e intercambio de clientes entre los primeros 10.500 de cada lista.
- `experimentos/solo_visa.R` · secundario · R · 230 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/nicobaranek/experimentos/solo_visa.R.txt) — Igual a tarjetas.R, usando sólo los 12 indicadores de historia y de Visa_status.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### BO_Origen.ipynb

Notebook de la optimización bayesiana que produjo los hiperparámetros usados en la entrega. Repite la carga y la configuración, activa bo_origen y ejecuta bayes() (definida en codigo/motor.R) sobre la receta ORIGINAL_LAG2; al final imprime el historial guardado en procedencia_bo/.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–26] Celdas 1 a 3. Título y carga en Python, igual a la de la notebook de entrega:
#   ubica el crudo (DMEYF_DATOS o datos/competencia_01_crudo.csv), lo descarga si no existe, verifica el MD5 y
#   escribe RUTA_DATOS.txt.
#%% celda 1 [texto]
# Mi optimización bayesiana de origen

Documento y puedo volver a ejecutar la BO ORIGINAL_LAG2 que seleccionó los HP usados en mi entrega. No la confundo con la BO de Sin cierres posterior, que descarté.

#%% celda 2 [texto]
## 1. Carga — Python

#%% celda 3 [código]
# Ubico el crudo y preparo mi carpeta de trabajo sin modificar el dataset.
from pathlib import Path
import hashlib, json, os, urllib.request
carpeta = Path.cwd()
datos = carpeta / 'datos'
datos.mkdir(exist_ok=True)
crudo = Path(os.environ.get('DMEYF_DATOS', str(datos / 'competencia_01_crudo.csv')))
if not crudo.is_file():
    crudo.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(
        'https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv', crudo)
with crudo.open('rb') as f:
    md5 = hashlib.file_digest(f, 'md5').hexdigest()
assert md5 == 'b6f759764c5d04cbf068548517ae1249', 'El crudo no coincide con mi corrida.'
(carpeta / 'RUTA_DATOS.txt').write_text(str(crudo.resolve()))
print('Dataset verificado:', crudo)

# [Anotación · líneas 27–54] Celdas 4 y 5 (inicio). El texto indica entrenamiento 202103-202104, evaluación en
#   202106, objetivo en el corte 11.500, 4 puntos iniciales y 8 propuestas. El código toma la ruta del dataset
#   de RUTA_DATOS.txt y define PARAM con los mismos valores que la notebook de entrega y una lista SW de 17
#   interruptores.
#%% celda 4 [texto]
## 2. Optimización — R

Cambio al kernel R. Uso marzo–abril para entrenar, junio para evaluar y K11500 como objetivo de esta BO. Mantengo 4 puntos iniciales y 8 propuestas por EI.

#%% celda 5 [código]
Sys.setenv(DMEYF_DATOS=readLines('RUTA_DATOS.txt',warn=FALSE)[1])
# Fijo mi entrega y dejo apagadas las variantes que no elegí.
PARAM <- list(
 semilla=100613L,
 semillas=c(100613L,100267L,101611L,102481L,103651L,104729L,
            105019L,105613L,106013L,106619L),
 threads=6L,train=c(202103L,202104L),
 train_final=c(202103L,202104L,202105L,202106L),
 valid=202106L,future=202108L,corte=11500L,orden_lags=2L,
 incluir_id_mes=TRUE,bo_evaluaciones=12L,bo_iniciales=4L,
 bounds=list(iter=c(512L,4096L),leaves=c(8L,256L),logh=c(-3,1)),
 top_configuraciones=1L,rank_campos=character()
)
SW <- list(
 reproducir_final=TRUE,bo_origen=FALSE,
 control=FALSE,rankings=FALSE,artificiales_original=FALSE,
 artificiales_rank=FALSE,rank_montos=FALSE,target_baja2=FALSE,
 tarjetas=FALSE,solo_visa=FALSE,solo_master=FALSE,
 vinculacion=FALSE,sin_cierres_historico=FALSE,
 rank_zero_tend3=FALSE,bo_sin_cierres_nueva=FALSE,
 diagnosticos_ens5=FALSE,cortes_historicos=FALSE
)
# [Anotación · líneas 55–79] Fija CORTE_FINAL y SHA_FINAL, resuelve carpetas y dataset, comprueba MD5,
#   paquetes y versiones (R 4.6.1, lightgbm 4.7.0.99, data.table 1.18.6.1) y carga codigo/motor.R. Al final pone
#   reproducir_final en FALSE y bo_origen en TRUE.
CORTE_FINAL <- 10375L
SHA_FINAL <- '7715cbb9568462c2a1f9b0534528fbce3f77c54cd43a255c59476dc9a37b5caa'
CARPETA <- normalizePath(Sys.getenv('DMEYF_ENTREGA',unset=getwd()),mustWork=TRUE)
if(!file.exists(file.path(CARPETA,'codigo','motor.R')))
 stop('Debo ejecutar desde la carpeta de entrega o definir DMEYF_ENTREGA.')
RAIZ_NUEVA <- Sys.getenv('DMEYF_SALIDA',unset=file.path(CARPETA,'salida'))
RAW_NUEVO <- Sys.getenv('DMEYF_DATOS',unset=file.path(CARPETA,'datos','competencia_01_crudo.csv'))
if(!file.exists(RAW_NUEVO)) stop('Debo indicar DMEYF_DATOS con el dataset crudo.')
if(unname(tools::md5sum(RAW_NUEVO))!='b6f759764c5d04cbf068548517ae1249')
 stop('El crudo no coincide con el dataset de la corrida final.')
Sys.setenv(DMEYF_RAIZ=RAIZ_NUEVA,DMEYF_DATOS=RAW_NUEVO)
if(dir.exists('/home/ds/.local/lib/R/site-library'))
 .libPaths(unique(c('/home/ds/.local/lib/R/site-library',.libPaths())))
paquetes <- c('data.table','lightgbm','digest','jsonlite','filelock')
faltan <- paquetes[!vapply(paquetes,requireNamespace,logical(1),quietly=TRUE)]
if(length(faltan)) stop('Debo instalar estos paquetes: ',paste(faltan,collapse=', '))
library(lightgbm)
stopifnot(as.character(getRversion())=='4.6.1',
 as.character(packageVersion('lightgbm'))=='4.7.0.99',
 as.character(packageVersion('data.table'))=='1.18.6.1')
source(file.path(CARPETA,'codigo','motor.R'),local=.GlobalEnv)

SW$reproducir_final <- FALSE
SW$bo_origen <- TRUE

# [Anotación · líneas 80–103] Celda 6. Ejecuta cargar_base() y preparar_features(), lee la configuración
#   guardada en procedencia_bo/52fc1b5d…/TERMINADO.rds y comprueba que sea 1907 / 77 / 2,83699883991516. Como
#   bo_origen es TRUE, exige mlrMBO, mlr, ParamHelpers, smoof y DiceKriging, ejecuta bayes() sobre la receta
#   ORIGINAL_LAG2 y guarda el resultado en BO_ORIGEN_REEJECUTADA.rds.
#%% celda 6 [código]
# Reconstruyo el target, corrijo mayo y calculo la historia calendario exacta.
D <- cargar_base()
REP <- preparar_features(D,FALSE)
stopifnot(REP$id=='c9527308c55d2d52c924dc64ce5594db3d240bce96c8a548c6f48a06239c71c8')
rm(D)
gc(full=TRUE)
# Dejo anotado: Recupero la procedencia de los HP sin hacer pasar una BO nueva por la original.
ORIGEN <- readRDS(file.path(CARPETA,'procedencia_bo',
 '52fc1b5d908fb495ce06d1ed3038defbaf9a2609d2ea0bc80904d2ba8b58c6ed',
 'TERMINADO.rds'))
HP_FINAL <- ORIGEN$valor$optimos[[1L]]
stopifnot(HP_FINAL$num_iterations==1907L,HP_FINAL$num_leaves==77L,
 abs(HP_FINAL$min_sum_hessian_in_leaf-2.83699883991516)<1e-12)
REC_CONTROL <- list(nombre='ORIGINAL_LAG2',rep=REP,estrategia='COMPLETO',
 umbral=NULL,seleccion=NULL,excluir=character(),planes=NULL)
# Dejo anotado: Si activo la BO de origen, la ejecuto en otra raíz sin reutilizar su resultado.
if(SW$bo_origen) {
 for(paquete in c('mlrMBO','mlr','ParamHelpers','smoof','DiceKriging'))
  if(!requireNamespace(paquete,quietly=TRUE))stop('Debo instalar ',paquete)
 b <- bayes(REC_CONTROL)
 atomic(b,file.path(RAIZ,'BO_ORIGEN_REEJECUTADA.rds'))
}

# [Anotación · líneas 104–110] Celdas 7 y 8. Imprime el historial y los hiperparámetros de la optimización
#   guardada. El texto final indica que el CSV de la entrega se genera con la notebook de entrega y que una
#   reejecución de la búsqueda no reemplaza la selección guardada.
#%% celda 7 [código]
# Comparo el resultado con la procedencia que guardé.
print(ORIGEN$valor$historial)
print(HP_FINAL)

#%% celda 8 [texto]
Para generar el CSV final vuelvo a la notebook de entrega con sus switches predeterminados. El historial guardado documenta los HP efectivamente usados; una reejecución de BO no sustituye silenciosamente esa selección.
```

### DMEyF_Nicky_Entrega_Final.ipynb

Notebook de la entrega. Una celda Python ubica y verifica el dataset; las celdas R definen parámetros e interruptores, las funciones del motor (mismo contenido que codigo/motor.R), la preparación (clase, corrección de datos, lags y deltas), el entrenamiento final de 10 semillas con promedio, corte en 10.375 y verificación por SHA256, y los bloques de experimentos y de cortes, que sólo corren si su interruptor está en TRUE.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–28] Celdas 1 a 3. Presentación de la entrega y carga en Python: toma la ruta del
#   dataset crudo de la variable de entorno DMEYF_DATOS o usa datos/competencia_01_crudo.csv; si el archivo no
#   existe lo descarga de una URL de storage.googleapis.com. Calcula el MD5 del archivo, lo compara con
#   b6f759764c5d04cbf068548517ae1249 y escribe la ruta resuelta en RUTA_DATOS.txt.
#%% celda 1 [texto]
# Competencia DMEyF — mi desarrollo y entrega final

Nicky Baranek. Cierro con Sin cierres original, diez semillas y 10.375 clientes. Conservo los experimentos que descarté para dejar trazabilidad de mis decisiones.

#%% celda 2 [texto]
## 1. Carga de datos — Python

Ejecuto esta sección con el kernel Python. Después cambio a R; no ejecuto las celdas Python con el kernel R.

#%% celda 3 [código]
# Ubico el crudo y preparo mi carpeta de trabajo sin modificar el dataset.
from pathlib import Path
import hashlib, json, os, urllib.request
carpeta = Path.cwd()
datos = carpeta / 'datos'
datos.mkdir(exist_ok=True)
crudo = Path(os.environ.get('DMEYF_DATOS', str(datos / 'competencia_01_crudo.csv')))
if not crudo.is_file():
    crudo.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(
        'https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv', crudo)
with crudo.open('rb') as f:
    md5 = hashlib.file_digest(f, 'md5').hexdigest()
assert md5 == 'b6f759764c5d04cbf068548517ae1249', 'El crudo no coincide con mi corrida.'
(carpeta / 'RUTA_DATOS.txt').write_text(str(crudo.resolve()))
print('Dataset verificado:', crudo)

# [Anotación · líneas 29–49] Celdas 4 y 5 (inicio), ya en R. Toma la ruta del dataset de RUTA_DATOS.txt si
#   DMEYF_DATOS está vacía y define PARAM: semilla 100613 para la búsqueda de hiperparámetros, lista de 10
#   semillas, 6 hilos, entrenamiento 202103-202104 en la etapa histórica y 202103-202106 en la final, validación
#   en 202106, predicción en 202108, corte 11.500 para medir la ganancia de junio, lags de orden 2,
#   numero_de_cliente y foto_mes incluidos como predictores, y una búsqueda bayesiana de 12 evaluaciones (4
#   iniciales) con límites 512-4096 iteraciones, 8-256 hojas y exponente -3 a 1 para el Hessian mínimo.
#%% celda 4 [texto]
## 2. Modelo y experimentos — R

Cambio al kernel R y mantengo la misma carpeta de trabajo. Ejecuto las celdas R en orden. Para la réplica final dejo los switches tal como están.

#%% celda 5 [código]
# Cargo la ruta que dejé desde Python.
if(!nzchar(Sys.getenv('DMEYF_DATOS')))
 Sys.setenv(DMEYF_DATOS=readLines('RUTA_DATOS.txt',warn=FALSE)[1])
# Fijo mi entrega y dejo apagadas las variantes que no elegí.
PARAM <- list(
 semilla=100613L,
 semillas=c(100613L,100267L,101611L,102481L,103651L,104729L,
            105019L,105613L,106013L,106619L),
 threads=6L,train=c(202103L,202104L),
 train_final=c(202103L,202104L,202105L,202106L),
 valid=202106L,future=202108L,corte=11500L,orden_lags=2L,
 incluir_id_mes=TRUE,bo_evaluaciones=12L,bo_iniciales=4L,
 bounds=list(iter=c(512L,4096L),leaves=c(8L,256L),logh=c(-3,1)),
 top_configuraciones=1L,rank_campos=character()
)
# [Anotación · líneas 50–62] Define los interruptores SW: reproducir_final en TRUE y los otros 19 (bo_origen y
#   las variantes de experimentos) en FALSE. Fija el corte de la entrega en 10.375 clientes (CORTE_FINAL) y el
#   SHA256 esperado del archivo de salida (SHA_FINAL).
SW <- list(
 reproducir_final=TRUE,bo_origen=FALSE,
 control=FALSE,rankings=FALSE,artificiales_original=FALSE,
 artificiales_rank=FALSE,rank_montos=FALSE,target_baja2=FALSE,
 tarjetas=FALSE,solo_visa=FALSE,solo_master=FALSE,
 vinculacion=FALSE,sin_cierres_historico=FALSE,
 rank_zero_tend3=FALSE,bo_sin_cierres_nueva=FALSE,
 diagnosticos_ens5=FALSE,cortes_historicos=FALSE,
 mezcla_control_rank=FALSE,visa_comparaciones=FALSE,
 sin_cierres_comparaciones=FALSE
)
CORTE_FINAL <- 10375L
SHA_FINAL <- '7715cbb9568462c2a1f9b0534528fbce3f77c54cd43a255c59476dc9a37b5caa'
# [Anotación · líneas 63–81] Resuelve la carpeta de la entrega (DMEYF_ENTREGA o el directorio actual) y exige
#   que contenga codigo/motor.R; define la carpeta de salida (DMEYF_SALIDA o salida/) y la ruta del crudo, cuyo
#   MD5 vuelve a comprobar. Agrega /home/ds/.local/lib/R/site-library a las rutas de paquetes si esa carpeta
#   existe, exige data.table, lightgbm, digest, jsonlite y filelock, y detiene la ejecución si las versiones no
#   son R 4.6.1, lightgbm 4.7.0.99 y data.table 1.18.6.1.
CARPETA <- normalizePath(Sys.getenv('DMEYF_ENTREGA',unset=getwd()),mustWork=TRUE)
if(!file.exists(file.path(CARPETA,'codigo','motor.R')))
 stop('Debo ejecutar desde la carpeta de entrega o definir DMEYF_ENTREGA.')
RAIZ_NUEVA <- Sys.getenv('DMEYF_SALIDA',unset=file.path(CARPETA,'salida'))
RAW_NUEVO <- Sys.getenv('DMEYF_DATOS',unset=file.path(CARPETA,'datos','competencia_01_crudo.csv'))
if(!file.exists(RAW_NUEVO)) stop('Debo indicar DMEYF_DATOS con el dataset crudo.')
if(unname(tools::md5sum(RAW_NUEVO))!='b6f759764c5d04cbf068548517ae1249')
 stop('El crudo no coincide con el dataset de la corrida final.')
Sys.setenv(DMEYF_RAIZ=RAIZ_NUEVA,DMEYF_DATOS=RAW_NUEVO)
if(dir.exists('/home/ds/.local/lib/R/site-library'))
 .libPaths(unique(c('/home/ds/.local/lib/R/site-library',.libPaths())))
paquetes <- c('data.table','lightgbm','digest','jsonlite','filelock')
faltan <- paquetes[!vapply(paquetes,requireNamespace,logical(1),quietly=TRUE)]
if(length(faltan)) stop('Debo instalar estos paquetes: ',paste(faltan,collapse=', '))
library(lightgbm)
stopifnot(as.character(getRversion())=='4.6.1',
 as.character(packageVersion('lightgbm'))=='4.7.0.99',
 as.character(packageVersion('data.table'))=='1.18.6.1')

# [Anotación · líneas 82–101] Celdas 6 y 7 (inicio). Carga data.table, digest, jsonlite y filelock, fija los
#   hilos de data.table y crea bajo la carpeta de salida las subcarpetas auditoria, datos, features, datasets,
#   modelos, scores, bo, seleccion, resultados, submits, figuras y fuentes. Define utilidades: hash SHA256 de un
#   objeto, mensaje con fecha a pantalla y a PROGRESO.log, guardado de .rds y .csv mediante archivo temporal y
#   renombrado, y un registro CSV de qué resultados se calculan y cuáles se reutilizan.
#%% celda 6 [texto]
### 2.1 Mis funciones

Mantengo el preprocesamiento y el motor que usé en las corridas. No dependo de archivos de otra VM.

#%% celda 7 [código]
# Dejo anotado: CELDA 04 — Defino mis funciones y la persistencia.
# Mantengo el cálculo en R y guardo cada resultado costoso antes de avanzar.
suppressPackageStartupMessages({library(data.table);library(digest);library(jsonlite);library(filelock)})
options(scipen=999, datatable.print.nrows=30)
setDTthreads(PARAM$threads)
CODE <- 'MAESTRA_CATEDRA_20261007_v1'
RAIZ <- Sys.getenv('DMEYF_RAIZ'); RAW <- Sys.getenv('DMEYF_DATOS')
stopifnot(nzchar(RAIZ),file.exists(RAW))
for (s in c('auditoria','datos','features','datasets','modelos','scores','bo','seleccion','resultados','submits','figuras','fuentes')) dir.create(file.path(RAIZ,s),recursive=TRUE,showWarnings=FALSE)
hash <- function(x) digest(x,algo='sha256')
log_ <- function(...) {s<-paste(format(Sys.time(),'%Y-%m-%d %H:%M:%S %Z'),paste(...,collapse=' '));cat(s,'\n');cat(s,'\n',file=file.path(RAIZ,'PROGRESO.log'),append=TRUE)}
atomic <- function(x,path) {tmp<-paste0(path,'.tmp_',Sys.getpid());saveRDS(x,tmp,compress=FALSE);if(!file.rename(tmp,path)){if(!file.copy(tmp,path,overwrite=TRUE))stop('No pude persistir ',path);unlink(tmp)};invisible(path)}
csv <- function(x,path) {tmp<-paste0(path,'.tmp_',Sys.getpid());fwrite(x,tmp);if(!file.rename(tmp,path)){if(!file.copy(tmp,path,overwrite=TRUE))stop('No pude persistir ',path);unlink(tmp)}}
registro <- function(etapa,archivo,accion,motivo){p<-file.path(RAIZ,'auditoria','AUDITORIA_REUTILIZACION.csv');d<-data.table(fecha=as.character(Sys.time()),etapa=etapa,archivo=archivo,accion=accion,motivo=motivo);fwrite(d,p,append=file.exists(p),col.names=!file.exists(p))}
# [Anotación · líneas 102–117] Define cache(): guarda cada resultado en un .rds cuyo nombre es el hash de su
#   firma, lo reutiliza si ya existe con firma idéntica y toma un archivo de bloqueo en ~/.cache/dmeyf_locks
#   para impedir dos ejecuciones simultáneas del mismo cálculo. Registra las versiones de R, lightgbm y
#   data.table, el MD5 del crudo y la salida de sessionInfo(); define PRESTAMOS (cprestamos_personales,
#   mprestamos_personales) y el vector de semillas.
# Dejo anotado: Los locks de cálculo viven en disco local; todos los procesos de esta VM comparten la ruta.
# No ejecuto simultáneamente esta misma RAIZ desde dos VM distintas.
LOCK_DIR<-file.path(path.expand('~/.cache/dmeyf_locks'),hash(RAIZ));dir.create(LOCK_DIR,recursive=TRUE,showWarnings=FALSE)
cache <- function(etapa,firma,fun){
 p<-file.path(RAIZ,etapa,paste0(hash(firma),'.rds'))
 lk<-filelock::lock(file.path(LOCK_DIR,paste0(hash(p),'.lock')),timeout=0)
 if(is.null(lk))stop('Otra ejecución está usando este checkpoint: ',p)
 on.exit(filelock::unlock(lk))
 if(file.exists(p)){z<-readRDS(p);stopifnot(identical(z$firma,firma));registro(etapa,p,'REUTILIZAR','Firma exacta');return(z$valor)}
 log_('CALCULO',etapa,basename(p));v<-fun();atomic(list(firma=firma,valor=v,fecha=Sys.time()),p);registro(etapa,p,'CALCULAR','No existe checkpoint compatible para esta firma');v
}
VERSIONES<-list(R=as.character(getRversion()),lightgbm=as.character(packageVersion('lightgbm')),data.table=as.character(packageVersion('data.table')))
RAW_HASH<-unname(tools::md5sum(RAW));writeLines(capture.output(sessionInfo()),file.path(RAIZ,'auditoria','SESSION_INFO.txt'))
atomic(PARAM,file.path(RAIZ,'PLAN_ACTUAL.rds'));atomic(VERSIONES,file.path(RAIZ,'auditoria','VERSIONES.rds'))
PRESTAMOS<-c('cprestamos_personales','mprestamos_personales')
SEMILLAS<-as.integer(PARAM$semillas)
# [Anotación · líneas 118–127] par_base(seed) devuelve los parámetros de LightGBM comunes a todos los modelos:
#   gbdt, objetivo binary, métrica average_precision, learning_rate 0,005, feature_fraction 0,50,
#   feature_fraction_bynode 0,20, max_bin 31, min_data_in_leaf 0, max_depth -1, lambda_l1 y lambda_l2 en 0, sin
#   bagging, scale_pos_weight 1 y modo determinístico. periodo() convierte AAAAMM en un número de mes
#   correlativo. rank_cero() reemplaza cada valor por su rango relativo dentro del grupo: el cero queda en 0,
#   los positivos entre 0 y 1 y los negativos entre -1 y 0; se aplica sólo cuando se pide ranking.
par_base<-function(seed){list(boosting='gbdt',objective='binary',metric='average_precision',feature_pre_filter=FALSE,
 first_metric_only=FALSE,boost_from_average=TRUE,force_row_wise=TRUE,deterministic=TRUE,verbosity=-1,
 seed=as.integer(seed),num_threads=PARAM$threads,max_depth=-1L,min_gain_to_split=0,lambda_l1=0,lambda_l2=0,max_bin=31L,
 bagging_fraction=1,bagging_freq=0L,pos_bagging_fraction=1,neg_bagging_fraction=1,is_unbalance=FALSE,scale_pos_weight=1,
 extra_trees=FALSE,min_data_in_leaf=0L,feature_fraction=.50,feature_fraction_bynode=.20,learning_rate=.005)}
periodo<-function(x) as.integer(x%/%100L*12L+x%%100L)
rank_cero<-function(x){z<-rep(NA_real_,length(x));z[which(x==0)]<-0;ip<-which(is.finite(x)&x>0);ineg<-which(is.finite(x)&x<0)
 if(length(ip))z[ip]<-frank(x[ip],ties.method='average')/length(ip)
 if(length(ineg))z[ineg]<- -frank(abs(x[ineg]),ties.method='average')/length(ineg)
 z}
# [Anotación · líneas 128–133] inventario_previo() lista los archivos csv, rds, txt, json, bin e ipynb que
#   existan en carpetas de corridas anteriores y en la salida, y guarda el listado en
#   auditoria/INVENTARIO_PREVIO.csv. Ninguna celda de esta notebook la invoca.
# Audito lo que existe, sin cargar modelos ni recalcular resultados anteriores.
inventario_previo<-function(){
 roots<-unique(c(Sys.getenv('DMEYF_ANTERIORES'),file.path(dirname(RAIZ),'HOJA_RUTA_AGOSTO'),RAIZ));roots<-roots[nzchar(roots)&dir.exists(roots)]
 out<-rbindlist(lapply(roots,function(root){ff<-list.files(root,recursive=TRUE,full.names=TRUE);ff<-ff[grepl('\\.(csv|rds|txt|json|bin|ipynb)$',ff)];if(!length(ff))return(NULL);fi<-file.info(ff);data.table(archivo=ff,bytes=fi$size,fecha=as.character(fi$mtime),estado='LOCALIZADO; compatibilidad pendiente, no equivale a reutilizado')}),fill=TRUE)
 csv(out,file.path(RAIZ,'auditoria','INVENTARIO_PREVIO.csv'));log_('Inventario',nrow(out),'archivos. No cambio ni borro artefactos anteriores.');out
}
# [Anotación · líneas 134–146] cargar_base() (inicio): lee el crudo con fread, exige que no haya pares
#   cliente-mes duplicados y que estén los meses 202103 a 202108, y guarda las dimensiones. Reconstruye la clase
#   a partir de la presencia mensual de cada cliente: CONTINUA para las filas de meses hasta 202106, BAJA+1 si
#   el cliente no tiene registro en el mes siguiente y BAJA+2 si lo tiene en el siguiente pero no en el
#   subsiguiente.
cargar_base<-function(){
 firma<-list(componente='base_DQ_target_v1',raw=RAW_HASH)
 cache('datos',firma,function(){
  d<-fread(RAW);stopifnot(all(c('numero_de_cliente','foto_mes')%in%names(d)),!anyNA(d$numero_de_cliente),!anyNA(d$foto_mes))
  if(anyDuplicated(d[,.(numero_de_cliente,foto_mes)]))stop('Duplicados cliente x mes')
  if(!all(202103L:202108L%in%unique(d$foto_mes)))stop('No están marzo-agosto de 2021')
  csv(data.table(filas=nrow(d),columnas=ncol(d),clientes=uniqueN(d$numero_de_cliente),md5=RAW_HASH),file.path(RAIZ,'auditoria','DIMENSIONES.csv'))
  setorder(d,numero_de_cliente,foto_mes)
  q<-d[,.(numero_de_cliente,foto_mes,p=periodo(foto_mes))];ult<-max(q$p)
  q[,c('p1','p2'):=shift(p,n=1:2,type='lead'),by=numero_de_cliente]
  q[,reconstruida:=fifelse(p<ult-1L,'CONTINUA',NA_character_)]
  q[p<ult & (is.na(p1)|p1>p+1L),reconstruida:='BAJA+1']
  q[p<ult-1L & !is.na(p1)&p1==p+1L & (is.na(p2)|p2>p+2L),reconstruida:='BAJA+2']
# [Anotación · líneas 147–157] Si el crudo trae clase_ternaria, tabula por mes la concordancia entre la clase
#   original y la reconstruida, guarda las discrepancias y detiene la ejecución si hay alguna; completa con la
#   reconstruida las filas sin clase original. Si no la trae, usa la reconstruida. Exige que no falten clases
#   hasta 202106 y guarda el conteo de clases por mes.
  if('clase_ternaria'%in%names(d)){
   q[,original:=as.character(d$clase_ternaria)]
   csv(q[, .N,by=.(foto_mes,original,reconstruida)],file.path(RAIZ,'auditoria','CONCORDANCIA_TARGET.csv'))
   ex<-q[!is.na(original)&!is.na(reconstruida)&original!=reconstruida]
   csv(ex,file.path(RAIZ,'auditoria','EXCEPCIONES_TARGET.csv'))
   if(nrow(ex))stop('Target original y reconstruido discrepan. Revisar EXCEPCIONES_TARGET.csv')
   d[,clase_ternaria:=as.character(clase_ternaria)]
   d[is.na(clase_ternaria),clase_ternaria:=q$reconstruida[is.na(d$clase_ternaria)]]
  }else{d[,clase_ternaria:=q$reconstruida];writeLines('Sin etiqueta original; uso la reconstrucción del notebook de cátedra, no una concordancia verificada.',file.path(RAIZ,'auditoria','FUENTE_TARGET.txt'))}
  if(anyNA(d[foto_mes<=202106L,clase_ternaria]))stop('Hay etiquetas faltantes en training/evaluación completos')
  csv(d[,.N,by=.(foto_mes,clase_ternaria)],file.path(RAIZ,'auditoria','CLASES_POR_MES.csv'))
# [Anotación · líneas 158–171] Guarda un conteo de ceros y faltantes de ccajas_depositos en 202105 y pasa esa
#   variable a NA en ese mes. Convierte las columnas no numéricas a códigos enteros según el orden de sus
#   valores (guarda el mapa) y reemplaza por NA los valores numéricos no finitos. Devuelve la tabla con la lista
#   de columnas categóricas como atributo; todo el resultado queda en caché.
  if(!'ccajas_depositos'%in%names(d))stop('No existe ccajas_depositos')
  csv(d[foto_mes==202105L,.(N=.N,ceros=sum(ccajas_depositos==0,na.rm=TRUE),missing=sum(is.na(ccajas_depositos)))],file.path(RAIZ,'auditoria','DQ_MAYO.csv'))
  d[foto_mes==202105L,ccajas_depositos:=NA_real_]
  campos<-setdiff(names(d),c('numero_de_cliente','foto_mes','clase_ternaria'))
  catvars<-campos[!vapply(d[,..campos],is.numeric,logical(1))]
  mapa<-list()
  for(v in catvars){lev<-sort(unique(as.character(d[[v]][!is.na(d[[v]])])));mapa[[v]]<-lev;set(d,j=v,value=match(as.character(d[[v]]),lev))}
  atomic(mapa,file.path(RAIZ,'auditoria','MAPA_CATEGORIAS.rds'))
  nums<-setdiff(campos,catvars)
  for(v in nums){ii<-which(!is.finite(d[[v]])&!is.na(d[[v]]));if(length(ii))set(d,ii,v,NA_real_)}
  attr(d,'categoricas')<-catvars
  d
 })
}
# [Anotación · líneas 172–185] preparar_features() (inicio): arma la firma de la representación (MD5 del
#   crudo, corrección de ccajas_depositos, orden de lags, campos a rankear, categóricas), crea una carpeta en
#   features/ con el hash de esa firma y determina qué meses de 202103 a 202108 todavía no tienen su bloque
#   guardado.
# Fijo la transformación sin usar el target; los percentiles se calculan por mes en toda la cartera.
preparar_features<-function(d,rankear=FALSE){
 campos<-setdiff(names(d),c('numero_de_cliente','foto_mes','clase_ternaria'));cats<-attr(d,'categoricas')
 ii_discovery<-which(d$foto_mes%in%PARAM$train)
 elegibles<-if(rankear)PARAM$rank_campos else character()
 if(rankear)stopifnot(length(elegibles)>0L,all(elegibles%in%campos),!any(elegibles%in%cats),all(vapply(d[,..elegibles],is.numeric,logical(1))))
 f<-list(componente=if(rankear)'historia_rank_montos_explicitos_v2' else 'historia_mensual_v1',raw=RAW_HASH,dq='ccajas_depositos_202105_NA',orden=PARAM$orden_lags,rank_cero=elegibles,categoricas=cats)
 k<-hash(f);rdir<-file.path(RAIZ,'features',k);dir.create(rdir,recursive=TRUE,showWarnings=FALSE)
 # Reutilizo cada bloque terminado aunque se haya interrumpido otro mes.
 meses<-202103L:202108L
 faltan<-meses[!file.exists(file.path(rdir,paste0(meses,'.rds')))]
 if(length(faltan)){
  log_('RECALCULO IMPRESCINDIBLE: bloques faltantes',paste(faltan,collapse=','),'representación',k)
  log_('Motivo: falta firma exacta de DQ, lags y ranking. Reutilizo base, bloques existentes y cálculos posteriores compatibles.')
# [Anotación · líneas 186–200] Para los meses faltantes: si se pidió ranking aplica rank_cero por mes a los
#   campos elegidos (en la entrega esa lista está vacía). Ubica para cada fila la fila del mismo cliente
#   exactamente 1 y 2 meses calendario antes (si el cliente no tiene registro de ese mes queda NA) y agrega, por
#   cada variable, el valor rezagado (_lag1, _lag2) y, para las numéricas, la diferencia entre el valor actual y
#   el rezagado (_delta_lag1, _delta_lag2). Guarda un .rds por mes.
  b<-copy(d)
  for(v in elegibles){set(b,j=v,value=as.numeric(b[[v]]));b[,(v):=rank_cero(get(v)),by=foto_mes]}
  pp<-periodo(b$foto_mes);ids<-b$numero_de_cliente
  # Localizo lag calendario exacto: no confundo una ausencia mensual con lag1.
  key<-paste(ids,pp,sep=':');lagidx<-lapply(seq_len(PARAM$orden_lags),function(l)match(paste(ids,pp-l,sep=':'),key))
  for(m in faltan){
   ix<-which(b$foto_mes==m);z<-copy(b[ix])
   for(l in seq_len(PARAM$orden_lags))for(v in campos){
    lagv<-b[[v]][lagidx[[l]][ix]];set(z,j=paste0(v,'_lag',l),value=lagv)
    if(!v%in%cats)set(z,j=paste0(v,'_delta_lag',l),value=b[[v]][ix]-lagv)
   }
   atomic(list(firma=f,mes=m,datos=z),file.path(rdir,paste0(m,'.rds')));log_('Bloque guardado',m,'features',ncol(z)-3L);rm(z);gc(FALSE)
  }
  rm(b);gc(FALSE)
 }
# [Anotación · líneas 201–207] Arma la lista ordenada de predictores: numero_de_cliente y foto_mes, las
#   variables originales y, para cada orden de lag, las columnas _lag y _delta_lag. Guarda el catálogo de
#   variables y la firma, y devuelve el identificador de la representación, su carpeta y la lista de campos.
 campos_todos<-c(campos,unlist(lapply(seq_len(PARAM$orden_lags),function(l)c(paste0(campos,'_lag',l),paste0(setdiff(campos,cats),'_delta_lag',l)))))
 if(PARAM$incluir_id_mes)campos_todos<-c('numero_de_cliente','foto_mes',campos_todos)
 cat<-data.table(variable=campos_todos,ranking=FALSE,temporal=grepl('_lag[12]$',campos_todos))
 cat[,origen:=sub('_(delta_)?lag[12]$','',variable)];cat[,ranking:=origen%in%elegibles]
 csv(cat,file.path(rdir,'CATALOGO_FEATURES.csv'));atomic(f,file.path(rdir,'FIRMA.rds'))
 list(id=k,dir=rdir,campos=campos_todos,rank=rankear,firma=f)
}
# [Anotación · líneas 208–216] leer_meses() lee y apila los bloques mensuales verificando firma y mes.
#   campos_receta() devuelve los predictores de una receta: quita la familia de préstamos personales (nivel,
#   lags y deltas) salvo que se pida conservarla, aplica una selección de variables si la receta la trae y quita
#   las familias listadas en excluir. curva() ordena por probabilidad descendente (desempate por ID) y acumula
#   la ganancia en millones: 1.072.500 por cada BAJA+2 y -27.500 por cada otro cliente.
leer_meses<-function(rep,meses){rbindlist(lapply(meses,function(m){z<-readRDS(file.path(rep$dir,paste0(m,'.rds')));stopifnot(identical(z$firma,rep$firma),identical(z$mes,as.integer(m)));z$datos}),use.names=TRUE)}
campos_receta<-function(rec,produccion=FALSE,prestamos=FALSE){
 c<-rec$rep$campos
 if(!prestamos)c<-c[!sub('_(delta_)?lag[12]$','',c)%in%PRESTAMOS]
 if(!is.null(rec$seleccion)){lo<-c[sub('_(delta_)?lag[12]$','',c)%in%PRESTAMOS];c<-intersect(c,rec$seleccion);if(prestamos)c<-unique(c(c,lo))}
 if(length(rec$excluir))c<-c[!sub('_(delta_)?lag[12]$','',c)%in%rec$excluir]
 c
}
curva<-function(ids,prob,y){stopifnot(length(ids)==length(prob),length(y)==length(ids),!anyNA(y),all(is.finite(prob)));ix<-order(-prob,ids);data.table(corte=seq_along(ix),ganancia=cumsum(ifelse(y[ix]=='BAJA+2',1072500,-27500))/1e6)}
# [Anotación · líneas 217–241] materializar() construye el dataset de LightGBM de una receta: meses
#   202103-202104 (histórico) o 202103-202106 (producción), etiqueta 1 para BAJA+1 y BAJA+2 y 0 para CONTINUA, o
#   las filas y etiquetas de un plan si la receta lo trae. Lee /proc/meminfo y se detiene si el tamaño estimado
#   de la matriz supera el 85 % de la memoria disponible. Construye el lgb.Dataset con max_bin 31, lo guarda en
#   binario en datasets/ y devuelve sus metadatos; si el archivo ya existe con la misma firma, lo reutiliza.
# Construyo el dataset LightGBM una vez por diseño; lo guardo en binario y libero la matriz densa.
materializar<-function(rec,prod=FALSE,prestamos=FALSE){
 meses<-if(prod)PARAM$train_final else PARAM$train
 if(!is.null(rec$planes)&&!is.null(rec$planes[[if(prod)'prod' else 'hist']]$meses))meses<-rec$planes[[if(prod)'prod' else 'hist']]$meses
 campos<-campos_receta(rec,prod,prestamos)
 firma<-list(componente='dataset_v1',raw=RAW_HASH,representacion=rec$rep$id,campos=campos,meses=meses,estrategia=rec$estrategia,umbral=rec$umbral,versiones=VERSIONES,
  plan=if(is.null(rec$planes))NULL else hash(rec$planes[[if(prod)'prod' else 'hist']]))
 key<-hash(firma);fp<-file.path(RAIZ,'datasets',paste0(key,'.rds'));bin<-file.path(RAIZ,'datasets',paste0(key,'.bin'))
 if(file.exists(fp)&&file.exists(bin)){z<-readRDS(fp);stopifnot(identical(z$firma,firma));registro('dataset',bin,'REUTILIZAR','Firma exacta');return(z$valor)}
 d<-leer_meses(rec$rep,meses);y<-as.integer(d$clase_ternaria%in%c('BAJA+1','BAJA+2'))
 if(!is.null(rec$planes)){
  plan<-rec$planes[[if(prod)'prod' else 'hist']]
  keys<-paste(d$numero_de_cliente,d$foto_mes);pi<-match(plan$key,keys);stopifnot(!anyNA(pi));d<-d[pi];y<-plan$y
 }
 stopifnot(length(campos)>0,nrow(d)>0,!anyNA(y),all(y%in%c(0,1)),uniqueN(y)==2L)
 # Calculo un límite conservador antes de materializar para evitar otra caída de RAM.
 mi<-readLines('/proc/meminfo');av<-as.numeric(sub('.*?([0-9]+).*','\\1',mi[grepl('^MemAvailable:',mi)]))*1024
 estimado<-as.double(nrow(d))*length(campos)*8*3
 if(length(av)&&is.finite(av)&&estimado>av*.85)stop('Memoria insuficiente para esta matriz: necesito margen aproximado ',round(estimado/2^30,1),' GiB. Checkpoints conservados.')
 log_('Dataset',rec$nombre,if(prod)'PRODUCCION' else 'HISTORICO','filas',nrow(d),'features',length(campos),'préstamos',prestamos)
 x<-data.matrix(d[,..campos]);dm<-lightgbm::lgb.Dataset(x,label=y,free_raw_data=TRUE,params=list(max_bin=31L,feature_pre_filter=FALSE));dm$construct()
 tmp<-paste0(bin,'.tmp_',Sys.getpid());lightgbm::lgb.Dataset.save(dm,tmp);if(!file.rename(tmp,bin))stop('No pude persistir dataset binario')
 meta<-list(bin=bin,campos=campos,n=nrow(d),y_hash=hash(y),filas_hash=hash(d[,.(numero_de_cliente,foto_mes)]),firma=firma,id=key)
 atomic(list(firma=firma,valor=meta),fp);rm(x,dm,d);gc(FALSE);meta
}
# [Anotación · líneas 242–265] fit_score() entrena un modelo para una receta, un juego de hiperparámetros y
#   una semilla, y predice 202106 (histórico) o 202108 (producción). Reutiliza modelo y puntajes guardados si la
#   firma coincide. Guarda el modelo en texto, la probabilidad y el puntaje crudo por cliente, la importancia de
#   variables y un registro; en el modo histórico calcula la curva de ganancia de junio y toma la ganancia en el
#   corte 11.500.
fit_score<-function(rec,hp,seed,prod=FALSE,prestamos=FALSE){
 meta<-materializar(rec,prod,prestamos);mes<-if(prod)202108L else 202106L;p<-modifyList(par_base(seed),hp)
 sig<-list(componente='fit_v1',dataset=meta$firma,pars=p,seed=seed,score_mes=mes,score_rep=rec$rep$id)
 key<-hash(sig);mp<-file.path(RAIZ,'modelos',paste0(key,'.txt'));sp<-file.path(RAIZ,'scores',paste0(key,'.rds'))
 if(file.exists(sp)&&file.exists(mp)){z<-readRDS(sp);stopifnot(identical(z$firma,sig));registro('modelo_scores',sp,'REUTILIZAR','Firma exacta');return(z$valor)}
 # Dejo anotado: Si el modelo terminó pero se cortó antes de guardar scores, lo reutilizo.
 mf<-paste0(mp,'.firma.rds');m<-NULL
 if(file.exists(mp)&&file.exists(mf)){stopifnot(identical(readRDS(mf),sig));m<-lightgbm::lgb.load(mp);log_('RECUPERO modelo terminado',key)}
 if(is.null(m)){
  log_('ENTRENO',rec$nombre,seed,'mes',mes,'iteraciones',p$num_iterations)
  dt<-lightgbm::lgb.Dataset(meta$bin,params=list(max_bin=31L,feature_pre_filter=FALSE))
  m<-lightgbm::lgb.train(params=p,data=dt,nrounds=p$num_iterations)
  tmp<-paste0(mp,'.tmp');lightgbm::lgb.save(m,tmp);if(!file.rename(tmp,mp))stop('No pude guardar modelo');atomic(sig,mf);rm(dt);gc(FALSE)
 }
 df<-leer_meses(rec$rep,mes);xx<-data.matrix(df[,meta$campos,with=FALSE]);pr<-predict(m,xx);raw<-predict(m,xx,type='raw')
 stopifnot(length(pr)==nrow(df),all(is.finite(pr)),all(is.finite(raw)))
 out<-list(id=key,receta=rec$nombre,seed=seed,mes=mes,prestamos=prestamos,hp=hp,campos=meta$campos,modelo=mp,
 scores=data.table(numero_de_cliente=df$numero_de_cliente,foto_mes=mes,clase_ternaria=df$clase_ternaria,prob=pr,raw=raw),ganancia=NA_real_)
 im<-as.data.table(lightgbm::lgb.importance(m));im<-merge(data.table(Feature=meta$campos),im,by='Feature',all.x=TRUE);csv(im,file.path(RAIZ,'modelos',paste0(key,'_importancia.csv')))
 if(!prod){cv<-curva(df$numero_de_cliente,pr,df$clase_ternaria);out$ganancia<-cv[corte==PARAM$corte,ganancia];csv(cv,file.path(RAIZ,'resultados',paste0('CURVA_',key,'.csv')))}
 atomic(list(firma=sig,valor=out,fecha=Sys.time()),sp)
 rp<-data.table(id=key,receta=rec$nombre,semilla=seed,mes=mes,prestamos=prestamos,N_train=meta$n,features=length(meta$campos),ganancia=out$ganancia,hp=toJSON(hp,auto_unbox=TRUE),modelo=mp,scores=sp)
 csv(rp,file.path(RAIZ,'modelos',paste0(key,'_registro.csv')));log_('GUARDADO',rec$nombre,seed,if(prod)'agosto' else paste('ganancia',out$ganancia));rm(m,df,xx);gc(FALSE);out
}
# [Anotación · líneas 266–300] bayes() ejecuta la optimización bayesiana con mlrMBO sobre el dataset histórico
#   (202103-202104, sin préstamos personales). Busca num_iterations (512-4096), num_leaves (8-256) y el
#   logaritmo en base 10 de min_sum_hessian_in_leaf (-3 a 1); el objetivo a maximizar es la ganancia de junio en
#   el corte 11.500 con la semilla 100613. Usa 4 puntos de diseño inicial y 8 iteraciones con criterio de mejora
#   esperada y un modelo kriging (regr.km, covarianza Matérn 3/2). Guarda cada evaluación en HISTORIAL, ordena
#   por ganancia descendente y devuelve la primera configuración; si existe TERMINADO.rds con la misma firma
#   devuelve ese resultado sin recalcular.
# Mantengo mlrMBO/DiceKriging, motor de la notebook de cátedra.
# Dejo anotado: Cada evaluación tiene caché propio: incluso si el estado del optimizador queda atrasado no reentreno el mismo punto.
bayes<-function(rec){
 meta<-materializar(rec,FALSE,FALSE)
 sig<-list(componente='bo_catedra_v1',dataset=meta$firma,base=par_base(PARAM$semilla),limites=PARAM$bounds,presupuesto=PARAM$bo_evaluaciones,corte=PARAM$corte,seed=PARAM$semilla,
  versiones=c(VERSIONES,list(mlrMBO=as.character(packageVersion('mlrMBO')),DiceKriging=as.character(packageVersion('DiceKriging')))))
 bd<-file.path(RAIZ,'bo',hash(sig));dir.create(bd,recursive=TRUE,showWarnings=FALSE);terminado<-file.path(bd,'TERMINADO.rds');histp<-file.path(bd,'HISTORIAL.rds');estado<-file.path(bd,'ESTADO.RData')
 if(file.exists(terminado)){z<-readRDS(terminado);stopifnot(identical(z$firma,sig));log_('BO RECUPERADA',rec$nombre);return(z$valor)}
 atomic(sig,file.path(bd,'FIRMA.rds'))
 objetivo<-function(x){
  hp<-list(num_iterations=as.integer(x$num_iterations),num_leaves=as.integer(x$num_leaves),min_sum_hessian_in_leaf=10^x$log10_min_sum_hessian_in_leaf)
  r<-fit_score(rec,hp,PARAM$semilla);g<-r$ganancia;if(!is.finite(g))stop('Ganancia no finita; no agrego evaluación inválida')
  h<-if(file.exists(histp))readRDS(histp) else data.table()
  if(!nrow(h)||!r$id%in%h$modelo){h<-rbindlist(list(h,data.table(evaluacion=nrow(h)+1L,num_iterations=hp$num_iterations,num_leaves=hp$num_leaves,log10_min_sum_hessian_in_leaf=x$log10_min_sum_hessian_in_leaf,min_sum_hessian_in_leaf=hp$min_sum_hessian_in_leaf,ganancia=g,modelo=r$id)),fill=TRUE);atomic(h,histp);csv(h,file.path(bd,'HISTORIAL.csv'))}
  log_('BO',rec$nombre,'evaluaciones únicas',nrow(h),'/',PARAM$bo_evaluaciones,'ganancia',g);g
 }
 ps<-ParamHelpers::makeParamSet(ParamHelpers::makeIntegerParam('num_iterations',lower=PARAM$bounds$iter[1],upper=PARAM$bounds$iter[2]),
  ParamHelpers::makeIntegerParam('num_leaves',lower=PARAM$bounds$leaves[1],upper=PARAM$bounds$leaves[2]),
  ParamHelpers::makeNumericParam('log10_min_sum_hessian_in_leaf',lower=PARAM$bounds$logh[1],upper=PARAM$bounds$logh[2]))
 obj<-smoof::makeSingleObjectiveFunction(name=rec$nombre,fn=objetivo,minimize=FALSE,noisy=TRUE,par.set=ps,has.simple.signature=FALSE)
 mlr::configureMlr(show.learner.output=FALSE)
 ctrl<-mlrMBO::makeMBOControl(save.on.disk.at.time=0,save.file.path=estado)
 ctrl<-mlrMBO::setMBOControlTermination(ctrl,iters=PARAM$bo_evaluaciones-PARAM$bo_iniciales)
 ctrl<-mlrMBO::setMBOControlInfill(ctrl,crit=mlrMBO::makeMBOInfillCritEI())
 learner<-mlr::makeLearner('regr.km',predict.type='se',covtype='matern3_2',control=list(trace=FALSE),nugget.estim=TRUE)
 set.seed(PARAM$semilla,kind="L'Ecuyer-CMRG")
 # Dejo anotado: El resultado final se decide con ganancias monetarias originales, nunca con scores estandarizados.
 if(file.exists(histp)&&nrow(readRDS(histp))>=PARAM$bo_evaluaciones){h<-readRDS(histp)}else{
  tryCatch({if(file.exists(estado)){mlrMBO::mboContinue(estado)}else{design<-ParamHelpers::generateDesign(n=PARAM$bo_iniciales,par.set=ps);mlrMBO::mbo(obj,design=design,learner=learner,control=ctrl)}} ,error=function(e){log_('BO interrumpida; historial/modelos conservados:',conditionMessage(e));stop('No cambio el método ni vuelvo a entrenar puntos guardados. Reejecutar celda 08 retoma; revisar el error anterior.')})
  h<-readRDS(histp)
 }
 setorder(h,-ganancia,modelo);h[,orden:=.I];csv(h,file.path(bd,'ORDENADOS.csv'))
 opt<-lapply(seq_len(min(PARAM$top_configuraciones,nrow(h))),function(i)as.list(h[i,.(num_iterations,num_leaves,min_sum_hessian_in_leaf)]))
 res<-list(nombre=rec$nombre,historial=h,optimos=opt,directorio=bd);atomic(list(firma=sig,valor=res),terminado);res
}
# [Anotación · líneas 301–316] canarios() agrega a los predictores de 202103-202104 un 20 % de columnas de
#   números al azar (canaritos), entrena un LightGBM con PARAM$hp_seleccion, ordena todas las variables por
#   ganancia y conserva las variables reales ubicadas antes de la posición media de los canaritos más un
#   múltiplo de su desvío. Ninguna celda de esta notebook la invoca y PARAM no define hp_seleccion.
# Dejo anotado: Canaritos: incluyo TODAS las variables, incluso las de importancia cero.
canarios<-function(rec,multiplo){
 f<-list(componente='canarios_v1',rep=rec$rep$id,train=PARAM$train,seed=PARAM$semilla,fraccion=.20,hp=PARAM$hp_seleccion)
 resultado<-cache('seleccion',f,function(){
  d<-leer_meses(rec$rep,PARAM$train);cam<-campos_receta(rec);x<-data.matrix(d[,..cam]);set.seed(PARAM$semilla)
  ncan<-ceiling(ncol(x)*.20);nom<-paste0('canarito_',seq_len(ncan));x<-cbind(x,matrix(runif(nrow(x)*ncan),nrow=nrow(x),dimnames=list(NULL,nom)))
  y<-as.integer(d$clase_ternaria%in%c('BAJA+1','BAJA+2'));dt<-lightgbm::lgb.Dataset(x,label=y,free_raw_data=TRUE)
  m<-lightgbm::lgb.train(params=modifyList(par_base(PARAM$semilla),PARAM$hp_seleccion),data=dt,nrounds=PARAM$hp_seleccion$num_iterations)
  imp<-merge(data.table(Feature=colnames(x)),as.data.table(lightgbm::lgb.importance(m)),by='Feature',all.x=TRUE);imp[is.na(Gain),Gain:=0]
  imp[,es_canarito:=Feature%in%nom];set.seed(PARAM$semilla);imp[,desempate:=runif(.N)];setorder(imp,-Gain,desempate);imp[,id:=.I]
  list(imp=imp,canaritos=ncan)
 })
 imp<-copy(resultado$imp);corte<-mean(imp[es_canarito==TRUE,id])+multiplo*sd(imp[es_canarito==TRUE,id]);imp[,conservar:=!es_canarito&id<corte]
 csv(imp,file.path(RAIZ,'seleccion',paste0('CANARITOS_',hash(f),'_SD',multiplo,'.csv')))
 list(campos=imp[conservar==TRUE,Feature],corte=corte,canaritos=resultado$canaritos)
}
# [Anotación · líneas 317–340] planes_negativos() parte al azar las filas de entrenamiento en 70 % y 30 %
#   dentro de cada mes y clase; si recibe un umbral entrena un modelo auxiliar con el 30 % (2180 iteraciones, 30
#   hojas), puntúa el 70 % y conserva los positivos y los negativos con probabilidad auxiliar menor al umbral.
#   Devuelve las claves cliente-mes y las etiquetas del plan resultante. Ninguna celda de esta notebook la
#   invoca.
# Dejo anotado: Filtro opcional, separado del experimento que continúa en Colab.
# Mantengo 30/70 por filas, auxiliares fuera del 70%, positivos conservados dentro del 70%.
planes_negativos<-function(rec,umbral=NULL){
 auxp<-modifyList(par_base(PARAM$semilla),list(feature_fraction_bynode=1,num_iterations=2180L,num_leaves=30L,min_sum_hessian_in_leaf=.1141634103))
 lapply(setNames(c(FALSE,TRUE),c('hist','prod')),function(prod){
  meses<-if(prod)PARAM$train_final else PARAM$train
  cache('seleccion',list(componente='filtro30_v1',rep=rec$rep$id,meses=meses,umbral=umbral,aux=auxp,seed=PARAM$semilla),function(){
   d<-leer_meses(rec$rep,meses);d[,y:=as.integer(clase_ternaria%in%c('BAJA+1','BAJA+2'))];set.seed(PARAM$semilla,kind="L'Ecuyer-CMRG")
   d[,fold:=sample(rep(c(rep(1L,7),rep(2L,3)),length.out=.N)),by=.(foto_mes,clase_ternaria)]
   i30<-which(d$fold==2L);i70<-which(d$fold==1L);stopifnot(length(i30)>0L,length(i70)>0L,length(intersect(i30,i70))==0L)
   pro<-rep(NA_real_,length(i70))
   if(!is.null(umbral)){
    pro<-cache('seleccion',list(componente='aux30_pred_v1',rep=rec$rep$id,meses=meses,aux=auxp,i30=hash(i30),i70=hash(i70)),function(){
     campos<-campos_receta(rec);dt<-lightgbm::lgb.Dataset(data.matrix(d[i30,..campos]),label=d$y[i30],free_raw_data=TRUE)
     m<-lightgbm::lgb.train(params=auxp,data=dt,nrounds=2180L);p<-predict(m,data.matrix(d[i70,..campos]));rm(dt,m);gc(FALSE);p
    })
   }
   keep<-if(is.null(umbral))rep(TRUE,length(i70)) else d$y[i70]==1L|pro<umbral
   aud<-data.table(numero_de_cliente=d$numero_de_cliente[i70],foto_mes=d$foto_mes[i70],y=d$y[i70],prob_aux=pro,conservar=keep)
   csv(aud,file.path(RAIZ,'seleccion',paste0('FILTRO_',if(prod)'prod' else 'hist','_',if(is.null(umbral))'control' else umbral,'.csv')))
   list(key=paste(d$numero_de_cliente[i70][keep],d$foto_mes[i70][keep]),y=d$y[i70][keep])
  })
 })
}
# [Anotación · líneas 341–354] planes_pseudo() entrena un modelo con las clases reales, predice los meses sin
#   clase completa (202105-202106 en histórico, 202107-202108 en producción), asigna etiqueta artificial 1 a las
#   filas con probabilidad mayor o igual a PARAM$pseudo_umbral y devuelve un plan que une filas reales y
#   artificiales. Ninguna celda de esta notebook la invoca.
# Dejo anotado: Pseudoetiquetas: mantengo el target verdadero separado; las etiquetas auxiliares nunca son predictors.
planes_pseudo<-function(rec,hp_docente){
 lapply(setNames(c(FALSE,TRUE),c('hist','prod')),function(prod){
  reales<-if(prod)PARAM$train_final else PARAM$train;artificiales<-if(prod)c(202107L,202108L) else c(202105L,202106L)
  cache('seleccion',list(componente='pseudo_v1',rep=rec$rep$id,reales=reales,artificiales=artificiales,hp=hp_docente,corte=PARAM$pseudo_umbral,seed=PARAM$semilla),function(){
   meta<-materializar(rec,prod,FALSE);dt<-lightgbm::lgb.Dataset(meta$bin,params=list(max_bin=31L,feature_pre_filter=FALSE));p<-modifyList(par_base(PARAM$semilla),hp_docente)
   m<-lightgbm::lgb.train(params=p,data=dt,nrounds=p$num_iterations)
   a<-leer_meses(rec$rep,artificiales);pr<-predict(m,data.matrix(a[,meta$campos,with=FALSE]));yr<-as.integer(pr>=PARAM$pseudo_umbral)
   r<-leer_meses(rec$rep,reales)
   csv(data.table(numero_de_cliente=a$numero_de_cliente,foto_mes=a$foto_mes,prob_docente=pr,etiqueta_artificial=yr),file.path(RAIZ,'seleccion',paste0('PSEUDO_',if(prod)'prod' else 'hist','_',rec$rep$id,'.csv')))
   list(key=c(paste(r$numero_de_cliente,r$foto_mes),paste(a$numero_de_cliente,a$foto_mes)),y=c(as.integer(r$clase_ternaria%in%c('BAJA+1','BAJA+2')),yr),meses=c(reales,artificiales))
  })
 })
}
# [Anotación · líneas 355–376] resumir_ensemble() promedia entre modelos, cliente por cliente, el puntaje
#   crudo y la probabilidad (dos modos). Para junio calcula la curva de ganancia del promedio, la ganancia en el
#   corte 11.500, un gráfico entre 8.000 y 15.000 clientes y una tabla de cortes cada 250 con la ganancia media
#   en una ventana de ±250.
resumir_ensemble<-function(resultados,nombre){
 stopifnot(length(resultados)>0L)
 ref<-resultados[[1L]]$scores;ids<-ref$numero_de_cliente
 for(z in resultados)stopifnot(identical(z$scores$numero_de_cliente,ids),identical(z$scores$foto_mes,ref$foto_mes))
 modos<-c('raw','prob');out<-list()
 for(modo in modos){
  s<-Reduce('+',lapply(resultados,function(z)z$scores[[modo]]))/length(resultados)
  tab<-copy(ref[,.(numero_de_cliente,foto_mes,clase_ternaria)]);tab[,score:=s]
  id<-hash(list(modelos=vapply(resultados,`[[`,character(1),'id'),modo=modo));dest<-file.path(RAIZ,'scores',paste0('ENS_',id,'.rds'));atomic(list(nombre=nombre,modo=modo,modelos=vapply(resultados,`[[`,character(1),'id'),tabla=tab),dest)
  gan<-NA_real_
  if(unique(tab$foto_mes)==202106L){
   cv<-curva(ids,s,tab$clase_ternaria);gan<-cv[corte==PARAM$corte,ganancia];csv(cv,file.path(RAIZ,'resultados',paste0('CURVA_ENS_',id,'.csv')))
   png(file.path(RAIZ,'figuras',paste0('GANANCIA_',id,'.png')),width=1300,height=750)
   plot(cv$corte,cv$ganancia,type='l',xlim=c(8000,15000),xlab='Clientes contactados',ylab='Ganancia junio (millones)',main=paste(nombre,modo));abline(v=PARAM$corte,lty=2);dev.off()
   cortes<-cv[corte%in%seq(8000L,15000L,250L)]
   cortes[,ganancia_media_vecindad:=vapply(corte,function(k)mean(cv[corte>=k-250L & corte<=k+250L,ganancia]),numeric(1))]
   csv(cortes,file.path(RAIZ,'resultados',paste0('MESETA_',id,'.csv')))
  }
  out[[modo]]<-list(id=id,nombre=nombre,modo=modo,tabla=tab,ganancia=gan,modelos=vapply(resultados,`[[`,character(1),'id'))
 }
 out
}
# [Anotación · líneas 377–391] confirmar() entrena la configuración devuelta por la búsqueda con todas las
#   semillas de PARAM en modo histórico, resume media y desvío de las ganancias individuales junto con la
#   ganancia de los promedios, y grafica la curva de cada semilla y la del promedio.
confirmar<-function(rec,bo){
 res<-list()
 for(j in seq_along(bo$optimos)){
  hp<-bo$optimos[[j]];xs<-lapply(SEMILLAS,function(s)fit_score(rec,hp,s))
  en<-resumir_ensemble(xs,paste0(rec$nombre,'_HP',j))
  resumen<-data.table(receta=rec$nombre,configuracion=j,n_semillas=length(xs),media=mean(vapply(xs,`[[`,numeric(1),'ganancia')),sd=sd(vapply(xs,`[[`,numeric(1),'ganancia')),ensemble_raw=en$raw$ganancia,ensemble_prob=en$prob$ganancia)
  csv(resumen,file.path(RAIZ,'resultados',paste0('CONF_',rec$nombre,'_',j,'.csv')))
  # Dejo anotado: Gráfico conjunto: ganancias individuales y ganancia del promedio de predicciones.
  png(file.path(RAIZ,'figuras',paste0('SEMILLAS_',rec$nombre,'_',j,'.png')),width=1300,height=750)
  cr<-curva(en$raw$tabla$numero_de_cliente,en$raw$tabla$score,en$raw$tabla$clase_ternaria);plot(cr$corte,cr$ganancia,type='n',xlim=c(8000,15000),xlab='Contactos',ylab='Ganancia junio (millones)',main=paste(rec$nombre,'configuración',j))
  for(x in xs){ci<-curva(x$scores$numero_de_cliente,x$scores$prob,x$scores$clase_ternaria);lines(ci$corte,ci$ganancia,col=adjustcolor('grey40',.4))};lines(cr$corte,cr$ganancia,col='blue',lwd=2);dev.off()
  res[[as.character(j)]]<-list(receta=rec$nombre,hp=hp,individuales=xs,ensemble=en,resumen=resumen)
 }
 res
}
# [Anotación · líneas 392–403] submit() ordena los puntajes de 202108 de mayor a menor (desempate por ID),
#   guarda la tabla ordenada y escribe un archivo con los primeros IDs hasta el corte, uno por línea,
#   verificando que lo escrito coincida con lo calculado. La ruta final no usa esta función: escribe su archivo
#   en la celda 11.
submit<-function(en,etiqueta,corte=PARAM$corte){
 d<-copy(en$tabla);stopifnot(all(d$foto_mes==202108L),nrow(d)>=corte,all(is.finite(d$score)),!anyDuplicated(d$numero_de_cliente))
 setorder(d,-score,numero_de_cliente);d[,ranking:=.I]
 csv(d,file.path(RAIZ,'resultados',paste0('SCORES_AGOSTO_',etiqueta,'.csv')))
 dest<-file.path(RAIZ,'submits',paste0('submit_',etiqueta,'_',corte,'.csv'))
 # Dejo anotado: Formateo IDs sin convertirlos a integer de 32 bits ni notación científica.
 ids<-format(d$numero_de_cliente[seq_len(corte)],scientific=FALSE,trim=TRUE,digits=22)
 stopifnot(length(ids)==corte,!anyDuplicated(ids),all(grepl('^[0-9]+$',ids)))
 writeLines(ids,paste0(dest,'.tmp'));if(!file.rename(paste0(dest,'.tmp'),dest))stop('No pude guardar submit')
 stopifnot(identical(readLines(dest),ids));log_('SUBMIT VERIFICADO',dest)
 data.table(nombre=etiqueta,corte=corte,archivo=dest,ensemble=en$id,public_gain=NA_real_,estado='NO ENVIADO; evaluación externa pendiente')
}
# [Anotación · líneas 404–416] ablaciones() reentrena la receta quitando de a una familia de variables (nivel,
#   lags y deltas), mide la diferencia de ganancia de junio contra la receta completa y devuelve recetas
#   candidatas sin las familias cuya exclusión aumentó la ganancia (hasta PARAM$ablaciones_top). Ninguna celda
#   de esta notebook la invoca.
# Dejo anotado: Reviso todas las variables originales mediante ablaciones de su familia (nivel + históricos).
# Primero filtro con parámetros fijos; después ajusto sólo las mejores, sin confundir ambas pruebas.
ablaciones<-function(rec,bo){
 hp<-bo$optimos[[1]];base<-fit_score(rec,hp,PARAM$semilla)$ganancia
 variables<-sort(unique(sub('_(delta_)?lag[12]$','',campos_receta(rec))))
 tab<-rbindlist(lapply(variables,function(v){rr<-rec;rr$nombre<-paste0('DROP_',v);rr$excluir<-v;x<-fit_score(rr,hp,PARAM$semilla);data.table(variable=v,ganancia=x$ganancia,delta=x$ganancia-base,modelo=x$id)}))
 setorder(tab,-delta,variable);csv(tab,file.path(RAIZ,'resultados',paste0('ABLACIONES_',rec$nombre,'.csv')))
 mejores<-tab[delta>0,head(variable,PARAM$ablaciones_top)]
 candidatos<-list()
 for(v in mejores){rr<-rec;rr$nombre<-paste0(rec$nombre,'_SIN_',v);rr$excluir<-v;candidatos[[rr$nombre]]<-rr}
 if(length(mejores)>1L){rr<-rec;rr$nombre<-paste0(rec$nombre,'_SIN_CONJUNTO');rr$excluir<-mejores;candidatos[[rr$nombre]]<-rr}
 candidatos
}
# [Anotación · líneas 417–425] auditar_drift() calcula por variable y por mes cantidad de filas, proporción de
#   faltantes y de ceros, cuartiles y cantidad de valores únicos, y lo guarda en CSV; ninguna celda de esta
#   notebook la invoca. La última línea comprueba rank_cero con un vector de prueba.
# Audito cambio de distribución de TODOS los campos numéricos, sin usar la baja como filtro.
auditar_drift<-function(d){
 vars<-setdiff(names(d),c('numero_de_cliente','foto_mes','clase_ternaria'));out<-rbindlist(lapply(vars,function(v){d[,{
  x<-get(v);q<-if(all(is.na(x)))rep(NA_real_,3) else as.numeric(quantile(x,c(.25,.50,.75),na.rm=TRUE));list(n=.N,missing=mean(is.na(x)),ceros=mean(x==0,na.rm=TRUE),p25=q[1],mediana=q[2],p75=q[3],unicos=uniqueN(x,na.rm=TRUE))
 },by=foto_mes][,variable:=v]}))
 csv(out,file.path(RAIZ,'auditoria','DISTRIBUCIONES_TODAS_VARIABLES.csv'));out
}
stopifnot(identical(rank_cero(c(NA,0,-20,-10,10,20,20)),c(NA_real_,0,-1,-.5,1/3,5/6,5/6)))

# [Anotación · líneas 426–454] Celdas 8 y 9. Ejecuta cargar_base() y preparar_features() sin ranking y exige
#   que el identificador de la representación sea c9527308…. Lee de procedencia_bo/52fc1b5d…/TERMINADO.rds la
#   primera configuración de la optimización de origen y comprueba que sea 1907 iteraciones, 77 hojas y
#   min_sum_hessian_in_leaf 2,83699883991516. Define la receta ORIGINAL_LAG2. Sólo si bo_origen es TRUE vuelve a
#   ejecutar bayes() y guarda el resultado en BO_ORIGEN_REEJECUTADA.rds.
#%% celda 8 [texto]
### 2.2 Data Quality, target e historia

Reconstruyo BAJA+1/BAJA+2 desde la presencia mensual, corrijo ccajas_depositos de mayo y calculo lags/deltas calendario de orden 1 y 2. No uso etiquetas de agosto para entrenar.

#%% celda 9 [código]
# Reconstruyo el target, corrijo mayo y calculo la historia calendario exacta.
D <- cargar_base()
REP <- preparar_features(D,FALSE)
stopifnot(REP$id=='c9527308c55d2d52c924dc64ce5594db3d240bce96c8a548c6f48a06239c71c8')
rm(D)
gc(full=TRUE)
# Dejo anotado: Recupero la procedencia de los HP sin hacer pasar una BO nueva por la original.
ORIGEN <- readRDS(file.path(CARPETA,'procedencia_bo',
 '52fc1b5d908fb495ce06d1ed3038defbaf9a2609d2ea0bc80904d2ba8b58c6ed',
 'TERMINADO.rds'))
HP_FINAL <- ORIGEN$valor$optimos[[1L]]
stopifnot(HP_FINAL$num_iterations==1907L,HP_FINAL$num_leaves==77L,
 abs(HP_FINAL$min_sum_hessian_in_leaf-2.83699883991516)<1e-12)
REC_CONTROL <- list(nombre='ORIGINAL_LAG2',rep=REP,estrategia='COMPLETO',
 umbral=NULL,seleccion=NULL,excluir=character(),planes=NULL)
# Dejo anotado: Si activo la BO de origen, la ejecuto en otra raíz sin reutilizar su resultado.
if(SW$bo_origen) {
 for(paquete in c('mlrMBO','mlr','ParamHelpers','smoof','DiceKriging'))
  if(!requireNamespace(paquete,quietly=TRUE))stop('Debo instalar ',paquete)
 b <- bayes(REC_CONTROL)
 atomic(b,file.path(RAIZ,'BO_ORIGEN_REEJECUTADA.rds'))
}

# [Anotación · líneas 455–482] Celdas 10 y 11 (inicio). Con reproducir_final en TRUE lee los bloques de
#   202103-202106 para entrenar y el de 202108 para predecir. Parte de los 752 campos de la receta sin
#   préstamos, agrega las 10 columnas de préstamos personales y quita las 10 de Visa_fultimo_cierre y
#   Master_fultimo_cierre (nivel, lags y deltas): quedan 752 predictores, cuyo orden debe coincidir con
#   referencia/FEATURES.csv. Exige 654.066 filas de entrenamiento y 164.647 clientes en 202108. Arma las
#   matrices, pasa los no finitos a NA, define la etiqueta 1 = BAJA+1 o BAJA+2 y construye el lgb.Dataset con
#   max_bin 31.
#%% celda 10 [texto]
### 2.3 Mi entrenamiento final y ensamble

Entreno marzo–junio sin undersampling. Restauro préstamos y sus históricos; retiro fechas de cierre y sus históricos. Conservo Visa_status y Master_status. Promedio probabilidades por cliente y después aplico el corte.

#%% celda 11 [código]
# Entreno la receta que elegí sin modificar el orden de las columnas.
if(SW$reproducir_final) {
 out <- file.path(RAIZ,'final');dir.create(out,recursive=TRUE,showWarnings=FALSE)
 tr <- leer_meses(REP,PARAM$train_final)
 va <- leer_meses(REP,202108L)
 campos_h <- campos_receta(REC_CONTROL,FALSE,FALSE)
 prestamos <- grep('^(cprestamos_personales|mprestamos_personales)($|_)',names(tr),value=TRUE)
 cierres <- grep('^(Visa_fultimo_cierre|Master_fultimo_cierre)($|_)',campos_h,value=TRUE)
 campos <- setdiff(unique(c(campos_h,prestamos)),cierres)
 referencia <- fread(file.path(CARPETA,'referencia','FEATURES.csv'))$campo
 stopifnot(length(campos_h)==752L,length(prestamos)==10L,length(cierres)==10L,
  length(campos)==752L,identical(campos,referencia),nrow(tr)==654066L,
  nrow(va)==164647L,!anyNA(tr$clase_ternaria),!anyDuplicated(va$numero_de_cliente))
 setDTthreads(1L)
 x <- data.matrix(tr[,..campos]);xv <- data.matrix(va[,..campos])
 x[!is.finite(x)] <- NA_real_;xv[!is.finite(xv)] <- NA_real_
 y <- as.integer(tr$clase_ternaria%in%c('BAJA+1','BAJA+2'))
 ids <- va$numero_de_cliente
 rm(tr,va);gc(FALSE)
 ds <- lgb.Dataset(x,label=y,params=list(max_bin=31L,
  feature_pre_filter=FALSE,num_threads=6L))
 rm(x);gc(FALSE)
# [Anotación · líneas 483–505] Para cada una de las 10 semillas combina par_base con los hiperparámetros
#   leídos, entrena 1907 iteraciones sobre el mismo dataset, predice 202108 y guarda el modelo
#   (MODELO_<semilla>.txt) y las probabilidades (SCORES_<semilla>.rds). Si ya existen los puntajes de una
#   semilla con la misma firma, los reutiliza en lugar de entrenar.
 P <- matrix(NA_real_,length(ids),length(PARAM$semillas))
 for(j in seq_along(PARAM$semillas)) {
  s <- PARAM$semillas[j]
  pars <- modifyList(par_base(s),HP_FINAL)
  firma <- list(raw=RAW_HASH,representacion=REP$id,campos=campos,
   meses=PARAM$train_final,seed=s,pars=pars,versiones=VERSIONES)
  sp <- file.path(out,paste0('SCORES_',s,'.rds'))
  mp <- file.path(out,paste0('MODELO_',s,'.txt'))
  if(file.exists(sp)) {
   anterior <- readRDS(sp)
   stopifnot(identical(anterior$firma,firma),identical(anterior$ids,ids),file.exists(mp))
   pr <- anterior$prob
  } else {
   log_('ENTRENO FINAL',j,'/',length(PARAM$semillas),'semilla',s)
   m <- lgb.train(params=pars,data=ds,nrounds=HP_FINAL$num_iterations)
   pr <- predict(m,xv,params=list(num_threads=6L))
   stopifnot(length(pr)==length(ids),all(is.finite(pr)))
   lgb.save(m,mp)
   atomic(list(firma=firma,ids=ids,prob=pr),sp)
   rm(m);gc(FALSE)
  }
  P[,j] <- pr
 }
# [Anotación · líneas 506–525] Promedia las 10 probabilidades por cliente, ordena de mayor a menor con
#   desempate por ID creciente y toma los primeros 10.375. Escribe los IDs, uno por línea y sin encabezado, en
#   final/SINCIERRES_PROB10_K10375.csv; guarda las probabilidades promedio de todos los clientes y un resumen
#   del ensamble. Calcula el SHA256 del archivo y detiene la ejecución si difiere del esperado; si coincide
#   escribe VERIFICACION_FINAL.txt.
 # Promedio las probabilidades antes de decidir a quién contacto.
 prob <- rowMeans(P)
 ix <- order(-prob,ids)[seq_len(CORTE_FINAL)]
 elegido <- ids[ix]
 stopifnot(length(elegido)==10375L,!anyDuplicated(elegido))
 archivo <- file.path(out,'SINCIERRES_PROB10_K10375.csv')
 writeLines(format(elegido,scientific=FALSE,trim=TRUE),archivo)
 sha <- digest(file=archivo,algo='sha256')
 fwrite(data.table(numero_de_cliente=ids,prob=prob),file.path(out,'PROBABILIDADES_AGOSTO.csv'))
 atomic(list(ids=ids,prob=prob,campos=campos,hp=HP_FINAL,
  semillas=PARAM$semillas,sha256=sha),file.path(out,'ENSAMBLE_FINAL.rds'))
 # Dejo anotado: Detengo mi entrega si no reproduje exactamente el archivo enviado.
 if(sha!=SHA_FINAL)stop('CSV distinto al entregado. SHA256 obtenido: ',sha,
  '. No debo subir esta reproducción sin revisar la diferencia.')
 writeLines(c('REPRODUCCION EXACTA: OK',paste('SHA256:',sha),
  paste('Archivo:',archivo)),file.path(out,'VERIFICACION_FINAL.txt'))
 log_('REPRODUCCION EXACTA VERIFICADA',sha)
 rm(ds,xv,P);gc(FALSE)
}

# [Anotación · líneas 526–567] Celdas 12 y 13 (inicio). Si algún interruptor de experimentos está en TRUE,
#   cambia la carpeta de trabajo a salida/laboratorio/maestra, enlaza allí la carpeta de features, extiende la
#   lista a 20 semillas (las 10 de la entrega más 106621 a 106693), define la regla de etiquetas artificiales
#   (top_k con 10.500 positivos por mes, docente de 10 semillas) y carga codigo/motor_integral.R. Si alguna
#   variante lo requiere, crea la representación con ranking de todas las variables.
#%% celda 12 [texto]
### 2.4 Mis experimentos descartados

Dejo estos switches en FALSE para la entrega. Si quiero volver a correr una variante, activo su switch en la configuración y ejecuto esta celda después de la preparación. Las variantes usan una carpeta de laboratorio y no reemplazan mi CSV final. Los resultados originales están en evidencia/. Junio fue reutilizado durante el desarrollo; no lo presento como un test independiente.

#%% celda 13 [código]
# Dejo anotado: Armo los controles que necesitan mis experimentos en una raíz separada.
EXTRAS <- any(unlist(SW[setdiff(names(SW),c('reproducir_final','bo_origen'))]))
if(EXTRAS) {
 raiz_final <- RAIZ
 laboratorio <- file.path(raiz_final,'laboratorio')
 RAIZ <- file.path(laboratorio,'maestra')
 BASE_LAB <- file.path(laboratorio,'experimentos')
 dir.create(RAIZ,recursive=TRUE,showWarnings=FALSE)
 dir.create(BASE_LAB,recursive=TRUE,showWarnings=FALSE)
 for(n in c('auditoria','datos','datasets','modelos','scores','bo','seleccion','resultados','submits','figuras'))
  dir.create(file.path(RAIZ,n),showWarnings=FALSE)
 if(!dir.exists(file.path(RAIZ,'features')))
  stopifnot(file.symlink(file.path(raiz_final,'features'),file.path(RAIZ,'features')))
 Sys.setenv(DMEYF_LAB_RAIZ=RAIZ,DMEYF_LAB_BASE=BASE_LAB)
 BASE_SEEDS <- PARAM$semillas
 SEEDS_INT <- c(BASE_SEEDS,106621L,106627L,106637L,106649L,106657L,
               106661L,106663L,106669L,106681L,106693L)
 CFG <- list(pseudo_regla='top_k',pseudo_top_k=10500L,
             pseudo_seed=100613L,pseudo_docente_semillas=10L)
 DIR_INT <- file.path(laboratorio,'integral')
 for(n in c('planes','historia','produccion','lotes','auditoria'))
  dir.create(file.path(DIR_INT,n),recursive=TRUE,showWarnings=FALSE)
 source(file.path(CARPETA,'codigo','motor_integral.R'),local=.GlobalEnv)
 rec_control_int <- REC_CONTROL
 HP_DOCENTE_INT <- HP_FINAL
 previo <- file.path(RAIZ,'integral_clase_20261008',
  '0b6b06569ceee877ea42e00a072112f6b536e82c366f16427290dbd4457a2440')
 dir.create(file.path(previo,'historia'),recursive=TRUE,showWarnings=FALSE)
 REC_INT <- list(CONTROL_ORIGINAL=REC_CONTROL)
 HIST_INT <- list();PROD_INT <- list()
 necesito_rank <- SW$rankings || SW$artificiales_rank || SW$rank_zero_tend3
 if(necesito_rank) {
  rr <- REC_CONTROL;rr$rep <- rank_todas_int(REP)
  rr$nombre <- 'RANK_TODAS_POST_LAG2'
  REC_INT$RANK_TODAS <- rr
 }
# [Anotación · líneas 568–591] ejecutar_receta() entrena una receta con las 20 semillas (para junio con
#   202103-202104, o para agosto con 202103-202106 y préstamos), promedia probabilidades y guarda el cierre.
#   Dentro de este bloque el control histórico se ejecuta siempre; el control de agosto y la receta con ranking
#   (hiperparámetros leídos de procedencia_bo/37fa6c85…) se ejecutan según los interruptores.
 ejecutar_receta <- function(nom,rec,hp,prod=FALSE) {
  xs <- lapply(SEEDS_INT,function(s)fit_score(rec,hp,s,prod,prod))
  en <- promediar_prob_int(xs,paste0(nom,if(prod)'_AGOSTO' else '_JUNIO'))
  plan <- list(semillas=SEEDS_INT,raw=RAW_HASH,rep=rec$rep$id)
  z <- list(nombre=nom,receta=rec,hp=hp,
   modelos=vapply(xs,`[[`,character(1),'id'),ensemble=en$en,
   plan=plan,resumen=if(prod)NULL else resumen_junio_int(xs,en$en,nom))
  if(prod) PROD_INT[[nom]] <<- z else {
   HIST_INT[[nom]] <<- z
   atomic(z,file.path(previo,'historia',paste0('CIERRE_',nom,'.rds')))
  }
  z
 }
 ejecutar_receta('CONTROL_ORIGINAL',REC_CONTROL,HP_FINAL,FALSE)
 if(SW$control || SW$diagnosticos_ens5)
  ejecutar_receta('CONTROL_ORIGINAL',REC_CONTROL,HP_FINAL,TRUE)
 if(necesito_rank) {
  hp_rank <- readRDS(file.path(CARPETA,'procedencia_bo',
   '37fa6c85a784b6a214de0590f8f9e40c037228d73d6dfc2aed3763b62b93d972',
   'TERMINADO.rds'))$valor$optimos[[1L]]
  ejecutar_receta('RANK_TODAS',REC_INT$RANK_TODAS,hp_rank,FALSE)
  if(SW$rankings || SW$diagnosticos_ens5)
   ejecutar_receta('RANK_TODAS',REC_INT$RANK_TODAS,hp_rank,TRUE)
 }
# [Anotación · líneas 592–629] Variantes con etiquetas artificiales (sobre la receta original o la rankeada,
#   con hiperparámetros de otras dos búsquedas guardadas), con ranking de cero fijo sólo en variables de monto
#   (campos tomados de la firma de la búsqueda 2595ac2f…) y con clase positiva sólo BAJA+2 (hiperparámetros de
#   la búsqueda bf654ea5…). Cada una corre únicamente si su interruptor está en TRUE.
 for(nom in c('ARTIFICIALES_ORIGINAL','ARTIFICIALES_RANK')) {
  activo <- if(nom=='ARTIFICIALES_ORIGINAL')SW$artificiales_original else SW$artificiales_rank
  if(!activo)next
  rr <- if(nom=='ARTIFICIALES_ORIGINAL')REC_CONTROL else REC_INT$RANK_TODAS
  rr$nombre <- paste0(nom,'_LAG2');rr$estrategia <- 'ARTIFICIALES_4H_6P'
  rr$planes <- list(hist=plan_pseudo_int(rr,FALSE),prod=NULL)
  bid <- if(nom=='ARTIFICIALES_ORIGINAL')
   'd3d28cc4bd4d5336fb1bd7e8d6b47de26375209806f59252be5d44873d477efa' else
   '0621c1e8942c1632c00f8ae4c7b80adcfd58c304a43bbb334088afbf63ff8b3c'
  hp <- readRDS(file.path(CARPETA,'procedencia_bo',bid,'TERMINADO.rds'))$valor$optimos[[1L]]
  ejecutar_receta(nom,rr,hp,FALSE)
  rr$planes$prod <- plan_pseudo_int(rr,TRUE)
  ejecutar_receta(nom,rr,hp,TRUE)
 }
 if(SW$rank_montos) {
  D <- cargar_base()
  bo <- readRDS(file.path(CARPETA,'procedencia_bo',
   '2595ac2f643b4afb3166b2701db84bc24e786246b65cabc9c73025d1ba5f66a8',
   'TERMINADO.rds'))
  PARAM$rank_campos <- bo$firma$dataset$campos[
   !grepl('_(delta_)?lag[12]$',bo$firma$dataset$campos)]
  PARAM$rank_campos <- intersect(PARAM$rank_campos,
   grep('^(m|Master_m|Visa_m)',names(D),value=TRUE))
  rr <- REC_CONTROL;rr$rep <- preparar_features(D,TRUE)
  rr$nombre <- 'RANK_MONTOS_CERO_LAG2'
  ejecutar_receta('RANK_MONTOS',rr,bo$valor$optimos[[1L]],FALSE)
  rm(D);gc(FALSE)
 }
 if(SW$target_baja2) {
  rr <- REC_CONTROL;rr$nombre <- 'ORIGINAL_LAG2_TARGET_BAJA2'
  d <- leer_meses(REP,PARAM$train)
  rr$planes <- list(hist=list(key=paste(d$numero_de_cliente,d$foto_mes),
   y=as.integer(d$clase_ternaria=='BAJA+2'),meses=PARAM$train),prod=NULL)
  hp <- readRDS(file.path(CARPETA,'procedencia_bo',
   'bf654ea508b68620dba3a8ffa6f1aeb91e2886174dceeca3fd104ac91f0fd675',
   'TERMINADO.rds'))$valor$optimos[[1L]]
  ejecutar_receta('TARGET_BAJA2',rr,hp,FALSE)
 }
# [Anotación · líneas 630–649] Asocia siete interruptores (tarjetas, solo_visa, solo_master, vinculacion,
#   sin_cierres_historico, rank_zero_tend3, bo_sin_cierres_nueva) con un script de experimentos/ y una carpeta
#   de salida, y ejecuta con source() los que estén activos. Para bo_sin_cierres_nueva copia antes los puntajes
#   finales de la semilla 100613 a la carpeta que ese script lee.
 mapa <- c(tarjetas='STATUS_TRANSICIONES_H_V1',
  solo_visa='STATUS_ABLACIONES_H_V1/SOLO_VISA',
  solo_master='STATUS_ABLACIONES_H_V1/SOLO_MASTER',
  vinculacion='VINCULACION_H_V1',sin_cierres_historico='SIN_CIERRES_H_V1',
  rank_zero_tend3='RANK_ZERO_TEND3_H_V1',bo_sin_cierres_nueva='SIN_CIERRES_BO_FINAL_V1')
 for(nom in names(mapa)) {
  if(!SW[[nom]])next
  od <- file.path(BASE_LAB,mapa[[nom]])
  dir.create(od,recursive=TRUE,showWarnings=FALSE)
  sp <- file.path(CARPETA,'experimentos',paste0(nom,'.R'))
  if(nom=='bo_sin_cierres_nueva') {
   fd <- file.path(BASE_LAB,'SIN_CIERRES_P_V1')
   dir.create(fd,recursive=TRUE,showWarnings=FALSE)
   fp <- readRDS(file.path(raiz_final,'final','SCORES_100613.rds'))
   fp$firma$plan <- list(campos=fp$firma$campos)
   atomic(fp,file.path(fd,'SCORES_100613.rds'))
  }
  Sys.setenv(DMEYF_STATUS_OUT=od,DMEYF_STATUS_SCRIPT=sp,BO_FINAL_OUT=od)
  source(sp,local=new.env(parent=.GlobalEnv))
 }
# [Anotación · líneas 650–669] Diagnóstico ENS5: para cada receta histórica toma 20 combinaciones al azar
#   (set.seed 100613) de 5 modelos entre los disponibles, promedia sus probabilidades y guarda la ganancia de
#   junio en el corte 10.500 y la media entre 10.000 y 11.500. Al terminar restablece la carpeta de salida.
 # Dejo los diagnósticos aparte del entrenamiento final.
 if(SW$diagnosticos_ens5) {
  for(nom in names(HIST_INT)) {
   a <- HIST_INT[[nom]]
   xs <- lapply(a$modelos,function(id)readRDS(file.path(RAIZ,'scores',paste0(id,'.rds')))$valor)
   ref <- xs[[1]]$scores
   P <- sapply(xs,function(v)v$scores$prob[match(ref$numero_de_cliente,v$scores$numero_de_cliente)])
   set.seed(100613L);comb <- combn(seq_len(ncol(P)),5L)
   grupos <- comb[,sample.int(ncol(comb),20L),drop=FALSE]
   tablas <- lapply(seq_len(ncol(grupos)),function(g) {
    cv <- curva(ref$numero_de_cliente,rowMeans(P[,grupos[,g],drop=FALSE]),ref$clase_ternaria)
    data.table(receta=nom,grupo=g,K10500=cv$ganancia[10500],
               meseta=mean(cv$ganancia[10000:11500]))
   })
   fwrite(rbindlist(tablas),file.path(BASE_LAB,paste0('ENS5_',nom,'.csv')))
  }
 }
 RAIZ <- raiz_final
}

# [Anotación · líneas 670–691] Celdas 14 y 15. Si cortes_historicos es TRUE, lee el resultado del experimento
#   Sin cierres histórico, promedia las probabilidades de junio de sus semillas y tabula, para los cortes
#   10.000, 10.250, 10.375, 10.500, 10.750, 11.000 y 11.500, la ganancia y la ganancia media en una ventana de
#   ±250. Guarda CORTES_HISTORICOS.csv.
#%% celda 14 [texto]
### 2.5 Mi evaluación de cortes

#%% celda 15 [código]
# Dejo anotado: Si lo activo, comparo los cortes históricos sin mirar etiquetas de agosto.
if(SW$cortes_historicos) {
 od <- file.path(Sys.getenv('DMEYF_LAB_BASE'),'SIN_CIERRES_H_V1')
 cierre <- file.path(od,'TERMINADO.rds')
 if(!file.exists(cierre))stop('Debo activar sin_cierres_historico antes de cortes_historicos.')
 h <- readRDS(cierre);ref <- h$ref
 P <- sapply(h$plan$semillas,function(s) {
  a <- readRDS(file.path(od,paste0('SCORES_',s,'.rds')))
  stopifnot(setequal(a$ids,ref$numero_de_cliente))
  a$prob[match(ref$numero_de_cliente,a$ids)]
 })
 ce <- curva(ref$numero_de_cliente,rowMeans(P),ref$clase_ternaria)
 tabla <- rbindlist(lapply(c(10000L,10250L,10375L,10500L,10750L,11000L,11500L),function(k)
  data.table(corte=k,ganancia=ce$ganancia[k],
   meseta=mean(ce$ganancia[(k-250L):(k+250L)]))))
 fwrite(tabla,file.path(RAIZ,'CORTES_HISTORICOS.csv'));print(tabla)
}

# [Anotación · líneas 692–697] Celda 16 (texto). Resume la configuración de la entrega: reproducir_final en
#   TRUE y el resto en FALSE, archivo SINCIERRES_PROB10_K10375.csv, diez semillas, 1907 iteraciones, 77 hojas,
#   752 columnas y promedio de probabilidades con verificación por SHA256.
#%% celda 16 [texto]
## 3. Mi configuración de entrega

Dejo **reproducir_final=TRUE** y el resto de switches en FALSE. Ejecuto la sección Python una vez; cambio a R y ejecuto configuración → funciones → preparación → entrenamiento y ensamble → experimentos apagados → cortes apagados.

Mi archivo es **SINCIERRES_PROB10_K10375.csv**. Uso diez semillas, HP 1907/77/2,83699883991516, 752 columnas en producción y promedio simple de probabilidades. La verificación SHA256 detiene la ejecución si el archivo no coincide. Conservo la BO de origen en BO_Origen.ipynb y procedencia_bo/. No utilizo la BO nueva de Sin cierres para la entrega.
```

### REPRODUCIR_FINAL.R

Punto de entrada sin Jupyter: ejecuta con source() configuracion.R, preparacion.R y final.R de la carpeta codigo/.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–3] Ejecuta en orden codigo/configuracion.R (parámetros, verificaciones y carga de
#   motor.R), codigo/preparacion.R (base, lags y lectura de hiperparámetros) y codigo/final.R (entrenamiento de
#   10 semillas, promedio, corte y verificación).
source('codigo/configuracion.R')
source('codigo/preparacion.R')
source('codigo/final.R')
```

### codigo/preparacion.R

Ejecuta la carga de la base y el cálculo de lags y deltas, lee de procedencia_bo/ los hiperparámetros de la optimización de origen y define la receta ORIGINAL_LAG2. Mismo contenido que la celda 9 de la notebook de entrega.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–6] Ejecuta cargar_base() (clase reconstruida y corrección de ccajas_depositos) y
#   preparar_features() sin ranking (lags y deltas de orden 1 y 2). Exige que el identificador de la
#   representación sea c9527308… y libera la tabla base.
# Reconstruyo el target, corrijo mayo y calculo la historia calendario exacta.
D <- cargar_base()
REP <- preparar_features(D,FALSE)
stopifnot(REP$id=='c9527308c55d2d52c924dc64ce5594db3d240bce96c8a548c6f48a06239c71c8')
rm(D)
gc(full=TRUE)
# [Anotación · líneas 7–15] Lee procedencia_bo/52fc1b5d…/TERMINADO.rds, toma la primera configuración de esa
#   optimización y comprueba que sea 1907 iteraciones, 77 hojas y min_sum_hessian_in_leaf 2,83699883991516.
#   Define la receta ORIGINAL_LAG2: representación con lags, sin selección ni exclusiones propias de la receta.
# Dejo anotado: Recupero la procedencia de los HP sin hacer pasar una BO nueva por la original.
ORIGEN <- readRDS(file.path(CARPETA,'procedencia_bo',
 '52fc1b5d908fb495ce06d1ed3038defbaf9a2609d2ea0bc80904d2ba8b58c6ed',
 'TERMINADO.rds'))
HP_FINAL <- ORIGEN$valor$optimos[[1L]]
stopifnot(HP_FINAL$num_iterations==1907L,HP_FINAL$num_leaves==77L,
 abs(HP_FINAL$min_sum_hessian_in_leaf-2.83699883991516)<1e-12)
REC_CONTROL <- list(nombre='ORIGINAL_LAG2',rep=REP,estrategia='COMPLETO',
 umbral=NULL,seleccion=NULL,excluir=character(),planes=NULL)
# [Anotación · líneas 16–22] Sólo si bo_origen es TRUE: exige mlrMBO, mlr, ParamHelpers, smoof y DiceKriging,
#   ejecuta bayes() sobre la receta y guarda el resultado en BO_ORIGEN_REEJECUTADA.rds.
# Dejo anotado: Si activo la BO de origen, la ejecuto en otra raíz sin reutilizar su resultado.
if(SW$bo_origen) {
 for(paquete in c('mlrMBO','mlr','ParamHelpers','smoof','DiceKriging'))
  if(!requireNamespace(paquete,quietly=TRUE))stop('Debo instalar ',paquete)
 b <- bayes(REC_CONTROL)
 atomic(b,file.path(RAIZ,'BO_ORIGEN_REEJECUTADA.rds'))
}
```

### codigo/motor.R

Funciones compartidas: caché con firma y bloqueo, parámetros base de LightGBM, reconstrucción de la clase y corrección de datos (cargar_base), lags y deltas (preparar_features), armado de datasets, entrenamiento con predicción y ganancia (fit_score), optimización bayesiana (bayes) y funciones de variantes que la ruta final no invoca (canaritos, filtro de negativos, etiquetas artificiales, ablaciones, auditoría de distribuciones). Idéntico a la celda 7 de la notebook de entrega.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–14] Carga data.table, digest, jsonlite y filelock, fija los hilos de data.table y crea
#   bajo la carpeta de salida las subcarpetas auditoria, datos, features, datasets, modelos, scores, bo,
#   seleccion, resultados, submits, figuras y fuentes. Define utilidades: hash SHA256 de un objeto, mensaje con
#   fecha a pantalla y a PROGRESO.log, guardado de .rds y .csv mediante archivo temporal y renombrado, y un
#   registro CSV de qué resultados se calculan y cuáles se reutilizan.
# Dejo anotado: CELDA 04 — Defino mis funciones y la persistencia.
# Mantengo el cálculo en R y guardo cada resultado costoso antes de avanzar.
suppressPackageStartupMessages({library(data.table);library(digest);library(jsonlite);library(filelock)})
options(scipen=999, datatable.print.nrows=30)
setDTthreads(PARAM$threads)
CODE <- 'MAESTRA_CATEDRA_20261007_v1'
RAIZ <- Sys.getenv('DMEYF_RAIZ'); RAW <- Sys.getenv('DMEYF_DATOS')
stopifnot(nzchar(RAIZ),file.exists(RAW))
for (s in c('auditoria','datos','features','datasets','modelos','scores','bo','seleccion','resultados','submits','figuras','fuentes')) dir.create(file.path(RAIZ,s),recursive=TRUE,showWarnings=FALSE)
hash <- function(x) digest(x,algo='sha256')
log_ <- function(...) {s<-paste(format(Sys.time(),'%Y-%m-%d %H:%M:%S %Z'),paste(...,collapse=' '));cat(s,'\n');cat(s,'\n',file=file.path(RAIZ,'PROGRESO.log'),append=TRUE)}
atomic <- function(x,path) {tmp<-paste0(path,'.tmp_',Sys.getpid());saveRDS(x,tmp,compress=FALSE);if(!file.rename(tmp,path)){if(!file.copy(tmp,path,overwrite=TRUE))stop('No pude persistir ',path);unlink(tmp)};invisible(path)}
csv <- function(x,path) {tmp<-paste0(path,'.tmp_',Sys.getpid());fwrite(x,tmp);if(!file.rename(tmp,path)){if(!file.copy(tmp,path,overwrite=TRUE))stop('No pude persistir ',path);unlink(tmp)}}
registro <- function(etapa,archivo,accion,motivo){p<-file.path(RAIZ,'auditoria','AUDITORIA_REUTILIZACION.csv');d<-data.table(fecha=as.character(Sys.time()),etapa=etapa,archivo=archivo,accion=accion,motivo=motivo);fwrite(d,p,append=file.exists(p),col.names=!file.exists(p))}
# [Anotación · líneas 15–30] Define cache(): guarda cada resultado en un .rds cuyo nombre es el hash de su
#   firma, lo reutiliza si ya existe con firma idéntica y toma un archivo de bloqueo en ~/.cache/dmeyf_locks
#   para impedir dos ejecuciones simultáneas del mismo cálculo. Registra las versiones de R, lightgbm y
#   data.table, el MD5 del crudo y la salida de sessionInfo(); define PRESTAMOS (cprestamos_personales,
#   mprestamos_personales) y el vector de semillas.
# Dejo anotado: Los locks de cálculo viven en disco local; todos los procesos de esta VM comparten la ruta.
# No ejecuto simultáneamente esta misma RAIZ desde dos VM distintas.
LOCK_DIR<-file.path(path.expand('~/.cache/dmeyf_locks'),hash(RAIZ));dir.create(LOCK_DIR,recursive=TRUE,showWarnings=FALSE)
cache <- function(etapa,firma,fun){
 p<-file.path(RAIZ,etapa,paste0(hash(firma),'.rds'))
 lk<-filelock::lock(file.path(LOCK_DIR,paste0(hash(p),'.lock')),timeout=0)
 if(is.null(lk))stop('Otra ejecución está usando este checkpoint: ',p)
 on.exit(filelock::unlock(lk))
 if(file.exists(p)){z<-readRDS(p);stopifnot(identical(z$firma,firma));registro(etapa,p,'REUTILIZAR','Firma exacta');return(z$valor)}
 log_('CALCULO',etapa,basename(p));v<-fun();atomic(list(firma=firma,valor=v,fecha=Sys.time()),p);registro(etapa,p,'CALCULAR','No existe checkpoint compatible para esta firma');v
}
VERSIONES<-list(R=as.character(getRversion()),lightgbm=as.character(packageVersion('lightgbm')),data.table=as.character(packageVersion('data.table')))
RAW_HASH<-unname(tools::md5sum(RAW));writeLines(capture.output(sessionInfo()),file.path(RAIZ,'auditoria','SESSION_INFO.txt'))
atomic(PARAM,file.path(RAIZ,'PLAN_ACTUAL.rds'));atomic(VERSIONES,file.path(RAIZ,'auditoria','VERSIONES.rds'))
PRESTAMOS<-c('cprestamos_personales','mprestamos_personales')
SEMILLAS<-as.integer(PARAM$semillas)
# [Anotación · líneas 31–40] par_base(seed) devuelve los parámetros de LightGBM comunes a todos los modelos:
#   gbdt, objetivo binary, métrica average_precision, learning_rate 0,005, feature_fraction 0,50,
#   feature_fraction_bynode 0,20, max_bin 31, min_data_in_leaf 0, max_depth -1, lambda_l1 y lambda_l2 en 0, sin
#   bagging, scale_pos_weight 1 y modo determinístico. periodo() convierte AAAAMM en un número de mes
#   correlativo. rank_cero() reemplaza cada valor por su rango relativo dentro del grupo: el cero queda en 0,
#   los positivos entre 0 y 1 y los negativos entre -1 y 0; se aplica sólo cuando se pide ranking.
par_base<-function(seed){list(boosting='gbdt',objective='binary',metric='average_precision',feature_pre_filter=FALSE,
 first_metric_only=FALSE,boost_from_average=TRUE,force_row_wise=TRUE,deterministic=TRUE,verbosity=-1,
 seed=as.integer(seed),num_threads=PARAM$threads,max_depth=-1L,min_gain_to_split=0,lambda_l1=0,lambda_l2=0,max_bin=31L,
 bagging_fraction=1,bagging_freq=0L,pos_bagging_fraction=1,neg_bagging_fraction=1,is_unbalance=FALSE,scale_pos_weight=1,
 extra_trees=FALSE,min_data_in_leaf=0L,feature_fraction=.50,feature_fraction_bynode=.20,learning_rate=.005)}
periodo<-function(x) as.integer(x%/%100L*12L+x%%100L)
rank_cero<-function(x){z<-rep(NA_real_,length(x));z[which(x==0)]<-0;ip<-which(is.finite(x)&x>0);ineg<-which(is.finite(x)&x<0)
 if(length(ip))z[ip]<-frank(x[ip],ties.method='average')/length(ip)
 if(length(ineg))z[ineg]<- -frank(abs(x[ineg]),ties.method='average')/length(ineg)
 z}
# [Anotación · líneas 41–46] inventario_previo() lista los archivos csv, rds, txt, json, bin e ipynb que
#   existan en carpetas de corridas anteriores y en la salida, y guarda el listado en
#   auditoria/INVENTARIO_PREVIO.csv. Los scripts de codigo/ no la invocan.
# Audito lo que existe, sin cargar modelos ni recalcular resultados anteriores.
inventario_previo<-function(){
 roots<-unique(c(Sys.getenv('DMEYF_ANTERIORES'),file.path(dirname(RAIZ),'HOJA_RUTA_AGOSTO'),RAIZ));roots<-roots[nzchar(roots)&dir.exists(roots)]
 out<-rbindlist(lapply(roots,function(root){ff<-list.files(root,recursive=TRUE,full.names=TRUE);ff<-ff[grepl('\\.(csv|rds|txt|json|bin|ipynb)$',ff)];if(!length(ff))return(NULL);fi<-file.info(ff);data.table(archivo=ff,bytes=fi$size,fecha=as.character(fi$mtime),estado='LOCALIZADO; compatibilidad pendiente, no equivale a reutilizado')}),fill=TRUE)
 csv(out,file.path(RAIZ,'auditoria','INVENTARIO_PREVIO.csv'));log_('Inventario',nrow(out),'archivos. No cambio ni borro artefactos anteriores.');out
}
# [Anotación · líneas 47–59] cargar_base() (inicio): lee el crudo con fread, exige que no haya pares cliente-
#   mes duplicados y que estén los meses 202103 a 202108, y guarda las dimensiones. Reconstruye la clase a
#   partir de la presencia mensual de cada cliente: CONTINUA para las filas de meses hasta 202106, BAJA+1 si el
#   cliente no tiene registro en el mes siguiente y BAJA+2 si lo tiene en el siguiente pero no en el
#   subsiguiente.
cargar_base<-function(){
 firma<-list(componente='base_DQ_target_v1',raw=RAW_HASH)
 cache('datos',firma,function(){
  d<-fread(RAW);stopifnot(all(c('numero_de_cliente','foto_mes')%in%names(d)),!anyNA(d$numero_de_cliente),!anyNA(d$foto_mes))
  if(anyDuplicated(d[,.(numero_de_cliente,foto_mes)]))stop('Duplicados cliente x mes')
  if(!all(202103L:202108L%in%unique(d$foto_mes)))stop('No están marzo-agosto de 2021')
  csv(data.table(filas=nrow(d),columnas=ncol(d),clientes=uniqueN(d$numero_de_cliente),md5=RAW_HASH),file.path(RAIZ,'auditoria','DIMENSIONES.csv'))
  setorder(d,numero_de_cliente,foto_mes)
  q<-d[,.(numero_de_cliente,foto_mes,p=periodo(foto_mes))];ult<-max(q$p)
  q[,c('p1','p2'):=shift(p,n=1:2,type='lead'),by=numero_de_cliente]
  q[,reconstruida:=fifelse(p<ult-1L,'CONTINUA',NA_character_)]
  q[p<ult & (is.na(p1)|p1>p+1L),reconstruida:='BAJA+1']
  q[p<ult-1L & !is.na(p1)&p1==p+1L & (is.na(p2)|p2>p+2L),reconstruida:='BAJA+2']
# [Anotación · líneas 60–70] Si el crudo trae clase_ternaria, tabula por mes la concordancia entre la clase
#   original y la reconstruida, guarda las discrepancias y detiene la ejecución si hay alguna; completa con la
#   reconstruida las filas sin clase original. Si no la trae, usa la reconstruida. Exige que no falten clases
#   hasta 202106 y guarda el conteo de clases por mes.
  if('clase_ternaria'%in%names(d)){
   q[,original:=as.character(d$clase_ternaria)]
   csv(q[, .N,by=.(foto_mes,original,reconstruida)],file.path(RAIZ,'auditoria','CONCORDANCIA_TARGET.csv'))
   ex<-q[!is.na(original)&!is.na(reconstruida)&original!=reconstruida]
   csv(ex,file.path(RAIZ,'auditoria','EXCEPCIONES_TARGET.csv'))
   if(nrow(ex))stop('Target original y reconstruido discrepan. Revisar EXCEPCIONES_TARGET.csv')
   d[,clase_ternaria:=as.character(clase_ternaria)]
   d[is.na(clase_ternaria),clase_ternaria:=q$reconstruida[is.na(d$clase_ternaria)]]
  }else{d[,clase_ternaria:=q$reconstruida];writeLines('Sin etiqueta original; uso la reconstrucción del notebook de cátedra, no una concordancia verificada.',file.path(RAIZ,'auditoria','FUENTE_TARGET.txt'))}
  if(anyNA(d[foto_mes<=202106L,clase_ternaria]))stop('Hay etiquetas faltantes en training/evaluación completos')
  csv(d[,.N,by=.(foto_mes,clase_ternaria)],file.path(RAIZ,'auditoria','CLASES_POR_MES.csv'))
# [Anotación · líneas 71–84] Guarda un conteo de ceros y faltantes de ccajas_depositos en 202105 y pasa esa
#   variable a NA en ese mes. Convierte las columnas no numéricas a códigos enteros según el orden de sus
#   valores (guarda el mapa) y reemplaza por NA los valores numéricos no finitos. Devuelve la tabla con la lista
#   de columnas categóricas como atributo; todo el resultado queda en caché.
  if(!'ccajas_depositos'%in%names(d))stop('No existe ccajas_depositos')
  csv(d[foto_mes==202105L,.(N=.N,ceros=sum(ccajas_depositos==0,na.rm=TRUE),missing=sum(is.na(ccajas_depositos)))],file.path(RAIZ,'auditoria','DQ_MAYO.csv'))
  d[foto_mes==202105L,ccajas_depositos:=NA_real_]
  campos<-setdiff(names(d),c('numero_de_cliente','foto_mes','clase_ternaria'))
  catvars<-campos[!vapply(d[,..campos],is.numeric,logical(1))]
  mapa<-list()
  for(v in catvars){lev<-sort(unique(as.character(d[[v]][!is.na(d[[v]])])));mapa[[v]]<-lev;set(d,j=v,value=match(as.character(d[[v]]),lev))}
  atomic(mapa,file.path(RAIZ,'auditoria','MAPA_CATEGORIAS.rds'))
  nums<-setdiff(campos,catvars)
  for(v in nums){ii<-which(!is.finite(d[[v]])&!is.na(d[[v]]));if(length(ii))set(d,ii,v,NA_real_)}
  attr(d,'categoricas')<-catvars
  d
 })
}
# [Anotación · líneas 85–95] preparar_features() (inicio): arma la firma de la representación (MD5 del crudo,
#   corrección de ccajas_depositos, orden de lags, campos a rankear, categóricas), crea una carpeta en features/
#   con el hash de esa firma y determina qué meses de 202103 a 202108 todavía no tienen su bloque guardado.
# Fijo la transformación sin usar el target; los percentiles se calculan por mes en toda la cartera.
preparar_features<-function(d,rankear=FALSE){
 campos<-setdiff(names(d),c('numero_de_cliente','foto_mes','clase_ternaria'));cats<-attr(d,'categoricas')
 ii_discovery<-which(d$foto_mes%in%PARAM$train)
 elegibles<-if(rankear)PARAM$rank_campos else character()
 if(rankear)stopifnot(length(elegibles)>0L,all(elegibles%in%campos),!any(elegibles%in%cats),all(vapply(d[,..elegibles],is.numeric,logical(1))))
 f<-list(componente=if(rankear)'historia_rank_montos_explicitos_v2' else 'historia_mensual_v1',raw=RAW_HASH,dq='ccajas_depositos_202105_NA',orden=PARAM$orden_lags,rank_cero=elegibles,categoricas=cats)
 k<-hash(f);rdir<-file.path(RAIZ,'features',k);dir.create(rdir,recursive=TRUE,showWarnings=FALSE)
 # Reutilizo cada bloque terminado aunque se haya interrumpido otro mes.
 meses<-202103L:202108L
 faltan<-meses[!file.exists(file.path(rdir,paste0(meses,'.rds')))]
# [Anotación · líneas 96–113] Para los meses faltantes: si se pidió ranking aplica rank_cero por mes a los
#   campos elegidos (en la entrega esa lista está vacía). Ubica para cada fila la fila del mismo cliente
#   exactamente 1 y 2 meses calendario antes (si el cliente no tiene registro de ese mes queda NA) y agrega, por
#   cada variable, el valor rezagado (_lag1, _lag2) y, para las numéricas, la diferencia entre el valor actual y
#   el rezagado (_delta_lag1, _delta_lag2). Guarda un .rds por mes.
 if(length(faltan)){
  log_('RECALCULO IMPRESCINDIBLE: bloques faltantes',paste(faltan,collapse=','),'representación',k)
  log_('Motivo: falta firma exacta de DQ, lags y ranking. Reutilizo base, bloques existentes y cálculos posteriores compatibles.')
  b<-copy(d)
  for(v in elegibles){set(b,j=v,value=as.numeric(b[[v]]));b[,(v):=rank_cero(get(v)),by=foto_mes]}
  pp<-periodo(b$foto_mes);ids<-b$numero_de_cliente
  # Localizo lag calendario exacto: no confundo una ausencia mensual con lag1.
  key<-paste(ids,pp,sep=':');lagidx<-lapply(seq_len(PARAM$orden_lags),function(l)match(paste(ids,pp-l,sep=':'),key))
  for(m in faltan){
   ix<-which(b$foto_mes==m);z<-copy(b[ix])
   for(l in seq_len(PARAM$orden_lags))for(v in campos){
    lagv<-b[[v]][lagidx[[l]][ix]];set(z,j=paste0(v,'_lag',l),value=lagv)
    if(!v%in%cats)set(z,j=paste0(v,'_delta_lag',l),value=b[[v]][ix]-lagv)
   }
   atomic(list(firma=f,mes=m,datos=z),file.path(rdir,paste0(m,'.rds')));log_('Bloque guardado',m,'features',ncol(z)-3L);rm(z);gc(FALSE)
  }
  rm(b);gc(FALSE)
 }
# [Anotación · líneas 114–120] Arma la lista ordenada de predictores: numero_de_cliente y foto_mes, las
#   variables originales y, para cada orden de lag, las columnas _lag y _delta_lag. Guarda el catálogo de
#   variables y la firma, y devuelve el identificador de la representación, su carpeta y la lista de campos.
 campos_todos<-c(campos,unlist(lapply(seq_len(PARAM$orden_lags),function(l)c(paste0(campos,'_lag',l),paste0(setdiff(campos,cats),'_delta_lag',l)))))
 if(PARAM$incluir_id_mes)campos_todos<-c('numero_de_cliente','foto_mes',campos_todos)
 cat<-data.table(variable=campos_todos,ranking=FALSE,temporal=grepl('_lag[12]$',campos_todos))
 cat[,origen:=sub('_(delta_)?lag[12]$','',variable)];cat[,ranking:=origen%in%elegibles]
 csv(cat,file.path(rdir,'CATALOGO_FEATURES.csv'));atomic(f,file.path(rdir,'FIRMA.rds'))
 list(id=k,dir=rdir,campos=campos_todos,rank=rankear,firma=f)
}
# [Anotación · líneas 121–129] leer_meses() lee y apila los bloques mensuales verificando firma y mes.
#   campos_receta() devuelve los predictores de una receta: quita la familia de préstamos personales (nivel,
#   lags y deltas) salvo que se pida conservarla, aplica una selección de variables si la receta la trae y quita
#   las familias listadas en excluir. curva() ordena por probabilidad descendente (desempate por ID) y acumula
#   la ganancia en millones: 1.072.500 por cada BAJA+2 y -27.500 por cada otro cliente.
leer_meses<-function(rep,meses){rbindlist(lapply(meses,function(m){z<-readRDS(file.path(rep$dir,paste0(m,'.rds')));stopifnot(identical(z$firma,rep$firma),identical(z$mes,as.integer(m)));z$datos}),use.names=TRUE)}
campos_receta<-function(rec,produccion=FALSE,prestamos=FALSE){
 c<-rec$rep$campos
 if(!prestamos)c<-c[!sub('_(delta_)?lag[12]$','',c)%in%PRESTAMOS]
 if(!is.null(rec$seleccion)){lo<-c[sub('_(delta_)?lag[12]$','',c)%in%PRESTAMOS];c<-intersect(c,rec$seleccion);if(prestamos)c<-unique(c(c,lo))}
 if(length(rec$excluir))c<-c[!sub('_(delta_)?lag[12]$','',c)%in%rec$excluir]
 c
}
curva<-function(ids,prob,y){stopifnot(length(ids)==length(prob),length(y)==length(ids),!anyNA(y),all(is.finite(prob)));ix<-order(-prob,ids);data.table(corte=seq_along(ix),ganancia=cumsum(ifelse(y[ix]=='BAJA+2',1072500,-27500))/1e6)}
# [Anotación · líneas 130–154] materializar() construye el dataset de LightGBM de una receta: meses
#   202103-202104 (histórico) o 202103-202106 (producción), etiqueta 1 para BAJA+1 y BAJA+2 y 0 para CONTINUA, o
#   las filas y etiquetas de un plan si la receta lo trae. Lee /proc/meminfo y se detiene si el tamaño estimado
#   de la matriz supera el 85 % de la memoria disponible. Construye el lgb.Dataset con max_bin 31, lo guarda en
#   binario en datasets/ y devuelve sus metadatos; si el archivo ya existe con la misma firma, lo reutiliza.
# Construyo el dataset LightGBM una vez por diseño; lo guardo en binario y libero la matriz densa.
materializar<-function(rec,prod=FALSE,prestamos=FALSE){
 meses<-if(prod)PARAM$train_final else PARAM$train
 if(!is.null(rec$planes)&&!is.null(rec$planes[[if(prod)'prod' else 'hist']]$meses))meses<-rec$planes[[if(prod)'prod' else 'hist']]$meses
 campos<-campos_receta(rec,prod,prestamos)
 firma<-list(componente='dataset_v1',raw=RAW_HASH,representacion=rec$rep$id,campos=campos,meses=meses,estrategia=rec$estrategia,umbral=rec$umbral,versiones=VERSIONES,
  plan=if(is.null(rec$planes))NULL else hash(rec$planes[[if(prod)'prod' else 'hist']]))
 key<-hash(firma);fp<-file.path(RAIZ,'datasets',paste0(key,'.rds'));bin<-file.path(RAIZ,'datasets',paste0(key,'.bin'))
 if(file.exists(fp)&&file.exists(bin)){z<-readRDS(fp);stopifnot(identical(z$firma,firma));registro('dataset',bin,'REUTILIZAR','Firma exacta');return(z$valor)}
 d<-leer_meses(rec$rep,meses);y<-as.integer(d$clase_ternaria%in%c('BAJA+1','BAJA+2'))
 if(!is.null(rec$planes)){
  plan<-rec$planes[[if(prod)'prod' else 'hist']]
  keys<-paste(d$numero_de_cliente,d$foto_mes);pi<-match(plan$key,keys);stopifnot(!anyNA(pi));d<-d[pi];y<-plan$y
 }
 stopifnot(length(campos)>0,nrow(d)>0,!anyNA(y),all(y%in%c(0,1)),uniqueN(y)==2L)
 # Calculo un límite conservador antes de materializar para evitar otra caída de RAM.
 mi<-readLines('/proc/meminfo');av<-as.numeric(sub('.*?([0-9]+).*','\\1',mi[grepl('^MemAvailable:',mi)]))*1024
 estimado<-as.double(nrow(d))*length(campos)*8*3
 if(length(av)&&is.finite(av)&&estimado>av*.85)stop('Memoria insuficiente para esta matriz: necesito margen aproximado ',round(estimado/2^30,1),' GiB. Checkpoints conservados.')
 log_('Dataset',rec$nombre,if(prod)'PRODUCCION' else 'HISTORICO','filas',nrow(d),'features',length(campos),'préstamos',prestamos)
 x<-data.matrix(d[,..campos]);dm<-lightgbm::lgb.Dataset(x,label=y,free_raw_data=TRUE,params=list(max_bin=31L,feature_pre_filter=FALSE));dm$construct()
 tmp<-paste0(bin,'.tmp_',Sys.getpid());lightgbm::lgb.Dataset.save(dm,tmp);if(!file.rename(tmp,bin))stop('No pude persistir dataset binario')
 meta<-list(bin=bin,campos=campos,n=nrow(d),y_hash=hash(y),filas_hash=hash(d[,.(numero_de_cliente,foto_mes)]),firma=firma,id=key)
 atomic(list(firma=firma,valor=meta),fp);rm(x,dm,d);gc(FALSE);meta
}
# [Anotación · líneas 155–178] fit_score() entrena un modelo para una receta, un juego de hiperparámetros y
#   una semilla, y predice 202106 (histórico) o 202108 (producción). Reutiliza modelo y puntajes guardados si la
#   firma coincide. Guarda el modelo en texto, la probabilidad y el puntaje crudo por cliente, la importancia de
#   variables y un registro; en el modo histórico calcula la curva de ganancia de junio y toma la ganancia en el
#   corte 11.500.
fit_score<-function(rec,hp,seed,prod=FALSE,prestamos=FALSE){
 meta<-materializar(rec,prod,prestamos);mes<-if(prod)202108L else 202106L;p<-modifyList(par_base(seed),hp)
 sig<-list(componente='fit_v1',dataset=meta$firma,pars=p,seed=seed,score_mes=mes,score_rep=rec$rep$id)
 key<-hash(sig);mp<-file.path(RAIZ,'modelos',paste0(key,'.txt'));sp<-file.path(RAIZ,'scores',paste0(key,'.rds'))
 if(file.exists(sp)&&file.exists(mp)){z<-readRDS(sp);stopifnot(identical(z$firma,sig));registro('modelo_scores',sp,'REUTILIZAR','Firma exacta');return(z$valor)}
 # Dejo anotado: Si el modelo terminó pero se cortó antes de guardar scores, lo reutilizo.
 mf<-paste0(mp,'.firma.rds');m<-NULL
 if(file.exists(mp)&&file.exists(mf)){stopifnot(identical(readRDS(mf),sig));m<-lightgbm::lgb.load(mp);log_('RECUPERO modelo terminado',key)}
 if(is.null(m)){
  log_('ENTRENO',rec$nombre,seed,'mes',mes,'iteraciones',p$num_iterations)
  dt<-lightgbm::lgb.Dataset(meta$bin,params=list(max_bin=31L,feature_pre_filter=FALSE))
  m<-lightgbm::lgb.train(params=p,data=dt,nrounds=p$num_iterations)
  tmp<-paste0(mp,'.tmp');lightgbm::lgb.save(m,tmp);if(!file.rename(tmp,mp))stop('No pude guardar modelo');atomic(sig,mf);rm(dt);gc(FALSE)
 }
 df<-leer_meses(rec$rep,mes);xx<-data.matrix(df[,meta$campos,with=FALSE]);pr<-predict(m,xx);raw<-predict(m,xx,type='raw')
 stopifnot(length(pr)==nrow(df),all(is.finite(pr)),all(is.finite(raw)))
 out<-list(id=key,receta=rec$nombre,seed=seed,mes=mes,prestamos=prestamos,hp=hp,campos=meta$campos,modelo=mp,
 scores=data.table(numero_de_cliente=df$numero_de_cliente,foto_mes=mes,clase_ternaria=df$clase_ternaria,prob=pr,raw=raw),ganancia=NA_real_)
 im<-as.data.table(lightgbm::lgb.importance(m));im<-merge(data.table(Feature=meta$campos),im,by='Feature',all.x=TRUE);csv(im,file.path(RAIZ,'modelos',paste0(key,'_importancia.csv')))
 if(!prod){cv<-curva(df$numero_de_cliente,pr,df$clase_ternaria);out$ganancia<-cv[corte==PARAM$corte,ganancia];csv(cv,file.path(RAIZ,'resultados',paste0('CURVA_',key,'.csv')))}
 atomic(list(firma=sig,valor=out,fecha=Sys.time()),sp)
 rp<-data.table(id=key,receta=rec$nombre,semilla=seed,mes=mes,prestamos=prestamos,N_train=meta$n,features=length(meta$campos),ganancia=out$ganancia,hp=toJSON(hp,auto_unbox=TRUE),modelo=mp,scores=sp)
 csv(rp,file.path(RAIZ,'modelos',paste0(key,'_registro.csv')));log_('GUARDADO',rec$nombre,seed,if(prod)'agosto' else paste('ganancia',out$ganancia));rm(m,df,xx);gc(FALSE);out
}
# [Anotación · líneas 179–213] bayes() ejecuta la optimización bayesiana con mlrMBO sobre el dataset histórico
#   (202103-202104, sin préstamos personales). Busca num_iterations (512-4096), num_leaves (8-256) y el
#   logaritmo en base 10 de min_sum_hessian_in_leaf (-3 a 1); el objetivo a maximizar es la ganancia de junio en
#   el corte 11.500 con la semilla 100613. Usa 4 puntos de diseño inicial y 8 iteraciones con criterio de mejora
#   esperada y un modelo kriging (regr.km, covarianza Matérn 3/2). Guarda cada evaluación en HISTORIAL, ordena
#   por ganancia descendente y devuelve la primera configuración; si existe TERMINADO.rds con la misma firma
#   devuelve ese resultado sin recalcular.
# Mantengo mlrMBO/DiceKriging, motor de la notebook de cátedra.
# Dejo anotado: Cada evaluación tiene caché propio: incluso si el estado del optimizador queda atrasado no reentreno el mismo punto.
bayes<-function(rec){
 meta<-materializar(rec,FALSE,FALSE)
 sig<-list(componente='bo_catedra_v1',dataset=meta$firma,base=par_base(PARAM$semilla),limites=PARAM$bounds,presupuesto=PARAM$bo_evaluaciones,corte=PARAM$corte,seed=PARAM$semilla,
  versiones=c(VERSIONES,list(mlrMBO=as.character(packageVersion('mlrMBO')),DiceKriging=as.character(packageVersion('DiceKriging')))))
 bd<-file.path(RAIZ,'bo',hash(sig));dir.create(bd,recursive=TRUE,showWarnings=FALSE);terminado<-file.path(bd,'TERMINADO.rds');histp<-file.path(bd,'HISTORIAL.rds');estado<-file.path(bd,'ESTADO.RData')
 if(file.exists(terminado)){z<-readRDS(terminado);stopifnot(identical(z$firma,sig));log_('BO RECUPERADA',rec$nombre);return(z$valor)}
 atomic(sig,file.path(bd,'FIRMA.rds'))
 objetivo<-function(x){
  hp<-list(num_iterations=as.integer(x$num_iterations),num_leaves=as.integer(x$num_leaves),min_sum_hessian_in_leaf=10^x$log10_min_sum_hessian_in_leaf)
  r<-fit_score(rec,hp,PARAM$semilla);g<-r$ganancia;if(!is.finite(g))stop('Ganancia no finita; no agrego evaluación inválida')
  h<-if(file.exists(histp))readRDS(histp) else data.table()
  if(!nrow(h)||!r$id%in%h$modelo){h<-rbindlist(list(h,data.table(evaluacion=nrow(h)+1L,num_iterations=hp$num_iterations,num_leaves=hp$num_leaves,log10_min_sum_hessian_in_leaf=x$log10_min_sum_hessian_in_leaf,min_sum_hessian_in_leaf=hp$min_sum_hessian_in_leaf,ganancia=g,modelo=r$id)),fill=TRUE);atomic(h,histp);csv(h,file.path(bd,'HISTORIAL.csv'))}
  log_('BO',rec$nombre,'evaluaciones únicas',nrow(h),'/',PARAM$bo_evaluaciones,'ganancia',g);g
 }
 ps<-ParamHelpers::makeParamSet(ParamHelpers::makeIntegerParam('num_iterations',lower=PARAM$bounds$iter[1],upper=PARAM$bounds$iter[2]),
  ParamHelpers::makeIntegerParam('num_leaves',lower=PARAM$bounds$leaves[1],upper=PARAM$bounds$leaves[2]),
  ParamHelpers::makeNumericParam('log10_min_sum_hessian_in_leaf',lower=PARAM$bounds$logh[1],upper=PARAM$bounds$logh[2]))
 obj<-smoof::makeSingleObjectiveFunction(name=rec$nombre,fn=objetivo,minimize=FALSE,noisy=TRUE,par.set=ps,has.simple.signature=FALSE)
 mlr::configureMlr(show.learner.output=FALSE)
 ctrl<-mlrMBO::makeMBOControl(save.on.disk.at.time=0,save.file.path=estado)
 ctrl<-mlrMBO::setMBOControlTermination(ctrl,iters=PARAM$bo_evaluaciones-PARAM$bo_iniciales)
 ctrl<-mlrMBO::setMBOControlInfill(ctrl,crit=mlrMBO::makeMBOInfillCritEI())
 learner<-mlr::makeLearner('regr.km',predict.type='se',covtype='matern3_2',control=list(trace=FALSE),nugget.estim=TRUE)
 set.seed(PARAM$semilla,kind="L'Ecuyer-CMRG")
 # Dejo anotado: El resultado final se decide con ganancias monetarias originales, nunca con scores estandarizados.
 if(file.exists(histp)&&nrow(readRDS(histp))>=PARAM$bo_evaluaciones){h<-readRDS(histp)}else{
  tryCatch({if(file.exists(estado)){mlrMBO::mboContinue(estado)}else{design<-ParamHelpers::generateDesign(n=PARAM$bo_iniciales,par.set=ps);mlrMBO::mbo(obj,design=design,learner=learner,control=ctrl)}} ,error=function(e){log_('BO interrumpida; historial/modelos conservados:',conditionMessage(e));stop('No cambio el método ni vuelvo a entrenar puntos guardados. Reejecutar celda 08 retoma; revisar el error anterior.')})
  h<-readRDS(histp)
 }
 setorder(h,-ganancia,modelo);h[,orden:=.I];csv(h,file.path(bd,'ORDENADOS.csv'))
 opt<-lapply(seq_len(min(PARAM$top_configuraciones,nrow(h))),function(i)as.list(h[i,.(num_iterations,num_leaves,min_sum_hessian_in_leaf)]))
 res<-list(nombre=rec$nombre,historial=h,optimos=opt,directorio=bd);atomic(list(firma=sig,valor=res),terminado);res
}
# [Anotación · líneas 214–229] canarios() agrega a los predictores de 202103-202104 un 20 % de columnas de
#   números al azar (canaritos), entrena un LightGBM con PARAM$hp_seleccion, ordena todas las variables por
#   ganancia y conserva las variables reales ubicadas antes de la posición media de los canaritos más un
#   múltiplo de su desvío. Los scripts de codigo/ no la invocan y configuracion.R no define hp_seleccion.
# Dejo anotado: Canaritos: incluyo TODAS las variables, incluso las de importancia cero.
canarios<-function(rec,multiplo){
 f<-list(componente='canarios_v1',rep=rec$rep$id,train=PARAM$train,seed=PARAM$semilla,fraccion=.20,hp=PARAM$hp_seleccion)
 resultado<-cache('seleccion',f,function(){
  d<-leer_meses(rec$rep,PARAM$train);cam<-campos_receta(rec);x<-data.matrix(d[,..cam]);set.seed(PARAM$semilla)
  ncan<-ceiling(ncol(x)*.20);nom<-paste0('canarito_',seq_len(ncan));x<-cbind(x,matrix(runif(nrow(x)*ncan),nrow=nrow(x),dimnames=list(NULL,nom)))
  y<-as.integer(d$clase_ternaria%in%c('BAJA+1','BAJA+2'));dt<-lightgbm::lgb.Dataset(x,label=y,free_raw_data=TRUE)
  m<-lightgbm::lgb.train(params=modifyList(par_base(PARAM$semilla),PARAM$hp_seleccion),data=dt,nrounds=PARAM$hp_seleccion$num_iterations)
  imp<-merge(data.table(Feature=colnames(x)),as.data.table(lightgbm::lgb.importance(m)),by='Feature',all.x=TRUE);imp[is.na(Gain),Gain:=0]
  imp[,es_canarito:=Feature%in%nom];set.seed(PARAM$semilla);imp[,desempate:=runif(.N)];setorder(imp,-Gain,desempate);imp[,id:=.I]
  list(imp=imp,canaritos=ncan)
 })
 imp<-copy(resultado$imp);corte<-mean(imp[es_canarito==TRUE,id])+multiplo*sd(imp[es_canarito==TRUE,id]);imp[,conservar:=!es_canarito&id<corte]
 csv(imp,file.path(RAIZ,'seleccion',paste0('CANARITOS_',hash(f),'_SD',multiplo,'.csv')))
 list(campos=imp[conservar==TRUE,Feature],corte=corte,canaritos=resultado$canaritos)
}
# [Anotación · líneas 230–253] planes_negativos() parte al azar las filas de entrenamiento en 70 % y 30 %
#   dentro de cada mes y clase; si recibe un umbral entrena un modelo auxiliar con el 30 % (2180 iteraciones, 30
#   hojas), puntúa el 70 % y conserva los positivos y los negativos con probabilidad auxiliar menor al umbral.
#   Devuelve las claves cliente-mes y las etiquetas del plan resultante. Los scripts de codigo/ no la invocan.
# Dejo anotado: Filtro opcional, separado del experimento que continúa en Colab.
# Mantengo 30/70 por filas, auxiliares fuera del 70%, positivos conservados dentro del 70%.
planes_negativos<-function(rec,umbral=NULL){
 auxp<-modifyList(par_base(PARAM$semilla),list(feature_fraction_bynode=1,num_iterations=2180L,num_leaves=30L,min_sum_hessian_in_leaf=.1141634103))
 lapply(setNames(c(FALSE,TRUE),c('hist','prod')),function(prod){
  meses<-if(prod)PARAM$train_final else PARAM$train
  cache('seleccion',list(componente='filtro30_v1',rep=rec$rep$id,meses=meses,umbral=umbral,aux=auxp,seed=PARAM$semilla),function(){
   d<-leer_meses(rec$rep,meses);d[,y:=as.integer(clase_ternaria%in%c('BAJA+1','BAJA+2'))];set.seed(PARAM$semilla,kind="L'Ecuyer-CMRG")
   d[,fold:=sample(rep(c(rep(1L,7),rep(2L,3)),length.out=.N)),by=.(foto_mes,clase_ternaria)]
   i30<-which(d$fold==2L);i70<-which(d$fold==1L);stopifnot(length(i30)>0L,length(i70)>0L,length(intersect(i30,i70))==0L)
   pro<-rep(NA_real_,length(i70))
   if(!is.null(umbral)){
    pro<-cache('seleccion',list(componente='aux30_pred_v1',rep=rec$rep$id,meses=meses,aux=auxp,i30=hash(i30),i70=hash(i70)),function(){
     campos<-campos_receta(rec);dt<-lightgbm::lgb.Dataset(data.matrix(d[i30,..campos]),label=d$y[i30],free_raw_data=TRUE)
     m<-lightgbm::lgb.train(params=auxp,data=dt,nrounds=2180L);p<-predict(m,data.matrix(d[i70,..campos]));rm(dt,m);gc(FALSE);p
    })
   }
   keep<-if(is.null(umbral))rep(TRUE,length(i70)) else d$y[i70]==1L|pro<umbral
   aud<-data.table(numero_de_cliente=d$numero_de_cliente[i70],foto_mes=d$foto_mes[i70],y=d$y[i70],prob_aux=pro,conservar=keep)
   csv(aud,file.path(RAIZ,'seleccion',paste0('FILTRO_',if(prod)'prod' else 'hist','_',if(is.null(umbral))'control' else umbral,'.csv')))
   list(key=paste(d$numero_de_cliente[i70][keep],d$foto_mes[i70][keep]),y=d$y[i70][keep])
  })
 })
}
# [Anotación · líneas 254–267] planes_pseudo() entrena un modelo con las clases reales, predice los meses sin
#   clase completa (202105-202106 en histórico, 202107-202108 en producción), asigna etiqueta artificial 1 a las
#   filas con probabilidad mayor o igual a PARAM$pseudo_umbral y devuelve un plan que une filas reales y
#   artificiales. Los scripts de codigo/ no la invocan.
# Dejo anotado: Pseudoetiquetas: mantengo el target verdadero separado; las etiquetas auxiliares nunca son predictors.
planes_pseudo<-function(rec,hp_docente){
 lapply(setNames(c(FALSE,TRUE),c('hist','prod')),function(prod){
  reales<-if(prod)PARAM$train_final else PARAM$train;artificiales<-if(prod)c(202107L,202108L) else c(202105L,202106L)
  cache('seleccion',list(componente='pseudo_v1',rep=rec$rep$id,reales=reales,artificiales=artificiales,hp=hp_docente,corte=PARAM$pseudo_umbral,seed=PARAM$semilla),function(){
   meta<-materializar(rec,prod,FALSE);dt<-lightgbm::lgb.Dataset(meta$bin,params=list(max_bin=31L,feature_pre_filter=FALSE));p<-modifyList(par_base(PARAM$semilla),hp_docente)
   m<-lightgbm::lgb.train(params=p,data=dt,nrounds=p$num_iterations)
   a<-leer_meses(rec$rep,artificiales);pr<-predict(m,data.matrix(a[,meta$campos,with=FALSE]));yr<-as.integer(pr>=PARAM$pseudo_umbral)
   r<-leer_meses(rec$rep,reales)
   csv(data.table(numero_de_cliente=a$numero_de_cliente,foto_mes=a$foto_mes,prob_docente=pr,etiqueta_artificial=yr),file.path(RAIZ,'seleccion',paste0('PSEUDO_',if(prod)'prod' else 'hist','_',rec$rep$id,'.csv')))
   list(key=c(paste(r$numero_de_cliente,r$foto_mes),paste(a$numero_de_cliente,a$foto_mes)),y=c(as.integer(r$clase_ternaria%in%c('BAJA+1','BAJA+2')),yr),meses=c(reales,artificiales))
  })
 })
}
# [Anotación · líneas 268–289] resumir_ensemble() promedia entre modelos, cliente por cliente, el puntaje
#   crudo y la probabilidad (dos modos). Para junio calcula la curva de ganancia del promedio, la ganancia en el
#   corte 11.500, un gráfico entre 8.000 y 15.000 clientes y una tabla de cortes cada 250 con la ganancia media
#   en una ventana de ±250.
resumir_ensemble<-function(resultados,nombre){
 stopifnot(length(resultados)>0L)
 ref<-resultados[[1L]]$scores;ids<-ref$numero_de_cliente
 for(z in resultados)stopifnot(identical(z$scores$numero_de_cliente,ids),identical(z$scores$foto_mes,ref$foto_mes))
 modos<-c('raw','prob');out<-list()
 for(modo in modos){
  s<-Reduce('+',lapply(resultados,function(z)z$scores[[modo]]))/length(resultados)
  tab<-copy(ref[,.(numero_de_cliente,foto_mes,clase_ternaria)]);tab[,score:=s]
  id<-hash(list(modelos=vapply(resultados,`[[`,character(1),'id'),modo=modo));dest<-file.path(RAIZ,'scores',paste0('ENS_',id,'.rds'));atomic(list(nombre=nombre,modo=modo,modelos=vapply(resultados,`[[`,character(1),'id'),tabla=tab),dest)
  gan<-NA_real_
  if(unique(tab$foto_mes)==202106L){
   cv<-curva(ids,s,tab$clase_ternaria);gan<-cv[corte==PARAM$corte,ganancia];csv(cv,file.path(RAIZ,'resultados',paste0('CURVA_ENS_',id,'.csv')))
   png(file.path(RAIZ,'figuras',paste0('GANANCIA_',id,'.png')),width=1300,height=750)
   plot(cv$corte,cv$ganancia,type='l',xlim=c(8000,15000),xlab='Clientes contactados',ylab='Ganancia junio (millones)',main=paste(nombre,modo));abline(v=PARAM$corte,lty=2);dev.off()
   cortes<-cv[corte%in%seq(8000L,15000L,250L)]
   cortes[,ganancia_media_vecindad:=vapply(corte,function(k)mean(cv[corte>=k-250L & corte<=k+250L,ganancia]),numeric(1))]
   csv(cortes,file.path(RAIZ,'resultados',paste0('MESETA_',id,'.csv')))
  }
  out[[modo]]<-list(id=id,nombre=nombre,modo=modo,tabla=tab,ganancia=gan,modelos=vapply(resultados,`[[`,character(1),'id'))
 }
 out
}
# [Anotación · líneas 290–304] confirmar() entrena la configuración devuelta por la búsqueda con todas las
#   semillas de PARAM en modo histórico, resume media y desvío de las ganancias individuales junto con la
#   ganancia de los promedios, y grafica la curva de cada semilla y la del promedio.
confirmar<-function(rec,bo){
 res<-list()
 for(j in seq_along(bo$optimos)){
  hp<-bo$optimos[[j]];xs<-lapply(SEMILLAS,function(s)fit_score(rec,hp,s))
  en<-resumir_ensemble(xs,paste0(rec$nombre,'_HP',j))
  resumen<-data.table(receta=rec$nombre,configuracion=j,n_semillas=length(xs),media=mean(vapply(xs,`[[`,numeric(1),'ganancia')),sd=sd(vapply(xs,`[[`,numeric(1),'ganancia')),ensemble_raw=en$raw$ganancia,ensemble_prob=en$prob$ganancia)
  csv(resumen,file.path(RAIZ,'resultados',paste0('CONF_',rec$nombre,'_',j,'.csv')))
  # Dejo anotado: Gráfico conjunto: ganancias individuales y ganancia del promedio de predicciones.
  png(file.path(RAIZ,'figuras',paste0('SEMILLAS_',rec$nombre,'_',j,'.png')),width=1300,height=750)
  cr<-curva(en$raw$tabla$numero_de_cliente,en$raw$tabla$score,en$raw$tabla$clase_ternaria);plot(cr$corte,cr$ganancia,type='n',xlim=c(8000,15000),xlab='Contactos',ylab='Ganancia junio (millones)',main=paste(rec$nombre,'configuración',j))
  for(x in xs){ci<-curva(x$scores$numero_de_cliente,x$scores$prob,x$scores$clase_ternaria);lines(ci$corte,ci$ganancia,col=adjustcolor('grey40',.4))};lines(cr$corte,cr$ganancia,col='blue',lwd=2);dev.off()
  res[[as.character(j)]]<-list(receta=rec$nombre,hp=hp,individuales=xs,ensemble=en,resumen=resumen)
 }
 res
}
# [Anotación · líneas 305–316] submit() ordena los puntajes de 202108 de mayor a menor (desempate por ID),
#   guarda la tabla ordenada y escribe un archivo con los primeros IDs hasta el corte, uno por línea,
#   verificando que lo escrito coincida con lo calculado. La ruta final no usa esta función: final.R escribe su
#   propio archivo.
submit<-function(en,etiqueta,corte=PARAM$corte){
 d<-copy(en$tabla);stopifnot(all(d$foto_mes==202108L),nrow(d)>=corte,all(is.finite(d$score)),!anyDuplicated(d$numero_de_cliente))
 setorder(d,-score,numero_de_cliente);d[,ranking:=.I]
 csv(d,file.path(RAIZ,'resultados',paste0('SCORES_AGOSTO_',etiqueta,'.csv')))
 dest<-file.path(RAIZ,'submits',paste0('submit_',etiqueta,'_',corte,'.csv'))
 # Dejo anotado: Formateo IDs sin convertirlos a integer de 32 bits ni notación científica.
 ids<-format(d$numero_de_cliente[seq_len(corte)],scientific=FALSE,trim=TRUE,digits=22)
 stopifnot(length(ids)==corte,!anyDuplicated(ids),all(grepl('^[0-9]+$',ids)))
 writeLines(ids,paste0(dest,'.tmp'));if(!file.rename(paste0(dest,'.tmp'),dest))stop('No pude guardar submit')
 stopifnot(identical(readLines(dest),ids));log_('SUBMIT VERIFICADO',dest)
 data.table(nombre=etiqueta,corte=corte,archivo=dest,ensemble=en$id,public_gain=NA_real_,estado='NO ENVIADO; evaluación externa pendiente')
}
# [Anotación · líneas 317–329] ablaciones() reentrena la receta quitando de a una familia de variables (nivel,
#   lags y deltas), mide la diferencia de ganancia de junio contra la receta completa y devuelve recetas
#   candidatas sin las familias cuya exclusión aumentó la ganancia (hasta PARAM$ablaciones_top). Los scripts de
#   codigo/ no la invocan.
# Dejo anotado: Reviso todas las variables originales mediante ablaciones de su familia (nivel + históricos).
# Primero filtro con parámetros fijos; después ajusto sólo las mejores, sin confundir ambas pruebas.
ablaciones<-function(rec,bo){
 hp<-bo$optimos[[1]];base<-fit_score(rec,hp,PARAM$semilla)$ganancia
 variables<-sort(unique(sub('_(delta_)?lag[12]$','',campos_receta(rec))))
 tab<-rbindlist(lapply(variables,function(v){rr<-rec;rr$nombre<-paste0('DROP_',v);rr$excluir<-v;x<-fit_score(rr,hp,PARAM$semilla);data.table(variable=v,ganancia=x$ganancia,delta=x$ganancia-base,modelo=x$id)}))
 setorder(tab,-delta,variable);csv(tab,file.path(RAIZ,'resultados',paste0('ABLACIONES_',rec$nombre,'.csv')))
 mejores<-tab[delta>0,head(variable,PARAM$ablaciones_top)]
 candidatos<-list()
 for(v in mejores){rr<-rec;rr$nombre<-paste0(rec$nombre,'_SIN_',v);rr$excluir<-v;candidatos[[rr$nombre]]<-rr}
 if(length(mejores)>1L){rr<-rec;rr$nombre<-paste0(rec$nombre,'_SIN_CONJUNTO');rr$excluir<-mejores;candidatos[[rr$nombre]]<-rr}
 candidatos
}
# [Anotación · líneas 330–337] auditar_drift() calcula por variable y por mes cantidad de filas, proporción de
#   faltantes y de ceros, cuartiles y cantidad de valores únicos, y lo guarda en CSV; los scripts de codigo/ no
#   la invocan. La última línea comprueba rank_cero con un vector de prueba.
# Audito cambio de distribución de TODOS los campos numéricos, sin usar la baja como filtro.
auditar_drift<-function(d){
 vars<-setdiff(names(d),c('numero_de_cliente','foto_mes','clase_ternaria'));out<-rbindlist(lapply(vars,function(v){d[,{
  x<-get(v);q<-if(all(is.na(x)))rep(NA_real_,3) else as.numeric(quantile(x,c(.25,.50,.75),na.rm=TRUE));list(n=.N,missing=mean(is.na(x)),ceros=mean(x==0,na.rm=TRUE),p25=q[1],mediana=q[2],p75=q[3],unicos=uniqueN(x,na.rm=TRUE))
 },by=foto_mes][,variable:=v]}))
 csv(out,file.path(RAIZ,'auditoria','DISTRIBUCIONES_TODAS_VARIABLES.csv'));out
}
stopifnot(identical(rank_cero(c(NA,0,-20,-10,10,20,20)),c(NA_real_,0,-1,-.5,1/3,5/6,5/6)))
```

### codigo/final.R

Entrena 10 modelos LightGBM con 202103-202106 y 752 predictores, promedia las probabilidades de 202108, escribe los 10.375 clientes de mayor probabilidad y verifica el SHA256 del archivo. Mismo contenido que la celda 11 de la notebook de entrega.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Con reproducir_final en TRUE lee los bloques de 202103-202106 para entrenar y el
#   de 202108 para predecir. Parte de los 752 campos de la receta sin préstamos, agrega las 10 columnas de
#   préstamos personales y quita las 10 de Visa_fultimo_cierre y Master_fultimo_cierre (nivel, lags y deltas):
#   quedan 752 predictores, cuyo orden debe coincidir con referencia/FEATURES.csv. Exige 654.066 filas de
#   entrenamiento, 164.647 clientes en 202108, clases sin faltantes y clientes sin duplicar.
# Entreno la receta que elegí sin modificar el orden de las columnas.
if(SW$reproducir_final) {
 out <- file.path(RAIZ,'final');dir.create(out,recursive=TRUE,showWarnings=FALSE)
 tr <- leer_meses(REP,PARAM$train_final)
 va <- leer_meses(REP,202108L)
 campos_h <- campos_receta(REC_CONTROL,FALSE,FALSE)
 prestamos <- grep('^(cprestamos_personales|mprestamos_personales)($|_)',names(tr),value=TRUE)
 cierres <- grep('^(Visa_fultimo_cierre|Master_fultimo_cierre)($|_)',campos_h,value=TRUE)
 campos <- setdiff(unique(c(campos_h,prestamos)),cierres)
 referencia <- fread(file.path(CARPETA,'referencia','FEATURES.csv'))$campo
 stopifnot(length(campos_h)==752L,length(prestamos)==10L,length(cierres)==10L,
  length(campos)==752L,identical(campos,referencia),nrow(tr)==654066L,
  nrow(va)==164647L,!anyNA(tr$clase_ternaria),!anyDuplicated(va$numero_de_cliente))
# [Anotación · líneas 14–22] Fija un hilo en data.table, arma las matrices de entrenamiento y de 202108, pasa
#   los valores no finitos a NA y define la etiqueta 1 = BAJA+1 o BAJA+2. Construye un lgb.Dataset con max_bin
#   31, feature_pre_filter FALSE y 6 hilos, y libera las tablas.
 setDTthreads(1L)
 x <- data.matrix(tr[,..campos]);xv <- data.matrix(va[,..campos])
 x[!is.finite(x)] <- NA_real_;xv[!is.finite(xv)] <- NA_real_
 y <- as.integer(tr$clase_ternaria%in%c('BAJA+1','BAJA+2'))
 ids <- va$numero_de_cliente
 rm(tr,va);gc(FALSE)
 ds <- lgb.Dataset(x,label=y,params=list(max_bin=31L,
  feature_pre_filter=FALSE,num_threads=6L))
 rm(x);gc(FALSE)
# [Anotación · líneas 23–45] Para cada una de las 10 semillas combina par_base con los hiperparámetros leídos
#   (1907 iteraciones, 77 hojas, min_sum_hessian_in_leaf 2,837), entrena sobre el mismo dataset, predice 202108
#   y guarda MODELO_<semilla>.txt y SCORES_<semilla>.rds con su firma. Si ya existen los puntajes de una semilla
#   con firma e IDs idénticos, los reutiliza en lugar de entrenar. Cada predicción ocupa una columna de la
#   matriz P.
 P <- matrix(NA_real_,length(ids),length(PARAM$semillas))
 for(j in seq_along(PARAM$semillas)) {
  s <- PARAM$semillas[j]
  pars <- modifyList(par_base(s),HP_FINAL)
  firma <- list(raw=RAW_HASH,representacion=REP$id,campos=campos,
   meses=PARAM$train_final,seed=s,pars=pars,versiones=VERSIONES)
  sp <- file.path(out,paste0('SCORES_',s,'.rds'))
  mp <- file.path(out,paste0('MODELO_',s,'.txt'))
  if(file.exists(sp)) {
   anterior <- readRDS(sp)
   stopifnot(identical(anterior$firma,firma),identical(anterior$ids,ids),file.exists(mp))
   pr <- anterior$prob
  } else {
   log_('ENTRENO FINAL',j,'/',length(PARAM$semillas),'semilla',s)
   m <- lgb.train(params=pars,data=ds,nrounds=HP_FINAL$num_iterations)
   pr <- predict(m,xv,params=list(num_threads=6L))
   stopifnot(length(pr)==length(ids),all(is.finite(pr)))
   lgb.save(m,mp)
   atomic(list(firma=firma,ids=ids,prob=pr),sp)
   rm(m);gc(FALSE)
  }
  P[,j] <- pr
 }
# [Anotación · líneas 46–56] Promedia las 10 columnas por cliente, ordena de mayor a menor con desempate por
#   ID creciente y toma los primeros 10.375. Escribe los IDs, uno por línea y sin encabezado, en
#   final/SINCIERRES_PROB10_K10375.csv, calcula su SHA256 y guarda PROBABILIDADES_AGOSTO.csv (todos los
#   clientes) y ENSAMBLE_FINAL.rds.
 # Promedio las probabilidades antes de decidir a quién contacto.
 prob <- rowMeans(P)
 ix <- order(-prob,ids)[seq_len(CORTE_FINAL)]
 elegido <- ids[ix]
 stopifnot(length(elegido)==10375L,!anyDuplicated(elegido))
 archivo <- file.path(out,'SINCIERRES_PROB10_K10375.csv')
 writeLines(format(elegido,scientific=FALSE,trim=TRUE),archivo)
 sha <- digest(file=archivo,algo='sha256')
 fwrite(data.table(numero_de_cliente=ids,prob=prob),file.path(out,'PROBABILIDADES_AGOSTO.csv'))
 atomic(list(ids=ids,prob=prob,campos=campos,hp=HP_FINAL,
  semillas=PARAM$semillas,sha256=sha),file.path(out,'ENSAMBLE_FINAL.rds'))
# [Anotación · líneas 57–64] Detiene la ejecución con un mensaje si el SHA256 obtenido difiere de SHA_FINAL.
#   Si coincide escribe VERIFICACION_FINAL.txt con el hash y la ruta del archivo, lo registra en el log y libera
#   memoria.
 # Dejo anotado: Detengo mi entrega si no reproduje exactamente el archivo enviado.
 if(sha!=SHA_FINAL)stop('CSV distinto al entregado. SHA256 obtenido: ',sha,
  '. No debo subir esta reproducción sin revisar la diferencia.')
 writeLines(c('REPRODUCCION EXACTA: OK',paste('SHA256:',sha),
  paste('Archivo:',archivo)),file.path(out,'VERIFICACION_FINAL.txt'))
 log_('REPRODUCCION EXACTA VERIFICADA',sha)
 rm(ds,xv,P);gc(FALSE)
}
```

### codigo/configuracion.R

Parámetros de la corrida (semillas, meses, límites de la búsqueda), interruptores, corte y SHA256 esperados, resolución de carpetas por variables de entorno, verificación del MD5 del crudo y de las versiones de R y paquetes; al final carga motor.R. Mismo contenido que la celda 5 de la notebook de entrega más la línea que carga el motor.

```r
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Define PARAM: semilla 100613 para la búsqueda de hiperparámetros, lista de 10
#   semillas, 6 hilos, entrenamiento 202103-202104 en la etapa histórica y 202103-202106 en la final, validación
#   en 202106, predicción en 202108, corte 11.500 para medir la ganancia de junio, lags de orden 2,
#   numero_de_cliente y foto_mes incluidos como predictores, y una búsqueda bayesiana de 12 evaluaciones (4
#   iniciales) con límites 512-4096 iteraciones, 8-256 hojas y exponente -3 a 1 para el Hessian mínimo.
# Fijo mi entrega y dejo apagadas las variantes que no elegí.
PARAM <- list(
 semilla=100613L,
 semillas=c(100613L,100267L,101611L,102481L,103651L,104729L,
            105019L,105613L,106013L,106619L),
 threads=6L,train=c(202103L,202104L),
 train_final=c(202103L,202104L,202105L,202106L),
 valid=202106L,future=202108L,corte=11500L,orden_lags=2L,
 incluir_id_mes=TRUE,bo_evaluaciones=12L,bo_iniciales=4L,
 bounds=list(iter=c(512L,4096L),leaves=c(8L,256L),logh=c(-3,1)),
 top_configuraciones=1L,rank_campos=character()
)
# [Anotación · líneas 13–25] Define los interruptores SW: reproducir_final en TRUE y los otros 19 en FALSE.
#   Fija el corte de la entrega en 10.375 clientes (CORTE_FINAL) y el SHA256 esperado del archivo de salida
#   (SHA_FINAL).
SW <- list(
 reproducir_final=TRUE,bo_origen=FALSE,
 control=FALSE,rankings=FALSE,artificiales_original=FALSE,
 artificiales_rank=FALSE,rank_montos=FALSE,target_baja2=FALSE,
 tarjetas=FALSE,solo_visa=FALSE,solo_master=FALSE,
 vinculacion=FALSE,sin_cierres_historico=FALSE,
 rank_zero_tend3=FALSE,bo_sin_cierres_nueva=FALSE,
 diagnosticos_ens5=FALSE,cortes_historicos=FALSE,
 mezcla_control_rank=FALSE,visa_comparaciones=FALSE,
 sin_cierres_comparaciones=FALSE
)
CORTE_FINAL <- 10375L
SHA_FINAL <- '7715cbb9568462c2a1f9b0534528fbce3f77c54cd43a255c59476dc9a37b5caa'
# [Anotación · líneas 26–34] Resuelve la carpeta de la entrega (DMEYF_ENTREGA o el directorio actual) y exige
#   que contenga codigo/motor.R; define la carpeta de salida (DMEYF_SALIDA o salida/) y la ruta del crudo
#   (DMEYF_DATOS o datos/competencia_01_crudo.csv). Detiene la ejecución si el archivo no existe o si su MD5 no
#   es b6f759764c5d04cbf068548517ae1249.
CARPETA <- normalizePath(Sys.getenv('DMEYF_ENTREGA',unset=getwd()),mustWork=TRUE)
if(!file.exists(file.path(CARPETA,'codigo','motor.R')))
 stop('Debo ejecutar desde la carpeta de entrega o definir DMEYF_ENTREGA.')
RAIZ_NUEVA <- Sys.getenv('DMEYF_SALIDA',unset=file.path(CARPETA,'salida'))
RAW_NUEVO <- Sys.getenv('DMEYF_DATOS',unset=file.path(CARPETA,'datos','competencia_01_crudo.csv'))
if(!file.exists(RAW_NUEVO)) stop('Debo indicar DMEYF_DATOS con el dataset crudo.')
if(unname(tools::md5sum(RAW_NUEVO))!='b6f759764c5d04cbf068548517ae1249')
 stop('El crudo no coincide con el dataset de la corrida final.')
Sys.setenv(DMEYF_RAIZ=RAIZ_NUEVA,DMEYF_DATOS=RAW_NUEVO)
# [Anotación · líneas 35–44] Agrega /home/ds/.local/lib/R/site-library a las rutas de paquetes si esa carpeta
#   existe, exige data.table, lightgbm, digest, jsonlite y filelock, y detiene la ejecución si las versiones no
#   son R 4.6.1, lightgbm 4.7.0.99 y data.table 1.18.6.1. Al final carga codigo/motor.R.
if(dir.exists('/home/ds/.local/lib/R/site-library'))
 .libPaths(unique(c('/home/ds/.local/lib/R/site-library',.libPaths())))
paquetes <- c('data.table','lightgbm','digest','jsonlite','filelock')
faltan <- paquetes[!vapply(paquetes,requireNamespace,logical(1),quietly=TRUE)]
if(length(faltan)) stop('Debo instalar estos paquetes: ',paste(faltan,collapse=', '))
library(lightgbm)
stopifnot(as.character(getRversion())=='4.6.1',
 as.character(packageVersion('lightgbm'))=='4.7.0.99',
 as.character(packageVersion('data.table'))=='1.18.6.1')
source(file.path(CARPETA,'codigo','motor.R'),local=.GlobalEnv)
```


## Explicaciones del alumno (texto original)

### ESTADO_VALIDACION.json

> {
>   "notebooks_formato": "OK",
>   "python_sintaxis": "OK",
>   "R_sintaxis_nativa": "OK (parser R 4.3.3; validación R 4.6.1 incluida para VM)",
>   "hp_procedencia": "OK",
>   "semillas_columnas": "OK",
>   "csv_referencia_sha256": "OK",
>   "replica_desde_crudo": "VERIFICADA: SHA256 EXACTO",
>   "corte": 10375,
>   "publico": 106.3975,
>   "submit_K10375": "1537-1791756238380992",
>   "ultimo_submit_confirmado": "K11500; falta reenvío K10375",
>   "verificacion_finalizada_buenos_aires": "2026-10-11 22:45:49"
> }

### VERIFICACION_FINAL.txt

> REPRODUCCION EXACTA: OK
> SHA256: 7715cbb9568462c2a1f9b0534528fbce3f77c54cd43a255c59476dc9a37b5caa
> Archivo: /home/ds/buckets/b1/exp/ENTREGA_REPLICA_K10375/salida_verificacion/final/SINCIERRES_PROB10_K10375.csv

### README.md

> # Mi entrega — Competencia DMEyF
>
> Soy Nicky Baranek. Mi predicción elegida es `SINCIERRES_PROB10_K10375.csv`.
>
> ## Mi secuencia de ejecución
>
> 1. Descomprimo esta carpeta y mantengo su estructura. Ubico el dataset crudo en `datos/competencia_01_crudo.csv`, o defino `DMEYF_DATOS` con su ruta absoluta.
> 2. Abro `DMEyF_Nicky_Entrega_Final.ipynb` en esa carpeta. Ejecuto la sección 1 con Python. Cambio al kernel R y ejecuto la sección 2 en orden: configuración, funciones, preparación, entrenamiento y ensamble, experimentos y cortes.
> 3. Dejo `reproducir_final=TRUE` y todos los demás switches en `FALSE`. Mantengo seis hilos en LightGBM. No activo los experimentos descartados para generar mi entrega.
> 4. Obtengo el archivo en `salida/final/SINCIERRES_PROB10_K10375.csv`. Mi código verifica el SHA256 y se detiene si no coincide con el archivo entregado.
>
> También puedo ejecutar la misma ruta con R, sin abrir Jupyter:
>
> ```bash
> DMEYF_DATOS=/ruta/competencia_01_crudo.csv Rscript --vanilla REPRODUCIR_FINAL.R
> ```
>
> Ejecuto ese comando desde la carpeta de entrega. Si necesito otra ubicación para las salidas, defino `DMEYF_SALIDA`; para cambiar la carpeta del código, defino `DMEYF_ENTREGA`.
>
> ## Mi modelo elegido
>
> - Reconstruyo el target por presencia mensual: BAJA+1/BAJA+2 = 1 y CONTINUA = 0.
> - Corrijo `ccajas_depositos` de 202105 asignando NA.
> - Calculo lags calendario de orden 1 y 2 y sus deltas; mantengo ausencias mensuales como NA.
> - Mantengo el orden exacto de las columnas. Incluyo `numero_de_cliente` y `foto_mes` como predictores, igual que en la corrida original.
> - Durante la BO de origen retiro préstamos personales y sus lags/deltas. En producción los restauro y retiro la familia completa de `Visa_fultimo_cierre` y `Master_fultimo_cierre`: diez columnas.
> - Conservo `Visa_status`, `Master_status` y sus lags/deltas. No agrego transiciones adicionales, rankings, flags zero, tendencias ni etiquetas artificiales al modelo final.
> - Entreno 202103, 202104, 202105 y 202106 sin undersampling: 654.066 filas y 752 predictores. Predigo 202108: 164.647 clientes.
> - Uso 1907 iteraciones, 77 hojas y Hessian mínimo 2,83699883991516. Conservo la métrica `average_precision` del entrenamiento que efectivamente generó la entrega. No uso early stopping.
> - Entreno las diez semillas 100613, 100267, 101611, 102481, 103651, 104729, 105019, 105613, 106013 y 106619.
> - Promedio sus probabilidades con pesos iguales, ordeno de mayor a menor y desempato por ID creciente. Selecciono 10.375 IDs y escribo una columna, sin encabezado, con salto de línea final.
>
> Mi SHA256 esperado es:
>
> `7715cbb9568462c2a1f9b0534528fbce3f77c54cd43a255c59476dc9a37b5caa`
>
> ## Mi optimización de origen
>
> Incluyo `BO_Origen.ipynb`, el código del motor y los archivos FIRMA/HISTORIAL/TERMINADO de la BO que produjo los HP usados. La BO ORIGINAL_LAG2 es `52fc1b5d908fb495ce06d1ed3038defbaf9a2609d2ea0bc80904d2ba8b58c6ed`.
>
> Entrené marzo–abril y evalué junio con ganancia en K11500, cuatro puntos iniciales y ocho propuestas de mejora esperada. Elijo los HP del historial efectivo, no de una búsqueda posterior. Si quiero volver a correr esa búsqueda, ejecuto `BO_Origen.ipynb` en una salida vacía; esa notebook activa `bo_origen=TRUE` y apaga producción.
>
> No uso la BO posterior de Sin cierres, de 1130 iteraciones: su ensayo público dio 98,89 M en K10500 y la descarté. La conservo como experimento.
>
> ## Mi ambiente
>
> Reproduzco en Linux x86_64 con R 4.6.1, LightGBM 4.7.0.99 y data.table 1.18.6.1. El código verifica esas versiones antes de entrenar. No actualizo LightGBM durante la réplica ni lo reemplazo silenciosamente por 4.7.0.
>
> Para la ruta final necesito `data.table`, `lightgbm`, `digest`, `jsonlite` y `filelock`. Para las BO necesito además `mlrMBO` 1.1.6, `DiceKriging` 1.6.1, `mlr`, `ParamHelpers` y `smoof`. Uso Python para la carga y R para preparar, entrenar y predecir. No necesito servicios externos, credenciales de GCP ni checkpoints de otra VM para ejecutar la ruta final.
>
> Guardo `sessionInfo()` en la salida. Para comprobar sintaxis en mi ambiente ejecuto:
>
> ```bash
> Rscript --vanilla VALIDAR_SINTAXIS.R
> ```
>
> ## Mis experimentos
>
> Conservo los resultados originales en `evidencia/`, los historiales de BO en `procedencia_bo/` y las fuentes anteriores en `procedencia/`. Documenté mis decisiones en `REGISTRO_EXPERIMENTOS.csv`.
>
> Mis switches incluyen control, rankings completos, ranking de montos, etiquetas artificiales originales y con rankings, target BAJA+2, tarjetas juntas, Visa sola, Master sola, vinculación, Sin cierres histórico, ranking con zero/tendencias, BO posterior, mezcla control/ranking, ensambles de cinco, comparaciones y cortes históricos.
>
> Si activo una variante, construyo sus controles en `salida/laboratorio` y no reemplazo mi CSV final. Para comparaciones de Visa activo `visa_comparaciones`; para las de Sin cierres activo `sin_cierres_comparaciones`. Esas opciones activan sus históricos necesarios. Para los cortes de junio activo `cortes_historicos`, que activa Sin cierres histórico. No ejecuto todas las variantes para entregar: consumen muchas horas.
>
> En `rank_zero_tend3` corrijo el parámetro anidado de Dataset que había emitido un warning; conservo la receta y un hilo. Distingo esta corrección de sintaxis del resultado histórico registrado.
>
> Mis grupos ENS5 comparten modelos; no los interpreto como veinte pruebas independientes. Junio fue reutilizado para desarrollar y seleccionar. El público no permite conocer la curva privada.
>
> ## Mi estado de verificación
>
> Verifiqué la estructura de las notebooks, la sintaxis Python, la sintaxis R y la procedencia de los HP. La reproducción desde el crudo queda confirmada únicamente cuando obtengo `salida/final/VERIFICACION_FINAL.txt` con el SHA256 esperado. Hasta entonces no presento la revisión estática como una ejecución completa.
>
> El archivo de `referencia/` permite contrastar la salida y su hash; no lo utilizo para generar las probabilidades ni para sustituir el entrenamiento.
>
>
> ## Mi reproducción confirmada
>
> Verifiqué la ejecución desde el crudo el 11/10/2026 a las 22:45:49 de Buenos Aires. Los diez modelos generaron exactamente el CSV elegido. Dejo la constancia en VERIFICACION_FINAL.txt.

