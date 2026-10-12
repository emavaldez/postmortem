# farpp8 — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: farpp8
- Repositorio: https://github.com/farpp8/dmeyf2026-competencia01
- Link posteado: https://github.com/farpp8/dmeyf2026-competencia01
- Commit: fd33f7d696802912cc96d3ac86f1da52afa8e833
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/farpp8/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/farpp8.json

## Resumen

Repositorio en Python con un README, un resumen de decisiones (DECISIONES.md), nueve archivos .py en la raíz y cuatro en `origen/`. `reproducir.py` regenera desde el crudo de la cátedra el archivo `d10dn11000.csv` y compara su SHA-256 con el del archivo enviado. El camino: `01_preparar_datos.py` recalcula `clase_ternaria` con DuckDB, reemplaza dos conteos de cajas por su suma, quita seis columnas (entre ellas las dos de préstamos personales) y pasa a NA valores de cuatro variables de tarjeta; `02_variables.py` agrega lag 1, delta 1, lag 2 y delta 2 de todos los predictores; `06_receta_denicolay.py` entrena 20 LightGBM, uno por semilla, con 202103–202106, positivo = BAJA+1 o BAJA+2 e hiperparámetros fijos (83 hojas, 1.000 rondas, learning_rate 0,005), predice 202108 y promedia las probabilidades; `07_archivo_d10.py` escribe los 11.000 clientes de mayor promedio. En `origen/`, que `reproducir.py` no ejecuta, están la búsqueda con Optuna y la selección de donde, según el README, salen las 83 hojas y el hessiano mínimo, y la regla que da el corte de 11.000. El repositorio también reproduce dos envíos anteriores (`d06d` y `base`).

**Qué entrega.** Un CSV, `d10dn11000.csv`, con 11.000 `numero_de_cliente` de 202108 (uno por línea, sin encabezado, ASCII con saltos CRLF): los de mayor promedio de probabilidad de 20 LightGBM. El archivo no está en el repositorio; el README da su SHA-256 (8a03bf3d…70b5) y `reproducir.py` lo regenera y lo compara. Según el README, se envió al bot el 9-oct-2026.

**Cómo se ejecuta.** Según el README: Python 3.13 de 64 bits; bajar `competencia_01_crudo.csv` a `datos/` (o definir la variable de entorno `COMPETENCIA_01_CRUDO` con su ruta); crear un entorno virtual, `pip install -r requirements.txt` y `python reproducir.py`. Sin argumentos reproduce `d10dn11000.csv`; `python reproducir.py d06d` y `python reproducir.py base` reproducen los dos envíos anteriores. Para `origen/` (según origen/README.md): `pip install -r origen/requirements.txt`, `python 01_preparar_datos.py` y después `python origen/d04_busqueda.py`, `python origen/d04_seleccion.py` y `python origen/regla_n.py`.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: positivo = BAJA+1 o BAJA+2, negativo = CONTINUA (`POSITIVAS` en 06_receta_denicolay.py). `clase_ternaria` se recalcula desde el crudo en 01_preparar_datos.py: BAJA+1 si el cliente falta el mes siguiente, BAJA+2 si está el siguiente y falta el subsiguiente.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202105, 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código: se entrena con todas las filas de 202103–202106 y `bagging_fraction=1.0`.
- **Calidad de datos:** En 01_preparar_datos.py: `numero_de_cliente` se lee como texto y se convierte a BIGINT (el docstring indica seis filas con el identificador en notación científica); `ccajas_depositos` y `ccajas_otras` se reemplazan por su suma `ccajas_depositos_otras`; se quitan `Visa_mconsumototal`, `Master_mconsumototal`, `cprestamos_personales` y `mprestamos_personales`; pasan a NA `Visa/Master_mfinanciacion_limite` cuando el límite de compra es positivo y la financiación lo supera 10 veces, y `Visa/Master_Fvencimiento` menores que −1.000.000. Se guarda el valor original de cada celda modificada y se controla celda por celda que el resto sea idéntico al crudo.
- **Drifting:** En el camino de la entrega no hay transformaciones por mes. Se quitan `cprestamos_personales` y `mprestamos_personales`; el docstring de 01_preparar_datos.py indica que en junio cambia su relación con la baja. 02_variables.py tiene opciones que D no activa: ranking percentil dentro del mes (`rangos`, `hist_selectiva`) y días desde el último cierre de tarjeta menos la moda del mes (`centrar`).
- **Variables dentro del mes:** Sólo `ccajas_depositos_otras` = `ccajas_depositos` + `ccajas_otras`, que reemplaza a sus dos componentes (01_preparar_datos.py). El bloque `nuevas` de 02_variables.py (tres sumas Visa+Master con su cobertura, saldo/límite por tarjeta y balance de transferencias) no se activa en D.
- **Variables históricas:** Lag 1, delta 1, lag 2 y delta 2 de todos los predictores (`construir(df, hist_1y2_todas=True)`), uniendo por cliente y mes calendario exacto: si falta el registro de k meses antes, queda NA. Se calculan sobre los seis meses antes de filtrar, así 202107 aporta los lags de 202108. Según el README quedan 735 columnas útiles.
- **Selección de variables:** No hay selección por importancia. Se descartan las columnas con menos de 2 valores distintos (contando NA) en las filas de entrenamiento (06_receta_denicolay.py, línea 63), además de las seis columnas quitadas en 01_preparar_datos.py.
- **Optimización de hiperparámetros:** Los scripts que corre reproducir.py no buscan: usan valores fijos. origen/d04_busqueda.py hace una búsqueda con Optuna (`TPESampler` con semilla 147347 y `n_startup_trials=12`; 40 pruebas: 3 anclas, 9 al azar y 28 adaptativas, según el docstring) sobre `num_leaves` (16–255) y el hessiano de referencia h (0,5–128), en escala logarítmica. Cada prueba entrena hasta 8.000 rondas con 2 semillas en dos cortes (202103 → 202105 y 202103–202104 → 202106), sobre las variables `BASE`, y toma la cantidad de rondas (1.000, 2.000, 3.000, 5.000 u 8.000) de mayor A, la media de la ganancia entre 8.000 y 15.000 envíos. origen/d04_seleccion.py compara las 5 pruebas de mayor A, con 5 semillas, contra la configuración anterior. Según origen/README.md, de ahí sale la prueba 38: 83 hojas y h = 12,79.
- **Hiperparámetros finales:** `objective=binary`, `learning_rate=0.005`, `num_leaves=83`, `max_bin=31`, `min_data_in_leaf=0`, `min_sum_hessian_in_leaf` = 12,791817301585011 × filas de entrenamiento / 326.184, `feature_fraction=0.5`, `feature_fraction_bynode=0.2`, `bagging_fraction=1.0`, `bagging_freq=0`, `feature_pre_filter=False`, 1.000 rondas, `num_threads=12`, `deterministic=True`, `force_col_wise=True` (06_receta_denicolay.py).
- **Semillas:** 20 semillas definidas en el código: 147347, 322607, 462467, 782149 y 983809 y los tres primos siguientes a cada una (`semillas()` en 03_envios_tablero.py). Cada una se pasa como `seed` a LightGBM.
- **Cantidad de semillas:** 20
- **Ensamble:** Promedio aritmético de las probabilidades de los 20 modelos, que tienen la misma configuración y distinta semilla.
- **Corte:** Cantidad fija: los 11.000 clientes de mayor probabilidad promedio, con `argsort` estable sobre los clientes ordenados por `numero_de_cliente`. 06_receta_denicolay.py escribe antes el archivo con 11.500 y 07_archivo_d10.py toma los primeros 11.000 del mismo orden. El valor sale de origen/regla_n.py: sobre siete escenarios de ganancia en meses con clase y la grilla 9.000–12.000 de paso 500, elige el N de menor arrepentimiento máximo y lo adopta si la media de G(N) − G(11.500) es positiva; el resultado guardado en origen/esperado/regla_n_d10.json es 11.000.
- **Validación:** Los scripts que corre reproducir.py no miden el modelo: comparan huellas SHA-256 con las de la corrida original. En `origen/` la validación es en un mes posterior al entrenamiento, con la ganancia G(k) = 1.100.000·TP(k) − 27.500·k (TP cuenta sólo BAJA+2): F1 202103 → 202105 y F2 202103–202104 → 202106 en la búsqueda y la selección; F1 (202103 → 202105), F2 (202103–202104 → 202106), F5 (202104 → 202105) y F4 (202105 → 202106) en la regla de N. DECISIONES.md describe además comparaciones en el tablero público.
- **Salidas:** `datos/competencia_01_d01.parquet`, `datos/reparaciones_d01.parquet` y `datos/resumen_d01.json`; en `envios/d06d/`: 20 archivos `probabilidades_<semilla>.npy`, `claves_202108.npy`, `columnas.json`, `d06dn11500.csv` y `manifiesto.json`; en `envios/d10d/`: `d10dn11000.csv` y `manifiesto.json`; `envios/reproduccion_d10d.json` con huellas y tiempos. Ninguna está en el repositorio.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)
- El repositorio declara el uso de asistentes de IA (`proceso.uso_de_ia_declarado`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)

## Técnicas sólo exploradas

- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Rank o percentil de variables dentro de cada mes (`drifting.rank_por_mes`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: no
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README: Windows 11 Pro, AMD Ryzen 7 9800X3D (8 núcleos, 16 hilos), Python 3.13.3 de 64 bits y las versiones de requirements.txt (duckdb 1.5.5, lightgbm 4.6.0, numpy 2.2.6, pandas 2.2.3, pyarrow 23.0.1 y dependencias indirectas). Declara 43 minutos de corrida y unos 12 GB de memoria máxima; en macOS pide además `libomp`.

## Pasos del camino de la entrega

1. **Control del entorno y del crudo.** `reproducir.py` compara las versiones instaladas con las de `requirements.txt` (avisa si difieren), exige que el crudo exista y que su SHA-256 sea el de `huellas_esperadas.json`, y termina si ya existen las carpetas de salida de la entrega. (`reproducir.py` líneas 55–71; `reproducir.py` líneas 97–115)
2. **Pruebas con paneles sintéticos.** Antes de preparar los datos corre `test_01_preparar_datos.py` y `test_02_variables.py`, que prueban el cálculo de la clase, los bordes de las reparaciones, la lectura del identificador y la historia por mes exacto. (`reproducir.py` líneas 118–119; `test_01_preparar_datos.py` líneas 34–42; `test_02_variables.py` líneas 40–63)
3. **Lectura del crudo.** `01_preparar_datos.py` lee `competencia_01_crudo.csv` con DuckDB, con `numero_de_cliente` como texto convertido a BIGINT, y controla tipos, claves cliente-mes únicas, los seis meses 202103–202108 y las columnas esperadas. (`01_preparar_datos.py` líneas 68–73; `01_preparar_datos.py` líneas 124–144)
4. **Cálculo de clase_ternaria.** Con funciones de ventana por cliente asigna BAJA+1 si el cliente no está el mes siguiente, BAJA+2 si está el siguiente y no el subsiguiente, y CONTINUA en el resto; 202107 sólo admite BAJA+1 y 202108 queda sin clase. Después exige las cantidades esperadas de BAJA+1 y BAJA+2 por mes. (`01_preparar_datos.py` líneas 76–92; `01_preparar_datos.py` líneas 146–146; `01_preparar_datos.py` líneas 172–181)
5. **Reparaciones de datos.** Quita seis columnas (`ccajas_depositos`, `ccajas_otras`, `Visa_mconsumototal`, `Master_mconsumototal`, `cprestamos_personales`, `mprestamos_personales`), agrega `ccajas_depositos_otras` como suma de las dos primeras y pasa a NA los valores de `*_mfinanciacion_limite` que superan 10 veces un límite de compra positivo y los `*_Fvencimiento` menores que −1.000.000. Guarda el valor original de cada celda modificada. (`01_preparar_datos.py` líneas 44–49; `01_preparar_datos.py` líneas 95–113; `01_preparar_datos.py` líneas 148–163)
6. **Controles y escritura del dataset de trabajo.** Compara celda por celda la salida con el crudo, verifica que las celdas reparadas quedaron en NA y escribe `datos/competencia_01_d01.parquet`, `reparaciones_d01.parquet` y `resumen_d01.json`. (`01_preparar_datos.py` líneas 189–223)
7. **Búsqueda de hojas y hessiano con Optuna (en origen/, fuera de reproducir.py).** `origen/d04_busqueda.py` corre 40 pruebas con `TPESampler` sobre `num_leaves` y el hessiano de referencia, con el resto de los hiperparámetros fijo. Cada prueba entrena 2 semillas en dos cortes (202103 → 202105 y 202103–202104 → 202106) y se valora con A, la media de la ganancia entre 8.000 y 15.000 envíos. Usa las variables `BASE` (historia selectiva), no las de D. (`origen/d04_busqueda.py` líneas 65–77; `origen/d04_busqueda.py` líneas 138–169; `origen/d04_busqueda.py` líneas 210–236)
8. **Selección entre cinco finalistas (en origen/, fuera de reproducir.py).** `origen/d04_seleccion.py` toma las 5 pruebas de mayor A y las compara, con 5 semillas, contra la configuración anterior (learning_rate 0,05, 63 hojas, 500 rondas). Según origen/README.md, de acá sale la prueba 38: 83 hojas y h = 12,79; según el docstring del script, ninguna finalista cumplió la regla de la D04 (ΔA de al menos 10 M, entre otras condiciones). (`origen/d04_seleccion.py` líneas 74–79; `origen/d04_seleccion.py` líneas 133–168)
9. **Variables históricas: lags y deltas de orden 1 y 2.** `06_receta_denicolay.py` llama a `construir(df, hist_1y2_todas=True)` sobre los seis meses: para cada predictor agrega el valor de 1 y de 2 meses calendario antes (lag) y la diferencia entre el valor actual y ese lag (delta). Después se queda con 202103–202106 y 202108. (`02_variables.py` líneas 84–103; `02_variables.py` líneas 145–146; `06_receta_denicolay.py` líneas 54–55)
10. **Matrices de entrenamiento y de predicción y clase binaria.** Descarta las columnas con menos de 2 valores distintos en entrenamiento, arma las matrices en float32 y define la etiqueta: 1 si la clase es BAJA+1 o BAJA+2, 0 si es CONTINUA. Guarda las claves de 202108, ordenadas por cliente, y la lista de columnas. (`06_receta_denicolay.py` líneas 56–71)
11. **Entrenamiento de 20 LightGBM, uno por semilla.** Construye el `Dataset` una vez y entrena un modelo por semilla (las cinco iniciales y los tres primos siguientes a cada una) con 83 hojas, 1.000 rondas, learning_rate 0,005 y `min_sum_hessian_in_leaf` escalado por la cantidad de filas. Cada modelo predice 202108 y sus probabilidades se guardan en un `.npy`. (`06_receta_denicolay.py` líneas 42–45; `06_receta_denicolay.py` líneas 74–86; `03_envios_tablero.py` líneas 58–74)
12. **Promedio de probabilidades y archivo de 11.500 clientes.** Promedia las 20 probabilidades, ordena de mayor a menor con desempate estable y escribe `d06dn11500.csv` con los primeros 11.500 clientes, un identificador por línea, sin encabezado y con saltos CRLF. (`06_receta_denicolay.py` líneas 87–104; `03_envios_tablero.py` líneas 81–88)
13. **Regla para la cantidad de clientes (en origen/, fuera de reproducir.py).** `origen/regla_n.py` entrena D con las 20 semillas en cuatro cortes de validación (meses validados: 202105 y 202106), arma siete escenarios de ganancia y elige en la grilla 9.000–12.000 el N de menor arrepentimiento máximo; lo adopta si la media de G(N) − G(11.500) es positiva. El resultado guardado en `origen/esperado/regla_n_d10.json` es N = 11.000. (`origen/regla_n.py` líneas 52–54; `origen/regla_n.py` líneas 71–78; `origen/regla_n.py` líneas 93–133; `origen/esperado/regla_n_d10.json` líneas 68–79)
14. **Archivo final con 11.000 clientes.** `07_archivo_d10.py` recalcula el orden con las 20 probabilidades guardadas, exige que los primeros 11.500 coincidan con `d06dn11500.csv` y escribe `d10dn11000.csv` con los primeros 11.000, sin reentrenar. (`07_archivo_d10.py` líneas 31–53)
15. **Comparación con las huellas de la corrida original.** `reproducir.py` compara los SHA-256 del parquet, de las claves, de las columnas y de las 20 probabilidades (avisa si difieren) y el del CSV final: si no coincide con el de `huellas_esperadas.json`, termina con `NO REPRODUCE`. (`reproducir.py` líneas 84–94; `reproducir.py` líneas 121–134; `huellas_esperadas.json` líneas 10–49)

## Archivos

- `huellas_esperadas.json` · configuracion · JSON · 134 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/huellas_esperadas.json.txt) — SHA-256 esperados del crudo y del parquet de datos y, para cada entrega (`d10d`, `d06d`, `base`), los pasos a correr, las carpetas de salida y las huellas de las claves, las columnas, las 20 probabilidades y el CSV final.
- `reproducir.py` · principal · Python · 138 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/reproducir.py.txt) — Orquestador: controla el entorno y la huella del crudo, corre las pruebas, `01_preparar_datos.py` y los pasos de la entrega pedida (por defecto `06_receta_denicolay.py` y `07_archivo_d10.py`), y compara cada etapa con `huellas_esperadas.json`.
- `requirements.txt` · configuracion · Texto · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/requirements.txt.txt) — Diez paquetes con versión exacta: duckdb 1.5.5, lightgbm 4.6.0, numpy 2.2.6, pandas 2.2.3, pyarrow 23.0.1 y cinco dependencias indirectas; el comentario indica Python 3.13.3 en Windows 11.
- `07_archivo_d10.py` · principal · Python · 65 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/07_archivo_d10.py.txt) — Sin reentrenar, toma las 20 probabilidades de `envios/d06d/`, verifica que su promedio reproduzca `d06dn11500.csv` y escribe `d10dn11000.csv` con los primeros 11.000 clientes del mismo orden.
- `01_preparar_datos.py` · principal · Python · 227 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/01_preparar_datos.py.txt) — Lee el crudo con DuckDB, recalcula `clase_ternaria`, aplica las reparaciones (suma de cajas, seis columnas quitadas, dos reglas de NA), controla el resultado contra el crudo y escribe `datos/competencia_01_d01.parquet`.
- `DECISIONES.md` · explicacion · Markdown · 205 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/DECISIONES.md.txt) — Resumen de once decisiones (D01 a D11) del 5 al 9-oct-2026: procedimiento, métrica A y regla de reemplazo, datos, variables, clase, hiperparámetros, archivo final, rondas posteriores y corte, con los valores de ganancia local y del tablero público que declara el autor, y una sección sobre el uso de asistentes de IA (Claude y Codex).
- `02_variables.py` · principal · Python · 151 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/02_variables.py.txt) — Módulo de variables. `construir()` arma el panel según las opciones pedidas; D lo llama con `hist_1y2_todas=True`, que agrega lag y delta de orden 1 y 2 de todos los predictores. Las demás opciones (centrado de cierres, indicadores de mantenimiento, rankings, historia selectiva y amplia, variables nuevas) no se activan en D.
- `06_receta_denicolay.py` · principal · Python · 108 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/06_receta_denicolay.py.txt) — Entrena el modelo D: 20 LightGBM (uno por semilla) con 202103–202106, clase BAJA+1 o BAJA+2 contra CONTINUA y lags y deltas de orden 1 y 2 de todos los predictores; predice 202108, promedia las probabilidades y escribe `d06dn11500.csv` con los 11.500 clientes de mayor promedio.
- `README.md` · explicacion · Markdown · 121 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/README.md.txt) — Presentación de la entrega: qué archivo reproduce (`d10dn11000.csv`, con su SHA-256), el modelo D, cómo reproducirlo, qué hace cada script, qué fija el resultado, las huellas, las diferencias con los scripts originales y qué no incluye el repositorio.
- `05_envios_ensamble.py` · secundario · Python · 142 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/05_envios_ensamble.py.txt) — Camino de un envío anterior, la «base» (`d04k2en11500.csv`): entrena 20 LightGBM con las variables `BASE` (historia selectiva), clase BAJA+1 o BAJA+2 y los hiperparámetros de `03_envios_tablero.py`, y arma un archivo con los N clientes de mayor promedio. `reproducir.py` lo corre sólo con el argumento `base`.
- `test_02_variables.py` · secundario · Python · 126 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/test_02_variables.py.txt) — Nueve pruebas de `02_variables.py` con paneles sintéticos: cierres centrados, indicadores de mantenimiento, historia por mes exacto de orden 1 y 2, `construir()` sin opciones y con `BASE`, variables nuevas y ranking por mes. `reproducir.py` lo corre antes de preparar los datos.
- `test_01_preparar_datos.py` · secundario · Python · 107 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/test_01_preparar_datos.py.txt) — Cuatro pruebas de `01_preparar_datos.py` con datos sintéticos: clase, bordes de las reglas de NA, identificador en notación científica y rutas con apóstrofo. `reproducir.py` lo corre antes de preparar los datos.
- `03_envios_tablero.py` · principal · Python · 145 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/03_envios_tablero.py.txt) — `06_receta_denicolay.py` y `07_archivo_d10.py` lo cargan como módulo y usan sus rutas, los meses de entrenamiento y de predicción, `semillas()`, `escribir_csv()` y `huella()`. Como script arma tres envíos de prueba con clase BAJA+2 contra el resto, que `reproducir.py` no corre.
- `datos/LEEME.md` · explicacion · Markdown · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/datos/LEEME.md.txt) — Indica que en `datos/` va el crudo de la cátedra (tamaño, SHA-256 y dirección de descarga), que no se incluye en el repositorio, y qué archivos escribe ahí `01_preparar_datos.py`.
- `origen/d04_busqueda.py` · principal · Python · 268 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/origen/d04_busqueda.py.txt) — Búsqueda con Optuna de `num_leaves` y del hessiano de referencia, de donde según origen/README.md salen las 83 hojas y h = 12,79 que `06_receta_denicolay.py` tiene fijos. `reproducir.py` no lo ejecuta; el README indica que no hace falta para reproducir el archivo.
- `origen/requirements.txt` · configuracion · Texto · 15 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/origen/requirements.txt.txt) — Incluye `../requirements.txt` y agrega optuna 5.0.0 y otros once paquetes con versión exacta, para los scripts de `origen/`.
- `origen/d04_seleccion.py` · principal · Python · 186 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/origen/d04_seleccion.py.txt) — Compara, con 5 semillas y en los cortes F1 y F2, las 5 pruebas de mayor A de la búsqueda contra la configuración anterior. Según su docstring, de acá sale la prueba 38 (83 hojas, h = 12,791817301585011). `reproducir.py` no lo ejecuta.
- `origen/README.md` · explicacion · Markdown · 91 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/origen/README.md.txt) — Explica la cadena búsqueda → selección → D → regla de N → archivo, cómo correr los scripts de `origen/`, qué fija sus resultados, qué cambia respecto de los scripts originales y qué se comprobó antes de publicar.
- `origen/regla_n.py` · principal · Python · 159 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/origen/regla_n.py.txt) — Calcula la cantidad de clientes a enviar: entrena D con 20 semillas en cuatro cortes de validación, arma siete escenarios de ganancia y aplica una regla de arrepentimiento máximo sobre la grilla 9.000–12.000. Según su docstring, de acá sale N = 11.000. `reproducir.py` no lo ejecuta.
- `origen/comun.py` · principal · Python · 53 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/origen/comun.py.txt) — Módulo compartido por los tres scripts de `origen/`: rutas, carga de `02_variables.py`, `03_envios_tablero.py` y `06_receta_denicolay.py` como módulos, curva de ganancia en millones y comparación numérica con tolerancia.
- `origen/esperado/regla_n_d10.json` · configuracion · JSON · 80 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/farpp8/origen/esperado/regla_n_d10.json.txt) — Resultado guardado de la regla de N: ganancia G de siete escenarios en la grilla 9.000–12.000, arrepentimiento máximo por N, `N_estrella` 11000, `mejora_media` 2,99 y `N_final` 11000. `origen/regla_n.py` compara su salida contra este archivo.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### reproducir.py

Orquestador: controla el entorno y la huella del crudo, corre las pruebas, `01_preparar_datos.py` y los pasos de la entrega pedida (por defecto `06_receta_denicolay.py` y `07_archivo_d10.py`), y compara cada etapa con `huellas_esperadas.json`.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–28] Docstring. Describe las tres entregas que el script reproduce (`d10d` por defecto,
#   `d06d` y `base`), los pasos que corre y la regla de detención: sólo un crudo distinto o un CSV final
#   distinto frenan la corrida; las diferencias intermedias se informan.
# -*- coding: utf-8 -*-
"""Reproduce desde el crudo un archivo enviado en la Competencia 1 y lo compara byte por byte.

Uso: `python reproducir.py [entrega]`, con el crudo de la cátedra en `datos/competencia_01_crudo.csv` o en la ruta
de la variable de entorno COMPETENCIA_01_CRUDO.
- `python reproducir.py` (o `d10d`): **el último envío**, `d10dn11000.csv`: D con N = 11.000, la regla de N de D10.
  Corre D y después `07_archivo_d10.py`. Tarda unos 40 minutos.
- `python reproducir.py d06d`: **D**, `d06dn11500.csv`: C0 con *lags* y deltas 1 y 2 de todas las variables,
  la receta de la prueba 38 y K2 (D06). Tarda unos 40 minutos.
- `python reproducir.py base`: la entrega anterior, `d04k2en11500.csv`: K2 sobre C7 (D05). Tarda unos 4 minutos.

Pasos:
1. controla el entorno y la huella SHA-256 del crudo;
2. corre las pruebas de los pasos 1 y 2;
3. `01_preparar_datos.py`: el dataset con las reparaciones de D01, en `datos/`;
4. los pasos de la entrega, según `huellas_esperadas.json`:
   - D: `06_receta_denicolay.py`, 20 modelos entrenados con 202103–202106 que predicen 202108, y el archivo con los
     11.500 clientes de mayor promedio;
   - D con N = 11.000: los de D y `07_archivo_d10.py`, que toma los 11.000 primeros del mismo promedio;
   - base: `05_envios_ensamble.py entrenar d03k2` y `05_envios_ensamble.py archivo d03k2 d04k2e 11500`.

Cada etapa se compara con `huellas_esperadas.json`, tomadas de la corrida que generó el envío. Detienen la
reproducción sólo dos diferencias: un crudo distinto, porque ya no hay nada que comparar, y un CSV final distinto,
porque es lo que se entregó. Las diferencias intermedias se informan y se sigue: el parquet y las probabilidades
pueden cambiar con otra versión o en otro procesador sin que cambie la lista de clientes.

Salidas: las de cada paso, en `datos/` y `envios/`, y `envios/reproduccion_<entrega>.json` con las huellas y los tiempos.
"""
# [Anotación · líneas 29–44] Importa módulos de la biblioteca estándar y define las rutas: la carpeta del
#   script, el crudo (variable de entorno `COMPETENCIA_01_CRUDO` o `datos/competencia_01_crudo.csv`), las
#   huellas esperadas leídas de `huellas_esperadas.json`, la carpeta `envios/`, la versión de Python de la
#   corrida original (3.13.3) y la entrega por defecto (`d10d`).
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CRUDO = Path(os.environ.get("COMPETENCIA_01_CRUDO", AQUI / "datos" / "competencia_01_crudo.csv")).resolve()
ESPERADAS = json.loads((AQUI / "huellas_esperadas.json").read_text(encoding="utf-8"))
ENVIOS = AQUI / "envios"
PYTHON_ORIGINAL = "3.13.3"
POR_DEFECTO = "d10d"


# [Anotación · líneas 47–52] `huella()`: calcula el SHA-256 de un archivo leyéndolo en bloques de 1 MiB.
def huella(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


# [Anotación · líneas 55–71] `entorno()`: recorre `requirements.txt`, obtiene la versión instalada de cada
#   paquete y termina si alguno falta; si una versión instalada o la de Python difiere de la fijada, imprime un
#   aviso y sigue. Devuelve las versiones instaladas.
def entorno():
    """Versiones instaladas de los paquetes de requirements.txt; si alguna difiere, se avisa y se sigue."""
    instaladas = {}
    for linea in (AQUI / "requirements.txt").read_text(encoding="utf-8").splitlines():
        linea = linea.split("#")[0].strip()
        if not linea:
            continue
        nombre, fijada = linea.split("==")
        try:
            instaladas[nombre] = importlib.metadata.version(nombre)
        except importlib.metadata.PackageNotFoundError:
            raise SystemExit(f"falta {nombre}: instalar con `pip install -r requirements.txt`")
        if instaladas[nombre] != fijada:
            print(f"AVISO: {nombre} {instaladas[nombre]}; el envío se generó con {fijada}")
    if platform.python_version() != PYTHON_ORIGINAL:
        print(f"AVISO: Python {platform.python_version()}; el envío se generó con {PYTHON_ORIGINAL}")
    return instaladas


# [Anotación · líneas 74–81] `correr()`: ejecuta un script en un subproceso con el mismo intérprete, desde la
#   carpeta del repositorio y con `COMPETENCIA_01_CRUDO` apuntando al crudo; registra el paso, los segundos y el
#   código de salida, y termina la reproducción si el código no es 0.
def correr(pasos, *args):
    """Corre un paso con este mismo Python y el crudo ya controlado; si falla, la reproducción se detiene."""
    print(f"\n>>> python {' '.join(args)}", flush=True)
    t0 = time.time()
    r = subprocess.run([sys.executable, *args], cwd=AQUI, env={**os.environ, "COMPETENCIA_01_CRUDO": str(CRUDO)})
    pasos.append({"paso": " ".join(args), "segundos": round(time.time() - t0, 1), "codigo": r.returncode})
    if r.returncode != 0:
        raise SystemExit(f"falló `python {' '.join(args)}` (código {r.returncode})")


# [Anotación · líneas 84–94] `comparar()`: calcula el SHA-256 de cada archivo de una etapa, lista los que
#   difieren del valor esperado, imprime un aviso o la coincidencia y devuelve cuántos coinciden y cuáles no.
def comparar(etapa, carpeta, esperadas):
    """Compara las huellas de una etapa con las de la corrida original e informa las que difieren."""
    distintas = [nombre for nombre, h in esperadas.items() if huella(carpeta / nombre) != h]
    if distintas:
        print(f"AVISO, {etapa}: {len(distintas)} de {len(esperadas)} archivos difieren de la corrida original "
              f"({', '.join(distintas[:3])}). Se sigue: lo que decide es el CSV.")
    elif len(esperadas) == 1:
        print(f"{etapa}: el archivo coincide con el de la corrida original")
    else:
        print(f"{etapa}: los {len(esperadas)} archivos coinciden con los de la corrida original")
    return {"coinciden": len(esperadas) - len(distintas), "total": len(esperadas), "distintos": distintas}


# [Anotación · líneas 97–115] `main()`, controles previos: verifica que la entrega pedida exista en
#   `huellas_esperadas.json`, toma el nombre y la huella del CSV esperado, registra sistema, procesador, Python
#   y paquetes, exige que el crudo exista y que su SHA-256 sea el esperado, y termina si ya existen las carpetas
#   de salida de la entrega dentro de `envios/`.
def main(nombre):
    if nombre not in ESPERADAS["entregas"]:
        raise SystemExit(f"entrega desconocida: {nombre}; las posibles son {', '.join(ESPERADAS['entregas'])}")
    entrega = ESPERADAS["entregas"][nombre]
    (csv_nombre, csv_esperada), = entrega["csv"].items()
    csv = ENVIOS / entrega["csv_en"] / csv_nombre
    t0 = time.time()
    resultado = {"entrega": nombre, "inicio": time.strftime("%Y-%m-%d %H:%M:%S"), "sistema": platform.platform(),
                 "procesador": platform.processor(), "python": platform.python_version(), "paquetes": entorno()}
    print(f"Entrega: {nombre}, {entrega['descripcion']}")
    if not CRUDO.exists():
        raise SystemExit(f"no encuentro el crudo en {CRUDO}: copiar competencia_01_crudo.csv a datos/ "
                         "o definir COMPETENCIA_01_CRUDO con su ruta")
    if huella(CRUDO) != ESPERADAS["crudo"]["competencia_01_crudo.csv"]:
        raise SystemExit(f"{CRUDO} no es el crudo de la cátedra: su SHA-256 no coincide")
    print("crudo: la huella coincide con la del dataset de la cátedra")
    for carpeta in {entrega["modelos_en"], entrega["csv_en"]}:
        if (ENVIOS / carpeta).exists():
            raise SystemExit(f"envios/{carpeta} ya existe: para reproducir desde cero, borrarla o moverla antes")

# [Anotación · líneas 117–124] Corre en orden `test_01_preparar_datos.py`, `test_02_variables.py` y
#   `01_preparar_datos.py`, compara la huella del parquet, corre los pasos de la entrega (para `d10d`:
#   `06_receta_denicolay.py` y `07_archivo_d10.py`) y compara las huellas de las claves, las columnas y las 20
#   probabilidades.
    pasos = resultado["pasos"] = []
    correr(pasos, "test_01_preparar_datos.py")
    correr(pasos, "test_02_variables.py")
    correr(pasos, "01_preparar_datos.py")
    resultado["datos"] = comparar("datos", AQUI / "datos", ESPERADAS["datos"])
    for paso in entrega["pasos"]:
        correr(pasos, *paso)
    resultado["modelos"] = comparar("modelos", ENVIOS / entrega["modelos_en"], entrega["modelos"])

# [Anotación · líneas 126–134] Calcula el SHA-256 del CSV final, escribe `envios/reproduccion_<entrega>.json`
#   con huellas, pasos y minutos, y termina con `NO REPRODUCE` si la huella no es la esperada; si coincide,
#   imprime `OK`.
    obtenida = huella(csv)
    resultado.update({"csv": csv_nombre, "sha256": obtenida, "sha256_esperado": csv_esperada,
                      "reproduce": obtenida == csv_esperada, "minutos": round((time.time() - t0) / 60, 1)})
    (ENVIOS / f"reproduccion_{nombre}.json").write_text(json.dumps(resultado, indent=1, ensure_ascii=False),
                                                         encoding="utf-8")
    if obtenida != csv_esperada:
        raise SystemExit(f"\nNO REPRODUCE: {csv_nombre} tiene SHA-256 {obtenida}; se esperaba {csv_esperada}")
    print(f"\nOK: {csv_nombre} coincide byte por byte con el archivo enviado (SHA-256 {obtenida}), "
          f"en {resultado['minutos']} minutos")


# [Anotación · líneas 137–138] Punto de entrada: toma la entrega del primer argumento de la línea de comandos
#   o usa `d10d`.
if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else POR_DEFECTO)
```

### 07_archivo_d10.py

Sin reentrenar, toma las 20 probabilidades de `envios/d06d/`, verifica que su promedio reproduzca `d06dn11500.csv` y escribe `d10dn11000.csv` con los primeros 11.000 clientes del mismo orden.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–19] Docstring. Indica que el archivo es el modelo D sin reentrenar con N = 11.000,
#   resume la regla de N de la decisión D10 y describe la entrada (`envios/d06d/`), el control contra
#   `d06dn11500.csv` y las salidas en `envios/d10d/`.
# -*- coding: utf-8 -*-
"""Competencia 1: el archivo de D con N = 11.000, la regla de N de la decisión D10 (9-oct-2026).

Es el modelo D de `06_receta_denicolay.py`, sin reentrenar ni cambiar nada: sólo cambia cuántos clientes se mandan.
- **Por qué 11.000:** la decisión D10 fijó una regla antes de mirar, que se aplicó sobre las 20 semillas de producción
  de D en cuatro cortes de validación (202103 → 202105, 202104 → 202105, 202103–04 → 202106 y 202105 → 202106) y en
  tres escenarios más (junio sin la cohorte de préstamos congelados, y junio con el 92% y el 85% de los aciertos).
  - N* es el que minimiza el arrepentimiento máximo sobre la grilla 9.000–12.000.
  - Se cambia de 11.500 a N* sólo si la media de la ganancia mejora.
  - Dio N* = 11.000, con una mejora media de +2,99 M. Ver DECISIONES.md.
- **Entrada:** las 20 probabilidades y las claves de agosto de `envios/d06d/` (de `06_receta_denicolay.py`).
- **Control:** los 11.500 primeros del mismo promedio tienen que ser, en el mismo orden, los de `d06dn11500.csv`.
- **Archivo:** los 11.000 clientes con mayor promedio de las 20 probabilidades, con desempate estable y el formato del
  envío. Es el prefijo de 11.000 líneas de `d06dn11500.csv`.

Uso: `python 07_archivo_d10.py`, después de `06_receta_denicolay.py`. Tarda unos segundos.

Salidas en `envios/d10d/`: `d10dn11000.csv` y `manifiesto.json`.
"""
# [Anotación · líneas 20–31] Importa numpy, carga `03_envios_tablero.py` como módulo `tb` y fija la carpeta de
#   origen (`d06d`), la de destino (`d10d`), N = 11.000 y el N del archivo de origen, 11.500.
import importlib.util
import json
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("tablero", AQUI / "03_envios_tablero.py")
tb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tb)

ORIGEN, NOMBRE, N, N_D = "d06d", "d10d", 11_000, 11_500


# [Anotación · líneas 34–43] `main()`: termina si falta `envios/d06d/manifiesto.json` o si
#   `envios/d10d/manifiesto.json` ya existe; carga las claves de 202108 y las 20 probabilidades (una por
#   semilla) y verifica tamaño y valores finitos.
def main():
    origen, carpeta = tb.SALIDA / ORIGEN, tb.SALIDA / NOMBRE
    if not (origen / "manifiesto.json").exists():
        raise SystemExit(f"falta envios/{ORIGEN}: primero python 06_receta_denicolay.py")
    if (carpeta / "manifiesto.json").exists():
        raise SystemExit(f"{NOMBRE} ya existe; no se sobrescribe")
    claves = np.load(origen / "claves_202108.npy", allow_pickle=False)
    probs = [np.load(origen / f"probabilidades_{s}.npy", allow_pickle=False) for s in tb.semillas()]
    if any(p.shape != claves.shape or not np.isfinite(p).all() for p in probs):
        raise RuntimeError("probabilidades inválidas en envios/d06d")
# [Anotación · líneas 44–47] Ordena los clientes por promedio de las 20 probabilidades, de mayor a menor y con
#   desempate estable, y exige que los primeros 11.500 sean, en el mismo orden, los de `d06dn11500.csv`.
    orden = np.argsort(-np.mean(probs, axis=0), kind="stable")
    ids_d = [int(x) for x in (origen / f"{ORIGEN}n{N_D}.csv").read_text(encoding="ascii").split()]
    if ids_d != claves[orden[:N_D]].tolist():
        raise RuntimeError(f"el promedio de las 20 probabilidades no reproduce {ORIGEN}n{N_D}.csv")
# [Anotación · líneas 48–53] Escribe `d10dn11000.csv` con los primeros 11.000 clientes de ese orden y verifica
#   que sean 11.000 identificadores distintos e iguales a las primeras 11.000 líneas de `d06dn11500.csv`.
    carpeta.mkdir(parents=True, exist_ok=True)
    csv = carpeta / f"{NOMBRE}n{N}.csv"
    tb.escribir_csv(csv, claves[orden[:N]])
    ids = [int(x) for x in csv.read_text(encoding="ascii").split()]
    if len(ids) != N or len(set(ids)) != N or ids != ids_d[:N]:
        raise RuntimeError(f"{csv.name}: control fallido")
# [Anotación · líneas 54–61] Escribe `manifiesto.json` con el origen, las semillas, N y las huellas, e imprime
#   el SHA-256 del CSV.
    manifiesto = {"envio": NOMBRE, "descripcion": "D con N = 11.000 (regla de N de D10)", "origen": f"envios/{ORIGEN}",
                  "semillas": tb.semillas(), "n_por_archivo": N,
                  "huellas": {f"{ORIGEN}/manifiesto.json": tb.huella(origen / "manifiesto.json"),
                              "07_archivo_d10.py": tb.huella(__file__)},
                  "archivos": [{"archivo": csv.name, "filas": N, "sha256": tb.huella(csv)}]}
    (carpeta / "manifiesto.json").write_text(json.dumps(manifiesto, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{NOMBRE}: {csv.name}, {N} clientes, el prefijo de {ORIGEN}n{N_D}.csv; "
          f"SHA-256 {manifiesto['archivos'][0]['sha256']}")


# [Anotación · líneas 64–65] Punto de entrada: ejecuta `main()` cuando el archivo se corre como script.
if __name__ == "__main__":
    main()
```

### 01_preparar_datos.py

Lee el crudo con DuckDB, recalcula `clase_ternaria`, aplica las reparaciones (suma de cajas, seis columnas quitadas, dos reglas de NA), controla el resultado contra el crudo y escribe `datos/competencia_01_d01.parquet`.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–30] Docstring. Enumera las operaciones sobre el crudo (clase, suma de cajas, columnas
#   quitadas, dos reglas de NA), el tratamiento del identificador escrito en notación científica y las tres
#   salidas en `datos/`.
# -*- coding: utf-8 -*-
"""Competencia 1, paso 1: dataset reparado según la decisión D01 (opción A, 5-oct-2026).

Parte del dataset original de la cátedra (`competencia_01_crudo.csv`), para que la entrega se pueda
reproducir desde cero. Aplica:

1. `clase_ternaria` con la lógica de la cátedra (notebook z470): falta en el mes siguiente = BAJA+1, aunque
   después vuelva; está en el siguiente pero no en el subsiguiente = BAJA+2. 202107 sólo admite BAJA+1 y
   202108 queda sin clase.
2. `ccajas_depositos + ccajas_otras` → `ccajas_depositos_otras`, y se sacan las componentes. Entre abril y
   junio las transacciones por caja se reclasificaron entre las dos.
3. Se sacan `Visa_mconsumototal` y `Master_mconsumototal`, idénticos a `*_mconsumospesos`.
4. NA en `*_mfinanciacion_limite` cuando `*_mlimitecompra > 0` y la financiación supera 10 veces el límite de
   compra: errores de escala de un mes por cliente.
5. NA en `*_Fvencimiento` menores que −1.000.000: valor centinela.
6. Se sacan `cprestamos_personales` y `mprestamos_personales`: en junio cambia su relación con la baja.

No se modifican los NA de descuentos, `cliente_vip` ni los estados de tarjeta.

El crudo escribe un identificador en notación científica, del tipo `9.9e+07`, en seis filas. Por eso
`numero_de_cliente` se lee como texto y se convierte a entero exacto (BIGINT); si alguna conversión no es exacta,
el proceso se detiene.

Salidas, en `datos/`:
- `competencia_01_d01.parquet`: los seis meses, con las reparaciones y la clase;
- `reparaciones_d01.parquet`: el valor original de cada celda modificada;
- `resumen_d01.json`: cantidades por regla y mes, clase por mes, versiones y huella del crudo.

Decisión y análisis: `decisiones/D01_datos/`. Revisión de código de Codex: `decisiones/D01_datos/revision_codigo_codex.md`.
"""
# [Anotación · líneas 31–54] Importa `duckdb` y define rutas y constantes: los seis meses 202103–202108, el
#   umbral de financiación (10), el centinela de vencimiento (−1.000.000), las seis columnas a quitar (`SACAR`),
#   las cuatro que se reparan (`REPARADAS`) y las cantidades esperadas de BAJA+2 (202103–202106) y de BAJA+1
#   (202103–202107) por mes.
import hashlib
import json
import os
import platform
from pathlib import Path

import duckdb

AQUI = Path(__file__).resolve().parent
# El crudo de la cátedra no se incluye en el repositorio: va en datos/, o en la ruta de COMPETENCIA_01_CRUDO.
CRUDO = Path(os.environ.get("COMPETENCIA_01_CRUDO", AQUI / "datos" / "competencia_01_crudo.csv"))
SALIDA = AQUI / "datos"

MESES = [202103, 202104, 202105, 202106, 202107, 202108]
UMBRAL_FINANCIACION = 10
CENTINELA_VENCIMIENTO = -1_000_000
SACAR = ["ccajas_depositos", "ccajas_otras", "Visa_mconsumototal", "Master_mconsumototal",
         "cprestamos_personales", "mprestamos_personales"]
REPARADAS = ["Visa_mfinanciacion_limite", "Master_mfinanciacion_limite", "Visa_Fvencimiento", "Master_Fvencimiento"]

# Verificado en D01 contra la definición literal: el archivo viejo marcaba CONTINUA a 29 clientes que faltan
# un mes y vuelven (`decisiones/D01_datos/cruce_claude.md`).
ESPERADO_BAJA2 = {202103: 960, 202104: 1139, 202105: 870, 202106: 1098}
ESPERADO_BAJA1 = {202103: 1019, 202104: 964, 202105: 1143, 202106: 874, 202107: 1103}


# [Anotación · líneas 57–65] `exigir()` lanza `RuntimeError` si una condición no se cumple. `literal()` arma
#   un literal de texto SQL duplicando cada apóstrofo.
def exigir(condicion, mensaje):
    """Control que no se apaga con `python -O`, a diferencia de assert."""
    if not condicion:
        raise RuntimeError(mensaje)


def literal(texto):
    """Literal de texto SQL con las comillas simples duplicadas, para que sirvan rutas como `O'Connor`."""
    return "'" + str(texto).replace("'", "''") + "'"


# [Anotación · líneas 68–73] `sql_leer_crudo()`: consulta que lee el CSV con `numero_de_cliente` como texto y
#   `foto_mes` como entero, usando todas las filas para detectar los demás tipos (`sample_size = -1`), y
#   convierte el identificador a DOUBLE y luego a BIGINT.
def sql_leer_crudo(path):
    """Lee el crudo con el identificador como texto y lo convierte a BIGINT."""
    return f"""
    SELECT * REPLACE (CAST(CAST(numero_de_cliente AS DOUBLE) AS BIGINT) AS numero_de_cliente)
    FROM read_csv({literal(path)}, header = true, sample_size = -1,
                  types = {{'numero_de_cliente': 'VARCHAR', 'foto_mes': 'INTEGER'}})"""


# [Anotación · líneas 76–92] `sql_clase()`: numera cada mes como año×12+mes y, por cliente, toma los dos
#   registros siguientes (`lead`). Asigna BAJA+2 si el registro siguiente es el mes inmediato y el subsiguiente
#   falta o está a más de dos meses; BAJA+1 si el registro siguiente falta o no es el mes inmediato; CONTINUA en
#   los demás registros anteriores al penúltimo mes. El último mes queda sin clase y el penúltimo sólo admite
#   BAJA+1.
def sql_clase(tabla):
    """Misma lógica que la cátedra: períodos consecutivos y los dos siguientes de cada cliente."""
    return f"""
    WITH p AS (
        SELECT numero_de_cliente, foto_mes, (foto_mes // 100) * 12 + foto_mes % 100 AS periodo0
        FROM {tabla}),
    l AS (
        SELECT *, lead(periodo0, 1) OVER w AS periodo1, lead(periodo0, 2) OVER w AS periodo2
        FROM p WINDOW w AS (PARTITION BY numero_de_cliente ORDER BY periodo0)),
    t AS (SELECT max(periodo0) AS ultimo FROM p)
    SELECT numero_de_cliente, foto_mes,
           CASE WHEN periodo0 < ultimo - 1 AND periodo1 = periodo0 + 1
                     AND (periodo2 IS NULL OR periodo2 > periodo0 + 2) THEN 'BAJA+2'
                WHEN periodo0 < ultimo AND (periodo1 IS NULL OR periodo1 > periodo0 + 1) THEN 'BAJA+1'
                WHEN periodo0 < ultimo - 1 THEN 'CONTINUA'
           END AS clase_ternaria
    FROM l, t"""


# [Anotación · líneas 95–101] Condiciones SQL de las dos reglas de NA por marca de tarjeta: límite de compra
#   positivo y financiación mayor que 10 veces ese límite; fecha de vencimiento menor que −1.000.000.
def regla_financiacion(marca):
    return (f"{marca}_mlimitecompra > 0 AND "
            f"{marca}_mfinanciacion_limite > {UMBRAL_FINANCIACION} * {marca}_mlimitecompra")


def regla_vencimiento(marca):
    return f"{marca}_Fvencimiento < {CENTINELA_VENCIMIENTO}"


# [Anotación · líneas 104–113] `sql_reparar()`: consulta que excluye las seis columnas de `SACAR`, reemplaza
#   por NULL los valores de `Visa/Master_mfinanciacion_limite` y `Visa/Master_Fvencimiento` que cumplen las
#   reglas y agrega `ccajas_depositos_otras` como suma de `ccajas_depositos` y `ccajas_otras`.
def sql_reparar(tabla):
    """Las reparaciones de D01 sobre una tabla con las columnas del crudo."""
    reemplazos = ", ".join(
        [f"CASE WHEN {regla_financiacion(m)} THEN NULL ELSE {m}_mfinanciacion_limite END AS {m}_mfinanciacion_limite"
         for m in ("Visa", "Master")]
        + [f"CASE WHEN {regla_vencimiento(m)} THEN NULL ELSE {m}_Fvencimiento END AS {m}_Fvencimiento"
           for m in ("Visa", "Master")])
    return f"""SELECT * EXCLUDE ({", ".join(SACAR)}) REPLACE ({reemplazos}),
                      ccajas_depositos + ccajas_otras AS ccajas_depositos_otras
               FROM {tabla}"""


# [Anotación · líneas 116–121] `huella()`: SHA-256 de un archivo, leído en bloques de 1 MiB.
def huella(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


# [Anotación · líneas 124–133] `main()`, lectura: crea `datos/`, lee el identificador como texto, exige que
#   todos los valores se conviertan a entero sin pérdida, cuenta los que no están escritos sólo con dígitos y
#   carga el crudo completo en la tabla `crudo`.
def main():
    SALIDA.mkdir(exist_ok=True)
    con = duckdb.connect()
    con.execute(f"CREATE TABLE texto AS SELECT numero_de_cliente FROM read_csv({literal(CRUDO.as_posix())}, header = true, all_varchar = true)")
    mal = con.execute("""SELECT count(*) FROM texto
                         WHERE try_cast(numero_de_cliente AS DOUBLE) IS NULL
                            OR CAST(numero_de_cliente AS DOUBLE) <> CAST(CAST(numero_de_cliente AS DOUBLE) AS BIGINT)""").fetchone()[0]
    exigir(mal == 0, f"{mal} identificadores no se convierten exactamente a entero")
    cientifica = con.execute("SELECT count(*) FROM texto WHERE NOT regexp_matches(numero_de_cliente, '^[0-9]+$')").fetchone()[0]
    con.execute(f"CREATE TABLE crudo AS {sql_leer_crudo(CRUDO.as_posix())}")

# [Anotación · líneas 135–144] Controles sobre el crudo: tipos BIGINT e INTEGER de las claves, pares cliente-
#   mes únicos y no nulos, meses iguales a la lista esperada y presencia de las columnas a quitar y a reparar.
    tipos = dict(con.execute("SELECT column_name, column_type FROM (DESCRIBE crudo)").fetchall())
    exigir(tipos["numero_de_cliente"] == "BIGINT" and tipos["foto_mes"] == "INTEGER", tipos)
    n_crudo, n_claves, n_nulas = con.execute("""SELECT count(*), count(DISTINCT (numero_de_cliente, foto_mes)),
                                                       count(*) FILTER (WHERE numero_de_cliente IS NULL OR foto_mes IS NULL)
                                                FROM crudo""").fetchone()
    exigir(n_crudo == n_claves and n_nulas == 0, "claves cliente-mes repetidas o nulas")
    meses = [m for m, in con.execute("SELECT DISTINCT foto_mes FROM crudo ORDER BY 1").fetchall()]
    exigir(meses == MESES, f"meses inesperados: {meses}")
    columnas_crudo = list(tipos)
    exigir(all(c in columnas_crudo for c in SACAR + REPARADAS), "faltan columnas esperadas en el crudo")

# [Anotación · líneas 146–157] Crea la tabla `clase` y la tabla `reparaciones`, que guarda cliente, mes,
#   variable, valor original y regla de cada celda que pasa a NA (cuatro consultas unidas, dos por marca).
    con.execute(f"CREATE TABLE clase AS {sql_clase('crudo')}")

    # Valor original de cada celda que se reemplaza por NA
    partes = []
    for marca in ("Visa", "Master"):
        partes.append(f"""SELECT numero_de_cliente, foto_mes, '{marca}_mfinanciacion_limite' AS variable,
                                 {marca}_mfinanciacion_limite AS valor_original, 'financiacion > 10 x limite de compra' AS regla
                          FROM crudo WHERE {regla_financiacion(marca)}""")
        partes.append(f"""SELECT numero_de_cliente, foto_mes, '{marca}_Fvencimiento',
                                 {marca}_Fvencimiento, 'centinela < -1000000'
                          FROM crudo WHERE {regla_vencimiento(marca)}""")
    con.execute("CREATE TABLE reparaciones AS " + " UNION ALL ".join(partes))

# [Anotación · líneas 159–170] Crea la tabla `final` uniendo el crudo reparado con la clase, ordenada por mes
#   y cliente, y exige que las columnas sean las del crudo menos las quitadas más `ccajas_depositos_otras` y
#   `clase_ternaria`, y que la cantidad de filas no cambie.
    con.execute(f"""
        CREATE TABLE final AS
        SELECT r.*, clase.clase_ternaria
        FROM ({sql_reparar('crudo')}) r JOIN clase USING (numero_de_cliente, foto_mes)
        ORDER BY foto_mes, numero_de_cliente""")

    # Esquema esperado
    columnas_final = [c for c, in con.execute("SELECT column_name FROM (DESCRIBE final)").fetchall()]
    esperadas = [c for c in columnas_crudo if c not in SACAR] + ["ccajas_depositos_otras", "clase_ternaria"]
    exigir(columnas_final == esperadas, "las columnas de salida no son las esperadas")
    n_final = con.execute("SELECT count(*) FROM final").fetchone()[0]
    exigir(n_final == n_crudo, (n_final, n_crudo))

# [Anotación · líneas 172–187] Cuenta la clase por mes y exige las cantidades esperadas de BAJA+2 y BAJA+1,
#   que 202108 no tenga clase y que 202107 no tenga CONTINUA. Exige además 4.159 celdas reparadas de
#   `Master_mfinanciacion_limite` en 202104 y 1.035 de `Visa_mfinanciacion_limite` en 202108.
    # Clase
    clase_mes = {}
    for m, c, n in con.execute("""SELECT foto_mes, coalesce(clase_ternaria, 'sin clase'), count(*)
                                  FROM final GROUP BY 1, 2 ORDER BY 1, 2""").fetchall():
        clase_mes.setdefault(m, {})[c] = n
    for m, n in ESPERADO_BAJA2.items():
        exigir(clase_mes[m].get("BAJA+2") == n, (m, clase_mes[m]))
    for m, n in ESPERADO_BAJA1.items():
        exigir(clase_mes[m].get("BAJA+1") == n, (m, clase_mes[m]))
    exigir(set(clase_mes[202108]) == {"sin clase"} and "CONTINUA" not in clase_mes[202107], "clase de julio o agosto")

    # Reparaciones
    rep = con.execute("SELECT variable, foto_mes, count(*) FROM reparaciones GROUP BY 1, 2 ORDER BY 1, 2").fetchall()
    rep_dict = {(v, m): n for v, m, n in rep}
    exigir(rep_dict[("Master_mfinanciacion_limite", 202104)] == 4159, "financiación Master de abril")
    exigir(rep_dict[("Visa_mfinanciacion_limite", 202108)] == 1035, "financiación Visa de agosto")

# [Anotación · líneas 189–204] Compara celda por celda el crudo con la salida: cada columna común puede
#   diferir sólo en la cantidad de celdas registradas en `reparaciones`; verifica que las celdas reparadas
#   quedaron en NA y que `ccajas_depositos_otras` es la suma de sus dos componentes.
    # Celda por celda: fuera de las reparaciones, la salida es idéntica al crudo
    comunes = [c for c in columnas_crudo if c not in SACAR and c not in ("numero_de_cliente", "foto_mes")]
    difs = con.execute("SELECT " + ", ".join(
        f'count(*) FILTER (WHERE c."{v}" IS DISTINCT FROM f."{v}")' for v in comunes)
        + " FROM crudo c JOIN final f USING (numero_de_cliente, foto_mes)").fetchone()
    difs = dict(zip(comunes, difs))
    rep_var = {v: sum(n for (vv, _), n in rep_dict.items() if vv == v) for v in REPARADAS}
    for v, n in difs.items():
        exigir(n == rep_var.get(v, 0), f"{v}: {n} celdas distintas del crudo, se esperaban {rep_var.get(v, 0)}")
    no_nulas = con.execute("SELECT " + " + ".join(
        f"(SELECT count(*) FROM reparaciones r JOIN final f USING (numero_de_cliente, foto_mes) "
        f"WHERE r.variable = '{v}' AND f.{v} IS NOT NULL)" for v in REPARADAS)).fetchone()[0]
    exigir(no_nulas == 0, "hay celdas reparadas que no quedaron en NA")
    suma = con.execute("""SELECT count(*) FILTER (WHERE f.ccajas_depositos_otras IS DISTINCT FROM c.ccajas_depositos + c.ccajas_otras)
                          FROM crudo c JOIN final f USING (numero_de_cliente, foto_mes)""").fetchone()[0]
    exigir(suma == 0, "la suma de cajas no coincide")

# [Anotación · líneas 206–223] Escribe `competencia_01_d01.parquet` (compresión zstd) y
#   `reparaciones_d01.parquet`, y arma, guarda e imprime `resumen_d01.json` con versiones, huella y tamaño del
#   crudo, columnas quitadas y agregadas, parámetros, clase por mes y reparaciones por variable y mes.
    con.execute(f"COPY final TO {literal((SALIDA / 'competencia_01_d01.parquet').as_posix())} (FORMAT parquet, COMPRESSION zstd)")
    con.execute(f"""COPY (SELECT * FROM reparaciones ORDER BY foto_mes, numero_de_cliente, variable)
                    TO {literal((SALIDA / 'reparaciones_d01.parquet').as_posix())} (FORMAT parquet)""")
    resumen = {
        "decision": "D01 opcion A (5-oct-2026)",
        "versiones": {"python": platform.python_version(), "duckdb": duckdb.__version__},
        "crudo": {"archivo": CRUDO.name, "sha256": huella(CRUDO), "filas": n_crudo, "columnas": len(columnas_crudo),
                  "identificadores_en_notacion_cientifica": cientifica},
        "salida": {"filas": n_final, "columnas": len(columnas_final)},
        "columnas_quitadas": SACAR,
        "columnas_agregadas": ["ccajas_depositos_otras", "clase_ternaria"],
        "parametros": {"umbral_financiacion": UMBRAL_FINANCIACION, "centinela_vencimiento": CENTINELA_VENCIMIENTO},
        "clase_por_mes": {str(m): clase_mes[m] for m in sorted(clase_mes)},
        "reparaciones_por_variable_y_mes": {f"{v} {m}": n for (v, m), n in sorted(rep_dict.items())},
        "celdas_distintas_del_crudo": {v: n for v, n in sorted(difs.items()) if n},
    }
    (SALIDA / "resumen_d01.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False, indent=1))


# [Anotación · líneas 226–227] Punto de entrada: ejecuta `main()` cuando el archivo se corre como script.
if __name__ == "__main__":
    main()
```

### 02_variables.py

Módulo de variables. `construir()` arma el panel según las opciones pedidas; D lo llama con `hist_1y2_todas=True`, que agrega lag y delta de orden 1 y 2 de todos los predictores. Las demás opciones (centrado de cierres, indicadores de mantenimiento, rankings, historia selectiva y amplia, variables nuevas) no se activan en D.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–33] Docstring. Describe `construir()`, la base `BASE` (C7: historia selectiva), las
#   opciones `centrar` y `mantenimiento` y los bloques optativos `rangos`, `hist_selectiva`, `hist_amplia`,
#   `nuevas` y `hist_1y2_todas`; indica que la historia une por cliente y mes calendario exacto.
# -*- coding: utf-8 -*-
"""Competencia 1, paso 2: variables según la decisión D02 (5 y 6-oct-2026).

Parte de `datos/competencia_01_d01.parquet` (paso 1). `construir()` arma el panel completo de variables; sin
opciones no transforma nada.

**Base vigente: `BASE`, es decir C7 = C0 + historia selectiva.** Usar `construir(df, **BASE)`. En la validación
local ningún bloque cumplió el umbral fijado antes, y el resultado fue C0. El 6-oct el usuario adoptó C7 por el
tablero público, que mide agosto: 84,77 contra 81,00 de C0, con 20 semillas cada uno.

La opción A fue aprobada primero y revertida después de la prueba, porque empeoró la validación de mayo en las
5 semillas. Sigue disponible como opción:
- `centrar=True`: `Visa_fultimo_cierre` y `Master_fultimo_cierre` pasan a la diferencia con la moda del mes,
  calculada entre los valores de 0 a 35 días; los NA se conservan;
- `mantenimiento=True`: `mcomisiones_mantenimiento` se reemplaza por dos indicadores, cobro (> 0) y devolución
  (< 0), que conservan los NA.

Copias exactas de versiones anteriores:
- la de las pruebas de D02 (valores por defecto = A): `experimentos/02_variables_usado_en_d02.py`;
- la de los envíos al tablero del 5-oct: `envios/02_variables_usado_en_envios_d02.py`.

- **Bloques optativos** (probados en D02, ninguno cumplió el umbral en la validación local):
  - `rangos`: ranking percentil dentro del mes de seis montos, conservando los originales;
  - `hist_selectiva`: *lag* 1 y delta 1 de seis conteos y del ranking mensual de cuatro montos (20 columnas);
  - `hist_amplia`: *lag* 1 y delta 1 de los predictores, con las exclusiones explícitas de `EXCLUIR_HIST_AMPLIA`;
  - `nuevas`: tres sumas Visa+Master, sus coberturas, saldo/límite por tarjeta y balance de transferencias;
  - `hist_1y2_todas`: *lag* y delta de orden 1 y 2 de todos los predictores, la receta de Denicolay (Zulip
    #192079). Se usa en el envío 3 al tablero.

La historia une por cliente y mes exacto (mes calendario anterior): marzo queda en NA y nunca se completa con
el presente ni con meses futuros. Los rankings usan sólo los valores de su propio mes.
Decisión: `decisiones/D02_variables/decision.md`.
"""
# [Anotación · líneas 34–57] Importa numpy y pandas y define listas de columnas: claves, clase, fechas de
#   cierre y variables en días, la comisión de mantenimiento, seis montos para ranking (`RANGOS`), seis conteos
#   y cuatro montos de la historia selectiva, las exclusiones de la historia amplia, tres pares Visa/Master para
#   sumar (`SUMAS`) y `BASE`, que activa sólo `hist_selectiva`.
import numpy as np
import pandas as pd

CLAVES = ["numero_de_cliente", "foto_mes"]
CLASE = "clase_ternaria"
CIERRES = ["Visa_fultimo_cierre", "Master_fultimo_cierre"]
DIAS = CIERRES + ["Visa_Fvencimiento", "Master_Fvencimiento", "Visa_fechaalta", "Master_fechaalta",
                  "Visa_Finiciomora", "Master_Finiciomora"]
MANTENIMIENTO = "mcomisiones_mantenimiento"
RANGOS = ["mpayroll", "mpayroll2", "mcomisiones", "mcomisiones_otras", "mrentabilidad", "mrentabilidad_annual"]
HIST_CONTEOS = ["ctrx_quarter", "cproductos", "ctarjeta_debito_transacciones", "ctarjeta_visa_transacciones",
                "ctarjeta_master_transacciones", "chomebanking_transacciones"]
HIST_MONTOS = ["mcuentas_saldo", "mpayroll", "mtransferencias_recibidas", "mtransferencias_emitidas"]
# Historia amplia: exclusiones exactas de la especificación conjunta (prueba_conjunta.json). Quedan fuera los
# estados y la mora (cierre transitorio de julio), el VIP (pico de junio), las variables en días y los descuentos
# (pico de julio). Edad y antigüedad se incluyen: la revisión de Codex marcó que excluirlas se apartaba de la
# especificación.
EXCLUIR_HIST_AMPLIA = {"Visa_status", "Master_status", "Visa_delinquency", "Master_delinquency", "cliente_vip",
                       "mtarjeta_visa_descuentos", "mtarjeta_master_descuentos", *DIAS}
SUMAS = {"suma_msaldototal": ("Visa_msaldototal", "Master_msaldototal"),
         "suma_mlimitecompra": ("Visa_mlimitecompra", "Master_mlimitecompra"),
         "suma_cconsumos": ("Visa_cconsumos", "Master_cconsumos")}
# Base vigente desde el 6-oct: C7 (decisión del usuario sobre el tablero; decisiones/D02_variables/decision.md).
BASE = {"hist_selectiva": True}


# [Anotación · líneas 60–81] Funciones auxiliares: `_periodo()` convierte AAAAMM en año×12+mes;
#   `centrar_cierres()` resta a los días desde el último cierre la moda del mes calculada entre los valores de 0
#   a 35; `indicadores_mantenimiento()` reemplaza la comisión de mantenimiento por dos indicadores (cobro y
#   devolución) que conservan los NA; `rango_mes()` calcula el ranking percentil dentro de cada mes. D no usa
#   `centrar_cierres()`, `indicadores_mantenimiento()` ni `rango_mes()`.
def _periodo(foto_mes):
    return (foto_mes // 100) * 12 + foto_mes % 100


def centrar_cierres(df):
    """Días desde el último cierre menos la moda del mes, calculada entre los valores de 0 a 35."""
    for v in CIERRES:
        validos = df.loc[df[v].between(0, 35), ["foto_mes", v]]
        moda = validos.groupby("foto_mes")[v].agg(lambda s: s.value_counts().idxmax())
        df[v] = df[v] - df["foto_mes"].map(moda)
    return df


def indicadores_mantenimiento(df):
    m = df.pop(MANTENIMIENTO)
    df["mantenimiento_cobro"] = np.where(m.isna(), np.nan, (m > 0).astype(float))
    df["mantenimiento_devolucion"] = np.where(m.isna(), np.nan, (m < 0).astype(float))
    return df


def rango_mes(df, v):
    return df.groupby("foto_mes")[v].rank(pct=True)


# [Anotación · líneas 84–103] `historia()`: para cada orden k copia las columnas pedidas con el período
#   corrido k meses hacia adelante y las une a la tabla actual por cliente y período (unión izquierda, uno a
#   uno). De ahí salen `<variable>_lag<k>`, el valor de k meses antes, y `<variable>_delta<k>`, el valor actual
#   menos ese lag, en float32; sin registro en ese mes exacto quedan en NA.
def historia(df, columnas, ordenes=(1,)):
    """lagk = valor del mismo cliente k meses calendario antes; deltak = actual − lagk. Sin ese mes, NA.

    Con `ordenes=(1, 2)`, el *lag* 2 existe aunque falte el mes intermedio: es el mes exacto t−2.
    """
    # Claves en int64 de los dos lados: con foto_mes INTEGER (int32) del parquet, pandas no puede unir.
    per = _periodo(df["foto_mes"].astype("int64")).to_numpy()
    cliente = df["numero_de_cliente"].astype("int64").to_numpy()
    actual = pd.DataFrame({"numero_de_cliente": cliente, "_per": per})
    salida = {}
    for k in ordenes:
        previo = df[columnas].copy()
        previo["numero_de_cliente"] = cliente
        previo["_per"] = per + k
        lag = actual.merge(previo, on=["numero_de_cliente", "_per"], how="left", validate="one_to_one")
        for v in columnas:
            lagk = lag[v].to_numpy(dtype="float64")
            salida[f"{v}_lag{k}"] = lagk.astype("float32")
            salida[f"{v}_delta{k}"] = (df[v].to_numpy(dtype="float64") - lagk).astype("float32")
    return pd.DataFrame(salida, index=df.index)


# [Anotación · líneas 106–119] `nuevas_variables()`: tres sumas Visa+Master con su cobertura (cuántos de los
#   dos sumandos no son NA), el cociente saldo/límite de compra por tarjeta con denominador positivo y finito, y
#   el balance de transferencias (recibidas − emitidas) / (|recibidas| + |emitidas|). D no activa este bloque.
def nuevas_variables(df):
    out = {}
    for nombre, (a, b) in SUMAS.items():
        out[nombre] = df[[a, b]].sum(axis=1, min_count=1)
        out[nombre.replace("suma_", "cobertura_")] = df[[a, b]].notna().sum(axis=1).astype(float)
    for t in ("Visa", "Master"):
        lim = df[f"{t}_mlimitecompra"]
        lim = lim.where((lim > 0) & np.isfinite(lim))          # denominador positivo y finito; si no, NA
        out[f"{t}_saldo_limite"] = df[f"{t}_msaldototal"] / lim
    rec, emi = df["mtransferencias_recibidas"], df["mtransferencias_emitidas"]
    den = rec.abs() + emi.abs()
    den = den.where((den > 0) & np.isfinite(den))
    out["balance_transferencias"] = (rec - emi) / den
    return pd.DataFrame(out, index=df.index)


# [Anotación · líneas 122–147] `construir()`: verifica que estén las columnas requeridas, ordena por cliente y
#   mes, aplica las opciones pedidas y concatena por columnas los bloques activados. Con `hist_1y2_todas=True`,
#   la opción que usa D, agrega `historia()` de órdenes 1 y 2 sobre todos los predictores (todas las columnas
#   salvo claves y clase).
def construir(df, centrar=False, mantenimiento=False, rangos=False, hist_selectiva=False, hist_amplia=False,
              nuevas=False, hist_1y2_todas=False):
    """Devuelve el panel con claves, clase y predictores. No modifica `df`."""
    faltan = {*CIERRES, MANTENIMIENTO, *RANGOS, *HIST_CONTEOS, *HIST_MONTOS, *(c for p in SUMAS.values() for c in p)} - set(df.columns)
    if faltan:
        raise KeyError(f"faltan columnas: {sorted(faltan)}")
    df = df.sort_values(CLAVES).reset_index(drop=True).copy()
    if centrar:
        df = centrar_cierres(df)
    if mantenimiento:
        df = indicadores_mantenimiento(df)
    predictores = [c for c in df.columns if c not in CLAVES + [CLASE]]
    bloques = [df]
    if rangos:
        bloques.append(pd.DataFrame({f"{v}_rango": rango_mes(df, v) for v in RANGOS}))
    if hist_selectiva:
        r = pd.DataFrame({f"{v}_rango": rango_mes(df, v) for v in HIST_MONTOS})
        base = pd.concat([df[CLAVES + HIST_CONTEOS], r], axis=1)
        bloques.append(historia(base, HIST_CONTEOS + list(r.columns)))
    if hist_amplia:
        bloques.append(historia(df, [c for c in predictores if c not in EXCLUIR_HIST_AMPLIA]))
    if nuevas:
        bloques.append(nuevas_variables(df))
    if hist_1y2_todas:
        bloques.append(historia(df, predictores, ordenes=(1, 2)))
    return pd.concat(bloques, axis=1)


# [Anotación · líneas 150–151] `predictores_de()`: devuelve las columnas del panel que no son claves ni clase.
def predictores_de(panel):
    return [c for c in panel.columns if c not in CLAVES + [CLASE]]
```

### 06_receta_denicolay.py

Entrena el modelo D: 20 LightGBM (uno por semilla) con 202103–202106, clase BAJA+1 o BAJA+2 contra CONTINUA y lags y deltas de orden 1 y 2 de todos los predictores; predice 202108, promedia las probabilidades y escribe `d06dn11500.csv` con los 11.500 clientes de mayor promedio.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–22] Docstring. Describe el archivo D: variables (datos de D01 más lag y delta de orden
#   1 y 2 de todos los predictores), clase (BAJA+1 y BAJA+2 contra CONTINUA), hiperparámetros, 20 semillas,
#   entrenamiento con 202103–202106 y salida con los 11.500 clientes de mayor promedio.
# -*- coding: utf-8 -*-
"""Competencia 1: el archivo D, la receta de Denicolay sobre la historia completa (decisión D06, 7-oct-2026).

- **Variables:** C0, los datos de D01 sin transformaciones, más *lag* 1, delta 1, *lag* 2 y delta 2 de todos los
  predictores (`construir(df, hist_1y2_todas=True)` de `02_variables.py`). La historia se arma sobre el panel completo
  antes de filtrar meses, así que julio aporta los *lags* de agosto. Quedan 735 columnas útiles.
- **Clase K2:** BAJA+1 y BAJA+2 contra CONTINUA. La ganancia cuenta sólo BAJA+2.
- **Receta,** la de la prueba 38 de la búsqueda de D04, sobre la receta de Denicolay:
  - `learning_rate` 0,005, `max_bin` 31, `min_data_in_leaf` 0, `feature_fraction` 0,5, `feature_fraction_bynode`
    0,2, sin *bagging*;
  - 83 hojas, 1.000 rondas y `min_sum_hessian_in_leaf` = 12,791817… × filas de entrenamiento / 326.184;
  - `deterministic`, `force_col_wise` y 12 hilos;
  - el `Dataset` se construye una vez, con `max_bin` 31 y `feature_pre_filter` False, y se reutiliza entre semillas.
- **Entrenamiento:** 202103–202106, con las 20 semillas de `03_envios_tablero.py`; predice 202108.
- **Archivo:** los 11.500 clientes con mayor promedio de las 20 probabilidades, con desempate estable y el formato del
  envío (`escribir_csv`: un entero por línea, sin encabezado, ASCII con CRLF).

Uso: `python 06_receta_denicolay.py`. Tarda unos 40 minutos, casi todos en entrenar.

Salidas en `envios/d06d/`: las 20 probabilidades, `claves_202108.npy`, `columnas.json`, `d06dn11500.csv` y
`manifiesto.json`.
"""
# [Anotación · líneas 23–37] Importa lightgbm, numpy y pandas y carga `03_envios_tablero.py` como módulo `tb`;
#   `var` es el módulo `02_variables.py` ya cargado por `tb`.
import importlib.util
import json
import platform
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("tablero", AQUI / "03_envios_tablero.py")
tb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tb)
var = tb.var

# [Anotación · líneas 39–45] Constantes: nombre de la carpeta de salida (`d06d`), N = 11.500, clases positivas
#   (BAJA+1 y BAJA+2), los hiperparámetros fijos `FIJOS` (learning_rate 0,005, max_bin 31, min_data_in_leaf 0,
#   feature_fraction 0,5, feature_fraction_bynode 0,2, sin bagging, 12 hilos, deterministic y force_col_wise) y
#   83 hojas, hessiano de referencia 12,791817301585011, 326.184 filas de referencia y 1.000 rondas.
NOMBRE = "d06d"
N = 11_500
POSITIVAS = ["BAJA+1", "BAJA+2"]
FIJOS = dict(objective="binary", learning_rate=0.005, max_bin=31, min_data_in_leaf=0, feature_fraction=0.5,
             feature_fraction_bynode=0.2, bagging_fraction=1.0, bagging_freq=0, feature_pre_filter=False,
             verbosity=-1, num_threads=12, deterministic=True, force_col_wise=True)
HOJAS, H_REF, FILAS_REF, RONDAS = 83, 12.791817301585011, 326_184, 1000


# [Anotación · líneas 48–61] `main()`: termina si `envios/d06d/manifiesto.json` ya existe; lee el parquet,
#   construye el panel con `hist_1y2_todas=True` sobre los seis meses y después se queda con 202103–202106 y
#   202108. Exige que el entrenamiento tenga las tres clases y que 202108 no tenga ninguna.
def main():
    carpeta = tb.SALIDA / NOMBRE
    if (carpeta / "manifiesto.json").exists():
        raise SystemExit(f"{NOMBRE} ya existe; no se sobrescribe")
    carpeta.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    panel = var.construir(pd.read_parquet(tb.DATOS), hist_1y2_todas=True)
    panel = panel[panel.foto_mes.isin(tb.MESES_TRAIN + [tb.MES_PREDICCION])].reset_index(drop=True)
    predictores = var.predictores_de(panel)
    en_train = panel.foto_mes.isin(tb.MESES_TRAIN).to_numpy()
    en_pred = (panel.foto_mes == tb.MES_PREDICCION).to_numpy()
    clase = panel[var.CLASE].to_numpy(dtype=object)
    if set(clase[en_train]) != {"BAJA+1", "BAJA+2", "CONTINUA"} or pd.notna(clase[en_pred]).any():
        raise RuntimeError("clases inesperadas: 202103–202106 deben tener las tres y 202108 ninguna")
# [Anotación · líneas 62–73] Pasa los predictores a float32, conserva las columnas con al menos 2 valores
#   distintos (contando NA) en las filas de entrenamiento, arma las matrices de entrenamiento y de 202108 y la
#   etiqueta (1 si la clase es BAJA+1 o BAJA+2). Exige que los clientes de 202108 sean únicos y estén en orden
#   creciente, y guarda `claves_202108.npy` y `columnas.json`.
    X = panel[predictores].astype("float32")
    cols = [c for c in predictores if X.loc[en_train, c].nunique(dropna=False) >= 2]
    X_train = np.ascontiguousarray(X.loc[en_train, cols].to_numpy())
    X_pred = np.ascontiguousarray(X.loc[en_pred, cols].to_numpy())
    y = np.isin(clase[en_train], POSITIVAS).astype("int8")
    claves = panel.loc[en_pred, "numero_de_cliente"].to_numpy(dtype="int64")
    if len(np.unique(claves)) != len(claves) or not (np.diff(claves) > 0).all():
        raise RuntimeError("las claves de 202108 deben ser únicas y estar ordenadas")
    np.save(carpeta / "claves_202108.npy", claves)
    (carpeta / "columnas.json").write_text(json.dumps(cols), encoding="utf-8")
    print(f"{NOMBRE}: {len(cols)} columnas, {len(y)} filas, {int(y.sum())} positivos, {len(claves)} clientes de agosto "
          f"({time.time() - t0:.0f} s)", flush=True)
# [Anotación · líneas 74–77] Construye una sola vez el `Dataset` de LightGBM con `max_bin` 31 y
#   `feature_pre_filter` False, y completa los parámetros con 83 hojas y `min_sum_hessian_in_leaf` = 12,7918 ×
#   filas de entrenamiento / 326.184.
    ds = lgb.Dataset(X_train, label=y, params={"max_bin": FIJOS["max_bin"], "feature_pre_filter": False, "verbosity": -1},
                     free_raw_data=False)
    ds.construct()
    params = {**FIJOS, "num_leaves": HOJAS, "min_sum_hessian_in_leaf": H_REF * len(y) / FILAS_REF}
# [Anotación · líneas 78–86] Para cada una de las 20 semillas entrena un modelo de 1.000 rondas sobre el mismo
#   `Dataset`, predice 202108, verifica que la predicción tenga el tamaño esperado y valores finitos, y guarda
#   `probabilidades_<semilla>.npy`.
    probs = []
    for s in tb.semillas():
        t1 = time.time()
        p = lgb.train({**params, "seed": s}, ds, num_boost_round=RONDAS).predict(X_pred)
        if p.shape != (len(claves),) or not np.isfinite(p).all():
            raise RuntimeError(f"semilla {s}: predicción inválida")
        np.save(carpeta / f"probabilidades_{s}.npy", p.astype("float64"))
        probs.append(p)
        print(f"  semilla {s}: {time.time() - t1:.0f} s", flush=True)
# [Anotación · líneas 87–93] Promedia las 20 probabilidades, ordena de mayor a menor con `argsort` estable,
#   toma los primeros 11.500 clientes, escribe `d06dn11500.csv` y verifica que tenga 11.500 identificadores
#   distintos de 202108.
    prom = np.mean(probs, axis=0)
    elegidos = claves[np.argsort(-prom, kind="stable")[:N]]
    csv = carpeta / f"{NOMBRE}n{N}.csv"
    tb.escribir_csv(csv, elegidos)
    ids = [int(x) for x in csv.read_text(encoding="ascii").split()]
    if len(ids) != N or len(set(ids)) != N or not set(ids) <= set(claves.tolist()):
        raise RuntimeError(f"{csv.name}: control fallido")
# [Anotación · líneas 94–104] Escribe `manifiesto.json` con parámetros, rondas, semillas, cantidad de columnas
#   y de filas, huellas SHA-256 de los datos y de los scripts, versiones de Python y LightGBM y la huella del
#   CSV.
    manifiesto = {"envio": NOMBRE, "descripcion": "D: C0 + lags y deltas 1 y 2 de todo, receta de la prueba 38, K2",
                  "positivas": POSITIVAS, "meses_train": tb.MESES_TRAIN, "mes_prediccion": tb.MES_PREDICCION,
                  "params": params, "rondas": RONDAS, "semillas": tb.semillas(), "columnas": len(cols),
                  "filas_train": int(len(y)), "n_por_archivo": N,
                  "huellas": {"datos": tb.huella(tb.DATOS), "02_variables.py": tb.huella(AQUI / "02_variables.py"),
                              "03_envios_tablero.py": tb.huella(AQUI / "03_envios_tablero.py"),
                              "06_receta_denicolay.py": tb.huella(__file__)},
                  "versiones": {"python": platform.python_version(), "lightgbm": lgb.__version__},
                  "archivos": [{"archivo": csv.name, "filas": N, "sha256": tb.huella(csv)}]}
    (carpeta / "manifiesto.json").write_text(json.dumps(manifiesto, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{NOMBRE}: {csv.name}, {N} clientes; {time.time() - t0:.0f} s")


# [Anotación · líneas 107–108] Punto de entrada: ejecuta `main()` cuando el archivo se corre como script.
if __name__ == "__main__":
    main()
```

### 03_envios_tablero.py

`06_receta_denicolay.py` y `07_archivo_d10.py` lo cargan como módulo y usan sus rutas, los meses de entrenamiento y de predicción, `semillas()`, `escribir_csv()` y `huella()`. Como script arma tres envíos de prueba con clase BAJA+2 contra el resto, que `reproducir.py` no corre.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–26] Docstring. Describe el uso del archivo como script: tres envíos de prueba al
#   tablero (`d02c0`, `d02c7`, `d02l12`) con 20 modelos cada uno, clase BAJA+2 contra el resto y N = 11.000.
# -*- coding: utf-8 -*-
"""Competencia 1: arma los tres envíos al tablero público. Sólo los prepara; no envía nada.

Los aprobó el usuario el 5-oct-2026. Cada envío tiene 20 modelos LightGBM, uno por semilla, entrenados con
202103–202106 (BAJA+2 contra el resto), que predicen 202108. Cada archivo tiene los N clientes con mayor
probabilidad, un `numero_de_cliente` entero por línea y sin encabezado, como pide el bot
(github.com/alejandro-bolanos/zulip-competition-bot).

| Envío | Variables |
|---|---|
| `d02c0` | C0, la decisión de D02 |
| `d02c7` | C0 + historia selectiva |
| `d02l12` | C0 + *lags* y deltas de orden 1 y 2 de todas las variables, la receta de Denicolay |

- **Semillas:** las cinco del usuario (CheckIn #182829) y, de cada una, los tres primos siguientes: 20 primos.
- **Hiperparámetros:** los mismos fijos de las pruebas de D02. Todavía no están optimizados; eso es D04.
- **Cantidad de clientes:** N = 11.000 en todos los archivos, de forma provisoria hasta D03. El bot devuelve
  una sola media por envío, así que la cantidad tiene que ser la misma en todos.

Uso: `python 03_envios_tablero.py [envio ...]`

Salidas en `envios/<envio>/`:
- los 20 CSV;
- `probabilidades_<semilla>.npy` y `claves_202108.npy`, para el ensamble final;
- `manifiesto.json`, con huellas, parámetros, semillas y controles de cada archivo.
"""
# [Anotación · líneas 27–43] Importa lightgbm, numpy y pandas y carga `02_variables.py` como módulo `var`
#   mediante `importlib.util`.
import hashlib
import importlib.util
import json
import platform
import re
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("variables", AQUI / "02_variables.py")
var = importlib.util.module_from_spec(spec)
spec.loader.exec_module(var)

# [Anotación · líneas 45–55] Constantes: ruta del parquet y de `envios/`, meses de entrenamiento
#   202103–202106, mes de predicción 202108, N = 11.000, las cinco semillas iniciales, los hiperparámetros
#   `PARAMS` (learning_rate 0,05, 63 hojas, min_data_in_leaf 200, feature_fraction 0,5, bagging 0,8 con
#   frecuencia 1) con 500 rondas, y las opciones de variables de los tres envíos. `06_receta_denicolay.py` toma
#   de acá las rutas y los meses, pero no `PARAMS` ni `RONDAS`.
DATOS = AQUI / "datos" / "competencia_01_d01.parquet"
SALIDA = AQUI / "envios"
MESES_TRAIN = [202103, 202104, 202105, 202106]
MES_PREDICCION = 202108
N_ENVIO = 11_000
SEMILLAS_USUARIO = [147347, 322607, 462467, 782149, 983809]
PARAMS = dict(objective="binary", learning_rate=0.05, num_leaves=63, min_data_in_leaf=200, feature_fraction=0.5,
              bagging_fraction=0.8, bagging_freq=1, verbosity=-1, num_threads=12, deterministic=True,
              force_col_wise=True)
RONDAS = 500
ENVIOS = {"d02c0": dict(), "d02c7": dict(hist_selectiva=True), "d02l12": dict(hist_1y2_todas=True)}


# [Anotación · líneas 58–74] `es_primo()` y `semillas()`: a cada una de las cinco semillas iniciales le agrega
#   los tres primos siguientes, lo que da 20 semillas; verifica que sean 20 distintas y todas primas.
def es_primo(n):
    return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))


def semillas():
    """Las cinco del usuario y los tres primos siguientes a cada una."""
    out = []
    for p in SEMILLAS_USUARIO:
        out.append(p)
        q = p
        for _ in range(3):
            q += 1
            while not es_primo(q):
                q += 1
            out.append(q)
    assert len(set(out)) == 20 and all(es_primo(s) for s in out)
    return out


# [Anotación · líneas 77–88] `huella()` devuelve el SHA-256 de un archivo. `escribir_csv()` escribe un
#   identificador entero por línea, sin encabezado, en ASCII y con saltos CRLF, relee el archivo y lanza un
#   error si la cantidad de líneas no coincide o alguna no es sólo dígitos.
def huella(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def escribir_csv(path, ids):
    """Un entero por línea, sin encabezado; se verifica el texto escrito."""
    ids = np.asarray(ids, dtype="int64")
    # Saltos de línea CRLF explícitos: así se escribió el archivo enviado (en Windows) y la huella no depende del sistema.
    path.write_text("\n".join(str(int(i)) for i in ids) + "\n", encoding="ascii", newline="\r\n")
    lineas = path.read_text(encoding="ascii").splitlines()
    if len(lineas) != len(ids) or not all(re.fullmatch(r"[0-9]+", l) for l in lineas):
        raise RuntimeError(f"{path.name}: formato inválido")


# [Anotación · líneas 91–110] `armar()`, que se usa sólo cuando el archivo corre como script: construye el
#   panel con las opciones del envío, filtra los meses de entrenamiento y 202108, descarta las columnas con
#   menos de 2 valores distintos en entrenamiento, arma las matrices y la etiqueta (1 = BAJA+2) y guarda las
#   claves de 202108.
def armar(nombre, base):
    carpeta = SALIDA / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    panel = var.construir(base, **ENVIOS[nombre])
    panel = panel[panel.foto_mes.isin(MESES_TRAIN + [MES_PREDICCION])].reset_index(drop=True)
    predictores = var.predictores_de(panel)
    en_train = panel.foto_mes.isin(MESES_TRAIN).to_numpy()
    en_pred = (panel.foto_mes == MES_PREDICCION).to_numpy()
    X = panel[predictores].astype("float32")
    cols = [c for c in predictores if X.loc[en_train, c].nunique(dropna=False) >= 2]
    X_train = np.ascontiguousarray(X.loc[en_train, cols].to_numpy())
    X_pred = np.ascontiguousarray(X.loc[en_pred, cols].to_numpy())
    y = (panel.loc[en_train, var.CLASE] == "BAJA+2").to_numpy(dtype="int8")
    claves = panel.loc[en_pred, "numero_de_cliente"].to_numpy(dtype="int64")
    if len(np.unique(claves)) != len(claves) or (panel.loc[en_pred, var.CLASE].notna().any()):
        raise RuntimeError("202108 debe tener clientes únicos y sin clase")
    np.save(carpeta / "claves_202108.npy", claves)
    print(f"{nombre}: {len(cols)} predictores útiles de {len(predictores)}, {en_train.sum()} filas de entrenamiento, "
          f"{len(claves)} clientes de agosto ({time.time() - t0:.0f} s)", flush=True)
# [Anotación · líneas 111–122] Para cada una de las 20 semillas entrena un LightGBM con `PARAMS` y 500 rondas,
#   guarda las probabilidades de 202108 y escribe un CSV con los 11.000 clientes de mayor probabilidad de esa
#   semilla.
    archivos = []
    for s in semillas():
        t1 = time.time()
        modelo = lgb.train({**PARAMS, "seed": s}, lgb.Dataset(X_train, label=y), num_boost_round=RONDAS)
        p = modelo.predict(X_pred)
        np.save(carpeta / f"probabilidades_{s}.npy", p.astype("float64"))
        elegidos = claves[np.argsort(-p, kind="stable")[:N_ENVIO]]
        csv = carpeta / f"{nombre}s{s}.csv"
        escribir_csv(csv, elegidos)
        archivos.append({"archivo": csv.name, "semilla": s, "filas": int(len(elegidos)), "sha256": huella(csv),
                         "prob_corte": float(np.sort(p)[::-1][N_ENVIO - 1])})
        print(f"  semilla {s}: {time.time() - t1:.0f} s, probabilidad en el corte {archivos[-1]['prob_corte']:.4f}", flush=True)
# [Anotación · líneas 123–138] Verifica que cada CSV tenga 11.000 identificadores distintos y pertenecientes a
#   202108, y escribe `manifiesto.json` (parámetros, semillas, huellas, versiones) y `columnas.json`.
    # Controles del conjunto
    agosto = set(claves.tolist())
    for a in archivos:
        ids = [int(l) for l in (carpeta / a["archivo"]).read_text(encoding="ascii").split()]
        if len(ids) != N_ENVIO or len(set(ids)) != N_ENVIO or not set(ids) <= agosto:
            raise RuntimeError(f"{a['archivo']}: control fallido")
    manifiesto = {"envio": nombre, "opciones_construir": ENVIOS[nombre], "meses_train": MESES_TRAIN,
                  "mes_prediccion": MES_PREDICCION, "n_por_archivo": N_ENVIO, "params": PARAMS, "rondas": RONDAS,
                  "predictores_utiles": len(cols), "semillas": semillas(),
                  "huellas": {"datos": huella(DATOS), "02_variables.py": huella(AQUI / "02_variables.py"),
                              "03_envios_tablero.py": huella(__file__)},
                  "versiones": {"python": platform.python_version(), "lightgbm": lgb.__version__},
                  "archivos": archivos}
    (carpeta / "manifiesto.json").write_text(json.dumps(manifiesto, indent=1), encoding="utf-8")
    (carpeta / "columnas.json").write_text(json.dumps(cols), encoding="utf-8")
    print(f"{nombre}: listo en {time.time() - t0:.0f} s", flush=True)


# [Anotación · líneas 141–145] Punto de entrada como script: lee el parquet y arma los envíos pedidos por
#   argumento, o los tres.
if __name__ == "__main__":
    elegidos = sys.argv[1:] or list(ENVIOS)
    base = pd.read_parquet(DATOS)
    for nombre in elegidos:
        armar(nombre, base)
```

### origen/d04_busqueda.py

Búsqueda con Optuna de `num_leaves` y del hessiano de referencia, de donde según origen/README.md salen las 83 hojas y h = 12,79 que `06_receta_denicolay.py` tiene fijos. `reproducir.py` no lo ejecuta; el README indica que no hace falta para reproducir el archivo.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–44] Docstring. Describe la búsqueda de la decisión D04: parámetros fijos y libres,
#   datos (variables `BASE`, clase BAJA+1 o BAJA+2), los dos cortes, las rondas evaluadas, el valor de cada
#   prueba, el muestreo TPE y el uso con `--hasta` y `--humo`; indica que no reanuda una búsqueda cortada.
# -*- coding: utf-8 -*-
"""Origen de los hiperparámetros de D, paso 1: la búsqueda bayesiana de la D04 (6 y 7-oct-2026).

Es el script que corrió la búsqueda (`experimentos/d04_busqueda/correr_busqueda.py` de la carpeta de trabajo), con
estos cambios, que no alteran los resultados:
- las rutas: lee `02_variables.py` y `datos/competencia_01_d01.parquet` de este repositorio, y escribe en
  `origen/salidas/`;
- no tiene los límites de tiempo del original (8 horas o el 8-oct a las 06:00). La corrida original terminó las 40
  pruebas antes de llegar a ellos, así que no cambian nada. El de fecha, hoy, cortaría la búsqueda en el acto;
- `--hasta K` corta después de K pruebas completas, en una carpeta propia, para comprobar una parte;
- **no reanuda.** El muestreador de Optuna no guarda el estado de su generador en el estudio: si la búsqueda se corta
  y se reanuda, vuelve a sortear desde la semilla y toma otro camino. La corrida original fue de corrido, así que el
  script exige una carpeta vacía;
- al final compara cada prueba con la corrida original (`origen/esperado/pruebas_d04.csv`).

**Qué busca:**
- **Fijos:** la receta de Denicolay (`learning_rate` 0,005, `max_bin` 31, `min_data_in_leaf` 0,
  `feature_fraction` 0,5, `feature_fraction_bynode` 0,2), sin *bagging*, 12 hilos y `deterministic`.
- **Libres:** `num_leaves` (16–255) y el hessiano de referencia h (0,5–128), en escala logarítmica.
  - `min_sum_hessian_in_leaf` = h · filas de entrenamiento / 326.184.
  - 326.184 son las filas de entrenamiento de F2 (202103–202104). En F2, h es exactamente el mínimo de hessiano por
    hoja; en los demás cortes se escala por sus filas.
- **Datos:** la base C7 (`construir(df, **BASE)`), con la clase K2, en dos cortes:
  - F1: entrena con 202103 y valida en 202105;
  - F2: entrena con 202103–202104 y valida en 202106.
- **Rondas:** cada ajuste llega a 8.000, y se evalúan los prefijos de 1.000, 2.000, 3.000, 5.000 y 8.000.
- **Valor de cada prueba:** el máximo sobre las rondas de A = (A_F1 + A_F2)/2.
  - A_f es la media de G(k) = 1.100.000·TP(k) − 27.500·k sobre los enteros de 8.000 a 15.000.
  - TP cuenta sólo los BAJA+2, con el ranking del promedio de las dos semillas (147347 y 322607).
- **Muestreo:** TPE con semilla 147347: 3 anclas (31, 63 y 255 hojas con h = 8), 9 al azar y 28 adaptativas, hasta
  40 pruebas completas.

Uso, desde la raíz del repositorio y después de `python 01_preparar_datos.py`:
    python origen/d04_busqueda.py            # las 40 pruebas: unas 3 horas (la original tardó 3,0 h)
    python origen/d04_busqueda.py --hasta 4  # las primeras 4 (las 3 anclas y la primera al azar): unos 17 minutos
    python origen/d04_busqueda.py --humo     # prueba de humo en una carpeta temporal, con pocas rondas

Si se corta, hay que borrar su carpeta de salida y empezar de nuevo.

Salidas en `origen/salidas/d04_busqueda/` (o en `d04_busqueda_hasta<K>/`, con `--hasta K`):
- `pruebas.csv`, una fila por prueba;
- `predicciones/`, las probabilidades de cada semilla y corte con las rondas elegidas;
- `manifiesto.json` y el estudio, en `busqueda.db`.
"""
# [Anotación · líneas 45–77] Importa lightgbm, optuna y el módulo `comun`, y define: los hiperparámetros fijos
#   (los mismos de `06_receta_denicolay.py`), los cortes F1 (202103 → 202105) y F2 (202103–202104 → 202106), dos
#   semillas (147347 y 322607), las rondas 1.000, 2.000, 3.000, 5.000 y 8.000, los rangos de `num_leaves`
#   (16–255) y de h (0,5–128), tres anclas (31, 63 y 255 hojas con h = 8), 40 pruebas con 12 iniciales, la
#   semilla del muestreador (147347) y los valores de la ganancia (1.100.000 por acierto y 27.500 por envío).
import datetime as dt
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

import comun

var = comun.var
DATOS = comun.DATOS
SALIDA = comun.SALIDAS / "d04_busqueda"
ESPERADO = comun.ESPERADO / "pruebas_d04.csv"

FIJOS = dict(objective="binary", learning_rate=0.005, max_bin=31, min_data_in_leaf=0, feature_fraction=0.5,
             feature_fraction_bynode=0.2, bagging_fraction=1.0, bagging_freq=0, feature_pre_filter=False,
             verbosity=-1, num_threads=12, deterministic=True, force_col_wise=True)
FILAS_REF = 326_184
CORTES = {"F1": ([202103], 202105), "F2": ([202103, 202104], 202106)}
SEMILLAS = [147347, 322607]
RONDAS = [1000, 2000, 3000, 5000, 8000]
POSITIVAS = ["BAJA+1", "BAJA+2"]
HOJAS = (16, 255)
H_REF = (0.5, 128.0)
ANCLAS = [{"num_leaves": 31, "h_ref": 8.0}, {"num_leaves": 63, "h_ref": 8.0}, {"num_leaves": 255, "h_ref": 8.0}]
N_PRUEBAS, N_INICIALES, SEMILLA_TPE = 40, 12, 147347
GANANCIA_TP, COSTO_ENVIO = 1_100_000, 27_500


# [Anotación · líneas 80–95] `curva_ganancia()` devuelve G(k) = 1.100.000·TP(k) − 27.500·k para cada k,
#   ordenando por probabilidad descendente. `a_rango()` promedia G(k) entre k = 8.000 y k = 15.000 y lo expresa
#   en millones. `auc()` calcula el área bajo la curva ROC a partir de los rangos de las probabilidades.
def curva_ganancia(y, p):
    """G(k) en pesos enteros, k = 1..n, ordenando por probabilidad descendente (empates en orden estable)."""
    orden = np.argsort(-np.asarray(p, dtype="float64"), kind="stable")
    return GANANCIA_TP * np.cumsum(np.asarray(y, dtype="int64")[orden]) - COSTO_ENVIO * np.arange(1, len(y) + 1)


def a_rango(y, p):
    """A en millones: media de G(k) sobre los 7.001 enteros k = 8.000..15.000."""
    return float(curva_ganancia(y, p)[7999:15000].mean()) / 1e6


def auc(y, p):
    y = np.asarray(y)
    r = pd.Series(np.asarray(p, dtype="float64")).rank(method="average").to_numpy()
    npos = y.sum()
    return float((r[y == 1].sum() - npos * (npos + 1) / 2) / (npos * (len(y) - npos)))


# [Anotación · líneas 98–109] `prefijos()` obtiene, de un modelo entrenado hasta el máximo de rondas, las
#   probabilidades con los primeros T árboles para cada T de la lista, acumulando los puntajes crudos por tramos
#   y aplicando la función logística. `huella()` devuelve el SHA-256 de un archivo.
def prefijos(modelo, X, rondas):
    """Probabilidades con los primeros T árboles, para cada T de `rondas`, sumando los puntajes crudos por bloques."""
    crudo, previo, salida = np.zeros(X.shape[0]), 0, {}
    for t in rondas:
        crudo = crudo + modelo.predict(X, start_iteration=previo, num_iteration=t - previo, raw_score=True)
        previo = t
        salida[t] = 1.0 / (1.0 + np.exp(-crudo))
    return salida


def huella(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# [Anotación · líneas 112–135] `preparar()`: construye el panel con `BASE`, se queda con 202103–202106 y, para
#   cada corte, arma el `Dataset` de entrenamiento (etiqueta 1 = BAJA+1 o BAJA+2, columnas con al menos 2
#   valores distintos en entrenamiento, `max_bin` 31) y la matriz de validación con su etiqueta (1 = BAJA+2), su
#   clase y sus claves.
def preparar():
    """Matrices de entrenamiento y validación de cada corte, con las columnas útiles de su entrenamiento."""
    comun.exigir_datos()
    panel = var.construir(pd.read_parquet(DATOS), **var.BASE)
    panel = panel[panel.foto_mes.between(202103, 202106)].reset_index(drop=True)
    predictores = var.predictores_de(panel)
    X = panel[predictores].astype("float32")
    clase = panel[var.CLASE].to_numpy(dtype="U8")
    if set(np.unique(clase)) != {"BAJA+1", "BAJA+2", "CONTINUA"}:
        raise SystemExit("clases inesperadas en 202103–202106")
    datos = {}
    for corte, (meses, mes_val) in CORTES.items():
        en_train, en_val = panel.foto_mes.isin(meses).to_numpy(), (panel.foto_mes == mes_val).to_numpy()
        cols = [c for c in predictores if X.loc[en_train, c].nunique(dropna=False) >= 2]
        y_train = np.isin(clase[en_train], POSITIVAS).astype("int8")
        ds = lgb.Dataset(np.ascontiguousarray(X.loc[en_train, cols].to_numpy()), label=y_train,
                         params={"max_bin": FIJOS["max_bin"], "feature_pre_filter": False, "verbosity": -1},
                         free_raw_data=False)
        ds.construct()
        datos[corte] = {"ds": ds, "X_val": np.ascontiguousarray(X.loc[en_val, cols].to_numpy()),
                        "y_val": (clase[en_val] == "BAJA+2").astype("int8"), "clase_val": clase[en_val],
                        "claves_val": panel.loc[en_val, "numero_de_cliente"].to_numpy(dtype="int64"),
                        "filas": int(en_train.sum()), "columnas": cols}
    return datos


# [Anotación · líneas 138–169] `evaluar()`: para cada corte y cada semilla entrena hasta 8.000 rondas con las
#   hojas y el hessiano de la prueba (h × filas del corte / 326.184) y obtiene las probabilidades de validación
#   en cada cantidad de rondas. Calcula A por ronda con el promedio de las dos semillas, como media de los dos
#   cortes, y toma la ronda de mayor A (en un empate, la de menos rondas). Devuelve A, A por corte y por semilla
#   y el AUC, y guarda las probabilidades de la ronda tomada.
def evaluar(datos, hojas, h_ref, rondas, salida=None, numero=None):
    """Entrena las semillas en los dos cortes y devuelve A por ronda, la ronda elegida y los detalles."""
    probs = {c: {s: None for s in SEMILLAS} for c in CORTES}
    segundos = 0.0
    for corte, d in datos.items():
        params = {**FIJOS, "num_leaves": int(hojas), "min_sum_hessian_in_leaf": h_ref * d["filas"] / FILAS_REF}
        for s in SEMILLAS:
            t0 = time.time()
            modelo = lgb.train({**params, "seed": s}, d["ds"], num_boost_round=rondas[-1])
            probs[corte][s] = prefijos(modelo, d["X_val"], rondas)
            segundos += time.time() - t0
    a_por_ronda = {}
    for t in rondas:
        a_f = {c: a_rango(datos[c]["y_val"], np.mean([probs[c][s][t] for s in SEMILLAS], axis=0)) for c in CORTES}
        a_por_ronda[t] = (a_f, float(np.mean(list(a_f.values()))))
    mejor_t = max(rondas, key=lambda t: (a_por_ronda[t][1], -t))       # ante un empate exacto, menos rondas
    detalle = {"rondas": mejor_t, "A": a_por_ronda[mejor_t][1], "segundos": round(segundos, 1)}
    for c in CORTES:
        detalle[f"A_{c}"] = a_por_ronda[mejor_t][0][c]
        detalle[f"auc_{c}"] = auc(datos[c]["y_val"], np.mean([probs[c][s][mejor_t] for s in SEMILLAS], axis=0))
        for s in SEMILLAS:
            detalle[f"A_{c}_{s}"] = a_rango(datos[c]["y_val"], probs[c][s][mejor_t])
    for t in rondas:
        detalle[f"A_r{t}"] = a_por_ronda[t][1]
    if salida is not None:
        for c in CORTES:
            for s in SEMILLAS:
                destino = salida / f"p{numero:03d}_{c}_{s}.npy"
                temporal = destino.with_suffix(".tmp.npy")
                np.save(temporal, probs[c][s][mejor_t].astype("float64"), allow_pickle=False)
                temporal.replace(destino)
    return detalle


# [Anotación · líneas 172–179] `manifiesto_actual()`: huellas SHA-256 de los datos, de `02_variables.py`, del
#   script y de la configuración, y versiones de lightgbm, optuna y numpy.
def manifiesto_actual(rondas):
    config = {"fijos": FIJOS, "filas_ref": FILAS_REF, "cortes": CORTES, "semillas": SEMILLAS, "rondas": rondas,
              "positivas": POSITIVAS, "hojas": HOJAS, "h_ref": H_REF, "anclas": ANCLAS, "n_pruebas": N_PRUEBAS,
              "n_iniciales": N_INICIALES, "semilla_tpe": SEMILLA_TPE, "base": var.BASE}
    return {"datos_sha256": huella(DATOS), "variables_py_sha256": huella(comun.RAIZ / "02_variables.py"),
            "script_sha256": huella(__file__),
            "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
            "lightgbm": lgb.__version__, "optuna": optuna.__version__, "numpy": np.__version__}


# [Anotación · líneas 182–215] `correr()`: termina si la carpeta ya tiene una búsqueda, escribe o verifica el
#   manifiesto, prepara los datos y guarda la etiqueta, la clase y las claves de validación de cada corte. Crea
#   el muestreador `TPESampler` (semilla 147347, 12 pruebas iniciales) y un estudio de Optuna que maximiza,
#   guardado en SQLite, y encola las tres anclas.
def correr(carpeta, rondas, n_pruebas, nueva=True):
    """`nueva`: exige una carpeta sin estudio, porque reanudar cambia el sorteo de Optuna."""
    if nueva and ((carpeta / "busqueda.db").exists() or (carpeta / "pruebas.csv").exists()):
        raise SystemExit(f"{carpeta} ya tiene una búsqueda. Reanudarla no reproduce la original, porque el muestreador "
                         "vuelve a sortear desde la semilla: borrar la carpeta y correr de nuevo, de corrido")
    carpeta.mkdir(parents=True, exist_ok=True)
    pred = carpeta / "predicciones"
    pred.mkdir(exist_ok=True)
    manifiesto = carpeta / "manifiesto.json"
    actual = manifiesto_actual(rondas)
    if manifiesto.exists():
        previo = json.loads(manifiesto.read_text(encoding="utf-8"))
        if any(previo.get(k) != v for k, v in actual.items()):
            raise SystemExit("la búsqueda cambió desde que empezó: usar una carpeta nueva")
    else:
        manifiesto.write_text(json.dumps(actual, indent=1), encoding="utf-8")
    t0 = time.time()
    datos = preparar()
    for c, d in datos.items():
        for nombre in ("y_val", "clase_val", "claves_val"):
            destino = pred / f"{nombre.split('_')[0]}_{c}.npy"
            if destino.exists():
                if not np.array_equal(np.load(destino, allow_pickle=False), d[nombre]):
                    raise SystemExit(f"{destino.name} no coincide")
            else:
                np.save(destino, d[nombre], allow_pickle=False)
    print(f"datos listos en {time.time() - t0:.0f} s: " +
          ", ".join(f"{c} {d['filas']} filas y {len(d['columnas'])} columnas" for c, d in datos.items()), flush=True)
    sampler = optuna.samplers.TPESampler(seed=SEMILLA_TPE, n_startup_trials=N_INICIALES)
    estudio = optuna.create_study(study_name="d04", storage=f"sqlite:///{(carpeta / 'busqueda.db').as_posix()}",
                                  direction="maximize", sampler=sampler, load_if_exists=True)
    if len(estudio.trials) == 0:
        for ancla in ANCLAS:
            estudio.enqueue_trial(ancla)

# [Anotación · líneas 217–229] `objetivo()`: pide a Optuna `num_leaves` y `h_ref` en escala logarítmica, llama
#   a `evaluar()`, guarda el detalle como atributos de la prueba, agrega una fila a `pruebas.csv` y devuelve A.
    def objetivo(trial):
        hojas = trial.suggest_int("num_leaves", HOJAS[0], HOJAS[1], log=True)
        h_ref = trial.suggest_float("h_ref", H_REF[0], H_REF[1], log=True)
        detalle = evaluar(datos, hojas, h_ref, rondas, salida=pred, numero=trial.number)
        for k, v in detalle.items():
            trial.set_user_attr(k, v)
        fila = {"prueba": trial.number, "num_leaves": hojas, "h_ref": h_ref, **detalle,
                "fin": dt.datetime.now().isoformat(timespec="seconds")}
        archivo = carpeta / "pruebas.csv"
        pd.DataFrame([fila]).to_csv(archivo, mode="a", header=not archivo.exists(), index=False)
        print(f"prueba {trial.number}: hojas {hojas}, h {h_ref:.3g}, rondas {detalle['rondas']}, A {detalle['A']:.2f} M "
              f"(F1 {detalle['A_F1']:.2f}, F2 {detalle['A_F2']:.2f}), {detalle['segundos']:.0f} s", flush=True)
        return detalle["A"]

# [Anotación · líneas 231–239] Ejecuta pruebas de a una hasta completar la cantidad pedida e imprime la prueba
#   de mayor A del estudio.
    while True:
        completas = [t for t in estudio.trials if t.state == optuna.trial.TrialState.COMPLETE]
        if len(completas) >= n_pruebas:
            print(f"fin: {len(completas)} pruebas completas", flush=True)
            break
        estudio.optimize(objetivo, n_trials=1, catch=())
    mejor = estudio.best_trial
    print(f"mejor hasta acá: prueba {mejor.number}, {mejor.params}, rondas {mejor.user_attrs['rondas']}, "
          f"A {mejor.value:.2f} M", flush=True)


# [Anotación · líneas 242–253] `comparar_con_original()`: compara cada prueba con la misma prueba de
#   `origen/esperado/pruebas_d04.csv`: hojas y rondas iguales, h con tolerancia 1e-12 y A, A_F1 y A_F2 con
#   tolerancia 1e-9.
def comparar_con_original(carpeta):
    """Cada prueba corrida contra la misma prueba de la corrida original: las hojas, h, las rondas y A."""
    obtenidas = pd.read_csv(carpeta / "pruebas.csv").drop_duplicates("prueba", keep="last").set_index("prueba")
    originales = pd.read_csv(ESPERADO).set_index("prueba").loc[obtenidas.index]
    print(f"\nComparación con la corrida original ({len(obtenidas)} pruebas):")
    ok = (obtenidas.num_leaves == originales.num_leaves).all() and (obtenidas.rondas == originales.rondas).all()
    print(f"  hojas y rondas: {'iguales' if ok else 'DISTINTAS'}")
    ok &= comun.comparar("h", obtenidas.h_ref, originales.h_ref, 1e-12)
    for col in ("A", "A_F1", "A_F2"):
        ok &= comun.comparar(col, obtenidas[col], originales[col], 1e-9)
    print("→ " + ("reproduce la búsqueda original" if ok else "NO reproduce la búsqueda original"))
    return ok


# [Anotación · líneas 256–268] Punto de entrada: con `--humo` corre 4 pruebas con rondas 10 y 20 en una
#   carpeta temporal; si no, corre hasta 40 pruebas (o las que indique `--hasta`, en otra carpeta), compara con
#   la corrida original y sale con código 1 si no coincide.
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    if "--humo" in sys.argv[1:]:
        d = Path(tempfile.mkdtemp())          # en Windows, SQLite mantiene abierto el estudio hasta salir
        correr(d, rondas=[10, 20], n_pruebas=4)
        print(pd.read_csv(d / "pruebas.csv")[["prueba", "num_leaves", "h_ref", "rondas", "A", "A_r10", "A_r20"]])
    else:
        hasta = int(sys.argv[sys.argv.index("--hasta") + 1]) if "--hasta" in sys.argv else N_PRUEBAS
        carpeta = SALIDA if hasta >= N_PRUEBAS else comun.SALIDAS / f"d04_busqueda_hasta{hasta}"
        correr(carpeta, RONDAS, min(hasta, N_PRUEBAS))
        if not comparar_con_original(carpeta):
            raise SystemExit(1)
```

### origen/d04_seleccion.py

Compara, con 5 semillas y en los cortes F1 y F2, las 5 pruebas de mayor A de la búsqueda contra la configuración anterior. Según su docstring, de acá sale la prueba 38 (83 hojas, h = 12,791817301585011). `reproducir.py` no lo ejecuta.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–32] Docstring. Describe la selección de la decisión D04: las 5 pruebas de mayor A de
#   la búsqueda, evaluadas con 5 semillas en F1 y F2 contra la configuración anterior (learning_rate 0,05, 63
#   hojas, 500 rondas), la regla de comparación y el control contra la tabla original. Indica que ninguna
#   finalista cumplió la regla y que la prueba 38 tuvo el mayor ΔA (+6,19 M).
# -*- coding: utf-8 -*-
"""Origen de los hiperparámetros de D, paso 2: la selección de la D04 con 5 semillas (7-oct-2026).

Es la etapa `seleccion` de `experimentos/d04_busqueda/correr_etapas.py` de la carpeta de trabajo, adaptada a este
repositorio. De acá sale la prueba 38: 83 hojas y h = 12,791817301585011.

**Qué hace:**
1. **Las finalistas:** las 5 pruebas de mayor A de la búsqueda, sin repetir hojas y h. En un empate, menos rondas ×
   hojas, después menos rondas y después el número de prueba.
   - Las toma de `origen/salidas/d04_busqueda/pruebas.csv` si la búsqueda está completa (40 pruebas).
   - Si no, de la corrida original, `origen/esperado/pruebas_d04.csv`.
2. **Cada finalista, con las 5 semillas del usuario,** en F1 y F2, con sus rondas (las 5 eligieron 1.000).
   - Con finalistas de la búsqueda propia, para las semillas 147347 y 322607 usa sus predicciones, como el original.
   - Con las de la corrida original, entrena las 5: las predicciones de una búsqueda propia podrían ser de otras
     pruebas.
3. **La referencia, «la K2 actual»:** la configuración vigente de la D03, con las mismas 5 semillas y en los mismos
   cortes.
   - `learning_rate` 0,05, 63 hojas, `min_data_in_leaf` 200, `feature_fraction` 0,5 y *bagging* 0,8 con
     frecuencia 1;
   - 500 rondas;
   - un `Dataset` por semilla, sin parámetros propios, como en `experimentos/d03_clase/correr.py`.
4. **La comparación:** ΔA del ensamble por corte, la diferencia media por semilla y cuántas semillas mejoran.
   - La regla de la D04 exigía ΔA ≥ 10 M, mejorar F1 y F2, y 4 de 5 semillas en cada corte.
   - **Ninguna finalista la cumplió.** La prueba 38 fue la de mayor ΔA (+6,19 M) y la que se llevó a D en la D06.
5. **El control:** compara la tabla con la original (`origen/esperado/seleccion_d04.csv`).

Uso, desde la raíz y después de `python 01_preparar_datos.py`: `python origen/d04_seleccion.py`. Sin la búsqueda
completa, entrena 50 modelos de las finalistas y 10 de la referencia: unos 10 minutos (la original, que reutilizó 20
predicciones de la búsqueda, tardó 5).

Salidas en `origen/salidas/d04_seleccion/`: `seleccion.csv` y las predicciones.
"""
# [Anotación · líneas 33–52] Importa `comun` y `d04_busqueda` (como `bq`) y define carpetas, las cinco
#   semillas (147347, 322607, 462467, 782149, 983809), 5 finalistas, el margen de A (10) y los parámetros y las
#   500 rondas de la configuración de referencia.
import sys
import time

import lightgbm as lgb
import numpy as np
import pandas as pd

import comun
import d04_busqueda as bq

SALIDA = comun.SALIDAS / "d04_seleccion"
PRED_BUSQUEDA = bq.SALIDA / "predicciones"
ESPERADO = comun.ESPERADO / "seleccion_d04.csv"
SEMILLAS_5 = [147347, 322607, 462467, 782149, 983809]
N_FINALISTAS, MARGEN_A = 5, 10.0
# la «K2 actual» de la D03 (experimentos/d03_clase/correr.py)
PARAMS_D03 = dict(objective="binary", learning_rate=0.05, num_leaves=63, min_data_in_leaf=200, feature_fraction=0.5,
                  bagging_fraction=0.8, bagging_freq=1, verbosity=-1, num_threads=12, deterministic=True,
                  force_col_wise=True)
RONDAS_D03 = 500


# [Anotación · líneas 55–59] `validar()`: termina si una predicción no tiene el tamaño esperado, tiene valores
#   no finitos o fuera de [0, 1].
def validar(p, n, nombre):
    p = np.asarray(p)
    if p.shape != (n,) or not np.isfinite(p).all() or p.min() < 0 or p.max() > 1:
        raise SystemExit(f"{nombre}: predicción inválida")
    return p


# [Anotación · líneas 62–79] `pruebas()` lee la tabla de la búsqueda corrida en este repositorio si tiene las
#   40 pruebas, y si no la de `origen/esperado/`. `finalistas()` ordena por A descendente (desempates: menor
#   rondas × hojas, menos rondas, número de prueba), quita repeticiones de hojas y h y toma las primeras 5.
def pruebas():
    """Las pruebas de la búsqueda completa corrida acá («propia»), o si no, las de la corrida original."""
    propia = bq.SALIDA / "pruebas.csv"
    if propia.exists():
        p = pd.read_csv(propia).drop_duplicates("prueba", keep="last")
        if len(p) >= bq.N_PRUEBAS:
            print(f"finalistas de la búsqueda corrida acá ({propia.relative_to(comun.RAIZ)})", flush=True)
            return p, "propia"
    print(f"finalistas de la corrida original ({ESPERADO.parent.relative_to(comun.RAIZ)}/pruebas_d04.csv)", flush=True)
    return pd.read_csv(bq.ESPERADO), "original"


def finalistas():
    todas, origen = pruebas()
    p = todas[["prueba", "num_leaves", "h_ref", "rondas", "A"]].copy()
    p["costo"] = p.rondas * p.num_leaves
    p = p.sort_values(["A", "costo", "rondas", "prueba"], ascending=[False, True, True, True])
    return p.drop_duplicates(["num_leaves", "h_ref"]).head(N_FINALISTAS), origen


# [Anotación · líneas 82–106] `guardar()` escribe una predicción en disco. `prediccion_finalista()` devuelve
#   la predicción de una finalista para un corte y una semilla: la lee si ya está guardada y, si no, entrena con
#   los parámetros fijos de la búsqueda y las hojas, el hessiano y las rondas de esa prueba, y la guarda.
def guardar(path, p):
    temporal = path.with_suffix(".tmp.npy")
    np.save(temporal, p.astype("float64"), allow_pickle=False)
    temporal.replace(path)


def prediccion_finalista(datos, fila, corte, s, origen):
    """Con finalistas de la búsqueda propia, usa sus predicciones (semillas 147347 y 322607), como el original. Con
    las de la corrida original, entrena: las predicciones de una búsqueda propia podrían ser de otras pruebas."""
    d = datos[corte]
    carpetas = ([PRED_BUSQUEDA] if origen == "propia" else []) + [SALIDA / origen]
    for carpeta in carpetas:
        path = carpeta / f"p{int(fila.prueba):03d}_{corte}_{s}.npy"
        if path.exists():
            return validar(np.load(path, allow_pickle=False), len(d["y_val"]), path.name)
    t0 = time.time()
    params = {**bq.FIJOS, "num_leaves": int(fila.num_leaves),
              "min_sum_hessian_in_leaf": fila.h_ref * d["filas"] / bq.FILAS_REF, "seed": s}
    p = validar(lgb.train(params, d["ds"], num_boost_round=int(fila.rondas)).predict(d["X_val"]), len(d["y_val"]),
                f"prueba {int(fila.prueba)} {corte} {s}")
    (SALIDA / origen).mkdir(parents=True, exist_ok=True)
    guardar(SALIDA / origen / f"p{int(fila.prueba):03d}_{corte}_{s}.npy", p)
    print(f"  prueba {int(fila.prueba)} {corte} {s}: A {bq.a_rango(d['y_val'], p):.2f} M, {time.time() - t0:.0f} s",
          flush=True)
    return p


# [Anotación · líneas 109–130] `prediccion_referencia()` hace lo mismo para la configuración de referencia: un
#   `Dataset` nuevo por semilla, `PARAMS_D03` y 500 rondas. `preparar()` toma los datos de la búsqueda y agrega
#   las matrices de entrenamiento.
def prediccion_referencia(datos, corte, s):
    """La K2 actual de la D03: un `Dataset` nuevo por semilla, sin parámetros propios, y los de la D03 al entrenar."""
    d = datos[corte]
    path = SALIDA / f"K2_{corte}_{s}.npy"
    if path.exists():
        return validar(np.load(path, allow_pickle=False), len(d["y_val"]), path.name)
    t0 = time.time()
    ds = lgb.Dataset(d["X_train"], label=d["y_train"], free_raw_data=False)
    p = validar(lgb.train({**PARAMS_D03, "seed": s}, ds, num_boost_round=RONDAS_D03).predict(d["X_val"]),
                len(d["y_val"]), f"K2 {corte} {s}")
    guardar(path, p)
    print(f"  K2 actual {corte} {s}: A {bq.a_rango(d['y_val'], p):.2f} M, {time.time() - t0:.0f} s", flush=True)
    return p


def preparar():
    """Los datos de la búsqueda (`bq.preparar()`), más las matrices de entrenamiento que necesita la referencia."""
    datos = bq.preparar()
    for d in datos.values():
        d["X_train"] = d["ds"].get_data()
        d["y_train"] = d["ds"].get_label().astype("int8")
    return datos


# [Anotación · líneas 133–168] `seleccion()`: para cada finalista y cada corte obtiene las predicciones de las
#   5 semillas de la finalista y de la referencia, calcula A del promedio de semillas de cada una, su
#   diferencia, la diferencia media por semilla y cuántas semillas mejoran. Marca `elegible` si la media de las
#   diferencias entre cortes es al menos 10, las dos diferencias son positivas y en cada corte la diferencia
#   media por semilla es positiva con al menos 4 de 5 semillas a favor. Guarda `seleccion.csv` e imprime la
#   prueba de mayor ΔA.
def seleccion():
    SALIDA.mkdir(parents=True, exist_ok=True)
    fins, origen = finalistas()
    print(f"finalistas: {fins.prueba.tolist()}", flush=True)
    datos = preparar()
    filas = []
    for fila in fins.itertuples(index=False):
        comp = {}
        for corte in bq.CORTES:
            y = datos[corte]["y_val"]
            nueva = {s: prediccion_finalista(datos, fila, corte, s, origen) for s in SEMILLAS_5}
            actual = {s: prediccion_referencia(datos, corte, s) for s in SEMILLAS_5}
            a_n = bq.a_rango(y, np.mean(list(nueva.values()), axis=0))
            a_a = bq.a_rango(y, np.mean(list(actual.values()), axis=0))
            ind = [bq.a_rango(y, nueva[s]) - bq.a_rango(y, actual[s]) for s in SEMILLAS_5]
            comp[corte] = {"A_nueva": a_n, "A_actual": a_a, "dif_ensamble": a_n - a_a,
                           "dif_individual_media": float(np.mean(ind)), "semillas_mejoran": int(sum(x > 0 for x in ind)),
                           "por_semilla": " ".join(f"{x:+.1f}" for x in ind)}
        d_a = float(np.mean([comp[c]["dif_ensamble"] for c in bq.CORTES]))
        ok = (d_a >= MARGEN_A and all(comp[c]["dif_ensamble"] > 0 for c in bq.CORTES)
              and all(comp[c]["dif_individual_media"] > 0 and comp[c]["semillas_mejoran"] >= 4 for c in bq.CORTES))
        for c in bq.CORTES:
            filas.append({"prueba": int(fila.prueba), "hojas": int(fila.num_leaves), "h_ref": round(fila.h_ref, 3),
                          "rondas": int(fila.rondas), "corte": c, "A_nueva_M": round(comp[c]["A_nueva"], 2),
                          "A_actual_M": round(comp[c]["A_actual"], 2), "dif_ensamble_M": round(comp[c]["dif_ensamble"], 2),
                          "dif_individual_media_M": round(comp[c]["dif_individual_media"], 2),
                          "semillas_que_mejoran": f"{comp[c]['semillas_mejoran']}/5", "por_semilla_M": comp[c]["por_semilla"],
                          "dA_M": round(d_a, 2), "elegible": "sí" if ok else "no"})
    t = pd.DataFrame(filas)
    t.to_csv(SALIDA / "seleccion.csv", index=False)
    print(t[["prueba", "hojas", "h_ref", "corte", "A_nueva_M", "A_actual_M", "dif_ensamble_M", "semillas_que_mejoran",
             "dA_M", "elegible"]].to_string(index=False))
    mejor = t.drop_duplicates("prueba").sort_values("dA_M", ascending=False).iloc[0]
    print(f"\nMayor ΔA: prueba {mejor.prueba} ({mejor.hojas} hojas, h {mejor.h_ref}), ΔA {mejor.dA_M:+.2f} M; "
          f"elegibles: {', '.join(map(str, t[t.elegible == 'sí'].prueba.unique())) or 'ninguna'}")
    return t


# [Anotación · líneas 171–186] `comparar_con_original()` compara la tabla con
#   `origen/esperado/seleccion_d04.csv` (finalistas, cortes, hojas, rondas, semillas que mejoran y elegibilidad
#   iguales; columnas de A con tolerancia 0,011). El punto de entrada corre la selección y sale con código 1 si
#   no coincide.
def comparar_con_original(t):
    o = pd.read_csv(ESPERADO)
    print("\nComparación con la selección original:")
    ok = t[["prueba", "corte", "hojas", "rondas", "semillas_que_mejoran", "elegible"]].equals(
        o[["prueba", "corte", "hojas", "rondas", "semillas_que_mejoran", "elegible"]])
    print(f"  finalistas, cortes, semillas que mejoran y elegibilidad: {'iguales' if ok else 'DISTINTAS'}")
    for col in ("A_nueva_M", "A_actual_M", "dif_ensamble_M", "dA_M"):
        ok &= comun.comparar(col, t[col], o[col], 0.011)        # la tabla original está redondeada a 2 decimales
    print("→ " + ("reproduce la selección original" if ok else "NO reproduce la selección original"))
    return ok


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if not comparar_con_original(seleccion()):
        raise SystemExit(1)
```

### origen/regla_n.py

Calcula la cantidad de clientes a enviar: entrena D con 20 semillas en cuatro cortes de validación, arma siete escenarios de ganancia y aplica una regla de arrepentimiento máximo sobre la grilla 9.000–12.000. Según su docstring, de acá sale N = 11.000. `reproducir.py` no lo ejecuta.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–38] Docstring. Describe el cálculo de N: entrenamiento de D en cuatro cortes de
#   validación con las 20 semillas, siete escenarios de ganancia, la regla sobre la grilla 9.000–12.000 y el
#   control contra `origen/esperado/regla_n_d10.json`. Declara el resultado original: N* = 11.000.
# -*- coding: utf-8 -*-
"""Origen de N = 11.000: la regla de N de la decisión D10 (9-oct-2026), aplicada a D.

Es el cálculo de `experimentos/d10/` de la carpeta de trabajo (el entrenamiento de D en los cuatro cortes y
`analizar.py n`), en un solo archivo. La regla se fijó antes de mirar los resultados.

**Qué hace:**
1. **Entrena D en cuatro cortes de validación,** con las 20 semillas de `03_envios_tablero.semillas()` y la receta de
   `06_receta_denicolay.py`: las mismas variables (C0 con *lags* y deltas 1 y 2 de todo), la clase K2 y los
   hiperparámetros. Las columnas útiles se calculan con las filas de entrenamiento de cada corte.

   | Corte | Entrenamiento | Validación |
   |---|---|---|
   | F1 | 202103 | 202105 |
   | F5 | 202104 | 202105 |
   | F2 | 202103–202104 | 202106 |
   | F4 | 202105 | 202106 |
2. **Arma siete escenarios** con el promedio de las 20 probabilidades. En cada uno, la ganancia
   G(N) = 1,1·TP(N) − 0,0275·N (M), con TP sólo de BAJA+2:
   - F1, F5, F2 y F4;
   - F2_L: junio sin la cohorte de préstamos personales congelados, en el orden de los demás. La cohorte son los
     clientes con `mprestamos_personales` > 0 e igual en 202104, 202105 y 202106. Se lee del crudo, porque esa columna
     no está en el dataset de `01_preparar_datos.py`;
   - F2 con el TP × 0,92 y × 0,85: un agosto más difícil.
3. **Aplica la regla** sobre la grilla N ∈ {9.000, 9.500, …, 12.000}:
   - el arrepentimiento de cada escenario es el máximo de G en la grilla menos G(N);
   - N* es el de menor arrepentimiento máximo; en un empate, el más cercano a 11.500, y si sigue, el menor;
   - se cambia de 11.500 a N* sólo si la media entre escenarios de G(N*) − G(11.500) es > 0.
4. **El control:** compara G, los arrepentimientos y N con la corrida original (`origen/esperado/regla_n_d10.json`).

Resultado original: N* = 11.000, con un arrepentimiento máximo de 6,05 contra 14,30 de 11.500 y una mejora media de
+2,99 M. Por eso el archivo entregado tiene 11.000 clientes (`07_archivo_d10.py`).

Uso, desde la raíz y después de `python 01_preparar_datos.py`, con el crudo en `datos/` o en
`COMPETENCIA_01_CRUDO`: `python origen/regla_n.py`. Entrena 80 modelos, unos 25 minutos.

Salidas en `origen/salidas/regla_n/`: las predicciones y `regla_n.json`.
"""
# [Anotación · líneas 39–54] Importa `comun` (y con él `var`, `tb` y `receta_d`) y define los cuatro cortes
#   (F1 202103 → 202105, F2 202103–202104 → 202106, F5 202104 → 202105, F4 202105 → 202106), la grilla de N de
#   9.000 a 12.000 con paso 500, el N vigente (11.500) y los factores 0,92 y 0,85.
import json
import sys
import time

import lightgbm as lgb
import numpy as np
import pandas as pd

import comun

var, tb, rd = comun.var, comun.tb, comun.receta_d
SALIDA = comun.SALIDAS / "regla_n"
ESPERADO = comun.ESPERADO / "regla_n_d10.json"
CORTES = {"F1": ([202103], 202105), "F2": ([202103, 202104], 202106), "F5": ([202104], 202105),
          "F4": ([202105], 202106)}                     # el orden de la D10, que fija el de la media entre escenarios
GRILLA, ACTUAL, FACTORES_TP = [9000, 9500, 10000, 10500, 11000, 11500, 12000], 11_500, [0.92, 0.85]


# [Anotación · líneas 57–68] `periodo()` convierte AAAAMM en año×12+mes. `cohorte()` devuelve los clientes con
#   `mprestamos_personales` positivo e igual en el mes dado y en los dos meses calendario anteriores, según el
#   crudo.
def periodo(foto_mes):
    f = np.asarray(foto_mes, dtype="int64")
    return (f // 100) * 12 + f % 100


def cohorte(crudo, mes):
    """Clientes con `mprestamos_personales` > 0 e igual en mes, mes−1 y mes−2 (meses calendario). No mira la clase."""
    per, p = periodo(crudo["foto_mes"]), periodo([mes])[0]
    t = [crudo[per == p - j].set_index("numero_de_cliente")["mprestamos_personales"] for j in range(3)]
    ids = t[0].index.intersection(t[1].index).intersection(t[2].index)
    a, b, z = (x.loc[ids].to_numpy(dtype="float64") for x in t)
    return set(ids[(a > 0) & (a == b) & (a == z)].astype("int64"))


# [Anotación · líneas 71–78] `regla_n()`: para cada escenario calcula el arrepentimiento de cada N (máximo de
#   G en la grilla menos G(N)) y, para cada N, el máximo entre escenarios. N* es el N con menor arrepentimiento
#   máximo (desempates: el más cercano a 11.500 y después el menor). El N final es N* si la media entre
#   escenarios de G(N*) − G(11.500) es mayor que 0; si no, 11.500.
def regla_n(G):
    """`G`: {escenario: {N: ganancia}}. Devuelve N*, la mejora media, el N final y los arrepentimientos."""
    reg = {s: {n: max(G[s][m] for m in GRILLA) - G[s][n] for n in GRILLA} for s in G}
    peor = {n: max(reg[s][n] for s in G) for n in GRILLA}
    n_star = min(GRILLA, key=lambda n: (peor[n], abs(n - ACTUAL), n))
    mejora = float(np.mean([G[s][n_star] - G[s][ACTUAL] for s in G]))
    return {"N_estrella": n_star, "mejora_media": mejora, "N_final": n_star if mejora > 0 else ACTUAL,
            "arrepentimiento_maximo": peor}


# [Anotación · líneas 81–92] `predicciones()`, preparación: exige el parquet y el crudo, construye el panel
#   con `hist_1y2_todas=True`, se queda con 202103–202106 y lee del crudo las tres columnas necesarias para la
#   cohorte.
def predicciones():
    """El promedio de las 20 semillas de D en cada corte, más la y y la cohorte del mes validado."""
    comun.exigir_datos()
    if not comun.CRUDO.exists():
        raise SystemExit(f"falta el crudo en {comun.CRUDO}: copiarlo a datos/ o definir COMPETENCIA_01_CRUDO")
    SALIDA.mkdir(parents=True, exist_ok=True)
    panel = var.construir(pd.read_parquet(comun.DATOS), hist_1y2_todas=True)
    panel = panel[panel.foto_mes.between(202103, 202106)].reset_index(drop=True)
    crudo = pd.read_csv(comun.CRUDO, usecols=["numero_de_cliente", "foto_mes", "mprestamos_personales"])
    predictores = var.predictores_de(panel)
    clase = panel[var.CLASE].to_numpy(dtype="U8")
    salida = {}
# [Anotación · líneas 93–122] Para cada corte arma el `Dataset` de entrenamiento con las columnas de al menos
#   2 valores distintos en ese entrenamiento y la clase BAJA+1 o BAJA+2, usa los hiperparámetros de
#   `06_receta_denicolay.py` (83 hojas, hessiano escalado por las filas del corte, 1.000 rondas) y entrena un
#   modelo por cada una de las 20 semillas, o lee su predicción si ya está guardada. Devuelve el promedio de las
#   20 probabilidades, la etiqueta de validación (1 = BAJA+2) y la pertenencia a la cohorte.
    for corte, (meses, mes_val) in CORTES.items():
        en_train = panel.foto_mes.isin(meses).to_numpy()
        en_val = (panel.foto_mes == mes_val).to_numpy()
        X = panel.loc[en_train | en_val, predictores].astype("float32")
        tr = en_train[en_train | en_val]
        cols = [c for c in predictores if X.loc[tr, c].nunique(dropna=False) >= 2]
        y_train = np.isin(clase[en_train], rd.POSITIVAS).astype("int8")
        X_val = np.ascontiguousarray(X.loc[~tr, cols].to_numpy())
        ds = lgb.Dataset(np.ascontiguousarray(X.loc[tr, cols].to_numpy()), label=y_train,
                         params={"max_bin": rd.FIJOS["max_bin"], "feature_pre_filter": False, "verbosity": -1},
                         free_raw_data=False)
        ds.construct()
        params = {**rd.FIJOS, "num_leaves": rd.HOJAS, "min_sum_hessian_in_leaf": rd.H_REF * len(y_train) / rd.FILAS_REF}
        probs = []
        for s in tb.semillas():
            path = SALIDA / f"D_{corte}_{s}.npy"
            if path.exists():
                probs.append(np.load(path, allow_pickle=False))
                continue
            t0 = time.time()
            p = lgb.train({**params, "seed": s}, ds, num_boost_round=rd.RONDAS).predict(X_val)
            np.save(path, p.astype("float64"), allow_pickle=False)
            probs.append(p)
            print(f"  D {corte} {s}: {time.time() - t0:.0f} s", flush=True)
        claves = panel.loc[en_val, "numero_de_cliente"].to_numpy(dtype="int64")
        salida[corte] = {"p": np.mean(probs, axis=0), "y": (clase[en_val] == "BAJA+2").astype("int8"),
                         "cohorte": np.isin(claves, np.fromiter(cohorte(crudo, mes_val), dtype="int64"))}
        print(f"{corte}: {len(cols)} columnas, {len(y_train)} filas de entrenamiento; la cohorte del mes validado "
              f"tiene {int(salida[corte]['cohorte'].sum())} clientes", flush=True)
    return salida


# [Anotación · líneas 125–133] `escenarios()`: calcula G(N), en millones, en la grilla para los cuatro cortes;
#   agrega `F2_L` (F2 sin los clientes de la cohorte) y dos escenarios de F2 con los aciertos multiplicados por
#   0,92 y 0,85.
def escenarios(d):
    G = {c: {n: float(comun.curva(d[c]["y"], d[c]["p"])[n - 1]) for n in GRILLA} for c in CORTES}
    y, coh, p = d["F2"]["y"], d["F2"]["cohorte"], d["F2"]["p"]
    gl = comun.curva(y[~coh], p[~coh])
    G["F2_L"] = {n: float(gl[n - 1]) for n in GRILLA}
    tp = np.cumsum(y[np.argsort(-p, kind="stable")])
    for f in FACTORES_TP:
        G[f"F2_TPx{f}"] = {n: float(1.1 * f * tp[n - 1] - 0.0275 * n) for n in GRILLA}
    return G


# [Anotación · líneas 136–147] `comparar_con_original()`: compara G de cada escenario y el arrepentimiento
#   máximo con `origen/esperado/regla_n_d10.json` (tolerancia 1e-9) y verifica que N* y el N final sean iguales.
def comparar_con_original(G, r):
    o = json.loads(ESPERADO.read_text(encoding="utf-8"))
    print("\nComparación con la corrida original:")
    ok = list(G) == list(o["G"])
    for s in G:
        ok &= comun.comparar(f"G de {s}", [G[s][n] for n in GRILLA], [o["G"][s][str(n)] for n in GRILLA], 1e-9)
    ok &= comun.comparar("arrepentimiento máximo", [r["arrepentimiento_maximo"][n] for n in GRILLA],
                         [o["arrepentimiento_maximo"][str(n)] for n in GRILLA], 1e-9)
    ok &= r["N_estrella"] == o["N_estrella"] and r["N_final"] == o["N_final"]
    print(f"  N* y N final: {r['N_estrella']} y {r['N_final']} (original {o['N_estrella']} y {o['N_final']})")
    print("→ " + ("reproduce la regla de N original" if ok else "NO reproduce la regla de N original"))
    return ok


# [Anotación · líneas 150–159] Punto de entrada: calcula los escenarios, aplica la regla, imprime la tabla de
#   G, los arrepentimientos y N, guarda `regla_n.json` y sale con código 1 si no coincide con la corrida
#   original.
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    G = escenarios(predicciones())
    r = regla_n(G)
    print(pd.DataFrame(G).T.round(2).to_string())
    print("arrepentimiento máximo: " + ", ".join(f"{n}: {x:.2f}" for n, x in r["arrepentimiento_maximo"].items()))
    print(f"N* = {r['N_estrella']}; media de G(N*) − G(11.500) = {r['mejora_media']:+.3f} → N = {r['N_final']}")
    (SALIDA / "regla_n.json").write_text(json.dumps({"G": G, **r}, indent=1), encoding="utf-8")
    if not comparar_con_original(G, r):
        raise SystemExit(1)
```

### origen/comun.py

Módulo compartido por los tres scripts de `origen/`: rutas, carga de `02_variables.py`, `03_envios_tablero.py` y `06_receta_denicolay.py` como módulos, curva de ganancia en millones y comparación numérica con tolerancia.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–16] Docstring, importaciones y rutas compartidas por los scripts de `origen/`: raíz
#   del repositorio, `origen/esperado/`, `origen/salidas/`, el parquet de datos y el crudo (variable
#   `COMPETENCIA_01_CRUDO` o `datos/competencia_01_crudo.csv`).
# -*- coding: utf-8 -*-
"""Lo que comparten los scripts de `origen/`: las rutas del repositorio, los módulos `02_variables.py`,
`03_envios_tablero.py` y `06_receta_denicolay.py`, la ganancia y la comparación con los resultados originales
(`origen/esperado/`)."""
import importlib.util
import os
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
ESPERADO = AQUI / "esperado"
SALIDAS = AQUI / "salidas"
DATOS = RAIZ / "datos" / "competencia_01_d01.parquet"
CRUDO = Path(os.environ.get("COMPETENCIA_01_CRUDO", RAIZ / "datos" / "competencia_01_crudo.csv"))


# [Anotación · líneas 19–28] `modulo()` carga un archivo .py por su ruta; con ella se cargan `02_variables.py`
#   (`var`), `03_envios_tablero.py` (`tb`) y `06_receta_denicolay.py` (`receta_d`).
def modulo(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


var = modulo("variables", RAIZ / "02_variables.py")
tb = modulo("tablero", RAIZ / "03_envios_tablero.py")
receta_d = modulo("receta_d", RAIZ / "06_receta_denicolay.py")


# [Anotación · líneas 31–44] `exigir_datos()` termina si falta el parquet. `curva()` devuelve la ganancia
#   acumulada en millones, 1,1·TP(k) − 0,0275·k, ordenando por probabilidad descendente con desempate estable.
#   `a_rango()` promedia esa curva entre k = 8.000 y k = 15.000.
def exigir_datos():
    if not DATOS.exists():
        raise SystemExit(f"falta {DATOS.relative_to(RAIZ)}: primero python 01_preparar_datos.py")


def curva(y, p):
    """G(k) en millones, k = 1..n: 1,1·TP(k) − 0,0275·k, con el ranking descendente de `p` y desempate estable."""
    orden = np.argsort(-np.asarray(p, dtype="float64"), kind="stable")
    return 1.1 * np.cumsum(np.asarray(y)[orden]) - 0.0275 * np.arange(1, len(y) + 1)


def a_rango(g):
    """A: la media de G(k) sobre los 7.001 enteros k = 8.000..15.000."""
    return float(np.mean(g[7999:15000]))


# [Anotación · líneas 47–53] `comparar()`: imprime la diferencia máxima en valor absoluto entre dos listas de
#   números y devuelve si tienen la misma forma y la diferencia está dentro de la tolerancia.
def comparar(nombre, obtenido, esperado, tolerancia):
    """Imprime la diferencia máxima entre dos listas de números y devuelve si está dentro de la tolerancia."""
    obtenido, esperado = np.asarray(obtenido, dtype="float64"), np.asarray(esperado, dtype="float64")
    dif = float(np.max(np.abs(obtenido - esperado))) if len(esperado) else 0.0
    ok = obtenido.shape == esperado.shape and dif <= tolerancia
    print(f"  {nombre}: diferencia máxima {dif:.3g} (tolerancia {tolerancia:g}) → {'coincide' if ok else 'NO COINCIDE'}")
    return ok
```


## Explicaciones del alumno (texto original)

### DECISIONES.md

> # Decisiones de la Competencia 1
>
> Resumen de las once decisiones que llevaron al archivo entregado, del 5 al 9-oct-2026. El detalle completo, con
> los análisis, las pruebas y las verificaciones, está en mi carpeta de trabajo y no se publica.
>
> ## Procedimiento
>
> Para cada decisión:
>
> 1. escribí la pregunta, con las opciones y los criterios;
> 2. dos asistentes de IA la analizaron por separado, y cada análisis se selló con su SHA-256 antes de que el otro
>    lo leyera;
> 3. cada uno criticó el análisis del otro;
> 4. decidí yo, con los dos análisis y las críticas a la vista;
> 5. se implementó el código, que se revisó antes de cada corrida y de cada envío. La excepción fue la búsqueda de
>    D04: a mi pedido arrancó con la revisión en paralelo, y no se frenó porque la revisión no encontró problemas
>    graves;
> 6. los resultados se verificaron por separado, recalculándolos desde las predicciones guardadas.
>
> Las reglas para adoptar un cambio se fijaron antes de ver los resultados.
>
> ## Cómo se midió
>
> **Ganancia:** G(k) = 1.100.000 · TP(k) − 27.500 · k, donde TP cuenta sólo los BAJA+2 entre los k clientes de
> mayor probabilidad. A_f es la media de G(k), en millones, sobre todos los enteros k de 8.000 a 15.000 del corte f
> (desde D03; en D02 se promediaba la grilla de 8.000 a 15.000 con paso 500):
>
> | Corte | Entrenamiento | Validación |
> |---|---|---|
> | F1 | 202103 | 202105 |
> | F2 | 202103–202104 | 202106 |
> | F3, control | 202104 | 202106 |
>
> La métrica principal es A = (A_F1 + A_F2) / 2, sobre el promedio de las probabilidades de las semillas.
>
> **Regla de reemplazo** (D03 a D05): una alternativa reemplaza a la vigente sólo si
> - A mejora al menos 10 M;
> - A_F1 y A_F2 mejoran los dos;
> - A_F3 no pierde más de 5 M;
> - en F1 y en F2, la diferencia media por semilla es positiva, con al menos 4 de 5 semillas a favor en la
>   pantalla y 16 de 20 en la confirmación.
>
> ## D01 · Datos
>
> - **Clase:** `clase_ternaria` recalculada con la lógica de la cátedra. Si el cliente falta el mes siguiente es
>   BAJA+1, aunque después vuelva; si está el siguiente y falta el subsiguiente, BAJA+2.
> - **Reparaciones:**
>   - `ccajas_depositos` y `ccajas_otras` se reemplazan por su suma, porque entre abril y junio se reclasificaron
>     transacciones entre las dos;
>   - se sacan `Visa_mconsumototal` y `Master_mconsumototal`, idénticas a `*_mconsumospesos`;
>   - NA en `*_mfinanciacion_limite` cuando el límite de compra es positivo y la financiación lo supera 10 veces,
>     errores de escala;
>   - NA en `*_Fvencimiento` menores que −1.000.000, un valor centinela;
>   - se sacan `cprestamos_personales` y `mprestamos_personales`: en junio cambia su relación con la baja.
> - **Meses:** el modelo final se entrena con 202103–202106 y predice 202108; 202107 se usa sólo como historia.
>
> ## D02 · Variables
>
> - **Validación local:** ningún bloque cumplió la regla fijada antes: cierres centrados, indicadores de
>   mantenimiento, rankings, historia selectiva, historia amplia y variables nuevas. El resultado local fue C0, los
>   datos de D01 sin variables nuevas.
> - **Tablero público,** media de 20 archivos de una semilla con N = 11.000:
>
>   | Envío | Ganancia pública |
>   |---|---:|
>   | C0 | 81,00 |
>   | C0 + historia selectiva (C7) | **84,77** |
>   | C0 + *lags* y deltas 1 y 2 de todas las variables | 82,86 |
>
> - **Decisión: C7,** es decir C0 más *lag* 1 y delta 1 de seis conteos y del ranking mensual de cuatro montos.
>   Me aparté del resultado local por la evidencia de agosto en el tablero, sabiendo que el tablero mide alrededor
>   del 25% de agosto.
>
> ## D03 · Clase de entrenamiento
>
> - **Variantes:** K1, BAJA+2 contra el resto; K2, BAJA+1 y BAJA+2 contra CONTINUA; K3, BAJA+2 contra CONTINUA sin
>   las filas BAJA+1.
> - **K2 pasó la regla** y se confirmó con 20 semillas: A +28,54 M (F1 +39,40, F2 +17,68 y F3 +35,93 M), con las 20
>   semillas a favor en los tres cortes. K3 no pasó.
> - **Tablero,** un archivo de ensamble de 20 semillas por clase, N = 11.000: K1 92,81 y K2 86,74. La diferencia,
>   −6,08, no llegó al veto fijado antes de mandar, −9,94.
> - **Decisión: K2,** con K1 como alternativa.
>
> ## D04 · Hiperparámetros
>
> - **Búsqueda:** 40 pruebas con Optuna (TPE, semilla 147347) sobre la receta de Denicolay que se compartió en el
>   Zulip de la materia: `learning_rate` 0,005, `max_bin` 31, `min_data_in_leaf` 0, `feature_fraction` 0,5 y
>   `feature_fraction_bynode` 0,2, sin *bagging*. Quedaron libres las hojas, el hessiano mínimo por hoja y las
>   rondas.
> - **Resultado: ninguna configuración cumplió la regla.** Las cinco mejores mejoraban A entre 3,89 y 6,19 M, y todas
>   empeoraban el ensamble en F1. La receta nueva da modelos individuales mejores, pero gana mucho menos al promediar
>   semillas. Tampoco hubo candidatas al ampliar la grilla a 250, 500 y 750 rondas.
> - **Control de clase** con la configuración vigente, N = 11.500: en el tablero, K1 91,82 y K2 86,74. La
>   diferencia, −5,09, no llegó al veto, −9,58.
> - **Corte:** N = 11.500, el que minimiza la peor pérdida entre F1 y F2 en la grilla de 8.000 a 15.000 con paso
>   500, con la pérdida medida contra el máximo de cada corte.
> - **Decisión:** se conservan los hiperparámetros vigentes, K2 y N = 11.500.
>
> ## D05 · Archivo final
>
> - **Decisión: K2 sola,** con 20 semillas y N = 11.500: `d04k2en11500.csv`, el último envío hasta ese momento.
> - **Alternativas medidas y no adoptadas,** porque ninguna cumplió la regla de reemplazo:
>
>   | Alternativa | Contra K2, en validación |
>   |---|---|
>   | Promedio de probabilidades K1 + K2 | A −0,03 M; en N = 11.500, F1 −2,20 y F2 −4,40 M |
>   | Promedio de rangos K1 + K2 | A −9,09 M; F3 −7,81 M |
>   | K2 + la receta de D04 (prueba 38, la mejor finalista de la selección) | entre +5,8 y +6,3 M en la media de F1 y F2, por debajo de los 10 M; sin F3 |
>   | K1 sola | A −28,54 M; mejor en el tablero: 92,81 y 91,82 contra 86,74 |
>
> ## D06 · Plan para los últimos días
>
> - **Un punto ciego de la validación local:**
>   - F1 no usa ninguna variable de historia, porque marzo no tiene mes anterior;
>   - la historia de orden 2 no existe en ningún corte: 0 columnas útiles en F1, F2 y F3, y 294 en el modelo final
>     (147 *lags* 2 y 147 deltas 2).
> - **Grilla cerrada contra la base:** ninguna variante pasó la regla. Fueron un ranking con «cero fijo», el signo de
>   la comisión de mantenimiento y sacar la historia.
> - **Tablero, con candidatos y regla fijados antes de ver resultados:**
>   - un envío por candidato, todos con 20 semillas y N = 11.500;
>   - para adoptar un candidato sin evidencia local hay que superar a la base por un margen corregido por la cantidad
>     de candidatos mirados.
>
>   | Candidato | Público | Contra la base |
>   |---|---:|---:|
>   | Base (K2 sobre C7) | 86,74 | — |
>   | K2 + prueba 38, mezcla 50/50 | 89,95 | +3,2 |
>   | K1 | 91,82 | +5,1 |
>   | L: *lags* y deltas 1 y 2 de todo, configuración vigente | 98,59 | +11,9 |
>   | **D: las variables de L con la receta de la prueba 38** | **103,18** | **+16,4** |
>
> - **La regla elige D**, lo que verificó Codex por su cuenta.
>
> ## D07 a D09 · Rondas alrededor de D
>
> Tres decisiones más intentaron mejorar a D, con reglas fijadas antes y el público sólo como control. Ninguna lo
> reemplazó:
>
> | Decisión | Qué se probó | Resultado |
> |---|---|---|
> | D07 | Un corte F4 (202105 → 202106), el único que ve la historia de orden 2; D con K1 y otras tres rondas | D-K1 perdió 10,6 en el público (92,57). Las rondas 2 y 3 no dejaron candidata y la 4 se omitió |
> | D08 | 24 configuraciones de hiperparámetros, medidas en F4 y F2 | La mejor pasó la pantalla (+4,56) pero no la confirmación con 20 semillas nuevas (+3,52, con una barra de 5,4). En el público, informativo, dio 99,19 |
> | D09 | Julio con etiquetas parciales, pesos para BAJA+1, reparar los cierres de tarjeta y un modelo auxiliar | La reparación se descartó antes de la pantalla, porque los cierres pesaban el 0,23% de la ganancia de los árboles. Las demás líneas no pasaron la pantalla: julio parcial ganaba en mayo y perdía 21 en junio |
>
> ## D10 · Investigación profunda y el corte
>
> - **Análisis:** Con un análisis de Claude (un flujo de agentes con verificación adversarial) y otro de Codex, cruzados     como en las decisiones anteriores.
> - **Hallazgo:** una cohorte de clientes con el préstamo personal congelado (el mismo monto positivo tres meses
>   seguidos) tiene 1,23% de BAJA+2 en mayo y 12,32% en junio. Explica entre el 21 y el 23% de la ganancia de D en
>   junio. Se mantuvo la métrica de D09, que pondera mayo y junio por igual, y se agregó un control que saca a esa
>   cohorte.
> - **Pantalla:** cinco cambios sobre D, cada uno por separado:
>   - un bloque de 21 variables de comportamiento por canal;
>   - *bagging* 0,8;
>   - `extra_trees`;
>   - pesos por recencia;
>   - BAJA+3 como positivo con peso 0,3.
>
>   **Ninguno llegó siquiera a empatar a D:**
>
>   | Cambio | Contra D (media de mayo y junio, M) |
>   |---|---:|
>   | Bloque de comportamiento | −3,70 |
>   | *Bagging* 0,8 | −0,24 |
>   | `extra_trees` | −24,30 |
>   | Pesos por recencia | −0,58 |
>   | BAJA+3 con peso 0,3 | −0,51 |
>
> - **El corte.** Esta regla se fijó antes de mirar los resultados:
>   - siete escenarios, con las 20 semillas de D en cuatro cortes de validación, junio sin la cohorte y junio con el
>     92% y el 85% de los aciertos;
>   - N\* es el de menor arrepentimiento máximo sobre la grilla 9.000–12.000;
>   - se cambia sólo si la media mejora.
>
>   **Dio N\* = 11.000:** el arrepentimiento máximo baja de 14,30 a 6,05 y la media sube 2,99 M. Sólo el corte F4
>   pierde al pasar de 11.500 a 11.000.
> - **El público como veto:** se adoptaba salvo que perdiera más de 2σ contra D (4,39). `d10dn11000.csv` dio
>   **102,60**, contra 103,18 de D: −0,58, dentro del ruido.
> - **Decisión: D con N = 11.000,** `d10dn11000.csv`. Es el último envío y lo reproduce este repositorio.
>
> ## D11 · `max_bin` 255 (9-oct, informativa)
>
> - **Qué:** D con 255 cortes por variable en lugar de 31, con la misma pantalla de la D10, sellada antes de correr.
> - **Resultado:** ΔT +2,17, debajo de la barra de +3:
>   - mayo +3,03 y junio +1,30;
>   - los diagnósticos, −1,14 y +1,95;
>   - sin la cohorte de préstamos, junio queda en −0,27.
> - **No pasó, así que no cambió nada.** No se bajó la barra después de ver el resultado.
>
> ## De dónde salen los hiperparámetros y el corte
>
> Las 83 hojas y el hessiano de D salen de la búsqueda y la selección de la D04; N = 11.000, de la regla de la D10. El
> código que los produjo, con las instrucciones para correrlo, está en [origen/](origen/README.md).
>
> ## Uso de IA
>
> Usé dos asistentes de IA como analistas independientes, con el procedimiento de arriba:
>
> - **Claude** (Anthropic), en Claude Code: análisis de cada decisión, código, pruebas, corridas y documentación.
> - **Codex** (OpenAI): análisis independientes, críticas cruzadas, revisión del código antes de cada corrida y de
>   cada envío (salvo la búsqueda de D04, revisada en paralelo) y verificación de los resultados.
>
> Las decisiones las tomé yo y quedaron registradas con fecha en cada paso. En D02 me aparté del resultado local
> por la evidencia del tablero; en D03 y D04 mantuve K2 por las reglas fijadas antes, aunque el tablero favorecía a
> K1.

### README.md

> # DMEyF 2026 · Competencia 1
>
> **Federico Ramírez** · Data Mining en Economía y Finanzas, Maestría en Data Mining (UBA), 2026 · comisión del lunes.
>
> Este repositorio reproduce, desde el dataset crudo de la cátedra, el último archivo que envié al bot de la
> competencia: **`d10dn11000.csv`**, con 11.000 clientes de 202108 y SHA-256
> `8a03bf3d5fd792569187e8093a1663f7c7f97eeab7b785af412b06fc595a70b5`. Lo mandé el 9-oct-2026 a las 18:27, hora de
> Buenos Aires.
>
> **El modelo, D:** el promedio de las probabilidades de 20 LightGBM, uno por semilla.
> - **Entrenamiento:** 202103–202106, para separar BAJA+1 y BAJA+2 de CONTINUA.
> - **Variables:** los datos reparados más *lag* 1, delta 1, *lag* 2 y delta 2 de todas las variables, 735 columnas
>   útiles.
> - **Receta de hiperparámetros:** la de Denicolay, ajustada en mi búsqueda de D04 (prueba 38).
> - **Envío:** los 11.000 clientes con mayor promedio. Es el mismo modelo que mandé el 7-oct con 11.500 clientes
>   (`d06dn11500.csv`); el 9-oct una regla fijada antes de mirar bajó el corte a 11.000 (D10, en
>   [DECISIONES.md](DECISIONES.md)). El archivo de 11.000 es exactamente las primeras 11.000 líneas del de 11.500.
>
> También reproduce los envíos anteriores: **`d06dn11500.csv`** (D con 11.500), con `python reproducir.py d06d`, y
> **`d04k2en11500.csv`** (la «base»), con `python reproducir.py base`.
>
> ## Cómo reproducirlo
>
> Hace falta Python 3.13 de 64 bits y el crudo de la cátedra, `competencia_01_crudo.csv`, que no está en el
> repositorio: se baja de <https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv> (ver
> `datos/LEEME.md`). En macOS, LightGBM necesita además OpenMP (`brew install libomp`).
>
> ```bash
> git clone https://github.com/farpp8/dmeyf2026-competencia01.git
> cd dmeyf2026-competencia01
> python -m venv .venv
> .venv\Scripts\activate            # en Linux o macOS: source .venv/bin/activate
> pip install -r requirements.txt
> # copiar competencia_01_crudo.csv a datos/, o definir COMPETENCIA_01_CRUDO con su ruta
> python reproducir.py
> ```
>
> **Comprobado en Windows 11,** en una carpeta limpia y con las versiones de `requirements.txt`: termina con
> `OK: d10dn11000.csv coincide byte por byte con el archivo enviado`. Tardó 43 minutos, casi todos en entrenar los 20
> modelos. `python reproducir.py d06d` tarda lo mismo, y la base (`python reproducir.py base`), unos 4 minutos. La
> memoria máxima de un proceso que arma las variables y entrena D es de unos 12 GB.
>
> En otro sistema operativo o con otra compilación de LightGBM, `deterministic=True` no garantiza las mismas
> probabilidades. Si cambian, `reproducir.py` lo avisa, y el CSV puede diferir en clientes cercanos al corte.
>
> ## Qué hace cada script
>
> | Script | Qué hace |
> |---|---|
> | `01_preparar_datos.py` | Lee el crudo, calcula `clase_ternaria` con la lógica de la cátedra y aplica las reparaciones de D01. Escribe `datos/competencia_01_d01.parquet`. |
> | `02_variables.py` | Módulo de variables. Para D se usa `construir(df, hist_1y2_todas=True)`: *lags* y deltas 1 y 2 de todos los predictores. La base usa `BASE`, la historia selectiva de C7. |
> | `03_envios_tablero.py` | Módulo con los meses, las 20 semillas y la escritura del CSV. Como script arma los envíos de prueba de D02; `reproducir.py` no lo corre así. |
> | `06_receta_denicolay.py` | **D:** los 20 modelos con la receta de la prueba 38, sus probabilidades para 202108 y el CSV con los 11.500 clientes de mayor promedio. |
> | `07_archivo_d10.py` | **El último envío:** los 11.000 clientes de mayor promedio de esas mismas 20 probabilidades, sin reentrenar. Controla que los 11.500 primeros sean los de `d06dn11500.csv`. |
> | `05_envios_ensamble.py` | **La base:** `entrenar d03k2` y `archivo d03k2 d04k2e 11500`. |
> | `test_01_preparar_datos.py`, `test_02_variables.py` | Pruebas con paneles chicos: clase, reparaciones, identificadores, rutas con apóstrofo e historia por mes exacto. |
> | `reproducir.py` | Corre las pruebas y los pasos en orden, y compara cada etapa con `huellas_esperadas.json`. |
> | `origen/` | **De dónde salen los hiperparámetros y el corte:** la búsqueda bayesiana y la selección de la D04, que dieron las 83 hojas y el hessiano, y la regla de N de la D10, que dio 11.000. Ver [origen/README.md](origen/README.md). No hace falta para reproducir el archivo. |
>
> ## Qué fija el resultado de D
>
> - **Semillas:** 147347, 322607, 462467, 782149 y 983809, y los tres primos siguientes a cada una
>   (`semillas()` en `03_envios_tablero.py`).
> - **LightGBM** (`06_receta_denicolay.py`):
>   - `objective` binary, `learning_rate` 0,005, `max_bin` 31, `min_data_in_leaf` 0, `feature_fraction` 0,5,
>     `feature_fraction_bynode` 0,2 y sin *bagging*;
>   - 83 hojas, 1.000 rondas y `min_sum_hessian_in_leaf` = 12,791817 × filas / 326.184;
>   - `deterministic=True`, `force_col_wise=True` y `num_threads=12`, fijos en el código. No hace falta tener 12
>     núcleos, pero con menos tarda más;
>   - el `Dataset` se construye una vez y se reutiliza entre semillas.
> - **Clase:** BAJA+1 y BAJA+2 contra CONTINUA. La ganancia cuenta sólo BAJA+2.
> - **Empates:** los clientes de 202108 están ordenados por `numero_de_cliente` y el orden se toma con `argsort`
>   estable.
> - **CSV:** un `numero_de_cliente` por línea, sin encabezado, en ASCII y con saltos de línea CRLF.
> - **Entorno de la corrida original:** Windows 11 Pro, AMD Ryzen 7 9800X3D (8 núcleos, 16 hilos), Python 3.13.3 y
>   las versiones de `requirements.txt`.
>
> `reproducir.py` se detiene si el crudo no es el de la cátedra o si el CSV final no coincide. Si difieren el parquet
> o las probabilidades, por ejemplo con otro procesador, avisa y sigue: lo que se envió es la lista de clientes.
>
> ## Huellas
>
> | Archivo | SHA-256 |
> |---|---|
> | `competencia_01_crudo.csv`, la entrada (492.769.580 bytes) | `c72c8f5c1149f1d972e996c2963c5e3dbb31eb38cfe41c2bb1bbaf847d7a7ca1` |
> | `d10dn11000.csv`, D con N = 11.000, el último envío | `8a03bf3d5fd792569187e8093a1663f7c7f97eeab7b785af412b06fc595a70b5` |
> | `d06dn11500.csv`, D | `de534992228e5f26ebda4dc867f86dc78282cc194030e1884ecdd2ffd1a3d294` |
> | `d04k2en11500.csv`, la base | `91c18043de05f63a85108a0463599171b7e8ede3d1fa73f0e65aa3a0208684ba` |
>
> Las intermedias, del parquet, las claves, las columnas y las 20 probabilidades de cada entrega, están en
> `huellas_esperadas.json`.
>
> ## Diferencias con los scripts que generaron los envíos
>
> Son copias de los que usé, con estos cambios, que no alteran el resultado:
>
> 1. `01_preparar_datos.py` lee el crudo de `datos/` o de `COMPETENCIA_01_CRUDO`. Antes lo buscaba en la carpeta
>    de mi proyecto.
> 2. `01_preparar_datos.py` duplica las comillas simples de las rutas que pasa a SQL. Sin eso, una carpeta como
>    `O'Connor` hacía fallar la lectura del crudo.
> 3. `03_envios_tablero.py` escribe el CSV con `newline="\r\n"`. En Windows el modo texto ya convertía `\n` en
>    CRLF, así que el archivo es el mismo; en Linux o macOS, sin este cambio, cambiaría la huella.
> 4. El docstring de `01_preparar_datos.py` y su prueba usan identificadores sintéticos en lugar de un cliente real
>    del crudo.
> 5. `06_receta_denicolay.py` es el camino de entrenamiento de D de mi armador de candidatos, en un solo archivo y sin
>    depender de mis carpetas de trabajo. Antes de armar D, ese armador reprodujo bit a bit los dos caminos de
>    entrenamiento que usa: el de la configuración vigente y el de la prueba 38.
> 6. `02_variables.py` no incluye dos opciones que agregué después en mi copia, `cero_fijo` y `mantenimiento_signo`.
>    Las probé en D06, no las adopté y ni D ni la base las usan.
> 7. `07_archivo_d10.py` es el camino de D de mi armador del archivo de D10, en un solo archivo: toma las 20
>    probabilidades de D y escribe los 11.000 primeros.
>
> Los docstrings mencionan archivos de mi carpeta de trabajo que no se publican: `decisiones/`, `experimentos/`,
> `envios/` y el script que manda los archivos al bot. El resumen de las decisiones está en
> [DECISIONES.md](DECISIONES.md).
>
> ## Qué no incluye
>
> - el crudo ni nada derivado de él: parquet, modelos o probabilidades;
> - los CSV enviados ni otras listas de clientes;
> - el script de envío al bot ni credenciales.

### datos/LEEME.md

> # datos/
>
> Acá va el dataset crudo de la cátedra, `competencia_01_crudo.csv` (492.769.580 bytes, SHA-256
> `c72c8f5c1149f1d972e996c2963c5e3dbb31eb38cfe41c2bb1bbaf847d7a7ca1`). No se incluye en el repositorio.
>
> Se baja del almacenamiento de la cátedra, la dirección que usan los notebooks del curso:
> <https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_01_crudo.csv>. `reproducir.py` controla su
> huella antes de empezar.
>
> También se puede dejar en otro lugar y definir la variable de entorno `COMPETENCIA_01_CRUDO` con su ruta.
>
> `01_preparar_datos.py` escribe en esta carpeta `competencia_01_d01.parquet`, `reparaciones_d01.parquet` y
> `resumen_d01.json`.

### origen/README.md

> # De dónde salen los hiperparámetros y el corte de D
>
> El archivo entregado, `d10dn11000.csv`, se reproduce con `python reproducir.py` desde la raíz. Usa valores fijos:
> 83 hojas, un hessiano de referencia h = 12,791817301585011 y N = 11.000 clientes. Esta carpeta tiene el código que
> produjo esos valores, como pidió la cátedra: si los hiperparámetros salen de una optimización anterior, hay que subir
> también esa optimización y explicar cómo correrla.
>
> No hace falta correr nada de esto para reproducir el archivo entregado. Sirve para reproducir el camino.
>
> ## La cadena
>
> | Paso | Qué se decidió | Script | Qué compara | Tiempo |
> |---|---|---|---|---:|
> | 1. Búsqueda bayesiana (D04, 6-oct) | 40 pruebas de hojas y h con Optuna, sobre la base C7 con la clase K2 | `d04_busqueda.py` | cada prueba contra `esperado/pruebas_d04.csv` | 3 h (las 4 primeras, 17 min) |
> | 2. Selección (D04, 7-oct) | las 5 mejores pruebas, con 5 semillas, contra la configuración vigente; la de mayor mejora fue la prueba 38: **83 hojas y h = 12,79** | `d04_seleccion.py` | la tabla contra `esperado/seleccion_d04.csv` | 10 min |
> | 3. D (D06, 7-oct) | la receta de la prueba 38 sobre las variables con historia (C0 con *lags* y deltas 1 y 2 de todo) | `../06_receta_denicolay.py` | — | 40 min |
> | 4. El corte (D10, 9-oct) | la regla de N, fijada antes de mirar, sobre D en cuatro cortes de validación: **N = 11.000** | `regla_n.py` | G, los arrepentimientos y N contra `esperado/regla_n_d10.json` | 25 min |
> | 5. El archivo | los 11.000 primeros de D | `../07_archivo_d10.py` | `../reproducir.py` lo compara byte por byte | segundos |
>
> **El hessiano:** `min_sum_hessian_in_leaf` = h · filas de entrenamiento / 326.184. 326.184 son las filas de
> entrenamiento de F2 (202103–202104), así que en F2 h es exactamente el mínimo por hoja, y en los demás cortes se
> escala por sus filas.
>
> **Los fijos de la receta,** que no se buscaron: `learning_rate` 0,005, `max_bin` 31, `min_data_in_leaf` 0,
> `feature_fraction` 0,5, `feature_fraction_bynode` 0,2 y sin *bagging*. Son la receta que Gustavo Denicolay compartió en
> el Zulip de la materia. Las 1.000 rondas salen de la búsqueda: las cinco finalistas eligieron 1.000 entre 1.000 y
> 8.000.
>
> **Lo que no es código:**
> - **La D06 eligió D en el tablero público,** con un umbral corregido por la cantidad de candidatos y fijado antes de
>   mirar. Fue después de que la regla local de la D04 (ΔA ≥ 10 M) no dejara ninguna elegible. El tablero no se puede
>   reproducir desde acá. Los números están en `../DECISIONES.md`.
> - **Lo que se probó después de la D06 y no cambió D** (D07 a D10, y la prueba de `max_bin` 255) está resumido en
>   `../DECISIONES.md`.
>
> ## Cómo correrlo
>
> Desde la raíz del repositorio, con el entorno de la reproducción principal más Optuna:
>
> ```bash
> pip install -r origen/requirements.txt
> python 01_preparar_datos.py           # el dataset de trabajo, desde el crudo en datos/ o en COMPETENCIA_01_CRUDO
> python origen/d04_busqueda.py         # paso 1; con --hasta 4 corre sólo las 4 primeras pruebas
> python origen/d04_seleccion.py        # paso 2
> python origen/regla_n.py              # paso 4; necesita también el crudo, por la cohorte de préstamos
> ```
>
> - Cada script termina diciendo si **reproduce** o **no reproduce** los resultados originales, y sale con código 1 si
>   no reproduce.
> - Las salidas van a `origen/salidas/`, que no se versiona.
> - **La búsqueda se reproduce sólo de corrido y en una carpeta vacía.** El muestreador de Optuna no guarda el estado
>   de su generador: si la búsqueda se corta y se reanuda, vuelve a sortear desde la semilla y toma otro camino. Por eso
>   el script se niega a reanudar. Si se corta, hay que borrar `origen/salidas/d04_busqueda/` y empezar de nuevo.
>   `--hasta K` escribe en otra carpeta, `d04_busqueda_hasta<K>/`.
> - `d04_seleccion.py` y `regla_n.py` sí reutilizan las predicciones que ya guardaron, sin volver a controlar con qué
>   datos, código o entorno se hicieron. Si cambia cualquiera de esas tres cosas, o se vuelve a correr la búsqueda, hay
>   que borrar antes `origen/salidas/d04_seleccion/` y `origen/salidas/regla_n/`.
> - `d04_seleccion.py` toma las finalistas de la búsqueda corrida acá si tiene las 40 pruebas; si no, de la original.
>   - Con las finalistas propias, para las semillas 147347 y 322607 usa las predicciones de la búsqueda, como la
>     corrida original.
>   - Con las de la original, entrena las cinco semillas.
>
> **Lo que fija los resultados:**
> - las semillas: 147347 para el muestreador TPE de Optuna, y las de cada script para LightGBM;
> - `deterministic=True`, `force_col_wise=True` y 12 hilos;
> - las versiones de `requirements.txt`.
>
> **Qué puede hacer que no coincida:**
> - en otro sistema operativo o con otra compilación de LightGBM, las probabilidades pueden cambiar en los últimos
>   decimales. Entonces A puede diferir un poco y, en la búsqueda, el muestreador puede tomar otro camino desde la
>   prueba en que difiera;
> - reanudar la búsqueda, por lo explicado arriba.
>
> ## Qué cambia respecto de los scripts que se corrieron
>
> Los originales están en la carpeta de trabajo del autor, que no se publica: `experimentos/d04_busqueda/` y
> `experimentos/d10/`.
> - Las rutas son las de este repositorio.
> - `d04_busqueda.py` no tiene los límites de tiempo del original: 8 horas, o el 8-oct a las 06:00. La corrida original
>   terminó las 40 pruebas antes de llegar a ellos. El de fecha, hoy, cortaría la búsqueda en el acto.
> - `d04_seleccion.py` reentrena la configuración vigente de la D03 en lugar de leer sus predicciones guardadas.
> - `regla_n.py` junta en un archivo el entrenamiento de D en los cuatro cortes (con la receta de
>   `06_receta_denicolay.py`) y la regla de `experimentos/d10/analizar.py`.
>
> **Lo que se comprobó antes de publicar,** en una copia limpia de este repositorio y con este mismo código (10-oct):
> - **`d04_busqueda.py --hasta 4`:** las 4 primeras pruebas (las 3 anclas y la primera al azar) dieron exactamente las de
>   la corrida original. Las 40 no se volvieron a correr. Un segundo intento sobre la misma carpeta se negó a reanudar;
> - **`d04_seleccion.py`:** la tabla de la selección dio igual a la original, con la configuración vigente de la D03
>   reentrenada;
> - **`regla_n.py`:** los siete escenarios dieron exactamente los originales, y N* = 11.000. Las 80 predicciones de D
>   fueron idénticas, bit a bit, a las de la corrida de la D10.

