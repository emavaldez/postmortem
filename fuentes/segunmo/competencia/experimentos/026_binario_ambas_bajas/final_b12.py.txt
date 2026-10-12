"""026b — experimento COMPLETO del binario con ambas bajas como positivos en el régimen del final (train 202103–06 -> score 202108), para compararlo en el Public.
Un solo cambio respecto de `010_multiclase/final.py`: mismas 6 configuraciones de 005 (mejores_trials.json), mismas filas de train (BAJA+1, BAJA+2 y fracción r de CONTINUA),
mismas 6 semillas, rank medio de las 6, ccajas corregida, sin auxiliar ni lag2; solo cambia el objetivo (binario BAJA+1/BAJA+2 vs CONTINUA en lugar de multiclase).
Salidas (k=12000, un archivo cada una) para enviar al Public y comparar de a pares:
  exp026_mc_k12000   ranking del 010 (multiclase, ya entrenado)          = control
  exp026_b12_k12000  binario con ambas bajas                              = tratamiento
  exp026_mix_k12000  rank medio de los dos
Uso (raíz del repo): venv/bin/python competencia/experimentos/026_binario_ambas_bajas/final_b12.py   |   tail -f competencia/experimentos/026_binario_ambas_bajas/final_log.txt"""
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
config.CORREGIR_CCAJAS = True
from config import ID_COL, MES_SCORING, SEMILLAS  # noqa: E402
from multiclase import etiquetas, filas  # noqa: E402
from optuna_run import es_hist  # noqa: E402
from pool import cargar  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402
from validacion import PARAMS_BASE, xy  # noqa: E402

K, LOG = 12000, AQUI / "final_log.txt"


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    js = json.loads((A005 / "mejores_trials.json").read_text())
    cfg = {tuple(k.split("_")): (d["r"], d["num_boost_round"], {**PARAMS_BASE, **{a: b for a, b in d.items() if a not in ("r", "num_boost_round")}}) for k, d in js.items()}
    semillas = (SEMILLAS + [121109])[:6]                                  # las mismas de 010/final.py
    dt = cargar([202103, 202104, 202105, 202106], negocio=True); score = cargar([MES_SCORING], solo_con_target=False, negocio=True)
    Xt0, _ = xy(dt); y3 = etiquetas(dt); yb = (y3 >= 1).astype(int)
    cols = {"M0": [c for c in Xt0.columns if not es_hist(c)], "M1": (A005 / "sel" / "top150_final.txt").read_text().split()}
    escribir(f"\n===== 026b {time.strftime('%Y-%m-%d %H:%M')} | train {dt.shape} (positivos BAJA+1/2: {yb.sum()}) | semillas {semillas} =====")
    t0, P = time.time(), {}
    for (c, nombre), (r, rondas, params) in cfg.items():
        ps = []
        for s in semillas:
            keep = filas(y3, r, s)                                        # igual que en el multiclase
            ps.append(lgb.train({**params, "seed": s}, lgb.Dataset(dt.loc[keep, cols[c]], label=yb[keep]), num_boost_round=rondas).predict(score[cols[c]]))
        P[f"{c}_{nombre}"] = np.mean(ps, axis=0); escribir(f"listo {c} {nombre} ({(time.time()-t0)/60:.0f} min)")
    ids = score[ID_COL].values
    rk_b = np.mean([rankdata(p) / len(p) for p in P.values()], axis=0)
    (AQUI / "tmp").mkdir(exist_ok=True)
    pd.DataFrame({ID_COL: ids, "rank": rk_b, **P}).to_csv(AQUI / "tmp" / "proba_b12_202108.csv", index=False)
    mc = pd.read_csv(AQUI.parents[0] / "010_multiclase" / "tmp" / "proba_202108.csv", usecols=[ID_COL, "rank"]).set_index(ID_COL).loc[ids, "rank"].values
    mix = (rankdata(mc) + rankdata(rk_b)) / (2 * len(ids))
    tops = {"mc": top_k_ids(ids, mc, K), "b12": top_k_ids(ids, rk_b, K), "mix": top_k_ids(ids, mix, K)}
    for n, t in tops.items():
        escribir(guardar_submit(t, f"exp026_{n}_k{K}").name)
    sol = lambda a, b: len(set(tops[a]) & set(tops[b])) / K  # noqa: E731
    escribir(f"solapamiento top-{K}: mc-b12 {sol('mc', 'b12'):.1%} | mc-mix {sol('mc', 'mix'):.1%} | b12-mix {sol('b12', 'mix'):.1%}")
    escribir("[026b] terminado")
