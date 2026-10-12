@echo off
REM ============================================================================
REM  receta_final.bat - DMEyF 2026 Primera Competencia
REM  Receta del profesor completa, SIN ensamble, sobre el dataset ganador de 5105 (ds3003):
REM   1) 4106  Bayesiana liviana: 40 pruebas, 1 semilla, confirmacion con 20 semillas
REM   2) 5013  produccion: lag1, lag2, delta1, delta2 + proceso de muerte, 50 semillas
REM   3) 6009  archivos para Zulip: 11.000 a 13.500 envios
REM  ~1 h 30 min. Si un paso falla, sigue con el siguiente. Logs en logs\
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
%PY% -c "import sys, lightgbm, optuna, pandas, pyarrow, plotly; print('Python', sys.version)" > logs\entorno_receta_final.txt 2>&1
if errorlevel 1 (
    echo ERROR: el Python elegido no funciona o le faltan librerias. Detalle:
    type logs\entorno_receta_final.txt
    pause
    exit /b 1
)
type logs\entorno_receta_final.txt
echo.

echo Inicio: %date% %time% > logs\receta_final_tiempos.txt
call :paso 1 "08_bo_fuera_de_tiempo.py configs\4106_bo_receta_muerte.json" 4106
call :paso 2 "07_modelo_final.py configs\5013_prod_receta_muerte_lag2.json" 5013
call :paso 3 "10_entrega_zulip.py configs\6009_zulip_final_5013.json" 6009
echo Fin: %date% %time% >> logs\receta_final_tiempos.txt

echo.
echo ==== TERMINADO. Revisar logs\receta_final_tiempos.txt y los logs de cada paso ====
pause
exit /b

:paso
echo [%date% %time%] Paso %1 de 3: %~2
echo [%date% %time%] Paso %1 de 3 (%3): inicio >> logs\receta_final_tiempos.txt
%PY% -u %~2 > logs\%3.txt 2>&1
echo [%date% %time%] Paso %1 de 3 (%3): fin, codigo %errorlevel% >> logs\receta_final_tiempos.txt
exit /b
