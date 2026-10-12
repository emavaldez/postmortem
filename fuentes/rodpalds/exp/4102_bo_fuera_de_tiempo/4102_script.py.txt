"""
08_bo_fuera_de_tiempo.py
DMEyF 2026 - Primera Competencia - Experimento 4102

Optimizacion Bayesiana que mide FUERA DEL MES de entrenamiento (la 4101 media dentro de abril
y eligio modelos que no generalizaban a junio).

  - Los clientes de junio se dividen al azar en dos mitades fijas: A y B.
  - Etapa 1: cada combinacion entrena con TODO abril y se mide en la mitad A de junio.
             La primera prueba son los hiperparametros del z601 (punto de partida conocido).
  - Etapa 2: los mejores de la etapa 1 y el z601 se entrenan con varias semillas y se miden
             en la mitad B, que la busqueda nunca vio: es la estimacion honesta.
  - Eleccion: se usa un candidato de la BO solo si le gana al z601 en la mitad B en
             promedio Y en la mayoria clara de las semillas. Si no, se queda el z601.
             El resultado se graba en 4102_eleccion.json, que lee 07_modelo_final.py.

Reanudable como la 4101 (PARAM["reanudar"] = True).

Uso:  python 08_bo_fuera_de_tiempo.py
"""

print("Arrancando 08_bo_fuera_de_tiempo.py ...", flush=True)

import json
import time

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import pyarrow.parquet as pq

from exp_utils import DIR_DATA, DIR_EXP, cerrar_experimento, iniciar_experimento

# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 4102,
    "nombre": "bo_fuera_de_tiempo",
    "descripcion": "Optuna entrenando con 202104 completo y midiendo en la mitad A de 202106 "
                   "(meseta 12-17 mil envios equivalentes). Confirmacion en la mitad B con 10 "
                   "semillas contra z601. Variables p95, crudo + binaria2.",
    "reanudar": False,
    "dataset": "ds3001_crudo.parquet",
    "variables": "4003_canaritos/4003_variables_p95.txt",   # None = todas (sin lag2)
    "mes_train": 202104,
    "mes_test": 202106,
    "clase": "clase_binaria2",
    "semilla_mitades": 571369,
    "n_trials": 150,
    "n_startup_trials": 25,
    "max_boost_round": 3000,
    "espacio": {
        "learning_rate": (0.005, 0.1, "log"),
        "num_leaves": (8, 128, "log"),
        "min_data_in_leaf": (50, 5000, "log"),
        "feature_fraction": (0.1, 1.0, "lineal"),
        "bagging_fraction": (0.2, 1.0, "lineal"),
        "lambda_l1": (0.001, 10.0, "log"),
        "lambda_l2": (0.001, 100.0, "log"),
    },
    "lgbm_fijos": {
        "objective": "binary",
        "boosting_type": "gbdt",
        "metric": "None",
        "max_bin": 31,
        "bagging_freq": 1,
        "feature_pre_filter": False,
        "first_metric_only": True,
        "deterministic": True,
        "force_row_wise": True,
        "verbose": -1,
    },
    "top_confirmar": 5,
    "semillas_confirmacion": 10,
    "semillas_base": [571369, 849571, 355049, 655531, 700103],
    "regla_minimo_semillas_ganadas": 7,     # de 10, para reemplazar al z601
    "meseta_mes_completo": [12000, 17000],  # en la mitad se usa la mitad de esos envios
    "ganancia_acierto": 1_072_500,
    "costo_estimulo": 27_500,
}

Z601 = {"learning_rate": 0.019868, "num_leaves": 16, "min_data_in_leaf": 816,
        "feature_fraction": 0.277155, "bagging_fraction": 0.634130, "lambda_l1": 0.001,
        "lambda_l2": 0.001}
Z601_ARBOLES = 250

exp = iniciar_experimento(PARAM)
GAN, COSTO = PARAM["ganancia_acierto"], PARAM["costo_estimulo"]
NO_FEATURES = {"numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"}

# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
t0 = time.time()
archivo = DIR_DATA / PARAM["dataset"]
if PARAM["variables"]:
    features = (DIR_EXP / PARAM["variables"]).read_text(encoding="utf-8").split()
else:
    features = [c for c in pq.ParquetFile(archivo).schema_arrow.names
                if c not in NO_FEATURES and not (c.endswith("_lag2") or c.endswith("_delta2"))]
df = pd.read_parquet(archivo, columns=features + ["numero_de_cliente", "foto_mes", "clase_ternaria", PARAM["clase"]],
                     filters=[("foto_mes", "in", [PARAM["mes_train"], PARAM["mes_test"]])])
train = df[df["foto_mes"] == PARAM["mes_train"]].reset_index(drop=True)
test = df[df["foto_mes"] == PARAM["mes_test"]].reset_index(drop=True)
del df

# mitades de junio estratificadas por clase ternaria (misma cantidad de BAJA+2 en cada una)
rng = np.random.default_rng(PARAM["semilla_mitades"])
mitad = np.empty(len(test), dtype="U1")
ternaria_test = test["clase_ternaria"].astype(str).to_numpy()
for clase in np.unique(ternaria_test):
    idx = np.flatnonzero(ternaria_test == clase)
    rng.shuffle(idx)
    mitad[idx[: len(idx) // 2]] = "A"
    mitad[idx[len(idx) // 2:]] = "B"
pd.DataFrame({"numero_de_cliente": test["numero_de_cliente"], "mitad": mitad}) \
    .to_csv(exp.ruta("mitades_junio"), index=False)

X_train, y_train = train[features], train[PARAM["clase"]].astype(int).to_numpy()
XA, XB = test.loc[mitad == "A", features], test.loc[mitad == "B", features]
baja2A = ternaria_test[mitad == "A"] == "BAJA+2"
baja2B = ternaria_test[mitad == "B"] == "BAJA+2"
lo, hi = (e // 2 for e in PARAM["meseta_mes_completo"])   # envios equivalentes en media poblacion
print(f"{len(features)} variables | train {len(train):,} | mitad A {len(XA):,} ({baja2A.sum()} BAJA+2) | "
      f"mitad B {len(XB):,} ({baja2B.sum()} BAJA+2) ({time.time() - t0:.0f} s)")
dtrain = lgb.Dataset(X_train, label=y_train, free_raw_data=False)


def meseta(prob, es_baja2):
    """Ganancia promedio entre 6.000 y 8.500 envios de media poblacion, x2 = mes completo."""
    orden = np.argsort(-prob, kind="stable")
    acum = np.cumsum(np.where(es_baja2[orden], GAN, -COSTO))
    return 2 * acum[lo - 1:hi].mean()


def feval_meseta(preds, data):
    return "meseta", meseta(preds, data.es_baja2), True


# ---------------------------------------------------------------------------
# Etapa 1: busqueda midiendo en la mitad A
# ---------------------------------------------------------------------------
def objetivo(trial):
    t = time.time()
    p = {}
    for nombre, (a, b, escala) in PARAM["espacio"].items():
        if nombre in ("num_leaves", "min_data_in_leaf"):
            p[nombre] = trial.suggest_int(nombre, a, b, log=(escala == "log"))
        else:
            p[nombre] = trial.suggest_float(nombre, a, b, log=(escala == "log"))
    params = dict(PARAM["lgbm_fijos"], **p, seed=PARAM["semillas_base"][0])
    dA = lgb.Dataset(XA, label=(baja2A).astype(int), reference=dtrain, free_raw_data=False)
    dA.es_baja2 = baja2A
    registro = {}
    lgb.train(params, dtrain, num_boost_round=PARAM["max_boost_round"], valid_sets=[dA],
              valid_names=["A"], feval=feval_meseta,
              callbacks=[lgb.early_stopping(int(50 + 5 / params["learning_rate"]), verbose=False),
                         lgb.record_evaluation(registro)])
    hist = np.array(registro["A"]["meseta"])
    trial.set_user_attr("best_iter", int(hist.argmax()) + 1)
    trial.set_user_attr("minutos", round((time.time() - t) / 60, 2))
    return float(hist.max())


def informar(study, trial):
    if trial.value is None:
        return
    hechos = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
    print(f"  prueba {trial.number:3d} | meseta A {trial.value / 1e6:6.1f} M | "
          f"{trial.user_attrs['best_iter']:4d} arboles | {trial.user_attrs['minutos']:.1f} min | "
          f"mejor {study.best_value / 1e6:.1f} M | {hechos}/{PARAM['n_trials']}", flush=True)
    study.trials_dataframe().to_csv(exp.ruta("pruebas"), index=False)


optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(
    direction="maximize", study_name=f"exp{exp.id}",
    storage=f"sqlite:///{(exp.carpeta / f'{exp.id}_optuna.db').as_posix()}", load_if_exists=True,
    sampler=optuna.samplers.TPESampler(seed=PARAM["semillas_base"][0],
                                       n_startup_trials=PARAM["n_startup_trials"]))
if len(study.trials) == 0:
    study.enqueue_trial(Z601)          # primera prueba: el punto de partida conocido
hechos = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
faltan = PARAM["n_trials"] - hechos
print(f"\n=== Etapa 1: busqueda en mitad A ({hechos} hechas, faltan {max(faltan, 0)}) ===")
if faltan > 0:
    study.optimize(objetivo, n_trials=faltan, callbacks=[informar], catch=(Exception,))
study.trials_dataframe().to_csv(exp.ruta("pruebas"), index=False)

# ---------------------------------------------------------------------------
# Etapa 2: confirmacion en la mitad B (nunca vista por la busqueda)
# ---------------------------------------------------------------------------
semillas = list(PARAM["semillas_base"])
rng_s = np.random.default_rng(PARAM["semillas_base"][0])
while len(semillas) < PARAM["semillas_confirmacion"]:
    c = int(rng_s.integers(100003, 999983))
    if all(c % d for d in range(2, int(c ** 0.5) + 1)) and c not in semillas:
        semillas.append(c)
semillas = semillas[:PARAM["semillas_confirmacion"]]

completas = [t for t in study.trials if t.value is not None]
mejores = sorted(completas, key=lambda t: t.value, reverse=True)[:PARAM["top_confirmar"]]
candidatos = [{"nombre": "z601", "params": Z601, "arboles": Z601_ARBOLES, "meseta_A": None}]
candidatos += [{"nombre": f"prueba_{t.number}", "params": t.params, "arboles": t.user_attrs["best_iter"],
                "meseta_A": t.value} for t in mejores]

print(f"\n=== Etapa 2: confirmacion en mitad B, {len(candidatos)} candidatos x {len(semillas)} semillas ===")
filas = []
for cand in candidatos:
    t = time.time()
    params = dict(PARAM["lgbm_fijos"], **cand["params"])
    params = {k: v for k, v in params.items() if k not in ("metric", "first_metric_only")}
    for semilla in semillas:
        modelo = lgb.train(dict(params, seed=semilla), dtrain, num_boost_round=cand["arboles"])
        filas.append({"candidato": cand["nombre"], "semilla": semilla,
                      "meseta_B": meseta(modelo.predict(XB), baja2B)})
    print(f"  {cand['nombre']}: listo ({(time.time() - t) / 60:.1f} min)", flush=True)

detalle = pd.DataFrame(filas)
detalle.to_csv(exp.ruta("confirmacion_por_semilla"), index=False)
piv = detalle.pivot(index="semilla", columns="candidato", values="meseta_B")
resumen = []
for cand in candidatos:
    n = cand["nombre"]
    resumen.append({
        "candidato": n,
        "meseta_A_M": None if cand["meseta_A"] is None else round(cand["meseta_A"] / 1e6, 1),
        "meseta_B_M": round(piv[n].mean() / 1e6, 1),
        "desvio_B_M": round(piv[n].std() / 1e6, 1),
        "semillas_mejor_que_z601": "-" if n == "z601" else f"{int((piv[n] > piv['z601']).sum())}/{len(semillas)}",
        "arboles": cand["arboles"],
        **{k: round(v, 4) if isinstance(v, float) else v for k, v in cand["params"].items()},
    })
tabla = pd.DataFrame(resumen).sort_values("meseta_B_M", ascending=False)
tabla.to_csv(exp.ruta("resumen"), index=False)
print("\n=== RESUMEN (meseta 12-17 mil envios equivalentes, millones) ===")
print(tabla.to_string(index=False))

# ---------------------------------------------------------------------------
# Eleccion
# ---------------------------------------------------------------------------
retadores = [c for c in candidatos if c["nombre"] != "z601"]
mejor = max(retadores, key=lambda c: piv[c["nombre"]].mean()) if retadores else None
ganadas = int((piv[mejor["nombre"]] > piv["z601"]).sum()) if mejor else 0
supera = (mejor is not None and piv[mejor["nombre"]].mean() > piv["z601"].mean()
          and ganadas >= PARAM["regla_minimo_semillas_ganadas"])
elegido = mejor if supera else candidatos[0]
fijos = {k: v for k, v in PARAM["lgbm_fijos"].items() if k not in ("metric", "first_metric_only")}
eleccion = {
    "origen": f"{exp.id} {elegido['nombre']}",
    "params": {**fijos, **elegido["params"]},
    "arboles": int(elegido["arboles"]),
    "fraccion_mes_referencia": 1.0,          # se entreno con un mes completo
    "variables": PARAM["variables"],
    "evidencia": {
        "meseta_B_elegido_M": round(piv[elegido["nombre"]].mean() / 1e6, 1),
        "meseta_B_z601_M": round(piv["z601"].mean() / 1e6, 1),
        "mejor_retador": mejor["nombre"] if mejor else None,
        "semillas_ganadas_por_el_mejor_retador": f"{ganadas}/{len(semillas)}",
    },
}
with open(exp.ruta("eleccion", ext="json"), "w", encoding="utf-8") as f:
    json.dump(eleccion, f, indent=2, ensure_ascii=False)
print(f"\nELECCION: {eleccion['origen']}  "
      f"(meseta B {eleccion['evidencia']['meseta_B_elegido_M']} M vs z601 {eleccion['evidencia']['meseta_B_z601_M']} M; "
      f"mejor retador gano {ganadas}/{len(semillas)} semillas)")

try:
    from optuna.visualization import plot_optimization_history, plot_slice
    plot_optimization_history(study).write_html(exp.ruta("historia", ext="html"), include_plotlyjs="cdn")
    plot_slice(study).write_html(exp.ruta("cortes_por_parametro", ext="html"), include_plotlyjs="cdn")
except Exception as e:
    print(f"(No se pudieron generar los graficos de Optuna: {e})")

cerrar_experimento(exp, {"pruebas": len(completas), "eleccion": eleccion["origen"],
                         "evidencia": eleccion["evidencia"]})
