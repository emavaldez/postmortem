"""Arma el train y el test de un experimento.

- Train: los meses de experimento.meses_train (todas sus filas juntas).
- Test: experimento.mes_test, que solo se usa para medir la ganancia.

Regla M - 2 (recomendada, no obligatoria): la BAJA+2 de un mes se conoce recien dos meses
despues. Para que el test copie la situacion real de agosto, los meses de train deberian ser
como mucho mes_test - 2. Si no, el experimento muestra un AVISO (ver Experimento.avisos).
"""
import lightgbm as lgb

from . import config
from .datos import separar


def sumar_meses(mes, n):
    """sumar_meses(202105, -2) -> 202103. Funciona cruzando anios."""
    anio, m = divmod(mes, 100)
    total = anio * 12 + (m - 1) + n
    return (total // 12) * 100 + total % 12 + 1


def etiqueta_entrenamiento(y_baja2, clase, clase_objetivo='baja2'):
    """El 1 con el que se entrena: BAJA+2 (modelo A) o BAJA+1 + BAJA+2 (modelo B)."""
    if clase_objetivo == 'baja2':
        return y_baja2
    return clase.isin(config.CLASES_OBJETIVO[clase_objetivo]).astype('int64')


def umbral_de_decision(y_baja2, y_entrenamiento):
    """p >= UMBRAL / s, con s = BAJA+2 / positivos de entrenamiento.

    Si el modelo predice "BAJA+1 o BAJA+2", solo una parte s de esos positivos paga; contactar
    conviene cuando la chance de BAJA+2 (~ s * p) es >= 0.025. En el modelo A, s = 1: da 0.025.
    """
    s = y_baja2.sum() / y_entrenamiento.sum()
    return config.UMBRAL / s


def armar_particion(data, meses_de_train, mes_test, columnas_excluidas=(), clase_objetivo='baja2'):
    """Train con meses_de_train, test con mes_test. Devuelve un dict con todo lo necesario.

    y_train es la etiqueta con la que se entrena (segun clase_objetivo); y_train_baja2 e y_test
    son siempre los BAJA+2 reales, con los que se cuenta la ganancia.
    """
    # Un mes sin BAJA+2 conocida (ej. 202107, 202108) quedaria con todo 0 sin avisar
    for mes in list(meses_de_train) + [mes_test]:
        if data.loc[data['foto_mes'] == mes, 'clase_ternaria'].isna().any():
            raise ValueError(f'El mes {mes} no tiene la clase completa (BAJA+2 desconocida): no sirve para train ni test')
    X_train, y_baja2_train, clase_train = separar(data, meses_de_train, columnas_excluidas)
    y_train = etiqueta_entrenamiento(y_baja2_train, clase_train, clase_objetivo)
    X_test, y_test, clase_test = separar(data, [mes_test], columnas_excluidas)
    return {
        'meses_train': list(meses_de_train),
        'mes_test': mes_test,
        'clase_objetivo': clase_objetivo,
        'X_train': X_train,
        'y_train': y_train,
        'y_train_baja2': y_baja2_train,
        'umbral': umbral_de_decision(y_baja2_train, y_train),
        'train_lgb': lgb.Dataset(X_train, label=y_train),
        'X_test': X_test,
        'y_test': y_test,
        'y_test_objetivo': etiqueta_entrenamiento(y_test, clase_test, clase_objetivo),
        'clase_test': clase_test,
    }


def armar_particiones(data, experimento):
    """{mes_test: particion}. Hay un solo mes de test; se devuelve como dict para que el resto
    del codigo (modelos, ensamble, graficos) lo recorra igual."""
    return {
        experimento.mes_test: armar_particion(
            data, experimento.meses_train, experimento.mes_test, experimento.columnas_excluidas,
            experimento.clase_objetivo)
    }


def describir(particiones):
    for mes, p in particiones.items():
        print(f"Test {mes} ({p['y_test'].sum()} BAJA+2 de {len(p['y_test'])}) <- "
              f"train {p['meses_train']} ({p['y_train_baja2'].sum()} BAJA+2 de {len(p['y_train'])})")
        if p.get('clase_objetivo', 'baja2') != 'baja2':
            print(f"  se entrena con {config.CLASES_OBJETIVO[p['clase_objetivo']]} = 1: {p['y_train'].sum()} positivos "
                  f"| umbral de decision p >= {p['umbral']:.4f}")
