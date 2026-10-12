"""Markdown a HTML (subconjunto, sin dependencias, con el HTML crudo escapado) y resaltado de código por línea."""
import html, re

def esc(s):
    return html.escape(s, quote=True)

# ------------------------------------------------------------------ markdown

def _enlinea(t, base_blob, base_raw, carpeta):
    partes = re.split(r"(`+)(.+?)\1", t)
    out = []
    for i in range(0, len(partes), 3):
        s = esc(partes[i])
        def img(m):
            u = _url(html.unescape(m.group(2)), base_raw, carpeta)
            return f'<img src="{esc(u)}" alt="{m.group(1)}" loading="lazy">'
        def lnk(m):
            u = _url(html.unescape(m.group(2)), base_blob, carpeta)
            return f'<a href="{esc(u)}" rel="noopener nofollow">{m.group(1)}</a>'
        s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+&quot;[^)]*&quot;)?\)", img, s)
        s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;[^)]*&quot;)?\)", lnk, s)
        s = re.sub(r"(?<![\"=>/\w])(https?://[^\s<)]+[^\s<).,;:])", r'<a href="\1" rel="noopener nofollow">\1</a>', s)
        s = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\w)__(?=\S)(.+?)(?<=\S)__(?!\w)", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<![\*\w])\*(?=\S)([^*]+?)(?<=\S)\*(?!\*)", r"<em>\1</em>", s)
        s = re.sub(r"(?<!\w)_(?=\S)([^_]+?)(?<=\S)_(?!\w)", r"<em>\1</em>", s)
        s = re.sub(r"~~(.+?)~~", r"<del>\1</del>", s)
        out.append(s)
        if i + 2 < len(partes):
            out.append(f"<code>{esc(partes[i + 2])}</code>")
    return "".join(out)

def _url(u, base, carpeta):
    if re.match(r"^(https?:|mailto:|#)", u):
        return u
    if not base:
        return "#"
    u = u.lstrip("./") if u.startswith("./") else u
    if u.startswith("/"):
        return base + u
    partes = [p for p in (carpeta.split("/") if carpeta else []) if p]
    for seg in u.split("/"):
        if seg == "..":
            if partes:
                partes.pop()
        elif seg and seg != ".":
            partes.append(seg)
    return base + "/" + "/".join(partes)

def markdown(texto, base_blob="", base_raw="", carpeta=""):
    L = texto.replace("\t", "    ").split("\n")
    out, i, n = [], 0, len(L)
    inl = lambda t: _enlinea(t, base_blob, base_raw, carpeta)
    def cerrar_parrafo(buf):
        if buf:
            out.append("<p>" + "<br>".join(inl(x) for x in buf) + "</p>")
            buf.clear()
    buf = []
    while i < n:
        l = L[i]
        m = re.match(r"^\s*(```+|~~~+)\s*([\w+\-.]*)", l)
        if m:
            cerrar_parrafo(buf)
            cerca, cuerpo = m.group(1)[0] * 3, []
            i += 1
            while i < n and not L[i].strip().startswith(cerca):
                cuerpo.append(L[i]); i += 1
            i += 1
            out.append(f'<pre class="bloque"><code>{esc(chr(10).join(cuerpo))}</code></pre>')
            continue
        if not l.strip():
            cerrar_parrafo(buf); i += 1; continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", l)
        if m:
            cerrar_parrafo(buf)
            k = min(6, len(m.group(1)) + 2)
            out.append(f"<h{k}>{inl(m.group(2))}</h{k}>"); i += 1; continue
        if re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", l):
            cerrar_parrafo(buf); out.append("<hr>"); i += 1; continue
        if l.lstrip().startswith(">"):
            cerrar_parrafo(buf); cita = []
            while i < n and L[i].lstrip().startswith(">"):
                cita.append(re.sub(r"^\s*>\s?", "", L[i])); i += 1
            out.append("<blockquote>" + markdown("\n".join(cita), base_blob, base_raw, carpeta) + "</blockquote>"); continue
        if "|" in l and i + 1 < n and re.match(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", L[i + 1]):
            cerrar_parrafo(buf)
            celdas = lambda s: [c.strip() for c in s.strip().strip("|").split("|")]
            cab = celdas(l); i += 2; filas = []
            while i < n and "|" in L[i] and L[i].strip():
                filas.append(celdas(L[i])); i += 1
            t = ['<div class="tabla"><table><thead><tr>' + "".join(f"<th>{inl(c)}</th>" for c in cab) + "</tr></thead><tbody>"]
            for f in filas:
                t.append("<tr>" + "".join(f"<td>{inl(c)}</td>" for c in f) + "</tr>")
            out.append("".join(t) + "</tbody></table></div>"); continue
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", l)
        if m:
            cerrar_parrafo(buf)
            pila = []
            def abrir(ind, ordenada):
                pila.append((ind, ordenada)); out.append("<ol>" if ordenada else "<ul>")
            def bajar(hasta):
                while pila and pila[-1][0] > hasta:
                    out.append("</li></ol>" if pila[-1][1] else "</li></ul>"); pila.pop()
            while i < n:
                m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", L[i])
                if not m:
                    if L[i].strip() and L[i].startswith(" ") and pila:
                        out.append(" " + inl(L[i].strip())); i += 1; continue
                    if not L[i].strip() and i + 1 < n and re.match(r"^(\s*)([-*+]|\d+[.)])\s+", L[i + 1]):
                        i += 1; continue
                    break
                ind, ordenada = len(m.group(1)), m.group(2)[0].isdigit()
                if not pila or ind > pila[-1][0]:
                    abrir(ind, ordenada)
                else:
                    bajar(ind)
                    if pila and pila[-1][0] == ind:
                        out.append("</li>")
                    else:
                        abrir(ind, ordenada)
                txt = re.sub(r"^\[( |x|X)\]\s+", lambda c: "☑ " if c.group(1).strip() else "☐ ", m.group(3))
                out.append("<li>" + inl(txt)); i += 1
            bajar(-1)
            continue
        buf.append(l.strip()); i += 1
    cerrar_parrafo(buf)
    return "\n".join(out)

# ------------------------------------------------------------------ resaltado

PALABRAS = {
    "R": set("if else for while repeat function return next break in TRUE FALSE NULL NA NA_integer_ NA_real_ NA_character_ Inf NaN library require source".split()),
    "Python": set("def class return if elif else for while in not and or is None True False import from as with try except finally raise lambda yield pass break continue global nonlocal assert del async await".split()),
    "SQL": set("select from where group by order having join left right inner outer on as and or not null case when then else end create table insert into values update set delete with union all distinct limit over partition".split()),
    "Shell": set("if then else elif fi for do done while case esac function in echo export cd".split()),
}
TOKEN = re.compile(r"""(?P<s>\"\"\"|'''|"(?:\\.|[^"\\\n])*"?|'(?:\\.|[^'\\\n])*'?)|(?P<c>\#.*$)|(?P<n>\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?L?\b)|(?P<w>[A-Za-z_.][A-Za-z0-9_.]*)""")

def familia(lenguaje):
    l = (lenguaje or "").lower()
    if "python" in l:
        return "Python"
    if l.startswith("r") or "(r)" in l or "quarto" in l:
        return "R"
    if "sql" in l:
        return "SQL"
    if "shell" in l or "batch" in l:
        return "Shell"
    return ""

def resaltar(lineas, lenguaje):
    """Devuelve una lista de HTML por línea. Mantiene el estado de las cadenas de triple comilla de Python."""
    fam = familia(lenguaje)
    if not fam:
        return [esc(l) for l in lineas]
    pal, out, triple = PALABRAS.get(fam, set()), [], None
    for l in lineas:
        if fam == "SQL":
            i = l.find("--")
            cuerpo, com = (l[:i], l[i:]) if i >= 0 else (l, "")
            h = "".join(f'<span class="k">{esc(w)}</span>' if w.lower() in pal else esc(w) for w in re.split(r"(\w+)", cuerpo))
            out.append(h + (f'<span class="c">{esc(com)}</span>' if com else "")); continue
        if triple:
            j = l.find(triple)
            if j < 0:
                out.append(f'<span class="s">{esc(l)}</span>'); continue
            pre, l2 = l[:j + 3], l[j + 3:]
            cab, triple = f'<span class="s">{esc(pre)}</span>', None
        else:
            cab, l2 = "", l
        partes, pos = [], 0
        for m in TOKEN.finditer(l2):
            partes.append(esc(l2[pos:m.start()]))
            t = m.group(0)
            if m.lastgroup == "s":
                if t in ('"""', "'''") and fam == "Python":
                    resto = l2[m.end():]
                    j = resto.find(t)
                    if j < 0:
                        partes.append(f'<span class="s">{esc(l2[m.start():])}</span>'); triple = t; pos = len(l2); break
                    fin = m.end() + j + 3
                    partes.append(f'<span class="s">{esc(l2[m.start():fin])}</span>'); pos = fin
                    resto_html = resaltar([l2[fin:]], lenguaje)[0] if l2[fin:] else ""
                    partes.append(resto_html); pos = len(l2); break
                partes.append(f'<span class="s">{esc(t)}</span>')
            elif m.lastgroup == "c":
                partes.append(f'<span class="c">{esc(t)}</span>')
            elif m.lastgroup == "n":
                partes.append(f'<span class="n">{esc(t)}</span>')
            else:
                partes.append(f'<span class="k">{esc(t)}</span>' if t in pal else esc(t))
            pos = m.end()
        partes.append(esc(l2[pos:]))
        out.append(cab + "".join(partes))
    return out

if __name__ == "__main__":
    print(markdown("# Hola\n\nUn **texto** con `codigo` y [link](a/b.md).\n\n- uno\n- dos\n  - tres\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n```r\nx <- 1\n```\n", "https://x/blob/c", "https://x/raw/c", "docs"))
    print(resaltar(['x <- "hola" # comentario', "def f(a): return 3.5", '"""doc', 'sigue"""  y = 1'], "Python"))
