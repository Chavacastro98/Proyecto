@echo off
title Visor de Diagramas Tecnicos - Super-Loop (v4.0) y FreeRTOS (RTOS 1.0)
cd /d "%~dp0"
echo =====================================================================
echo   INICIANDO VISOR GRAFICO MULTI-VENTANA DE DIAGRAMAS TECNICOS
echo   Suites Disponibles: Super-Loop (v4.0) y FreeRTOS (RTOS 1.0)
echo =====================================================================
echo.
python visor_diagramas.py
if errorlevel 1 (
    echo.
    echo [ERROR] No se pudo ejecutar Python. Abriendo visor web en su defecto...
    start index.html
)
