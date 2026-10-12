# Q0 — Reproducir C3 y probar una corrección de datos

**Qué hice:** `ccajas_depositos` está toda en cero en mayo de 2021 (dato roto, no comportamiento). Acá primero reproduzco exacto los 20 modelos de C3 (entrenados con marzo y abril) y después vuelvo a puntuar junio con ese mes marcado como faltante antes de construir la historia, para ver si cambia la ganancia.

No entrena nada nuevo para la entrega: sirve de control de que el código reproduce C3 bit a bit (el *canary* de la semilla 17 tiene que dar igual que la corrida original) y deja los 20 modelos congelados que usa B1.

```bash
python run_q0.py --preflight   # solo lectura: verifica dataset, paquete y banco
python run_q0.py --prepare
python run_q0.py --canary      # semilla 17; escribe CANARY_OK.json si reproduce C3
python run_q0.py --execute     # las 20 semillas
```

Salida: `$HOME/c1q0ccajas06/` con `LISTO.json`.
