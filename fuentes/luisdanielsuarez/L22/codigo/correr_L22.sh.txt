#!/bin/bash
# correr_L22.sh — entrena modelos con 03-06 (una semilla tras otra) y guarda la predicción de 08 de cada uno.
#
# Uso (desde ~/dmeyf, con 01_entrenar_08_L22.py y comun_L22.py en la misma carpeta):
#     nohup bash correr_L22.sh > /dev/null 2>&1 &                                  # VM 1: semillas 0 a 199, volumen L22
#     nohup bash correr_L22.sh --volumen L22b --desde 200 > /dev/null 2>&1 &       # VM 2: semillas 200 a 399, volumen L22b
# Opciones: cualquier argumento de 01_entrenar_08_L22.py (--volumen, --desde, --n_semillas, --dataset, --hiperparametros)
#           y --apagar (apaga la VM al terminar; necesita sudo).
#
# Seguimiento (devuelve el prompt):   tail -n 30 <volumen>_todo.log     (L22_todo.log o L22b_todo.log)
# Se puede interrumpir cuando quieras (pkill -f 01_entrenar_08_L22.py): lo ya guardado queda, y se puede
# ensamblar con: python 02_ensamblar_08_L22.py
# Es reanudable: si la VM spot se corta, encenderla y relanzar el mismo comando.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
VOL=L22
APAGAR=0
ARGS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --apagar)  APAGAR=1 ;;
        --volumen) VOL="$2"; ARGS+=("$1" "$2"); shift ;;
        *)         ARGS+=("$1") ;;
    esac
    shift
done
BUCKET=gs://luisdsuarez_buckito2026
LOG=${VOL}_todo.log
exec >> "$LOG" 2>&1                       # todo lo que sigue va al log

# Candado: impide lanzar una segunda corrida mientras la primera sigue viva EN ESTA VM
# (dos procesos de LightGBM se pisan los núcleos y la RAM, y todo se vuelve lentísimo).
exec 9> /tmp/correr_dmeyf.lock
if ! flock -n 9; then
    echo "$(date '+%F %T') YA HAY UNA CORRIDA EN CURSO: esta se cancela"
    exit 1
fi
# además: no arrancar si quedó algún script de CUALQUIER volumen todavía vivo
if pgrep -f "^([^ ]*/)?python[0-9.]* +(\./)?0[123]_[a-z0-9_]*_L[0-9]+[a-z]?\.py" > /dev/null; then
    echo "$(date '+%F %T') HAY OTRO SCRIPT DE UN VOLUMEN ANTERIOR TODAVÍA CORRIENDO: esta corrida se cancela"
    exit 1
fi

mkdir -p exp/$VOL/codigo
cp "$(readlink -f "$0")" exp/$VOL/codigo/        # copia del código para reproducibilidad

echo "$(date '+%F %T') === inicio: volumen $VOL, argumentos: ${ARGS[*]} (apagar al final: $APAGAR)"
python 01_entrenar_08_L22.py "${ARGS[@]}"
RC=$?
echo "$(date '+%F %T') === fin (código $RC)"

# respaldo del log junto al experimento
cp "$LOG" exp/$VOL/
gsutil -q -m rsync -r exp/$VOL "$BUCKET/exp/$VOL"

if [ $APAGAR -eq 1 ]; then
    echo "$(date '+%F %T') apagando la VM"
    sudo shutdown -h now
fi
