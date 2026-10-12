"""004 paso 2 — ¿cuánta ganancia cuesta (o no) reducir el pool de 319 columnas? 20 semillas pareadas, folds A, B, Bh.
Para cada fold la lista sale de importancias_<fold>.csv (calculadas SOLO con el train de ese fold, ver seleccion.py):
  P_full     las 319 columnas (referencia)
  P_canario  variables que superan al percentil 90 de los canaritos (regla estricta)
  P_top80 / P_top150  las N de mayor importancia en train (reglas más permisivas)
Mide ganancia (k=11000), AUC y tiempo medio de entrenamiento por semilla. Baseline V0 (originales) de 002/003a.
Uso (raíz del repo): venv/bin/python competencia/experimentos/004_seleccion_variables/run.py"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(AQUI.parents[1] / "src"))
from pool import cargar  # noqa: E402
from seleccion import elegir  # noqa: E402
from validacion import FOLDS, K_REF, evaluar  # noqa: E402

FOLDS_004 = {**FOLDS, "Bh": ([202104], 202106)}
SEMILLAS_20 = pd.read_csv(AQUI.parents[0] / "002_eda_variables" / "resultados_20s.csv").query("variante == 'V0_baseline' and fold == 'A'").semilla.tolist()


def listas(fold: str, columnas: list[str]) -> dict:
    imp = pd.read_csv(AQUI / "sel" / f"importancias_{fold}.csv", index_col=0)
    orden = [c for c in imp.index if not c.startswith("canario_")]
    return {"P_full": columnas, "P_canario": elegir(imp, "p90"), "P_top80": orden[:80], "P_top150": orden[:150]}


if __name__ == "__main__":
    res = []
    for fold, (meses_train, mes_valid) in FOLDS_004.items():
        d = cargar(meses_train)
        cols = [c for c in d.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria")]
        for nombre, ok in listas(fold, cols).items():
            quitar = tuple(c for c in cols if c not in set(ok))
            t0 = time.time()
            r = evaluar(folds={fold: (meses_train, mes_valid)}, semillas=SEMILLAS_20, cargar=cargar, quitar=quitar, verbose=False)
            r = r.assign(variante=nombre, n_cols=len(ok), seg_por_modelo=(time.time() - t0) / len(SEMILLAS_20))
            res.append(r); print(f"fold {fold} {nombre}: {len(ok)} cols | {r.seg_por_modelo.iloc[0]:.1f}s/modelo | "
                                 f"gan k={K_REF}: {r[f'gan_k{K_REF}'].mean()/1e6:.1f}M", flush=True)
    res = pd.concat(res, ignore_index=True); res.to_csv(AQUI / "resultados.csv", index=False)

    col = f"gan_k{K_REF}"
    r = res.set_index(["variante", "fold", "semilla"]).sort_index()
    filas = []
    for v in ["P_canario", "P_top80", "P_top150"]:
        fila = {"variante": v}
        for fold in FOLDS_004:
            dif = (r.loc[(v, fold), col] - r.loc[("P_full", fold), col]) / 1e6        # selección vs pool completo
            fila[f"{fold}_vs_full"], fila[f"{fold}_ee"] = dif.mean(), dif.std() / np.sqrt(len(dif))
        filas.append(fila)
    comp = pd.DataFrame(filas).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    print((res.groupby(["variante", "fold"])[col].mean() / 1e6).round(1).unstack())
    print(res.groupby(["variante", "fold"]).seg_por_modelo.first().round(1).unstack())
    print(comp.to_string(index=False))
