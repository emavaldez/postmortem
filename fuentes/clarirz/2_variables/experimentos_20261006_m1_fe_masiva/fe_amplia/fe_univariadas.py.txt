"""Transformaciones univariadas explícitas según semántica, no según target."""
from __future__ import annotations
import numpy as np
from fe_core import flag, safe_divide, FORBIDDEN

def generate_univariate(panel, spec, config):
    v = spec['variable']
    if v in FORBIDDEN:
        raise ValueError('Una clave o target no puede transformarse como predictor')
    kind = spec['kind']; x = panel.get(v); obs = np.isfinite(x)
    lags = config['lags']; windows = config['windows']; maxk = max(max(lags), max(windows)-1)
    def emit(op, values, block, formula, history=0, fkind='numeric', caution='', unit=None):
        return f'fe__{v}__{op}', np.asarray(values, dtype=float), {
            'block': block, 'sources': [v], 'formula': formula,
            'interpretation': f"{spec.get('history_mode','unknown')}: {op}",
            'min_history': history, 'unit': unit or spec.get('unit','--'),
            'caution': (spec.get('caution','') + ' ' + caution).strip(), 'feature_kind': fkind}

    yield emit('missing', ~obs, 'disponibilidad', '1 si el valor no es finito, 0 si observado', unit='indicador')
    # Diferenciar transición de disponibilidad de falta de fila.
    for k in lags:
        prev = panel.lag(x, k); po = np.isfinite(prev); row = panel.row_present(k)
        yield emit(f'aparece_dato_l{k}', flag(obs & ~po, row), 'disponibilidad', f'fila t-{k} presente con NA, valor t observado', k, unit='indicador')
        yield emit(f'desaparece_dato_l{k}', flag(~obs & po, row), 'disponibilidad', f'fila t-{k} presente y observada, valor t NA', k, unit='indicador')

    if kind == 'relative_date':
        # Sólo vista derivada: RAW no se cambia. Valores >1000 años son extremos,
        # no fechas válidas para pendientes. Incluye vencimientos año 9999.
        bound = config.get('relative_date_abs_limit', 365000)
        extreme = obs & (np.abs(x) > bound)
        yield emit('fecha_extrema', flag(extreme, obs), 'fechas', f'abs(x) > {bound} días', unit='indicador', caution='Alerta de calidad, no causa de baja.')
        clean = np.where(extreme, np.nan, x)
        for k in lags:
            prev = panel.lag(clean, k)
            elapsed = panel.days - panel.lag(panel.days, k)
            adj = clean - prev - elapsed
            yield emit(f'lag{k}_limpio', prev, 'fechas', f'x(t-{k}) excluyendo extremos', k)
            yield emit(f'delta_evento_l{k}', adj, 'fechas', f'x(t)-x(t-{k})-[días foto(t)-días foto(t-{k})]', k, caution='Convención foto−evento; cero equivale a evento fijo, no a ausencia de actividad.')
            yield emit(f'cambio_evento_l{k}', flag(np.abs(adj) > 0.5, np.isfinite(adj)), 'fechas', f'abs(delta_evento_l{k}) > 0.5 días', k, unit='indicador')
        return

    if kind == 'clock':
        for k in lags:
            prev = panel.lag(x, k)
            yield emit(f'lag{k}', prev, 'relojes', f'x(t-{k})', k)
            yield emit(f'delta{k}', x-prev, 'relojes', f'x(t)-x(t-{k})', k, caution='Cambio de edad/antigüedad; no se interpreta como uso o apagado.')
            if v == 'cliente_antiguedad':
                yield emit(f'delta_ajustado{k}', x-prev-k, 'relojes', f'x(t)-x(t-{k})-{k} meses', k)
        return

    if kind == 'category':
        for k in lags:
            prev = panel.lag(x, k); ok = obs & np.isfinite(prev)
            yield emit(f'estado_lag{k}', prev, 'categoricas', f'código nominal observado en t-{k}', k, 'category', unit='código nominal')
            yield emit(f'cambio_l{k}', flag(x != prev, ok), 'categoricas', f'x(t) != x(t-{k}) con ambos observados', k, unit='indicador')
        streak = np.ones(panel.n); continuing = obs.copy()
        for k in range(1, maxk+1):
            prev = panel.lag(x, k); continuing &= np.isfinite(prev) & (prev == x)
            streak += continuing
        yield emit('racha_estado_observada', np.where(obs, streak, np.nan), 'categoricas', f'longitud consecutiva hacia atrás del código actual, máximo {maxk+1}', maxk, unit='meses', caution='Racha observada, censurada al inicio del archivo, hueco o NA; no duración total conocida.')
        for w in windows:
            a = np.vstack([panel.lag(x,k) for k in range(w)]); seen = np.isfinite(a); n = seen.sum(axis=0)
            same = ((a == x) & seen).sum(axis=0)
            pairs = seen[:-1] & seen[1:]
            changes = ((a[:-1] != a[1:]) & pairs).sum(axis=0)
            yield emit(f'nobs_w{w}', n, 'categoricas', f'número de códigos observados en {w} meses calendario', w-1, unit='meses')
            yield emit(f'prop_estado_actual_w{w}', safe_divide(same, n, obs), 'categoricas', f'fracción observada igual al código actual en {w} meses', w-1, unit='proporción')
            yield emit(f'cambios_w{w}', np.where(pairs.sum(axis=0)>0, changes, np.nan), 'categoricas', f'cambios entre pares adyacentes observados de {w} meses', w-1, unit='cambios')
            yield emit(f'pares_observados_w{w}', pairs.sum(axis=0), 'categoricas', f'pares mensuales con ambos códigos observados en ventana {w}', w-1, unit='pares')
        return

    if kind != 'numeric':
        raise ValueError(f'Tipo no soportado {kind}: {v}')
    for op, cond in [('cero',x == 0),('negativo',x < 0),('positivo',x > 0)]:
        yield emit(op, flag(cond,obs), 'estado_numerico', op+' con valor observado', unit='indicador', caution='Estado matemático; no equivale automáticamente a actividad voluntaria.')
    yield emit('signed_log1p', np.sign(x)*np.log1p(np.abs(x)), 'transformaciones', 'sign(x)*log(1+abs(x))', unit='escala transformada', caution='Transformación monótona; puede ser redundante para árboles.')
    rank = panel.rank(x)
    yield emit('rank_mes', rank, 'ranks', 'percentil con empates medios de observados en la foto completa', unit='percentil', caution='Requiere disponer del lote mensual de scoring completo; no utiliza target.')
    yield emit('rank_no_cero_mes', panel.rank(np.where(x!=0,x,np.nan)), 'ranks', 'percentil entre valores observados distintos de cero del mismo mes', unit='percentil')

    for k in lags:
        prev = panel.lag(x,k); delta = x-prev
        yield emit(f'lag{k}', prev, 'historia_numerica', f'x(t-{k}) exacto por calendario', k)
        yield emit(f'delta{k}', delta, 'historia_numerica', f'x(t)-x(t-{k})', k)
        den = np.abs(x)+np.abs(prev)
        sym = safe_divide(delta,den)
        sym = np.where(obs & np.isfinite(prev) & (den==0),0,sym)
        yield emit(f'delta_simetrico{k}', sym, 'historia_numerica', f'(x(t)-x(t-{k}))/(abs(x(t))+abs(x(t-{k}))); 0 si ambos cero', k, unit='cambio simétrico [-1,1]', caution='No es variación porcentual convencional.')
        yield emit(f'delta_rank{k}', rank-panel.lag(rank,k), 'ranks', f'rank_mes(t)-rank_mes(t-{k})', k, unit='diferencia percentiles', caution='Puede cambiar porque cambia la población de referencia.')
        if spec.get('history_mode') in {'nonnegative_flow','rolling_flow','count_stock'}:
            yield emit(f'cambio_relativo{k}', safe_divide(delta,prev,(prev>0)&(x>=0)), 'historia_numerica', f'(x(t)-x(t-{k}))/x(t-{k}), previo>0 y actual>=0', k, unit='proporción')

    prev = panel.lag(x,1); ok = obs & np.isfinite(prev)
    transitions = {
        'cero_a_cero': (prev==0)&(x==0),
        'no_cero_a_cero': (prev!=0)&(x==0),
        'cero_a_no_cero': (prev==0)&(x!=0),
        'paso_a_negativo': (prev>=0)&(x<0),
        'negativo_persistente': (prev<0)&(x<0),
        'salio_de_negativo': (prev<0)&(x>=0),
    }
    for op, val in transitions.items():
        yield emit(op, flag(val,ok), 'transiciones_numericas', f'{op}: t-1→t, ambos observados', 1, unit='indicador', caution='No-cero incluye negativos; no se etiqueta automáticamente como uso.')
    if maxk >= 2:
        yield emit('aceleracion2', x-2*prev+panel.lag(x,2), 'historia_numerica', 'x(t)-2*x(t-1)+x(t-2)', 2)

    recent = np.full(panel.n,np.nan); zero_run = np.zeros(panel.n); nonzero_run = np.zeros(panel.n)
    zcont = obs.copy(); nzcont = obs.copy()
    for k in range(maxk+1):
        a = panel.lag(x,k); ao = np.isfinite(a)
        recent = np.where(np.isnan(recent)&ao&(a!=0),k,recent)
        zcont &= ao & (a==0); nzcont &= ao & (a!=0)
        zero_run += zcont; nonzero_run += nzcont
    yield emit('meses_desde_no_cero_observado', recent, 'recencia', f'mínimo k con x(t-k) observado y distinto de cero, 0≤k≤{maxk}', maxk, unit='meses', caution='Recencia del último registro observado; un hueco no demuestra ausencia de eventos.')
    yield emit('racha_cero_observada', np.where(obs,zero_run,np.nan), 'recencia', f'ceros consecutivos desde t hacia atrás, máximo {maxk+1}; corta en NA/hueco', maxk, unit='meses')
    yield emit('racha_no_cero_observada', np.where(obs,nonzero_run,np.nan), 'recencia', f'no-ceros consecutivos desde t hacia atrás, máximo {maxk+1}; corta en NA/hueco', maxk, unit='meses')

    for w in windows:
        # Orden: pasado → presente. Cada posición es un mes exacto.
        a = np.vstack([panel.lag(x,k) for k in range(w-1,-1,-1)])
        seen = np.isfinite(a); n = seen.sum(axis=0); complete = n==w
        total = np.where(seen,a,0).sum(axis=0); mean = safe_divide(total,n)
        variance = safe_divide(np.where(seen,(a-mean)**2,0).sum(axis=0),n)
        mn = np.where(seen,a,np.inf).min(axis=0); mx = np.where(seen,a,-np.inf).max(axis=0)
        mn[n==0]=np.nan; mx[n==0]=np.nan
        pairs = seen[1:]&seen[:-1]; d=np.diff(a,axis=0); npairs=pairs.sum(axis=0)
        up=((d>0)&pairs).sum(axis=0); down=((d<0)&pairs).sum(axis=0)
        # No usar nansum como suma económica: con faltantes la suma queda NA.
        vals = {
            'nobs':(n,'número de valores observados','meses'),
            'media_obs':(mean,'media de observados; leer junto a nobs',spec.get('unit','--')),
            'std_obs':(np.where(n>=2,np.sqrt(variance),np.nan),'desvío poblacional entre observados, n>=2',spec.get('unit','--')),
            'min_obs':(mn,'mínimo observado',spec.get('unit','--')),
            'max_obs':(mx,'máximo observado',spec.get('unit','--')),
            'amplitud_obs':(np.where(n>=2,mx-mn,np.nan),'máximo-mínimo, n>=2',spec.get('unit','--')),
            'prop_cero_obs':(safe_divide(((a==0)&seen).sum(axis=0),n),'ceros/valores observados','proporción'),
            'prop_negativo_obs':(safe_divide(((a<0)&seen).sum(axis=0),n),'negativos/valores observados','proporción'),
            'pares_obs':(npairs,'pares de meses adyacentes con ambos valores observados','pares'),
            'subidas_obs':(np.where(npairs>0,up,np.nan),'pares observados con delta>0','pares'),
            'bajadas_obs':(np.where(npairs>0,down,np.nan),'pares observados con delta<0','pares'),
        }
        for op,(val,formula,unit) in vals.items():
            yield emit(f'{op}_w{w}',val,'ventanas',formula+f' en {w} meses calendario',w-1,unit=unit,caution='Ventana incluye t; los resúmenes parciales llevan nobs y pares_obs.')
        if spec.get('history_mode') in {'nonnegative_flow','signed_flow'}:
            yield emit(f'suma_completa_w{w}',np.where(complete,total,np.nan),'ventanas',f'suma de flujos mensuales sólo con {w} valores observados',w-1)
        tt=np.arange(w,dtype=float); tt-=tt.mean()
        slope=(np.where(seen,a,0)*tt[:,None]).sum(axis=0)/(tt@tt)
        yield emit(f'pendiente_completa_w{w}',np.where(complete,slope,np.nan),'tendencias',f'pendiente OLS vs mes; requiere los {w} meses observados',w-1,unit=spec.get('unit','--')+'/mes',caution='Ventanas móviles de RAW se superponen; pendiente no prueba causa ni salida abrupta.')
        yield emit(f'decreciente_completo_w{w}',flag((down>0)&(up==0),complete),'tendencias',f'ningún aumento y alguna disminución en {w} meses completos',w-1,unit='indicador')
        yield emit(f'creciente_completo_w{w}',flag((up>0)&(down==0),complete),'tendencias',f'ninguna disminución y algún aumento en {w} meses completos',w-1,unit='indicador')
        yield emit(f'alternancia_completa_w{w}',flag((up>0)&(down>0),complete),'tendencias',f'al menos una subida y una bajada en {w} meses completos',w-1,unit='indicador')
