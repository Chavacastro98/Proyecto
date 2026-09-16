@echo off
title Exportar Diagramas a Imagenes PNG y SVG (Superloop y RTOS)
cd /d "%~dp0"
echo =====================================================================
echo   EXPORTADOR MODULAR DE DIAGRAMAS A ALTA DEFINICION (PNG/SVG)
echo   Suites: Super-Loop (v4.0) y FreeRTOS (RTOS 1.0)
echo =====================================================================
echo.
python visor_diagramas.py --exportar-todo
echo.
echo Presiona cualquier tecla para salir...
pause >nul
