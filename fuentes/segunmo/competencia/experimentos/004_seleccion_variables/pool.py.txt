"""Pool de variables candidatas de 004: originales + historia 003b (lag1, delta1, ratio1 de 50 vars) + 17 ratios 003c."""
import sys
from functools import lru_cache
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from data import cargar_meses  # noqa: E402,F401
from features import features_negocio, ratios_entre_variables  # noqa: E402
from historia import agregar_deltas, agregar_ratios, cargar_con_lags  # noqa: E402

VARS = (AQUI.parents[0] / "003a_lag1_delta" / "variables_historia.txt").read_text().split()


@lru_cache(maxsize=8)
def cargar_pool(meses: tuple, solo_con_target: bool = True, negocio: bool = False):
    """Se cachea por meses: evaluar() y la selección piden los mismos meses varias veces. No modificar el resultado.
    negocio=True suma las 26 columnas `n_*` de 003d (el pool pasa de 319 a 345 columnas)."""
    d = cargar_con_lags(list(meses), VARS, solo_con_target=solo_con_target)
    d = ratios_entre_variables(agregar_ratios(agregar_deltas(d, VARS), VARS))
    return features_negocio(d) if negocio else d


def cargar(meses, **kw):
    return cargar_pool(tuple(meses), **kw)
