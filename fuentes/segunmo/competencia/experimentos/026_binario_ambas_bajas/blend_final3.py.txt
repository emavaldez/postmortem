"""026c — candidato con tres componentes: rank medio de (a) 017 con lag2+auxiliar, (b) 010 multiclase, (c) 8 modelos de la receta (024), (d) binario con ambas bajas (026b),
con pesos 1/6, 1/6, 1/3, 1/3 (es decir: blend 019 = 1/3, receta = 1/3, binario ambas bajas = 1/3). k=12000, un solo archivo.
Uso (raíz del repo): venv/bin/python competencia/experimentos/026_binario_ambas_bajas/blend_final3.py [k]"""
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from config import ID_COL  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402

K, E = (int(sys.argv[1]) if len(sys.argv) > 1 else 12000), AQUI.parents[0]
fuentes = {"r017": E / "017_final" / "tmp" / "scores_202108_conlag2.csv", "r010": E / "010_multiclase" / "tmp" / "proba_202108.csv",
           "rrec": E / "024_final_receta" / "tmp" / "scores_rec_202108.csv", "rb12": E / "026_binario_ambas_bajas" / "tmp" / "proba_b12_202108.csv"}
d = None
for n, f in fuentes.items():
    x = pd.read_csv(f, usecols=[ID_COL, "rank"]).rename(columns={"rank": n})
    d = x if d is None else d.merge(x, on=ID_COL, validate="one_to_one")
assert len(d) == 164647, len(d)
R = {n: rankdata(d[n]) / len(d) for n in fuentes}
d["final3"] = R["r017"] / 6 + R["r010"] / 6 + R["rrec"] / 3 + R["rb12"] / 3
ids = d[ID_COL].values; top = top_k_ids(ids, d.final3.values, K)
actual = set(pd.read_csv(E.parent / "submissions" / "exp024_final_k12000.csv", header=None)[0])
print(f"k={K} | solapamiento con exp024_final (el vigente) {len(set(top) & actual) / K:.1%}")
print(guardar_submit(top, f"exp027_final3_k{K}").name)
