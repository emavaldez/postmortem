# Primera Competencia DMEyF 2026 — Clara M. Rodríguez

<p align="justify"><b>Entrega final:</b> <code>C1CLAW2C065771C9ENS13500.csv</code> (13.500 <code>numero_de_cliente</code> de 202108, una columna, sin encabezado). Ganancia pública del bot: <b>101,0900 M ARS</b> (Submission ID <code>1586-1791569183206183</code>).</p>

## Cómo armé mi predicción final

<p align="justify">Es un <b>ensamble por promedio de 20 modelos LightGBM</b>. Todos tienen las mismas variables y los mismos hiperparámetros; solo cambia la semilla. Lo distinto del modelo es <b>cómo pesa a los clientes que se van</b> mientras entrena.</p>

| Paso | Carpeta | Qué hace |
|---|---|---|
| 1 | [`1_dataset/`](1_dataset/) | Del CSV de la cátedra arma la clase (`clase_ternaria`) y guarda un Parquet |
| 2 | [`2_variables/`](2_variables/) | Construye las variables: a las 152 originales les agrega historia y ratios de tarjetas → **2.062 variables** |
| 3 | [`3_grupos_baja2/`](3_grupos_baja2/) | Separa a los clientes BAJA+2 en **cinco grupos** según cómo se van del banco |
| 4 | [`4_modelo/`](4_modelo/) | Elige hiperparámetros con **Optuna** (SUPERFINAL) y entrena el modelo final (**CLAW2**), que reparte el peso de los BAJA+2 entre esos cinco grupos → archivo final |
| 5 | [`5_prediccion_final/`](5_prediccion_final/) | Qué archivo se envió, con qué parámetros, y cómo verificarlo |

<p align="justify">La probabilidad final de cada cliente es el promedio simple de las probabilidades de los 20 modelos. Se ordenan de mayor a menor (empates por <code>numero_de_cliente</code>) y se envían los primeros 13.500.</p>

### Detalle del modelo

- **Clase:** BAJA+2 contra el resto (BAJA+1 y CONTINUA juntos).
- **Meses:** entrenamiento final 202103–202106, predicción 202108. 202107 no tiene clase; solo aporta historia para los lags de agosto.
- **Variables (2.062):** las 152 originales + 1.910 derivadas: historia de cada variable (lags, deltas, transiciones) y ratios de tarjetas. Es el bloque que llamo **C3**.
- **Ventana:** los cuatro meses de entrenamiento con el mismo peso.
- **Hiperparámetros:** los que eligió Optuna en SUPERFINAL (20 trials, `TPESampler(seed=17)`, entrenando marzo y midiendo ganancia en mayo). El modelo final no volvió a optimizar.

| num_iterations | learning_rate | num_leaves | min_data_in_leaf | feature_fraction | bagging_fraction | max_bin | lambda_l1 | lambda_l2 |
|---|---|---|---|---|---|---|---|---|
| 361 | 0,015387 | 79 | 551 | 0,686638 | 0,652536 | 63 | 5,72e-06 | 0,013649 |

<p align="justify">Con todos los decimales: <a href="5_prediccion_final/MANIFIESTO_CLAW2_TRANSCRIPTO.json"><code>5_prediccion_final/MANIFIESTO_CLAW2_TRANSCRIPTO.json</code></a>. Los 20 trials de Optuna están en <a href="4_modelo/experimentos_20261007_post_c3/05_superfinal100/trials.csv"><code>4_modelo/.../05_superfinal100/trials.csv</code></a>.</p>

- **Semillas (20):** 17, 101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203, 1304, 1405, 1506, 1607, 1708, 1809, 1910.
- **Pesos de los BAJA+2:** cada BAJA+2 de marzo a junio pertenece a uno de cinco grupos. Los grupos chicos pesan más y los grandes menos (tope entre 0,5 y 4), y después se reescala para que **el peso total de los BAJA+2 no cambie** (4.067). No cambia el balance entre los que se van y los que se quedan; solo cambia a cuáles BAJA+2 mira más el modelo.

| Grupo | BAJA+2 marzo–junio | Peso de cada uno |
|---|---:|---:|
| C1 | 1.280 | 0,635 |
| C2 | 1.136 | 0,716 |
| C3 | 857 | 0,949 |
| C4 | 579 | 1,405 |
| C5 | 215 | 3,783 |

<p align="justify">Los grupos <b>no son una variable del modelo</b> y no se usan para predecir agosto: solo definen el peso de los BAJA+2 de entrenamiento.</p>

### Por qué esos pesos

<p align="justify">Cuando miré a quién se le escapaba a SUPERFINAL en junio, vi que no fallaba parejo. De los 1.098 BAJA+2 de junio agarraba 697 y perdía 401, y <b>309 de esos 401 eran de dos grupos (C2 y C5)</b>:</p>

| Grupo | BAJA+2 en junio | Detectados | % detectado |
|---|---:|---:|---:|
| C1 | 324 | 238 | 73,5% |
| C2 | 334 | 115 | 34,4% |
| C3 | 185 | 181 | 97,8% |
| C4 | 105 | 103 | 98,1% |
| C5 | 150 | 60 | 40,0% |

<p align="justify">El modelo aprendía bien las formas "fáciles" de irse y casi ignoraba las otras. Repartiendo el peso, en junio pasó de <b>697 a 718 BAJA+2 detectados</b> con los mismos 13.500 envíos (+23,10 M ARS), y mejoró en las 20 semillas.</p>

## Cómo replicar (en orden)

<p align="justify">Todo es <b>Python 3.12</b>; la corrida original fue en una máquina Linux con 56 GB de RAM. En el repo está el código y nada más: el dataset (<code>competencia_01_crudo.csv</code> de la cátedra), las variables, los grupos, los 20 modelos y el archivo final se generan corriendo los pasos en orden. Cada carpeta tiene su README con el comando exacto; acá va el resumen.</p>

```bash
git clone https://github.com/ClariRZ/Primera-compentencia.git
cd Primera-compentencia
python3.12 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.lock -r requirements-z501.txt
```

<p align="justify">Los scripts leen y escriben en carpetas fijas dentro de <code>$HOME</code>; el mapa de cuál es cada una está en <a href="4_modelo/README.md"><code>4_modelo/README.md</code></a>.</p>

1. **Dataset** → `1_dataset/preparar_competencia.py` deja `competencia_01.parquet`.
2. **Variables** → `2_variables/.../run_screening.py` construye el banco de variables y `run_s3_confirm_c3.py` deja el bloque C3.
3. **Grupos** → `3_grupos_baja2/validar_clusters_estabilidad.py` escribe `reference_labels.csv` (4.067 clientes y su grupo).
4. **Modelo** → dentro de `4_modelo/`: controles de calidad (`run_q0.py`), SUPERFINAL con Optuna (`run_superfinal100_v2_safe.py --all`) y el modelo final (`run_cluster_aware.py --phase all`), que escribe:

```
$HOME/c1clusteraware01/stage4_august/delivery/C1CLAW2C065771C9ENS13500.csv   <- la entrega final
```

5. **Verificación** → `5_prediccion_final/verificar_csv_final.py` compara filas, formato y SHA-256 contra el archivo enviado.

<p align="justify">Al reentrenar 20 modelos LightGBM en otra máquina puede haber diferencias ínfimas en las probabilidades y, como mucho, un puñado de clientes distintos cerca del corte 13.500. El nombre del archivo lo arma el script: <code>C1CLAW</code> + los primeros 10 caracteres de la identidad de la corrida + <code>ENS13500</code>. El código es el que corrió; el único cambio es que los respaldos a Cloud Storage se saltean si no se configura un bucket.</p>

## Lo que probé en el camino

<p align="justify">Fueron cuatro etapas. "Bot" es la ganancia <b>pública</b> en millones de ARS; "interno" es la diferencia de ganancia en junio contra el modelo que venía usando, entrenando con marzo y abril.</p>

### 1. ¿Qué clase y qué variables originales? (corte 11.000)

| Qué probé | Bot | ¿Me lo quedé? | Por qué |
|---|---:|---|---|
| Ambas bajas contra CONTINUA, sin las seis variables de préstamos | 87,16 | Punto de partida | Mi primer modelo. Promediar sus 20 semillas dio 87,37. |
| Lo mismo + resúmenes de fechas de Visa y Master | 86,96 | No | No agregó nada. |
| BAJA+2 contra CONTINUA, sacando los BAJA+1 del entrenamiento | 87,56 | No | Casi igual que el primero. |
| Ambas bajas, con las variables de préstamos | 89,32 | — | Los préstamos ayudaban. |
| Montos de préstamos sí, cantidades no | 89,56 | No | Parecido al anterior. |
| Historia de 10 variables, sin préstamos | 89,86 | — | La historia ayudaba. |
| Historia de 10 variables, con préstamos | 90,03 | — | Mejor que por separado. |
| **BAJA+2 contra el resto**, con préstamos | 91,47 | **Sí** | Entrenar con la clase que paga fue lo que más mejoró. |
| Mezclas mitad y mitad del primer modelo con los tres mejores | 90,62 / 90,19 / 88,36 | No | Mezclar con un modelo peor bajó al mejor. |
| Promedio de las 20 semillas de BAJA+2 contra el resto | **91,80** | **Sí** | Base de todo lo que siguió. |

### 2. ¿Más variables?

| Qué probé | Interno | Bot | ¿Me lo quedé? | Por qué |
|---|---:|---:|---|---|
| Historia masiva de todas las variables | −6,97 | — | No | Peor que sin agregar nada. |
| Representaciones masivas (rankings, estados, transformaciones) | −7,41 | — | No | Peor en mayo y en junio. |
| Las dos cosas juntas | +3,67 | — | No | Mejoraba en promedio, pero el desvío entre semillas (23,34) era mucho mayor que la mejora. |
| **Solo dos familias: historia + tarjetas/ratios (C3)** | +8,95 | **96,06** | **Sí** | Confirmado con 20 semillas: +6,01 y 15 de 20 a favor. |

<p align="justify">Agregar miles de variables empeoró; agregar dos familias elegidas mejoró.</p>

### 3. Ventana, hiperparámetros y corte

| Qué probé | Bot | ¿Me lo quedé? | Por qué |
|---|---:|---|---|
| **SUPERFINAL:** sobre C3, comparar representaciones, pesos por mes, 20 trials de Optuna y el corte, con reglas fijadas de antemano | **98,51** | **Sí** | Quedó C3, los cuatro meses con igual peso, los hiperparámetros de la tabla de arriba y corte 13.500. |
| Promediar modelos con hiperparámetros distintos | — | No | En junio dio −12,1 M contra SUPERFINAL. |
| Mezclar los modelos de C3 con los de SUPERFINAL | — | No | No pasó mi regla para reemplazar a SUPERFINAL. |

### 4. ¿A cuáles BAJA+2 mirar más?

<p align="justify">Las tres primeras filas se compararon en mayo, entrenando con marzo y con 3 semillas.</p>

| Qué probé | Interno | Bot | ¿Me lo quedé? | Por qué |
|---|---:|---:|---|---|
| Triplicar el peso de C2 y multiplicar por 2,5 el de C5 | −9,9 | — | No | Recuperaba más C2 y C5, pero perdía más en los otros grupos. |
| Peso inverso a lo que se detectaba cada grupo en junio | −12,1 | — | No | Lo mismo. |
| **Peso inverso al tamaño del grupo, con tope** | +4,4 | **101,09** | **Sí, es la entrega final** | Único que pasó mayo; en junio dio +23,10 M y 20 de 20 semillas. |
| Armar los grupos solo con marzo, sin mirar meses posteriores | — | — | No | No pasó la prueba de mayo. |

<p align="justify"><b>Sobre el corte:</b> hasta C3 usé 11.000. SUPERFINAL comparó de 8.000 a 15.000 de a 500 y eligió 13.500 con 20 semillas en junio; el modelo final lo mantuvo fijo. Entre C3 y SUPERFINAL cambiaron a la vez el modelo y el corte, así que los +2,45 M del bot no son solo del modelo.</p>

<p align="justify"><b>Lo que me llevo:</b> lo que más movió la ganancia fue <b>qué le pido al modelo que aprenda</b>: primero la clase (BAJA+2 sola) y al final a qué BAJA+2 prestarle atención. Agregar variables en masa y mezclar modelos distintos me dio peor casi siempre.</p>
