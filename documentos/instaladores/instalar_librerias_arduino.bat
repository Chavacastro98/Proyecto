@echo off
setlocal enabledelayedexpansion
title Instalador de Librerias de Hardware - Arduino IDE y ESP32
cd /d "%~dp0"

echo ===============================================================================
echo   INSTALADOR DE LIBRERIAS PARA ARDUINO IDE / ESP32 (FIRMWARE v3.5)
echo   Proyecto: Automatizacion de Planta Piloto de Electrodeposicion
echo ===============================================================================
echo.

:: 1. Determinar directorio de librerias de Arduino del usuario
set "ARDUINO_LIB_DIR=%USERPROFILE%\Documents\Arduino\libraries"

for /f "usebackq tokens=*" %%P in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('MyDocuments') + '\Arduino\libraries'"`) do (
    set "ARDUINO_LIB_DIR=%%P"
)

echo [->] Directorio de librerias de Arduino detectado:
echo      "%ARDUINO_LIB_DIR%"
echo.

if not exist "%ARDUINO_LIB_DIR%" (
    echo [->] Creando carpeta de librerias de Arduino...
    mkdir "%ARDUINO_LIB_DIR%"
)

:: 2. Comprobar si existe arduino-cli
where arduino-cli >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [->] Se detecto 'arduino-cli' en el sistema.
    echo [->] Instalando librerias oficiales via gestor de paquetes de Arduino...
    echo.
    arduino-cli lib install "Adafruit ADS1X15"
    arduino-cli lib install "Adafruit AHTX0"
    arduino-cli lib install "Adafruit BMP280 Library"
    arduino-cli lib install "Adafruit MCP4725"
    arduino-cli lib install "MAX6675 library"
    arduino-cli lib install "Adafruit BusIO"
    arduino-cli lib install "Adafruit Unified Sensor"
    goto :RESUMEN_HARDWARE
)

:: 3. Descarga e instalacion automatica de repositorios oficiales via PowerShell
echo [->] Descargando y desplegando librerias directamente desde GitHub...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$libDir = '%ARDUINO_LIB_DIR%';" ^
    "$libs = @(" ^
    "    @{ name = 'Adafruit_ADS1X15'; url = 'https://github.com/adafruit/Adafruit_ADS1X15/archive/refs/heads/master.zip' }," ^
    "    @{ name = 'Adafruit_AHTX0'; url = 'https://github.com/adafruit/Adafruit_AHTX0/archive/refs/heads/master.zip' }," ^
    "    @{ name = 'Adafruit_BMP280_Library'; url = 'https://github.com/adafruit/Adafruit_BMP280_Library/archive/refs/heads/master.zip' }," ^
    "    @{ name = 'Adafruit_MCP4725'; url = 'https://github.com/adafruit/Adafruit_MCP4725/archive/refs/heads/master.zip' }," ^
    "    @{ name = 'MAX6675_library'; url = 'https://github.com/adafruit/MAX6675-library/archive/refs/heads/master.zip' }," ^
    "    @{ name = 'Adafruit_BusIO'; url = 'https://github.com/adafruit/Adafruit_BusIO/archive/refs/heads/master.zip' }," ^
    "    @{ name = 'Adafruit_Sensor'; url = 'https://github.com/adafruit/Adafruit_Sensor/archive/refs/heads/master.zip' }" ^
    ");" ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;" ^
    "$tempDir = Join-Path $env:TEMP 'arduino_libs_dl';" ^
    "if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force };" ^
    "New-Item -ItemType Directory -Path $tempDir | Out-Null;" ^
    "foreach ($lib in $libs) {" ^
    "    Write-Host ('   [>>] Descargando ' + $lib.name + '...');" ^
    "    $zipPath = Join-Path $tempDir ($lib.name + '.zip');" ^
    "    $destPath = Join-Path $libDir $lib.name;" ^
    "    try {" ^
    "        (New-Object Net.WebClient).DownloadFile($lib.url, $zipPath);" ^
    "        $extractPath = Join-Path $tempDir $lib.name;" ^
    "        Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force;" ^
    "        $subfolder = Get-ChildItem -Path $extractPath | Where-Object { $_.PSIsContainer } | Select-Object -First 1;" ^
    "        if (Test-Path $destPath) { Remove-Item $destPath -Recurse -Force };" ^
    "        Move-Item -Path $subfolder.FullName -Destination $destPath -Force;" ^
    "        Write-Host ('   [OK] ' + $lib.name + ' instalada con exito.') -ForegroundColor Green;" ^
    "    } catch {" ^
    "        Write-Host ('   [!] Error al descargar ' + $lib.name + ': ' + $_.Exception.Message) -ForegroundColor Yellow;" ^
    "    }" ^
    "};" ^
    "Remove-Item $tempDir -Recurse -Force;"

:RESUMEN_HARDWARE
echo.
echo ===============================================================================
echo   LIBRERIAS DE ARDUINO/ESP32 INSTALADAS SATISFACTORIAMENTE
echo ===============================================================================
echo.
echo   Librerias configuradas:
echo     1. Adafruit_ADS1X15       (Convertidor ADC 16-Bit I2C para pH y Shunts)
echo     2. Adafruit_AHTX0         (Sensor ambiental Temperatura / Humedad)
echo     3. Adafruit_BMP280        (Sensor ambiental Presion Barometrica)
echo     4. Adafruit_MCP4725       (Convertidor DAC 12-Bit para Corriente VCSS)
echo     5. MAX6675_library        (Sensores de Temperatura SPI Termopar K)
echo     6. Adafruit_BusIO         (Manejador de buses I2C / SPI Adafruit)
echo     7. Adafruit_Sensor        (Capa unificada de sensores)
echo.
echo   -----------------------------------------------------------------------------
echo   PASOS PARA COMPILAR EL FIRMWARE EN ARDUINO IDE:
echo   -----------------------------------------------------------------------------
echo   1. ARDUINO NANO (Dimmer de TRIACs):
echo      - Abrir: arduino_nano\nano\nano.ino
echo      - Placa: Arduino Nano (Procesador: ATmega328P o Old Bootloader)
echo      - Puerto COM: Seleccionar el correspondiente al cable Nano.
echo      - Dar clic en Subir / Upload.
echo.
echo   2. ESP32-S3 N16R8 (Nodo Maestro FreeRTOS Dual-Core RTOS 1.0):
echo      - Abrir: esp32\RTOS1.0\RTOS1.0.ino
echo      - En Preferencias -> 'Gestor de URLs Adicionales de Tarjetas', agregar:
echo        https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
echo      - Placa: 'ESP32S3 Dev Module'
echo      - Flash Size: '16MB (128Mb)'
echo      - Partition Scheme: '16M Flash (3MB APP/9.9MB FATFS)'
echo      - PSRAM: 'OPI PSRAM'
echo      - USB CDC On Boot: 'Enabled'
echo      - Dar clic en Subir / Upload.
echo ===============================================================================
echo.
pause
