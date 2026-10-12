"""
12_ensamble.py
DMEyF 2026 - Primera Competencia - Experimento 5201

Junta las probabilidades de agosto de varias producciones (07_modelo_final.py) en una sola:
  - cada fuente se convierte en ranking (percentil 0..1) para que todas pesen lo mismo
    aunque sus probabilidades esten en escalas distintas
  - se promedian los rankings
  - se graba <id>_probabilidades.csv con el mismo formato que 07 (numero_de_cliente, prob),
    asi 10_entrega_zulip.py lo usa como cualquier otra fuente

Evidencia (mitad B de junio, 5102, bootstrap pareado de 1.000): el promedio de rankings de los
tres pipelines dio +5,1 M de meseta contra el pipeline actual solo, IC90 [-1,6 ; +12,1],
gana en el 88% de los remuestreos. A 12.000 envios: 437,8 M contra 429,0 M.

Uso:  py -3.12 12_ensamble.py configs\\5201_ensamble_3_pipelines.json
"""

print("Arrancando 12_ensamble.py ...", flush=True)

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
    "experimento": 5201,
    "nombre": "ensamble_3_pipelines",
    "descripcion": "Ensamble por promedio de rankings de 5005, 5009 y 5010.",
    "fuentes": ["5005_prod_eleccion_4102", "5009_prod_rank_bo4104_sin_lag2", "5010_prod_rank_p117_sin_lag2"],
    "clientes_esperados": 164647,
    "cortes_control": [11000, 12000, 13000],
}

if len(sys.argv) > 1:
    config = Path(sys.argv[1])
    PARAM.update(json.loads(config.read_text(encoding="utf-8")))
    PARAM["_config"] = config.name
    print(f"Configuracion tomada de {config}")

# antes de crear la carpeta: que existan todas las fuentes
faltan = []
for f in PARAM["fuentes"]:
    archivo = DIR_EXP / f / f"{f.split('_')[0]}_probabilidades.csv"
    if not archivo.exists():
        faltan.append(str(archivo))
if faltan:
    raise SystemExit("Faltan probabilidades de alguna fuente (¿termino su 07?):\n  " + "\n  ".join(faltan))

exp = iniciar_experimento(PARAM)

# ---------------------------------------------------------------------------
# Lectura y controles
# ---------------------------------------------------------------------------
tablas = {}
for f in PARAM["fuentes"]:
    id_f = f.split("_")[0]
    df = pd.read_csv(DIR_EXP / f / f"{id_f}_probabilidades.csv")
    assert {"numero_de_cliente", "prob"} <= set(df.columns), f"{f}: faltan columnas"
    assert df["numero_de_cliente"].is_unique, f"{f}: clientes repetidos"
    assert df["prob"].notna().all(), f"{f}: hay probabilidades vacias"
    assert len(df) == PARAM["clientes_esperados"], f"{f}: {len(df):,} clientes, se esperaban {PARAM['clientes_esperados']:,}"
    tablas[id_f] = df.set_index("numero_de_cliente")["prob"]

ids = tablas[next(iter(tablas))].index
for k, s in tablas.items():
    assert set(s.index) == set(ids), f"La fuente {k} tiene otros clientes"
probs = pd.DataFrame({k: s.reindex(ids) for k, s in tablas.items()})

# ---------------------------------------------------------------------------
# Promedio de rankings
# ---------------------------------------------------------------------------
rankings = probs.rank(pct=True, method="average")
ensamble = rankings.mean(axis=1)
salida = pd.DataFrame({"numero_de_cliente": ids.astype("int64"), "prob": ensamble.to_numpy()})
salida.to_csv(exp.ruta("probabilidades"), index=False)

# ---------------------------------------------------------------------------
# Cuanto se parecen las listas (informativo)
# ---------------------------------------------------------------------------
print("\nCorrelacion de Spearman entre fuentes:")
print(probs.corr(method="spearman").round(3).to_string())

filas = []
for corte in PARAM["cortes_control"]:
    top_ens = set(ensamble.nlargest(corte).index)
    fila = {"envios": corte}
    for k in probs.columns:
        fila[f"comun_con_{k}_pct"] = round(100 * len(top_ens & set(probs[k].nlargest(corte).index)) / corte, 1)
    filas.append(fila)
comunes = pd.DataFrame(filas)
comunes.to_csv(exp.ruta("coincidencias"), index=False)
print("\n% de clientes del ensamble que tambien estan en la lista de cada fuente:")
print(comunes.to_string(index=False))

cerrar_experimento(exp, {"fuentes": PARAM["fuentes"],
                         "coincidencia_12000": comunes.set_index("envios").loc[12000].to_dict()
                         if 12000 in PARAM["cortes_control"] else None})
