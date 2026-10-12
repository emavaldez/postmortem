"""003a — lag1 + delta1 de 50 variables (híbrido acordado, 20 semillas pareadas).

Folds:  A  (train 202103 -> valid 202105)   : train SIN historia (todo NaN) -> se espera delta ~ 0, sirve de control
        B  (train 202103+04 -> valid 202106): NaN nativo en 202103 (riesgo de proxy de calendario)
        Bh (train 202104 -> valid 202106)   : solo filas con historia, sin NaN artificiales
Variantes: V0 baseline (A/B de 002/resultados_20s.csv; Bh se recalcula sacando las columnas históricas),
           H1 lag1+delta1, H1c control (columnas históricas barajadas dentro de cada mes).
Uso (raíz del repo): venv/bin/python competencia/experimentos/003a_lag1_delta/run.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from config import MES_COL, SEMILLAS  # noqa: E402
from historia import agregar_deltas, barajar_historia, cargar_con_lags, quitar_historia  # noqa: E402
from validacion import FOLDS, K_REF, evaluar  # noqa: E402

VARS = (AQUI / "variables_historia.txt").read_text().split()
FOLDS_003 = {**FOLDS, "Bh": ([202104], 202106)}
rng = np.random.RandomState(SEMILLAS[0])
SEMILLAS_20 = SEMILLAS + [int(s) for s in rng.randint(100_003, 999_983, size=15)]   # igual que 002


def cargar(meses):
    return agregar_deltas(cargar_con_lags(meses, VARS), VARS)


VARIANTES = {
    "V0_baseline": quitar_historia,
    "H1_lag1_delta1": None,
    "H1c_control_barajado": lambda d: barajar_historia(d, SEMILLAS[0]),
}

if __name__ == "__main__":
    d = cargar([202104, 202106])
    print("% con lag1 por mes:", (d.groupby(MES_COL)[f"{VARS[0]}_lag1"].apply(lambda s: s.notna().mean())).round(3).to_dict())
    res = []
    for nombre, f in VARIANTES.items():
        print("===", nombre, flush=True)
        folds = {k: v for k, v in FOLDS_003.items() if not (nombre == "V0_baseline" and k != "Bh")}  # A/B baseline: de 002
        res.append(evaluar(transformar=f, folds=folds, semillas=SEMILLAS_20, cargar=cargar, verbose=False).assign(variante=nombre))
    base_ab = pd.read_csv(AQUI.parents[0] / "002_eda_variables" / "resultados_20s.csv").query("variante == 'V0_baseline'")
    res = pd.concat([base_ab] + res, ignore_index=True)
    res.to_csv(AQUI / "resultados.csv", index=False)

    col = f"gan_k{K_REF}"
    b = res[res.variante == "V0_baseline"].set_index(["fold", "semilla"])
    filas = []
    for v, g in res[res.variante != "V0_baseline"].groupby("variante"):
        g = g.set_index(["fold", "semilla"]); fila = {"variante": v}
        for fold in ["A", "B", "Bh"]:
            dif = (g.loc[fold, col] - b.loc[fold, col]) / 1e6        # pareada por semilla
            fila[f"{fold}_delta"], fila[f"{fold}_ee"] = dif.mean(), dif.std() / np.sqrt(len(dif))
            fila[f"{fold}_auc_delta"] = (g.loc[fold, "auc"] - b.loc[fold, "auc"]).mean()
        filas.append(fila)
    comp = pd.DataFrame(filas).round(3); comp.to_csv(AQUI / "comparacion.csv", index=False)
    print((res.groupby(["variante", "fold"])[col].mean() / 1e6).round(1).unstack())
    print(comp.to_string(index=False))
