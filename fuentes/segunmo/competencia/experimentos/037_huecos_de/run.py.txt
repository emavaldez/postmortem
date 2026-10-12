"""037d / 037e — segundo lote del plan de cierre de huecos (COBERTURA.md §8; reglas fijadas antes de correr). Mismo harness que 036/037:
train 202103–06 → valid 202107, tarea BAJA+1, binario, M2 = 855 columnas, hiperparámetros de M1 top1 salvo que se indique.
  037d  M2 SIN undersampling (profe 1.7): r = 0.3 y r = 1.0 contra la base r = 0.0986 (la base se lee de 037_huecos_abc/resultados.csv: mismas semillas, mismo modelo).
        5 semillas (SEMILLAS_20[2:7]). Confusión conocida y declarada: con más filas, `min_data_in_leaf` pesa relativamente menos; no se retunea.
  037e  Diversidad (profe 2.1): ensemble de las 3 configuraciones M1 vs 6 (M1 top1-3 + M0 top1-3), mismas 855 columnas, rank medio, 8 semillas (SEMILLAS_20[2:10]).
Estadística: t pareado unilateral; la decisión BH q=0.10 con m=8 se toma al final sobre TODA la familia (037a–f) con `bh_final.py`; pasa solo si BH Y Δ ≥ +3M.
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/037_huecos_de/run.py   |   tail -f competencia/experimentos/037_huecos_de/log.txt"""
import importlib.util
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("m37", AQUI.parents[0] / "037_huecos_abc" / "run.py"); m37 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m37)
t028 = m37.t028
from multiclase import gan_media  # noqa: E402
from reevaluar import SEMILLAS_20  # noqa: E402
from validacion import PARAMS_BASE  # noqa: E402

LOG = AQUI / "log.txt"
S5, S8 = SEMILLAS_20[2:7], SEMILLAS_20[2:10]


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def cfg(js, clave):
    d = js[clave]
    return d["r"], d["num_boost_round"], {**PARAMS_BASE, **{a: b for a, b in d.items() if a not in ("r", "num_boost_round")}}


def test(dd):
    t, p2 = stats.ttest_1samp(dd, 0.0)
    return p2 / 2 if t > 0 else 1 - p2 / 2


if __name__ == "__main__":
    js = json.loads((t028.A005 / "mejores_trials.json").read_text())
    r0, rondas0, params0 = cfg(js, "M1_top1")
    drop = {l.split("\t")[0] for l in (AQUI.parents[0] / "031_final_todas_lags" / "drop_psi.txt").read_text().splitlines() if l}
    t0 = time.time()
    dt = t028.construir([202103, 202104, 202105, 202106]); dv = t028.construir([202107], solo_con_target=False)
    yt, yv = (dt["clase_ternaria"] == "BAJA+1").astype(int).values, (dv["clase_ternaria"] == "BAJA+1").astype(int).values
    todas = [c for c in dt.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria") and not c.startswith("canario") and c not in drop]
    Xt, Xv = dt[todas], dv[todas]
    escribir(f"\n===== 037 d/e {time.strftime('%Y-%m-%d %H:%M')} | train {dt.shape} | {len(todas)} columnas =====")
    # ---------------- 037d ----------------
    base = pd.read_csv(AQUI.parents[0] / "037_huecos_abc" / "resultados.csv").query("variante == 'BASE'").set_index("semilla")
    res = []
    for s in S5:
        g = {"BASE": base.loc[s, "M"]}
        for r in (0.3, 1.0):
            keep = (yt == 1) | (np.random.RandomState(s).rand(len(yt)) < r)
            p = lgb.train({**params0, "seed": s}, lgb.Dataset(Xt.loc[keep], label=yt[keep]), num_boost_round=rondas0).predict(Xv)
            res.append({"semilla": s, "variante": f"037d_r{r}", "M": gan_media(yv, p), "auc": roc_auc_score(yv, p), "filas": int(keep.sum())}); g[f"r{r}"] = res[-1]["M"]
        escribir(f"[037d s={s}] BASE(r=0.0986) {g['BASE']:.1f} | r=0.3 {g['r0.3'] - g['BASE']:+.1f} | r=1.0 {g['r1.0'] - g['BASE']:+.1f} ({(time.time()-t0)/60:.0f} min)")
        pd.DataFrame(res).to_csv(AQUI / "resultados_d.csv", index=False)
    R = pd.DataFrame(res); filas = []
    for v in ("037d_r0.3", "037d_r1.0"):
        dd = R[R.variante == v].set_index("semilla").M - base.loc[S5, "M"]
        filas.append({"variante": v, "delta_M": dd.mean(), "ee": dd.std() / np.sqrt(len(dd)), "pares+": f"{int((dd > 0).sum())}/{len(dd)}", "p_unilateral": test(dd),
                      "delta_auc": (R[R.variante == v].set_index("semilla").auc - base.loc[S5, "auc"]).mean()})
    D = pd.DataFrame(filas); D.round(4).to_csv(AQUI / "comparacion_d.csv", index=False)
    escribir("\n037d — contra BASE (r=0.0986), 5 semillas:\n" + D.round(4).to_string(index=False))
    # ---------------- 037e ----------------
    claves = ["M1_top1", "M1_top2", "M1_top3", "M0_top1", "M0_top2", "M0_top3"]; res = []
    for s in S8:
        P = {}
        for k in claves:
            r, rondas, params = cfg(js, k)
            keep = (yt == 1) | (np.random.RandomState(s).rand(len(yt)) < r)
            P[k] = lgb.train({**params, "seed": s}, lgb.Dataset(Xt.loc[keep], label=yt[keep]), num_boost_round=rondas).predict(Xv)
        rk = lambda ks: np.mean([rankdata(P[k]) / len(yv) for k in ks], axis=0)  # noqa: E731
        E3, E6 = rk(claves[:3]), rk(claves)
        res.append({"semilla": s, "E3_M1": gan_media(yv, E3), "E6_M1M0": gan_media(yv, E6), "auc3": roc_auc_score(yv, E3), "auc6": roc_auc_score(yv, E6),
                    **{f"solo_{k}": gan_media(yv, P[k]) for k in claves}})
        escribir(f"[037e s={s}] E3 (M1) {res[-1]['E3_M1']:.1f} | E6 (M1+M0) {res[-1]['E6_M1M0'] - res[-1]['E3_M1']:+.1f} | solos: " + ", ".join(f"{k} {res[-1]['solo_' + k]:.0f}" for k in claves) + f" ({(time.time()-t0)/60:.0f} min)")
        pd.DataFrame(res).to_csv(AQUI / "resultados_e.csv", index=False)
    R = pd.DataFrame(res); dd = R.E6_M1M0 - R.E3_M1
    E = pd.DataFrame([{"variante": "037e_E6-E3", "delta_M": dd.mean(), "ee": dd.std() / np.sqrt(len(dd)), "pares+": f"{int((dd > 0).sum())}/{len(dd)}", "p_unilateral": test(dd),
                       "delta_auc": (R.auc6 - R.auc3).mean()}])
    E.round(4).to_csv(AQUI / "comparacion_e.csv", index=False)
    escribir("\n037e — E6 (M1+M0) contra E3 (M1), 8 semillas:\n" + E.round(4).to_string(index=False) + "\n[037 d/e] terminado")
