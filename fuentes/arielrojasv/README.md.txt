# Predicción Bajas en Agosto

El repositorio cuenta con 2 carpetas:

- Predicción: contiene 2 scripts, "Optimizador_Hiperparametros.ipynb" y "Modelo_Final.ipynb".

- Script_IngenieraData: contiene 1 solo script, "IngenieriaAtributos.ipynb"


En primer lugar se debe ejecutar el script de "IngenieriaAtributos". Este toma el archivo inicial y genera 
una variedad de atributos, como lags de orden 1 y 2, delta lags de orden 1 y 2, combina atributos y calcula 
algunas relaciones entre los mismos. 

Para realizar esta tarea se utiliza SQL.

Este archivo se exporta como csv.


En segundo lugar se puede ejecutar el script de "Modelo_Final", el cual genera el listado final de clientes, 
creando un csv con el detalle de los numeros de clientes. 

En este se utiliza lenguaje R.


El script de "Optimizador_Hiperparametros", permite determinar los mejores hiperparametros tomando como entrenamiento
los meses de 202103 y 202104, testeando en 202106.

Este script se deberia ejecutar luego de "IngenieriaAtributos". El resultado del mismo se utiliza en el 
script que genera el modelo final, el cual ya posee los mejores hiperparametros del modelo, con lo cual en este caso 
puede saltearse este paso.

Para este script se tomo como base el "Gustavo Pasquini", optimizando 3 hiperparametros:
- num_iterations
- num_leaves
- min_sum_hessian_in_leaf
  
No se uso undersampling.

La métrica a optimizar es "auc".

El script también devuelve la curva de envios para 202106 con las ganancias estimadas, que se uso para determinar
el corte óptimo.

Los mejores hiperparametros de este se utilizan en el Modelo Final, para reentrenar con los nuevos meses y predecir 202108.
