"""
05_canaritos.py
DMEyF 2026 - Primera Competencia - Experimento 4003

Seleccion de variables con canaritos, y evaluacion de la seleccion por ganancia.

Paso 1 - Diagnostico: se agregan columnas de puro azar ("canaritos") al dataset de
         entrenamiento, se entrena LightGBM con varias semillas y se mide la importancia
         (gain) de cada variable. Una variable que no supera a los canaritos le aporta al
         modelo lo mismo que el ruido.
Paso 2 - Evaluacion: se entrena SIN canaritos con tres conjuntos de variables
         (todas / superan al percentil 95 de los canaritos / superan al mejor canarito)
         y se compara la ganancia en el mes de test, con varias semillas.

Uso:  python 05_canaritos.py
"""

print("Arrancando 05_canaritos.py ...", flush=True)

import time

import lightgbm as lgb
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pyarrow.parquet as pq

from exp_utils import DIR_DATA, cerrar_experimento, iniciar_experimento

# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 4003,
    "nombre": "canaritos",
    "descripcion": "Canaritos sobre crudo + binaria2 (train 202104). Compara todas las variables "
                   "vs las que superan el p95 de los canaritos vs las que superan al mejor canarito.",
    "dataset": "ds3001_crudo.parquet",
    "mes_train": 202104,
    "mes_test": 202106,
    "clase": "clase_binaria2",
    "usar_lag2": False,
    "n_canaritos": 100,
    "semillas": [571369, 849571, 355049, 655531, 700103],
    "num_boost_round": 250,
    "lgbm": {
        "objective": "binary",
        "boosting_type": "gbdt",
        "max_bin": 31,
        "num_leaves": 16,
        "learning_rate": 0.019868,
        "min_data_in_leaf": 816,
        "feature_fraction": 0.277155,
        "bagging_fraction": 0.634130,
        "bagging_freq": 1,
        "feature_pre_filter": False,
        "verbose": -1,
    },
    "ganancia_acierto": 1_072_500,
    "costo_estimulo": 27_500,
    "cortes": {"desde": 2000, "hasta": 20000, "paso": 500},
}

exp = iniciar_experimento(PARAM)

NO_FEATURES = {"numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"}
CORTES = np.arange(PARAM["cortes"]["desde"], PARAM["cortes"]["hasta"] + 1, PARAM["cortes"]["paso"])

# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
t0 = time.time()
archivo = DIR_DATA / PARAM["dataset"]
columnas = pq.ParquetFile(archivo).schema_arrow.names
if not PARAM["usar_lag2"]:
    columnas = [c for c in columnas if not (c.endswith("_lag2") or c.endswith("_delta2"))]
df = pd.read_parquet(archivo, columns=columnas,
                     filters=[("foto_mes", "in", [PARAM["mes_train"], PARAM["mes_test"]])])
features = [c for c in df.columns if c not in NO_FEATURES]
train = df[df["foto_mes"] == PARAM["mes_train"]].reset_index(drop=True)
test = df[df["foto_mes"] == PARAM["mes_test"]].reset_index(drop=True)
del df
y_train = train[PARAM["clase"]].astype(int).to_numpy()
ternaria_test = test["clase_ternaria"].astype(str).to_numpy()
print(f"{len(features)} variables | train {len(train):,} filas | test {len(test):,} filas "
      f"({time.time() - t0:.0f} s)")


def curva_ganancia(prob):
    orden = np.argsort(-prob, kind="stable")
    g = np.where(ternaria_test[orden] == "BAJA+2", PARAM["ganancia_acierto"], -PARAM["costo_estimulo"])
    acumulada = np.cumsum(g)
    return acumulada[np.minimum(CORTES, len(acumulada)) - 1]


# ---------------------------------------------------------------------------
# Paso 1: diagnostico con canaritos
# ---------------------------------------------------------------------------
print(f"\n=== Paso 1: {PARAM['n_canaritos']} canaritos, {len(PARAM['semillas'])} semillas ===")
nombres_can = [f"canarito_{i:03d}" for i in range(PARAM["n_canaritos"])]
importancias = []
for semilla in PARAM["semillas"]:
    rng = np.random.default_rng(semilla)
    canaritos = pd.DataFrame(rng.uniform(0, 1, (len(train), PARAM["n_canaritos"])).astype("float32"),
                             columns=nombres_can)
    X = pd.concat([train[features], canaritos], axis=1)
    modelo = lgb.train(dict(PARAM["lgbm"], seed=semilla), lgb.Dataset(X, label=y_train),
                       num_boost_round=PARAM["num_boost_round"])
    gain = pd.Series(modelo.feature_importance("gain"), index=X.columns)
    importancias.append(gain / gain.sum())          # normalizado: comparable entre semillas
    print(f"  semilla {semilla}: mejor canarito en el puesto "
          f"{int(gain.rank(ascending=False)[nombres_can].min())} de {len(gain)}")
    del X, canaritos

imp = pd.concat(importancias, axis=1).mean(axis=1).rename("gain_medio").to_frame()
imp["es_canarito"] = imp.index.str.startswith("canarito_")
gain_can = imp.loc[imp["es_canarito"], "gain_medio"]
umbral_p95 = gain_can.quantile(0.95)
umbral_max = gain_can.max()
reales = imp[~imp["es_canarito"]].copy()
reales["supera_p95"] = reales["gain_medio"] > umbral_p95
reales["supera_max"] = reales["gain_medio"] > umbral_max
reales = reales.sort_values("gain_medio", ascending=False)
reales["puesto"] = np.arange(1, len(reales) + 1)
reales.drop(columns="es_canarito").to_csv(exp.ruta("importancia_variables"), index_label="variable")

conjuntos = {
    "todas": features,
    "p95": reales.index[reales["supera_p95"]].tolist(),
    "max": reales.index[reales["supera_max"]].tolist(),
}
print(f"\nVariables que superan al percentil 95 de los canaritos: {len(conjuntos['p95'])} de {len(features)}")
print(f"Variables que superan al mejor canarito:             {len(conjuntos['max'])} de {len(features)}")
print(f"Variables con importancia cero (nunca usadas):       {(reales['gain_medio'] == 0).sum()}")
for nombre in ("p95", "max"):
    with open(exp.ruta(f"variables_{nombre}", ext="txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(conjuntos[nombre]))

# ---------------------------------------------------------------------------
# Paso 2: evaluacion por ganancia de cada conjunto (sin canaritos)
# ---------------------------------------------------------------------------
print(f"\n=== Paso 2: ganancia en {PARAM['mes_test']} con cada conjunto de variables ===")
filas = []
for nombre, vars_ in conjuntos.items():
    if not vars_:
        print(f"  {nombre}: sin variables, se saltea")
        continue
    dtrain = lgb.Dataset(train[vars_], label=y_train)
    for semilla in PARAM["semillas"]:
        modelo = lgb.train(dict(PARAM["lgbm"], seed=semilla), dtrain,
                           num_boost_round=PARAM["num_boost_round"])
        curva = curva_ganancia(modelo.predict(test[vars_]))
        filas += [{"conjunto": nombre, "n_variables": len(vars_), "semilla": semilla,
                   "corte": c, "ganancia": g} for c, g in zip(CORTES, curva)]
    print(f"  {nombre} ({len(vars_)} variables): listo")

detalle = pd.DataFrame(filas)
detalle.to_csv(exp.ruta("ganancia_por_corte_y_semilla"), index=False)
media = detalle.groupby(["conjunto", "corte"])["ganancia"].agg(["mean", "std", "min", "max"]).reset_index()

resumen = []
gan_todas = None
for nombre in conjuntos:
    m = media[media["conjunto"] == nombre]
    if m.empty:
        continue
    mejor = m.loc[m["mean"].idxmax()]
    por_sem = detalle[(detalle["conjunto"] == nombre) & (detalle["corte"] == mejor["corte"])] \
        .set_index("semilla")["ganancia"]
    if nombre == "todas":
        gan_todas = por_sem
    resumen.append({
        "conjunto": nombre,
        "n_variables": len(conjuntos[nombre]),
        "corte_optimo": int(mejor["corte"]),
        "ganancia_media_M": round(mejor["mean"] / 1e6, 1),
        "desvio_M": round(mejor["std"] / 1e6, 1),
        "min_M": round(mejor["min"] / 1e6, 1),
        "max_M": round(mejor["max"] / 1e6, 1),
        "semillas_mejor_que_todas": "-" if nombre == "todas"
        else f"{int((por_sem > gan_todas).sum())}/{len(por_sem)}",
    })
tabla = pd.DataFrame(resumen)
tabla.to_csv(exp.ruta("resumen"), index=False)
print("\n=== RESUMEN (ganancia en junio, millones) ===")
print(tabla.to_string(index=False))

# grafico
COLORES = {"todas": "#B2BEC3", "p95": "#00B894", "max": "#6C5CE7"}
fig = go.Figure()
for nombre in conjuntos:
    m = media[media["conjunto"] == nombre]
    if m.empty:
        continue
    c = COLORES[nombre]
    fig.add_scatter(x=np.concatenate([m["corte"], m["corte"][::-1]]),
                    y=np.concatenate([m["max"], m["min"][::-1]]) / 1e6, fill="toself",
                    fillcolor=c, opacity=0.15, line=dict(width=0), hoverinfo="skip", showlegend=False)
    fig.add_scatter(x=m["corte"], y=m["mean"] / 1e6, mode="lines",
                    name=f"{nombre} ({len(conjuntos[nombre])} variables)",
                    line=dict(color=c, width=4, shape="spline"))
fig.update_layout(
    title=dict(text="<b>Ganancia en junio segun conjunto de variables</b><br>"
                    "<span style='font-size:13px;color:#636e72'>Linea = promedio de semillas · "
                    "banda = minimo a maximo</span>", x=0.02),
    font=dict(family="Inter, Segoe UI, Helvetica, sans-serif", size=14, color="#2d3436"),
    plot_bgcolor="white", paper_bgcolor="white", height=520, margin=dict(l=70, r=30, t=95, b=60),
    xaxis=dict(title="Cantidad de envios", gridcolor="#f1f2f6"),
    yaxis=dict(title="Ganancia (millones)", gridcolor="#f1f2f6"),
    legend=dict(orientation="h", y=-0.18, x=0), hovermode="x unified",
)
fig.write_html(exp.ruta("curvas_ganancia", ext="html"), include_plotlyjs="cdn")

cerrar_experimento(exp, {
    "n_variables": {k: len(v) for k, v in conjuntos.items()},
    "umbral_p95": float(umbral_p95), "umbral_max": float(umbral_max),
    "ranking": tabla[["conjunto", "n_variables", "ganancia_media_M", "desvio_M"]].to_dict("records"),
})
