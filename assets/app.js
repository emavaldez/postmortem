"use strict";
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const RAIZ = document.documentElement.dataset.raiz || "";
const ruta = p => RAIZ + p.split("/").map(encodeURIComponent).join("/");

const PALABRAS = {
  R: "if else for while repeat function return next break in TRUE FALSE NULL NA Inf NaN library require source".split(" "),
  Python: "def class return if elif else for while in not and or is None True False import from as with try except finally raise lambda yield pass break continue global assert del".split(" "),
};
function familia(l) {
  l = (l || "").toLowerCase();
  if (l.includes("python")) return "Python";
  if (l.startsWith("r") || l.includes("(r)") || l.includes("quarto")) return "R";
  return "";
}
function resaltar(linea, fam) {
  if (!fam) return esc(linea);
  const pal = PALABRAS[fam] || [];
  const re = /("(?:\\.|[^"\\])*"?|'(?:\\.|[^'\\])*'?)|(#.*$)|(\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?L?\b)|([A-Za-z_.][A-Za-z0-9_.]*)/g;
  let out = "", pos = 0, m;
  while ((m = re.exec(linea))) {
    out += esc(linea.slice(pos, m.index));
    if (m[1]) out += '<span class="s">' + esc(m[1]) + "</span>";
    else if (m[2]) out += '<span class="c">' + esc(m[2]) + "</span>";
    else if (m[3]) out += '<span class="n">' + esc(m[3]) + "</span>";
    else out += pal.includes(m[4]) ? '<span class="k">' + esc(m[4]) + "</span>" : esc(m[4]);
    pos = re.lastIndex;
  }
  return out + esc(linea.slice(pos));
}
function pintarCodigo(texto, archivo, prefijo, enlaceBase) {
  const lineas = texto.replace(/\n$/, "").split("\n");
  const fam = familia(archivo.lenguaje), cuaderno = (archivo.lenguaje || "").startsWith("Jupyter");
  const notas = {};
  (archivo.anotaciones || []).forEach(n => { notas[n.desde] = n; });
  let prosa = false, h = "";
  lineas.forEach((l, i) => {
    const k = i + 1;
    if (notas[k]) h += `<div class="nota"><span class="rango">Anotación · líneas ${notas[k].desde}–${notas[k].hasta}</span>${esc(notas[k].texto)}</div>`;
    let cls = "l", cuerpo;
    if (cuaderno && l.startsWith("#%% celda")) { prosa = l.includes("[texto]"); cls += " celda"; cuerpo = esc(l.slice(4)); }
    else if (prosa) { cls += " prosa"; cuerpo = esc(l); }
    else cuerpo = resaltar(l, fam);
    const href = enlaceBase ? `${enlaceBase}#${prefijo}-L${k}` : `#${prefijo}-L${k}`;
    h += `<div class="${cls}" id="${prefijo}-L${k}"><a class="ln" href="${href}">${k}</a><span class="t">${cuerpo || " "}</span></div>`;
  });
  return h;
}

// ---------------------------------------------------------------- página de una entrega
function iniciarEntrega() {
  const b = $("#alternar-notas");
  if (b) b.addEventListener("click", () => {
    const off = document.body.classList.toggle("sin-notas");
    b.textContent = off ? "Mostrar anotaciones" : "Ocultar anotaciones";
    b.setAttribute("aria-pressed", String(off));
  });
  $$("details[data-src]").forEach(d => d.addEventListener("toggle", async () => {
    if (!d.open || d.dataset.listo) return;
    d.dataset.listo = "1";
    const caja = $(".codigo", d);
    try {
      const r = await fetch(d.dataset.src);
      if (!r.ok) throw new Error(r.status);
      const t = await r.text();
      caja.innerHTML = pintarCodigo(t, { lenguaje: d.dataset.leng, anotaciones: [] }, d.dataset.ancla, "");
    } catch (e) {
      caja.innerHTML = `<div class="l"><span class="t">No se pudo cargar el archivo desde esta página. Se puede abrir desde el enlace «texto».</span></div>`;
    }
  }));
}

// ---------------------------------------------------------------- listado con filtro
function iniciarFiltro() {
  const q = $("#filtro"), sel = $("#filtro-tecnica"), cuenta = $("#cuenta");
  if (!q) return;
  const filas = $$("[data-buscar]");
  const aplicar = () => {
    const t = q.value.trim().toLowerCase(), c = sel ? sel.value : "";
    let n = 0;
    filas.forEach(f => {
      const ok = (!t || f.dataset.buscar.includes(t)) && (!c || (" " + f.dataset.tecnicas + " ").includes(" " + c + " "));
      f.classList.toggle("oculto", !ok); if (ok) n++;
    });
    if (cuenta) cuenta.textContent = `${n} de ${filas.length}`;
  };
  q.addEventListener("input", aplicar); if (sel) sel.addEventListener("change", aplicar); aplicar();
}

// ---------------------------------------------------------------- comparador
const CAMPOS = [
  ["lenguajes", "Lenguajes"], ["modelos", "Modelos"], ["clase_objetivo", "Clase que entrena"], ["meses_entrenamiento", "Meses de entrenamiento"],
  ["meses_validacion", "Meses de validación"], ["meses_prediccion", "Mes que predice"], ["submuestreo", "Submuestreo"], ["calidad_de_datos", "Calidad de datos"],
  ["drifting", "Drifting"], ["variables_intra_mes", "Variables dentro del mes"], ["variables_historicas", "Variables históricas"],
  ["seleccion_de_variables", "Selección de variables"], ["optimizacion_de_hiperparametros", "Optimización de hiperparámetros"],
  ["hiperparametros_finales", "Hiperparámetros finales"], ["semillas", "Semillas"], ["cantidad_de_semillas", "Cantidad de semillas"], ["ensamble", "Ensamble"],
  ["corte", "Corte"], ["validacion", "Validación"], ["salidas", "Salidas"],
];
const REPRO = [
  ["tiene_readme", "Tiene README o texto de presentación"], ["explica_como_ejecutar", "Explica cómo ejecutar"], ["declara_versiones_o_dependencias", "Declara versiones o dependencias"],
  ["fija_semillas", "Fija las semillas"], ["usa_rutas_absolutas_o_de_una_maquina", "Usa rutas absolutas o de una máquina"], ["incluye_datos_o_predicciones", "Incluye datos o predicciones"],
  ["es_un_solo_comando", "Sale de un solo script o notebook"],
];
const valor = v => Array.isArray(v) ? v.join(", ") : (v === null || v === undefined || v === "" ? "—" : String(v));

async function iniciarComparador() {
  const sa = $("#sel-a"), sb = $("#sel-b");
  if (!sa) return;
  const indice = await (await fetch(ruta("data/index.json"))).json();
  const voc = await (await fetch(ruta("data/tecnicas.json"))).json();
  const etiqueta = {}; voc.grupos.forEach(g => g.tecnicas.forEach(t => { etiqueta[t.codigo] = t.nombre; }));
  const opciones = indice.entregas.map(e => `<option value="${esc(e.slug)}">${esc(e.nombre)}${e.nombre.toLowerCase() !== e.usuario.toLowerCase() ? " (" + esc(e.usuario) + ")" : ""}</option>`).join("");
  sa.innerHTML = '<option value="">Elegir entrega A…</option>' + opciones;
  sb.innerHTML = '<option value="">Elegir entrega B…</option>' + opciones;
  const p = new URLSearchParams(location.search);
  if (p.get("a")) sa.value = p.get("a");
  if (p.get("b")) sb.value = p.get("b");
  const cache = {};
  const cargar = async slug => cache[slug] || (cache[slug] = await (await fetch(ruta(`data/entregas/${slug}.json`))).json());

  async function mostrarArchivo(lado, d, idx, linea) {
    const a = d.archivos[idx], caja = $(`#cod-${lado}`), info = $(`#info-${lado}`);
    $(`#arch-${lado}`).value = String(idx);
    info.innerHTML = `${esc(a.descripcion || "")} <span class="meta">· ${esc(a.lenguaje || "")} · ${a.lineas} líneas · <a href="${ruta("entregas/" + d.slug + "/")}#${a.ancla}">en su página</a>${a.github ? ` · <a href="${esc(a.github)}" rel="noopener">GitHub</a>` : ""}</span>`;
    if (!a.texto) { caja.innerHTML = '<div class="l"><span class="t">El contenido de este archivo no se publica en esta página.</span></div>'; return; }
    caja.innerHTML = '<div class="l"><span class="t">Cargando…</span></div>';
    const t = await (await fetch(ruta(a.texto))).text();
    caja.innerHTML = pintarCodigo(t, a, `${lado}`, "");
    if (linea) {
      const el = $(`#${lado}-L${linea}`);
      if (el) { $$(".marcada", caja).forEach(x => x.classList.remove("marcada")); el.classList.add("marcada"); caja.scrollTop = el.offsetTop - caja.offsetTop - 60; }
    } else caja.scrollTop = 0;
  }
  function panel(lado, d) {
    const cont = $(`#panel-${lado}`);
    const orden = { principal: 0, configuracion: 1, secundario: 2, explicacion: 3, ajeno: 4 };
    const idxs = d.archivos.map((a, i) => i).filter(i => d.archivos[i].tipo !== "texto" || d.archivos[i].rol === "principal").sort((x, y) => (orden[d.archivos[x].rol] - orden[d.archivos[y].rol]) || d.archivos[x].ruta.localeCompare(d.archivos[y].ruta));
    const opts = idxs.map(i => `<option value="${i}">[${d.archivos[i].rol}] ${esc(d.archivos[i].ruta)}</option>`).join("");
    const pasos = (d.pasos || []).map((s, k) => {
      const r = (s.referencias || [])[0];
      const i = r ? d.archivos.findIndex(a => a.ruta === r.ruta) : -1;
      return `<li>${i >= 0 ? `<a href="#" data-lado="${lado}" data-arch="${i}" data-linea="${r.desde}">${esc(s.titulo)}</a>` : esc(s.titulo)}</li>`;
    }).join("");
    cont.innerHTML = `<h3><a href="${ruta("entregas/" + d.slug + "/")}">${esc(d.nombre)}</a></h3>
      <p class="meta">${esc(d.repo)}</p>
      <details open><summary>Pasos del camino de la entrega (un clic lleva al código)</summary><ol class="lista-pasos">${pasos || "<li>Sin pasos descriptos.</li>"}</ol></details>
      <label class="meta" for="arch-${lado}">Archivo</label><br><select id="arch-${lado}" style="width:100%">${opts}</select>
      <p id="info-${lado}" style="font-size:.9rem"></p>
      <div class="codigo" id="cod-${lado}" tabindex="0" aria-label="Código de ${esc(d.nombre)}"></div>`;
    $(`#arch-${lado}`).addEventListener("change", e => mostrarArchivo(lado, d, Number(e.target.value)));
    $$("a[data-arch]", cont).forEach(a => a.addEventListener("click", e => { e.preventDefault(); mostrarArchivo(lado, d, Number(a.dataset.arch), Number(a.dataset.linea)); }));
    if (idxs.length) mostrarArchivo(lado, d, idxs[0]); else $(`#cod-${lado}`).innerHTML = '<div class="l"><span class="t">Esta entrega no tiene archivos de código.</span></div>';
  }
  async function comparar() {
    const a = sa.value, b = sb.value, zona = $("#comparacion");
    const q = new URLSearchParams(); if (a) q.set("a", a); if (b) q.set("b", b);
    history.replaceState(null, "", location.pathname + (q.toString() ? "?" + q : ""));
    if (!a || !b) { zona.classList.add("oculto"); return; }
    const [A, B] = await Promise.all([cargar(a), cargar(b)]);
    zona.classList.remove("oculto");
    const filas = CAMPOS.map(([k, n]) => {
      const x = valor((A.ficha || {})[k]), y = valor((B.ficha || {})[k]);
      const cls = x === y ? "igual" : "distinto";
      return `<tr><th scope="row">${n}</th><td class="${cls}">${esc(x)}</td><td class="${cls}">${esc(y)}</td></tr>`;
    }).join("");
    $("#tabla-ficha").innerHTML = `<thead><tr><th></th><th>${esc(A.nombre)}</th><th>${esc(B.nombre)}</th></tr></thead><tbody>${filas}</tbody>`;
    const ta = new Set(A.tecnicas_en_la_entrega || []), tb = new Set(B.tecnicas_en_la_entrega || []);
    const chips = l => l.length ? l.map(c => `<span class="chip si">${esc(etiqueta[c] || c)}</span>`).join("") : '<span class="meta">—</span>';
    $("#tec-a").innerHTML = chips([...ta].filter(c => !tb.has(c)));
    $("#tec-ab").innerHTML = chips([...ta].filter(c => tb.has(c)));
    $("#tec-b").innerHTML = chips([...tb].filter(c => !ta.has(c)));
    $("#tec-na").textContent = "Sólo " + A.nombre; $("#tec-nb").textContent = "Sólo " + B.nombre;
    const sn = v => v === true ? '<span class="si-no si">Sí</span>' : v === false ? '<span class="si-no no">No</span>' : "—";
    $("#tabla-repro").innerHTML = `<thead><tr><th></th><th>${esc(A.nombre)}</th><th>${esc(B.nombre)}</th></tr></thead><tbody>` + REPRO.map(([k, n]) => `<tr><th scope="row">${n}</th><td>${sn((A.reproducibilidad || {})[k])}</td><td>${sn((B.reproducibilidad || {})[k])}</td></tr>`).join("") + "</tbody>";
    $("#res-a").innerHTML = `<strong>${esc(A.nombre)}.</strong> ${esc(A.resumen || "")}`;
    $("#res-b").innerHTML = `<strong>${esc(B.nombre)}.</strong> ${esc(B.resumen || "")}`;
    panel("a", A); panel("b", B);
  }
  sa.addEventListener("change", comparar); sb.addEventListener("change", comparar);
  $("#invertir").addEventListener("click", () => { const t = sa.value; sa.value = sb.value; sb.value = t; comparar(); });
  comparar();
}

// ---------------------------------------------------------------- buscador
async function iniciarBuscador() {
  const q = $("#consulta");
  if (!q) return;
  const estado = $("#estado-busqueda"), salida = $("#resultados"), chk = $("#exp-regular"), may = $("#mayusculas");
  let datos = null;
  const cargar = async () => datos || (estado.textContent = "Cargando el índice…", datos = await (await fetch(ruta("data/busqueda.json"))).json());
  async function buscar() {
    const t = q.value;
    const p = new URLSearchParams(); if (t) p.set("q", t); if (chk.checked) p.set("re", "1"); if (may.checked) p.set("mm", "1");
    history.replaceState(null, "", location.pathname + (p.toString() ? "?" + p : ""));
    if (t.trim().length < 2) { salida.innerHTML = ""; estado.textContent = "Escribí al menos dos caracteres."; return; }
    const d = await cargar();
    let re;
    try { re = new RegExp(chk.checked ? t : t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), may.checked ? "g" : "gi"); }
    catch (e) { estado.textContent = "Expresión regular inválida."; return; }
    let n = 0, entregas = new Set(), h = "";
    const TOPE = 400;
    for (const e of d.entregas) for (const a of e.archivos) {
      for (let i = 0; i < a.lineas.length; i++) {
        re.lastIndex = 0;
        if (!re.test(a.lineas[i])) continue;
        n++; entregas.add(e.slug);
        if (n > TOPE) continue;
        re.lastIndex = 0;
        const marcada = esc(a.lineas[i]).replace(new RegExp(re.source.replace(/</g, "&lt;").replace(/>/g, "&gt;"), re.flags), m => m ? `<mark>${m}</mark>` : m);
        h += `<div class="resultado"><div class="donde"><a href="${ruta("entregas/" + e.slug + "/")}#${a.ancla}-L${i + 1}">${esc(e.nombre)} · ${esc(a.ruta)} · línea ${i + 1}</a></div><pre>${marcada}</pre></div>`;
      }
    }
    estado.textContent = n ? `${n} líneas en ${entregas.size} entregas${n > TOPE ? ` (se muestran las primeras ${TOPE})` : ""}.` : "Sin resultados.";
    salida.innerHTML = h;
  }
  let reloj;
  const diferir = () => { clearTimeout(reloj); reloj = setTimeout(buscar, 220); };
  q.addEventListener("input", diferir); chk.addEventListener("change", buscar); may.addEventListener("change", buscar);
  const p = new URLSearchParams(location.search);
  if (p.get("re")) chk.checked = true; if (p.get("mm")) may.checked = true;
  if (p.get("q")) { q.value = p.get("q"); buscar(); }
}

document.addEventListener("DOMContentLoaded", () => {
  iniciarEntrega(); iniciarFiltro();
  iniciarComparador().catch(e => { const z = $("#aviso-carga"); if (z) z.classList.remove("oculto"); console.error(e); });
  iniciarBuscador().catch(e => { const z = $("#aviso-carga"); if (z) z.classList.remove("oculto"); console.error(e); });
  if (location.hash) { const el = document.getElementById(location.hash.slice(1)); if (el) { const d = el.closest("details"); if (d) d.open = true; } }
});
