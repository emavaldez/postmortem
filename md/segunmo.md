# segunmo — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: segunmo
- Repositorio: https://github.com/segunmo/DM-EyF-2026
- Link posteado: https://github.com/segunmo/DM-EyF-2026/blob/main/competencia/REPRODUCIR.md
- Commit: b8a68483d7e81100591c44e1ec53ca13fa5d04b7
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/segunmo/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/segunmo.json

## Resumen

Repositorio en Python cuya carpeta competencia/ contiene módulos comunes (src/), 47 carpetas de experimentos numeradas, una bitácora (LOG.md), un registro de envíos y un instructivo (REPRODUCIR.md, el archivo posteado). Según ese instructivo, la entrega es exp031_final_w67_md_k12000.csv: 12.000 clientes elegidos por una mezcla de ranks de cuatro componentes LightGBM entrenados con 202103–202106 y puntuados sobre 202108. El componente de mayor peso (2/3), llamado M2, es un multiclase CONTINUA/BAJA+1/BAJA+2 con 855 columnas (variables originales, 43 variables del mes, lag1, lag2, deltas y cocientes contra meses anteriores), 3 configuraciones de hiperparámetros de Optuna × 10 semillas y puntaje P(BAJA+2)/(1−P(BAJA+1)). El tercio restante combina 017 (6 configuraciones × 30 semillas, con un binario auxiliar de BAJA+1 que suma 202107), 010 (6 configuraciones × 6 semillas) y 8 modelos con hiperparámetros fijos y sin submuestreo. Los datos se preparan con DuckDB (clase ternaria por SQL y parquet), ccajas_depositos se anula en 202105 y en M2 se excluyen 8 columnas (6 de delta 2 y 2 de lag 2) con PSI mayor que 0,20.

**Qué entrega.** Un CSV sin encabezado con 12.000 numero_de_cliente (exp031_final_w67_md_k12000.csv). Según REPRODUCIR.md y submissions/REGISTRO.md, es el único archivo del último envío, con 103,21 M en el Public. El CSV no está en el repositorio: el .gitignore excluye competencia/submissions/*.csv.

**Cómo se ejecuta.** REPRODUCIR.md §1 y §3, desde la raíz del repositorio y con un entorno virtual de Python 3.14: pip install -r requirements-lock.txt; competencia/preparar_datos.py (descarga el CSV crudo y arma clase_ternaria y el parquet); competencia/verificar_determinismo.py; luego, en orden, 017_final/final.py --semillas 30 --k 11000 --lag2; 010_multiclase/final.py; 024_final_receta/final_rec.py --semillas 8; 031_final_todas_lags/final_m2.py --semillas 10 --min_data 50,65,80; 031_final_todas_lags/blend_m2.py 0.6667 12000 scores_m2_md50-65-80_202108.csv; y competencia/verificar_modelos.py. El texto estima ≈ 6 h 35 min de cómputo secuencial e indica borrar tmp/ o usar un clon nuevo para reentrenar. §4 agrega los pasos para rehacer la selección de columnas y Optuna (≈ 8 h más).

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Tres clases (CONTINUA = 0, BAJA+1 = 1, BAJA+2 = 2) en los modelos principales; el puntaje de cada cliente es P(BAJA+2) / (1 − P(BAJA+1)). En el componente 017, P(BAJA+1) sale de un modelo binario auxiliar (positivo = BAJA+1) entrenado con 202103–202107; 202107 sólo entra en ese auxiliar.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106, 202107
- **Meses de validación:** 202105, 202106, 202107
- **Mes que predice:** 202108
- **Submuestreo:** En los modelos con hiperparámetros de Optuna (017, 010 y M2) se conservan todas las filas BAJA+1 y BAJA+2 y cada fila CONTINUA con probabilidad r, sorteada con RandomState(semilla); r es propio de cada configuración (entre 0,096 y 0,106 en mejores_trials.json). En el auxiliar de 017 se conservan los BAJA+1 y el resto con probabilidad r. Los 8 modelos de 024 entrenan con todas las filas (r = 1,0).
- **Calidad de datos:** ccajas_depositos se reemplaza por NULL sólo en 202105 al crear la vista de DuckDB (config.CORREGIR_CCAJAS = True en los scripts del final). Los nulos no se imputan. REPRODUCIR.md §9 menciona un chequeo sin duplicados de (cliente, mes).
- **Drifting:** En M2 se calcula el PSI de cada columna terminada en _lag2 o _d2 entre las filas de entrenamiento de 202105–202106 y las de 202108, y se excluyen las de PSI mayor que 0,20 (8 columnas, listadas en drop_psi.txt). El camino de la entrega no aplica rank, deflación ni estandarización por mes; esas transformaciones aparecen en experimentos (027, 037c, 011).
- **Variables dentro del mes:** 17 columnas r_* (cocientes entre variables del mismo mes y una suma de consumos de tarjetas) y 26 columnas n_* (sumas, restas y cocientes por grupos: ingresos, egresos, inversiones, deuda, patrimonio, límites y saldos de tarjetas, comisiones, transacciones digitales y físicas, productos con valor mayor que 0).
- **Variables históricas:** Pool de M1: lag1, delta1 (v − lag1) y ratio1 (v/lag1 − 1) de 50 variables; en 017 se agregan lag2, delta2 y ratio2 de esas 50. M2 agrega además lag1 y delta1 de otras 92 variables y lag2 y delta2 de las 142: 863 columnas antes del filtro de PSI y 855 después. Los lags salen de un join por cliente y mes anterior y quedan en NaN si el cliente no estaba o el mes no existe.
- **Selección de variables:** M1: las 150 columnas de mayor importancia (gain relativo medio de 5 semillas en un modelo binario al que se agregan 20 canaritos, que se quitan del ranking) sobre el pool de 345 columnas con 202103–202106 (top150_final.txt). Las 50 variables con historia salen de un ranking de importancia de 003a y las 142 de M2 de un ranking de 008c, en ambos casos sin fechas en días, cierres de tarjeta, edad ni antigüedad. M0 son las 178 columnas sin historia. M2 usa todas sus columnas salvo las 8 excluidas por PSI.
- **Optimización de hiperparámetros:** Optuna (TPESampler multivariado con semilla 771227 y pruner por percentil 75), dos estudios (M0 y M1) alternados durante un presupuesto de horas (8 por defecto). Cada trial entrena un binario BAJA+2 en los folds A (202103 → 202105) y B (202103–04 → 202106) con 2 semillas y devuelve la media de ganancia / referencia, con la ganancia promediada en k = 8.000…15.000. Los 3 trials de mayor valor de cada estudio quedan en mejores_trials.json y se reutilizan en multiclase. En M2, min_data_in_leaf se pasa por línea de comando (50, 65, 80; valores probados en 032 y 033). Los modelos de 024 usan hiperparámetros fijos; según su README, 512 hojas y 800 rondas provienen de la grilla de 021.
- **Hiperparámetros finales:** M2, tres configuraciones M1 de mejores_trials.json: top1 con r 0,0986, 688 rondas, 160 hojas, learning_rate 0,0101, feature_fraction 0,129, bagging_fraction 0,771 y min_data_in_leaf 50; top2 con r 0,0961, 624 rondas, 144 hojas, learning_rate 0,0122, feature_fraction 0,221, bagging_fraction 0,815 y min_data_in_leaf 65; top3 con r 0,1040, 718 rondas, 194 hojas, learning_rate 0,0129, feature_fraction 0,155, bagging_fraction 0,826 y min_data_in_leaf 80; todas con max_bin 31, bagging_freq 1, deterministic y force_row_wise. Modelos de 024: 512 hojas, learning_rate 0,005, 800 rondas, min_data_in_leaf 0, min_sum_hessian_in_leaf 0,05, feature_fraction 0,5, feature_fraction_bynode 0,2 y max_bin 31.
- **Semillas:** 5 semillas propias escritas en config.py (852583, 771227, 676057, 482687, 399221) y 25 derivadas de la primera con RandomState(852583).randint, listadas literalmente y verificadas con una aserción al importar. Cada script toma las primeras n: 30 en 017, 6 en 010, 8 en 024 y 10 por configuración en M2. La semilla fija el sorteo del submuestreo y el parámetro seed de LightGBM.
- **Cantidad de semillas:** 30
- **Ensamble:** Cuatro componentes sobre 202108; dentro de cada uno se promedian los puntajes entre semillas por configuración y luego los ranks entre configuraciones: 017 (6 configuraciones × 30 semillas, cada una con modelo principal y auxiliar: 360 modelos), 010 (6 × 6 = 36), 024 (8) y M2 (3 × 10 = 30). blend_m2.py combina ranks: 2/3 de M2 y 1/3 del rank de [rank(017 + 010) + 024]. Pesos aproximados según REPRODUCIR.md: M2 67 %, 024 17 %, 017 8 % y 010 8 %.
- **Corte:** Cantidad fija: los 12.000 clientes de mayor puntaje final (argumento k de blend_m2.py). REPRODUCIR.md cita como apoyo la curva local de ganancia por k de 015 (folds A, B y Bh), la estimación de positivos de 018 y una curva de k medida en el Public con 5 envíos de 5 archivos (025).
- **Validación:** Folds por mes futuro, sin validación cruzada: A (202103 → 202105), B (202103–04 → 202106), Bh (202104 → 202106), L (202105 → 202106) y B2 (202104–05 → 202106); en 036 y 037, entrenamiento con 202103–06 y validación en 202107 con BAJA+1 como etiqueta. Métrica: ganancia acumulada (1.072.500 por acierto, −27.500 por cada otro envío) promediada en k = 8.000…15.000, con diferencias pareadas por semilla. Los scripts del final no validan: entrenan con 202103–202106 y puntúan 202108.
- **Salidas:** competencia/submissions/exp031_final_w67_md_k12000.csv (12.000 numero_de_cliente, sin encabezado, uno por línea). Intermedios: tmp/*.npy por configuración y semilla, tmp/scores_*.csv por componente, modelos en artifacts/modelos_final/ y huellas en competencia/modelos_manifiesto.csv; ninguno de ellos ni los CSV de envío están en el repositorio (el .gitignore excluye data/, artifacts/, tmp/ y submissions/*.csv). Sí están drop_psi.txt y los log.txt de cada corrida.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Tres clases (CONTINUA, BAJA+1, BAJA+2) (`clase.multiclase`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Optuna (`hiperparametros.optuna`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Búsqueda en grilla o al azar (`hiperparametros.grilla_o_azar`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)
- El repositorio declara el uso de asistentes de IA (`proceso.uso_de_ia_declarado`)

## Técnicas sólo exploradas

- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Deflación por IPC, dólar o UVA (`drifting.deflacion`)
- Estandarización o normalización por mes (`drifting.estandarizacion_por_mes`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Random Forest (`modelo.random_forest`)
- Corta por umbral de probabilidad (`corte.umbral_probabilidad`)
- Genera archivos con varios cortes (`corte.varios_cortes`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: no
- Entorno declarado: Python 3.14; requirements-lock.txt (raíz del repositorio) fija versiones exactas, entre ellas lightgbm 4.7.0, duckdb 1.5.5, pandas 3.0.5, numpy 2.5.3, scipy 1.18.1 y optuna 5.0.0, y dice que se generó con Python 3.14.2 en macOS. REPRODUCIR.md pide ~16 GB de RAM y ~12 GB de disco, informa tiempos medidos en una máquina de 10 núcleos y declara que no se verificó en otro sistema operativo ni arquitectura. Los docstrings de uso anteponen el comando caffeinate de macOS.

## Pasos del camino de la entrega

1. **Preparación de los datos.** preparar_datos.py descarga competencia_01_crudo.csv si no está en data/, construye clase_ternaria con una consulta SQL en DuckDB (presencia del cliente uno y dos meses después) y guarda competencia_01.csv y competencia_01.parquet.gzip. Con esa consulta 202107 queda sólo con BAJA+1 conocida y 202108 sin clase. (`competencia/preparar_datos.py` líneas 14–30; `competencia/preparar_datos.py` líneas 45–51)
2. **Carga con orden fijo y corrección de ccajas_depositos.** data.py crea una vista de DuckDB sobre el parquet; con CORREGIR_CCAJAS en True deja ccajas_depositos en NULL en 202105. Toda carga se ordena por foto_mes y numero_de_cliente, porque el submuestreo sortea por posición de fila. (`competencia/src/data.py` líneas 9–26; `competencia/src/config.py` líneas 50–56)
3. **Semillas.** config.py lista 5 semillas propias y 25 derivadas de la primera; semillas(n) entrega las primeras n y una aserción verifica al importar que las derivadas coinciden con su generador. (`competencia/src/config.py` líneas 21–48)
4. **Pool de 345 columnas.** pool.py carga los meses con el lag1 de 50 variables (join por cliente y mes anterior), agrega delta1 y ratio1, 17 columnas r_* y 26 columnas n_* calculadas con datos del mismo mes. (`competencia/experimentos/004_seleccion_variables/pool.py` líneas 12–25; `competencia/src/historia.py` líneas 20–28; `competencia/src/historia.py` líneas 42–57; `competencia/src/features.py` líneas 75–100; `competencia/src/features.py` líneas 112–148)
5. **Lista de 150 columnas (M1).** 005_optuna/seleccion.py entrena, por conjunto de meses, modelos binarios con 20 canaritos y 5 semillas, promedia el gain relativo y guarda las 150 primeras columnas que no son canaritos; la lista calculada con 202103–202106 es top150_final.txt. (`competencia/experimentos/005_optuna/seleccion.py` líneas 14–25; `competencia/src/seleccion.py` líneas 16–31)
6. **Búsqueda de hiperparámetros y elección de 6 configuraciones.** optuna_run.py alterna trials de dos estudios (M0 y M1): cada trial sortea r y 8 hiperparámetros, entrena un binario BAJA+2 en los folds A y B con 2 semillas y devuelve la media de ganancia / referencia. reevaluar.py ordena los trials completos y toma los 3 de mayor valor por estudio; 005_optuna/final.py los escribe en mejores_trials.json. (`competencia/experimentos/005_optuna/optuna_run.py` líneas 70–99; `competencia/experimentos/005_optuna/optuna_run.py` líneas 114–144; `competencia/experimentos/005_optuna/reevaluar.py` líneas 34–46; `competencia/experimentos/005_optuna/final.py` líneas 23–27; `competencia/experimentos/005_optuna/mejores_trials.json` líneas 1–68)
7. **Componente 017: multiclase con auxiliar de BAJA+1 y lag2.** Con --semillas 30 --k 11000 --lag2: para cada una de las 6 configuraciones y 30 semillas entrena un multiclase con 202103–202106 y un binario de BAJA+1 con 202103–202107; el puntaje sobre 202108 es P2 del multiclase / (1 − P1 del auxiliar). Promedia por semillas, luego promedia los ranks de las 6 configuraciones y guarda tmp/scores_202108_conlag2.csv. (`competencia/experimentos/017_final/final.py` líneas 66–100)
8. **Componente 010: multiclase sin auxiliar ni lag2.** Las mismas 6 configuraciones con 6 semillas cada una, entrenadas con 202103–202106; el puntaje es P2 / (1 − P1) del propio multiclase. Guarda el rank medio en tmp/proba_202108.csv. (`competencia/experimentos/010_multiclase/final.py` líneas 47–77)
9. **Componente 024: hiperparámetros fijos sin submuestreo.** 8 modelos multiclase (uno por semilla) con 512 hojas, learning_rate 0,005 y 800 rondas sobre las 150 columnas M1 y todas las filas de 202103–202106; guarda el promedio de puntajes y su rank en tmp/scores_rec_202108.csv. (`competencia/experimentos/024_final_receta/final_rec.py` líneas 25–27; `competencia/experimentos/024_final_receta/final_rec.py` líneas 44–55)
10. **Columnas de M2.** construir() de 028_todas_lags/run.py parte del pool de 345 columnas y agrega lag2, delta2 y ratio2 de las 50 variables, lag1 y delta1 de otras 92 y lag2 y delta2 de esas 92: 863 columnas, pasadas a float32. (`competencia/experimentos/028_todas_lags/run.py` líneas 38–51; `competencia/src/historia.py` líneas 31–39)
11. **Filtro por PSI y entrenamiento de M2.** final_m2.py calcula el PSI de las columnas _lag2 y _d2 entre 202105–202106 y 202108 y quita las que superan 0,20 (8 columnas). Con las 855 restantes entrena, para las 3 configuraciones M1 (min_data_in_leaf 50, 65 y 80) y 10 semillas, un multiclase con submuestreo de CONTINUA; promedia P2 / (1 − P1) por semillas y los ranks de las 3 configuraciones. (`competencia/experimentos/031_final_todas_lags/final_m2.py` líneas 36–72; `competencia/src/drift.py` líneas 15–27; `competencia/src/multiclase.py` líneas 17–28)
12. **Caché por modelo, modelos guardados y huellas.** Cada predicción por configuración y semilla se guarda en tmp/ como .npy y se reutiliza si existe; modelos.py guarda cada booster, registra su SHA-256 y el de su predicción en un manifiesto y verifica que el orden de clientes de la caché coincida con el actual. (`competencia/src/modelos.py` líneas 39–67)
13. **Mezcla por rank y corte en 12.000.** blend_m2.py lee los ranks de los cuatro componentes, reconstruye rank(017 + 010) y luego rank de esa mezcla más 024, y calcula 0,6667 · rank de M2 + 0,3333 · esa mezcla. Toma los 12.000 clientes de mayor valor y escribe exp031_final_w67_md_k12000.csv con las validaciones de guardar_submit(). (`competencia/experimentos/031_final_todas_lags/blend_m2.py` líneas 15–43; `competencia/src/submit.py` líneas 17–40)
14. **Verificaciones.** verificar_determinismo.py compara la huella del orden de filas con un valor esperado y la predicción de un modelo entrenado con 1 hilo y con todos; verificar_modelos.py compara las huellas de los modelos guardados con las del manifiesto. (`competencia/verificar_determinismo.py` líneas 18–32; `competencia/verificar_modelos.py` líneas 10–24)

## Archivos

- `competencia/GLOSARIO.md` · explicacion · Markdown · 194 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/GLOSARIO.md.txt) — Glosario en 12 secciones: problema y métrica, folds, estadística de las comparaciones, conjuntos de columnas M0, M1 y M2, variables construidas, hiperparámetros, ensambles, drift, leaderboard, sesgos metodológicos, lectura de tablas y nombres de archivos, y reproducibilidad.
- `competencia/verificar_determinismo.py` · secundario · Python · 32 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/verificar_determinismo.py.txt) — Verificación previa del instructivo (§1): compara el orden de filas con una huella esperada y la predicción de un modelo entrenado con 1 hilo y con todos los hilos. No genera predicciones para el envío.
- `competencia/preparar_datos.py` · principal · Python · 51 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/preparar_datos.py.txt) — Descarga el CSV crudo, construye clase_ternaria con SQL en DuckDB y genera el CSV con clase y el parquet que leen los demás scripts.
- `competencia/README.md` · explicacion · Markdown · 47 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/README.md.txt) — Presentación de la carpeta competencia/: estructura de src/, experimentos/ y submissions/, flujo de trabajo por experimento, formato del envío por Zulip y reglas. Remite a ../CLAUDE.md para el problema, la función de ganancia y las reglas de integridad.
- `competencia/LOG.md` · explicacion · Markdown · 62 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/LOG.md.txt) — Bitácora con una fila por experimento (de 001 a 038-rep2, la más reciente arriba): cambio probado, meses de entrenamiento y validación, ganancia local, puntaje público y conclusión. Las filas 038-rep y 038-rep2 registran una auditoría de reproducibilidad: según el texto, el envío no se regenera idéntico (coincide 94–95 % del top-12000 por modelo) y, con ORDER BY y deterministic agregados, dos corridas independientes dan modelos idénticos.
- `competencia/REPRODUCIR.md` · explicacion · Markdown · 97 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/REPRODUCIR.md.txt) — Archivo posteado. Identifica el envío final y su composición, da los comandos para preparar datos y regenerarlo (§1 y §3), indica qué está versionado (§2), los pasos para rehacer la selección de columnas y Optuna (§4), una tabla de decisiones con el experimento que cita como evidencia (§5), lo descartado (§6), el Public de cada envío (§7) y los riesgos que el texto declara sin resolver (§8 y §9). Remite a secciones §0 y §0b que no figuran en el archivo en este commit.
- `competencia/PLAN.md` · explicacion · Markdown · 75 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/PLAN.md.txt) — Plan de trabajo fechado el 2026-10-03 con su estado final: decisiones tomadas, esquema de validación con los folds A y B, tabla de experimentos previstos (002 a 008), estrategia de envíos, riesgos y una actualización del 2026-10-07 con el diseño del auxiliar de BAJA+1 (014).
- `competencia/verificar_modelos.py` · secundario · Python · 24 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/verificar_modelos.py.txt) — Verificación final del instructivo (§3.6): compara las huellas de los modelos guardados con las del manifiesto. El manifiesto competencia/modelos_manifiesto.csv no figura entre los archivos del repositorio en este commit.
- `competencia/COBERTURA.md` · explicacion · Markdown · 149 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/COBERTURA.md.txt) — Matriz que cruza lo propuesto por varias fuentes (mensaje del docente, libro de la cátedra, compañeros, carpeta research/) con el experimento que lo probó; plan 037 con reglas fijadas de antemano (semillas pareadas en 202107, Benjamini–Hochberg con q = 0,10 y mínimo de +3 M) y tabla de resultados de 9 pruebas, ninguna de las cuales cumple la regla según el texto.
- `competencia/submissions/REGISTRO.md` · explicacion · Markdown · 23 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/submissions/REGISTRO.md.txt) — Tabla de envíos al bot entre el 2026-10-03 y el 2026-10-09: nombre, archivos, experimento, cantidad de clientes, ganancia local y media y desvío del Public. Indica como envío final exp031_final_w67_md_k12000.csv, con 103,2075 M en el Public.
- `competencia/experimentos/037_huecos_de/run.py` · secundario · Python · 94 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_huecos_de/run.py.txt)
- `competencia/experimentos/037_huecos_de/README.md` · secundario · Markdown · 19 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_huecos_de/README.md.txt)
- `competencia/experimentos/037_huecos_de/log.txt` · secundario · Texto · 25 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_huecos_de/log.txt.txt)
- `competencia/experimentos/008c_lags_150/run.py` · secundario · Python · 90 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/008c_lags_150/run.py.txt)
- `competencia/experimentos/008c_lags_150/variables_150.txt` · configuracion · Texto · 142 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/008c_lags_150/variables_150.txt.txt) — Lista de 142 variables (las 50 anteriores más 92) que M2 usa para lag1, lag2 y diferencias. Según 008c_lags_150/run.py, las 92 salen del ranking sel/importancias_Bh.csv restringido a originales numéricas, con las mismas exclusiones de 003a.
- `competencia/experimentos/008c_lags_150/README.md` · secundario · Markdown · 31 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/008c_lags_150/README.md.txt)
- `competencia/experimentos/010_multiclase/run.py` · secundario · Python · 90 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/010_multiclase/run.py.txt)
- `competencia/experimentos/010_multiclase/final.py` · principal · Python · 87 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/010_multiclase/final.py.txt) — Componente 010 de la mezcla: las 6 configuraciones en multiclase, sin auxiliar ni lag2, con 6 semillas cada una. Deja tmp/proba_202108.csv.
- `competencia/experimentos/010_multiclase/final_log.txt` · secundario · Texto · 11 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/010_multiclase/final_log.txt.txt) — Registro de la corrida de 010_multiclase/final.py del 2026-10-07: 3.985 filas BAJA+1 y 4.067 BAJA+2 en el entrenamiento, 6 semillas, 38 minutos.
- `competencia/experimentos/010_multiclase/final5_log.txt` · secundario · Texto · 10 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/010_multiclase/final5_log.txt.txt)
- `competencia/experimentos/010_multiclase/final_5semillas.py` · secundario · Python · 67 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/010_multiclase/final_5semillas.py.txt)
- `competencia/experimentos/010_multiclase/README.md` · explicacion · Markdown · 23 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/010_multiclase/README.md.txt) — Hipótesis, diseño y tabla de resultados del cambio de binario a multiclase con puntaje P2/(1−P1) en los folds A, B y Bh, con una corrección fechada el 2026-10-08 sobre el sentido del puntaje condicional.
- `competencia/experimentos/010_multiclase/log.txt` · secundario · Texto · 47 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/010_multiclase/log.txt.txt)
- `competencia/experimentos/019_blend/blend.py` · secundario · Python · 28 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/019_blend/blend.py.txt) — Arma el envío anterior exp019_blend: promedio de los ranks de 017 y 010, k = 12.000, sin reentrenar.
- `competencia/experimentos/019_blend/README.md` · secundario · Markdown · 2 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/019_blend/README.md.txt)
- `competencia/experimentos/009b_ensemble_receta/run.py` · secundario · Python · 93 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/009b_ensemble_receta/run.py.txt)
- `competencia/experimentos/009b_ensemble_receta/README.md` · secundario · Markdown · 22 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/009b_ensemble_receta/README.md.txt)
- `competencia/experimentos/009b_ensemble_receta/log.txt` · secundario · Texto · 44 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/009b_ensemble_receta/log.txt.txt)
- `competencia/experimentos/013_ensemble_multiclase/run.py` · secundario · Python · 77 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/013_ensemble_multiclase/run.py.txt)
- `competencia/experimentos/013_ensemble_multiclase/README.md` · secundario · Markdown · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/013_ensemble_multiclase/README.md.txt)
- `competencia/experimentos/013_ensemble_multiclase/log.txt` · secundario · Texto · 40 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/013_ensemble_multiclase/log.txt.txt)
- `competencia/experimentos/004_seleccion_variables/run.py` · secundario · Python · 57 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/run.py.txt)
- `competencia/experimentos/004_seleccion_variables/final.py` · secundario · Python · 32 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/final.py.txt)
- `competencia/experimentos/004_seleccion_variables/seleccion.py` · secundario · Python · 28 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/seleccion.py.txt)
- `competencia/experimentos/004_seleccion_variables/README.md` · secundario · Markdown · 32 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/README.md.txt)
- `competencia/experimentos/004_seleccion_variables/pool.py` · principal · Python · 25 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/pool.py.txt) — Arma el pool de columnas que cargan todos los scripts del final: originales, historia de orden 1 de 50 variables, 17 columnas r_* y, con negocio=True, 26 columnas n_*.
- `competencia/experimentos/004_seleccion_variables/variables_final_top150.txt` · secundario · Texto · 150 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/variables_final_top150.txt.txt)
- `competencia/experimentos/004_seleccion_variables/sel/vars_Bh_p90.txt` · secundario · Texto · 16 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/sel/vars_Bh_p90.txt.txt)
- `competencia/experimentos/004_seleccion_variables/sel/vars_Bh_max.txt` · secundario · Texto · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/sel/vars_Bh_max.txt.txt)
- `competencia/experimentos/004_seleccion_variables/sel/vars_B_p90.txt` · secundario · Texto · 18 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/sel/vars_B_p90.txt.txt)
- `competencia/experimentos/004_seleccion_variables/sel/vars_B_max.txt` · secundario · Texto · 18 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/sel/vars_B_max.txt.txt)
- `competencia/experimentos/004_seleccion_variables/sel/vars_final_p90.txt` · secundario · Texto · 29 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/sel/vars_final_p90.txt.txt)
- `competencia/experimentos/004_seleccion_variables/sel/vars_final_max.txt` · secundario · Texto · 28 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/sel/vars_final_max.txt.txt)
- `competencia/experimentos/004_seleccion_variables/sel/vars_A_max.txt` · secundario · Texto · 10 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/sel/vars_A_max.txt.txt)
- `competencia/experimentos/004_seleccion_variables/sel/vars_A_p90.txt` · secundario · Texto · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004_seleccion_variables/sel/vars_A_p90.txt.txt)
- `competencia/experimentos/031_final_todas_lags/blend_m2.py` · principal · Python · 43 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/031_final_todas_lags/blend_m2.py.txt) — Mezcla final: combina por rank M2 (2/3) con la mezcla de 017, 010 y 024 (1/3), toma los k clientes de mayor valor y escribe el CSV de envío.
- `competencia/experimentos/031_final_todas_lags/final_m2.py` · principal · Python · 72 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/031_final_todas_lags/final_m2.py.txt) — Componente M2, el de mayor peso en la mezcla: multiclase con 855 columnas, 3 configuraciones M1 × 10 semillas, con exclusión previa de columnas de lag2 por PSI. Deja tmp/scores_m2_md50-65-80_202108.csv.
- `competencia/experimentos/031_final_todas_lags/README.md` · explicacion · Markdown · 5 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/031_final_todas_lags/README.md.txt) — Describe M2 (3 configuraciones × 10 semillas, 855 columnas, las 8 excluidas por PSI con su valor), la versión final con --min_data 50,65,80, los tiempos de corrida y la mezcla 2/3–1/3, de la que dice que el peso es un juicio.
- `competencia/experimentos/031_final_todas_lags/log.txt` · secundario · Texto · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/031_final_todas_lags/log.txt.txt) — Registro de dos corridas de final_m2.py del 2026-10-09: entrenamiento de 654.066 filas, 855 columnas, las 8 excluidas por PSI y 10 semillas × 3 configuraciones; la segunda con min_data 50,65,80 (49 a 51 minutos cada una).
- `competencia/experimentos/031_final_todas_lags/drop_psi.txt` · configuracion · Texto · 8 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/031_final_todas_lags/drop_psi.txt.txt) — Salida de final_m2.py: las 8 columnas excluidas de M2 con su PSI, de ccajas_depositos_d2 (2,083) y mpayroll_d2 (1,000) a cpayroll_trx_lag2 (0,205).
- `competencia/experimentos/034_binario_todas_lags/run.py` · secundario · Python · 66 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/034_binario_todas_lags/run.py.txt)
- `competencia/experimentos/034_binario_todas_lags/README.md` · secundario · Markdown · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/034_binario_todas_lags/README.md.txt)
- `competencia/experimentos/034_binario_todas_lags/log.txt` · secundario · Texto · 23 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/034_binario_todas_lags/log.txt.txt)
- `competencia/experimentos/021_receta_multiclase/run.py` · secundario · Python · 68 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/021_receta_multiclase/run.py.txt)
- `competencia/experimentos/021_receta_multiclase/README.md` · secundario · Markdown · 16 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/021_receta_multiclase/README.md.txt)
- `competencia/experimentos/021_receta_multiclase/log.txt` · secundario · Texto · 103 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/021_receta_multiclase/log.txt.txt)
- `competencia/experimentos/003a_lag1_delta/run.py` · secundario · Python · 61 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/003a_lag1_delta/run.py.txt)
- `competencia/experimentos/003a_lag1_delta/final.py` · secundario · Python · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/003a_lag1_delta/final.py.txt)
- `competencia/experimentos/003a_lag1_delta/seleccion_vars.py` · secundario · Python · 34 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/003a_lag1_delta/seleccion_vars.py.txt)
- `competencia/experimentos/003a_lag1_delta/README.md` · secundario · Markdown · 29 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/003a_lag1_delta/README.md.txt)
- `competencia/experimentos/003a_lag1_delta/variables_historia.txt` · configuracion · Texto · 50 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/003a_lag1_delta/variables_historia.txt.txt) — Lista de las 50 variables a las que se les arma lag1, delta1 y ratio1 (y lag2 en 017 y M2). Según 003a_lag1_delta/seleccion_vars.py, son las 50 de mayor gain de un LightGBM entrenado con 202103–202104, sin las fechas en días, los cierres de tarjeta, la edad ni la antigüedad.
- `competencia/experimentos/008b_lag2/run.py` · secundario · Python · 64 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/008b_lag2/run.py.txt)
- `competencia/experimentos/008b_lag2/README.md` · secundario · Markdown · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/008b_lag2/README.md.txt)
- `competencia/experimentos/024_final_receta/blend_final.py` · secundario · Python · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/024_final_receta/blend_final.py.txt) — Arma el envío anterior exp024_final: rank de (017 + 010) promediado 50/50 con el rank de 024, k = 12.000. blend_m2.py repite ese cálculo en memoria sin leer este archivo de salida.
- `competencia/experimentos/024_final_receta/README.md` · explicacion · Markdown · 2 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/024_final_receta/README.md.txt) — Resume los 8 modelos de hiperparámetros fijos sin submuestreo y el envío anterior exp024_final (rank 50/50 con el blend 019, k = 12.000, 101,15 M en el Public según el texto).
- `competencia/experimentos/024_final_receta/log.txt` · secundario · Texto · 11 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/024_final_receta/log.txt.txt) — Registro de la corrida de final_rec.py del 2026-10-08: 654.066 filas × 150 columnas, 8 semillas, 38 minutos.
- `competencia/experimentos/024_final_receta/final_rec.py` · principal · Python · 55 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/024_final_receta/final_rec.py.txt) — Componente 024 de la mezcla: 8 modelos multiclase con hiperparámetros fijos escritos en el código y sin submuestreo, sobre las 150 columnas M1. Deja tmp/scores_rec_202108.csv.
- `competencia/experimentos/032_busqueda_dirigida/run.py` · secundario · Python · 62 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/032_busqueda_dirigida/run.py.txt)
- `competencia/experimentos/032_busqueda_dirigida/README.md` · secundario · Markdown · 16 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/032_busqueda_dirigida/README.md.txt)
- `competencia/experimentos/032_busqueda_dirigida/log.txt` · secundario · Texto · 39 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/032_busqueda_dirigida/log.txt.txt)
- `competencia/experimentos/026_binario_ambas_bajas/run.py` · secundario · Python · 65 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/026_binario_ambas_bajas/run.py.txt)
- `competencia/experimentos/026_binario_ambas_bajas/final_log.txt` · secundario · Texto · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/026_binario_ambas_bajas/final_log.txt.txt)
- `competencia/experimentos/026_binario_ambas_bajas/README.md` · secundario · Markdown · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/026_binario_ambas_bajas/README.md.txt)
- `competencia/experimentos/026_binario_ambas_bajas/log.txt` · secundario · Texto · 34 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/026_binario_ambas_bajas/log.txt.txt)
- `competencia/experimentos/026_binario_ambas_bajas/final_b12.py` · secundario · Python · 66 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/026_binario_ambas_bajas/final_b12.py.txt)
- `competencia/experimentos/026_binario_ambas_bajas/blend_final3.py` · secundario · Python · 28 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/026_binario_ambas_bajas/blend_final3.py.txt)
- `competencia/experimentos/036_validacion_202107/run.py` · secundario · Python · 81 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/036_validacion_202107/run.py.txt) — Validación en 202107 con BAJA+1 como etiqueta: binario entrenado con 202103–06, hiperparámetros de M1_top1, 5 semillas; compara 7 conjuntos (150 columnas, 150 + lag2, 855 columnas, min_data_in_leaf 50, sin las dos columnas de cierre de tarjeta en cada caso y peso 2 para 202106) por ganancia media en k = 8.000…15.000, AUC y recall a k = 12.000 de un grupo de clientes con préstamo personal.
- `competencia/experimentos/036_validacion_202107/README.md` · secundario · Markdown · 23 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/036_validacion_202107/README.md.txt)
- `competencia/experimentos/036_validacion_202107/log.txt` · secundario · Texto · 29 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/036_validacion_202107/log.txt.txt)
- `competencia/experimentos/015_curva_k/run.py` · secundario · Python · 66 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/015_curva_k/run.py.txt) — Curva de ganancia a posteriori del ensamble multiclase de 6 configuraciones para k de 6.000 a 16.000 (paso 500) en los folds A, B y Bh con 3 semillas; guarda el k de máxima ganancia por fold y semilla.
- `competencia/experimentos/015_curva_k/README.md` · secundario · Markdown · 22 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/015_curva_k/README.md.txt)
- `competencia/experimentos/015_curva_k/log.txt` · secundario · Texto · 18 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/015_curva_k/log.txt.txt)
- `competencia/experimentos/027_rank_mes/run.py` · secundario · Python · 75 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/027_rank_mes/run.py.txt)
- `competencia/experimentos/027_rank_mes/README.md` · secundario · Markdown · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/027_rank_mes/README.md.txt)
- `competencia/experimentos/027_rank_mes/log.txt` · secundario · Texto · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/027_rank_mes/log.txt.txt)
- `competencia/experimentos/023_ensemble_con_receta/run.py` · secundario · Python · 68 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/023_ensemble_con_receta/run.py.txt)
- `competencia/experimentos/023_ensemble_con_receta/README.md` · secundario · Markdown · 18 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/023_ensemble_con_receta/README.md.txt)
- `competencia/experimentos/023_ensemble_con_receta/log.txt` · secundario · Texto · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/023_ensemble_con_receta/log.txt.txt)
- `competencia/experimentos/014_auxiliar_baja1/run.py` · secundario · Python · 96 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/014_auxiliar_baja1/run.py.txt)
- `competencia/experimentos/014_auxiliar_baja1/README.md` · secundario · Markdown · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/014_auxiliar_baja1/README.md.txt)
- `competencia/experimentos/014_auxiliar_baja1/log.txt` · secundario · Texto · 42 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/014_auxiliar_baja1/log.txt.txt)
- `competencia/experimentos/003b_ratios/run.py` · secundario · Python · 47 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/003b_ratios/run.py.txt)
- `competencia/experimentos/003b_ratios/README.md` · secundario · Markdown · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/003b_ratios/README.md.txt)
- `competencia/experimentos/035_tendencias/run.py` · secundario · Python · 64 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/035_tendencias/run.py.txt)
- `competencia/experimentos/035_tendencias/README.md` · secundario · Markdown · 11 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/035_tendencias/README.md.txt)
- `competencia/experimentos/035_tendencias/log.txt` · secundario · Texto · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/035_tendencias/log.txt.txt)
- `competencia/experimentos/037_huecos_abc/columnas_canario_p90.txt` · secundario · Texto · 30 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_huecos_abc/columnas_canario_p90.txt.txt)
- `competencia/experimentos/037_huecos_abc/run.py` · secundario · Python · 141 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_huecos_abc/run.py.txt)
- `competencia/experimentos/037_huecos_abc/columnas_canario_max.txt` · secundario · Texto · 22 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_huecos_abc/columnas_canario_max.txt.txt)
- `competencia/experimentos/037_huecos_abc/README.md` · secundario · Markdown · 17 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_huecos_abc/README.md.txt)
- `competencia/experimentos/037_huecos_abc/log.txt` · secundario · Texto · 29 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_huecos_abc/log.txt.txt)
- `competencia/experimentos/022_opciones_lgbm/run.py` · secundario · Python · 58 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/022_opciones_lgbm/run.py.txt)
- `competencia/experimentos/022_opciones_lgbm/README.md` · secundario · Markdown · 16 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/022_opciones_lgbm/README.md.txt)
- `competencia/experimentos/022_opciones_lgbm/log.txt` · secundario · Texto · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/022_opciones_lgbm/log.txt.txt)
- `competencia/experimentos/005_optuna/final30.py` · secundario · Python · 40 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/final30.py.txt)
- `competencia/experimentos/005_optuna/final.py` · principal · Python · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/final.py.txt) — Escribe mejores_trials.json con las 6 configuraciones elegidas; además genera un envío anterior (exp005_mix6) con modelos binarios, que no forma parte de la mezcla final.
- `competencia/experimentos/005_optuna/optuna_log.txt` · secundario · Texto · 1145 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/optuna_log.txt.txt)
- `competencia/experimentos/005_optuna/seleccion.py` · principal · Python · 25 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/seleccion.py.txt) — Genera las listas de 150 columnas por conjunto de meses (A, B, Bh y final) a partir de importancias calculadas con canaritos.
- `competencia/experimentos/005_optuna/reevaluar.py` · principal · Python · 74 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/reevaluar.py.txt) — Lee los estudios de Optuna, arma las configuraciones top1 a top3 por conjunto y las vuelve a medir con 10 semillas distintas en los folds A, B y Bh. final_m2.py lo importa de forma indirecta a través de 028_todas_lags/run.py.
- `competencia/experimentos/005_optuna/mejores_trials.json` · configuracion · JSON · 68 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/mejores_trials.json.txt) — Hiperparámetros de las 6 configuraciones (M0_top1 a top3 y M1_top1 a top3): r entre 0,096 y 0,106, 624 a 738 rondas, 123 a 194 hojas, learning_rate entre 0,0101 y 0,0129, min_data_in_leaf entre 27 y 42, feature_fraction entre 0,129 y 0,353, bagging_fraction entre 0,628 y 0,826 y dos lambdas. Lo escribe 005_optuna/final.py y lo leen 017, 010 y final_m2.py.
- `competencia/experimentos/005_optuna/k_calibrado.py` · secundario · Python · 53 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/k_calibrado.py.txt)
- `competencia/experimentos/005_optuna/optuna_run.py` · principal · Python · 144 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/optuna_run.py.txt) — Búsqueda de hiperparámetros con Optuna en dos estudios alternados (M0 y M1), con el submuestreo r como un hiperparámetro más. Los scripts 017 y 010 importan de aquí es_hist().
- `competencia/experimentos/005_optuna/README.md` · explicacion · Markdown · 58 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/README.md.txt) — Diseño de la búsqueda (rangos, índice, sampler y pruner; 241 trials por estudio en ~8 h según el texto), tabla de la reevaluación con 10 semillas en A, B y Bh, una segunda ronda con rangos corridos y la prueba de corte por probabilidad corregida.
- `competencia/experimentos/005_optuna/progreso.py` · secundario · Python · 34 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/progreso.py.txt)
- `competencia/experimentos/005_optuna/sel/top150_B.txt` · configuracion · Texto · 150 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/sel/top150_B.txt.txt) — Lista de 150 columnas calculada con 202103–202104 (entrenamiento del fold B); la leen optuna_run.py y reevaluar.py.
- `competencia/experimentos/005_optuna/sel/top150_A.txt` · configuracion · Texto · 150 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/sel/top150_A.txt.txt) — Lista de 150 columnas calculada sólo con 202103 (entrenamiento del fold A); la leen optuna_run.py y reevaluar.py.
- `competencia/experimentos/005_optuna/sel/top150_final.txt` · configuracion · Texto · 150 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/sel/top150_final.txt.txt) — Lista de las 150 columnas M1 calculada con 202103–202106; contiene variables originales, 64 columnas con sufijo _lag1, _d1 o _r1, 21 columnas n_* y 16 r_*. La usan 017, 010 y 024.
- `competencia/experimentos/005_optuna/sel/top150_Bh.txt` · configuracion · Texto · 150 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/005_optuna/sel/top150_Bh.txt.txt) — Lista de 150 columnas calculada sólo con 202104 (fold Bh); la leen reevaluar.py y varios experimentos como conjunto de referencia.
- `competencia/experimentos/028_todas_lags/run.py` · principal · Python · 79 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/028_todas_lags/run.py.txt) — Experimento 028; define construir(), la función que final_m2.py importa para armar las 863 columnas de M2. El bloque principal del experimento no se ejecuta al importarlo.
- `competencia/experimentos/028_todas_lags/README.md` · explicacion · Markdown · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/028_todas_lags/README.md.txt) — Motivo, diseño y resultados del experimento que compara 150 columnas, 150 + lag2 de 50 variables y 863 columnas en los folds L y B2 con 4 semillas pareadas.
- `competencia/experimentos/028_todas_lags/log.txt` · secundario · Texto · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/028_todas_lags/log.txt.txt)
- `competencia/experimentos/008_control_submit/final.py` · secundario · Python · 59 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/008_control_submit/final.py.txt)
- `competencia/experimentos/029_control_todas_lags/run.py` · secundario · Python · 54 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/029_control_todas_lags/run.py.txt)
- `competencia/experimentos/029_control_todas_lags/README.md` · secundario · Markdown · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/029_control_todas_lags/README.md.txt)
- `competencia/experimentos/029_control_todas_lags/log.txt` · secundario · Texto · 23 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/029_control_todas_lags/log.txt.txt)
- `competencia/experimentos/030_ensemble_todas_lags/run.py` · secundario · Python · 62 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/030_ensemble_todas_lags/run.py.txt)
- `competencia/experimentos/030_ensemble_todas_lags/README.md` · secundario · Markdown · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/030_ensemble_todas_lags/README.md.txt)
- `competencia/experimentos/030_ensemble_todas_lags/log.txt` · secundario · Texto · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/030_ensemble_todas_lags/log.txt.txt)
- `competencia/experimentos/001_baseline_lgbm/run.py` · secundario · Python · 98 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/001_baseline_lgbm/run.py.txt)
- `competencia/experimentos/001_baseline_lgbm/README.md` · secundario · Markdown · 38 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/001_baseline_lgbm/README.md.txt)
- `competencia/experimentos/001_baseline_lgbm/run_folds.py` · secundario · Python · 16 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/001_baseline_lgbm/run_folds.py.txt)
- `competencia/experimentos/017_final/final.py` · principal · Python · 114 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/017_final/final.py.txt) — Componente 017 de la mezcla: 6 configuraciones en multiclase con un binario auxiliar de BAJA+1 entrenado con un mes más (202107) y, con --lag2, lag2 de 50 variables en M1. Deja tmp/scores_202108_conlag2.csv.
- `competencia/experimentos/017_final/README.md` · explicacion · Markdown · 3 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/017_final/README.md.txt) — Resume el componente 017 (6 configuraciones en multiclase con auxiliar de BAJA+1, lag2 en M1, 30 semillas, 180 + 180 modelos) y su Public con k = 11.000 (99,14 M según el texto).
- `competencia/experimentos/017_final/log.txt` · secundario · Texto · 24 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/017_final/log.txt.txt) — Registro de dos corridas de 017 del 2026-10-08 con 30 semillas × 6 configuraciones, k = 11.000 y lag2: 178 columnas en M0 y 300 en M1, 265 minutos la primera; la segunda reutiliza la caché e informa que el archivo regenerado es idéntico.
- `competencia/experimentos/009_receta_profe/resumen.py` · secundario · Python · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/009_receta_profe/resumen.py.txt)
- `competencia/experimentos/009_receta_profe/run.py` · secundario · Python · 81 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/009_receta_profe/run.py.txt)
- `competencia/experimentos/009_receta_profe/README.md` · secundario · Markdown · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/009_receta_profe/README.md.txt)
- `competencia/experimentos/009_receta_profe/log.txt` · secundario · Texto · 120 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/009_receta_profe/log.txt.txt)
- `competencia/experimentos/_plantilla/README.md` · secundario · Markdown · 20 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/_plantilla/README.md.txt)
- `competencia/experimentos/008a_ccajas_na/run.py` · secundario · Python · 48 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/008a_ccajas_na/run.py.txt)
- `competencia/experimentos/008a_ccajas_na/README.md` · secundario · Markdown · 16 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/008a_ccajas_na/README.md.txt)
- `competencia/experimentos/016_multiclase_lag2/run.py` · secundario · Python · 74 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/016_multiclase_lag2/run.py.txt)
- `competencia/experimentos/016_multiclase_lag2/README.md` · secundario · Markdown · 15 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/016_multiclase_lag2/README.md.txt)
- `competencia/experimentos/016_multiclase_lag2/log.txt` · secundario · Texto · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/016_multiclase_lag2/log.txt.txt)
- `competencia/experimentos/003d_features_negocio/run.py` · secundario · Python · 32 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/003d_features_negocio/run.py.txt)
- `competencia/experimentos/003d_features_negocio/README.md` · secundario · Markdown · 17 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/003d_features_negocio/README.md.txt)
- `competencia/experimentos/018_score_y_rondas/run.py` · secundario · Python · 93 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/018_score_y_rondas/run.py.txt)
- `competencia/experimentos/018_score_y_rondas/README.md` · secundario · Markdown · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/018_score_y_rondas/README.md.txt)
- `competencia/experimentos/018_score_y_rondas/log.txt` · secundario · Texto · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/018_score_y_rondas/log.txt.txt)
- `competencia/experimentos/012_optuna_multiclase/optuna_log.txt` · secundario · Texto · 72 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/012_optuna_multiclase/optuna_log.txt.txt)
- `competencia/experimentos/012_optuna_multiclase/README.md` · secundario · Markdown · 3 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/012_optuna_multiclase/README.md.txt)
- `competencia/experimentos/012_optuna_multiclase/progreso.py` · secundario · Python · 22 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/012_optuna_multiclase/progreso.py.txt)
- `competencia/experimentos/012_optuna_multiclase/optuna_mc.py` · secundario · Python · 115 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/012_optuna_multiclase/optuna_mc.py.txt)
- `competencia/experimentos/003c_features_mes/run.py` · secundario · Python · 44 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/003c_features_mes/run.py.txt)
- `competencia/experimentos/003c_features_mes/README.md` · secundario · Markdown · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/003c_features_mes/README.md.txt)
- `competencia/experimentos/002_eda_variables/eda.ipynb` · secundario · Jupyter (python) · 250 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/002_eda_variables/eda.ipynb.txt)
- `competencia/experimentos/002_eda_variables/run.py` · secundario · Python · 51 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/002_eda_variables/run.py.txt)
- `competencia/experimentos/002_eda_variables/run_potencia.py` · secundario · Python · 43 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/002_eda_variables/run_potencia.py.txt)
- `competencia/experimentos/002_eda_variables/README.md` · secundario · Markdown · 34 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/002_eda_variables/README.md.txt)
- `competencia/experimentos/033_min_data/run.py` · secundario · Python · 59 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/033_min_data/run.py.txt)
- `competencia/experimentos/033_min_data/log.txt` · secundario · Texto · 27 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/033_min_data/log.txt.txt)
- `competencia/experimentos/008_c1_adversarial/run.py` · secundario · Python · 35 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/008_c1_adversarial/run.py.txt)
- `competencia/experimentos/008_c1_adversarial/README.md` · secundario · Markdown · 18 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/008_c1_adversarial/README.md.txt)
- `competencia/experimentos/004b_mezcla/run.py` · secundario · Python · 55 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004b_mezcla/run.py.txt)
- `competencia/experimentos/004b_mezcla/final.py` · secundario · Python · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004b_mezcla/final.py.txt)
- `competencia/experimentos/004b_mezcla/run_control.py` · secundario · Python · 39 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004b_mezcla/run_control.py.txt)
- `competencia/experimentos/004b_mezcla/README.md` · secundario · Markdown · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/004b_mezcla/README.md.txt)
- `competencia/experimentos/007_undersampling/run.py` · secundario · Python · 59 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/007_undersampling/run.py.txt)
- `competencia/experimentos/007_undersampling/README.md` · secundario · Markdown · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/007_undersampling/README.md.txt)
- `competencia/experimentos/011_features_eventos/run.py` · secundario · Python · 96 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/011_features_eventos/run.py.txt)
- `competencia/experimentos/011_features_eventos/README.md` · secundario · Markdown · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/011_features_eventos/README.md.txt)
- `competencia/experimentos/011_features_eventos/log.txt` · secundario · Texto · 41 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/011_features_eventos/log.txt.txt)
- `competencia/experimentos/037_hojas_rf/run.py` · secundario · Python · 73 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_hojas_rf/run.py.txt)
- `competencia/experimentos/037_hojas_rf/bh_final.py` · secundario · Python · 25 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_hojas_rf/bh_final.py.txt)
- `competencia/experimentos/037_hojas_rf/README.md` · secundario · Markdown · 17 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_hojas_rf/README.md.txt)
- `competencia/experimentos/037_hojas_rf/log.txt` · secundario · Texto · 23 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_hojas_rf/log.txt.txt)
- `competencia/experimentos/037_hojas_rf/run_numerico.py` · secundario · Python · 77 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_hojas_rf/run_numerico.py.txt)
- `competencia/experimentos/037_hojas_rf/log_numerico.txt` · secundario · Texto · 15 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/037_hojas_rf/log_numerico.txt.txt)
- `competencia/experimentos/020_pesos_recientes/run.py` · secundario · Python · 59 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/020_pesos_recientes/run.py.txt)
- `competencia/experimentos/020_pesos_recientes/README.md` · secundario · Markdown · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/020_pesos_recientes/README.md.txt)
- `competencia/experimentos/020_pesos_recientes/log.txt` · secundario · Texto · 27 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/experimentos/020_pesos_recientes/log.txt.txt)
- `competencia/src/validacion.py` · principal · Python · 83 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/src/validacion.py.txt) — Define PARAMS_BASE (diccionario de parámetros del que parten todas las configuraciones), los folds A y B, la grilla de k y las funciones xy(), evaluar() y resumen() de los experimentos.
- `competencia/src/multiclase.py` · principal · Python · 34 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/src/multiclase.py.txt) — Funciones del modelo de tres clases: etiquetas, máscara de submuestreo de CONTINUA, entrenamiento y puntaje condicional.
- `competencia/src/submit.py` · principal · Python · 45 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/src/submit.py.txt) — Escritura y validación del CSV de envío y selección de los k clientes de mayor puntaje.
- `competencia/src/config.py` · configuracion · Python · 56 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/src/config.py.txt) — Constantes compartidas: rutas de datos, nombres de columnas, ganancia y costo, semillas propias y derivadas, mes a puntuar y bandera de corrección de ccajas_depositos.
- `competencia/src/seleccion.py` · principal · Python · 39 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/src/seleccion.py.txt) — Importancia de variables con columnas de ruido (canaritos); 005_optuna/seleccion.py la usa para generar las listas de 150 columnas.
- `competencia/src/drift.py` · principal · Python · 43 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/src/drift.py.txt) — PSI por variable y clasificador que distingue un mes de otro; final_m2.py usa psi() para excluir columnas de lag2.
- `competencia/src/features.py` · principal · Python · 198 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/src/features.py.txt) — Variables construidas con datos del mismo mes. El camino de la entrega usa ratios_entre_variables() (17 columnas r_*) y features_negocio() (26 columnas n_*); el resto de las funciones corresponde a los experimentos 002, 003c y 011.
- `competencia/src/modelos.py` · principal · Python · 67 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/src/modelos.py.txt) — Guardado de cada booster, registro de huellas SHA-256 en un manifiesto y control del orden de filas de las predicciones en caché.
- `competencia/src/historia.py` · principal · Python · 112 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/src/historia.py.txt) — Variables históricas: lags por join de cliente y mes anterior, deltas y cocientes; incluye funciones de control y de variables derivadas que sólo usan los experimentos.
- `competencia/src/data.py` · principal · Python · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/src/data.py.txt) — Carga del dataset con DuckDB: vista sobre el parquet (o el CSV), corrección opcional de ccajas_depositos y lectura de meses con orden fijo.
- `competencia/src/ganancia.py` · principal · Python · 35 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/segunmo/competencia/src/ganancia.py.txt) — Funciones de ganancia: por umbral, acumulada por cantidad de envíos y corte de máxima ganancia. La búsqueda de Optuna y los experimentos usan ganancia_acumulada().

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### competencia/preparar_datos.py

Descarga el CSV crudo, construye clase_ternaria con SQL en DuckDB y genera el CSV con clase y el parquet que leen los demás scripts.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Docstring con los tres pasos (descarga, clase_ternaria, parquet), imports de
#   duckdb y pandas y la URL pública del CSV crudo de la cátedra.
"""Prepara los datos de la competencia SIN notebooks, con los mismos pasos de clases/z101_target_sql.ipynb y clases/z701_drifting.ipynb:
  1. baja competencia_01_crudo.csv de la URL pública de la cátedra (si no está);
  2. construye competencia_01.csv con `clase_ternaria` (SQL de la celda 27 de z101: cross join cliente x mes, lead 1 y 2);
  3. genera competencia_01.parquet.gzip desde ese CSV (celda 3 de z701).
Uso (raíz del repo): venv/bin/python competencia/preparar_datos.py [--dir data] [--url URL]
Los archivos quedan en --dir (por defecto `data/`, fuera de git). El orden de filas del CSV no importa: el código siempre ordena por (foto_mes, numero_de_cliente) al cargar."""
import argparse
from pathlib import Path

import duckdb
import pandas as pd

URL = "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
# [Anotación · líneas 14–30] Consulta SQL que arma clase_ternaria: cruza todos los clientes con todos los
#   meses, marca con mes_0 si el cliente está ese mes y mira con lead() su presencia uno y dos meses después. Si
#   está a los dos meses es CONTINUA; si está al mes siguiente y no a los dos meses, BAJA+2; si no está al mes
#   siguiente, BAJA+1; en otro caso queda NULL. Conserva sólo las filas en que el cliente está presente.
SQL = """
create or replace table competencia_01 as
with periodos as (select distinct foto_mes from crudo),
     clientes as (select distinct numero_de_cliente from crudo),
     todo as (select numero_de_cliente, foto_mes from clientes cross join periodos),
     clase_ternaria as (
        select c.*,
               if(c.numero_de_cliente is null, 0, 1) as mes_0,
               lead(mes_0, 1) over (partition by t.numero_de_cliente order by foto_mes) as mes_1,
               lead(mes_0, 2) over (partition by t.numero_de_cliente order by foto_mes) as mes_2,
               case when mes_2 = 1 then 'CONTINUA'                     -- vuelve a aparecer en t+2: la ausencia fue transitoria
                    when mes_1 = 1 and mes_2 = 0 then 'BAJA+2'         -- está en t+1 y no en t+2
                    when mes_1 = 0 then 'BAJA+1'                       -- no está en t+1
                    else null end as clase_ternaria                    -- últimos 2 meses: el futuro no se conoce
        from todo t left join crudo c using (numero_de_cliente, foto_mes))
select * exclude (mes_0, mes_1, mes_2) from clase_ternaria where mes_0 = 1
"""

# [Anotación · líneas 32–36] Argumentos --dir (por defecto data), --url y --crudo, y rutas de los tres
#   archivos: CSV crudo, CSV con clase y parquet.
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", default="data"); ap.add_argument("--url", default=URL); ap.add_argument("--crudo", default=None)
    a = ap.parse_args()
    d = Path(a.dir); d.mkdir(parents=True, exist_ok=True)
    crudo, csv, pq = Path(a.crudo) if a.crudo else d / "competencia_01_crudo.csv", d / "competencia_01.csv", d / "competencia_01.parquet.gzip"
# [Anotación · líneas 37–44] Si el CSV crudo no existe, lo descarga con requests en bloques de 1 MB.
    if not crudo.exists():
        import requests
        print("bajando", a.url)
        with requests.get(a.url, stream=True) as r:
            r.raise_for_status()
            with open(crudo, "wb") as f:
                for bloque in r.iter_content(1 << 20):
                    f.write(bloque)
# [Anotación · líneas 45–51] Carga el crudo en DuckDB, ejecuta la consulta, exporta competencia_01.csv con
#   encabezado, imprime la cantidad de filas por mes y clase y convierte el CSV a competencia_01.parquet.gzip
#   con pandas.
    con = duckdb.connect()
    con.execute(f"create table crudo as select * from read_csv_auto('{crudo.as_posix()}')")
    con.execute(SQL)
    con.execute(f"copy competencia_01 to '{csv.as_posix()}' (format csv, header)")
    print("clase_ternaria por mes:\n", con.sql("select foto_mes, clase_ternaria, count(*) n from competencia_01 group by 1, 2 order by 1, 2").df().to_string(index=False))
    pd.read_csv(csv).to_parquet(pq, compression="gzip")
    print("listo:", csv, pq)
```

### competencia/experimentos/010_multiclase/final.py

Componente 010 de la mezcla: las 6 configuraciones en multiclase, sin auxiliar ni lag2, con 6 semillas cada una. Deja tmp/proba_202108.csv.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–4] Docstring: las 6 configuraciones de 005 en multiclase, puntaje condicional,
#   promedio por rank, sin lag2, 6 semillas por configuración y un archivo con k = 11.500.
"""010 — submit de prueba: MIX6 de 005 (3 mejores trials de M0 y de M1) pasado a MULTICLASE (B1), score condicional P(BAJA+2)/(1-P(BAJA+1)),
promedio por RANK de los 6 modelos (009b), ccajas corregida, SIN lag2 (para probar solo el cambio validado en B1). Train 202103–06 -> score 202108,
6 semillas por configuración, un solo archivo con k=11500. Cada configuración usa su propio r de Optuna sobre CONTINUA; BAJA+1 y BAJA+2 completos.
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/010_multiclase/final.py   |   tail -f competencia/experimentos/010_multiclase/final_log.txt"""
# [Anotación · líneas 5–28] Imports; activa CORREGIR_CCAJAS; constantes K = 11.500 y N_SEM = 6 y mapa de
#   clases.
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
config.CORREGIR_CCAJAS = True
from config import ID_COL, MES_SCORING, SEMILLAS, TARGET_COL  # noqa: E402
from modelos import guardar_modelo, verificar_orden_cache  # noqa: E402
from optuna_run import es_hist  # noqa: E402
from pool import cargar  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402
from validacion import PARAMS_BASE, xy  # noqa: E402

K, N_SEM, LOG = 11500, 6, AQUI / "final_log.txt"
CLASES = {"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}


# [Anotación · líneas 31–44] configs_desde_json() lee mejores_trials.json (r, rondas y parámetros por
#   configuración) y escribir() imprime y agrega al log.
def configs_desde_json() -> dict:
    """{(conjunto, 'topN'): (r, rondas, params)} desde `005_optuna/mejores_trials.json` (versionado). Antes se leían de la base SQLite de Optuna
    (artifacts/, no versionada); ambas fuentes dan valores idénticos (verificado el 2026-10-08/10), pero el JSON permite reproducir sin repetir Optuna."""
    out = {}
    for clave, d in json.loads((A005 / "mejores_trials.json").read_text()).items():
        c, n = clave.split("_")
        out[(c, n)] = (d["r"], d["num_boost_round"], {**PARAMS_BASE, **{k: v for k, v in d.items() if k not in ("r", "num_boost_round")}})
    return out


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


# [Anotación · líneas 47–56] Toma las primeras 6 semillas, carga 202103–202106 y 202108 con el pool, arma la
#   etiqueta de tres clases y las columnas M0 (no históricas) y M1 (top150_final.txt), escribe el encabezado del
#   log y verifica el orden de la caché.
if __name__ == "__main__":
    semillas = config.semillas(N_SEM)                               # semillas explícitas en config.py
    cfg = configs_desde_json()
    dt = cargar([202103, 202104, 202105, 202106], negocio=True)
    score = cargar([MES_SCORING], solo_con_target=False, negocio=True)
    y3 = dt[TARGET_COL].map(CLASES).values
    Xt0, _ = xy(dt)
    cols = {"M0": [c for c in Xt0.columns if not es_hist(c)], "M1": (A005 / "sel" / "top150_final.txt").read_text().split()}
    escribir(f"\n===== final 010 {time.strftime('%Y-%m-%d %H:%M')} | train {dt.shape} (BAJA+1 {(y3==1).sum()}, BAJA+2 {(y3==2).sum()}) | score {score.shape} | semillas {semillas} =====")
    verificar_orden_cache(AQUI / "tmp", score[ID_COL].values)            # no mezclar predicciones cacheadas con otro orden de filas
# [Anotación · líneas 57–73] Para cada configuración y semilla sin caché entrena el multiclase con BAJA+1 y
#   BAJA+2 completos y una fracción r de CONTINUA, calcula P2 / (1 − P1) sobre 202108 y guarda el modelo y el
#   .npy; promedia entre semillas.
    t0, P = time.time(), {}
    for (c, nombre), (r, rondas, params) in cfg.items():
        ps = []
        for s in semillas:
            f = AQUI / "tmp" / f"mc_{c}_{nombre}_{s}.npy"                          # cache por (configuración, semilla): se reanuda si se corta
            if not f.exists():
                keep = (y3 >= 1) | (np.random.RandomState(s).rand(len(y3)) < r)
                m = lgb.train({**params, "objective": "multiclass", "num_class": 3, "seed": s},
                              lgb.Dataset(dt.loc[keep, cols[c]], label=y3[keep]), num_boost_round=rondas)
                pm = m.predict(score[cols[c]])
                sc_ = pm[:, 2] / np.clip(1 - pm[:, 1], 1e-6, None)                  # score condicional
                (AQUI / "tmp").mkdir(exist_ok=True)
                guardar_modelo(m, f"010_{c}_{nombre}_{s}", sc_)
                np.save(f, sc_)
            ps.append(np.load(f))
        P[f"{c}_{nombre}"] = np.mean(ps, axis=0)
        escribir(f"listo {c} {nombre} ({(time.time()-t0)/60:.0f} min)")
# [Anotación · líneas 74–83] Promedia los ranks de las 6 configuraciones y guarda tmp/proba_202108.csv, que
#   lee la mezcla final. Toma los 11.500 primeros y compara con exp010_mc_h2_k11500.csv si existe, o lo escribe.
    ids = score[ID_COL].values
    rk = np.mean([rankdata(p) / len(p) for p in P.values()], axis=0)           # rank medio de los 6 (009b)
    (AQUI / "tmp").mkdir(exist_ok=True)
    pd.DataFrame({ID_COL: ids, "rank": rk, **P}).to_csv(AQUI / "tmp" / "proba_202108.csv", index=False)
    top = top_k_ids(ids, rk, K); destino = AQUI.parents[1] / "submissions" / f"exp010_mc_h2_k{K}.csv"
    if destino.exists():                                  # reproducibilidad: si ya existe, se compara en vez de fallar
        previo = np.loadtxt(destino, dtype=np.int64)
        escribir(f"{destino.name} ya existía: " + ("IDÉNTICO al regenerado" if np.array_equal(previo, top) else f"DISTINTO (coinciden {len(set(previo) & set(top)) / K:.1%} de los clientes)"))
    else:
        escribir(guardar_submit(top, f"exp010_mc_h2_k{K}").name)
# [Anotación · líneas 84–87] Informa el solapamiento del top-11.500 con dos envíos anteriores, si sus archivos
#   existen.
    for previo in ("exp005_final_s30_k11500", "exp008_lag2_ccajas_k11500"):
        f = AQUI.parents[1] / "submissions" / f"{previo}.csv"
        if f.exists():
            escribir(f"solapamiento top-{K} con {previo}: {len(set(top_k_ids(ids, rk, K)) & set(np.loadtxt(f, dtype=np.int64))) / K:.1%}")
```

### competencia/experimentos/004_seleccion_variables/pool.py

Arma el pool de columnas que cargan todos los scripts del final: originales, historia de orden 1 de 50 variables, 17 columnas r_* y, con negocio=True, 26 columnas n_*.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Imports y lectura de las 50 variables con historia desde
#   003a_lag1_delta/variables_historia.txt.
"""Pool de variables candidatas de 004: originales + historia 003b (lag1, delta1, ratio1 de 50 vars) + 17 ratios 003c."""
import sys
from functools import lru_cache
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from data import cargar_meses  # noqa: E402,F401
from features import features_negocio, ratios_entre_variables  # noqa: E402
from historia import agregar_deltas, agregar_ratios, cargar_con_lags  # noqa: E402

VARS = (AQUI.parents[0] / "003a_lag1_delta" / "variables_historia.txt").read_text().split()


# [Anotación · líneas 15–25] cargar_pool(), con caché de hasta 8 combinaciones de meses: carga los meses con
#   el lag1 de las 50 variables, agrega delta1 y ratio1, las 17 columnas r_* y, con negocio=True, las 26 n_*
#   (345 columnas según el docstring). cargar() convierte la lista de meses en tupla para poder usar la caché.
@lru_cache(maxsize=8)
def cargar_pool(meses: tuple, solo_con_target: bool = True, negocio: bool = False):
    """Se cachea por meses: evaluar() y la selección piden los mismos meses varias veces. No modificar el resultado.
    negocio=True suma las 26 columnas `n_*` de 003d (el pool pasa de 319 a 345 columnas)."""
    d = cargar_con_lags(list(meses), VARS, solo_con_target=solo_con_target)
    d = ratios_entre_variables(agregar_ratios(agregar_deltas(d, VARS), VARS))
    return features_negocio(d) if negocio else d


def cargar(meses, **kw):
    return cargar_pool(tuple(meses), **kw)
```

### competencia/experimentos/031_final_todas_lags/blend_m2.py

Mezcla final: combina por rank M2 (2/3) con la mezcla de 017, 010 y 024 (1/3), toma los k clientes de mayor valor y escribe el CSV de envío.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Docstring (pesos por defecto 2/3 de M2 y 1/3 de la mezcla anterior) e imports.
"""031b — candidato final con M2: rank medio ponderado entre el ensemble M2 (todas las variables con lags, 031) y el blend actual `exp024_final` (017 + 010 + receta).
Pesos por defecto: 2/3 M2 + 1/3 exp024. Juicio, no validado: 030 mostró M2 +8.8M sobre E1 en B2 y la mezcla 50/50 con E1 +5.9M; exp024 aporta diversidad (receta) y cobertura.
Uso (raíz del repo): venv/bin/python competencia/experimentos/031_final_todas_lags/blend_m2.py [peso_m2] [k]"""
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from config import ID_COL  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402

# [Anotación · líneas 15–18] Argumentos posicionales: peso de M2 (2/3 por defecto), k (12.000 por defecto) y
#   nombre del archivo de puntajes de M2; rutas de los cuatro archivos de puntajes (M2, 017, 010 y 024).
W, K, E = (float(sys.argv[1]) if len(sys.argv) > 1 else 2 / 3), (int(sys.argv[2]) if len(sys.argv) > 2 else 12000), AQUI.parents[0]
ARCH = sys.argv[3] if len(sys.argv) > 3 else "scores_m2_202108.csv"            # p. ej. scores_m2_md50-65-80_202108.csv
src = {"m2": AQUI / "tmp" / ARCH, "r017": E / "017_final" / "tmp" / "scores_202108_conlag2.csv", "r010": E / "010_multiclase" / "tmp" / "proba_202108.csv",
       "rrec": E / "024_final_receta" / "tmp" / "scores_rec_202108.csv"}
# [Anotación · líneas 19–23] Lee cliente y rank de cada archivo, los une uno a uno por cliente y verifica que
#   queden 164.647 filas.
d = None
for n, f in src.items():
    x = pd.read_csv(f, usecols=[ID_COL, "rank"]).rename(columns={"rank": n})
    d = x if d is None else d.merge(x, on=ID_COL, validate="one_to_one")
assert len(d) == 164647, len(d)
# [Anotación · líneas 24–27] Vuelve a calcular el rank de cada componente; reconstruye el blend 019 como rank
#   de (017 + 010) y el blend 024 como rank de (blend 019 + 024); el puntaje final es W · rank de M2 + (1 − W) ·
#   blend 024.
R = {n: rankdata(d[n]) / len(d) for n in src}
mix019 = rankdata(R["r017"] + R["r010"]) / len(d)                                   # = blend 019
actual = rankdata(mix019 + R["rrec"]) / len(d)                                       # = exp024_final (50/50 blend 019 y receta)
final = W * R["m2"] + (1 - W) * actual
# [Anotación · líneas 28–31] Toma los k clientes de mayor puntaje final e imprime el solapamiento con el top-k
#   del blend 024 y con el de M2 solo.
ids = d[ID_COL].values; top = top_k_ids(ids, final, K)
tm2 = set(top_k_ids(ids, R["m2"], K))
t24 = set(top_k_ids(ids, actual, K))                                                  # exp024_final regenerado en memoria (no se lee del disco)
print(f"peso M2 {W:.3f} | k={K} | solapamiento con exp024_final {len(set(top) & t24) / K:.1%} | con M2 solo {len(set(top) & tm2) / K:.1%} | M2 vs exp024 {len(tm2 & t24) / K:.1%}")
# [Anotación · líneas 32–43] Arma el nombre exp031_final_w<peso>[_md]_k<k>. Si el archivo ya existe en
#   submissions/ informa si es idéntico; si difiere, guarda el regenerado con sufijo _regenerado; si no existe,
#   lo escribe con guardar_submit().
nombre = f"exp031_final_w{int(round(W * 100))}{'_md' if 'md' in ARCH else ''}_k{K}"
destino = AQUI.parents[1] / "submissions" / f"{nombre}.csv"
if destino.exists():                                      # reproducibilidad: si ya existe, se compara en vez de fallar
    import numpy as np
    previo = np.loadtxt(destino, dtype=np.int64)
    if np.array_equal(previo, top):
        print(f"{nombre}.csv ya existía: IDÉNTICO al regenerado (mismo conjunto y mismo orden)")
    else:                                                 # no se pisa el enviado: el regenerado queda con sufijo para poder compararlos
        print(f"{nombre}.csv ya existía y es DISTINTO: coinciden {len(set(previo) & set(top)) / K:.1%} de los clientes. Se guarda el regenerado como {nombre}_regenerado.csv")
        print(guardar_submit(top, f"{nombre}_regenerado").name)
else:
    print(guardar_submit(top, nombre).name)
```

### competencia/experimentos/031_final_todas_lags/final_m2.py

Componente M2, el de mayor peso en la mezcla: multiclase con 855 columnas, 3 configuraciones M1 × 10 semillas, con exclusión previa de columnas de lag2 por PSI. Deja tmp/scores_m2_md50-65-80_202108.csv.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–5] Docstring: multiclase con todas las variables con lag1, lag2 y diferencias, 3
#   configuraciones M1 × N semillas, exclusión de columnas lag2 y d2 por PSI, caché por configuración y semilla.
"""031 — modelo final M2: multiclase con TODAS las variables con lag1, lag2 y diferencias (028/030), 3 configuraciones M1 de 005 (mejores_trials.json) × N semillas,
train 202103–06 -> score 202108, score condicional P2/(1-P1), rank medio. Se EXCLUYEN las columnas lag2/d2 cuyo PSI entre las filas de train con lag2 real (202105, 202106)
y 202108 supera --psi (por defecto 0.20): el lag2 de 202108 apunta a junio (aguinaldo) y esas columnas quedan fuera de la distribución de train. Sin mirar el target.
La lista queda en drop_psi.txt. Cada (configuración, semilla) se guarda en tmp/ y se reanuda.
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/031_final_todas_lags/final_m2.py --semillas 10 [--psi 0.20]   |   tail -f competencia/experimentos/031_final_todas_lags/log.txt"""
# [Anotación · líneas 6–27] Imports; carga 028_todas_lags/run.py como módulo t028 con importlib (ese módulo
#   activa CORREGIR_CCAJAS y aporta construir()); rutas de log y tmp.
import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(AQUI.parents[0] / "005_optuna"))
spec = importlib.util.spec_from_file_location("t028", AQUI.parents[0] / "028_todas_lags" / "run.py"); t028 = importlib.util.module_from_spec(spec); spec.loader.exec_module(t028)
import config  # noqa: E402
from config import ID_COL  # noqa: E402
from drift import psi  # noqa: E402
from modelos import guardar_modelo, verificar_orden_cache  # noqa: E402
from multiclase import entrenar, etiquetas, filas, score_cond  # noqa: E402
from validacion import PARAMS_BASE  # noqa: E402

LOG, TMP = AQUI / "log.txt", AQUI / "tmp"


# [Anotación · líneas 30–33] escribir() imprime y agrega al log.
def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


# [Anotación · líneas 36–48] Argumentos --semillas (10), --psi (0,20) y --min_data. Lee de mejores_trials.json
#   las tres configuraciones cuyo nombre empieza con M1 y, si se pasa --min_data, reemplaza min_data_in_leaf de
#   top1, top2 y top3 por los valores dados (50, 65 y 80 en la entrega) y agrega md50-65-80_ a los nombres de
#   archivo.
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--semillas", type=int, default=10); ap.add_argument("--psi", type=float, default=0.20)
    ap.add_argument("--min_data", default="", help="min_data_in_leaf para M1 top1,top2,top3 separados por coma (032/033: meseta en 50-80)"); args = ap.parse_args()
    semillas = config.semillas(args.semillas)                       # semillas explícitas en config.py (5 propias + derivadas)
    js = json.loads((t028.A005 / "mejores_trials.json").read_text())
    cfg = {tuple(k.split("_")): (d["r"], d["num_boost_round"], {**PARAMS_BASE, **{a: b for a, b in d.items() if a not in ("r", "num_boost_round")}}) for k, d in js.items() if k.startswith("M1")}
    TAG = ""
    if args.min_data:                                                                # 033: meseta de min_data_in_leaf entre 50 y 80
        md = [int(v) for v in args.min_data.split(",")]
        for i, k in enumerate(sorted(cfg)):
            cfg[k][2]["min_data_in_leaf"] = md[i]
        TAG = "md" + "-".join(map(str, md)) + "_"
    TMP.mkdir(exist_ok=True)
# [Anotación · líneas 49–55] Construye las columnas para 202103–202106 y para 202108. Calcula el PSI de cada
#   columna terminada en _lag2 o _d2 entre las filas de entrenamiento de 202105 y 202106 y las de 202108,
#   escribe en drop_psi.txt las que superan el umbral y las quita de la lista (quedan 855 según el log).
    dt = t028.construir([202103, 202104, 202105, 202106]); sc = t028.construir([202108], solo_con_target=False)
    cols = [c for c in dt.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria") and not c.startswith("canario")]
    ref = dt[dt.foto_mes.isin([202105, 202106])]                                    # filas de train con lag2 real
    p = {c: psi(ref[c], sc[c]) for c in cols if c.endswith(("_lag2", "_d2"))}
    drop = sorted([c for c, v in p.items() if v > args.psi], key=lambda c: -p[c])
    (AQUI / "drop_psi.txt").write_text("\n".join(f"{c}\t{p[c]:.3f}" for c in drop) + "\n")
    cols = [c for c in cols if c not in drop]; y3 = etiquetas(dt)
# [Anotación · líneas 56–57] Escribe el encabezado del log con dimensiones, columnas excluidas y cantidad de
#   semillas, y verifica el orden de la caché.
    escribir(f"\n===== 031 final M2 {time.strftime('%Y-%m-%d %H:%M')} | train {dt.shape} | {len(cols)} columnas (excluidas por PSI>{args.psi}: {len(drop)}: {drop}) | {len(semillas)} semillas × {len(cfg)} configs | min_data: {args.min_data or "originales"} =====")
    verificar_orden_cache(TMP, sc[ID_COL].values)                       # no mezclar predicciones cacheadas con otro orden de filas
# [Anotación · líneas 58–69] Para cada configuración y semilla sin caché: entrena el multiclase con BAJA+1 y
#   BAJA+2 completos y una fracción r de CONTINUA, calcula P2 / (1 − P1) sobre 202108 y guarda el modelo con su
#   huella y el .npy. Promedia entre semillas por configuración.
    t0, S = time.time(), {}
    for (c, nombre), (r, rondas, params) in cfg.items():
        ps = []
        for s in semillas:
            f = TMP / f"m2_{TAG}{c}_{nombre}_{s}.npy"
            if not f.exists():
                m = entrenar(params, dt[cols], y3, filas(y3, r, s), s, rondas)
                sc_ = score_cond(m.predict(sc[cols]))
                guardar_modelo(m, f"031_m2_{TAG}{c}_{nombre}_{s}", sc_)
                np.save(f, sc_)
            ps.append(np.load(f))
        S[f"{c}_{nombre}"] = np.mean(ps, axis=0); escribir(f"listo {c} {nombre} ({len(semillas)} semillas, {(time.time()-t0)/60:.0f} min)")
# [Anotación · líneas 70–72] Promedia los ranks de las 3 configuraciones y escribe
#   tmp/scores_m2_<TAG>202108.csv con el rank medio y una columna por configuración.
    rk = np.mean([rankdata(v) / len(v) for v in S.values()], axis=0)
    pd.DataFrame({ID_COL: sc[ID_COL].values, "rank": rk, **S}).to_csv(TMP / f"scores_m2_{TAG}202108.csv", index=False)
    escribir("[031 final M2] terminado")
```

### competencia/experimentos/024_final_receta/final_rec.py

Componente 024 de la mezcla: 8 modelos multiclase con hiperparámetros fijos escritos en el código y sin submuestreo, sobre las 150 columnas M1. Deja tmp/scores_rec_202108.csv.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–4] Docstring: multiclase sin submuestreo, 512 hojas, 800 rondas y learning_rate 0,005
#   sobre las columnas M1, un modelo por semilla.
"""024 — modelos de la RECETA del profe para el final: multiclase SIN undersampling, 512 hojas, min_sum_hessian 0.05, 800 rondas, lr 0.005, min_data_in_leaf 0,
ff 0.5, bynode 0.2 (023), columnas M1 top150_final, train 202103–06 (654k filas, todas), score P2/(1-P1) sobre 202108. Un modelo por semilla; se guarda cada uno en tmp/
(se puede cortar y reanudar). Salida: tmp/scores_rec_202108.csv con el promedio de scores y su rank.
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/024_final_receta/final_rec.py --semillas 8   |   tail -f competencia/experimentos/024_final_receta/log.txt"""
# [Anotación · líneas 5–27] Imports; activa CORREGIR_CCAJAS; diccionario RECETA con hiperparámetros fijos
#   (num_leaves 512, learning_rate 0,005, min_data_in_leaf 0, min_sum_hessian_in_leaf 0,05, feature_fraction
#   0,5, feature_fraction_bynode 0,2, max_bin 31, deterministic y force_row_wise) y 800 rondas.
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
config.CORREGIR_CCAJAS = True
from config import ID_COL, MES_SCORING, SEMILLAS  # noqa: E402
from modelos import guardar_modelo, verificar_orden_cache  # noqa: E402
from multiclase import entrenar, etiquetas, filas, score_cond  # noqa: E402
from pool import cargar  # noqa: E402

LOG, TMP = AQUI / "log.txt", AQUI / "tmp"
RECETA = {"max_bin": 31, "min_data_in_leaf": 0, "feature_fraction": 0.5, "feature_fraction_bynode": 0.2, "learning_rate": 0.005,
          "min_sum_hessian_in_leaf": 0.05, "num_leaves": 512, "feature_pre_filter": False, "verbose": -1, "num_threads": 0, "deterministic": True, "force_row_wise": True}
RONDAS = 800


# [Anotación · líneas 30–33] escribir() imprime y agrega al log.
def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


# [Anotación · líneas 36–43] Argumento --semillas (8); carga 202103–202106 y 202108 con el pool, toma las 150
#   columnas de top150_final.txt y la etiqueta de tres clases; verifica el orden de la caché.
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--semillas", type=int, default=8); args = ap.parse_args()
    semillas = config.semillas(args.semillas)                       # semillas explícitas en config.py (5 propias + derivadas)
    TMP.mkdir(exist_ok=True)
    dt = cargar([202103, 202104, 202105, 202106], negocio=True); score = cargar([MES_SCORING], solo_con_target=False, negocio=True)
    cols = (A005 / "sel" / "top150_final.txt").read_text().split(); y3 = etiquetas(dt)
    escribir(f"\n===== 024 final receta {time.strftime('%Y-%m-%d %H:%M')} | train {dt[cols].shape} | {len(semillas)} semillas =====")
    verificar_orden_cache(TMP, score[ID_COL].values)                    # no mezclar predicciones cacheadas con otro orden de filas
# [Anotación · líneas 44–55] Por semilla sin caché entrena un multiclase con todas las filas (r = 1,0),
#   calcula el puntaje condicional sobre 202108 y guarda modelo y .npy. Promedia las semillas y escribe
#   tmp/scores_rec_202108.csv con cliente, puntaje y rank.
    t0, ps = time.time(), []
    for s in semillas:
        f = TMP / f"rec_{s}.npy"
        if not f.exists():
            m = entrenar(RECETA, dt[cols], y3, filas(y3, 1.0, s), s, RONDAS)
            sc_ = score_cond(m.predict(score[cols]))
            guardar_modelo(m, f"024_receta_{s}", sc_)
            np.save(f, sc_)
        ps.append(np.load(f)); escribir(f"semilla {s} lista ({(time.time()-t0)/60:.0f} min)")
    p = np.mean(ps, axis=0)
    pd.DataFrame({ID_COL: score[ID_COL].values, "score": p, "rank": rankdata(p) / len(p)}).to_csv(TMP / "scores_rec_202108.csv", index=False)
    escribir("[024 final receta] terminado")
```

### competencia/experimentos/005_optuna/final.py

Escribe mejores_trials.json con las 6 configuraciones elegidas; además genera un envío anterior (exp005_mix6) con modelos binarios, que no forma parte de la mezcla final.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–21] Docstring e imports.
"""005 — entrega 5: MIX6 = promedio de las probabilidades de los 3 mejores trials de M0 y los 3 mejores de M1
(hiperparámetros + undersampling r de Optuna), entrenados con 202103–202106, 10 semillas por configuración
(las 5 propias + 5 derivadas), y puntuados sobre 202108. 8 archivos top-k (k=8000..15000) para comparar con las entregas anteriores.
Guarda los hiperparámetros elegidos en mejores_trials.json (la base de Optuna vive en artifacts/, que no se versiona).
Uso (raíz del repo): venv/bin/python competencia/experimentos/005_optuna/final.py"""
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from optuna_run import CONJUNTOS, es_hist  # noqa: E402
from reevaluar import N_TOP, SEMILLAS_20, configs  # noqa: E402
from config import ID_COL, MES_SCORING  # noqa: E402
from pool import cargar  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402
from validacion import KS, xy  # noqa: E402

# [Anotación · líneas 23–27] Toma 10 semillas y las configuraciones top1 a top3 de M0 y M1 y escribe
#   mejores_trials.json con r, num_boost_round y siete hiperparámetros por configuración (num_leaves,
#   learning_rate, min_data_in_leaf, feature_fraction, bagging_fraction, lambda_l1, lambda_l2).
if __name__ == "__main__":
    semillas = SEMILLAS_20[:10]
    cfg = {k: v for k, v in configs().items() if k[1].startswith("top")}
    (AQUI / "mejores_trials.json").write_text(json.dumps({f"{c}_{n}": {"r": r, "num_boost_round": rounds, **{k: v for k, v in p.items() if k in ("num_leaves", "learning_rate", "min_data_in_leaf", "feature_fraction", "bagging_fraction", "lambda_l1", "lambda_l2")}}
                                                          for (c, n), (r, rounds, p) in cfg.items()}, indent=1))
# [Anotación · líneas 28–39] Entrena cada configuración como binario BAJA+2 con 202103–202106 y submuestreo r,
#   con 10 semillas, y promedia las predicciones sobre 202108.
    Xt, yt = xy(cargar([202103, 202104, 202105, 202106], negocio=True)); yt = yt.values
    score = cargar([MES_SCORING], solo_con_target=False, negocio=True)
    cols = {"M0": [c for c in Xt.columns if not es_hist(c)], "M1": (AQUI / "sel" / "top150_final.txt").read_text().split()}
    print(f"train {Xt.shape} ({yt.sum()} BAJA+2) | score {score.shape} | M0 {len(cols['M0'])} cols, M1 {len(cols['M1'])} cols | semillas {semillas}", flush=True)
    P = {}
    for (c, nombre), (r, rounds, params) in cfg.items():
        ps = []
        for s in semillas:
            keep = (yt == 1) | (np.random.RandomState(s).rand(len(yt)) < r)
            m = lgb.train({**params, "seed": s}, lgb.Dataset(Xt.loc[keep, cols[c]], label=yt[keep]), num_boost_round=rounds)
            ps.append(m.predict(score[cols[c]]))
        P[(c, nombre)] = np.mean(ps, axis=0); print(f"listo {c} {nombre}", flush=True)
# [Anotación · líneas 40–46] Promedia las 6 configuraciones, guarda tmp/proba_202108.csv y escribe 8 archivos
#   exp005_mix6_k8000 a k15000; imprime cuántos clientes tienen probabilidad mayor o igual a 0,025.
    p = np.mean(list(P.values()), axis=0)
    ids = score[ID_COL].values
    (AQUI / "tmp").mkdir(exist_ok=True)
    pd.DataFrame({ID_COL: ids, "p": p, **{f"{c}_{n}": v for (c, n), v in P.items()}}).to_csv(AQUI / "tmp" / "proba_202108.csv", index=False)
    for k in KS:
        print(guardar_submit(top_k_ids(ids, p, k), f"exp005_mix6_k{k}").name)
    print("clientes con p>=0.025:", int((p >= .025).sum()), "| p media %.4f" % p.mean())
```

### competencia/experimentos/005_optuna/seleccion.py

Genera las listas de 150 columnas por conjunto de meses (A, B, Bh y final) a partir de importancias calculadas con canaritos.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Docstring e imports.
"""005 paso 0 — repite la selección top150 de 004 sobre el pool ampliado (345 columnas: + 26 `n_*` de 003d).
Importancia (gain, 5 semillas, con 20 canaritos solo para excluirlos del ranking) calculada SOLO con el train de cada fold.
Guarda sel/importancias_<fold>.csv. Uso (raíz del repo): venv/bin/python competencia/experimentos/005_optuna/seleccion.py"""
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables"))
from pool import cargar  # noqa: E402
from seleccion import importancias_con_canaritos  # noqa: E402
from validacion import xy  # noqa: E402

# [Anotación · líneas 14–25] Para cuatro conjuntos de meses (A: 202103; B: 202103–04; Bh: 202104; final:
#   202103–06) carga el pool de 345 columnas, calcula las importancias con 20 canaritos y 5 semillas sobre la
#   etiqueta binaria BAJA+2, guarda sel/importancias_<nombre>.csv y escribe en sel/top150_<nombre>.txt las 150
#   primeras columnas que no son canaritos.
CONJUNTOS = {"A": [202103], "B": [202103, 202104], "Bh": [202104], "final": [202103, 202104, 202105, 202106]}

if __name__ == "__main__":
    (AQUI / "sel").mkdir(exist_ok=True)
    for nombre, meses in CONJUNTOS.items():
        t0 = time.time()
        X, y = xy(cargar(meses, negocio=True))
        imp = importancias_con_canaritos(X, y)
        imp.to_csv(AQUI / "sel" / f"importancias_{nombre}.csv")
        top = [c for c in imp.index if not c.startswith("canario_")][:150]
        (AQUI / "sel" / f"top150_{nombre}.txt").write_text("\n".join(top) + "\n")
        print(f"{nombre}: {X.shape[1]} cols -> top150 | n_ en el top150: {sum(c.startswith('n_') for c in top)} | {time.time()-t0:.0f}s", flush=True)
```

### competencia/experimentos/005_optuna/reevaluar.py

Lee los estudios de Optuna, arma las configuraciones top1 a top3 por conjunto y las vuelve a medir con 10 semillas distintas en los folds A, B y Bh. final_m2.py lo importa de forma indirecta a través de 028_todas_lags/run.py.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–27] Docstring, imports, folds A, B y Bh (202104 → 202106), 10 semillas de reevaluación
#   (SEMILLAS_20[2:12], distintas de las de búsqueda) y N_TOP = 3.
"""005 paso 2 — reevaluación honesta de los mejores trials: semillas DISTINTAS a las de la búsqueda (10 de SEMILLAS_20[2:]),
folds A, B y Bh (Bh no se usó en la búsqueda), ganancia = media sobre k=8000..15000 y k=11000.
Compara, por set (M0, M1): base_r1 (params del baseline, sin undersampling), base_r02 (trial 0), top1..top3 de Optuna, y mezclas:
MIX1 = promedio de las probabilidades de top1(M0) y top1(M1);  MIX6 = promedio de los 3 mejores de cada set.
Uso (raíz del repo): venv/bin/python competencia/experimentos/005_optuna/reevaluar.py"""
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from optuna_run import CONJUNTOS, DB, PARAMS_BASE, es_hist, escribir  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from pool import cargar  # noqa: E402
from validacion import KS, xy  # noqa: E402

FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
from config import SEMILLAS_20  # noqa: E402,F811  (explícitas en config.py; antes se leían de 002/resultados_20s.csv)
SEMILLAS_REEVAL = SEMILLAS_20[2:12]
N_TOP = 3


# [Anotación · líneas 29–46] configs() abre los estudios M0 y M1 de la base SQLite, ordena los trials
#   completos por valor y arma, por conjunto, cinco configuraciones: base sin submuestreo con 300 rondas, el
#   trial 0 (r = 0,2) y los tres trials de mayor valor (top1 a top3).
def params_de(p: dict):
    r, rounds = p["r"], p["num_boost_round"]
    return r, rounds, {**PARAMS_BASE, **{k: v for k, v in p.items() if k not in ("r", "num_boost_round")}}


def configs():
    """{(conjunto, nombre): (r, rounds, params)}"""
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    cfg = {}
    for c in CONJUNTOS:
        e = optuna.load_study(study_name=c, storage=f"sqlite:///{DB}")
        ok = sorted([t for t in e.trials if t.state == optuna.trial.TrialState.COMPLETE], key=lambda t: -t.value)
        cfg[(c, "base_r1")] = (1.0, 300, dict(PARAMS_BASE))
        cfg[(c, "base_r02")] = params_de(e.trials[0].params)
        for i, t in enumerate(ok[:N_TOP], 1):
            cfg[(c, f"top{i}")] = params_de(t.params)
            escribir(f"[reeval] {c} top{i}: trial #{t.number} índice búsqueda {t.value:.4f} | {t.params}")
    return cfg


# [Anotación · líneas 49–74] Bloque principal: en cada fold y semilla entrena cada configuración con su r,
#   predice la validación y agrega tres mezclas por promedio de probabilidades (MIX1, MIX6 y la de los trials
#   0). Guarda AUC, ganancia media en k = 8.000…15.000 y ganancia por k en reevaluacion.csv e imprime la tabla
#   por conjunto, configuración y fold.
if __name__ == "__main__":
    cfg = configs(); filas = []; t0 = time.time()
    escribir(f"\n===== reevaluación {time.strftime('%Y-%m-%d %H:%M')} | semillas {SEMILLAS_REEVAL} =====")
    for fold, (mt, mv) in FOLDS.items():
        (Xt, yt), (Xv, yv) = xy(cargar(mt, negocio=True)), xy(cargar([mv], negocio=True))
        cols = {"M0": [c for c in Xt.columns if not es_hist(c)],
                "M1": (AQUI / "sel" / f"top150_{fold}.txt").read_text().split()}
        yt, yv = yt.values, yv.values
        for s in SEMILLAS_REEVAL:
            P = {}
            for (c, nombre), (r, rounds, params) in cfg.items():
                keep = (yt == 1) | (np.random.RandomState(s).rand(len(yt)) < r)
                m = lgb.train({**params, "seed": s}, lgb.Dataset(Xt.loc[keep, cols[c]], label=yt[keep]), num_boost_round=rounds)
                P[(c, nombre)] = m.predict(Xv[cols[c]])
            P[("MIX", "MIX1")] = (P[("M0", "top1")] + P[("M1", "top1")]) / 2
            P[("MIX", "MIX6")] = np.mean([P[(c, f"top{i}")] for c in CONJUNTOS for i in range(1, N_TOP + 1)], axis=0)
            P[("MIX", "MIX_base_r02")] = (P[("M0", "base_r02")] + P[("M1", "base_r02")]) / 2
            for (c, nombre), p in P.items():
                acum = ganancia_acumulada(yv, p)
                filas.append({"fold": fold, "semilla": s, "conjunto": c, "config": nombre, "auc": roc_auc_score(yv, p),
                              "gan_media_k": np.mean([acum[k - 1] for k in KS]), **{f"gan_k{k}": acum[k - 1] for k in KS}})
            escribir(f"[reeval] fold {fold} semilla {s} listo ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(filas).to_csv(AQUI / "reevaluacion.csv", index=False)
    res = pd.DataFrame(filas); res.to_csv(AQUI / "reevaluacion.csv", index=False)
    tabla = (res.groupby(["conjunto", "config", "fold"]).gan_media_k.mean().div(1e6).round(1).unstack())
    print(tabla.to_string()); escribir("[reeval] terminado")
```

### competencia/experimentos/005_optuna/optuna_run.py

Búsqueda de hiperparámetros con Optuna en dos estudios alternados (M0 y M1), con el submuestreo r como un hiperparámetro más. Los scripts 017 y 010 importan de aquí es_hist().

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Docstring: dos estudios (M0 con 178 columnas sin historia y M1 con las 150
#   columnas por fold) que se alternan trial a trial; cada trial devuelve un índice de ganancia relativo a una
#   referencia por fold.
"""005 — Optuna sobre LightGBM, dos estudios (M0 y M1) que se alternan trial a trial.

M0 = 152 columnas originales + 26 `n_*` de negocio (178)      M1 = top150 con historia (pool de 345 columnas, selección por fold)
Cada trial: sortea hiperparámetros + `r` (fracción de negativos que se conserva, 007), entrena en los folds A y B con 2 semillas
de búsqueda (las dos primeras propias) y devuelve el ÍNDICE de ganancia = media de (ganancia_fold / referencia_fold), donde la
ganancia de un fold es la media sobre los k=8000..15000 (así no se optimiza un único k) y las referencias son A=220M, B=360M
(índice 1.000 ≈ baseline). Se usan dos folds con meses de validación distintos (202105 y 202106) para no sobreajustar a un mes.
Los mejores trials se reevalúan después con otras semillas y los 3 folds (ver reevaluar.py): no confiar en el valor de la búsqueda.

Uso (raíz del repo; deja correr, se puede cortar con Ctrl-C o creando el archivo STOP en esta carpeta):
    caffeinate -i venv/bin/python competencia/experimentos/005_optuna/optuna_run.py --horas 8
Progreso: `tail -f competencia/experimentos/005_optuna/optuna_log.txt`  o  `venv/bin/python competencia/experimentos/005_optuna/progreso.py`
"""
# [Anotación · líneas 14–38] Imports, ruta de la base SQLite (artifacts/optuna/005_optuna.db), folds A y B,
#   referencias de 220 M (A) y 360 M (B), las 2 primeras semillas propias para la búsqueda y el trial de base (r
#   0,2, 31 hojas, learning_rate 0,05, 300 rondas).
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables"))
from config import RAIZ, SEMILLAS  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from pool import cargar  # noqa: E402
from validacion import KS, PARAMS_BASE, xy  # noqa: E402

LOG = AQUI / "optuna_log.txt"
DB = RAIZ / "artifacts" / "optuna" / "005_optuna.db"
FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106)}
REFERENCIA = {"A": 220e6, "B": 360e6}
SEMILLAS_BUSQUEDA = SEMILLAS[:2]
CONJUNTOS = ["M0", "M1"]
BASELINE_TRIAL = {"r": 0.2, "num_leaves": 31, "learning_rate": 0.05, "min_data_in_leaf": 200, "feature_fraction": 0.5,
                  "bagging_fraction": 0.8, "lambda_l1": 1e-3, "lambda_l2": 1e-3, "num_boost_round": 300}
# [Anotación · líneas 39–48] Rangos de la ronda 1 (r 0,05–0,5; hojas 8–256; learning_rate 0,01–0,2;
#   min_data_in_leaf 20–1.000; feature_fraction 0,1–1; bagging_fraction 0,4–1; lambdas; 100–800 rondas) y de la
#   ronda 2 (rangos corridos y max_bin en 15, 31, 63 o 127). es_hist() marca como históricas las columnas con
#   _lag1, terminadas en _d1 o _r1, o que empiezan con r_.
# Ronda 1: rangos amplios. Ronda 2: rangos corridos hacia donde convergió la 1 (lr y rondas topaban con el borde) + max_bin.
ESPACIOS = {
    1: {"r": (0.05, 0.5), "num_leaves": (8, 256), "learning_rate": (0.01, 0.2), "min_data_in_leaf": (20, 1000),
        "feature_fraction": (0.1, 1.0), "bagging_fraction": (0.4, 1.0), "lambda_l1": (1e-3, 10), "lambda_l2": (1e-3, 100),
        "num_boost_round": (100, 800), "max_bin": None},
    2: {"r": (0.03, 0.3), "num_leaves": (16, 400), "learning_rate": (0.003, 0.03), "min_data_in_leaf": (10, 300),
        "feature_fraction": (0.05, 0.6), "bagging_fraction": (0.5, 1.0), "lambda_l1": (1e-3, 10), "lambda_l2": (1e-3, 100),
        "num_boost_round": (300, 1800), "max_bin": (15, 31, 63, 127)},
}
es_hist = lambda c: "_lag1" in c or c.endswith(("_d1", "_r1")) or c.startswith("r_")  # noqa: E731


# [Anotación · líneas 51–67] escribir() agrega líneas al log. preparar_datos() carga entrenamiento y
#   validación de cada fold con el pool y recorta a las columnas de M0 (las no históricas) y de M1
#   (sel/top150_<fold>.txt).
def escribir(texto: str):
    with open(LOG, "a") as f:
        f.write(texto + "\n")


def preparar_datos() -> dict:
    """datos[conjunto][fold] = (Xt, yt, Xv, yv): ya recortados a las columnas del conjunto (ahorra memoria)."""
    datos = {c: {} for c in CONJUNTOS}
    for fold, (mt, mv) in FOLDS.items():
        (Xt, yt), (Xv, yv) = xy(cargar(mt, negocio=True)), xy(cargar([mv], negocio=True))
        cols = {"M0": [c for c in Xt.columns if not es_hist(c)],
                "M1": (AQUI / "sel" / f"top150_{fold}.txt").read_text().split()}
        for c in CONJUNTOS:
            datos[c][fold] = (Xt[cols[c]].copy(), yt.values, Xv[cols[c]].copy(), yv.values)
        del Xt, Xv
        escribir(f"[datos] fold {fold}: M0 {len(cols['M0'])} cols, M1 {len(cols['M1'])} cols")
    return datos


# [Anotación · líneas 70–99] objetivo(): sortea r y los hiperparámetros; en cada fold y con cada una de las 2
#   semillas conserva los positivos y una fracción r del resto, entrena un LightGBM binario y promedia la
#   ganancia acumulada en k = 8.000…15.000. Devuelve la media entre folds de ganancia / referencia e informa el
#   valor parcial al pruner después del fold A.
def objetivo(trial: optuna.Trial, conjunto: str, datos: dict, ronda: int = 1) -> float:
    e = ESPACIOS[ronda]
    r = trial.suggest_float("r", *e["r"], log=True)
    params = {**PARAMS_BASE,
              "num_leaves": trial.suggest_int("num_leaves", *e["num_leaves"], log=True),
              "learning_rate": trial.suggest_float("learning_rate", *e["learning_rate"], log=True),
              "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", *e["min_data_in_leaf"], log=True),
              "feature_fraction": trial.suggest_float("feature_fraction", *e["feature_fraction"]),
              "bagging_fraction": trial.suggest_float("bagging_fraction", *e["bagging_fraction"]),
              "lambda_l1": trial.suggest_float("lambda_l1", *e["lambda_l1"], log=True),
              "lambda_l2": trial.suggest_float("lambda_l2", *e["lambda_l2"], log=True)}
    if e["max_bin"]:
        params["max_bin"] = trial.suggest_categorical("max_bin", list(e["max_bin"]))
    rounds = trial.suggest_int("num_boost_round", *e["num_boost_round"], log=True)
    indices = []
    for paso, fold in enumerate(FOLDS):
        Xt, yt, Xv, yv = datos[conjunto][fold]
        gans = []
        for s in SEMILLAS_BUSQUEDA:
            keep = (yt == 1) | (np.random.RandomState(s).rand(len(yt)) < r)      # undersampling (007)
            m = lgb.train({**params, "seed": s}, lgb.Dataset(Xt[keep], label=yt[keep]), num_boost_round=rounds)
            acum = ganancia_acumulada(yv, m.predict(Xv))
            gans.append(np.mean([acum[k - 1] for k in KS]))
        g = float(np.mean(gans))
        trial.set_user_attr(f"gan_{fold}", g / 1e6)
        indices.append(g / REFERENCIA[fold])
        trial.report(float(np.mean(indices)), paso)                               # el pruner puede cortar tras el fold A
        if trial.should_prune():
            raise optuna.TrialPruned()
    return float(np.mean(indices))


# [Anotación · líneas 102–111] callback() escribe en el log una línea por trial con estado, índice, ganancias
#   por fold, duración y parámetros.
def callback(study: optuna.Study, trial: optuna.trial.FrozenTrial):
    seg = (trial.datetime_complete - trial.datetime_start).total_seconds()
    ok = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    mejor = f"mejor {study.best_value:.4f} (#{study.best_trial.number})" if ok else "mejor -"
    p = trial.params
    resumen = " ".join(f"{k}={v:.3g}" if isinstance(v, float) else f"{k}={v}" for k, v in p.items())
    val = f"{trial.value:.4f}" if trial.value is not None else "  -   "
    gan = f"A {trial.user_attrs.get('gan_A', float('nan')):.1f}M B {trial.user_attrs.get('gan_B', float('nan')):.1f}M"
    escribir(f"{datetime.now():%m-%d %H:%M:%S} {study.study_name} #{trial.number:<4} {trial.state.name:<8} índice {val} ({gan}) {seg:4.0f}s | {mejor} | "
             f"{len(ok)} ok/{len(study.trials)} total | {resumen}")


# [Anotación · líneas 114–136] Bloque principal: argumentos --horas (8), --ronda, --db y --log; crea o retoma
#   un estudio por conjunto con TPESampler multivariado (semilla 771227, 25 trials iniciales) y PercentilePruner
#   al 75 %. En la ronda 1 encola el trial de base; en la ronda 2 encola los 5 trials de mayor valor de la ronda
#   1 con max_bin 31.
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--horas", type=float, default=8.0)
    ap.add_argument("--ronda", type=int, default=1, choices=[1, 2], help="2 = rangos corridos; estudios M0_r2/M1_r2, arranca con los mejores de la ronda 1")
    ap.add_argument("--db", default=str(DB), help="base SQLite (para pruebas, usar otra)"); ap.add_argument("--log", default=str(LOG))
    args = ap.parse_args(); DB, LOG = Path(args.db), Path(args.log)
    DB.parent.mkdir(parents=True, exist_ok=True)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    escribir(f"\n===== inicio {datetime.now():%Y-%m-%d %H:%M} | presupuesto {args.horas} h | semillas de búsqueda {SEMILLAS_BUSQUEDA} =====")
    datos = preparar_datos()
    estudios = {}
    sufijo = "" if args.ronda == 1 else f"_r{args.ronda}"
    for c in CONJUNTOS:
        e = optuna.create_study(study_name=c + sufijo, storage=f"sqlite:///{DB}", load_if_exists=True, direction="maximize",
                                sampler=optuna.samplers.TPESampler(seed=SEMILLAS[1], multivariate=True, n_startup_trials=25),
                                pruner=optuna.pruners.PercentilePruner(75.0, n_startup_trials=15, n_warmup_steps=0))
        if len(e.trials) == 0 and args.ronda == 1:
            e.enqueue_trial(BASELINE_TRIAL)       # el primer trial es el baseline con undersampling 0.2: sirve de referencia
        elif len(e.trials) == 0:                  # ronda 2: se re-evalúan los 5 mejores de la ronda 1 (con las mismas semillas de búsqueda) como ancla
            e1 = optuna.load_study(study_name=c, storage=f"sqlite:///{DB}")
            mejores = sorted([t for t in e1.trials if t.state == optuna.trial.TrialState.COMPLETE], key=lambda t: -t.value)[:5]
            for t in mejores:
                e.enqueue_trial({**t.params, "max_bin": 31})
        estudios[c] = e
# [Anotación · líneas 137–144] Hasta agotar el presupuesto de horas o encontrar un archivo STOP, ejecuta un
#   trial de M0 y uno de M1 por vuelta; Ctrl-C corta el bucle.
    fin = time.time() + args.horas * 3600
    try:
        while time.time() < fin and not (AQUI / "STOP").exists():
            for c, e in estudios.items():
                e.optimize(lambda t, c=c: objetivo(t, c[:2], datos, args.ronda), n_trials=1, callbacks=[callback])
    except KeyboardInterrupt:
        pass
    escribir(f"===== fin {datetime.now():%Y-%m-%d %H:%M} =====")
```

### competencia/experimentos/028_todas_lags/run.py

Experimento 028; define construir(), la función que final_m2.py importa para armar las 863 columnas de M2. El bloque principal del experimento no se ejecuta al importarlo.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–6] Docstring del experimento: compara, en multiclase, las 150 columnas M1 (V0), V0 más
#   lag2 de 50 variables (V1) y el conjunto con lag1, lag2 y diferencias de 142 variables (V2).
"""028 — la receta de los compañeros con Public > 100: lag1 y lag2 y diferencias (d1, d2) de TODAS las variables (≈ 760 columnas), sin selección, en el MULTICLASE con los
hiperparámetros tuneados de 005 (008c lo probó en binario con parámetros base). Folds con lag2 real en el train (como 016): L (202105 -> 202106) y B2 (202104+05 -> 202106),
con el solapamiento de targets en 202107 (informan la diferencia pareada, no el nivel). 4 semillas (SEMILLAS_20[2:6]); ccajas corregida.
  V0 M1 top150 (referencia) | V1 = V0 + lag2/delta2/ratio2 de las 50 variables (lo que usa el final, 016) | V2 = pool completo (345 cols) + lag1/delta1 de las 142 variables
  de 008c que faltaban + lag2/delta2 de las 142 (≈ 800 columnas, sin selección).
Ganancia = media sobre k=8000..15000 (M ARS). Uso (raíz del repo): venv/bin/python competencia/experimentos/028_todas_lags/run.py   |   tail -f competencia/experimentos/028_todas_lags/log.txt"""
# [Anotación · líneas 7–29] Imports (entre ellos reevaluar, de 005_optuna); activa CORREGIR_CCAJAS; define los
#   folds L (202105 → 202106) y B2 (202104–05 → 202106), 4 semillas, la lista de 142 variables de
#   008c_lags_150/variables_150.txt, las 92 que no están entre las 50 del pool y los nombres de las 150 columnas
#   lag2, d2 y r2 de las 50.
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
A005, A008C = AQUI.parents[0] / "005_optuna", AQUI.parents[0] / "008c_lags_150"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from historia import agregar_historia_n  # noqa: E402
from multiclase import entrenar, etiquetas, filas, gan_media, score_cond  # noqa: E402
from pool import VARS, cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
FOLDS = {"L": ([202105], 202106), "B2": ([202104, 202105], 202106)}
SEMILLAS_028 = SEMILLAS_20[2:6]
V142 = (A008C / "variables_150.txt").read_text().split()
EXTRA = [v for v in V142 if v not in VARS]
LAG2_50 = [f"{v}_{s}2" for v in VARS for s in ("lag", "d", "r")]


# [Anotación · líneas 32–35] escribir() imprime y agrega al log.
def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


# [Anotación · líneas 38–51] construir(): parte del pool de 345 columnas, agrega lag2, delta2 y ratio2 de las
#   50 variables, lag1 y delta1 de las 92 variables extra (sin ratio1) y lag2 y delta2 de esas 92 (sin ratio2),
#   y pasa las columnas float64 a float32. Resultan 863 columnas predictoras.
def construir(meses, solo_con_target=True):
    """DataFrame con todo lo necesario: pool (345) + lag2 de las 50 (para V1) + lag1/d1 de las 92 extra + lag2/d2 de las 142 (para V2)."""
    d = cargar(meses, solo_con_target=solo_con_target, negocio=True).copy()
    d = agregar_historia_n(d, VARS, 2)                                   # lag2/d2/r2 de las 50 (V1)
    l1 = agregar_historia_n(d[["numero_de_cliente", "foto_mes"] + EXTRA].copy(), EXTRA, 1).drop(columns=["numero_de_cliente", "foto_mes"] + EXTRA)
    l1 = l1[[c for c in l1.columns if not c.endswith("_r1")]]
    d = pd.concat([d, l1], axis=1)
    # lag2/d2 de las 92 extra (las 50 ya las tienen)
    l2 = agregar_historia_n(d[["numero_de_cliente", "foto_mes"] + EXTRA], EXTRA, 2).drop(columns=["numero_de_cliente", "foto_mes"] + EXTRA)
    l2 = l2[[c for c in l2.columns if not c.endswith("_r2")]]
    d = pd.concat([d, l2], axis=1)
    c = d.select_dtypes("float64").columns
    d[c] = d[c].astype("float32")
    return d


# [Anotación · líneas 54–79] Bloque principal del experimento: por fold y semilla entrena la configuración M1
#   top1 con cada conjunto de columnas, calcula la ganancia media en k = 8.000…15.000 y guarda resultados.csv y
#   comparacion.csv con las diferencias pareadas.
if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]
    base = (A005 / "sel" / "top150_Bh.txt").read_text().split()
    res, t0 = [], time.time()
    escribir(f"\n===== 028 {time.strftime('%Y-%m-%d %H:%M')} | {len(SEMILLAS_028)} semillas | {len(V142)} variables ({len(EXTRA)} extra) =====")
    for fold, (mt, mv) in FOLDS.items():
        dt, dv = construir(mt), construir([mv])
        todas = [c for c in dt.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria") and not c.startswith("canario")]
        sets = {"V0_top150": base, "V1_lag2_50": base + LAG2_50, "V2_todas_lags": todas}
        escribir(f"[{fold}] columnas: " + ", ".join(f"{n} {len(c)}" for n, c in sets.items()))
        y3, yv = etiquetas(dt), (dv["clase_ternaria"] == "BAJA+2").astype(int).values
        for s in SEMILLAS_028:
            keep, g = filas(y3, r, s), {}
            for n, cs in sets.items():
                g[n] = gan_media(yv, score_cond(entrenar(params, dt[cs], y3, keep, s, rondas).predict(dv[cs])))
                res.append({"fold": fold, "semilla": s, "variante": n, "M": g[n]})
            escribir(f"[{fold} s={s}] V0 {g['V0_top150']:.1f} | V1 {g['V1_lag2_50'] - g['V0_top150']:+.1f} | V2 {g['V2_todas_lags'] - g['V0_top150']:+.1f} ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.DataFrame(res); p = r_.pivot_table(index=["fold", "semilla"], columns="variante", values="M"); filas_ = []
    for a, b in [("V1_lag2_50", "V0_top150"), ("V2_todas_lags", "V0_top150"), ("V2_todas_lags", "V1_lag2_50")]:
        d = (p[a] - p[b]).groupby("fold")
        filas_.append({"comparacion": f"{a} - {b}", **{f"{f}_delta": d.mean()[f] for f in FOLDS}, **{f"{f}_ee": d.std()[f] / np.sqrt(len(SEMILLAS_028)) for f in FOLDS},
                       "pares_positivos": f"{int(((p[a] - p[b]) > 0).sum())}/{len(p)}"})
    comp = pd.DataFrame(filas_).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + r_.groupby(["variante", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas:\n" + comp.to_string(index=False)); escribir("[028] terminado")
```

### competencia/experimentos/017_final/final.py

Componente 017 de la mezcla: 6 configuraciones en multiclase con un binario auxiliar de BAJA+1 entrenado con un mes más (202107) y, con --lag2, lag2 de 50 variables en M1. Deja tmp/scores_202108_conlag2.csv.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–11] Docstring con el diseño: 6 configuraciones de 005, modelo principal multiclase con
#   202103–202106, auxiliar binario de BAJA+1 con 202103–202107, puntaje P2 / (1 − P1 del auxiliar), promedio
#   por semillas y luego promedio de ranks.
"""017 — MODELO FINAL de la Primera Competencia (un solo archivo).
Pipeline (todo validado en 010/013/014, ver LOG.md):
  - 6 configuraciones de 005 (3 mejores trials de Optuna de M0 y de M1, cada una con su r e hiperparámetros), `ccajas_depositos`=NA en 202105.
  - Principal MULTICLASE (CONTINUA/BAJA+1/BAJA+2), train 202103–202106: BAJA+1 y BAJA+2 completos + fracción r de CONTINUA. Da P(BAJA+2).
  - Auxiliar BINARIO de BAJA+1 (resto submuestreado con la misma r), train 202103–202107 (202107 solo aporta BAJA+1, que se conoce porque vemos 202108).
  - Score por modelo = P2_principal / (1 − P1_auxiliar); se promedia sobre semillas por configuración y luego se promedian los RANKS de las 6 configuraciones.
  - Se envían los k clientes con mayor score (k a elegir con 015; por defecto 11500).
Opciones: --semillas N (30: las 5 propias + derivadas, como en 005/final30), --k, --lag2 (suma lag2/delta2/ratio2 de las 50 variables a las configuraciones M1; solo si 016 lo avala).
Cada (configuración, semilla) se guarda en tmp/ y se salta si ya existe, así que se puede cortar y reanudar.
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/017_final/final.py --semillas 30 --k 11500 [--lag2]
Seguimiento:        tail -f competencia/experimentos/017_final/log.txt"""
# [Anotación · líneas 12–38] Imports; activa CORREGIR_CCAJAS; rutas de log y tmp, mapa de clases y nombres de
#   las 150 columnas lag2, d2 y r2 de las 50 variables.
import argparse
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
config.CORREGIR_CCAJAS = True
from config import ID_COL, MES_SCORING, SEMILLAS, TARGET_COL  # noqa: E402
from historia import agregar_historia_n  # noqa: E402
from modelos import guardar_modelo, verificar_orden_cache  # noqa: E402
from optuna_run import es_hist  # noqa: E402
from pool import VARS, cargar  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402
from validacion import PARAMS_BASE, xy  # noqa: E402

LOG, TMP = AQUI / "log.txt", AQUI / "tmp"
CLASES = {"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}
COLS_LAG2 = [f"{v}_{s}2" for v in VARS for s in ("lag", "d", "r")]


# [Anotación · líneas 41–56] configs_desde_json() lee mejores_trials.json y devuelve, por configuración, r,
#   cantidad de rondas y los parámetros de PARAMS_BASE pisados por los del trial. escribir() imprime y agrega al
#   log.
def configs_desde_json() -> dict:
    """{(conjunto, 'topN'): (r, rondas, params)} desde `005_optuna/mejores_trials.json` (versionado). Antes se leían de la base SQLite de Optuna
    (artifacts/, no versionada): ambas fuentes dan valores idénticos (verificado el 2026-10-08), pero el JSON permite reproducir sin repetir las 8 h de Optuna."""
    js = json.loads((A005 / "mejores_trials.json").read_text())
    out = {}
    for clave, d in js.items():
        c, n = clave.split("_")
        out[(c, n)] = (d["r"], d["num_boost_round"], {**PARAMS_BASE, **{k: v for k, v in d.items() if k not in ("r", "num_boost_round")}})
    return out


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


# [Anotación · líneas 58–70] Argumentos --semillas (30), --k (11.500) y --lag2. Carga con el pool
#   202103–202106 (principal), 202107 sin filtrar por clase (mes extra del auxiliar) y 202108 (a puntuar); con
#   --lag2 agrega a los tres lag2, delta2 y ratio2 de las 50 variables.
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--semillas", type=int, default=30); ap.add_argument("--k", type=int, default=11500)
    ap.add_argument("--lag2", action="store_true"); args = ap.parse_args()
    semillas = config.semillas(args.semillas)                       # semillas explícitas en config.py (5 propias + derivadas)
    semillas = semillas[:args.semillas]
    TAG = "conlag2" if args.lag2 else "sinlag2"        # antes el sufijo era lag0/lag1 (valor del flag) y confundía
    TMP.mkdir(exist_ok=True)
    cfg = configs_desde_json()
    dt = cargar([202103, 202104, 202105, 202106], negocio=True).copy()                   # principal: meses con BAJA+2 conocido
    dx = cargar([202107], solo_con_target=False, negocio=True).copy()                    # mes extra del auxiliar: solo BAJA+1 conocido
    score = cargar([MES_SCORING], solo_con_target=False, negocio=True).copy()
    if args.lag2:
        dt, dx, score = (agregar_historia_n(d, VARS, 2) for d in (dt, dx, score))
# [Anotación · líneas 71–79] Define las columnas: M0 son las no históricas (178 según el log) y M1 las de
#   top150_final.txt más, con --lag2, las 150 de lag2 (300). Arma la etiqueta de tres clases, une 202103–202107
#   para el auxiliar con etiqueta 1 si la clase es BAJA+1, escribe el encabezado del log y verifica el orden de
#   la caché.
    Xt0, _ = xy(dt)
    cols = {"M0": [c for c in Xt0.columns if not es_hist(c) and c in dt.columns and not c.endswith(("_lag2", "_d2", "_r2"))],
            "M1": (A005 / "sel" / "top150_final.txt").read_text().split() + (COLS_LAG2 if args.lag2 else [])}
    y3 = dt[TARGET_COL].map(CLASES).values
    da = pd.concat([dt, dx], ignore_index=True)                                          # auxiliar: 202103–07
    y1 = (da[TARGET_COL] == "BAJA+1").astype(int).values
    escribir(f"\n===== final 017 {time.strftime('%Y-%m-%d %H:%M')} | principal {dt.shape} | auxiliar {da.shape} (BAJA+1: {y1.sum()}) | score {score.shape} | "
             f"{len(semillas)} semillas x {len(cfg)} configs | k={args.k} | lag2={args.lag2} | M0 {len(cols['M0'])} cols, M1 {len(cols['M1'])} cols =====")
    verificar_orden_cache(TMP, score[ID_COL].values)                     # no mezclar predicciones cacheadas con otro orden de filas
# [Anotación · líneas 80–97] Para cada configuración y semilla sin caché: entrena el multiclase con todas las
#   filas BAJA+1 y BAJA+2 y una fracción r de CONTINUA y toma P(BAJA+2) sobre 202108; entrena el auxiliar
#   binario con los BAJA+1 y una fracción r del resto (sorteo con semilla + 1) y toma P(BAJA+1); guarda ambos
#   modelos con sus huellas y el puntaje P2 / (1 − P1) en un .npy. Promedia los puntajes entre semillas.
    t0, S = time.time(), {}
    for (c, nombre), (r, rondas, params) in cfg.items():
        ps = []
        for s in semillas:
            f = TMP / f"score_{c}_{nombre}_{s}_{TAG}.npy"
            if not f.exists():
                keep = (y3 >= 1) | (np.random.RandomState(s).rand(len(y3)) < r)
                mc = lgb.train({**params, "objective": "multiclass", "num_class": 3, "seed": s}, lgb.Dataset(dt.loc[keep, cols[c]], label=y3[keep]), num_boost_round=rondas)
                p2 = mc.predict(score[cols[c]])[:, 2]
                ka = (y1 == 1) | (np.random.RandomState(s + 1).rand(len(y1)) < r)
                aux = lgb.train({**params, "seed": s}, lgb.Dataset(da.loc[ka, cols[c]], label=y1[ka]), num_boost_round=rondas)
                p1 = aux.predict(score[cols[c]])
                guardar_modelo(mc, f"017_{TAG}_principal_{c}_{nombre}_{s}", p2)      # modelos en artifacts/ (no versionado) + huellas en el manifiesto
                guardar_modelo(aux, f"017_{TAG}_auxiliar_{c}_{nombre}_{s}", p1)
                np.save(f, p2 / np.clip(1 - p1, 1e-6, None))
            ps.append(np.load(f))
        S[f"{c}_{nombre}"] = np.mean(ps, axis=0)
        escribir(f"listo {c} {nombre} ({len(semillas)} semillas, {(time.time()-t0)/60:.0f} min)")
# [Anotación · líneas 98–109] Convierte el puntaje de cada configuración en rank dividido por la cantidad de
#   clientes y promedia los 6; guarda tmp/scores_202108_<TAG>.csv, que lee la mezcla final. Toma los k primeros
#   y, si el archivo exp017_final_... ya existe, informa si es idéntico; si no, lo escribe.
    ids = score[ID_COL].values
    rk = np.mean([rankdata(p) / len(p) for p in S.values()], axis=0)
    pd.DataFrame({ID_COL: ids, "rank": rk, **S}).to_csv(TMP / f"scores_202108_{TAG}.csv", index=False)
    nombre = f"exp017_final_s{len(semillas)}_k{args.k}" + ("_lag2" if args.lag2 else "")
    sub = AQUI.parents[1] / "submissions"
    top = top_k_ids(ids, rk, args.k)
    if (sub / f"{nombre}.csv").exists():       # reproducibilidad: si el archivo ya existe, se compara en vez de fallar
        previo = np.loadtxt(sub / f"{nombre}.csv", dtype=np.int64)
        escribir(f"{nombre}.csv ya existía: " + ("IDÉNTICO al regenerado (mismo conjunto y mismo orden)" if np.array_equal(previo, top) else
                 f"DISTINTO (mismo conjunto: {set(previo) == set(top)})"))
    else:
        escribir(guardar_submit(top, nombre).name)
# [Anotación · líneas 110–114] Informa el solapamiento del top-k con dos envíos anteriores, si sus archivos
#   existen.
    for previo in ("exp010_mc_h2_k11500", "exp005_final_s30_k11500"):
        f = sub / f"{previo}.csv"
        if f.exists():
            escribir(f"solapamiento top-{args.k} con {previo}: {len(set(top_k_ids(ids, rk, args.k)) & set(np.loadtxt(f, dtype=np.int64))) / args.k:.1%}")
    escribir("[final 017] terminado")
```

### competencia/src/validacion.py

Define PARAMS_BASE (diccionario de parámetros del que parten todas las configuraciones), los folds A y B, la grilla de k y las funciones xy(), evaluar() y resumen() de los experimentos.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–25] Docstring con los dos folds (A: 202103 → 202105; B: 202103 + 202104 → 202106) e
#   imports.
"""Validación out-of-time de 2 folds, común a todos los experimentos (ver competencia/PLAN.md).

  Fold A: train 202103            -> valid 202105
  Fold B: train 202103 + 202104   -> valid 202106   (el del baseline 001)
(Entre train y valid queda un mes de separación: el target de un mes mira 2 meses adelante.)

Uso típico:
    res = evaluar()                                  # baseline
    res = evaluar(transformar=mi_funcion)            # transformar(df) -> df con features modificadas
    res = evaluar(params={...}, rounds=500)          # otros hiperparámetros
    print(resumen(res))
`transformar` se aplica a train y a valid por separado: debe ser fila a fila o usar solo información del
propio mes (si necesita historia de otros meses, pasar `cargar=` propio que devuelva el DataFrame ya armado).
"""
import time
from typing import Callable

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from config import ID_COL, MES_COL, SEMILLAS, TARGET_COL, UMBRAL
from data import cargar_meses
from ganancia import ganancia_acumulada, ganancia_por_umbral

# [Anotación · líneas 27–38] Folds, 300 rondas por defecto y PARAMS_BASE: objective binary, max_bin 31,
#   num_leaves 31, learning_rate 0,05, min_data_in_leaf 200, feature_fraction 0,5, bagging_fraction 0,8 con
#   bagging_freq 1, deterministic y force_row_wise en True. Los scripts del final parten de este diccionario y
#   pisan los valores de cada configuración. KS son las cantidades de envíos 8.000 a 15.000 de a 1.000 y K_REF
#   es 11.000.
FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106)}
NUM_ROUNDS = 300
PARAMS_BASE = {
    "objective": "binary", "boosting_type": "gbdt", "max_bin": 31,
    "num_leaves": 31, "learning_rate": 0.05, "min_data_in_leaf": 200,
    "feature_fraction": 0.5, "bagging_fraction": 0.8, "bagging_freq": 1,
    "feature_pre_filter": False, "verbose": -1, "num_threads": 0,
    # Reproducibilidad: mismo resultado con cualquier cantidad de hilos/máquina (verificado: no cambia el modelo respecto de no ponerlo)
    "deterministic": True, "force_row_wise": True,
}
KS = list(range(8000, 15001, 1000))   # cantidades de envíos candidatas (rango permitido por el bot)
K_REF = 11000                         # k de referencia para comparar experimentos


# [Anotación · líneas 41–43] xy() separa las columnas predictoras (sin cliente, mes ni clase) y la etiqueta
#   binaria, que vale 1 si la clase es BAJA+2.
def xy(df: pd.DataFrame, quitar: tuple = ()):
    X = df.drop(columns=[c for c in (ID_COL, MES_COL, TARGET_COL, *quitar) if c in df.columns])
    return X, (df[TARGET_COL] == "BAJA+2").astype(int)


# [Anotación · líneas 46–71] evaluar() recorre folds y semillas: entrena LightGBM con los meses de
#   entrenamiento, predice el mes de validación y guarda AUC, ganancia por umbral 0,025, cantidad de clientes
#   sobre el umbral, ganancia máxima a posteriori con su k y ganancia en cada k de KS. La usan experimentos de
#   validación (por ejemplo 008c).
def evaluar(transformar: Callable | None = None, params: dict | None = None, rounds: int = NUM_ROUNDS,
            folds: dict = FOLDS, semillas=SEMILLAS, cargar: Callable = cargar_meses, quitar: tuple = (),
            verbose: bool = True) -> pd.DataFrame:
    """Una fila por (fold, semilla) con AUC y ganancias (mes completo, sin escalar)."""
    params = {**PARAMS_BASE, **(params or {})}
    filas = []
    for nombre, (meses_train, mes_valid) in folds.items():
        train, valid = cargar(meses_train), cargar([mes_valid])
        if transformar is not None:
            train, valid = transformar(train), transformar(valid)
        (Xt, yt), (Xv, yv) = xy(train, quitar), xy(valid, quitar)
        if verbose:
            print(f"fold {nombre}: train {Xt.shape} ({yt.sum()} BAJA+2) -> valid {mes_valid} {Xv.shape} ({yv.sum()} BAJA+2)")
        for s in semillas:
            t0 = time.time()
            # Dataset nuevo por semilla: el binning depende de `seed` (como en el baseline 001)
            p = lgb.train({**params, "seed": s}, lgb.Dataset(Xt, label=yt), num_boost_round=rounds).predict(Xv)
            acum = ganancia_acumulada(yv.values, p)
            filas.append({"fold": nombre, "semilla": s, "auc": roc_auc_score(yv, p),
                          "gan_umbral": ganancia_por_umbral(yv.values, p), "n_umbral": int((p >= UMBRAL).sum()),
                          "gan_max_expost": acum.max(), "k_max_expost": int(acum.argmax()) + 1,
                          **{f"gan_k{k}": acum[k - 1] for k in KS}})
            if verbose:
                print(f"  semilla {s}: AUC {filas[-1]['auc']:.4f} | k={K_REF}: {filas[-1][f'gan_k{K_REF}']/1e6:.1f}M "
                      f"| {time.time()-t0:.0f}s", flush=True)
    return pd.DataFrame(filas)


# [Anotación · líneas 74–83] resumen() calcula media y desvío entre semillas por fold, en millones, y agrega
#   una fila con la media de los folds A y B.
def resumen(res: pd.DataFrame) -> pd.DataFrame:
    """Media y desvío entre semillas por fold (ganancias en millones) + fila 'A+B' con la media de los folds."""
    cols = ["auc", "gan_umbral", "gan_max_expost"] + [f"gan_k{k}" for k in KS]
    m = res.groupby("fold")[cols].mean()
    s = res.groupby("fold")[cols].std()
    out = pd.concat({"media": m, "desvio": s}, axis=1)
    out.loc["A+B"] = pd.concat([m.mean(), s.mean()]).values
    ganancias = [c for c in out.columns if c[1] != "auc"]
    out[ganancias] = out[ganancias] / 1e6
    return out.round(3)
```

### competencia/src/multiclase.py

Funciones del modelo de tres clases: etiquetas, máscara de submuestreo de CONTINUA, entrenamiento y puntaje condicional.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–10] Docstring, imports y mapa de clases: CONTINUA = 0, BAJA+1 = 1, BAJA+2 = 2.
"""Funciones comunes de los experimentos con el modelo MULTICLASE (CONTINUA/BAJA+1/BAJA+2), ver 010/013/020-022.
Score condicional P(BAJA+2)/(1-P(BAJA+1)); filas de train = BAJA+1 y BAJA+2 completos + fracción r de CONTINUA."""
import lightgbm as lgb
import numpy as np

from config import TARGET_COL
from ganancia import ganancia_acumulada
from validacion import KS

CLASES = {"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}


# [Anotación · líneas 13–19] etiquetas() convierte clase_ternaria en 0, 1 o 2. filas() arma la máscara de
#   entrenamiento: todas las filas BAJA+1 y BAJA+2 y cada CONTINUA con probabilidad r, sorteada con
#   RandomState(seed); con r = 1,0 quedan todas.
def etiquetas(df) -> np.ndarray:
    return df[TARGET_COL].map(CLASES).values


def filas(y3: np.ndarray, r: float, seed: int) -> np.ndarray:
    """Máscara de entrenamiento: BAJA+1 y BAJA+2 siempre, CONTINUA con probabilidad r (r=1.0 = sin undersampling)."""
    return (y3 >= 1) | (np.random.RandomState(seed).rand(len(y3)) < r)


# [Anotación · líneas 22–28] entrenar() llama a lgb.train con objective multiclass, num_class 3 y la semilla,
#   sobre las filas de la máscara y con pesos opcionales. score_cond() calcula P(BAJA+2) / (1 − P(BAJA+1)), con
#   el denominador acotado por debajo en 1e-6.
def entrenar(params: dict, X, y3, keep, seed: int, rondas: int, peso=None):
    return lgb.train({**params, "objective": "multiclass", "num_class": 3, "seed": seed},
                     lgb.Dataset(X[keep], label=y3[keep], weight=None if peso is None else peso[keep]), num_boost_round=rondas)


def score_cond(pm: np.ndarray) -> np.ndarray:
    return pm[:, 2] / np.clip(1 - pm[:, 1], 1e-6, None)


# [Anotación · líneas 31–34] gan_media() devuelve la media de la ganancia acumulada en k = 8.000, 9.000, …,
#   15.000, en millones; la usan los experimentos de validación.
def gan_media(yv, p) -> float:
    """Ganancia media sobre k=8000..15000, en millones de ARS."""
    acum = ganancia_acumulada(yv, p)
    return float(np.mean([acum[k - 1] for k in KS])) / 1e6
```

### competencia/src/submit.py

Escritura y validación del CSV de envío y selección de los k clientes de mayor puntaje.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–14] Docstring con el formato del archivo (sin encabezado, un numero_de_cliente entero
#   por línea), carpeta de salida competencia/submissions y límites de 8.000 y 15.000 registros.
"""Armado y validación de archivos de submit (formato Zulip de la cátedra).

Formato: CSV sin encabezado, un numero_de_cliente entero por línea (los clientes a estimular),
entre 8000 y 15000 registros. Cuidado con la notación científica (48000000 → 4.8e+07).
"""
import re
from pathlib import Path

import numpy as np

from config import RAIZ

SUBMISSIONS = RAIZ / "competencia" / "submissions"
MIN_ENVIOS, MAX_ENVIOS = 8000, 15000


# [Anotación · líneas 17–34] guardar_submit() verifica que los identificadores sean enteros y no se repitan,
#   que la cantidad esté entre 8.000 y 15.000, que el nombre sólo tenga letras, dígitos, guion y guion bajo y
#   que el archivo no exista; escribe con np.savetxt y formato %d.
def guardar_submit(ids, nombre: str, carpeta: Path = SUBMISSIONS) -> Path:
    """Escribe `<nombre>.csv` con los ids a estimular. Usar un nombre de archivo distinto en cada submit."""
    ids = np.asarray(ids)
    if not np.all(np.mod(ids, 1) == 0):
        raise ValueError("los numero_de_cliente deben ser enteros")
    ids = ids.astype(np.int64)
    if len(np.unique(ids)) != len(ids):
        raise ValueError("hay numero_de_cliente repetidos")
    if not MIN_ENVIOS <= len(ids) <= MAX_ENVIOS:
        raise ValueError(f"{len(ids)} registros: el bot espera entre {MIN_ENVIOS} y {MAX_ENVIOS}")
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", nombre):
        raise ValueError("nombre sin espacios ni caracteres raros")
    ruta = carpeta / f"{nombre}.csv"
    if ruta.exists():
        raise FileExistsError(f"{ruta.name} ya existe: usar un nombre distinto para cada submit")
    carpeta.mkdir(parents=True, exist_ok=True)
    np.savetxt(ruta, ids, fmt="%d")  # %d garantiza enteros, sin encabezado
    return ruta


# [Anotación · líneas 37–45] top_k_ids() devuelve los k clientes de mayor puntaje con un orden estable.
#   cuerpo_mensaje() arma el texto 'submit    <nombre>' del mensaje de Zulip; el módulo no envía el mensaje.
def top_k_ids(ids, proba, k: int):
    """Los k clientes con mayor probabilidad (corte por cantidad de envíos)."""
    orden = np.argsort(-np.asarray(proba), kind="stable")[:k]
    return np.asarray(ids)[orden]


def cuerpo_mensaje(nombre_submit: str) -> str:
    """Cuerpo del mensaje de Zulip. Se adjuntan uno o más .csv (máx 20 por submit, 13 submits/día)."""
    return f"submit    {nombre_submit}"
```

### competencia/src/seleccion.py

Importancia de variables con columnas de ruido (canaritos); 005_optuna/seleccion.py la usa para generar las listas de 150 columnas.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Docstring con la idea de los canaritos (columnas de ruido agregadas al
#   entrenamiento) e imports.
"""Selección de variables con "canaritos": columnas de ruido puro agregadas al entrenamiento.

Idea: una variable real que el modelo usa menos que una columna de ruido aleatorio no está aportando señal (los
árboles la usan igual para ajustar ruido del train). Se entrena con N canaritos U(0,1), se promedia la importancia
(gain relativo) entre semillas y se descartan las variables cuya importancia no supera el umbral de los canaritos.
Solo se mira el train: nunca el mes de validación.
"""
import lightgbm as lgb
import numpy as np
import pandas as pd

from config import SEMILLAS
from validacion import NUM_ROUNDS, PARAMS_BASE


# [Anotación · líneas 16–31] importancias_con_canaritos(): por cada semilla (las 5 propias por defecto) agrega
#   20 columnas U(0,1) llamadas canario_i, entrena un LightGBM con PARAMS_BASE y 300 rondas y toma el gain de
#   cada columna dividido por el total; devuelve media y desvío entre semillas, de mayor a menor.
def importancias_con_canaritos(X: pd.DataFrame, y, semillas=SEMILLAS, n_canaritos: int = 20,
                               params: dict | None = None, rounds: int = NUM_ROUNDS) -> pd.DataFrame:
    """Gain relativo (suma 1 por modelo) de cada columna, media y desvío entre semillas. Los canaritos se llaman
    `canario_i` y se redibujan en cada semilla."""
    params = {**PARAMS_BASE, **(params or {})}
    filas = []
    for s in semillas:
        rng = np.random.RandomState(s)
        canarios = pd.DataFrame(rng.rand(len(X), n_canaritos), columns=[f"canario_{i}" for i in range(n_canaritos)],
                                index=X.index)
        Xc = pd.concat([X, canarios], axis=1)
        m = lgb.train({**params, "seed": s}, lgb.Dataset(Xc, label=y), num_boost_round=rounds)
        g = pd.Series(m.feature_importance("gain"), index=Xc.columns)
        filas.append(g / g.sum())
    imp = pd.concat(filas, axis=1)
    return pd.DataFrame({"gain_media": imp.mean(axis=1), "gain_sd": imp.std(axis=1)}).sort_values("gain_media", ascending=False)


# [Anotación · líneas 34–39] elegir() devuelve las variables cuya importancia media supera el máximo de los
#   canaritos (regla 'max') o su percentil 90 (regla 'p90'); la usa el experimento 004, no el camino de la
#   entrega.
def elegir(imp: pd.DataFrame, regla: str = "max") -> list[str]:
    """Variables (sin canaritos) cuya importancia media supera el umbral de los canaritos:
    'max' = el mejor canarito (estricto), 'p90' = percentil 90 de los canaritos (más permisivo)."""
    es_can = imp.index.str.startswith("canario_")
    umbral = imp.loc[es_can, "gain_media"].max() if regla == "max" else imp.loc[es_can, "gain_media"].quantile(0.9)
    return [c for c in imp.index[~es_can] if imp.loc[c, "gain_media"] > umbral]
```

### competencia/src/drift.py

PSI por variable y clasificador que distingue un mes de otro; final_m2.py usa psi() para excluir columnas de lag2.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Docstring que describe las tres funciones e imports de lightgbm, numpy, pandas y
#   scikit-learn.
"""Detección de drift sin usar el target: PSI por variable y validación adversarial.

psi(ref, act)        Population Stability Index con bins por cuantiles de la referencia; los nulos son un bin propio.
tabla_psi(df_ref, df_act, cols)   PSI de cada columna.
adversarial(df_a, df_b, cols)     LightGBM que intenta distinguir el mes A del mes B (AUC ~0.5 = sin drift);
                                  devuelve (AUC en hold-out, importancias por gain).
"""
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


# [Anotación · líneas 15–27] psi() calcula el Population Stability Index entre una serie de referencia y otra
#   actual: 10 intervalos por cuantiles de la referencia con extremos abiertos, un intervalo aparte para los
#   nulos, proporciones acotadas por debajo en 0,0001 y suma de (a − e) · ln(a / e).
def psi(ref: pd.Series, act: pd.Series, bins: int = 10, eps: float = 1e-4) -> float:
    ref_n, act_n = ref.dropna(), act.dropna()
    if ref_n.nunique() < 2:
        cortes = np.array([-np.inf, np.inf])
    else:
        cortes = np.unique(np.quantile(ref_n, np.linspace(0, 1, bins + 1)))
        cortes[0], cortes[-1] = -np.inf, np.inf
    def prop(s):
        h = np.histogram(s.dropna(), bins=cortes)[0].astype(float)
        p = np.append(h, s.isna().sum()) / max(len(s), 1)   # último bin = nulos
        return np.clip(p, eps, None)
    e, a = prop(ref), prop(act)
    return float(np.sum((a - e) * np.log(a / e)))


# [Anotación · líneas 30–31] tabla_psi() aplica psi() a una lista de columnas y ordena de mayor a menor.
def tabla_psi(df_ref: pd.DataFrame, df_act: pd.DataFrame, cols) -> pd.Series:
    return pd.Series({c: psi(df_ref[c], df_act[c]) for c in cols}).sort_values(ascending=False)


# [Anotación · líneas 34–43] adversarial() entrena un LightGBM de 100 rondas que distingue las filas de un mes
#   de las de otro, con 30 % de las filas apartadas de forma estratificada, y devuelve el AUC y la importancia
#   relativa por gain; la usa el experimento 008_c1.
def adversarial(df_a: pd.DataFrame, df_b: pd.DataFrame, cols, semilla: int = 852583, rounds: int = 100):
    X = pd.concat([df_a[cols], df_b[cols]], ignore_index=True)
    y = np.r_[np.zeros(len(df_a)), np.ones(len(df_b))]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, stratify=y, random_state=semilla)
    params = {"objective": "binary", "num_leaves": 31, "learning_rate": 0.1, "feature_fraction": 0.5,
              "max_bin": 31, "seed": semilla, "verbose": -1, "num_threads": 0}
    m = lgb.train(params, lgb.Dataset(Xtr, label=ytr), num_boost_round=rounds)
    auc = roc_auc_score(yte, m.predict(Xte))
    imp = pd.Series(m.feature_importance("gain"), index=cols).sort_values(ascending=False)
    return auc, imp / imp.sum()
```

### competencia/src/features.py

Variables construidas con datos del mismo mes. El camino de la entrega usa ratios_entre_variables() (17 columnas r_*) y features_negocio() (26 columnas n_*); el resto de las funciones corresponde a los experimentos 002, 003c y 011.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Docstring e imports; listas de las 2 columnas de cierre de tarjeta y de las 6 de
#   fechas en días, y valor centinela −100.000 para 'sin fecha'.
"""Transformaciones de variables del EDA 002 (ver experimentos/002_eda_variables/README.md).
Todas reciben un DataFrame con varios meses (columna foto_mes) y devuelven una copia; son fila a fila o usan
solo información del propio mes, así que no filtran futuro.
"""
import numpy as np
import pandas as pd

CIERRES = ["Master_fultimo_cierre", "Visa_fultimo_cierre"]
# variables que miden "días desde/hasta un evento" y avanzan 30/31 por mes aunque el evento sea el mismo
FECHAS_DIAS = ["Master_fechaalta", "Visa_fechaalta", "Master_Fvencimiento", "Visa_Fvencimiento",
               "Master_Finiciomora", "Visa_Finiciomora"]
SENTINELA = -100_000   # Fvencimiento ≈ -2.914.000 = "sin fecha"


# [Anotación · líneas 15–58] Transformaciones del experimento 002, fuera del camino de la entrega: fecha de la
#   foto en días, cierre de tarjeta relativo a la moda del mes, eliminación de las columnas de cierre, paso de
#   'días desde el evento' a fecha absoluta y de antigüedad a mes de ingreso, y marcado como NaN de
#   Visa_Finiciomora y Visa_delinquency en las filas con Visa_Finiciomora = 0.
def fin_de_mes_en_dias(foto_mes: pd.Series) -> pd.Series:
    """Fecha de la foto (último día del mes) como días desde 1970-01-01."""
    f = pd.to_datetime(foto_mes.astype(str) + "01", format="%Y%m%d") + pd.offsets.MonthEnd(0)
    return (f - pd.Timestamp("1970-01-01")).dt.days


def cierre_relativo(df: pd.DataFrame) -> pd.DataFrame:
    """fultimo_cierre vale lo mismo para ~77% de los clientes de un mes (la fecha de cierre del ciclo) y cambia
    de mes en mes (1,2,5,0,3,6): sólo identifica el mes. Lo reemplazamos por la diferencia contra la moda del mes
    (0 / +7 / +14 / +21 = a qué ciclo de facturación pertenece el cliente), que sí es estable."""
    df = df.copy()
    for c in CIERRES:
        moda = df.groupby("foto_mes")[c].transform(lambda s: s.mode().iloc[0] if s.notna().any() else np.nan)
        df[c + "_rel"] = df[c] - moda
        df = df.drop(columns=c)
    return df


def sacar_cierre(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=CIERRES)


def fechas_absolutas(df: pd.DataFrame) -> pd.DataFrame:
    """Pasa 'días desde/hasta el evento' a la fecha absoluta del evento (= fecha de la foto - días), que no cambia
    entre meses para el mismo cliente. La antigüedad en meses pasa a 'mes de ingreso' (ordinal de mes)."""
    df = df.copy()
    fin = fin_de_mes_en_dias(df["foto_mes"])
    for c in FECHAS_DIAS:
        x = df[c].where(df[c] > SENTINELA)          # el centinela -2914xxx es "sin fecha": nulo
        df[c + "_abs"] = fin - x
        df = df.drop(columns=c)
    mes_ord = df["foto_mes"] // 100 * 12 + df["foto_mes"] % 100
    df["cliente_ingreso_mes"] = mes_ord - df["cliente_antiguedad"]
    return df.drop(columns="cliente_antiguedad")


def artefacto_visa(df: pd.DataFrame) -> pd.DataFrame:
    """En 202105 y 202108 ~2% de los clientes aparece con Visa_delinquency=1 y Visa_Finiciomora=0 (en el resto de los
    meses es 0 filas): artefacto de calendario, no mora real (su tasa de BAJA+2 es la de un cliente normal).
    Los marcamos como dato roto (NaN), como sugiere el libro (§13.3)."""
    df = df.copy()
    roto = df["Visa_Finiciomora"] == 0
    df.loc[roto, ["Visa_Finiciomora", "Visa_delinquency"]] = np.nan
    return df


# [Anotación · líneas 61–72] _div() divide dejando NaN cuando el denominador es 0 o falta; _suma() suma series
#   tratando NaN como 0 salvo que falten todos los sumandos.
# --- 003c: features del mes actual (no usan historia ni otros meses) ---------------------------------------------
def _div(a: pd.Series, b: pd.Series) -> pd.Series:
    """a/b con NaN cuando el denominador es 0 o falta (evita inf)."""
    return a / b.replace(0, np.nan)


def _suma(*series: pd.Series) -> pd.Series:
    """Suma que trata NaN como 0 (no tiene la tarjeta) pero devuelve NaN si faltan todos."""
    out = series[0]
    for s in series[1:]:
        out = out.add(s, fill_value=0)
    return out


# [Anotación · líneas 75–100] ratios_entre_variables() agrega 17 columnas r_*: sueldo por transacción; saldo,
#   rentabilidad y transacciones por producto; uso del límite y pago sobre saldo de Visa y Master; ticket medio
#   por tarjeta; suma de consumos de tarjetas; consumo sobre sueldo; deuda y margen pasivo sobre saldo;
#   comisiones sobre rentabilidad y transferencias recibidas sobre emitidas.
def ratios_entre_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Ratios con sentido de negocio, definidos a priori (no elegidos mirando la validación). Normalizan por tamaño
    del cliente: ticket promedio, uso del límite de tarjeta, gasto vs. ingreso, deuda vs. saldo, etc."""
    df = df.copy()
    consumo_tarjetas = _suma(df.Visa_mconsumototal, df.Master_mconsumototal)
    deuda = _suma(df.mprestamos_personales, df.mprestamos_prendarios, df.mprestamos_hipotecarios)
    nuevas = {
        "r_payroll_por_trx": _div(df.mpayroll, df.cpayroll_trx),
        "r_saldo_por_producto": _div(df.mcuentas_saldo, df.cproductos),
        "r_rentab_por_producto": _div(df.mrentabilidad, df.cproductos),
        "r_trx_por_producto": _div(df.ctrx_quarter, df.cproductos),
        "r_visa_uso_limite": _div(df.Visa_msaldototal, df.Visa_mlimitecompra),
        "r_master_uso_limite": _div(df.Master_msaldototal, df.Master_mlimitecompra),
        "r_visa_consumo_limite": _div(df.Visa_mconsumototal, df.Visa_mlimitecompra),
        "r_visa_pago_saldo": _div(df.Visa_mpagospesos, df.Visa_msaldopesos),
        "r_master_pago_saldo": _div(df.Master_mpagospesos, df.Master_msaldopesos),
        "r_visa_ticket": _div(df.mtarjeta_visa_consumo, df.ctarjeta_visa_transacciones),
        "r_master_ticket": _div(df.mtarjeta_master_consumo, df.ctarjeta_master_transacciones),
        "r_consumo_tarjetas": consumo_tarjetas,
        "r_gasto_vs_ingreso": _div(consumo_tarjetas, df.mpayroll),
        "r_deuda_vs_saldo": _div(deuda, df.mcuentas_saldo),
        "r_margen_pasivo_saldo": _div(df.mpasivos_margen, df.mcuentas_saldo),
        "r_comisiones_rentab": _div(df.mcomisiones, df.mrentabilidad),
        "r_transf_recibidas_emitidas": _div(df.mtransferencias_recibidas, df.mtransferencias_emitidas),
    }
    return df.assign(**nuevas)


# [Anotación · líneas 103–109] rangos_en_el_mes() agrega el percentil (0–1) de cada variable dentro de su
#   foto_mes en columnas con sufijo _rk; la usa el experimento 003c.
def rangos_en_el_mes(df: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    """Percentil (0–1) de cada variable dentro de su propio mes: cambia 'cuánto' por 'qué tan arriba está respecto
    del resto de los clientes ese mes'. Es robusto a drift y a inflación; solo mira filas del mismo foto_mes."""
    df = df.copy()
    rangos = df.groupby("foto_mes")[variables].rank(pct=True)
    rangos.columns = [f"{c}_rk" for c in variables]
    return pd.concat([df, rangos], axis=1)


# [Anotación · líneas 112–148] features_negocio() agrega 26 columnas n_*: ingresos, egresos, neto y cociente
#   entre ambos; parte del sueldo en los ingresos; inversiones, deuda y patrimonio; saldo del paquete y parte en
#   dólares; límite y saldo total de tarjetas y su cociente; comisiones; descuentos; rentabilidad mensual × 12
#   sobre la anual; márgenes sobre rentabilidad; cantidad de seguros; transacciones digitales y físicas; y
#   cantidad de productos con valor mayor que 0 entre 17 indicadores.
def features_negocio(df: pd.DataFrame) -> pd.DataFrame:
    """003d — sumas, restas y ratios agregados por grupos de negocio, definidos a priori (no mirando la validación).
    Usan solo columnas del mismo mes. NaN en un componente cuenta como 0 mientras haya al menos otro dato."""
    df = df.copy()
    S = _suma
    ingresos = S(df.mpayroll, df.mpayroll2, df.mtransferencias_recibidas, df.mcheques_depositados)
    egresos = S(df.mtransferencias_emitidas, df.mcheques_emitidos, df.mpagodeservicios, df.mpagomiscuentas,
                df.mextraccion_autoservicio, df.mcuenta_debitos_automaticos, df.mttarjeta_visa_debitos_automaticos,
                df.mttarjeta_master_debitos_automaticos)
    inversiones = S(df.mplazo_fijo_dolares, df.mplazo_fijo_pesos, df.minversion1_pesos, df.minversion1_dolares, df.minversion2)
    deuda = S(df.mprestamos_personales, df.mprestamos_prendarios, df.mprestamos_hipotecarios)
    saldo_paquete = S(df.mcuenta_corriente, df.mcaja_ahorro, df.mcaja_ahorro_dolares, df.mcuenta_corriente_adicional, df.mcaja_ahorro_adicional)
    limite = S(df.Visa_mlimitecompra, df.Master_mlimitecompra)
    saldo_tarjetas = S(df.Visa_msaldototal, df.Master_msaldototal)
    comisiones = S(df.mcomisiones_mantenimiento, df.mcomisiones_otras)
    trx_digital = S(df.chomebanking_transacciones, df.cmobile_app_trx)
    trx_fisica = S(df.ccajas_transacciones, df.catm_trx, df.catm_trx_other)
    indicadores = ["ccuenta_corriente", "ccaja_ahorro", "ctarjeta_debito", "ctarjeta_visa", "ctarjeta_master", "cprestamos_personales",
                   "cprestamos_prendarios", "cprestamos_hipotecarios", "cplazo_fijo", "cinversion1", "cinversion2", "cseguro_vida",
                   "cseguro_auto", "cseguro_vivienda", "cseguro_accidentes_personales", "ccaja_seguridad", "cpayroll_trx"]
    nuevas = {
        "n_ingresos": ingresos, "n_egresos": egresos, "n_neto": ingresos - egresos, "n_ingr_sobre_egr": _div(ingresos, egresos),
        "n_payroll_share": _div(df.mpayroll, ingresos),
        "n_inversiones": inversiones, "n_deuda": deuda, "n_patrimonio": S(df.mcuentas_saldo, inversiones) - deuda.fillna(0),
        "n_inv_sobre_patrim": _div(inversiones, S(df.mcuentas_saldo, inversiones)),
        "n_saldo_paquete": saldo_paquete, "n_usd_share": _div(df.mcaja_ahorro_dolares, saldo_paquete),
        "n_limite_total": limite, "n_saldo_tarjetas": saldo_tarjetas, "n_uso_limite_total": _div(saldo_tarjetas, limite),
        "n_comisiones": comisiones, "n_comis_mant_share": _div(df.mcomisiones_mantenimiento, comisiones),
        "n_descuentos": S(df.mtarjeta_visa_descuentos, df.mtarjeta_master_descuentos, df.mcajeros_propios_descuentos),
        "n_rentab_mes_vs_anual": _div(df.mrentabilidad * 12, df.mrentabilidad_annual),
        "n_pasivos_sobre_rentab": _div(df.mpasivos_margen, df.mrentabilidad), "n_activos_sobre_rentab": _div(df.mactivos_margen, df.mrentabilidad),
        "n_seguros": S(df.cseguro_vida, df.cseguro_auto, df.cseguro_vivienda, df.cseguro_accidentes_personales),
        "n_trx_digital": trx_digital, "n_trx_fisica": trx_fisica, "n_digital_share": _div(trx_digital, S(trx_digital, trx_fisica)),
        "n_productos_activos": sum((df[c].fillna(0) > 0).astype(int) for c in indicadores),
        "n_activos_sobre_cproductos": _div(sum((df[c].fillna(0) > 0).astype(int) for c in indicadores), df.cproductos),
    }
    return df.assign(**nuevas)


# [Anotación · líneas 151–169] agregados_cambios() cuenta por fila cuántas variables con lag1 > 0 cayeron 50 %
#   o más, pasaron a 0 o subieron 50 % o más, y calcula la media del cambio relativo acotado a [−1, 2];
#   experimento 011.
# --- 011: agregados de cambios, eventos de productos, comisiones normalizadas --------------------------------------
def agregados_cambios(df: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    """Conteos fila a fila sobre los cambios vs el mes anterior de `variables` (usa `{v}_lag1` y `{v}_r1` ya armadas).
    Un árbol no puede construir un conteo sobre 50 columnas: 'cuántas variables cayeron a la mitad' resume una señal difusa de que el
    cliente se está desarmando. Solo cuentan variables con lag > 0 (si no, el cambio relativo no está definido). NaN si no hay historia."""
    lag = df[[f"{v}_lag1" for v in variables]].to_numpy(dtype=float)
    hoy = df[variables].to_numpy(dtype=float)
    r = np.clip(df[[f"{v}_r1" for v in variables]].to_numpy(dtype=float), -1, 2)
    validas = lag > 0
    n_val = validas.sum(axis=1).astype(float)
    sin_hist = np.isnan(lag).all(axis=1)
    cae50 = (validas & (r <= -0.5)).sum(axis=1)
    cero = (validas & (np.nan_to_num(hoy, nan=0) == 0)).sum(axis=1)
    sube50 = (validas & (r >= 0.5)).sum(axis=1)
    out = pd.DataFrame({"g_n_validas": n_val, "g_n_cae50": cae50, "g_n_a_cero": cero, "g_n_sube50": sube50,
                        "g_share_cae50": cae50 / np.where(n_val > 0, n_val, np.nan),
                        "g_media_r1": np.nanmean(np.where(validas, r, np.nan), axis=1)}, index=df.index)
    out[sin_hist] = np.nan
    return out


# [Anotación · líneas 172–190] eventos_productos() compara el mes actual con el lag1: productos perdidos y
#   ganados entre 17 indicadores y banderas de dejar de cobrar sueldo, de consumir con tarjetas y de usar
#   homebanking; devuelve NaN si el cliente no estaba el mes anterior; experimento 011.
def eventos_productos(df: pd.DataFrame, lag: pd.DataFrame) -> pd.DataFrame:
    """Eventos entre el mes anterior y este (`lag` = columnas `{v}_lag1` de lags_crudos): productos perdidos/ganados y banderas de
    'dejó de cobrar sueldo', 'dejó de usar la tarjeta', 'dejó de usar homebanking'. NaN (no 0) si el cliente no tenía el mes anterior."""
    indicadores = ["ccuenta_corriente", "ccaja_ahorro", "ctarjeta_debito", "ctarjeta_visa", "ctarjeta_master", "cprestamos_personales",
                   "cprestamos_prendarios", "cprestamos_hipotecarios", "cplazo_fijo", "cinversion1", "cinversion2", "cseguro_vida",
                   "cseguro_auto", "cseguro_vivienda", "cseguro_accidentes_personales", "ccaja_seguridad", "cpayroll_trx"]
    hay = lag["cproductos_lag1"].notna()
    hoy = lambda c: df[c].fillna(0)            # noqa: E731  (NaN = no tiene el producto)
    ant = lambda c: lag[f"{c}_lag1"].fillna(0)  # noqa: E731
    perdidos = sum(((ant(c) > 0) & (hoy(c) == 0)).astype(int) for c in indicadores)
    ganados = sum(((ant(c) == 0) & (hoy(c) > 0)).astype(int) for c in indicadores)
    consumo_ant = ant("Visa_mconsumototal") + ant("Master_mconsumototal"); consumo = hoy("Visa_mconsumototal") + hoy("Master_mconsumototal")
    ev = {"e_prod_perdidos": perdidos, "e_prod_ganados": ganados, "e_prod_neto": ganados - perdidos,
          "e_dejo_payroll": ((ant("mpayroll") > 0) & (hoy("mpayroll") == 0)).astype(int),
          "e_dejo_payroll_trx": ((ant("cpayroll_trx") > 0) & (hoy("cpayroll_trx") == 0)).astype(int),
          "e_dejo_consumo_tarjetas": ((consumo_ant > 0) & (consumo == 0)).astype(int),
          "e_dejo_homebanking": ((ant("chomebanking_transacciones") > 0) & (hoy("chomebanking_transacciones") == 0)).astype(int),
          "e_d_cproductos": df["cproductos"] - lag["cproductos_lag1"]}
    return pd.DataFrame(ev, index=df.index).where(hay)


# [Anotación · líneas 193–198] comisiones_normalizadas() divide mcomisiones_mantenimiento por la mediana de
#   sus valores positivos en el mismo mes; experimento 011.
def comisiones_normalizadas(df: pd.DataFrame) -> pd.DataFrame:
    """`mcomisiones_mantenimiento` dividida por la mediana (de los valores > 0) de su propio mes: el monto nominal salta de un mes a otro
    (C1 de 008: la variable que más separa 202108 del train) y la versión relativa debería sobrevivir. Solo mira filas del mismo mes."""
    x = df["mcomisiones_mantenimiento"]
    mediana = x.where(x > 0).groupby(df["foto_mes"]).transform("median")
    return pd.DataFrame({"mcomisiones_mant_norm": x / mediana}, index=df.index)
```

### competencia/src/modelos.py

Guardado de cada booster, registro de huellas SHA-256 en un manifiesto y control del orden de filas de las predicciones en caché.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–17] Docstring, imports y rutas: los modelos van a artifacts/modelos_final/ y las
#   huellas a competencia/modelos_manifiesto.csv, con columnas nombre, sha256_modelo y sha256_prediccion.
"""Guardado de modelos y huellas, para NO tener que reentrenar (cada modelo del final cuesta minutos) y para poder verificar la reproducción.

- El modelo (texto de LightGBM, decenas de MB) se guarda en `artifacts/modelos_final/` -> NO se versiona (tamaño; el repo es público).
- Lo que SÍ se versiona es `competencia/modelos_manifiesto.csv`: por cada modelo, la huella SHA-256 del archivo de modelo y de su predicción sobre el mes a puntuar.
  Quien regenere el pipeline puede comprobar que obtiene exactamente los mismos modelos comparando huellas (`competencia/verificar_modelos.py`).
"""
import csv
import hashlib
from pathlib import Path

import numpy as np

from config import RAIZ

CARPETA = RAIZ / "artifacts" / "modelos_final"
MANIFIESTO = RAIZ / "competencia" / "modelos_manifiesto.csv"
COLUMNAS = ["nombre", "sha256_modelo", "sha256_prediccion"]


# [Anotación · líneas 20–36] huella_arreglo() calcula el SHA-256 de un arreglo convertido a float64;
#   huella_archivo() el de un archivo leído en bloques de 1 MB; _leer() carga el manifiesto como diccionario por
#   nombre.
def huella_arreglo(a) -> str:
    return hashlib.sha256(np.ascontiguousarray(a, dtype=np.float64).tobytes()).hexdigest()


def huella_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _leer() -> dict:
    if not MANIFIESTO.exists():
        return {}
    with open(MANIFIESTO, newline="") as f:
        return {fila["nombre"]: fila for fila in csv.DictReader(f)}


# [Anotación · líneas 39–51] guardar_modelo() escribe el booster como texto en
#   artifacts/modelos_final/<nombre>.txt y reescribe el manifiesto, ordenado por nombre, con la huella del
#   archivo y la de la predicción.
def guardar_modelo(booster, nombre: str, prediccion=None) -> Path:
    """Guarda el booster en artifacts/modelos_final/<nombre>.txt y registra sus huellas en el manifiesto (reemplaza la entrada si ya existía)."""
    CARPETA.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA / f"{nombre}.txt"
    booster.save_model(str(ruta))
    filas = _leer()
    filas[nombre] = {"nombre": nombre, "sha256_modelo": huella_archivo(ruta),
                     "sha256_prediccion": huella_arreglo(prediccion) if prediccion is not None else ""}
    with open(MANIFIESTO, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas[k] for k in sorted(filas))
    return ruta


# [Anotación · líneas 54–67] verificar_orden_cache() guarda en tmp/_orden_scoring.md5 el MD5 del orden de los
#   numero_de_cliente a puntuar. Si la marca existe y difiere, o si hay archivos .npy sin marca, lanza un
#   RuntimeError que pide borrar tmp/ y reentrenar.
def verificar_orden_cache(tmp: Path, ids) -> None:
    """Guarda contra un error silencioso: las predicciones cacheadas (`tmp/*.npy`) son vectores POSICIONALES (una entrada por fila de scoring).
    Si se generaron con otro orden de filas (p. ej. antes del ORDER BY explícito del 2026-10-10) y se cargan con el orden actual, los scores
    quedarían asignados a los clientes equivocados sin ningún error. Se deja una marca con la huella del orden de `ids` y se exige que coincida."""
    huella = hashlib.md5(np.ascontiguousarray(ids, dtype=np.int64).tobytes()).hexdigest()
    marca = Path(tmp) / "_orden_scoring.md5"
    if marca.exists():
        if marca.read_text().strip() != huella:
            raise RuntimeError(f"{tmp}: las predicciones cacheadas se generaron con otro orden de filas. Borrar o mover esa carpeta tmp/ y reentrenar.")
    else:
        if any(Path(tmp).glob("*.npy")):
            raise RuntimeError(f"{tmp}: hay predicciones cacheadas SIN marca de orden (corrida anterior al ORDER BY explícito). Borrar o mover esa carpeta tmp/ y reentrenar.")
        Path(tmp).mkdir(parents=True, exist_ok=True)
        marca.write_text(huella)
```

### competencia/src/historia.py

Variables históricas: lags por join de cliente y mes anterior, deltas y cocientes; incluye funciones de control y de variables derivadas que sólo usan los experimentos.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–12] Docstring: los lags se arman con un join explícito por cliente y mes anterior, de
#   modo que un cliente ausente el mes previo queda con NaN; 202103 no tiene mes anterior. Imports.
"""Features históricas: valor del mismo cliente en meses anteriores (solo pasado, nunca futuro).

El lag se arma con un join explícito por (cliente, mes anterior) y no con `lag()` sobre filas: si un cliente no
estaba el mes anterior (cliente nuevo) el lag es NaN, en lugar de agarrar un mes más viejo sin avisar.

Ojo con el borde: 202103 no tiene mes anterior, así que todos sus lags son NaN (ver PLAN.md / exp 003).
"""
import numpy as np
import pandas as pd

from config import ID_COL, MES_COL, TARGET_COL
from data import conectar


# [Anotación · líneas 15–17] mes_anterior_sql() devuelve la expresión SQL del mes de hace n meses en formato
#   AAAAMM, restando 88 + n cuando cruza el año.
def mes_anterior_sql(col: str = MES_COL, n: int = 1) -> str:
    """Expresión SQL del mes n meses atrás (formato AAAAMM, cruza el año)."""
    return f"(case when ({col} % 100) - {n} >= 1 then {col} - {n} else {col} - 88 - {n} end)"


# [Anotación · líneas 20–28] cargar_con_lags() une la vista c01 consigo misma por cliente y mes de hace n
#   meses y agrega una columna {v}_lag{n} por variable; filtra los meses pedidos, opcionalmente las filas con
#   clase, y ordena por mes y cliente.
def cargar_con_lags(meses: list[int], variables: list[str], n: int = 1, solo_con_target: bool = True) -> pd.DataFrame:
    """Meses pedidos + `{v}_lag{n}` para cada variable (valor del cliente n meses antes, NaN si no estaba)."""
    lista = ",".join(str(m) for m in meses)
    lags = ", ".join(f'p."{v}" as "{v}_lag{n}"' for v in variables)
    filtro_t = f"and a.{TARGET_COL} is not null" if solo_con_target else ""
    sql = (f"select a.*, {lags} from c01 a left join c01 p "
           f"on a.{ID_COL} = p.{ID_COL} and p.{MES_COL} = {mes_anterior_sql('a.' + MES_COL, n)} "
           f"where a.{MES_COL} in ({lista}) {filtro_t} order by a.{MES_COL}, a.{ID_COL}")   # orden determinista (ver data.py)
    return conectar().sql(sql).df()


# [Anotación · líneas 31–39] agregar_historia_n() consulta el lag n de las variables para los meses de un
#   DataFrame ya armado, lo une uno a uno por cliente y mes y agrega los deltas y cocientes de orden n.
def agregar_historia_n(df: pd.DataFrame, variables: list[str], n: int) -> pd.DataFrame:
    """A un df ya armado le suma `{v}_lag{n}`, `{v}_d{n}` y `{v}_r{n}` (join por cliente y mes de hace n meses; NaN si no estaba).
    Sirve para sumar el lag 2 sin rehacer el pool; el orden de filas de `df` se conserva."""
    lista = ",".join(str(m) for m in sorted(df[MES_COL].unique()))
    lags = ", ".join(f'p."{v}" as "{v}_lag{n}"' for v in variables)
    sql = (f"select a.{ID_COL}, a.{MES_COL}, {lags} from c01 a left join c01 p "
           f"on a.{ID_COL} = p.{ID_COL} and p.{MES_COL} = {mes_anterior_sql('a.' + MES_COL, n)} where a.{MES_COL} in ({lista})")
    out = df.merge(conectar().sql(sql).df(), on=[ID_COL, MES_COL], how="left", validate="one_to_one")
    return agregar_ratios(agregar_deltas(out, variables, n), variables, n)


# [Anotación · líneas 42–57] agregar_deltas() crea {v}_d{n} = valor actual − lag n. agregar_ratios() crea
#   {v}_r{n} = valor / lag − 1, con NaN cuando el lag es 0 o falta.
def agregar_deltas(df: pd.DataFrame, variables: list[str], n: int = 1) -> pd.DataFrame:
    """`{v}_d{n}` = valor actual - valor de hace n meses (NaN si no hay lag)."""
    df = df.copy()
    for v in variables:
        df[f"{v}_d{n}"] = df[v] - df[f"{v}_lag{n}"]
    return df


def agregar_ratios(df: pd.DataFrame, variables: list[str], n: int = 1) -> pd.DataFrame:
    """`{v}_r{n}` = cambio relativo vs hace n meses = v/lag - 1 (NaN si no hay lag o el lag es 0).
    Distinto del delta: normaliza por el tamaño del cliente (un cambio de $10k no es lo mismo con saldo 20k que 2M)."""
    df = df.copy()
    for v in variables:
        lag = df[f"{v}_lag{n}"].replace(0, np.nan)
        df[f"{v}_r{n}"] = df[v] / lag - 1
    return df


# [Anotación · líneas 60–75] quitar_historia() elimina las columnas históricas. barajar_historia() permuta,
#   dentro de cada mes y con RandomState(seed), las filas del bloque de columnas históricas; la usan
#   experimentos de control (por ejemplo 029), no el camino de la entrega.
def quitar_historia(df: pd.DataFrame) -> pd.DataFrame:
    """Saca todas las columnas históricas (deja las variables originales): sirve de baseline pareado."""
    return df.drop(columns=[c for c in df.columns if "_lag" in c or c.endswith(("_d1", "_d2", "_r1", "_r2"))])


def barajar_historia(df: pd.DataFrame, seed: int, cols: list[str] | None = None) -> pd.DataFrame:
    """Control: permuta las filas de las columnas históricas DENTRO de cada mes (bloque completo, a la vez).
    Mantiene las distribuciones y la proporción de NaN por mes pero rompe el vínculo con el cliente: si el modelo
    mejora con esto, la ganancia viene del patrón de NaN/calendario y no de la información de la historia."""
    df = df.copy()
    cols = cols or [c for c in df.columns if "_lag" in c or c.endswith(("_d1", "_d2", "_r1", "_r2"))]
    rng = np.random.RandomState(seed)
    for _, idx in df.groupby(MES_COL).indices.items():
        perm = rng.permutation(len(idx))
        df.iloc[idx, [df.columns.get_loc(c) for c in cols]] = df[cols].iloc[idx[perm]].values
    return df


# [Anotación · líneas 78–87] lags_crudos() devuelve sólo las columnas {v}_lag{n} alineadas con las filas de un
#   DataFrame, sin pegarlas; la usa el experimento 011.
def lags_crudos(df: pd.DataFrame, variables: list[str], n: int = 1) -> pd.DataFrame:
    """Solo las columnas `{v}_lag{n}` (valor de hace n meses; NaN si el cliente no estaba), alineadas con las filas de `df`.
    A diferencia de `agregar_historia_n` no se las pega a `df`: sirve cuando `df` ya trae algunas de esas columnas."""
    lista = ",".join(str(m) for m in sorted(df[MES_COL].unique()))
    lags = ", ".join(f'p."{v}" as "{v}_lag{n}"' for v in variables)
    sql = (f"select a.{ID_COL}, a.{MES_COL}, {lags} from c01 a left join c01 p "
           f"on a.{ID_COL} = p.{ID_COL} and p.{MES_COL} = {mes_anterior_sql('a.' + MES_COL, n)} where a.{MES_COL} in ({lista})")
    out = df[[ID_COL, MES_COL]].merge(conectar().sql(sql).df(), on=[ID_COL, MES_COL], how="left", validate="one_to_one")
    out.index = df.index
    return out.drop(columns=[ID_COL, MES_COL])


# [Anotación · líneas 90–112] lag_derivadas() calcula lag, delta y cociente de orden n para variables
#   derivadas (n_*, r_*): carga los meses previos, recalcula esas variables con features_negocio y
#   ratios_entre_variables, desplaza el mes n posiciones y une por cliente y mes. La usa el experimento 011.
def lag_derivadas(df: pd.DataFrame, columnas: list[str], n: int = 1) -> pd.DataFrame:
    """`{c}_lag{n}`, `{c}_d{n}` y `{c}_r{n}` para features DERIVADAS (n_*, r_*): el valor de la feature calculada con los datos del mes
    de hace n meses (la feature se calcula mes por mes con features_negocio/ratios_entre_variables y después se desplaza).
    NaN si ese mes no existe o el cliente no estaba. Usa solo meses anteriores."""
    from data import cargar_meses
    from features import features_negocio, ratios_entre_variables
    meses = sorted(df[MES_COL].unique())
    previos = sorted({m_ant for m in meses if (m_ant := int(m - 88 - n if (m % 100) - n < 1 else m - n)) >= 202103})
    if not previos:
        return pd.DataFrame({f"{c}_{s}{n}": np.nan for c in columnas for s in ("lag", "d", "r")}, index=df.index)
    raw = cargar_meses(previos, solo_con_target=False)
    der = features_negocio(ratios_entre_variables(raw))[[ID_COL, MES_COL] + columnas]
    # mes siguiente al del dato, para que el join con df sea (cliente, mes de df)
    der[MES_COL] = np.where(der[MES_COL] % 100 + n <= 12, der[MES_COL] + n, der[MES_COL] + 88 + n)
    der = der.rename(columns={c: f"{c}_lag{n}" for c in columnas})
    out = df[[ID_COL, MES_COL]].merge(der, on=[ID_COL, MES_COL], how="left", validate="one_to_one")
    out.index = df.index
    res = out.drop(columns=[ID_COL, MES_COL])
    for c in columnas:
        lag = res[f"{c}_lag{n}"]
        res[f"{c}_d{n}"] = df[c] - lag
        res[f"{c}_r{n}"] = df[c] / lag.replace(0, np.nan) - 1
    return res
```

### competencia/src/data.py

Carga del dataset con DuckDB: vista sobre el parquet (o el CSV), corrección opcional de ccajas_depositos y lectura de meses con orden fijo.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–17] conectar() abre DuckDB y crea la vista c01 sobre el parquet si existe o, si no,
#   sobre el CSV. Con config.CORREGIR_CCAJAS en True reemplaza ccajas_depositos por NULL en las filas de 202105
#   y deja igual el resto de las columnas.
"""Carga del dataset con DuckDB (lazy: no trae todo el CSV a memoria)."""
import duckdb
import pandas as pd

import config
from config import CSV, MES_COL, PARQUET, TARGET_COL


def conectar() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    fuente = (f"read_parquet('{PARQUET.as_posix()}')" if PARQUET.exists()
              else f"read_csv_auto('{CSV.as_posix()}')")   # parquet si existe, si no el CSV
    # `* replace` deja todas las columnas igual salvo ccajas_depositos en 202105 (rota: todo 0) -> NA. Ver config.CORREGIR_CCAJAS.
    corregir = (f"replace (case when {MES_COL} = 202105 then null else ccajas_depositos end as ccajas_depositos)"
                if config.CORREGIR_CCAJAS else "")
    con.sql(f"create view c01 as select * {corregir} from {fuente}")
    return con


# [Anotación · líneas 20–26] cargar_meses() devuelve un DataFrame con los meses pedidos, opcionalmente sólo
#   las filas con clase_ternaria no nula, ordenado por foto_mes y numero_de_cliente.
def cargar_meses(meses: list[int], solo_con_target: bool = True) -> pd.DataFrame:
    """DataFrame con los meses pedidos. Para entrenar/validar usar solo_con_target=True."""
    filtro_t = f"and {TARGET_COL} is not null" if solo_con_target else ""
    lista = ",".join(str(m) for m in meses)
    # ORDER BY explícito: sin él DuckDB devuelve las filas en un orden que cambia entre corridas (lecturas paralelas) y, como el
    # undersampling sortea por POSICIÓN, cada corrida entrenaba con otros clientes (ver REPRODUCIR.md §0).
    return conectar().sql(f"select * from c01 where {MES_COL} in ({lista}) {filtro_t} order by {MES_COL}, numero_de_cliente").df()
```

### competencia/src/ganancia.py

Funciones de ganancia: por umbral, acumulada por cantidad de envíos y corte de máxima ganancia. La búsqueda de Optuna y los experimentos usan ganancia_acumulada().

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–13] Docstring, imports y _es_positivo(), que acepta etiquetas de texto (BAJA+2) o
#   binarias (1).
"""Funciones de ganancia de la campaña de retención.

y_true: array de etiquetas ('BAJA+2' / otras) o binario (1 = BAJA+2).
proba:  probabilidad predicha de BAJA+2.
"""
import numpy as np

from config import COSTO_ESTIMULO, GANANCIA_ACIERTO, POSITIVO, UMBRAL


def _es_positivo(y_true) -> np.ndarray:
    y = np.asarray(y_true)
    return (y == POSITIVO) if y.dtype.kind in "OUS" else (y == 1)


# [Anotación · líneas 16–21] ganancia_por_umbral(): suma 1.072.500 por cada positivo y resta 27.500 por cada
#   otro cliente con probabilidad mayor o igual al umbral (0,025 por defecto), y divide por la fracción de datos
#   evaluada.
def ganancia_por_umbral(y_true, proba, umbral: float = UMBRAL, prop: float = 1.0) -> float:
    """Ganancia total si se estimula a todos los clientes con proba >= umbral.
    `prop` es la fracción de los datos evaluada (se reescala dividiendo por prop)."""
    pos = _es_positivo(y_true)
    estimula = np.asarray(proba) >= umbral
    return float((np.where(pos, GANANCIA_ACIERTO, -COSTO_ESTIMULO)[estimula]).sum() / prop)


# [Anotación · líneas 24–28] ganancia_acumulada(): ordena por probabilidad descendente con orden estable y
#   devuelve la suma acumulada; el elemento k − 1 es la ganancia de enviar a los k primeros.
def ganancia_acumulada(y_true, proba) -> np.ndarray:
    """Ganancia acumulada ordenando por proba descendente: el elemento k-1 es la ganancia de enviar a los k primeros."""
    pos = _es_positivo(y_true)
    orden = np.argsort(-np.asarray(proba), kind="stable")
    return np.cumsum(np.where(pos[orden], GANANCIA_ACIERTO, -COSTO_ESTIMULO))


# [Anotación · líneas 31–35] mejor_corte(): cantidad de envíos que maximiza la ganancia acumulada y su valor,
#   calculados sobre los mismos datos.
def mejor_corte(y_true, proba) -> tuple[int, float]:
    """(cantidad óptima de envíos, ganancia máxima). OJO: óptimo ex post sobre estos datos."""
    acum = ganancia_acumulada(y_true, proba)
    k = int(np.argmax(acum))
    return k + 1, float(acum[k])
```


## Explicaciones del alumno (texto original)

### competencia/GLOSARIO.md

> # Glosario de la Primera Competencia
>
> Para poder volver más adelante y entender los términos, números y nombres que aparecen en `LOG.md`, `REPRODUCIR.md`, `COBERTURA.md` y los README de cada experimento. Cada entrada dice qué significa **en este proyecto** y dónde aparece. Los números de experimento (001, 037a…) son las carpetas de `experimentos/`.
>
> **Índice:** [1. El problema](#1-el-problema-y-la-métrica) · [2. Validación](#2-validación-folds-y-comparaciones) · [3. Estadística de las comparaciones](#3-estadística-de-las-comparaciones) · [4. Modelos y conjuntos de columnas](#4-modelos-y-conjuntos-de-columnas-m0-m1-m2) · [5. Features](#5-features-variables-construidas) · [6. Entrenamiento e hiperparámetros](#6-entrenamiento-e-hiperparámetros) · [7. Ensembles y mezcla](#7-ensembles-y-mezclas) · [8. Drift y calidad de datos](#8-drift-y-calidad-de-datos) · [9. Leaderboard y entrega](#9-leaderboard-y-entrega) · [10. Sesgos y vicios metodológicos](#10-sesgos-y-vicios-metodológicos-que-hay-que-reconocer) · [11. Cómo leer una tabla y los nombres](#11-cómo-leer-una-tabla-de-resultados-y-los-nombres)
>
> ---
>
> ## 1. El problema y la métrica
>
> | Término | Qué es |
> |---|---|
> | **Paquete Premium, cliente-mes** | Cada fila del dataset es un cliente en un mes (`numero_de_cliente`, `foto_mes` = AAAAMM). Solo titulares de Paquete Premium. Meses disponibles: 202103 a 202108 |
> | **`clase_ternaria`** | Etiqueta que se construye mirando el futuro del cliente: **CONTINUA** (reaparece dentro de 2 meses), **BAJA+1** (no está el mes siguiente), **BAJA+2** (está el mes siguiente pero no a los dos meses). Los dos últimos meses no tienen etiqueta completa: 202107 solo tiene BAJA+1 conocido; 202108 no tiene ninguna |
> | **BAJA+2 = positivo** | Es lo que se predice: al cliente que dentro de dos meses ya no está se lo puede alcanzar a tiempo con un estímulo. BAJA+1 ya se fue (tarde para retenerlo) |
> | **Prevalencia** | Proporción de positivos: ≈ 0,6% (≈ 1.000 BAJA+2 por mes sobre ≈ 164.000 clientes) |
> | **Función de ganancia** | Enviar estímulo a un BAJA+2 gana **+1.072.500**; enviarlo a cualquier otro cuesta **−27.500**; no enviar es 0. La ganancia de un envío = 1.072.500 × aciertos − 27.500 × errores |
> | **Punto de equilibrio (p\*)** | Probabilidad a partir de la cual conviene enviar: 27.500 / (1.072.500 + 27.500) = **0,025** (2,5%). Un cliente con P(BAJA+2) ≥ 2,5% tiene ganancia esperada positiva |
> | **k, corte por cantidad** | En vez de cortar por probabilidad, se envían los **k clientes con mayor score**. El bot exige 8.000 ≤ k ≤ 15.000. En este trabajo el final usa k = 12.000. Se prefiere porque las probabilidades de LightGBM no están calibradas (005c) |
> | **Ganancia acumulada** | Ganancia si se envía a los primeros 1, 2, …, k clientes ordenados por score. El máximo ex post es el "óptimo" de un mes (depende del mes: ≈ 9–11 veces los positivos, 015) |
> | **`gan_media_k` / "ganancia media sobre k"** | Promedio de la ganancia acumulada en k = 8.000, 9.000, …, 15.000. Es la métrica de casi todos los experimentos: no depende de un k puntual. Se reporta en **millones de ARS** (M) de un mes completo |
> | **AUC** | Probabilidad de que un positivo reciba más score que un negativo (0,5 = azar). Mide el ranking sin importar el corte; sube poco (0,89–0,90) aunque la ganancia cambie decenas de M |
> | **Positivos esperados** | Estimación del número de BAJA+2 en 202108 a partir de la suma de probabilidades del modelo (razón ≈ 3,7 entre suma de P2 y positivos reales, 018): ≈ 1.150–1.200 |
>
> ## 2. Validación: folds y comparaciones
>
> | Término | Qué es |
> |---|---|
> | **Out-of-time (OOT)** | Entrenar con meses anteriores y validar en un mes posterior. Es lo único honesto para una predicción a futuro; nunca se valida en el mismo mes de entrenamiento |
> | **Mes de separación (gap)** | Como la etiqueta de un mes mira 2 meses adelante, entre el último mes de train y el de validación tiene que haber un mes, para que la etiqueta de train no "vea" el valid |
> | **Fold** | Una partición concreta (meses de train → mes de valid). Los usados: **A** (train 202103 → valid 202105); **B** (202103+04 → 202106, el del baseline); **Bh** (202104 → 202106: la "h" es de *historia*: solo filas con lags reales); **L** (202105 → 202106: el único train con lag2 real); **B2** (202104+05 → 202106) |
> | **Solapamiento de targets** | En L y B2 la etiqueta del mes de train 202105 mira 202106–07 y la del valid 202106 mira 202107–08: comparten el mes 202107. Puede inflar las ganancias de features que capturan eventos de ese mes. Por eso se prefirió la validación en 202107 |
> | **Proxy / tarea proxy (036)** | Validar en 202107 con **BAJA+1** como etiqueta (sí se conoce) en vez de BAJA+2 (no se conoce). Es un mes limpio, sin aguinaldo y sin solapamiento de targets, pero **no es el mismo objetivo** (BAJA+1 ya se fue); sirve para elegir entre variantes de features, no para estimar la ganancia |
> | **Semilla pareada** | Para comparar dos variantes se entrenan ambas con las **mismas semillas** y se restan los resultados semilla a semilla. Quita gran parte del ruido de entrenamiento |
> | **Escala local vs Public** | La ganancia local es de un **mes completo**; el Public es ≈ **25%** de los clientes. Una diferencia local de +8M equivale a ≈ +2M en el Public. Hay que dividir por ≈ 4 antes de compararlas |
> | **Régimen (de datos)** | Cuántos meses de train hay: 1 mes (A, Bh, L), 2 meses (B, B2), 4 meses (el final). Varias conclusiones cambian de signo con el régimen (026, 018) |
>
> ## 3. Estadística de las comparaciones
>
> | Término | Qué es |
> |---|---|
> | **Delta (Δ)** | Diferencia de ganancia entre una variante y su base, en M ARS. Positivo = la variante gana |
> | **Error estándar (ee) de la diferencia** | Desvío de las diferencias por semilla dividido por √(n semillas). Mide cuánto "se mueve" el promedio de la diferencia por ruido de entrenamiento. Regla práctica del proyecto: una diferencia se toma en serio si |Δ| > **~2 ee**. Ojo: mide ruido de semillas, **no** la variación entre meses ni entre muestras de clientes |
> | **Pares positivos (p. ej. 5/5, 12/15)** | En cuántas de las comparaciones semilla-fold la variante le gana a la base. 5/5 es consistente; 2/6 es ruido |
> | **Test t pareado unilateral** | Test sobre las diferencias por semilla (H0: Δ ≤ 0). Da un p-valor: probabilidad de ver un Δ así de grande por azar |
> | **Comparaciones múltiples / forking paths** | Cuantas más variantes se prueban sobre los mismos datos, más probable es que alguna salga bien por casualidad. Es el problema central de este trabajo: decenas de pruebas sobre dos meses |
> | **FDR y Benjamini–Hochberg (BH)** | *False Discovery Rate*: proporción esperada de "descubrimientos" falsos. BH ordena los p-valores de menor a mayor y acepta el i-ésimo si p(i) ≤ q·i/m (q = 0,10, m = nº de pruebas). Se fijó de antemano para el plan 037 (libro §19) |
> | **Umbral de +3M** | Tamaño mínimo que importa: por debajo de eso, no justifica el riesgo de reentrenar el final aunque sea "significativo" |
> | **Regla fijada antes de ver el resultado (pre-registro)** | Se escribe en el documento la condición de adopción antes de correr el experimento, para no ajustarla a lo que salga. Ejemplo: 018, 037 |
> | **Potencia (de un test)** | Capacidad de detectar un efecto real. El Public del bot tiene poca potencia: ±2–3M de ruido contra efectos de ≈ 1–2M |
> | **Control barajado** | Experimento de control: se permutan al azar las columnas nuevas dentro de cada mes (conservan distribución y nulos, pierden el vínculo con el cliente). Si la ganancia sobrevive, era un artefacto; si desaparece, era información (008b, 029) |
> | **Winner's curse (maldición del ganador)** | El mejor de varios resultados ruidosos está sesgado hacia arriba. Por eso no se elige el modelo por el Public ni se confía en el "mejor trial" de Optuna sin reevaluarlo con semillas nuevas |
>
> ## 4. Modelos y conjuntos de columnas (M0, M1, M2…)
>
> | Término | Qué es |
> |---|---|
> | **M0** | Conjunto de **178 columnas sin historia**: 152 originales + 26 variables de negocio `n_*`. Es el modelo "del mes" (005, 010) |
> | **M1** | **Top 150** columnas por importancia sobre un *pool* de 345 columnas que incluye la historia lag1/delta1/ratio1 de 50 variables, ratios y `n_*`. La selección se hace con las importancias de un modelo entrenado solo con meses de train (004, 005) |
> | **M2** | **Todas las variables con lag1, lag2 y diferencias**: 855 columnas (863 menos 8 con PSI > 0,20 porque su lag2 apunta al aguinaldo). Sin selección. Es el modelo principal del final (028–031) |
> | **Pool** | Conjunto amplio de columnas candidatas del que se elige (319 → 345 columnas, 004) |
> | **MIX6** | Ensemble de 6 modelos: los 3 mejores trials de Optuna de M0 y los 3 de M1, cada uno con sus propios hiperparámetros (005) |
> | **top1 / top2 / top3** | Los 3 mejores trials de Optuna (tras reevaluarlos con semillas nuevas). Sus hiperparámetros están en `005_optuna/mejores_trials.json` |
> | **Binario** | LightGBM que predice P(BAJA+2) vs resto |
> | **Binario "ambas bajas"** | Binario con BAJA+1 **y** BAJA+2 como positivos (026, 034). Lo usan compañeros con Public > 100; con la historia completa pierde frente al multiclase |
> | **Multiclase** | LightGBM con 3 clases (CONTINUA / BAJA+1 / BAJA+2): da P0, P1, P2 por cliente. Mayor mejora individual desde Optuna (010, 013) |
> | **Score condicional** | `P2 / (1 − P1)` = probabilidad de BAJA+2 *dado que no es BAJA+1*. **Sube** (no baja) el score de quien tiene P1 alto: incorpora la señal "propenso a irse" (018; la explicación original estaba al revés y se corrigió) |
> | **P2 + α·P1** | Familia de scores que suma P1 con peso α. Con poco train el α óptimo es alto; con más datos la ventaja se achica (018) |
> | **Auxiliar de BAJA+1** | Modelo binario de BAJA+1 entrenado con 202103–**07** (202107 solo aporta BAJA+1, que se conoce). Su P1 reemplaza al P1 del multiclase en el score condicional (014, 017). No está en M2 |
> | **Receta del profe (REC)** | Hiperparámetros pedidos por la cátedra: `max_bin` 31, `min_data_in_leaf` 0, `feature_fraction` 0,5, `feature_fraction_bynode` 0,2, `learning_rate` 0,005, **sin undersampling**. En el final: multiclase con 512 hojas y 800 rondas (009, 021, 024) |
> | **E1 / E2** | En 030: ensemble de 3 configuraciones con el pool anterior (E1) o con las 855 columnas (E2) |
> | **V0, V1, V2…** | Nombres de variantes **locales de cada experimento** (V0 suele ser la base). No significan lo mismo entre experimentos: mirar el README |
>
> ## 5. Features (variables construidas)
>
> | Término | Qué es |
> |---|---|
> | **Variable original / cruda** | Columna tal como viene del banco (152 numéricas) |
> | **Lag (`v_lag1`, `v_lag2`)** | Valor de la misma variable para el mismo cliente 1 o 2 meses antes. NaN si el cliente no estaba |
> | **Delta (`v_d1`, `v_d2`)** | `v − lag`: cuánto cambió respecto de 1 o 2 meses atrás |
> | **Ratio (`v_r1`, `v_r2`)** | `v / lag − 1`: cambio relativo (normaliza por el tamaño del cliente) |
> | **Historia / variables históricas** | Lags, deltas y ratios. La receta ganadora de los compañeros: lag1, lag2 y diferencias de **todas** las variables (028) |
> | **Variables `n_*` (negocio)** | Sumas, restas y ratios por grupos de negocio definidos a priori (ingresos, egresos, patrimonio, productos activos…; 003d). Varias están entre las más importantes |
> | **Variables `r_*`** | Ratios entre variables del mismo mes (ticket promedio, uso del límite, etc.; 003c) |
> | **Rank del mes** | Reemplazar cada valor por su posición relativa dentro del mes (027): perjudicó, porque el nivel nominal lleva información |
> | **Deflactor** | Dividir los montos por un factor de precios del mes para volverlos comparables (037c) |
> | **Variables de calendario** | `Master_fultimo_cierre` y `Visa_fultimo_cierre`: valen 1, 2, 5, 0, 3, 6 de 202103 a 202108; identifican el mes. Neutras al sacarlas (036) |
> | **`ccajas_depositos`** | Variable "rota" en 202105 (todos ceros). Se pone en NA solo ese mes (008a; flag `CORREGIR_CCAJAS`) |
> | **NaN nativo** | LightGBM maneja los nulos solo: un nulo en `Visa_*` significa "no tiene la tarjeta", no se imputa |
> | **Canarios** | Columnas de ruido (números al azar) que se agregan al entrenamiento. Una variable real que no supera a los canarios en importancia no aporta (004, 037a) |
> | **Importancia (gain)** | Cuánto reduce el error cada variable sumando sus cortes en los árboles |
> | **Top150** | Las 150 columnas más importantes de un fold, calculadas **solo con meses de train** (nunca con el de validación) |
> | **Hojas de Random Forest** | Features que indican en qué hoja de un RF cae cada fila; técnica de la cátedra aún no probada (037f) |
> | **Fuga (leakage)** | Que el modelo "vea" información que en producción no tendría (un mes futuro, la etiqueta del valid). Hay que cuidarla en historia, selección de variables y solapamiento |
>
> ## 6. Entrenamiento e hiperparámetros
>
> | Término | Qué es |
> |---|---|
> | **LightGBM** | Gradient boosting de árboles de decisión. Es el único algoritmo usado |
> | **Ronda / `num_boost_round`** | Cantidad de árboles. Con `learning_rate` bajo hacen falta más |
> | **`learning_rate` (lr)** | Cuánto aporta cada árbol. Menor = más rondas y más regular |
> | **`num_leaves`** | Hojas máximas por árbol (complejidad) |
> | **`min_data_in_leaf`** | Filas mínimas por hoja: regulariza. Con muchas columnas ruidosas, valores 50–80 ayudaron en L/B2 pero fueron neutros en 202107 (032, 033, 036) |
> | **`feature_fraction` / `bynode`** | Fracción de columnas sorteada por árbol / por nodo |
> | **`bagging_fraction`** | Fracción de filas sorteada por ronda |
> | **`lambda_l1`, `lambda_l2`** | Regularización de los pesos de las hojas |
> | **`max_bin`** | Cantidad de intervalos con que se discretiza cada variable |
> | **`min_sum_hessian_in_leaf`** | Peso mínimo (suma de hessianos) por hoja: otro regularizador |
> | **`extra_trees`, `path_smooth`, `min_gain_to_split`** | Opciones de LightGBM probadas en 022 (perjudicaron o fueron neutras) |
> | **Undersampling (r)** | Entrenar con todos los positivos y solo una fracción **r** de los negativos (CONTINUA). Acelera ~5–10× y en nuestras pruebas mejoró la ganancia; infla las probabilidades. En el multiclase se conservan BAJA+1 y BAJA+2 completos |
> | **Optuna** | Biblioteca de optimización bayesiana (algoritmo TPE) de hiperparámetros. Cada **trial** prueba una combinación |
> | **Trial / ancla** | Un intento de Optuna / trials iniciales con hiperparámetros conocidos para chequear el script (012) |
> | **Pruner** | Corta los trials malos antes de terminar |
> | **Reevaluación honesta** | Volver a medir los mejores trials con semillas **distintas** a las de la búsqueda y en un fold que no se usó para buscar (005) |
> | **Borde de la grilla / de rango** | Cuando el mejor valor está en el extremo de lo probado, no se vio el óptimo (009, 021) |
> | **Meseta (plateau)** | Zona donde la métrica casi no cambia: señal de que se llegó al techo de ese espacio (012, 015, 033) |
> | **Búsqueda dirigida** | Variar a mano un hiperparámetro por vez en vez de un Optuna completo (032/033) |
> | **Semilla** | Número que fija el azar de un entrenamiento. Propias: 852583, 771227, 676057, 482687, 399221 (las demás se derivan) |
>
> ## 7. Ensembles y mezclas
>
> | Término | Qué es |
> |---|---|
> | **Ensemble** | Promedio de varios modelos |
> | **Semillero** | Mismo modelo entrenado con muchas semillas y promediado: baja la varianza (004b, 017: 30 semillas por configuración) |
> | **Rank medio** | En vez de promediar probabilidades, se convierte cada score en su posición (rank) y se promedian los ranks. Igual o algo mejor (009b, 013) |
> | **Blend** | Mezcla de rankings de modelos ya entrenados, sin reentrenar. 019 = 017 + 010; 024 = 019 + receta; 031 = 2/3 M2 + 1/3 de 024 |
> | **Diversidad** | Que los modelos se equivoquen distinto: por eso aporta mezclar configuraciones, targets o columnas distintas |
> | **Stacking** | Entrenar un meta-modelo sobre las salidas de otros. No se hizo (riesgo de sobreajuste con dos meses) |
> | **Solapamiento (top-k)** | % de clientes que dos envíos tienen en común. 95–99% = casi el mismo envío; una diferencia del Public entre ellos es ruido |
>
> ## 8. Drift y calidad de datos
>
> | Término | Qué es |
> |---|---|
> | **Drift** | Que los datos del mes a predecir difieran de los de entrenamiento |
> | **Covariate drift / concept drift** | Cambia la distribución de las variables / cambia la **relación** entre variables y target. El segundo es el que el PSI no ve (caso `mprestamos_personales` en 202106) |
> | **PSI** | *Population Stability Index*: compara la proporción de población por bin entre dos períodos: Σ (a − e)·ln(a/e). < 0,1 estable; 0,1–0,25 moderado; > 0,25 importante |
> | **Validación adversarial (C1, 008)** | Entrenar un clasificador que distinga el mes A del mes B sin usar el target. AUC ≈ 0,5 = sin drift; entre meses consecutivos ya da 0,83–0,92 por los montos nominales |
> | **Aguinaldo** | Medio aguinaldo que se paga en junio: infla sueldos y saldos en 202106. Hace atípico ese mes (el fold B y el aumento de payroll) |
> | **Ola de salidas (préstamo y mora)** | Aumento de las bajas de clientes con préstamo personal y saldo negativo o tarjeta en *status 6*: 0,28% → 1,3% mensual hasta 202108 (REPRODUCIR §9). Probablemente cierres por mora |
> | **Status 6** | Valor de `Visa_status`/`Master_status` que pasó de ≈ 100 clientes por mes a 1.429 en 202107 |
> | **Inflación / montos nominales** | Los montos en ARS suben mes a mes; un corte aprendido en marzo no significa lo mismo en agosto |
>
> ## 9. Leaderboard y entrega
>
> | Término | Qué es |
> |---|---|
> | **Public Leaderboard** | Ganancia de un envío sobre ≈ 25% de los clientes de 202108 (muestra fija), sin escalar, en millones. El bot devuelve media y desvío entre los archivos del submit |
> | **Private** | Ganancia sobre el resto (≈ 75%): lo que cuenta para la nota. Empíricamente ≈ **3 × Public** (ratio medio 2,98) |
> | **Línea de Muerte** | Ganancia mínima para obtener un 5; por encima se normaliza a [5, 10]. Aproximadamente 100M de Public (≈ 300 en Private) según el alumno |
> | **Submit / archivo** | Mensaje al bot con 1–20 CSV de `numero_de_cliente` a estimular (8.000–15.000 filas, sin encabezado). El **último submit antes del cierre es el final y debe ser un solo archivo** |
> | **Sobreajuste al Public** | Elegir modelos por el Public: sube artificialmente. Por eso solo se usó para detectar roturas, con reglas fijadas antes |
>
> ## 10. Sesgos y vicios metodológicos que hay que reconocer
>
> | Término | Qué es |
> |---|---|
> | **Sesgo de la versión débil** | Probar una idea en una forma limitada (binario, pocos datos, pocas variables) y darla por muerta. Pasó con 008c, 009, 003c (agregar vs reemplazar) |
> | **Anclaje / path dependence** | Que decisiones tempranas condicionen todo lo posterior (el top150 sobre un pool de 50 variables) |
> | **Sobreajuste a los folds** | Que las decisiones se ajusten a los dos meses de validación |
> | **Confusión de factores** | Cambiar dos cosas a la vez (p. ej. k y modelo) y atribuir el efecto a una |
> | **Sesgo de selección** | Elegir el mejor de muchos intentos y reportar ese número (ver winner's curse) |
>
> ## 11. Cómo leer una tabla de resultados y los nombres
>
> **Una fila típica** (`LOG.md`, `comparacion.csv`): `V2 − V1: +11.7 (ee 2.1), 5/5`
> → la variante V2 gana a V1 por **11,7M** (de ganancia media en un mes completo), el promedio de las diferencias por semilla tiene un error estándar de 2,1M (es decir ≈ 5,6 ee: bien por encima de 2), y gana en las **5 de 5** semillas. Eso se toma en serio. En cambio `−0.4 (1.7), 1/5` es "no hay efecto".
>
> **Nombres de envíos y archivos**
> - `exp017_final_s30_k11000_lag2.csv`: experimento 017, 30 semillas, k = 11.000, con lag2.
> - `exp031_final_w67_md_k12000.csv`: experimento 031, peso 67% de M2, con los `min_data` ajustados (md), k = 12.000. **Es el submit final.**
> - `exp025_k12000_s399221.csv`: medición de la curva de k (025): k = 12.000, semilla 399221.
> - Carpeta `tmp/` de cada experimento: scores por cliente y modelos por semilla (no versionada).
>
> **Documentos**
> - `LOG.md`: bitácora, una fila por experimento (más reciente arriba).
> - `submissions/REGISTRO.md`: cada envío al bot con su Public.
> - `REPRODUCIR.md`: cómo regenerar el final y la evidencia de cada decisión.
> - `COBERTURA.md`: auditoría de lo que proponían las fuentes y plan de lo que falta.
> - `PLAN.md`: el plan original y su estado final.
>
> ## 12. Reproducibilidad
> | Término | Qué es |
> |---|---|
> | **Determinismo** | Que el mismo código, los mismos datos y las mismas semillas den **siempre** el mismo resultado. Se rompe con orden de filas variable, hilos y versiones de librerías |
> | **Orden de filas** | Posición de cada cliente en el DataFrame. Importa porque el undersampling sortea por posición (`rand(n) < r`): otro orden = otra muestra de clientes = otro modelo |
> | **`ORDER BY` explícito** | Fija el orden de salida de DuckDB (sin él, un join paralelo devuelve filas en orden distinto entre corridas). Se agregó el 2026-10-10 (REPRODUCIR §0) |
> | **Huella (hash)** | Resumen corto (md5) de un arreglo para comparar si dos corridas produjeron exactamente lo mismo (`verificar_determinismo.py`) |
> | **`deterministic` / `force_row_wise`** | Opciones de LightGBM que fijan el resultado con cualquier cantidad de hilos |
> | **Semillas derivadas** | Las 25 semillas generadas a partir de la primera propia (`config.SEMILLAS_DERIVADAS`): reproducibles, pero no registradas en el check-in |
> | **`requirements-lock.txt`** | Versiones exactas de las librerías con las que se generó el final |
> | **Manifiesto de modelos** | `competencia/modelos_manifiesto.csv`: huellas SHA-256 de cada modelo y su predicción. Es lo versionable (los modelos pesan decenas de MB cada uno y viven en `artifacts/`, fuera de git) |

### competencia/README.md

> # Competencia (estilo Kaggle)
>
> Espacio de trabajo para las competencias de DMEyF 2026.
> - **Primera Competencia:** cierre **dom 11-oct-2026 23:59:59 (hora Buenos Aires)**. Se predice **202108** (último mes del dataset, sin `clase_ternaria`). La "Línea de Muerte" es privada por ahora.
> - Última Competencia: lanzamiento ~05-oct, cierre mié 09-dic (confirmar).
> **Plan de trabajo y decisiones acordadas: [`PLAN.md`](PLAN.md).** El problema, la función de ganancia y las reglas de integridad están en [`../CLAUDE.md`](../CLAUDE.md).
>
> ## Estructura
> ```
> src/config.py        constantes (ganancia, umbral, meses, semillas propias)
> src/ganancia.py      ganancia por umbral, ganancia acumulada, mejor corte por cantidad de envíos
> src/submit.py        escribe y valida los CSV de submit, arma el cuerpo del mensaje de Zulip
> src/data.py          carga del dataset con DuckDB desde el parquet (sin traer todo a memoria); aplica la corrección de ccajas_depositos
> src/features.py     features del mes (ratios, negocio), agregados de cambios, eventos de productos
> src/historia.py     lags y diferencias (lag1, lagN), lags de features derivadas
> src/validacion.py   folds out-of-time y evaluación; src/multiclase.py funciones del modelo multiclase
> src/drift.py        PSI y validación adversarial; src/seleccion.py selección con canaritos
> experimentos/        NNN_descripcion/ (README.md + scripts/notebook + resultados chicos)
> submissions/         CSV enviados + submissions/REGISTRO.md
> LOG.md               bitácora: qué se probó, métrica local, puntaje público, conclusión
> PLAN.md              plan acordado y estado final (arriba)
> GLOSARIO.md          qué significa cada término (fold, M0/M1/M2, ee, PSI, BH…) y cómo leer las tablas
> COBERTURA.md         auditoría de lo que proponían las fuentes y plan de lo que falta
> REPRODUCIR.md        cómo regenerar el submit final desde el dataset, y evidencia de cada decisión
> ../research/         investigación de estrategias de la literatura/industria (hipótesis, no medidas)
> ```
>
> ## Flujo
> 1. Plantear hipótesis en `experimentos/NNN_nombre/README.md` (copiar `experimentos/_plantilla/`).
> 2. Cambiar UNA cosa respecto del baseline; fijar semillas de `config.py`; medir ganancia sobre **varias semillas** y en un mes out-of-time.
> 3. Anotar en `LOG.md` (también lo que no funcionó).
> 4. Si es candidato a submit: generar el CSV desde el script del experimento (reproducible desde `data/competencia_01_crudo.csv`), guardarlo en `submissions/` y registrarlo en `submissions/REGISTRO.md` con el puntaje público.
> 5. Commit chico por experimento.
>
> ## Formato del submit (entrega por Zulip)
> Se envía un mensaje de Zulip al bot con **cuerpo** y **uno o varios adjuntos .csv**:
> - **Cuerpo:** `submit    NombreInterno` — `submit` en minúsculas; `NombreInterno` es un string sin espacios ni caracteres raros, **distinto en cada submit** (ej. `submit    PredSimpres666`).
> - **Adjuntos:** extensión `.csv`, nombres distintos dentro del mensaje (y conviene que sean distintos a todos los enviados alguna vez). Máx. **20 archivos por submit** y **13 submits por día** al inicio (el bot mostró luego 17 y 23 por día; el contador se renueva a las 21:00 hora argentina).
> - **Contenido de cada CSV:** solo los `numero_de_cliente` a los que se enviaría estímulo (**entre 8000 y 15000 registros**), **sin encabezado**, uno por línea, como **enteros** (nunca notación científica: 48000000 → `4.8e+07` rompe el submit; también cuidado con 31100000).
> - **Respuesta del bot:** *Public Gain mean* (ganancia promedio de cada archivo en el Public Leaderboard, ≈25% de los datos, **sin escalar**, en millones de ARS) y *Public gain std dev*. Para estimar la ganancia total, comparar con una ganancia local escalada (÷0.25 aprox.).
>
> Usar `src/submit.py`: `guardar_submit(ids, nombre)` valida cantidad, enteros, unicidad y nombre, y escribe sin encabezado; `top_k_ids(ids, proba, k)` elige los k mejores; `cuerpo_mensaje(nombre)` arma el cuerpo. Mandar varios archivos (ej. distintas semillas o cantidades de envíos) en un mismo submit permite ver la media y el desvío de la ganancia pública. **El último submit antes del cierre es el final: debe ser un solo archivo** (un envío de varios archivos deja de ser "el final" válido hasta que se reenvíe uno solo).
>
> ## Reglas a recordar
> - Respetar las restricciones de algoritmos/datos del enunciado de cada competencia.
> - La solución final debe ser original, reproducible (semillas incluidas) y comprensible por el alumno: hay examen individual sobre la Última Competencia, sin LLMs.
> - Nunca entrenar ni evaluar con meses cuya `clase_ternaria` es NULL.

### competencia/LOG.md

> # Bitácora de experimentos
>
> Una fila por experimento (más reciente arriba). Ganancia en ARS; indicar mes(es) de train/validación, semillas usadas y cuántas.
>
> | # | Fecha | Experimento | Cambio vs baseline | Train → Valid | Ganancia local (media ± desvío) | Puntaje público | Conclusión |
> |---|---|---|---|---|---|---|---|
> | 038-rep2 | 2026-10-10 | Verificación A/B del código corregido | M2 top1–3, semilla 852583, desde cero en dos copias independientes | datos oficiales | modelos y predicciones IDÉNTICOS bit a bit (huellas SHA-256); contra el modelo original: 91% del top-12000 alineado por cliente | — | El pipeline es determinista de punta a punta; el submit enviado sigue sin ser regenerable idéntico. Agregados: guardado de modelos + manifiesto, `preparar_datos.py`, guarda del orden de cache |
> | 038-rep | 2026-10-10 | Auditoría de reproducibilidad (clon limpio) | reentrenar M2 top1–3 con semilla 852583 en un clon y comparar con lo guardado | clon de `b8d14da`, datos oficiales | top-12000 coincide 94–95% por modelo (no idéntico); causa: orden de filas no determinista de DuckDB; con `ORDER BY` + `deterministic` el orden y el modelo son estables entre procesos e hilos | — | El submit enviado NO es regenerable bit a bit; código corregido (config.py, data.py, historia.py, validacion.py); REPRODUCIR.md §0. Pendiente: decidir si se regenera y reenvía el final |
> | 037f | 2026-10-09 | [Hojas de Random Forest](experimentos/037_hojas_rf/README.md) | RF con 202103–04 → índices de hoja como features; LightGBM con 202105–06; categóricas (plan) y numéricas (posterior) | proxy 202107, 8 semillas pareadas | categóricas −46.5 (ee 1.5)M, 0/8; numéricas −12.1 (1.3)M, 0/8 | — | No pasa (BH m=9: 0 de 9 variantes pasan). Parte del desastre es codificación; el signo es negativo en ambas |
> | 037e | 2026-10-09 | [Diversidad M0 sobre columnas de M2](experimentos/037_huecos_de/README.md) | ensemble 3 configs M1 vs 6 (M1 + M0), 855 columnas | proxy 202107, 8 semillas pareadas | +0.6 (ee 0.5)M, 4/8, p=0.16 | — | No pasa: ensemble saturado |
> | 037d | 2026-10-09 | [M2 sin undersampling](experimentos/037_huecos_de/README.md) | r = 0.3 y 1.0 vs r = 0.0986 (min_data sin retunear) | proxy 202107, 5 semillas pareadas | r=0.3: +2.9 (2.2)M, 3/5; r=1.0: +1.8 (2.9)M, 3/5 | — | No pasa; r=1.0 muy variable. El undersampling no pierde y cuesta 10× menos |
> | 037c | 2026-10-09 | [Deflactar montos](experimentos/037_huecos_abc/README.md) | factor mensual de montos (mediana entre variables) | proxy 202107, 8 semillas pareadas | −1.4 (ee 0.7)M, 2/8 | — | No pasa. Factor mezcla inflación y aguinaldo |
> | 037b | 2026-10-09 | [Sin 202103](experimentos/037_huecos_abc/README.md) | entrenar con 202104–06 | proxy 202107, 8 semillas pareadas | +1.9 (1.6)M, 5/8, p=0.14 | — | No pasa (neutro) |
> | 037a | 2026-10-09 | [Canarios sobre 855 columnas](experimentos/037_huecos_abc/README.md) | podar por canarios (> máx / > p90) | proxy 202107, 8 semillas pareadas | −122M (22 y 30 columnas), 0/8 | — | No sirve en esta forma: casi todas las columnas reales quedan bajo el mejor canario (coherente con 004) |
> | 036 | 2026-10-09 | [Validación en 202107 (BAJA+1 proxy)](experimentos/036_validacion_202107/README.md) | pool anterior vs 855 columnas, min_data 50, sin calendario, peso 2 en 202106 | train 202103–06 → valid 202107 (BAJA+1); 5 semillas pareadas | V2−V1: +11.7 (ee 2.1)M, 5/5; V1−V0: +8.0 (1.7); min_data50 −0.4 (1.7); sin calendario −1.5 (1.8); peso 202106 −1.1 (1.4) | — | Confirma las 855 columnas en un mes limpio; min_data y calendario neutros; la recencia no ayuda. El final no cambia |
> | 036-rev | 2026-10-09 | Revisión de sesgos (solo análisis, sin modelos) | ola de salidas en préstamo y mora; columnas de calendario en los modelos; auxiliar fuera de M2 | datos 202103–08 | grupo préstamo&mora: salida mensual 0.28 → 0.51 → 1.3%, BAJA+2 0.4 → 1.7% en 202106; final lo trata como promedio (8.2% del top vs 7.5% población) | — | Riesgos documentados en REPRODUCIR.md §9; propuestas: validar en 202107 con BAJA+1 (proxy), sacar columnas de calendario, auxiliar para M2 |
> | 035 | 2026-10-09 | [Tendencias por variable](experimentos/035_tendencias/README.md) | aceleración y cambio relativo a la media de 3 meses (855 → ~1100 columnas) | L y B2; 3 semillas pareadas | +1.05 (ee 1.56) / +2.84 (0.18)M, 5/6 | — | Chico y consistente pero no pasa la regla (> 2 ee en ambos folds). No se adopta |
> | 034 | 2026-10-09 | [Binario ambas bajas con 855 columnas](experimentos/034_binario_todas_lags/README.md) | binario BAJA+1/2 y mezclas con el multiclase M2 | L y B2; 3 semillas pareadas | EB−EM: −4.0 / −9.0M (1/6); M67: +3.2 / +0.9M | — | Con la historia completa el binario pierde, incluso con 1 mes de train. Descartado |
> | 033 | 2026-10-09 | [min_data_in_leaf, extensión](experimentos/032_busqueda_dirigida/README.md) | min_data 80, 120, 200 (M2, 855 columnas) | L y B2; 3 semillas | 80: +4.5 / +3.8M (6/6); 120: −0.2 / −2.0; 200: −11.0 / −11.6 | — | U invertida, meseta 50–80 |
> | 032 | 2026-10-09 | [Búsqueda dirigida M2](experimentos/032_busqueda_dirigida/README.md) | ff, hojas, min_data, rondas sobre M1 top1 con 855 columnas | L y B2; 3 semillas | min_data 50: +6.3 (ee 1.2) / +3.8 (2.2)M, 5/6; el resto ruido | — | Solo min_data_in_leaf mueve algo; final con 50/65/80 |
> | 031 | 2026-10-09 | [Final M2](experimentos/031_final_todas_lags/README.md) | 3 configs M1 × 10 semillas con 855 columnas (todas las variables con lags 1 y 2 y diferencias), 8 excluidas por PSI; min_data 50/65/80; blend 2/3 M2 + 1/3 exp024, k=12000 | train 202103–06 → 202108, un archivo | validado por partes: 028/030 +8.8M en B2, 029 control, 032/033 | **103.21M** (`exp031_final_w67_md`; vs 101.15 exp024) | **FINAL ENTREGADO.** Public +2.06M sobre exp024, acorde a lo esperado (+8.8M locales ≈ +2.2M en escala Public) |
> | 030 | 2026-10-09 | [Ensemble con todas las lags](experimentos/030_ensemble_todas_lags/README.md) | 3 configs M1 con 863 columnas (E2) vs 150+lag2 de 50 (E1); mezcla 50/50 | L y B2; 3 semillas pareadas | E2−E1: +3.6 (ee 0.9) / +8.8 (3.1)M, 6/6; mezcla: +3.9 / +5.9M, 6/6 | — | La ventaja se mantiene en ensemble. M2 es el componente principal del final |
> | 029 | 2026-10-09 | [Control: historia barajada](experimentos/029_control_todas_lags/README.md) | V2 con las columnas históricas barajadas en el train | L y B2; 4 semillas | V2c−V2: −73.4 (5.8) / −31.5 (4.5)M, 0/8 | — | No es un artefacto de calendario/NaN: la historia aporta información real |
> | 028 | 2026-10-09 | [Todas las variables con lags](experimentos/028_todas_lags/README.md) | lag1, lag2 y diferencias de 142 variables sin selección (863 columnas) en multiclase | L y B2 (targets solapados); 4 semillas pareadas | V2−V1: +2.1 (ee 0.4) / +10.5 (2.7)M, 8/8 pares; V2−V0: +23.0 / +13.9M | — | La mayor mejora desde el multiclase; la receta de los compañeros gana. Control (029) y ensemble (030) lo confirman |
> | 027 | 2026-10-09 | [Rank del mes en [−1,1]](experimentos/027_rank_mes/README.md) | reemplazar variables crudas por 2·percentil−1 del mes (todas las continuas / solo montos) | A, B, Bh; 5 semillas pareadas | V1: −3.8 / −19.3 / −18.0M (0/15 pares); V2: −0.8 / −5.9 / −7.1M | — | Perjudica con claridad: el nivel nominal lleva información. Descartado |
> | 026b | 2026-10-09 | [Binario ambas bajas en el Public](experimentos/026_binario_ambas_bajas/README.md) | binario BAJA+1/2 vs multiclase, 6 configs × 6 semillas, train 202103–06, k=12000 | un archivo cada uno | — | mc 99.99 / **b12 101.31** / mix 101.31 | +1.32M del binario: no concluyente (poca potencia), pero no muestra la pérdida del fold B. Descartado como componente (034: con la historia completa el binario pierde) |
> | 026 | 2026-10-09 | [Binario ambas bajas](experimentos/026_binario_ambas_bajas/README.md) | binario BAJA+1+2 vs multiclase (mismas filas, columnas e hiperparámetros); P1+P2; mezcla por rank | A, B, Bh; 5 semillas pareadas | B12: +9.2 / −4.6 / +5.8M; MC_suma: +9.5 / −0.2 / +9.4M; MC+B12: +7.2 / −0.5 / +6.8M | — | Gana con 1 mes de train (A, Bh) y desaparece con 2 meses (B): efecto de pocos datos, igual que 018. No se adopta |
> | 025 | 2026-10-09 | [Curva de k en el Public](submissions/REGISTRO.md) | mismo MIX6 multiclase (1 semilla/config, 5 semillas propias) cortado en k = 11000…13000 (paso 500), 5 submits × 5 archivos | train 202103–06 → 202108 | — | 97.48 / 98.02 / **98.18** / 96.84 / 96.55M (desvío entre semillas 1.7 / 2.5 / 1.9 / 1.3 / 0.8) | Plana con pico en 11.5–12k, cae ≥ 12.5k. Coherente con la curva local (015) y los positivos esperados (018). k=12000 |
> | 024 | 2026-10-09 | [Final con receta](experimentos/024_final_receta/blend_final.py) | rank 50/50 entre blend 019 y 8 modelos de la receta (multiclase sin undersampling), k=12000 | train 202103–06 → 202108, un solo archivo | validado por partes (023: +3.5 / +7.3M en B/Bh con 50/50; −0.9 en A) | **101.15M** (`exp024_final`; vs 101.09 exp019) | Candidato final en su momento (superado por 031). Indistinguible de 019 (±0.06M, ~400 clientes distintos); se mantuvo por la validación (023) según regla fijada antes de enviar |
> | 023 | 2026-10-09 | [Ensemble con la receta](experimentos/023_ensemble_con_receta/README.md) | MIX6 multiclase + modelo de la receta (sin undersampling, 512 hojas, 800 rondas); mezcla 1/7 y 50/50 | A, B, Bh; 3 semillas pareadas | MIX6+REC − MIX6: +0.6 / +1.8 / +3.5M (8/9 pares); 50/50: −0.9 / +3.5 / +7.3M (7/9) | — | La receta suma por diversidad; 50/50 mejor donde hay más datos. Entró al final (1/3 vía exp024) |
> | 022 | 2026-10-08 | [Opciones de LightGBM](experimentos/022_opciones_lgbm/README.md) | extra_trees, path_smooth (5, 20), min_gain_to_split 0.5, extra_trees+path_smooth (multiclase M1 top1) | A, B, Bh; 4 semillas pareadas | extra_trees −2.1 / −8.5 / −4.8M; min_gain −6.5 en B; path_smooth ±1M (ruido); 2–6 de 12 pares positivos | — | Ninguna ayuda; extra_trees y min_gain perjudican. Descartado |
> | 021 | 2026-10-08 | [Receta del profe en multiclase](experimentos/021_receta_multiclase/README.md) | receta (lr 0.005, min_data 0, ff 0.5/bynode 0.2) en multiclase, 128/256/512 hojas × hessian, 100–800 rondas, con y sin undersampling | A, B, Bh; 2 semillas | mejor sin undersampling (512 hojas, 800 rondas): +4.1 / +0.1 / +6.0M vs Optuna (media +3.4); con undersampling −1.4 | — | En multiclase la receta no pierde sin undersampling (corrige el −12M de 009, binario con grilla truncada). Óptimo en el borde de la grilla; candidato a miembro del ensemble |
> | 020 | 2026-10-08 | [Pesos por mes recientes](experimentos/020_pesos_recientes/README.md) | peso ×2 y ×3 al mes reciente (multiclase M1 top1) | B y B2; 6 semillas pareadas | P12−P11: −2.70 (ee 0.84) / −2.64 (2.10)M; P13−P11: −2.34 (1.34) / −3.87 (1.44)M; 2/12 pares positivos | — | Perjudica. Con 014 (mes viejo ×2: −3.7M) los pesos iguales son lo mejor. Descartado |
> | 019 | 2026-10-08 | [Blend 017+010](experimentos/019_blend/blend.py) | promedio por rank de 017 (lag2+auxiliar) y 010 (sin ambos), k=12000 | train 202103–06 → 202108, un solo archivo | sin validación propia (cobertura de riesgo de lag2) | **101.09M** (`exp019_blend`; vs 99.14 exp017, 99.99 exp010) | Sobre la línea de ~100M; dentro del ruido y confundido con el cambio de k (11000 → 12000). Vigente en su momento (superado por 024 y luego 031) |
> | 018 | 2026-10-08 | [Score, positivos y rondas](experimentos/018_score_y_rondas/README.md) | familia de scores con el mismo multiclase; estimación de positivos en 202108; rondas vs train | A, B, Bh; 5 semillas | P2+0.5·P1 vs P2/(1−P1): +7.5 / +1.7 / +7.5M; α óptimo baja con más datos; rondas ya en el óptimo; ~1.150–1.200 positivos esperados en 202108 | — | Se mantiene P2/(1−P1) (con 4 meses de train la ventaja esperada ≤ ~1.7M). k=12000 |
> | 017 | 2026-10-08 | [Modelo final](experimentos/017_final/final.py) | MIX6 multiclase + auxiliar BAJA+1 (202103–07) + lag2 en M1 + rank + ccajas corregida, 30 semillas/config, k=11000 | train 202103–06 → 202108, un solo archivo | validado por partes: 013 +5.5 a +9.3M, 014 +0.9 a +1.5M, 016 +5.4M (B2), 015 meseta de k 10–12k | **99.14M** (`exp017_final`; vs 99.99M exp010 con 6 semillas, 98.02 ± 2.5M con 1 semilla) | Candidato final en su momento (superado por 019, 024 y 031). Public dentro del ruido (±1–2.5M): no se elige por él |
> | 016 | 2026-10-08 | [Multiclase + lag2](experimentos/016_multiclase_lag2/README.md) | +150 cols de lag2/delta2/ratio2 en las 3 configs M1 multiclase | L y B2 (targets solapados en 202107); 5 semillas pareadas | V1−V0: +18.9 (ee 3.7) / +5.4 (2.3)M, 9/10 pares; control barajado −3.4 / −19.7M | — | En multiclase el lag2 sí suma (en el binario no era consistente). Entra a las M1 del final |
> | 015 | 2026-10-08 | [Curva de k](experimentos/015_curva_k/README.md) | ganancia vs k (6000–16000) del ensemble multiclase | A, B, Bh; 3 semillas | pico por fold: A 7.5k (870 positivos), B 12.5k, Bh 13k (1098); media de folds plana 10–12k (352.7–354.5M) | — | k óptimo ≈ 9–11× los positivos; se eligió k=11000, movido después a k=12000 (018, 025) |
> | 014 | 2026-10-07 | [Auxiliar BAJA+1 con mes extra](experimentos/014_auxiliar_baja1/README.md) | P(BAJA+1) del score condicional desde un binario dedicado entrenado con un mes más (202105 como 'extra'); control: pesos 2× al mes viejo | B y Bh; 10 semillas pareadas | V1−V0: +0.88 (ee 0.32) / +1.46 (0.45)M, 16/20; sin mes extra (V2) +0.67 / +0.78; peso 2× −3.7M | — | Mejora chica y consistente, casi toda por usar un binario dedicado; el mes extra aporta ~+0.2/+0.7M. Duplicar el mes viejo perjudica. Incluido en el final (017) por decisión del alumno |
> | 013 | 2026-10-07 | [Ensemble multiclase](experimentos/013_ensemble_multiclase/README.md) | MIX6 de 005 pasado a multiclase (score condicional, rank) vs MIX6 binario | A, B, Bh; 5 semillas pareadas con 009b | MC_MIX6 − BIN_MIX6: +9.0 (ee 0.9) / +5.9 (1.0) / +8.8 (0.8)M, 15/15 pares; por rank +8.8 / +5.5 / +9.3; sin M0 pierde 2–3M en A y Bh | — | La ventaja de B1 se confirma en ensemble. Rank ≥ prob; M0 aporta. Pipeline final = MIX6 multiclase por rank |
> | 012 | 2026-10-07 | [Optuna multiclase](experimentos/012_optuna_multiclase/optuna_mc.py) | Optuna propio del multiclase sobre M1 (67 trials, 4 h; anclas = top1-3 del binario) | búsqueda en A y B, 2 semillas | mejor #64 índice 1.0167 vs ancla 1.0120 (+0.005 ≈ +1.5M); casi todos los trials buenos entre 1.00 y 1.017 | — | Meseta: el multiclase hereda bien los hiperparámetros del binario. No se adopta (no llega a +5M); sin reevaluación |
> | 011 | 2026-10-07 | [Features de eventos](experimentos/011_features_eventos/README.md) | V1 agregados de cambios, V2 lags de 20 derivadas, V3 eventos de productos, V4 comisiones normalizadas (cada una por separado sobre la base multiclase B1) | B y Bh; 10 semillas pareadas | Δ vs base (B/Bh): V1 +0.0 (1.1) / +2.7 (1.7); V2 −9.0 (1.8) / −4.1 (1.5); V3 −4.5 (1.7) / +0.9 (2.3); V4 −0.3 / −0.2 | — | Ninguna ayuda; V2 perjudica (2/20 pares). Espacio de features saturado con el modelo de entonces (matizado por 028: la veta estaba en usar todas las variables con lags 1 y 2). No entran al final |
> | 010 (B1) | 2026-10-07 | [Multiclase](experimentos/010_multiclase/README.md) | objetivo multiclase (3 clases), score P(BAJA+2)/(1−P(BAJA+1)); mismas filas e hiperparámetros que M1 top1 | A, B, Bh; 5 semillas nuevas | MC_h2 − BIN_005: +7.5 (ee 1.5) / +10.5 (2.1) / +8.3 (2.0)M, 15/15 pares; vs MC_p2 +5M | **99.99M** (`exp010_mc_h2`, MIX6 multiclase por rank, sin lag2; vs 98.97M exp008 / 96.83M exp005) | **Mayor mejora desde Optuna.** Score condicional clave. Validado como ensemble en 013 |
> | 009b | 2026-10-07 | [Receta en el ensemble + rank](experimentos/009b_ensemble_receta/README.md) | MIX6 + 2 modelos receta (r=0.1); promedio por rank vs probabilidad | A, B, Bh; 5 semillas nuevas | MIX6+REC2−MIX6: +0.4 (ee 0.2) / −0.6 (0.7) / +1.9 (0.6)M; rank−prob: +0.1 / +1.1 / +2.3M | — | La receta no suma al MIX6 binario (ensemble saturado; en multiclase sí suma, ver 023). Rank ≥ probabilidad en 3/3 folds, efecto chico: se adopta en el final |
> | 009 | 2026-10-07 | [Receta del profe](experimentos/009_receta_profe/README.md) | lr 0.005, min_data_in_leaf 0, ff 0.5/bynode 0.2; grilla hojas × hessian × rondas; con y sin undersampling | A, B, Bh; 2 semillas | mejor con r=0.1: A 234.8 / B 396.6 / Bh 386.8M vs Optuna 233.4 / 405.3 / 389.8 (−3.4M); sin undersampling −12.3M | — | El undersampling sigue ayudando en binario (+9–16M en B, con grilla truncada: corregido en 021, donde en multiclase la receta sin undersampling no pierde). La receta con r=0.1 queda cerca de Optuna: candidato de diversidad para el ensemble. Óptimo en el borde (128 hojas) |
> | 008c | 2026-10-07 | [Historia sobre 142 variables ± lag2](experimentos/008c_lags_150/README.md) | V1 +92 variables con lag1/d1/r1; V2 + lag2 de las 142 | B, Bh, L, B2; 10 semillas pareadas | V1−V0: −3.6 (ee 5.6) / +0.7 (3.2) / −3.9 (4.8) / −3.5 (4.3)M; V2−V1 (L/B2): +10.8 (3.2) / +5.4 (4.3) | — | Más variables con historia NO ayudan; lag2 sí suma sobre lag1 pero igual con 50 que con 142 variables. Se descarta la expansión; se mantiene pool actual + lag2 de 50 (008b). **Superado por 028**: con multiclase tuneado y lag1+lag2 usar todas las variables sí ayuda (+10.5M en B2) |
> | 008c0 | 2026-10-06 | [Submit de control](experimentos/008_control_submit/final.py) | MIX6 de 005 con ccajas NA + lag2 en M1 (6 semillas/config) | train 202103–06 → 202108, k=11500, 1 archivo | — | **98.97M** (`exp008_lag2_ccajas`; vs 96.83M de exp005_final_s30, misma muestra) | +2.1M: dentro del ruido (±3M) pero positivo; top-11500 solapa 96.2% con exp005. Pipeline de lag2 sobre 202108 validado |
> | 008b | 2026-10-06 | [lag2/delta2/ratio2](experimentos/008b_lag2/README.md) | +150 cols (lag2 de las 50 vars) sobre el pool 003 | L (202105→202106) y B2 (202104+05→202106), 20 semillas; targets solapados en 202107 | V1−V0: L +10.8 (ee 3.3) / B2 −2.4 (3.1)M; vs control barajado +33 / +22M | — | Información real pero aporte sobre lag1 inconsistente; +150 columnas cuestan ruido (control −22/−25M). Candidato débil: pasa a 008c con selección de columnas |
> | 008a | 2026-10-06 | [ccajas_depositos NA en 202105](experimentos/008a_ccajas_na/README.md) | columna rota (todo 0) → NA solo en 202105 | A, L, B2; 20 semillas; set M0 | A 0.0 (exacto: sin NaN en train) / L −0.9 (2.6) / B2 +3.0 (2.2)M | — | Sin efecto medible; se aplica por corrección de datos (`config.CORREGIR_CCAJAS=True` desde 008c) |
> | 008-C1 | 2026-10-06 | [Adversarial validation](experimentos/008_c1_adversarial/README.md) | 202108 vs meses de train, sin target | pares de meses consecutivos y 202103–06 vs 202108 | AUC 0.83–0.92 entre meses consecutivos; 202108 vs train 0.92 | — | Sin drift extraordinario; destaca `mcomisiones_mantenimiento` (salto nominal) |
> | 005c | 2026-10-06 | k por probabilidades corregidas | corregir el efecto del undersampling y cortar en p≥0.025 | A, B, Bh; MIX6 3 semillas | k estimado ≈ 6.000 vs óptimo real 8.564 / 13.184 / 10.778; pierde 13–89M vs k=11.500 | — | Descartado: probabilidades no calibradas (positivos esperados 25–35% por debajo de los reales). Se mantiene k≈11.500 |
> | 005b | 2026-10-06 | Optuna ronda 2 (rangos corridos) | lr 0.003–0.03, rondas hasta 1800, max_bin | A y B, 2 semillas de búsqueda | M0 1.0833 (=1.0830), M1 1.0970 (vs 1.0934) | — | Sin mejora relevante: el ajuste de hiperparámetros está saturado. Se mantiene la ronda 1 |
> | 005 | 2026-10-06 | [Optuna](experimentos/005_optuna/README.md) | LGBM tuneado (+r de undersampling), 241 trials por set (M0 originales+negocio, M1 top150 historia) | búsqueda en A y B; reeval 10 semillas nuevas en A, B, Bh | MIX6: A 233.9 / B 398.4 / Bh 387.0M (baseline r=1: 213.7/356.6/347.5); tuning vs r=0.2: +9 a +28M | 96.7M ± 2.8M (submit `exp005_mix6`) | Mejor mejora del proyecto. M1>M0 en B/Bh (+14/+19). MIX6 ≈ M1 top1 (cobertura). lr y rondas topan con el borde del rango |
> | 007 | 2026-10-05 | [Undersampling](experimentos/007_undersampling/README.md) | train: todos los BAJA+2 + fracción r del resto (0.5/0.2/0.1/0.05) | A, B, Bh; sets M0 y M1; 20 semillas | r=0.2: M0 +5.1/+8.9/+9.1M, M1 +6.3/+15.1/+6.8M (ee 2–3) | — | Mejora la ganancia y entrena ~5× menos filas. r=0.1 también; 0.05 se degrada. r entra a Optuna como hiperparámetro |
> | 004b | 2026-10-04 | [Mezcla M0+M1](experimentos/004b_mezcla/README.md) | promedio de prob. de originales y top150 historia | A, B, Bh, 20 semillas + control 10 modelos | 1 modelo/semilla: MIX−M0 +6/+14/+21M, MIX−M1 +6/+7/+6M. Con 10 modelos: MIX−M1x10 +4.1/+0.5/−1.1M | 94.0M ± 1.9M (submit `exp004b_mix`, 10+10 semillas) | La ganancia de la mezcla es sobre todo promediar más modelos; más semillas (5→10) suman 0–8M → final con 20–30 semillas. Mezcla = cobertura barata (pierde ≤2.5M vs el mejor) |
> | 004 | 2026-10-04 | [Selección con canaritos](experimentos/004_seleccion_variables/README.md) | pool 319 cols → subsets por fold (solo train) | A, B, Bh, 20 semillas | vs pool completo: canario −37/−61/−93M; top80 −6/−13/−22M; **top150 −1.9/+1.6/+0.9M (= full), 2.4× más rápido** | — | Regla canarito estricta descartada; se usan top150 (`variables_final_top150.txt`). Pool vs V0: +1.4/+4.8/+17.6M | Public 90.7M ± 1.5M (`exp004_top150`): −3.5M vs baseline, ver diagnóstico |
> | 003d | 2026-10-05 | [Features de negocio](experimentos/003d_features_negocio/README.md) | +26 sumas/restas/ratios por grupos de negocio (`n_*`) | A, B, Bh, 20 semillas | N1−N0: +3.5 (ee 2.4) / +2.5 (3.1) / +4.6 (2.1)M | — | Positivo en 3/3 folds pero débil; entra como candidata al set final |
> | 003c | 2026-10-04 | [Features del mes](experimentos/003c_features_mes/README.md) | C1 17 ratios entre variables; C2 percentiles en el mes (50 vars); C3 ambas | A y B, 20 semillas | Δ vs base (A/B): C1 +0.4/+3.6M; C2 +0.3/−4.6M; C3 +0.3/−4.9M (ee 2.4–3.3) | — | Nada significativo. Percentiles descartados; ratios = candidatos débiles que pasan al pool de 004 |
> | 003b | 2026-10-03 | [Ratios vs lag1](experimentos/003b_ratios/README.md) | +50 cols `v/lag1-1` sobre 003a | B y Bh, 20 semillas | H2−base: B +5.7M (ee 2.8), Bh +12.5M (ee 2.2); H2−H1: B +1.2, Bh +6.8 | — | Positivo pero solo marginalmente significativo (Bh). Lag2/medias móviles/tendencia no son validables con los meses disponibles → 003c reemplazado |
> | 003a | 2026-10-03 | [Lag1 + delta1](experimentos/003a_lag1_delta/README.md) | +100 features históricas (50 vars) | A, B (NaN nativo) y Bh (solo filas con historia), 20 semillas | Δ vs baseline: B +4.5M (ee 3.4), Bh +5.7M (ee 2.4); control barajado −25M | 93.1M ± 2.4M (submit `exp003a_lag1`) | Efecto local chico y positivo, sin señal de proxy de calendario; AUC igual. Public −1.1M vs baseline = ruido; pipeline OK sobre 202108 |
> | 002 | 2026-10-03 | [EDA de variables](experimentos/002_eda_variables/README.md) | transformaciones de fechas/calendario/artefacto Visa (V1–V5) | folds A (→202105) y B (→202106), 20 semillas | Δ vs baseline: −4 a +2M (ruido) | — | Ninguna ayuda; se mantienen variables crudas. Baseline 20 semillas: A 220.6M, B 361.8M. 202108 sin drift fuerte; 202106 atípico (aguinaldo) |
> | 001 | 2026-10-03 | [Baseline LightGBM](experimentos/001_baseline_lgbm/README.md) | LGBM fijo, sin FE ni Optuna; corte top-k | 202103-04 → 202106 (5 semillas) | k=11000: 354.4M ± 9.0M (AUC 0.894) | 94.2M ± 2.4M (8 archivos; submit `exp001_baseline`) | Piso de referencia; k plano en 10-14k. Public ≈ 94.2M, algo sobre lo esperado (85-90M) |

### competencia/REPRODUCIR.md

> # Cómo regenerar el submit final de la Primera Competencia
>
>
> **Submit final entregado: `competencia/submissions/exp031_final_w67_md_k12000.csv`** (un solo archivo, 12.000 clientes, Public 103.21M; Línea de Muerte ≈ 100M en Public, Private ≈ 3 × Public).
> Qué es: ranking que combina, por rank, **2/3 de M2** (multiclase CONTINUA/BAJA+1/BAJA+2 con todas las variables con lag1, lag2 y diferencias, 855 columnas, 3 configuraciones de Optuna × 10 semillas) y **1/3 del blend anterior** `exp024` (a su vez 50/50 entre el blend 017 + 010 y 8 modelos de la receta del profe). Pesos efectivos aproximados: M2 67%, receta 17%, 017 8%, 010 8%.
>
> Todo parte del dataset original (`data/competencia_01.csv`, con `clase_ternaria`, que se construye con `clases/z101_target_sql.ipynb`; fuera de git). Python 3.14, dependencias en `requirements.txt`. Semillas propias en `competencia/src/config.py` (`SEMILLAS = 852583, 771227, 676057, 482687, 399221`; las demás se derivan de la primera con `RandomState(852583)`). Comandos desde la raíz del repo, con `source venv/bin/activate`.
>
>
> ## 1. Datos y entorno
> ```bash
> python3.14 -m venv venv && source venv/bin/activate
> pip install -r requirements-lock.txt                 # versiones exactas (requirements.txt, sin versiones, es para uso general)
> venv/bin/python competencia/preparar_datos.py        # ~3 min: baja el CSV crudo, construye clase_ternaria y genera el parquet en data/
> venv/bin/python competencia/verificar_determinismo.py   # ~1 min: debe imprimir OK en las dos líneas
> ```
> - `preparar_datos.py` reemplaza a los notebooks `z101` y `z701` (mismos pasos: SQL de la celda 27 de z101 y el `to_parquet` de la celda 3 de z701). **Verificado el 2026-10-10:** reconstruye un CSV con las mismas 983.061 filas que el original (0 filas de diferencia en ambos sentidos) y un parquet con las mismas columnas, tipos y contenido.
> - El orden de filas de esos archivos **no importa**: el código ordena siempre por (`foto_mes`, `numero_de_cliente`) al cargar (§0).
> - `config.CORREGIR_CCAJAS = True` pone `ccajas_depositos` en NA solo en 202105 (viene rota: todo 0); todos los scripts del final lo activan solos (el default es False para que 001–007 sigan reproducibles).
> - Requisitos: ~12 GB de disco para los modelos guardados (§0b), ~16 GB de RAM (cada entrenamiento de M2 maneja 654.066 filas × 855 columnas), y un entorno de 10 núcleos para los tiempos de abajo.
>
> **Verificación del §1 y §3 (2026-10-10, clon limpio del commit `6e31c95`, venv nuevo con `requirements-lock.txt`):**
> - §1 ejecutado al pie de la letra: instalación, descarga (el crudo bajado tiene el mismo md5 que el que ya teníamos), `preparar_datos.py` (~2 min; el parquet resultante es idéntico al original) y `verificar_determinismo.py` (OK, con las mismas huellas `a1db22d02f` y `b916c5cf75`).
> - §3.1 a 3.6 ejecutados con tamaño **reducido solo en el clon** (5 rondas por modelo y 1 semilla) para probar la mecánica: los 6 pasos terminan con código 0, se guardan 22 modelos, el manifiesto tiene 22 huellas y `verificar_modelos.py` informa 22 idénticos. **Esto prueba que los pasos corren y se encadenan; no prueba los números de una corrida completa.**
> - Determinismo a tamaño real: demostrado para los 3 modelos de M2 (dos copias independientes, huellas idénticas). Para 017, 010 y 024 comparten cargador, parámetros y semillas, pero no se repitió una corrida completa.
> - Requisito: Python 3.14 instalado en el sistema (el lock se generó con 3.14.2). No se verificó en otro sistema operativo ni arquitectura de CPU.
>
> ## 2. Qué está versionado y qué no
> - **Versionado:** código, hiperparámetros de los 6 trials de Optuna (`005_optuna/mejores_trials.json`, idénticos a los de la base SQLite, verificado), columnas M1 (`005_optuna/sel/top150_*.txt`), lista de 50 variables con historia (`003a_lag1_delta/variables_historia.txt`), lista de 142 variables (`008c_lags_150/variables_150.txt`), columnas excluidas por PSI (`031_final_todas_lags/drop_psi.txt`).
> - **No versionado (se regenera):** `data/`, `artifacts/` (base de Optuna), `tmp/` de cada experimento (scores por cliente, modelos por semilla) y los CSV de `submissions/` (listas de `numero_de_cliente`; el repo es público). El registro de cada envío está en `submissions/REGISTRO.md`.
>
> ## 3. Del dataset al submit final (en este orden)
> Los cuatro modelos son independientes entre sí; el orden de abajo es el de las dependencias de la mezcla (3.5). Tiempos **medidos en una máquina de 10 núcleos** (logs de `017_final`, `024_final_receta`, `031_final_todas_lags`, `010_multiclase`); el guardado de modelos y huellas agrega segundos por modelo.
> ```bash
> # 3.1  017  MIX6 multiclase + auxiliar de BAJA+1 + lag2 en M1; 6 configs × 30 semillas (360 modelos)      ~4 h 25 min
> venv/bin/python competencia/experimentos/017_final/final.py --semillas 30 --k 11000 --lag2
> # 3.2  010  MIX6 multiclase sin auxiliar ni lag2; 6 configs × 6 semillas (36 modelos)                    ~40 min
> venv/bin/python competencia/experimentos/010_multiclase/final.py
> # 3.3  024  receta del profe: multiclase sin undersampling, 512 hojas, 8 semillas (8 modelos)             ~40 min
> venv/bin/python competencia/experimentos/024_final_receta/final_rec.py --semillas 8
> # 3.4  031  M2: todas las variables con lag1, lag2 y diferencias; 3 configs × 10 semillas (30 modelos)   ~50 min
> venv/bin/python competencia/experimentos/031_final_todas_lags/final_m2.py --semillas 10 --min_data 50,65,80
> # 3.5  mezcla por rank: 2/3 M2 + 1/3 (017 + 010 + receta), k=12000                                       segundos
> venv/bin/python competencia/experimentos/031_final_todas_lags/blend_m2.py 0.6667 12000 scores_m2_md50-65-80_202108.csv
> # 3.6  verificación: huellas de los modelos regenerados contra el manifiesto versionado
> venv/bin/python competencia/verificar_modelos.py
> ```
> **Medición de hilos (2026-10-10, M2 top1, 1 semilla, 654.066 filas × 855 columnas):** 91 s con 10 hilos y 115 s con 1 hilo (solo 26% más lento). Como el modelo determinista da lo mismo con cualquier cantidad de hilos, la regeneración **se podría paralelizar por procesos** (varios modelos a la vez con 1 hilo cada uno) con un rendimiento teórico de hasta ~8× sobre el secuencial. **No está implementado ni medido a escala**: cada proceso mantiene ~2–3 GB de datos y la máquina de referencia tiene 17 GB de RAM, lo que limita a ~4 procesos.
> **Tiempo total: ≈ 6 h 35 min de cómputo secuencial** (más ~5 min de preparación de datos). Salida: `competencia/submissions/exp031_final_w67_md_k12000.csv`; si ya existe un archivo con ese nombre y es distinto, el regenerado se guarda como `..._regenerado.csv` (no se pisa el enviado).
> - Cada predicción se guarda por (configuración, semilla) en `tmp/` y los modelos en `artifacts/modelos_final/`; si se corta, al relanzar se retoma. **Para regenerar los modelos hay que correr en un clon limpio o borrar `tmp/`** (si la predicción ya existe, el script no reentrena).
> - Cada script deja los scores que usa la mezcla: 017 → `tmp/scores_202108_conlag2.csv`; 010 → `tmp/proba_202108.csv`; 024 → `tmp/scores_rec_202108.csv`; 031 → `tmp/scores_m2_md50-65-80_202108.csv`.
> - `blend_m2.py` reconstruye en memoria la parte `exp024` a partir de los scores de 017, 010 y la receta; no necesita el CSV de `exp024`.
>
> ## 4. Si se quiere repetir todo desde cero (≈ 15 h de cómputo: 8 h de Optuna + 6,5 h de §3)
> 1. `005_optuna/seleccion.py` → importancias y `sel/top150_*.txt` (selección con el train de cada fold; canaritos solo para excluir ruido).
> 2. `005_optuna/optuna_run.py --horas 8` → base SQLite en `artifacts/optuna/` (no versionada); `reevaluar.py` y `final.py` eligen y guardan `mejores_trials.json`. (Los scripts de validación de 013, 015 y 016 en adelante leen esa base vía `reevaluar.configs()`; los del final leen el JSON.)
> 3. Los cinco pasos del apartado 3.
>
> ## 5. Decisiones del modelo final y su evidencia (con sus límites)
> Validación: todos los folds validan en 202105 (A) o 202106 (B, Bh, L, B2); 202106 es atípico por el aguinaldo. Los "pares positivos" son pares fold-semilla de **dos meses**, y el error estándar mide ruido de entrenamiento, no variación entre meses. L y B2 (los únicos con lag2 real en el train) tienen los targets solapados en 202107. **Escala:** las diferencias locales son de un mes completo; el Public es ~25%, así que hay que dividirlas por ~4 para compararlas (ruido por semilla en el Public ≈ 2.5M con 1 semilla/config, ≈ 1M con 6).
>
> | Pieza | Evidencia local (experimento) | Confianza |
> |---|---|---|
> | LightGBM, ganancia por k envíos (no por umbral) | 001, z601; probabilidades no calibradas (005c) | alta |
> | Undersampling de CONTINUA (r≈0.1) en los modelos M0/M1 de Optuna | +5 a +15M en 6/6 combinaciones en binario (007). En multiclase la receta **sin** undersampling no pierde (021): por eso la receta del profe va sin undersampling | media |
> | Optuna (6 trials, M0/M1) | +20 a +40M sobre el baseline (005); ronda 2 sin mejora (005b); Optuna del multiclase con 150 columnas: meseta (012) | media (sobreajuste a 202105/06) |
> | **Multiclase CONTINUA/BAJA+1/BAJA+2 con score P2/(1−P1)** | +5.5 a +9.3M sobre el binario en ensemble, 15/15 pares (010, 013); sumar P1 ayuda con poco train (018) | media-alta; el mecanismo ("propenso a irse") no está demostrado |
> | **Todas las variables con lag1, lag2 y diferencias (M2, 855 columnas)** | +10.5M en B2, 8/8 pares (028); en ensemble +3.6 / +8.8M, 6/6 (030); control con la historia barajada: −31 a −73M (029); **confirmado en un mes limpio (202107, BAJA+1 proxy): +11.7M sobre el pool anterior, 5/5 pares, AUC +0.0025 (036)** | alta (dos meses distintos, uno sin solapamiento de targets) |
> | 8 columnas lag2/d2 excluidas por PSI > 0.20 (`drop_psi.txt`) | el lag2 de 202108 apunta a junio (aguinaldo): `mpayroll_d2` PSI 1.0, etc. Decisión sin mirar el target; su costo no se midió | baja (precaución) |
> | `min_data_in_leaf` 50/65/80 en M2 | meseta 50–80: +4 a +6M en L, +4M en B2 (032, 033); **no se confirma en 202107: −0.4 ± 1.7M (036)**; solo probado en top1 | baja (neutro; no hace daño) |
> | Historia lag1/delta1/ratio1 de 50 variables (M1 y 017) | +4.5 a +12M (003a/b); en binario y con parámetros base, más variables no ayudaban (008c): **superado por 028** | media |
> | lag2 sobre 50 variables en M1 (017) | multiclase +18.9 (L) / +5.4M (B2) (016); binario inconsistente (008b) | baja-media |
> | Auxiliar de BAJA+1 con 202107 (017) | +0.9 a +1.5M (014), casi todo por usar un binario dedicado | baja (no distinguible de 0 para 202108) |
> | Receta del profe (multiclase sin undersampling, 512 hojas, lr 0.005) como miembro | 021: +3M sobre Optuna en 150 columnas (en el borde de la grilla); 023: +0.6 a +3.5M con peso 1/7, 50/50 −0.9 / +3.5 / +7.3M en A/B/Bh; 3 semillas | baja-media (diversidad) |
> | Promedio por rank en vez de probabilidades | +0.1 a +2.9M (009b, 013) | baja (efecto chico) |
> | Blend 017 + 010 (cobertura del riesgo de lag2/auxiliar) | 019: cambia ~2% de los clientes respecto de cada uno | seguro, sin mejora medida |
> | k = 12000 | meseta 10–12k (015); el pico depende de los positivos del mes (A 870 → 7.5k, B/Bh 1098 → 12–13k); ~1.150–1.200 positivos esperados en 202108 (018); curva en el Public 97.5 / 98.0 / **98.2** / 96.8 / 96.6M para k = 11.0k…13.0k (025) | media |
> | Peso 2/3 M2 + 1/3 blend anterior | **juicio**, no validado: 030 mostró M2 +8.8M sobre el pool anterior en B2 y la mezcla 50/50 +5.9M; el resto aporta diversidad y cobertura | baja |
>
> ## 6. Descartado con evidencia (para el video a Michelina)
> Plan de cierre de huecos 037 (COBERTURA.md, 0 de 9 variantes pasan BH): canarios sobre las 855 columnas (−122M), quitar 202103 (+1.9 ± 1.6M), deflactar montos (−1.4 ± 0.7M), M2 sin undersampling (+1.8 ± 2.9M), configuraciones M0 sobre las mismas columnas (+0.6 ± 0.5M), hojas de Random Forest (−12 a −47M).
> Fechas y calendario (002), percentiles del mes agregados (003c), regla canarito estricta (004), k por probabilidades calibradas (005c), más variables con lag1 en binario (008c; el patrón con todas las variables y multiclase sí funciona, 028), lags de features derivadas, eventos de productos, agregados y comisiones normalizadas (011), receta del profe en **binario** con grilla truncada (009; corregido en 021), pesos por mes (014: −3.7M al mes viejo; 020: −2.5M al reciente), `extra_trees`, `path_smooth`, `min_gain_to_split` (022), binario con ambas bajas sobre las 855 columnas (034: −4 a −9M), rank del mes en [−1, 1] (027: −4 a −19M), tendencias por variable (035: +1 a +3M, no pasa la regla de > 2 ee en ambos folds), Optuna completo sobre M2 (no hay fold independiente para certificarlo; búsqueda dirigida en 032/033).
>
> ## 7. Public de referencia (25% de 202108)
> 94.2 (001) → 96.8 (005, 30 semillas) → 98.97 (008) → 99.99 (010, 6 semillas; 98.0 ± 2.5 con 1 semilla) → 99.14 (017) → 101.09 (019) → 101.15 (024) → **103.21 (031, final)**. Registro completo en `submissions/REGISTRO.md` y `LOG.md`. Los envíos de varios archivos fueron mediciones (ruido por semilla, curva de k), no candidatos.
>
> ## 8. Cautelas honestas
> - Dos meses de validación (202105 y 202106) y tres envíos de ajuste fino sobre ellos: cada decisión nueva suma riesgo de sobreajuste a esos meses.
> - Con ratio Private/Public ≈ 3, 103.2 equivale a ~309 en Private, un ~3% sobre el corte de ~300; el margen es del orden del ruido.
> - Cada pieza agregada después del multiclase y de M2 aporta ≈ 1M o menos; la mayor parte de la ganancia está en tres decisiones: multiclase con score condicional, todas las variables con lags 1 y 2, y no tirar información de la historia.
>
> ## 9. Riesgos conocidos NO resueltos (revisión del 2026-10-09)
> 1. **Ola de salidas en clientes con préstamo y mora** (concept drift que el PSI no ve; la cátedra lo avisa en z701 para `mprestamos_personales`). En el grupo "préstamo personal y (tarjeta con status 6 o saldo total negativo)" (≈12.400 clientes, 7.5% de la población en 202108) la tasa de salida por mes de ausencia fue 0.22 → 0.29 → 0.28 → 0.51 → **1.3%** (ausentes en 202104 … 202108); su BAJA+2 pasó de 0.35–0.45% (202103–05) a **1.7%** en 202106 (17% de los positivos de ese mes con 7% de la población). Los que se van tienen saldo de cuenta corriente muy negativo, rentabilidad negativa y tarjetas en status 6 o faltantes: parecen cierres por mora, no bajas voluntarias. El final trata al grupo como promedio (8.2% del top-12000 contra 7.5% de la población). Si la ola persiste hasta 202110 el grupo merecería ~2× esa representación; si no, el modelo ya lo sobreestima algo. **No se puede validar** (no hay mes con BAJA+2 posterior a la ola).
> 2. **Columnas de calendario en los modelos** (036: neutras en 202107, −1.5 ± 1.8M al sacarlas; riesgo no corroborado): `Master_fultimo_cierre` y `Visa_fultimo_cierre` identifican el mes (valores 1, 2, 5, 0, 3, 6 de 202103 a 202108; AUC adversarial 1.0), están en M1 top150 y en las 855 columnas de M2, y 202108 trae un valor (6) que no existe en train (el árbol lo trata como el mayor visto, 5 = 202105). El modelo puede atribuir efectos del mes (p. ej. la ola de 202106) al identificador de mes, que no se transfiere. 002 (V4) dio −0.6 / −4.2M al sacarlas en el modelo binario de entonces; no se re-midió con M2. `Visa_mpagado` también está contaminada por el calendario (ceros 87% → 69% cuando el cierre cae tarde).
> 3. **El auxiliar de BAJA+1 con 202107 quedó solo en el 017 (≈ 8% del final)**: M2 (2/3) no lo usa, justo cuando 202107 contiene la ola. 014 midió +0.9 a +1.5M con un mes extra sin ola.
> 4. **Un solo mes de validación con evento** (202106: aguinaldo + ola) para casi todas las decisiones, y L/B2 con targets solapados. → Parcialmente resuelto: 036 validó en 202107 con BAJA+1 como proxy (mes limpio, sin solapamiento): las 855 columnas se confirman (+11.7M, 5/5); min_data, calendario y recencia no aportan. Sigue sin poder validarse el auxiliar de BAJA+1 en M2 ni la persistencia de la ola.
> 5. Calidad de datos (chequeo del 2026-10-09): sin duplicados (cliente, mes); salvo `ccajas_depositos` (corregida), las únicas variables con saltos de > 15 puntos en % de nulos o ceros son las de calendario (`*_fultimo_cierre`, `Visa_mpagado`).

### competencia/PLAN.md

> # Plan de la Primera Competencia (acordado con el alumno, 2026-10-03)
>
> **Deadline:** dom 11-oct-2026 23:59:59 (hora Buenos Aires). Se predice **202108**.
> > **ESTADO FINAL (2026-10-09): submit entregado = `exp031_final_w67_md_k12000.csv`, un solo archivo, Public 103.21M** (Línea de Muerte ≈ 100M en Public; Private ≈ 3 × Public). Es el rank 2/3 de M2 (multiclase CONTINUA/BAJA+1/BAJA+2 con todas las variables con lag1, lag2 y diferencias, 855 columnas, 3 configs × 10 semillas) + 1/3 del blend anterior (017 + 010 + receta del profe), k=12000. Receta para regenerarlo: [`REPRODUCIR.md`](REPRODUCIR.md). Evidencia y descartes: [`LOG.md`](LOG.md) y [`submissions/REGISTRO.md`](submissions/REGISTRO.md).
> > **Plan de cierre de huecos (auditoría + reglas de decisión fijadas de antemano): [`COBERTURA.md`](COBERTURA.md) §7–12.**
> > Este documento conserva el plan original (2026-10-03) y su evolución como historia: las secciones de abajo se escribieron antes de los resultados que se indican; donde algo cambió, está marcado con ✅/→.
> Leer también: `LOG.md` (resultados), `README.md` (formato de submit), `../CLAUDE.md` (contexto y reglas).
>
> ## Decisiones tomadas (no re-discutir sin evidencia nueva)
> - **Datos:** usar el parquet (`data/competencia_01.parquet.gzip`, ya generado; `src/data.py` lo usa solo). Solo hay meses 202103–202108; con target completo hasta 202106 (202107: solo BAJA+1, 202108: sin target).
> - **Más meses de train / walk-forward largo:** se saltea en esta competencia (no hay más meses); queda para la Última Competencia, donde también habrá que considerar inflación en los montos.
> - **Optuna (LightGBM) y variables históricas:** obligatorios.
> - **Selección de variables:** sí, descartar las que no aportan para bajar el costo computacional (ver 004).
> - **Drift / variables de fecha:** primero **EDA para entender qué significan** (no tirar ni transformar a ciegas). Ajuste por inflación: no ahora.
> - **Clase BAJA+1+2 (006) y undersampling (007):** baja prioridad, pruebas al final, el alumno desconfía de ambas. → ✅ 007 hecho (ayuda, r≈0.1); 006 se probó recién en 026/034: como binario no mejora al multiclase con la historia completa; lo que entró fue el **multiclase** (010/013).
> - **Validación:** siempre out-of-time, 5 semillas propias (`src/config.py`), corte por cantidad de envíos (top-k, k en 8000–15000). Entrenamiento final con todos los meses con target (202103–202106).
>
> ## Esquema de validación para comparar experimentos
> Dos folds out-of-time (el target de un mes mira 2 meses adelante, por eso hay un mes de separación):
> - **Fold A:** train 202103 → valid 202105.  **Fold B:** train 202103+202104 → valid 202106 (el del baseline).
> - Métrica: ganancia con el top-k óptimo sobre una grilla (reportar también k fijo ~11000), media ± desvío entre 5 semillas, en ambos folds.
> - **Semillas: usar 20 (las 5 propias + 15 derivadas, ver `002_eda_variables/run_potencia.py`) para decidir.** Con 5 el ruido de la media es de ±4–8M (en 002 un +13M con 5 semillas era −0.4M con 20). Comparar de a pares (misma semilla) y aceptar un cambio solo si mejora ambos folds por más que ~2 errores estándar de la diferencia. Referencia del baseline (k=11000, 20 semillas): **A 220.6M, B 361.8M**. Nota: el fold B (valid 202106) está inflado por el aguinaldo; no comparar niveles absolutos entre folds.
> - Herramientas: `src/validacion.py` (`evaluar`, `resumen`), `src/features.py`, `src/drift.py`.
> - Cada experimento: cambiar UNA cosa, carpeta `experimentos/NNN_nombre/` con README y script reproducible (copiar el patrón de `001_baseline_lgbm/run.py`), y fila en `LOG.md`.
> - No elegir por el Public LB (≈25% de 202108, ruidoso): usarlo como control de cordura.
>
> ## Fases y experimentos (orden recomendado)
> | # | Experimento | Objetivo / método | Fecha objetivo |
> |---|---|---|---|
> | 002 | ✅ **HECHO** — ver `experimentos/002_eda_variables/README.md`. Resultado: ninguna transformación de fechas/calendario mejora la ganancia (con 20 semillas); 202108 sin drift fuerte; se mantienen variables crudas. **EDA de variables** (sin modelar) | Entender el significado de cada familia en `docs/diccionario_datos.csv`. Foco: variables de fecha en días (`*_Finiciomora`, `*_Fvencimiento`, `*_fultimo_cierre`, `*_fechaalta`, `cliente_antiguedad`). Hallazgo inicial: `Master_Finiciomora` (99.5% nulo) crece ~30 días por mes (máx 169→207→230→260→291→300) porque es *tiempo transcurrido*: un corte tipo "> 200" solo existe en meses futuros → drift mecánico. `Visa_Finiciomora` en 202105 y 202108 tiene 2.6% de no-nulos con media ~9 días (vs 0.6% y ~45 en el resto): 202108 se parece a 202105 → **hipótesis a verificar**; mirar si 202105 es un buen mes de validación. Probar transformaciones (días → fecha de inicio absoluta, binarias "está en mora", etc.) y medir ΔGanancia en ambos folds. También: PSI de 202108 vs train sin usar target, nulos/ceros por mes. | 03–05 oct |
> | 003 | **Feature engineering histórico** (003a lag1+delta1 HECHO: +4.5/+5.7M débil, ver exp; 003b ratios HECHO (+5.7/+12.5M vs base; marginal sobre 003a +1.2/+6.8); lag2/medias móviles/tendencia NO validables con los meses disponibles (ver 003b/README) → 003c HECHO (features del mes): ratios entre variables +0.4/+3.6M (ruido), percentiles descartados (−2M); el pool de 004 = originales + historia 003b (lag1, delta1, ratio1 de 50 vars) + 17 ratios de 003c; subset = `003a/variables_historia.txt`; el train truncado se trata con el híbrido NaN nativo + fold Bh + control barajado) | Con funciones de ventana en DuckDB (`lag`, `avg over rows between`): lags 1 y 2, delta lag, medias móviles (3 meses), tendencia (pendiente) para variables numéricas relevantes. Ojo: con sólo 202103–202108 un lag de 2 meses deja sin historia a los primeros meses; decidir cómo tratar los nulos de borde y NO usar información del futuro (solo meses ≤ t). Generar a parquet y medir en los 2 folds. | 04–06 oct |
> | 004 | **Selección de variables** (HECHO: regla canarito descartada, top150 = pool completo y 2.4× más rápido → `004/variables_final_top150.txt`) | Sobre el set ampliado (150 → ~500+ columnas). Método sugerido: agregar columnas aleatorias ("canaritos") y descartar las variables cuya importancia (gain, promediada en varias semillas) sea menor a la de los canaritos / cero; decidir la selección **solo con meses de train**, no con el de validación. Verificar que la ganancia no cae y que el tiempo baja. | 06–07 oct |
> | 004b | Mezcla M0+M1 (HECHO, ver exp): la ganancia es sobre todo ensemble size; promediar 20–30 semillas en el final; mezcla = cobertura. | | 
> | 005 | ✅ HECHO (ver `experimentos/005_optuna/README.md`): MIX6 +20 a +40M sobre el baseline en reeval. **Optuna sobre LightGBM** | Sobre el set final de variables. Objetivo = ganancia media en ambos folds (o CV agrupado por cliente dentro del train), no un solo valor. Rangos amplios (`num_leaves`, `learning_rate` en log, `min_data_in_leaf`, `feature_fraction`, `bagging_fraction`, `lambda_l1/l2`, rondas), storage SQLite en `artifacts/optuna/` para reanudar. Reevaluar los mejores 3–5 trials con semillas distintas a las de la búsqueda antes de elegir (z203: riesgo de sobreoptimizar). Pensar en correr de noche. | 07–09 oct |
> | 006 | ✅ HECHO (026, 034) — Clase BAJA+1+2 (baja prioridad) | Binario con ambas bajas: gana con 1 mes de train pero pierde con 2 meses o con las 855 columnas (026: +9.2 / −4.6 / +5.8M en A/B/Bh; 034: −4 a −9M); en el Public (k=12000, 4 meses) +1.3M sobre el multiclase, no concluyente. El multiclase con score P2/(1−P1) lo reemplaza. | 09–10 oct |
> | 007 | ✅ HECHO (adelantado): r=0.2 mejora +5 a +15M en 6/6 combinaciones; r va como hiperparámetro de Optuna (0.05–0.5). Undersampling de CONTINUA (baja prioridad) | Prueba rápida: ¿mantiene la ganancia? Si sí, puede acelerar Optuna; si no, descartar. Si Optuna resulta muy lento, adelantarlo. | 09–10 oct |
> | 008 | ✅ HECHO — **Modelo final y submit** | Final = `exp031_final_w67_md` (017 → 019 → 024 → 031). k=12000 (015, 018, 025). Un solo archivo. Ver `REPRODUCIR.md`. | entregado 09-oct |
>
> ## Estrategia de submits
> - Máx. 13 submits/día al inicio (el bot llegó a mostrar 17 y 23 por día; se renueva a las 21:00 ART) y hasta 20 archivos por submit. El bot devuelve solo media y desvío entre los archivos.
> - **El último submit antes del cierre es el final.** Antes del cierre, el último envío debe ser el modelo elegido. **Confirmar en Zulip cómo se puntúa el submit final si trae varios archivos** (¿el mejor, el promedio, el primero?); hasta saberlo, el submit final debería llevar **un solo archivo**. → Resuelto en la práctica: el final es un solo archivo; los envíos de varios archivos fueron solo mediciones (ruido por semilla, curva de k).
> - Usar el Public LB (baseline = 94.2M) para detectar desastres (ej. un error de formato o drift enorme), no para elegir entre diferencias chicas. **Escala:** el Public es ~25% del mes; las diferencias de ganancia locales (mes completo) hay que dividirlas por ~4 para compararlas con el Public. Ruido por semilla ≈ 2.5M con 1 semilla por configuración, ≈ 1M con 6.
> - Antes de cada submit: registrar en `submissions/REGISTRO.md`.
>
> ## Riesgos a vigilar
> 1. Leakage temporal en las variables históricas (usar solo meses ≤ t) y en la selección de variables (no usar el mes de validación).
> 2. Sobreajustar la validación (un fold, un mes) con Optuna y FE: siempre 2 folds y semillas de evaluación distintas de las de la búsqueda.
> 3. Tiempo/cómputo: Optuna con cientos de columnas es lento; seleccionar variables antes.
> 4. Drift en 202108 que no existe en los meses de validación (ver 002).
> 5. Formato del submit (enteros, sin encabezado, 8000–15000 filas): `src/submit.py` ya valida.
> 6. Para el material de la cátedra: mantener el repo reproducible (semillas propias, scripts que parten del dataset original).
>
> ---
>
> ## Actualización 2026-10-07 (noche) — estado y experimentos pendientes
>
> **Estado:** modelo vigente = MIX6 (6 trials de Optuna de 005, M0 y M1) pasado a **multiclase** (CONTINUA/BAJA+1/BAJA+2), score `P(BAJA+2)/(1−P(BAJA+1))`, promedio por rank, `ccajas_depositos`=NA en 202105, r≈0.1 sobre CONTINUA (BAJA+1 y BAJA+2 completos), sin lag2. Public: 99.99M (`exp010_mc_h2`, 6 semillas/config, un archivo), 98.0M ± 2.5M con 1 semilla/config (5 archivos): el ruido por semilla del Public es ~2.5M, no leer diferencias < 3M. Línea de Muerte ≈ 100M (Public). **El submit final tiene que ser UN solo archivo** (el vigente hoy en el bot es el de 5 archivos hasta que se reenvíe uno solo; `exp010_mc_h2_k11500.csv` es el candidato seguro).
> Descartado hoy (ver LOG.md): más variables con historia (008c), lags de derivadas / eventos / agregados / comisiones (011), receta del profe (009/009b: el undersampling sigue ayudando, la receta no suma al ensemble), Optuna propio del multiclase (012: meseta, +0.005 de índice sobre las anclas). Ganó: multiclase con score condicional (+7.5 a +10.5M vs binario, 15/15 pares); rank ≥ probabilidad (+1M).
>
> **En curso:** ✅ 013 hecho — el ensemble multiclase conserva la ventaja: +9.0 / +5.9 / +8.8M sobre el MIX6 binario, 15/15 pares.
>
> ### 014 (✅ HECHO: +0.9 a +1.5M, casi todo por usar un binario dedicado; incluido en 017) — usar 202107: modelo auxiliar de BAJA+1 con un mes más de datos
> **Idea (del alumno + research B2):** de 202107 se conoce BAJA+1 (quién no está en 202108) pero no BAJA+2 (necesita 202109). El término `P(BAJA+1)` del score condicional se puede estimar con 202103–202107, o sea con el mes más cercano a 202108, que hoy queda afuera del entrenamiento.
> **Validación honesta (fold B):** modelo principal multiclase entrena 202103–04 → valida 202106 (como hoy); el auxiliar de BAJA+1 (binario, o 2 clases BAJA+1 vs resto) entrena 202103–05 (202105 hace de "202107": BAJA+1 conocido, BAJA+2 no). Score = `P2_principal / (1 − P1_aux)`. Comparar pareado (10 semillas) contra el multiclase actual (`P2/(1−P1)` del mismo modelo). Réplica con el desfase de Bh si hay tiempo.
> **Cuidados:** (a) las filas de 202105 sin BAJA+2 conocido NO pueden entrar al modelo principal (sus BAJA+2 estarían mal etiquetados como CONTINUA); solo entran al auxiliar de BAJA+1, y ahí el "resto" incluye ~0.6% de BAJA+2 que se confunde con no-baja (efecto menor, verificar); (b) sin leakage: el auxiliar no ve el target del mes de validación; (c) para el final: auxiliar entrena 202103–07 y principal 202103–06.
> **Control incluido en el mismo experimento:** pesos 2× a los meses viejos (202103–04) = "copiar los dos primeros meses" (idea del alumno); se espera ≈ 0, es el control de que duplicar no agrega información.
> **Decisión:** entra al final si mejora en B (y Bh) por > ~2 ee pareados.
>
> ### Orden hasta el cierre (dom 11-oct 23:59) — plan del 07-oct, superado por los hechos (ver estado final arriba)
> | Cuándo | Qué |
> |---|---|
> | Hoy/mañana | 013 → 014 → 015/016 (k y lag2) → 018 → 020–035 (receta, opciones LightGBM, todas las variables con lags, min_data). Ver LOG.md. |
> | 9–10-oct | Final = 031 (M2 + blend), k=12000, un solo archivo; registrado en REGISTRO.md. |
> | 10-oct | Submit del candidato final (UN archivo). |
> | 11-oct | Solo colchón: el último submit antes de las 23:59:59 es el que cuenta. Verificar que el último sea un único archivo. |

### competencia/COBERTURA.md

> # Cobertura: qué proponen las fuentes y qué hicimos (auditoría del 2026-10-09)
>
> Matriz armada desde los textos literales de las fuentes para que las omisiones sean visibles. **✅ probado** = hay experimento con medición; **◐ parcial** = se probó una versión limitada (se aclara cuál); **✗ no probado**; **— no aplica / conceptual**.
> Límite: solo cubre lo que las fuentes mencionan. No puede mostrar ideas que ninguna fuente ni yo planteamos.
>
> ## 1. Mensaje del profe (competencia)
> | Ítem | Estado | Dónde / qué falta |
> |---|---|---|
> | 1.1 `ccajas_depositos` = NA en 202105 | ✅ | 008a (sin efecto medible; aplicado por corrección) |
> | 1.3 Feature engineering intra mes (listas en blanco en el mensaje) | ◐ | 003c, 003d, 011 (ratios y negocio entran; agregados/eventos no ayudan) |
> | 1.4 Lags y delta lags de orden 1 **y 2** | ✅ (tarde) | 028–030, 036: leído primero como "50 variables"; la receta con todas las variables llegó recién en 028 |
> | 1.5 Variables hojas de Random Forest | ✅ | **037f**: −46.5M (categóricas) / −12.1M (numéricas), 0/8 pares; diseño sin fuga (RF con 202103–04, LightGBM con 202105–06). Un solo diseño probado |
> | 1.6 Canaritos asesinos | ✅ | 004 (319 columnas) y **037a (855 columnas: −122M, solo 22 columnas superan al canario máximo)**: sin ganancia en esta forma |
> | 1.7 Sin undersampling | ✅ | 007/009 (binario, grilla truncada), 021 (multiclase, 150 columnas: no pierde), **037d (M2 855 columnas: r=1.0 +1.8 ± 2.9M, r=0.3 +2.9 ± 2.2M; sin ganancia detectable)** |
> | 1.7 Métrica AUC, `max_bin`=31, `min_data_in_leaf`=0, ff 0.5, bynode 0.2, lr 0.005 | ✅ | 009, 021 (receta; componente del final) |
> | 2.1 10+ modelos con hiperparámetros distintos, sin undersampling | ✅ | M2: 3 configs × 10 semillas con undersampling; **037e: sumar 3 configs M0 sobre las mismas columnas +0.6 ± 0.5M**; 037d: sin undersampling sin ganancia |
> | 2.2 Promediar probabilidades | ✅ | 009b, 013: el rank rinde igual o algo mejor |
> | 2.3 Cortes 10000, 10500, 11000… | ✅ | 015, 018, 025 |
>
> ## 2. Libro de la cátedra (secciones del temario)
> | Sección | Estado | Dónde / qué falta |
> |---|---|---|
> | 13.2 Drifting de atributos | ✅ | 002, 008-C1 (adversarial), PSI de lag2 (031) |
> | 13.3 Variables "rotas" → NA | ✅ | 008a; barrido de ceros y nulos por mes el 2026-10-09 |
> | 13.4 Nulos (¿imputar o dejar que LightGBM los maneje?) | ◐ | NaN nativo en todo el trabajo; **no se comparó contra imputación** |
> | 13.5 Outliers | ✗ | No tratados ni comparados (los árboles son robustos; no se midió) |
> | 19 Controlando el False Discovery Rate | ✗ | No se aplicó ninguna corrección formal por comparaciones múltiples (decenas de pruebas sobre los mismos folds); solo la regla de > 2 ee |
> | 20.2 Cambiando la clase | ✅ | 026, 034 (binario ambas bajas); multiclase 010/013 |
> | 20.3 Variables manuales | ✅ | 003c, 003d, 011 |
> | 20.4 Transformaciones (lineal, log, normalización) | — | Conceptual: invariantes para árboles. El rank dentro del mes (027) perjudica |
> | 20.5–20.7 Históricas, lags y delta lags, tendencias | ✅ | 003a/b, 008, 016, 028–030, 035, 036 |
> | 20.8 Medias móviles | ◐ | Solo como "cambio relativo a la media de 3 meses" (035); no como columna propia |
> | 20.9 Ajuste por inflación | ✅ | Rank del mes (027: perjudica), comisiones normalizadas (011) y **deflactar por factor mensual (037c: −1.4 ± 0.7M)**; ojo: el factor mezcla inflación y aguinaldo |
> | 20.10 Hojas de un Random Forest | ✅ | Ver 1.5 (037f) |
> | 20.11 Reducción de dimensionalidad para acelerar | ✅ | 004 (top150) y 037a (canarios sobre M2: destruyen el modelo) |
> | 24.1 Mejores períodos para entrenar | ✅ | 020 (pesos), B vs Bh (más meses ayuda), **037b (quitar 202103: +1.9 ± 1.6M, neutro)** |
> | 24.2 Evitar cross validation | ✅ | Folds out-of-time en todo el trabajo |
> | 24.3 Undersampling | ✅ | 007, 009, 021 |
> | 25.2 Valores Shapley | ✗ | No hecho (interpretabilidad; el video a Miranda ya se entregó) |
> | 26 Stacking de modelos | ✗ | No probado (riesgo de sobreajuste con dos meses) |
> | 26.1–26.2 Semilleríos e hibridación | ✅ | 004b, 013, 031 (30 semillas por configuración; mezclas de configuraciones) |
> | 27.2–27.3 Calibración en GB, "otra forma de cortar" | ✅ | 005c (probabilidades no calibradas), corte por cantidad |
> | 28 Clustering con distancia de RF (como features de cohorte) | ✗ | G1 del informe de `research/`: no probado |
>
> ## 3. Comentarios de compañeros con Public > 100
> Positivos = ambas bajas ✅ (026/034); `ccajas` en NA ✅; sin ajuste por inflación (igual que nosotros) ◐; lags 1 y 2 y diferencias de todas las variables ✅ (028); duda sobre `mprestamos_personales` ✅ (análisis del 2026-10-09: la variable es informativa, la relación con el target cambia en 202106); rankings en [−1, 1] ✅ (027, perjudica).
>
> ## 4. Informe `research/` (hipótesis del 05-oct)
> B1 multiclase ✅ (la mayor mejora); C1 adversarial ✅; A3 k calibrado ✅ (falló); D1 forma de promediar ✅; B2 auxiliar BAJA+1 ✅ (+0.9–1.5M, **no está en M2**); A2 `scale_pos_weight` ✗; F1 SHAP ✗; F2 monotone constraints ✗; G1 cohortes ✗; E1 pseudo-labeling — (descartado a priori); H1 null importance ✗.
>
> ## 5. Mis propias propuestas que quedaron sin ejecutar
> Canarios sobre las 855 columnas (propuesto como punto 3 de la revisión de sesgos y **no lanzado por omisión mía**: solo se aprobó el punto 1); auxiliar de BAJA+1 para M2 (no testeable en 202107; sin validación propia); reentrenar M2 sin calendario (036 mostró neutralidad: no corresponde); Optuna completo sobre M2 (sin fold independiente para certificar; lo reemplazó 032/033, y 036 no confirmó el efecto de `min_data`).
>
> ## 6. Resumen de huecos reales, por valor esperado y costo
> | # | Hueco | Costo | Nota |
> |---|---|---|---|
> | 1 | Canarios sobre 855 columnas | ~30 min | Técnica de la cátedra; probablemente empate |
> | 2 | Quitar el mes más viejo (202103) en el régimen de M2 | ~20 min con el proxy 202107 | Barato y no testeado |
> | 3 | Deflactar montos por índice mensual | ~20 min con el proxy | Único pendiente del tema inflación |
> | 4 | M2 con r=1 (sin undersampling) | ~1–2 h | El profe lo pidió explícitamente |
> | 5 | Hojas de Random Forest | ~2–3 h | Única técnica enseñada y no probada; riesgo de fuga |
> | 6 | Configuraciones M0 sobre las columnas de M2 (diversidad) | ~1 h | Mejora esperada chica |
> | 7 | Auxiliar de BAJA+1 en M2 | ~1.5 h | Sin forma de validarlo |
>
> ---
>
> # PLAN DE CIERRE DE HUECOS (fijado antes de correr nada; 2026-10-09)
>
> Las reglas de esta sección se escribieron **antes** de ver ningún resultado de los experimentos nuevos. No se modifican después; si una regla resulta mal planteada, se anota como tal y se informa el resultado igual.
>
> ## 7. Protocolo común (vale para todos los experimentos de este plan)
> | Aspecto | Decisión |
> |---|---|
> | **Validación primaria** | La del 036: train 202103–06, valid 202107, tarea BAJA+1 (sin solapamiento, mes sin aguinaldo, con la ola). Mismo harness (`036_validacion_202107/run.py`): binario, hiperparámetros de M1 top1, undersampling r=0.0986 salvo que el experimento lo cambie, ganancia media sobre k=8000..15000 + AUC |
> | **Semillas** | 8 pareadas (`SEMILLAS_20[2:10]`; las del 036 son 5, así que la variante base se recalcula con las 8). Excepción: B1 (costoso) usa 5 |
> | **Línea base** | V2 del 036: las 855 columnas (M2), `min_data_in_leaf` 27, sin cambios. Todas las variantes se comparan contra esa línea base, pareadas por semilla |
> | **Una sola cosa por variante** | Cada variante cambia un solo factor respecto de la base |
> | **Tamaño mínimo que importa** | Δ ≥ **+3M** en la escala del proxy (≈ +0.5% de la ganancia; en el Public equivaldría a ~+0.75M, que es lo mínimo que justifica el riesgo de reentrenar) |
> | **Significancia (FDR, libro §19)** | Test t pareado unilateral por variante (gl = 7). Se aplica **Benjamini–Hochberg con q = 0.10 sobre todos los tests del lote** (≈ 8 variantes). Una variante "pasa" solo si es significativa tras BH **y** Δ ≥ +3M |
> | **Confirmación en BAJA+2** | Toda variante que pase se confirma en L y B2 con el multiclase (4 semillas pareadas, `028`/`030`). Se adopta solo si Δ ≥ −1 ee en ambos folds (no empeora) |
> | **Qué cuenta como "no adoptar"** | Si no pasa, **no se adopta aunque dé positivo**. Se documenta como "técnica probada, sin ganancia" (útil para el video a Michelina). No se prueban variantes adicionales para "rescatarla" |
> | **Registro** | Cada experimento: carpeta `NNN_nombre/` con README, fila en `LOG.md`, y actualización de `COBERTURA.md` (✗ → ✅/◐ con el número) |
>
> ## 8. Experimentos, en orden, con su condición de adopción
> Numeración desde el 037. Cada uno corre sobre el mismo harness; los tres primeros comparten una sola corrida de línea base.
>
> | # | Experimento (cierra el hueco de) | Diseño exacto | Se adopta si… | Qué se reentrena si se adopta |
> |---|---|---|---|---|
> | **037a** | Canarios sobre 855 columnas (profe 1.6) | 20 columnas U(0,1) + las 855; importancia gain media de 3 modelos entrenados **solo con 202103–06**; variantes: (i) conservar columnas con gain > máximo canario; (ii) conservar las > percentil 90 de los canarios | Δ ≥ +3M tras BH **y** confirma en L/B2. *Variante de velocidad:* si queda dentro de ±1 ee y quita > 50% de columnas **no se adopta** (el ahorro de cómputo no justifica cambiar el modelo final) | M2 con la lista de columnas podada |
> | **037b** | Quitar el mes más viejo, 202103 (libro 24.1) | Igual a la base pero entrenando con 202104–06 | Δ ≥ +3M tras BH y confirma en L/B2 (en L/B2 el train ya excluye 202103: la confirmación mira que no pierda) | M2 entrenado con 202104–06 (cambia el auxiliar y el resto del blend: se evalúa como "final con 202104–06", ver §9) |
> | **037c** | Deflactar montos (libro 20.9) | Factor mensual `f_m` = mediana (entre variables de monto) de [mediana de la variable entre clientes con valor > 0 en el mes m / la misma en 202103], calculado sin el target. Se divide cada monto por `f_m`, cada `_lag1` por `f_{m−1}`, cada `_lag2` por `f_{m−2}`; diferencias y ratios se recalculan; las columnas `n_*` y `r_*` con montos se deflactan igual (lista exacta en el README) | Δ ≥ +3M tras BH y confirma en L/B2 | M2 con montos deflactados (el factor de 202108 se calcula con sus propias features, sin target) |
> | **037d** | M2 sin undersampling (profe 1.7) | r ∈ {0.0986 (base), 0.3, 1.0}; mismos hiperparámetros (**confusión conocida**: con más filas, `min_data_in_leaf` pesa relativamente menos; se documenta pero no se retunea); 5 semillas | r=1.0 (o 0.3) con Δ ≥ +3M tras BH y confirma en L/B2 | M2 con ese r (entrenamiento más lento: ~10× filas; ~6–8 h para 30 modelos → en ese caso se reduce a 3 semillas por configuración y se documenta) |
> | **037e** | Diversidad con configuraciones M0 sobre las columnas de M2 (profe 2.1) | Ensemble de 3 configuraciones M1 vs 6 (M1 + M0), mismas columnas (855), rank medio, 8 semillas | Δ ≥ +3M tras BH y confirma en L/B2 | 30 modelos más de M2 con parámetros M0 |
> | **037f** | Hojas de Random Forest (profe 1.5, libro 20.10) | Sin fuga: el RF (sklearn, 100 árboles, profundidad ≤ 8, `min_samples_leaf` 200) se entrena con **202103–04** y sus índices de hoja se agregan como columnas; LightGBM entrena con **202105–06** (con y sin las hojas, mismos filas) y se valida en 202107. 8 semillas | Δ ≥ +3M tras BH y confirma en L/B2 **con el mismo esquema temporal** | Esquema de dos etapas completo (RF con 202103–04 → M2 con 202105–06): cambia el régimen de entrenamiento; se evalúa como "otro modelo" para mezclar, no como reemplazo |
>
> ## 9. Si algo se adopta: protocolo de reentrenamiento del final
> 1. **Solo después de terminar todo el lote** (no se reentrena por experimento): se combinan **todas** las variantes que pasaron, pero primero se verifica en una corrida de 036 que la combinación **no** pierde frente a cada una por separado (interacciones).
> 2. Se reentrena M2 (3 configuraciones × 10 semillas, ~50 min; más si 037d) con la combinación y se arma el blend con el mismo esquema (2/3 M2 + 1/3 resto), k=12000.
> 3. Se compara el top-12000 nuevo con `exp031`: si el solapamiento es > 97%, el cambio es chico y **no** se reenvía (el riesgo de un nuevo submit no se justifica); si es < 97%, se evalúa.
> 4. Para enviar al bot: un solo archivo. Regla del Public: se mantiene el nuevo salvo caída > ~3M respecto de 103.21 (señal de rotura); no se elige por diferencias menores.
> 5. `exp031` queda como respaldo; el último submit antes del cierre debe ser un único archivo.
>
> ## 10. Lo que decidimos NO hacer, y por qué
> | Idea | Decisión | Razón |
> |---|---|---|
> | Optuna completo sobre M2 | No | Sin fold independiente para certificar; 032/033 lo reemplazó y 036 no confirmó el efecto de `min_data` |
> | Auxiliar de BAJA+1 en M2 | No | No se puede validar (el valid del proxy es 202107, que el auxiliar usa para entrenar); el único aporte medido es ~+1M con 150 columnas |
> | Sacar columnas de calendario | No | 036: −1.5 ± 1.8M |
> | Peso mayor a 202106 | No | 036: −1.1 ± 1.4M; 020: −2.5M |
> | Stacking con meta-modelo | No | Con dos meses de validación es el método más propenso a sobreajustar |
> | Shapley / SHAP | No (para el modelo) | Interpretabilidad; el video a Miranda ya se entregó. Puede hacerse para el video a Michelina sin tocar el final |
> | Tratamiento de outliers, imputación vs NaN | No | Los árboles de LightGBM son robustos a ambos; la cátedra lo plantea como pregunta, y el costo de medirlo no se justifica con el tiempo que queda |
> | Features de cohorte con distancia de RF (clustering) | No | Costoso y sin forma de validarlo en el proxy; queda para la Última Competencia |
> | Pseudo-labeling de 202107/202108 | No | Transductivo y difícil de defender en el examen oral |
> | Monotone constraints, null importance, `scale_pos_weight` | No | Ganancia esperada baja; no hay hipótesis específica |
>
> ## 11. Calendario y límites
> | Hito | Fecha límite (hora local) | Qué pasa si no se llega |
> |---|---|---|
> | Terminar los experimentos 037a–f y la tabla BH | sáb 10-oct, 18:00 | Lo que no esté listo se documenta como "no probado por tiempo" |
> | Decidir qué se adopta | sáb 10-oct, 19:00 | — |
> | Reentrenar el final (si hay algo adoptado) | sáb 10-oct, 20:00 → ~00:00 | Si no termina antes del domingo 10:00, se descarta y queda `exp031` |
> | Enviar el submit | dom 11-oct, 12:00 | Pasada esa hora no se envía nada nuevo |
> | Ventana de seguridad | dom 11-oct, 12:00–23:59 | Solo verificar que el último submit del bot sea un único archivo |
> **Tiempo total estimado de cómputo:** 037a 30 min + 037b 20 + 037c 40 (incluye armar el factor) + 037d 65 + 037e 40 + 037f 120 ≈ **5.5 h**, más 1–2 h si se adopta algo. Mis estimaciones de tiempo fallaron por hasta 2× varias veces: el cronograma deja ~10 h de margen.
>
> ## 12. Riesgos del propio plan
> - Cada experimento nuevo sobre los mismos datos suma riesgo de sobreajuste: por eso BH y el umbral de +3M.
> - El proxy es BAJA+1, no BAJA+2: la confirmación en L/B2 es obligatoria, pero esos folds tienen los targets solapados. Una variante que solo pase en uno de los dos entornos **no** se adopta.
> - Ninguno de estos experimentos puede resolver si la ola de salidas de clientes con préstamo y mora persiste en 202110.
>
> ---
>
> # RESULTADO DEL PLAN DE CIERRE DE HUECOS (2026-10-09)
> Familia de **9 pruebas** (8 planeadas + 1 exploratoria posterior), Benjamini–Hochberg q = 0.10, mínimo +3M, proxy 202107 con 5–8 semillas pareadas (`037_hojas_rf/bh_final.py`, `bh_final.csv`):
>
> | Prueba | Δ (M) | ee | Pares | p unilateral | ¿Pasa? |
> |---|---|---|---|---|---|
> | 037d r = 0.3 (más negativos) | +2.9 | 2.2 | 3/5 | 0.13 | No |
> | 037b sin 202103 | +1.9 | 1.6 | 5/8 | 0.14 | No |
> | 037e + configuraciones M0 | +0.6 | 0.5 | 4/8 | 0.16 | No |
> | 037d r = 1.0 (sin undersampling) | +1.8 | 2.9 | 3/5 | 0.29 | No |
> | 037c deflactado | −1.4 | 0.7 | 2/8 | 0.94 | No |
> | 037a canarios > máximo (22 columnas) | −122.2 | 3.1 | 0/8 | 1.00 | No |
> | 037a canarios > p90 (30 columnas) | −122.4 | 3.1 | 0/8 | 1.00 | No |
> | 037f hojas de RF categóricas | −46.5 | 1.5 | 0/8 | 1.00 | No |
> | 037f hojas de RF numéricas (posterior) | −12.1 | 1.3 | 0/8 | 1.00 | No |
>
> **Ninguna variante pasa. El final (`exp031_final_w67_md_k12000.csv`) no cambia.** Lo que quedó en ✅ en las secciones 1 y 2 de este documento es "probado, sin ganancia en esta forma". Huecos que **siguen sin probarse** (los más caros o sin forma de validarse): stacking, Shapley sobre el modelo, outliers e imputación, features de cohorte con la distancia de RF, y el auxiliar de BAJA+1 sobre M2.

