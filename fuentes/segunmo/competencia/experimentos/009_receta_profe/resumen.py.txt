"""Resumen parcial o final de 009 (lee resultados.csv). Uso: venv/bin/python competencia/experimentos/009_receta_profe/resumen.py"""
from pathlib import Path

import pandas as pd

r = pd.read_csv(Path(__file__).resolve().parent / "resultados.csv")
r["M"] = r.gan_media_k / 1e6
ref = r[r.brazo == "ref"].groupby("fold").M.mean().rename("ref_Optuna")
t = r[r.brazo != "ref"].groupby(["brazo", "config", "rondas", "fold"]).M.mean().unstack()
for f in t.columns:
    t[f"{f}_vs_ref"] = t[f] - ref.get(f)
t["media_vs_ref"] = t[[c for c in t.columns if c.endswith("_vs_ref")]].mean(axis=1)
print("Referencia M1 top1 de Optuna (M ARS, media k=8000..15000):", ref.round(1).to_dict())
print(t.sort_values("media_vs_ref", ascending=False).head(15).round(1).to_string())
