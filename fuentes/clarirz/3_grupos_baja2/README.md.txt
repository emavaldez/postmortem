# 3 — Cinco grupos de clientes que se van

**Qué hice:** quería saber si los BAJA+2 se van todos de la misma manera o hay varias formas de irse. Entrené un Random Forest para distinguir BAJA+2 de clientes fieles, armé un perfil de cada BAJA+2 con las hojas en que cae, y sobre esos perfiles hice KMeans con k=5. Salen cinco grupos (C1 a C5) de los 4.067 BAJA+2 de marzo a junio.

El modelo final (paso 4) usa estos grupos **solo para decidir cuánto pesa cada BAJA+2 al entrenar**. No son una variable y no se usan para predecir agosto.

| Archivo | Qué hace |
|---|---|
| `eda_clusters_profundo.py` | Random Forest (300 árboles, semilla 214363) + perfil de hojas + KMeans k=5 |
| `validar_clusters_estabilidad.py` | Escribe `reference_labels.csv` (cliente, grupo) y después comprueba que los cinco grupos reaparecen cambiando semillas, bootstrap de clientes y árboles |

```bash
python 3_grupos_baja2/validar_clusters_estabilidad.py \
  --data $HOME/c1m1femasiva03/datos/competencia_01.parquet --out $HOME/z501
```

El script escribe `reference_labels.csv` al principio y después sigue con las pruebas de estabilidad (20 semillas de KMeans, bootstrap, otros bosques), que tardan y no hacen falta para la entrega: se puede cortar una vez que apareció el archivo.

`$HOME/z501/reference_labels.csv` debe tener 4.067 filas con estos tamaños: C1 1.280, C2 1.136, C3 857, C4 579, C5 215. El archivo no está en el repo porque tiene IDs de clientes.

Lo que encontré con estos grupos está en el README principal: SUPERFINAL detectaba casi todos los BAJA+2 de C3 y C4 (98%) y menos de la mitad de los de C2 y C5.
