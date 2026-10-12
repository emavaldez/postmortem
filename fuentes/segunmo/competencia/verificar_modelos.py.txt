"""Compara los modelos guardados en `artifacts/modelos_final/` con las huellas versionadas en `competencia/modelos_manifiesto.csv`.
Uso (raíz del repo): venv/bin/python competencia/verificar_modelos.py
Cada modelo regenerado con el código corregido y el mismo entorno (requirements-lock.txt) debe tener exactamente la misma huella."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from modelos import CARPETA, MANIFIESTO, _leer, huella_archivo  # noqa: E402

filas = _leer()
if not filas:
    sys.exit(f"El manifiesto {MANIFIESTO} está vacío o no existe.")
ok = faltan = distintos = 0
for nombre, fila in sorted(filas.items()):
    ruta = CARPETA / f"{nombre}.txt"
    if not ruta.exists():
        faltan += 1
    elif huella_archivo(ruta) == fila["sha256_modelo"]:
        ok += 1
    else:
        distintos += 1
        print("DISTINTO:", nombre)
print(f"{len(filas)} modelos en el manifiesto: {ok} idénticos, {distintos} distintos, {faltan} sin archivo en {CARPETA}")
sys.exit(0 if distintos == 0 and faltan == 0 else 1)
