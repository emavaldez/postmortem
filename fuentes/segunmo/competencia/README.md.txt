# Competencia (estilo Kaggle)

Espacio de trabajo para las competencias de DMEyF 2026.
- **Primera Competencia:** cierre **dom 11-oct-2026 23:59:59 (hora Buenos Aires)**. Se predice **202108** (último mes del dataset, sin `clase_ternaria`). La "Línea de Muerte" es privada por ahora.
- Última Competencia: lanzamiento ~05-oct, cierre mié 09-dic (confirmar).
**Plan de trabajo y decisiones acordadas: [`PLAN.md`](PLAN.md).** El problema, la función de ganancia y las reglas de integridad están en [`../CLAUDE.md`](../CLAUDE.md).

## Estructura
```
src/config.py        constantes (ganancia, umbral, meses, semillas propias)
src/ganancia.py      ganancia por umbral, ganancia acumulada, mejor corte por cantidad de envíos
src/submit.py        escribe y valida los CSV de submit, arma el cuerpo del mensaje de Zulip
src/data.py          carga del dataset con DuckDB desde el parquet (sin traer todo a memoria); aplica la corrección de ccajas_depositos
src/features.py     features del mes (ratios, negocio), agregados de cambios, eventos de productos
src/historia.py     lags y diferencias (lag1, lagN), lags de features derivadas
src/validacion.py   folds out-of-time y evaluación; src/multiclase.py funciones del modelo multiclase
src/drift.py        PSI y validación adversarial; src/seleccion.py selección con canaritos
experimentos/        NNN_descripcion/ (README.md + scripts/notebook + resultados chicos)
submissions/         CSV enviados + submissions/REGISTRO.md
LOG.md               bitácora: qué se probó, métrica local, puntaje público, conclusión
PLAN.md              plan acordado y estado final (arriba)
GLOSARIO.md          qué significa cada término (fold, M0/M1/M2, ee, PSI, BH…) y cómo leer las tablas
COBERTURA.md         auditoría de lo que proponían las fuentes y plan de lo que falta
REPRODUCIR.md        cómo regenerar el submit final desde el dataset, y evidencia de cada decisión
../research/         investigación de estrategias de la literatura/industria (hipótesis, no medidas)
```

## Flujo
1. Plantear hipótesis en `experimentos/NNN_nombre/README.md` (copiar `experimentos/_plantilla/`).
2. Cambiar UNA cosa respecto del baseline; fijar semillas de `config.py`; medir ganancia sobre **varias semillas** y en un mes out-of-time.
3. Anotar en `LOG.md` (también lo que no funcionó).
4. Si es candidato a submit: generar el CSV desde el script del experimento (reproducible desde `data/competencia_01_crudo.csv`), guardarlo en `submissions/` y registrarlo en `submissions/REGISTRO.md` con el puntaje público.
5. Commit chico por experimento.

## Formato del submit (entrega por Zulip)
Se envía un mensaje de Zulip al bot con **cuerpo** y **uno o varios adjuntos .csv**:
- **Cuerpo:** `submit    NombreInterno` — `submit` en minúsculas; `NombreInterno` es un string sin espacios ni caracteres raros, **distinto en cada submit** (ej. `submit    PredSimpres666`).
- **Adjuntos:** extensión `.csv`, nombres distintos dentro del mensaje (y conviene que sean distintos a todos los enviados alguna vez). Máx. **20 archivos por submit** y **13 submits por día** al inicio (el bot mostró luego 17 y 23 por día; el contador se renueva a las 21:00 hora argentina).
- **Contenido de cada CSV:** solo los `numero_de_cliente` a los que se enviaría estímulo (**entre 8000 y 15000 registros**), **sin encabezado**, uno por línea, como **enteros** (nunca notación científica: 48000000 → `4.8e+07` rompe el submit; también cuidado con 31100000).
- **Respuesta del bot:** *Public Gain mean* (ganancia promedio de cada archivo en el Public Leaderboard, ≈25% de los datos, **sin escalar**, en millones de ARS) y *Public gain std dev*. Para estimar la ganancia total, comparar con una ganancia local escalada (÷0.25 aprox.).

Usar `src/submit.py`: `guardar_submit(ids, nombre)` valida cantidad, enteros, unicidad y nombre, y escribe sin encabezado; `top_k_ids(ids, proba, k)` elige los k mejores; `cuerpo_mensaje(nombre)` arma el cuerpo. Mandar varios archivos (ej. distintas semillas o cantidades de envíos) en un mismo submit permite ver la media y el desvío de la ganancia pública. **El último submit antes del cierre es el final: debe ser un solo archivo** (un envío de varios archivos deja de ser "el final" válido hasta que se reenvíe uno solo).

## Reglas a recordar
- Respetar las restricciones de algoritmos/datos del enunciado de cada competencia.
- La solución final debe ser original, reproducible (semillas incluidas) y comprensible por el alumno: hay examen individual sobre la Última Competencia, sin LLMs.
- Nunca entrenar ni evaluar con meses cuya `clase_ternaria` es NULL.
