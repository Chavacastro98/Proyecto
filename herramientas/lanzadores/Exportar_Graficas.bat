@echo off
setlocal enabledelayedexpansion
title Generador Offline de Graficas Cientificas - Telemetria ESP32 (300 DPI)
cd /d "%~dp0..\..\software"

echo ===============================================================================
echo   GENERADOR Y EXPORTADOR OFFLINE DE GRAFICAS CIENTIFICAS (300 DPI)
echo   Telemetria 1.0 y Telemetria 2.0 - Planta Piloto de Electrodeposicion
echo ===============================================================================
echo.

set "PYTHON_CMD="
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 set "PYTHON_CMD=python"

if "!PYTHON_CMD!"=="" (
    where py >nul 2>&1
    if %ERRORLEVEL% EQU 0 set "PYTHON_CMD=py"
)

if "!PYTHON_CMD!"=="" (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
        if exist "%%D\python.exe" (
            set "PYTHON_CMD=%%D\python.exe"
            set "PATH=%%D;%%D\Scripts;!PATH!"
        )
    )
)

if "!PYTHON_CMD!"=="" (
    echo [!] No se detecto Python instalado en el sistema.
    echo [->] Abriendo el instalador automatico...
    call "..\documentos\instaladores\instalar_python_y_librerias.bat"
    exit /b 0
)

!PYTHON_CMD! exportar_graficas_offline.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ===============================================================================
    echo   [AVISO] Ocurrio un problema al iniciar el generador o faltan librerias.
    echo   Ejecutando instalador y comprobador de librerias...
    echo ===============================================================================
    echo.
    call "..\documentos\instaladores\instalar_python_y_librerias.bat"
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [OK] Reintentando abrir aplicacion...
        !PYTHON_CMD! exportar_graficas_offline.py %*
    ) else (
        pause
    )
)
