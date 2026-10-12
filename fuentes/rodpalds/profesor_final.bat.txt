@echo off
REM ============================================================================
REM  profesor_final.bat - DMEyF 2026 Primera Competencia
REM  Indicaciones del profesor (reunion del 9/10):
REM   0) 5107  sirve marzo: abril solo contra marzo + abril, misma receta e hiperparametros (~20 min)
REM   1) 4107  Bayesiana entrenando con marzo + abril (toda la informacion, aunque haya NA),
REM            rangos del profesor, 50 pruebas, confirmacion con 20 semillas en la mitad B
REM   2) 5015  modelo final entrenando con marzo a junio, 50 semillas
REM   3) 6011  archivos para Zulip: 11.000 a 13.500 envios
REM  ~4 h 20 min. Si un paso falla, sigue con el siguiente. Logs en logs\
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
%PY% -c "import sys, lightgbm, optuna, pandas, pyarrow, plotly; print('Python', sys.version)" > logs\entorno_profesor_final.txt 2>&1
if errorlevel 1 (
    echo ERROR: el Python elegido no funciona o le faltan librerias. Detalle:
    type logs\entorno_profesor_final.txt
    pause
    exit /b 1
)
type logs\entorno_profesor_final.txt
echo.

echo Inicio: %date% %time% > logs\profesor_final_tiempos.txt
call :paso 0 "11_comparar_pipelines.py configs\5107_comparar_marzo.json" 5107
call :paso 1 "08_bo_fuera_de_tiempo.py configs\4107_bo_profesor_mar_abr.json" 4107
call :paso 2 "07_modelo_final.py configs\5015_prod_profesor_mar_jun.json" 5015
call :paso 3 "10_entrega_zulip.py configs\6011_zulip_final_5015.json" 6011
echo Fin: %date% %time% >> logs\profesor_final_tiempos.txt

echo.
echo ==== TERMINADO. Revisar logs\profesor_final_tiempos.txt y los logs de cada paso ====
pause
exit /b

:paso
echo [%date% %time%] Paso %1 de 3: %~2
echo [%date% %time%] Paso %1 de 3 (%3): inicio >> logs\profesor_final_tiempos.txt
%PY% -u %~2 > logs\%3.txt 2>&1
echo [%date% %time%] Paso %1 de 3 (%3): fin, codigo %errorlevel% >> logs\profesor_final_tiempos.txt
exit /b
