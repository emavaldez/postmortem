"""003b — a lag1+delta1 (003a) se le suman los cambios relativos v/lag1-1 de las mismas 50 variables (+50 cols).
Folds B y Bh (A no tiene historia en train: no informa). 20 semillas pareadas; baseline y H1 salen de 003a/resultados.csv.
Uso (raíz del repo): venv/bin/python competencia/experimentos/003b_ratios/run.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
A003 = AQUI.parents[0] / "003a_lag1_delta"
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from historia import agregar_deltas, agregar_ratios, cargar_con_lags  # noqa: E402
from validacion import FOLDS, K_REF, evaluar  # noqa: E402

VARS = (A003 / "variables_historia.txt").read_text().split()
FOLDS_B = {"B": FOLDS["B"], "Bh": ([202104], 202106)}
SEMILLAS_20 = pd.read_csv(A003 / "resultados.csv").query("variante == 'V0_baseline' and fold == 'B'").semilla.tolist()


def cargar(meses):
    return agregar_ratios(agregar_deltas(cargar_con_lags(meses, VARS), VARS), VARS)


if __name__ == "__main__":
    nueva = evaluar(folds=FOLDS_B, semillas=SEMILLAS_20, cargar=cargar, verbose=False).assign(variante="H2_lag1_delta1_ratio1")
    previo = pd.read_csv(A003 / "resultados.csv").query("variante in ['V0_baseline', 'H1_lag1_delta1']")
    res = pd.concat([previo, nueva], ignore_index=True)
    res.to_csv(AQUI / "resultados.csv", index=False)
    col = f"gan_k{K_REF}"
    r = res.set_index(["variante", "fold", "semilla"])
    filas = []
    for v in ["H1_lag1_delta1", "H2_lag1_delta1_ratio1"]:
        fila = {"variante": v}
        for fold in ["B", "Bh"]:
            dif = (r.loc[(v, fold), col] - r.loc[("V0_baseline", fold), col]) / 1e6
            fila[f"{fold}_vs_base"], fila[f"{fold}_ee"] = dif.mean(), dif.std() / np.sqrt(len(dif))
        filas.append(fila)
    # H2 contra H1 (efecto marginal de los ratios), pareado
    fila = {"variante": "H2 - H1"}
    for fold in ["B", "Bh"]:
        dif = (r.loc[("H2_lag1_delta1_ratio1", fold), col] - r.loc[("H1_lag1_delta1", fold), col]) / 1e6
        fila[f"{fold}_vs_base"], fila[f"{fold}_ee"] = dif.mean(), dif.std() / np.sqrt(len(dif))
    filas.append(fila)
    comp = pd.DataFrame(filas).round(3); comp.to_csv(AQUI / "comparacion.csv", index=False)
    print((res.groupby(["variante", "fold"])[col].mean() / 1e6).round(1).unstack())
    print(comp.to_string(index=False))
