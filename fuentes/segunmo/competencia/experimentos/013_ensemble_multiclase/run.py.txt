"""013 — ¿el ENSEMBLE multiclase (6 configuraciones de 005 pasadas a multiclase) conserva la ventaja de B1 sobre el MIX6 binario?
B1 midió un solo modelo (M1 top1): +7.5/+10.5/+8.3M. Acá: las mismas 6 configuraciones del MIX6 de 005 (3 mejores trials de M0 y de M1, cada uno con su r y sus
hiperparámetros) entrenadas como multiclase (BAJA+1 y BAJA+2 completos + fracción r de CONTINUA), score P(BAJA+2)/(1-P(BAJA+1)), ccajas corregida.
Se comparan, pareado por (fold, semilla), contra el MIX6 binario de 009b (`009b_ensemble_receta/resultados.csv`: mismas 5 semillas SEMILLAS_20[2:7], mismos folds y columnas).
Ensembles: MC_MIX6 (media de probabilidades), MC_MIX6_rank (media de ranks), MC_M1 (solo las 3 de M1: ¿aporta M0?). Folds A, B, Bh. Ganancia = media sobre k=8000..15000 (M ARS).
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/013_ensemble_multiclase/run.py   |   tail -f competencia/experimentos/013_ensemble_multiclase/log.txt"""
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent
A005, A009B = AQUI.parents[0] / "005_optuna", AQUI.parents[0] / "009b_ensemble_receta"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from config import TARGET_COL  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from optuna_run import es_hist  # noqa: E402
from pool import cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402
from validacion import KS, xy  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
SEMILLAS_013 = SEMILLAS_20[2:7]
CLASES = {"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    cfg = {k: v for k, v in configs().items() if k[1].startswith("top")}
    filas, t0 = [], time.time()
    escribir(f"\n===== 013 {time.strftime('%Y-%m-%d %H:%M')} | semillas {SEMILLAS_013} =====")
    for fold, (mt, mv) in FOLDS.items():
        dt, dv = cargar(mt, negocio=True), cargar([mv], negocio=True)
        Xt0, _ = xy(dt)
        cols = {"M0": [c for c in Xt0.columns if not es_hist(c)], "M1": (A005 / "sel" / f"top150_{fold}.txt").read_text().split()}
        y3 = dt[TARGET_COL].map(CLASES).values; yv = (dv[TARGET_COL] == "BAJA+2").astype(int).values
        for s in SEMILLAS_013:
            P, u = {}, np.random.RandomState(s)
            for (c, nombre), (r, rondas, params) in cfg.items():
                keep = (y3 >= 1) | (np.random.RandomState(s).rand(len(y3)) < r)
                m = lgb.train({**params, "objective": "multiclass", "num_class": 3, "seed": s}, lgb.Dataset(dt.loc[keep, cols[c]], label=y3[keep]), num_boost_round=rondas)
                pm = m.predict(dv[cols[c]]); P[f"{c}_{nombre}"] = pm[:, 2] / np.clip(1 - pm[:, 1], 1e-6, None)
            rk = lambda ps: np.mean([rankdata(p) / len(p) for p in ps], axis=0)   # noqa: E731
            m1 = [p for k, p in P.items() if k.startswith("M1")]
            E = {**P, "MC_MIX6": np.mean(list(P.values()), axis=0), "MC_MIX6_rank": rk(list(P.values())), "MC_M1_rank": rk(m1)}
            for nombre, p in E.items():
                acum = ganancia_acumulada(yv, p)
                filas.append({"fold": fold, "semilla": s, "modelo": nombre, "auc": roc_auc_score(yv, p),
                              "gan_media_k": np.mean([acum[k - 1] for k in KS]), "gan_k11500": acum[11500 - 1]})
            g = {f["modelo"]: f["gan_media_k"] / 1e6 for f in filas[-len(E):]}
            escribir(f"[{fold} s={s}] MC_MIX6 {g['MC_MIX6']:.1f} | rank {g['MC_MIX6_rank']:.1f} | solo M1 {g['MC_M1_rank']:.1f} | M1_top1 {g['M1_top1']:.1f} ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(filas).to_csv(CSV, index=False)
    res = pd.DataFrame(filas); res.to_csv(CSV, index=False); res["M"] = res.gan_media_k / 1e6
    bin_ = pd.read_csv(A009B / "resultados.csv"); bin_["M"] = bin_.gan_media_k / 1e6
    pb = bin_[bin_.modelo.isin(["MIX6", "MIX6_rank"])].pivot_table(index=["fold", "semilla"], columns="modelo", values="M").add_prefix("BIN_")
    p = res.pivot_table(index=["fold", "semilla"], columns="modelo", values="M").join(pb); comp = []
    for a, b in [("MC_MIX6", "BIN_MIX6"), ("MC_MIX6_rank", "BIN_MIX6_rank"), ("MC_MIX6_rank", "MC_MIX6"), ("MC_M1_rank", "MC_MIX6_rank")]:
        d = (p[a] - p[b]).groupby("fold"); fila = {"comparacion": f"{a} - {b}"}
        for f in FOLDS:
            fila[f"{f}_delta"], fila[f"{f}_ee"] = d.mean()[f], d.std()[f] / np.sqrt(len(SEMILLAS_013))
        fila["pares_positivos"] = f"{int(((p[a] - p[b]) > 0).sum())}/{len(p)}"; comp.append(fila)
    comp = pd.DataFrame(comp).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + pd.concat([res.groupby(["modelo", "fold"]).M.mean().unstack(), p[["BIN_MIX6", "BIN_MIX6_rank"]].groupby("fold").mean().T]).round(1).to_string())
    escribir("\nDiferencias pareadas:\n" + comp.to_string(index=False)); escribir("[013] terminado")
