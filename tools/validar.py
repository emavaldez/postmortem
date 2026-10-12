"""Valida el análisis de una entrega (JSON) contra el esquema, el vocabulario y los archivos de la copia canónica.
    python3 tools/validar.py _trabajo/analisis/<id>.json        (sale con código 0 si está bien)"""
import json, re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
VOC = json.load(open(RAIZ / "tools" / "vocabulario.json"))
CODIGOS = {f"{g}.{c}" for g, d in VOC.items() for c in d}
PROHIBIDAS = re.compile(r"(?i)\b(excelente|pobre(mente)?|prolij\w*|desprolij\w*|elegante\w*|lamentablemente|afortunadamente|recomend\w*|deber[ií]an?|convendr[ií]a\w*|acertad\w*|desacertad\w*|sofisticad\w*|"
                        r"interesante\w*|correctamente|incorrect\w*|adecuad\w*|inadecuad\w*|confus\w*|buena pr[aá]ctica|mala pr[aá]ctica|destaca\w*|notable\w*|valios\w*|ingenios\w*|cuidados\w*|"
                        r"descuidad\w*|s[oó]lid[oa]s?|flojo\w*|logra\w*|falla\w* en|error conceptual|bien (hecho|resuelto|pensado)|mal (hecho|resuelto|pensado))\b")
AVISO = re.compile(r"(?i)\b(mejor(es)?|peor(es)?|[oó]ptim\w*|robust\w*|simple(s|mente)?|complej\w*|b[aá]sic\w*|avanzad\w*|claro|clara)\b")

def textos(o, ruta=""):
    if isinstance(o, str):
        yield ruta, o
    elif isinstance(o, list):
        for i, x in enumerate(o):
            yield from textos(x, f"{ruta}[{i}]")
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from textos(v, f"{ruta}.{k}" if ruta else k)

def validar(path):
    err, avisos = [], []
    d = json.loads(Path(path).read_text())
    tarea = json.load(open(RAIZ / "_trabajo" / "tareas" / f"{d.get('id', '')}.json")) if (RAIZ / "_trabajo" / "tareas" / f"{d.get('id', '')}.json").exists() else None
    if tarea is None:
        return [f"id desconocido: {d.get('id')!r} (tiene que ser el id de la tarea)"], []
    largo = {a["ruta"]: a["lineas"] for a in tarea["archivos"]}
    def req(o, k, t, donde):
        if k not in o:
            err.append(f"falta {donde}.{k}"); return None
        if not isinstance(o[k], t):
            err.append(f"{donde}.{k} tiene que ser {t.__name__ if isinstance(t, type) else t}"); return None
        return o[k]
    res = req(d, "resumen", str, "raíz")
    if res is not None and not (200 <= len(res) <= 1600):
        err.append(f"resumen: {len(res)} caracteres (entre 200 y 1.600)")
    for k in ("que_entrega", "como_se_ejecuta"):
        req(d, k, str, "raíz")
    ficha = req(d, "ficha", dict, "raíz") or {}
    for k in ("lenguajes", "modelos", "meses_entrenamiento", "meses_validacion", "meses_prediccion"):
        req(ficha, k, list, "ficha")
    for k in ("clase_objetivo", "submuestreo", "calidad_de_datos", "drifting", "variables_intra_mes", "variables_historicas", "seleccion_de_variables", "optimizacion_de_hiperparametros",
              "hiperparametros_finales", "semillas", "ensamble", "corte", "validacion", "salidas"):
        v = req(ficha, k, str, "ficha")
        if v is not None and not v.strip():
            err.append(f"ficha.{k} vacío (si no aplica o no se ve en el código, escribir 'No se observa en el código')")
    for k in ("meses_entrenamiento", "meses_validacion", "meses_prediccion"):
        for m in ficha.get(k) or []:
            if not (isinstance(m, int) and 201901 <= m <= 202212):
                err.append(f"ficha.{k}: {m!r} no es un mes AAAAMM")
    if "cantidad_de_semillas" in ficha and ficha["cantidad_de_semillas"] is not None and not isinstance(ficha["cantidad_de_semillas"], int):
        err.append("ficha.cantidad_de_semillas tiene que ser entero o null")
    for k in ("tecnicas_en_la_entrega", "tecnicas_solo_exploradas"):
        for c in req(d, k, list, "raíz") or []:
            if c not in CODIGOS:
                err.append(f"{k}: código desconocido {c!r} (ver tools/vocabulario.json; formato grupo.codigo)")
    rep = req(d, "reproducibilidad", dict, "raíz") or {}
    for k in ("tiene_readme", "explica_como_ejecutar", "declara_versiones_o_dependencias", "fija_semillas", "usa_rutas_absolutas_o_de_una_maquina", "incluye_datos_o_predicciones", "es_un_solo_comando"):
        if k not in rep or not isinstance(rep[k], bool):
            err.append(f"reproducibilidad.{k} tiene que ser true o false")
    req(rep, "entorno_declarado", str, "reproducibilidad")
    def refs(lista, donde):
        for i, r in enumerate(lista or []):
            if not isinstance(r, dict) or r.get("ruta") not in largo:
                err.append(f"{donde}[{i}]: ruta inexistente {r.get('ruta') if isinstance(r, dict) else r!r}"); continue
            a, b = r.get("desde"), r.get("hasta")
            if not (isinstance(a, int) and isinstance(b, int) and 1 <= a <= b <= largo[r["ruta"]]):
                err.append(f"{donde}[{i}]: líneas {a}-{b} fuera de 1-{largo[r['ruta']]} en {r['ruta']}")
    pasos = req(d, "pasos", list, "raíz") or []
    if not (2 <= len(pasos) <= 16) and largo and any(a["tipo"] == "codigo" for a in tarea["archivos"]):
        err.append(f"pasos: {len(pasos)} (entre 2 y 16)")
    for i, p in enumerate(pasos):
        if not isinstance(p, dict) or not p.get("titulo") or not p.get("descripcion"):
            err.append(f"pasos[{i}] necesita titulo y descripcion"); continue
        refs(p.get("referencias"), f"pasos[{i}].referencias")
    vistos = set()
    for i, a in enumerate(req(d, "archivos", list, "raíz") or []):
        if not isinstance(a, dict) or a.get("ruta") not in largo:
            err.append(f"archivos[{i}]: ruta inexistente {a.get('ruta') if isinstance(a, dict) else a!r}"); continue
        if a["ruta"] in vistos:
            err.append(f"archivos: {a['ruta']} repetido")
        vistos.add(a["ruta"])
        if a.get("rol") not in ("principal", "secundario", "explicacion", "configuracion", "ajeno"):
            err.append(f"archivos[{i}].rol inválido: {a.get('rol')!r}")
        if not isinstance(a.get("descripcion"), str) or not a["descripcion"].strip():
            err.append(f"archivos[{i}] ({a['ruta']}): falta descripcion")
        ant = a.get("anotaciones") or []
        fin = 0
        for j, n in enumerate(ant):
            x, y = n.get("desde"), n.get("hasta")
            if not (isinstance(x, int) and isinstance(y, int) and 1 <= x <= y <= largo[a["ruta"]]):
                err.append(f"archivos[{i}].anotaciones[{j}]: líneas {x}-{y} fuera de 1-{largo[a['ruta']]} ({a['ruta']})"); continue
            if x <= fin:
                err.append(f"archivos[{i}].anotaciones[{j}]: se pisa con la anterior o está desordenada ({a['ruta']} línea {x})")
            fin = y
            if not isinstance(n.get("texto"), str) or len(n["texto"].strip()) < 15:
                err.append(f"archivos[{i}].anotaciones[{j}]: texto muy corto")
    for i, c in enumerate(d.get("carpetas") or []):
        if not isinstance(c, dict) or not isinstance(c.get("carpeta"), str) or not any(r.startswith(c["carpeta"]) for r in largo):
            err.append(f"carpetas[{i}]: {c.get('carpeta') if isinstance(c, dict) else c!r} no contiene ningún archivo de la tarea"); continue
        if c.get("rol") not in ("principal", "secundario", "explicacion", "configuracion", "ajeno"):
            err.append(f"carpetas[{i}].rol inválido: {c.get('rol')!r}")
        if not isinstance(c.get("descripcion"), str) or not c["descripcion"].strip():
            err.append(f"carpetas[{i}]: falta descripcion")
    meta = {a["ruta"]: a for a in tarea["archivos"]}
    for a in d.get("archivos") or []:
        m = meta.get(a.get("ruta"))
        if m and a.get("rol") == "principal" and m["tipo"] == "codigo" and m["proporcion_comentarios"] < 0.08 and m["lineas"] >= 30 and not a.get("anotaciones") and a["ruta"] not in " ".join(d.get("no_cubierto") or []):
            err.append(f"{a['ruta']}: es principal, casi no tiene comentarios ({m['proporcion_comentarios']:.0%}) y no trae anotaciones (o nombrarlo en no_cubierto con el motivo)")
    req(d, "no_cubierto", list, "raíz")
    for ruta, t in textos({k: v for k, v in d.items() if k not in ("id",)}):
        for mo in PROHIBIDAS.finditer(t):
            err.append(f"palabra de opinión {mo.group(0)!r} en {ruta}: reescribir como descripción de lo que hace el código")
        for mo in AVISO.finditer(t):
            avisos.append(f"{mo.group(0)!r} en {ruta}")
    return err, avisos

if __name__ == "__main__":
    e, a = validar(sys.argv[1])
    for x in e[:60]:
        print("ERROR:", x)
    if a:
        print(f"AVISO: {len(a)} usos de palabras ambiguas (revisar que describan lo que el código elige, no una valoración):", "; ".join(a[:12]))
    print("VÁLIDO" if not e else f"{len(e)} errores")
    sys.exit(1 if e else 0)
