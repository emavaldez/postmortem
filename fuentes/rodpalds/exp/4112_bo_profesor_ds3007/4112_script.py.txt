r"""
16_bo_profesor_v2.py
DMEyF 2026 - Primera Competencia - Experimentos 4111 (ds3003) y 4112 (ds3007, dataset del profesor)

Optimizacion Bayesiana con la "1.7 Training Strategy" que envio el profesor:
  - SIN undersampling de los CONTINUA (todas las filas).
  - Metrica AUC en LightGBM (metric = "auc"); la Bayesiana maximiza el AUC promedio de las
    particiones de validacion (clase binaria2, la misma con la que se entrena).
  - Hiperparametros FIJOS: max_bin 31, min_data_in_leaf 0, feature_fraction 0,50,
    feature_fraction_bynode 0,20, learning_rate 0,005. Sin bagging (no lo menciona).
  - Hiperparametros BAYESIANOS: num_iterations, num_leaves, min_sum_hessian_in_leaf.
Validacion como el z601 de la catedra: 5 particiones 70/30 estratificadas por clase ternaria
dentro de 202103 + 202104 (toda la informacion disponible con la misma distancia de 2 meses que
hay entre junio y agosto). Junio NO se usa en la busqueda.
Ademas del AUC se guarda la ganancia de meseta (12.000-17.000 envios, escalada a mes completo)
de cada prueba, solo como informacion.

Para apurar a mano: crear el archivo APURAR.txt en la carpeta del proyecto (mismo efecto que
la hora limite, desde la prueba siguiente).
Corte por horario: PARAM["hora_limite"] (hora local, "AAAA-MM-DD HH:MM"). Pasada esa hora no se
empiezan pruebas nuevas, siempre que haya al menos PARAM["min_pruebas"] terminadas, para que
la evaluacion y el modelo final lleguen antes del cierre. Reanudable (4111_optuna.db).

Salida: <id>_pruebas.csv y <id>_top.json (las PARAM["top_n"] mejores por AUC) -> 17_eval_profesor_v2.py
(top 3) o 18_ensamble_profesor.py (top 12, ensamble del profesor).

Uso:  py -3.12 16_bo_profesor_v2.py configs\4111_bo_profesor_v2.json
"""

print("Arrancando 16_bo_profesor_v2.py ...", flush=True)

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import pyarrow.parquet as pq

from exp_utils import DIR_DATA, ROOT, cerrar_experimento, iniciar_experimento

# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 4111,
    "nombre": "bo_profesor_v2",
    "descripcion": "Bayesiana con la Training Strategy 1.7 del profesor (AUC, lr 0,005 y min_data_in_leaf 0 fijos).",
    "reanudar": True,
    "dataset": "ds3003_rank_extra.parquet",
    "usar_lag2": True,
    "meses_train": [202103, 202104],
    "clase": "clase_binaria2",
    "n_particiones": 5,
    "fraccion_valida": 0.3,
    "semilla_particiones": 571369,
    "n_trials": 40,
    "n_startup_trials": 12,
    "min_pruebas": 15,
    "hora_limite": None,                       # ej. "2026-10-11 16:00"
    "semilla_sampler": 849571,
    "espacio": {
        "num_iterations": [250, 4000, "log"],
        "num_leaves": [8, 2000, "log"],
        "min_sum_hessian_in_leaf": [0.001, 100.0, "log"],
    },
    "lgbm_fijos": {
        "objective": "binary", "boosting_type": "gbdt", "metric": "auc",
        "max_bin": 31, "min_data_in_leaf": 0, "feature_fraction": 0.50,
        "feature_fraction_bynode": 0.20, "learning_rate": 0.005,
        "feature_pre_filter": False, "deterministic": True, "force_row_wise": True, "verbose": -1,
    },
    "semilla_modelo": 571369,
    "top_n": 3,
    "meseta_mes_completo": [12000, 17000],
    "ganancia_acierto": 1_072_500,
    "costo_estimulo": 27_500,
}

if len(sys.argv) > 1:
    config = Path(sys.argv[1])
    PARAM.update(json.loads(config.read_text(encoding="utf-8")))
    PARAM["_config"] = config.name
    print(f"Configuracion tomada de {config}")

exp = iniciar_experimento(PARAM)
GAN, COSTO = PARAM["ganancia_acierto"], PARAM["costo_estimulo"]
NO_FEATURES = {"numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"}
LIMITE = datetime.strptime(PARAM["hora_limite"], "%Y-%m-%d %H:%M") if PARAM.get("hora_limite") else None
ENTEROS = ("num_iterations", "num_leaves")
APURAR = ROOT / "APURAR.txt"      # si existe: hacer solo el minimo y seguir

# ---------------------------------------------------------------------------
# Datos: solo los meses de entrenamiento (junio no se toca)
# ---------------------------------------------------------------------------
t0 = time.time()
archivo = DIR_DATA / PARAM["dataset"]
features = [c for c in pq.ParquetFile(archivo).schema_arrow.names if c not in NO_FEATURES
            and (PARAM["usar_lag2"] or not (c.endswith("_lag2") or c.endswith("_delta2")))]
df = pd.read_parquet(archivo, columns=features + ["foto_mes", "clase_ternaria", PARAM["clase"]],
                     filters=[("foto_mes", "in", PARAM["meses_train"])])
assert sorted(df["foto_mes"].unique()) == sorted(PARAM["meses_train"]), "Faltan meses de entrenamiento"
assert df[PARAM["clase"]].notna().all(), "Hay filas sin clase"
ternaria = df["clase_ternaria"].astype(str).to_numpy()
y = df[PARAM["clase"]].astype(int).to_numpy()
X = df[features]
filas_por_mes = len(df) / len(PARAM["meses_train"])
print(f"{len(features)} variables | {len(df):,} filas {PARAM['meses_train']} ({time.time() - t0:.0f} s)")

# ---------------------------------------------------------------------------
# Particiones 70/30 estratificadas por clase ternaria (StratifiedShuffleSplit, sin sklearn)
# ---------------------------------------------------------------------------
rng = np.random.default_rng(PARAM["semilla_particiones"])
particiones = []
for k in range(PARAM["n_particiones"]):
    es_valida = np.zeros(len(df), dtype=bool)
    for clase in np.unique(ternaria):
        idx = np.flatnonzero(ternaria == clase)
        n_va = int(round(len(idx) * PARAM["fraccion_valida"]))
        es_valida[rng.choice(idx, size=n_va, replace=False)] = True
    particiones.append(es_valida)
pd.DataFrame({f"particion_{k}": p.astype(np.int8) for k, p in enumerate(particiones)}).to_csv(
    exp.ruta("particiones"), index=False)

params_dataset = {"max_bin": PARAM["lgbm_fijos"]["max_bin"], "min_data_in_leaf": PARAM["lgbm_fijos"]["min_data_in_leaf"],
                  "feature_pre_filter": False, "verbose": -1}
pliegues = []
for k, es_valida in enumerate(particiones):
    dtr = lgb.Dataset(X[~es_valida], label=y[~es_valida], params=params_dataset, free_raw_data=True).construct()
    fv = es_valida.sum() / filas_por_mes                 # cuantos "meses completos" representa la validacion
    pliegues.append({"dtr": dtr, "Xva": X[es_valida].reset_index(drop=True), "yva": y[es_valida],
                     "b2": ternaria[es_valida] == "BAJA+2", "fv": fv,
                     "lo": int(round(PARAM["meseta_mes_completo"][0] * fv)),
                     "hi": int(round(PARAM["meseta_mes_completo"][1] * fv))})
    print(f"  particion {k}: train {(~es_valida).sum():,} | valida {es_valida.sum():,} "
          f"({pliegues[-1]['b2'].sum()} BAJA+2, {pliegues[-1]['yva'].sum()} positivos binaria2)", flush=True)
del X, df


def auc(y_true, score):
    """AUC por rangos (Mann-Whitney), con empates promediados."""
    r = pd.Series(score).rank(method="average").to_numpy()
    n1 = y_true.sum()
    n0 = len(y_true) - n1
    return float((r[y_true == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def meseta(pl, prob):
    orden = np.argsort(-prob, kind="stable")
    acum = np.cumsum(np.where(pl["b2"][orden], GAN, -COSTO))
    return float(acum[pl["lo"] - 1:pl["hi"]].mean() / pl["fv"])


# ---------------------------------------------------------------------------
# Busqueda
# ---------------------------------------------------------------------------
def objetivo(trial):
    t = time.time()
    p = {}
    for nombre, (a, b, escala) in PARAM["espacio"].items():
        if nombre in ENTEROS:
            p[nombre] = trial.suggest_int(nombre, int(a), int(b), log=(escala == "log"))
        else:
            p[nombre] = trial.suggest_float(nombre, a, b, log=(escala == "log"))
    n_iter = p.pop("num_iterations")
    params = dict(PARAM["lgbm_fijos"], **p, seed=PARAM["semilla_modelo"])
    aucs, aucs_b2, mesetas = [], [], []
    for pl in pliegues:
        modelo = lgb.train(params, pl["dtr"], num_boost_round=n_iter)
        prob = modelo.predict(pl["Xva"])
        aucs.append(auc(pl["yva"], prob))
        aucs_b2.append(auc(pl["b2"].astype(int), prob))
        mesetas.append(meseta(pl, prob))
    trial.set_user_attr("auc_desvio", float(np.std(aucs)))
    trial.set_user_attr("auc_baja2", float(np.mean(aucs_b2)))
    trial.set_user_attr("meseta_M", round(float(np.mean(mesetas)) / 1e6, 2))
    trial.set_user_attr("minutos", round((time.time() - t) / 60, 2))
    return float(np.mean(aucs))


def informar(study, trial):
    if trial.value is None:
        print(f"  prueba {trial.number:3d} | FALLO ({trial.state})", flush=True)
        return
    hechas = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
    print(f"  prueba {trial.number:3d} | AUC {trial.value:.5f} | meseta {trial.user_attrs['meseta_M']:6.1f} M | "
          f"{trial.params['num_iterations']:4d} arboles, {trial.params['num_leaves']:4d} hojas, "
          f"hess {trial.params['min_sum_hessian_in_leaf']:.4g} | {trial.user_attrs['minutos']:.1f} min | "
          f"mejor AUC {study.best_value:.5f} | {hechas}/{PARAM['n_trials']} | {datetime.now():%a %H:%M}", flush=True)
    study.trials_dataframe().to_csv(exp.ruta("pruebas"), index=False)
    if hechas >= PARAM["min_pruebas"] and ((LIMITE and datetime.now() >= LIMITE) or APURAR.exists()):
        motivo = "existe APURAR.txt" if APURAR.exists() else f"se paso la hora limite ({PARAM['hora_limite']})"
        print(f"  ** {motivo}: se corta la busqueda con {hechas} pruebas **", flush=True)
        study.stop()


optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(
    direction="maximize", study_name=f"exp{exp.id}",
    storage=f"sqlite:///{(exp.carpeta / f'{exp.id}_optuna.db').as_posix()}", load_if_exists=True,
    sampler=optuna.samplers.TPESampler(seed=PARAM["semilla_sampler"], n_startup_trials=PARAM["n_startup_trials"]))
hechas = len([t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE])
faltan = PARAM["n_trials"] - hechas
if (LIMITE and datetime.now() >= LIMITE) or APURAR.exists():
    faltan = min(faltan, PARAM["min_pruebas"] - hechas)
print(f"\n=== Busqueda: AUC promedio de {PARAM['n_particiones']} particiones 70/30 "
      f"({hechas} hechas, faltan {max(faltan, 0)}; hora limite {PARAM.get('hora_limite')}) ===", flush=True)
if faltan > 0:
    study.optimize(objetivo, n_trials=faltan, callbacks=[informar], catch=(Exception,))
study.trials_dataframe().to_csv(exp.ruta("pruebas"), index=False)

# ---------------------------------------------------------------------------
# Top N por AUC
# ---------------------------------------------------------------------------
completas = sorted([t for t in study.trials if t.value is not None], key=lambda t: t.value, reverse=True)
assert len(completas) >= min(PARAM["min_pruebas"], PARAM["n_trials"]), \
    f"Solo {len(completas)} pruebas completas (minimo {PARAM['min_pruebas']})"
fijos = {k: v for k, v in PARAM["lgbm_fijos"].items() if k != "metric"}
top = []
for t in completas[:PARAM["top_n"]]:
    p = dict(t.params)
    arboles = int(p.pop("num_iterations"))
    top.append({"nombre": f"cv{exp.id}_p{t.number}", "params": {**fijos, **p}, "arboles": arboles,
                "auc_cv": round(t.value, 5), "auc_desvio": round(t.user_attrs["auc_desvio"], 5),
                "meseta_cv_M": t.user_attrs["meseta_M"]})
(exp.carpeta / f"{exp.id}_top.json").write_text(json.dumps(top, indent=2, ensure_ascii=False), encoding="utf-8")
print("\n=== TOP por AUC (validacion interna) ===")
a_lo, a_hi = PARAM["espacio"]["num_iterations"][:2]
for c in top:
    print(f"  {c['nombre']}: AUC {c['auc_cv']} (+/- {c['auc_desvio']}) | meseta {c['meseta_cv_M']} M | "
          f"{c['arboles']} arboles | num_leaves {c['params']['num_leaves']} | "
          f"min_sum_hessian {c['params']['min_sum_hessian_in_leaf']:.4g}")
    if c["arboles"] >= 0.9 * a_hi:
        print(f"    AVISO: {c['arboles']} arboles esta cerca del maximo del rango ({a_hi}); quizas convenia mas.")
corr = pd.DataFrame([{"auc": t.value, "meseta": t.user_attrs["meseta_M"]} for t in completas]).corr(method="spearman")
print(f"\nCorrelacion (Spearman) entre AUC y meseta de las {len(completas)} pruebas: {corr.iloc[0, 1]:.2f}")

try:
    from optuna.visualization import plot_optimization_history, plot_slice
    plot_optimization_history(study).write_html(exp.ruta("historia", ext="html"), include_plotlyjs="cdn")
    plot_slice(study).write_html(exp.ruta("cortes_por_parametro", ext="html"), include_plotlyjs="cdn")
except Exception as e:
    print(f"(No se pudieron generar los graficos de Optuna: {e})")

cerrar_experimento(exp, {"pruebas": len(completas), "top": [c["nombre"] for c in top],
                         "corr_auc_meseta": round(float(corr.iloc[0, 1]), 3)})
