"""
10_entrega_zulip.py
DMEyF 2026 - Primera Competencia - Experimentos 6xxx

Arma los archivos para el bot @competencia-uno de Zulip:
  - solo los numero_de_cliente a los que se envia estimulo (los N de mayor probabilidad)
  - SIN encabezado, un id por linea, enteros (nunca notacion cientifica: 48000000, no 4.8e+07)
  - entre 8.000 y 15.000 registros, extension .csv, nombre unico

Dos modos:
  "final"     -> UN archivo con el semillerio (probabilidad promediada). Es el que tiene que
                 quedar como ULTIMO submit antes del domingo 11/10 23:59:59.
  "semillas"  -> UN archivo por semilla (hasta 20), desde <id>_prob_por_semilla.parquet que
                 graba 07 con "guardar_prob_por_semilla": true. El bot devuelve la media y el
                 desvio de la ganancia publica entre esos archivos.

Uso:  py -3.12 10_entrega_zulip.py                      (PARAM de abajo)
      py -3.12 10_entrega_zulip.py configs/6001.json    (el JSON reemplaza claves del PARAM)
"""

print("Arrancando 10_entrega_zulip.py ...", flush=True)

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from exp_utils import DIR_EXP, cerrar_experimento, iniciar_experimento

# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 6001,
    "nombre": "zulip_final_5005_e13000",
    "descripcion": "Archivo final para Zulip: semillerio de 5005 (retador 4102 prueba 117), 13.000 envios.",
    "modo": "final",                          # "final" o "semillas"
    "fuente": "5005_prod_eleccion_4102",      # carpeta de exp\ con la produccion
    "envios": 13000,
    "max_archivos": 20,
    "clientes_esperados": 164647,             # clientes de 202108
}

if len(sys.argv) > 1:
    config = Path(sys.argv[1])
    PARAM.update(json.loads(config.read_text(encoding="utf-8")))
    PARAM["_config"] = config.name
    print(f"Configuracion tomada de {config}")

assert 8000 <= PARAM["envios"] <= 15000, "El bot exige entre 8.000 y 15.000 registros"
exp = iniciar_experimento(PARAM)
carpeta_fuente = DIR_EXP / PARAM["fuente"]
id_fuente = carpeta_fuente.name.split("_")[0]
salida = exp.carpeta / "zulip"
salida.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Probabilidades
# ---------------------------------------------------------------------------
if PARAM["modo"] == "final":
    df = pd.read_csv(carpeta_fuente / f"{id_fuente}_probabilidades.csv")
    columnas = {"semillerio": df["prob"].to_numpy()}
elif PARAM["modo"] == "semillas":
    df = pd.read_parquet(carpeta_fuente / f"{id_fuente}_prob_por_semilla.parquet")
    cols = [c for c in df.columns if c.startswith("s")][:PARAM["max_archivos"]]
    columnas = {c: df[c].to_numpy() for c in cols}
else:
    raise ValueError("modo tiene que ser 'final' o 'semillas'")

ids = df["numero_de_cliente"]
assert ids.notna().all() and ids.is_unique, "Hay ids vacios o repetidos"
assert (ids == ids.round()).all(), "Hay ids no enteros"
ids = ids.astype("int64").to_numpy()
assert len(ids) == PARAM["clientes_esperados"], f"Se esperaban {PARAM['clientes_esperados']:,} clientes, hay {len(ids):,}"

# ---------------------------------------------------------------------------
# Archivos
# ---------------------------------------------------------------------------
archivos = []
listas = {}
for nombre, prob in columnas.items():
    orden = np.argsort(-prob, kind="stable")
    elegidos = ids[orden[:PARAM["envios"]]]
    texto = "\n".join(str(int(x)) for x in elegidos) + "\n"
    # nombre unico: experimento, fuente, envios y modelo (no se repite entre submits)
    archivo = salida / f"Z{exp.id}_{id_fuente}_e{PARAM['envios']}_{nombre}.csv"
    archivo.write_text(texto, encoding="ascii", newline="\n")

    # controles sobre el archivo tal como quedo grabado
    lineas = archivo.read_text(encoding="ascii").split()
    assert len(lineas) == PARAM["envios"], "Cantidad de registros incorrecta"
    assert all(l.isdigit() for l in lineas), "Hay lineas que no son enteros (encabezado, decimales o notacion cientifica)"
    assert len(set(lineas)) == len(lineas), "Hay ids repetidos"
    archivos.append(archivo)
    listas[nombre] = set(lineas)

print(f"\n{len(archivos)} archivo(s) en {salida}:")
for a in archivos[:5]:
    print(f"  {a.name}")
if len(archivos) > 5:
    print(f"  ... y {len(archivos) - 5} mas")

if len(listas) > 1:
    nombres = list(listas)
    coincid = [len(listas[a] & listas[b]) / PARAM["envios"] for i, a in enumerate(nombres) for b in nombres[i + 1:]]
    print(f"Coincidencia promedio entre archivos de semillas distintas: {np.mean(coincid):.1%}")

cuerpo = f"submit {exp.carpeta.name.replace('_', '')}"
print("\nControles OK: sin encabezado, ids enteros unicos, "
      f"{PARAM['envios']:,} registros por archivo.")
print(f"\nCuerpo sugerido del mensaje a @competencia-uno (sin espacios en el nombre):\n    {cuerpo}")
(exp.carpeta / "cuerpo_mensaje.txt").write_text(cuerpo + "\n", encoding="utf-8")

cerrar_experimento(exp, {"archivos": [a.name for a in archivos], "cuerpo": cuerpo})
