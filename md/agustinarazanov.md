# Agustina Razanov — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: agustinarazanov
- Repositorio: https://github.com/agustinarazanov/dmeyf
- Link posteado: https://github.com/agustinarazanov/dmeyf
- Commit: 11ff4842a05653277d2b04f237bc94098507bd8a
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/agustinarazanov/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/agustinarazanov.json

## Resumen

Repositorio en Python con un script de reproducción (`reproducir.py`), cuatro módulos en `src/`, 86 scripts en `scripts/` (experimentos numerados c100 a c280 y dos utilidades), dos notebooks, cuatro documentos en `docs/` (entre ellos un diario de 2.156 líneas), el export de un registro de envíos en `ledger/` y los CSV enviados en `experimentos/`. Según el README, la entrega es `c241_rondas2000_ens20_14000`. El camino que la produce parte del CSV crudo, construye `clase_ternaria` con DuckDB, agrega lag 1, delta 1, lag 2 y delta 2 de las 150 variables (750 predictoras), pone `ccajas_depositos` en NULL en 202105 y deja fuera `Visa_Finiciomora` y `Master_Finiciomora`. Entrena LightGBM en 202103–202106 con clase binaria (positivo = BAJA+1 o BAJA+2, con BAJA+1 pesando 0,25), hiperparámetros fijos y 2.000 rondas, una vez por cada una de 20 semillas; promedia los rangos percentiles de las 20 predicciones sobre 202108 y escribe los 14.000 clientes de mayor promedio. `reproducir.py` rehace ese recorrido con un comando y compara el SHA-256 del archivo con el registrado; `scripts/c210_variante.py` es, según el README, el script con el que se entrenó el experimento.

**Qué entrega.** Un CSV sin encabezado con una columna de `numero_de_cliente`: los 14.000 clientes de 202108 con mayor promedio de rangos entre los 20 modelos, ordenados por id. Según el README, el archivo entregado es `experimentos/c241_rondas2000/envios_14000/c241_rondas2000_14000_ens20.csv` (SHA-256 657d747a…), enviado como un solo archivo.

**Cómo se ejecuta.** Según el README (sección 2): `pyenv local facultad` y `python reproducir.py --rondas 2000 --salida entrega_final.csv` (unas 4 horas en 8 cores). El script espera el CSV crudo en `data/competencia_01_crudo.csv`; `data` es un symlink a `../dmeyf2026/monday/data` que no se versiona.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: positivo = BAJA+1 o BAJA+2. El peso por fila es 1,0 para BAJA+2 y para los negativos y 0,25 para BAJA+1. La clase ternaria se construye desde el CSV crudo en `fe_panel.construir_base`.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** —
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código: el modelo de la entrega entrena con todas las filas de 202103–202106 (654.066 filas y 8.067 positivos según el README).
- **Calidad de datos:** `ccajas_depositos` pasa a NULL en 202105 en la columna del mes (los lags y deltas de esa variable se calculan sobre los valores sin anular, según el comentario de `construir_lags`). `Visa_Finiciomora` y `Master_Finiciomora` quedan fuera de las predictoras. `numero_de_cliente` se convierte a int64 y las filas se ordenan por cliente y mes antes de entrenar.
- **Drifting:** No se observa en el camino de la entrega: las 150 variables entran con sus valores crudos. En scripts de exploración aparecen `percent_rank` por mes (c101, c202), rank con cero fijo (c167) y división de montos por la mediana mensual (c127, c250).
- **Variables dentro del mes:** No se observa en el camino de la entrega. En scripts de exploración: 11 cocientes entre montos (c260), sumas y conteos (c261) e indicadores de negocio (c111, c115).
- **Variables históricas:** Lag 1, delta 1, lag 2 y delta 2 de cada una de las 150 variables numéricas (600 columnas nuevas en FLOAT), calculados en SQL sobre DuckDB con una ventana por cliente ordenada por `foto_mes`.
- **Selección de variables:** No hay selección en el camino de la entrega: se usan las 750 predictoras (el script lo verifica con un `assert`). En scripts de exploración: poda con canaritos (c161, c165) y entrenamiento con un subconjunto de columnas leído de un archivo (opción `--columnas` de c210).
- **Optimización de hiperparámetros:** No hay búsqueda en el camino de la entrega: los hiperparámetros están escritos en el código y el README los atribuye a una receta publicada por el profesor en Zulip. En scripts de exploración hay cuatro búsquedas con Optuna (c105, c122, c180, c220) y variantes de un hiperparámetro por vez con las opciones `--rondas`, `--hojas`, `--ff` y `--hessian` de c210.
- **Hiperparámetros finales:** objective binary, boosting gbdt, max_bin 31, min_data_in_leaf 0, feature_fraction 0,5, feature_fraction_bynode 0,2, learning_rate 0,005, num_leaves 83, min_sum_hessian_in_leaf = 12,791817 × filas / 326.184, bagging_fraction 1,0, bagging_freq 0, num_threads 8, force_col_wise y deterministic en True; 2.000 rondas.
- **Semillas:** 20: las cinco escritas en el código (261431, 269281, 429899, 560771, 749401) más 15 obtenidas con `np.random.seed(261431)` y `np.random.choice(1_000_000, size=15, replace=False)`.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio de los rangos percentiles (`rank(pct=True)`) de las predicciones de los 20 modelos sobre 202108; no promedia probabilidades.
- **Corte:** Cantidad fija de 14.000 clientes (constante `CORTE`). Según el README, el valor sale del pico de la curva de ganancia pública medida con 20 archivos por punto y del regret calculado sobre 202106 por `scripts/c216_captura_foldB.py` (minimax en 13.500, regret medio mínimo en 14.000 según el diario).
- **Validación:** `reproducir.py` no valida. `scripts/c216_captura_foldB.py` entrena en 202103–202104 y evalúa en 202106 la captura de BAJA+2 y la ganancia por corte, y calcula el regret bajo cuatro prevalencias. `scripts/c222_fold_A_control.py` entrena en 202103 y evalúa en 202105 la receta frente a cinco trials de Optuna. El README declara además comparaciones en el leaderboard público con 20 archivos (una semilla por archivo) y las mismas semillas y corte.
- **Salidas:** Un CSV de una columna sin encabezado con 14.000 `numero_de_cliente` ordenados por id (por defecto `entrega_final.csv`); el script imprime el SHA-256 y lo compara con el registrado. Si no existen, deja en `data/` los parquet `competencia_01.parquet` y `competencia_01_lags12.parquet`. El pipeline de experimentos (c210) guarda además un modelo y un parquet de scores por semilla y un CSV por semilla y por corte.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)
- Incluye código para enviar al bot o a la plataforma (`proceso.automatizacion_envios`)
- El repositorio declara el uso de asistentes de IA (`proceso.uso_de_ia_declarado`)

## Técnicas sólo exploradas

- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Clase artificial o pseudo-etiquetas para meses sin clase (`clase.clase_artificial`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Estandarización o normalización por mes (`drifting.estandarizacion_por_mes`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Mínimos y máximos de ventana (`variables.min_max_ventana`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Optuna (`hiperparametros.optuna`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README: entorno pyenv `facultad` con Python 3.14, duckdb 1.5.5, lightgbm 4.7.0, pandas 2.3.3 y numpy 2.5.3; unas 4 horas en 8 cores, con `num_threads` 8, `deterministic=True` y `force_col_wise=True`. `data/` es un symlink a `../dmeyf2026/monday/data` que no se versiona. CLAUDE.md agrega un segundo entorno pyenv `zulip` para `scripts/enviar.py` y un contenedor Docker `zulip-postgres` para el registro de envíos.

## Pasos del camino de la entrega

1. **Parámetros de la corrida.** Se fijan las rutas bajo `data/`, los SHA-256 esperados, los meses de entrenamiento (202103 a 202106), el mes a predecir (202108), el peso 0,25 de BAJA+1, las 2.000 rondas, el corte en 14.000, las 20 semillas y la lista de columnas que no entran al modelo. (`reproducir.py` líneas 44–67)
2. **Clase ternaria desde el CSV crudo.** Si no existe el parquet base, DuckDB lee el CSV crudo, arma la grilla cliente × mes y etiqueta cada fila según la presencia del cliente uno y dos meses después: BAJA+2, BAJA+1 o CONTINUA. Agrega cinco columnas a nivel cliente (`mes_ultimo`, `meses_historia`, `es_baja`, `mes_baja`, `k`) que después se descartan. (`reproducir.py` líneas 114–118; `src/fe_panel.py` líneas 74–123; `src/fe_panel.py` líneas 126–158)
3. **Lags y deltas de orden 1 y 2 de todas las variables.** Para cada una de las 150 columnas numéricas se generan el valor del mes anterior, la diferencia con él, el valor de dos meses atrás y la diferencia con él, con una ventana por cliente. En la misma consulta `ccajas_depositos` pasa a NULL en 202105. El resultado se guarda en `competencia_01_lags12.parquet`. (`reproducir.py` líneas 90–111; `src/fe_panel.py` líneas 216–238)
4. **Carga, tipos y orden de filas.** Se lee el parquet con pandas, se descartan las columnas de baja, `numero_de_cliente` pasa a int64 y las filas se ordenan por cliente y mes. (`reproducir.py` líneas 119–127)
5. **Matriz de entrenamiento, clase binaria y pesos.** Se verifican 750 predictoras y 983.061 filas. Con las filas de 202103–202106 se arma `y` = 1 para BAJA+1 o BAJA+2 y el peso por fila (0,25 para BAJA+1, 1,0 para el resto). Las filas de 202108 quedan aparte con sus ids. (`reproducir.py` líneas 138–151)
6. **Hiperparámetros fijos.** Los hiperparámetros de LightGBM están escritos en una función; `min_sum_hessian_in_leaf` se escala con la cantidad de filas de entrenamiento (12,791817 × filas / 326.184). (`reproducir.py` líneas 70–81)
7. **Semillas.** Las cinco semillas propias más 15 sorteadas con el generador de numpy inicializado en 261431. (`reproducir.py` líneas 84–87)
8. **Entrenamiento de 20 modelos y predicción sobre 202108.** Por cada semilla se entrena un LightGBM de 2.000 rondas con un `lgb.Dataset` nuevo, se predice sobre 202108 y la predicción se convierte en rango percentil. (`reproducir.py` líneas 153–163)
9. **Ensamble por rango y corte en 14.000.** Se promedian los rangos de los 20 modelos y se toman los 14.000 clientes de mayor promedio, con orden estable para los empates. (`reproducir.py` líneas 164–166; `src/competencia.py` líneas 226–229)
10. **Escritura y verificaciones del archivo.** Los ids se escriben ordenados, como enteros y sin encabezado. El archivo se relee para verificar que no tenga notación científica y que tenga 14.000 filas. `verificar_seleccion` compara, entre elegidos y no elegidos de 202108, la proporción con `ctrx_quarter` en cero, con saldo negativo y sin sueldo, y corta la ejecución si ningún cociente llega a 2. (`reproducir.py` líneas 166–173; `src/competencia.py` líneas 264–311)
11. **Comparación del SHA-256.** Se calcula el SHA-256 del archivo y se compara con el registrado para 2.000 rondas (657d747a…); el script imprime si coincide y si es la entrega final. (`reproducir.py` líneas 174–184)
12. **El mismo recorrido en el pipeline de experimentos.** Según el README, el experimento c241 se entrenó con `scripts/c210_variante.py`: carga el parquet con lags generado por `scripts/c200_lags_todo.py`, usa la receta y las semillas definidas en `scripts/c201_receta_lags.py`, guarda un modelo y un parquet de scores por semilla y escribe, por corte, un CSV por semilla y uno del ensamble (`<nombre>_<corte>_ens<n>.csv`). (`scripts/c200_lags_todo.py` líneas 46–62; `scripts/c201_receta_lags.py` líneas 46–62; `scripts/c210_variante.py` líneas 87–115; `src/competencia.py` líneas 160–180)
13. **Medición local citada para el corte.** `scripts/c216_captura_foldB.py` entrena la receta en 202103–202104, calcula en 202106 la captura de BAJA+2 y la ganancia para cortes de 8.000 a 16.000 y el regret de cada corte bajo cuatro prevalencias. El comentario de la constante `CORTE` en `reproducir.py` cita ese resultado y la meseta pública. (`scripts/c216_captura_foldB.py` líneas 21–48; `reproducir.py` líneas 59–59)
14. **Registro y envío al bot.** `scripts/enviar.py` registra el submit en PostgreSQL con su hipótesis y, con `--enviar`, sube los CSV al bot de Zulip y guarda la respuesta. Según el diario, el archivo del ensamble de c241 a 14.000 se reenvió como último submit el 10-oct. (`scripts/enviar.py` líneas 73–129; `src/registro.py` líneas 210–241; `docs/diario_competencia.md` líneas 2136–2144)

## Archivos

- `reproducir.py` · principal · Python · 188 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/reproducir.py.txt) — Script que el README indica para reproducir la entrega: va del CSV crudo al CSV de 14.000 clientes (clase, lags y deltas, 20 modelos LightGBM de 2.000 rondas, ensamble por rango) y compara el SHA-256 del resultado con el registrado.
- `README.md` · explicacion · Markdown · 152 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/README.md.txt) — Presentación de la entrega en seis secciones: tabla con las piezas (datos, variables, columnas excluidas, clase, hiperparámetros, semillas, ensamble, corte y archivo entregado con su SHA-256), comando para reproducir, cómo se midió (tablas de ganancia pública por cambio, por corte y por variante), validación interna, lo que no funcionó, trazabilidad y fuentes. Declara 103,79 de ganancia pública para el archivo entregado.
- `CLAUDE.md` · explicacion · Markdown · 81 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/CLAUDE.md.txt) — Mapa del repositorio (árbol de carpetas con el contenido de cada una), siete «reglas de la casa» sobre envíos, persistencia de modelos y scores, reproducibilidad y comparaciones con 20 archivos, los dos entornos pyenv y dos reglas de feature engineering fechadas el 9-oct. Las reglas se refieren a «la usuaria» en tercera persona; el archivo dice que el diario de `docs/` «es el `CLAUDE.md` histórico», y el diario menciona una cuenta bot de Zulip llamada `Claude` usada para archivar mensajes.
- `docs/pistas_profesor.md` · explicacion · Markdown · 138 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/docs/pistas_profesor.md.txt) — Recopilación de mensajes de Zulip del profesor y de tutores, con ids de mensaje: la receta de variables e hiperparámetros, indicaciones sobre drift y variables, una tabla de ganancia pública frente a privada, canaritos, pseudo-etiquetado y las reglas de entrega y cierre.
- `docs/backlog_ideas.md` · explicacion · Markdown · 131 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/docs/backlog_ideas.md.txt) — Lista de ideas con fundamento, costo y estado: seis propuestas del 7-oct, ideas B1 a B17 con el resultado público que el documento declara para cada una, una lista de lo descartado con medición y una sección de deuda técnica.
- `docs/diario_competencia.md` · explicacion · Markdown · 2156 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/docs/diario_competencia.md.txt) — Diario de 2.156 líneas con entradas fechadas del 3 al 10 de octubre de 2026: reglas del bot, observaciones sobre los datos, el resultado público que el diario declara para cada experimento, secciones tituladas «RETRACTACIÓN» que corrigen conclusiones anteriores, bugs encontrados, la decisión del corte y el registro del reenvío final.
- `docs/diagnostico_fe.md` · explicacion · Markdown · 246 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/docs/diagnostico_fe.md.txt) — Informe fechado el 2026-10-04 sobre tres rondas de variables nuevas que no cambiaron la ganancia en los folds: tablas de clientes que cruzan el corte, correlación entre rankings, bootstrap de clientes y diferencia de AUC pareada por semilla.
- `scripts/c134.py` · secundario · Python · 40 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c134.py.txt)
- `scripts/c141.py` · secundario · Python · 38 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c141.py.txt)
- `scripts/c108_meses.py` · secundario · Python · 83 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c108_meses.py.txt)
- `scripts/c111_v101.py` · secundario · Python · 85 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c111_v101.py.txt)
- `scripts/c220_optuna_receta.py` · secundario · Python · 98 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c220_optuna_receta.py.txt) — Búsqueda con Optuna (TPE, sqlite) sobre el dataset con lags: num_leaves 16–256, feature_fraction 0,3–0,7, feature_fraction_bynode 0,1–0,5 y hessiano por fila. El objetivo es el AUC medio en dos folds (202103–202104→202106 con BAJA+2 y 202103–202105→202107 con BAJA+1), con early stopping de 150 rondas y tope de 2.500.
- `scripts/c160_corte_privado.py` · secundario · Python · 129 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c160_corte_privado.py.txt)
- `scripts/c113_sonda.py` · secundario · Python · 128 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c113_sonda.py.txt)
- `scripts/c130.py` · secundario · Python · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c130.py.txt)
- `scripts/c110_decaimiento.py` · secundario · Python · 85 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c110_decaimiento.py.txt)
- `scripts/c106_revalidacion.py` · secundario · Python · 125 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c106_revalidacion.py.txt)
- `scripts/c114.py` · secundario · Python · 30 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c114.py.txt)
- `scripts/c145.py` · secundario · Python · 35 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c145.py.txt)
- `scripts/c171.py` · secundario · Python · 47 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c171.py.txt)
- `scripts/c240_pu_202107.py` · secundario · Python · 112 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c240_pu_202107.py.txt) — Agrega 202107 al entrenamiento: los BAJA+1 de ese mes entran como positivos con peso 0,25, se excluyen los clientes sin BAJA+1 que quedan entre los 2.500 primeros del ranking de cinco modelos de c201 y el resto entra como negativo.
- `scripts/c144.py` · secundario · Python · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c144.py.txt)
- `scripts/c170.py` · secundario · Python · 38 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c170.py.txt)
- `scripts/c222_fold_A_control.py` · secundario · Python · 61 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c222_fold_A_control.py.txt) — Entrena la receta y los cinco trials de mayor AUC de c220 en 202103 con una semilla y 1.000 rondas, y reporta AUC y ganancia a 8.000, 10.000 y 14.000 envíos en 202105.
- `scripts/c261_agregados.py` · secundario · Python · 126 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c261_agregados.py.txt) — Agrega 10 sumas de montos, 5 conteos (canales, productos activos, seguros, tarjetas en cierre, transacciones por canal), 5 rachas de fotos consecutivas y 8 variaciones relativas frente al mes anterior; sumas y conteos llevan lags y deltas 1 y 2.
- `scripts/c150.py` · secundario · Python · 51 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c150.py.txt)
- `scripts/c135.py` · secundario · Python · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c135.py.txt)
- `scripts/c102_comparacion.py` · secundario · Python · 139 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c102_comparacion.py.txt)
- `scripts/c174.py` · secundario · Python · 27 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c174.py.txt)
- `scripts/c140.py` · secundario · Python · 49 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c140.py.txt)
- `scripts/c280_verificar_semilla.py` · secundario · Python · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c280_verificar_semilla.py.txt) — Entrena una semilla (por defecto 269281, 2.000 rondas) con las funciones de `reproducir.py` y compara sus predicciones sobre 202108 con el parquet de scores guardado del experimento c241: imprime la diferencia absoluta máxima y cuántos ids cambian entre los 14.000 primeros.
- `scripts/canaritos_sobrevivientes.json` · configuracion · JSON · 450 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/canaritos_sobrevivientes.json.txt) — Salida de `c161_canaritos.py` sobre `competencia_01_fe.parquet`: parámetros (ratio 0,2, 4 desvíos, cinco semillas), 186 variables sobrevivientes de 223, votos por variable y diagnóstico por semilla.
- `scripts/c250_comision_deflactada.py` · secundario · Python · 63 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c250_comision_deflactada.py.txt) — Divide `mcomisiones_mantenimiento` y `mcomisiones` por su mediana mensual entre valores positivos y recalcula sus lags y deltas sobre el parquet con lags.
- `scripts/c165_barrido_poda.py` · secundario · Python · 118 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c165_barrido_poda.py.txt) — Calcula la importancia con canaritos en cinco semillas, deriva conjuntos de variables para cinco umbrales y evalúa cada conjunto en dos folds a 9.000 envíos con diez semillas, frente a las 150 columnas base con Wilcoxon pareado.
- `scripts/c100_esqueleto.py` · secundario · Python · 160 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c100_esqueleto.py.txt) — Primera corrida de punta a punta: 150 columnas, clase BAJA+2 sola, 45 hojas, learning_rate 0,0077, min_data_in_leaf 174 y 250 rondas. Valida en dos folds (202103→202105 y 202103–202104→202106) con cinco semillas, elige el corte por minimax del regret, simula el sorteo público del 25%, entrena en 202103–202106 con tres semillas, escribe un CSV por semilla y registra el experimento y el submit.
- `scripts/c101_dataset.py` · secundario · Python · 74 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c101_dataset.py.txt) — Genera `competencia_01_fe.parquet`: lag 1, delta 1 y pendiente (`regr_slope`) de 34 campos y `percent_rank` dentro del mes de las columnas cuyo nombre empieza con `m`.
- `scripts/c131_historico.py` · secundario · Python · 99 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c131_historico.py.txt) — Genera `competencia_01_hist.parquet`: para 20 campos calcula el cociente contra el promedio de los tres meses previos, la diferencia de diferencias, el desvío relativo y el cociente contra el máximo de los tres meses previos.
- `scripts/c210_variante.py` · principal · Python · 119 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c210_variante.py.txt) — Script parametrizado que entrena una variante (dataset, hiperparámetros, clase, meses, rondas, columnas) y escribe envíos por semilla y del ensamble para cada corte. El README le atribuye el entrenamiento del experimento c241 (20 semillas, 2.000 rondas); la línea de comando usada no figura en el repositorio. Los experimentos c211–c215, c241–c249, c262–c265 y c290–c292 que nombra el README no tienen script propio en `scripts/`.
- `scripts/c260_proporciones.py` · secundario · Python · 82 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c260_proporciones.py.txt) — Agrega 11 cocientes entre montos (uso del límite de tarjetas, saldo, préstamo y consumo sobre sueldo, pago y pago mínimo sobre saldo de Visa, entre otros) con sus lag 1, delta 1, lag 2 y delta 2: 55 columnas.
- `scripts/c121_productos.py` · secundario · Python · 129 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c121_productos.py.txt)
- `scripts/c125_segundo.py` · secundario · Python · 86 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c125_segundo.py.txt)
- `scripts/c202_lags_rank.py` · secundario · Python · 66 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c202_lags_rank.py.txt) — Genera `competencia_01_lagsrank.parquet`: reemplaza cada monto por su `percent_rank` dentro del mes y calcula lag 1, delta 1, lag 2 y delta 2 sobre esa versión.
- `scripts/c109_recencia.py` · secundario · Python · 89 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c109_recencia.py.txt)
- `scripts/c169.py` · secundario · Python · 29 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c169.py.txt)
- `scripts/c138.py` · secundario · Python · 32 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c138.py.txt)
- `scripts/c119_foldC.py` · secundario · Python · 100 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c119_foldC.py.txt)
- `scripts/c271_mezcla_h1.py` · secundario · Python · 52 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c271_mezcla_h1.py.txt) — Mezcla, semilla a semilla, los rangos de c241 con los de un modelo de clase BAJA+1 entrenado hasta 202107 (c270), con peso 0,3 por defecto para este último, y escribe cinco CSV a 14.000.
- `scripts/c128.py` · secundario · Python · 40 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c128.py.txt)
- `scripts/c122_busqueda_limpia.py` · secundario · Python · 127 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c122_busqueda_limpia.py.txt) — La misma búsqueda de c105 con las cinco particiones hechas por cliente (`GroupShuffleSplit`) en lugar de por fila.
- `scripts/c216_captura_foldB.py` · principal · Python · 51 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c216_captura_foldB.py.txt) — Medición local que el README cita como origen del corte: entrena la receta en 202103–202104, evalúa en 202106 contra BAJA+2 y calcula captura, ganancia por corte y regret bajo cuatro prevalencias.
- `scripts/c124_sin_marzo.py` · secundario · Python · 98 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c124_sin_marzo.py.txt) — Compara entrenar con y sin 202103 en dos folds (validación 202106 con BAJA+2 y 202107 con BAJA+1) a cuatro cortes y con diez semillas, con Wilcoxon pareado.
- `scripts/c200_lags_todo.py` · principal · Python · 68 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c200_lags_todo.py.txt) — Genera `data/competencia_01_lags12.parquet` con lag 1, delta 1, lag 2 y delta 2 de todas las predictoras; el README lo cita como origen de las variables de la entrega. Su comentario indica que esta versión calcula los lags de `ccajas_depositos` sobre la columna ya anulada, mientras que el archivo generado el 2026-10-07, con el que se entrenó, los tenía sobre los ceros de 202105; `reproducir.construir_lags` reproduce la versión del 7-oct.
- `scripts/c112_v101_test.py` · secundario · Python · 104 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c112_v101_test.py.txt)
- `scripts/c201_cortar.py` · secundario · Python · 64 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c201_cortar.py.txt) — Lee los scores por semilla ya guardados de un experimento (por defecto c201_receta_lags), arma el ensamble por rango y escribe, para cada corte pedido, un CSV por semilla y uno del ensamble, sin reentrenar.
- `scripts/c161_canaritos.py` · secundario · Python · 130 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c161_canaritos.py.txt) — Agrega variables uniformes al azar (canaritos) en cantidad igual al 20% de las predictoras, entrena, ordena por importancia (gain) y conserva las variables reales cuya posición queda por debajo de la mediana más 4 desvíos de la posición de los canaritos; repite con cinco semillas, se queda con las que sobreviven en mayoría y escribe `canaritos_sobrevivientes.json`.
- `scripts/c148.py` · secundario · Python · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c148.py.txt)
- `scripts/c168.py` · secundario · Python · 56 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c168.py.txt)
- `scripts/c139.py` · secundario · Python · 27 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c139.py.txt)
- `scripts/c172_corte_final.py` · secundario · Python · 91 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c172_corte_final.py.txt) — Calcula la curva de captura de BAJA+2 en dos folds con diez semillas, la combina con cinco prevalencias (870 a 1.139) para obtener la ganancia por corte y devuelve el corte que minimiza el máximo regret y el que minimiza el regret medio.
- `scripts/c130b.py` · secundario · Python · 31 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c130b.py.txt)
- `scripts/c107_final.py` · secundario · Python · 136 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c107_final.py.txt) — Experimento c107_pesos25: 150 columnas, clase BAJA+1 o BAJA+2 con peso 0,25 para BAJA+1, 45 hojas y 250 rondas, 20 semillas. Mide en dos folds el ensamble por rango frente a las semillas sueltas, elige el corte por minimax del regret y escribe un CSV por semilla y uno del ensamble.
- `scripts/c221_ensamble_heterogeneo.py` · secundario · Python · 112 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c221_ensamble_heterogeneo.py.txt) — Entrena en 202103–202106 los cinco trials de mayor AUC de c220 con cuatro semillas cada uno (1.500 rondas por defecto) y escribe envíos por trial, por semilla y del ensamble por rango de todos.
- `scripts/enviar.py` · secundario · Python · 133 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/enviar.py.txt) — Registra un submit en el ledger (experimento, archivos, hipótesis y contra qué se compara) y, con `--enviar`, sube los CSV al bot de Zulip mediante un módulo externo al repositorio (`~/Documents/segundo-cuatrimestre/zulip/competencia.py`), espera la respuesta hasta 240 segundos y guarda la ganancia pública media y su desvío en la tabla `resultado`.
- `scripts/c132.py` · secundario · Python · 39 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c132.py.txt)
- `scripts/c123_revalidar.py` · secundario · Python · 109 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c123_revalidar.py.txt)
- `scripts/c190.py` · secundario · Python · 35 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c190.py.txt)
- `scripts/c147.py` · secundario · Python · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c147.py.txt)
- `scripts/c116.py` · secundario · Python · 41 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c116.py.txt)
- `scripts/c104_diagnostico_fe.py` · secundario · Python · 95 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c104_diagnostico_fe.py.txt)
- `scripts/c203_corte_calculado.py` · secundario · Python · 114 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c203_corte_calculado.py.txt) — Estima la cantidad de BAJA+2 de 202108 como suma de probabilidades de modelos con clase BAJA+2 sola, calcula la curva de captura en 202107 contra BAJA+1 (entrenando en 202103–202105) y deriva el regret por corte bajo las cuatro prevalencias observadas (870, 960, 1.098, 1.139) y la estimada.
- `scripts/c129_sacar_drift.py` · secundario · Python · 115 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c129_sacar_drift.py.txt)
- `scripts/c153.py` · secundario · Python · 30 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c153.py.txt)
- `scripts/c272_ens40.py` · secundario · Python · 43 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c272_ens40.py.txt) — Promedia por rango los 40 conjuntos de scores guardados de c201 (1.000 rondas) y c241 (2.000 rondas), escribe el envío a 14.000 y su SHA-256.
- `scripts/c136.py` · secundario · Python · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c136.py.txt)
- `scripts/c167.py` · secundario · Python · 43 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c167.py.txt) — Compara en dos folds el dataset `competencia_01_rcf.parquet` (rank con cero fijo, según su encabezado) con el base y escribe 20 archivos de 9.000 envíos. La construcción de ese parquet no se observa en el repositorio.
- `scripts/c126.py` · secundario · Python · 52 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c126.py.txt)
- `scripts/c115_features2.py` · secundario · Python · 115 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c115_features2.py.txt) — Genera `competencia_01_v2.parquet` con indicadores de negocio: saldo negativo y su suma en una ventana de 3 meses, canales sin uso, caída de `ctrx_quarter`, mínimo de `ctrx_quarter` en 3 meses, estado de tarjetas, mora, acreditación de sueldo y un rank por mes de comisión por transacción.
- `scripts/c143.py` · secundario · Python · 34 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c143.py.txt)
- `scripts/ledger_export.py` · secundario · Python · 34 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/ledger_export.py.txt) — Exporta las tablas `experimento`, `submit`, `archivo` y `resultado` y la vista `v_submits` de PostgreSQL a `ledger/*.csv`.
- `scripts/c254_calendario.py` · secundario · Python · 58 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c254_calendario.py.txt) — Sobre el dataset de c252, reemplaza `cliente_vip` de 202106 por el valor de mayo y pone `Visa_delinquency` en 0 donde `Visa_Finiciomora` = 0 en 202105 y 202108; recalcula sus lags y deltas.
- `scripts/c137.py` · secundario · Python · 31 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c137.py.txt)
- `scripts/c166.py` · secundario · Python · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c166.py.txt)
- `scripts/c142.py` · secundario · Python · 50 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c142.py.txt)
- `scripts/c201_receta_lags.py` · principal · Python · 117 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c201_receta_lags.py.txt) — Define `params_receta` y `semillas_c107`, que importan `c210_variante.py` y `c216_captura_foldB.py`. Su `main` corresponde al experimento c201: la misma receta con 1.000 rondas sobre el parquet con lags, con modelos y scores guardados por semilla y envíos por corte.
- `scripts/c127_deflactado.py` · secundario · Python · 127 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c127_deflactado.py.txt) — Divide cada monto por la mediana de sus valores positivos del mes y compara la captura de tres conjuntos de columnas (crudas, divididas, ambas) entrenando en 202103 y evaluando en 202105 y 202106 con diez semillas.
- `scripts/c105_busqueda.py` · secundario · Python · 121 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c105_busqueda.py.txt) — Búsqueda con Optuna (TPE, study en PostgreSQL) sobre 202103–202104: el objetivo es la ganancia media en cinco particiones aleatorias estratificadas 70/30, con early stopping sobre la ganancia. Explora el esquema de clase, el peso de BAJA+1, learning_rate, num_leaves, min_data_in_leaf, feature_fraction, bagging_fraction, lambda_l1, lambda_l2, min_gain_to_split y max_bin.
- `scripts/c103_ruido_publico.py` · secundario · Python · 99 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c103_ruido_publico.py.txt)
- `scripts/c133.py` · secundario · Python · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c133.py.txt)
- `scripts/c180_busqueda_oot.py` · secundario · Python · 96 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c180_busqueda_oot.py.txt) — Búsqueda con Optuna cuyo objetivo es la ganancia a 10.500 envíos en dos folds fuera de tiempo (202103→202105 y 202103–202104→202106) con tres semillas por trial; el espacio incluye el peso de BAJA+1 y la cantidad de rondas.
- `scripts/c146.py` · secundario · Python · 32 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c146.py.txt)
- `scripts/c117.py` · secundario · Python · 27 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c117.py.txt)
- `scripts/c181.py` · secundario · Python · 49 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c181.py.txt)
- `scripts/c230_reparado_transiciones.py` · secundario · Python · 104 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c230_reparado_transiciones.py.txt) — Genera `competencia_01_rep.parquet`: pone en NULL los `*_Fvencimiento` menores a −1.000.000 y los `*_mfinanciacion_limite` mayores a 10 veces `*_mlimitecompra`, suma `ccajas_depositos` y `ccajas_otras`, quita `*_mconsumototal`, agrega un indicador de bloque de nulos, 36 indicadores de transición (a cero, a negativo, desde cero) para 12 montos, cuatro contadores de meses desde el último evento (hasta 3) y lags y deltas 1 y 2 de todo.
- `scripts/c252_aguinaldo.py` · secundario · Python · 52 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/scripts/c252_aguinaldo.py.txt) — En 202106, para las filas con 2 o más acreditaciones de sueldo o con `mpayroll` más de un 30% por encima del mes anterior, divide `mpayroll` y `mpayroll2` por 1,5 y resta una acreditación a `cpayroll_trx`; recalcula lags y deltas de esas tres columnas.
- `notebooks/n02_experimentos.ipynb` · secundario · Jupyter (python) · 468 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/notebooks/n02_experimentos.ipynb.txt) — Gráficos armados desde `ledger/v_submits.csv` y los scores guardados: ganancia pública por submit, curvas por corte con 20 archivos, 24 variantes frente a la referencia, cantidad de columnas frente a ganancia, 5 semillas frente a 20, mezcla con el modelo de horizonte 1, importancia de variables, coincidencia entre las 20 listas, validación interna (c216, c222, local frente a público) y submits por día.
- `notebooks/n01_eda.ipynb` · secundario · Jupyter (python) · 247 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/notebooks/n01_eda.ipynb.txt) — Exploración del dataset con DuckDB en ocho secciones con gráficos: altas y bajas por mes, columnas con nulos, medianas mensuales de montos indexadas a marzo, variables con valores distintos en un solo mes, `ctrx_quarter` y saldo negativo por clase, trayectoria antes de la baja, AUC univariado contra BAJA+2 y correlación de cada variable con su lag 1.
- `experimentos/c106_base/ganador.json` · configuracion · JSON · 32 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/experimentos/c106_base/ganador.json.txt) — Trial 15 de una búsqueda de Optuna con su revalidación: esquema `pesos` con peso 0,91, 1.428 rondas, corte 10.000, ganancia en 202105 y 202106 y sus hiperparámetros.
- `experimentos/c113_sonda/resumen.json` · configuracion · JSON · 56 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/experimentos/c113_sonda/resumen.json.txt) — Resumen de las cuatro variantes de `c113_sonda.py`: ganancia local en 202105 y 202106, cantidad de columnas, meses, factor de decaimiento y filas de entrenamiento.
- `experimentos/c107_pesos25/params.json` · configuracion · JSON · 48 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/experimentos/c107_pesos25/params.json.txt) — Parámetros de `c107_final.py`: hiperparámetros, clase `pesos` con 0,25, meses 202103–202106, 250 rondas, corte 11.000 y la lista de 20 semillas.
- `experimentos/c100_esqueleto/params.json` · configuracion · JSON · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/experimentos/c100_esqueleto/params.json.txt) — Parámetros guardados por `c100_esqueleto.py`: 45 hojas, learning_rate 0,0077, min_data_in_leaf 174, feature_fraction 0,277, bagging_fraction 0,918, meses 202103–202106, clase `baja2`, 250 rondas y corte 11.000.
- `experimentos/c102_comparacion/params.json` · configuracion · JSON · 32 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/experimentos/c102_comparacion/params.json.txt) — Hiperparámetros, los dos folds (202103→202105 y 202103–202104→202106) y las 250 rondas del experimento c102.
- `experimentos/c203_corte_calculado/prevalencia.json` · configuracion · JSON · 17 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/experimentos/c203_corte_calculado/prevalencia.json.txt) — Suma de probabilidades (media y desvío entre semillas) sobre 202106, 202107 y 202108 calculada por `c203_corte_calculado.py`, con el valor real 1.098 para 202106.
- `src/registro.py` · secundario · Python · 325 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/src/registro.py.txt) — Registro de experimentos y envíos en PostgreSQL: define las tablas `experimento`, `submit`, `archivo`, `resultado` y `leaderboard` y la vista `v_submits`, y las funciones para dar de alta un experimento o un submit (estado inicial `preparado`, con el SHA-256 de cada archivo), marcarlo como enviado, guardar la respuesta del bot, listar y borrar archivos de submits descartados. Toma la conexión de un `.env` o de variables de entorno.
- `src/competencia.py` · principal · Python · 311 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/src/competencia.py.txt) — Funciones compartidas por `reproducir.py` y por los scripts: carga y orden de datos, armado de X, clase y pesos, ganancia acumulada, regret por corte, caché de modelos, ensamble por rango, selección de los K primeros y escritura verificada de los envíos. `reproducir.py` importa de acá `verificar_seleccion`; `c210_variante.py` usa además `cargar`, `preparar`, `entrenar_o_cargar`, `ensamble_por_rank`, `top_k` y `escribir_envios`.
- `src/v_estilo.py` · secundario · Python · 241 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/src/v_estilo.py.txt) — Estilo de gráficos de matplotlib que usan los dos notebooks: paleta, `rcParams` y funciones para barras horizontales y verticales, líneas con etiqueta directa, líneas de referencia, nota al pie y guardado en PNG.
- `src/fe_panel.py` · principal · Python · 238 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/src/fe_panel.py.txt) — Módulo de DuckDB: construye el dataset base con `clase_ternaria` desde el crudo y ofrece generadores de fragmentos SQL (rank, lag, delta, agregados de ventana, pendiente). El camino de la entrega usa `conectar`, `construir_base`, `_fragmento`, `clausula_ventana` y `columnas_numericas`; los generadores `sql_rank`, `sql_lag`, `sql_delta`, `sql_ventana` y `sql_slope` los usan scripts de exploración.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### reproducir.py

Script que el README indica para reproducir la entrega: va del CSV crudo al CSV de 14.000 clientes (clase, lags y deltas, 20 modelos LightGBM de 2.000 rondas, ensamble por rango) y compara el SHA-256 del resultado con el registrado.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–28] Texto de encabezado: indica los dos usos (`--rondas 2000` para un ensamble de 20
#   modelos; `--rondas 1000 2000` para uno de 40), enumera tres candidatos con su ganancia pública y su SHA-256
#   según el propio archivo, y resume la receta común: 750 predictoras, columnas excluidas, clase con pesos,
#   meses 202103–202106, 20 semillas, ensamble por rango y 14.000 envíos.
"""Reproduce la entrega final desde el dataset original.

La materia lo exige: «scripts/notebooks que partiendo del dataset original permitan a los
profesores replicar exactamente sus entregas finales, esto incluye a las semillas aleatorias».

    python reproducir.py --rondas 2000 --salida entrega_final.csv        # ensamble de 20 a 2.000 rondas
    python reproducir.py --rondas 1000 2000 --salida entrega_final.csv   # ensamble de 40 (20 a 1.000 + 20 a 2.000)

Parte de `data/competencia_01_crudo.csv` (el CSV tal cual se baja de la catedra, SIN clase_ternaria),
construye la clase, arma el dataset con historia, entrena las 20 semillas y escribe el CSV que se le
manda al bot. Imprime el SHA-256 para compararlo con el entregado. Tarda ~2 horas en 8 cores.

LOS TRES CANDIDATOS (9-oct-2026), misma receta, mismos datos, mismas 20 semillas; cambia solo num_boost_round:
  --rondas 1000       -> `c201_lags_ens20_14000`      104,17 publico   sha 5157ac24...
  --rondas 2000       -> `c241_rondas2000_ens20_14000` 103,79 publico   sha 657d747a...
  --rondas 1000 2000  -> `c272_ens40_14000`            103,02 publico   sha 7ace9c16...
El SHA esperado se elige segun --rondas. LA ENTREGA FINAL se fija en SHA_FINAL cuando se decida.

LA RECETA COMUN:
  - variables: las 150 crudas + lag 1, delta 1, lag 2 y delta 2 de cada una (750 predictoras),
    con `ccajas_depositos` en NULL en 202105 (es todo cero ese mes)
  - fuera: id, foto_mes, clase, las columnas de baja, Visa_Finiciomora y Master_Finiciomora
  - clase: positivo = BAJA+1 o BAJA+2, con BAJA+1 pesando 0,25
  - entrena 202103..202106, 20 semillas por cada valor de --rondas, receta de hiperparametros de Denicolay
  - ensamble por RANGO de todas las predicciones sobre 202108; se envian los 14.000 mejores

Todo lo que decide el resultado esta aca arriba, explicito. Nada depende de modelos guardados.
"""
# [Anotación · líneas 29–42] Importa argparse, hashlib, lightgbm, numpy y pandas; agrega `src/` al path e
#   importa el módulo `fe_panel` y la función `verificar_seleccion` de `competencia`.
import argparse
import hashlib
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))
import fe_panel as fe  # noqa: E402
from competencia import verificar_seleccion  # noqa: E402

# [Anotación · líneas 44–52] Define las rutas del CSV crudo, del parquet base y del parquet con lags (todas
#   bajo `data/`), un diccionario con el SHA-256 esperado para cada combinación de rondas (1.000; 2.000; 1.000 y
#   2.000) y `SHA_FINAL`, igual al de 2.000 rondas.
CRUDO = RAIZ / "data" / "competencia_01_crudo.csv"
PANEL = RAIZ / "data" / "competencia_01.parquet"
LAGS = RAIZ / "data" / "competencia_01_lags12.parquet"
SHA_POR_RONDAS = {
    (1000,): "5157ac244673de5f50a4531373b4164fd58d5d9905edc5fd7f99e0bfe64b4ae9",       # c201_lags_ens20_14000
    (2000,): "657d747addc61efad64145ec9cef550c29c50c5ce283745f176d243270bb9d2e",       # c241_rondas2000_ens20_14000
    (1000, 2000): "7ace9c160cbc47ab047af41da18ee1774c2d3c71626cc3ba599c140d37e1643d",  # c272_ens40_14000
}
SHA_FINAL = "657d747addc61efad64145ec9cef550c29c50c5ce283745f176d243270bb9d2e"   # c241_rondas2000_ens20_14000: 20 semillas x 2.000 rondas, corte 14.000 (decidido 10-oct)

# [Anotación · líneas 54–67] Parámetros de la corrida: meses de entrenamiento 202103 a 202106, mes a predecir
#   202108, peso 0,25 para BAJA+1, 2.000 rondas por defecto, corte en 14.000, 20 semillas y las cinco semillas
#   propias. `FUERA` reúne las columnas que no entran al modelo: las cinco columnas de baja,
#   `numero_de_cliente`, `foto_mes`, `clase_ternaria`, `clase_binaria`, `Visa_Finiciomora` y
#   `Master_Finiciomora`.
# ---------------------------------------------------------------- la receta
MESES_TRAIN = [202103, 202104, 202105, 202106]
MES_PREDECIR = 202108
PESO_BAJA1 = 0.25         # BAJA+2 pesa 1,0; BAJA+1 pesa esto
RONDAS_DEFAULT = [2000]       # --rondas lo cambia; ver SHA_POR_RONDAS
CORTE = 14_000            # publico: meseta 13.500-14.500; fold B a horizonte 2: minimax 13.500, esperado 14.000
N_SEMILLAS = 20
SEMILLAS_PROPIAS = [261431, 269281, 429899, 560771, 749401]

FUERA = (
    fe.COLUMNAS_DE_BAJA          # miran el futuro: es_baja ES la respuesta
    + [fe.ID, fe.MES, fe.CLASE, "clase_binaria"]
    + ["Visa_Finiciomora", "Master_Finiciomora"]   # ceros inyectados en 202105 y 202108
)


# [Anotación · líneas 70–81] `params` devuelve los hiperparámetros de LightGBM: objetivo binario, gbdt,
#   métrica AUC, max_bin 31, min_data_in_leaf 0, feature_fraction 0,5, feature_fraction_bynode 0,2,
#   learning_rate 0,005, 83 hojas, sin bagging, 8 hilos, `force_col_wise` y `deterministic` activados.
#   `min_sum_hessian_in_leaf` se calcula como 12,791817 × filas de entrenamiento / 326.184.
def params(n_filas: int) -> dict:
    """Receta de Denicolay (Zulip, J-Clase 08 > En Limpio, 2026-10-06)."""
    return {
        "objective": "binary", "boosting_type": "gbdt", "metric": "auc",
        "boost_from_average": True, "feature_pre_filter": False,
        "max_bin": 31, "min_data_in_leaf": 0,
        "feature_fraction": 0.5, "feature_fraction_bynode": 0.2,
        "learning_rate": 0.005, "num_leaves": 83,
        "min_sum_hessian_in_leaf": 12.791817 * n_filas / 326_184,
        "bagging_fraction": 1.0, "bagging_freq": 0,
        "num_threads": 8, "force_col_wise": True, "deterministic": True, "verbose": -1,
    }


# [Anotación · líneas 84–87] `semillas` fija `np.random.seed(261431)`, sortea 15 enteros distintos menores a
#   1.000.000 y devuelve las cinco semillas propias seguidas de esas 15.
def semillas() -> list[int]:
    np.random.seed(SEMILLAS_PROPIAS[0])      # sin esto cambian en cada corrida
    extra = np.random.choice(1_000_000, size=15, replace=False).tolist()
    return (SEMILLAS_PROPIAS + [int(x) for x in extra])[:N_SEMILLAS]


# [Anotación · líneas 90–111] `construir_lags` crea una vista sobre el parquet base, toma las columnas
#   numéricas que no están en `FUERA` y para cada una genera cuatro columnas FLOAT: valor del mes anterior
#   (`__lag1`), diferencia con el mes anterior (`__delta1`), valor de dos meses atrás (`__lag2`) y diferencia
#   con ese valor (`__delta2`), con una ventana por cliente ordenada por mes. En el mismo SELECT reemplaza
#   `ccajas_depositos` por NULL en 202105; los lags de esa variable se calculan sobre la vista sin anular, como
#   indica el comentario. Escribe el resultado en parquet con compresión ZSTD.
def construir_lags(con) -> None:
    """Las 150 crudas + lag1/delta1/lag2/delta2 de cada una, en FLOAT. Igual que scripts/c200 del 7-oct.

    OJO: la version que entreno la entrega anula ccajas_depositos en 202105 SOLO en la columna del mes;
    sus lags van sobre los ceros crudos. Se reproduce tal cual (scripts/c200 corrige esto para
    datasets futuros, pero la entrega es esta).
    """
    con.execute(f"create or replace view base as select * from read_parquet('{PANEL}')")
    campos = [x for x in fe.columnas_numericas(con, "base", excluir=("Visa_Finiciomora", "Master_Finiciomora"))
              if x not in FUERA]
    nuevas = []
    for x in campos:
        nuevas.append(f"lag({x}, 1) over historia :: FLOAT as {x}__lag1")
        nuevas.append(f"({x} - lag({x}, 1) over historia) :: FLOAT as {x}__delta1")
        nuevas.append(f"lag({x}, 2) over historia :: FLOAT as {x}__lag2")
        nuevas.append(f"({x} - lag({x}, 2) over historia) :: FLOAT as {x}__delta2")
    sql = (
        "select * exclude (ccajas_depositos)"
        f"\n  , case when {fe.MES} = 202105 then null else ccajas_depositos end as ccajas_depositos"
        + fe._fragmento(nuevas) + "\nfrom base" + fe.clausula_ventana("historia")
    )
    con.execute(f"copy ({sql}) to '{LAGS}' (format PARQUET, COMPRESSION ZSTD)")


# [Anotación · líneas 114–127] `datos` abre DuckDB; si falta el parquet base lo construye desde el CSV crudo
#   con `fe.construir_base` y si falta el de lags llama a `construir_lags`. Lee el parquet con pandas, descarta
#   las columnas de baja, convierte `numero_de_cliente` a int64 y ordena las filas por cliente y mes con
#   mergesort.
def datos() -> pd.DataFrame:
    con = fe.conectar()
    if not PANEL.exists():
        print(f"  {PANEL.name} no existe: reconstruyendo desde {CRUDO.name}")
        fe.construir_base(con, str(CRUDO), str(PANEL))
    if not LAGS.exists():
        print(f"  {LAGS.name} no existe: construyendo la historia")
        construir_lags(con)
    con.close()
    d = pd.read_parquet(LAGS)
    d = d.drop(columns=fe.COLUMNAS_DE_BAJA, errors="ignore")
    d[fe.ID] = d[fe.ID].astype("int64")      # viene DOUBLE: 48000000 -> 4.8e+07 rompe el submit
    # DuckDB no garantiza el orden de las filas y LightGBM depende de el.
    return d.sort_values([fe.ID, fe.MES], kind="mergesort").reset_index(drop=True)


# [Anotación · líneas 130–136] `main` define tres argumentos: `--salida` (por defecto `entrega_final.csv`),
#   `--semillas` (por defecto 20) y `--rondas` (uno o más valores, por defecto 2000).
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", type=Path, default=Path("entrega_final.csv"))
    ap.add_argument("--semillas", type=int, default=N_SEMILLAS, help="menos semillas = prueba rapida (no reproduce el SHA)")
    ap.add_argument("--rondas", type=int, nargs="+", default=RONDAS_DEFAULT, help="num_boost_round de cada bloque de 20 semillas; varios valores = ensamble de todos")
    args = ap.parse_args()
    t0 = time.time()

# [Anotación · líneas 138–151] Carga los datos y arma la lista de predictoras (todas las columnas que no están
#   en `FUERA`); verifica con `assert` que sean 750 y que el dataset tenga 983.061 filas. Con las filas de
#   202103–202106 arma `y` = 1 si la clase es BAJA+1 o BAJA+2 y el peso por fila: 0,25 para BAJA+1 y 1,0 para el
#   resto. Separa las filas de 202108 con sus ids e imprime los tamaños.
    d = datos()
    pred = [x for x in d.columns if x not in FUERA]
    assert len(pred) == 750, f"{len(pred)} predictoras, se esperaban 750"
    assert len(d) == 983_061, f"{len(d):,} filas, se esperaban 983.061"
    tr = d[d[fe.MES].isin(MESES_TRAIN)]
    clase = tr[fe.CLASE].to_numpy()
    y = np.isin(clase, ["BAJA+1", "BAJA+2"]).astype("int8")
    w = np.where(clase == "BAJA+1", PESO_BAJA1, 1.0)
    X = tr[pred]
    fut = d[d[fe.MES] == MES_PREDECIR]
    ids = fut[fe.ID].to_numpy()
    Xfut = fut[pred]
    print(f"  train {MESES_TRAIN} ({len(X):,} filas, {int(y.sum()):,} positivos) -> {MES_PREDECIR} ({len(fut):,}) "
          f"| {len(pred)} predictoras [{time.time()-t0:.0f}s]", flush=True)

# [Anotación · líneas 153–164] Para cada valor de rondas y cada semilla entrena un modelo con un `lgb.Dataset`
#   nuevo (el comentario explica que los bins se construyen con una muestra de 200.000 filas sorteada con la
#   semilla), predice sobre 202108 y convierte la predicción en rango percentil. Al terminar promedia los rangos
#   de todos los modelos.
    P = params(len(X))
    rangos = []
    for nbr in args.rondas:
        for i, s in enumerate(semillas()[:args.semillas], 1):
            # Un Dataset NUEVO por semilla, igual que el pipeline que entreno la entrega: los bins se
            # construyen sobre una muestra de 200.000 filas sorteada con la semilla, asi que compartir
            # el Dataset entre semillas entrena 19 modelos distintos de los registrados (10-oct: 157 ids
            # de diferencia en el ensamble).
            m = lgb.train({**P, "seed": s}, lgb.Dataset(X, label=y, weight=w), num_boost_round=nbr)
            rangos.append(pd.Series(m.predict(Xfut)).rank(pct=True).to_numpy())
            print(f"    {nbr} rondas, semilla {s} ({i}/{args.semillas}) [{time.time()-t0:.0f}s]", flush=True)
    ens = np.mean(rangos, axis=0)            # ensamble por RANGO, no por score, de todos los modelos

# [Anotación · líneas 166–173] Toma los 14.000 clientes de mayor promedio de rangos con un orden estable, los
#   ordena por id y los escribe como enteros, uno por línea. Relee el archivo y verifica que no tenga notación
#   científica ni puntos y que tenga 14.000 filas. Llama a `verificar_seleccion` e imprime, por marcador, la
#   proporción entre los elegidos, entre el resto y el cociente.
    elegidos = np.sort(ids[np.argsort(-ens, kind="stable")[:CORTE]]).astype("int64")   # empates: por orden de id
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(args.salida, elegidos, fmt="%d")
    texto = args.salida.read_text()
    assert "e+" not in texto and "." not in texto, "notacion cientifica en el CSV"
    assert len(np.loadtxt(args.salida, dtype="int64")) == CORTE
    for nombre, (p_sel, p_resto, lift) in verificar_seleccion(elegidos, d).items():
        print(f"  {nombre:22s} {p_sel:6.1%} vs {p_resto:6.1%}   x{lift:.2f}")
# [Anotación · líneas 174–188] Calcula el SHA-256 del archivo, busca el esperado para la combinación de rondas
#   pedida e imprime si coincide con el envío registrado y si es la entrega final; con menos de 20 semillas o
#   una combinación sin referencia lo avisa. Cierra con el punto de entrada del script.
    sha = hashlib.sha256(args.salida.read_bytes()).hexdigest()
    esperado = SHA_POR_RONDAS.get(tuple(args.rondas))
    print(f"\n  {args.salida}: {CORTE:,} envios, rondas {args.rondas}, {len(rangos)} modelos  [{time.time()-t0:.0f}s]")
    print(f"  sha256: {sha}")
    if args.semillas < N_SEMILLAS or esperado is None:
        print("  (sin SHA de referencia para esta combinacion)")
    else:
        print("  " + ("COINCIDE con el submit registrado" if sha == esperado else
                      f"NO coincide con el submit registrado ({esperado[:12]}...): revisar version de LightGBM, hilos y orden de filas"))
        if SHA_FINAL:
            print("  " + ("ES LA ENTREGA FINAL" if sha == SHA_FINAL else "no es la entrega final"))


if __name__ == "__main__":
    main()
```

### scripts/c210_variante.py

Script parametrizado que entrena una variante (dataset, hiperparámetros, clase, meses, rondas, columnas) y escribe envíos por semilla y del ensamble para cada corte. El README le atribuye el entrenamiento del experimento c241 (20 semillas, 2.000 rondas); la línea de comando usada no figura en el repositorio. Los experimentos c211–c215, c241–c249, c262–c265 y c290–c292 que nombra el README no tienen script propio en `scripts/`.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–14] Texto de encabezado con cuatro ejemplos de invocación (c211 a c214) y la
#   descripción de los dos juegos de hiperparámetros: `z701` (45 hojas, 250 rondas) y `receta` (83 hojas, 1.000
#   rondas).
"""Una variante de la entrega, parametrizada: dataset x hiperparametros x target x meses.

Reemplaza escribir un script por experimento cuando lo que cambia es una celda de la grilla.
Cada corrida cachea modelos y scores de 202108 por semilla en experimentos/<nombre>/ y escribe
envios por corte (archivos de semilla + ensamble). Las semillas son las de c107, en orden.

    python scripts/c210_variante.py --nombre c211_lags_z701   --dataset competencia_01_lags12.parquet --params z701
    python scripts/c210_variante.py --nombre c212_base_receta --dataset competencia_01.parquet        --params receta
    python scripts/c210_variante.py --nombre c213_lags_baja2  --dataset competencia_01_lags12.parquet --params receta --target baja2
    python scripts/c210_variante.py --nombre c214_lags_sin03  --dataset competencia_01_lags12.parquet --params receta --meses 202104 202105 202106

--params z701   : los de la entrega vieja (45 hojas, lr 0,0077, mdl 174, ff 0,277, bagging 0,918; 250 rondas)
--params receta : la de Denicolay (mdl 0, lr 0,005, ff 0,5, bynode 0,2, 83 hojas; 1.000 rondas)
"""
# [Anotación · líneas 15–35] Importaciones (toma `params_receta` y `semillas_c107` de `c201_receta_lags`) y el
#   diccionario `PARAMS_Z701`: 45 hojas, learning_rate 0,0077, min_data_in_leaf 174, feature_fraction 0,277,
#   bagging_fraction 0,918.
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ.parent / "src"))
import competencia as c  # noqa: E402
from c201_receta_lags import params_receta, semillas_c107  # noqa: E402

PARAMS_Z701 = {
    "objective": "binary", "boosting_type": "gbdt", "first_metric_only": True,
    "boost_from_average": True, "feature_pre_filter": False, "max_bin": 31,
    "num_leaves": 45, "learning_rate": 0.0077, "min_data_in_leaf": 174,
    "feature_fraction": 0.277, "bagging_fraction": 0.918, "bagging_freq": 1,
    "num_threads": 8, "force_col_wise": True, "deterministic": True,
}


# [Anotación · líneas 38–56] Argumentos: `--nombre`, `--dataset` (por defecto el parquet con lags), `--params`
#   (z701 o receta), `--target` (baja1, baja2, baja12 o pesos), `--peso-baja1` (0,25), `--meses`
#   (202103–202106), `--semillas` (5), `--cortes` (10.000 y 14.000), `--rondas`, `--hojas`, `--columnas`, `--ff`
#   y `--hessian`. Crea la carpeta del experimento.
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--dataset", default="competencia_01_lags12.parquet")
    ap.add_argument("--params", choices=["z701", "receta"], default="receta")
    ap.add_argument("--target", choices=["baja1", "baja2", "baja12", "pesos"], default="pesos")
    ap.add_argument("--peso-baja1", type=float, default=0.25)
    ap.add_argument("--meses", type=int, nargs="+", default=[202103, 202104, 202105, 202106])
    ap.add_argument("--semillas", type=int, default=5)
    ap.add_argument("--cortes", type=int, nargs="+", default=[10_000, 14_000])
    ap.add_argument("--rondas", type=int, default=None, help="num_boost_round; por defecto 1.000 (receta) o 250 (z701)")
    ap.add_argument("--hojas", type=int, default=None, help="num_leaves (receta: 83)")
    ap.add_argument("--columnas", type=Path, default=None, help="archivo con una columna por linea: se entrena SOLO con esas predictoras (reduccion de dimensionalidad por importancia)")
    ap.add_argument("--ff", type=float, default=None, help="feature_fraction (receta: 0,5)")
    ap.add_argument("--hessian", type=float, default=None, help="factor sobre min_sum_hessian_in_leaf de la receta (1,0 = 12,79 x filas / 326.184)")
    args = ap.parse_args()
    t0 = time.time()
    carpeta = c.EXPERIMENTOS / args.nombre
    carpeta.mkdir(parents=True, exist_ok=True)

# [Anotación · líneas 58–70] Carga el dataset y la lista de predictoras; si se pasa `--columnas`, se queda
#   sólo con las columnas listadas en ese archivo. Arma X, y y pesos y separa las filas de 202108.
    d = c.cargar(args.dataset)
    pred = c.columnas_predictoras(d)
    if args.columnas:
        quedan = set(args.columnas.read_text().split())
        faltan = quedan - set(pred)
        assert not faltan, f"{len(faltan)} columnas de {args.columnas} no estan en el dataset: {sorted(faltan)[:5]}"
        pred = [x for x in pred if x in quedan]
    X, y, w = c.preparar(d, args.meses, args.target, args.peso_baja1)
    X = X[pred]
    fut = d[d[c.fe.MES] == c.MES_COMPETENCIA]
    ids = fut[c.fe.ID].to_numpy()
    Xfut = fut[pred]
    del d
# [Anotación · líneas 71–85] Elige los hiperparámetros y las rondas por defecto (1.000 para la receta, 250
#   para z701) y aplica los reemplazos pedidos: rondas, hojas, feature_fraction y un factor sobre
#   `min_sum_hessian_in_leaf`. Imprime el resumen de la corrida.
    if args.params == "receta":
        P, nbr = params_receta(len(X)), 1_000
    else:
        P, nbr = PARAMS_Z701, 250
    if args.rondas:
        nbr = args.rondas
    if args.hojas:
        P = {**P, "num_leaves": args.hojas}
    if args.ff:
        P = {**P, "feature_fraction": args.ff}
    if args.hessian:
        P = {**P, "min_sum_hessian_in_leaf": P["min_sum_hessian_in_leaf"] * args.hessian}
    print(f"  {args.nombre}: {args.dataset} | {len(pred)} predictoras | {args.params} | "
          f"{args.target} {args.peso_baja1 if args.target == 'pesos' else ''} | meses {args.meses} | "
          f"{len(X):,} filas, {int(y.sum()):,} positivos | {nbr} rondas, {P['num_leaves']} hojas, hessian {P['min_sum_hessian_in_leaf']:.2f} [{time.time()-t0:.0f}s]", flush=True)

# [Anotación · líneas 87–99] Por cada semilla: lee los scores guardados si existen y verifica los ids; si no,
#   entrena o carga el modelo con `entrenar_o_cargar`, predice sobre 202108 y guarda los scores en parquet.
    scores = {}
    for i, s in enumerate(semillas_c107(args.semillas), 1):
        ruta = carpeta / f"scores_202108_s{s}.parquet"
        if ruta.exists():
            t = pd.read_parquet(ruta)
            assert (t[c.fe.ID].to_numpy() == ids).all(), f"{ruta.name}: ids distintos del dataset actual"
            scores[s] = t["score"].to_numpy()
        else:
            etq = f"{args.params}_{s}_{c.clave(P, args.meses, args.target, args.peso_baja1, args.dataset + (f"|{len(pred)}cols" if args.columnas else ""), nbr, s)}"
            m = c.entrenar_o_cargar(P, X, y, w, nbr, s, carpeta, etq)
            scores[s] = m.predict(Xfut)
            pd.DataFrame({c.fe.ID: ids, "score": scores[s]}).to_parquet(ruta)
        print(f"  semilla {s} ({i}/{args.semillas}) [{time.time()-t0:.0f}s]", flush=True)

# [Anotación · líneas 101–119] Calcula el ensamble por rango y lo guarda. Para cada corte escribe un CSV por
#   semilla y uno del ensamble llamado `<nombre>_<corte>_ens<cantidad de semillas>.csv`, con las verificaciones
#   de `escribir_envios` y `verificar_seleccion`.
    ens = c.ensamble_por_rank(scores)
    pd.DataFrame({c.fe.ID: ids, "ensamble": ens}).to_parquet(carpeta / f"scores_202108_ens{len(scores)}.parquet")
    ref = c.referencia_202108()
    validos = set(ids.tolist())
    for K in args.cortes:
        E = carpeta / f"envios_{K}"
        E.mkdir(exist_ok=True)
        for j, s in enumerate(scores):
            sel = c.top_k(scores[s], ids, K)
            if j == 0:
                c.verificar_seleccion(sel, ref)
            c.escribir_envios(sel, E / f"{args.nombre}_{K}_s{s}.csv", validos)
        c.escribir_envios(c.top_k(ens, ids, K), E / f"{args.nombre}_{K}_ens{len(scores)}.csv", validos, referencia=ref)
        print(f"  corte {K:6,}: {len(scores)} archivos + ensamble", flush=True)
    print(f"  listo [{time.time()-t0:.0f}s]", flush=True)


if __name__ == "__main__":
    main()
```

### scripts/c216_captura_foldB.py

Medición local que el README cita como origen del corte: entrena la receta en 202103–202104, evalúa en 202106 contra BAJA+2 y calcula captura, ganancia por corte y regret bajo cuatro prevalencias.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–10] Texto de encabezado: explica que mide la curva de captura a dos meses de distancia
#   con el fold que entrena en 202103–202104 y valida en 202106, y da un ejemplo de uso.
"""Captura a HORIZONTE 2 del modelo nuevo: fold B ([03,04] -> 202106, BAJA+2).

c203 midio la captura en el fold C, que valida BAJA+1 a un mes: tarea mas facil, curva mas
concentrada, K* mas chico (9.500-10.500). El publico, que mide agosto a dos meses, dice
13.500-14.500. Este script mide la curva a dos meses con el unico fold que lo permite; tiene
lag1 en abril y nada en marzo, asi que subestima al modelo, pero la FORMA de la curva en la cola
es lo que decide si el K* a horizonte 2 esta a la derecha.

    python scripts/c216_captura_foldB.py --semillas 3
"""
# [Anotación · líneas 11–19] Importaciones y constantes: nombre y carpeta del experimento, cortes de 8.000 a
#   16.000 cada 500 y cuatro cantidades de positivos (870, 960, 1.098 y 1.139).
import argparse, sys, time
from pathlib import Path
import numpy as np, pandas as pd
RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ.parent / "src"))
import competencia as c
from c201_receta_lags import DATASET, NBR, params_receta, semillas_c107
NOMBRE = "c216_captura_foldB"; CARPETA = c.EXPERIMENTOS / NOMBRE
KS = list(range(8_000, 16_001, 500)); PREV = [870, 960, 1_098, 1_139]

# [Anotación · líneas 21–27] `main` lee `--semillas` (por defecto 3), carga el parquet con lags, arma el
#   entrenamiento con 202103 y 202104 (clase `pesos` con 0,25) y toma 202106 como validación, con BAJA+2 como
#   positivo.
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--semillas", type=int, default=3); a = ap.parse_args()
    t0 = time.time(); CARPETA.mkdir(parents=True, exist_ok=True)
    d = c.cargar(DATASET); pred = c.columnas_predictoras(d)
    meses, mes_val = [202103, 202104], 202106
    X, y, w = c.preparar(d, meses, "pesos", 0.25); X = X[pred]; P = params_receta(len(X))
    val = d[d[c.fe.MES] == mes_val]; es = (val[c.fe.CLASE].to_numpy() == "BAJA+2"); Xv = val[pred]; del d
# [Anotación · líneas 28–32] Por cada semilla entrena o carga un modelo de 1.000 rondas con la receta y
#   predice sobre 202106.
    scores = {}
    for s in semillas_c107(a.semillas):
        etq = f"pesos_foldB_{s}_{c.clave(P, meses, 'pesos', 0.25, DATASET, NBR, s)}"
        scores[s] = c.entrenar_o_cargar(P, X, y, w, NBR, s, CARPETA, etq).predict(Xv)
        print(f"  semilla {s} [{time.time()-t0:.0f}s]", flush=True)
# [Anotación · líneas 33–39] Ensambla por rango, calcula para cada corte la fracción de BAJA+2 de 202106 que
#   queda dentro de los K primeros y la guarda en parquet; calcula además la ganancia acumulada en 202106 para
#   cada corte e imprime la tabla.
    ens = c.ensamble_por_rank(scores); orden = np.argsort(ens)[::-1]; acum = np.cumsum(es[orden])
    cap = pd.DataFrame({"K": KS, "captura": [acum[k-1]/es.sum() for k in KS]})
    cap.to_parquet(CARPETA / "captura_foldB.parquet")
    g_real = c.ganancia_acumulada(ens, es)
    cap["ganancia_real_M"] = [g_real[k-1]/1e6 for k in KS]
    print("\n  captura fold B (horizonte 2, 1.098 positivos) y ganancia real en 202106:")
    print(cap.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
# [Anotación · líneas 40–51] Para cada cantidad de positivos calcula la ganancia esperada por corte (captura ×
#   positivos × 1.072.500 menos el resto de los envíos × 27.500) y el regret porcentual frente al máximo. Arma
#   la tabla por corte con el máximo y el promedio entre prevalencias, la guarda en `regret.csv` e imprime el
#   corte que minimiza cada uno.
    filas = []
    for n_pos in PREV:
        g = {k: cp*n_pos*c.GANANCIA_ACIERTO - (k-cp*n_pos)*c.COSTO_ESTIMULO for k, cp in zip(cap.K, cap.captura)}
        mejor = max(g.values())
        filas += [{"prevalencia": n_pos, "K": k, "regret_pct": 100*(mejor-v)/mejor} for k, v in g.items()]
    t = pd.DataFrame(filas).pivot(index="K", columns="prevalencia", values="regret_pct")
    t["peor"] = t.max(axis=1); t["medio"] = t.drop(columns="peor").mean(axis=1); t.to_csv(CARPETA / "regret.csv")
    print("\n  arrepentimiento % por K:"); print(t.round(2).to_string())
    print(f"\n  minimax: K = {t['peor'].idxmin():,}   minimo esperado: K = {t['medio'].idxmin():,}   [{time.time()-t0:.0f}s]")

if __name__ == "__main__":
    main()
```

### scripts/c200_lags_todo.py

Genera `data/competencia_01_lags12.parquet` con lag 1, delta 1, lag 2 y delta 2 de todas las predictoras; el README lo cita como origen de las variables de la entrega. Su comentario indica que esta versión calcula los lags de `ccajas_depositos` sobre la columna ya anulada, mientras que el archivo generado el 2026-10-07, con el que se entrenó, los tenía sobre los ceros de 202105; `reproducir.construir_lags` reproduce la versión del 7-oct.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Texto de encabezado: una nota sobre `ccajas_depositos` en 202106, el origen de la
#   idea (mensaje de Denicolay en Zulip y el repositorio de un compañero, con las ganancias públicas que el
#   texto les atribuye), la anulación de `ccajas_depositos` en 202105 y el uso de FLOAT para las columnas
#   nuevas.
"""
NOTA (review monday-45, 9-oct): ccajas_depositos tambien esta casi muerta en 202106 (831 no-cero contra 2.175-6.486 los
otros meses); el delta2 de agosto apunta a junio y queda inflado para ~5.800 clientes. 0,23% de la ganancia: no se
regenero el dataset a dos dias del cierre. Si se vuelve a construir, anular 202106 tambien.
Dataset con lag 1, delta 1, lag 2 y delta 2 de TODAS las predictoras.

Es la receta que Denicolay dejo en Zulip (J-Clase 08 > En Limpio, 2026-10-06):
"es superador agregar al dataset lags y delta lags de orden 1 y 2", y la que
Ramirez (farpp8/dmeyf2026-competencia01, DECISIONES.md D06) midio en publico:
86,74 -> 98,59 con los mismos hiperparametros. Nuestro competencia_01_fe.parquet
tiene historia de 21 variables, no de 150, y nunca tuvo lag 2.

Tambien aplica el unico arreglo de data quality de esa receta:
ccajas_depositos -> NULL en 202105 (todos sus valores son cero ese mes).

Las columnas nuevas van en FLOAT (4 bytes): 600 columnas x 983k filas en DOUBLE
no entran comodas en 16 GB junto con el Dataset de LightGBM.

Salida: data/competencia_01_lags12.parquet
"""
# [Anotación · líneas 21–31] Importaciones y rutas de origen (`competencia_01.parquet`) y destino
#   (`competencia_01_lags12.parquet`) dentro de `data/`.
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
import fe_panel as fe  # noqa: E402
import competencia as c  # noqa: E402

ORIGEN = c.DATOS / "competencia_01.parquet"
DESTINO = c.DATOS / "competencia_01_lags12.parquet"


# [Anotación · líneas 34–44] `main` acepta `--forzar`; si el destino existe y no se pasa esa opción, termina
#   sin regenerarlo. Abre DuckDB, crea una vista sobre el parquet base y toma las columnas numéricas que no
#   están en `FUERA_DE_X` ni son las dos `Finiciomora`.
def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--forzar", action="store_true"); args = ap.parse_args()
    if DESTINO.exists() and not args.forzar:
        raise SystemExit(f"{DESTINO.name} ya existe; regenerarlo invalida los modelos cacheados que lo usaron. --forzar para pisarlo")
    t0 = time.time()
    con = fe.conectar()
    con.execute(f"create or replace view base as select * from read_parquet('{ORIGEN}')")
    campos = fe.columnas_numericas(con, "base", excluir=tuple(c.ROTAS_EN_202108))
    campos = [x for x in campos if x not in c.FUERA_DE_X]
    print(f"  {len(campos)} predictoras -> {4 * len(campos)} columnas de historia")

# [Anotación · líneas 46–51] Para cada columna arma cuatro expresiones FLOAT: lag 1, diferencia con el lag 1,
#   lag 2 y diferencia con el lag 2, sobre la ventana `historia`.
    nuevas = []
    for x in campos:
        nuevas.append(f"lag({x}, 1) over historia :: FLOAT as {x}__lag1")
        nuevas.append(f"({x} - lag({x}, 1) over historia) :: FLOAT as {x}__delta1")
        nuevas.append(f"lag({x}, 2) over historia :: FLOAT as {x}__lag2")
        nuevas.append(f"({x} - lag({x}, 2) over historia) :: FLOAT as {x}__delta2")

# [Anotación · líneas 53–68] Arma la consulta con una CTE `limpia` que pone `ccajas_depositos` en NULL en
#   202105 y calcula los lags y deltas sobre esa CTE; la escribe en parquet con ZSTD e imprime la cantidad de
#   filas y columnas. Cierra con el punto de entrada.
    # La anulacion va en una CTE para que los lags/deltas se calculen sobre la columna ya
    # corregida. OJO: el archivo generado el 2026-10-07 (el que entreno c201) tenia los lags
    # sobre los ceros crudos de 202105; esta version los corrige. Regenerar cambia el dataset.
    sql = (
        "with limpia as (select * exclude (ccajas_depositos)"
        f"\n  , case when {fe.MES} = 202105 then null else ccajas_depositos end as ccajas_depositos"
        "\n  from base)"
        "\nselect *" + fe._fragmento(nuevas) + "\nfrom limpia" + fe.clausula_ventana("historia")
    )
    con.execute(f"copy ({sql}) to '{DESTINO}' (format PARQUET, COMPRESSION ZSTD)")
    n, k = con.execute(f"select count(*), (select count(*) from (describe select * from read_parquet('{DESTINO}'))) from read_parquet('{DESTINO}')").fetchone()
    print(f"  {DESTINO.name}: {n:,} filas x {k} columnas [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
```

### scripts/c201_receta_lags.py

Define `params_receta` y `semillas_c107`, que importan `c210_variante.py` y `c216_captura_foldB.py`. Su `main` corresponde al experimento c201: la misma receta con 1.000 rondas sobre el parquet con lags, con modelos y scores guardados por semilla y envíos por corte.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–24] Texto de encabezado: hipótesis del experimento, la receta de hiperparámetros con
#   su fuente, lo que se mantiene igual respecto de la entrega anterior (clase con peso 0,25, meses
#   202103–202106, las mismas 20 semillas, ensamble por rango) y dos ejemplos de uso.
"""Lags de todo (c200) + la receta de hiperparametros de Denicolay.

HIPOTESIS: la entrega base (150 columnas, params de z701, 93,24 publico a 10.000
con 20 archivos) esta debajo de la linea de muerte (~100) porque le falta la
historia de todas las variables y porque sus hiperparametros son de otra tarea.
Dos compañeros con las mismas reglas lo midieron en publico: Ramirez
86,74 -> 98,59 (lags de todo) -> 103,18 (+ esta receta); Abregu 88 -> 110.

La receta, textual de J-Clase 08 > En Limpio (2026-10-06) y de
farpp8/dmeyf2026-competencia01 (06_receta_denicolay.py):
  max_bin 31 - min_data_in_leaf 0 - feature_fraction 0,5 - feature_fraction_bynode 0,2
  learning_rate 0,005 - sin bagging - 83 hojas - 1.000 rondas
  min_sum_hessian_in_leaf = 12,791817 x filas / 326.184

Lo que NO cambia respecto de la entrega, para que el delta sea atribuible:
target pesos 0,25, meses 202103-202106, las mismas 20 semillas de c107,
ensamble por rank, FUERA_DE_X.

Cada modelo se cachea por semilla; los scores de 202108 se guardan por semilla
para re-cortar sin reentrenar. Se puede interrumpir y retomar.

    python c201_receta_lags.py --semillas 5        # entrena/carga 5 y escribe envios
    python c201_receta_lags.py --semillas 20 --cortes 10000 11000 11500
"""
# [Anotación · líneas 25–43] Importaciones y constantes: nombre del experimento, dataset
#   `competencia_01_lags12.parquet`, meses 202103–202106, esquema de clase `pesos` con 0,25, 1.000 rondas y
#   carpeta de salida.
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ.parent / "src"))   # la raiz del repo: competencia.py y fe_panel.py
import competencia as c  # noqa: E402

NOMBRE = "c201_receta_lags"
DATASET = "competencia_01_lags12.parquet"
MESES = [202103, 202104, 202105, 202106]
TARGET, PESO_BAJA1 = "pesos", 0.25
NBR = 1_000
CARPETA = c.EXPERIMENTOS / NOMBRE


# [Anotación · líneas 46–62] `params_receta` devuelve los mismos hiperparámetros que `reproducir.params` (sin
#   `verbose`), con `min_sum_hessian_in_leaf` = 12,791817 × filas / 326.184. `semillas_c107` devuelve las
#   primeras n de la lista formada por las cinco semillas propias y 15 sorteadas con `np.random.seed(261431)`.
def params_receta(n_filas: int) -> dict:
    return {
        "objective": "binary", "boosting_type": "gbdt", "metric": "auc",
        "boost_from_average": True, "feature_pre_filter": False,
        "max_bin": 31, "min_data_in_leaf": 0,
        "feature_fraction": 0.5, "feature_fraction_bynode": 0.2,
        "learning_rate": 0.005, "num_leaves": 83,
        "min_sum_hessian_in_leaf": 12.791817 * n_filas / 326_184,
        "bagging_fraction": 1.0, "bagging_freq": 0,
        "num_threads": 8, "force_col_wise": True, "deterministic": True,
    }


def semillas_c107(n: int) -> list[int]:
    np.random.seed(c.SEMILLAS[0])
    extra = np.random.choice(1_000_000, size=15, replace=False).tolist()
    return (c.SEMILLAS + [int(x) for x in extra])[:n]


# [Anotación · líneas 65–84] `main` lee `--semillas` (por defecto 5) y `--cortes` (por defecto 10.000, 11.000
#   y 11.500), carga el dataset, arma X, y y pesos con `preparar`, separa las filas de 202108 y calcula los
#   parámetros para la cantidad de filas de entrenamiento.
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--semillas", type=int, default=5)
    ap.add_argument("--cortes", type=int, nargs="+", default=[10_000, 11_000, 11_500])
    args = ap.parse_args()
    t0 = time.time()
    CARPETA.mkdir(parents=True, exist_ok=True)

    d = c.cargar(DATASET)
    pred = c.columnas_predictoras(d)
    X, y, w = c.preparar(d, MESES, TARGET, PESO_BAJA1)
    X = X[pred]
    fut = d[d[c.fe.MES] == c.MES_COMPETENCIA]
    ids = fut[c.fe.ID].to_numpy()
    validos = set(ids.tolist())
    Xfut = fut[pred]
    del d
    P = params_receta(len(X))
    print(f"  {len(pred)} predictoras | train {len(X):,} filas, {int(y.sum()):,} positivos "
          f"| min_sum_hessian {P['min_sum_hessian_in_leaf']:.2f} [{time.time()-t0:.0f}s]")

# [Anotación · líneas 86–98] Por cada semilla: si ya existe el parquet de scores de 202108 lo lee y verifica
#   que los ids coincidan; si no, entrena o carga el modelo de 1.000 rondas, predice y guarda los scores.
    scores: dict[int, np.ndarray] = {}
    for i, s in enumerate(semillas_c107(args.semillas), 1):
        ruta = CARPETA / f"scores_202108_s{s}.parquet"
        if ruta.exists():
            t = pd.read_parquet(ruta)
            assert (t[c.fe.ID].to_numpy() == ids).all(), f"{ruta.name}: los ids cacheados no son los del dataset actual"
            scores[s] = t["score"].to_numpy()
        else:
            etiqueta = f"receta_{s}_{c.clave(P, MESES, TARGET, PESO_BAJA1, DATASET, NBR, s)}"
            m = c.entrenar_o_cargar(P, X, y, w, NBR, s, CARPETA, etiqueta)
            scores[s] = m.predict(Xfut)
            pd.DataFrame({c.fe.ID: ids, "score": scores[s]}).to_parquet(ruta)
        print(f"  semilla {s} ({i}/{args.semillas}) [{time.time()-t0:.0f}s]", flush=True)

# [Anotación · líneas 100–117] Calcula el ensamble por rango y lo guarda. Para cada corte escribe un CSV por
#   semilla y uno del ensamble con `escribir_envios`, aplicando `verificar_seleccion` al primer archivo y al del
#   ensamble.
    ens = c.ensamble_por_rank(scores)
    pd.DataFrame({c.fe.ID: ids, "ensamble": ens}).to_parquet(CARPETA / "scores_202108.parquet")
    ref = c.cargar("competencia_01.parquet")
    for K in args.cortes:
        E = CARPETA / f"envios_{K}"
        E.mkdir(exist_ok=True)
        for j, s in enumerate(scores):
            sel = c.top_k(scores[s], ids, K)
            if j == 0:
                c.verificar_seleccion(sel, ref)
            c.escribir_envios(sel, E / f"{NOMBRE}_{K}_s{s}.csv", validos)
        c.escribir_envios(c.top_k(ens, ids, K), E / f"{NOMBRE}_{K}_ens.csv", validos, referencia=ref)
        print(f"  corte {K:6,}: {len(scores)} archivos de semilla + 1 ensamble")
    print(f"  listo [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
```

### src/competencia.py

Funciones compartidas por `reproducir.py` y por los scripts: carga y orden de datos, armado de X, clase y pesos, ganancia acumulada, regret por corte, caché de modelos, ensamble por rango, selección de los K primeros y escritura verificada de los envíos. `reproducir.py` importa de acá `verificar_seleccion`; `c210_variante.py` usa además `cargar`, `preparar`, `entrenar_o_cargar`, `ensamble_por_rank`, `top_k` y `escribir_envios`.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–27] Texto de encabezado con tres convenciones (ganancia de +1.072.500 por BAJA+2
#   estimulado y −27.500 en otro caso; corte expresado en cantidad de envíos; columnas que quedan fuera de X) e
#   importaciones; agrega la carpeta del módulo al path para importar `fe_panel`.
"""Piezas compartidas de la Primera Competencia: datos, ganancia, corte y envios.

Convenciones que valen para todo el directorio:

- Una sola convencion de ganancia: +GANANCIA_ACIERTO si el estimulado era
  BAJA+2, -COSTO_ESTIMULO si no. Es la consistente con el umbral
  0,025 = 27.500 / (1.072.500 + 27.500). z601 mezcla dos y no las distingue.
- El corte se elige en CANTIDAD DE ENVIOS, no en probabilidad: la escala de los
  scores cambia con el target y con la semilla, la cantidad de envios no.
- Fuera de X van siempre: las columnas de baja (es_baja ES la respuesta),
  numero_de_cliente (asa de memorizacion), foto_mes (202108 es un valor que el
  modelo nunca vio) y las dos F*iniciomora (rotas justo en 202108).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fe_panel as fe  # noqa: E402

# [Anotación · líneas 29–46] Rutas (`experimentos/`, `data/`), ganancia y costo, umbral 27.500 / 1.100.000 =
#   0,025, semillas, mes de la competencia 202108, meses etiquetados 202103–202106, límites de 8.000 y 15.000
#   envíos, y `FUERA_DE_X`: columnas de baja, id, mes, clase, `clase_binaria`, `peso`, `Visa_Finiciomora` y
#   `Master_Finiciomora`.
RAIZ = Path(__file__).resolve().parent.parent     # la raiz del repo; este modulo vive en src/
EXPERIMENTOS = RAIZ / "experimentos"
DATOS = RAIZ / "data"          # symlink a ../dmeyf2026/monday/data

GANANCIA_ACIERTO = fe.GANANCIA_ACIERTO      # 1_072_500
COSTO_ESTIMULO = fe.COSTO_ESTIMULO          # 27_500
UMBRAL = COSTO_ESTIMULO / (GANANCIA_ACIERTO + COSTO_ESTIMULO)   # 0.025
SEMILLAS = fe.SEMILLAS

MES_COMPETENCIA = 202108
MESES_ETIQUETADOS = [202103, 202104, 202105, 202106]

MIN_ENVIOS = 8_000
MAX_ENVIOS = 15_000

ROTAS_EN_202108 = ["Visa_Finiciomora", "Master_Finiciomora"]
NO_PREDICTORAS = [fe.ID, fe.MES, fe.CLASE, "clase_binaria", "peso"]
FUERA_DE_X = fe.COLUMNAS_DE_BAJA + NO_PREDICTORAS + ROTAS_EN_202108


# [Anotación · líneas 49–62] `cargar` lee un parquet de `data/`, descarta las columnas de baja, convierte el
#   id a int64 y ordena por cliente y mes. `columnas_predictoras` devuelve las columnas que no están en
#   `FUERA_DE_X`.
def cargar(dataset: str = "competencia_01.parquet") -> pd.DataFrame:
    data = pd.read_parquet(DATOS / dataset)
    data = data.drop(columns=fe.COLUMNAS_DE_BAJA, errors="ignore")
    data[fe.ID] = data[fe.ID].astype("int64")
    # Orden canonico. DuckDB no garantiza el orden de las filas al escribir un parquet
    # y LightGBM depende de el, asi que sin esto el pipeline y reproducir.py entrenan
    # sobre ordenes distintos y entregan CSV distintos con las mismas semillas.
    # OJO: la llave de cache NO incluye el orden, asi que los modelos entrenados antes
    # de este cambio quedan obsoletos aunque entrenar_o_cargar los acepte.
    return data.sort_values([fe.ID, fe.MES], kind="mergesort").reset_index(drop=True)


def columnas_predictoras(data: pd.DataFrame) -> list[str]:
    return [c for c in data.columns if c not in FUERA_DE_X]


# [Anotación · líneas 65–88] `preparar` devuelve X, y y peso para un conjunto de meses según el esquema de
#   clase: `baja1` (positivo BAJA+1), `baja2` (positivo BAJA+2), `baja12` (positivo ambas, peso 1) y `pesos`
#   (positivo ambas, con BAJA+1 pesando `peso_baja1`).
def preparar(data: pd.DataFrame, meses: list[int], target: str = "baja2",
             peso_baja1: float = 0.0) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """X, y, peso para un conjunto de meses.

    target 'baja2'  : positivo = BAJA+2
    target 'baja12' : positivo = BAJA+1 o BAJA+2
    target 'baja1'  : positivo = BAJA+1 solo (horizonte 1: permite entrenar con 202107, que tiene BAJA+1 completo)
    target 'pesos'  : positivo = BAJA+1 o BAJA+2, con peso 1 para BAJA+2 y
                      peso_baja1 para BAJA+1. Interpola entre los dos anteriores.
    """
    d = data[data[fe.MES].isin(meses)]
    clase = d[fe.CLASE].to_numpy()
    if target == "baja1":
        y = (d[fe.CLASE] == "BAJA+1").astype("int8").to_numpy(); peso = np.ones(len(d))
    elif target == "baja2":
        y = (clase == "BAJA+2").astype("int8")
        peso = np.ones(len(d))
    elif target in ("baja12", "pesos"):
        y = np.isin(clase, ["BAJA+1", "BAJA+2"]).astype("int8")
        peso = np.ones(len(d)) if target == "baja12" else np.where(
            clase == "BAJA+1", peso_baja1, 1.0)
    else:
        raise ValueError(f"target desconocido: {target!r}")
    return d[columnas_predictoras(data)], y, peso


# [Anotación · líneas 91–113] `aporte` exige un vector booleano o 0/1 y devuelve 1.072.500 o −27.500 por fila.
#   `ganancia_acumulada` ordena por score descendente con orden estable y acumula; `ganancia` toma el valor en K
#   envíos y `curva_de_corte` lo tabula de 6.000 a 16.000 cada 250.
def aporte(es_baja2: np.ndarray) -> np.ndarray:
    # np.where() acepta cualquier cosa truthy: pasarle el array de clase_ternaria
    # (strings) da TODOS aciertos sin tirar error, y la ganancia sale 40x de mas.
    es_baja2 = np.asarray(es_baja2)
    if es_baja2.dtype.kind not in "bi" or (es_baja2.dtype.kind == "i" and es_baja2.max(initial=0) > 1):
        raise TypeError(f"aporte() espera booleanos o 0/1, recibio dtype={es_baja2.dtype}. "
                        f"Probablemente falte el '== \"BAJA+2\"'.")
    return np.where(es_baja2, GANANCIA_ACIERTO, -COSTO_ESTIMULO).astype("float64")


def ganancia_acumulada(scores: np.ndarray, es_baja2: np.ndarray) -> np.ndarray:
    orden = np.argsort(-np.asarray(scores), kind="stable")   # empates: orden de entrada, no el del quicksort
    return np.cumsum(aporte(es_baja2)[orden])


def ganancia(scores: np.ndarray, es_baja2: np.ndarray, envios: int) -> float:
    return float(ganancia_acumulada(scores, es_baja2)[envios - 1])


def curva_de_corte(scores, es_baja2, desde=6_000, hasta=16_000, paso=250) -> pd.DataFrame:
    acum = ganancia_acumulada(scores, es_baja2)
    cortes = np.arange(desde, min(hasta, len(acum)) + 1, paso)
    return pd.DataFrame({"envios": cortes, "ganancia": acum[cortes - 1]})


# [Anotación · líneas 116–147] `meseta` devuelve el tramo de cortes cuya ganancia media supera el 99,5% del
#   máximo y su centro. `simular_publico_privado` reparte 500 veces al azar un 25% de las filas y devuelve la
#   ganancia de esa parte para un corte dado.
def meseta(curvas: pd.DataFrame, columna: str = "ganancia",
           tolerancia: float = 0.995) -> tuple[int, int, int]:
    """El tramo donde la ganancia media se mantiene sobre `tolerancia` del maximo.

    Devuelve (desde, centro, hasta). Se elige el centro, no el pico: cada semilla
    tiene su maximo en otro lado y el pico exacto es ruido.
    """
    medias = curvas.groupby("envios")[columna].mean()
    alto = medias[medias >= medias.max() * tolerancia]
    desde, hasta = int(alto.index.min()), int(alto.index.max())
    centro = int(np.clip(round((desde + hasta) / 2 / 250) * 250, MIN_ENVIOS, MAX_ENVIOS))
    return desde, centro, hasta


def simular_publico_privado(scores, es_baja2, envios: int, publico: float = 0.25,
                            repeticiones: int = 500, semilla: int = SEMILLAS[3]):
    """Reparte la ganancia del mes en publico/privado muchas veces.

    Da la resolucion del instrumento: cuanto se mueve la lectura publica por el
    solo sorteo de la particion, sin que el modelo cambie en nada.
    """
    scores, es_baja2 = np.asarray(scores), np.asarray(es_baja2)   # una Series con indice de etiquetas se indexa mal
    n = len(scores)
    elegidos = np.argsort(scores)[::-1][:envios]
    v = np.zeros(n)
    v[elegidos] = aporte(es_baja2[elegidos])
    rng = np.random.default_rng(semilla)
    n_pub = int(round(n * publico))
    pub = np.empty(repeticiones)
    for i in range(repeticiones):
        pub[i] = v[rng.permutation(n)[:n_pub]].sum()
    return pd.Series(pub, name="publico")


# [Anotación · líneas 150–180] `clave` arma un hash de 16 caracteres con parámetros, meses, clase, peso,
#   nombre del dataset, rondas y semilla. `entrenar_o_cargar` carga el modelo guardado si existe y sus nombres
#   de columnas coinciden con los pedidos; si no, entrena con un `lgb.Dataset` nuevo y guarda el modelo en
#   texto.
def clave(params: dict, meses: list[int], target: str, peso_baja1: float,
          dataset: str, num_boost_round: int, semilla: int) -> str:
    firma = json.dumps(
        {"params": {k: v for k, v in sorted(params.items()) if k != "seed"},
         "meses": sorted(meses), "target": target, "peso_baja1": peso_baja1,
         "dataset": dataset, "nbr": num_boost_round, "semilla": semilla},
        sort_keys=True, default=str)
    return hashlib.sha256(firma.encode()).hexdigest()[:16]


def entrenar_o_cargar(params: dict, X, y, peso, num_boost_round: int, semilla: int,
                      carpeta: Path, etiqueta: str) -> lgb.Booster:
    """Entrena, o carga del disco si ya se entreno lo mismo. El patron de z701."""
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / f"modelo_{etiqueta}.txt"
    if destino.exists():
        guardado = lgb.Booster(model_file=str(destino))
        # La llave de cache incluye el NOMBRE del dataset, no su contenido: si un
        # parquet se regenera con otras columnas, el nombre no cambia y se cargaria
        # un modelo ajeno (con la misma cantidad de columnas ni siquiera tira error,
        # devuelve scores mal). Chequear los nombres de las features lo detecta.
        if list(guardado.feature_name()) == list(X.columns):
            return guardado
        print(f"    cache invalido en {destino.name}: el modelo guardado tiene "
              f"{guardado.num_feature()} columnas distintas de las pedidas, reentreno")
        destino.unlink()
    p = {**params, "seed": semilla, "verbose": -1}
    modelo = lgb.train(p, lgb.Dataset(X, label=y, weight=peso),
                       num_boost_round=num_boost_round)
    modelo.save_model(str(destino))
    return modelo


# [Anotación · líneas 183–223] `escribir_envios` valida que haya entre 8.000 y 15.000 ids, sin repetidos y
#   pertenecientes al mes; los escribe ordenados como enteros, relee el archivo y verifica que no tenga notación
#   científica y que coincida con lo escrito; opcionalmente llama a `verificar_seleccion`. `top_k` devuelve los
#   K ids de mayor score con orden estable.
def escribir_envios(ids, ruta: Path, validos: set[int] | None = None,
                    referencia: "pd.DataFrame | None" = None) -> int:
    """Escribe el CSV de entrega y lo vuelve a leer para verificarlo.

    El bot pide: sin encabezado, una columna, 8.000-15.000 filas, enteros y
    NUNCA notacion cientifica. numero_de_cliente viene como DOUBLE en el parquet
    y 48000000 / 31100000 estan los dos en 202108, asi que el 4.8e+07 no es
    hipotetico: es lo que pasa si uno no castea.
    """
    ids = np.asarray(ids).astype("int64")
    if not MIN_ENVIOS <= len(ids) <= MAX_ENVIOS:
        raise ValueError(f"{len(ids)} envios, fuera de [{MIN_ENVIOS}, {MAX_ENVIOS}]")
    if len(np.unique(ids)) != len(ids):
        raise ValueError("hay numero_de_cliente repetidos")
    if validos is not None and not set(ids.tolist()) <= validos:
        faltan = set(ids.tolist()) - validos
        raise ValueError(f"{len(faltan)} ids no estan en el mes de la competencia")

    ruta.parent.mkdir(parents=True, exist_ok=True)
    # Orden canonico por id. Al bot le da igual el orden (pide una columna de ids sin
    # encabezado), pero asi el archivo es identico byte a byte venga del pipeline o de
    # reproducir.py, y verificar la reproducibilidad es un diff en vez de un set().
    np.savetxt(ruta, np.sort(ids), fmt="%d")

    texto = ruta.read_text()
    if "e+" in texto or "E+" in texto or "." in texto:
        raise AssertionError(f"{ruta}: hay notacion cientifica o decimales")
    releido = np.loadtxt(ruta, dtype="int64", ndmin=1)
    if not np.array_equal(np.sort(releido), np.sort(ids)):
        raise AssertionError(f"{ruta}: lo releido no coincide con lo escrito")
    # el chequeo de `validos` es tautologico cuando sale del mismo array que `ids`.
    # Lo que importa es la CORRESPONDENCIA: que los elegidos parezcan elegidos por un
    # modelo y no indexados contra otra tabla. Ver verificar_seleccion().
    if referencia is not None:
        verificar_seleccion(ids, referencia)
    return len(ids)


def top_k(scores: np.ndarray, ids: np.ndarray, k: int) -> np.ndarray:
    # estable: clientes con score identico (perfil todo-cero) entran en orden de id, no segun el quicksort
    return np.asarray(ids)[np.argsort(-np.asarray(scores), kind="stable")[:k]]


# [Anotación · líneas 226–254] `ensamble_por_rank` promedia los rangos percentiles de los scores de cada
#   semilla. `regret` tabula, para cortes de 8.000 a 15.000 cada 500, la pérdida relativa de cada escenario
#   frente a su máximo, con una columna para el escenario de mayor pérdida y otra para el promedio;
#   `corte_minimax` devuelve el corte que minimiza esa mayor pérdida.
def ensamble_por_rank(scores_por_semilla: dict[int, np.ndarray]) -> np.ndarray:
    """Promedia posiciones, no probabilidades: las escalas no son comparables."""
    rangos = [pd.Series(s).rank(pct=True).to_numpy() for s in scores_por_semilla.values()]
    return np.mean(rangos, axis=0)


def regret(escenarios: dict[str, np.ndarray], desde: int = MIN_ENVIOS,
           hasta: int = MAX_ENVIOS, paso: int = 500) -> pd.DataFrame:
    """Cuanto se pierde, en cada escenario, por cortar en un K fijo.

    Un escenario es un mes de validacion con su curva de ganancia acumulada.
    Hace falta porque el K optimo lo manda la PREVALENCIA del mes —202105 tiene
    870 BAJA+2 y quiere 8.092 envios, 202106 tiene 1.098 y quiere 14.788— y la
    prevalencia de 202108 no se conoce. Elegir el K optimo de un mes solo es la
    misma trampa que elegir el pico de una semilla sola.
    """
    ks = np.arange(desde, hasta + 1, paso)
    tabla = pd.DataFrame(
        {nombre: [curva[k - 1] / curva.max() - 1 for k in ks]
         for nombre, curva in escenarios.items()}, index=ks)
    tabla.index.name = "envios"
    tabla["peor_caso"] = tabla.min(axis=1)
    tabla["esperado"] = tabla.drop(columns="peor_caso").mean(axis=1)
    return tabla


def corte_minimax(escenarios: dict[str, np.ndarray], **kw) -> tuple[int, pd.DataFrame]:
    tabla = regret(escenarios, **kw)
    return int(tabla["peor_caso"].idxmax()), tabla


# [Anotación · líneas 257–311] `referencia_202108` lee del parquet base cinco columnas del mes 202108.
#   `verificar_seleccion` exige que todos los elegidos estén en el mes y calcula, para tres marcadores
#   (`ctrx_quarter` en cero, `mcuentas_saldo` negativo, sin acreditación de sueldo), la proporción entre
#   elegidos, entre el resto y el cociente; lanza un error si algún cociente no es finito o si el mayor es menor
#   a 2,0.
def referencia_202108() -> pd.DataFrame:
    """Solo las columnas y el mes que usa verificar_seleccion: evita cargar y ordenar 121 MB por corrida."""
    return pd.read_parquet(DATOS / "competencia_01.parquet",
                           columns=[fe.ID, fe.MES, "ctrx_quarter", "mcuentas_saldo", "cpayroll_trx"],
                           filters=[(fe.MES, "==", MES_COMPETENCIA)])


def verificar_seleccion(elegidos, data, mes: int = MES_COMPETENCIA,
                        minimo_lift: float = 2.0) -> dict:
    """¿La seleccion parece hecha por un modelo, o parece al azar?

    El guard de escribir_envios chequea que los ids EXISTAN en el mes; eso es
    membresia, no correspondencia. Si uno indexa scores de una tabla contra los
    ids de otra —y DuckDB reordena las filas al escribir el parquet— salen ids
    perfectamente validos que no son los que el modelo eligio. Pasa el guard y
    el bot devuelve ganancia NEGATIVA.

    Esto lo caza antes de enviar: los elegidos tienen que estar enriquecidos en
    marcadores de riesgo conocidos. Si no hay separacion, la seleccion es ruido.
    """
    mes_df = data[data[fe.MES] == mes]
    elegidos = np.asarray(elegidos)
    sel = mes_df[fe.ID].isin(set(elegidos.tolist()))
    # FALLA CERRADO. Si los elegidos no son del mes, cond[sel] queda vacio, la media da
    # NaN, el lift da NaN y `NaN < minimo_lift` es False: el guard no levantaba nada
    # JUSTO en el caso de desalineacion para el que se escribio.
    cubiertos = int(sel.sum())
    if cubiertos < len(elegidos):
        raise AssertionError(
            f"solo {cubiertos:,} de {len(elegidos):,} elegidos estan en el mes {mes}. "
            f"Los ids no corresponden a esa foto.")
    marcadores = {
        "ctrx_quarter == 0": mes_df["ctrx_quarter"].fillna(0) == 0,
        "mcuentas_saldo < 0": mes_df["mcuentas_saldo"].fillna(0) < 0,
        "sin sueldo": mes_df["cpayroll_trx"].fillna(0) == 0,
    }
    reporte = {}
    for nombre, cond in marcadores.items():
        p_sel = cond[sel].mean()
        p_resto = cond[~sel].mean()
        reporte[nombre] = (p_sel, p_resto, p_sel / p_resto if p_resto else np.inf)
    lifts = [r[2] for r in reporte.values()]
    if not all(np.isfinite(l) for l in lifts):
        raise AssertionError(
            f"hay lifts no finitos {lifts}: algun marcador no se pudo evaluar. "
            f"Tipicamente los elegidos no corresponden al mes {mes}.")
    mejor = max(lifts)
    if mejor < minimo_lift:
        detalle = " | ".join(f"{k}: {v[0]:.1%} vs {v[1]:.1%} (x{v[2]:.2f})"
                             for k, v in reporte.items())
        raise AssertionError(
            f"la seleccion no se distingue de la poblacion (lift max {mejor:.2f} < "
            f"{minimo_lift}). Casi seguro los scores y los ids vienen de tablas "
            f"con distinto orden de filas. {detalle}")
    return reporte
```

### src/fe_panel.py

Módulo de DuckDB: construye el dataset base con `clase_ternaria` desde el crudo y ofrece generadores de fragmentos SQL (rank, lag, delta, agregados de ventana, pendiente). El camino de la entrega usa `conectar`, `construir_base`, `_fragmento`, `clausula_ventana` y `columnas_numericas`; los generadores `sql_rank`, `sql_lag`, `sql_delta`, `sql_ventana` y `sql_slope` los usan scripts de exploración.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–23] Texto de encabezado que describe las dos partes del módulo (`construir_base` y los
#   generadores de SQL) e importación de duckdb.
"""Feature engineering del panel cliente x mes, en SQL sobre DuckDB.

El panel de la competencia es una fila por (numero_de_cliente, foto_mes). Este
modulo concentra las dos cosas que todos los notebooks necesitan y que hoy
estan copiadas y pegadas entre ellos:

1. `construir_base`: arma el dataset base a partir del crudo, con la
   `clase_ternaria` de siempre mas cuatro columnas de baja a nivel cliente
   (`mes_ultimo`, `mes_baja`, `es_baja`, `k`).
2. Los generadores de SQL (`sql_rank`, `sql_lag`, `sql_delta`, `sql_slope`,
   `sql_ventana`): escriben a mano lo que seria insoportable tipear para 150
   campos, siguiendo los patrones de z402_Feature_Engineering_en_SQL.ipynb.

Uso tipico:

    import fe_panel as fe
    con = fe.conectar()
    fe.construir_base(con, "data/competencia_01_crudo.csv", "data/competencia_01.parquet")
"""

from __future__ import annotations

import duckdb

# [Anotación · líneas 25–46] Constantes: las cinco semillas (261431, 269281, 429899, 560771, 749401), valor
#   anual de un cliente 2.200.000, ganancia por acierto 1.072.500, costo del estímulo 27.500, la lista
#   `COLUMNAS_DE_BAJA` (`mes_ultimo`, `mes_baja`, `es_baja`, `k`, `meses_historia`) y los nombres de las
#   columnas de id, mes y clase.
# --- constantes del curso -------------------------------------------------

#: Las primas que pidio la catedra al arrancar la cursada.
SEMILLAS: list[int] = [261431, 269281, 429899, 560771, 749401]
#: La de toda corrida unica (muestreo, KMeans, RandomForest).
SEMILLA: int = SEMILLAS[0]

#: Valor anual de un cliente premium, segun la minuta de la clase 1.
VALOR_CLIENTE_ANUAL: int = 2_200_000
#: Ganancia esperada de acertar un BAJA+2 (2.2M * 50% de aceptacion).
GANANCIA_ACIERTO: int = 1_072_500
#: Costo de estimular a un cliente.
COSTO_ESTIMULO: int = 27_500

#: Columnas que `construir_base` agrega mirando el futuro del cliente. Sirven para
#: analisis (quien se murio, cuando), pero meterlas en un modelo es leakage puro:
#: `es_baja` y `mes_baja` SON la respuesta. Hay que sacarlas antes de entrenar.
COLUMNAS_DE_BAJA = ["mes_ultimo", "mes_baja", "es_baja", "k", "meses_historia"]

ID = "numero_de_cliente"
MES = "foto_mes"
CLASE = "clase_ternaria"


# [Anotación · líneas 49–69] Macros SQL para pasar `foto_mes` a un índice de mes continuo y volver, sumar
#   meses y contar meses entre dos fotos; `suma_sin_null` trata el NULL como cero y `ratio_seguro` devuelve NULL
#   si el denominador es cero. `conectar` abre una conexión DuckDB y registra las macros.
# --- conexion y macros ----------------------------------------------------

_MACROS = """
-- foto_mes (YYYYMM) <-> indice de mes continuo, para poder sumar y restar meses
create or replace macro mes_indice(m) as ((m // 100) * 12 + (m % 100) - 1);
create or replace macro indice_mes(i) as ((i // 12) * 100 + (i % 12) + 1);
create or replace macro mes_mas(m, n) as indice_mes(mes_indice(m) + n);
create or replace macro meses_entre(a, b) as (mes_indice(b) - mes_indice(a));

-- el nulo de las c*/m* significa "no tiene el producto", o sea cero
create or replace macro suma_sin_null(a, b) as ifnull(a, 0) + ifnull(b, 0);
-- ratio que sobrevive al nulo y a la division por cero: devuelve NULL, que es honesto
create or replace macro ratio_seguro(a, b) as ifnull(a, 0) / nullif(ifnull(b, 0), 0);
"""


def conectar(base: str | None = None) -> duckdb.DuckDBPyConnection:
    """Abre una conexion DuckDB con las macros del proyecto ya registradas."""
    con = duckdb.connect(base) if base else duckdb.connect()
    con.execute(_MACROS)
    return con


# [Anotación · líneas 72–123] Consulta `_SQL_BASE`: arma la grilla completa cliente × mes, marca la presencia
#   del cliente en cada mes (`mes_0`) y con `lead` obtiene la presencia uno y dos meses después. Etiqueta BAJA+2
#   si está al mes siguiente y no a los dos meses, BAJA+1 si no está al mes siguiente y CONTINUA si está en
#   ambos; en otro caso la clase queda en NULL. Calcula por cliente el último mes con foto y la cantidad de
#   fotos, y devuelve las filas del crudo con la clase y las columnas `mes_ultimo`, `meses_historia`, `es_baja`,
#   `mes_baja` y `k`.
# --- dataset base ---------------------------------------------------------

_SQL_BASE = """
with crudo as (
    select * from {origen}
),
periodos as (select distinct {mes} as {mes} from crudo),
clientes as (select distinct {id} as {id} from crudo),
-- el cliente puede faltar un mes y volver, asi que la grilla completa va primero
grilla as (select {id}, {mes} from clientes cross join periodos),
presencia as (
    select g.{id}, g.{mes},
           case when c.{id} is null then 0 else 1 end as mes_0
    from grilla g
    left join crudo c using ({id}, {mes})
),
horizonte as (
    select *,
           lead(mes_0, 1) over (partition by {id} order by {mes}) as mes_1,
           lead(mes_0, 2) over (partition by {id} order by {mes}) as mes_2
    from presencia
),
etiqueta as (
    select {id}, {mes}, mes_0,
           case when mes_1 = 1 and mes_2 = 0 then 'BAJA+2'
                when mes_1 = 0               then 'BAJA+1'
                when mes_1 = 1 and mes_2 = 1 then 'CONTINUA'
           end as {clase}
    from horizonte
),
-- lo mismo pero a nivel cliente: cuando se murio, si es que se murio
vida as (
    select {id},
           max({mes}) filter (where mes_0 = 1) as mes_ultimo,
           count(*)   filter (where mes_0 = 1) as meses_historia
    from etiqueta
    group by 1
),
panel as (select max({mes}) as mes_final from crudo)
select c.*,
       e.{clase},
       v.mes_ultimo,
       v.meses_historia,
       v.mes_ultimo < p.mes_final                       as es_baja,
       if(v.mes_ultimo < p.mes_final,
          mes_mas(v.mes_ultimo, 1), null)               as mes_baja,
       meses_entre(c.{mes}, v.mes_ultimo)               as k
from crudo c
join etiqueta e using ({id}, {mes})
join vida     v using ({id})
cross join panel p
"""


# [Anotación · líneas 126–158] `construir_base` elige `read_csv` (con `sample_size=-1`) o `read_parquet` según
#   la extensión del origen, crea la tabla con la consulta anterior y, si se indica destino, la exporta a
#   parquet con ZSTD o a CSV con encabezado.
def construir_base(
    con: duckdb.DuckDBPyConnection,
    origen: str,
    destino: str | None = None,
    tabla: str = "competencia_01",
) -> duckdb.DuckDBPyRelation:
    """Construye el dataset base: crudo + clase_ternaria + columnas de baja.

    `clase_ternaria` conserva exactamente la semantica de z101_target_sql: es una
    etiqueta *de fila*, y por eso todo BAJA+2 del mes t vuelve a aparecer como
    BAJA+1 en t+1. Las columnas nuevas son *de cliente* y no tienen ese
    solapamiento:

    - `mes_ultimo`     ultimo foto_mes en que el cliente aparece
    - `meses_historia` cuantas fotos tiene en total
    - `es_baja`        True si desaparecio dentro de la ventana observable
    - `mes_baja`       el primer mes en que ya no esta (null si sobrevive)
    - `k`              meses entre esta foto y la ultima; 0 = su ultima foto

    La cohorte de bajas es entonces `select distinct numero_de_cliente where es_baja`,
    sin doble conteo, y `k` alinea a cada cliente en su propio reloj.
    """
    lector = (
        f"read_csv('{origen}', sample_size=-1)"
        if origen.endswith((".csv", ".csv.gz"))
        else f"read_parquet('{origen}')"
    )
    sql = _SQL_BASE.format(origen=lector, id=ID, mes=MES, clase=CLASE)
    con.execute(f"create or replace table {tabla} as {sql}")
    if destino:
        formato = "PARQUET, COMPRESSION ZSTD" if destino.endswith(".parquet") else "CSV, HEADER TRUE"
        con.execute(f"copy {tabla} to '{destino}' (format {formato})")
    return con.table(tabla)


# [Anotación · líneas 161–193] `_fragmento` convierte una lista de expresiones en un tramo de SELECT que
#   empieza con coma. `sql_rank` genera una función de ventana por mes para cada campo (por defecto
#   `percent_rank`), `sql_lag` el valor de n meses atrás y `sql_delta` la diferencia con ese valor.
# --- generadores de SQL ---------------------------------------------------
# Todos devuelven un fragmento de SELECT que empieza con coma, listo para pegar
# despues de la ultima columna de una consulta.


def _fragmento(lineas: list[str]) -> str:
    return "".join(f"\n  , {linea}" for linea in lineas)


def sql_rank(campos: list[str], particion: str = MES, funcion: str = "percent_rank") -> str:
    """Rankea cada campo dentro de su mes: el antidoto al data drifting.

    Con inflacion, "tiene 48.000 pesos" no es comparable entre marzo y agosto,
    pero "esta en el percentil 70 de su mes" si. `funcion` acepta cualquiera de
    percent_rank, cume_dist, ntile(4), ntile(10), rank, dense_rank.
    """
    llamada = funcion if "(" in funcion else f"{funcion}()"
    sufijo = funcion.replace("(", "_").replace(")", "").replace(" ", "")
    return _fragmento(
        [f"{llamada} over (partition by {particion} order by {c}) as {c}__{sufijo}" for c in campos]
    )


def sql_lag(campos: list[str], n: int = 1, ventana: str = "historia") -> str:
    """El valor de hace n meses del mismo cliente."""
    return _fragmento([f"lag({c}, {n}) over {ventana} as {c}__lag{n}" for c in campos])


def sql_delta(campos: list[str], n: int = 1, ventana: str = "historia") -> str:
    """Cuanto cambio el campo respecto de hace n meses."""
    return _fragmento(
        [f"{c} - lag({c}, {n}) over {ventana} as {c}__delta{n}" for c in campos]
    )


# [Anotación · líneas 196–213] `sql_ventana` genera agregados (por defecto promedio, mínimo y máximo) sobre
#   una ventana nombrada y `sql_slope` la pendiente de regresión del campo contra `cliente_antiguedad`
#   (`regr_slope`).
def sql_ventana(campos: list[str], aggs: tuple[str, ...] = ("avg", "min", "max"), ventana: str = "historia") -> str:
    """Agregados moviles sobre la ventana nombrada que se pase."""
    return _fragmento(
        [f"{a}({c}) over {ventana} as {c}__{a}" for c in campos for a in aggs]
    )


def sql_slope(campos: list[str], eje: str = "cliente_antiguedad", ventana: str = "historia") -> str:
    """La pendiente de minimos cuadrados del campo contra el eje temporal.

    Es la variable que encarna la hipotesis de negocio de la materia: un cliente
    no se va de golpe, se va apagando. Un ctrx_quarter de 40 no dice nada; un 40
    con pendiente -12 es un cliente en caida libre. Como `cliente_antiguedad`
    crece exactamente 1 por mes, la pendiente se lee "cuanto gana o pierde por mes".
    """
    return _fragmento(
        [f"regr_slope({c}, {eje}) over {ventana} as {c}__slope" for c in campos]
    )


# [Anotación · líneas 216–238] `clausula_ventana` devuelve la cláusula WINDOW con partición por cliente y
#   orden por mes, con un marco opcional. `columnas_numericas` consulta `information_schema` y devuelve las
#   columnas de tipo numérico de una tabla, sin las llaves, la clase, las columnas de baja ni las que se pasen
#   en `excluir`.
def clausula_ventana(
    nombre: str = "historia",
    orden: str = MES,
    marco: str | None = None,
    particion: str = ID,
) -> str:
    """La clausula WINDOW que nombra la ventana una sola vez.

    `marco=None` usa toda la historia previa del cliente. Ojo con el clasico
    'rows between 3 preceding and current row': son CUATRO meses, no tres.
    """
    marco = f" {marco}" if marco else ""
    return f"\nwindow {nombre} as (partition by {particion} order by {orden}{marco})"


def columnas_numericas(con: duckdb.DuckDBPyConnection, tabla: str, excluir: tuple[str, ...] = ()) -> list[str]:
    """Las columnas numericas de una tabla, sin las llaves ni el target."""
    fijas = {ID, MES, CLASE, "mes_ultimo", "mes_baja", "es_baja", "k", "meses_historia", *excluir}
    filas = con.execute(
        f"select column_name, data_type from information_schema.columns where table_name = ?", [tabla]
    ).fetchall()
    numericos = ("BIGINT", "INTEGER", "DOUBLE", "FLOAT", "DECIMAL", "HUGEINT", "SMALLINT", "TINYINT")
    return [c for c, t in filas if c not in fijas and any(t.startswith(n) for n in numericos)]
```


## Explicaciones del alumno (texto original)

### README.md

> # DMEyF 2026 · Primera Competencia
>
> Agustina Razanov · Data Mining en Economía y Finanzas (UBA), comisión de los lunes.
>
> Objetivo: elegir a qué clientes de la foto `202108` mandar el estímulo de retención, maximizando
> `+1.072.500` por cada `BAJA+2` acertado y `−27.500` por cada estimulado que no lo es. El bot de Zulip
> `@competencia-uno` devuelve la ganancia pública (~25% de agosto) de cada archivo enviado.
>
> > Estado al 2026-10-10 por la tarde. **La entrega es `c241_rondas2000_ens20_14000`** (sección 1), reproducida
> > bit a bit con `reproducir.py`. El diario completo, con retractaciones, está en `docs/diario_competencia.md`;
> > los gráficos, en `notebooks/`.
>
> ## 1. La entrega, en una tabla
>
> | Pieza | Elección | Dónde |
> | --- | --- | --- |
> | Datos | `competencia_01_crudo.csv` → `clase_ternaria` con horizonte 2 (`fe_panel.construir_base`) | `scripts/c100` |
> | Variables | las 150 crudas + **lag 1, delta 1, lag 2 y delta 2 de todas** (750 columnas); `ccajas_depositos` → NA en 202105 | `scripts/c200_lags_todo.py` |
> | Fuera del modelo | `numero_de_cliente`, `foto_mes`, las columnas de baja, `Visa_Finiciomora`, `Master_Finiciomora` (ceros inyectados en 202105 y 202108) | `src/competencia.py` |
> | Clase | positivo = `BAJA+1` ∪ `BAJA+2`, con `BAJA+1` pesando 0,25 (`target='pesos'`); pesos 0,5 y 1 perdieron (−2,0 / −1,4), BAJA+2 solo perdió −5,3 | `scripts/c242`, `c243`, `c213` |
> | Hiperparámetros | receta de Denicolay (Zulip `J-Clase 08 > En Limpio`): `max_bin` 31, `min_data_in_leaf` 0, `feature_fraction` 0,5, `feature_fraction_bynode` 0,2, `learning_rate` 0,005, 83 hojas, `min_sum_hessian_in_leaf` = 12,79 × filas / 326.184, **2.000 rondas** | `scripts/c201_receta_lags.py`, `c241` |
> | Entrenamiento | 202103–202106, 654.066 filas, 8.067 positivos, sin undersampling | `scripts/c210_variante.py` |
> | Semillas | 261431, 269281, 429899, 560771, 749401 + 15 sorteadas con `np.random.seed(261431)` | `src/competencia.py` |
> | Ensamble | promedio de **rangos** (no de probabilidades) de las 20 semillas | `competencia.ensamble_por_rank` |
> | Corte | **14.000**: pico de la curva pública con 20 archivos por punto, y minimax del regret local a horizonte 2 en 13.500 (sección 3) | `scripts/c216_captura_foldB.py` |
> | Archivo entregado | `experimentos/c241_rondas2000/envios_14000/c241_rondas2000_14000_ens20.csv` (en el ledger, submit `c241_rondas2000_ens20_14000`), un solo archivo, SHA-256 `657d747addc61efad64145ec9cef550c29c50c5ce283745f176d243270bb9d2e`, 103,79 público; reenviado como último submit el 10-oct 19:05 | `reproducir.py` |
>
> ## 2. Cómo reproducir
>
> ```bash
> pyenv local facultad          # Python 3.14, duckdb 1.5.5, lightgbm 4.7.0, pandas 2.3.3, numpy 2.5.3
> python reproducir.py --rondas 2000 --salida entrega_final.csv      # ~4 h en 8 cores
> ```
>
> `reproducir.py` parte del crudo de la cátedra en `data/` (symlink a `../dmeyf2026/monday/data`),
> reconstruye la clase, construye la historia (lag 1, delta 1, lag 2, delta 2 de las 150 variables),
> ordena las filas por `(numero_de_cliente, foto_mes)` —DuckDB no garantiza el orden y LightGBM depende
> de él—, entrena las 20 semillas con la receta, ensambla por rango y escribe los 14.000 ids ordenados.
> Imprime el SHA-256 y lo compara con el del archivo entregado: **el 10-oct dio `657d747a…`, idéntico**.
>
> Dos detalles que decidieron el bit a bit: `deterministic=True`, `force_col_wise=True` y 8 hilos; y **un
> `lgb.Dataset` nuevo por semilla**. LightGBM muestrea 200.000 filas con la semilla para construir los bins, así
> que un `Dataset` compartido entre semillas entrena otros modelos (la primera corrida difirió en 157 de
> 14.000 ids por eso). `scripts/c280_verificar_semilla.py` entrena una semilla y la compara con la registrada.
>
> Para medir sin reentrenar: los modelos quedan en `experimentos/<exp>/modelo_<semilla>.txt` y los
> scores de 202108 en `scores_202108_s<semilla>.parquet`; `scripts/c201_cortar.py` re-corta en segundos.
>
> ## 3. Cómo se midió
>
> El público es ~25% de agosto. Entre semillas de un mismo modelo el desvío por archivo es **1,8–2,5**, así que
> la media de 5 archivos tiene sd ≈ 0,9 y la de 20, ≈ 0,45. Reglas que valen para todo lo que sigue:
>
> - **La referencia honesta es la media de 20 archivos (103,85)**, no el mejor submit. Las primeras 5 semillas
>   salieron con suerte en los dos modelos de referencia (+1,2 y +1,7 sobre su media de 20): la "maldición del
>   ganador" medida en casa.
> - Una variante medida con 5 archivos se compara contra la franja 103,85–105,51 (media de 20 / mismas 5 semillas
>   de la receta). Lo que cae adentro no se distingue de la receta. **Se adopta solo con 20 contra 20.**
> - Cada submit se registra con su hipótesis y contra qué se compara antes de enviarse (`ledger/v_submits.csv`).
>
> ### Lo que movió el público
>
> | cambio | público | contra | lectura |
> | --- | ---: | --- | --- |
> | línea de base: 150 col, params de `z701`, `BAJA+2` solo, 11.000 | 89,02 | — | el esqueleto funciona |
> | `BAJA+1` pesando 0,25, 20 semillas, 11.000 | 91,36 | 89,02 | dentro del ruido; la evidencia es de los folds |
> | corte 9.000 de ese ranking | 94,22 | 91,36 | la base pica en 9.000 y cae 11 M hasta 15.000 |
> | FE propio (`z402`, 228 col) / FE histórico de 80 col + sacar préstamos + deflactar | 91,11 / 87,62 | 94,22 / 92,62 | pierden; el profesor lo confirmó: no sacar variables para 202108 |
> | **lags/deltas 1 y 2 de las 150 + receta de Denicolay**, 20 semillas, 10.000 | **100,03** | 93,24 | **+6,8 pareado (mismas semillas, corte y partición)** |
> | desacople: lags con params viejos / base con la receta, 10.000 | 96,43 / 97,06 | 93,24 | +3,2 y +3,8, aditivos |
> | el mismo ranking a 14.000, 20 semillas | 103,00 | 100,03 | el óptimo se corrió a la derecha |
> | **2.000 rondas en vez de 1.000**, 20 semillas, 14.000 | **103,85** | 103,00 | +0,85, y +0,85 a +1,56 en los cinco cortes medidos (tabla de abajo) |
> | ensamble por rango de las 20 semillas, un archivo | 103,79 | 103,85 | el ensamble reduce varianza, no "gana": **la entrega** |
>
> ### La curva de corte, 20 archivos por punto (sd ≈ 0,45)
>
> | corte | 10.000 | 12.000 | 13.000 | 13.500 | **14.000** | 14.500 | 15.000 |
> | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
> | 1.000 rondas (`c201`) | 100,03 | — | 101,74 | 102,69 | **103,00** | 102,50 | 101,32 |
> | 2.000 rondas (`c241`) | — | 101,12 | 103,30 | 103,56 | **103,85** | 103,37 | 102,81 |
>
> El pico es 14.000 para los dos. Lo que el público no puede decir: entre 12.000 y 14.000 el salto son ~15 bajas en
> 500 clientes públicos (3,1% de precisión contra 2,5% de equilibrio), con desvío ±4 que ninguna semilla achica.
> Fuera del público, la captura de junio a horizonte 2 (`c216`, fold B) da óptimos entre 13.500 y 14.000 según
> la prevalencia de agosto, con el minimax del regret en 13.500 (`notebooks/n02_experimentos.ipynb`, sección 8).
>
> ### Las variantes sobre la receta, 5 archivos cada una, a 14.000, contra la franja 103,85–105,51
>
> | familia | variante | público | lectura |
> | --- | --- | ---: | --- |
> | hiperparámetros | 3.000 rondas · 127 hojas · ff 0,4 · ff 0,3 | 103,80 · 104,12 · 104,26 · 103,89 | dentro de la franja |
> | hiperparámetros | hessiano × 0,5 · × 2 | 102,23 · 101,49 | pierden |
> | target y meses | pseudo-etiquetas de julio · sin marzo · BAJA+2 solo | 103,21 · 100,95 · 98,82 | neutro · pierde · pierde |
> | datos y drift | comisión deflactada · aguinaldo · calendario · lags de ranks | 104,56 · 104,52 · 103,49 · 103,16 | dentro de la franja |
> | columnas nuevas | 11 proporciones (815 col) · sumas, conteos y rachas (848 col) | 104,62 · 103,27 | dentro de la franja aunque se llevan 20–29% del gain |
> | menos columnas | sin las 52 nunca usadas (698) · solo las 392 del 99% del gain | 102,71 · 102,05 | pierden en las dos intensidades |
> | segundo modelo | horizonte 1 (BAJA+1, hasta julio) mezclado por rango, pesos 0,15 / 0,3 / 0,5 / 0,7 / 1 | 105,70 / 105,75 / 105,67 / 103,65 / 99,92 | plano hasta 0,5, se hunde después |
> | sacar las importantes | sin la familia `ctrx_quarter` (745) · sin las 10 familias top (700) · sin una de cada par con \|r\| ≥ 0,95 (708) | 102,71 · 87,21 · 104,12 | pierde · se derrumba · dentro de la franja |
>
> Las tres últimas (`c290`, `c291`, `c292`, 10-oct) son la prueba de la clase de ensambles llevada a LightGBM: en el
> random forest sacar `ctrx_quarter` subía la ganancia; acá con muestreo de columnas la descorrelación ya está y lo
> que queda es pérdida de información. Sin las 10 familias que concentran el 45% del gain el modelo vuelve al
> nivel de la primera semana: la señal no se recupera desde las otras 140. Sacar las 42 casi duplicadas no cambia nada.
>
> ### Validación interna
>
> - **Fold A (`c222`)**: la búsqueda bayesiana (AUC en junio y julio) eligió hiperparámetros que en mayo, mes que no
>   vio, quedan debajo de la receta. Con ~1.100 positivos por mes el error muestral del AUC es del tamaño de la mejora.
> - **Fold B (`c216`)**: captura a horizonte 2 → curva de ganancia esperada por prevalencia y regret por corte.
> - **Local vs público (primera semana)**: seis experimentos con las dos medidas, Spearman 0,26. La validación en un
>   mes no distinguía variantes; los lags no se podían ver localmente porque marzo no tiene mes anterior.
>
> ## 4. Lo que no funcionó, y por qué queda documentado
>
> - **Búsqueda bayesiana con CV dentro del mes**: ganaba en CV y perdía fuera de tiempo. Causa: los
>   `BAJA+2` de marzo son `BAJA+1` de abril, y el split por filas los ponía a ambos lados (leakage de gemelos).
> - **Cadena de validación a horizonte 1** (`c144`–`c147`, `c166`): 99,5% de los positivos de validación
>   ya estaban en el entrenamiento. Inválida. Los folds limpios son A `[03]→05`, B `[03,04]→06`, C `[03,04,05]→07`.
> - **Sacar marzo, decaimiento por antigüedad, entrenar sólo con el mes reciente**: atacaban "los meses
>   viejos son malos"; lo que pesa es la distancia al mes a predecir, y 202106 ya está a dos meses de agosto.
> - **Reducción de dimensionalidad**: poda con canaritos en cinco niveles (nunca ayudó), sacar las 52 columnas que
>   ningún árbol usa (−1,1) y quedarse con las 392 que juntan el 99% del gain (−1,8). Las columnas "muertas" sirven
>   de ruido útil en el muestreo de columnas de cada árbol, o la importancia en train no es la que vale en agosto.
> - **Validación adversaria**: AUC 0,9998 por dos relojes de calendario (`*_fultimo_cierre`); sacarlos no
>   cambió nada. Separable no implica perjudicial.
> - **El instrumento**: durante una semana se mandó un archivo por submit cuando se podían mandar veinte; después
>   se usó el desvío entre semillas como si fuera el ruido de la partición; y las primeras 5 semillas se tomaron
>   como referencia cuando estaban +1,7 sobre la media de 20. Las tres cosas dejaron comparaciones debajo del
>   piso de ruido y se retractaron.
> - **Los folds no ven los lags**: marzo no tiene mes anterior y lag 2 está vacío en todo el
>   entrenamiento de los folds A y B. Por eso "el FE pierde" se sostuvo tanto tiempo: lo medimos donde
>   no podía ganar.
>
> ## 5. Trazabilidad
>
> Cada experimento, submit, archivo y respuesta del bot está en el ledger de Postgres (`src/registro.py`) y
> exportado a `ledger/*.csv`. Un submit se registra con hipótesis y delta **antes** de enviarse
> (`scripts/enviar.py`), y la respuesta cruda del bot se guarda al volver. `ledger/v_submits.csv` es el
> leaderboard propio completo; `enviado_en` es la hora del mensaje al bot en Zulip. Los CSV enviados están en
> `experimentos/`, con su SHA-256 en el ledger.
>
> `notebooks/n01_eda.ipynb` es el dataset mirado antes de modelar; `notebooks/n02_experimentos.ipynb` es todo lo
> de arriba en gráficos, generado desde el ledger y los scores cacheados.
>
> ## 6. Fuentes
>
> - Zulip de la materia (archivado en `../zulip/`): `J-Clase 08 > En Limpio` (receta), `J-Clase 08 >
>   venciendo Primero Competencia` (préstamos), `Cartelera > Entrega a Primera Competencia` (reglas de entrega),
>   `general > Private vs Public` (tabla público/privado del 8-oct). Resumen con ids en `docs/pistas_profesor.md`.
> - Repos públicos de compañeros con las mismas reglas: `ezequielabregu/DMEyF_competencia_1` (110,25) y
>   `farpp8/dmeyf2026-competencia01` (103,18). De ahí salió la pista de los lags de todo.
> - Libro de la Asignatura, §1.5.1: reproducibilidad exacta desde el dataset original, semillas incluidas.

### CLAUDE.md

> # Primera Competencia DMEyF 2026 — mapa del repo
>
> Repo propio de la competencia (antes vivía en `dmeyf2026/monday/competencia/`, el fork de la cátedra).
> Remoto `origin` = `[correo]:agustinarazanov/dmeyf.git`; **se commitea y pushea directo a `main`**
> (git plano; GitButler quedó instalado pero el workspace se desarmó con `but teardown` el 8-oct).
> Cierra el **sábado 10 de octubre 23:59 ART según el reloj del bot** (`2026-10-11T03:01:01` UTC);
> Zulip dice domingo 11. Se entrega el sábado.
>
> El diario completo de decisiones, retractaciones y mediciones está en `docs/diario_competencia.md`
> (1.600 líneas; es el `CLAUDE.md` histórico). Este archivo es solo el mapa y las reglas.
>
> ## Dónde está cada cosa
>
> ```
> competencia-1/
> ├── README.md                 el reporte: modelo final, cómo reproducir, qué se probó y qué dio
> ├── CLAUDE.md                 este mapa
> ├── reproducir.py             LA ENTREGA: del crudo al CSV entregado, bit a bit, con las semillas
> ├── src/                      lo que se importa
> │   ├── competencia.py        datos, ganancia, corte, caché de modelos, escritura de envíos
> │   ├── registro.py           el ledger en Postgres (base `competencia`, contenedor zulip-postgres)
> │   ├── fe_panel.py           panel base + generadores de SQL (lags, deltas, ranks, ventanas)
> │   └── v_estilo.py           estilo de los gráficos (paleta validada)
> ├── scripts/                  lo que se corre a mano
> │   ├── cNNN_*.py             un experimento por script, numerados (c100–c280)
> │   ├── enviar.py             ledger -> bot -> respuesta -> ledger, un submit por comando
> │   └── ledger_export.py      Postgres -> ledger/*.csv
> ├── notebooks/                n01_eda (el dataset), n02_experimentos (lo que se probó, del ledger)
> ├── experimentos/<cNNN>/      modelos (.txt), scores (.parquet), envios/*.csv   <- solo los CSV y
> │                             json/md se versionan; modelos y scores pesan 4 GB y se regeneran
> ├── ledger/                   export CSV de las tablas del ledger (experimento, submit, archivo,
> │                             resultado), para que la trazabilidad viaje con el repo
> ├── docs/                     diario, pistas del profesor, backlog, diagnóstico de FE
> └── data -> ../dmeyf2026/monday/data   symlink; los parquet no se versionan
> ```
>
> Las clases y los notebooks de la cátedra siguen en `../dmeyf2026/monday/` (ver su `CLAUDE.md`).
> El archivo de Zulip está en `../zulip/` (Postgres `zulip`, mismo contenedor). Las notas de clase y
> los apuntes por notebook, en el vault de Obsidian `DMEyF/`.
>
> ## Reglas de la casa (no negociables)
>
> 1. **Un submit mide una hipótesis con fundamento**, escrita antes en el ledger con su delta contra una
>    referencia. Nunca al azar, nunca para "dejar vigente" el mejor puntaje: eso se hace solo cuando la
>    usuaria lo indique, cerca del cierre. El cupo diario se gasta entero midiendo: **17** desde el 8-oct (el bot pasó de x/13 a x/17 sin anuncio); si rechaza el 14º, volver a 13. Renueva 21:00 ART.
> 2. **Nada se envía sin pasar por `scripts/enviar.py`**, que registra primero (`estado='preparado'`) y envía
>    después. Sin `--enviar` solo registra e imprime el resumen para aprobar.
> 3. **Todo lo que cuesta cómputo se persiste**: modelos por semilla en `experimentos/<exp>/modelo_*.txt`,
>    scores de 202108 por semilla en `scores_202108_s<semilla>.parquet`. Re-cortar es gratis.
> 4. **Cada submit es reproducible**: dataset, params, meses, target, semillas y corte quedan en el
>    ledger; el CSV se escribe ordenado por id para que un `diff` verifique la reproducción.
> 5. **`es`/`y` salen SIEMPRE del mismo DataFrame que las predicciones.** DuckDB no garantiza el orden
>    de las filas; ya costó un submit con ganancia −49,86 y dos mediciones imposibles.
> 6. **No sacar variables para predecir 202108.** Préstamos incluidos. Lo dijo el profesor con sus
>    experimentos (Zulip 2026-10-05) y lo confirmaron tres mediciones públicas.
> 7. **Comparaciones públicas con 20 archivos de una semilla**, mismas semillas y mismo corte que la
>    referencia. Ruido de partición ±3 M entre modelos, ±4 M entre cortes anidados: reportar la
>    diferencia en clientes (÷1,1 M), el sd por sorteo y el z.
>
> ## Entorno
>
> pyenv `facultad` (Python 3.14) para todo lo de modelos; pyenv `zulip` para `scripts/enviar.py` (tiene el
> módulo `zulip` además de `psycopg`). Después de un reboot: `open -a Docker && docker start zulip-postgres`.
>
> Las pistas del profesor, con ids de Zulip, están en `docs/pistas_profesor.md`.
>
> ## Estado
>
> Ver `README.md` para el modelo vigente y la tabla pública. Última novedad: `c201_receta_lags`
> (lags/deltas 1 y 2 de todo + receta de Denicolay) cruzó los 100 públicos; su óptimo de corte está en
> la banda 13.000–14.500, no en 9.000–10.000 como la base.
>
> ## Reglas de feature engineering (9-oct, Agustina)
> - **Si una variable se escala, deflacta, rankea o normaliza, entra la transformada y sale la original.**
>   Un cociente o una suma no es una transformación de una columna, es información nueva: ahí las crudas
>   se quedan (c260, c261).
> - **Reducción de dimensionalidad** se considera siempre (no contradice la regla 6: esa prohíbe sacar variables
>   *por drift*; esto es por importancia medida), pero por importancia medida, no por PCA (el
>   profesor lo lista como inútil) ni por canaritos (los dejó para la segunda). Con `feature_fraction` 0,5 ×
>   `bynode` 0,2 cada split ve ~75 columnas al azar; las muertas le roban lugar a las vivas.
>   `experimentos/c241_rondas2000/importancia_20.csv` es la medición base (20 modelos).

### docs/pistas_profesor.md

> # Pistas del profesor (Gustavo Denicolay) para la Primera Competencia
>
> Recopiladas de Zulip (archivo en `../zulip/`, ids entre corchetes). Son las fuentes de autoridad del
> curso; cuando una medición nuestra las contradice, se mide de nuevo antes de descartarlas.
>
> ## La receta oficial — `J-Clase 08 > En Limpio` [193837–193846], 6-oct
> - Data quality: `ccajas_depositos` → NA en 202105 (todos sus valores son cero).
> - FE histórico: "es superador agregar lags y delta lags de orden 1 y 2".
> - Training: sin undersampling en la búsqueda ("son muy pocos meses"); métrica AUC.
> - Fijos: `max_bin` 31, `min_data_in_leaf` 0 ("muy importante"), `feature_fraction` 0,50,
>   `feature_fraction_bynode` 0,20, `learning_rate` 0,005 ("muy importante").
> - Bayesianos: `num_iterations`, `num_leaves`, `min_sum_hessian_in_leaf`.
> - Entrega: varios modelos (10+) con hiperparámetros distintos, entrenados en 202103–202106, sin
>   undersampling, promediando probabilidades por cliente. Probar cortes 10.000 / 10.500 / 11.000.
> - FE hojas de Random Forest y canaritos asesinos: "tbd" (nunca los completó para esta competencia).
>
> ## Drift y variables — `J-Clase 08 > venciendo Primero Competencia` [192777, 192801, 192811], 5-oct
> - "¿Vos me has visto escribir que para predecir 202108 hay que eliminar alguna variable?" — **no**.
> - Sobre sacar los préstamos (la "salsa mágica" que ganaba en junio): "hice los experimentos y
>   funciona peor". Siempre que cambia el mes a predecir hay que rehacer los experimentos.
> - El `help` del bot no fija tope de filas; los 8.000–15.000 son del mensaje [191492].
>
> ## La línea de muerte — Tutorias [192556] y Libro p. 11
> - "Para entender en dónde se encuentran parados contra el Public Leaderboard de 202108, si se caen
>   del precipicio de los 100k o no."
> - Libro: superar la Línea de Muerte da un 5; lo de arriba se mapea a [5, 10]. El valor se publica
>   antes del cierre, el script nunca.
>
> ## Public vs Private — `general > Private vs Public` [197324], 8-oct 18:56
> Sobre todos los submits del curso con 10 o más archivos (≈7.300):
>
> | público | private < 300 | private > 300 | % > 300 |
> | --- | ---: | ---: | ---: |
> | < 95 | 2.659 | 25 | 1% |
> | 95–100 | 1.706 | 115 | 6% |
> | 100–105 | 1.829 | 327 | 15% |
> | > 105 | 349 | 257 | 42% |
>
> `mean(Public/Private) = 2,98`. "Bastante bien si se considera que los submits sucesivos van
> overfiteando el Public Leaderboard, ya que la gente solo vuelve a subir cosas parecidas a las que
> dieron bien en lo que puede ver." → el umbral que mira en private es **300 M** (≈ 100 público × 3).
>
> ## Canaritos y foco — `J-Clase 06 > Canaritos y selección de variables` [196876], 8-oct 14:53
> - "El uso de canaritos para selección de variables es útil recién para la Segunda Competencia."
> - "La selección de variables NO la hacemos para mejorar el poder predictivo del modelo" (es para
>   hacer lugar en memoria). "Ahora que estás entrenando en 4 meses para la predicción final, no te
>   hace falta hacer espacio."
> - "Conclusión 1: no te compliques la vida al pedo en esta Primera Competencia. Conclusión 2:
>   focalizate en cosas que SÍ incrementen la ganancia, y en no estar teniendo en algún lado un
>   'moquito' que haga que estés por abajo de 100M en el Public Leaderboard."
>
> ## Pseudo-etiquetado — `J-Clase 06 > Entrenar en CUATRO meses` [190539–190562], 25-sep
> Entrenar en los meses con clase, predecir una clase artificial `{BAJA+1, BAJA+2}` en los meses sin
> clase con un corte de probabilidad, reentrenar con todos. Presentado como "bomba lógica" para que
> los agentes "muerdan el polvo": él mismo lo pone a prueba, no lo afirma.
>
> ## Lo que lista como inútil — `off-topic > Instructional Scaffolding` [184534], 21-ago
> Deep learning, PCA, imputación de nulos, tratamiento de outliers, AutoML, técnicas para el
> desbalanceo, variables derivadas de clustering. "Los mejores modelos se hacen sin reducir la
> dimensionalidad y sin imputar nulos" [183214]. `scale_pos_weight`: "ni en pedo" [187068].
>
> ## Semillas y overfitting — Cartelera [191495], 2-oct
> "Generan varios modelos, cada uno solamente cambiando el hiperparámetro seed... esos múltiples
> archivos (hasta 20) son los que entregan en un submit, y el bot les devuelve la media y la varianza,
> con lo cual reducen enormemente el overfitting (técnicamente NO lo eliminan por completo)."
>
> ## De dónde sale la receta — `J-Clase 06 > un detalle insoslayable` [189058–189080], 18-sep
> - `z495_GustavoPasquini.ipynb` (adjunto en [187193]) optimiza solo `num_iterations`, `num_leaves` y
>   `min_sum_hessian_in_leaf`, y hace **4 × 3 = 12 iteraciones no inteligentes y 0 inteligentes**:
>   "simplemente se está quedando con la mejor de las 12". La receta de `En Limpio` no es un óptimo fino.
> - Rangos de su bayesiana ("MUY generosos, no hay trampa"): `num_iterations` 64–4096, `num_leaves`
>   16–2048, `min_sum_hessian_in_leaf` **1e-06–0,1 absoluto**, sobre ~13k filas (undersampling 0,1 en la
>   búsqueda, métrica average_precision). Por fila es hasta ~7e-6: la zona donde `c220` encontró su
>   óptimo y que después no transfirió (`c221` público, `c222` mayo).
> - El `12,791817 × filas / 326.184` **no es de Denicolay**: 326.184 son las filas de 202103+202104, es la
>   calibración de Ramírez. Nuestro barrido ×0,5/×2 (12,8 y 51 absolutos) pisa una región que ni la
>   cátedra ni `c220` recorrieron.
>
> ## Entrega — confirmado por la tutora Silvana Contreras, `Tutorias > J_08` [197392], 8-oct 19:41
> - "Para la competencia final **vale el último que hayas enviado** y debe ser una submission de **un
>   solo archivo**." El bot lo repite en cada `list`: "The private gain is only known for your LAST
>   pre-deadline submission". → el último submit antes del cierre tiene que ser la entrega, de un archivo.
> - `z-Entrega Final > Primera Competencia` [191074], 29-sep: ahí se postea el link a GitHub con
>   scripts/notebooks e instrucciones "de forma que la cátedra sea capaz de replicar en forma exacta su
>   predicción final". **Al 8-oct 22:40 nadie posteó nada en ese tópico, nosotras tampoco.**
> - `general` [191563], 2-oct: "ir cambiando de a un registro para subir en el Public" es "actividad
>   ilícita". Nuestros submits de curva de corte van de a 500 y se registran como medición con hipótesis.
> - `J-Clase 06 > Canaritos` [197252], 8-oct 18:18: **Public ≈ 25% / Private ≈ 75%** de 202108. "El único
>   que cuenta para la aprobación y nota" es Private > 300. Al 8-oct 18:46 no hay leaderboard global
>   publicado; el podio eran "tres alumnas, una del lunes y dos del jueves" y "va bajando día a día".
>
> ## La guía de la tutoría previa al cierre — Tutorias [193986], PDF en Drive
> Es el cuestionario de la cátedra y sirve de índice para el README: variables rotas; drift por
> inflación / dólar / UVA / ranking / ranking con cero fijo; imputación; FE intra e histórico; canaritos;
> particiones y meses; undersampling sí/no; target {BAJA+1, BAJA+2}; métrica; cuántas iteraciones de BO,
> qué entra y con qué bordes; feature importance; meses del final; ensembles; cómo deciden la cantidad
> de envíos; plan para los días que quedan; "¿identificaron cosas que tienen que hacer sí o sí?".
> Cada ítem tiene un experimento en el diario (c215 rank, c167 cero fijo, c127 deflactar, canaritos,
> c213/c242/c243 target, c220/c222 BO, c245 ensambles, curva de corte).
>
> ## Cerrado con medición (sesión monday-3d, 8-oct): `*_fultimo_cierre` y `Visa_mpagado`
> Laura Pasquini [192773] reportó ceros raros; Denicolay no respondió. Medido sobre `competencia_01.parquet`:
> `*_fultimo_cierre` es reloj puro (moda por mes 1/2/5/0/3/6; el 0 de junio es el día modal, 113.299
> ceros, BAJA+2 0,52% con cero vs 0,47% sin); `Visa_mpagado` en 05 y 08 pasa de ~141k ceros a ~114k, o sea
> ~27k clientes con pago real por ciclo. Nada que reparar.
>
> ## Cierre
> - Zulip [189817]: domingo 11-oct 23:59 ART. `help` del bot (6-oct): `2026-10-11T03:01:01` (UTC → sábado
>   10 23:59 ART). Una tutora el jueves 8: "a 3 días del cierre" (→ domingo). **Sin zanjar; la entrega
>   va adentro el sábado.**
> - Cupo del bot: 13/día hasta el 8-oct 16:11; desde entonces reporta `x/17`, sin anuncio en Zulip.
>
> ## Barrido del 10-oct a la mañana (mensajes desde el 9-oct 12:00): nada que mueva el modelo
>
> - **Silvana Contreras, `general > Private vs Public` [198194, 198197]:** "ayer se recomendó intensamente que no saquen
>   la conclusión de que les está yendo bien por la medida del leaderboard público"; la recomendación para los días
>   que quedan es construir el baseline de `J-Clase 08 > En Limpio` (lo que ya es nuestra entrega) y optimizar
>   **sin undersampling**. Propone comparar modelos "semilleados" con **Wilcoxon sobre vectores de ganancia** [198178]
>   (es lo que hacemos con 20 archivos contra 20, mismas semillas).
> - **Karina Formoso [198148]** (tabla): dos modelos con 50 semillas, corte 13.000: público 105,49 / 106,54 promediados,
>   106,25 / 104,33 como 10 archivos de 5 semillas. Mismo orden de magnitud que el nuestro; su meseta local en junio
>   va de 11.400 a 14.600 y la tutora le objeta que una meseta de 3.000 envíos "es un mesetón".
> - **Florencia Rodriguez [198165]:** sus modelos > 100 son exactamente la receta (03–06, ambas bajas positivas,
>   `ccajas_depositos` NA en mayo, lags 1 y 2 + deltas, 762 variables, préstamos adentro).
> - **Emmanuel Valdez [198166, 198182]:** sugiere **rankear las variables entre −1 y 1** (rank con signo: positivos en
>   (0, 1], negativos en [−1, 0), 0 → 0) e imputar nulos con el mes anterior o el promedio. Sin medición publicada.
>   Nuestra medición previa de rank por mes (`c150_pormes`, dataset viejo) perdió −2; sobre lags12 no se midió.
> - **German Reintgen [199199]:** curva de ganancia en junio (train marzo–abril), 20 semillas + ensamble por promedio
>   de probabilidades: pico ~12.000 en test local, igual que el sesgo chico de nuestro fold C.
> - Alejandro Bolaños arregla `list submit` del bot (sale truncado) [199714]. Nadie posteó todavía en
>   `z-Entrega Final > Primera Competencia`.
>
> ## 10-oct, `z-Entrega Final > Primera Competencia`: las reglas de entrega, en limpio
> Denicolay [200311, 200312, 200319, 200334]: cierre 23:59:59 ART; cuenta el último submit; **el último submit es
> un solo archivo**; el link a GitHub va en ese tópico minutos antes o después, y debe permitir replicar
> exactamente ese archivo; notebook único → solo ese archivo; ensambles → subcarpetas + README; hiperparámetros
> heredados → subir la optimización que los generó. Bolaños [200869]: sin los CSV de la competencia en el repo;
> repo público (lo ven docentes y compañeros). Nuestro post: [200992].

### docs/backlog_ideas.md

> # Backlog de ideas para mejorar la predicción
>
> Cada ítem lleva fundamento, costo y estado. Las que se prueban pasan al diario con su medición; las que
> se descartan quedan acá con el motivo, para no repetirlas. Regla: un submit mide una hipótesis con
> fundamento; lo que no tiene fundamento no se manda.
>
> ## A. Las seis propuestas del 7-oct (de los repos de compañeros y la receta de la cátedra)
>
> | # | Idea | Fundamento | Estado |
> | --- | --- | --- | --- |
> | 1 | Lag 1 / delta 1 / lag 2 / delta 2 de **todas** las variables | Ramírez 86,7 → 98,6 público; Denicolay "superador" | **Hecho sobre valores crudos** (`c200`, `c201`): 100–104 público. **Pendiente la variante sobre montos rankeados por mes**, para que el lag no arrastre inflación (Abregu la usa) |
> | 2 | Hiperparámetros para 750 columnas: receta de Denicolay (`min_data_in_leaf` 0, `lr` 0,005, `ff` 0,5, `ff_bynode` 0,2, 83 hojas, 1.000 rondas) y después Optuna sobre `num_iterations`, `num_leaves`, `min_sum_hessian` | Ramírez +4,6 encima de los lags; Abregu +6,8 del semillerío con `ff` 0,40 | **Receta hecha** (`c201`). **Pendiente** Optuna (`c180` sobre el dataset nuevo, arreglando antes el bug del slice de folds) con early stopping por AUC en el fold C |
> | 3 | Re-barrer el corte para el modelo nuevo | un ranking mejor captura más profundo y corre el óptimo a la derecha | **Hecho**: meseta 13.500–14.500, pico 14.000 (5 semillas). Repetir con 20 archivos y con el ensamble |
> | 4 | ~~Stacking en vez de promedio~~ MEDIDO 8-oct (`c245`, promedio por rank de 5 variantes buenas): 104,00 vs 104,17; correlaciones 0,95–0,999, sin diversidad. Cerrado: meta-modelo chico sobre los scores de varios preprocesamientos (base, lags crudos, lags rankeados, deflactado) | experimento colaborativo 2025: stackear tres preprocesamientos +14,2 M, promediarlos 0; nosotros vimos base+FE con correlación 0,99 y promedio sin efecto | Pendiente. Entrenar el meta-modelo con los scores del fold B (202106) y aplicarlo a los de 202108 |
> | 5 | Reparaciones de datos: `ccajas_depositos + ccajas_otras` (reclasificación abr–jun); sacar `*_mconsumototal` (duplica `mconsumospesos`); NA en centinelas de `*_Fvencimiento` (< −1.000.000); NA en `mfinanciacion_limite` > 10× `mlimitecompra`; `ccajas_depositos` NA en 202105 | Ramírez D01, Denicolay (`En Limpio` 1.1) | Solo `ccajas_depositos` NA hecho. El resto pendiente, barato, un dataset `c202` |
> | 6 | ~~202107 con corrección positive-unlabeled~~ MEDIDO 8-oct (`c240`): 103,21 a 14k, −1,0, neutro. Cerrado: BAJA+1 conocidos como positivos, y **sacar** los negativos que el base puntúa alto (los ~870 BAJA+2 escondidos) | `c168` perdió 33,7 M al etiquetarlos negativos; la ley de envejecimiento dice que un mes de distancia vale puntos de captura; Aramendía en Zulip: "los BAJA+1 de 202107 sí sirven" | Pendiente. Validación limpia: train [03,04] + [05 con BAJA+1 y negativos podados] → val 202106 BAJA+2 |
>
> ## B0. Desacoplar FE de hiperparámetros — HECHO 7-oct 23:18: lags +3,2, receta +3,8, aditivos
> `lags12 + params z701` y `base + receta Denicolay`, 5 semillas cada uno, corte 10.000 y 14.000, contra
> `c201` (100,25 / 104,16) y `c191` (93,24). Sin esto el +7 no está atribuido (mismo error que `c133_todo`).
>
> ## B. Ideas nuevas, por orden de expectativa × costo
>
> ### B1. Target — MEDIDO 8-oct: peso 0 → −5,3, 0,5 → −2,0, 1,0 → −1,4 a 14k. El 0,25 es el máximo. Cerrado
> `BAJA+2` solo (K1), `BAJA+1 ∪ BAJA+2` (K2) y `pesos` 0,25 (lo actual). Ramírez midió en público K1 91,8
> contra K2 86,7 **con el mismo modelo**, y nosotros adoptamos `pesos` con evidencia que solo valía a
> 11.000. Con el modelo nuevo nunca se midió. Costo: dos entrenamientos de 5 semillas (~1 h), dos submits.
>
> ### B2. Meses de entrenamiento con lags — MEDIDO 8-oct: sin marzo −3,2 a 14k. Refutado
> Con lags, marzo tiene **todas** las columnas de historia nulas y abril no tiene lag 2: el patrón de
> nulos vuelve a codificar el mes (ya se midió que explicaba ~6 de 47 M en el FE viejo). "Sacar marzo"
> perdió para el base por la ley de distancia, pero el trade-off cambia cuando marzo aporta 1/4 de las
> filas y 0 de la historia. Costo: un entrenamiento de 5 semillas, un submit.
>
> ### B3. Ensamble heterogéneo — MEDIDO 8-oct 16:11: −2,2 contra el ensamble de la receta (104,17). Refutado tal como se hizo (sus miembros salieron de una búsqueda que sobreajustó)
> Denicolay pide "10+ modelos con hiperparámetros distintos" promediados. El semillerío de 20 iguales
> cancela ruido de orden; modelos distintos (otro `num_leaves`, otro `ff`, otro dataset) cancelan sesgos.
> Salida natural del Optuna de A2: promediar los rangos del top-5 de trials. Abregu: 40 semillas no
> mejoran sobre 20, o sea el ruido de semilla ya está agotado.
>
> ### B4. Estimar la prevalencia de agosto con un modelo calibrado — MEDIDO 9-oct: sum(p) = 957, K* = 8.626; contradice la curva pública (14k > 13k > 10k), que mide agosto directo. Descartado como instrumento de K
> El corte depende de cuántos BAJA+2 hay en agosto (870–1.139 en los meses vistos) y lo venimos
> infiriendo del barrido público. Un modelo con target `BAJA+2` puro y `objective binary` da
> probabilidades; la suma de `p` sobre 202108 estima los positivos de agosto. Validar: la misma suma
> sobre 202106 (fold B) contra los 1.098 reales. Si calibra razonablemente, es un segundo instrumento
> para el corte, independiente del público. Costo: casi cero con un modelo K1 de B1.
>
> ### B5. Features de transición y de recencia — MEDIDO 8-oct 16:12 (`c231`): 102,58 a 14k, −1,6, neutro. No se adopta (junto con las reparaciones A5)
> Indicadores "pasó a cero este mes" y "pasó a negativo" para las variables de monto, y "meses desde
> el último sueldo / desde la última transacción / desde que entró en rojo". Clara Rodríguez midió en
> Zulip transiciones a cero en `mcaja_ahorro` (32% → 41% en la cohorte BAJA+2) y `mpasivos_margen`.
> Son binarias, así que no sufren inflación ni drift de escala, y el árbol no las reconstruye bien desde
> lags continuos con `max_bin` 31. Costo: SQL en `fe_panel`, un dataset, un submit.
>
> ### B6. Lags sobre rangos por mes — MEDIDO 8-oct: −1,0 a 14k, neutro. No se adopta
> `percent_rank` dentro de `foto_mes` de los 73 montos **antes** de calcular lag y delta. Un delta de
> pesos entre junio (aguinaldo) y julio mide calendario, no conducta; un delta de percentil mide conducta.
> Abregu lo hace (`l1_rk0_`, `d1_rk0_`). Costo: `c202`, un entrenamiento, un submit.
>
> ### B7. Bloque de nulos simultáneos — NO EXISTE en nuestro parquet (8-oct): los nulos vienen en 4 bloques estructurales (99.644 / 47.186 / 579.470 / 127.760 filas); el flag quedó constante en 0 y es inerte
> 35.301 filas (3,5%) tienen todo el bloque de variables de negocio en nulo a la vez (Zulip, Alexander
> Arias). Para esas filas los lags y deltas salen nulos o espurios. Un flag `bloque_nulo` y su lag
> separan "el dato falta" de "el valor cambió". Costo: trivial; va junto con A5.
>
> ### B8. Regularizadores — MEDIDO 9-oct (c247/c248/c249, a 2.000 rondas): hessiano ×0,5 −3,3, ×2 −4,0, 127 hojas −1,4; 3.000 rondas (c246) −1,7. La receta + 2.000 rondas es óptimo local. Cerrado
> #### (texto original)
> `extra_trees=True`, `path_smooth`, `monotone_constraints` en las variables de dirección conocida
> (`ctrx_quarter` baja el riesgo, `mcuentas_saldo` baja el riesgo) y `max_bin_by_feature` más grueso en
> las columnas que `c128` marcó con AUC móvil. Fundamento: el modelo pierde ~50 M por drift entre meses
> (`diagnostico_fe`), y estos cuatro reducen la dependencia de umbrales finos aprendidos en un mes. Costo:
> entran como dimensiones del Optuna de A2, no hacen falta corridas aparte.
>
> ### B9. DART
> German Reintgen (Zulip) lo reportó como su mejor ganancia y menor sobreajuste, "lentísimo". Con 6
> minutos por modelo GBDT, DART de 1.000 rondas es de madrugada. Solo si sobra una noche de máquina.
>
> ### B10. Pseudo-etiquetado de 202107 y 202108 — DESCARTADO sin medir: A6 (la versión conservadora) dio neutro
> `J-Clase 06 > Entrenar en CUATRO meses`: entrenar en los meses con clase, pintar una clase artificial en
> los meses sin clase con un corte de probabilidad, reentrenar con todos. Más agresivo que A6 (A6 solo
> poda negativos dudosos; esto inventa positivos). Riesgo de circularidad; el propio profesor lo plantea
> como "bomba lógica" para probar. Costo: dos entrenamientos. Después de A6.
>
> ### B12. Proporciones de negocio — MEDIDO 9-oct (`c260`): 104,62, −0,9, neutro. Cerrado
> 11 cocientes pesos/pesos con lags: invariantes a la inflación, mal aproximados por un árbol de `max_bin` 31.
>
> ### B13. Sumas, conteos, rachas y crecimientos — MEDIDO 9-oct (`c261`): 103,27, −2,2. Pierde. Cerrado
> Totales Visa+Master / deuda / ingresos / inversiones; cuántos canales y productos activos; fotos seguidas en
> rojo, sin sueldo, sin consumo, sin operar; `x / lag1(x) − 1`. Las crudas se quedan (no son escalados).
>
> ### B14. Reducción de dimensionalidad por importancia — MEDIDO 9-oct: c262 (sin 52) −1,1, c263 (392 cols) −1,8 vs media de 20. Pierde en las dos intensidades. Cerrado
> 52 de 750 columnas no tienen un solo split en 20 modelos; 392 juntan el 99% de la ganancia. Con
> `ff` 0,5 × `bynode` 0,2, cada split muestrea ~75 columnas: sacar las muertas sube la probabilidad de que
> las vivas estén. Dos niveles: sin las 52 (conservador) y solo las 392 (agresivo).
>
> ### B15. feature_fraction 0,4 / 0,3 — MEDIDO 9-oct: 104,26 / 103,89, dentro de la banda. No mueve. Cerrado
> El único botón de la receta nunca barrido; Abregu +6,8 con 0,40. 2.000 rondas, 5 semillas.
>
> ### B16. Miembro de horizonte 1 — MEDIDO 9-oct (`c270`/`c271`): curva de peso pareada por semilla 0 → 105,51 · 0,15 → 105,70 · 0,3 → 105,75 · 0,5 → 105,67 · 0,7 → 103,65 · 1,0 → 99,92. Solo vale −5,6; mezclado es plano (+0,2, indistinguible de cero) hasta 0,5 y hunde desde 0,7. No aporta señal. Cerrado
> Target BAJA+1 solo, meses 03–07 (julio tiene BAJA+1 completo y sin BAJA+2 escondidos). Mezcla por rank con
> c241 semilla a semilla, 5 archivos contra 5 con la misma suerte de semillas (el diseño que deja ver ±0,5 en
> vez de ±1,5). Review `monday-45`. Lo que queda: BAJA+1 con el mes más fresco no ve nada que `pesos` 0,25 no vea.
>
> ### B17. Sacar las variables más importantes / correlacionadas — MEDIDO 10-oct: sin `ctrx_quarter` (`c290`) 102,71 (−2,8); sin las 10 familias top (`c291`) 87,21 (−18,3); sin una de cada par con |r| ≥ 0,95 (`c292`, 42 fuera) 104,12 (−1,4, dentro del ruido). Cerrado: ni sacar importantes ni sacar duplicadas gana
> Idea de la clase de ensambles (exp. 1): en el RF, sacar `ctrx_quarter` subía la ganancia. En LightGBM con
> muestreo de columnas no: la información no se recupera del todo por otras variables. Pregunta de Agustina.
>
> ### B11. Submit de 16.000 filas — la curva de 20 archivos ya cae desde 14.500 (103,37) y 15.000 (102,81): no hay nada que ganar; `enviar.py`/`c201_cortar` lo rechazan por rango
> El `help` del bot no menciona tope; los 8.000–15.000 son del mensaje del profesor. Si el bot acepta,
> un punto más de la curva (que ya baja en 15.000, así que la expectativa es confirmar el límite, no
> ganar). Hay que saltear `MAX_ENVIOS` y `MAX_FILAS` a propósito; lo corre la usuaria.
>
> ## C. Descartado con medición (no volver a probar sin un motivo nuevo)
> - 9-oct: comisiones deflactadas por tarifa (c251, −0,95), aguinaldo normalizado (c253, −1,0), vip + delinquency (c255, −1,0 más): neutras o peores, sd más baja. Corte con 20 archivos: 13k −0,55, 15k −1,0 contra 14k.
>
> - Sacar variables con drift para 202108 (préstamos incluidos): el profesor, `c133` en público, Abregu, Ramírez.
> - Deflactar por mediana mensual, `rank_cero_fijo`, FE histórico de 80 columnas sobre 21 variables.
> - Decaimiento por antigüedad, entrenar solo con el mes reciente, sacar marzo **para el base**.
> - Poda con canaritos en cinco niveles; también a una alumna de los jueves le bajó la ganancia.
> - Arreglar `Visa_delinquency` en 202105/202108: 0 efecto; sacar a los inyectados cuesta −8,7 M.
> - Sacar los relojes de calendario `*_fultimo_cierre`: separables pero inertes.
> - Demoter de horizonte 1 ingenuo, dos etapas, modelo por mes, `scale_pos_weight`: firma mayo/junio o nada.
> - Más rondas con árboles complejos (45 hojas, `min_data_in_leaf` 174): sobreajusta.
> - Lo que el profesor lista como inútil: PCA, imputar, outliers, AutoML, desbalanceo, features de clustering.
>
> ## D. Deuda técnica abierta (del code review del 7-oct noche, sesión competencia-1-05)
> - `reproducir.py` reproduce la entrega vieja (base 150 col, 10.000) y no fija `deterministic`/`force_col_wise`/
>   `num_threads` como `c201`. Se reescribe entero cuando se fije la entrega final.
> - `data/competencia_01_lags12.parquet` del 7-oct tiene los lags de `ccajas_depositos` sobre los ceros crudos de
>   202105 (una columna de 750). `c200` ya está corregido y se niega a pisar el archivo sin `--forzar`: el
>   desacople (B0) se corre sobre el archivo viejo para que el dataset sea idéntico al de `c201`; recién después
>   se regenera y se reentrena lo que quede vigente.

### docs/diario_competencia.md

> # Primera Competencia DMEyF 2026 — contexto del directorio
>
> Cierra el **domingo 11 de octubre 2026, 23:59:59 ART**. Vale el **ÚLTIMO** submit recibido antes de
> esa hora. Este archivo es el mapa de `monday/competencia/`; el del repo entero es `../CLAUDE.md`.
>
> ## Qué se predice
>
> **No** es "los clientes que se van en agosto". Es: de los **164.647 clientes de la foto 202108**,
> cuáles reciben **estímulo**. Paga `+1.072.500` si el estimulado resulta `BAJA+2` (está en 202108,
> está en 202109, **no** está en 202110) y cuesta `−27.500` si no. El CSV es una **lista de acciones**,
> no de predicciones; coinciden sólo porque el conjunto óptimo de acciones es el top-K por
> `P(BAJA+2)`.
>
> ## Las reglas del bot (Zulip topic 61, msgs 191490–191496)
>
> | | |
> | --- | --- |
> | Destino | DM a `@competencia-uno`, user_id **1692** |
> | Cuerpo | `submit    <NombreUnico>` — minúsculas, sin espacios, **distinto cada vez** |
> | Adjuntos | 1–20 `.csv`, nombres distintos |
> | Formato | **sin encabezado**, una columna de `numero_de_cliente`, **8.000–15.000** filas, enteros |
> | Cupo | **13 submits/día**, renueva **21:00 ART** |
> | Respuesta | `Public Gain mean` y `Public gain std dev` sobre los archivos, **sin escalar, en millones de ARS**, calculado sobre el **~25% público** |
> | Otros comandos | `list submits`, `help` (no consumen submit) |
>
> ## Dos trampas verificadas en los datos
>
> 1. **`numero_de_cliente` es `DOUBLE`** en `competencia_01.parquet`, y los dos ids que el instructor
>    marcó —`48000000` y `31100000`— **están los dos en 202108**. Sin castear a `int64` se escribe
>    `4.8e+07` y el submit falla. `escribir_envios()` castea, **relee el archivo** y falla si encuentra
>    `e+` o un punto.
> 2. **`Visa_Finiciomora` tiene ceros inyectados sólo en 202105 (3.222) y 202108 (3.249)**, cero en
>    todos los demás meses. Cae justo en el mes de la competencia. Las dos `F*iniciomora` están en
>    `ROTAS_EN_202108` y se sacan; la mora se lee de `Visa_delinquency` / `Master_delinquency`.
>
> ## El hallazgo que más condiciona todo: el corte lo manda el MES, no el modelo
>
> El **mismo modelo** (train 202103), scoreado en dos meses distintos:
>
> | validación | BAJA+2 | K* óptimo |
> | --- | ---: | ---: |
> | 202105 | 870 | **8.092** |
> | 202106 | 1.098 | **14.051** |
>
> Y con la validación fija en 202106, cambiar el modelo mueve K* apenas (13.055 → 14.788). O sea: **la
> prevalencia del mes domina**, y la de 202108 **no se conoce** (los meses etiquetados van de 870 a
> 1.139).
>
> Por eso el corte **no** se elige con el óptimo de un mes. Se elige por **minimax regret** sobre los
> dos folds (`competencia.regret` / `corte_minimax`):
>
> | K | regret 202105 | regret 202106 | peor caso |
> | ---: | ---: | ---: | ---: |
> | 8.000 | −0,7% | −14,4% | −14,4% |
> | **11.000** | −4,5% | −4,5% | **−4,5%** ← minimax |
> | 14.500 | −15,9% | −0,2% | −15,9% |
>
> Elegir 14.500 —el óptimo de 202106— es la misma trampa que perseguir el pico de **una** semilla, un
> nivel más arriba: se persigue el pico de **un mes**. El mínimo de regret esperado cae en 10.000 y el
> minimax en 11.000, los dos lejísimos de 14.500.
>
> ## Lo que contestó el bot, y qué mide su `std dev`
>
> Primer submit (`c100_esqueleto`, 3 semillas, 11.000 envíos), 2026-10-03:
>
> ```
> 📦 Submission received: 3 candidate models
> 📊 Public gain -> mean: 89.0175, std dev: 0.6496
> 🆔 Submission ID: 1572-1791073635598180
> 📅 Submissions today: 1/13
> ```
>
> > **El `std dev` del bot NO es el ruido de la partición.** Es el desvío entre los **archivos**
> > —o sea entre **semillas**— sobre una partición pública **fija**. Da 0,73% de la media. La
> > simulación local del sorteo 25/75 da 11,8%, pero esa partición **no se vuelve a sortear**: es la
> > misma para todos y para siempre. Entonces comparar dos submits está **pareado** sobre ella, y el
> > umbral útil para decidir **no es 11,4 M**. Hay que medir el ruido *pareado*, que es mucho menor.
>
> Otras lecturas de esa respuesta:
>
> - `89,0175 × 4 ≈ 356 M` extrapolado al mes entero, contra los **317 M** que predijeron los dos
>   folds. 202108 viene **mejor** que la validación — probablemente porque el modelo final entrena
>   con cuatro meses y los folds sólo con uno o dos.
> - El `help` confirma el formato: *"1 column with the IDs you predict as positive (no header)"*.
> - *"each submission spends 1, no matter how many files it has"*: **los archivos son gratis, lo que
>   se gasta son submits**. Conviene mandar siempre 20 semillas, no 3.
> - *"This is now your final submission — your LAST pre-deadline submit always is, with no separate
>   step needed"*: el bot lo hace solo, no hay que reenviar como pedía el mensaje del profesor.
>
> > **El deadline del bot está mal y NO hay que preocuparse.** El `help` dice
> > `Deadline: 2026-10-05T03:01:01`, que es exactamente el cierre viejo (`dom 04-oct 23:59:59 ART`,
> > en UTC) de **antes** del cambio de cronograma del 21-sep. El cierre real es **dom 11-oct 23:59**,
> > como dicen los mensajes del profesor. **Decisión tomada: no se gasta ni un submit en protegerse
> > de ese reloj.** No volver a levantar el tema.
>
> ## Estrategia de submits
>
> El cupo (117 submits hasta el cierre) **no es el recurso escaso**; la suerte en el privado sí.
> `z301` midió que **para un modelo fijo público y privado correlacionan −1**, y la simulación local
> del sorteo 25/75 sobre 202106 da **sd ≈ 11,4 M sobre una media de 96 M (11,8%)**. Diferencias
> menores que eso entre dos submits **son el sorteo, no el modelo**.
>
> 1. **El bot no es un conjunto de validación.** Se elige localmente: dos folds × semillas × Wilcoxon.
> 2. **~8 submits en total**, cada uno pre-registrado con su hipótesis y su delta.
> 3. **Un submit = una configuración × hasta 20 semillas**, para que media/sd aíslen la semilla.
> 4. **Reenvío final el viernes 10**, no la noche del 11.
>
> > **Regla: los submits se gastan en MEDIR, no en que la entrega vigente se vea bien.** Vale el
> > último submit antes del cierre, así que acomodarlo durante la semana **desperdicia cupo**. Cada
> > submit tiene que contestar algo que los datos locales no pueden: los folds validan **junio**, el
> > público mide **agosto**, y en este problema el mes manda. El submit final se arregla **cerca del
> > domingo**, de una.
>
> > **Regla dura: nunca se envía nada sin preguntar antes**, mostrando nombre, config, delta contra el
> > submit anterior, archivos con su cantidad de envíos y la ganancia esperada. La estructura lo
> > impone: un `submit` nace `estado='preparado'` con `enviado_en NULL`.
>
> ## Qué hay acá
>
> ```
> competencia.py      datos, ganancia, corte, regret, público/privado, escritura de envíos, caché
> registro.py         el ledger en Postgres (base `competencia`)
> c100_esqueleto.py   fase 0: params de z701, sin búsqueda, de punta a punta en ~70 s
> experimentos/<nombre>/
>     params.json  modelo_*.txt  scores_202108.parquet  regret.parquet  envios/*.csv
> ```
>
> El código de Zulip vive en el **otro repo**, `../../zulip/competencia.py`:
> `validar`, `comando`, `submit`, `escuchar`, `ultimas`.
>
> ## Después de un reboot
>
> Nada se pierde, pero **nada arranca solo**. En orden:
>
> ```sh
> open -a Docker                       # Docker Desktop no arranca solo en macOS
> docker start zulip-postgres          # el contenedor tiene RestartPolicy=no
> docker exec zulip-postgres pg_isready
> ```
>
> Los datos viven en el volumen `zulip`, que sobrevive reboots y recreaciones del contenedor: el
> *study* de Optuna, el ledger y el archivo de Zulip quedan intactos. Los modelos están en disco bajo
> `experimentos/`, así que **retomar no reentrena nada**.
>
> La búsqueda se retoma sola con el mismo comando: `load_if_exists=True` arranca donde quedó y el TPE
> lee los *trials* previos, así que **no pierde lo aprendido**. `--trials N` son N *trials* **más**.
>
> > Si se corta la búsqueda a mitad, el *trial* en vuelo queda `RUNNING` para siempre y Optuna lo
> > cuenta. Hay que marcarlo `FAIL` a mano:
> > ```python
> > from optuna.trial import TrialState
> > for t in s.trials:
> >     if t.state == TrialState.RUNNING:
> >         s._storage.set_trial_state_values(t._trial_id, TrialState.FAIL)
> > ```
>
> ## Persistencia y caché
>
> | Qué | Dónde |
> | --- | --- |
> | Study de Optuna | **Postgres** (`registro.dsn_url()`) — resumible y permite varios procesos a la vez |
> | Boosters | `experimentos/<exp>/modelo_<etiqueta>.txt`, patrón `entrenar_o_cargar` de `z701` |
> | **Scores** | `experimentos/<exp>/scores_<mes>.parquet` — **el caché que más rinde**: permite re-cortar en otro K, re-ensamblar y re-simular público/privado **sin reentrenar** |
> | Ledger y resultados | **Postgres** |
>
> La llave de caché hashea `params + meses + target + peso + dataset + semilla`: volver a correr con
> los mismos parámetros **carga**, no reentrena. `registro.purgar()` borra los bytes de los submits
> descartados y **conserva la fila**, para no repetir un experimento ya hecho.
>
> ## La identidad con la que se envía — se descubrió a los golpes
>
> > **El submit tiene que salir de la cuenta personal de la alumna, no del bot que archiva.**
>
> `~/zuliprc` autentica como **`Claude` (user_id 1687, `is_bot=true`)**, que es la cuenta con la que
> corre el ingestor. Mandarle `help` a `@competencia-uno` desde ahí devuelve:
>
> > :prohibited: You are not authorized to use this bot. If you think you should be, please tell a teacher.
>
> Las tres cuentas en juego:
>
> | id | nombre | bot | |
> | ---: | --- | :-: | --- |
> | **1572** | Agustina Razanov | no | la cuenta de alumna, **la que tiene que enviar** |
> | 1687 | Claude | sí | la del `~/zuliprc`, sólo para archivar |
> | 1692 | competencia-uno | sí | el bot de la competencia |
>
> La solución es un zuliprc aparte apuntado por **`COMPETENCIA_ZULIPRC`** (por defecto
> `~/zuliprc-competencia`): el ingestor sigue usando el bot y sólo los submits usan la identidad
> personal. La API key se saca en Zulip: rueda dentada → *Personal settings* → *Account & privacy* →
> *API key*.
>
> `exigir_cuenta_de_alumna()` **rechaza el submit** si la cuenta configurada es un bot, antes de subir
> un solo archivo. `competencia.py quien` dice con qué identidad se está hablando.
>
> ## Cómo recibimos la respuesta del bot
>
> Zulip tiene **API de eventos en tiempo real** (`register` + `get_events`, long-polling): el servidor
> mantiene la conexión abierta hasta que llega el evento. No hace falta *polling* tonto ni un webhook
> —los *outgoing webhooks* son para bots que **reciben** mensajes, y acá somos el usuario que recibe un
> DM—. `escuchar()` registra una cola con `narrow=[["is","dm"]]` y filtra por `sender_id == 1692` en el
> callback, porque el narrow no filtra por remitente.
>
> ## Lo que NO hay que heredar de los notebooks de clase
>
> 1. **`numero_de_cliente` y `foto_mes` fuera de `X`.** `z601` deja las dos adentro. El id memoriza; y
>    **202108 es un `foto_mes` que el modelo nunca vio**, así que LightGBM lo manda a un lado
>    arbitrario.
> 2. **`bagging_fraction` sin `bagging_freq` no hace nada** (`z601` lo olvida, `z701` lo arregla).
> 3. **`best_iter` se calcula y no se usa**: `z601` entrena con `num_boost_round=250` hardcodeado.
> 4. **Una sola convención de ganancia**: `+1.072.500` / `−27.500`, la consistente con el umbral.
> 5. **`ntile()` sobre columnas con muchos ceros no es determinístico**: desempatar con el id.
> 6. `fe_panel.COLUMNAS_DE_BAJA` fuera de `X` siempre: **`es_baja` *es* la respuesta**.
>
> ## Fase 1: qué dijeron los folds
>
> Los cuatro esquemas de target × dos datasets, cada uno **en su propio corte**, pareado por
> (fold, semilla) contra `base_baja2`, cerrado con Wilcoxon:
>
> | config | corte | 202105 | 202106 | Δ vs base | gana en | p |
> | --- | ---: | ---: | ---: | ---: | :-: | ---: |
> | **`base_pesos25`** | 11.000 | 250,8 | **399,7** | **+8,6 M** | **8/10** | **0,0078** |
> | `base_pesos5` | 10.500 | 253,8 | 386,6 | +3,5 M | 5/10 | 0,37 |
> | `base_baja2` | 11.000 | 236,9 | 396,4 | — | — | — |
> | `base_baja12` | 11.000 | 251,0 | 379,3 | −1,5 M | 5/10 | 0,75 |
> | `fe_baja2` | 11.500 | 237,0 | 349,5 | **−23,4 M** | 2/10 | 0,037 |
>
> **Pesar `BAJA+1` en 0,25 gana**, y es lo único significativo de la grilla. Es la respuesta a la
> pregunta de Zulip (*¿qué métrica optimiza con las dos bajas juntas?*): **ninguno de los dos
> esquemas puros; la interpolación**.
>
> ### El FE pierde, y no por lo que yo creía
>
> Primera hipótesis, **equivocada**: en 202103 las 102 columnas de historia son **100% nulas** (no
> hay mes anterior) contra ~1,4% en el resto, así que el patrón de nulos identifica a marzo y vuelve
> a meter el `foto_mes` que sacamos a propósito. Es un defecto real —y **introducido por nosotros**,
> `z402` nunca lo vio porque entrenaba un mes solo— pero entrenando **sólo en 202104** el FE sigue
> perdiendo **40,9 M** (antes 46,9 M). Explica ~6 de 47 M.
>
> | train [202104] → 202106 | @11.000 | Δ vs base | gana en |
> | --- | ---: | ---: | :-: |
> | `base_p25` | 409,0 M | +6,4 M | 4/5 |
> | `base` | 402,6 M | — | — |
> | `ferank_p25` (sin lag/delta/slope) | 374,2 M | −28,4 M | 0/5 |
> | `fe` | 361,7 M | −40,9 M | 0/5 |
>
> Explicación que queda en pie: los hiperparámetros son los que `z701` afinó para **150** columnas y
> se están aplicando a **297**. `feature_fraction`, `num_leaves` y `min_data_in_leaf` dependen de la
> dimensionalidad, así que **esto nunca fue una prueba justa del FE**. Lo decide Optuna, por dataset.
>
> > Con 5 semillas el p de Wilcoxon más chico posible es 0,0625: un `0/5` es la evidencia más fuerte
> > que ese tamaño de muestra puede dar.
>
> ## El umbral REAL para leer el leaderboard
>
> Simulando 2.000 particiones del 25% sobre 202106, el sd **de la diferencia** entre dos submits:
>
> | comparando | sd de la diferencia pública |
> | --- | ---: |
> | variantes del mismo pipeline | **3,15 M** |
> | datasets distintos | 16,3 M |
>
> **Para declarar ganador con ~95% hace falta una brecha pública ≥ 6,3 M**, que son ~25 M de
> diferencia real en el mes entero. Verificación: `base_pesos25` le gana a `base_baja2` por 14,3 M
> reales → se ve como 3,59 ± 2,81 M en público → el público acierta el orden **90%** de las veces.
>
> > **No usar el `std dev` del bot como umbral.** Dio 0,6496, que es la **semilla**; el ruido de una
> > comparación es **5× más grande**. Y mi estimación previa de ±11,4 M era igual de inútil pero al
> > revés: sobreestima, porque la partición no se vuelve a sortear.
>
> ## Fase 2: la búsqueda no le ganó al baseline
>
> 31 *trials* de Optuna sobre `base`, con `esquema` y `peso_baja1` **dentro** del espacio, más
> `lambda_l1/l2`, `min_gain_to_split` y `max_bin`. Revalidando el top 5 *out of time*:
>
> | | corte | 202105 | 202106 | media |
> | --- | ---: | ---: | ---: | ---: |
> | **`base_pesos25`** (params de `z701`, w=0,25) | 11.000 | 250,8 | **399,7** | **325,3** |
> | optuna t15 (w=0,91) | 10.000 | 262,5 | 373,3 | 317,9 |
> | optuna t17 (w=0,99) | 10.000 | 262,7 | 372,0 | 317,4 |
> | `base_baja2` (w=0) | 11.000 | 236,9 | 396,4 | 316,7 |
>
> Los candidatos de Optuna quedan **~7,5 M abajo** del baseline (5/10, o sea empate). **La búsqueda no
> aportó nada.** Spearman entre el ranking CV y el *out of time*: **+0,10**.
>
> **Por qué falló**: el objetivo era ganancia en CV **dentro** de 202103-202104, y encima con el corte
> elegido *post-hoc* sobre el mismo mes. Las dos cosas favorecen fusionar las clases —más positivos, y
> la fusión no paga el cambio de escala—, así que TPE se fue a `peso ≈ 0,9`, que es justo lo que los
> folds rechazan. **Optimizó bien hacia el blanco equivocado.** Además descubrió "bajar el *learning
> rate* y entrenar más rondas", que sube el CV del mes y tocó el techo de 1.500 rondas.
>
> Y hay algo estructural: subir el peso no mejora el modelo, **cambia en qué mes anda bien**
> (202105 mejor, 202106 peor). El peso, como el corte, es **una apuesta sobre la prevalencia del mes**.
>
> > Para el video de Michelina esto es material directo de *"qué no funcionó"*: una búsqueda
> > bayesiana de 31 *trials* perdiendo contra unos hiperparámetros heredados, por tener mal el
> > objetivo y no el algoritmo.
>
> ## Fase 3: la entrega vigente
>
> `c107_pesos25`: params de `z701` + target fusionado con `BAJA+1` pesando **0,25**, entrenado en los
> cuatro meses etiquetados, **corte 11.000** (minimax con 20 semillas, peor caso −3,47%).
>
> **El ensamble por rank se midió, no se supuso**: 254,1 M vs 249,4 M de la semilla media en 202105 y
> 405,9 M vs 398,9 M en 202106 — **le gana al 80-85% de las semillas sueltas**, aunque no a la mejor
> (que no se puede saber de antemano). Por eso es el candidato de un solo archivo.
>
> | submit | archivos | public mean | std |
> | --- | ---: | ---: | ---: |
> | `c100_esqueleto` (w=0) | 3 | 89,0175 | 0,6496 |
> | `c107_pesos25` (w=0,25) | 20 | 91,3550 | 1,4873 |
> | **`c107_pesos25_ens`** (ensamble) | 1 | **92,6750** | **0,0000** |
>
> Dos cosas que salieron como estaban previstas:
>
> - **El cambio de target cayó donde decían los folds.** Local: +8,6 M al mes → ~+2,15 M en el 25%
>   público. Observado: **+2,34 M**. Un *check* lindo de toda la maquinaria de validación.
> - **El `std` de un solo archivo es 0,0000.** No es precisión, es ausencia de medición.
>
> > Pero **+3,66 M en total sigue por debajo del umbral de 6,3 M**: el leaderboard **no confirmó**
> > nada. Se movió en la dirección que predijeron los folds, que es alentador, no evidencia
> > independiente. La razón para creerle a `pesos25` sigue siendo el pareado (8/10, p=0,0078).
>
> ## El drift: no es «marzo es malo», es DISTANCIA
>
> > [!warning] Esto corrige una interpretación que estuvo vigente casi todo el trabajo
>
> **Lo que se midió primero.** Entrenar con un mes solo (202104) le gana a entrenar con dos
> (202103+202104): **+10,6 M, 18/20, p=0,0002**. Se duplicaron los positivos y el modelo empeoró.
> Y no es la prevalencia: recortando 202104 a los mismos **960** positivos que 202103, igual le saca
> **+34,2 M (10/10, p=0,002)**.
>
> **La interpretación equivocada** fue *«marzo es un mes de entrenamiento malo»*. De ahí salieron
> tres remedios y **los tres fallaron**: decaimiento exponencial por antigüedad, sacar marzo, y
> entrenar sólo con el mes más reciente.
>
> ### El test que lo resuelve
>
> Marzo siempre estuvo a 3 meses de la validación y abril a 2: mes y distancia venían confundidos.
> Separándolos con la **captura** (qué fracción de los que se van cae en el top K — no depende de la
> prevalencia del mes):
>
> | caso | 5k | 9k | 11k | 15k |
> | --- | ---: | ---: | ---: | ---: |
> | marzo → mayo (**distancia 2**) | 39,1% | 52,6% | 57,8% | 64,7% |
> | marzo → junio (**distancia 3**) | 35,6% | 49,6% | 55,8% | 67,0% |
> | abril → junio (**distancia 2**) | 35,0% | 51,9% | 58,9% | 68,3% |
>
> - efecto de la **distancia** (mismo marzo, a 2 vs a 3): **+1,6%**
> - efecto del **mes** (misma distancia, abril vs marzo): **−0,0%**
>
> **Marzo y abril son igual de buenos. Lo que pesa es cuán lejos está el dato del mes a predecir.**
>
> ### Y la aritmética cierra
>
> A K=11.000 sobre 202106 (1.098 bajas): marzo captura 55,8% → 613 aciertos → 371,5 M; abril captura
> 58,9% → 647 → 408,9 M. Diferencia **+37,4 M** contra los **+34,2 M** medidos. **La brecha entera son
> 3,1 puntos de captura: 34 fugados más, ni uno menos.**
>
> > [!note] El modelo envejece ~3 puntos de captura por mes de distancia
> > Y eso explica de una vez las tres cosas que tratábamos por separado:
> > - **Sacar marzo no sirvió** (−4,07 M en agosto): no sacábamos un mes malo, sacábamos un cuarto
> >   de los datos. El perjuicio ya estaba diluido.
> > - **El decaimiento y «sólo el mes reciente» fallaron**: atacaban «los meses viejos son malos»,
> >   que no es el problema. El mes más nuevo que tenemos —202106— **ya está a 2 meses de agosto**,
> >   y no hay forma de acercarlo.
> > - **Los ~50 M de brecha in-month vs out-of-time no son un defecto nuestro**: son el costo
> >   estructural de predecir con dos meses de atraso, que es lo que el enunciado exige.
>
> ### Lo que NO explica a marzo (descartado midiendo)
>
> Nulos (6,88% contra 6,6–6,9% de los demás), composición de clientes, antigüedad, actividad,
> productos: **marzo es idéntico a los otros meses**. Y la relación variable→fuga también: el lift
> del decil 1 de `ctrx_quarter` contra la tasa base de cada mes da 5,97 / 6,09 / 5,30 / 5,87 — los
> cuatro separan igual.
>
> > [!warning] Un cociente con denominador chico me engañó cuatro veces hoy
> > Llegué a «medir» que `ctrx_quarter` separaba 33,7× en marzo contra ~50× en los otros meses. Era
> > un artefacto: el denominador es el decil 10, que tiene **9 a 17 bajas en total**. Normalizando
> > contra la tasa base de cada mes, los cuatro meses separan igual. Es el mismo error que el pico
> > de la curva de corte (4 clientes), el bloque 9k→15k, y el `K*` de junio.
>
> ## Las features de v101, y el límite de los folds
>
> 14 columnas sacadas del EDA de Miranda, con hipótesis de negocio cada una. Los *lifts* crudos contra
> la tasa base son altísimos: `v_meses_sin_trx ≥ 2` **11,6×**, `v_rojo_sin_acuerdo` **10,5×**,
> `v_tc_cerrando` **9,4×**.
>
> | | Δ vs base | gana en | p |
> | --- | ---: | :-: | ---: |
> | las 14 | +4,0 M | 13/20 | 0,057 |
> | sólo las de la misma fila | +3,6 M | 13/20 | 0,076 |
> | sólo las acumuladas | +0,4 M | 11/20 | 0,67 |
>
> > **Predicción mía, equivocada.** Dije que las acumuladas serían las valiosas —el árbol no puede
> > inventarlas— y aportaron nada. Pero el motivo es un **defecto del test, no de las features**: en el
> > fold A se entrena en 202103, que tiene **cero** historia, y en el fold B con un mes a lo sumo.
> > `meses_en_rojo` casi no varía ahí; en 202108 tendría seis meses de recorrido.
> >
> > **Los folds no pueden medir features históricas.** Es el mismo defecto que hundió al FE de `z402`.
> > Que den +0,4 M no significa que no sirvan: significa que **no las medimos**.

(sigue en https://emavaldez.github.io/postmortem/fuentes/agustinarazanov/docs/diario_competencia.md.txt)

### docs/diagnostico_fe.md

> # Diagnóstico: por qué tres rondas de FE no movieron la ganancia
>
> Fecha: 2026-10-04. Sin features nuevas: sólo se midieron los modelos ya cacheados de `c116_v2`
> (base / v101_viejo / v2_corregido × 10 semillas × 2 folds) y unos pocos modelos chicos de sonda.
> Scripts en el scratchpad de la sesión (`d1`…`d6`), no en el repo.
>
> ## La conclusión en una línea
>
> **El FE no puede mover la aguja porque en este espacio de features no queda nada que agregar.** El
> techo medido sin *drift* (CV dentro de 202106) da **452 M con las 150 crudas y 456 M con v2: +3,8
> M**. Mientras tanto, el *drift* entre meses cuesta **~50 M** (452 → 403). Además el instrumento no
> resuelve efectos por debajo de ~8–10 M. Quedan en pie **H1 + H2 + H3**, y la palanca es **H4: el
> mes**.
>
> ---
>
> ## 1. La escala real del efecto: ±5 clientes
>
> Cada positivo que entra o sale del top-11.000 vale **1,1 M** (+1.072.500 que se gana o se pierde,
> más los 27.500 del negativo que ocupa su lugar). Entre `base` y `v2`, en el ensamble por rank:
>
> | fold | clientes que cambian de lado | positivos que salen | positivos que entran | neto |
> | --- | ---: | ---: | ---: | ---: |
> | 202105 | 535 | 13 | 6 | **−7** |
> | 202106 | 537 | 11 | 14 | **+3** |
>
> **Tres rondas de FE movieron entre 3 y 7 clientes en meses de 870–1.098 positivos.** Los "−1,5
> a −5,6 M" son eso.
>
> ## 2. H3: el instrumento no tiene resolución para lo que se busca medir — **EN PIE**
>
> ### 2a. El Spearman de 0,99 no es una pista: es el piso del ruido
>
> | comparación (202106) | Spearman | comparten del top-11k |
> | --- | ---: | ---: |
> | base vs v2 | 0,989 | 95,1% |
> | base vs v101 | 0,991 | 94,8% |
> | **base semilla 1 vs base semilla 2** | **0,994** | **94,2%** |
>
> Una configuración con 17 columnas nuevas se aleja del base **lo mismo** que el base se aleja de sí
> mismo con otra semilla. El 0,988–0,995 dice que **el cambio de features es del tamaño del ruido
> de semilla**, no que todos los modelos "vean lo mismo".
>
> ### 2b. Bootstrap de clientes: el intervalo es más ancho que cualquier efecto medido
>
> Remuestreando clientes del mes de validación (1.000 réplicas, ensamble por rank):
>
> | fold | Δ v101 − base | IC 95% | Δ v2 − base | IC 95% |
> | --- | ---: | --- | ---: | --- |
> | 202105 | −4,8 M | [−16,5, +5,5] | −8,0 M | [−18,7, +1,1] |
> | 202106 | +4,4 M | [−6,6, +16,5] | +2,9 M | [−8,8, +14,3] |
>
> **sd del delta ≈ 5–6 M por fold.** Con dos folds, el efecto mínimo detectable al 95% es de
> **~8–10 M al mes ≈ 8–9 clientes**. Ninguna de las tres rondas llegó a ese tamaño, ni a favor ni en
> contra. El "−1,5 a −5,6 M" **no es una pérdida medida, es un cero con ruido**. (El pareado por
> semilla de `c112`/`c116` sólo controla la semilla, no qué clientes se fueron ese mes, y por eso da
> p chicos que no se sostienen.)
>
> ### 2c. El AUC sí ve la mejora; la ganancia @K no
>
> | | ΔAUC pareado por semilla | gana en | p |
> | --- | ---: | :-: | ---: |
> | v101, 202105 | +0,0008 | 9/10 | 0,014 |
> | v101, 202106 | +0,0009 | 9/10 | 0,004 |
> | v2, 202105 | +0,0004 | 8/10 | 0,084 |
> | v2, 202106 | +0,0011 | 9/10 | 0,020 |
>
> La ganancia @K es una métrica **de pertenencia al conjunto**: reordenar dentro del top-11k vale
> cero, y reordenar dentro de la cola también. Sólo cuenta cruzar el corte. Las features mejoran el
> orden **lejos del corte**, entre los que ya se mandaban y entre los que no se iban a mandar nunca.
>
> ### 2d. Las features de ventana significan otra cosa en los meses de train
>
> Las columnas de los meses de **entrenamiento** de los dos folds tienen la ventana truncada:
>
> | feature (media) | 202103 | 202104 | 202105 | 202106 |
> | --- | ---: | ---: | ---: | ---: |
> | `w_rojo_3m` | 0,204 | 0,404 | 0,600 | 0,567 |
> | `w_canales_cero_3m` | 0,037 | 0,073 | 0,107 | 0,106 |
> | `v_meses_en_rojo` | 0,204 | 0,404 | 0,600 | 0,759 |
> | `w_ctrx_min_3m` | 118,2 (= `ctrx_quarter`) | 114,0 | 110,3 | 110,9 |
>
> La corrección de `c115` a "ventanas fijas" estabiliza 202105 → 202108, pero **no** los meses de
> train. En 202103 la ventana tiene **una** fila: `w_rojo_3m ≡ w_rojo` y `w_ctrx_min_3m ≡
> ctrx_quarter`. El fold A entrena sólo en 202103, así que **aprende cortes sobre {0,1} y valida sobre
> {0,1,2,3}**. Y `w_ctrx_min_3m` es la **segunda feature en importancia** del modelo v2 (10% del
> gain). **Ninguna feature histórica fue medida en condiciones comparables a 202108.**
>
> ### 2e. Contaminación del fold A
>
> En 202105, 225 de las 3.222 filas con `Visa_Finiciomora = 0` inyectado entran en el top-11k del
> base, con tasa de BAJA+2 de 0,81% (~−6 M de peso muerto). Afecta a todas las configuraciones por
> igual, así que no sesga el Δ. Pero sí ensucia el nivel del fold que menos se parece a 202108.
>
> ## 3. H4: el margen cambia de mes a mes — **EN PIE: es donde está la plata**
>
> **Prueba directa.** Se tomaron los clientes con la *flag* que el base dejaba en los puestos
> 11k–30k y se los pasó al frente, sin reentrenar nada. Es lo máximo que esa *flag* podía aportar:
>
> | flag | 202105 | 202106 |
> | --- | ---: | ---: |
> | `v_rojo_sin_acuerdo` | −4,4 M | +16,5 M |
> | `v_meses_sin_trx >= 2` | −3,3 M | +15,4 M |
> | `w_aq1_ctrx0` | −6,6 M | +14,3 M |
> | `w_ctrx_cae_fuerte` | −7,7 M | +13,2 M |
> | `w_canales_cero_3m >= 3` | −11,0 M | +6,6 M |
> | **todas juntas** | **−24,2 M** | **+38,5 M** |
>
> **Las mismas *flags*, con signo opuesto según el mes.** La tasa de BAJA+2 entre los que tienen la
> *flag* **dentro de la franja del margen** (rank 6k–20k) lo explica:
>
> | flag | 202105 con / sin flag | 202106 con / sin flag |
> | --- | --- | --- |
> | `v_rojo_sin_acuerdo` | 2,9% / 1,7% | **11,3% / 2,6%** |
> | `v_meses_sin_trx >= 2` | 1,6% / 1,7% | **11,3% / 2,6%** |
> | `w_aq1_ctrx0` | 0,3% / 1,7% | **15,9% / 2,7%** |
>
> En 202106 las *flags* son oro en el margen (×4–6). En 202105 no valen nada, y algunas son
> negativas. Los lifts univariados de 9–11× son reales, pero pertenecen **a la población**. En el
> margen, que es donde se gana la plata, el lift depende del mes. Es el mismo fenómeno que `z701`
> encontró con `mprestamos_personales` y que `c108`/`c110` midieron como «manda la recencia»: la
> relación X→y en el margen deriva mes a mes. Promediada sobre los dos folds, da ≈ 0.
>
> ## 4. H1: LightGBM ya lo tenía — **EN PIE**
>
> Los positivos de cada *flag* que el base **ya mandaba** sin ella:
>
> | flag | % de sus positivos ya en el top-11k (202105 / 202106) | positivos con flag que quedaban afuera |
> | --- | --- | ---: |
> | `v_tc_cerrando` / `w_tc_cierre_nuevo` | 97% / 83–84% | 1 / 5 |
> | `v_meses_sin_trx >= 2` | 94% / 85% | 4 / 20 |
> | `v_rojo_sin_acuerdo` | 88% / 80% | 7 / 25 |
> | `w_ctrx_cae_a_cero` | 94% / 93% | 1 / 2 |
>
> Importancia (gain, promedio de 10 semillas, fold 202106): las *flags* de lift alto caen en
> `w_rojo_sin_acuerdo` **#65**, `w_tc_cerrando` #63, `w_ctrx_cae_a_cero` #108 y `w_aq1_ctrx0` #123
> de 167. El árbol llega solo con dos cortes. Las que el modelo **sí** usa son las continuas e
> históricas: `w_ctrx_min_3m` #2 (10%), `w_fee_por_trx_rk` #3 (6,9%) y `w_anclas` #7. Entre todas
> las nuevas suman 25–30% del gain. **El modelo las usa, y mucho**: no es que las ignore. Les saca
> importancia a las crudas que ya cubrían lo mismo (`ctrx_quarter` baja de primera holgada a 11%).
>
> ### Redundancia: ¿se puede reconstruir la feature desde las 150 crudas de la misma fila?
>
> LightGBM de 300 árboles, entrenado en 202104 y evaluado en 202106:
>
> | feature | derivable | |
> | --- | --- | --- |
> | `w_rojo`, `w_rojo_sin_acuerdo`, `w_aq1_ctrx0`, `w_tc_cerrando` | AUC **1,000** | idénticas a dos cortes del árbol |
> | `w_mora_vieja` | R² 0,9995 | |
> | `w_cobra_sueldo`, `w_usa_cajero` / `w_anclas`, `w_fee_por_trx_rk` | AUC 1,000 / R² 1,000, 0,998 | las que más importancia toman: **son crudas re-expresadas** |
> | `w_ctrx_cae_a_cero` | AUC 0,976 | |
> | `w_ctrx_min_3m` | R² 0,966 | la segunda en importancia, y casi `ctrx_quarter` |
> | `w_ctrx_cae_fuerte` | AUC 0,918 | |
> | `w_canales_mes` / `w_tc_saldo` | R² 0,91 / 0,89 | |
> | `w_canales_cero_3m` / `w_rojo_3m` | R² 0,76 / 0,69 | lo único con historia genuina… |
> | `v_meses_sin_trx` / `v_meses_en_rojo` | R² 0,70 / 0,53 | historia genuina (y truncada en train, §2d) |
> | `w_tc_cierre_nuevo` | AUC **0,58** | …y esta: la única de verdad nueva, con 0,4% de cobertura |
>
> ### Canaritos (30 columnas de ruido, fold B, v2, 3 semillas)
>
> El mejor canarito queda en el puesto **#57** de 197. **111 de las 167 columnas quedan por debajo**
> —reproduce el 120/154 de `z401`—, y entre ellas **siete de las 17 nuevas**: `w_rojo_sin_acuerdo`,
> `w_aq1_ctrx0`, `w_ctrx_cae_a_cero`, `w_ctrx_cae_fuerte`, `w_canales_cero_3m`, `w_mora_vieja` y
> `w_usa_cajero`. **Las de lift 10–14× puntúan como ruido**: son redundantes, no inútiles. Las que
> superan al canarito son las continuas que reemplazan a una cruda (`w_ctrx_min_3m` #2, `w_anclas`
> #4, `w_fee_por_trx_rk` #6).
>
>
> ## 5. H2: saturación del espacio de features — **EN PIE** (corrige mi lectura inicial)
>
> | escenario, validando en 202106 | ganancia @11k |
> | --- | ---: |
> | oráculo (mandar exactamente a los 1.098 BAJA+2) | 1.178 M |
> | **sin *drift*: CV 5-fold dentro de 202106, v2** | **455,9 ± 1,6 M** (AUC 0,9065) |
> | **sin *drift*: CV 5-fold dentro de 202106, base** | **452,1 ± 2,2 M** (AUC 0,9053) |
> | *out of time*, ensamble base (train 202103+04) | 405,9 M |
> | *out of time*, base, train 202104 completo | 402,6 ± 3,6 M |
> | ídem con 50% / 25% / 12,5% de las filas | 395,3 / 363,0 / 389,8 M |
>
> Tres lecturas:
>
> - **Ni en el mejor caso el FE vale más de ~4 M.** Con el modelo entrenando sobre el mismo mes que
>   se evalúa, sin *drift* y sin truncamiento, v2 le gana al base por **+3,8 M**: unos 3,5 clientes.
>   Eso es el techo de lo que estas features pueden aportar, y está por debajo del umbral de
>   detección.
> - **El oráculo está lejos (1.178 M), pero no es alcanzable con estas columnas.** El 34–36% de los
>   BAJA+2 **ningún** modelo de los 30 de cada fold lo manda nunca (316 / 371 clientes). Todos los
>   modelos fallan con los **mismos** clientes: es el núcleo «Te ghostea» de `v101`, sin rastro en
>   los datos de cuenta.
> - **Más filas tampoco.** Con 1/8 de 202104 el modelo ya está a ~13 M del mes completo (la curva es
>   ruidosa con 3 semillas, pero plana). Y `c108` ya mostró que sumar un mes viejo **resta**.
>
> La distancia que sí existe es **452 → 403 = ~50 M, y es *drift***: lo que el modelo pierde por
> entrenar en un mes y predecir en otro. Es 12× el techo del FE.
>
> ### Corrección a §3
>
> El empuje de +38 M en 202106 se eligió **mirando 202106** (los lifts del tamiz incluyen ese mes).
> El techo *in-month* de v2 dice que el modelo, viendo el mes, sólo saca +3,8 M de esas mismas
> columnas. O sea: **las crudas ya alcanzan para encontrar el margen de 202106 si se entrena en
> 202106**. Lo que cambia entre meses no es qué columnas hay sino **qué corte sobre ellas separa el
> margen**.
>
>
> ---
>
> ## Qué implica para el esfuerzo que queda
>
> 1. **Dejen de buscar features.** El número: **+3,8 M de techo** —v2 contra base, entrenando y
>    validando en el mismo mes, sin *drift*—, contra un efecto mínimo detectable de **~8–10 M** por
>    fold. Aunque una cuarta ronda fuera perfecta, no se podría ver. Las *flags* de lift 10× son
>    reconstruibles al 100% desde la fila (AUC 1,000) y puntúan por debajo de un canarito.
>
> 2. **El esfuerzo va al *drift* temporal: son ~50 M en juego**, la brecha entre 452 *in-month* y
>    403 *out of time*. Las palancas ya medidas que superan el umbral son todas temporales: `c108`
>    (train sólo con el mes más reciente, +10,6 M, 18/20) y `c110` (decaimiento λ = 0,15, +8,0 M,
>    10/10). Lo siguiente es **entrenar 202108 con 202106 dominante** (decaimiento), y el **corte**
>    para una prevalencia desconocida (`corte_minimax`).
>
> 3. **Cambiar el estadístico de comparación.** El Wilcoxon pareado por semilla sobre la ganancia
>    @11k no remuestrea clientes, así que da p chicos para efectos de ±5 clientes. Para decidir
>    entre configuraciones: **bootstrap de clientes** del mes de validación (sd ≈ 5–6 M por fold) y,
>    como desempate, AUC o ganancia integrada en 8k–15k.
>
> 4. **Las features de ventana nunca se midieron bien** (§2d): en 202103 `w_*_3m` tiene una fila. No
>    vale la pena arreglarlo **para medirlas**, porque el techo *in-month* ya acota su valor en
>    ~4 M. Pero si v2 entra en la entrega, el decaimiento temporal resuelve el truncamiento de
>    rebote, porque los meses truncados pesan poco.
>
> 5. **Usar v101/v2 en la entrega es neutro**: Δ indistinguible de 0, AUC +0,001 (9/10). No hay
>    motivo para sacarlas ni para pelear por ellas.
>
> ## Correlación de errores, para el video de Michelina
>
> Cada positivo de los meses de validación, contado sobre los 30 modelos de su fold (3
> configuraciones × 10 semillas):
>
> | | 202105 | 202106 |
> | --- | ---: | ---: |
> | lo mandan **todos** | 445 (51%) | 551 (50%) |
> | lo mandan algunos (disputados) | 109 (13%) | 176 (16%) |
> | **no lo manda ninguno** | **316 (36%)** | **371 (34%)** |
>
> **Un tercio de las bajas es invisible para cualquier modelo de esta familia**: es el «Te ghostea»
> de `v101`. Todo el FE pelea por la franja de disputados, que son 109–176 clientes. Y aun ahí el
> techo sin *drift* da ~4 M.

