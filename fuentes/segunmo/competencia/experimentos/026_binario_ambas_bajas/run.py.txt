"""026 — binario con AMBAS bajas como positivos (BAJA+1 y BAJA+2), el experimento 006 del plan que nunca se corrió. Lo usan compañeros con Public > 100.
Mismas filas de entrenamiento que el multiclase (BAJA+1, BAJA+2 y fracción r de CONTINUA), mismas columnas (M1 top150 por fold) y mismos hiperparámetros (M1 top1 de 005):
cambia solo el objetivo. La ganancia se mide siempre sobre BAJA+2 (lo que paga), con corte por cantidad de envíos.
Variantes: MC_cond (referencia: multiclase, score P2/(1-P1)) | MC_suma (P1+P2 del mismo multiclase) | B12 (binario BAJA+1/2 vs CONTINUA) |
  B12_w05 (binario con peso 0.5 en BAJA+1) | MC+B12 (rank medio de MC_cond y B12).
Folds A, B, Bh; 5 semillas (SEMILLAS_20[2:7]); ccajas corregida. Ganancia = media sobre k=8000..15000 (M ARS).
Uso (raíz del repo): venv/bin/python competencia/experimentos/026_binario_ambas_bajas/run.py   |   tail -f competencia/experimentos/026_binario_ambas_bajas/log.txt"""
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import rankdata

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
SEMILLAS_026 = SEMILLAS_20[2:7]


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]
    res, t0 = [], time.time()
    escribir(f"\n===== 026 {time.strftime('%Y-%m-%d %H:%M')} | {len(SEMILLAS_026)} semillas =====")
    for fold, (mt, mv) in FOLDS.items():
        dt, dv = cargar(mt, negocio=True), cargar([mv], negocio=True)
        cols = (A005 / "sel" / f"top150_{fold}.txt").read_text().split(); Xt, Xv = dt[cols], dv[cols]
        y3, yv = etiquetas(dt), (dv["clase_ternaria"] == "BAJA+2").astype(int).values
        yb = (y3 >= 1).astype(int)
        for s in SEMILLAS_026:
            keep = filas(y3, r, s); P = {}
            pm = entrenar(params, Xt, y3, keep, s, rondas).predict(Xv)
            P["MC_cond"], P["MC_suma"] = score_cond(pm), pm[:, 1] + pm[:, 2]
            P["B12"] = lgb.train({**params, "seed": s}, lgb.Dataset(Xt[keep], label=yb[keep]), num_boost_round=rondas).predict(Xv)
            w = np.where(y3 == 1, 0.5, 1.0)
            P["B12_w05"] = lgb.train({**params, "seed": s}, lgb.Dataset(Xt[keep], label=yb[keep], weight=w[keep]), num_boost_round=rondas).predict(Xv)
            P["MC+B12"] = (rankdata(P["MC_cond"]) + rankdata(P["B12"])) / (2 * len(yv))
            g = {n: gan_media(yv, p) for n, p in P.items()}
            res += [{"fold": fold, "semilla": s, "variante": n, "M": v} for n, v in g.items()]
            escribir(f"[{fold} s={s}] MC_cond {g['MC_cond']:.1f} | " + " | ".join(f"{n} {v - g['MC_cond']:+.1f}" for n, v in g.items() if n != "MC_cond") + f" ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.DataFrame(res); p = r_.pivot_table(index=["fold", "semilla"], columns="variante", values="M"); filas_ = []
    for v in ("MC_suma", "B12", "B12_w05", "MC+B12"):
        d = (p[v] - p["MC_cond"]).groupby("fold")
        filas_.append({"variante": f"{v} - MC_cond", **{f"{f}_delta": d.mean()[f] for f in FOLDS}, **{f"{f}_ee": d.std()[f] / np.sqrt(len(SEMILLAS_026)) for f in FOLDS},
                       "pares_positivos": f"{int(((p[v] - p['MC_cond']) > 0).sum())}/{len(p)}"})
    comp = pd.DataFrame(filas_).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + r_.groupby(["variante", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas vs MC_cond:\n" + comp.to_string(index=False)); escribir("[026] terminado")
