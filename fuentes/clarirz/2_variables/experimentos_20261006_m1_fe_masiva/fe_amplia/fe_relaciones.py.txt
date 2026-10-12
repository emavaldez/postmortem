"""Candidate, target-free relations for the DMEyF panel.

Only raw columns and past/current snapshots are accessed.  Every yielded array
has one value per panel row; undefined quantities stay NaN.  This module proposes
features, it does not assert that they improve a predictive model.
"""
from __future__ import annotations

import numpy as np

__all__ = ["generate_relations"]

# Amount and count refer to the same named concept and monthly period.
TICKETS = (
    ("payroll", "mpayroll", "cpayroll_trx"),
    ("payroll2", "mpayroll2", "cpayroll2_trx"),
    ("visa", "mtarjeta_visa_consumo", "ctarjeta_visa_transacciones"),
    ("master", "mtarjeta_master_consumo", "ctarjeta_master_transacciones"),
    ("extraccion_autoservicio", "mextraccion_autoservicio", "cextraccion_autoservicio"),
    ("atm", "matm", "catm_trx"),
    ("atm_other", "matm_other", "catm_trx_other"),
    ("transferencias_recibidas", "mtransferencias_recibidas", "ctransferencias_recibidas"),
    ("transferencias_emitidas", "mtransferencias_emitidas", "ctransferencias_emitidas"),
    ("pagodeservicios", "mpagodeservicios", "cpagodeservicios"),
    ("pagomiscuentas", "mpagomiscuentas", "cpagomiscuentas"),
    ("debitos_cuenta", "mcuenta_debitos_automaticos", "ccuenta_debitos_automaticos"),
    ("debitos_visa", "mttarjeta_visa_debitos_automaticos", "ctarjeta_visa_debitos_automaticos"),
    ("debitos_master", "mttarjeta_master_debitos_automaticos", "ctarjeta_master_debitos_automaticos"),
    ("descuentos_debito", "mcajeros_propios_descuentos", "ccajeros_propios_descuentos"),
    ("descuentos_visa", "mtarjeta_visa_descuentos", "ctarjeta_visa_descuentos"),
    ("descuentos_master", "mtarjeta_master_descuentos", "ctarjeta_master_descuentos"),
    ("comisiones_mantenimiento", "mcomisiones_mantenimiento", "ccomisiones_mantenimiento"),
    ("comisiones_otras", "mcomisiones_otras", "ccomisiones_otras"),
    ("cheques_depositados", "mcheques_depositados", "ccheques_depositados"),
    ("cheques_emitidos", "mcheques_emitidos", "ccheques_emitidos"),
    ("cheques_depositados_rechazados", "mcheques_depositados_rechazados", "ccheques_depositados_rechazados"),
    ("cheques_emitidos_rechazados", "mcheques_emitidos_rechazados", "ccheques_emitidos_rechazados"),
    ("forex_buy", "mforex_buy", "cforex_buy"),
    ("forex_sell", "mforex_sell", "cforex_sell"),
    ("visa_detalle", "Visa_mconsumototal", "Visa_cconsumos"),
    ("master_detalle", "Master_mconsumototal", "Master_cconsumos"),
)

# These seven domains are channels/functions, NOT mutually exclusive operations.
# Counts provide evidence of use.  Amounts, fees, profits, product stocks,
# nominal status codes and 'ever installed' flags are intentionally excluded.
FUNCTIONS = {
    "haberes": ("cpayroll_trx", "cpayroll2_trx"),
    "tarjetas": ("ctarjeta_debito_transacciones", "ctarjeta_visa_transacciones", "ctarjeta_master_transacciones"),
    "pagos": ("cpagomiscuentas", "cpagodeservicios", "ccuenta_debitos_automaticos", "ctarjeta_visa_debitos_automaticos", "ctarjeta_master_debitos_automaticos"),
    "transferencias": ("ctransferencias_recibidas", "ctransferencias_emitidas"),
    "cajeros_y_extracciones": ("cextraccion_autoservicio", "catm_trx", "catm_trx_other", "ccajas_extracciones"),
    "digitales": ("chomebanking_transacciones", "cmobile_app_trx"),
    "atencion": ("ccallcenter_transacciones", "ccajas_transacciones", "ccajas_consultas", "ccajas_depositos", "ccajas_otras"),
}

CARD_FIELDS = (
    "mfinanciacion_limite", "mlimitecompra", "msaldototal", "msaldopesos",
    "msaldodolares", "mconsumospesos", "mconsumosdolares", "mconsumototal",
    "madelantopesos", "madelantodolares", "mpagado", "mpagospesos",
    "mpagosdolares", "mpagominimo", "cconsumos", "cadelantosefectivo",
)
PRODUCTS = {
    "cuentas": ("ccuenta_corriente", "ccaja_ahorro"),
    "debito": ("ctarjeta_debito",),
    "credito": ("ctarjeta_visa", "ctarjeta_master"),
    "prestamos_personales": ("cprestamos_personales",),
    "prestamos_prendarios": ("cprestamos_prendarios",),
    "prestamos_hipotecarios": ("cprestamos_hipotecarios",),
    "plazo_fijo": ("cplazo_fijo",),
    "inversiones": ("cinversion1", "cinversion2"),
    "seguros": ("cseguro_vida", "cseguro_auto", "cseguro_vivienda", "cseguro_accidentes_personales"),
}


def _safe_ratio(num, den, nonnegative_num=False):
    """Undefined denominator (including zero) is NaN; never add epsilon."""
    out = np.full(len(num), np.nan, dtype=np.float64)
    good = np.isfinite(num) & np.isfinite(den) & (den > 0)
    if nonnegative_num:
        good &= num >= 0
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        np.divide(num, den, out=out, where=good)
    out[~np.isfinite(out)] = np.nan
    return out


def _activity(arrays):
    """Positive evidence wins; inactivity requires every count observed as zero."""
    any_positive = np.zeros(len(arrays[0]), dtype=bool)
    all_zero = np.ones(len(arrays[0]), dtype=bool)
    for x in arrays:
        finite = np.isfinite(x)
        any_positive |= finite & (x > 0)
        all_zero &= finite & (x == 0)
    out = np.full(len(arrays[0]), np.nan, dtype=np.float64)
    out[all_zero] = 0.0
    out[any_positive] = 1.0
    return out


def _and(a, b):
    """Three-valued Boolean AND: false dominates unknown."""
    out = np.full(len(a), np.nan, dtype=np.float64)
    out[(a == 0) | (b == 0)] = 0.0
    out[(a == 1) & (b == 1)] = 1.0
    return out


def _strict_sum(arrays):
    """Arithmetic sum only when every required component is finite."""
    out = np.zeros(len(arrays[0]), dtype=np.float64)
    good = np.ones(len(out), dtype=bool)
    with np.errstate(over="ignore", invalid="ignore"):
        for x in arrays:
            good &= np.isfinite(x)
            out += x
    out[~good | ~np.isfinite(out)] = np.nan
    return out


def _n_finite(arrays, nonnegative=False):
    out = np.zeros(len(arrays[0]), dtype=np.float64)
    for x in arrays:
        out += np.isfinite(x) & ((x >= 0) if nonnegative else True)
    return out


def _meta(block, sources, formula, interpretation, unit, caution="", min_history=0):
    return dict(block=block, sources=list(dict.fromkeys(sources)), formula=formula,
                interpretation=interpretation, min_history=int(min_history),
                unit=unit, caution=caution)


def generate_relations(panel, config):
    """Yield ``(name, values, metadata)``; ``relations=False`` disables the module.

    panel supplies df/get/lag/rank/columns/n.  panel.lag MUST enforce same-customer
    exact calendar lags; no row shift across an absent month is valid.  Filtering
    on metadata['block'] belongs to the caller.  Source absence skips a whole
    feature definition rather than silently redefining its denominator/domain.
    """
    if not config.get("relations", True):
        return
    available = set(panel.columns)
    n = int(panel.n)
    history = []
    has = lambda cols: all(c in available for c in cols)

    def get(v):
        # Borrow panel arrays read-only; never modify raw vectors in-place.
        out = np.asarray(panel.get(v), dtype=np.float64)
        if out.ndim != 1 or len(out) != n:
            raise ValueError(f"Invalid raw vector shape for {v}: {out.shape}")
        return out

    def emit(suffix, values, meta, remember=False, binary=False):
        values = np.asarray(values, dtype=np.float64)
        if values.ndim != 1 or len(values) != n:
            raise ValueError(f"Invalid feature shape for {suffix}: {values.shape}")
        if np.isinf(values).any():
            values = values.copy()
            values[np.isinf(values)] = np.nan
        name = "fe__rel__" + suffix
        if remember:
            history.append((name, values, meta, binary))
        return name, values, meta

    # Monthly amount per recorded operation. Negative numerators are retained:
    # they may represent adjustments; they never become activity indicators.
    for concept, amount, count in TICKETS:
        if not has((amount, count)):
            continue
        caution = ("Denominador estrictamente positivo y ambos campos finitos; 0/0 es NA. "
                   "Montos negativos se conservan como ajustes posibles. No mide número de productos.")
        if concept.startswith("comisiones"):
            caution += " Comisión cobrada no equivale a una operación voluntaria del cliente."
        yield emit("ticket__" + concept, _safe_ratio(get(amount), get(count)),
                   _meta("ratios", (amount, count), f"{amount}/{count} si {count}>0",
                         f"Monto medio por registro mensual: {concept}", "pesos_por_registro", caution))

    # Card fields are combined only with the identical field in the other brand.
    for field in CARD_FIELDS:
        cols = ("Visa_" + field, "Master_" + field)
        if not has(cols):
            continue
        a, b = (get(v) for v in cols)
        unit = "conteo" if field.startswith("c") else "unidad_original_del_campo"
        caution = ("Mismo campo en Visa y Master; suma/diferencia requieren ambos observados. "
                   "No convierte monedas, no suma pesos con dólares ni completa una marca faltante con cero. "
                   "Cantidad de marcas observadas mide cobertura, no tenencia.")
        if field == "msaldototal":
            caution += " EDA detectó escala aproximada 0.8525 en Visa_msaldototal respecto de sus componentes; comparabilidad de escala pendiente."
        summed = _strict_sum([a, b])
        yield emit("tarjetas__" + field + "_sum", summed,
                   _meta("tarjetas", cols, "Visa_campo + Master_campo; soporte completo",
                         "Total del mismo concepto entre ambas marcas", unit, caution))
        yield emit("tarjetas__" + field + "_diff_visa_master", _strict_sum([a, -b]),
                   _meta("tarjetas", cols, "Visa_campo - Master_campo; soporte completo",
                         "Diferencia entre marcas en el mismo concepto", unit, caution))
        yield emit("tarjetas__" + field + "_n_marcas_observadas", _n_finite([a, b]),
                   _meta("tarjetas", cols, "I(Visa observado)+I(Master observado)",
                         "Cobertura del campo, de cero a dos marcas", "conteo", caution))
        if field in ("mlimitecompra", "mfinanciacion_limite", "mconsumototal", "cconsumos", "cadelantosefectivo"):
            share = _safe_ratio(a, summed, nonnegative_num=True)
            share[~np.isfinite(b) | (b < 0)] = np.nan
            yield emit("tarjetas__" + field + "_fraccion_visa", share,
                       _meta("tarjetas", cols, "Visa/(Visa+Master), ambos>=0, suma>0",
                             "Participación de Visa en un concepto observado en las dos marcas",
                             "fraccion", caution + " No se define con total cero o componentes negativos."))

    for brand in ("Visa", "Master"):
        # These are accounting ratios, not assertions of arrears or limit breach.
        ratios = (
            ("consumo_sobre_limite_compra", "mconsumototal", "mlimitecompra", "Consumo mensual respecto del límite de compra"),
            ("saldo_no_negativo_sobre_limite_financiacion", "msaldototal", "mfinanciacion_limite", "Saldo no negativo respecto del límite de financiación"),
            ("pagado_sobre_pago_minimo", "mpagado", "mpagominimo", "Pagos registrados respecto del pago mínimo informado"),
        )
        for suffix, numerator, denominator, meaning in ratios:
            cols = (brand + "_" + numerator, brand + "_" + denominator)
            if not has(cols):
                continue
            yield emit("tarjetas__" + brand.lower() + "_" + suffix,
                       _safe_ratio(get(cols[0]), get(cols[1]), nonnegative_num=True),
                       _meta("tarjetas", cols, "numerador>=0 / denominador>0; ambos finitos",
                             meaning, "razon",
                             "Relación contable exploratoria: los cortes pueden diferir. No acredita mora, pago suficiente ni utilización contractual exacta. No se trunca en 1. Visa_msaldototal mostró escala aproximada 0.8525 frente a sus componentes; relación saldo/límite conserva esa incertidumbre."))

    # Separately identify ownership and observed use, without treating missing
    # card details as absence of a card.
    own, use = {}, {}
    for brand, owncol, usecol in (
        ("visa", "ctarjeta_visa", "ctarjeta_visa_transacciones"),
        ("master", "ctarjeta_master", "ctarjeta_master_transacciones"),
        ("debito", "ctarjeta_debito", "ctarjeta_debito_transacciones"),
    ):
        if not has((owncol, usecol)):
            continue
        own[brand], use[brand] = _activity([get(owncol)]), _activity([get(usecol)])
        for suffix, values, formula, meaning in (
            ("tenencia_sin_uso", _and(own[brand], 1 - use[brand]), "tenencia>0 AND transacciones=0", "Tenencia observada sin uso mensual observado"),
            ("tenencia_con_uso", _and(own[brand], use[brand]), "tenencia>0 AND transacciones>0", "Tenencia y uso observados"),
            ("uso_sin_tenencia", _and(1 - own[brand], use[brand]), "tenencia=0 AND transacciones>0", "Incoherencia o diferencia de corte entre tenencia y uso"),
        ):
            yield emit("tarjetas__" + brand + "_" + suffix, values,
                       _meta("tarjetas", (owncol, usecol), formula, meaning, "indicador_0_1",
                             "Lógica de tres valores; una ausencia de información no equivale a cero. Tenencia no significa actividad."))
    if all(b in own for b in ("visa", "master")):
        sources = ("ctarjeta_visa", "ctarjeta_master")
        yield emit("tarjetas__n_marcas_con_cuenta", _strict_sum([own['visa'], own['master']]),
                   _meta("tarjetas", sources, "I(cuentas Visa>0)+I(cuentas Master>0), ambos resueltos",
                         "Cantidad de marcas de crédito con cuenta observada", "conteo",
                         "No cuenta plásticos ni monedas y no mide uso."), remember=True)
        sources = ("ctarjeta_visa_transacciones", "ctarjeta_master_transacciones")
        yield emit("tarjetas__n_marcas_con_uso", _strict_sum([use['visa'], use['master']]),
                   _meta("tarjetas", sources, "I(trx Visa>0)+I(trx Master>0), ambos resueltos",
                         "Cantidad de marcas de crédito con transacciones", "conteo",
                         "No equivale al total de transacciones."), remember=True)

    function_flags = {}
    for domain, cols in FUNCTIONS.items():
        if not has(cols):
            continue
        arrays = [get(c) for c in cols]
        flag = _activity(arrays)
        function_flags[domain] = flag
        caution = ("Un positivo observado implica función activa; cero exige todos los conteos observados en cero. "
                   "Los negativos inesperados no prueban inactividad. Dominios pueden solaparse; no suman operaciones únicas.")
        if domain == "digitales":
            caution += " cmobile_app_trx tiene semántica empírica binaria; se usa sólo su positividad, no su magnitud."
        if domain == "atencion":
            caution += " ccajas_depositos fue constante en mayo; interpretar con la auditoría de fuente."
        yield emit("funcion__" + domain + "_activa", flag,
                   _meta("funciones", cols, "OR de conteos>0; 0 sólo con todos=0; resto NA",
                         "Evidencia de uso mensual del dominio " + domain,
                         "indicador_0_1", caution), remember=True, binary=True)
        yield emit("funcion__" + domain + "_n_campos_validos", _n_finite(arrays, nonnegative=True),
                   _meta("funciones", cols, "sum I(conteo finito y>=0)",
                         "Cobertura de los conteos requeridos para interpretar el dominio", "conteo", caution))
    all_function_sources = tuple(dict.fromkeys(c for cols in FUNCTIONS.values() for c in cols))
    function_total = None
    if len(function_flags) == len(FUNCTIONS):
        flags = list(function_flags.values())
        function_total = _strict_sum(flags)
        resolved = _n_finite(flags)
        lower = np.zeros(n, dtype=np.float64)
        for x in flags:
            lower += x == 1
        caution = ("Siete dominios fijos: haberes, tarjetas, pagos, transferencias, cajeros/extracciones, digitales y atención. "
                   "Miden amplitud de uso; no son operaciones independientes ni productos. No incluyen comisiones, rentabilidad o saldos.")
        for suffix, values, formula, meaning in (
            ("n_activas", function_total, "suma de siete indicadores; todos resueltos", "Amplitud mensual de funciones activas con cobertura completa"),
            ("n_activas_min", lower, "número de dominios con evidencia positiva", "Cota inferior de funciones activas, aunque falte información"),
            ("n_resueltas", resolved, "número de indicadores 0/1 resueltos", "Cobertura para interpretar amplitud de uso"),
        ):
            yield emit("funciones__" + suffix, values,
                       _meta("funciones", all_function_sources, formula, meaning, "conteo", caution),
                       remember=(suffix == "n_activas"))
        yield emit("funciones__fraccion_activas_observadas", _safe_ratio(lower, resolved),
                   _meta("funciones", all_function_sources, "n_activas_min/n_resueltas si n_resueltas>0",
                         "Fracción activa entre funciones resueltas", "fraccion",
                         caution + " Denominador variable: comparar junto con n_resueltas; no sustituye al total completo."))

    product_flags = {}
    for domain, cols in PRODUCTS.items():
        if not has(cols):
            continue
        flag = _activity([get(c) for c in cols]); product_flags[domain] = flag
        yield emit("producto__" + domain + "_presente", flag,
                   _meta("stocks_productos_deuda", cols, "OR de cantidades>0; 0 sólo con todos=0",
                         "Tenencia del grupo de productos " + domain, "indicador_0_1",
                         "Tenencia no equivale a uso, pago de cuotas ni compromiso activo. No utiliza montos como un segundo producto."))
    if len(product_flags) == len(PRODUCTS):
        psources = tuple(dict.fromkeys(c for cols in PRODUCTS.values() for c in cols))
        product_total = _strict_sum(list(product_flags.values()))
        yield emit("productos__n_familias_presentes", product_total,
                   _meta("stocks_productos_deuda", psources, "suma de nueve grupos de tenencia con cobertura completa",
                         "Diversidad de grupos de productos presentes", "conteo",
                         "Nueve grupos definidos en PRODUCTS; no coincide con cproductos ni cuenta monedas o cuentas individuales."), remember=True)
        if function_total is not None:
            yield emit("productos__familias_sin_funciones_observadas",
                       _and(_activity([product_total]), 1 - _activity([function_total])),
                       _meta("stocks_productos_deuda", psources + all_function_sources,
                             "n_familias_presentes>0 AND n_funciones_activas=0",
                             "Productos presentes con las siete funciones observadas inactivas", "indicador_0_1",
                             "No significa cliente sin relación, cuenta cerrada ni deuda como único vínculo."))

    loan_types = ("personales", "prendarios", "hipotecarios")
    loan_counts = tuple("cprestamos_" + t for t in loan_types)
    loan_amounts = tuple("mprestamos_" + t for t in loan_types)
    loan_stock = None
    if has(loan_amounts):
        loan_stock = _strict_sum([get(c) for c in loan_amounts])
        yield emit("deuda__prestamos_saldo_total", loan_stock,
                   _meta("stocks_productos_deuda", loan_amounts, "suma de tres saldos restantes; soporte completo",
                         "Saldo de deuda restante de los préstamos registrados", "pesos",
                         "Es un stock, no una cuota pagada ni mora. No se añade saldo de cuenta negativo o tarjeta para evitar mezclar conceptos."), remember=True)
    if has(loan_counts):
        yield emit("deuda__prestamos_cantidad_total", _strict_sum([get(c) for c in loan_counts]),
                   _meta("stocks_productos_deuda", loan_counts, "suma de cantidades de préstamos vigentes; soporte completo",
                         "Cantidad de préstamos vigentes", "conteo",
                         "No informa cuántas cuotas se pagaron ni si hay atraso."))
    for kind in loan_types:
        cols = ("mprestamos_" + kind, "cprestamos_" + kind)
        if has(cols):
            yield emit("deuda__saldo_medio_" + kind, _safe_ratio(get(cols[0]), get(cols[1])),
                       _meta("stocks_productos_deuda", cols, "saldo restante/cantidad vigente si cantidad>0",
                             "Saldo medio por préstamo de la misma clase", "pesos_por_prestamo",
                             "Promedio de stocks, no ticket de una transacción ni pago mensual."))
    if has(("mcuentas_saldo",)):
        balance = get("mcuentas_saldo"); good = np.isfinite(balance)
        for suffix, vals, meaning in (
            ("saldo_cuentas_positivo", np.where(good, np.maximum(balance, 0), np.nan), "Parte positiva del saldo total de cuentas"),
            ("saldo_cuentas_negativo_magnitud", np.where(good, np.maximum(-balance, 0), np.nan), "Magnitud de la parte negativa del saldo total de cuentas"),
        ):
            yield emit("stock__" + suffix, vals,
                       _meta("stocks_productos_deuda", ("mcuentas_saldo",), "max(saldo,0) o max(-saldo,0); NA preservado",
                             meaning, "pesos", "Saldo es posición, no flujo ni actividad. Saldo negativo no prueba inactividad ni mora."))

    # Directed hypotheses from semantic relations, not an all-pairs explosion.
    # Binary conditions are explicit; no arbitrary ordinal encoding of internet,
    # card status, clusters or the target is involved.
    if has(("cpayroll_trx", "mtarjeta_visa_consumo")):
        cols = ("cpayroll_trx", "mtarjeta_visa_consumo")
        p, v = _activity([get(cols[0])]), _activity([get(cols[1])])
        for suffix, a, b, meaning in (
            ("haberes_visa_ambos_positivos", p, v, "Haberes acreditados y consumo Visa positivo"),
            ("haberes_visa_ambos_cero", 1-p, 1-v, "Ausencia observada de haberes y consumo Visa en la foto"),
            ("haberes_sin_consumo_visa", p, 1-v, "Haberes acreditados con consumo Visa observado en cero"),
            ("consumo_visa_sin_haberes", 1-p, v, "Consumo Visa positivo con haberes observados en cero"),
        ):
            yield emit("interaccion__" + suffix, _and(a, b),
                       _meta("interacciones", cols, "AND de condiciones binarias con tres valores",
                             meaning, "indicador_0_1",
                             "Complementariedad descriptiva del EDA; no interacción predictiva aprobada. Una foto no demuestra apagado histórico ni ausencia de otras funciones."),
                       remember=(suffix == "haberes_visa_ambos_cero"), binary=True)

    if has(("mcuentas_saldo", "cextraccion_autoservicio")):
        cols = ("mcuentas_saldo", "cextraccion_autoservicio")
        balance = get(cols[0]); extr = _activity([get(cols[1])])
        negative = np.where(np.isfinite(balance), (balance < 0).astype(float), np.nan)
        for suffix, b, meaning in (
            ("saldo_negativo_sin_extracciones", 1-extr, "Saldo negativo con extracciones observadas en cero"),
            ("saldo_negativo_con_extracciones", extr, "Saldo negativo con extracciones registradas"),
        ):
            yield emit("interaccion__" + suffix, _and(negative, b),
                       _meta("interacciones", cols, "saldo<0 AND condición de extracciones; tres valores",
                             meaning, "indicador_0_1",
                             "No identifica mora ni causa de baja; el signo del saldo y el uso describen dimensiones distintas."))
        yield emit("interaccion__saldo_por_estado_extraccion", balance * extr,
                   _meta("interacciones", cols, "mcuentas_saldo * I(extracciones>0); requiere ambos observados",
                         "Saldo signed condicionado a extracción observada", "pesos",
                         "Producto dirigido, no cociente por un saldo cercano a cero; su utilidad debe contrastarse frente a efectos principales."))

    if has(("cextraccion_autoservicio", "ctransferencias_recibidas")):
        cols = ("cextraccion_autoservicio", "ctransferencias_recibidas")
        extraction = _activity([get(cols[0])]); received = _activity([get(cols[1])])
        for suffix, a, b, meaning in (
            ("extraccion_transferencia_ambas_positivas", extraction, received, "Extracciones y transferencias recibidas registradas"),
            ("extraccion_transferencia_ambas_cero", 1-extraction, 1-received, "Extracciones y transferencias recibidas observadas en cero"),
            ("extraccion_sin_transferencia_recibida", extraction, 1-received, "Extracciones con transferencias recibidas observadas en cero"),
            ("transferencia_recibida_sin_extraccion", 1-extraction, received, "Transferencias recibidas con extracciones observadas en cero"),
        ):
            yield emit("interaccion__" + suffix, _and(a, b),
                       _meta("interacciones", cols, "AND de condiciones de conteos positivos/cero; tres valores",
                             meaning, "indicador_0_1",
                             "Familia motivada por relación exploratoria entre montos, reformulada con conteos para estados interpretables. No supone que una transferencia financió una extracción ni añade un ratio monetario."))

    if has(("ctrx_quarter", "mcaja_ahorro")):
        cols = ("ctrx_quarter", "mcaja_ahorro")
        quarter = _activity([get(cols[0])]); saving = get(cols[1])
        positive = np.where(np.isfinite(saving), (saving > 0).astype(float), np.nan)
        yield emit("interaccion__caja_positiva_sin_trx_trimestre", _and(positive, 1-quarter),
                   _meta("interacciones", cols, "mcaja_ahorro>0 AND ctrx_quarter=0; tres valores",
                         "Saldo positivo en caja de ahorro con cero transacciones trimestrales registradas", "indicador_0_1",
                         "Combina stock y ventana de 90 días. No interpreta ausencia de transacciones como cuenta vacía ni cierre."))
        rq = np.asarray(panel.rank(get(cols[0])), dtype=np.float64)
        rs = np.asarray(panel.rank(saving), dtype=np.float64)
        yield emit("interaccion__brecha_rank_trx_caja", rq-rs,
                   _meta("interacciones", cols, "rango_percentil_mensual(ctrx_quarter)-rango_percentil_mensual(mcaja_ahorro)",
                         "Desacople relativo entre nivel transaccional trimestral y saldo", "diferencia_de_percentiles",
                         "Rangos sin target, calculados en la foto actual. Empates y población afectan su valor; no es una relación causal ni un ratio monetario."))

    # History of deliberately selected summaries: no future snapshots and no
    # zero-fill at panel boundaries. Other raw-column history belongs elsewhere.
    if not config.get("relations_history", True):
        return
    lags = sorted({int(k) for k in config.get("lags", [1, 2, 3, 4, 5]) if int(k) > 0})
    windows = sorted({int(w) for w in config.get("windows", [2, 3, 4, 5, 6]) if int(w) >= 2})
    for name, current, meta, binary in history:
        base = name.removeprefix("fe__rel__")
        hist_caution = (meta['caution'] + " Historia por meses calendario del mismo cliente; una foto ausente no es cero. "
                        "Los lags del resumen se recalculan sobre sus valores pasados; no incorporan información futura.")
        for k in lags:
            past = np.asarray(panel.lag(current, k), dtype=np.float64)
            for operation, values, formula in (
                (f"lag{k}", past, f"{name}(t-{k})"),
                (f"delta{k}", current-past, f"{name}(t)-{name}(t-{k})"),
            ):
                yield emit(base + "__" + operation, values,
                           _meta("historia_relaciones", meta['sources'], formula,
                                 "Historia del resumen: " + meta['interpretation'],
                                 "cambio_indicador_-1_0_1" if binary and operation.startswith("delta") else meta['unit'], hist_caution, k))
            if binary:
                known = np.isfinite(current) & np.isfinite(past)
                for suffix, before, now in (("pasa_a_cero",1,0), ("pasa_a_uno",0,1), ("persiste_uno",1,1), ("persiste_cero",0,0)):
                    vals = np.where(known, ((past == before) & (current == now)).astype(float), np.nan)
                    yield emit(base + f"__{suffix}_lag{k}", vals,
                               _meta("historia_relaciones", meta['sources'], f"I({name}(t-{k})={before} AND {name}(t)={now}), extremos observados",
                                     "Transición entre extremos observados del resumen", "indicador_0_1",
                                     hist_caution + " Para lag>1 no prueba permanencia ni monotonicidad en meses intermedios.", k))
        for w in windows:
            # Exact w-month history including t; neither expanding windows nor
            # variable denominators are substituted when history is incomplete.
            observed = np.isfinite(current).astype(np.float64)
            total = np.where(np.isfinite(current), current, 0.0)
            mn = np.where(np.isfinite(current), current, np.inf)
            mx = np.where(np.isfinite(current), current, -np.inf)
            for k in range(1, w):
                prev = np.asarray(panel.lag(current, k), dtype=np.float64)
                ok = np.isfinite(prev); observed += ok
                total += np.where(ok, prev, 0.0)
                mn = np.minimum(mn, np.where(ok, prev, np.inf))
                mx = np.maximum(mx, np.where(ok, prev, -np.inf))
            complete = observed == w
            definitions = (
                ("n_observados", observed, "conteo", "Cantidad de meses con resumen interpretable"),
                ("media", np.where(complete, total/w, np.nan), "fraccion" if binary else meta['unit'], "Media con todos los meses observados"),
                ("min", np.where(complete, mn, np.nan), meta['unit'], "Mínimo con todos los meses observados"),
                ("max", np.where(complete, mx, np.nan), meta['unit'], "Máximo con todos los meses observados"),
            )
            for op, vals, unit, meaning in definitions:
                yield emit(base + f"__{op}_ventana{w}", vals,
                           _meta("historia_relaciones", meta['sources'], f"{op} de {name} en [t-{w-1},t]; ventana fija",
                                 meaning + ": " + meta['interpretation'], unit,
                                 hist_caution + " Media/min/max son NA sin ventana completa; n_observados conserva la cobertura.",
                                 0 if op == "n_observados" else w-1))
