# vmanuelmarasco — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: vmanuelmarasco
- Repositorio: https://github.com/vmanuelmarasco/dmeyf_2c_2026
- Link posteado: https://github.com/vmanuelmarasco/dmeyf_2c_2026/blob/verscla09/agente_churn/v09/verscla09.py
- Commit: 87c3f4165fb63fff37e03b2cfbc3d38f023bdf96
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/vmanuelmarasco/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/vmanuelmarasco.json

## Resumen

La entrega es la carpeta agente_churn/v09 del repositorio: el script verscla09.py (el archivo del link posteado), un README, dos scripts de trabajo (pipeline_v8.py y lab.py), un notebook de experimentos, un registro de experimentos (registro.csv) y 23 archivos CSV de predicciones. verscla09.py lee el CSV crudo con DuckDB, pasa a NULL ccajas_depositos en 202105, arma la clase ternaria según la presencia del cliente en los dos meses siguientes y genera variables en SQL: lag 1 y delta 1 de todas las variables numéricas, lags 2 y 3 y promedios de 3 meses de algunas, cambio relativo contra el mes anterior de 20 variables, cocientes de las tarjetas Visa y Master, 9 indicadores binarios de desvinculación y un índice que suma 4 de ellos. Entrena LightGBM con clase binaria (positivo = BAJA+1 o BAJA+2) sobre 202103-202106, con hiperparámetros fijos, 655 árboles y min_data_in_leaf escalado por la cantidad de filas; repite con 10 semillas y promedia las probabilidades. Ordena los clientes de 202108 por probabilidad y escribe los 13.000 primeros en un CSV de una columna sin encabezado, más un archivo por semilla. Con --validar entrena además con 202103-202104 y calcula la ganancia en 202106 para cortes entre 10.000 y 16.000 envíos. Según el README, verscla09 obtuvo 101,09 en el público y pipeline_v8.py y lab.py son los scripts de trabajo con los que se llegó a esa versión.

**Qué entrega.** Un CSV de una columna, sin encabezado, con los numero_de_cliente de los 13.000 clientes de 202108 de mayor probabilidad promedio (verscla09_k13000.csv), y 10 archivos con el mismo formato, uno por semilla. El repositorio incluye entregas/verscla09_k13000.csv (13.000 líneas), que el README identifica como la entrega final, y entregas/verscla09_semillas/ con 10 archivos cuyos nombres llevan las mismas 10 semillas del script.

**Cómo se ejecuta.** Según el README y el docstring del script: `python verscla09.py` genera entregas_verscla09/verscla09_k13000.csv y 10 archivos por semilla; `python verscla09.py --validar` calcula además la ganancia en 202106 entrenando con 202103-202104; `--crudo /ruta/competencia_01_crudo.csv` indica la ubicación del dataset. El README lista también los comandos de los scripts de trabajo (por ejemplo `python pipeline_v8.py --solo-final --features todas --semillas-final 10 --k 13000 --nombre verscla09`) y aclara que dependen de la carpeta resultados/base/ de competencia_v5, que no está dentro de agente_churn/v09.

## Ficha

- **Lenguajes:** Python, SQL
- **Modelos:** LightGBM
- **Clase que entrena:** Arma la clase ternaria en SQL (BAJA+1 si el cliente no está el mes siguiente, BAJA+2 si está el mes siguiente y no a los dos meses, CONTINUA si está en ambos) y entrena con una clase binaria: positivo = BAJA+1 o BAJA+2 (columna clase_binaria2).
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código de verscla09.py: entrena con todas las filas de 202103-202106. lab.py define una máscara de submuestreo de CONTINUA (parámetro ratio, por defecto 1.0, que no descarta filas); en los archivos de la carpeta no hay una llamada con ratio menor a 1.
- **Calidad de datos:** Convierte numero_de_cliente a entero de 64 bits (el comentario indica que el CSV trae algún id en notación científica) y pasa ccajas_depositos a NULL en 202105 (el comentario indica que vale 0 para todos los clientes ese mes).
- **Drifting:** No aplica rank, deflación ni estandarización por mes. Deja fuera del modelo las variables cuyo nombre contiene fultimo_cierre o Finiciomora (el comentario las describe como fechas con drift de datos) o mpayroll (el comentario: monto de sueldo, aguinaldo), junto con sus lags y deltas. Para 20 variables calcula el cambio relativo contra el mes anterior; el comentario indica que ese valor no depende de la inflación.
- **Variables dentro del mes:** Para Visa y Master: saldo total menos pagado, pagado / saldo total, pagado / pago mínimo y saldo total / límite de compra (4 por tarjeta, cada una sólo si existen las columnas que usa). Indicadores cobra_sueldo (cpayroll_trx > 0) y pocos_productos (cproductos <= 5).
- **Variables históricas:** Lag 1 y delta 1 de todas las variables numéricas; lag 2 y delta 2 de ctrx_quarter, delta 2 de cproductos, lags 2 y 3 de cpayroll_trx y lag 3 de mprestamos_personales; promedio de 3 meses (el actual y los dos anteriores) de ctrx_quarter y del consumo de tarjetas; cambio relativo contra el mes anterior de 20 variables (sufijo _var1); 9 indicadores binarios: cobra_sueldo, pocos_productos y 7 que comparan con la historia (cayo_actividad, cayo_consumo_tc, bajo_productos, dejo_de_cobrar_sueldo, dejo_de_cobrar_reciente, termino_prestamo, prestamo_por_terminar) y el índice indice_desvinculacion, que suma 4 de ellos.
- **Selección de variables:** Usa todas las columnas salvo numero_de_cliente, foto_mes y las dos de clase, y salvo las que contienen fultimo_cierre, Finiciomora o mpayroll en el nombre. Según el README quedan 484 variables. El notebook de experimentos prueba una selección por null importance (umbrales 1,5 y 3), fuera del camino de la entrega.
- **Optimización de hiperparámetros:** No se observa en el código de la entrega: los valores están escritos en el script. El comentario indica que son los de verscla05, obtenidos con Optuna sobre abril; el código de esa búsqueda no está en la carpeta.
- **Hiperparámetros finales:** objective binary, boosting_type gbdt, num_leaves 76, learning_rate 0.009414528604172152, min_data_in_leaf 691 multiplicado por (filas de entrenamiento / filas de 202104), feature_fraction 0.8075276247459833, bagging_fraction 0.5141471765041344, bagging_freq 1, max_bin 31, boost_from_average True, feature_pre_filter False, first_metric_only True; 655 árboles.
- **Semillas:** 10 semillas escritas en el código: 100129, 100183, 100151, 500041, 900007, 273311, 750209, 219281, 484609 y 496259. Cada una se pasa al Dataset y a los parámetros de LightGBM.
- **Cantidad de semillas:** 10
- **Ensamble:** Semillerío: un LightGBM por semilla con los mismos hiperparámetros y promedio de las 10 probabilidades. lab.py y el notebook prueban además promedios de rankings entre modelos distintos (LightGBM, XGBoost, objetivos de ranking), fuera del camino de la entrega.
- **Corte:** Cantidad fija: los K = 13000 clientes de mayor probabilidad promedio; K está escrito como constante.
- **Validación:** Opcional, con --validar: entrena el semillerío con 202103-202104, predice 202106 y calcula la ganancia acumulada (1.072.500 por cada BAJA+2 y −27.500 por cada otro cliente) para cortes de 10.000 a 16.000 envíos cada 500.
- **Salidas:** entregas_verscla09/verscla09_k13000.csv (carpeta configurable con --salida) y entregas_verscla09/semillas/verscla09_seed{semilla}_k13000.csv, uno por semilla. Si existe entregas/verscla09_k13000.csv, imprime el porcentaje de ids en común con ese archivo.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)

## Técnicas sólo exploradas

- XGBoost (`modelo.xgboost`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Validación cruzada (`validacion.validacion_cruzada`)
- Pesos distintos por clase o por fila al entrenar (`clase.pesos_por_clase`)
- Submuestreo de la clase CONTINUA (`datos.submuestreo_continua`)
- Optuna (`hiperparametros.optuna`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: no
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: sí
- Entorno declarado: No se declara. La ruta por defecto del dataset escrita en el código es una carpeta de usuario bajo /Users/…/Library/CloudStorage/ y se puede reemplazar con --crudo.

## Pasos del camino de la entrega

1. **Configuración de la corrida.** Define como constantes la ruta por defecto del CSV crudo, los meses de entrenamiento (202103 a 202106), el mes a predecir (202108), el mes de referencia (202104), K = 13000, los valores de ganancia y costo, los hiperparámetros de LightGBM, los 655 árboles, las 10 semillas, los patrones de variables excluidas y la lista de 20 variables para el cambio relativo. (`agente_churn/v09/verscla09.py` líneas 31–57)
2. **Lectura del crudo y corrección de datos.** Carga el CSV en una tabla DuckDB en memoria, convierte numero_de_cliente a entero y pasa ccajas_depositos a NULL en 202105. (`agente_churn/v09/verscla09.py` líneas 67–74)
3. **Clase ternaria.** Cruza todos los clientes con todos los meses, marca la presencia en cada mes y, mirando los dos meses siguientes con lead, asigna BAJA+1, BAJA+2, CONTINUA o NULL. Conserva sólo las filas en que el cliente está presente. (`agente_churn/v09/verscla09.py` líneas 76–99)
4. **Lag 1 y delta 1 de todas las variables numéricas.** Identifica las columnas numéricas de la tabla base y arma, para cada una, el valor de la fila anterior del cliente y la diferencia con ese valor. (`agente_churn/v09/verscla09.py` líneas 103–115)
5. **Historia puntual, cambio relativo y variables de tarjeta.** Agrega 8 variables de historia (lags 2 y 3, deltas 2 y promedios de 3 meses de variables elegidas), el cambio relativo contra el mes anterior de las 20 variables de la lista AMEX y cuatro variables por tarjeta (Visa y Master). Todo se materializa en la tabla historia con dos ventanas por cliente. (`agente_churn/v09/verscla09.py` líneas 116–146)
6. **Señales de desvinculación.** Crea la tabla fe con 9 indicadores 0/1 (caída de actividad, caída de consumo de tarjetas, baja de productos, dejó de cobrar sueldo, cobra sueldo, pocos productos, préstamo terminado o por terminar) y un índice que suma cuatro de ellos. (`agente_churn/v09/verscla09.py` líneas 148–164)
7. **Selección de meses, clase binaria y lista de variables.** Trae a pandas los meses pedidos, agrega la clase binaria (1 si BAJA+1 o BAJA+2) y arma la lista de variables excluyendo identificador, mes, clases y las columnas con fultimo_cierre, Finiciomora o mpayroll en el nombre. (`agente_churn/v09/verscla09.py` líneas 167–176)
8. **Validación opcional en 202106.** Con --validar entrena el semillerío con 202103 y 202104, predice 202106 e imprime la ganancia en millones para cortes de 10.000 a 16.000 envíos cada 500. (`agente_churn/v09/verscla09.py` líneas 196–199; `agente_churn/v09/verscla09.py` líneas 224–231)
9. **Entrenamiento final con semillerío.** Entrena un LightGBM por cada una de las 10 semillas con 202103-202106, 655 árboles y min_data_in_leaf escalado por la relación entre las filas de entrenamiento y las filas de 202104; predice 202108 y promedia las probabilidades. (`agente_churn/v09/verscla09.py` líneas 180–193; `agente_churn/v09/verscla09.py` líneas 233–235)
10. **Escritura de la entrega.** Ordena los clientes de 202108 por probabilidad, toma los 13.000 primeros y escribe un CSV de una columna sin encabezado; repite con la predicción de cada semilla en la subcarpeta semillas/. (`agente_churn/v09/verscla09.py` líneas 203–208; `agente_churn/v09/verscla09.py` líneas 237–242)
11. **Comparación con el archivo enviado.** Si existe entregas/verscla09_k13000.csv, imprime el porcentaje de ids que el archivo recién generado tiene en común con él. (`agente_churn/v09/verscla09.py` líneas 244–248)

## Archivos

- `agente_churn/v09/experimentos_v7.ipynb` · secundario · Jupyter (python) · 172 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/vmanuelmarasco/agente_churn/v09/experimentos_v7.ipynb.txt) — Notebook de experimentos sobre las tablas guardadas de una versión anterior (resultados/base/), medidos en 202106 con lab.evaluar: ensambles con otro modelo (verscla02), variables bancarias adicionales, objetivos de ranking, selección por null importance, validación cruzada dentro de 202106 y dos celdas que ejecutan pipeline_v8.py.
- `agente_churn/v09/README.md` · explicacion · Markdown · 47 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/vmanuelmarasco/agente_churn/v09/README.md.txt) — Presenta la entrega verscla09. Incluye una tabla de versiones (verscla05, verscla07, ens4, verscla08 y verscla09) con cantidad de variables, meses de entrenamiento y puntajes del público declarados por el autor (para verscla09: 484 variables, 202103-202106, 100,31 ± 1,38 de media por semilla en 10 archivos y 101,09 el semillerío), los comandos para reproducir, una lista de experimentos descartados medidos en 202106 y la descripción de los archivos de entregas/.
- `agente_churn/v09/verscla09.py` · principal · Python · 252 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/vmanuelmarasco/agente_churn/v09/verscla09.py.txt) — Script del link posteado. Lee el crudo, arma la clase y las variables en DuckDB, entrena un semillerío de LightGBM con 202103-202106 y escribe los 13.000 clientes de 202108 de mayor probabilidad. El README lo describe como el script único y autocontenido de la entrega final.
- `agente_churn/v09/lab.py` · secundario · Python · 205 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/vmanuelmarasco/agente_churn/v09/lab.py.txt) — Módulo de funciones para experimentar que usan pipeline_v8.py y el notebook: carga de tablas guardadas en resultados/base/, curva de ganancia y meseta en 202106, registro de experimentos en resultados/registro.csv, promedio de rankings, semilleríos de LightGBM, XGBoost y objetivos de ranking, null importance y escritura del archivo de entrega.
- `agente_churn/v09/pipeline_v8.py` · secundario · Python · 262 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/vmanuelmarasco/agente_churn/v09/pipeline_v8.py.txt) — Script de trabajo que, según el README, se usó para llegar a verscla08 y verscla09. Construye las mismas tablas de variables que verscla09.py, lee hiperparámetros, semillas y lista de variables de resultados/base/config.json, valida en 202106 con dos esquemas y entrena el modelo final con 202103-202106; con --features todas y el nombre verscla09 escribe entregas/verscla09_k{k}.csv y un archivo por semilla mediante lab.entrega.

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### agente_churn/v09/verscla09.py

Script del link posteado. Lee el crudo, arma la clase y las variables en DuckDB, entrena un semillerío de LightGBM con 202103-202106 y escribe los 13.000 clientes de 202108 de mayor probabilidad. El README lo describe como el script único y autocontenido de la entrega final.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–21] Docstring del módulo: enumera los cuatro pasos del script (lectura y clase
#   ternaria, variables en DuckDB, entrenamiento de LightGBM con 202103-202106 y 10 semillas, entrega de 13.000
#   clientes de 202108) y las tres formas de uso (sin argumentos, --validar, --crudo). Declara un puntaje
#   público de 101,09.
"""verscla09.py — script único que genera la entrega final verscla09 (público 101,09).

Qué hace, en orden:
  1. Lee el crudo y arma la clase ternaria (BAJA+1 / BAJA+2 / CONTINUA), como en z101.
  2. Feature engineering en DuckDB:
       - lag 1 y delta 1 de todas las variables numéricas (historia por cliente, z402);
       - historia puntual: lags 2 y 3, promedios de 3 meses;
       - cambio relativo contra el mes anterior y manejo de la tarjeta ("Amex");
       - señales de desvinculación (cayó la actividad, dejó de cobrar el sueldo, préstamo por terminar, etc.).
  3. Entrena LightGBM con 202103-202106 (los 4 meses con clase completa), target BAJA+1 + BAJA+2,
     min_data_in_leaf escalado por la cantidad de filas (z494), semillerío de 10 semillas.
  4. Ordena los clientes de 202108 por probabilidad y entrega los 13.000 primeros:
     un CSV de una columna, sin encabezado, ids enteros. Además un archivo por semilla.

Uso:
  python verscla09.py                      genera la entrega
  python verscla09.py --validar            además mide en 202106 entrenando con 202103-202104
  python verscla09.py --crudo /ruta/competencia_01_crudo.csv

Si ya existe entregas/verscla09_k13000.csv (la entrega enviada), al final compara contra ella.
"""
# [Anotación · líneas 22–29] Importa argparse, os y time de la biblioteca estándar, y duckdb, lightgbm, numpy
#   y pandas.
import argparse
import os
import time

import duckdb
import lightgbm as lgb
import numpy as np
import pandas as pd

# [Anotación · líneas 31–39] Constantes de la corrida: ruta por defecto del CSV crudo (una carpeta de usuario
#   con almacenamiento en la nube), meses de entrenamiento final 202103 a 202106, mes a predecir 202108, mes de
#   referencia 202104 para escalar min_data_in_leaf, K = 13000 envíos y los valores de la ganancia: 1.072.500
#   por acierto y 27.500 de costo.
# ============================================================================ configuración
CRUDO = ('/Users/manuelmarasco/Library/CloudStorage/[correo]/'
         'Mi unidad/DMEyF/2026/notebooks/data/competencia_01_crudo.csv')
MESES_FINAL = [202103, 202104, 202105, 202106]   # todos los meses con clase completa
MES_FUTURO = 202108
MES_REFERENCIA = 202104                           # los hiperparámetros se buscaron con un mes (abril)
K = 13000                                         # cantidad de envíos

GANANCIA, COSTO = 1_072_500, 27_500

# [Anotación · líneas 41–48] Hiperparámetros fijos de LightGBM (objetivo binario, gbdt, num_leaves 76,
#   learning_rate 0,0094, min_data_in_leaf 691, feature_fraction 0,81, bagging_fraction 0,51 con bagging_freq 1,
#   max_bin 31), 655 árboles y la lista de 10 semillas. El comentario indica que los valores vienen de una
#   búsqueda con Optuna sobre abril hecha para verscla05.
# Hiperparámetros de verscla05 (Optuna sobre abril, z601), 655 árboles
PARAMS = {'objective': 'binary', 'boosting_type': 'gbdt', 'first_metric_only': True,
          'boost_from_average': True, 'feature_pre_filter': False, 'max_bin': 31,
          'bagging_freq': 1, 'verbose': -1, 'num_leaves': 76,
          'learning_rate': 0.009414528604172152, 'min_data_in_leaf': 691,
          'feature_fraction': 0.8075276247459833, 'bagging_fraction': 0.5141471765041344}
N_ARBOLES = 655
SEMILLAS = [100129, 100183, 100151, 500041, 900007, 273311, 750209, 219281, 484609, 496259]

# [Anotación · líneas 50–57] Define las columnas que no entran como variables (identificador, mes y las dos
#   clases), los tres patrones de nombre que se excluyen del modelo junto con todo lo derivado (fultimo_cierre,
#   Finiciomora, mpayroll) y la lista AMEX de 20 variables a las que se les calcula el cambio relativo mensual.
NO_FEATURES = {'numero_de_cliente', 'foto_mes', 'clase_ternaria', 'clase_binaria2'}
# Fuera del modelo, con todo lo derivado: fechas con drift de datos y monto de sueldo (aguinaldo)
FUERA = ('fultimo_cierre', 'Finiciomora', 'mpayroll')
AMEX = ['ctrx_quarter', 'mcuentas_saldo', 'mcaja_ahorro', 'mpasivos_margen', 'mactivos_margen',
        'mrentabilidad', 'mcomisiones', 'mcomisiones_mantenimiento', 'mtarjeta_visa_consumo',
        'mtarjeta_master_consumo', 'ctarjeta_visa_transacciones', 'ctarjeta_master_transacciones',
        'chomebanking_transacciones', 'mtransferencias_recibidas', 'mtransferencias_emitidas',
        'mprestamos_personales', 'Visa_msaldototal', 'Master_msaldototal', 'Visa_mpagado', 'Master_mpagado']

# [Anotación · líneas 59–63] Guarda la hora de inicio y define log(), que imprime cada mensaje precedido por
#   los minutos transcurridos.
T0 = time.time()


def log(*a):
    print(f'[{(time.time() - T0) / 60:5.1f} min]', *a, flush=True)


# [Anotación · líneas 66–74] cargar_y_clase(): carga el CSV en una tabla DuckDB llamada crudo, convirtiendo
#   numero_de_cliente a entero de 64 bits. Si existe la columna ccajas_depositos, la pasa a NULL en todas las
#   filas de 202105.
# ============================================================================ 1. datos y clase
def cargar_y_clase(con, crudo):
    # numero_de_cliente a entero: el CSV trae algún id en notación científica (48000000)
    con.sql(f"""create table crudo as
                select * replace (cast(numero_de_cliente as bigint) as numero_de_cliente)
                from read_csv_auto('{crudo}')""")
    # ccajas_depositos vale 0 para todos los clientes en 202105: error de datos
    if 'ccajas_depositos' in [r[0] for r in con.sql('describe crudo').fetchall()]:
        con.sql("update crudo set ccajas_depositos = null where foto_mes = 202105")

# [Anotación · líneas 76–99] Crea la tabla base con la clase ternaria: cruza todos los clientes con todos los
#   meses, marca con 1 o 0 si el cliente está presente en cada mes y, con lead sobre la ventana por cliente,
#   asigna BAJA+1 si no está el mes siguiente, BAJA+2 si está el mes siguiente y no a los dos meses, CONTINUA si
#   está en ambos y NULL en los casos restantes. Conserva sólo las filas en que el cliente está presente e
#   imprime las tres primeras filas del conteo por mes y clase.
    # Clase ternaria: se mira si el cliente está en t+1 y t+2
    con.sql("""
    create table base as
    with periodos as (select distinct foto_mes from crudo),
         clientes as (select distinct numero_de_cliente from crudo),
         todo as (select numero_de_cliente, foto_mes from clientes cross join periodos),
         marca as (
            select t.numero_de_cliente, t.foto_mes,
                   if(c.numero_de_cliente is null, 0, 1) as mes_0
            from todo t left join crudo c using (numero_de_cliente, foto_mes)),
         clase as (
            select numero_de_cliente, foto_mes, mes_0,
              case
                when lead(mes_0, 1) over w = 0 then 'BAJA+1'
                when lead(mes_0, 1) over w = 1 and lead(mes_0, 2) over w = 0 then 'BAJA+2'
                when lead(mes_0, 1) over w = 1 and lead(mes_0, 2) over w = 1 then 'CONTINUA'
                else null end as clase_ternaria
            from marca window w as (partition by numero_de_cliente order by foto_mes))
    select c.*, k.clase_ternaria
    from crudo c join clase k using (numero_de_cliente, foto_mes)
    where k.mes_0 = 1
    """)
    log('clase armada:', con.sql("""select foto_mes, clase_ternaria, count(*) from base
                                    group by all order by all""").fetchall()[:3], '...')


# [Anotación · líneas 102–115] armar_variables(): toma de la tabla base las columnas de tipo numérico (entero,
#   double, float o decimal) que no están en NO_FEATURES y, para cada una, arma la expresión SQL del valor en la
#   fila anterior del cliente (sufijo _lag1) y la de la diferencia con ese valor (sufijo _delta1).
# ============================================================================ 2. variables
def armar_variables(con):
    tipos = {r[0]: r[1] for r in con.sql('describe base').fetchall()}
    numericas = [c for c, t in tipos.items()
                 if c not in NO_FEATURES and any(x in t for x in ('INT', 'DOUBLE', 'FLOAT', 'DECIMAL'))]

    def q(c):
        return f'"{c}"'

    exprs = []
    # lag 1 y delta 1 de todas las variables numéricas
    for c in numericas:
        exprs.append(f'lag({q(c)}, 1) over w as {q(c + "_lag1")}')
        exprs.append(f'{q(c)} - lag({q(c)}, 1) over w as {q(c + "_delta1")}')
# [Anotación · líneas 116–127] Agrega 8 variables de historia puntual: lag 2 y delta 2 de ctrx_quarter, delta
#   2 de cproductos, promedio de 3 meses de ctrx_quarter y del consumo sumado de Visa y Master (nulos como 0),
#   lag 3 de mprestamos_personales y lags 2 y 3 de cpayroll_trx.
    # historia puntual que usan las señales de desvinculación
    puntual = {
        'ctrx_quarter_lag2': 'lag(ctrx_quarter, 2) over w',
        'ctrx_quarter_delta2': 'ctrx_quarter - lag(ctrx_quarter, 2) over w',
        'cproductos_delta2': 'cproductos - lag(cproductos, 2) over w',
        'ctrx_quarter_avg3': 'avg(ctrx_quarter) over w3',
        'consumo_tc_avg3': 'avg(coalesce(mtarjeta_visa_consumo, 0) + coalesce(mtarjeta_master_consumo, 0)) over w3',
        'mprestamos_personales_lag3': 'lag(mprestamos_personales, 3) over w',
        'cpayroll_trx_lag2': 'lag(cpayroll_trx, 2) over w',
        'cpayroll_trx_lag3': 'lag(cpayroll_trx, 3) over w',
    }
    exprs += [f'{e} as {n}' for n, e in puntual.items()]
# [Anotación · líneas 128–140] Para cada variable de la lista AMEX calcula el cambio relativo contra el mes
#   anterior, (valor − lag 1) / |lag 1|, con NULL cuando el lag es 0 (sufijo _var1). Para Visa y Master arma
#   cuatro variables del mes: saldo total menos pagado, pagado sobre saldo total, pagado sobre pago mínimo y
#   saldo total sobre límite de compra, con NULL cuando el denominador es 0.
    # cambio relativo contra el mes anterior: -0,5 = cayó a la mitad, sin importar la inflación
    for c in [a for a in AMEX if a in numericas]:
        exprs.append(f'({q(c)} - lag({q(c)}, 1) over w) / nullif(abs(lag({q(c)}, 1) over w), 0) as {q(c + "_var1")}')
    # manejo de la tarjeta
    for t in ['Visa', 'Master']:
        s, p, m, l = f'{t}_msaldototal', f'{t}_mpagado', f'{t}_mpagominimo', f'{t}_mlimitecompra'
        if s in numericas and p in numericas:
            exprs.append(f'{s} - {p} as {t}_deuda_tras_pago')
            exprs.append(f'{p} / nullif({s}, 0) as {t}_pago_sobre_saldo')
        if p in numericas and m in numericas:
            exprs.append(f'{p} / nullif({m}, 0) as {t}_pago_sobre_minimo')
        if s in numericas and l in numericas:
            exprs.append(f'{s} / nullif({l}, 0) as {t}_uso_limite')

# [Anotación · líneas 142–146] Crea la tabla historia con todas las columnas de base más las expresiones
#   anteriores. Define dos ventanas por cliente ordenadas por foto_mes: w, para lags y deltas, y w3, que abarca
#   la fila actual y las dos anteriores, para los promedios.
    con.sql(f"""create table historia as
        select *, {', '.join(exprs)}
        from base
        window w as (partition by numero_de_cliente order by foto_mes),
               w3 as (partition by numero_de_cliente order by foto_mes rows between 2 preceding and current row)""")

# [Anotación · líneas 148–164] Crea la tabla fe agregando 9 indicadores 0/1: actividad trimestral menor a la
#   mitad de su promedio de 3 meses, consumo de tarjetas menor a la mitad de su promedio, menos productos que el
#   mes anterior, dejó de cobrar sueldo (respecto del mes anterior y respecto de alguno de los 3 anteriores),
#   cobra sueldo, 5 productos o menos, préstamo personal terminado (había saldo hace 3 meses y ahora es 0) y
#   préstamo por terminar (saldo menor al 25 % del de hace 3 meses). Suma cuatro de ellos en
#   indice_desvinculacion.
    # señales de desvinculación (respaldadas por el EDA)
    con.sql("""create table fe as
    with s as (
      select *
        , if(ctrx_quarter < 0.5 * ctrx_quarter_avg3, 1, 0) as cayo_actividad
        , if(coalesce(mtarjeta_visa_consumo, 0) + coalesce(mtarjeta_master_consumo, 0) < 0.5 * consumo_tc_avg3, 1, 0) as cayo_consumo_tc
        , if(cproductos < cproductos_lag1, 1, 0) as bajo_productos
        , if(cpayroll_trx_lag1 > 0 and coalesce(cpayroll_trx, 0) = 0, 1, 0) as dejo_de_cobrar_sueldo
        , if(coalesce(cpayroll_trx, 0) = 0 and (cpayroll_trx_lag1 > 0 or cpayroll_trx_lag2 > 0 or cpayroll_trx_lag3 > 0), 1, 0) as dejo_de_cobrar_reciente
        , if(coalesce(cpayroll_trx, 0) > 0, 1, 0) as cobra_sueldo
        , if(cproductos <= 5, 1, 0) as pocos_productos
        , if(mprestamos_personales_lag3 > 0 and coalesce(mprestamos_personales, 0) = 0, 1, 0) as termino_prestamo
        , if(mprestamos_personales_lag3 > 0 and mprestamos_personales > 0
             and mprestamos_personales < 0.25 * mprestamos_personales_lag3, 1, 0) as prestamo_por_terminar
      from historia)
    select *, cayo_actividad + cayo_consumo_tc + bajo_productos + dejo_de_cobrar_reciente as indice_desvinculacion
    from s""")


# [Anotación · líneas 167–176] meses() trae de fe a un DataFrame de pandas los meses pedidos, ordenados por
#   mes y cliente, y agrega clase_binaria2 = 1 si la clase ternaria es BAJA+1 o BAJA+2. variables_del_modelo()
#   devuelve las columnas que no están en NO_FEATURES ni contienen alguno de los patrones de FUERA.
def meses(con, lista):
    df = con.sql(f"select * from fe where foto_mes in ({', '.join(map(str, lista))}) "
                 f"order by foto_mes, numero_de_cliente").df()
    if 'clase_ternaria' in df.columns:
        df['clase_binaria2'] = df['clase_ternaria'].isin(['BAJA+1', 'BAJA+2']).astype(int)
    return df


def variables_del_modelo(df):
    return [c for c in df.columns if c not in NO_FEATURES and not any(p in c for p in FUERA)]


# [Anotación · líneas 179–193] semillerio(): copia los hiperparámetros y recalcula min_data_in_leaf como 691 ×
#   filas de entrenamiento / filas del mes de referencia, con mínimo 1. Para cada una de las 10 semillas arma el
#   Dataset de LightGBM, entrena 655 iteraciones con esa semilla y predice sobre la tabla a aplicar. Devuelve el
#   promedio de las probabilidades y la lista de predicciones por semilla.
# ============================================================================ 3. modelo
def semillerio(train, aplicar, feats, filas_ref):
    """Un LightGBM por semilla (mismos hiperparámetros) y promedio de las probabilidades."""
    p = dict(PARAMS)
    # min_data_in_leaf es un mínimo absoluto de filas: se escala con el tamaño del entrenamiento
    p['min_data_in_leaf'] = max(1, int(round(PARAMS['min_data_in_leaf'] * len(train) / filas_ref)))
    log(f'entreno {len(SEMILLAS)} semillas | {len(train):,} filas | {len(feats)} variables | '
        f'min_data_in_leaf {PARAMS["min_data_in_leaf"]} -> {p["min_data_in_leaf"]}')
    preds = []
    for i, s in enumerate(SEMILLAS):
        d = lgb.Dataset(train[feats], label=train['clase_binaria2'], params={'max_bin': p['max_bin'], 'seed': s})
        m = lgb.train({**p, 'seed': s, 'verbose': -1}, d, num_boost_round=N_ARBOLES)
        preds.append(m.predict(aplicar[feats]))
        log(f'  semilla {i + 1}/{len(SEMILLAS)} ({s}) lista')
    return np.mean(preds, axis=0), preds


# [Anotación · líneas 196–199] ganancia_por_envios(): ordena de mayor a menor probabilidad, acumula +1.072.500
#   por cada BAJA+2 y −27.500 por cada otro cliente y devuelve la ganancia en millones para cada corte de 10.000
#   a 16.000 envíos, de a 500.
def ganancia_por_envios(prob, clase, cortes=range(10000, 16001, 500)):
    orden = np.argsort(-prob, kind='stable')
    acum = np.cumsum(np.where(clase[orden] == 'BAJA+2', GANANCIA, -COSTO))
    return pd.Series({k: acum[k - 1] / 1e6 for k in cortes}, name='ganancia_M')


# [Anotación · líneas 202–208] escribir(): toma los ids de los K = 13000 clientes de mayor probabilidad, los
#   convierte a entero, verifica que no haya repetidos, crea la carpeta de destino y guarda un CSV de una
#   columna sin índice ni encabezado.
# ============================================================================ 4. entrega
def escribir(prob, ids, archivo):
    elegidos = ids[np.argsort(-prob, kind='stable')][:K].astype('int64')
    assert len(set(elegidos)) == K
    os.makedirs(os.path.dirname(archivo), exist_ok=True)
    pd.Series(elegidos).to_csv(archivo, index=False, header=False)
    return archivo


# [Anotación · líneas 211–222] main(): lee los argumentos --crudo, --validar y --salida (por defecto
#   entregas_verscla09), abre una conexión DuckDB en memoria, ejecuta la carga y la creación de variables y
#   cuenta las filas de 202104, que usa como referencia para escalar min_data_in_leaf.
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--crudo', default=CRUDO)
    ap.add_argument('--validar', action='store_true', help='mide en 202106 entrenando con 202103-202104')
    ap.add_argument('--salida', default='entregas_verscla09')
    a = ap.parse_args()

    con = duckdb.connect()
    cargar_y_clase(con, a.crudo)
    armar_variables(con)
    filas_ref = con.sql(f'select count(*) from fe where foto_mes = {MES_REFERENCIA}').fetchone()[0]
    log('variables listas')

# [Anotación · líneas 224–231] Si se pasa --validar: entrena el semillerío con 202103 y 202104, predice 202106
#   e imprime la ganancia en millones para cada corte; luego libera esas tablas.
    if a.validar:
        # Mismo hueco de dos meses que la entrega: se aprende hasta abril y se mide en junio
        train, junio = meses(con, [202103, 202104]), meses(con, [202106])
        feats = variables_del_modelo(train)
        prob, _ = semillerio(train, junio, feats, filas_ref)
        print('\nValidación 202103-202104 -> 202106 (millones):')
        print(ganancia_por_envios(prob, junio['clase_ternaria'].values).round(1).to_string())
        del train, junio

# [Anotación · líneas 233–242] Entrena el semillerío con 202103-202106 y predice 202108. Escribe
#   verscla09_k13000.csv con el promedio de las 10 semillas y, en la subcarpeta semillas/, un archivo por
#   semilla con la predicción individual. Imprime los primeros 60 caracteres del archivo principal.
    train, agosto = meses(con, MESES_FINAL), meses(con, [MES_FUTURO])
    feats = variables_del_modelo(train)
    prob, preds = semillerio(train, agosto, feats, filas_ref)

    ids = agosto['numero_de_cliente'].values
    final = escribir(prob, ids, f'{a.salida}/verscla09_k{K}.csv')
    for s, p in zip(SEMILLAS, preds):
        escribir(p, ids, f'{a.salida}/semillas/verscla09_seed{s}_k{K}.csv')
    log(f'listo: {final} y {len(SEMILLAS)} archivos por semilla en {a.salida}/semillas/')
    print(open(final).read()[:60])

# [Anotación · líneas 244–252] Si existe entregas/verscla09_k13000.csv, lee ese archivo y el recién generado e
#   imprime el porcentaje de ids en común sobre 13.000. Las dos últimas líneas ejecutan main() cuando el archivo
#   se corre como script.
    enviada = 'entregas/verscla09_k13000.csv'
    if os.path.exists(enviada):
        a_ = set(pd.read_csv(final, header=None)[0])
        b_ = set(pd.read_csv(enviada, header=None)[0])
        print(f'Coincidencia con la entrega enviada ({enviada}): {len(a_ & b_) / K * 100:.2f} %')


if __name__ == '__main__':
    main()
```


## Explicaciones del alumno (texto original)

### agente_churn/v09/README.md

> # verscla09 — entrega final (público 101,09)
>
> Pipeline en un script (`pipeline_v8.py`) que arma todo desde el crudo en DuckDB y entrena con LightGBM,
> más un módulo de experimentos (`lab.py`) y su notebook (`experimentos_v7.ipynb`).
>
> ## El cambio que movió la aguja
> Hasta verscla07 el modelo de la entrega se entrenaba **solo con 202106**. verscla09 lo entrena con
> **202103–202106** (cuatro veces más bajas para aprender), con `min_data_in_leaf` escalado por la cantidad
> de filas (`param_normalizado`, z494), y suma **lag 1 y delta 1 de todas las variables** (z402) a las 203 de verscla05.
>
> | Versión | Variables | Entrena la entrega con | Público: media por semilla | Público: semillerío |
> |---|---|---|---|---|
> | verscla05 | 203 (señales + Amex) | 202106 | 96,32 ± 1,68 (5 archivos) | 98,285 |
> | verscla07 | ensamble de 3 modelos | 202106 | — | 97,955 |
> | ens4 (`verscla08_ens4_k13500.csv`) | verscla07 + verscla02 | 202106 | — | 98,70 |
> | verscla08 | 203 (señales + Amex) | 202103–202106 | — | 96,69 (enviado como `verscla09b`) |
> | **verscla09** | **484 (+ lag 1 y delta 1 de todas)** | **202103–202106** | **100,31 ± 1,38 (10 archivos)** | **101,09** |
>
> Lectura: con las 203 variables, entrenar con más meses no mejora; el salto aparece al combinar los 4 meses
> con lag 1 y delta 1 de todas las variables, que describen a cada cliente "en movimiento" de la misma forma
> en todos los meses (las señales de verscla05 dependen de lags 2 y 3, vacíos en marzo y abril).
>
> ## Cómo reproducir
> **`verscla09.py`** es el script único y autocontenido de la entrega final: lee el crudo, arma la clase y las
> variables, entrena con 202103–202106 y escribe el CSV. No depende de ningún otro archivo.
> ```bash
> python verscla09.py                 # entrega: entregas_verscla09/verscla09_k13000.csv + 10 archivos por semilla
> python verscla09.py --validar       # además: ganancia en 202106 entrenando con 202103-202104
> ```
> Los scripts de trabajo con los que se llegó (dependen de `resultados/base/` de competencia_v5):
> ```bash
> python pipeline_v8.py --solo-final --features todas --semillas-final 10 --k 13000 --nombre verscla09
> python pipeline_v8.py --solo-final --semillas-final 10 --k 13000                     # verscla08
> python pipeline_v8.py --solo-validacion --features todas                           # validación en 202106
> ```
> Hiperparámetros: los de verscla05 (`resultados/base/config.json`), 655 árboles.
>
> ## Experimentos descartados en el camino (`registro.csv`, medidos en 202106)
> Variables bancarias del agente, ranking (`rank_xendcg`, `lambdarank`), null importance, hojas de
> Random Forest (fuga de información), pesos para BAJA+2, ensamble con verscla02: ninguno superó
> a verscla07 por más de 10 M. Todos los enfoques quedaron entre 426 y 436 M en junio: el techo estaba
> en los datos de entrenamiento de la entrega, no en el modelo.
>
> ## Archivos
> - `entregas/verscla09_k13000.csv`: **entrega final** (13.000 ids, sin encabezado).
> - `entregas/verscla09_semillas/`: 10 archivos, uno por semilla (envío `verscla09.semillas`).
> - `entregas/verscla08_*`: la variante con 203 variables.

