"""C1 — Adversarial validation sin target: ¿202108 se distingue de los meses de train más de lo que se distinguen
entre sí los meses consecutivos? (AUC ~0.5 = indistinguibles; un mes "nuevo" siempre se distingue algo por nominales/calendario).
Se excluyen las variables de calendario puro (Master/Visa_fultimo_cierre identifican el mes: AUC 1.0, ver 002).
Uso (raíz del repo): venv/bin/python competencia/experimentos/008_c1_adversarial/run.py"""
import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from config import ID_COL, MES_COL, TARGET_COL  # noqa: E402
from data import cargar_meses  # noqa: E402
from drift import adversarial  # noqa: E402

MESES = [202103, 202104, 202105, 202106, 202107, 202108]
d = cargar_meses(MESES, solo_con_target=False)
# ccajas_depositos está rota en 202105 (todo 0, o NA tras la corrección): delata al mes por artefacto de datos -> se excluye
EXCLUIR = (ID_COL, MES_COL, TARGET_COL, "ccajas_depositos")
cols = [c for c in d.columns if c not in EXCLUIR and not c.endswith("fultimo_cierre")]
por_mes = {m: d[d[MES_COL] == m] for m in MESES}

filas, imps = [], {}
pares = [(a, b) for a, b in zip(MESES[:-1], MESES[1:])] + [(202106, 202108), (202105, 202108), (202104, 202108), (202103, 202108)]
for a, b in pares:
    auc, imp = adversarial(por_mes[a], por_mes[b], cols)
    filas.append({"mes_a": a, "mes_b": b, "auc": round(auc, 3), "top5": ", ".join(f"{k} ({v:.2f})" for k, v in imp.head(5).items())})
    imps[(a, b)] = imp
    print(filas[-1], flush=True)
# train completo (202103-06) vs 202108
tr = d[d[MES_COL].isin(MESES[:4])]
auc, imp = adversarial(tr, por_mes[202108], cols)
filas.append({"mes_a": "202103-06", "mes_b": 202108, "auc": round(auc, 3), "top5": ", ".join(f"{k} ({v:.2f})" for k, v in imp.head(5).items())})
print(filas[-1])
pd.DataFrame(filas).to_csv(AQUI / "resultados.csv", index=False)
