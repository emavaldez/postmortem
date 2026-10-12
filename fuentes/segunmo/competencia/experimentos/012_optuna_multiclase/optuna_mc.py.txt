"""012 — Optuna para el MULTICLASE (B1). Los hiperparámetros de 005 se tunearon para el binario; el multiclase (3 árboles por ronda, BAJA+1 completo)
podría preferir otros. Un solo estudio sobre M1 (top150 con historia por fold, el set que mejor anda), score P(BAJA+2)/(1-P(BAJA+1)).

Cada trial: sortea r (fracción de CONTINUA que se conserva; BAJA+1 y BAJA+2 completos) y los hiperparámetros, entrena en los folds A y B con las 2 semillas
de búsqueda y devuelve el ÍNDICE = media de (ganancia_fold / referencia_fold), con ganancia = media sobre k=8000..15000. Referencias = nivel del multiclase
M1 top1 de 005 en B1 (A 237M, B 406M): índice 1.000 ≈ el modelo actual. Bh NO entra a la búsqueda (se usa después para reevaluar con semillas nuevas).
Los 3 primeros trials son M1 top1/2/3 de 005 (anclas: deberían dar ~1.0 con estas semillas). Pruner tras el fold A.
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/012_optuna_multiclase/optuna_mc.py --horas 4     (parar: crear el archivo STOP en esta carpeta)
Seguimiento:        tail -f competencia/experimentos/012_optuna_multiclase/optuna_log.txt        |  resumen: venv/bin/python competencia/experimentos/012_optuna_multiclase/progreso.py"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from config import RAIZ, SEMILLAS, TARGET_COL  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from pool import cargar  # noqa: E402
from reevaluar import configs  # noqa: E402
from validacion import KS, PARAMS_BASE  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, DB = AQUI / "optuna_log.txt", RAIZ / "artifacts" / "optuna" / "012_optuna_mc.db"
FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106)}
REFERENCIA = {"A": 237e6, "B": 406e6}
SEMILLAS_BUSQUEDA = SEMILLAS[:2]
CLASES = {"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}
ESPACIO = {"r": (0.03, 0.3), "num_leaves": (8, 256), "learning_rate": (0.005, 0.1), "min_data_in_leaf": (10, 500), "feature_fraction": (0.1, 0.8),
           "bagging_fraction": (0.4, 1.0), "lambda_l1": (1e-3, 10), "lambda_l2": (1e-3, 100), "num_boost_round": (100, 1000)}


def escribir(texto: str):
    with open(LOG, "a") as f:
        f.write(texto + "\n")


def preparar_datos() -> dict:
    datos = {}
    for fold, (mt, mv) in FOLDS.items():
        dt, dv = cargar(mt, negocio=True), cargar([mv], negocio=True)
        cols = (A005 / "sel" / f"top150_{fold}.txt").read_text().split()
        datos[fold] = (dt[cols].copy(), dt[TARGET_COL].map(CLASES).values, dv[cols].copy(), (dv[TARGET_COL] == "BAJA+2").astype(int).values)
        escribir(f"[datos] fold {fold}: train {datos[fold][0].shape}")
    return datos


def objetivo(trial: optuna.Trial, datos: dict) -> float:
    e = ESPACIO
    r = trial.suggest_float("r", *e["r"], log=True)
    params = {**PARAMS_BASE, "objective": "multiclass", "num_class": 3,
              "num_leaves": trial.suggest_int("num_leaves", *e["num_leaves"], log=True),
              "learning_rate": trial.suggest_float("learning_rate", *e["learning_rate"], log=True),
              "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", *e["min_data_in_leaf"], log=True),
              "feature_fraction": trial.suggest_float("feature_fraction", *e["feature_fraction"]),
              "bagging_fraction": trial.suggest_float("bagging_fraction", *e["bagging_fraction"]),
              "lambda_l1": trial.suggest_float("lambda_l1", *e["lambda_l1"], log=True),
              "lambda_l2": trial.suggest_float("lambda_l2", *e["lambda_l2"], log=True)}
    rondas = trial.suggest_int("num_boost_round", *e["num_boost_round"], log=True)
    indices = []
    for paso, fold in enumerate(FOLDS):
        Xt, y3, Xv, yv = datos[fold]
        gans = []
        for s in SEMILLAS_BUSQUEDA:
            keep = (y3 >= 1) | (np.random.RandomState(s).rand(len(y3)) < r)
            m = lgb.train({**params, "seed": s}, lgb.Dataset(Xt[keep], label=y3[keep]), num_boost_round=rondas)
            pm = m.predict(Xv); acum = ganancia_acumulada(yv, pm[:, 2] / np.clip(1 - pm[:, 1], 1e-6, None))
            gans.append(np.mean([acum[k - 1] for k in KS]))
        g = float(np.mean(gans)); trial.set_user_attr(f"gan_{fold}", g / 1e6); indices.append(g / REFERENCIA[fold])
        trial.report(float(np.mean(indices)), paso)
        if trial.should_prune():
            raise optuna.TrialPruned()
    return float(np.mean(indices))


def callback(study: optuna.Study, trial: optuna.trial.FrozenTrial):
    seg = (trial.datetime_complete - trial.datetime_start).total_seconds()
    ok = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    mejor = f"mejor {study.best_value:.4f} (#{study.best_trial.number})" if ok else "mejor -"
    resumen = " ".join(f"{k}={v:.3g}" if isinstance(v, float) else f"{k}={v}" for k, v in trial.params.items())
    val = f"{trial.value:.4f}" if trial.value is not None else "  -   "
    gan = f"A {trial.user_attrs.get('gan_A', float('nan')):.1f}M B {trial.user_attrs.get('gan_B', float('nan')):.1f}M"
    escribir(f"{datetime.now():%m-%d %H:%M:%S} #{trial.number:<4} {trial.state.name:<8} índice {val} ({gan}) {seg:4.0f}s | {mejor} | "
             f"{len(ok)} ok/{len(study.trials)} total | {resumen}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--horas", type=float, default=4.0)
    args = ap.parse_args()
    DB.parent.mkdir(parents=True, exist_ok=True)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    escribir(f"\n===== inicio {datetime.now():%Y-%m-%d %H:%M} | presupuesto {args.horas} h | semillas de búsqueda {SEMILLAS_BUSQUEDA} =====")
    datos = preparar_datos()
    e = optuna.create_study(study_name="MC_M1", storage=f"sqlite:///{DB}", load_if_exists=True, direction="maximize",
                            sampler=optuna.samplers.TPESampler(seed=SEMILLAS[1], multivariate=True, n_startup_trials=20),
                            pruner=optuna.pruners.PercentilePruner(75.0, n_startup_trials=12, n_warmup_steps=0))
    if len(e.trials) == 0:                        # anclas: los 3 mejores del binario (M1) pasados a multiclase
        for i in (1, 2, 3):
            r, rondas, p = configs()[("M1", f"top{i}")]
            e.enqueue_trial({"r": r, "num_boost_round": rondas, **{k: p[k] for k in ("num_leaves", "learning_rate", "min_data_in_leaf",
                             "feature_fraction", "bagging_fraction", "lambda_l1", "lambda_l2")}})
    fin = time.time() + args.horas * 3600
    try:
        while time.time() < fin and not (AQUI / "STOP").exists():
            e.optimize(lambda t: objetivo(t, datos), n_trials=1, callbacks=[callback])
    except KeyboardInterrupt:
        pass
    escribir(f"===== fin {datetime.now():%Y-%m-%d %H:%M} =====")
