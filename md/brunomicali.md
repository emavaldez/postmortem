# BrunoMicali — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: BrunoMicali
- Repositorio: https://github.com/BrunoMicali/comp.1
- Link posteado: https://share.google/JVDPtba7jA1OtMcdu
- Commit: af345fc7f9c78c6efb5abf7d6ba8301e38595b02
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/brunomicali/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/brunomicali.json

## Resumen

El repositorio contiene dos archivos: README.md (89 líneas) y entrega_ensamble3prop_50sem_k10750_202108_10750.csv. No contiene código: las carpetas codigo/ y anexo_investigacion/ que el README describe no están en el repositorio, por lo que todo lo que sigue es lo que declara el README. Según ese texto, la predicción sale de un pipeline en Python de cuatro etapas (01_target.py, 03_features.py, 04_entrenar.py, 05_predecir_y_armar.py) lanzado por reproducir.py: agrega clase_ternaria, arma 462 variables (columnas originales, variables de dominio, diferencias contra 1 y 2 meses atrás y 4 proporciones), entrena 150 modelos LightGBM en tres familias de 50 semillas cada una (positivo BAJA+2 con 202103 a 202106; positivo BAJA+1 o BAJA+2 con 202103 a 202107; positivo BAJA+1 con 202103 a 202107), conservando todas las filas positivas y el 10 % del resto, y combina las familias promediando rangos por semilla y después entre las 50 semillas. Se envían los 10.750 primeros clientes de ese ordenamiento para 202108. Los hiperparámetros provienen, según el README, de la prueba 62 de una búsqueda con Optuna. El CSV del repositorio tiene 10.750 números de cliente distintos y su SHA-256 coincide con el que figura en el README.

**Qué entrega.** Un CSV, entrega_ensamble3prop_50sem_k10750_202108_10750.csv, incluido en el repositorio (96.750 bytes): 10.750 líneas, cada una con un número entero, sin encabezado y sin repetidos. Según el README, son numero_de_cliente de la foto 202108.

**Cómo se ejecuta.** Según el README: con Python 3.10 y las versiones de codigo/requirements.txt, entrar a codigo/, correr `pip install -r requirements.txt`, ubicar el dataset en ../datos/competencia_01_crudo.csv o definir la variable de entorno DMEYF_CSV con su ruta, y correr `python reproducir.py`, que ejecuta las etapas en orden y al final compara el SHA-256 del archivo obtenido con el de codigo/sha256_esperado.txt. El README agrega que cada etapa se puede reanudar volviendo a correr el mismo comando. La carpeta codigo/ no está en el repositorio.

## Ficha

- **Lenguajes:** Python
- **Modelos:** LightGBM
- **Clase que entrena:** No se observa en el código (el repositorio no trae código). Según el README, la etiqueta es BAJA+1 si el cliente no aparece en m+1, BAJA+2 si aparece en m+1 pero no en m+2 y CONTINUA en el resto; en 202107 sólo se conoce BAJA+1. Se entrenan tres familias con clase binaria distinta: base (positivo = BAJA+2), baja12_r (positivo = BAJA+1 o BAJA+2) y baja1_r (positivo = BAJA+1). En las dos familias _r, 202107 aporta la BAJA+1.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106, 202107
- **Meses de validación:** 202105, 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código. Según el README, se conservan todas las filas de la clase positiva y el 10 % del resto, de forma determinística por semilla (usa la función hash() de DuckDB 1.5.5), y la probabilidad se corrige por esa tasa.
- **Calidad de datos:** No se observa en el código. El README no describe tratamiento de variables rotas ni de valores faltantes.
- **Drifting:** No se observa en el código. El README no nombra un tratamiento de drifting. Indica que se excluyen 6 variables de calendario que cambian con el foto_mes (config.EXCLUIR) y que la normalización mensual figura en la lista de lo que se probó y no se adoptó.
- **Variables dentro del mes:** No se observa en el código. Según el README, a las columnas originales se suman variables de dominio (tarjetas, payroll, consumo sobre límite y transacciones totales) y 4 proporciones de dónde está el dinero del cliente (comun.ext_proporciones).
- **Variables históricas:** No se observa en el código. Según el README, para cada variable se calculan las diferencias contra 1 y 2 meses atrás (d1 y d2). El README no nombra otras variables históricas. El total declarado, sumando todas las variables, es de 462.
- **Selección de variables:** No se observa en el código. Según el README, se excluyen 6 variables de calendario (config.EXCLUIR); los canaritos figuran en la lista de lo que se probó y no se adoptó.
- **Optimización de hiperparámetros:** No se observa en el código. Según el README, búsqueda con Optuna en anexo_investigacion/codigo/09_experimentos.py (modo optuna; el archivo no está en el repositorio), con validación walk-forward: entrena con 202103 y 202104 y valida en 202106, y entrena con 202103 y valida en 202105. La entrega usa la prueba 62 y reproducir.py no repite la búsqueda.
- **Hiperparámetros finales:** No se observan: el README indica que están en codigo/hiperparametros.json (archivo que no está en el repositorio), que salen de la prueba 62 de Optuna y que se usan 275 rondas (250 × 1,1); el README da como motivo que el entrenamiento final tiene más meses que la validación. También declara deterministic=True y force_row_wise=True.
- **Semillas:** No se observa en el código. Según el README, 50 semillas por familia (150 modelos en total). Los valores de las semillas no figuran en el repositorio.
- **Cantidad de semillas:** 50
- **Ensamble:** No se observa en el código. Según el README, para cada semilla se promedian las posiciones relativas (rangos) de las tres familias (base, baja12_r y baja1_r) y después se promedia entre las 50 semillas.
- **Corte:** Cantidad fija: 10.750 clientes. Según el README, K = 10.750 se eligió mirando el leaderboard público (la ganancia fue pareja entre K = 10.500 y 11.000 y 10.750 es el centro de ese intervalo) y queda fijo en el código. El CSV del repositorio tiene 10.750 líneas.
- **Validación:** No se observa en el código. Según el README, la búsqueda de hiperparámetros usa validación walk-forward: entrena con 202103 y 202104 y valida en 202106, y entrena con 202103 y valida en 202105. El README no indica la métrica de esa validación.
- **Salidas:** Según el README: trabajo/base.parquet (etapa 1), variables por mes en trabajo/fe/ (etapa 2), 150 modelos en trabajo/modelos/ (etapa 3) y la carpeta resultado/ (etapa 4). trabajo/ y resultado/ no están en el repositorio. El repositorio incluye el archivo final entrega_ensamble3prop_50sem_k10750_202108_10750.csv.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)

## Técnicas sólo exploradas

- Estandarización o normalización por mes (`drifting.estandarizacion_por_mes`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Stacking (un modelo sobre las salidas de otros) (`ensamble.stacking`)
- Red neuronal (`modelo.red_neuronal`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: Según el README: Python 3.10, DuckDB 1.5.5 y el resto de las versiones en codigo/requirements.txt (archivo que no está en el repositorio); verificación hecha en Linux x86_64; tiempos de cada etapa medidos con 2 CPU y 3 GB de RAM; unos 1,5 GB de disco para trabajo/. Declara no haberlo probado en Windows nativo ni en Mac con ARM.

## Pasos del camino de la entrega

1. **Decisiones previas que quedan fijas.** Según el README, los hiperparámetros salen de la prueba 62 de una búsqueda con Optuna con validación walk-forward (entrena con 202103 y 202104 y valida en 202106; entrena con 202103 y valida en 202105) y K = 10.750 se eligió mirando el leaderboard público. reproducir.py no repite ninguna de las dos. (`README.md` líneas 68–68; `README.md` líneas 74–79)
2. **Etapa 1: construcción de la clase.** Según el README, 01_target.py agrega clase_ternaria al CSV de la cátedra y guarda trabajo/base.parquet. BAJA+1 si el cliente no aparece en m+1, BAJA+2 si aparece en m+1 pero no en m+2, CONTINUA en el resto; en 202107 sólo se conoce BAJA+1. (`README.md` líneas 31–31; `README.md` líneas 52–52)
3. **Etapa 2: armado de variables.** Según el README, 03_features.py arma las variables por mes y las guarda en trabajo/fe/: columnas originales, variables de dominio (tarjetas, payroll, consumo sobre límite, transacciones totales), diferencias de cada variable contra 1 y 2 meses atrás (d1 y d2) y 4 proporciones de dónde está el dinero del cliente; se excluyen 6 variables de calendario. Total declarado: 462 variables. (`README.md` líneas 32–32; `README.md` líneas 54–54)
4. **Submuestreo de las filas no positivas.** Según el README, se conservan todas las filas de la clase positiva y el 10 % del resto, de forma determinística por semilla con la función hash() de DuckDB, y la probabilidad se corrige por esa tasa. El README no indica en cuál de los scripts se aplica. (`README.md` líneas 15–15; `README.md` líneas 66–66)
5. **Etapa 3: entrenamiento de 150 modelos LightGBM.** Según el README, 04_entrenar.py entrena tres familias con 50 semillas cada una y guarda los modelos en trabajo/modelos/: base (positivo BAJA+2, 202103 a 202106), baja12_r (positivo BAJA+1 o BAJA+2, 202103 a 202107) y baja1_r (positivo BAJA+1, 202103 a 202107). Usa los hiperparámetros de codigo/hiperparametros.json con 275 rondas (250 × 1,1), deterministic=True y force_row_wise=True. (`README.md` líneas 33–33; `README.md` líneas 46–46; `README.md` líneas 56–64; `README.md` líneas 68–68)
6. **Etapa 4: puntaje de 202108 y combinación por rangos.** Según el README, 05_predecir_y_armar.py puntúa 202108 y escribe resultado/. Para cada semilla se promedian las posiciones relativas (rangos) de las tres familias y después se promedia entre las 50 semillas. (`README.md` líneas 34–34; `README.md` líneas 70–70)
7. **Corte y archivo de salida.** Según el README, se envían los 10.750 primeros clientes del ordenamiento, en un CSV sin encabezado con un numero_de_cliente por línea. Como referencia, el README indica que 9.091 clientes tienen probabilidad media mayor a 2,5 % según la familia base. (`README.md` líneas 7–11; `README.md` líneas 72–72)
8. **Comparación con el SHA-256 esperado.** Según el README, reproducir.py compara la suma SHA-256 del archivo obtenido con la de codigo/sha256_esperado.txt e imprime REPRODUCCIÓN EXACTA o EL ARCHIVO NO COINCIDE. El README da además el tamaño (492.769.580 bytes) y el SHA-256 del dataset de entrada, y declara que una corrida desde el CSV crudo en una carpeta vacía dio variables, modelos y archivo final idénticos byte a byte a los originales. (`README.md` líneas 25–27; `README.md` líneas 38–48)

## Archivos

- `README.md` · explicacion · Markdown · 89 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/brunomicali/README.md.txt) — Texto de presentación de la entrega: nombre y SHA-256 del archivo entregado, pasos para reproducirlo con reproducir.py, tabla de las cuatro etapas con sus tiempos, verificación declarada, descripción del método (etiqueta, variables, tres familias de LightGBM, submuestreo, hiperparámetros, puntaje y corte), lo que el script no reproduce y el contenido de la carpeta. Nombra las carpetas codigo/ y anexo_investigacion/, que no están en el repositorio.

## Explicaciones del alumno (texto original)

### README.md

> # DMEyF 2026 · Competencia 01 · Entrega final
>
> Autor: Bruno Micali Dejter
>
> ## Archivo a entregar
>
> `entrega_ensamble3prop_50sem_k10750_202108_10750.csv`
>
> 10.750 `numero_de_cliente` de la foto 202108, uno por línea, sin encabezado, enteros y sin repetidos.
>
> SHA-256 del archivo: `3c85bcbe055f01522bad34dcd7a73e04b7d5f491bb8f0e871f4f1860c46bb6d9`
>
> ## Cómo reproducirlo
>
> Requisitos: Python 3.10 y las versiones exactas de `codigo/requirements.txt`. DuckDB tiene que ser 1.5.5, porque el submuestreo de negativos usa su función `hash()`.
>
> ```bash
> cd codigo
> pip install -r requirements.txt
> # dataset de la cátedra en ../datos/competencia_01_crudo.csv, o bien:
> export DMEYF_CSV=/ruta/a/competencia_01_crudo.csv
> python reproducir.py
> ```
>
> `reproducir.py` corre todas las etapas en orden. Al final compara la suma SHA-256 del archivo obtenido con la esperada (`codigo/sha256_esperado.txt`) e imprime `REPRODUCCIÓN EXACTA` o `EL ARCHIVO NO COINCIDE`. Cada etapa se puede reanudar: si se interrumpe, se vuelve a correr el mismo comando.
>
> Dataset de entrada verificado: `competencia_01_crudo.csv`, 492.769.580 bytes, SHA-256 `c72c8f5c1149f1d972e996c2963c5e3dbb31eb38cfe41c2bb1bbaf847d7a7ca1`.
>
> | Etapa | Script | Qué hace | Tiempo (2 CPU, 3 GB de RAM) |
> |---|---|---|---|
> | 1 | `01_target.py` | Agrega `clase_ternaria` al CSV y guarda `trabajo/base.parquet` | ~30 s |
> | 2 | `03_features.py` | Arma las features por mes y las guarda en `trabajo/fe/` | ~3 min |
> | 3 | `04_entrenar.py` | Entrena 150 modelos LightGBM y los guarda en `trabajo/modelos/` | ~35 min |
> | 4 | `05_predecir_y_armar.py` | Puntúa 202108 y escribe `resultado/` | ~3 min |
>
> Se necesitan unos 1,5 GB de disco para `trabajo/`.
>
> ### Verificación hecha
>
> El paquete se corrió desde el CSV crudo en una carpeta vacía, y los resultados son idénticos byte a byte a los originales en las tres capas:
>
> - **Features:** las de los seis meses (202103 a 202108) coinciden con las del pipeline de trabajo.
> - **Modelos:** los 150 modelos coinciden con los originales.
> - **Archivo final:** el que se genera es el mismo que se entrega.
>
> LightGBM corre con `deterministic=True` y `force_row_wise=True`. Un mismo modelo dio predicciones idénticas con 1, 2 y 4 hilos, así que el resultado no depende de la cantidad de núcleos.
>
> La verificación se hizo en Linux x86_64. En otro sistema operativo o arquitectura (Windows nativo, Mac con ARM) no está probado. Si el hash no coincide ahí, recomiendo correrlo en Linux o WSL con las mismas versiones.
>
> ## Método
>
> **Etiqueta.** BAJA+1 si el cliente no aparece en m+1. BAJA+2 si aparece en m+1 pero no en m+2. CONTINUA en el resto. En 202107 solo se conoce BAJA+1.
>
> **Features (`03_features.py`).** Columnas originales más variables de dominio: tarjetas, payroll, consumo sobre límite y transacciones totales. Para cada variable se calculan además las diferencias contra 1 y 2 meses atrás (d1 y d2). Se excluyen 6 variables de calendario que cambian con el foto_mes (`config.EXCLUIR`). A eso se agregan 4 proporciones de dónde está el dinero del cliente (`comun.ext_proporciones`). En total son 462 variables.
>
> **Ensamble de tres familias LightGBM, 50 semillas cada una (150 modelos):**
>
> | Familia | Positivo | Meses de entrenamiento |
> |---|---|---|
> | base | BAJA+2 | 202103 a 202106 |
> | baja12_r | BAJA+1 o BAJA+2 | 202103 a 202107 |
> | baja1_r | BAJA+1 | 202103 a 202107 |
>
> En las dos familias `_r`, 202107 aporta la BAJA+1 recién conocida.
>
> **Submuestreo.** Se conservan todas las filas de la clase positiva y el 10 % del resto, de forma determinística por semilla. La probabilidad se corrige por esa tasa.
>
> **Hiperparámetros.** Están en `codigo/hiperparametros.json` y salen de la prueba 62 de Optuna. Se usan 275 rondas (250 × 1,1), porque el entrenamiento final tiene más meses que la validación.
>
> **Puntaje.** Para cada semilla se promedian las posiciones relativas (rangos) de las tres familias, y después se promedia entre las 50 semillas.
>
> **Corte.** Se envían los 10.750 primeros. En el leaderboard público la ganancia fue pareja entre K = 10.500 y 11.000, y 10.750 es el centro de esa meseta. Como referencia, 9.091 clientes tienen probabilidad media mayor a 2,5 % según la familia base.
>
> ## Qué no reproduce el script
>
> Hay dos decisiones que se tomaron antes y quedan fijas en el código:
>
> - **Hiperparámetros.** La búsqueda con Optuna está en `anexo_investigacion/codigo/09_experimentos.py`, modo `optuna`. La validación es walk-forward: entrena con 202103 y 202104 y valida en 202106, y entrena con 202103 y valida en 202105.
> - **K = 10.750.** Se eligió mirando el leaderboard público.
>
> ## Contenido de la carpeta
>
> - `codigo/`: el pipeline mínimo que genera el archivo.
>   - `config.py` y `comun.py`: las funciones copiadas literalmente del pipeline de trabajo.
>   - Los scripts de las cuatro etapas, `reproducir.py`, `requirements.txt`, `hiperparametros.json` y `sha256_esperado.txt`.
> - `anexo_investigacion/`: todo el código de trabajo y los informes de los experimentos (rondas 1 a 9).
>   - Incluye lo que se probó y no se adoptó: normalización mensual, canaritos, apilado, validación adversaria, ranking, supervivencia, GRU, entre otros.
>   - No hace falta para reproducir la entrega.
> - `trabajo/` y `resultado/`: los genera la reproducción. No forman parte del zip.

