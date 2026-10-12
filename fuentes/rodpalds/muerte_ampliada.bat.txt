@echo off
REM ============================================================================
REM  muerte_ampliada.bat - DMEyF 2026 Primera Competencia
REM   1) 3006  dataset: receta + proceso de muerte ampliado (34 variables nuevas en total)
REM   2) 5108  comparacion en la mitad B: ds3003 contra ds3006 (train marzo + abril, 30 semillas)
REM   3) 5016  modelo final con ds3006 (train marzo a junio, 50 semillas)
REM   4) 6012  archivos para Zulip: 11.000 a 13.500 envios
REM   5) 4108  Bayesiana sobre ds3006 (rangos del profesor, train marzo + abril, 50 pruebas)
REM   6) 5017  modelo final con los hiperparametros de 4108 (marzo a junio, 50 semillas)
REM   7) 6013  archivos para Zulip de 5017
REM  ~8 horas. Si un paso falla, sigue con el siguiente. Logs en logs\
REM ============================================================================

set "PY=py -3.12"

cd /d "%~dp0"
if not exist logs mkdir logs
if not exist exp\4107_bo_profesor_mar_abr\4107_eleccion.json (
    echo ERROR: falta exp\4107_bo_profesor_mar_abr\4107_eleccion.json. Correr antes profesor_final.bat.
    pause
    exit /b 1
)

echo Verificando Python y librerias...
%PY% -c "import sys, lightgbm, pandas, pyarrow, plotly; print('Python', sys.version)" > logs\entorno_muerte_ampliada.txt 2>&1
if errorlevel 1 (
    echo ERROR: el Python elegido no funciona o le faltan librerias. Detalle:
    type logs\entorno_muerte_ampliada.txt
    pause
    exit /b 1
)
type logs\entorno_muerte_ampliada.txt
echo.

echo Inicio: %date% %time% > logs\muerte_ampliada_tiempos.txt
call :paso 1 "03e_fe_muerte_ampliada.py" 3006
call :paso 2 "11_comparar_pipelines.py configs\5108_comparar_muerte_ampliada.json" 5108
call :paso 3 "07_modelo_final.py configs\5016_prod_muerte_ampliada.json" 5016
call :paso 4 "10_entrega_zulip.py configs\6012_zulip_final_5016.json" 6012
call :paso 5 "08_bo_fuera_de_tiempo.py configs\4108_bo_muerte_ampliada.json" 4108
call :paso 6 "07_modelo_final.py configs\5017_prod_muerte_ampliada_bo4108.json" 5017
call :paso 7 "10_entrega_zulip.py configs\6013_zulip_final_5017.json" 6013
echo Fin: %date% %time% >> logs\muerte_ampliada_tiempos.txt

echo.
echo ==== TERMINADO. Revisar logs\muerte_ampliada_tiempos.txt y los logs de cada paso ====
pause
exit /b

:paso
echo [%date% %time%] Paso %1 de 7: %~2
echo [%date% %time%] Paso %1 de 7 (%3): inicio >> logs\muerte_ampliada_tiempos.txt
%PY% -u %~2 > logs\%3.txt 2>&1
echo [%date% %time%] Paso %1 de 7 (%3): fin, codigo %errorlevel% >> logs\muerte_ampliada_tiempos.txt
exit /b
