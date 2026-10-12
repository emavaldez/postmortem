"""007 — undersampling de los negativos en el TRAIN (adelantado al lugar 1 porque decide el presupuesto de Optuna).
Se conservan todos los BAJA+2 y una fracción r del resto (CONTINUA + BAJA+1), sorteada con la semilla del modelo.
La validación NO se toca (mes completo). Se corta por top-k, así que la calibración de las probabilidades no importa.
Sets: M0 (152 columnas originales) y M1 (top150 con historia del fold). r ∈ {1.0 referencia, 0.5, 0.2, 0.1, 0.05}.
20 semillas pareadas, folds A, B, Bh; ganancia en k=11000. Params fijos del baseline (min_data_in_leaf=200 no se reescala).
Uso (raíz del repo): venv/bin/python competencia/experimentos/007_undersampling/run.py"""
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables"))
from ganancia import ganancia_acumulada  # noqa: E402
from pool import cargar  # noqa: E402
from validacion import KS, K_REF, NUM_ROUNDS, PARAMS_BASE, xy  # noqa: E402

FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
RATIOS = [1.0, 0.5, 0.2, 0.1, 0.05]
SEMILLAS_20 = pd.read_csv(AQUI.parent / "002_eda_variables" / "resultados_20s.csv").query("variante == 'V0_baseline' and fold == 'A'").semilla.tolist()
es_hist = lambda c: "_lag1" in c or c.endswith(("_d1", "_r1")) or c.startswith("r_")  # noqa: E731

if __name__ == "__main__":
    filas = []
    for fold, (mt, mv) in FOLDS.items():
        (Xt, yt), (Xv, yv) = xy(cargar(mt)), xy(cargar([mv]))
        imp = pd.read_csv(AQUI.parent / "004_seleccion_variables" / "sel" / f"importancias_{fold}.csv", index_col=0)
        sets = {"M0": [c for c in Xt.columns if not es_hist(c)], "M1": [c for c in imp.index if not c.startswith("canario_")][:150]}
        for nombre, cols in sets.items():
            for r in RATIOS:
                t0 = time.time()
                for s in SEMILLAS_20:
                    rng = np.random.RandomState(s)
                    keep = (yt.values == 1) | (rng.rand(len(yt)) < r)          # todos los positivos + fracción r del resto
                    m = lgb.train({**PARAMS_BASE, "seed": s}, lgb.Dataset(Xt.loc[keep, cols], label=yt[keep]), num_boost_round=NUM_ROUNDS)
                    p = m.predict(Xv[cols]); acum = ganancia_acumulada(yv.values, p)
                    filas.append({"fold": fold, "set": nombre, "r": r, "semilla": s, "n_train": int(keep.sum()), "auc": roc_auc_score(yv, p),
                                  **{f"gan_k{k}": acum[k - 1] for k in KS}})
                seg = (time.time() - t0) / len(SEMILLAS_20)
                g = pd.DataFrame(filas).query("fold == @fold and `set` == @nombre and r == @r")[f"gan_k{K_REF}"].mean() / 1e6
                print(f"fold {fold} {nombre} r={r}: n_train {filas[-1]['n_train']} | {seg:.1f}s/modelo | gan {g:.1f}M", flush=True)
    res = pd.DataFrame(filas); res.to_csv(AQUI / "resultados.csv", index=False)

    col = f"gan_k{K_REF}"
    r_ = res.set_index(["set", "r", "fold", "semilla"]).sort_index()
    out = []
    for nombre in ["M0", "M1"]:
        for r in RATIOS[1:]:
            fila = {"set": nombre, "r": r}
            for fold in FOLDS:
                d = (r_.loc[(nombre, r, fold), col] - r_.loc[(nombre, 1.0, fold), col]) / 1e6      # pareado vs sin undersampling
                fila[fold], fila[f"{fold}_ee"] = d.mean(), d.std() / np.sqrt(len(d))
            out.append(fila)
    comp = pd.DataFrame(out).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    print(comp.to_string(index=False))
