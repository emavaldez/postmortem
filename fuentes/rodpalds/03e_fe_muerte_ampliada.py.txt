"""
03e_fe_muerte_ampliada.py
DMEyF 2026 - Primera Competencia - Experimento 3006

Receta del profesor (como 03c / ds3003: lags y deltas 1 y 2 sobre crudos, despues ranking de
TODO dentro de cada mes con cero fijo, NA se mantiene) + las 6 variables del proceso de muerte
de 03c (mismas 16 claves) + una version AMPLIADA del proceso de muerte:

  A) Conteo sobre ~45 productos (en lugar de 16):
       n_apagados_amplio, n_apagados_amplio_delta1, n_apagados_amplio_delta2, n_dejo_de_usar_amplio
  B) Conteo por GRUPO de productos (el profesor: "deja primero las tarjetas, despues otros
     servicios"), apagados y dejo_de_usar por grupo:
       tarjetas, canales, transaccional, ahorro, credito, sueldo, seguros  -> 14 variables
  C) Puntaje ponderado: suma de los productos apagados pesados por log(lift), con el lift
     calculado SOLO con BAJA+2 de 202103-202104 (sin mirar junio: no contamina la mitad B):
       score_apagado, score_apagado_delta1
  D) Valor de hoy / maximo de los ultimos 3 meses para 8 variables mas (ademas de las 2 de 03c)

"Apagado" = 0 o NA.  "Activo" = distinto de 0 y no NA.  Todas las nuevas se rankean por mes con
cero fijo, igual que el resto (como en 03c, que gano en 5104/5105).

Uso:  py -3.12 03e_fe_muerte_ampliada.py
"""

print("Arrancando 03e_fe_muerte_ampliada.py ...", flush=True)

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
    "experimento": 3006,
    "nombre": "fe_muerte_ampliada",
    "descripcion": "ds3003 (receta + 6 variables del proceso de muerte) + proceso de muerte ampliado: conteo "
                   "sobre ~45 productos, conteos por grupo (tarjetas, canales, transaccional, ahorro, credito, "
                   "sueldo, seguros), puntaje ponderado por log(lift) calculado con 202103-202104, y relativo al "
                   "maximo de 3 meses para 8 variables mas. Todo rankeado por mes con cero fijo.",
    "dataset_entrada": "ds1001_base.parquet",
    "dataset_salida": "ds3006_muerte_ampliada.parquet",
    "lags": [1, 2],
    "deltas": [1, 2],
    # las 16 de 03c (se conservan las 6 variables originales tal cual)
    "claves_03c": ["ctrx_quarter", "mpasivos_margen", "mcaja_ahorro", "mcuentas_saldo",
                   "ctarjeta_visa_transacciones", "ctarjeta_master_transacciones",
                   "ctarjeta_debito_transacciones", "mprestamos_personales", "mpayroll",
                   "cmobile_app_trx", "chomebanking_transacciones", "mcomisiones",
                   "cdescubierto_preacordado", "mcuenta_corriente", "Visa_msaldototal",
                   "Master_msaldototal"],
    "relativas_max3_03c": ["ctrx_quarter", "mcaja_ahorro"],
    "grupos": {
        "tarjetas": ["ctarjeta_visa", "ctarjeta_master", "ctarjeta_visa_transacciones",
                     "ctarjeta_master_transacciones", "mtarjeta_visa_consumo", "mtarjeta_master_consumo",
                     "Visa_msaldototal", "Master_msaldototal", "ctarjeta_debito_transacciones"],
        "canales": ["chomebanking_transacciones", "cmobile_app_trx", "thomebanking", "tmobile_app",
                    "catm_trx", "catm_trx_other", "cextraccion_autoservicio", "ccajas_transacciones"],
        "transaccional": ["ctrx_quarter", "active_quarter", "ctransferencias_recibidas",
                          "ctransferencias_emitidas", "cpagomiscuentas", "cpagodeservicios",
                          "ccuenta_debitos_automaticos", "ctarjeta_visa_debitos_automaticos",
                          "mcomisiones", "ccomisiones_otras"],
        "ahorro": ["mcaja_ahorro", "mcuentas_saldo", "mcaja_ahorro_dolares", "mpasivos_margen",
                   "cplazo_fijo", "cinversion1", "cinversion2"],
        "credito": ["cprestamos_personales", "mprestamos_personales", "cdescubierto_preacordado"],
        "sueldo": ["mpayroll", "cpayroll_trx"],
        "seguros": ["cseguro_vida", "cseguro_vivienda", "cseguro_accidentes_personales"],
    },
    "relativas_max3_extra": ["mpayroll", "mtarjeta_visa_consumo", "mcuentas_saldo",
                             "ctarjeta_visa_transacciones", "chomebanking_transacciones",
                             "cmobile_app_trx", "mpasivos_margen", "ctarjeta_debito_transacciones"],
    "meses_lift": [202103, 202104],     # SOLO meses de entrenamiento de la validacion
}

if len(sys.argv) > 1:
    config = Path(sys.argv[1])
    PARAM.update(json.loads(config.read_text(encoding="utf-8")))
    PARAM["_config"] = config.name
    print(f"Configuracion tomada de {config}")

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

claves_03c = [c for c in PARAM["claves_03c"] if c in features]
assert len(claves_03c) >= 12, "Faltan variables clave de 03c"
grupos = {g: [c for c in vs if c in features] for g, vs in PARAM["grupos"].items()}
faltan = sorted({c for vs in PARAM["grupos"].values() for c in vs} - set(features))
if faltan:
    print(f"AVISO: variables de los grupos que no estan en el dataset (se omiten): {faltan}")
assert all(len(v) >= 1 for v in grupos.values()), f"Algun grupo quedo vacio: {grupos}"
amplio = sorted(set(claves_03c) | {c for vs in grupos.values() for c in vs})
assert len(amplio) >= 30, f"La lista ampliada tiene solo {len(amplio)} variables"
rel_extra = [c for c in PARAM["relativas_max3_extra"] if c in features and c not in PARAM["relativas_max3_03c"]]
print(f"Leido {PARAM['dataset_entrada']}: {len(base):,} filas, {len(features)} variables | "
      f"16 claves de 03c: {len(claves_03c)} | lista ampliada: {len(amplio)} | "
      f"grupos: { {g: len(v) for g, v in grupos.items()} } ({time.time() - t0:.0f} s)")

n = len(base)
mes = base["foto_mes"].to_numpy()
cliente = base["numero_de_cliente"].to_numpy()
periodo = (mes // 100) * 12 + mes % 100
meses = sorted(int(m) for m in np.unique(mes))
idx_mes = {m: np.flatnonzero(mes == m) for m in meses}
fila_valida = {}
for k in (1, 2):
    ok = np.zeros(n, dtype=bool)
    ok[k:] = (cliente[k:] == cliente[:-k]) & (periodo[k:] - periodo[:-k] == k)
    fila_valida[k] = ok
sin_historia = ~fila_valida[1] & ~fila_valida[2]


def lag_de(x, k):
    out = np.full(n, np.nan, dtype="float32")
    out[k:] = x[:-k]
    out[~fila_valida[k]] = np.nan
    return out


def rank_cero_fijo(x):
    """Dentro de cada mes: positivos (0,1], negativos [-1,0), cero 0, NA NA (identico a 03b/03c)."""
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
apagado, dejo = {}, {}
for c in amplio:
    x = base[c].to_numpy(dtype="float32")
    ap = np.isnan(x) | (x == 0)
    l1, l2 = lag_de(x, 1), lag_de(x, 2)
    activo_antes = (~np.isnan(l1) & (l1 != 0)) | (~np.isnan(l2) & (l2 != 0))
    apagado[c] = ap
    dejo[c] = ap & activo_antes


def conteo(lista, cual):
    return np.sum([cual[c] for c in lista], axis=0).astype("float32")


nuevas = {}
# --- las 6 de 03c, identicas ---
na16 = conteo(claves_03c, apagado)
nd16 = conteo(claves_03c, dejo)
nd16[sin_historia] = np.nan
nuevas["n_apagados"] = na16
nuevas["n_apagados_delta1"] = na16 - lag_de(na16, 1)
nuevas["n_apagados_delta2"] = na16 - lag_de(na16, 2)
nuevas["n_dejo_de_usar"] = nd16


def rel_max3(c):
    x = base[c].to_numpy(dtype="float32")
    maximo = np.fmax(np.fmax(x, lag_de(x, 1)), lag_de(x, 2))
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(maximo > 0, x / maximo, np.nan).astype("float32")


for c in PARAM["relativas_max3_03c"]:
    nuevas[f"{c}_rel_max3"] = rel_max3(c)
n_03c = len(nuevas)

# --- A) conteo amplio ---
na = conteo(amplio, apagado)
nd = conteo(amplio, dejo)
nd[sin_historia] = np.nan
nuevas["n_apagados_amplio"] = na
nuevas["n_apagados_amplio_delta1"] = na - lag_de(na, 1)
nuevas["n_apagados_amplio_delta2"] = na - lag_de(na, 2)
nuevas["n_dejo_de_usar_amplio"] = nd

# --- B) por grupo ---
for g, vs in grupos.items():
    nuevas[f"n_apagados_{g}"] = conteo(vs, apagado)
    d = conteo(vs, dejo)
    d[sin_historia] = np.nan
    nuevas[f"n_dejo_{g}"] = d

# --- C) puntaje ponderado por log(lift), lift SOLO con meses_lift ---
ct = base["clase_ternaria"].astype(str).to_numpy()
en_lift = np.isin(mes, PARAM["meses_lift"])
baja2 = (ct == "BAJA+2")
tasa = baja2[en_lift].mean()
assert tasa > 0, "No hay BAJA+2 en los meses para el lift"
pesos = {}
for c in amplio:
    m = en_lift & apagado[c]
    if m.sum() >= 500:
        lift = baja2[m].mean() / tasa
        pesos[c] = float(max(np.log(lift), 0.0)) if lift > 0 else 0.0
    else:
        pesos[c] = 0.0
score = np.sum([apagado[c] * pesos[c] for c in amplio], axis=0).astype("float32")
nuevas["score_apagado"] = score
nuevas["score_apagado_delta1"] = score - lag_de(score, 1)
pd.Series(pesos, name="peso_log_lift").sort_values(ascending=False).to_csv(exp.ruta("pesos_score"))

# --- D) relativo al maximo de 3 meses, 8 variables mas ---
for c in rel_extra:
    nuevas[f"{c}_rel_max3"] = rel_max3(c)

# controles
assert np.nanmax(nuevas["n_apagados_amplio"]) <= len(amplio)
assert (nuevas["n_dejo_de_usar_amplio"][~sin_historia] <= nuevas["n_apagados_amplio"][~sin_historia]).all()
assert np.isnan(nuevas["n_apagados_amplio_delta1"][~fila_valida[1]]).all()
for g, vs in grupos.items():
    assert np.nanmax(nuevas[f"n_apagados_{g}"]) <= len(vs)
for c in PARAM["relativas_max3_03c"] + rel_extra:
    assert np.nanmax(nuevas[f"{c}_rel_max3"]) <= 1 + 1e-5
del apagado, dejo
gc.collect()

# informativo: tasa de BAJA+2 segun el conteo amplio y el puntaje (meses con clase completa)
completos = np.isin(mes, meses[:-2])
filas = []
for nombre in ["n_apagados", "n_apagados_amplio", "score_apagado"] + [f"n_apagados_{g}" for g in grupos]:
    v = nuevas[nombre][completos]
    q = pd.qcut(pd.Series(v), 10, labels=False, duplicates="drop")
    t = pd.DataFrame({"decil": q, "b2": baja2[completos]}).groupby("decil")["b2"].mean()
    filas.append({"variable": nombre, "tasa_decil_bajo_pct": round(100 * t.iloc[0], 3),
                  "tasa_decil_alto_pct": round(100 * t.iloc[-1], 3),
                  "cociente_alto_bajo": round(t.iloc[-1] / max(t.iloc[0], 1e-9), 1)})
senal = pd.DataFrame(filas)
senal.to_csv(exp.ruta("senal_nuevas"), index=False)
print("\nTasa de BAJA+2 en el decil mas bajo y mas alto de cada variable nueva (meses con clase completa):")
print(senal.to_string(index=False))
print(f"Variables nuevas: {len(nuevas)} ({n_03c} de 03c + {len(nuevas) - n_03c} ampliadas) "
      f"({time.time() - t0:.0f} s)")

# ---------------------------------------------------------------------------
# 2) Lags/deltas de las originales + ranking de todo (como 03b/03c)
# ---------------------------------------------------------------------------
t0 = time.time()
columnas = {}
for i, c in enumerate(features, start=1):
    x = base[c].to_numpy(dtype="float32")
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
    del x, crudas, lags
    if i % 25 == 0 or i == len(features):
        print(f"  {i}/{len(features)} variables ({time.time() - t0:.0f} s)", flush=True)

for nombre, valores in nuevas.items():
    rk = rank_cero_fijo(valores)
    controlar_rank(nombre, valores, rk)
    columnas[nombre] = rk
n_nuevas = len(nuevas)
del nuevas
gc.collect()

var_ctrl = "mcuentas_saldo" if "mcuentas_saldo" in features else features[0]
assert np.isnan(columnas[f"{var_ctrl}_lag1"][idx_mes[meses[0]]]).all(), "En el primer mes no puede haber lag1"
assert np.isnan(columnas[f"{var_ctrl}_lag2"][idx_mes[meses[1]]]).all(), "En el segundo mes no puede haber lag2"

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
assert tabla.num_rows == n
esperadas = len(NO_FEATURES) + len(features) * 5 + n_nuevas
assert n_cols == esperadas, f"Cantidad de columnas inesperada: {n_cols} (se esperaban {esperadas})"
del tabla
gc.collect()
mb = archivo.stat().st_size / 1e6
print(f"\nGrabado {archivo.name}: {n:,} filas x {n_cols} columnas ({n_nuevas} nuevas), {mb:,.0f} MB "
      f"({time.time() - t0:.0f} s)")

cerrar_experimento(exp, {"archivo": archivo.name, "columnas": n_cols, "MB": round(mb), "nuevas": n_nuevas,
                         "lista_ampliada": len(amplio)})
