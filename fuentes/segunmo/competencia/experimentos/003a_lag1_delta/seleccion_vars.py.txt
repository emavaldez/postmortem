"""003a — paso 1: elegir las ~50 variables a las que se les arma historia.
Criterio: importancia (gain, media de 5 semillas) de un LightGBM baseline entrenado SOLO con 202103+202104
(los meses de train del fold B; no se mira ningún mes de validación). Se excluyen las variables de tiempo
transcurrido y el cierre de tarjeta: su delta es una constante de calendario (ver 002).
Uso (raíz del repo): venv/bin/python competencia/experimentos/003a_lag1_delta/seleccion_vars.py"""
import sys
from pathlib import Path

import lightgbm as lgb
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from config import SEMILLAS  # noqa: E402
from data import cargar_meses  # noqa: E402
from features import CIERRES, FECHAS_DIAS  # noqa: E402
from validacion import NUM_ROUNDS, PARAMS_BASE, xy  # noqa: E402

N_VARS = 50
EXCLUIR = set(FECHAS_DIAS + CIERRES + ["cliente_antiguedad", "cliente_edad"])

if __name__ == "__main__":
    X, y = xy(cargar_meses([202103, 202104]))
    X = X.select_dtypes("number")
    imp = pd.Series(0.0, index=X.columns)
    for s in SEMILLAS:
        m = lgb.train({**PARAMS_BASE, "seed": s}, lgb.Dataset(X, label=y), num_boost_round=NUM_ROUNDS)
        imp += pd.Series(m.feature_importance("gain"), index=X.columns) / len(SEMILLAS)
    imp = (imp / imp.sum()).sort_values(ascending=False)
    elegidas = [c for c in imp.index if c not in EXCLUIR][:N_VARS]
    imp.rename("gain_rel").to_frame().assign(elegida=lambda d: d.index.isin(elegidas)).to_csv(AQUI / "importancias_train.csv")
    (AQUI / "variables_historia.txt").write_text("\n".join(elegidas) + "\n")
    print(f"{len(elegidas)} variables; gain acumulado de las elegidas: {imp[elegidas].sum():.1%}")
    print(elegidas)
