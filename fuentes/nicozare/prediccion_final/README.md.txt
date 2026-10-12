# Archivo final

`prediccion_final.csv`: 11.500 `numero_de_cliente`, sin encabezado, uno por
línea. Es la lista de clientes a los que conviene ofrecerles una acción de
retención.

SHA-256:

```
6c3229728b7fb353dd46338d39d277d88e9b95c67247a70b2450e4dd8d48225a
```

Al correr `scripts/03_generar_submission.py` (ver el README de la raíz), el
archivo `submissions/submission_promedio.csv` que genera debe dar este mismo
hash:

```bash
shasum -a 256 submissions/submission_promedio.csv
```

Si da un hash distinto, algo cambió respecto a la corrida original (otra
versión del dataset crudo, otra versión de LightGBM, etc.).
