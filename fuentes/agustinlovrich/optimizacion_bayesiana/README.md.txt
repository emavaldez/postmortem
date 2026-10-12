# Optimización bayesiana: hiperparámetros del modelo final

Esta carpeta documenta **cómo se obtuvieron los hiperparámetros** del modelo final y permite
**saltar la optimización bayesiana** (BO) para no repetirla (~125 min), usando directamente la
configuración encontrada.

Se incluye por la indicación de la cátedra: si un modelo usa los mejores hiperparámetros de una
corrida anterior para no volver a correr la BO, hay que subir **también la optimización que los
originó** y explicar cómo proceder.

## Archivos

| Archivo | Qué es |
|---|---|
| `bo_mejor_config.csv` | La configuración elegida por la BO (la que salta la optimización). |
| `bo_evaluaciones.csv` | **La optimización completa**: cada punto evaluado por la BO con su AUC y ganancia. |
| `junbo_hist.log` | Log completo de la corrida que generó todo (procedencia verificable). |

### `bo_mejor_config.csv`
```
fuente,num_leaves,min_sum_hessian_in_leaf,num_iterations,auc
BO_AUC,256,0.0299943000368938,1439,0.919070894119264
```
- `num_leaves = 256`, `min_sum_hessian_in_leaf = 0.0299943000368938`, `num_iterations = 1439`.
- Elegida por **AUC** sobre la validación de 202106 (la métrica que optimiza la BO).

## Cómo se generó (la optimización)

En el mismo script `run_rank_prestamos_junbo_hist.R`, paso 8:

- **Motor:** `mlrMBO` con surrogate Kriging (`regr.km`, matérn 3/2) y criterio de infill
  **Expected Improvement**.
- **Diseño inicial:** 10 puntos de un hipercubo latino maximin.
- **Iteraciones:** hasta 30 guiadas por EI, con tope de 120 minutos.
- **Espacio de búsqueda:** `num_iterations ∈ [600, 3500]`, `num_leaves ∈ [16, 256]`,
  `min_sum_hessian_in_leaf ∈ [0.0001, 0.03]`.
- **Datos de la BO:** entrena 202103+04, valida 202106 (sin cross-validation), **sin
  undersampling** y **sin las columnas de los 2 préstamos personales** (1050 columnas, ya con el
  FE histórico).
- **Semilla:** la primigenia 100193 → la BO es **determinista y reproducible**.
- **Selección:** la mejor por AUC. En `bo_evaluaciones.csv` queda registrada también la ganancia
  por corte de cada punto (informativa; no cambia la selección).

El trazado completo (con la correlación AUC↔ganancia de esa corrida) está en `junbo_hist.log`.

> **Observación:** la BO eligió `num_leaves = 256`, que es el **tope del rango** (`hojas_max`), y
> un hessiano (`0.0299943`) muy cerca de su tope (`0.03`). La búsqueda quedó pegada al borde del
> espacio, así que el óptimo podría estar más allá del rango. Ampliar el rango de hojas sería el
> próximo paso; para esta entrega se usó la mejor configuración dentro del rango.

## Cómo usar estos hiperparámetros para saltar la BO

El script busca un archivo `bo_mejor_config.csv` **dentro de la carpeta de salida**
(`DMEYF_EXP`). Si existe, no corre la optimización y usa esos hiperparámetros:

```bash
mkdir -p salida_run
cp optimizacion_bayesiana/bo_mejor_config.csv salida_run/bo_mejor_config.csv

DMEYF_CRUDO=data/competencia_01_crudo.csv \
DMEYF_EXP=salida_run \
GCS_BUCKET= \
NTHREAD=8 NSEEDS=40 \
Rscript run_rank_prestamos_junbo_hist.R
```

En el log verás `bo_mejor_config.csv ya existe: no repito la BO` y luego
`hiperparametros finales [BO_AUC]: hojas 256 | hess 0.02999430 | arboles 1439`. El resto del
pipeline (feature engineering, FE histórico, 40 semillas, ensamble, cortes) es idéntico a la
reproducción completa.

> **Importante:** saltar la BO da exactamente la misma configuración que correrla (es
> determinista). Esta opción es solo para ahorrar las ~2 horas de optimización.
