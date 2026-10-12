# Postmortem de la Primera Competencia — DMEyF 2026 (UBA)

Una lectura descriptiva de las entregas de la Primera Competencia de la materia: qué hizo cada alumno para predecir las bajas
de clientes (clase BAJA+2) de 202108, con su código, sus explicaciones y una descripción objetiva de cada paso.

**Página:** https://emavaldez.github.io/postmortem/

## Qué hay

- **Resumen general** de lo que se hizo: lenguajes, modelos, técnicas, semillas, meses de entrenamiento.
- **Una página por entrega**: resumen, ficha, pasos del camino que produce la predicción, los textos que escribió el alumno
  y el código, con anotaciones agregadas donde casi no había comentarios.
- **Comparador**: elegir dos entregas y ver sus fichas y sus códigos en paralelo.
- **Técnicas**: matriz de quién usó qué, con enlaces a la línea del código donde se ve.
- **Reproducibilidad**: qué trae cada repositorio para volver a correrlo.
- **Buscador** en el código principal de todas las entregas, y un **glosario**.

No hay puntajes, posiciones ni valoraciones: las descripciones dicen lo que el código hace.

## Cómo se hizo

1. Se tomaron los links a GitHub que cada alumno posteó como entrega y se clonó cada repositorio (todos públicos) en el commit
   vigente al momento de la descarga.
2. `tools/inventario.py` y `tools/fuentes.py` arman una copia en texto plano de cada entrega (los notebooks, celda por celda).
3. Un lector automático describe cada entrega siguiendo `tools/INSTRUCCIONES_LECTOR.md`; una segunda pasada automática
   contrasta contra el código los datos principales de cada ficha y una muestra de las anotaciones, y las diferencias se
   corrigen. `tools/validar.py` controla la forma y rechaza palabras de valoración.
4. `tools/generar.py` arma el sitio estático.

Las lecturas son automáticas (hechas con asistencia de IA) y pueden contener errores.

## Para agentes

Todo el contenido está también en formatos legibles sin navegador:

| Qué | Dónde |
|---|---|
| Guía e índice en texto plano | `llms.txt` |
| Índice de entregas | `data/index.json` |
| Una entrega completa (ficha, pasos, archivos, anotaciones) | `data/entregas/<slug>.json` |
| Una entrega en Markdown, con el código principal anotado | `md/<slug>.md` |
| Cada archivo en texto plano | `fuentes/<slug>/<ruta>.txt` |
| Archivos principales con las anotaciones como comentarios | `comentado/<slug>/<ruta>.txt` |
| Técnicas y matriz | `data/tecnicas.json`, `data/matriz.csv` |
| Líneas del código principal, para buscar | `data/busqueda.json` |

Los números de línea se refieren siempre a los archivos de `fuentes/`.

## Correcciones y retiro de una entrega

El código y los textos de cada entrega pertenecen a sus autores y se muestran con enlace a su repositorio original. Si sos
autor de una entrega y querés corregir una descripción o que se retire tu código de esta página, abrí un
[issue](https://github.com/emavaldez/postmortem/issues).

## Verla en tu máquina

```bash
python3 -m http.server 8000
```

y abrir http://localhost:8000. El comparador y el buscador necesitan un servidor web; el resto se puede abrir como archivo.
