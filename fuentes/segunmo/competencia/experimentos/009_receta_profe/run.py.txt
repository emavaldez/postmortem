"""009 — receta del profe vs. nuestro mejor trial de Optuna (M1 top1), con y sin undersampling, mismas semillas (pareado).

Receta (mensaje del profe, 1.7): max_bin=31, min_data_in_leaf=0, feature_fraction=0.50, feature_fraction_bynode=0.20, learning_rate=0.005,
métrica AUC; lo "bayesiano" son num_iterations, num_leaves y min_sum_hessian_in_leaf. Acá NO corremos un Optuna entero: grilla de
3 num_leaves x 3 min_sum_hessian_in_leaf, y las iteraciones salen gratis (se entrena 3000 rondas una vez y se puntúa en 500/1000/1500/2000/3000).
Dos brazos: r=1.0 (sin undersampling, como pide el profe) y r=0.1 (nuestro hallazgo de 007/005). La referencia es M1 top1 de 005 (Optuna).
Mismas columnas que M1 (top150 con historia, selección por fold solo con el train), ccajas corregida, sin lag2 (un cambio por vez).
Métrica: media de la ganancia sobre k=8000..15000 (como 005) y k=11500; folds A, B, Bh; semillas = las dos primeras propias.
Las ganancias son del mes completo, en millones de ARS. Los mejores se reevalúan después con otras semillas.
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/009_receta_profe/run.py
Progreso:           tail -f competencia/experimentos/009_receta_profe/log.txt"""
import sys
import time
from itertools import product
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from config import SEMILLAS  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from pool import cargar  # noqa: E402
from reevaluar import configs  # noqa: E402
from validacion import KS, xy  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
FOLDS = {"B": ([202103, 202104], 202106), "A": ([202103], 202105), "Bh": ([202104], 202106)}
RONDAS_TOTAL, CHECKPOINTS = 3000, [500, 1000, 1500, 2000, 3000]
HOJAS, HESSIAN, BRAZOS = [8, 32, 128], [0.05, 0.5, 2.0], {"sin_us": 1.0, "us_0.1": 0.1}
RECETA = {"objective": "binary", "metric": "auc", "max_bin": 31, "min_data_in_leaf": 0, "feature_fraction": 0.5,
          "feature_fraction_bynode": 0.2, "learning_rate": 0.005, "feature_pre_filter": False, "verbose": -1, "num_threads": 0}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def fila(base, p, yv, nombre, rondas):
    acum = ganancia_acumulada(yv, p)
    return {**base, "config": nombre, "rondas": rondas, "auc": roc_auc_score(yv, p),
            "gan_media_k": np.mean([acum[k - 1] for k in KS]), "gan_k11500": acum[11500 - 1]}


if __name__ == "__main__":
    ref_r, ref_rondas, ref_params = configs()[("M1", "top1")]
    filas, t0 = [], time.time()
    escribir(f"\n===== 009 {time.strftime('%Y-%m-%d %H:%M')} | grilla {len(HOJAS)}x{len(HESSIAN)} x brazos {list(BRAZOS)} | semillas {SEMILLAS[:2]} =====")
    for fold, (mt, mv) in FOLDS.items():
        (Xt, yt), (Xv, yv) = xy(cargar(mt, negocio=True)), xy(cargar([mv], negocio=True))
        cols = (A005 / "sel" / f"top150_{fold}.txt").read_text().split()
        Xt, Xv, yt, yv = Xt[cols], Xv[cols], yt.values, yv.values
        escribir(f"[{fold}] train {Xt.shape} ({yt.sum()} BAJA+2) -> valid {mv}")
        for s in SEMILLAS[:2]:
            base = {"fold": fold, "semilla": s}
            m = lgb.train({**ref_params, "seed": s}, lgb.Dataset(Xt[(yt == 1) | (np.random.RandomState(s).rand(len(yt)) < ref_r)],
                          label=yt[(yt == 1) | (np.random.RandomState(s).rand(len(yt)) < ref_r)]), num_boost_round=ref_rondas)
            filas.append(fila({**base, "brazo": "ref"}, m.predict(Xv), yv, "ref_M1_top1_optuna", ref_rondas))
            escribir(f"[{fold} s={s}] ref M1 top1 Optuna: {filas[-1]['gan_media_k']/1e6:.1f}M ({(time.time()-t0)/60:.0f} min)")
            for brazo, r in BRAZOS.items():
                keep = (yt == 1) | (np.random.RandomState(s).rand(len(yt)) < r)
                ds = lgb.Dataset(Xt[keep], label=yt[keep], free_raw_data=False)
                for hojas, h in product(HOJAS, HESSIAN):
                    t1 = time.time()
                    m = lgb.train({**RECETA, "num_leaves": hojas, "min_sum_hessian_in_leaf": h, "seed": s}, ds, num_boost_round=RONDAS_TOTAL)
                    for n in CHECKPOINTS:
                        filas.append(fila({**base, "brazo": brazo}, m.predict(Xv, num_iteration=n), yv, f"hojas{hojas}_h{h}", n))
                    g = [f for f in filas[-len(CHECKPOINTS):]]
                    mejor = max(g, key=lambda f: f["gan_media_k"])
                    escribir(f"[{fold} s={s}] {brazo} hojas={hojas} hess={h}: mejor {mejor['gan_media_k']/1e6:.1f}M en {mejor['rondas']} rondas "
                             f"({time.time()-t1:.0f}s, total {(time.time()-t0)/60:.0f} min)")
                    pd.DataFrame(filas).to_csv(CSV, index=False)
    pd.DataFrame(filas).to_csv(CSV, index=False); escribir("[009] terminado")
