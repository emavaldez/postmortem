# 4 — Hiperparámetros y modelo final

Acá está el entrenamiento, en dos partes que van en orden:

| Carpeta | Qué hice |
|---|---|
| [`02_q0_ccajas_na/`](experimentos_20261007_post_c3/02_q0_ccajas_na/) y [`04_b1_variables_rotas/`](experimentos_20261007_post_c3/04_b1_variables_rotas/) | Controles de calidad de datos: reproduzco exacto el modelo C3 y pruebo si marcar como faltante una variable rota en un mes mejora algo. SUPERFINAL los necesita para elegir con qué versión del dataset arranca. |
| [`05_superfinal100/`](experimentos_20261007_post_c3/05_superfinal100/) | **SUPERFINAL:** una sola corrida con reglas fijadas de antemano que elige representación, pesos por mes, hiperparámetros (**Optuna**) y corte. De acá salen los parámetros del modelo final. |
| [`13_cluster_aware_reweighting/`](experimentos_20261007_post_c3/13_cluster_aware_reweighting/) | **Modelo final (CLAW2):** mismo modelo que SUPERFINAL, pero repartiendo el peso de los BAJA+2 entre los cinco grupos del paso 3. Escribe el CSV de la entrega. |

Las carpetas conservan sus nombres originales porque los scripts se llaman entre sí por esos nombres (`13_…` importa de `05_…`, y `05_…` ejecuta `04_…`).

## Dónde espera cada cosa

Los scripts leen y escriben en carpetas fijas de `$HOME`:

```
$HOME/
├── c1m1femasiva03/datos/competencia_01.parquet          <- paso 1
├── c1m1femasiva03_s3/
│   ├── paquete_c1/                                      <- paso 2 (copia de 2_variables/)
│   ├── resultados_s1/fe_bank_dev/                       <- paso 2
│   └── resultados_s3/                                   <- paso 2
├── z501/reference_labels.csv                            <- paso 3
├── c1q0ccajas06/           c1b1rotas01/                 <- salidas de Q0 y B1
├── c1superfinal100v2/                                   <- salida de SUPERFINAL
└── c1clusteraware01/stage4_august/delivery/             <- CSV final
```

Máquina: Linux con 56 GB de RAM y 6 hilos.

En la corrida original cada etapa se respaldaba a un bucket de Cloud Storage con `gcloud`. Para publicar, el nombre del bucket se reemplazó por un placeholder y esas copias se saltean (función `_gcs` al inicio de cada script); es el único cambio respecto del código que corrió y no toca ningún cálculo. Si se quiere respaldar, basta poner un bucket propio en la constante `REMOTE` de cada script.

## Comandos

```bash
R=4_modelo/experimentos_20261007_post_c3

# Controles de calidad (Q0 reproduce C3 con 20 semillas; B1 lo lanza SUPERFINAL solo)
python $R/02_q0_ccajas_na/run_q0.py --preflight
python $R/02_q0_ccajas_na/run_q0.py --prepare
python $R/02_q0_ccajas_na/run_q0.py --canary
python $R/02_q0_ccajas_na/run_q0.py --execute

# SUPERFINAL: calidad -> representación -> pesos por mes -> Optuna -> 20 semillas -> producción
python $R/05_superfinal100/run_superfinal100_v2_safe.py --home $HOME --all
python $R/05_superfinal100/auditar_superfinal100_v2.py --home $HOME     # obligatorio: escribe AUDITORIA_FINAL.json, que el modelo final exige

# Modelo final (CLAW2_REPLICA=1: acepta la corrida de SUPERFINAL recién hecha; ver nota)
export CLAW2_REPLICA=1
python $R/13_cluster_aware_reweighting/run_cluster_aware.py \
  --home $HOME --labels-cluster $HOME/z501/reference_labels.csv --phase all
python $R/13_cluster_aware_reweighting/audit_cluster_aware.py --home $HOME   # debe decir AUDIT_OK
```

Cada script primero verifica hashes, identidades y conteos de la etapa anterior y se detiene si algo no coincide. Nada hace submit automático.

**Nota sobre `CLAW2_REPLICA=1`.** Cada corrida de SUPERFINAL lleva una huella (un hash que incluye, entre otras cosas, el tiempo que tardó en generar las variables), y el modelo final tiene grabada en `plan.json` la huella de la corrida original. Una corrida nueva de SUPERFINAL tiene otra huella, así que sin esa variable de entorno el modelo final se detiene en su preflight. Con `CLAW2_REPLICA=1` toma la huella de la corrida presente en `$HOME`, que igual debe haber pasado su auditoría. El resto de los controles no cambia. El archivo generado tendrá otro prefijo (sale de esa huella), pero el contenido se compara con el verificador del paso 5.

Tests sin datos (corren en GitHub Actions):

```bash
(cd $R/13_cluster_aware_reweighting && python test_cluster_aware.py)
(cd $R/05_superfinal100 && python test_superfinal100_v2.py)
```
