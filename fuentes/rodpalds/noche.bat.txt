@echo off
REM ============================================================================
REM  noche.bat - DMEyF 2026 Primera Competencia
REM  Corre en orden: simulaciones 5001-5002, produccion 5003-5004,
REM  Bayesiana fuera de tiempo 4102 y produccion con lo que elija (5005).
REM  Si un paso falla, sigue con el siguiente. Cada paso deja su log en logs\
REM ============================================================================

REM ---- Python a usar. "py -3.12" elige la version 3.12 aunque haya otras instaladas.
REM ---- Si no funciona, reemplazalo por la ruta completa, por ejemplo:
REM ---- set "PY=C:\Users\rpalpa\AppData\Local\Programs\Python\Python312\python.exe"
set "PY=py -3.12"

cd /d "%~dp0"
if not exist logs mkdir logs

REM ---- Control previo: version de Python y librerias. Si falla, no arranca nada.
echo Verificando Python y librerias...
%PY% -c "import sys, lightgbm, optuna, pandas, pyarrow, plotly; print('Python', sys.version); print('lightgbm', lightgbm.__version__, '| optuna', optuna.__version__, '| pandas', pandas.__version__)" > logs\entorno.txt 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: el Python elegido no funciona o le faltan librerias. Detalle:
    type logs\entorno.txt
    echo.
    echo Corregir la linea "set PY=" al principio de este archivo y volver a ejecutarlo.
    pause
    exit /b 1
)
type logs\entorno.txt
echo.

echo Inicio: %date% %time% > logs\noche_tiempos.txt
call :paso 1 "07_modelo_final.py configs\5001_sim_z601_p95.json" 5001
call :paso 2 "07_modelo_final.py configs\5002_sim_z601_todas.json" 5002
call :paso 3 "07_modelo_final.py configs\5003_prod_z601_todas.json" 5003
call :paso 4 "07_modelo_final.py configs\5004_prod_z601_p95.json" 5004
call :paso 5 "08_bo_fuera_de_tiempo.py" 4102
call :paso 6 "07_modelo_final.py configs\5005_prod_eleccion_4102.json" 5005
echo Fin: %date% %time% >> logs\noche_tiempos.txt

echo.
echo ==== TERMINADO. Revisar logs\noche_tiempos.txt y los logs de cada paso ====
pause
exit /b

:paso
echo [%date% %time%] Paso %1 de 6: %~2
echo [%date% %time%] Paso %1 de 6 (%3): inicio >> logs\noche_tiempos.txt
%PY% -u %~2 > logs\%3.txt 2>&1
echo [%date% %time%] Paso %1 de 6 (%3): fin, codigo %errorlevel% >> logs\noche_tiempos.txt
exit /b
