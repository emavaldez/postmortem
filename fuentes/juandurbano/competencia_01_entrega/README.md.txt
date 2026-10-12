# Competencia 1 · DMEyF 2026 · Entrega final (E780)

Esta carpeta contiene todo lo necesario para replicar en forma exacta la predicción final entregada.

|Archivo|Qué es|
|-|-|
|`E780_entrega.R`|Script único que, partiendo del crudo de la competencia, hace todo: clase, preprocesamiento, optimización de hiperparámetros, curva de junio, 109 modelos, ensamble y archivos de envío.|
|`README.md`|Este archivo: instrucciones, tiempos, resultados esperados y decisiones.|

No hace falta ningún otro archivo: la optimización de hiperparámetros que dio origen a la configuración final está dentro del mismo script y se vuelve a correr.

## Archivo entregado

**`E780_ens109m_k11000_20261011.csv`**

Es el ensamble (promedio simple de probabilidades) de 109 modelos LightGBM que solo difieren en la semilla, con los **11.000** clientes de mayor probabilidad.

El script genera el ensamble para los 15 cortes entre 8000 y 15000 (cada 500). El entregado es el del corte indicado arriba. Se encuentra en:

```
colab_replica/C1-E780-PR2108-final/entrega/ensamble/E780_ens109m_k<corte>_<fecha>.csv
```

La fecha del nombre es la del día en que se corre el script; la de la entrega fue `20261011`. El contenido no depende de la fecha.

## Requisitos

|Componente|Versión usada|
|-|-|
|R|4.6.1 (Windows 11 x64)|
|lightgbm|**4.7.0** (paquete de CRAN, **no** zlightgbm)|
|data.table|1.18.6.1|
|Hardware|Ryzen 7 7435HS, 16 hilos, 16 GB de RAM|

El script se detiene si la versión de lightgbm no es 4.7.0, porque otra versión puede dar otras predicciones. LightGBM corre con `num_threads = 16`, `deterministic = TRUE` y `force_row_wise = TRUE`.

## Cómo correrlo

1. Crear una carpeta de trabajo **vacía** y poner en ella el crudo de la competencia con el nombre `competencia_01_crudo.csv` (983.061 filas, 154 columnas).
2. Copiar `E780_entrega.R` a esa carpeta.
3. Desde esa carpeta, correr:

```
Rscript E780_entrega.R > E780.log 2>&1
```

Los resultados quedan en `colab_replica/C1-E780-PR2108-final/`. Si se prefieren otras rutas, se pueden indicar con las variables de entorno `DMEYF_CRUDO` (ruta del crudo) y `DMEYF_EXP` (carpeta de resultados).

**Es reanudable:** si la corrida se corta, al volver a lanzarla en la misma carpeta saltea lo que ya terminó (evaluaciones de la BO, curva de junio y cada modelo). El script nunca pisa archivos existentes y no envía nada a Zulip.

## Tiempo de ejecución

Tiempos reales en la notebook descripta arriba:

|Etapa|Tiempo|
|-|-|
|Lectura, clase y ranking|menos de 1 min|
|Optimización de hiperparámetros (10 evaluaciones)|33 min|
|Curva de ganancia en junio (5 modelos)|17 min|
|109 modelos finales (\~9,1 min cada uno)|\~16,5 h|
|**Total aproximado**|**\~17,5 h**|

## Qué hace el script

1. **Lee el crudo** y calcula `clase_ternaria`. Clase binaria: BAJA+1 y BAJA+2 = 1.
2. **Data quality:** `ccajas_depositos` está rota en 202105 (todo cero), así que se pone NA solo en ese mes.
3. **Ranking con cero fijo**, por variable y por mes: positivos en (0, 1], negativos en \[−1, 0), el cero queda en cero y los NA quedan NA. Se aplica a las 152 variables.
4. **Lags y delta lags de orden 1 y 2** calculados sobre los rankings. Después se eliminan las variables originales. Cada variable deja 5 columnas: ranking, lag1, delta1, lag2 y delta2.
5. **Optimización de hiperparámetros sin undersampling:**

   * train 202103+04, validación 202106 completo, métrica AUC, una semilla (106937), sin los préstamos personales (750 columnas);
   * solo el diseño inicial de 10 puntos, sin iteraciones inteligentes;
   * se elige la configuración de mayor AUC.
6. **Curva de ganancia en junio** de la configuración elegida, con 5 semillas y su ensamble. Es para mirar los envíos óptimos en junio y no interviene en la predicción.
7. **Entrenamiento final:** 202103 a 202106, sin undersampling, con los préstamos personales reincorporados ya rankeados (760 columnas).
8. **109 modelos** con los mismos hiperparámetros, uno por semilla. Se usan las primeras 109.
9. **Ensamble:** promedio simple de probabilidades por `numero_de_cliente`, y un archivo por corte con los clientes de mayor probabilidad.
10. **Validación de formato** de todos los archivos: entre 8000 y 15000 filas, enteros sin encabezado, sin repetidos y solo clientes de 202108.

## Resultados esperados (para verificar la réplica)

**Controles que imprime el log:**

```
npos 202103-05 = 6095 | ancla = 6095 -> OK
variables base a rankear: 152 | esperadas: 152 -> OK
columnas del modelo FINAL: 760 | esperadas: 760 -> OK
columnas de la BO (sin prestamos personales): 750 | esperadas: 750 -> OK
modelos terminados: 109
archivos validados: 335
```

**Optimización de hiperparámetros** (debe dar esta tabla; se guarda en `bo_top_configs.csv`):

|Iteración|Hojas|Hessiano|Árboles|AUC en 202106|
|-|-|-|-|-|
|**10 (elegida)**|**45**|**0,0244994712564396**|**2428**|**0,917295**|
|2|65|0,001693|2058|0,917282|
|6|80|0,013967|3259|0,917214|
|1|96|0,005135|1226|0,917200|
|3|111|0,028195|1011|0,917185|
|4|31|0,011653|3017|0,917177|
|8|89|0,019771|2049|0,916909|
|7|128|0,016312|2685|0,916299|
|5|18|0,007160|1708|0,915654|
|9|51|0,023864|779|0,914558|

**Curva de junio:** AUC del ensamble de 5 semillas en 202106 = 0,91792.

### Si la optimización eligiera otra configuración

La iteración 10 le gana a la 2 por solo 0,00001 de AUC. Con lightgbm 4.7.0 y 16 hilos se reproduce exactamente; con otro entorno, una diferencia numérica mínima podría invertir la elección.

Si `bo_mejor_config.csv` no muestra 45 hojas, hessiano 0,0244994712564396 y 2428 árboles, hay que:

1. descomentar en el script la línea marcada **`[ENTREGA 6] RESPALDO`**, que escribe `bo_mejor_config.csv` con esos valores;
2. volver a correr en una carpeta **nueva**.

El script usa entonces esa configuración sin repetir la optimización.

## Cambios respecto del script original

En el código, cada cambio está marcado `[ENTREGA n]`, con la línea original comentada y la nueva debajo.

|Marca|Original|En la entrega|Motivo|
|-|-|-|-|
|ENTREGA 1|Usaba zlightgbm si estaba instalado, si no lightgbm|Siempre lightgbm, y exige la versión 4.7.0|En la notebook se usó lightgbm 4.7.0; zlightgbm daría otras predicciones|
|ENTREGA 2|Rutas locales de mi PC y de mi VM (solo funcionan ahí)|Rutas relativas a la carpeta de trabajo|Que corra en cualquier máquina|
|ENTREGA 3|Sin `num_threads` (LightGBM usaba los 16 hilos de la notebook)|`num_threads = 16`|Misma cantidad de hilos en otra máquina|
|ENTREGA 4|Entrenaba semillas en orden hasta que se creaba `PARAR.txt` (paró en 109)|Las primeras 109 de la misma lista|Que la cantidad de modelos quede fija en el código|
|ENTREGA 5|Copiaba archivos ya calculados con este mismo código (BO, curva de junio y modelos ya entrenados)|No copia nada: hace todo desde el crudo|Que el script sea autocontenido|
|ENTREGA 6|—|Línea comentada de respaldo con la configuración elegida|Por si la optimización eligiera otra (ver arriba)|
|ENTREGA 7|Otro nombre de carpeta del experimento y de los archivos de cada modelo|`C1-E780-PR2108-final` y `prob_modelo_s<semilla>.csv`|Nombres más claros; no afecta el cálculo ni el nombre del archivo entregado|

## Elección del corte

El corte se eligió combinando tres fuentes:

* **Curva de cortes en el leaderboard público:** promedio de 20 semillas en cada corte entre 8000 y 15000, más ensambles de 20, 50 y 109 semillas.
* **Curva de ganancia en junio:** es el mes de validación.
* **Puntaje público:** se tomó con cautela.

**Lo que mostraron las curvas:**

* Las dos tienen un acantilado por debajo de unos 10.000 envíos y una meseta desde ahí.
* En el tramo 10.500 a 12.000, ningún corte pierde más de 1,2 % respecto del mejor de cada curva.
* Se evitaron los picos aislados del público.

**Corte elegido: 11.000.** Está dentro de la meseta de las dos curvas y deja margen respecto del "acantilado", que puede correrse en agosto (se consideró que era mejor pasarse que quedarse corto). En junio rinde apenas mejor que 10.500, y en el público la diferencia entre ambos puede ser ruido.
