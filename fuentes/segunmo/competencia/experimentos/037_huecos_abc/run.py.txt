"""037a/b/c — primer lote del plan de cierre de huecos (COBERTURA.md §7–8; reglas fijadas ANTES de correr).
Harness de 036: train 202103–06, valid 202107, tarea BAJA+1 (proxy limpio), binario, hiperparámetros de M1 top1 (min_data 27, r=0.0986, 688 rondas), 8 semillas pareadas (SEMILLAS_20[2:10]).
Línea base BASE = las 855 columnas de M2 (sin las 8 con PSI>0.20). Una sola cosa por variante:
  037a_max  canarios: columnas con importancia (gain, media de 3 modelos solo con train) > MÁXIMO de 20 canarios U(0,1)
  037a_p90  canarios: columnas con importancia > percentil 90 de los canarios
  037b      quitar 202103 del train (entrenar con 202104–06)
  037c      deflactar montos: factor mensual f_m = mediana entre variables de monto de [mediana del mes m entre clientes con valor>0 / la de 202103] (sin target);
            monto/f_m, _lag1/f_{m-1}, _lag2/f_{m-2}, diferencias y ratios recalculados; n_*/r_* con montos /f_m
Estadística (fijada): t pareado unilateral (gl=7); Benjamini–Hochberg q=0.10 con m=8 (tamaño planeado de la familia completa del plan); pasa si p<=q*rango/8 Y delta >= +3M.
La confirmación en L/B2 con BAJA+2 se hace aparte, solo para las que pasen.
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/037_huecos_abc/run.py   |   tail -f competencia/experimentos/037_huecos_abc/log.txt"""
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy import stats
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
SEMILLAS_037, M_FAMILIA, Q, MIN_DELTA = SEMILLAS_20[2:10], 8, 0.10, 3.0
ES_MONTO = re.compile(r"^(m|Master_m|Visa_m)[a-z_]")
HIST = re.compile(r"_(lag1|lag2|d1|d2|r1|r2)$")
DERIV_MONTO = ["n_ingresos", "n_egresos", "n_neto", "n_inversiones", "n_deuda", "n_patrimonio", "n_saldo_paquete", "n_limite_total", "n_saldo_tarjetas",
               "n_comisiones", "n_descuentos", "r_consumo_tarjetas", "r_payroll_por_trx", "r_saldo_por_producto", "r_rentab_por_producto", "r_visa_ticket", "r_master_ticket"]


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def previo(m):
    return m - 1 if m % 100 > 1 else m - 89


def factores_mensuales(frames: list, monto: list) -> dict:
    """f_m = mediana entre variables de [mediana de v (v>0) en el mes m / la de 202103]. Solo features, sin target."""
    med = {}
    for d in frames:
        for m, g in d.groupby("foto_mes"):
            med[m] = {v: g[v][g[v] > 0].median() for v in monto if (g[v] > 0).sum() >= 2000}
    base = med[202103]
    f = {}
    for m in sorted(med):
        r = [med[m][v] / base[v] for v in med[m] if v in base and base[v] > 0 and med[m][v] > 0]
        f[m] = float(np.median(r))
    return f


def deflactar(df: pd.DataFrame, f: dict, monto: list) -> pd.DataFrame:
    out = df.copy()
    m = df["foto_mes"]
    ft, f1, f2 = m.map(f).values, m.map(lambda x: f.get(previo(x), f[x])).values, m.map(lambda x: f.get(previo(previo(x)), f[x])).values
    for v in monto:
        out[v] = (df[v] / ft).astype("float32")
        for k, ff in (("lag1", f1), ("lag2", f2)):
            if f"{v}_{k}" in df.columns:
                out[f"{v}_{k}"] = (df[f"{v}_{k}"] / ff).astype("float32")
        for k, lag in (("1", "lag1"), ("2", "lag2")):
            if f"{v}_{lag}" in df.columns:
                if f"{v}_d{k}" in df.columns:
                    out[f"{v}_d{k}"] = (out[v] - out[f"{v}_{lag}"]).astype("float32")
                if f"{v}_r{k}" in df.columns:
                    out[f"{v}_r{k}"] = (out[v] / out[f"{v}_{lag}"].replace(0, np.nan) - 1).astype("float32")
    for c in DERIV_MONTO:
        if c in df.columns:
            out[c] = (df[c] / ft).astype("float32")
    return out


def importancia_canarios(X, y, r, params, rondas, semillas, n_can=20):
    gs = []
    for s in semillas:
        keep = (y == 1) | (np.random.RandomState(s).rand(len(y)) < r)
        Xc = X.loc[keep].copy()
        can = pd.DataFrame(np.random.RandomState(s + 7).rand(len(Xc), n_can).astype("float32"), columns=[f"canario_{i}" for i in range(n_can)], index=Xc.index)
        m = lgb.train({**params, "seed": s}, lgb.Dataset(pd.concat([Xc, can], axis=1), label=y[keep]), num_boost_round=rondas)
        g = pd.Series(m.feature_importance("gain"), index=list(Xc.columns) + list(can.columns)); gs.append(g / g.sum())
    return pd.concat(gs, axis=1).mean(axis=1)


if __name__ == "__main__":
    d = json.loads((t028.A005 / "mejores_trials.json").read_text())["M1_top1"]
    r, rondas = d["r"], d["num_boost_round"]
    params = {**PARAMS_BASE, **{a: b for a, b in d.items() if a not in ("r", "num_boost_round")}}
    drop = {l.split("\t")[0] for l in (AQUI.parents[0] / "031_final_todas_lags" / "drop_psi.txt").read_text().splitlines() if l}
    t0 = time.time()
    dt = t028.construir([202103, 202104, 202105, 202106]); dv = t028.construir([202107], solo_con_target=False)
    yt, yv = (dt["clase_ternaria"] == "BAJA+1").astype(int).values, (dv["clase_ternaria"] == "BAJA+1").astype(int).values
    todas = [c for c in dt.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria") and not c.startswith("canario") and c not in drop]
    monto = [c for c in dt.columns if ES_MONTO.match(c) and not HIST.search(c)]
    f = factores_mensuales([dt, dv], monto)
    dtd, dvd = deflactar(dt, f, monto), deflactar(dv, f, monto)
    escribir(f"\n===== 037 a/b/c {time.strftime('%Y-%m-%d %H:%M')} | train {dt.shape} ({yt.sum()} BAJA+1) | valid 202107 ({yv.sum()} BAJA+1) | {len(SEMILLAS_037)} semillas | {len(todas)} columnas =====")
    escribir(f"montos: {len(monto)} variables | factor de precios por mes (202103=1): " + ", ".join(f"{m}: {v:.3f}" for m, v in f.items()))
    imp = importancia_canarios(dt[todas], yt, r, params, rondas, SEMILLAS_037[:3])
    can = imp[imp.index.str.startswith("canario_")]; real = imp.drop(can.index)
    cols_max, cols_p90 = list(real.index[real > can.max()]), list(real.index[real > can.quantile(0.9)])
    escribir(f"canarios: gain máx {can.max():.5f}, p90 {can.quantile(0.9):.5f} | columnas > máx: {len(cols_max)} de {len(todas)} | > p90: {len(cols_p90)}  ({(time.time()-t0)/60:.0f} min)")
    pd.Series(cols_max).to_csv(AQUI / "columnas_canario_max.txt", index=False, header=False); pd.Series(cols_p90).to_csv(AQUI / "columnas_canario_p90.txt", index=False, header=False)
    mask_b = (dt["foto_mes"] != 202103).values
    # (nombre, X_train, y_train, X_valid, columnas)
    variantes = {"BASE": (dt, yt, dv, todas), "037a_max": (dt, yt, dv, cols_max), "037a_p90": (dt, yt, dv, cols_p90),
                 "037b_sin202103": (dt[mask_b], yt[mask_b], dv, todas), "037c_deflactado": (dtd, yt, dvd, todas)}
    res = []
    for s in SEMILLAS_037:
        g = {}
        for n, (Xt, y, Xv, cols) in variantes.items():
            keep = (y == 1) | (np.random.RandomState(s).rand(len(y)) < r)
            p = lgb.train({**params, "seed": s}, lgb.Dataset(Xt.loc[keep, cols] if isinstance(Xt, pd.DataFrame) else Xt[keep][cols], label=y[keep]), num_boost_round=rondas).predict(Xv[cols])
            res.append({"semilla": s, "variante": n, "M": gan_media(yv, p), "auc": roc_auc_score(yv, p), "n_cols": len(cols)}); g[n] = res[-1]["M"]
        escribir(f"[s={s}] BASE {g['BASE']:.1f} | " + " | ".join(f"{n} {v - g['BASE']:+.1f}" for n, v in g.items() if n != "BASE") + f" ({(time.time()-t0)/60:.0f} min)")
        pd.DataFrame(res).to_csv(CSV, index=False)
    R = pd.DataFrame(res); P = R.pivot_table(index="semilla", columns="variante", values="M"); A = R.pivot_table(index="semilla", columns="variante", values="auc")
    filas = []
    for v in [c for c in P.columns if c != "BASE"]:
        dd = P[v] - P["BASE"]; t, p2 = stats.ttest_1samp(dd, 0.0); p1 = p2 / 2 if t > 0 else 1 - p2 / 2
        filas.append({"variante": v, "n_cols": int(R[R.variante == v].n_cols.iloc[0]), "delta_M": dd.mean(), "ee": dd.std() / np.sqrt(len(dd)), "pares+": f"{int((dd > 0).sum())}/{len(dd)}",
                      "delta_auc": (A[v] - A["BASE"]).mean(), "p_unilateral": p1})
    T = pd.DataFrame(filas).sort_values("p_unilateral").reset_index(drop=True)
    T["umbral_BH"] = Q * (T.index + 1) / M_FAMILIA
    T["pasa"] = (T.p_unilateral <= T.umbral_BH) & (T.delta_M >= MIN_DELTA)
    T.round(4).to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (ganancia media en M ARS sobre BAJA+1):\n" + R.groupby("variante")[["M", "auc", "n_cols"]].mean().round(4).to_string())
    escribir("\nContra BASE (pareado; BH con m=8 y q=0.10; mínimo +3M):\n" + T.round(4).to_string(index=False)); escribir("[037 a/b/c] terminado")
