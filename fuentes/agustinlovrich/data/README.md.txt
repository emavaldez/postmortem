# data/

Acá va el **dataset crudo de la competencia**. No se versiona en GitHub (es el dato de la
cátedra y es grande).

## Qué poner acá

- `competencia_01_crudo.csv`: el crudo de la competencia 01 (foto_mes 202103 a 202108, con
  `numero_de_cliente`, `foto_mes` y las ~152 variables del dataset).

El script lo toma vía la variable de entorno `DMEYF_CRUDO`:

```bash
DMEYF_CRUDO=data/competencia_01_crudo.csv ... Rscript ../run_rank_prestamos_junbo_hist.R
```

## Requisitos del crudo

- Deben estar los meses `202103, 202104, 202105, 202106, 202107, 202108` (202107 hace falta para
  los retrovisores de 202108 y para la clase de 202106).
- Todas las columnas numéricas (salvo `clase_ternaria` si ya viene calculada). Si no trae
  `clase_ternaria`, el script la calcula.
