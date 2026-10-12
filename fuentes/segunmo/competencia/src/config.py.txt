"""Constantes compartidas de la competencia."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATA = RAIZ / "data"
CSV_CRUDO = DATA / "competencia_01_crudo.csv"
CSV = DATA / "competencia_01.csv"          # con clase_ternaria
PARQUET = DATA / "competencia_01.parquet.gzip"  # misma tabla en parquet (5x más liviano y rápido); la usa data.py

ID_COL = "numero_de_cliente"
MES_COL = "foto_mes"
TARGET_COL = "clase_ternaria"
POSITIVO = "BAJA+2"

# Campaña de retención
GANANCIA_ACIERTO = 1_072_500   # estimular a un BAJA+2
COSTO_ESTIMULO = 27_500        # estimular a cualquier otro
# Punto de equilibrio: p* = costo / (ganancia + costo) = 0.025
UMBRAL = COSTO_ESTIMULO / (GANANCIA_ACIERTO + COSTO_ESTIMULO)

# Semillas propias (5 primos, 100003 < p < 999983; Check-in de Zulip). Usar SIEMPRE estas.
SEMILLAS: list[int] = [852583, 771227, 676057, 482687, 399221]

# Semillas DERIVADAS de la primera semilla propia, para tener más réplicas (semilleríos del final y experimentos con 20 semillas).
# Se generaron UNA vez con `np.random.RandomState(SEMILLAS[0]).randint(100_003, 999_983, size=25)` y se listan literalmente acá para que el repo
# no dependa de ningún generador. NO son todas primos (solo 133559, 131321 y 514793 lo son) y NO figuran en el check-in de Zulip: si la cátedra
# exige usar únicamente las 5 semillas registradas, hay que reentrenar con SEMILLAS solas (el submit cambia). La aserción de abajo
# verifica que la lista coincide con su generador.
SEMILLAS_DERIVADAS: list[int] = [121109, 292131, 133559, 956184, 853814, 796055, 407085, 202811, 536784, 597474, 188259, 131321, 359659,
                                 119369, 514793, 913528, 771958, 818272, 207823, 363952, 659964, 838620, 552606, 777618, 174440]
SEMILLAS_20: list[int] = SEMILLAS + SEMILLAS_DERIVADAS[:15]      # las 20 semillas de los experimentos de validación
SEMILLAS_FINAL: list[int] = SEMILLAS + SEMILLAS_DERIVADAS        # hasta 30 semillas (017 usa las 30)


def semillas(n: int) -> list[int]:
    """Las primeras n semillas de SEMILLAS_FINAL: las 5 propias y, si n > 5, las derivadas en el orden listado."""
    if not 1 <= n <= len(SEMILLAS_FINAL):
        raise ValueError(f"n debe estar entre 1 y {len(SEMILLAS_FINAL)}")
    return SEMILLAS_FINAL[:n]


def _verificar_semillas() -> None:
    import numpy as np
    generadas = [int(x) for x in np.random.RandomState(SEMILLAS[0]).randint(100_003, 999_983, size=len(SEMILLAS_DERIVADAS))]
    assert generadas == SEMILLAS_DERIVADAS, "SEMILLAS_DERIVADAS no coincide con su generador"


_verificar_semillas()

# Primera Competencia: se predice el último mes del dataset (sin clase conocida).
MES_SCORING = 202108

# 202105: `ccajas_depositos` viene rota (todos los valores en 0, el profe lo confirmó). Con True se pone NA solo en ese mes.
# Default False para que los experimentos anteriores (001-007) sigan siendo reproducibles. 008a no mostró efecto medible (la variable es casi toda ceros), pero se aplica por corrección de
# datos: los scripts de 008 en adelante (y todos los del final) lo ponen en True al empezar (`config.CORREGIR_CCAJAS = True`).
CORREGIR_CCAJAS = False
