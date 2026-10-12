"""004 paso 1 — selección con canaritos, UNA vez por fold, usando solo los meses de train de ese fold
(+ una selección final con 202103–202106 para el modelo final). Guarda importancias y listas en sel/.
Uso (raíz del repo): venv/bin/python competencia/experimentos/004_seleccion_variables/seleccion.py"""
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(AQUI.parents[1] / "src"))
from pool import cargar  # noqa: E402
from seleccion import elegir, importancias_con_canaritos  # noqa: E402
from validacion import FOLDS, xy  # noqa: E402

CONJUNTOS = {**{k: v[0] for k, v in FOLDS.items()}, "Bh": [202104], "final": [202103, 202104, 202105, 202106]}

if __name__ == "__main__":
    (AQUI / "sel").mkdir(exist_ok=True)
    for nombre, meses in CONJUNTOS.items():
        t0 = time.time()
        X, y = xy(cargar(meses))
        imp = importancias_con_canaritos(X, y)
        imp.to_csv(AQUI / "sel" / f"importancias_{nombre}.csv")
        for regla in ["max", "p90"]:
            ok = elegir(imp, regla)
            (AQUI / "sel" / f"vars_{nombre}_{regla}.txt").write_text("\n".join(ok) + "\n")
        can = imp[imp.index.str.startswith("canario_")].gain_media
        print(f"{nombre:>5} (train {meses}): {X.shape[1]} cols | canaritos gain máx {can.max():.5f} p90 {can.quantile(.9):.5f} | "
              f"quedan max={len(elegir(imp,'max'))} p90={len(elegir(imp,'p90'))} | {time.time()-t0:.0f}s", flush=True)
