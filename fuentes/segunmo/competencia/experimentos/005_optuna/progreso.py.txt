"""Resumen del progreso de Optuna (se puede correr mientras optuna_run.py está corriendo).
Uso (raíz del repo): venv/bin/python competencia/experimentos/005_optuna/progreso.py [--ronda 2]"""
import sys
from pathlib import Path

import optuna
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from config import RAIZ  # noqa: E402

optuna.logging.set_verbosity(optuna.logging.WARNING)
DB = f"sqlite:///{RAIZ / 'artifacts' / 'optuna' / '005_optuna.db'}"
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 30)
ronda = int(sys.argv[sys.argv.index("--ronda") + 1]) if "--ronda" in sys.argv else 1
for nombre in [f"M0{'' if ronda == 1 else '_r' + str(ronda)}", f"M1{'' if ronda == 1 else '_r' + str(ronda)}"]:
    try:
        e = optuna.load_study(study_name=nombre, storage=DB)
    except KeyError:
        print(f"{nombre}: sin trials todavía"); continue
    df = e.trials_dataframe()
    ok = df[df.state == "COMPLETE"]
    print(f"\n=== {nombre}: {len(ok)} completos, {(df.state == 'PRUNED').sum()} podados, {(df.state == 'RUNNING').sum()} corriendo ===")
    if ok.empty:
        continue
    base = ok[ok.number == 0]
    if not base.empty:
        print(f"trial 0 (baseline con r=0.2): índice {base.value.iloc[0]:.4f}")
    dur = (ok.datetime_complete - ok.datetime_start).dt.total_seconds()
    print(f"duración media por trial completo: {dur.mean():.0f}s")
    cols = ["number", "value", "user_attrs_gan_A", "user_attrs_gan_B"] + [c for c in ok.columns if c.startswith("params_")]
    print("top 5:"); print(ok.sort_values("value", ascending=False).head(5)[cols].round(4).to_string(index=False))
    print("últimos índices:", ok.value.tail(8).round(4).tolist())
