# Rodrigo — entrega de la Primera Competencia DMEyF 2026

- Usuario de GitHub: RodPalDS
- Repositorio: https://github.com/RodPalDS/DMEF-Primera-Competencia-2026
- Link posteado: https://github.com/RodPalDS/DMEF-Primera-Competencia-2026/tree/main
- Commit: 28be952e0e04d4c1146d403fa4f89d6632c45e93
- Estado de la lectura: verificada
- Página: https://emavaldez.github.io/postmortem/entregas/rodpalds/
- Datos: https://emavaldez.github.io/postmortem/data/entregas/rodpalds.json

## Resumen

Repositorio en Python con 22 scripts numerados, un módulo de registro de experimentos (exp_utils.py), 54 configuraciones JSON, 14 lotes .bat para Windows y la carpeta exp/ con parámetros, resultados y copia del script de 66 experimentos; trae README, informe técnico y el CSV enviado. El camino de la entrega (experimento 5015) arma la clase ternaria y dos clases binarias (01_preparar_dataset.py); genera el dataset ds3003 con lag1, lag2, delta1 y delta2 de las 152 variables y seis variables propias sobre productos en cero o NA, y reemplaza todas las columnas por su ranking dentro del mes con cero fijo (03c_fe_extra.py); entrena un LightGBM binario (positivo = BAJA+1 o BAJA+2) con 202103 a 202106, sin submuestreo, con 50 semillas cuyas probabilidades se promedian (07_modelo_final.py). Los hiperparámetros (la «prueba 23») salen de búsquedas con Optuna que entrenan con meses anteriores y miden la ganancia en dos mitades fijas de 202106 (08_bo_fuera_de_tiempo.py); min_data_in_leaf se multiplica por la relación entre cantidades de meses de entrenamiento (20.248 × 2 = 40.496). 10_entrega_zulip.py escribe las listas para el bot; se entregan los 12.500 clientes de 202108 de mayor probabilidad promedio. Los demás scripts son diagnósticos, variantes de variables, comparaciones y ensambles; el README detalla cuáles de esas pruebas se adoptaron y cuáles no.

**Qué entrega.** entrega_final/Z6011_5015_e12500_final2.csv: 12.500 numero_de_cliente de 202108, uno por línea, sin encabezado. Sus 12.500 ids son los de mayor «prob» en exp/5015_prod_profesor_mar_jun/5015_probabilidades.csv (164.647 clientes), archivo que también está en el repositorio. Según el README, es copia de exp/6011_zulip_final_5015/zulip/Z6011_5015_e12500_semillerio.csv (carpeta no versionada) y corresponde al envío «submit 5015e12500final2» del 11/10/2026 20:14, con ganancia pública 95,59. El README (línea 55) y el informe técnico nombran la copia como Z6011_5015_e12500_final.csv; en el repositorio el archivo se llama Z6011_5015_e12500_final2.csv.

**Cómo se ejecuta.** El README (sección 3) indica: Python 3.12 y «pip install -r requirements.txt»; colocar competencia_01_crudo.csv en data/ (no incluido); definir DMEYF_ROOT con la carpeta del repositorio («set DMEYF_ROOT=%CD%» en Windows, «export DMEYF_ROOT=$(pwd)» en Linux). Camino corto (1 a 2 h según el README), cuatro comandos en orden: «py -3.12 01_preparar_dataset.py», «py -3.12 03c_fe_extra.py», «py -3.12 07_modelo_final.py configs/5015_prod_profesor_mar_jun.json» y «py -3.12 10_entrega_zulip.py configs/6011_zulip_final_5015.json»; usa los hiperparámetros guardados en exp/4107_bo_profesor_mar_abr/4107_eleccion.json. Camino completo: antes de esos cuatro, «03b_fe_rank_total.py», «08_bo_fuera_de_tiempo.py configs/4104_bo_rank_total.json» y «08_bo_fuera_de_tiempo.py configs/4107_bo_profesor_mar_abr.json». Los .bat encadenan los mismos scripts en Windows (profesor_final.bat corre 5107, 4107, 5015 y 6011).

## Ficha

- **Lenguajes:** Python, Batch
- **Modelos:** LightGBM
- **Clase que entrena:** Binaria «clase_binaria2»: positivo = BAJA+1 o BAJA+2, negativo = CONTINUA (01_preparar_dataset.py, línea 97; configs/5015, clave «clase»). La clase ternaria se arma en el mismo script a partir de los dos registros siguientes de cada cliente. La ganancia de las validaciones se calcula sólo con BAJA+2.
- **Meses de entrenamiento:** 202103, 202104, 202105, 202106
- **Meses de validación:** 202106
- **Mes que predice:** 202108
- **Submuestreo:** No se observa en el código. 07_modelo_final.py entrena con todas las filas de los meses indicados; el README declara 654.066 filas de 202103 a 202106 «sin undersampling».
- **Calidad de datos:** En el camino de la entrega no se corrigen ni se anulan variables. 01_preparar_dataset.py detiene la corrida si hay filas cliente-mes repetidas y verifica que el Parquet grabado conserve filas, columnas y nulos; 03c_fe_extra.py mantiene los NA y los ceros al rankear. Según el README, ds3003 no pone ccajas_depositos en NA en 202105. En archivos de exploración: 03f_fe_profesor.py pasa ccajas_depositos a NA en 202105 y configs/5023 excluye Master_Finiciomora, Visa_Finiciomora, Master_fultimo_cierre y Visa_fultimo_cierre con sus lags y deltas.
- **Drifting:** Todas las columnas del dataset (las 152 originales, sus lags y deltas y las 6 variables nuevas) se reemplazan por su ranking percentil dentro de cada mes con cero fijo: positivos en (0,1], negativos en [−1,0) según su valor absoluto, cero = 0, NA = NA, empates por promedio (03c_fe_extra.py, función rank_cero_fijo). Los lags y deltas se calculan antes, sobre los valores sin transformar.
- **Variables dentro del mes:** n_apagados: cantidad de 16 variables clave que en el mes valen 0 o NA (ctrx_quarter, mpasivos_margen, mcaja_ahorro, mcuentas_saldo, ctarjeta_visa_transacciones, ctarjeta_master_transacciones, ctarjeta_debito_transacciones, mprestamos_personales, mpayroll, cmobile_app_trx, chomebanking_transacciones, mcomisiones, cdescubierto_preacordado, mcuenta_corriente, Visa_msaldototal y Master_msaldototal).
- **Variables históricas:** Para cada una de las 152 variables: lag1 y lag2 (valor del mismo cliente exactamente 1 y 2 meses antes; NA si ese mes no existe) y delta1 y delta2 (valor actual menos el lag). Además: n_apagados_delta1 y n_apagados_delta2; n_dejo_de_usar (variables clave con valor distinto de 0 hace 1 o 2 meses que hoy están en 0 o NA); ctrx_quarter_rel_max3 y mcaja_ahorro_rel_max3 (valor del mes dividido por el máximo entre el mes y los dos anteriores). Total: 152 × 5 + 6 = 766 variables.
- **Selección de variables:** No se observa en el camino de la entrega: configs/5015 tiene «variables» nulo y «usar_lag2» verdadero, por lo que 07_modelo_final.py usa todas las columnas del dataset salvo identificador, mes y clases. En archivos de exploración, 05_canaritos.py arma listas de variables cuya importancia supera a la de 100 columnas de azar (usadas en experimentos anteriores, como 5005).
- **Optimización de hiperparámetros:** Optuna (TPESampler) en 08_bo_fuera_de_tiempo.py, maximizando la «meseta»: ganancia promedio entre 12.000 y 17.000 envíos equivalentes al mes completo, medida en la mitad A de 202106 con corte temprano (hasta 3.000 árboles, paciencia 50 + 5/learning_rate). Búsqueda 4104: entrena con 202104 sobre ds3002, 40 pruebas (12 iniciales al azar), rangos learning_rate 0,01–0,2, num_leaves 8–256, min_data_in_leaf 100–20.000, feature_fraction 0,05–1 y bagging_fraction 0,05–1; de ella sale la prueba 23. Búsqueda 4107: entrena con 202103 + 202104 sobre ds3003, 50 pruebas (15 iniciales), num_leaves 8–2.000, min_data_in_leaf 1–20.000, feature_fraction 0,05–0,9, bagging_fraction 0,05–1 y learning_rate 0,01–0,2, con la prueba 23 como referencia. En la etapa 2 las 5 pruebas de mayor meseta en A y las referencias se entrenan con 20 semillas y se miden en la mitad B; el retador reemplaza a la referencia sólo si la supera en promedio y en al menos 14 de 20 semillas. 4107_eleccion.json registra como elegida la referencia p23_4104.
- **Hiperparámetros finales:** Según exp/5015_prod_profesor_mar_jun/5015_params_lightgbm.json: objective binary, boosting_type gbdt, learning_rate 0,0678, num_leaves 41, min_data_in_leaf 40.496 (20.248 × 2), feature_fraction 0,1798, bagging_fraction 0,3124, bagging_freq 1, lambda_l1 0,001, lambda_l2 0,001, max_bin 31, feature_pre_filter false, deterministic true, force_row_wise true; 580 árboles, sin corte temprano en el entrenamiento final.
- **Semillas:** 50 semillas: las cinco de «semillas_base» (571369, 849571, 355049, 655531, 700103) más 45 números primos entre 100003 y 999983 sorteados con numpy.random.default_rng(571369) (07_modelo_final.py, líneas 92-105). La lista queda grabada en exp/5015_prod_profesor_mar_jun/5015_semillas.csv.
- **Cantidad de semillas:** 50
- **Ensamble:** Semillerío: el mismo LightGBM se entrena 50 veces cambiando sólo la semilla y se promedian las probabilidades por cliente (07_modelo_final.py, líneas 225-260). En la entrega no se combinan modelos con hiperparámetros distintos.
- **Corte:** Cantidad fija: los 12.500 clientes de mayor probabilidad promedio. 10_entrega_zulip.py genera una lista por cada cantidad de configs/6011 (11.000, 11.500, 12.000, 12.500, 13.000 y 13.500). Según el README (sección 5), se elige 12.500 como punto medio entre lo que indica el puntaje público (12.000) y lo que muestran las curvas de ganancia en junio (12.500 a 15.000).
- **Validación:** Fuera de tiempo: se entrena con 202103 + 202104 (sólo 202104 en la búsqueda 4104) y se mide en 202106. Los clientes de 202106 se dividen en dos mitades fijas, A y B, estratificadas por clase ternaria (semilla 571369; se reutilizan desde exp/4102_bo_fuera_de_tiempo/4102_mitades_junio.csv): la búsqueda mide en la mitad A y la confirmación con 20 semillas mide en la mitad B. Métrica: «meseta», ganancia promedio entre 12.000 y 17.000 envíos equivalentes al mes completo, con +1.072.500 por cada BAJA+2 y −27.500 por el resto. El modelo final no tiene validación propia: entrena con 202103–202106 y predice 202108.
- **Salidas:** 07_modelo_final.py (5015): 5015_probabilidades.csv (numero_de_cliente, prob), 5015_semillas.csv, 5015_params_lightgbm.json, 5015_importancia.csv (gain de la primera semilla) y 13 archivos kaggle/KA5015_e<N>.csv con columna Predicted, para N de 9.000 a 15.000 cada 500. 10_entrega_zulip.py (6011): seis archivos zulip/Z6011_5015_e<N>_semillerio.csv con un id por línea y sin encabezado, y cuerpo_mensaje.txt. Cada experimento agrega una fila a exp/registro_experimentos.csv.

## Técnicas en el camino de la entrega

- LightGBM (`modelo.lightgbm`)
- Clase binaria: positivo = BAJA+1 o BAJA+2 (`clase.binaria_baja1_baja2`)
- Rank con cero fijo (`drifting.rank_cero_fijo`)
- Variables nuevas dentro del mes (sumas, cocientes, combinaciones) (`variables.intra_mes`)
- Lags (`variables.lags`)
- Deltas (diferencia con meses anteriores) (`variables.deltas`)
- Cocientes contra valores anteriores o contra la ventana (`variables.ratios_historia`)
- Optuna (`hiperparametros.optuna`)
- Validación en un mes posterior al entrenamiento (`validacion.mes_futuro`)
- Usa la ganancia de la competencia como métrica (`validacion.ganancia_como_metrica`)
- Promedio de varias semillas del mismo modelo (`ensamble.semillerio`)
- Envía una cantidad fija de clientes (`corte.cantidad_fija`)
- Genera archivos con varios cortes (`corte.varios_cortes`)
- El modelo final se reentrena sumando los meses usados para validar (`final.reentrena_con_todo`)
- Incluye bitácora o registro de experimentos (`proceso.bitacora`)
- El repositorio declara el uso de asistentes de IA (`proceso.uso_de_ia_declarado`)
- Mínimos y máximos de ventana (`variables.min_max_ventana`)

## Técnicas sólo exploradas

- Clase binaria: positivo = BAJA+2 (`clase.binaria_baja2`)
- Variables rotas en algún mes pasadas a NA o corregidas (`datos.variables_rotas_a_na`)
- Excluye variables a mano (por ejemplo préstamos personales) (`datos.excluye_variables`)
- Estandarización o normalización por mes (`drifting.estandarizacion_por_mes`)
- Tendencias (pendiente en una ventana) (`variables.tendencias`)
- Promedios móviles o de ventana (`variables.promedios_ventana`)
- Canaritos (variables al azar para medir ruido) (`variables.canaritos`)
- Selección de variables por importancia (`variables.seleccion_por_importancia`)
- Hiperparámetros fijos escritos en el código (`hiperparametros.fijos`)
- Validación cruzada (`validacion.validacion_cruzada`)
- Partición aleatoria de entrenamiento y validación (`validacion.particion_aleatoria`)
- Combina modelos o configuraciones distintas (`ensamble.modelos_distintos`)
- El corte sale de una curva de ganancia en meses con clase (`corte.elegido_en_validacion`)

## Reproducibilidad (hechos)

- Tiene README o texto de presentación: sí
- Explica cómo ejecutar: sí
- Declara versiones o dependencias: sí
- Fija las semillas: sí
- Usa rutas absolutas o de una máquina: sí
- Incluye datos o predicciones: sí
- Sale de un solo script o notebook: no
- Entorno declarado: README: Windows o Linux con Python 3.12 y unos 16 GB de RAM. requirements.txt: lightgbm 4.7.0, numpy 2.5.2, optuna 5.0.0, pandas 3.0.5, plotly 7.1.0, pyarrow 24.0.0 y scipy 1.18.1 (su comentario inicial pide reemplazar las versiones por la salida de pip freeze). Los .bat usan «py -3.12» en Windows. exp_utils.py toma la carpeta del proyecto de la variable DMEYF_ROOT y, si no está definida, de una ruta de Windows escrita en el código.

## Pasos del camino de la entrega

1. **Lectura del crudo y clase ternaria.** 01_preparar_dataset.py lee competencia_01_crudo.csv, detiene la corrida si el archivo ya trae clase_ternaria o si hay filas cliente-mes repetidas, y arma la clase ternaria: convierte foto_mes en un número de período consecutivo, toma los dos registros siguientes de cada cliente y asigna CONTINUA, BAJA+1 (falta el registro del mes siguiente) o BAJA+2 (existe el mes siguiente y falta el de dos meses después). 202107 queda sólo con BAJA+1 y 202108 sin clase. (`01_preparar_dataset.py` líneas 43–54; `01_preparar_dataset.py` líneas 64–88)
2. **Clases binarias, controles y grabado en Parquet.** Agrega clase_binaria1 (1 = BAJA+2) y clase_binaria2 (1 = BAJA+1 o BAJA+2), nulas donde la ternaria es nula. Verifica por aserciones qué meses tienen clase completa y graba data/ds1001_base.parquet con zstd; relee el archivo y compara forma y cantidad de nulos. exp/1001_dataset_base/1001_resultados.json registra 983.061 filas, 157 columnas y clase completa en 202103–202106. (`01_preparar_dataset.py` líneas 95–97; `01_preparar_dataset.py` líneas 110–119; `01_preparar_dataset.py` líneas 131–142)
3. **Dataset ds3002: lags, deltas y ranking por mes.** 03b_fe_rank_total.py ordena por cliente y mes, calcula lag1, lag2, delta1 y delta2 de cada variable sobre los valores originales y reemplaza todas las columnas por su ranking dentro del mes con cero fijo. Graba ds3002_rank_total.parquet, el dataset sobre el que corre la búsqueda 4104. (`03b_fe_rank_total.py` líneas 65–92; `03b_fe_rank_total.py` líneas 102–116)
4. **Mitades de junio y métrica de la búsqueda.** 08_bo_fuera_de_tiempo.py separa los clientes de 202106 en dos mitades, A y B, estratificadas por clase ternaria (o las relee de un experimento anterior con «mitades_desde») y define la «meseta»: ganancia acumulada promedio entre 6.000 y 8.500 envíos de la mitad, multiplicada por 2, que equivale a 12.000–17.000 envíos del mes completo. (`08_bo_fuera_de_tiempo.py` líneas 134–152; `08_bo_fuera_de_tiempo.py` líneas 164–172)
5. **Búsqueda 4104 con Optuna: aparece la prueba 23.** Con configs/4104_bo_rank_total.json, cada prueba de Optuna (TPE, 40 pruebas, 12 iniciales al azar) entrena con 202104 sobre ds3002 y se mide en la mitad A con corte temprano; z601 y p117_4102 entran como primeras pruebas y como referencias. La prueba 23 de esta búsqueda (learning_rate 0,0678, num_leaves 41, min_data_in_leaf 10.124, feature_fraction 0,1798, bagging_fraction 0,3124 y 580 árboles, según exp/4104_bo_rank_total/4104_pruebas.csv) es la que después se copia como referencia «p23_4104». Según el informe técnico (S4), la regla de 4104 eligió la prueba 35 y la 23 se incorporó como referencia en las búsquedas siguientes. (`configs/4104_bo_rank_total.json` líneas 1–54; `08_bo_fuera_de_tiempo.py` líneas 178–204; `08_bo_fuera_de_tiempo.py` líneas 217–222)
6. **Dataset ds3003: variables sobre productos en cero o NA.** 03c_fe_extra.py calcula, sobre valores sin transformar, n_apagados (cuántas de 16 variables clave valen 0 o NA en el mes), n_apagados_delta1 y n_apagados_delta2, n_dejo_de_usar (variables clave activas hace 1 o 2 meses y hoy en 0 o NA) y, para ctrx_quarter y mcaja_ahorro, el valor del mes dividido por el máximo de los últimos 3 meses. (`03c_fe_extra.py` líneas 144–167)
7. **Dataset ds3003: lags, deltas y ranking con cero fijo.** Para cada una de las 152 variables arma lag1, lag2, delta1 y delta2 (NA si el cliente no tiene fila exactamente k meses antes) y reemplaza cada columna, incluidas las 6 nuevas, por su ranking percentil dentro del mes: positivos en (0,1], negativos en [−1,0), cero en 0 y NA en NA. Graba ds3003_rank_extra.parquet con 771 columnas (5 de identificación y clase + 152 × 5 + 6). (`03c_fe_extra.py` líneas 103–131; `03c_fe_extra.py` líneas 205–226; `03c_fe_extra.py` líneas 243–255)
8. **Búsqueda 4107: 202103 + 202104 con la prueba 23 como referencia.** Con configs/4107_bo_profesor_mar_abr.json la búsqueda entrena con 202103 + 202104 sobre ds3003 (con lag2), 50 pruebas (15 iniciales al azar) y cinco hiperparámetros. Las referencias z601 y p23_4104 se encolan como primeras pruebas, con min_data_in_leaf multiplicado por la cantidad de meses de entrenamiento (10.124 × 2 = 20.248) y recortado al borde del rango de búsqueda al encolarse. (`configs/4107_bo_profesor_mar_abr.json` líneas 1–62; `08_bo_fuera_de_tiempo.py` líneas 223–246)
9. **Confirmación en la mitad B y elección de hiperparámetros.** Las 5 pruebas de mayor meseta en A y las referencias se entrenan con 20 semillas y cantidad fija de árboles, y se miden en la mitad B. El retador (la prueba de mayor meseta en A) reemplaza a la referencia de mayor meseta media en B sólo si la supera en promedio y en al menos 14 de 20 semillas. 4107_eleccion.json registra como elegida «4107 p23_4104» (retador prueba_42, 3/20 semillas), con min_data_in_leaf 20.248, 580 árboles y fraccion_mes_referencia 2,0. (`08_bo_fuera_de_tiempo.py` líneas 251–276; `08_bo_fuera_de_tiempo.py` líneas 308–336; `exp/4107_bo_profesor_mar_abr/4107_eleccion.json` líneas 1–31)
10. **Configuración del modelo final 5015.** 07_modelo_final.py recibe configs/5015_prod_profesor_mar_jun.json, cuyas claves reemplazan el PARAM por defecto: modo «produccion», dataset ds3003, clase_binaria2, entrenamiento 202103–202106, predicción 202108, 50 semillas, todas las variables con lag2 y los hiperparámetros de 4107_eleccion.json. (`configs/5015_prod_profesor_mar_jun.json` líneas 1–50; `07_modelo_final.py` líneas 67–71; `07_modelo_final.py` líneas 115–120)
11. **Semillas del semillerío.** La lista de semillas arranca con las cinco de «semillas_base» y se completa hasta 50 con primos entre 100003 y 999983 sorteados con un generador de numpy inicializado con la primera semilla; se graba en 5015_semillas.csv. (`07_modelo_final.py` líneas 92–105)
12. **Datos de entrenamiento y escalado de min_data_in_leaf.** Lee del Parquet sólo los meses de entrenamiento y el de predicción, verifica que el entrenamiento tenga todos los meses y ninguna fila sin clase, y multiplica min_data_in_leaf por el cociente entre los meses de entrenamiento (4) y los usados al elegir los hiperparámetros (2): 20.248 pasa a 40.496. Graba los parámetros en 5015_params_lightgbm.json y arma el lgb.Dataset con la etiqueta clase_binaria2. (`07_modelo_final.py` líneas 153–160; `07_modelo_final.py` líneas 172–181; `07_modelo_final.py` líneas 186–191; `07_modelo_final.py` líneas 203–207)
13. **Entrenamiento de 50 modelos y promedio de probabilidades.** Para cada semilla entrena un LightGBM de 580 árboles con todo el entrenamiento, predice 202108 y acumula las probabilidades; de la primera semilla guarda la importancia (gain). La probabilidad final es la suma dividida por la cantidad de semillas y se graba en 5015_probabilidades.csv. (`07_modelo_final.py` líneas 232–244; `07_modelo_final.py` líneas 256–264)
14. **Archivos por cantidad de envíos (formato Kaggle).** En modo producción ordena a los clientes por probabilidad promedio y, para cada cantidad de «envios» (9.000 a 15.000 cada 500), escribe kaggle/KA5015_e<N>.csv con Predicted = 1 en los N primeros. (`07_modelo_final.py` líneas 315–333)
15. **Listas para el bot y corte de 12.500.** 10_entrega_zulip.py lee 5015_probabilidades.csv, verifica probabilidades finitas, ids enteros y únicos y 164.647 clientes, y por cada cantidad de configs/6011 (11.000 a 13.500 cada 500) escribe los ids de mayor probabilidad, uno por línea y sin encabezado; relee cada archivo y verifica cantidad, formato y ausencia de repetidos. El archivo de 12.500 es el que el README indica como entregado. (`configs/6011_zulip_final_5015.json` líneas 1–15; `10_entrega_zulip.py` líneas 66–82; `10_entrega_zulip.py` líneas 89–105)
16. **Registro de cada experimento.** Todos los scripts llaman a iniciar_experimento, que crea exp/<id>_<nombre>/ y guarda el PARAM y una copia del script, y a cerrar_experimento, que guarda los resultados y agrega una fila a exp/registro_experimentos.csv. profesor_final.bat encadena en Windows los pasos 5107, 4107, 5015 y 6011. (`exp_utils.py` líneas 61–92; `exp_utils.py` líneas 109–126; `profesor_final.bat` líneas 34–39)

## Archivos

- `muerte_ampliada.bat` · secundario · Batch · 55 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/muerte_ampliada.bat.txt) — Lote: dataset 3006, comparación 5108, producciones 5016 y 5017, búsqueda 4108 y archivos 6012 y 6013.
- `informe_tecnico.md` · explicacion · Markdown · 267 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/informe_tecnico.md.txt) — Informe técnico fechado el 11/10/2026: resumen de la entrega, pipeline de 5015 paso a paso, tabla de candidatos de la búsqueda 4107, tabla de reglas de decisión (R1, R3, R4, R6, R7, R8 y R9), historial de 11 submits con su ganancia pública, experimentos de la última semana y 12 supuestos y desvíos declarados (S1 a S12). Declara asistencia de IA (Claude).
- `profesor2.bat` · secundario · Batch · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/profesor2.bat.txt) — Lote: búsqueda 4105, comparación 5103, producción 5011 y archivos 6007.
- `fe_profesor.bat` · secundario · Batch · 75 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/fe_profesor.bat.txt) — Lote reanudable: evaluación 5114 y, sólo si existe 5114_ADOPTAR.txt, producción 5022 y archivos 6018.
- `noche.bat` · secundario · Batch · 51 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/noche.bat.txt) — Lote: simulaciones 5001 y 5002, producciones 5003 y 5004, búsqueda 4102 y producción 5005.
- `profesor.bat` · secundario · Batch · 51 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/profesor.bat.txt) — Lote: diagnóstico 2002, dataset 3002 (03b_fe_rank_total.py), búsqueda 4104, comparación 5102, producción 5008 y archivos 6003 y 6004.
- `receta_final.bat` · secundario · Batch · 48 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/receta_final.bat.txt) — Lote: búsqueda 4106, producción 5013 y archivos 6009.
- `02_diagnostico_aguinaldo.py` · secundario · Python · 227 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/02_diagnostico_aguinaldo.py.txt) — Experimento 2001: mide en las variables de payroll la relación entre el sueldo de un mes y el del anterior, la proporción de clientes con un salto de entre 1,3 y 1,7 veces por mes y la tasa de bajas según ese salto, con gráficos HTML.
- `01_preparar_dataset.py` · principal · Python · 150 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/01_preparar_dataset.py.txt) — Experimento 1001: lee el CSV crudo, construye clase_ternaria, clase_binaria1 y clase_binaria2, hace controles sobre la clase y graba data/ds1001_base.parquet.
- `requirements.txt` · configuracion · Texto · 9 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/requirements.txt.txt) — Lista de 7 paquetes con versión fija: lightgbm 4.7.0, numpy 2.5.2, optuna 5.0.0, pandas 3.0.5, plotly 7.1.0, pyarrow 24.0.0 y scipy 1.18.1. Su comentario inicial indica Python 3.12 y pide reemplazar las versiones por la salida de pip freeze.
- `03c_fe_extra.py` · principal · Python · 265 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/03c_fe_extra.py.txt) — Experimento 3003: genera ds3003_rank_extra.parquet, el dataset del modelo entregado: lags y deltas de orden 1 y 2 de las 152 variables, seis variables nuevas sobre productos en cero o NA y ranking de todas las columnas dentro del mes con cero fijo.
- `10_entrega_zulip.py` · principal · Python · 124 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/10_entrega_zulip.py.txt) — Experimentos 6xxx: a partir de las probabilidades de una producción escribe, para cada cantidad de envíos, un archivo con los numero_de_cliente de mayor probabilidad, uno por línea y sin encabezado, y verifica su formato. Con configs/6011 genera las listas de 5015, entre ellas la de 12.500.
- `fe_extra.bat` · secundario · Batch · 40 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/fe_extra.bat.txt) — Lote: genera ds3003 con 03c_fe_extra.py (3003) y corre la comparación 5104 contra ds3002.
- `03_feature_engineering.py` · secundario · Python · 185 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/03_feature_engineering.py.txt) — Experimento 3001: genera tres datasets con lags y deltas de orden 1 y 2 que difieren en el tratamiento de los montos: sin cambios (ds3001_crudo), divididos por la mediana de la variable en el mes (ds3001_mediana) y reemplazados por su posición relativa en el mes con cero fijo (ds3001_rank).
- `08_bo_fuera_de_tiempo.py` · principal · Python · 350 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/08_bo_fuera_de_tiempo.py.txt) — Búsqueda de hiperparámetros con Optuna (experimentos 4102 a 4109 según la configuración): entrena con meses anteriores, mide la ganancia de meseta en la mitad A de 202106, confirma con varias semillas en la mitad B y graba <id>_eleccion.json. Con configs/4104 y configs/4107 produce los hiperparámetros del modelo entregado.
- `tarde.bat` · secundario · Batch · 42 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/tarde.bat.txt) — Lote: búsqueda 4103, curvas 5101 y producción 5006.
- `03d_fe_variantes.py` · secundario · Python · 278 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/03d_fe_variantes.py.txt) — Experimentos 3004 y 3005: variantes del dataset: rankear antes de calcular lags y deltas, y agregar un indicador por producto «dejo_<variable>» además de los conteos, con o sin ranking de las variables nuevas.
- `profesor_final.bat` · principal · Batch · 51 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/profesor_final.bat.txt) — Lote de Windows que encadena la comparación 5107, la búsqueda 4107, el modelo final 5015 y los archivos 6011, con un log por paso en logs/.
- `16_bo_profesor_v2.py` · secundario · Python · 250 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/16_bo_profesor_v2.py.txt) — Experimentos 4111 y 4112: búsqueda con Optuna que maximiza el AUC promedio de 5 particiones 70/30 dentro de 202103 + 202104, con learning_rate 0,005, min_data_in_leaf 0, feature_fraction 0,5 y feature_fraction_bynode 0,2 fijos, y num_iterations, num_leaves y min_sum_hessian_in_leaf como hiperparámetros buscados.
- `09_curva_mitad_b.py` · secundario · Python · 216 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/09_curva_mitad_b.py.txt) — Experimento 5101: semillerío de 20 por candidato (z601 y las elecciones de 4102 y 4103) entrenado con 202104 y curva de ganancia en la mitad B de 202106, incluida la combinación de candidatos por promedio de rankings.
- `README.md` · explicacion · Markdown · 158 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/README.md.txt) — Presentación de la entrega: archivo entregado y submit, tabla del modelo, pasos para reproducir (camino corto y camino completo), protocolo de validación, elección del corte, tabla de las indicaciones del profesor evaluadas, otras pruebas, supuestos y desvíos declarados y estructura del repositorio.
- `04_comparar_datasets.py` · secundario · Python · 220 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/04_comparar_datasets.py.txt) — Experimentos 4001 y 4002: entrena el mismo LightGBM con hiperparámetros fijos (z601) con 202104 sobre distintos datasets y clases (clase_binaria1 o clase_binaria2), con 5 semillas, y compara la ganancia en 202106 para cantidades de envíos de 2.000 a 20.000.
- `06_optimizacion_bayesiana.py` · secundario · Python · 266 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/06_optimizacion_bayesiana.py.txt) — Experimento 4101: búsqueda con Optuna con validación cruzada de 5 particiones dentro de 202104 midiendo ganancia suavizada; los 5 candidatos de mayor valor se entrenan con todo el mes y se miden en 202106 con 5 semillas.
- `03f_fe_profesor.py` · secundario · Python · 259 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/03f_fe_profesor.py.txt) — Experimento 3007: ds3003 más ccajas_depositos en NA en 202105, indicadores <var>_zero sin rankear y, por variable, tendencia (pendiente de cuadrados mínimos) y promedio de 3 meses (_tend3 y _avg3); procesa y graba mes por mes.
- `final_limpio.bat` · secundario · Batch · 101 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/final_limpio.bat.txt) — Lote reanudable con dependencias entre pasos: comparación 5109, decisión 7001, búsqueda 4109, comparación 5110, decisión 7002, producción 5018 y archivos 6014; cada paso terminado deja logs\ok_<id>.txt.
- `variantes.bat` · secundario · Batch · 51 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/variantes.bat.txt) — Lote: datasets 3004 y 3005 y comparaciones 5105 y 5106.
- `ensamble2.bat` · secundario · Batch · 35 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/ensamble2.bat.txt) — Lote: ensamble 5202 (12_ensamble.py) y archivos 6008.
- `03b_fe_rank_total.py` · principal · Python · 149 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/03b_fe_rank_total.py.txt) — Experimento 3002: genera ds3002_rank_total.parquet con lags y deltas de orden 1 y 2 y ranking de todas las columnas dentro de cada mes con cero fijo. Es el dataset de la búsqueda 4104, de la que sale la prueba 23 (camino completo del README).
- `07_modelo_final.py` · principal · Python · 335 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/07_modelo_final.py.txt) — Semillerío de LightGBM (experimentos 5xxx): con configs/5015 entrena 50 modelos con 202103–202106, promedia las probabilidades de 202108 y graba 5015_probabilidades.csv y un archivo por cantidad de envíos. Tiene además un modo «simulacion» que mide la ganancia en un mes con clase.
- `05_canaritos.py` · secundario · Python · 218 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/05_canaritos.py.txt) — Experimento 4003: agrega 100 columnas uniformes al azar al entrenamiento de 202104, promedia la importancia (gain) en 5 semillas y arma las listas de variables que superan el percentil 95 y el máximo de los canaritos; después compara la ganancia en 202106 de entrenar con todas las variables, con la lista p95 y con la lista max.
- `opcion_a.bat` · secundario · Batch · 30 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/opcion_a.bat.txt) — Lote: producción 5023 (igual a 5015 sin las variables Finiciomora y fultimo_cierre de Master y Visa, con 30 semillas) y archivo 6019 de 12.500 envíos.
- `18_ensamble_profesor.py` · secundario · Python · 350 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/18_ensamble_profesor.py.txt) — Experimentos 5113 y 5021: ensamble por promedio de probabilidades de las 12 pruebas de mayor AUC de 4112; en modo evaluación lo entrena con 202103 + 202104 y lo mide en 202106 contra el semillerío de la prueba 23, y en modo producción entrena con 202103–202106 y predice 202108.
- `exp_utils.py` · principal · Python · 126 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp_utils.py.txt) — Módulo común que importan todos los scripts: define las rutas del proyecto y las funciones iniciar_experimento y cerrar_experimento, que crean la carpeta de cada experimento, guardan parámetros, copia del script y resultados, y mantienen exp/registro_experimentos.csv.
- `12_ensamble.py` · secundario · Python · 105 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/12_ensamble.py.txt) — Experimentos 5201 y 5202: convierte las probabilidades de 202108 de varias producciones en ranking percentil, las promedia y graba un <id>_probabilidades.csv con el mismo formato que 07_modelo_final.py.
- `19_eval_dataset.py` · secundario · Python · 155 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/19_eval_dataset.py.txt) — Experimento 5114: con los hiperparámetros de 4107_eleccion.json y 20 semillas, entrena con 202103 + 202104 sobre ds3003 y sobre ds3007 y compara la meseta en 202106 completo; aplica la regla R8 de su docstring.
- `11_comparar_pipelines.py` · secundario · Python · 257 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/11_comparar_pipelines.py.txt) — Experimentos 5102 a 5110: compara candidatos (dataset, variables, hiperparámetros, meses de entrenamiento) con semillerío en la mitad B de 202106; calcula meseta, curva por envíos, bootstrap pareado de 1.000 remuestreos contra la referencia y la distribución de la cantidad de envíos de mayor ganancia.
- `estrategia_profesor.bat` · secundario · Batch · 99 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/estrategia_profesor.bat.txt) — Lote reanudable: dataset 3007, búsqueda 4112, evaluación 5113, ensamble 5021 y archivos 6017.
- `13_decidir.py` · secundario · Python · 147 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/13_decidir.py.txt) — Experimentos 7001 y 7002: lee los resúmenes de 5109 y 5110, aplica las reglas R3, R4 y R5 escritas en su docstring y escribe las configuraciones del paso siguiente (5110, 5018 y 6014).
- `02b_diagnostico_ceros_na.py` · secundario · Python · 106 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/02b_diagnostico_ceros_na.py.txt) — Experimento 2002: para cada variable, en 202103–202106, calcula la tasa de BAJA+2 y el lift de los grupos NA, cero, negativo y positivo y, para los BAJA+2, cuántos meses antes queda en cero o vacío cada producto de una lista de 10.
- `03e_fe_muerte_ampliada.py` · secundario · Python · 324 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/03e_fe_muerte_ampliada.py.txt) — Experimento 3006: ds3003 más conteos de variables en cero o NA sobre unos 45 productos, conteos por grupo de productos (7 grupos), un puntaje ponderado por log(lift) calculado con 202103–202104 y cocientes contra el máximo de 3 meses para 8 variables más.
- `configs/4107_bo_profesor_mar_abr.json` · configuracion · JSON · 62 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/4107_bo_profesor_mar_abr.json.txt) — Configuración de la búsqueda 4107: ds3003 con lag2, entrenamiento 202103 + 202104, prueba 202106, mitades reutilizadas de 4102, 50 pruebas (15 iniciales), rangos de cinco hiperparámetros, referencia extra p23_4104 (learning_rate 0,0678, num_leaves 41, min_data_in_leaf 10.124, feature_fraction 0,1798, bagging_fraction 0,3124, 580 árboles), 5 candidatos a confirmar con 20 semillas y mínimo de 14 semillas ganadas.
- `configs/4106_bo_receta_muerte.json` · configuracion · JSON · 83 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/4106_bo_receta_muerte.json.txt)
- `configs/5015_prod_profesor_mar_jun.json` · configuracion · JSON · 50 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5015_prod_profesor_mar_jun.json.txt) — Configuración del modelo entregado: modo produccion, ds3003_rank_extra.parquet, clase_binaria2, meses 202103–202106, predicción 202108, 50 semillas, «variables» nulo con usar_lag2, hiperparámetros desde 4107_eleccion.json, escalado de min_data_in_leaf activado y envíos de 9.000 a 15.000 cada 500.
- `configs/6007_zulip_final_5011.json` · configuracion · JSON · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6007_zulip_final_5011.json.txt)
- `configs/4103_bo_ampliada.json` · configuracion · JSON · 60 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/4103_bo_ampliada.json.txt)
- `configs/3005_fe_rank_luego_lag.json` · configuracion · JSON · 9 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/3005_fe_rank_luego_lag.json.txt)
- `configs/5003_prod_z601_todas.json` · configuracion · JSON · 48 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5003_prod_z601_todas.json.txt)
- `configs/3004_fe_flags.json` · configuracion · JSON · 9 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/3004_fe_flags.json.txt)
- `configs/6004_zulip_semillas_rank.json` · configuracion · JSON · 8 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6004_zulip_semillas_rank.json.txt)
- `configs/6005_zulip_cortes_5005.json` · configuracion · JSON · 8 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6005_zulip_cortes_5005.json.txt)
- `configs/6018_zulip_final_5022.json` · configuracion · JSON · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6018_zulip_final_5022.json.txt)
- `configs/5002_sim_z601_todas.json` · configuracion · JSON · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5002_sim_z601_todas.json.txt)
- `configs/5107_comparar_marzo.json` · configuracion · JSON · 32 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5107_comparar_marzo.json.txt)
- `configs/6017_zulip_final_5021.json` · configuracion · JSON · 19 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6017_zulip_final_5021.json.txt)
- `configs/5113_eval_ensamble.json` · configuracion · JSON · 17 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5113_eval_ensamble.json.txt)
- `configs/4108_bo_muerte_ampliada.json` · configuracion · JSON · 62 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/4108_bo_muerte_ampliada.json.txt)
- `configs/4112_bo_profesor_ds3007.json` · configuracion · JSON · 17 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/4112_bo_profesor_ds3007.json.txt)
- `configs/5008_prod_rank_total.json` · configuracion · JSON · 50 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5008_prod_rank_total.json.txt)
- `configs/6001_zulip_final.json` · configuracion · JSON · 8 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6001_zulip_final.json.txt)
- `configs/5004_prod_z601_p95.json` · configuracion · JSON · 48 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5004_prod_z601_p95.json.txt)
- `configs/5001_sim_z601_p95.json` · configuracion · JSON · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5001_sim_z601_p95.json.txt)
- `configs/5022_prod_p23_ds3007.json` · configuracion · JSON · 53 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5022_prod_p23_ds3007.json.txt)
- `configs/5108_comparar_muerte_ampliada.json` · configuracion · JSON · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5108_comparar_muerte_ampliada.json.txt)
- `configs/6013_zulip_final_5017.json` · configuracion · JSON · 15 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6013_zulip_final_5017.json.txt)
- `configs/5202_ensamble_5005_5011.json` · configuracion · JSON · 9 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5202_ensamble_5005_5011.json.txt)
- `configs/6014_zulip_final_5018.json` · configuracion · JSON · 16 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6014_zulip_final_5018.json.txt)
- `configs/5104_comparar_fe_extra.json` · configuracion · JSON · 25 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5104_comparar_fe_extra.json.txt)
- `configs/5106_lag2_entrenando_mayo.json` · configuracion · JSON · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5106_lag2_entrenando_mayo.json.txt)
- `configs/6011_zulip_final_5015.json` · configuracion · JSON · 15 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6011_zulip_final_5015.json.txt) — Configuración de los archivos para el bot: modo final, fuente 5015_prod_profesor_mar_jun y envíos 11.000, 11.500, 12.000, 12.500, 13.000 y 13.500.
- `configs/5110_comparar_bo4109.json` · configuracion · JSON · 38 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5110_comparar_bo4109.json.txt)
- `configs/5018_prod_final.json` · configuracion · JSON · 53 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5018_prod_final.json.txt)
- `configs/6019_zulip_final_5023.json` · configuracion · JSON · 11 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6019_zulip_final_5023.json.txt)
- `configs/5011_prod_rank_bo4105.json` · configuracion · JSON · 49 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5011_prod_rank_bo4105.json.txt)
- `configs/5023_prod_5015_sin_rotas.json` · configuracion · JSON · 59 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5023_prod_5015_sin_rotas.json.txt)
- `configs/5105_comparar_variantes_receta.json` · configuracion · JSON · 41 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5105_comparar_variantes_receta.json.txt)
- `configs/5006_prod_eleccion_4103.json` · configuracion · JSON · 50 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5006_prod_eleccion_4103.json.txt)
- `configs/5007_prod_p117_por_semilla.json` · configuracion · JSON · 43 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5007_prod_p117_por_semilla.json.txt)
- `configs/6008_zulip_final_ensamble_5202.json` · configuracion · JSON · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6008_zulip_final_ensamble_5202.json.txt)
- `configs/6003_zulip_final_rank.json` · configuracion · JSON · 16 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6003_zulip_final_rank.json.txt)
- `configs/4109_bo_limpia_profesor.json` · configuracion · JSON · 51 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/4109_bo_limpia_profesor.json.txt)
- `configs/4105_bo_rank_ampliada.json` · configuracion · JSON · 93 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/4105_bo_rank_ampliada.json.txt)
- `configs/5114_eval_dataset.json` · configuracion · JSON · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5114_eval_dataset.json.txt)
- `configs/6009_zulip_final_5013.json` · configuracion · JSON · 15 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6009_zulip_final_5013.json.txt)
- `configs/4104_bo_rank_total.json` · configuracion · JSON · 54 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/4104_bo_rank_total.json.txt) — Configuración de la búsqueda 4104: ds3002 con lag2, todas las variables, mitades reutilizadas de 4102, 40 pruebas (12 iniciales), rangos de cinco hiperparámetros y referencia extra p117_4102.
- `configs/5013_prod_receta_muerte_lag2.json` · configuracion · JSON · 49 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5013_prod_receta_muerte_lag2.json.txt)
- `configs/6012_zulip_final_5016.json` · configuracion · JSON · 15 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6012_zulip_final_5016.json.txt)
- `configs/6002_zulip_semillas.json` · configuracion · JSON · 8 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/6002_zulip_semillas.json.txt)
- `configs/5017_prod_muerte_ampliada_bo4108.json` · configuracion · JSON · 50 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5017_prod_muerte_ampliada_bo4108.json.txt)
- `configs/5012_prod_rank_con_lag2.json` · configuracion · JSON · 49 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5012_prod_rank_con_lag2.json.txt)
- `configs/5021_prod_ensamble.json` · configuracion · JSON · 18 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5021_prod_ensamble.json.txt)
- `configs/5005_prod_eleccion_4102.json` · configuracion · JSON · 50 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5005_prod_eleccion_4102.json.txt)
- `configs/5016_prod_muerte_ampliada.json` · configuracion · JSON · 50 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5016_prod_muerte_ampliada.json.txt)
- `configs/5109_comparar_arboles_min_data.json` · configuracion · JSON · 49 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5109_comparar_arboles_min_data.json.txt)
- `configs/5103_comparar_bo4105.json` · configuracion · JSON · 32 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/configs/5103_comparar_bo4105.json.txt)
- `exp/5101_curva_mitad_b/5101_script.py` · secundario · Python · 216 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5101_curva_mitad_b/5101_script.py.txt)
- `exp/5101_curva_mitad_b/5101_resultados.json` · secundario · JSON · 40 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5101_curva_mitad_b/5101_resultados.json.txt)
- `exp/5101_curva_mitad_b/5101_PARAM.json` · secundario · JSON · 56 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5101_curva_mitad_b/5101_PARAM.json.txt)
- `exp/4107_bo_profesor_mar_abr/4107_resultados.json` · secundario · JSON · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4107_bo_profesor_mar_abr/4107_resultados.json.txt)
- `exp/4107_bo_profesor_mar_abr/4107_script.py` · secundario · Python · 338 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4107_bo_profesor_mar_abr/4107_script.py.txt) — Copia de 08_bo_fuera_de_tiempo.py guardada al correr la búsqueda 4107 (338 líneas): usa una sola semilla por prueba y no tiene la opción «regla_eleccion».
- `exp/4107_bo_profesor_mar_abr/4107_eleccion.json` · configuracion · JSON · 31 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4107_bo_profesor_mar_abr/4107_eleccion.json.txt) — Salida de la búsqueda 4107 que lee 07_modelo_final.py: origen «4107 p23_4104», parámetros (learning_rate 0,0678, num_leaves 41, min_data_in_leaf 20.248, feature_fraction 0,1798, bagging_fraction 0,3124, lambda_l1 y lambda_l2 0,001, max_bin 31), 580 árboles, fraccion_mes_referencia 2,0 y la evidencia de la mitad B (435,8 M; retador prueba_42 con 3/20 semillas).
- `exp/4107_bo_profesor_mar_abr/4107_PARAM.json` · secundario · JSON · 96 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4107_bo_profesor_mar_abr/4107_PARAM.json.txt)
- `exp/6003_zulip_final_5008_cortes/6003_resultados.json` · secundario · JSON · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6003_zulip_final_5008_cortes/6003_resultados.json.txt)
- `exp/6003_zulip_final_5008_cortes/cuerpo_mensaje.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6003_zulip_final_5008_cortes/cuerpo_mensaje.txt.txt)
- `exp/6003_zulip_final_5008_cortes/6003_PARAM.json` · secundario · JSON · 22 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6003_zulip_final_5008_cortes/6003_PARAM.json.txt)
- `exp/6003_zulip_final_5008_cortes/6003_script.py` · secundario · Python · 122 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6003_zulip_final_5008_cortes/6003_script.py.txt)
- `exp/2001_diagnostico_aguinaldo/2001_resultados.json` · secundario · JSON · 17 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/2001_diagnostico_aguinaldo/2001_resultados.json.txt)
- `exp/2001_diagnostico_aguinaldo/2001_script.py` · secundario · Python · 227 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/2001_diagnostico_aguinaldo/2001_script.py.txt)
- `exp/2001_diagnostico_aguinaldo/2001_PARAM.json` · secundario · JSON · 11 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/2001_diagnostico_aguinaldo/2001_PARAM.json.txt)
- `exp/5102_comparar_pipelines/5102_resultados.json` · secundario · JSON · 47 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5102_comparar_pipelines/5102_resultados.json.txt)
- `exp/5102_comparar_pipelines/5102_PARAM.json` · secundario · JSON · 76 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5102_comparar_pipelines/5102_PARAM.json.txt)
- `exp/5102_comparar_pipelines/5102_script.py` · secundario · Python · 231 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5102_comparar_pipelines/5102_script.py.txt)
- `exp/4102_bo_fuera_de_tiempo/4102_eleccion.json` · secundario · JSON · 29 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4102_bo_fuera_de_tiempo/4102_eleccion.json.txt)
- `exp/4102_bo_fuera_de_tiempo/4102_PARAM.json` · secundario · JSON · 83 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4102_bo_fuera_de_tiempo/4102_PARAM.json.txt)
- `exp/4102_bo_fuera_de_tiempo/4102_resultados.json` · secundario · JSON · 11 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4102_bo_fuera_de_tiempo/4102_resultados.json.txt)
- `exp/4102_bo_fuera_de_tiempo/4102_script.py` · secundario · Python · 278 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4102_bo_fuera_de_tiempo/4102_script.py.txt)
- `exp/5017_prod_muerte_ampliada_bo4108/5017_script.py` · secundario · Python · 305 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5017_prod_muerte_ampliada_bo4108/5017_script.py.txt)
- `exp/5017_prod_muerte_ampliada_bo4108/5017_params_lightgbm.json` · secundario · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5017_prod_muerte_ampliada_bo4108/5017_params_lightgbm.json.txt)
- `exp/5017_prod_muerte_ampliada_bo4108/5017_resultados.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5017_prod_muerte_ampliada_bo4108/5017_resultados.json.txt)
- `exp/5017_prod_muerte_ampliada_bo4108/5017_PARAM.json` · secundario · JSON · 54 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5017_prod_muerte_ampliada_bo4108/5017_PARAM.json.txt)
- `exp/5005_prod_eleccion_4102/5005_PARAM.json` · secundario · JSON · 54 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5005_prod_eleccion_4102/5005_PARAM.json.txt)
- `exp/5005_prod_eleccion_4102/5005_resultados.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5005_prod_eleccion_4102/5005_resultados.json.txt)
- `exp/5005_prod_eleccion_4102/5005_script.py` · secundario · Python · 295 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5005_prod_eleccion_4102/5005_script.py.txt)
- `exp/5005_prod_eleccion_4102/5005_params_lightgbm.json` · secundario · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5005_prod_eleccion_4102/5005_params_lightgbm.json.txt)
- `exp/5109_comparar_arboles_min_data/5109_resultados.json` · secundario · JSON · 165 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5109_comparar_arboles_min_data/5109_resultados.json.txt)
- `exp/5109_comparar_arboles_min_data/5109_PARAM.json` · secundario · JSON · 93 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5109_comparar_arboles_min_data/5109_PARAM.json.txt)
- `exp/5109_comparar_arboles_min_data/5109_script.py` · secundario · Python · 257 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5109_comparar_arboles_min_data/5109_script.py.txt)
- `exp/5023_prod_5015_sin_rotas/5023_PARAM.json` · secundario · JSON · 63 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5023_prod_5015_sin_rotas/5023_PARAM.json.txt)
- `exp/5023_prod_5015_sin_rotas/5023_script.py` · secundario · Python · 335 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5023_prod_5015_sin_rotas/5023_script.py.txt)
- `exp/5023_prod_5015_sin_rotas/5023_params_lightgbm.json` · secundario · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5023_prod_5015_sin_rotas/5023_params_lightgbm.json.txt)
- `exp/5023_prod_5015_sin_rotas/5023_resultados.json` · secundario · JSON · 15 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5023_prod_5015_sin_rotas/5023_resultados.json.txt)
- `exp/5113_eval_ensamble/5113_eleccion.json` · secundario · JSON · 216 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5113_eval_ensamble/5113_eleccion.json.txt)
- `exp/5113_eval_ensamble/5113_resultados.json` · secundario · JSON · 6 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5113_eval_ensamble/5113_resultados.json.txt)
- `exp/5113_eval_ensamble/5113_script.py` · secundario · Python · 311 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5113_eval_ensamble/5113_script.py.txt)
- `exp/5113_eval_ensamble/5113_PARAM.json` · secundario · JSON · 62 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5113_eval_ensamble/5113_PARAM.json.txt)
- `exp/4106_bo_receta_muerte/4106_PARAM.json` · secundario · JSON · 118 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4106_bo_receta_muerte/4106_PARAM.json.txt)
- `exp/4106_bo_receta_muerte/4106_script.py` · secundario · Python · 314 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4106_bo_receta_muerte/4106_script.py.txt)
- `exp/4106_bo_receta_muerte/4106_resultados.json` · secundario · JSON · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4106_bo_receta_muerte/4106_resultados.json.txt)
- `exp/4106_bo_receta_muerte/4106_eleccion.json` · secundario · JSON · 31 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4106_bo_receta_muerte/4106_eleccion.json.txt)
- `exp/5018_prod_final/5018_params_lightgbm.json` · secundario · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5018_prod_final/5018_params_lightgbm.json.txt)
- `exp/5018_prod_final/5018_resultados.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5018_prod_final/5018_resultados.json.txt)
- `exp/5018_prod_final/5018_PARAM.json` · secundario · JSON · 57 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5018_prod_final/5018_PARAM.json.txt)
- `exp/5018_prod_final/5018_script.py` · secundario · Python · 311 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5018_prod_final/5018_script.py.txt)
- `exp/5003_prod_z601_todas/5003_script.py` · secundario · Python · 295 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5003_prod_z601_todas/5003_script.py.txt)
- `exp/5003_prod_z601_todas/5003_resultados.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5003_prod_z601_todas/5003_resultados.json.txt)
- `exp/5003_prod_z601_todas/5003_params_lightgbm.json` · secundario · JSON · 19 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5003_prod_z601_todas/5003_params_lightgbm.json.txt)
- `exp/5003_prod_z601_todas/5003_PARAM.json` · secundario · JSON · 52 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5003_prod_z601_todas/5003_PARAM.json.txt)
- `exp/4108_bo_muerte_ampliada/4108_resultados.json` · secundario · JSON · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4108_bo_muerte_ampliada/4108_resultados.json.txt)
- `exp/4108_bo_muerte_ampliada/4108_script.py` · secundario · Python · 338 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4108_bo_muerte_ampliada/4108_script.py.txt)
- `exp/4108_bo_muerte_ampliada/4108_PARAM.json` · secundario · JSON · 96 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4108_bo_muerte_ampliada/4108_PARAM.json.txt)
- `exp/4108_bo_muerte_ampliada/4108_eleccion.json` · secundario · JSON · 31 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4108_bo_muerte_ampliada/4108_eleccion.json.txt)
- `exp/4109_bo_limpia_profesor/4109_eleccion.json` · secundario · JSON · 29 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4109_bo_limpia_profesor/4109_eleccion.json.txt)
- `exp/4109_bo_limpia_profesor/4109_PARAM.json` · secundario · JSON · 84 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4109_bo_limpia_profesor/4109_PARAM.json.txt)
- `exp/4109_bo_limpia_profesor/4109_resultados.json` · secundario · JSON · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4109_bo_limpia_profesor/4109_resultados.json.txt)
- `exp/4109_bo_limpia_profesor/4109_script.py` · secundario · Python · 350 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4109_bo_limpia_profesor/4109_script.py.txt)
- `exp/3007_fe_profesor/3007_PARAM.json` · secundario · JSON · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3007_fe_profesor/3007_PARAM.json.txt)
- `exp/3007_fe_profesor/3007_script.py` · secundario · Python · 259 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3007_fe_profesor/3007_script.py.txt)
- `exp/3007_fe_profesor/3007_resultados.json` · secundario · JSON · 8 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3007_fe_profesor/3007_resultados.json.txt)
- `exp/3003_fe_rank_extra/3003_script.py` · secundario · Python · 265 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3003_fe_rank_extra/3003_script.py.txt)
- `exp/3003_fe_rank_extra/3003_PARAM.json` · secundario · JSON · 40 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3003_fe_rank_extra/3003_PARAM.json.txt)
- `exp/3003_fe_rank_extra/3003_resultados.json` · secundario · JSON · 16 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3003_fe_rank_extra/3003_resultados.json.txt)
- `exp/5202_ensamble_5005_5011/5202_resultados.json` · secundario · JSON · 11 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5202_ensamble_5005_5011/5202_resultados.json.txt)
- `exp/5202_ensamble_5005_5011/5202_PARAM.json` · secundario · JSON · 19 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5202_ensamble_5005_5011/5202_PARAM.json.txt)
- `exp/5202_ensamble_5005_5011/5202_script.py` · secundario · Python · 105 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5202_ensamble_5005_5011/5202_script.py.txt)
- `exp/5105_comparar_variantes_receta/5105_resultados.json` · secundario · JSON · 61 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5105_comparar_variantes_receta/5105_resultados.json.txt)
- `exp/5105_comparar_variantes_receta/5105_PARAM.json` · secundario · JSON · 85 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5105_comparar_variantes_receta/5105_PARAM.json.txt)
- `exp/5105_comparar_variantes_receta/5105_script.py` · secundario · Python · 240 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5105_comparar_variantes_receta/5105_script.py.txt)
- `exp/1001_dataset_base/1001_resultados.json` · secundario · JSON · 27 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/1001_dataset_base/1001_resultados.json.txt)
- `exp/1001_dataset_base/1001_script.py` · secundario · Python · 150 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/1001_dataset_base/1001_script.py.txt)
- `exp/1001_dataset_base/1001_PARAM.json` · secundario · JSON · 10 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/1001_dataset_base/1001_PARAM.json.txt)
- `exp/5006_prod_eleccion_4103/5006_resultados.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5006_prod_eleccion_4103/5006_resultados.json.txt)
- `exp/5006_prod_eleccion_4103/5006_params_lightgbm.json` · secundario · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5006_prod_eleccion_4103/5006_params_lightgbm.json.txt)
- `exp/5006_prod_eleccion_4103/5006_script.py` · secundario · Python · 295 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5006_prod_eleccion_4103/5006_script.py.txt)
- `exp/5006_prod_eleccion_4103/5006_PARAM.json` · secundario · JSON · 54 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5006_prod_eleccion_4103/5006_PARAM.json.txt)
- `exp/5013_prod_receta_muerte_lag2/5013_resultados.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5013_prod_receta_muerte_lag2/5013_resultados.json.txt)
- `exp/5013_prod_receta_muerte_lag2/5013_params_lightgbm.json` · secundario · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5013_prod_receta_muerte_lag2/5013_params_lightgbm.json.txt)
- `exp/5013_prod_receta_muerte_lag2/5013_PARAM.json` · secundario · JSON · 53 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5013_prod_receta_muerte_lag2/5013_PARAM.json.txt)
- `exp/5013_prod_receta_muerte_lag2/5013_script.py` · secundario · Python · 305 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5013_prod_receta_muerte_lag2/5013_script.py.txt)
- `exp/6012_zulip_final_5016/6012_script.py` · secundario · Python · 122 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6012_zulip_final_5016/6012_script.py.txt)
- `exp/6012_zulip_final_5016/6012_resultados.json` · secundario · JSON · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6012_zulip_final_5016/6012_resultados.json.txt)
- `exp/6012_zulip_final_5016/cuerpo_mensaje.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6012_zulip_final_5016/cuerpo_mensaje.txt.txt)
- `exp/6012_zulip_final_5016/6012_PARAM.json` · secundario · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6012_zulip_final_5016/6012_PARAM.json.txt)
- `exp/5008_prod_rank_total_bo4104/5008_PARAM.json` · secundario · JSON · 54 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5008_prod_rank_total_bo4104/5008_PARAM.json.txt)
- `exp/5008_prod_rank_total_bo4104/5008_script.py` · secundario · Python · 305 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5008_prod_rank_total_bo4104/5008_script.py.txt)
- `exp/5008_prod_rank_total_bo4104/5008_resultados.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5008_prod_rank_total_bo4104/5008_resultados.json.txt)
- `exp/5008_prod_rank_total_bo4104/5008_params_lightgbm.json` · secundario · JSON · 19 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5008_prod_rank_total_bo4104/5008_params_lightgbm.json.txt)
- `exp/6001_zulip_final_5005_e13000/6001_script.py` · secundario · Python · 116 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6001_zulip_final_5005_e13000/6001_script.py.txt)
- `exp/6001_zulip_final_5005_e13000/6001_PARAM.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6001_zulip_final_5005_e13000/6001_PARAM.json.txt)
- `exp/6001_zulip_final_5005_e13000/cuerpo_mensaje.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6001_zulip_final_5005_e13000/cuerpo_mensaje.txt.txt)
- `exp/6001_zulip_final_5005_e13000/6001_resultados.json` · secundario · JSON · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6001_zulip_final_5005_e13000/6001_resultados.json.txt)
- `exp/5021_prod_ensamble/5021_PARAM.json` · secundario · JSON · 65 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5021_prod_ensamble/5021_PARAM.json.txt)
- `exp/5021_prod_ensamble/5021_script.py` · secundario · Python · 350 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5021_prod_ensamble/5021_script.py.txt)
- `exp/5104_comparar_fe_extra/5104_resultados.json` · secundario · JSON · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5104_comparar_fe_extra/5104_resultados.json.txt)
- `exp/5104_comparar_fe_extra/5104_PARAM.json` · secundario · JSON · 69 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5104_comparar_fe_extra/5104_PARAM.json.txt)
- `exp/5104_comparar_fe_extra/5104_script.py` · secundario · Python · 240 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5104_comparar_fe_extra/5104_script.py.txt)
- `exp/5015_prod_profesor_mar_jun/5015_resultados.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5015_prod_profesor_mar_jun/5015_resultados.json.txt)
- `exp/5015_prod_profesor_mar_jun/5015_script.py` · secundario · Python · 305 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5015_prod_profesor_mar_jun/5015_script.py.txt) — Copia de 07_modelo_final.py guardada al correr el experimento 5015 (305 líneas). Respecto de la versión de la raíz no tiene la exclusión por prefijos, el escalado de min_sum_hessian_in_leaf, los valores explícitos de min_data_in_leaf y de árboles ni el corte por hora límite.
- `exp/5015_prod_profesor_mar_jun/5015_PARAM.json` · configuracion · JSON · 54 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5015_prod_profesor_mar_jun/5015_PARAM.json.txt) — PARAM completo del experimento 5015 con fecha de inicio 2026-10-10 00:39:38, script 07_modelo_final.py y configuración 5015_prod_profesor_mar_jun.json.
- `exp/5015_prod_profesor_mar_jun/5015_params_lightgbm.json` · configuracion · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5015_prod_profesor_mar_jun/5015_params_lightgbm.json.txt) — Parámetros de LightGBM con los que corrió 5015, tal como los graba 07_modelo_final.py: origen «eleccion: 4107 p23_4104», 580 árboles y min_data_in_leaf 40.496.
- `exp/6013_zulip_final_5017/6013_resultados.json` · secundario · JSON · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6013_zulip_final_5017/6013_resultados.json.txt)
- `exp/6013_zulip_final_5017/6013_script.py` · secundario · Python · 122 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6013_zulip_final_5017/6013_script.py.txt)
- `exp/6013_zulip_final_5017/6013_PARAM.json` · secundario · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6013_zulip_final_5017/6013_PARAM.json.txt)
- `exp/6013_zulip_final_5017/cuerpo_mensaje.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6013_zulip_final_5017/cuerpo_mensaje.txt.txt)
- `exp/6011_zulip_final_5015/6011_PARAM.json` · secundario · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6011_zulip_final_5015/6011_PARAM.json.txt)
- `exp/6011_zulip_final_5015/cuerpo_mensaje.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6011_zulip_final_5015/cuerpo_mensaje.txt.txt)
- `exp/6011_zulip_final_5015/6011_script.py` · secundario · Python · 122 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6011_zulip_final_5015/6011_script.py.txt) — Copia de 10_entrega_zulip.py guardada al correr 6011 (122 líneas); no tiene la verificación de probabilidades finitas.
- `exp/6011_zulip_final_5015/6011_resultados.json` · secundario · JSON · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6011_zulip_final_5015/6011_resultados.json.txt)
- `exp/5108_comparar_muerte_ampliada/5108_PARAM.json` · secundario · JSON · 77 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5108_comparar_muerte_ampliada/5108_PARAM.json.txt)
- `exp/5108_comparar_muerte_ampliada/5108_script.py` · secundario · Python · 250 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5108_comparar_muerte_ampliada/5108_script.py.txt)
- `exp/5108_comparar_muerte_ampliada/5108_resultados.json` · secundario · JSON · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5108_comparar_muerte_ampliada/5108_resultados.json.txt)
- `exp/6007_zulip_final_5011/6007_script.py` · secundario · Python · 122 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6007_zulip_final_5011/6007_script.py.txt)
- `exp/6007_zulip_final_5011/6007_PARAM.json` · secundario · JSON · 19 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6007_zulip_final_5011/6007_PARAM.json.txt)
- `exp/6007_zulip_final_5011/cuerpo_mensaje.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6007_zulip_final_5011/cuerpo_mensaje.txt.txt)
- `exp/6007_zulip_final_5011/6007_resultados.json` · secundario · JSON · 10 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6007_zulip_final_5011/6007_resultados.json.txt)
- `exp/5107_comparar_marzo/5107_script.py` · secundario · Python · 250 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5107_comparar_marzo/5107_script.py.txt)
- `exp/5107_comparar_marzo/5107_PARAM.json` · secundario · JSON · 76 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5107_comparar_marzo/5107_PARAM.json.txt)
- `exp/5107_comparar_marzo/5107_resultados.json` · secundario · JSON · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5107_comparar_marzo/5107_resultados.json.txt)
- `exp/5002_sim_z601_todas/5002_resultados.json` · secundario · JSON · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5002_sim_z601_todas/5002_resultados.json.txt)
- `exp/5002_sim_z601_todas/5002_script.py` · secundario · Python · 295 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5002_sim_z601_todas/5002_script.py.txt)
- `exp/5002_sim_z601_todas/5002_PARAM.json` · secundario · JSON · 50 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5002_sim_z601_todas/5002_PARAM.json.txt)
- `exp/5002_sim_z601_todas/5002_params_lightgbm.json` · secundario · JSON · 19 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5002_sim_z601_todas/5002_params_lightgbm.json.txt)
- `exp/5004_prod_z601_p95/5004_params_lightgbm.json` · secundario · JSON · 19 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5004_prod_z601_p95/5004_params_lightgbm.json.txt)
- `exp/5004_prod_z601_p95/5004_script.py` · secundario · Python · 295 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5004_prod_z601_p95/5004_script.py.txt)
- `exp/5004_prod_z601_p95/5004_resultados.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5004_prod_z601_p95/5004_resultados.json.txt)
- `exp/5004_prod_z601_p95/5004_PARAM.json` · secundario · JSON · 52 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5004_prod_z601_p95/5004_PARAM.json.txt)
- `exp/5011_prod_rank_bo4105/5011_script.py` · secundario · Python · 305 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5011_prod_rank_bo4105/5011_script.py.txt)
- `exp/5011_prod_rank_bo4105/5011_PARAM.json` · secundario · JSON · 53 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5011_prod_rank_bo4105/5011_PARAM.json.txt)
- `exp/5011_prod_rank_bo4105/5011_params_lightgbm.json` · secundario · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5011_prod_rank_bo4105/5011_params_lightgbm.json.txt)
- `exp/5011_prod_rank_bo4105/5011_resultados.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5011_prod_rank_bo4105/5011_resultados.json.txt)
- `exp/4104_bo_rank_total/4104_eleccion.json` · secundario · JSON · 29 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4104_bo_rank_total/4104_eleccion.json.txt)
- `exp/4104_bo_rank_total/4104_PARAM.json` · secundario · JSON · 92 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4104_bo_rank_total/4104_PARAM.json.txt)
- `exp/4104_bo_rank_total/4104_resultados.json` · secundario · JSON · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4104_bo_rank_total/4104_resultados.json.txt)
- `exp/4104_bo_rank_total/4104_script.py` · secundario · Python · 314 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4104_bo_rank_total/4104_script.py.txt) — Copia de 08_bo_fuera_de_tiempo.py guardada al correr la búsqueda 4104 (314 líneas): admite un solo mes de entrenamiento y no multiplica el min_data_in_leaf de las referencias.
- `exp/4112_bo_profesor_ds3007/4112_PARAM.json` · secundario · JSON · 64 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4112_bo_profesor_ds3007/4112_PARAM.json.txt)
- `exp/4112_bo_profesor_ds3007/4112_script.py` · secundario · Python · 250 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4112_bo_profesor_ds3007/4112_script.py.txt)
- `exp/4112_bo_profesor_ds3007/4112_resultados.json` · secundario · JSON · 19 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4112_bo_profesor_ds3007/4112_resultados.json.txt)
- `exp/4112_bo_profesor_ds3007/4112_top.json` · secundario · JSON · 266 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4112_bo_profesor_ds3007/4112_top.json.txt)
- `exp/4101_bo_crudo_p95/4101_script.py` · secundario · Python · 266 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4101_bo_crudo_p95/4101_script.py.txt)
- `exp/4101_bo_crudo_p95/4101_PARAM.json` · secundario · JSON · 81 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4101_bo_crudo_p95/4101_PARAM.json.txt)
- `exp/4101_bo_crudo_p95/4101_resultados.json` · secundario · JSON · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4101_bo_crudo_p95/4101_resultados.json.txt)
- `exp/3006_fe_muerte_ampliada/3006_PARAM.json` · secundario · JSON · 112 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3006_fe_muerte_ampliada/3006_PARAM.json.txt)
- `exp/3006_fe_muerte_ampliada/3006_resultados.json` · secundario · JSON · 8 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3006_fe_muerte_ampliada/3006_resultados.json.txt)
- `exp/3006_fe_muerte_ampliada/3006_script.py` · secundario · Python · 324 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3006_fe_muerte_ampliada/3006_script.py.txt)
- `exp/5001_sim_z601_p95/5001_params_lightgbm.json` · secundario · JSON · 19 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5001_sim_z601_p95/5001_params_lightgbm.json.txt)
- `exp/5001_sim_z601_p95/5001_PARAM.json` · secundario · JSON · 50 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5001_sim_z601_p95/5001_PARAM.json.txt)
- `exp/5001_sim_z601_p95/5001_script.py` · secundario · Python · 295 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5001_sim_z601_p95/5001_script.py.txt)
- `exp/3005_fe_rank_luego_lag/3005_script.py` · secundario · Python · 278 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3005_fe_rank_luego_lag/3005_script.py.txt)
- `exp/3005_fe_rank_luego_lag/3005_resultados.json` · secundario · JSON · 10 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3005_fe_rank_luego_lag/3005_resultados.json.txt)
- `exp/3005_fe_rank_luego_lag/3005_PARAM.json` · secundario · JSON · 44 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3005_fe_rank_luego_lag/3005_PARAM.json.txt)
- `exp/6005_zulip_cortes_5005/6005_PARAM.json` · secundario · JSON · 19 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6005_zulip_cortes_5005/6005_PARAM.json.txt)
- `exp/6005_zulip_cortes_5005/6005_resultados.json` · secundario · JSON · 10 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6005_zulip_cortes_5005/6005_resultados.json.txt)
- `exp/6005_zulip_cortes_5005/cuerpo_mensaje.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6005_zulip_cortes_5005/cuerpo_mensaje.txt.txt)
- `exp/6005_zulip_cortes_5005/6005_script.py` · secundario · Python · 122 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6005_zulip_cortes_5005/6005_script.py.txt)
- `exp/5007_prod_p117_por_semilla/5007_PARAM.json` · secundario · JSON · 47 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5007_prod_p117_por_semilla/5007_PARAM.json.txt)
- `exp/5007_prod_p117_por_semilla/5007_script.py` · secundario · Python · 302 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5007_prod_p117_por_semilla/5007_script.py.txt)
- `exp/5007_prod_p117_por_semilla/5007_resultados.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5007_prod_p117_por_semilla/5007_resultados.json.txt)
- `exp/5007_prod_p117_por_semilla/5007_params_lightgbm.json` · secundario · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5007_prod_p117_por_semilla/5007_params_lightgbm.json.txt)
- `exp/6008_zulip_final_ensamble_5202/6008_PARAM.json` · secundario · JSON · 19 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6008_zulip_final_ensamble_5202/6008_PARAM.json.txt)
- `exp/6008_zulip_final_ensamble_5202/cuerpo_mensaje.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6008_zulip_final_ensamble_5202/cuerpo_mensaje.txt.txt)
- `exp/6008_zulip_final_ensamble_5202/6008_script.py` · secundario · Python · 122 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6008_zulip_final_ensamble_5202/6008_script.py.txt)
- `exp/6008_zulip_final_ensamble_5202/6008_resultados.json` · secundario · JSON · 10 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6008_zulip_final_ensamble_5202/6008_resultados.json.txt)
- `exp/6009_zulip_final_5013/6009_PARAM.json` · secundario · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6009_zulip_final_5013/6009_PARAM.json.txt)
- `exp/6009_zulip_final_5013/6009_resultados.json` · secundario · JSON · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6009_zulip_final_5013/6009_resultados.json.txt)
- `exp/6009_zulip_final_5013/6009_script.py` · secundario · Python · 122 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6009_zulip_final_5013/6009_script.py.txt)
- `exp/6009_zulip_final_5013/cuerpo_mensaje.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6009_zulip_final_5013/cuerpo_mensaje.txt.txt)
- `exp/3002_fe_lag2_rank_total/3002_resultados.json` · secundario · JSON · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3002_fe_lag2_rank_total/3002_resultados.json.txt)
- `exp/3002_fe_lag2_rank_total/3002_script.py` · secundario · Python · 149 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3002_fe_lag2_rank_total/3002_script.py.txt)
- `exp/3002_fe_lag2_rank_total/3002_PARAM.json` · secundario · JSON · 18 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3002_fe_lag2_rank_total/3002_PARAM.json.txt)
- `exp/7002_decision_final/7002_script.py` · secundario · Python · 147 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/7002_decision_final/7002_script.py.txt)
- `exp/7002_decision_final/7002_PARAM.json` · secundario · JSON · 9 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/7002_decision_final/7002_PARAM.json.txt)
- `exp/7002_decision_final/7002_decision.json` · secundario · JSON · 8 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/7002_decision_final/7002_decision.json.txt)
- `exp/7002_decision_final/7002_resultados.json` · secundario · JSON · 9 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/7002_decision_final/7002_resultados.json.txt)
- `exp/6014_zulip_final_5018/6014_resultados.json` · secundario · JSON · 12 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6014_zulip_final_5018/6014_resultados.json.txt)
- `exp/6014_zulip_final_5018/6014_script.py` · secundario · Python · 124 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6014_zulip_final_5018/6014_script.py.txt)
- `exp/6014_zulip_final_5018/6014_PARAM.json` · secundario · JSON · 22 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6014_zulip_final_5018/6014_PARAM.json.txt)
- `exp/6014_zulip_final_5018/cuerpo_mensaje.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6014_zulip_final_5018/cuerpo_mensaje.txt.txt)
- `exp/5103_comparar_bo4105/5103_resultados.json` · secundario · JSON · 47 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5103_comparar_bo4105/5103_resultados.json.txt)
- `exp/5103_comparar_bo4105/5103_script.py` · secundario · Python · 240 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5103_comparar_bo4105/5103_script.py.txt)
- `exp/5103_comparar_bo4105/5103_PARAM.json` · secundario · JSON · 77 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5103_comparar_bo4105/5103_PARAM.json.txt)
- `exp/6019_zulip_final_5023/6019_script.py` · secundario · Python · 124 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6019_zulip_final_5023/6019_script.py.txt)
- `exp/6019_zulip_final_5023/6019_PARAM.json` · secundario · JSON · 17 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6019_zulip_final_5023/6019_PARAM.json.txt)
- `exp/6019_zulip_final_5023/cuerpo_mensaje.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6019_zulip_final_5023/cuerpo_mensaje.txt.txt)
- `exp/6019_zulip_final_5023/6019_resultados.json` · secundario · JSON · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6019_zulip_final_5023/6019_resultados.json.txt)
- `exp/6004_zulip_semillas_5008/6004_resultados.json` · secundario · JSON · 26 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6004_zulip_semillas_5008/6004_resultados.json.txt)
- `exp/6004_zulip_semillas_5008/6004_script.py` · secundario · Python · 122 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6004_zulip_semillas_5008/6004_script.py.txt)
- `exp/6004_zulip_semillas_5008/6004_PARAM.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6004_zulip_semillas_5008/6004_PARAM.json.txt)
- `exp/6004_zulip_semillas_5008/cuerpo_mensaje.txt` · secundario · Texto · 1 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/6004_zulip_semillas_5008/cuerpo_mensaje.txt.txt)
- `exp/4001_comparar_fe/4001_PARAM.json` · secundario · JSON · 46 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4001_comparar_fe/4001_PARAM.json.txt)
- `exp/4001_comparar_fe/4001_resultados.json` · secundario · JSON · 30 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4001_comparar_fe/4001_resultados.json.txt)
- `exp/4001_comparar_fe/4001_script.py` · secundario · Python · 213 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4001_comparar_fe/4001_script.py.txt)
- `exp/3001_fe_lags_deltas/3001_PARAM.json` · secundario · JSON · 23 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3001_fe_lags_deltas/3001_PARAM.json.txt)
- `exp/3001_fe_lags_deltas/3001_script.py` · secundario · Python · 185 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3001_fe_lags_deltas/3001_script.py.txt)
- `exp/3001_fe_lags_deltas/3001_resultados.json` · secundario · JSON · 22 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3001_fe_lags_deltas/3001_resultados.json.txt)
- `exp/7001_decision_p23/7001_resultados.json` · secundario · JSON · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/7001_decision_p23/7001_resultados.json.txt)
- `exp/7001_decision_p23/7001_script.py` · secundario · Python · 147 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/7001_decision_p23/7001_script.py.txt)
- `exp/7001_decision_p23/7001_PARAM.json` · secundario · JSON · 9 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/7001_decision_p23/7001_PARAM.json.txt)
- `exp/7001_decision_p23/7001_decision.json` · secundario · JSON · 6 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/7001_decision_p23/7001_decision.json.txt)
- `exp/4002_binaria2/4002_script.py` · secundario · Python · 220 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4002_binaria2/4002_script.py.txt)
- `exp/4002_binaria2/4002_PARAM.json` · secundario · JSON · 44 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4002_binaria2/4002_PARAM.json.txt)
- `exp/4002_binaria2/4002_resultados.json` · secundario · JSON · 18 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4002_binaria2/4002_resultados.json.txt)
- `exp/3004_fe_flags/3004_resultados.json` · secundario · JSON · 10 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3004_fe_flags/3004_resultados.json.txt)
- `exp/3004_fe_flags/3004_script.py` · secundario · Python · 278 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3004_fe_flags/3004_script.py.txt)
- `exp/3004_fe_flags/3004_PARAM.json` · secundario · JSON · 44 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/3004_fe_flags/3004_PARAM.json.txt)
- `exp/5110_comparar_bo4109/5110_resultados.json` · secundario · JSON · 37 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5110_comparar_bo4109/5110_resultados.json.txt)
- `exp/5110_comparar_bo4109/5110_PARAM.json` · secundario · JSON · 82 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5110_comparar_bo4109/5110_PARAM.json.txt)
- `exp/5110_comparar_bo4109/5110_script.py` · secundario · Python · 257 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5110_comparar_bo4109/5110_script.py.txt)
- `exp/5016_prod_muerte_ampliada/5016_params_lightgbm.json` · secundario · JSON · 21 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5016_prod_muerte_ampliada/5016_params_lightgbm.json.txt)
- `exp/5016_prod_muerte_ampliada/5016_PARAM.json` · secundario · JSON · 54 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5016_prod_muerte_ampliada/5016_PARAM.json.txt)
- `exp/5016_prod_muerte_ampliada/5016_script.py` · secundario · Python · 305 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5016_prod_muerte_ampliada/5016_script.py.txt)
- `exp/5016_prod_muerte_ampliada/5016_resultados.json` · secundario · JSON · 14 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5016_prod_muerte_ampliada/5016_resultados.json.txt)
- `exp/4003_canaritos/4003_script.py` · secundario · Python · 218 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4003_canaritos/4003_script.py.txt)
- `exp/4003_canaritos/4003_variables_max.txt` · secundario · Texto · 120 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4003_canaritos/4003_variables_max.txt.txt)
- `exp/4003_canaritos/4003_variables_p95.txt` · secundario · Texto · 123 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4003_canaritos/4003_variables_p95.txt.txt)
- `exp/4003_canaritos/4003_PARAM.json` · secundario · JSON · 42 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4003_canaritos/4003_PARAM.json.txt)
- `exp/4003_canaritos/4003_resultados.json` · secundario · JSON · 30 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4003_canaritos/4003_resultados.json.txt)
- `exp/5114_eval_dataset/5114_resultados.json` · secundario · JSON · 7 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5114_eval_dataset/5114_resultados.json.txt)
- `exp/5114_eval_dataset/5114_PARAM.json` · secundario · JSON · 52 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5114_eval_dataset/5114_PARAM.json.txt)
- `exp/5114_eval_dataset/5114_script.py` · secundario · Python · 155 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5114_eval_dataset/5114_script.py.txt)
- `exp/2002_diagnostico_ceros_na/2002_PARAM.json` · secundario · JSON · 28 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/2002_diagnostico_ceros_na/2002_PARAM.json.txt)
- `exp/2002_diagnostico_ceros_na/2002_script.py` · secundario · Python · 106 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/2002_diagnostico_ceros_na/2002_script.py.txt)
- `exp/2002_diagnostico_ceros_na/2002_resultados.json` · secundario · JSON · 5 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/2002_diagnostico_ceros_na/2002_resultados.json.txt)
- `exp/4105_bo_rank_ampliada/4105_script.py` · secundario · Python · 314 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4105_bo_rank_ampliada/4105_script.py.txt)
- `exp/4105_bo_rank_ampliada/4105_eleccion.json` · secundario · JSON · 31 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4105_bo_rank_ampliada/4105_eleccion.json.txt)
- `exp/4105_bo_rank_ampliada/4105_PARAM.json` · secundario · JSON · 128 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4105_bo_rank_ampliada/4105_PARAM.json.txt)
- `exp/4105_bo_rank_ampliada/4105_resultados.json` · secundario · JSON · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4105_bo_rank_ampliada/4105_resultados.json.txt)
- `exp/4103_bo_fuera_de_tiempo_ampliada/4103_PARAM.json` · secundario · JSON · 100 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4103_bo_fuera_de_tiempo_ampliada/4103_PARAM.json.txt)
- `exp/4103_bo_fuera_de_tiempo_ampliada/4103_eleccion.json` · secundario · JSON · 31 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4103_bo_fuera_de_tiempo_ampliada/4103_eleccion.json.txt)
- `exp/4103_bo_fuera_de_tiempo_ampliada/4103_resultados.json` · secundario · JSON · 13 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4103_bo_fuera_de_tiempo_ampliada/4103_resultados.json.txt)
- `exp/4103_bo_fuera_de_tiempo_ampliada/4103_script.py` · secundario · Python · 304 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/4103_bo_fuera_de_tiempo_ampliada/4103_script.py.txt)
- `exp/5106_lag2_entrenando_mayo/5106_script.py` · secundario · Python · 240 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5106_lag2_entrenando_mayo/5106_script.py.txt)
- `exp/5106_lag2_entrenando_mayo/5106_resultados.json` · secundario · JSON · 33 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5106_lag2_entrenando_mayo/5106_resultados.json.txt)
- `exp/5106_lag2_entrenando_mayo/5106_PARAM.json` · secundario · JSON · 69 líneas — [texto](https://emavaldez.github.io/postmortem/fuentes/rodpalds/exp/5106_lag2_entrenando_mayo/5106_PARAM.json.txt)

## Código principal con anotaciones

Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.

### 01_preparar_dataset.py

Experimento 1001: lee el CSV crudo, construye clase_ternaria, clase_binaria1 y clase_binaria2, hace controles sobre la clase y graba data/ds1001_base.parquet.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Docstring con el propósito del script y cómo correrlo; imprime un aviso de
#   arranque e importa numpy, pandas y las funciones de exp_utils.
"""
01_preparar_dataset.py
DMEyF 2026 - Primera Competencia

Lee el dataset crudo, construye la clase ternaria (misma logica que el
script R de la catedra), agrega las dos clases binarias y guarda todo en
Parquet. Al final valida que el archivo grabado sea identico al de memoria.

Uso:  python 01_preparar_dataset.py   (exp_utils.py tiene que estar en la misma carpeta)
Requiere:  pip install pandas pyarrow
"""

print("Arrancando 01_preparar_dataset.py ...", flush=True)

import time

import numpy as np
import pandas as pd

from exp_utils import DIR_DATA, cerrar_experimento, iniciar_experimento

# [Anotación · líneas 22–36] PARAM del experimento 1001 (dataset_base): entrada competencia_01_crudo.csv y
#   salida ds1001_base.parquet, ambas en data/. Inicia el experimento y arma las dos rutas.
# ---------------------------------------------------------------------------
# PARAM: todo lo que define este experimento
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 1001,
    "nombre": "dataset_base",
    "descripcion": "Crudo -> clase_ternaria (logica catedra) + clase_binaria1 (BAJA+2) "
                   "+ clase_binaria2 (BAJA+1 y BAJA+2). Sin feature engineering.",
    "dataset_entrada": "competencia_01_crudo.csv",
    "dataset_salida": "ds1001_base.parquet",   # el id del experimento que lo genero va en el nombre
}

exp = iniciar_experimento(PARAM)
ARCH_CRUDO = DIR_DATA / PARAM["dataset_entrada"]
ARCH_SALIDA = DIR_DATA / PARAM["dataset_salida"]

# [Anotación · líneas 38–54] Lee el CSV con el motor pyarrow. Detiene la corrida si el archivo ya trae
#   clase_ternaria o si hay filas repetidas de numero_de_cliente y foto_mes; lista los meses presentes.
# ---------------------------------------------------------------------------
# 1. Lectura
# ---------------------------------------------------------------------------
t0 = time.time()
print(f"Leyendo {ARCH_CRUDO} ...")
df = pd.read_csv(ARCH_CRUDO, engine="pyarrow")
print(f"  {len(df):,} filas x {df.shape[1]} columnas  ({time.time() - t0:.1f} s)")

if "clase_ternaria" in df.columns:
    raise ValueError("El crudo ya trae clase_ternaria. ¿Seguro que es el archivo crudo?")

meses = sorted(int(m) for m in df["foto_mes"].unique())
print(f"  Meses: {meses}")

dups = df.duplicated(["numero_de_cliente", "foto_mes"]).sum()
if dups:
    raise ValueError(f"Hay {dups} filas repetidas de cliente-mes. Revisar el crudo antes de seguir.")

# [Anotación · líneas 56–88] Arma la clase ternaria: convierte foto_mes en un período consecutivo (año × 12 +
#   mes), ordena por cliente y período y toma los dos períodos siguientes de cada cliente. Asigna CONTINUA a los
#   períodos anteriores al anteúltimo, BAJA+1 cuando falta el registro del mes siguiente y BAJA+2 cuando existe
#   el mes siguiente y falta el de dos meses después; luego vuelve al orden original de las filas.
# ---------------------------------------------------------------------------
# 2. Clase ternaria
#    Traduccion directa del codigo R de la catedra:
#    - periodo0 = mes como numero consecutivo (anio*12 + mes)
#    - periodo1 y periodo2 = los dos registros siguientes del MISMO cliente
#    - un hueco (periodo1 > periodo0 + 1) cuenta como baja
# ---------------------------------------------------------------------------
t0 = time.time()
aux = pd.DataFrame({
    "pos": np.arange(len(df)),
    "numero_de_cliente": df["numero_de_cliente"].to_numpy(),
    "periodo0": (df["foto_mes"] // 100) * 12 + df["foto_mes"] % 100,
})
aux = aux.sort_values(["numero_de_cliente", "periodo0"], kind="mergesort")

g = aux.groupby("numero_de_cliente", sort=False)["periodo0"]
aux["periodo1"] = g.shift(-1)
aux["periodo2"] = g.shift(-2)

periodo_ultimo = aux["periodo0"].max()
periodo_anteultimo = periodo_ultimo - 1

p0, p1, p2 = aux["periodo0"], aux["periodo1"], aux["periodo2"]
clase = pd.Series(pd.NA, index=aux.index, dtype="string")

# orden igual al de la catedra: primero CONTINUA, despues se pisa con las bajas
clase[p0 < periodo_anteultimo] = "CONTINUA"
clase[(p0 < periodo_ultimo) & (p1.isna() | (p0 + 1 < p1))] = "BAJA+1"
clase[(p0 < periodo_anteultimo) & (p0 + 1 == p1) & (p2.isna() | (p0 + 2 < p2))] = "BAJA+2"

aux["clase_ternaria"] = clase
aux = aux.sort_values("pos")                       # vuelvo al orden original
df["clase_ternaria"] = aux["clase_ternaria"].to_numpy()

# [Anotación · líneas 90–98] Crea clase_binaria1 (1 si la clase es BAJA+2) y clase_binaria2 (1 si es BAJA+1 o
#   BAJA+2), en tipo Int8 y con nulo donde la ternaria es nula.
# ---------------------------------------------------------------------------
# 3. Clases binarias (quedan nulas donde la ternaria es nula)
#    clase_binaria1: BAJA+2 vs resto                 (la del libro)
#    clase_binaria2: BAJA+1 y BAJA+2 vs CONTINUA     (la del z601)
# ---------------------------------------------------------------------------
ct = df["clase_ternaria"]
df["clase_binaria1"] = (ct == "BAJA+2").astype("Int8").where(ct.notna())
df["clase_binaria2"] = ct.isin(["BAJA+1", "BAJA+2"]).astype("Int8").where(ct.notna())
print(f"Clases construidas ({time.time() - t0:.1f} s)")

# [Anotación · líneas 100–125] Arma la tabla de clientes por mes y clase y la graba en CSV. Verifica por
#   aserciones que el último mes quede sin clase, que el anteúltimo sólo tenga BAJA+1 y que los demás tengan
#   clase completa; imprime el porcentaje de cada clase por mes.
# ---------------------------------------------------------------------------
# 4. Controles de la clase
# ---------------------------------------------------------------------------
tabla = (df.assign(clase=df["clase_ternaria"].fillna("(sin clase)"))
           .pivot_table(index="foto_mes", columns="clase", values="numero_de_cliente",
                        aggfunc="count", fill_value=0))
print("\nClientes por mes y clase:")
print(tabla.to_string())
tabla.to_csv(exp.ruta("clientes_por_mes_y_clase"))

ult, anteult = meses[-1], meses[-2]
assert df.loc[df["foto_mes"] == ult, "clase_ternaria"].isna().all(), \
    "El ultimo mes deberia quedar 100% sin clase"
assert set(df.loc[df["foto_mes"] == anteult, "clase_ternaria"].dropna()) <= {"BAJA+1"}, \
    "El anteultimo mes solo puede tener BAJA+1 (el resto sin clase)"
for m in meses[:-2]:
    assert df.loc[df["foto_mes"] == m, "clase_ternaria"].notna().all(), \
        f"El mes {m} deberia tener clase completa"
print(f"\nOK: meses con clase completa = {meses[:-2]}; "
      f"{anteult} solo BAJA+1; {ult} sin clase (es el 'futuro').")

tasa = (df[df["foto_mes"].isin(meses[:-2])]
        .groupby("foto_mes")["clase_ternaria"]
        .value_counts(normalize=True).unstack().mul(100).round(3))
print("\nPorcentaje de cada clase por mes (meses completos):")
print(tasa.to_string())

# [Anotación · líneas 127–150] Graba el dataset en Parquet con compresión zstd, lo relee y verifica que
#   conserve la forma y la cantidad de nulos por columna. Cierra el experimento registrando filas, columnas,
#   meses, meses con clase completa y cantidad de BAJA+2 por mes.
# ---------------------------------------------------------------------------
# 5. Grabacion y verificacion de ida y vuelta
# ---------------------------------------------------------------------------
t0 = time.time()
df.to_parquet(ARCH_SALIDA, engine="pyarrow", compression="zstd", index=False)
print(f"\nGrabado {ARCH_SALIDA}  ({ARCH_SALIDA.stat().st_size / 1e6:.0f} MB, {time.time() - t0:.1f} s)")

t0 = time.time()
chk = pd.read_parquet(ARCH_SALIDA)
print(f"Releido en {time.time() - t0:.1f} s")

assert chk.shape == df.shape, "Cambio la forma del dataset al grabar"
assert chk["clase_ternaria"].isna().sum() == df["clase_ternaria"].isna().sum(), \
    "Los nulos de clase_ternaria no sobrevivieron al grabado"
assert (chk.isna().sum() == df.isna().sum()).all(), "Cambio la cantidad de nulos en alguna columna"
print("OK: el Parquet conserva filas, columnas y nulos (no se repite el problema fwrite/fread).")

cerrar_experimento(exp, {
    "filas": len(df),
    "columnas": df.shape[1],
    "meses": meses,
    "meses_clase_completa": meses[:-2],
    "baja2_por_mes": {int(m): int(n) for m, n in tabla["BAJA+2"].items()},
})
```

### 03c_fe_extra.py

Experimento 3003: genera ds3003_rank_extra.parquet, el dataset del modelo entregado: lags y deltas de orden 1 y 2 de las 152 variables, seis variables nuevas sobre productos en cero o NA y ranking de todas las columnas dentro del mes con cero fijo.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–47] Docstring: mismo procedimiento que 03b más seis variables nuevas (n_apagados,
#   n_apagados_delta1, n_apagados_delta2, n_dejo_de_usar, ctrx_quarter_rel_max3 y mcaja_ahorro_rel_max3), con su
#   definición; las nuevas no llevan lags ni deltas. Importa las librerías y, si exp_utils no está en la carpeta
#   actual, agrega la carpeta superior a la ruta de importación.
"""
03c_fe_extra.py
DMEyF 2026 - Primera Competencia - Experimento 3003

Igual que 03b (receta del profesor: lags y deltas 1 y 2 sobre crudos, despues ranking de TODO
dentro de cada mes con cero fijo, NA se mantiene) MAS 6 variables nuevas del "proceso de muerte"
(ver revision_cowork4/informe_revision4.md, tarea 3):

  n_apagados             cuantas de las variables clave estan en cero o NA este mes
  n_apagados_delta1      n_apagados - n_apagados del mes anterior   (NA si no hay mes anterior)
  n_apagados_delta2      n_apagados - n_apagados de 2 meses antes   (NA si no hay)
  n_dejo_de_usar         cuantas variables clave estaban activas (distintas de 0 y no NA) hace
                         1 o 2 meses y ahora estan en cero o NA      (NA si no hay ninguno de los dos meses)
  ctrx_quarter_rel_max3  ctrx_quarter / maximo de ctrx_quarter en los ultimos 3 meses (este incluido)
                         NA si ese maximo es 0 o NA
  mcaja_ahorro_rel_max3  idem con mcaja_ahorro (saldo de caja de ahorro), NA si el maximo <= 0

Las 6 nuevas NO llevan lags/deltas (ya miran el pasado); se rankean igual que el resto.
Las 152 originales llevan lag1, lag2, delta1, delta2 como en 03b.

OJO lag2: en 202104 los lag2/delta2 (y n_apagados_delta2) estan 100% vacios porque el dataset
empieza en 202103. Entrenando solo con abril no se pueden validar.

Uso (desde la carpeta Primera_competencia, cuando la PC este libre):
    Copy-Item revision_cowork4\\03c_fe_extra.py 03c_fe_extra.py
    py -3.12 03c_fe_extra.py
Genera data/ds3003_rank_extra.parquet (~983 mil filas x 771 columnas, ~550 MB) en ~1-2 min.
Memoria: pico estimado ~5 GB (las ~770 columnas finales en float32 = ~3 GB + la base).
"""

print("Arrancando 03c_fe_extra.py ...", flush=True)

import gc
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

try:
    from exp_utils import DIR_DATA, cerrar_experimento, iniciar_experimento
except ImportError:   # si se corre desde revision_cowork4\ en lugar de la raiz del proyecto
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from exp_utils import DIR_DATA, cerrar_experimento, iniciar_experimento

# [Anotación · líneas 49–74] PARAM del experimento 3003: entrada ds1001_base.parquet, salida
#   ds3003_rank_extra.parquet, lags y deltas [1, 2], la lista de 16 variables «claves» (transacciones, saldos,
#   tarjetas, préstamos personales, payroll, canales digitales, comisiones, descubierto y cuenta corriente) y
#   las dos variables de «relativas_max3» (ctrx_quarter y mcaja_ahorro).
# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 3003,
    "nombre": "fe_rank_extra",
    "descripcion": "Como 3002 (lags/deltas 1 y 2 + rank total por mes con cero fijo, NA se mantiene) "
                   "mas 6 variables del proceso de muerte: n_apagados, sus deltas 1 y 2, n_dejo_de_usar, "
                   "ctrx_quarter y mcaja_ahorro relativos al maximo de 3 meses.",
    "dataset_entrada": "ds1001_base.parquet",
    "dataset_salida": "ds3003_rank_extra.parquet",
    "lags": [1, 2],
    "deltas": [1, 2],
    # variables cuyo cero/NA mas se asocia a la baja (2002: lift) o que se apagan antes de irse
    # (2002: proceso de muerte), mas las mas importantes de 5005
    "claves": ["ctrx_quarter", "mpasivos_margen", "mcaja_ahorro", "mcuentas_saldo",
               "ctarjeta_visa_transacciones", "ctarjeta_master_transacciones",
               "ctarjeta_debito_transacciones", "mprestamos_personales", "mpayroll",
               "cmobile_app_trx", "chomebanking_transacciones", "mcomisiones",
               "cdescubierto_preacordado", "mcuenta_corriente", "Visa_msaldototal",
               "Master_msaldototal"],
    "relativas_max3": ["ctrx_quarter", "mcaja_ahorro"],
}

exp = iniciar_experimento(PARAM)
NO_FEATURES = ["numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"]

# [Anotación · líneas 76–94] Lee el dataset base y lo ordena por cliente y mes; verifica que no haya cliente-
#   mes repetidos ni variables no numéricas. Comprueba que al menos 12 de las variables clave y las dos de
#   relativas_max3 existan en el dataset.
# ---------------------------------------------------------------------------
# Carga (orden cliente-mes: necesario para los lags)
# ---------------------------------------------------------------------------
t0 = time.time()
base = pd.read_parquet(DIR_DATA / PARAM["dataset_entrada"])
base = base.sort_values(["numero_de_cliente", "foto_mes"], kind="mergesort").reset_index(drop=True)
assert not base.duplicated(["numero_de_cliente", "foto_mes"]).any(), "Hay cliente-mes repetidos"
features = [c for c in base.columns if c not in NO_FEATURES]
no_numericas = [c for c in features if not pd.api.types.is_numeric_dtype(base[c])]
if no_numericas:
    raise ValueError(f"Hay variables no numericas, revisar: {no_numericas}")
claves = [c for c in PARAM["claves"] if c in features]
faltan = sorted(set(PARAM["claves"]) - set(claves))
assert len(claves) >= 12, f"Faltan demasiadas variables clave en el dataset: {faltan}"
if faltan:
    print(f"AVISO: variables clave que no estan en el dataset (se omiten): {faltan}")
assert all(c in features for c in PARAM["relativas_max3"]), "Falta alguna variable de relativas_max3"
print(f"Leido {PARAM['dataset_entrada']}: {len(base):,} filas, {len(features)} variables, "
      f"{len(claves)} claves ({time.time() - t0:.0f} s)")

# [Anotación · líneas 96–116] Calcula el período consecutivo de cada fila y los índices por mes. Para k = 1 y
#   2 marca las filas cuya fila k posiciones arriba es del mismo cliente y de exactamente k meses antes; lag_de
#   devuelve el valor desplazado k filas y NaN donde esa marca es falsa.
n = len(base)
mes = base["foto_mes"].to_numpy()
cliente = base["numero_de_cliente"].to_numpy()
periodo = (mes // 100) * 12 + mes % 100
meses = sorted(int(m) for m in np.unique(mes))
idx_mes = {m: np.flatnonzero(mes == m) for m in meses}

# fila k posiciones arriba = mismo cliente exactamente k meses antes
fila_valida = {}
for k in sorted(set(PARAM["lags"]) | set(PARAM["deltas"])):
    ok = np.zeros(n, dtype=bool)
    ok[k:] = (cliente[k:] == cliente[:-k]) & (periodo[k:] - periodo[:-k] == k)
    fila_valida[k] = ok
assert 1 in fila_valida and 2 in fila_valida, "Las variables nuevas necesitan lags 1 y 2"


def lag_de(x, k):
    out = np.full(n, np.nan, dtype="float32")
    out[k:] = x[:-k]
    out[~fila_valida[k]] = np.nan
    return out


# [Anotación · líneas 119–138] rank_cero_fijo reemplaza, dentro de cada mes, los positivos por su rango
#   percentil en (0,1] y los negativos por el rango percentil de su valor absoluto con signo menos; deja el cero
#   en 0 y el NA en NA. controlar_rank verifica que el ranking conserve NA, ceros y signo y quede en [−1, 1].
def rank_cero_fijo(x):
    """Dentro de cada mes: positivos (0,1], negativos [-1,0), cero 0, NA NA (identico a 03b)."""
    out = np.full(n, np.nan, dtype="float32")
    for m, idx in idx_mes.items():
        v = x[idx]
        r = np.where(np.isnan(v), np.nan, 0.0)
        pos, neg = v > 0, v < 0
        if pos.any():
            r[pos] = pd.Series(v[pos]).rank(method="average", pct=True).to_numpy()
        if neg.any():
            r[neg] = -pd.Series(-v[neg]).rank(method="average", pct=True).to_numpy()
        out[idx] = r
    return out


def controlar_rank(nombre, valores, rk):
    assert np.array_equal(np.isnan(rk), np.isnan(valores)), f"Cambiaron los NA en {nombre}"
    assert np.array_equal(rk == 0, valores == 0), f"Cambiaron los ceros en {nombre}"
    assert np.array_equal(rk > 0, valores > 0), f"Cambio el signo en {nombre}"
    assert np.nanmin(rk, initial=0) >= -1 and np.nanmax(rk, initial=0) <= 1, f"Fuera de rango en {nombre}"


# [Anotación · líneas 141–160] Sobre valores sin rankear, recorre las 16 variables clave: una variable está
#   «apagada» si vale NA o 0 y estuvo «activa antes» si su lag1 o su lag2 es distinto de 0. Suma n_apagados y
#   n_dejo_de_usar (apagada hoy y activa antes; NA si el cliente no tiene ninguno de los dos meses previos) y
#   calcula n_apagados_delta1 y n_apagados_delta2 contra el n_apagados de 1 y 2 meses antes.
# ---------------------------------------------------------------------------
# 1) Variables nuevas (sobre valores CRUDOS, antes de rankear)
# ---------------------------------------------------------------------------
t0 = time.time()
nuevas = {}
n_apagados = np.zeros(n, dtype="float32")
n_dejo = np.zeros(n, dtype="float32")
for c in claves:
    x = base[c].to_numpy(dtype="float32")
    apagado = np.isnan(x) | (x == 0)
    l1, l2 = lag_de(x, 1), lag_de(x, 2)
    activo_antes = (~np.isnan(l1) & (l1 != 0)) | (~np.isnan(l2) & (l2 != 0))
    n_apagados += apagado
    n_dejo += apagado & activo_antes
sin_historia = ~fila_valida[1] & ~fila_valida[2]
n_dejo[sin_historia] = np.nan
nuevas["n_apagados"] = n_apagados
nuevas["n_apagados_delta1"] = n_apagados - lag_de(n_apagados, 1)
nuevas["n_apagados_delta2"] = n_apagados - lag_de(n_apagados, 2)
nuevas["n_dejo_de_usar"] = n_dejo

# [Anotación · líneas 162–177] Para ctrx_quarter y mcaja_ahorro divide el valor del mes por el máximo entre
#   ese valor, el lag1 y el lag2 (ignorando NA); el resultado es NA si ese máximo no es positivo. Siguen
#   aserciones sobre los rangos de las seis variables nuevas.
for c in PARAM["relativas_max3"]:
    x = base[c].to_numpy(dtype="float32")
    maximo = np.fmax(np.fmax(x, lag_de(x, 1)), lag_de(x, 2))     # fmax ignora NA
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.where(maximo > 0, x / maximo, np.nan).astype("float32")
    nuevas[f"{c}_rel_max3"] = rel

# controles de las nuevas
assert np.nanmin(nuevas["n_apagados"]) >= 0 and np.nanmax(nuevas["n_apagados"]) <= len(claves)
assert np.isnan(nuevas["n_apagados_delta1"][~fila_valida[1]]).all(), "delta1 deberia ser NA sin mes anterior"
assert np.nanmax(nuevas["n_dejo_de_usar"]) <= len(claves)
assert (nuevas["n_dejo_de_usar"][~sin_historia] <= nuevas["n_apagados"][~sin_historia]).all(), \
    "No se puede haber dejado de usar mas productos de los que estan apagados"
for c in PARAM["relativas_max3"]:
    r = nuevas[f"{c}_rel_max3"]
    assert np.nanmax(r) <= 1 + 1e-5, f"{c}_rel_max3 mayor que 1"

# [Anotación · líneas 179–200] Graba en CSV, para cada variable nueva y mes, el porcentaje de NA y la media, y
#   una tabla con la tasa de BAJA+2 según el valor de n_apagados en los meses con clase completa.
# resumen de las nuevas por mes y su relacion con la clase (meses con clase completa)
ct = base["clase_ternaria"].astype(str).to_numpy()
completos = meses[:-2]
en_completos = np.isin(mes, completos)
baja2 = (ct == "BAJA+2") & en_completos
filas = []
for nombre, v in nuevas.items():
    for m in meses:
        idx = idx_mes[m]
        filas.append({"variable": nombre, "foto_mes": m, "pct_na": round(100 * np.isnan(v[idx]).mean(), 1),
                      "media": round(float(np.nanmean(v[idx])), 3) if (~np.isnan(v[idx])).any() else np.nan})
pd.DataFrame(filas).to_csv(exp.ruta("nuevas_por_mes"), index=False)

# tasa de BAJA+2 por valor de n_apagados (meses completos): deberia crecer con n_apagados
na = nuevas["n_apagados"]
tabla_ap = (pd.DataFrame({"n_apagados": na[en_completos], "baja2": baja2[en_completos]})
              .groupby("n_apagados")["baja2"].agg(clientes="size", tasa_baja2_pct="mean"))
tabla_ap["tasa_baja2_pct"] = (100 * tabla_ap["tasa_baja2_pct"]).round(3)
tabla_ap.to_csv(exp.ruta("tasa_por_n_apagados"))
print("\nTasa de BAJA+2 segun cantidad de variables clave apagadas (meses con clase completa):")
print(tabla_ap.to_string())
print(f"Variables nuevas listas ({time.time() - t0:.0f} s)")

# [Anotación · líneas 202–228] Para cada una de las variables originales arma la columna del mes, lag1, lag2,
#   delta1 y delta2 en float32 y reemplaza cada una por su ranking con cero fijo, con el control de NA, ceros y
#   signo. Después rankea del mismo modo las seis variables nuevas.
# ---------------------------------------------------------------------------
# 2) Lags/deltas de las 152 originales + ranking de todo (como 03b)
# ---------------------------------------------------------------------------
t0 = time.time()
columnas = {}
for i, c in enumerate(features, start=1):
    x = base[c].to_numpy(dtype="float32")
    crudas = {c: x}
    lags = {k: lag_de(x, k) for k in fila_valida}
    for k in PARAM["lags"]:
        crudas[f"{c}_lag{k}"] = lags[k]
    for k in PARAM["deltas"]:
        crudas[f"{c}_delta{k}"] = x - lags[k]
    for nombre, valores in crudas.items():
        rk = rank_cero_fijo(valores)
        controlar_rank(nombre, valores, rk)
        columnas[nombre] = rk
    del x, crudas, lags
    if i % 25 == 0 or i == len(features):
        print(f"  {i}/{len(features)} variables ({time.time() - t0:.0f} s)", flush=True)

for nombre, valores in nuevas.items():
    rk = rank_cero_fijo(valores)
    controlar_rank(nombre, valores, rk)
    columnas[nombre] = rk
del nuevas
gc.collect()

# [Anotación · líneas 230–238] Aserciones sobre mcuentas_saldo: su lag1 rankeado es NA donde no hay mes
#   anterior, en el primer mes no hay lag1 y en el segundo mes no hay lag2.
# control de lag: en una muestra, el lag1 rankeado de mcuentas_saldo es NA exactamente donde no hay mes anterior
var_ctrl = "mcuentas_saldo" if "mcuentas_saldo" in features else features[0]
assert np.array_equal(np.isnan(columnas[f"{var_ctrl}_lag1"]),
                      ~fila_valida[1] | np.isnan(lag_de(base[var_ctrl].to_numpy(dtype="float32"), 1))), \
    f"El lag1 de {var_ctrl} no respeta los meses faltantes"
# en el primer mes y en abril para lag2 todo tiene que ser NA
primer = idx_mes[meses[0]]
assert np.isnan(columnas[f"{var_ctrl}_lag1"][primer]).all(), "En el primer mes no puede haber lag1"
assert np.isnan(columnas[f"{var_ctrl}_lag2"][idx_mes[meses[1]]]).all(), "En el segundo mes no puede haber lag2"

# [Anotación · líneas 240–265] Arma una tabla Arrow con identificador, mes y clases y le agrega las columnas
#   una por una; la graba en Parquet con zstd y verifica la cantidad de filas y de columnas (5 + variables × 5 +
#   6). Cierra el experimento con los nombres de las variables nuevas.
# ---------------------------------------------------------------------------
# Grabado (columna por columna en una tabla Arrow: no arma un DataFrame gigante)
# ---------------------------------------------------------------------------
t0 = time.time()
tabla = pa.Table.from_pandas(base[NO_FEATURES], preserve_index=False)
del base
gc.collect()
n_nuevas = 0
for nombre in list(columnas):
    tabla = tabla.append_column(nombre, pa.array(columnas.pop(nombre), from_pandas=True))
    n_nuevas += 1
archivo = DIR_DATA / PARAM["dataset_salida"]
pq.write_table(tabla, archivo, compression="zstd")
n_cols = tabla.num_columns
assert tabla.num_rows == n, "Cambio la cantidad de filas al grabar"
assert n_cols == len(NO_FEATURES) + len(features) * 5 + 6, f"Cantidad de columnas inesperada: {n_cols}"
del tabla
gc.collect()
mb = archivo.stat().st_size / 1e6
print(f"\nGrabado {archivo.name}: {n:,} filas x {n_cols} columnas "
      f"({len(features)} x 5 + 6 nuevas + id/mes/clases), {mb:,.0f} MB ({time.time() - t0:.0f} s)")

cerrar_experimento(exp, {"archivo": archivo.name, "columnas": n_cols, "MB": round(mb),
                         "variables_originales": len(features), "claves": len(claves),
                         "nuevas": ["n_apagados", "n_apagados_delta1", "n_apagados_delta2", "n_dejo_de_usar"]
                                   + [f"{c}_rel_max3" for c in PARAM["relativas_max3"]]})
```

### 10_entrega_zulip.py

Experimentos 6xxx: a partir de las probabilidades de una producción escribe, para cada cantidad de envíos, un archivo con los numero_de_cliente de mayor probabilidad, uno por línea y sin encabezado, y verifica su formato. Con configs/6011 genera las listas de 5015, entre ellas la de 12.500.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–30] Docstring: arma los archivos para el bot de Zulip (sólo los numero_de_cliente
#   elegidos, sin encabezado, un id entero por línea, entre 8.000 y 15.000 registros) en dos modos, «final» (un
#   archivo del semillerío) y «semillas» (un archivo por semilla). Importa numpy, pandas y exp_utils.
"""
10_entrega_zulip.py
DMEyF 2026 - Primera Competencia - Experimentos 6xxx

Arma los archivos para el bot @competencia-uno de Zulip:
  - solo los numero_de_cliente a los que se envia estimulo (los N de mayor probabilidad)
  - SIN encabezado, un id por linea, enteros (nunca notacion cientifica: 48000000, no 4.8e+07)
  - entre 8.000 y 15.000 registros, extension .csv, nombre unico

Dos modos:
  "final"     -> UN archivo con el semillerio (probabilidad promediada). Es el que tiene que
                 quedar como ULTIMO submit antes del domingo 11/10 23:59:59.
  "semillas"  -> UN archivo por semilla (hasta 20), desde <id>_prob_por_semilla.parquet que
                 graba 07 con "guardar_prob_por_semilla": true. El bot devuelve la media y el
                 desvio de la ganancia publica entre esos archivos.

Uso:  py -3.12 10_entrega_zulip.py                      (PARAM de abajo)
      py -3.12 10_entrega_zulip.py configs/6001.json    (el JSON reemplaza claves del PARAM)
"""

print("Arrancando 10_entrega_zulip.py ...", flush=True)

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from exp_utils import DIR_EXP, cerrar_experimento, iniciar_experimento

# [Anotación · líneas 32–50] PARAM por defecto (experimento 6001): modo final, fuente 5005_prod_eleccion_4102,
#   13.000 envíos, hasta 20 archivos y 164.647 clientes esperados en 202108. Un JSON pasado por línea de
#   comandos reemplaza esas claves.
# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 6001,
    "nombre": "zulip_final_5005_e13000",
    "descripcion": "Archivo final para Zulip: semillerio de 5005 (retador 4102 prueba 117), 13.000 envios.",
    "modo": "final",                          # "final" o "semillas"
    "fuente": "5005_prod_eleccion_4102",      # carpeta de exp\ con la produccion
    "envios": 13000,
    "max_archivos": 20,
    "clientes_esperados": 164647,             # clientes de 202108
}

if len(sys.argv) > 1:
    config = Path(sys.argv[1])
    PARAM.update(json.loads(config.read_text(encoding="utf-8")))
    PARAM["_config"] = config.name
    print(f"Configuracion tomada de {config}")

# [Anotación · líneas 52–61] Convierte «envios» en lista, exige que cada cantidad esté entre 8.000 y 15.000 y
#   que el modo «semillas» use una sola cantidad. Inicia el experimento, ubica la carpeta fuente y crea la
#   subcarpeta zulip/.
# "envios" puede ser un numero o una lista (en modo "final": un archivo por cada cantidad)
ENVIOS = PARAM["envios"] if isinstance(PARAM["envios"], list) else [PARAM["envios"]]
assert all(8000 <= e <= 15000 for e in ENVIOS), "El bot exige entre 8.000 y 15.000 registros"
if PARAM["modo"] == "semillas":
    assert len(ENVIOS) == 1, "En modo 'semillas' va una sola cantidad de envios"
exp = iniciar_experimento(PARAM)
carpeta_fuente = DIR_EXP / PARAM["fuente"]
id_fuente = carpeta_fuente.name.split("_")[0]
salida = exp.carpeta / "zulip"
salida.mkdir(exist_ok=True)

# [Anotación · líneas 63–82] Lee las probabilidades: en modo final, <id>_probabilidades.csv de la fuente; en
#   modo semillas, las columnas del Parquet por semilla. Verifica que las probabilidades sean finitas y que los
#   ids no estén vacíos ni repetidos, sean enteros y sumen la cantidad esperada de clientes.
# ---------------------------------------------------------------------------
# Probabilidades
# ---------------------------------------------------------------------------
if PARAM["modo"] == "final":
    df = pd.read_csv(carpeta_fuente / f"{id_fuente}_probabilidades.csv")
    columnas = {"semillerio": df["prob"].to_numpy()}
elif PARAM["modo"] == "semillas":
    df = pd.read_parquet(carpeta_fuente / f"{id_fuente}_prob_por_semilla.parquet")
    cols = [c for c in df.columns if c.startswith("s")][:PARAM["max_archivos"]]
    columnas = {c: df[c].to_numpy() for c in cols}
else:
    raise ValueError("modo tiene que ser 'final' o 'semillas'")

for _n, _p in columnas.items():
    assert np.isfinite(_p).all(), f"Hay probabilidades no finitas (NaN o infinito) en {_n}"
ids = df["numero_de_cliente"]
assert ids.notna().all() and ids.is_unique, "Hay ids vacios o repetidos"
assert (ids == ids.round()).all(), "Hay ids no enteros"
ids = ids.astype("int64").to_numpy()
assert len(ids) == PARAM["clientes_esperados"], f"Se esperaban {PARAM['clientes_esperados']:,} clientes, hay {len(ids):,}"

# [Anotación · líneas 84–105] Para cada cantidad de envíos y cada columna ordena por probabilidad descendente
#   (orden estable), toma los primeros N ids y los escribe uno por línea en Z<exp>_<fuente>_e<N>_<nombre>.csv.
#   Relee el archivo y verifica la cantidad de líneas, que todas sean dígitos y que no haya repetidos.
# ---------------------------------------------------------------------------
# Archivos
# ---------------------------------------------------------------------------
archivos = []
listas = {}
for envios in ENVIOS:
    for nombre, prob in columnas.items():
        orden = np.argsort(-prob, kind="stable")
        elegidos = ids[orden[:envios]]
        texto = "\n".join(str(int(x)) for x in elegidos) + "\n"
        # nombre unico: experimento, fuente, envios y modelo (no se repite entre submits)
        archivo = salida / f"Z{exp.id}_{id_fuente}_e{envios}_{nombre}.csv"
        archivo.write_text(texto, encoding="ascii", newline="\n")

        # controles sobre el archivo tal como quedo grabado
        lineas = archivo.read_text(encoding="ascii").split()
        assert len(lineas) == envios, "Cantidad de registros incorrecta"
        assert all(l.isdigit() for l in lineas), "Hay lineas que no son enteros (encabezado, decimales o notacion cientifica)"
        assert len(set(lineas)) == len(lineas), "Hay ids repetidos"
        archivos.append(archivo)
        if len(ENVIOS) == 1:
            listas[nombre] = set(lineas)

# [Anotación · líneas 107–124] Imprime los archivos generados y, si hay varias listas de semillas, la
#   coincidencia promedio entre ellas. Escribe en cuerpo_mensaje.txt el texto sugerido «submit <nombre de la
#   carpeta sin guiones bajos>» y cierra el experimento con la lista de archivos.
print(f"\n{len(archivos)} archivo(s) en {salida}:")
for a in archivos[:5]:
    print(f"  {a.name}")
if len(archivos) > 5:
    print(f"  ... y {len(archivos) - 5} mas")

if len(listas) > 1:
    nombres = list(listas)
    coincid = [len(listas[a] & listas[b]) / ENVIOS[0] for i, a in enumerate(nombres) for b in nombres[i + 1:]]
    print(f"Coincidencia promedio entre archivos de semillas distintas: {np.mean(coincid):.1%}")

cuerpo = f"submit {exp.carpeta.name.replace('_', '')}"
print("\nControles OK: sin encabezado, ids enteros unicos, "
      f"registros por archivo: {', '.join(f'{e:,}' for e in ENVIOS)}.")
print(f"\nCuerpo sugerido del mensaje a @competencia-uno (sin espacios en el nombre):\n    {cuerpo}")
(exp.carpeta / "cuerpo_mensaje.txt").write_text(cuerpo + "\n", encoding="utf-8")

cerrar_experimento(exp, {"archivos": [a.name for a in archivos], "cuerpo": cuerpo})
```

### 08_bo_fuera_de_tiempo.py

Búsqueda de hiperparámetros con Optuna (experimentos 4102 a 4109 según la configuración): entrena con meses anteriores, mide la ganancia de meseta en la mitad A de 202106, confirma con varias semillas en la mitad B y graba <id>_eleccion.json. Con configs/4104 y configs/4107 produce los hiperparámetros del modelo entregado.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–42] Docstring: búsqueda que mide fuera del mes de entrenamiento, con los clientes de
#   junio divididos en mitades A y B; etapa 1 sobre A, etapa 2 de confirmación sobre B y elección grabada en
#   <id>_eleccion.json. Con varios meses de entrenamiento, el min_data_in_leaf de las referencias se multiplica
#   por la cantidad de meses. Importa lightgbm, numpy, optuna, pandas, pyarrow y exp_utils.
"""
08_bo_fuera_de_tiempo.py
DMEyF 2026 - Primera Competencia - Experimento 4102

Optimizacion Bayesiana que mide FUERA DEL MES de entrenamiento (la 4101 media dentro de abril
y eligio modelos que no generalizaban a junio).

  - Los clientes de junio se dividen al azar en dos mitades fijas: A y B.
  - Etapa 1: cada combinacion entrena con TODO abril y se mide en la mitad A de junio.
             La primera prueba son los hiperparametros del z601 (punto de partida conocido).
  - Etapa 2: los mejores de la etapa 1 y el z601 se entrenan con varias semillas y se miden
             en la mitad B, que la busqueda nunca vio: es la estimacion honesta.
  - Eleccion: se usa un candidato de la BO solo si le gana al z601 en la mitad B en
             promedio Y en la mayoria clara de las semillas. Si no, se queda el z601.
             El resultado se graba en 4102_eleccion.json, que lee 07_modelo_final.py.

Reanudable como la 4101 (PARAM["reanudar"] = True).

Varios meses de entrenamiento: PARAM["meses_train"] = [202103, 202104] (si no esta, se usa
"mes_train"). Las referencias (z601 y referencias_extra) se eligieron entrenando con UN mes: su
min_data_in_leaf se multiplica por la cantidad de meses de train, para que cada hoja represente
la misma proporcion de clientes. La eleccion graba fraccion_mes_referencia = cantidad de meses,
asi 07 escala bien al entrenar con otra cantidad de meses.

Uso:  py -3.12 08_bo_fuera_de_tiempo.py                       (PARAM de abajo)
      py -3.12 08_bo_fuera_de_tiempo.py configs/4103.json      (el JSON reemplaza claves del PARAM)
"""

print("Arrancando 08_bo_fuera_de_tiempo.py ...", flush=True)

import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import pyarrow.parquet as pq

from exp_utils import DIR_DATA, DIR_EXP, cerrar_experimento, iniciar_experimento

# [Anotación · líneas 44–96] PARAM por defecto (experimento 4102): dataset ds3001_crudo.parquet con la lista
#   de variables p95, entrenamiento 202104, prueba 202106, clase_binaria2, 150 pruebas (25 iniciales), hasta
#   3.000 árboles, espacio de siete hiperparámetros, parámetros fijos de LightGBM (max_bin 31, bagging_freq 1,
#   deterministic), 5 candidatos a confirmar con 10 semillas, mínimo de 7 semillas ganadas y meseta
#   12.000–17.000.
# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 4102,
    "nombre": "bo_fuera_de_tiempo",
    "descripcion": "Optuna entrenando con 202104 completo y midiendo en la mitad A de 202106 "
                   "(meseta 12-17 mil envios equivalentes). Confirmacion en la mitad B con 10 "
                   "semillas contra z601. Variables p95, crudo + binaria2.",
    "reanudar": False,
    "dataset": "ds3001_crudo.parquet",
    "variables": "4003_canaritos/4003_variables_p95.txt",   # None = todas
    "usar_lag2": False,                     # con variables None: incluir lag2/delta2
    "mes_train": 202104,
    "mes_test": 202106,
    "clase": "clase_binaria2",
    "semilla_mitades": 571369,
    "n_trials": 150,
    "n_startup_trials": 25,
    "max_boost_round": 3000,
    "espacio": {
        "learning_rate": (0.005, 0.1, "log"),
        "num_leaves": (8, 128, "log"),
        "min_data_in_leaf": (50, 5000, "log"),
        "feature_fraction": (0.1, 1.0, "lineal"),
        "bagging_fraction": (0.2, 1.0, "lineal"),
        "lambda_l1": (0.001, 10.0, "log"),
        "lambda_l2": (0.001, 100.0, "log"),
    },
    "lgbm_fijos": {
        "objective": "binary",
        "boosting_type": "gbdt",
        "metric": "None",
        "max_bin": 31,
        "bagging_freq": 1,
        "feature_pre_filter": False,
        "first_metric_only": True,
        "deterministic": True,
        "force_row_wise": True,
        "verbose": -1,
    },
    "semilla_sampler": 571369,
    # puntos de partida: siempre se agrega el z601; aca se pueden sumar otros conocidos
    # (cada uno: {"nombre", "params", "arboles"}). Tambien compiten en la etapa 2 como referencias.
    "referencias_extra": [],
    "top_confirmar": 5,
    "semillas_confirmacion": 10,
    "semillas_base": [571369, 849571, 355049, 655531, 700103],
    "regla_minimo_semillas_ganadas": 7,     # de 10, para reemplazar al z601
    "meseta_mes_completo": [12000, 17000],  # en la mitad se usa la mitad de esos envios
    "ganancia_acierto": 1_072_500,
    "costo_estimulo": 27_500,
}

# [Anotación · líneas 98–111] Hiperparámetros de referencia z601 y sus 250 árboles. Si se pasa un JSON por
#   línea de comandos, sus claves reemplazan las de PARAM; inicia el experimento y toma los valores de ganancia
#   y costo.
Z601 = {"learning_rate": 0.019868, "num_leaves": 16, "min_data_in_leaf": 816,
        "feature_fraction": 0.277155, "bagging_fraction": 0.634130, "lambda_l1": 0.001,
        "lambda_l2": 0.001}
Z601_ARBOLES = 250

if len(sys.argv) > 1:
    config = Path(sys.argv[1])
    PARAM.update(json.loads(config.read_text(encoding="utf-8")))
    PARAM["_config"] = config.name
    print(f"Configuracion tomada de {config}")

exp = iniciar_experimento(PARAM)
GAN, COSTO = PARAM["ganancia_acierto"], PARAM["costo_estimulo"]
NO_FEATURES = {"numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"}

# [Anotación · líneas 113–132] Define las variables (lista de un archivo o todas las columnas, con o sin lag2
#   y delta2), arma la lista de meses de entrenamiento y lee del Parquet esos meses más el mes de prueba.
#   Verifica que el mes de prueba no esté en el entrenamiento y que no haya filas de entrenamiento sin clase.
# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
t0 = time.time()
archivo = DIR_DATA / PARAM["dataset"]
if PARAM["variables"]:
    features = (DIR_EXP / PARAM["variables"]).read_text(encoding="utf-8").split()
else:
    features = [c for c in pq.ParquetFile(archivo).schema_arrow.names
                if c not in NO_FEATURES
                and (PARAM.get("usar_lag2", False) or not (c.endswith("_lag2") or c.endswith("_delta2")))]
MESES_TRAIN = list(PARAM.get("meses_train") or [PARAM["mes_train"]])
assert PARAM["mes_test"] not in MESES_TRAIN, "El mes de test no puede estar en train"
df = pd.read_parquet(archivo, columns=features + ["numero_de_cliente", "foto_mes", "clase_ternaria", PARAM["clase"]],
                     filters=[("foto_mes", "in", MESES_TRAIN + [PARAM["mes_test"]])])
train = df[df["foto_mes"].isin(MESES_TRAIN)].reset_index(drop=True)
assert sorted(train["foto_mes"].unique()) == sorted(MESES_TRAIN), "Faltan meses de train"
assert train[PARAM["clase"]].notna().all(), "Hay filas de train sin clase"
test = df[df["foto_mes"] == PARAM["mes_test"]].reset_index(drop=True)
del df

# [Anotación · líneas 134–152] Divide los clientes del mes de prueba en mitades A y B: si la configuración
#   trae «mitades_desde», relee la asignación de otro experimento; si no, baraja los clientes de cada clase
#   ternaria con semilla_mitades y manda la mitad a cada grupo. Graba la asignación en <id>_mitades_junio.csv.
# mitades de junio estratificadas por clase ternaria (misma cantidad de BAJA+2 en cada una)
ternaria_test = test["clase_ternaria"].astype(str).to_numpy()
if PARAM.get("mitades_desde"):
    # reutiliza las mitades de otro experimento: la mitad B sigue sin verse en ninguna busqueda
    previas = pd.read_csv(DIR_EXP / PARAM["mitades_desde"]).set_index("numero_de_cliente")["mitad"]
    mitad = test["numero_de_cliente"].map(previas).to_numpy()
    assert pd.notna(mitad).all(), "Hay clientes de junio que no estan en las mitades reutilizadas"
    mitad = mitad.astype("U1")
    print(f"Mitades reutilizadas de {PARAM['mitades_desde']}")
else:
    rng = np.random.default_rng(PARAM["semilla_mitades"])
    mitad = np.empty(len(test), dtype="U1")
    for clase in np.unique(ternaria_test):
        idx = np.flatnonzero(ternaria_test == clase)
        rng.shuffle(idx)
        mitad[idx[: len(idx) // 2]] = "A"
        mitad[idx[len(idx) // 2:]] = "B"
pd.DataFrame({"numero_de_cliente": test["numero_de_cliente"], "mitad": mitad}) \
    .to_csv(exp.ruta("mitades_junio"), index=False)

# [Anotación · líneas 154–172] Arma las matrices de entrenamiento, de la mitad A y de la mitad B y los
#   indicadores de BAJA+2 de cada mitad. La función meseta ordena por probabilidad, acumula la ganancia y
#   promedia entre la mitad de los envíos de «meseta_mes_completo» (6.000 a 8.500), multiplicado por 2;
#   feval_meseta la expone como métrica de LightGBM.
X_train, y_train = train[features], train[PARAM["clase"]].astype(int).to_numpy()
XA, XB = test.loc[mitad == "A", features], test.loc[mitad == "B", features]
baja2A = ternaria_test[mitad == "A"] == "BAJA+2"
baja2B = ternaria_test[mitad == "B"] == "BAJA+2"
lo, hi = (e // 2 for e in PARAM["meseta_mes_completo"])   # envios equivalentes en media poblacion
print(f"{len(features)} variables | train {len(train):,} filas {MESES_TRAIN} | mitad A {len(XA):,} ({baja2A.sum()} BAJA+2) | "
      f"mitad B {len(XB):,} ({baja2B.sum()} BAJA+2) ({time.time() - t0:.0f} s)")
dtrain = lgb.Dataset(X_train, label=y_train, free_raw_data=False)


def meseta(prob, es_baja2):
    """Ganancia promedio entre 6.000 y 8.500 envios de media poblacion, x2 = mes completo."""
    orden = np.argsort(-prob, kind="stable")
    acum = np.cumsum(np.where(es_baja2[orden], GAN, -COSTO))
    return 2 * acum[lo - 1:hi].mean()


def feval_meseta(preds, data):
    return "meseta", meseta(preds, data.es_baja2), True


# [Anotación · líneas 175–204] Función objetivo de la etapa 1: sugiere cada hiperparámetro del espacio
#   (enteros para num_leaves y min_data_in_leaf, escala logarítmica según el caso), entrena con los meses de
#   entrenamiento midiendo la meseta en la mitad A con corte temprano de paciencia 50 + 5/learning_rate y, si
#   hay varias semillas por prueba, promedia sus curvas. Guarda la iteración de mayor meseta como best_iter y
#   devuelve ese valor.
# ---------------------------------------------------------------------------
# Etapa 1: busqueda midiendo en la mitad A
# ---------------------------------------------------------------------------
def objetivo(trial):
    t = time.time()
    p = {}
    for nombre, (a, b, escala) in PARAM["espacio"].items():
        if nombre in ("num_leaves", "min_data_in_leaf"):
            p[nombre] = trial.suggest_int(nombre, a, b, log=(escala == "log"))
        else:
            p[nombre] = trial.suggest_float(nombre, a, b, log=(escala == "log"))
    # PARAM["semillas_por_prueba"] > 1: la curva de meseta en A es el promedio de varias semillas
    # (menos ruido al elegir por A). Cada semilla corta con su propio corte temprano; se promedian
    # las curvas hasta la longitud de la mas corta.
    historias = []
    for semilla in PARAM["semillas_base"][:int(PARAM.get("semillas_por_prueba", 1))]:
        params = dict(PARAM["lgbm_fijos"], **p, seed=semilla)
        dA = lgb.Dataset(XA, label=(baja2A).astype(int), reference=dtrain, free_raw_data=False)
        dA.es_baja2 = baja2A
        registro = {}
        lgb.train(params, dtrain, num_boost_round=PARAM["max_boost_round"], valid_sets=[dA],
                  valid_names=["A"], feval=feval_meseta,
                  callbacks=[lgb.early_stopping(int(50 + 5 / params["learning_rate"]), verbose=False),
                             lgb.record_evaluation(registro)])
        historias.append(np.array(registro["A"]["meseta"]))
    largo = min(len(h_) for h_ in historias)
    hist = np.mean([h_[:largo] for h_ in historias], axis=0)
    trial.set_user_attr("best_iter", int(hist.argmax()) + 1)
    trial.set_user_attr("minutos", round((time.time() - t) / 60, 2))
    return float(hist.max())


# [Anotación · líneas 207–214] informar imprime el avance de cada prueba y vuelve a grabar <id>_pruebas.csv
#   con todas las pruebas del estudio.
def informar(study, trial):
    if trial.value is None:
        return
    hechos = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
    print(f"  prueba {trial.number:3d} | meseta A {trial.value / 1e6:6.1f} M | "
          f"{trial.user_attrs['best_iter']:4d} arboles | {trial.user_attrs['minutos']:.1f} min | "
          f"mejor {study.best_value / 1e6:.1f} M | {hechos}/{PARAM['n_trials']}", flush=True)
    study.trials_dataframe().to_csv(exp.ruta("pruebas"), index=False)


# [Anotación · líneas 217–246] Crea el estudio de Optuna (maximizar, almacenamiento SQLite en la carpeta del
#   experimento, TPESampler con semilla y pruebas iniciales). Arma las referencias (z601 y referencias_extra)
#   con min_data_in_leaf multiplicado por la cantidad de meses de entrenamiento y las encola como primeras
#   pruebas, recortando al rango de búsqueda los valores que caen fuera; ejecuta las pruebas que faltan.
optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(
    direction="maximize", study_name=f"exp{exp.id}",
    storage=f"sqlite:///{(exp.carpeta / f'{exp.id}_optuna.db').as_posix()}", load_if_exists=True,
    sampler=optuna.samplers.TPESampler(seed=PARAM["semilla_sampler"],
                                       n_startup_trials=PARAM["n_startup_trials"]))
REFERENCIAS = [{"nombre": "z601", "params": Z601, "arboles": Z601_ARBOLES}] + list(PARAM["referencias_extra"])
# las referencias se eligieron con 1 mes de train: min_data_in_leaf escalado por cantidad de meses
REFERENCIAS = [dict(r, params=dict(r["params"], min_data_in_leaf=int(round(r["params"]["min_data_in_leaf"]
                                                                            * len(MESES_TRAIN)))))
               for r in REFERENCIAS]
if len(MESES_TRAIN) > 1:
    print("Referencias con min_data_in_leaf x", len(MESES_TRAIN), ":",
          {r["nombre"]: r["params"]["min_data_in_leaf"] for r in REFERENCIAS})


def dentro_del_espacio(k, v):
    """Para encolar una referencia: si su valor cae fuera del rango buscado, se usa el borde."""
    a, b, _ = PARAM["espacio"][k]
    return type(v)(min(max(v, a), b))
if len(study.trials) == 0:
    for ref in REFERENCIAS:            # primeras pruebas: los puntos de partida conocidos
        study.enqueue_trial({k: dentro_del_espacio(k, ref["params"][k]) for k in PARAM["espacio"]},
                            skip_if_exists=True)
hechos = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
faltan = PARAM["n_trials"] - hechos
print(f"\n=== Etapa 1: busqueda en mitad A ({hechos} hechas, faltan {max(faltan, 0)}) ===")
if faltan > 0:
    study.optimize(objetivo, n_trials=faltan, callbacks=[informar], catch=(Exception,))
study.trials_dataframe().to_csv(exp.ruta("pruebas"), index=False)

# [Anotación · líneas 248–265] Etapa 2: arma la lista de semillas (las base más primos sorteados) hasta
#   semillas_confirmacion. Los candidatos son las referencias y las top_confirmar pruebas de mayor meseta en A,
#   sin contar las pruebas encoladas como referencia.
# ---------------------------------------------------------------------------
# Etapa 2: confirmacion en la mitad B (nunca vista por la busqueda)
# ---------------------------------------------------------------------------
semillas = list(PARAM["semillas_base"])
rng_s = np.random.default_rng(PARAM["semillas_base"][0])
while len(semillas) < PARAM["semillas_confirmacion"]:
    c = int(rng_s.integers(100003, 999983))
    if all(c % d for d in range(2, int(c ** 0.5) + 1)) and c not in semillas:
        semillas.append(c)
semillas = semillas[:PARAM["semillas_confirmacion"]]

completas = [t for t in study.trials if t.value is not None]
# las primeras pruebas son las referencias encoladas: no compiten como "retadores"
busqueda = [t for t in completas if t.number >= len(REFERENCIAS)]
mejores = sorted(busqueda, key=lambda t: t.value, reverse=True)[:PARAM["top_confirmar"]]
candidatos = [dict(ref, meseta_A=None, es_referencia=True) for ref in REFERENCIAS]
candidatos += [{"nombre": f"prueba_{t.number}", "params": t.params, "arboles": t.user_attrs["best_iter"],
                "meseta_A": t.value, "es_referencia": False} for t in mejores]

# [Anotación · líneas 267–301] Entrena cada candidato con cada semilla y su cantidad fija de árboles, y mide
#   la meseta en la mitad B. Graba el detalle por semilla y un resumen con la meseta en A, la media y el desvío
#   en B y en cuántas semillas cada candidato supera a la referencia de mayor media en B.
print(f"\n=== Etapa 2: confirmacion en mitad B, {len(candidatos)} candidatos x {len(semillas)} semillas ===")
filas = []
for cand in candidatos:
    t = time.time()
    params = dict(PARAM["lgbm_fijos"], **cand["params"])
    params = {k: v for k, v in params.items() if k not in ("metric", "first_metric_only")}
    for semilla in semillas:
        modelo = lgb.train(dict(params, seed=semilla), dtrain, num_boost_round=cand["arboles"])
        filas.append({"candidato": cand["nombre"], "semilla": semilla,
                      "meseta_B": meseta(modelo.predict(XB), baja2B)})
    print(f"  {cand['nombre']}: listo ({(time.time() - t) / 60:.1f} min)", flush=True)

detalle = pd.DataFrame(filas)
detalle.to_csv(exp.ruta("confirmacion_por_semilla"), index=False)
piv = detalle.pivot(index="semilla", columns="candidato", values="meseta_B")
refs = [c for c in candidatos if c["es_referencia"]]
ref_mejor = max(refs, key=lambda c: piv[c["nombre"]].mean())
resumen = []
for cand in candidatos:
    n = cand["nombre"]
    resumen.append({
        "candidato": n,
        "tipo": "referencia" if cand["es_referencia"] else "busqueda",
        "meseta_A_M": None if cand["meseta_A"] is None else round(cand["meseta_A"] / 1e6, 1),
        "meseta_B_M": round(piv[n].mean() / 1e6, 1),
        "desvio_B_M": round(piv[n].std() / 1e6, 1),
        f"semillas_mejor_que_{ref_mejor['nombre']}": "-" if n == ref_mejor["nombre"]
        else f"{int((piv[n] > piv[ref_mejor['nombre']]).sum())}/{len(semillas)}",
        "arboles": cand["arboles"],
        **{k: round(v, 4) if isinstance(v, float) else v for k, v in cand["params"].items()},
    })
tabla = pd.DataFrame(resumen).sort_values("meseta_B_M", ascending=False)
tabla.to_csv(exp.ruta("resumen"), index=False)
print("\n=== RESUMEN (meseta 12-17 mil envios equivalentes, millones) ===")
print(tabla.to_string(index=False))

# [Anotación · líneas 303–340] Elección: el retador es la prueba de mayor meseta en A; reemplaza a la
#   referencia sólo si su media en B es mayor y gana en al menos regla_minimo_semillas_ganadas semillas (con el
#   valor alternativo de «regla_eleccion» se elige el retador sin esa condición). Graba <id>_eleccion.json con
#   origen, parámetros, árboles, fraccion_mes_referencia igual a la cantidad de meses de entrenamiento y la
#   evidencia.
# ---------------------------------------------------------------------------
# Eleccion
# ---------------------------------------------------------------------------
# El retador se elige por la mitad A (la busqueda) y se COMPARA en B contra la mejor referencia:
# asi B queda como medicion honesta (no se usa para elegir entre retadores).
retadores = [c for c in candidatos if not c["es_referencia"]]
mejor = max(retadores, key=lambda c: c["meseta_A"]) if retadores else None
ganadas = int((piv[mejor["nombre"]] > piv[ref_mejor["nombre"]]).sum()) if mejor else 0
supera = (mejor is not None and piv[mejor["nombre"]].mean() > piv[ref_mejor["nombre"]].mean()
          and ganadas >= PARAM["regla_minimo_semillas_ganadas"])
if PARAM.get("regla_eleccion", "confirmacion") == "mejor_A":
    # regla limpia: el elegido es el mejor de la busqueda segun la mitad A; B solo se informa
    assert mejor is not None, "La busqueda no produjo retadores"
    elegido = mejor
else:
    elegido = mejor if supera else ref_mejor
fijos = {k: v for k, v in PARAM["lgbm_fijos"].items() if k not in ("metric", "first_metric_only")}
eleccion = {
    "origen": f"{exp.id} {elegido['nombre']}",
    "params": {**fijos, **elegido["params"]},
    "arboles": int(elegido["arboles"]),
    "fraccion_mes_referencia": float(len(MESES_TRAIN)),   # meses completos de train al elegir
    "variables": PARAM["variables"],
    "evidencia": {
        "meseta_B_elegido_M": round(piv[elegido["nombre"]].mean() / 1e6, 1),
        "referencia": ref_mejor["nombre"],
        "meseta_B_referencia_M": round(piv[ref_mejor["nombre"]].mean() / 1e6, 1),
        "meseta_B_z601_M": round(piv["z601"].mean() / 1e6, 1),
        "mejor_retador_segun_A": mejor["nombre"] if mejor else None,
        "semillas_ganadas_por_el_retador": f"{ganadas}/{len(semillas)}",
    },
}
with open(exp.ruta("eleccion", ext="json"), "w", encoding="utf-8") as f:
    json.dump(eleccion, f, indent=2, ensure_ascii=False)
print(f"\nELECCION: {eleccion['origen']}  (meseta B {eleccion['evidencia']['meseta_B_elegido_M']} M; "
      f"mejor referencia {ref_mejor['nombre']} {eleccion['evidencia']['meseta_B_referencia_M']} M; "
      f"retador elegido por A: {eleccion['evidencia']['mejor_retador_segun_A']}, "
      f"gano {ganadas}/{len(semillas)} semillas)")

# [Anotación · líneas 342–350] Genera los gráficos HTML de historia y de cortes por parámetro de Optuna y
#   cierra el experimento con la cantidad de pruebas y la elección.
try:
    from optuna.visualization import plot_optimization_history, plot_slice
    plot_optimization_history(study).write_html(exp.ruta("historia", ext="html"), include_plotlyjs="cdn")
    plot_slice(study).write_html(exp.ruta("cortes_por_parametro", ext="html"), include_plotlyjs="cdn")
except Exception as e:
    print(f"(No se pudieron generar los graficos de Optuna: {e})")

cerrar_experimento(exp, {"pruebas": len(completas), "eleccion": eleccion["origen"],
                         "evidencia": eleccion["evidencia"]})
```

### profesor_final.bat

Lote de Windows que encadena la comparación 5107, la búsqueda 4107, el modelo final 5015 y los archivos 6011, con un log por paso en logs/.

```
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–11] Encabezado en comentarios REM con los pasos del lote: 5107 (entrenar con abril
#   contra marzo + abril), 4107 (búsqueda con marzo + abril), 5015 (modelo final con marzo a junio y 50
#   semillas) y 6011 (archivos para Zulip de 11.000 a 13.500 envíos).
@echo off
REM ============================================================================
REM  profesor_final.bat - DMEyF 2026 Primera Competencia
REM  Indicaciones del profesor (reunion del 9/10):
REM   0) 5107  sirve marzo: abril solo contra marzo + abril, misma receta e hiperparametros (~20 min)
REM   1) 4107  Bayesiana entrenando con marzo + abril (toda la informacion, aunque haya NA),
REM            rangos del profesor, 50 pruebas, confirmacion con 20 semillas en la mitad B
REM   2) 5015  modelo final entrenando con marzo a junio, 50 semillas
REM   3) 6011  archivos para Zulip: 11.000 a 13.500 envios
REM  ~4 h 20 min. Si un paso falla, sigue con el siguiente. Logs en logs\
REM ============================================================================

# [Anotación · líneas 13–21] Fija el intérprete «py -3.12», se ubica en la carpeta del lote, crea logs/ y se
#   detiene si falta data\ds3003_rank_extra.parquet.
set "PY=py -3.12"

cd /d "%~dp0"
if not exist logs mkdir logs
if not exist data\ds3003_rank_extra.parquet (
    echo ERROR: falta data\ds3003_rank_extra.parquet. Correr antes fe_extra.bat.
    pause
    exit /b 1
)

# [Anotación · líneas 23–32] Comprueba que el intérprete pueda importar lightgbm, optuna, pandas, pyarrow y
#   plotly; guarda la salida en logs\entorno_profesor_final.txt y se detiene si la importación termina con
#   error.
echo Verificando Python y librerias...
%PY% -c "import sys, lightgbm, optuna, pandas, pyarrow, plotly; print('Python', sys.version)" > logs\entorno_profesor_final.txt 2>&1
if errorlevel 1 (
    echo ERROR: el Python elegido no funciona o le faltan librerias. Detalle:
    type logs\entorno_profesor_final.txt
    pause
    exit /b 1
)
type logs\entorno_profesor_final.txt
echo.

# [Anotación · líneas 34–44] Ejecuta en orden 11_comparar_pipelines.py con configs\5107,
#   08_bo_fuera_de_tiempo.py con configs\4107, 07_modelo_final.py con configs\5015 y 10_entrega_zulip.py con
#   configs\6011, anotando inicio y fin en logs\profesor_final_tiempos.txt.
echo Inicio: %date% %time% > logs\profesor_final_tiempos.txt
call :paso 0 "11_comparar_pipelines.py configs\5107_comparar_marzo.json" 5107
call :paso 1 "08_bo_fuera_de_tiempo.py configs\4107_bo_profesor_mar_abr.json" 4107
call :paso 2 "07_modelo_final.py configs\5015_prod_profesor_mar_jun.json" 5015
call :paso 3 "10_entrega_zulip.py configs\6011_zulip_final_5015.json" 6011
echo Fin: %date% %time% >> logs\profesor_final_tiempos.txt

echo.
echo ==== TERMINADO. Revisar logs\profesor_final_tiempos.txt y los logs de cada paso ====
pause
exit /b

# [Anotación · líneas 46–51] Subrutina :paso: corre el comando recibido con la salida redirigida a
#   logs\<id>.txt y anota hora de inicio, hora de fin y código de salida; el lote continúa con el paso siguiente
#   aunque el anterior termine con error.
:paso
echo [%date% %time%] Paso %1 de 3: %~2
echo [%date% %time%] Paso %1 de 3 (%3): inicio >> logs\profesor_final_tiempos.txt
%PY% -u %~2 > logs\%3.txt 2>&1
echo [%date% %time%] Paso %1 de 3 (%3): fin, codigo %errorlevel% >> logs\profesor_final_tiempos.txt
exit /b
```

### 03b_fe_rank_total.py

Experimento 3002: genera ds3002_rank_total.parquet con lags y deltas de orden 1 y 2 y ranking de todas las columnas dentro de cada mes con cero fijo. Es el dataset de la búsqueda 4104, de la que sale la prueba 23 (camino completo del README).

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–27] Docstring: lags y deltas de orden 1 y 2 sobre los valores originales y después
#   ranking de todas las columnas dentro de cada mes con cero fijo. Importa numpy, pandas, pyarrow y exp_utils.
"""
03b_fe_rank_total.py
DMEyF 2026 - Primera Competencia - Experimento 3002

Feature engineering con la receta del profesor:
  1. Lags y deltas de orden 1 y 2 sobre los valores CRUDOS de todas las variables
     (vacio si el cliente no estaba exactamente k meses antes; los NA se mantienen).
  2. Despues, TODAS las columnas (originales, lags y deltas) se reemplazan por su ranking
     dentro de cada mes, con el cero fijo:
        positivos -> (0, 1]     negativos -> [-1, 0)     cero -> 0     NA -> NA
     Es un percentil: equiespaciado, no conserva distancias. Corrige inflacion y aguinaldo.
  No se rankean numero_de_cliente, foto_mes ni las clases.

Uso:  py -3.12 03b_fe_rank_total.py   (despues de 01_preparar_dataset.py)
"""

print("Arrancando 03b_fe_rank_total.py ...", flush=True)

import gc
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from exp_utils import DIR_DATA, cerrar_experimento, iniciar_experimento

# [Anotación · líneas 29–44] PARAM del experimento 3002: entrada ds1001_base.parquet, salida
#   ds3002_rank_total.parquet, lags [1, 2] y deltas [1, 2]. Define las cinco columnas que no son variables
#   (identificador, mes y las tres clases).
# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 3002,
    "nombre": "fe_lag2_rank_total",
    "descripcion": "Lags y deltas 1 y 2 sobre valores crudos; despues todas las columnas rankeadas "
                   "dentro de cada mes con cero fijo (positivos 0..1, negativos -1..0, NA se mantiene).",
    "dataset_entrada": "ds1001_base.parquet",
    "dataset_salida": "ds3002_rank_total.parquet",
    "lags": [1, 2],
    "deltas": [1, 2],
}

exp = iniciar_experimento(PARAM)
NO_FEATURES = ["numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"]

# [Anotación · líneas 46–63] Lee el dataset base, lo ordena por cliente y mes y arma la lista de variables; se
#   detiene si alguna no es numérica. Calcula el período consecutivo de cada fila y los índices de las filas de
#   cada mes.
# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------
t0 = time.time()
base = pd.read_parquet(DIR_DATA / PARAM["dataset_entrada"])
base = base.sort_values(["numero_de_cliente", "foto_mes"], kind="mergesort").reset_index(drop=True)
features = [c for c in base.columns if c not in NO_FEATURES]
no_numericas = [c for c in features if not pd.api.types.is_numeric_dtype(base[c])]
if no_numericas:
    raise ValueError(f"Hay variables no numericas, revisar: {no_numericas}")
print(f"Leido {PARAM['dataset_entrada']}: {len(base):,} filas, {len(features)} variables ({time.time() - t0:.0f} s)")

n = len(base)
mes = base["foto_mes"].to_numpy()
cliente = base["numero_de_cliente"].to_numpy()
periodo = (mes // 100) * 12 + mes % 100
meses = sorted(int(m) for m in np.unique(mes))
idx_mes = {m: np.flatnonzero(mes == m) for m in meses}

# [Anotación · líneas 65–77] Para k = 1 y 2 marca las filas en las que la fila k posiciones arriba es del
#   mismo cliente y de exactamente k meses antes. lag_de desplaza el vector k posiciones y deja NaN donde esa
#   condición no se cumple.
# fila k posiciones arriba = mismo cliente exactamente k meses antes
fila_valida = {}
for k in sorted(set(PARAM["lags"]) | set(PARAM["deltas"])):
    ok = np.zeros(n, dtype=bool)
    ok[k:] = (cliente[k:] == cliente[:-k]) & (periodo[k:] - periodo[:-k] == k)
    fila_valida[k] = ok


def lag_de(x, k):
    out = np.full(n, np.nan, dtype="float32")
    out[k:] = x[:-k]
    out[~fila_valida[k]] = np.nan
    return out


# [Anotación · líneas 80–92] rank_cero_fijo: dentro de cada mes, los positivos se reemplazan por su rango
#   percentil (empates por promedio) en (0,1], los negativos por el rango percentil de su valor absoluto con
#   signo menos en [−1,0), el cero queda en 0 y el NA en NA.
def rank_cero_fijo(x):
    """Dentro de cada mes: positivos (0,1], negativos [-1,0), cero 0, NA NA."""
    out = np.full(n, np.nan, dtype="float32")
    for m, idx in idx_mes.items():
        v = x[idx]
        r = np.where(np.isnan(v), np.nan, 0.0)
        pos, neg = v > 0, v < 0
        if pos.any():
            r[pos] = pd.Series(v[pos]).rank(method="average", pct=True).to_numpy()
        if neg.any():
            r[neg] = -pd.Series(-v[neg]).rank(method="average", pct=True).to_numpy()
        out[idx] = r
    return out


# [Anotación · líneas 95–123] Para cada variable arma la columna original, lag1, lag2, delta1 y delta2 en
#   float32 y reemplaza cada una por su ranking; verifica que NA y ceros se conserven y que todo quede en [−1,
#   1]. Para mpayroll guarda la mediana de los positivos por mes antes y después del ranking.
# ---------------------------------------------------------------------------
# 1) lags y deltas sobre crudos  2) ranking de todo
# ---------------------------------------------------------------------------
t0 = time.time()
columnas = {}
ejemplo = "mpayroll" if "mpayroll" in features else features[0]
comparacion = {}
for i, c in enumerate(features, start=1):
    x = base[c].to_numpy(dtype="float32")
    crudas = {c: x}
    lags = {k: lag_de(x, k) for k in fila_valida}
    for k in PARAM["lags"]:
        crudas[f"{c}_lag{k}"] = lags[k]
    for k in PARAM["deltas"]:
        crudas[f"{c}_delta{k}"] = x - lags[k]
    for nombre, valores in crudas.items():
        rk = rank_cero_fijo(valores)
        # controles: NA, ceros y signos se conservan; todo en [-1, 1]
        assert np.array_equal(np.isnan(rk), np.isnan(valores)), f"Cambiaron los NA en {nombre}"
        assert np.array_equal(rk == 0, valores == 0), f"Cambiaron los ceros en {nombre}"
        assert np.nanmin(rk, initial=0) >= -1 and np.nanmax(rk, initial=0) <= 1, f"Fuera de rango en {nombre}"
        columnas[nombre] = rk
    if c == ejemplo:
        for m in meses:
            v, r = x[idx_mes[m]], columnas[c][idx_mes[m]]
            comparacion[m] = {"mediana_cruda_positivos": float(np.nanmedian(v[v > 0])) if (v > 0).any() else np.nan,
                              "mediana_rank_positivos": float(np.nanmedian(r[r > 0])) if (r > 0).any() else np.nan}
    if i % 25 == 0 or i == len(features):
        print(f"  {i}/{len(features)} variables ({time.time() - t0:.0f} s)", flush=True)

# [Anotación · líneas 125–130] Graba en CSV la comparación de medianas de mpayroll por mes (valor original
#   contra valor rankeado) y la imprime.
comp = pd.DataFrame(comparacion).T
comp.index.name = "foto_mes"
comp.to_csv(exp.ruta(f"efecto_rank_{ejemplo}"))
print(f"\nEfecto del ranking sobre {ejemplo} (mediana de los positivos por mes):")
print(comp.round(3).to_string())
print("Lectura: la mediana cruda salta en junio (aguinaldo); la rankeada queda fija cerca de 0,5.")

# [Anotación · líneas 132–149] Arma una tabla Arrow con las cinco columnas de identificación y clase más todas
#   las columnas rankeadas y la graba en Parquet con zstd. Cierra el experimento con nombre de archivo, cantidad
#   de columnas, tamaño y cantidad de variables originales.
# ---------------------------------------------------------------------------
# Grabado
# ---------------------------------------------------------------------------
t0 = time.time()
tabla = pa.Table.from_pandas(base[NO_FEATURES], preserve_index=False)
for nombre, arr in columnas.items():
    tabla = tabla.append_column(nombre, pa.array(arr, from_pandas=True))
archivo = DIR_DATA / PARAM["dataset_salida"]
pq.write_table(tabla, archivo, compression="zstd")
n_cols = tabla.num_columns
del tabla, columnas
gc.collect()
mb = archivo.stat().st_size / 1e6
print(f"\nGrabado {archivo.name}: {n:,} filas x {n_cols} columnas ({len(features)} x 5 + id/mes/clases), "
      f"{mb:,.0f} MB ({time.time() - t0:.0f} s)")

cerrar_experimento(exp, {"archivo": archivo.name, "columnas": n_cols, "MB": round(mb),
                         "variables_originales": len(features)})
```

### 07_modelo_final.py

Semillerío de LightGBM (experimentos 5xxx): con configs/5015 entrena 50 modelos con 202103–202106, promedia las probabilidades de 202108 y graba 5015_probabilidades.csv y un archivo por cantidad de envíos. Tiene además un modo «simulacion» que mide la ganancia en un mes con clase.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–37] Docstring: semillerío del mismo LightGBM con dos modos, «simulacion» (mide
#   ganancia en un mes con clase) y «produccion» (predice el mes de la competencia), y tres orígenes de
#   hiperparámetros (z601, una prueba de una búsqueda o un archivo de elección). Importa lightgbm, numpy,
#   pandas, plotly, pyarrow y exp_utils.
"""
07_modelo_final.py
DMEyF 2026 - Primera Competencia - Experimentos 5xxx

Modelo final con SEMILLERIO: el mismo LightGBM entrenado con muchas semillas; se promedian
las probabilidades y se ordena a los clientes por ese promedio.

Dos modos (PARAM["modo"]):
  "simulacion"  -> aplica la receta sobre un mes CON clase conocida y mide la ganancia por
                   cantidad de envios, comparando el semillerio contra una semilla sola.
  "produccion"  -> entrena con los meses finales, predice el mes de Kaggle y genera un
                   archivo de entrega por cada cantidad de envios.

Hiperparametros (PARAM["hiperparametros"]):
  "z601"                                              -> los del notebook z601 de la catedra
  {"bo": "4101_bo_crudo_p95", "prueba": 73}            -> una prueba de una Optimizacion Bayesiana
  {"eleccion": "4102_bo_fuera_de_tiempo/4102_eleccion.json"} -> lo que eligio el script 08

Uso:  python 07_modelo_final.py                      (usa el PARAM de abajo)
      python 07_modelo_final.py configs/5003.json    (el JSON reemplaza las claves que trae)
"""

print("Arrancando 07_modelo_final.py ...", flush=True)

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pyarrow.parquet as pq

from exp_utils import DIR_DATA, DIR_EXP, cerrar_experimento, iniciar_experimento

# [Anotación · líneas 39–65] PARAM por defecto (experimento 5001, simulación): dataset ds3001_crudo.parquet,
#   lista de variables p95 de canaritos, hiperparámetros z601, entrenamiento 202104 y predicción 202106,
#   clase_binaria2, 20 semillas con cinco semillas base, envíos de 12.000 a 19.000 cada 500, meseta
#   12.000–17.000, ganancia 1.072.500 y costo 27.500.
# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 5001,
    "nombre": "sim_z601_p95",
    "descripcion": "Simulacion: semillerio 20 semillas, params z601, crudo + binaria2, "
                   "variables p95. Train 202104 -> junio.",
    "modo": "simulacion",                     # "simulacion" o "produccion"
    "dataset": "ds3001_crudo.parquet",
    # archivo con la lista de variables, o None para usar todas (lag2/delta2 solo si usar_lag2)
    "variables": "4003_canaritos/4003_variables_p95.txt",
    "hiperparametros": "z601",                # o {"bo": "4101_bo_crudo_p95", "prueba": 73}
    # simulacion: [202104] -> 202106     produccion: [202104, 202105, 202106] -> 202108
    "meses_train": [202104],
    "mes_prediccion": 202106,
    "clase": "clase_binaria2",
    # min_data_in_leaf se escala por FILAS: si se entrena con mas filas que las usadas al
    # elegir los hiperparametros, cada hoja sigue representando la misma proporcion de clientes
    "escalar_min_data_in_leaf": True,
    "n_semillas": 20,                         # las 5 tuyas + primos generados a partir de la primera
    "semillas_base": [571369, 849571, 355049, 655531, 700103],
    "envios": list(range(12000, 19001, 500)),
    "meseta": [12000, 17000],                 # rango para la ganancia promedio "de meseta"
    "ganancia_acierto": 1_072_500,
    "costo_estimulo": 27_500,
}

# [Anotación · líneas 67–87] Si se pasa un JSON por línea de comandos, sus claves reemplazan las de PARAM.
#   Inicia el experimento y define las columnas que no son variables, los parámetros deterministic y
#   force_row_wise, y los hiperparámetros z601 (num_leaves 16, learning_rate 0,019868, min_data_in_leaf 816,
#   feature_fraction 0,277155, bagging_fraction 0,634130, 250 árboles).
if len(sys.argv) > 1:
    config = Path(sys.argv[1])
    PARAM.update(json.loads(config.read_text(encoding="utf-8")))
    PARAM["_config"] = config.name
    print(f"Configuracion tomada de {config}")

exp = iniciar_experimento(PARAM)
NO_FEATURES = {"numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"}

# parametros que hacen el resultado identico en cualquier maquina
REPRODUCIBLE = {"deterministic": True, "force_row_wise": True, "verbose": -1}

HIPER_Z601 = {
    "params": {
        "objective": "binary", "boosting_type": "gbdt", "max_bin": 31, "num_leaves": 16,
        "learning_rate": 0.019868, "min_data_in_leaf": 816, "feature_fraction": 0.277155,
        "bagging_fraction": 0.634130, "bagging_freq": 1, "feature_pre_filter": False,
    },
    "arboles": 250,
    "fraccion_mes_referencia": 1.0,           # se eligieron entrenando con un mes completo
}

# [Anotación · líneas 89–105] Arma la lista de semillas: parte de semillas_base y agrega números primos entre
#   100003 y 999983 sorteados con un generador de numpy inicializado con la primera semilla base, hasta llegar a
#   n_semillas. Graba la lista en <id>_semillas.csv.
# ---------------------------------------------------------------------------
# Semillas
# ---------------------------------------------------------------------------
def es_primo(n):
    if n < 2 or n % 2 == 0:
        return n == 2
    return all(n % d for d in range(3, int(n ** 0.5) + 1, 2))


semillas = list(PARAM["semillas_base"])
rng = np.random.default_rng(PARAM["semillas_base"][0])
while len(semillas) < PARAM["n_semillas"]:
    candidato = int(rng.integers(100003, 999983))
    if es_primo(candidato) and candidato not in semillas:
        semillas.append(candidato)
semillas = semillas[:PARAM["n_semillas"]]
pd.Series(semillas, name="semilla").to_csv(exp.ruta("semillas"), index=False)

# [Anotación · líneas 107–148] Carga los hiperparámetros según el origen: z601; un archivo de elección
#   (params, cantidad de árboles y fraccion_mes_referencia); o una prueba de una búsqueda, leída de su
#   <id>_pruebas.csv junto con los parámetros fijos de esa búsqueda. Convierte a entero num_leaves,
#   min_data_in_leaf, max_bin y bagging_freq, exige bagging_freq ≥ 1 si bagging_fraction es menor que 1 y agrega
#   los parámetros de reproducibilidad.
# ---------------------------------------------------------------------------
# Hiperparametros
# ---------------------------------------------------------------------------
if PARAM["hiperparametros"] == "z601":
    params = dict(HIPER_Z601["params"])
    arboles = HIPER_Z601["arboles"]
    fraccion_ref = HIPER_Z601["fraccion_mes_referencia"]
    origen = "z601"
elif "eleccion" in PARAM["hiperparametros"]:
    eleccion = json.loads((DIR_EXP / PARAM["hiperparametros"]["eleccion"]).read_text(encoding="utf-8"))
    params = dict(eleccion["params"])
    arboles = int(eleccion["arboles"])
    fraccion_ref = float(eleccion["fraccion_mes_referencia"])
    origen = f"eleccion: {eleccion['origen']}"
    if "escalar_regularizacion" in eleccion:      # la evaluacion decidio si se escala o no (5112)
        PARAM["escalar_min_data_in_leaf"] = bool(eleccion["escalar_regularizacion"])
        print(f"La eleccion indica escalar_regularizacion = {eleccion['escalar_regularizacion']}")
else:
    carpeta_bo = DIR_EXP / PARAM["hiperparametros"]["bo"]
    id_bo = carpeta_bo.name.split("_")[0]
    param_bo = json.loads((carpeta_bo / f"{id_bo}_PARAM.json").read_text(encoding="utf-8"))
    pruebas = pd.read_csv(carpeta_bo / f"{id_bo}_pruebas.csv")
    pruebas = pruebas[pruebas["state"] == "COMPLETE"]
    fila = pruebas[pruebas["number"] == PARAM["hiperparametros"]["prueba"]]
    if fila.empty:
        raise ValueError(f"No existe la prueba {PARAM['hiperparametros']['prueba']} completa en {id_bo}")
    fila = fila.iloc[0]
    buscados = {c.removeprefix("params_"): fila[c] for c in pruebas.columns if c.startswith("params_")}
    # fijos (max_bin, bagging_freq, ...) desde el PARAM de la BO: sin ellos seria otro modelo
    fijos = {k: v for k, v in param_bo["lgbm_fijos"].items()
             if k not in ("metric", "first_metric_only", "verbose")}
    params = {**fijos, **buscados}
    arboles = int(fila["user_attrs_best_iter"])
    # la BO entreno cada fold con (k-1)/k del mes
    fraccion_ref = (param_bo["cv_folds"] - 1) / param_bo["cv_folds"]
    origen = f"{id_bo} prueba {PARAM['hiperparametros']['prueba']}"
for k in ("num_leaves", "min_data_in_leaf", "max_bin", "bagging_freq"):
    if k in params:
        params[k] = int(params[k])
if params.get("bagging_fraction", 1.0) < 1.0:
    assert params.get("bagging_freq", 0) >= 1, "bagging_freq tiene que ser >= 1 o bagging_fraction no actua"
params.update(REPRODUCIBLE)

# [Anotación · líneas 150–170] Define las variables: las de un archivo de lista o, si «variables» es nulo,
#   todas las columnas del Parquet salvo identificador, mes y clases (sin las terminadas en _lag2 y _delta2
#   cuando «usar_lag2» es falso). Si la configuración trae «excluir_prefijos», quita las variables que empiezan
#   con esos prefijos.
# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
t0 = time.time()
archivo = DIR_DATA / PARAM["dataset"]
if PARAM["variables"]:
    features = (DIR_EXP / PARAM["variables"]).read_text(encoding="utf-8").split()
else:
    features = [c for c in pq.ParquetFile(archivo).schema_arrow.names
                if c not in NO_FEATURES
                and (PARAM.get("usar_lag2", False) or not (c.endswith("_lag2") or c.endswith("_delta2")))]
if PARAM.get("excluir_prefijos"):              # variables que se sacan con todos sus lags y deltas
    antes = len(features)
    excluidas = [f for f in features if f.startswith(tuple(PARAM["excluir_prefijos"]))]
    features = [f for f in features if f not in set(excluidas)]
    assert excluidas, f"No se encontro ninguna variable con los prefijos {PARAM['excluir_prefijos']}"
    print(f"Se excluyen {len(excluidas)} variables ({antes} -> {len(features)}): {excluidas}")
if not PARAM.get("usar_lag2", False):
    assert not any(f.endswith(("_lag2", "_delta2")) for f in features), \
        "Hay lag2/delta2 en la lista: poner \"usar_lag2\": true si es intencional"
assert not set(features) & NO_FEATURES, "Hay columnas de id o de clase entre las variables"

# [Anotación · líneas 172–184] Lee del Parquet sólo los meses de entrenamiento y el mes de predicción y los
#   separa. Verifica que estén todos los meses de entrenamiento, que ninguna fila de entrenamiento tenga la
#   clase nula y que el mes de predicción tenga filas.
meses = PARAM["meses_train"] + [PARAM["mes_prediccion"]]
df = pd.read_parquet(archivo, columns=["numero_de_cliente", "foto_mes", "clase_ternaria", PARAM["clase"]] + features,
                     filters=[("foto_mes", "in", meses)])
train = df[df["foto_mes"].isin(PARAM["meses_train"])]
pred = df[df["foto_mes"] == PARAM["mes_prediccion"]].reset_index(drop=True)
del df

assert sorted(train["foto_mes"].unique()) == sorted(PARAM["meses_train"]), "Faltan meses de train"
assert train[PARAM["clase"]].notna().all(), "Hay filas de train sin clase (¿se colo 202107?)"
assert len(pred) > 0, "No hay filas en el mes de prediccion"
print(f"Hiperparametros: {origen} | {arboles} arboles")
print(f"{len(features)} variables | train {len(train):,} filas {PARAM['meses_train']} | "
      f"prediccion {len(pred):,} filas ({PARAM['mes_prediccion']}) ({time.time() - t0:.0f} s)")

# [Anotación · líneas 186–208] Si «escalar_min_data_in_leaf» es verdadero, multiplica min_data_in_leaf (y
#   min_sum_hessian_in_leaf si existe) por la cantidad de meses de entrenamiento dividida por
#   fraccion_mes_referencia; la configuración puede fijar de forma explícita min_data_in_leaf_final y la
#   cantidad de árboles. Graba <id>_params_lightgbm.json y arma el lgb.Dataset con la etiqueta de la clase
#   elegida y la matriz del mes de predicción.
if PARAM["escalar_min_data_in_leaf"]:
    filas_por_mes = len(train) / len(PARAM["meses_train"])
    factor = len(train) / (filas_por_mes * fraccion_ref)
    original = params["min_data_in_leaf"]
    params["min_data_in_leaf"] = int(round(original * factor))
    print(f"min_data_in_leaf: {original} x {factor:.2f} (por filas) = {params['min_data_in_leaf']}")
    if "min_sum_hessian_in_leaf" in params:     # misma logica: la suma de hessianos crece con las filas
        original_h = params["min_sum_hessian_in_leaf"]
        params["min_sum_hessian_in_leaf"] = float(original_h * factor)
        print(f"min_sum_hessian_in_leaf: {original_h:.6g} x {factor:.2f} (por filas) = {params['min_sum_hessian_in_leaf']:.6g}")
if PARAM.get("min_data_in_leaf_final"):        # valor final explicito (pisa el escalado)
    params["min_data_in_leaf"] = int(PARAM["min_data_in_leaf_final"])
    print(f"min_data_in_leaf fijado por config: {params['min_data_in_leaf']}")
if PARAM.get("arboles"):                       # cantidad de arboles validada aparte
    arboles = int(PARAM["arboles"])
    print(f"arboles fijados por config: {arboles}")

with open(exp.ruta("params_lightgbm", ext="json"), "w", encoding="utf-8") as f:
    json.dump({"origen": origen, "arboles": arboles, "params": params}, f, indent=2)

dtrain = lgb.Dataset(train[features], label=train[PARAM["clase"]].astype(int).to_numpy())
X_pred = pred[features]
del train

# [Anotación · líneas 210–222] En modo simulación marca los BAJA+2 del mes de predicción y toma el rango de la
#   meseta. La función curva ordena por probabilidad descendente y devuelve la ganancia acumulada para cada
#   cantidad de envíos.
# ---------------------------------------------------------------------------
# Semillerio
# ---------------------------------------------------------------------------
simulacion = PARAM["modo"] == "simulacion"
if simulacion:
    baja2 = (pred["clase_ternaria"].astype(str) == "BAJA+2").to_numpy()
    lo, hi = PARAM["meseta"]


def curva(prob):
    """Ganancia acumulada para cada cantidad de envios entre 1 y el total."""
    orden = np.argsort(-prob, kind="stable")
    return np.cumsum(np.where(baja2[orden], PARAM["ganancia_acierto"], -PARAM["costo_estimulo"]))


# [Anotación · líneas 225–258] Recorre las semillas: entrena un modelo con la cantidad fija de árboles,
#   predice y suma las probabilidades; si hay «hora_limite» y ya se entrenó el mínimo de semillas, corta el
#   recorrido. En simulación registra, por semilla y para el promedio acumulado, la ganancia en cada cantidad de
#   envíos y la meseta; con la primera semilla graba la importancia (gain) de las variables.
suma = np.zeros(len(pred))
filas = []
por_semilla = {}       # se llena solo si PARAM["guardar_prob_por_semilla"]
LIMITE = datetime.strptime(PARAM["hora_limite"], "%Y-%m-%d %H:%M") if PARAM.get("hora_limite") else None
MIN_SEMILLAS = int(PARAM.get("min_semillas", len(semillas)))
print(f"\n=== Semillerio: {len(semillas)} semillas"
      + (f" (corte a las {PARAM['hora_limite']} con al menos {MIN_SEMILLAS})" if LIMITE else "") + " ===")
for i, semilla in enumerate(semillas, start=1):
    if LIMITE and datetime.now() >= LIMITE and i - 1 >= MIN_SEMILLAS:
        print(f"** Se paso la hora limite ({PARAM['hora_limite']}): el semillerio queda con {i - 1} semillas **", flush=True)
        semillas = semillas[:i - 1]
        pd.Series(semillas, name="semilla").to_csv(exp.ruta("semillas"), index=False)
        break
    t = time.time()
    modelo = lgb.train(dict(params, seed=semilla), dtrain, num_boost_round=arboles)
    prob = modelo.predict(X_pred)
    suma += prob
    if PARAM.get("guardar_prob_por_semilla", False):
        por_semilla[f"s{semilla}"] = prob.astype("float32")
    linea = f"  semilla {i:2d}/{len(semillas)} ({semilla}) {time.time() - t:.0f} s | {datetime.now():%a %H:%M}"
    if simulacion:
        c_ind, c_acu = curva(prob), curva(suma / i)
        for e in PARAM["envios"]:
            filas.append({"semillas_promediadas": i, "semilla": semilla, "envios": e,
                          "ganancia_esta_semilla": c_ind[e - 1], "ganancia_semillerio": c_acu[e - 1]})
        filas.append({"semillas_promediadas": i, "semilla": semilla, "envios": "meseta",
                      "ganancia_esta_semilla": c_ind[lo - 1:hi].mean(),
                      "ganancia_semillerio": c_acu[lo - 1:hi].mean()})
        linea += (f" | semillerio hasta aca: meseta {c_acu[lo - 1:hi].mean() / 1e6:.1f} M, "
                  f"maximo {c_acu[PARAM['envios'][0] - 1:PARAM['envios'][-1]].max() / 1e6:.1f} M")
    print(linea, flush=True)
    if i == 1:
        imp = pd.DataFrame({"variable": features, "gain": modelo.feature_importance("gain")})
        imp.sort_values("gain", ascending=False).to_csv(exp.ruta("importancia"), index=False)

# [Anotación · líneas 260–271] Divide la suma por la cantidad de semillas y graba <id>_probabilidades.csv con
#   numero_de_cliente y prob (más la clase en simulación); si se pidió, graba las probabilidades de cada semilla
#   en Parquet. Arma el diccionario de resultados.
prob_final = suma / len(semillas)
salida_prob = pd.DataFrame({"numero_de_cliente": pred["numero_de_cliente"].astype("int64"), "prob": prob_final})
if simulacion:
    salida_prob["clase_ternaria"] = pred["clase_ternaria"].astype(str).to_numpy()
salida_prob.to_csv(exp.ruta("probabilidades"), index=False)
if por_semilla:
    pd.DataFrame({"numero_de_cliente": pred["numero_de_cliente"].astype("int64"), **por_semilla}) \
        .to_parquet(exp.ruta("prob_por_semilla", ext="parquet"), index=False)
    print(f"Probabilidades de cada semilla grabadas ({len(por_semilla)} columnas)")
resultados = {"hiperparametros": origen, "arboles": arboles,
              "min_data_in_leaf": params["min_data_in_leaf"],
              "min_sum_hessian_in_leaf": params.get("min_sum_hessian_in_leaf"), "n_semillas": len(semillas)}

# [Anotación · líneas 273–314] Salidas de simulación: detalle de ganancia por envíos, resumen del semillerío
#   contra la media y el desvío de una semilla sola, la cantidad de envíos de mayor ganancia y un gráfico HTML
#   de la meseta según semillas promediadas.
# ---------------------------------------------------------------------------
# Salidas
# ---------------------------------------------------------------------------
if simulacion:
    detalle = pd.DataFrame(filas)
    detalle.to_csv(exp.ruta("ganancia_por_envios"), index=False)
    final = detalle[detalle["semillas_promediadas"] == len(semillas)].set_index("envios")
    individual = detalle.groupby("envios")["ganancia_esta_semilla"].agg(["mean", "std"])
    tabla = pd.DataFrame({
        "semillerio_M": final["ganancia_semillerio"] / 1e6,
        "semilla_sola_media_M": individual["mean"] / 1e6,
        "semilla_sola_desvio_M": individual["std"] / 1e6,
    }).astype(float).round(1)
    tabla.index = tabla.index.astype(str)
    tabla.to_csv(exp.ruta("resumen"))
    print(f"\n=== Ganancia en {PARAM['mes_prediccion']} (millones) ===")
    print(tabla.to_string())
    solo_envios = tabla.drop(index="meseta")
    mejor = solo_envios["semillerio_M"].idxmax()
    print(f"\nSemillerio: maximo {solo_envios.loc[mejor, 'semillerio_M']} M en {int(mejor):,} envios "
          f"({int(mejor) / len(pred):.1%} de los clientes); meseta {lo:,}-{hi:,}: "
          f"{tabla.loc['meseta', 'semillerio_M']} M.")
    print(f"Una semilla sola (promedio de {len(semillas)}): meseta {tabla.loc['meseta', 'semilla_sola_media_M']} M "
          f"(desvio {tabla.loc['meseta', 'semilla_sola_desvio_M']} M).")
    resultados.update({
        "mejor_envios": int(mejor), "proporcion_envios": round(int(mejor) / len(pred), 4),
        "maximo_semillerio_M": float(solo_envios.loc[mejor, "semillerio_M"]),
        "meseta_semillerio_M": float(tabla.loc["meseta", "semillerio_M"]),
        "meseta_semilla_sola_M": float(tabla.loc["meseta", "semilla_sola_media_M"]),
    })

    evol = detalle[detalle["envios"] == "meseta"].set_index("semillas_promediadas")["ganancia_semillerio"] / 1e6
    fig = go.Figure(go.Scatter(x=evol.index, y=evol.values, mode="lines+markers",
                               line=dict(color="#6C5CE7", width=4, shape="spline"), marker=dict(size=9)))
    fig.update_layout(
        title=dict(text=f"<b>Ganancia de meseta ({lo:,}-{hi:,} envios) segun semillas promediadas</b>", x=0.02),
        font=dict(family="Inter, Segoe UI, Helvetica, sans-serif", size=14, color="#2d3436"),
        plot_bgcolor="white", paper_bgcolor="white", height=460,
        xaxis=dict(title="Semillas promediadas", gridcolor="#f1f2f6"),
        yaxis=dict(title="Ganancia (millones)", gridcolor="#f1f2f6"),
    )
    fig.write_html(exp.ruta("semillerio", ext="html"), include_plotlyjs="cdn")
# [Anotación · líneas 315–335] Salidas de producción: crea la carpeta kaggle/ y, para cada cantidad de envíos,
#   graba KA<id>_e<N>.csv con numero_de_cliente y Predicted (1 para los N de mayor probabilidad). Imprime los
#   percentiles 50, 90 y 99 de la probabilidad y cierra el experimento.
else:
    carpeta_ka = exp.carpeta / "kaggle"
    carpeta_ka.mkdir(exist_ok=True)
    orden = np.argsort(-prob_final, kind="stable")
    ids = pred["numero_de_cliente"].astype("int64")
    assert ids.is_unique, "Hay clientes repetidos en el mes de prediccion"
    for e in PARAM["envios"]:
        predicted = np.zeros(len(pred), dtype=int)
        predicted[orden[:e]] = 1
        ka = pd.DataFrame({"numero_de_cliente": ids, "Predicted": predicted})
        assert list(ka.columns) == ["numero_de_cliente", "Predicted"]
        assert ka["Predicted"].sum() == e and set(ka["Predicted"].unique()) <= {0, 1}
        ka.to_csv(carpeta_ka / f"KA{exp.id}_e{e}.csv", index=False)
    print(f"\nArchivos para Kaggle en {carpeta_ka}: {len(PARAM['envios'])} archivos de "
          f"{len(pred):,} filas (de {min(PARAM['envios']):,} a {max(PARAM['envios']):,} envios)")
    pct = np.percentile(prob_final, [50, 90, 99]).round(4)
    print(f"Probabilidades en {PARAM['mes_prediccion']}: mediana {pct[0]}, p90 {pct[1]}, p99 {pct[2]}")
    resultados.update({"archivos_kaggle": len(PARAM["envios"]), "filas": len(pred),
                       "prob_p50_p90_p99": pct.tolist()})

cerrar_experimento(exp, resultados)
```

### exp_utils.py

Módulo común que importan todos los scripts: define las rutas del proyecto y las funciones iniciar_experimento y cerrar_experimento, que crean la carpeta de cada experimento, guardan parámetros, copia del script y resultados, y mantienen exp/registro_experimentos.csv.

```python
# Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada
# anotación son los del archivo original, sin estas líneas agregadas.

# [Anotación · líneas 1–20] Docstring del módulo: cada script define un diccionario PARAM, llama a
#   iniciar_experimento al comienzo y a cerrar_experimento al final. Fija la numeración de los identificadores
#   de 4 dígitos por familia: 1xxx datasets, 2xxx diagnósticos, 3xxx ingeniería de variables, 4xxx
#   hiperparámetros, 5xxx modelo final y semillerío, 6xxx entregas.
"""
exp_utils.py
DMEyF 2026 - utilidades comunes para que cada experimento quede trazable.

Cada script define un diccionario PARAM y hace:

    exp = iniciar_experimento(PARAM)          # crea exp/<id>_<nombre>/, guarda PARAM y copia el script
    ...
    tabla.to_csv(exp.ruta("ganancia_cortes", semilla=571369))   # -> 4101_ganancia_cortes_s571369.csv
    ...
    cerrar_experimento(exp, {"ganancia_max": 123, "envios_opt": 11000})

Al cerrar se agrega una fila a exp/registro_experimentos.csv con PARAM + resultados,
para poder comparar todos los experimentos en una sola tabla.

Numeracion sugerida del id (4 digitos, el primero indica la familia):
    1xxx preparacion de datasets      2xxx diagnosticos / drift
    3xxx feature engineering          4xxx optimizacion de hiperparametros
    5xxx modelo final / semillerio    6xxx entregas a Kaggle
"""

# [Anotación · líneas 22–36] Importa las librerías y define las rutas. ROOT sale de la variable de entorno
#   DMEYF_ROOT y, si no está definida, de una ruta de Windows escrita en el código
#   (C:\Users\rpalpa\Documents\Maestria\DMEyF\Primera_competencia); de ROOT cuelgan data/, exp/ y
#   exp/registro_experimentos.csv.
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(os.environ.get("DMEYF_ROOT", r"C:\Users\rpalpa\Documents\Maestria\DMEyF\Primera_competencia"))
DIR_DATA = ROOT / "data"
DIR_EXP = ROOT / "exp"
ARCH_REGISTRO = DIR_EXP / "registro_experimentos.csv"


# [Anotación · líneas 39–49] Clase Experimento: guarda el PARAM, el id, la carpeta y la hora de inicio. Su
#   método ruta() arma nombres de archivo con el id adelante y, si se pasa, la semilla (por ejemplo
#   4101_ganancia_cortes_s571369.csv).
class Experimento:
    def __init__(self, param, carpeta):
        self.param = param
        self.id = str(param["experimento"])
        self.carpeta = carpeta
        self.inicio = time.time()

    def ruta(self, nombre, semilla=None, ext="csv"):
        """Nombre de archivo con el id (y la semilla si corresponde) adelante."""
        s = f"_s{semilla}" if semilla is not None else ""
        return self.carpeta / f"{self.id}_{nombre}{s}.{ext}"


# [Anotación · líneas 52–58] _git_commit devuelve el hash corto del commit actual del repositorio, o el texto
#   «sin_git» si el comando git no se puede ejecutar.
def _git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=Path(sys.argv[0]).resolve().parent,
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return "sin_git"


# [Anotación · líneas 61–92] iniciar_experimento exige las claves experimento, nombre y descripcion; crea
#   exp/<id>_<nombre>/ y se detiene si la carpeta ya tiene archivos, salvo que PARAM traiga «sobrescribir» o
#   «reanudar». Copia el script en ejecución como <id>_script.py, agrega a PARAM la fecha de inicio, el nombre
#   del script y el commit, y lo graba en <id>_PARAM.json.
def iniciar_experimento(param):
    for clave in ("experimento", "nombre", "descripcion"):
        if clave not in param:
            raise ValueError(f"PARAM tiene que tener '{clave}'")

    carpeta = DIR_EXP / f"{param['experimento']}_{param['nombre']}"
    existe = carpeta.exists() and any(carpeta.iterdir())
    if existe and not (param.get("sobrescribir", False) or param.get("reanudar", False)):
        raise FileExistsError(
            f"Ya existe {carpeta}.\nUsa otro numero de experimento, PARAM['reanudar'] = True para "
            f"continuar uno interrumpido, o PARAM['sobrescribir'] = True si de verdad queres pisarlo.")
    if existe and param.get("reanudar", False):
        print(f"Reanudando experimento existente en {carpeta}")
    carpeta.mkdir(parents=True, exist_ok=True)

    exp = Experimento(param, carpeta)

    # copia del script tal cual se corrio (reproducibilidad aunque despues lo edites)
    script = Path(sys.argv[0]).resolve()
    if script.suffix == ".py" and script.exists():
        shutil.copy2(script, exp.ruta("script", ext="py"))

    param["_fecha_inicio"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    param["_script"] = script.name
    param["_git_commit"] = _git_commit()
    with open(exp.ruta("PARAM", ext="json"), "w", encoding="utf-8") as f:
        json.dump(param, f, indent=2, ensure_ascii=False, default=str)

    print(f"=== Experimento {exp.id} - {param['nombre']} ===")
    print(f"{param['descripcion']}")
    print(f"Carpeta: {carpeta}\n")
    return exp


# [Anotación · líneas 95–106] _aplanar convierte un diccionario anidado en uno de un solo nivel con claves
#   unidas por punto (lgbm.num_leaves) y pasa las listas a texto separado por espacios, para que entren en una
#   fila del registro.
def _aplanar(d, prefijo=""):
    """{'lgbm': {'num_leaves': 31}} -> {'lgbm.num_leaves': 31}  (para el registro en una fila)."""
    plano = {}
    for k, v in d.items():
        clave = f"{prefijo}{k}"
        if isinstance(v, dict):
            plano.update(_aplanar(v, clave + "."))
        elif isinstance(v, (list, tuple)):
            plano[clave] = " ".join(str(x) for x in v)
        else:
            plano[clave] = v
    return plano


# [Anotación · líneas 109–126] cerrar_experimento calcula los minutos transcurridos, graba
#   <id>_resultados.json y agrega a exp/registro_experimentos.csv una fila con el PARAM aplanado y los
#   resultados con prefijo «res.»; si el experimento ya estaba en el registro, reemplaza su fila.
def cerrar_experimento(exp, resultados=None):
    resultados = resultados or {}
    minutos = round((time.time() - exp.inicio) / 60, 2)
    resultados["_minutos"] = minutos

    with open(exp.ruta("resultados", ext="json"), "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False, default=str)

    fila = _aplanar(exp.param)
    fila.update({f"res.{k}": v for k, v in resultados.items()})
    nueva = pd.DataFrame([fila])
    if ARCH_REGISTRO.exists():
        registro = pd.read_csv(ARCH_REGISTRO, dtype=str)
        registro = registro[registro["experimento"] != exp.id]       # si se re-corrio, queda la ultima
        nueva = pd.concat([registro, nueva.astype(str)], ignore_index=True)
    nueva.to_csv(ARCH_REGISTRO, index=False)

    print(f"\n=== Fin experimento {exp.id} ({minutos} min). Registrado en {ARCH_REGISTRO.name} ===")
```


## Explicaciones del alumno (texto original)

### informe_tecnico.md

> # Informe técnico — Primera Competencia DMEyF 2026
>
> **Autor:** Rodrigo Palpa (desarrollado con asistencia de IA: Claude).
> **Fecha:** 11/10/2026.
> **Propósito:** documentar el proceso, las decisiones y los resultados de la entrega final (modelo 5015), cómo se
> evaluaron las recomendaciones del profesor y qué supuestos y desvíos quedan declarados.
>
> ---
>
> ## 0. Resumen
>
> | Ítem | Valor |
> |---|---|
> | Submit final | `submit 5015e12500final2`, ID `1626-1791760490758459`, 11/10/2026 20:14 |
> | Archivo | `entrega_final/Z6011_5015_e12500_final.csv` (12.500 `numero_de_cliente`, sin encabezado) |
> | Ganancia pública | **95,59** (el público es ≈25% de los clientes de agosto) |
> | Modelo | LightGBM binario, semillerío de 50 semillas |
> | Clase de entrenamiento | `clase_binaria2`: BAJA+1 y BAJA+2 positivos. La ganancia se mide siempre sobre BAJA+2 |
> | Dataset | `ds3003_rank_extra.parquet`: lags y deltas de orden 1 y 2 sobre valores crudos, después ranking por mes con cero fijo (NA se mantiene), más 6 variables del "proceso de muerte". **766 variables** |
> | Meses de entrenamiento | 202103 a 202106. Se predice 202108 |
> | Hiperparámetros | "Prueba 23" (encontrada en la Bayesiana 4104 y mantenida por las Bayesianas 4105, 4106 y 4107) |
> | Corte | 12.500 envíos |
> | Validación interna | Junio completo, prueba 23 entrenada con marzo + abril: 441,4 M de meseta (semillerío de 20, exp 5114) |
>
> ---
>
> ## 1. Problema y datos
>
> - **Dataset:** `competencia_01`, de 202103 a 202108: 983.061 filas y 152 variables originales, más el id y el mes.
> - **Clase ternaria** con la lógica de la cátedra (CONTINUA, BAJA+1, BAJA+2), en `01_preparar_dataset.py` (exp 1001).
> - **Meses con clase completa:** 202103 a 202106. 202107 tiene la clase incompleta y no se usa para entrenar.
>   202108 es el mes a predecir.
> - **Ganancia:** +1.072.500 por cada BAJA+2 contactado y −27.500 por cada otro contacto.
> - **Entrega:** bot de Zulip `@competencia-uno`, entre 8.000 y 15.000 ids. Vale el último submit antes del cierre
>   (11/10/2026 23:59).
>
> ---
>
> ## 2. Recomendaciones del profesor y cómo se evaluaron
>
> Cada recomendación se evaluó con el mismo protocolo (sección 4) contra el modelo vigente, con una regla fijada
> antes de ver el resultado. Se adoptaron las que mejoraron o empataron.
>
> | Recomendación | Evaluación | Resultado | Decisión |
> |---|---|---|---|
> | Lags y deltas de orden 1 y 2, aunque las columnas tengan muchos NA | 5105 (receta contra dataset anterior), 5106 (con y sin lag2) | Mejora; lag2 empata (−1,5 M, IC90 −13 a +11) | **Adoptada** |
> | Ranking de todas las variables dentro de cada mes, con cero fijo y NA conservado (después de los lags) | 5105 (ds3002 y ds3003 contra variantes) | Mejor que rankear antes de los lags (3005) y que indicadores sin rankear (3004) | **Adoptada** |
> | Sin canaritos, sin undersampling | — | — | **Adoptada** |
> | Usar toda la información disponible para la búsqueda de hiperparámetros, aunque haya NA | 5107: marzo + abril contra solo abril | +4,8 M (IC90 −7,1 a +16,4; 75% de los remuestreos) | **Adoptada** |
> | Entrenamiento final con todos los meses con clase (marzo a junio) | — | — | **Adoptada** |
> | Rangos de búsqueda: `num_leaves` 8–2000, `min_data_in_leaf` 0–20.000, `feature_fraction` 0,05–0,9, `bagging_fraction` 0,05–1, `learning_rate` 0,01–0,2; `max_bin` 31 | Bayesiana 4107 (50 pruebas) | Ninguna prueba nueva superó a la prueba 23 en la mitad B (sección 3.3) | **Adoptada**; se mantuvo la prueba 23 |
> | ≥20 semillas en el modelo final | — | 50 semillas | **Adoptada** |
> | Estrategia de entrenamiento 1.7: métrica AUC; fijos `max_bin` 31, `min_data_in_leaf` 0, `feature_fraction` 0,5, `feature_fraction_bynode` 0,2, `learning_rate` 0,005; Bayesiana sobre `num_iterations`, `num_leaves` y `min_sum_hessian_in_leaf`; final como ensamble de 10+ modelos con hiperparámetros distintos (2.1 y 2.2) | 4112 + 5113 (sección 6.1) | **−52 M** en junio contra la prueba 23 | No adoptada (R7) |
> | Feature engineering 1.1–1.4: `ccajas_depositos` NA en 202105, flags `_zero`, tendencia y promedio de 3 meses | 5114 (sección 6.2) | **−3,7 M** en junio, mejor en 4/20 semillas | No adoptada (R8) |
> | Probar distintos cortes contra el público (2.3) | Sección 5.2 | 12.000 → 96,11; 12.500 → 95,59 | Se combinó con la evidencia de junio |
>
> ---
>
> ## 3. Pipeline de 5015, paso a paso
>
> ### 3.1 Preparación (exp 1001)
> `competencia_01_crudo.csv` → `ds1001_base.parquet` con `clase_ternaria`, `clase_binaria1` y `clase_binaria2`.
> El script verifica que el archivo grabado sea idéntico al de memoria.
>
> ### 3.2 Ingeniería de variables (exp 3003, `03c_fe_extra.py`)
> 1. Datos ordenados por cliente y mes.
> 2. Para cada una de las 152 variables: `x_lag1`, `x_lag2` (valor 1 y 2 meses antes; NA si el cliente no estaba
>    exactamente k meses antes) y `x_delta1`, `x_delta2` (diferencia contra esos valores), sobre valores crudos.
> 3. Seis variables del "proceso de muerte", sobre valores crudos:
>
>    | Variable | Qué mide |
>    |---|---|
>    | `n_apagados` | Cuántas de 16 variables clave (tarjetas, préstamos, sueldo, saldos, transacciones) están en 0 o NA |
>    | `n_apagados_delta1` / `n_apagados_delta2` | Diferencia de `n_apagados` contra 1 y 2 meses antes |
>    | `n_dejo_de_usar` | Productos activos hace 1 o 2 meses que hoy están en 0 o NA |
>    | `ctrx_quarter_rel_max3` / `mcaja_ahorro_rel_max3` | Valor de hoy dividido por el máximo de los últimos 3 meses |
>
> 4. **Todas** las columnas (originales, lags, deltas y nuevas) se reemplazan por su ranking dentro del mes:
>    positivos en (0,1], negativos en [−1,0), cero = 0, NA = NA, empates por promedio. Corrige la inflación y el
>    aguinaldo: la mediana cruda de `mpayroll` entre los positivos sube de ~105 mil (mayo) a ~157 mil (junio);
>    rankeada queda en 0,500 todos los meses.
> 5. Resultado: 983.061 × 771 columnas (5 de id y clase + 152 × 5 + 6).
>
> ### 3.3 Selección de hiperparámetros (`08_bo_fuera_de_tiempo.py`)
>
> - Se entrena con meses anteriores y se mide en **junio (202106)**, a la misma distancia de 2 meses que hay entre
>   junio y agosto.
> - Los clientes de junio se dividen en **dos mitades fijas**, estratificadas por clase ternaria (549 BAJA+2 en cada
>   una; `exp/4102_bo_fuera_de_tiempo/4102_mitades_junio.csv`).
> - **Etapa 1:** Optuna TPE sobre la **mitad A**, 1 semilla por prueba, corte temprano (hasta 3.000 árboles).
> - **Etapa 2:** las 5 mejores de la etapa 1 y las referencias se entrenan con 20 semillas y se miden en la
>   **mitad B**. El mejor retador reemplaza a la mejor referencia solo si gana en promedio **y** en ≥14 de 20 semillas.
> - **Métrica "meseta":** ganancia promedio entre 12.000 y 17.000 envíos equivalentes al mes completo.
>
> **Bayesiana 4107** (recomendaciones del profesor): ds3003 con lag2; entrenamiento 202103 + 202104; rangos de la
> sección 2; `max_bin` 31 y `bagging_freq` 1 fijos; 50 pruebas (15 al azar).
>
> | Candidato | Mitad A | Mitad B | Desvío | Le gana a la p23 en | Árboles | lr | Hojas | min_data | ff | bf |
> |---|---|---|---|---|---|---|---|---|---|---|
> | **p23 (referencia)** | – | **435,8** | 6,4 | – | 580 | 0,0678 | 41 | 20.248 | 0,180 | 0,312 |
> | prueba 48 | 450,5 | 432,1 | 5,7 | 7/20 | 270 | 0,0116 | 754 | 254 | 0,086 | 0,894 |
> | prueba 40 | 447,5 | 429,9 | 6,8 | 6/20 | 283 | 0,0169 | 634 | 196 | 0,072 | 0,854 |
> | prueba 41 | 447,1 | 425,5 | 6,5 | 2/20 | 607 | 0,0120 | 1555 | 118 | 0,079 | 0,826 |
> | prueba 42 (mejor según A) | 453,2 | 418,2 | 12,7 | 3/20 | 428 | 0,0111 | 1621 | 852 | 0,110 | 0,828 |
> | prueba 47 | 453,2 | 410,2 | 12,5 | 0/20 | 334 | 0,0104 | 1703 | 1244 | 0,136 | 0,870 |
> | z601 (referencia de clase) | – | 357,0 | 8,1 | 0/20 | 250 | 0,0199 | 16 | 1.632 | 0,277 | 0,634 |
>
> Las pruebas con muchas hojas y `min_data_in_leaf` chico ganan en la mitad A y caen en la mitad B. Se mantuvo la prueba 23.
>
> **Historia de la prueba 23:**
>
> | Búsqueda | Entrenamiento | Dataset | Resultado |
> |---|---|---|---|
> | 4104 | Solo abril | ds3002 con lag2 | Aparece la prueba 23 (3.ª en la mitad A, 1.ª en la B) |
> | 4105 | Solo abril | ds3002 sin lag2 | Se mantiene (427,2 M en B) |
> | 4106 | Solo abril | ds3003 con lag2 | Se mantiene (432,5 M en B) |
> | 4107 | Marzo + abril | ds3003 con lag2 | Se mantiene (435,8 M en B) |
>
> ### 3.4 Modelo final 5015 (`07_modelo_final.py`, `configs/5015_prod_profesor_mar_jun.json`)
>
> | Parámetro | Valor |
> |---|---|
> | Entrenamiento | 202103 a 202106 (654.066 filas, sin undersampling) |
> | Predicción | 202108 (164.647 clientes) |
> | `learning_rate` / `num_leaves` | 0,0678 / 41 |
> | `min_data_in_leaf` | **40.496** (10.124 por mes × 4; supuesto S1) |
> | `feature_fraction` / `bagging_fraction` / `bagging_freq` | 0,1798 / 0,3124 / 1 |
> | `lambda_l1` / `lambda_l2` / `max_bin` | 0,001 / 0,001 / 31 |
> | Árboles | 580, fijos (supuesto S2) |
> | Reproducibilidad | `deterministic=True`, `force_row_wise=True` |
> | Semillas | 50: 571369, 849571, 355049, 655531, 700103 y 45 primos generados de forma determinística |
> | Ensamble | Promedio de las probabilidades de las 50 semillas |
>
> ### 3.5 Entrega (exp 6011, `10_entrega_zulip.py`)
> Archivos de 11.000 a 13.500 envíos, con controles: sin encabezado, ids enteros, sin repetidos, cantidad exacta.
> Se entregó el de 12.500.
>
> ---
>
> ## 4. Protocolo de validación y reglas de decisión
>
> - Entrenar con 202103 + 202104 y medir en 202106 (mitad B o junio completo), con semillas pareadas.
> - Comparaciones con bootstrap pareado (IC90 y % de remuestreos a favor) o Wilcoxon.
> - **Reglas fijadas antes de ver cada resultado:**
>
> | Regla | Decisión | Criterio |
> |---|---|---|
> | R1 | Variables de muerte ampliadas (5108) | Adoptar solo si mejora; dio −7,8 M → no |
> | R3 | `min_data_in_leaf` y árboles de la prueba 23 (5109) | Mitad de `min_data_in_leaf` solo si no pierde >3 M; otra cantidad de árboles solo si gana ≥5 M en ≥85% → se mantuvieron 20.248 (2 meses) y 580 |
> | R4 | Bayesiana "limpia" 4109 contra la prueba 23 (5110) | Usar 4109 salvo que pierda >3 M; perdió (432,5 vs 443,1) → prueba 23 |
> | R6 | Escalar o no `min_sum_hessian_in_leaf` en el ensamble 1.7 | La versión con mayor meseta en junio |
> | R7 | Ensamble de la estrategia 1.7 contra la prueba 23 (5113) | Adoptar si no pierde >3 M; perdió 52 M → no |
> | R8 | Dataset con el FE 1.1–1.4 (5114) | Adoptar si no pierde >3 M; perdió 3,7 M → no |
> | R9 | 5015 sin columnas anómalas (5023) | Cambiar la entrega solo si el público ≥ 100,6; dio 94,35 → no |
>
> ---
>
> ## 5. Resultados
>
> ### 5.1 Historial de submits (público)
>
> | # | Modelo | Envíos | Público |
> |---|---|---|---|
> | 1 | 5005 (crudo, 123 variables por canaritos, hiperparámetros de 4102) | 13.000 | 92,73 |
> | 2–5 | 5005 | 10.000 / 11.000 / 12.000 / 14.000 | 89,38 / 92,57 / 96,58 / 90,26 |
> | 6 | Combinación 5005 + 5011 (receta sin lag2) | 12.000 | 94,44 |
> | 7 | 5013: ds3003 con lag2, prueba 23, entrenada con abril a junio | 12.000 | 97,08 |
> | 8 | 5015: ídem, entrenada con marzo a junio | 12.000 | 96,11 |
> | 9 | 5015 | 12.500 | 95,59 |
> | 10 | 5023: 5015 sin columnas anómalas | 12.500 | 94,35 |
> | 11 | **5015 (reenvío como submit final)** | **12.500** | **95,59** |
>
> Ruido estimado de la diferencia de público entre dos listas con ~95% de coincidencia: ±3 M. Las diferencias
> entre los submits 5 a 11 están dentro del ruido.
>
> ### 5.2 El corte
>
> | Evidencia | 12.000 | 12.500 | 13.500 | 14.000 |
> |---|---|---|---|---|
> | Público 5015 | **96,11** | 95,59 | – | – |
> | Junio completo, prueba 23, semillerío de 12 (5113) | 443,3 | **449,4** | 449,4 | 446,6 |
> | Junio completo, prueba 23, semillerío de 20 (5114) | 442,2 | 443,8 | 442,8 | **452,1** |
> | Mitad B de junio (bootstrap, 5109) | | | óptimo 13.500–14.000 | |
>
> El público favorece 12.000 y junio favorece 12.500 o más. Se eligió **12.500**, el punto medio entre las dos
> fuentes (~12.750) redondeado hacia la única medición sobre agosto.
>
> ---
>
> ## 6. Experimentos con las recomendaciones de la última semana (10 y 11/10)
>
> ### 6.1 Estrategia de entrenamiento 1.7 (4112 + 5113)
>
> - **Dataset ds3007** (exp 3007, `03f_fe_profesor.py`): ds3003 + recomendaciones 1.1–1.4 (1.210 variables).
> - **Bayesiana 4112** (`16_bo_profesor_v2.py`): AUC promedio de 5 particiones 70/30 estratificadas dentro de
>   202103 + 202104; fijos de la estrategia 1.7; `num_iterations` 250–4000, `num_leaves` 8–2000,
>   `min_sum_hessian_in_leaf` 0,001–100 (rangos propios: la recomendación no los fija). 16 pruebas en 15 h.
> - Eligió árboles grandes: las mejores pruebas tienen ~1.000–1.800 hojas, 2.000–3.900 árboles y
>   `min_sum_hessian_in_leaf` entre 0,002 y 0,1.
> - **Evaluación 5113** (`18_ensamble_profesor.py`): ensamble de las 12 mejores, entrenado con 202103 + 202104 y
>   medido en junio completo, contra la prueba 23 con 12 semillas sobre ds3003:
>
> | Modelo | Meseta junio | Público 30% (12.000) | Privado 70% (12.000) |
> |---|---|---|---|
> | Ensamble escalado | 388,6 | 373,7 | 386,7 |
> | Ensamble sin escalar | 389,7 | 377,8 | 389,7 |
> | **Prueba 23 (semillerío de 12)** | **441,3** | **452,7** | **439,3** |
>
>   El ensamble pierde en todos los cortes de 9.000 a 15.000. Los modelos individuales del ensamble promedian 389 M
>   (desvío 11) y la prueba 23, 436 M (desvío 3,5): el mejor modelo del ensamble (406,8) no alcanza a la peor
>   semilla de la prueba 23 (429,9). **R7 → no se adopta;** el final 5021 no se entrenó.
> - Lectura: optimizar AUC llevó a `min_sum_hessian_in_leaf` muy bajos y árboles enormes, que en junio sobreajustan.
>
> ### 6.2 Feature engineering 1.1–1.4 con la prueba 23 (5114, `19_eval_dataset.py`)
>
> Mismos hiperparámetros, mismas 20 semillas, entrenamiento 202103 + 202104, junio completo:
>
> | Dataset | Meseta media | Desvío | Semillerío |
> |---|---|---|---|
> | ds3003 (vigente) | 436,5 | 3,7 | 441,4 |
> | ds3007 (con FE 1.1–1.4) | 432,7 | 4,3 | 437,6 |
>
> Diferencia −3,7 M, mejor en 4/20 semillas. **R8 → no se adopta.**
>
> ### 6.3 Columnas con valores anómalos (5023)
>
> 5015 sin `Master/Visa_Finiciomora` ni `Master/Visa_fultimo_cierre` (y sus lags y deltas; 20 columnas), que
> presentan ceros inyectados en 202105, 202106 y 202108. Como la anomalía afecta a agosto, la validación en junio no
> la puede medir y se usó el público con una regla exigente (≥ 100,6). Dio **94,35** contra 95,59 → no se adopta.
>
> ---
>
> ## 7. Supuestos y desvíos declarados
>
> | # | Qué | Detalle |
> |---|---|---|
> | S1 | `min_data_in_leaf` **escalado por cantidad de filas** (×2 con 2 meses, ×4 en el final) | Decisión propia para que cada hoja represente la misma proporción de clientes. El valor final (40.496) queda fuera del rango de búsqueda recomendado (0–20.000). Apoyo: con la mitad del valor, 5109 dio −21 M |
> | S2 | **580 árboles fijos** en el final | Salen del corte temprano de 4104 (solo abril); no se reajustaron para 4 meses. En 5109, 750 y 900 árboles no superaron la regla R3 |
> | S3 | **`num_leaves` = 41 no actúa** | Con `bagging_fraction` 0,31 y `min_data_in_leaf` 40.496, cada árbol tiene como máximo ~5 hojas (654.066 × 0,3124 / 40.496) |
> | S4 | **La prueba 23 llegó como referencia elegida por la mitad B** | En 4104 la regla eligió la prueba 35; la 23 (3.ª en A, 1.ª en B) se agregó como referencia en 4105 y desde entonces las búsquedas eligen entre referencias por B. Las cifras de la mitad B (435,8; 443,1) son algo optimistas. Las comparaciones en **junio completo** de 5113 y 5114 la confirman |
> | S5 | **Búsqueda con marzo + abril, sin mayo** | Para mantener la distancia de 2 meses con junio. Con mayo, la medición sería a 1 mes y más optimista |
> | S6 | **Métrica "meseta"** (12.000–17.000 envíos) en lugar del máximo | Reduce la sensibilidad al corte |
> | S7 | `min_data_in_leaf` busca desde 1 | La escala logarítmica no admite 0; en la práctica son equivalentes |
> | S8 | `max_bin` fijo en 31 | "Hasta 31" y "= 31" coinciden; buscarlo exige rearmar el dataset en cada prueba |
> | S9 | `lambda_l1` = `lambda_l2` = 0,001 | Vienen de la prueba 23; efecto casi nulo (el default es 0) |
> | S10 | Las 16 variables clave del proceso de muerte se eligieron con un diagnóstico que incluía junio | Verificado: sin junio, las 16 ocupan los mismos puestos (Spearman 0,999) |
> | S11 | Lag2 se omitió durante un tramo (4105, 5103, 5011, 5104) | Corregido desde 5105; 5015 lo incluye. El submit 6 no tenía lag2 |
> | S12 | `clase_binaria2` en lugar de `clase_binaria1` | Exp 4002: +11 a +18 M |
>
> ---
>
> ## 8. Lo que queda para la segunda competencia
>
> 1. **Validación y regularización.** La validación con 2 meses de entrenamiento eligió siempre el modelo más
>    rígido, y ese valor se escaló ×4 para el final. Probar validar con 202103–202105 → 202106 antes de fijar la
>    regularización, y medir el efecto de escalar en vez de suponerlo.
> 2. **Estrategia 1.7.** Buscar con la ganancia (no con AUC) o acotar `min_sum_hessian_in_leaf` a valores más altos.
> 3. **Aguinaldo.** Los deltas de orden 2 de agosto comparan contra junio; el ranking corrige niveles, no saltos.
> 4. **Calidad de datos en el mes a predecir.** Revisar 202108 antes de entrenar: la validación en junio no detecta
>    anomalías que aparecen solo en agosto.
>
> ---
>
> ## 9. Reproducción
>
> Ver `README.md`, sección 3. Cada experimento guarda en `exp/<id>_<nombre>/` su `PARAM.json`, una copia del script y
> sus resultados, y agrega una fila a `exp/registro_experimentos.csv`.

### README.md

> # DMEyF 2026 · Primera Competencia — Rodrigo Palpa
>
> Maestría en Minería de Datos (UBA) · Data Mining en Economía y Finanzas.
>
> Objetivo: elegir a qué clientes de la foto `202108` enviarles el estímulo de retención, maximizando
> `+1.072.500` por cada `BAJA+2` acertado y `−27.500` por cada estimulado que no lo es.
>
> ## 1. La entrega final
>
> | | |
> |---|---|
> | Archivo | `entrega_final/Z6011_5015_e12500_final2.csv` |
> | Contenido | 12.500 `numero_de_cliente` de 202108, una columna, sin encabezado |
> | Modelo | experimento **5015** (semillerío de 50 LightGBM) |
> | Submit final | `submit 5015e12500final2` · ID `1626-1791760490758459` · 11/10/2026 20:14 |
> | Ganancia pública | **95,59** (el mismo modelo con 12.000 envíos dio 96,11) |
>
> ## 2. El modelo, en una tabla
>
> | Pieza | Elección | Script / config |
> |---|---|---|
> | Datos | `competencia_01_crudo.csv` → `clase_ternaria` con la lógica de la cátedra, más `clase_binaria1` (BAJA+2) y `clase_binaria2` (BAJA+1 y BAJA+2) | `01_preparar_dataset.py` |
> | Clase de entrenamiento | `clase_binaria2` (BAJA+1 + BAJA+2 positivos). La ganancia se mide siempre con BAJA+2 | — |
> | Variables (dataset **ds3003**, 766) | Lags y deltas de orden 1 y 2 de las 152 variables, calculados sobre los valores crudos (NA si el cliente no estaba exactamente k meses antes). Después, **todas** las columnas se reemplazan por su ranking dentro del mes con el cero fijo: positivos en (0,1], negativos en [−1,0), cero = 0, NA = NA; esto corrige la inflación y el aguinaldo. Más 6 variables propias del "proceso de muerte": `n_apagados` (cuántos de 16 productos clave están en 0 o NA), sus deltas 1 y 2, `n_dejo_de_usar`, `ctrx_quarter_rel_max3` y `mcaja_ahorro_rel_max3` | `03c_fe_extra.py` |
> | Hiperparámetros | **Prueba 23**: `learning_rate` 0,0678 · `num_leaves` 41 · `min_data_in_leaf` 10.124 por mes de entrenamiento · `feature_fraction` 0,1798 · `bagging_fraction` 0,3124 (`bagging_freq` 1) · `lambda_l1` = `lambda_l2` = 0,001 · `max_bin` 31 · 580 árboles | `08_bo_fuera_de_tiempo.py` (4104 → 4107) |
> | `min_data_in_leaf` final | Escalado por cantidad de filas: 10.124 × 4 meses = **40.496** | `07_modelo_final.py` |
> | Entrenamiento final | 202103–202106 (654.066 filas), **sin undersampling** | `configs/5015_prod_profesor_mar_jun.json` |
> | Semillerío | 50 semillas: 571369, 849571, 355049, 655531, 700103 y 45 primos generados a partir de la primera; se promedian las probabilidades | `07_modelo_final.py` |
> | Corte | Los **12.500** clientes de mayor probabilidad (sección 5) | `10_entrega_zulip.py`, `configs/6011_zulip_final_5015.json` |
>
> ## 3. Cómo reproducir la entrega
>
> ### Requisitos
>
> - Windows o Linux con **Python 3.12** y `pip install -r requirements.txt`.
> - ~16 GB de RAM (el entrenamiento final usa 4 meses × 766 variables).
> - El dataset de la cátedra `competencia_01_crudo.csv` en `data/` (no se incluye en el repo).
> - La carpeta del proyecto: `exp_utils.py` toma la raíz de la variable de entorno `DMEYF_ROOT`;
>   si no existe, usa la ruta de la máquina original. Antes de correr:
>   - Windows: `set DMEYF_ROOT=%CD%` (desde la carpeta del repo)
>   - Linux: `export DMEYF_ROOT=$(pwd)`
>
> ### Camino corto (~1 a 2 h): usa los hiperparámetros ya elegidos
>
> Los hiperparámetros salen de `exp/4107_bo_profesor_mar_abr/4107_eleccion.json`, que está en el repo.
>
> ```bash
> py -3.12 01_preparar_dataset.py                                       # data/ds1001_base.parquet
> py -3.12 03c_fe_extra.py                                              # data/ds3003_rank_extra.parquet
> py -3.12 07_modelo_final.py configs/5015_prod_profesor_mar_jun.json   # exp/5015_.../5015_probabilidades.csv
> py -3.12 10_entrega_zulip.py configs/6011_zulip_final_5015.json       # exp/6011_.../zulip/*.csv
> ```
>
> El archivo entregado es `exp/6011_zulip_final_5015/zulip/Z6011_5015_e12500_semillerio.csv`
> (copiado como `entrega_final/Z6011_5015_e12500_final.csv`). Para verificarlo, comparar los dos archivos
> (mismo conjunto de ids). LightGBM es multihilo: en otra máquina puede haber diferencias mínimas en las
> probabilidades y, como mucho, unos pocos clientes distintos cerca del corte.
>
> ### Camino completo: también la búsqueda de hiperparámetros (varias horas)
>
> ```bash
> py -3.12 03b_fe_rank_total.py                                             # ds3002 (sin las 6 variables propias)
> py -3.12 08_bo_fuera_de_tiempo.py configs/4104_bo_rank_total.json         # encuentra la prueba 23 (entrena abril)
> py -3.12 08_bo_fuera_de_tiempo.py configs/4107_bo_profesor_mar_abr.json   # Bayesiana marzo + abril; confirma la prueba 23
> ```
>
> Después, los cuatro comandos del camino corto. Las mitades de junio que usan todas las búsquedas están en
> `exp/4102_bo_fuera_de_tiempo/4102_mitades_junio.csv`.
>
> ## 4. Cómo se validó
>
> - **Fuera de tiempo:** se entrena con **202103 + 202104** y se mide en **202106**, que tiene la clase completa.
>   Respeta la misma distancia de 2 meses que hay entre junio y agosto.
> - **Mitades fijas de junio**, estratificadas por clase (549 BAJA+2 en cada una): la Bayesiana elige mirando
>   la **mitad A** y la **mitad B** solo se usa para confirmar. En las últimas comparaciones se usó junio completo.
> - **Métrica "meseta":** ganancia promedio entre 12.000 y 17.000 envíos (equivalentes al mes completo), más
>   estable que el máximo de la curva.
> - **Reglas fijadas antes de ver los resultados** para cada decisión (R1–R9), con semillas pareadas y
>   bootstrap o Wilcoxon. Están en el informe técnico.
>
> ## 5. El corte
>
> | Evidencia | Corte que favorece |
> |---|---|
> | Público (5005: 10.000 → 89,4 · 12.000 → 96,6 · 14.000 → 90,3; 5015: 12.000 → 96,11 · 12.500 → 95,59) | ~12.000 |
> | Mitad B de junio (bootstrap) | 13.500–14.000 |
> | Junio completo, prueba 23 con 12 y 20 semillas (5113, 5114) | meseta plana de 12.500 a 15.000 |
>
> Se eligió **12.500**: el punto medio entre lo que sugería el público y lo que mostraba junio. La diferencia
> pública entre 12.000 y 12.500 (−0,5) está dentro del ruido (±2 a 3 entre listas parecidas).
>
> ## 6. Recomendaciones del profesor: cómo se evaluaron
>
> Cada recomendación se evaluó con el mismo protocolo (entrenar con marzo + abril, medir en junio contra el
> modelo vigente, regla fijada de antemano). Se adoptaron las que mejoraron o empataron.
>
> | Recomendación | Cómo se evaluó | Resultado | Decisión |
> |---|---|---|---|
> | Lags y deltas de orden 1 y 2, y ranking por mes con cero fijo | 5105 / 5106: receta contra el dataset anterior; lag2 contra sin lag2 | La receta mejora; lag2 empata | **Adoptada** (ds3003) |
> | Usar toda la información disponible para buscar hiperparámetros (marzo + abril aunque tengan NA) | 5107: búsqueda con marzo + abril contra solo abril | +4,8 M en junio (75% de los remuestreos) | **Adoptada** |
> | Entrenar el final con todos los meses con clase (marzo a junio) | Entrenamiento final de 5015 | — | **Adoptada** |
> | Sin undersampling, `max_bin` 31, rangos de búsqueda (`num_leaves` 8–2000, `min_data_in_leaf` 0–20.000, `feature_fraction` 0,05–0,9, `bagging_fraction` 0,05–1, `learning_rate` 0,01–0,2) | Bayesiana 4107 | Ninguna prueba nueva superó a la prueba 23 en la mitad B | **Adoptada**; se mantuvo la prueba 23 |
> | Estrategia de entrenamiento 1.7: AUC, `learning_rate` 0,005, `min_data_in_leaf` 0, `feature_fraction` 0,5, `feature_fraction_bynode` 0,2, Bayesiana sobre árboles, hojas y `min_sum_hessian_in_leaf`, y ensamble de 10+ modelos | 4112 (16 pruebas, 15 h) + 5113: ensamble de las 12 mejores contra la prueba 23 | Junio 389,7 vs 441,3: **−52 M**, menor en todos los cortes | No adoptada (regla R7). La búsqueda por AUC eligió árboles de ~1.000 hojas con `min_sum_hessian_in_leaf` muy bajo |
> | Feature engineering 1.1–1.4: `ccajas_depositos` NA en 202105, flags `_zero`, tendencia y promedio de 3 meses | 5114 (ds3007) con los hiperparámetros de la prueba 23, 20 semillas pareadas | Junio 432,7 vs 436,5: **−3,7 M**, mejor en 4/20 semillas | No adoptada (regla R8, tolerancia 3 M) |
>
> ## 7. Otras pruebas
>
> Junio = ganancia de meseta en junio (mitad B ×2 o junio completo, según el experimento), contra el modelo de
> referencia del momento. Público = ganancia en el bot.
>
> | Exp | Qué probé | Resultado | ¿Me lo quedé? | Por qué |
> |---|---|---|---|---|
> | 5005 | Crudo, 123 variables elegidas con canaritos, hiperparámetros de la Bayesiana 4102 | Público 96,58 (12.000) | No | Base de comparación; después el ranking corrigió la inflación |
> | 5105 | 6 variables propias del proceso de muerte (ds3003) contra el dataset sin ellas (ds3002) | Junio +4,6 M (81% de los remuestreos) | **Sí** | Mejora estable |
> | 5108 | Variables de muerte ampliadas (ds3006) | Junio −7,8 M | No | Regla R1 |
> | 5109 | Prueba 23 con la mitad de `min_data_in_leaf` | Junio −21 M | No | Sustenta escalar `min_data_in_leaf` por filas |
> | 4109 / 5110 | Bayesiana "limpia" (elegida solo por la mitad A) | Junio 432,5 vs 443,1 | No | Regla R4 |
> | 5202 | Combinar 5005 con la receta sin lag2 | Público 94,44 | No | Mezclar con un modelo peor bajó al mejor |
> | 5023 | 5015 sin `Master/Visa_Finiciomora` ni `Master/Visa_fultimo_cierre` (columnas con ceros inyectados en 202105, 202106 y 202108) | Público 94,35 (12.500) | No | Regla fijada antes: cambiar solo si el público ≥ 100,6. Se reenvió 5015 como submit final |
>
> ## 8. Supuestos y desvíos declarados
>
> - **Escalar `min_data_in_leaf` por filas** (×2 con dos meses, ×4 en el final). Es una decisión propia; el valor
>   final (40.496) queda fuera del rango de búsqueda recomendado (0–20.000). Se apoya en 5109.
> - **580 árboles fijos** en el final, aunque entrena con más meses que la búsqueda.
> - **`num_leaves` = 41 no actúa:** con `bagging_fraction` 0,31 y `min_data_in_leaf` 40.496, cada árbol tiene
>   como máximo ~5 hojas. El modelo es un boosting de árboles muy chicos.
> - **La prueba 23** fue encontrada en 4104 (entrenando solo abril, dataset ds3002). La Bayesiana 4107, con
>   marzo + abril y los rangos recomendados, la evaluó como referencia y ninguna prueba propia la superó en la mitad B.
> - **ds3003 no pone `ccajas_depositos` en NA en 202105.** Esa corrección se evaluó dentro de ds3007 (5114) y no mejoró.
>
> ## 9. Lo que me llevo para la segunda competencia
>
> - **La validación con 2 meses de entrenamiento eligió siempre el modelo más rígido** (árboles de ~5 hojas), y
>   después ese valor se escaló ×4 para el final. Hipótesis a probar: validar entrenando con más meses
>   (202103–202105 → 202106) antes de elegir la regularización, y medir el efecto de escalar `min_data_in_leaf`
>   en vez de suponerlo.
> - **La estrategia 1.7 depende mucho de `min_sum_hessian_in_leaf`:** optimizar por AUC la llevó a valores muy
>   bajos y a árboles enormes. Conviene buscar con la ganancia o acotar ese parámetro a valores más altos.
> - **El aguinaldo de junio afecta los deltas de orden 2 de agosto**, que comparan contra junio. El ranking por
>   mes corrige los niveles, pero no los saltos.
> - **Calidad de datos en el mes a predecir:** revisar columnas con valores anómalos en 202108 antes de entrenar,
>   porque la validación en junio no puede detectarlos.
>
> ## 10. Estructura del repo
>
> ```
> README.md · requirements.txt · .gitignore
> exp_utils.py                       registro de experimentos (cada uno en exp/<id>_<nombre>/)
> 01_*.py ... 19_*.py                scripts numerados (dataset, FE, búsqueda, final, entrega, evaluaciones)
> configs/                           un JSON por experimento (lo que se corrió, con su descripción)
> *.bat                              lotes reanudables usados en Windows
> exp/                               PARAM, resultados y elecciones de cada experimento (sin archivos pesados)
> entrega_final/                     el CSV enviado como submit final
> informe_tecnico.md                 decisiones, reglas, resultados y desvíos en detalle
> ```
>
> `data/`, `logs/`, cachés y probabilidades por semilla no se versionan: se regeneran.

