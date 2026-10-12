"""Arma la copia canónica de cada entrega (texto plano, con los notebooks pasados a texto celda por celda y los secretos tapados)
y la lista de archivos que recibe cada lector. Escribe _trabajo/fuentes/<repo>/... y _trabajo/tareas/<repo>.json."""
import json, os, re, shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGEN = Path(os.environ.get("POSTMORTEM_ORIGEN", "../primeracompetencia")).resolve()  # carpeta con un clon por entrega y manifest.csv
FUENTES, TAREAS = RAIZ / "_trabajo" / "fuentes", RAIZ / "_trabajo" / "tareas"
MAX_LINEAS = 5000
CONFIG = {".yml", ".yaml", ".toml", ".json"}
SECRETOS = [
    (re.compile(r"""(?i)\b(api[_-]?key|apikey|token|password|passwd|secret)\b(["']?\s*[:=]\s*)(["'])[A-Za-z0-9_\-+/=.]{16,}\3"""), r"\1\2\3***REDACTADO***\3"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "***REDACTADO***"),
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}\b"), "***REDACTADO***"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b"), "***REDACTADO***"),
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[correo]"),
]

def es_dato(nombre, lineas):
    """Un .txt que no es prosa: volcado de modelo, tabla de números, lista de ids."""
    con = [l for l in lineas if l.strip()]
    if not con or "requirement" in nombre.lower():
        return False
    num = sum(1 for l in con if re.fullmatch(r"[\d\s.,;:eE+\-\t|/]+", l.strip()))
    primera = con[0].strip().lower()
    return num / len(con) > 0.5 or primera in ("tree", "numero_de_cliente") or primera.startswith(("tree=", "version=v")) or (len(con) > 300 and sum(l.count("\t") + l.count(",") for l in con[:50]) > 150)

def tapar(t):
    n = 0
    for rx, rep in SECRETOS:
        t, k = rx.subn(rep, t); n += k
    return t, n

def notebook(p):
    nb = json.loads(p.read_text(errors="replace"))
    out, k = [], 0
    for c in nb.get("cells", []):
        src = c.get("source", ""); src = "".join(src) if isinstance(src, list) else src
        if not src.strip():
            continue
        k += 1
        tipo = {"code": "código", "markdown": "texto"}.get(c.get("cell_type"), c.get("cell_type", "otro"))
        out.append(f"#%% celda {k} [{tipo}]")
        out.extend(src.rstrip("\n").split("\n"))
        out.append("")
    return "\n".join(out)

inv = json.load(open(RAIZ / "_trabajo" / "inventario.json"))["repos"]
gh = json.load(open(RAIZ / "_trabajo" / "github.json"))
for d in (FUENTES, TAREAS):
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
tot_lin = tot_arch = tot_red = 0
for r in inv:
    base, lista, red, datos_txt = ORIGEN / r["dir"], [], 0, []
    for a in r["archivos"]:
        if a["tipo"] not in ("codigo", "texto"):
            continue
        p = base / a["ruta"]
        try:
            t = notebook(p) if a["ext"] == ".ipynb" else p.read_text(errors="replace")
        except Exception:
            continue
        t = t.replace("\r\n", "\n").replace("\r", "\n").expandtabs(4)
        t, k = tapar(t); red += k
        lineas = t.split("\n")
        while lineas and not lineas[-1].strip():
            lineas.pop()
        if not lineas:
            continue
        if a["ext"] == ".txt" and es_dato(a["ruta"], lineas):
            datos_txt.append(a["ruta"]); continue
        cortado = len(lineas) > MAX_LINEAS
        if cortado:
            lineas = lineas[:MAX_LINEAS]
        lineas = [l if len(l) <= 4000 else l[:4000] + " …[línea recortada]" for l in lineas]
        dest = FUENTES / r["dir"] / (a["ruta"] + (".txt" if a["ext"] == ".ipynb" else ("" if Path(a["ruta"]).suffix else ".md")))
        dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text("\n".join(lineas) + "\n")
        nl = sum(1 for l in lineas if l.strip())
        lista.append({"ruta": a["ruta"], "copia": str(dest), "tipo": "configuracion" if a["ext"] in CONFIG else a["tipo"], "lenguaje": a.get("lenguaje", ""), "lineas": len(lineas),
                      "lineas_con_contenido": nl, "lineas_de_comentario": a.get("comentarios", 0), "proporcion_comentarios": round(a.get("comentarios", 0) / max(1, a.get("lineas", nl)), 3),
                      "repos_con_el_mismo_contenido": a.get("en_repos", 1), "dentro_del_link_posteado": a["en_alcance"], "recortado": cortado})
        tot_lin += len(lineas); tot_arch += 1
    docs = [{"ruta": a["ruta"], "bytes": a["bytes"]} for a in r["archivos"] if a["tipo"] == "documento"]
    otros = {}
    for a in r["archivos"]:
        if a["tipo"] in ("otro", "dato", "grande"):
            otros[a["ext"] or "(sin extensión)"] = otros.get(a["ext"] or "(sin extensión)", 0) + 1
    g = gh.get(r["repo"], {})
    tarea = {"id": r["dir"], "repo": r["repo"], "usuario": r["repo"].split("/")[0], "nombre_publico": g.get("nombre_publico", ""), "url_posteada": r["url"], "subruta_posteada": r["subpath"],
             "rama": r["rama"], "commit": r["commit"], "es_fork": bool(g.get("f")), "licencia": g.get("l", ""), "carpeta_original": str(base), "carpeta_copia": str(FUENTES / r["dir"]),
             "archivos": lista, "txt_que_son_datos": datos_txt, "documentos_no_texto": docs, "otros_archivos_por_extension": otros, "secretos_tapados": red}
    (TAREAS / f"{r['dir']}.json").write_text(json.dumps(tarea, ensure_ascii=False, indent=1))
    tot_red += red
print(f"{len(inv)} repos | {tot_arch} archivos de texto | {tot_lin} líneas | {tot_red} datos tapados")
import collections
c = collections.Counter(); 
for r in inv:
    t = json.load(open(TAREAS / f"{r['dir']}.json"))
    for a in t["archivos"]: c[a["lenguaje"]] += a["lineas"]
print(dict(c.most_common(12)))
