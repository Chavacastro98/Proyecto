@echo off
setlocal enabledelayedexpansion
title Instalador Automatizado - Python y Dependencias de Telemetria
cd /d "%~dp0"

echo ===============================================================================
echo   INSTALADOR AUTOMATIZADO DE ENTORNO PYTHON - SISTEMA DE TELEMETRIA
echo   Proyecto: Automatizacion de Planta Piloto de Electrodeposicion (ESP32)
echo ===============================================================================
echo.

:: 1. Verificar si Python ya esta instalado y accesible en PATH
set "PYTHON_EXE="
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_EXE=python"
    goto :PYTHON_ENCONTRADO
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_EXE=py"
    goto :PYTHON_ENCONTRADO
)

:: Buscar en rutas comunes de instalacion de Windows
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_EXE=%%D\python.exe"
        set "PATH=%%D;%%D\Scripts;!PATH!"
        goto :PYTHON_ENCONTRADO
    )
)

for /d %%D in ("%ProgramFiles%\Python*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_EXE=%%D\python.exe"
        set "PATH=%%D;%%D\Scripts;!PATH!"
        goto :PYTHON_ENCONTRADO
    )
)

:: 2. Si no se encontro Python, instalar mediante la herramienta oficial de Windows (winget)
echo [!] No se detecto una instalacion activa de Python en el sistema.
echo [INFO] Intentando instalacion oficial mediante Windows Package Manager (winget)...
echo.

where winget >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [->] Instalando Python 3.11 oficial desde el catalogo de Microsoft...
    winget install Python.Python.3.11 --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Python instalado exitosamente via winget.
        timeout /t 3 >nul
        for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
            if exist "%%D\python.exe" (
                set "PYTHON_EXE=%%D\python.exe"
                set "PATH=%%D;%%D\Scripts;!PATH!"
                goto :PYTHON_ENCONTRADO
            )
        )
    )
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_EXE=python"
    goto :PYTHON_ENCONTRADO
)

:: Fallback amigable si winget no esta o fallo la instalacion desatendida
echo.
echo ===============================================================================
echo   [ACCION REQUERIDA] INSTALACION MANUAL DE PYTHON
echo ===============================================================================
echo   Se abrira la pagina oficial de descarga de Python en su navegador.
echo   1. Descargue el instalador para Windows.
echo   2. Al ejecutarlo, MARQUE LA CASILLA: 'Add python.exe to PATH'
echo   3. Seleccione 'Install Now' y finalice la instalacion.
echo ===============================================================================
echo.
start https://www.python.org/downloads/
pause
exit /b 1

:PYTHON_ENCONTRADO
echo.
echo [OK] Python detectado correctamente:
!PYTHON_EXE! --version
echo.

:: 3. Actualizar pip
echo [->] Verificando pip...
!PYTHON_EXE! -m pip install --upgrade pip --quiet

:: 4. Instalar dependencias desde requirements.txt
set "REQ_FILE=%~dp0..\..\requirements.txt"
if exist "!REQ_FILE!" (
    echo [->] Instalando librerias desde requirements.txt...
    !PYTHON_EXE! -m pip install -r "!REQ_FILE!"
) else (
    echo [->] Instalando librerias de telemetria...
    !PYTHON_EXE! -m pip install requests matplotlib pandas openpyxl numpy
)

:: 5. Validacion final de librerias
echo.
echo [->] Verificando importacion de librerias...
!PYTHON_EXE! -c "import requests, matplotlib, pandas, openpyxl, numpy; print('   [OK] Todas las librerias se cargaron exitosamente.')"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===============================================================================
    echo   CONFIGURACION COMPLETADA CON EXITO
    echo   El entorno de telemetria esta listo para ejecutarse.
    echo   Puedes iniciar el sistema haciendo doble clic en 'Iniciar_Sistema.bat'.
    echo ===============================================================================
) else (
    echo.
    echo [AVISO] Hubo un problema al verificar algunas librerias. Revisa tu conexion a Internet.
)

echo.
pause
