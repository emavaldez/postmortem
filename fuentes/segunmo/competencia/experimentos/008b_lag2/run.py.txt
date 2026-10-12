"""008b — se suman lag2, delta2 y ratio2 de las 50 variables de historia a las columnas de 003 (lag1/delta1/ratio1).
Folds A/B/Bh NO sirven: el lag2 del train 202103/04 es todo NaN (no hay 202101/02), así que el modelo nunca lo ve.
Se usan folds con train desde 202105 (lag2 real = 202103):
  L  : train 202105          -> valid 202106
  B2 : train 202104 + 202105 -> valid 202106   (202104 con lag2 NaN: híbrido de NaN nativo)
Limitación: el target de 202105 mira 202106-07 y el de 202106 mira 202107-08 (se solapan en 202107): falta el mes de separación del
resto de los folds. Afecta por igual a las dos variantes, así que la diferencia pareada sigue siendo informativa, pero el nivel no es comparable.
Variantes: V0 pool 003 (lag1) | V1 + lag2 | V1c + lag2 con el bloque barajado dentro de cada mes (control: si V1c ~ V1 no hay señal).
Uso (raíz del repo): venv/bin/python competencia/experimentos/008b_lag2/run.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
sys.path.insert(0, str(AQUI.parents[1] / "experimentos" / "004_seleccion_variables"))
import config  # noqa: E402
from config import SEMILLAS  # noqa: E402
from historia import agregar_historia_n, barajar_historia  # noqa: E402
from pool import VARS, cargar as cargar_pool  # noqa: E402
from validacion import K_REF, evaluar  # noqa: E402

config.CORREGIR_CCAJAS = True    # 202105 entra al train: se usa la variable ya corregida (008a)
rng = np.random.RandomState(SEMILLAS[0])
SEMILLAS_20 = SEMILLAS + [int(s) for s in rng.randint(100_003, 999_983, size=15)]
FOLDS_L = {"L": ([202105], 202106), "B2": ([202104, 202105], 202106)}
COLS_LAG2 = [f"{v}_{s}2" for v in VARS for s in ("lag", "d", "r")]


def base(meses):
    return cargar_pool(meses, negocio=True).copy()       # el pool está cacheado: copiar antes de modificar


def con_lag2(meses):
    return agregar_historia_n(base(meses), VARS, 2)


VARIANTES = {
    "V0_lag1": (base, None),
    "V1_lag2": (con_lag2, None),
    "V1c_lag2_barajado": (con_lag2, lambda d: barajar_historia(d, SEMILLAS[0], cols=COLS_LAG2)),
}

if __name__ == "__main__":
    res = []
    for nombre, (cargar, f) in VARIANTES.items():
        print("===", nombre, flush=True)
        res.append(evaluar(transformar=f, folds=FOLDS_L, semillas=SEMILLAS_20, cargar=cargar, verbose=False).assign(variante=nombre))
        pd.concat(res).to_csv(AQUI / "resultados.csv", index=False)
    res = pd.concat(res, ignore_index=True)
    col = f"gan_k{K_REF}"
    r = res.set_index(["variante", "fold", "semilla"])
    filas = []
    for a, b in [("V1_lag2", "V0_lag1"), ("V1c_lag2_barajado", "V0_lag1"), ("V1_lag2", "V1c_lag2_barajado")]:
        fila = {"comparacion": f"{a} - {b}"}
        for fold in FOLDS_L:
            dif = (r.loc[(a, fold), col] - r.loc[(b, fold), col]) / 1e6
            fila[f"{fold}_delta"], fila[f"{fold}_ee"] = dif.mean(), dif.std() / np.sqrt(len(dif))
            fila[f"{fold}_auc"] = (r.loc[(a, fold), "auc"] - r.loc[(b, fold), "auc"]).mean()
        filas.append(fila)
    comp = pd.DataFrame(filas).round(4); comp.to_csv(AQUI / "comparacion.csv", index=False)
    print((res.groupby(["variante", "fold"])[col].mean() / 1e6).round(1).unstack()); print(comp.to_string(index=False))
