"""033 — EXTENSIÓN de 032: en 032 `min_data_in_leaf` 15 → 27 → 50 mejoraba de forma monótona (−4.1/−0.9, base, +6.3/+3.8) y 50 era el borde de lo probado. Acá 80, 120 y 200, con las mismas semillas y folds
(se compara contra `base` y `mindata50` de 032, que se leen de su resultados.csv). Original 032 — búsqueda DIRIGIDA de hiperparámetros para M2 (855 columnas: todas las variables con lag1, lag2 y diferencias, menos las 8 con PSI>0.20 de 031).
Los hiperparámetros de M1 top1 se tunearon para 150 columnas (feature_fraction 0.129 ≈ 19 columnas por árbol; con 855 columnas son ~110). Un cambio por vez sobre M1 top1 (r=0.0986, 688 rondas,
160 hojas, min_data_in_leaf 27, lr 0.0101, ff 0.129): feature_fraction {0.05, 0.08, 0.20, 0.35} | num_leaves {100, 256} | min_data_in_leaf {15, 50} | rondas (se puntúa en 500/688/900/1100).
No es un Optuna: L y B2 validan el mismo mes (202106, targets solapados), no hay fold independiente para certificar; se acepta un cambio solo si mejora en AMBOS folds por más de ~2 ee pareados.
Folds L y B2; 3 semillas (SEMILLAS_20[2:5]); multiclase, score condicional; ganancia = media sobre k=8000..15000 (M ARS).
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/032_busqueda_dirigida/run.py   |   tail -f competencia/experimentos/032_busqueda_dirigida/log.txt"""
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
SEMILLAS_032 = SEMILLAS_20[2:5]
VARIANTES = {f"mindata{v}": {"min_data_in_leaf": v} for v in (80, 120, 200)}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]
    drop = {l.split("\t")[0] for l in (AQUI.parents[0] / "031_final_todas_lags" / "drop_psi.txt").read_text().splitlines() if l}
    prev = pd.read_csv(AQUI.parents[0] / "032_busqueda_dirigida" / "resultados.csv")
    res, t0 = [], time.time()
    escribir(f"\n===== 032 {time.strftime('%Y-%m-%d %H:%M')} | {len(SEMILLAS_032)} semillas | columnas excluidas por PSI: {len(drop)} =====")
    for fold, (mt, mv) in t028.FOLDS.items():
        dt, dv = t028.construir(mt), t028.construir([mv])
        cols = [c for c in dt.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria") and not c.startswith("canario") and c not in drop]
        y3, yv = etiquetas(dt), (dv["clase_ternaria"] == "BAJA+2").astype(int).values
        for s in SEMILLAS_032:
            keep, g = filas(y3, r, s), {}
            for nombre, extra in VARIANTES.items():
                g[nombre] = gan_media(yv, score_cond(entrenar({**params, **extra}, dt[cols], y3, keep, s, rondas).predict(dv[cols])))
                res.append({"fold": fold, "semilla": s, "variante": nombre, "M": g[nombre]})
            ref = prev[(prev.fold == fold) & (prev.semilla == s)].set_index("variante").M
            g["base"], g["mindata50"] = ref["base"], ref["mindata50"]
            escribir(f"[{fold} s={s}] base {g['base']:.1f} | " + " | ".join(f"{n} {v - g['base']:+.1f}" for n, v in g.items() if n != "base") + f" ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.concat([pd.DataFrame(res), prev[prev.variante.isin(["base", "mindata15", "mindata50"])]], ignore_index=True); p = r_.pivot_table(index=["fold", "semilla"], columns="variante", values="M"); filas_ = []
    for v in [c for c in p.columns if c != "base"]:
        d = (p[v] - p["base"]).groupby("fold")
        filas_.append({"variante": v, **{f"{f}_delta": d.mean()[f] for f in t028.FOLDS}, **{f"{f}_ee": d.std()[f] / np.sqrt(len(SEMILLAS_032)) for f in t028.FOLDS},
                       "pares_positivos": f"{int(((p[v] - p['base']) > 0).sum())}/{len(p)}"})
    comp = pd.DataFrame(filas_).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + r_.groupby(["variante", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas vs base:\n" + comp.to_string(index=False)); escribir("[032] terminado")
