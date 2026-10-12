"""008a — `ccajas_depositos` = NA solo en 202105 (viene rota: todos 0). Un solo cambio, 20 semillas pareadas.
Set M0 (152 originales + 26 `n_*` de negocio). Fold A: delta = 0 exacto por construcción (el train 202103 no tiene NaN en la columna y LightGBM trata
los NaN como 0 al predecir si no vio NaN al entrenar). B y Bh no tocan 202105. La corrección solo puede importar cuando 202105 está en el
train: folds L (train 202105 -> valid 202106) y B2 (202104+05 -> 202106), con el solapamiento de targets descrito en 008b.
Uso (raíz del repo): venv/bin/python competencia/experimentos/008a_ccajas_na/run.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
import config  # noqa: E402
from config import SEMILLAS  # noqa: E402
from data import cargar_meses  # noqa: E402
from features import features_negocio  # noqa: E402
from validacion import FOLDS, K_REF, evaluar

FOLDS_008A = {"A": FOLDS["A"], "L": ([202105], 202106), "B2": ([202104, 202105], 202106)}  # noqa: E402

rng = np.random.RandomState(SEMILLAS[0])
SEMILLAS_20 = SEMILLAS + [int(s) for s in rng.randint(100_003, 999_983, size=15)]   # igual que 002/003


def cargar(corregir):
    def f(meses):
        config.CORREGIR_CCAJAS = corregir          # conectar() lee el flag cada vez que se llama
        return features_negocio(cargar_meses(meses))
    return f


if __name__ == "__main__":
    res = []
    for nombre, corregir in {"V0_sin_corregir": False, "V1_ccajas_NA_202105": True}.items():
        res.append(evaluar(folds=FOLDS_008A, semillas=SEMILLAS_20, cargar=cargar(corregir), verbose=False).assign(variante=nombre))
    res = pd.concat(res, ignore_index=True); res.to_csv(AQUI / "resultados.csv", index=False)
    col = f"gan_k{K_REF}"
    filas = []
    for fold, g in res.groupby("fold"):
        a = g.pivot(index="semilla", columns="variante", values=col) / 1e6
        dif = a["V1_ccajas_NA_202105"] - a["V0_sin_corregir"]
        auc = g.pivot(index="semilla", columns="variante", values="auc")
        filas.append({"fold": fold, "base_M": a["V0_sin_corregir"].mean(), "fix_M": a["V1_ccajas_NA_202105"].mean(),
                      "delta_M": dif.mean(), "ee": dif.std() / np.sqrt(len(dif)),
                      "auc_delta": (auc["V1_ccajas_NA_202105"] - auc["V0_sin_corregir"]).mean()})
    comp = pd.DataFrame(filas).round(4)
    comp.to_csv(AQUI / "comparacion.csv", index=False); print(comp.to_string(index=False))
