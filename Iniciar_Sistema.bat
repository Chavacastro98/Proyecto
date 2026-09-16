@echo off
setlocal enabledelayedexpansion
title Sistema de Electrodeposicion y Galvanoplastia - Panel de Control
cd /d "%~dp0"

:: 1. Deteccion del ejecutable de Python
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
    echo [INFO] Abriendo instalador oficial...
    call "documentos\instaladores\instalar_python_y_librerias.bat"
    where python >nul 2>&1
    if %ERRORLEVEL% EQU 0 set "PYTHON_CMD=python"
)

:: 2. Si Python esta disponible, iniciar Panel Maestro en Python (GUI)
if exist "launcher.py" (
    if not "!PYTHON_CMD!"=="" (
        start "" !PYTHON_CMD! launcher.py
        exit /b 0
    )
)

:MENU
cls
echo ===============================================================================
echo   SISTEMA AUTOMATIZADO DE ELECTRODEPOSICION (ESP32-S3 / ARDUINO NANO)
echo   Plataforma de Control, SCADA, Metrologia de Faraday y Documentacion
echo ===============================================================================
echo.
echo   [1] Iniciar Telemetria 2.0 SCADA (Canal A1 - RTOS 2.0) [ACTIVO]
echo   [2] Iniciar Telemetria 1.0 SCADA (Version Base - RTOS 1.3)
echo   [3] Exportador Offline de Graficas Cientificas (300 DPI)
echo   [4] Abrir Manual de Operacion Quimica y Protocolo de Laboratorio (HTML)
echo   [5] Abrir Visor Interactivo de Diagramas de Arquitectura
echo   [6] Abrir Hub de Simuladores Web (Previews de Interfaces)
echo   [7] Abrir Panel Web ESP32 en Navegador (http://192.168.4.1)
echo   [8] Abrir Carpeta de Tesis y Documentos Academicos
echo   [0] Salir
echo.
echo ===============================================================================
choice /c 123456780 /n /m "Seleccione una opcion [0-8]: "

if errorlevel 9 exit /b 0
if errorlevel 8 goto ABRIR_ACADEMICOS
if errorlevel 7 goto LANZAR_PANEL_WEB
if errorlevel 6 goto LANZAR_PREVIEWS
if errorlevel 5 goto LANZAR_DIAGRAMAS
if errorlevel 4 goto LANZAR_MANUAL
if errorlevel 3 goto LANZAR_EXPORTADOR
if errorlevel 2 goto LANZAR_TEL1
if errorlevel 1 goto LANZAR_TEL2

goto MENU

:LANZAR_TEL2
echo [->] Iniciando Telemetria 2.0 SCADA...
cd /d "%~dp0software"
!PYTHON_CMD! telemetria2.0
cd /d "%~dp0"
pause
goto MENU

:LANZAR_TEL1
echo [->] Iniciando Telemetria 1.0 SCADA...
cd /d "%~dp0software"
!PYTHON_CMD! -m telemetria
cd /d "%~dp0"
pause
goto MENU

:LANZAR_EXPORTADOR
echo [->] Iniciando Generador Offline de Graficas (300 DPI)...
cd /d "%~dp0software"
!PYTHON_CMD! exportar_graficas_offline.py
cd /d "%~dp0"
pause
goto MENU

:LANZAR_MANUAL
echo [->] Abriendo Manual de Operacion Quimica...
start "" "%~dp0documentos\manuales\MANUAL_DE_OPERACION_QUIMICA.html"
goto MENU

:LANZAR_DIAGRAMAS
echo [->] Iniciando Visor de Diagramas Tecnicos...
cd /d "%~dp0visualizacion\diagramas"
!PYTHON_CMD! visor_diagramas.py
if errorlevel 1 (
    echo [INFO] Abriendo visor web en navegador...
    start index.html
)
cd /d "%~dp0"
goto MENU

:LANZAR_PREVIEWS
echo [->] Abriendo Hub de Previews y Simulador Web...
cd /d "%~dp0visualizacion\preview"
start index.html
cd /d "%~dp0"
goto MENU

:LANZAR_PANEL_WEB
echo [->] Abriendo Panel Web del ESP32 (http://192.168.4.1)...
echo [INFO] Recuerde conectarse a la red Wi-Fi 'Uli' (Pass: 12345678) si usa el ESP32 fisico.
start http://192.168.4.1
timeout /t 3 > nul
goto MENU

:ABRIR_ACADEMICOS
echo [->] Abriendo carpeta de Documentos Academicos y Tesis...
start "" "%~dp0documentos\academicos"
goto MENU