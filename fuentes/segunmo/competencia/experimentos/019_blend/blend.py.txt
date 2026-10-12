"""019 — candidato final con cobertura de riesgo: promedio por RANK de dos modelos ya entrenados (no se reentrena nada).
  017: MIX6 multiclase + auxiliar de BAJA+1 + lag2 en M1, 30 semillas/config  (`017_final/tmp/scores_202108_conlag2.csv`, columna `rank`)
  010: MIX6 multiclase sin auxiliar ni lag2, 6 semillas/config                (`010_multiclase/tmp/proba_202108.csv`, columna `rank`)
Motivo: el lag2 de 202108 apunta a 202106 (aguinaldo; PSI 0.23 en mpayroll/cpayroll_trx) y la validación del lag2 es de folds solapados; el 010 no depende de eso.
Corte en k=12000 (018: ~1150–1200 positivos esperados en 202108, parecido a B/Bh, cuyo pico está en 12–13k; la curva es plana en 11.5–12k).
Uso (raíz del repo): venv/bin/python competencia/experimentos/019_blend/blend.py [k]"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from config import ID_COL  # noqa: E402
from submit import guardar_submit, top_k_ids  # noqa: E402

K = int(sys.argv[1]) if len(sys.argv) > 1 else 12000
a = pd.read_csv(AQUI.parents[0] / "017_final" / "tmp" / "scores_202108_conlag2.csv", usecols=[ID_COL, "rank"]).rename(columns={"rank": "r017"})
b = pd.read_csv(AQUI.parents[0] / "010_multiclase" / "tmp" / "proba_202108.csv", usecols=[ID_COL, "rank"]).rename(columns={"rank": "r010"})
d = a.merge(b, on=ID_COL, validate="one_to_one")
assert len(d) == len(a) == len(b), "los dos modelos deben puntuar los mismos clientes"
d["rank_blend"] = (rankdata(d.r017) + rankdata(d.r010)) / (2 * len(d))        # se re-rankea cada uno antes de promediar
ids = d[ID_COL].values
top, t017, t010 = top_k_ids(ids, d.rank_blend.values, K), top_k_ids(ids, d.r017.values, K), top_k_ids(ids, d.r010.values, K)
print(f"clientes {len(d)} | k={K} | solapamiento blend-017 {len(set(top) & set(t017)) / K:.1%} | blend-010 {len(set(top) & set(t010)) / K:.1%} | 017-010 {len(set(t017) & set(t010)) / K:.1%}")
print(guardar_submit(top, f"exp019_blend_k{K}").name)
