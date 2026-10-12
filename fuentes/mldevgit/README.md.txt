# Competencia 01 — FINAL Z636 C25 FULL762

**FINAL = Z636 C25 FULL762.** Public gain: **98.6150 M**. Submission ID: **1560-1791746981180245**. Resultado informado por el autor; no participa en el pipeline ni en la selección metodológica.

Entrega autocontenida en código. Requiere el dataset original, que **no se incluye**. Tampoco se incluyen parquet, scores, modelos ni CSV final. No realiza uploads.

## Entrada y entorno

Obtener el CSV por el canal autorizado y colocarlo en `data/competencia_01.csv` dentro de esta carpeta. No publicarlo. SHA256 de la fuente:

```text
53fd6265cfa565224fa4370e1fabe72d343a5c76540eb769758686a194bb5dfd
```

Requiere Python **3.12.0**, preferentemente Windows x64, y las versiones exactas de `requirements.txt`. Desde esta carpeta, en PowerShell:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -B src/01_feature_engineering.py
.venv/Scripts/python.exe -B src/02_train_lightgbm.py
.venv/Scripts/python.exe -B src/03_train_catboost.py
.venv/Scripts/python.exe -B src/04_build_final_c25.py
.venv/Scripts/python.exe -B src/05_verify_submission.py
```

Ejecutar los cinco pasos exactamente en ese orden. El primero requiere una carpeta `output/` nueva. Ningún paso sobrescribe salidas; ante un error, detenerse e investigar sin cambiar parámetros. Todos aceptan `--output-dir`; usar la misma ruta en todos los pasos. El primer paso admite `--input` para otra ubicación del CSV. El verificador admite `--submission` y `--features` si se necesitan rutas explícitas. Los valores predeterminados se resuelven respecto de esta carpeta, sin rutas personales ni dependencias del directorio de trabajo.

## Arquitectura congelada

**LightGBM utiliza exclusivamente FULL762. CatBoost utiliza exclusivamente FULL457.** Ambos entrenan cinco seeds desde cero en una reproducción completa; el código no reutiliza modelos o scores históricos.

FULL457, preservando el orden de las 152 variables originales en el CSV:

1. 152 originales.
2. 152 `<feature>_lag1`.
3. 152 `<feature>_delta_lag1`.
4. `lag1_disponible`.

Lag1 corresponde al mismo cliente exactamente un mes calendario antes. FULL762 conserva ese prefijo y agrega 152 `<feature>_lag2`, 152 `<feature>_delta_lag2` y `lag2_disponible`. Lag2 corresponde al mismo cliente exactamente **dos meses calendario antes**, incluyendo cambios de año; no es un shift por filas. Un registro de hace dos meses puede existir aunque falte el mes intermedio. Cada delta es actual menos lag, sin imputación. Los indicadores miden existencia del registro, aunque sus variables sean NaN.

Hashes SHA256 de nombres unidos con `\n` en UTF-8, sin salto final:

| Features | SHA256 |
|---|---|
| FULL457 | `c3578882fcf1adf79df9c20c472864719672522fa2ee9283d4a9b1c0fe080c12` |
| FULL762 | `1e9747955f214a8ddcb405af0e3a71d4a516f1818bf829c0d6c14ca0f934e8f6` |

La ingeniería genera dos parquet independientes, con 983061 filas cada uno, conserva el orden del CSV y relee sus valores antes de aceptarlos. En ambos modelos el train se ordena estable por `numero_de_cliente ASC, foto_mes ASC`: abril+mayo+junio de 2021, 491166 filas, pesos 0.75/1/1 y suma 450345. No se entrena con July. August tiene 164647 IDs únicos y se proyecta sin target para entrenamiento/predicción y verificación de IDs. La ingeniería transporta `clase_ternaria`; sólo se auditan las etiquetas de los meses de entrenamiento.

Seeds, en orden: **290497, 100003, 200003, 300007, 400009**. Hiperparámetros exactos en `src/common.py`: LightGBM multiclass, 1200 iteraciones; CatBoost MultiClass CPU, 1000 iteraciones, FULL457 y sin class weights. No hay tuning, early stopping ni cambios de pesos. LightGBM usa matrices float64 por lotes con respaldo temporal en disco, sin reducir precisión; CatBoost conserva las columnas FULL457 y sus tipos numéricos.

Se extrae P(BAJA+2) usando `classes_`. Cada familia promedia las cinco probabilidades antes de rankear todos los clientes, score DESC e ID ASC. Con rank desde 1:

```text
u = (M-rank)/(M-1)
C25 = 0.75*u_lgbm_full762 + 0.25*u_catboost_full457
```

C25 se ordena directamente por ese score DESC e ID ASC, sin otra normalización. Se escriben 12000 IDs, una columna, sin header/index, UTF-8 sin BOM y LF incluyendo el final.

## Selección metodológica

El peso 75/25 se seleccionó históricamente en May/June antes de transferir el modelo a August. Lag2 se evaluó sin utilizar August: en June, LightGBM FULL762 mejoró de 669 a 686 TP (**+17**) y mejoraron **5/5 seeds**. Dentro de C25, sustituir sólo LightGBM manteniendo CatBoost FULL457 produjo 688 a 695 TP (**+7**), con **5/5 seeds** positivas; May permaneció en 520. July no proporcionaba target completo utilizable y no se imputaron etiquetas.

La transferencia estructural June→August se auditó antes de submission. No se utilizaron labels August para seleccionar modelo, features, peso ni hiperparámetros. El resultado Public indicado arriba es posterior e informativo.

## Salida y estado de reproducción

Salida final: `output/submit_z636_c25_full762_n12000.csv`. SHA256 obligatorio:

```text
00534f4c23bb87c5e0962ee615a0f81740cf1e2f3e64232c7af5bc83aae697a0
```

El constructor y el verificador terminan con error si el hash difiere. `output/` contiene los dos parquet, auditoría de features, cinco scores y ranking ensemble por familia, `ranking_c25.parquet`, `final_audit.json` y el CSV. Todo queda ignorado por Git.

**Reproducción integral Z636: PASS.**
Se ejecutó el pipeline completo desde cero, incluyendo generación de features, entrenamiento de cinco seeds LightGBM FULL762, cinco seeds CatBoost FULL457, construcción del ensamble C25 y verificación del CSV final. Tiempo total: 3 h 04 min 26 s. Se verificaron 12.000 IDs únicos, sin encabezado, correspondientes a agosto, y el SHA256 final 00534f4c23bb87c5e0962ee615a0f81740cf1e2f3e64232c7af5bc83aae697a0.
El estado y el alcance de las verificaciones están en `REPRODUCCION.md` y `AUDITORIA_ENTREGA.md`. La generación de referencia FULL762 observada tardó **1 h 57 min 50 s**, reutilizando CatBoost; ese tiempo no es una medición end-to-end de este paquete. Reservar varias horas, al menos 16 GB RAM y espacio para ambos parquet y unos 4 GB adicionales de matrices temporales. Los tiempos dependen de hardware/carga. Un SHA de parquet distinto por serialización no determina identidad predictiva; el CSV sí debe coincidir exactamente.
