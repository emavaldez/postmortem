"""Decisión final del plan de cierre de huecos (COBERTURA.md §7): Benjamini–Hochberg q=0.10 sobre TODA la familia de pruebas 037a–f.
m = 8 pruebas planeadas (037a_max, 037a_p90, 037b, 037c, 037d_r0.3, 037d_r1.0, 037e, 037f_categorico) + 1 prueba POSTERIOR al primer resultado de 037f (hojas numéricas),
que se incluye en la familia para no inflar los descubrimientos: m = 9. Pasa solo si el p-valor cumple BH Y delta >= +3M.
Uso (raíz del repo): venv/bin/python competencia/experimentos/037_hojas_rf/bh_final.py"""
from pathlib import Path

import pandas as pd

E, Q, MIN_DELTA = Path(__file__).resolve().parents[1], 0.10, 3.0
partes = [pd.read_csv(E / "037_huecos_abc" / "comparacion.csv")[["variante", "delta_M", "ee", "pares+", "p_unilateral"]],
          pd.read_csv(E / "037_huecos_de" / "comparacion_d.csv")[["variante", "delta_M", "ee", "pares+", "p_unilateral"]],
          pd.read_csv(E / "037_huecos_de" / "comparacion_e.csv")[["variante", "delta_M", "ee", "pares+", "p_unilateral"]],
          pd.read_csv(E / "037_hojas_rf" / "comparacion.csv")[["variante", "delta_M", "ee", "pares+", "p_unilateral"]],
          pd.read_csv(E / "037_hojas_rf" / "comparacion_numerico.csv")[["variante", "delta_M", "ee", "pares+", "p_unilateral"]]]
T = pd.concat(partes, ignore_index=True).sort_values("p_unilateral").reset_index(drop=True)
m = len(T)
T["umbral_BH"] = Q * (T.index + 1) / m
# BH: se rechaza H0 para todos los rangos hasta el mayor i con p(i) <= q*i/m
ok = (T.p_unilateral <= T.umbral_BH)
T["significativa_BH"] = [bool(ok[i:].any()) for i in range(m)]
T["pasa"] = T.significativa_BH & (T.delta_M >= MIN_DELTA)
print(f"Familia de {m} pruebas (q = {Q}); mínimo +{MIN_DELTA}M\n")
print(T.round(4).to_string(index=False))
print(f"\nVariantes que pasan: {int(T.pasa.sum())}")
T.round(4).to_csv(Path(__file__).resolve().parent / "bh_final.csv", index=False)
