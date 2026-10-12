"""Corre un experimento completo desde la terminal: lo mismo que hacen las notebooks primerComp_*,
sin graficos. Los parametros se configuran en CONFIG (abajo) o por linea de comandos.

Pasos (los mismos de la notebook):
  1. datos y train/test
  2. Optuna (solo corre los trials que faltan)
  3. mejor trial, top 3 y prueba de semillas
  4. modelo elegido (automatico o a mano) y sus metricas en el mes de test, con ensamble
  5. ensayo: reentrenar con otros meses y medir en otro mes (opcional)
  6. prediccion de agosto y archivo de submit (en la carpeta de main.py)

Todo lo ya calculado se carga del disco (db/, modelos/, resultados/), igual que en las notebooks.

Uso (desde la carpeta competencia_uno/):
    .venv/bin/python main.py                      # usa CONFIG tal cual
    .venv/bin/python main.py --corte umbral       # cambia un parametro
    .venv/bin/python main.py --sin-submit         # no guarda el archivo de submit
    .venv/bin/python main.py --comparar submits/<archivo>.csv   # compara el submit con otro archivo
    .venv/bin/python main.py --help
"""
import argparse
import os
import sys
from pathlib import Path

# ============================ CONFIGURACIÓN ============================
# Valores de la notebook 010: reproducen el submit
# it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optumbral_ajustado_trial49_top12058_20261007_182001.csv
CONFIG = {
    # Dataset: 'final' (195 columnas) o 'extendido' (+ inflación, lags y deltas). Ver FEATURES.md
    'DATASET': 'extendido',
    # Espacio de búsqueda de Optuna (comp/optimizacion_optuna.py, ESPACIOS): 'it00_z601' o 'it01_bordes'
    'ESPACIO_BUSQUEDA': 'it01_bordes',
    # Meses de train (Optuna elige los parámetros solo con estos) y mes de test (solo para medir)
    'MESES_TRAIN': [202103, 202104, 202105],
    'MES_TEST': 202106,
    # True: numero_de_cliente no se usa como variable
    'DROP_NUMERO_CLIENTE': False,
    # Fracción de la clase 0 que se queda en el train (None: todos)
    'UNDERSAMPLING': 0.1,
    # 'baja2' (modelo A) o 'baja1y2' (modelo B: BAJA+1 y BAJA+2 = 1)
    'CLASE_OBJETIVO': 'baja1y2',
    # Cómo puntúa Optuna: 'umbral' (p >= 0.025), 'umbral_ajustado' (p >= 0.025 / s) o 'franja' (top 5% a 9%)
    'METRICA_OPTUNA': 'umbral_ajustado',
    # Trials de Optuna (None: config.N_TRIALS)
    'N_TRIALS': None,
    # Modelo elegido: un número de trial a mano, o None para elegir según CRITERIO_ELEGIDO
    'TRIAL_ELEGIDO': None,
    # 'semillas' (caja más alta y concentrada, mayor Q1) u 'optuna' (mejor trial de Optuna)
    'CRITERIO_ELEGIDO': 'semillas',
    # Ensayo: reentrenar el modelo elegido con estos meses y medir en este mes (None: no se hace)
    'MESES_TRAIN_EXTRA': [202103, 202104, 202105],
    'MES_TEST_EXTRA': 202106,
    # Predicción final
    'MESES_TRAIN_FINAL': [202103, 202104, 202105, 202106],
    'MES_PREDICCION': 202108,
    # 'umbral' (p >= umbral de decisión) o una cantidad de clientes, ej. 12058
    'CORTE': 12058,
    'GUARDAR_SUBMIT': True,
}
# =======================================================================


def lista_de_meses(texto):
    return [int(m) for m in texto.replace(',', ' ').split()]


def parsear_argumentos(config):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--dataset')
    p.add_argument('--espacio', dest='ESPACIO_BUSQUEDA')
    p.add_argument('--meses-train', type=int, nargs='+')
    p.add_argument('--mes-test', type=int)
    p.add_argument('--sin-id', action='store_true', default=None, help='no usar numero_de_cliente como variable')
    p.add_argument('--undersampling', type=float, help='fracción de la clase 0 en el train; 0 = sin undersampling')
    p.add_argument('--clase-objetivo', choices=['baja2', 'baja1y2'])
    p.add_argument('--metrica-optuna', choices=['umbral', 'umbral_ajustado', 'franja'])
    p.add_argument('--trials', type=int, dest='N_TRIALS')
    p.add_argument('--trial-elegido', type=int)
    p.add_argument('--criterio-elegido', choices=['semillas', 'optuna'])
    p.add_argument('--meses-train-extra', type=int, nargs='+')
    p.add_argument('--mes-test-extra', type=int)
    p.add_argument('--sin-ensayo', action='store_true', help='no hacer el ensayo con otros meses')
    p.add_argument('--meses-train-final', type=int, nargs='+')
    p.add_argument('--mes-prediccion', type=int)
    p.add_argument('--corte', help="'umbral' o una cantidad de clientes")
    p.add_argument('--sin-submit', action='store_true', help='no guardar el archivo de submit')
    p.add_argument('--comparar', type=Path, help='submit (.csv) con el que comparar el resultado')
    p.add_argument('--salidas', type=Path,
                   help='carpeta para db/, modelos/, resultados/ y submits/ (por defecto clusters/)')
    a = p.parse_args()

    cfg = dict(config)
    for clave, valor in [
        ('DATASET', a.dataset), ('ESPACIO_BUSQUEDA', a.ESPACIO_BUSQUEDA), ('MESES_TRAIN', a.meses_train),
        ('MES_TEST', a.mes_test), ('CLASE_OBJETIVO', a.clase_objetivo), ('METRICA_OPTUNA', a.metrica_optuna),
        ('N_TRIALS', a.N_TRIALS), ('TRIAL_ELEGIDO', a.trial_elegido), ('CRITERIO_ELEGIDO', a.criterio_elegido),
        ('MESES_TRAIN_EXTRA', a.meses_train_extra), ('MES_TEST_EXTRA', a.mes_test_extra),
        ('MESES_TRAIN_FINAL', a.meses_train_final), ('MES_PREDICCION', a.mes_prediccion),
    ]:
        if valor is not None:
            cfg[clave] = valor
    if a.sin_id:
        cfg['DROP_NUMERO_CLIENTE'] = True
    if a.undersampling is not None:
        cfg['UNDERSAMPLING'] = a.undersampling or None
    if a.sin_ensayo:
        cfg['MESES_TRAIN_EXTRA'] = None
    if a.corte is not None:
        cfg['CORTE'] = a.corte if a.corte == 'umbral' else int(a.corte)
    if a.sin_submit:
        cfg['GUARDAR_SUBMIT'] = False
    return cfg, a.comparar, a.salidas


def titulo(texto):
    print(f"\n{'=' * 10} {texto} {'=' * max(0, 70 - len(texto))}", flush=True)


def main():
    cfg, comparar, salidas = parsear_argumentos(CONFIG)
    if salidas is not None:
        os.environ['COMP_SALIDAS_DIR'] = str(salidas.resolve())  # antes de importar comp

    # los modulos se importan aca para que COMP_SALIDAS_DIR ya este definido
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import numpy as np
    import pandas as pd
    from comp import config, datos, ensamble, entrega, metricas, modelos, optimizacion_optuna
    from comp.experimento import Experimento
    from comp.particiones import armar_particion, armar_particiones, describir, sumar_meses

    pd.set_option('display.width', 200)
    pd.set_option('display.max_columns', 30)

    # ---------------------------------------------------------------- 1. experimento y datos
    titulo('Experimento')
    exp = Experimento(
        espacio=cfg['ESPACIO_BUSQUEDA'],
        meses_train=tuple(cfg['MESES_TRAIN']),
        mes_test=cfg['MES_TEST'],
        drop_numero_cliente=cfg['DROP_NUMERO_CLIENTE'],
        dataset=cfg['DATASET'],
        undersampling=cfg['UNDERSAMPLING'],
        clase_objetivo=cfg['CLASE_OBJETIVO'],
        metrica_optuna=cfg['METRICA_OPTUNA'],
    )
    exp.describir()
    semillas = config.generar_semillas(exp.semilla)
    n_trials = cfg['N_TRIALS'] if cfg['N_TRIALS'] is not None else config.N_TRIALS
    print(f'  trials de Optuna: {n_trials} | semillas: {config.N_SEMILLAS}')

    titulo('Datos')
    data = datos.agregar_clase_binaria(datos.cargar_datos(exp.dataset))
    particiones = armar_particiones(data, exp)
    describir(particiones)

    # ---------------------------------------------------------------- 2. Optuna
    titulo('Optuna')
    study = optimizacion_optuna.cargar_estudio(exp)
    objective = optimizacion_optuna.crear_objetivo(exp, particiones, semillas[0])
    study = optimizacion_optuna.optimizar_hasta(study, objective, n_trials_total=n_trials)

    # ---------------------------------------------------------------- 3. mejor trial, top 3, semillas
    titulo('Mejor trial de Optuna')
    best = study.best_trial
    arboles_best = modelos.cantidad_arboles(exp, best.user_attrs['best_iter'])
    params_best = optimizacion_optuna.armar_params(best.params, semillas[0], exp.espacio)
    print(f"Mejor trial: {best.number} | best_iter en Optuna: {best.user_attrs['best_iter']} | árboles usados: {arboles_best}")
    for mes, p in particiones.items():
        modelo_best = modelos.entrenar_o_cargar(
            exp.modelos_dir / f'lgb_mejor_trial_{mes}.txt', params_best, modelos.datos_train(p, exp, semillas[0]), arboles_best)
        print(f"Ganancia LGBM en {mes}:", modelos.ganancia_experimento(modelos.predecir(modelo_best, p['X_test'], exp), p, exp))

    titulo('Top 3 trials, medidos en el mes de test')
    df_top3 = modelos.evaluar_top_trials(optimizacion_optuna.top_trials(study, 3), particiones, exp, semillas[0])
    print(df_top3.to_string(index=False))

    titulo(f'Prueba de semillas ({config.N_SEMILLAS})')
    df_semillas = modelos.evaluar_semillas(df_top3, particiones, exp, semillas[:config.N_SEMILLAS])
    estadisticas = modelos.estadisticas_semillas(df_semillas)
    print((estadisticas / 1e6).round(2).to_string())

    # ---------------------------------------------------------------- 4. modelo elegido
    titulo('Modelo elegido')
    if exp.es_original:
        params_elegido = {
            **config.PARAMS_FIJOS,
            'num_leaves': 16,
            'learning_rate': 0.019868,
            'min_data_in_leaf': 816,
            'feature_fraction': 0.277155,
            'bagging_fraction': 0.634130,
            'seed': semillas[0],
            'verbose': -1,
        }
        arboles_elegido = config.NUM_BOOST_ROUND
        id_elegido = ''  # nombres de archivo del notebook original
        trial_txt = 'fijo'
        print('Modelo elegido: parámetros fijos del notebook original')
    else:
        if cfg['TRIAL_ELEGIDO'] is not None:
            t = study.trials[cfg['TRIAL_ELEGIDO']]
            if t.state.name != 'COMPLETE':
                raise ValueError(f"El trial {cfg['TRIAL_ELEGIDO']} no terminó (estado {t.state.name})")
            fila = {**t.params, 'trial': t.number,
                    'best_iter': modelos.cantidad_arboles(exp, t.user_attrs.get('best_iter'))}
            como = 'a mano'
        elif cfg['CRITERIO_ELEGIDO'] == 'semillas':
            fila = modelos.elegir_por_semillas(df_top3, estadisticas)
            como = 'semillas'
        elif cfg['CRITERIO_ELEGIDO'] == 'optuna':
            fila = df_top3[df_top3['orden'] == 1].iloc[0]
            como = 'optuna'
        else:
            raise ValueError(f"CRITERIO_ELEGIDO tiene que ser 'semillas' u 'optuna', no {cfg['CRITERIO_ELEGIDO']!r}")
        params_elegido = optimizacion_optuna.armar_params(fila, semillas[0], exp.espacio)
        arboles_elegido = int(fila['best_iter'])
        id_elegido = f"_trial{int(fila['trial'])}"
        trial_txt = str(int(fila['trial']))
        print(f"Modelo elegido ({como}): trial {trial_txt} ({arboles_elegido} árboles)")

    comparacion = []
    for mes, p in particiones.items():
        modelo = modelos.entrenar_o_cargar(
            exp.modelos_dir / f'lgb_elegido{id_elegido}_{mes}.txt', params_elegido,
            modelos.datos_train(p, exp, semillas[0]), arboles_elegido)
        y_una = modelos.predecir(modelo, p['X_test'], exp)
        y_ens = ensamble.predecir_promedio_semillas(
            params_elegido, arboles_elegido, p['train_lgb'], p['X_test'], semillas[:config.N_SEMILLAS],
            archivo=exp.resultados_dir / f'pred_ensamble{id_elegido}_{mes}_{config.N_SEMILLAS}semillas.npy',
            y_train=p['y_train'], undersampling=exp.undersampling,
        )
        for nombre, y in [('una semilla', y_una), (f'ensamble {config.N_SEMILLAS} semillas', y_ens)]:
            comparacion.append({'mes': mes, 'modelo': nombre, 'ks': metricas.ks(y, p['y_test'])['ks'],
                                'prob_media': float(np.mean(y)),
                                **metricas.umbral_vs_mejor_corte(y, p['y_test'], umbral=p['umbral'], con_franja=True)})
    titulo(f"Mes de test: p >= umbral de decisión contra el mejor corte (ganancias en millones)")
    tabla = pd.DataFrame(comparacion)
    for c in ['ganancia_umbral', 'ganancia_mejor_corte', 'perdida', 'ganancia_franja']:
        tabla[c] = (tabla[c] / 1e6).round(1)
    print(tabla.round({'ks': 4, 'prob_media': 4, 'p_mejor_corte': 4, 'perdida_pct': 1}).to_string(index=False))

    # ---------------------------------------------------------------- 5. ensayo con otros meses
    if cfg['MESES_TRAIN_EXTRA']:
        titulo(f"Ensayo: train {cfg['MESES_TRAIN_EXTRA']} -> test {cfg['MES_TEST_EXTRA']}")
        for m in cfg['MESES_TRAIN_EXTRA']:
            if m > sumar_meses(cfg['MES_TEST_EXTRA'], -2):
                print(f"AVISO: train {m} rompe la regla M - 2 (su BAJA+2 se conoce recién en {sumar_meses(m, 2)}, "
                      f"después de {cfg['MES_TEST_EXTRA']}): la ganancia puede ser optimista.")
        if cfg['MESES_TRAIN_EXTRA'] == cfg['MESES_TRAIN'] and cfg['MES_TEST_EXTRA'] == cfg['MES_TEST']:
            p_extra = particiones[cfg['MES_TEST']]
        else:
            del particiones
            datos.liberar_memoria()
            p_extra = armar_particion(data, cfg['MESES_TRAIN_EXTRA'], cfg['MES_TEST_EXTRA'], exp.columnas_excluidas,
                                      exp.clase_objetivo)
        print(f"Train ({p_extra['y_train'].sum()} positivos de {len(p_extra['y_train'])}) -> "
              f"test ({p_extra['y_test'].sum()} BAJA+2 de {len(p_extra['y_test'])})")
        sufijo = 'train' + '-'.join(map(str, cfg['MESES_TRAIN_EXTRA'])) + f"_test{cfg['MES_TEST_EXTRA']}"
        modelo_extra = modelos.entrenar_o_cargar(
            exp.modelos_dir / f'lgb_elegido{id_elegido}_{sufijo}.txt', params_elegido,
            modelos.datos_train(p_extra, exp, semillas[0]), arboles_elegido)
        y_una = modelos.predecir(modelo_extra, p_extra['X_test'], exp)
        y_ens_extra = ensamble.predecir_promedio_semillas(
            params_elegido, arboles_elegido, p_extra['train_lgb'], p_extra['X_test'], semillas[:config.N_SEMILLAS],
            archivo=exp.resultados_dir / f'pred_ensamble{id_elegido}_{sufijo}_{config.N_SEMILLAS}semillas.npy',
            y_train=p_extra['y_train'], undersampling=exp.undersampling,
        )
        filas = []
        for nombre, y in [('una semilla', y_una), (f'ensamble {config.N_SEMILLAS} semillas', y_ens_extra)]:
            filas.append({'modelo': nombre, 'ks': metricas.ks(y, p_extra['y_test'])['ks'],
                          **metricas.umbral_vs_mejor_corte(y, p_extra['y_test'], umbral=p_extra['umbral'], con_franja=True)})
        tabla_extra = pd.DataFrame(filas)
        for c in ['ganancia_umbral', 'ganancia_mejor_corte', 'perdida', 'ganancia_franja']:
            tabla_extra[c] = (tabla_extra[c] / 1e6).round(1)
        print(tabla_extra.round({'ks': 4, 'p_mejor_corte': 4, 'perdida_pct': 1}).to_string(index=False))
        del p_extra
    if 'particiones' in locals():
        del particiones
    datos.liberar_memoria()

    # ---------------------------------------------------------------- 6. predicción y submit
    titulo(f"Predicción de {cfg['MES_PREDICCION']}")
    pred = entrega.armar_prediccion(data, cfg['MESES_TRAIN_FINAL'], cfg['MES_PREDICCION'], exp.columnas_excluidas,
                                    exp.clase_objetivo)
    del data
    datos.liberar_memoria()
    print(f"Train {cfg['MESES_TRAIN_FINAL']} ({pred['y_train'].sum()} positivos de {len(pred['y_train'])}) -> "
          f"predicción {cfg['MES_PREDICCION']} ({len(pred['ids'])} clientes)")
    sufijo_final = 'train' + '-'.join(map(str, cfg['MESES_TRAIN_FINAL'])) + f"_pred{cfg['MES_PREDICCION']}"
    y_pred_final = entrega.predecir(
        params_elegido, arboles_elegido, pred, semillas[:config.N_SEMILLAS], undersampling=exp.undersampling,
        archivo=exp.resultados_dir / f'pred_ensamble{id_elegido}_{sufijo_final}_{config.N_SEMILLAS}semillas.npy',
    )
    print(f"Probabilidad media predicha: {y_pred_final.mean():.4f} | umbral de decisión: p >= {pred['umbral']:.4f}")
    print(entrega.resumen_cortes(y_pred_final, umbral=pred['umbral']).round(4).to_string(index=False))

    corte = cfg['CORTE']
    ids_submit = entrega.clientes_a_contactar(pred['ids'], y_pred_final, corte, umbral=pred['umbral'])
    print(f'Corte {corte!r}: {len(ids_submit)} clientes a estimular')

    if cfg['GUARDAR_SUBMIT']:
        nombre_corte = 'umbral' if corte == 'umbral' else f'top{corte}'
        dir_main = Path(__file__).resolve().parent
        archivo_submit = entrega.guardar_submit(ids_submit, f'{exp.tag}{id_elegido}_{nombre_corte}', carpeta=dir_main)
        entrega.anotar_en_registro(archivo_submit, exp.tag, trial_txt, corte, ids_submit, y_pred_final,
                                   cfg['MESES_TRAIN_FINAL'], carpeta=dir_main)
        print('Submit guardado en', archivo_submit)

    if comparar is not None:
        titulo(f'Comparación con {comparar.name}')
        otros = np.loadtxt(comparar, dtype='int64', ndmin=1)
        iguales = len(otros) == len(ids_submit) and np.array_equal(np.sort(otros), ids_submit)
        print(f'clientes: {len(ids_submit)} (nuevo) | {len(otros)} ({comparar.name})')
        print(f'en común: {len(np.intersect1d(otros, ids_submit))} | '
              f'solo en el nuevo: {len(np.setdiff1d(ids_submit, otros))} | solo en el otro: {len(np.setdiff1d(otros, ids_submit))}')
        print('RESULTADO:', 'IDÉNTICO' if iguales else 'DISTINTO')


if __name__ == '__main__':
    main()
