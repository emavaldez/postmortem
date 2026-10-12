# DMEyF 2026 · Primera Competencia — Rodrigo Palpa

Maestría en Minería de Datos (UBA) · Data Mining en Economía y Finanzas.

Objetivo: elegir a qué clientes de la foto `202108` enviarles el estímulo de retención, maximizando
`+1.072.500` por cada `BAJA+2` acertado y `−27.500` por cada estimulado que no lo es.

## 1. La entrega final

| | |
|---|---|
| Archivo | `entrega_final/Z6011_5015_e12500_final2.csv` |
| Contenido | 12.500 `numero_de_cliente` de 202108, una columna, sin encabezado |
| Modelo | experimento **5015** (semillerío de 50 LightGBM) |
| Submit final | `submit 5015e12500final2` · ID `1626-1791760490758459` · 11/10/2026 20:14 |
| Ganancia pública | **95,59** (el mismo modelo con 12.000 envíos dio 96,11) |

## 2. El modelo, en una tabla

| Pieza | Elección | Script / config |
|---|---|---|
| Datos | `competencia_01_crudo.csv` → `clase_ternaria` con la lógica de la cátedra, más `clase_binaria1` (BAJA+2) y `clase_binaria2` (BAJA+1 y BAJA+2) | `01_preparar_dataset.py` |
| Clase de entrenamiento | `clase_binaria2` (BAJA+1 + BAJA+2 positivos). La ganancia se mide siempre con BAJA+2 | — |
| Variables (dataset **ds3003**, 766) | Lags y deltas de orden 1 y 2 de las 152 variables, calculados sobre los valores crudos (NA si el cliente no estaba exactamente k meses antes). Después, **todas** las columnas se reemplazan por su ranking dentro del mes con el cero fijo: positivos en (0,1], negativos en [−1,0), cero = 0, NA = NA; esto corrige la inflación y el aguinaldo. Más 6 variables propias del "proceso de muerte": `n_apagados` (cuántos de 16 productos clave están en 0 o NA), sus deltas 1 y 2, `n_dejo_de_usar`, `ctrx_quarter_rel_max3` y `mcaja_ahorro_rel_max3` | `03c_fe_extra.py` |
| Hiperparámetros | **Prueba 23**: `learning_rate` 0,0678 · `num_leaves` 41 · `min_data_in_leaf` 10.124 por mes de entrenamiento · `feature_fraction` 0,1798 · `bagging_fraction` 0,3124 (`bagging_freq` 1) · `lambda_l1` = `lambda_l2` = 0,001 · `max_bin` 31 · 580 árboles | `08_bo_fuera_de_tiempo.py` (4104 → 4107) |
| `min_data_in_leaf` final | Escalado por cantidad de filas: 10.124 × 4 meses = **40.496** | `07_modelo_final.py` |
| Entrenamiento final | 202103–202106 (654.066 filas), **sin undersampling** | `configs/5015_prod_profesor_mar_jun.json` |
| Semillerío | 50 semillas: 571369, 849571, 355049, 655531, 700103 y 45 primos generados a partir de la primera; se promedian las probabilidades | `07_modelo_final.py` |
| Corte | Los **12.500** clientes de mayor probabilidad (sección 5) | `10_entrega_zulip.py`, `configs/6011_zulip_final_5015.json` |

## 3. Cómo reproducir la entrega

### Requisitos

- Windows o Linux con **Python 3.12** y `pip install -r requirements.txt`.
- ~16 GB de RAM (el entrenamiento final usa 4 meses × 766 variables).
- El dataset de la cátedra `competencia_01_crudo.csv` en `data/` (no se incluye en el repo).
- La carpeta del proyecto: `exp_utils.py` toma la raíz de la variable de entorno `DMEYF_ROOT`;
  si no existe, usa la ruta de la máquina original. Antes de correr:
  - Windows: `set DMEYF_ROOT=%CD%` (desde la carpeta del repo)
  - Linux: `export DMEYF_ROOT=$(pwd)`

### Camino corto (~1 a 2 h): usa los hiperparámetros ya elegidos

Los hiperparámetros salen de `exp/4107_bo_profesor_mar_abr/4107_eleccion.json`, que está en el repo.

```bash
py -3.12 01_preparar_dataset.py                                       # data/ds1001_base.parquet
py -3.12 03c_fe_extra.py                                              # data/ds3003_rank_extra.parquet
py -3.12 07_modelo_final.py configs/5015_prod_profesor_mar_jun.json   # exp/5015_.../5015_probabilidades.csv
py -3.12 10_entrega_zulip.py configs/6011_zulip_final_5015.json       # exp/6011_.../zulip/*.csv
```

El archivo entregado es `exp/6011_zulip_final_5015/zulip/Z6011_5015_e12500_semillerio.csv`
(copiado como `entrega_final/Z6011_5015_e12500_final.csv`). Para verificarlo, comparar los dos archivos
(mismo conjunto de ids). LightGBM es multihilo: en otra máquina puede haber diferencias mínimas en las
probabilidades y, como mucho, unos pocos clientes distintos cerca del corte.

### Camino completo: también la búsqueda de hiperparámetros (varias horas)

```bash
py -3.12 03b_fe_rank_total.py                                             # ds3002 (sin las 6 variables propias)
py -3.12 08_bo_fuera_de_tiempo.py configs/4104_bo_rank_total.json         # encuentra la prueba 23 (entrena abril)
py -3.12 08_bo_fuera_de_tiempo.py configs/4107_bo_profesor_mar_abr.json   # Bayesiana marzo + abril; confirma la prueba 23
```

Después, los cuatro comandos del camino corto. Las mitades de junio que usan todas las búsquedas están en
`exp/4102_bo_fuera_de_tiempo/4102_mitades_junio.csv`.

## 4. Cómo se validó

- **Fuera de tiempo:** se entrena con **202103 + 202104** y se mide en **202106**, que tiene la clase completa.
  Respeta la misma distancia de 2 meses que hay entre junio y agosto.
- **Mitades fijas de junio**, estratificadas por clase (549 BAJA+2 en cada una): la Bayesiana elige mirando
  la **mitad A** y la **mitad B** solo se usa para confirmar. En las últimas comparaciones se usó junio completo.
- **Métrica "meseta":** ganancia promedio entre 12.000 y 17.000 envíos (equivalentes al mes completo), más
  estable que el máximo de la curva.
- **Reglas fijadas antes de ver los resultados** para cada decisión (R1–R9), con semillas pareadas y
  bootstrap o Wilcoxon. Están en el informe técnico.

## 5. El corte

| Evidencia | Corte que favorece |
|---|---|
| Público (5005: 10.000 → 89,4 · 12.000 → 96,6 · 14.000 → 90,3; 5015: 12.000 → 96,11 · 12.500 → 95,59) | ~12.000 |
| Mitad B de junio (bootstrap) | 13.500–14.000 |
| Junio completo, prueba 23 con 12 y 20 semillas (5113, 5114) | meseta plana de 12.500 a 15.000 |

Se eligió **12.500**: el punto medio entre lo que sugería el público y lo que mostraba junio. La diferencia
pública entre 12.000 y 12.500 (−0,5) está dentro del ruido (±2 a 3 entre listas parecidas).

## 6. Recomendaciones del profesor: cómo se evaluaron

Cada recomendación se evaluó con el mismo protocolo (entrenar con marzo + abril, medir en junio contra el
modelo vigente, regla fijada de antemano). Se adoptaron las que mejoraron o empataron.

| Recomendación | Cómo se evaluó | Resultado | Decisión |
|---|---|---|---|
| Lags y deltas de orden 1 y 2, y ranking por mes con cero fijo | 5105 / 5106: receta contra el dataset anterior; lag2 contra sin lag2 | La receta mejora; lag2 empata | **Adoptada** (ds3003) |
| Usar toda la información disponible para buscar hiperparámetros (marzo + abril aunque tengan NA) | 5107: búsqueda con marzo + abril contra solo abril | +4,8 M en junio (75% de los remuestreos) | **Adoptada** |
| Entrenar el final con todos los meses con clase (marzo a junio) | Entrenamiento final de 5015 | — | **Adoptada** |
| Sin undersampling, `max_bin` 31, rangos de búsqueda (`num_leaves` 8–2000, `min_data_in_leaf` 0–20.000, `feature_fraction` 0,05–0,9, `bagging_fraction` 0,05–1, `learning_rate` 0,01–0,2) | Bayesiana 4107 | Ninguna prueba nueva superó a la prueba 23 en la mitad B | **Adoptada**; se mantuvo la prueba 23 |
| Estrategia de entrenamiento 1.7: AUC, `learning_rate` 0,005, `min_data_in_leaf` 0, `feature_fraction` 0,5, `feature_fraction_bynode` 0,2, Bayesiana sobre árboles, hojas y `min_sum_hessian_in_leaf`, y ensamble de 10+ modelos | 4112 (16 pruebas, 15 h) + 5113: ensamble de las 12 mejores contra la prueba 23 | Junio 389,7 vs 441,3: **−52 M**, menor en todos los cortes | No adoptada (regla R7). La búsqueda por AUC eligió árboles de ~1.000 hojas con `min_sum_hessian_in_leaf` muy bajo |
| Feature engineering 1.1–1.4: `ccajas_depositos` NA en 202105, flags `_zero`, tendencia y promedio de 3 meses | 5114 (ds3007) con los hiperparámetros de la prueba 23, 20 semillas pareadas | Junio 432,7 vs 436,5: **−3,7 M**, mejor en 4/20 semillas | No adoptada (regla R8, tolerancia 3 M) |

## 7. Otras pruebas

Junio = ganancia de meseta en junio (mitad B ×2 o junio completo, según el experimento), contra el modelo de
referencia del momento. Público = ganancia en el bot.

| Exp | Qué probé | Resultado | ¿Me lo quedé? | Por qué |
|---|---|---|---|---|
| 5005 | Crudo, 123 variables elegidas con canaritos, hiperparámetros de la Bayesiana 4102 | Público 96,58 (12.000) | No | Base de comparación; después el ranking corrigió la inflación |
| 5105 | 6 variables propias del proceso de muerte (ds3003) contra el dataset sin ellas (ds3002) | Junio +4,6 M (81% de los remuestreos) | **Sí** | Mejora estable |
| 5108 | Variables de muerte ampliadas (ds3006) | Junio −7,8 M | No | Regla R1 |
| 5109 | Prueba 23 con la mitad de `min_data_in_leaf` | Junio −21 M | No | Sustenta escalar `min_data_in_leaf` por filas |
| 4109 / 5110 | Bayesiana "limpia" (elegida solo por la mitad A) | Junio 432,5 vs 443,1 | No | Regla R4 |
| 5202 | Combinar 5005 con la receta sin lag2 | Público 94,44 | No | Mezclar con un modelo peor bajó al mejor |
| 5023 | 5015 sin `Master/Visa_Finiciomora` ni `Master/Visa_fultimo_cierre` (columnas con ceros inyectados en 202105, 202106 y 202108) | Público 94,35 (12.500) | No | Regla fijada antes: cambiar solo si el público ≥ 100,6. Se reenvió 5015 como submit final |

## 8. Supuestos y desvíos declarados

- **Escalar `min_data_in_leaf` por filas** (×2 con dos meses, ×4 en el final). Es una decisión propia; el valor
  final (40.496) queda fuera del rango de búsqueda recomendado (0–20.000). Se apoya en 5109.
- **580 árboles fijos** en el final, aunque entrena con más meses que la búsqueda.
- **`num_leaves` = 41 no actúa:** con `bagging_fraction` 0,31 y `min_data_in_leaf` 40.496, cada árbol tiene
  como máximo ~5 hojas. El modelo es un boosting de árboles muy chicos.
- **La prueba 23** fue encontrada en 4104 (entrenando solo abril, dataset ds3002). La Bayesiana 4107, con
  marzo + abril y los rangos recomendados, la evaluó como referencia y ninguna prueba propia la superó en la mitad B.
- **ds3003 no pone `ccajas_depositos` en NA en 202105.** Esa corrección se evaluó dentro de ds3007 (5114) y no mejoró.

## 9. Lo que me llevo para la segunda competencia

- **La validación con 2 meses de entrenamiento eligió siempre el modelo más rígido** (árboles de ~5 hojas), y
  después ese valor se escaló ×4 para el final. Hipótesis a probar: validar entrenando con más meses
  (202103–202105 → 202106) antes de elegir la regularización, y medir el efecto de escalar `min_data_in_leaf`
  en vez de suponerlo.
- **La estrategia 1.7 depende mucho de `min_sum_hessian_in_leaf`:** optimizar por AUC la llevó a valores muy
  bajos y a árboles enormes. Conviene buscar con la ganancia o acotar ese parámetro a valores más altos.
- **El aguinaldo de junio afecta los deltas de orden 2 de agosto**, que comparan contra junio. El ranking por
  mes corrige los niveles, pero no los saltos.
- **Calidad de datos en el mes a predecir:** revisar columnas con valores anómalos en 202108 antes de entrenar,
  porque la validación en junio no puede detectarlos.

## 10. Estructura del repo

```
README.md · requirements.txt · .gitignore
exp_utils.py                       registro de experimentos (cada uno en exp/<id>_<nombre>/)
01_*.py ... 19_*.py                scripts numerados (dataset, FE, búsqueda, final, entrega, evaluaciones)
configs/                           un JSON por experimento (lo que se corrió, con su descripción)
*.bat                              lotes reanudables usados en Windows
exp/                               PARAM, resultados y elecciones de cada experimento (sin archivos pesados)
entrega_final/                     el CSV enviado como submit final
informe_tecnico.md                 decisiones, reglas, resultados y desvíos en detalle
```

`data/`, `logs/`, cachés y probabilidades por semilla no se versionan: se regeneran.
