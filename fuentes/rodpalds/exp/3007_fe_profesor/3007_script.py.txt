"""
03f_fe_profesor.py
DMEyF 2026 - Primera Competencia - Experimento 3007

Dataset con TODAS las indicaciones de Feature Engineering del profesor, sobre la base de ds3003
(receta + proceso de muerte, la mejor hasta ahora):

  1.1 Data Quality: ccajas_depositos esta rota en 202105 (todos ceros) -> NA solo en 202105.
      Se arregla ANTES de todo, asi los lags/deltas/tendencias de junio y julio tampoco la usan.
  1.3 Intra mes: para cada variable original que alguna vez vale cero, un FLAG <var>_zero:
      1 si vale cero, NA si era NA, 0 en el resto. Las _zero NO se rankean.
  1.4 Historico: lags y deltas de orden 1 y 2 (como 03b/03c) y, del codigo del profesor
      (TendenciaYmuchomas con ventana 3, tendencia y promedio):
        <var>_tend3  pendiente de la recta de cuadrados minimos sobre el mes actual y los 2
                     anteriores (x = 1, 2, 3; los NA se saltean; NA si hay menos de 2 valores)
        <var>_avg3   promedio de esos valores (NA si hay menos de 2, igual que fhistC)
      Sobre los valores CRUDOS y despues rankeadas como el resto.
  Ranking de todo lo demas dentro de cada mes con cero fijo (positivos (0,1], negativos [-1,0),
  cero 0, NA NA), como 03b/03c. Las 6 variables del proceso de muerte se mantienen (03c).

Diferencia con el codigo del profesor: fhistC arma la ventana por FILAS del cliente; aca se usan
los meses calendario (lag de exactamente 1 y 2 meses). Solo difiere si el cliente tiene huecos.

Se procesa y graba MES POR MES (un row group por mes) para no tener las ~1.200 columnas de todo
el dataset en memoria a la vez.

Uso:  py -3.12 03f_fe_profesor.py
"""

print("Arrancando 03f_fe_profesor.py ...", flush=True)

import gc
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from exp_utils import DIR_DATA, cerrar_experimento, iniciar_experimento

PARAM = {
    "experimento": 3007,
    "nombre": "fe_profesor",
    "descripcion": "ds3003 (lags/deltas 1 y 2 + rank cero fijo + proceso de muerte) mas indicaciones del profesor: "
                   "ccajas_depositos NA en 202105, flags _zero (sin rankear), tendencia y promedio de 3 meses (_tend3, _avg3).",
    "dataset_entrada": "ds1001_base.parquet",
    "dataset_salida": "ds3007_profesor.parquet",
    "rotas": {"ccajas_depositos": [202105]},
    "claves": ["ctrx_quarter", "mpasivos_margen", "mcaja_ahorro", "mcuentas_saldo",
               "ctarjeta_visa_transacciones", "ctarjeta_master_transacciones",
               "ctarjeta_debito_transacciones", "mprestamos_personales", "mpayroll",
               "cmobile_app_trx", "chomebanking_transacciones", "mcomisiones",
               "cdescubierto_preacordado", "mcuenta_corriente", "Visa_msaldototal",
               "Master_msaldototal"],
    "relativas_max3": ["ctrx_quarter", "mcaja_ahorro"],
}

exp = iniciar_experimento(PARAM)
NO_FEATURES = ["numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"]

# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------
t0 = time.time()
base = pd.read_parquet(DIR_DATA / PARAM["dataset_entrada"])
base = base.sort_values(["numero_de_cliente", "foto_mes"], kind="mergesort").reset_index(drop=True)
assert not base.duplicated(["numero_de_cliente", "foto_mes"]).any(), "Hay cliente-mes repetidos"
features = [c for c in base.columns if c not in NO_FEATURES]
no_numericas = [c for c in features if not pd.api.types.is_numeric_dtype(base[c])]
if no_numericas:
    raise ValueError(f"Hay variables no numericas, revisar: {no_numericas}")
n = len(base)
mes = base["foto_mes"].to_numpy()
cliente = base["numero_de_cliente"].to_numpy()
periodo = (mes // 100) * 12 + mes % 100
meses = sorted(int(m) for m in np.unique(mes))
idx_mes = {m: np.flatnonzero(mes == m) for m in meses}
print(f"Leido {PARAM['dataset_entrada']}: {n:,} filas, {len(features)} variables, meses {meses} ({time.time() - t0:.0f} s)")

X = {c: base[c].to_numpy(dtype="float32").copy() for c in features}
base = base[NO_FEATURES]           # libera memoria: las variables ya estan en X
gc.collect()

# ---------------------------------------------------------------------------
# 1.1 Data Quality
# ---------------------------------------------------------------------------
calidad = []
for var, meses_rotos in PARAM["rotas"].items():
    assert var in X, f"No existe la variable {var}"
    for m in meses_rotos:
        idx = idx_mes[m]
        v = X[var][idx]
        pct_cero = float(np.mean(v[~np.isnan(v)] == 0)) * 100 if (~np.isnan(v)).any() else np.nan
        calidad.append({"variable": var, "foto_mes": m, "pct_cero_antes": round(pct_cero, 2),
                        "pct_na_antes": round(float(np.isnan(v).mean()) * 100, 2)})
        print(f"1.1 {var} en {m}: {pct_cero:.2f}% ceros antes del arreglo -> se pone NA")
        if pct_cero < 99:
            print(f"   AVISO: el profesor dijo que eran TODOS ceros y aca hay {pct_cero:.2f}%; se pone NA igual.")
        X[var][idx] = np.nan
pd.DataFrame(calidad).to_csv(exp.ruta("data_quality"), index=False)

# ---------------------------------------------------------------------------
# Herramientas
# ---------------------------------------------------------------------------
fila_valida = {}
for k in (1, 2):
    ok = np.zeros(n, dtype=bool)
    ok[k:] = (cliente[k:] == cliente[:-k]) & (periodo[k:] - periodo[:-k] == k)
    fila_valida[k] = ok


def lag_de(x, k):
    out = np.full(n, np.nan, dtype="float32")
    out[k:] = x[:-k]
    out[~fila_valida[k]] = np.nan
    return out


def rank_cero_fijo(v):
    """Un solo mes: positivos (0,1], negativos [-1,0), cero 0, NA NA."""
    r = np.where(np.isnan(v), np.nan, 0.0)
    pos, neg = v > 0, v < 0
    if pos.any():
        r[pos] = pd.Series(v[pos]).rank(method="average", pct=True).to_numpy()
    if neg.any():
        r[neg] = -pd.Series(-v[neg]).rank(method="average", pct=True).to_numpy()
    return r.astype("float32")


def controlar_rank(nombre, valores, rk):
    assert np.array_equal(np.isnan(rk), np.isnan(valores)), f"Cambiaron los NA en {nombre}"
    assert np.array_equal(rk == 0, valores == 0), f"Cambiaron los ceros en {nombre}"
    assert np.array_equal(rk > 0, valores > 0), f"Cambio el signo en {nombre}"


def tend_avg3(x, l1, l2):
    """fhistC del profesor con ventana 3: x = 1 (hace 2 meses), 2 (hace 1), 3 (actual); salta NA."""
    ys = np.stack([l2, l1, x]).astype("float64")
    xs = np.array([1.0, 2.0, 3.0])[:, None] * np.ones_like(ys)
    ok = ~np.isnan(ys)
    cnt = ok.sum(axis=0)
    ys0 = np.where(ok, ys, 0.0)
    xs0 = np.where(ok, xs, 0.0)
    sx, sy = xs0.sum(axis=0), ys0.sum(axis=0)
    sxy, sxx = (xs0 * ys0).sum(axis=0), (xs0 * xs0).sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        pend = (cnt * sxy - sx * sy) / (cnt * sxx - sx * sx)
        prom = sy / cnt
    pend[cnt < 2] = np.nan
    prom[cnt < 2] = np.nan
    pend[np.abs(pend) < 1e-9 * (1 + np.abs(prom))] = 0.0      # ruido de redondeo -> 0 exacto
    return pend.astype("float32"), prom.astype("float32")


# control de tend_avg3 contra la formula directa
_x = np.array([3, np.nan, 5, 1], dtype="float32")
_l1 = np.array([2, 4, np.nan, np.nan], dtype="float32")
_l2 = np.array([1, 2, 1, np.nan], dtype="float32")
_p, _a = tend_avg3(_x, _l1, _l2)
assert np.allclose(_p[:3], [1.0, 2.0, 2.0]) and np.isnan(_p[3]), _p
assert np.allclose(_a[:3], [2.0, 3.0, 3.0]) and np.isnan(_a[3]), _a

# ---------------------------------------------------------------------------
# Variables historicas (crudas, sobre todo el dataset) que no son por variable
# ---------------------------------------------------------------------------
claves = [c for c in PARAM["claves"] if c in X]
n_apagados = np.zeros(n, dtype="float32")
n_dejo = np.zeros(n, dtype="float32")
for c in claves:
    x = X[c]
    apagado = np.isnan(x) | (x == 0)
    l1, l2 = lag_de(x, 1), lag_de(x, 2)
    n_apagados += apagado
    n_dejo += apagado & ((~np.isnan(l1) & (l1 != 0)) | (~np.isnan(l2) & (l2 != 0)))
n_dejo[~fila_valida[1] & ~fila_valida[2]] = np.nan
muerte = {"n_apagados": n_apagados,
          "n_apagados_delta1": n_apagados - lag_de(n_apagados, 1),
          "n_apagados_delta2": n_apagados - lag_de(n_apagados, 2),
          "n_dejo_de_usar": n_dejo}
for c in PARAM["relativas_max3"]:
    x = X[c]
    maximo = np.fmax(np.fmax(x, lag_de(x, 1)), lag_de(x, 2))
    with np.errstate(divide="ignore", invalid="ignore"):
        muerte[f"{c}_rel_max3"] = np.where(maximo > 0, x / maximo, np.nan).astype("float32")

# variables con algun cero (en cualquier mes, despues del arreglo 1.1)
con_cero = [c for c in features if (X[c] == 0).any()]
print(f"1.3 flags _zero para {len(con_cero)} de {len(features)} variables")

# lags de todo el dataset (crudos) una sola vez
L1 = {c: lag_de(X[c], 1) for c in features}
L2 = {c: lag_de(X[c], 2) for c in features}
gc.collect()

# ---------------------------------------------------------------------------
# Mes por mes: armar, rankear, grabar
# ---------------------------------------------------------------------------
archivo = DIR_DATA / PARAM["dataset_salida"]
writer = None
nombres_ref = None
resumen = []
t0 = time.time()
for m in meses:
    idx = idx_mes[m]
    cols = {}
    for c in features:
        x, l1, l2 = X[c][idx], L1[c][idx], L2[c][idx]
        t3, a3 = tend_avg3(x, l1, l2)
        crudas = {c: x, f"{c}_lag1": l1, f"{c}_lag2": l2, f"{c}_delta1": x - l1, f"{c}_delta2": x - l2,
                  f"{c}_tend3": t3, f"{c}_avg3": a3}
        for nombre, v in crudas.items():
            rk = rank_cero_fijo(v)
            controlar_rank(nombre, v, rk)
            cols[nombre] = rk
    for nombre, v in muerte.items():
        rk = rank_cero_fijo(v[idx])
        controlar_rank(nombre, v[idx], rk)
        cols[nombre] = rk
    for c in con_cero:                                   # 1.3: sin rankear
        x = X[c][idx]
        cols[f"{c}_zero"] = np.where(np.isnan(x), np.nan, (x == 0).astype("float32")).astype("float32")

    if nombres_ref is None:
        nombres_ref = list(cols)
    assert list(cols) == nombres_ref, "Las columnas cambiaron entre meses"
    tabla = pa.Table.from_pandas(base.iloc[idx][NO_FEATURES].reset_index(drop=True), preserve_index=False)
    for nombre in nombres_ref:
        tabla = tabla.append_column(nombre, pa.array(cols.pop(nombre), type=pa.float32(), from_pandas=True))
    if writer is None:
        writer = pq.ParquetWriter(archivo, tabla.schema, compression="zstd")
        esquema = tabla.schema
    writer.write_table(tabla.cast(esquema))
    resumen.append({"foto_mes": m, "filas": len(idx),
                    "pct_na_lag2": round(float(np.isnan(L2[features[0]][idx]).mean()) * 100, 1)})
    print(f"  {m}: {len(idx):,} filas x {tabla.num_columns} columnas grabadas ({time.time() - t0:.0f} s)", flush=True)
    del tabla, cols
    gc.collect()
writer.close()

# ---------------------------------------------------------------------------
# Controles del archivo grabado
# ---------------------------------------------------------------------------
pf = pq.ParquetFile(archivo)
n_cols = len(pf.schema_arrow.names)
esperadas = len(NO_FEATURES) + len(features) * 7 + len(muerte) + len(con_cero)
assert pf.metadata.num_rows == n, "Cambio la cantidad de filas al grabar"
assert n_cols == esperadas, f"Columnas {n_cols} != esperadas {esperadas}"
chk = pd.read_parquet(archivo, columns=["foto_mes", "ccajas_depositos", "ccajas_depositos_lag1"],
                      filters=[("foto_mes", "in", [202105, 202106])])
assert chk.loc[chk.foto_mes == 202105, "ccajas_depositos"].isna().all(), "ccajas_depositos 202105 deberia ser NA"
assert chk.loc[chk.foto_mes == 202106, "ccajas_depositos_lag1"].isna().all(), "el lag1 de junio deberia ser NA"
pd.DataFrame(resumen).to_csv(exp.ruta("resumen_por_mes"), index=False)
mb = archivo.stat().st_size / 1e6
print(f"\nGrabado {archivo.name}: {n:,} filas x {n_cols} columnas = {len(features)} x 7 (original, lag1, lag2, "
      f"delta1, delta2, tend3, avg3) + {len(muerte)} proceso de muerte + {len(con_cero)} _zero + id/mes/clases; "
      f"{mb:,.0f} MB")
cerrar_experimento(exp, {"archivo": archivo.name, "columnas": n_cols, "MB": round(mb),
                         "variables_originales": len(features), "flags_zero": len(con_cero)})
