"""
04_comparar_datasets.py
DMEyF 2026 - Primera Competencia - Experimento 4001

Pregunta: ¿suman los lags/deltas? ¿cual tratamiento de montos funciona mejor?

Mismo LightGBM (hiperparametros fijos) sobre cada dataset:
  entrena con un mes, mide la GANANCIA en otro mes dos meses despues,
  ordenando a los clientes por probabilidad y probando distintas cantidades de envios.
Se repite con varias semillas para separar la mejora real de la suerte.

Uso:  python 04_comparar_datasets.py
Requiere:  pip install lightgbm pandas pyarrow plotly
"""

print("Arrancando 04_comparar_datasets.py ...", flush=True)

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
    # "experimento": 4001,
    "experimento": 4002,
    # "nombre": "comparar_fe",
    "nombre": "binaria2",
    "descripcion": "Base sin lags vs lags/deltas (crudo, mediana, rank). "
                   "LightGBM fijo (params del z601), train 202104 -> test 202106, 5 semillas.",
    # "datasets": {
    #     "base": "ds1001_base.parquet",
    #     "crudo": "ds3001_crudo.parquet",
    #     "mediana": "ds3001_mediana.parquet",
    #     "rank": "ds3001_rank.parquet",
    # },
    "datasets": {
    "base": "ds1001_base.parquet",
    "crudo": "ds3001_crudo.parquet",
                },
    "mes_train": 202104,
    "mes_test": 202106,
    # "clase": "clase_binaria1",        # BAJA+2 vs resto. La ganancia SIEMPRE se mide sobre BAJA+2
    "clase": "clase_binaria2",
    "usar_lag2": False,               # en abril lag2/delta2 estan vacios: no se pueden evaluar
    "semillas": [571369, 849571, 355049, 655531, 700103],
    "num_boost_round": 250,
    "lgbm": {                         # modelo elegido en el z601 de la catedra
        "objective": "binary",
        "boosting_type": "gbdt",
        "max_bin": 31,
        "num_leaves": 16,
        "learning_rate": 0.019868,
        "min_data_in_leaf": 816,
        "feature_fraction": 0.277155,
        "bagging_fraction": 0.634130,
        "bagging_freq": 1,            # sin esto bagging_fraction no tiene efecto
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


def leer(nombre_archivo):
    """Lee solo los meses y columnas necesarios (Parquet lo permite y ahorra mucha memoria)."""
    archivo = DIR_DATA / nombre_archivo
    columnas = pq.ParquetFile(archivo).schema_arrow.names
    if not PARAM["usar_lag2"]:
        columnas = [c for c in columnas if not (c.endswith("_lag2") or c.endswith("_delta2"))]
    df = pd.read_parquet(archivo, columns=columnas,
                         filters=[("foto_mes", "in", [PARAM["mes_train"], PARAM["mes_test"]])])
    features = [c for c in df.columns if c not in NO_FEATURES]
    return df, features


def auc(y, prob):
    """AUC por ranking (Mann-Whitney), sin depender de scikit-learn."""
    rangos = pd.Series(prob).rank().to_numpy()
    pos = y == 1
    n_pos, n_neg = pos.sum(), (~pos).sum()
    return (rangos[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def curva_ganancia(prob, ternaria):
    """Ganancia acumulada al enviar a los N clientes con mayor probabilidad, para cada N de CORTES."""
    orden = np.argsort(-prob, kind="stable")
    g = np.where(ternaria[orden] == "BAJA+2", PARAM["ganancia_acierto"], -PARAM["costo_estimulo"])
    acumulada = np.cumsum(g)
    return acumulada[np.minimum(CORTES, len(acumulada)) - 1]


filas = []
importancias = []
t_total = time.time()

for nombre, archivo in PARAM["datasets"].items():
    t0 = time.time()
    df, features = leer(archivo)
    train = df[df["foto_mes"] == PARAM["mes_train"]]
    test = df[df["foto_mes"] == PARAM["mes_test"]]
    y_train = train[PARAM["clase"]].astype(int).to_numpy()
    ternaria_test = test["clase_ternaria"].astype(str).to_numpy()
    y_test_bin = (ternaria_test == "BAJA+2").astype(int)

    print(f"\n--- {nombre}: {len(features)} variables | train {len(train):,} filas "
          f"({y_train.sum():,} positivos) | test {len(test):,} filas ({y_test_bin.sum():,} BAJA+2)")

    dtrain = lgb.Dataset(train[features], label=y_train, free_raw_data=True)
    X_test = test[features]

    for semilla in PARAM["semillas"]:
        params = dict(PARAM["lgbm"], seed=semilla)
        modelo = lgb.train(params, dtrain, num_boost_round=PARAM["num_boost_round"])
        prob = modelo.predict(X_test)

        curva = curva_ganancia(prob, ternaria_test)
        auc_ = auc(y_test_bin, prob)
        for corte, gan in zip(CORTES, curva):
            filas.append({"dataset": nombre, "semilla": semilla, "corte": corte, "ganancia": gan,
                          "auc": auc_})
        print(f"  semilla {semilla}: AUC {auc_:.4f} | ganancia maxima {curva.max() / 1e6:,.1f} M "
              f"en {CORTES[curva.argmax()]:,} envios")

        if semilla == PARAM["semillas"][0]:
            imp = pd.DataFrame({"dataset": nombre, "variable": features,
                                "gain": modelo.feature_importance("gain")})
            importancias.append(imp.sort_values("gain", ascending=False).head(40))

    print(f"  ({time.time() - t0:.0f} s)")
    del df, train, test, dtrain, X_test

# ---------------------------------------------------------------------------
# Resumen
# ---------------------------------------------------------------------------
detalle = pd.DataFrame(filas)
detalle.to_csv(exp.ruta("ganancia_por_corte_y_semilla"), index=False)
pd.concat(importancias).to_csv(exp.ruta("importancia_top40"), index=False)

# curva promedio entre semillas: el corte se elige sobre el PROMEDIO (no el maximo de cada semilla,
# que es optimista porque elige el corte mirando el resultado)
media = detalle.groupby(["dataset", "corte"])["ganancia"].agg(["mean", "std", "min", "max"]).reset_index()

resumen = []
for nombre in PARAM["datasets"]:
    m = media[media["dataset"] == nombre]
    mejor = m.loc[m["mean"].idxmax()]
    por_semilla = detalle[(detalle["dataset"] == nombre) & (detalle["corte"] == mejor["corte"])]
    resumen.append({
        "dataset": nombre,
        "corte_optimo": int(mejor["corte"]),
        "ganancia_media_M": round(mejor["mean"] / 1e6, 1),
        "desvio_M": round(mejor["std"] / 1e6, 1),
        "min_M": round(mejor["min"] / 1e6, 1),
        "max_M": round(mejor["max"] / 1e6, 1),
        "auc_media": round(detalle.loc[detalle["dataset"] == nombre, "auc"].mean(), 4),
        "_gan_por_semilla": por_semilla.set_index("semilla")["ganancia"],
    })

# ¿en cuantas semillas cada dataset le gana a la base, en el corte optimo de cada uno?
base_sem = next(r["_gan_por_semilla"] for r in resumen if r["dataset"] == "base") \
    if "base" in PARAM["datasets"] else None
for r in resumen:
    if base_sem is not None and r["dataset"] != "base":
        r["semillas_mejor_que_base"] = f"{int((r['_gan_por_semilla'] > base_sem).sum())}/{len(base_sem)}"
    else:
        r["semillas_mejor_que_base"] = "-"
tabla = pd.DataFrame(resumen).drop(columns="_gan_por_semilla").sort_values("ganancia_media_M",
                                                                           ascending=False)
tabla.to_csv(exp.ruta("resumen"), index=False)

print("\n=== RESUMEN (ganancia en junio, millones) ===")
print(tabla.to_string(index=False))
print("\nLectura: una diferencia vale la pena si supera claramente al desvio y se repite "
      "en la mayoria de las semillas.")

# ---------------------------------------------------------------------------
# Grafico: curva de ganancia promedio por dataset, con la banda min-max de las semillas
# ---------------------------------------------------------------------------
COLORES = {"base": "#B2BEC3", "crudo": "#FDCB6E", "mediana": "#00B894", "rank": "#6C5CE7"}
fig = go.Figure()
for nombre in PARAM["datasets"]:
    m = media[media["dataset"] == nombre]
    color = COLORES.get(nombre, "#636e72")
    fig.add_scatter(x=np.concatenate([m["corte"], m["corte"][::-1]]),
                    y=np.concatenate([m["max"], m["min"][::-1]]) / 1e6,
                    fill="toself", fillcolor=color, opacity=0.15, line=dict(width=0),
                    hoverinfo="skip", showlegend=False)
    fig.add_scatter(x=m["corte"], y=m["mean"] / 1e6, mode="lines", name=nombre,
                    line=dict(color=color, width=4, shape="spline"))
fig.update_layout(
    title=dict(text="<b>Ganancia en junio segun cantidad de envios</b><br>"
                    "<span style='font-size:13px;color:#636e72'>Linea = promedio de "
                    f"{len(PARAM['semillas'])} semillas · banda = minimo a maximo</span>", x=0.02),
    font=dict(family="Inter, Segoe UI, Helvetica, sans-serif", size=14, color="#2d3436"),
    plot_bgcolor="white", paper_bgcolor="white", height=520, margin=dict(l=70, r=30, t=95, b=60),
    xaxis=dict(title="Cantidad de envios", gridcolor="#f1f2f6"),
    yaxis=dict(title="Ganancia (millones)", gridcolor="#f1f2f6"),
    legend=dict(orientation="h", y=-0.18, x=0), hovermode="x unified",
)
fig.write_html(exp.ruta("curvas_ganancia", ext="html"), include_plotlyjs="cdn")

cerrar_experimento(exp, {
    "minutos_total": round((time.time() - t_total) / 60, 1),
    "ranking": tabla[["dataset", "ganancia_media_M", "desvio_M", "corte_optimo"]].to_dict("records"),
})
