@echo off
REM ============================================================================
REM  final_limpio.bat - DMEyF 2026 Primera Competencia  (reanudable)
REM   1) 5109  prueba 23: min_data_in_leaf 20.248 vs 10.124 y 400-1.100 arboles
REM   2) 7001  aplica R3 y escribe la config de 5110                (necesita 5109)
REM   3) 4109  Bayesiana limpia, rangos del profesor, solo mitad A   (independiente)
REM   4) 5110  4109 contra la prueba 23 en la mitad B                (necesita 7001 y 4109)
REM   5) 7002  aplica R4 y R5 y escribe las configs del final        (necesita 5110)
REM   6) 5018  modelo final marzo-junio, 50 semillas                 (necesita 7002)
REM   7) 6014  archivos para Zulip                                   (necesita 5018)
REM
REM  COMO FUNCIONA:
REM  - Cada paso terminado deja logs\ok_<id>.txt. Si volves a ejecutar el .bat, los pasos
REM    terminados se saltean y sigue donde quedo. La Bayesiana (4109) retoma sus pruebas.
REM  - Si un paso falla, se anota en logs\ERRORES_final_limpio.txt (paso, archivo de log y
REM    ultimas 40 lineas del error) y el lote SIGUE con los pasos que no dependen de el.
REM  - Al final, si hubo errores, se abre ese archivo en el Bloc de notas.
REM  - Para rehacer un paso ya terminado: borrar su logs\ok_<id>.txt y volver a ejecutar.
REM ============================================================================

set "PY=py -3.12"
set "ERR=logs\ERRORES_final_limpio.txt"
set "TIE=logs\final_limpio_tiempos.txt"

cd /d "%~dp0"
if not exist logs mkdir logs
if exist "%ERR%" del "%ERR%"
if not exist exp\4107_bo_profesor_mar_abr\4107_eleccion.json (
    echo ERROR: falta exp\4107_bo_profesor_mar_abr\4107_eleccion.json.
    pause
    exit /b 1
)

echo Verificando Python y librerias...
%PY% -c "import sys, lightgbm, optuna, pandas, pyarrow, plotly; print('Python', sys.version)" > logs\entorno_final_limpio.txt 2>&1
if errorlevel 1 (
    echo ERROR: el Python elegido no funciona o le faltan librerias. Detalle:
    type logs\entorno_final_limpio.txt
    pause
    exit /b 1
)
type logs\entorno_final_limpio.txt
echo.

echo ===== Ejecucion: %date% %time% ===== >> "%TIE%"
call :paso 1 5109 "11_comparar_pipelines.py configs\5109_comparar_arboles_min_data.json" ""
call :paso 2 7001 "13_decidir.py p23" "5109"
call :paso 3 4109 "08_bo_fuera_de_tiempo.py configs\4109_bo_limpia_profesor.json" ""
call :paso 4 5110 "11_comparar_pipelines.py configs\5110_comparar_bo4109.json" "7001 4109"
call :paso 5 7002 "13_decidir.py final" "5110"
call :paso 6 5018 "07_modelo_final.py configs\5018_prod_final.json" "7002"
call :paso 7 6014 "10_entrega_zulip.py configs\6014_zulip_final_5018.json" "5018"
echo Fin: %date% %time% >> "%TIE%"

echo.
if exist "%ERR%" (
    echo ==== HUBO ERRORES. Mandale a Claude el archivo %ERR% ====
    echo Despues de corregir, volve a ejecutar este .bat: sigue donde quedo.
    start "" notepad "%ERR%"
) else (
    if exist logs\7002.txt type logs\7002.txt
    echo ==== TERMINADO SIN ERRORES ====
)
pause
exit /b 0

REM ---------------------------------------------------------------------------
REM :paso  numero  id  "comando"  "ids de los que depende"
REM ---------------------------------------------------------------------------
:paso
if exist logs\ok_%2.txt (
    echo [%date% %time%] Paso %1 de 7 ^(%2^): ya estaba hecho, se saltea
    echo [%date% %time%] Paso %1 de 7 ^(%2^): ya hecho, salteado >> "%TIE%"
    exit /b 0
)
for %%d in (%~4) do (
    if not exist logs\ok_%%d.txt (
        echo [%date% %time%] Paso %1 de 7 ^(%2^): NO se corre, falta terminar %%d
        echo [%date% %time%] Paso %1 de 7 ^(%2^): salteado, falta %%d >> "%TIE%"
        >> "%ERR%" echo ==== Paso %1 ^(%2^) NO SE CORRIO: depende de %%d, que no termino ====
        >> "%ERR%" echo.
        exit /b 1
    )
)
echo [%date% %time%] Paso %1 de 7 ^(%2^): %~3
echo [%date% %time%] Paso %1 de 7 (%2): inicio >> "%TIE%"
%PY% -u %~3 > logs\%2.txt 2>&1
set "RC=%errorlevel%"
echo [%date% %time%] Paso %1 de 7 (%2): fin, codigo %RC% >> "%TIE%"
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
