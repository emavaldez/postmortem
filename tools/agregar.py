"""Junta las lecturas en un solo archivo de conteos y fichas compactas (_trabajo/agregado.json), que es la única fuente
del resumen general en prosa."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar as G

entregas = [e for e in G.cargar() if e["an"]]
usa, exp = G.conteos(entregas)
def cuenta(campo):
    d = {}
    for e in entregas:
        for x in (e["an"].get("ficha") or {}).get(campo) or []:
            d[str(x)] = d.get(str(x), 0) + 1
    return dict(sorted(d.items(), key=lambda x: -x[1]))
sem = [(e["an"].get("ficha") or {}).get("cantidad_de_semillas") for e in entregas]
sem_n = sorted(x for x in sem if isinstance(x, int))
meses = {}
for e in entregas:
    k = ", ".join(map(str, (e["an"].get("ficha") or {}).get("meses_entrenamiento") or [])) or "No se observa"
    meses[k] = meses.get(k, 0) + 1
val = {}
for e in entregas:
    k = ", ".join(map(str, (e["an"].get("ficha") or {}).get("meses_validacion") or [])) or "sin meses de validación"
    val[k] = val.get(k, 0) + 1
agregado = {
    "entregas_leidas": len(entregas),
    "entregas_posteadas": 68, "entregas_descargadas": 66,
    "lenguajes": cuenta("lenguajes"), "modelos": cuenta("modelos"),
    "tecnicas": {c: {"nombre": G.ETIQUETA[c], "en_la_entrega": len(usa.get(c, [])), "solo_exploradas": len(exp.get(c, []))} for c in G.ETIQUETA},
    "cantidad_de_semillas": {"con_dato": len(sem_n), "sin_dato": len(sem) - len(sem_n), "minimo": sem_n[0] if sem_n else None, "mediana": sem_n[len(sem_n) // 2] if sem_n else None,
                             "maximo": sem_n[-1] if sem_n else None, "una_sola": sum(1 for x in sem_n if x <= 1), "de_2_a_10": sum(1 for x in sem_n if 2 <= x <= 10),
                             "de_11_a_50": sum(1 for x in sem_n if 11 <= x <= 50), "mas_de_50": sum(1 for x in sem_n if x > 50)},
    "meses_de_entrenamiento": dict(sorted(meses.items(), key=lambda x: -x[1])),
    "meses_de_validacion": dict(sorted(val.items(), key=lambda x: -x[1])),
    "reproducibilidad": {k: sum(1 for e in entregas if (e["an"].get("reproducibilidad") or {}).get(k) is True) for k, _ in G.REPRO},
    "con_textos_de_explicacion": sum(1 for e in entregas if any(a["rol"] == "explicacion" and a["publicado"] for a in e["archivos"])),
    "sin_codigo": [e["nombre"] for e in entregas if not any(a["rol"] == "principal" and a["tipo"] == "codigo" for a in e["archivos"])],
    "lineas_de_codigo_principal": sum(a["lineas"] for e in entregas for a in e["archivos"] if a["rol"] == "principal" and a["tipo"] == "codigo"),
    "fichas": [{"nombre": e["nombre"], "slug": e["slug"], "resumen": e["an"].get("resumen", ""), **{k: (v if not isinstance(v, str) else v[:420]) for k, v in (e["an"].get("ficha") or {}).items()},
                "tecnicas_en_la_entrega": e["an"].get("tecnicas_en_la_entrega") or []} for e in entregas],
}
(G.TRABAJO / "agregado.json").write_text(json.dumps(agregado, ensure_ascii=False, indent=1))
print(len(entregas), "entregas agregadas;", round((G.TRABAJO / "agregado.json").stat().st_size / 1024), "KB")
