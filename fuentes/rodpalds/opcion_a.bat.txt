@echo off
REM ============================================================================
REM  opcion_a.bat - DMEyF 2026: 5015 sin columnas rotas (Finiciomora, fultimo_cierre)
REM   1) 5023  final marzo-junio, 30 semillas (min 20, corte 20:30)   ~50-60 min
REM   2) 6019  archivo para el bot con 12.500 envios
REM ============================================================================
set "PY=py -3.12"
cd /d "%~dp0"
if not exist logs mkdir logs
if exist APURAR.txt echo OJO: existe APURAR.txt - borralo.
echo [%date% %time%] Paso 1: 5023 (log en logs\5023.txt)
%PY% -u 07_modelo_final.py configs\5023_prod_5015_sin_rotas.json > logs\5023.txt 2>&1
if errorlevel 1 (
    echo *** FALLO 5023. Ultimas lineas: ***
    powershell -NoProfile -Command "Get-Content -Path 'logs\5023.txt' -Tail 30"
    pause
    exit /b 1
)
echo [%date% %time%] Paso 2: 6019 (log en logs\6019.txt)
%PY% -u 10_entrega_zulip.py configs\6019_zulip_final_5023.json > logs\6019.txt 2>&1
if errorlevel 1 (
    echo *** FALLO 6019. Ultimas lineas: ***
    powershell -NoProfile -Command "Get-Content -Path 'logs\6019.txt' -Tail 30"
    pause
    exit /b 1
)
echo.
echo [%date% %time%] TERMINADO. Archivo para el bot en exp\6019_zulip_final_5023\zulip
powershell -NoProfile -Command "Get-Content -Path 'logs\5023.txt' | Select-String -Pattern 'Se excluyen|semilla '"
pause
