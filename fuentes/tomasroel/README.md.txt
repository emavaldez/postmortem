# DMEyF 2026 — Competencia 1

Objetivo: predicción de clientes BAJA+2 para 202108. Meses disponibles en base de datos: desde 202103 a 202108.

Contenido del repositorio:

| Archivo | Qué es |
|------------------------------------|------------------------------------|
| `8_0_competencia1_gcp_entrega.ipynb` | Notebook único que genera el csv con ids de clients para la entrega |
| `BO_log.txt` | Resultado de la Bayesian Optimization de ese mismo notebook |

## 1. Instrucciones de corrida

Es un solo notebook que hace todo. Se corre de punta a punta, con kernel **R**, de arriba hacia abajo, sin ningún script previo. Está configurado para correr sobra una VM configurada según las instrucciones de los profesores de esta materia.

Pasos que ejecuta:

1.  Baja el dataset `competencia_01_crudo.csv` a `~/buckets/b1/datasets/` si todavía no está ahí.
2.  Preprocesa: clase ternaria, features nuevas, lags y deltas, tendencias y ranking.
3.  Detecta outliers y corre su propia Bayesian Optimization (20 evaluaciones) sobre 202103 + 202104.
4.  Testea en 202106 con 10 semillas.
5.  Entrena sobre los 4 meses (202103 a 202106) con 50 semillas y predice 202108.
6.  Graba las predicciones según los cortes definidos en `PARAM$cortes`.

Todo queda en `~/buckets/b1/outputs/base_080/`:

- `m<corte>/`: una carpeta por corte, con un csv por semilla.
- `ensamble/`: un csv por corte, armado con el promedio de las 50 semillas.

Se corrió en una VM de Google Cloud con 8 vCPU y 62 GB de RAM. La corrida completa tarda unas 7 horas y media.

Si la corrida se corta, se vuelve a correr desde arriba y sigue desde donde quedó.

## 2. Resultado de la BO

Se incluye `BO_log.txt` por si se quiere saltear esa parte. Ese archivo sale de este mismo notebook.

Para usarlo, copiarlo antes de correr a:

```         
~/buckets/b1/outputs/base_080/BO_log.txt
```

El notebook detecta que el log ya tiene las 20 evaluaciones, no vuelve a correr la BO y toma de ahí los mejores hiperparámetros.

## 3. Entrega final

De todos los csv que genera el notebook, la entrega final corresponde a:

```         
ensamble/8_0_competencia1_gcp_ensamble_m12500.csv
```
