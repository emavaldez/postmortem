"""024 — modelos de la RECETA del profe para el final: multiclase SIN undersampling, 512 hojas, min_sum_hessian 0.05, 800 rondas, lr 0.005, min_data_in_leaf 0,
ff 0.5, bynode 0.2 (023), columnas M1 top150_final, train 202103–06 (654k filas, todas), score P2/(1-P1) sobre 202108. Un modelo por semilla; se guarda cada uno en tmp/
(se puede cortar y reanudar). Salida: tmp/scores_rec_202108.csv con el promedio de scores y su rank.
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/024_final_receta/final_rec.py --semillas 8   |   tail -f competencia/experimentos/024_final_receta/log.txt"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
config.CORREGIR_CCAJAS = True
from config import ID_COL, MES_SCORING, SEMILLAS  # noqa: E402
from modelos import guardar_modelo, verificar_orden_cache  # noqa: E402
from multiclase import entrenar, etiquetas, filas, score_cond  # noqa: E402
from pool import cargar  # noqa: E402

LOG, TMP = AQUI / "log.txt", AQUI / "tmp"
RECETA = {"max_bin": 31, "min_data_in_leaf": 0, "feature_fraction": 0.5, "feature_fraction_bynode": 0.2, "learning_rate": 0.005,
          "min_sum_hessian_in_leaf": 0.05, "num_leaves": 512, "feature_pre_filter": False, "verbose": -1, "num_threads": 0, "deterministic": True, "force_row_wise": True}
RONDAS = 800


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--semillas", type=int, default=8); args = ap.parse_args()
    semillas = config.semillas(args.semillas)                       # semillas explícitas en config.py (5 propias + derivadas)
    TMP.mkdir(exist_ok=True)
    dt = cargar([202103, 202104, 202105, 202106], negocio=True); score = cargar([MES_SCORING], solo_con_target=False, negocio=True)
    cols = (A005 / "sel" / "top150_final.txt").read_text().split(); y3 = etiquetas(dt)
    escribir(f"\n===== 024 final receta {time.strftime('%Y-%m-%d %H:%M')} | train {dt[cols].shape} | {len(semillas)} semillas =====")
    verificar_orden_cache(TMP, score[ID_COL].values)                    # no mezclar predicciones cacheadas con otro orden de filas
    t0, ps = time.time(), []
    for s in semillas:
        f = TMP / f"rec_{s}.npy"
        if not f.exists():
            m = entrenar(RECETA, dt[cols], y3, filas(y3, 1.0, s), s, RONDAS)
            sc_ = score_cond(m.predict(score[cols]))
            guardar_modelo(m, f"024_receta_{s}", sc_)
            np.save(f, sc_)
        ps.append(np.load(f)); escribir(f"semilla {s} lista ({(time.time()-t0)/60:.0f} min)")
    p = np.mean(ps, axis=0)
    pd.DataFrame({ID_COL: score[ID_COL].values, "score": p, "rank": rankdata(p) / len(p)}).to_csv(TMP / "scores_rec_202108.csv", index=False)
    escribir("[024 final receta] terminado")
