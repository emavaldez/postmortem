# DMEyF 2026 - Competencia 1

Este repositorio contiene el código, notebooks y experimentos desarrollados para la **Competencia 1** de la materia Datos Minería y Finanzas (DMEyF 2026).

---

## 🚀 Requisitos e Instalación

Desde la raíz del repositorio (`dmeyf2026/`):

1. **Crear y activar el entorno virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 📌 Reproducción del Submit con `main.py`

El script `main.py` está preparado y configurado por defecto para reproducir exactamente lo que fue el **último submit de la competencia**.

El script corre el flujo completo (o carga del disco todo lo ya calculado en `db/`, `modelos/` y `resultados/` para una reproducción inmediata) y genera el archivo `.csv` final listo para la plataforma directamente en la carpeta `competencia_uno/`.

### Ejecución

Ejecutar z101_target_sql.ipynb para generar competencia_01.csv en competencia_uno.

Ejecutar python competencia_uno/generate_features_extendido.py. Genera un archivo .parquet.


Por último, desde la raíz del repositorio:
```bash
.venv/bin/python competencia_uno/main.py
```

*(O si estás ubicado dentro de la carpeta `competencia_uno/`:)*
```bash
../.venv/bin/python main.py
```

### Comparación con el submit de referencia (opcional)
Si deseas comprobar automáticamente que el submit generado coincida cliente por cliente con el archivo original enviado:
```bash
.venv/bin/python competencia_uno/main.py --comparar competencia_uno/submits/it01_bordes_train202103-202104-202105_test202106_dsextendido_us10_clasebaja1y2_optumbral_ajustado_trial49_top12058_20261007_182001.csv
```

---

## 📂 Salidas y Resultados

* **Submits generados por `main.py`:** se guardan directamente en `competencia_uno/<nombre_experimento>_<fecha_hora>.csv` para no sobreescribir los archivos de la carpeta `submits/`.
* **Caché y reproducibilidad:** El script carga automáticamente los estudios de Optuna desde `db/`, los modelos entrenados desde `modelos/` y las predicciones calculadas desde `resultados/`. No recalcula lo existente, asegurando idénticos resultados y tiempos de ejecución mínimos.
