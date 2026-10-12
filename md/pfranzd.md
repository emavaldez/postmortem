# Pedro Pablo Franz Duran — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: pfranzd
- Repositorio: https://github.com/pfranzd/dmeyf2026-entregas
- Link posteado: https://github.com/pfranzd/dmeyf2026-entregas
- Commit: 8f5e659a3177997d838cea33fceddeb7835d516a
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/pfranzd/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/pfranzd.json

## Resumen

Repositorio con una carpeta `competencia_01/` que contiene un pipeline en Python (paquete `competencia_1`: DuckDB para datos y variables, LightGBM, Optuna y polars), configuraciones YAML, 72 modelos LightGBM ya entrenados, tres estudios de Optuna y dos README. La predicción sale de `entrega.py` (o `entrega.ipynb`, con el mismo código; `reproducir.sh` lo ejecuta dentro de un entorno virtual): descarga el CSV crudo, reconstruye la clase ternaria con SQL y, para cada uno de 3 componentes (e032, e033, e034), arma las variables (intra-fila, lags, deltas, ventanas, tendencia y rankings por mes; e033 pasa los montos a rank con cero fijo; e034 agrega variables de comportamiento), predice 202108 con 24 modelos (12 conjuntos de hiperparámetros salidos de Optuna × 2 semillas, entrenados con 202103–202106 y clase binaria BAJA+1 o BAJA+2) y promedia sus probabilidades. Después promedia los ranks normalizados de los 3 componentes, escribe los 10.500 clientes de mayor valor y compara el sha256 del CSV con el registrado. Hay tres modos: predecir con los modelos guardados, reentrenarlos, o rehacer también la búsqueda de hiperparámetros.

**Qué entrega.** Un CSV sin encabezado con 10.500 numero_de_cliente, uno por línea: `<fecha>_ensamble_e10500.csv` en work/entrega/runs/<fecha>_ensamble/submits/. Según el README, el archivo entregado fue `20261011-091551_ens04_e032_e033_e034_e10500.csv` (sha256 385da709…50d5df), con puntaje público declarado de 110,1650 M. El repositorio no incluye ese CSV: trae los 72 modelos entrenados y el sha256 esperado para comparar.

**Cómo se ejecuta.** Según competencia_01/README.md: en Linux o una VM de GCP, `bash reproducir.sh` (opcionalmente con el argumento `entrenar` o `completo`), que crea .venv con requirements-lock.txt y ejecuta entrega.py. En Windows: crear el entorno con `py -3.11 -m venv .venv`, instalar requirements-lock.txt, fijar ENTREGA_MODO y ejecutar entrega.py. También se puede ejecutar entrega.ipynb completo. Modos: `predecir` (por defecto, usa los 72 modelos guardados, ~1 h), `entrenar` (reentrena, ~4 h) y `completo` (rehace Optuna, 180 trials, ~5 h). El CSV crudo se descarga de una URL pública si no está en datasets/raw/.

## Ficha

- **Lenguajes:** Python, SQL, Shell
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: positivo = BAJA+1 o BAJA+2 (`target.positivos` en configs/base.yaml). La clase ternaria se reconstruye desde el CSV crudo con SQL (datos.py). Para medir (AUC y curva de ganancia) el positivo es sólo BAJA+2. El peso de BAJA+1 al entrenar es 1,0 (sin pesos).
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202105, 202106
- **Mes que predice:** 202108
- **Submuestreo:** Sólo en la búsqueda de hiperparámetros: se conserva el 0,25 de las filas CONTINUA y todas las BAJA+1 y BAJA+2, eligiendo con un número determinístico derivado de (cliente, mes, semilla). Los modelos finales se entrenan sin submuestreo y min_data_in_leaf se multiplica por el cociente entre las filas de los meses finales y las filas de train del último fold.
- **Calidad de datos:** Se excluyen 4 columnas listadas en `fe.drop_drift` (Master_fultimo_cierre, Visa_fultimo_cierre, Master_Finiciomora, Visa_Finiciomora; el comentario del YAML dice `PSI alto`). El parquet base se valida: tipos de numero_de_cliente (BIGINT) y foto_mes (INTEGER), unicidad de (cliente, mes), valores de clase y nulos en las claves. No se observa en el código el pase a NA de variables por mes.
- **Drifting:** En los tres componentes: exclusión de las 4 columnas de `drop_drift` y rankings dentro de cada mes (percent_rank de una lista curada de 19 campos y decil de 4). Sólo en e033: todos los montos (m*, Master_m*, Visa_m*, tc_m*, m_*) se reemplazan por su rank con cero fijo por mes y por signo (cume_dist) antes de calcular lags, deltas y ventanas. El código tiene además un modo `deflactado` (monto / mediana de los montos positivos del mes) que la entrega no usa.
- **Variables dentro del mes:** Familia 1 (intrafila.py): 16 sumas Master + Visa (tc_*), 6 variables de fechas y estado de tarjetas (2 de las 8 definidas se omiten por derivar de columnas excluidas), 11 agregados (activos, préstamos, seguros, transacciones por canal, transferencias netas, cheques rechazados, descuentos, productos contratados), 13 cocientes (r_*) y 12 indicadores 0/1 (f_*). Además percent_rank por mes de una lista curada de 19 campos (pr_*) y decil de 4 (d10_*). e034 suma r_transf_emitidas_recibidas y rfm_score.
- **Variables históricas:** Sobre una lista curada de 36 campos y un panel denso cliente × mes: lags 1 y 2; deltas 1 y 2 en valor y en porcentaje; media, máximo, mínimo y desvío sobre t-2..t; cociente contra esa media; pendiente (regr_slope contra cliente_antiguedad) sobre t-2..t; meses_en_panel y antiguedad_panel. e034 agrega f_perdio_payroll, n_productos_perdidos, f_visa_status_sube, f_master_status_sube, tres recency (payroll, transacciones, consumo de tarjeta), r_saldo_vs_max, r_activos_vs_max y racha_caida_ctrx.
- **Selección de variables:** En el camino de la entrega no se quita ninguna variable por selección: `dataset.excluir_bloques` y `dataset.excluir_features` están vacíos y entran todas las columnas del parquet de features salvo claves y clase. El repositorio incluye etapas de canaritos y de ablación por bloques, desactivadas en los configs de la entrega.
- **Optimización de hiperparámetros:** Optuna, un estudio de 60 trials por componente (180 en total) guardado en SQLite: TPESampler con semilla 111623 + trials ya hechos y MedianPruner con 10 trials iniciales, que corta el trial después del primer fold. Objetivo: AUC sobre BAJA+2 promediado en 2 folds temporales. Espacio: learning_rate 0,005–0,05 (log), feature_fraction 0,05–0,5 (log), num_leaves 8–256 (log), min_data_in_leaf 5–2000 (log), num_iterations 150–1500. No hay early stopping: num_iterations es un hiperparámetro más.
- **Hiperparámetros finales:** 12 conjuntos por componente en params.json, con min_data_in_leaf ya reescalado. Rangos: e032: learning_rate 0,0077–0,0122, num_iterations 510–1176, feature_fraction 0,131–0,191, num_leaves 28–233, min_data_in_leaf 1585–5868; e033: learning_rate 0,0050–0,0136, num_iterations 568–1384, feature_fraction 0,137–0,347, num_leaves 49–109, min_data_in_leaf 1237–5914; e034: learning_rate 0,0082–0,0154, num_iterations 619–895, feature_fraction 0,142–0,347, num_leaves 49–141, min_data_in_leaf 1106–5914. Fijos en los tres: objective binary, max_bin 31, boost_from_average true, feature_pre_filter false, force_row_wise true, deterministic true, num_threads 8.
- **Semillas:** 2 semillas por conjunto de hiperparámetros: 111623 y 116239, las dos primeras de la lista de 5 de config/semillas.py (`final.n_semillas: 2`). La semilla maestra 111623 se usa en Optuna, en el submuestreo y en LightGBM durante la búsqueda.
- **Cantidad de semillas:** 2
- **Ensamble:** Dos niveles. Dentro de cada componente: promedio de las probabilidades de 24 modelos (12 conjuntos de hiperparámetros × 2 semillas). Entre los 3 componentes (e032, e033, e034): cada promedio se convierte en rank normalizado (rank promedio / n) y se promedian con pesos 1, 1, 1. Son 72 modelos en total.
- **Corte:** Cantidad fija: los 10.500 clientes de mayor valor del ensamble (`envios: 10500` en definitiva/entrega.json), con desempate por numero_de_cliente ascendente. Los YAML de experimento piden cortes de 10.000 y 11.000 por componente. No se observa en el código de dónde sale el valor 10.500.
- **Validación:** Validación temporal con 2 meses de distancia entre train y validación, en 2 folds de ventana expansiva: train [202103] → 202105 y train [202103, 202104] → 202106. Se usa dentro de Optuna con el AUC sobre BAJA+2 como objetivo; por trial también se guardan la ganancia en meseta (media móvil de 401 envíos sobre la curva, con 1.072.500 por acierto y −27.500 por el resto según dmeyf/metrics.py) y la cantidad de envíos donde ocurre, que no intervienen en la elección. La etapa `validacion` del pipeline está desactivada en los configs de la entrega.
- **Salidas:** Todo dentro de work/entrega/. Por componente: runs/<fecha>_entrega/ con probas/ensamble/<trial>_s<semilla>.parquet, probas/promedio.parquet, submits/<run>_promedio_e<N>.csv, config_resuelta.yaml, meta.json, run.log y features.txt. Del ensamble: runs/<fecha>_ensamble/probas.parquet y submits/<fecha>_ensamble_e10500.csv (sólo numero_de_cliente, sin encabezado). Al reentrenar se guardan también modelos/*.txt e importancias.csv; en modo completo, optuna_trials.csv y best_params.json.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Mínimos y máximos de ventana (`variables.min_max_ventana`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Técnicas sólo exploradas

- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Estandarización o normalización por mes (`drifting.estandarizacion_por_mes`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Python 3.11 (archivo .python-version; 3.11.0 en entrega.json) y unos 16 GB de RAM según el README, que da instrucciones para Linux o una VM de GCP y para Windows (PowerShell). Versiones en requirements.txt: duckdb 1.5.5, lightgbm 4.7.0, numpy 2.4.6, optuna 4.9.0, polars 1.43.2, pyyaml 6.0.3; requirements-lock.txt lista 19 paquetes con versión exacta. `num_threads` está fijado en 8.

## Pasos del camino de la entrega

1. **Punto de entrada y modo de ejecución.** `reproducir.sh` crea un entorno virtual con requirements-lock.txt y ejecuta `entrega.py` con el modo pasado como argumento. `entrega.py` lee ENTREGA_MODO (predecir, entrenar o completo), fija la carpeta de trabajo en work/entrega y la ruta de la base de Optuna. (`competencia_01/reproducir.sh` líneas 11–22; `competencia_01/entrega.py` líneas 18–40)
2. **Chequeo de versiones y descarga del dataset crudo.** Compara las versiones instaladas con las guardadas en definitiva/entrega.json e imprime las que difieren. Si falta datasets/raw/competencia_01_crudo.csv lo copia de una ruta local o lo descarga de la URL pública. (`competencia_01/entrega.py` líneas 48–70)
3. **Recorrido de los tres componentes.** `_reproducir_ensamble` recorre los 3 componentes de definitiva/entrega.json y para cada uno ejecuta el pipeline (`main`) con su config.yaml congelado, que activa las etapas datos, features, final y salida. En modo entrenar agrega `final.modelos_desde=null`; en modo completo usa el YAML original del experimento. (`competencia_01/competencia_1/pipeline/entrega.py` líneas 445–474; `competencia_01/competencia_1/main.py` líneas 109–129; `competencia_01/competencia_1/definitiva/entrega.json` líneas 30–67)
4. **Carga y validación de la configuración.** Cada config YAML se lee resolviendo la herencia (`hereda`), se le aplican los overrides y se convierte en dataclasses que rechazan claves faltantes o desconocidas. Se valida, entre otras cosas, que haya al menos 2 meses entre el último mes de train y el de validación o el objetivo. (`competencia_01/competencia_1/pipeline/config.py` líneas 247–257; `competencia_01/competencia_1/pipeline/config.py` líneas 305–314; `competencia_01/competencia_1/pipeline/config.py` líneas 362–392; `competencia_01/competencia_1/configs/base.yaml` líneas 7–19; `competencia_01/competencia_1/configs/exp/e032_expansiva_auc_topk.yaml` líneas 18–48)
5. **Reconstrucción de la clase y parquet base.** DuckDB lee el CSV crudo forzando numero_de_cliente a BIGINT y foto_mes a INTEGER, arma el panel denso cliente × mes y asigna CONTINUA, BAJA+1 o BAJA+2 según la presencia del cliente 1 y 2 meses después. El resultado se guarda como cache/base.parquet y se valida. (`competencia_01/competencia_1/pipeline/datos.py` líneas 28–53; `competencia_01/competencia_1/pipeline/datos.py` líneas 66–93; `competencia_01/competencia_1/pipeline/datos.py` líneas 127–167)
6. **Panel denso y variables intra-fila.** La query de variables parte de un panel cliente × mes con filas `fantasma` para los meses ausentes. Sobre él se agregan las sumas Master + Visa, las variables de fechas de tarjetas, los agregados, los cocientes y los indicadores, usando macros que tratan los nulos y la división por cero. (`competencia_01/competencia_1/pipeline/features/temporales.py` líneas 15–33; `competencia_01/competencia_1/pipeline/features/intrafila.py` líneas 306–348; `competencia_01/competencia_1/pipeline/features/macros.py` líneas 5–11)
7. **Escala de los montos (sólo componente e033).** Con `fe.montos: rank_cero_fijo`, cada columna de monto se reemplaza por un valor entre −1 y 1: 0 queda en 0, los positivos toman su cume_dist dentro del mes y los negativos el cume_dist con signo menos. El cálculo se hace en lotes de 5 columnas y el resultado se une al panel antes de las variables históricas. (`competencia_01/competencia_1/pipeline/features/rankings.py` líneas 47–56; `competencia_01/competencia_1/pipeline/features/rankings.py` líneas 59–99; `competencia_01/competencia_1/pipeline/features/query.py` líneas 84–97; `competencia_01/competencia_1/configs/exp/e033_montos_rank_cero_fijo.yaml` líneas 12–13)
8. **Variables históricas.** Para cada uno de los 36 campos de la lista curada se calculan lags 1 y 2, estadísticos sobre la ventana t-2..t (media, máximo, mínimo, desvío), la pendiente sobre esa ventana, deltas 1 y 2 en valor y en porcentaje y el cociente contra la media móvil; además dos variables de historia del cliente en el panel. (`competencia_01/competencia_1/pipeline/features/campos.py` líneas 10–48; `competencia_01/competencia_1/pipeline/features/temporales.py` líneas 75–121; `competencia_01/competencia_1/pipeline/features/temporales.py` líneas 124–151)
9. **Variables de comportamiento (sólo componente e034).** Con `fe.comportamiento: true` se agregan indicadores de pérdida de payroll y de productos, suba del status de las tarjetas, meses desde el último payroll, transacción o consumo de tarjeta, cocientes de saldo y activos contra su máximo de t-2..t, racha de caída de ctrx_quarter, cociente de transferencias emitidas / recibidas y un puntaje RFM por quintiles del mes. (`competencia_01/competencia_1/pipeline/features/comportamiento.py` líneas 50–94; `competencia_01/competencia_1/pipeline/features/comportamiento.py` líneas 97–118; `competencia_01/competencia_1/configs/exp/e034_comportamiento.yaml` líneas 15–16)
10. **Rankings por mes y parquet de features.** Sobre las filas reales se calculan el percent_rank dentro del mes de los campos de una lista curada (19) y el decil de 4. La query final excluye las columnas auxiliares y las de `drop_drift`, se ordena por mes y cliente y se escribe en features/<fe_hash>/features.parquet junto con el catálogo de variables y el SQL ejecutado. (`competencia_01/competencia_1/pipeline/features/rankings.py` líneas 17–38; `competencia_01/competencia_1/pipeline/features/query.py` líneas 113–135; `competencia_01/competencia_1/pipeline/features/__init__.py` líneas 130–181)
11. **Búsqueda de hiperparámetros con Optuna (origen de params.json).** Cada trial entrena en los 2 folds temporales con el 0,25 de CONTINUA y la semilla maestra, y devuelve el AUC medio sobre BAJA+2; el pruner puede cortar el trial después del primer fold. Son 60 trials por componente. En los modos predecir y entrenar esta etapa no se ejecuta: se usan los resultados guardados. (`competencia_01/competencia_1/pipeline/optimizacion.py` líneas 70–125; `competencia_01/competencia_1/pipeline/optimizacion.py` líneas 202–224; `competencia_01/competencia_1/pipeline/optimizacion.py` líneas 256–274; `competencia_01/competencia_1/pipeline/dataset.py` líneas 91–96; `competencia_01/competencia_1/configs/exp/e032_expansiva_auc_topk.yaml` líneas 28–40)
12. **Elección de 12 trials y reescalado de min_data_in_leaf.** `final.params_desde: top:12` toma los 12 trials completos de mayor AUC. Como el final entrena sin submuestreo, min_data_in_leaf se multiplica por filas de los meses finales / filas de train del último fold. Los conjuntos ya reescalados quedaron guardados en el params.json de cada componente. (`competencia_01/competencia_1/pipeline/optimizacion.py` líneas 315–319; `competencia_01/competencia_1/pipeline/final.py` líneas 46–64; `competencia_01/competencia_1/pipeline/final.py` líneas 88–95; `competencia_01/competencia_1/pipeline/modelo.py` líneas 104–109; `competencia_01/competencia_1/definitiva/componentes/0_e032_expansiva_auc_topk/params.json` líneas 1–13)
13. **Modelos finales y predicción de 202108.** Para cada conjunto de hiperparámetros × cada semilla (12 × 2) se carga el modelo guardado o se entrena con 202103–202106 sin submuestreo, y se predice la probabilidad de cada cliente de 202108. Las 24 predicciones se promedian en probas/promedio.parquet. (`competencia_01/competencia_1/pipeline/final.py` líneas 105–173; `competencia_01/competencia_1/pipeline/modelo.py` líneas 20–36)
14. **CSV de cada componente y verificación.** La etapa salida verifica que las probabilidades cubran exactamente los clientes del mes objetivo, ordena por probabilidad descendente (desempate por numero_de_cliente) y escribe el CSV del corte pedido, que relee como texto para validar el formato. Su sha256 se compara con el guardado para ese componente. (`competencia_01/competencia_1/pipeline/salida.py` líneas 47–55; `competencia_01/competencia_1/pipeline/salida.py` líneas 81–97; `competencia_01/competencia_1/pipeline/salida.py` líneas 186–219; `competencia_01/competencia_1/pipeline/entrega.py` líneas 405–412)
15. **Ensamble por ranks, corte en 10.500 y comparación final.** Las probabilidades promedio de los 3 componentes se convierten en rank normalizado, se promedian con pesos iguales y se escriben los 10.500 clientes de mayor valor en `<fecha>_ensamble_e10500.csv`. El sha256 de ese archivo se compara con el de definitiva/entrega.json y el script termina con código 1 si difiere. (`competencia_01/competencia_1/pipeline/ensamble.py` líneas 20–63; `competencia_01/competencia_1/pipeline/entrega.py` líneas 476–490; `competencia_01/competencia_1/definitiva/entrega.json` líneas 5–17; `competencia_01/entrega.py` líneas 84–87)

## Archivos

- `README.md` · explicacion · Markdown · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/README.md.txt) — Presentación del repositorio: una tabla con la competencia 01, su carpeta, el nombre de la entrega (ens04_e032_e033_e034), 10.500 envíos, el inicio del sha256 y el puntaje público que declara (110,17 M). Indica que los datasets no se suben y que el script los descarga.
- `competencia_01/requirements.txt` · configuracion · Texto · 9 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/requirements.txt.txt) — Dependencias directas con versión exacta: duckdb 1.5.5, lightgbm 4.7.0, numpy 2.4.6, optuna 4.9.0, polars 1.43.2 y pyyaml 6.0.3; indica Python 3.11 o superior.
- `competencia_01/entrega.ipynb` · principal · Jupyter (python) · 87 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/entrega.ipynb.txt) — Notebook con el mismo código que entrega.py, en 10 celdas (4 de texto y 6 de código). Según el README, el modo se elige en la segunda celda.
- `competencia_01/README.md` · explicacion · Markdown · 157 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/README.md.txt) — Describe la entrega: ensamble por promedio de rankings de 3 componentes de 24 modelos cada uno, nombre y sha256 del CSV, puntaje público declarado (110,1650 M), los tres modos de reproducción con sus tiempos, comandos para Linux y Windows, el entorno, qué hace cada componente, los trials de Optuna usados y el contenido de la carpeta. Menciona la ganancia como +780.000 / −20.000.
- `competencia_01/reproducir.sh` · principal · Shell · 22 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/reproducir.sh.txt) — Script de shell para Linux o una VM de GCP: prepara el entorno virtual y ejecuta entrega.py con el modo recibido como argumento.
- `competencia_01/entrega.py` · principal · Python · 87 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/entrega.py.txt) — Punto de entrada en formato de celdas `# %%`: elige el modo, revisa versiones, obtiene el CSV crudo y llama a la reproducción del pipeline, que termina comparando el sha256 del CSV generado.
- `competencia_01/requirements-lock.txt` · configuracion · Texto · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/requirements-lock.txt.txt) — Entorno congelado: 19 paquetes con versión exacta, incluidas las dependencias transitivas. Es el archivo que instala reproducir.sh.
- `competencia_01/optimizacion/2_e034_comportamiento/resumen.json` · configuracion · JSON · 141 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/optimizacion/2_e034_comportamiento/resumen.json.txt) — Resumen del estudio de Optuna del componente: nombre del estudio, objetivo auc, 60 trials (34 completos y 26 podados) y los 12 trials de mayor AUC (entre 0,8973 y 0,8982 según el archivo) con sus hiperparámetros antes del reescalado de min_data_in_leaf. Ningún script lo lee.
- `competencia_01/optimizacion/1_e033_montos_rank_cero_fijo/resumen.json` · configuracion · JSON · 141 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/optimizacion/1_e033_montos_rank_cero_fijo/resumen.json.txt) — Resumen del estudio de Optuna del componente: nombre del estudio, objetivo auc, 60 trials (38 completos y 22 podados) y los 12 trials de mayor AUC (entre 0,8966 y 0,8974 según el archivo) con sus hiperparámetros antes del reescalado de min_data_in_leaf. Ningún script lo lee.
- `competencia_01/optimizacion/0_e032_expansiva_auc_topk/resumen.json` · configuracion · JSON · 141 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/optimizacion/0_e032_expansiva_auc_topk/resumen.json.txt) — Resumen del estudio de Optuna del componente: nombre del estudio, objetivo auc, 60 trials (37 completos y 23 podados) y los 12 trials de mayor AUC (entre 0,8977 y 0,8986 según el archivo) con sus hiperparámetros antes del reescalado de min_data_in_leaf. Ningún script lo lee.
- `competencia_01/competencia_1/entrega.py` · secundario · Python · 123 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/entrega.py.txt) — Interfaz de línea de comandos (`python -m competencia_1.entrega`) con los subcomandos `promover` (congela un run o un ensamble en competencia_1/definitiva/) y `reproducir`. El entrega.py de la raíz no pasa por este archivo: importa directamente pipeline/entrega.py.
- `competencia_01/competencia_1/main.py` · principal · Python · 133 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/main.py.txt) — Orquestador del pipeline: carga la configuración, abre un run y ejecuta en orden las etapas activas.
- `competencia_01/competencia_1/pipeline/datos.py` · principal · Python · 212 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/datos.py.txt) — Etapa datos: lee el CSV con DuckDB, reconstruye la clase ternaria si se pide, escribe el parquet base en caché y valida esquema, unicidad, clases y períodos.
- `competencia_01/competencia_1/pipeline/final.py` · principal · Python · 186 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/final.py.txt) — Etapa final: resuelve los conjuntos de hiperparámetros y las semillas, entrena (o carga) un modelo por combinación, predice el mes objetivo y promedia las probabilidades.
- `competencia_01/competencia_1/pipeline/semillas.py` · principal · Python · 45 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/semillas.py.txt) — Genera y valida semillas: primos entre 100003 y 999983, empezando por las 5 de config/semillas.py.
- `competencia_01/competencia_1/pipeline/salida.py` · principal · Python · 234 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/salida.py.txt) — Etapa salida: convierte probabilidades en CSV de entrega (sólo IDs, sin encabezado), valida el archivo escrito y mide la coincidencia entre modelos.
- `competencia_01/competencia_1/pipeline/config.py` · principal · Python · 511 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/config.py.txt) — Configuración centralizada: lee YAML con herencia y overrides, la convierte en dataclasses inmutables sin valores por defecto y valida rangos y dependencias entre opciones.
- `competencia_01/competencia_1/pipeline/modelo.py` · principal · Python · 191 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/modelo.py.txt) — Funciones de LightGBM: armado de parámetros, Dataset, entrenamiento, predicción, importancias, reescalado de min_data_in_leaf, nombre del estudio de Optuna y lectura de hiperparámetros.
- `competencia_01/competencia_1/pipeline/periodos.py` · principal · Python · 73 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/periodos.py.txt) — Aritmética de meses AAAAMM, derivación de folds y meses finales a partir del mes objetivo y el gap, y validaciones de distancia y de clase completa.
- `competencia_01/competencia_1/pipeline/dataset.py` · principal · Python · 142 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/dataset.py.txt) — Arma las matrices de entrenamiento y predicción desde el parquet de features, con submuestreo determinístico de CONTINUA y pesos opcionales para BAJA+1.
- `competencia_01/competencia_1/pipeline/canaritos.py` · secundario · Python · 164 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/canaritos.py.txt) — Etapa canaritos: compara la importancia de cada variable con la de columnas aleatorias y escribe la lista de las que no superan al canarito de mayor importancia. Está desactivada en los configs de la entrega.
- `competencia_01/competencia_1/pipeline/optimizacion.py` · principal · Python · 411 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/optimizacion.py.txt) — Etapa optuna: búsqueda de hiperparámetros con validación temporal por folds, estudio persistido en SQLite y exportación de los resultados. De sus trials salen los hiperparámetros guardados en params.json; sólo se ejecuta en el modo completo.
- `competencia_01/competencia_1/pipeline/entrega.py` · principal · Python · 534 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/entrega.py.txt) — Lógica de la entrega definitiva: `promover` y `promover_ensamble` congelan runs en competencia_1/definitiva/, y `reproducir` / `reproducir_completo` vuelven a correr cada componente, arman el ensamble y comparan el sha256 del CSV.
- `competencia_01/competencia_1/pipeline/evaluacion.py` · secundario · Python · 101 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/evaluacion.py.txt) — Etapa validacion: evalúa un único conjunto de hiperparámetros en los folds temporales y guarda la curva de ganancia. Está desactivada en los configs de la entrega.
- `competencia_01/competencia_1/pipeline/ablacion.py` · secundario · Python · 278 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/ablacion.py.txt) — Etapa ablacion: compara variantes de conjuntos de variables (subconjuntos de columnas por bloque) con las mismas semillas y la misma muestra de submuestreo. Está desactivada en los configs de la entrega.
- `competencia_01/competencia_1/pipeline/ensamble.py` · principal · Python · 88 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/ensamble.py.txt) — Combina las probabilidades de varios runs en un solo ranking, por promedio de ranks normalizados (método `rank`, el de la entrega) o de probabilidades (método `prob`).
- `competencia_01/competencia_1/pipeline/metricas.py` · principal · Python · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/metricas.py.txt) — Resumen de métricas de un mes de validación: AUC sobre BAJA+2, curva de ganancia y ganancia en meseta.
- `competencia_01/competencia_1/pipeline/estabilidad.py` · secundario · Python · 325 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/estabilidad.py.txt) — Etapa estabilidad: reentrena los top-k trials de Optuna con N semillas, compara sus estadísticos, corre la simulación público / privado y exporta el trial elegido. Está desactivada en los configs de la entrega.
- `competencia_01/competencia_1/pipeline/tracking.py` · principal · Python · 208 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/tracking.py.txt) — Registro por corrida: carpeta del run, logging, meta.json con sha256 de los archivos generados y una fila por run en runs.csv.
- `competencia_01/competencia_1/pipeline/simulacion.py` · secundario · Python · 96 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/simulacion.py.txt) — Simulación de repartos público / privado (30 % / 70 %) sobre un mes con clase conocida; la usa la etapa estabilidad, desactivada en la entrega.
- `competencia_01/competencia_1/pipeline/features/extras.py` · secundario · Python · 23 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/extras.py.txt) — Genera columnas aleatorias (canaritos). La query la invoca siempre, pero con `fe.canaritos.activo: false` (el valor de los configs de la entrega) devuelve una cadena vacía.
- `competencia_01/competencia_1/pipeline/features/campos.py` · principal · Python · 146 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/campos.py.txt) — Listas de campos sobre los que se calculan las variables históricas (36) y los rankings por mes (19), y funciones que resuelven qué campos usar y cuáles son montos.
- `competencia_01/competencia_1/pipeline/features/comportamiento.py` · principal · Python · 118 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/comportamiento.py.txt) — Familia 9 (activa sólo en el componente e034): indicadores de eventos, recency, cocientes contra el máximo reciente y un puntaje RFM, mirando como máximo 2 meses hacia atrás.
- `competencia_01/competencia_1/pipeline/features/query.py` · principal · Python · 135 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/query.py.txt) — Ensambla la query SQL de variables en el orden panel → base → escala → series → reales → selección final, y rechaza cualquier query que contenga `lead(` o `following`.
- `competencia_01/competencia_1/pipeline/features/seleccion.py` · secundario · Python · 102 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/seleccion.py.txt) — Selección de columnas por bloque del catálogo, usada por la ablación y por `dataset.excluir_*`. En la entrega no hay exclusiones y sus funciones no se llegan a llamar.
- `competencia_01/competencia_1/pipeline/features/rankings.py` · principal · Python · 99 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/rankings.py.txt) — Rankings dentro del mes (percent_rank y decil) y reescalado de los montos a una escala relativa por mes (modo `rank_cero_fijo`, usado por el componente e033, y modo `deflactado`, sin uso en la entrega).
- `competencia_01/competencia_1/pipeline/features/catalogo.py` · principal · Python · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/catalogo.py.txt) — Catálogo de variables: cada fragmento de SQL se registra al generarse y el conjunto se guarda como CSV.
- `competencia_01/competencia_1/pipeline/features/__init__.py` · principal · Python · 195 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/__init__.py.txt) — Etapa features: construye el parquet de variables con una única query de DuckDB, lo guarda en una caché identificada por un hash de la configuración y verifica la salida.
- `competencia_01/competencia_1/pipeline/features/intrafila.py` · principal · Python · 348 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/intrafila.py.txt) — Familia 1: variables calculadas dentro de la misma fila (sumas Master + Visa, fechas de tarjetas, agregados, cocientes e indicadores).
- `competencia_01/competencia_1/pipeline/features/macros.py` · principal · Python · 16 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/macros.py.txt) — Tres macros SQL de DuckDB usadas por las demás familias de variables.
- `competencia_01/competencia_1/pipeline/features/temporales.py` · principal · Python · 151 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/temporales.py.txt) — Familias históricas calculadas sobre el panel denso cliente × mes: lags, estadísticos de ventana, pendiente, historia en el panel, deltas y cociente contra la media móvil.
- `competencia_01/competencia_1/definitiva/entrega.json` · configuracion · JSON · 74 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/definitiva/entrega.json.txt) — Descripción del ensamble entregado: método `rank`, pesos 1, 1, 1, corte de 10.500 envíos, nombre y sha256 del CSV, versiones (Python 3.11.0, lightgbm 4.7.0, optuna 4.9.0, polars 1.43.2, duckdb 1.5.5, numpy 2.4.6), resultado público declarado 110,165, 72 modelos y los 3 componentes con su carpeta, run de origen, corte de verificación (10.500, 10.000 y 10.000) y sha256.
- `competencia_01/competencia_1/definitiva/componentes/2_e034_comportamiento/entrega.json` · configuracion · JSON · 23 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/definitiva/componentes/2_e034_comportamiento/entrega.json.txt) — Datos del componente e034_comportamiento: run de origen, commits, corte de verificación de 10.000 envíos, nombre y sha256 del CSV propio, versiones y 24 modelos incluidos.
- `competencia_01/competencia_1/definitiva/componentes/2_e034_comportamiento/config.yaml` · configuracion · YAML · 172 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/definitiva/componentes/2_e034_comportamiento/config.yaml.txt) — Configuración congelada del componente e034_comportamiento, generada por `promover`: folds y meses finales, familias de variables, hiperparámetros leídos de params.json sin reescalar, modelos leídos de la carpeta `modelos`, corte de 10.000 y sólo las etapas datos, features, final y salida. Tiene `fe.comportamiento: true`.
- `competencia_01/competencia_1/definitiva/componentes/2_e034_comportamiento/params.json` · configuracion · JSON · 125 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/definitiva/componentes/2_e034_comportamiento/params.json.txt) — 12 conjuntos de hiperparámetros del componente e034_comportamiento (etiquetas t<número de trial>): learning_rate, num_iterations, feature_fraction, num_leaves y min_data_in_leaf ya reescalado.
- `competencia_01/competencia_1/definitiva/componentes/1_e033_montos_rank_cero_fijo/entrega.json` · configuracion · JSON · 23 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/definitiva/componentes/1_e033_montos_rank_cero_fijo/entrega.json.txt) — Datos del componente e033_montos_rank_cero_fijo: run de origen, commits, corte de verificación de 10.000 envíos, nombre y sha256 del CSV propio, versiones y 24 modelos incluidos.
- `competencia_01/competencia_1/definitiva/componentes/1_e033_montos_rank_cero_fijo/config.yaml` · configuracion · YAML · 172 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/definitiva/componentes/1_e033_montos_rank_cero_fijo/config.yaml.txt) — Configuración congelada del componente e033_montos_rank_cero_fijo, generada por `promover`: folds y meses finales, familias de variables, hiperparámetros leídos de params.json sin reescalar, modelos leídos de la carpeta `modelos`, corte de 10.000 y sólo las etapas datos, features, final y salida. Tiene `fe.montos: rank_cero_fijo`.
- `competencia_01/competencia_1/definitiva/componentes/1_e033_montos_rank_cero_fijo/params.json` · configuracion · JSON · 125 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/definitiva/componentes/1_e033_montos_rank_cero_fijo/params.json.txt) — 12 conjuntos de hiperparámetros del componente e033_montos_rank_cero_fijo (etiquetas t<número de trial>): learning_rate, num_iterations, feature_fraction, num_leaves y min_data_in_leaf ya reescalado.
- `competencia_01/competencia_1/definitiva/componentes/0_e032_expansiva_auc_topk/entrega.json` · configuracion · JSON · 23 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/definitiva/componentes/0_e032_expansiva_auc_topk/entrega.json.txt) — Datos del componente e032_expansiva_auc_topk: run de origen, commits, corte de verificación de 10.500 envíos, nombre y sha256 del CSV propio, versiones y 24 modelos incluidos.
- `competencia_01/competencia_1/definitiva/componentes/0_e032_expansiva_auc_topk/config.yaml` · configuracion · YAML · 169 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/definitiva/componentes/0_e032_expansiva_auc_topk/config.yaml.txt) — Configuración congelada del componente e032_expansiva_auc_topk, generada por `promover`: folds y meses finales, familias de variables, hiperparámetros leídos de params.json sin reescalar, modelos leídos de la carpeta `modelos`, corte de 10.500 y sólo las etapas datos, features, final y salida. No trae las claves `fe.montos`, `fe.comportamiento` ni `target.peso_baja1`, que el código completa con sus valores por defecto.
- `competencia_01/competencia_1/definitiva/componentes/0_e032_expansiva_auc_topk/params.json` · configuracion · JSON · 125 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/definitiva/componentes/0_e032_expansiva_auc_topk/params.json.txt) — 12 conjuntos de hiperparámetros del componente e032_expansiva_auc_topk (etiquetas t<número de trial>): learning_rate, num_iterations, feature_fraction, num_leaves y min_data_in_leaf ya reescalado.
- `competencia_01/competencia_1/configs/base.yaml` · configuracion · YAML · 126 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/configs/base.yaml.txt) — Valores por defecto de todas las secciones: mes objetivo 202108, gap 2, clases positivas BAJA+1 y BAJA+2, 4 columnas en `drop_drift`, familias de variables activas, undersampling 0,1, parámetros fijos de LightGBM (max_bin 31, num_threads 8, deterministic), un conjunto manual de hiperparámetros, espacio de Optuna por defecto y etapas activas.
- `competencia_01/competencia_1/configs/exp/e034_comportamiento.yaml` · configuracion · YAML · 16 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/configs/exp/e034_comportamiento.yaml.txt) — Experimento del componente 2. Hereda de e032 y activa `fe.comportamiento`. El encabezado comentado lista las variables que se agregan y una observación sobre los clientes con payroll.
- `competencia_01/competencia_1/configs/exp/e033_montos_rank_cero_fijo.yaml` · configuracion · YAML · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/configs/exp/e033_montos_rank_cero_fijo.yaml.txt) — Experimento del componente 1. Hereda de e032 y cambia `fe.montos` a `rank_cero_fijo`. El encabezado comentado enuncia la hipótesis sobre el cambio de los montos nominales entre meses.
- `competencia_01/competencia_1/configs/exp/e032_expansiva_auc_topk.yaml` · configuracion · YAML · 55 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/configs/exp/e032_expansiva_auc_topk.yaml.txt) — Experimento del componente 0. Hereda de base.yaml y define 2 folds explícitos (train [202103] → 202105; train [202103, 202104] → 202106), meses finales 202103–202106, ventanas y tendencia de tamaño 2, undersampling 0,25, Optuna con 60 trials, objetivo auc y pruning, el espacio de búsqueda, final con top:12, 2 semillas y reescalado por filas, y cortes de 10.000 y 11.000. El encabezado comentado explica el diseño.
- `competencia_01/config/semillas.py` · principal · Python · 29 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/config/semillas.py.txt) — Lista de las 5 semillas del proyecto, de la que el pipeline toma las dos primeras para los modelos finales.
- `competencia_01/dmeyf/metrics.py` · principal · Python · 84 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/dmeyf/metrics.py.txt) — Cálculo de la ganancia: constantes, ganancia por umbral, curva de ganancia acumulada y máximo de la curva suavizada. Las constantes del archivo son 1.072.500 y 27.500; el README menciona +780.000 / −20.000.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### competencia_01/entrega.ipynb

Notebook con el mismo código que entrega.py, en 10 celdas (4 de texto y 6 de código). Según el README, el modo se elige en la segunda celda.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–15] Encabezado: título, nombre y sha256 del CSV entregado y tabla de los tres modos
#   (predecir, entrenar, completo) con su duración aproximada.
#%% celda 1 [texto]
# Entrega Competencia 01 — ens04_e032_e033_e034 (10500 envíos)

Este archivo (y su copia `entrega.ipynb`, que es el mismo código) reproduce **exactamente** el
CSV entregado: `20261011-091551_ens04_e032_e033_e034_e10500.csv` (sha256 `385da7093ab1e93b894016de3cb537460dc48ee0cc2befdce943ddbae850d5df`).

Parte del dataset de la competencia (`competencia_01_crudo.csv`, se descarga solo si falta) y
comprueba al final que el CSV generado tenga el mismo sha256. Elegí el modo en la celda
siguiente o con la variable de entorno `ENTREGA_MODO`:

| MODO | Qué hace | Tiempo aprox. |
|---|---|---|
| `predecir` (default) | datos → features → predice con los 72 modelos ya entrenados (`competencia_1/definitiva/componentes/*/modelos`) | ~1 h |
| `entrenar` | datos → features → reentrena los 72 modelos con los hiperparámetros guardados | ~4 h |
| `completo` | rehace TODO: la optimización de hiperparámetros con Optuna (180 trials), selección de los mejores y modelos finales | ~5 h |

# [Anotación · líneas 17–21] Lee el modo de la variable de entorno ENTREGA_MODO (por defecto `predecir`) y
#   verifica que sea uno de los tres valores admitidos.
#%% celda 2 [código]
import os

MODO = os.environ.get("ENTREGA_MODO", "predecir")  # "predecir" | "entrenar" | "completo"
assert MODO in ("predecir", "entrenar", "completo"), MODO

# [Anotación · líneas 23–40] Importa utilidades, pasa al directorio del archivo y lo agrega al path. Define
#   DMEYF_WORK y DMEYF_DB dentro de work/entrega, la URL pública del CSV crudo y su ruta local
#   datasets/raw/competencia_01_crudo.csv.
#%% celda 3 [código]
import importlib.metadata as metadata
import json
import shutil
import sys
import urllib.request
from pathlib import Path

# Carpeta de esta entrega (en un notebook __file__ no existe: se usa el directorio actual).
AQUI = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
os.chdir(AQUI)
sys.path.insert(0, str(AQUI))
# Todo lo que se genera va a work/entrega (y la base de Optuna también): nada se mezcla.
os.environ["DMEYF_WORK"] = str(AQUI / "work" / "entrega")
os.environ["DMEYF_DB"] = str(AQUI / "work" / "entrega" / "db" / "competencia_1.db")

URL_CRUDO = "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
CRUDO = AQUI / "datasets" / "raw" / "competencia_01_crudo.csv"

# [Anotación · líneas 42–55] Lee las versiones esperadas de competencia_1/definitiva/entrega.json y las
#   compara con las instaladas; imprime `DISTINTA` junto a las que no coinciden y continúa.
#%% celda 4 [texto]
## 1. Versiones de las librerías
La igualdad byte a byte requiere las mismas versiones con las que se generó la entrega
(`requirements-lock.txt` las instala). Si alguna difiere se avisa, pero se sigue.

#%% celda 5 [código]
info = json.loads((AQUI / "competencia_1" / "definitiva" / "entrega.json").read_text(encoding="utf-8"))
esperadas = info.get("versiones") or {}
print(f"python {sys.version.split()[0]} (esperado {esperadas.get('python')})")
for paquete, esperada in esperadas.items():
    if paquete == "python":
        continue
    instalada = metadata.version(paquete)
    print(f"{paquete:10s} {instalada:10s} esperado {esperada}", "" if instalada == esperada else "  <-- DISTINTA")

# [Anotación · líneas 57–70] Si el CSV crudo no existe, lo copia desde la ruta indicada en ENTREGA_CRUDO_LOCAL
#   o lo descarga de la URL; imprime su tamaño en MB.
#%% celda 6 [texto]
## 2. Dataset crudo
Se usa tal cual lo publica la cátedra (no se sube al repositorio). Si no está, se descarga.

#%% celda 7 [código]
if not CRUDO.exists():
    CRUDO.parent.mkdir(parents=True, exist_ok=True)
    local = os.environ.get("ENTREGA_CRUDO_LOCAL")  # atajo para no descargar de nuevo
    if local and Path(local).exists():
        shutil.copyfile(local, CRUDO)
    else:
        print("descargando", URL_CRUDO)
        urllib.request.urlretrieve(URL_CRUDO, CRUDO)
print(CRUDO, f"{CRUDO.stat().st_size / 1e6:.0f} MB")

# [Anotación · líneas 72–82] Importa el pipeline y llama a `reproducir_completo` (modo completo) o a
#   `reproducir` con `entrenar` verdadero o falso, siempre borrando antes el directorio de trabajo.
#%% celda 8 [texto]
## 3. Reproducción y comparación del sha256
La lógica vive en `competencia_1/` (el mismo pipeline con el que se hicieron los experimentos).

#%% celda 9 [código]
from competencia_1.pipeline.entrega import DIR_DEFINITIVA, reproducir, reproducir_completo

if MODO == "completo":
    ok = reproducir_completo(DIR_DEFINITIVA, limpiar=True)
else:
    ok = reproducir(DIR_DEFINITIVA, limpiar=True, entrenar=(MODO == "entrenar"))

# [Anotación · líneas 84–87] Imprime si el CSV coincide con la entrega y termina con código 1 si difiere.
#%% celda 10 [código]
print("RESULTADO:", "OK, el CSV coincide con la entrega" if ok else "DIFIERE")
if not ok:
    raise SystemExit(1)
```

### competencia_01/reproducir.sh

Script de shell para Linux o una VM de GCP: prepara el entorno virtual y ejecuta entrega.py con el modo recibido como argumento.

```
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–9] Comentarios de uso con los tres modos; activa `set -euo pipefail` y pasa a la
#   carpeta del script.
#!/usr/bin/env bash
# Reproduce la entrega (Linux / VM de GCP). Uso:
#   bash reproducir.sh              # predice con los modelos ya entrenados (~1 h)
#   bash reproducir.sh entrenar     # reentrena los modelos (~4 h)
#   bash reproducir.sh completo     # rehace también la optimización de Optuna (~5 h)
# Crea un entorno virtual .venv con las versiones exactas de requirements-lock.txt (Python 3.11),
# descarga el dataset si falta y termina con código 0 solo si el sha256 coincide.
set -euo pipefail
cd "$(dirname "$0")"

# [Anotación · líneas 11–17] Busca un intérprete de Python 3.11 o superior (variable PYTHON, o python3.11,
#   python3, python) y termina con un mensaje si no lo encuentra.
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  for c in python3.11 python3 python; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then PY="$c"; break; fi
  done
fi
[ -n "$PY" ] || { echo "Hace falta Python >= 3.11 (instalá python3.11 o exportá PYTHON=<ruta>)"; exit 1; }

# [Anotación · líneas 19–22] Crea .venv si no existe, actualiza pip, instala requirements-lock.txt y ejecuta
#   entrega.py con ENTREGA_MODO igual al primer argumento (por defecto `predecir`).
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements-lock.txt
ENTREGA_MODO="${1:-predecir}" exec .venv/bin/python entrega.py
```

### competencia_01/entrega.py

Punto de entrada en formato de celdas `# %%`: elige el modo, revisa versiones, obtiene el CSV crudo y llama a la reproducción del pipeline, que termina comparando el sha256 del CSV generado.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–15] Encabezado: título, nombre y sha256 del CSV entregado y tabla de los tres modos
#   (predecir, entrenar, completo) con su duración aproximada.
# %% [markdown]
# # Entrega Competencia 01 — ens04_e032_e033_e034 (10500 envíos)
#
# Este archivo (y su copia `entrega.ipynb`, que es el mismo código) reproduce **exactamente** el
# CSV entregado: `20261011-091551_ens04_e032_e033_e034_e10500.csv` (sha256 `385da7093ab1e93b894016de3cb537460dc48ee0cc2befdce943ddbae850d5df`).
#
# Parte del dataset de la competencia (`competencia_01_crudo.csv`, se descarga solo si falta) y
# comprueba al final que el CSV generado tenga el mismo sha256. Elegí el modo en la celda
# siguiente o con la variable de entorno `ENTREGA_MODO`:
#
# | MODO | Qué hace | Tiempo aprox. |
# |---|---|---|
# | `predecir` (default) | datos → features → predice con los 72 modelos ya entrenados (`competencia_1/definitiva/componentes/*/modelos`) | ~1 h |
# | `entrenar` | datos → features → reentrena los 72 modelos con los hiperparámetros guardados | ~4 h |
# | `completo` | rehace TODO: la optimización de hiperparámetros con Optuna (180 trials), selección de los mejores y modelos finales | ~5 h |

# [Anotación · líneas 17–21] Lee el modo de la variable de entorno ENTREGA_MODO (por defecto `predecir`) y
#   verifica que sea uno de los tres valores admitidos.
# %%
import os

MODO = os.environ.get("ENTREGA_MODO", "predecir")  # "predecir" | "entrenar" | "completo"
assert MODO in ("predecir", "entrenar", "completo"), MODO

# [Anotación · líneas 23–40] Importa utilidades, pasa al directorio del archivo y lo agrega al path. Define
#   DMEYF_WORK y DMEYF_DB dentro de work/entrega, la URL pública del CSV crudo y su ruta local
#   datasets/raw/competencia_01_crudo.csv.
# %%
import importlib.metadata as metadata
import json
import shutil
import sys
import urllib.request
from pathlib import Path

# Carpeta de esta entrega (en un notebook __file__ no existe: se usa el directorio actual).
AQUI = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
os.chdir(AQUI)
sys.path.insert(0, str(AQUI))
# Todo lo que se genera va a work/entrega (y la base de Optuna también): nada se mezcla.
os.environ["DMEYF_WORK"] = str(AQUI / "work" / "entrega")
os.environ["DMEYF_DB"] = str(AQUI / "work" / "entrega" / "db" / "competencia_1.db")

URL_CRUDO = "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv"
CRUDO = AQUI / "datasets" / "raw" / "competencia_01_crudo.csv"

# [Anotación · líneas 42–55] Lee las versiones esperadas de competencia_1/definitiva/entrega.json y las
#   compara con las instaladas; imprime `DISTINTA` junto a las que no coinciden y continúa.
# %% [markdown]
# ## 1. Versiones de las librerías
# La igualdad byte a byte requiere las mismas versiones con las que se generó la entrega
# (`requirements-lock.txt` las instala). Si alguna difiere se avisa, pero se sigue.

# %%
info = json.loads((AQUI / "competencia_1" / "definitiva" / "entrega.json").read_text(encoding="utf-8"))
esperadas = info.get("versiones") or {}
print(f"python {sys.version.split()[0]} (esperado {esperadas.get('python')})")
for paquete, esperada in esperadas.items():
    if paquete == "python":
        continue
    instalada = metadata.version(paquete)
    print(f"{paquete:10s} {instalada:10s} esperado {esperada}", "" if instalada == esperada else "  <-- DISTINTA")

# [Anotación · líneas 57–70] Si el CSV crudo no existe, lo copia desde la ruta indicada en ENTREGA_CRUDO_LOCAL
#   o lo descarga de la URL; imprime su tamaño en MB.
# %% [markdown]
# ## 2. Dataset crudo
# Se usa tal cual lo publica la cátedra (no se sube al repositorio). Si no está, se descarga.

# %%
if not CRUDO.exists():
    CRUDO.parent.mkdir(parents=True, exist_ok=True)
    local = os.environ.get("ENTREGA_CRUDO_LOCAL")  # atajo para no descargar de nuevo
    if local and Path(local).exists():
        shutil.copyfile(local, CRUDO)
    else:
        print("descargando", URL_CRUDO)
        urllib.request.urlretrieve(URL_CRUDO, CRUDO)
print(CRUDO, f"{CRUDO.stat().st_size / 1e6:.0f} MB")

# [Anotación · líneas 72–82] Importa el pipeline y llama a `reproducir_completo` (modo completo) o a
#   `reproducir` con `entrenar` verdadero o falso, siempre borrando antes el directorio de trabajo.
# %% [markdown]
# ## 3. Reproducción y comparación del sha256
# La lógica vive en `competencia_1/` (el mismo pipeline con el que se hicieron los experimentos).

# %%
from competencia_1.pipeline.entrega import DIR_DEFINITIVA, reproducir, reproducir_completo

if MODO == "completo":
    ok = reproducir_completo(DIR_DEFINITIVA, limpiar=True)
else:
    ok = reproducir(DIR_DEFINITIVA, limpiar=True, entrenar=(MODO == "entrenar"))

# [Anotación · líneas 84–87] Imprime si el CSV coincide con la entrega y termina con código 1 si difiere.
# %%
print("RESULTADO:", "OK, el CSV coincide con la entrega" if ok else "DIFIERE")
if not ok:
    raise SystemExit(1)
```

### competencia_01/competencia_1/main.py

Orquestador del pipeline: carga la configuración, abre un run y ejecuta en orden las etapas activas.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–36] Docstring con ejemplos de uso; importa la función de cada etapa y reconfigura
#   stdout y stderr a UTF-8.
"""Punto de entrada: orquesta las etapas del pipeline de la Primera Competencia.

    python -m competencia_1.main --config competencia_1/configs/exp/e001_baseline_catedra.yaml
    python -m competencia_1.main --config <exp>.yaml --set final.n_semillas=20 --set etapas.optuna=true
    python -m competencia_1.main --reproducir work/competencia_1/runs/<run_id>

Este archivo solo orquesta: la lógica vive en competencia_1/pipeline/.
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml

from competencia_1.pipeline import config as cfgmod
from competencia_1.pipeline.ablacion import etapa_ablacion
from competencia_1.pipeline.canaritos import etapa_canaritos
from competencia_1.pipeline.datos import etapa_datos
from competencia_1.pipeline.estabilidad import etapa_estabilidad
from competencia_1.pipeline.evaluacion import etapa_validacion
from competencia_1.pipeline.features import etapa_features
from competencia_1.pipeline.final import etapa_final
from competencia_1.pipeline.optimizacion import etapa_optuna
from competencia_1.pipeline.salida import etapa_salida
from competencia_1.pipeline.tracking import Run

log = logging.getLogger("competencia_1.main")

# La consola de Windows usa cp1252 por defecto y rompe las tildes de los logs.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# [Anotación · líneas 38–69] Define el orden de las 9 etapas (datos, features, optuna, estabilidad, ablacion,
#   canaritos, validacion, final, salida) y el diccionario que asocia cada nombre con su función.
ORDEN_ETAPAS = [
    "datos",
    "features",
    "optuna",
    "estabilidad",
    "ablacion",
    "canaritos",
    "validacion",
    "final",
    "salida",
]


def _etapa_pendiente(nombre: str, cfg: cfgmod.Config, run: Run) -> None:
    # Etapas todavía sin implementar (ver plan, sección 11).
    raise NotImplementedError(f"etapa '{nombre}' todavía no implementada")


# nombre de etapa -> callable(cfg, run). Cada módulo nuevo se registra acá.
ETAPAS = {
    nombre: (lambda cfg, run, n=nombre: _etapa_pendiente(n, cfg, run))
    for nombre in ORDEN_ETAPAS
}
ETAPAS["datos"] = etapa_datos
ETAPAS["features"] = etapa_features
ETAPAS["optuna"] = etapa_optuna
ETAPAS["estabilidad"] = etapa_estabilidad
ETAPAS["ablacion"] = etapa_ablacion
ETAPAS["canaritos"] = etapa_canaritos
ETAPAS["validacion"] = etapa_validacion
ETAPAS["final"] = etapa_final
ETAPAS["salida"] = etapa_salida


# [Anotación · líneas 72–87] Argumentos de línea de comandos: `--config` o `--reproducir` (excluyentes),
#   `--set CLAVE=VALOR` repetible y `--etapas`.
def parsear_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--config", type=Path, help="YAML del experimento (hereda de base.yaml)"
    )
    g.add_argument("--reproducir", type=Path, help="carpeta de un run previo")
    ap.add_argument(
        "--set", dest="overrides", action="append", default=[], metavar="CLAVE=VALOR"
    )
    ap.add_argument(
        "--etapas", help="lista separada por comas; reemplaza lo de etapas.* del config"
    )
    return ap.parse_args(argv)


# [Anotación · líneas 90–107] Carga la configuración desde el YAML (con herencia y overrides) o desde el
#   config_resuelta.yaml de un run previo; si se pasó `--etapas`, reemplaza la sección de etapas activas.
def main(argv: list[str] | None = None) -> int:
    args = parsear_args(argv)

    if args.reproducir:
        resuelta = args.reproducir / "config_resuelta.yaml"
        with open(resuelta, encoding="utf-8") as f:
            d = cfgmod.aplicar_overrides(yaml.safe_load(f), args.overrides)
        cfg = cfgmod.desde_dict(d)
    else:
        cfg, d = cfgmod.cargar_config(args.config, args.overrides)

    if args.etapas is not None:
        pedidas = [e.strip() for e in args.etapas.split(",") if e.strip()]
        desconocidas = set(pedidas) - set(ORDEN_ETAPAS)
        if desconocidas:
            raise SystemExit(f"etapas desconocidas: {sorted(desconocidas)}")
        d["etapas"] = {e: e in pedidas for e in ORDEN_ETAPAS}
        cfg = cfgmod.desde_dict(d)

# [Anotación · líneas 109–133] Abre un `Run`, registra el mes objetivo, las semillas, los folds y los meses
#   finales, y ejecuta en orden las etapas activas marcando cada una como `ok` en meta.json.
    with Run(cfg.experimento, d) as run:
        run.registrar(
            target=cfg.periodos.target,
            semillas=cfgmod.semillas_finales(cfg) if cfg.etapas.final else None,
            periodos={
                "folds": [
                    {"train": list(f.train), "valid": f.valid}
                    for f in cfgmod.folds(cfg)
                ],
                "meses_final": cfgmod.meses_final(cfg),
            },
        )
        for nombre in ORDEN_ETAPAS:
            if not getattr(cfg.etapas, nombre):
                log.info("etapa %s: desactivada", nombre)
                continue
            log.info("etapa %s: inicio", nombre)
            ETAPAS[nombre](cfg, run)
            run.meta["etapas"][nombre] = "ok"
            run.guardar_meta()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### competencia_01/competencia_1/pipeline/datos.py

Etapa datos: lee el CSV con DuckDB, reconstruye la clase ternaria si se pide, escribe el parquet base en caché y valida esquema, unicidad, clases y períodos.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–24] Docstring con las decisiones de tipos y caché; importaciones; ruta de
#   `cache/base.parquet`, tipos forzados (numero_de_cliente BIGINT, foto_mes INTEGER) y las tres clases válidas.
"""Etapa datos: CSV procesado -> parquet tipado en caché + validaciones.

Decisiones:
- `numero_de_cliente` se fuerza a BIGINT y `foto_mes` a INTEGER desde la lectura,
  para que los IDs nunca pasen por float (riesgo de notación científica).
- La caché se regenera solo si el origen es más nuevo (o si se reconstruye el target).
- Un mes tiene "target completo" si ninguna de sus filas tiene clase_ternaria NULL
  (hoy: 202103-202106; 202107 solo conoce BAJA+1 y 202108 es el mes a predecir).
"""

import logging
from pathlib import Path

import duckdb

from competencia_1.pipeline import config as cfgmod
from competencia_1.pipeline import periodos
from competencia_1.pipeline.tracking import WORK, Run, ruta_relativa

log = logging.getLogger("competencia_1.datos")

CACHE_BASE = WORK / "cache" / "base.parquet"
TIPOS_FORZADOS = {"numero_de_cliente": "BIGINT", "foto_mes": "INTEGER"}
CLASES = {"CONTINUA", "BAJA+1", "BAJA+2"}

# [Anotación · líneas 26–53] SQL_TARGET: arma el panel denso cliente × mes, calcula con `lead` si el cliente
#   está presente 1 y 2 meses después y asigna CONTINUA (presente en t+2), BAJA+2 (presente en t+1 y ausente en
#   t+2), BAJA+1 (ausente en t+1) o nulo; conserva sólo las filas reales.
# Portado de exp/z101_target_sql/target_sql.py (upstream monday/z101_target_sql,
# commit 21402a7 de dmecoyfin/dmeyf2026). Panel denso cliente x mes + lead.
SQL_TARGET = """
    with periodos as (
        select distinct foto_mes from crudo
    ), clientes as (
        select distinct numero_de_cliente from crudo
    ), todo as (
        select numero_de_cliente, foto_mes from clientes cross join periodos
    ), con_target as (
        select
            c.*
            , if(c.numero_de_cliente is null, 0, 1) as mes_0
            , lead(mes_0, 1) over (partition by t.numero_de_cliente order by foto_mes) as mes_1
            , lead(mes_0, 2) over (partition by t.numero_de_cliente order by foto_mes) as mes_2
            , case
                when mes_2 = 1 then 'CONTINUA'
                when mes_1 = 1 and mes_2 = 0 then 'BAJA+2'
                when mes_1 = 0 then 'BAJA+1'
                else null
              end as clase_ternaria
        from todo t
        left join crudo c using (numero_de_cliente, foto_mes)
    )
    select * exclude (mes_0, mes_1, mes_2)
    from con_target
    where mes_0 = 1
"""


# [Anotación · líneas 56–63] Funciones auxiliares: ruta absoluta respecto de la raíz y expresión `read_csv`
#   con muestreo completo de tipos y los dos tipos forzados.
def _ruta(rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else cfgmod.RAIZ / p


def _leer_csv_sql(path: Path) -> str:
    tipos = ", ".join(f"'{k}': '{v}'" for k, v in TIPOS_FORZADOS.items())
    return f"read_csv('{path.as_posix()}', sample_size = -1, types = {{{tipos}}})"


# [Anotación · líneas 66–93] `construir_cache`: elige el CSV crudo o el procesado según `reconstruir_target`;
#   si la caché es más nueva que el origen no la rehace; si no, escribe el parquet con compresión zstd,
#   aplicando SQL_TARGET cuando se reconstruye la clase.
def construir_cache(cfg: cfgmod.Config, destino: Path = CACHE_BASE) -> Path:
    """Escribe el parquet base tipado (si hace falta) y devuelve su ruta."""
    d = cfg.datos
    origen = _ruta(d.csv_crudo if d.reconstruir_target else d.csv_procesado)
    if not origen.exists():
        raise FileNotFoundError(f"no existe el origen de datos: {origen}")
    if destino.exists() and destino.stat().st_mtime >= origen.stat().st_mtime:
        log.info("caché vigente, no se regenera: %s", destino)
        return destino

    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".tmp.parquet")
    con = duckdb.connect()
    try:
        if d.reconstruir_target:
            log.info("reconstruyendo clase_ternaria desde %s", origen)
            con.execute(f"create table crudo as select * from {_leer_csv_sql(origen)}")
            query = SQL_TARGET
        else:
            query = f"select * from {_leer_csv_sql(origen)}"
        con.execute(
            f"copy ({query}) to '{tmp.as_posix()}' (format parquet, compression zstd)"
        )
    finally:
        con.close()
    tmp.replace(destino)
    log.info("caché escrita: %s (%.0f MB)", destino, destino.stat().st_size / 1e6)
    return destino


# [Anotación · líneas 96–124] `resumen_meses`: por mes cuenta filas, clientes distintos y filas de cada clase,
#   incluidas las que no tienen clase.
def resumen_meses(parquet: Path) -> list[dict]:
    """Por mes: filas, clientes y conteo por clase (incluye NULL)."""
    con = duckdb.connect()
    try:
        filas = con.execute(
            f"""
            select foto_mes
                 , count(*) as filas
                 , count(distinct numero_de_cliente) as clientes
                 , count(*) filter (clase_ternaria = 'CONTINUA') as continua
                 , count(*) filter (clase_ternaria = 'BAJA+1') as baja1
                 , count(*) filter (clase_ternaria = 'BAJA+2') as baja2
                 , count(*) filter (clase_ternaria is null) as sin_target
            from read_parquet('{parquet.as_posix()}')
            group by 1 order by 1
            """
        ).fetchall()
        cols = [
            "foto_mes",
            "filas",
            "clientes",
            "continua",
            "baja1",
            "baja2",
            "sin_target",
        ]
        return [dict(zip(cols, f, strict=True)) for f in filas]
    finally:
        con.close()


# [Anotación · líneas 127–167] `validar_base`: verifica los tipos de las claves, la presencia de
#   clase_ternaria, la unicidad de (cliente, mes), que las clases sean las esperadas y que no haya nulos en las
#   claves.
def validar_base(parquet: Path) -> list[dict]:
    """Chequea esquema, unicidad (cliente, mes) y clases válidas. Devuelve el resumen."""
    con = duckdb.connect()
    try:
        esquema = {
            r[0]: r[1]
            for r in con.execute(
                f"describe select * from read_parquet('{parquet.as_posix()}')"
            ).fetchall()
        }
        for col, tipo in TIPOS_FORZADOS.items():
            if col not in esquema:
                raise ValueError(f"falta la columna obligatoria: {col}")
            if esquema[col] != tipo:
                raise ValueError(f"{col} debe ser {tipo}, es {esquema[col]}")
        if "clase_ternaria" not in esquema:
            raise ValueError("falta la columna clase_ternaria")
        n, n_unicos = con.execute(
            f"""select count(*), count(distinct (numero_de_cliente, foto_mes))
                from read_parquet('{parquet.as_posix()}')"""
        ).fetchone()
        if n != n_unicos:
            raise ValueError(f"hay {n - n_unicos:,} duplicados de (cliente, mes)")
        clases = {
            r[0]
            for r in con.execute(
                f"select distinct clase_ternaria from read_parquet('{parquet.as_posix()}')"
            ).fetchall()
        }
        raros = clases - CLASES - {None}
        if raros:
            raise ValueError(f"clase_ternaria con valores inesperados: {sorted(raros)}")
        nulos_id = con.execute(
            f"""select count(*) from read_parquet('{parquet.as_posix()}')
                where numero_de_cliente is null or foto_mes is null"""
        ).fetchone()[0]
        if nulos_id:
            raise ValueError(f"{nulos_id:,} filas con cliente o mes nulo")
    finally:
        con.close()
    return resumen_meses(parquet)


# [Anotación · líneas 170–189] `meses_con_target_completo` devuelve los meses sin filas con clase nula;
#   `validar_periodos` exige que el mes objetivo exista y que los meses de cada fold y los finales tengan la
#   clase completa, y avisa si el mes objetivo ya tiene clase.
def meses_con_target_completo(resumen: list[dict]) -> set[int]:
    return {r["foto_mes"] for r in resumen if r["sin_target"] == 0}


def validar_periodos(cfg: cfgmod.Config, resumen: list[dict]) -> None:
    """Cruza los períodos del config con lo que realmente hay en los datos."""
    presentes = {r["foto_mes"] for r in resumen}
    completos = meses_con_target_completo(resumen)
    objetivo = cfg.periodos.target
    if objetivo not in presentes:
        raise ValueError(f"el target_period {objetivo} no existe en los datos")
    for i, f in enumerate(cfgmod.folds(cfg)):
        periodos.validar_target_completo(list(f.train), completos, f"fold {i} train")
        periodos.validar_target_completo([f.valid], completos, f"fold {i} valid")
    periodos.validar_target_completo(cfgmod.meses_final(cfg), completos, "final")
    if objetivo in completos:
        log.warning(
            "el target_period %s ya tiene target conocido: se está prediciendo un mes etiquetado",
            objetivo,
        )


# [Anotación · líneas 192–212] `etapa_datos`: construye la caché, la valida, escribe en el log el conteo por
#   mes y guarda el resumen en meta.json.
def etapa_datos(cfg: cfgmod.Config, run: Run) -> None:
    parquet = construir_cache(cfg)
    resumen = validar_base(parquet)
    for r in resumen:
        log.info(
            "mes %s: %s filas | CONTINUA=%s BAJA+1=%s BAJA+2=%s sin_target=%s",
            r["foto_mes"],
            r["filas"],
            r["continua"],
            r["baja1"],
            r["baja2"],
            r["sin_target"],
        )
    validar_periodos(cfg, resumen)
    run.registrar(
        datos={
            "parquet": ruta_relativa(parquet),
            "meses": resumen,
            "meses_target_completo": sorted(meses_con_target_completo(resumen)),
        }
    )
```

### competencia_01/competencia_1/pipeline/final.py

Etapa final: resuelve los conjuntos de hiperparámetros y las semillas, entrena (o carga) un modelo por combinación, predice el mes objetivo y promedia las probabilidades.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–43] Docstring que describe el semillerío, el ensamble de conjuntos de hiperparámetros
#   y el modo de sólo predecir con modelos guardados; importaciones.
"""Etapa final (semillerío): entrena N modelos con los mismos params/features y distinta semilla.

Cada modelo predice el mes objetivo y deja `probas/s<seed>.parquet`; si hay 2 o más
semillas también `probas/promedio.parquet` (promedio de probabilidades).
Entrena SIN undersampling y reescala min_data_in_leaf si se ajustó con undersampling.

Ensamble de hiperparámetros: con `final.params_desde: top:<k>` (los k mejores trials del
estudio) o un json con la clave `ensamble`, se entrena cada conjunto × cada semilla. Los
modelos sueltos quedan en `probas/ensamble/<conjunto>_s<seed>.parquet` y solo el
`promedio.parquet` queda en `probas/` (de ahí sale el CSV).

Con `final.modelos_desde: <carpeta>` no se entrena: se cargan los modelos ya entrenados
(`<conjunto>_s<semilla>.txt`, en el mismo orden que el entrenamiento) y solo se predice. Los
modelos guardados predicen idéntico bit a bit, así que el promedio y el CSV no cambian.
"""

import logging
from pathlib import Path

import lightgbm as lgb
import numpy as np
import polars as pl

from competencia_1.pipeline import config as cfgmod
from competencia_1.pipeline.dataset import cargar_particion, contar_filas, pesos_filas
from competencia_1.pipeline.features import columnas_seleccionadas, construir_features
from competencia_1.pipeline.modelo import (
    cargar_json_params,
    entrenar_lgbm,
    escalar_min_data,
    escalar_min_data_factor,
    importancias,
    nombre_estudio,
    params_lgbm,
    peso_baja1,
    predecir,
    resolver_params,
    ruta_params,
)
from competencia_1.pipeline.optimizacion import DB_PATH, cargar_estudio, top_trials
from competencia_1.pipeline.tracking import Run

log = logging.getLogger("competencia_1.final")


# [Anotación · líneas 46–57] `resolver_conjunto`: lista de (etiqueta, hiperparámetros): los k trials de mayor
#   valor del estudio (`top:<k>`, etiqueta t<número>), los conjuntos de un JSON con la clave `ensamble`, o un
#   único conjunto.
def resolver_conjunto(cfg: cfgmod.Config, fe_hash: str) -> list[tuple[str, dict]]:
    """[(etiqueta, params)] a entrenar. Un solo conjunto => etiqueta vacía (flujo de siempre)."""
    origen = cfg.final.params_desde
    if origen.startswith("top:"):
        estudio = cargar_estudio(nombre_estudio(cfg, fe_hash), DB_PATH)
        trials = top_trials(estudio, int(origen[4:]))
        return [(f"t{t.number}", {**cfg.lgbm.manual, **t.params}) for t in trials]
    if origen.startswith("archivo:"):
        data = cargar_json_params(cfg, ruta_params(cfg, fe_hash), fe_hash)
        if "ensamble" in data:
            return [(m["etiqueta"], dict(m["params"])) for m in data["ensamble"]]
    return [("", resolver_params(cfg, fe_hash))]


# [Anotación · líneas 60–64] `_factor_filas`: filas de los meses finales dividido por filas de train del
#   último fold con su undersampling.
def _factor_filas(cfg: cfgmod.Config, parquet: Path, meses_final: list[int]) -> float:
    """Filas del final / filas de train del último fold (con su undersampling)."""
    ultimo = cfgmod.folds(cfg)[-1]
    filas_fold = contar_filas(parquet, list(ultimo.train), cfg.dataset.undersampling)
    return contar_filas(parquet, meses_final) / filas_fold


# [Anotación · líneas 67–79] `_cargar_modelo`: carga un Booster desde un archivo .txt y verifica que su
#   cantidad de features coincida con la del FE actual.
def _cargar_modelo(ruta: Path, n_features: int) -> lgb.Booster:
    if not ruta.exists():
        raise FileNotFoundError(
            f"falta el modelo {ruta}: ¿los conjuntos y semillas del config coinciden con los "
            "modelos guardados?"
        )
    modelo = lgb.Booster(model_file=str(ruta))
    if modelo.num_feature() != n_features:
        raise ValueError(
            f"{ruta.name}: entrenado con {modelo.num_feature()} features pero el FE actual "
            f"da {n_features}"
        )
    return modelo


# [Anotación · líneas 82–103] `etapa_final` (inicio): obtiene features, conjuntos, semillas y meses; reescala
#   min_data_in_leaf por el factor de filas (`filas`) o por el undersampling (true), o no lo toca (false, el
#   valor de los config.yaml congelados).
def etapa_final(cfg: cfgmod.Config, run: Run) -> None:
    parquet, fe_hash = construir_features(cfg)
    features = columnas_seleccionadas(cfg, parquet)
    conjuntos = resolver_conjunto(cfg, fe_hash)
    semillas = cfgmod.semillas_finales(cfg)
    meses = cfgmod.meses_final(cfg)
    if cfg.final.reescalar_min_data == "filas":
        factor = _factor_filas(cfg, parquet, meses)
        log.info("min_data_in_leaf x %.3f (filas del final / filas de train)", factor)
        conjuntos = [(e, escalar_min_data_factor(p, factor)) for e, p in conjuntos]
    elif cfg.final.reescalar_min_data:
        conjuntos = [
            (e, escalar_min_data(p, cfg.dataset.undersampling)) for e, p in conjuntos
        ]
    ensamble = len(conjuntos) > 1
    log.info(
        "final: meses=%s semillas=%s conjuntos=%d params=%s",
        meses,
        semillas,
        len(conjuntos),
        conjuntos[0][1] if not ensamble else "(ver meta.json)",
    )

# [Anotación · líneas 105–133] Carga la partición del mes objetivo sin clase; si hay `modelos_desde` no carga
#   train, y si no carga los meses finales sin undersampling; crea las carpetas de probabilidades y de modelos.
    cargar = cfg.final.modelos_desde is not None
    objetivo = cargar_particion(
        parquet, features, [cfg.periodos.target], cfg.target.positivos, con_target=False
    )
    if cargar:
        origen = Path(cfg.final.modelos_desde)
        origen = origen if origen.is_absolute() else cfgmod.RAIZ / origen
        train = None
        log.info(
            "modelos ya entrenados en %s: no se entrena | a predecir: %d clientes",
            origen,
            len(objetivo),
        )
    else:
        train = cargar_particion(parquet, features, meses, cfg.target.positivos)
        log.info(
            "train: %d filas, %d positivos (%.2f%%) | a predecir: %d clientes",
            len(train),
            train.y.sum(),
            100 * train.y.mean(),
            len(objetivo),
        )

    dir_probas, dir_modelos = run.dir / "probas", run.dir / "modelos"
    dir_probas.mkdir(exist_ok=True)
    if not cargar:
        dir_modelos.mkdir(exist_ok=True)
    dir_sueltas = dir_probas / "ensamble" if ensamble else dir_probas
    dir_sueltas.mkdir(exist_ok=True)

# [Anotación · líneas 135–165] Para cada conjunto × semilla: carga el modelo `<etiqueta>_s<semilla>.txt` o lo
#   entrena, predice el mes objetivo, guarda las probabilidades en parquet y, si entrenó, guarda el modelo y las
#   importancias del primero.
    todas = []
    total = len(conjuntos) * len(semillas)
    for etiqueta, params in conjuntos:
        for seed in semillas:
            nombre = f"{etiqueta}_s{seed}" if etiqueta else f"s{seed}"
            if cargar:
                modelo = _cargar_modelo(origen / f"{nombre}.txt", len(features))
            else:
                p, n_iter = params_lgbm(cfg, params, seed)
                w = pesos_filas(train, peso_baja1(cfg, params))
                modelo = entrenar_lgbm(train.X, train.y, features, p, n_iter, w)
            prob = predecir(modelo, objetivo.X)
            todas.append(prob)
            df = pl.DataFrame({"numero_de_cliente": objetivo.ids, "prob": prob})
            destino = dir_sueltas / f"{nombre}.parquet"
            df.write_parquet(destino)
            if cargar:
                run.registrar_archivo(destino)
            else:
                modelo.save_model(str(dir_modelos / f"{nombre}.txt"))
                if len(todas) == 1:
                    importancias(modelo).write_csv(run.dir / "importancias.csv")
                for f in (destino, dir_modelos / f"{nombre}.txt"):
                    run.registrar_archivo(f)
            log.info(
                "modelo %s (%d/%d): prob media=%.5f",
                nombre,
                len(todas),
                total,
                prob.mean(),
            )

# [Anotación · líneas 167–186] Con 2 o más modelos escribe `promedio.parquet` con la media de las
#   probabilidades; registra en meta.json los hiperparámetros finales, la cantidad de features y los meses.
    if len(todas) >= 2:
        promedio = pl.DataFrame(
            {"numero_de_cliente": objetivo.ids, "prob": np.mean(todas, axis=0)}
        )
        destino = dir_probas / "promedio.parquet"
        promedio.write_parquet(destino)
        run.registrar_archivo(destino)

    run.registrar(
        modelo={
            "params_final": (
                [{"etiqueta": e, "params": p} for e, p in conjuntos]
                if ensamble
                else conjuntos[0][1]
            ),
            "n_features": len(features),
            "meses_final": meses,
            "modelos_desde": cfg.final.modelos_desde,
        }
    )
```

### competencia_01/competencia_1/pipeline/semillas.py

Genera y valida semillas: primos entre 100003 y 999983, empezando por las 5 de config/semillas.py.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Importa SEMILLAS de config/semillas.py, fija el rango [100003, 999983] y define un
#   test de primalidad por división.
"""Semillas reproducibles: primos en [100003, 999983] derivados de la maestra."""

import random

from config.semillas import SEMILLAS

_MIN, _MAX = 100003, 999983


def _es_primo(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


# [Anotación · líneas 23–28] `validar_semilla_curso`: exige un entero primo dentro del rango.
def validar_semilla_curso(semilla: int, etiqueta: str = "semilla") -> None:
    """La cátedra exige primos entre 100003 y 999983."""
    if not isinstance(semilla, int) or isinstance(semilla, bool):
        raise TypeError(f"{etiqueta}: debe ser un entero, es {semilla!r}")
    if not _MIN <= semilla <= _MAX or not _es_primo(semilla):
        raise ValueError(f"{etiqueta}={semilla}: debe ser primo entre {_MIN} y {_MAX}")


# [Anotación · líneas 31–45] `generar_semillas`: devuelve las primeras `n` de las 5 semillas fijas; si n es
#   mayor que 5 completa con primos sorteados con `random.Random(maestra)`.
def generar_semillas(maestra: int, n: int) -> list[int]:
    """Devuelve `n` primos distintos; los primeros son las SEMILLAS del curso.

    Las 5 semillas oficiales van primero (en orden) y el resto se sortea de
    forma determinística a partir de `maestra`, así un semillerío de 20 modelos
    extiende al de 5 sin cambiar sus primeros modelos.
    """
    if n < 1:
        raise ValueError("n debe ser >= 1")
    fijas = list(SEMILLAS)
    if n <= len(fijas):
        return fijas[:n]
    primos = [p for p in range(_MIN, _MAX + 1) if _es_primo(p) and p not in fijas]
    extra = random.Random(maestra).sample(primos, n - len(fijas))
    return fijas + extra
```

### competencia_01/competencia_1/pipeline/salida.py

Etapa salida: convierte probabilidades en CSV de entrega (sólo IDs, sin encabezado), valida el archivo escrito y mide la coincidencia entre modelos.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–26] Docstring con las garantías del formato; importaciones; expresión regular de sólo
#   dígitos y redondeo de envíos a múltiplos de 500.
"""Etapa salida: probabilidades -> CSV de entrega (solo IDs enteros, sin header).

Garantías del formato:
- `numero_de_cliente` viaja como Int64 de punta a punta (nunca float/pandas).
- Una línea por cliente, solo dígitos: se relee el archivo escrito como TEXTO y
  cada línea debe cumplir ^\\d+$ (descarta 4.8e+07, decimales, comillas, signos).
- Si alguna validación falla, el archivo se borra y se lanza la excepción.
"""

import itertools
import logging
import re
import statistics
from pathlib import Path

import duckdb
import polars as pl

from competencia_1.pipeline import config as cfgmod
from competencia_1.pipeline.datos import CACHE_BASE
from competencia_1.pipeline.tracking import Run

log = logging.getLogger("competencia_1.salida")

_SOLO_DIGITOS = re.compile(r"^\d+$")
REDONDEO_ENVIOS = 500


# [Anotación · líneas 29–44] `validar_probas`: exige las columnas numero_de_cliente (Int64, sin nulos ni
#   repetidos) y prob (entre 0 y 1, sin NaN).
def validar_probas(probas: pl.DataFrame) -> None:
    """Contrato de entrada: numero_de_cliente Int64 único y sin nulos; prob en [0, 1]."""
    if set(probas.columns) != {"numero_de_cliente", "prob"}:
        raise ValueError(
            f"columnas esperadas (numero_de_cliente, prob), llegaron {probas.columns}"
        )
    if probas.schema["numero_de_cliente"] != pl.Int64:
        raise TypeError(
            f"numero_de_cliente debe ser Int64, es {probas.schema['numero_de_cliente']}"
        )
    if probas["numero_de_cliente"].null_count() or probas["prob"].null_count():
        raise ValueError("hay nulos en numero_de_cliente o prob")
    if probas["numero_de_cliente"].n_unique() != probas.height:
        raise ValueError("numero_de_cliente duplicado en las probabilidades")
    if probas["prob"].is_nan().any() or not probas["prob"].is_between(0, 1).all():
        raise ValueError("prob fuera de [0, 1] o NaN")


# [Anotación · líneas 47–55] `seleccionar_top`: ordena por prob descendente y numero_de_cliente ascendente y
#   toma los primeros `envios`.
def seleccionar_top(probas: pl.DataFrame, envios: int) -> pl.Series:
    """IDs de los `envios` clientes con mayor prob. Desempata por ID: determinístico."""
    if not 0 < envios <= probas.height:
        raise ValueError(f"envios={envios} fuera de (0, {probas.height}]")
    return (
        probas.sort(["prob", "numero_de_cliente"], descending=[True, False])
        .head(envios)
        .get_column("numero_de_cliente")
    )


# [Anotación · líneas 58–78] `validar_csv`: relee el archivo como texto y exige que no haya retornos de carro,
#   que cada línea sea sólo dígitos, la cantidad de líneas esperada, que no haya repetidos y, si se pasa el
#   conjunto, que los IDs sean del mes objetivo.
def validar_csv(path: Path, envios: int, ids_validos: set[int] | None = None) -> None:
    """Relee `path` como texto y verifica el formato exigido por la competencia."""
    texto = path.read_bytes().decode("utf-8")
    if "\r" in texto:
        raise ValueError(f"{path.name}: contiene \\r (se esperan fines de línea \\n)")
    lineas = texto.split("\n")
    if lineas and lineas[-1] == "":
        lineas.pop()
    malas = [(i + 1, x) for i, x in enumerate(lineas) if not _SOLO_DIGITOS.match(x)]
    if malas:
        raise ValueError(f"{path.name}: líneas que no son enteros planos: {malas[:5]}")
    if len(lineas) != envios:
        raise ValueError(f"{path.name}: {len(lineas)} líneas, se esperaban {envios}")
    if len(set(lineas)) != len(lineas):
        raise ValueError(f"{path.name}: IDs duplicados")
    if ids_validos is not None:
        fuera = [x for x in lineas if int(x) not in ids_validos]
        if fuera:
            raise ValueError(
                f"{path.name}: {len(fuera)} IDs no pertenecen al período objetivo: {fuera[:5]}"
            )


# [Anotación · líneas 81–97] `escribir_csv_ids`: valida las probabilidades, selecciona el top, escribe el CSV
#   sin encabezado y lo borra si no pasa la validación.
def escribir_csv_ids(
    probas: pl.DataFrame,
    envios: int,
    path: Path,
    ids_validos: set[int] | None = None,
) -> Path:
    """Escribe y valida un CSV de entrega. Borra el archivo si no pasa la validación."""
    validar_probas(probas)
    ids = seleccionar_top(probas, envios)
    path.parent.mkdir(parents=True, exist_ok=True)
    ids.to_frame().write_csv(path, include_header=False, line_terminator="\n")
    try:
        validar_csv(path, envios, ids_validos)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


# [Anotación · líneas 100–123] `resolver_envios`: un entero, una lista, o `auto` (mediana de los envíos del
#   máximo en validación, escalada por clientes del mes objetivo / clientes de validación y redondeada a
#   múltiplos de 500).
def resolver_envios(
    spec: str | int | list[int],
    envios_optimos_valid: list[int] | None = None,
    n_target: int | None = None,
    n_valid: int | None = None,
) -> list[int]:
    """Convierte `salida.envios` en una lista concreta de cortes.

    auto: mediana de los envíos óptimos de validación, escalada por la razón de
    clientes (target/valid) y redondeada a múltiplos de 500.
    """
    if isinstance(spec, int):
        return [spec]
    if isinstance(spec, list):
        return sorted(set(spec))
    if spec != "auto":
        raise ValueError(f"salida.envios inválido: {spec!r}")
    if not envios_optimos_valid or not n_target or not n_valid:
        raise ValueError(
            "salida.envios=auto requiere envíos óptimos de validación (corré optuna/"
            "evaluación antes) o indicá un número / lista de envíos"
        )
    escalado = statistics.median(envios_optimos_valid) * n_target / n_valid
    return [max(REDONDEO_ENVIOS, round(escalado / REDONDEO_ENVIOS) * REDONDEO_ENVIOS)]


# [Anotación · líneas 126–152] `ids_del_periodo` lee del parquet base los clientes del mes; `generar_submits`
#   escribe un CSV `<prefijo>_<modelo>_e<envios>.csv` por modelo y corte.
def ids_del_periodo(parquet: Path, foto_mes: int) -> set[int]:
    con = duckdb.connect()
    try:
        filas = con.execute(
            f"select numero_de_cliente from read_parquet('{parquet.as_posix()}') where foto_mes = ?",
            [foto_mes],
        ).fetchall()
    finally:
        con.close()
    return {f[0] for f in filas}


def generar_submits(
    probas_por_modelo: dict[str, pl.DataFrame],
    envios: list[int],
    destino: Path,
    prefijo: str,
    ids_validos: set[int] | None = None,
) -> list[Path]:
    """Un CSV por (modelo, corte): `<prefijo>_<modelo>_e<envios>.csv`."""
    generados = []
    for modelo, probas in probas_por_modelo.items():
        for n in envios:
            path = destino / f"{prefijo}_{modelo}_e{n}.csv"
            generados.append(escribir_csv_ids(probas, n, path, ids_validos))
            log.info("submit escrito: %s", path.name)
    return generados


# [Anotación · líneas 155–183] `resumen_semillerio`: índice de Jaccard del top-N entre pares de modelos y de
#   cada uno contra el promedio, para cada corte.
def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b)


def resumen_semillerio(
    probas_por_modelo: dict[str, pl.DataFrame], envios: list[int]
) -> dict:
    """Cuánto coinciden los clientes elegidos por los distintos modelos en cada corte.

    Jaccard del top-N entre pares de semillas y de cada semilla contra el promedio:
    cerca de 1 las semillas casi no aportan diversidad; bajo, el promedio sí estabiliza.
    """
    semillas = {k: v for k, v in probas_por_modelo.items() if k != "promedio"}
    resumen = {}
    for n in envios:
        tops = {k: set(seleccionar_top(v, n).to_list()) for k, v in semillas.items()}
        pares = [_jaccard(a, b) for a, b in itertools.combinations(tops.values(), 2)]
        r = {
            "n_modelos": len(semillas),
            "jaccard_medio_pares": statistics.fmean(pares) if pares else None,
            "jaccard_min_pares": min(pares) if pares else None,
        }
        if "promedio" in probas_por_modelo and tops:
            top_prom = set(seleccionar_top(probas_por_modelo["promedio"], n).to_list())
            r["jaccard_medio_vs_promedio"] = statistics.fmean(
                _jaccard(t, top_prom) for t in tops.values()
            )
        resumen[str(n)] = r
    return resumen


# [Anotación · líneas 186–234] `etapa_salida`: lee los parquet de probabilidades del run, resuelve los cortes,
#   verifica que cubran exactamente los clientes del mes objetivo, escribe los CSV, registra sus sha256 y guarda
#   el resumen de coincidencias.
def etapa_salida(cfg: cfgmod.Config, run: Run) -> None:
    """Lee run/probas/*.parquet (contrato de la etapa final) y escribe los CSV."""
    dir_probas = run.dir / "probas"
    archivos = sorted(dir_probas.glob("*.parquet"))
    if not archivos:
        raise FileNotFoundError(
            f"no hay probabilidades en {dir_probas}: corré la etapa 'final'"
        )
    probas = {a.stem: pl.read_parquet(a) for a in archivos}

    objetivo = cfg.periodos.target
    validos = ids_del_periodo(CACHE_BASE, objetivo)
    ref = run.meta.get("validacion", {})
    envios = resolver_envios(
        cfg.salida.envios,
        ref.get("envios_optimos"),
        len(validos),
        ref.get("n_clientes_valid"),
    )
    log.info("cortes de envíos: %s", envios)

    for h in probas.values():
        validar_probas(h)
        if set(h["numero_de_cliente"].to_list()) != validos:
            raise ValueError(
                "las probabilidades no cubren exactamente los clientes del target"
            )

    nombres = {k: probas[k] for k in probas if cfg.final.promedio or k != "promedio"}
    archivos_csv = generar_submits(
        nombres, envios, run.dir / "submits", run.run_id, validos
    )
    for a in archivos_csv:
        run.registrar_archivo(a)
    semillerio = resumen_semillerio(nombres, envios)
    for n, r in semillerio.items():
        if r["jaccard_medio_pares"] is not None:
            log.info(
                "semillerío en %s envíos: Jaccard medio entre semillas=%.3f (mín %.3f)%s",
                n,
                r["jaccard_medio_pares"],
                r["jaccard_min_pares"],
                (
                    f" | vs promedio={r['jaccard_medio_vs_promedio']:.3f}"
                    if "jaccard_medio_vs_promedio" in r
                    else ""
                ),
            )
    run.registrar(envios=envios, semillerio=semillerio)
```

### competencia_01/competencia_1/pipeline/config.py

Configuración centralizada: lee YAML con herencia y overrides, la convierte en dataclasses inmutables sin valores por defecto y valida rangos y dependencias entre opciones.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Docstring e importaciones; define la raíz del repositorio y la carpeta de configs.
"""Configuración centralizada: YAML con herencia + overrides CLI -> dataclasses frozen.

`configs/base.yaml` es la única fuente de defaults: los dataclasses no tienen
valores por defecto, así que una clave faltante o desconocida (typo) es error.
"""

import copy
import dataclasses
import hashlib
import types
import typing
from dataclasses import dataclass
from pathlib import Path

import yaml

from competencia_1.pipeline import periodos

RAIZ = Path(__file__).resolve().parents[2]
CONFIGS_DIR = Path(__file__).resolve().parents[1] / "configs"


# [Anotación · líneas 23–54] Dataclasses de períodos (target, gap, n_meses_train, n_folds, meses_final,
#   folds), de la clase (positivos y peso de BAJA+1), de datos (rutas de los CSV y si se reconstruye la clase) y
#   de las 5 sub-familias intra-fila.
@dataclass(frozen=True)
class Periodos:
    target: int
    gap: int
    n_meses_train: int
    n_folds: int
    meses_final: list[int] | None  # override explícito
    folds: (
        list[dict] | None
    )  # [{train: [AAAAMM, ...], valid: AAAAMM}]; null = derivados


@dataclass(frozen=True)
class Target:
    positivos: list[str]
    peso_baja1: float  # peso de las filas BAJA+1 al entrenar (1.0 = sin pesos)


@dataclass(frozen=True)
class Datos:
    csv_procesado: str
    csv_crudo: str
    reconstruir_target: bool


@dataclass(frozen=True)
class IntraFila:
    tc_consolidado: bool
    tc_fechas: bool
    ratios: bool
    agregados: bool
    flags: bool


# [Anotación · líneas 57–112] Dataclasses de las familias de variables: Lags, Deltas, Ventanas, Tendencia,
#   Rankings y Canaritos, y FE, que las agrupa junto con drop_drift, drop_extra, campos_serie, historia, montos
#   y comportamiento.
@dataclass(frozen=True)
class Lags:
    activo: bool
    n: list[int]


@dataclass(frozen=True)
class Deltas:
    activo: bool
    n: list[int]
    pct: bool


@dataclass(frozen=True)
class Ventanas:
    activo: bool
    tamanio: int
    stats: list[str]
    ratio_avg: bool


@dataclass(frozen=True)
class Tendencia:
    activo: bool
    tamanio: int


@dataclass(frozen=True)
class Rankings:
    activo: bool
    campos: str | list[str]
    ntile10: list[str]


@dataclass(frozen=True)
class Canaritos:
    activo: bool
    n: int


@dataclass(frozen=True)
class FE:
    originales: bool
    drop_drift: list[str]
    drop_extra: list[str]
    intrafila: IntraFila
    campos_serie: str | list[str]
    lags: Lags
    deltas: Deltas
    ventanas: Ventanas
    tendencia: Tendencia
    historia: bool
    rankings: Rankings
    canaritos: Canaritos
    montos: str  # crudo | rank_cero_fijo | deflactado (escala de los montos m*)
    comportamiento: bool  # familia 9: eventos, recency, drenaje, RFM


# [Anotación · líneas 115–161] Dataclasses de dataset (undersampling y exclusiones), LGBM (parámetros fijos y
#   manuales), Optuna (trials, espacio, objetivo, pruning), Estabilidad, Variante y Ablacion.
@dataclass(frozen=True)
class DatasetCfg:
    undersampling: float
    excluir_bloques: list[
        str
    ]  # bloques del catálogo (+ originales/derivadas) a no usar
    excluir_features: list[str]  # columnas puntuales a no usar


@dataclass(frozen=True)
class LGBM:
    fijos: dict
    manual: dict


@dataclass(frozen=True)
class OptunaCfg:
    n_trials: int
    study_name: str  # "auto" -> derivado de experimento + fe_hash + folds
    ventana_meseta: int
    espacio: dict
    objetivo: str  # ganancia (meseta, la de negocio) | auc (sobre BAJA+2)
    pruning: bool  # corta el trial si el primer fold queda bajo la mediana


@dataclass(frozen=True)
class Estabilidad:
    top_k: int
    n_semillas: int
    criterio: str  # mediana | media_menos_desvio
    n_simulaciones: int  # simulaciones public/private 30/70


@dataclass(frozen=True)
class Variante:
    solo_bloques: list[str] | None  # si se indica, solo estos bloques
    excluir_bloques: list[str]
    excluir_features: list[str]


@dataclass(frozen=True)
class Ablacion:
    n_semillas: int
    referencia: str  # variante contra la que se comparan las demás (pareado)
    variantes: (
        dict  # nombre -> Variante (se valida y convierte en `variantes_ablacion`)
    )


# [Anotación · líneas 164–211] Dataclasses Final (origen de los hiperparámetros, semillas, promedio,
#   reescalado de min_data_in_leaf, carpeta de modelos ya entrenados), Salida (envíos y formato), Etapas (9
#   banderas) y Config, que reúne todo.
@dataclass(frozen=True)
class Final:
    params_desde: str  # manual | optuna:<study> | archivo:<path>
    n_semillas: int
    semillas: list[int] | None
    promedio: bool
    reescalar_min_data: bool | str  # true | false | "filas" (por filas de train)
    params_ignorar_fe_hash: (
        bool  # usar params optimizados con otras features (con warning)
    )
    modelos_desde: str | None  # carpeta con modelos ya entrenados: solo predecir


@dataclass(frozen=True)
class Salida:
    envios: str | int | list[int]  # "auto" | N | [N, ...]
    formato: str


@dataclass(frozen=True)
class Etapas:
    datos: bool
    features: bool
    validacion: bool
    optuna: bool
    estabilidad: bool
    ablacion: bool
    canaritos: bool
    final: bool
    salida: bool


@dataclass(frozen=True)
class Config:
    experimento: str
    semilla_maestra: int
    periodos: Periodos
    target: Target
    datos: Datos
    fe: FE
    dataset: DatasetCfg
    lgbm: LGBM
    optuna: OptunaCfg
    estabilidad: Estabilidad
    ablacion: Ablacion
    final: Final
    salida: Salida
    etapas: Etapas


# [Anotación · líneas 214–234] CLAVES_POSTERIORES: valores que se completan cuando un config ya congelado no
#   trae claves agregadas después (folds nulo, objetivo `ganancia`, pruning falso, modelos_desde nulo, montos
#   `crudo`, comportamiento falso, peso_baja1 1,0).
# ---------------------------------------------------------------- carga

# Claves agregadas después de congelar configs viejos (config_resuelta.yaml de runs,
# definitiva/config.yaml). Si faltan se completan con el valor que reproduce el comportamiento
# anterior. Solo estas: cualquier otra clave faltante o desconocida sigue siendo error.
CLAVES_POSTERIORES = {
    "periodos": {"folds": None},
    "optuna": {"objetivo": "ganancia", "pruning": False},
    "final": {"modelos_desde": None},
    "fe": {"montos": "crudo", "comportamiento": False},
    "target": {"peso_baja1": 1.0},
}


def completar_claves_posteriores(d: dict) -> dict:
    d = copy.deepcopy(d)
    for seccion, claves in CLAVES_POSTERIORES.items():
        if isinstance(d.get(seccion), dict):
            for k, v in claves.items():
                d[seccion].setdefault(k, v)
    return d


# [Anotación · líneas 237–276] `_deep_merge` mezcla diccionarios anidados; `cargar_dict` lee un YAML
#   resolviendo `hereda` de forma recursiva y detecta herencia circular; `aplicar_overrides` aplica
#   `clave.anidada=valor` interpretando el valor como YAML.
def _deep_merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def cargar_dict(path: Path, _vistos: tuple = ()) -> dict:
    """Lee un YAML resolviendo `hereda: otro.yaml` (relativo al archivo)."""
    path = Path(path).resolve()
    if path in _vistos:
        raise ValueError(f"herencia circular en {path}")
    with open(path, encoding="utf-8") as f:
        d = yaml.safe_load(f) or {}
    padre = d.pop("hereda", None)
    if padre is None:
        return d
    return _deep_merge(cargar_dict(path.parent / padre, _vistos + (path,)), d)


def aplicar_overrides(d: dict, overrides: list[str]) -> dict:
    """Aplica `clave.anidada=valor` (el valor se interpreta como YAML)."""
    d = copy.deepcopy(d)
    for ov in overrides:
        if "=" not in ov:
            raise ValueError(f"override inválido (falta '='): {ov}")
        clave, valor = ov.split("=", 1)
        partes = clave.strip().split(".")
        nodo = d
        for p in partes[:-1]:
            if not isinstance(nodo.get(p), dict):
                raise TypeError(f"override {clave}: '{p}' no es una sección")
            nodo = nodo[p]
        if partes[-1] not in nodo:
            raise ValueError(f"override {clave}: clave inexistente")
        nodo[partes[-1]] = yaml.safe_load(valor)
    return d


# [Anotación · líneas 279–321] `_construir` convierte el diccionario en dataclasses y rechaza claves faltantes
#   o desconocidas; `cargar_config` y `desde_dict` devuelven la Config ya validada.
def _construir(cls, d, ruta: str = ""):
    """dict -> dataclass recursivo; rechaza claves faltantes y desconocidas."""
    if not isinstance(d, dict):
        raise TypeError(f"{ruta or 'config'}: se esperaba una sección, llegó {d!r}")
    hints = typing.get_type_hints(cls)
    campos = {f.name for f in dataclasses.fields(cls)}
    desconocidas = set(d) - campos
    faltantes = campos - set(d)
    if desconocidas:
        raise ValueError(
            f"{ruta or 'config'}: claves desconocidas {sorted(desconocidas)}"
        )
    if faltantes:
        raise ValueError(f"{ruta or 'config'}: faltan claves {sorted(faltantes)}")
    kwargs = {}
    for nombre in campos:
        tipo = hints[nombre]
        valor = d[nombre]
        if dataclasses.is_dataclass(tipo):
            valor = _construir(tipo, valor, f"{ruta}.{nombre}".lstrip("."))
        elif isinstance(tipo, (types.UnionType, typing._UnionGenericAlias)):
            pass  # unión de tipos simples; validada en `validar`
        kwargs[nombre] = valor
    return cls(**kwargs)


def cargar_config(
    path: Path, overrides: list[str] | None = None
) -> tuple[Config, dict]:
    """Devuelve (Config validada, dict resuelto) listo para congelar a YAML."""
    d = aplicar_overrides(
        completar_claves_posteriores(cargar_dict(path)), overrides or []
    )
    cfg = _construir(Config, d)
    validar(cfg)
    return cfg, d


def desde_dict(d: dict) -> Config:
    d = completar_claves_posteriores(d)
    cfg = _construir(Config, d)
    validar(cfg)
    return cfg


# ------------------------------------------------------------ validación


# [Anotación · líneas 327–359] Funciones derivadas: `folds` (los explícitos o los calculados), `meses_final`,
#   `semillas_finales` (lista explícita o `generar_semillas`) y `variantes_ablacion`.
def folds(cfg: Config) -> list[periodos.Fold]:
    p = cfg.periodos
    if p.folds is not None:
        return [
            periodos.Fold(train=tuple(sorted(f["train"])), valid=int(f["valid"]))
            for f in p.folds
        ]
    return periodos.derivar_folds(p.target, p.gap, p.n_meses_train, p.n_folds)


def meses_final(cfg: Config) -> list[int]:
    p = cfg.periodos
    if p.meses_final is not None:
        return list(p.meses_final)
    return periodos.derivar_meses_final(p.target, p.gap, p.n_meses_train)


def semillas_finales(cfg: Config) -> list[int]:
    from competencia_1.pipeline.semillas import generar_semillas

    if cfg.final.semillas is not None:
        return list(cfg.final.semillas)
    return generar_semillas(cfg.semilla_maestra, cfg.final.n_semillas)


def variantes_ablacion(cfg: Config) -> dict[str, Variante]:
    """Variantes de la ablación como dataclasses validados (claves desconocidas = error)."""
    # una variante en `null` quita la heredada de base.yaml (el deep-merge no puede borrar claves)
    return {
        nombre: _construir(Variante, spec, f"ablacion.variantes.{nombre}")
        for nombre, spec in cfg.ablacion.variantes.items()
        if spec is not None
    }


# [Anotación · líneas 362–392] `validar` (primera parte): gap mínimo de 2 meses, forma de los folds
#   explícitos, mes objetivo con formato AAAAMM, distancia entre train y validación y entre meses finales y
#   objetivo, y clases positivas dentro de CONTINUA, BAJA+1 y BAJA+2.
def validar(cfg: Config) -> None:
    p = cfg.periodos
    if p.gap < 2:
        raise ValueError(f"periodos.gap={p.gap}: el gap mínimo es 2 meses")
    if p.n_meses_train < 1 or p.n_folds < 1:
        raise ValueError("periodos.n_meses_train y n_folds deben ser >= 1")
    if p.folds is not None:
        if not p.folds:
            raise ValueError("periodos.folds no puede ser una lista vacía")
        for f in p.folds:
            if (
                not isinstance(f, dict)
                or set(f) != {"train", "valid"}
                or not f["train"]
                or not isinstance(f["train"], list)
            ):
                raise ValueError(
                    f"periodos.folds: cada fold es {{train: [AAAAMM, ...], valid: AAAAMM}}: {f!r}"
                )
    if not 190001 <= p.target <= 299912 or not 1 <= p.target % 100 <= 12:
        raise ValueError(f"periodos.target inválido: {p.target}")
    for f in folds(cfg):
        periodos.validar_gap(f.train, f.valid, p.gap)
    for m in meses_final(cfg):
        periodos.validar_gap([m], p.target, p.gap)
    if not cfg.target.positivos or not set(cfg.target.positivos) <= {
        "CONTINUA",
        "BAJA+1",
        "BAJA+2",
    }:
        raise ValueError(f"target.positivos inválido: {cfg.target.positivos}")
# [Anotación · líneas 393–422] Valida peso_baja1 mayor o igual a 0, undersampling en (0, 1], entre 1 y 20
#   semillas, que cada semilla sea un primo del rango pedido, y los valores admitidos de `final.params_desde` y
#   `final.reescalar_min_data`.
    if not cfg.target.peso_baja1 >= 0:
        raise ValueError("target.peso_baja1 debe ser >= 0")
    e = cfg.optuna.espacio.get("peso_baja1")
    if e is not None and (e["tipo"] != "float" or float(e["low"]) < 0):
        raise ValueError("optuna.espacio.peso_baja1: float con low >= 0")
    if not 0 < cfg.dataset.undersampling <= 1:
        raise ValueError("dataset.undersampling debe estar en (0, 1]")
    if not 1 <= cfg.final.n_semillas <= 20:
        raise ValueError("final.n_semillas debe estar entre 1 y 20")
    from competencia_1.pipeline.semillas import validar_semilla_curso

    validar_semilla_curso(cfg.semilla_maestra, "semilla_maestra")
    if cfg.final.semillas is not None:
        if not cfg.final.semillas:
            raise ValueError("final.semillas no puede ser una lista vacía")
        if len(set(cfg.final.semillas)) != len(cfg.final.semillas):
            raise ValueError("final.semillas tiene semillas repetidas")
        if len(cfg.final.semillas) > 20:
            raise ValueError("final.semillas admite como máximo 20 semillas")
        for x in cfg.final.semillas:
            validar_semilla_curso(x, "final.semillas")
    fp = cfg.final.params_desde
    if fp != "manual" and not fp.startswith(
        ("optuna:", "estable:", "archivo:", "top:")
    ):
        raise ValueError(f"final.params_desde inválido: {fp}")
    if fp.startswith("top:") and not (fp[4:].isdigit() and int(fp[4:]) >= 1):
        raise ValueError(f"final.params_desde={fp}: se espera top:<k> con k >= 1")
    if cfg.final.reescalar_min_data not in (True, False, "filas"):
        raise ValueError("final.reescalar_min_data debe ser true, false o 'filas'")
# [Anotación · líneas 423–459] Valida las secciones de estabilidad y ablación, n_trials, el objetivo de Optuna
#   (`ganancia` o `auc`), cada entrada del espacio de búsqueda, que num_iterations esté en el espacio o en
#   `lgbm.manual`, y el formato y los envíos de la salida.
    e = cfg.estabilidad
    if e.top_k < 1 or not 1 <= e.n_semillas <= 20 or e.n_simulaciones < 1:
        raise ValueError(
            "estabilidad: top_k >= 1, n_semillas en 1..20 y n_simulaciones >= 1"
        )
    if e.criterio not in ("mediana", "media_menos_desvio"):
        raise ValueError(f"estabilidad.criterio inválido: {e.criterio}")
    a = cfg.ablacion
    if not 1 <= a.n_semillas <= 20:
        raise ValueError("ablacion.n_semillas debe estar entre 1 y 20")
    variantes = variantes_ablacion(cfg)
    if cfg.etapas.ablacion and a.referencia not in variantes:
        raise ValueError(
            f"ablacion.referencia '{a.referencia}' no está en ablacion.variantes"
        )
    if cfg.optuna.n_trials < 1:
        raise ValueError("optuna.n_trials debe ser >= 1")
    if cfg.optuna.objetivo not in ("ganancia", "auc"):
        raise ValueError(f"optuna.objetivo inválido: {cfg.optuna.objetivo}")
    for nombre, esp in cfg.optuna.espacio.items():
        if esp.get("tipo") not in ("int", "float"):
            raise ValueError(f"optuna.espacio.{nombre}: tipo debe ser int o float")
        if esp["low"] >= esp["high"]:
            raise ValueError(f"optuna.espacio.{nombre}: low >= high")
        if esp.get("log", False) and esp["low"] <= 0:
            raise ValueError(f"optuna.espacio.{nombre}: log=true requiere low > 0")
    if (
        "num_iterations" not in cfg.optuna.espacio
        and "num_iterations" not in cfg.lgbm.manual
    ):
        raise ValueError("num_iterations debe estar en optuna.espacio o en lgbm.manual")
    if cfg.salida.formato != "solo_ids":
        raise ValueError(f"salida.formato no soportado: {cfg.salida.formato}")
    e = cfg.salida.envios
    if not (e == "auto" or isinstance(e, int) or (isinstance(e, list) and e)):
        raise ValueError(f"salida.envios inválido: {e!r}")
    validar_fe(cfg.fe)


# [Anotación · líneas 462–506] `validar_fe`: lags y deltas mayores o iguales a 1, tamaño y estadísticos de las
#   ventanas, tendencia de tamaño 2 o más, dependencias (ratios y comportamiento requieren tc_consolidado y
#   agregados), modo de montos y especificación de campos.
MONTOS = ("crudo", "rank_cero_fijo", "deflactado")


def validar_fe(fe: FE) -> None:
    if fe.lags.activo and (not fe.lags.n or min(fe.lags.n) < 1):
        raise ValueError("fe.lags.n debe tener enteros >= 1 con lags activos")
    if fe.deltas.activo and (not fe.deltas.n or min(fe.deltas.n) < 1):
        raise ValueError("fe.deltas.n debe tener enteros >= 1 con deltas activos")
    v = fe.ventanas
    if v.activo:
        if v.tamanio < 1:
            raise ValueError("fe.ventanas.tamanio debe ser >= 1")
        if not v.stats or not set(v.stats) <= {"avg", "max", "min", "std"}:
            raise ValueError(f"fe.ventanas.stats inválido: {v.stats} (avg|max|min|std)")
        if v.ratio_avg and "avg" not in v.stats:
            raise ValueError(
                "fe.ventanas.ratio_avg requiere 'avg' en fe.ventanas.stats"
            )
    if fe.tendencia.activo and fe.tendencia.tamanio < 2:
        raise ValueError("fe.tendencia.tamanio debe ser >= 2 (se ajusta una recta)")
    if fe.intrafila.ratios and not (
        fe.intrafila.tc_consolidado and fe.intrafila.agregados
    ):
        raise ValueError(
            "fe.intrafila.ratios requiere tc_consolidado y agregados activos"
        )
    if fe.montos not in MONTOS:
        raise ValueError(
            f"fe.montos inválido: {fe.montos} (crudo | rank_cero_fijo | deflactado)"
        )
    if fe.comportamiento and not (
        fe.intrafila.tc_consolidado and fe.intrafila.agregados
    ):
        raise ValueError(
            "fe.comportamiento requiere intrafila.tc_consolidado y agregados"
        )
    if fe.canaritos.activo and fe.canaritos.n < 1:
        raise ValueError("fe.canaritos.n debe ser >= 1 con canaritos activos")
    for nombre, spec in (
        ("campos_serie", fe.campos_serie),
        ("rankings.campos", fe.rankings.campos),
    ):
        if isinstance(spec, str) and spec not in ("curado", "todos"):
            raise ValueError(f"fe.{nombre}: '{spec}' inválido (curado | todos | lista)")


# [Anotación · líneas 508–511] `hash_dict`: sha256 de un diccionario serializado como YAML con claves
#   ordenadas, recortado a 12 caracteres.
def hash_dict(d: dict, largo: int = 12) -> str:
    """Hash estable de un dict (YAML canónico con claves ordenadas)."""
    canon = yaml.safe_dump(d, sort_keys=True, allow_unicode=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:largo]
```

### competencia_01/competencia_1/pipeline/modelo.py

Funciones de LightGBM: armado de parámetros, Dataset, entrenamiento, predicción, importancias, reescalado de min_data_in_leaf, nombre del estudio de Optuna y lectura de hiperparámetros.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–17] Importaciones; carpeta de hiperparámetros exportados y lista de los que se
#   convierten a entero.
"""LightGBM: entrenamiento reproducible, predicción, importancias y resolución de params."""

import json
import logging
from pathlib import Path

import lightgbm as lgb
import numpy as np
import polars as pl

from competencia_1.pipeline import config as cfgmod
from competencia_1.pipeline.tracking import WORK

log = logging.getLogger("competencia_1.modelo")

PARAMS_DIR = WORK / "params"
_ENTEROS = ("num_leaves", "min_data_in_leaf", "max_bin", "bagging_freq", "max_depth")


# [Anotación · líneas 20–41] `params_lgbm` une los parámetros fijos, los del conjunto y la semilla, separa
#   num_iterations y quita peso_baja1; `peso_baja1` devuelve el peso del trial o el fijo de la configuración.
def params_lgbm(cfg: cfgmod.Config, params: dict, seed: int) -> tuple[dict, int]:
    """Mezcla fijos + hiperparámetros + semilla. Devuelve (params, num_iterations).

    `seed` fija bagging, feature_fraction y el resto de las semillas internas de
    LightGBM; junto con `deterministic` y `num_threads` fijos hace el entrenamiento
    reproducible bit a bit.
    """
    # peso_baja1 no es de LightGBM: va como pesos del Dataset (ver peso_baja1())
    p = {**cfg.lgbm.fijos, **params, "seed": int(seed)}
    p.pop("peso_baja1", None)
    if "num_iterations" not in p:
        raise ValueError("falta num_iterations en los hiperparámetros")
    n_iter = int(p.pop("num_iterations"))
    for k in _ENTEROS:
        if k in p:
            p[k] = int(p[k])
    return p, n_iter


def peso_baja1(cfg: cfgmod.Config, params: dict) -> float:
    """Peso de BAJA+1: el del trial (si se tuneó) o el fijo de target.peso_baja1."""
    return float(params.get("peso_baja1", cfg.target.peso_baja1))


# [Anotación · líneas 44–82] `crear_dataset` arma el Dataset de LightGBM con max_bin y feature_pre_filter;
#   `entrenar_dataset` y `entrenar_lgbm` llaman a `lgb.train` con num_boost_round = num_iterations y sin
#   conjunto de validación; `predecir` devuelve las probabilidades.
def crear_dataset(
    X: np.ndarray,
    y: np.ndarray,
    features: list[str],
    params: dict,
    weight: np.ndarray | None = None,
) -> lgb.Dataset:
    """Dataset de LightGBM. max_bin y feature_pre_filter se fijan acá (al construirlo)."""
    ds_params = {k: params[k] for k in ("max_bin", "feature_pre_filter") if k in params}
    return lgb.Dataset(
        X,
        label=y,
        weight=weight,
        feature_name=features,
        params=ds_params,
        free_raw_data=True,
    )


def entrenar_dataset(dtrain: lgb.Dataset, params: dict, n_iter: int) -> lgb.Booster:
    """Entrena sobre un Dataset (reutilizable entre trials de Optuna: se binariza una vez)."""
    return lgb.train(params, dtrain, num_boost_round=n_iter)


def entrenar_lgbm(
    X: np.ndarray,
    y: np.ndarray,
    features: list[str],
    params: dict,
    n_iter: int,
    weight: np.ndarray | None = None,
) -> lgb.Booster:
    return entrenar_dataset(
        crear_dataset(X, y, features, params, weight), params, n_iter
    )


def predecir(booster: lgb.Booster, X: np.ndarray) -> np.ndarray:
    return booster.predict(X)


# [Anotación · líneas 85–92] `importancias`: tabla de importancia por gain y por split de cada variable,
#   ordenada por gain.
def importancias(booster: lgb.Booster) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "feature": booster.feature_name(),
            "gain": booster.feature_importance(importance_type="gain"),
            "split": booster.feature_importance(importance_type="split"),
        }
    ).sort("gain", descending=True)


# [Anotación · líneas 95–109] `escalar_min_data` divide min_data_in_leaf por la fracción de undersampling;
#   `escalar_min_data_factor` lo multiplica por un factor (el que usa `reescalar_min_data: filas`).
def escalar_min_data(params: dict, undersampling: float) -> dict:
    """min_data_in_leaf se ajustó sobre datos submuestreados: al entrenar con todos
    los datos se divide por la fracción de undersampling (z494, 'punto SUTIL')."""
    out = dict(params)
    if "min_data_in_leaf" in out and undersampling < 1.0:
        out["min_data_in_leaf"] = max(1, round(out["min_data_in_leaf"] / undersampling))
    return out


def escalar_min_data_factor(params: dict, factor: float) -> dict:
    """Multiplica min_data_in_leaf por `factor` (cociente de filas final / validación)."""
    out = dict(params)
    if "min_data_in_leaf" in out and factor != 1:
        out["min_data_in_leaf"] = max(1, round(out["min_data_in_leaf"] * factor))
    return out


# [Anotación · líneas 112–145] `nombre_estudio`: `<experimento>_<fe_hash[:8]>_<hash>`; el hash cubre folds,
#   clases positivas, undersampling, espacio, parámetros fijos (sin num_threads), ventana y semilla, y agrega
#   objetivo, peso_baja1 o selección cuando difieren de su valor por defecto.
def nombre_estudio(cfg: cfgmod.Config, fe_hash: str) -> str:
    """`<exp>_<fe_hash[:8]>_<hash de lo que invalida los trials>`.

    Si cambia algo que altera el significado de un trial (folds, target, undersampling,
    espacio, parámetros fijos, ventana, semilla) el estudio es otro y no se mezclan.
    num_threads se excluye: `deterministic` lo hace irrelevante para el resultado.
    """
    if cfg.optuna.study_name != "auto":
        return cfg.optuna.study_name
    fijos = {k: v for k, v in cfg.lgbm.fijos.items() if k != "num_threads"}
    huella = {
        "folds": [(list(f.train), f.valid) for f in cfgmod.folds(cfg)],
        "positivos": cfg.target.positivos,
        "undersampling": cfg.dataset.undersampling,
        "espacio": cfg.optuna.espacio,
        "fijos": fijos,
        "ventana": cfg.optuna.ventana_meseta,
        "semilla": cfg.semilla_maestra,
    }
    if (
        cfg.optuna.objetivo != "ganancia"
    ):  # solo si cambia: no renombra estudios previos
        huella["objetivo"] = cfg.optuna.objetivo
    if cfg.target.peso_baja1 != 1.0:  # idem
        huella["peso_baja1"] = cfg.target.peso_baja1
    d = cfg.dataset
    if (
        d.excluir_bloques or d.excluir_features
    ):  # solo si hay selección: no cambia estudios previos
        huella["seleccion"] = {
            "bloques": sorted(d.excluir_bloques),
            "features": sorted(d.excluir_features),
        }
    return f"{cfg.experimento}_{fe_hash[:8]}_{cfgmod.hash_dict(huella, 8)}"


# [Anotación · líneas 148–171] `cargar_json_params` lee un JSON de hiperparámetros y compara su fe_hash con el
#   actual (error, o aviso si `params_ignorar_fe_hash` es verdadero); `ruta_params` resuelve el archivo según
#   `final.params_desde`.
def cargar_json_params(cfg: cfgmod.Config, path: Path, fe_hash: str) -> dict:
    """Lee un json de hiperparámetros y verifica que sea de las mismas features."""
    if not path.exists():
        raise FileNotFoundError(f"no existe el archivo de hiperparámetros: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("fe_hash") != fe_hash:
        msg = (
            f"{path.name}: optimizado con fe_hash={data.get('fe_hash')} pero el actual es "
            f"{fe_hash}; esos hiperparámetros no corresponden a estas features"
        )
        if not cfg.final.params_ignorar_fe_hash:
            raise ValueError(msg)
        log.warning("%s (se usan igual por final.params_ignorar_fe_hash)", msg)
    return data


def ruta_params(cfg: cfgmod.Config, fe_hash: str) -> Path:
    """Archivo de hiperparámetros según `final.params_desde` (optuna/estable/archivo)."""
    tipo, _, ref = cfg.final.params_desde.partition(":")
    if tipo in ("optuna", "estable"):
        nombre = nombre_estudio(cfg, fe_hash) if ref == "auto" else ref
        sufijo = "__estable" if tipo == "estable" else ""
        return PARAMS_DIR / f"{nombre}{sufijo}.json"
    return Path(ref) if Path(ref).is_absolute() else cfgmod.RAIZ / ref


# [Anotación · líneas 174–191] `resolver_params`: devuelve un único conjunto de hiperparámetros (manual o de
#   archivo) y lanza error si el origen es `top:<k>` o un archivo con varios conjuntos.
def resolver_params(cfg: cfgmod.Config, fe_hash: str) -> dict:
    """Hiperparámetros según `final.params_desde` (manual | optuna:<study|auto> | estable:<study|auto> | archivo:<path>).

    Los json de Optuna guardan el `fe_hash` con el que se optimizaron: usarlos con
    otras features es un error, no un warning.
    """
    if cfg.final.params_desde == "manual":
        return dict(cfg.lgbm.manual)
    if cfg.final.params_desde.startswith("top:"):
        raise ValueError(
            "params_desde=top:<k> son varios conjuntos: usar resolver_conjunto"
        )
    data = cargar_json_params(cfg, ruta_params(cfg, fe_hash), fe_hash)
    if "ensamble" in data:
        raise ValueError(
            "el archivo es un ensamble (varios conjuntos): usar resolver_conjunto"
        )
    return dict(data["params"])
```

### competencia_01/competencia_1/pipeline/periodos.py

Aritmética de meses AAAAMM, derivación de folds y meses finales a partir del mes objetivo y el gap, y validaciones de distancia y de clase completa.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–27] Docstring con las fórmulas; `mes_offset` suma o resta meses a un AAAAMM y
#   `rango_meses` lista los meses consecutivos entre dos extremos.
"""Aritmética de períodos YYYYMM y derivación de folds temporales.

Con target = T y gap = g:
  - meses finales : [T-g-(n-1) .. T-g]            (n = n_meses_train)
  - fold k        : valid = T-g-k, train = [valid-g-(n-1) .. valid-g]
El gap garantiza que el target del último mes de train (que mira 2 meses
hacia adelante) no se solape con el mes de validación.
"""

from dataclasses import dataclass


def mes_offset(foto_mes: int, delta: int) -> int:
    """Suma `delta` meses (puede ser negativo) a un período YYYYMM."""
    anio, mes = divmod(foto_mes, 100)
    if not 1 <= mes <= 12:
        raise ValueError(f"foto_mes inválido: {foto_mes}")
    total = anio * 12 + (mes - 1) + delta
    return (total // 12) * 100 + (total % 12) + 1


def rango_meses(desde: int, hasta: int) -> list[int]:
    """Lista de períodos consecutivos entre `desde` y `hasta` inclusive."""
    n = (hasta // 100 - desde // 100) * 12 + (hasta % 100 - desde % 100)
    if n < 0:
        raise ValueError(f"rango invertido: {desde}..{hasta}")
    return [mes_offset(desde, i) for i in range(n + 1)]


# [Anotación · líneas 30–50] `Fold` (meses de train y mes de validación); `derivar_folds` (validación =
#   objetivo − gap − k; train termina gap meses antes) y `derivar_meses_final` (terminan gap meses antes del
#   objetivo).
@dataclass(frozen=True)
class Fold:
    train: tuple[int, ...]
    valid: int


def derivar_folds(
    target: int, gap: int, n_meses_train: int, n_folds: int
) -> list[Fold]:
    folds = []
    for k in range(n_folds):
        valid = mes_offset(target, -gap - k)
        fin = mes_offset(valid, -gap)
        train = rango_meses(mes_offset(fin, -(n_meses_train - 1)), fin)
        folds.append(Fold(train=tuple(train), valid=valid))
    return folds


def derivar_meses_final(target: int, gap: int, n_meses_train: int) -> list[int]:
    fin = mes_offset(target, -gap)
    return rango_meses(mes_offset(fin, -(n_meses_train - 1)), fin)


# [Anotación · líneas 53–73] `validar_gap` lanza error si el último mes de train queda a menos de `gap` meses
#   de la validación; `validar_target_completo` lanza error si algún mes usado no tiene la clase completa.
def validar_gap(train: list[int] | tuple[int, ...], valid: int, gap: int) -> None:
    """Falla si el último mes de train queda a menos de `gap` meses de valid."""
    distancia = (valid // 100 - max(train) // 100) * 12 + (
        valid % 100 - max(train) % 100
    )
    if distancia < gap:
        raise ValueError(
            f"gap insuficiente: train termina en {max(train)}, valid={valid}, "
            f"distancia={distancia} < gap={gap}"
        )


def validar_target_completo(
    meses: list[int], meses_completos: set[int], etiqueta: str
) -> None:
    """Falla si algún mes usado para entrenar no tiene el target completo."""
    malos = sorted(set(meses) - set(meses_completos))
    if malos:
        raise ValueError(
            f"{etiqueta}: meses con target incompleto o inexistente: {malos}"
        )
```

### competencia_01/competencia_1/pipeline/dataset.py

Arma las matrices de entrenamiento y predicción desde el parquet de features, con submuestreo determinístico de CONTINUA y pesos opcionales para BAJA+1.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–31] Docstring; importaciones; nombres de las claves y la clase `Particion` (matriz X
#   en float32, ids, meses, lista de features, y, y las marcas es_baja2 y es_baja1).
"""Arma X / y / es_baja2 por lista de meses desde el parquet de features.

- Nunca entran como features `numero_de_cliente`, `foto_mes` ni `clase_ternaria`.
- `y` sale de `target.positivos` (lo que se entrena); `es_baja2` marca BAJA+2, la
  única clase que da ganancia (se usa para medir, nunca para entrenar).
- El undersampling de CONTINUA es determinístico: azar = hash(cliente, mes, semilla).
  Se conservan TODAS las filas BAJA+1 y BAJA+2 (como z494).
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl

CLAVES = ("numero_de_cliente", "foto_mes", "clase_ternaria")
CLASES_BAJA = ("BAJA+1", "BAJA+2")


@dataclass
class Particion:
    X: np.ndarray  # float32, NaN donde hay nulos
    ids: np.ndarray  # int64
    meses: np.ndarray  # int32
    features: list[str]
    y: np.ndarray | None  # int8; None si no hay target (mes a predecir)
    es_baja2: np.ndarray | None  # bool; None si no hay target
    es_baja1: np.ndarray | None = None  # bool; None si no hay target

    def __len__(self) -> int:
        return len(self.ids)


# [Anotación · líneas 34–47] `azar_uniforme`: número en [0, 1) determinístico por (cliente, mes, semilla),
#   obtenido con una mezcla de bits tipo splitmix64 hecha en numpy.
def azar_uniforme(ids: np.ndarray, meses: np.ndarray, seed: int) -> np.ndarray:
    """U[0,1) determinístico por (cliente, mes, semilla) con mezcla splitmix64.

    Se implementa a mano (y no con el hash de polars/duckdb) porque estos no
    garantizan estabilidad entre versiones y acá importa reproducir exacto.
    """
    with np.errstate(over="ignore"):
        x = ids.astype(np.uint64) * np.uint64(1_000_003) + meses.astype(np.uint64)
        x = x ^ np.uint64(seed)
        x = x + np.uint64(0x9E3779B97F4A7C15)
        x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        x = x ^ (x >> np.uint64(31))
    return (x >> np.uint64(11)).astype(np.float64) / float(1 << 53)


# [Anotación · líneas 50–55] `validar_features`: rechaza que las claves o la clase figuren como features y que
#   haya nombres repetidos.
def validar_features(features: list[str]) -> None:
    prohibidas = set(features) & set(CLAVES)
    if prohibidas:
        raise ValueError(f"claves/target no pueden ser features: {sorted(prohibidas)}")
    if len(set(features)) != len(features):
        raise ValueError("lista de features con duplicados")


# [Anotación · líneas 58–84] `cargar_particion` (lectura): lee del parquet las filas de los meses pedidos con
#   las claves, la clase (si corresponde) y las features; lanza error si algún mes no tiene filas.
def cargar_particion(
    parquet: Path,
    features: list[str],
    meses: list[int],
    positivos: list[str],
    undersampling: float = 1.0,
    seed: int = 0,
    con_target: bool = True,
) -> Particion:
    validar_features(features)
    cols = [
        "numero_de_cliente",
        "foto_mes",
        *(["clase_ternaria"] if con_target else []),
        *features,
    ]
    df = (
        pl.scan_parquet(parquet)
        .filter(pl.col("foto_mes").is_in(meses))
        .select(cols)
        .collect()
    )
    if df.height == 0:
        raise ValueError(f"no hay filas para los meses {meses}")
    faltan = set(meses) - set(df["foto_mes"].unique().to_list())
    if faltan:
        raise ValueError(f"meses sin filas en el parquet: {sorted(faltan)}")

# [Anotación · líneas 86–101] Con clase: exige que no haya filas sin clase; si undersampling es menor que 1
#   conserva todas las BAJA+1 y BAJA+2 y las demás filas cuyo azar es menor o igual a undersampling; arma `y` (1
#   si la clase está en `positivos`) y las marcas es_baja2 y es_baja1.
    if con_target:
        if df["clase_ternaria"].null_count():
            raise ValueError(
                f"meses {meses}: hay filas sin clase_ternaria (target incompleto)"
            )
        if undersampling < 1.0:
            azar = azar_uniforme(
                df["numero_de_cliente"].to_numpy(), df["foto_mes"].to_numpy(), seed
            )
            es_baja = df["clase_ternaria"].is_in(CLASES_BAJA).to_numpy()
            df = df.filter(pl.Series(es_baja | (azar <= undersampling)))
        y = df["clase_ternaria"].is_in(positivos).to_numpy().astype(np.int8)
        es_baja2 = (df["clase_ternaria"] == "BAJA+2").to_numpy()
        es_baja1 = (df["clase_ternaria"] == "BAJA+1").to_numpy()
    else:
        y = es_baja2 = es_baja1 = None

# [Anotación · líneas 103–115] Convierte las features a una matriz float32 contigua (los nulos pasan a NaN) y
#   devuelve la `Particion`.
    X = np.ascontiguousarray(
        df.select([pl.col(c).cast(pl.Float32) for c in features]).to_numpy(),
        dtype=np.float32,
    )
    return Particion(
        X=X,
        ids=df["numero_de_cliente"].to_numpy().astype(np.int64),
        meses=df["foto_mes"].to_numpy().astype(np.int32),
        features=list(features),
        y=y,
        es_baja2=es_baja2,
        es_baja1=es_baja1,
    )


# [Anotación · líneas 118–125] `pesos_filas`: devuelve None si peso_baja1 es 1,0; si no, un vector con ese
#   peso en las filas BAJA+1 y 1 en el resto.
def pesos_filas(part: Particion, peso_baja1: float) -> np.ndarray | None:
    """Pesos de entrenamiento: 1 salvo BAJA+1, que pesa `peso_baja1`. None si no hace falta
    (peso 1): el Dataset queda idéntico al de antes y los resultados previos no cambian."""
    if peso_baja1 == 1.0:
        return None
    if part.es_baja1 is None:
        raise ValueError("peso_baja1 requiere una partición con target")
    return np.where(part.es_baja1, peso_baja1, 1.0)


# [Anotación · líneas 128–142] `contar_filas`: filas esperadas para unos meses: todas las bajas más la
#   fracción de undersampling del resto.
def contar_filas(parquet: Path, meses: list[int], undersampling: float = 1.0) -> float:
    """Filas esperadas de `cargar_particion` para esos meses (sin cargar las features).

    Con undersampling se esperan todas las BAJA+1/BAJA+2 y esa fracción de CONTINUA.
    """
    df = (
        pl.scan_parquet(parquet)
        .filter(pl.col("foto_mes").is_in(meses))
        .select("clase_ternaria")
        .collect()
    )
    if df.height == 0:
        raise ValueError(f"no hay filas para los meses {meses}")
    n_baja = int(df["clase_ternaria"].is_in(CLASES_BAJA).sum())
    return n_baja + undersampling * (df.height - n_baja)
```

### competencia_01/competencia_1/pipeline/optimizacion.py

Etapa optuna: búsqueda de hiperparámetros con validación temporal por folds, estudio persistido en SQLite y exportación de los resultados. De sus trials salen los hiperparámetros guardados en params.json; sólo se ejecuta en el modo completo.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–53] Docstring con los criterios de la etapa (folds temporales, objetivo, pruning,
#   num_iterations como hiperparámetro, misma semilla en todos los trials); importaciones; `_resolver_db` da la
#   ruta de la base SQLite, modificable con DMEYF_DB.
"""Etapa optuna: búsqueda de hiperparámetros con validación temporal.

Alineado con la metodología de la materia, no un Optuna genérico:
- Cada trial se evalúa en los folds temporales del config (train en meses anteriores,
  validación en el mes que está `gap` meses después): nada de CV dentro del mismo mes.
- El objetivo (`optuna.objetivo`) es por defecto la ganancia meseta sobre BAJA+2,
  promediada entre folds y normalizada por la cantidad de clientes de cada mes. También
  puede ser el AUC sobre BAJA+2 (media simple entre folds).
- Con `optuna.pruning` el primer fold decide si el trial sigue (MedianPruner): los folds
  deben ir de menor a mayor costo.
- `num_iterations` es un hiperparámetro más: no hay early stopping sobre el mes de
  validación, que lo filtraría hacia el modelo.
- Todos los trials usan la misma semilla de LightGBM, así comparan hiperparámetros y
  no azar. El estudio vive en SQLite y se reanuda: `n_trials` es el TOTAL deseado.
"""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import polars as pl

from competencia_1.pipeline import config as cfgmod
from competencia_1.pipeline.dataset import cargar_particion, pesos_filas
from competencia_1.pipeline.features import columnas_seleccionadas, construir_features
from competencia_1.pipeline.metricas import resumir_scores
from competencia_1.pipeline.modelo import (
    PARAMS_DIR,
    crear_dataset,
    entrenar_dataset,
    nombre_estudio,
    params_lgbm,
    peso_baja1,
    predecir,
)
from competencia_1.pipeline.periodos import Fold
from competencia_1.pipeline.tracking import Run, ruta_relativa

log = logging.getLogger("competencia_1.optuna")


def _resolver_db() -> Path:
    """Base de Optuna. DMEYF_DB la cambia (p. ej. work/entrega/db para aislar una reproducción)."""
    p = Path(os.environ.get("DMEYF_DB") or cfgmod.RAIZ / "db" / "competencia_1.db")
    return p if p.is_absolute() else cfgmod.RAIZ / p


DB_PATH = _resolver_db()


# [Anotación · líneas 56–67] `FoldPreparado`: datos de un fold ya cargados (Dataset de train binarizado,
#   matriz de validación, marca de BAJA+2 y peso vigente de BAJA+1).
@dataclass
class FoldPreparado:
    """Datos de un fold ya cargados: se arman una vez y se reusan en todos los trials."""

    fold: Fold
    dtrain: lgb.Dataset  # ya binarizado
    n_train: int
    n_train_pos: int
    X_valid: np.ndarray
    es_baja2_valid: np.ndarray
    es_baja1_train: np.ndarray | None = None
    peso_actual: float = 1.0  # peso de BAJA+1 con el que está armado dtrain


# [Anotación · líneas 70–125] `preparar_folds`: por cada fold carga train con undersampling y la semilla dada
#   y el mes de validación completo, y construye el Dataset de LightGBM una sola vez para reutilizarlo entre
#   trials.
def preparar_folds(
    cfg: cfgmod.Config,
    parquet: Path,
    features: list[str],
    seed: int,
    reusar_valid: list[FoldPreparado] | None = None,
) -> list[FoldPreparado]:
    """Carga cada fold (train con undersampling de semilla `seed`, valid completo).

    `reusar_valid`: folds ya preparados con otra semilla; el mes de validación no
    depende de la semilla, así que se copia en vez de volver a leerlo del parquet.
    """
    out = []
    for i, fold in enumerate(cfgmod.folds(cfg)):
        train = cargar_particion(
            parquet,
            features,
            list(fold.train),
            cfg.target.positivos,
            undersampling=cfg.dataset.undersampling,
            seed=seed,
        )
        if reusar_valid is not None:
            X_valid, es_baja2 = reusar_valid[i].X_valid, reusar_valid[i].es_baja2_valid
        else:
            valid = cargar_particion(
                parquet, features, [fold.valid], cfg.target.positivos
            )
            X_valid, es_baja2 = valid.X, valid.es_baja2
        peso = cfg.target.peso_baja1
        dtrain = crear_dataset(
            train.X, train.y, features, cfg.lgbm.fijos, pesos_filas(train, peso)
        )
        dtrain.construct()
        out.append(
            FoldPreparado(
                fold,
                dtrain,
                len(train),
                int(train.y.sum()),
                X_valid,
                es_baja2,
                train.es_baja1,
                peso,
            )
        )
        log.info(
            "fold preparado (seed %d): train=%s (n=%d, pos=%d) valid=%s (n=%d)",
            seed,
            fold.train,
            len(train),
            int(train.y.sum()),
            fold.valid,
            len(es_baja2),
        )
    return out


# [Anotación · líneas 128–153] `ajustar_pesos` cambia el peso de BAJA+1 en el Dataset ya construido; `sugerir`
#   pide a Optuna cada hiperparámetro del espacio (entero o real, con o sin escala logarítmica).
def ajustar_pesos(prep: FoldPreparado, peso: float) -> None:
    """Deja `prep.dtrain` con BAJA+1 pesando `peso` (el Dataset se reusa entre trials)."""
    if peso == prep.peso_actual:
        return
    # set_field y no set_weight: set_weight convierte un vector de unos en None, y None no
    # borra los pesos ya cargados en un Dataset construido.
    w = np.where(prep.es_baja1_train, peso, 1.0).astype(np.float32)
    prep.dtrain.set_field("weight", w)
    prep.dtrain.weight = w
    prep.peso_actual = peso


def sugerir(trial: optuna.Trial, espacio: dict) -> dict:
    """Hiperparámetros de un trial según `optuna.espacio` del config."""
    params = {}
    for nombre, e in espacio.items():
        log_scale = bool(e.get("log", False))
        if e["tipo"] == "int":
            params[nombre] = trial.suggest_int(
                nombre, int(e["low"]), int(e["high"]), log=log_scale
            )
        else:
            params[nombre] = trial.suggest_float(
                nombre, float(e["low"]), float(e["high"]), log=log_scale
            )
    return params


# [Anotación · líneas 156–168] `valor_objetivo`: media del AUC entre folds, o media de la ganancia en meseta
#   normalizada por la cantidad de clientes de cada mes.
def valor_objetivo(resultados: list[dict], objetivo: str = "ganancia") -> float:
    """Valor que maximiza Optuna a partir del resumen de cada fold.

    `ganancia`: media de la ganancia meseta entre folds, llevada a un mes de tamaño
    promedio. La ganancia crece con la cantidad de clientes del mes: se normaliza por n
    para que ningún fold pese más solo por tener más clientes. `auc`: media simple.
    """
    if objetivo == "auc":
        return float(np.mean([r["auc"] for r in resultados]))
    if objetivo != "ganancia":
        raise ValueError(f"objetivo inválido: {objetivo}")
    n_ref = np.mean([r["n"] for r in resultados])
    return float(np.mean([r["ganancia_meseta"] * n_ref / r["n"] for r in resultados]))


# [Anotación · líneas 171–199] `puntuar_folds` entrena y predice el mes de validación de cada fold;
#   `resumir_folds` calcula las métricas por fold; `evaluar_trial` encadena ambas.
def puntuar_folds(
    cfg: cfgmod.Config, preps: list[FoldPreparado], params: dict, seed: int
) -> list[np.ndarray]:
    """Entrena con `params` y `seed` y devuelve el score del mes de validación de cada fold."""
    p, n_iter = params_lgbm(cfg, params, seed)
    scores = []
    for prep in preps:
        ajustar_pesos(prep, peso_baja1(cfg, params))
        scores.append(predecir(entrenar_dataset(prep.dtrain, p, n_iter), prep.X_valid))
    return scores


def resumir_folds(
    cfg: cfgmod.Config, preps: list[FoldPreparado], scores: list[np.ndarray]
) -> list[dict]:
    """Ganancia meseta y envíos óptimos por fold a partir de los scores."""
    resultados = []
    for prep, score in zip(preps, scores, strict=True):
        r = resumir_scores(prep.es_baja2_valid, score, cfg.optuna.ventana_meseta)
        r.pop("curva")
        r["valid"] = prep.fold.valid
        resultados.append(r)
    return resultados


def evaluar_trial(
    cfg: cfgmod.Config, preps: list[FoldPreparado], params: dict, seed: int
) -> list[dict]:
    return resumir_folds(cfg, preps, puntuar_folds(cfg, preps, params, seed))


# [Anotación · líneas 202–224] `abrir_estudio`: crea o reanuda el estudio en SQLite con dirección maximizar,
#   MedianPruner con 10 trials iniciales si hay pruning, y TPESampler con semilla = semilla maestra + trials ya
#   terminados (completos o podados).
def abrir_estudio(
    cfg: cfgmod.Config, nombre: str, storage: Path
) -> tuple[optuna.Study, int]:
    """Crea o reanuda el estudio. Devuelve (estudio, trials completos ya hechos).

    El sampler se resiembra con semilla + trials hechos: si se reanudara con la misma
    semilla, el generador volvería a empezar y repetiría los primeros sorteos al azar.
    """
    storage.parent.mkdir(parents=True, exist_ok=True)
    study = optuna.create_study(
        study_name=nombre,
        storage=f"sqlite:///{storage.as_posix()}",
        direction="maximize",
        load_if_exists=True,
        pruner=optuna.pruners.MedianPruner(n_startup_trials=10)
        if cfg.optuna.pruning
        else optuna.pruners.NopPruner(),
    )
    # los podados cuentan: son trials ya gastados del presupuesto
    terminados = (optuna.trial.TrialState.COMPLETE, optuna.trial.TrialState.PRUNED)
    hechos = sum(t.state in terminados for t in study.trials)
    study.sampler = optuna.samplers.TPESampler(seed=cfg.semilla_maestra + hechos)
    return study, hechos


# [Anotación · líneas 227–235] `_guardar_attrs`: guarda en el trial, por fold, la ganancia en meseta, la
#   cantidad de envíos donde ocurre, el AUC y la cantidad de filas de validación.
def _guardar_attrs(trial: optuna.Trial, resultados: list[dict]) -> None:
    trial.set_user_attr(
        "ganancia_meseta_folds", [r["ganancia_meseta"] for r in resultados]
    )
    trial.set_user_attr(
        "envios_optimos_folds", [r["envios_optimos"] for r in resultados]
    )
    trial.set_user_attr("auc_folds", [r["auc"] for r in resultados])
    trial.set_user_attr("n_valid_folds", [r["n"] for r in resultados])


# [Anotación · líneas 238–274] `correr_estudio` (función objetivo): cada trial sugiere hiperparámetros,
#   entrena fold por fold con la semilla maestra y, con pruning, informa el valor después de cada fold salvo el
#   último y corta el trial si el pruner lo indica.
def correr_estudio(
    cfg: cfgmod.Config,
    study: optuna.Study,
    preps: list[FoldPreparado],
    hechos: int,
) -> None:
    restantes = cfg.optuna.n_trials - hechos
    if restantes <= 0:
        log.info(
            "el estudio ya tiene %d trials (objetivo %d): nada que correr",
            hechos,
            cfg.optuna.n_trials,
        )
        return

    objetivo_cfg = cfg.optuna.objetivo
    fmt = "%.4f" if objetivo_cfg == "auc" else "%.0f"

    def objetivo(trial: optuna.Trial) -> float:
        params = sugerir(trial, cfg.optuna.espacio)
        completos = {
            **cfg.lgbm.manual,
            **params,
        }  # num_iterations fuera del espacio -> manual
        p, n_iter = params_lgbm(cfg, completos, cfg.semilla_maestra)
        resultados: list[dict] = []
        for i, prep in enumerate(preps):
            ajustar_pesos(prep, peso_baja1(cfg, completos))
            score = predecir(entrenar_dataset(prep.dtrain, p, n_iter), prep.X_valid)
            resultados += resumir_folds(cfg, [prep], [score])
            if cfg.optuna.pruning and i < len(preps) - 1:
                trial.report(valor_objetivo(resultados, objetivo_cfg), i)
                if trial.should_prune():
                    _guardar_attrs(trial, resultados)
                    raise optuna.TrialPruned
        _guardar_attrs(trial, resultados)
        return valor_objetivo(resultados, objetivo_cfg)

# [Anotación · líneas 276–301] Función que escribe una línea de log por trial y llamada a `study.optimize` con
#   los trials que faltan para llegar a n_trials.
    def reportar(study: optuna.Study, trial: optuna.trial.FrozenTrial) -> None:
        if trial.state != optuna.trial.TrialState.COMPLETE:
            log.info(
                "trial %d: podado tras el primer fold (%s) | %s",
                trial.number,
                trial.user_attrs.get("ganancia_meseta_folds"),
                trial.params,
            )
            return
        log.info(
            "trial %d: valor=" + fmt + " envios=%s | mejor=" + fmt + " (trial %d) | %s",
            trial.number,
            trial.value,
            trial.user_attrs["envios_optimos_folds"],
            study.best_value,
            study.best_trial.number,
            trial.params,
        )

    log.info(
        "optimizando: %d trials más (hechos: %d, objetivo: %d)",
        restantes,
        hechos,
        cfg.optuna.n_trials,
    )
    study.optimize(objetivo, n_trials=restantes, callbacks=[reportar])


# [Anotación · líneas 304–335] `cargar_estudio` abre un estudio existente; `top_trials` devuelve los k trials
#   completos de mayor valor; `tabla_trials` arma una fila por trial con estado, valor, hiperparámetros y
#   métricas por fold.
def cargar_estudio(nombre: str, storage: Path) -> optuna.Study:
    try:
        return optuna.load_study(
            study_name=nombre, storage=f"sqlite:///{storage.as_posix()}"
        )
    except KeyError as e:
        raise FileNotFoundError(
            f"no existe el estudio '{nombre}' en {storage}: corré antes la etapa 'optuna'"
        ) from e


def top_trials(study: optuna.Study, k: int) -> list[optuna.trial.FrozenTrial]:
    completos = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    if not completos:
        raise ValueError(f"el estudio '{study.study_name}' no tiene trials completos")
    return sorted(completos, key=lambda t: t.value, reverse=True)[:k]


def tabla_trials(study: optuna.Study) -> pl.DataFrame:
    filas = []
    for t in study.trials:
        fila = {"trial": t.number, "estado": t.state.name, "valor": t.value}
        fila.update({f"param_{k}": v for k, v in t.params.items()})
        fila["ganancia_meseta_folds"] = json.dumps(
            t.user_attrs.get("ganancia_meseta_folds")
        )
        fila["envios_optimos_folds"] = json.dumps(
            t.user_attrs.get("envios_optimos_folds")
        )
        fila["auc_folds"] = json.dumps(t.user_attrs.get("auc_folds"))
        filas.append(fila)
    return pl.DataFrame(filas)


# [Anotación · líneas 338–369] `exportar_mejores`: escribe params/<estudio>.json con los hiperparámetros del
#   trial de mayor valor, fe_hash, métricas por fold, folds, undersampling y semilla.
def exportar_mejores(
    cfg: cfgmod.Config,
    study: optuna.Study,
    fe_hash: str,
    dir_params: Path,
) -> dict:
    """Escribe params/<estudio>.json: lo que la etapa final reutiliza y verifica."""
    mejor = study.best_trial
    params = {**cfg.lgbm.manual, **mejor.params}
    info = {
        "study_name": study.study_name,
        "fe_hash": fe_hash,
        "valor": mejor.value,
        "trial": mejor.number,
        "n_trials": len(study.trials),
        "params": params,
        "ganancia_meseta_folds": mejor.user_attrs.get("ganancia_meseta_folds"),
        "auc_folds": mejor.user_attrs.get("auc_folds"),
        "objetivo": cfg.optuna.objetivo,
        "envios_optimos_folds": mejor.user_attrs.get("envios_optimos_folds"),
        "undersampling": cfg.dataset.undersampling,
        "positivos": cfg.target.positivos,
        "folds": [
            {"train": list(f.train), "valid": f.valid} for f in cfgmod.folds(cfg)
        ],
        "semilla": cfg.semilla_maestra,
    }
    dir_params.mkdir(parents=True, exist_ok=True)
    (dir_params / f"{study.study_name}.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return info


# [Anotación · líneas 372–411] `etapa_optuna`: construye las features, abre el estudio, prepara los folds si
#   faltan trials, corre la búsqueda, escribe el JSON exportado, optuna_trials.csv y best_params.json y registra
#   el resumen en meta.json.
def etapa_optuna(cfg: cfgmod.Config, run: Run) -> None:
    optuna.logging.set_verbosity(
        optuna.logging.WARNING
    )  # los trials los loguea `reportar`
    parquet, fe_hash = construir_features(cfg)
    features = columnas_seleccionadas(cfg, parquet)
    nombre = nombre_estudio(cfg, fe_hash)
    study, hechos = abrir_estudio(cfg, nombre, DB_PATH)
    log.info("estudio %s (%d features)", nombre, len(features))

    if hechos < cfg.optuna.n_trials:  # no cargar datos si no hay nada que correr
        preps = preparar_folds(cfg, parquet, features, cfg.semilla_maestra)
        correr_estudio(cfg, study, preps, hechos)
    else:
        correr_estudio(cfg, study, [], hechos)

    info = exportar_mejores(cfg, study, fe_hash, PARAMS_DIR)
    tabla_trials(study).write_csv(run.dir / "optuna_trials.csv")
    (run.dir / "best_params.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    run.registrar(
        fe_hash=fe_hash,
        optuna={
            "study_name": nombre,
            "storage": ruta_relativa(DB_PATH),
            "n_trials": info["n_trials"],
            "mejor_valor": info["valor"],
            "mejor_trial": info["trial"],
            "mejores_params": info["params"],
        },
    )
    log.info(
        "mejor trial %d: %s | para usarlo: final.params_desde=optuna:%s (o optuna:auto)",
        info["trial"],
        f"{info['valor']:.4f}"
        if cfg.optuna.objetivo == "auc"
        else f"{info['valor']:.0f}",
        nombre,
    )
```

### competencia_01/competencia_1/pipeline/entrega.py

Lógica de la entrega definitiva: `promover` y `promover_ensamble` congelan runs en competencia_1/definitiva/, y `reproducir` / `reproducir_completo` vuelven a correr cada componente, arman el ensamble y comparan el sha256 del CSV.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–36] Docstring e importaciones; define la carpeta definitiva, las 4 etapas de una
#   entrega (datos, features, final, salida) y la cabecera de texto de los config.yaml generados.
"""Entrega definitiva: congela un run ya ejecutado para que otra persona lo reproduzca.

`promover` toma un run (su config_resuelta.yaml, los hiperparámetros finales de meta.json y el
sha256 de su CSV) y escribe en competencia_1/definitiva/ una configuración autocontenida:
no depende de configs/exp, de work/ ni de db/ (el estudio de Optuna no hace falta).
`reproducir` corre esa configuración en un directorio de trabajo aparte y compara el sha256.
"""

import copy
import json
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path

import yaml

from competencia_1.pipeline import config as cfgmod
from competencia_1.pipeline.tracking import (
    RAIZ,
    info_git,
    ruta_relativa,
    sha256_archivo,
)

log = logging.getLogger("competencia_1.entrega")

DIR_DEFINITIVA = RAIZ / "competencia_1" / "definitiva"
ETAPAS_ENTREGA = ("datos", "features", "final", "salida")
CABECERA = """\
# ENTREGA DEFINITIVA (generada por `python -m competencia_1.entrega promover`; no editar a mano).
# Reproducir: python -m competencia_1.entrega reproducir
# Origen y sha256 esperado: ver entrega.json. Los hiperparámetros ya vienen escalados en
# params.json (reescalar_min_data: false) y no hace falta Optuna.
"""


# [Anotación · líneas 39–45] `_cargar_run`: lee meta.json y config_resuelta.yaml de la carpeta de un run.
def _cargar_run(run_dir: Path) -> tuple[dict, dict]:
    meta_p, cfg_p = run_dir / "meta.json", run_dir / "config_resuelta.yaml"
    for p in (meta_p, cfg_p):
        if not p.exists():
            raise FileNotFoundError(f"no existe {p}: ¿es la carpeta de un run?")
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    return meta, yaml.safe_load(cfg_p.read_text(encoding="utf-8"))


# [Anotación · líneas 48–82] `_csv_del_run` busca en el run el CSV `*_<modelo>_e<envios>.csv` y devuelve su
#   ruta y sha256; `_cortes_del_run` lista los cortes de envíos que tienen CSV.
def _csv_del_run(
    meta: dict, envios: int, modelo: str, run_dir: Path | None = None
) -> tuple[str, str]:
    """(ruta, sha256) del CSV `*_<modelo>_e<envios>.csv` registrado en el run.

    Si el corte no se registró (p. ej. un CSV extra generado después con las probabilidades
    del run), se toma de `<run>/submits/`: el contenido es el mismo que escribiría la etapa
    salida con ese corte, y el sha256 se calcula del archivo.
    """
    sufijo = f"_{modelo}_e{envios}.csv"
    candidatos = {
        k: v for k, v in meta.get("archivos", {}).items() if k.endswith(sufijo)
    }
    if not candidatos and run_dir is not None:
        extra = sorted((run_dir / "submits").glob(f"*{sufijo}"))
        if extra:
            return ruta_relativa(extra[0]), sha256_archivo(extra[0])
    if not candidatos:
        disponibles = sorted(
            Path(k).name for k in meta.get("archivos", {}) if k.endswith(".csv")
        )
        raise ValueError(
            f"el run no tiene un CSV '{modelo}' con {envios} envíos. "
            f"Cortes disponibles: {disponibles[:6]}"
        )
    ruta = min(candidatos)
    return ruta, candidatos[ruta]["sha256"]


def _cortes_del_run(meta: dict, run_dir: Path, modelo: str = "promedio") -> list[int]:
    """Cortes de envíos con CSV `*_<modelo>_e<N>.csv` en el run (registrados o en submits/)."""
    patron = re.compile(rf"_{re.escape(modelo)}_e(\d+)\.csv$")
    nombres = [Path(k).name for k in meta.get("archivos", {})]
    nombres += [p.name for p in (run_dir / "submits").glob("*.csv")]
    return sorted({int(m.group(1)) for n in nombres if (m := patron.search(n))})


# [Anotación · líneas 85–117] `_referencias_archivo` y `cadena_config` recorren un YAML de experimento
#   siguiendo `hereda` y los valores `archivo:<ruta>` para listar los archivos de los que depende.
def _referencias_archivo(valor) -> list[str]:
    """Rutas de los valores `archivo:<ruta>` que aparezcan en cualquier parte de un config."""
    if isinstance(valor, str):
        return [valor.removeprefix("archivo:")] if valor.startswith("archivo:") else []
    if isinstance(valor, dict):
        valor = list(valor.values())
    if isinstance(valor, list):
        return [r for v in valor for r in _referencias_archivo(v)]
    return []


def cadena_config(path: Path) -> list[Path]:
    """Archivos de los que depende un config de experimento: él, sus `hereda` y los `archivo:`."""
    vistos: list[Path] = []
    pendientes = [Path(path).resolve()]
    while pendientes:
        p = pendientes.pop()
        if p in vistos:
            continue
        if not p.exists():
            raise FileNotFoundError(
                f"el config referencia un archivo que no existe: {p}"
            )
        vistos.append(p)
        if p.suffix not in (".yaml", ".yml"):
            continue
        d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if d.get("hereda"):
            pendientes.append((p.parent / d["hereda"]).resolve())
        for ref in _referencias_archivo(d):
            r = Path(ref)
            pendientes.append((r if r.is_absolute() else RAIZ / r).resolve())
    return sorted(vistos)


# [Anotación · líneas 120–134] `_experimento_reproducible`: ubica el YAML del experimento en configs/exp y
#   marca si se puede rehacer de punta a punta: la etapa optuna está activa y `final.params_desde` es
#   `optuna:auto`, `estable:auto` o `top:<k>`.
def _experimento_reproducible(meta: dict, cfg: dict) -> tuple[Path | None, bool]:
    """(yaml del experimento, ¿se puede rehacer de punta a punta con ese solo config?).

    Es automático si el experimento optimiza en su propia corrida y toma los hiperparámetros
    de su propio estudio (no de otra corrida): así `reproducir --completo` rehace todo.
    """
    nombre = f"{meta.get('experimento')}.yaml"
    yaml_exp = RAIZ / "competencia_1" / "configs" / "exp" / nombre
    if not yaml_exp.exists():
        return None, False
    desde = cfg.get("final", {}).get("params_desde", "")
    propio = bool(cfg.get("etapas", {}).get("optuna")) and bool(
        re.fullmatch(r"(optuna|estable):auto|top:\d+", desde)
    )
    return yaml_exp, propio


# [Anotación · líneas 137–166] `promover` (inicio): verifica que el run terminó en estado `ok`, que ejecutó la
#   etapa final y que meta.json tiene los hiperparámetros finales; obtiene el CSV del corte pedido y su sha256.
def promover(
    run_dir: Path,
    envios: int,
    modelo: str = "promedio",
    destino: Path = DIR_DEFINITIVA,
    desde_crudo: bool = True,
    con_modelos: bool = False,
    resultado_publico: float | None = None,
) -> Path:
    """Escribe config.yaml, params.json y entrega.json en `destino` a partir de un run.

    Con `con_modelos` copia los modelos entrenados del run a `destino/modelos/` y el config
    queda en modo "solo predecir" (`final.modelos_desde`): reproducir tarda minutos en vez de
    reentrenar. Pesa del orden de 100 MB: queda a criterio de quien promueve.
    """
    run_dir = Path(run_dir)
    run_dir = run_dir if run_dir.is_absolute() else RAIZ / run_dir
    meta, cfg = _cargar_run(run_dir)

    if meta.get("estado") != "ok":
        raise ValueError(f"el run terminó con estado {meta.get('estado')!r}, no 'ok'")
    if meta.get("etapas", {}).get("final") != "ok":
        raise ValueError(
            "el run no ejecutó la etapa 'final': no hay modelo que promover"
        )
    params = meta.get("modelo", {}).get("params_final")
    if not params:
        raise ValueError("meta.json no tiene modelo.params_final")
    csv_ruta, csv_sha = _csv_del_run(meta, envios, modelo, run_dir)
    yaml_exp, completo_auto = _experimento_reproducible(meta, cfg)

# [Anotación · líneas 168–192] Arma la configuración congelada: experimento `entrega`, clase reconstruida
#   desde el crudo, hiperparámetros leídos de params.json sin reescalar, carpeta de modelos si se copian, un
#   solo corte de envíos y sólo las etapas datos, features, final y salida. La valida antes de escribir.
    # Reconstruye desde el crudo solo si se pide: la base debe dar el mismo contenido
    # (se verificó para esta entrega); si no, se usa el CSV procesado local.
    entrega = copy.deepcopy(cfg)
    entrega["experimento"] = "entrega"
    entrega["datos"]["reconstruir_target"] = bool(desde_crudo)
    entrega["final"].update(
        {
            "params_desde": f"archivo:{ruta_relativa(destino / 'params.json')}",
            # Los params ya salen escalados del run: no volver a dividir por el undersampling.
            "reescalar_min_data": False,
            # fe_hash depende de los bytes de base.parquet (cambian con la versión de duckdb);
            # las features quedan fijadas por este mismo archivo.
            "params_ignorar_fe_hash": True,
        }
    )
    entrega["final"]["modelos_desde"] = None
    if con_modelos:
        origen = run_dir / "modelos"
        archivos = sorted(origen.glob("*.txt"))
        if not archivos:
            raise ValueError(f"el run no tiene modelos guardados en {origen}")
        entrega["final"]["modelos_desde"] = ruta_relativa(destino / "modelos")
    entrega["salida"]["envios"] = [envios]
    entrega["etapas"] = {k: k in ETAPAS_ENTREGA for k in entrega["etapas"]}
    cfgmod.desde_dict(entrega)  # valida: falla antes de escribir nada

# [Anotación · líneas 194–223] Limpia el destino, copia los modelos `.txt` si se pidió y escribe config.yaml y
#   params.json (con la clave `ensamble` cuando hay varios conjuntos de hiperparámetros).
    destino.mkdir(parents=True, exist_ok=True)
    # una entrega de ensamble anterior no se mezcla con esta (un run suelto)
    shutil.rmtree(destino / "componentes", ignore_errors=True)
    viejos = destino / "modelos"
    if (
        viejos.exists()
    ):  # los modelos de una entrega anterior no se mezclan con los nuevos
        shutil.rmtree(viejos)
    if con_modelos:
        viejos.mkdir()
        for a in archivos:
            shutil.copy2(a, viejos / a.name)
    (destino / "config.yaml").write_text(
        CABECERA + yaml.safe_dump(entrega, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
        newline="\n",
    )
    (destino / "params.json").write_text(
        json.dumps(
            {
                "nota": f"hiperparámetros finales (ya escalados) del run {run_dir.name}",
                # lista [{etiqueta, params}] => ensamble de varios conjuntos (resolver_conjunto)
                ("ensamble" if isinstance(params, list) else "params"): params,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
# [Anotación · líneas 224–261] Escribe entrega.json con el run de origen, los commits, el corte, el nombre y
#   sha256 del CSV, las versiones, el puntaje público (lo conserva si se vuelve a promover el mismo run y corte)
#   y la cantidad de modelos incluidos.
    # Si se vuelve a promover el mismo run con el mismo corte, se conserva el resultado público.
    previo = destino / "entrega.json"
    if resultado_publico is None and previo.exists():
        anterior = json.loads(previo.read_text(encoding="utf-8"))
        # el puntaje es de un corte concreto: solo se conserva si es el mismo run y el mismo corte
        if (
            anterior.get("run") == ruta_relativa(run_dir)
            and anterior.get("envios") == envios
        ):
            resultado_publico = anterior.get("resultado_publico")
    info = {
        "run": ruta_relativa(run_dir),
        "experimento": meta.get("experimento"),
        "commit_del_run": meta.get("git", {}).get("commit"),
        "commit_actual": info_git()["commit"],
        "promovido": datetime.now().astimezone().isoformat(timespec="seconds"),
        "envios": envios,
        "modelo": modelo,
        "csv_original": Path(csv_ruta).name,
        "sha256_esperado": csv_sha,
        "versiones": meta.get("versiones"),
        "resultado_publico": resultado_publico,
        "modelos_incluidos": len(archivos) if con_modelos else 0,
        "config_experimento": ruta_relativa(yaml_exp) if yaml_exp else None,
        "completo_automatico": completo_auto,
    }
    (destino / "entrega.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    log.info(
        "entrega escrita en %s (run %s, %d envíos)",
        ruta_relativa(destino),
        run_dir.name,
        envios,
    )
    return destino


# [Anotación · líneas 264–306] `promover_ensamble` (inicio): lee meta.json del ensamble, exige un único CSV
#   con el corte pedido, conserva el puntaje público previo si coinciden run y corte y borra del destino los
#   archivos de una entrega anterior.
def promover_ensamble(
    ens_dir: Path,
    envios: int,
    destino: Path = DIR_DEFINITIVA,
    desde_crudo: bool = True,
    con_modelos: bool = True,
    resultado_publico: float | None = None,
) -> Path:
    """Congela un ensamble de runs (`python -m competencia_1.ensamble`) como entrega definitiva.

    Cada run del ensamble se promueve con `promover` en `destino/componentes/<i>_<exp>/` (su
    config, params y modelos); `destino/entrega.json` guarda el método, los pesos y el sha256 del
    CSV del ensamble. Reproducir = reproducir cada componente + promediar sus rankings.
    """
    ens_dir = Path(ens_dir)
    ens_dir = ens_dir if ens_dir.is_absolute() else RAIZ / ens_dir
    meta_p = ens_dir / "meta.json"
    if not meta_p.exists():
        raise FileNotFoundError(f"no existe {meta_p}: ¿es la carpeta de un ensamble?")
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    csvs = sorted((ens_dir / "submits").glob(f"*_e{envios}.csv"))
    if len(csvs) != 1:
        raise ValueError(
            f"el ensamble no tiene un único CSV con {envios} envíos en {ens_dir / 'submits'}"
        )
    csv = csvs[0]

    # El puntaje público es de un ensamble y un corte concretos: solo se conserva si coinciden.
    previo = destino / "entrega.json"
    if resultado_publico is None and previo.exists():
        anterior = json.loads(previo.read_text(encoding="utf-8"))
        if (
            anterior.get("run") == ruta_relativa(ens_dir)
            and anterior.get("envios") == envios
        ):
            resultado_publico = anterior.get("resultado_publico")

    # La carpeta queda solo con el ensamble: nada de una entrega anterior de un run suelto.
    destino.mkdir(parents=True, exist_ok=True)
    for viejo in ("config.yaml", "params.json", "entrega.json"):
        (destino / viejo).unlink(missing_ok=True)
    for viejo in ("modelos", "componentes"):
        shutil.rmtree(destino / viejo, ignore_errors=True)

# [Anotación · líneas 308–343] Para cada run del ensamble llama a `promover` en
#   `componentes/<i>_<experimento>/` con el mismo corte si ese run tiene CSV para él (si no, con el primer corte
#   disponible) y guarda carpeta, peso, sha256 del CSV y de las probabilidades y cantidad de modelos.
    componentes = []
    for i, e in enumerate(meta["entradas"]):
        run = Path(e["run"])
        run = run if run.is_absolute() else RAIZ / run
        m, _ = _cargar_run(run)
        # cada componente se verifica con su propio CSV: el del mismo corte si existe
        cortes = _cortes_del_run(m, run)
        if not cortes:
            raise ValueError(
                f"el run {run.name} no tiene CSV 'promedio' para verificar"
            )
        corte = envios if envios in cortes else cortes[0]
        sub = destino / "componentes" / f"{i}_{m['experimento']}"
        promover(
            run,
            corte,
            "promedio",
            sub,
            desde_crudo=desde_crudo,
            con_modelos=con_modelos,
        )
        ci = json.loads((sub / "entrega.json").read_text(encoding="utf-8"))
        componentes.append(
            {
                "carpeta": ruta_relativa(sub),
                "run": ci["run"],
                "experimento": ci["experimento"],
                "peso": e.get("peso", 1.0),
                "envios_verificacion": corte,
                "sha256_csv": ci["sha256_esperado"],
                "sha256_probas": e.get("sha256"),
                "modelos": ci["modelos_incluidos"],
                "config_experimento": ci["config_experimento"],
                "completo_automatico": ci["completo_automatico"],
            }
        )

# [Anotación · líneas 345–381] Escribe el entrega.json del ensamble: tipo, método, pesos, corte, nombre y
#   sha256 del CSV del ensamble, versiones, total de modelos y lista de componentes.
    nombre = meta["ensamble_id"].split("_", 1)[1]
    versiones = json.loads(
        (RAIZ / componentes[0]["carpeta"] / "entrega.json").read_text(encoding="utf-8")
    ).get("versiones")
    info = {
        "tipo": "ensamble",
        "run": ruta_relativa(ens_dir),
        "experimento": nombre,
        "metodo": meta["metodo"],
        "pesos": [c["peso"] for c in componentes],
        "commit_del_run": meta.get("git", {}).get("commit"),
        "commit_actual": info_git()["commit"],
        "promovido": datetime.now().astimezone().isoformat(timespec="seconds"),
        "envios": envios,
        "modelo": "ensamble",
        "csv_original": csv.name,
        "sha256_esperado": sha256_archivo(csv),
        "versiones": versiones,
        "resultado_publico": resultado_publico,
        "modelos_incluidos": sum(c["modelos"] for c in componentes),
        "config_experimento": None,
        "completo_automatico": all(c["completo_automatico"] for c in componentes),
        "componentes": componentes,
    }
    previo.write_text(
        json.dumps(info, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    log.info(
        "ensamble %s escrito en %s (%d componentes, %d envíos)",
        nombre,
        ruta_relativa(destino),
        len(componentes),
        envios,
    )
    return destino


# [Anotación · líneas 384–412] `_correr` ejecuta `main` con los argumentos dados y devuelve la carpeta del run
#   nuevo; `_csv_unico` ubica el CSV del corte; `_comparar` calcula el sha256 del CSV y lo compara con el
#   esperado, registrando `OK, coincide` o `DIFIERE`.
def _correr(args: list[str]) -> Path:
    """Corre el pipeline con `args` y devuelve la carpeta del run nuevo."""
    # Import diferido: main arrastra todo el pipeline y WORK ya quedó fijado por el entorno.
    from competencia_1 import main as main_mod
    from competencia_1.pipeline.tracking import RUNS_DIR

    antes = {p.name for p in RUNS_DIR.glob("*")} if RUNS_DIR.exists() else set()
    main_mod.main(args)
    nuevos = sorted({p.name for p in RUNS_DIR.glob("*")} - antes)
    if not nuevos:
        raise RuntimeError("la corrida no generó ninguna carpeta de run")
    return RUNS_DIR / nuevos[-1]


def _csv_unico(run: Path, modelo: str, envios: int) -> Path:
    csvs = list((run / "submits").glob(f"*_{modelo}_e{envios}.csv"))
    if len(csvs) != 1:
        raise RuntimeError(f"se esperaba 1 CSV en {run / 'submits'}, hay {len(csvs)}")
    return csvs[0]


def _comparar(csv: Path, esperado: str, etiqueta: str = "") -> bool:
    obtenido = sha256_archivo(csv)
    ok = obtenido == esperado
    log.info("%sCSV generado: %s", etiqueta, ruta_relativa(csv))
    log.info("%ssha256 esperado: %s", etiqueta, esperado)
    log.info("%ssha256 obtenido: %s", etiqueta, obtenido)
    log.info("%sRESULTADO: %s", etiqueta, "OK, coincide" if ok else "DIFIERE")
    return ok


# [Anotación · líneas 415–442] `_limpiar_work` borra el directorio de trabajo; `_correr_y_comparar` corre y
#   compara; `_args_completo` arma los argumentos del modo completo: el YAML original del experimento con
#   `salida.envios=[N]` y `datos.reconstruir_target=true`.
def _limpiar_work() -> None:
    from competencia_1.pipeline.tracking import WORK

    if WORK.exists():
        shutil.rmtree(WORK)


def _correr_y_comparar(args: list[str], info: dict, limpiar: bool) -> bool:
    """Corre el pipeline con `args` y compara el sha256 del CSV con `info`."""
    if limpiar:
        _limpiar_work()
    run = _correr(args)
    return _comparar(
        _csv_unico(run, info["modelo"], info["envios"]), info["sha256_esperado"]
    )


def _args_completo(info: dict) -> list[str]:
    config = Path(info["config_experimento"])
    config = config if config.is_absolute() else RAIZ / config
    return [
        "--config",
        str(config),
        "--set",
        f"salida.envios=[{info['envios']}]",
        "--set",
        "datos.reconstruir_target=true",
    ]


# [Anotación · líneas 445–474] `_reproducir_ensamble` (inicio): para cada componente corre el pipeline según
#   el modo (predecir: su config.yaml; entrenar: agrega `final.modelos_desde=null`; completo: el YAML del
#   experimento), compara el sha256 de su CSV y lee `probas/promedio.parquet`.
def _reproducir_ensamble(info: dict, limpiar: bool, modo: str) -> bool:
    """Reproduce cada componente (predecir | entrenar | completo), verifica su CSV, promedia
    los rankings como el ensamble original y compara el sha256 del CSV del ensamble."""
    import polars as pl

    from competencia_1.pipeline.datos import CACHE_BASE
    from competencia_1.pipeline.ensamble import combinar
    from competencia_1.pipeline.salida import escribir_csv_ids, ids_del_periodo
    from competencia_1.pipeline.tracking import RUNS_DIR

    if limpiar:
        _limpiar_work()
    probas, componentes_ok, target = [], True, None
    for c in info["componentes"]:
        sub = RAIZ / c["carpeta"]
        ci = _info(sub)
        etiqueta = f"[{Path(c['carpeta']).name}] "
        log.info("%sreproduciendo componente (modo %s)", etiqueta, modo)
        if modo == "completo":
            args = _args_completo(ci)
        else:
            args = ["--config", str(sub / "config.yaml")]
            if modo == "entrenar":
                args += ["--set", "final.modelos_desde=null"]
        run = _correr(args)
        csv = _csv_unico(run, ci["modelo"], ci["envios"])
        componentes_ok &= _comparar(csv, ci["sha256_esperado"], etiqueta)
        probas.append(pl.read_parquet(run / "probas" / "promedio.parquet"))
        cfg = yaml.safe_load((run / "config_resuelta.yaml").read_text(encoding="utf-8"))
        target = cfg["periodos"]["target"]

# [Anotación · líneas 476–490] Combina las probabilidades de los componentes con el método y los pesos de
#   entrega.json, escribe probas.parquet y el CSV `<fecha>_ensamble_e<N>.csv` usando los clientes del mes
#   objetivo como conjunto válido, y compara su sha256. Devuelve verdadero sólo si coinciden el ensamble y todos
#   los componentes.
    ens = combinar(probas, info["metodo"], info["pesos"])
    run_id = f"{datetime.now().astimezone():%Y%m%d-%H%M%S}_ensamble"
    salida = RUNS_DIR / run_id / "submits"
    salida.mkdir(parents=True)
    ens.write_parquet(salida.parent / "probas.parquet")
    csv = escribir_csv_ids(
        ens,
        info["envios"],
        salida / f"{run_id}_e{info['envios']}.csv",  # *_ensamble_e<N>.csv
        ids_del_periodo(CACHE_BASE, target),
    )
    ok = _comparar(csv, info["sha256_esperado"], "[ensamble] ")
    if not componentes_ok:
        log.error("algún componente no reprodujo su propio CSV")
    return ok and componentes_ok


# [Anotación · líneas 493–534] `_info` lee entrega.json; `reproducir` despacha al caso ensamble o corre un
#   config suelto; `reproducir_completo` exige la marca `completo_automatico` y rehace también la búsqueda de
#   hiperparámetros.
def _info(destino: Path) -> dict:
    info_p = destino / "entrega.json"
    if not info_p.exists():
        raise FileNotFoundError(f"no existe {info_p}: corré primero `promover`")
    return json.loads(info_p.read_text(encoding="utf-8"))


def reproducir(
    destino: Path = DIR_DEFINITIVA, limpiar: bool = False, entrenar: bool = False
) -> bool:
    """Corre config.yaml y compara el sha256 del CSV con entrega.json. True si coincide.

    Si la entrega incluye modelos entrenados, solo predice con ellos; `entrenar=True` los
    ignora y reentrena todo desde cero.
    """
    info = _info(destino)
    if info.get("tipo") == "ensamble":
        return _reproducir_ensamble(
            info, limpiar, "entrenar" if entrenar else "predecir"
        )
    args = ["--config", str(destino / "config.yaml")]
    if entrenar:
        args += ["--set", "final.modelos_desde=null"]
    return _correr_y_comparar(args, info, limpiar)


def reproducir_completo(destino: Path = DIR_DEFINITIVA, limpiar: bool = False) -> bool:
    """Rehace TODO: Optuna, selección de los mejores trials, modelos finales y CSV.

    Corre el config original del experimento (el que dio origen a los hiperparámetros) con un
    estudio de Optuna nuevo (DMEYF_DB aislado) y el target reconstruido desde el crudo, y
    compara el sha256 con la entrega. Solo es automático si el experimento es autocontenido.
    """
    info = _info(destino)
    if not info.get("completo_automatico"):
        raise ValueError(
            "esta entrega no se puede rehacer de punta a punta con un solo config "
            "(sus hiperparámetros vienen de otra corrida): ver los pasos en el README"
        )
    if info.get("tipo") == "ensamble":
        return _reproducir_ensamble(info, limpiar, "completo")
    return _correr_y_comparar(_args_completo(info), info, limpiar)
```

### competencia_01/competencia_1/pipeline/ensamble.py

Combina las probabilidades de varios runs en un solo ranking, por promedio de ranks normalizados (método `rank`, el de la entrega) o de probabilidades (método `prob`).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–17] Docstring con los dos métodos; importaciones; lista de métodos admitidos.
"""Ensamble de runs: combina las probabilidades finales de varios runs en un solo ranking.

Cada run aporta su `probas/promedio.parquet` (o el parquet que se indique). Dos métodos:
- rank (default): cada modelo se convierte en su rank normalizado en (0, 1] y se promedia.
  Es el adecuado cuando los modelos tienen escalas de probabilidad distintas (p. ej. 15 vs
  113 hojas, o distinto min_data_in_leaf): solo importa el orden, que es lo que decide el corte.
- prob: promedio ponderado de probabilidades (sesga hacia el modelo más "confiado").
"""

import itertools
import statistics

import polars as pl

from competencia_1.pipeline.salida import seleccionar_top, validar_probas

METODOS = ("rank", "prob")


# [Anotación · líneas 20–25] `normalizar_rank`: reemplaza prob por rank promedio / n, en (0, 1]; a mayor
#   probabilidad, mayor valor.
def normalizar_rank(probas: pl.DataFrame) -> pl.DataFrame:
    """prob -> rank promedio / n, en (0, 1]: mayor prob, mayor valor. Empates comparten rank."""
    n = probas.height
    return probas.with_columns(
        (pl.col("prob").rank(method="average") / n).alias("prob")
    )


# [Anotación · líneas 28–46] `combinar` (validaciones): método admitido, al menos 2 modelos, pesos positivos y
#   que todos los modelos tengan exactamente los mismos clientes.
def combinar(
    probas: list[pl.DataFrame], metodo: str = "rank", pesos: list[float] | None = None
) -> pl.DataFrame:
    """Promedio ponderado de los modelos sobre exactamente el mismo conjunto de clientes."""
    if metodo not in METODOS:
        raise ValueError(f"metodo={metodo!r}; opciones: {METODOS}")
    if len(probas) < 2:
        raise ValueError("un ensamble necesita al menos 2 modelos")
    pesos = pesos or [1.0] * len(probas)
    if len(pesos) != len(probas) or any(p <= 0 for p in pesos):
        raise ValueError(f"pesos inválidos: {pesos} para {len(probas)} modelos")
    for p in probas:
        validar_probas(p)
    ids = set(probas[0]["numero_de_cliente"].to_list())
    for i, p in enumerate(probas[1:], start=1):
        if set(p["numero_de_cliente"].to_list()) != ids:
            raise ValueError(
                f"el modelo {i} no tiene los mismos clientes que el modelo 0"
            )

# [Anotación · líneas 48–63] Convierte cada modelo a rank normalizado (método `rank`) o deja la probabilidad,
#   multiplica por peso / suma de pesos, une por numero_de_cliente, suma, recorta a [0, 1] y ordena por
#   numero_de_cliente.
    total = sum(pesos)
    partes = []
    for i, (p, w) in enumerate(zip(probas, pesos, strict=True)):
        q = normalizar_rank(p) if metodo == "rank" else p
        partes.append(
            q.select("numero_de_cliente", (pl.col("prob") * w / total).alias(f"m{i}"))
        )
    out = partes[0]
    for q in partes[1:]:
        out = out.join(q, on="numero_de_cliente", how="inner")
    out = out.select(
        "numero_de_cliente",
        pl.sum_horizontal(pl.exclude("numero_de_cliente")).alias("prob"),
    ).with_columns(pl.col("prob").clip(0.0, 1.0))  # redondeo de punto flotante
    validar_probas(out)
    return out.sort("numero_de_cliente")


# [Anotación · líneas 66–88] `coincidencias`: índice de Jaccard del top-N entre pares de modelos y de cada
#   modelo contra el ensamble.
def coincidencias(
    modelos: dict[str, pl.DataFrame], ensamble: pl.DataFrame, envios: list[int]
) -> dict:
    """Jaccard del top-N entre pares de modelos y de cada modelo contra el ensamble.

    Si los modelos ya coinciden casi del todo (Jaccard ~1), el ensamble no puede aportar.
    """
    out = {}
    for n in envios:
        tops = {k: set(seleccionar_top(v, n).to_list()) for k, v in modelos.items()}
        top_ens = set(seleccionar_top(ensamble, n).to_list())
        pares = {
            f"{a}|{b}": len(tops[a] & tops[b]) / len(tops[a] | tops[b])
            for a, b in itertools.combinations(tops, 2)
        }
        out[str(n)] = {
            "jaccard_pares": pares,
            "jaccard_medio_pares": statistics.fmean(pares.values()),
            "jaccard_vs_ensamble": {
                k: len(t & top_ens) / len(t | top_ens) for k, t in tops.items()
            },
        }
    return out
```

### competencia_01/competencia_1/pipeline/metricas.py

Resumen de métricas de un mes de validación: AUC sobre BAJA+2, curva de ganancia y ganancia en meseta.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–21] `auc`: AUC de BAJA+2 contra el resto calculado por Mann-Whitney con rangos
#   promedio; lanza error si falta una de las dos clases.
"""Métricas de negocio sobre scores: curva de ganancia, meseta y envíos óptimos.

La lógica numérica vive en dmeyf/metrics.py (reutilizable por cualquier experimento);
acá solo se arma el resumen que consumen validación, Optuna y los logs.
"""

import numpy as np
import polars as pl

from dmeyf.metrics import curva_ganancia, ganancia_meseta


def auc(es_baja2: np.ndarray, score: np.ndarray) -> float:
    """AUC (Mann-Whitney con rangos promedio: los empates cuentan 0,5) de BAJA+2 contra el resto."""
    y = np.asarray(es_baja2, dtype=bool)
    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    if n_pos == 0 or n_neg == 0:
        raise ValueError("AUC indefinido: falta una de las dos clases en el mes")
    rangos = pl.Series(np.asarray(score, dtype=float)).rank("average").to_numpy()
    return float((rangos[y].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


# [Anotación · líneas 24–38] `resumir_scores`: devuelve cantidad de filas y de BAJA+2, AUC, ganancia en meseta
#   y cantidad de envíos donde ocurre, máximo de la curva sin suavizar y su posición, y la curva.
def resumir_scores(es_baja2: np.ndarray, score: np.ndarray, ventana: int) -> dict:
    """Resumen de un mes de validación (la ganancia se mide siempre sobre BAJA+2)."""
    curva = curva_ganancia(es_baja2, score)
    meseta, envios_meseta = ganancia_meseta(curva, ventana)
    i_max = int(np.argmax(curva))
    return {
        "n": len(curva),
        "n_baja2": int(es_baja2.sum()),
        "auc": auc(es_baja2, score),
        "ganancia_meseta": meseta,
        "envios_optimos": envios_meseta,
        "ganancia_max_cruda": int(curva[i_max]),
        "envios_max_crudo": i_max + 1,
        "curva": curva,
    }


# [Anotación · líneas 41–46] `curva_submuestreada`: puntos (envíos, ganancia) cada 100 envíos hasta 30.000.
def curva_submuestreada(
    curva: np.ndarray, hasta: int = 30_000, paso: int = 100
) -> list[tuple]:
    """Puntos (envíos, ganancia) para guardar la curva sin escribir 160k filas."""
    n = min(hasta, len(curva))
    return [(k, int(curva[k - 1])) for k in range(paso, n + 1, paso)]
```

### competencia_01/competencia_1/pipeline/tracking.py

Registro por corrida: carpeta del run, logging, meta.json con sha256 de los archivos generados y una fila por run en runs.csv.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–47] Docstring; importaciones; `_resolver_work` da la carpeta de trabajo (modificable
#   con DMEYF_WORK), y se definen las rutas de runs y las columnas de runs.csv.
"""Tracking por corrida: carpeta de run, logging, meta.json y registro global.

Cada run vive en work/competencia_1/runs/<run_id>/ con su config congelada,
run.log y meta.json (actualizado de forma incremental, así un run caído deja
rastro). `runs.csv` resume todas las corridas en una fila cada una.
"""

import csv
import hashlib
import json
import logging
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Self

import yaml

from competencia_1.pipeline.config import RAIZ


def _resolver_work() -> Path:
    """Carpeta de salidas. DMEYF_WORK la cambia (p. ej. work/entrega o un disco en GCP)."""
    p = Path(os.environ.get("DMEYF_WORK") or RAIZ / "work" / "competencia_1")
    return p if p.is_absolute() else RAIZ / p


WORK = _resolver_work()
RUNS_DIR = WORK / "runs"
RUNS_CSV = WORK / "runs.csv"
CAMPOS_RUNS_CSV = [
    "run_id",
    "inicio",
    "experimento",
    "estado",
    "target",
    "fe_hash",
    "semillas",
    "ganancia_valid",
    "envios",
    "ruta",
]

log = logging.getLogger("competencia_1")


# [Anotación · líneas 50–65] `sha256_archivo` calcula el hash de un archivo leyéndolo por bloques;
#   `ruta_relativa` devuelve la ruta relativa a la raíz del repositorio.
def sha256_archivo(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def ruta_relativa(path: Path) -> str:
    """Ruta relativa al repo (con /) si está adentro; si no, la ruta absoluta."""
    path = Path(path)
    return (
        path.relative_to(RAIZ).as_posix()
        if path.is_relative_to(RAIZ)
        else path.as_posix()
    )


# [Anotación · líneas 68–99] `_git` e `info_git` obtienen el commit y si hay cambios sin commitear en
#   competencia_1; `versiones` devuelve las de Python, lightgbm, optuna, polars, duckdb y numpy.
def _git(*args: str) -> str:
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=RAIZ,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def info_git() -> dict:
    sucio = _git("status", "--porcelain", "--", "competencia_1")
    return {
        "commit": _git("rev-parse", "HEAD") or None,
        "dirty": bool(sucio),
        "dirty_archivos": sucio.splitlines()[:20],
    }


def versiones() -> dict:
    out = {"python": platform.python_version()}
    for mod in ("lightgbm", "optuna", "polars", "duckdb", "numpy"):
        try:
            out[mod] = __import__(mod).__version__
        except Exception:  # noqa: BLE001 - no instalado o sin __version__
            out[mod] = None
    return out


# [Anotación · líneas 102–132] `Run.__init__`: crea la carpeta `<fecha-hora>_<experimento>`, inicializa
#   meta.json (estado, git, versiones, archivos, etapas), escribe config_resuelta.yaml y configura el logging.
class Run:
    """Contexto de una corrida. Úsese con `with Run(...) as run:`."""

    def __init__(
        self, experimento: str, config_resuelta: dict, run_id: str | None = None
    ):
        self.inicio = datetime.now(UTC).astimezone()
        self.run_id = run_id or f"{self.inicio:%Y%m%d-%H%M%S}_{experimento}"
        self.dir = RUNS_DIR / self.run_id
        self.dir.mkdir(parents=True, exist_ok=False)
        self.meta: dict = {
            "run_id": self.run_id,
            "experimento": experimento,
            "inicio": self.inicio.isoformat(timespec="seconds"),
            "fin": None,
            "estado": "running",
            "git": info_git(),
            "versiones": versiones(),
            "archivos": {},
            "etapas": {},
        }
        with open(self.dir / "config_resuelta.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(config_resuelta, f, sort_keys=False, allow_unicode=True)
        self._config_logging()
        if self.meta["git"]["dirty"]:
            log.warning(
                "competencia_1 tiene cambios sin commitear: el run no es 100%% "
                "reproducible desde git (%s)",
                ", ".join(self.meta["git"]["dirty_archivos"][:5]),
            )
        self.guardar_meta()

# [Anotación · líneas 134–169] Logging a run.log y a stderr; `registrar` agrega claves a meta.json,
#   `registrar_archivo` anota sha256 y tamaño, y `guardar_meta` escribe a un temporal y lo reemplaza.
    # -- logging ---------------------------------------------------------
    def _config_logging(self) -> None:
        fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
        raiz = logging.getLogger("competencia_1")
        raiz.setLevel(logging.INFO)
        raiz.handlers.clear()
        for h in (
            logging.FileHandler(self.dir / "run.log", encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ):
            h.setFormatter(fmt)
            raiz.addHandler(h)
        logging.captureWarnings(True)
        logging.getLogger("py.warnings").addHandler(raiz.handlers[0])

    # -- meta ------------------------------------------------------------
    def registrar(self, **kv) -> None:
        """Agrega claves de primer nivel a meta.json (se guarda al instante)."""
        self.meta.update(kv)
        self.guardar_meta()

    def registrar_archivo(self, path: Path) -> None:
        path = Path(path)
        self.meta["archivos"][ruta_relativa(path)] = {
            "sha256": sha256_archivo(path),
            "bytes": path.stat().st_size,
        }
        self.guardar_meta()

    def guardar_meta(self) -> None:
        tmp = self.dir / "meta.json.tmp"
        tmp.write_text(
            json.dumps(self.meta, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        tmp.replace(self.dir / "meta.json")

# [Anotación · líneas 171–208] Entrada y salida del contexto: marca el estado `ok` o `failed`, guarda
#   meta.json y agrega una fila a runs.csv.
    # -- ciclo de vida ---------------------------------------------------
    def __enter__(self) -> Self:
        log.info("run %s iniciado -> %s", self.run_id, self.dir)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.meta["fin"] = datetime.now(UTC).astimezone().isoformat(timespec="seconds")
        if exc_type is None:
            self.meta["estado"] = "ok"
        else:
            self.meta["estado"] = "failed"
            self.meta["error"] = f"{exc_type.__name__}: {exc}"
            log.error("run %s falló", self.run_id, exc_info=(exc_type, exc, tb))
        self.guardar_meta()
        self._agregar_runs_csv()
        log.info("run %s terminó: %s", self.run_id, self.meta["estado"])
        return False  # no tragar la excepción

    def _agregar_runs_csv(self) -> None:
        m = self.meta
        fila = {
            "run_id": self.run_id,
            "inicio": m["inicio"],
            "experimento": m["experimento"],
            "estado": m["estado"],
            "target": m.get("target"),
            "fe_hash": m.get("fe_hash"),
            "semillas": json.dumps(m.get("semillas")),
            "ganancia_valid": m.get("ganancia_valid"),
            "envios": json.dumps(m.get("envios")),
            "ruta": ruta_relativa(self.dir),
        }
        nuevo = not RUNS_CSV.exists()
        with open(RUNS_CSV, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS_RUNS_CSV)
            if nuevo:
                w.writeheader()
            w.writerow(fila)
```

### competencia_01/competencia_1/pipeline/features/campos.py

Listas de campos sobre los que se calculan las variables históricas (36) y los rankings por mes (19), y funciones que resuelven qué campos usar y cuáles son montos.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–48] CAMPOS_SERIE_CURADO: 36 campos (26 originales de transacciones, saldos, márgenes,
#   comisiones, payroll, tarjetas, préstamos y transferencias, y 10 derivados de la familia intra-fila) sobre
#   los que se calculan lags, deltas, ventanas y tendencia.
"""Listas de campos "curados" y resolución de `campos_serie` / `rankings.campos`."""

import logging
import re

log = logging.getLogger("competencia_1.fe")

# Variables con mayor AUC / importancia según el EDA (docs/Hallazgos EDA Zulip.txt)
# más derivadas de la familia 1 (fe_sql.py, CAMPOS_SERIE_CURADO).
CAMPOS_SERIE_CURADO = [
    "ctrx_quarter",
    "chomebanking_transacciones",
    "cmobile_app_trx",
    "ccajas_transacciones",
    "catm_trx",
    "ctarjeta_debito_transacciones",
    "ccallcenter_transacciones",
    "mcuentas_saldo",
    "mcaja_ahorro",
    "mcuenta_corriente",
    "mpasivos_margen",
    "mactivos_margen",
    "mrentabilidad",
    "mcomisiones",
    "mcomisiones_mantenimiento",
    "cpayroll_trx",
    "mpayroll",
    "cproductos",
    "mautoservicio",
    "matm",
    "mtarjeta_visa_consumo",
    "mtarjeta_master_consumo",
    "mprestamos_personales",
    "mtransferencias_recibidas",
    "mtransferencias_emitidas",
    "cdescubierto_preacordado",
    # derivadas de la familia 1
    "tc_msaldototal",
    "tc_mconsumototal",
    "tc_mlimitecompra",
    "tc_mpagado",
    "r_tc_uso_limite",
    "c_trx_digitales",
    "c_trx_presenciales",
    "r_engagement_digital",
    "m_activos_totales",
    "c_productos_contratados",
]

# [Anotación · líneas 50–70] CAMPOS_RANK_CURADO: 19 campos para el ranking dentro del mes (rentabilidad,
#   comisiones, márgenes, saldos, payroll, préstamos, consumos de tarjeta, transacciones, productos, antigüedad
#   y edad).
CAMPOS_RANK_CURADO = [
    "mrentabilidad",
    "mrentabilidad_annual",
    "mcomisiones",
    "mactivos_margen",
    "mpasivos_margen",
    "mcuentas_saldo",
    "mcaja_ahorro",
    "mcuenta_corriente",
    "mpayroll",
    "mprestamos_personales",
    "mtarjeta_visa_consumo",
    "mtarjeta_master_consumo",
    "tc_msaldototal",
    "tc_mlimitecompra",
    "ctrx_quarter",
    "cproductos",
    "cliente_antiguedad",
    "cliente_edad",
    "chomebanking_transacciones",
]

# [Anotación · líneas 72–90] NO_SERIE: claves, clase y columnas auxiliares del panel que nunca entran a series
#   ni rankings; TIPOS_NUM: prefijos de los tipos numéricos de DuckDB.
# Nunca entran a series ni rankings: claves, target y columnas auxiliares del panel.
NO_SERIE = {
    "pk_cliente",
    "pk_mes",
    "mes_0",
    "numero_de_cliente",
    "foto_mes",
    "clase_ternaria",
}
TIPOS_NUM = (
    "BIGINT",
    "INTEGER",
    "DOUBLE",
    "FLOAT",
    "DECIMAL",
    "HUGEINT",
    "SMALLINT",
    "TINYINT",
)


# [Anotación · líneas 93–130] `resolver_campos`: una lista explícita (error si un nombre no existe), `curado`
#   (la lista curada menos las inexistentes y las excluidas, que se informan en el log) o `todos` (todas las
#   numéricas salvo claves y excluidas).
def resolver_campos(
    spec: str | list[str],
    curado: list[str],
    esquema: dict[str, str],
    excluidos: set[str],
    etiqueta: str,
) -> list[str]:
    """Resuelve una especificación de campos contra el esquema de `base`.

    - "curado": la lista curada, salvo columnas inexistentes (familia apagada) o excluidas.
    - "todos": todas las numéricas, salvo claves y excluidas (p. ej. drop_drift).
    - lista explícita: se respeta tal cual; un nombre inexistente es error.
    """
    if isinstance(spec, list):
        faltan = [c for c in spec if c not in esquema]
        if faltan:
            raise ValueError(f"{etiqueta}: campos inexistentes: {faltan}")
        return list(spec)
    if spec == "curado":
        usables = [c for c in curado if c in esquema and c not in excluidos]
        omitidos = [c for c in curado if c not in usables]
        if omitidos:
            log.info(
                "%s curado: se omiten %d campos no disponibles/excluidos: %s",
                etiqueta,
                len(omitidos),
                omitidos,
            )
        return usables
    if spec == "todos":
        return [
            c
            for c, t in esquema.items()
            if c not in NO_SERIE
            and c not in excluidos
            and t.upper().startswith(TIPOS_NUM)
        ]
    raise ValueError(f"{etiqueta}: valor inválido {spec!r} (curado | todos | lista)")


# [Anotación · líneas 133–146] `campos_monto`: columnas numéricas cuyo nombre empieza con m, Master_m, Visa_m
#   o tc_m (seguido de letra minúscula o guion bajo), salvo claves y excluidas.
# Montos nominales en pesos: originales m*, de las tarjetas (Master_m*, Visa_m*), consolidados
# de TC (tc_m*) y agregados de la familia 1 (m_*). Los ratios (r_*) ya son adimensionales.
_PATRON_MONTO = re.compile(r"^((Master|Visa|tc)_)?m[a-z_]")


def campos_monto(esquema: dict[str, str], excluidos: set[str]) -> list[str]:
    return [
        c
        for c, t in esquema.items()
        if _PATRON_MONTO.match(c)
        and c not in NO_SERIE
        and c not in excluidos
        and t.upper().startswith(TIPOS_NUM)
    ]
```

### competencia_01/competencia_1/pipeline/features/comportamiento.py

Familia 9 (activa sólo en el componente e034): indicadores de eventos, recency, cocientes contra el máximo reciente y un puntaje RFM, mirando como máximo 2 meses hacia atrás.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–31] Docstring con el criterio de la familia; nombre del bloque `9_comportamiento`,
#   índice de mes continuo, tres ventanas (orden; t-2..t-1; t-2..t) y tres condiciones de recency (payroll,
#   transacciones, consumo de tarjeta).
"""Familia 9: señales de comportamiento previas a la baja (literatura de churn bancario).

Eventos discretos que un árbol solo aproxima con deltas: deja de entrar el sueldo, se pierde
un producto, sube el status de una tarjeta, se vacía la cuenta, cae la actividad. Recency,
frecuencia y monto (RFM) como en Van den Poel & Larivière (2004) y Verbeke et al. (2012).

Todo mira como máximo 2 meses atrás (ventana de 3 puntos t-2..t), igual que el FE de e032:
así una fila de train (202105-202106) y una de 202108 ven la misma profundidad de historia.
Si la ventana no está completa (202103, 202104) la recency queda NULL salvo que el evento
aparezca dentro de lo disponible.

Se calcula sobre el panel denso (filas fantasma incluidas: sus montos son NULL y los
agregados null-safe de la familia 1 valen 0). Requiere fe.intrafila.tc_consolidado y agregados.
"""

from competencia_1.pipeline.features.catalogo import Catalogo

BLOQUE = "9_comportamiento"
# Índice de mes continuo: con el panel denso, diferencias de índice = meses transcurridos.
IDX = "(pk_mes // 100 * 12 + pk_mes % 100)"
VENTANAS = {
    "comp_orden": "",
    "comp_previos": "rows between 2 preceding and 1 preceding",
    "comp_3": "rows between 2 preceding and current row",
}
# (nombre, condición del evento "hay actividad" en el mes)
RECENCY = [
    ("meses_desde_payroll", "ifnull(cpayroll_trx, 0) + ifnull(cpayroll2_trx, 0) > 0"),
    ("meses_desde_trx", "c_trx_total > 0"),
    ("meses_desde_consumo_tc", "tc_mconsumototal > 0"),
]


# [Anotación · líneas 34–47] `ventanas_comportamiento` arma las definiciones de ventana; `_recency` da los
#   meses desde el último mes en que se cumple la condición dentro de t-2..t, 3 si no ocurrió y la ventana tiene
#   3 filas, y nulo en otro caso.
def ventanas_comportamiento() -> list[str]:
    return [
        f"{n} as (partition by pk_cliente order by pk_mes {marco})"
        for n, marco in VENTANAS.items()
    ]


def _recency(cond: str) -> str:
    """Meses desde el último mes con `cond` en t-2..t; 3 si no ocurrió con la ventana completa."""
    ultimo = f"max(case when {cond} then {IDX} end) over comp_3"
    return (
        f"case when {ultimo} is not null then {IDX} - {ultimo} "
        f"when count(*) over comp_3 = 3 then 3 end"
    )


# [Anotación · líneas 50–71] `sql_comportamiento_series` (primera parte): f_perdio_payroll (hubo payroll en
#   t-1 o t-2 y no en t), n_productos_perdidos (contra el máximo de t-1 y t-2) y f_visa_status_sube /
#   f_master_status_sube (status mayor que el máximo de t-1 y t-2).
def sql_comportamiento_series(cat: Catalogo) -> str:
    """Fragmento del SELECT de `series` (ventanas sobre el panel)."""
    payroll = "if(ifnull(cpayroll_trx, 0) + ifnull(cpayroll2_trx, 0) > 0, 1, 0)"
    frag = cat.reg(
        BLOQUE,
        "f_perdio_payroll",
        f"if(max({payroll}) over comp_previos = 1 and {payroll} = 0, 1, 0)",
        "tenía sueldo en t-1 o t-2 y en t no",
    )
    frag += cat.reg(
        BLOQUE,
        "n_productos_perdidos",
        "greatest(max(c_productos_contratados) over comp_previos - c_productos_contratados, 0)",
        "familias de producto perdidas contra el máximo de t-1/t-2",
    )
    for tc in ("Visa", "Master"):
        frag += cat.reg(
            BLOQUE,
            f"f_{tc.lower()}_status_sube",
            f"if(ifnull({tc}_status, 0) > max(ifnull({tc}_status, 0)) over comp_previos, 1, 0)",
            f"{tc}_status empeora contra t-1/t-2 (camino al cierre)",
        )
# [Anotación · líneas 72–94] Las tres recency, r_saldo_vs_max y r_activos_vs_max (valor / máximo de t-2..t) y
#   racha_caida_ctrx (0, 1 o 2 meses consecutivos de caída de ctrx_quarter).
    for nombre, cond in RECENCY:
        frag += cat.reg(BLOQUE, nombre, _recency(cond), f"recency: {cond}")
    frag += cat.reg(
        BLOQUE,
        "r_saldo_vs_max",
        "ratio_seguro(mcuentas_saldo, nullif(greatest(max(mcuentas_saldo) over comp_3, 0), 0))",
        "drenaje: saldo / máximo de t-2..t",
    )
    frag += cat.reg(
        BLOQUE,
        "r_activos_vs_max",
        "ratio_seguro(m_activos_totales, nullif(max(m_activos_totales) over comp_3, 0))",
        "drenaje: activos / máximo de t-2..t",
    )
    frag += cat.reg(
        BLOQUE,
        "racha_caida_ctrx",
        "if(ctrx_quarter < lag(ctrx_quarter, 1) over comp_orden, 1, 0)"
        " + if(ctrx_quarter < lag(ctrx_quarter, 1) over comp_orden"
        " and lag(ctrx_quarter, 1) over comp_orden < lag(ctrx_quarter, 2) over comp_orden, 1, 0)",
        "meses consecutivos con caída de ctrx_quarter (0-2)",
    )
    return frag


# [Anotación · líneas 97–104] `sql_comportamiento_mes`: r_transf_emitidas_recibidas, cociente entre
#   transferencias emitidas y recibidas del mes.
def sql_comportamiento_mes(cat: Catalogo) -> str:
    """Fragmento intra-fila (no necesita historia)."""
    return cat.reg(
        BLOQUE,
        "r_transf_emitidas_recibidas",
        "ratio_seguro(mtransferencias_emitidas, mtransferencias_recibidas)",
        "salida de fondos por transferencias",
    )


# [Anotación · líneas 107–118] `sql_comportamiento_final`: rfm_score, suma de tres quintiles dentro del mes
#   calculados con percent_rank: recency de transacciones (invertida), ctrx_quarter y mcuentas_saldo.
def sql_comportamiento_final(cat: Catalogo) -> str:
    """RFM por quintiles dentro del mes (sobre filas reales, en el SELECT final)."""
    q = "least(1 + floor(5 * percent_rank() over (partition by foto_mes order by {e})), 5)"
    r = q.format(e="ifnull(meses_desde_trx, 3) desc")
    f = q.format(e="ifnull(ctrx_quarter, 0)")
    m = q.format(e="ifnull(mcuentas_saldo, 0)")
    return cat.reg(
        BLOQUE,
        "rfm_score",
        f"({r} + {f} + {m})::INTEGER",
        "recency + frecuencia (ctrx_quarter) + monto (mcuentas_saldo), quintiles del mes",
    )
```

### competencia_01/competencia_1/pipeline/features/query.py

Ensambla la query SQL de variables en el orden panel → base → escala → series → reales → selección final, y rechaza cualquier query que contenga `lead(` o `following`.

El código completo está en https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/query.py.txt

### competencia_01/competencia_1/pipeline/features/rankings.py

Rankings dentro del mes (percent_rank y decil) y reescalado de los montos a una escala relativa por mes (modo `rank_cero_fijo`, usado por el componente e033, y modo `deflactado`, sin uso en la entrega).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–15] Docstring: los rankings se calculan sobre filas reales, dejan nulo lo nulo y el
#   decil se deriva de percent_rank en lugar de ntile.
"""Familia 2: rankings intra-mes (defensa contra data drifting).

La inflación mueve todos los montos nominales pero no la posición relativa del
cliente frente a sus contemporáneos. Se calculan sobre filas REALES (después de
descartar las fantasma) y son NULL-safe: un NULL queda NULL en vez de recibir el
ranking más alto (comportamiento por defecto de `percent_rank` en z402).

El decil NO usa `ntile(10)`: ntile reparte los empates según el orden físico de las
filas, y con variables muy repetidas (ctrx_quarter) daba deciles distintos entre
corridas. Con `percent_rank` los valores iguales caen siempre en el mismo decil.
"""

from competencia_1.pipeline.config import FE
from competencia_1.pipeline.features.catalogo import Catalogo


# [Anotación · líneas 17–38] `sql_rankings`: por cada campo genera pr_<campo> = percent_rank dentro del mes
#   (nulo si el valor es nulo) y, para los campos de `ntile10`, d10_<campo> = decil de 1 a 10 derivado del
#   percent_rank.
def sql_rankings(fe: FE, campos: list[str], cat: Catalogo) -> str:
    if not fe.rankings.activo:
        return ""
    frag = ""
    for c in campos:
        frag += cat.reg(
            "2_rank_intrames",
            f"pr_{c}",
            f"case when {c} is null then null else "
            f"percent_rank() over (partition by foto_mes, ({c} is null) order by {c}) end",
            f"{c} — posición relativa dentro del mes",
        )
    for c in fe.rankings.ntile10:
        frag += cat.reg(
            "2_rank_intrames",
            f"d10_{c}",
            f"case when {c} is null then null else "
            f"least(1 + floor(10 * percent_rank() over "
            f"(partition by foto_mes, ({c} is null) order by {c})), 10)::INTEGER end",
            f"{c} — decil dentro del mes (por percent_rank: empates -> mismo decil)",
        )
    return frag


# [Anotación · líneas 41–56] LOTE_MONTOS = 5 y `_expresion_monto`: en `rank_cero_fijo`, nulo queda nulo, 0
#   queda 0, los positivos toman cume_dist por mes y signo y los negativos −cume_dist en orden descendente; en
#   `deflactado`, monto / mediana de los montos positivos del mes.
# Columnas de monto que se escalan por consulta. Cada ventana ordenada arrastra todas las
# columnas ya calculadas, así que el costo crece más que linealmente con el tamaño del lote:
# con 91 montos en una sola consulta tardaba >1 h; en lotes de 5 son ~10 s (mismos valores).
LOTE_MONTOS = 5


def _expresion_monto(modo: str) -> str:
    if modo == "rank_cero_fijo":
        return (
            "case when {c} is null then null when {c} = 0 then 0 "
            "when {c} > 0 then cume_dist() over (partition by pk_mes, sign({c}) order by {c}) "
            "else -cume_dist() over (partition by pk_mes, sign({c}) order by {c} desc) end"
        )
    if modo == "deflactado":
        return "{c} / nullif(median(case when {c} > 0 then {c} end) over (partition by pk_mes), 0)"
    raise ValueError(f"fe.montos inválido: {modo}")


# [Anotación · líneas 59–99] `materializar_montos`: copia los montos de las filas reales a una tabla temporal,
#   calcula la escala relativa en lotes de 5 columnas, une los lotes en la tabla `rel` y devuelve la cláusula
#   `replace` que sustituye cada monto por su versión reescalada.
def materializar_montos(con, modo: str, campos: list[str]) -> str:
    """Crea la tabla temporal `rel` (pk_cliente, pk_mes + los montos en escala relativa, solo
    filas reales) y devuelve la cláusula `replace` que la aplica sobre `base`.

    Lleva los montos a una escala comparable entre meses; se aplica sobre el panel, antes de
    lags, deltas y ventanas, que quedan expresados en la escala nueva. Las filas fantasma
    quedan en NULL (no están en `rel`).
    - rank_cero_fijo: negativos -> [-1, 0), cero -> 0, positivos -> (0, 1], por mes y por
      signo con `cume_dist` (los empates reciben el mismo valor: determinístico).
    - deflactado: monto / mediana de los montos positivos del mes (quita inflación y aguinaldo
      sin perder la forma de la distribución).
    Requiere la vista `base` en `con`. Devuelve "" si no hay nada que escalar.
    """
    if modo == "crudo" or not campos:
        return ""
    expr = _expresion_monto(modo)
    con.execute(
        "create or replace temp table montos_crudos as select pk_cliente, pk_mes, "
        + ", ".join(campos)
        + " from base where mes_0 = 1"
    )
    lotes = [campos[i : i + LOTE_MONTOS] for i in range(0, len(campos), LOTE_MONTOS)]
    for j, lote in enumerate(lotes):
        partes = ", ".join(f"{expr.format(c=c)} as {c}" for c in lote)
        con.execute(
            f"create or replace temp table montos_lote_{j} as "
            f"select pk_cliente, pk_mes, {partes} from montos_crudos"
        )
    seleccion = ", ".join(f"l{j}.{c}" for j, lote in enumerate(lotes) for c in lote)
    uniones = " ".join(
        f"join montos_lote_{j} l{j} using (pk_cliente, pk_mes)"
        for j in range(1, len(lotes))
    )
    con.execute(
        "create or replace temp table rel as select l0.pk_cliente, l0.pk_mes, "
        f"{seleccion} from montos_lote_0 l0 {uniones}"
    )
    con.execute("drop table montos_crudos")
    for j in range(len(lotes)):
        con.execute(f"drop table montos_lote_{j}")
    return " replace (" + ", ".join(f"rel.{c} as {c}" for c in campos) + ")"
```

### competencia_01/competencia_1/pipeline/features/catalogo.py

Catálogo de variables: cada fragmento de SQL se registra al generarse y el conjunto se guarda como CSV.

El código completo está en https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/catalogo.py.txt

### competencia_01/competencia_1/pipeline/features/__init__.py

Etapa features: construye el parquet de variables con una única query de DuckDB, lo guarda en una caché identificada por un hash de la configuración y verifica la salida.

El código completo está en https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/__init__.py.txt

### competencia_01/competencia_1/pipeline/features/intrafila.py

Familia 1: variables calculadas dentro de la misma fila (sumas Master + Visa, fechas de tarjetas, agregados, cocientes e indicadores).

El código completo está en https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/intrafila.py.txt

### competencia_01/competencia_1/pipeline/features/macros.py

Tres macros SQL de DuckDB usadas por las demás familias de variables.

El código completo está en https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/macros.py.txt

### competencia_01/competencia_1/pipeline/features/temporales.py

Familias históricas calculadas sobre el panel denso cliente × mes: lags, estadísticos de ventana, pendiente, historia en el panel, deltas y cociente contra la media móvil.

El código completo está en https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/competencia_1/pipeline/features/temporales.py.txt

### competencia_01/config/semillas.py

Lista de las 5 semillas del proyecto, de la que el pipeline toma las dos primeras para los modelos finales.

El código completo está en https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/config/semillas.py.txt

### competencia_01/dmeyf/metrics.py

Cálculo de la ganancia: constantes, ganancia por umbral, curva de ganancia acumulada y máximo de la curva suavizada. Las constantes del archivo son 1.072.500 y 27.500; el README menciona +780.000 / −20.000.

El código completo está en https://emavaldez.github.io/postmortem/fuentes/pfranzd/competencia_01/dmeyf/metrics.py.txt


## Explicaciones del alumno (texto original)

### README.md

> # dmeyf2026-entregas
>
> Entregas de las competencias de *Data Mining en Economía y Finanzas* (UBA, 2026). Cada carpeta
> contiene todo lo necesario para replicar **exactamente** el archivo entregado: código, entorno
> con versiones fijas, hiperparámetros, modelos y la optimización que los originó. Los datasets de
> la competencia no se suben (el script los descarga).
>
> | Competencia | Carpeta | Entrega | Envíos | sha256 | Público |
> |---|---|---|---|---|---|
> | Competencia 01 | [`competencia_01/`](competencia_01/) | ens04_e032_e033_e034 | 10500 | `385da7093ab1…` | 110.17 M |
>
> Instrucciones de cada entrega: el `README.md` dentro de su carpeta.

### competencia_01/README.md

> # Competencia 01 — entrega final: ensamble ens04_e032_e033_e034 con 10500 envíos
>
> Esta carpeta contiene todo lo necesario para replicar **exactamente** el archivo que se subió
> como entrega final de la competencia. La entrega es un **ensamble**: el promedio de los rankings
> de 3 modelos (cada uno, a su vez, un ensamble de LightGBM con varios conjuntos de
> hiperparámetros y semillas). Cada componente está en su propia subcarpeta con su configuración,
> sus hiperparámetros y sus modelos entrenados.
>
> | | |
> |---|---|
> | Archivo entregado | `20261011-091551_ens04_e032_e033_e034_e10500.csv` (solo `numero_de_cliente`, sin encabezado, 10500 filas) |
> | sha256 | `385da7093ab1e93b894016de3cb537460dc48ee0cc2befdce943ddbae850d5df` |
> | Puntaje público | 110.1650 M |
> | Período objetivo | 202108 |
>
> El dataset de la competencia **no está en el repositorio**: el script lo descarga solo desde la
> URL pública de la cátedra (`competencia_01_crudo.csv`).
>
> ## Componentes del ensamble
>
> | # | Experimento | Modelos | Peso | Run de origen |
> |---|---|---|---|---|
> | 0 | `e032_expansiva_auc_topk` | 24 | 1 | `20261009-232755_e032_expansiva_auc_topk` |
> | 1 | `e033_montos_rank_cero_fijo` | 24 | 1 | `20261011-023622_e033_montos_rank_cero_fijo` |
> | 2 | `e034_comportamiento` | 24 | 1 | `20261011-041115_e034_comportamiento` |
>
> Combinación: cada componente predice la probabilidad de BAJA+2 en 202108; se convierte en su
> rank normalizado dentro del mes (`competencia_1/pipeline/ensamble.py`, método `rank`), se
> promedian los rankings y se envían los 10500 clientes de mayor valor.
>
> ## Cómo replicarla
>
> Hace falta Python 3.11 y unos 16 GB de RAM. Hay tres niveles; en todos se reproduce cada
> componente (y se verifica el sha256 de su propio CSV), se arma el ensamble y se compara el sha256
> del CSV final con el de arriba (`[ensamble] RESULTADO: OK, coincide`):
>
> | Modo | Qué rehace | Tiempo aprox. |
> |---|---|---|
> | `predecir` (default) | Datos y features desde el crudo, y **predice** con los 72 modelos ya entrenados | ~1 h |
> | `entrenar` | Lo anterior, pero **reentrena** los 72 modelos con los hiperparámetros de cada componente | ~4 h |
> | `completo` | **Todo, incluida la optimización de hiperparámetros** de cada componente (Optuna, 180 trials en total) | ~5 h |
>
> **Linux o VM de GCP:**
>
> ```bash
> git clone https://github.com/pfranzd/dmeyf2026-entregas.git && cd dmeyf2026-entregas/competencia_01
> bash reproducir.sh              # o: bash reproducir.sh entrenar | bash reproducir.sh completo
> ```
>
> **Windows (PowerShell):**
>
> ```powershell
> git clone https://github.com/pfranzd/dmeyf2026-entregas.git; cd dmeyf2026-entregas\competencia_01
> py -3.11 -m venv .venv
> .venv\Scripts\python -m pip install --upgrade pip
> .venv\Scripts\python -m pip install -r requirements-lock.txt
> $env:ENTREGA_MODO = "predecir"      # o "entrenar" / "completo"
> .venv\Scripts\python entrega.py
> ```
>
> También se puede abrir `entrega.ipynb` (es el mismo código que `entrega.py`) y ejecutarlo
> completo; el modo se elige en la segunda celda.
>
> El CSV del ensamble queda en `work/entrega/runs/<fecha>_ensamble/submits/` y los de cada
> componente en `work/entrega/runs/<fecha>_entrega/submits/`.
>
> ## Entorno
>
> - `requirements-lock.txt`: **versiones exactas** de todas las librerías (incluidas las
>   transitivas) con las que se generó la entrega. `requirements.txt` lista solo las directas.
> - Python 3.11 (`.python-version`). El script avisa si alguna versión instalada difiere.
> - La igualdad byte a byte depende de las versiones de LightGBM y DuckDB y de
>   `lgbm.fijos.num_threads` (8) en `competencia_1/configs/base.yaml`; no los cambies.
>
> ## Qué hace cada modelo
>
> ### 0_e032_expansiva_auc_topk
>
> - LightGBM, objetivo `binary` sobre `BAJA+1 + BAJA+2`; la ganancia se mide sobre BAJA+2 (+780.000 / −20.000).
> - Features: datos originales + familias temporales (lags, deltas, ventanas, tendencia) según `competencia_1/configs/exp/e032_expansiva_auc_topk.yaml`.
> - Optimización: validación temporal con gap de 2 meses; objetivo `auc` promedio de los folds:
>   - train [202103] → validación 202105
>   - train [202103, 202104] → validación 202106
> - Undersampling de CONTINUA en la optimización: 0.25 (el modelo final entrena sin undersampling).
> - Modelo final entrenado con los meses [202103, 202104, 202105, 202106]; predice 202108.
> - Ensamble final: 12 conjuntos de hiperparámetros × 2 semillas; se promedian las probabilidades.
>
> ### 1_e033_montos_rank_cero_fijo
>
> - LightGBM, objetivo `binary` sobre `BAJA+1 + BAJA+2`; la ganancia se mide sobre BAJA+2 (+780.000 / −20.000).
> - Features: datos originales + familias temporales (lags, deltas, ventanas, tendencia) según `competencia_1/configs/exp/e033_montos_rank_cero_fijo.yaml`.
> - Optimización: validación temporal con gap de 2 meses; objetivo `auc` promedio de los folds:
>   - train [202103] → validación 202105
>   - train [202103, 202104] → validación 202106
> - Undersampling de CONTINUA en la optimización: 0.25 (el modelo final entrena sin undersampling).
> - Modelo final entrenado con los meses [202103, 202104, 202105, 202106]; predice 202108.
> - Ensamble final: 12 conjuntos de hiperparámetros × 2 semillas; se promedian las probabilidades.
>
> ### 2_e034_comportamiento
>
> - LightGBM, objetivo `binary` sobre `BAJA+1 + BAJA+2`; la ganancia se mide sobre BAJA+2 (+780.000 / −20.000).
> - Features: datos originales + familias temporales (lags, deltas, ventanas, tendencia) según `competencia_1/configs/exp/e034_comportamiento.yaml`.
> - Optimización: validación temporal con gap de 2 meses; objetivo `auc` promedio de los folds:
>   - train [202103] → validación 202105
>   - train [202103, 202104] → validación 202106
> - Undersampling de CONTINUA en la optimización: 0.25 (el modelo final entrena sin undersampling).
> - Modelo final entrenado con los meses [202103, 202104, 202105, 202106]; predice 202108.
> - Ensamble final: 12 conjuntos de hiperparámetros × 2 semillas; se promedian las probabilidades.
>
> ## De dónde salen los hiperparámetros (optimización)
>
> ### 0_e032_expansiva_auc_topk
>
> Los hiperparámetros **no están fijados a mano**: salen de una optimización bayesiana con Optuna, incluida en esta carpeta.
>
> - Estudio: `optimizacion/0_e032_expansiva_auc_topk/estudio.db` (SQLite de Optuna, 60 trials, 37 completos y 23 podados) y `optimizacion/0_e032_expansiva_auc_topk/resumen.json`.
> - La entrega usa los 12 mejores trials: #43, #41, #32, #22, #27, #44, #57, #31, #51, #42, #52, #21.
> - Para rehacerla de punta a punta: el modo `completo` (corre `competencia_1/configs/exp/e032_expansiva_auc_topk.yaml`: Optuna → mejores trials → modelos → CSV) y comprueba el sha256.
>
>
> ### 1_e033_montos_rank_cero_fijo
>
> Los hiperparámetros **no están fijados a mano**: salen de una optimización bayesiana con Optuna, incluida en esta carpeta.
>
> - Estudio: `optimizacion/1_e033_montos_rank_cero_fijo/estudio.db` (SQLite de Optuna, 60 trials, 38 completos y 22 podados) y `optimizacion/1_e033_montos_rank_cero_fijo/resumen.json`.
> - La entrega usa los 12 mejores trials: #57, #55, #59, #58, #15, #54, #14, #21, #27, #42, #56, #34.
> - Para rehacerla de punta a punta: el modo `completo` (corre `competencia_1/configs/exp/e033_montos_rank_cero_fijo.yaml`: Optuna → mejores trials → modelos → CSV) y comprueba el sha256.
>
>
> ### 2_e034_comportamiento
>
> Los hiperparámetros **no están fijados a mano**: salen de una optimización bayesiana con Optuna, incluida en esta carpeta.
>
> - Estudio: `optimizacion/2_e034_comportamiento/estudio.db` (SQLite de Optuna, 60 trials, 34 completos y 26 podados) y `optimizacion/2_e034_comportamiento/resumen.json`.
> - La entrega usa los 12 mejores trials: #53, #52, #15, #31, #14, #24, #32, #21, #51, #16, #57, #44.
> - Para rehacerla de punta a punta: el modo `completo` (corre `competencia_1/configs/exp/e034_comportamiento.yaml`: Optuna → mejores trials → modelos → CSV) y comprueba el sha256.
>
>
> ## Contenido de la carpeta
>
> ```
> entrega.py / entrega.ipynb     punto de entrada (mismo código)
> reproducir.sh                  atajo para Linux / GCP
> requirements*.txt, .python-version
> competencia_1/                 pipeline (datos → features → Optuna → modelos → CSV)
>   configs/base.yaml            defaults
>   configs/exp/*.yaml           configuración de cada experimento (optimización + final)
>   definitiva/entrega.json      el ensamble: componentes, método, pesos y sha256 esperado
>   definitiva/componentes/<i>_<experimento>/   config.yaml, params.json, entrega.json y modelos/
> dmeyf/, config/                métricas y semillas
> optimizacion/<i>_<experimento>/  evidencia de la optimización de cada componente (Optuna)
> ```
>
> ## Trazabilidad
>
> Generada el 2026-10-11 12:13 desde el repositorio de trabajo, commit `27084eb76e`, ensamble
> `20261011-091551_ens04_e032_e033_e034`. El CSV de ese ensamble coincide byte a byte con el que reproduce esta carpeta.

