"""Catálogo semántico de los 152 predictores fuente, sin selección por target.

El catálogo distingue representaciones y habilita operaciones compatibles;
no calcula transformaciones, no imputa y no redefine valores de la fuente.
"""
from __future__ import annotations

import csv
from pathlib import Path

FIELDS = (
    'variable', 'kind', 'subtype', 'family', 'unit', 'history_mode',
    'zero_interpretable', 'signed', 'caution',
)
KINDS = frozenset({'numeric', 'category', 'relative_date', 'clock'})
HISTORY_MODES = frozenset({
    'nonnegative_flow', 'signed_flow', 'stock', 'count_stock',
    'rolling_flow', 'nominal', 'relative_date', 'clock', 'unknown',
})
STRUCTURAL_COLUMNS = frozenset({'numero_de_cliente', 'foto_mes', 'clase_ternaria'})
EXPECTED_VARIABLES = frozenset(('Master_Finiciomora', 'Master_Fvencimiento', 'Master_cadelantosefectivo', 'Master_cconsumos', 'Master_delinquency', 'Master_fechaalta', 'Master_fultimo_cierre', 'Master_madelantodolares', 'Master_madelantopesos', 'Master_mconsumosdolares', 'Master_mconsumospesos', 'Master_mconsumototal', 'Master_mfinanciacion_limite', 'Master_mlimitecompra', 'Master_mpagado', 'Master_mpagominimo', 'Master_mpagosdolares', 'Master_mpagospesos', 'Master_msaldodolares', 'Master_msaldopesos', 'Master_msaldototal', 'Master_status', 'Visa_Finiciomora', 'Visa_Fvencimiento', 'Visa_cadelantosefectivo', 'Visa_cconsumos', 'Visa_delinquency', 'Visa_fechaalta', 'Visa_fultimo_cierre', 'Visa_madelantodolares', 'Visa_madelantopesos', 'Visa_mconsumosdolares', 'Visa_mconsumospesos', 'Visa_mconsumototal', 'Visa_mfinanciacion_limite', 'Visa_mlimitecompra', 'Visa_mpagado', 'Visa_mpagominimo', 'Visa_mpagosdolares', 'Visa_mpagospesos', 'Visa_msaldodolares', 'Visa_msaldopesos', 'Visa_msaldototal', 'Visa_status', 'active_quarter', 'catm_trx', 'catm_trx_other', 'ccaja_ahorro', 'ccaja_seguridad', 'ccajas_consultas', 'ccajas_depositos', 'ccajas_extracciones', 'ccajas_otras', 'ccajas_transacciones', 'ccajeros_propios_descuentos', 'ccallcenter_transacciones', 'ccheques_depositados', 'ccheques_depositados_rechazados', 'ccheques_emitidos', 'ccheques_emitidos_rechazados', 'ccomisiones_mantenimiento', 'ccomisiones_otras', 'ccuenta_corriente', 'ccuenta_debitos_automaticos', 'cdescubierto_preacordado', 'cextraccion_autoservicio', 'cforex', 'cforex_buy', 'cforex_sell', 'chomebanking_transacciones', 'cinversion1', 'cinversion2', 'cliente_antiguedad', 'cliente_edad', 'cliente_vip', 'cmobile_app_trx', 'cpagodeservicios', 'cpagomiscuentas', 'cpayroll2_trx', 'cpayroll_trx', 'cplazo_fijo', 'cprestamos_hipotecarios', 'cprestamos_personales', 'cprestamos_prendarios', 'cproductos', 'cseguro_accidentes_personales', 'cseguro_auto', 'cseguro_vida', 'cseguro_vivienda', 'ctarjeta_debito', 'ctarjeta_debito_transacciones', 'ctarjeta_master', 'ctarjeta_master_debitos_automaticos', 'ctarjeta_master_descuentos', 'ctarjeta_master_transacciones', 'ctarjeta_visa', 'ctarjeta_visa_debitos_automaticos', 'ctarjeta_visa_descuentos', 'ctarjeta_visa_transacciones', 'ctransferencias_emitidas', 'ctransferencias_recibidas', 'ctrx_quarter', 'internet', 'mactivos_margen', 'matm', 'matm_other', 'mautoservicio', 'mcaja_ahorro', 'mcaja_ahorro_adicional', 'mcaja_ahorro_dolares', 'mcajeros_propios_descuentos', 'mcheques_depositados', 'mcheques_depositados_rechazados', 'mcheques_emitidos', 'mcheques_emitidos_rechazados', 'mcomisiones', 'mcomisiones_mantenimiento', 'mcomisiones_otras', 'mcuenta_corriente', 'mcuenta_corriente_adicional', 'mcuenta_debitos_automaticos', 'mcuentas_saldo', 'mextraccion_autoservicio', 'mforex_buy', 'mforex_sell', 'minversion1_dolares', 'minversion1_pesos', 'minversion2', 'mpagodeservicios', 'mpagomiscuentas', 'mpasivos_margen', 'mpayroll', 'mpayroll2', 'mplazo_fijo_dolares', 'mplazo_fijo_pesos', 'mprestamos_hipotecarios', 'mprestamos_personales', 'mprestamos_prendarios', 'mrentabilidad', 'mrentabilidad_annual', 'mtarjeta_master_consumo', 'mtarjeta_master_descuentos', 'mtarjeta_visa_consumo', 'mtarjeta_visa_descuentos', 'mtransferencias_emitidas', 'mtransferencias_recibidas', 'mttarjeta_master_debitos_automaticos', 'mttarjeta_visa_debitos_automaticos', 'tcallcenter', 'tcuentas', 'thomebanking', 'tmobile_app'))


def _boolean(value: str, field: str, variable: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {'true', '1'}:
        return True
    if normalized in {'false', '0'}:
        return False
    raise ValueError(f'{variable}: {field} debe ser true/false o 1/0; recibido {value!r}')


def load_catalog(path=None) -> list[dict]:
    """Lee y valida el catálogo completo; devuelve booleanos reales.

    La ruta por defecto es ``catalogo_fuentes.csv`` junto a este módulo.
    Una copia externa debe conservar exactamente los 152 predictores y el
    esquema. La comprobación contra metadatos fuente se documenta en notas;
    el lector no necesita acceder a la base ni al target para funcionar.
    """
    source = Path(path) if path is not None else Path(__file__).with_name('catalogo_fuentes.csv')
    with source.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f'Esquema de catálogo inesperado. Se requieren, en orden: {FIELDS}')
        specs = [dict(row) for row in reader]
    if len(specs) != 152:
        raise ValueError(f'El catálogo completo requiere 152 predictores; recibidos {len(specs)}')
    names = [r['variable'] for r in specs]
    if len(set(names)) != 152 or any(not name for name in names):
        raise ValueError('Variables vacías o duplicadas en el catálogo')
    if set(names) != EXPECTED_VARIABLES:
        missing = sorted(EXPECTED_VARIABLES.difference(names))
        extra = sorted(set(names).difference(EXPECTED_VARIABLES))
        raise ValueError(f'Cobertura de fuentes diferente: faltan={missing}, extras={extra}')
    if STRUCTURAL_COLUMNS.intersection(names):
        raise ValueError('ID, foto_mes y target no pertenecen al catálogo de predictores')
    for spec in specs:
        variable = spec['variable']
        if spec['kind'] not in KINDS or spec['history_mode'] not in HISTORY_MODES:
            raise ValueError(f'{variable}: kind/history_mode no admitido')
        for field in ('zero_interpretable', 'signed'):
            spec[field] = _boolean(spec[field], field, variable)
        if not spec['subtype'] or not spec['family'] or not spec['unit']:
            raise ValueError(f'{variable}: subtype/family/unit incompleto')
        expected = {'category':'nominal', 'relative_date':'relative_date', 'clock':'clock'}
        if spec['kind'] in expected and spec['history_mode'] != expected[spec['kind']]:
            raise ValueError(f'{variable}: combinación kind/history_mode incompatible')
        if spec['kind'] == 'numeric' and spec['history_mode'] in {'nominal','relative_date','clock'}:
            raise ValueError(f'{variable}: history_mode incompatible con numeric')
        if spec['history_mode'] == 'nonnegative_flow' and spec['signed']:
            raise ValueError(f'{variable}: flujo nonnegative marcado signed')
    return specs


def make_specs() -> list[dict]:
    """Alias sin efectos laterales para obtener el catálogo predeterminado."""
    return load_catalog()


__all__ = ['load_catalog', 'make_specs', 'FIELDS', 'KINDS', 'HISTORY_MODES']
