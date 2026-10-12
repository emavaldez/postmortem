# 2 — Variables

**Qué hice:** a las 152 variables originales les agregué historia (lag, delta y transiciones mes a mes de cada variable) y ratios entre las variables de tarjetas. Son 1.910 variables nuevas; con las originales, **2.062**. A ese conjunto lo llamo **C3**.

Antes probé agregar muchísimas más variables (miles, de varias familias: rankings, estados, transformaciones) y fue peor que no agregar nada. C3 fue la única combinación que mejoró de forma estable en junio: +8,95 M ARS con 5 semillas, y confirmado con 20 semillas (+6,01 M, 15 de 20 a favor).

| Archivo | Qué hace |
|---|---|
| `experimentos_20261006_m1_fe_masiva/fe_amplia/generar_fe.py` y `fe_*.py` | Generan las variables por bloques; `catalogo_fuentes.csv` dice de qué variable original sale cada una |
| `experimentos_20261006_m1_fe_masiva/run_screening.py` | Construye el banco completo de variables (`fe_bank_dev`) y hace la primera comparación |
| `experimentos_20261006_m1_fe_masiva/run_s3_confirm_c3.py` | Confirma C3 con 20 semillas y deja la lista de las 2.062 variables (`C3_HIST_MAS_TARJETAS/features.json`) |
| `vendor/comun/config.yaml` | Parámetros base de LightGBM y meses del protocolo |
| `PAQUETE.json` | Hash de cada archivo; el paso 4 lo usa para comprobar que el código de este paso es el que corrió |

Esta carpeta es el "paquete" que el paso 4 espera en `$HOME/c1m1femasiva03_s3/paquete_c1/`, por eso tiene esa estructura y no se le pueden cambiar los nombres.

```bash
mkdir -p $HOME/c1m1femasiva03_s3
cp -r 2_variables $HOME/c1m1femasiva03_s3/paquete_c1
D=$HOME/c1m1femasiva03/datos/competencia_01.parquet
cd $HOME/c1m1femasiva03_s3/paquete_c1/experimentos_20261006_m1_fe_masiva
python run_screening.py      --data $D --out $HOME/c1m1femasiva03_s3/resultados_s1 --solo-generar-fe
python run_s3_confirm_c3.py  --data $D --s1-root $HOME/c1m1femasiva03_s3/resultados_s1 --out $HOME/c1m1femasiva03_s3/resultados_s3
```

`--solo-generar-fe` construye el banco de variables y termina; sin ese flag además entrena los 15 modelos de la comparación masiva, que no hacen falta para la entrega.

Salidas que usa el paso 4: `resultados_s1/fe_bank_dev/` (banco de variables y `etiquetas.parquet`) y `resultados_s3/confirmacion_c3.json` + `resultados_s3/C3_HIST_MAS_TARJETAS/features.json`.
