r"""
19_eval_dataset.py
DMEyF 2026 - Primera Competencia - Experimento 5114

Pregunta: ¿el Feature Engineering del profesor (ds3007: 1.1 ccajas_depositos NA en 202105,
1.3 flags _zero, 1.4 tendencia y promedio de 3 meses) mejora al modelo que funciona (prueba 23)?
5113 mostro que la Training Strategy 1.7 (AUC, min_data_in_leaf 0, arboles de >1.000 hojas)
pierde ~52 M en junio, pero ahi cambiaron dataset e hiperparametros a la vez. Aca se cambia
SOLO el dataset: mismos hiperparametros (prueba 23), mismas semillas, mismo entrenamiento
(202103 + 202104), medido en 202106 completo.

REGLA R8 (fijada antes de ver resultados, mismo criterio que R7): se adopta ds3007 si su
meseta media (12.000-17.000) no es mas de 3 M peor que la de ds3003. En ese caso escribe
5114_ADOPTAR.txt y el .bat entrena el final 5022 (prueba 23 sobre ds3007, marzo-junio).

Uso:  py -3.12 19_eval_dataset.py configs\5114_eval_dataset.json
"""

print("Arrancando 19_eval_dataset.py ...", flush=True)

import json
import sys
import time
from datetime import datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from exp_utils import DIR_DATA, DIR_EXP, cerrar_experimento, iniciar_experimento

PARAM = {
    "experimento": 5114,
    "nombre": "eval_dataset",
    "descripcion": "Prueba 23 sobre ds3003 contra prueba 23 sobre ds3007 (FE del profesor), junio completo.",
    "sobrescribir": True,
    "candidatos": {"p23_ds3003": "ds3003_rank_extra.parquet", "p23_ds3007": "ds3007_profesor.parquet"},
    "referencia": "p23_ds3003",
    "retador": "p23_ds3007",
    "eleccion": "4107_bo_profesor_mar_abr/4107_eleccion.json",
    "usar_lag2": True,
    "clase": "clase_binaria2",
    "meses_train": [202103, 202104],
    "mes_futuro": 202106,
    "n_semillas": 20,
    "semillas_base": [571369, 849571, 355049, 655531, 700103],
    "tolerancia_R8_M": 3.0,
    "meseta": [12000, 17000],
    "cortes": list(range(10000, 15001, 500)),
    "ganancia_acierto": 1_072_500,
    "costo_estimulo": 27_500,
}
if len(sys.argv) > 1:
    config = Path(sys.argv[1])
    PARAM.update(json.loads(config.read_text(encoding="utf-8")))
    PARAM["_config"] = config.name
    print(f"Configuracion tomada de {config}")

exp = iniciar_experimento(PARAM)
GAN, COSTO = PARAM["ganancia_acierto"], PARAM["costo_estimulo"]
NO_FEATURES = {"numero_de_cliente", "foto_mes", "clase_ternaria", "clase_binaria1", "clase_binaria2"}
(exp.carpeta / f"{exp.id}_ADOPTAR.txt").unlink(missing_ok=True)


def es_primo(n):
    if n < 2 or n % 2 == 0:
        return n == 2
    return all(n % d for d in range(3, int(n ** 0.5) + 1, 2))


semillas = list(PARAM["semillas_base"])
rng = np.random.default_rng(PARAM["semillas_base"][0])
while len(semillas) < PARAM["n_semillas"]:
    c = int(rng.integers(100003, 999983))
    if es_primo(c) and c not in semillas:
        semillas.append(c)
semillas = semillas[:PARAM["n_semillas"]]

el = json.loads((DIR_EXP / PARAM["eleccion"]).read_text(encoding="utf-8"))
params = {k: v for k, v in el["params"].items() if k not in ("metric", "first_metric_only", "seed")}
for k in ("num_leaves", "min_data_in_leaf", "max_bin", "bagging_freq"):
    if k in params:
        params[k] = int(params[k])
params.update({"deterministic": True, "force_row_wise": True, "verbose": -1})
arboles = int(el["arboles"])
print(f"Hiperparametros: {el['origen']} | {arboles} arboles | min_data_in_leaf {params['min_data_in_leaf']}")

lo, hi = PARAM["meseta"]
ref_ids, g = None, None
filas = []
for nombre, dataset in PARAM["candidatos"].items():
    t0 = time.time()
    archivo = DIR_DATA / dataset
    feats = [c for c in pq.ParquetFile(archivo).schema_arrow.names if c not in NO_FEATURES
             and (PARAM["usar_lag2"] or not (c.endswith("_lag2") or c.endswith("_delta2")))]
    df = pd.read_parquet(archivo, columns=feats + ["numero_de_cliente", "foto_mes", "clase_ternaria", PARAM["clase"]],
                         filters=[("foto_mes", "in", PARAM["meses_train"] + [PARAM["mes_futuro"]])])
    tr = df[df["foto_mes"].isin(PARAM["meses_train"])]
    fu = df[df["foto_mes"] == PARAM["mes_futuro"]].sort_values("numero_de_cliente").reset_index(drop=True)
    del df
    if ref_ids is None:
        ref_ids = fu["numero_de_cliente"].to_numpy()
        g = np.where(fu["clase_ternaria"].astype(str).to_numpy() == "BAJA+2", GAN, -COSTO).astype(float)
    assert (fu["numero_de_cliente"].to_numpy() == ref_ids).all(), "Los clientes de junio no coinciden entre datasets"
    dtr = lgb.Dataset(tr[feats], label=tr[PARAM["clase"]].astype(int).to_numpy(),
                      params={"max_bin": 31, "feature_pre_filter": False, "verbose": -1}, free_raw_data=True)
    Xf = fu[feats]
    del tr
    print(f"{nombre}: {len(feats)} variables ({time.time() - t0:.0f} s de carga)", flush=True)
    suma = np.zeros(len(fu))
    for i, s in enumerate(semillas, start=1):
        prob = lgb.train(dict(params, seed=s), dtr, num_boost_round=arboles).predict(Xf)
        suma += prob
        acum = np.cumsum(g[np.argsort(-prob, kind="stable")])
        filas.append({"candidato": nombre, "semilla": s, "meseta": acum[lo - 1:hi].mean(),
                      **{f"g{c}": acum[c - 1] for c in PARAM["cortes"]}})
        if i % 5 == 0:
            print(f"  {nombre}: {i}/{len(semillas)} semillas | {datetime.now():%a %H:%M}", flush=True)
    acum = np.cumsum(g[np.argsort(-(suma / len(semillas)), kind="stable")])
    filas.append({"candidato": nombre, "semilla": "semillerio", "meseta": acum[lo - 1:hi].mean(),
                  **{f"g{c}": acum[c - 1] for c in PARAM["cortes"]}})
    del dtr, Xf, fu

tabla = pd.DataFrame(filas)
tabla.to_csv(exp.ruta("por_semilla"), index=False)
ind = tabla[tabla["semilla"] != "semillerio"]
sem = tabla[tabla["semilla"] == "semillerio"].set_index("candidato")
a = ind[ind["candidato"] == PARAM["referencia"]].set_index("semilla")["meseta"]
b = ind[ind["candidato"] == PARAM["retador"]].set_index("semilla")["meseta"]
d = (b - a.loc[b.index]) / 1e6
resumen = pd.DataFrame({
    "meseta_media_M": ind.groupby("candidato")["meseta"].mean() / 1e6,
    "desvio_M": ind.groupby("candidato")["meseta"].std() / 1e6,
    "semillerio_meseta_M": sem["meseta"] / 1e6}).round(1)
curvas = sem[[f"g{c}" for c in PARAM["cortes"]]].div(1e6).round(1).T
resumen.to_csv(exp.ruta("resumen"))
curvas.to_csv(exp.ruta("curvas_semillerio"))
print(f"\n=== Junio completo, prueba 23, {len(semillas)} semillas (millones) ===")
print(resumen.to_string())
print("\nGanancia del semillerio por corte:")
print(curvas.to_string())
print(f"\nDiferencia {PARAM['retador']} - {PARAM['referencia']} por semilla: media {d.mean():+.1f} M, "
      f"gana en {(d > 0).sum()}/{len(d)} semillas")

adoptar = bool(d.mean() >= -PARAM["tolerancia_R8_M"])
texto = (f"R8: {PARAM['retador']} {b.mean() / 1e6:.1f} M vs {PARAM['referencia']} {a.mean() / 1e6:.1f} M "
         f"(dif {d.mean():+.1f} M) -> " + ("ADOPTAR ds3007 (FE del profesor): se entrena el final 5022"
                                            if adoptar else "QUEDARSE CON 5015 (ds3003)"))
print(texto)
if adoptar:
    (exp.carpeta / f"{exp.id}_ADOPTAR.txt").write_text(texto + "\n", encoding="utf-8")
cerrar_experimento(exp, {"R8": texto, "dif_media_M": round(float(d.mean()), 2),
                         "semillas_gana": int((d > 0).sum()), "adoptar": adoptar})
