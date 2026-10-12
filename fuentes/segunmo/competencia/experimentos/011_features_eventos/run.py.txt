"""011 — cuatro ideas de feature engineering, cada una sumada por separado a la MISMA base multiclase (un cambio por vez), folds B y Bh
(train con historia real; A no sirve: su train no tiene historia). Modelo = B1: multiclase con score P(BAJA+2)/(1-P(BAJA+1)), hiperparámetros y rondas
de M1 top1 de Optuna, columnas base = top150 por fold (M1), filas = BAJA+1, BAJA+2 y fracción r de CONTINUA, ccajas corregida. 10 semillas nuevas.
  V0  base (M1 top150)
  V1  + agregados de cambios sobre las 50 variables con historia: cuántas cayeron a la mitad, cuántas pasaron a cero, cuántas subieron..., (6 cols `g_*`)
  V2  + lag1/delta1/ratio1 de las 20 features derivadas (n_*, r_*) más importantes (ranking de importancias_Bh: solo train de 202104) (60 cols)
  V3  + eventos de productos entre mes anterior y actual: perdidos, ganados, dejó payroll/consumo/homebanking (8 cols `e_*`)
  V4  + mcomisiones_mantenimiento normalizada por la mediana del mes (y se quita la cruda si estaba) (1 col)
Ganancia = media sobre k=8000..15000 (M ARS). Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/011_features_eventos/run.py
Progreso: tail -f competencia/experimentos/011_features_eventos/log.txt"""
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from config import TARGET_COL  # noqa: E402
from features import agregados_cambios, comisiones_normalizadas, eventos_productos  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from historia import lag_derivadas, lags_crudos  # noqa: E402
from pool import VARS, cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402
from validacion import KS  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
FOLDS = {"B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
SEMILLAS_011 = SEMILLAS_20[2:12]
CLASES = {"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}
TOP20 = [c for c in pd.read_csv(A005 / "sel" / "importancias_Bh.csv", index_col=0).index
         if c.startswith(("n_", "r_")) and not any(s in c for s in ("_lag", "_r1", "_d1"))][:20]
EV_VARS = ["cproductos", "mpayroll", "cpayroll_trx", "Visa_mconsumototal", "Master_mconsumototal", "chomebanking_transacciones",
           "ccuenta_corriente", "ccaja_ahorro", "ctarjeta_debito", "ctarjeta_visa", "ctarjeta_master", "cprestamos_personales",
           "cprestamos_prendarios", "cprestamos_hipotecarios", "cplazo_fijo", "cinversion1", "cinversion2", "cseguro_vida", "cseguro_auto",
           "cseguro_vivienda", "cseguro_accidentes_personales", "ccaja_seguridad"]
EXTRAS = {"V1_agregados": lambda d: agregados_cambios(d, VARS),
          "V2_lags_derivadas": lambda d: lag_derivadas(d, TOP20),
          "V3_eventos": lambda d: eventos_productos(d, lags_crudos(d, EV_VARS)),
          "V4_comisiones_norm": comisiones_normalizadas}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def armar(d, cols, extra):
    if extra is None:
        return d[cols]
    e = extra(d)
    base = [c for c in cols if not (c == "mcomisiones_mantenimiento" and "mcomisiones_mant_norm" in e.columns)]
    return pd.concat([d[base], e], axis=1)


if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]
    filas, t0 = [], time.time()
    escribir(f"\n===== 011 {time.strftime('%Y-%m-%d %H:%M')} | r={r:.3f} rondas={rondas} | {len(SEMILLAS_011)} semillas | TOP20 derivadas: {TOP20[:5]}... =====")
    for fold, (mt, mv) in FOLDS.items():
        dt, dv = cargar(mt, negocio=True), cargar([mv], negocio=True)
        cols = (A005 / "sel" / f"top150_{fold}.txt").read_text().split()
        y3 = dt[TARGET_COL].map(CLASES).values; yv = (dv[TARGET_COL] == "BAJA+2").astype(int).values
        variantes = {"V0_base": None, **EXTRAS}
        data = {n: (armar(dt, cols, f), armar(dv, cols, f)) for n, f in variantes.items()}
        escribir(f"[{fold}] columnas: " + ", ".join(f"{n} {data[n][0].shape[1]}" for n in data))
        for s in SEMILLAS_011:
            keep = (y3 >= 1) | (np.random.RandomState(s).rand(len(y3)) < r); g = {}
            for n, (Xt, Xv) in data.items():
                m = lgb.train({**params, "objective": "multiclass", "num_class": 3, "seed": s}, lgb.Dataset(Xt[keep], label=y3[keep]), num_boost_round=rondas)
                pm = m.predict(Xv); p = pm[:, 2] / np.clip(1 - pm[:, 1], 1e-6, None)
                acum = ganancia_acumulada(yv, p)
                filas.append({"fold": fold, "semilla": s, "variante": n, "auc": roc_auc_score(yv, p),
                              "gan_media_k": np.mean([acum[k - 1] for k in KS]), "gan_k11500": acum[11500 - 1]})
                g[n] = filas[-1]["gan_media_k"] / 1e6
            escribir(f"[{fold} s={s}] V0 {g['V0_base']:.1f} | " + " | ".join(f"{n[:2]} {v - g['V0_base']:+.1f}" for n, v in g.items() if n != "V0_base")
                     + f" ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(filas).to_csv(CSV, index=False)
    res = pd.DataFrame(filas); res.to_csv(CSV, index=False); res["M"] = res.gan_media_k / 1e6
    p = res.pivot_table(index=["fold", "semilla"], columns="variante", values="M"); comp = []
    for v in EXTRAS:
        d = (p[v] - p["V0_base"]).groupby("fold"); fila = {"variante": v}
        for f in FOLDS:
            fila[f"{f}_delta"], fila[f"{f}_ee"] = d.mean()[f], d.std()[f] / np.sqrt(len(SEMILLAS_011))
        fila["pares_positivos"] = f"{int(((p[v] - p['V0_base']) > 0).sum())}/{len(p)}"
        comp.append(fila)
    comp = pd.DataFrame(comp).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + res.groupby(["variante", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas vs V0:\n" + comp.to_string(index=False)); escribir("[011] terminado")
