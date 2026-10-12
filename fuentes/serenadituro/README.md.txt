# DMEyF 2026 — Competencia 01

Predicción de bajas (BAJA+2) de clientes del banco para 202108. Todas las notebooks están en R y se corrieron en una VM de Google Cloud con 8 vCPU y 64 GB de RAM.

## Datos

Copiar el dataset crudo `competencia_01_crudo.csv` (también sirve `.csv.gz` o `.zip`) en:

```
~/buckets/b1/datasets/
```

La carpeta tiene que existir. Las notebooks generan solas la clase ternaria y el dataset con feature engineering, y escriben sus resultados en `~/buckets/b1/exp/`. Si se usa otra carpeta base, cambiar `carpeta_base` en la primera celda de cada notebook.

## Notebooks

| Notebook | Qué hace |
|---|---|
| `C1_E012_con-rank-final_BO.ipynb` | Desarrollo de la E012: feature engineering y **optimización bayesiana** |
| `C1_E012_modelo-MH-entrega.ipynb` | Entrega de la E012: hiperparámetros fijos, test en 202106, 20 modelos finales, ensamble y archivo para Zulip |
| `exp/HTC1_E012/BO_eval_kfold5_auc.txt` | Cada evaluación de la optimización bayesiana, en orden (hiperparámetros, AUC, minutos) |
| `exp/HTC1_E012/BO_log_kfold5_auc.txt` | Las mismas evaluaciones ordenadas por AUC (archivo final de la BO cortada) |

**Feature engineering**
`ccajas_depositos` en NA para 202105 → lag1/delta1 y lag2/delta2 → ranking por mes con cero fijo de todas las variables (salvo `numero_de_cliente`, `foto_mes` y `clase_ternaria`).

**Optimización bayesiana:** `mlrMBO`, k-fold 5 estratificado sobre 202103–202105, métrica AUC, sin undersampling, rangos de la notebook z495 (`num_iterations` 64–4096, `num_leaves` 16–2048, `min_sum_hessian_in_leaf` 1e-06–0.1).

## Cómo reproducir la entrega

Los hiperparámetros de los modelos finales **no se optimizan en la notebook de entrega**: vienen de la BO de la notebook de desarrollo del mismo experimento. Por eso hay dos formas de correrlo.

## Origen de los hiperparámetros

Los hiperparámetros de los modelos finales salen de la optimización bayesiana de la notebook de desarrollo `C1_E012_con-rank-final_BO.ipynb` (sección 4.5): k-fold 5 estratificado, métrica AUC, sin undersampling, rangos de la notebook z495. La BO se cortó después de 16 evaluaciones (12 puntos iniciales + 4 iteraciones bayesianas) y se tomó el punto de mayor AUC.

El registro completo está en `exp/HTC1_E012/`:
- `BO_eval_kfold5_auc.txt`: cada evaluación en el orden en que se hizo (hiperparámetros, AUC y minutos).
- `BO_log_kfold5_auc.txt`: las mismas evaluaciones ordenadas por AUC.

### Envío final

| Experimento | Modelos en el ensamble | Envíos | Archivo |
|---|---|---|---|
| C1_E012 | 20 | 12000 | `exp/C1_E012_entrega_MH/zulip/C1_E012_ensamble_20S_12000.csv` |

El archivo es el ensamble de los 20 modelos (promedio por cliente de las probabilidades, 20 semillas fijas), ordenado de mayor a menor y cortado en la cantidad de envíos elegida.
