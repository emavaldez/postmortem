"""022 — opciones de LightGBM que nunca exploramos, sobre el multiclase M1 top1 de 005 (mismas rondas y r): un cambio por variante.
  base | extra_trees | path_smooth=5 | path_smooth=20 | min_gain_to_split=0.5 | extra_trees + path_smooth=5
Folds A, B, Bh; 4 semillas (SEMILLAS_20[2:6]); columnas M1 top150 por fold. Pareado contra la base. Ganancia = media sobre k=8000..15000 (M ARS).
Uso (raíz del repo): venv/bin/python competencia/experimentos/022_opciones_lgbm/run.py   |   tail -f competencia/experimentos/022_opciones_lgbm/log.txt"""
import sys
import time
from pathlib import Path

import numpy as np
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
SEMILLAS_022 = SEMILLAS_20[2:6]
VARIANTES = {"base": {}, "extra_trees": {"extra_trees": True}, "path_smooth5": {"path_smooth": 5}, "path_smooth20": {"path_smooth": 20},
             "min_gain0.5": {"min_gain_to_split": 0.5}, "extra+smooth5": {"extra_trees": True, "path_smooth": 5}}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]
    res, t0 = [], time.time()
    escribir(f"\n===== 022 {time.strftime('%Y-%m-%d %H:%M')} | {len(SEMILLAS_022)} semillas =====")
    for fold, (mt, mv) in FOLDS.items():
        dt, dv = cargar(mt, negocio=True), cargar([mv], negocio=True)
        cols = (A005 / "sel" / f"top150_{fold}.txt").read_text().split(); Xt, Xv = dt[cols], dv[cols]
        y3, yv = etiquetas(dt), (dv["clase_ternaria"] == "BAJA+2").astype(int).values
        for s in SEMILLAS_022:
            keep, g = filas(y3, r, s), {}
            for nombre, extra in VARIANTES.items():
                g[nombre] = gan_media(yv, score_cond(entrenar({**params, **extra}, Xt, y3, keep, s, rondas).predict(Xv)))
                res.append({"fold": fold, "semilla": s, "variante": nombre, "M": g[nombre]})
            escribir(f"[{fold} s={s}] base {g['base']:.1f} | " + " | ".join(f"{n} {v - g['base']:+.1f}" for n, v in g.items() if n != "base") + f" ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.DataFrame(res); p = r_.pivot_table(index=["fold", "semilla"], columns="variante", values="M"); filas_ = []
    for v in VARIANTES:
        if v == "base":
            continue
        d = (p[v] - p["base"]).groupby("fold")
        filas_.append({"variante": v, **{f"{f}_delta": d.mean()[f] for f in FOLDS}, **{f"{f}_ee": d.std()[f] / np.sqrt(len(SEMILLAS_022)) for f in FOLDS},
                       "pares_positivos": f"{int(((p[v] - p['base']) > 0).sum())}/{len(p)}"})
    comp = pd.DataFrame(filas_).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + r_.groupby(["variante", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas vs base:\n" + comp.to_string(index=False)); escribir("[022] terminado")
