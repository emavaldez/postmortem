---

editor_options: 
  markdown: 
    wrap: sentence
---

# Primera competencia DMEyF 2026 — Entrega final (Laura Pasquini)

**Archivo entregado como último submit:** `Aprimaplus_B100_corte10600.csv` (10.600 clientes con `Predicted = 1`; Public Leaderboard: ganancia 119,3775).

El archivo sale de un ensamble de dos modelos LightGBM, **A'plus** y **B**, con 100 semillas cada uno. Todo lo necesario para regenerarlo exactamente está en la raíz de esta carpeta: la notebook final y `variables_A_Aprimaplus.txt`. La carpeta `procesamiento_previo/` documenta **de dónde salen** los hiperparámetros y las listas de variables que la notebook final usa como datos fijos (no hace falta volver a ejecutarla).

## Estructura

```         
Notebook_final_reproducible_Aprimaplus_B100.ipynb   <- genera el archivo entregado (hay que ejecutarla)
variables_A_Aprimaplus.txt                           <- lista de las 576 variables de A'plus (entrada de la notebook)
README.md
procesamiento_previo/                                <- evidencia, no hace falta ejecutarla
    (16 notebooks, ver tabla)
    archivos_de_apoyo/                               <- log de la BO y listas de variables
```

| Etapa | Notebook (`procesamiento_previo/`) | Qué documenta |
|------------------------|------------------------|------------------------|
| BO | `z494_TareaHogar_04_TerceraCapa_SalsaMagica` | Bayesian Optimization (experimento 4961) |
| BO | `z601_BO_Diagnostico` | Diagnóstico de la BO |
| BO | `z601_Top3Trials_NSemillas`, `z601_Top5Trials_NSemillas` | Validación de los mejores trials con 10 semillas |
| Grilla | `z494_Grilla_LR_ScalePosWeight_Trial2` | learning_rate × scale_pos_weight sobre el trial 2 |
| Grilla | `z_grid_lr_scalePosWeight` | Misma grilla, más fina, sobre 359 variables |
| Grilla | `z_grilla_mdl_modeloA` | `min_data_in_leaf` de A (→ 4000) |
| Grilla | `z_grilla_rankeado_lags`, `z_grilla_min_data_lags`, `z_grilla_min_data_in_leaf_canaritos` | `min_data_in_leaf` de B (→ 1000) |
| Variables | `z_canaritos_asesinos` | Lista A (358 variables) |
| Variables | `z_canaritos_202105_06` | Lista A' (526 variables) |
| Variables | `z_overnight_canaritos_genetico`, `z_verificacion_gen1_sobre_ganadora`, `z_modeloA_gen1_v2` | Origen y verificación de `gen_1` |
| Variables | `z_exportar_datasets_A_B_rankeados` | Exportación de los datasets procesados (auxiliar) |

## Cómo replicar el archivo entregado

1.  Dejar `competencia_01.csv` en la carpeta de datasets y poner `variables_A_Aprimaplus.txt` junto a la notebook.
2.  En la celda 1 de `Notebook_final_reproducible_Aprimaplus_B100.ipynb` cambiar **solo las dos rutas** (carpeta de datasets y carpeta de salida).
3.  Ejecutar la notebook completa (R, kernel IRkernel). `N_SEMILLAS <- 100` ya está configurado.
4.  Resultado: `Aprimaplus_B100_corte10600.csv` en la carpeta de salida. La sección 10 lo compara con el archivo entregado (cuando está disponible).

**Tiempos medidos** (PC con 20 GB de RAM): preparación de datos ≈ 70 min; modelo A'plus ≈ 1,9 min por semilla; modelo B ≈ 4,2 min por semilla. Con 100 semillas por modelo el total es ≈ 11 h. La notebook es **reanudable**: guarda un ranking por semilla en `rankings/` y salta los ya hechos. Para una verificación rápida: `N_SEMILLAS <- 1` (≈ 1 h 20 min); la sección 11 compara el resultado de la semilla 585581 con el original (idéntico).

**Precaución:** la primera celda de configuración contiene `rm(list = ls())`; no volver a ejecutarla en medio de una sesión.

## Qué hace el modelo

- **Entrenamiento:** meses 202103 a 202106 (con `clase_ternaria` BAJA+2 como objetivo). **Predicción:** 202108.
- **Variables históricas:** el promedio, máximo, mínimo, razones (valor actual / promedio y / máximo) y tendencia de 3 meses se calculan dentro de la notebook final (celda 12) a partir del valor actual y los rezagos de 1 y 2 meses; no hace falta ejecutar ningún otro notebook para generarlas.
- **Transformación de variables:** "ranking cero fijo" por mes y variable (ceros fijos en 0, valores distintos de cero reescalados de 1 a 100, NA se mantiene). Se corrige `ccajas_depositos` de 202105 (ceros pasados a NA).
- **Modelo A'plus:** 576 variables (575 seleccionadas con canaritos + `gen_1`), `min_data_in_leaf = 4000`.
- **Modelo B:** 760 variables = 152 variables × (original, lag 1, lag 2, delta 1, delta 2), `min_data_in_leaf = 1000`. Sin `foto_mes` ni `numero_de_cliente`.
- **Hiperparámetros comunes:** learning_rate 0,02; feature_fraction 0,1541961; num_leaves 1684; lambda_l1 1,520327; lambda_l2 7,548036; min_gain_to_split 0,2158453; bagging_fraction 0,8425105 (freq 6); scale_pos_weight 0,5; 600 iteraciones; max_bin 31; boosting gbdt.
- **Ensamble en dos niveles (todo por percentiles):**
  1.  Por semilla: la probabilidad predicha se convierte en percentil (`rank/n`).
  2.  Por modelo: promedio de los 100 percentiles de cada modelo (rA, rB).
  3.  Entre modelos: `(rA + rB) / 2`.
  4.  Corte: los 10.600 clientes con mayor puntaje reciben `Predicted = 1`.

## Origen de los hiperparámetros (`procesamiento_previo/`)

1.  **Bayesian Optimization (mlrMBO)** — `z494_TareaHogar_04_TerceraCapa_SalsaMagica.ipynb`: experimento 4961, 11 hiperparámetros, 100 iteraciones, 5 folds, undersampling 0,1 de los CONTINUA, entrenamiento solo en 202104 (151 variables originales, sin lags), ganancia directa como métrica. Sigue la plantilla de la Tarea Hogar 04 del curso, con "Salsa Mágica" (se excluyen `cprestamos_personales` y `mprestamos_personales`). Resultados en `archivos_de_apoyo/` (`BO_log.txt`, `bayesiana.RDATA` y `PARAM.yml`, de la carpeta `HT4961`). El `competencia_01.csv` se genera en esa misma notebook (celda de `clase_ternaria`) a partir del archivo crudo.
2.  **Selección del trial:** el mejor trial por ganancia interna (trial 1) no fue el elegido. Con 10 semillas sobre 202106 el **trial 2** (iteración 70; ganancia interna 253,66 M; segundo mejor) validó mejor (media 439,9 M contra 411,0 M del trial 1; `z601_Top3Trials_NSemillas.ipynb` y `z601_Top5Trials_NSemillas.ipynb`). De ese trial se toman feature_fraction, num_leaves, min_gain_to_split, lambda_l1, lambda_l2 y bagging_fraction. `z601_BO_Diagnostico.ipynb` muestra el diagnóstico de la BO. *Limitaciones conocidas:* (a) la BO y estas comparaciones usan `numero_de_cliente` como variable (así viene la plantilla del curso); los modelos finales lo excluyen;
    (b) `Top3/Top5` usan `min_data_in_leaf` sin multiplicar por 10 (el factor de la normalización por undersampling), por lo que la comparación entre trials no es exactamente la misma configuración que se usa después.
3.  **Grilla learning_rate × scale_pos_weight:** `z494_Grilla_LR_ScalePosWeight_Trial2.ipynb` (sobre el trial 2, 930 iteraciones, una semilla, 25 combinaciones): ganó learning_rate 0,02 y scale_pos_weight 0,5. `z_grid_lr_scalePosWeight.ipynb` repite una grilla más fina (56 combinaciones, 3 etapas, 600 iteraciones, 359 variables): el mejor candidato (0,015 / 0,6) quedó prácticamente empatado (+0,11 M sobre 463,98 M, dentro del ruido) y se mantuvo 0,02 / 0,5.
4.  **`min_data_in_leaf`:**
    - **A'plus = 4000:** `z_grilla_mdl_modeloA.ipynb` (A con 358 variables + `gen_1`, dataset rankeado con lags y FE histórico, 10 semillas, entrenamiento 202103+202104, corte fijo 12.000, resto de hiperparámetros fijos). Valores probados 300, 500, 1000, 2000, 3000, 4000 y 5000: ganó 4000 (media 463,98 M); 3000 y 2000 quedaron muy cerca (463,65 M y 463,43 M). La grilla se hizo sobre el modelo A de 358 variables; el valor se mantuvo al pasar a A'plus (576 variables). Como respaldo, en `z_grilla_min_data_lags.ipynb` (dataset con lags sin rankear) un `min_data_in_leaf` alto reduce el porcentaje de Gain que se llevan los canaritos (de 50,7 % con 1000 a 40,8 % con 4000).
    - **B = 1000:** `z_grilla_rankeado_lags.ipynb` (grilla de B sobre el dataset rankeado con lags; confirmó 1000 como mejor valor) y, antes, `z_grilla_min_data_lags.ipynb` (1000 y 2000 empatan en 464,09 M; se eligió 1000). `z_grilla_min_data_in_leaf_canaritos.ipynb` (variables originales, 151) también da 1000 como mejor valor para B (450,78 M).
5.  **600 iteraciones:** valor fijado en las primeras pruebas manuales con learning_rate 0,02, sin grilla propia. Los notebooks de la cadena de canaritos ya usaban 600 y se mantuvo para el modelo final (la grilla sobre el trial 2 usa 930, que es el valor de la BO con su learning_rate original de 0,0273).

La BO **no se vuelve a ejecutar**: el log se incluye como evidencia y los valores quedan fijos en la notebook final.

**Otras BOs exploradas y no adoptadas.** Además de la BO de la que salen los hiperparámetros finales (HT4961, trial 2), se probaron otras optimizaciones que **no** intervienen en el archivo entregado y por eso no se incluyen en este repositorio:
- BO de 11 hiperparámetros sobre el dataset con lags rankeado (751 variables) y sobre la lista de 358 variables + `gen_1`, primero optimizando AUC (la ganancia real quedó en 452,65 M contra 463,98 M de referencia) y luego ganancia directa (411,77 M en screening de 3 semillas; descartada porque los hiperparámetros quedaron pegados a los bordes del espacio de búsqueda y el modelo se sobreajustó a los folds internos).
- BO entrenando con los 4 meses (202103 a 202106), con y sin canaritos.
- BO por separado para el modelo A y para el modelo B (con undersampling 0,1 y folds agrupados por cliente).
- BO de B contra pseudo-etiquetas de 202108.

Ninguna de ellas reemplazó a los hiperparámetros del trial 2, que son los que usa la notebook final para A'plus y B (solo `min_data_in_leaf` se define por modelo, ver más abajo).

## Origen de las listas de variables (`procesamiento_previo/`)

- **Lista A (358 variables):** `z_canaritos_asesinos.ipynb`, receta de la cátedra ("canaritos asesinos": 20 % de canaritos, un LightGBM, id ordinal por importancia, se descartan las variables con id mayor a media + 2 desvíos de los ids de los canaritos), entrenando con 202103 y 202104.
- **Lista A' (526 variables):** `z_canaritos_202105_06.ipynb`, misma receta entrenando con 202105 y 202106 y con dos semillas (585581 y 249449); A' es la **intersección** de las dos listas de 2 desvíos.
- **A'plus (575 variables)** = unión de A y A'. Más `gen_1` = 576 (`variables_A_Aprimaplus.txt`, en orden). La notebook final verifica que la lista que calcula coincide con ese archivo.
- **`gen_1` = `ctrx_quarter` + `cpayroll_trx_min3`:** surgió de un algoritmo genético (AUC univariado) en `z_overnight_canaritos_genetico.ipynb` (parte 2; la parte 1 es una poda de canaritos anterior, descartada; la corrida original duró unas 8,9 h (≈ 11.900 generaciones) y el mejor individuo fue siempre el mismo, con AUC univariado 0,8752: `genetico_top_features.txt` lo registra y `genetico_log.txt` guarda la evolución. Dos corridas posteriores (v2 y v3, no incluidas) encontraron otras combinaciones con AUC univariado similar (0,8775 y 0,8756) que no se adoptaron en el modelo final). Se verificó en `z_verificacion_gen1_sobre_ganadora.ipynb` sobre la lista A de 358 variables, con 10 semillas: 462,44 M sin `gen_1` contra 463,98 M con `gen_1` (+1,54 M, dentro del ruido entre semillas; sobre la poda vieja de 110 variables había sumado +4,29 M) y se conservó. `z_modeloA_gen1_v2.ipynb` compara además `gen_1` sin rankear contra rankeada (463,98 M contra 463,43 M). En el modelo final se calcula sobre las variables ya rankeadas.
- Del modelo A se excluyen `Master_fultimo_cierre`, `Visa_fultimo_cierre` y `Visa_mpagado` (variables con un mes anómalo).
- Los archivos de listas (`campos_canaritos_asesinos_2sd.txt`, `campos_canaritos_202105_06_s585581_2sd.txt`, `campos_canaritos_202105_06_s249449_2sd.txt`, `genetico_top_features.txt`) están en `procesamiento_previo/archivos_de_apoyo/`.
- `z_exportar_datasets_A_B_rankeados.ipynb` exporta los datasets ya procesados (unión de A y A', lags, deltas y ranking); es un auxiliar y no interviene en el archivo final.

## Verificación realizada

- Semilla 585581 reentrenada desde cero con la notebook final: ranking idéntico al original (A'plus y B).
- El archivo final reconstruido a partir de los 200 rankings guardados coincide con el entregado: 10.600 de 10.600, mismo orden.

## Entorno

R 4.5.3, Windows, 20 GB de RAM. Paquetes: data.table, lightgbm 4.7.0. El entrenamiento es determinista para una semilla dada.

## Uso de asistencia de IA

Para el desarrollo de este trabajo usé Claude (Anthropic) como asistente: revisión y limpieza de código,
armado de la notebook reproducible final y redacción de este README. Las decisiones de modelado,
los experimentos y las corridas son propios.
