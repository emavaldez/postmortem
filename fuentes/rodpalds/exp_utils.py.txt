"""
exp_utils.py
DMEyF 2026 - utilidades comunes para que cada experimento quede trazable.

Cada script define un diccionario PARAM y hace:

    exp = iniciar_experimento(PARAM)          # crea exp/<id>_<nombre>/, guarda PARAM y copia el script
    ...
    tabla.to_csv(exp.ruta("ganancia_cortes", semilla=571369))   # -> 4101_ganancia_cortes_s571369.csv
    ...
    cerrar_experimento(exp, {"ganancia_max": 123, "envios_opt": 11000})

Al cerrar se agrega una fila a exp/registro_experimentos.csv con PARAM + resultados,
para poder comparar todos los experimentos en una sola tabla.

Numeracion sugerida del id (4 digitos, el primero indica la familia):
    1xxx preparacion de datasets      2xxx diagnosticos / drift
    3xxx feature engineering          4xxx optimizacion de hiperparametros
    5xxx modelo final / semillerio    6xxx entregas a Kaggle
"""

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(os.environ.get("DMEYF_ROOT", r"C:\Users\rpalpa\Documents\Maestria\DMEyF\Primera_competencia"))
DIR_DATA = ROOT / "data"
DIR_EXP = ROOT / "exp"
ARCH_REGISTRO = DIR_EXP / "registro_experimentos.csv"


class Experimento:
    def __init__(self, param, carpeta):
        self.param = param
        self.id = str(param["experimento"])
        self.carpeta = carpeta
        self.inicio = time.time()

    def ruta(self, nombre, semilla=None, ext="csv"):
        """Nombre de archivo con el id (y la semilla si corresponde) adelante."""
        s = f"_s{semilla}" if semilla is not None else ""
        return self.carpeta / f"{self.id}_{nombre}{s}.{ext}"


def _git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       cwd=Path(sys.argv[0]).resolve().parent,
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return "sin_git"


def iniciar_experimento(param):
    for clave in ("experimento", "nombre", "descripcion"):
        if clave not in param:
            raise ValueError(f"PARAM tiene que tener '{clave}'")

    carpeta = DIR_EXP / f"{param['experimento']}_{param['nombre']}"
    existe = carpeta.exists() and any(carpeta.iterdir())
    if existe and not (param.get("sobrescribir", False) or param.get("reanudar", False)):
        raise FileExistsError(
            f"Ya existe {carpeta}.\nUsa otro numero de experimento, PARAM['reanudar'] = True para "
            f"continuar uno interrumpido, o PARAM['sobrescribir'] = True si de verdad queres pisarlo.")
    if existe and param.get("reanudar", False):
        print(f"Reanudando experimento existente en {carpeta}")
    carpeta.mkdir(parents=True, exist_ok=True)

    exp = Experimento(param, carpeta)

    # copia del script tal cual se corrio (reproducibilidad aunque despues lo edites)
    script = Path(sys.argv[0]).resolve()
    if script.suffix == ".py" and script.exists():
        shutil.copy2(script, exp.ruta("script", ext="py"))

    param["_fecha_inicio"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    param["_script"] = script.name
    param["_git_commit"] = _git_commit()
    with open(exp.ruta("PARAM", ext="json"), "w", encoding="utf-8") as f:
        json.dump(param, f, indent=2, ensure_ascii=False, default=str)

    print(f"=== Experimento {exp.id} - {param['nombre']} ===")
    print(f"{param['descripcion']}")
    print(f"Carpeta: {carpeta}\n")
    return exp


def _aplanar(d, prefijo=""):
    """{'lgbm': {'num_leaves': 31}} -> {'lgbm.num_leaves': 31}  (para el registro en una fila)."""
    plano = {}
    for k, v in d.items():
        clave = f"{prefijo}{k}"
        if isinstance(v, dict):
            plano.update(_aplanar(v, clave + "."))
        elif isinstance(v, (list, tuple)):
            plano[clave] = " ".join(str(x) for x in v)
        else:
            plano[clave] = v
    return plano


def cerrar_experimento(exp, resultados=None):
    resultados = resultados or {}
    minutos = round((time.time() - exp.inicio) / 60, 2)
    resultados["_minutos"] = minutos

    with open(exp.ruta("resultados", ext="json"), "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False, default=str)

    fila = _aplanar(exp.param)
    fila.update({f"res.{k}": v for k, v in resultados.items()})
    nueva = pd.DataFrame([fila])
    if ARCH_REGISTRO.exists():
        registro = pd.read_csv(ARCH_REGISTRO, dtype=str)
        registro = registro[registro["experimento"] != exp.id]       # si se re-corrio, queda la ultima
        nueva = pd.concat([registro, nueva.astype(str)], ignore_index=True)
    nueva.to_csv(ARCH_REGISTRO, index=False)

    print(f"\n=== Fin experimento {exp.id} ({minutos} min). Registrado en {ARCH_REGISTRO.name} ===")
