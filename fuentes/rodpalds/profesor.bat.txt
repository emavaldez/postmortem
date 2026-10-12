@echo off
REM ============================================================================
REM  profesor.bat - DMEyF 2026 Primera Competencia
REM  Receta del profesor, en orden:
REM   1) 2002  diagnostico de NA / ceros / negativos / positivos
REM   2) 3002  lags y deltas 1 y 2 + ranking de todas las variables (cero fijo)
REM   3) 4104  Bayesiana fuera de tiempo sobre el dataset rankeado (1 semilla)
REM   4) 5102  comparacion: pipeline actual contra receta del profesor (mitad B de junio)
REM   5) 5008  produccion de la receta del profesor (20 semillas)
REM   6) 6003  archivos finales para Zulip: cortes 9.000 a 14.000
REM   7) 6004  20 archivos (uno por semilla) para Zulip
REM  Si un paso falla, sigue con el siguiente. Cada paso deja su log en logs\
REM ============================================================================

set "PY=py -3.12"

cd /d "%~dp0"
if not exist logs mkdir logs

echo Verificando Python y librerias...
%PY% -c "import sys, lightgbm, optuna, pandas, pyarrow, plotly; print('Python', sys.version)" > logs\entorno_profesor.txt 2>&1
if errorlevel 1 (
    echo ERROR: el Python elegido no funciona o le faltan librerias. Detalle:
    type logs\entorno_profesor.txt
    pause
    exit /b 1
)
type logs\entorno_profesor.txt
echo.

echo Inicio: %date% %time% > logs\profesor_tiempos.txt
call :paso 1 "02b_diagnostico_ceros_na.py" 2002
call :paso 2 "03b_fe_rank_total.py" 3002
call :paso 3 "08_bo_fuera_de_tiempo.py configs\4104_bo_rank_total.json" 4104
call :paso 4 "11_comparar_pipelines.py" 5102
call :paso 5 "07_modelo_final.py configs\5008_prod_rank_total.json" 5008
call :paso 6 "10_entrega_zulip.py configs\6003_zulip_final_rank.json" 6003
call :paso 7 "10_entrega_zulip.py configs\6004_zulip_semillas_rank.json" 6004
echo Fin: %date% %time% >> logs\profesor_tiempos.txt

echo.
echo ==== TERMINADO. Revisar logs\profesor_tiempos.txt y los logs de cada paso ====
pause
exit /b

:paso
echo [%date% %time%] Paso %1 de 7: %~2
echo [%date% %time%] Paso %1 de 7 (%3): inicio >> logs\profesor_tiempos.txt
%PY% -u %~2 > logs\%3.txt 2>&1
echo [%date% %time%] Paso %1 de 7 (%3): fin, codigo %errorlevel% >> logs\profesor_tiempos.txt
exit /b
