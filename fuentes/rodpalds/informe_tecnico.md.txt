# Informe técnico — Primera Competencia DMEyF 2026

**Autor:** Rodrigo Palpa (desarrollado con asistencia de IA: Claude).
**Fecha:** 11/10/2026.
**Propósito:** documentar el proceso, las decisiones y los resultados de la entrega final (modelo 5015), cómo se
evaluaron las recomendaciones del profesor y qué supuestos y desvíos quedan declarados.

---

## 0. Resumen

| Ítem | Valor |
|---|---|
| Submit final | `submit 5015e12500final2`, ID `1626-1791760490758459`, 11/10/2026 20:14 |
| Archivo | `entrega_final/Z6011_5015_e12500_final.csv` (12.500 `numero_de_cliente`, sin encabezado) |
| Ganancia pública | **95,59** (el público es ≈25% de los clientes de agosto) |
| Modelo | LightGBM binario, semillerío de 50 semillas |
| Clase de entrenamiento | `clase_binaria2`: BAJA+1 y BAJA+2 positivos. La ganancia se mide siempre sobre BAJA+2 |
| Dataset | `ds3003_rank_extra.parquet`: lags y deltas de orden 1 y 2 sobre valores crudos, después ranking por mes con cero fijo (NA se mantiene), más 6 variables del "proceso de muerte". **766 variables** |
| Meses de entrenamiento | 202103 a 202106. Se predice 202108 |
| Hiperparámetros | "Prueba 23" (encontrada en la Bayesiana 4104 y mantenida por las Bayesianas 4105, 4106 y 4107) |
| Corte | 12.500 envíos |
| Validación interna | Junio completo, prueba 23 entrenada con marzo + abril: 441,4 M de meseta (semillerío de 20, exp 5114) |

---

## 1. Problema y datos

- **Dataset:** `competencia_01`, de 202103 a 202108: 983.061 filas y 152 variables originales, más el id y el mes.
- **Clase ternaria** con la lógica de la cátedra (CONTINUA, BAJA+1, BAJA+2), en `01_preparar_dataset.py` (exp 1001).
- **Meses con clase completa:** 202103 a 202106. 202107 tiene la clase incompleta y no se usa para entrenar.
  202108 es el mes a predecir.
- **Ganancia:** +1.072.500 por cada BAJA+2 contactado y −27.500 por cada otro contacto.
- **Entrega:** bot de Zulip `@competencia-uno`, entre 8.000 y 15.000 ids. Vale el último submit antes del cierre
  (11/10/2026 23:59).

---

## 2. Recomendaciones del profesor y cómo se evaluaron

Cada recomendación se evaluó con el mismo protocolo (sección 4) contra el modelo vigente, con una regla fijada
antes de ver el resultado. Se adoptaron las que mejoraron o empataron.

| Recomendación | Evaluación | Resultado | Decisión |
|---|---|---|---|
| Lags y deltas de orden 1 y 2, aunque las columnas tengan muchos NA | 5105 (receta contra dataset anterior), 5106 (con y sin lag2) | Mejora; lag2 empata (−1,5 M, IC90 −13 a +11) | **Adoptada** |
| Ranking de todas las variables dentro de cada mes, con cero fijo y NA conservado (después de los lags) | 5105 (ds3002 y ds3003 contra variantes) | Mejor que rankear antes de los lags (3005) y que indicadores sin rankear (3004) | **Adoptada** |
| Sin canaritos, sin undersampling | — | — | **Adoptada** |
| Usar toda la información disponible para la búsqueda de hiperparámetros, aunque haya NA | 5107: marzo + abril contra solo abril | +4,8 M (IC90 −7,1 a +16,4; 75% de los remuestreos) | **Adoptada** |
| Entrenamiento final con todos los meses con clase (marzo a junio) | — | — | **Adoptada** |
| Rangos de búsqueda: `num_leaves` 8–2000, `min_data_in_leaf` 0–20.000, `feature_fraction` 0,05–0,9, `bagging_fraction` 0,05–1, `learning_rate` 0,01–0,2; `max_bin` 31 | Bayesiana 4107 (50 pruebas) | Ninguna prueba nueva superó a la prueba 23 en la mitad B (sección 3.3) | **Adoptada**; se mantuvo la prueba 23 |
| ≥20 semillas en el modelo final | — | 50 semillas | **Adoptada** |
| Estrategia de entrenamiento 1.7: métrica AUC; fijos `max_bin` 31, `min_data_in_leaf` 0, `feature_fraction` 0,5, `feature_fraction_bynode` 0,2, `learning_rate` 0,005; Bayesiana sobre `num_iterations`, `num_leaves` y `min_sum_hessian_in_leaf`; final como ensamble de 10+ modelos con hiperparámetros distintos (2.1 y 2.2) | 4112 + 5113 (sección 6.1) | **−52 M** en junio contra la prueba 23 | No adoptada (R7) |
| Feature engineering 1.1–1.4: `ccajas_depositos` NA en 202105, flags `_zero`, tendencia y promedio de 3 meses | 5114 (sección 6.2) | **−3,7 M** en junio, mejor en 4/20 semillas | No adoptada (R8) |
| Probar distintos cortes contra el público (2.3) | Sección 5.2 | 12.000 → 96,11; 12.500 → 95,59 | Se combinó con la evidencia de junio |

---

## 3. Pipeline de 5015, paso a paso

### 3.1 Preparación (exp 1001)
`competencia_01_crudo.csv` → `ds1001_base.parquet` con `clase_ternaria`, `clase_binaria1` y `clase_binaria2`.
El script verifica que el archivo grabado sea idéntico al de memoria.

### 3.2 Ingeniería de variables (exp 3003, `03c_fe_extra.py`)
1. Datos ordenados por cliente y mes.
2. Para cada una de las 152 variables: `x_lag1`, `x_lag2` (valor 1 y 2 meses antes; NA si el cliente no estaba
   exactamente k meses antes) y `x_delta1`, `x_delta2` (diferencia contra esos valores), sobre valores crudos.
3. Seis variables del "proceso de muerte", sobre valores crudos:

   | Variable | Qué mide |
   |---|---|
   | `n_apagados` | Cuántas de 16 variables clave (tarjetas, préstamos, sueldo, saldos, transacciones) están en 0 o NA |
   | `n_apagados_delta1` / `n_apagados_delta2` | Diferencia de `n_apagados` contra 1 y 2 meses antes |
   | `n_dejo_de_usar` | Productos activos hace 1 o 2 meses que hoy están en 0 o NA |
   | `ctrx_quarter_rel_max3` / `mcaja_ahorro_rel_max3` | Valor de hoy dividido por el máximo de los últimos 3 meses |

4. **Todas** las columnas (originales, lags, deltas y nuevas) se reemplazan por su ranking dentro del mes:
   positivos en (0,1], negativos en [−1,0), cero = 0, NA = NA, empates por promedio. Corrige la inflación y el
   aguinaldo: la mediana cruda de `mpayroll` entre los positivos sube de ~105 mil (mayo) a ~157 mil (junio);
   rankeada queda en 0,500 todos los meses.
5. Resultado: 983.061 × 771 columnas (5 de id y clase + 152 × 5 + 6).

### 3.3 Selección de hiperparámetros (`08_bo_fuera_de_tiempo.py`)

- Se entrena con meses anteriores y se mide en **junio (202106)**, a la misma distancia de 2 meses que hay entre
  junio y agosto.
- Los clientes de junio se dividen en **dos mitades fijas**, estratificadas por clase ternaria (549 BAJA+2 en cada
  una; `exp/4102_bo_fuera_de_tiempo/4102_mitades_junio.csv`).
- **Etapa 1:** Optuna TPE sobre la **mitad A**, 1 semilla por prueba, corte temprano (hasta 3.000 árboles).
- **Etapa 2:** las 5 mejores de la etapa 1 y las referencias se entrenan con 20 semillas y se miden en la
  **mitad B**. El mejor retador reemplaza a la mejor referencia solo si gana en promedio **y** en ≥14 de 20 semillas.
- **Métrica "meseta":** ganancia promedio entre 12.000 y 17.000 envíos equivalentes al mes completo.

**Bayesiana 4107** (recomendaciones del profesor): ds3003 con lag2; entrenamiento 202103 + 202104; rangos de la
sección 2; `max_bin` 31 y `bagging_freq` 1 fijos; 50 pruebas (15 al azar).

| Candidato | Mitad A | Mitad B | Desvío | Le gana a la p23 en | Árboles | lr | Hojas | min_data | ff | bf |
|---|---|---|---|---|---|---|---|---|---|---|
| **p23 (referencia)** | – | **435,8** | 6,4 | – | 580 | 0,0678 | 41 | 20.248 | 0,180 | 0,312 |
| prueba 48 | 450,5 | 432,1 | 5,7 | 7/20 | 270 | 0,0116 | 754 | 254 | 0,086 | 0,894 |
| prueba 40 | 447,5 | 429,9 | 6,8 | 6/20 | 283 | 0,0169 | 634 | 196 | 0,072 | 0,854 |
| prueba 41 | 447,1 | 425,5 | 6,5 | 2/20 | 607 | 0,0120 | 1555 | 118 | 0,079 | 0,826 |
| prueba 42 (mejor según A) | 453,2 | 418,2 | 12,7 | 3/20 | 428 | 0,0111 | 1621 | 852 | 0,110 | 0,828 |
| prueba 47 | 453,2 | 410,2 | 12,5 | 0/20 | 334 | 0,0104 | 1703 | 1244 | 0,136 | 0,870 |
| z601 (referencia de clase) | – | 357,0 | 8,1 | 0/20 | 250 | 0,0199 | 16 | 1.632 | 0,277 | 0,634 |

Las pruebas con muchas hojas y `min_data_in_leaf` chico ganan en la mitad A y caen en la mitad B. Se mantuvo la prueba 23.

**Historia de la prueba 23:**

| Búsqueda | Entrenamiento | Dataset | Resultado |
|---|---|---|---|
| 4104 | Solo abril | ds3002 con lag2 | Aparece la prueba 23 (3.ª en la mitad A, 1.ª en la B) |
| 4105 | Solo abril | ds3002 sin lag2 | Se mantiene (427,2 M en B) |
| 4106 | Solo abril | ds3003 con lag2 | Se mantiene (432,5 M en B) |
| 4107 | Marzo + abril | ds3003 con lag2 | Se mantiene (435,8 M en B) |

### 3.4 Modelo final 5015 (`07_modelo_final.py`, `configs/5015_prod_profesor_mar_jun.json`)

| Parámetro | Valor |
|---|---|
| Entrenamiento | 202103 a 202106 (654.066 filas, sin undersampling) |
| Predicción | 202108 (164.647 clientes) |
| `learning_rate` / `num_leaves` | 0,0678 / 41 |
| `min_data_in_leaf` | **40.496** (10.124 por mes × 4; supuesto S1) |
| `feature_fraction` / `bagging_fraction` / `bagging_freq` | 0,1798 / 0,3124 / 1 |
| `lambda_l1` / `lambda_l2` / `max_bin` | 0,001 / 0,001 / 31 |
| Árboles | 580, fijos (supuesto S2) |
| Reproducibilidad | `deterministic=True`, `force_row_wise=True` |
| Semillas | 50: 571369, 849571, 355049, 655531, 700103 y 45 primos generados de forma determinística |
| Ensamble | Promedio de las probabilidades de las 50 semillas |

### 3.5 Entrega (exp 6011, `10_entrega_zulip.py`)
Archivos de 11.000 a 13.500 envíos, con controles: sin encabezado, ids enteros, sin repetidos, cantidad exacta.
Se entregó el de 12.500.

---

## 4. Protocolo de validación y reglas de decisión

- Entrenar con 202103 + 202104 y medir en 202106 (mitad B o junio completo), con semillas pareadas.
- Comparaciones con bootstrap pareado (IC90 y % de remuestreos a favor) o Wilcoxon.
- **Reglas fijadas antes de ver cada resultado:**

| Regla | Decisión | Criterio |
|---|---|---|
| R1 | Variables de muerte ampliadas (5108) | Adoptar solo si mejora; dio −7,8 M → no |
| R3 | `min_data_in_leaf` y árboles de la prueba 23 (5109) | Mitad de `min_data_in_leaf` solo si no pierde >3 M; otra cantidad de árboles solo si gana ≥5 M en ≥85% → se mantuvieron 20.248 (2 meses) y 580 |
| R4 | Bayesiana "limpia" 4109 contra la prueba 23 (5110) | Usar 4109 salvo que pierda >3 M; perdió (432,5 vs 443,1) → prueba 23 |
| R6 | Escalar o no `min_sum_hessian_in_leaf` en el ensamble 1.7 | La versión con mayor meseta en junio |
| R7 | Ensamble de la estrategia 1.7 contra la prueba 23 (5113) | Adoptar si no pierde >3 M; perdió 52 M → no |
| R8 | Dataset con el FE 1.1–1.4 (5114) | Adoptar si no pierde >3 M; perdió 3,7 M → no |
| R9 | 5015 sin columnas anómalas (5023) | Cambiar la entrega solo si el público ≥ 100,6; dio 94,35 → no |

---

## 5. Resultados

### 5.1 Historial de submits (público)

| # | Modelo | Envíos | Público |
|---|---|---|---|
| 1 | 5005 (crudo, 123 variables por canaritos, hiperparámetros de 4102) | 13.000 | 92,73 |
| 2–5 | 5005 | 10.000 / 11.000 / 12.000 / 14.000 | 89,38 / 92,57 / 96,58 / 90,26 |
| 6 | Combinación 5005 + 5011 (receta sin lag2) | 12.000 | 94,44 |
| 7 | 5013: ds3003 con lag2, prueba 23, entrenada con abril a junio | 12.000 | 97,08 |
| 8 | 5015: ídem, entrenada con marzo a junio | 12.000 | 96,11 |
| 9 | 5015 | 12.500 | 95,59 |
| 10 | 5023: 5015 sin columnas anómalas | 12.500 | 94,35 |
| 11 | **5015 (reenvío como submit final)** | **12.500** | **95,59** |

Ruido estimado de la diferencia de público entre dos listas con ~95% de coincidencia: ±3 M. Las diferencias
entre los submits 5 a 11 están dentro del ruido.

### 5.2 El corte

| Evidencia | 12.000 | 12.500 | 13.500 | 14.000 |
|---|---|---|---|---|
| Público 5015 | **96,11** | 95,59 | – | – |
| Junio completo, prueba 23, semillerío de 12 (5113) | 443,3 | **449,4** | 449,4 | 446,6 |
| Junio completo, prueba 23, semillerío de 20 (5114) | 442,2 | 443,8 | 442,8 | **452,1** |
| Mitad B de junio (bootstrap, 5109) | | | óptimo 13.500–14.000 | |

El público favorece 12.000 y junio favorece 12.500 o más. Se eligió **12.500**, el punto medio entre las dos
fuentes (~12.750) redondeado hacia la única medición sobre agosto.

---

## 6. Experimentos con las recomendaciones de la última semana (10 y 11/10)

### 6.1 Estrategia de entrenamiento 1.7 (4112 + 5113)

- **Dataset ds3007** (exp 3007, `03f_fe_profesor.py`): ds3003 + recomendaciones 1.1–1.4 (1.210 variables).
- **Bayesiana 4112** (`16_bo_profesor_v2.py`): AUC promedio de 5 particiones 70/30 estratificadas dentro de
  202103 + 202104; fijos de la estrategia 1.7; `num_iterations` 250–4000, `num_leaves` 8–2000,
  `min_sum_hessian_in_leaf` 0,001–100 (rangos propios: la recomendación no los fija). 16 pruebas en 15 h.
- Eligió árboles grandes: las mejores pruebas tienen ~1.000–1.800 hojas, 2.000–3.900 árboles y
  `min_sum_hessian_in_leaf` entre 0,002 y 0,1.
- **Evaluación 5113** (`18_ensamble_profesor.py`): ensamble de las 12 mejores, entrenado con 202103 + 202104 y
  medido en junio completo, contra la prueba 23 con 12 semillas sobre ds3003:

| Modelo | Meseta junio | Público 30% (12.000) | Privado 70% (12.000) |
|---|---|---|---|
| Ensamble escalado | 388,6 | 373,7 | 386,7 |
| Ensamble sin escalar | 389,7 | 377,8 | 389,7 |
| **Prueba 23 (semillerío de 12)** | **441,3** | **452,7** | **439,3** |

  El ensamble pierde en todos los cortes de 9.000 a 15.000. Los modelos individuales del ensamble promedian 389 M
  (desvío 11) y la prueba 23, 436 M (desvío 3,5): el mejor modelo del ensamble (406,8) no alcanza a la peor
  semilla de la prueba 23 (429,9). **R7 → no se adopta;** el final 5021 no se entrenó.
- Lectura: optimizar AUC llevó a `min_sum_hessian_in_leaf` muy bajos y árboles enormes, que en junio sobreajustan.

### 6.2 Feature engineering 1.1–1.4 con la prueba 23 (5114, `19_eval_dataset.py`)

Mismos hiperparámetros, mismas 20 semillas, entrenamiento 202103 + 202104, junio completo:

| Dataset | Meseta media | Desvío | Semillerío |
|---|---|---|---|
| ds3003 (vigente) | 436,5 | 3,7 | 441,4 |
| ds3007 (con FE 1.1–1.4) | 432,7 | 4,3 | 437,6 |

Diferencia −3,7 M, mejor en 4/20 semillas. **R8 → no se adopta.**

### 6.3 Columnas con valores anómalos (5023)

5015 sin `Master/Visa_Finiciomora` ni `Master/Visa_fultimo_cierre` (y sus lags y deltas; 20 columnas), que
presentan ceros inyectados en 202105, 202106 y 202108. Como la anomalía afecta a agosto, la validación en junio no
la puede medir y se usó el público con una regla exigente (≥ 100,6). Dio **94,35** contra 95,59 → no se adopta.

---

## 7. Supuestos y desvíos declarados

| # | Qué | Detalle |
|---|---|---|
| S1 | `min_data_in_leaf` **escalado por cantidad de filas** (×2 con 2 meses, ×4 en el final) | Decisión propia para que cada hoja represente la misma proporción de clientes. El valor final (40.496) queda fuera del rango de búsqueda recomendado (0–20.000). Apoyo: con la mitad del valor, 5109 dio −21 M |
| S2 | **580 árboles fijos** en el final | Salen del corte temprano de 4104 (solo abril); no se reajustaron para 4 meses. En 5109, 750 y 900 árboles no superaron la regla R3 |
| S3 | **`num_leaves` = 41 no actúa** | Con `bagging_fraction` 0,31 y `min_data_in_leaf` 40.496, cada árbol tiene como máximo ~5 hojas (654.066 × 0,3124 / 40.496) |
| S4 | **La prueba 23 llegó como referencia elegida por la mitad B** | En 4104 la regla eligió la prueba 35; la 23 (3.ª en A, 1.ª en B) se agregó como referencia en 4105 y desde entonces las búsquedas eligen entre referencias por B. Las cifras de la mitad B (435,8; 443,1) son algo optimistas. Las comparaciones en **junio completo** de 5113 y 5114 la confirman |
| S5 | **Búsqueda con marzo + abril, sin mayo** | Para mantener la distancia de 2 meses con junio. Con mayo, la medición sería a 1 mes y más optimista |
| S6 | **Métrica "meseta"** (12.000–17.000 envíos) en lugar del máximo | Reduce la sensibilidad al corte |
| S7 | `min_data_in_leaf` busca desde 1 | La escala logarítmica no admite 0; en la práctica son equivalentes |
| S8 | `max_bin` fijo en 31 | "Hasta 31" y "= 31" coinciden; buscarlo exige rearmar el dataset en cada prueba |
| S9 | `lambda_l1` = `lambda_l2` = 0,001 | Vienen de la prueba 23; efecto casi nulo (el default es 0) |
| S10 | Las 16 variables clave del proceso de muerte se eligieron con un diagnóstico que incluía junio | Verificado: sin junio, las 16 ocupan los mismos puestos (Spearman 0,999) |
| S11 | Lag2 se omitió durante un tramo (4105, 5103, 5011, 5104) | Corregido desde 5105; 5015 lo incluye. El submit 6 no tenía lag2 |
| S12 | `clase_binaria2` en lugar de `clase_binaria1` | Exp 4002: +11 a +18 M |

---

## 8. Lo que queda para la segunda competencia

1. **Validación y regularización.** La validación con 2 meses de entrenamiento eligió siempre el modelo más
   rígido, y ese valor se escaló ×4 para el final. Probar validar con 202103–202105 → 202106 antes de fijar la
   regularización, y medir el efecto de escalar en vez de suponerlo.
2. **Estrategia 1.7.** Buscar con la ganancia (no con AUC) o acotar `min_sum_hessian_in_leaf` a valores más altos.
3. **Aguinaldo.** Los deltas de orden 2 de agosto comparan contra junio; el ranking corrige niveles, no saltos.
4. **Calidad de datos en el mes a predecir.** Revisar 202108 antes de entrenar: la validación en junio no detecta
   anomalías que aparecen solo en agosto.

---

## 9. Reproducción

Ver `README.md`, sección 3. Cada experimento guarda en `exp/<id>_<nombre>/` su `PARAM.json`, una copia del script y
sus resultados, y agrega una fila a `exp/registro_experimentos.csv`.
