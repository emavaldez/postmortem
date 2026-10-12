@echo off
REM ============================================================================
REM  variantes.bat - DMEyF 2026 Primera Competencia
REM  Receta del profesor SOLA (sin ensamble): otras formas razonables de la misma idea
REM   1) 3004  dataset: proceso de muerte con un indicador por producto, sin rankear
REM   2) 3005  dataset: primero rank por mes, despues lags/deltas del ranking (solo informativo:
REM            el orden del profesor es lags primero, que es el de 3003 y 3004)
REM   3) 5105  comparacion en la mitad B: 3002 / 3003 / 3004 / 3005 (30 semillas)
REM   4) 5106  lag2: 3003 sin y con lag2, entrenando con mayo (30 semillas)
REM  No entrena produccion ni genera archivos para Zulip. ~50-60 minutos.
REM ============================================================================

set "PY=py -3.12"

cd /d "%~dp0"
if not exist logs mkdir logs
if not exist data\ds3003_rank_extra.parquet (
    echo ERROR: falta data\ds3003_rank_extra.parquet. Correr antes fe_extra.bat.
    pause
    exit /b 1
)

echo Verificando Python y librerias...
%PY% -c "import sys, lightgbm, pandas, pyarrow, plotly; print('Python', sys.version)" > logs\entorno_variantes.txt 2>&1
if errorlevel 1 (
    echo ERROR: el Python elegido no funciona o le faltan librerias. Detalle:
    type logs\entorno_variantes.txt
    pause
    exit /b 1
)
type logs\entorno_variantes.txt
echo.

echo Inicio: %date% %time% > logs\variantes_tiempos.txt
call :paso 1 "03d_fe_variantes.py configs\3004_fe_flags.json" 3004
call :paso 2 "03d_fe_variantes.py configs\3005_fe_rank_luego_lag.json" 3005
call :paso 3 "11_comparar_pipelines.py configs\5105_comparar_variantes_receta.json" 5105
call :paso 4 "11_comparar_pipelines.py configs\5106_lag2_entrenando_mayo.json" 5106
echo Fin: %date% %time% >> logs\variantes_tiempos.txt

echo.
echo ==== TERMINADO. Revisar logs\variantes_tiempos.txt y los logs de cada paso ====
pause
exit /b

:paso
echo [%date% %time%] Paso %1 de 4: %~2
echo [%date% %time%] Paso %1 de 4 (%3): inicio >> logs\variantes_tiempos.txt
%PY% -u %~2 > logs\%3.txt 2>&1
echo [%date% %time%] Paso %1 de 4 (%3): fin, codigo %errorlevel% >> logs\variantes_tiempos.txt
exit /b
