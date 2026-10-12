"""
03_etapa2_L20.py — DMEyF, 1ra competencia, L20 (data augmentation con 05 y 06). ETAPA 2.

Requiere haber terminado 02_etapa1_L20.py (usa L20_clase_artificial.parquet), más 01_preprocesamiento_L20.py y
comun_L20.py (misma carpeta). Sin variables derivadas.

Etiquetas de ENTRENAMIENTO: real en 03 y 04; ARTIFICIAL en 05 y 06 (la clase real de 05 y 06 nunca se usa para entrenar,
solo para evaluar). Todo se entrena SIN las variables de préstamos (16 columnas: las 2 originales y sus variantes), como en la etapa 1.

  A) Nueva bayesiana (mismos rangos, misma semilla 878443, 10 trials aleatorios): entrena con 03, 04, 05 artificial
     y 06 artificial; evalúa el AUC en 06 con la clase REAL.
  B) Con los hiperparámetros encontrados: 10 modelos, 10 semillas, mismos datos de entrenamiento, que predicen 06.
     Se evalúa con la clase real de 06 (AUC y ganancia por línea de corte).
Es el mismo esquema que se aplicará luego a 08: etiquetas artificiales en 07 y 08, entrenar con ellos y predecir 08.

Salidas en ~/dmeyf/exp/L20/ (y copia en el bucket):
    config_e2.json, L20_e2_bo_trials.jsonl, L20_e2_bayesiana.csv, L20_e2_hiperparametros.json
    L20_e2_pred_06.parquet        10 predicciones sobre 06 (prob_<semilla>) + prob_ens, con la clase real
    L20_e2_auc.csv, L20_e2_ganancia.csv

Uso:  nohup python 03_etapa2_L20.py > L20_e2.log 2>&1 &    (o con el runner correr_L20.sh)
"""
import argparse
import json
import os

import lightgbm as lgb
import numpy as np
import pandas as pd

import comun_L20 as cm
from comun_L20 import log


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
    ruta_art = os.path.join(dir_exp, f"{a.volumen}_clase_artificial.parquet")
    if not os.path.exists(ruta_art):
        raise SystemExit(f"Falta {ruta_art}: terminar primero 02_etapa1_L20.py")
    pref = os.path.join(dir_exp, f"{a.volumen}_e2")
    sync = lambda: cm.sync(dir_exp, a.volumen, not a.sin_bucket)
    semillas = cm.semillas_n(cm.CFG["n_semillas"])
    with open(os.path.join(dir_exp, "config_e2.json"), "w") as fh:
        json.dump(dict(CFG=cm.CFG, params_fijos=cm.PARAMS_FIJOS, dataset=ruta_pq, clase_artificial=ruta_art,
                       semillas=semillas, versiones=dict(lightgbm=lgb.__version__, pandas=pd.__version__)),
                  fh, indent=1, default=list)
    sync()

    log(f"=== ETAPA 2 ({a.volumen}): cargando meses 03 a 06 de {ruta_pq}")
    D = cm.cargar(ruta_pq, [202103, 202104, 202105, 202106])
    X, mes, yb, cols = D["X"], D["mes"], D["yb"], D["cols"]
    idx, cols_sp, excl = cm.idx_sin_prestamos(cols)
    log(f"  entrenamiento SIN {len(excl)} columnas de préstamos ({len(cols_sp)} de {len(cols)} features)")

    # ---------------------------------------------------------------- etiquetas de entrenamiento
    art = pd.read_parquet(ruta_art, columns=["numero_de_cliente", "foto_mes", "clase_artificial"])
    llave = pd.DataFrame(dict(numero_de_cliente=D["ids"], foto_mes=mes.astype("int32")))
    unido = llave.merge(art, on=["numero_de_cliente", "foto_mes"], how="left")
    assert len(unido) == len(D["ids"]), "la unión con la clase artificial duplicó o perdió filas"
    y_art = unido["clase_artificial"].to_numpy()                   # NaN en 03 y 04 (no tienen clase artificial)
    y_train = yb.copy()                                            # real en 03 y 04
    m_art = np.isin(mes, [202105, 202106])
    assert not np.isnan(y_art[m_art]).any(), "faltan etiquetas artificiales en 05 o 06"
    y_train[m_art] = y_art[m_art]                                  # ARTIFICIAL en 05 y 06
    assert not np.isnan(y_train).any()
    for mm in (202103, 202104, 202105, 202106):
        s = mes == mm
        log(f"  {mm}: etiqueta de entrenamiento {'ARTIFICIAL' if mm in (202105, 202106) else 'real'}, "
            f"{int(y_train[s].sum()):,} BAJA de {s.sum():,} ({y_train[s].mean():.3%}); BAJA real: {int(yb[s].sum()):,}")
    m06 = mes == 202106
    y06_real = yb[m06]                                             # solo para EVALUAR

    # ---------------------------------------------------------------- A) bayesiana
    log("=== A) Bayesiana: train 03, 04, 05 artificial, 06 artificial -> evalúa AUC en 06 con la clase real")
    Xs = np.take(X, idx, axis=1)                                   # copia C-contigua sin las columnas de préstamos
    del D["X"], X
    dtr = lgb.Dataset(Xs, y_train, feature_name=cols_sp, params=cm.PARAMS_DATASET).construct()
    X06 = Xs[np.flatnonzero(m06)]
    del Xs
    hist, mejores, mejor = cm.correr_bayesiana(dtr, X06, y06_real, f"{pref}_bo_trials.jsonl", sync, "[e2]")
    pd.DataFrame([dict(trial=h["trial"], auc=h["auc"], **h["params"], segundos=h["segundos"],
                       semilla_muestreador=h["semilla_muestreador"]) for h in hist]).to_csv(f"{pref}_bayesiana.csv", index=False)
    with open(f"{pref}_hiperparametros.json", "w") as fh:
        json.dump(dict(mejores_hiperparametros=mejores, auc_evaluacion_06_real=mejor["auc"], trial_ganador=mejor["trial"],
                       params_fijos=cm.PARAMS_FIJOS, semilla_bayesiana=cm.CFG["semilla_bo"],
                       entrenamiento="03, 04 reales + 05, 06 artificiales", evaluacion="06 real",
                       columnas_excluidas=excl), fh, indent=1)
    sync()

    # ---------------------------------------------------------------- B) 10 modelos -> predicen 06
    log("=== B) 10 modelos (mismos datos de entrenamiento, sin préstamos) que predicen 06")
    P = cm.entrenar_semillas(dtr, mejores, semillas, {"m06": X06}, {"m06": y06_real},
                             os.path.join(dir_exp, "pred_e2"), sync)["m06"]
    pred = cm.tabla_predicciones(D["ids"][m06], mes[m06], D["tern"][m06], y06_real, P)
    cm.guardar_atomico(lambda r: pred.to_parquet(r, index=False), f"{pref}_pred_06.parquet")
    cm.resumen_mes(P, y06_real, D["tern"][m06], pref, "[e2 06]")
    sync()
    log("etapa 2 lista")


if __name__ == "__main__":
    main()
