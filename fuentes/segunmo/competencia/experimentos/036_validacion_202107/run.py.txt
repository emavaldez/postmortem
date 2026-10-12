"""036 — VALIDACIÓN LIMPIA EN 202107 con BAJA+1 como tarea proxy (respuesta a la revisión de sesgos del 2026-10-09).
Por qué: todas las decisiones se tomaron sobre 202105/202106 (dos meses, uno con aguinaldo y con la ola de salidas de clientes con préstamo y mora), y L/B2 tienen los targets solapados.
202107 es el mes más cercano a 202108, sin aguinaldo, con la ola, y de él se conoce BAJA+1 (quién no está en 202108). Tarea: predecir BAJA+1 en 202107 entrenando con 202103–202106
(BAJA+1 conocido en todos): sin solapamiento (las etiquetas de train miran hasta 202107; la de 202107 mira 202108).
Limitación: BAJA+1 no es BAJA+2 (el negocio paga BAJA+2); ambas miden "propensión a irse" con las mismas features, pero la ola de 202108 pesa distinto. Métrica: ganancia con la misma función
(+1.072.500 por acierto, −27.500 por envío) sobre BAJA+1 y corte por cantidad (media sobre k=8000..15000; 1.103 positivos, parecido a los 1.098 de BAJA+2 en 202106), más AUC.
Binario (BAJA+1 vs resto), hiperparámetros de M1 top1 de 005 (r sobre los negativos), 5 semillas (SEMILLAS_20[2:7]).
Variantes (un cambio por vez):
  V0 M1 top150 (final de 017/010) | V1 = V0 + lag2 de 50 variables (el pool del final anterior) | V2 = 855 columnas (M2) | V2_md50 = V2 con min_data_in_leaf=50 (como el final)
  V3 = V2 sin las 2 columnas de calendario | V4 = V0 sin las 2 columnas de calendario | V5 = V2 con peso 2 en 202106 (recencia)
Diagnóstico extra: recall a k=12000 de los positivos del grupo "préstamo y (status 6 o saldo<0)" y del resto.
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/036_validacion_202107/run.py   |   tail -f competencia/experimentos/036_validacion_202107/log.txt"""
import importlib.util
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(AQUI.parents[0] / "005_optuna"))
spec = importlib.util.spec_from_file_location("t028", AQUI.parents[0] / "028_todas_lags" / "run.py"); t028 = importlib.util.module_from_spec(spec); spec.loader.exec_module(t028)
import config  # noqa: E402
config.CORREGIR_CCAJAS = True
from multiclase import gan_media  # noqa: E402
from reevaluar import SEMILLAS_20  # noqa: E402
from validacion import PARAMS_BASE  # noqa: E402

LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
SEMILLAS_036, CALENDARIO, K_DIAG = SEMILLAS_20[2:7], ["Master_fultimo_cierre", "Visa_fultimo_cierre"], 12000


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    d = json.loads((t028.A005 / "mejores_trials.json").read_text())["M1_top1"]
    r, rondas = d["r"], d["num_boost_round"]
    params = {**PARAMS_BASE, **{a: b for a, b in d.items() if a not in ("r", "num_boost_round")}}
    drop = {l.split("\t")[0] for l in (AQUI.parents[0] / "031_final_todas_lags" / "drop_psi.txt").read_text().splitlines() if l}
    dt = t028.construir([202103, 202104, 202105, 202106]); dv = t028.construir([202107], solo_con_target=False)
    yt, yv = (dt["clase_ternaria"] == "BAJA+1").astype(int).values, (dv["clase_ternaria"] == "BAJA+1").astype(int).values
    todas = [c for c in dt.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria") and not c.startswith("canario") and c not in drop]
    base = (t028.A005 / "sel" / "top150_final.txt").read_text().split()
    sets = {"V0_top150": base, "V1_lag2_50": base + t028.LAG2_50, "V2_todas": todas, "V2_md50": todas,
            "V3_todas_sin_cal": [c for c in todas if c not in CALENDARIO], "V4_top150_sin_cal": [c for c in base if c not in CALENDARIO], "V5_todas_w2": todas}
    extra = {"V2_md50": {"min_data_in_leaf": 50}}
    peso = np.where(dt["foto_mes"].values == 202106, 2.0, 1.0)
    seg = ((dv["mprestamos_personales"].fillna(0) > 0) & ((dv["Master_status"] == 6) | (dv["Visa_status"] == 6) | (dv["mcuentas_saldo"] < 0))).values
    escribir(f"\n===== 036 {time.strftime('%Y-%m-%d %H:%M')} | train {dt.shape} ({yt.sum()} BAJA+1) | valid 202107 {dv.shape} ({yv.sum()} BAJA+1; en el grupo préstamo&mora: {int((yv * seg).sum())}) | "
             f"{len(SEMILLAS_036)} semillas | columnas: " + ", ".join(f"{n} {len(c)}" for n, c in sets.items()) + " =====")
    res, t0 = [], time.time()
    for s in SEMILLAS_036:
        keep = (yt == 1) | (np.random.RandomState(s).rand(len(yt)) < r); g = {}
        for n, cols in sets.items():
            ds = lgb.Dataset(dt.loc[keep, cols], label=yt[keep], weight=peso[keep] if n == "V5_todas_w2" else None)
            p = lgb.train({**params, **extra.get(n, {}), "seed": s}, ds, num_boost_round=rondas).predict(dv[cols])
            top = np.argsort(-p, kind="stable")[:K_DIAG]; en = np.zeros(len(p), bool); en[top] = True
            res.append({"semilla": s, "variante": n, "M": gan_media(yv, p), "auc": roc_auc_score(yv, p),
                        "recall_seg": (yv * seg * en).sum() / max((yv * seg).sum(), 1), "recall_resto": (yv * ~seg * en).sum() / max((yv * ~seg).sum(), 1)})
            g[n] = res[-1]["M"]
        escribir(f"[s={s}] V0 {g['V0_top150']:.1f} | " + " | ".join(f"{n.split('_')[0]}{'' if n.count('_') < 2 and n not in ('V2_md50',) else '*'} {v - g['V0_top150']:+.1f}" for n, v in g.items() if n != "V0_top150") + f" ({(time.time()-t0)/60:.0f} min)")
        pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.DataFrame(res); p = r_.pivot_table(index="semilla", columns="variante", values="M")
    niveles = r_.groupby("variante")[["M", "auc", "recall_seg", "recall_resto"]].mean().round(4)
    comp = []
    for a, b in [("V1_lag2_50", "V0_top150"), ("V2_todas", "V1_lag2_50"), ("V2_todas", "V0_top150"), ("V2_md50", "V2_todas"), ("V3_todas_sin_cal", "V2_todas"),
                 ("V4_top150_sin_cal", "V0_top150"), ("V5_todas_w2", "V2_todas")]:
        dd = p[a] - p[b]
        comp.append({"comparacion": f"{a} - {b}", "delta_M": dd.mean(), "ee": dd.std() / np.sqrt(len(dd)), "pares_positivos": f"{int((dd > 0).sum())}/{len(dd)}",
                     "delta_auc": (r_[r_.variante == a].set_index("semilla").auc - r_[r_.variante == b].set_index("semilla").auc).mean()})
    comp = pd.DataFrame(comp).round(4); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (ganancia media en M ARS sobre BAJA+1, AUC, recall a k=12000 del grupo préstamo&mora y del resto):\n" + niveles.to_string())
    escribir("\nDiferencias pareadas:\n" + comp.to_string(index=False)); escribir("[036] terminado")
