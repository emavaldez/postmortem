"""
03c_fe_extra.py
DMEyF 2026 - Primera Competencia - Experimento 3003

Igual que 03b (receta del profesor: lags y deltas 1 y 2 sobre crudos, despues ranking de TODO
dentro de cada mes con cero fijo, NA se mantiene) MAS 6 variables nuevas del "proceso de muerte"
(ver revision_cowork4/informe_revision4.md, tarea 3):

  n_apagados             cuantas de las variables clave estan en cero o NA este mes
  n_apagados_delta1      n_apagados - n_apagados del mes anterior   (NA si no hay mes anterior)
  n_apagados_delta2      n_apagados - n_apagados de 2 meses antes   (NA si no hay)
  n_dejo_de_usar         cuantas variables clave estaban activas (distintas de 0 y no NA) hace
                         1 o 2 meses y ahora estan en cero o NA      (NA si no hay ninguno de los dos meses)
  ctrx_quarter_rel_max3  ctrx_quarter / maximo de ctrx_quarter en los ultimos 3 meses (este incluido)
                         NA si ese maximo es 0 o NA
  mcaja_ahorro_rel_max3  idem con mcaja_ahorro (saldo de caja de ahorro), NA si el maximo <= 0

Las 6 nuevas NO llevan lags/deltas (ya miran el pasado); se rankean igual que el resto.
Las 152 originales llevan lag1, lag2, delta1, delta2 como en 03b.

OJO lag2: en 202104 los lag2/delta2 (y n_apagados_delta2) estan 100% vacios porque el dataset
empieza en 202103. Entrenando solo con abril no se pueden validar.

Uso (desde la carpeta Primera_competencia, cuando la PC este libre):
    Copy-Item revision_cowork4\\03c_fe_extra.py 03c_fe_extra.py
    py -3.12 03c_fe_extra.py
Genera data/ds3003_rank_extra.parquet (~983 mil filas x 771 columnas, ~550 MB) en ~1-2 min.
Memoria: pico estimado ~5 GB (las ~770 columnas finales en float32 = ~3 GB + la base).
"""

print("Arrancando 03c_fe_extra.py ...", flush=True)

import gc
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

try:
    from exp_utils import DIR_DATA, cerrar_experimento, iniciar_experimento
except ImportError:   # si se corre desde revision_cowork4\ en lugar de la raiz del proyecto
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from exp_utils import DIR_DATA, cerrar_experimento, iniciar_experimento

# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 3003,
    "nombre": "fe_rank_extra",
    "descripcion": "Como 3002 (lags/deltas 1 y 2 + rank total por mes con cero fijo, NA se mantiene) "
                   "mas 6 variables del proceso de muerte: n_apagados, sus deltas 1 y 2, n_dejo_de_usar, "
                   "ctrx_quarter y mcaja_ahorro relativos al maximo de 3 meses.",
    "dataset_entrada": "ds1001_base.parquet",
    "dataset_salida": "ds3003_rank_extra.parquet",
    "lags": [1, 2],
    "deltas": [1, 2],
    # variables cuyo cero/NA mas se asocia a la baja (2002: lift) o que se apagan antes de irse
    # (2002: proceso de muerte), mas las mas importantes de 5005
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
faltan = sorted(set(PARAM["claves"]) - set(claves))
assert len(claves) >= 12, f"Faltan demasiadas variables clave en el dataset: {faltan}"
if faltan:
    print(f"AVISO: variables clave que no estan en el dataset (se omiten): {faltan}")
assert all(c in features for c in PARAM["relativas_max3"]), "Falta alguna variable de relativas_max3"
print(f"Leido {PARAM['dataset_entrada']}: {len(base):,} filas, {len(features)} variables, "
      f"{len(claves)} claves ({time.time() - t0:.0f} s)")

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
assert 1 in fila_valida and 2 in fila_valida, "Las variables nuevas necesitan lags 1 y 2"


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
# 1) Variables nuevas (sobre valores CRUDOS, antes de rankear)
# ---------------------------------------------------------------------------
t0 = time.time()
nuevas = {}
n_apagados = np.zeros(n, dtype="float32")
n_dejo = np.zeros(n, dtype="float32")
for c in claves:
    x = base[c].to_numpy(dtype="float32")
    apagado = np.isnan(x) | (x == 0)
    l1, l2 = lag_de(x, 1), lag_de(x, 2)
    activo_antes = (~np.isnan(l1) & (l1 != 0)) | (~np.isnan(l2) & (l2 != 0))
    n_apagados += apagado
    n_dejo += apagado & activo_antes
sin_historia = ~fila_valida[1] & ~fila_valida[2]
n_dejo[sin_historia] = np.nan
nuevas["n_apagados"] = n_apagados
nuevas["n_apagados_delta1"] = n_apagados - lag_de(n_apagados, 1)
nuevas["n_apagados_delta2"] = n_apagados - lag_de(n_apagados, 2)
nuevas["n_dejo_de_usar"] = n_dejo

for c in PARAM["relativas_max3"]:
    x = base[c].to_numpy(dtype="float32")
    maximo = np.fmax(np.fmax(x, lag_de(x, 1)), lag_de(x, 2))     # fmax ignora NA
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.where(maximo > 0, x / maximo, np.nan).astype("float32")
    nuevas[f"{c}_rel_max3"] = rel

# controles de las nuevas
assert np.nanmin(nuevas["n_apagados"]) >= 0 and np.nanmax(nuevas["n_apagados"]) <= len(claves)
assert np.isnan(nuevas["n_apagados_delta1"][~fila_valida[1]]).all(), "delta1 deberia ser NA sin mes anterior"
assert np.nanmax(nuevas["n_dejo_de_usar"]) <= len(claves)
assert (nuevas["n_dejo_de_usar"][~sin_historia] <= nuevas["n_apagados"][~sin_historia]).all(), \
    "No se puede haber dejado de usar mas productos de los que estan apagados"
for c in PARAM["relativas_max3"]:
    r = nuevas[f"{c}_rel_max3"]
    assert np.nanmax(r) <= 1 + 1e-5, f"{c}_rel_max3 mayor que 1"

# resumen de las nuevas por mes y su relacion con la clase (meses con clase completa)
ct = base["clase_ternaria"].astype(str).to_numpy()
completos = meses[:-2]
en_completos = np.isin(mes, completos)
baja2 = (ct == "BAJA+2") & en_completos
filas = []
for nombre, v in nuevas.items():
    for m in meses:
        idx = idx_mes[m]
        filas.append({"variable": nombre, "foto_mes": m, "pct_na": round(100 * np.isnan(v[idx]).mean(), 1),
                      "media": round(float(np.nanmean(v[idx])), 3) if (~np.isnan(v[idx])).any() else np.nan})
pd.DataFrame(filas).to_csv(exp.ruta("nuevas_por_mes"), index=False)

# tasa de BAJA+2 por valor de n_apagados (meses completos): deberia crecer con n_apagados
na = nuevas["n_apagados"]
tabla_ap = (pd.DataFrame({"n_apagados": na[en_completos], "baja2": baja2[en_completos]})
              .groupby("n_apagados")["baja2"].agg(clientes="size", tasa_baja2_pct="mean"))
tabla_ap["tasa_baja2_pct"] = (100 * tabla_ap["tasa_baja2_pct"]).round(3)
tabla_ap.to_csv(exp.ruta("tasa_por_n_apagados"))
print("\nTasa de BAJA+2 segun cantidad de variables clave apagadas (meses con clase completa):")
print(tabla_ap.to_string())
print(f"Variables nuevas listas ({time.time() - t0:.0f} s)")

# ---------------------------------------------------------------------------
# 2) Lags/deltas de las 152 originales + ranking de todo (como 03b)
# ---------------------------------------------------------------------------
t0 = time.time()
columnas = {}
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
        controlar_rank(nombre, valores, rk)
        columnas[nombre] = rk
    del x, crudas, lags
    if i % 25 == 0 or i == len(features):
        print(f"  {i}/{len(features)} variables ({time.time() - t0:.0f} s)", flush=True)

for nombre, valores in nuevas.items():
    rk = rank_cero_fijo(valores)
    controlar_rank(nombre, valores, rk)
    columnas[nombre] = rk
del nuevas
gc.collect()

# control de lag: en una muestra, el lag1 rankeado de mcuentas_saldo es NA exactamente donde no hay mes anterior
var_ctrl = "mcuentas_saldo" if "mcuentas_saldo" in features else features[0]
assert np.array_equal(np.isnan(columnas[f"{var_ctrl}_lag1"]),
                      ~fila_valida[1] | np.isnan(lag_de(base[var_ctrl].to_numpy(dtype="float32"), 1))), \
    f"El lag1 de {var_ctrl} no respeta los meses faltantes"
# en el primer mes y en abril para lag2 todo tiene que ser NA
primer = idx_mes[meses[0]]
assert np.isnan(columnas[f"{var_ctrl}_lag1"][primer]).all(), "En el primer mes no puede haber lag1"
assert np.isnan(columnas[f"{var_ctrl}_lag2"][idx_mes[meses[1]]]).all(), "En el segundo mes no puede haber lag2"

# ---------------------------------------------------------------------------
# Grabado (columna por columna en una tabla Arrow: no arma un DataFrame gigante)
# ---------------------------------------------------------------------------
t0 = time.time()
tabla = pa.Table.from_pandas(base[NO_FEATURES], preserve_index=False)
del base
gc.collect()
n_nuevas = 0
for nombre in list(columnas):
    tabla = tabla.append_column(nombre, pa.array(columnas.pop(nombre), from_pandas=True))
    n_nuevas += 1
archivo = DIR_DATA / PARAM["dataset_salida"]
pq.write_table(tabla, archivo, compression="zstd")
n_cols = tabla.num_columns
assert tabla.num_rows == n, "Cambio la cantidad de filas al grabar"
assert n_cols == len(NO_FEATURES) + len(features) * 5 + 6, f"Cantidad de columnas inesperada: {n_cols}"
del tabla
gc.collect()
mb = archivo.stat().st_size / 1e6
print(f"\nGrabado {archivo.name}: {n:,} filas x {n_cols} columnas "
      f"({len(features)} x 5 + 6 nuevas + id/mes/clases), {mb:,.0f} MB ({time.time() - t0:.0f} s)")

cerrar_experimento(exp, {"archivo": archivo.name, "columnas": n_cols, "MB": round(mb),
                         "variables_originales": len(features), "claves": len(claves),
                         "nuevas": ["n_apagados", "n_apagados_delta1", "n_apagados_delta2", "n_dejo_de_usar"]
                                   + [f"{c}_rel_max3" for c in PARAM["relativas_max3"]]})
