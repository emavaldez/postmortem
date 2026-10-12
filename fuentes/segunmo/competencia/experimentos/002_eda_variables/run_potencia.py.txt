"""002 (complemento): las variantes principales con 20 semillas (las 5 propias + 15 derivadas de la primera)
para separar efectos chicos del ruido. Uso: venv/bin/python competencia/experimentos/002_eda_variables/run_potencia.py
Escribe resultados_20s.csv y comparacion_20s.csv aquí."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from config import SEMILLAS  # noqa: E402
from features import artefacto_visa, cierre_relativo, fechas_absolutas, sacar_cierre  # noqa: E402
from validacion import K_REF, evaluar  # noqa: E402

rng = np.random.RandomState(SEMILLAS[0])
SEMILLAS_20 = SEMILLAS + [int(s) for s in rng.randint(100_003, 999_983, size=15)]
VARIANTES = {
    "V0_baseline": None,
    "V2_fechas_absolutas": fechas_absolutas,
    "V4_sin_fultimo_cierre": sacar_cierre,
    "V5_V1+V2+V3": lambda d: fechas_absolutas(cierre_relativo(artefacto_visa(d))),
}
if __name__ == "__main__":
    res = []
    for nombre, f in VARIANTES.items():
        print("===", nombre, flush=True)
        res.append(evaluar(transformar=f, semillas=SEMILLAS_20, verbose=False).assign(variante=nombre))
    res = pd.concat(res, ignore_index=True)
    res.to_csv(AQUI / "resultados_20s.csv", index=False)
    col = f"gan_k{K_REF}"
    b = res[res.variante == "V0_baseline"].set_index(["fold", "semilla"])
    filas = []
    for v, g in res[res.variante != "V0_baseline"].groupby("variante"):
        g = g.set_index(["fold", "semilla"]); fila = {"variante": v}
        for fold in ["A", "B"]:
            d = (g.loc[fold, col] - b.loc[fold, col]) / 1e6
            fila[f"{fold}_delta"], fila[f"{fold}_error_std"] = d.mean(), d.std() / np.sqrt(len(d))
        fila["delta_AB"] = (fila["A_delta"] + fila["B_delta"]) / 2
        filas.append(fila)
    comp = pd.DataFrame(filas).round(2); comp.to_csv(AQUI / "comparacion_20s.csv", index=False)
    print(res.groupby(["variante", "fold"])[col].agg(["mean", "std"]).div(1e6).round(2))
    print(comp.to_string(index=False))
