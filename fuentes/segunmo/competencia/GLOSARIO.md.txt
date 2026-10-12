# Glosario de la Primera Competencia

Para poder volver más adelante y entender los términos, números y nombres que aparecen en `LOG.md`, `REPRODUCIR.md`, `COBERTURA.md` y los README de cada experimento. Cada entrada dice qué significa **en este proyecto** y dónde aparece. Los números de experimento (001, 037a…) son las carpetas de `experimentos/`.

**Índice:** [1. El problema](#1-el-problema-y-la-métrica) · [2. Validación](#2-validación-folds-y-comparaciones) · [3. Estadística de las comparaciones](#3-estadística-de-las-comparaciones) · [4. Modelos y conjuntos de columnas](#4-modelos-y-conjuntos-de-columnas-m0-m1-m2) · [5. Features](#5-features-variables-construidas) · [6. Entrenamiento e hiperparámetros](#6-entrenamiento-e-hiperparámetros) · [7. Ensembles y mezcla](#7-ensembles-y-mezclas) · [8. Drift y calidad de datos](#8-drift-y-calidad-de-datos) · [9. Leaderboard y entrega](#9-leaderboard-y-entrega) · [10. Sesgos y vicios metodológicos](#10-sesgos-y-vicios-metodológicos-que-hay-que-reconocer) · [11. Cómo leer una tabla y los nombres](#11-cómo-leer-una-tabla-de-resultados-y-los-nombres)

---

## 1. El problema y la métrica

| Término | Qué es |
|---|---|
| **Paquete Premium, cliente-mes** | Cada fila del dataset es un cliente en un mes (`numero_de_cliente`, `foto_mes` = AAAAMM). Solo titulares de Paquete Premium. Meses disponibles: 202103 a 202108 |
| **`clase_ternaria`** | Etiqueta que se construye mirando el futuro del cliente: **CONTINUA** (reaparece dentro de 2 meses), **BAJA+1** (no está el mes siguiente), **BAJA+2** (está el mes siguiente pero no a los dos meses). Los dos últimos meses no tienen etiqueta completa: 202107 solo tiene BAJA+1 conocido; 202108 no tiene ninguna |
| **BAJA+2 = positivo** | Es lo que se predice: al cliente que dentro de dos meses ya no está se lo puede alcanzar a tiempo con un estímulo. BAJA+1 ya se fue (tarde para retenerlo) |
| **Prevalencia** | Proporción de positivos: ≈ 0,6% (≈ 1.000 BAJA+2 por mes sobre ≈ 164.000 clientes) |
| **Función de ganancia** | Enviar estímulo a un BAJA+2 gana **+1.072.500**; enviarlo a cualquier otro cuesta **−27.500**; no enviar es 0. La ganancia de un envío = 1.072.500 × aciertos − 27.500 × errores |
| **Punto de equilibrio (p\*)** | Probabilidad a partir de la cual conviene enviar: 27.500 / (1.072.500 + 27.500) = **0,025** (2,5%). Un cliente con P(BAJA+2) ≥ 2,5% tiene ganancia esperada positiva |
| **k, corte por cantidad** | En vez de cortar por probabilidad, se envían los **k clientes con mayor score**. El bot exige 8.000 ≤ k ≤ 15.000. En este trabajo el final usa k = 12.000. Se prefiere porque las probabilidades de LightGBM no están calibradas (005c) |
| **Ganancia acumulada** | Ganancia si se envía a los primeros 1, 2, …, k clientes ordenados por score. El máximo ex post es el "óptimo" de un mes (depende del mes: ≈ 9–11 veces los positivos, 015) |
| **`gan_media_k` / "ganancia media sobre k"** | Promedio de la ganancia acumulada en k = 8.000, 9.000, …, 15.000. Es la métrica de casi todos los experimentos: no depende de un k puntual. Se reporta en **millones de ARS** (M) de un mes completo |
| **AUC** | Probabilidad de que un positivo reciba más score que un negativo (0,5 = azar). Mide el ranking sin importar el corte; sube poco (0,89–0,90) aunque la ganancia cambie decenas de M |
| **Positivos esperados** | Estimación del número de BAJA+2 en 202108 a partir de la suma de probabilidades del modelo (razón ≈ 3,7 entre suma de P2 y positivos reales, 018): ≈ 1.150–1.200 |

## 2. Validación: folds y comparaciones

| Término | Qué es |
|---|---|
| **Out-of-time (OOT)** | Entrenar con meses anteriores y validar en un mes posterior. Es lo único honesto para una predicción a futuro; nunca se valida en el mismo mes de entrenamiento |
| **Mes de separación (gap)** | Como la etiqueta de un mes mira 2 meses adelante, entre el último mes de train y el de validación tiene que haber un mes, para que la etiqueta de train no "vea" el valid |
| **Fold** | Una partición concreta (meses de train → mes de valid). Los usados: **A** (train 202103 → valid 202105); **B** (202103+04 → 202106, el del baseline); **Bh** (202104 → 202106: la "h" es de *historia*: solo filas con lags reales); **L** (202105 → 202106: el único train con lag2 real); **B2** (202104+05 → 202106) |
| **Solapamiento de targets** | En L y B2 la etiqueta del mes de train 202105 mira 202106–07 y la del valid 202106 mira 202107–08: comparten el mes 202107. Puede inflar las ganancias de features que capturan eventos de ese mes. Por eso se prefirió la validación en 202107 |
| **Proxy / tarea proxy (036)** | Validar en 202107 con **BAJA+1** como etiqueta (sí se conoce) en vez de BAJA+2 (no se conoce). Es un mes limpio, sin aguinaldo y sin solapamiento de targets, pero **no es el mismo objetivo** (BAJA+1 ya se fue); sirve para elegir entre variantes de features, no para estimar la ganancia |
| **Semilla pareada** | Para comparar dos variantes se entrenan ambas con las **mismas semillas** y se restan los resultados semilla a semilla. Quita gran parte del ruido de entrenamiento |
| **Escala local vs Public** | La ganancia local es de un **mes completo**; el Public es ≈ **25%** de los clientes. Una diferencia local de +8M equivale a ≈ +2M en el Public. Hay que dividir por ≈ 4 antes de compararlas |
| **Régimen (de datos)** | Cuántos meses de train hay: 1 mes (A, Bh, L), 2 meses (B, B2), 4 meses (el final). Varias conclusiones cambian de signo con el régimen (026, 018) |

## 3. Estadística de las comparaciones

| Término | Qué es |
|---|---|
| **Delta (Δ)** | Diferencia de ganancia entre una variante y su base, en M ARS. Positivo = la variante gana |
| **Error estándar (ee) de la diferencia** | Desvío de las diferencias por semilla dividido por √(n semillas). Mide cuánto "se mueve" el promedio de la diferencia por ruido de entrenamiento. Regla práctica del proyecto: una diferencia se toma en serio si |Δ| > **~2 ee**. Ojo: mide ruido de semillas, **no** la variación entre meses ni entre muestras de clientes |
| **Pares positivos (p. ej. 5/5, 12/15)** | En cuántas de las comparaciones semilla-fold la variante le gana a la base. 5/5 es consistente; 2/6 es ruido |
| **Test t pareado unilateral** | Test sobre las diferencias por semilla (H0: Δ ≤ 0). Da un p-valor: probabilidad de ver un Δ así de grande por azar |
| **Comparaciones múltiples / forking paths** | Cuantas más variantes se prueban sobre los mismos datos, más probable es que alguna salga bien por casualidad. Es el problema central de este trabajo: decenas de pruebas sobre dos meses |
| **FDR y Benjamini–Hochberg (BH)** | *False Discovery Rate*: proporción esperada de "descubrimientos" falsos. BH ordena los p-valores de menor a mayor y acepta el i-ésimo si p(i) ≤ q·i/m (q = 0,10, m = nº de pruebas). Se fijó de antemano para el plan 037 (libro §19) |
| **Umbral de +3M** | Tamaño mínimo que importa: por debajo de eso, no justifica el riesgo de reentrenar el final aunque sea "significativo" |
| **Regla fijada antes de ver el resultado (pre-registro)** | Se escribe en el documento la condición de adopción antes de correr el experimento, para no ajustarla a lo que salga. Ejemplo: 018, 037 |
| **Potencia (de un test)** | Capacidad de detectar un efecto real. El Public del bot tiene poca potencia: ±2–3M de ruido contra efectos de ≈ 1–2M |
| **Control barajado** | Experimento de control: se permutan al azar las columnas nuevas dentro de cada mes (conservan distribución y nulos, pierden el vínculo con el cliente). Si la ganancia sobrevive, era un artefacto; si desaparece, era información (008b, 029) |
| **Winner's curse (maldición del ganador)** | El mejor de varios resultados ruidosos está sesgado hacia arriba. Por eso no se elige el modelo por el Public ni se confía en el "mejor trial" de Optuna sin reevaluarlo con semillas nuevas |

## 4. Modelos y conjuntos de columnas (M0, M1, M2…)

| Término | Qué es |
|---|---|
| **M0** | Conjunto de **178 columnas sin historia**: 152 originales + 26 variables de negocio `n_*`. Es el modelo "del mes" (005, 010) |
| **M1** | **Top 150** columnas por importancia sobre un *pool* de 345 columnas que incluye la historia lag1/delta1/ratio1 de 50 variables, ratios y `n_*`. La selección se hace con las importancias de un modelo entrenado solo con meses de train (004, 005) |
| **M2** | **Todas las variables con lag1, lag2 y diferencias**: 855 columnas (863 menos 8 con PSI > 0,20 porque su lag2 apunta al aguinaldo). Sin selección. Es el modelo principal del final (028–031) |
| **Pool** | Conjunto amplio de columnas candidatas del que se elige (319 → 345 columnas, 004) |
| **MIX6** | Ensemble de 6 modelos: los 3 mejores trials de Optuna de M0 y los 3 de M1, cada uno con sus propios hiperparámetros (005) |
| **top1 / top2 / top3** | Los 3 mejores trials de Optuna (tras reevaluarlos con semillas nuevas). Sus hiperparámetros están en `005_optuna/mejores_trials.json` |
| **Binario** | LightGBM que predice P(BAJA+2) vs resto |
| **Binario "ambas bajas"** | Binario con BAJA+1 **y** BAJA+2 como positivos (026, 034). Lo usan compañeros con Public > 100; con la historia completa pierde frente al multiclase |
| **Multiclase** | LightGBM con 3 clases (CONTINUA / BAJA+1 / BAJA+2): da P0, P1, P2 por cliente. Mayor mejora individual desde Optuna (010, 013) |
| **Score condicional** | `P2 / (1 − P1)` = probabilidad de BAJA+2 *dado que no es BAJA+1*. **Sube** (no baja) el score de quien tiene P1 alto: incorpora la señal "propenso a irse" (018; la explicación original estaba al revés y se corrigió) |
| **P2 + α·P1** | Familia de scores que suma P1 con peso α. Con poco train el α óptimo es alto; con más datos la ventaja se achica (018) |
| **Auxiliar de BAJA+1** | Modelo binario de BAJA+1 entrenado con 202103–**07** (202107 solo aporta BAJA+1, que se conoce). Su P1 reemplaza al P1 del multiclase en el score condicional (014, 017). No está en M2 |
| **Receta del profe (REC)** | Hiperparámetros pedidos por la cátedra: `max_bin` 31, `min_data_in_leaf` 0, `feature_fraction` 0,5, `feature_fraction_bynode` 0,2, `learning_rate` 0,005, **sin undersampling**. En el final: multiclase con 512 hojas y 800 rondas (009, 021, 024) |
| **E1 / E2** | En 030: ensemble de 3 configuraciones con el pool anterior (E1) o con las 855 columnas (E2) |
| **V0, V1, V2…** | Nombres de variantes **locales de cada experimento** (V0 suele ser la base). No significan lo mismo entre experimentos: mirar el README |

## 5. Features (variables construidas)

| Término | Qué es |
|---|---|
| **Variable original / cruda** | Columna tal como viene del banco (152 numéricas) |
| **Lag (`v_lag1`, `v_lag2`)** | Valor de la misma variable para el mismo cliente 1 o 2 meses antes. NaN si el cliente no estaba |
| **Delta (`v_d1`, `v_d2`)** | `v − lag`: cuánto cambió respecto de 1 o 2 meses atrás |
| **Ratio (`v_r1`, `v_r2`)** | `v / lag − 1`: cambio relativo (normaliza por el tamaño del cliente) |
| **Historia / variables históricas** | Lags, deltas y ratios. La receta ganadora de los compañeros: lag1, lag2 y diferencias de **todas** las variables (028) |
| **Variables `n_*` (negocio)** | Sumas, restas y ratios por grupos de negocio definidos a priori (ingresos, egresos, patrimonio, productos activos…; 003d). Varias están entre las más importantes |
| **Variables `r_*`** | Ratios entre variables del mismo mes (ticket promedio, uso del límite, etc.; 003c) |
| **Rank del mes** | Reemplazar cada valor por su posición relativa dentro del mes (027): perjudicó, porque el nivel nominal lleva información |
| **Deflactor** | Dividir los montos por un factor de precios del mes para volverlos comparables (037c) |
| **Variables de calendario** | `Master_fultimo_cierre` y `Visa_fultimo_cierre`: valen 1, 2, 5, 0, 3, 6 de 202103 a 202108; identifican el mes. Neutras al sacarlas (036) |
| **`ccajas_depositos`** | Variable "rota" en 202105 (todos ceros). Se pone en NA solo ese mes (008a; flag `CORREGIR_CCAJAS`) |
| **NaN nativo** | LightGBM maneja los nulos solo: un nulo en `Visa_*` significa "no tiene la tarjeta", no se imputa |
| **Canarios** | Columnas de ruido (números al azar) que se agregan al entrenamiento. Una variable real que no supera a los canarios en importancia no aporta (004, 037a) |
| **Importancia (gain)** | Cuánto reduce el error cada variable sumando sus cortes en los árboles |
| **Top150** | Las 150 columnas más importantes de un fold, calculadas **solo con meses de train** (nunca con el de validación) |
| **Hojas de Random Forest** | Features que indican en qué hoja de un RF cae cada fila; técnica de la cátedra aún no probada (037f) |
| **Fuga (leakage)** | Que el modelo "vea" información que en producción no tendría (un mes futuro, la etiqueta del valid). Hay que cuidarla en historia, selección de variables y solapamiento |

## 6. Entrenamiento e hiperparámetros

| Término | Qué es |
|---|---|
| **LightGBM** | Gradient boosting de árboles de decisión. Es el único algoritmo usado |
| **Ronda / `num_boost_round`** | Cantidad de árboles. Con `learning_rate` bajo hacen falta más |
| **`learning_rate` (lr)** | Cuánto aporta cada árbol. Menor = más rondas y más regular |
| **`num_leaves`** | Hojas máximas por árbol (complejidad) |
| **`min_data_in_leaf`** | Filas mínimas por hoja: regulariza. Con muchas columnas ruidosas, valores 50–80 ayudaron en L/B2 pero fueron neutros en 202107 (032, 033, 036) |
| **`feature_fraction` / `bynode`** | Fracción de columnas sorteada por árbol / por nodo |
| **`bagging_fraction`** | Fracción de filas sorteada por ronda |
| **`lambda_l1`, `lambda_l2`** | Regularización de los pesos de las hojas |
| **`max_bin`** | Cantidad de intervalos con que se discretiza cada variable |
| **`min_sum_hessian_in_leaf`** | Peso mínimo (suma de hessianos) por hoja: otro regularizador |
| **`extra_trees`, `path_smooth`, `min_gain_to_split`** | Opciones de LightGBM probadas en 022 (perjudicaron o fueron neutras) |
| **Undersampling (r)** | Entrenar con todos los positivos y solo una fracción **r** de los negativos (CONTINUA). Acelera ~5–10× y en nuestras pruebas mejoró la ganancia; infla las probabilidades. En el multiclase se conservan BAJA+1 y BAJA+2 completos |
| **Optuna** | Biblioteca de optimización bayesiana (algoritmo TPE) de hiperparámetros. Cada **trial** prueba una combinación |
| **Trial / ancla** | Un intento de Optuna / trials iniciales con hiperparámetros conocidos para chequear el script (012) |
| **Pruner** | Corta los trials malos antes de terminar |
| **Reevaluación honesta** | Volver a medir los mejores trials con semillas **distintas** a las de la búsqueda y en un fold que no se usó para buscar (005) |
| **Borde de la grilla / de rango** | Cuando el mejor valor está en el extremo de lo probado, no se vio el óptimo (009, 021) |
| **Meseta (plateau)** | Zona donde la métrica casi no cambia: señal de que se llegó al techo de ese espacio (012, 015, 033) |
| **Búsqueda dirigida** | Variar a mano un hiperparámetro por vez en vez de un Optuna completo (032/033) |
| **Semilla** | Número que fija el azar de un entrenamiento. Propias: 852583, 771227, 676057, 482687, 399221 (las demás se derivan) |

## 7. Ensembles y mezclas

| Término | Qué es |
|---|---|
| **Ensemble** | Promedio de varios modelos |
| **Semillero** | Mismo modelo entrenado con muchas semillas y promediado: baja la varianza (004b, 017: 30 semillas por configuración) |
| **Rank medio** | En vez de promediar probabilidades, se convierte cada score en su posición (rank) y se promedian los ranks. Igual o algo mejor (009b, 013) |
| **Blend** | Mezcla de rankings de modelos ya entrenados, sin reentrenar. 019 = 017 + 010; 024 = 019 + receta; 031 = 2/3 M2 + 1/3 de 024 |
| **Diversidad** | Que los modelos se equivoquen distinto: por eso aporta mezclar configuraciones, targets o columnas distintas |
| **Stacking** | Entrenar un meta-modelo sobre las salidas de otros. No se hizo (riesgo de sobreajuste con dos meses) |
| **Solapamiento (top-k)** | % de clientes que dos envíos tienen en común. 95–99% = casi el mismo envío; una diferencia del Public entre ellos es ruido |

## 8. Drift y calidad de datos

| Término | Qué es |
|---|---|
| **Drift** | Que los datos del mes a predecir difieran de los de entrenamiento |
| **Covariate drift / concept drift** | Cambia la distribución de las variables / cambia la **relación** entre variables y target. El segundo es el que el PSI no ve (caso `mprestamos_personales` en 202106) |
| **PSI** | *Population Stability Index*: compara la proporción de población por bin entre dos períodos: Σ (a − e)·ln(a/e). < 0,1 estable; 0,1–0,25 moderado; > 0,25 importante |
| **Validación adversarial (C1, 008)** | Entrenar un clasificador que distinga el mes A del mes B sin usar el target. AUC ≈ 0,5 = sin drift; entre meses consecutivos ya da 0,83–0,92 por los montos nominales |
| **Aguinaldo** | Medio aguinaldo que se paga en junio: infla sueldos y saldos en 202106. Hace atípico ese mes (el fold B y el aumento de payroll) |
| **Ola de salidas (préstamo y mora)** | Aumento de las bajas de clientes con préstamo personal y saldo negativo o tarjeta en *status 6*: 0,28% → 1,3% mensual hasta 202108 (REPRODUCIR §9). Probablemente cierres por mora |
| **Status 6** | Valor de `Visa_status`/`Master_status` que pasó de ≈ 100 clientes por mes a 1.429 en 202107 |
| **Inflación / montos nominales** | Los montos en ARS suben mes a mes; un corte aprendido en marzo no significa lo mismo en agosto |

## 9. Leaderboard y entrega

| Término | Qué es |
|---|---|
| **Public Leaderboard** | Ganancia de un envío sobre ≈ 25% de los clientes de 202108 (muestra fija), sin escalar, en millones. El bot devuelve media y desvío entre los archivos del submit |
| **Private** | Ganancia sobre el resto (≈ 75%): lo que cuenta para la nota. Empíricamente ≈ **3 × Public** (ratio medio 2,98) |
| **Línea de Muerte** | Ganancia mínima para obtener un 5; por encima se normaliza a [5, 10]. Aproximadamente 100M de Public (≈ 300 en Private) según el alumno |
| **Submit / archivo** | Mensaje al bot con 1–20 CSV de `numero_de_cliente` a estimular (8.000–15.000 filas, sin encabezado). El **último submit antes del cierre es el final y debe ser un solo archivo** |
| **Sobreajuste al Public** | Elegir modelos por el Public: sube artificialmente. Por eso solo se usó para detectar roturas, con reglas fijadas antes |

## 10. Sesgos y vicios metodológicos que hay que reconocer

| Término | Qué es |
|---|---|
| **Sesgo de la versión débil** | Probar una idea en una forma limitada (binario, pocos datos, pocas variables) y darla por muerta. Pasó con 008c, 009, 003c (agregar vs reemplazar) |
| **Anclaje / path dependence** | Que decisiones tempranas condicionen todo lo posterior (el top150 sobre un pool de 50 variables) |
| **Sobreajuste a los folds** | Que las decisiones se ajusten a los dos meses de validación |
| **Confusión de factores** | Cambiar dos cosas a la vez (p. ej. k y modelo) y atribuir el efecto a una |
| **Sesgo de selección** | Elegir el mejor de muchos intentos y reportar ese número (ver winner's curse) |

## 11. Cómo leer una tabla de resultados y los nombres

**Una fila típica** (`LOG.md`, `comparacion.csv`): `V2 − V1: +11.7 (ee 2.1), 5/5`
→ la variante V2 gana a V1 por **11,7M** (de ganancia media en un mes completo), el promedio de las diferencias por semilla tiene un error estándar de 2,1M (es decir ≈ 5,6 ee: bien por encima de 2), y gana en las **5 de 5** semillas. Eso se toma en serio. En cambio `−0.4 (1.7), 1/5` es "no hay efecto".

**Nombres de envíos y archivos**
- `exp017_final_s30_k11000_lag2.csv`: experimento 017, 30 semillas, k = 11.000, con lag2.
- `exp031_final_w67_md_k12000.csv`: experimento 031, peso 67% de M2, con los `min_data` ajustados (md), k = 12.000. **Es el submit final.**
- `exp025_k12000_s399221.csv`: medición de la curva de k (025): k = 12.000, semilla 399221.
- Carpeta `tmp/` de cada experimento: scores por cliente y modelos por semilla (no versionada).

**Documentos**
- `LOG.md`: bitácora, una fila por experimento (más reciente arriba).
- `submissions/REGISTRO.md`: cada envío al bot con su Public.
- `REPRODUCIR.md`: cómo regenerar el final y la evidencia de cada decisión.
- `COBERTURA.md`: auditoría de lo que proponían las fuentes y plan de lo que falta.
- `PLAN.md`: el plan original y su estado final.

## 12. Reproducibilidad
| Término | Qué es |
|---|---|
| **Determinismo** | Que el mismo código, los mismos datos y las mismas semillas den **siempre** el mismo resultado. Se rompe con orden de filas variable, hilos y versiones de librerías |
| **Orden de filas** | Posición de cada cliente en el DataFrame. Importa porque el undersampling sortea por posición (`rand(n) < r`): otro orden = otra muestra de clientes = otro modelo |
| **`ORDER BY` explícito** | Fija el orden de salida de DuckDB (sin él, un join paralelo devuelve filas en orden distinto entre corridas). Se agregó el 2026-10-10 (REPRODUCIR §0) |
| **Huella (hash)** | Resumen corto (md5) de un arreglo para comparar si dos corridas produjeron exactamente lo mismo (`verificar_determinismo.py`) |
| **`deterministic` / `force_row_wise`** | Opciones de LightGBM que fijan el resultado con cualquier cantidad de hilos |
| **Semillas derivadas** | Las 25 semillas generadas a partir de la primera propia (`config.SEMILLAS_DERIVADAS`): reproducibles, pero no registradas en el check-in |
| **`requirements-lock.txt`** | Versiones exactas de las librerías con las que se generó el final |
| **Manifiesto de modelos** | `competencia/modelos_manifiesto.csv`: huellas SHA-256 de cada modelo y su predicción. Es lo versionable (los modelos pesan decenas de MB cada uno y viven en `artifacts/`, fuera de git) |
