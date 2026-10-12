"""008c — historia sobre ~150 variables en lugar de 50, con y sin lag2. Un cambio por escalón (pareado, 10 semillas):
  V0  pool 003/004 actual: lag1/delta1/ratio1 de 50 variables                       (referencia)
  V1  lag1/delta1/ratio1 de ~150 variables                                          (V1-V0: ¿más variables con historia?)
  V2  V1 + lag2/delta2/ratio2 de las mismas ~150 variables                          (V2-V1: ¿lag2 sobre más variables?)
Variables: las 50 de 003 + las de mayor importancia (gain) entre las ORIGINALES numéricas, ranking de `005_optuna/sel/importancias_Bh.csv`
(modelo entrenado solo con 202104: no incluye ningún mes de validación de los folds usados). Se excluyen `*fultimo_cierre` (calendario)
y las mismas variables de tiempo que excluyó 003a (FECHAS_DIAS, CIERRES, edad y antigüedad: su delta es ~constante entre meses).
Folds: B, Bh (train con lag1 real; lag2 no existe) -> mide V1-V0.  L, B2 (train desde 202105, lag2 real) -> mide V1-V0 y V2-V1.
L y B2 tienen el solapamiento de targets en 202107 descrito en 008b: informan la diferencia pareada, no el nivel.
ccajas_depositos corregida (008a). Uso (raíz del repo): venv/bin/python competencia/experimentos/008c_lags_150/run.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
A004, A005 = AQUI.parents[0] / "004_seleccion_variables", AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(A004))
import config  # noqa: E402
from config import ID_COL, MES_COL, SEMILLAS, TARGET_COL  # noqa: E402
from data import conectar  # noqa: E402
from features import CIERRES, FECHAS_DIAS  # noqa: E402
from historia import agregar_deltas, agregar_historia_n, agregar_ratios, cargar_con_lags  # noqa: E402
from pool import VARS, cargar as cargar_pool  # noqa: E402
from validacion import K_REF, evaluar  # noqa: E402

config.CORREGIR_CCAJAS = True
SEMILLAS_10 = SEMILLAS + [int(s) for s in np.random.RandomState(SEMILLAS[0]).randint(100_003, 999_983, size=15)][:5]
FOLDS = {"B": ([202103, 202104], 202106), "Bh": ([202104], 202106), "L": ([202105], 202106), "B2": ([202104, 202105], 202106)}
N_VARS = 150


def variables_150() -> list[str]:
    tipos = dict(conectar().sql("describe c01").fetchall()[i][:2] for i in range(len(conectar().sql("describe c01").fetchall())))
    numericas = {c for c, t in tipos.items() if t in ("BIGINT", "DOUBLE", "INTEGER", "HUGEINT", "FLOAT")}
    imp = pd.read_csv(A005 / "sel" / "importancias_Bh.csv", index_col=0)
    excluir = set(FECHAS_DIAS + CIERRES + ["cliente_antiguedad", "cliente_edad", ID_COL, MES_COL])   # igual que 003a
    orden = [c for c in imp.index if c in numericas and c not in excluir and not c.endswith("fultimo_cierre")]
    return list(dict.fromkeys(VARS + orden))[:max(N_VARS, len(VARS))]


V150 = variables_150()
EXTRA = [v for v in V150 if v not in VARS]


def v0(meses):
    return cargar_pool(meses, negocio=True).copy()


def v1(meses):
    d = cargar_con_lags(meses, EXTRA)                                # lag1 de las variables extra (el pool ya trae las 50)
    pool = cargar_pool(meses, negocio=True)
    d = pool.merge(d[[ID_COL, MES_COL] + [f"{v}_lag1" for v in EXTRA]], on=[ID_COL, MES_COL], how="left", validate="one_to_one")
    return agregar_ratios(agregar_deltas(d, EXTRA), EXTRA)


def v2(meses):
    return agregar_historia_n(v1(meses), V150, 2)


def a_float32(f):
    def g(meses):
        d = f(meses)
        c = d.select_dtypes("float64").columns
        d[c] = d[c].astype("float32")                                # ~1000 columnas: la mitad de memoria
        return d
    return g


VARIANTES = {"V0_50vars_lag1": v0, "V1_150vars_lag1": v1, "V2_150vars_lag1_lag2": v2}

if __name__ == "__main__":
    print(f"{len(V150)} variables con historia ({len(EXTRA)} nuevas); primeras nuevas: {EXTRA[:8]}", flush=True)
    (AQUI / "variables_150.txt").write_text("\n".join(V150) + "\n")
    res = []
    for nombre, cargar in VARIANTES.items():
        print("===", nombre, flush=True)
        res.append(evaluar(folds=FOLDS, semillas=SEMILLAS_10, cargar=a_float32(cargar), verbose=False).assign(variante=nombre))
        pd.concat(res).to_csv(AQUI / "resultados.csv", index=False)
    res = pd.concat(res, ignore_index=True); col = f"gan_k{K_REF}"
    r = res.set_index(["variante", "fold", "semilla"]); filas = []
    for a, b, folds in [("V1_150vars_lag1", "V0_50vars_lag1", list(FOLDS)), ("V2_150vars_lag1_lag2", "V1_150vars_lag1", ["L", "B2"])]:
        fila = {"comparacion": f"{a} - {b}"}
        for fold in folds:
            dif = (r.loc[(a, fold), col] - r.loc[(b, fold), col]) / 1e6
            fila[f"{fold}_delta"], fila[f"{fold}_ee"] = dif.mean(), dif.std() / np.sqrt(len(dif))
        filas.append(fila)
    comp = pd.DataFrame(filas).round(3); comp.to_csv(AQUI / "comparacion.csv", index=False)
    print((res.groupby(["variante", "fold"])[col].mean() / 1e6).round(1).unstack()); print(comp.to_string(index=False))
