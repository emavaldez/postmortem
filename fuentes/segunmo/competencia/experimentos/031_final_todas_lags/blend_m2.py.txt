"""031b — candidato final con M2: rank medio ponderado entre el ensemble M2 (todas las variables con lags, 031) y el blend actual `exp024_final` (017 + 010 + receta).
Pesos por defecto: 2/3 M2 + 1/3 exp024. Juicio, no validado: 030 mostró M2 +8.8M sobre E1 en B2 y la mezcla 50/50 con E1 +5.9M; exp024 aporta diversidad (receta) y cobertura.
Uso (raíz del repo): venv/bin/python competencia/experimentos/031_final_todas_lags/blend_m2.py [peso_m2] [k]"""
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from config import ID_COL  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402

W, K, E = (float(sys.argv[1]) if len(sys.argv) > 1 else 2 / 3), (int(sys.argv[2]) if len(sys.argv) > 2 else 12000), AQUI.parents[0]
ARCH = sys.argv[3] if len(sys.argv) > 3 else "scores_m2_202108.csv"            # p. ej. scores_m2_md50-65-80_202108.csv
src = {"m2": AQUI / "tmp" / ARCH, "r017": E / "017_final" / "tmp" / "scores_202108_conlag2.csv", "r010": E / "010_multiclase" / "tmp" / "proba_202108.csv",
       "rrec": E / "024_final_receta" / "tmp" / "scores_rec_202108.csv"}
d = None
for n, f in src.items():
    x = pd.read_csv(f, usecols=[ID_COL, "rank"]).rename(columns={"rank": n})
    d = x if d is None else d.merge(x, on=ID_COL, validate="one_to_one")
assert len(d) == 164647, len(d)
R = {n: rankdata(d[n]) / len(d) for n in src}
mix019 = rankdata(R["r017"] + R["r010"]) / len(d)                                   # = blend 019
actual = rankdata(mix019 + R["rrec"]) / len(d)                                       # = exp024_final (50/50 blend 019 y receta)
final = W * R["m2"] + (1 - W) * actual
ids = d[ID_COL].values; top = top_k_ids(ids, final, K)
tm2 = set(top_k_ids(ids, R["m2"], K))
t24 = set(top_k_ids(ids, actual, K))                                                  # exp024_final regenerado en memoria (no se lee del disco)
print(f"peso M2 {W:.3f} | k={K} | solapamiento con exp024_final {len(set(top) & t24) / K:.1%} | con M2 solo {len(set(top) & tm2) / K:.1%} | M2 vs exp024 {len(tm2 & t24) / K:.1%}")
nombre = f"exp031_final_w{int(round(W * 100))}{'_md' if 'md' in ARCH else ''}_k{K}"
destino = AQUI.parents[1] / "submissions" / f"{nombre}.csv"
if destino.exists():                                      # reproducibilidad: si ya existe, se compara en vez de fallar
    import numpy as np
    previo = np.loadtxt(destino, dtype=np.int64)
    if np.array_equal(previo, top):
        print(f"{nombre}.csv ya existía: IDÉNTICO al regenerado (mismo conjunto y mismo orden)")
    else:                                                 # no se pisa el enviado: el regenerado queda con sufijo para poder compararlos
        print(f"{nombre}.csv ya existía y es DISTINTO: coinciden {len(set(previo) & set(top)) / K:.1%} de los clientes. Se guarda el regenerado como {nombre}_regenerado.csv")
        print(guardar_submit(top, f"{nombre}_regenerado").name)
else:
    print(guardar_submit(top, nombre).name)
