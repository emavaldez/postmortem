"""Primitivas del panel: sólo calendario actual/pasado, sin consultar el target."""
from __future__ import annotations
import numpy as np
import pandas as pd

KEYS = ['numero_de_cliente', 'foto_mes']
FORBIDDEN = {'numero_de_cliente', 'foto_mes', 'clase_ternaria', 'clase_binaria'}

class Panel:
    def __init__(self, df, config=None):
        self.config = config or {}
        if not set(KEYS).issubset(df):
            raise ValueError('Faltan claves numero_de_cliente/foto_mes')
        if df[KEYS].isna().any().any() or df.duplicated(KEYS).any():
            raise ValueError('Claves nulas o cliente-mes duplicado')
        fm = pd.to_numeric(df.foto_mes, errors='raise').to_numpy(float)
        if not np.isfinite(fm).all() or not np.equal(fm, np.floor(fm)).all():
            raise ValueError('foto_mes debe ser un entero YYYYMM')
        if not (((fm % 100) >= 1) & ((fm % 100) <= 12)).all():
            raise ValueError('Mes inválido')
        self.df = df.sort_values(KEYS, kind='stable').reset_index(drop=True)
        self.n = len(self.df)
        self.columns = set(self.df.columns)
        self.month = self.df.foto_mes.to_numpy(dtype=np.int64)
        self.month_index = (self.month // 100) * 12 + self.month % 100 - 1
        # Convención del EDA: fecha de foto = fin del mes.
        dates = pd.to_datetime(self.df.foto_mes.astype(str), format='%Y%m') + pd.offsets.MonthEnd(0)
        self.days = dates.to_numpy(dtype='datetime64[D]').astype(np.int64)
        self.index = pd.MultiIndex.from_arrays([self.df.numero_de_cliente, self.month_index])
        self._indices = {}
        self._month_groups = [np.flatnonzero(self.month == m) for m in np.unique(self.month)]

    def get(self, name):
        x = pd.to_numeric(self.df[name], errors='raise').to_numpy(dtype=np.float64, na_value=np.nan)
        if np.isinf(x).any():
            x = x.copy(); x[np.isinf(x)] = np.nan
        return x

    def lag_index(self, k):
        if not isinstance(k, (int, np.integer)) or k < 0:
            raise ValueError('lag debe ser entero no negativo')
        if k == 0:
            return np.arange(self.n)
        if k not in self._indices:
            previous = pd.MultiIndex.from_arrays([self.df.numero_de_cliente, self.month_index - k])
            self._indices[k] = self.index.get_indexer(previous)
        return self._indices[k]

    def lag(self, values, k):
        values = np.asarray(values, dtype=float)
        if values.shape != (self.n,):
            raise ValueError('Vector no alineado con panel')
        idx = self.lag_index(k)
        result = np.full(self.n, np.nan)
        valid = idx >= 0
        result[valid] = values[idx[valid]]
        return result

    def row_present(self, k):
        return self.lag_index(k) >= 0

    def rank(self, values):
        """Percentil [0,1] por foto completa, empates medios; no mira otros meses."""
        values = np.asarray(values, dtype=float)
        out = np.full(self.n, np.nan)
        for idx in self._month_groups:
            ok = np.isfinite(values[idx]); n = int(ok.sum())
            if not n:
                continue
            ranks = pd.Series(values[idx][ok]).rank(method='average').to_numpy()
            out[idx[ok]] = (ranks - 1) / (n - 1) if n > 1 else 0.0
        return out

def flag(condition, valid):
    return np.where(valid, np.asarray(condition, bool).astype(float), np.nan)

def safe_divide(num, den, valid=None):
    num, den = np.asarray(num, float), np.asarray(den, float)
    ok = np.isfinite(num) & np.isfinite(den) & (den != 0)
    if valid is not None:
        ok &= valid
    out = np.full(np.broadcast_shapes(num.shape, den.shape), np.nan)
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        np.divide(num, den, out=out, where=ok)
    out[~np.isfinite(out)] = np.nan
    return out

def generate_coverage(panel, config):
    lags = config['lags']; windows = config['windows']
    def item(op, value, formula, history=0):
        return 'fe__panel__' + op, np.asarray(value, float), dict(block='cobertura_panel', sources=[], formula=formula, interpretation='Disponibilidad de filas; nunca se usa ausencia futura.', min_history=history, unit='meses/indicador', caution='No mide actividad; las fronteras del archivo censuran la historia.', feature_kind='numeric')
    for k in lags:
        yield item(f'fila_lag{k}', panel.row_present(k), f'existe fila del mismo cliente en t-{k}', k)
    for w in windows:
        nrows = sum(panel.row_present(k).astype(float) for k in range(w))
        yield item(f'filas_w{w}', nrows, f'filas presentes en [t-{w-1},t]', w-1)
        yield item(f'completo_w{w}', nrows == w, f'filas_w{w} == {w}', w-1)
