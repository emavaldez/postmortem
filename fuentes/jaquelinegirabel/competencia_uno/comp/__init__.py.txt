"""Modulos para el modelo de BAJA+2 (competencia 01).

- config:               rutas, matriz de ganancia, meses, semillas, parametros fijos
- experimento:          flags de un experimento y carpetas donde se guardan sus resultados
- datos:                carga del dataset (con cache parquet) y X / y por meses
- particiones:          train (meses_train) y test (mes_test) de un experimento
- metricas:             ganancia, KS, ganancia acumulada, lift, captura
- optimizacion_optuna:  espacios de busqueda y estudio de Optuna (reanudable)
- modelos:              entrenar/cargar modelos, top trials, estabilidad por semillas
- ensamble:             promedio de predicciones de varias semillas
- graficos:             figuras plotly de las metricas
- entrega:              prediccion de agosto y archivo de submit (submits/)
"""
