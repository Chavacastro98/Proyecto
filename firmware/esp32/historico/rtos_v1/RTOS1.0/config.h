#ifndef CONFIG_H
#define CONFIG_H

/**
 * =================================================================================
 * CONFIGURACIÓN GLOBAL DEL SISTEMA (config.h) — Versión RTOS 1.0
 * =================================================================================
 * Arquitectura: ESP32 Master Controller / FreeRTOS SMP Dual-Core + Patrón MVC
 *
 * ASIGNACIÓN DE NÚCLEOS (Dual-Core):
 * - Core 0 (COMUNICACIONES): Pila WiFi, SoftAP, WebServer HTTP, telemetría y OTA.
 * - Core 1 (CONTROL REAL-TIME): Control térmico PI, DAC, sensado ADS1115, supervisor.
 *
 * JERARQUÍA DE PRIORIDADES (FreeRTOS):
 * - Prioridad 6 (Máxima):  Task_Supervisor (Fail-Safe Watchdog e interlocks físicos)
 * - Prioridad 5 (Alta):    Task_Termico (4 lazos PI @ 1000ms, Rampa @ 200ms, UART2 al Nano)
 * - Prioridad 4 (Med-Alta): Task_Fuente (DAC MCP4725, modulación 1-100Hz, relé ZCS GPIO 20)
 * - Prioridad 3 (Media):   Task_Sensado (ADS1115 pH @ 20ms, Shunts @ 500ms, AHT20/BMP280 @ 5s)
 * - Prioridad 2 (Baja):    Task_Web (Gestión HTTP y vistas PROGMEM en Core 0)
 * =================================================================================
 */

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <Adafruit_ADS1X15.h>
#include <Adafruit_MCP4725.h>
#include <Adafruit_AHTX0.h>
#include <Adafruit_BMP280.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/semphr.h>
#include <freertos/event_groups.h>

#define FIRMWARE_VERSION "1.0-RTOS"

// =================================================================================
// MAPA DE PINES DEL HARDWARE (ESP32-S3)
// =================================================================================

/**
 * BUS I2C PRINCIPAL (Wire):
 * - Frecuencia: 400 kHz (I2C Fast Mode).
 * - Dispositivos conectados:
 *   1. ADS1115 (Dirección 0x48): Lectura diferencial de pH (A0/A1) y Shunts de corriente (A2/A3).
 *   2. MCP4725 (Dirección 0x60): DAC I2C de 12 bits para consigna de control del VCSS.
 *   3. AHT20   (Dirección 0x38): Sensor ambiental de temperatura y humedad relativa de cabina.
 *   4. BMP280  (Dirección 0x76/0x77): Sensor ambiental de presión barométrica.
 * - Sincronización: Cualquier transacción debe estar envuelta en takeI2CMutex() / giveI2CMutex().
 */
#define PIN_I2C_SDA         8   // Bus I2C Datos (SDA)
#define PIN_I2C_SCL         9   // Bus I2C Reloj (SCL)

/**
 * BUS SPI COMPARTIDO (MAX6675 - Termopares Tipo K):
 * - Lectura digital de 12 bits solo recepción (MISO). No requiere línea MOSI.
 * - Reloj máximo soportado por MAX6675: 4.3 MHz (se opera a 4 MHz en modo SPI_MODE0).
 * - 4 módulos MAX6675 comparten SCK y SO (MISO), seleccionados individualmente por CS activo en nivel BAJO.
 */
#define COMMON_SCK          18  // Reloj SPI compartido (SCK)
#define COMMON_SO           19  // Datos SPI compartidos desde los módulos hacia ESP32 (MISO / SO)
#define PIN_CS_TC0          5   // Chip Select Tina 0: Limpieza Química (Calentador 450W)
#define PIN_CS_TC1          4   // Chip Select Tina 1: Decapado Ácido (Calentador 450W)
#define PIN_CS_TC2          13  // Chip Select Tina 2: Zincado Celda Hull (Calentador 18W)
#define PIN_CS_TC3          14  // Chip Select Tina 3: Niquelado Químico (Calentador 450W)

/**
 * ENLACES DE COMUNICACIÓN Y POTENCIA EXTERNA:
 */
#define PIN_UART2_TX        17  // Transmisión serie asíncrona UART2 hacia esclavo Arduino Nano (9600 bps, 8N1)

/**
 * RELÉ DE AISLAMIENTO DE LA ETAPA DE POTENCIA (ZCS - Zero Current Switching):
 * - Desconecta físicamente la línea positiva de +12V (VDD) que alimenta la celda de electrodeposición.
 * - Al apagar la fuente o en paradas de emergencia, primero se fija la consigna DAC a 0V (corriente = 0A)
 *   y tras un retardo de asentamiento de 50 ms se conmuta el relé para evitar arcos voltaicos y degradación de contactos.
 * - Lógica: Optoacoplador activo en nivel BAJO (Active-LOW).
 */
#define PIN_RELE_VCSS       20  // Control de bobina relé +12V
#define RELE_NIVEL_ACTIVO   LOW // Nivel lógico para energizar bobina (conectar +12V a celda)

/**
 * PARÁMETROS FÍSICOS DEL SUMIDERO DE CORRIENTE (VCSS - Voltage-Controlled Current Sink):
 * - Topología eléctrica: Sumidero de corriente de lado bajo compuesto por dos ramas MOSFET N en paralelo.
 * - Cada rama cuenta con un shunt de sensado de 0.50 Ohms y un amplificador operacional en lazo cerrado local.
 * - Transconductancia nominal por rama: 1.0 A/V.
 * - Transconductancia total combinada: Gm = 1.0 A/V + 1.0 A/V = 2.00 Siemens (A/V).
 * - Rango de entrada DAC: 0.00 V a 3.30 V -> Rango nominal de salida: 0.00 A a 6.60 A (limitado por firmware a 3.50 A).
 */
#define VCSS_GM_NOMINAL     2.00f   // Transconductancia total nominal (2.00 S)
#define VCSS_VREF_DAC       3.30f   // Tensión de fondo de escala del DAC MCP4725 (3.30 V)
#define VCSS_IMAX_NOMINAL   (VCSS_VREF_DAC * VCSS_GM_NOMINAL) // 6.60 A teóricos a 4095 LSB

/**
 * BALIZA LUMINOSA RGB DEL SUPERVISOR FREERTOS:
 * - Indicador de estado de proceso en tiempo real gestionado por Task_Supervisor en Core 1 @ 50 Hz.
 * - Utiliza el LED WS2812 direccionable integrado en la placa ESP32-S3 (GPIO 48 por defecto).
 */
#ifndef PIN_LED_RGB
  #if defined(RGB_BUILTIN)
    #define PIN_LED_RGB     RGB_BUILTIN
  #else
    #define PIN_LED_RGB     48  // Pin de datos WS2812 RGB en ESP32-S3 DevKit
  #endif
#endif

// =================================================================================
// CONFIGURACIÓN DE TAREAS FREERTOS (SMP DUAL-CORE)
// =================================================================================
#define CORE_REALTIME       1   // Core 1: Lazos de control y adquisición de hardware
#define CORE_COMMS          0   // Core 0: Pila de red WiFi, HTTP y actualización OTA

#define PRIO_TASK_SUPERVISOR 6  // Máxima prioridad del sistema
#define PRIO_TASK_TERMICO    5  // Control térmico de potencia (4x450W)
#define PRIO_TASK_FUENTE     4  // Fuente de corriente y modulación DAC
#define PRIO_TASK_SENSADO    3  // Adquisición I2C compartida
#define PRIO_TASK_WEB        2  // Servidor web y respuestas JSON

#define STACK_TASK_SUPERVISOR 3072
#define STACK_TASK_TERMICO    4096
#define STACK_TASK_FUENTE     3072
#define STACK_TASK_SENSADO    4096
#define STACK_TASK_WEB        6144

// =================================================================================
// CONSTANTES FÍSICAS Y DE PROCESO
// =================================================================================
#define VREF                  3.3f
#define PH_OFFSET_TEORICO     1.650f
#define PH_PENDIENTE_TEORICA  4.242f

// =================================================================================
// OBJETOS GLOBALES DE HARDWARE Y ALMACENAMIENTO
// =================================================================================
extern const char *ssid;
extern const char *password;
extern WebServer server;
extern Preferences memoria;

extern Adafruit_ADS1115 ads;
extern Adafruit_MCP4725 dac;
extern Adafruit_AHTX0   aht;
extern Adafruit_BMP280  bmp;

// =================================================================================
// VARIABLES GLOBALES COMPARTIDAS (Protegidas con Mutexes de FreeRTOS)
// =================================================================================

// --- Variables Ambientales ---
extern volatile float amb_temp;
extern volatile float amb_hum;
extern volatile float amb_pres;
extern bool ahtInicializado;
extern bool bmpInicializado;

// --- Variables Módulo pH ---
extern volatile bool    phModuloActivo;
extern volatile uint8_t tipoCalPH1, tipoCalPH2;
extern volatile float   v7_1, v4_1, v10_1, m_ph1, mAcida1, mBasica1, phActual1;
extern volatile bool    calibradoPH1;
extern volatile float   v7_2, v4_2, v10_2, m_ph2, mAcida2, mBasica2, phActual2;
extern volatile bool    calibradoPH2;
extern volatile float   voltajeCrudoPH;

// --- Variables Fuente VCSS ---
extern volatile bool  fuenteActiva;
extern volatile bool  modoPulsado;
extern volatile int   amplitudDAC;
extern volatile int   amplitudDAC_Setpoint;
extern volatile int   frecuencia;
extern volatile int   dutyCycle;
extern volatile bool  estadoReleVDD;
extern volatile float corrienteReal_R1;
extern volatile float corrienteReal_R2;
extern volatile float corrienteTotalReal;
extern volatile float voltajeShunt1_raw;
extern volatile float voltajeShunt2_raw;
extern volatile float factorGananciaVCSS;
extern volatile bool  compensacionLazoCerrado;

// =================================================================================
// MATRIZ DE CÓDIGOS DE ERROR (ESTÁNDAR INDUSTRIAL ISA-18.2)
// =================================================================================
enum ErrorCode_t : uint8_t {
  ERR_NONE                = 0,   // Operación Normal (Sin Fallas)
  ERR_TC0_FAIL            = 10,  // Falla Termopar 0 (Limpieza)
  ERR_TC1_FAIL            = 11,  // Falla Termopar 1 (Decapado)
  ERR_TC2_FAIL            = 12,  // Falla Termopar 2 (Celda Hull)
  ERR_TC3_FAIL            = 13,  // Falla Termopar 3 (Niquelado)
  ERR_TEMP_OVERHEAT       = 14,  // Sobretemperatura Crítica (> Setpoint + 5°C)
  ERR_VCSS_OPEN_CIRCUIT   = 20,  // Circuito Abierto en Celda VCSS (0A medido con consigna activa)
  ERR_VCSS_OVERCURRENT    = 21,  // Sobrecorriente en Celda VCSS (> 3.5A medido)
  ERR_I2C_ADS_LOST        = 30,  // Pérdida de comunicación ADC ADS1115
  ERR_I2C_DAC_LOST        = 31,  // Pérdida de comunicación DAC MCP4725
  ERR_I2C_ENV_LOST        = 32,  // Pérdida de sensores AHT20/BMP280
  ERR_RTOS_HEARTBEAT      = 40,  // Falla Watchdog: Tarea FreeRTOS congelada (> 5000 ms)
  ERR_UART_NANO_TIMEOUT   = 50,  // Pérdida de enlace serie con Arduino Nano
  ERR_WIFI_FAIL           = 60   // Falla crítica en arranque de Red Wi-Fi SoftAP
};

// --- Variables de Seguridad Fail-Safe ---
extern volatile uint8_t g_failsafe_code;

#endif // CONFIG_H
