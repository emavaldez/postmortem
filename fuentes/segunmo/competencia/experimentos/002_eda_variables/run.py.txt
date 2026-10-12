"""002 — ¿Mejoran la ganancia las transformaciones sugeridas por el EDA? (una por vez, contra el baseline 001)

Uso (raíz del repo):  venv/bin/python competencia/experimentos/002_eda_variables/run.py
Compara contra experimentos/001_baseline_lgbm/validacion_folds.csv (mismas semillas y folds, pareado).
Escribe resultados.csv y comparacion.csv aquí."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from features import artefacto_visa, cierre_relativo, fechas_absolutas, sacar_cierre  # noqa: E402
from validacion import K_REF, evaluar  # noqa: E402

VARIANTES = {
    "V1_cierre_relativo": cierre_relativo,
    "V2_fechas_absolutas": fechas_absolutas,
    "V3_artefacto_visa": artefacto_visa,
    "V4_sin_fultimo_cierre": sacar_cierre,
    "V5_V1+V2+V3": lambda d: fechas_absolutas(cierre_relativo(artefacto_visa(d))),
}

if __name__ == "__main__":
    base = pd.read_csv(AQUI.parents[0] / "001_baseline_lgbm" / "validacion_folds.csv").assign(variante="V0_baseline")
    todos = [base]
    for nombre, f in VARIANTES.items():
        print(f"\n=== {nombre} ===", flush=True)
        todos.append(evaluar(transformar=f, verbose=False).assign(variante=nombre))
    res = pd.concat(todos, ignore_index=True)
    res.to_csv(AQUI / "resultados.csv", index=False)

    col = f"gan_k{K_REF}"
    b = base.set_index(["fold", "semilla"])
    filas = []
    for v, g in res[res.variante != "V0_baseline"].groupby("variante"):
        g = g.set_index(["fold", "semilla"])
        fila = {"variante": v}
        for fold in ["A", "B"]:
            d = (g.loc[fold, col] - b.loc[fold, col]) / 1e6                  # diferencia pareada por semilla
            fila[f"{fold}_gan"] = g.loc[fold, col].mean() / 1e6
            fila[f"{fold}_delta"], fila[f"{fold}_sd_delta"] = d.mean(), d.std()
            fila[f"{fold}_auc_delta"] = (g.loc[fold, "auc"] - b.loc[fold, "auc"]).mean()
        fila["delta_AB"] = (fila["A_delta"] + fila["B_delta"]) / 2
        filas.append(fila)
    comp = pd.DataFrame(filas).round(3)
    comp.to_csv(AQUI / "comparacion.csv", index=False)
    print(f"\nBaseline k={K_REF}: A {base[base.fold=='A'][col].mean()/1e6:.1f}M | B {base[base.fold=='B'][col].mean()/1e6:.1f}M")
    print("Diferencia vs baseline (millones, pareada por semilla; sd = desvío de la diferencia):")
    print(comp.to_string(index=False))
