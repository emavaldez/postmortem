"""
03_feature_engineering.py
DMEyF 2026 - Primera Competencia - Experimento 3001

Genera tres datasets con lags y deltas, que solo difieren en como se tratan
las variables en pesos (montos):

  ds3001_crudo.parquet    montos tal cual vienen
  ds3001_mediana.parquet  cada monto dividido por la mediana de esa variable en su mes
                          (corrige inflacion y aguinaldo, variable por variable)
  ds3001_rank.parquet     cada monto reemplazado por su posicion relativa dentro del mes:
                          positivos entre 0 y 1, negativos entre -1 y 0, el cero queda en cero

Despues de corregir los montos se calculan, para TODAS las variables:
  lag k   = valor del mismo cliente k meses antes   (vacio si ese mes no existe)
  delta k = valor actual - lag k

Uso:  python 03_feature_engineering.py   (despues de 01_preparar_dataset.py)
"""

print("Arrancando 03_feature_engineering.py ...", flush=True)

import gc
import re
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
    "experimento": 3001,
    "nombre": "fe_lags_deltas",
    "descripcion": "Lags y deltas 1 y 2 sobre todas las variables, con tres tratamientos "
                   "de montos: crudo, dividido por mediana del mes, rank dentro del mes.",
    "dataset_entrada": "ds1001_base.parquet",
    "versiones": ["crudo", "mediana", "rank"],   # se puede correr una sola, ej. ["rank"]
    "lags": [1, 2],
    "deltas": [1, 2],
    # variables en pesos: empiezan con m, Master_m o Visa_m (convencion del diccionario)
    "regex_montos": r"^(m|Master_m|Visa_m)",
}

exp = iniciar_experimento(PARAM)

COLS_NO_FEATURE = ["numero_de_cliente", "foto_mes",
                   "clase_ternaria", "clase_binaria1", "clase_binaria2"]

# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------
t0 = time.time()
base = pd.read_parquet(DIR_DATA / PARAM["dataset_entrada"])
print(f"Leido {PARAM['dataset_entrada']}: {len(base):,} filas x {base.shape[1]} columnas "
      f"({time.time() - t0:.1f} s)")

# orden por cliente y mes: necesario para los lags
base = base.sort_values(["numero_de_cliente", "foto_mes"], kind="mergesort").reset_index(drop=True)

features = [c for c in base.columns if c not in COLS_NO_FEATURE]
no_numericas = [c for c in features if not pd.api.types.is_numeric_dtype(base[c])]
if no_numericas:
    raise ValueError(f"Hay variables no numericas, revisar: {no_numericas}")

# float32 para que entre en memoria (la mitad que float64, sin perder nada relevante para arboles)
for c in features:
    base[c] = base[c].astype("float32")

montos = [c for c in features if re.match(PARAM["regex_montos"], c)]
print(f"Variables: {len(features)} en total, {len(montos)} son montos en pesos.")
pd.Series(montos, name="variable_monto").to_csv(exp.ruta("variables_monto"), index=False)

mes = base["foto_mes"].to_numpy()
cliente = base["numero_de_cliente"].to_numpy()
periodo = (mes // 100) * 12 + mes % 100
n = len(base)

# para cada k: True si la fila k posiciones arriba es el MISMO cliente exactamente k meses antes
fila_valida = {}
for k in sorted(set(PARAM["lags"]) | set(PARAM["deltas"])):
    ok = np.zeros(n, dtype=bool)
    ok[k:] = (cliente[k:] == cliente[:-k]) & (periodo[k:] - periodo[:-k] == k)
    fila_valida[k] = ok


# ---------------------------------------------------------------------------
# Tratamientos de montos
# ---------------------------------------------------------------------------
def por_mediana(s):
    """Divide por la mediana de |valor| (sin ceros) de esa variable en el mismo mes."""
    ref = s.abs().where(s != 0).groupby(mes).transform("median")
    out = s / ref
    return out.where(ref.notna() & (ref != 0), s).astype("float32")


def por_rank(s):
    """Positivos -> (0,1], negativos -> [-1,0), cero -> 0, vacio -> vacio. Dentro de cada mes."""
    out = pd.Series(np.where(s.notna(), 0.0, np.nan), index=s.index, dtype="float64")
    pos, neg = s > 0, s < 0
    if pos.any():
        out[pos] = s[pos].groupby(mes[pos.to_numpy()]).rank(pct=True)
    if neg.any():
        out[neg] = -(-s[neg]).groupby(mes[neg.to_numpy()]).rank(pct=True)
    return out.astype("float32")


TRATAMIENTO = {"crudo": None, "mediana": por_mediana, "rank": por_rank}


# ---------------------------------------------------------------------------
# Generacion de cada version
# ---------------------------------------------------------------------------
def lag_de(x, k):
    out = np.full(n, np.nan, dtype="float32")
    out[k:] = x[:-k]
    out[~fila_valida[k]] = np.nan
    return out


resultados = {}
for version in PARAM["versiones"]:
    t0 = time.time()
    print(f"\n--- Version '{version}' ---")
    df = base.copy()

    if TRATAMIENTO[version] is not None:
        for c in montos:
            df[c] = TRATAMIENTO[version](df[c])
        print(f"  montos corregidos ({time.time() - t0:.0f} s)")

    nuevas = {}
    for c in features:
        x = df[c].to_numpy(dtype="float32")
        lags_c = {k: lag_de(x, k) for k in fila_valida}
        for k in PARAM["lags"]:
            nuevas[f"{c}_lag{k}"] = lags_c[k]
        for k in PARAM["deltas"]:
            nuevas[f"{c}_delta{k}"] = x - lags_c[k]
    n_cols = df.shape[1] + len(nuevas)
    print(f"  lags y deltas listos: {n_cols} columnas ({time.time() - t0:.0f} s)")

    # control: en una muestra de filas, el lag1 tiene que ser el valor del mes anterior
    var_ctrl = "mcuentas_saldo" if "mcuentas_saldo" in features else features[0]
    if 1 in PARAM["lags"]:
        rng = np.random.default_rng(1)
        idx = rng.choice(n, size=min(2000, n), replace=False)
        ref = pd.Series(df[var_ctrl].to_numpy(), index=pd.MultiIndex.from_arrays([cliente, mes]))
        mes_ant = np.where(mes[idx] % 100 == 1, mes[idx] - 89, mes[idx] - 1)   # 202201 -> 202112
        esperado = ref.reindex(list(zip(cliente[idx], mes_ant))).to_numpy()
        obtenido = nuevas[f"{var_ctrl}_lag1"][idx]
        assert np.allclose(esperado, obtenido, equal_nan=True), \
            f"El lag1 de {var_ctrl} no coincide con el mes anterior"
        print(f"  OK: lag1 de {var_ctrl} verificado contra el mes anterior en {len(idx):,} filas")

    # grabado directo con pyarrow: evita armar una copia gigante en memoria
    tabla = pa.Table.from_pandas(df, preserve_index=False)
    for nombre, arr in nuevas.items():
        tabla = tabla.append_column(nombre, pa.array(arr, from_pandas=True))
    archivo = DIR_DATA / f"ds{exp.id}_{version}.parquet"
    pq.write_table(tabla, archivo, compression="zstd")
    del tabla
    mb = archivo.stat().st_size / 1e6
    print(f"  Grabado {archivo.name}: {n:,} filas x {n_cols} columnas, {mb:.0f} MB "
          f"({time.time() - t0:.0f} s)")

    if version == PARAM["versiones"][0] and PARAM["lags"]:
        # que % de filas tiene lag disponible en cada mes (los primeros meses no tienen historia)
        cobertura = pd.DataFrame({f"lag{k}": pd.Series(~np.isnan(nuevas[f"{var_ctrl}_lag{k}"]))
                                  for k in PARAM["lags"]}).groupby(mes).mean().mul(100).round(1)
        cobertura.index.name = "foto_mes"
        print(f"\n  % de filas con lag disponible ({var_ctrl}), por mes:")
        print(cobertura.to_string())
        cobertura.to_csv(exp.ruta("cobertura_lags"))

    resultados[version] = {"archivo": archivo.name, "columnas": n_cols, "MB": round(mb)}
    del df, nuevas
    gc.collect()

cerrar_experimento(exp, {"datasets": resultados, "variables": len(features), "montos": len(montos)})
