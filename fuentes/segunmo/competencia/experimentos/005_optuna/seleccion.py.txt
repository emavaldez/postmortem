"""005 paso 0 — repite la selección top150 de 004 sobre el pool ampliado (345 columnas: + 26 `n_*` de 003d).
Importancia (gain, 5 semillas, con 20 canaritos solo para excluirlos del ranking) calculada SOLO con el train de cada fold.
Guarda sel/importancias_<fold>.csv. Uso (raíz del repo): venv/bin/python competencia/experimentos/005_optuna/seleccion.py"""
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "src")); sys.path.insert(0, str(AQUI.parents[0] / "004_seleccion_variables"))
from pool import cargar  # noqa: E402
from seleccion import importancias_con_canaritos  # noqa: E402
from validacion import xy  # noqa: E402

CONJUNTOS = {"A": [202103], "B": [202103, 202104], "Bh": [202104], "final": [202103, 202104, 202105, 202106]}

if __name__ == "__main__":
    (AQUI / "sel").mkdir(exist_ok=True)
    for nombre, meses in CONJUNTOS.items():
        t0 = time.time()
        X, y = xy(cargar(meses, negocio=True))
        imp = importancias_con_canaritos(X, y)
        imp.to_csv(AQUI / "sel" / f"importancias_{nombre}.csv")
        top = [c for c in imp.index if not c.startswith("canario_")][:150]
        (AQUI / "sel" / f"top150_{nombre}.txt").write_text("\n".join(top) + "\n")
        print(f"{nombre}: {X.shape[1]} cols -> top150 | n_ en el top150: {sum(c.startswith('n_') for c in top)} | {time.time()-t0:.0f}s", flush=True)
