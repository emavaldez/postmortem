"""004b — ¿conviene mezclar el modelo de variables originales (M0) con el de historia top150 (M1)?
Mezcla = promedio de probabilidades con la misma semilla. 20 semillas pareadas, folds A, B, Bh; ganancia en k=11000.
M0: columnas originales (como el baseline). M1: top150 de cada fold (sel/importancias_<fold>.csv, solo train).
Uso (raíz del repo): venv/bin/python competencia/experimentos/004b_mezcla/run.py"""
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(AQUI.parents[1] / "src"))
from ganancia import ganancia_acumulada  # noqa: E402
from pool import cargar  # noqa: E402
from validacion import KS, K_REF, NUM_ROUNDS, PARAMS_BASE, xy  # noqa: E402

FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
SEMILLAS_20 = pd.read_csv(AQUI.parent / "002_eda_variables" / "resultados_20s.csv").query("variante == 'V0_baseline' and fold == 'A'").semilla.tolist()
es_hist = lambda c: "_lag1" in c or c.endswith(("_d1", "_r1")) or c.startswith("r_")  # noqa: E731


def ajustar(Xt, yt, Xv, s):
    return lgb.train({**PARAMS_BASE, "seed": s}, lgb.Dataset(Xt, label=yt), num_boost_round=NUM_ROUNDS).predict(Xv)


if __name__ == "__main__":
    filas = []
    for fold, (mt, mv) in FOLDS.items():
        (Xt, yt), (Xv, yv) = xy(cargar(mt)), xy(cargar([mv]))
        orig = [c for c in Xt.columns if not es_hist(c)]
        imp = pd.read_csv(AQUI.parent / "004_seleccion_variables" / "sel" / f"importancias_{fold}.csv", index_col=0)
        top = [c for c in imp.index if not c.startswith("canario_")][:150]
        print(f"fold {fold}: M0 {len(orig)} cols | M1 {len(top)} cols", flush=True)
        for s in SEMILLAS_20:
            p0, p1 = ajustar(Xt[orig], yt, Xv[orig], s), ajustar(Xt[top], yt, Xv[top], s)
            for nombre, p in [("M0_original", p0), ("M1_historia", p1), ("MIX_promedio", (p0 + p1) / 2)]:
                acum = ganancia_acumulada(yv.values, p)
                filas.append({"fold": fold, "semilla": s, "variante": nombre, "auc": roc_auc_score(yv, p),
                              **{f"gan_k{k}": acum[k - 1] for k in KS}})
    res = pd.DataFrame(filas); res.to_csv(AQUI / "resultados.csv", index=False)
    col = f"gan_k{K_REF}"
    r = res.set_index(["variante", "fold", "semilla"]).sort_index()
    out = []
    for a, b in [("M1_historia", "M0_original"), ("MIX_promedio", "M0_original"), ("MIX_promedio", "M1_historia")]:
        fila = {"comparación": f"{a} - {b}"}
        for fold in FOLDS:
            d = (r.loc[(a, fold), col] - r.loc[(b, fold), col]) / 1e6
            fila[f"{fold}"], fila[f"{fold}_ee"] = d.mean(), d.std() / np.sqrt(len(d))
        out.append(fila)
    comp = pd.DataFrame(out).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    print((res.groupby(["variante", "fold"])[col].mean() / 1e6).round(1).unstack())
    print((res.groupby(["variante", "fold"]).auc.mean()).round(4).unstack())
    print(comp.to_string(index=False))
