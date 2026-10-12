"""
03b_fe_rank_total.py
DMEyF 2026 - Primera Competencia - Experimento 3002

Feature engineering con la receta del profesor:
  1. Lags y deltas de orden 1 y 2 sobre los valores CRUDOS de todas las variables
     (vacio si el cliente no estaba exactamente k meses antes; los NA se mantienen).
  2. Despues, TODAS las columnas (originales, lags y deltas) se reemplazan por su ranking
     dentro de cada mes, con el cero fijo:
        positivos -> (0, 1]     negativos -> [-1, 0)     cero -> 0     NA -> NA
     Es un percentil: equiespaciado, no conserva distancias. Corrige inflacion y aguinaldo.
  No se rankean numero_de_cliente, foto_mes ni las clases.

Uso:  py -3.12 03b_fe_rank_total.py   (despues de 01_preparar_dataset.py)
"""

print("Arrancando 03b_fe_rank_total.py ...", flush=True)

import gc
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from exp_utils import DIR_DATA, cerrar_experimento, iniciar_experimento

# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 3002,
    "nombre": "fe_lag2_rank_total",
    "descripcion": "Lags y deltas 1 y 2 sobre valores crudos; despues todas las columnas rankeadas "
                   "dentro de cada mes con cero fijo (positivos 0..1, negativos -1..0, NA se mantiene).",
    "dataset_entrada": "ds1001_base.parquet",
    "dataset_salida": "ds3002_rank_total.parquet",
    "lags": [1, 2],
    "deltas": [1, 2],
}

exp = iniciar_experimento(PARAM)
NO_FEATURES = ["numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"]

# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------
t0 = time.time()
base = pd.read_parquet(DIR_DATA / PARAM["dataset_entrada"])
base = base.sort_values(["numero_de_cliente", "foto_mes"], kind="mergesort").reset_index(drop=True)
features = [c for c in base.columns if c not in NO_FEATURES]
no_numericas = [c for c in features if not pd.api.types.is_numeric_dtype(base[c])]
if no_numericas:
    raise ValueError(f"Hay variables no numericas, revisar: {no_numericas}")
print(f"Leido {PARAM['dataset_entrada']}: {len(base):,} filas, {len(features)} variables ({time.time() - t0:.0f} s)")

n = len(base)
mes = base["foto_mes"].to_numpy()
cliente = base["numero_de_cliente"].to_numpy()
periodo = (mes // 100) * 12 + mes % 100
meses = sorted(int(m) for m in np.unique(mes))
idx_mes = {m: np.flatnonzero(mes == m) for m in meses}

# fila k posiciones arriba = mismo cliente exactamente k meses antes
fila_valida = {}
for k in sorted(set(PARAM["lags"]) | set(PARAM["deltas"])):
    ok = np.zeros(n, dtype=bool)
    ok[k:] = (cliente[k:] == cliente[:-k]) & (periodo[k:] - periodo[:-k] == k)
    fila_valida[k] = ok


def lag_de(x, k):
    out = np.full(n, np.nan, dtype="float32")
    out[k:] = x[:-k]
    out[~fila_valida[k]] = np.nan
    return out


def rank_cero_fijo(x):
    """Dentro de cada mes: positivos (0,1], negativos [-1,0), cero 0, NA NA."""
    out = np.full(n, np.nan, dtype="float32")
    for m, idx in idx_mes.items():
        v = x[idx]
        r = np.where(np.isnan(v), np.nan, 0.0)
        pos, neg = v > 0, v < 0
        if pos.any():
            r[pos] = pd.Series(v[pos]).rank(method="average", pct=True).to_numpy()
        if neg.any():
            r[neg] = -pd.Series(-v[neg]).rank(method="average", pct=True).to_numpy()
        out[idx] = r
    return out


# ---------------------------------------------------------------------------
# 1) lags y deltas sobre crudos  2) ranking de todo
# ---------------------------------------------------------------------------
t0 = time.time()
columnas = {}
ejemplo = "mpayroll" if "mpayroll" in features else features[0]
comparacion = {}
for i, c in enumerate(features, start=1):
    x = base[c].to_numpy(dtype="float32")
    crudas = {c: x}
    lags = {k: lag_de(x, k) for k in fila_valida}
    for k in PARAM["lags"]:
        crudas[f"{c}_lag{k}"] = lags[k]
    for k in PARAM["deltas"]:
        crudas[f"{c}_delta{k}"] = x - lags[k]
    for nombre, valores in crudas.items():
        rk = rank_cero_fijo(valores)
        # controles: NA, ceros y signos se conservan; todo en [-1, 1]
        assert np.array_equal(np.isnan(rk), np.isnan(valores)), f"Cambiaron los NA en {nombre}"
        assert np.array_equal(rk == 0, valores == 0), f"Cambiaron los ceros en {nombre}"
        assert np.nanmin(rk, initial=0) >= -1 and np.nanmax(rk, initial=0) <= 1, f"Fuera de rango en {nombre}"
        columnas[nombre] = rk
    if c == ejemplo:
        for m in meses:
            v, r = x[idx_mes[m]], columnas[c][idx_mes[m]]
            comparacion[m] = {"mediana_cruda_positivos": float(np.nanmedian(v[v > 0])) if (v > 0).any() else np.nan,
                              "mediana_rank_positivos": float(np.nanmedian(r[r > 0])) if (r > 0).any() else np.nan}
    if i % 25 == 0 or i == len(features):
        print(f"  {i}/{len(features)} variables ({time.time() - t0:.0f} s)", flush=True)

comp = pd.DataFrame(comparacion).T
comp.index.name = "foto_mes"
comp.to_csv(exp.ruta(f"efecto_rank_{ejemplo}"))
print(f"\nEfecto del ranking sobre {ejemplo} (mediana de los positivos por mes):")
print(comp.round(3).to_string())
print("Lectura: la mediana cruda salta en junio (aguinaldo); la rankeada queda fija cerca de 0,5.")

# ---------------------------------------------------------------------------
# Grabado
# ---------------------------------------------------------------------------
t0 = time.time()
tabla = pa.Table.from_pandas(base[NO_FEATURES], preserve_index=False)
for nombre, arr in columnas.items():
    tabla = tabla.append_column(nombre, pa.array(arr, from_pandas=True))
archivo = DIR_DATA / PARAM["dataset_salida"]
pq.write_table(tabla, archivo, compression="zstd")
n_cols = tabla.num_columns
del tabla, columnas
gc.collect()
mb = archivo.stat().st_size / 1e6
print(f"\nGrabado {archivo.name}: {n:,} filas x {n_cols} columnas ({len(features)} x 5 + id/mes/clases), "
      f"{mb:,.0f} MB ({time.time() - t0:.0f} s)")

cerrar_experimento(exp, {"archivo": archivo.name, "columnas": n_cols, "MB": round(mb),
                         "variables_originales": len(features)})
