"""003c — features del mes actual: ratios entre variables (C1), percentiles dentro del mes (C2) y ambas (C3).
Folds A y B (el train no necesita historia → ambos informan). 20 semillas pareadas; baseline de 002/resultados_20s.csv.
Uso (raíz del repo): venv/bin/python competencia/experimentos/003c_features_mes/run.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from features import rangos_en_el_mes, ratios_entre_variables  # noqa: E402
from validacion import K_REF, evaluar  # noqa: E402

VARS = (AQUI.parents[0] / "003a_lag1_delta" / "variables_historia.txt").read_text().split()
SEMILLAS_20 = pd.read_csv(AQUI.parents[0] / "002_eda_variables" / "resultados_20s.csv").query("variante == 'V0_baseline' and fold == 'A'").semilla.tolist()
VARIANTES = {
    "C1_ratios": ratios_entre_variables,
    "C2_rangos_mes": lambda d: rangos_en_el_mes(d, VARS),
    "C3_ratios+rangos": lambda d: rangos_en_el_mes(ratios_entre_variables(d), VARS),
}

if __name__ == "__main__":
    base = pd.read_csv(AQUI.parents[0] / "002_eda_variables" / "resultados_20s.csv").query("variante == 'V0_baseline'")
    res = [base]
    for nombre, f in VARIANTES.items():
        print("===", nombre, flush=True)
        res.append(evaluar(transformar=f, semillas=SEMILLAS_20, verbose=False).assign(variante=nombre))
    res = pd.concat(res, ignore_index=True)
    res.to_csv(AQUI / "resultados.csv", index=False)
    col = f"gan_k{K_REF}"
    b = res[res.variante == "V0_baseline"].set_index(["fold", "semilla"]).sort_index()
    filas = []
    for v, g in res[res.variante != "V0_baseline"].groupby("variante"):
        g = g.set_index(["fold", "semilla"]).sort_index(); fila = {"variante": v}
        for fold in ["A", "B"]:
            dif = (g.loc[fold, col] - b.loc[fold, col]) / 1e6
            fila[f"{fold}_delta"], fila[f"{fold}_ee"] = dif.mean(), dif.std() / np.sqrt(len(dif))
            fila[f"{fold}_auc_delta"] = (g.loc[fold, "auc"] - b.loc[fold, "auc"]).mean()
        fila["delta_AB"] = (fila["A_delta"] + fila["B_delta"]) / 2
        filas.append(fila)
    comp = pd.DataFrame(filas).round(3); comp.to_csv(AQUI / "comparacion.csv", index=False)
    print((res.groupby(["variante", "fold"])[col].mean() / 1e6).round(1).unstack())
    print(comp.to_string(index=False))
