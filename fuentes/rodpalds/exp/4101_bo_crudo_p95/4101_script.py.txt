"""
06_optimizacion_bayesiana.py
DMEyF 2026 - Primera Competencia - Experimento 4101

Optimizacion Bayesiana de hiperparametros de LightGBM (Optuna), en dos etapas:

  Etapa 1 - Busqueda: cada combinacion se evalua con validacion cruzada DENTRO del mes de
            train, midiendo ganancia. El mes de test no se mira en esta etapa.
  Etapa 2 - Validacion: los mejores candidatos se entrenan con todo el mes de train y se
            miden en el mes de test con varias semillas.

Es REANUDABLE: cada prueba se guarda en una base SQLite dentro de la carpeta del
experimento. Si se corta, volver a correr el script con PARAM["reanudar"] = True y sigue
desde donde quedo (Ctrl+C tambien sirve para frenarlo a mano).

Uso:  python 06_optimizacion_bayesiana.py
Requiere:  pip install optuna lightgbm pandas pyarrow plotly
"""

print("Arrancando 06_optimizacion_bayesiana.py ...", flush=True)

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
    "experimento": 4101,
    "nombre": "bo_crudo_p95",
    "descripcion": "Optuna sobre crudo + binaria2, variables p95 de canaritos (4003). "
                   "CV 5 folds en 202104 midiendo ganancia; top 5 validados en 202106 con 5 semillas.",
    "reanudar": False,                 # True para continuar una corrida interrumpida
    "dataset": "ds3001_crudo.parquet",
    # lista de variables: archivo de texto (una por linea) o None para usar todas
    "variables": "4003_canaritos/4003_variables_p95.txt",
    "mes_train": 202104,
    "mes_test": 202106,
    "clase": "clase_binaria2",
    "n_trials": 100,                   # total de combinaciones a probar
    "n_startup_trials": 20,            # las primeras al azar, despues "aprende"
    "cv_folds": 5,
    "max_boost_round": 3000,           # tope; el early stopping corta antes
    "espacio": {                       # rangos de busqueda
        "learning_rate": (0.005, 0.1, "log"),
        "num_leaves": (8, 256, "log"),
        "min_data_in_leaf": (20, 3000, "log"),
        "feature_fraction": (0.1, 1.0, "lineal"),
        "bagging_fraction": (0.3, 1.0, "lineal"),
        "lambda_l1": (0.001, 10.0, "log"),
        "lambda_l2": (0.001, 100.0, "log"),
    },
    "lgbm_fijos": {
        "objective": "binary",
        "boosting_type": "gbdt",
        "metric": "None",              # solo se mide la ganancia propia
        "max_bin": 31,
        "bagging_freq": 1,
        "feature_pre_filter": False,
        "first_metric_only": True,
        "verbose": -1,
    },
    "top_validar": 5,
    "semillas": [571369, 849571, 355049, 655531, 700103],
    "ventana_meseta": 401,             # la ganancia se suaviza promediando 401 cortes vecinos
    "ganancia_acierto": 1_072_500,
    "costo_estimulo": 27_500,
    "cortes": {"desde": 2000, "hasta": 20000, "paso": 500},
}

exp = iniciar_experimento(PARAM)
GAN, COSTO = PARAM["ganancia_acierto"], PARAM["costo_estimulo"]
NO_FEATURES = {"numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"}
CORTES = np.arange(PARAM["cortes"]["desde"], PARAM["cortes"]["hasta"] + 1, PARAM["cortes"]["paso"])

# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
t0 = time.time()
archivo = DIR_DATA / PARAM["dataset"]
todas = [c for c in pq.ParquetFile(archivo).schema_arrow.names if c not in NO_FEATURES]
if PARAM["variables"]:
    features = (DIR_EXP / PARAM["variables"]).read_text(encoding="utf-8").split()
    faltan = set(features) - set(todas)
    if faltan:
        raise ValueError(f"Variables de la lista que no estan en el dataset: {sorted(faltan)[:10]}")
else:
    features = [c for c in todas if not (c.endswith("_lag2") or c.endswith("_delta2"))]

df = pd.read_parquet(archivo, columns=features + ["foto_mes", "clase_ternaria", PARAM["clase"]],
                     filters=[("foto_mes", "in", [PARAM["mes_train"], PARAM["mes_test"]])])
train = df[df["foto_mes"] == PARAM["mes_train"]].reset_index(drop=True)
test = df[df["foto_mes"] == PARAM["mes_test"]].reset_index(drop=True)
del df
X_train = train[features]
y_train = train[PARAM["clase"]].astype(int).to_numpy()
baja2_train = (train["clase_ternaria"].astype(str) == "BAJA+2").to_numpy()
baja2_test = (test["clase_ternaria"].astype(str) == "BAJA+2").to_numpy()
X_test = test[features]
print(f"{len(features)} variables | train {len(train):,} filas | test {len(test):,} filas "
      f"({time.time() - t0:.0f} s)")

# folds estratificados por clase ternaria, FIJOS para todas las pruebas (comparacion pareja)
rng = np.random.default_rng(PARAM["semillas"][0])
fold_de = np.empty(len(train), dtype=int)
for clase in train["clase_ternaria"].astype(str).unique():
    idx = np.flatnonzero(train["clase_ternaria"].astype(str).to_numpy() == clase)
    rng.shuffle(idx)
    fold_de[idx] = np.arange(len(idx)) % PARAM["cv_folds"]
folds = [(np.flatnonzero(fold_de != k), np.flatnonzero(fold_de == k)) for k in range(PARAM["cv_folds"])]


# ---------------------------------------------------------------------------
# Ganancia
# ---------------------------------------------------------------------------
def ganancia_meseta(prob, es_baja2):
    """Ganancia maxima de la curva acumulada, suavizada (promedio de cortes vecinos)."""
    orden = np.argsort(-prob, kind="stable")
    acum = np.cumsum(np.where(es_baja2[orden], GAN, -COSTO))
    w = min(PARAM["ventana_meseta"], len(acum))
    cs = np.cumsum(np.insert(acum, 0, 0.0))
    return ((cs[w:] - cs[:-w]) / w).max()


def feval_ganancia(preds, data):
    # data.es_baja2 se agrega al armar cada Dataset de validacion; se escala al mes completo
    return "ganancia", ganancia_meseta(preds, data.es_baja2) * PARAM["cv_folds"], True


def curva_ganancia(prob, es_baja2):
    orden = np.argsort(-prob, kind="stable")
    acum = np.cumsum(np.where(es_baja2[orden], GAN, -COSTO))
    return acum[np.minimum(CORTES, len(acum)) - 1]


# ---------------------------------------------------------------------------
# Etapa 1: busqueda con Optuna
# ---------------------------------------------------------------------------
def sugerir(trial):
    p = {}
    for nombre, (lo, hi, escala) in PARAM["espacio"].items():
        if nombre in ("num_leaves", "min_data_in_leaf"):
            p[nombre] = trial.suggest_int(nombre, lo, hi, log=(escala == "log"))
        else:
            p[nombre] = trial.suggest_float(nombre, lo, hi, log=(escala == "log"))
    return p


def objetivo(trial):
    t = time.time()
    params = dict(PARAM["lgbm_fijos"], **sugerir(trial), seed=PARAM["semillas"][0])
    paciencia = int(50 + 5 / params["learning_rate"])
    historias = []
    for idx_tr, idx_va in folds:
        dtr = lgb.Dataset(X_train.iloc[idx_tr], label=y_train[idx_tr], free_raw_data=False)
        dva = lgb.Dataset(X_train.iloc[idx_va], label=y_train[idx_va], reference=dtr, free_raw_data=False)
        dva.es_baja2 = baja2_train[idx_va]
        registro = {}
        lgb.train(params, dtr, num_boost_round=PARAM["max_boost_round"], valid_sets=[dva],
                  valid_names=["valid"], feval=feval_ganancia,
                  callbacks=[lgb.early_stopping(paciencia, verbose=False),
                             lgb.record_evaluation(registro)])
        historias.append(np.array(registro["valid"]["ganancia"]))
    largo = min(len(h) for h in historias)
    media = np.mean([h[:largo] for h in historias], axis=0)
    mejor_iter = int(media.argmax()) + 1
    trial.set_user_attr("best_iter", mejor_iter)
    trial.set_user_attr("minutos", round((time.time() - t) / 60, 2))
    return float(media.max())


def informar(study, trial):
    if trial.value is None:
        return
    hechos = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
    print(f"  prueba {trial.number:3d} | ganancia CV {trial.value / 1e6:6.1f} M | "
          f"{trial.user_attrs['best_iter']:4d} arboles | {trial.user_attrs['minutos']:.1f} min | "
          f"mejor hasta ahora {study.best_value / 1e6:.1f} M | {hechos}/{PARAM['n_trials']}", flush=True)
    study.trials_dataframe().to_csv(exp.ruta("pruebas"), index=False)


optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(
    direction="maximize",
    study_name=f"exp{exp.id}",
    storage=f"sqlite:///{(exp.carpeta / f'{exp.id}_optuna.db').as_posix()}",
    load_if_exists=True,
    sampler=optuna.samplers.TPESampler(seed=PARAM["semillas"][0],
                                       n_startup_trials=PARAM["n_startup_trials"]),
)
hechos = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
faltan = PARAM["n_trials"] - hechos
print(f"\n=== Etapa 1: busqueda ({hechos} pruebas hechas, faltan {max(faltan, 0)}) ===")
print("La primera prueba suele ser la mas lenta. Con el tiempo de las primeras podes estimar el total.")
if faltan > 0:
    study.optimize(objetivo, n_trials=faltan, callbacks=[informar], catch=(Exception,))

pruebas = study.trials_dataframe()
pruebas.to_csv(exp.ruta("pruebas"), index=False)

# ---------------------------------------------------------------------------
# Etapa 2: validacion de los mejores en el mes de test
# ---------------------------------------------------------------------------
completas = [t for t in study.trials if t.value is not None]
mejores = sorted(completas, key=lambda t: t.value, reverse=True)[:PARAM["top_validar"]]
print(f"\n=== Etapa 2: validacion de los {len(mejores)} mejores en {PARAM['mes_test']} "
      f"con {len(PARAM['semillas'])} semillas ===")

dtrain_full = lgb.Dataset(X_train, label=y_train, free_raw_data=False)
filas = []
for t in mejores:
    params = dict(PARAM["lgbm_fijos"], **t.params)
    for semilla in PARAM["semillas"]:
        modelo = lgb.train(dict(params, seed=semilla), dtrain_full, num_boost_round=t.user_attrs["best_iter"])
        curva = curva_ganancia(modelo.predict(X_test), baja2_test)
        filas += [{"prueba": t.number, "semilla": semilla, "corte": c, "ganancia": g}
                  for c, g in zip(CORTES, curva)]
    print(f"  prueba {t.number} validada")

detalle = pd.DataFrame(filas)
detalle.to_csv(exp.ruta("validacion_por_corte_y_semilla"), index=False)
media = detalle.groupby(["prueba", "corte"])["ganancia"].agg(["mean", "std", "min", "max"]).reset_index()

resumen = []
for t in mejores:
    m = media[media["prueba"] == t.number]
    mejor = m.loc[m["mean"].idxmax()]
    resumen.append({
        "prueba": t.number,
        "ganancia_cv_M": round(t.value / 1e6, 1),
        "corte_optimo": int(mejor["corte"]),
        "ganancia_test_M": round(mejor["mean"] / 1e6, 1),
        "desvio_M": round(mejor["std"] / 1e6, 1),
        "min_M": round(mejor["min"] / 1e6, 1),
        "max_M": round(mejor["max"] / 1e6, 1),
        "arboles": t.user_attrs["best_iter"],
        **{k: round(v, 4) if isinstance(v, float) else v for k, v in t.params.items()},
    })
tabla = pd.DataFrame(resumen).sort_values("ganancia_test_M", ascending=False)
tabla.to_csv(exp.ruta("resumen"), index=False)
print("\n=== RESUMEN ===")
print(tabla.to_string(index=False))
print("\nReferencia sin optimizar (4003): todas 408.2 M, p95 403.7 M en junio.")

# graficos de Optuna (si fallan no importa: los datos ya estan en los CSV)
try:
    from optuna.visualization import plot_optimization_history, plot_param_importances, plot_slice
    plot_optimization_history(study).write_html(exp.ruta("historia", ext="html"), include_plotlyjs="cdn")
    plot_slice(study).write_html(exp.ruta("cortes_por_parametro", ext="html"), include_plotlyjs="cdn")
    plot_param_importances(study).write_html(exp.ruta("importancia_parametros", ext="html"),
                                             include_plotlyjs="cdn")
except Exception as e:
    print(f"(No se pudieron generar los graficos de Optuna: {e})")

cerrar_experimento(exp, {
    "pruebas_completas": len(completas),
    "mejor_cv_M": round(study.best_value / 1e6, 1),
    "ranking_test": tabla[["prueba", "ganancia_test_M", "desvio_M", "corte_optimo"]].to_dict("records"),
})
