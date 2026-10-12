"""035 — features de TENDENCIA por variable sobre las 855 columnas de M2: aceleración = v - 2*lag1 + lag2 y cambio relativo a la media de 3 meses = v / mean(v, lag1, lag2) - 1,
para cada una de las 142 variables (menos las que tienen lag2/d2 excluidas por PSI: su lag2 apunta a junio en 202108). Son combinaciones de v, lag1 y lag2 que un árbol no arma fácil.
Un cambio: E2 (855 columnas) vs E2 + tendencias. Multiclase M1 top1 con min_data_in_leaf=50 (el final), folds L y B2, 3 semillas (SEMILLAS_20[2:5]); ganancia = media sobre k=8000..15000 (M ARS).
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/035_tendencias/run.py   |   tail -f competencia/experimentos/035_tendencias/log.txt"""
import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(AQUI.parents[0] / "005_optuna"))
spec = importlib.util.spec_from_file_location("t028", AQUI.parents[0] / "028_todas_lags" / "run.py"); t028 = importlib.util.module_from_spec(spec); spec.loader.exec_module(t028)
from multiclase import entrenar, etiquetas, filas, gan_media, score_cond  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402

LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
SEMILLAS_035 = SEMILLAS_20[2:5]


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def tendencias(d: pd.DataFrame, variables: list) -> pd.DataFrame:
    out = {}
    for v in variables:
        x, l1, l2 = d[v], d[f"{v}_lag1"], d[f"{v}_lag2"]
        out[f"{v}_acel"] = x - 2 * l1 + l2
        media = (x + l1 + l2) / 3
        out[f"{v}_rel3"] = x / media.replace(0, np.nan) - 1
    return pd.DataFrame(out, index=d.index).astype("float32")


if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]; params = {**params, "min_data_in_leaf": 50}
    drop = {l.split("\t")[0] for l in (AQUI.parents[0] / "031_final_todas_lags" / "drop_psi.txt").read_text().splitlines() if l}
    variables = [v for v in t028.V142 if f"{v}_lag2" not in drop and f"{v}_d2" not in drop]
    res, t0 = [], time.time()
    escribir(f"\n===== 035 {time.strftime('%Y-%m-%d %H:%M')} | {len(SEMILLAS_035)} semillas | {len(variables)} variables con tendencia (de {len(t028.V142)}) =====")
    for fold, (mt, mv) in t028.FOLDS.items():
        dt, dv = t028.construir(mt), t028.construir([mv])
        cols = [c for c in dt.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria") and not c.startswith("canario") and c not in drop]
        Tt, Tv = tendencias(dt, variables), tendencias(dv, variables)
        Xt, Xv = pd.concat([dt[cols], Tt], axis=1), pd.concat([dv[cols], Tv], axis=1)
        y3, yv = etiquetas(dt), (dv["clase_ternaria"] == "BAJA+2").astype(int).values
        escribir(f"[{fold}] columnas: E2 {len(cols)} | E2+tendencias {Xt.shape[1]}")
        for s in SEMILLAS_035:
            keep = filas(y3, r, s)
            g = {"E2": gan_media(yv, score_cond(entrenar(params, dt[cols], y3, keep, s, rondas).predict(dv[cols]))),
                 "E2_tend": gan_media(yv, score_cond(entrenar(params, Xt, y3, keep, s, rondas).predict(Xv)))}
            res += [{"fold": fold, "semilla": s, "variante": n, "M": v} for n, v in g.items()]
            escribir(f"[{fold} s={s}] E2 {g['E2']:.1f} | +tendencias {g['E2_tend'] - g['E2']:+.1f} ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.DataFrame(res); p = r_.pivot_table(index=["fold", "semilla"], columns="variante", values="M"); d = (p["E2_tend"] - p["E2"]).groupby("fold")
    comp = pd.DataFrame([{"comparacion": "E2_tend - E2", **{f"{f}_delta": d.mean()[f] for f in t028.FOLDS}, **{f"{f}_ee": d.std()[f] / np.sqrt(len(SEMILLAS_035)) for f in t028.FOLDS},
                          "pares_positivos": f"{int(((p['E2_tend'] - p['E2']) > 0).sum())}/{len(p)}"}]).round(2)
    comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + r_.groupby(["variante", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencia pareada:\n" + comp.to_string(index=False)); escribir("[035] terminado")
