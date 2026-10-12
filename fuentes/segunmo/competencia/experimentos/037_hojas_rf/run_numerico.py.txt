"""037f-diagnóstico (POSTERIOR al primer resultado, exploratorio) — mismo diseño que run.py pero las hojas entran como columnas NUMÉRICAS (no categóricas).
Motivo: con categóricas el modelo cayó −46M en las 8 semillas; se quiere distinguir "la técnica no sirve" de "mi codificación sobreajusta". Se cuenta como un test más de la familia (m=9).
F0 se lee de resultados.csv (mismas semillas y mismas filas: idéntico). Salidas: resultados_numerico.csv, comparacion_numerico.csv, log_numerico.txt.
---- docstring original ----
037f — hojas de Random Forest como features (profe 1.5, libro 20.10; plan COBERTURA.md §8, reglas fijadas antes de correr).
Sin fuga: el RF se entrena con 202103–04 (etiqueta BAJA+1) y sus índices de hoja se agregan como columnas CATEGÓRICAS; LightGBM entrena con 202105–06 (filas que el RF no vio)
y se valida en 202107. Dos variantes sobre las MISMAS filas de train: F0 = 855 columnas (M2); F1 = 855 + 100 columnas de hojas. 8 semillas pareadas (la semilla también sortea el RF).
RF: sklearn, 100 árboles, profundidad ≤ 8, min_samples_leaf 100, negativos submuestreados al 10% (como el undersampling del resto), columnas = M1 top150 (final).
Contexto adicional: nivel de F0 (2 meses de train) contra BASE de 037 (4 meses): cuánto se pierde por dejar 202103–04 solo para el RF.
Estadística: t pareado unilateral; decisión BH q=0.10 con m=8 sobre la familia completa con `bh_final.py`; pasa solo si BH Y Δ ≥ +3M.
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/037_hojas_rf/run.py   |   tail -f competencia/experimentos/037_hojas_rf/log.txt"""
import importlib.util
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("m37", AQUI.parents[0] / "037_huecos_abc" / "run.py"); m37 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m37)
t028 = m37.t028
from multiclase import gan_media  # noqa: E402
from reevaluar import SEMILLAS_20  # noqa: E402
from validacion import PARAMS_BASE  # noqa: E402

LOG, S8, N_ARB = AQUI / "log_numerico.txt", SEMILLAS_20[2:10], 100


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    d = json.loads((t028.A005 / "mejores_trials.json").read_text())["M1_top1"]
    r, rondas = d["r"], d["num_boost_round"]
    params = {**PARAMS_BASE, **{a: b for a, b in d.items() if a not in ("r", "num_boost_round")}}
    drop = {l.split("\t")[0] for l in (AQUI.parents[0] / "031_final_todas_lags" / "drop_psi.txt").read_text().splitlines() if l}
    t0 = time.time()
    dt = t028.construir([202103, 202104, 202105, 202106]); dv = t028.construir([202107], solo_con_target=False)
    y = (dt["clase_ternaria"] == "BAJA+1").astype(int).values; yv = (dv["clase_ternaria"] == "BAJA+1").astype(int).values
    todas = [c for c in dt.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria") and not c.startswith("canario") and c not in drop]
    cols_rf = (t028.A005 / "sel" / "top150_final.txt").read_text().split()
    m_rf = dt["foto_mes"].isin([202103, 202104]).values; m_gb = ~m_rf
    escribir(f"\n===== 037f {time.strftime('%Y-%m-%d %H:%M')} | RF con 202103–04 ({int(m_rf.sum())} filas, {int(y[m_rf].sum())} positivos) | LightGBM con 202105–06 ({int(m_gb.sum())} filas, {int(y[m_gb].sum())} positivos) | valid 202107 =====")
    base = pd.read_csv(AQUI.parents[0] / "037_huecos_abc" / "resultados.csv").query("variante == 'BASE'").set_index("semilla")
    F0 = pd.read_csv(AQUI / "resultados.csv").query("variante == 'F0'").set_index("semilla")
    res = []
    for s in S8:
        rng = np.random.RandomState(s)
        idx = np.where(m_rf & ((y == 1) | (rng.rand(len(y)) < 0.1)))[0]                       # RF: positivos + 10% de negativos
        rf = RandomForestClassifier(n_estimators=N_ARB, max_depth=8, min_samples_leaf=100, n_jobs=-1, random_state=s)
        rf.fit(dt.iloc[idx][cols_rf], y[idx])
        nombres = [f"hoja_{i}" for i in range(N_ARB)]
        H_gb = pd.DataFrame(rf.apply(dt.loc[m_gb, cols_rf]).astype("int32"), columns=nombres, index=dt.index[m_gb])
        H_v = pd.DataFrame(rf.apply(dv[cols_rf]).astype("int32"), columns=nombres, index=dv.index)
        Xg, yg = dt.loc[m_gb, todas], y[m_gb]
        keep = (yg == 1) | (np.random.RandomState(s + 1).rand(len(yg)) < r)
        g = {"F0": float(F0.loc[s, "M"])}
        Xtr, Xva = pd.concat([Xg, H_gb], axis=1), pd.concat([dv[todas], H_v], axis=1)
        ds = lgb.Dataset(Xtr.iloc[np.where(keep)[0]], label=yg[keep])                 # sin categorical_feature: las hojas son enteros ordinales
        p = lgb.train({**params, "seed": s}, ds, num_boost_round=rondas).predict(Xva)
        res.append({"semilla": s, "variante": "F2_numerico", "M": gan_media(yv, p), "auc": roc_auc_score(yv, p), "n_cols": Xtr.shape[1]}); g["F2"] = res[-1]["M"]
        escribir(f"[s={s}] F0 {g['F0']:.1f} | F2 (+hojas numéricas) {g['F2'] - g['F0']:+.1f} ({(time.time()-t0)/60:.0f} min)")
        pd.DataFrame(res).to_csv(AQUI / "resultados_numerico.csv", index=False)
    R = pd.DataFrame(res).set_index("semilla"); dd = R.M - F0.loc[R.index, "M"]; t, p2 = stats.ttest_1samp(dd, 0.0); p1 = p2 / 2 if t > 0 else 1 - p2 / 2
    T = pd.DataFrame([{"variante": "037f_hojas_rf_numerico(posterior)", "delta_M": dd.mean(), "ee": dd.std() / np.sqrt(len(dd)), "pares+": f"{int((dd > 0).sum())}/{len(dd)}",
                       "delta_auc": (R.auc - F0.loc[R.index, "auc"]).mean(), "p_unilateral": p1}])
    T.round(4).to_csv(AQUI / "comparacion_numerico.csv", index=False)
    escribir("\nF2 (hojas numéricas) contra F0 (pareado):\n" + T.round(4).to_string(index=False) + "\n[037f numérico] terminado")
