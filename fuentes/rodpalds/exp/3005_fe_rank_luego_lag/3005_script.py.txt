"""
03d_fe_variantes.py
DMEyF 2026 - Primera Competencia - Experimentos 3004 / 3005

Variantes de la receta del profesor + "proceso de muerte", para responder dos dudas de
interpretacion que 03b/03c resolvieron de UNA sola manera:

  1) ORDEN lags/ranking  ("orden")
     "lag_luego_rank"  (como 03b/03c): lag y delta sobre valores CRUDOS, despues todo se rankea
                       dentro del mes. El delta1 de junio = (junio - mayo) en pesos, rankeado.
     "rank_luego_lag"  (alternativa): primero se rankea cada variable dentro de SU mes, despues
                       lag y delta de ese ranking. El lag1 de junio = la posicion que tenia el
                       cliente en mayo, entre los clientes de mayo; delta1 = cambio de posicion
                       (en [-2, 2]). No se vuelve a rankear: ya es comparable entre meses.

  2) COMO medir el proceso de muerte  ("extras")
     "conteo"  (como 03c, 6 variables): n_apagados, n_apagados_delta1/2, n_dejo_de_usar,
               ctrx_quarter_rel_max3, mcaja_ahorro_rel_max3.
     "flags"   (alternativa, 22 variables): las 6 anteriores + un indicador POR PRODUCTO
               dejo_<variable> = 1 si estaba activo hace 1 o 2 meses y hoy esta en 0/NA
               (NA si no hay historia). El arbol ve QUE producto se apago, no solo cuantos.
     "rankear_extras": si las variables nuevas se rankean por mes (como 03c) o quedan en su
               escala natural (conteos 0-16, indicadores 0/1, cocientes 0-1: no tienen inflacion).

Las variables clave son las mismas 16 de 03c para que la comparacion sea limpia.
"Apagado" = 0 o NA.  "Activo" = distinto de 0 y no NA.

Uso:  py -3.12 03d_fe_variantes.py configs\\3004_fe_flags.json
      py -3.12 03d_fe_variantes.py configs\\3005_fe_rank_luego_lag.json
"""

print("Arrancando 03d_fe_variantes.py ...", flush=True)

import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from exp_utils import DIR_DATA, cerrar_experimento, iniciar_experimento

# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 3004,
    "nombre": "fe_flags",
    "descripcion": "Receta (lag luego rank) + proceso de muerte con un indicador por producto, sin rankear las nuevas.",
    "dataset_entrada": "ds1001_base.parquet",
    "dataset_salida": "ds3004_flags.parquet",
    "orden": "lag_luego_rank",          # "lag_luego_rank" o "rank_luego_lag"
    "extras": "flags",                  # "conteo" o "flags"
    "rankear_extras": False,
    "lags": [1, 2],
    "deltas": [1, 2],
    "claves": ["ctrx_quarter", "mpasivos_margen", "mcaja_ahorro", "mcuentas_saldo",
               "ctarjeta_visa_transacciones", "ctarjeta_master_transacciones",
               "ctarjeta_debito_transacciones", "mprestamos_personales", "mpayroll",
               "cmobile_app_trx", "chomebanking_transacciones", "mcomisiones",
               "cdescubierto_preacordado", "mcuenta_corriente", "Visa_msaldototal",
               "Master_msaldototal"],
    "relativas_max3": ["ctrx_quarter", "mcaja_ahorro"],
}

if len(sys.argv) > 1:
    config = Path(sys.argv[1])
    PARAM.update(json.loads(config.read_text(encoding="utf-8")))
    PARAM["_config"] = config.name
    print(f"Configuracion tomada de {config}")

assert PARAM["orden"] in ("lag_luego_rank", "rank_luego_lag"), "orden invalido"
assert PARAM["extras"] in ("conteo", "flags"), "extras invalido"
exp = iniciar_experimento(PARAM)
NO_FEATURES = ["numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"]

# ---------------------------------------------------------------------------
# Carga (orden cliente-mes: necesario para los lags)
# ---------------------------------------------------------------------------
t0 = time.time()
base = pd.read_parquet(DIR_DATA / PARAM["dataset_entrada"])
base = base.sort_values(["numero_de_cliente", "foto_mes"], kind="mergesort").reset_index(drop=True)
assert not base.duplicated(["numero_de_cliente", "foto_mes"]).any(), "Hay cliente-mes repetidos"
features = [c for c in base.columns if c not in NO_FEATURES]
no_numericas = [c for c in features if not pd.api.types.is_numeric_dtype(base[c])]
if no_numericas:
    raise ValueError(f"Hay variables no numericas, revisar: {no_numericas}")
claves = [c for c in PARAM["claves"] if c in features]
assert len(claves) >= 12, f"Faltan demasiadas variables clave: {sorted(set(PARAM['claves']) - set(claves))}"
assert all(c in features for c in PARAM["relativas_max3"]), "Falta alguna variable de relativas_max3"
print(f"Leido {PARAM['dataset_entrada']}: {len(base):,} filas, {len(features)} variables, {len(claves)} claves "
      f"| orden={PARAM['orden']} extras={PARAM['extras']} rankear_extras={PARAM['rankear_extras']} "
      f"({time.time() - t0:.0f} s)")

n = len(base)
mes = base["foto_mes"].to_numpy()
cliente = base["numero_de_cliente"].to_numpy()
periodo = (mes // 100) * 12 + mes % 100
meses = sorted(int(m) for m in np.unique(mes))
idx_mes = {m: np.flatnonzero(mes == m) for m in meses}

fila_valida = {}
for k in sorted(set(PARAM["lags"]) | set(PARAM["deltas"]) | {1, 2}):
    ok = np.zeros(n, dtype=bool)
    ok[k:] = (cliente[k:] == cliente[:-k]) & (periodo[k:] - periodo[:-k] == k)
    fila_valida[k] = ok


def lag_de(x, k):
    out = np.full(n, np.nan, dtype="float32")
    out[k:] = x[:-k]
    out[~fila_valida[k]] = np.nan
    return out


def rank_cero_fijo(x):
    """Dentro de cada mes: positivos (0,1], negativos [-1,0), cero 0, NA NA (identico a 03b)."""
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


def controlar_rank(nombre, valores, rk):
    assert np.array_equal(np.isnan(rk), np.isnan(valores)), f"Cambiaron los NA en {nombre}"
    assert np.array_equal(rk == 0, valores == 0), f"Cambiaron los ceros en {nombre}"
    assert np.array_equal(rk > 0, valores > 0), f"Cambio el signo en {nombre}"
    assert np.nanmin(rk, initial=0) >= -1 and np.nanmax(rk, initial=0) <= 1, f"Fuera de rango en {nombre}"


# ---------------------------------------------------------------------------
# 1) Variables del proceso de muerte (sobre valores CRUDOS)
# ---------------------------------------------------------------------------
t0 = time.time()
nuevas = {}
n_apagados = np.zeros(n, dtype="float32")
n_dejo = np.zeros(n, dtype="float32")
sin_historia = ~fila_valida[1] & ~fila_valida[2]
for c in claves:
    x = base[c].to_numpy(dtype="float32")
    apagado = np.isnan(x) | (x == 0)
    l1, l2 = lag_de(x, 1), lag_de(x, 2)
    activo_antes = (~np.isnan(l1) & (l1 != 0)) | (~np.isnan(l2) & (l2 != 0))
    dejo = (apagado & activo_antes).astype("float32")
    n_apagados += apagado
    n_dejo += dejo
    if PARAM["extras"] == "flags":
        dejo[sin_historia] = np.nan
        nuevas[f"dejo_{c}"] = dejo
n_dejo[sin_historia] = np.nan
nuevas["n_apagados"] = n_apagados
nuevas["n_apagados_delta1"] = n_apagados - lag_de(n_apagados, 1)
nuevas["n_apagados_delta2"] = n_apagados - lag_de(n_apagados, 2)
nuevas["n_dejo_de_usar"] = n_dejo
for c in PARAM["relativas_max3"]:
    x = base[c].to_numpy(dtype="float32")
    maximo = np.fmax(np.fmax(x, lag_de(x, 1)), lag_de(x, 2))
    with np.errstate(divide="ignore", invalid="ignore"):
        nuevas[f"{c}_rel_max3"] = np.where(maximo > 0, x / maximo, np.nan).astype("float32")

# controles
assert np.nanmax(nuevas["n_apagados"]) <= len(claves)
assert np.isnan(nuevas["n_apagados_delta1"][~fila_valida[1]]).all()
assert (nuevas["n_dejo_de_usar"][~sin_historia] <= nuevas["n_apagados"][~sin_historia]).all()
if PARAM["extras"] == "flags":
    suma = np.nansum(np.column_stack([nuevas[f"dejo_{c}"] for c in claves]), axis=1)
    assert np.array_equal(suma[~sin_historia], nuevas["n_dejo_de_usar"][~sin_historia]), \
        "La suma de los indicadores tiene que ser n_dejo_de_usar"
for c in PARAM["relativas_max3"]:
    assert np.nanmax(nuevas[f"{c}_rel_max3"]) <= 1 + 1e-5

# informativo: tasa de BAJA+2 cuando se apago cada producto (meses con clase completa)
ct = base["clase_ternaria"].astype(str).to_numpy()
en_completos = np.isin(mes, meses[:-2])
baja2 = ct == "BAJA+2"
tasa_general = baja2[en_completos].mean()
if PARAM["extras"] == "flags":
    filas = []
    for c in claves:
        f = nuevas[f"dejo_{c}"]
        m1 = en_completos & (f == 1)
        filas.append({"producto": c, "clientes_que_lo_dejaron": int(m1.sum()),
                      "tasa_baja2_pct": round(100 * baja2[m1].mean(), 3) if m1.any() else np.nan,
                      "lift": round(baja2[m1].mean() / tasa_general, 2) if m1.any() else np.nan})
    t = pd.DataFrame(filas).sort_values("lift", ascending=False)
    t.to_csv(exp.ruta("lift_por_producto_abandonado"), index=False)
    print("\nTasa de BAJA+2 entre quienes DEJARON cada producto (meses con clase completa):")
    print(t.to_string(index=False))
print(f"Variables nuevas: {len(nuevas)} ({time.time() - t0:.0f} s)")

# ---------------------------------------------------------------------------
# 2) Lags/deltas + ranking de las 152 originales
# ---------------------------------------------------------------------------
t0 = time.time()
columnas = {}
for i, c in enumerate(features, start=1):
    x = base[c].to_numpy(dtype="float32")
    if PARAM["orden"] == "lag_luego_rank":
        crudas = {c: x}
        lags = {k: lag_de(x, k) for k in (1, 2)}
        for k in PARAM["lags"]:
            crudas[f"{c}_lag{k}"] = lags[k]
        for k in PARAM["deltas"]:
            crudas[f"{c}_delta{k}"] = x - lags[k]
        for nombre, valores in crudas.items():
            rk = rank_cero_fijo(valores)
            controlar_rank(nombre, valores, rk)
            columnas[nombre] = rk
    else:  # rank_luego_lag
        rk = rank_cero_fijo(x)
        controlar_rank(c, x, rk)
        columnas[c] = rk
        lags = {k: lag_de(rk, k) for k in (1, 2)}     # posicion que tenia en SU mes
        for k in PARAM["lags"]:
            columnas[f"{c}_lag{k}"] = lags[k]
        for k in PARAM["deltas"]:
            d = rk - lags[k]                            # cambio de posicion, en [-2, 2]
            assert np.nanmax(np.abs(d), initial=0) <= 2 + 1e-5
            columnas[f"{c}_delta{k}"] = d
    if i % 25 == 0 or i == len(features):
        print(f"  {i}/{len(features)} variables ({time.time() - t0:.0f} s)", flush=True)

for nombre, valores in nuevas.items():
    if PARAM["rankear_extras"]:
        rk = rank_cero_fijo(valores)
        controlar_rank(nombre, valores, rk)
        columnas[nombre] = rk
    else:
        columnas[nombre] = valores.astype("float32")
n_nuevas = len(nuevas)
del nuevas
gc.collect()

# controles de lag
var_ctrl = "mcuentas_saldo" if "mcuentas_saldo" in features else features[0]
assert np.isnan(columnas[f"{var_ctrl}_lag1"][idx_mes[meses[0]]]).all(), "En el primer mes no puede haber lag1"
assert np.isnan(columnas[f"{var_ctrl}_lag2"][idx_mes[meses[1]]]).all(), "En el segundo mes no puede haber lag2"
if PARAM["orden"] == "rank_luego_lag":
    # el lag1 de un cliente tiene que ser su ranking del mes anterior
    j = np.flatnonzero(fila_valida[1])[:1000]
    assert np.allclose(columnas[f"{var_ctrl}_lag1"][j], columnas[var_ctrl][j - 1], equal_nan=True), \
        "El lag1 no coincide con el ranking del mes anterior"

# ---------------------------------------------------------------------------
# Grabado
# ---------------------------------------------------------------------------
t0 = time.time()
tabla = pa.Table.from_pandas(base[NO_FEATURES], preserve_index=False)
del base
gc.collect()
for nombre in list(columnas):
    tabla = tabla.append_column(nombre, pa.array(columnas.pop(nombre), from_pandas=True))
archivo = DIR_DATA / PARAM["dataset_salida"]
pq.write_table(tabla, archivo, compression="zstd")
n_cols = tabla.num_columns
assert tabla.num_rows == n, "Cambio la cantidad de filas al grabar"
esperadas = len(NO_FEATURES) + len(features) * (1 + len(PARAM["lags"]) + len(PARAM["deltas"])) + n_nuevas
assert n_cols == esperadas, f"Cantidad de columnas inesperada: {n_cols} (se esperaban {esperadas})"
del tabla
gc.collect()
mb = archivo.stat().st_size / 1e6
print(f"\nGrabado {archivo.name}: {n:,} filas x {n_cols} columnas ({n_nuevas} nuevas), {mb:,.0f} MB "
      f"({time.time() - t0:.0f} s)")

cerrar_experimento(exp, {"archivo": archivo.name, "columnas": n_cols, "MB": round(mb), "nuevas": n_nuevas,
                         "orden": PARAM["orden"], "extras": PARAM["extras"],
                         "rankear_extras": PARAM["rankear_extras"]})
