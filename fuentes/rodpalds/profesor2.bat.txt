@echo off
REM ============================================================================
REM  profesor2.bat - DMEyF 2026 Primera Competencia
REM  Receta del profesor, version mejorada (SIN lag2, que en abril esta vacio):
REM   1) 4105  Bayesiana ampliada: 150 pruebas, 7 hiperparametros, confirmacion con 20 semillas
REM   2) 5103  comparacion en la mitad B: actual vs receta 4104 vs receta 4105 (30 semillas)
REM   3) 5011  produccion de la receta con la eleccion de 4105 (50 semillas)
REM   4) 6007  archivos para Zulip de 5011: 11.500 a 13.000 envios
REM  Si un paso falla, sigue con el siguiente. Cada paso deja su log en logs\
REM  Se puede cortar y volver a lanzar: la 4105 se reanuda (ver README).
REM ============================================================================

set "PY=py -3.12"

cd /d "%~dp0"
if not exist logs mkdir logs

echo Verificando Python y librerias...
%PY% -c "import sys, lightgbm, optuna, pandas, pyarrow, plotly; print('Python', sys.version)" > logs\entorno_profesor2.txt 2>&1
if errorlevel 1 (
    echo ERROR: el Python elegido no funciona o le faltan librerias. Detalle:
    type logs\entorno_profesor2.txt
    pause
    exit /b 1
)
type logs\entorno_profesor2.txt
echo.

echo Inicio: %date% %time% > logs\profesor2_tiempos.txt
call :paso 1 "08_bo_fuera_de_tiempo.py configs\4105_bo_rank_ampliada.json" 4105
call :paso 2 "11_comparar_pipelines.py configs\5103_comparar_bo4105.json" 5103
call :paso 3 "07_modelo_final.py configs\5011_prod_rank_bo4105.json" 5011
call :paso 4 "10_entrega_zulip.py configs\6007_zulip_final_5011.json" 6007
echo Fin: %date% %time% >> logs\profesor2_tiempos.txt

echo.
echo ==== TERMINADO. Revisar logs\profesor2_tiempos.txt y los logs de cada paso ====
pause
exit /b

:paso
echo [%date% %time%] Paso %1 de 4: %~2
echo [%date% %time%] Paso %1 de 4 (%3): inicio >> logs\profesor2_tiempos.txt
%PY% -u %~2 > logs\%3.txt 2>&1
echo [%date% %time%] Paso %1 de 4 (%3): fin, codigo %errorlevel% >> logs\profesor2_tiempos.txt
exit /b
