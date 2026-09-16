@echo off
title Visor de Diagramas Tecnicos - Super-Loop y FreeRTOS
cd /d "%~dp0..\..\visualizacion\diagramas"
python visor_diagramas.py
if errorlevel 1 (
    echo [INFO] Abriendo visor web interactivo en su defecto...
    start index.html
)
