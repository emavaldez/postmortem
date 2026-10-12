# Competencia 1 — Sofía González Romero

Modelo final: notebook 19, ensamble de diez semillas, corte de 12.500 clientes. Envío `sofia13`, ID `1627-1791748586270969`, ganancia pública **101,4200** reportada por el bot.

## Preparación del target desde el archivo crudo

La notebook `notebooks/01_target_sql.ipynb` se incluye sin modificaciones. Parte de `data/competencia_01_crudo.csv` y exporta `data/competencia_01.csv`, que luego consume la 19. Si ya se dispone del archivo con clase_ternaria, ejecutar directamente la 19.

Para ejecutar la notebook de target, instalar primero las versiones de requirements.txt y además `python -m pip install jupysql sqlalchemy duckdb-engine`. Estas tres dependencias adicionales no estaban registradas en la configuración del modelo; sus versiones originales no se conocen. Abrir Jupyter desde la carpeta notebooks para que las rutas relativas `../data` se resuelvan correctamente, y ejecutar la notebook de target en orden. No ejecutar celdas de exportación sobre un archivo que se quiera conservar sin guardar antes una copia.

El SQL construye una grilla de clientes por períodos observados, marca presencia/ausencia y consulta la presencia en los dos períodos siguientes:

| Presencia siguiente | Presencia dos períodos después | Clase |
| --- | --- | --- |
| Sí | Sí | CONTINUA |
| Sí | No | BAJA+2 |
| No | No | BAJA+1 |
| Otras combinaciones o futuro no disponible | | NULL |

Solo se exportan filas en las que el cliente está presente en el período actual. Los últimos períodos pueden quedar sin target. La definición supone que los períodos observados son meses consecutivos: LEAD opera por posición dentro de la grilla de períodos. La 19 usa BAJA+2=1 y CONTINUA/BAJA+1=0; excluye filas sin target del entrenamiento.

Se incluye el procedimiento original como antecedente; no se ha ejecutado de nuevo aquí ni comparado su exportación con el dataset utilizado en el envío. La consulta COPY original no fija ORDER BY: no se garantiza el mismo orden de filas o hash del CSV exportado. Para verificar la cadena completa desde crudo hay que comparar claves, valores y target del archivo generado con el utilizado en la corrida final.

## Ejecución del modelo desde competencia_01.csv

1. Usar preferentemente Python **3.14.7**, la versión registrada en la corrida.
2. Crear un entorno e instalar dependencias: `python -m pip install -r requirements.txt`.
3. Crear `data/` en la raíz de este repositorio y colocar allí **competencia_01.csv** de la competencia. El dataset no se incluye.
4. Abrir `notebooks/19_Modelo_Final.ipynb`, elegir ese entorno, reiniciar el kernel y ejecutar todas las celdas en orden.
5. Buscar el ensamble en `resultados/exploracion19_…/envios/…/SofiaCerca19Ensamble_…/`. El archivo terminado en `_top13000.csv` es el candidato final. Los archivos ANALISIS contienen probabilidades y no son envíos.

La notebook no requiere una base de Optuna, modelos, FE ni selecciones de corridas anteriores. Reconstruye todo desde el original. Cada ejecución utiliza una carpeta nueva. El CSV de referencia es solo para verificar; no se usa para entrenar ni predecir.

## Método

Se corrige ccajas_depositos de mayo a NA. Se excluyen préstamos personales y sus derivadas. Se generan lags de uno y dos meses calendario y deltas; se normalizan por máximo absoluto de cada variable dentro del mes. Tendencia y promedio usan la observación actual y dos anteriores por cliente, con al menos dos valores válidos; no necesariamente son tres meses consecutivos. Julio aporta historia para agosto. No se agregan flags cero ni ranking percentil.

Canaritos: semilla 17, 1000 árboles, 31 hojas, Hessian mínimo 10; ruido uniforme equivalente al 20 % de las variables evaluables, con mínimo diez canaritos. La selección usa posiciones de importancia gain, mediana de posiciones de canaritos menos un desvío muestral; conserva aparte columnas vacías o constantes. La lista anterior de 400 variables en la notebook sirve únicamente para comparar, nunca para sustituir la selección nueva.

Búsqueda: marzo–abril para entrenamiento, junio para validación; target BAJA+2=1 y CONTINUA/BAJA+1=0, sin undersampling. Se maximizó AUC con cinco trials secuenciales, semilla 17, estudio vacío. Rangos: árboles 1000–2000, paso 100; hojas 8–128; Hessian mínimo 0,1–100 en escala logarítmica. TPESampler predeterminado tiene diez trials iniciales aleatorios: esta búsqueda de cinco trials permanece en esa fase, sin etapa adaptativa TPE.

Parámetros fijos de la cátedra: max_bin=31, min_data_in_leaf=0, feature_fraction=0.50, feature_fraction_bynode=0.20, learning_rate=0.005. La configuración ganadora fue **1000 árboles, 103 hojas y min_sum_hessian_in_leaf=9.311090875055461**. Es un resultado de búsqueda; la notebook lo vuelve a buscar.

Se valida con diez semillas y se reentrena con marzo–junio. Semillas: [17, 103, 211, 307, 401, 503, 601, 701, 809, 907]. Se promedian las probabilidades de agosto con pesos iguales y se ordenan de mayor a menor, desempate por ID ascendente. El CSV contiene IDs sin encabezado. El corte final es 12.500.

La variante se exploró alrededor de los 1500 árboles del experimento anterior. Su elección consideró la validación de junio y la comparación pública de agosto; el resultado público no constituye una evaluación independiente de la selección final.

## Verificación contra el envío

El CSV final está en `referencia/SofiaCerca19Ensamble_20261011_162005_top12500.csv`. SHA256: `f2827098eaa3b85bfea46a3094c9da8bb58c30c05c9ebd2e46d3b134c9bdd3a0`.

La última celda original compara contra un CSV anterior de la 13 si existe; no es la referencia del envío final de la 19. Para comparar con este envío, cambiar **solo** CSV_REFERENCIA en la celda de configuración a:

```python
CSV_REFERENCIA = BASE / "referencia" / "SofiaCerca19Ensamble_20261011_162005_top13000.csv"
```

Esto no cambia entrenamiento ni predicciones. Al final muestra coincidencia de clientes, orden y bytes. Distintos saltos de línea pueden cambiar bytes sin cambiar IDs ni orden. La comparación de parámetros que menciona 1500 árboles es contra la corrida anterior; False es esperable para la 19.

La estructura de la notebook, configuración y formato del CSV se comprobaron. El dataset original y modelos no están disponibles en este paquete: no se volvió a ejecutar el entrenamiento aquí ni se comprobó una segunda ejecución exacta contra este CSV. Conservar las versiones registradas y verificar el CSV regenerado; plataformas y versiones pueden afectar resultados.

## Archivos

- `notebooks/01_target_sql.ipynb`: preparación original del target desde el dataset crudo.
- `notebooks/19_Modelo_Final.ipynb`: código suministrado, sin cambios al entrenamiento.
- `requirements.txt`: versiones registradas en la configuración.
- `registro/`: configuración de corrida e historia, selección e identificación del envío.
- `referencia/`: CSV final enviado.

No subir a GitHub el dataset, las bases DuckDB ni la carpeta resultados. Son archivos regenerables y quedan excluidos por .gitignore.
