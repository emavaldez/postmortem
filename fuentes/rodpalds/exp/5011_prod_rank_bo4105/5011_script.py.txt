"""
07_modelo_final.py
DMEyF 2026 - Primera Competencia - Experimentos 5xxx

Modelo final con SEMILLERIO: el mismo LightGBM entrenado con muchas semillas; se promedian
las probabilidades y se ordena a los clientes por ese promedio.

Dos modos (PARAM["modo"]):
  "simulacion"  -> aplica la receta sobre un mes CON clase conocida y mide la ganancia por
                   cantidad de envios, comparando el semillerio contra una semilla sola.
  "produccion"  -> entrena con los meses finales, predice el mes de Kaggle y genera un
                   archivo de entrega por cada cantidad de envios.

Hiperparametros (PARAM["hiperparametros"]):
  "z601"                                              -> los del notebook z601 de la catedra
  {"bo": "4101_bo_crudo_p95", "prueba": 73}            -> una prueba de una Optimizacion Bayesiana
  {"eleccion": "4102_bo_fuera_de_tiempo/4102_eleccion.json"} -> lo que eligio el script 08

Uso:  python 07_modelo_final.py                      (usa el PARAM de abajo)
      python 07_modelo_final.py configs/5003.json    (el JSON reemplaza las claves que trae)
"""

print("Arrancando 07_modelo_final.py ...", flush=True)

import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pyarrow.parquet as pq

from exp_utils import DIR_DATA, DIR_EXP, cerrar_experimento, iniciar_experimento

# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 5001,
    "nombre": "sim_z601_p95",
    "descripcion": "Simulacion: semillerio 20 semillas, params z601, crudo + binaria2, "
                   "variables p95. Train 202104 -> junio.",
    "modo": "simulacion",                     # "simulacion" o "produccion"
    "dataset": "ds3001_crudo.parquet",
    # archivo con la lista de variables, o None para usar todas (lag2/delta2 solo si usar_lag2)
    "variables": "4003_canaritos/4003_variables_p95.txt",
    "hiperparametros": "z601",                # o {"bo": "4101_bo_crudo_p95", "prueba": 73}
    # simulacion: [202104] -> 202106     produccion: [202104, 202105, 202106] -> 202108
    "meses_train": [202104],
    "mes_prediccion": 202106,
    "clase": "clase_binaria2",
    # min_data_in_leaf se escala por FILAS: si se entrena con mas filas que las usadas al
    # elegir los hiperparametros, cada hoja sigue representando la misma proporcion de clientes
    "escalar_min_data_in_leaf": True,
    "n_semillas": 20,                         # las 5 tuyas + primos generados a partir de la primera
    "semillas_base": [571369, 849571, 355049, 655531, 700103],
    "envios": list(range(12000, 19001, 500)),
    "meseta": [12000, 17000],                 # rango para la ganancia promedio "de meseta"
    "ganancia_acierto": 1_072_500,
    "costo_estimulo": 27_500,
}

if len(sys.argv) > 1:
    config = Path(sys.argv[1])
    PARAM.update(json.loads(config.read_text(encoding="utf-8")))
    PARAM["_config"] = config.name
    print(f"Configuracion tomada de {config}")

exp = iniciar_experimento(PARAM)
NO_FEATURES = {"numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"}

# parametros que hacen el resultado identico en cualquier maquina
REPRODUCIBLE = {"deterministic": True, "force_row_wise": True, "verbose": -1}

HIPER_Z601 = {
    "params": {
        "objective": "binary", "boosting_type": "gbdt", "max_bin": 31, "num_leaves": 16,
        "learning_rate": 0.019868, "min_data_in_leaf": 816, "feature_fraction": 0.277155,
        "bagging_fraction": 0.634130, "bagging_freq": 1, "feature_pre_filter": False,
    },
    "arboles": 250,
    "fraccion_mes_referencia": 1.0,           # se eligieron entrenando con un mes completo
}

# ---------------------------------------------------------------------------
# Semillas
# ---------------------------------------------------------------------------
def es_primo(n):
    if n < 2 or n % 2 == 0:
        return n == 2
    return all(n % d for d in range(3, int(n ** 0.5) + 1, 2))


semillas = list(PARAM["semillas_base"])
rng = np.random.default_rng(PARAM["semillas_base"][0])
while len(semillas) < PARAM["n_semillas"]:
    candidato = int(rng.integers(100003, 999983))
    if es_primo(candidato) and candidato not in semillas:
        semillas.append(candidato)
semillas = semillas[:PARAM["n_semillas"]]
pd.Series(semillas, name="semilla").to_csv(exp.ruta("semillas"), index=False)

# ---------------------------------------------------------------------------
# Hiperparametros
# ---------------------------------------------------------------------------
if PARAM["hiperparametros"] == "z601":
    params = dict(HIPER_Z601["params"])
    arboles = HIPER_Z601["arboles"]
    fraccion_ref = HIPER_Z601["fraccion_mes_referencia"]
    origen = "z601"
elif "eleccion" in PARAM["hiperparametros"]:
    eleccion = json.loads((DIR_EXP / PARAM["hiperparametros"]["eleccion"]).read_text(encoding="utf-8"))
    params = dict(eleccion["params"])
    arboles = int(eleccion["arboles"])
    fraccion_ref = float(eleccion["fraccion_mes_referencia"])
    origen = f"eleccion: {eleccion['origen']}"
else:
    carpeta_bo = DIR_EXP / PARAM["hiperparametros"]["bo"]
    id_bo = carpeta_bo.name.split("_")[0]
    param_bo = json.loads((carpeta_bo / f"{id_bo}_PARAM.json").read_text(encoding="utf-8"))
    pruebas = pd.read_csv(carpeta_bo / f"{id_bo}_pruebas.csv")
    pruebas = pruebas[pruebas["state"] == "COMPLETE"]
    fila = pruebas[pruebas["number"] == PARAM["hiperparametros"]["prueba"]]
    if fila.empty:
        raise ValueError(f"No existe la prueba {PARAM['hiperparametros']['prueba']} completa en {id_bo}")
    fila = fila.iloc[0]
    buscados = {c.removeprefix("params_"): fila[c] for c in pruebas.columns if c.startswith("params_")}
    # fijos (max_bin, bagging_freq, ...) desde el PARAM de la BO: sin ellos seria otro modelo
    fijos = {k: v for k, v in param_bo["lgbm_fijos"].items()
             if k not in ("metric", "first_metric_only", "verbose")}
    params = {**fijos, **buscados}
    arboles = int(fila["user_attrs_best_iter"])
    # la BO entreno cada fold con (k-1)/k del mes
    fraccion_ref = (param_bo["cv_folds"] - 1) / param_bo["cv_folds"]
    origen = f"{id_bo} prueba {PARAM['hiperparametros']['prueba']}"
for k in ("num_leaves", "min_data_in_leaf", "max_bin", "bagging_freq"):
    if k in params:
        params[k] = int(params[k])
assert params.get("bagging_freq", 0) >= 1, "bagging_freq tiene que ser >= 1 o bagging_fraction no actua"
params.update(REPRODUCIBLE)

# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
t0 = time.time()
archivo = DIR_DATA / PARAM["dataset"]
if PARAM["variables"]:
    features = (DIR_EXP / PARAM["variables"]).read_text(encoding="utf-8").split()
else:
    features = [c for c in pq.ParquetFile(archivo).schema_arrow.names
                if c not in NO_FEATURES
                and (PARAM.get("usar_lag2", False) or not (c.endswith("_lag2") or c.endswith("_delta2")))]
if not PARAM.get("usar_lag2", False):
    assert not any(f.endswith(("_lag2", "_delta2")) for f in features), \
        "Hay lag2/delta2 en la lista: poner \"usar_lag2\": true si es intencional"
assert not set(features) & NO_FEATURES, "Hay columnas de id o de clase entre las variables"

meses = PARAM["meses_train"] + [PARAM["mes_prediccion"]]
df = pd.read_parquet(archivo, columns=["numero_de_cliente", "foto_mes", "clase_ternaria", PARAM["clase"]] + features,
                     filters=[("foto_mes", "in", meses)])
train = df[df["foto_mes"].isin(PARAM["meses_train"])]
pred = df[df["foto_mes"] == PARAM["mes_prediccion"]].reset_index(drop=True)
del df

assert sorted(train["foto_mes"].unique()) == sorted(PARAM["meses_train"]), "Faltan meses de train"
assert train[PARAM["clase"]].notna().all(), "Hay filas de train sin clase (¿se colo 202107?)"
assert len(pred) > 0, "No hay filas en el mes de prediccion"
print(f"Hiperparametros: {origen} | {arboles} arboles")
print(f"{len(features)} variables | train {len(train):,} filas {PARAM['meses_train']} | "
      f"prediccion {len(pred):,} filas ({PARAM['mes_prediccion']}) ({time.time() - t0:.0f} s)")

if PARAM["escalar_min_data_in_leaf"]:
    filas_por_mes = len(train) / len(PARAM["meses_train"])
    factor = len(train) / (filas_por_mes * fraccion_ref)
    original = params["min_data_in_leaf"]
    params["min_data_in_leaf"] = int(round(original * factor))
    print(f"min_data_in_leaf: {original} x {factor:.2f} (por filas) = {params['min_data_in_leaf']}")

with open(exp.ruta("params_lightgbm", ext="json"), "w", encoding="utf-8") as f:
    json.dump({"origen": origen, "arboles": arboles, "params": params}, f, indent=2)

dtrain = lgb.Dataset(train[features], label=train[PARAM["clase"]].astype(int).to_numpy())
X_pred = pred[features]
del train

# ---------------------------------------------------------------------------
# Semillerio
# ---------------------------------------------------------------------------
simulacion = PARAM["modo"] == "simulacion"
if simulacion:
    baja2 = (pred["clase_ternaria"].astype(str) == "BAJA+2").to_numpy()
    lo, hi = PARAM["meseta"]


def curva(prob):
    """Ganancia acumulada para cada cantidad de envios entre 1 y el total."""
    orden = np.argsort(-prob, kind="stable")
    return np.cumsum(np.where(baja2[orden], PARAM["ganancia_acierto"], -PARAM["costo_estimulo"]))


suma = np.zeros(len(pred))
filas = []
por_semilla = {}       # se llena solo si PARAM["guardar_prob_por_semilla"]
print(f"\n=== Semillerio: {len(semillas)} semillas ===")
for i, semilla in enumerate(semillas, start=1):
    t = time.time()
    modelo = lgb.train(dict(params, seed=semilla), dtrain, num_boost_round=arboles)
    prob = modelo.predict(X_pred)
    suma += prob
    if PARAM.get("guardar_prob_por_semilla", False):
        por_semilla[f"s{semilla}"] = prob.astype("float32")
    linea = f"  semilla {i:2d}/{len(semillas)} ({semilla}) {time.time() - t:.0f} s"
    if simulacion:
        c_ind, c_acu = curva(prob), curva(suma / i)
        for e in PARAM["envios"]:
            filas.append({"semillas_promediadas": i, "semilla": semilla, "envios": e,
                          "ganancia_esta_semilla": c_ind[e - 1], "ganancia_semillerio": c_acu[e - 1]})
        filas.append({"semillas_promediadas": i, "semilla": semilla, "envios": "meseta",
                      "ganancia_esta_semilla": c_ind[lo - 1:hi].mean(),
                      "ganancia_semillerio": c_acu[lo - 1:hi].mean()})
        linea += (f" | semillerio hasta aca: meseta {c_acu[lo - 1:hi].mean() / 1e6:.1f} M, "
                  f"maximo {c_acu[PARAM['envios'][0] - 1:PARAM['envios'][-1]].max() / 1e6:.1f} M")
    print(linea, flush=True)
    if i == 1:
        imp = pd.DataFrame({"variable": features, "gain": modelo.feature_importance("gain")})
        imp.sort_values("gain", ascending=False).to_csv(exp.ruta("importancia"), index=False)

prob_final = suma / len(semillas)
salida_prob = pd.DataFrame({"numero_de_cliente": pred["numero_de_cliente"].astype("int64"), "prob": prob_final})
if simulacion:
    salida_prob["clase_ternaria"] = pred["clase_ternaria"].astype(str).to_numpy()
salida_prob.to_csv(exp.ruta("probabilidades"), index=False)
if por_semilla:
    pd.DataFrame({"numero_de_cliente": pred["numero_de_cliente"].astype("int64"), **por_semilla}) \
        .to_parquet(exp.ruta("prob_por_semilla", ext="parquet"), index=False)
    print(f"Probabilidades de cada semilla grabadas ({len(por_semilla)} columnas)")
resultados = {"hiperparametros": origen, "arboles": arboles,
              "min_data_in_leaf": params["min_data_in_leaf"], "n_semillas": len(semillas)}

# ---------------------------------------------------------------------------
# Salidas
# ---------------------------------------------------------------------------
if simulacion:
    detalle = pd.DataFrame(filas)
    detalle.to_csv(exp.ruta("ganancia_por_envios"), index=False)
    final = detalle[detalle["semillas_promediadas"] == len(semillas)].set_index("envios")
    individual = detalle.groupby("envios")["ganancia_esta_semilla"].agg(["mean", "std"])
    tabla = pd.DataFrame({
        "semillerio_M": final["ganancia_semillerio"] / 1e6,
        "semilla_sola_media_M": individual["mean"] / 1e6,
        "semilla_sola_desvio_M": individual["std"] / 1e6,
    }).astype(float).round(1)
    tabla.index = tabla.index.astype(str)
    tabla.to_csv(exp.ruta("resumen"))
    print(f"\n=== Ganancia en {PARAM['mes_prediccion']} (millones) ===")
    print(tabla.to_string())
    solo_envios = tabla.drop(index="meseta")
    mejor = solo_envios["semillerio_M"].idxmax()
    print(f"\nSemillerio: maximo {solo_envios.loc[mejor, 'semillerio_M']} M en {int(mejor):,} envios "
          f"({int(mejor) / len(pred):.1%} de los clientes); meseta {lo:,}-{hi:,}: "
          f"{tabla.loc['meseta', 'semillerio_M']} M.")
    print(f"Una semilla sola (promedio de {len(semillas)}): meseta {tabla.loc['meseta', 'semilla_sola_media_M']} M "
          f"(desvio {tabla.loc['meseta', 'semilla_sola_desvio_M']} M).")
    resultados.update({
        "mejor_envios": int(mejor), "proporcion_envios": round(int(mejor) / len(pred), 4),
        "maximo_semillerio_M": float(solo_envios.loc[mejor, "semillerio_M"]),
        "meseta_semillerio_M": float(tabla.loc["meseta", "semillerio_M"]),
        "meseta_semilla_sola_M": float(tabla.loc["meseta", "semilla_sola_media_M"]),
    })

    evol = detalle[detalle["envios"] == "meseta"].set_index("semillas_promediadas")["ganancia_semillerio"] / 1e6
    fig = go.Figure(go.Scatter(x=evol.index, y=evol.values, mode="lines+markers",
                               line=dict(color="#6C5CE7", width=4, shape="spline"), marker=dict(size=9)))
    fig.update_layout(
        title=dict(text=f"<b>Ganancia de meseta ({lo:,}-{hi:,} envios) segun semillas promediadas</b>", x=0.02),
        font=dict(family="Inter, Segoe UI, Helvetica, sans-serif", size=14, color="#2d3436"),
        plot_bgcolor="white", paper_bgcolor="white", height=460,
        xaxis=dict(title="Semillas promediadas", gridcolor="#f1f2f6"),
        yaxis=dict(title="Ganancia (millones)", gridcolor="#f1f2f6"),
    )
    fig.write_html(exp.ruta("semillerio", ext="html"), include_plotlyjs="cdn")
else:
    carpeta_ka = exp.carpeta / "kaggle"
    carpeta_ka.mkdir(exist_ok=True)
    orden = np.argsort(-prob_final, kind="stable")
    ids = pred["numero_de_cliente"].astype("int64")
    assert ids.is_unique, "Hay clientes repetidos en el mes de prediccion"
    for e in PARAM["envios"]:
        predicted = np.zeros(len(pred), dtype=int)
        predicted[orden[:e]] = 1
        ka = pd.DataFrame({"numero_de_cliente": ids, "Predicted": predicted})
        assert list(ka.columns) == ["numero_de_cliente", "Predicted"]
        assert ka["Predicted"].sum() == e and set(ka["Predicted"].unique()) <= {0, 1}
        ka.to_csv(carpeta_ka / f"KA{exp.id}_e{e}.csv", index=False)
    print(f"\nArchivos para Kaggle en {carpeta_ka}: {len(PARAM['envios'])} archivos de "
          f"{len(pred):,} filas (de {min(PARAM['envios']):,} a {max(PARAM['envios']):,} envios)")
    pct = np.percentile(prob_final, [50, 90, 99]).round(4)
    print(f"Probabilidades en {PARAM['mes_prediccion']}: mediana {pct[0]}, p90 {pct[1]}, p99 {pct[2]}")
    resultados.update({"archivos_kaggle": len(PARAM["envios"]), "filas": len(pred),
                       "prob_p50_p90_p99": pct.tolist()})

cerrar_experimento(exp, resultados)
