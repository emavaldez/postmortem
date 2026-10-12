"""005 paso 2 — reevaluación honesta de los mejores trials: semillas DISTINTAS a las de la búsqueda (10 de SEMILLAS_20[2:]),
folds A, B y Bh (Bh no se usó en la búsqueda), ganancia = media sobre k=8000..15000 y k=11000.
Compara, por set (M0, M1): base_r1 (params del baseline, sin undersampling), base_r02 (trial 0), top1..top3 de Optuna, y mezclas:
MIX1 = promedio de las probabilidades de top1(M0) y top1(M1);  MIX6 = promedio de los 3 mejores de cada set.
Uso (raíz del repo): venv/bin/python competencia/experimentos/005_optuna/reevaluar.py"""
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from optuna_run import CONJUNTOS, DB, PARAMS_BASE, es_hist, escribir  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from pool import cargar  # noqa: E402
from validacion import KS, xy  # noqa: E402

FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
from config import SEMILLAS_20  # noqa: E402,F811  (explícitas en config.py; antes se leían de 002/resultados_20s.csv)
SEMILLAS_REEVAL = SEMILLAS_20[2:12]
N_TOP = 3


def params_de(p: dict):
    r, rounds = p["r"], p["num_boost_round"]
    return r, rounds, {**PARAMS_BASE, **{k: v for k, v in p.items() if k not in ("r", "num_boost_round")}}


def configs():
    """{(conjunto, nombre): (r, rounds, params)}"""
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    cfg = {}
    for c in CONJUNTOS:
        e = optuna.load_study(study_name=c, storage=f"sqlite:///{DB}")
        ok = sorted([t for t in e.trials if t.state == optuna.trial.TrialState.COMPLETE], key=lambda t: -t.value)
        cfg[(c, "base_r1")] = (1.0, 300, dict(PARAMS_BASE))
        cfg[(c, "base_r02")] = params_de(e.trials[0].params)
        for i, t in enumerate(ok[:N_TOP], 1):
            cfg[(c, f"top{i}")] = params_de(t.params)
            escribir(f"[reeval] {c} top{i}: trial #{t.number} índice búsqueda {t.value:.4f} | {t.params}")
    return cfg


if __name__ == "__main__":
    cfg = configs(); filas = []; t0 = time.time()
    escribir(f"\n===== reevaluación {time.strftime('%Y-%m-%d %H:%M')} | semillas {SEMILLAS_REEVAL} =====")
    for fold, (mt, mv) in FOLDS.items():
        (Xt, yt), (Xv, yv) = xy(cargar(mt, negocio=True)), xy(cargar([mv], negocio=True))
        cols = {"M0": [c for c in Xt.columns if not es_hist(c)],
                "M1": (AQUI / "sel" / f"top150_{fold}.txt").read_text().split()}
        yt, yv = yt.values, yv.values
        for s in SEMILLAS_REEVAL:
            P = {}
            for (c, nombre), (r, rounds, params) in cfg.items():
                keep = (yt == 1) | (np.random.RandomState(s).rand(len(yt)) < r)
                m = lgb.train({**params, "seed": s}, lgb.Dataset(Xt.loc[keep, cols[c]], label=yt[keep]), num_boost_round=rounds)
                P[(c, nombre)] = m.predict(Xv[cols[c]])
            P[("MIX", "MIX1")] = (P[("M0", "top1")] + P[("M1", "top1")]) / 2
            P[("MIX", "MIX6")] = np.mean([P[(c, f"top{i}")] for c in CONJUNTOS for i in range(1, N_TOP + 1)], axis=0)
            P[("MIX", "MIX_base_r02")] = (P[("M0", "base_r02")] + P[("M1", "base_r02")]) / 2
            for (c, nombre), p in P.items():
                acum = ganancia_acumulada(yv, p)
                filas.append({"fold": fold, "semilla": s, "conjunto": c, "config": nombre, "auc": roc_auc_score(yv, p),
                              "gan_media_k": np.mean([acum[k - 1] for k in KS]), **{f"gan_k{k}": acum[k - 1] for k in KS}})
            escribir(f"[reeval] fold {fold} semilla {s} listo ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(filas).to_csv(AQUI / "reevaluacion.csv", index=False)
    res = pd.DataFrame(filas); res.to_csv(AQUI / "reevaluacion.csv", index=False)
    tabla = (res.groupby(["conjunto", "config", "fold"]).gan_media_k.mean().div(1e6).round(1).unstack())
    print(tabla.to_string()); escribir("[reeval] terminado")
