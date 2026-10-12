"""024 — candidato final: rank 50/50 entre el blend actual (019: 017 + 010) y el ensemble de la receta (final_rec.py), corte k=12000, un solo archivo.
Uso (raíz del repo): venv/bin/python competencia/experimentos/024_final_receta/blend_final.py [k]"""
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from config import ID_COL  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402

K = int(sys.argv[1]) if len(sys.argv) > 1 else 12000
E = AQUI.parents[0]
a = pd.read_csv(E / "017_final" / "tmp" / "scores_202108_conlag2.csv", usecols=[ID_COL, "rank"]).rename(columns={"rank": "r017"})
b = pd.read_csv(E / "010_multiclase" / "tmp" / "proba_202108.csv", usecols=[ID_COL, "rank"]).rename(columns={"rank": "r010"})
c = pd.read_csv(AQUI / "tmp" / "scores_rec_202108.csv", usecols=[ID_COL, "rank"]).rename(columns={"rank": "rrec"})
d = a.merge(b, on=ID_COL, validate="one_to_one").merge(c, on=ID_COL, validate="one_to_one")
assert len(d) == len(a) == len(b) == len(c)
d["mix"] = (rankdata(d.r017) + rankdata(d.r010)) / (2 * len(d))                      # = blend 019
d["final"] = (rankdata(d.mix) + rankdata(d.rrec)) / (2 * len(d))                    # 50/50 con la receta
ids = d[ID_COL].values; top = top_k_ids(ids, d.final.values, K)
t = {n: set(top_k_ids(ids, d[n].values, K)) for n in ("mix", "rrec", "r017")}
print(f"k={K} | solapamiento final-mix(019) {len(set(top) & t['mix']) / K:.1%} | final-receta {len(set(top) & t['rrec']) / K:.1%} | receta-mix {len(t['rrec'] & t['mix']) / K:.1%}")
print(guardar_submit(top, f"exp024_final_k{K}").name)
