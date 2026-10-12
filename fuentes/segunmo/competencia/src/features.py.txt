"""Transformaciones de variables del EDA 002 (ver experimentos/002_eda_variables/README.md).
Todas reciben un DataFrame con varios meses (columna foto_mes) y devuelven una copia; son fila a fila o usan
solo información del propio mes, así que no filtran futuro.
"""
import numpy as np
import pandas as pd

CIERRES = ["Master_fultimo_cierre", "Visa_fultimo_cierre"]
# variables que miden "días desde/hasta un evento" y avanzan 30/31 por mes aunque el evento sea el mismo
FECHAS_DIAS = ["Master_fechaalta", "Visa_fechaalta", "Master_Fvencimiento", "Visa_Fvencimiento",
               "Master_Finiciomora", "Visa_Finiciomora"]
SENTINELA = -100_000   # Fvencimiento ≈ -2.914.000 = "sin fecha"


def fin_de_mes_en_dias(foto_mes: pd.Series) -> pd.Series:
    """Fecha de la foto (último día del mes) como días desde 1970-01-01."""
    f = pd.to_datetime(foto_mes.astype(str) + "01", format="%Y%m%d") + pd.offsets.MonthEnd(0)
    return (f - pd.Timestamp("1970-01-01")).dt.days


def cierre_relativo(df: pd.DataFrame) -> pd.DataFrame:
    """fultimo_cierre vale lo mismo para ~77% de los clientes de un mes (la fecha de cierre del ciclo) y cambia
    de mes en mes (1,2,5,0,3,6): sólo identifica el mes. Lo reemplazamos por la diferencia contra la moda del mes
    (0 / +7 / +14 / +21 = a qué ciclo de facturación pertenece el cliente), que sí es estable."""
    df = df.copy()
    for c in CIERRES:
        moda = df.groupby("foto_mes")[c].transform(lambda s: s.mode().iloc[0] if s.notna().any() else np.nan)
        df[c + "_rel"] = df[c] - moda
        df = df.drop(columns=c)
    return df


def sacar_cierre(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=CIERRES)


def fechas_absolutas(df: pd.DataFrame) -> pd.DataFrame:
    """Pasa 'días desde/hasta el evento' a la fecha absoluta del evento (= fecha de la foto - días), que no cambia
    entre meses para el mismo cliente. La antigüedad en meses pasa a 'mes de ingreso' (ordinal de mes)."""
    df = df.copy()
    fin = fin_de_mes_en_dias(df["foto_mes"])
    for c in FECHAS_DIAS:
        x = df[c].where(df[c] > SENTINELA)          # el centinela -2914xxx es "sin fecha": nulo
        df[c + "_abs"] = fin - x
        df = df.drop(columns=c)
    mes_ord = df["foto_mes"] // 100 * 12 + df["foto_mes"] % 100
    df["cliente_ingreso_mes"] = mes_ord - df["cliente_antiguedad"]
    return df.drop(columns="cliente_antiguedad")


def artefacto_visa(df: pd.DataFrame) -> pd.DataFrame:
    """En 202105 y 202108 ~2% de los clientes aparece con Visa_delinquency=1 y Visa_Finiciomora=0 (en el resto de los
    meses es 0 filas): artefacto de calendario, no mora real (su tasa de BAJA+2 es la de un cliente normal).
    Los marcamos como dato roto (NaN), como sugiere el libro (§13.3)."""
    df = df.copy()
    roto = df["Visa_Finiciomora"] == 0
    df.loc[roto, ["Visa_Finiciomora", "Visa_delinquency"]] = np.nan
    return df


# --- 003c: features del mes actual (no usan historia ni otros meses) ---------------------------------------------
def _div(a: pd.Series, b: pd.Series) -> pd.Series:
    """a/b con NaN cuando el denominador es 0 o falta (evita inf)."""
    return a / b.replace(0, np.nan)


def _suma(*series: pd.Series) -> pd.Series:
    """Suma que trata NaN como 0 (no tiene la tarjeta) pero devuelve NaN si faltan todos."""
    out = series[0]
    for s in series[1:]:
        out = out.add(s, fill_value=0)
    return out


def ratios_entre_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Ratios con sentido de negocio, definidos a priori (no elegidos mirando la validación). Normalizan por tamaño
    del cliente: ticket promedio, uso del límite de tarjeta, gasto vs. ingreso, deuda vs. saldo, etc."""
    df = df.copy()
    consumo_tarjetas = _suma(df.Visa_mconsumototal, df.Master_mconsumototal)
    deuda = _suma(df.mprestamos_personales, df.mprestamos_prendarios, df.mprestamos_hipotecarios)
    nuevas = {
        "r_payroll_por_trx": _div(df.mpayroll, df.cpayroll_trx),
        "r_saldo_por_producto": _div(df.mcuentas_saldo, df.cproductos),
        "r_rentab_por_producto": _div(df.mrentabilidad, df.cproductos),
        "r_trx_por_producto": _div(df.ctrx_quarter, df.cproductos),
        "r_visa_uso_limite": _div(df.Visa_msaldototal, df.Visa_mlimitecompra),
        "r_master_uso_limite": _div(df.Master_msaldototal, df.Master_mlimitecompra),
        "r_visa_consumo_limite": _div(df.Visa_mconsumototal, df.Visa_mlimitecompra),
        "r_visa_pago_saldo": _div(df.Visa_mpagospesos, df.Visa_msaldopesos),
        "r_master_pago_saldo": _div(df.Master_mpagospesos, df.Master_msaldopesos),
        "r_visa_ticket": _div(df.mtarjeta_visa_consumo, df.ctarjeta_visa_transacciones),
        "r_master_ticket": _div(df.mtarjeta_master_consumo, df.ctarjeta_master_transacciones),
        "r_consumo_tarjetas": consumo_tarjetas,
        "r_gasto_vs_ingreso": _div(consumo_tarjetas, df.mpayroll),
        "r_deuda_vs_saldo": _div(deuda, df.mcuentas_saldo),
        "r_margen_pasivo_saldo": _div(df.mpasivos_margen, df.mcuentas_saldo),
        "r_comisiones_rentab": _div(df.mcomisiones, df.mrentabilidad),
        "r_transf_recibidas_emitidas": _div(df.mtransferencias_recibidas, df.mtransferencias_emitidas),
    }
    return df.assign(**nuevas)


def rangos_en_el_mes(df: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    """Percentil (0–1) de cada variable dentro de su propio mes: cambia 'cuánto' por 'qué tan arriba está respecto
    del resto de los clientes ese mes'. Es robusto a drift y a inflación; solo mira filas del mismo foto_mes."""
    df = df.copy()
    rangos = df.groupby("foto_mes")[variables].rank(pct=True)
    rangos.columns = [f"{c}_rk" for c in variables]
    return pd.concat([df, rangos], axis=1)


def features_negocio(df: pd.DataFrame) -> pd.DataFrame:
    """003d — sumas, restas y ratios agregados por grupos de negocio, definidos a priori (no mirando la validación).
    Usan solo columnas del mismo mes. NaN en un componente cuenta como 0 mientras haya al menos otro dato."""
    df = df.copy()
    S = _suma
    ingresos = S(df.mpayroll, df.mpayroll2, df.mtransferencias_recibidas, df.mcheques_depositados)
    egresos = S(df.mtransferencias_emitidas, df.mcheques_emitidos, df.mpagodeservicios, df.mpagomiscuentas,
                df.mextraccion_autoservicio, df.mcuenta_debitos_automaticos, df.mttarjeta_visa_debitos_automaticos,
                df.mttarjeta_master_debitos_automaticos)
    inversiones = S(df.mplazo_fijo_dolares, df.mplazo_fijo_pesos, df.minversion1_pesos, df.minversion1_dolares, df.minversion2)
    deuda = S(df.mprestamos_personales, df.mprestamos_prendarios, df.mprestamos_hipotecarios)
    saldo_paquete = S(df.mcuenta_corriente, df.mcaja_ahorro, df.mcaja_ahorro_dolares, df.mcuenta_corriente_adicional, df.mcaja_ahorro_adicional)
    limite = S(df.Visa_mlimitecompra, df.Master_mlimitecompra)
    saldo_tarjetas = S(df.Visa_msaldototal, df.Master_msaldototal)
    comisiones = S(df.mcomisiones_mantenimiento, df.mcomisiones_otras)
    trx_digital = S(df.chomebanking_transacciones, df.cmobile_app_trx)
    trx_fisica = S(df.ccajas_transacciones, df.catm_trx, df.catm_trx_other)
    indicadores = ["ccuenta_corriente", "ccaja_ahorro", "ctarjeta_debito", "ctarjeta_visa", "ctarjeta_master", "cprestamos_personales",
                   "cprestamos_prendarios", "cprestamos_hipotecarios", "cplazo_fijo", "cinversion1", "cinversion2", "cseguro_vida",
                   "cseguro_auto", "cseguro_vivienda", "cseguro_accidentes_personales", "ccaja_seguridad", "cpayroll_trx"]
    nuevas = {
        "n_ingresos": ingresos, "n_egresos": egresos, "n_neto": ingresos - egresos, "n_ingr_sobre_egr": _div(ingresos, egresos),
        "n_payroll_share": _div(df.mpayroll, ingresos),
        "n_inversiones": inversiones, "n_deuda": deuda, "n_patrimonio": S(df.mcuentas_saldo, inversiones) - deuda.fillna(0),
        "n_inv_sobre_patrim": _div(inversiones, S(df.mcuentas_saldo, inversiones)),
        "n_saldo_paquete": saldo_paquete, "n_usd_share": _div(df.mcaja_ahorro_dolares, saldo_paquete),
        "n_limite_total": limite, "n_saldo_tarjetas": saldo_tarjetas, "n_uso_limite_total": _div(saldo_tarjetas, limite),
        "n_comisiones": comisiones, "n_comis_mant_share": _div(df.mcomisiones_mantenimiento, comisiones),
        "n_descuentos": S(df.mtarjeta_visa_descuentos, df.mtarjeta_master_descuentos, df.mcajeros_propios_descuentos),
        "n_rentab_mes_vs_anual": _div(df.mrentabilidad * 12, df.mrentabilidad_annual),
        "n_pasivos_sobre_rentab": _div(df.mpasivos_margen, df.mrentabilidad), "n_activos_sobre_rentab": _div(df.mactivos_margen, df.mrentabilidad),
        "n_seguros": S(df.cseguro_vida, df.cseguro_auto, df.cseguro_vivienda, df.cseguro_accidentes_personales),
        "n_trx_digital": trx_digital, "n_trx_fisica": trx_fisica, "n_digital_share": _div(trx_digital, S(trx_digital, trx_fisica)),
        "n_productos_activos": sum((df[c].fillna(0) > 0).astype(int) for c in indicadores),
        "n_activos_sobre_cproductos": _div(sum((df[c].fillna(0) > 0).astype(int) for c in indicadores), df.cproductos),
    }
    return df.assign(**nuevas)


# --- 011: agregados de cambios, eventos de productos, comisiones normalizadas --------------------------------------
def agregados_cambios(df: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    """Conteos fila a fila sobre los cambios vs el mes anterior de `variables` (usa `{v}_lag1` y `{v}_r1` ya armadas).
    Un árbol no puede construir un conteo sobre 50 columnas: 'cuántas variables cayeron a la mitad' resume una señal difusa de que el
    cliente se está desarmando. Solo cuentan variables con lag > 0 (si no, el cambio relativo no está definido). NaN si no hay historia."""
    lag = df[[f"{v}_lag1" for v in variables]].to_numpy(dtype=float)
    hoy = df[variables].to_numpy(dtype=float)
    r = np.clip(df[[f"{v}_r1" for v in variables]].to_numpy(dtype=float), -1, 2)
    validas = lag > 0
    n_val = validas.sum(axis=1).astype(float)
    sin_hist = np.isnan(lag).all(axis=1)
    cae50 = (validas & (r <= -0.5)).sum(axis=1)
    cero = (validas & (np.nan_to_num(hoy, nan=0) == 0)).sum(axis=1)
    sube50 = (validas & (r >= 0.5)).sum(axis=1)
    out = pd.DataFrame({"g_n_validas": n_val, "g_n_cae50": cae50, "g_n_a_cero": cero, "g_n_sube50": sube50,
                        "g_share_cae50": cae50 / np.where(n_val > 0, n_val, np.nan),
                        "g_media_r1": np.nanmean(np.where(validas, r, np.nan), axis=1)}, index=df.index)
    out[sin_hist] = np.nan
    return out


def eventos_productos(df: pd.DataFrame, lag: pd.DataFrame) -> pd.DataFrame:
    """Eventos entre el mes anterior y este (`lag` = columnas `{v}_lag1` de lags_crudos): productos perdidos/ganados y banderas de
    'dejó de cobrar sueldo', 'dejó de usar la tarjeta', 'dejó de usar homebanking'. NaN (no 0) si el cliente no tenía el mes anterior."""
    indicadores = ["ccuenta_corriente", "ccaja_ahorro", "ctarjeta_debito", "ctarjeta_visa", "ctarjeta_master", "cprestamos_personales",
                   "cprestamos_prendarios", "cprestamos_hipotecarios", "cplazo_fijo", "cinversion1", "cinversion2", "cseguro_vida",
                   "cseguro_auto", "cseguro_vivienda", "cseguro_accidentes_personales", "ccaja_seguridad", "cpayroll_trx"]
    hay = lag["cproductos_lag1"].notna()
    hoy = lambda c: df[c].fillna(0)            # noqa: E731  (NaN = no tiene el producto)
    ant = lambda c: lag[f"{c}_lag1"].fillna(0)  # noqa: E731
    perdidos = sum(((ant(c) > 0) & (hoy(c) == 0)).astype(int) for c in indicadores)
    ganados = sum(((ant(c) == 0) & (hoy(c) > 0)).astype(int) for c in indicadores)
    consumo_ant = ant("Visa_mconsumototal") + ant("Master_mconsumototal"); consumo = hoy("Visa_mconsumototal") + hoy("Master_mconsumototal")
    ev = {"e_prod_perdidos": perdidos, "e_prod_ganados": ganados, "e_prod_neto": ganados - perdidos,
          "e_dejo_payroll": ((ant("mpayroll") > 0) & (hoy("mpayroll") == 0)).astype(int),
          "e_dejo_payroll_trx": ((ant("cpayroll_trx") > 0) & (hoy("cpayroll_trx") == 0)).astype(int),
          "e_dejo_consumo_tarjetas": ((consumo_ant > 0) & (consumo == 0)).astype(int),
          "e_dejo_homebanking": ((ant("chomebanking_transacciones") > 0) & (hoy("chomebanking_transacciones") == 0)).astype(int),
          "e_d_cproductos": df["cproductos"] - lag["cproductos_lag1"]}
    return pd.DataFrame(ev, index=df.index).where(hay)


def comisiones_normalizadas(df: pd.DataFrame) -> pd.DataFrame:
    """`mcomisiones_mantenimiento` dividida por la mediana (de los valores > 0) de su propio mes: el monto nominal salta de un mes a otro
    (C1 de 008: la variable que más separa 202108 del train) y la versión relativa debería sobrevivir. Solo mira filas del mismo mes."""
    x = df["mcomisiones_mantenimiento"]
    mediana = x.where(x > 0).groupby(df["foto_mes"]).transform("median")
    return pd.DataFrame({"mcomisiones_mant_norm": x / mediana}, index=df.index)
