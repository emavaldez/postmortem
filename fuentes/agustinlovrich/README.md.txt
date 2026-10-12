# DM EyF 2026: Competencia 01 (predicción de BAJA+2 en 202108)

Entrega de **Agustín Lovrich**. Este repositorio contiene **todo lo necesario para replicar
en forma exacta la predicción final** que subí al bot: el script end-to-end, los
hiperparámetros con la optimización bayesiana que los produjo, y el archivo de entrega.

- **Predicción final entregada:** `prediccion_final/lovrich_ensamble_corte11000.csv`
- **Modelo:** LightGBM con normalización por rango con signo + retrovisores + **FE histórico**
  (tendencia y promedio de 3 meses), semillerío de 40 semillas.
- **Hiperparámetros (de la BO):** `num_leaves = 256`, `min_sum_hessian_in_leaf = 0.0299943`,
  `num_iterations = 1439` (ver `optimizacion_bayesiana/`).
- **Corte elegido:** 11000 envíos (justificación más abajo).

> Agregar el **FE histórico** (tendencia + promedio de 3 meses sobre los rankings) subió el
> leaderboard público de **104.50** (misma receta sin FE histórico, corte 11000) a **107.44**.

---

## Estructura del repositorio

```
competencia_01/
├── README.md                                 # este archivo
├── run_rank_prestamos_junbo_hist.R           # script ÚNICO end-to-end (FE + FE histórico + BO + 40 semillas + submits)
├── optimizacion_bayesiana/
│   ├── README.md                             # cómo saltar la BO y cómo se generaron los hiper
│   ├── bo_mejor_config.csv                   # los hiperparámetros elegidos (para saltar la BO)
│   ├── bo_evaluaciones.csv                   # la optimización bayesiana que los produjo
│   └── junbo_hist.log                        # log completo de la corrida (procedencia)
├── prediccion_final/
│   ├── README.md                             # qué es el archivo entregado + verificación por hash
│   ├── lovrich_ensamble_corte11000.csv       # el archivo EXACTO entregado al bot
│   └── SHA256.txt                            # hash del archivo de entrega
└── data/
    └── README.md                             # dónde poner el dataset crudo (no se versiona)
```

---

## Cómo replicar la predicción final

### Requisitos
- R (probado en 4.6.1) con `data.table`, `lightgbm` (4.7.0) y `Rcpp` (para el FE histórico en C++).
  El FE histórico compila una función C++ con `Rcpp::cppFunction`, así que hace falta un compilador
  de C++ (Rtools en Windows, `build-essential` en Linux).
- Para la optimización bayesiana: `DiceKriging`, `mlrMBO`, `smoof`, `lhs`, `ParamHelpers`
  (el script los instala solo si faltan).
- El dataset crudo de la competencia: `competencia_01_crudo.csv` (ver `data/README.md`).

### Opción A: reproducción completa (corre la BO desde cero)
Genera la predicción de punta a punta, **incluyendo** la optimización bayesiana
(~125 min de BO + feature engineering + 40 modelos). Es 100% autocontenido.

```bash
DMEYF_CRUDO=data/competencia_01_crudo.csv \
DMEYF_EXP=salida_run \
GCS_BUCKET= \
NTHREAD=8 NSEEDS=40 \
Rscript run_rank_prestamos_junbo_hist.R
```

- `GCS_BUCKET=` (vacío) desactiva la subida opcional a Google Cloud; **no hace falta ningún
  bucket para replicar.**
- La entrega queda en `salida_run/entrega/corte_11000/lovrich_ensamble.csv`.

### Opción B: saltar la BO usando los hiperparámetros ya optimizados
Si no se quiere volver a correr la optimización bayesiana (~2 h), se le entrega al script
la configuración ya encontrada. Ver instrucciones detalladas en
[`optimizacion_bayesiana/README.md`](optimizacion_bayesiana/README.md). En resumen:

```bash
mkdir -p salida_run
cp optimizacion_bayesiana/bo_mejor_config.csv salida_run/bo_mejor_config.csv
DMEYF_CRUDO=data/competencia_01_crudo.csv DMEYF_EXP=salida_run GCS_BUCKET= \
  NTHREAD=8 NSEEDS=40 Rscript run_rank_prestamos_junbo_hist.R
```

El script detecta `bo_mejor_config.csv` en la carpeta de salida y **no repite la BO**
(`bo_mejor_config.csv ya existe: no repito la BO`). El resto del flujo es idéntico.

> La configuración de la Opción B **es la misma** que elige la Opción A: la BO es
> determinista (misma semilla primigenia 100193). La Opción B solo existe para ahorrar tiempo.
> Siguiendo la indicación de la cátedra, se incluye además la optimización que dio origen a
> esos hiperparámetros (`bo_evaluaciones.csv` + `junbo_hist.log`).

---

## El pipeline (de punta a punta)

Todo ocurre en un único script R, reproducible y autocontenido:

1. **Lectura del crudo** y controles (meses presentes, sin columnas de texto).
2. **`clase_ternaria`** por cliente y mes calendario (BAJA+1 / BAJA+2 / CONTINUA). Si el crudo
   ya la trae, se usa; si no, se genera.
3. **Data Quality (dq1):** `ccajas_depositos` se pone en NA solo en 202105 (mes roto), antes
   de cualquier transformación.
4. **Normalización por rango con signo**, por variable y por mes (columnas `_rank`):
   faltante → faltante, cero → cero, positivos → (0,1], negativos → [-1,0).
5. **Retrovisores 1 y 2 y sus diferencias** calculados **sobre las columnas normalizadas**
   (lag1/delta1/lag2/delta2, calendario-exactos: el mismo cliente k meses atrás).
6. **FE histórico sobre los rankings:** por cada variable, la **tendencia** (pendiente por
   mínimos cuadrados de los últimos 3 meses del cliente, `_rank_tend3`) y el **promedio** de los
   últimos 3 meses (`_rank_avg3`). Se calcula con una función C++ (núcleo de la cátedra) sobre una
   ventana posicional por cliente. Cada variable deja así **7 columnas**.
7. **Se descartan los valores crudos**: el árbol solo ve columnas transformadas
   (7 por variable → **1064 columnas**).
8. **Optimización bayesiana** (mlrMBO, Kriging + Expected Improvement, métrica AUC, sin CV):
   entrena 202103+04 → valida 202106, **sin undersampling**, **sin los 2 préstamos personales**
   (1050 columnas). Busca `num_iterations`, `num_leaves`, `min_sum_hessian_in_leaf`.
9. **Foto de junio** (diagnóstico): modelo 202103+04 → predice 202106 (con las 1050 columnas),
   curva de ganancia por corte para mirar la forma.
10. **Entrenamiento final** (202103-06, sin undersampling, **con los préstamos reincorporados**
    ya transformados → 1064 columnas): **40 modelos** con los mismos hiperparámetros, cambiando
    solo la semilla (primigenia 100193).
11. **Ensamble** = promedio simple de probabilidades por cliente.
12. **Barrido de cortes** (9000–13000, paso 500) → un archivo de envío por corte.
13. **Validación de formato** de todos los archivos (8000–13000 filas, enteros, sin
    duplicados, solo clientes de 202108).

**Hiperparámetros fijos** (no entran a la BO): `objective=binary`, `metric=auc`,
`max_bin=31`, `min_data_in_leaf=0`, `feature_fraction=0.5`, `feature_fraction_bynode=0.2`,
`learning_rate=0.005`, `deterministic=TRUE`.

---

## Resumen de decisiones

| Decisión | Elección |
|---|---|
| **Datos** | `competencia_01_crudo.csv` → `clase_ternaria` (BAJA+1 / BAJA+2 / CONTINUA, por cliente y mes). Se genera en el script si el crudo no la trae. |
| **Variables** | las 152 base normalizadas por rango con signo + `lag1`, `delta1`, `lag2`, `delta2`, `rank_tend3`, `rank_avg3` de todas (7 por variable → 1064 columnas). La BO usa 1050 (sin las 2 de préstamos). `ccajas_depositos` → NA en 202105 (dq1). |
| **FE histórico** | sobre los rankings: tendencia (pendiente mínimos cuadrados, 3 meses) y promedio (3 meses), por cliente, con función C++ (núcleo de la cátedra). |
| **Fuera del modelo** | `numero_de_cliente`, `foto_mes`, `clase_ternaria`. `cprestamos_personales` y `mprestamos_personales` quedan fuera de la BO y se reincorporan (ya transformados) en el entrenamiento final. |
| **Clase** | `clase01` = 1 si `BAJA+1` ∪ `BAJA+2`, 0 si `CONTINUA`. Sin pesos ni clase artificial. |
| **Hiperparámetros** | fijos: `max_bin` 31, `min_data_in_leaf` 0, `feature_fraction` 0.5, `feature_fraction_bynode` 0.2, `learning_rate` 0.005, `deterministic`. De la BO: **256 hojas**, `min_sum_hessian_in_leaf` **0.0299943**, **1439 árboles**. |
| **Entrenamiento** | 202103-202106, 654.066 filas, sin undersampling. |
| **Semillas** | 40, derivadas de la primigenia 100193 (criba de primos 1e5-1e6, `set.seed`, `sample`). |
| **Ensamble** | promedio simple de **probabilidades** de las 40 semillas. |
| **Corte** | **11000** (por la curva de ganancia en junio; público consistente: 107.44). |

> **Nota sobre la BO:** eligió `num_leaves = 256`, que es el **tope del rango** de búsqueda
> (`hojas_max = 256`), y un hessiano (`0.0299943`) muy cerca de su tope (`0.03`). O sea, la
> búsqueda quedó pegada al borde del espacio: el óptimo podría estar más allá del rango. Se dejó
> así para esta entrega; ampliar el rango de hojas sería el próximo paso.

---

## Por qué corte 11000

El corte se eligió mirando la curva de ganancia en junio (mes 202106, etiquetado, validación
propia del modelo), en la corrida final de 40 semillas. La ganancia es la del bot (BAJA+2 suma
1.072.500; cualquier otro envío resta 27.500), en millones:

| Corte | Ganancia media ± sd entre semillas | Ganancia del ensamble |
|---|---|---|
| 9000  | 445.17 ± 3.95 | 462.00 |
| 9500  | 449.68 ± 5.16 | 459.25 |
| 10000 | 453.20 ± 5.31 | 456.50 |
| 10500 | 453.64 ± 5.27 | 455.95 |
| 11000 | **454.96 ± 3.89** | 454.30 |
| 11500 | 454.30 ± 4.41 | 450.45 |
| 12000 | 454.63 ± 5.19 | 452.10 |
| 12500 | 453.97 ± 3.23 | 452.65 |
| 13000 | 453.53 ± 4.73 | 456.50 |

La media entre semillas (más estable que el ensamble de una sola realización) **tiene su máximo
en 11000** (454.96).

El leaderboard público coincide. El promedio de los envíos por-semilla (20 archivos) da la
variabilidad entre semillas; el ensamble de las 40 semillas es un único archivo:

| Corte | Público: por-semilla (media ± sd, 20 envíos) | Público: ensamble |
|---|---|---|
| 9500  | 99.83 ± 2.86 | n/d |
| 10000 | 102.66 ± 1.94 | n/d |
| 10500 | 103.64 ± 2.64 | 104.42 |
| 11000 | **104.48 ± 2.84** | **107.44** |

11000 es el mejor tanto en la media por-semilla como en el ensamble. Las dos señales (junio y
público) apuntan a 11000, así que ese es el corte de la entrega.

---

## Experimentos que se probaron y NO mejoraron la predicción

Apartado de cosas que exploré y **descarté** porque no mejoraban (o empeoraban) el resultado:

1. **Manejo alternativo de NAs (`keepna`).** Leaderboard **101.27**. Peor.
2. **Rangos angostos de la BO** (`num_leaves ≤ 128`, `hessiano ≥ 0.0005`). Leaderboard
   **103.12** vs **104.66** con rangos amplios (hasta 256 hojas, hessiano desde 0.0001). Los
   rangos amplios dejan a la BO alcanzar árboles más profundos, que es donde está la ganancia.
3. **Flags binarios "es cero" por variable (`_zero`, 140 columnas intra-mes).** El modelo se
   volvió más complejo (217 hojas, 900 columnas) pero la ganancia en junio quedó prácticamente
   igual (~460M contra ~457M, una diferencia menor al desvío entre semillas de ~4-5 M) y no mostró
   mejora clara. No se adoptó: más complejidad y más riesgo de sobreajuste sin beneficio.
4. **Hiperparámetros fijos salteando la Bayesiana**.
   Se descartó en favor de dejar que la BO busque (es parte de la receta).
5. **Más semillas del mismo modelo (50, 80).** Rendimiento decreciente marcado: a 40 semillas el
   ensamble ya es estable. Clonar el mismo modelo con más semillas **no agrega diversidad**, solo
   reduce varianza marginalmente; no justifica el tiempo.
6. **Elegir el corte por el pico del leaderboard público.** El leaderboard público se mueve entre
   cortes vecinos más de lo que distingue a un corte del otro: en una corrida el corte 10500 dio
   105.71 con 10 semillas y 103.70 con 40 semillas, una diferencia comparable al desvío entre
   semillas del semillerío. Por eso el corte final se decidió por la curva de ganancia en junio,
   corroborada por el público, no por un único pico público.
