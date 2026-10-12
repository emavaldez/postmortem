@echo off
REM ============================================================================
REM  tarde.bat - DMEyF 2026 Primera Competencia
REM  1) 4103: Bayesiana fuera de tiempo con rangos ampliados
REM  2) 5101: curvas de ganancia en la mitad B de junio (z601, 4102, 4103 y combinaciones)
REM  3) 5006: produccion para agosto con lo que elija la 4103
REM  Si un paso falla, sigue con el siguiente. Cada paso deja su log en logs\
REM ============================================================================

set "PY=py -3.12"

cd /d "%~dp0"
if not exist logs mkdir logs

echo Verificando Python y librerias...
%PY% -c "import sys, lightgbm, optuna, pandas, pyarrow, plotly; print('Python', sys.version)" > logs\entorno_tarde.txt 2>&1
if errorlevel 1 (
    echo ERROR: el Python elegido no funciona o le faltan librerias. Detalle:
    type logs\entorno_tarde.txt
    pause
    exit /b 1
)
type logs\entorno_tarde.txt
echo.

echo Inicio: %date% %time% > logs\tarde_tiempos.txt
call :paso 1 "08_bo_fuera_de_tiempo.py configs\4103_bo_ampliada.json" 4103
call :paso 2 "09_curva_mitad_b.py" 5101
call :paso 3 "07_modelo_final.py configs\5006_prod_eleccion_4103.json" 5006
echo Fin: %date% %time% >> logs\tarde_tiempos.txt

echo.
echo ==== TERMINADO. Revisar logs\tarde_tiempos.txt y los logs de cada paso ====
pause
exit /b

:paso
echo [%date% %time%] Paso %1 de 3: %~2
echo [%date% %time%] Paso %1 de 3 (%3): inicio >> logs\tarde_tiempos.txt
%PY% -u %~2 > logs\%3.txt 2>&1
echo [%date% %time%] Paso %1 de 3 (%3): fin, codigo %errorlevel% >> logs\tarde_tiempos.txt
exit /b
