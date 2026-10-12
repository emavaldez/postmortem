"""020 — pesos por cercanía del mes: ¿darle más peso a los meses recientes mejora? (014 mostró que duplicar el mes MÁS VIEJO perjudica: -3.7M.)
Multiclase M1 top1 de 005, score condicional, ccajas corregida; 6 semillas (SEMILLAS_20[2:8]); folds con 2 meses de train:
  B  : train 202103 + 202104 -> valid 202106        (limpio)
  B2 : train 202104 + 202105 -> valid 202106        (targets solapados en 202107, como en 008b/016: informa la diferencia pareada)
Variantes (peso del mes más viejo : peso del más reciente): P11 (base) | P12 | P13. El peso va en lgb.Dataset(weight=...).
Ganancia = media sobre k=8000..15000 (M ARS). Uso (raíz del repo): venv/bin/python competencia/experimentos/020_pesos_recientes/run.py   |   tail -f competencia/experimentos/020_pesos_recientes/log.txt"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from config import MES_COL  # noqa: E402
from multiclase import entrenar, etiquetas, filas, gan_media, score_cond  # noqa: E402
from pool import cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
FOLDS = {"B": ([202103, 202104], 202106, "top150_B.txt"), "B2": ([202104, 202105], 202106, "top150_Bh.txt")}
SEMILLAS_020, VARIANTES = SEMILLAS_20[2:8], {"P11": 1.0, "P12": 2.0, "P13": 3.0}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]
    res, t0 = [], time.time()
    escribir(f"\n===== 020 {time.strftime('%Y-%m-%d %H:%M')} | {len(SEMILLAS_020)} semillas =====")
    for fold, (mt, mv, selec) in FOLDS.items():
        dt, dv = cargar(mt, negocio=True), cargar([mv], negocio=True)
        cols = (A005 / "sel" / selec).read_text().split(); Xt, Xv = dt[cols], dv[cols]
        y3, yv = etiquetas(dt), (dv["clase_ternaria"] == "BAJA+2").astype(int).values
        reciente = (dt[MES_COL].values == max(mt))
        for s in SEMILLAS_020:
            keep, g = filas(y3, r, s), {}
            for nombre, w in VARIANTES.items():
                peso = np.where(reciente, w, 1.0)
                g[nombre] = gan_media(yv, score_cond(entrenar(params, Xt, y3, keep, s, rondas, peso).predict(Xv)))
                res.append({"fold": fold, "semilla": s, "variante": nombre, "M": g[nombre]})
            escribir(f"[{fold} s={s}] P11 {g['P11']:.1f} | P12 {g['P12'] - g['P11']:+.1f} | P13 {g['P13'] - g['P11']:+.1f} ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.DataFrame(res); p = r_.pivot_table(index=["fold", "semilla"], columns="variante", values="M"); filas_ = []
    for v in ("P12", "P13"):
        d = (p[v] - p["P11"]).groupby("fold")
        filas_.append({"variante": f"{v} - P11", **{f"{f}_delta": d.mean()[f] for f in FOLDS}, **{f"{f}_ee": d.std()[f] / np.sqrt(len(SEMILLAS_020)) for f in FOLDS},
                       "pares_positivos": f"{int(((p[v] - p['P11']) > 0).sum())}/{len(p)}"})
    comp = pd.DataFrame(filas_).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + r_.groupby(["variante", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas:\n" + comp.to_string(index=False)); escribir("[020] terminado")
