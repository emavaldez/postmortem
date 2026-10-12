"""
11_comparar_pipelines.py
DMEyF 2026 - Primera Competencia - Experimento 5102

Compara pipelines completos (dataset + variables + hiperparametros) en la MITAD B de junio,
que ninguna busqueda uso para elegir:
  - cada candidato: semillerio entrenado con abril completo, curva de ganancia en la mitad B (x2)
  - bootstrap PAREADO de clientes de la mitad B contra la referencia
  - distribucion del corte optimo (proporcion de clientes -> envios en agosto)

Uso:  py -3.12 11_comparar_pipelines.py                          (PARAM de abajo, experimento 5102)
      py -3.12 11_comparar_pipelines.py configs\\5103_comparar_bo4105.json   (el JSON reemplaza claves)
"""

print("Arrancando 11_comparar_pipelines.py ...", flush=True)

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
    "experimento": 5102,
    "nombre": "comparar_pipelines",
    "descripcion": "Pipeline actual (crudo, p95, retador 4102) contra la receta del profesor (rank total con "
                   "lag2, todas las variables) con los hiperparametros del retador y con los de su propia BO "
                   "(4104). Semillerio de 20, train 202104, mitad B de 202106 (x2), bootstrap pareado.",
    "mitades": "4102_bo_fuera_de_tiempo/4102_mitades_junio.csv",
    "referencia": "actual_crudo_p95",
    "candidatos": {
        "actual_crudo_p95": {"dataset": "ds3001_crudo.parquet",
                             "variables": "4003_canaritos/4003_variables_p95.txt", "usar_lag2": False,
                             "hiperparametros": {"eleccion": "4102_bo_fuera_de_tiempo/4102_eleccion.json"}},
        "rank_total_p117": {"dataset": "ds3002_rank_total.parquet", "variables": None, "usar_lag2": True,
                            "hiperparametros": {"eleccion": "4102_bo_fuera_de_tiempo/4102_eleccion.json"}},
        "rank_total_bo4104": {"dataset": "ds3002_rank_total.parquet", "variables": None, "usar_lag2": True,
                              "hiperparametros": {"eleccion": "4104_bo_rank_total/4104_eleccion.json"}},
    },
    "mes_train": 202104,
    "mes_test": 202106,
    "clase": "clase_binaria2",
    "n_semillas": 20,
    "semillas_base": [571369, 849571, 355049, 655531, 700103],
    "envios": list(range(8000, 17001, 500)),      # equivalentes en el mes completo
    "meseta": [12000, 17000],
    "n_bootstrap": 1000,
    "ganancia_acierto": 1_072_500,
    "costo_estimulo": 27_500,
    "clientes_agosto": 164_647,
}

if len(sys.argv) > 1:
    config = Path(sys.argv[1])
    PARAM.update(json.loads(config.read_text(encoding="utf-8")))
    PARAM["_config"] = config.name
    print(f"Configuracion tomada de {config}")

exp = iniciar_experimento(PARAM)
GAN, COSTO = PARAM["ganancia_acierto"], PARAM["costo_estimulo"]
NO_FEATURES = {"numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"}
REPRODUCIBLE = {"deterministic": True, "force_row_wise": True, "verbose": -1}
Z601 = {"params": {"objective": "binary", "boosting_type": "gbdt", "max_bin": 31, "num_leaves": 16,
                   "learning_rate": 0.019868, "min_data_in_leaf": 816, "feature_fraction": 0.277155,
                   "bagging_fraction": 0.634130, "bagging_freq": 1, "feature_pre_filter": False},
        "arboles": 250, "origen": "z601"}


def es_primo(n):
    if n < 2 or n % 2 == 0:
        return n == 2
    return all(n % d for d in range(3, int(n ** 0.5) + 1, 2))


semillas = list(PARAM["semillas_base"])
rng = np.random.default_rng(PARAM["semillas_base"][0])
while len(semillas) < PARAM["n_semillas"]:
    c = int(rng.integers(100003, 999983))
    if es_primo(c) and c not in semillas:
        semillas.append(c)
semillas = semillas[:PARAM["n_semillas"]]

mitades = pd.read_csv(DIR_EXP / PARAM["mitades"])
ids_B = mitades.loc[mitades["mitad"] == "B", "numero_de_cliente"].astype("int64")
ENV = np.array(PARAM["envios"])
lo, hi = PARAM["meseta"]


def hiper(fuente):
    if fuente == "z601":
        return dict(Z601)
    archivo = DIR_EXP / fuente["eleccion"]
    if not archivo.exists():
        return None
    el = json.loads(archivo.read_text(encoding="utf-8"))
    return {"params": dict(el["params"]), "arboles": int(el["arboles"]), "origen": el["origen"],
            "fraccion_mes_referencia": float(el.get("fraccion_mes_referencia", 1.0))}


# ---------------------------------------------------------------------------
# Semillerio por candidato (mismos clientes de la mitad B, mismo orden)
# ---------------------------------------------------------------------------
probs = {}
info = {}
baja2B = None
orden_ids = None
for nombre, cand in PARAM["candidatos"].items():
    h = hiper(cand["hiperparametros"])
    if h is None:
        print(f"- {nombre}: falta {cand['hiperparametros']['eleccion']}, se saltea")
        continue
    t0 = time.time()
    archivo = DIR_DATA / cand["dataset"]
    if not archivo.exists():
        print(f"- {nombre}: falta {cand['dataset']}, se saltea")
        continue
    if cand["variables"]:
        features = (DIR_EXP / cand["variables"]).read_text(encoding="utf-8").split()
    else:
        features = [c for c in pq.ParquetFile(archivo).schema_arrow.names if c not in NO_FEATURES
                    and (cand["usar_lag2"] or not (c.endswith("_lag2") or c.endswith("_delta2")))]
    # cada candidato puede entrenar con otros meses ("meses_train"); por defecto PARAM["mes_train"]
    meses_c = list(cand.get("meses_train") or [PARAM["mes_train"]])
    assert PARAM["mes_test"] not in meses_c, "El mes de test no puede estar en train"
    df = pd.read_parquet(archivo, columns=["numero_de_cliente", "foto_mes", "clase_ternaria", PARAM["clase"]] + features,
                         filters=[("foto_mes", "in", meses_c + [PARAM["mes_test"]])])
    train = df[df["foto_mes"].isin(meses_c)]
    assert sorted(train["foto_mes"].unique()) == sorted(meses_c), f"{nombre}: faltan meses de train"
    testB = (df[(df["foto_mes"] == PARAM["mes_test"]) & df["numero_de_cliente"].isin(ids_B)]
             .sort_values("numero_de_cliente").reset_index(drop=True))
    del df
    if orden_ids is None:
        orden_ids = testB["numero_de_cliente"].astype("int64").to_numpy()
        baja2B = (testB["clase_ternaria"].astype(str) == "BAJA+2").to_numpy()
    assert np.array_equal(testB["numero_de_cliente"].astype("int64").to_numpy(), orden_ids), \
        "Los clientes de la mitad B no coinciden entre datasets"

    params = dict(h["params"])
    for k in ("num_leaves", "min_data_in_leaf", "max_bin", "bagging_freq"):
        if k in params:
            params[k] = int(params[k])
    params = {k: v for k, v in params.items() if k not in ("metric", "first_metric_only")}
    params.update(REPRODUCIBLE)
    # min_data_in_leaf por filas: los hiperparametros se eligieron con h["fraccion_mes_referencia"] meses
    factor = len(meses_c) / h.get("fraccion_mes_referencia", 1.0)
    if factor != 1.0:
        params["min_data_in_leaf"] = int(round(params["min_data_in_leaf"] * factor))
    if "min_data_in_leaf" in cand:                    # valor fijo para este candidato (pisa el escalado)
        params["min_data_in_leaf"] = int(cand["min_data_in_leaf"])
    dtrain = lgb.Dataset(train[features], label=train[PARAM["clase"]].astype(int).to_numpy(), free_raw_data=False)
    XB = testB[features]
    # "arboles_lista": se entrena una vez con el maximo y se predice cortando en cada cantidad
    iters = [int(k) for k in (cand.get("arboles_lista") or [h["arboles"]])]
    sumas = {k: np.zeros(len(testB)) for k in iters}
    for semilla in semillas:
        modelo = lgb.train(dict(params, seed=semilla), dtrain, num_boost_round=max(iters))
        for k in iters:
            sumas[k] += modelo.predict(XB, num_iteration=k)
    for k in iters:
        clave = nombre if len(iters) == 1 else f"{nombre}_a{k}"
        probs[clave] = sumas[k] / len(semillas)
        info[clave] = {"dataset": cand["dataset"], "variables": len(features), "hiper": h["origen"],
                       "arboles": k, "meses_train": " ".join(map(str, meses_c)),
                       "min_data_in_leaf": params["min_data_in_leaf"]}
    print(f"  {nombre}: {len(features)} variables, {h['origen']}, {len(semillas)} semillas, arboles {iters}, "
          f"min_data_in_leaf {params['min_data_in_leaf']} ({(time.time() - t0) / 60:.1f} min)", flush=True)
    del train, testB, dtrain, XB

if PARAM["referencia"] not in probs:
    raise RuntimeError("No se pudo calcular la referencia; revisar los archivos de entrada")

# ---------------------------------------------------------------------------
# Curvas (x2 = mes completo equivalente) y bootstrap pareado
# ---------------------------------------------------------------------------
g = np.where(baja2B, GAN, -COSTO).astype(float)
n = len(g)
E_meseta = np.arange(lo // 2, hi // 2 + 1)
E_curva = ENV // 2


def ganancia_en(orden, w, envios):
    wo, go_ = w[orden], g[orden]
    cw, cg = np.cumsum(wo), np.cumsum(wo * go_)
    pos = np.minimum(np.searchsorted(cw, envios, side="left"), n - 1)
    return 2 * (cg[pos] - (cw[pos] - envios) * go_[pos])


ordenes = {k: np.argsort(-p, kind="stable") for k, p in probs.items()}
uno = np.ones(n)
curvas = {k: ganancia_en(o, uno, E_curva) for k, o in ordenes.items()}
resumen = []
for k in probs:
    c = curvas[k]
    i = int(c.argmax())
    resumen.append({"modelo": k, **info[k], "meseta_M": round(ganancia_en(ordenes[k], uno, E_meseta).mean() / 1e6, 1),
                    "maximo_M": round(c[i] / 1e6, 1), "envios_optimos": int(ENV[i])})

rng_b = np.random.default_rng(20261011)
grilla = np.arange(3000, 9001, 50)        # en media poblacion
filas_b = []
for b in range(PARAM["n_bootstrap"]):
    w = np.bincount(rng_b.integers(0, n, n), minlength=n).astype(float)
    fila = {"b": b}
    for k, o in ordenes.items():
        fila[f"meseta_{k}"] = ganancia_en(o, w, E_meseta).mean()
        gg = ganancia_en(o, w, grilla)
        fila[f"corte_{k}"] = grilla[gg.argmax()] * 2
    filas_b.append(fila)
boot = pd.DataFrame(filas_b)
boot.to_csv(exp.ruta("bootstrap"), index=False)

ref = PARAM["referencia"]
for r in resumen:
    k = r["modelo"]
    prop = boot[f"corte_{k}"] / (2 * n)
    r["envios_agosto_p25_p50_p75"] = " / ".join(f"{q * PARAM['clientes_agosto']:,.0f}" for q in prop.quantile([.25, .5, .75]))
    if k != ref:
        d = (boot[f"meseta_{k}"] - boot[f"meseta_{ref}"]) / 1e6
        r[f"dif_vs_{ref}_M"] = round(d.mean(), 1)
        r["IC90_M"] = f"[{d.quantile(.05):.1f} ; {d.quantile(.95):.1f}]"
        r["pct_remuestreos_gana"] = f"{(d > 0).mean():.0%}"
tabla = pd.DataFrame(resumen).sort_values("meseta_M", ascending=False)
tabla.to_csv(exp.ruta("resumen"), index=False)
pd.DataFrame({"envios": ENV, **{k: np.round(v / 1e6, 1) for k, v in curvas.items()}}).to_csv(exp.ruta("curvas"), index=False)
pd.DataFrame({"numero_de_cliente": orden_ids, "baja2": baja2B.astype(int), **probs}) \
    .to_csv(exp.ruta("probabilidades_mitad_B"), index=False)

print(f"\n=== Mitad B de junio (x2), semillerio de {len(semillas)}. Referencia: {ref} ===")
print(tabla.to_string(index=False))
print("\nCurva por envios (millones):")
print(pd.read_csv(exp.ruta("curvas")).to_string(index=False))

COLORES = ["#B2BEC3", "#6C5CE7", "#00B894", "#FDCB6E"]
fig = go.Figure()
for (k, c), color in zip(curvas.items(), COLORES):
    fig.add_scatter(x=ENV, y=c / 1e6, mode="lines", name=k, line=dict(color=color, width=4, shape="spline"))
fig.update_layout(
    title=dict(text="<b>Ganancia en la mitad B de junio (x2) segun envios</b>", x=0.02),
    font=dict(family="Inter, Segoe UI, Helvetica, sans-serif", size=14, color="#2d3436"),
    plot_bgcolor="white", paper_bgcolor="white", height=520,
    xaxis=dict(title="Envios equivalentes en el mes completo", gridcolor="#f1f2f6"),
    yaxis=dict(title="Ganancia (millones)", gridcolor="#f1f2f6"),
    legend=dict(orientation="h", y=-0.18, x=0), hovermode="x unified",
)
fig.write_html(exp.ruta("curvas", ext="html"), include_plotlyjs="cdn")

cerrar_experimento(exp, {"resumen": tabla.to_dict("records")})
