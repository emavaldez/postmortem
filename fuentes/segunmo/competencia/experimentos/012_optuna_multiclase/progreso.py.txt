"""Resumen del progreso del Optuna multiclase (se puede correr mientras optuna_mc.py corre).
Uso (raíz del repo): venv/bin/python competencia/experimentos/012_optuna_multiclase/progreso.py"""
import sys
from pathlib import Path

import optuna
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from config import RAIZ  # noqa: E402

optuna.logging.set_verbosity(optuna.logging.WARNING)
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
df = optuna.load_study(study_name="MC_M1", storage=f"sqlite:///{RAIZ / 'artifacts' / 'optuna' / '012_optuna_mc.db'}").trials_dataframe()
ok = df[df.state == "COMPLETE"]
print(f"{len(ok)} completos, {(df.state == 'PRUNED').sum()} podados, {(df.state == 'RUNNING').sum()} corriendo")
if len(ok):
    print("anclas (trials 0-2 = M1 top1/2/3 del binario en multiclase):", ok[ok.number < 3].value.round(4).tolist())
    print(f"duración media por trial completo: {(ok.datetime_complete - ok.datetime_start).dt.total_seconds().mean():.0f}s")
    cols = ["number", "value", "user_attrs_gan_A", "user_attrs_gan_B"] + [c for c in ok.columns if c.startswith("params_")]
    print("top 8:"); print(ok.sort_values("value", ascending=False).head(8)[cols].round(4).to_string(index=False))
    print("últimos índices:", ok.value.tail(10).round(4).tolist())
