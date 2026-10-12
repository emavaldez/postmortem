# primeracompetencia-dmeyf
Entrega de archivos para reproducir resultados de primera competencia del curso Data Mining para Economía y Finanzas 2026

# 📊 Primera Competencia: Data Mining para Economía y Finanzas 2026
* **Nombre:** [Isabel Espinoza Herrera]
---

## 🏛️ Resumen Metodológico y Bitácora de Experimentos
Este repositorio contiene la arquitectura reproducible utilizada para la Primera Competencia de Churn Bancario. El enfoque principal consistió en explotar la atrición conductual de los clientes mediante ventanas móviles de historia clínica transaccional, optimizando los hiperparámetros mediante mlrMBO y controlando la varianza con ensambles masivos de semillas.

A lo largo del proceso experimental, se exploraron  los límites de la infraestructura y el balance de datos, documentando algunas de las siguientes métricas en el Public Leaderboard:

| ID Experimento | Estrategia de Feature Engineering | Hiperparámetros (Hojas / Rondas) | Muestreo / RAM | Ganancia Pública Promedio (\$) | Veredicto / Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EXP-01** | Variables Originales Base | 30 Leaves / 500 Rondas | 100% Datos | \$ 81.200.000 | 
| **EXP-02 (Récord)** | **Historia Clínica de Orden 1** (Lag1 + Delta1) | **30 Leaves / 2.180 Rondas** | **100% Datos** | **\$ 95.782.500** | **Candidato Elegido** |
| **EXP-03** | Selección Purificada (Gain > 0) | 16 Leaves / 500 Rondas | 30% Undersampling | \$ 84.865.000 | El más estable |
| **VARIOS** | Historia Completa Orden 2 (Lag2 + Delta2) |  Leaves / Rondas varias | 100% Datos | *Fallo por OOM / Colapso* | Error Crítico de Infraestructura |

---

## 🛠️ Lecciones Aprendidas e Ingeniería de Infraestructura 

### 1. El Impacto Exponencial del Orden 1
La incorporación de desfasajes de **Orden 1 (Lags y Deltas a 30 días)** demostró ser el verdadero motor predictivo del modelo, permitiendo que LightGBM identifique patrones nítidos de vaciamiento de cuentas. Esta estrategia empujó la ganancia local y pública de forma neta hacia el récord del laboratorio de **\$95.782.500**.

### 2. El Desafío de la Alta Dimensionalidad y la Memoria Virtual (Out Of Memory)
Al intentar profundizar la sensibilidad del modelo incorporando la historia clínica completa de **Orden 2 (Lags 2 y Deltas 2 a 60 días)**, la matriz de datos se expandió originalmente a **753 columnas complejas**. 
Al entrenar con el 100% de la población (sin undersampling) a lo largo del cuatrimestre acumulado, el volumen matemático colosal saturó de forma iterativa los hilos de cálculo en la Máquina Virtual de 60GB de RAM, provocando:
* **Bloqueos de hilos (*Deadlocks*)** y congelamiento de semillas individuales (superando los 900 segundos por iteración).
* **Caídas completas del Kernel de R** por sobrecarga de memoria (*Out of Memory*).

### 3. Mitigación Híbrida y Criterio de Cierre
Se probó con diferentes undersamplings, todos dando resultados sub-óptimos. Para solucionar la restricción física de hardware, se diseñó e implementó un algoritmo automatizado de **Selección Híbrida de Características** en R (`lgb.importance()`). Este script extrajo las 30 variables reinas del negocio bancario, calculando el Orden 2 estrictamente sobre este grupo selecto para desinflar la base a 501 dimensiones limpias. Evaluando los costos de cómputo remanentes y priorizando la estabilidad estadística ante el corte rígido de envíos, se optó por consolidar la entrega definitiva bajo la arquitectura consagrada de **30 hojas y 2.180 rondas**, la cual demostró el máximo equilibrio de regularización matemática en la población del banco sin llegar al OOM. Se continuarán explorando estrategias para poder utilizar y explotar la información que los lags y deltas de segundo orden puedan aportar y los métodos que se puedan implementar.
