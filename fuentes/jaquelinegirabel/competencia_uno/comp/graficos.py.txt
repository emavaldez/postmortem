"""Graficos (plotly) de las metricas del modelo. Cada funcion devuelve la figura."""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import gaussian_kde

from . import metricas


def box_semillas(df_semillas, estadisticas, columna='ganancia_promedio', titulo_mes='test'):
    """Distribucion de ganancia por modelo: la caja y todas las semillas como puntos."""
    orden_trials = [str(t) for t in estadisticas.index]
    n_semillas = df_semillas['seed'].nunique()

    fig = go.Figure()
    for trial in estadisticas.index:
        datos_trial = df_semillas[df_semillas['trial'] == trial]
        fig.add_trace(go.Box(
            y=datos_trial[columna],
            x=[str(trial)] * len(datos_trial),
            name=str(trial),
            boxpoints='all', jitter=0.4, pointpos=0,
            showlegend=False,
        ))

    fig.update_layout(
        title=f"Ganancia en {titulo_mes} por modelo ({n_semillas} semillas)",
        xaxis_title="Trial (modelo)",
        yaxis_title=f"Ganancia en {titulo_mes}",
        xaxis=dict(categoryorder='array', categoryarray=orden_trials),
        template='plotly_white',
    )
    return fig


def distribucion_por_clase(y_pred, clase_ternaria):
    """Histograma + KDE de la probabilidad predicha, total y por clase real."""
    clase = np.asarray(clase_ternaria)
    grupos = [
        ('Distribución de la salida (todas las clases)', y_pred, 'gray'),
        ('Distribución de la salida - BAJA+2', y_pred[clase == 'BAJA+2'], 'red'),
        ('Distribución de la salida - BAJA+1', y_pred[clase == 'BAJA+1'], 'orange'),
        ('Distribución de la salida - CONTINUA', y_pred[clase == 'CONTINUA'], 'blue'),
    ]

    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, subplot_titles=[g[0] for g in grupos])
    for i, (_, datos, color) in enumerate(grupos, start=1):
        fig.add_trace(go.Histogram(
            x=datos, nbinsx=50, histnorm='probability density',
            marker_color=color, opacity=0.6, showlegend=False,
        ), row=i, col=1)

        kde = gaussian_kde(datos)
        x_kde = np.linspace(datos.min(), datos.max(), 200)
        fig.add_trace(go.Scatter(
            x=x_kde, y=kde(x_kde), mode='lines',
            line=dict(color=color), showlegend=False,
        ), row=i, col=1)

    fig.update_layout(height=1000, width=700, template='plotly_white')
    fig.update_xaxes(title_text='Probabilidad predicha', row=4, col=1)
    return fig


def curva_ks(res_ks):
    """CDF de probabilidades por clase y la distancia maxima (KS). res_ks = metricas.ks(...)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=res_ks['x_pos'], y=res_ks['cdf_pos'], mode='lines',
                             name='Clase 1 (Baja)', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=res_ks['x_neg'], y=res_ks['cdf_neg'], mode='lines',
                             name='Clase 0 (Continúa)', line=dict(color='blue')))
    fig.add_trace(go.Scatter(
        x=[res_ks['x_ks'], res_ks['x_ks']], y=[res_ks['cdf_neg_ks'], res_ks['cdf_pos_ks']],
        mode='lines', name=f"KS = {res_ks['ks']:.4f}",
        line=dict(color='black', dash='dash'),
    ))
    fig.update_layout(
        title='Test KS - distribución acumulada de probabilidades por clase',
        xaxis_title='Probabilidad predicha',
        yaxis_title='CDF',
        template='plotly_white',
    )
    return fig


def curva_ganancia(res_gan, limite=20000, titulo='Ganancia acumulada según cantidad de clientes estimulados',
                   envios_umbral=None, umbral=None):
    """Ganancia acumulada con el corte optimo marcado. res_gan = metricas.ganancia_acumulada(...)."""
    curva = res_gan['curva']
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, limite + 1)), y=curva[:limite],
        mode='lines', name='Ganancia acumulada', line=dict(color='blue'),
    ))
    fig.add_vline(
        x=res_gan['mejor_corte'], line_dash='dash', line_color='black',
        annotation_text=f"Corte óptimo: {res_gan['mejor_corte']} clientes",
        annotation_position='top',
    )
    fig.add_trace(go.Scatter(
        x=[res_gan['mejor_corte']], y=[res_gan['mejor_ganancia']],
        mode='markers+text', marker=dict(color='red', size=10),
        text=[f"p = {res_gan['p_corte']:.4f}"], textposition='middle right',
        showlegend=False,
    ))
    if envios_umbral:
        # punto de la regla p >= umbral sobre la misma curva
        fig.add_trace(go.Scatter(
            x=[envios_umbral], y=[curva[envios_umbral - 1]],
            mode='markers+text', marker=dict(color='green', size=10, symbol='diamond'),
            text=[f'p ≥ {umbral}: {envios_umbral} clientes'], textposition='bottom right',
            showlegend=False,
        ))
    fig.update_layout(
        title=titulo,
        xaxis_title='Cantidad de clientes ordenados por probabilidad descendente',
        yaxis_title='Ganancia acumulada',
        xaxis_range=[0, limite],
        template='plotly_white',
    )
    return fig


def curva_lift(cortes, lift_valores):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cortes, y=lift_valores,
        mode='lines+markers', marker=dict(color='green'), line=dict(color='green'),
        name='Lift',
    ))
    fig.add_hline(y=1, line_dash='dash', line_color='gray', annotation_text='Azar (lift = 1)')
    fig.update_layout(
        title='Lift según cantidad de clientes estimulados',
        xaxis_title='Cantidad de clientes (ordenados por probabilidad descendente)',
        yaxis_title='Lift',
        xaxis=dict(tickvals=cortes, tickangle=-45),
        template='plotly_white',
    )
    return fig


def curva_captura(percentiles, captura, titulo='Captura acumulada de BAJA+2'):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=percentiles, y=captura, mode='lines', name='Modelo', line=dict(color='blue')))
    fig.update_layout(
        title=titulo,
        xaxis_title='Percentil de clientes (ordenados por probabilidad descendente)',
        yaxis_title='Proporción de BAJA+2 capturados',
        xaxis_range=[0, 100],
        template='plotly_white',
    )
    return fig


def todas_las_metricas(y_pred, y_true, clase_ternaria, umbral=metricas.UMBRAL, y_objetivo=None):
    """Calcula y grafica todas las metricas de un modelo de una vez. Devuelve (resumen, figuras).

    y_true: BAJA+2 reales (con los que se cuenta la ganancia). umbral: corte de decision (0.025 en el
    modelo A). y_objetivo: la etiqueta con la que se entreno, si no es BAJA+2 (modelo B), para el
    control de calibracion.
    """
    res_ks = metricas.ks(y_pred, y_true)
    res_gan = metricas.ganancia_acumulada(y_pred, y_true)
    cortes, lift_valores = metricas.lift(y_pred, y_true)
    percentiles, capt = metricas.captura(y_pred, y_true)

    resumen = {
        'ks': res_ks['ks'],
        f'ganancia_umbral_{umbral:.4g}': metricas.ganancia_umbral(y_pred, y_true, umbral),
        'mejor_corte': int(res_gan['mejor_corte']),
        'mejor_ganancia': res_gan['mejor_ganancia'],
        'p_corte': res_gan['p_corte'],
        # calibracion: con probabilidades bien corregidas, las dos tienen que ser parecidas
        'prob_media': float(np.mean(y_pred)),
        'tasa_real_baja2': float(np.mean(np.asarray(y_true))),
    }
    if y_objetivo is not None:
        resumen['tasa_real_objetivo'] = float(np.mean(np.asarray(y_objetivo)))  # comparar con prob_media
    figuras = {
        'distribucion': distribucion_por_clase(y_pred, clase_ternaria),
        'ks': curva_ks(res_ks),
        'ganancia': curva_ganancia(res_gan),
        'lift': curva_lift(cortes, lift_valores),
        'captura': curva_captura(percentiles, capt),
    }
    return resumen, figuras
