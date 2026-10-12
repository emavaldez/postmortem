# Primera Competencia DMEyF 2026 — Ana Dominguez

**Entrega final:** `entrega_final/FINAL_e6019x40_N11000.csv`
(11.000 `numero_de_cliente` de 202108, sin encabezado).

## Cómo armé mi predicción final...

Es un **ensamble por promedio de 40 modelos LightGBM**. Todos tienen las mismas variables y los mismos hiperparámetros; solo cambié la semilla:

| Parte | Notebook | Qué aporta |
|---|---|---|
| 1 | `1_hiperparametros_6005/` | Bayesian Optimization que dio los hiperparámetros (`BO_log.txt`) |
| 2 | `2_modelo_6018/competencia01_gcp_6018_rank_cero_fijo.ipynb` | 20 modelos (bagging, 20 semillas) → `exp/HT6018/predicciones_futuro.csv` |
| 3 | `3_modelo_6019_y_final/competencia01_gcp_6019_6018_semillas_nuevas.ipynb` | 20 modelos más (20 semillas nuevas) + **promedio de los 40** → archivo final |

La probabilidad final de cada cliente es el promedio simple de las probabilidades de los 40 modelos (20 del 6018 + 20 del 6019). Se ordenan de mayor a menor y se envían los primeros 11.000.

### Detalle del modelo (6018 y 6019 son idénticos salvo las semillas)
- **Clase:** `clase01` = BAJA+1 + BAJA+2.
- **Meses:** entrenamiento final 202103–202106, predicción 202108 (202107 no se usa: no tiene clase).
- **Variables:**
  - aguinaldo  (`mpayroll_sin_sac`, `cobra_aguinaldo`);
  - lags y deltas de orden 1 para todas las variables;
  - lag y delta de orden 2 para una lista fija de 78 variables (escrita en la notebook);
  - 62 rankings "con cero fijo" dentro de cada mes (`rk_*`): 0 → 0, positivos en (0,1], negativos en [−1,0).
- **Entrenamiento:** cada modelo usa todas las bajas + un 25% de los CONTINUA, elegido con su propia semilla (`set.seed(semilla, kind="Mersenne-Twister")`).
- **Hiperparámetros:** la mejor fila de `exp/HT6005/BO_log.txt` (num_iterations, learning_rate, feature_fraction, num_leaves, min_data_in_leaf).
- **Semillas:**
  - 6018: las 10 de `PARAM$semillas` + 10 de `set.seed(992720)`;
  - 6019: 20 nuevas de `set.seed(992720 + 6019)`, sin repetir ninguna del 6018.

### De dónde sale cada parte
Las variables del 6018 se fueron sumando en experimentos anteriores: 6006 (bagging), 6011 (orden 2 selectivo), 6016 (rankings), 6018 (rankings con cero fijo). Esas notebooks **no hacen falta para replicar**: la notebook del 6018 ya incluye todo ese feature engineering, y ninguna de ellas genera un archivo que use la entrega final. Lo único que se reutiliza de un experimento anterior son los hiperparámetros del 6005.

## Cómo replicar (en orden)

Las notebooks están en **R** y esperan la estructura del curso en Google Cloud: `BASE <- ~/buckets/b1`. Cada notebook escribe en `~/buckets/b1/exp/HTxxxx/`. El dataset se descarga solo desde la URL de la competencia.

Máquina usada: Google Cloud, e2 custom de 8 vCPU y 64 GB de RAM (template del curso `to-064ram-08vcpu`).

**Paso 1 — Hiperparámetros (6005).** La notebook `1_hiperparametros_6005/competencia01_gcp_6005.ipynb` corre una Bayesian Optimization de 30 iteraciones (entrena 202103–202105 con 25% de CONTINUA, mide la ganancia en 202106) y escribe `exp/HT6005/BO_log.txt`. La mejor fila, que es la que usan el 6018 y el 6019, es:

| num_iterations | learning_rate | feature_fraction | num_leaves | min_data_in_leaf |
|---|---|---|---|---|
| 1168 | 0.01315415 | 0.3446377 | 61 | 966 |

 Hay dos opciones:
- **A (rápida, la recomendada):** copiar `1_hiperparametros_6005/BO_log.txt` a `~/buckets/b1/exp/HT6005/BO_log.txt`. Las notebooks 6018 y 6019 solo leen la mejor fila de ese archivo.
- **B (completa):** correr la notebook de `1_hiperparametros_6005/`, que genera ese mismo `BO_log.txt`. Tarda varias horas.

**Paso 2 — 6018.** Abrir `competencia01_gcp_6018_rank_cero_fijo.ipynb` y hacer **Run All** (~1,5–2,5 h).
Genera `exp/HT6018/predicciones_futuro.csv`, con las probabilidades de los 20 modelos para 202108.

**Paso 3 — 6019 y archivo final.** Abrir `competencia01_gcp_6019_6018_semillas_nuevas.ipynb` y hacer **Run All** (~1,5–2,5 h).
Entrena los 20 modelos nuevos y, en la última celda de código, promedia con los 20 del 6018 (lee `exp/HT6018/predicciones_futuro.csv`) y escribe:

```
exp/HT6019/zulip/FINAL_e6019x40_N11000.csv   <- la entrega final
```

**Verificación:** comparar ese archivo con `entrega_final/FINAL_e6019x40_N11000.csv`.
## Lo que probé en el camino

En el camino hubo muchos (MUCHOS) experimentos que no me salieron, o que por lo menos me tiraban para atrás, tanto en el bot como en mis métricas internas (la ganancia en junio, que usé como mes de prueba). Así que acá dejo el listado para los docentes y los compañeros del curso, por si a alguien le sirve saber qué caminos no conviene repetir.

| Exp | Qué probé | Ganancia (bot) | ¿Me lo quedé? | Por qué |
|---|---|---|---|---|
| 6005 | Modelo base: marca de aguinaldo, lags y deltas de orden 1, Bayesian Optimization propia, 10 semillas | 108,82 | Sí, como base | Es el punto de partida. Sus hiperparámetros fueron los que usé hasta el final. |
| 6006 | Bagging: 20 modelos, cada uno entrenado con su propio 25% de los CONTINUA | 109,04 | **Sí** | Antes, todos los modelos veían el mismo 25% de los clientes que se quedan. Con un sorteo distinto para cada modelo, entre los 20 ven a casi todos, y al promediar se compensan sus errores. En junio ganó 4 M contra la versión sin bagging. |
| 6007 | Más variables armadas a mano dentro de cada mes | 97,32 | No | Muchas columnas nuevas que repetían información que el modelo ya tenía. En vez de ayudar, le dieron más lugares donde encontrar patrones casuales del entrenamiento. |
| 6008 | Lag 2 y delta 2 para **todas** las variables | 99,83 | No | Para agosto, el delta 2 compara contra junio, que es el mes del aguinaldo. Sueldos y saldos de junio están inflados, entonces en agosto muchísimos clientes "parecen" haber caído, y el modelo los confunde con clientes que se van. |
| 8001 | Otra Bayesian Optimization, con otros hiperparámetros | 97,60 | No | Los hiperparámetros que mejor andan en el mes donde se eligen tienen parte de suerte. Ganaban en junio pero no se sostenían en agosto. |
| 6010 | Ensamble mezclando modelos con configuraciones distintas | 105,74 / 101,20 | No | Promediar solo ayuda si todos los modelos son buenos y se equivocan en cosas distintas. Acá los más flojos arrastraron hacia abajo al mejor. |
| 6011 | Lag 2 y delta 2 **solo** para 78 variables que no "mienten" en agosto | 109,56 | **Sí** | Hice un diagnóstico variable por variable: comparé cuánto se mueve agosto contra un mes normal. El orden 2 quedó solo donde agosto se ve como un mes común, y afuera las variables tocadas por el aguinaldo. |
| 6012 | Elegir hiperparámetros midiendo en mayo en vez de junio | 103,73 | No | La idea era tener junio como examen limpio, pero la bayesiana tuvo un mes menos para aprender, y lo que eligió no se trasladó bien a agosto. |
| 6013 | 6006 + 6011 juntos (40 modelos) | 109,29 | No | Dio lo mismo que el 6011 solo. Mezclar con un modelo un poco peor no suma. |
| 6014 | Sacar el aguinaldo también de junio en el entrenamiento | 107,58 | No | Al "limpiar" junio, las filas de entrenamiento dejaron de parecerse a lo que el modelo ve en agosto, y perdí información real de ese mes. |
| 6015 | El 6011 con semillas nuevas (40 modelos) | 109,48 | No lo usé, pero sirvió como control | Dio igual que el 6011. Confirmó que la mejora era real y no suerte de las semillas. |
| 6016 | 62 rankings de montos dentro de cada mes | 111,65 | **Sí** | Por la inflación, todos los montos en pesos suben mes a mes, así que un mismo sueldo "significa" distinto en marzo que en agosto. El ranking compara a cada cliente con los demás del mismo mes, y eso borra la inflación y el aguinaldo. |
| 6017 | Variables "dejó de…" (cobrar sueldo, débitos automáticos, tarjeta, canales) | 111,32 | No | La idea tenía sentido, pero esa información ya estaba en los lags, los deltas y `ctrx_quarter`. Para el modelo no era nada nuevo. |
| 6018 | Rankings con "cero fijo" | **112,39** | **Sí** | En el ranking común, "no tener el producto" quedaba pegado a "tener muy poco". Con cero fijo, el 0 es siempre 0, los positivos van entre 0 y 1 y las deudas entre −1 y 0. Tres situaciones distintas, bien separadas. |
| 6019x40 | El 6018 con 20 semillas nuevas, promediando los 40 modelos | 110,47 | **Sí, es la entrega final** | Es el mismo modelo que el 6018, promediado el doble de veces. Las semillas nuevas coinciden con las viejas en 10.812 de los 11.000 clientes enviados, así que la diferencia con el 6018 es ruido, y con 40 modelos la suerte de cada uno pesa la mitad. |
| 6022 | La receta de entrenamiento de la cátedra: sin undersampling, learning rate 0,005, bayesiana de 3 hiperparámetros, 10 modelos distintos | 105,02 | No | Con un learning rate tan bajo, seguramente necesitaba más árboles de los que le dejé probar a la bayesiana. Además, mis variables y mi forma de entrenar venían ajustadas juntas desde el principio. No me dio el tiempo para afinarla. |

**Sobre el corte:** probé desde 9.500 hasta 14.000 clientes. El 11.000 fue el mejor de forma consistente en todos los modelos.

**Lo que me llevo:** lo que más mejoró fueron las **variables que corrigen efectos del calendario**: el aguinaldo, la inflación y los meses que "mienten". Cambiar hiperparámetros o la forma de entrenar siempre me dio peor. Y aprendí a no perseguir diferencias chiquitas entre envíos: por eso elegí la versión de 40 modelos, la más estable, aunque el 6018 solo haya tenido un número un poco más alto.
### Notas
- Las celdas que comparan contra otros experimentos (6006, 6016) son solo informativas. Si esos archivos no existen, se saltean solas!
- LightGBM corre multihilo, así que en otra máquina puede haber diferencias ínfimas en las probabilidades y, como mucho, un puñado de clientes distintos cerca del corte 11.000.
