"""Busqueda de hiperparametros de LightGBM con Optuna.

Los trials quedan guardados en la base SQLite del experimento, asi que volver a correr no
repite trials: solo se calculan los que faltan.

Cada trial se puntua como en el notebook de clase: ganancia promedio en 5 particiones 70/30
de los meses de train (todas sus filas juntas). El mes de test no se usa para elegir nada.
"""
import lightgbm as lgb
import numpy as np
import optuna
from sklearn.model_selection import StratifiedShuffleSplit

from . import config
from .metricas import feval_ganancia, ganancia_segun_metrica
from .undersampling import construir_si_hace_falta, corregir_probabilidad, indices_muestra

# Espacios de busqueda, uno por iteracion. Nombre: it<NN>_<palabra que lo recuerde>.
# Para probar uno nuevo: copiar el ultimo, darle el numero siguiente y cambiar lo que haga falta.
# Cada parametro buscado: (nombre, tipo, minimo, maximo, escala_log). El orden importa
# (es el orden de los suggest de Optuna).
ESPACIOS = {
    # it00 "z601": el del notebook de clase z601, sin cambios (para reproducir sus resultados)
    'it00_z601': {
        'parametros': [
            ('num_leaves', 'int', 8, 100, False),
            ('learning_rate', 'float', 0.005, 0.3, False),
            ('min_data_in_leaf', 'int', 1, 1000, False),
            ('feature_fraction', 'float', 0.1, 1.0, False),
            ('bagging_fraction', 'float', 0.1, 1.0, False),  # sin bagging_freq no tiene efecto
        ],
        'fijos': {},
        'num_boost_round_max': 1000,
        'paciencia': lambda lr: int(50 + 5 / lr),
        'arboles_fijos': 250,  # los modelos finales usan 250 arboles, no best_iter
    },
    # it01 "bordes": rangos ampliados donde los 250 trials de it00 se apilaban contra el borde,
    # bagging activado y regularizacion L1/L2
    'it01_bordes': {
        'parametros': [
            ('num_leaves', 'int', 4, 64, True),          # los mejores estaban en 8-20, pegados al minimo
            ('learning_rate', 'float', 0.003, 0.1, True),  # los mejores < 0.06; > 0.1 siempre malo
            ('min_data_in_leaf', 'int', 200, 8000, True),  # los mejores en 800-1000, pegados al maximo
            ('feature_fraction', 'float', 0.2, 0.9, False),
            ('bagging_fraction', 'float', 0.2, 1.0, False),  # ahora activo (bagging_freq = 1)
            ('lambda_l1', 'float', 0.01, 10.0, True),      # regularizacion, nuevo
            ('lambda_l2', 'float', 0.01, 100.0, True),     # regularizacion, nuevo
        ],
        'fijos': {'bagging_freq': 1},
        'num_boost_round_max': 3000,
        'paciencia': lambda lr: min(int(50 + 5 / lr), 500),
        'arboles_fijos': None,  # los modelos finales usan best_iter del trial
    },
}


def armar_params(hiperparametros, seed, espacio, verbose=-1):
    """Parametros fijos + los buscados (de un dict de Optuna o una fila de DataFrame)."""
    esp = ESPACIOS[espacio]
    params = {**config.PARAMS_FIJOS, **esp['fijos']}
    for nombre, tipo, *_ in esp['parametros']:
        valor = hiperparametros[nombre]
        params[nombre] = int(valor) if tipo == 'int' else valor
    params['seed'] = seed
    params['verbose'] = verbose
    return params


def sugerir(trial, espacio):
    """Pide a Optuna un valor para cada parametro del espacio."""
    valores = {}
    for nombre, tipo, minimo, maximo, log in ESPACIOS[espacio]['parametros']:
        if tipo == 'int':
            valores[nombre] = trial.suggest_int(nombre, minimo, maximo, log=log)
        else:
            valores[nombre] = trial.suggest_float(nombre, minimo, maximo, log=log)
    return valores


def crear_objetivo_cv(particion, espacio, semilla, test_size=0.3, r=None):
    """Ganancia maxima promedio en 5 particiones 70/30 del train (esquema original).

    r (undersampling): se reduce solo el 70% con el que aprende el modelo; el 30% con el que
    se mide queda completo y sus probabilidades se corrigen. Las muestras son las mismas para
    todos los trials, asi los trials se comparan entre si.
    """
    esp = ESPACIOS[espacio]
    X_train, y_train, train_lgb = particion['X_train'], particion['y_train'], particion['train_lgb']
    sss = StratifiedShuffleSplit(n_splits=5, test_size=test_size, random_state=semilla)
    feval = feval_ganancia(prop=test_size, r=r)
    if r is not None:
        y = np.asarray(y_train)
        folds_muestra = [
            (tr[indices_muestra(y[tr], r, semilla + k)], va)
            for k, (tr, va) in enumerate(sss.split(X_train, y_train))
        ]

    def objective(trial):
        params = {**armar_params(sugerir(trial, espacio), semilla, espacio), 'metric': 'custom'}
        cv_results = lgb.cv(
            params,
            train_lgb,
            num_boost_round=esp['num_boost_round_max'],
            callbacks=[lgb.early_stopping(stopping_rounds=esp['paciencia'](params['learning_rate']), verbose=False)],
            feval=feval,
            folds=sss.split(X_train, y_train) if r is None else folds_muestra,
            seed=semilla,
        )

        max_gan = max(cv_results['valid gan_prob-mean'])
        trial.set_user_attr('best_iter', cv_results['valid gan_prob-mean'].index(max_gan) + 1)
        return max_gan

    return objective


def crear_objetivo_cv_metrica(particion, espacio, semilla, metrica, test_size=0.3, r=None):
    """Como crear_objetivo_cv, pero con cualquier METRICA_OPTUNA y cualquier clase objetivo.

    Las mismas 5 particiones 70/30 (y las mismas muestras si hay undersampling). Cada particion
    sabe cuales de sus clientes son BAJA+2 reales, asi la ganancia se cuenta bien aunque el
    modelo se entrene con BAJA+1 + BAJA+2 (modelo B).
    Diferencia con lgb.cv: cada particion corta por early stopping por su cuenta; la curva
    promedio se toma hasta la particion mas corta y best_iter es su maximo.
    """
    esp = ESPACIOS[espacio]
    X_train, y_train, train_lgb = particion['X_train'], particion['y_train'], particion['train_lgb']
    y_baja2 = np.asarray(particion['y_train_baja2'])
    umbral = particion['umbral'] if metrica == 'umbral_ajustado' else config.UMBRAL
    sss = StratifiedShuffleSplit(n_splits=5, test_size=test_size, random_state=semilla)
    y = np.asarray(y_train)

    construir_si_hace_falta(train_lgb, semilla)
    folds = []
    for k, (tr, va) in enumerate(sss.split(X_train, y_train)):
        if r is not None:
            tr = tr[indices_muestra(y[tr], r, semilla + k)]
        # LightGBM ordena las filas de un subset por posicion: se ordenan aca para que
        # los BAJA+2 reales queden alineados con las predicciones
        tr, va = np.sort(tr), np.sort(va)
        folds.append({
            'train': train_lgb.subset(tr.tolist()),
            'valid': train_lgb.subset(va.tolist()),
            'baja2': y_baja2[va],
        })

    def objective(trial):
        params = {**armar_params(sugerir(trial, espacio), semilla, espacio), 'metric': 'custom'}
        curvas = []
        for f in folds:
            def feval(y_pred, data, baja2=f['baja2']):
                y_pred = corregir_probabilidad(y_pred, r)
                return 'gan', ganancia_segun_metrica(y_pred, baja2, metrica, umbral, prop=test_size), True
            evals = {}
            lgb.train(
                params, f['train'],
                num_boost_round=esp['num_boost_round_max'],
                valid_sets=[f['valid']], valid_names=['valid'], feval=feval,
                callbacks=[
                    lgb.early_stopping(stopping_rounds=esp['paciencia'](params['learning_rate']), verbose=False),
                    lgb.record_evaluation(evals),
                ],
            )
            curvas.append(evals['valid']['gan'])

        n = min(len(c) for c in curvas)
        promedio = np.mean([c[:n] for c in curvas], axis=0)
        best_iter = int(np.argmax(promedio)) + 1
        trial.set_user_attr('best_iter', best_iter)
        return float(promedio[best_iter - 1])

    return objective


def crear_objetivo(experimento, particiones, semilla):
    """Optuna se puntua solo con los meses de train (el mes de test no se mira).

    Con los valores por defecto (modelo A, METRICA_OPTUNA = 'umbral') se usa exactamente el
    mismo codigo que en todos los experimentos ya corridos.
    """
    (particion,) = particiones.values()
    if experimento.clase_objetivo == 'baja2' and experimento.metrica_optuna == 'umbral':
        return crear_objetivo_cv(particion, experimento.espacio, semilla, r=experimento.undersampling)
    return crear_objetivo_cv_metrica(particion, experimento.espacio, semilla, experimento.metrica_optuna,
                                     r=experimento.undersampling)


def cargar_estudio(experimento):
    """Abre el estudio del experimento si existe, o lo crea vacio."""
    return optuna.create_study(
        direction='maximize',
        study_name=experimento.study_name,
        storage=experimento.storage,
        load_if_exists=True,
    )


def trials_completos(study):
    return [t for t in study.trials if t.state.name == 'COMPLETE']


def optimizar_hasta(study, objective, n_trials_total):
    """Corre solo los trials que faltan para llegar a n_trials_total."""
    faltan = n_trials_total - len(trials_completos(study))
    print(f"Trials completos: {len(trials_completos(study))} | faltan: {max(faltan, 0)}")
    if faltan > 0:
        study.optimize(objective, n_trials=faltan)
    return study


def top_trials(study, n=3):
    """Los n trials con mayor valor."""
    return sorted(
        [t for t in study.trials if t.value is not None],
        key=lambda t: t.value,
        reverse=True,
    )[:n]
