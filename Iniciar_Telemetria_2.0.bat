@echo off
setlocal enabledelayedexpansion
title Telemetria ESP32 - Planta de Electrodeposicion (RTOS 2.0)
cd /d "%~dp0"

echo ===============================================================================
echo   INICIANDO INTERFAZ DE TELEMETRIA 2.0 (CANAL DEDICADO A1 - RTOS 2.0)
echo ===============================================================================
echo.

:: 1. Detectar ejecutable de Python disponible
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
    echo [INFO] Abriendo el instalador oficial...
    call "documentos\instaladores\instalar_python_y_librerias.bat"
    where python >nul 2>&1
    if %ERRORLEVEL% EQU 0 set "PYTHON_CMD=python"
)

if "!PYTHON_CMD!"=="" (
    echo [ERROR] No se pudo encontrar ni instalar Python.
    pause
    exit /b 1
)

:: 2. Intentar ejecutar la interfaz Telemetria 2.0
cd /d "%~dp0software"
!PYTHON_CMD! telemetria2.0

:: 3. Si fallo, diagnosticar si fue por librerias faltantes
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ===============================================================================
    echo   [AVISO] Ocurrio un problema al iniciar la interfaz o faltan librerias.
    echo   Ejecutando comprobador e instalador de dependencias...
    echo ===============================================================================
    echo.
    cd /d "%~dp0"
    call "documentos\instaladores\instalar_python_y_librerias.bat"
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [OK] Reintentando abrir aplicacion de telemetria 2.0...
        cd /d "%~dp0software"
        !PYTHON_CMD! telemetria2.0
    ) else (
        pause
    )
)
