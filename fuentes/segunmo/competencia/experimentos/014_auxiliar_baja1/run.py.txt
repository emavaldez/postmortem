"""014 — modelo auxiliar de BAJA+1 con un mes más de datos (idea del alumno + research B2) y control de pesos.

Contexto: en 202108 conocemos BAJA+1 de 202107 (quién no está en 202108) pero no su BAJA+2. El score condicional P(BAJA+2)/(1-P(BAJA+1)) necesita P(BAJA+1),
que se puede estimar con ese mes extra, el más cercano a 202108. Réplica honesta en los folds de validación: el mes "extra" es 202105 (BAJA+1 conocido porque ya
vemos 202106; su BAJA+2 NO se usa).
  Fold B : principal multiclase entrena 202103+04, auxiliar entrena 202103+04+05 -> valida 202106
  Fold Bh: principal entrena 202104,         auxiliar entrena 202104+05          -> valida 202106
Principal = multiclase de M1 top1 (005), filas = BAJA+1, BAJA+2 y fracción r de CONTINUA (como B1). Auxiliar = binario BAJA+1 vs resto (el resto, incluido BAJA+2,
submuestreado con la misma r; para 202105 la clase solo distingue BAJA+1), mismas columnas M1 y mismos hiperparámetros. Sin leakage: nadie ve el target de 202106.
Variantes (score = P2_principal / (1 - P1)):
  V0_actual     P1 = la del propio multiclase principal                                  (referencia)
  V1_aux_extra  P1 = auxiliar entrenado con el mes extra
  V2_aux_mismos P1 = auxiliar entrenado con los MISMOS meses que el principal           (control: ¿el cambio viene del mes extra o de usar un binario aparte?)
  V3_prom       P1 = promedio de la del principal y la del auxiliar con mes extra
  V4_peso2      (solo fold B) principal con peso 2 en 202103 (= "copiar el mes más viejo"); P1 propia. Control: duplicar no agrega información, se espera ~0.
10 semillas nuevas (SEMILLAS_20[2:12]). Ganancia = media sobre k=8000..15000 (M ARS).
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/014_auxiliar_baja1/run.py   |   tail -f competencia/experimentos/014_auxiliar_baja1/log.txt"""
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from config import MES_COL, TARGET_COL  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from pool import cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402
from validacion import KS  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
FOLDS = {"B": ([202103, 202104], 202105, 202106), "Bh": ([202104], 202105, 202106)}   # (meses principal, mes extra, valid)
SEMILLAS_014 = SEMILLAS_20[2:12]
CLASES = {"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def ganancia(yv, p):
    acum = ganancia_acumulada(yv, p)
    return np.mean([acum[k - 1] for k in KS])


if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]
    filas, t0 = [], time.time()
    escribir(f"\n===== 014 {time.strftime('%Y-%m-%d %H:%M')} | r={r:.3f} rondas={rondas} | {len(SEMILLAS_014)} semillas =====")
    for fold, (mt, mextra, mv) in FOLDS.items():
        dt, dx, dv = cargar(mt, negocio=True), cargar([mextra], negocio=True), cargar([mv], negocio=True)
        cols = (A005 / "sel" / f"top150_{fold}.txt").read_text().split()
        Xt, Xx, Xv = dt[cols], dx[cols], dv[cols]
        y3 = dt[TARGET_COL].map(CLASES).values
        y1_t, y1_x = (y3 == 1).astype(int), (dx[TARGET_COL] == "BAJA+1").astype(int).values     # del mes extra SOLO se usa BAJA+1
        Xa, y1_a = pd.concat([Xt, Xx], ignore_index=True), np.r_[y1_t, y1_x]
        yv = (dv[TARGET_COL] == "BAJA+2").astype(int).values
        w = np.where(dt[MES_COL].values == 202103, 2.0, 1.0)
        escribir(f"[{fold}] principal {Xt.shape} | auxiliar +mes extra {Xa.shape} (BAJA+1: {y1_a.sum()}) -> valid {mv}")
        for s in SEMILLAS_014:
            keep = (y3 >= 1) | (np.random.RandomState(s).rand(len(y3)) < r)
            mc = lgb.train({**params, "objective": "multiclass", "num_class": 3, "seed": s}, lgb.Dataset(Xt[keep], label=y3[keep]), num_boost_round=rondas)
            pm = mc.predict(Xv); p2, p1_prop = pm[:, 2], pm[:, 1]
            def aux(X, y):                     # binario BAJA+1 vs resto (resto submuestreado con la misma r)
                k = (y == 1) | (np.random.RandomState(s + 1).rand(len(y)) < r)
                return lgb.train({**params, "seed": s}, lgb.Dataset(X[k], label=y[k]), num_boost_round=rondas).predict(Xv)
            p1_extra, p1_mismos = aux(Xa, y1_a), aux(Xt, y1_t)
            P = {"V0_actual": p2 / np.clip(1 - p1_prop, 1e-6, None), "V1_aux_extra": p2 / np.clip(1 - p1_extra, 1e-6, None),
                 "V2_aux_mismos": p2 / np.clip(1 - p1_mismos, 1e-6, None), "V3_prom": p2 / np.clip(1 - (p1_prop + p1_extra) / 2, 1e-6, None)}
            if fold == "B":
                mw = lgb.train({**params, "objective": "multiclass", "num_class": 3, "seed": s}, lgb.Dataset(Xt[keep], label=y3[keep], weight=w[keep]), num_boost_round=rondas)
                pw = mw.predict(Xv); P["V4_peso2"] = pw[:, 2] / np.clip(1 - pw[:, 1], 1e-6, None)
            for n, p in P.items():
                filas.append({"fold": fold, "semilla": s, "variante": n, "auc": roc_auc_score(yv, p), "gan_media_k": ganancia(yv, p)})
            g = {f["variante"]: f["gan_media_k"] / 1e6 for f in filas[-len(P):]}
            escribir(f"[{fold} s={s}] V0 {g['V0_actual']:.1f} | " + " | ".join(f"{n[:2]} {v - g['V0_actual']:+.1f}" for n, v in g.items() if n != "V0_actual") + f" ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(filas).to_csv(CSV, index=False)
    res = pd.DataFrame(filas); res.to_csv(CSV, index=False); res["M"] = res.gan_media_k / 1e6
    p = res.pivot_table(index=["fold", "semilla"], columns="variante", values="M"); comp = []
    for a, b in [("V1_aux_extra", "V0_actual"), ("V2_aux_mismos", "V0_actual"), ("V1_aux_extra", "V2_aux_mismos"), ("V3_prom", "V0_actual"), ("V4_peso2", "V0_actual")]:
        d = (p[a] - p[b]).dropna().groupby("fold"); fila = {"comparacion": f"{a} - {b}"}
        for f in FOLDS:
            fila[f"{f}_delta"], fila[f"{f}_ee"] = (d.mean().get(f, np.nan), d.std().get(f, np.nan) / np.sqrt(len(SEMILLAS_014)))
        fila["pares_positivos"] = f"{int(((p[a] - p[b]).dropna() > 0).sum())}/{len((p[a] - p[b]).dropna())}"; comp.append(fila)
    comp = pd.DataFrame(comp).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + res.groupby(["variante", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas:\n" + comp.to_string(index=False)); escribir("[014] terminado")
