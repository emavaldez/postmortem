"""Features históricas: valor del mismo cliente en meses anteriores (solo pasado, nunca futuro).

El lag se arma con un join explícito por (cliente, mes anterior) y no con `lag()` sobre filas: si un cliente no
estaba el mes anterior (cliente nuevo) el lag es NaN, en lugar de agarrar un mes más viejo sin avisar.

Ojo con el borde: 202103 no tiene mes anterior, así que todos sus lags son NaN (ver PLAN.md / exp 003).
"""
import numpy as np
import pandas as pd

from config import ID_COL, MES_COL, TARGET_COL
from data import conectar


def mes_anterior_sql(col: str = MES_COL, n: int = 1) -> str:
    """Expresión SQL del mes n meses atrás (formato AAAAMM, cruza el año)."""
    return f"(case when ({col} % 100) - {n} >= 1 then {col} - {n} else {col} - 88 - {n} end)"


def cargar_con_lags(meses: list[int], variables: list[str], n: int = 1, solo_con_target: bool = True) -> pd.DataFrame:
    """Meses pedidos + `{v}_lag{n}` para cada variable (valor del cliente n meses antes, NaN si no estaba)."""
    lista = ",".join(str(m) for m in meses)
    lags = ", ".join(f'p."{v}" as "{v}_lag{n}"' for v in variables)
    filtro_t = f"and a.{TARGET_COL} is not null" if solo_con_target else ""
    sql = (f"select a.*, {lags} from c01 a left join c01 p "
           f"on a.{ID_COL} = p.{ID_COL} and p.{MES_COL} = {mes_anterior_sql('a.' + MES_COL, n)} "
           f"where a.{MES_COL} in ({lista}) {filtro_t} order by a.{MES_COL}, a.{ID_COL}")   # orden determinista (ver data.py)
    return conectar().sql(sql).df()


def agregar_historia_n(df: pd.DataFrame, variables: list[str], n: int) -> pd.DataFrame:
    """A un df ya armado le suma `{v}_lag{n}`, `{v}_d{n}` y `{v}_r{n}` (join por cliente y mes de hace n meses; NaN si no estaba).
    Sirve para sumar el lag 2 sin rehacer el pool; el orden de filas de `df` se conserva."""
    lista = ",".join(str(m) for m in sorted(df[MES_COL].unique()))
    lags = ", ".join(f'p."{v}" as "{v}_lag{n}"' for v in variables)
    sql = (f"select a.{ID_COL}, a.{MES_COL}, {lags} from c01 a left join c01 p "
           f"on a.{ID_COL} = p.{ID_COL} and p.{MES_COL} = {mes_anterior_sql('a.' + MES_COL, n)} where a.{MES_COL} in ({lista})")
    out = df.merge(conectar().sql(sql).df(), on=[ID_COL, MES_COL], how="left", validate="one_to_one")
    return agregar_ratios(agregar_deltas(out, variables, n), variables, n)


def agregar_deltas(df: pd.DataFrame, variables: list[str], n: int = 1) -> pd.DataFrame:
    """`{v}_d{n}` = valor actual - valor de hace n meses (NaN si no hay lag)."""
    df = df.copy()
    for v in variables:
        df[f"{v}_d{n}"] = df[v] - df[f"{v}_lag{n}"]
    return df


def agregar_ratios(df: pd.DataFrame, variables: list[str], n: int = 1) -> pd.DataFrame:
    """`{v}_r{n}` = cambio relativo vs hace n meses = v/lag - 1 (NaN si no hay lag o el lag es 0).
    Distinto del delta: normaliza por el tamaño del cliente (un cambio de $10k no es lo mismo con saldo 20k que 2M)."""
    df = df.copy()
    for v in variables:
        lag = df[f"{v}_lag{n}"].replace(0, np.nan)
        df[f"{v}_r{n}"] = df[v] / lag - 1
    return df


def quitar_historia(df: pd.DataFrame) -> pd.DataFrame:
    """Saca todas las columnas históricas (deja las variables originales): sirve de baseline pareado."""
    return df.drop(columns=[c for c in df.columns if "_lag" in c or c.endswith(("_d1", "_d2", "_r1", "_r2"))])


def barajar_historia(df: pd.DataFrame, seed: int, cols: list[str] | None = None) -> pd.DataFrame:
    """Control: permuta las filas de las columnas históricas DENTRO de cada mes (bloque completo, a la vez).
    Mantiene las distribuciones y la proporción de NaN por mes pero rompe el vínculo con el cliente: si el modelo
    mejora con esto, la ganancia viene del patrón de NaN/calendario y no de la información de la historia."""
    df = df.copy()
    cols = cols or [c for c in df.columns if "_lag" in c or c.endswith(("_d1", "_d2", "_r1", "_r2"))]
    rng = np.random.RandomState(seed)
    for _, idx in df.groupby(MES_COL).indices.items():
        perm = rng.permutation(len(idx))
        df.iloc[idx, [df.columns.get_loc(c) for c in cols]] = df[cols].iloc[idx[perm]].values
    return df


def lags_crudos(df: pd.DataFrame, variables: list[str], n: int = 1) -> pd.DataFrame:
    """Solo las columnas `{v}_lag{n}` (valor de hace n meses; NaN si el cliente no estaba), alineadas con las filas de `df`.
    A diferencia de `agregar_historia_n` no se las pega a `df`: sirve cuando `df` ya trae algunas de esas columnas."""
    lista = ",".join(str(m) for m in sorted(df[MES_COL].unique()))
    lags = ", ".join(f'p."{v}" as "{v}_lag{n}"' for v in variables)
    sql = (f"select a.{ID_COL}, a.{MES_COL}, {lags} from c01 a left join c01 p "
           f"on a.{ID_COL} = p.{ID_COL} and p.{MES_COL} = {mes_anterior_sql('a.' + MES_COL, n)} where a.{MES_COL} in ({lista})")
    out = df[[ID_COL, MES_COL]].merge(conectar().sql(sql).df(), on=[ID_COL, MES_COL], how="left", validate="one_to_one")
    out.index = df.index
    return out.drop(columns=[ID_COL, MES_COL])


def lag_derivadas(df: pd.DataFrame, columnas: list[str], n: int = 1) -> pd.DataFrame:
    """`{c}_lag{n}`, `{c}_d{n}` y `{c}_r{n}` para features DERIVADAS (n_*, r_*): el valor de la feature calculada con los datos del mes
    de hace n meses (la feature se calcula mes por mes con features_negocio/ratios_entre_variables y después se desplaza).
    NaN si ese mes no existe o el cliente no estaba. Usa solo meses anteriores."""
    from data import cargar_meses
    from features import features_negocio, ratios_entre_variables
    meses = sorted(df[MES_COL].unique())
    previos = sorted({m_ant for m in meses if (m_ant := int(m - 88 - n if (m % 100) - n < 1 else m - n)) >= 202103})
    if not previos:
        return pd.DataFrame({f"{c}_{s}{n}": np.nan for c in columnas for s in ("lag", "d", "r")}, index=df.index)
    raw = cargar_meses(previos, solo_con_target=False)
    der = features_negocio(ratios_entre_variables(raw))[[ID_COL, MES_COL] + columnas]
    # mes siguiente al del dato, para que el join con df sea (cliente, mes de df)
    der[MES_COL] = np.where(der[MES_COL] % 100 + n <= 12, der[MES_COL] + n, der[MES_COL] + 88 + n)
    der = der.rename(columns={c: f"{c}_lag{n}" for c in columnas})
    out = df[[ID_COL, MES_COL]].merge(der, on=[ID_COL, MES_COL], how="left", validate="one_to_one")
    out.index = df.index
    res = out.drop(columns=[ID_COL, MES_COL])
    for c in columnas:
        lag = res[f"{c}_lag{n}"]
        res[f"{c}_d{n}"] = df[c] - lag
        res[f"{c}_r{n}"] = df[c] / lag.replace(0, np.nan) - 1
    return res
