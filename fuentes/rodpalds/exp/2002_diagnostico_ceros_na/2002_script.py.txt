"""
02b_diagnostico_ceros_na.py
DMEyF 2026 - Primera Competencia - Experimento 2002

Pregunta del profesor: ¿los NA y los ceros tienen significado? (el "proceso de muerte" del
cliente: deja primero las tarjetas, despues otros servicios).

Para cada variable, en los meses con clase completa, separa a los clientes en cuatro grupos:
  NA, cero, negativo, positivo
y calcula en cada grupo la tasa de BAJA+2 y el "lift" (tasa del grupo / tasa general).
Un lift alto en el grupo NA o cero significa que NO tener ese producto o movimiento ya es
una senal de baja.

Ademas, para los clientes BAJA+2, mira cuantos meses antes de irse cada producto clave
quedo en cero o vacio (el orden en que "se apagan").

Uso:  py -3.12 02b_diagnostico_ceros_na.py   (despues de 01_preparar_dataset.py)
"""

print("Arrancando 02b_diagnostico_ceros_na.py ...", flush=True)

import numpy as np
import pandas as pd

from exp_utils import DIR_DATA, cerrar_experimento, iniciar_experimento

PARAM = {
    "experimento": 2002,
    "nombre": "diagnostico_ceros_na",
    "descripcion": "Tasa de BAJA+2 segun la variable sea NA, cero, negativa o positiva (meses con clase "
                   "completa) y orden en que los BAJA+2 apagan sus productos.",
    "dataset": "ds1001_base.parquet",
    "meses": [202103, 202104, 202105, 202106],
    "min_clientes_grupo": 500,          # grupos mas chicos se informan pero no entran al ranking
    "productos_clave": ["ctarjeta_visa_transacciones", "ctarjeta_master_transacciones",
                        "mtarjeta_visa_consumo", "mpayroll", "mcuentas_saldo", "chomebanking_transacciones",
                        "cmobile_app_trx", "mprestamos_personales", "ctrx_quarter", "cproductos"],
}

exp = iniciar_experimento(PARAM)
NO_FEATURES = {"numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"}

df = pd.read_parquet(DIR_DATA / PARAM["dataset"], filters=[("foto_mes", "in", PARAM["meses"])])
features = [c for c in df.columns if c not in NO_FEATURES]
baja2 = (df["clase_ternaria"].astype(str) == "BAJA+2").to_numpy()
tasa_general = baja2.mean()
print(f"{len(df):,} filas | {len(features)} variables | tasa general de BAJA+2: {tasa_general:.3%}")

# ---------------------------------------------------------------------------
# 1) tasa de BAJA+2 por grupo NA / cero / negativo / positivo
# ---------------------------------------------------------------------------
filas = []
for c in features:
    x = df[c].to_numpy(dtype="float64")
    grupos = {"NA": np.isnan(x), "cero": x == 0, "negativo": x < 0, "positivo": x > 0}
    for g, m in grupos.items():
        n = int(m.sum())
        if n == 0:
            continue
        tasa = baja2[m].mean()
        filas.append({"variable": c, "grupo": g, "clientes": n, "pct_clientes": round(100 * n / len(x), 2),
                      "baja2": int(baja2[m].sum()), "tasa_baja2_pct": round(100 * tasa, 3),
                      "lift": round(tasa / tasa_general, 2)})
tabla = pd.DataFrame(filas)
tabla.to_csv(exp.ruta("tasa_por_grupo"), index=False)

ok = tabla[tabla["clientes"] >= PARAM["min_clientes_grupo"]]
top_na_cero = (ok[ok["grupo"].isin(["NA", "cero"])].sort_values("lift", ascending=False).head(25))
print("\n=== Variables donde estar en NA o en cero mas se asocia a la baja (lift = tasa del grupo / tasa general) ===")
print(top_na_cero.to_string(index=False))

# resumen por variable: lift de cada grupo en una fila
pivote = ok.pivot(index="variable", columns="grupo", values="lift")
pivote["max_lift_na_o_cero"] = pivote.reindex(columns=["NA", "cero"]).max(axis=1)
pivote = pivote.sort_values("max_lift_na_o_cero", ascending=False)
pivote.to_csv(exp.ruta("lift_por_variable"))
n_senal = int((pivote["max_lift_na_o_cero"] >= 2).sum())
print(f"\nVariables donde NA o cero multiplica por 2 o mas la tasa de baja: {n_senal} de {len(pivote)}")

# ---------------------------------------------------------------------------
# 2) "proceso de muerte": cuantos meses antes de irse cada producto quedo en cero/NA
# ---------------------------------------------------------------------------
claves = [c for c in PARAM["productos_clave"] if c in features]
if claves:
    todo = pd.read_parquet(DIR_DATA / PARAM["dataset"], columns=["numero_de_cliente", "foto_mes", "clase_ternaria"] + claves)
    todo = todo.sort_values(["numero_de_cliente", "foto_mes"])
    # ultimo mes de cada cliente que alguna vez fue BAJA+2 (la foto dos meses antes de irse)
    b2 = todo[todo["clase_ternaria"].astype(str) == "BAJA+2"][["numero_de_cliente", "foto_mes"]]
    b2 = b2.rename(columns={"foto_mes": "mes_baja2"})
    hist = todo.merge(b2, on="numero_de_cliente")
    per = lambda m: (m // 100) * 12 + m % 100
    hist["meses_antes"] = per(hist["mes_baja2"]) - per(hist["foto_mes"])
    hist = hist[hist["meses_antes"].between(0, 3)]
    filas2 = []
    for c in claves:
        apagado = hist[c].isna() | (hist[c] == 0)
        por_mes = apagado.groupby(hist["meses_antes"]).mean().mul(100).round(1)
        filas2.append({"variable": c, **{f"{k}_meses_antes": por_mes.get(k, np.nan) for k in (3, 2, 1, 0)}})
    muerte = pd.DataFrame(filas2).sort_values("3_meses_antes", ascending=False)
    muerte.to_csv(exp.ruta("proceso_de_muerte"), index=False)
    print("\n=== % de clientes BAJA+2 con el producto en cero o vacio, segun meses antes de la foto BAJA+2 ===")
    print("(0 = el mes de la foto, dos meses antes de irse; 3 = tres meses antes de esa foto)")
    print(muerte.to_string(index=False))

cerrar_experimento(exp, {"tasa_general_baja2": round(float(tasa_general), 5),
                         "variables_con_lift_na_o_cero_mayor_2": n_senal})
