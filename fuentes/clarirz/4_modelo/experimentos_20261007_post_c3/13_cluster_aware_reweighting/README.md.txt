# CLAW2 — el modelo final

**Qué hice:** es SUPERFINAL otra vez (mismas 2.062 variables, mismos hiperparámetros, 361 rondas, 20 semillas, corte 13.500) con un solo cambio: **cuánto pesa cada BAJA+2 al entrenar**, según a cuál de los cinco grupos del paso 3 pertenece.

La idea vino de mirar a quién perdía SUPERFINAL en junio: 309 de los 401 BAJA+2 que se le escapaban eran de los grupos C2 y C5. Probé tres recetas de pesos, con la regla de que el peso total de los BAJA+2 no cambia (así no estoy cambiando el balance de clases, solo a quién mira más el modelo):

| Receta | Pesos | Mayo (3 semillas, vs SUPERFINAL) | ¿Siguió? |
|---|---|---:|---|
| C25_FOCUSED | C2 ×3, C5 ×2,5, el resto ×1 | −9,9 M | No |
| DIFFICULTY_JUNE | Inverso a lo que se detectaba cada grupo en junio | −12,1 M | No |
| **BALANCED_CAPPED** | Inverso al tamaño del grupo en el train, tope 0,5–4 | **+4,4 M** | **Sí** |

BALANCED_CAPPED después se confirmó en junio: con 5 semillas y con 20. Con 20 semillas pasó de 697 a **718 BAJA+2** detectados a igual corte (+23,10 M ARS), mejorando en las 20. Solo entonces se entrenó agosto.

Pesos efectivos con los que se entrenó el modelo de agosto: C1 0,635 · C2 0,716 · C3 0,949 · C4 1,405 · C5 3,783. Los grupos no entran como variable ni se usan para puntuar agosto.

| Archivo | Qué hace |
|---|---|
| `run_cluster_aware.py` | Todo el pipeline: preflight → mayo → junio 5 semillas → junio 20 semillas → agosto → CSV |
| `cluster_aware_common.py` | Cálculo de pesos, normalización y métricas |
| `plan.json` | Reglas y umbrales, congelados antes de correr |
| `audit_cluster_aware.py` | Sin entrenar: reconstruye el top-13.500 desde los 20 modelos y verifica el hash del CSV |
| `test_cluster_aware.py` | Tests de los pesos con datos sintéticos |

```bash
python run_cluster_aware.py --home $HOME --labels-cluster $HOME/z501/reference_labels.csv --phase all
python audit_cluster_aware.py --home $HOME
```

Salida: `$HOME/c1clusteraware01/stage4_august/delivery/C1CLAW2C065771C9ENS13500.csv`, más `MANIFEST.json` (parámetros, pesos y SHA-256 del CSV) y los 20 `modelo_<semilla>.txt`. El nombre del archivo lo arma el script: `C1CLAW` + 10 caracteres de la identidad de la corrida + `ENS13500`.

Para correrlo sobre una corrida nueva de SUPERFINAL hay que exportar `CLAW2_REPLICA=1` (explicado en el README de `4_modelo/`).

Si alguna etapa intermedia no mejora, el script se detiene y no genera agosto. En la corrida original pasó todo y la auditoría dio `AUDIT_OK`.
