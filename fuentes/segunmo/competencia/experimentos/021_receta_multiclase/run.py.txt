"""021 — la receta del profe EN MULTICLASE, sin undersampling y con menos rondas (cierra el agujero de 009).
En 009 (binario) el mejor punto sin undersampling estaba en el primer checkpoint (500 rondas, lr 0.005) y en el borde de la grilla (128 hojas): nunca se vio el óptimo.
Receta: max_bin 31, min_data_in_leaf 0, feature_fraction 0.5, feature_fraction_bynode 0.2, learning_rate 0.005; se entrena 800 rondas y se puntúa en 100/200/300/500/800.
Grilla: num_leaves {128, 256, 512} x min_sum_hessian_in_leaf {0.05, 2.0}; dos brazos: r=1.0 (sin undersampling, lo que pide el profe) y r=0.1 (el nuestro).
Referencia: M1 top1 multiclase de 005 (r=0.099, 688 rondas) con las mismas semillas. Folds A, B, Bh; 2 semillas (SEMILLAS_20[2:4]); columnas M1 top150 por fold.
Ganancia = media sobre k=8000..15000 (M ARS). Uso (raíz del repo): venv/bin/python competencia/experimentos/021_receta_multiclase/run.py   |   tail -f competencia/experimentos/021_receta_multiclase/log.txt"""
import sys
import time
from itertools import product
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from multiclase import entrenar, etiquetas, filas, gan_media, score_cond  # noqa: E402
from pool import cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
SEMILLAS_021, CHECK = SEMILLAS_20[2:4], [100, 200, 300, 500, 800]
RECETA = {"max_bin": 31, "min_data_in_leaf": 0, "feature_fraction": 0.5, "feature_fraction_bynode": 0.2, "learning_rate": 0.005,
          "feature_pre_filter": False, "verbose": -1, "num_threads": 0}
HOJAS, HESSIAN, BRAZOS = [128, 256, 512], [0.05, 2.0], {"sin_us": 1.0, "us_0.1": 0.1}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]
    res, t0 = [], time.time()
    escribir(f"\n===== 021 {time.strftime('%Y-%m-%d %H:%M')} | {len(SEMILLAS_021)} semillas | grilla {len(HOJAS)}x{len(HESSIAN)} x {len(BRAZOS)} brazos =====")
    for fold, (mt, mv) in FOLDS.items():
        dt, dv = cargar(mt, negocio=True), cargar([mv], negocio=True)
        cols = (A005 / "sel" / f"top150_{fold}.txt").read_text().split(); Xt, Xv = dt[cols], dv[cols]
        y3, yv = etiquetas(dt), (dv["clase_ternaria"] == "BAJA+2").astype(int).values
        for s in SEMILLAS_021:
            res.append({"fold": fold, "semilla": s, "config": "REF_optuna", "rondas": rondas,
                        "M": gan_media(yv, score_cond(entrenar(params, Xt, y3, filas(y3, r, s), s, rondas).predict(Xv)))})
            escribir(f"[{fold} s={s}] ref Optuna {res[-1]['M']:.1f}M ({(time.time()-t0)/60:.0f} min)")
            for brazo, rr in BRAZOS.items():
                keep = filas(y3, rr, s)
                for hojas, h in product(HOJAS, HESSIAN):
                    t1 = time.time()
                    m = entrenar({**RECETA, "num_leaves": hojas, "min_sum_hessian_in_leaf": h}, Xt, y3, keep, s, max(CHECK))
                    ult = []
                    for n in CHECK:
                        ult.append({"fold": fold, "semilla": s, "config": f"{brazo}_h{hojas}_hs{h}", "rondas": n, "M": gan_media(yv, score_cond(m.predict(Xv, num_iteration=n)))})
                    res += ult; mej = max(ult, key=lambda x: x["M"])
                    escribir(f"[{fold} s={s}] {brazo} hojas={hojas} hess={h}: mejor {mej['M']:.1f}M a {mej['rondas']} rondas ({time.time()-t1:.0f}s, total {(time.time()-t0)/60:.0f} min)")
                    pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.DataFrame(res); ref = r_[r_.config == "REF_optuna"].groupby("fold").M.mean()
    t = r_[r_.config != "REF_optuna"].groupby(["config", "rondas", "fold"]).M.mean().unstack()[["A", "B", "Bh"]]
    for f in ["A", "B", "Bh"]:
        t[f"{f}_vs_ref"] = t[f] - ref[f]
    t["media_vs_ref"] = t[[c for c in t.columns if c.endswith("_vs_ref")]].mean(axis=1)
    escribir("\nReferencia Optuna (M ARS): " + ", ".join(f"{f} {v:.1f}" for f, v in ref.items()))
    escribir("Mejores 12 configuraciones de la receta (diferencia contra la referencia):\n" + t.sort_values("media_vs_ref", ascending=False).head(12).round(1).to_string())
    escribir("\nMejor por brazo:\n" + t.reset_index().assign(brazo=lambda d: d.config.str.split("_h").str[0]).sort_values("media_vs_ref", ascending=False).groupby("brazo").head(1).round(1).to_string(index=False))
    escribir("[021] terminado")
