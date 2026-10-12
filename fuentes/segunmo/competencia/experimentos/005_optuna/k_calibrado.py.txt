"""005 — ¿se puede elegir k corrigiendo el efecto del undersampling sobre las probabilidades?
El undersampling (se conservan todos los positivos y una fracción r de negativos) infla la probabilidad: q = p/(p + r(1-p)).
Se invierte: p = q r / (1 - q + q r). Con p corregida, cada cliente aporta en esperanza 1.0725M p - 27.5k (1-p) = 1.1M p - 27.5k,
así que el k que maximiza la ganancia esperada es el número de clientes con p >= 0.025 (punto de equilibrio de la cátedra).
Se valida en los folds A, B y Bh: ¿el k estimado se parece al k real óptimo y cuánto se pierde de usarlo?
Uso (raíz del repo): venv/bin/python competencia/experimentos/005_optuna/k_calibrado.py"""
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from optuna_run import PARAMS_BASE, es_hist  # noqa: E402
from reevaluar import FOLDS, SEMILLAS_REEVAL  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from pool import cargar  # noqa: E402
from validacion import xy  # noqa: E402

CFG = json.loads((AQUI / "mejores_trials.json").read_text())


def corregir(q, r):
    return q * r / (1 - q + q * r)


if __name__ == "__main__":
    filas = []
    for fold, (mt, mv) in FOLDS.items():
        (Xt, yt), (Xv, yv) = xy(cargar(mt, negocio=True)), xy(cargar([mv], negocio=True)); yt, yv = yt.values, yv.values
        cols = {"M0": [c for c in Xt.columns if not es_hist(c)], "M1": (AQUI / "sel" / f"top150_{fold}.txt").read_text().split()}
        pm, pc = [], []                                           # promedio de probabilidades crudas y de corregidas
        for nombre, c in CFG.items():
            r, rounds = c["r"], c["num_boost_round"]
            params = {**PARAMS_BASE, **{k: v for k, v in c.items() if k not in ("r", "num_boost_round")}}
            q = np.mean([lgb.train({**params, "seed": s}, lgb.Dataset(Xt.loc[(yt == 1) | (np.random.RandomState(s).rand(len(yt)) < r), cols[nombre[:2]]],
                         label=yt[(yt == 1) | (np.random.RandomState(s).rand(len(yt)) < r)]), num_boost_round=rounds).predict(Xv[cols[nombre[:2]]])
                         for s in SEMILLAS_REEVAL[:3]], axis=0)
            pm.append(q); pc.append(corregir(q, r))
        p_rank, p_cal = np.mean(pm, axis=0), np.mean(pc, axis=0)   # ranking con el promedio crudo (como en las entregas); calibradas para estimar k
        orden = np.argsort(-p_rank); acum = ganancia_acumulada(yv, p_rank)
        esperada = np.cumsum(1.1e6 * p_cal[orden] - 27_500)
        k_hat, k_real = int(esperada.argmax()) + 1, int(acum.argmax()) + 1
        filas.append({"fold": fold, "positivos_reales": int(yv.sum()), "positivos_esperados(sum p_cal)": round(float(p_cal.sum()), 0),
                      "k_estimado": k_hat, "k_real_optimo": k_real, "n_p_cal>=0.025": int((p_cal >= .025).sum()),
                      "gan@k_est": acum[k_hat - 1] / 1e6, "gan@k_real": acum.max() / 1e6, "gan@11500": acum[11499] / 1e6,
                      "gan_esperada@k_est": esperada.max() / 1e6})
        print(pd.DataFrame(filas).iloc[-1].to_dict(), flush=True)
    pd.DataFrame(filas).round(1).to_csv(AQUI / "k_calibrado.csv", index=False)
    print(pd.DataFrame(filas).round(1).to_string(index=False))
