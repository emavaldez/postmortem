# 1 — Dataset con clase

**Qué hice:** del CSV crudo de la cátedra armé la clase `clase_ternaria` (CONTINUA, BAJA+1, BAJA+2) mirando si el cliente aparece uno y dos meses después, y guardé todo en un Parquet para que los pasos siguientes lo lean rápido.

Script: [`preparar_competencia.py`](preparar_competencia.py) (DuckDB). Si no encuentra el CSV, lo descarga de la URL de la competencia.

```bash
mkdir -p $HOME/c1m1femasiva03/datos
cp /RUTA/competencia_01_crudo.csv $HOME/c1m1femasiva03/datos/
python 1_dataset/preparar_competencia.py --workdir $HOME/c1m1femasiva03/datos
sha256sum $HOME/c1m1femasiva03/datos/competencia_01.parquet
```

Los scripts del paso 4 comprueban que ese Parquet tenga SHA-256
`59231e670a1342ad6f689ad7edc7ece047fc9f7115c6d7845e6c72fa3bbd95bb` (983.061 filas, 155 columnas) y se detienen si no coincide.
