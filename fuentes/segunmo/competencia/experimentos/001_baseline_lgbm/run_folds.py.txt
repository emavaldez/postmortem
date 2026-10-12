"""001 (complemento): el mismo baseline evaluado en los 2 folds de PLAN.md (A: ->202105, B: ->202106).
Uso (raíz del repo):  venv/bin/python competencia/experimentos/001_baseline_lgbm/run_folds.py
Escribe validacion_folds.csv en esta carpeta. No genera submits."""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src"))
from validacion import evaluar, resumen  # noqa: E402

res = evaluar()
res.to_csv(AQUI / "validacion_folds.csv", index=False)
r = resumen(res)
print("\nGanancia en millones (media | desvío entre semillas):")
for c in ["auc", "gan_umbral", "gan_max_expost", "gan_k10000", "gan_k11000", "gan_k12000"]:
    print(f"  {c:>15}: " + "   ".join(f"{i}: {r.loc[i, ('media', c)]:8.3f} ± {r.loc[i, ('desvio', c)]:.3f}" for i in r.index))
