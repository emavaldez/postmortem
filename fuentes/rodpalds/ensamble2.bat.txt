@echo off
REM ============================================================================
REM  ensamble2.bat - DMEyF 2026 Primera Competencia (no entrena nada, ~1 minuto)
REM   1) 5202  ensamble: promedio de rankings de 5005 (actual) + 5011 (receta del profesor)
REM   2) 6008  archivos para Zulip del ensamble: 11.500 a 13.000 envios
REM ============================================================================

set "PY=py -3.12"

cd /d "%~dp0"
if not exist logs mkdir logs
if not exist 12_ensamble.py (
    echo ERROR: falta 12_ensamble.py. Descomprimir antes ensamble_dmeyf.zip en esta carpeta.
    pause
    exit /b 1
)

echo Inicio: %date% %time% > logs\ensamble2_tiempos.txt
call :paso 1 "12_ensamble.py configs\5202_ensamble_5005_5011.json" 5202
call :paso 2 "10_entrega_zulip.py configs\6008_zulip_final_ensamble_5202.json" 6008
echo Fin: %date% %time% >> logs\ensamble2_tiempos.txt

echo.
type logs\6008.txt
echo.
echo ==== TERMINADO. Revisar logs\ensamble2_tiempos.txt ====
pause
exit /b

:paso
echo [%date% %time%] Paso %1 de 2: %~2
echo [%date% %time%] Paso %1 de 2 (%3): inicio >> logs\ensamble2_tiempos.txt
%PY% -u %~2 > logs\%3.txt 2>&1
echo [%date% %time%] Paso %1 de 2 (%3): fin, codigo %errorlevel% >> logs\ensamble2_tiempos.txt
exit /b
