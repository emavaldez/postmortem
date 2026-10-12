"""
02_diagnostico_aguinaldo.py
DMEyF 2026 - Primera Competencia

Pregunta: ¿el aguinaldo de junio cambia los datos o el comportamiento de los clientes?
  A. ¿Se ve el aguinaldo en las variables de sueldo (payroll)?
  B. ¿Cuantos clientes tienen un "salto" de sueldo tipo aguinaldo (x1.3 a x1.7) cada mes?
  C. ¿Cambia la tasa de bajas segun el mes y segun si el cliente cobra sueldo en el banco?
  D. En junio/julio: ¿los que recibieron el salto se dan de baja distinto que el resto?

Se miran junio Y julio porque el aguinaldo puede acreditarse unos dias despues del 30/6.

Uso:  python 02_diagnostico_aguinaldo.py   (despues de 01_preparar_dataset.py; exp_utils.py en la misma carpeta)
Requiere:  pip install pandas pyarrow plotly
"""

print("Arrancando 02_diagnostico_aguinaldo.py ...", flush=True)

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pyarrow.parquet as pq

from exp_utils import DIR_DATA, cerrar_experimento, iniciar_experimento

# ---------------------------------------------------------------------------
# PARAM
# ---------------------------------------------------------------------------
PARAM = {
    "experimento": 2001,
    "nombre": "diagnostico_aguinaldo",
    "descripcion": "Efecto del aguinaldo (jun/jul) en variables de sueldo y en la tasa de bajas.",
    "dataset": "ds1001_base.parquet",
    "salto_min": 1.3,     # sueldo de este mes / sueldo del mes anterior
    "salto_max": 1.7,
}

exp = iniciar_experimento(PARAM)
ARCH_DATASET = DIR_DATA / PARAM["dataset"]
ARCH_HTML = exp.ruta("graficos", ext="html")
SALTO_MIN, SALTO_MAX = PARAM["salto_min"], PARAM["salto_max"]

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

# ---------------------------------------------------------------------------
# Carga (solo las columnas necesarias, Parquet lo permite y es mucho mas rapido)
# ---------------------------------------------------------------------------
nombres = pq.ParquetFile(ARCH_DATASET).schema_arrow.names
cols_payroll = [c for c in nombres if "payroll" in c.lower()]
cols_monto = [c for c in cols_payroll if c.startswith("m")]
print("Variables de sueldo encontradas:", cols_payroll)
if not cols_monto:
    raise ValueError("No encontre variables de monto de sueldo (m...payroll...).")

df = pd.read_parquet(ARCH_DATASET,
                     columns=["numero_de_cliente", "foto_mes", "clase_ternaria"] + cols_payroll)
meses = sorted(int(m) for m in df["foto_mes"].unique())
meses_completos = meses[:-2]          # los que tienen clase ternaria completa

# sueldo total del cliente en el mes (suma de todos los montos de payroll)
df["sueldo"] = df[cols_monto].fillna(0).sum(axis=1)
df["cobra_sueldo"] = df["sueldo"] > 0

# ---------------------------------------------------------------------------
# A. Variables de sueldo mes a mes
# ---------------------------------------------------------------------------
print("\n=== A. VARIABLES DE SUELDO POR MES ===")
filas = []
for c in cols_payroll:
    for m, sub in df.groupby("foto_mes"):
        pos = sub[c][sub[c] > 0]
        filas.append({"variable": c, "foto_mes": m,
                      "pct_clientes_con_valor": round(100 * len(pos) / len(sub), 2),
                      "mediana_si_>0": round(pos.median(), 1) if len(pos) else np.nan,
                      "total_millones": round(sub[c].sum() / 1e6, 1)})
tabla_a = pd.DataFrame(filas)
for c in cols_payroll:
    print(f"\n{c}")
    print(tabla_a[tabla_a["variable"] == c].drop(columns="variable").to_string(index=False))
tabla_a.to_csv(exp.ruta("A_variables_sueldo"), index=False)

# ---------------------------------------------------------------------------
# B. Salto de sueldo respecto del mes anterior, cliente por cliente
# ---------------------------------------------------------------------------
df = df.sort_values(["numero_de_cliente", "foto_mes"])
periodo = (df["foto_mes"] // 100) * 12 + df["foto_mes"] % 100
g = df.groupby("numero_de_cliente", sort=False)
consecutivo = (periodo - g["foto_mes"].shift(1).pipe(lambda s: (s // 100) * 12 + s % 100)) == 1
sueldo_ant = g["sueldo"].shift(1)

comparable = consecutivo & (df["sueldo"] > 0) & (sueldo_ant > 0)
df["ratio_sueldo"] = np.where(comparable, df["sueldo"] / sueldo_ant, np.nan)
df["salto_aguinaldo"] = df["ratio_sueldo"].between(SALTO_MIN, SALTO_MAX)

print("\n=== B. SUELDO DE ESTE MES / SUELDO DEL MES ANTERIOR (clientes que cobran ambos meses) ===")
tabla_b = (df[comparable].groupby("foto_mes")
             .agg(clientes=("ratio_sueldo", "size"),
                  ratio_mediano=("ratio_sueldo", "median"),
                  pct_salto_aguinaldo=("salto_aguinaldo", lambda s: 100 * s.mean()),
                  pct_estable_0_9_a_1_1=("ratio_sueldo", lambda s: 100 * s.between(0.9, 1.1).mean()))
             .round(3))
print(tabla_b.to_string())
tabla_b.to_csv(exp.ruta("B_salto_sueldo"))
print("Lectura: un mes normal deberia tener ratio mediano cercano a 1 (algo mas por inflacion).\n"
      "Si junio o julio muestran ~1.5 y mucho % de salto, el aguinaldo esta en los datos.")

# ---------------------------------------------------------------------------
# C. Tasa de bajas por mes, segun cobra sueldo o no
# ---------------------------------------------------------------------------
print("\n=== C. TASA DE BAJAS (%) POR MES, SEGUN COBRA SUELDO EN EL BANCO ===")
# Se usan todos los meses menos el ultimo. En el anteultimo solo se puede calcular
# BAJA+1 (los demas clientes quedan sin clase y cuentan como "no BAJA+1");
# su BAJA+2 se deja vacio porque no es calculable.
base = df[df["foto_mes"].isin(meses[:-1])].copy()
base["ct"] = base["clase_ternaria"].fillna("SIN_CLASE")


def tasas(datos, claves):
    t = (datos.groupby(claves)["ct"]
              .agg(clientes="size",
                   pct_baja2=lambda s: 100 * (s == "BAJA+2").mean(),
                   pct_baja1=lambda s: 100 * (s == "BAJA+1").mean())
              .round(3))
    t.loc[t.index.get_level_values("foto_mes") == meses[-2], "pct_baja2"] = np.nan
    return t


tabla_c = tasas(base, ["foto_mes", "cobra_sueldo"])
print(tabla_c.to_string())
tabla_c.to_csv(exp.ruta("C_bajas_cobra_sueldo"))
print(f"{meses[-2]}: solo BAJA+1 es calculable (BAJA+2 queda vacio).")

# ---------------------------------------------------------------------------
# D. ¿Los que recibieron el salto en junio/julio se van distinto?
# ---------------------------------------------------------------------------
print("\n=== D. BAJAS SEGUN GRUPO DE SUELDO, MES POR MES ===")
df["grupo"] = np.select(
    [~df["cobra_sueldo"], df["salto_aguinaldo"]],
    ["sin sueldo", "con salto x1.3-1.7"],
    default="sueldo sin salto")
base["grupo"] = df.loc[base.index, "grupo"]
tabla_d = tasas(base, ["foto_mes", "grupo"])
print(tabla_d.to_string())
tabla_d.to_csv(exp.ruta("D_bajas_grupo_sueldo"))
print("Lectura: comparar el grupo 'con salto' contra 'sueldo sin salto' DENTRO de cada mes.\n"
      "Con solo 4 meses completos esto es una pista, no una prueba.")

# ---------------------------------------------------------------------------
# Graficos (HTML interactivo, abrir en el navegador)
# ---------------------------------------------------------------------------
COLOR = {"principal": "#6C5CE7", "secundario": "#00B894", "terciario": "#FD79A8", "gris": "#B2BEC3"}
meses_txt = [str(m) for m in meses]


def estilo(fig, titulo, subtitulo, eje_y):
    fig.update_layout(
        title=dict(text=f"<b>{titulo}</b><br><span style='font-size:13px;color:#636e72'>{subtitulo}</span>",
                   x=0.02),
        font=dict(family="Inter, Segoe UI, Helvetica, sans-serif", size=14, color="#2d3436"),
        plot_bgcolor="white", paper_bgcolor="white", height=460,
        margin=dict(l=70, r=30, t=95, b=50),
        legend=dict(orientation="h", y=-0.15, x=0),
        xaxis=dict(type="category", showgrid=False, linecolor="#dfe6e9"),
        yaxis=dict(title=eje_y, gridcolor="#f1f2f6", zeroline=False),
        hoverlabel=dict(bgcolor="white"),
    )
    return fig


figs = []

# 1. ratio mediano y % con salto
f1 = go.Figure()
f1.add_bar(x=[str(m) for m in tabla_b.index], y=tabla_b["pct_salto_aguinaldo"],
           marker_color=COLOR["principal"], name="% clientes con salto x1.3-1.7",
           text=tabla_b["pct_salto_aguinaldo"].round(1), textposition="outside")
figs.append(estilo(f1, "¿Se ve el aguinaldo en los sueldos?",
                   "% de clientes cuyo sueldo salto entre 1.3 y 1.7 veces respecto del mes anterior",
                   "% de clientes"))

# 2. total acreditado por mes (variable de monto principal)
var_ppal = cols_monto[0]
ta = tabla_a[tabla_a["variable"] == var_ppal]
f2 = go.Figure()
f2.add_scatter(x=[str(m) for m in ta["foto_mes"]], y=ta["total_millones"], mode="lines+markers",
               line=dict(color=COLOR["secundario"], width=4, shape="spline"),
               marker=dict(size=11), name=var_ppal)
figs.append(estilo(f2, f"Total acreditado en {var_ppal}",
                   "Millones de pesos por mes", "millones"))

# 3. tasa de BAJA+2 por mes segun cobra sueldo
tc = tabla_c.reset_index()
tc = tc[tc["foto_mes"].isin(meses_completos)]
f3 = go.Figure()
for valor, nombre, color in [(True, "Cobra sueldo en el banco", COLOR["principal"]),
                             (False, "No cobra sueldo", COLOR["terciario"])]:
    s = tc[tc["cobra_sueldo"] == valor]
    f3.add_scatter(x=[str(m) for m in s["foto_mes"]], y=s["pct_baja2"], mode="lines+markers",
                   line=dict(color=color, width=4), marker=dict(size=11), name=nombre)
figs.append(estilo(f3, "Tasa de BAJA+2 por mes",
                   "Junio (202106) = clientes que se van en agosto", "% BAJA+2"))

# 4. BAJA+2 por grupo de sueldo en cada mes
td = tabla_d.reset_index()
td = td[td["foto_mes"].isin(meses_completos)]
f4 = go.Figure()
for grupo, color in [("sin sueldo", COLOR["gris"]), ("sueldo sin salto", COLOR["secundario"]),
                     ("con salto x1.3-1.7", COLOR["principal"])]:
    s = td[td["grupo"] == grupo]
    f4.add_bar(x=[str(m) for m in s["foto_mes"]], y=s["pct_baja2"], name=grupo, marker_color=color)
f4.update_layout(barmode="group")
figs.append(estilo(f4, "¿Los que recibieron el salto se van distinto?",
                   "% BAJA+2 por grupo, dentro de cada mes", "% BAJA+2"))

html = ["<html><head><meta charset='utf-8'><title>Diagnostico aguinaldo</title>",
        "<script src='https://cdn.plot.ly/plotly-2.35.2.min.js'></script></head>",
        "<body style='max-width:980px;margin:30px auto;font-family:Inter,Segoe UI,sans-serif'>"]
html += [f.to_html(full_html=False, include_plotlyjs=False) for f in figs]
html.append("</body></html>")
ARCH_HTML.write_text("\n".join(html), encoding="utf-8")
print(f"\nGraficos en: {ARCH_HTML}")

cerrar_experimento(exp, {
    "ratio_mediano_por_mes": tabla_b["ratio_mediano"].to_dict(),
    "pct_salto_por_mes": tabla_b["pct_salto_aguinaldo"].to_dict(),
})
