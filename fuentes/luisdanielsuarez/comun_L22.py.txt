"""
comun_L22.py — funciones y parámetros compartidos por 02_etapa1_L22.py y 03_etapa2_L22.py (DMEyF, 1ra competencia).

No se ejecuta solo: lo importan los dos scripts de etapa. Debe estar en la misma carpeta que ellos (~/dmeyf).

Contenido:
  - parámetros fijos de LightGBM (los de z495 de Pasquini + feature_fraction_bynode de las recomendaciones),
  - configuración de la bayesiana (3 hiperparámetros, rangos de Pasquini, 10 trials aleatorios, semilla 878443),
  - bayesiana reproducible aunque se interrumpa (cada trial depende solo de su número y de los anteriores),
  - entrenamiento de N modelos con N semillas, reanudable (guarda cada predicción al terminar),
  - utilidades de carga, ganancia, respaldo al bucket.
"""
import gc
import json
import os
import shutil
import subprocess
import time
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.metrics import roc_auc_score

try:                                    # solo lo usa la bayesiana (L22 no la corre)
    import optuna
except ImportError:
    optuna = None

warnings.filterwarnings("ignore", message="Overriding the parameters from Reference Dataset")

VOLUMEN = "L22"
BUCKET = "gs://luisdsuarez_buckito2026"
SEMILLAS = [878443, 455471, 178447, 235397, 409027]       # asignadas; nunca 42


def semillas_n(n):
    """Las 5 asignadas + adicionales deterministas (misma función que L13). Nunca 42."""
    extra, x = [], 500009
    while len(SEMILLAS) + len(extra) < n:
        x += 7919
        if x != 42 and x not in SEMILLAS:
            extra.append(x)
    out = (SEMILLAS + extra)[:n]
    assert 42 not in out and len(set(out)) == len(out)
    return out


# ---------------------------------------------------------------------------
# Hiperparámetros FIJOS (z495 + feature_fraction_bynode). num_iterations, num_leaves y
# min_sum_hessian_in_leaf los pone la bayesiana. Sin early stopping, sin undersampling, sin pesos.
# ---------------------------------------------------------------------------
PARAMS_FIJOS = dict(
    boosting="gbdt", objective="binary", metric="auc",
    first_metric_only=False, boost_from_average=True, force_row_wise=True, deterministic=True,
    verbosity=-1,
    max_depth=-1, min_gain_to_split=0.0, lambda_l1=0.0, lambda_l2=0.0,
    max_bin=31,
    bagging_fraction=1.0, pos_bagging_fraction=1.0, neg_bagging_fraction=1.0,
    is_unbalance=False, scale_pos_weight=1.0,
    drop_rate=0.1, max_drop=50, skip_drop=0.5,
    extra_trees=False,
    min_data_in_leaf=0,
    feature_fraction=0.50,
    feature_fraction_bynode=0.20,
    learning_rate=0.005,
    feature_pre_filter=False,
)
PARAMS_DATASET = dict(max_bin=31, feature_pre_filter=False, min_data_in_leaf=0, verbosity=-1)

# Configuración (dict mutable para que --prueba pueda achicarla)
CFG = dict(
    espacio=dict(num_iterations=(64, 4096),               # rangos del script de Pasquini (lineales)
                 num_leaves=(16, 2048),
                 min_sum_hessian_in_leaf=(1e-6, 0.1)),
    n_trials=10,                                           # como Pasquini: 10 evaluaciones
    n_startup_trials=12,                                   # 4 x 3 hiperparámetros > 10 -> los 10 son aleatorios
    semilla_bo=SEMILLAS[0],
    n_semillas=10,
    prop_baja_artificial=0.01251,                          # tasa de BAJA en 03-04 (1,251 %)
    ganancia_baja2=1_072_500,
    costo=-27_500,
)
VARS_PRESTAMOS = ["cprestamos_personales", "mprestamos_personales"]
SUFIJOS = ("", "_lag1", "_delta1", "_lag2", "_delta2", "_tend3", "_avg3", "_zero")   # variantes de cada variable de préstamos


def modo_prueba():
    """SOLO para probar el código con datos chicos."""
    CFG.update(espacio=dict(num_iterations=(8, 24), num_leaves=(4, 16), min_sum_hessian_in_leaf=(1e-6, 0.1)),
               n_trials=3, n_startup_trials=2, n_semillas=3)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def sync(dir_exp, volumen, activo):
    """Respaldo al bucket; nunca frena el experimento."""
    if not activo:
        return
    try:
        subprocess.run(["gsutil", "-q", "-m", "rsync", "-r", dir_exp, f"{BUCKET}/exp/{volumen}"],
                       check=False, timeout=900, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log("  (aviso: falló el sync al bucket:", e, ")")


def guardar_atomico(escribir, ruta):
    tmp = ruta + ".tmp"
    escribir(tmp)
    os.replace(tmp, ruta)


def preparar(volumen, dir_base, scripts):
    """Crea exp/<volumen>/codigo y deja copia de los scripts y de este módulo."""
    dir_exp = os.path.join(dir_base, "exp", volumen)
    os.makedirs(os.path.join(dir_exp, "codigo"), exist_ok=True)
    for f in list(scripts) + [__file__]:
        shutil.copy(os.path.abspath(f), os.path.join(dir_exp, "codigo"))
    return dir_exp


def cargar(ruta_pq, meses):
    """Lee solo los meses pedidos. Matriz de features en float64 (numero_de_cliente no entra en float32).
    Ninguna columna 'clase_*' entra a la matriz de features."""
    tabla = pq.read_table(ruta_pq, filters=[("foto_mes", "in", [int(m) for m in meses])])
    cols = [c for c in tabla.column_names if not c.startswith("clase_")]
    assert not any(c.startswith("clase") for c in cols)
    n = tabla.num_rows
    X = np.empty((n, len(cols)), dtype="float64")
    for j, c in enumerate(cols):
        X[:, j] = tabla[c].to_numpy()
    D = dict(X=X, cols=cols,
             ids=tabla["numero_de_cliente"].to_numpy().astype("int64"),
             mes=tabla["foto_mes"].to_numpy(),
             yb=tabla["clase_binaria"].to_numpy().astype("float64"),
             tern=np.array(tabla["clase_ternaria"].to_pylist(), dtype=object))
    del tabla
    gc.collect()
    log(f"  datos cargados: X={X.shape}, {X.nbytes / 1e9:.1f} GB; features = foto_mes, numero_de_cliente y el resto; "
        f"ninguna clase")
    return D


def idx_sin_prestamos(cols):
    """Índices de las columnas SIN las 2 variables de préstamos personales y todas sus variantes: lag1, delta1, lag2, delta2, tend3, avg3 y _zero (16 columnas)."""
    excl = [b + s for b in VARS_PRESTAMOS for s in SUFIJOS]
    faltan = [x for x in excl if x not in cols]
    assert not faltan, f"columnas de préstamos que no están en el dataset: {faltan}"
    idx = np.array([j for j, c in enumerate(cols) if c not in set(excl)])
    return idx, [cols[j] for j in idx], excl


def curva_ganancia(prob, ternaria):
    """Ganancia acumulada al enviar los N de mayor probabilidad (N = 1..n)."""
    o = np.argsort(-prob, kind="stable")
    return np.cumsum(np.where(ternaria[o] == "BAJA+2", CFG["ganancia_baja2"], CFG["costo"]))


def entrenar(params_bo, semilla, ds):
    p = dict(PARAMS_FIJOS, seed=semilla, num_leaves=int(params_bo["num_leaves"]),
             min_sum_hessian_in_leaf=float(params_bo["min_sum_hessian_in_leaf"]))
    return lgb.train(p, ds, num_boost_round=int(params_bo["num_iterations"]))     # todos los árboles


# ---------------------------------------------------------------------------
# Bayesiana reproducible aunque se interrumpa.
# El registro de trials completos vive en un .jsonl (una línea por trial). Para proponer el trial k se arma
# un estudio nuevo en memoria con los k trials ya completos, en orden, y un muestreador con semilla = semilla_bo + k.
# La propuesta depende solo de k y de los resultados anteriores, no de cuántas veces ni dónde se cortó.
# ---------------------------------------------------------------------------
def correr_bayesiana(dtr, X_va, y_va, ruta_jsonl, despues_de_trial=None, etiqueta=""):
    if optuna is None:
        raise SystemExit("Falta instalar optuna (pip install optuna) para correr la bayesiana")
    esp = CFG["espacio"]
    dists = dict(num_iterations=optuna.distributions.IntDistribution(*esp["num_iterations"]),
                 num_leaves=optuna.distributions.IntDistribution(*esp["num_leaves"]),
                 min_sum_hessian_in_leaf=optuna.distributions.FloatDistribution(*esp["min_sum_hessian_in_leaf"]))
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    hist = [json.loads(l) for l in open(ruta_jsonl)] if os.path.exists(ruta_jsonl) else []
    if hist:
        log(f"  {etiqueta} retomando: {len(hist)} trials ya completos")
    while len(hist) < CFG["n_trials"]:
        k = len(hist)
        semilla_trial = CFG["semilla_bo"] + k
        estudio = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(
            seed=semilla_trial, n_startup_trials=CFG["n_startup_trials"]))
        for h in hist:
            estudio.add_trial(optuna.trial.create_trial(params=h["params"], distributions=dists, value=h["auc"]))
        trial = estudio.ask()
        t0 = time.time()
        hp = dict(num_iterations=trial.suggest_int("num_iterations", *esp["num_iterations"]),
                  num_leaves=trial.suggest_int("num_leaves", *esp["num_leaves"]),
                  min_sum_hessian_in_leaf=trial.suggest_float("min_sum_hessian_in_leaf", *esp["min_sum_hessian_in_leaf"]))
        m = entrenar(hp, CFG["semilla_bo"], dtr)                  # la bayesiana usa la primera semilla
        auc = float(roc_auc_score(y_va, m.predict(X_va)))
        del m
        gc.collect()
        seg = round(time.time() - t0)
        log(f"  {etiqueta} trial {k:>2}: it={hp['num_iterations']:>4} hojas={hp['num_leaves']:>4} "
            f"hess={hp['min_sum_hessian_in_leaf']:.6f} -> AUC {auc:.5f}  ({seg}s, semilla del muestreador {semilla_trial})")
        hist.append(dict(trial=k, params=hp, auc=auc, segundos=seg, semilla_muestreador=semilla_trial))
        with open(ruta_jsonl, "a") as fh:
            fh.write(json.dumps(hist[-1]) + "\n")
        if despues_de_trial:
            despues_de_trial()
    mejor = max(hist, key=lambda h: h["auc"])                      # ante empate, el primero
    mejores = dict(num_iterations=int(mejor["params"]["num_iterations"]),
                   num_leaves=int(mejor["params"]["num_leaves"]),
                   min_sum_hessian_in_leaf=float(mejor["params"]["min_sum_hessian_in_leaf"]))
    log(f"  {etiqueta} MEJORES hiperparámetros (trial {mejor['trial']}, AUC {mejor['auc']:.5f}): {mejores}")
    return hist, mejores, mejor


def entrenar_semillas(dtr, mejores, semillas, matrices, y_eval, dir_p, despues=None):
    """Entrena un modelo por semilla sobre dtr y predice cada matriz de `matrices` (dict nombre -> X).
    Guarda <nombre>_<semilla>.npy al terminar cada semilla (reanudable). Devuelve {nombre: {semilla: prob}}."""
    os.makedirs(dir_p, exist_ok=True)
    ruta = lambda nom, sd: os.path.join(dir_p, f"{nom}_{sd}.npy")
    pend = [sd for sd in semillas if not all(os.path.exists(ruta(n, sd)) for n in matrices)]
    log(f"  {len(semillas)} semillas {semillas}; pendientes {len(pend)}")
    for sd in pend:
        t = time.time()
        m = entrenar(mejores, sd, dtr)
        msg = []
        for nom, X in matrices.items():
            pr = m.predict(X).astype("float64")
            guardar_atomico(lambda r: np.save(open(r, "wb"), pr), ruta(nom, sd))
            if nom in y_eval:
                msg.append(f"AUC {nom} {roc_auc_score(y_eval[nom], pr):.5f}")
        log(f"  semilla {sd}: {', '.join(msg)}  ({time.time() - t:.0f}s)")
        del m
        gc.collect()
        if despues:
            despues()
    return {nom: {sd: np.load(ruta(nom, sd)) for sd in semillas} for nom in matrices}


def tabla_predicciones(ids, mes, tern, yb, P):
    """DataFrame con identificación, clase real, una columna prob_<semilla> por semilla y prob_ens (promedio simple)."""
    out = pd.DataFrame(dict(numero_de_cliente=ids, foto_mes=mes, clase_ternaria=tern, clase_binaria=yb.astype("float32")))
    for sd, pr in P.items():
        out[f"prob_{sd}"] = pr
    out["prob_ens"] = out[[f"prob_{sd}" for sd in P]].mean(axis=1)
    return out


def resumen_mes(P, y_real, tern, prefijo, etiqueta):
    """AUC por semilla y del ensamble, y curva de ganancia (por semilla, media y ensamble) en un mes con clase real."""
    semillas = list(P)
    ens = np.mean([P[s] for s in semillas], axis=0)
    aucs = {s: float(roc_auc_score(y_real, P[s])) for s in semillas}
    auc_ens = float(roc_auc_score(y_real, ens))
    pd.DataFrame(dict(semilla=semillas + ["ensamble"], auc=list(aucs.values()) + [auc_ens])
                 ).to_csv(f"{prefijo}_auc.csv", index=False)
    log(f"  {etiqueta}: AUC media de semillas {np.mean(list(aucs.values())):.5f} "
        f"(sd {np.std(list(aucs.values()), ddof=1):.5f}), ensamble {auc_ens:.5f}")
    envios = np.arange(1000, min(30000, len(tern)) + 1, 100)
    tab = pd.DataFrame(dict(envios=envios, **{f"g_{s}": curva_ganancia(P[s], tern)[envios - 1] for s in semillas}))
    tab["g_media"] = tab[[f"g_{s}" for s in semillas]].mean(axis=1)
    tab["g_ens"] = curva_ganancia(ens, tern)[envios - 1]
    tab.to_csv(f"{prefijo}_ganancia.csv", index=False)
    for nombre in ("g_media", "g_ens"):
        k = int(tab[nombre].idxmax())
        log(f"  {etiqueta} {nombre}: máximo {tab[nombre][k] / 1e6:,.1f} M con {int(tab['envios'][k]):,} envíos "
            f"(mirar la curva suavizada, no solo el pico)")


# ---------------------------------------------------------------------------
# Ensamble de las predicciones sobre 08 disponibles hasta el momento (se puede llamar en cualquier momento).
# ---------------------------------------------------------------------------
def ensamblar_08(dir_exp, volumen, semillas_orden, n=None, top=11000, guardar=True, otros_dirs=()):
    """Promedia las probabilidades guardadas en pred_08/prob_<semilla>.npy (en el orden de semillas_orden).
    otros_dirs: carpetas exp/<otro volumen> con más predicciones de las mismas características (mismo 08, mismo orden de
    clientes); no puede haber semillas repetidas entre carpetas. n: usar solo los primeros n modelos (None = todos)."""
    dirs = [dir_exp] + list(otros_dirs)
    ids = np.load(os.path.join(dir_exp, "ids_08.npy"))
    ruta_de = {}
    for d in dirs:
        ids_d = np.load(os.path.join(d, "ids_08.npy"))
        assert np.array_equal(ids_d, ids), f"{d}: ids_08.npy distinto: no son los mismos clientes de 08 en el mismo orden"
        dir_p = os.path.join(d, "pred_08")
        for sd in semillas_orden:
            f = os.path.join(dir_p, f"prob_{sd}.npy")
            if os.path.exists(f):
                assert sd not in ruta_de, f"la semilla {sd} está en dos carpetas ({ruta_de[sd]} y {f}): rangos de semillas superpuestos"
                ruta_de[sd] = f
    usadas = [sd for sd in semillas_orden if sd in ruta_de]
    if n:
        usadas = usadas[:n]
    if not usadas:
        raise SystemExit(f"No hay predicciones en {[os.path.join(d, 'pred_08') for d in dirs]}")
    P = np.column_stack([np.load(ruta_de[sd]) for sd in usadas])
    assert P.shape[0] == len(ids), "las predicciones no tienen la misma cantidad de clientes que ids_08.npy"
    ens = P.mean(axis=1)
    out = pd.DataFrame(dict(numero_de_cliente=ids, prob_ens=ens))
    log(f"  ensamble de {len(usadas)} modelos sobre {len(ids):,} clientes de 08"
        + (f" (carpetas: {', '.join(os.path.basename(d) for d in dirs)})" if len(dirs) > 1 else ""))
    # estabilidad: cuánto del top-N del ensamble completo ya está en el top-N del ensamble de los primeros k modelos
    if len(usadas) >= 4:
        top = min(top, len(ids))
        topN = set(np.argsort(-ens, kind="stable")[:top])
        ks = sorted({k for k in (2, 5, 10, 20, 40, 80, 160, 320) if k < len(usadas)})
        for k in ks:
            tk = set(np.argsort(-P[:, :k].mean(axis=1), kind="stable")[:top])
            log(f"  top {top:,}: con {k:>3} modelos coincide el {len(tk & topN) / top:.1%} con el ensamble de {len(usadas)}")
    if guardar:
        etiqueta = "+".join(os.path.basename(d) for d in dirs) if len(dirs) > 1 else volumen
        ruta_out = os.path.join(dir_exp, f"{etiqueta}_pred_08_ens_{len(usadas)}modelos.parquet")
        guardar_atomico(lambda r: out.to_parquet(r, index=False), ruta_out)
        log(f"  guardado: {ruta_out}")
    return out, usadas
