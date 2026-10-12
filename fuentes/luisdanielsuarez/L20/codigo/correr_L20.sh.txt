#!/bin/bash
# correr_L20.sh — corre el paso 1 y, si termina bien, el paso 2. Opcionalmente apaga la VM al final.
#
# Uso (desde ~/dmeyf, con los dos .py en la misma carpeta):
#     nohup bash correr_L20.sh --apagar > /dev/null 2>&1 &     # corre todo y apaga la VM
#     nohup bash correr_L20.sh           > /dev/null 2>&1 &    # corre todo y la deja encendida
#
# Seguimiento (estos comandos devuelven el prompt):   tail -n 30 L20_todo.log
# Es reanudable: si la VM spot se corta, encenderla y relanzar el mismo comando; cada script
# saltea lo que ya terminó.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
APAGAR=0
[ "$1" = "--apagar" ] && APAGAR=1
BUCKET=gs://luisdsuarez_buckito2026
LOG=L20_todo.log
exec >> "$LOG" 2>&1                       # todo lo que sigue va al log

# Candado: impide lanzar una segunda corrida mientras la primera sigue viva
# (dos procesos sobre el mismo estudio se pisan los núcleos y la RAM, y todo se vuelve lentísimo).
exec 9> /tmp/correr_dmeyf.lock                 # mismo candado para todos los volúmenes
if ! flock -n 9; then
    echo "$(date '+%F %T') YA HAY UNA CORRIDA EN CURSO: esta se cancela"
    exit 1
fi
# además: no arrancar si quedó algún script de CUALQUIER volumen todavía vivo (p. ej. L15)
if pgrep -f "^([^ ]*/)?python[0-9.]* +(\./)?0[123]_[a-z0-9_]*_L[0-9]+\.py" > /dev/null; then
    echo "$(date '+%F %T') HAY OTRO SCRIPT DE UN VOLUMEN ANTERIOR TODAVÍA CORRIENDO: esta corrida se cancela"
    exit 1
fi

mkdir -p exp/L20/codigo
cp "$(readlink -f "$0")" exp/L20/codigo/        # copia del código para reproducibilidad

echo "$(date '+%F %T') === inicio (apagar al final: $APAGAR)"
python 01_preprocesamiento_L20.py
RC=$?
if [ $RC -eq 0 ]; then
    echo "$(date '+%F %T') === paso 1 (preprocesamiento) OK; empieza la etapa 1"
    python 02_etapa1_L20.py
    RC=$?
fi
if [ $RC -eq 0 ]; then
    echo "$(date '+%F %T') === etapa 1 OK; empieza la etapa 2"
    python 03_etapa2_L20.py
    RC=$?
fi
if [ $RC -ne 0 ]; then
    echo "$(date '+%F %T') === algo falló (código $RC): las etapas siguientes NO se corrieron"
fi
echo "$(date '+%F %T') === fin (código $RC)"

# respaldo del log junto al experimento (si el paso 1 falló, igual queda el diagnóstico)
mkdir -p exp/L20
cp "$LOG" exp/L20/
gsutil -q -m rsync -r exp/L20 "$BUCKET/exp/L20"

if [ $APAGAR -eq 1 ]; then
    echo "$(date '+%F %T') apagando la VM"
    sudo shutdown -h now
fi
