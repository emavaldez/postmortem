"""Verificación rápida (≈1 min) de que el pipeline es determinista en esta máquina. Uso (raíz del repo): venv/bin/python competencia/verificar_determinismo.py
Carga 4 meses, imprime la huella del ORDEN de filas (depende solo de los datos y del ORDER BY: debe coincidir en cualquier máquina) y entrena un modelo
chico con 1 hilo y con todos los hilos (deben dar la MISMA predicción). La huella del modelo depende de la versión de LightGBM (ver requirements-lock.txt)."""
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "competencia" / "src")); sys.path.insert(0, str(RAIZ / "competencia" / "experimentos" / "004_seleccion_variables"))
import config  # noqa: E402
config.CORREGIR_CCAJAS = True
import lightgbm as lgb  # noqa: E402
import numpy as np  # noqa: E402
from pool import cargar  # noqa: E402
from validacion import PARAMS_BASE  # noqa: E402

ORDEN_ESPERADO = "a1db22d02f"          # huella md5 del orden de filas de los 4 meses de train (datos oficiales de la cátedra)
d = json.loads((RAIZ / "competencia/experimentos/005_optuna/mejores_trials.json").read_text())["M1_top1"]
r, params = d.pop("r"), {**PARAMS_BASE, **{k: v for k, v in d.items() if k != "num_boost_round"}}
cols = (RAIZ / "competencia/experimentos/005_optuna/sel/top150_final.txt").read_text().split()
dt, dv = cargar([202103, 202104, 202105, 202106], negocio=True), cargar([202106], negocio=True)
orden = hashlib.md5(dt["numero_de_cliente"].values.tobytes()).hexdigest()[:10]
y = (dt["clase_ternaria"] == "BAJA+2").astype(int).values
keep = (y == 1) | (np.random.RandomState(config.SEMILLAS[0]).rand(len(y)) < r)
preds = {}
for hilos in (1, 0):
    p = lgb.train({**params, "num_threads": hilos, "seed": config.SEMILLAS[0]}, lgb.Dataset(dt.loc[keep, cols], label=y[keep]), num_boost_round=300).predict(dv[cols])
    preds[hilos] = hashlib.md5(p.tobytes()).hexdigest()[:10]
print(f"orden de filas: {orden}  -> {'OK (coincide con el esperado)' if orden == ORDEN_ESPERADO else 'DISTINTO del esperado: revisar datos o versión de DuckDB'}")
print(f"modelo con 1 hilo: {preds[1]} | con todos los hilos: {preds[0]}  -> {'OK (idénticos)' if preds[1] == preds[0] else 'NO DETERMINISTA: revisar versión de LightGBM'}")
sys.exit(0 if orden == ORDEN_ESPERADO and preds[1] == preds[0] else 1)
