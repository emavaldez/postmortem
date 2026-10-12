"""Ensamble por semillas: entrena el mismo modelo con varias semillas y promedia las
probabilidades. Reduce la variacion que da una sola semilla "con suerte" (o sin ella).

Sirve tanto para evaluar (X_pred = mes de test) como para la prediccion final (X_pred = agosto).
"""
import lightgbm as lgb
import numpy as np

from .undersampling import corregir_probabilidad, dataset_muestra


def predecir_promedio_semillas(params, num_boost_round, train_lgb, X_pred, semillas, archivo=None, recalcular=False,
                               y_train=None, undersampling=None):
    """Promedio de las predicciones de un modelo entrenado con cada semilla.

    undersampling (con y_train): cada semilla entrena con su propia muestra y sus
    probabilidades se corrigen antes de promediar.

    archivo (.npy, opcional): si existe se carga; si no, se guarda ahi el resultado.
    """
    if archivo is not None and archivo.exists() and not recalcular:
        print('Predicciones cargadas desde', archivo)
        return np.load(archivo)

    predicciones = []
    for seed in semillas:
        datos = dataset_muestra(train_lgb, y_train, undersampling, seed)
        model = lgb.train({**params, 'seed': seed}, datos, num_boost_round=num_boost_round)
        predicciones.append(corregir_probabilidad(model.predict(X_pred), undersampling))
    y_pred = np.mean(predicciones, axis=0)

    if archivo is not None:
        np.save(archivo, y_pred)
    return y_pred
