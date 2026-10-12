"""Inventario de las entregas: por repo, qué archivos de código y de texto hay dentro del alcance posteado, con tamaño, líneas,
proporción de comentarios y en cuántos repos aparece el mismo contenido. Escribe _trabajo/inventario.json."""
import csv, hashlib, json, os, re, sys
from pathlib import Path

ORIGEN = Path(os.environ.get("POSTMORTEM_ORIGEN", "../primeracompetencia")).resolve()  # carpeta con un clon por entrega y manifest.csv
SALIDA = Path(__file__).resolve().parents[1] / "_trabajo" / "inventario.json"
CODIGO = {".r": "R", ".rmd": "R Markdown", ".qmd": "Quarto", ".py": "Python", ".ipynb": "Jupyter", ".sql": "SQL", ".sh": "Shell", ".jl": "Julia",
          ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML", ".json": "JSON", ".bat": "Batch", ".ps1": "PowerShell", ".cpp": "C++"}
TEXTO = {".md": "Markdown", ".txt": "Texto", ".rst": "Texto"}
OTROS_DOC = {".pdf", ".docx", ".doc", ".pptx", ".html", ".htm", ".odt"}
IGNORAR_DIR = {".git", ".ipynb_checkpoints", "__pycache__", ".Rproj.user", "node_modules", ".venv", "venv", "renv", ".idea", ".vscode"}

def comentarios(texto, ext):
    lineas = [l for l in texto.splitlines() if l.strip()]
    if not lineas:
        return 0, 0
    if ext in (".r", ".py", ".sh", ".yml", ".yaml", ".toml", ".jl", ".rmd", ".qmd", ".ps1"):
        c = sum(1 for l in lineas if l.strip().startswith("#"))
    elif ext == ".sql":
        c = sum(1 for l in lineas if l.strip().startswith("--"))
    elif ext == ".cpp":
        c = sum(1 for l in lineas if l.strip().startswith(("//", "/*", "*")))
    else:
        c = 0
    return len(lineas), c

def celdas(path):
    try:
        nb = json.loads(path.read_text(errors="replace"))
    except Exception:
        return None
    out = []
    for c in nb.get("cells", []):
        src = c.get("source", "")
        src = "".join(src) if isinstance(src, list) else src
        out.append({"tipo": c.get("cell_type", "code"), "fuente": src})
    leng = (nb.get("metadata", {}).get("kernelspec", {}) or {}).get("language") or (nb.get("metadata", {}).get("language_info", {}) or {}).get("name") or ""
    return {"celdas": out, "lenguaje": leng}

filas = list(csv.DictReader(open(ORIGEN / "manifest.csv")))
repos, por_hash = [], {}
for f in filas:
    if f["estado_clon"] != "OK":
        continue
    base = ORIGEN / f["dir"]
    sub = f["subpath_link"] if f["subpath_presente"].startswith("si") else ""
    alcance = base / sub if sub else base
    archivos = []
    raices = [alcance] if alcance.is_dir() else [alcance.parent]
    solo = alcance if alcance.is_file() else None
    for raiz in raices:
        for dp, dn, fn in os.walk(raiz):
            dn[:] = [d for d in dn if d not in IGNORAR_DIR]
            for n in fn:
                p = Path(dp) / n
                ext = p.suffix.lower()
                rel = str(p.relative_to(base))
                try:
                    tam = p.stat().st_size
                except OSError:
                    continue
                if not ext and not n.startswith(".") and 0 < tam < 3_000_000:
                    try:
                        cabeza = p.read_bytes()[:400].decode("utf-8")
                        ext = ".ipynb" if '"nbformat"' in cabeza or '"cells"' in cabeza else (".md" if n.lower() not in ("license", "makefile", "dockerfile") else "")
                    except UnicodeDecodeError:
                        ext = ""
                en_alcance = solo is None or p == solo
                if ext in CODIGO or ext in TEXTO or n.lower().startswith(("readme", "leeme")):
                    if ext == ".json" and tam > 200_000:
                        archivos.append({"ruta": rel, "tipo": "dato", "ext": ext, "bytes": tam, "en_alcance": en_alcance}); continue
                    if ext == ".ipynb":
                        nb = celdas(p)
                        if nb is None:
                            continue
                        cod = "\n".join(c["fuente"] for c in nb["celdas"] if c["tipo"] == "code")
                        md = "\n".join(c["fuente"] for c in nb["celdas"] if c["tipo"] == "markdown")
                        nl, nc = comentarios(cod, ".py" if "py" in nb["lenguaje"].lower() else ".r")
                        h = hashlib.sha1(cod.encode()).hexdigest()
                        archivos.append({"ruta": rel, "tipo": "codigo", "lenguaje": "Jupyter (" + (nb["lenguaje"] or "?") + ")", "ext": ext, "bytes": tam, "lineas": nl,
                                         "comentarios": nc, "celdas_codigo": sum(c["tipo"] == "code" for c in nb["celdas"]), "celdas_texto": sum(c["tipo"] == "markdown" for c in nb["celdas"]),
                                         "bytes_fuente": len(cod) + len(md), "sha1": h, "en_alcance": en_alcance})
                    else:
                        if tam > 600_000:
                            archivos.append({"ruta": rel, "tipo": "grande", "ext": ext, "bytes": tam, "en_alcance": en_alcance}); continue
                        t = p.read_text(errors="replace")
                        nl, nc = comentarios(t, ext)
                        h = hashlib.sha1(re.sub(r"\s+", " ", t).strip().encode()).hexdigest()
                        tipo = "codigo" if ext in CODIGO else "texto"
                        archivos.append({"ruta": rel, "tipo": tipo, "lenguaje": CODIGO.get(ext) or TEXTO.get(ext) or "Texto", "ext": ext, "bytes": tam, "lineas": nl,
                                         "comentarios": nc, "sha1": h, "en_alcance": en_alcance})
                    if archivos[-1].get("sha1"):
                        por_hash.setdefault(archivos[-1]["sha1"], set()).add(f["dir"])
                elif ext in OTROS_DOC:
                    archivos.append({"ruta": rel, "tipo": "documento", "ext": ext, "bytes": tam, "en_alcance": en_alcance})
                else:
                    archivos.append({"ruta": rel, "tipo": "otro", "ext": ext, "bytes": tam, "en_alcance": en_alcance})
    repos.append({"msg_id": f["msg_id"], "autor_zulip": f["autor"], "url": f["url_posted"], "repo": f["repo"], "dir": f["dir"], "subpath": sub,
                  "rama": f["rama_actual"], "commit": f["head"], "archivos": archivos})
for r in repos:
    for a in r["archivos"]:
        if a.get("sha1"):
            a["en_repos"] = len(por_hash[a["sha1"]])
SALIDA.write_text(json.dumps({"repos": repos}, ensure_ascii=False))
print(len(repos), "repos")
for r in repos:
    cod = [a for a in r["archivos"] if a["tipo"] == "codigo" and a["ext"] not in (".json", ".yml", ".yaml", ".toml")]
    prop = [a for a in cod if a.get("en_repos", 1) < 3]
    txt = [a for a in r["archivos"] if a["tipo"] == "texto"]
    doc = [a for a in r["archivos"] if a["tipo"] == "documento"]
    print(f"{r['dir'][:44]:44s} sub={r['subpath'][:28]:28s} código {len(cod):3d} (propios {len(prop):3d}, {sum(a['bytes'] for a in prop)//1024:5d} KB, {sum(a.get('lineas',0) for a in prop):6d} líneas) | texto {len(txt):3d} | docs {len(doc):2d}")
