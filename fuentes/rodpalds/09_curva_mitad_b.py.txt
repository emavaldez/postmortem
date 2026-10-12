"""
09_curva_mitad_b.py
DMEyF 2026 - Primera Competencia - Experimento 5101

Para cada candidato (z601, el elegido por 4102, el de 4103 si existe) y para la COMBINACION
de candidatos, arma un semillerio entrenado con abril completo y mide la curva de ganancia
en la MITAD B de junio, que ninguna busqueda uso para elegir hiperparametros.

Sirve para dos cosas:
  1. Comparar candidatos y su combinacion con semillerio (no con una semilla).
  2. Elegir la cantidad de envios de CADA modelo (como proporcion de clientes), porque un
     modelo distinto puede tener su optimo en otro lugar.

La ganancia de la mitad se multiplica por 2 para que sea comparable con el mes completo.
La combinacion promedia el RANKING de cada cliente en cada modelo (no las probabilidades,
porque cada modelo tiene su propia escala).

Uso:  py -3.12 09_curva_mitad_b.py
"""

print("Arrancando 09_curva_mitad_b.py ...", flush=True)

import json
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from exp_utils import DIR_DATA, DIR_EXP, cerrar_experimento, iniciar_experimento

# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 5101,
    "nombre": "curva_mitad_b",
    "descripcion": "Semillerio de 20 por candidato (z601, eleccion 4102, eleccion 4103 si existe) y su "
                   "combinacion por ranking. Train 202104 completo, curva de ganancia en la mitad B de 202106 (x2).",
    "dataset": "ds3001_crudo.parquet",
    "variables": "4003_canaritos/4003_variables_p95.txt",
    "mitades": "4102_bo_fuera_de_tiempo/4102_mitades_junio.csv",
    "candidatos": {
        "z601": "z601",
        "bo4102": "4102_bo_fuera_de_tiempo/4102_eleccion.json",
        "bo4103": "4103_bo_fuera_de_tiempo_ampliada/4103_eleccion.json",   # si no existe, se saltea
    },
    "mes_train": 202104,
    "mes_test": 202106,
    "clase": "clase_binaria2",
    "n_semillas": 20,
    "semillas_base": [571369, 849571, 355049, 655531, 700103],
    # envios equivalentes en el mes COMPLETO (en la mitad se usa la mitad)
    "envios": list(range(10000, 20001, 500)),
    "meseta": [12000, 17000],
    "ganancia_acierto": 1_072_500,
    "costo_estimulo": 27_500,
}

exp = iniciar_experimento(PARAM)
GAN, COSTO = PARAM["ganancia_acierto"], PARAM["costo_estimulo"]

HIPER_Z601 = {
    "params": {"objective": "binary", "boosting_type": "gbdt", "max_bin": 31, "num_leaves": 16,
               "learning_rate": 0.019868, "min_data_in_leaf": 816, "feature_fraction": 0.277155,
               "bagging_fraction": 0.634130, "bagging_freq": 1, "feature_pre_filter": False},
    "arboles": 250,
}
REPRODUCIBLE = {"deterministic": True, "force_row_wise": True, "verbose": -1}


# ---------------------------------------------------------------------------
# Semillas (mismo procedimiento que 07)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Candidatos
# ---------------------------------------------------------------------------
candidatos = {}
for nombre, fuente in PARAM["candidatos"].items():
    if fuente == "z601":
        candidatos[nombre] = {"params": dict(HIPER_Z601["params"]), "arboles": HIPER_Z601["arboles"],
                              "origen": "z601"}
        continue
    archivo = DIR_EXP / fuente
    if not archivo.exists():
        print(f"- {nombre}: no existe {fuente}, se saltea")
        continue
    el = json.loads(archivo.read_text(encoding="utf-8"))
    candidatos[nombre] = {"params": dict(el["params"]), "arboles": int(el["arboles"]), "origen": el["origen"]}
for c in candidatos.values():
    for k in ("num_leaves", "min_data_in_leaf", "max_bin", "bagging_freq"):
        if k in c["params"]:
            c["params"][k] = int(c["params"][k])
    c["params"].update(REPRODUCIBLE)
print("Candidatos:", {k: v["origen"] for k, v in candidatos.items()})

# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
t0 = time.time()
features = (DIR_EXP / PARAM["variables"]).read_text(encoding="utf-8").split()
df = pd.read_parquet(DIR_DATA / PARAM["dataset"],
                     columns=["numero_de_cliente", "foto_mes", "clase_ternaria", PARAM["clase"]] + features,
                     filters=[("foto_mes", "in", [PARAM["mes_train"], PARAM["mes_test"]])])
train = df[df["foto_mes"] == PARAM["mes_train"]]
test = df[df["foto_mes"] == PARAM["mes_test"]]
del df
mitades = pd.read_csv(DIR_EXP / PARAM["mitades"])
ids_B = set(mitades.loc[mitades["mitad"] == "B", "numero_de_cliente"])
testB = test[test["numero_de_cliente"].isin(ids_B)].reset_index(drop=True)
assert len(testB) == len(ids_B), "Las mitades no coinciden con los clientes de junio del dataset"
baja2B = (testB["clase_ternaria"].astype(str) == "BAJA+2").to_numpy()
print(f"{len(features)} variables | train {len(train):,} | mitad B {len(testB):,} ({baja2B.sum()} BAJA+2) "
      f"({time.time() - t0:.0f} s)")
dtrain = lgb.Dataset(train[features], label=train[PARAM["clase"]].astype(int).to_numpy(), free_raw_data=False)
XB = testB[features]
del train, test

ENV = np.array(PARAM["envios"])
lo, hi = PARAM["meseta"]


def curva_x2(prob):
    """Ganancia del mes completo equivalente: envios/2 en la mitad, ganancia x2."""
    orden = np.argsort(-prob, kind="stable")
    acum = np.cumsum(np.where(baja2B[orden], GAN, -COSTO))
    en_envios = 2 * acum[ENV // 2 - 1]
    meseta = 2 * acum[lo // 2 - 1:hi // 2].mean()
    return en_envios, meseta


# ---------------------------------------------------------------------------
# Semillerio por candidato
# ---------------------------------------------------------------------------
prob_final = {}
filas = []
for nombre, c in candidatos.items():
    t = time.time()
    suma = np.zeros(len(testB))
    for i, semilla in enumerate(semillas, start=1):
        modelo = lgb.train(dict(c["params"], seed=semilla), dtrain, num_boost_round=c["arboles"])
        p = modelo.predict(XB)
        suma += p
        _, mes_ind = curva_x2(p)
        filas.append({"modelo": nombre, "semilla": semilla, "meseta_semilla_sola": mes_ind})
    prob_final[nombre] = suma / len(semillas)
    print(f"  {nombre}: {len(semillas)} semillas ({(time.time() - t) / 60:.1f} min)", flush=True)
pd.DataFrame(filas).to_csv(exp.ruta("meseta_por_semilla"), index=False)


def a_ranking(p):
    return pd.Series(p).rank(pct=True).to_numpy()


if len(prob_final) >= 2:
    prob_final["combinacion_todos"] = np.mean([a_ranking(p) for p in prob_final.values()], axis=0)
    if "z601" in prob_final and "bo4102" in prob_final and len(candidatos) > 2:
        prob_final["combinacion_z601_bo4102"] = (a_ranking(prob_final["z601"]) + a_ranking(prob_final["bo4102"])) / 2

# ---------------------------------------------------------------------------
# Curvas y resumen
# ---------------------------------------------------------------------------
curvas = {}
resumen = []
for nombre, p in prob_final.items():
    en_envios, meseta = curva_x2(p)
    curvas[nombre] = en_envios
    i = int(en_envios.argmax())
    resumen.append({"modelo": nombre, "meseta_M": round(meseta / 1e6, 1),
                    "maximo_M": round(en_envios[i] / 1e6, 1), "envios_optimos": int(ENV[i]),
                    "proporcion_clientes": round(ENV[i] / (2 * len(testB)), 4)})
tabla = pd.DataFrame(resumen).sort_values("meseta_M", ascending=False)
tabla.to_csv(exp.ruta("resumen"), index=False)
pd.DataFrame({"envios": ENV, **{k: np.round(v / 1e6, 1) for k, v in curvas.items()}}) \
    .to_csv(exp.ruta("curvas"), index=False)
pd.DataFrame({"numero_de_cliente": testB["numero_de_cliente"].astype("int64"),
              "clase_ternaria": testB["clase_ternaria"].astype(str), **prob_final}) \
    .to_csv(exp.ruta("probabilidades_mitad_B"), index=False)

print("\n=== Mitad B de junio, ganancia equivalente al mes completo (millones) ===")
print(tabla.to_string(index=False))
print("\nPor envios:")
print(pd.read_csv(exp.ruta("curvas")).to_string(index=False))

COLORES = ["#B2BEC3", "#6C5CE7", "#00B894", "#FDCB6E", "#E17055"]
fig = go.Figure()
for (nombre, c), color in zip(curvas.items(), COLORES):
    fig.add_scatter(x=ENV, y=c / 1e6, mode="lines", name=nombre, line=dict(color=color, width=4, shape="spline"))
fig.update_layout(
    title=dict(text="<b>Ganancia en la mitad B de junio (x2) segun envios</b><br>"
                    f"<span style='font-size:13px;color:#636e72'>Semillerio de {len(semillas)} por modelo</span>",
               x=0.02),
    font=dict(family="Inter, Segoe UI, Helvetica, sans-serif", size=14, color="#2d3436"),
    plot_bgcolor="white", paper_bgcolor="white", height=520, margin=dict(l=70, r=30, t=95, b=60),
    xaxis=dict(title="Envios equivalentes en el mes completo", gridcolor="#f1f2f6"),
    yaxis=dict(title="Ganancia (millones)", gridcolor="#f1f2f6"),
    legend=dict(orientation="h", y=-0.18, x=0), hovermode="x unified",
)
fig.write_html(exp.ruta("curvas", ext="html"), include_plotlyjs="cdn")

cerrar_experimento(exp, {"resumen": tabla.to_dict("records")})
