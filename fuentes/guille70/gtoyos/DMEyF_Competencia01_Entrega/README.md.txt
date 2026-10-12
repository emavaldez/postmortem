# DMEyF 2026 - Competencia 1 - Entrega final

Predicción de BAJA+2 para agosto de 2026 (foto_mes 202108).

**Entrega final (el archivo que se subió a zulip):** promedio de 20 semillas, LightGBM con FE04b y los hiperparámetros del trial 25 de la optimización, entrenado con junio (target fusionado BAJA+1 + BAJA+2) y con corte en **N = 12.000** clientes.

Archivo: `data/out/Sbm04ajaFE04bOptN12000_sem_final.csv`

## Estructura

```
DMEyF_Competencia01_Entrega/
├── README.md
├── scripts/
│   ├── DMEyF_Competencia01_EntregaFinal.ipynb   <- notebook final: genera el archivo entregado
│   └── semillas.py                              <- lista de semillas (SEMILLAS)
└── data/
    ├── fe04_b_con_delta1.txt                    <- columnas usadas por el modelo (602)
    ├── competencia_01_fe03.parquet              <- NO está en el repo (1,86 GB): ver abajo
    ├── databases/
    │   └── cpt2_optim_lgbm_Step1.db             <- optimización bayesiana (Optuna, 50 trials)
    └── out/
        └── Sbm04ajaFE04bOptN12000_sem_final.csv <- archivo entregado
```

## Cómo replicar la entrega

### 1. Descargar `competencia_01_fe03.parquet`

El parquet pesa 1,86 GB y no entra en GitHub. Descargarlo y dejarlo en `data/competencia_01_fe03.parquet`:

**https://drive.google.com/file/d/1iHL2qZQgRHsGoHBrwUz-ELsM2gTyh5Zh/view?usp=sharing**

(Google Drive puede mostrar un aviso de "no se puede analizar en busca de virus" por el tamaño; se puede descargar igual.)

Contiene el dataset de la competencia (1.614 columnas) con el feature engineering y los tipos ya corregidos.

### 2. Lista de columnas

`data/fe04_b_con_delta1.txt` (una columna por línea, 602) se construyó a partir de las columnas del parquet. Incluye:

- las 155 columnas originales (con `numero_de_cliente`, `foto_mes` y `clase_ternaria`);
- 16 variables intra mes creadas a mano;
- las variables intra mes de ranking, `pr_` (percent_rank) y `nt10_` (ntile 10), 140 de cada una;
- las 151 variables históricas de orden 1 (`delta_1_`).

Se excluyen:

- otras históricas (`delta_2_`, `delta_3_`, `avg_3_`, `stddev_3_`, `min_3_`, `max_3_`, `ratio_avg3_`);
- 10 derivadas de `ccajas_depositos`, que está rota en 202105 (todos sus valores son cero).

Total: 155 + 16 + 140 + 140 + 151 = 602. A `ccajas_depositos` se le asigna  NA para 202105 al cargar los datos (lo hace la función `cargar` de la notebook).

### 3. Ejecutar la notebook

Abrir `scripts/DMEyF_Competencia01_EntregaFinal.ipynb` (la carpeta de trabajo tiene que ser `scripts/`) y ejecutar todas las celdas. Tarda unos 20-25 minutos (entrena 20 modelos). La notebook:

1. Carga los meses 202104, 202106 y 202108 con las columnas de `fe04_b_con_delta1.txt`.
2. Lee la optimización guardada en `data/databases/cpt2_optim_lgbm_Step1.db` (50 trials ya completos; no corre trials nuevos).
3. Toma los hiperparámetros y el `best_iter` del **trial 25**.
4. Entrena con junio (target fusionado BAJA+1 + BAJA+2) 20 modelos, uno por semilla (`semillas[20:40]`), y predice agosto.
5. Promedia las 20 probabilidades por cliente y toma los **12.000** clientes como punto de corte.
6. Guarda el archivo en `data/out/submit04ajaFE04bOptN12000Sem/Sbm04ajaFE04bOptN12000_sem.csv`.
7. Lo compara con el archivo enviado (`data/out/Sbm04ajaFE04bOptN12000_sem_final.csv`): deben coincidir los 12.000 IDs y el orden.

Resultado de la corrida de verificación: `IDs en común: 12000` y `Archivos idénticos (mismo orden): True`.

## Optimización de hiperparámetros

- Estudio de Optuna `cpt2_step1_b2_lgbm_sss_3000_con_FE04-b`, guardado en `data/databases/cpt2_optim_lgbm_Step1.db`.
- Se optimizó con **abril** como mes de entrenamiento, con target BAJA+2 solo, maximizando el AUC en validación cruzada (`StratifiedShuffleSplit`, 5 splits, 30% de test) con FE04b.
- Parámetros fijos: `max_bin = 31`, `min_data_in_leaf = 0`, `feature_pre_filter = False`. Parámetros optimizados: `num_leaves`, `min_sum_hessian_in_leaf`, `learning_rate`, `feature_fraction`, `feature_fraction_bynode`, `bagging_fraction`, `bagging_freq`. El número de árboles (`best_iter`) sale de la validación cruzada de cada trial.
- La optimización **no es reproducible exactamente** (el sampler de Optuna no tiene semilla fija). Por eso se incluye el `.db`: la notebook final lee de ahí el trial 25 (la notebook imprime sus hiperparámetros y su `best_iter`).

## Cómo se llegó al trial 25 y al corte N = 12.000

- **Trial 25:** se validaron los 5 mejores trials por AUC, cada uno con 20 semillas, entrenados con abril y medidos en junio con la ganancia real de BAJA+2. El trial 25 quedó entre los candidatos con ganancia más alta y se eligió para la configuración final.
- **Entrenamiento final:** con junio y el target fusionado BAJA+1 + BAJA+2. La ganancia siempre se midió con BAJA+2 real (+1.072.500 si acierta, −27.500 si no).
- **Corte N:** el barrido del corte se definió a partir del mejor corte en junio, pasado a porcentaje de clientes y trasladado a agosto. El valor final de **12.000** (≈ 7,3% de los clientes de agosto) se eligió con el puntaje público del bot, probando N entre 9.000 y 16.037. El puntaje público tiene ruido (≈ 25% de los clientes de agosto), así que se tomó una zona alta (10.000 a 13.122) y no un pico aislado. Como se eligió el máximo del público, ese puntaje puede estar algo inflado respecto del privado.

## Reproducibilidad

- Los modelos usan semillas de `scripts/semillas.py`. Los 20 modelos finales usan `semillas[20:40]`.
- La notebook usa `lgb_threads = 10`. LightGBM no garantiza resultados idénticos con otra cantidad de threads; en la máquina de desarrollo se obtuvo exactamente el mismo archivo. En otra máquina podría moverse algún cliente del borde del corte. El archivo entregado está en `data/out/Sbm04ajaFE04bOptN12000_sem_final.csv`.
- No se incluyen los modelos entrenados: se regeneran al ejecutar la notebook.
- Entorno: Python 3.11.16. Librerías principales y versiones: `lightgbm` 4.7.0, `optuna` 5.0.0, `duckdb` 1.0.0, `pandas` 2.3.3, `numpy` 2.4.6, `scikit-learn` 1.9.1, `plotly` 7.0.0, `matplotlib` 3.11.1.
