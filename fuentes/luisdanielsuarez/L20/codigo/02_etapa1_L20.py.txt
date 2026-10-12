"""
02_etapa1_L20.py — DMEyF, 1ra competencia, L20 (data augmentation con 05 y 06). ETAPA 1.

Requiere 01_preprocesamiento_L20.py (con preproc_comun.py) y comun_L20.py (misma carpeta). Sin variables derivadas.
L20 = L19 + lo recomendado por el profesor: tendencia y promedio de 3 meses, y variables _zero.

  A) Bayesiana (primera semilla, 878443; 3 hiperparámetros con rangos de Pasquini; 10 trials aleatorios):
     entrena con 202103 y 202104 SIN las variables de préstamos (cprestamos_personales y mprestamos_personales
     y todas sus variantes: lag1, delta1, lag2, delta2, tend3, avg3 y _zero = 16 columnas) y valida con 202106 (clase real, AUC).
  B) Con los hiperparámetros encontrados: 10 modelos, 10 semillas, entrenados en 03-04 sin préstamos,
     que predicen 202105 y 202106. Se guardan las predicciones.
  C) CLASE ARTIFICIAL: con la probabilidad promedio de las 10 semillas, se etiqueta BAJA (1) a la proporción
     1,251 % de clientes con mayor probabilidad (CADA MES POR SEPARADO) y CONTINUA (0) al resto. 05 y 06.
     Se guarda en un archivo aparte; no se mezcla con la clase real ni con el dataset.

Salidas en ~/dmeyf/exp/L20/ (y copia en el bucket):
    config_e1.json, L20_e1_bo_trials.jsonl, L20_e1_bayesiana.csv, L20_e1_hiperparametros.json
    L20_e1_pred_05_06.parquet     predicciones (prob_<semilla> x10 + prob_ens) de 05 y 06, con la clase real
    L20_e1_auc_05.csv / _06.csv, L20_e1_ganancia_05.csv / _06.csv
    L20_clase_artificial.parquet  numero_de_cliente, foto_mes, clase_artificial (0/1), prob_ens, clase_binaria (real)

Uso:  nohup python 02_etapa1_L20.py > L20_e1.log 2>&1 &    (o con el runner correr_L20.sh)
"""
import argparse
import json
import os

import lightgbm as lgb
import numpy as np
import pandas as pd

import comun_L20 as cm
from comun_L20 import log


def clase_artificial(prob_ens, prop):
    """1 (BAJA) a la proporción `prop` de mayor probabilidad; 0 (CONTINUA) al resto."""
    n = len(prob_ens)
    k = int(round(prop * n))
    orden = np.argsort(-prob_ens, kind="stable")
    y = np.zeros(n, dtype="int8")
    y[orden[:k]] = 1
    return y, k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volumen", default=cm.VOLUMEN)
    ap.add_argument("--dir_base", default=os.path.expanduser("~/dmeyf"))
    ap.add_argument("--dataset", default=None)
    ap.add_argument("--sin_bucket", action="store_true")
    ap.add_argument("--prueba", action="store_true", help="SOLO para probar el código: pocos trials y árboles chicos")
    a = ap.parse_args()
    if a.prueba:
        cm.modo_prueba()

    dir_exp = cm.preparar(a.volumen, a.dir_base, [__file__])
    ruta_pq = a.dataset or os.path.join(a.dir_base, "datasets", f"{a.volumen}_dataset.parquet")
    pref = os.path.join(dir_exp, f"{a.volumen}_e1")
    sync = lambda: cm.sync(dir_exp, a.volumen, not a.sin_bucket)
    semillas = cm.semillas_n(cm.CFG["n_semillas"])
    with open(os.path.join(dir_exp, "config_e1.json"), "w") as fh:
        json.dump(dict(CFG=cm.CFG, params_fijos=cm.PARAMS_FIJOS, dataset=ruta_pq, semillas=semillas,
                       versiones=dict(lightgbm=lgb.__version__, pandas=pd.__version__)), fh, indent=1, default=list)
    sync()

    log(f"=== ETAPA 1 ({a.volumen}): cargando meses 03 a 06 de {ruta_pq}")
    D = cm.cargar(ruta_pq, [202103, 202104, 202105, 202106])
    X, mes, yb, cols = D["X"], D["mes"], D["yb"], D["cols"]
    idx, cols_sp, excl = cm.idx_sin_prestamos(cols)
    log(f"  entrenamiento SIN {len(excl)} columnas de préstamos ({len(cols_sp)} de {len(cols)} features)")

    tr = np.isin(mes, [202103, 202104])
    m05, m06 = mes == 202105, mes == 202106
    assert not np.isnan(yb[tr]).any() and not np.isnan(yb[m06]).any() and not np.isnan(yb[m05]).any()

    # ---------------------------------------------------------------- A) bayesiana
    log(f"=== A) Bayesiana: train 03-04 ({tr.sum():,} filas, {yb[tr].mean():.3%} positivos) -> valida 06 real")
    dtr = lgb.Dataset(X[np.ix_(np.flatnonzero(tr), idx)], yb[tr], feature_name=cols_sp, params=cm.PARAMS_DATASET).construct()
    X06 = X[np.ix_(np.flatnonzero(m06), idx)]
    X05 = X[np.ix_(np.flatnonzero(m05), idx)]
    hist, mejores, mejor = cm.correr_bayesiana(dtr, X06, yb[m06], f"{pref}_bo_trials.jsonl", sync, "[e1]")
    pd.DataFrame([dict(trial=h["trial"], auc=h["auc"], **h["params"], segundos=h["segundos"],
                       semilla_muestreador=h["semilla_muestreador"]) for h in hist]).to_csv(f"{pref}_bayesiana.csv", index=False)
    with open(f"{pref}_hiperparametros.json", "w") as fh:
        json.dump(dict(mejores_hiperparametros=mejores, auc_validacion_06=mejor["auc"], trial_ganador=mejor["trial"],
                       params_fijos=cm.PARAMS_FIJOS, semilla_bayesiana=cm.CFG["semilla_bo"],
                       entrenamiento=[202103, 202104], validacion=202106, columnas_excluidas=excl), fh, indent=1)
    sync()

    # ---------------------------------------------------------------- B) 10 modelos -> predicen 05 y 06
    log(f"=== B) 10 modelos (03-04, sin préstamos) que predicen 05 y 06")
    P = cm.entrenar_semillas(dtr, mejores, semillas, {"m05": X05, "m06": X06},
                             {"m05": yb[m05], "m06": yb[m06]}, os.path.join(dir_exp, "pred_e1"), sync)
    del dtr, X05, X06
    pred = pd.concat([
        cm.tabla_predicciones(D["ids"][m], mes[m], D["tern"][m], yb[m], P[nom]) for nom, m in (("m05", m05), ("m06", m06))
    ], ignore_index=True)
    cm.guardar_atomico(lambda r: pred.to_parquet(r, index=False), f"{pref}_pred_05_06.parquet")
    for nom, m, etq in (("m05", m05, "05"), ("m06", m06, "06")):
        cm.resumen_mes(P[nom], yb[m], D["tern"][m], f"{pref}_{etq}", f"[e1 {etq}]")

    # ---------------------------------------------------------------- C) clase artificial
    prop = cm.CFG["prop_baja_artificial"]
    log(f"=== C) Clase artificial: {prop:.3%} de mayor probabilidad promedio = BAJA, por mes")
    partes = []
    for mm in (202105, 202106):
        s = pred[pred["foto_mes"] == mm].reset_index(drop=True)
        y_art, k = clase_artificial(s["prob_ens"].to_numpy(), prop)
        real = s["clase_binaria"].to_numpy() == 1
        aciertos = int(((y_art == 1) & real).sum())
        log(f"  {mm}: {len(s):,} clientes, {k:,} etiquetados BAJA | BAJA real: {int(real.sum()):,} | "
            f"coinciden {aciertos:,} (precisión {aciertos / k:.1%}, cobertura {aciertos / real.sum():.1%}) | "
            f"prob_ens de corte {s['prob_ens'].nlargest(k).iloc[-1]:.5f}")
        partes.append(pd.DataFrame(dict(numero_de_cliente=s["numero_de_cliente"].to_numpy().astype("int64"),
                                        foto_mes=s["foto_mes"].to_numpy().astype("int32"),
                                        clase_artificial=y_art, prob_ens=s["prob_ens"].to_numpy(),
                                        clase_binaria=s["clase_binaria"].to_numpy())))
    art = pd.concat(partes, ignore_index=True)
    cm.guardar_atomico(lambda r: art.to_parquet(r, index=False), os.path.join(dir_exp, f"{a.volumen}_clase_artificial.parquet"))
    sync()
    log("etapa 1 lista")


if __name__ == "__main__":
    main()
