"""Configuracion de un experimento (los flags del notebook) y donde se guardan sus resultados.

Un experimento entrena con `meses_train` y mide la ganancia en `mes_test`:
- Optuna elige los parametros solo con los meses de train (5 particiones 70/30, como el
  notebook de clase z601). El mes de test no se usa para elegir nada: solo para informar.

Cada combinacion de flags tiene su propio nombre (tag) y sus propias carpetas, para que
nunca se mezclen resultados de experimentos distintos:
    db/<tag>.db, modelos/<tag>/, resultados/<tag>/
La combinacion que reproduce el notebook de clase (espacio 'it00_z601', train 202103,
test 202105, con numero_de_cliente, dataset final) usa el estudio de Optuna de
z601_clases_final_csv.ipynb.
"""
from dataclasses import dataclass

from . import config
from .particiones import sumar_meses
from .optimizacion_optuna import ESPACIOS


@dataclass(frozen=True)
class Experimento:
    espacio: str = 'it01_bordes'               # nombre de un espacio de optimizacion_optuna.ESPACIOS
    meses_train: tuple = (config.MES_TRAIN,)   # meses con los que se entrena (y Optuna elige parametros)
    mes_test: int = config.MES_TEST            # mes donde se mide la ganancia
    drop_numero_cliente: bool = False          # True: numero_de_cliente no se usa como feature
    dataset: str = 'final'                     # nombre de un dataset de config.DATASETS
    undersampling: float = None                # fraccion de la clase 0 que se queda en el train (None: todos)
    clase_objetivo: str = 'baja2'              # 'baja2' (modelo A) o 'baja1y2' (modelo B), ver config.CLASES_OBJETIVO
    metrica_optuna: str = 'umbral'             # como puntua Optuna, ver config.METRICAS_OPTUNA

    def __post_init__(self):
        if self.espacio not in ESPACIOS:
            raise ValueError(f"Espacio '{self.espacio}' no existe. Opciones: {list(ESPACIOS)}")
        if self.dataset not in config.DATASETS:
            raise ValueError(f"Dataset '{self.dataset}' no existe. Opciones: {list(config.DATASETS)}")
        if self.clase_objetivo not in config.CLASES_OBJETIVO:
            raise ValueError(f"Clase objetivo '{self.clase_objetivo}' no existe. Opciones: {list(config.CLASES_OBJETIVO)}")
        if self.metrica_optuna not in config.METRICAS_OPTUNA:
            raise ValueError(f"Metrica '{self.metrica_optuna}' no existe. Opciones: {config.METRICAS_OPTUNA}")
        if self.undersampling is not None and not 0 < self.undersampling < 1:
            raise ValueError(f'undersampling tiene que estar entre 0 y 1 (o None), no {self.undersampling}')
        tardios = [m for m in self.meses_train if m >= self.mes_test]
        if tardios:
            raise ValueError(f'Meses de train {tardios} no son anteriores al mes de test {self.mes_test}')

    def avisos(self):
        """Meses de train que rompen la regla M - 2 (su BAJA+2 usa datos posteriores al mes de test)."""
        limite = sumar_meses(self.mes_test, -2)
        return [
            f'train {m} rompe la regla M - 2: su BAJA+2 se conoce recien en '
            f'{sumar_meses(m, 2)}, despues de {self.mes_test}. '
            f'La ganancia en {self.mes_test} puede ser optimista.'
            for m in self.meses_train if m > limite
        ]

    @property
    def columnas_excluidas(self):
        return ['numero_de_cliente'] if self.drop_numero_cliente else []

    @property
    def es_esquema_clase(self):
        """Train marzo, test mayo: el esquema del notebook de clase."""
        return tuple(self.meses_train) == (config.MES_TRAIN,) and self.mes_test == config.MES_TEST

    @property
    def es_original(self):
        return (self.espacio == 'it00_z601' and self.es_esquema_clase and not self.drop_numero_cliente
                and self.dataset == 'final' and self.undersampling is None
                and self.clase_objetivo == 'baja2' and self.metrica_optuna == 'umbral')

    @property
    def semilla(self):
        """config.SEMILLA, salvo al reproducir el notebook de clase (usa la suya)."""
        return config.SEMILLA_CLASE if self.es_original else config.SEMILLA

    @property
    def tag(self):
        partes = [self.espacio]
        if self.es_esquema_clase:
            partes.append('cv')  # nombre que ya usaban 001, 002 y 004
        else:
            partes.append('train' + '-'.join(str(m) for m in self.meses_train) + f'_test{self.mes_test}')
        if self.drop_numero_cliente:
            partes.append('sinid')
        if self.dataset != 'final':
            partes.append(f'ds{self.dataset}')
        if self.undersampling is not None:
            partes.append(f'us{round(self.undersampling * 100):g}')
        if self.clase_objetivo != 'baja2':
            partes.append(f'clase{self.clase_objetivo}')
        if self.metrica_optuna != 'umbral':
            partes.append(f'opt{self.metrica_optuna}')
        return '_'.join(partes)

    @property
    def storage(self):
        if self.es_original:
            return config.STORAGE_OPTUNA_ORIGINAL
        return f"sqlite:///{config.DB_DIR / (self.tag + '.db')}"

    @property
    def study_name(self):
        return config.STUDY_NAME_ORIGINAL if self.es_original else self.tag

    @property
    def resultados_dir(self):
        d = config.RESULTADOS_DIR / self.tag
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def modelos_dir(self):
        d = config.MODELOS_DIR / self.tag
        d.mkdir(parents=True, exist_ok=True)
        return d

    def describir(self):
        print(f"Experimento: {self.tag}")
        print(f"  dataset: {self.dataset} ({config.DATASETS[self.dataset].name})")
        print(f"  espacio de busqueda: {self.espacio}")
        print(f"  train: {list(self.meses_train)} -> test: {self.mes_test}")
        print(f"  columnas excluidas: {self.columnas_excluidas or 'ninguna'}")
        print(f"  clase objetivo: {self.clase_objetivo} ({' + '.join(config.CLASES_OBJETIVO[self.clase_objetivo])} = 1)")
        print(f"  metrica de Optuna: {self.metrica_optuna}")
        if self.undersampling is None:
            print('  undersampling: no')
        else:
            print(f'  undersampling: se queda el {self.undersampling:.0%} de los no-BAJA+2 en el train '
                  '(cada semilla su muestra; el mes de test se mide con todos)')
        print(f"  Optuna: {self.study_name} en {self.storage}")
        print(f"  semilla: {self.semilla}")
        for aviso in self.avisos():
            print('  AVISO:', aviso)
