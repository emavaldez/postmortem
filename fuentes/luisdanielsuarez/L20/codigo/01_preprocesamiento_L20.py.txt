"""
01_preprocesamiento_L20.py — DMEyF, 1ra competencia, L20: base de datos con lo recomendado por el profesor.
PASO 1: genera la base de datos en parquet.

Qué hace (en este orden):
  1) Lee competencia_01_ternaria.csv.
  2) ccajas_depositos = NA solo en 202105 (la columna está rota ese mes: todos ceros).
  3) clase_binaria: BAJA+1 y BAJA+2 = 1, CONTINUA = 0, resto (07 no-baja y 08) = NA.
     Se conserva clase_ternaria (la ganancia necesita distinguir BAJA+2).
  4) Variables históricas de todas las columnas, EXCEPTO las 10 sin historia (edad, antigüedad y fechas relativas):
        lag1, lag2, delta1 = x - lag1, delta2 = x - lag2                       (orden 1 y 2)
        tend3 = pendiente de la recta de cuadrados mínimos sobre el mes actual y los 2 anteriores
        avg3  = promedio de esos 3 meses
     Todo por UNIÓN con (cliente, mes-k), no con shift por fila: los meses faltantes quedan como NA.
     tend3 y avg3 necesitan al menos 2 meses disponibles (si no, NA). Réplica de fhistC del ejemplo en R (ventana=3).
  5) Ranking con cero fijo, por variable y por mes, sobre los SIETE grupos
     (original, lag1, delta1, lag2, delta2, tend3, avg3). Reemplaza a la variable cruda:
        x > 0 -> rank entre los positivos del mes / n_positivos      en (0, 1]
        x = 0 -> 0
        x < 0 -> -(rank de |x| entre los negativos del mes / n_neg)  en [-1, 0)
        NA    -> NA
  6) Variables _zero (recomendación 1.3): para cada variable ORIGINAL que alguna vez vale cero, un flag:
     1 si vale cero, NA si el original era NA, 0 en el resto. Se calculan sobre el valor crudo y NO se rankean.
     Quedan SIN rankear: numero_de_cliente, foto_mes, clase_ternaria, clase_binaria y las _zero.
  7) Guarda parquet (numero_de_cliente en float64) y lo copia al bucket.
Sin variables derivadas. Requiere preproc_comun.py en la misma carpeta que este script.

Uso (terminal de la VM, desde ~/dmeyf):
    pip install pandas pyarrow gcsfs
    nohup python 01_preprocesamiento_L20.py > L20_prep.log 2>&1 &

Salidas:
    ~/dmeyf/datasets/L20_dataset.parquet           -> gs://luisdsuarez_buckito2026/datasets/L20_dataset.parquet
    ~/dmeyf/exp/L20/L20_dataset_manifest.json      -> gs://luisdsuarez_buckito2026/exp/L20/
    ~/dmeyf/exp/L20/codigo/                        (copia de este script y de preproc_comun.py)
"""
import argparse
import json
import os
import shutil
import subprocess
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

try:
    import preproc_comun as pc
    from preproc_comun import (NO_RANKEAR, SIN_HISTORIA, aplicar_lag, flag_zero, posicion_de_lag, rank_cero_fijo,
                               tendencia_promedio)
except ImportError:
    raise SystemExit("Falta preproc_comun.py: copiarlo a la misma carpeta que este script (~/dmeyf).")

VOLUMEN = "L20"
BUCKET = "gs://luisdsuarez_buckito2026"
ENTRADA = f"{BUCKET}/datasets/competencia_01_ternaria.csv"

MES_ROTO = 202105
COL_ROTA = "ccajas_depositos"


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def gsutil(*args):
    """Corre gsutil sin frenar el proceso si falla (el respaldo nunca debe romper el cálculo)."""
    try:
        r = subprocess.run(["gsutil", "-q", *args], capture_output=True, text=True, timeout=3600)
        if r.returncode != 0:
            log("  (aviso gsutil:", r.stderr.strip()[:300], ")")
        return r.returncode == 0
    except Exception as e:
        log("  (aviso gsutil:", e, ")")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default=ENTRADA)
    ap.add_argument("--volumen", default=VOLUMEN)
    ap.add_argument("--dir_base", default=os.path.expanduser("~/dmeyf"))
    ap.add_argument("--sin_bucket", action="store_true", help="no copia nada al bucket (pruebas)")
    ap.add_argument("--forzar", action="store_true", help="regenera aunque el parquet ya exista")
    a = ap.parse_args()

    dir_exp = os.path.join(a.dir_base, "exp", a.volumen)
    dir_ds = os.path.join(a.dir_base, "datasets")
    os.makedirs(os.path.join(dir_exp, "codigo"), exist_ok=True)
    os.makedirs(dir_ds, exist_ok=True)
    shutil.copy(os.path.abspath(__file__), os.path.join(dir_exp, "codigo"))
    shutil.copy(os.path.abspath(pc.__file__), os.path.join(dir_exp, "codigo"))
    ruta_pq = os.path.join(dir_ds, f"{a.volumen}_dataset.parquet")
    t00 = time.time()

    if os.path.exists(ruta_pq) and not a.forzar:
        log(f"{ruta_pq} ya existe; nada que hacer (usar --forzar para regenerar)")
        return

    # ------------------------------------------------------------------ 1) lectura
    log("leyendo", a.entrada)
    cabecera = pd.read_csv(a.entrada, nrows=0).columns.tolist()
    dtypes = {c: "float64" for c in cabecera if c not in NO_RANKEAR}
    dtypes.update(numero_de_cliente="int64", foto_mes="int32", clase_ternaria="object")
    df = pd.read_csv(a.entrada, dtype=dtypes)
    cols = [c for c in df.columns if c not in NO_RANKEAR]
    log(f"  filas={len(df):,}  columnas={df.shape[1]}  features originales={len(cols)}")
    assert len(cols) == 152, f"se esperaban 152 features originales y hay {len(cols)}"
    assert not df.duplicated(["numero_de_cliente", "foto_mes"]).any(), "hay (cliente, mes) duplicados"
    faltan = [c for c in SIN_HISTORIA + [COL_ROTA] if c not in df.columns]
    assert not faltan, f"columnas esperadas que no están en el dataset: {faltan}"

    # ------------------------------------------------------------------ 2) ccajas_depositos en 202105
    m = (df["foto_mes"] == MES_ROTO).to_numpy()
    assert m.sum() > 0, f"no hay filas de {MES_ROTO}"
    v = df.loc[m, COL_ROTA]
    assert (v.fillna(0) == 0).all(), f"{COL_ROTA} en {MES_ROTO} NO es todo cero: revisar antes de poner NA"
    otros = df.loc[~m, COL_ROTA]
    log(f"  {COL_ROTA} en {MES_ROTO}: {m.sum():,} filas, todas cero -> NA. "
        f"(en los demás meses: {(otros != 0).mean():.2%} distintos de cero)")
    df.loc[m, COL_ROTA] = np.nan

    # ------------------------------------------------------------------ 3) clase binaria
    t = df["clase_ternaria"]
    df["clase_binaria"] = np.where(t.isin(["BAJA+1", "BAJA+2"]), 1.0, np.where(t == "CONTINUA", 0.0, np.nan))
    df["clase_binaria"] = df["clase_binaria"].astype("float32")
    log("  clase_ternaria por mes:\n" + pd.crosstab(df["foto_mes"], t.fillna("NA")).to_string())
    for mes in (202103, 202104, 202105, 202106):
        assert df.loc[df["foto_mes"] == mes, "clase_binaria"].notna().all(), f"faltan clases en {mes}"
    assert df.loc[df["foto_mes"] == 202108, "clase_binaria"].isna().all(), "202108 no debería tener clase"

    # ------------------------------------------------------------------ 4) preparación de lags
    df = df.sort_values(["foto_mes", "numero_de_cliente"], ignore_index=True)
    n = len(df)
    mes = df["foto_mes"].to_numpy()
    p = (mes // 100) * 12 + (mes % 100)                 # período consecutivo (cruza años sin problema)
    p0 = p - p.min()
    assert p0.max() < 99
    key = df["numero_de_cliente"].to_numpy().astype("int64") * 100 + p0
    pos = {1: posicion_de_lag(key, 1), 2: posicion_de_lag(key, 2)}
    for k in (1, 2):
        log(f"  filas con lag{k} disponible: {(pos[k] >= 0).mean():.1%}")
    idx_mes = [np.flatnonzero(mes == mm) for mm in np.unique(mes)]

    # verificación independiente del lag1 (con un merge de pandas) en dos columnas
    for c in ("mrentabilidad", COL_ROTA):
        prev = pd.DataFrame({"numero_de_cliente": df["numero_de_cliente"], "p": p + 1, "ref": df[c]})
        ref = df[["numero_de_cliente"]].assign(p=p).merge(prev, on=["numero_de_cliente", "p"], how="left")["ref"].to_numpy()
        mio = aplicar_lag(df[c].to_numpy(), pos[1])
        assert np.array_equal(mio, ref, equal_nan=True), f"lag1 de {c} no coincide con el merge de control"
    log("  verificación de lag1 por merge independiente: OK")

    # verificación independiente de tend3 / avg3: ajuste de mínimos cuadrados con np.polyfit sobre una muestra de filas
    rng = np.random.default_rng(878443)
    for c in ("mrentabilidad", "ctrx_quarter", COL_ROTA):
        x = df[c].to_numpy()
        valor = pd.Series(x, index=key)
        l1c, l2c = aplicar_lag(x, pos[1]), aplicar_lag(x, pos[2])
        tend, avg = tendencia_promedio(x, l1c, l2c)
        for r in rng.choice(n, size=min(2000, n), replace=False):
            pts = [(xv, yv) for xv, yv in ((1.0, valor.get(key[r] - 2, np.nan)), (2.0, valor.get(key[r] - 1, np.nan)),
                                           (3.0, x[r])) if not np.isnan(yv)]
            if len(pts) < 2:
                assert np.isnan(tend[r]) and np.isnan(avg[r])
            else:
                xs_, ys_ = zip(*pts)
                assert np.isclose(tend[r], np.polyfit(xs_, ys_, 1)[0], rtol=1e-7, atol=1e-7), (c, r)
                assert np.isclose(avg[r], np.mean(ys_), rtol=1e-9, atol=1e-9), (c, r)
    log("  verificación de tend3 y avg3 contra np.polyfit: OK")

    # variables _zero: solo para originales que alguna vez valen cero (NaN == 0 es False)
    cols_zero = [c for c in cols if (df[c].to_numpy() == 0).any()]
    log(f"  variables que alguna vez valen cero (llevan _zero): {len(cols_zero)} de {len(cols)}")

    # ------------------------------------------------------------------ 5) historia + ranking
    nombres, arrays, grupos = [], [], {}
    for c in NO_RANKEAR:
        if c == "numero_de_cliente":
            arr = df[c].to_numpy().astype("float64")      # float64: los IDs no entran en float32
        elif c == "foto_mes":
            arr = df[c].to_numpy().astype("int32")
        elif c == "clase_ternaria":
            arr = pa.array(df[c], type=pa.string(), from_pandas=True)   # NaN -> nulo
        else:
            arr = df[c].to_numpy().astype("float32")
        nombres.append(c)
        arrays.append(arr if isinstance(arr, pa.Array) else pa.array(arr))

    def agregar(nombre, valores, grupo):
        r = rank_cero_fijo(valores, idx_mes)
        # chequeos baratos: mismo patrón de NA, mismo signo, el cero se conserva
        assert np.array_equal(np.isnan(r), np.isnan(valores)), f"{nombre}: cambió el patrón de NA"
        ok = ~np.isnan(valores)
        assert np.all(np.sign(r[ok]) == np.sign(valores[ok])), f"{nombre}: cambió el signo/cero"
        nombres.append(nombre)
        arrays.append(pa.array(r))
        grupos.setdefault(grupo, []).append(nombre)

    zeros_sin_rank = []                                   # (nombre, array float32): no se rankean
    for j, c in enumerate(cols):
        x = df[c].to_numpy()                              # float64
        agregar(c, x, "original")
        if c not in SIN_HISTORIA:
            l1, l2 = aplicar_lag(x, pos[1]), aplicar_lag(x, pos[2])
            agregar(f"{c}_lag1", l1, "lag1")
            agregar(f"{c}_delta1", x - l1, "delta1")
            agregar(f"{c}_lag2", l2, "lag2")
            agregar(f"{c}_delta2", x - l2, "delta2")
            tend, avg = tendencia_promedio(x, l1, l2)
            agregar(f"{c}_tend3", tend, "tend3")
            agregar(f"{c}_avg3", avg, "avg3")
        if c in cols_zero:
            fz = flag_zero(x)
            assert np.array_equal(np.isnan(fz), np.isnan(x)) and np.array_equal(fz[~np.isnan(x)] == 1, x[~np.isnan(x)] == 0)
            nombres.append(f"{c}_zero")
            arrays.append(pa.array(fz))
            grupos.setdefault("zero", []).append(f"{c}_zero")
        if (j + 1) % 20 == 0:
            log(f"  columnas procesadas: {j + 1}/{len(cols)}")

    n_feat = len(nombres) - len(NO_RANKEAR)
    log(f"  features finales: {n_feat}  " + str({g: len(v) for g, v in grupos.items()}))
    assert n_feat == 152 + 142 * 6 + len(cols_zero), n_feat
    # ccajas_depositos de 202105 debe haber quedado en NA (original y flag _zero)
    for nom in (COL_ROTA, f"{COL_ROTA}_zero"):
        assert np.isnan(arrays[nombres.index(nom)].to_numpy(zero_copy_only=False)[mes == MES_ROTO]).all(), nom

    # ------------------------------------------------------------------ 6) escritura
    tabla = pa.Table.from_arrays(arrays, names=nombres)
    tmp = ruta_pq + ".tmp"
    pq.write_table(tabla, tmp, compression="zstd")
    os.replace(tmp, ruta_pq)
    log(f"parquet escrito: {ruta_pq}  ({os.path.getsize(ruta_pq) / 1e9:.2f} GB, {n:,} filas x {len(nombres)} columnas)")

    manifest = dict(volumen=a.volumen, entrada=a.entrada, filas=n, columnas=len(nombres),
                    sin_historia=SIN_HISTORIA, no_rankeadas=NO_RANKEAR + [f"{c}_zero" for c in cols_zero],
                    variables_con_zero=cols_zero,
                    grupos={g: len(v) for g, v in grupos.items()},
                    ccajas_depositos_NA_en=MES_ROTO,
                    ranking="cero fijo con signo, por variable y por mes (rank average / n); _zero sin rankear",
                    ventana_tendencia=3,
                    columnas_features=[c for c in nombres if c not in NO_RANKEAR])
    with open(os.path.join(dir_exp, f"{a.volumen}_dataset_manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)

    if not a.sin_bucket:
        gsutil("cp", ruta_pq, f"{BUCKET}/datasets/{a.volumen}_dataset.parquet")
        gsutil("-m", "rsync", "-r", dir_exp, f"{BUCKET}/exp/{a.volumen}")
    log(f"listo en {(time.time() - t00) / 60:.1f} min")


if __name__ == "__main__":
    main()
