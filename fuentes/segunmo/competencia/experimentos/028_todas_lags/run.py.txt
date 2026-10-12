"""028 — la receta de los compañeros con Public > 100: lag1 y lag2 y diferencias (d1, d2) de TODAS las variables (≈ 760 columnas), sin selección, en el MULTICLASE con los
hiperparámetros tuneados de 005 (008c lo probó en binario con parámetros base). Folds con lag2 real en el train (como 016): L (202105 -> 202106) y B2 (202104+05 -> 202106),
con el solapamiento de targets en 202107 (informan la diferencia pareada, no el nivel). 4 semillas (SEMILLAS_20[2:6]); ccajas corregida.
  V0 M1 top150 (referencia) | V1 = V0 + lag2/delta2/ratio2 de las 50 variables (lo que usa el final, 016) | V2 = pool completo (345 cols) + lag1/delta1 de las 142 variables
  de 008c que faltaban + lag2/delta2 de las 142 (≈ 800 columnas, sin selección).
Ganancia = media sobre k=8000..15000 (M ARS). Uso (raíz del repo): venv/bin/python competencia/experimentos/028_todas_lags/run.py   |   tail -f competencia/experimentos/028_todas_lags/log.txt"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
A005, A008C = AQUI.parents[0] / "005_optuna", AQUI.parents[0] / "008c_lags_150"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from historia import agregar_historia_n  # noqa: E402
from multiclase import entrenar, etiquetas, filas, gan_media, score_cond  # noqa: E402
from pool import VARS, cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
FOLDS = {"L": ([202105], 202106), "B2": ([202104, 202105], 202106)}
SEMILLAS_028 = SEMILLAS_20[2:6]
V142 = (A008C / "variables_150.txt").read_text().split()
EXTRA = [v for v in V142 if v not in VARS]
LAG2_50 = [f"{v}_{s}2" for v in VARS for s in ("lag", "d", "r")]


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def construir(meses, solo_con_target=True):
    """DataFrame con todo lo necesario: pool (345) + lag2 de las 50 (para V1) + lag1/d1 de las 92 extra + lag2/d2 de las 142 (para V2)."""
    d = cargar(meses, solo_con_target=solo_con_target, negocio=True).copy()
    d = agregar_historia_n(d, VARS, 2)                                   # lag2/d2/r2 de las 50 (V1)
    l1 = agregar_historia_n(d[["numero_de_cliente", "foto_mes"] + EXTRA].copy(), EXTRA, 1).drop(columns=["numero_de_cliente", "foto_mes"] + EXTRA)
    l1 = l1[[c for c in l1.columns if not c.endswith("_r1")]]
    d = pd.concat([d, l1], axis=1)
    # lag2/d2 de las 92 extra (las 50 ya las tienen)
    l2 = agregar_historia_n(d[["numero_de_cliente", "foto_mes"] + EXTRA], EXTRA, 2).drop(columns=["numero_de_cliente", "foto_mes"] + EXTRA)
    l2 = l2[[c for c in l2.columns if not c.endswith("_r2")]]
    d = pd.concat([d, l2], axis=1)
    c = d.select_dtypes("float64").columns
    d[c] = d[c].astype("float32")
    return d


if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]
    base = (A005 / "sel" / "top150_Bh.txt").read_text().split()
    res, t0 = [], time.time()
    escribir(f"\n===== 028 {time.strftime('%Y-%m-%d %H:%M')} | {len(SEMILLAS_028)} semillas | {len(V142)} variables ({len(EXTRA)} extra) =====")
    for fold, (mt, mv) in FOLDS.items():
        dt, dv = construir(mt), construir([mv])
        todas = [c for c in dt.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria") and not c.startswith("canario")]
        sets = {"V0_top150": base, "V1_lag2_50": base + LAG2_50, "V2_todas_lags": todas}
        escribir(f"[{fold}] columnas: " + ", ".join(f"{n} {len(c)}" for n, c in sets.items()))
        y3, yv = etiquetas(dt), (dv["clase_ternaria"] == "BAJA+2").astype(int).values
        for s in SEMILLAS_028:
            keep, g = filas(y3, r, s), {}
            for n, cs in sets.items():
                g[n] = gan_media(yv, score_cond(entrenar(params, dt[cs], y3, keep, s, rondas).predict(dv[cs])))
                res.append({"fold": fold, "semilla": s, "variante": n, "M": g[n]})
            escribir(f"[{fold} s={s}] V0 {g['V0_top150']:.1f} | V1 {g['V1_lag2_50'] - g['V0_top150']:+.1f} | V2 {g['V2_todas_lags'] - g['V0_top150']:+.1f} ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.DataFrame(res); p = r_.pivot_table(index=["fold", "semilla"], columns="variante", values="M"); filas_ = []
    for a, b in [("V1_lag2_50", "V0_top150"), ("V2_todas_lags", "V0_top150"), ("V2_todas_lags", "V1_lag2_50")]:
        d = (p[a] - p[b]).groupby("fold")
        filas_.append({"comparacion": f"{a} - {b}", **{f"{f}_delta": d.mean()[f] for f in FOLDS}, **{f"{f}_ee": d.std()[f] / np.sqrt(len(SEMILLAS_028)) for f in FOLDS},
                       "pares_positivos": f"{int(((p[a] - p[b]) > 0).sum())}/{len(p)}"})
    comp = pd.DataFrame(filas_).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + r_.groupby(["variante", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas:\n" + comp.to_string(index=False)); escribir("[028] terminado")
