"""
03_submit_L22.py — arma UN archivo de submit con el ensamble de las predicciones sobre 08 disponibles.

Promedia las probabilidades de todos los modelos disponibles (de este volumen y de los volúmenes de --otros), ordena
los clientes por ese promedio y toma los --corte con mayor probabilidad. Escribe un .csv con el formato del bot:
    - extensión .csv, SIN encabezado, un numero_de_cliente por línea, entre 8000 y 15000 registros
    - ids como enteros (nunca notación científica: 48000000, no 4.8e+07)

Uso (desde ~/dmeyf):
    python 03_submit_L22.py --corte 10500 --volumen L22 --otros L22b

Salida: exp/<volumen>/submit/<nombre>.csv  (el nombre incluye cantidad de modelos, corte y fecha: es distinto en cada corrida)
y la línea para el cuerpo del mensaje a @competencia-uno:   submit <nombre>
"""
import argparse
import os
import re
import time

import numpy as np
import pandas as pd

import comun_L22 as cm
from comun_L22 import log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volumen", default=cm.VOLUMEN)
    ap.add_argument("--otros", nargs="*", default=[], help="otros volúmenes (carpetas exp/<volumen>) con más predicciones")
    ap.add_argument("--dir_base", default=os.path.expanduser("~/dmeyf"))
    ap.add_argument("--corte", type=int, required=True, help="cantidad de clientes a enviar (los de mayor probabilidad)")
    ap.add_argument("--nombre", default=None, help="nombre del submit (sin espacios); por defecto se arma solo y es único")
    ap.add_argument("--prueba", action="store_true", help="SOLO para probar el código: no exige el rango 8000-15000")
    a = ap.parse_args()
    if not a.prueba:
        assert 8000 <= a.corte <= 15000, "el bot acepta archivos con entre 8000 y 15000 registros"

    dir_exp = os.path.join(a.dir_base, "exp", a.volumen)
    otros = [os.path.join(a.dir_base, "exp", v) for v in a.otros]
    ens, usadas = cm.ensamblar_08(dir_exp, a.volumen, cm.semillas_n(1000), otros_dirs=otros, guardar=False)

    orden = np.argsort(-ens["prob_ens"].to_numpy(), kind="stable")[:a.corte]
    ids = ens["numero_de_cliente"].to_numpy().astype("int64")[orden]
    assert len(ids) == a.corte and len(np.unique(ids)) == a.corte, "ids repetidos o menos clientes que el corte"
    corte_prob = ens["prob_ens"].to_numpy()[orden[-1]]
    log(f"  corte {a.corte:,}: se envían los clientes con prob_ens >= {corte_prob:.5f}")

    nombre = a.nombre or f"{a.volumen}_ens{len(usadas)}m_c{a.corte}_{time.strftime('%Y%m%d%H%M')}"
    assert re.fullmatch(r"[A-Za-z0-9_.-]+", nombre), "el nombre no puede tener espacios ni caracteres raros"
    carpeta = os.path.join(dir_exp, "submit")
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f"{nombre}.csv")
    assert not os.path.exists(ruta), f"ya existe {ruta}: cada submit debe tener un nombre distinto"
    pd.Series(ids, dtype="int64").to_csv(ruta, index=False, header=False)    # enteros, sin encabezado

    # verificación del archivo escrito, leyéndolo como texto
    with open(ruta) as fh:
        lineas = fh.read().split("\n")
    assert lineas[-1] == "", "el archivo debe terminar en salto de línea"
    lineas = lineas[:-1]
    assert len(lineas) == a.corte, (len(lineas), a.corte)
    assert all(re.fullmatch(r"[0-9]+", l) for l in lineas), "hay líneas que no son enteros puros (encabezado, decimales o notación científica)"
    log(f"  archivo verificado: {len(lineas):,} líneas, sin encabezado, todos enteros")
    log(f"  primeras 7 líneas: {lineas[:7]}")
    log(f"  guardado: {ruta}")
    print(f"\nCuerpo del mensaje a @competencia-uno:\n    submit    {nombre}\nArchivo adjunto:\n    {ruta}")


if __name__ == "__main__":
    main()
