# Plan de la Primera Competencia (acordado con el alumno, 2026-10-03)

**Deadline:** dom 11-oct-2026 23:59:59 (hora Buenos Aires). Se predice **202108**.
> **ESTADO FINAL (2026-10-09): submit entregado = `exp031_final_w67_md_k12000.csv`, un solo archivo, Public 103.21M** (Línea de Muerte ≈ 100M en Public; Private ≈ 3 × Public). Es el rank 2/3 de M2 (multiclase CONTINUA/BAJA+1/BAJA+2 con todas las variables con lag1, lag2 y diferencias, 855 columnas, 3 configs × 10 semillas) + 1/3 del blend anterior (017 + 010 + receta del profe), k=12000. Receta para regenerarlo: [`REPRODUCIR.md`](REPRODUCIR.md). Evidencia y descartes: [`LOG.md`](LOG.md) y [`submissions/REGISTRO.md`](submissions/REGISTRO.md).
> **Plan de cierre de huecos (auditoría + reglas de decisión fijadas de antemano): [`COBERTURA.md`](COBERTURA.md) §7–12.**
> Este documento conserva el plan original (2026-10-03) y su evolución como historia: las secciones de abajo se escribieron antes de los resultados que se indican; donde algo cambió, está marcado con ✅/→.
Leer también: `LOG.md` (resultados), `README.md` (formato de submit), `../CLAUDE.md` (contexto y reglas).

## Decisiones tomadas (no re-discutir sin evidencia nueva)
- **Datos:** usar el parquet (`data/competencia_01.parquet.gzip`, ya generado; `src/data.py` lo usa solo). Solo hay meses 202103–202108; con target completo hasta 202106 (202107: solo BAJA+1, 202108: sin target).
- **Más meses de train / walk-forward largo:** se saltea en esta competencia (no hay más meses); queda para la Última Competencia, donde también habrá que considerar inflación en los montos.
- **Optuna (LightGBM) y variables históricas:** obligatorios.
- **Selección de variables:** sí, descartar las que no aportan para bajar el costo computacional (ver 004).
- **Drift / variables de fecha:** primero **EDA para entender qué significan** (no tirar ni transformar a ciegas). Ajuste por inflación: no ahora.
- **Clase BAJA+1+2 (006) y undersampling (007):** baja prioridad, pruebas al final, el alumno desconfía de ambas. → ✅ 007 hecho (ayuda, r≈0.1); 006 se probó recién en 026/034: como binario no mejora al multiclase con la historia completa; lo que entró fue el **multiclase** (010/013).
- **Validación:** siempre out-of-time, 5 semillas propias (`src/config.py`), corte por cantidad de envíos (top-k, k en 8000–15000). Entrenamiento final con todos los meses con target (202103–202106).

## Esquema de validación para comparar experimentos
Dos folds out-of-time (el target de un mes mira 2 meses adelante, por eso hay un mes de separación):
- **Fold A:** train 202103 → valid 202105.  **Fold B:** train 202103+202104 → valid 202106 (el del baseline).
- Métrica: ganancia con el top-k óptimo sobre una grilla (reportar también k fijo ~11000), media ± desvío entre 5 semillas, en ambos folds.
- **Semillas: usar 20 (las 5 propias + 15 derivadas, ver `002_eda_variables/run_potencia.py`) para decidir.** Con 5 el ruido de la media es de ±4–8M (en 002 un +13M con 5 semillas era −0.4M con 20). Comparar de a pares (misma semilla) y aceptar un cambio solo si mejora ambos folds por más que ~2 errores estándar de la diferencia. Referencia del baseline (k=11000, 20 semillas): **A 220.6M, B 361.8M**. Nota: el fold B (valid 202106) está inflado por el aguinaldo; no comparar niveles absolutos entre folds.
- Herramientas: `src/validacion.py` (`evaluar`, `resumen`), `src/features.py`, `src/drift.py`.
- Cada experimento: cambiar UNA cosa, carpeta `experimentos/NNN_nombre/` con README y script reproducible (copiar el patrón de `001_baseline_lgbm/run.py`), y fila en `LOG.md`.
- No elegir por el Public LB (≈25% de 202108, ruidoso): usarlo como control de cordura.

## Fases y experimentos (orden recomendado)
| # | Experimento | Objetivo / método | Fecha objetivo |
|---|---|---|---|
| 002 | ✅ **HECHO** — ver `experimentos/002_eda_variables/README.md`. Resultado: ninguna transformación de fechas/calendario mejora la ganancia (con 20 semillas); 202108 sin drift fuerte; se mantienen variables crudas. **EDA de variables** (sin modelar) | Entender el significado de cada familia en `docs/diccionario_datos.csv`. Foco: variables de fecha en días (`*_Finiciomora`, `*_Fvencimiento`, `*_fultimo_cierre`, `*_fechaalta`, `cliente_antiguedad`). Hallazgo inicial: `Master_Finiciomora` (99.5% nulo) crece ~30 días por mes (máx 169→207→230→260→291→300) porque es *tiempo transcurrido*: un corte tipo "> 200" solo existe en meses futuros → drift mecánico. `Visa_Finiciomora` en 202105 y 202108 tiene 2.6% de no-nulos con media ~9 días (vs 0.6% y ~45 en el resto): 202108 se parece a 202105 → **hipótesis a verificar**; mirar si 202105 es un buen mes de validación. Probar transformaciones (días → fecha de inicio absoluta, binarias "está en mora", etc.) y medir ΔGanancia en ambos folds. También: PSI de 202108 vs train sin usar target, nulos/ceros por mes. | 03–05 oct |
| 003 | **Feature engineering histórico** (003a lag1+delta1 HECHO: +4.5/+5.7M débil, ver exp; 003b ratios HECHO (+5.7/+12.5M vs base; marginal sobre 003a +1.2/+6.8); lag2/medias móviles/tendencia NO validables con los meses disponibles (ver 003b/README) → 003c HECHO (features del mes): ratios entre variables +0.4/+3.6M (ruido), percentiles descartados (−2M); el pool de 004 = originales + historia 003b (lag1, delta1, ratio1 de 50 vars) + 17 ratios de 003c; subset = `003a/variables_historia.txt`; el train truncado se trata con el híbrido NaN nativo + fold Bh + control barajado) | Con funciones de ventana en DuckDB (`lag`, `avg over rows between`): lags 1 y 2, delta lag, medias móviles (3 meses), tendencia (pendiente) para variables numéricas relevantes. Ojo: con sólo 202103–202108 un lag de 2 meses deja sin historia a los primeros meses; decidir cómo tratar los nulos de borde y NO usar información del futuro (solo meses ≤ t). Generar a parquet y medir en los 2 folds. | 04–06 oct |
| 004 | **Selección de variables** (HECHO: regla canarito descartada, top150 = pool completo y 2.4× más rápido → `004/variables_final_top150.txt`) | Sobre el set ampliado (150 → ~500+ columnas). Método sugerido: agregar columnas aleatorias ("canaritos") y descartar las variables cuya importancia (gain, promediada en varias semillas) sea menor a la de los canaritos / cero; decidir la selección **solo con meses de train**, no con el de validación. Verificar que la ganancia no cae y que el tiempo baja. | 06–07 oct |
| 004b | Mezcla M0+M1 (HECHO, ver exp): la ganancia es sobre todo ensemble size; promediar 20–30 semillas en el final; mezcla = cobertura. | | 
| 005 | ✅ HECHO (ver `experimentos/005_optuna/README.md`): MIX6 +20 a +40M sobre el baseline en reeval. **Optuna sobre LightGBM** | Sobre el set final de variables. Objetivo = ganancia media en ambos folds (o CV agrupado por cliente dentro del train), no un solo valor. Rangos amplios (`num_leaves`, `learning_rate` en log, `min_data_in_leaf`, `feature_fraction`, `bagging_fraction`, `lambda_l1/l2`, rondas), storage SQLite en `artifacts/optuna/` para reanudar. Reevaluar los mejores 3–5 trials con semillas distintas a las de la búsqueda antes de elegir (z203: riesgo de sobreoptimizar). Pensar en correr de noche. | 07–09 oct |
| 006 | ✅ HECHO (026, 034) — Clase BAJA+1+2 (baja prioridad) | Binario con ambas bajas: gana con 1 mes de train pero pierde con 2 meses o con las 855 columnas (026: +9.2 / −4.6 / +5.8M en A/B/Bh; 034: −4 a −9M); en el Public (k=12000, 4 meses) +1.3M sobre el multiclase, no concluyente. El multiclase con score P2/(1−P1) lo reemplaza. | 09–10 oct |
| 007 | ✅ HECHO (adelantado): r=0.2 mejora +5 a +15M en 6/6 combinaciones; r va como hiperparámetro de Optuna (0.05–0.5). Undersampling de CONTINUA (baja prioridad) | Prueba rápida: ¿mantiene la ganancia? Si sí, puede acelerar Optuna; si no, descartar. Si Optuna resulta muy lento, adelantarlo. | 09–10 oct |
| 008 | ✅ HECHO — **Modelo final y submit** | Final = `exp031_final_w67_md` (017 → 019 → 024 → 031). k=12000 (015, 018, 025). Un solo archivo. Ver `REPRODUCIR.md`. | entregado 09-oct |

## Estrategia de submits
- Máx. 13 submits/día al inicio (el bot llegó a mostrar 17 y 23 por día; se renueva a las 21:00 ART) y hasta 20 archivos por submit. El bot devuelve solo media y desvío entre los archivos.
- **El último submit antes del cierre es el final.** Antes del cierre, el último envío debe ser el modelo elegido. **Confirmar en Zulip cómo se puntúa el submit final si trae varios archivos** (¿el mejor, el promedio, el primero?); hasta saberlo, el submit final debería llevar **un solo archivo**. → Resuelto en la práctica: el final es un solo archivo; los envíos de varios archivos fueron solo mediciones (ruido por semilla, curva de k).
- Usar el Public LB (baseline = 94.2M) para detectar desastres (ej. un error de formato o drift enorme), no para elegir entre diferencias chicas. **Escala:** el Public es ~25% del mes; las diferencias de ganancia locales (mes completo) hay que dividirlas por ~4 para compararlas con el Public. Ruido por semilla ≈ 2.5M con 1 semilla por configuración, ≈ 1M con 6.
- Antes de cada submit: registrar en `submissions/REGISTRO.md`.

## Riesgos a vigilar
1. Leakage temporal en las variables históricas (usar solo meses ≤ t) y en la selección de variables (no usar el mes de validación).
2. Sobreajustar la validación (un fold, un mes) con Optuna y FE: siempre 2 folds y semillas de evaluación distintas de las de la búsqueda.
3. Tiempo/cómputo: Optuna con cientos de columnas es lento; seleccionar variables antes.
4. Drift en 202108 que no existe en los meses de validación (ver 002).
5. Formato del submit (enteros, sin encabezado, 8000–15000 filas): `src/submit.py` ya valida.
6. Para el material de la cátedra: mantener el repo reproducible (semillas propias, scripts que parten del dataset original).

---

## Actualización 2026-10-07 (noche) — estado y experimentos pendientes

**Estado:** modelo vigente = MIX6 (6 trials de Optuna de 005, M0 y M1) pasado a **multiclase** (CONTINUA/BAJA+1/BAJA+2), score `P(BAJA+2)/(1−P(BAJA+1))`, promedio por rank, `ccajas_depositos`=NA en 202105, r≈0.1 sobre CONTINUA (BAJA+1 y BAJA+2 completos), sin lag2. Public: 99.99M (`exp010_mc_h2`, 6 semillas/config, un archivo), 98.0M ± 2.5M con 1 semilla/config (5 archivos): el ruido por semilla del Public es ~2.5M, no leer diferencias < 3M. Línea de Muerte ≈ 100M (Public). **El submit final tiene que ser UN solo archivo** (el vigente hoy en el bot es el de 5 archivos hasta que se reenvíe uno solo; `exp010_mc_h2_k11500.csv` es el candidato seguro).
Descartado hoy (ver LOG.md): más variables con historia (008c), lags de derivadas / eventos / agregados / comisiones (011), receta del profe (009/009b: el undersampling sigue ayudando, la receta no suma al ensemble), Optuna propio del multiclase (012: meseta, +0.005 de índice sobre las anclas). Ganó: multiclase con score condicional (+7.5 a +10.5M vs binario, 15/15 pares); rank ≥ probabilidad (+1M).

**En curso:** ✅ 013 hecho — el ensemble multiclase conserva la ventaja: +9.0 / +5.9 / +8.8M sobre el MIX6 binario, 15/15 pares.

### 014 (✅ HECHO: +0.9 a +1.5M, casi todo por usar un binario dedicado; incluido en 017) — usar 202107: modelo auxiliar de BAJA+1 con un mes más de datos
**Idea (del alumno + research B2):** de 202107 se conoce BAJA+1 (quién no está en 202108) pero no BAJA+2 (necesita 202109). El término `P(BAJA+1)` del score condicional se puede estimar con 202103–202107, o sea con el mes más cercano a 202108, que hoy queda afuera del entrenamiento.
**Validación honesta (fold B):** modelo principal multiclase entrena 202103–04 → valida 202106 (como hoy); el auxiliar de BAJA+1 (binario, o 2 clases BAJA+1 vs resto) entrena 202103–05 (202105 hace de "202107": BAJA+1 conocido, BAJA+2 no). Score = `P2_principal / (1 − P1_aux)`. Comparar pareado (10 semillas) contra el multiclase actual (`P2/(1−P1)` del mismo modelo). Réplica con el desfase de Bh si hay tiempo.
**Cuidados:** (a) las filas de 202105 sin BAJA+2 conocido NO pueden entrar al modelo principal (sus BAJA+2 estarían mal etiquetados como CONTINUA); solo entran al auxiliar de BAJA+1, y ahí el "resto" incluye ~0.6% de BAJA+2 que se confunde con no-baja (efecto menor, verificar); (b) sin leakage: el auxiliar no ve el target del mes de validación; (c) para el final: auxiliar entrena 202103–07 y principal 202103–06.
**Control incluido en el mismo experimento:** pesos 2× a los meses viejos (202103–04) = "copiar los dos primeros meses" (idea del alumno); se espera ≈ 0, es el control de que duplicar no agrega información.
**Decisión:** entra al final si mejora en B (y Bh) por > ~2 ee pareados.

### Orden hasta el cierre (dom 11-oct 23:59) — plan del 07-oct, superado por los hechos (ver estado final arriba)
| Cuándo | Qué |
|---|---|
| Hoy/mañana | 013 → 014 → 015/016 (k y lag2) → 018 → 020–035 (receta, opciones LightGBM, todas las variables con lags, min_data). Ver LOG.md. |
| 9–10-oct | Final = 031 (M2 + blend), k=12000, un solo archivo; registrado en REGISTRO.md. |
| 10-oct | Submit del candidato final (UN archivo). |
| 11-oct | Solo colchón: el último submit antes de las 23:59:59 es el que cuenta. Verificar que el último sea un único archivo. |
