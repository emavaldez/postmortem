# DMEyF 2026 - Competencia 01: Predicción de Churn Bancario

**Alumno:** Matías Bellesi  
**Archivo Final Entregado:** `BLEND_CONSENSO_11000_VS_11000_K11000.csv`  


---

## 1. Metodología e Hiperparámetros
- **Hiperparámetros:** Si bien en el proceso experimental se exploró optimización bayesiana con Optuna, sus resultados no superaron la estabilidad del modelo de referencia. Por lo tanto, para la corrida final de producción se adoptaron directamente los **hiperparámetros recomendados por la cátedra para 6 meses** (`learning_rate=0.005`, `num_leaves=85`, `num_iterations=2500`, `min_sum_hessian_in_leaf=0.0067`, `feature_fraction=0.55`, `bagging_fraction=0.80`, `max_bin=31`). No es necesario reejecutar la sección de optimización bayesiana para reproducir el resultado.
- **Feature Engineering:**
  - Corrección operativa de tarjetas inactivas (valores nulos y flag de drift para abril 2021).
  - Eliminación preventiva de variables dañadas (`cprestamos_personales`, `mprestamos_personales`).
  - Lags 1 y 2, deltas porcentuales y absolutos.
  - Pendientes lineales de mínimos cuadrados (`_tend3`) y medias móviles (`_avg3`) aceleradas mediante Numba JIT.
  - Normalización de importes monetarios mediante Ranking Cero Fijo.
- **Selección de Variables:** Filtrado estricto al Top 300 variables por ganancia acumulada.
- **Ensamble Final:** Ensamble por Consenso de Rangos Simétrico (50% modelo 5 semillas + 50% modelo 20 semillas primas) evaluado sobre el corte simétrico de K=11.000 clientes.

---

## 2. Aclaraciones de Ejecución y Reproducibilidad
- **Pipeline Integral:** El notebook contiene el flujo completo desde el dataset crudo hasta el entrenamiento de ambos ensambles (5 y 20 semillas).
- **Generación del Blend:** Al haberse desconectado la máquina virtual de Google Colab tras generar las predicciones parciales, el ensamble final por consenso se computó cargando los dos archivos resultantes de 11.000 clientes (`ENTREGABLE_PROD_GANADOR_K11000.csv` y `GANADOR_20_SEMILLAS_K11000.csv`). No obstante, en una corrida continua el pipeline ejecuta ambos modelos y calcula el blend directamente en la misma sesión.
- **Resultado:** El archivo generado de forma determinística es `BLEND_CONSENSO_11000_VS_11000_K11000.csv`, idéntico al enviado como entrega definitiva de la competencia.
