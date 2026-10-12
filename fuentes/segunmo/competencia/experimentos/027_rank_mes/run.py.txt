"""027 — normalizar las variables por su RANK dentro del mes, en [-1, 1] (rank = 2*percentil-1), REEMPLAZANDO a las crudas. (003c solo AGREGÓ percentiles de 50 variables: -4.6M en B.)
Idea: los montos son nominales y la inflación los desplaza mes a mes; un corte "saldo < X" aprendido en 202103-06 no significa lo mismo en 202108. El rank dentro del mes es invariante a eso.
El fold B valida a 2 meses del último mes de train (como el final con 202108), así que sí puede verlo.
Variantes sobre el multiclase M1 top1 de 005 (score condicional, columnas M1 top150 por fold):
  V0 crudas (referencia) | V1 todas las columnas continuas (más de 20 valores distintos) por rank del mes | V2 solo las de MONTO (nombre que empieza con m, Master_m o Visa_m, y sus _lag1/_d1/_r1).
NaN se conserva. El rank se calcula con las filas de cada mes por separado (train y valid). Folds A, B, Bh; 5 semillas (SEMILLAS_20[2:7]); ganancia = media sobre k=8000..15000 (M ARS).
Uso (raíz del repo): venv/bin/python competencia/experimentos/027_rank_mes/run.py   |   tail -f competencia/experimentos/027_rank_mes/log.txt"""
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
A005 = AQUI.parents[0] / "005_optuna"
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(A005))
import config  # noqa: E402
from config import MES_COL  # noqa: E402
from multiclase import entrenar, etiquetas, filas, gan_media, score_cond  # noqa: E402
from pool import cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
FOLDS = {"A": ([202103], 202105), "B": ([202103, 202104], 202106), "Bh": ([202104], 202106)}
SEMILLAS_027 = SEMILLAS_20[2:7]
ES_MONTO = re.compile(r"^(m|Master_m|Visa_m)[a-z_]")


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def a_rank(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Reemplaza cada columna por 2*percentil-1 dentro de su foto_mes (NaN se conserva)."""
    X = df[cols].copy()
    X[cols] = 2 * df.groupby(MES_COL)[cols].rank(pct=True) - 1
    return X


if __name__ == "__main__":
    r, rondas, params = configs()[("M1", "top1")]
    res, t0 = [], time.time()
    escribir(f"\n===== 027 {time.strftime('%Y-%m-%d %H:%M')} | {len(SEMILLAS_027)} semillas =====")
    for fold, (mt, mv) in FOLDS.items():
        dt, dv = cargar(mt, negocio=True), cargar([mv], negocio=True)
        cols = (A005 / "sel" / f"top150_{fold}.txt").read_text().split()
        cont = [c for c in cols if dt[c].nunique() > 20]
        monto = [c for c in cont if ES_MONTO.match(c)]
        escribir(f"[{fold}] columnas {len(cols)}: continuas {len(cont)}, de monto {len(monto)}")
        datos = {"V0_crudas": (dt[cols], dv[cols])}
        for nombre, sel in (("V1_rank_todas", cont), ("V2_rank_montos", monto)):
            Xt, Xv = dt[cols].copy(), dv[cols].copy()
            Xt[sel], Xv[sel] = a_rank(dt, sel), a_rank(dv, sel)
            datos[nombre] = (Xt, Xv)
        y3, yv = etiquetas(dt), (dv["clase_ternaria"] == "BAJA+2").astype(int).values
        for s in SEMILLAS_027:
            keep, g = filas(y3, r, s), {}
            for n, (Xt, Xv) in datos.items():
                g[n] = gan_media(yv, score_cond(entrenar(params, Xt, y3, keep, s, rondas).predict(Xv)))
                res.append({"fold": fold, "semilla": s, "variante": n, "M": g[n]})
            escribir(f"[{fold} s={s}] V0 {g['V0_crudas']:.1f} | V1 {g['V1_rank_todas'] - g['V0_crudas']:+.1f} | V2 {g['V2_rank_montos'] - g['V0_crudas']:+.1f} ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(res).to_csv(CSV, index=False)
    r_ = pd.DataFrame(res); p = r_.pivot_table(index=["fold", "semilla"], columns="variante", values="M"); filas_ = []
    for v in ("V1_rank_todas", "V2_rank_montos"):
        d = (p[v] - p["V0_crudas"]).groupby("fold")
        filas_.append({"variante": f"{v} - V0", **{f"{f}_delta": d.mean()[f] for f in FOLDS}, **{f"{f}_ee": d.std()[f] / np.sqrt(len(SEMILLAS_027)) for f in FOLDS},
                       "pares_positivos": f"{int(((p[v] - p['V0_crudas']) > 0).sum())}/{len(p)}"})
    comp = pd.DataFrame(filas_).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + r_.groupby(["variante", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas vs crudas:\n" + comp.to_string(index=False)); escribir("[027] terminado")
