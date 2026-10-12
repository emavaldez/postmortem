r"""
18_ensamble_profesor.py
DMEyF 2026 - Primera Competencia - Experimentos 5113 (evaluacion) y 5021 (produccion)

Final Training / Scoring del profesor (2.1 y 2.2):
  - Se entrenan VARIOS modelos (10+) con hiperparametros DISTINTOS: las mejores pruebas de la
    Bayesiana (por AUC), cada uno con su semilla, sin undersampling.
  - Se aplican al mes a predecir y se ENSAMBLAN promediando sus probabilidades por cliente.

Modo "evaluacion" (5113, agregado nuestro para decidir con evidencia, no lo pide el profesor):
  entrena el ensamble con 202103 + 202104 completos y lo mide en 202106 completo, en dos
  versiones: con min_sum_hessian_in_leaf escalado al 100% de las filas (x 1/0,7, porque la
  Bayesiana entreno con el 70%) y sin escalar (como la catedra). Como referencia, el semillerio
  de la prueba 23 sobre ds3003 (el pipeline de la entrega vigente 5015) con la misma cantidad
  de modelos. REGLAS fijadas de antemano:
    R6  escalado: se usa la version del ensamble con mayor meseta (12.000-17.000) en junio.
    R7  entrega: se recomienda el ensamble si su meseta en junio no es mas de 3 M peor que la de
        la prueba 23; si no, se recomienda quedarse con 5015.
  Escribe 5113_eleccion.json (lista de modelos ya en la escala de 2 meses + si escalar).

Modo "produccion" (5021): lee la eleccion, entrena cada modelo con 202103-202106, predice
  202108, promedia y graba <id>_probabilidades.csv para 10_entrega_zulip.py.

Reanudable: cada modelo entrenado se guarda en cache\; si se corta la PC, al volver a correr
se reutiliza lo hecho. Para apurar a mano: crear APURAR.txt en la carpeta del proyecto.
Corte por horario en los dos modos: pasada PARAM["hora_limite"] no se empiezan modelos nuevos
si ya hay PARAM["min_modelos"] (10, el minimo del profesor).

Uso:  py -3.12 18_ensamble_profesor.py configs\5113_eval_ensamble.json
      py -3.12 18_ensamble_profesor.py configs\5021_prod_ensamble.json
"""

print("Arrancando 18_ensamble_profesor.py ...", flush=True)

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from exp_utils import DIR_DATA, DIR_EXP, ROOT, cerrar_experimento, iniciar_experimento

PARAM = {
    "experimento": 5113,
    "nombre": "eval_ensamble",
    "descripcion": "Ensamble de las mejores pruebas de 4112 medido en junio (escalado y sin escalar) contra la prueba 23.",
    "sobrescribir": True,
    "modo": "evaluacion",                      # "evaluacion" | "produccion"
    "dataset": "ds3007_profesor.parquet",
    "usar_lag2": True,
    "clase": "clase_binaria2",
    "top": "4112_bo_profesor_ds3007/4112_top.json",   # evaluacion
    "eleccion": "5113_eval_ensamble/5113_eleccion.json",  # produccion
    "top_k": 12,
    # PC AYUDANTE: entrena los modelos en orden INVERSO (del ultimo al primero) y solo los deja en
    # cache\; no arma el ensamble ni decide nada. Copiando su carpeta cache\ a la de la PC principal,
    # esta los reutiliza al llegar a ellos en vez de entrenarlos.
    "ayudante": False,
    "min_modelos": 10,
    "hora_limite": None,
    "meses_train": [202103, 202104],
    "mes_futuro": 202106,                      # evaluacion
    "mes_prediccion": 202108,                  # produccion
    "fraccion_train_cv": 0.7,
    "referencia_p23": {"dataset": "ds3003_rank_extra.parquet",
                       "eleccion": "4107_bo_profesor_mar_abr/4107_eleccion.json"},
    "tolerancia_R7_M": 3.0,
    "semillas_base": [571369, 849571, 355049, 655531, 700103],
    "semilla_publico": 571369,
    "fraccion_publico": 0.3,
    "meseta": [12000, 17000],
    "cortes": list(range(9000, 15001, 500)),
    "ganancia_acierto": 1_072_500,
    "costo_estimulo": 27_500,
}

if len(sys.argv) > 1:
    config = Path(sys.argv[1])
    PARAM.update(json.loads(config.read_text(encoding="utf-8")))
    PARAM["_config"] = config.name
    print(f"Configuracion tomada de {config}")
assert PARAM["modo"] in ("evaluacion", "produccion")
EVAL = PARAM["modo"] == "evaluacion"

exp = iniciar_experimento(PARAM)
GAN, COSTO = PARAM["ganancia_acierto"], PARAM["costo_estimulo"]
NO_FEATURES = {"numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"}
REPRODUCIBLE = {"deterministic": True, "force_row_wise": True, "verbose": -1}
LIMITE = datetime.strptime(PARAM["hora_limite"], "%Y-%m-%d %H:%M") if PARAM.get("hora_limite") else None
MES_OBJ = PARAM["mes_futuro"] if EVAL else PARAM["mes_prediccion"]


def es_primo(n):
    if n < 2 or n % 2 == 0:
        return n == 2
    return all(n % d for d in range(3, int(n ** 0.5) + 1, 2))


def generar_semillas(k):
    s = list(PARAM["semillas_base"])
    rng = np.random.default_rng(PARAM["semillas_base"][0])
    while len(s) < k:
        c = int(rng.integers(100003, 999983))
        if es_primo(c) and c not in s:
            s.append(c)
    return s[:k]


def limpiar(params):
    p = {k: v for k, v in params.items() if k not in ("metric", "first_metric_only", "seed")}
    for k in ("num_leaves", "min_data_in_leaf", "max_bin", "bagging_freq"):
        if k in p:
            p[k] = int(round(p[k]))
    return {**p, **REPRODUCIBLE}


APURAR = ROOT / "APURAR.txt"      # si existe: hacer solo el minimo y seguir
CACHE = exp.carpeta / "cache"     # prediccion de cada modelo ya entrenado (para reanudar sin perder nada)
CACHE.mkdir(exist_ok=True)


def hora_de_cortar(hechos):
    if hechos < PARAM["min_modelos"]:
        return False
    return (LIMITE is not None and datetime.now() >= LIMITE) or APURAR.exists()


def predecir(params, semilla, arboles, dtr, X, etiqueta):
    """Entrena y predice; si ese mismo modelo ya se habia entrenado antes, lee la prediccion guardada."""
    import hashlib
    clave = json.dumps({"p": params, "s": int(semilla), "a": int(arboles), "mes": MES_OBJ,
                        "train": PARAM["meses_train"], "filas": len(X)}, sort_keys=True, default=str)
    archivo = CACHE / f"{etiqueta}_{hashlib.md5(clave.encode()).hexdigest()[:10]}.npy"
    if archivo.exists():
        try:
            prob = np.load(archivo)
            if prob.shape == (len(X),) and np.isfinite(prob).all():
                print(f"    ({etiqueta}: ya estaba hecho, se reutiliza)", flush=True)
                return prob
        except Exception:
            pass
        print(f"    ({etiqueta}: el archivo guardado estaba incompleto, se entrena de nuevo)", flush=True)
    prob = lgb.train(dict(params, seed=int(semilla)), dtr, num_boost_round=int(arboles)).predict(X)
    temporal = archivo.with_name(archivo.stem + ".escribiendo")      # no termina en .npy: nadie lo toma a medias
    with open(temporal, "wb") as f:
        np.save(f, prob)
    os.replace(temporal, archivo)                                    # aparece completo, de una sola vez
    return prob


def cargar(dataset, meses_train, mes_obj):
    archivo = DIR_DATA / dataset
    feats = [c for c in pq.ParquetFile(archivo).schema_arrow.names if c not in NO_FEATURES
             and (PARAM["usar_lag2"] or not (c.endswith("_lag2") or c.endswith("_delta2")))]
    df = pd.read_parquet(archivo, columns=feats + ["numero_de_cliente", "foto_mes", "clase_ternaria", PARAM["clase"]],
                         filters=[("foto_mes", "in", meses_train + [mes_obj])])
    tr = df[df["foto_mes"].isin(meses_train)]
    ob = df[df["foto_mes"] == mes_obj].reset_index(drop=True)
    del df
    assert sorted(tr["foto_mes"].unique()) == sorted(meses_train), "Faltan meses de entrenamiento"
    assert tr[PARAM["clase"]].notna().all(), "Hay filas de train sin clase"
    assert len(ob) > 0, f"No hay filas de {mes_obj}"
    dtr = lgb.Dataset(tr[feats], label=tr[PARAM["clase"]].astype(int).to_numpy(),
                      params={"max_bin": 31, "min_data_in_leaf": 0, "feature_pre_filter": False, "verbose": -1},
                      free_raw_data=True).construct()
    n_tr = len(tr)
    del tr
    print(f"{dataset}: {len(feats)} variables | train {n_tr:,} filas {meses_train} | {mes_obj}: {len(ob):,} filas", flush=True)
    return dtr, ob[feats], ob[["numero_de_cliente", "clase_ternaria"]].copy(), n_tr


# ===========================================================================
# EVALUACION
# ===========================================================================
if EVAL:
    top = json.loads((DIR_EXP / PARAM["top"]).read_text(encoding="utf-8"))[:PARAM["top_k"]]
    assert len(top) >= PARAM["min_modelos"], f"La Bayesiana dejo {len(top)} pruebas; hacen falta {PARAM['min_modelos']}"
    semillas = generar_semillas(len(top))
    dtr, Xf, info, _ = cargar(PARAM["dataset"], PARAM["meses_train"], MES_OBJ)
    tern = info["clase_ternaria"].astype(str).to_numpy()
    g = np.where(tern == "BAJA+2", GAN, -COSTO).astype(float)
    rng_p = np.random.default_rng(PARAM["semilla_publico"])
    publico = np.zeros(len(info), dtype=bool)
    for clase in np.unique(tern):
        idx = np.flatnonzero(tern == clase)
        publico[rng_p.choice(idx, size=int(round(len(idx) * PARAM["fraccion_publico"])), replace=False)] = True
    lo, hi = PARAM["meseta"]

    def medir(prob):
        orden = np.argsort(-prob, kind="stable")
        go, pub = g[orden], publico[orden]
        acum = np.cumsum(go)
        out = {"meseta": acum[lo - 1:hi].mean()}
        for c in PARAM["cortes"]:
            out[f"g{c}"] = acum[c - 1]
        out["publico_12000"] = go[:12000][pub[:12000]].sum() / PARAM["fraccion_publico"]
        out["privado_12000"] = go[:12000][~pub[:12000]].sum() / (1 - PARAM["fraccion_publico"])
        return out

    versiones = {"escalado": True, "sin_escalar": False}
    if PARAM["ayudante"]:
        print(f"MODO AYUDANTE: {len(top)} modelos en orden inverso -> {CACHE}", flush=True)
        for c, s in reversed(list(zip(top, semillas))):
            t = time.time()
            for v, escalar in versiones.items():
                p = dict(c["params"])
                if escalar and p.get("min_sum_hessian_in_leaf"):
                    p["min_sum_hessian_in_leaf"] = p["min_sum_hessian_in_leaf"] / PARAM["fraccion_train_cv"]
                predecir(limpiar(p), s, c["arboles"], dtr, Xf, f"{c['nombre']}_{v}")
            print(f"  listo {c['nombre']} ({(time.time() - t) / 60:.1f} min) | {datetime.now():%a %H:%M} | "
                  f"COPIAR la carpeta cache a la PC principal", flush=True)
        print("AYUDANTE: termino todos los modelos.")
        sys.exit(0)
    suma = {v: np.zeros(len(info)) for v in versiones}
    filas, usados = [], []
    for i, (c, s) in enumerate(zip(top, semillas), start=1):
        if hora_de_cortar(len(usados)):
            print(f"** Hora limite o APURAR.txt: el ensamble queda con {len(usados)} modelos **", flush=True)
            break
        t = time.time()
        for v, escalar in versiones.items():
            p = dict(c["params"])
            if escalar and p.get("min_sum_hessian_in_leaf"):
                p["min_sum_hessian_in_leaf"] = p["min_sum_hessian_in_leaf"] / PARAM["fraccion_train_cv"]
            prob = predecir(limpiar(p), s, c["arboles"], dtr, Xf, f"{c['nombre']}_{v}")
            suma[v] += prob
            filas.append({"modelo": c["nombre"], "version": v, "semilla": s, "arboles": c["arboles"],
                          "num_leaves": p["num_leaves"], "min_sum_hessian_in_leaf": p.get("min_sum_hessian_in_leaf"),
                          "auc_cv": c.get("auc_cv"), **medir(prob),
                          **{f"ensamble_{k}": val for k, val in medir(suma[v] / i).items() if k == "meseta"}})
        usados.append(c)
        pd.DataFrame(filas).to_csv(exp.ruta("por_modelo"), index=False)
        print(f"  modelo {i:2d}/{len(top)} {c['nombre']} ({c['arboles']} arboles, {c['params']['num_leaves']} hojas) "
              f"{(time.time() - t) / 60:.1f} min | {datetime.now():%a %H:%M} | ensamble hasta aca: "
              + ", ".join(f"{v} {medir(suma[v] / i)['meseta'] / 1e6:.1f} M" for v in versiones), flush=True)
    k = len(usados)
    del dtr, Xf

    # referencia: semillerio de la prueba 23 sobre ds3003 con la misma cantidad de modelos
    ref = PARAM["referencia_p23"]
    el = json.loads((DIR_EXP / ref["eleccion"]).read_text(encoding="utf-8"))
    dtr3, Xf3, info3, _ = cargar(ref["dataset"], PARAM["meses_train"], MES_OBJ)
    # alinear por cliente (los datasets pueden estar ordenados distinto)
    pos = pd.Series(np.arange(len(info3)), index=info3["numero_de_cliente"].to_numpy())
    alinear = pos.loc[info["numero_de_cliente"].to_numpy()].to_numpy()
    suma_p23 = np.zeros(len(info))
    t = time.time()
    for s in semillas[:k]:
        prob = predecir(limpiar(el["params"]), s, el["arboles"], dtr3, Xf3, "p23")
        suma_p23 += prob[alinear]
        filas.append({"modelo": "p23", "version": "referencia", "semilla": s, "arboles": el["arboles"], **medir(prob[alinear])})
    print(f"  p23: {k} semillas ({(time.time() - t) / 60:.1f} min)", flush=True)
    del dtr3, Xf3
    por_modelo = pd.DataFrame(filas)
    por_modelo.to_csv(exp.ruta("por_modelo"), index=False)

    ens = {"ensamble_escalado": medir(suma["escalado"] / k), "ensamble_sin_escalar": medir(suma["sin_escalar"] / k),
           f"p23_semillerio_{k}": medir(suma_p23 / k)}
    tabla = pd.DataFrame([{"modelo": n_, "meseta_M": round(m_["meseta"] / 1e6, 1),
                           "publico12000_M": round(m_["publico_12000"] / 1e6, 1),
                           "privado12000_M": round(m_["privado_12000"] / 1e6, 1),
                           **{f"g{c}_M": round(m_[f"g{c}"] / 1e6, 1) for c in PARAM["cortes"]}} for n_, m_ in ens.items()])
    tabla.to_csv(exp.ruta("resumen"), index=False)
    indiv = por_modelo.groupby("version")["meseta"].agg(["mean", "std", "min", "max"]).div(1e6).round(1)
    print(f"\n=== Junio completo: ensambles de {k} modelos (millones) ===")
    print(tabla[["modelo", "meseta_M", "publico12000_M", "privado12000_M"]].to_string(index=False))
    print("\nGanancia por corte:")
    print(tabla.set_index("modelo")[[f"g{c}_M" for c in PARAM["cortes"]]].T.to_string())
    print("\nModelos individuales (meseta, millones):")
    print(indiv.to_string())

    m_esc, m_sin = ens["ensamble_escalado"]["meseta"], ens["ensamble_sin_escalar"]["meseta"]
    escalar = bool(m_esc >= m_sin)
    m_ens = max(m_esc, m_sin)
    m_p23 = ens[f"p23_semillerio_{k}"]["meseta"]
    usar_ensamble = bool(m_ens >= m_p23 - PARAM["tolerancia_R7_M"] * 1e6)
    modelos = []
    for c in usados:
        p = {kk: vv for kk, vv in limpiar(c["params"]).items() if kk not in REPRODUCIBLE}
        if escalar and p.get("min_sum_hessian_in_leaf"):
            p["min_sum_hessian_in_leaf"] = p["min_sum_hessian_in_leaf"] / PARAM["fraccion_train_cv"]
        modelos.append({"nombre": c["nombre"], "params": p, "arboles": int(c["arboles"])})
    eleccion = {"origen": f"5113: ensamble de {k} pruebas de {PARAM['top']}",
                "modelos": modelos, "semillas": semillas[:k],
                "escalar_regularizacion": escalar, "fraccion_mes_referencia": float(len(PARAM["meses_train"])),
                "R6": f"escalado {m_esc / 1e6:.1f} M vs sin escalar {m_sin / 1e6:.1f} M -> {'escalar' if escalar else 'no escalar'}",
                "R7": f"ensamble {m_ens / 1e6:.1f} M vs p23 {m_p23 / 1e6:.1f} M -> "
                      f"{'ENTREGAR EL ENSAMBLE' if usar_ensamble else 'QUEDARSE CON 5015'}",
                "recomendacion": "ensamble" if usar_ensamble else "5015"}
    (exp.carpeta / f"{exp.id}_eleccion.json").write_text(json.dumps(eleccion, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nR6: {eleccion['R6']}\nR7: {eleccion['R7']}")
    cerrar_experimento(exp, {"modelos": k, "R6": eleccion["R6"], "R7": eleccion["R7"]})

# ===========================================================================
# PRODUCCION
# ===========================================================================
else:
    el = json.loads((DIR_EXP / PARAM["eleccion"]).read_text(encoding="utf-8"))
    print(f"Eleccion: {el['origen']} | {el.get('R6')} | {el.get('R7')}")
    dtr, Xp, info, n_tr = cargar(PARAM["dataset"], PARAM["meses_train"], MES_OBJ)
    factor = len(PARAM["meses_train"]) / el["fraccion_mes_referencia"]
    escalar = el["escalar_regularizacion"]
    print(f"Regularizacion de hoja: {'x ' + format(factor, '.2f') + ' (por filas)' if escalar else 'sin escalar'}")
    if PARAM["ayudante"]:
        print(f"MODO AYUDANTE: {len(el['modelos'])} modelos en orden inverso -> {CACHE}", flush=True)
        for c, s in reversed(list(zip(el["modelos"], el["semillas"]))):
            t = time.time()
            p = limpiar(c["params"])
            if escalar and p.get("min_sum_hessian_in_leaf"):
                p["min_sum_hessian_in_leaf"] = p["min_sum_hessian_in_leaf"] * factor
            predecir(p, s, c["arboles"], dtr, Xp, c["nombre"])
            print(f"  listo {c['nombre']} ({(time.time() - t) / 60:.1f} min) | {datetime.now():%a %H:%M} | "
                  f"COPIAR la carpeta cache a la PC principal", flush=True)
        print("AYUDANTE: termino todos los modelos.")
        sys.exit(0)
    suma = np.zeros(len(info))
    probs, usados = {}, []
    for i, (c, s) in enumerate(zip(el["modelos"], el["semillas"]), start=1):
        if hora_de_cortar(len(usados)):
            print(f"** Hora limite o APURAR.txt: el ensamble queda con {len(usados)} modelos **", flush=True)
            break
        t = time.time()
        p = limpiar(c["params"])
        if escalar and p.get("min_sum_hessian_in_leaf"):
            p["min_sum_hessian_in_leaf"] = p["min_sum_hessian_in_leaf"] * factor
        prob = predecir(p, s, c["arboles"], dtr, Xp, c["nombre"])
        assert np.isfinite(prob).all(), f"Probabilidades no finitas en {c['nombre']}"
        suma += prob
        probs[c["nombre"]] = prob.astype("float32")
        usados.append({"nombre": c["nombre"], "semilla": s, "arboles": c["arboles"], "num_leaves": p["num_leaves"],
                       "min_sum_hessian_in_leaf": p.get("min_sum_hessian_in_leaf")})
        print(f"  modelo {i:2d}/{len(el['modelos'])} {c['nombre']} {(time.time() - t) / 60:.1f} min | "
              f"{datetime.now():%a %H:%M}", flush=True)
    k = len(usados)
    assert k >= PARAM["min_modelos"], f"Solo {k} modelos (minimo {PARAM['min_modelos']})"
    prob_final = suma / k
    ids = info["numero_de_cliente"].astype("int64").to_numpy()
    pd.DataFrame({"numero_de_cliente": ids, "prob": prob_final}).to_csv(exp.ruta("probabilidades"), index=False)
    pd.DataFrame({"numero_de_cliente": ids, **probs}).to_parquet(exp.ruta("prob_por_modelo", ext="parquet"), index=False)
    pd.DataFrame(usados).to_csv(exp.ruta("modelos"), index=False)
    q = np.quantile(prob_final, [0.5, 0.9, 0.99])
    print(f"\nEnsamble de {k} modelos sobre {MES_OBJ}: {len(ids):,} clientes | prob mediana {q[0]:.4f}, "
          f"p90 {q[1]:.4f}, p99 {q[2]:.4f}")
    cerrar_experimento(exp, {"modelos": k, "escalar": escalar, "recomendacion_5113": el.get("recomendacion")})
