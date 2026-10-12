"""034 — componente binario con ambas bajas SOBRE LAS 855 COLUMNAS (todas las variables con lags): ¿suma al ensemble multiclase M2?
026 lo midió sobre 150 columnas: +9.2/+5.8M con 1 mes de train (A, Bh), −4.6M con 2 meses (B); en el Public (k=12000, 4 meses) b12 quedó +1.32M sobre el multiclase.
Acá, con las columnas de M2 (855, menos las 8 con PSI>0.20) y los min_data del final (50/65/80), en los folds con lag2 real: L y B2 (targets solapados en 202107).
EM = ensemble MC (3 configs M1 top1-3, score condicional, rank medio) | EB = ensemble binario BAJA+1/2 (mismas filas, configs e hiperparámetros) | M50 = rank 50/50 | M67 = 2/3 EM + 1/3 EB.
3 semillas (SEMILLAS_20[2:5]); ganancia = media sobre k=8000..15000 (M ARS). Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/034_binario_todas_lags/run.py   |   tail -f competencia/experimentos/034_binario_todas_lags/log.txt"""
import importlib.util
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(AQUI.parents[0] / "005_optuna"))
spec = importlib.util.spec_from_file_location("t028", AQUI.parents[0] / "028_todas_lags" / "run.py"); t028 = importlib.util.module_from_spec(spec); spec.loader.exec_module(t028)
from multiclase import entrenar, etiquetas, filas, gan_media, score_cond  # noqa: E402
from reevaluar import SEMILLAS_20  # noqa: E402
from validacion import PARAMS_BASE  # noqa: E402

LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
SEMILLAS_034, MIN_DATA = SEMILLAS_20[2:5], {"top1": 50, "top2": 65, "top3": 80}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


rk = lambda ps: np.mean([rankdata(p) / len(p) for p in ps], axis=0)  # noqa: E731

if __name__ == "__main__":
    js = json.loads((t028.A005 / "mejores_trials.json").read_text())
    cfg = {k.split("_")[1]: (d["r"], d["num_boost_round"], {**PARAMS_BASE, **{a: b for a, b in d.items() if a not in ("r", "num_boost_round")}, "min_data_in_leaf": MIN_DATA[k.split("_")[1]]})
           for k, d in js.items() if k.startswith("M1")}
    drop = {l.split("\t")[0] for l in (AQUI.parents[0] / "031_final_todas_lags" / "drop_psi.txt").read_text().splitlines() if l}
    res, t0 = [], time.time()
    escribir(f"\n===== 034 {time.strftime('%Y-%m-%d %H:%M')} | {len(SEMILLAS_034)} semillas | {len(cfg)} configs | min_data {MIN_DATA} =====")
    for fold, (mt, mv) in t028.FOLDS.items():
        dt, dv = t028.construir(mt), t028.construir([mv])
        cols = [c for c in dt.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria") and not c.startswith("canario") and c not in drop]
        y3, yv = etiquetas(dt), (dv["clase_ternaria"] == "BAJA+2").astype(int).values; yb = (y3 >= 1).astype(int)
        for s in SEMILLAS_034:
            PM, PB = [], []
            for nombre, (r, rondas, params) in cfg.items():
                keep = filas(y3, r, s)
                PM.append(score_cond(entrenar(params, dt[cols], y3, keep, s, rondas).predict(dv[cols])))
                PB.append(lgb.train({**params, "seed": s}, lgb.Dataset(dt.loc[keep, cols], label=yb[keep]), num_boost_round=rondas).predict(dv[cols]))
            EM, EB = rk(PM), rk(PB)
            R = {"EM": EM, "EB": EB, "M50": (rankdata(EM) + rankdata(EB)) / (2 * len(yv)), "M67": (2 * rankdata(EM) + rankdata(EB)) / (3 * len(yv))}
            g = {n: gan_media(yv, p) for n, p in R.items()}
            res += [{"fold": fold, "semilla": s, "modelo": n, "M": v} for n, v in g.items()]
            escribir(f"[{fold} s={s}] EM {g['EM']:.1f} | EB {g['EB'] - g['EM']:+.1f} | M50 {g['M50'] - g['EM']:+.1f} | M67 {g['M67'] - g['EM']:+.1f} ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.DataFrame(res); p = r_.pivot_table(index=["fold", "semilla"], columns="modelo", values="M"); filas_ = []
    for v in ("EB", "M50", "M67"):
        d = (p[v] - p["EM"]).groupby("fold")
        filas_.append({"comparacion": f"{v} - EM", **{f"{f}_delta": d.mean()[f] for f in t028.FOLDS}, **{f"{f}_ee": d.std()[f] / np.sqrt(len(SEMILLAS_034)) for f in t028.FOLDS},
                       "pares_positivos": f"{int(((p[v] - p['EM']) > 0).sum())}/{len(p)}"})
    comp = pd.DataFrame(filas_).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + r_.groupby(["modelo", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas vs EM:\n" + comp.to_string(index=False)); escribir("[034] terminado")
