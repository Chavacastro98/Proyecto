@echo off
setlocal enabledelayedexpansion
title Telemetria ESP32 - Planta de Electrodeposicion (v3.5 / RTOS 1.3)
cd /d "%~dp0..\..\software"

echo ===============================================================================
echo   INICIANDO INTERFAZ DE TELEMETRIA EN VIVO Y SCADA (v1.0)
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

!PYTHON_CMD! -m telemetria

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ===============================================================================
    echo   [AVISO] Ocurrio un problema al iniciar la interfaz o faltan librerias.
    echo   Ejecutando instalador y comprobador de librerias...
    echo ===============================================================================
    echo.
    call "..\documentos\instaladores\instalar_python_y_librerias.bat"
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [OK] Reintentando abrir aplicacion de telemetria...
        !PYTHON_CMD! -m telemetria
    ) else (
        pause
    )
)
