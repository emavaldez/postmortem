"""029 — control del 028: ¿la ganancia de 'todas las variables con lag1, lag2 y diferencias' viene de la información o de un artefacto de los folds solapados?
V2 (todas las columnas, 863) contra V2c: mismas columnas, pero las columnas HISTÓRICAS (lags, diferencias, ratios) barajadas dentro de cada mes en el TRAIN (el valid queda intacto):
mantiene distribuciones y patrón de NaN, rompe el vínculo con el cliente. Si V2c ≈ V2, la ganancia era un artefacto (calendario/solapamiento); si V2c << V2, es información real.
Folds L y B2 (como 016/028), 4 semillas (SEMILLAS_20[2:6]), multiclase M1 top1. Ganancia = media sobre k=8000..15000 (M ARS).
Uso (raíz del repo): venv/bin/python competencia/experimentos/029_control_todas_lags/run.py   |   tail -f competencia/experimentos/029_control_todas_lags/log.txt"""
import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(AQUI.parents[0] / "005_optuna"))
spec = importlib.util.spec_from_file_location("t028", AQUI.parents[0] / "028_todas_lags" / "run.py"); t028 = importlib.util.module_from_spec(spec); spec.loader.exec_module(t028)
from historia import barajar_historia  # noqa: E402
from multiclase import entrenar, etiquetas, filas, gan_media, score_cond  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402

LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
SEMILLAS_029 = SEMILLAS_20[2:6]


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]
    res, t0 = [], time.time()
    escribir(f"\n===== 029 {time.strftime('%Y-%m-%d %H:%M')} | {len(SEMILLAS_029)} semillas =====")
    for fold, (mt, mv) in t028.FOLDS.items():
        dt, dv = t028.construir(mt), t028.construir([mv])
        todas = [c for c in dt.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria") and not c.startswith("canario")]
        hist = [c for c in todas if "_lag" in c or c.endswith(("_d1", "_d2", "_r1", "_r2"))]
        dtc = barajar_historia(dt, 852583, cols=hist)
        y3, yv = etiquetas(dt), (dv["clase_ternaria"] == "BAJA+2").astype(int).values
        escribir(f"[{fold}] columnas {len(todas)}, de ellas históricas (barajadas en V2c): {len(hist)}")
        for s in SEMILLAS_029:
            keep = filas(y3, r, s)
            g = {"V2": gan_media(yv, score_cond(entrenar(params, dt[todas], y3, keep, s, rondas).predict(dv[todas]))),
                 "V2c": gan_media(yv, score_cond(entrenar(params, dtc[todas], y3, keep, s, rondas).predict(dv[todas])))}
            res += [{"fold": fold, "semilla": s, "variante": n, "M": v} for n, v in g.items()]
            escribir(f"[{fold} s={s}] V2 {g['V2']:.1f} | V2c (historia barajada) {g['V2c'] - g['V2']:+.1f} ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.DataFrame(res); p = r_.pivot_table(index=["fold", "semilla"], columns="variante", values="M"); d = (p["V2c"] - p["V2"]).groupby("fold")
    comp = pd.DataFrame([{"comparacion": "V2c - V2", **{f"{f}_delta": d.mean()[f] for f in t028.FOLDS}, **{f"{f}_ee": d.std()[f] / np.sqrt(len(SEMILLAS_029)) for f in t028.FOLDS},
                          "pares_positivos": f"{int(((p['V2c'] - p['V2']) > 0).sum())}/{len(p)}"}]).round(2)
    comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + r_.groupby(["variante", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencia pareada:\n" + comp.to_string(index=False)); escribir("[029] terminado")
