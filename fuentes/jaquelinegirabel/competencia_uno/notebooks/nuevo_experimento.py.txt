"""Crea un notebook de experimento a partir de la plantilla primerComp_001.ipynb.

Copia la plantilla, fija los flags, le pone el numero siguiente y lo anota en EXPERIMENTOS.md.
Asi todos los notebooks de experimento tienen exactamente el mismo codigo y solo cambian los flags.

Uso (desde la carpeta competencia_uno/):
    .venv/bin/python notebooks/nuevo_experimento.py --espacio it01_bordes
    .venv/bin/python notebooks/nuevo_experimento.py --espacio it01_bordes --meses-train 202103 202104 202105 --mes-test 202106
    .venv/bin/python notebooks/nuevo_experimento.py --espacio it01_bordes --dataset extendido --sin-id --trials 100
    .venv/bin/python notebooks/nuevo_experimento.py --espacio it01_bordes --undersampling 0.1
    .venv/bin/python notebooks/nuevo_experimento.py --espacio it01_bordes --clase-objetivo baja1y2 --metrica-optuna franja

Sin --meses-train / --mes-test se usa el esquema de clase (train 202103, test 202105).
Sin --trials se usa config.N_TRIALS.

Resultado: notebooks/primerComp_<NNN>_<experimento>.ipynb, listo para correr completo.
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

import nbformat as nbf

BASE_DIR = Path(__file__).resolve().parent
COMP_DIR = BASE_DIR.parent
if str(COMP_DIR) not in sys.path:
    sys.path.insert(0, str(COMP_DIR))

from comp import config
from comp.experimento import Experimento

PLANTILLA = BASE_DIR / 'primerComp_001.ipynb'
REGISTRO = COMP_DIR / 'EXPERIMENTOS.md'


def siguiente_numero():
    numeros = [int(m.group(1)) for p in BASE_DIR.glob('primerComp_*.ipynb')
               if (m := re.match(r'primerComp_(\d{3})', p.name))]
    return max(numeros) + 1


def fijar_flag(fuente, nombre, valor):
    patron = rf'^{nombre} = .*$'
    if not re.search(patron, fuente, flags=re.M):
        raise ValueError(f'No encontre el flag {nombre} en la plantilla')
    return re.sub(patron, f'{nombre} = {valor!r}', fuente, count=1, flags=re.M)


def notebook_desde_plantilla(exp, trials, encabezado):
    """Plantilla con los flags del experimento, sin salidas y con un encabezado arriba."""
    flags = {
        'DATASET': exp.dataset,
        'ESPACIO_BUSQUEDA': exp.espacio,
        'MESES_TRAIN': list(exp.meses_train),
        'MES_TEST': exp.mes_test,
        'DROP_NUMERO_CLIENTE': exp.drop_numero_cliente,
        'UNDERSAMPLING': exp.undersampling,
        'CLASE_OBJETIVO': exp.clase_objetivo,
        'METRICA_OPTUNA': exp.metrica_optuna,
        'N_TRIALS': trials,
    }
    nb = nbf.read(PLANTILLA, as_version=4)
    celda_config = next(c for c in nb.cells if c.cell_type == 'code' and 'CONFIGURACIÓN' in c.source)
    for nombre, valor in flags.items():
        celda_config.source = fijar_flag(celda_config.source, nombre, valor)
    # El trial elegido a mano es de cada experimento: una copia nueva empieza en automatico.
    # Estos dos settings viven en la celda del modelo elegido, no en la de configuracion.
    celda_modelo = next(c for c in nb.cells if c.cell_type == 'code' and 'TRIAL_ELEGIDO' in c.source and 'es_original' in c.source)
    celda_modelo.source = fijar_flag(celda_modelo.source, 'TRIAL_ELEGIDO', None)
    celda_modelo.source = fijar_flag(celda_modelo.source, 'CRITERIO_ELEGIDO', 'semillas')
    for celda in nb.cells:
        if celda.cell_type == 'code':
            celda.outputs = []
            celda.execution_count = None
    nb.cells.insert(0, nbf.v4.new_markdown_cell(encabezado))
    return nb


def fila_registro(numero, nombre_notebook, exp, trials):
    si_no = lambda x: 'sí' if x else 'no'
    train = ', '.join(map(str, exp.meses_train))
    us = 'no' if exp.undersampling is None else f'{exp.undersampling:.0%}'
    extra = ''
    if exp.clase_objetivo != 'baja2' or exp.metrica_optuna != 'umbral':
        extra = f' (clase {exp.clase_objetivo}, Optuna con {exp.metrica_optuna})'
    return (f"| {numero:03d} | `{nombre_notebook}` | {exp.dataset} | {exp.espacio} | {train} | {exp.mes_test} "
            f"| {si_no(exp.drop_numero_cliente)} | {us} | {trials if trials is not None else config.N_TRIALS} | Por correr{extra} |\n")


def agregar_al_registro(fila):
    """Agrega la fila al final de la primera tabla de EXPERIMENTOS.md."""
    lineas = REGISTRO.read_text(encoding='utf-8').splitlines(keepends=True)
    inicio = next(i for i, l in enumerate(lineas) if l.startswith('|'))
    fin = next((i for i in range(inicio, len(lineas)) if not lineas[i].startswith('|')), len(lineas))
    lineas.insert(fin, fila)
    REGISTRO.write_text(''.join(lineas), encoding='utf-8')


def crear(espacio, meses_train=None, mes_test=None, sin_id=False, dataset='final', trials=None, undersampling=None,
          clase_objetivo='baja2', metrica_optuna='umbral'):
    exp = Experimento(
        espacio=espacio,
        meses_train=tuple(meses_train) if meses_train else (config.MES_TRAIN,),
        mes_test=mes_test or config.MES_TEST,
        drop_numero_cliente=sin_id,
        dataset=dataset,
        undersampling=undersampling,
        clase_objetivo=clase_objetivo,
        metrica_optuna=metrica_optuna,
    )

    existentes = list(BASE_DIR.glob(f'primerComp_*_{exp.tag}.ipynb'))
    if existentes:
        raise SystemExit(f'Ya existe un notebook para {exp.tag}: {existentes[0].name}')

    numero = siguiente_numero()
    destino = BASE_DIR / f'primerComp_{numero:03d}_{exp.tag}.ipynb'
    hoy = datetime.date.today().isoformat()
    nb = notebook_desde_plantilla(exp, trials, (
        f"> **Experimento {numero:03d}: `{exp.tag}`**, creado el {hoy} desde `primerComp_001.ipynb` "
        f"con `nuevo_experimento.py`. No cambiar los flags acá: para otra combinación, crear otro experimento."
    ))
    nbf.write(nb, destino)
    agregar_al_registro(fila_registro(numero, destino.name, exp, trials))

    for aviso in exp.avisos():
        print('AVISO:', aviso)
    print('Creado', destino.name)
    return destino


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--espacio', required=True, help='nombre de un espacio de comp/optimizacion_optuna.py')
    parser.add_argument('--meses-train', type=int, nargs='+', default=None,
                        help=f'meses de train (por defecto {config.MES_TRAIN})')
    parser.add_argument('--mes-test', type=int, default=None, help=f'mes de test (por defecto {config.MES_TEST})')
    parser.add_argument('--sin-id', action='store_true', help='no usar numero_de_cliente como variable')
    parser.add_argument('--dataset', default='final', help=f'dataset de config.DATASETS: {list(config.DATASETS)}')
    parser.add_argument('--undersampling', type=float, default=None,
                        help='fraccion de no-BAJA+2 que se queda en el train, ej. 0.1 (por defecto: todos)')
    parser.add_argument('--clase-objetivo', default='baja2', choices=list(config.CLASES_OBJETIVO),
                        help='baja2 (modelo A, por defecto) o baja1y2 (modelo B)')
    parser.add_argument('--metrica-optuna', default='umbral', choices=config.METRICAS_OPTUNA,
                        help='como puntua Optuna: umbral (p >= 0.025, por defecto), umbral_ajustado o franja')
    parser.add_argument('--trials', type=int, default=None,
                        help=f'trials de Optuna (por defecto config.N_TRIALS = {config.N_TRIALS})')
    args = parser.parse_args()
    if args.trials is not None and args.trials < 1:
        parser.error('--trials tiene que ser mayor que 0')
    crear(args.espacio, args.meses_train, args.mes_test, args.sin_id, args.dataset, args.trials, args.undersampling,
          args.clase_objetivo, args.metrica_optuna)
