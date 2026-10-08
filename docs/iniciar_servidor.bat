@echo off
title Servidor Local Showcase CTS-C51 ^| SMEQ 2026
cd /d "%~dp0"

echo ======================================================================
echo    CTS-C51: Sistema de Control In-Operando ^& Celda Hull (SMEQ 2026)
echo    Iniciando Servidor Web Local ^& Generador de Codigo QR...
echo ======================================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python servidor_showcase.py
    goto fin
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py servidor_showcase.py
    goto fin
)

echo [ERROR] No se encontro Python instalado en el sistema.
echo Por favor instala Python 3 desde python.org o asegurate de agregarlo al PATH.
echo.
pause

:fin
