"""004b (control) — misma cantidad de modelos: ¿la mezcla gana por DIVERSIDAD de variables o solo por promediar más modelos?
Las 20 semillas se parten en 4 grupos de 5. Un ensemble de 5 semillas = lo que va en el submit.
  MIX      = 5 modelos M0 + 5 modelos M1 (10 modelos)          [grupo g]
  M0 x10   = 10 modelos M0 (grupos g y h)      M1 x10 = 10 modelos M1 (grupos g y h)
4 réplicas por fold: (g,h) = (0,1),(1,0),(2,3),(3,2). Ganancia en k=11000.
Uso (raíz del repo): venv/bin/python competencia/experimentos/004b_mezcla/run_control.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables")); sys.path.insert(0, str(AQUI))   # AQUI primero: "run" es el de 004b, no el de 004
from run import FOLDS, SEMILLAS_20, ajustar, es_hist  # noqa: E402
from ganancia import ganancia_acumulada  # noqa: E402
from pool import cargar  # noqa: E402
from validacion import K_REF, xy  # noqa: E402

if __name__ == "__main__":
    grupos = [SEMILLAS_20[i:i + 5] for i in range(0, 20, 5)]
    filas = []
    for fold, (mt, mv) in FOLDS.items():
        (Xt, yt), (Xv, yv) = xy(cargar(mt)), xy(cargar([mv]))
        orig = [c for c in Xt.columns if not es_hist(c)]
        imp = pd.read_csv(AQUI.parent / "004_seleccion_variables" / "sel" / f"importancias_{fold}.csv", index_col=0)
        top = [c for c in imp.index if not c.startswith("canario_")][:150]
        E0 = [np.mean([ajustar(Xt[orig], yt, Xv[orig], s) for s in g], axis=0) for g in grupos]
        E1 = [np.mean([ajustar(Xt[top], yt, Xv[top], s) for s in g], axis=0) for g in grupos]
        gan = lambda p: ganancia_acumulada(yv.values, p)[K_REF - 1] / 1e6  # noqa: E731
        for g, h in [(0, 1), (1, 0), (2, 3), (3, 2)]:
            filas.append({"fold": fold, "rep": f"{g}{h}", "M0x10": gan((E0[g] + E0[h]) / 2), "M1x10": gan((E1[g] + E1[h]) / 2),
                          "MIX": gan((E0[g] + E1[g]) / 2), "M0x5": gan(E0[g]), "M1x5": gan(E1[g])})
        print("listo fold", fold, flush=True)
    res = pd.DataFrame(filas); res.to_csv(AQUI / "resultados_control.csv", index=False)
    print(res.groupby("fold").mean(numeric_only=True).round(1))
    for fold, g in res.groupby("fold"):
        print(fold, "MIX - M0x10: %.1f | MIX - M1x10: %.1f | M1x10 - M0x10: %.1f" % ((g.MIX - g.M0x10).mean(), (g.MIX - g.M1x10).mean(), (g.M1x10 - g.M0x10).mean()),
              "| desvío entre réplicas MIX-mejor:", round((g.MIX - g[["M0x10", "M1x10"]].max(axis=1)).std(), 1))
