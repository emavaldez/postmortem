"""018 — tres chequeos baratos sobre el multiclase M1 top1 (respuesta a la revisión del 08-oct), 5 semillas (SEMILLAS_20[2:7]), ccajas corregida.
(A) FAMILIA DE SCORES con el mismo modelo multiclase (P0,P1,P2): P2 | P2/(1-P1) (actual) | P2+P1 | P2+alpha*P1 (alpha en 0.1,0.25,0.5,1,2).
    Regla: elegir alpha mirando solo el fold A (el mes menos usado); adoptarlo solo si también gana en B y Bh. Sirve además para explicar QUÉ aporta el score condicional.
(B) POSITIVOS ESPERADOS en 202108: suma de P2 del modelo / positivos reales, en A (-> 202105) y B (-> 202106), y suma de P2 en 202108 con el modelo entrenado en 202103-06.
    Estimación = suma_P2(202108) / razón_observada. Usa 3 semillas. Es una pista del k óptimo (≈ 9-11 veces los positivos, según 015), no una medida exacta: la razón varía por fold.
(C) RONDAS vs TAMAÑO DEL TRAIN: se entrena 1400 rondas y se puntúa en 300..1400; Bh (1 mes de train) vs B (2 meses) vs A (1 mes). Si el óptimo sube con más datos, el final (4 meses) estaría sub-ajustado.
Ganancia = media sobre k=8000..15000 (M ARS). Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/018_score_y_rondas/run.py   |   tail -f competencia/experimentos/018_score_y_rondas/log.txt"""
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from config import MES_SCORING, TARGET_COL  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from pool import cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402
from validacion import KS  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG = AQUI / "log.txt"
FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
SEMILLAS_018, CHECK = SEMILLAS_20[2:7], [300, 500, 688, 900, 1100, 1400]
ALFAS = [0.1, 0.25, 0.5, 1.0, 2.0]
CLASES = {"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def gan(yv, p):
    acum = ganancia_acumulada(yv, p)
    return np.mean([acum[k - 1] for k in KS]) / 1e6


def scores(pm):
    p1, p2 = pm[:, 1], pm[:, 2]
    S = {"P2": p2, "P2/(1-P1)": p2 / np.clip(1 - p1, 1e-6, None), "P2+P1": p2 + p1}
    S.update({f"P2+{a}*P1": p2 + a * p1 for a in ALFAS if a != 1.0})
    return S


if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]
    mc = {**params, "objective": "multiclass", "num_class": 3}
    filas_s, filas_r, razones, t0 = [], [], {}, time.time()
    escribir(f"\n===== 018 {time.strftime('%Y-%m-%d %H:%M')} | semillas {SEMILLAS_018} | M1 top1: r={r:.3f}, {rondas} rondas =====")
    for fold, (mt, mv) in FOLDS.items():
        dt, dv = cargar(mt, negocio=True), cargar([mv], negocio=True)
        cols = (A005 / "sel" / f"top150_{fold}.txt").read_text().split()
        y3 = dt[TARGET_COL].map(CLASES).values; yv = (dv[TARGET_COL] == "BAJA+2").astype(int).values
        for s in SEMILLAS_018:
            keep = (y3 >= 1) | (np.random.RandomState(s).rand(len(y3)) < r)
            m = lgb.train({**mc, "seed": s}, lgb.Dataset(dt.loc[keep, cols], label=y3[keep]), num_boost_round=max(CHECK))
            for n in CHECK:                                              # (C) rondas
                filas_r.append({"fold": fold, "semilla": s, "rondas": n, "M": gan(yv, scores(m.predict(dv[cols], num_iteration=n))["P2/(1-P1)"])})
            pm = m.predict(dv[cols], num_iteration=rondas)                # (A) scores al número de rondas de Optuna
            for nombre, p in scores(pm).items():
                filas_s.append({"fold": fold, "semilla": s, "score": nombre, "M": gan(yv, p)})
            if fold != "Bh" and s in SEMILLAS_018[:3]:                    # (B) razón suma(P2)/positivos
                razones.setdefault(fold, []).append(pm[:, 2].sum() / yv.sum())
            escribir(f"[{fold} s={s}] actual {filas_s[-len(scores(pm)) + 1]['M']:.1f} | " + " ".join(f"{f['score']}={f['M']:.1f}" for f in filas_s[-len(scores(pm)):]) + f" ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(filas_s).to_csv(AQUI / "scores.csv", index=False); pd.DataFrame(filas_r).to_csv(AQUI / "rondas.csv", index=False)
    # (B) 202108: modelo entrenado con 202103-06 (columnas top150_final), suma de P2
    dt4 = cargar([202103, 202104, 202105, 202106], negocio=True); sc = cargar([MES_SCORING], solo_con_target=False, negocio=True)
    cols = (A005 / "sel" / "top150_final.txt").read_text().split(); y3 = dt4[TARGET_COL].map(CLASES).values; sumas = []
    for s in SEMILLAS_018[:3]:
        keep = (y3 >= 1) | (np.random.RandomState(s).rand(len(y3)) < r)
        sumas.append(lgb.train({**mc, "seed": s}, lgb.Dataset(dt4.loc[keep, cols], label=y3[keep]), num_boost_round=rondas).predict(sc[cols])[:, 2].sum())
        escribir(f"[202108 s={s}] suma(P2) = {sumas[-1]:.0f} ({(time.time()-t0)/60:.0f} min)")
    # resúmenes
    S = pd.DataFrame(filas_s); T = S.groupby(["score", "fold"]).M.mean().unstack()[["A", "B", "Bh"]]
    T["B-A"] = T["B"] - T.loc["P2/(1-P1)", "B"]; base = T.loc["P2/(1-P1)", ["A", "B", "Bh"]]
    rel = T[["A", "B", "Bh"]].sub(base, axis=1).round(2); rel.columns = ["A_vs_actual", "B_vs_actual", "Bh_vs_actual"]
    escribir("\n(A) Familia de scores (M ARS) y diferencia contra el score actual P2/(1-P1):\n" + pd.concat([T[["A", "B", "Bh"]].round(1), rel], axis=1).to_string())
    R = pd.DataFrame(filas_r).groupby(["rondas", "fold"]).M.mean().unstack().round(1)
    escribir("\n(C) Ganancia por número de rondas (M ARS); el óptimo por fold es el máximo de cada columna:\n" + R.to_string()
             + "\nóptimo: " + ", ".join(f"{f}: {int(R[f].idxmax())} rondas" for f in R.columns))
    ra = {f: float(np.mean(v)) for f, v in razones.items()}; est = {f: float(np.mean(sumas)) / v for f, v in ra.items()}
    pos = {"A": 870, "B": 1098}
    escribir("\n(B) Razón suma(P2)/positivos reales: " + ", ".join(f"{f}: {v:.2f}" for f, v in ra.items())
             + f" | suma(P2) en 202108: {np.mean(sumas):.0f}\nPositivos esperados en 202108 con la razón de A: {est['A']:.0f}; con la de B: {est['B']:.0f}"
             + f" (referencia: 202105 = 870, 202106 = 1098). k≈9-11x → {9*min(est.values()):.0f}-{11*max(est.values()):.0f}")
    escribir("[018] terminado")
