"""016 — ¿el lag2 suma en el modelo MULTICLASE? (008b lo midió en el binario: +10.8 en L, -2.4 en B2.)
Ensemble de las 3 configuraciones M1 de 005 pasadas a multiclase (score condicional, rank medio), con y sin lag2/delta2/ratio2 de las 50 variables (+150 columnas).
Folds con lag2 real en el train: L (202105 -> 202106) y B2 (202104+05 -> 202106), con el solapamiento de targets en 202107 descrito en 008b (informa la diferencia pareada,
no el nivel). Columnas base = top150 de `sel/top150_Bh.txt` (selección con solo 202104: no incluye ningún mes de estos folds). ccajas corregida. 5 semillas (SEMILLAS_20[2:7]).
Control: lag2 con el bloque barajado dentro de cada mes. Ganancia = media sobre k=8000..15000 (M ARS).
Uso (raíz del repo): caffeinate -i venv/bin/python competencia/experimentos/016_multiclase_lag2/run.py   |   tail -f competencia/experimentos/016_multiclase_lag2/log.txt"""
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
from config import TARGET_COL  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from historia import agregar_historia_n, barajar_historia  # noqa: E402
from pool import VARS, cargar  # noqa: E402
from reevaluar import SEMILLAS_20, configs  # noqa: E402
from validacion import KS  # noqa: E402

config.CORREGIR_CCAJAS = True
LOG, CSV = AQUI / "log.txt", AQUI / "resultados.csv"
FOLDS = {"L": ([202105], 202106), "B2": ([202104, 202105], 202106)}
SEMILLAS_016 = SEMILLAS_20[2:7]
COLS_LAG2 = [f"{v}_{s}2" for v in VARS for s in ("lag", "d", "r")]
CLASES = {"CONTINUA": 0, "BAJA+1": 1, "BAJA+2": 2}


def escribir(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


if __name__ == "__main__":
    cfg = {k: v for k, v in configs().items() if k[1].startswith("top") and k[0] == "M1"}
    base = (A005 / "sel" / "top150_Bh.txt").read_text().split()
    filas, t0 = [], time.time()
    escribir(f"\n===== 016 {time.strftime('%Y-%m-%d %H:%M')} | semillas {SEMILLAS_016} | {len(cfg)} configs M1 =====")
    for fold, (mt, mv) in FOLDS.items():
        dt = agregar_historia_n(cargar(mt, negocio=True).copy(), VARS, 2)
        dv = agregar_historia_n(cargar([mv], negocio=True).copy(), VARS, 2)
        dtb = barajar_historia(dt, 852583, cols=COLS_LAG2)                 # control: lag2 barajado en train (valid intacto)
        y3 = dt[TARGET_COL].map(CLASES).values; yv = (dv[TARGET_COL] == "BAJA+2").astype(int).values
        variantes = {"V0_sin_lag2": (dt, dv, base), "V1_lag2": (dt, dv, base + COLS_LAG2), "V1c_lag2_barajado": (dtb, dv, base + COLS_LAG2)}
        for s in SEMILLAS_016:
            g, E = {}, {}
            for vn, (Dt, Dv, cols) in variantes.items():
                P = []
                for (c, nombre), (r, rondas, params) in cfg.items():
                    keep = (y3 >= 1) | (np.random.RandomState(s).rand(len(y3)) < r)
                    m = lgb.train({**params, "objective": "multiclass", "num_class": 3, "seed": s}, lgb.Dataset(Dt.loc[keep, cols], label=y3[keep]), num_boost_round=rondas)
                    pm = m.predict(Dv[cols]); P.append(pm[:, 2] / np.clip(1 - pm[:, 1], 1e-6, None))
                acum = ganancia_acumulada(yv, np.mean([rankdata(p) / len(p) for p in P], axis=0))
                g[vn] = np.mean([acum[k - 1] for k in KS])
                filas.append({"fold": fold, "semilla": s, "variante": vn, "gan_media_k": g[vn]})
            escribir(f"[{fold} s={s}] V0 {g['V0_sin_lag2']/1e6:.1f} | lag2 {(g['V1_lag2']-g['V0_sin_lag2'])/1e6:+.1f} | barajado {(g['V1c_lag2_barajado']-g['V0_sin_lag2'])/1e6:+.1f} ({(time.time()-t0)/60:.0f} min)")
            pd.DataFrame(filas).to_csv(CSV, index=False)
    res = pd.DataFrame(filas); res["M"] = res.gan_media_k / 1e6; res.to_csv(CSV, index=False)
    p = res.pivot_table(index=["fold", "semilla"], columns="variante", values="M"); comp = []
    for a, b in [("V1_lag2", "V0_sin_lag2"), ("V1c_lag2_barajado", "V0_sin_lag2"), ("V1_lag2", "V1c_lag2_barajado")]:
        d = (p[a] - p[b]).groupby("fold"); fila = {"comparacion": f"{a} - {b}"}
        for f in FOLDS:
            fila[f"{f}_delta"], fila[f"{f}_ee"] = d.mean()[f], d.std()[f] / np.sqrt(len(SEMILLAS_016))
        fila["pares_positivos"] = f"{int(((p[a] - p[b]) > 0).sum())}/{len(p)}"; comp.append(fila)
    comp = pd.DataFrame(comp).round(2); comp.to_csv(AQUI / "comparacion.csv", index=False)
    escribir("\nNiveles (M ARS):\n" + res.groupby(["variante", "fold"]).M.mean().unstack().round(1).to_string())
    escribir("\nDiferencias pareadas:\n" + comp.to_string(index=False)); escribir("[016] terminado")
