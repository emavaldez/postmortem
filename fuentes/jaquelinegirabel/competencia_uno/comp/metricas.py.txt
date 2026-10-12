"""Metricas de negocio y de discriminacion para el modelo binario (BAJA+2 vs resto)."""
import numpy as np
from scipy.stats import ks_2samp

from .config import COSTO_ESTIMULO, FRANJA, GANANCIA_ACIERTO, UMBRAL
from .undersampling import corregir_probabilidad


def ganancia_por_cliente(y_true):
    """+GANANCIA_ACIERTO si es BAJA+2, -COSTO_ESTIMULO si no."""
    return np.where(y_true == 1, GANANCIA_ACIERTO, 0) - np.where(y_true == 0, COSTO_ESTIMULO, 0)


def ganancia_umbral(y_pred, y_true, umbral=UMBRAL, prop=1):
    """Ganancia de estimular a todos los clientes con probabilidad >= umbral.

    prop escala la ganancia cuando se evalua sobre una fraccion de los datos (ej. 0.3 en CV).
    """
    return ganancia_por_cliente(y_true)[y_pred >= umbral].sum() / prop


def ganancia_franja(y_pred, y_true, fracciones=FRANJA, prop=1):
    """Ganancia promedio enviando al top f de los clientes, para cada f de `fracciones`.

    No depende de la calibracion: solo del orden de los clientes.
    """
    y_true = np.asarray(y_true)
    ganancia_ordenada = ganancia_por_cliente(y_true)[np.argsort(y_pred)[::-1]]
    acumulada = np.cumsum(ganancia_ordenada)
    n = len(y_true)
    return np.mean([acumulada[max(int(round(f * n)), 1) - 1] for f in fracciones]) / prop


def ganancia_segun_metrica(y_pred, y_true, metrica='umbral', umbral=UMBRAL, prop=1):
    """La ganancia con la que se juzga un modelo, segun METRICA_OPTUNA.

    'umbral' y 'umbral_ajustado' cortan en p >= umbral (el umbral ajustado lo calcula quien llama);
    'franja' promedia el top 5% a 9%. y_true son los BAJA+2 reales.
    """
    if metrica in ('umbral', 'umbral_ajustado'):
        return ganancia_umbral(y_pred, y_true, umbral, prop)
    if metrica == 'franja':
        return ganancia_franja(y_pred, y_true, prop=prop)
    raise ValueError(f"Metrica '{metrica}' no existe. Opciones: umbral, umbral_ajustado, franja")


def feval_ganancia(prop=0.3, umbral=UMBRAL, r=None):
    """Metrica custom para lgb.cv / lgb.train ('gan_prob', mayor es mejor).

    r: fraccion de undersampling del train (None: sin undersampling). Si hay, las
    probabilidades se corrigen antes de aplicar el umbral.
    """
    def ganancia_prob_lgm(y_pred, data):
        y_pred = corregir_probabilidad(y_pred, r)
        return 'gan_prob', ganancia_umbral(y_pred, data.get_label(), umbral, prop), True
    return ganancia_prob_lgm


def ks(y_pred, y_true):
    """Estadistico KS entre las probabilidades de positivos y negativos.

    Devuelve un dict con el valor, el p-value y los datos para graficar las CDF.
    """
    y_true = np.asarray(y_true)
    pred_pos = y_pred[y_true == 1]
    pred_neg = y_pred[y_true == 0]

    ks_stat, ks_pvalue = ks_2samp(pred_pos, pred_neg)

    x_pos = np.sort(pred_pos)
    x_neg = np.sort(pred_neg)

    # punto donde se da la maxima distancia entre las dos CDF
    todos = np.sort(np.concatenate([x_pos, x_neg]))
    cdf_pos_interp = np.searchsorted(x_pos, todos, side='right') / len(x_pos)
    cdf_neg_interp = np.searchsorted(x_neg, todos, side='right') / len(x_neg)
    idx_max = np.argmax(np.abs(cdf_pos_interp - cdf_neg_interp))

    return {
        'ks': ks_stat,
        'p_value': ks_pvalue,
        'x_pos': x_pos,
        'cdf_pos': np.arange(1, len(x_pos) + 1) / len(x_pos),
        'x_neg': x_neg,
        'cdf_neg': np.arange(1, len(x_neg) + 1) / len(x_neg),
        'x_ks': todos[idx_max],
        'cdf_pos_ks': cdf_pos_interp[idx_max],
        'cdf_neg_ks': cdf_neg_interp[idx_max],
    }


def ganancia_acumulada(y_pred, y_true):
    """Ordena por probabilidad descendente y acumula la ganancia.

    Devuelve un dict con la curva, el corte optimo (cantidad de clientes),
    la ganancia maxima y la probabilidad en ese corte.
    """
    orden = np.argsort(y_pred)[::-1]
    ganancia_ordenada = np.where(np.asarray(y_true) == 1, GANANCIA_ACIERTO, -COSTO_ESTIMULO)[orden]
    curva = np.cumsum(ganancia_ordenada)

    mejor_corte = np.argmax(curva) + 1
    return {
        'curva': curva,
        'mejor_corte': mejor_corte,
        'mejor_ganancia': curva[mejor_corte - 1],
        'p_corte': y_pred[orden][mejor_corte - 1],
    }


def umbral_vs_mejor_corte(y_pred, y_true, umbral=UMBRAL, con_franja=False):
    """Compara la regla p >= umbral con el mejor corte posible (elegido mirando las respuestas).

    perdida = cuanto deja de ganar la regla del umbral frente al mejor corte de ese mes.
    con_franja: agrega la ganancia promedio enviando al top 5% a 9% (ver config.FRANJA).
    """
    res = ganancia_acumulada(y_pred, y_true)
    envios_umbral = int((np.asarray(y_pred) >= umbral).sum())
    gan_umbral = ganancia_umbral(y_pred, y_true, umbral)
    return {
        'envios_umbral': envios_umbral,
        'ganancia_umbral': gan_umbral,
        'envios_mejor_corte': int(res['mejor_corte']),
        'ganancia_mejor_corte': res['mejor_ganancia'],
        'p_mejor_corte': res['p_corte'],
        'perdida': res['mejor_ganancia'] - gan_umbral,
        'perdida_pct': (res['mejor_ganancia'] - gan_umbral) / res['mejor_ganancia'] * 100,
        **({'ganancia_franja': ganancia_franja(y_pred, y_true)} if con_franja else {}),
    }


def ganancia_en_cortes(curva, cortes):
    """Ganancia acumulada en cada cantidad de clientes de `cortes`."""
    cortes = np.asarray(cortes)
    cortes = cortes[cortes <= len(curva)]
    return cortes, curva[cortes - 1]


def lift(y_pred, y_true, cortes=np.arange(1000, 20001, 1000)):
    """Tasa de BAJA+2 en el top-N dividida por la tasa en toda la poblacion."""
    y_true = np.asarray(y_true)
    y_true_ordenado = y_true[np.argsort(y_pred)[::-1]]
    tasa_base = y_true.mean()
    return cortes, np.array([y_true_ordenado[:corte].mean() / tasa_base for corte in cortes])


def captura(y_pred, y_true):
    """Proporcion acumulada de BAJA+2 capturados, por percentil de clientes contactados."""
    y_true_ordenado = np.asarray(y_true)[np.argsort(y_pred)[::-1]]
    curva = np.cumsum(y_true_ordenado) / y_true_ordenado.sum()
    n = len(y_true_ordenado)
    percentiles = np.arange(1, n + 1) / n * 100
    return percentiles, curva
