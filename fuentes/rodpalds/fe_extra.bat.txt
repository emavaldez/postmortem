@echo off
REM ============================================================================
REM  fe_extra.bat - DMEyF 2026 Primera Competencia
REM   1) 3003  dataset de la receta + 6 variables del proceso de muerte (ds3003)
REM   2) 5104  comparacion en la mitad B: receta (ds3002) contra receta + variables extra (ds3003)
REM  No entrena produccion ni genera archivos para Zulip. ~20-25 minutos.
REM ============================================================================

set "PY=py -3.12"

cd /d "%~dp0"
if not exist logs mkdir logs

echo Verificando Python y librerias...
%PY% -c "import sys, lightgbm, pandas, pyarrow, plotly; print('Python', sys.version)" > logs\entorno_fe_extra.txt 2>&1
if errorlevel 1 (
    echo ERROR: el Python elegido no funciona o le faltan librerias. Detalle:
    type logs\entorno_fe_extra.txt
    pause
    exit /b 1
)
type logs\entorno_fe_extra.txt
echo.

echo Inicio: %date% %time% > logs\fe_extra_tiempos.txt
call :paso 1 "03c_fe_extra.py" 3003
call :paso 2 "11_comparar_pipelines.py configs\5104_comparar_fe_extra.json" 5104
echo Fin: %date% %time% >> logs\fe_extra_tiempos.txt

echo.
echo ==== TERMINADO. Revisar logs\fe_extra_tiempos.txt y los logs de cada paso ====
pause
exit /b

:paso
echo [%date% %time%] Paso %1 de 2: %~2
echo [%date% %time%] Paso %1 de 2 (%3): inicio >> logs\fe_extra_tiempos.txt
%PY% -u %~2 > logs\%3.txt 2>&1
echo [%date% %time%] Paso %1 de 2 (%3): fin, codigo %errorlevel% >> logs\fe_extra_tiempos.txt
exit /b
