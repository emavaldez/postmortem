"""Genera el sitio estático del postmortem a partir de las tareas (_trabajo/tareas), las lecturas verificadas
(_trabajo/analisis) y la copia canónica de cada entrega (_trabajo/fuentes).

    python3 tools/generar.py

Escribe en la raíz del repositorio: index.html, entregas/, comparar.html, tecnicas.html, reproducibilidad.html, buscar.html,
glosario.html, data/, md/, fuentes/, comentado/, llms.txt.
"""
import csv, datetime, json, re, shutil, subprocess, textwrap
from pathlib import Path
from urllib.parse import quote

from texto import esc, markdown, resaltar

RAIZ = Path(__file__).resolve().parents[1]
TRABAJO = RAIZ / "_trabajo"
VOC = json.load(open(RAIZ / "tools" / "vocabulario.json"))
GRUPOS = {"modelo": "Modelo", "clase": "Clase", "datos": "Datos", "drifting": "Drifting", "variables": "Variables", "hiperparametros": "Hiperparámetros",
          "validacion": "Validación", "ensamble": "Ensamble", "corte": "Corte", "final": "Modelo final", "proceso": "Proceso"}
ETIQUETA = {f"{g}.{c}": n for g, d in VOC.items() for c, n in d.items()}
SITIO = "https://emavaldez.github.io/postmortem/"
REPO_SITIO = "https://github.com/emavaldez/postmortem"
HOY = datetime.date.today().isoformat()
ROLES = {"principal": "Principal", "secundario": "Secundario", "explicacion": "Explicación", "configuracion": "Configuración", "ajeno": "Ajeno a la competencia"}
CAMPOS = [("lenguajes", "Lenguajes"), ("modelos", "Modelos"), ("clase_objetivo", "Clase que entrena"), ("meses_entrenamiento", "Meses de entrenamiento"),
          ("meses_validacion", "Meses de validación"), ("meses_prediccion", "Mes que predice"), ("submuestreo", "Submuestreo"), ("calidad_de_datos", "Calidad de datos"),
          ("drifting", "Drifting"), ("variables_intra_mes", "Variables dentro del mes"), ("variables_historicas", "Variables históricas"),
          ("seleccion_de_variables", "Selección de variables"), ("optimizacion_de_hiperparametros", "Optimización de hiperparámetros"),
          ("hiperparametros_finales", "Hiperparámetros finales"), ("semillas", "Semillas"), ("cantidad_de_semillas", "Cantidad de semillas"), ("ensamble", "Ensamble"),
          ("corte", "Corte"), ("validacion", "Validación"), ("salidas", "Salidas")]
REPRO = [("tiene_readme", "Tiene README o texto de presentación"), ("explica_como_ejecutar", "Explica cómo ejecutar"),
         ("declara_versiones_o_dependencias", "Declara versiones o dependencias"), ("fija_semillas", "Fija las semillas"),
         ("usa_rutas_absolutas_o_de_una_maquina", "Usa rutas absolutas o de una máquina"), ("incluye_datos_o_predicciones", "Incluye datos o predicciones"),
         ("es_un_solo_comando", "Sale de un solo script o notebook")]
PISTAS = {  # dónde buscar un ejemplo de cada técnica en el código principal (primera línea que coincide)
    "modelo.lightgbm": r"lightgbm|lgb\.", "modelo.xgboost": r"xgboost|xgb\.", "modelo.catboost": r"catboost", "modelo.random_forest": r"ranger|randomForest|RandomForest|boosting.{0,12}rf",
    "modelo.arbol_decision": r"rpart|DecisionTree", "modelo.regresion_logistica": r"LogisticRegression|glm\(", "modelo.red_neuronal": r"keras|torch|MLPClassifier|nnet",
    "clase.binaria_baja2": r"BAJA\+2", "clase.binaria_baja1_baja2": r"BAJA\+1", "clase.multiclase": r"multiclass|num_class", "clase.pesos_por_clase": r"weight|is_unbalance",
    "clase.clase_artificial": r"pseudo|artificial", "datos.submuestreo_continua": r"undersampl|submuestr|runif|\.sample\(|azar", "datos.variables_rotas_a_na": r"\bNA\b|np\.nan|None",
    "datos.excluye_variables": r"prestamos_personales|drop\(|setdiff", "datos.excluye_meses": r"foto_mes", "drifting.rank_por_mes": r"frank|rank\(|percent", "drifting.rank_cero_fijo": r"cero|frank|rank",
    "drifting.deflacion": r"ipc|defla|dolar|uva", "drifting.estandarizacion_por_mes": r"scale\(|standard|zscore|normaliz", "variables.intra_mes": r"/|ratio|suma|vm_",
    "variables.lags": r"lag|shift\(", "variables.deltas": r"delta|diff", "variables.tendencias": r"tend|slope|pendiente|fhist", "variables.promedios_ventana": r"avg|frollmean|rolling|promedio|mean",
    "variables.min_max_ventana": r"min|max", "variables.ratios_historia": r"ratio", "variables.canaritos": r"canarit", "variables.seleccion_por_importancia": r"importan",
    "hiperparametros.optimizacion_bayesiana": r"mlrMBO|mlr3mbo|bbotk|skopt|[Bb]ayes", "hiperparametros.optuna": r"optuna", "hiperparametros.grilla_o_azar": r"GridSearch|RandomizedSearch|expand\.grid|grilla",
    "hiperparametros.fijos": r"learning_rate|num_leaves|eta", "validacion.mes_futuro": r"valid|test|future", "validacion.particion_aleatoria": r"train_test_split|createDataPartition|particion|sample",
    "validacion.validacion_cruzada": r"cv\b|KFold|fold|cross", "validacion.varios_meses_de_prueba": r"valid|test|backtest", "validacion.ganancia_como_metrica": r"gananc|1072500|780000|273000",
    "ensamble.semillerio": r"semill|seed", "ensamble.modelos_distintos": r"ensamble|ensemble|promedio|mean", "ensamble.stacking": r"stack", "corte.cantidad_fija": r"envios|corte|top|head\(|\[1:",
    "corte.umbral_probabilidad": r"umbral|threshold|> *0\.\d|1/40|0\.025", "corte.elegido_en_validacion": r"gananc|cumsum|corte", "corte.varios_cortes": r"cortes|seq\(|range\(",
    "final.reentrena_con_todo": r"train_final|final", "proceso.bitacora": r".", "proceso.uso_de_ia_declarado": r".", "proceso.automatizacion_envios": r"zulip|kaggle|submit|requests",
}


# ---------------------------------------------------------------------------------------------- carga

def cargar():
    entregas, usados = [], set()
    for f in sorted((TRABAJO / "tareas").glob("*.json")):
        t = json.load(open(f))
        slug = re.sub(r"[^a-z0-9\-]+", "-", t["usuario"].lower()).strip("-")
        if slug in usados:
            slug += "-" + re.sub(r"[^a-z0-9\-]+", "-", t["repo"].split("/")[1].lower())
        usados.add(slug)
        try:
            sha = subprocess.run(["git", "-C", t["carpeta_original"], "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() or t["commit"]
        except Exception:
            sha = t["commit"]
        final, borr = TRABAJO / "analisis" / f"{t['id']}.json", TRABAJO / "borrador" / f"{t['id']}.json"
        an, estado = None, "pendiente"
        for p, e in ((final, "verificada"), (borr, "sin verificar")):
            if p.exists():
                try:
                    an, estado = json.load(open(p)), e
                    break
                except Exception:
                    pass
        an = an or {}
        porruta = {a["ruta"]: a for a in an.get("archivos") or [] if isinstance(a, dict)}
        carpetas = sorted((c for c in an.get("carpetas") or [] if isinstance(c, dict) and c.get("carpeta")), key=lambda c: -len(c["carpeta"]))
        archivos = []
        for i, a in enumerate(t["archivos"]):
            x = porruta.get(a["ruta"])
            nombre = a["ruta"].split("/")[-1].lower()
            if x:
                rol, desc, notas = x.get("rol") or "secundario", x.get("descripcion") or "", x.get("anotaciones") or []
            else:
                c = next((c for c in carpetas if a["ruta"].startswith(c["carpeta"])), None)
                if c:
                    rol, desc, notas = c.get("rol") or "secundario", "", []
                else:
                    rol = "configuracion" if a["tipo"] == "configuracion" else ("explicacion" if a["tipo"] == "texto" and nombre.startswith(("readme", "leeme", "reproducir")) else "secundario")
                    if not an and a["tipo"] == "codigo":
                        rol = "principal"
                    desc, notas = "", []
            notas = sorted((n for n in notas if isinstance(n, dict) and isinstance(n.get("desde"), int) and isinstance(n.get("hasta"), int) and 1 <= n["desde"] <= n["hasta"] <= a["lineas"]), key=lambda n: n["desde"])
            archivos.append({**a, "rol": rol, "descripcion": desc, "anotaciones": notas, "ancla": f"a{i}", "publicado": rol != "ajeno",
                             "texto": f"fuentes/{slug}/{a['ruta']}.txt" if rol != "ajeno" else None,
                             "github": f"https://github.com/{t['repo']}/blob/{sha}/{quote(a['ruta'])}"})
        entregas.append({"slug": slug, "id": t["id"], "usuario": t["usuario"], "nombre": (t.get("nombre_publico") or "").strip() or t["usuario"], "repo": t["repo"],
                         "url_repo": f"https://github.com/{t['repo']}", "url_posteada": t["url_posteada"], "subruta": t["subruta_posteada"], "sha": sha, "rama": t["rama"],
                         "es_fork": t.get("es_fork", False), "licencia": t.get("licencia", ""), "an": an, "estado": estado, "archivos": archivos,
                         "documentos": t.get("documentos_no_texto", []), "otros": t.get("otros_archivos_por_extension", {}), "txt_datos": t.get("txt_que_son_datos", []),
                         "tapados": t.get("secretos_tapados", 0)})
    entregas.sort(key=lambda e: e["nombre"].lower())
    return entregas


def leer(a):
    return Path(a["copia"]).read_text().rstrip("\n").split("\n")


# ---------------------------------------------------------------------------------------------- piezas de HTML

def pagina(titulo, cuerpo, raiz="", actual="", descripcion="", ancho=False, alternos=()):
    nav = [("index.html", "Resumen", "inicio"), ("index.html#entregas", "Entregas", "entregas"), ("comparar.html", "Comparar", "comparar"), ("fichas.html", "Fichas", "fichas"), ("tecnicas.html", "Técnicas", "tecnicas"),
           ("reproducibilidad.html", "Reproducibilidad", "repro"), ("buscar.html", "Buscar en el código", "buscar"), ("glosario.html", "Glosario", "glosario"),
           ("agentes.html", "Para agentes", "agentes")]
    enlaces = "".join(f'<a href="{raiz}{h}"{" aria-current=\"page\"" if k == actual else ""}>{n}</a>' for h, n, k in nav)
    alt = "".join(f'<link rel="alternate" type="{t}" href="{h}" title="{esc(n)}">' for t, h, n in alternos)
    return f"""<!doctype html>
<html lang="es" data-raiz="{raiz}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)} · Postmortem Primera Competencia DMEyF 2026</title>
<meta name="description" content="{esc(descripcion or titulo)}">
<link rel="stylesheet" href="{raiz}assets/estilo.css">
<link rel="help" href="{raiz}llms.txt" title="Guía para agentes">
{alt}
<script src="{raiz}assets/app.js" defer></script>
</head>
<body>
<header class="barra"><div class="barra-int"><a class="marca" href="{raiz}index.html">Postmortem · Primera Competencia</a><nav aria-label="Secciones">{enlaces}</nav></div></header>
<main{' class="ancho"' if ancho else ''}>
{cuerpo}
<footer class="pie">
<p>Página armada el {HOY} a partir de los repositorios públicos que cada alumno posteó como entrega de la Primera Competencia de DMEyF 2026 (UBA). Las descripciones y las anotaciones del código son lecturas automáticas hechas con asistencia de IA y revisadas por una segunda pasada automática; describen lo que el código hace, sin valorarlo, y pueden contener errores. El código y los textos de cada entrega pertenecen a sus autores y se muestran tal como estaban en el commit indicado en cada página.</p>
<p>Para corregir una descripción o pedir que se retire una entrega: <a href="{REPO_SITIO}/issues">abrir un issue</a>. <a href="{raiz}agentes.html">Versión para agentes</a> · <a href="{raiz}llms.txt">llms.txt</a> · <a href="{REPO_SITIO}">repositorio de esta página</a>.</p>
</footer>
</main>
</body>
</html>
"""


def chips(codigos, clase="si", raiz=""):
    return "".join(f'<a class="chip {clase}" href="{raiz}tecnicas.html#{c.replace(".", "-")}">{esc(ETIQUETA.get(c, c))}</a>' for c in codigos if c in ETIQUETA)


def valor(v):
    if isinstance(v, list):
        return ", ".join(str(x) for x in v) if v else "—"
    return "—" if v in (None, "") else str(v)


def si_no(v):
    return '<span class="si-no si">Sí</span>' if v is True else '<span class="si-no no">No</span>' if v is False else "—"


def html_codigo(a, lineas=None):
    lineas = leer(a) if lineas is None else lineas
    cuaderno = a["lenguaje"].startswith("Jupyter")
    notas = {n["desde"]: n for n in a["anotaciones"]}
    out, prosa = [], False
    if cuaderno:
        res, tramo, ini = [None] * len(lineas), [], 0
        def volcar(tr, i0):
            for k, h in enumerate(resaltar(tr, a["lenguaje"])):
                res[i0 + k] = h
        modo = False
        for i, l in enumerate(lineas):
            if l.startswith("#%% celda"):
                if tramo:
                    volcar(tramo, ini); tramo = []
                modo = "[texto]" in l
            elif not modo:
                if not tramo:
                    ini = i
                tramo.append(l)
            if modo and tramo:
                volcar(tramo, ini); tramo = []
        if tramo:
            volcar(tramo, ini)
    else:
        res = resaltar(lineas, a["lenguaje"])
    for i, l in enumerate(lineas):
        k = i + 1
        if k in notas:
            n = notas[k]
            out.append(f'<div class="nota"><span class="rango">Anotación · líneas {n["desde"]}–{n["hasta"]}</span>{esc(n["texto"])}</div>')
        cls = "l"
        if cuaderno and l.startswith("#%% celda"):
            prosa = "[texto]" in l; cls += " celda"; cuerpo = esc(l[4:])
        elif cuaderno and prosa:
            cls += " prosa"; cuerpo = esc(l)
        else:
            cuerpo = res[i] if res[i] is not None else esc(l)
        out.append(f'<div class="{cls}" id="{a["ancla"]}-L{k}"><a class="ln" href="#{a["ancla"]}-L{k}">{k}</a><span class="t">{cuerpo or " "}</span></div>')
    return "".join(out)


def comentado(a):
    """El archivo con las anotaciones intercaladas como comentarios, antes de cada bloque."""
    pref = "-- " if "SQL" in a["lenguaje"] else "# "
    notas = {n["desde"]: n for n in a["anotaciones"]}
    out = [f"{pref}Copia con anotaciones agregadas por la página del postmortem (no son del autor). Los números de línea de cada", f"{pref}anotación son los del archivo original, sin estas líneas agregadas.", ""]
    for i, l in enumerate(leer(a)):
        if i + 1 in notas:
            n = notas[i + 1]
            for j, w in enumerate(textwrap.wrap(f"[Anotación · líneas {n['desde']}–{n['hasta']}] {n['texto']}", 108)):
                out.append(pref + ("" if j == 0 else "  ") + w)
        out.append(l)
    return "\n".join(out) + "\n"


def evidencia(e, codigo):
    rx = PISTAS.get(codigo)
    if not rx:
        return None
    rx = re.compile(rx, re.I)
    for a in e["archivos"]:
        if a["rol"] == "principal" and a["tipo"] == "codigo":
            for i, l in enumerate(leer(a)):
                if rx.search(l) and not l.startswith("#%% celda"):
                    return f'{a["ancla"]}-L{i + 1}'
    return None


# ---------------------------------------------------------------------------------------------- página de una entrega

def pagina_entrega(e, entregas):
    an, raiz = e["an"], "../../"
    ficha, rep = an.get("ficha") or {}, an.get("reproducibilidad") or {}
    princ = [a for a in e["archivos"] if a["rol"] == "principal" and a["tipo"] != "texto"]
    expl = [a for a in e["archivos"] if a["publicado"] and (a["rol"] == "explicacion" or (a["tipo"] == "texto" and a["rol"] == "principal"))]
    expl.sort(key=lambda a: (not a["ruta"].split("/")[-1].lower().startswith(("readme", "leeme")), a["ruta"].count("/"), a["ruta"]))
    otros = [a for a in e["archivos"] if a["publicado"] and a not in princ and a not in expl]
    ajenos = [a for a in e["archivos"] if not a["publicado"]]
    n_notas = sum(len(a["anotaciones"]) for a in princ)
    c = []
    c.append(f'<p class="meta"><a href="{raiz}index.html#entregas">Entregas</a> › {esc(e["nombre"])}</p>')
    c.append(f'<h1>{esc(e["nombre"])}</h1>')
    sub = f' · carpeta o archivo posteado: <code>{esc(e["subruta"])}</code>' if e["subruta"] else ""
    c.append(f'<p class="bajada">Entrega de <strong>{esc(e["usuario"])}</strong> · repositorio <a href="{esc(e["url_repo"])}" rel="noopener">{esc(e["repo"])}</a>{sub} · commit <a href="{esc(e["url_repo"])}/tree/{e["sha"]}" rel="noopener"><code>{e["sha"][:7]}</code></a>{" · fork" if e["es_fork"] else ""}</p>')
    estado = {"verificada": "Lectura revisada por una segunda pasada automática (datos principales de la ficha y una muestra de las anotaciones).", "sin verificar": "Lectura sin la segunda revisión.", "pendiente": "Todavía no hay lectura de esta entrega: se muestran sólo los archivos."}[e["estado"]]
    c.append(f'<p class="meta">{estado} <a href="{esc(e["url_posteada"])}" rel="noopener">Link posteado por el alumno</a> · <a href="{raiz}comparar.html?a={e["slug"]}">comparar con otra entrega</a> · <a href="{raiz}md/{e["slug"]}.md">versión Markdown</a> · <a href="{raiz}data/entregas/{e["slug"]}.json">JSON</a></p>')
    c.append('<nav class="chips" aria-label="En esta página"><a class="chip" href="#resumen">Resumen</a><a class="chip" href="#ficha">Ficha</a><a class="chip" href="#pasos">Pasos</a><a class="chip" href="#explicaciones">Explicaciones del alumno</a><a class="chip" href="#codigo">Código</a><a class="chip" href="#otros">Otros archivos</a></nav>')
    c.append('<h2 id="resumen">Resumen</h2>')
    if an:
        c.append(f'<p style="max-width:62rem">{esc(an.get("resumen", ""))}</p>')
        c.append(f'<p style="max-width:62rem"><strong>Qué entrega.</strong> {esc(an.get("que_entrega", ""))}</p><p style="max-width:62rem"><strong>Cómo se ejecuta.</strong> {esc(an.get("como_se_ejecuta", ""))}</p>')
    else:
        c.append('<p class="aviso">Esta entrega todavía no tiene una lectura. Abajo están sus archivos tal como se subieron.</p>')
    if an:
        c.append('<h2 id="ficha">Ficha</h2><div class="tabla"><table class="ficha"><tbody>')
        for k, n in CAMPOS:
            c.append(f'<tr><th scope="row">{n}</th><td>{esc(valor(ficha.get(k)))}</td></tr>')
        c.append("</tbody></table></div>")
        c.append('<h3>Técnicas que usa el camino de la entrega</h3><div class="chips">' + (chips(an.get("tecnicas_en_la_entrega") or [], "si", raiz) or '<span class="meta">Ninguna del vocabulario.</span>') + "</div>")
        if an.get("tecnicas_solo_exploradas"):
            c.append('<h3>Técnicas que aparecen sólo en archivos de exploración</h3><div class="chips">' + chips(an["tecnicas_solo_exploradas"], "exp", raiz) + "</div>")
        c.append('<h3>Reproducibilidad (hechos que se ven en el repositorio)</h3><div class="tabla"><table class="ficha"><tbody>')
        for k, n in REPRO:
            c.append(f'<tr><th scope="row">{n}</th><td>{si_no(rep.get(k))}</td></tr>')
        c.append(f'<tr><th scope="row">Entorno declarado</th><td>{esc(valor(rep.get("entorno_declarado")))}</td></tr></tbody></table></div>')
        c.append('<h2 id="pasos">Pasos del camino de la entrega</h2><ol class="pasos">')
        porruta = {a["ruta"]: a for a in e["archivos"]}
        for p in an.get("pasos") or []:
            refs = []
            for r in p.get("referencias") or []:
                a = porruta.get(r.get("ruta"))
                if a and a in princ:
                    refs.append(f'<a href="#{a["ancla"]}-L{r["desde"]}"><code>{esc(a["ruta"].split("/")[-1])}</code> líneas {r["desde"]}–{r["hasta"]}</a>')
                elif a:
                    refs.append(f'<code>{esc(a["ruta"])}</code> líneas {r.get("desde")}–{r.get("hasta")}')
            c.append(f'<li><span class="t">{esc(p.get("titulo", ""))}.</span> {esc(p.get("descripcion", ""))}' + (f'<div class="refs">{" · ".join(refs)}</div>' if refs else "") + "</li>")
        c.append("</ol>")
    c.append('<h2 id="explicaciones">Explicaciones del alumno</h2>')
    if expl:
        c.append('<p class="meta">Textos del repositorio, tal como los escribió el autor.</p>')
        for i, a in enumerate(expl):
            carpeta = "/".join(a["ruta"].split("/")[:-1])
            cuerpo = markdown("\n".join(leer(a)), f"https://github.com/{e['repo']}/blob/{e['sha']}", f"https://raw.githubusercontent.com/{e['repo']}/{e['sha']}", carpeta)
            c.append(f'<details{" open" if i == 0 and a["lineas"] <= 700 else ""} id="{a["ancla"]}"><summary><code>{esc(a["ruta"])}</code> <span class="meta">· {a["lineas"]} líneas · <a href="{esc(a["github"])}" rel="noopener">GitHub</a> · <a href="{raiz}{quote(a["texto"])}">texto</a></span></summary>'
                     + (f'<p>{esc(a["descripcion"])}</p>' if a["descripcion"] else "") + f'<div class="explicacion">{cuerpo}</div></details>')
    else:
        c.append('<p>El repositorio no trae textos de explicación dentro de la entrega.</p>')
    if e["documentos"]:
        c.append("<p>Documentos en otros formatos (se abren en GitHub): " + ", ".join(f'<a href="https://github.com/{e["repo"]}/blob/{e["sha"]}/{quote(d["ruta"])}" rel="noopener"><code>{esc(d["ruta"])}</code></a>' for d in e["documentos"][:60]) + ("…" if len(e["documentos"]) > 60 else "") + "</p>")
    c.append('<h2 id="codigo">Código</h2>')
    if princ:
        c.append(f'<p class="meta">{len(princ)} archivo{"s" if len(princ) != 1 else ""} en el camino de la entrega · {sum(a["lineas"] for a in princ)} líneas · {n_notas} anotaciones agregadas por esta página.</p>')
        if n_notas:
            c.append('<div class="filtros"><button id="alternar-notas" type="button" aria-pressed="false">Ocultar anotaciones</button><span class="meta">Las anotaciones (fondo amarillo) no son del autor: describen cada bloque del código. Los comentarios del autor aparecen dentro del código, tal como los escribió.</span></div>')
        for a in princ:
            com = f' · <a href="{raiz}comentado/{e["slug"]}/{quote(a["ruta"])}.txt">copia comentada</a>' if a["anotaciones"] else ""
            c.append(f'<section class="archivo" id="{a["ancla"]}"><header><h4>{esc(a["ruta"])}</h4><span class="rol">principal</span><span class="meta">{esc(a["lenguaje"])} · {a["lineas"]} líneas · {round(100 * a["proporcion_comentarios"])}% de líneas con comentarios del autor · <a href="{esc(a["github"])}" rel="noopener">GitHub</a> · <a href="{raiz}{quote(a["texto"])}">texto</a>{com}</span></header>'
                     + (f'<p style="max-width:62rem">{esc(a["descripcion"])}</p>' if a["descripcion"] else "")
                     + ('<p class="meta">El archivo se muestra recortado a las primeras 5.000 líneas.</p>' if a.get("recortado") else "")
                     + f'<div class="codigo" role="region" aria-label="{esc(a["ruta"])}" tabindex="0">{html_codigo(a)}</div></section>')
    else:
        c.append("<p>La entrega no tiene archivos de código marcados como parte del camino que produce la predicción.</p>")
    c.append('<h2 id="otros">Otros archivos de la entrega</h2>')
    if otros:
        c.append('<p class="meta">Exploración, versiones anteriores, configuración y utilidades. Se cargan al abrirlos.</p>')
        for a in sorted(otros, key=lambda a: (a["rol"], a["ruta"])):
            c.append(f'<details data-src="{raiz}{quote(a["texto"])}" data-leng="{esc(a["lenguaje"])}" data-ancla="{a["ancla"]}" id="{a["ancla"]}"><summary><code>{esc(a["ruta"])}</code> <span class="rol {a["rol"]}">{ROLES[a["rol"]].lower()}</span> <span class="meta">{esc(a["lenguaje"])} · {a["lineas"]} líneas · <a href="{esc(a["github"])}" rel="noopener">GitHub</a> · <a href="{raiz}{quote(a["texto"])}">texto</a></span></summary>'
                     + (f'<p>{esc(a["descripcion"])}</p>' if a["descripcion"] else "") + '<div class="codigo"></div></details>')
    else:
        c.append("<p>No hay otros archivos de texto en la entrega.</p>")
    for cp in an.get("carpetas") or []:
        if isinstance(cp, dict) and cp.get("descripcion"):
            c.append(f'<p><code>{esc(cp.get("carpeta", ""))}</code> <span class="rol {esc(cp.get("rol", "secundario"))}">{esc(ROLES.get(cp.get("rol"), cp.get("rol", "")).lower())}</span> {esc(cp["descripcion"])}</p>')
    if ajenos:
        c.append(f'<details><summary>{len(ajenos)} archivos del repositorio que no son de esta competencia (no se publican acá)</summary><p class="meta">' + ", ".join(f'<a href="{esc(a["github"])}" rel="noopener"><code>{esc(a["ruta"])}</code></a>' for a in ajenos[:200]) + ("…" if len(ajenos) > 200 else "") + "</p></details>")
    extra = []
    if e["otros"]:
        extra.append("Archivos que no son texto ni código (datos, modelos, imágenes), por extensión: " + ", ".join(f"{esc(k)} ({v})" for k, v in sorted(e["otros"].items(), key=lambda x: -x[1])[:14]) + ".")
    if e["txt_datos"]:
        extra.append(f'{len(e["txt_datos"])} archivos .txt con datos o modelos guardados no se muestran.')
    if e["tapados"]:
        extra.append(f'Se taparon {e["tapados"]} datos personales o credenciales que aparecían en los archivos (figuran como [correo] o ***REDACTADO***).')
    for x in an.get("no_cubierto") or []:
        extra.append("No cubierto por la lectura: " + esc(str(x)))
    if extra:
        c.append('<h3>Notas</h3><ul style="max-width:62rem">' + "".join(f"<li>{x}</li>" for x in extra) + "</ul>")
    alt = (("text/markdown", f"{raiz}md/{e['slug']}.md", "Markdown"), ("application/json", f"{raiz}data/entregas/{e['slug']}.json", "JSON"))
    return pagina(e["nombre"], "\n".join(c), raiz, "entregas", f"Entrega de {e['nombre']} ({e['repo']}): resumen, ficha, pasos, explicaciones y código anotado.", alternos=alt)


def markdown_entrega(e):
    an = e["an"]
    ficha, rep = an.get("ficha") or {}, an.get("reproducibilidad") or {}
    o = [f"# {e['nombre']} — entrega de la Primera Competencia DMEyF 2026", "",
         f"- Usuario de GitHub: {e['usuario']}", f"- Repositorio: {e['url_repo']}", f"- Link posteado: {e['url_posteada']}", f"- Commit: {e['sha']}",
         f"- Estado de la lectura: {e['estado']}", f"- Página: {SITIO}entregas/{e['slug']}/", f"- Datos: {SITIO}data/entregas/{e['slug']}.json", ""]
    if an:
        o += ["## Resumen", "", an.get("resumen", ""), "", f"**Qué entrega.** {an.get('que_entrega', '')}", "", f"**Cómo se ejecuta.** {an.get('como_se_ejecuta', '')}", "", "## Ficha", ""]
        o += [f"- **{n}:** {valor(ficha.get(k))}" for k, n in CAMPOS]
        o += ["", "## Técnicas en el camino de la entrega", ""] + [f"- {ETIQUETA.get(c, c)} (`{c}`)" for c in an.get("tecnicas_en_la_entrega") or []]
        if an.get("tecnicas_solo_exploradas"):
            o += ["", "## Técnicas sólo exploradas", ""] + [f"- {ETIQUETA.get(c, c)} (`{c}`)" for c in an["tecnicas_solo_exploradas"]]
        o += ["", "## Reproducibilidad (hechos)", ""] + [f"- {n}: {'sí' if rep.get(k) is True else 'no' if rep.get(k) is False else '—'}" for k, n in REPRO] + [f"- Entorno declarado: {valor(rep.get('entorno_declarado'))}"]
        o += ["", "## Pasos del camino de la entrega", ""]
        for i, p in enumerate(an.get("pasos") or [], 1):
            refs = "; ".join(f"`{r.get('ruta')}` líneas {r.get('desde')}–{r.get('hasta')}" for r in p.get("referencias") or [])
            o.append(f"{i}. **{p.get('titulo', '')}.** {p.get('descripcion', '')}" + (f" ({refs})" if refs else ""))
    o += ["", "## Archivos", ""]
    for a in e["archivos"]:
        t = f" — [texto]({SITIO}{quote(a['texto'])})" if a["texto"] else " — no publicado en esta página"
        o.append(f"- `{a['ruta']}` · {a['rol']} · {a['lenguaje']} · {a['lineas']} líneas{t}" + (f" — {a['descripcion']}" if a["descripcion"] else ""))
    princ = [a for a in e["archivos"] if a["rol"] == "principal" and a["tipo"] != "texto"]
    if princ:
        o += ["", "## Código principal con anotaciones", "", "Las líneas que empiezan con `# [Anotación …]` no son del autor: las agrega esta página para describir cada bloque.", ""]
        total = 0
        for a in princ:
            lin = (comentado(a) if a["anotaciones"] else "\n".join(leer(a)) + "\n").split("\n")
            o.append(f"### {a['ruta']}")
            o.append("")
            if a["descripcion"]:
                o += [a["descripcion"], ""]
            if total + len(lin) > 4000:
                o += [f"El código completo está en {SITIO}{quote(a['texto'])}", ""]
                continue
            total += len(lin)
            cerca = "````" if any(l.startswith("```") for l in lin) else "```"
            o += [cerca + ("python" if "ython" in a["lenguaje"] else "r" if a["lenguaje"].startswith(("R", "Jupyter (R")) else ""), *lin[:-1], cerca, ""]
    expl = [a for a in e["archivos"] if a["publicado"] and a["rol"] == "explicacion"]
    if expl:
        o += ["", "## Explicaciones del alumno (texto original)", ""]
        for a in expl[:6]:
            lin = leer(a)
            o += [f"### {a['ruta']}", "", *(["> " + l if l.strip() else ">" for l in lin[:400]]), ""] + ([f"(sigue en {SITIO}{quote(a['texto'])})", ""] if len(lin) > 400 else [])
    return "\n".join(o) + "\n"


def json_entrega(e):
    an = e["an"]
    return {"slug": e["slug"], "usuario": e["usuario"], "nombre": e["nombre"], "repo": e["repo"], "url_repo": e["url_repo"], "url_posteada": e["url_posteada"],
            "subruta_posteada": e["subruta"], "commit": e["sha"], "estado_de_la_lectura": e["estado"], "resumen": an.get("resumen", ""), "que_entrega": an.get("que_entrega", ""),
            "como_se_ejecuta": an.get("como_se_ejecuta", ""), "ficha": an.get("ficha") or {}, "tecnicas_en_la_entrega": an.get("tecnicas_en_la_entrega") or [],
            "tecnicas_solo_exploradas": an.get("tecnicas_solo_exploradas") or [], "reproducibilidad": an.get("reproducibilidad") or {}, "pasos": an.get("pasos") or [],
            "no_cubierto": an.get("no_cubierto") or [],
            "archivos": [{"ruta": a["ruta"], "rol": a["rol"], "tipo": a["tipo"], "lenguaje": a["lenguaje"], "lineas": a["lineas"], "proporcion_comentarios": a["proporcion_comentarios"],
                          "descripcion": a["descripcion"], "anotaciones": a["anotaciones"], "ancla": a["ancla"], "texto": a["texto"], "github": a["github"],
                          "comentado": f"comentado/{e['slug']}/{a['ruta']}.txt" if a["rol"] == "principal" and a["anotaciones"] else None} for a in e["archivos"]]}


# ---------------------------------------------------------------------------------------------- páginas generales

def conteos(entregas):
    usa, exp = {}, {}
    for e in entregas:
        for c in set(e["an"].get("tecnicas_en_la_entrega") or []):
            usa.setdefault(c, []).append(e)
        for c in set(e["an"].get("tecnicas_solo_exploradas") or []):
            exp.setdefault(c, []).append(e)
    return usa, exp


def barras(pares, total, secundarios=None):
    h = ['<div class="barras">']
    for i, (n, v) in enumerate(pares):
        s = (secundarios or {}).get(n, 0)
        sec = f'<i class="sec" style="width:{100 * (v + s) / max(1, total):.1f}%"></i>' if s else ""
        h.append(f'<div>{n}</div><div class="b">{sec}<i style="width:{100 * v / max(1, total):.1f}%"></i></div><div class="v">{v}{f" +{s}" if s else ""}</div>')
    return "".join(h) + "</div>"


def sintesis_auto(entregas):
    """El resumen general en prosa. Cada número sale de las fichas: no hay texto escrito a mano con cifras."""
    con = [e for e in entregas if e["an"]]
    n = len(con)
    usa, exp = conteos(entregas)
    def t(cod, texto=None):
        k, x = len(usa.get(cod, [])), len(exp.get(cod, []))
        extra = f" (+{x})" if x else ""
        return f'<a href="tecnicas.html#{cod.replace(".", "-")}">{texto or ETIQUETA[cod].lower()}</a> en {k}{extra}'
    def k(cod):
        return len(usa.get(cod, []))
    def cuenta(campo):
        d = {}
        for e in con:
            for x in (e["an"].get("ficha") or {}).get(campo) or []:
                d[str(x)] = d.get(str(x), 0) + 1
        return d
    leng, mod = cuenta("lenguajes"), cuenta("modelos")
    sin_codigo = [e for e in con if not any(a["rol"] == "principal" and a["tipo"] == "codigo" for a in e["archivos"])]
    lineas = sum(a["lineas"] for e in con for a in e["archivos"] if a["rol"] == "principal" and a["tipo"] == "codigo")
    sem = sorted(x for x in ((e["an"].get("ficha") or {}).get("cantidad_de_semillas") for e in con) if isinstance(x, int))
    meses, val = {}, {}
    for e in con:
        f = e["an"].get("ficha") or {}
        m = tuple(f.get("meses_entrenamiento") or []); meses[m] = meses.get(m, 0) + 1
        v = tuple(f.get("meses_validacion") or []); val[v] = val.get(v, 0) + 1
    top_m = sorted(((v, m) for m, v in meses.items() if m), reverse=True)
    top_v = sorted(((v, m) for m, v in val.items() if m), reverse=True)
    rep = {key: sum(1 for e in con if (e["an"].get("reproducibilidad") or {}).get(key) is True) for key, _ in REPRO}
    def lista(m):
        return f"{m[0]} a {m[-1]}" if len(m) > 2 and all(b - a == 1 for a, b in zip(m, m[1:])) else " y ".join(map(str, m)) if len(m) <= 2 else ", ".join(map(str, m))
    otros_mod = ", ".join(f"{x} ({v})" for x, v in sorted(mod.items(), key=lambda x: -x[1]) if x != "LightGBM")
    P = []
    P.append(("El punto de partida", [
        f"Se postearon 68 entregas; 66 repositorios se pudieron descargar y {n} tienen lectura. Los caminos que producen las predicciones entregadas suman {lineas:,} líneas de código.".replace(",", ".")
        + (f" {'Una entrega no trae' if len(sin_codigo) == 1 else str(len(sin_codigo)) + ' entregas no traen'} código en el repositorio ({', '.join(esc(e['nombre']) for e in sin_codigo)})." if sin_codigo else ""),
        f"Python aparece en {leng.get('Python', 0)} entregas y R en {leng.get('R', 0)}; SQL en {leng.get('SQL', 0)}. Una misma entrega puede usar más de un lenguaje."]))
    P.append(("Modelos", [
        f"LightGBM figura como modelo en {mod.get('LightGBM', 0)} de las {n} entregas." + (f" En las fichas figuran además: {esc(otros_mod)}." if otros_mod else "")
        + f" En archivos de exploración aparecen también Random Forest ({len(exp.get('modelo.random_forest', []))}), XGBoost ({len(exp.get('modelo.xgboost', []))}), árboles de decisión ({len(exp.get('modelo.arbol_decision', []))}), regresión logística ({len(exp.get('modelo.regresion_logistica', []))}) y redes neuronales ({len(exp.get('modelo.red_neuronal', []))})."]))
    P.append(("La clase y los meses", [
        f"Para entrenar, la {t('clase.binaria_baja1_baja2', 'clase binaria que cuenta como positivos a BAJA+1 y BAJA+2')}; la {t('clase.binaria_baja2', 'binaria con sólo BAJA+2 como positivo')}; las {t('clase.multiclase', 'tres clases por separado')}. Usan {t('clase.pesos_por_clase', 'pesos distintos por clase o por fila')}.",
        "Meses de entrenamiento del modelo entregado: " + "; ".join(f"{lista(m)} en {v}" for v, m in top_m[:5]) + ". "
        + "Meses reservados para medir o elegir: " + "; ".join(f"{lista(m)} en {v}" for v, m in top_v[:4]) + f"; {val.get((), 0)} entregas no reservan meses de validación.",
        f"El {t('final.reentrena_con_todo', 'modelo final se reentrena sumando los meses de validación')}."]))
    P.append(("Tratamiento de los datos", [
        f"Las {t('datos.variables_rotas_a_na', 'variables rotas en algún mes se pasan a NA o se corrigen')}. Se {t('datos.excluye_variables', 'excluyen variables a mano')}. Hay {t('datos.submuestreo_continua', 'submuestreo de la clase CONTINUA')}.",
        f"Para el drifting: {t('drifting.rank_cero_fijo', 'rank con cero fijo')}; {t('drifting.rank_por_mes', 'rank o percentil dentro de cada mes')}; {t('drifting.deflacion', 'deflación')}; {t('drifting.estandarizacion_por_mes', 'estandarización por mes')}."]))
    P.append(("Variables", [
        f"Variables históricas: {t('variables.deltas', 'deltas')}; {t('variables.lags', 'lags')}; {t('variables.promedios_ventana', 'promedios de ventana')}; {t('variables.tendencias', 'tendencias')}; {t('variables.ratios_historia', 'cocientes contra la historia')}; {t('variables.min_max_ventana', 'mínimos y máximos de ventana')}.",
        f"Hay {t('variables.intra_mes', 'variables nuevas armadas dentro del mes')}. Para elegir variables: {t('variables.canaritos', 'canaritos')}; {t('variables.seleccion_por_importancia', 'selección por importancia')}."]))
    P.append(("Hiperparámetros y validación", [
        f"Búsqueda de hiperparámetros: {t('hiperparametros.optuna', 'Optuna')}; {t('hiperparametros.optimizacion_bayesiana', 'optimización bayesiana con otras librerías')}; {t('hiperparametros.grilla_o_azar', 'grilla o búsqueda al azar')}. Hay {t('hiperparametros.fijos', 'hiperparámetros fijos escritos en el código')}. Una entrega puede figurar en más de un grupo.",
        f"Cómo se mide: {t('validacion.mes_futuro', 'en un mes posterior al entrenamiento')}; {t('validacion.varios_meses_de_prueba', 'en más de un mes')}; {t('validacion.validacion_cruzada', 'con validación cruzada')}; {t('validacion.particion_aleatoria', 'con una partición al azar')}. Usan la {t('validacion.ganancia_como_metrica', 'ganancia de la competencia como métrica')}."]))
    if sem:
        P.append(("Semillas y ensambles", [
            f"El {t('ensamble.semillerio', 'promedio de varias semillas del mismo modelo')}. La cantidad de semillas del modelo entregado va de {sem[0]} a {sem[-1]}, con mediana {sem[len(sem) // 2]}: "
            f"{sum(1 for x in sem if x <= 1)} entregas con una sola, {sum(1 for x in sem if 2 <= x <= 10)} con 2 a 10, {sum(1 for x in sem if 11 <= x <= 50)} con 11 a 50 y {sum(1 for x in sem if x > 50)} con más de 50.",
            f"Se {t('ensamble.modelos_distintos', 'combinan modelos o configuraciones distintas')}; {t('ensamble.stacking', 'stacking')}."]))
    P.append(("El corte", [
        f"La lista se arma con una {t('corte.cantidad_fija', 'cantidad fija de clientes')}; por {t('corte.umbral_probabilidad', 'umbral de probabilidad')}. El {t('corte.elegido_en_validacion', 'corte sale de una curva de ganancia en meses con clase')}. Se {t('corte.varios_cortes', 'generan archivos con varios cortes')}."]))
    P.append(("Lo que acompaña al código", [
        f"De las {n} entregas, {rep['tiene_readme']} traen README u otro texto de presentación y {rep['explica_como_ejecutar']} explican cómo ejecutar; {rep['declara_versiones_o_dependencias']} declaran versiones o dependencias; {rep['es_un_solo_comando']} salen de un solo script o notebook; "
        f"{rep['usa_rutas_absolutas_o_de_una_maquina']} tienen rutas absolutas o de una máquina en el código principal; {rep['incluye_datos_o_predicciones']} incluyen datos, predicciones o modelos guardados. El detalle está en <a href=\"reproducibilidad.html\">Reproducibilidad</a>.",
        f"Incluyen {t('proceso.bitacora', 'bitácora o registro de experimentos')}. El {t('proceso.uso_de_ia_declarado', 'uso de asistentes de IA está declarado en el repositorio')}."]))
    h = ['<p class="meta" style="max-width:62rem">Cada número de esta sección sale de las fichas y lleva a la lista de entregas correspondiente. «En N (+K)» quiere decir: en N de las ' + str(n) + ' entregas leídas, dentro del camino que produce la predicción entregada, y en K más sólo en archivos de exploración.</p>']
    for titulo, parrafos in P:
        h.append(f"<h3>{titulo}</h3>")
        h += [f'<p style="max-width:62rem">{p}</p>' for p in parrafos]
    return "\n".join(h)


def pagina_inicio(entregas, sintesis):
    con = [e for e in entregas if e["an"]]
    usa, exp = conteos(entregas)
    n = len(entregas)
    def cuenta(campo):
        d = {}
        for e in con:
            for x in (e["an"].get("ficha") or {}).get(campo) or []:
                d[str(x)] = d.get(str(x), 0) + 1
        return sorted(d.items(), key=lambda x: -x[1])
    lineas_princ = sum(a["lineas"] for e in entregas for a in e["archivos"] if a["rol"] == "principal" and a["tipo"] == "codigo")
    notas = sum(len(a["anotaciones"]) for e in entregas for a in e["archivos"])
    con_expl = sum(1 for e in entregas if any(a["rol"] == "explicacion" and a["publicado"] for a in e["archivos"]))
    c = ['<h1>Postmortem de la Primera Competencia</h1>',
         '<p class="bajada">Una lectura descriptiva de las entregas de DMEyF 2026 (UBA): qué hizo cada alumno para predecir las bajas de 202108, con su código, sus explicaciones y una descripción objetiva de cada paso. No hay puntajes ni valoraciones: la idea es poder mirar cómo lo resolvió cada uno y comparar.</p>',
         f'<div class="grilla"><div class="tarjeta"><div class="num">{n}</div><div class="rot">entregas con repositorio accesible</div></div>'
         f'<div class="tarjeta"><div class="num">{len(con)}</div><div class="rot">entregas leídas y descriptas</div></div>'
         f'<div class="tarjeta"><div class="num">{lineas_princ:,}</div><div class="rot">líneas de código en los caminos de entrega</div></div>'.replace(",", ".") +
         f'<div class="tarjeta"><div class="num">{notas:,}</div><div class="rot">anotaciones agregadas al código</div></div>'.replace(",", ".") +
         f'<div class="tarjeta"><div class="num">{con_expl}</div><div class="rot">entregas con textos de explicación</div></div></div>',
         '<div class="grilla">'
         '<a class="tarjeta" href="#entregas"><h3>Entregas</h3><p>La página de cada alumno: resumen, ficha, pasos, explicaciones y código anotado.</p></a>'
         '<a class="tarjeta" href="comparar.html"><h3>Comparar dos entregas</h3><p>Elegir dos alumnos y ver sus fichas y sus códigos en paralelo.</p></a>'
         '<a class="tarjeta" href="fichas.html"><h3>Fichas</h3><p>Todas las fichas en una tabla, para seguir una misma decisión entre entregas.</p></a>'
         '<a class="tarjeta" href="tecnicas.html"><h3>Técnicas</h3><p>Quién usó cada técnica y en qué línea de su código se puede ver.</p></a>'
         '<a class="tarjeta" href="reproducibilidad.html"><h3>Reproducibilidad</h3><p>Qué trae cada repositorio para poder volver a correrlo.</p></a>'
         '<a class="tarjeta" href="buscar.html"><h3>Buscar en el código</h3><p>Buscar una función, una variable o un parámetro en todas las entregas.</p></a>'
         '<a class="tarjeta" href="glosario.html"><h3>Glosario</h3><p>Los términos de la materia, con enlaces a ejemplos en el código.</p></a></div>',
         '<h2 id="resumen">Qué se hizo en general</h2>']
    c.append(sintesis_auto(entregas))
    c.append(f'<h3>En números</h3><p class="meta">Sobre las {len(con)} entregas leídas. La barra llena cuenta las entregas que usan la técnica en el camino que produce la predicción; el tramo claro y el «+», las que sólo la tienen en archivos de exploración.</p>')
    c.append("<h4>Lenguajes</h4>" + barras(cuenta("lenguajes")[:8], len(con)))
    c.append("<h4>Modelos</h4>" + barras(cuenta("modelos")[:10], len(con)))
    for g, nombre in GRUPOS.items():
        pares = sorted(((ETIQUETA[f"{g}.{k}"], len(usa.get(f"{g}.{k}", []))) for k in VOC[g]), key=lambda x: -x[1])
        sec = {ETIQUETA[f"{g}.{k}"]: len(exp.get(f"{g}.{k}", [])) for k in VOC[g]}
        pares = [p for p in pares if p[1] or sec.get(p[0])]
        if pares:
            c.append(f"<h4>{nombre}</h4>" + barras(pares, len(con), sec))
    sem = {}
    for e in con:
        k = (e["an"].get("ficha") or {}).get("cantidad_de_semillas")
        clave = "No se observa" if not isinstance(k, int) else "1" if k <= 1 else "2 a 5" if k <= 5 else "6 a 10" if k <= 10 else "11 a 20" if k <= 20 else "21 a 50" if k <= 50 else "más de 50"
        sem[clave] = sem.get(clave, 0) + 1
    orden = ["1", "2 a 5", "6 a 10", "11 a 20", "21 a 50", "más de 50", "No se observa"]
    c.append("<h4>Cantidad de semillas del modelo entregado</h4>" + barras([(k, sem[k]) for k in orden if k in sem], len(con)))
    mes = {}
    for e in con:
        k = tuple((e["an"].get("ficha") or {}).get("meses_entrenamiento") or [])
        mes[k] = mes.get(k, 0) + 1
    c.append("<h4>Meses de entrenamiento del modelo entregado</h4>" + barras([(", ".join(map(str, k)) if k else "No se observa", v) for k, v in sorted(mes.items(), key=lambda x: -x[1])[:10]], len(con)))
    c.append('<h2 id="entregas">Entregas</h2>')
    opciones = "".join(f'<optgroup label="{GRUPOS[g]}">' + "".join(f'<option value="{g}.{k}">{esc(v)}</option>' for k, v in VOC[g].items()) + "</optgroup>" for g in VOC)
    c.append(f'<div class="filtros"><label for="filtro" class="meta">Filtrar</label><input id="filtro" type="search" placeholder="nombre, usuario, lenguaje, modelo…" aria-label="Filtrar entregas"><select id="filtro-tecnica" aria-label="Filtrar por técnica"><option value="">Cualquier técnica</option>{opciones}</select><span id="cuenta" class="meta" aria-live="polite"></span></div>')
    c.append('<div class="tabla"><table><thead><tr><th>Entrega</th><th>Lenguajes</th><th>Modelos</th><th>Meses de entrenamiento</th><th>Semillas</th><th class="c">Código principal</th><th class="c">Anotaciones</th><th class="c">Explicaciones</th></tr></thead><tbody>')
    for e in entregas:
        f = e["an"].get("ficha") or {}
        lp = sum(a["lineas"] for a in e["archivos"] if a["rol"] == "principal" and a["tipo"] == "codigo")
        nn = sum(len(a["anotaciones"]) for a in e["archivos"])
        ne = sum(1 for a in e["archivos"] if a["rol"] == "explicacion" and a["publicado"])
        tec = " ".join(e["an"].get("tecnicas_en_la_entrega") or [])
        buscar = " ".join([e["nombre"], e["usuario"], e["repo"], valor(f.get("lenguajes")), valor(f.get("modelos"))]).lower()
        usuario = f'<br><span class="meta">{esc(e["usuario"])}</span>' if e["usuario"].lower() != e["nombre"].lower() else ""
        c.append(f'<tr data-buscar="{esc(buscar)}" data-tecnicas="{esc(tec)}"><th scope="row"><a href="entregas/{e["slug"]}/">{esc(e["nombre"])}</a>{usuario}</th><td>{esc(valor(f.get("lenguajes")))}</td><td>{esc(valor(f.get("modelos")))}</td>'
                 f'<td>{esc(valor(f.get("meses_entrenamiento")))}</td><td>{esc(valor(f.get("cantidad_de_semillas")))}</td><td class="c">{lp or "—"}</td><td class="c">{nn or "—"}</td><td class="c">{ne or "—"}</td></tr>')
    c.append("</tbody></table></div>")
    c.append('<h2 id="metodo">Cómo se hizo esta página</h2><div style="max-width:62rem">'
             '<p>Se partió de los links a GitHub que cada alumno posteó en el canal de entrega. De cada repositorio se tomó el commit vigente al momento de la descarga y, dentro de él, la carpeta o el archivo que el alumno señaló. Los notebooks se pasaron a texto, celda por celda.</p>'
             '<p>Cada entrega la leyó un lector automático que escribió el resumen, la ficha, los pasos y las anotaciones, con una regla: describir lo que el código hace, sin opinar. Una segunda pasada automática contrastó contra el código los datos principales de cada ficha (lenguajes, modelo, clase, meses, semillas, corte y técnicas) y una muestra de las anotaciones; lo que no pudo respaldar con una línea se revisó y se corrigió. Las anotaciones se agregaron en los archivos del camino de la entrega que casi no tenían comentarios; los comentarios del autor quedaron como estaban.</p>'
             '<p>Lo que no hay: puntajes, posiciones ni juicios sobre qué enfoque conviene. Dos entregas posteadas no se pudieron descargar porque sus repositorios ya no eran accesibles. Los correos y credenciales que aparecían en algunos archivos se taparon.</p></div>')
    return pagina("Resumen", "\n".join(c), "", "inicio", "Postmortem de la Primera Competencia de DMEyF 2026: resumen general, código anotado de cada entrega, comparador y matriz de técnicas.",
                  alternos=(("application/json", "data/index.json", "Índice en JSON"), ("text/plain", "llms.txt", "Guía para agentes")))


def pagina_tecnicas(entregas):
    usa, exp = conteos(entregas)
    con = [e for e in entregas if e["an"]]
    c = ['<h1>Técnicas</h1>', '<p class="bajada">Qué técnicas aparecen en cada entrega. Primero la matriz completa; debajo, para cada técnica, quiénes la usan y un enlace a una línea de su código donde se puede ver.</p>',
         '<p class="meta">● la usa el camino que produce la predicción entregada · ○ sólo aparece en archivos de exploración. El enlace «ver en el código» lleva a la primera línea del código principal que coincide con la técnica: es una ayuda para ubicarse, no una cita exacta.</p>']
    cols = [(g, k) for g in VOC for k in VOC[g] if usa.get(f"{g}.{k}") or exp.get(f"{g}.{k}")]
    cab1, cab2, prev = "", "", None
    for g in VOC:
        k = sum(1 for x in cols if x[0] == g)
        if k:
            cab1 += f'<th class="g" colspan="{k}">{GRUPOS[g]}</th>'
    for g, k in cols:
        cab2 += f'<th class="v{" sep" if g != prev else ""}"><a href="#{g}-{k}">{esc(ETIQUETA[f"{g}.{k}"])}</a></th>'; prev = g
    c.append(f'<div class="tabla" style="max-height:80vh"><table class="matriz"><thead><tr><th rowspan="2">Entrega</th>{cab1}</tr><tr>{cab2}</tr></thead><tbody>')
    for e in con:
        en, ex = set(e["an"].get("tecnicas_en_la_entrega") or []), set(e["an"].get("tecnicas_solo_exploradas") or [])
        fila, prev = "", None
        for g, k in cols:
            cod = f"{g}.{k}"
            fila += f'<td class="p{" sep" if g != prev else ""}{" e" if cod in ex and cod not in en else ""}">{"●" if cod in en else "○" if cod in ex else ""}</td>'; prev = g
        c.append(f'<tr><th scope="row"><a href="entregas/{e["slug"]}/">{esc(e["nombre"])}</a></th>{fila}</tr>')
    c.append("</tbody></table></div>")
    c.append('<p><a href="data/matriz.csv">Descargar la matriz en CSV</a></p>')
    for g in VOC:
        c.append(f'<h2 id="g-{g}">{GRUPOS[g]}</h2>')
        for k, nombre in VOC[g].items():
            cod = f"{g}.{k}"
            u, x = usa.get(cod, []), exp.get(cod, [])
            c.append(f'<h3 id="{g}-{k}">{esc(nombre)} <span class="meta">· {len(u)} en la entrega{f", {len(x)} sólo exploradas" if x else ""}</span></h3>')
            if not u and not x:
                c.append('<p class="meta">Ninguna entrega.</p>'); continue
            items = []
            for e in u:
                ev = evidencia(e, cod)
                items.append(f'<a class="chip si" href="entregas/{e["slug"]}/{"#" + ev if ev else ""}">{esc(e["nombre"])}{" · ver en el código" if ev else ""}</a>')
            for e in x:
                items.append(f'<a class="chip exp" href="entregas/{e["slug"]}/">{esc(e["nombre"])} (explorada)</a>')
            c.append('<div class="chips">' + "".join(items) + "</div>")
    return pagina("Técnicas", "\n".join(c), "", "tecnicas", "Matriz de técnicas por entrega y enlaces a ejemplos en el código.", ancho=True, alternos=(("application/json", "data/tecnicas.json", "Técnicas en JSON"), ("text/csv", "data/matriz.csv", "Matriz en CSV")))


def pagina_repro(entregas):
    con = [e for e in entregas if e["an"]]
    c = ['<h1>Reproducibilidad</h1>', '<p class="bajada">Qué trae cada repositorio para que otra persona pueda volver a correr la entrega. Son hechos que se ven en los archivos, no una evaluación: nadie corrió los códigos para armar esta tabla.</p>']
    tot = {k: sum(1 for e in con if (e["an"].get("reproducibilidad") or {}).get(k) is True) for k, _ in REPRO}
    c.append(barras([(n, tot[k]) for k, n in REPRO], len(con)))
    c.append('<div class="tabla"><table><thead><tr><th>Entrega</th>' + "".join(f'<th class="c">{n}</th>' for _, n in REPRO) + "<th>Entorno declarado</th></tr></thead><tbody>")
    for e in con:
        r = e["an"].get("reproducibilidad") or {}
        c.append(f'<tr><th scope="row"><a href="entregas/{e["slug"]}/">{esc(e["nombre"])}</a></th>' + "".join(f'<td class="c">{si_no(r.get(k))}</td>' for k, _ in REPRO) + f'<td>{esc(valor(r.get("entorno_declarado")))}</td></tr>')
    c.append("</tbody></table></div>")
    return pagina("Reproducibilidad", "\n".join(c), "", "repro", "Qué trae cada repositorio para volver a correr la entrega.", ancho=True)


def pagina_fichas(entregas):
    con = [e for e in entregas if e["an"]]
    c = ['<h1>Fichas</h1>', '<p class="bajada">Todas las fichas en una sola tabla, para recorrer una misma decisión (la clase, los meses, el submuestreo, las semillas, el corte) a lo largo de las entregas.</p>',
         '<div class="filtros"><label for="filtro" class="meta">Filtrar</label><input id="filtro" type="search" placeholder="texto en cualquier columna" aria-label="Filtrar fichas"><span id="cuenta" class="meta" aria-live="polite"></span><a href="data/fichas.csv">Descargar en CSV</a></div>',
         '<div class="tabla" style="max-height:82vh"><table><thead><tr><th>Entrega</th>' + "".join(f"<th>{n}</th>" for _, n in CAMPOS) + "</tr></thead><tbody>"]
    for e in con:
        f = e["an"].get("ficha") or {}
        celdas = [valor(f.get(k)) for k, _ in CAMPOS]
        c.append(f'<tr data-buscar="{esc(" ".join([e["nombre"], e["usuario"]] + celdas).lower())}" data-tecnicas=""><th scope="row" style="white-space:nowrap"><a href="entregas/{e["slug"]}/">{esc(e["nombre"])}</a></th>'
                 + "".join(f'<td style="min-width:{"7rem" if len(x) < 30 else "16rem"}">{esc(x)}</td>' for x in celdas) + "</tr>")
    c.append("</tbody></table></div>")
    return pagina("Fichas", "\n".join(c), "", "fichas", "Las fichas de todas las entregas en una tabla.", ancho=True, alternos=(("text/csv", "data/fichas.csv", "Fichas en CSV"),))


def pagina_comparar():
    c = ['<h1>Comparar dos entregas</h1>', '<p class="bajada">Elegí dos alumnos para ver sus fichas lado a lado y sus códigos en paralelo. Los pasos de cada uno llevan a la parte del código donde ocurren.</p>',
         '<div class="filtros"><select id="sel-a" aria-label="Entrega A"></select><button id="invertir" type="button" aria-label="Intercambiar A y B">⇄</button><select id="sel-b" aria-label="Entrega B"></select></div>',
         '<p id="aviso-carga" class="aviso oculto">No se pudieron cargar los datos. Esta página necesita abrirse desde un servidor web (por ejemplo GitHub Pages, o <code>python3 -m http.server</code> en la carpeta del repositorio), no como archivo suelto.</p>',
         '<noscript><p class="aviso">El comparador necesita JavaScript. Sin él, se pueden abrir las páginas de dos entregas en dos pestañas, o leer sus versiones en Markdown desde <a href="agentes.html">la guía para agentes</a>.</p></noscript>',
         '<div id="comparacion" class="oculto">',
         '<h2>Resumen</h2><div class="dos"><p id="res-a"></p><p id="res-b"></p></div>',
         '<h2>Ficha</h2><p class="meta">Las celdas resaltadas son las que difieren entre las dos entregas.</p><div class="tabla"><table class="ficha dif" id="tabla-ficha"></table></div>',
         '<h2>Técnicas</h2><div class="tabla"><table><thead><tr><th id="tec-na">Sólo A</th><th>Las dos</th><th id="tec-nb">Sólo B</th></tr></thead><tbody><tr><td><div class="chips" id="tec-a"></div></td><td><div class="chips" id="tec-ab"></div></td><td><div class="chips" id="tec-b"></div></td></tr></tbody></table></div>',
         '<h2>Reproducibilidad</h2><div class="tabla"><table class="ficha" id="tabla-repro"></table></div>',
         '<h2>Código en paralelo</h2><div class="dos"><section class="panel" id="panel-a" aria-label="Entrega A"></section><section class="panel" id="panel-b" aria-label="Entrega B"></section></div>',
         '</div>']
    return pagina("Comparar", "\n".join(c), "", "comparar", "Comparador de dos entregas: fichas y códigos en paralelo.", ancho=True)


def pagina_buscar():
    c = ['<h1>Buscar en el código</h1>', '<p class="bajada">Busca en el código principal de todas las entregas (el camino que produce la predicción). Sirve para ver cómo usó cada uno una función, una variable o un parámetro.</p>',
         '<div class="filtros"><input id="consulta" type="search" placeholder="por ejemplo: feature_fraction, ccajas_depositos, frank(" aria-label="Texto a buscar" style="flex:1 1 22rem"><label><input type="checkbox" id="exp-regular"> expresión regular</label><label><input type="checkbox" id="mayusculas"> distinguir mayúsculas</label></div>',
         '<p id="aviso-carga" class="aviso oculto">No se pudo cargar el índice. Esta página necesita abrirse desde un servidor web.</p>',
         '<noscript><p class="aviso">El buscador necesita JavaScript. El índice completo está en <a href="data/busqueda.json">data/busqueda.json</a>.</p></noscript>',
         '<p id="estado-busqueda" class="meta" aria-live="polite">Escribí al menos dos caracteres.</p><div id="resultados"></div>']
    return pagina("Buscar en el código", "\n".join(c), "", "buscar", "Buscador en el código principal de todas las entregas.")


GLOSARIO = [
    ("La competencia", [
        ("BAJA+2, BAJA+1, CONTINUA", "La clase de cada cliente en cada mes. BAJA+2: el cliente deja de aparecer dos meses después. BAJA+1: deja de aparecer el mes siguiente. CONTINUA: sigue. Lo que se premia es identificar los BAJA+2 del mes a predecir.", ["clase.binaria_baja2", "clase.binaria_baja1_baja2", "clase.multiclase"]),
        ("Ganancia", "La métrica de la competencia: cada cliente BAJA+2 incluido en la lista suma un monto fijo y cada cliente incluido que no lo es resta un costo fijo.", ["validacion.ganancia_como_metrica"]),
        ("Corte o envíos", "Cuántos clientes se incluyen en la lista que se entrega. Se puede fijar como cantidad, como umbral de probabilidad, o elegir mirando una curva de ganancia en meses con clase.", ["corte.cantidad_fija", "corte.umbral_probabilidad", "corte.elegido_en_validacion", "corte.varios_cortes"]),
    ]),
    ("Datos", [
        ("Variables rotas", "Variables que en algún mes vienen con valores que no corresponden (por ejemplo, todo en cero). Un tratamiento habitual es pasarlas a NA en ese mes.", ["datos.variables_rotas_a_na"]),
        ("Submuestreo", "Entrenar con sólo una parte de los clientes CONTINUA (la clase mayoritaria) y todos los que se van.", ["datos.submuestreo_continua"]),
        ("Drifting", "Cambio en la distribución de una variable de un mes a otro. Entre los tratamientos que aparecen: reemplazar el valor por su posición (rank) dentro del mes, dejar el cero fijo y ordenar positivos y negativos por separado, o deflactar los montos.", ["drifting.rank_por_mes", "drifting.rank_cero_fijo", "drifting.deflacion", "drifting.estandarizacion_por_mes"]),
    ]),
    ("Variables", [
        ("Lag y delta", "Lag: el valor de una variable en un mes anterior del mismo cliente. Delta: la diferencia entre el valor actual y ese valor anterior.", ["variables.lags", "variables.deltas"]),
        ("Tendencia y ventana", "Resúmenes de los últimos meses de un cliente: pendiente de la recta que ajusta los valores (tendencia), promedio, mínimo y máximo de la ventana, y cocientes contra esos valores.", ["variables.tendencias", "variables.promedios_ventana", "variables.min_max_ventana", "variables.ratios_historia"]),
        ("Variables dentro del mes", "Variables nuevas armadas con datos del mismo mes: sumas, cocientes y combinaciones de las originales.", ["variables.intra_mes"]),
        ("Canaritos", "Variables de números al azar que se agregan al dataset. Si el modelo las usa tanto como a una variable real, esa variable real no aporta más que ruido; sirven para decidir cuáles quedarse.", ["variables.canaritos", "variables.seleccion_por_importancia"]),
    ]),
    ("Modelo", [
        ("Hiperparámetros y su búsqueda", "Los valores que definen cómo aprende el modelo (cantidad de árboles, hojas, tasa de aprendizaje). Se pueden dejar fijos o buscar con optimización bayesiana, Optuna, grillas o al azar.", ["hiperparametros.optimizacion_bayesiana", "hiperparametros.optuna", "hiperparametros.grilla_o_azar", "hiperparametros.fijos"]),
        ("Validación", "Cómo se mide un modelo antes de entregar: en un mes posterior al de entrenamiento, con una partición al azar, con validación cruzada, o en varios meses.", ["validacion.mes_futuro", "validacion.particion_aleatoria", "validacion.validacion_cruzada", "validacion.varios_meses_de_prueba"]),
        ("Semillerío", "Entrenar el mismo modelo varias veces cambiando sólo la semilla y promediar las probabilidades.", ["ensamble.semillerio"]),
        ("Ensamble", "Combinar las predicciones de modelos o configuraciones distintas, por promedio o entrenando otro modelo sobre sus salidas (stacking).", ["ensamble.modelos_distintos", "ensamble.stacking"]),
        ("Reentrenar con todo", "Después de elegir hiperparámetros y corte, volver a entrenar sumando los meses que se habían reservado para validar.", ["final.reentrena_con_todo"]),
    ]),
]


def pagina_glosario(entregas):
    usa, _ = conteos(entregas)
    c = ['<h1>Glosario</h1>', '<p class="bajada">Los términos que aparecen en las entregas, definidos en una o dos frases, con enlaces a las entregas donde se puede ver cada cosa en el código.</p>']
    for titulo, items in GLOSARIO:
        c.append(f"<h2>{titulo}</h2>")
        for termino, definicion, codigos in items:
            c.append(f'<h3>{esc(termino)}</h3><p style="max-width:62rem">{esc(definicion)}</p>')
            links = [f'<a class="chip si" href="tecnicas.html#{cod.replace(".", "-")}">{esc(ETIQUETA[cod])} · {len(usa.get(cod, []))} entregas</a>' for cod in codigos]
            c.append('<div class="chips">' + "".join(links) + "</div>")
    return pagina("Glosario", "\n".join(c), "", "glosario", "Glosario de la competencia con enlaces a ejemplos en el código.")


def pagina_agentes(entregas):
    c = ['<h1>Para agentes</h1>', '<p class="bajada">Todo el contenido de esta página existe también en formatos pensados para leerse sin navegador: texto plano, Markdown, JSON y CSV. Nada depende de ejecutar JavaScript, salvo el comparador y el buscador, que se pueden reemplazar leyendo los archivos de abajo.</p>',
         '<h2>Por dónde empezar</h2><ul style="max-width:62rem">'
         '<li><a href="llms.txt"><code>llms.txt</code></a>: índice en texto plano con todos los enlaces de esta lista.</li>'
         '<li><a href="data/index.json"><code>data/index.json</code></a>: las entregas con su ficha, técnicas, reproducibilidad y enlaces.</li>'
         '<li><a href="data/tecnicas.json"><code>data/tecnicas.json</code></a>: el vocabulario de técnicas y qué entregas usan cada una. <a href="data/matriz.csv"><code>data/matriz.csv</code></a>: lo mismo como tabla. <a href="data/fichas.csv"><code>data/fichas.csv</code></a>: todas las fichas.</li>'
         '<li><code>data/entregas/&lt;slug&gt;.json</code>: una entrega completa (resumen, ficha, pasos, archivos y anotaciones con sus rangos de líneas).</li>'
         '<li><code>md/&lt;slug&gt;.md</code>: una entrega en Markdown, con el código principal y las anotaciones intercaladas como comentarios.</li>'
         '<li><code>fuentes/&lt;slug&gt;/&lt;ruta&gt;.txt</code>: cada archivo de la entrega en texto plano (los notebooks, celda por celda).</li>'
         '<li><code>comentado/&lt;slug&gt;/&lt;ruta&gt;.txt</code>: los archivos principales con las anotaciones agregadas como comentarios.</li>'
         '<li><a href="data/busqueda.json"><code>data/busqueda.json</code></a>: todas las líneas del código principal, para buscar.</li></ul>',
         '<h2>Cómo comparar dos entregas sin el comparador</h2><p style="max-width:62rem">Leer <code>data/entregas/A.json</code> y <code>data/entregas/B.json</code>: el campo <code>ficha</code> tiene las mismas claves en las dos, <code>tecnicas_en_la_entrega</code> usa los códigos de <code>data/tecnicas.json</code>, y <code>pasos</code> apunta a archivo y líneas. El código está en el <code>texto</code> de cada archivo.</p>',
         '<h2>Convenciones</h2><ul style="max-width:62rem"><li>Los números de línea se refieren siempre a los archivos de <code>fuentes/</code>.</li><li>Los meses van como AAAAMM. Las claves están en español, sin tildes.</li><li>Las descripciones y anotaciones son lecturas automáticas: describen el código, no lo valoran, y pueden tener errores. El campo <code>estado_de_la_lectura</code> dice si pasó la segunda revisión.</li><li>Los textos de cada alumno están en los archivos con rol <code>explicacion</code>.</li></ul>',
         '<h2>Entregas</h2><div class="tabla"><table><thead><tr><th>Entrega</th><th>slug</th><th>Markdown</th><th>JSON</th><th>Página</th></tr></thead><tbody>']
    for e in entregas:
        c.append(f'<tr><th scope="row">{esc(e["nombre"])}</th><td><code>{e["slug"]}</code></td><td><a href="md/{e["slug"]}.md">md</a></td><td><a href="data/entregas/{e["slug"]}.json">json</a></td><td><a href="entregas/{e["slug"]}/">html</a></td></tr>')
    c.append("</tbody></table></div>")
    return pagina("Para agentes", "\n".join(c), "", "agentes", "Guía de los formatos legibles por máquina de esta página.", alternos=(("text/plain", "llms.txt", "llms.txt"), ("application/json", "data/index.json", "Índice")))


def llms(entregas):
    o = ["# Postmortem de la Primera Competencia — DMEyF 2026 (UBA)", "",
         "> Lectura descriptiva de las entregas de una competencia universitaria de predicción de bajas de clientes bancarios (clase BAJA+2 en 202108). Para cada entrega: resumen, ficha, pasos, explicaciones del alumno y código con anotaciones objetivas. Sin puntajes ni valoraciones.", "",
         "Las descripciones y anotaciones son lecturas automáticas con una segunda revisión automática; pueden contener errores. Los números de línea se refieren a los archivos de fuentes/. Idioma: español.", "",
         "## Datos", "",
         f"- [Índice de entregas]({SITIO}data/index.json): ficha, técnicas, reproducibilidad y enlaces de cada entrega (JSON)",
         f"- [Técnicas]({SITIO}data/tecnicas.json): vocabulario y entregas que usan cada técnica (JSON)",
         f"- [Matriz de técnicas]({SITIO}data/matriz.csv): una fila por entrega, una columna por técnica (CSV)",
         f"- [Fichas]({SITIO}data/fichas.csv): una fila por entrega, una columna por campo de la ficha (CSV)",
         f"- [Líneas del código principal]({SITIO}data/busqueda.json): para buscar texto en todas las entregas (JSON)", "",
         "## Páginas", "",
         f"- [Resumen general]({SITIO}index.html)", f"- [Técnicas]({SITIO}tecnicas.html)", f"- [Reproducibilidad]({SITIO}reproducibilidad.html)", f"- [Glosario]({SITIO}glosario.html)",
         f"- [Guía para agentes]({SITIO}agentes.html)", "", "## Entregas", ""]
    for e in entregas:
        r = (e["an"].get("resumen") or "").split(". ")[0][:220]
        o.append(f"- [{e['nombre']}]({SITIO}md/{e['slug']}.md): {r}".rstrip(": ") + f" · [JSON]({SITIO}data/entregas/{e['slug']}.json)")
    o += ["", "## Opcional", "", f"- [Repositorio de esta página]({REPO_SITIO}): incluye las herramientas con que se generó (tools/)"]
    return "\n".join(o) + "\n"


# ---------------------------------------------------------------------------------------------- principal

def escribir(ruta, texto):
    p = RAIZ / ruta
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(texto)


def main():
    entregas = cargar()
    for d in ("entregas", "data", "md", "fuentes", "comentado"):
        shutil.rmtree(RAIZ / d, ignore_errors=True)
    sintesis = json.load(open(TRABAJO / "sintesis.json")) if (TRABAJO / "sintesis.json").exists() else None
    usa, exp = conteos(entregas)
    busqueda = []
    for e in entregas:
        for a in e["archivos"]:
            if a["publicado"]:
                escribir(a["texto"], "\n".join(leer(a)) + "\n")
            if a["rol"] == "principal" and a["anotaciones"] and a["tipo"] != "texto":
                escribir(f"comentado/{e['slug']}/{a['ruta']}.txt", comentado(a))
        escribir(f"entregas/{e['slug']}/index.html", pagina_entrega(e, entregas))
        escribir(f"md/{e['slug']}.md", markdown_entrega(e))
        escribir(f"data/entregas/{e['slug']}.json", json.dumps(json_entrega(e), ensure_ascii=False))
        arch = [{"ruta": a["ruta"], "ancla": a["ancla"], "lineas": leer(a)} for a in e["archivos"] if a["rol"] == "principal" and a["tipo"] == "codigo"]
        if arch:
            busqueda.append({"slug": e["slug"], "nombre": e["nombre"], "archivos": arch})
    indice = {"titulo": "Postmortem de la Primera Competencia — DMEyF 2026", "generado": HOY, "sitio": SITIO, "entregas": [
        {"slug": e["slug"], "usuario": e["usuario"], "nombre": e["nombre"], "repo": e["repo"], "url_repo": e["url_repo"], "url_posteada": e["url_posteada"], "commit": e["sha"],
         "estado_de_la_lectura": e["estado"], "resumen": e["an"].get("resumen", ""), "ficha": e["an"].get("ficha") or {}, "tecnicas_en_la_entrega": e["an"].get("tecnicas_en_la_entrega") or [],
         "tecnicas_solo_exploradas": e["an"].get("tecnicas_solo_exploradas") or [], "reproducibilidad": e["an"].get("reproducibilidad") or {},
         "pagina": f"entregas/{e['slug']}/", "markdown": f"md/{e['slug']}.md", "json": f"data/entregas/{e['slug']}.json"} for e in entregas]}
    escribir("data/index.json", json.dumps(indice, ensure_ascii=False))
    escribir("data/tecnicas.json", json.dumps({"grupos": [{"grupo": g, "nombre": GRUPOS[g], "tecnicas": [
        {"codigo": f"{g}.{k}", "nombre": n, "en_la_entrega": [e["slug"] for e in usa.get(f"{g}.{k}", [])], "solo_exploradas": [e["slug"] for e in exp.get(f"{g}.{k}", [])]} for k, n in VOC[g].items()]} for g in VOC]}, ensure_ascii=False))
    escribir("data/busqueda.json", json.dumps({"entregas": busqueda}, ensure_ascii=False))
    with open(RAIZ / "data" / "matriz.csv", "w", newline="") as f:
        w = csv.writer(f)
        cods = [f"{g}.{k}" for g in VOC for k in VOC[g]]
        w.writerow(["slug", "usuario", "nombre", "repo"] + cods)
        for e in entregas:
            en, ex = set(e["an"].get("tecnicas_en_la_entrega") or []), set(e["an"].get("tecnicas_solo_exploradas") or [])
            w.writerow([e["slug"], e["usuario"], e["nombre"], e["repo"]] + ["entrega" if c in en else "explorada" if c in ex else "" for c in cods])
    with open(RAIZ / "data" / "fichas.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["slug", "usuario", "nombre", "repo"] + [k for k, _ in CAMPOS])
        for e in entregas:
            fi = e["an"].get("ficha") or {}
            w.writerow([e["slug"], e["usuario"], e["nombre"], e["repo"]] + [valor(fi.get(k)) for k, _ in CAMPOS])
    escribir("fichas.html", pagina_fichas(entregas))
    escribir("index.html", pagina_inicio(entregas, sintesis))
    escribir("tecnicas.html", pagina_tecnicas(entregas))
    escribir("reproducibilidad.html", pagina_repro(entregas))
    escribir("comparar.html", pagina_comparar())
    escribir("buscar.html", pagina_buscar())
    escribir("glosario.html", pagina_glosario(entregas))
    escribir("agentes.html", pagina_agentes(entregas))
    escribir("llms.txt", llms(entregas))
    escribir(".nojekyll", "")
    est = {}
    for e in entregas:
        est[e["estado"]] = est.get(e["estado"], 0) + 1
    print(f"{len(entregas)} entregas {est} | {sum(len(b['archivos']) for b in busqueda)} archivos principales en el buscador")


if __name__ == "__main__":
    main()
