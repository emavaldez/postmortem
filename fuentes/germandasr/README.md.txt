# Entrega final -- DMEyF 2026, Primera Competencia

Reproduce exactamente el archivo CSV enviado como última entrega al bot `competencia-uno`.

## Metodología

LightGBM con Bayesian Optimization (mlr3/mlr3mbo), entrenado sobre variables originales +
lag1/lag2/delta1/delta2 (sin Ranking Cero Fijo), sin undersampling. La BO se corre con
marzo+abril (202103-202104, meses con `clase_ternaria` 100% real) como train/validation. El
modelo final se entrena con marzo a junio (202103-202106, todo lo conocido antes de agosto) y
predice sobre agosto (202108). Semillerío de 20 semillas, ensamble por promedio simple de
probabilidades.

## Archivos

| Archivo | Qué hace |
|---|---|
| `Exp_51_entrega_final.ipynb` | Notebook único y self-contained: desde el dataset crudo de la competencia hasta `probabilidades_20_semillas.txt` (corre la Bayesian Optimization y despues entrena las 20 semillas finales). Tarda varias horas en correr completo. |
| `Exp_51_ensamble_submit.ipynb` | Toma `probabilidades_20_semillas.txt`, arma el ensamble (promedio simple de las 20 probabilidades) y genera `entrega_final.csv` -- el archivo exacto que se subió al bot. No necesita reentrenar nada. |
| `probabilidades_20_semillas.txt` | Probabilidades ya calculadas (20 columnas, una por semilla) para agosto. Se provee como atajo, para poder correr `Exp_51_ensamble_submit.ipynb` directamente sin tener que correr `Exp_51_entrega_final.ipynb` (que tarda horas). |

## Cómo reproducir

**Opción rápida (recomendada):** usar el `probabilidades_20_semillas.txt` ya provisto y correr
directamente `Exp_51_ensamble_submit.ipynb`. Genera `entrega_final.csv` en segundos.

**Opción completa (desde cero):**
1. Correr `Exp_51_entrega_final.ipynb` de punta a punta. Requiere el dataset crudo de la
   competencia (`competencia_01_crudo.csv`) en la ruta indicada en la celda de setup inicial
   (ajustar `PARAM$data_dir` según corresponda). Genera `BO_log.txt` y
   `probabilidades_20_semillas.txt`.
2. Correr `Exp_51_ensamble_submit.ipynb` en la misma carpeta. Genera `entrega_final.csv`.

## Corte final

El corte (cantidad de clientes a los que se les envía la oferta) está fijado en la variable
`CORTE_FINAL` dentro de `Exp_51_ensamble_submit.ipynb`.
