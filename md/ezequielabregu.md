# Ezequiel Abregu — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: ezequielabregu
- Repositorio: https://github.com/ezequielabregu/DMEyF_competencia_1
- Link posteado: https://github.com/ezequielabregu/DMEyF_competencia_1
- Commit: bc9f2a9257a19fd803c68e3aebeba024e964f854
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/ezequielabregu/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/ezequielabregu.json

## Resumen

Repositorio con siete notebooks de Python (carpeta notebook/), un README, requirements.txt, el JSON de hiperparámetros del modelo final y el CSV entregado con su hash sha256. El camino de la entrega: el 01 lee el crudo con DuckDB, arma clase_ternaria en SQL y guarda un parquet base; el 02 fija 20 semillas (primos de 6 dígitos sorteados a partir de 979201) y el protocolo de backtest (A: entrena 202103–202104 y predice 202106; B: entrena 202103 y predice 202105; ganancia en el máximo de la curva suavizada); el 04 define variantes de limpieza y la entrega usa V5 (sin Master/Visa_fultimo_cierre ni Master/Visa_Finiciomora, y ccajas_depositos en NA en 202105); el 05 agrega variables (historia de 3 meses de 8 variables, señales de comisión y sueldo, ranking dentro del mes de los 73 montos, lag 1 y delta 1 de todas las variables); el 08 busca hiperparámetros de LightGBM con Optuna y escribe la prueba elegida en un JSON; el 03 entrena con 202103–202106, clase binaria con positivo = BAJA+1 o BAJA+2, 20 semillas por corrida, y predice 202108; el 07 promedia las probabilidades de dos corridas del 03 (40 modelos) y escribe los 12.000 clientes de mayor probabilidad promedio.

**Qué entrega.** Un CSV de una columna sin encabezado con 12.000 numero_de_cliente de 202108 (entrega_final/final01fe03x40N12000/final01fe03x40N12000_locro.csv), acompañado de su hash sha256. Según el README, es el archivo que se subió al bot de Zulip como 'submit final01fe03x40N12000' y dio 110,25 en el leaderboard público.

**Cómo se ejecuta.** El README da dos caminos. Camino corto (~1 hora según el README): instalar requirements.txt, ubicar competencia_01_crudo.csv en ../dataset/ respecto de la raíz del repositorio y correr enteros, en orden: 01_pipeline_base sin cambios; 02_linea_base y 04_drift con MODO_RAPIDO = True; 05_variables con MODO_RAPIDO = True, BASE = 'V5', CONFIG = 'z470_bajas', BLOQUES_A_CORRER = [], COMBINACIONES = [['B2', 'B3', 'B4', 'B5']] y REFERENCIA = None; 03_entrega dos veces con HIPER_OPTUNA = 42 y N_ENVIOS = 12_000 (NOMBRE_SUBMIT = 'fe03z470bajasV5B2345Opt42' con JUEGO_SEMILLAS = 1 y 'fe03z470bajasV5B2345Opt42J2' con JUEGO_SEMILLAS = 2); 07_ensamble con esos dos orígenes y N = 12_000; y comparar el sha256 del archivo generado con el incluido. Los hiperparámetros se toman de exp/08_optuna/hiperparametros_p42.json, que viene en el repositorio. Camino completo (~4–5 horas según el README): 02, 04 y 05 con MODO_RAPIDO = False, 08_optuna con N_PRUEBAS = 50 y ELEGIDA = 42, y después los pasos del 03 y el 07. Los notebooks están guardados con otros valores en algunos parámetros (03 con NOMBRE_SUBMIT = 'fe04z470bajasV5B2345Opt44' y HIPER_OPTUNA = 44; 08 con ELEGIDA = 44; 02, 04 y 05 con MODO_RAPIDO = False); el README lista los valores a poner en cada paso.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria: positivo = BAJA+1 o BAJA+2, negativo = CONTINUA (esquema 'bajas' de la configuración 'z470_bajas'). clase_ternaria se calcula en SQL en el 01. La ganancia de los backtests cuenta sólo BAJA+2 como acierto.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202105, 202106
- **Mes que predice:** 202108
- **Submuestreo:** El modelo final entrena con todas las filas con clase de 202103–202106, sin submuestreo. En la búsqueda de Optuna (08) se entrena con todas las bajas y el 20 % de los CONTINUA de 202103–202104, elegidos con un generador de semilla 979201; al pasar a todos los datos, min_data_in_leaf se divide por 0,2.
- **Calidad de datos:** El 01 calcula por variable y mes el porcentaje de nulos y de ceros y lista las variables con algún mes a más de 5 puntos de la mediana. La variante V5 del 04 excluye Master_fultimo_cierre, Visa_fultimo_cierre, Master_Finiciomora y Visa_Finiciomora y pasa ccajas_depositos a NA en 202105 (también sus derivadas). No hay imputación de nulos. numero_de_cliente se lee como BIGINT y las 152 variables pasan a float32.
- **Drifting:** Los 73 montos (columnas que empiezan con 'm', 'Visa_m' o 'Master_m') se reemplazan por su percent_rank dentro del mes (variables rk_, bloque B4). Los lags y deltas de montos del bloque B5 se calculan sobre el ranking con el cero fijo (rk0_: el 0 queda en 0, los positivos en (0, 1] y los negativos en [−1, 0)). Las variables de B2 y B3 se calculan sobre las columnas originales. foto_mes no entra como variable. La exclusión de los préstamos personales (V1) se evalúa en el 04 y no forma parte de V5.
- **Variables dentro del mes:** En la combinación entregada: el reemplazo de cada monto por su ranking dentro del mes (B4) y el indicador tiene_caja_ahorro (mcaja_ahorro > 0) del bloque B3. El bloque B1 (dos cocientes consumo/límite de tarjeta, suma de saldos de tarjetas, cociente saldo/rentabilidad anual y dos rankings) está definido en el 05 y no integra la combinación B2+B3+B4+B5.
- **Variables históricas:** B2 (56): lag 1, lag 2, delta 1, promedio, mínimo, máximo y pendiente (regr_slope contra cliente_antiguedad) sobre los últimos 3 meses, para 8 variables. B3 (17): inicio del pago de comisión, meses con comisión y con sueldo en 3 meses, lags de cpayroll_trx y mpayroll, pérdida de sueldo, consumo Visa sobre el promedio de los 3 meses anteriores, caída de saldo, caja de ahorro en el mes anterior y deltas de transacciones de tarjeta, consultas en caja y call center. B5 (293): lag 1 y delta 1 del resto de las variables.
- **Selección de variables:** No se observa selección por importancia. La lista de variables se arma por bloques: base V5 con los montos reemplazados por su ranking, más B2, B3 y B5, sin las derivadas de columnas excluidas; según el README, 507 variables. numero_de_cliente queda entre las variables. Cada bloque y combinación se compara contra la base con backtests pareados por semilla (Wilcoxon) en el 05.
- **Optimización de hiperparámetros:** Optuna con TPESampler (semilla 979201), N_PRUEBAS = 50, estudio guardado en SQLite. Maximiza la ganancia de meseta de la prueba A (entrena 202103–202104 submuestreado, predice 202106 completo) con una semilla de LightGBM. Espacio: num_leaves 8–512, min_data_in_leaf 10–2.000, learning_rate 0,01–0,1 y num_iterations 200–1.500 en escala logarítmica; feature_fraction 0,2–1,0; bagging_fraction 0,4–1,0. La prueba 0 son los valores de z470. Las 3 de mayor ganancia se validan con todos los datos y 5 semillas en A y C contra z470 (t pareado y Wilcoxon).
- **Hiperparámetros finales:** Prueba 42 de Optuna (exp/08_optuna/hiperparametros_p42.json): objective binary, boosting gbdt, max_bin 31, num_leaves 36, min_data_in_leaf 1.855, learning_rate 0,0423, feature_fraction 0,4027, bagging_fraction 0,9291, bagging_freq 1, num_iterations 637, lambda_l1 0, lambda_l2 0, min_gain_to_split 0, feature_pre_filter false.
- **Semillas:** Semilla primigenia 979201. Juego 1: 20 primos de 6 dígitos sorteados sin reemplazo con numpy.random.default_rng(979201) (02). Juego 2: otros 20 primos, sin repetir los del juego 1, con default_rng([979201, 2]) (03). Los backtests usan las primeras 10 del juego 1 y la validación del 08, las primeras 5. El mismo número alimenta el sampler de Optuna, el submuestreo del 08 y el sorteo del 07.
- **Cantidad de semillas:** 40
- **Ensamble:** Promedio de las probabilidades de 40 modelos LightGBM con los mismos hiperparámetros y variables y distinta semilla: dos corridas del 03 de 20 semillas cada una, promediadas en el 07. El 07 arma además 20 promedios de 20 modelos sorteados entre los 40 (archivos Dist), que no son el archivo entregado.
- **Corte:** Cantidad fija: los 12.000 clientes de mayor probabilidad promedio (N_ENVIOS = 12_000 en el 03, N = 12_000 en el 07). Según el README, N se eligió con el leaderboard público. El 03 tiene un modo 'auto' que toma el promedio de los N de meseta de los backtests A y B, redondeado a 500 y acotado a 8.000–15.000.
- **Validación:** Backtests con dos meses entre entrenamiento y predicción: A (entrena 202103–202104, predice 202106) y B (entrena 202103, predice 202105); C (entrena 202103–202105, predice 202106) como referencia para variables con historia. 10 semillas por configuración; la métrica es la ganancia en el máximo de la curva promedio suavizada con media móvil centrada de 501; las alternativas se comparan semilla por semilla con Wilcoxon. Según el README, también se usa el leaderboard público con 20 semillas.
- **Salidas:** En el repositorio: entrega_final/final01fe03x40N12000/final01fe03x40N12000_locro.csv (12.000 líneas, un numero_de_cliente por línea, sin encabezado) y su .sha256. Al correr, los notebooks escriben data/ (parquets base y de variables), exp/ (curvas .npz, probabilidades .npy por semilla, JSON de configuración, CSV de resumen y comparación) y entregas/ (CSV por semilla, de semillerío, del promedio final, 20 ensambles y registro_submits.md); esas carpetas no están versionadas.

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
- Mínimos y máximos de ventana (`variables.min_max_ventana`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Prueba en más de un mes (backtesting) (`validacion.varios_meses_de_prueba`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Técnicas sólo exploradas

- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: no
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: no
- Entorno declarado: requirements.txt: Python 3.14.7, duckdb 1.5.5, lightgbm 4.7.0, optuna 4.9.0, pandas 2.2.2, numpy 2.4.3, scipy 1.17.1, scikit-learn 1.8.0, matplotlib 3.10.8, nbformat 5.11.1 y jupyter. El README indica ~16 GB de RAM. No se declara sistema operativo ni máquina.

## Pasos del camino de la entrega

1. **Lectura del crudo y controles.** El 01 carga competencia_01_crudo.csv en DuckDB recorriendo el archivo entero para inferir los tipos y con numero_de_cliente declarado BIGINT. Verifica con assert 983.061 filas, 154 columnas, 169.727 clientes, ninguna clave (cliente, mes) duplicada y la cantidad de filas de cada mes de 202103 a 202108. (`notebook/01_pipeline_base.ipynb` líneas 92–119)
2. **Clase ternaria en SQL.** Con un período consecutivo (año × 12 + mes) y los dos períodos siguientes de cada cliente (lead), asigna BAJA+2, BAJA+1, CONTINUA o NULL donde falta futuro. La tabla de cantidades por mes y clase se compara con assert contra valores escritos en el notebook. (`notebook/01_pipeline_base.ipynb` líneas 140–181)
3. **Tipos, parquet base y tabla de calidad.** Pasa las 152 variables a float32, guarda ../data/competencia_01_base.parquet y lo relee para verificarlo. Calcula el porcentaje de nulos y de ceros por variable y mes y lo guarda en un CSV. (`notebook/01_pipeline_base.ipynb` líneas 200–215; `notebook/01_pipeline_base.ipynb` líneas 254–267; `notebook/01_pipeline_base.ipynb` líneas 279–298)
4. **Semillas y configuración compartida.** El 02 sortea 20 primos de 6 dígitos con default_rng(979201) y los guarda en semillas.json. Escribe en configuraciones.json los hiperparámetros z601 y z470, los dos esquemas de clase, las variables excluidas (clase_ternaria y foto_mes), las pruebas A y B, los cortes y los valores de ganancia y costo. (`notebook/02_linea_base.ipynb` líneas 47–101; `notebook/02_linea_base.ipynb` líneas 113–130)
5. **Protocolo de backtest y métrica.** Cada backtest entrena con los meses de la prueba que tienen clase y predice un mes dos meses posterior. La curva de ganancia acumula +1.072.500 por BAJA+2 y −27.500 por el resto en orden de probabilidad descendente; se suaviza con media móvil centrada de 501 y se toma su máximo (N y ganancia). (`notebook/02_linea_base.ipynb` líneas 152–159; `notebook/02_linea_base.ipynb` líneas 183–197; `notebook/02_linea_base.ipynb` líneas 214–229)
6. **Variantes de limpieza y V5.** El 04 arma las variantes V1 a V4 acumulando exclusiones y un pase a NA, y V5 como V4 con los préstamos personales de vuelta: excluye Master_fultimo_cierre, Visa_fultimo_cierre, Master_Finiciomora y Visa_Finiciomora y pasa ccajas_depositos a NA en 202105. Las escribe en variantes.json. (`notebook/04_drift.ipynb` líneas 47–53; `notebook/04_drift.ipynb` líneas 77–96; `notebook/04_drift.ipynb` líneas 116–122)
7. **Variables nuevas.** El 05 define los bloques B1 a B5 y B4c, calcula B1 a B4 con una consulta SQL de ventanas por cliente y B4c y B5 en numpy, y escribe ../data/competencia_01_fe.parquet con el mismo orden de filas que el parquet base. (`notebook/05_variables.ipynb` líneas 171–229; `notebook/05_variables.ipynb` líneas 232–239; `notebook/05_variables.ipynb` líneas 251–298)
8. **Lista de variables de la combinación B2+B3+B4+B5.** variables_de parte de las variables de V5, reemplaza cada monto por su ranking rk_ y agrega las variables de B2, B3 y B5 que no derivan de columnas excluidas. La lista de cada corrida se guarda en bloques.json, que leen el 03 y el 08. (`notebook/05_variables.ipynb` líneas 369–408)
9. **Búsqueda de hiperparámetros con Optuna.** El 08 entrena con todas las bajas y el 20 % de los CONTINUA de 202103–202104 y evalúa en 202106 completo. El estudio usa TPESampler con semilla 979201, encola z470 como prueba 0 y maximiza la ganancia de meseta. (`notebook/08_optuna.ipynb` líneas 113–127; `notebook/08_optuna.ipynb` líneas 139–173)
10. **Validación de las candidatas y JSON de hiperparámetros.** Las 3 pruebas de mayor ganancia se reentrenan con todos los datos (min_data_in_leaf dividido por 0,2) y 5 semillas en A y C, y se comparan contra z470 con t pareado y Wilcoxon. La prueba elegida se escribe en hiperparametros_p<prueba>.json; el repositorio incluye el de la prueba 42. (`notebook/08_optuna.ipynb` líneas 201–236; `notebook/08_optuna.ipynb` líneas 246–270; `notebook/08_optuna.ipynb` líneas 279–289; `exp/08_optuna/hiperparametros_p42.json` líneas 1–50)
11. **Parámetros y controles del modelo final.** El 03 lee la configuración y las semillas del 02, la variante del 04, la lista de variables del 05 y los hiperparámetros del 08, y verifica con assert que el nombre del submit refleje esos valores. Para el segundo juego de semillas sortea 20 primos nuevos con default_rng([979201, 2]). (`notebook/03_entrega.ipynb` líneas 49–66; `notebook/03_entrega.ipynb` líneas 135–193)
12. **Entrenamiento y predicción de 202108.** Entrena con las filas con clase de 202103 a 202106, etiqueta 1 si la clase es BAJA+1 o BAJA+2, un LightGBM por semilla (20 por corrida) con los mismos hiperparámetros, y guarda las probabilidades de 202108 de cada semilla. (`notebook/03_entrega.ipynb` líneas 204–237; `notebook/03_entrega.ipynb` líneas 247–263)
13. **Archivos por semilla, semillerío y controles de formato.** Escribe un CSV por semilla con los N clientes de mayor probabilidad y uno con los N de mayor promedio de las 20. Relee cada archivo y verifica enteros, cantidad de líneas, duplicados y pertenencia a 202108. (`notebook/03_entrega.ipynb` líneas 274–294; `notebook/03_entrega.ipynb` líneas 309–325)
14. **Promedio de las 40 semillas y corte en 12.000.** El 07 carga las probabilidades de las dos corridas del 03, verifica que reproducen sus semilleríos, promedia los 40 modelos y escribe final01fe03x40N12000_locro.csv con los 12.000 clientes de mayor promedio. (`notebook/07_ensamble.ipynb` líneas 29–33; `notebook/07_ensamble.ipynb` líneas 60–87; `notebook/07_ensamble.ipynb` líneas 98–103; `notebook/07_ensamble.ipynb` líneas 114–134)

## Archivos

- `requirements.txt` · configuracion · Texto · 11 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ezequielabregu/requirements.txt.txt) — Versiones de las librerías con las que, según su primera línea, se generó la entrega final (Python 3.14.7): duckdb 1.5.5, lightgbm 4.7.0, optuna 4.9.0, pandas 2.2.2, numpy 2.4.3, scipy 1.17.1, scikit-learn 1.8.0, matplotlib 3.10.8, nbformat 5.11.1 y jupyter sin versión.
- `README.md` · explicacion · Markdown · 128 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ezequielabregu/README.md.txt) — Presentación de la entrega: tabla con las elecciones del modelo final, requisitos, pasos para reproducirla (camino corto y camino completo), qué hace cada notebook, una tabla de puntajes del leaderboard público por paso y la estructura del repositorio.
- `notebook/05_variables.ipynb` · principal · Jupyter (python) · 632 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ezequielabregu/notebook/05_variables.ipynb.txt) — Define los bloques de variables nuevas (B1 a B5 y B4c), arma el parquet que las contiene, escribe en bloques.json la lista de variables de cada combinación y compara bloques y combinaciones en los backtests A, B y C.
- `notebook/01_pipeline_base.ipynb` · principal · Jupyter (python) · 317 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ezequielabregu/notebook/01_pipeline_base.ipynb.txt) — Lee el dataset crudo con DuckDB, calcula clase_ternaria en SQL, fija los tipos, verifica contra valores esperados y guarda el parquet base y una tabla de nulos y ceros por variable y mes.
- `notebook/07_ensamble.ipynb` · principal · Jupyter (python) · 150 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ezequielabregu/notebook/07_ensamble.ipynb.txt) — Promedia las probabilidades por semilla guardadas por dos corridas del 03 (40 modelos) y escribe el CSV entregado con los 12.000 clientes de mayor promedio, además de 20 archivos con promedios de 20 modelos sorteados.
- `notebook/02_linea_base.ipynb` · principal · Jupyter (python) · 354 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ezequielabregu/notebook/02_linea_base.ipynb.txt) — Genera las 20 semillas y el archivo de configuración que leen los demás notebooks, y mide en los backtests A y B cuatro configuraciones de LightGBM con hiperparámetros fijos (z601 y z470, cada uno con dos esquemas de clase).
- `notebook/08_optuna.ipynb` · principal · Jupyter (python) · 289 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ezequielabregu/notebook/08_optuna.ipynb.txt) — Busca hiperparámetros de LightGBM con Optuna sobre las variables de la combinación B2+B3+B4+B5, valida las candidatas contra z470 con todos los datos y escribe el JSON de la prueba elegida, que lee el 03.
- `notebook/04_drift.ipynb` · principal · Jupyter (python) · 326 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ezequielabregu/notebook/04_drift.ipynb.txt) — Define las variantes de limpieza V0 a V5 (variables excluidas y variables pasadas a NA en un mes), las escribe en variantes.json y las compara en los backtests A y B semilla por semilla.
- `notebook/03_entrega.ipynb` · principal · Jupyter (python) · 363 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ezequielabregu/notebook/03_entrega.ipynb.txt) — Entrena el modelo final con 202103–202106 y 20 semillas, predice 202108, guarda las probabilidades por semilla y escribe un CSV por semilla y uno de semillerío con los N clientes de mayor probabilidad. Se corre una vez por juego de semillas.
- `exp/08_optuna/hiperparametros_p42.json` · configuracion · JSON · 50 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/ezequielabregu/exp/08_optuna/hiperparametros_p42.json.txt) — Hiperparámetros de LightGBM de la prueba 42 del estudio de Optuna, con los datos de su validación. Lo escribe el 08 y lo lee el 03 cuando HIPER_OPTUNA = 42.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### notebook/05_variables.ipynb

Define los bloques de variables nuevas (B1 a B5 y B4c), arma el parquet que las contiene, escribe en bloques.json la lista de variables de cada combinación y compara bloques y combinaciones en los backtests A, B y C.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–28] Celdas de texto de presentación. Describen los bloques de variables (B1 del mismo
#   mes, B2 historia de 8 variables, B3 señales de comisión, sueldo, consumo y saldo, B4 ranking de los 73
#   montos dentro del mes, B4c ranking con el cero fijo, B5 lag 1 y delta 1 de todas las variables), las pruebas
#   A, B y C (C: entrena 202103–202105 y predice 202106, sólo de referencia) y los parámetros.
#%% celda 1 [texto]
# 05 · Variables nuevas (experimento #3)

**Etapa 5 del plan** (`fichas/etapa_5_variables_nuevas.md`). Mide, bloque por bloque, si las variables nuevas **suben la ganancia**, con el mismo protocolo del `02` y el `04`: 10 semillas, meseta suavizada, ganancia solo con `BAJA+2` y comparación pareada con Wilcoxon.

| Bloque | Qué es | Variables |
|---|---|---:|
| **B1** | Del mismo mes (TP4): uso del límite de tarjeta, saldo total de tarjetas, saldo / rentabilidad, ranking de `ctrx_quarter` y de `mcuentas_saldo` dentro del mes | 6 |
| **B2** | Historia del TP4: `lag_1`, `lag_2`, `delta_1`, `avg3`, `min3`, `max3` y `slope3` de 8 variables. **Ventana corregida a 3 meses** (el TP4 tomaba 4) | 56 |
| **B3** | Señales del video de Miranda: comisión, sueldo, consumo de tarjeta comparado con los meses anteriores, saldo, caja de ahorro, sucursal y call center | 17 |
| **B4** | Los 73 montos **reemplazados** por su ranking dentro del mes (contra la inflación, el aguinaldo y la suba de la comisión) | 73 reemplazadas |
| **B4c** | Igual que B4, pero con el ranking **con el cero fijo** (cátedra 2024, `rank_cero_fijo`): el 0 queda en 0, los positivos van a (0, 1] y los negativos a [−1, 0). Conserva el cero y el signo. No se combina con B4 | 73 reemplazadas |
| **B5** | Lag 1 y delta 1 de **todas** las variables ("meter todo", Bolaños; flujo de la cátedra 2024). Para los montos, sobre su ranking con el cero fijo, para que el drift no vuelva a entrar por el lag. No repite los que ya están en B2 y B3 | 293 |

**Pruebas:**
- **A** (entrena `202103`–`202104`, predice `202106`) y **B** (entrena `202103`, predice `202105`), como siempre.
- **C** (entrena `202103`–`202105`, predice `202106`), **solo de referencia** y solo para los bloques con historia (B2, B3, B5). No tiene el hueco de dos meses, pero es la única prueba con historia completa en el entrenamiento: B entrena solo con marzo, donde toda la historia está vacía.

**Cada bloque se compara contra la base**, y las combinaciones (`COMBINACIONES`) también **contra la `REFERENCIA`**, la mejor combinación hasta ahora (`B2+B3+B4`). Lo ya corrido no se repite.

#%% celda 2 [texto]
## 1. Parámetros

- **`BASE` (obligatoria):** `'linea_base'` (las variables del `02`) o una variante del `04`, por ejemplo `'V5'`. Las curvas de la base en A y B se leen del `02` o del `04`; la de C se corre acá.
- **`MODO_RAPIDO = True`** corre 1 semilla, para medir el tiempo. Con `False` corre las 10. Retoma si se corta.
- **`COMBINACIONES`:** una lista de combinaciones de bloques, por ejemplo `[['B2', 'B3', 'B4'], ['B2', 'B3', 'B4c']]`. Lo ya corrido no se repite.
- **`REFERENCIA`:** la combinación contra la que se comparan las demás, además de la base (tiene que estar en `COMBINACIONES`).
- **`REHACER_FE`:** el parquet de variables nuevas se arma una sola vez. Si cambia la definición de un bloque, se rearma solo.

# [Anotación · líneas 30–67] Importa las librerías y define los parámetros con los que está guardado el
#   notebook: MODO_RAPIDO = False, BASE = 'V5', CONFIG = 'z470_bajas', bloques a correr por separado B1 a B4,
#   cuatro combinaciones (B2+B3+B4, B2+B3+B4c, B2+B3+B4c+B5 y B2+B3+B4+B5), REFERENCIA = 'B2+B3+B4', la prueba C
#   y las rutas del parquet base y del parquet de variables nuevas (../data/competencia_01_fe.parquet).
#%% celda 3 [código]
from itertools import product
from pathlib import Path
import json
import time
import warnings

import duckdb
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.metrics import roc_auc_score

warnings.filterwarnings('ignore', message='.*ChainedAssignmentError.*')  # falso positivo pandas 2.2 + Py 3.14

# --- Parámetros -------------------------------------------------------------
MODO_RAPIDO = False              # True: 1 semilla (medir tiempos) · False: 10 semillas
BASE = 'V5'                     # <- OBLIGATORIO: 'linea_base' o una variante del 04 (decidido: 'V5')
CONFIG = 'z470_bajas'           # decisión 2 de la ficha
BLOQUES_A_CORRER = ['B1', 'B2', 'B3', 'B4']          # cada uno solo, contra la base (ya corridos: no se repiten)
COMBINACIONES = [['B2', 'B3', 'B4'],                   # la adoptada (ya corrida)
                 ['B2', 'B3', 'B4c'],                  # paso 2: ranking con el cero fijo
                 ['B2', 'B3', 'B4c', 'B5'],            # paso 2: + lag 1 y delta 1 de todas las variables
                 ['B2', 'B3', 'B4', 'B5']]             # paso 2: ranking simple + historia de todas
REFERENCIA = 'B2+B3+B4'         # la mejor hasta ahora: las combinaciones se comparan también contra esta
PRUEBA_C = {'train': [202103, 202104, 202105], 'test': 202106}   # referencia: sin el hueco de dos meses
REHACER_FE = False              # True: vuelve a armar el parquet de variables nuevas

BASE_PARQUET = Path('../data/competencia_01_base.parquet')
FE_PARQUET = Path('../data/competencia_01_fe.parquet')
EXP02 = Path('../exp/02_linea_base')
EXP04 = Path('../exp/04_drift')
EXP = Path('../exp/05_variables')
CURVAS = EXP / 'curvas'
LARGO_CURVA = 25_000
# -----------------------------------------------------------------------------

# [Anotación · líneas 69–108] Lee del 02 hiperparámetros, clases, pruebas, cortes y las primeras 10 semillas,
#   y del 04 la definición de la base elegida (variables excluidas y pases a NA por mes). Valida BASE y CONFIG,
#   marca B2, B3 y B5 como bloques con historia, impide combinar B4 con B4c y arma los nombres de las corridas
#   uniendo los bloques con '+'. pruebas_de devuelve A y B, y también C si la corrida incluye un bloque con
#   historia.
assert BASE_PARQUET.exists(), 'Falta el dataset base: correr 01_pipeline_base'
assert (EXP02 / 'configuraciones.json').exists(), 'Falta la salida del 02'
CURVAS.mkdir(parents=True, exist_ok=True)

config02 = json.loads((EXP02 / 'configuraciones.json').read_text())
HIPERPARAMETROS = config02['hiperparametros']
CLASES = config02['clases']
PRUEBAS = {**config02['pruebas'], 'C': PRUEBA_C}
CORTES = config02['cortes']
VENTANA_SUAVIZADO = config02['ventana_suavizado']
GANANCIA_ACIERTO, COSTO_ESTIMULO = config02['ganancia_acierto'], config02['costo_estimulo']

SEMILLAS_BACKTEST = json.loads((EXP02 / 'semillas.json').read_text())['semillas'][:10]
SEMILLAS_A_USAR = SEMILLAS_BACKTEST[:1] if MODO_RAPIDO else SEMILLAS_BACKTEST

# La base se elige siempre a propósito (decisión 1 de la ficha)
variantes_04 = json.loads((EXP04 / 'variantes.json').read_text()) if (EXP04 / 'variantes.json').exists() else {}
assert BASE == 'linea_base' or (BASE in variantes_04 and BASE != 'V0'), \
    f"BASE tiene que ser 'linea_base' o una de {sorted(set(variantes_04) - {'V0'})}"
DEF_BASE = {'excluir': [], 'na_en_mes': {}} if BASE == 'linea_base' else variantes_04[BASE]

HIPER, CLASE = CONFIG.split('_', 1)
assert HIPER in HIPERPARAMETROS and CLASE in CLASES, f'Configuración desconocida: {CONFIG}'

HISTORIA = {'B2', 'B3', 'B5'}    # bloques que usan meses anteriores
TODOS = {'B1', 'B2', 'B3', 'B4', 'B4c', 'B5'}
assert set(BLOQUES_A_CORRER) | {b for c in COMBINACIONES for b in c} <= TODOS
assert not any({'B4', 'B4c'} <= set(c) for c in COMBINACIONES), 'B4 y B4c reemplazan los mismos montos: van por separado'
NOMBRES = list(BLOQUES_A_CORRER) + ['+'.join(sorted(c)) for c in COMBINACIONES]
assert REFERENCIA is None or REFERENCIA in NOMBRES, 'REFERENCIA tiene que estar entre las corridas'


def pruebas_de(nombre):
    # A y B siempre; C también si incluye un bloque con historia
    return ['A', 'B'] + (['C'] if HISTORIA & set(nombre.split('+')) else [])


NECESITA_C = any('C' in pruebas_de(n) for n in NOMBRES)
print(f'>>> BASE: {BASE} · excluye: {DEF_BASE["excluir"] or "—"} · NA: {DEF_BASE["na_en_mes"] or "—"}')
print(f'Configuración: {CONFIG} · semillas: {len(SEMILLAS_A_USAR)} · a correr: {NOMBRES}')

# [Anotación · líneas 110–126] Celda de texto que describe cómo se arman las variables: tres ventanas por
#   cliente que sólo miran hacia atrás (fila anterior, últimos 3 meses con el actual, 3 meses anteriores sin el
#   actual), el tratamiento de nulos en rankings, contadores y flags, y que B1 a B4 se calculan en SQL y B4c y
#   B5 en numpy.
#%% celda 4 [texto]
## 2. Variables nuevas en SQL

Todo se arma en DuckDB sobre el parquet base, con ventanas que **solo miran hacia atrás**:
- `vc`: las filas del cliente ordenadas por mes (para `lag`);
- `v3`: los últimos **3** meses, el actual incluido (`rows between 2 preceding and current row`);
- `vprev3`: los 3 meses **anteriores**, sin el actual (para comparar el mes contra su historia).

Detalles:
- **Rankings** (`percent_rank` dentro del mes): los nulos quedan nulos y no corren el ranking de los demás.
- **Contadores de 3 meses** (`meses_pagando_comision_3`, `meses_con_sueldo_3`): quedan vacíos si el cliente tiene menos de 3 meses de historia. Así no se confunde "pagó 1 de 1 mes" con "pagó 1 de 3".
- **Flags contra el mes anterior** (`empieza_comision`, `perdio_sueldo`, `cae_saldo`): vacíos si no hay mes anterior.
- **B1–B4 se arman en SQL; B4c y B5, en numpy.** Con ~150 rankings y ~300 lags en una sola consulta, DuckDB se quedaba sin memoria (cada ranking ordena todas las filas con todas sus columnas). En numpy es directo, y el parquet se escribe igual con DuckDB.
- **Ranking con el cero fijo** (B4c): el 0 queda en 0; los positivos, su ranking entre los positivos del mes dividido por cuántos son (en (0, 1]); los negativos, lo mismo con signo menos, contando desde el más cercano a 0 (el más negativo queda en −1). Empates: el rango mayor.
- **Lags de B5:** por cliente, la fila anterior ordenada por mes, igual que el `lag` de SQL (en los intermitentes, el último mes en que estuvieron).
- **B5:** `lag_1`/`delta_1` de cada variable que no es monto, y `l1_rk0_`/`d1_rk0_` del ranking con el cero fijo de cada monto. Sin `numero_de_cliente`, `cliente_antiguedad` ni `cliente_edad`, y sin los que ya están en B2 y B3.
- Si la base saca una variable (por ejemplo, los préstamos), **sus derivadas tampoco entran** (`FUENTES`).

# [Anotación · líneas 128–168] Abre DuckDB y define dos macros: ratio_seguro (devuelve NULL si el divisor es
#   nulo o 0 y toma el numerador nulo como 0) y suma_sin_null. MONTOS son las columnas cuyo nombre empieza con
#   'm', 'Visa_m' o 'Master_m'. Define los registros de bloques y de columnas de origen de cada variable
#   (FUENTES) y los generadores de expresiones: percent_rank dentro del mes con nulos preservados, lag por
#   cliente, flag 1/0 contra el mes anterior y contador sobre 3 meses que queda vacío si el cliente tiene menos
#   de 3 filas.
#%% celda 5 [código]
con = duckdb.connect()
con.execute('CREATE OR REPLACE MACRO ratio_seguro(a, b) AS CASE WHEN b IS NULL OR b = 0 THEN NULL ELSE ifnull(a, 0) / b END')
con.execute('CREATE OR REPLACE MACRO suma_sin_null(a, b) AS ifnull(a, 0) + ifnull(b, 0)')

COLUMNAS_BASE = con.sql(f"describe select * from read_parquet('{BASE_PARQUET.as_posix()}')").df()['column_name'].tolist()
MONTOS = [c for c in COLUMNAS_BASE if c.startswith(('m', 'Visa_m', 'Master_m'))]

BLOQUES = {b: [] for b in ['B1', 'B2', 'B3', 'B4', 'B4c', 'B5']}
FUENTES = {}          # variable nueva -> columnas originales que usa
lineas_sql = []       # B1–B4 (SQL)
NUMPY = {}            # B4c y B5: variable nueva -> (tipo, columna de origen)


def nueva(bloque, nombre, sql, fuentes):
    BLOQUES[bloque].append(nombre)
    FUENTES[nombre] = sorted(fuentes)
    lineas_sql.append(f'({sql})::FLOAT as {nombre}')


def nueva_numpy(bloque, nombre, tipo, origen, fuentes):
    BLOQUES[bloque].append(nombre)
    FUENTES[nombre] = sorted(fuentes)
    NUMPY[nombre] = (tipo, origen)


def rank_mes(x):
    return f'case when {x} is null then null else percent_rank() over (partition by foto_mes, {x} is null order by {x}) end'


def lag(x, k=1):
    return f'lag({x}, {k}) over vc'


def flag_vs_anterior(x, condicion):
    # 1/0 según la condición; vacío si falta el mes actual o el anterior
    return f'case when {x} is null or {lag(x)} is null then null when {condicion} then 1 else 0 end'


def meses_de_3(condicion):
    return f'case when count(*) over v3 = 3 then sum(case when {condicion} then 1 else 0 end) over v3 end'


# [Anotación · líneas 171–189] B1 (6 variables del mismo mes): consumo sobre límite de compra de Visa y de
#   Master, suma de los saldos totales de las dos tarjetas, saldo de cuentas sobre rentabilidad anual, y ranking
#   dentro del mes de ctrx_quarter y de mcuentas_saldo. B2 (56 variables): para ctrx_quarter, mcuentas_saldo,
#   mpasivos_margen, mcaja_ahorro, mprestamos_personales, mcuenta_corriente, mrentabilidad_annual y
#   mtarjeta_visa_consumo calcula lag 1, lag 2, delta 1, promedio, mínimo y máximo de los últimos 3 meses y la
#   pendiente (regr_slope contra cliente_antiguedad) en esa ventana.
# B1 · del mismo mes (TP4)
nueva('B1', 'ratio_uso_limite_visa', 'ratio_seguro(mtarjeta_visa_consumo, Visa_mlimitecompra)', ['mtarjeta_visa_consumo', 'Visa_mlimitecompra'])
nueva('B1', 'ratio_uso_limite_master', 'ratio_seguro(mtarjeta_master_consumo, Master_mlimitecompra)', ['mtarjeta_master_consumo', 'Master_mlimitecompra'])
nueva('B1', 'tc_saldo_total', 'suma_sin_null(Master_msaldototal, Visa_msaldototal)', ['Master_msaldototal', 'Visa_msaldototal'])
nueva('B1', 'ratio_saldo_rentabilidad', 'ratio_seguro(mcuentas_saldo, mrentabilidad_annual)', ['mcuentas_saldo', 'mrentabilidad_annual'])
nueva('B1', 'prank_ctrx_quarter', rank_mes('ctrx_quarter'), ['ctrx_quarter'])
nueva('B1', 'prank_mcuentas_saldo', rank_mes('mcuentas_saldo'), ['mcuentas_saldo'])

# B2 · historia del TP4, con la ventana corregida a 3 meses
CAMPOS_B2 = ['ctrx_quarter', 'mcuentas_saldo', 'mpasivos_margen', 'mcaja_ahorro',
             'mprestamos_personales', 'mcuenta_corriente', 'mrentabilidad_annual', 'mtarjeta_visa_consumo']
for c in CAMPOS_B2:
    nueva('B2', f'lag_1_{c}', lag(c), [c])
    nueva('B2', f'lag_2_{c}', lag(c, 2), [c])
    nueva('B2', f'delta_1_{c}', f'{c} - {lag(c)}', [c])
    nueva('B2', f'avg3_{c}', f'avg({c}) over v3', [c])
    nueva('B2', f'min3_{c}', f'min({c}) over v3', [c])
    nueva('B2', f'max3_{c}', f'max({c}) over v3', [c])
    nueva('B2', f'slope3_{c}', f'regr_slope({c}, cliente_antiguedad) over v3', [c, 'cliente_antiguedad'])

# [Anotación · líneas 191–209] B3 (17 variables): flag de que mcomisiones_mantenimiento pasa de no positivo a
#   positivo, cantidad de meses con comisión positiva en 3 meses y delta 1 de la comisión; lag 1 y lag 2 de
#   cpayroll_trx y mpayroll, flag de pérdida de sueldo y meses con sueldo en 3 meses; consumo Visa del mes sobre
#   el promedio de los 3 meses anteriores; delta 1 de las transacciones de Visa y Master; flag de caída del
#   saldo; indicador de caja de ahorro positiva en el mes y en el mes anterior; delta 1 de ccajas_consultas y
#   ccallcenter_transacciones.
# B3 · señales del video de Miranda (informe técnico §6–7)
cm = 'mcomisiones_mantenimiento'
nueva('B3', 'empieza_comision', flag_vs_anterior(cm, f'{cm} > 0 and {lag(cm)} <= 0'), [cm])
nueva('B3', 'meses_pagando_comision_3', meses_de_3(f'{cm} > 0'), [cm])
nueva('B3', f'delta_1_{cm}', f'{cm} - {lag(cm)}', [cm])
for c in ['cpayroll_trx', 'mpayroll']:
    nueva('B3', f'lag_1_{c}', lag(c), [c])
    nueva('B3', f'lag_2_{c}', lag(c, 2), [c])
nueva('B3', 'perdio_sueldo', flag_vs_anterior('cpayroll_trx', f"{lag('cpayroll_trx')} > 0 and cpayroll_trx = 0"), ['cpayroll_trx'])
nueva('B3', 'meses_con_sueldo_3', meses_de_3('cpayroll_trx > 0'), ['cpayroll_trx'])
nueva('B3', 'consumo_visa_vs_prom3', 'ratio_seguro(mtarjeta_visa_consumo, avg(mtarjeta_visa_consumo) over vprev3)', ['mtarjeta_visa_consumo'])
for c in ['ctarjeta_visa_transacciones', 'ctarjeta_master_transacciones']:
    nueva('B3', f'delta_1_{c}', f'{c} - {lag(c)}', [c])
nueva('B3', 'cae_saldo', flag_vs_anterior('mcuentas_saldo', f"mcuentas_saldo < {lag('mcuentas_saldo')}"), ['mcuentas_saldo'])
tiene_ca = 'case when mcaja_ahorro is null then null when mcaja_ahorro > 0 then 1 else 0 end'
nueva('B3', 'tiene_caja_ahorro', tiene_ca, ['mcaja_ahorro'])
nueva('B3', 'tenia_caja_ahorro', lag(tiene_ca), ['mcaja_ahorro'])
for c in ['ccajas_consultas', 'ccallcenter_transacciones']:
    nueva('B3', f'delta_1_{c}', f'{c} - {lag(c)}', [c])

# [Anotación · líneas 211–229] B4: una variable rk_ por cada monto con su percent_rank dentro del mes. B4c:
#   una variable rk0_ por cada monto con el ranking con el cero fijo. B5: lag 1 y delta 1 de cada columna salvo
#   numero_de_cliente, foto_mes, clase_ternaria, cliente_antiguedad y cliente_edad; para los montos se calculan
#   sobre rk0_ (prefijos l1_rk0_ y d1_rk0_) y se omiten los nombres que ya existen en B2 y B3.
# B4 · montos → ranking dentro del mes (reemplazan al monto)
for c in MONTOS:
    nueva('B4', f'rk_{c}', rank_mes(c), [c])

# B4c · montos → ranking con el cero fijo (reemplazan al monto) · numpy
for c in MONTOS:
    nueva_numpy('B4c', f'rk0_{c}', 'rank0', c, [c])

# B5 · lag 1 y delta 1 de todas las variables (montos: sobre su ranking con el cero fijo) · numpy
ya_hechas = set(BLOQUES['B2']) | set(BLOQUES['B3'])
for c in COLUMNAS_BASE:
    if c in ('numero_de_cliente', 'foto_mes', 'clase_ternaria', 'cliente_antiguedad', 'cliente_edad'):
        continue
    origen = f'rk0_{c}' if c in MONTOS else c
    prefijos = ('l1_rk0_', 'd1_rk0_') if c in MONTOS else ('lag_1_', 'delta_1_')
    for prefijo, tipo in zip(prefijos, ('lag', 'delta')):
        nombre = f'{prefijo}{c}'
        if nombre not in ya_hechas:
            nueva_numpy('B5', nombre, tipo, origen, [c])


# [Anotación · líneas 232–250] rank_cero_fijo deja el 0 en 0, asigna a los positivos su rango dentro del mes
#   dividido por la cantidad de positivos (empates con el rango mayor) y a los negativos lo mismo con signo
#   menos. Verifica la cantidad de variables por bloque (B1 6, B2 56, B3 17, B4 73, B4c 73, B5 293) y que no
#   haya nombres repetidos, y compara la lista de columnas esperada con la del parquet existente.
def rank_cero_fijo(x, meses):
    # 0 → 0; positivos: rango (empates: el mayor) / cantidad de positivos del mes; negativos: igual, con signo menos
    s, out = pd.Series(x), np.full(len(x), np.nan, dtype=np.float32)
    out[s.to_numpy() == 0] = 0
    for signo in (1, -1):
        m = (s * signo > 0).to_numpy()
        out[m] = signo * (s[m] * signo).groupby(meses[m]).rank(method='max', pct=True).to_numpy()
    return out

# Control 2 de la ficha
cantidades = {b: len(v) for b, v in BLOQUES.items()}
print('Variables nuevas por bloque:', cantidades)
assert cantidades == {'B1': 6, 'B2': 56, 'B3': 17, 'B4': 73, 'B4c': 73, 'B5': 293}
NUEVAS = [v for b in BLOQUES.values() for v in b]
assert len(NUEVAS) == len(set(NUEVAS)) and not set(NUEVAS) & set(COLUMNAS_BASE)

esperadas = COLUMNAS_BASE + [v for v in NUEVAS if v not in NUMPY] + [v for v in NUEVAS if v in NUMPY]
existentes = (con.sql(f"describe select * from read_parquet('{FE_PARQUET.as_posix()}')").df()['column_name'].tolist()
              if FE_PARQUET.exists() else None)
# [Anotación · líneas 251–300] Si el parquet no existe, cambió su lista de columnas o REHACER_FE es True, lo
#   arma: una consulta SQL agrega las variables de B1 a B4 con las tres ventanas por cliente y conserva el orden
#   de filas del parquet base; después, en numpy, ordena por cliente y mes, calcula los rk0_ y los lags y deltas
#   de B5 (el lag queda NaN en la primera fila de cada cliente), concatena las columnas y escribe
#   competencia_01_fe.parquet.
if REHACER_FE or existentes != esperadas:
    t0 = time.time()
    separador = '\n        , '
    # B1–B4 en SQL
    tabla = con.sql(f'''
        select * exclude (file_row_number)
        , {separador.join(lineas_sql)}
        from read_parquet('{BASE_PARQUET.as_posix()}', file_row_number = true)
        window
            vc as (partition by numero_de_cliente order by foto_mes),
            v3 as (partition by numero_de_cliente order by foto_mes rows between 2 preceding and current row),
            vprev3 as (partition by numero_de_cliente order by foto_mes rows between 3 preceding and 1 preceding)
        order by file_row_number          -- mismo orden de filas que el parquet base (LightGBM depende del orden)
    ''').df()
    print(f'B1–B4 (SQL): {tabla.shape[1]} columnas · {time.time() - t0:.0f} s')

    # B4c y B5 en numpy
    meses_fe = tabla['foto_mes'].to_numpy()
    orden = np.lexsort((meses_fe, tabla['numero_de_cliente'].to_numpy()))     # por cliente y mes
    cli = tabla['numero_de_cliente'].to_numpy()[orden]
    sin_anterior = np.r_[True, cli[1:] != cli[:-1]]                           # primera fila de cada cliente

    def lag_1(v):
        vs = v[orden].astype(np.float32)
        l = np.r_[np.float32(np.nan), vs[:-1]]
        l[sin_anterior] = np.nan
        out = np.empty_like(l)
        out[orden] = l
        return out

    nuevas_numpy = {}
    for nombre, (tipo, origen) in NUMPY.items():
        if tipo == 'rank0':
            nuevas_numpy[nombre] = rank_cero_fijo(tabla[origen].to_numpy(), meses_fe)
    for nombre, (tipo, origen) in NUMPY.items():
        if tipo != 'rank0':
            v = (nuevas_numpy[origen] if origen in nuevas_numpy else tabla[origen].to_numpy()).astype(np.float32)
            nuevas_numpy[nombre] = lag_1(v) if tipo == 'lag' else v - lag_1(v)
    tabla = pd.concat([tabla, pd.DataFrame(nuevas_numpy, index=tabla.index)], axis=1)
    del nuevas_numpy
    assert tabla.columns.tolist() == esperadas
    print(f'B4c y B5 (numpy): {len(NUMPY)} columnas · {time.time() - t0:.0f} s')

    con.register('tabla_fe', tabla)
    con.execute(f"copy tabla_fe to '{FE_PARQUET.as_posix()}' (format parquet)")
    con.unregister('tabla_fe')
    del tabla
    print(f'Parquet armado: {FE_PARQUET} · {len(esperadas)} columnas · {time.time() - t0:.0f} s')
else:
    print(f'Parquet ya armado, con las mismas columnas: {FE_PARQUET}')

# [Anotación · líneas 302–351] Controles sobre el parquet: 983.061 filas con clave única y en el mismo orden
#   que el base; lags y deltas de 1 mes vacíos en 202103 y lag 2 vacío en 202104; para un cliente con los 6
#   meses, lag 1 igual al valor del mes anterior y avg3 igual al promedio de 3 meses; cantidad de
#   empieza_comision por mes igual a valores escritos en el código (4.423 en 202104, 2.744 en 202105, 7.543 en
#   202106, 2.743 en 202107 y 3.041 en 202108); rankings rk_ entre 0 y 1 y rk0_ entre −1 y 1 con el signo del
#   monto, con los mismos nulos que el monto.
#%% celda 6 [texto]
## 3. Controles de las variables (ficha, controles 1 y 3–6)

Se hacen con consultas sobre el parquet, antes de cargarlo en memoria. El control 1 incluye que **las filas estén en el mismo orden que el parquet base**: LightGBM arma los cortes de los histogramas con una muestra de filas, y con otro orden el modelo cambia.

#%% celda 7 [código]
fe = f"read_parquet('{FE_PARQUET.as_posix()}')"

# 1 · filas, clave única y el mismo orden de filas que el parquet base
filas, claves = con.sql(f'select count(*), count(distinct (numero_de_cliente, foto_mes)) from {fe}').fetchone()
assert filas == claves == 983_061, (filas, claves)
desordenadas = con.sql(f'''select count(*) from (select numero_de_cliente, foto_mes from {fe})
                           positional join (select numero_de_cliente as c, foto_mes as m from read_parquet('{BASE_PARQUET.as_posix()}'))
                           where numero_de_cliente <> c or foto_mes <> m''').fetchone()[0]
assert desordenadas == 0, f'{desordenadas} filas en otro orden que el parquet base'

# 3 · lags vacíos donde no hay historia
lags_1 = [v for v in NUEVAS if v.startswith(('lag_1_', 'delta_1_', 'l1_', 'd1_'))]
lags_2 = [v for v in NUEVAS if v.startswith('lag_2_')]
no_nulos_mar = con.sql(f"select {' + '.join(f'count({v})' for v in lags_1)} from {fe} where foto_mes = 202103").fetchone()[0]
no_nulos_abr = con.sql(f"select {' + '.join(f'count({v})' for v in lags_2)} from {fe} where foto_mes = 202104").fetchone()[0]
assert no_nulos_mar == 0 and no_nulos_abr == 0, (no_nulos_mar, no_nulos_abr)

# 4 · un cliente con los 6 meses, a mano: lag_1 = el mes anterior; avg3 = promedio de 3 meses (no de 4)
cliente = con.sql(f'select numero_de_cliente from {fe} group by 1 having count(*) = 6 order by 1 limit 1').fetchone()[0]
h = con.sql(f'''select foto_mes, ctrx_quarter, lag_1_ctrx_quarter, avg3_ctrx_quarter, rk0_mcuentas_saldo,
                       l1_rk0_mcuentas_saldo, cproductos, lag_1_cproductos
                from {fe} where numero_de_cliente = {cliente} order by foto_mes''').df().set_index('foto_mes')
assert h.loc[202106, 'lag_1_ctrx_quarter'] == h.loc[202105, 'ctrx_quarter']
assert h.loc[202106, 'l1_rk0_mcuentas_saldo'] == h.loc[202105, 'rk0_mcuentas_saldo']     # B5 sobre el ranking
assert h.loc[202106, 'lag_1_cproductos'] == h.loc[202105, 'cproductos']                 # B5 sobre el crudo
assert np.isclose(h.loc[202106, 'avg3_ctrx_quarter'], h.loc[[202104, 202105, 202106], 'ctrx_quarter'].mean(), rtol=1e-5)

# 5 · empieza_comision contra el informe técnico del video (§6.2)
empiezan = dict(con.sql(f'select foto_mes, sum(empieza_comision)::INT from {fe} group by 1 order by 1').fetchall())
print('Empiezan a pagar la comisión, por mes:', empiezan)
assert {m: empiezan[m] for m in (202104, 202105, 202106, 202107, 202108)} == \
    {202104: 4_423, 202105: 2_744, 202106: 7_543, 202107: 2_743, 202108: 3_041}

# 6 · rankings entre 0 y 1, con los mismos nulos que el monto
fuera_de_rango = con.sql(f"select {' + '.join(f'count(*) filter (where rk_{c} < 0 or rk_{c} > 1)' for c in MONTOS)} from {fe}").fetchone()[0]
nulos_distintos = con.sql(f"select {' + '.join(f'count(*) filter (where ({c} is null) <> (rk_{c} is null))' for c in MONTOS)} from {fe}").fetchone()[0]
assert fuera_de_rango == 0 and nulos_distintos == 0, (fuera_de_rango, nulos_distintos)

# 6b · ranking con el cero fijo: entre −1 y 1, mismo signo que el monto (el 0 queda en 0), mismos nulos
mal_signo = con.sql(f"select {' + '.join(f'count(*) filter (where sign(rk0_{c}) <> sign({c}) or rk0_{c} < -1 or rk0_{c} > 1)' for c in MONTOS)} from {fe}").fetchone()[0]
nulos_distintos0 = con.sql(f"select {' + '.join(f'count(*) filter (where ({c} is null) <> (rk0_{c} is null))' for c in MONTOS)} from {fe}").fetchone()[0]
assert mal_signo == 0 and nulos_distintos0 == 0, (mal_signo, nulos_distintos0)

print(f'Controles OK · cliente de prueba {cliente} · {len(lags_1)} lags/deltas vacíos en 202103 · {len(lags_2)} lag_2 vacíos en 202104')

# [Anotación · líneas 353–408] Carga el parquet en memoria. variables_de arma la lista de una corrida:
#   variables de la base menos las excluidas; con B4 o B4c cada monto se reemplaza por su rk_ o rk0_; los demás
#   bloques agregan sus variables salvo las que derivan de una columna excluida. matriz aplica el pase a NA por
#   mes a la columna y a sus derivadas, sobre una copia. Escribe ../exp/05_variables/bloques.json con la base,
#   la configuración, los NA por mes, la ruta del parquet, las fuentes y la lista exacta de variables de cada
#   corrida.
#%% celda 8 [texto]
## 4. Datos

Se carga el parquet con las variables nuevas. Cada bloque usa las variables de la base **más** las suyas; B4 **reemplaza** cada monto por su ranking. La limpieza de la base (variables a `NA` en ciertos meses) se aplica sobre una copia, y alcanza también a las variables que salen de esa columna.

`bloques.json` guarda la lista exacta de variables de cada corrida, para el `03`.

#%% celda 9 [código]
t0 = time.time()
df = con.sql(f'select * from {fe}').df()
VARIABLES_BASE = [c for c in COLUMNAS_BASE if c not in config02['variables_excluidas']]
EXCLUIR_BASE = set(DEF_BASE['excluir'])
NA_EN_MES = DEF_BASE['na_en_mes']
print(f'{len(df):,} filas · {df.shape[1]} columnas · {time.time() - t0:.0f} s')


def variables_de(nombre):
    # 'base', un bloque ('B2') o una combinación ('B1+B3')
    bloques = [] if nombre == 'base' else nombre.split('+')
    variables = [c for c in VARIABLES_BASE if c not in EXCLUIR_BASE]
    for b, prefijo in (('B4', 'rk_'), ('B4c', 'rk0_')):        # reemplazan cada monto por su ranking
        if b in bloques:
            variables = [f'{prefijo}{c}' if c in MONTOS else c for c in variables]
    for b in bloques:
        if b not in ('B4', 'B4c'):
            variables += [v for v in BLOQUES[b] if not set(FUENTES[v]) & EXCLUIR_BASE]
    return variables


def matriz(indices, nombre):
    # X de una corrida para unas filas, con la limpieza de la base (sobre una copia)
    columnas = variables_de(nombre)
    X = df[columnas].iloc[indices].copy()
    meses = df['foto_mes'].iloc[indices].to_numpy()
    for columna, meses_na in NA_EN_MES.items():
        afectadas = [v for v in columnas if v == columna or columna in FUENTES.get(v, [])]
        X.loc[np.isin(meses, meses_na), afectadas] = np.nan
    return X


def particion(prueba):
    meses = PRUEBAS[prueba]
    es_train = df['foto_mes'].isin(meses['train']) & df['clase_ternaria'].notna()
    es_test = df['foto_mes'] == meses['test']
    return np.flatnonzero(es_train), np.flatnonzero(es_test)


cantidades = {n: len(variables_de(n)) for n in ['base'] + NOMBRES}
print('Variables por corrida:', cantidades)
assert cantidades['base'] == 153 - len(EXCLUIR_BASE)
assert all(not set(FUENTES.get(v, [])) & EXCLUIR_BASE for n in NOMBRES for v in variables_de(n))
assert df.loc[df['foto_mes'] == 202108, 'clase_ternaria'].isna().all()

(EXP / 'bloques.json').write_text(json.dumps({
    'base': BASE, 'config': CONFIG, 'na_en_mes': NA_EN_MES, 'fe_parquet': FE_PARQUET.as_posix(),
    'fuentes': FUENTES, 'variables': {n: variables_de(n) for n in ['base'] + NOMBRES}}, indent=2))

# [Anotación · líneas 410–447] Funciones de ganancia iguales a las del 02 y el 04. archivo_curva ubica la
#   curva de cada corrida (la base en A y B se lee del 02 o del 04). entrenar ajusta un LightGBM con los
#   hiperparámetros de CONFIG y la semilla, predice el mes de prueba y devuelve la curva de ganancia y el AUC
#   contra BAJA+2.
#%% celda 10 [texto]
## 5. Ganancia (mismas funciones que el `02` y el `04`)

#%% celda 11 [código]
def curva_ganancia(prob, es_baja2, largo=LARGO_CURVA):
    orden = np.argsort(-prob, kind='stable')
    ganancia = np.where(es_baja2[orden], GANANCIA_ACIERTO, -COSTO_ESTIMULO)
    return np.cumsum(ganancia)[:largo].astype(np.float64)


def suavizar(curva, ventana=VENTANA_SUAVIZADO):
    return pd.Series(curva).rolling(ventana, center=True, min_periods=ventana).mean().to_numpy()


def meseta(curva):
    s = suavizar(curva)
    i = int(np.nanargmax(s))
    return i + 1, float(s[i])


def archivo_curva(nombre, prueba, semilla):
    if nombre == 'base' and prueba in ('A', 'B'):      # la base en A y B ya está corrida
        if BASE == 'linea_base':
            return EXP02 / 'curvas' / f'{CONFIG}_{prueba}_s{semilla}.npz'
        return EXP04 / 'curvas' / f'{CONFIG}_{BASE}_{prueba}_s{semilla}.npz'
    return CURVAS / f'{CONFIG}_{BASE}_{nombre}_{prueba}_s{semilla}.npz'


def entrenar(nombre, prueba, semilla):
    i_train, i_test = particion(prueba)
    y_train = df['clase_ternaria'].iloc[i_train].isin(CLASES[CLASE]).astype(int).to_numpy()
    params = dict(HIPERPARAMETROS[HIPER])
    rondas = params.pop('num_iterations')
    params['seed'] = semilla
    modelo = lgb.train(params, lgb.Dataset(matriz(i_train, nombre), label=y_train), num_boost_round=rondas)
    prob = modelo.predict(matriz(i_test, nombre))
    es_baja2 = (df['clase_ternaria'].iloc[i_test] == 'BAJA+2').to_numpy()
    return curva_ganancia(prob, es_baja2), roc_auc_score(es_baja2, prob)

# [Anotación · líneas 449–473] Control: entrena la base en A con la primera semilla leyendo el parquet de
#   variables nuevas y exige que la meseta difiera en menos de 1 de la curva guardada por el 02 o el 04; hace lo
#   mismo con la REFERENCIA si su curva ya existe.
#%% celda 12 [texto]
## 6. Control 7: la base se reproduce desde el parquet nuevo

Se entrena la base en A con la primera semilla, leyendo el parquet de variables nuevas, y se compara con la curva guardada del `02` o del `04`. Si da distinto, algo cambió en las columnas de la base.

**7b:** lo mismo con la `REFERENCIA`, si ya estaba corrida. Así se confirma que las curvas guardadas siguen valiendo con el parquet rearmado.

#%% celda 13 [código]
faltan_base = [s for s in SEMILLAS_A_USAR for p in ('A', 'B') if not archivo_curva('base', p, s).exists()]
assert not faltan_base, f'Faltan curvas de la base {BASE} en A/B: correr completo el {"02" if BASE == "linea_base" else "04"}'

t0 = time.time()
curva_nueva, _ = entrenar('base', 'A', SEMILLAS_A_USAR[0])
referencia = meseta(np.load(archivo_curva('base', 'A', SEMILLAS_A_USAR[0]))['curva'])[1]
diferencia = meseta(curva_nueva)[1] - referencia
print(f'Base {BASE} en A, semilla {SEMILLAS_A_USAR[0]}: diferencia contra la curva guardada = {diferencia:,.0f} · {time.time() - t0:.0f} s')
assert abs(diferencia) < 1, 'La base no se reproduce desde el parquet nuevo'

# 7b · si la referencia ya está corrida, su curva guardada tiene que salir igual con el parquet actual
if REFERENCIA and archivo_curva(REFERENCIA, 'A', SEMILLAS_A_USAR[0]).exists():
    t0 = time.time()
    curva_ref, _ = entrenar(REFERENCIA, 'A', SEMILLAS_A_USAR[0])
    dif_ref = meseta(curva_ref)[1] - meseta(np.load(archivo_curva(REFERENCIA, 'A', SEMILLAS_A_USAR[0]))['curva'])[1]
    print(f'{REFERENCIA} en A, semilla {SEMILLAS_A_USAR[0]}: diferencia contra la curva guardada = {dif_ref:,.0f} · {time.time() - t0:.0f} s')
    assert abs(dif_ref) < 1, 'Las curvas guardadas no se reproducen con el parquet actual'

# [Anotación · líneas 475–492] Backtests: la base en C (si alguna corrida la necesita) y cada bloque o
#   combinación en sus pruebas, con cada semilla. Cada curva se guarda en .npz al terminar y las existentes no
#   se repiten.
#%% celda 14 [texto]
## 7. Backtests

Para cada bloque (y la combinación, si está), cada prueba y cada semilla. La base en C se corre una vez, si algún bloque con historia la necesita. Retoma si se corta.

#%% celda 15 [código]
corridas = ([('base', 'C', s) for s in SEMILLAS_A_USAR] if NECESITA_C else []) + \
           [(n, p, s) for n in NOMBRES for p in pruebas_de(n) for s in SEMILLAS_A_USAR]
pendientes = [c for c in corridas if not archivo_curva(*c).exists()]
print(f'{len(corridas)} modelos · {len(pendientes)} pendientes')

t_total = time.time()
for k, (nombre, prueba, semilla) in enumerate(pendientes, 1):
    t0 = time.time()
    curva, auc = entrenar(nombre, prueba, semilla)
    np.savez(archivo_curva(nombre, prueba, semilla), curva=curva, auc=auc)
    print(f'[{k}/{len(pendientes)}] {nombre} · {prueba} · semilla {semilla} · {time.time() - t0:.0f} s')
print(f'Listo en {(time.time() - t_total) / 60:.1f} min')

# [Anotación · líneas 494–536] Resumen por corrida y prueba (cantidad de variables, N y ganancia de meseta,
#   media y desvío por semilla, AUC medio, ganancia en cada corte), guardado en resumen.csv. En la corrida
#   completa verifica que la base reproduce la ganancia de meseta del resumen del 02 o del 04.
#%% celda 16 [texto]
## 8. Resumen por corrida

La misma tabla que el `02` y el `04`. Con 10 semillas, la base tiene que dar lo mismo que en el `02` o el `04` (control 7 de la ficha).

#%% celda 17 [código]
def cargar(nombre, prueba, semillas=SEMILLAS_A_USAR):
    datos = [np.load(archivo_curva(nombre, prueba, s)) for s in semillas]
    return np.vstack([d['curva'] for d in datos]), np.array([float(d['auc']) for d in datos])


filas, promedios, por_semilla = [], {}, {}
for nombre in ['base'] + NOMBRES:
    pruebas = (['A', 'B'] + (['C'] if NECESITA_C else [])) if nombre == 'base' else pruebas_de(nombre)
    for prueba in pruebas:
        curvas, aucs = cargar(nombre, prueba)
        promedio = curvas.mean(axis=0)
        promedios[(nombre, prueba)] = promedio
        por_semilla[(nombre, prueba)] = np.array([meseta(c)[1] for c in curvas])
        n_mes, g_mes = meseta(promedio)
        fila = {'config': CONFIG, 'base': BASE, 'nombre': nombre, 'prueba': prueba, 'semillas': len(curvas),
                'variables': len(variables_de(nombre)), 'N_meseta': n_mes, 'ganancia_meseta': g_mes,
                'ganancia_media': por_semilla[(nombre, prueba)].mean(),
                'ganancia_desvio': por_semilla[(nombre, prueba)].std(ddof=1) if len(curvas) > 1 else np.nan,
                'auc_medio': aucs.mean()}
        fila.update({f'g_{n}': promedio[n - 1] for n in CORTES})
        filas.append(fila)

resumen = pd.DataFrame(filas)
resumen.to_csv(EXP / ('resumen_rapido.csv' if MODO_RAPIDO else 'resumen.csv'), index=False)

if not MODO_RAPIDO:   # control 7: la base igual que en el 02 o el 04
    if BASE == 'linea_base':
        ref = pd.read_csv(EXP02 / 'resumen.csv').query('config == @CONFIG').set_index('prueba')['ganancia_meseta']
    else:
        ref = pd.read_csv(EXP04 / 'resumen.csv').query('config == @CONFIG and variante == @BASE').set_index('prueba')['ganancia_meseta']
    for prueba in ('A', 'B'):
        g = resumen.query('nombre == "base" and prueba == @prueba')['ganancia_meseta'].iloc[0]
        assert abs(g - ref[prueba]) < 1, f'La base no reproduce el {"02" if BASE == "linea_base" else "04"} en {prueba}'
    print('Control 7 OK: la base reproduce su resumen')

(resumen.pivot_table(index='nombre', columns='prueba', values=['ganancia_meseta', 'ganancia_desvio', 'N_meseta'], sort=False)
        .style.format('{:,.0f}'))

# [Anotación · líneas 538–584] comparar calcula, por prueba, la diferencia de meseta semilla por semilla de
#   una corrida contra la base o contra la REFERENCIA: media en millones, cantidad de semillas con diferencia
#   positiva y p de Wilcoxon. La columna adoptar exige, para corridas con historia, diferencia media positiva en
#   A con p < 0,05 y que B no sea negativa con p < 0,05; para las demás, que la suma A + B sea positiva en
#   promedio y que ninguna prueba sea negativa con p < 0,05; siempre con más de una semilla. C_contradice marca
#   si C es negativa con p < 0,05. Guarda comparacion.csv.
#%% celda 18 [texto]
## 9. Comparación pareada: contra la base y contra la referencia

Cada corrida contra la base, y cada combinación también contra la `REFERENCIA`, semilla por semilla, con la meseta de cada semilla:
- **`dif_media`:** diferencia promedio, en millones;
- **`mejoran`:** en cuántas semillas mejora;
- **`p`:** Wilcoxon pareado (solo con 10 semillas).

**Regla** (decisión 3 de la ficha, corregida el 2026-10-05: "ante la duda, no sumar"), columna `adoptar`:
- **Sin historia (B1, B4, B4c):** la suma de A + B mejora (semilla por semilla), y en ninguna prueba empeora con p < 0,05.
- **Con historia (B2, B3, B5, o una combinación que los incluya):** mejora en A con p < 0,05, y en B no empeora con p < 0,05. **C no decide:** si C empeora con p < 0,05, la columna `C_contradice` lo marca para discutirlo.

**Después**, la combinación que gane contra la referencia se confirma con el público: un submit de 20 semillas en N = 12.000 (CLAUDE.md §6.2).

Con `MODO_RAPIDO = True` no se adopta nada: una semilla no sirve para decidir.

#%% celda 19 [código]
def comparar(nombre, contra):
    con_historia = bool(HISTORIA & set(nombre.split('+')))
    fila, res, difs = {'nombre': nombre, 'contra': contra, 'historia': con_historia}, {}, {}
    for prueba in pruebas_de(nombre):
        if (contra, prueba) not in por_semilla:
            continue
        d = por_semilla[(nombre, prueba)] - por_semilla[(contra, prueba)]
        p = wilcoxon(d).pvalue if len(d) >= 6 and np.any(d != 0) else np.nan
        fila[f'{prueba}_dif_media'] = d.mean() / 1e6
        fila[f'{prueba}_mejoran'] = f'{(d > 0).sum()}/{len(d)}'
        fila[f'{prueba}_p'] = p
        res[prueba], difs[prueba] = (d.mean(), p), d
    empeora = lambda pr: pr in res and res[pr][0] < 0 and res[pr][1] < 0.05
    if con_historia:
        adoptar = res['A'][0] > 0 and res['A'][1] < 0.05 and not empeora('B')
        fila['C_contradice'] = empeora('C')
    else:   # ante la duda, no sumar: la suma A + B tiene que mejorar
        adoptar = (difs['A'] + difs['B']).mean() > 0 and not empeora('A') and not empeora('B')
    fila['adoptar'] = bool(adoptar and len(SEMILLAS_A_USAR) > 1)
    return fila


comparacion = pd.DataFrame([comparar(n, 'base') for n in NOMBRES]
                           + [comparar(n, REFERENCIA) for n in NOMBRES if REFERENCIA and '+' in n and n != REFERENCIA])
comparacion.to_csv(EXP / ('comparacion_rapido.csv' if MODO_RAPIDO else 'comparacion.csv'), index=False)
if REFERENCIA:
    ganan = comparacion.query('contra == @REFERENCIA and adoptar')['nombre'].tolist()
    print(f'Combinaciones que le ganan a {REFERENCIA} con la regla:', ganan or 'ninguna', '(la decisión es del usuario)')
comparacion.style.format({c: '{:+.1f}' for c in comparacion.columns if c.endswith('dif_media')}
                         | {c: '{:.3f}' for c in comparacion.columns if c.endswith('_p')})

# [Anotación · líneas 586–602] Grafica la meseta promedio de cada corrida en A, B y C con barras de ± un
#   desvío entre semillas y una línea punteada en el valor de la base.
#%% celda 20 [texto]
## 10. Gráfico: ganancia por corrida

La meseta promedio de cada corrida en cada prueba, con una barra de ± desvío entre semillas. La línea punteada es la base.

#%% celda 21 [código]
pruebas_graf = ['A', 'B'] + (['C'] if NECESITA_C else [])
fig, ejes = plt.subplots(1, len(pruebas_graf), figsize=(6 * len(pruebas_graf), 4.5))
for eje, prueba in zip(np.atleast_1d(ejes), pruebas_graf):
    ns = [n for n in ['base'] + NOMBRES if (n, prueba) in por_semilla]
    medias = [por_semilla[(n, prueba)].mean() / 1e6 for n in ns]
    desvios = [por_semilla[(n, prueba)].std(ddof=1) / 1e6 if len(SEMILLAS_A_USAR) > 1 else 0 for n in ns]
    eje.errorbar(ns, medias, yerr=desvios, fmt='o', capsize=4)
    eje.axhline(medias[0], linestyle='--', color='gray')
    eje.set_title(f'Prueba {prueba}: meseta por corrida (millones)' + (' · referencia' if prueba == 'C' else ''))
plt.tight_layout()
plt.show()

# [Anotación · líneas 604–632] Tabla de elección: N sugerido de cada corrida (promedio de los N de A y B
#   redondeado a 500, entre 8.000 y 15.000), ganancia de A, B y C en ese N, suma A + B, desvío combinado y
#   diferencias contra la base y contra la REFERENCIA. Las celdas de texto indican cómo pasar la combinación al
#   03.
#%% celda 22 [texto]
## 11. Elección (la decide el usuario)

- **A + B** en el N sugerido de cada corrida (promedio de los N de A y B, redondeado a 500, entre 8.000 y 15.000), y diferencia contra la base. C se muestra en el mismo N, como referencia.
- **Combinaciones:** se agregan a `COMBINACIONES` y se vuelve a correr el notebook. Solo se entrena lo nuevo.
- **Submit:** si una combinación le gana a la referencia, se confirma con el público. En el `03`: `BLOQUES = '<nombre>'` y `N_ENVIOS = 12_000` (decisión del 2026-10-05).

#%% celda 23 [código]
filas = []
for nombre in ['base'] + NOMBRES:
    r = resumen.query('nombre == @nombre').set_index('prueba')
    n = int(np.clip(round((r.loc['A', 'N_meseta'] + r.loc['B', 'N_meseta']) / 2 / 500) * 500, 8_000, 15_000))
    gA, gB = promedios[(nombre, 'A')][n - 1], promedios[(nombre, 'B')][n - 1]
    filas.append({'nombre': nombre, 'N_sugerido': n, 'A_en_N': gA / 1e6, 'B_en_N': gB / 1e6, 'A+B_en_N': (gA + gB) / 1e6,
                  'desvio_A+B': np.sqrt(r.loc[['A', 'B'], 'ganancia_desvio'].pow(2).sum()) / 1e6,
                  'C_en_N': promedios[(nombre, 'C')][n - 1] / 1e6 if (nombre, 'C') in promedios else np.nan})
eleccion = pd.DataFrame(filas)
eleccion['vs_base'] = eleccion['A+B_en_N'] - eleccion['A+B_en_N'].iloc[0]
if REFERENCIA:
    eleccion['vs_referencia'] = eleccion['A+B_en_N'] - eleccion.set_index('nombre').loc[REFERENCIA, 'A+B_en_N']
eleccion.style.format({c: '{:,.1f}' for c in ['A_en_N', 'B_en_N', 'A+B_en_N', 'desvio_A+B', 'C_en_N', 'vs_base', 'vs_referencia']
                       if c in eleccion} | {'N_sugerido': '{:,}'})

#%% celda 24 [texto]
## 12. Cierre

- **Registro:** anotar en `decisiones.md` el experimento #3 (resumen por bloque en A, B y C, y la comparación pareada) y qué bloques se adoptan.
- **Combinaciones:** `COMBINACIONES = [...]` y correr de nuevo.
- **Submit:** en el `03`, `BLOQUES = '<nombre>'`, `VARIANTE` = la base del `05` y `N_ENVIOS = 12_000`.
```

### notebook/01_pipeline_base.ipynb

Lee el dataset crudo con DuckDB, calcula clase_ternaria en SQL, fija los tipos, verifica contra valores esperados y guarda el parquet base y una tabla de nulos y ceros por variable y mes.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Celdas de texto de presentación. Indican que el notebook parte de
#   competencia_01_crudo.csv, agrega clase_ternaria, verifica contra valores conocidos y guarda el dataset base
#   en parquet con una tabla de calidad por mes; no limpia, no arma variables y no entrena. Las rutas son
#   relativas a la carpeta del notebook.
#%% celda 1 [texto]
# 01 · Pipeline base desde el crudo

**Etapa 1 del plan** (`fichas/etapa_1_pipeline_base.md`). Este notebook:

- parte del dataset original de la cátedra (`competencia_01_crudo.csv`);
- agrega la clase `clase_ternaria`, con el mismo criterio que el código oficial (`z470`);
- verifica todo contra valores conocidos;
- guarda el dataset base en parquet, junto con una tabla de calidad por mes.

**No** limpia ni saca variables, **no** arma variables nuevas y **no** entrena. Todo eso se decide después, con experimentos.

Decisiones de esta etapa: `decisiones.md`.

#%% celda 2 [texto]
## 1. Parámetros

Las rutas son relativas a la carpeta del notebook, `TPs/competencia_1/notebook/`. Las salidas van a `TPs/competencia_1/data/` (dataset base) y a `TPs/competencia_1/exp/` (tablas de cada experimento), fuera de la carpeta de notebooks.

`CRUDO` es **lo único que se cambia** al pasar a Google Cloud. El link oficial del crudo está en el libro de la materia, 1.2.

# [Anotación · líneas 22–53] Importa pathlib, time, warnings, duckdb y pandas. Define las rutas (crudo en
#   ../../dataset/competencia_01_crudo.csv, salidas en ../data/competencia_01_base.parquet y
#   ../exp/01_calidad_por_mes.csv) y SEMILLA_PRIMIGENIA = 979201. Crea las carpetas de salida y frena con assert
#   si el crudo no existe o si la semilla no es un primo de 6 dígitos.
#%% celda 3 [código]
from pathlib import Path
import time
import warnings

import duckdb
import pandas as pd

# --- Parámetros -------------------------------------------------------------
CRUDO = Path('../../dataset/competencia_01_crudo.csv')
DATA = Path('../data')   # salidas fuera de notebook/
EXP = Path('../exp')
BASE_PARQUET = DATA / 'competencia_01_base.parquet'
CALIDAD_CSV = EXP / '01_calidad_por_mes.csv'

SEMILLA_PRIMIGENIA = 979201  # <- tu primo de 6 dígitos (de ella salen todas las demás semillas)
# -----------------------------------------------------------------------------

# Falso positivo conocido de pandas 2.2 con Python 3.14 (no afecta resultados)
warnings.filterwarnings('ignore', message='.*ChainedAssignmentError.*')

DATA.mkdir(exist_ok=True)
EXP.mkdir(exist_ok=True)


def es_primo(n):
    return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))


assert CRUDO.exists(), f'No encuentro el crudo en {CRUDO.resolve()}'
assert isinstance(SEMILLA_PRIMIGENIA, int) and 100_000 <= SEMILLA_PRIMIGENIA <= 999_999 \
    and es_primo(SEMILLA_PRIMIGENIA), 'SEMILLA_PRIMIGENIA tiene que ser un primo de 6 dígitos'

# [Anotación · líneas 55–83] Declara los valores esperados que se usan como control: 983.061 filas, 154
#   columnas, 169.727 clientes, la cantidad de filas de cada mes de 202103 a 202108, la cantidad de BAJA+1,
#   BAJA+2, CONTINUA y sin clase por mes, y dos numero_de_cliente (48000000 y 31100000) que se verifican más
#   abajo.
#%% celda 4 [texto]
## 2. Valores esperados

Estos números se verificaron sobre el crudo el 2026-10-03 y el 2026-10-05. El notebook se **frena** si algo no coincide, para no seguir con datos distintos de los esperados.

Las clases siguen el criterio de la cátedra: los 15 clientes que se van un mes y vuelven al siguiente (1 → 0 → 1) cuentan como `BAJA+1`.

#%% celda 5 [código]
ESPERADO_FILAS = 983_061
ESPERADO_COLUMNAS_CRUDO = 154
ESPERADO_CLIENTES = 169_727

ESPERADO_FILAS_POR_MES = {
    202103: 162_900, 202104: 163_284, 202105: 163_768,
    202106: 164_114, 202107: 164_348, 202108: 164_647,
}

# None = sin clase (falta el futuro para saberla)
ESPERADO_CLASES = {
    202103: {'BAJA+1': 1_019, 'BAJA+2': 960,   'CONTINUA': 160_921},
    202104: {'BAJA+1': 964,   'BAJA+2': 1_139, 'CONTINUA': 161_181},
    202105: {'BAJA+1': 1_143, 'BAJA+2': 870,   'CONTINUA': 161_755},
    202106: {'BAJA+1': 874,   'BAJA+2': 1_098, 'CONTINUA': 162_142},
    202107: {'BAJA+1': 1_103, None: 163_245},
    202108: {None: 164_647},
}

# IDs que Python o R pueden escribir en notación científica (Zulip, Denicolay)
IDS_TRAICIONEROS = [48_000_000, 31_100_000]

# [Anotación · líneas 85–119] Carga el CSV en una tabla de DuckDB con sample_size=-1 (recorre todo el archivo
#   para decidir los tipos) y numero_de_cliente declarado BIGINT. Cuenta filas, columnas, clientes distintos,
#   claves (numero_de_cliente, foto_mes) duplicadas y filas por mes; frena con assert si no coinciden con los
#   valores esperados.
#%% celda 6 [texto]
## 3. Carga del crudo

- **Por qué se declara el tipo del ID:** el crudo trae `4.8e+07` en 6 filas, una por mes (es el cliente 48000000). Sin declararlo, DuckDB lee `numero_de_cliente` como decimal; con `types={'numero_de_cliente': 'BIGINT'}` queda entero.
- **`sample_size=-1`:** DuckDB recorre el archivo entero antes de decidir el tipo de cada columna.

#%% celda 7 [código]
t0 = time.time()
con = duckdb.connect()

con.execute(f"""
    create or replace table crudo as
    select *
    from read_csv('{CRUDO.as_posix()}', sample_size=-1,
                  types={{'numero_de_cliente': 'BIGINT'}})
""")

filas = con.execute("select count(*) from crudo").fetchone()[0]
columnas = len(con.execute("describe crudo").fetchall())
clientes = con.execute("select count(distinct numero_de_cliente) from crudo").fetchone()[0]
duplicados = con.execute("""
    select count(*) from (
        select numero_de_cliente, foto_mes from crudo group by all having count(*) > 1)
""").fetchone()[0]

print(f'{filas:,} filas · {columnas} columnas · {clientes:,} clientes · '
      f'{duplicados} claves duplicadas · {time.time() - t0:.0f} s')

assert (filas, columnas, clientes, duplicados) == \
    (ESPERADO_FILAS, ESPERADO_COLUMNAS_CRUDO, ESPERADO_CLIENTES, 0)

#%% celda 8 [código]
por_mes = dict(con.execute("select foto_mes, count(*) from crudo group by 1 order by 1").fetchall())
print(por_mes)
assert por_mes == ESPERADO_FILAS_POR_MES

# [Anotación · líneas 121–181] Arma clase_ternaria en SQL. Calcula un período consecutivo p0 = año × 12 + mes
#   y, por cliente, los dos períodos siguientes presentes en los datos (lead 1 y lead 2). Asigna BAJA+2 si el
#   cliente está el mes siguiente y no el subsiguiente, BAJA+1 si no está el mes siguiente, CONTINUA en el resto
#   de las filas con dos meses de futuro y NULL donde falta futuro. La tabla de cantidades por mes y clase se
#   compara con assert contra la esperada.
#%% celda 9 [texto]
## 4. Clase ternaria

Es la misma lógica que el código oficial de la cátedra (`z470`, en R), escrita en SQL.

1. **Período consecutivo:** `p0 = año × 12 + mes`. Así el mes siguiente es siempre `p0 + 1`, incluso de diciembre a enero.
2. **Para cada cliente** se miran sus dos períodos siguientes en el dataset: `p1` y `p2`, con `lead`.
3. **Se asigna la clase:**

| Clase | Condición |
|---|---|
| `BAJA+2` | está el mes siguiente (`p1 = p0 + 1`) pero no el subsiguiente (`p2` no existe o es mayor que `p0 + 2`) |
| `BAJA+1` | no está el mes siguiente (`p1` no existe o es mayor que `p0 + 1`) |
| `CONTINUA` | el resto, siempre que haya dos meses de futuro para saberlo |
| `NULL` | falta el futuro: `202108` entero, y `202107` salvo los `BAJA+1` |

**La lógica de tres valores** (bug de la Clase 01): si `p2` es `NULL`, `p2 > p0 + 2` da `NULL` y no `TRUE`. Por eso se pregunta explícitamente `p2 is null`. Si no, la fila caería por defecto en otra clase.

#%% celda 10 [código]
ultimo = con.execute("select max((foto_mes // 100) * 12 + foto_mes % 100) from crudo").fetchone()[0]

con.execute(f"""
    create or replace table con_clase as
    with periodos as (
        select *, (foto_mes // 100) * 12 + foto_mes % 100 as p0
        from crudo
    ),
    futuros as (
        select *,
               lead(p0, 1) over w as p1,
               lead(p0, 2) over w as p2
        from periodos
        window w as (partition by numero_de_cliente order by p0)
    )
    select * exclude (p0, p1, p2),
           case
               when p0 < {ultimo} - 1 and p1 = p0 + 1 and (p2 is null or p2 > p0 + 2) then 'BAJA+2'
               when p0 < {ultimo}     and (p1 is null or p1 > p0 + 1)                  then 'BAJA+1'
               when p0 < {ultimo} - 1                                                    then 'CONTINUA'
               else null
           end as clase_ternaria
    from futuros
""")

tabla_clases = con.execute("""
    select foto_mes, clase_ternaria, count(*) as n
    from con_clase group by all order by all
""").df()
tabla_clases.pivot(index='foto_mes', columns='clase_ternaria', values='n').fillna(0).astype(int)

#%% celda 11 [código]
def clases_por_mes(tabla):
    """{foto_mes: {clase: n}}, con None para las filas sin clase."""
    salida = {}
    for mes, clase, n in tabla[['foto_mes', 'clase_ternaria', 'n']].itertuples(index=False):
        salida.setdefault(int(mes), {})[None if pd.isna(clase) else clase] = int(n)
    return salida


assert clases_por_mes(tabla_clases) == ESPERADO_CLASES, 'La tabla de clases no coincide con la esperada'
print('Clases OK: coinciden con el código oficial de la cátedra')

# [Anotación · líneas 183–215] Fija los tipos: numero_de_cliente BIGINT, foto_mes INTEGER, clase_ternaria
#   texto y las 152 variables restantes FLOAT (float32). El texto indica que no hay imputación de nulos.
#   Verifica los tipos con assert.
#%% celda 12 [texto]
## 5. Tipos

Decisión de la etapa:
- `numero_de_cliente` queda en `int64` (`BIGINT`);
- `foto_mes` pasa a entero de 32 bits;
- `clase_ternaria` queda como texto;
- **todo el resto pasa a `float32`** (`FLOAT` en DuckDB).

**Por qué:**
- Reduce a la mitad la memoria de las 152 variables. Hay 16 GB de RAM y después vienen las variables nuevas.
- LightGBM trabaja internamente en `float32`, así que el modelo no pierde nada.
- Los `NULL` se mantienen: no hay ningún `fillna` ni ninguna imputación.

**Cuidado con lo que redondea `float32`:** guarda unos 7 dígitos significativos, así que montos de millones con centavos pierden los últimos decimales. Para ordenar y cortar (lo que hacen los árboles) no importa.

#%% celda 13 [código]
columnas_crudo = [c[0] for c in con.execute("describe con_clase").fetchall()]
claves = ['numero_de_cliente', 'foto_mes', 'clase_ternaria']
variables = [c for c in columnas_crudo if c not in claves]

select_tipado = ',\n    '.join(
    ['numero_de_cliente::BIGINT as numero_de_cliente', 'foto_mes::INTEGER as foto_mes']
    + [f'"{c}"::FLOAT as "{c}"' for c in variables]
    + ['clase_ternaria']
)
con.execute(f"create or replace table base as select\n    {select_tipado}\nfrom con_clase")

tipos = con.execute("describe base").df().set_index('column_name')['column_type']
print(tipos.value_counts().to_string())
assert tipos['numero_de_cliente'] == 'BIGINT' and tipos['foto_mes'] == 'INTEGER'
assert tipos['clase_ternaria'] == 'VARCHAR'
assert (tipos[variables] == 'FLOAT').all() and len(variables) == 152

# [Anotación · líneas 217–244] Controles sobre la tabla base: en 202107 sólo hay BAJA+1 (1.103) o filas sin
#   clase (163.245) y en 202108 todas las filas están sin clase; los dos IDs listados aparecen 6 veces cada uno;
#   ningún numero_de_cliente tiene decimales.
#%% celda 14 [texto]
## 6. Controles del dataset base

Estos controles corresponden a la tabla de verificación de la ficha:
- **6 y 7:** clase y meses sin futuro;
- **2 y 7:** IDs y clave única.

#%% celda 15 [código]
# 202107: solo BAJA+1 o sin clase; 202108: todo sin clase
clases_jul = dict(con.execute("""select coalesce(clase_ternaria, 'NULL'), count(*) from base
                                 where foto_mes = 202107 group by 1""").fetchall())
clases_ago = dict(con.execute("""select coalesce(clase_ternaria, 'NULL'), count(*) from base
                                 where foto_mes = 202108 group by 1""").fetchall())
print('202107:', clases_jul, '· 202108:', clases_ago)
assert clases_jul == {'BAJA+1': 1_103, 'NULL': 163_245}
assert clases_ago == {'NULL': 164_647}

# IDs traicioneros: enteros, 6 apariciones cada uno (una por mes)
for id_ in IDS_TRAICIONEROS:
    n = con.execute(f"select count(*) from base where numero_de_cliente = {id_}").fetchone()[0]
    print(f'{id_}: {n} filas')
    assert n == 6

# Ningún ID con decimales y clave única
no_enteros = con.execute("""select count(*) from base
                            where numero_de_cliente <> round(numero_de_cliente)""").fetchone()[0]
assert no_enteros == 0
print('Controles OK')

# [Anotación · líneas 246–267] Escribe la tabla base en parquet con compresión zstd y la relee para verificar
#   que la cantidad de filas, los tipos y la tabla de clases por mes son iguales a los de la tabla en memoria.
#%% celda 16 [texto]
## 7. Persistencia en parquet

Se guarda el dataset base y **se relee para confirmar** que quedó igual: filas, columnas, tipos y la tabla de clases.

Los notebooks siguientes leen este archivo, no el crudo. `data/` no se versiona.

#%% celda 17 [código]
t0 = time.time()
con.execute(f"copy base to '{BASE_PARQUET.as_posix()}' (format parquet, compression zstd)")
print(f'Guardado: {BASE_PARQUET} · {BASE_PARQUET.stat().st_size / 1e6:.0f} MB · {time.time() - t0:.0f} s')

releido = f"read_parquet('{BASE_PARQUET.as_posix()}')"
filas_p = con.execute(f"select count(*) from {releido}").fetchone()[0]
tipos_p = con.execute(f"describe select * from {releido}").df().set_index('column_name')['column_type']
tabla_p = con.execute(f"""select foto_mes, clase_ternaria, count(*) as n
                          from {releido} group by all order by all""").df()

assert filas_p == ESPERADO_FILAS
assert tipos_p.equals(tipos), 'Los tipos del parquet no coinciden con los de la tabla base'
assert clases_por_mes(tabla_p) == ESPERADO_CLASES
print(f'Parquet OK: {filas_p:,} filas · {len(tipos_p)} columnas · clases iguales')

# [Anotación · líneas 269–298] Calcula, para cada variable y cada mes, el porcentaje de nulos y el porcentaje
#   de ceros sobre todas las filas del mes, y lo guarda en ../exp/01_calidad_por_mes.csv. Después lista las
#   variables en las que algún mes se aparta más de 5 puntos de la mediana de los meses.
#%% celda 18 [texto]
## 8. Tabla de calidad por mes

Para cada variable y cada mes, el **% de nulos** y el **% de ceros**, los dos **sobre todas las filas del mes** (como en `z701`): las "dos reglas de oro" de la Clase 08.
- **Un salto de nulos** suele ser un mal *left join*.
- **Un salto de ceros** suele ser una imputación por defecto.

Se guarda completa en `exp/01_calidad_por_mes.csv`, como insumo de la etapa 4. Abajo se listan las variables donde algún mes se aparta más de 5 puntos del resto.

#%% celda 19 [código]
t0 = time.time()
agregados = ',\n    '.join(
    f'avg(("{c}" is null)::INT) as "nulos__{c}", avg(coalesce("{c}" = 0, false)::INT) as "ceros__{c}"'
    for c in variables
)
ancho = con.execute(f"select foto_mes,\n    {agregados}\nfrom base group by 1 order by 1").df()

calidad = (ancho.melt(id_vars='foto_mes', var_name='medida_variable', value_name='proporcion')
                .assign(medida=lambda d: d['medida_variable'].str.split('__').str[0],
                        variable=lambda d: d['medida_variable'].str.split('__').str[1])
                .pivot_table(index=['variable', 'medida'], columns='foto_mes', values='proporcion')
                .mul(100).round(2))
calidad.to_csv(CALIDAD_CSV)
print(f'Guardado: {CALIDAD_CSV} · {len(calidad)} filas · {time.time() - t0:.0f} s')

#%% celda 20 [código]
# Variables donde algún mes se aparta más de 5 puntos de la mediana de los meses
desvio = calidad.sub(calidad.median(axis=1), axis=0).abs().max(axis=1)
saltos = calidad[desvio > 5].assign(max_desvio_pp=desvio[desvio > 5]).sort_values('max_desvio_pp', ascending=False)
saltos

# [Anotación · líneas 300–317] Celdas de texto de cierre: enumeran los saltos que el texto dice esperar en la
#   tabla de calidad (Master_fultimo_cierre y Visa_fultimo_cierre con 69 % de ceros en 202106, Visa_mpagado, los
#   débitos automáticos de Visa en 202103, y ccajas_depositos con 100 % de ceros en 202105, que queda debajo del
#   umbral de 5 puntos). La última celda cierra la conexión de DuckDB.
#%% celda 21 [texto]
**Qué esperar** (verificado al preparar la etapa y en la corrida de prueba del 2026-10-05; ver CLAUDE.md §2.2):
- `Master_fultimo_cierre` y `Visa_fultimo_cierre`: 69 % en cero en `202106`, 0 % los otros meses;
- `Visa_mpagado`: ~70 % de ceros en `202105` y `202108`, contra ~86 % el resto;
- `ctarjeta_visa_debitos_automaticos` y `mttarjeta_visa_debitos_automaticos`: 43 % de ceros en `202103`, contra 35–37 % después (hallazgo de la corrida de prueba);
- `ccajas_depositos` (100 % en cero en `202105`) **no** aparece: siempre está cerca del 96 %, así que el salto queda debajo del umbral de 5 puntos. Mirarlo en el CSV.

Si aparece algo más, se anota para la etapa 4.

#%% celda 22 [texto]
## 9. Cierre

- **Tabla de verificación de la ficha:** se cumplen los controles 1 a 8. El 9 (reproducibilidad) se cumple corriendo el notebook entero en un kernel nuevo: *Restart* → *Run All*.
- **Registro:** anotar en `decisiones.md` el resultado de la verificación y cualquier hallazgo nuevo de la tabla de calidad.
- **Lo que sigue:** etapa 2, la línea base con LightGBM (necesita su ficha). El próximo notebook lee `data/competencia_01_base.parquet`.

#%% celda 23 [código]
con.close()
```

### notebook/07_ensamble.ipynb

Promedia las probabilidades por semilla guardadas por dos corridas del 03 (40 modelos) y escribe el CSV entregado con los 12.000 clientes de mayor promedio, además de 20 archivos con promedios de 20 modelos sorteados.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–16] Celdas de texto de presentación. El notebook no entrena: junta las probabilidades
#   por semilla guardadas por el 03 para varios submits y arma un archivo con el promedio de todos los modelos
#   cortado en N (llamado 'locro') y 20 archivos con promedios de 20 modelos sorteados.
#%% celda 1 [texto]
# 07 · Ensamble final ("el locro")

**Paso 3 del orden vigente** (CLAUDE.md §7). Junta las probabilidades por semilla que guardó el `03` para varios submits (`../exp/03_entrega/<ORIGEN>/`) y arma, **sin entrenar**:

1. **El locro:** el promedio de **todos** los modelos (todas las semillas de todos los orígenes), cortado en N. Es **un solo archivo**: el candidato a entrega final. El bot evalúa en el privado el mejor archivo del público del último submit, así que la entrega final tiene que ser un solo archivo (CLAUDE.md §1.2).
2. **La distribución de ensambles** (sugerencia de Bolaños en la tutoría): 20 archivos, cada uno el promedio de 20 modelos sorteados entre todos. Mandados juntos, el bot devuelve la media y el desvío **de ensambles**, en vez de semillas sueltas.

Los orígenes tienen que usar **la misma clase** (por ejemplo, `bajas`): así sus probabilidades están en la misma escala y se pueden promediar. Promediar con un modelo `baja2` sería "mezclar peras con bananas" (Bolaños).

#%% celda 2 [texto]
## 1. Parámetros

- **`ORIGENES`:** los `NOMBRE_SUBMIT` de submits hechos con el `03`, con la misma configuración.
- **`N`:** los envíos. Decidido el 2026-10-05: 12.000, el centro de la meseta del público.
- **`NOMBRE`:** prefijo de los archivos y de los dos submits: `<NOMBRE>` (el locro, un archivo) y `<NOMBRE>Dist` (los 20 ensambles).

# [Anotación · líneas 18–48] Parámetros: ORIGENES = 'fe03z470bajasV5B2345Opt42' y
#   'fe03z470bajasV5B2345Opt42J2', N = 12.000, NOMBRE = 'final01fe03x40N12000', 20 ensambles de 20 modelos y
#   semilla de sorteo 979201. Verifica que N esté entre 8.000 y 15.000, que la carpeta de salida no exista y que
#   estén las probabilidades de cada origen.
#%% celda 3 [código]
from pathlib import Path
from datetime import datetime
import json
import re

import duckdb
import numpy as np
import pandas as pd

# --- Parámetros -------------------------------------------------------------
ORIGENES = ['fe03z470bajasV5B2345Opt42', 'fe03z470bajasV5B2345Opt42J2']
N = 12_000                                                    
NOMBRE = 'final01fe03x40N12000'                               # <- único, sin espacios
ENSAMBLES, MODELOS_POR_ENSAMBLE = 20, 20                     # distribución de ensambles (Bolaños)
SEMILLA_SORTEO = 979201                                      # la semilla primigenia

BASE_PARQUET = Path('../data/competencia_01_base.parquet')
EXP02 = Path('../exp/02_linea_base')
EXP03 = Path('../exp/03_entrega')
ENTREGAS = Path('../entregas')
MES_FUTURO = 202108
# -----------------------------------------------------------------------------

assert 8_000 <= N <= 15_000, 'El bot acepta entre 8.000 y 15.000 registros'
assert re.fullmatch(r'[A-Za-z0-9_]+', NOMBRE)
SALIDA = ENTREGAS / NOMBRE
assert not SALIDA.exists(), f'Ya existe {SALIDA}: los nombres no se repiten'
for origen in ORIGENES:
    assert (EXP03 / origen).exists(), f'No están las probabilidades de {origen}'
print(f'Orígenes: {ORIGENES} · N = {N:,} · submits: {NOMBRE} (1 archivo) y {NOMBRE}Dist ({ENSAMBLES} archivos)')

# [Anotación · líneas 50–87] Lee del parquet base los 164.647 numero_de_cliente de 202108. Para cada origen
#   carga sus 20 vectores de probabilidad (con las semillas guardadas por el 03 en esa carpeta o, si no hay
#   archivo, las del 02) y verifica que su promedio coincide con el semillerío guardado y que el corte de ese
#   promedio reproduce el CSV de semillerío del origen. Apila todos los modelos en una matriz.
#%% celda 4 [texto]
## 2. Probabilidades

Se cargan las 20 semillas de cada origen (las del `semillas.json` que guardó el `03` en su carpeta, si existe; si no, las del `02`), en el orden de las filas de `202108` del parquet base.

**Controles:**
- el promedio de cada origen tiene que ser **idéntico** al semillerío que guardó el `03`;
- y el semillerío de cada origen, cortado en su N original, tiene que reproducir exactamente su CSV de semillerío. Si coinciden, los clientes están en el orden correcto.

#%% celda 5 [código]
SEMILLAS = json.loads((EXP02 / 'semillas.json').read_text())['semillas']
assert len(SEMILLAS) == 20
ids_futuro = duckdb.sql(f'''select numero_de_cliente from read_parquet('{BASE_PARQUET.as_posix()}')
                            where foto_mes = {MES_FUTURO}''').df()['numero_de_cliente'].to_numpy()
assert ids_futuro.dtype == np.int64 and len(ids_futuro) == 164_647


def top_n(prob, n=N):
    return ids_futuro[np.argsort(-prob, kind='stable')[:n]]


bloques_probs, etiquetas = [], []
for origen in ORIGENES:
    # las semillas de cada origen: las que guardó el 03 (juegos de semillas), o las del 02
    archivo_sem = EXP03 / origen / 'semillas.json'
    semillas_o = json.loads(archivo_sem.read_text())['semillas'] if archivo_sem.exists() else SEMILLAS
    p = np.vstack([np.load(EXP03 / origen / f'prob_s{s}.npy') for s in semillas_o])
    assert p.shape == (20, len(ids_futuro))
    assert np.allclose(p.mean(axis=0), np.load(EXP03 / origen / 'prob_semillerio.npy')), f'{origen}: el promedio no coincide'
    csv_sem = ENTREGAS / origen / f'{origen}_semillerio.csv'
    ids_sem = np.loadtxt(csv_sem, dtype=np.int64)
    assert np.array_equal(ids_sem, top_n(p.mean(axis=0), len(ids_sem))), f'{origen}: el semillerío no se reproduce'
    bloques_probs.append(p)
    etiquetas += [f'{origen}_s{s}' for s in semillas_o]
    print(f'{origen}: 20 semillas · media de probabilidad {p.mean():.4f} · control OK')

MODELOS = np.vstack(bloques_probs)          # (20 × orígenes) × 164.647
print(f'{MODELOS.shape[0]} modelos en la olla')

# [Anotación · líneas 89–108] Calcula el promedio de todos los modelos y su lista de los N clientes de mayor
#   probabilidad. Sortea 20 subconjuntos de 20 modelos sin reposición con default_rng(979201) y arma la lista de
#   cada uno. Imprime cuántos clientes comparte la lista general con el semillerío de cada origen y con cada
#   subconjunto.
#%% celda 6 [texto]
## 3. El locro y la distribución de ensambles

- **Locro:** el promedio de todos los modelos. Cada origen pesa lo mismo, porque todos tienen 20 semillas.
- **Distribución:** `ENSAMBLES` sorteos sin reposición de `MODELOS_POR_ENSAMBLE` modelos, con `SEMILLA_SORTEO`. Cada ensamble es el promedio de sus modelos.

Se muestra cuánto se parece la lista del locro a la de cada origen, en N.

#%% celda 7 [código]
locro = MODELOS.mean(axis=0)
lista_locro = top_n(locro)

rng = np.random.default_rng(SEMILLA_SORTEO)
sorteos = [np.sort(rng.choice(len(MODELOS), MODELOS_POR_ENSAMBLE, replace=False)) for _ in range(ENSAMBLES)]
listas_dist = [top_n(MODELOS[idx].mean(axis=0)) for idx in sorteos]

en_comun = {o: len(set(top_n(p.mean(axis=0)).tolist()) & set(lista_locro.tolist())) for o, p in zip(ORIGENES, bloques_probs)}
print('Clientes del locro que también están en el semillerío de cada origen (en N):', en_comun)
coincid = [len(set(l.tolist()) & set(lista_locro.tolist())) / N for l in listas_dist]
print(f'Ensambles de la distribución contra el locro: media {100 * np.mean(coincid):.1f} % · mín {100 * min(coincid):.1f} %')

# [Anotación · líneas 110–134] Escribe <NOMBRE>_locro.csv y los 20 archivos <NOMBRE>Dist_eXX.csv; cada archivo
#   se relee y se verifica que tenga N líneas enteras, sin duplicados y con IDs de 202108. Guarda el vector
#   promedio en prob_locro.npy y la composición (orígenes, N, modelos, sorteos y semilla) en composicion.json.
#%% celda 8 [texto]
## 4. Archivos y checklist (CLAUDE.md §8)

#%% celda 9 [código]
ids_validos = set(ids_futuro.tolist())


def escribir(ids, ruta):
    pd.Series(ids, dtype='int64').to_csv(ruta, index=False, header=False)
    lineas = ruta.read_text().splitlines()
    assert all(re.fullmatch(r'\d+', l) for l in lineas), f'{ruta.name}: hay líneas que no son enteros'
    v = [int(l) for l in lineas]
    assert len(v) == N and len(set(v)) == N and set(v) <= ids_validos, ruta.name


SALIDA.mkdir(parents=True)
escribir(lista_locro, SALIDA / f'{NOMBRE}_locro.csv')
for k, lista in enumerate(listas_dist, 1):
    escribir(lista, SALIDA / f'{NOMBRE}Dist_e{k:02d}.csv')
(EXP03 / NOMBRE).mkdir(parents=True, exist_ok=True)
np.save(EXP03 / NOMBRE / 'prob_locro.npy', locro)
(EXP03 / NOMBRE / 'composicion.json').write_text(json.dumps({
    'origenes': ORIGENES, 'N': N, 'modelos': etiquetas,
    'sorteos': [[etiquetas[i] for i in idx] for idx in sorteos], 'semilla_sorteo': SEMILLA_SORTEO}, indent=2))
print(f'Checklist OK: 1 locro + {ENSAMBLES} ensambles en {SALIDA}')

# [Anotación · líneas 136–150] Agrega dos filas a registro_submits.md, una para los 20 ensambles y otra para
#   el archivo único, e imprime los dos mensajes de submit con los archivos a adjuntar.
#%% celda 10 [texto]
## 5. Registro y mensajes para el bot

- **`submit <NOMBRE>Dist`** con los 20 archivos `_e01` … `_e20`: la media y el desvío **de ensambles**.
- **`submit <NOMBRE>`** con **solo** el archivo `_locro.csv`: un punto. Es el candidato a **entrega final**, que tiene que ser el **último** submit.

#%% celda 11 [código]
REGISTRO = ENTREGAS / 'registro_submits.md'
with REGISTRO.open('a') as f:
    f.write(f"| {datetime.now():%Y-%m-%d %H:%M} | `{NOMBRE}Dist` | ensamble (07): {ENSAMBLES} ensambles de {MODELOS_POR_ENSAMBLE} modelos de {' + '.join(ORIGENES)} | {N:,} | "
            f"{ENSAMBLES}: `{NOMBRE}Dist_eXX.csv` | sorteo con {SEMILLA_SORTEO} | *(completar)* | *(completar)* | |\n")
    f.write(f"| {datetime.now():%Y-%m-%d %H:%M} | `{NOMBRE}` | locro (07): promedio de los {len(MODELOS)} modelos de {' + '.join(ORIGENES)} | {N:,} | "
            f"1: `{NOMBRE}_locro.csv` | 979201 → 20 primos por origen | *(completar)* | 0 (un archivo) | |\n")
print(f'submit {NOMBRE}Dist   → adjuntar los {ENSAMBLES} archivos {NOMBRE}Dist_eXX.csv de {SALIDA}/')
print(f'submit {NOMBRE}       → adjuntar SOLO {NOMBRE}_locro.csv de {SALIDA}/')
```

### notebook/02_linea_base.ipynb

Genera las 20 semillas y el archivo de configuración que leen los demás notebooks, y mide en los backtests A y B cuatro configuraciones de LightGBM con hiperparámetros fijos (z601 y z470, cada uno con dos esquemas de clase).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–29] Celdas de texto de presentación. Describen dos backtests con dos meses entre el
#   entrenamiento y el mes a predecir (A: entrena 202103–202104 y predice 202106; B: entrena 202103 y predice
#   202105) y cuatro configuraciones (hiperparámetros z601 o z470, cada uno con clase positiva BAJA+2 sola o
#   BAJA+1 más BAJA+2). MODO_RAPIDO = True corre una semilla por configuración y prueba; False corre 10.
#%% celda 1 [texto]
# 02 · Línea base con LightGBM (y comparación de clases)

**Etapa 2 del plan** (`fichas/etapa_2_linea_base.md`). Se adelanta la etapa 3.

**Qué mide:** cuánta plata gana un LightGBM **sin mejoras**, con variables crudas y hiperparámetros ya probados por la cátedra. Lo mide en dos backtests que imitan la competencia: dos meses de distancia entre el entrenamiento y el mes a predecir.

| Prueba | Entrena con | Predice |
|---|---|---|
| **A** | `202103`–`202104` | `202106` |
| **B** | `202103` | `202105` |

**Qué compara** (4 configuraciones):

| | `BAJA+2` sola | `BAJA+1` + `BAJA+2` |
|---|---|---|
| **`z601`** (lunes) | `z601_baja2` | `z601_bajas` |
| **`z470`** (jueves) | `z470_baja2` | `z470_bajas` |

**La ganancia siempre se mide con `BAJA+2` como único acierto**, aunque el modelo se entrene con las dos bajas. El corte es por **cantidad de envíos (N)**, en el máximo de la curva de ganancia suavizada (media móvil de 501, `z0607`).

**No** limpia variables, **no** arma variables nuevas y **no** optimiza: eso viene después. El primer submit sale del `03_entrega.ipynb`.

#%% celda 2 [texto]
## 1. Parámetros

**`MODO_RAPIDO = True`** corre **una sola semilla** por configuración y prueba: 8 modelos. Sirve para medir el tiempo real antes de la corrida completa (ficha: "conviene correr primero una sola semilla").

Con `False` corre las 10 semillas: 80 modelos. Cada modelo se guarda apenas termina; si se corta la corrida, al volver a correr **retoma** desde donde quedó.

# [Anotación · líneas 31–73] Importa las librerías (duckdb, lightgbm, matplotlib, numpy, pandas,
#   roc_auc_score) y define los parámetros: MODO_RAPIDO = False, semilla primigenia 979201, 20 semillas en total
#   y 10 para backtests, ganancia de 1.072.500 por BAJA+2 y costo de 27.500 por estímulo, ventana de suavizado
#   501, curva guardada hasta 25.000 envíos, cortes de 8.000 a 15.000 cada 500, las pruebas A y B y los dos
#   esquemas de clase positiva.
#%% celda 3 [código]
from itertools import product
from pathlib import Path
import json
import time
import warnings

import duckdb
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

warnings.filterwarnings('ignore', message='.*ChainedAssignmentError.*')  # falso positivo pandas 2.2 + Py 3.14

# --- Parámetros -------------------------------------------------------------
MODO_RAPIDO = False          # True: 1 semilla (medir tiempos) · False: corrida completa

BASE_PARQUET = Path('../data/competencia_01_base.parquet')
EXP = Path('../exp/02_linea_base')
CURVAS = EXP / 'curvas'      # una curva por (configuración, prueba, semilla)

SEMILLA_PRIMIGENIA = 979201
N_SEMILLAS_TOTAL = 20        # el 03 usa las 20 para el modelo final
N_SEMILLAS_BACKTEST = 10

GANANCIA_ACIERTO = 1_072_500
COSTO_ESTIMULO = 27_500
VENTANA_SUAVIZADO = 501      # media móvil centrada, como z0607
LARGO_CURVA = 25_000         # se guarda la curva hasta 25.000 envíos (el bot acepta 8.000–15.000)
CORTES = list(range(8_000, 15_001, 500))

PRUEBAS = {
    'A': {'train': [202103, 202104], 'test': 202106},
    'B': {'train': [202103], 'test': 202105},
}

# Clases positivas de cada esquema (la ganancia SIEMPRE cuenta solo BAJA+2)
CLASES = {
    'baja2': ['BAJA+2'],
    'bajas': ['BAJA+1', 'BAJA+2'],
}

# [Anotación · líneas 75–101] Define los dos juegos de hiperparámetros: z601 (num_leaves 16, learning_rate
#   0,019868, min_data_in_leaf 816, feature_fraction 0,277155, bagging_fraction 0,634130, 250 iteraciones,
#   max_bin 31) y z470 (num_leaves 8, learning_rate 0,027, min_data_in_leaf 76, feature_fraction 0,8, 1.000
#   iteraciones, max_bin 31). Excluye clase_ternaria y foto_mes de las variables. Escribe todo en
#   ../exp/02_linea_base/configuraciones.json, que leen los notebooks siguientes.
# Hiperparámetros de la cátedra, tal cual sus notebooks
HIPERPARAMETROS = {
    # z601 (lunes): model_params + num_boost_round=250. Su bagging_fraction NO tiene efecto
    # porque no fija bagging_freq; se deja así para reproducir el notebook de clase.
    'z601': dict(objective='binary', boosting='gbdt', first_metric_only=True,
                 boost_from_average=True, feature_pre_filter=False, max_bin=31,
                 num_leaves=16, learning_rate=0.019868, min_data_in_leaf=816,
                 feature_fraction=0.277155, bagging_fraction=0.634130,
                 num_iterations=250, verbose=-1),
    # z470 (jueves): PARAM$lgb de "LightGBM, una corrida"
    'z470': dict(objective='binary', boosting='gbdt', max_bin=31,
                 num_leaves=8, learning_rate=0.027, min_data_in_leaf=76,
                 feature_fraction=0.8, num_iterations=1000, verbose=-1),
}

VARIABLES_EXCLUIDAS = ['clase_ternaria', 'foto_mes']   # decisión de la etapa 2
# -----------------------------------------------------------------------------

EXP.mkdir(parents=True, exist_ok=True)
CURVAS.mkdir(parents=True, exist_ok=True)
assert BASE_PARQUET.exists(), f'Falta el dataset base: correr 01_pipeline_base ({BASE_PARQUET.resolve()})'

# Fuente única de la configuración: el 03_entrega lee este archivo en vez de copiar los parámetros
(EXP / 'configuraciones.json').write_text(json.dumps(
    {'hiperparametros': HIPERPARAMETROS, 'clases': CLASES, 'variables_excluidas': VARIABLES_EXCLUIDAS,
     'pruebas': PRUEBAS, 'cortes': CORTES, 'ventana_suavizado': VENTANA_SUAVIZADO,
     'ganancia_acierto': GANANCIA_ACIERTO, 'costo_estimulo': COSTO_ESTIMULO}, indent=2))

# [Anotación · líneas 103–130] Genera las semillas: arma con una criba todos los primos de 6 dígitos y sortea
#   20 sin reemplazo con numpy.random.default_rng(979201). Las primeras 10 son las de backtest (una sola en modo
#   rápido). Guarda la lista en semillas.json.
#%% celda 4 [texto]
## 2. Semillas

Salen de la semilla primigenia, como en `z0201`:
1. se arman todos los primos de 6 dígitos;
2. se sortean 20 sin reemplazo con `numpy.random.default_rng(979201)`.

Siempre dan **las mismas y en el mismo orden**. Las primeras 10 son las de los backtests; las 20, las del modelo final (`03`).

#%% celda 5 [código]
def primos_6_digitos():
    criba = np.ones(1_000_000, dtype=bool)
    criba[:2] = False
    for i in range(2, 1_001):
        if criba[i]:
            criba[i * i::i] = False
    return np.flatnonzero(criba[100_000:]) + 100_000


SEMILLAS = np.random.default_rng(SEMILLA_PRIMIGENIA).choice(
    primos_6_digitos(), size=N_SEMILLAS_TOTAL, replace=False).tolist()
SEMILLAS_BACKTEST = SEMILLAS[:N_SEMILLAS_BACKTEST]
SEMILLAS_A_USAR = SEMILLAS_BACKTEST[:1] if MODO_RAPIDO else SEMILLAS_BACKTEST

(EXP / 'semillas.json').write_text(json.dumps(
    {'semilla_primigenia': SEMILLA_PRIMIGENIA, 'semillas': SEMILLAS}, indent=2))
print('Semillas:', SEMILLAS)
print(f'En esta corrida: {len(SEMILLAS_A_USAR)} por configuración y prueba')

# [Anotación · líneas 132–169] Lee el parquet base con DuckDB. Las variables son todas las columnas menos
#   clase_ternaria y foto_mes (numero_de_cliente queda como variable). particion() devuelve los índices de
#   entrenamiento (meses de la prueba con clase conocida) y de prueba, y verifica con assert la distancia de dos
#   meses. Imprime filas y cantidad de positivos de cada prueba.
#%% celda 6 [texto]
## 3. Datos

Se lee el dataset base completo (~0,6 GB en memoria con `float32`). Las variables son todas menos `clase_ternaria` y `foto_mes`.
- **`foto_mes`:** con varios meses de entrenamiento, el modelo puede aprender "el mes", y en `202108` el valor queda fuera de rango.
- **`numero_de_cliente`:** queda como variable, como en los notebooks de la cátedra.

**Filas de entrenamiento:** solo las de los meses de la prueba **que tienen clase**. `202107` no se usa nunca para entrenar.

#%% celda 7 [código]
t0 = time.time()
# Se lee con DuckDB (pandas necesitaría pyarrow, que no está instalado)
df = duckdb.sql(f"select * from read_parquet('{BASE_PARQUET.as_posix()}')").df()
VARIABLES = [c for c in df.columns if c not in VARIABLES_EXCLUIDAS]
print(f'{len(df):,} filas · {len(VARIABLES)} variables · {time.time() - t0:.0f} s')
assert 'clase_ternaria' not in VARIABLES and 'foto_mes' not in VARIABLES
assert df['numero_de_cliente'].dtype == 'int64'
assert df[VARIABLES[1:]].dtypes.eq('float32').all(), 'las variables tienen que venir en float32'


def particion(prueba):
    """Índices de entrenamiento y de prueba de un backtest."""
    meses = PRUEBAS[prueba]
    es_train = df['foto_mes'].isin(meses['train']) & df['clase_ternaria'].notna()
    es_test = df['foto_mes'] == meses['test']
    assert not (es_train & es_test).any()
    assert df.loc[es_train, 'foto_mes'].max() < meses['test'] - 1, 'falta la distancia de 2 meses'
    return np.flatnonzero(es_train), np.flatnonzero(es_test)


# Control de la ficha (#1 y #2): meses y positivos de entrenamiento
for prueba in PRUEBAS:
    i_train, i_test = particion(prueba)
    clases_train = df['clase_ternaria'].iloc[i_train]
    print(f"{prueba}: train {sorted(int(m) for m in df['foto_mes'].iloc[i_train].unique())} ({len(i_train):,} filas) · "
          f"test {PRUEBAS[prueba]['test']} ({len(i_test):,}) · "
          f"BAJA+2 en train: {(clases_train == 'BAJA+2').sum():,} · "
          f"las dos bajas: {clases_train.isin(CLASES['bajas']).sum():,}")

# [Anotación · líneas 171–197] Funciones de ganancia: curva_ganancia ordena el mes de prueba por probabilidad
#   descendente y acumula +1.072.500 si la fila es BAJA+2 y −27.500 si no, hasta 25.000 posiciones; suavizar
#   aplica una media móvil centrada de 501 posiciones; meseta devuelve la posición (N) y el valor del máximo de
#   la curva suavizada.
#%% celda 8 [texto]
## 4. Funciones de ganancia

- **Curva de ganancia:**
  1. se ordena a los clientes del mes de prueba por probabilidad descendente;
  2. se acumula +1.072.500 si es `BAJA+2` y −27.500 si no lo es.

  El valor en la posición N es la ganancia de mandar N estímulos.
- **Meseta:** la curva se suaviza con una media móvil centrada de 501 posiciones y se toma su máximo. N es la posición del máximo; es "elegir N en la meseta" y no en un pico con suerte (`z0607`, CLAUDE.md §3).
- **Varias semillas:** se promedian las curvas posición por posición y después se suaviza. El desvío entre semillas sale de la meseta de cada semilla por separado.

#%% celda 9 [código]
def curva_ganancia(prob, es_baja2, largo=LARGO_CURVA):
    orden = np.argsort(-prob, kind='stable')
    ganancia = np.where(es_baja2[orden], GANANCIA_ACIERTO, -COSTO_ESTIMULO)
    return np.cumsum(ganancia)[:largo].astype(np.float64)


def suavizar(curva, ventana=VENTANA_SUAVIZADO):
    return pd.Series(curva).rolling(ventana, center=True, min_periods=ventana).mean().to_numpy()


def meseta(curva):
    """(N, ganancia) en el máximo de la curva suavizada."""
    s = suavizar(curva)
    i = int(np.nanargmax(s))
    return i + 1, float(s[i])

# [Anotación · líneas 199–241] correr_modelo entrena un LightGBM con los hiperparámetros de la configuración y
#   la semilla dada, con etiqueta 1 para las clases positivas del esquema, predice el mes de prueba y guarda en
#   un .npz la curva de ganancia y el AUC medido contra BAJA+2. El bucle recorre hiperparámetros × clases ×
#   pruebas × semillas y saltea los modelos que ya tienen archivo.
#%% celda 10 [texto]
## 5. Backtests

Para cada configuración, prueba y semilla:
1. entrenar;
2. predecir el mes de prueba;
3. guardar la curva de ganancia y el AUC.

El AUC se mide siempre contra `BAJA+2`, para que sea comparable entre las dos clases. Cada modelo se guarda en `curvas/` apenas termina; si ya existe, se saltea.

#%% celda 11 [código]
def archivo_curva(hiper, clase, prueba, semilla):
    return CURVAS / f'{hiper}_{clase}_{prueba}_s{semilla}.npz'


def correr_modelo(hiper, clase, prueba, semilla):
    i_train, i_test = particion(prueba)
    X_train = df[VARIABLES].iloc[i_train]
    y_train = df['clase_ternaria'].iloc[i_train].isin(CLASES[clase]).astype(int).to_numpy()

    params = dict(HIPERPARAMETROS[hiper])
    rondas = params.pop('num_iterations')
    params['seed'] = semilla

    modelo = lgb.train(params, lgb.Dataset(X_train, label=y_train), num_boost_round=rondas)
    prob = modelo.predict(df[VARIABLES].iloc[i_test])
    es_baja2 = (df['clase_ternaria'].iloc[i_test] == 'BAJA+2').to_numpy()

    np.savez(archivo_curva(hiper, clase, prueba, semilla),
             curva=curva_ganancia(prob, es_baja2),
             auc=roc_auc_score(es_baja2, prob))


corridas = list(product(HIPERPARAMETROS, CLASES, PRUEBAS, SEMILLAS_A_USAR))
pendientes = [c for c in corridas if not archivo_curva(*c).exists()]
print(f'{len(corridas)} modelos en esta corrida · {len(pendientes)} pendientes')

t_total = time.time()
for k, (hiper, clase, prueba, semilla) in enumerate(pendientes, 1):
    t0 = time.time()
    correr_modelo(hiper, clase, prueba, semilla)
    print(f'[{k}/{len(pendientes)}] {hiper}_{clase} · {prueba} · semilla {semilla} · {time.time() - t0:.0f} s')
print(f'Listo en {(time.time() - t_total) / 60:.1f} min')

# [Anotación · líneas 243–284] Para cada configuración y prueba promedia las curvas de las semillas posición
#   por posición y calcula N y ganancia de la meseta del promedio, media y desvío de la meseta de cada semilla,
#   AUC medio y la ganancia promedio en cada corte de 8.000 a 15.000. Guarda la tabla en resumen.csv
#   (resumen_rapido.csv en modo rápido).
#%% celda 12 [texto]
## 6. Resumen por configuración

Para cada configuración y prueba:

| Columna | Qué es |
|---|---|
| `N_meseta`, `ganancia_meseta` | N y ganancia en el máximo de la curva promedio suavizada |
| `ganancia_media`, `ganancia_desvio` | Media y desvío de la meseta de cada semilla |
| `auc_medio` | AUC contra `BAJA+2`, promedio entre semillas |
| `g_8000` … `g_15000` | Ganancia promedio en N fijos, el rango del bot |

#%% celda 13 [código]
def cargar(hiper, clase, prueba, semillas):
    datos = [np.load(archivo_curva(hiper, clase, prueba, s)) for s in semillas]
    return np.vstack([d['curva'] for d in datos]), np.array([float(d['auc']) for d in datos])


filas = []
promedios = {}
for hiper, clase, prueba in product(HIPERPARAMETROS, CLASES, PRUEBAS):
    curvas, aucs = cargar(hiper, clase, prueba, SEMILLAS_A_USAR)
    promedio = curvas.mean(axis=0)
    promedios[(hiper, clase, prueba)] = promedio
    n_mes, g_mes = meseta(promedio)
    por_semilla = np.array([meseta(c)[1] for c in curvas])
    fila = {'config': f'{hiper}_{clase}', 'prueba': prueba, 'semillas': len(curvas),
            'N_meseta': n_mes, 'ganancia_meseta': g_mes,
            'ganancia_media': por_semilla.mean(), 'ganancia_desvio': por_semilla.std(ddof=1) if len(curvas) > 1 else np.nan,
            'auc_medio': aucs.mean()}
    fila.update({f'g_{n}': promedio[n - 1] for n in CORTES})
    filas.append(fila)

resumen = pd.DataFrame(filas)
resumen.to_csv(EXP / ('resumen_rapido.csv' if MODO_RAPIDO else 'resumen.csv'), index=False)

vista = resumen.pivot(index='config', columns='prueba',
                      values=['ganancia_meseta', 'ganancia_desvio', 'N_meseta', 'auc_medio'])
(vista.style
     .format('{:,.0f}', subset=[c for c in vista.columns if c[0] in ('ganancia_meseta', 'ganancia_desvio')])
     .format('{:,.0f}', subset=[c for c in vista.columns if c[0] == 'N_meseta'])
     .format('{:.4f}', subset=[c for c in vista.columns if c[0] == 'auc_medio']))

# [Anotación · líneas 286–318] Grafica la curva promedio suavizada de cada configuración en A y en B, con una
#   franja para el rango de 8.000 a 15.000 envíos, y, si hay más de una semilla, un boxplot de la meseta por
#   semilla.
#%% celda 14 [texto]
## 7. Gráficos

- **Arriba:** curva promedio suavizada de cada configuración, en A y en B. La franja gris es el rango que acepta el bot (8.000–15.000).
- **Abajo:** distribución de la meseta entre semillas (solo con la corrida completa).

#%% celda 15 [código]
fig, ejes = plt.subplots(1, 2, figsize=(15, 5), sharey=False)
for eje, prueba in zip(ejes, PRUEBAS):
    for hiper, clase in product(HIPERPARAMETROS, CLASES):
        s = suavizar(promedios[(hiper, clase, prueba)])
        eje.plot(np.arange(1, len(s) + 1), s / 1e6, label=f'{hiper}_{clase}')
    eje.axvspan(min(CORTES), max(CORTES), color='grey', alpha=0.12)
    eje.set_title(f"Prueba {prueba}: entrena {PRUEBAS[prueba]['train']} → predice {PRUEBAS[prueba]['test']}")
    eje.set_xlabel('Cantidad de envíos (N)')
    eje.set_ylabel('Ganancia suavizada (millones)')
    eje.legend()
plt.tight_layout()
plt.show()

if len(SEMILLAS_A_USAR) > 1:
    fig, ejes = plt.subplots(1, 2, figsize=(15, 4))
    for eje, prueba in zip(ejes, PRUEBAS):
        datos, nombres = [], []
        for hiper, clase in product(HIPERPARAMETROS, CLASES):
            curvas, _ = cargar(hiper, clase, prueba, SEMILLAS_A_USAR)
            datos.append([meseta(c)[1] / 1e6 for c in curvas])
            nombres.append(f'{hiper}_{clase}')
        eje.boxplot(datos, tick_labels=nombres)
        eje.set_title(f'Prueba {prueba}: meseta por semilla (millones)')
        eje.tick_params(axis='x', rotation=20)
    plt.tight_layout()
    plt.show()

# [Anotación · líneas 320–354] Arma la tabla de elección: ganancia de meseta de cada configuración en A y B,
#   su diferencia porcentual contra el máximo de cada prueba, un N sugerido (promedio de los N de A y B,
#   redondeado a 500 y acotado a 8.000–15.000) y una columna que indica si supera 123 millones en B y 360,8
#   millones en A. Las celdas de texto enuncian el criterio de elección y el cierre de la etapa.
#%% celda 16 [texto]
## 8. Elección (la decide el usuario)

**Criterio de la ficha:**
- gana la configuración que gana en A **y** en B;
- si cada prueba da un ganador distinto, gana la más estable (menor desvío);
- ante una diferencia chica, decide la estabilidad, no la media puntual.

La tabla de abajo muestra:
- la ganancia de cada configuración **relativa a la mejor** de cada prueba;
- el N sugerido para el primer submit: promedio de los N de A y B, redondeado a 500 y acotado a 8.000–15.000 (decisión 5).

**Pisos a superar** (CLAUDE.md §3):
- **B:** $123 M (reglas de la segmentación);
- **A:** $195 M (reglas) y $360,8 M (árbol de `z0607`).

Con `MODO_RAPIDO = True` es una sola semilla: **no sirve para decidir**, solo para medir tiempos.

#%% celda 17 [código]
eleccion = resumen.pivot(index='config', columns='prueba', values='ganancia_meseta')
eleccion = eleccion.join(resumen.pivot(index='config', columns='prueba', values='N_meseta').add_prefix('N_'))
for prueba in PRUEBAS:
    eleccion[f'vs_mejor_{prueba}_%'] = 100 * (eleccion[prueba] / eleccion[prueba].max() - 1)
eleccion['N_sugerido'] = (((eleccion['N_A'] + eleccion['N_B']) / 2 / 500).round() * 500).clip(8_000, 15_000).astype(int)
eleccion['supera_pisos'] = (eleccion['B'] > 123e6) & (eleccion['A'] > 360.8e6)
eleccion.sort_values('A', ascending=False).style.format(
    {'A': '{:,.0f}', 'B': '{:,.0f}', 'N_A': '{:,.0f}', 'N_B': '{:,.0f}',
     'vs_mejor_A_%': '{:+.1f}', 'vs_mejor_B_%': '{:+.1f}', 'N_sugerido': '{:,}'})

#%% celda 18 [texto]
## 9. Cierre

- **Registro:** anotar en `decisiones.md` el **experimento #1** (tabla de A y B por configuración, con semillas) y la configuración elegida, con su N sugerido.
- **Lo que sigue:** `03_entrega.ipynb`, que entrena la configuración elegida con `202103`–`202106` y las 20 semillas, predice `202108` y genera los 20 CSV del primer submit.
- **Para el verificador:** fuga de información (variables, meses), ganancia con `BAJA+2` como único acierto, corte por N, semillas, hiperparámetros.
```

### notebook/08_optuna.ipynb

Busca hiperparámetros de LightGBM con Optuna sobre las variables de la combinación B2+B3+B4+B5, valida las candidatas contra z470 con todos los datos y escribe el JSON de la prueba elegida, que lee el 03.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–15] Celdas de texto de presentación. Describen la búsqueda con Optuna sobre las
#   variables de la combinación B2+B3+B4+B5 con base V5, que maximiza la ganancia de meseta de la prueba A con
#   todas las bajas y el 20 % de los CONTINUA; la validación de las 3 pruebas de mayor ganancia con todos los
#   datos y 5 semillas en A y C contra z470; y la escritura del JSON de la prueba elegida.
#%% celda 1 [texto]
# 08 · Hiperparámetros con Optuna (etapa 7)

**Ficha:** `fichas/etapa_7_hiperparametros.md` (las seis decisiones van con la recomendación).

1. **Optuna** busca hiperparámetros de LightGBM con las variables de `fe02` (`B2+B3+B4+B5`, base V5, 507 variables), optimizando la ganancia en la meseta de la prueba **A** (entrena `202103`–`202104`, predice `202106` completo).
   - Para que cada prueba sea rápida, entrena con **todas las bajas y el 20 % de los `CONTINUA`** (las mismas filas en todas las pruebas).
   - La prueba 0 es `z470`, cargada a mano.
2. **Validación:** las 3 mejores, con **todos los datos** y `min_data_in_leaf` ÷ 0,2 (el truco de `z494`), 5 semillas, en A y C. Se comparan semilla por semilla contra `z470` (las curvas del `05`).
3. **Elección** (la decide el usuario): `ELEGIDA` = el número de prueba. Se escribe `hiperparametros.json` para el `03`.

`MODO_RAPIDO = True`: 3 pruebas en un estudio aparte (`..._rapido`, no se mezcla con el de verdad) y la validación de la mejor con 1 semilla, solo en A. Sirve para medir tiempos.

#%% celda 2 [texto]
## 1. Parámetros

# [Anotación · líneas 17–52] Importa las librerías (optuna, ttest_rel y wilcoxon de scipy) y define los
#   parámetros con los que está guardado el notebook: MODO_RAPIDO = False, N_PRUEBAS = 50, ELEGIDA = 44, CONFIG
#   'z470_bajas', BASE 'V5', BLOQUES 'B2+B3+B4+B5', prueba de búsqueda A, FRACCION = 0,2, validación de las 3
#   primeras con 5 semillas en A y C, semilla 979201, nombre del estudio 'e7_fe02_A_us20', almacenamiento en un
#   archivo SQLite y N_ENVIOS = 12.000. El README indica ELEGIDA = 42, y el JSON incluido en el repositorio es
#   el de la prueba 42.
#%% celda 3 [código]
from pathlib import Path
import json
import time
import warnings

import duckdb
import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from scipy.stats import ttest_rel, wilcoxon

warnings.filterwarnings('ignore', message='.*ChainedAssignmentError.*')  # falso positivo pandas 2.2 + Py 3.14
optuna.logging.set_verbosity(optuna.logging.WARNING)

# --- Parámetros -------------------------------------------------------------
MODO_RAPIDO = False              # True: 3 pruebas (estudio aparte) · False: N_PRUEBAS
N_PRUEBAS = 50                  # decisión 4 (si a la mitad todavía mejora, se suben: el estudio se retoma)
ELEGIDA = 44                  # <- después de la validación: el número de prueba elegida

CONFIG, BASE, BLOQUES = 'z470_bajas', 'V5', 'B2+B3+B4+B5'      # las variables de fe02
PRUEBA_OPTUNA = 'A'             # decisión 1
FRACCION = 0.2                  # decisión 2: fracción de CONTINUA en Optuna
TOP, SEMILLAS_VAL, PRUEBAS_VAL = 3, 5, ['A', 'C']                # decisión 5
SEMILLA_PRIMIGENIA = 979201
PRUEBA_C = {'train': [202103, 202104, 202105], 'test': 202106}

ESTUDIO = 'e7_fe02_A_us20' + ('_rapido' if MODO_RAPIDO else '')
EXP02, EXP05 = Path('../exp/02_linea_base'), Path('../exp/05_variables')
EXP = Path('../exp/08_optuna')
CURVAS = EXP / 'curvas'
STORAGE = f"sqlite:///{(EXP / ('optuna_e7' + ('_rapido' if MODO_RAPIDO else '') + '.db')).as_posix()}"
LARGO_CURVA = 25_000
N_ENVIOS = 12_000               # el N decidido: también se reporta la ganancia ahí
# -----------------------------------------------------------------------------

# [Anotación · líneas 54–72] Lee configuraciones.json y semillas.json del 02 y bloques.json del 05; toma de
#   ahí la lista de variables de la combinación, las fuentes, los NA por mes y la ruta del parquet. En modo
#   rápido reduce a 3 pruebas, valida 1 con 1 semilla y sólo en A.
CURVAS.mkdir(parents=True, exist_ok=True)
config02 = json.loads((EXP02 / 'configuraciones.json').read_text())
PRUEBAS = {**config02['pruebas'], 'C': PRUEBA_C}
VENTANA_SUAVIZADO = config02['ventana_suavizado']
GANANCIA_ACIERTO, COSTO_ESTIMULO = config02['ganancia_acierto'], config02['costo_estimulo']
SEMILLAS = json.loads((EXP02 / 'semillas.json').read_text())['semillas']
HIPER, CLASE = CONFIG.split('_', 1)
POSITIVOS = config02['clases'][CLASE]
Z470 = dict(config02['hiperparametros'][HIPER])

bloques_05 = json.loads((EXP05 / 'bloques.json').read_text())
assert bloques_05['base'] == BASE and bloques_05['config'] == CONFIG and BLOQUES in bloques_05['variables']
VARIABLES = bloques_05['variables'][BLOQUES]
FUENTES, NA_EN_MES = bloques_05['fuentes'], bloques_05['na_en_mes']
FE_PARQUET = Path(bloques_05['fe_parquet'])
if MODO_RAPIDO:
    N_PRUEBAS, TOP, SEMILLAS_VAL, PRUEBAS_VAL = 3, 1, 1, ['A']
print(f'>>> estudio {ESTUDIO} · {N_PRUEBAS} pruebas · {len(VARIABLES)} variables · validación: top {TOP}, '
      f'{SEMILLAS_VAL} semillas, {PRUEBAS_VAL}')

# [Anotación · líneas 74–110] Carga del parquet sólo las columnas necesarias. matriz aplica los pases a NA por
#   mes a la columna y sus derivadas; particion devuelve los índices de entrenamiento con clase y los del mes de
#   prueba; curva_ganancia y meseta repiten la métrica del 02.
#%% celda 4 [texto]
## 2. Datos

Las mismas variables y la misma limpieza que el `05` (la lista exacta de `bloques.json`). Se cargan solo las columnas necesarias.

#%% celda 5 [código]
t0 = time.time()
columnas = ['numero_de_cliente', 'foto_mes', 'clase_ternaria'] + VARIABLES
lista = ', '.join(f'"{c}"' for c in columnas)
df = duckdb.sql(f"select {lista} from read_parquet('{FE_PARQUET.as_posix()}')").df()
print(f'{len(df):,} filas · {len(VARIABLES)} variables · {time.time() - t0:.0f} s')


def matriz(indices):
    X = df[VARIABLES].iloc[indices].copy()
    meses = df['foto_mes'].iloc[indices].to_numpy()
    for columna, meses_na in NA_EN_MES.items():
        afectadas = [v for v in VARIABLES if v == columna or columna in FUENTES.get(v, [])]
        X.loc[np.isin(meses, meses_na), afectadas] = np.nan
    return X


def particion(prueba):
    meses = PRUEBAS[prueba]
    es_train = df['foto_mes'].isin(meses['train']) & df['clase_ternaria'].notna()
    return np.flatnonzero(es_train), np.flatnonzero(df['foto_mes'] == meses['test'])


def curva_ganancia(prob, es_baja2, largo=LARGO_CURVA):
    orden = np.argsort(-prob, kind='stable')
    return np.cumsum(np.where(es_baja2[orden], GANANCIA_ACIERTO, -COSTO_ESTIMULO))[:largo].astype(np.float64)


def meseta(curva):
    s = pd.Series(curva).rolling(VENTANA_SUAVIZADO, center=True, min_periods=VENTANA_SUAVIZADO).mean().to_numpy()
    i = int(np.nanargmax(s))
    return i + 1, float(s[i])


# [Anotación · líneas 113–127] Submuestreo fijo para la búsqueda: del entrenamiento de la prueba A conserva
#   todas las filas que no son CONTINUA y las CONTINUA con un número aleatorio menor que 0,2 (generador con
#   semilla 979201). El mes de prueba 202106 va completo (164.114 filas). Arma un Dataset de LightGBM
#   reutilizable con max_bin 31 y feature_pre_filter en False.
# Submuestreo fijo para Optuna: todas las bajas y FRACCION de los CONTINUA (control 2)
i_train, i_test = particion(PRUEBA_OPTUNA)
clase_train = df['clase_ternaria'].iloc[i_train].to_numpy()
rng = np.random.default_rng(SEMILLA_PRIMIGENIA)
queda = (clase_train != 'CONTINUA') | (rng.random(len(i_train)) < FRACCION)
i_us = i_train[queda]
y_us = df['clase_ternaria'].iloc[i_us].isin(POSITIVOS).astype(int).to_numpy()
X_test = matriz(i_test)
es_baja2_test = (df['clase_ternaria'].iloc[i_test] == 'BAJA+2').to_numpy()
assert y_us.sum() == np.isin(clase_train, POSITIVOS).sum(), 'Tienen que quedar todas las bajas'
assert len(i_test) == 164_114, 'El mes de prueba va completo (control 3)'
dtrain_us = lgb.Dataset(matriz(i_us), label=y_us, params={'max_bin': 31, 'feature_pre_filter': False},
                        free_raw_data=False)
print(f'Optuna entrena con {len(i_us):,} filas ({y_us.sum():,} bajas + {(~np.isin(clase_train[queda], POSITIVOS)).sum():,} CONTINUA) '
      f'y evalúa en {len(i_test):,} filas de {PRUEBAS[PRUEBA_OPTUNA]["test"]}')

# [Anotación · líneas 129–173] Define los hiperparámetros fijos (binary, gbdt, max_bin 31, bagging_freq 1,
#   lambda_l1, lambda_l2 y min_gain_to_split en 0) y la función objetivo, que sugiere num_leaves (8–512),
#   min_data_in_leaf (10–2.000), learning_rate (0,01–0,1) y num_iterations (200–1.500) en escala logarítmica,
#   feature_fraction (0,2–1,0) y bagging_fraction (0,4–1,0), entrena con la submuestra y la primera semilla de
#   backtest y devuelve la ganancia de meseta en 202106. El estudio maximiza, usa TPESampler con semilla 979201,
#   se guarda en SQLite y se retoma si existe; la prueba 0 se encola con los valores de z470 (8 hojas,
#   min_data_in_leaf 15, learning_rate 0,027, 1.000 iteraciones, feature_fraction 0,8 y bagging_fraction 1,0).
#%% celda 6 [texto]
## 3. Optuna

- **Fijos:** `gbdt`, `max_bin` 31, `bagging_freq` 1, sin regularizaciones (Clase 08), `feature_pre_filter` en `False` (necesario para cambiar `min_data_in_leaf` sin rearmar el dataset).
- **Espacio** (decisión 3): `num_leaves` 8–512, `min_data_in_leaf` 10–2.000 (escala submuestreada), `learning_rate` 0,01–0,1 y `num_iterations` 200–1.500, todos logarítmicos; `feature_fraction` 0,2–1,0 y `bagging_fraction` 0,4–1,0.
  - El piso de `min_data_in_leaf` baja de 20 (ficha) a 10, para que entre `z470`: sus 76 a escala completa son ~15 en la escala submuestreada.
- **Prueba 0:** `z470` (8 hojas, `min_data_in_leaf` 15, 0,027, 1.000 árboles, 0,8, sin bagging).
- **Una semilla de LightGBM** en todas las pruebas, la primera de las de backtest. El sampler TPE usa la semilla primigenia. El estudio se retoma si se corta.

#%% celda 7 [código]
FIJOS = {'objective': 'binary', 'boosting': 'gbdt', 'max_bin': 31, 'bagging_freq': 1,
         'lambda_l1': 0.0, 'lambda_l2': 0.0, 'min_gain_to_split': 0.0,
         'feature_pre_filter': False, 'verbose': -1}
SEMILLA_MODELO = SEMILLAS[0]


def objetivo(trial):
    p = {**FIJOS,
         'num_leaves': trial.suggest_int('num_leaves', 8, 512, log=True),
         'min_data_in_leaf': trial.suggest_int('min_data_in_leaf', 10, 2000, log=True),
         'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
         'feature_fraction': trial.suggest_float('feature_fraction', 0.2, 1.0),
         'bagging_fraction': trial.suggest_float('bagging_fraction', 0.4, 1.0),
         'seed': SEMILLA_MODELO}
    rondas = trial.suggest_int('num_iterations', 200, 1500, log=True)
    t0 = time.time()
    modelo = lgb.train(p, dtrain_us, num_boost_round=rondas)
    n, g = meseta(curva_ganancia(modelo.predict(X_test), es_baja2_test))
    trial.set_user_attr('N_meseta', n)
    trial.set_user_attr('segundos', round(time.time() - t0))
    print(f'prueba {trial.number}: {g / 1e6:,.1f} M (N {n:,}) · hojas {p["num_leaves"]} · mdl {p["min_data_in_leaf"]} · '
          f'lr {p["learning_rate"]:.3f} · árboles {rondas} · ff {p["feature_fraction"]:.2f} · bf {p["bagging_fraction"]:.2f} · '
          f'{time.time() - t0:.0f} s')
    return g


estudio = optuna.create_study(study_name=ESTUDIO, storage=STORAGE, direction='maximize', load_if_exists=True,
                              sampler=optuna.samplers.TPESampler(seed=SEMILLA_PRIMIGENIA))
if len(estudio.trials) == 0:     # prueba 0: z470
    estudio.enqueue_trial({'num_leaves': 8, 'min_data_in_leaf': 15, 'learning_rate': 0.027, 'num_iterations': 1000,
                           'feature_fraction': 0.8, 'bagging_fraction': 1.0})
hechas = len([t for t in estudio.trials if t.state == optuna.trial.TrialState.COMPLETE])
t_total = time.time()
estudio.optimize(objetivo, n_trials=max(0, N_PRUEBAS - hechas))
print(f'{len(estudio.trials)} pruebas en el estudio · esta corrida: {(time.time() - t_total) / 60:.1f} min')

# [Anotación · líneas 175–189] Arma la tabla de pruebas completas ordenada por ganancia descendente, la guarda
#   en pruebas.csv, imprime la ganancia de la prueba 0 y toma como candidatas las TOP (3) primeras.
#%% celda 8 [texto]
## 4. Las mejores pruebas

Control 1: la prueba 0 (`z470` con submuestreo) tiene que dar del orden de la meseta de `B2+B3+B4+B5` en A del `05` (~368 M), sin ser igual.

#%% celda 9 [código]
pruebas = estudio.trials_dataframe(attrs=('number', 'value', 'params', 'user_attrs', 'state'))
pruebas = pruebas[pruebas['state'] == 'COMPLETE'].rename(columns=lambda c: c.replace('params_', '').replace('user_attrs_', ''))
pruebas['ganancia_M'] = pruebas['value'] / 1e6
pruebas = pruebas.sort_values('value', ascending=False)
pruebas.drop(columns=['value', 'state']).to_csv(EXP / ('pruebas_rapido.csv' if MODO_RAPIDO else 'pruebas.csv'), index=False)
print(f"Prueba 0 (z470 con submuestreo): {pruebas.set_index('number').loc[0, 'ganancia_M']:,.1f} M")
mejores = pruebas.head(TOP)['number'].tolist()
print('Las mejores:', mejores)
pruebas.head(10).drop(columns=['value', 'state']).round(3)

# [Anotación · líneas 191–236] params_completos pasa una prueba a la escala de todos los datos dividiendo
#   min_data_in_leaf por 0,2. entrenar_completo entrena con todas las filas de la prueba y devuelve la curva de
#   ganancia; curva_z470 lee del 05 la curva de z470 con las mismas variables y semilla. Un control exige que
#   z470 entrenado acá en A con la primera semilla difiera en menos de 1 de la curva del 05. Luego entrena cada
#   candidata en A y C con 5 semillas y guarda cada curva en .npy.
#%% celda 10 [texto]
## 5. Validación: con todos los datos, contra `z470`

Para cada una de las mejores: todos los datos de entrenamiento, `min_data_in_leaf` ÷ `FRACCION`, `SEMILLAS_VAL` semillas, en `PRUEBAS_VAL`. `z470` se lee del `05` (mismas semillas).

**Control 6:** `z470` entrenado acá con la primera semilla tiene que dar **exactamente** la curva del `05`. Si da distinto, algo cambió en los datos.

Con 5 semillas, el Wilcoxon no puede bajar de p = 0,0625. Por eso se informa también el **t pareado**, y la regla usa ese.

#%% celda 11 [código]
def params_completos(numero):
    p = estudio.trials[numero].params
    return {**FIJOS, 'num_leaves': p['num_leaves'], 'min_data_in_leaf': int(round(p['min_data_in_leaf'] / FRACCION)),
            'learning_rate': p['learning_rate'], 'feature_fraction': p['feature_fraction'],
            'bagging_fraction': p['bagging_fraction'], 'num_iterations': p['num_iterations']}


def entrenar_completo(params, prueba, semilla):
    i_tr, i_te = particion(prueba)
    y = df['clase_ternaria'].iloc[i_tr].isin(POSITIVOS).astype(int).to_numpy()
    p = dict(params)
    rondas = p.pop('num_iterations')
    modelo = lgb.train({**p, 'seed': semilla}, lgb.Dataset(matriz(i_tr), label=y), num_boost_round=rondas)
    return curva_ganancia(modelo.predict(matriz(i_te)), (df['clase_ternaria'].iloc[i_te] == 'BAJA+2').to_numpy())


def curva_z470(prueba, semilla):
    return np.load(EXP05 / 'curvas' / f'{CONFIG}_{BASE}_{BLOQUES}_{prueba}_s{semilla}.npz')['curva']


# Control 6
t0 = time.time()
dif = meseta(entrenar_completo(Z470, 'A', SEMILLAS[0]))[1] - meseta(curva_z470('A', SEMILLAS[0]))[1]
print(f'Control 6: z470 en A, semilla {SEMILLAS[0]}, contra el 05: diferencia {dif:,.0f} · {time.time() - t0:.0f} s')
assert abs(dif) < 1, 'z470 no reproduce la curva del 05'

curvas_val = {}
for numero in mejores:
    for prueba in PRUEBAS_VAL:
        for semilla in SEMILLAS[:SEMILLAS_VAL]:
            archivo = CURVAS / f'{ESTUDIO}_p{numero}_{prueba}_s{semilla}.npy'
            if not archivo.exists():
                t0 = time.time()
                np.save(archivo, entrenar_completo(params_completos(numero), prueba, semilla))
                print(f'prueba {numero} · {prueba} · semilla {semilla} · {time.time() - t0:.0f} s')
            curvas_val[(numero, prueba, semilla)] = np.load(archivo)

# [Anotación · líneas 238–271] Para cada candidata y prueba compara la meseta de cada semilla contra la de
#   z470: medias en millones, diferencia media, cantidad de semillas con diferencia positiva, p del t pareado, p
#   de Wilcoxon y ganancia promedio en N = 12.000. La columna adoptar es verdadera si la suma de diferencias A +
#   C es positiva en promedio, en ninguna prueba la diferencia es negativa con p < 0,05 (t pareado) y hay más de
#   una semilla. Guarda validacion.csv.
#%% celda 12 [texto]
## 6. Comparación pareada contra `z470`

Por prueba: la meseta de cada semilla, la diferencia contra `z470` (media, cuántas semillas mejoran, t pareado y Wilcoxon) y la ganancia en N = 12.000.

**Regla** (decisión 6): se adopta si **A + C**, sumando semilla por semilla, le gana a `z470`, y **en ninguna de las dos pierde** con p < 0,05 (t pareado).

#%% celda 13 [código]
filas = []
semillas_v = SEMILLAS[:SEMILLAS_VAL]
for numero in mejores:
    fila, difs = {'prueba': numero, **{k: v for k, v in params_completos(numero).items() if k not in FIJOS}}, {}
    for prueba in PRUEBAS_VAL:
        g_opt = np.array([meseta(curvas_val[(numero, prueba, s)])[1] for s in semillas_v])
        g_z = np.array([meseta(curva_z470(prueba, s))[1] for s in semillas_v])
        d = g_opt - g_z
        difs[prueba] = d
        fila[f'{prueba}_optuna'] = g_opt.mean() / 1e6
        fila[f'{prueba}_z470'] = g_z.mean() / 1e6
        fila[f'{prueba}_dif'] = d.mean() / 1e6
        fila[f'{prueba}_mejoran'] = f'{(d > 0).sum()}/{len(d)}'
        fila[f'{prueba}_p_t'] = ttest_rel(g_opt, g_z).pvalue if len(d) > 1 else np.nan
        fila[f'{prueba}_p_wilcoxon'] = wilcoxon(d).pvalue if len(d) >= 5 and np.any(d != 0) else np.nan
        fila[f'{prueba}_en_12000'] = np.mean([curvas_val[(numero, prueba, s)][N_ENVIOS - 1] for s in semillas_v]) / 1e6
        fila[f'{prueba}_z470_en_12000'] = np.mean([curva_z470(prueba, s)[N_ENVIOS - 1] for s in semillas_v]) / 1e6
    total = sum(difs.values())
    pierde = any(difs[p].mean() < 0 and fila[f'{p}_p_t'] < 0.05 for p in PRUEBAS_VAL)
    fila['adoptar'] = bool(total.mean() > 0 and not pierde and SEMILLAS_VAL > 1)
    filas.append(fila)

validacion = pd.DataFrame(filas)
validacion.to_csv(EXP / ('validacion_rapido.csv' if MODO_RAPIDO else 'validacion.csv'), index=False)
print('Pasan la regla:', validacion.query('adoptar')['prueba'].tolist() or 'ninguna', '(la decisión es del usuario)')
validacion.round(3).T

# [Anotación · líneas 273–289] Si ELEGIDA no es None, exige la corrida completa y que el número esté entre las
#   candidatas validadas, y escribe ../exp/08_optuna/hiperparametros_p<ELEGIDA>.json con el estudio, la prueba,
#   la configuración, la base, los bloques, la fracción de submuestreo, los hiperparámetros para todos los datos
#   y la fila de validación.
#%% celda 14 [texto]
## 7. Elección y `hiperparametros.json`

Con `ELEGIDA` = el número de prueba, se escribe `../exp/08_optuna/hiperparametros_p<ELEGIDA>.json` (uno por prueba, para que elegir otra no pise la anterior) con los hiperparámetros **para todos los datos** (`min_data_in_leaf` ya corregido), que lee el `03`. Con `None`, no se escribe nada.

#%% celda 15 [código]
if ELEGIDA is None:
    print('ELEGIDA = None: todavía no se eligió (mirar la validación).')
else:
    assert not MODO_RAPIDO, 'La elección se hace con la corrida completa'
    assert ELEGIDA in mejores, f'ELEGIDA tiene que ser una de las validadas: {mejores}'
    salida = {'estudio': ESTUDIO, 'prueba': int(ELEGIDA), 'config': CONFIG, 'base': BASE, 'bloques': BLOQUES,
              'fraccion_optuna': FRACCION, 'params': params_completos(ELEGIDA),
              'validacion': validacion.set_index('prueba').loc[ELEGIDA].to_dict()}
    archivo = EXP / f'hiperparametros_p{ELEGIDA}.json'          # uno por prueba: no se pisan
    archivo.write_text(json.dumps(salida, indent=2, default=str))
    print(f'Escrito {archivo}:', salida['params'])
```

### notebook/04_drift.ipynb

Define las variantes de limpieza V0 a V5 (variables excluidas y variables pasadas a NA en un mes), las escribe en variantes.json y las compara en los backtests A y B semilla por semilla.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–22] Celdas de texto de presentación. Describen variantes de limpieza acumulativas (V1
#   a V4) y una no acumulativa (V5), evaluadas con el protocolo del 02 (pruebas A y B, 10 semillas, meseta
#   suavizada, ganancia con BAJA+2) y comparadas semilla por semilla.
#%% celda 1 [texto]
# 04 · Limpieza por drift (experimento #2)

**Etapa 4 del plan** (`fichas/etapa_4_limpieza_drift.md`). Mide si sacar o neutralizar las variables con drift **sube la ganancia**, con el mismo protocolo del `02`: pruebas A y B, 10 semillas, meseta suavizada y ganancia solo con `BAJA+2`.

**Variantes acumulativas:** cada una suma un cambio a la anterior.

| Variante | Cambio sobre la anterior |
|---|---|
| **V0** | Línea base del `02`. **No se reentrena:** se leen sus curvas |
| **V1** | − `cprestamos_personales`, `mprestamos_personales` ("variable veneno") |
| **V2** | − `Master_fultimo_cierre`, `Visa_fultimo_cierre` (rotas en `202106`) |
| **V3** | − `Master_Finiciomora`, `Visa_Finiciomora` (PSI de 3–6) |
| **V4** | `ccajas_depositos` → `NA` en `202105` (100 % en cero ese mes) |
| **V5** | **No acumulativa:** V4 con los préstamos de vuelta (solo saca las variables rotas). Se agregó después del submit de V4 (pública 83,63 contra 88,09), para separar los préstamos del resto. Solo con `z470_bajas` |

Las semillas son las mismas en todas las variantes, así que la comparación es **pareada**, semilla por semilla. Las curvas ya calculadas no se recalculan: al agregar V5, solo se entrena V5.

#%% celda 2 [texto]
## 1. Parámetros

`MODO_RAPIDO = True` corre 1 semilla para medir el tiempo. Con `False` corre las 10. Igual que el `02`, retoma si se corta.

# [Anotación · líneas 24–60] Importa las librerías (incluye wilcoxon de scipy) y define los parámetros:
#   MODO_RAPIDO = False, configuraciones z470_bajas y z601_baja2, y los pasos de limpieza: V1 excluye
#   cprestamos_personales y mprestamos_personales; V2, Master_fultimo_cierre y Visa_fultimo_cierre; V3,
#   Master_Finiciomora y Visa_Finiciomora; V4 pasa ccajas_depositos a NA en 202105. V5 se corre sólo con
#   z470_bajas.
#%% celda 3 [código]
from itertools import product
from pathlib import Path
import json
import time
import warnings

import duckdb
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.metrics import roc_auc_score

warnings.filterwarnings('ignore', message='.*ChainedAssignmentError.*')  # falso positivo pandas 2.2 + Py 3.14

# --- Parámetros -------------------------------------------------------------
MODO_RAPIDO = False             # True: 1 semilla (medir tiempos) · False: 10 semillas

CONFIGS = ['z470_bajas', 'z601_baja2']   # decisión 1 de la ficha

# Cambios acumulativos: cada variante suma su paso a la anterior
PASOS = [
    ('V1', {'excluir': ['cprestamos_personales', 'mprestamos_personales']}),
    ('V2', {'excluir': ['Master_fultimo_cierre', 'Visa_fultimo_cierre']}),
    ('V3', {'excluir': ['Master_Finiciomora', 'Visa_Finiciomora']}),
    ('V4', {'na_en_mes': {'ccajas_depositos': [202105]}}),
]
V5_CONFIGS = ['z470_bajas']     # V5 (no acumulativa) solo con esta configuración

BASE_PARQUET = Path('../data/competencia_01_base.parquet')
EXP02 = Path('../exp/02_linea_base')
EXP = Path('../exp/04_drift')
CURVAS = EXP / 'curvas'
LARGO_CURVA = 25_000
# -----------------------------------------------------------------------------

# [Anotación · líneas 62–98] Lee del 02 los hiperparámetros, clases, pruebas, cortes y las primeras 10
#   semillas. Construye las variantes acumulando los pasos sobre V0 (sin cambios) y define V5 como V4 sin la
#   exclusión de los préstamos personales: excluye las cuatro variables de V2 y V3 y pasa ccajas_depositos a NA
#   en 202105. Escribe ../exp/04_drift/variantes.json, que lee el 03.
CURVAS.mkdir(parents=True, exist_ok=True)
assert (EXP02 / 'configuraciones.json').exists(), 'Falta la salida del 02'

config02 = json.loads((EXP02 / 'configuraciones.json').read_text())
HIPERPARAMETROS = config02['hiperparametros']
CLASES = config02['clases']
PRUEBAS = config02['pruebas']
CORTES = config02['cortes']
VENTANA_SUAVIZADO = config02['ventana_suavizado']
GANANCIA_ACIERTO, COSTO_ESTIMULO = config02['ganancia_acierto'], config02['costo_estimulo']

SEMILLAS_BACKTEST = json.loads((EXP02 / 'semillas.json').read_text())['semillas'][:10]
SEMILLAS_A_USAR = SEMILLAS_BACKTEST[:1] if MODO_RAPIDO else SEMILLAS_BACKTEST

# Variantes acumuladas: V0 = línea base
VARIANTES = {'V0': {'excluir': [], 'na_en_mes': {}}}
anterior = VARIANTES['V0']
for nombre, paso in PASOS:
    actual = {'excluir': anterior['excluir'] + paso.get('excluir', []),
              'na_en_mes': {**anterior['na_en_mes'], **paso.get('na_en_mes', {})}}
    VARIANTES[nombre] = actual
    anterior = actual

# V5: V4 con los préstamos de vuelta (solo saca las variables rotas)
VARIANTES['V5'] = {'excluir': [c for c in VARIANTES['V4']['excluir'] if c not in dict(PASOS)['V1']['excluir']],
                   'na_en_mes': dict(VARIANTES['V4']['na_en_mes'])}


def corre(config, variante):
    """V5 solo se corre con las configuraciones de V5_CONFIGS."""
    return variante != 'V5' or config in V5_CONFIGS


# El 03 lee este archivo para hacer un submit con una variante
(EXP / 'variantes.json').write_text(json.dumps(VARIANTES, indent=2))
for nombre, v in VARIANTES.items():
    print(nombre, '· excluye:', v['excluir'] or '—', '· NA:', v['na_en_mes'] or '—')

# [Anotación · líneas 100–141] Lee el parquet base. variables_de devuelve las variables de la línea base menos
#   las excluidas por la variante; matriz arma la X de unas filas y aplica el pase a NA por mes sobre una copia.
#   Verifica con assert la cantidad de variables por variante (V0 153, V1 151, V2 149, V3 147, V4 147, V5 149),
#   que V5 conserva los préstamos y que en V4 ccajas_depositos queda NA en 202105 sin modificar el dataframe
#   original.
#%% celda 4 [texto]
## 2. Datos

Las variables de la línea base son todas menos la clase y `foto_mes`, como en el `02`. Cada variante saca las suyas. La transformación a `NA` se aplica **sobre la copia** de las filas de entrenamiento o de prueba, nunca sobre `df`.

#%% celda 5 [código]
t0 = time.time()
df = duckdb.sql(f"select * from read_parquet('{BASE_PARQUET.as_posix()}')").df()
VARIABLES_BASE = [c for c in df.columns if c not in config02['variables_excluidas']]
print(f'{len(df):,} filas · {len(VARIABLES_BASE)} variables en la línea base · {time.time() - t0:.0f} s')


def variables_de(variante):
    return [c for c in VARIABLES_BASE if c not in VARIANTES[variante]['excluir']]


def matriz(indices, variante):
    """X de la variante para unas filas, con sus transformaciones a NA (sobre una copia)."""
    X = df[variables_de(variante)].iloc[indices].copy()
    meses = df['foto_mes'].iloc[indices].to_numpy()
    for columna, meses_na in VARIANTES[variante]['na_en_mes'].items():
        X.loc[np.isin(meses, meses_na), columna] = np.nan
    return X


def particion(prueba):
    meses = PRUEBAS[prueba]
    es_train = df['foto_mes'].isin(meses['train']) & df['clase_ternaria'].notna()
    es_test = df['foto_mes'] == meses['test']
    return np.flatnonzero(es_train), np.flatnonzero(es_test)


# Controles 2 y 3 de la ficha
cantidades = {v: len(variables_de(v)) for v in VARIANTES}
print('Variables por variante:', cantidades)
assert cantidades == {'V0': 153, 'V1': 151, 'V2': 149, 'V3': 147, 'V4': 147, 'V5': 149}
assert {'cprestamos_personales', 'mprestamos_personales'} <= set(variables_de('V5')), 'V5 tiene que tener los préstamos'
_, i_test_B = particion('B')                       # B predice 202105
X_prueba = matriz(i_test_B, 'V4')
assert X_prueba['ccajas_depositos'].isna().all(), 'V4: ccajas_depositos tiene que ser NA en 202105'
assert df['ccajas_depositos'].notna().all(), 'df no se tiene que modificar'
del X_prueba

# [Anotación · líneas 143–160] Repite las funciones de ganancia del 02: curva acumulada por probabilidad
#   descendente, media móvil centrada de 501 y máximo de la curva suavizada.
#%% celda 6 [texto]
## 3. Ganancia (mismas funciones que el `02`)

#%% celda 7 [código]
def curva_ganancia(prob, es_baja2, largo=LARGO_CURVA):
    orden = np.argsort(-prob, kind='stable')
    ganancia = np.where(es_baja2[orden], GANANCIA_ACIERTO, -COSTO_ESTIMULO)
    return np.cumsum(ganancia)[:largo].astype(np.float64)


def suavizar(curva, ventana=VENTANA_SUAVIZADO):
    return pd.Series(curva).rolling(ventana, center=True, min_periods=ventana).mean().to_numpy()


def meseta(curva):
    s = suavizar(curva)
    i = int(np.nanargmax(s))
    return i + 1, float(s[i])

# [Anotación · líneas 162–200] Backtests: las curvas de V0 se leen de la carpeta del 02; las de V1 a V5 se
#   entrenan con los hiperparámetros del 02, la matriz de la variante y cada semilla, y se guardan en .npz con
#   su AUC contra BAJA+2. Se saltean los modelos ya corridos.
#%% celda 8 [texto]
## 4. Backtests de V1 a V4

V0 se lee de `../exp/02_linea_base/curvas/`. El resto se entrena acá, con los hiperparámetros del `02`.

#%% celda 9 [código]
def archivo_curva(config, variante, prueba, semilla):
    if variante == 'V0':
        return EXP02 / 'curvas' / f'{config}_{prueba}_s{semilla}.npz'
    return CURVAS / f'{config}_{variante}_{prueba}_s{semilla}.npz'


def correr_modelo(config, variante, prueba, semilla):
    hiper, clase = config.split('_', 1)
    i_train, i_test = particion(prueba)
    y_train = df['clase_ternaria'].iloc[i_train].isin(CLASES[clase]).astype(int).to_numpy()
    params = dict(HIPERPARAMETROS[hiper])
    rondas = params.pop('num_iterations')
    params['seed'] = semilla
    modelo = lgb.train(params, lgb.Dataset(matriz(i_train, variante), label=y_train), num_boost_round=rondas)
    prob = modelo.predict(matriz(i_test, variante))
    es_baja2 = (df['clase_ternaria'].iloc[i_test] == 'BAJA+2').to_numpy()
    np.savez(archivo_curva(config, variante, prueba, semilla),
             curva=curva_ganancia(prob, es_baja2), auc=roc_auc_score(es_baja2, prob))


faltan_v0 = [c for c in product(CONFIGS, ['V0'], PRUEBAS, SEMILLAS_A_USAR) if not archivo_curva(*c).exists()]
assert not faltan_v0, f'Faltan curvas del 02 (correrlo completo): {faltan_v0[:3]}'

corridas = [c for c in product(CONFIGS, [v for v in VARIANTES if v != 'V0'], PRUEBAS, SEMILLAS_A_USAR) if corre(*c[:2])]
pendientes = [c for c in corridas if not archivo_curva(*c).exists()]
print(f'{len(corridas)} modelos · {len(pendientes)} pendientes')

t_total = time.time()
for k, (config, variante, prueba, semilla) in enumerate(pendientes, 1):
    t0 = time.time()
    correr_modelo(config, variante, prueba, semilla)
    print(f'[{k}/{len(pendientes)}] {config} · {variante} · {prueba} · semilla {semilla} · {time.time() - t0:.0f} s')
print(f'Listo en {(time.time() - t_total) / 60:.1f} min')

# [Anotación · líneas 202–241] Arma el resumen por configuración, variante y prueba (N y ganancia de meseta
#   del promedio, media y desvío por semilla, AUC medio, ganancia en cada corte) y lo guarda en resumen.csv. En
#   la corrida completa verifica que V0 reproduce la ganancia de meseta del resumen del 02 con diferencia menor
#   que 1.
#%% celda 10 [texto]
## 5. Resumen por variante

La misma tabla que el `02`, para cada configuración y variante. El control 1 de la ficha: V0 tiene que dar igual que en el `02`.

#%% celda 11 [código]
def cargar(config, variante, prueba, semillas=SEMILLAS_A_USAR):
    datos = [np.load(archivo_curva(config, variante, prueba, s)) for s in semillas]
    return np.vstack([d['curva'] for d in datos]), np.array([float(d['auc']) for d in datos])


filas, promedios, por_semilla = [], {}, {}
for config, variante, prueba in product(CONFIGS, VARIANTES, PRUEBAS):
    if not corre(config, variante):
        continue
    curvas, aucs = cargar(config, variante, prueba)
    promedio = curvas.mean(axis=0)
    promedios[(config, variante, prueba)] = promedio
    por_semilla[(config, variante, prueba)] = np.array([meseta(c)[1] for c in curvas])
    n_mes, g_mes = meseta(promedio)
    fila = {'config': config, 'variante': variante, 'prueba': prueba, 'semillas': len(curvas),
            'N_meseta': n_mes, 'ganancia_meseta': g_mes,
            'ganancia_media': por_semilla[(config, variante, prueba)].mean(),
            'ganancia_desvio': por_semilla[(config, variante, prueba)].std(ddof=1) if len(curvas) > 1 else np.nan,
            'auc_medio': aucs.mean()}
    fila.update({f'g_{n}': promedio[n - 1] for n in CORTES})
    filas.append(fila)

resumen = pd.DataFrame(filas)
resumen.to_csv(EXP / ('resumen_rapido.csv' if MODO_RAPIDO else 'resumen.csv'), index=False)

if not MODO_RAPIDO:   # control 1: V0 igual que en el 02
    r02 = pd.read_csv(EXP02 / 'resumen.csv').set_index(['config', 'prueba'])['ganancia_meseta']
    for config, prueba in product(CONFIGS, PRUEBAS):
        v0 = resumen.query('config == @config and variante == "V0" and prueba == @prueba')['ganancia_meseta'].iloc[0]
        assert abs(v0 - r02[(config, prueba)]) < 1, f'V0 no reproduce el 02 en {config} {prueba}'
    print('Control 1 OK: V0 reproduce el 02')

(resumen.pivot_table(index=['config', 'variante'], columns='prueba', values=['ganancia_meseta', 'ganancia_desvio', 'N_meseta'])
        .style.format('{:,.0f}'))

# [Anotación · líneas 243–277] Comparación pareada: cada variante contra la anterior (de V0→V1 a V3→V4) y V5
#   contra V0 y contra V4. Para cada prueba calcula la diferencia de meseta semilla por semilla, su media en
#   millones, en cuántas semillas es positiva y el p del test de Wilcoxon (si hay al menos 6 diferencias). La
#   columna adoptar es verdadera si en ninguna prueba la media es negativa con p < 0,05 y, además, la media es
#   positiva en alguna prueba o se corrió más de una semilla. Guarda comparacion.csv.
#%% celda 12 [texto]
## 6. Comparación pareada: ¿cada paso suma?

Para cada configuración y prueba, cada variante se compara contra **la anterior**, semilla por semilla, con la meseta de cada semilla. **V5** se compara contra V0 (¿sacar solo las rotas suma?) y contra V4 (¿devolver los préstamos suma?):
- **`dif_media`:** diferencia promedio, en millones;
- **`mejoran`:** en cuántas de las 10 semillas mejora;
- **`p`:** test de Wilcoxon pareado, solo con 10 semillas.

**Regla de la ficha ("ante la duda, sacar")**, columna `adoptar`: se adopta el paso si mejora en al menos una prueba y en ninguna empeora con p < 0,05.

#%% celda 13 [código]
acumulativas = [v for v in VARIANTES if v != 'V5']
PARES = list(zip(acumulativas[:-1], acumulativas[1:])) + [('V0', 'V5'), ('V4', 'V5')]
filas = []
for config in CONFIGS:
    for ant, var in PARES:
        if not corre(config, var):
            continue
        fila = {'config': config, 'paso': f'{ant} → {var}'}
        empeora_signif, mejora_alguna = False, False
        for prueba in PRUEBAS:
            d = por_semilla[(config, var, prueba)] - por_semilla[(config, ant, prueba)]
            p = wilcoxon(d).pvalue if len(d) >= 6 and np.any(d != 0) else np.nan
            fila[f'{prueba}_dif_media'] = d.mean() / 1e6
            fila[f'{prueba}_mejoran'] = f'{(d > 0).sum()}/{len(d)}'
            fila[f'{prueba}_p'] = p
            mejora_alguna |= d.mean() > 0
            empeora_signif |= (d.mean() < 0) and (p < 0.05)
        fila['adoptar'] = (not empeora_signif) and (mejora_alguna or len(SEMILLAS_A_USAR) > 1)
        filas.append(fila)

comparacion = pd.DataFrame(filas)
comparacion.to_csv(EXP / ('comparacion_rapido.csv' if MODO_RAPIDO else 'comparacion.csv'), index=False)
comparacion.style.format({c: '{:+.1f}' for c in comparacion.columns if c.endswith('dif_media')}
                         | {c: '{:.3f}' for c in comparacion.columns if c.endswith('_p')})

# [Anotación · líneas 279–295] Grafica la meseta promedio de cada variante en A y en B con una barra de ± un
#   desvío entre semillas, una serie por configuración.
#%% celda 14 [texto]
## 7. Gráfico: ganancia por variante

La meseta promedio de cada variante, en A y en B, con una barra de ± desvío entre semillas.

#%% celda 15 [código]
fig, ejes = plt.subplots(1, 2, figsize=(14, 4.5))
for eje, prueba in zip(ejes, PRUEBAS):
    for config in CONFIGS:
        vs = [v for v in VARIANTES if corre(config, v)]
        medias = [por_semilla[(config, v, prueba)].mean() / 1e6 for v in vs]
        desvios = [por_semilla[(config, v, prueba)].std(ddof=1) / 1e6 if len(SEMILLAS_A_USAR) > 1 else 0 for v in vs]
        eje.errorbar(vs, medias, yerr=desvios, marker='o', capsize=4, label=config)
    eje.set_title(f"Prueba {prueba}: meseta por variante (millones)")
    eje.legend()
plt.tight_layout()
plt.show()

# [Anotación · líneas 297–326] Tabla de elección por configuración y variante: N sugerido (promedio de los N
#   de A y B redondeado a 500, entre 8.000 y 15.000), ganancia promedio de A y de B en ese N, su suma, el desvío
#   combinado y la diferencia contra V0. Las celdas de texto indican cómo pasar la variante elegida al 03.
#%% celda 16 [texto]
## 8. Elección (la decide el usuario)

- **Suma de A + B** en el N sugerido de cada variante (promedio de los N de A y B, redondeado a 500, entre 8.000 y 15.000), y diferencia contra V0.
- **Para el submit** (decisión 3): solo si la mejora en A + B supera el desvío entre semillas.
- **En el `03`:** `CONFIG` y `VARIANTE` (por ejemplo `'V4'`). El `03` lee `variantes.json` y el `resumen.csv` de esta carpeta.

Con `MODO_RAPIDO = True` es una sola semilla: **no sirve para decidir.**

#%% celda 17 [código]
filas = []
for config, variante in product(CONFIGS, VARIANTES):
    if not corre(config, variante):
        continue
    r = resumen.query('config == @config and variante == @variante').set_index('prueba')
    n = int(np.clip(round((r.loc['A', 'N_meseta'] + r.loc['B', 'N_meseta']) / 2 / 500) * 500, 8_000, 15_000))
    gA, gB = promedios[(config, variante, 'A')][n - 1], promedios[(config, variante, 'B')][n - 1]
    filas.append({'config': config, 'variante': variante, 'N_sugerido': n,
                  'A_en_N': gA / 1e6, 'B_en_N': gB / 1e6, 'A+B_en_N': (gA + gB) / 1e6,
                  'desvio_A+B': np.sqrt(r['ganancia_desvio'].pow(2).sum()) / 1e6})
eleccion = pd.DataFrame(filas)
eleccion['vs_V0'] = eleccion['A+B_en_N'] - eleccion.groupby('config')['A+B_en_N'].transform('first')
eleccion.style.format({c: '{:,.1f}' for c in ['A_en_N', 'B_en_N', 'A+B_en_N', 'desvio_A+B', 'vs_V0']} | {'N_sugerido': '{:,}'})

#%% celda 18 [texto]
## 9. Cierre

- **Registro:** anotar en `decisiones.md` el experimento #2 (resumen y comparación pareada) y qué variante se adopta para cada configuración.
- **Si hay submit:** en el `03`, fijar `CONFIG`, `VARIANTE` y un `NOMBRE_SUBMIT` nuevo.
- **Lo que sigue:** las variables nuevas (`05`, ficha de la etapa 5) sobre V5 si le gana a V0 con la regla de la ficha, o sobre la línea base si no. Después, el ensamble.
```

### notebook/03_entrega.ipynb

Entrena el modelo final con 202103–202106 y 20 semillas, predice 202108, guarda las probabilidades por semilla y escribe un CSV por semilla y uno de semillerío con los N clientes de mayor probabilidad. Se corre una vez por juego de semillas.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–31] Celdas de texto de presentación. Indican que el notebook se usa para cada submit
#   cambiando parámetros: entrena la configuración elegida con 202103–202106 y 20 semillas, predice 202108,
#   escribe 20 CSV (uno por semilla) y uno de semillerío, verifica el formato y anota el submit. Describen cada
#   parámetro y los controles que atan el nombre del submit a los valores elegidos.
#%% celda 1 [texto]
# 03 · Entrega: modelo final, predicción de `202108` y archivos para el bot

Este notebook se usa **para cada submit**: el primero (línea base) y la entrega final, cambiando solo los parámetros.

1. Entrena la configuración elegida en el `02` con **`202103`–`202106`** y **20 semillas**.
2. Predice **`202108`**.
3. Genera los archivos para el bot `@competencia-uno`:
   - **20 CSV, uno por semilla**, con los N clientes de mayor probabilidad. Se suben juntos: el bot devuelve media y desvío, y eso evita la "maldición del ganador".
   - **1 CSV de semillerío**, con el promedio de las 20 probabilidades. Es el candidato a **entrega definitiva**, que va sola como último submit.
4. Verifica cada CSV con el checklist del CLAUDE.md §8.
5. Anota el submit en `../entregas/registro_submits.md`.

**N y la configuración salen del backtest (`02`, `04` o `05`)**, nunca del leaderboard público.

#%% celda 2 [texto]
## 1. Parámetros

- **`CONFIG`:** la configuración elegida en el `02`, por ejemplo `'z601_bajas'`. La elige el usuario, y se anota en `decisiones.md`.
- **`N_ENVIOS = 'auto'`:** aplica la decisión 5 de la etapa 2, el promedio de los N de la meseta en A y B, redondeado a 500 y acotado a 8.000–15.000. Lo lee del `resumen.csv` de la corrida completa del `02`. También acepta un número fijo.
- **`VARIANTE` (obligatoria):**
  - `'linea_base'`: el modelo del `02`;
  - una variante del `04` (por ejemplo `'V4'`): aplica su limpieza (variables que se sacan y variables que pasan a `NA` en ciertos meses), y N sale del `resumen.csv` del `04`.

  No tiene valor por defecto, para que siempre se elija a propósito.
- **`BLOQUES` (opcional):** una corrida del `05`, por ejemplo `'B2+B3+B4'`. Usa el parquet de variables nuevas y **la lista exacta de variables** que guardó el `05` en `bloques.json`, y N sale del `resumen.csv` del `05`. Exige que `VARIANTE` sea la misma base que usó el `05`. Con `None`, el `03` funciona como antes.
- **Control del nombre:** si `NOMBRE_SUBMIT` menciona una variante (`V1`…`V4`), tiene que ser la misma que `VARIANTE`. Con `'linea_base'`, el nombre no puede mencionar ninguna. Con `BLOQUES`, el nombre tiene que llevar su código: `'B2+B3+B4'` → `B234`, `'B2+B3+B4c+B5'` → `B234c5`; sin `BLOQUES`, no puede llevar ningún código de bloques.
- **`MESES_FINAL`:** los meses de entrenamiento del modelo final. Por defecto, `202103`–`202106`. **Sin marzo** (`[202104, 202105, 202106]`) el nombre tiene que llevar `SinMar`, y al revés.
- **`HIPER_OPTUNA`:** el número de una prueba elegida en el `08` (por ejemplo `42`): usa sus hiperparámetros (`../exp/08_optuna/hiperparametros_p<prueba>.json`) en lugar de los de `CONFIG`. Exige la misma configuración, base y bloques que usó el `08`, y que el nombre lleve `Opt<prueba>`. Con `None`, usa los de `CONFIG` y el nombre no puede llevar `Opt`.
- **`JUEGO_SEMILLAS`:** `1` = las 20 semillas del `02` (por defecto). `2`, `3`, … = 20 primos de 6 dígitos nuevos por juego, sorteados con `default_rng([979201, juego])` sin repetir ninguna de los juegos anteriores. Sirve para sumar semillas a un modelo sin reentrenar las que ya están: después el `07` promedia los juegos. Con un juego distinto de 1, el nombre tiene que llevar `J<juego>`.
- **`NOMBRE_SUBMIT`:** el nombre interno del submit, distinto en cada uno, sin espacios ni caracteres raros. Es también el prefijo de los archivos.

# [Anotación · líneas 33–66] Importa las librerías y define los parámetros con los que está guardado el
#   notebook: CONFIG = 'z470_bajas', VARIANTE = 'V5', N_ENVIOS = 12_000, BLOQUES = 'B2+B3+B4+B5', NOMBRE_SUBMIT
#   = 'fe04z470bajasV5B2345Opt44', HIPER_OPTUNA = 44, JUEGO_SEMILLAS = 1, MESES_FINAL = 202103 a 202106 y
#   MES_FUTURO = 202108. El README indica para la entrega HIPER_OPTUNA = 42 y los nombres
#   'fe03z470bajasV5B2345Opt42' (juego 1) y 'fe03z470bajasV5B2345Opt42J2' (juego 2).
#%% celda 3 [código]
from pathlib import Path
from datetime import datetime
import json
import re
import time
import warnings

import duckdb
import lightgbm as lgb
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore', message='.*ChainedAssignmentError.*')  # falso positivo pandas 2.2 + Py 3.14

# --- Parámetros -------------------------------------------------------------
CONFIG = 'z470_bajas'            # <- la elegida en el 02, por ejemplo 'z601_bajas'
VARIANTE = 'V5'          # <- OBLIGATORIO: 'linea_base' o 'V1'…'V4' (del 04)
N_ENVIOS = 12_000        # 'auto' (decisión 5 de la etapa 2) o un número entre 8.000 y 15.000
BLOQUES = 'B2+B3+B4+B5'           # opcional: una corrida del 05, por ejemplo 'B2+B3+B4' (VARIANTE = la BASE del 05)
NOMBRE_SUBMIT = 'fe04z470bajasV5B2345Opt44'     # <- por ejemplo 'lb01z601bajas' (único, sin espacios)
HIPER_OPTUNA = 44       # None: los de CONFIG · un número: la prueba del 08 (el nombre lleva 'Opt<prueba>')
JUEGO_SEMILLAS = 1       # 1: las 20 del 02 · 2, 3…: 20 semillas nuevas por juego (el nombre lleva 'J<juego>')

BASE_PARQUET = Path('../data/competencia_01_base.parquet')
EXP02 = Path('../exp/02_linea_base')
EXP04 = Path('../exp/04_drift')
EXP05 = Path('../exp/05_variables')
EXP08 = Path('../exp/08_optuna')
ENTREGAS = Path('../entregas')

MESES_FINAL = [202103, 202104, 202105, 202106]   # marzo se queda (decidido el 2026-10-06); sin marzo: [202104, 202105, 202106] + 'SinMar'
MES_FUTURO = 202108
# -----------------------------------------------------------------------------

# [Anotación · líneas 68–127] Validaciones con assert antes de entrenar: existen el parquet base y las salidas
#   del 02; el nombre sólo tiene letras, números y guion bajo; el nombre menciona la variante, el código de
#   bloques, 'SinMar' si no se entrena con 202103, 'J<n>' si el juego de semillas no es 1 y 'Opt<n>' si se usan
#   hiperparámetros del 08; la base y la configuración de bloques.json y del JSON de hiperparámetros coinciden
#   con CONFIG, VARIANTE y BLOQUES. Crea las carpetas de salida y no admite un nombre que ya tenga CSV.
assert BASE_PARQUET.exists(), 'Falta el dataset base: correr 01_pipeline_base'
assert (EXP02 / 'configuraciones.json').exists() and (EXP02 / 'semillas.json').exists(), \
    'Falta la salida del 02: correrlo antes'
assert isinstance(NOMBRE_SUBMIT, str) and re.fullmatch(r'[A-Za-z0-9_]+', NOMBRE_SUBMIT), \
    'NOMBRE_SUBMIT: solo letras, números y guion bajo'

# VARIANTE se elige siempre a propósito (2026-10-05: un submit salió con la línea base por dejarla vacía)
variantes_04 = json.loads((EXP04 / 'variantes.json').read_text()) if (EXP04 / 'variantes.json').exists() else {}
assert VARIANTE == 'linea_base' or VARIANTE in variantes_04, \
    f"VARIANTE tiene que ser 'linea_base' o una de {sorted(variantes_04)}"
mencionadas = set(re.findall(r'V\d+', NOMBRE_SUBMIT))
if VARIANTE == 'linea_base':
    assert not mencionadas, f'El nombre menciona {mencionadas} pero VARIANTE es la línea base'
else:
    assert mencionadas == {VARIANTE}, f'El nombre tiene que mencionar {VARIANTE} (menciona {mencionadas or "ninguna"})'
# BLOQUES: una corrida del 05, con la misma base y la misma configuración
codigos = set(re.findall(r'B[0-9c]+', NOMBRE_SUBMIT))
if BLOQUES is None:
    bloques_05 = None
    assert not codigos, f'El nombre menciona bloques {codigos} pero BLOQUES es None'
else:
    assert (EXP05 / 'bloques.json').exists(), 'Falta la salida del 05'
    bloques_05 = json.loads((EXP05 / 'bloques.json').read_text())
    assert BLOQUES in bloques_05['variables'] and BLOQUES != 'base', \
        f"BLOQUES tiene que ser una de {sorted(set(bloques_05['variables']) - {'base'})}"
    assert bloques_05['base'] == VARIANTE and bloques_05['config'] == CONFIG, \
        f"El 05 corrió con base {bloques_05['base']} y {bloques_05['config']}: VARIANTE y CONFIG tienen que coincidir"
    codigo = 'B' + ''.join(re.findall(r'\d+c?', BLOQUES))     # 'B2+B3+B4c+B5' → 'B234c5'
    assert codigos == {codigo}, f'El nombre tiene que llevar {codigo} (lleva {codigos or "ninguno"})'
# MESES_FINAL: sin marzo, el nombre lo tiene que decir
assert set(MESES_FINAL) <= {202103, 202104, 202105, 202106}, 'Solo meses con clase completa'
assert (202103 not in MESES_FINAL) == ('SinMar' in NOMBRE_SUBMIT), \
    "Sin marzo, el nombre lleva 'SinMar' (y con marzo, no)"
# JUEGO_SEMILLAS: con un juego distinto de 1, el nombre lo tiene que decir
assert isinstance(JUEGO_SEMILLAS, int) and JUEGO_SEMILLAS >= 1
assert (JUEGO_SEMILLAS != 1) == bool(re.search(r'J\d+', NOMBRE_SUBMIT)) and \
    (JUEGO_SEMILLAS == 1 or f'J{JUEGO_SEMILLAS}' in NOMBRE_SUBMIT), f"Con JUEGO_SEMILLAS = {JUEGO_SEMILLAS}, el nombre lleva 'J{JUEGO_SEMILLAS}' (con 1, ninguno)"
# HIPER_OPTUNA: los hiperparámetros del 08, con la misma configuración, base y bloques
assert HIPER_OPTUNA is None or (isinstance(HIPER_OPTUNA, int) and not isinstance(HIPER_OPTUNA, bool)), \
    'HIPER_OPTUNA: None o el número de prueba del 08 (por ejemplo 42)'
if HIPER_OPTUNA is not None:
    archivo_h = EXP08 / f'hiperparametros_p{HIPER_OPTUNA}.json'
    assert archivo_h.exists(), f'Falta {archivo_h.name}: en el 08, ELEGIDA = {HIPER_OPTUNA}'
    hiper_08 = json.loads(archivo_h.read_text())
    assert hiper_08['prueba'] == HIPER_OPTUNA
    assert (hiper_08['config'], hiper_08['base'], hiper_08['bloques']) == (CONFIG, VARIANTE, BLOQUES), \
        f"El 08 usó {hiper_08['config']} · {hiper_08['base']} · {hiper_08['bloques']}: CONFIG, VARIANTE y BLOQUES tienen que coincidir"
    assert f"Opt{hiper_08['prueba']}" in NOMBRE_SUBMIT, f"El nombre tiene que llevar Opt{hiper_08['prueba']}"
else:
    hiper_08 = None
    assert 'Opt' not in NOMBRE_SUBMIT, "El nombre lleva 'Opt' pero HIPER_OPTUNA es None"
print(f'>>> VARIANTE: {VARIANTE} · BLOQUES: {BLOQUES or "—"} · MESES_FINAL: {MESES_FINAL} · '
      f'hiperparámetros: {"Optuna prueba " + str(hiper_08["prueba"]) if hiper_08 else CONFIG} · NOMBRE_SUBMIT: {NOMBRE_SUBMIT}')

SALIDA = ENTREGAS / NOMBRE_SUBMIT
PROBS = Path('../exp/03_entrega') / NOMBRE_SUBMIT   # probabilidades por semilla (para retomar)
assert not SALIDA.exists() or not any(SALIDA.glob('*.csv')), \
    f'Ya hay CSV con el nombre {NOMBRE_SUBMIT}: elegir otro (los nombres no se repiten)'
SALIDA.mkdir(parents=True, exist_ok=True)
PROBS.mkdir(parents=True, exist_ok=True)

# [Anotación · líneas 129–158] Lee configuraciones.json y las 20 semillas del 02. Para un juego de semillas 2
#   o mayor sortea 20 primos de 6 dígitos que no estén entre los ya usados, con
#   numpy.random.default_rng([979201, juego]). Guarda las semillas del juego en la carpeta de probabilidades del
#   submit.
#%% celda 4 [texto]
## 2. Configuración, semillas y N (salen del `02`)

Los hiperparámetros, las clases y las variables excluidas se leen de `configuraciones.json`, y las 20 semillas de `semillas.json`. Por construcción, el modelo final es **el mismo** que se evaluó en el backtest.

#%% celda 5 [código]
config = json.loads((EXP02 / 'configuraciones.json').read_text())
SEMILLAS = json.loads((EXP02 / 'semillas.json').read_text())['semillas']
assert len(SEMILLAS) == 20


def primos_6_digitos():          # la misma criba del 02
    criba = np.ones(1_000_000, dtype=bool)
    criba[:2] = False
    for i in range(2, 1_001):
        if criba[i]:
            criba[i * i::i] = False
    return np.flatnonzero(criba[100_000:]) + 100_000


usadas = list(SEMILLAS)
for juego in range(2, JUEGO_SEMILLAS + 1):       # cada juego: 20 primos nuevos, sin repetir los anteriores
    disponibles = np.setdiff1d(primos_6_digitos(), usadas)
    nuevas = np.random.default_rng([979201, juego]).choice(disponibles, size=20, replace=False).tolist()
    usadas += nuevas
    if juego == JUEGO_SEMILLAS:
        SEMILLAS = nuevas
assert len(SEMILLAS) == 20 and len(set(usadas)) == len(usadas)
print(f'Juego de semillas {JUEGO_SEMILLAS}: {SEMILLAS}')
(PROBS / 'semillas.json').write_text(json.dumps({'juego': JUEGO_SEMILLAS, 'semillas': SEMILLAS}, indent=2))

# [Anotación · líneas 160–193] Separa CONFIG en juego de hiperparámetros y esquema de clase. Los
#   hiperparámetros salen del JSON del 08 si HIPER_OPTUNA tiene un número, o de configuraciones.json si es None.
#   Suma a las variables excluidas las de la variante y toma sus pases a NA por mes. N es el número fijado o,
#   con 'auto', el promedio de los N de meseta de A y B del resumen.csv correspondiente, redondeado a 500 y
#   acotado a 8.000–15.000; verifica que N esté entre 8.000 y 15.000.
assert isinstance(CONFIG, str) and '_' in CONFIG, "CONFIG: por ejemplo 'z601_bajas'"
HIPER, CLASE = CONFIG.split('_', 1)
assert HIPER in config['hiperparametros'] and CLASE in config['clases'], f'Configuración desconocida: {CONFIG}'
PARAMS = dict(hiper_08['params']) if hiper_08 else dict(config['hiperparametros'][HIPER])
POSITIVOS = config['clases'][CLASE]
EXCLUIDAS = list(config['variables_excluidas'])
NA_EN_MES = {}
if VARIANTE != 'linea_base':
    EXCLUIDAS += variantes_04[VARIANTE]['excluir']
    NA_EN_MES = variantes_04[VARIANTE]['na_en_mes']
GANANCIA_ACIERTO, COSTO_ESTIMULO = config['ganancia_acierto'], config['costo_estimulo']

if N_ENVIOS == 'auto':
    if BLOQUES is not None:
        resumen = pd.read_csv(EXP05 / 'resumen.csv')
        fila = resumen[(resumen['config'] == CONFIG) & (resumen['base'] == VARIANTE)
                       & (resumen['nombre'] == BLOQUES)].set_index('prueba')
    elif VARIANTE == 'linea_base':
        resumen = pd.read_csv(EXP02 / 'resumen.csv')   # el de la corrida completa (no el rápido)
        fila = resumen[resumen['config'] == CONFIG].set_index('prueba')
    else:
        resumen = pd.read_csv(EXP04 / 'resumen.csv')
        fila = resumen[(resumen['config'] == CONFIG) & (resumen['variante'] == VARIANTE)].set_index('prueba')
    assert {'A', 'B'} <= set(fila.index), f'No está {CONFIG} en resumen.csv'
    assert (fila['semillas'] >= 10).all(), 'resumen.csv tiene que venir de la corrida completa (10 semillas)'
    N = int(np.clip(round((fila.loc['A', 'N_meseta'] + fila.loc['B', 'N_meseta']) / 2 / 500) * 500, 8_000, 15_000))
    print(f"N de la meseta: A = {fila.loc['A', 'N_meseta']:,} · B = {fila.loc['B', 'N_meseta']:,} → N = {N:,}")
else:
    N = int(N_ENVIOS)
assert 8_000 <= N <= 15_000, 'El bot acepta entre 8.000 y 15.000 registros'

print(f'Configuración: {CONFIG} · variante: {VARIANTE} · bloques: {BLOQUES or "—"} · positivos: {POSITIVOS} · N = {N:,}')
print('Excluidas:', EXCLUIDAS, '· NA por mes:', NA_EN_MES or '—')
print('Hiperparámetros:', PARAMS)

# [Anotación · líneas 195–237] Lee el parquet de variables nuevas (o el base si no hay bloques) y toma la
#   lista exacta de variables de bloques.json. Pasa a NA, en los meses indicados por la variante, la columna y
#   las variables derivadas de ella. Entrenamiento: filas de MESES_FINAL con clase, etiqueta 1 si la clase está
#   entre las positivas. Predicción: filas de 202108. Verifica con assert filas por mes, cantidad de positivos,
#   164.647 clientes en 202108 sin clase e IDs únicos.
#%% celda 6 [texto]
## 3. Datos

- **Entrenamiento:** `202103`–`202106`, solo las filas con clase.
- **Predicción:** `202108`. `202107` no se usa.

Las variables son las mismas del backtest. Con `BLOQUES`, se lee el parquet de variables nuevas (mismo orden de filas que el base) y la lista de variables de `bloques.json`, en el mismo orden. La limpieza de la variante alcanza también a las variables que salen de esa columna, igual que en el `05`.

#%% celda 7 [código]
t0 = time.time()
PARQUET = Path(bloques_05['fe_parquet']) if BLOQUES else BASE_PARQUET
df = duckdb.sql(f"select * from read_parquet('{PARQUET.as_posix()}')").df()
if BLOQUES:
    VARIABLES = bloques_05['variables'][BLOQUES]               # la lista exacta del 05, en su orden
    assert not set(VARIABLES) & set(EXCLUIDAS), 'Hay variables excluidas por la variante'
    fuentes = bloques_05['fuentes']
else:
    VARIABLES = [c for c in df.columns if c not in EXCLUIDAS]
    fuentes = {}
for columna, meses_na in NA_EN_MES.items():          # limpieza de la variante (misma regla que el 04 y el 05)
    afectadas = [c for c in df.columns if c == columna or columna in fuentes.get(c, [])]
    df.loc[df['foto_mes'].isin(meses_na), afectadas] = np.nan
    print(f'{afectadas} → NA en {meses_na}')
print(f'Parquet: {PARQUET.name} · {len(VARIABLES)} variables')

es_train = df['foto_mes'].isin(MESES_FINAL) & df['clase_ternaria'].notna()
es_futuro = df['foto_mes'] == MES_FUTURO
X_train = df.loc[es_train, VARIABLES]
y_train = df.loc[es_train, 'clase_ternaria'].isin(POSITIVOS).astype(int).to_numpy()
X_futuro = df.loc[es_futuro, VARIABLES]
ids_futuro = df.loc[es_futuro, 'numero_de_cliente'].to_numpy()

print(f'Entrenamiento: {len(X_train):,} filas · {y_train.sum():,} positivos · '
      f'futuro {MES_FUTURO}: {len(X_futuro):,} clientes · {time.time() - t0:.0f} s')

# Controles: filas y positivos conocidos
FILAS_MES = {202103: 162_900, 202104: 163_284, 202105: 163_768, 202106: 164_114}        # filas con clase
POSITIVOS_MES = {'baja2': {202103: 960, 202104: 1_139, 202105: 870, 202106: 1_098},
                 'bajas': {202103: 1_979, 202104: 2_103, 202105: 2_013, 202106: 1_972}}
assert len(X_train) == sum(FILAS_MES[m] for m in MESES_FINAL) and len(X_futuro) == 164_647
assert y_train.sum() == sum(POSITIVOS_MES[CLASE][m] for m in MESES_FINAL)
assert df.loc[es_futuro, 'clase_ternaria'].isna().all()
assert ids_futuro.dtype == np.int64 and len(np.unique(ids_futuro)) == len(ids_futuro)

# [Anotación · líneas 239–263] Entrena un LightGBM por semilla con los mismos hiperparámetros (num_boost_round
#   = num_iterations, seed = la semilla) sobre un único Dataset, predice 202108 y guarda las probabilidades en
#   un .npy por semilla; si el archivo existe, saltea esa semilla. Al final apila las 20 predicciones en una
#   matriz de 20 × 164.647.
#%% celda 8 [texto]
## 4. Modelo final con 20 semillas

Cada semilla entrena un modelo con **los mismos hiperparámetros** y predice `202108`. Las probabilidades se guardan apenas termina cada una, así que si se corta la corrida, retoma desde donde quedó.

**Nota para iterar:** los hiperparámetros se ajustaron con 1 o 2 meses de entrenamiento y acá se entrena con 4. `min_data_in_leaf` y la cantidad de árboles podrían necesitar un ajuste. Es un tema para una iteración (CLAUDE.md §4, el reescalado de `z494`), no para la línea base.

#%% celda 9 [código]
rondas = PARAMS['num_iterations']
params_lgb = {k: v for k, v in PARAMS.items() if k != 'num_iterations'}  # se puede re-ejecutar la celda
dtrain = lgb.Dataset(X_train, label=y_train, free_raw_data=False)

t_total = time.time()
for k, semilla in enumerate(SEMILLAS, 1):
    archivo = PROBS / f'prob_s{semilla}.npy'
    if archivo.exists():
        continue
    t0 = time.time()
    modelo = lgb.train({**params_lgb, 'seed': semilla}, dtrain, num_boost_round=rondas)
    np.save(archivo, modelo.predict(X_futuro))
    print(f'[{k}/20] semilla {semilla} · {time.time() - t0:.0f} s')
print(f'Listo en {(time.time() - t_total) / 60:.1f} min')

probs = np.vstack([np.load(PROBS / f'prob_s{s}.npy') for s in SEMILLAS])   # 20 × 164.647
assert probs.shape == (20, len(ids_futuro))

# [Anotación · líneas 265–294] top_n devuelve los N numero_de_cliente de mayor probabilidad (orden estable).
#   Escribe un CSV por semilla con su lista y un CSV de semillerío con los N de mayor promedio de las 20
#   probabilidades; guarda también el vector promedio. Los CSV tienen una columna de enteros sin encabezado.
#%% celda 10 [texto]
## 5. Archivos para el bot

- **Por semilla:** los N clientes con mayor probabilidad de esa semilla.
- **Semillerío:** los N clientes con mayor **promedio** de las 20 probabilidades. Es lo estándar; nada de tomar el máximo (CLAUDE.md §9).

Los CSV tienen una sola columna, sin encabezado, con IDs enteros.

#%% celda 11 [código]
def top_n(prob, n=N):
    orden = np.argsort(-prob, kind='stable')
    return ids_futuro[orden[:n]]


def escribir(ids, ruta):
    pd.Series(ids, dtype='int64').to_csv(ruta, index=False, header=False)


archivos_semillas = []
for semilla, prob in zip(SEMILLAS, probs):
    ruta = SALIDA / f'{NOMBRE_SUBMIT}_s{semilla}.csv'
    escribir(top_n(prob), ruta)
    archivos_semillas.append(ruta)

prob_semillerio = probs.mean(axis=0)
archivo_semillerio = SALIDA / f'{NOMBRE_SUBMIT}_semillerio.csv'
escribir(top_n(prob_semillerio), archivo_semillerio)
np.save(PROBS / 'prob_semillerio.npy', prob_semillerio)

print(f'{len(archivos_semillas)} archivos por semilla + 1 de semillerío en {SALIDA}')

# [Anotación · líneas 296–325] Relee cada CSV como texto y verifica que todas las líneas sean enteros, que
#   haya exactamente N, que no haya duplicados y que todos los IDs sean de 202108. Registra si 48000000 y
#   31100000 aparecen en cada archivo.
#%% celda 12 [texto]
## 6. Checklist de cada CSV (CLAUDE.md §8)

Se relee **cada archivo como texto**, igual que lo va a leer el bot, y se controla:
- que no haya encabezado;
- que cada línea sea un entero, sin notación científica;
- que no haya duplicados;
- que haya exactamente N líneas;
- que todos los IDs sean de `202108`.

Si `48000000` o `31100000` están en la lista, tienen que aparecer escritos así, completos.

#%% celda 13 [código]
ids_validos = set(ids_futuro.tolist())


def verificar_csv(ruta):
    lineas = ruta.read_text().splitlines()
    assert all(re.fullmatch(r'\d+', l) for l in lineas), f'{ruta.name}: hay líneas que no son enteros (¿encabezado o 4.8e+07?)'
    ids = [int(l) for l in lineas]
    assert len(ids) == N, f'{ruta.name}: {len(ids)} líneas, se esperaban {N}'
    assert len(set(ids)) == len(ids), f'{ruta.name}: IDs duplicados'
    assert set(ids) <= ids_validos, f'{ruta.name}: hay IDs que no son de {MES_FUTURO}'
    return {'archivo': ruta.name, 'lineas': len(ids),
            '48000000': '48000000' in lineas, '31100000': '31100000' in lineas}


control = pd.DataFrame([verificar_csv(r) for r in archivos_semillas + [archivo_semillerio]])
print(f'Checklist OK en los {len(control)} archivos')
control.tail(3)

# [Anotación · líneas 327–336] Calcula qué porcentaje de los clientes de la lista de cada semilla está también
#   en la lista del semillerío e imprime la media, el mínimo y el máximo.
#%% celda 14 [texto]
## 7. Estabilidad entre semillas

Qué tanto coinciden las listas de las 20 semillas con la del semillerío: % de clientes en común. Si coinciden mucho, el resultado no depende de la suerte de una semilla. Es diagnóstico, no un criterio de decisión.

#%% celda 15 [código]
lista_semillerio = set(top_n(prob_semillerio).tolist())
coincidencia = np.array([len(set(top_n(p).tolist()) & lista_semillerio) / N for p in probs])
print(f'Coincidencia con el semillerío: media {100 * coincidencia.mean():.1f} % · '
      f'mín {100 * coincidencia.min():.1f} % · máx {100 * coincidencia.max():.1f} %')

# [Anotación · líneas 338–363] Agrega una fila a ../entregas/registro_submits.md (lo crea con encabezado si no
#   existe) con fecha, nombre del submit, configuración, N, archivos y semillas, y deja para completar a mano
#   las columnas de la respuesta del bot. Imprime el texto del mensaje 'submit <nombre>' y qué archivos
#   adjuntar.
#%% celda 16 [texto]
## 8. Registro del submit

Agrega una fila a `../entregas/registro_submits.md`. **Las columnas de la respuesta del bot** (media y desvío públicos) **las completa el usuario** al recibirla.

**El mensaje al bot** es un mensaje privado a `@competencia-uno`:
- **Cuerpo:** `submit <NOMBRE_SUBMIT>`.
- **Primer submit (evaluación):** los 20 CSV por semilla adjuntos.
- **Entrega definitiva:** solo el CSV del semillerío, y tiene que ser **el último submit**, antes de salir de viaje (CLAUDE.md §1.1).

#%% celda 17 [código]
REGISTRO = ENTREGAS / 'registro_submits.md'
if not REGISTRO.exists():
    REGISTRO.write_text(
        '# Registro de submits\n\n'
        'Cada submit: qué modelo, qué N y qué devolvió el bot. **El que vale es el último antes del cierre.**\n\n'
        '| Fecha | Submit (`submit ...`) | Config | N | Archivos | Semillas | Media pública | Desvío público | Notas |\n'
        '|---|---|---|---|---|---|---|---|---|\n')

with REGISTRO.open('a') as f:
    f.write(f"| {datetime.now():%Y-%m-%d %H:%M} | `{NOMBRE_SUBMIT}` | {CONFIG} · {VARIANTE}{' · ' + BLOQUES if BLOQUES else ''}{' · sin marzo' if 202103 not in MESES_FINAL else ''}{' · Optuna p' + str(hiper_08['prueba']) if hiper_08 else ''}{' · juego ' + str(JUEGO_SEMILLAS) if JUEGO_SEMILLAS != 1 else ''} | {N:,} | "
            f"20 por semilla + semillerío (`{SALIDA.name}/`) | {'979201 → 20 primos' if JUEGO_SEMILLAS == 1 else f'juego {JUEGO_SEMILLAS}: 20 primos nuevos'} | *(completar)* | *(completar)* | |\n")

print(f'Registrado en {REGISTRO}')
print(f'\nMensaje para @competencia-uno:  submit {NOMBRE_SUBMIT}')
print(f'Adjuntar los 20 archivos  {NOMBRE_SUBMIT}_s<semilla>.csv  de {SALIDA}/')
```


## Explicaciones del alumno (texto original)

### README.md

> # DMEyF 2026 · Primera Competencia: predicción de bajas del Paquete Premium
>
> Ezequiel Abregu · Data Mining en Economía y Finanzas (UBA), comisión de los lunes.
>
> Objetivo: elegir a qué clientes estimular en **`202108`** para retener a los que van a ser `BAJA+2`, maximizando la ganancia: +$1.072.500 por cada `BAJA+2` estimulado y −$27.500 por cada estimulado que no lo es.
>
> **Entrega final:** `entrega_final/final01fe03x40N12000/final01fe03x40N12000_locro.csv`, con 12.000 clientes. Es el archivo que se subió al bot de Zulip, como `submit final01fe03x40N12000`. Dio **110,25** en el leaderboard público del bot, que mide ~25 % de agosto.
>
> ---
>
> ## 1. El modelo final, en una tabla
>
> | Pieza | Elección | Dónde se decidió |
> |---|---|---|
> | Datos | `competencia_01_crudo.csv` → clase ternaria con horizonte de 2 meses (lógica de la cátedra) | `01` |
> | Clase | **`BAJA+1` + `BAJA+2` contra `CONTINUA`**. La ganancia siempre se mide solo con `BAJA+2` | `02` |
> | Limpieza por drift (**V5**) | Sin `Master/Visa_fultimo_cierre` (rotas en `202106`) ni `Master/Visa_Finiciomora` (PSI de 3 a 6). `ccajas_depositos` → `NA` en `202105` (todo en cero ese mes). **Los préstamos personales se quedan**: sacarlos ganaba en junio, pero en el público de agosto restó 4,5 | `04` |
> | Variables nuevas | **B2** historia del TP4 (lags, delta, promedio, mínimo, máximo y pendiente de 3 meses de 8 variables) · **B3** señales del análisis de segmentación (empieza a pagar la comisión, historia del sueldo, consumo de tarjeta contra sus meses anteriores…) · **B4** los 73 montos pasados a ranking dentro del mes · **B5** lag 1 y delta 1 de todas las variables. En total, **507 variables** | `05` |
> | Hiperparámetros | LightGBM `gbdt`, **prueba 42 de Optuna**: 36 hojas, `min_data_in_leaf` 1.855, `learning_rate` 0,042, 637 árboles, `feature_fraction` 0,40, `bagging_fraction` 0,93 con `bagging_freq` 1 | `08` |
> | Entrenamiento final | `202103`–`202106` (654.066 filas). `202107` no se usa: no tiene `BAJA+2` | `03` |
> | Ensamble | Promedio de las probabilidades de **40 semillas**: dos juegos de 20 primos de 6 dígitos, sacados de la semilla primigenia **979201** | `03` + `07` |
> | Corte | Los **12.000** clientes de mayor probabilidad. N se eligió con el leaderboard público: 11.500–12.500 es la meseta | `07` |
>
> ## 2. Cómo reproducir la entrega final
>
> ### Requisitos
>
> - Python 3.14 con las versiones de `requirements.txt` (`pip install -r requirements.txt`): `duckdb` 1.5.5, `lightgbm` 4.7.0, `optuna` 4.9.0, `pandas` 2.2.2, `numpy` 2.4.3, `scipy` 1.17.1, `scikit-learn` 1.8.0, `matplotlib` 3.10.8, `jupyter`.
> - **El dataset original** `competencia_01_crudo.csv` en `../dataset/` relativo a la raíz de este repo. Si está en otro lugar, se cambia `CRUDO` en la celda de parámetros del `01`: es la única ruta externa.
> - ~16 GB de RAM: el dataset con las variables nuevas ocupa ~2,5 GB en memoria.
>
> ### Camino corto: solo lo que entra en el archivo final (~1 hora)
>
> Los notebooks están en `notebook/`. Se corren **en este orden y enteros**. En cada paso figura el bloque completo de parámetros; lo que no está en el bloque queda como viene.
>
> 1. **`01_pipeline_base`**, sin cambios. Crea `data/competencia_01_base.parquet` y controla las filas, la clase y los IDs (~1 min).
> 2. **`02_linea_base`** con `MODO_RAPIDO = True`. Escribe las semillas (`semillas.json`) y las configuraciones que usan los demás notebooks (~2 min).
> 3. **`04_drift`** con `MODO_RAPIDO = True`. Escribe `variantes.json`, que incluye **V5** (~1 min).
> 4. **`05_variables`**, para armar el parquet de variables nuevas y la lista de variables (`bloques.json`):
>    ```python
>    MODO_RAPIDO = True
>    BASE = 'V5'
>    CONFIG = 'z470_bajas'
>    BLOQUES_A_CORRER = []
>    COMBINACIONES = [['B2', 'B3', 'B4', 'B5']]
>    REFERENCIA = None
>    ```
>    Tarda ~5 min.
> 5. **Los hiperparámetros:** `exp/08_optuna/hiperparametros_p42.json` viene en el repo. Para rehacer la búsqueda, ver el camino completo.
> 6. **`03_entrega`, juego de semillas 1** (~21 min):
>    ```python
>    CONFIG = 'z470_bajas'
>    VARIANTE = 'V5'
>    N_ENVIOS = 12_000
>    BLOQUES = 'B2+B3+B4+B5'
>    NOMBRE_SUBMIT = 'fe03z470bajasV5B2345Opt42'
>    HIPER_OPTUNA = 42
>    JUEGO_SEMILLAS = 1
>    MESES_FINAL = [202103, 202104, 202105, 202106]
>    ```
> 7. **`03_entrega`, juego de semillas 2** (~21 min). Mismo bloque, con dos cambios:
>    ```python
>    NOMBRE_SUBMIT = 'fe03z470bajasV5B2345Opt42J2'
>    JUEGO_SEMILLAS = 2
>    ```
> 8. **`07_ensamble`**, que promedia las 40 semillas y corta en 12.000 (segundos):
>    ```python
>    ORIGENES = ['fe03z470bajasV5B2345Opt42', 'fe03z470bajasV5B2345Opt42J2']
>    N = 12_000
>    NOMBRE = 'final01fe03x40N12000'
>    ENSAMBLES, MODELOS_POR_ENSAMBLE = 20, 20
>    SEMILLA_SORTEO = 979201
>    ```
> 9. **Control:** el archivo generado tiene que ser **idéntico** al entregado.
>    ```bash
>    shasum -a 256 entregas/final01fe03x40N12000/final01fe03x40N12000_locro.csv
>    # 88f49493daa9598f89db702ce72b61f2d64df189301cfeecb6bf6d2f86259954  (entrega_final/final01fe03x40N12000/*.sha256)
>    ```
>
> **Por qué alcanza con el modo rápido en el `02`, el `04` y el `05`:** esos notebooks escriben sus configuraciones (semillas, variantes, lista de variables) sin importar el modo. El modo completo solo agrega los backtests con 10 semillas que sirvieron para decidir. Los controles internos verifican que las semillas, las variables y el orden de las filas coincidan en cada paso.
>
> ### Camino completo: todos los experimentos (~4–5 horas)
>
> 1. **`01`**.
> 2. **`02`, `04` y `05` con `MODO_RAPIDO = False`.** En el `05`: `BASE = 'V5'` y las `COMBINACIONES` que vienen por defecto, más `['B2', 'B3', 'B4', 'B5']`.
> 3. **`08_optuna`** con `MODO_RAPIDO = False`, `N_PRUEBAS = 50` y `ELEGIDA = 42`: 50 pruebas, la validación y `hiperparametros_p42.json`.
> 4. **Los pasos 6 a 9 del camino corto.**
>
> **Aviso:** Optuna usa un sampler con semilla (TPE, 979201), pero LightGBM puede dar diferencias numéricas mínimas entre máquinas, y eso puede cambiar el camino de la búsqueda. Por eso el repo incluye el resultado (`hiperparametros_p42.json`), y el camino corto parte de ahí.
>
> ## 3. Qué hace cada notebook
>
> | Notebook | Qué hace |
> |---|---|
> | `01_pipeline_base` | Crudo → clase ternaria en SQL (DuckDB) → parquet base. Tabla de calidad por mes (nulos y ceros) |
> | `02_linea_base` | Línea base: hiperparámetros de la cátedra (`z601`, `z470`) × las dos clases, backtests A (`202103`–`04` → `202106`) y B (`202103` → `202105`), 10 semillas, ganancia en la meseta suavizada (501) |
> | `03_entrega` | Modelo final con 20 semillas sobre `202103`–`202106`, predicción de `202108`, CSV por semilla y semillerío, checklist del formato del bot y registro del submit |
> | `04_drift` | Variantes de limpieza por drift (V1–V5), comparación pareada con Wilcoxon |
> | `05_variables` | Bloques de variables nuevas (B1–B5) y sus combinaciones, contra la base y contra una referencia; prueba C (`202103`–`05` → `202106`) para la historia |
> | `07_ensamble` | Promedio de las probabilidades de varios submits del `03`, cortado en N, en un solo archivo |
> | `08_optuna` | Optuna en A con el 20 % de los `CONTINUA`, validación con todos los datos y 5 semillas en A y C, contra `z470` |
>
>
> ## 4. Lo que más movió la ganancia (público)
>
> | Paso | Público |
> |---|---:|
> | Línea base (`z470`, las dos bajas, semillerío) | 88,30 |
> | + limpieza V5 + variables B2, B3 y B4 (semillerío, N = 9.500) | 98,01 |
> | N = 12.000 en lugar de 9.500 (mismo modelo, 20 semillas) | 94,86 → 101,54 |
> | + B5 (20 semillas) | 102,99 |
> | + hiperparámetros de Optuna, prueba 42 (20 semillas) | 103,62 |
> | **+ semillerío de la prueba 42 (20 semillas / 40 semillas)** | **110,41 / 110,25** |
>
> Dos lecciones:
> 1. **El público con 20 semillas sirvió como segundo juez.** Rechazó una limpieza que los backtests de junio adoptaban, y mostró que el N de los backtests era corto para agosto.
> 2. **El ensamble rinde más cuanto más varían las semillas.** Con `z470`, el semillerío sumaba +1 a +3. Con la prueba 42 (bagging y `feature_fraction` de 0,40), sumó +6,8.
>
> ## 5. Estructura
>
> ```
> notebook/                              los notebooks 01–05, 07 y 08
> requirements.txt                       las versiones de las librerías
> exp/08_optuna/hiperparametros_p42.json los hiperparámetros del modelo final
> entrega_final/final01fe03x40N12000/    el CSV entregado (el que se subió al bot) y su sha256
> ```
>
> Al correr, los notebooks crean `data/` (los parquets), `exp/` (curvas, probabilidades y configuraciones) y `entregas/` (los CSV de cada corrida y un registro). No se versionan: se regeneran.

