r"""
13_decidir.py
DMEyF 2026 - Primera Competencia - Experimentos 7001 / 7002

Aplica las REGLAS FIJADAS DE ANTEMANO (antes de ver resultados) y escribe las configs del paso
siguiente, para que todo el lote corra sin intervencion y sin decisiones a ojo sobre la mitad B.

Modo "p23"  (despues de 5109): elige min_data_in_leaf y cantidad de arboles para la prueba 23
  R3a  min_data_in_leaf: se usa 10.124 con 2 meses (=> 20.248 en el final, DENTRO del rango del
       profesor) si su meseta en B no es mas de 3 M peor que la de 20.248 con 580 arboles.
       Si es mas de 3 M peor, se mantiene 20.248 (=> 40.496 en el final) y queda declarado.
  R3b  arboles: se cambia 580 por otra cantidad k solo si, con el min_data elegido, k le gana a 580
       por >= +5 M de meseta en >= 85% de los remuestreos y las cantidades vecinas de k (sin contar
       580) tambien le ganan en promedio. Si hay varias, la de mayor meseta.
  Escribe configs\5110_comparar_bo4109.json (bo4109 contra la variante elegida de la prueba 23).

Modo "final" (despues de 5110): elige los hiperparametros del modelo final
  R4   se usa la eleccion de 4109 (la Bayesiana limpia, elegida solo por la mitad A) salvo que su
       meseta en B sea mas de 3 M peor que la de la variante de la prueba 23.
  R5   min_data_in_leaf final: escalado por meses (x2: de 2 a 4 meses). Si R3a mostro que la mitad
       del valor no empeora (se eligio 10.124) y el escalado supera 20.000, se fija en 20.000.
  Escribe configs\5018_prod_final.json y configs\6014_zulip_final_5018.json.

Uso:  py -3.12 13_decidir.py p23
      py -3.12 13_decidir.py final
"""

print("Arrancando 13_decidir.py ...", flush=True)

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from exp_utils import DIR_EXP, ROOT, cerrar_experimento, iniciar_experimento

MODO = sys.argv[1] if len(sys.argv) > 1 else ""
assert MODO in ("p23", "final"), "Uso: py -3.12 13_decidir.py p23 | final"
CONFIGS = ROOT / "configs"
ARBOLES = [400, 580, 750, 900, 1100]
DATASET = "ds3003_rank_extra.parquet"
H4107 = {"eleccion": "4107_bo_profesor_mar_abr/4107_eleccion.json"}
H4109 = {"eleccion": "4109_bo_limpia_profesor/4109_eleccion.json"}
MESES_VAL = [202103, 202104]


def carpeta(id_exp):
    c = sorted(p for p in DIR_EXP.glob(f"{id_exp}_*") if p.is_dir())
    assert c, f"No existe la carpeta del experimento {id_exp}"
    return c[0]


def leer(id_exp, nombre):
    c = carpeta(id_exp)
    return pd.read_csv(c / f"{id_exp}_{nombre}.csv")


if MODO == "p23":
    exp = iniciar_experimento({"experimento": 7001, "nombre": "decision_p23", "sobrescribir": True,
                               "descripcion": "Aplica R3a (min_data_in_leaf) y R3b (arboles) sobre 5109 y escribe la config de 5110."})
    res = leer(5109, "resumen").set_index("modelo")
    boot = leer(5109, "bootstrap")
    m_hi, m_lo = res.loc["md20248_a580", "meseta_M"], res.loc["md10124_a580", "meseta_M"]
    md = "md10124" if m_lo >= m_hi - 3 else "md20248"
    print(f"R3a: meseta md10124_a580 = {m_lo} M, md20248_a580 = {m_hi} M -> se usa {md}")

    base = boot[f"meseta_{md}_a580"]
    detalle, aptos = [], []
    for i, k in enumerate(ARBOLES):
        if k == 580:
            continue
        d = (boot[f"meseta_{md}_a{k}"] - base) / 1e6
        vecinos = [ARBOLES[j] for j in (i - 1, i + 1) if 0 <= j < len(ARBOLES) and ARBOLES[j] != 580]
        vec_ok = all(((boot[f"meseta_{md}_a{v}"] - base) / 1e6).mean() > 0 for v in vecinos)
        ok = d.mean() >= 5 and (d > 0).mean() >= 0.85 and vec_ok
        detalle.append({"arboles": k, "dif_vs_580_M": round(d.mean(), 1), "pct_gana": round((d > 0).mean(), 3),
                        "vecinos_ganan": vec_ok, "cumple_R3b": ok})
        if ok:
            aptos.append((res.loc[f"{md}_a{k}", "meseta_M"], k))
    arboles = max(aptos)[1] if aptos else 580
    pd.DataFrame(detalle).to_csv(exp.ruta("detalle_arboles"), index=False)
    print(pd.DataFrame(detalle).to_string(index=False))
    print(f"R3b: arboles = {arboles}")

    md_ref = int(json.loads((carpeta(4107) / "4107_eleccion.json").read_text(encoding="utf-8"))["params"]["min_data_in_leaf"])
    decision = {"min_data_variante": md, "min_data_2meses": int(round(md_ref / 2)) if md == "md10124" else md_ref,
                "arboles": arboles, "meseta_B_M": float(res.loc[f"{md}_a{arboles}", "meseta_M"])}
    (exp.carpeta / "7001_decision.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")

    cand_p23 = {"dataset": DATASET, "variables": None, "usar_lag2": True, "hiperparametros": H4107,
                "meses_train": MESES_VAL, "min_data_in_leaf": decision["min_data_2meses"],
                "arboles_lista": [arboles]}
    cfg = {"experimento": 5110, "nombre": "comparar_bo4109", "sobrescribir": True,
           "descripcion": f"R4: Bayesiana limpia 4109 (elegida solo por la mitad A) contra la prueba 23 en la "
                          f"variante elegida por R3 ({md}, {arboles} arboles). Train 202103+202104, ds3003 con lag2, "
                          f"mitad B de 202106 (x2), 30 semillas, bootstrap pareado.",
           "referencia": "bo4109", "n_semillas": 30,
           "candidatos": {"bo4109": {"dataset": DATASET, "variables": None, "usar_lag2": True,
                                     "hiperparametros": H4109, "meses_train": MESES_VAL},
                          "p23": cand_p23}}
    (CONFIGS / "5110_comparar_bo4109.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Escrita configs\\5110_comparar_bo4109.json")
    cerrar_experimento(exp, decision)

else:
    exp = iniciar_experimento({"experimento": 7002, "nombre": "decision_final", "sobrescribir": True,
                               "descripcion": "Aplica R4 (bo4109 contra la prueba 23) y R5 (min_data final) y escribe 5018 y 6014."})
    d1 = json.loads((carpeta(7001) / "7001_decision.json").read_text(encoding="utf-8"))
    res = leer(5110, "resumen").set_index("modelo")
    clave_p23 = "p23"
    m_bo, m_p23 = res.loc["bo4109", "meseta_M"], res.loc[clave_p23, "meseta_M"]
    usa_bo = m_bo >= m_p23 - 3
    print(f"R4: meseta bo4109 = {m_bo} M, p23 = {m_p23} M -> se usa {'bo4109' if usa_bo else 'p23'}")

    el = json.loads((carpeta(4109 if usa_bo else 4107) / f"{4109 if usa_bo else 4107}_eleccion.json").read_text(encoding="utf-8"))
    cfg = json.loads((CONFIGS / "5015_prod_profesor_mar_jun.json").read_text(encoding="utf-8"))
    cfg.update({"experimento": 5018, "nombre": "prod_final", "sobrescribir": True, "dataset": DATASET, "usar_lag2": True,
                "meses_train": [202103, 202104, 202105, 202106], "n_semillas": 50,
                "hiperparametros": H4109 if usa_bo else H4107})
    for k in ("arboles", "min_data_in_leaf_final"):
        cfg.pop(k, None)
    min_2m = el["params"]["min_data_in_leaf"] if usa_bo else d1["min_data_2meses"]
    escalado = int(round(min_2m * 4 / 2))
    if not usa_bo:
        cfg["arboles"] = int(d1["arboles"])
        cfg["min_data_in_leaf_final"] = escalado
    if d1["min_data_variante"] == "md10124" and escalado > 20000:
        cfg["min_data_in_leaf_final"] = 20000
    final_md = cfg.get("min_data_in_leaf_final", escalado)
    arboles = cfg.get("arboles", el["arboles"])
    cfg["descripcion"] = (f"Modelo final: ds3003 (receta del profesor + proceso de muerte) con lag2, train 202103-202106, "
                          f"hiperparametros {'de 4109 (Bayesiana limpia, rangos del profesor, elegida por la mitad A)' if usa_bo else 'de la prueba 23'}, "
                          f"min_data_in_leaf final {final_md}, {arboles} arboles, 50 semillas. Reglas R3-R5 fijadas de antemano.")
    (CONFIGS / "5018_prod_final.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    z = {"experimento": 6014, "nombre": "zulip_final_5018", "sobrescribir": True, "modo": "final", "fuente": "5018_prod_final",
         "envios": [11000, 11500, 12000, 12500, 13000, 13500],
         "descripcion": "Archivos para el bot del modelo final 5018: 11.000 a 13.500 envios."}
    (CONFIGS / "6014_zulip_final_5018.json").write_text(json.dumps(z, indent=2, ensure_ascii=False), encoding="utf-8")
    decision = {"usa": "bo4109" if usa_bo else "p23", "meseta_B_bo4109_M": float(m_bo), "meseta_B_p23_M": float(m_p23),
                "min_data_in_leaf_final": int(final_md), "arboles": int(arboles),
                "dentro_del_rango_profesor": bool(final_md <= 20000)}
    (exp.carpeta / "7002_decision.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")
    print(json.dumps(decision, indent=2))
    print("Escritas configs\\5018_prod_final.json y configs\\6014_zulip_final_5018.json")
    cerrar_experimento(exp, decision)
