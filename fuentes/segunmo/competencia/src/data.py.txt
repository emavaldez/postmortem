"""Carga del dataset con DuckDB (lazy: no trae todo el CSV a memoria)."""
import duckdb
import pandas as pd

import config
from config import CSV, MES_COL, PARQUET, TARGET_COL


def conectar() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    fuente = (f"read_parquet('{PARQUET.as_posix()}')" if PARQUET.exists()
              else f"read_csv_auto('{CSV.as_posix()}')")   # parquet si existe, si no el CSV
    # `* replace` deja todas las columnas igual salvo ccajas_depositos en 202105 (rota: todo 0) -> NA. Ver config.CORREGIR_CCAJAS.
    corregir = (f"replace (case when {MES_COL} = 202105 then null else ccajas_depositos end as ccajas_depositos)"
                if config.CORREGIR_CCAJAS else "")
    con.sql(f"create view c01 as select * {corregir} from {fuente}")
    return con


def cargar_meses(meses: list[int], solo_con_target: bool = True) -> pd.DataFrame:
    """DataFrame con los meses pedidos. Para entrenar/validar usar solo_con_target=True."""
    filtro_t = f"and {TARGET_COL} is not null" if solo_con_target else ""
    lista = ",".join(str(m) for m in meses)
    # ORDER BY explícito: sin él DuckDB devuelve las filas en un orden que cambia entre corridas (lecturas paralelas) y, como el
    # undersampling sortea por POSICIÓN, cada corrida entrenaba con otros clientes (ver REPRODUCIR.md §0).
    return conectar().sql(f"select * from c01 where {MES_COL} in ({lista}) {filtro_t} order by {MES_COL}, numero_de_cliente").df()
