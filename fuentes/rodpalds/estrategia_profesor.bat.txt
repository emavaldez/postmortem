@echo off
REM ============================================================================
REM  estrategia_profesor.bat - DMEyF 2026 Primera Competencia  (reanudable)
REM  Todas las indicaciones del profesor (1.1, 1.3, 1.4, 1.7, 2.1, 2.2, 2.3):
REM   1) 3007  dataset ds3007: ccajas_depositos NA en 202105, _zero, lags/deltas 1-2, tend3, avg3, rank
REM   2) 4112  Bayesiana (AUC, lr 0,005, min_data_in_leaf 0...) en marzo+abril 5x70/30  corte dom 13:00
REM   3) 5113  ensamble de las 12 mejores medido en junio (escalado o no) vs prueba 23   corte dom 20:00
REM   4) 5021  ensamble final marzo-junio -> 202108                                   corte lun 07:30
REM   5) 6017  archivos para Zulip de 10.000 a 14.000 envios (de a 500)
REM  Si un paso falla: logs\ERRORES_estrategia.txt. Volver a ejecutar sigue donde quedo.
REM  Para rehacer un paso terminado: borrar logs\ok_<id>.txt.
REM  Para APURAR (hacer solo el minimo y pasar al siguiente paso): crear APURAR.txt en esta carpeta.
REM ============================================================================

set "PY=py -3.12"
set "ERR=logs\ERRORES_estrategia.txt"
set "TIE=logs\estrategia_tiempos.txt"

cd /d "%~dp0"
if not exist logs mkdir logs
if exist "%ERR%" del "%ERR%"
if not exist data\ds1001_base.parquet (
    echo ERROR: falta data\ds1001_base.parquet.
    pause
    exit /b 1
)
if not exist exp\4107_bo_profesor_mar_abr\4107_eleccion.json (
    echo ERROR: falta exp\4107_bo_profesor_mar_abr\4107_eleccion.json.
    pause
    exit /b 1
)

echo Verificando Python y librerias...
%PY% -c "import sys, lightgbm, optuna, pandas, pyarrow, plotly; print('Python', sys.version)" > logs\entorno_estrategia.txt 2>&1
if errorlevel 1 (
    echo ERROR: el Python elegido no funciona o le faltan librerias. Detalle:
    type logs\entorno_estrategia.txt
    pause
    exit /b 1
)
type logs\entorno_estrategia.txt
echo.

if exist APURAR.txt echo OJO: existe APURAR.txt - cada paso hace solo el minimo. Borralo si no queres eso.
echo ===== Ejecucion: %date% %time% ===== >> "%TIE%"
call :paso 1 3007 "03f_fe_profesor.py" ""
call :paso 2 4112 "16_bo_profesor_v2.py configs\4112_bo_profesor_ds3007.json" "3007"
call :paso 3 5113 "18_ensamble_profesor.py configs\5113_eval_ensamble.json" "4112"
call :paso 4 5021 "18_ensamble_profesor.py configs\5021_prod_ensamble.json" "5113"
call :paso 5 6017 "10_entrega_zulip.py configs\6017_zulip_final_5021.json" "5021"
echo Fin: %date% %time% >> "%TIE%"

echo.
if exist "%ERR%" (
    echo ==== HUBO ERRORES. Mandale a Claude el archivo %ERR% ====
    echo Despues de corregir, volve a ejecutar este .bat: sigue donde quedo.
    start "" notepad "%ERR%"
) else (
    if exist logs\5113.txt powershell -NoProfile -Command "Get-Content -Path 'logs\5113.txt' -Tail 30"
    echo ==== TERMINADO SIN ERRORES ====
)
pause
exit /b 0

REM ---------------------------------------------------------------------------
REM :paso  numero  id  "comando"  "ids de los que depende"
REM ---------------------------------------------------------------------------
:paso
if exist logs\ok_%2.txt (
    echo [%date% %time%] Paso %1 de 5 ^(%2^): ya estaba hecho, se saltea
    echo [%date% %time%] Paso %1 de 5 ^(%2^): ya hecho, salteado >> "%TIE%"
    exit /b 0
)
for %%d in (%~4) do (
    if not exist logs\ok_%%d.txt (
        echo [%date% %time%] Paso %1 de 5 ^(%2^): NO se corre, falta terminar %%d
        echo [%date% %time%] Paso %1 de 5 ^(%2^): salteado, falta %%d >> "%TIE%"
        >> "%ERR%" echo ==== Paso %1 ^(%2^) NO SE CORRIO: depende de %%d, que no termino ====
        >> "%ERR%" echo.
        exit /b 1
    )
)
echo [%date% %time%] Paso %1 de 5 ^(%2^): %~3
echo [%date% %time%] Paso %1 de 5 (%2): inicio >> "%TIE%"
%PY% -u %~3 > logs\%2.txt 2>&1
set "RC=%errorlevel%"
echo [%date% %time%] Paso %1 de 5 (%2): fin, codigo %RC% >> "%TIE%"
if "%RC%"=="0" (
    echo ok > logs\ok_%2.txt
    exit /b 0
)
echo     *** FALLO el paso %2. Detalle en %ERR% ***
>> "%ERR%" echo ==== Paso %1 ^(%2^) FALLO con codigo %RC% - %date% %time% ====
>> "%ERR%" echo Comando: py -3.12 %~3
>> "%ERR%" echo Log completo: logs\%2.txt
>> "%ERR%" echo --- ultimas 40 lineas del log ---
powershell -NoProfile -Command "Get-Content -Path 'logs\%2.txt' -Tail 40" >> "%ERR%"
>> "%ERR%" echo.
exit /b 1
