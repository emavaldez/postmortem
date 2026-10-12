@echo off
REM ============================================================================
REM  fe_profesor.bat - DMEyF 2026 (reanudable, mismo formato que estrategia_profesor.bat)
REM  ¿El Feature Engineering del profesor (ds3007) mejora a la prueba 23?
REM   1) 5114  prueba 23 sobre ds3003 vs ds3007 en junio, 20 semillas  (~1 h)
REM   2) 5022  SOLO si R8 adopta ds3007: final marzo-junio, 50 semillas (corte lun 09:00, min 20)
REM   3) 6018  archivos para el bot: 12.000, 12.500 y 13.000 envios
REM  Errores en logs\ERRORES_fe_profesor.txt. Volver a ejecutar sigue donde quedo.
REM ============================================================================
set "PY=py -3.12"
set "ERR=logs\ERRORES_fe_profesor.txt"
set "TIE=logs\fe_profesor_tiempos.txt"
cd /d "%~dp0"
if not exist logs mkdir logs
if exist "%ERR%" del "%ERR%"
if exist APURAR.txt echo OJO: existe APURAR.txt - borralo, este .bat no lo necesita.
for %%f in (data\ds3003_rank_extra.parquet data\ds3007_profesor.parquet exp\4107_bo_profesor_mar_abr\4107_eleccion.json) do (
    if not exist %%f (
        echo ERROR: falta %%f
        pause
        exit /b 1
    )
)
echo ===== Ejecucion: %date% %time% ===== >> "%TIE%"
call :paso 1 5114 "19_eval_dataset.py configs\5114_eval_dataset.json" ""
if not exist exp\5114_eval_dataset\5114_ADOPTAR.txt (
    echo.
    if exist logs\ok_5114.txt (
        echo ==== R8: quedarse con 5015. No hace falta entrenar nada mas ni reenviar. ====
        powershell -NoProfile -Command "Get-Content -Path 'logs\5114.txt' -Tail 25"
    )
    goto fin
)
call :paso 2 5022 "07_modelo_final.py configs\5022_prod_p23_ds3007.json" "5114"
call :paso 3 6018 "10_entrega_zulip.py configs\6018_zulip_final_5022.json" "5022"
:fin
echo Fin: %date% %time% >> "%TIE%"
echo.
if exist "%ERR%" (
    echo ==== HUBO ERRORES. Mandale a Claude el archivo %ERR% ====
    start "" notepad "%ERR%"
) else (
    if exist logs\5114.txt powershell -NoProfile -Command "Get-Content -Path 'logs\5114.txt' -Tail 25"
    echo ==== TERMINADO SIN ERRORES ====
)
pause
exit /b 0

:paso
if exist logs\ok_%2.txt (
    echo [%date% %time%] Paso %1 ^(%2^): ya estaba hecho, se saltea
    exit /b 0
)
for %%d in (%~4) do (
    if not exist logs\ok_%%d.txt (
        echo [%date% %time%] Paso %1 ^(%2^): NO se corre, falta terminar %%d
        >> "%ERR%" echo ==== Paso %1 ^(%2^) NO SE CORRIO: depende de %%d ====
        exit /b 1
    )
)
echo [%date% %time%] Paso %1 ^(%2^): %~3
echo [%date% %time%] Paso %1 (%2): inicio >> "%TIE%"
%PY% -u %~3 > logs\%2.txt 2>&1
set "RC=%errorlevel%"
echo [%date% %time%] Paso %1 (%2): fin, codigo %RC% >> "%TIE%"
if "%RC%"=="0" (
    echo ok > logs\ok_%2.txt
    exit /b 0
)
echo     *** FALLO el paso %2. Detalle en %ERR% ***
>> "%ERR%" echo ==== Paso %1 ^(%2^) FALLO con codigo %RC% - %date% %time% ====
>> "%ERR%" echo Comando: py -3.12 %~3
>> "%ERR%" echo --- ultimas 40 lineas del log ---
powershell -NoProfile -Command "Get-Content -Path 'logs\%2.txt' -Tail 40" >> "%ERR%"
exit /b 1
