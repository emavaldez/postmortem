"""003d — sumas, restas y ratios por grupos de negocio (26 columnas `n_*`, ver features.features_negocio) sobre las originales.
Folds A, B, Bh (solo originales: no dependen de la historia, así que los tres informan). 20 semillas pareadas:
  N0 = originales (referencia, se recalcula aquí)   N1 = originales + n_*
Uso (raíz del repo): venv/bin/python competencia/experimentos/003d_features_negocio/run.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from features import features_negocio  # noqa: E402
from validacion import K_REF, evaluar  # noqa: E402

FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
SEMILLAS_20 = pd.read_csv(AQUI.parents[0] / "002_eda_variables" / "resultados_20s.csv").query("variante == 'V0_baseline' and fold == 'A'").semilla.tolist()

if __name__ == "__main__":
    res = [evaluar(transformar=f, folds=FOLDS, semillas=SEMILLAS_20, verbose=False).assign(variante=n)
           for n, f in [("N0_originales", None), ("N1_con_negocio", features_negocio)]]
    res = pd.concat(res, ignore_index=True); res.to_csv(AQUI / "resultados.csv", index=False)
    col = f"gan_k{K_REF}"
    r = res.set_index(["variante", "fold", "semilla"]).sort_index()
    fila = {}
    for fold in FOLDS:
        d = (r.loc[("N1_con_negocio", fold), col] - r.loc[("N0_originales", fold), col]) / 1e6
        fila[fold], fila[f"{fold}_ee"] = d.mean(), d.std() / np.sqrt(len(d))
        fila[f"{fold}_auc"] = (r.loc[("N1_con_negocio", fold), "auc"] - r.loc[("N0_originales", fold), "auc"]).mean()
    comp = pd.DataFrame([fila]).round(3); comp.to_csv(AQUI / "comparacion.csv", index=False)
    print((res.groupby(["variante", "fold"])[col].mean() / 1e6).round(1).unstack())
    print(comp.to_string(index=False))
